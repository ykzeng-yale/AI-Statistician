from __future__ import annotations

import json
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .fingerprint import stable_hash


FORMAL_VERIFIER_REPLAY_REPAIR_EXECUTION_QUEUE_SCHEMA_VERSION = 1


@dataclass(frozen=True)
class FormalVerifierReplayRepairExecutionQueueItem:
    schema_version: int
    execution_id: str
    execution_priority_rank: int
    application_id: str
    validation_id: str
    packet_id: str
    replay_id: str
    latest_attempt_id: str
    source_queue_item_id: str
    route_id: str
    task_id: str
    theorem_goal_id: str
    display_name: str
    repair_class: str
    application_mode: str
    priority_score: int
    target_theorem_name: str
    candidate_bridge_lemma_name: str
    artifact_path: str
    validation_status: str
    local_lean_checked: bool
    local_lean_compiled: bool
    static_checks_ok: bool
    placeholder_free: bool
    proof_evidence_status: str
    required_primitives: tuple[str, ...]
    subclaim_replay_obligations: tuple[str, ...]
    retrieval_hit_obligations: tuple[str, ...]
    related_proof_obligations: tuple[str, ...]
    route_specific_repair_steps: tuple[str, ...]
    execution_steps: tuple[str, ...]
    command_plan: tuple[str, ...]
    acceptance_gate: str
    execution_status: str
    proof_evidence_boundary: str
    ok: bool
    errors: tuple[str, ...] = ()


