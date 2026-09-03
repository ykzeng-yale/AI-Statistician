from __future__ import annotations

import asyncio
import contextlib
import os
import re
import shutil
import signal
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from .research_source_inventory import VENDORED_EMPIRICAL_PROCESS_ROOT
from .schema import FormalObligation, ProofCheck, RetrievalHit


LEAN_ENV = os.environ.get("AXLE_ENVIRONMENT", "lean-4.29.0")
DEFAULT_LOCAL_LEAN_PROJECTS = (
    Path(os.environ["AI_STATISTICIAN_LEAN_PROJECT"])
    if os.environ.get("AI_STATISTICIAN_LEAN_PROJECT")
    else None,
    VENDORED_EMPIRICAL_PROCESS_ROOT,
    Path.home() / "LeanProjects" / "LeanPractice",
    Path.home() / "Desktop" / "AI for Math" / "Codex",
)


def splice_proof(formal_statement: str, proof_body: str) -> str:
    proof = proof_body.strip()
    if proof.lower().startswith("by"):
        return formal_statement.replace("by sorry", proof, 1)
    indented = "\n  ".join(proof.splitlines())
    return formal_statement.replace("by sorry", "by\n  " + indented, 1)


def placeholder_proof_errors(content: str) -> list[str]:
    """Reject Lean placeholders that compile by warning but are not proofs."""

    patterns = (
        (r"\bsorry\b", "candidate still contains sorry"),
        (r"\badmit\b", "candidate still contains admit"),
        (r"\baxiom\b", "candidate introduces axiom"),
    )
    return [message for pattern, message in patterns if re.search(pattern, content)]


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
        errors: list[str] = placeholder_proof_errors(content)
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
        candidate = splice_proof(obligation.formal_statement, proof_body)
        placeholder_errors = placeholder_proof_errors(candidate)
        if placeholder_errors:
            return ProofCheck(
                obligation_id=obligation.id,
                ok=False,
                proof_body=proof_body,
                verifier=self.name,
                verification_strength="axle_placeholder_rejected",
                kernel_verified=False,
                errors=placeholder_errors,
                retrieval_hits=retrieval_hits,
            )
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


async def _terminate_process_tree(proc: asyncio.subprocess.Process | None) -> None:
    if proc is None or proc.returncode is not None:
        return
    with contextlib.suppress(ProcessLookupError):
        os.killpg(proc.pid, signal.SIGTERM)
    with contextlib.suppress(Exception):
        await asyncio.wait_for(proc.wait(), timeout=2)
        return
    with contextlib.suppress(ProcessLookupError):
        os.killpg(proc.pid, signal.SIGKILL)
    with contextlib.suppress(Exception):
        await asyncio.wait_for(proc.wait(), timeout=2)


