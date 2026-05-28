from __future__ import annotations

import asyncio
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
            elapsed_ms=int((time.perf_counter() - start) * 1000),
            errors=errors,
            retrieval_hits=retrieval_hits,
        )


def run_async(coro):
    return asyncio.run(coro)