def export_formal_verifier_replay_repair_execution_queue(
    formal_verifier_replay_repair_application_dir: Path,
    formal_verifier_replay_repair_application_validation_dir: Path,
    out_dir: Path | None = None,
) -> dict[str, object]:
    """Export ranked repair-patch work orders from validated replay scaffolds.

    This queue is a handoff to a RAG/prover worker. It does not apply code,
    submit proof bodies, or promote a theorem. Promotion still requires a
    repaired full-route replay attempt to pass AXLE/local Lean and calibrate as
    full_route_kernel_verified.
    """

    errors: list[str] = []
    application_manifest_path = (
        formal_verifier_replay_repair_application_dir
        / "formal_verifier_replay_repair_application_manifest.json"
    )
    validation_manifest_path = (
        formal_verifier_replay_repair_application_validation_dir
        / "formal_verifier_replay_repair_application_validation_manifest.json"
    )
    application_payload = _read_json(application_manifest_path, errors)
    validation_payload = _read_json(validation_manifest_path, errors)
    tasks = [
        row
        for row in application_payload.get("tasks", [])
        if isinstance(row, dict)
    ]
    validations_by_application = {
        str(row.get("application_id", "")): row
        for row in validation_payload.get("rows", [])
        if isinstance(row, dict) and str(row.get("application_id", ""))
    }
    unranked = [
        _queue_item(
            task,
            validation=validations_by_application.get(str(task.get("application_id", "")), {}),
        )
        for task in tasks
    ]
    ranked = [
        _with_rank(row, rank)
        for rank, row in enumerate(
            sorted(
                unranked,
                key=lambda row: (
                    _status_rank(row.execution_status),
                    -row.priority_score,
                    row.display_name,
                    row.execution_id,
                ),
            ),
            start=1,
        )
    ]
    by_status = Counter(row.execution_status for row in ranked)
    by_mode = Counter(row.application_mode for row in ranked)
    by_repair_class = Counter(row.repair_class for row in ranked)
    payload: dict[str, object] = {
        "schema_version": FORMAL_VERIFIER_REPLAY_REPAIR_EXECUTION_QUEUE_SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "formal_verifier_replay_repair_application_dir": str(
            formal_verifier_replay_repair_application_dir
        ),
        "formal_verifier_replay_repair_application_manifest": str(application_manifest_path),
        "formal_verifier_replay_repair_application_validation_dir": str(
            formal_verifier_replay_repair_application_validation_dir
        ),
        "formal_verifier_replay_repair_application_validation_manifest": str(
            validation_manifest_path
        ),
        "n_application_tasks": len(tasks),
        "n_validation_rows": len(validation_payload.get("rows", []) or []),
        "n_queue_items": len(ranked),
        "n_ok": sum(1 for row in ranked if row.ok),
        "n_ready_for_patch": sum(
            1 for row in ranked if row.execution_status.startswith("READY_FOR_REPAIR_PATCH")
        ),
        "n_ready_local_lean_compiled": sum(
            1
            for row in ranked
            if row.execution_status == "READY_FOR_REPAIR_PATCH_LOCAL_LEAN_SCAFFOLD_VALIDATED"
        ),
        "n_ready_static_validated": sum(
            1
            for row in ranked
            if row.execution_status == "READY_FOR_REPAIR_PATCH_STATIC_VALIDATED"
        ),
        "n_blocked": sum(1 for row in ranked if row.execution_status.startswith("BLOCKED")),
        "n_placeholder_free": sum(1 for row in ranked if row.placeholder_free),
        "n_static_checks_ok": sum(1 for row in ranked if row.static_checks_ok),
        "n_local_lean_checked": sum(1 for row in ranked if row.local_lean_checked),
        "n_local_lean_compiled": sum(1 for row in ranked if row.local_lean_compiled),
        "all_ok": not errors and all(row.ok for row in ranked),
        "errors": errors,
        "by_execution_status": dict(sorted(by_status.items())),
        "by_application_mode": dict(sorted(by_mode.items())),
        "by_repair_class": dict(sorted(by_repair_class.items())),
        "queue": [asdict(row) for row in ranked],
        "queue_fingerprint": stable_hash([asdict(row) for row in ranked]),
        "limitations": [
            "repair execution queue items are patch work orders, not proof evidence",
            "validated scaffolds still require concrete bridge/import/type repair before replay",
            "proof evidence requires rerunning formal-verifier-replay-attempts and recalibrating as full_route_kernel_verified",
            "candidate bridge lemma names are work targets, not declarations known to exist",
        ],
    }
    if out_dir is not None:
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "formal_verifier_replay_repair_execution_queue_manifest.json").write_text(
            json.dumps(payload, indent=2, default=str),
            encoding="utf-8",
        )
        (out_dir / "formal_verifier_replay_repair_execution_queue.jsonl").write_text(
            "\n".join(json.dumps(asdict(row), sort_keys=True) for row in ranked)
            + ("\n" if ranked else ""),
            encoding="utf-8",
        )
        (out_dir / "formal_verifier_replay_repair_execution_queue.md").write_text(
            _markdown_report(payload),
            encoding="utf-8",
        )
    return payload


