from __future__ import annotations

import json
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .fingerprint import stable_hash


FORMAL_VERIFIER_REPLAY_REPAIR_PATCH_RERUN_CALIBRATION_SCHEMA_VERSION = 1


@dataclass(frozen=True)
class FormalVerifierReplayRepairPatchRerunCalibrationRow:
    schema_version: int
    rerun_calibration_id: str
    rerun_id: str
    rerun_attempt_id: str
    response_validation_id: str
    promotion_id: str
    replay_id: str
    route_id: str
    display_name: str
    target_theorem_name: str
    candidate_bridge_lemma_name: str
    attempted: bool
    local_lean_checked: bool
    local_lean_compiled: bool
    verification_strength: str
    patched_artifact_path: str
    artifact_placeholder_free: bool
    contains_patch_proposal_marker: bool
    residual_formal_gaps: tuple[str, ...]
    n_residual_formal_gaps: int
    patch_rerun_calibration_status: str
    full_route_proof_status: str
    proof_evidence_status: str
    next_action: str
    proof_evidence_boundary: str
    ok: bool
    errors: tuple[str, ...] = ()


def export_formal_verifier_replay_repair_patch_rerun_calibration(
    formal_verifier_replay_repair_patch_rerun_queue_dir: Path,
    formal_verifier_replay_repair_patch_rerun_attempt_dir: Path,
    out_dir: Path | None = None,
) -> dict[str, object]:
    """Calibrate patch-rerun attempts before any proof-ledger promotion."""

    errors: list[str] = []
    queue_manifest_path = (
        formal_verifier_replay_repair_patch_rerun_queue_dir
        / "formal_verifier_replay_repair_patch_rerun_queue_manifest.json"
    )
    attempt_manifest_path = (
        formal_verifier_replay_repair_patch_rerun_attempt_dir
        / "formal_verifier_replay_repair_patch_rerun_attempt_manifest.json"
    )
    queue_payload = _read_json(queue_manifest_path, errors)
    attempt_payload = _read_json(attempt_manifest_path, errors)
    queue_rows = [row for row in queue_payload.get("rows", []) if isinstance(row, dict)]
    attempt_rows = [row for row in attempt_payload.get("rows", []) if isinstance(row, dict)]
    attempts_by_rerun = {
        str(row.get("rerun_id", "")): row
        for row in attempt_rows
        if str(row.get("rerun_id", ""))
    }
    calibration_rows = [
        _calibration_row(row, attempt=attempts_by_rerun.get(str(row.get("rerun_id", "")), {}))
        for row in queue_rows
        if str(row.get("rerun_status", "")) == "READY_FOR_PATCH_REPLAY_CALIBRATION"
    ]
    by_status = Counter(row.patch_rerun_calibration_status for row in calibration_rows)
    payload: dict[str, object] = {
        "schema_version": FORMAL_VERIFIER_REPLAY_REPAIR_PATCH_RERUN_CALIBRATION_SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "formal_verifier_replay_repair_patch_rerun_queue_dir": str(
            formal_verifier_replay_repair_patch_rerun_queue_dir
        ),
        "formal_verifier_replay_repair_patch_rerun_queue_manifest": str(queue_manifest_path),
        "formal_verifier_replay_repair_patch_rerun_attempt_dir": str(
            formal_verifier_replay_repair_patch_rerun_attempt_dir
        ),
        "formal_verifier_replay_repair_patch_rerun_attempt_manifest": str(
            attempt_manifest_path
        ),
        "n_queue_rows": len(queue_rows),
        "n_attempt_rows": len(attempt_rows),
        "n_calibration_rows": len(calibration_rows),
        "n_ok": sum(1 for row in calibration_rows if row.ok),
        "n_attempted": sum(1 for row in calibration_rows if row.attempted),
        "n_local_lean_checked": sum(1 for row in calibration_rows if row.local_lean_checked),
        "n_local_lean_compiled": sum(
            1 for row in calibration_rows if row.local_lean_compiled
        ),
        "n_with_patch_proposal_marker": sum(
            1 for row in calibration_rows if row.contains_patch_proposal_marker
        ),
        "n_with_residual_formal_gaps": sum(
            1 for row in calibration_rows if row.residual_formal_gaps
        ),
        "n_full_route_kernel_verified": by_status.get("full_route_kernel_verified", 0),
        "n_compiled_patch_proposal_not_proof": by_status.get(
            "patch_artifact_compiles_patch_proposal_not_proof",
            0,
        ),
        "n_compiled_with_residual_gaps": by_status.get(
            "patch_artifact_compiles_with_residual_formal_gaps",
            0,
        ),
        "n_compile_failed": by_status.get("patch_artifact_compile_failed", 0),
        "n_awaiting_attempt": by_status.get("awaiting_patch_rerun_attempt", 0),
        "by_patch_rerun_calibration_status": dict(sorted(by_status.items())),
        "all_ok": not errors and all(row.ok for row in calibration_rows),
        "errors": errors,
        "rows": [asdict(row) for row in calibration_rows],
        "calibration_fingerprint": stable_hash([asdict(row) for row in calibration_rows]),
        "limitations": [
            "patch-rerun calibration rows are proof evidence only when status is full_route_kernel_verified",
            "compiled patch proposals with residual gaps remain non-evidence",
            "claim-ledger promotion requires this calibration plus response validation/promotion evidence",
        ],
    }
    if out_dir is not None:
        out_dir.mkdir(parents=True, exist_ok=True)
        (
            out_dir / "formal_verifier_replay_repair_patch_rerun_calibration_manifest.json"
        ).write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
        (
            out_dir / "formal_verifier_replay_repair_patch_rerun_calibration.jsonl"
        ).write_text(
            "\n".join(json.dumps(asdict(row), sort_keys=True) for row in calibration_rows)
            + ("\n" if calibration_rows else ""),
            encoding="utf-8",
        )
        (
            out_dir / "formal_verifier_replay_repair_patch_rerun_calibration.md"
        ).write_text(_markdown_report(payload), encoding="utf-8")
    return payload


