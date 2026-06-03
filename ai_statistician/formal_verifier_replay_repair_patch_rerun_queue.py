from __future__ import annotations

import json
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .fingerprint import stable_hash


FORMAL_VERIFIER_REPLAY_REPAIR_PATCH_RERUN_QUEUE_SCHEMA_VERSION = 1


@dataclass(frozen=True)
class FormalVerifierReplayRepairPatchRerunQueueRow:
    schema_version: int
    rerun_id: str
    response_validation_id: str
    promotion_id: str
    prompt_packet_id: str
    execution_id: str
    application_id: str
    replay_id: str
    route_id: str
    display_name: str
    target_theorem_name: str
    candidate_bridge_lemma_name: str
    source_acceptance_status: str
    promotion_status: str
    patched_artifact_path: str
    patched_artifact_exists: bool
    changed_lean_declarations: tuple[str, ...]
    residual_formal_gaps: tuple[str, ...]
    rerun_commands: tuple[str, ...]
    replay_attempt_manifest_out: str
    replay_calibration_manifest_out: str
    rerun_status: str
    owner_agent: str
    priority: str
    required_gate: str
    proof_evidence_status: str
    proof_evidence_boundary: str
    ok: bool
    errors: tuple[str, ...] = ()


def export_formal_verifier_replay_repair_patch_rerun_queue(
    formal_verifier_replay_repair_patch_response_validation_dir: Path,
    formal_verifier_replay_repair_patch_response_promotion_dir: Path,
    out_dir: Path | None = None,
) -> dict[str, object]:
    """Export replay-calibration work items for validated repair patch proposals."""

    errors: list[str] = []
    validation_manifest_path = (
        formal_verifier_replay_repair_patch_response_validation_dir
        / "formal_verifier_replay_repair_patch_response_validation_manifest.json"
    )
    promotion_manifest_path = (
        formal_verifier_replay_repair_patch_response_promotion_dir
        / "formal_verifier_replay_repair_patch_response_promotion_manifest.json"
    )
    validation_payload = _read_json(validation_manifest_path, errors)
    promotion_payload = _read_json(promotion_manifest_path, errors)
    validation_rows = [
        row for row in validation_payload.get("rows", []) if isinstance(row, dict)
    ]
    promotion_rows = [
        row for row in promotion_payload.get("rows", []) if isinstance(row, dict)
    ]
    promotions_by_validation = {
        str(row.get("response_validation_id", "")): row
        for row in promotion_rows
        if str(row.get("response_validation_id", ""))
    }
    patch_rows = [
        row
        for row in validation_rows
        if str(row.get("acceptance_status", ""))
        == "PATCH_PROPOSAL_RECORDED_NOT_PROOF_EVIDENCE"
    ]
    queue_rows = [
        _rerun_row(
            row,
            promotion_row=promotions_by_validation.get(
                str(row.get("response_validation_id", "")),
                {},
            ),
            validation_dir=formal_verifier_replay_repair_patch_response_validation_dir,
            out_dir=out_dir,
        )
        for row in patch_rows
    ]
    by_status = Counter(row.rerun_status for row in queue_rows)
    payload: dict[str, object] = {
        "schema_version": FORMAL_VERIFIER_REPLAY_REPAIR_PATCH_RERUN_QUEUE_SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "formal_verifier_replay_repair_patch_response_validation_dir": str(
            formal_verifier_replay_repair_patch_response_validation_dir
        ),
        "formal_verifier_replay_repair_patch_response_validation_manifest": str(
            validation_manifest_path
        ),
        "formal_verifier_replay_repair_patch_response_promotion_dir": str(
            formal_verifier_replay_repair_patch_response_promotion_dir
        ),
        "formal_verifier_replay_repair_patch_response_promotion_manifest": str(
            promotion_manifest_path
        ),
        "n_response_validation_rows": len(validation_rows),
        "n_patch_proposal_rows": len(patch_rows),
        "n_rerun_queue_items": len(queue_rows),
        "n_ready_for_patch_replay": by_status.get("READY_FOR_PATCH_REPLAY_CALIBRATION", 0),
        "n_blocked": sum(1 for row in queue_rows if row.rerun_status.startswith("BLOCKED_")),
        "n_with_patched_artifact": sum(1 for row in queue_rows if row.patched_artifact_exists),
        "n_with_rerun_commands": sum(1 for row in queue_rows if row.rerun_commands),
        "n_ok": sum(1 for row in queue_rows if row.ok),
        "all_ok": not errors and all(row.ok for row in queue_rows),
        "errors": errors,
        "by_rerun_status": dict(sorted(by_status.items())),
        "rows": [asdict(row) for row in queue_rows],
        "rerun_queue_fingerprint": stable_hash([asdict(row) for row in queue_rows]),
        "limitations": [
            "patch-rerun queue rows are executable work contracts, not proof evidence",
            "patched artifacts must be rerun through formal-verifier replay attempts and calibration",
            "proof-ledger promotion still requires full_route_kernel_verified calibration",
        ],
    }
    if out_dir is not None:
        out_dir.mkdir(parents=True, exist_ok=True)
        (
            out_dir / "formal_verifier_replay_repair_patch_rerun_queue_manifest.json"
        ).write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
        (out_dir / "formal_verifier_replay_repair_patch_rerun_queue.jsonl").write_text(
            "\n".join(json.dumps(asdict(row), sort_keys=True) for row in queue_rows)
            + ("\n" if queue_rows else ""),
            encoding="utf-8",
        )
        (out_dir / "formal_verifier_replay_repair_patch_rerun_queue.md").write_text(
            _markdown_report(payload),
            encoding="utf-8",
        )
    return payload