def _queue_item(
    task: dict[str, Any],
    *,
    validation: dict[str, Any],
) -> FormalVerifierReplayRepairExecutionQueueItem:
    errors: list[str] = []
    application_id = str(task.get("application_id", ""))
    validation_id = str(validation.get("validation_id", ""))
    priority_score = _safe_int(task.get("priority_score", 0))
    validation_ok = bool(validation.get("ok", False))
    static_checks_ok = bool(validation.get("static_checks_ok", False))
    local_lean_checked = bool(validation.get("local_lean_checked", False))
    local_lean_compiled = bool(validation.get("local_lean_compiled", False))
    placeholder_free = bool(validation.get("placeholder_free", False))
    artifact_path = str(task.get("artifact_path") or validation.get("artifact_path") or "")
    if not application_id:
        errors.append("application_id missing")
    if not validation_id:
        errors.append("validation row missing")
    if not artifact_path:
        errors.append("artifact_path missing")
    if validation and not validation_ok:
        errors.append("validation row is not ok")
    if validation and not static_checks_ok:
        errors.append("validation row static checks failed")
    if validation and not placeholder_free:
        errors.append("validated scaffold is not placeholder-free")

    execution_status = _execution_status(
        has_validation=bool(validation_id),
        validation_ok=validation_ok,
        static_checks_ok=static_checks_ok,
        local_lean_checked=local_lean_checked,
        local_lean_compiled=local_lean_compiled,
    )
    command_plan = _command_plan(task)
    if not command_plan:
        errors.append("verification command plan missing")
    execution_steps = _execution_steps(task)
    execution_id = (
        "formal_verifier_replay_repair_execution:"
        f"{stable_hash([application_id, validation_id, artifact_path])[:16]}"
    )
    return FormalVerifierReplayRepairExecutionQueueItem(
        schema_version=FORMAL_VERIFIER_REPLAY_REPAIR_EXECUTION_QUEUE_SCHEMA_VERSION,
        execution_id=execution_id,
        execution_priority_rank=0,
        application_id=application_id,
        validation_id=validation_id,
        packet_id=str(task.get("packet_id", "")),
        replay_id=str(task.get("replay_id", "")),
        latest_attempt_id=str(task.get("latest_attempt_id", "")),
        source_queue_item_id=str(task.get("source_queue_item_id", "")),
        route_id=str(task.get("route_id", "")),
        task_id=str(task.get("task_id", "")),
        theorem_goal_id=str(task.get("theorem_goal_id", "")),
        display_name=str(task.get("display_name", "")),
        repair_class=str(task.get("repair_class", "")),
        application_mode=str(task.get("application_mode", "")),
        priority_score=priority_score,
        target_theorem_name=str(task.get("target_theorem_name", "")),
        candidate_bridge_lemma_name=str(task.get("candidate_bridge_lemma_name", "")),
        artifact_path=artifact_path,
        validation_status=str(validation.get("validation_status", "")),
        local_lean_checked=local_lean_checked,
        local_lean_compiled=local_lean_compiled,
        static_checks_ok=static_checks_ok,
        placeholder_free=placeholder_free,
        proof_evidence_status="PATCH_WORK_ORDER_NOT_PROOF_EVIDENCE",
        required_primitives=_str_tuple(task.get("required_primitives", [])),
        subclaim_replay_obligations=_str_tuple(task.get("subclaim_replay_obligations", [])),
        retrieval_hit_obligations=_str_tuple(task.get("retrieval_hit_obligations", [])),
        related_proof_obligations=_str_tuple(task.get("related_proof_obligations", [])),
        route_specific_repair_steps=_str_tuple(task.get("route_specific_repair_steps", [])),
        execution_steps=execution_steps,
        command_plan=command_plan,
        acceptance_gate=str(
            task.get("acceptance_gate")
            or "repaired replay calibration reports full_route_kernel_verified"
        ),
        execution_status=execution_status,
        proof_evidence_boundary=(
            "This queue item is a repair-patch work order, not proof evidence. "
            "The theorem remains unproved until the patched replay target passes "
            "AXLE/local Lean and calibration reports full_route_kernel_verified."
        ),
        ok=not errors and execution_status.startswith("READY_FOR_REPAIR_PATCH"),
        errors=tuple(errors),
    )


def _with_rank(
    row: FormalVerifierReplayRepairExecutionQueueItem,
    rank: int,
) -> FormalVerifierReplayRepairExecutionQueueItem:
    data = asdict(row)
    data["execution_priority_rank"] = rank
    return FormalVerifierReplayRepairExecutionQueueItem(**data)


def _execution_status(
    *,
    has_validation: bool,
    validation_ok: bool,
    static_checks_ok: bool,
    local_lean_checked: bool,
    local_lean_compiled: bool,
) -> str:
    if not has_validation:
        return "BLOCKED_MISSING_SCAFFOLD_VALIDATION"
    if not validation_ok or not static_checks_ok:
        return "BLOCKED_INVALID_SCAFFOLD_VALIDATION"
    if local_lean_checked and local_lean_compiled:
        return "READY_FOR_REPAIR_PATCH_LOCAL_LEAN_SCAFFOLD_VALIDATED"
    if local_lean_checked and not local_lean_compiled:
        return "BLOCKED_LOCAL_LEAN_SCAFFOLD_COMPILE_FAILED"
    return "READY_FOR_REPAIR_PATCH_STATIC_VALIDATED"