def _calibration_row(
    queue_row: dict[str, Any],
    *,
    attempt: dict[str, Any],
) -> FormalVerifierReplayRepairPatchRerunCalibrationRow:
    errors: list[str] = []
    rerun_id = str(queue_row.get("rerun_id", ""))
    residual_gaps = _str_tuple(queue_row.get("residual_formal_gaps", []))
    attempted = bool(attempt)
    if not rerun_id:
        errors.append("rerun_id missing")
    if not str(queue_row.get("replay_id", "")):
        errors.append("replay_id missing")
    if not str(queue_row.get("route_id", "")):
        errors.append("route_id missing")
    if not str(queue_row.get("display_name", "")):
        errors.append("display_name missing")

    local_checked = bool(attempt.get("local_lean_checked", False))
    local_compiled = bool(attempt.get("local_lean_compiled", False))
    artifact_placeholder_free = bool(attempt.get("artifact_placeholder_free", False))
    contains_patch_marker = bool(attempt.get("contains_patch_proposal_marker", False))
    status = _calibration_status(
        attempted=attempted,
        local_checked=local_checked,
        local_compiled=local_compiled,
        artifact_placeholder_free=artifact_placeholder_free,
        residual_gaps=residual_gaps,
    )
    proof_evidence_status = (
        "FULL_ROUTE_KERNEL_VERIFIED_PROOF_EVIDENCE"
        if status == "full_route_kernel_verified"
        else "PATCH_RERUN_CALIBRATION_NOT_PROOF_EVIDENCE"
    )
    return FormalVerifierReplayRepairPatchRerunCalibrationRow(
        schema_version=FORMAL_VERIFIER_REPLAY_REPAIR_PATCH_RERUN_CALIBRATION_SCHEMA_VERSION,
        rerun_calibration_id=(
            "formal_verifier_replay_repair_patch_rerun_calibration:"
            f"{stable_hash([rerun_id, attempt, residual_gaps])[:16]}"
        ),
        rerun_id=rerun_id,
        rerun_attempt_id=str(attempt.get("rerun_attempt_id", "")),
        response_validation_id=str(queue_row.get("response_validation_id", "")),
        promotion_id=str(queue_row.get("promotion_id", "")),
        replay_id=str(queue_row.get("replay_id", "")),
        route_id=str(queue_row.get("route_id", "")),
        display_name=str(queue_row.get("display_name", "")),
        target_theorem_name=str(queue_row.get("target_theorem_name", "")),
        candidate_bridge_lemma_name=str(queue_row.get("candidate_bridge_lemma_name", "")),
        attempted=attempted,
        local_lean_checked=local_checked,
        local_lean_compiled=local_compiled,
        verification_strength=str(attempt.get("verification_strength", "")),
        patched_artifact_path=str(
            attempt.get("patched_artifact_path", queue_row.get("patched_artifact_path", ""))
        ),
        artifact_placeholder_free=artifact_placeholder_free,
        contains_patch_proposal_marker=contains_patch_marker,
        residual_formal_gaps=residual_gaps,
        n_residual_formal_gaps=len(residual_gaps),
        patch_rerun_calibration_status=status,
        full_route_proof_status=(
            "PROVED_BY_PATCH_RERUN_KERNEL"
            if status == "full_route_kernel_verified"
            else "UNPROVED_PATCH_RERUN_TARGET"
        ),
        proof_evidence_status=proof_evidence_status,
        next_action=_next_action(status),
        proof_evidence_boundary=(
            "This patch-rerun calibration row is proof evidence only when "
            "patch_rerun_calibration_status is full_route_kernel_verified. "
            "Compiled patch proposals, residual formal gaps, and missing attempts "
            "remain repair feedback."
        ),
        ok=not errors,
        errors=tuple(errors),
    )


