from __future__ import annotations

import json
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .fingerprint import stable_hash


FORMAL_VERIFIER_REPLAY_REPAIR_PATCH_RERUN_RESIDUAL_FOLLOWUP_QUEUE_SCHEMA_VERSION = 1
RESIDUAL_PATCH_ACCEPTANCE_STATUS = (
    "RESIDUAL_PATCH_PROPOSAL_RECORDED_NOT_PROOF_EVIDENCE"
)
SOURCE_DISCOVERY_ACCEPTANCE_STATUS = (
    "SOURCE_DISCOVERY_RESPONSE_RECORDED_NOT_PROOF_EVIDENCE"
)


@dataclass(frozen=True)
class FormalVerifierReplayRepairPatchRerunResidualFollowupQueueRow:
    schema_version: int
    followup_id: str
    residual_response_validation_id: str
    prompt_packet_id: str
    residual_obligation_id: str
    rerun_calibration_id: str
    rerun_id: str
    rerun_attempt_id: str
    replay_id: str
    route_id: str
    display_name: str
    target_theorem_name: str
    candidate_bridge_lemma_name: str
    residual_gap: str
    action_class: str
    source_acceptance_status: str
    response_present: bool
    response_contract_ok: bool
    proposed_lean_artifact_path: str
    proposed_artifact_exists: bool
    changed_lean_declarations: tuple[str, ...]
    used_proof_bank_obligations: tuple[str, ...]
    used_local_declarations: tuple[str, ...]
    source_discovery_queries: tuple[str, ...]
    remaining_residual_formal_gaps: tuple[str, ...]
    followup_kind: str
    followup_status: str
    owner_agent: str
    priority: str
    required_gate: str
    execution_commands: tuple[str, ...]
    proof_evidence_status: str
    proof_evidence_boundary: str
    ok: bool
    errors: tuple[str, ...] = ()


def export_formal_verifier_replay_repair_patch_rerun_residual_followup_queue(
    formal_verifier_replay_repair_patch_rerun_residual_response_validation_dir: Path,
    out_dir: Path | None = None,
) -> dict[str, object]:
    """Queue follow-up work from validated residual worker responses.

    The queue consumes validation rows that were accepted as non-proof work:
    residual patch proposals and source-discovery responses. It does not
    promote theorem evidence; it only makes the next operational action
    auditable.
    """

    errors: list[str] = []
    validation_manifest_path = (
        formal_verifier_replay_repair_patch_rerun_residual_response_validation_dir
        / "formal_verifier_replay_repair_patch_rerun_residual_response_validation_manifest.json"
    )
    validation_payload = _read_json(validation_manifest_path, errors)
    validation_rows = [
        row for row in validation_payload.get("rows", []) if isinstance(row, dict)
    ]
    actionable_rows = [
        row
        for row in validation_rows
        if str(row.get("acceptance_status", ""))
        in {RESIDUAL_PATCH_ACCEPTANCE_STATUS, SOURCE_DISCOVERY_ACCEPTANCE_STATUS}
    ]
    queue_rows = [
        _followup_row(
            row,
            validation_dir=formal_verifier_replay_repair_patch_rerun_residual_response_validation_dir,
        )
        for row in actionable_rows
    ]
    by_followup_kind = Counter(row.followup_kind for row in queue_rows)
    by_followup_status = Counter(row.followup_status for row in queue_rows)
    by_action_class = Counter(row.action_class for row in queue_rows)
    payload: dict[str, object] = {
        "schema_version": (
            FORMAL_VERIFIER_REPLAY_REPAIR_PATCH_RERUN_RESIDUAL_FOLLOWUP_QUEUE_SCHEMA_VERSION
        ),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "formal_verifier_replay_repair_patch_rerun_residual_response_validation_dir": str(
            formal_verifier_replay_repair_patch_rerun_residual_response_validation_dir
        ),
        "formal_verifier_replay_repair_patch_rerun_residual_response_validation_manifest": str(
            validation_manifest_path
        ),
        "n_response_validation_rows": len(validation_rows),
        "n_followup_items": len(queue_rows),
        "n_ready": sum(1 for row in queue_rows if row.followup_status.startswith("READY_")),
        "n_blocked": sum(
            1 for row in queue_rows if row.followup_status.startswith("BLOCKED_")
        ),
        "n_patch_rerun_items": by_followup_kind.get("residual_patch_rerun", 0),
        "n_source_discovery_items": by_followup_kind.get(
            "residual_source_discovery",
            0,
        ),
        "n_with_artifact": sum(
            1 for row in queue_rows if row.proposed_artifact_exists
        ),
        "n_with_source_queries": sum(
            1
            for row in queue_rows
            if row.followup_kind == "residual_source_discovery"
            and row.source_discovery_queries
        ),
        "n_ok": sum(1 for row in queue_rows if row.ok),
        "all_ok": not errors and all(row.ok for row in queue_rows),
        "errors": errors,
        "by_followup_kind": dict(sorted(by_followup_kind.items())),
        "by_followup_status": dict(sorted(by_followup_status.items())),
        "by_action_class": dict(sorted(by_action_class.items())),
        "rows": [asdict(row) for row in queue_rows],
        "followup_queue_fingerprint": stable_hash([asdict(row) for row in queue_rows]),
        "limitations": [
            "residual follow-up queue rows are operational work items, not theorem proof evidence",
            "residual patch proposals still require patch-rerun attempts and full-route kernel calibration",
            "source-discovery follow-ups only expand retrieval/source coverage; they do not close formal gaps",
        ],
    }
    if out_dir is not None:
        out_dir.mkdir(parents=True, exist_ok=True)
        (
            out_dir
            / "formal_verifier_replay_repair_patch_rerun_residual_followup_queue_manifest.json"
        ).write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
        (
            out_dir
            / "formal_verifier_replay_repair_patch_rerun_residual_followup_queue.jsonl"
        ).write_text(
            "\n".join(json.dumps(asdict(row), sort_keys=True) for row in queue_rows)
            + ("\n" if queue_rows else ""),
            encoding="utf-8",
        )
        (
            out_dir
            / "formal_verifier_replay_repair_patch_rerun_residual_followup_queue.md"
        ).write_text(_markdown_report(payload), encoding="utf-8")
    return payload


