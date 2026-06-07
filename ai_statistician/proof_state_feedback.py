from __future__ import annotations

import re
import shutil
import subprocess
import tempfile
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Protocol, Sequence

from .fingerprint import stable_hash
from .research_schema import FormalSubclaim


PROOF_STATE_FEEDBACK_STATUS = "PROOF_STATE_FEEDBACK_NOT_PROOF_EVIDENCE"
PROOF_STATE_FEEDBACK_BOUNDARY = (
    "Proof-state feedback, Lean diagnostics, residual goals, and LSP/MCP tool "
    "requests are diagnostic/search evidence only. They do not prove a theorem "
    "unless the intended formal claim is separately accepted by AXLE or a local "
    "Lean kernel verifier without placeholders."
)

PLACEHOLDER_RE = re.compile(r"\b(sorry|admit|axiom)\b")
FORMAL_GAP_RE = re.compile(r"\bFORMAL_GAP\b|h_frontier_missing")


@dataclass(frozen=True)
class ProofStateFeedbackRow:
    schema_version: int
    feedback_id: str
    subclaim_id: str
    proof_obligation_id: str
    claim_type: str
    provider_name: str
    provider_preferences: tuple[str, ...]
    requested_tools: tuple[str, ...]
    attempt_status: str
    diagnostics: tuple[str, ...]
    residual_goals: tuple[str, ...]
    route_revision_recommended: bool
    subclaim_status: str
    subclaim_kernel_verified: bool
    local_lean_checked: bool
    local_lean_returncode: int | None
    proof_evidence_status: str
    proof_evidence_boundary: str
    created_at: str


class ProofStateFeedbackProvider(Protocol):
    name: str

    def inspect(self, subclaims: Sequence[FormalSubclaim]) -> list[ProofStateFeedbackRow]:
        ...