class LocalLeanProofVerifier:
    """Local `lake env lean` verifier for Mathlib-backed proof-bank checks.

    AXLE remains the preferred remote verifier when available. This backend is
    an auditable kernel fallback: it splices the proof body into the Lean file,
    runs the local Lean executable through an existing Mathlib Lake workspace,
    and treats Lean's exit code as the trusted proof result.
    """

    name = "local.lake_env_lean"

    def __init__(self, project_root: str | Path | None = None, timeout_s: int = 90):
        self.project_root = _resolve_local_lean_project(project_root)
        self.timeout_s = int(timeout_s)

    async def verify_many(
        self,
        items: list[tuple[FormalObligation, str, list[RetrievalHit]]],
    ) -> list[ProofCheck]:
        """Verify many obligations with one Lean process when possible.

        Per-obligation `lake env lean` startup dominates local proof-bank audits.
        Batch mode namespaces each candidate to avoid local definition clashes,
        runs Lean once, and falls back to individual checks if the combined file
        fails so diagnostics stay precise.
        """

        start = time.perf_counter()
        if not items:
            return []
        if any(
            placeholder_proof_errors(splice_proof(obligation.formal_statement, proof_body))
            for obligation, proof_body, _ in items
        ):
            return [
                await self.verify(obligation, proof_body, retrieval_hits)
                for obligation, proof_body, retrieval_hits in items
            ]
        if shutil.which("lake") is None or self.project_root is None:
            return [
                await self.verify(obligation, proof_body, retrieval_hits)
                for obligation, proof_body, retrieval_hits in items
            ]

        code = _batch_local_lean_code(
            [
                (obligation.id, splice_proof(obligation.formal_statement, proof_body))
                for obligation, proof_body, _ in items
            ]
        )
        with tempfile.TemporaryDirectory(prefix="ai_stat_lean_batch_") as tmp:
            lean_file = Path(tmp) / "proof_bank_batch.lean"
            lean_file.write_text(code, encoding="utf-8")
            proc = None
            try:
                proc = await asyncio.create_subprocess_exec(
                    "lake",
                    "env",
                    "lean",
                    str(lean_file),
                    cwd=str(self.project_root),
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    start_new_session=True,
                )
                stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=self.timeout_s)
            except asyncio.TimeoutError:
                await _terminate_process_tree(proc)
                elapsed_ms = int((time.perf_counter() - start) * 1000)
                return [
                    ProofCheck(
                        obligation_id=obligation.id,
                        ok=False,
                        proof_body=proof_body,
                        verifier=self.name,
                        verification_strength="local_lean_timeout",
                        kernel_verified=False,
                        elapsed_ms=elapsed_ms,
                        errors=[f"local Lean batch verification timed out after {self.timeout_s}s"],
                        retrieval_hits=retrieval_hits,
                    )
                    for obligation, proof_body, retrieval_hits in items
                ]
            except asyncio.CancelledError:
                await _terminate_process_tree(proc)
                raise
            except Exception:
                return [
                    await self.verify(obligation, proof_body, retrieval_hits)
                    for obligation, proof_body, retrieval_hits in items
                ]

        if proc.returncode != 0:
            return [
                await self.verify(obligation, proof_body, retrieval_hits)
                for obligation, proof_body, retrieval_hits in items
            ]

        elapsed_ms = int((time.perf_counter() - start) * 1000)
        per_item_elapsed_ms = max(1, elapsed_ms // len(items))
        return [
            ProofCheck(
                obligation_id=obligation.id,
                ok=True,
                proof_body=proof_body,
                verifier=self.name,
                verification_strength="local_lean_kernel_batch",
                kernel_verified=True,
                elapsed_ms=per_item_elapsed_ms,
                errors=[],
                retrieval_hits=retrieval_hits,
            )
            for obligation, proof_body, retrieval_hits in items
        ]

    async def verify(
        self,
        obligation: FormalObligation,
        proof_body: str,
        retrieval_hits: list[RetrievalHit],
    ) -> ProofCheck:
        start = time.perf_counter()
        candidate = splice_proof(obligation.formal_statement, proof_body)
        placeholder_errors = placeholder_proof_errors(candidate)
        if placeholder_errors:
            return ProofCheck(
                obligation_id=obligation.id,
                ok=False,
                proof_body=proof_body,
                verifier=self.name,
                verification_strength="local_lean_placeholder_rejected",
                kernel_verified=False,
                elapsed_ms=int((time.perf_counter() - start) * 1000),
                errors=placeholder_errors,
                retrieval_hits=retrieval_hits,
            )
        if shutil.which("lake") is None:
            return ProofCheck(
                obligation_id=obligation.id,
                ok=False,
                proof_body=proof_body,
                verifier=self.name,
                verification_strength="local_lean_unavailable",
                kernel_verified=False,
                elapsed_ms=int((time.perf_counter() - start) * 1000),
                errors=["lake executable not found on PATH"],
                retrieval_hits=retrieval_hits,
            )
        if self.project_root is None:
            return ProofCheck(
                obligation_id=obligation.id,
                ok=False,
                proof_body=proof_body,
                verifier=self.name,
                verification_strength="local_lean_unavailable",
                kernel_verified=False,
                elapsed_ms=int((time.perf_counter() - start) * 1000),
                errors=["no local Lean/Lake project found; set AI_STATISTICIAN_LEAN_PROJECT or --lean-project"],
                retrieval_hits=retrieval_hits,
            )
        with tempfile.TemporaryDirectory(prefix="ai_stat_lean_") as tmp:
            lean_file = Path(tmp) / f"{obligation.id}.lean"
            lean_file.write_text(candidate, encoding="utf-8")
            proc = None
            try:
                proc = await asyncio.create_subprocess_exec(
                    "lake",
                    "env",
                    "lean",
                    str(lean_file),
                    cwd=str(self.project_root),
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    start_new_session=True,
                )
                stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=self.timeout_s)
            except asyncio.TimeoutError:
                await _terminate_process_tree(proc)
                errors = [f"local Lean verification timed out after {self.timeout_s}s"]
                return ProofCheck(
                    obligation_id=obligation.id,
                    ok=False,
                    proof_body=proof_body,
                    verifier=self.name,
                    verification_strength="local_lean_timeout",
                    kernel_verified=False,
                    elapsed_ms=int((time.perf_counter() - start) * 1000),
                    errors=errors,
                    retrieval_hits=retrieval_hits,
                )
            except asyncio.CancelledError:
                await _terminate_process_tree(proc)
                raise
            except Exception as exc:
                return ProofCheck(
                    obligation_id=obligation.id,
                    ok=False,
                    proof_body=proof_body,
                    verifier=self.name,
                    verification_strength="local_lean_kernel",
                    kernel_verified=False,
                    elapsed_ms=int((time.perf_counter() - start) * 1000),
                    errors=[f"{type(exc).__name__}: {exc}"],
                    retrieval_hits=retrieval_hits,
                )
        output = (stdout or b"").decode(errors="replace").strip()
        error_output = (stderr or b"").decode(errors="replace").strip()
        errors = [line for line in (output + "\n" + error_output).splitlines() if line.strip()]
        ok = proc.returncode == 0
        return ProofCheck(
            obligation_id=obligation.id,
            ok=ok,
            proof_body=proof_body,
            verifier=self.name,
            verification_strength="local_lean_kernel",
            kernel_verified=ok,
            elapsed_ms=int((time.perf_counter() - start) * 1000),
            errors=[] if ok else errors,
            retrieval_hits=retrieval_hits,
        )