def _rerun_row(
    row: dict[str, Any],
    *,
    promotion_row: dict[str, Any],
    validation_dir: Path,
    out_dir: Path | None,
) -> FormalVerifierReplayRepairPatchRerunQueueRow:
    errors: list[str] = []
    response_validation_id = str(row.get("response_validation_id", ""))
    replay_id = str(row.get("replay_id", ""))
    patched_artifact_path = str(row.get("patched_artifact_path", ""))
    artifact_exists = _path_exists(patched_artifact_path, validation_dir)
    changed_declarations = _str_tuple(row.get("changed_lean_declarations", []))
    residual_formal_gaps = _str_tuple(row.get("residual_formal_gaps", []))
    rerun_commands = _str_tuple(row.get("rerun_commands", []))
    promotion_id = str(promotion_row.get("promotion_id", ""))
    promotion_status = str(promotion_row.get("promotion_status", ""))
    if not promotion_row:
        errors.append("matching promotion row missing")
    if promotion_status != "PATCH_PROPOSAL_NEEDS_REPLAY_CALIBRATION":
        errors.append(f"promotion_status is not patch replay eligible: {promotion_status}")
    if not patched_artifact_path:
        errors.append("patched_artifact_path missing")
    elif not artifact_exists:
        errors.append(f"patched_artifact_path does not exist: {patched_artifact_path}")
    if not changed_declarations:
        errors.append("changed_lean_declarations missing")
    if not rerun_commands:
        errors.append("rerun_commands missing")
    if not replay_id:
        errors.append("replay_id missing")
    status = "READY_FOR_PATCH_REPLAY_CALIBRATION" if not errors else "BLOCKED_PATCH_REPLAY_INPUT"
    base_out = out_dir or validation_dir
    attempt_manifest_out = str(
        base_out / "patch_replay_attempts" / "formal_verifier_replay_attempt_manifest.json"
    )
    calibration_manifest_out = str(
        base_out
        / "patch_replay_calibration"
        / "formal_verifier_replay_calibration_manifest.json"
    )
    return FormalVerifierReplayRepairPatchRerunQueueRow(
        schema_version=FORMAL_VERIFIER_REPLAY_REPAIR_PATCH_RERUN_QUEUE_SCHEMA_VERSION,
        rerun_id=(
            "formal_verifier_replay_repair_patch_rerun:"
            f"{stable_hash([response_validation_id, promotion_id, patched_artifact_path])[:16]}"
        ),
        response_validation_id=response_validation_id,
        promotion_id=promotion_id,
        prompt_packet_id=str(row.get("prompt_packet_id", "")),
        execution_id=str(row.get("execution_id", "")),
        application_id=str(row.get("application_id", "")),
        replay_id=replay_id,
        route_id=str(row.get("route_id", "")),
        display_name=str(row.get("display_name", "")),
        target_theorem_name=str(row.get("target_theorem_name", "")),
        candidate_bridge_lemma_name=str(row.get("candidate_bridge_lemma_name", "")),
        source_acceptance_status=str(row.get("acceptance_status", "")),
        promotion_status=promotion_status,
        patched_artifact_path=patched_artifact_path,
        patched_artifact_exists=artifact_exists,
        changed_lean_declarations=changed_declarations,
        residual_formal_gaps=residual_formal_gaps,
        rerun_commands=rerun_commands,
        replay_attempt_manifest_out=attempt_manifest_out,
        replay_calibration_manifest_out=calibration_manifest_out,
        rerun_status=status,
        owner_agent="formal_verifier",
        priority="high",
        required_gate=(
            "rerun the patched artifact through formal-verifier replay attempts and "
            "formal-verifier replay calibration; promote only if calibration is "
            "full_route_kernel_verified"
        ),
        proof_evidence_status="PATCH_RERUN_QUEUE_NOT_PROOF_EVIDENCE",
        proof_evidence_boundary=(
            "This row is a replay-calibration work item for a patch proposal. "
            "It is not theorem proof evidence until the patched route calibrates "
            "as full_route_kernel_verified with kernel_verified=true."
        ),
        ok=not errors,
        errors=tuple(errors),
    )