def _followup_row(
    row: dict[str, Any],
    *,
    validation_dir: Path,
) -> FormalVerifierReplayRepairPatchRerunResidualFollowupQueueRow:
    errors: list[str] = []
    validation_id = str(row.get("residual_response_validation_id", ""))
    prompt_packet_id = str(row.get("prompt_packet_id", ""))
    residual_obligation_id = str(row.get("residual_obligation_id", ""))
    acceptance_status = str(row.get("acceptance_status", ""))
    response_present = bool(row.get("response_present", False))
    response_contract_ok = bool(row.get("response_contract_ok", False))
    proposed_artifact_path = str(row.get("proposed_lean_artifact_path", ""))
    proposed_artifact_exists = _path_exists(proposed_artifact_path, validation_dir)
    changed_declarations = _str_tuple(row.get("changed_lean_declarations", []))
    proof_bank_obligations = _str_tuple(row.get("used_proof_bank_obligations", []))
    local_declarations = _str_tuple(row.get("used_local_declarations", []))
    source_queries = _str_tuple(row.get("source_discovery_queries", []))
    remaining_gaps = _str_tuple(row.get("remaining_residual_formal_gaps", []))
    rerun_commands = _str_tuple(row.get("rerun_commands", []))

    if not validation_id:
        errors.append("residual_response_validation_id missing")
    if not prompt_packet_id:
        errors.append("prompt_packet_id missing")
    if not residual_obligation_id:
        errors.append("residual_obligation_id missing")
    if not response_present:
        errors.append("response_present is false")
    if not response_contract_ok:
        errors.append("response_contract_ok is false")

    if acceptance_status == SOURCE_DISCOVERY_ACCEPTANCE_STATUS:
        followup_kind = "residual_source_discovery"
        owner_agent = "rag_retrieval"
        priority = "medium"
        required_gate = (
            "expand primitive-source coverage and proof-bank source discovery, then "
            "rerun residual prompt-packet generation and response validation"
        )
        execution_commands = (
            "rerun primitive-source coverage/proof-bank source discovery with the "
            "expanded source registry for the listed source_discovery_queries",
        )
        if not source_queries:
            errors.append("source_discovery_queries missing")
        status = (
            "READY_FOR_RESIDUAL_SOURCE_DISCOVERY"
            if not errors
            else "BLOCKED_RESIDUAL_SOURCE_DISCOVERY_INPUT"
        )
    else:
        followup_kind = "residual_patch_rerun"
        owner_agent = "formal_verifier"
        priority = "high"
        required_gate = (
            "rerun the residual patch proposal through patch-rerun attempts and "
            "patch-rerun calibration; treat it as proof only if calibration is "
            "full_route_kernel_verified with kernel_verified=true and no remaining "
            "residual formal gaps"
        )
        execution_commands = rerun_commands
        if not proposed_artifact_path:
            errors.append("proposed_lean_artifact_path missing")
        elif not proposed_artifact_exists:
            errors.append(
                f"proposed_lean_artifact_path does not exist: {proposed_artifact_path}"
            )
        if not changed_declarations:
            errors.append("changed_lean_declarations missing")
        if not rerun_commands:
            errors.append("rerun_commands missing")
        status = (
            "READY_FOR_RESIDUAL_PATCH_RERUN"
            if not errors
            else "BLOCKED_RESIDUAL_PATCH_RERUN_INPUT"
        )

    return FormalVerifierReplayRepairPatchRerunResidualFollowupQueueRow(
        schema_version=(
            FORMAL_VERIFIER_REPLAY_REPAIR_PATCH_RERUN_RESIDUAL_FOLLOWUP_QUEUE_SCHEMA_VERSION
        ),
        followup_id=(
            "formal_verifier_replay_repair_patch_rerun_residual_followup:"
            f"{stable_hash([validation_id, prompt_packet_id, residual_obligation_id, followup_kind])[:16]}"
        ),
        residual_response_validation_id=validation_id,
        prompt_packet_id=prompt_packet_id,
        residual_obligation_id=residual_obligation_id,
        rerun_calibration_id=str(row.get("rerun_calibration_id", "")),
        rerun_id=str(row.get("rerun_id", "")),
        rerun_attempt_id=str(row.get("rerun_attempt_id", "")),
        replay_id=str(row.get("replay_id", "")),
        route_id=str(row.get("route_id", "")),
        display_name=str(row.get("display_name", "")),
        target_theorem_name=str(row.get("target_theorem_name", "")),
        candidate_bridge_lemma_name=str(row.get("candidate_bridge_lemma_name", "")),
        residual_gap=str(row.get("residual_gap", "")),
        action_class=str(row.get("action_class", "")),
        source_acceptance_status=acceptance_status,
        response_present=response_present,
        response_contract_ok=response_contract_ok,
        proposed_lean_artifact_path=proposed_artifact_path,
        proposed_artifact_exists=proposed_artifact_exists,
        changed_lean_declarations=changed_declarations,
        used_proof_bank_obligations=proof_bank_obligations,
        used_local_declarations=local_declarations,
        source_discovery_queries=source_queries,
        remaining_residual_formal_gaps=remaining_gaps,
        followup_kind=followup_kind,
        followup_status=status,
        owner_agent=owner_agent,
        priority=priority,
        required_gate=required_gate,
        execution_commands=execution_commands,
        proof_evidence_status="RESIDUAL_FOLLOWUP_QUEUE_NOT_PROOF_EVIDENCE",
        proof_evidence_boundary=(
            "This residual follow-up queue row is an operational work item, not "
            "theorem proof evidence. It becomes proof-relevant only after the "
            "follow-up is rerun through patch-rerun calibration and accepted as "
            "full_route_kernel_verified with kernel_verified=true and no remaining "
            "residual formal gaps."
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
        "# Formal Verifier Patch Rerun Residual Follow-up Queue",
        "",
        f"- Residual response validation manifest: `{payload.get('formal_verifier_replay_repair_patch_rerun_residual_response_validation_manifest')}`",
        f"- Follow-up items: {payload.get('n_followup_items')}",
        f"- Ready: {payload.get('n_ready')}",
        f"- Blocked: {payload.get('n_blocked')}",
        f"- Patch rerun items: {payload.get('n_patch_rerun_items')}",
        f"- Source-discovery items: {payload.get('n_source_discovery_items')}",
        f"- With artifacts: {payload.get('n_with_artifact')}",
        f"- With source queries: {payload.get('n_with_source_queries')}",
        f"- All OK: {payload.get('all_ok')}",
        f"- Fingerprint: `{payload.get('followup_queue_fingerprint')}`",
        "",
        "## Items",
        "",
    ]
    for row in payload.get("rows", []):
        if not isinstance(row, dict):
            continue
        lines.append(
            f"- `{row.get('display_name')}` -> `{row.get('residual_gap')}` "
            f"({row.get('followup_status')}): {row.get('followup_kind')}"
        )
        if row.get("proposed_lean_artifact_path"):
            lines.append(f"  artifact: `{row.get('proposed_lean_artifact_path')}`")
        queries = ", ".join(
            f"`{item}`" for item in row.get("source_discovery_queries", [])
        )
        if queries:
            lines.append(f"  source queries: {queries}")
        lines.append(f"  required gate: {row.get('required_gate')}")
        lines.append(f"  boundary: {row.get('proof_evidence_boundary')}")
        if row.get("errors"):
            lines.append(f"  errors: {row.get('errors')}")
    return "\n".join(lines) + "\n"