def _calibration_status(
    *,
    attempted: bool,
    local_checked: bool,
    local_compiled: bool,
    artifact_placeholder_free: bool,
    residual_gaps: tuple[str, ...],
) -> str:
    if not attempted:
        return "awaiting_patch_rerun_attempt"
    if not local_checked:
        return "patch_rerun_awaiting_local_lean"
    if not local_compiled:
        return "patch_artifact_compile_failed"
    if not artifact_placeholder_free:
        return "patch_artifact_placeholder_reference_repair_needed"
    if residual_gaps:
        return "patch_artifact_compiles_with_residual_formal_gaps"
    return "full_route_kernel_verified"


def _next_action(status: str) -> str:
    return {
        "awaiting_patch_rerun_attempt": "run the queued patch artifact under local Lean or AXLE",
        "patch_rerun_awaiting_local_lean": "rerun with --lean-project to obtain kernel compile evidence",
        "patch_artifact_compile_failed": "return the complete source and exact Lean diagnostics to the proof agent",
        "patch_artifact_placeholder_reference_repair_needed": "return the complete source and verification result to the proof agent",
        "patch_artifact_compiles_with_residual_formal_gaps": "return the complete source and unresolved goals to the proof agent",
        "full_route_kernel_verified": "eligible for response validation and proof-ledger promotion evidence",
    }.get(status, "inspect patch-rerun calibration row")


def _read_json(path: Path, errors: list[str]) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        errors.append(f"missing JSON file: {path}")
        return {}
    except Exception as exc:
        errors.append(f"failed to parse {path}: {type(exc).__name__}: {exc}")
        return {}
    return payload if isinstance(payload, dict) else {}


def _str_tuple(value: Any) -> tuple[str, ...]:
    if isinstance(value, (list, tuple)):
        return tuple(str(item) for item in value if str(item))
    if str(value):
        return (str(value),)
    return ()


def _markdown_report(payload: dict[str, object]) -> str:
    lines = [
        "# Formal Verifier Repair Patch Rerun Calibration",
        "",
        f"- Queue manifest: `{payload.get('formal_verifier_replay_repair_patch_rerun_queue_manifest')}`",
        f"- Attempt manifest: `{payload.get('formal_verifier_replay_repair_patch_rerun_attempt_manifest')}`",
        f"- Calibration rows: {payload.get('n_ok')}/{payload.get('n_calibration_rows')} audit-clean",
        f"- Local Lean compiled: {payload.get('n_local_lean_compiled')}",
        f"- Full-route kernel verified: {payload.get('n_full_route_kernel_verified')}",
        f"- Compiled patch proposals: {payload.get('n_compiled_patch_proposal_not_proof')}",
        "",
        "These rows are proof evidence only at `full_route_kernel_verified`.",
        "",
        "## Rows",
        "",
    ]
    rows = payload.get("rows", [])
    if not isinstance(rows, list) or not rows:
        lines.append("No ready patch-rerun queue rows were calibrated.")
    else:
        for row in rows[:30]:
            if not isinstance(row, dict):
                continue
            lines.append(
                f"- `{row.get('display_name')}` ({row.get('patch_rerun_calibration_status')}): "
                f"residual_gaps={row.get('n_residual_formal_gaps')}"
            )
            lines.append(f"  next: {row.get('next_action')}")
            lines.append(f"  boundary: {row.get('proof_evidence_boundary')}")
    lines.extend(["", "## Honesty Boundary", ""])
    for item in payload.get("limitations", []):
        lines.append(f"- {item}")
    return "\n".join(lines) + "\n"