def _resolve_local_lean_project(project_root: str | Path | None) -> Path | None:
    candidates = (Path(project_root),) if project_root else tuple(
        path for path in DEFAULT_LOCAL_LEAN_PROJECTS if path is not None
    )
    for candidate in candidates:
        if (candidate / "lakefile.toml").exists() or (candidate / "lakefile.lean").exists():
            return candidate
    return None


def _batch_local_lean_code(candidates: list[tuple[str, str]]) -> str:
    imports: list[str] = []
    bodies: list[str] = []
    for index, (obligation_id, candidate) in enumerate(candidates, start=1):
        body_lines: list[str] = []
        for line in candidate.splitlines():
            if line.startswith("import "):
                if line not in imports:
                    imports.append(line)
            else:
                body_lines.append(line)
        namespace = f"O{index}_{_lean_identifier_suffix(obligation_id)}"
        bodies.append(
            "\n".join(
                [
                    f"namespace {namespace}",
                    "\n".join(body_lines).strip(),
                    f"end {namespace}",
                ]
            )
        )
    if not imports:
        imports = ["import Mathlib"]
    return "\n\n".join(imports + ["namespace AIStatisticianProofAudit", *bodies, "end AIStatisticianProofAudit"]) + "\n"


def _lean_identifier_suffix(value: str) -> str:
    cleaned = "".join(char if char.isalnum() or char == "_" else "_" for char in value)
    cleaned = cleaned.strip("_") or "obligation"
    if cleaned[0].isdigit():
        cleaned = "obligation_" + cleaned
    return cleaned