class LocalLeanProofStateFeedbackProvider:
    """Runtime proof-state feedback via local Lean diagnostics when possible.

    This is not a Lean LSP MCP implementation. It is the local fallback side of
    the same proof-state provider contract: it classifies placeholder/formal-gap
    skeletons without executing them, and runs `lake env lean` only on complete
    non-placeholder Lean text.
    """

    name = "local_lean_proof_state_feedback"

    def __init__(
        self,
        *,
        project_root: str | Path | None = None,
        timeout_s: int = 90,
        lean_command: Sequence[str] | None = None,
    ) -> None:
        self.project_root = Path(project_root).resolve() if project_root else None
        self.timeout_s = int(timeout_s)
        self.lean_command = tuple(lean_command) if lean_command is not None else self._default_lean_command()

    def inspect(self, subclaims: Sequence[FormalSubclaim]) -> list[ProofStateFeedbackRow]:
        return [self._inspect_subclaim(row) for row in subclaims]

    def _inspect_subclaim(self, subclaim: FormalSubclaim) -> ProofStateFeedbackRow:
        statement = str(subclaim.lean_statement or "").strip()
        diagnostics: list[str] = []
        residual_goals: list[str] = []
        attempt_status = ""
        checked = False
        returncode: int | None = None
        if subclaim.kernel_verified:
            attempt_status = "already_kernel_verified_subclaim"
            diagnostics.append(
                "subclaim already has kernel_verified=true from the formal verifier; "
                "proof-state feedback is not adding proof evidence"
            )
        elif not statement:
            attempt_status = "missing_lean_statement"
            diagnostics.append("subclaim has no Lean statement to inspect")
            residual_goals.extend(_residual_goals_for_subclaim(subclaim, "missing Lean statement"))
        elif PLACEHOLDER_RE.search(statement):
            attempt_status = "placeholder_blocked"
            diagnostics.append("Lean statement contains sorry/admit/axiom; proof-state provider did not run it")
            residual_goals.extend(_residual_goals_for_subclaim(subclaim, "placeholder Lean statement"))
        elif FORMAL_GAP_RE.search(statement):
            attempt_status = "formal_gap_scaffold_blocked"
            diagnostics.append(
                "Lean statement is a formal-gap scaffold with h_frontier_missing/FORMAL_GAP markers; "
                "diagnostic feedback records residual goals instead of treating it as proof"
            )
            residual_goals.extend(_residual_goals_for_subclaim(subclaim, "formal-gap scaffold"))
        elif not _looks_like_lean_command(statement):
            attempt_status = "non_lean_statement"
            diagnostics.append("subclaim text is not a complete Lean command")
            diagnostics.append(f"statement_excerpt={statement[:160]!r}")
            residual_goals.extend(_residual_goals_for_subclaim(subclaim, "non-Lean statement"))
        elif not self.lean_command:
            attempt_status = "local_lean_unavailable"
            diagnostics.append("local Lean command unavailable; configure lake/lean before live proof-state diagnostics")
            residual_goals.extend(_residual_goals_for_subclaim(subclaim, "local Lean unavailable"))
        else:
            result = self._run_local_lean(statement)
            checked = True
            returncode = int(result["returncode"])
            diagnostics.extend(result["diagnostics"])
            attempt_status = str(result["attempt_status"])
            if returncode != 0:
                residual_goals.extend(
                    _residual_goals_for_subclaim(
                        subclaim,
                        str(result.get("first_error") or "local Lean failed"),
                    )
                )
        residual_goals = sorted(dict.fromkeys(goal for goal in residual_goals if goal))
        return ProofStateFeedbackRow(
            schema_version=1,
            feedback_id="proof_state_feedback:" + stable_hash(
                [
                    subclaim.id,
                    subclaim.proof_obligation_id or "",
                    attempt_status,
                    diagnostics[:3],
                    residual_goals[:5],
                ]
            )[:20],
            subclaim_id=subclaim.id,
            proof_obligation_id=str(subclaim.proof_obligation_id or ""),
            claim_type=str(subclaim.claim_type),
            provider_name=self.name,
            provider_preferences=(
                "lean_lsp_mcp",
                "local_lean_proof_state_adapter",
                "local.lake_env_lean",
            ),
            requested_tools=("lean_goal", "lean_diagnostic_messages"),
            attempt_status=attempt_status,
            diagnostics=tuple(diagnostics or ["no proof-state diagnostic emitted"]),
            residual_goals=tuple(residual_goals),
            route_revision_recommended=attempt_status
            in {
                "formal_gap_scaffold_blocked",
                "local_lean_failed",
                "missing_lean_statement",
                "non_lean_statement",
                "placeholder_blocked",
            },
            subclaim_status=str(subclaim.status),
            subclaim_kernel_verified=bool(subclaim.kernel_verified),
            local_lean_checked=checked,
            local_lean_returncode=returncode,
            proof_evidence_status=PROOF_STATE_FEEDBACK_STATUS,
            proof_evidence_boundary=PROOF_STATE_FEEDBACK_BOUNDARY,
            created_at=datetime.now(timezone.utc).isoformat(),
        )

    def _default_lean_command(self) -> tuple[str, ...]:
        if self.project_root is not None and shutil.which("lake") is not None:
            return ("lake", "env", "lean")
        lean = shutil.which("lean")
        return (lean,) if lean else ()

    def _run_local_lean(self, statement: str) -> dict[str, Any]:
        with tempfile.TemporaryDirectory(prefix="ai_stat_proof_state_") as tmp:
            lean_file = Path(tmp) / "ProofStateFeedback.lean"
            lean_file.write_text(_lean_source(statement), encoding="utf-8")
            command = (*self.lean_command, str(lean_file))
            try:
                proc = subprocess.run(
                    command,
                    cwd=str(self.project_root) if self.project_root is not None else None,
                    text=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    timeout=self.timeout_s,
                    check=False,
                )
            except subprocess.TimeoutExpired as exc:
                return {
                    "attempt_status": "local_lean_failed",
                    "returncode": -1,
                    "diagnostics": [f"local Lean proof-state check timed out after {self.timeout_s}s: {exc}"],
                    "first_error": "local Lean timeout",
                }
            except Exception as exc:
                return {
                    "attempt_status": "local_lean_failed",
                    "returncode": -1,
                    "diagnostics": [f"local Lean proof-state invocation failed: {type(exc).__name__}: {exc}"],
                    "first_error": str(exc),
                }
        combined = "\n".join(item for item in (proc.stdout, proc.stderr) if item).strip()
        diagnostics = _diagnostic_lines(combined)
        return {
            "attempt_status": "local_lean_scaffold_accepted" if proc.returncode == 0 else "local_lean_failed",
            "returncode": proc.returncode,
            "diagnostics": diagnostics or [f"local Lean exited with return code {proc.returncode}"],
            "first_error": diagnostics[0] if diagnostics and proc.returncode != 0 else "",
        }


def proof_state_feedback_row_to_json(row: ProofStateFeedbackRow) -> dict[str, Any]:
    return asdict(row)


def _residual_goals_for_subclaim(subclaim: FormalSubclaim, reason: str) -> list[str]:
    rows: list[str] = []
    if subclaim.gap_reason:
        rows.append(str(subclaim.gap_reason))
    rows.extend(str(error) for error in subclaim.errors[:3])
    if subclaim.proof_dependencies:
        rows.append("review proof dependencies: " + ", ".join(subclaim.proof_dependencies[:5]))
    if subclaim.primitive_formal_source_hits:
        rows.append(
            "bridge primitives: "
            + ", ".join(sorted(str(key) for key in subclaim.primitive_formal_source_hits.keys())[:8])
        )
    if not rows:
        rows.append(reason)
    return rows


def _looks_like_lean_command(statement: str) -> bool:
    stripped = statement.lstrip()
    return stripped.startswith(("theorem ", "lemma ", "example ", "def ", "abbrev "))


def _lean_source(statement: str) -> str:
    if statement.lstrip().startswith("import "):
        return statement
    return "import Mathlib\n\n" + statement + "\n"


def _diagnostic_lines(text: str, *, limit: int = 12) -> list[str]:
    if not text:
        return []
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    interesting = [
        line
        for line in lines
        if any(
            marker in line.lower()
            for marker in (
                "error",
                "warning",
                "unsolved goals",
                "unknown identifier",
                "failed",
                "type mismatch",
            )
        )
    ]
    return (interesting or lines)[:limit]
