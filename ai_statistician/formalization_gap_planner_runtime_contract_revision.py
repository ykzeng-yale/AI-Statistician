from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

from .agent_runtime import AgentTask
from .fingerprint import stable_hash


MAX_SAME_RUN_CONTRACT_REVISIONS = 2
CONTRACT_FEEDBACK_STATUS = (
    "RUNTIME_FORMALIZATION_GAP_PLANNER_LIVE_ROUTE_PLANNER_"
    "CONTRACT_FEEDBACK_NOT_PROOF_EVIDENCE"
)
CONTRACT_REPAIR_TRIGGER = "FORMALIZATION_GAP_PLANNER_LIVE_ROUTE_PLANNER_CONTRACT_REPAIR"
CONTRACT_REPAIR_QUEUE_STATUS = (
    "PENDING_FORMALIZATION_GAP_PLANNER_LIVE_ROUTE_PLANNER_CONTRACT_REPAIR"
)
CONTRACT_REPAIR_BOUNDARY = (
    "Runtime live route-planner contract-repair rows are orchestration feedback "
    "for rerunning a failed LLM route-planning response with a compact staged "
    "schema-validation gate. They are not theorem proof evidence and cannot "
    "close a formal gap without later target-prover replay and kernel evidence."
)
CONTRACT_REVISION_ARTIFACT_KIND = "RuntimeFormalizationGapPlannerContractRevision"


def contract_revision_artifact_hash(artifact: Mapping[str, Any]) -> str:
    return stable_hash(
        {
            key: value
            for key, value in artifact.items()
            if key != "revision_artifact_hash"
        }
    )