def _path_exists(raw: str, base_dir: Path) -> bool:
    if not raw:
        return False
    path = Path(raw)
    if path.exists():
        return True
    if path.is_absolute():
        return False
    return (base_dir / path).exists() or (base_dir.parent / path).exists()


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
        "# AI Statistical Theory Lab Formal Verifier Patch Rerun Queue",
        "",
        f"- Response validation: `{payload.get('formal_verifier_replay_repair_patch_response_validation_manifest')}`",
        f"- Response promotion: `{payload.get('formal_verifier_replay_repair_patch_response_promotion_manifest')}`",
        f"- Queue items: {payload.get('n_ok')}/{payload.get('n_rerun_queue_items')} audit-clean",
        f"- Ready for patch replay: {payload.get('n_ready_for_patch_replay')}",
        "",
        "These rows are replay-calibration work items, not proof evidence.",
        "",
        "## Queue",
        "",
    ]
    rows = payload.get("rows", [])
    if not isinstance(rows, list) or not rows:
        lines.append("No patch proposals require replay calibration.")
        return "\n".join(lines) + "\n"
    for row in rows:
        if not isinstance(row, dict):
            continue
        lines.extend(
            [
                f"### {row.get('display_name') or row.get('rerun_id')}",
                "",
                f"- Status: `{row.get('rerun_status')}`",
                f"- Target theorem: `{row.get('target_theorem_name')}`",
                f"- Candidate bridge: `{row.get('candidate_bridge_lemma_name')}`",
                f"- Patched artifact: `{row.get('patched_artifact_path')}`",
                f"- Changed declarations: {', '.join(row.get('changed_lean_declarations') or [])}",
                f"- Boundary: {row.get('proof_evidence_boundary')}",
                "",
            ]
        )
    return "\n".join(lines) + "\n"
