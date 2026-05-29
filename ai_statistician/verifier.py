from __future__ import annotations

import asyncio
import copy
import os
import time
from dataclasses import dataclass
from typing import Protocol

from .schema import FormalObligation, ProofCheck, RetrievalHit


LEAN_ENV = os.environ.get("AXLE_ENVIRONMENT", "lean-4.29.0")


def splice_proof(formal_statement: str, proof_body: str) -> str:
    proof = proof_body.strip()
    if proof.lower().startswith("by "):
        return formal_statement.replace("by sorry", proof, 1)
    if any(proof.startswith(prefix) for prefix in ("exact ", "apply ", "simp", "rfl", "omega", "linarith")):
        return formal_statement.replace("by sorry", "by\n  " + proof, 1)
    return formal_statement.replace(":= by sorry", ":=\n  " + proof, 1)


class ProofVerifier(Protocol):
    name: str

    async def verify(
        self,
        obligation: FormalObligation,
        proof_body: str,
        retrieval_hits: list[RetrievalHit],
    ) -> ProofCheck:
        ...


class MockProofVerifier:
    """Fast verifier for CI and offline demos.

    It rejects missing proofs and any candidate that still contains `sorry`.
    Use AxleProofVerifier for actual Lean kernel-backed verification.
    """

    name = "mock"

    async def verify(
        self,
        obligation: FormalObligation,
        proof_body: str,
        retrieval_hits: list[RetrievalHit],
    ) -> ProofCheck:
        start = time.perf_counter()
        content = splice_proof(obligation.formal_statement, proof_body)
        errors: list[str] = []
        if "sorry" in content:
            errors.append("candidate still contains sorry")
        if not proof_body.strip():
            errors.append("empty proof body")
        return ProofCheck(
            obligation_id=obligation.id,
            ok=not errors,
            proof_body=proof_body,
            verifier=self.name,
            verification_strength="mock_static_check",
            kernel_verified=False,
            elapsed_ms=int((time.perf_counter() - start) * 1000),
            errors=errors,
            retrieval_hits=retrieval_hits,
        )


class AxleProofVerifier:
    """AXLE-backed real Lean proof verifier."""

    name = "axle.verify_proof"

    def __init__(self, environment: str = LEAN_ENV, api_key: str | None = None):
        self.environment = environment
        self.api_key = api_key or os.environ.get("AXLE_API_KEY")

    async def verify(
        self,
        obligation: FormalObligation,
        proof_body: str,
        retrieval_hits: list[RetrievalHit],
    ) -> ProofCheck:
        if not self.api_key:
            return ProofCheck(
                obligation_id=obligation.id,
                ok=False,
                proof_body=proof_body,
                verifier=self.name,
                verification_strength="axle_unavailable",
                kernel_verified=False,
                errors=["AXLE_API_KEY is not set"],
                retrieval_hits=retrieval_hits,
            )

        candidate = splice_proof(obligation.formal_statement, proof_body)
        start = time.perf_counter()

        async def _run() -> tuple[bool, list[str]]:
            try:
                from axle import AxleClient
            except Exception as exc:
                return False, [f"failed to import axle package: {exc!r}"]

            async with AxleClient(api_key=self.api_key) as axle:
                try:
                    result = await axle.verify_proof(
                        formal_statement=obligation.formal_statement,
                        content=candidate,
                        environment=self.environment,
                    )
                except Exception as exc:
                    return False, [f"{type(exc).__name__}: {exc}"]
            errors: list[str] = []
            for bag_name in ("tool_messages", "lean_messages"):
                bag = getattr(result, bag_name, None)
                if bag is not None:
                    errors.extend(str(item) for item in (getattr(bag, "errors", []) or []))
            return bool(getattr(result, "okay", False)), errors

        ok, errors = await _run()
        return ProofCheck(
            obligation_id=obligation.id,
            ok=ok,
            proof_body=proof_body,
            verifier=self.name,
            verification_strength="axle_lean_kernel",
            kernel_verified=ok,
            elapsed_ms=int((time.perf_counter() - start) * 1000),
            errors=errors,
            retrieval_hits=retrieval_hits,
        )


class CachingProofVerifier:
    """Memoize verifier calls within one audit/run.

    AXLE verification is the expensive trusted boundary. A research-system audit
    reuses the same registered obligations across the proof-bank audit, frontier
    smoke benchmark, and research benchmark. This wrapper avoids repeated remote
    checks while preserving the original verifier's `kernel_verified` result.
    """

    def __init__(self, verifier: ProofVerifier) -> None:
        self.verifier = verifier
        self.name = getattr(verifier, "name", type(verifier).__name__)
        self.cache_hits = 0
        self.cache_misses = 0
        self._cache: dict[tuple[str, str], ProofCheck] = {}

    async def verify(
        self,
        obligation: FormalObligation,
        proof_body: str,
        retrieval_hits: list[RetrievalHit],
    ) -> ProofCheck:
        key = (obligation.id, proof_body)
        if key in self._cache:
            self.cache_hits += 1
            cached = copy.deepcopy(self._cache[key])
            cached.retrieval_hits = retrieval_hits
            return cached
        self.cache_misses += 1
        check = await self.verifier.verify(obligation, proof_body, retrieval_hits)
        self._cache[key] = copy.deepcopy(check)
        return check

    def cache_info(self) -> dict[str, int]:
        return {
            "hits": self.cache_hits,
            "misses": self.cache_misses,
            "size": len(self._cache),
        }


def run_async(coro):
    return asyncio.run(coro)