def build_contract_revision_artifact(
    *,
    schema_version: int,
    task_id: str,
    live_manifest: Mapping[str, Any],
    contract_feedback_rows: Sequence[Mapping[str, Any]],
    out_dir: Path,
    revision_attempt: int,
    max_same_run_contract_revisions: int = MAX_SAME_RUN_CONTRACT_REVISIONS,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    revision_limit = max(0, int(max_same_run_contract_revisions))
    source_manifest_id = str(live_manifest.get("manifest_id", "") or "")
    source_manifest_hash = stable_hash(dict(live_manifest))
    question = _mapping(live_manifest.get("question", {}))
    question_id = str(question.get("id", "") or "")
    feedback_ids = [
        str(row.get("route_planner_contract_feedback_id", "") or "")
        for row in contract_feedback_rows
        if str(row.get("route_planner_contract_feedback_id", "") or "").strip()
    ]
    artifact_id = (
        "runtime_formalization_gap_planner_contract_revision:"
        + stable_hash(
            [
                task_id,
                source_manifest_id,
                source_manifest_hash,
                feedback_ids,
                revision_attempt,
            ]
        )[:20]
    )
    revision_root = (
        out_dir
        / "runtime_formalization_gap_planner_contract_revisions"
        / _safe_identifier(artifact_id)
    )
    contract_feedback_handoff_ids = list(
        dict.fromkeys(
            str(row.get("formalization_gap_planner_handoff_id", "") or "")
            for row in contract_feedback_rows
            if str(row.get("formalization_gap_planner_handoff_id", "") or "").strip()
        )
    )
    rows_by_handoff = {
        str(row.get("handoff_id", "") or ""): row
        for row in live_manifest.get("rows", []) or []
        if isinstance(row, Mapping)
        and str(row.get("handoff_id", "") or "").strip()
        and str(row.get("handoff_id", "") or "") in contract_feedback_handoff_ids
    }
    reuse_bundles = [
        bundle
        for handoff_id, live_row in rows_by_handoff.items()
        if (
            bundle := _reuse_bundle(
                live_row,
                handoff_id=handoff_id,
                question_id=question_id,
                source_manifest_id=source_manifest_id,
                source_manifest_hash=source_manifest_hash,
                revision_artifact_id=artifact_id,
                revision_root=revision_root,
            )
        )
    ]
    bundles_by_handoff = {
        str(bundle.get("handoff_id", "") or ""): bundle for bundle in reuse_bundles
    }
    enhanced_feedback_rows = [
        _enhanced_feedback_row(
            feedback,
            bundle=bundles_by_handoff.get(
                str(feedback.get("formalization_gap_planner_handoff_id", "") or ""),
                {},
            ),
            source_manifest_hash=source_manifest_hash,
            revision_artifact_id=artifact_id,
            revision_attempt=revision_attempt,
        )
        for feedback in contract_feedback_rows
    ]
    artifact: dict[str, Any] = {
        "schema_version": schema_version,
        "artifact_kind": CONTRACT_REVISION_ARTIFACT_KIND,
        "revision_artifact_id": artifact_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "question": question,
        "question_id": question_id,
        "source_task_id": task_id,
        "source_manifest_id": source_manifest_id,
        "source_manifest_hash": source_manifest_hash,
        "revision_attempt": revision_attempt,
        "max_same_run_contract_revisions": revision_limit,
        "contract_feedback_handoff_ids": contract_feedback_handoff_ids,
        "selected_handoff_ids": list(rows_by_handoff),
        "selected_bridge_ids": list(
            dict.fromkeys(
                str(row.get("bridge_id", "") or "")
                for row in rows_by_handoff.values()
                if str(row.get("bridge_id", "") or "").strip()
            )
        ),
        "contract_feedback_ids": feedback_ids,
        "contract_feedback_rows": enhanced_feedback_rows,
        "reuse_bundles": reuse_bundles,
        "n_reuse_bundles": len(reuse_bundles),
        "n_accepted_staged_followup_stage_attempts": sum(
            int(bundle.get("n_accepted_staged_followup_stage_attempts", 0) or 0)
            for bundle in reuse_bundles
        ),
        "proof_evidence_status": CONTRACT_FEEDBACK_STATUS,
        "proof_evidence_boundary": CONTRACT_REPAIR_BOUNDARY,
        "boundary": (
            "This artifact binds validator feedback and reusable planning fragments "
            "to one rejected live route-planner manifest. Reuse still passes the "
            "current route-planner contract and is not theorem proof evidence."
        ),
    }
    runtime_control = live_manifest.get("runtime_architect_control", {})
    if isinstance(runtime_control, Mapping) and runtime_control:
        artifact["runtime_architect_control"] = dict(runtime_control)
    artifact["revision_artifact_hash"] = contract_revision_artifact_hash(artifact)
    return artifact, enhanced_feedback_rows


def validate_contract_revision_artifact(
    *,
    context: Mapping[str, Any],
    artifacts: Mapping[str, Any],
    question_id: str,
    environment_feedback: Mapping[str, Any],
    learning_feedback_ids: set[str],
) -> tuple[dict[str, Any], list[str]]:
    if not context:
        return {}, []
    errors: list[str] = []
    artifact_id = str(context.get("revision_artifact_id", "") or "")
    artifact = _mapping(artifacts.get(artifact_id, {}))
    if not artifact:
        return {}, ["contract revision artifact is missing from runtime blackboard"]
    if artifact.get("artifact_kind") != CONTRACT_REVISION_ARTIFACT_KIND:
        errors.append("contract revision artifact_kind mismatch")
    expected_hash = str(context.get("revision_artifact_hash", "") or "")
    recorded_hash = str(artifact.get("revision_artifact_hash", "") or "")
    if not expected_hash or expected_hash != recorded_hash:
        errors.append("contract revision task/artifact hash binding mismatch")
    if recorded_hash != contract_revision_artifact_hash(artifact):
        errors.append("contract revision artifact content hash mismatch")
    if str(artifact.get("question_id", "") or "") != question_id:
        errors.append("contract revision question_id mismatch")
    revision_attempt = int(context.get("revision_attempt", 0) or 0)
    if revision_attempt != int(artifact.get("revision_attempt", 0) or 0):
        errors.append("contract revision attempt mismatch")
    context_revision_limit = int(
        context.get("max_same_run_contract_revisions", 0) or 0
    )
    artifact_revision_limit = int(
        artifact.get("max_same_run_contract_revisions", 0) or 0
    )
    if context_revision_limit != artifact_revision_limit:
        errors.append("contract revision limit binding mismatch")
    if not 1 <= revision_attempt <= artifact_revision_limit:
        errors.append("contract revision attempt exceeds same-run budget")
    source_manifest_id = str(artifact.get("source_manifest_id", "") or "")
    source_manifest = artifacts.get(source_manifest_id)
    if not isinstance(source_manifest, Mapping):
        errors.append("contract revision source manifest is missing")
    elif stable_hash(dict(source_manifest)) != str(
        artifact.get("source_manifest_hash", "") or ""
    ):
        errors.append("contract revision source manifest hash mismatch")
    for feedback_key, artifact_key in (
        ("selected_handoff_ids", "selected_handoff_ids"),
        ("formalization_gap_planner_bridge_ids", "selected_bridge_ids"),
    ):
        task_values = _string_set(environment_feedback.get(feedback_key, []))
        artifact_values = _string_set(artifact.get(artifact_key, []))
        if task_values != artifact_values:
            errors.append(f"contract revision {feedback_key} binding mismatch")
    expected_feedback_ids = _string_set(artifact.get("contract_feedback_ids", []))
    if not expected_feedback_ids.issubset(learning_feedback_ids):
        errors.append("contract revision feedback rows are missing from task memory")
    selected_handoff_ids = _string_set(artifact.get("selected_handoff_ids", []))
    feedback_handoff_ids = _string_set(
        artifact.get("contract_feedback_handoff_ids", [])
    )
    if not selected_handoff_ids:
        errors.append("contract revision has no selected rejected handoffs")
    if selected_handoff_ids != feedback_handoff_ids:
        errors.append("contract revision feedback/selected handoff mismatch")
    for bundle in artifact.get("reuse_bundles", []) or []:
        errors.extend(
            _reuse_bundle_errors(
                bundle,
                source_manifest_id=source_manifest_id,
            )
        )
    return artifact, list(dict.fromkeys(errors))


def build_contract_revision_task(
    *,
    current_task: AgentTask,
    question_id: str,
    question_payload: Mapping[str, Any],
    revision_artifact: Mapping[str, Any],
    runtime_learning_rows: Sequence[Mapping[str, Any]],
    architect_context: Mapping[str, Any],
    base_environment_feedback: Mapping[str, Any],
    settings: Mapping[str, Any],
) -> AgentTask:
    revision_artifact_id = str(revision_artifact.get("revision_artifact_id", "") or "")
    revision_attempt = int(revision_artifact.get("revision_attempt", 0) or 0)
    revision_limit = int(
        revision_artifact.get(
            "max_same_run_contract_revisions",
            MAX_SAME_RUN_CONTRACT_REVISIONS,
        )
        or 0
    )
    selected_handoff_ids = list(revision_artifact.get("selected_handoff_ids", []) or [])
    selected_bridge_ids = list(revision_artifact.get("selected_bridge_ids", []) or [])
    revision_environment_feedback = {
        **dict(base_environment_feedback),
        "failure_classification": (
            "formalization_gap_planner_live_route_planner_contract_repair_requested"
        ),
        "selected_handoff_ids": selected_handoff_ids,
        "formalization_gap_planner_bridge_ids": selected_bridge_ids,
        "source_live_route_planner_manifest_id": str(
            revision_artifact.get("source_manifest_id", "") or ""
        ),
        "source_live_route_planner_manifest_hash": str(
            revision_artifact.get("source_manifest_hash", "") or ""
        ),
        "contract_revision_artifact_id": revision_artifact_id,
        "contract_revision_attempt": revision_attempt,
        "proof_evidence_status": CONTRACT_FEEDBACK_STATUS,
    }
    next_architect_context = dict(architect_context)
    next_architect_context["environment_feedback"] = dict(revision_environment_feedback)
    revision_context = {
        "revision_artifact_id": revision_artifact_id,
        "revision_artifact_hash": str(
            revision_artifact.get("revision_artifact_hash", "") or ""
        ),
        "source_manifest_id": str(
            revision_artifact.get("source_manifest_id", "") or ""
        ),
        "source_manifest_hash": str(
            revision_artifact.get("source_manifest_hash", "") or ""
        ),
        "revision_attempt": revision_attempt,
        "max_same_run_contract_revisions": revision_limit,
    }
    max_handoffs = int(settings.get("max_handoffs", 0) or 0)
    max_route_requests = int(settings.get("max_route_requests_per_handoff", 0) or 0)
    return AgentTask(
        task_id=(
            "gap-planner-live-route-revise:"
            + question_id
            + ":"
            + stable_hash(
                [current_task.task_id, revision_context, selected_handoff_ids]
            )[:12]
        ),
        owner_subsystem="FormalizationGapPlanner",
        objective=(
            "Revise one contract-rejected live route-planner handoff using "
            "validator feedback and any source-bound accepted staged fragments, "
            "then replay the complete contract."
        ),
        inputs={
            "question": dict(question_payload),
            "architect_context": next_architect_context,
            "environment_feedback": revision_environment_feedback,
            "runtime_learning_memory": {
                "artifact_kind": "RuntimeLearningMemoryContext",
                "rows": [dict(row) for row in runtime_learning_rows],
                "counts": {
                    "rows_loaded": len(runtime_learning_rows),
                    "max_rows": len(runtime_learning_rows),
                },
            },
            "route_planner_contract_revision": revision_context,
            "invoke_live_route_planner": True,
            "max_handoffs": max_handoffs,
            "max_route_requests_per_handoff": max_route_requests,
            "provider": str(settings.get("provider", "") or ""),
            "model": str(settings.get("model", "") or ""),
            "model_tier": str(settings.get("model_tier", "") or ""),
            "max_tokens": int(settings.get("max_tokens", 0) or 0),
            "max_estimated_prompt_input_tokens": int(
                settings.get("max_estimated_prompt_input_tokens", 0) or 0
            ),
            "temperature": float(settings.get("temperature", 0.0) or 0.0),
            "max_repair_attempts": int(settings.get("max_repair_attempts", 0) or 0),
            "max_contract_revisions": revision_limit,
            "max_staged_followup_stage_calls": int(
                settings.get("max_staged_followup_stage_calls", 0) or 0
            ),
            "timeout_seconds": float(settings.get("timeout_seconds", 0.0) or 0.0),
        },
        allowed_tools=current_task.allowed_tools
        or (
            "model_backend",
            "formalization_gap_planner_llm_route_planner",
            "evidence_ledger",
        ),
        budget={
            "max_handoffs": max_handoffs,
            "max_route_requests_per_handoff": max_route_requests,
            "max_estimated_prompt_input_tokens": int(
                settings.get("max_estimated_prompt_input_tokens", 0) or 0
            ),
            "same_run_contract_revision_attempt": revision_attempt,
            "same_run_contract_revision_limit": revision_limit,
        },
        expected_artifacts=(
            "RuntimeFormalizationGapPlannerLiveRoutePlannerManifest",
            "RuntimeFormalizationGapPlannerExecutionManifest",
        ),
        acceptance_gate=(
            "The rebound or newly generated route packet passes the full LLM "
            "route-planner response contract; planning evidence remains separate "
            "from target-prover and kernel evidence."
        ),
        stop_condition=(
            "Stop after this source-bound revision succeeds, or fail closed "
            "when the configured same-run revision limit is exhausted."
        ),
    )


def contract_revision_handoff_errors(
    artifact: Mapping[str, Any],
    handoff_rows: Sequence[Mapping[str, Any]],
) -> list[str]:
    if not artifact:
        return []
    errors: list[str] = []
    expected_handoff_ids = _string_set(artifact.get("selected_handoff_ids", []))
    handoffs_by_id = {
        str(row.get("handoff_id", "") or ""): row
        for row in handoff_rows
        if isinstance(row, Mapping) and str(row.get("handoff_id", "") or "").strip()
    }
    if set(handoffs_by_id) != expected_handoff_ids:
        errors.append("contract revision regenerated handoff set mismatch")
    for bundle in artifact.get("reuse_bundles", []) or []:
        if not isinstance(bundle, Mapping):
            continue
        handoff = handoffs_by_id.get(str(bundle.get("handoff_id", "") or ""), {})
        if not handoff:
            errors.append("contract revision reuse bundle has no regenerated handoff")
            continue
        for handoff_key, bundle_key, label in (
            ("bridge_id", "bridge_id", "bridge"),
            ("target_prover_family", "target_prover_family", "prover-family"),
            (
                "prior_staged_followup_stage_attempts_jsonl",
                "accepted_staged_followup_stage_attempts_jsonl",
                "reuse path",
            ),
            (
                "prior_staged_followup_stage_attempts_hash",
                "accepted_staged_followup_stage_attempts_hash",
                "reuse hash",
            ),
        ):
            if str(handoff.get(handoff_key, "") or "") != str(
                bundle.get(bundle_key, "") or ""
            ):
                errors.append(f"contract revision regenerated handoff {label} mismatch")
    return list(dict.fromkeys(errors))


def _reuse_bundle(
    live_row: Mapping[str, Any],
    *,
    handoff_id: str,
    question_id: str,
    source_manifest_id: str,
    source_manifest_hash: str,
    revision_artifact_id: str,
    revision_root: Path,
) -> dict[str, Any]:
    accepted_rows = []
    for attempt in live_row.get("staged_followup_stage_attempt_rows", []) or []:
        if not isinstance(attempt, Mapping) or not _accepted_stage_attempt(attempt):
            continue
        source_attempt = {
            key: value
            for key, value in attempt.items()
            if not str(key).startswith("runtime_revision_source_")
        }
        accepted_rows.append(
            {
                **source_attempt,
                "runtime_revision_source_manifest_id": source_manifest_id,
                "runtime_revision_source_manifest_hash": source_manifest_hash,
                "runtime_revision_source_handoff_id": handoff_id,
                "runtime_revision_source_bridge_id": str(
                    live_row.get("bridge_id", "") or ""
                ),
                "runtime_revision_source_question_id": question_id,
                "runtime_revision_source_stage_attempt_hash": stable_hash(
                    source_attempt
                ),
                "runtime_revision_source_artifact_id": revision_artifact_id,
            }
        )
    if not accepted_rows:
        return {}
    bundle_dir = revision_root / _safe_identifier(handoff_id)
    bundle_dir.mkdir(parents=True, exist_ok=True)
    bundle_path = bundle_dir / "accepted_staged_followup_stage_attempts.jsonl"
    _write_jsonl(bundle_path, accepted_rows)
    return {
        "handoff_id": handoff_id,
        "bridge_id": str(live_row.get("bridge_id", "") or ""),
        "question_id": question_id,
        "target_prover_family": str(
            accepted_rows[0].get("target_prover_family", "") or ""
        ),
        "accepted_staged_followup_stage_attempts_jsonl": str(bundle_path),
        "accepted_staged_followup_stage_attempts_hash": stable_hash(accepted_rows),
        "n_accepted_staged_followup_stage_attempts": len(accepted_rows),
        "accepted_stage_attempt_ids": [
            str(row.get("stage_attempt_id", "") or "") for row in accepted_rows
        ],
        "accepted_stage_ids": [
            str(row.get("stage_id", "") or "") for row in accepted_rows
        ],
    }


def _enhanced_feedback_row(
    feedback: Mapping[str, Any],
    *,
    bundle: Mapping[str, Any],
    source_manifest_hash: str,
    revision_artifact_id: str,
    revision_attempt: int,
) -> dict[str, Any]:
    row = dict(feedback)
    values = {
        "source_manifest_hash": source_manifest_hash,
        "contract_revision_artifact_id": revision_artifact_id,
        "contract_revision_attempt": revision_attempt,
        "accepted_staged_followup_stage_attempts_jsonl": str(
            bundle.get("accepted_staged_followup_stage_attempts_jsonl", "") or ""
        ),
        "accepted_staged_followup_stage_attempts_hash": str(
            bundle.get("accepted_staged_followup_stage_attempts_hash", "") or ""
        ),
        "n_accepted_staged_followup_stage_attempts": int(
            bundle.get("n_accepted_staged_followup_stage_attempts", 0) or 0
        ),
    }
    row.update(values)
    input_summary = _mapping(row.get("input_summary", {}))
    input_summary.update(values)
    row["input_summary"] = input_summary
    return row


def _reuse_bundle_errors(
    bundle: Any,
    *,
    source_manifest_id: str,
) -> list[str]:
    if not isinstance(bundle, Mapping):
        return ["contract revision reuse bundle must be an object"]
    path = Path(
        str(bundle.get("accepted_staged_followup_stage_attempts_jsonl", "") or "")
    )
    if not path.exists():
        return [f"contract revision reuse bundle is missing: {path}"]
    try:
        rows = _read_jsonl(path)
    except Exception as exc:
        return [f"contract revision reuse bundle unreadable: {exc}"]
    errors: list[str] = []
    if stable_hash(rows) != str(
        bundle.get("accepted_staged_followup_stage_attempts_hash", "") or ""
    ):
        errors.append("contract revision reuse bundle content hash mismatch")
    if len(rows) != int(
        bundle.get("n_accepted_staged_followup_stage_attempts", 0) or 0
    ):
        errors.append("contract revision reuse bundle row count mismatch")
    for row in rows:
        source_attempt = {
            key: value
            for key, value in row.items()
            if not str(key).startswith("runtime_revision_source_")
        }
        if stable_hash(source_attempt) != str(
            row.get("runtime_revision_source_stage_attempt_hash", "") or ""
        ):
            errors.append("contract revision source stage-attempt hash mismatch")
        if str(row.get("runtime_revision_source_manifest_id", "") or "") != (
            source_manifest_id
        ):
            errors.append("contract revision reuse row source manifest mismatch")
        if str(row.get("runtime_revision_source_handoff_id", "") or "") != str(
            bundle.get("handoff_id", "") or ""
        ):
            errors.append("contract revision reuse row handoff mismatch")
        if str(row.get("runtime_revision_source_bridge_id", "") or "") != str(
            bundle.get("bridge_id", "") or ""
        ):
            errors.append("contract revision reuse row bridge mismatch")
        if str(row.get("target_prover_family", "") or "") != str(
            bundle.get("target_prover_family", "") or ""
        ):
            errors.append("contract revision reuse row prover-family mismatch")
    return errors


def _accepted_stage_attempt(row: Mapping[str, Any]) -> bool:
    return bool(
        row.get("response_present") is True
        and row.get("response_contract_ok") is True
        and row.get("provider_failure") is not True
        and row.get("ok") is True
        and isinstance(row.get("fragment", {}), Mapping)
        and "not theorem proof evidence"
        in str(row.get("proof_evidence_boundary", "") or "").lower()
    )


def _write_jsonl(path: Path, rows: Sequence[Mapping[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, default=str) + "\n")


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line_number, raw_line in enumerate(
        path.read_text(encoding="utf-8").splitlines(),
        start=1,
    ):
        if not raw_line.strip():
            continue
        value = json.loads(raw_line)
        if not isinstance(value, dict):
            raise ValueError(f"{path}:{line_number}: expected JSON object row")
        rows.append(value)
    return rows


def _mapping(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _string_set(value: Any) -> set[str]:
    if isinstance(value, str):
        values = [value]
    elif isinstance(value, Sequence) and not isinstance(value, (bytes, bytearray)):
        values = value
    else:
        values = []
    return {str(item) for item in values if str(item).strip()}


def _safe_identifier(raw: str) -> str:
    value = re.sub(r"[^A-Za-z0-9_]+", "_", str(raw).strip())
    return re.sub(r"_+", "_", value).strip("_") or "contract_revision"