def _status_rank(status: str) -> int:
    if status == "READY_FOR_REPAIR_PATCH_LOCAL_LEAN_SCAFFOLD_VALIDATED":
        return 0
    if status == "READY_FOR_REPAIR_PATCH_STATIC_VALIDATED":
        return 1
    return 9


def _execution_steps(task: dict[str, Any]) -> tuple[str, ...]:
    bridge_name = str(task.get("candidate_bridge_lemma_name", ""))
    target_name = str(task.get("target_theorem_name", ""))
    artifact_path = str(task.get("artifact_path", ""))
    steps = [
        f"patch scaffold artifact {artifact_path}",
        f"prove or import candidate bridge lemma {bridge_name}",
        f"replace the failed replay proof for {target_name} with the bridge/subclaim composition",
        "rerun formal-verifier-replay-attempts on the repaired route",
        "rerun formal-verifier-replay-calibration and accept only full_route_kernel_verified",
    ]
    return tuple(step for step in steps if step.strip())


def _command_plan(task: dict[str, Any]) -> tuple[str, ...]:
    commands = _str_tuple(task.get("verification_commands", []))
    if commands:
        return commands
    return (
        "python3 -m ai_statistician.cli formal-verifier-replay-attempts --formal-verifier-replay-dir <replay-dir> --formal-gap-tasks-dir <formal-gap-tasks-dir> --local-lean --lean-project <lean-project> --max-tasks <n> --out <attempt-out>",
        "python3 -m ai_statistician.cli formal-verifier-replay-calibration --formal-verifier-replay-dir <replay-dir> --attempt-log <attempt-out>/formal_verifier_replay_attempts.jsonl --out <calibration-out>",
        "accept only if replay_calibration_status is full_route_kernel_verified and no h_frontier_missing placeholder remains",
    )


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


def _safe_int(value: Any) -> int:
    try:
        return int(value)
    except Exception:
        return 0


def _markdown_report(payload: dict[str, object]) -> str:
    lines = [
        "# Formal Verifier Replay Repair Execution Queue",
        "",
        f"- Application manifest: `{payload.get('formal_verifier_replay_repair_application_manifest')}`",
        f"- Validation manifest: `{payload.get('formal_verifier_replay_repair_application_validation_manifest')}`",
        f"- Queue items: {payload.get('n_ok')}/{payload.get('n_queue_items')} ready",
        f"- Ready for patch: {payload.get('n_ready_for_patch')}",
        f"- Ready with local Lean scaffold validation: {payload.get('n_ready_local_lean_compiled')}",
        f"- Blocked: {payload.get('n_blocked')}",
        f"- Fingerprint: `{payload.get('queue_fingerprint')}`",
        "",
        "Queue items are repair-patch work orders, not theorem proof evidence.",
        "",
        "## Queue",
        "",
    ]
    rows = payload.get("queue", [])
    if not isinstance(rows, list) or not rows:
        lines.append("No repair execution queue items were exported.")
    else:
        for row in rows[:30]:
            if not isinstance(row, dict):
                continue
            lines.append(
                f"{row.get('execution_priority_rank')}. `{row.get('display_name')}` "
                f"({row.get('execution_status')}): {row.get('candidate_bridge_lemma_name')}"
            )
            lines.append(f"   artifact: `{row.get('artifact_path')}`")
            lines.append(f"   gate: {row.get('acceptance_gate')}")
            lines.append(f"   boundary: {row.get('proof_evidence_boundary')}")
    lines.extend(["", "## Honesty Boundary", ""])
    for item in payload.get("limitations", []):
        lines.append(f"- {item}")
    return "\n".join(lines) + "\n"
