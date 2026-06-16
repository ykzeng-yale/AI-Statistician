from __future__ import annotations

import json
import re
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .fingerprint import stable_hash
from .formalization_gap_planner_contract import (
    LIBRARY_AWARE_FORMALIZATION_GAP_PLANNER_NAME,
    PORTABLE_FORMALIZATION_GAP_PLAN_SCHEMA_ID,
    PROOF_EVIDENCE_BOUNDARY as PLANNER_PROOF_EVIDENCE_BOUNDARY,
)


FORMALIZATION_GAP_PLANNER_REFINEMENT_QUEUE_SCHEMA_VERSION = 2
PROOF_EVIDENCE_STATUS = "FORMALIZATION_GAP_PLANNER_REFINEMENT_QUEUE_NOT_PROOF_EVIDENCE"
PROOF_EVIDENCE_BOUNDARY = (
    "Formalization gap planner refinement rows are interactive search, "
    "library-grounding, and prover-feedback work orders. They revise route "
    "evidence and the planned formalization delta, but they are not theorem proof "
    "evidence. Only target-prover kernel verification can prove a theorem or "
    "bridge lemma."
)
REFINEMENT_WORK_ITEM_SCHEMA_ID = (
    "urn:ai-statistician:schemas:"
    "formalization-gap-planner-refinement-work-item:1"
)
REFINEMENT_HOOK_KINDS = (
    "literature_discovery",
    "formal_library_grounding",
    "lean_library_grounding",
    "proof_state_feedback",
    "route_revision",
)
REFINEMENT_QUEUE_STATUSES = (
    "READY_FOR_INTERACTIVE_REFINEMENT",
    "BLOCKED_INTERACTIVE_REFINEMENT_INPUT",
)


@dataclass(frozen=True)
class FormalizationGapPlannerRefinementQueueRow:
    schema_version: int
    refinement_item_id: str
    goal_plan_id: str
    route_id: str
    display_name: str
    theorem_skeleton: str
    theorem_statement: str
    route_class: str
    pareto_profile: str
    hook_kind: str
    refinement_stage: str
    owner_agent: str
    target_prover_family: str
    target_primitives: tuple[str, ...]
    trigger_kinds: tuple[str, ...]
    trigger_conditions: tuple[str, ...]
    trigger_next_actions: tuple[str, ...]
    queries: tuple[str, ...]
    recommended_tools: tuple[str, ...]
    frontier_resource_adapters: tuple[str, ...]
    resource_request_ids: tuple[str, ...]
    resource_ids: tuple[str, ...]
    resource_request_bindings: tuple[dict[str, object], ...]
    quality_controls: dict[str, tuple[str, ...]]
    llm_route_planner_hook_trace: dict[str, object]
    evaluation_signal: str
    evaluation_route_missing_primitives: tuple[str, ...]
    evaluation_delta_missing_primitives: tuple[str, ...]
    evaluation_coverage_confusions: tuple[dict[str, object], ...]
    prover_feedback_status: str
    prover_feedback_error_category: str
    prover_feedback_first_error: str
    acceptance_record: str
    expected_artifacts: tuple[str, ...]
    execution_commands: tuple[str, ...]
    required_gate: str
    status: str
    priority_score: int
    rank: int
    proof_evidence_status: str
    proof_evidence_boundary: str
    ok: bool
    errors: tuple[str, ...] = ()


def export_formalization_gap_planner_refinement_queue(
    goal_conditioned_minimal_formalization_plan_dir: Path,
    out_dir: Path | None = None,
    *,
    formalization_gap_planner_evaluation_dir: Path | None = None,
    formal_verifier_replay_calibration_dir: Path | None = None,
    max_items: int = 0,
) -> dict[str, object]:
    """Export interactive route-refinement work items from gap-plan rows.

    This queue turns the planner's `interactive_refinement_hooks` and
    `route_revision_triggers` into concrete, auditable work orders for
    literature discovery, formal-library grounding, proof-state feedback, and
    route revision. Optional evaluator and replay-calibration manifests add
    held-out truth errors and prover residuals as prioritization signals.
    """

    errors: list[str] = []
    plan_manifest_path = (
        goal_conditioned_minimal_formalization_plan_dir
        / "goal_conditioned_minimal_formalization_plan_manifest.json"
    )
    plan_payload = _read_json(plan_manifest_path, errors)
    if plan_payload.get("component_name") != LIBRARY_AWARE_FORMALIZATION_GAP_PLANNER_NAME:
        errors.append("input manifest is not the library-aware formalization gap planner")
    if plan_payload.get("portable_schema_id") != PORTABLE_FORMALIZATION_GAP_PLAN_SCHEMA_ID:
        errors.append("input manifest portable schema id mismatch")

    evaluation_manifest_path = (
        formalization_gap_planner_evaluation_dir
        / "formalization_gap_planner_evaluation_manifest.json"
        if formalization_gap_planner_evaluation_dir is not None
        else None
    )
    evaluation_payload = (
        _read_json(evaluation_manifest_path, errors)
        if evaluation_manifest_path is not None
        else {}
    )
    calibration_manifest_path = (
        formal_verifier_replay_calibration_dir
        / "formal_verifier_replay_calibration_manifest.json"
        if formal_verifier_replay_calibration_dir is not None
        else None
    )
    calibration_payload = (
        _read_json(calibration_manifest_path, errors)
        if calibration_manifest_path is not None
        else {}
    )

    plan_rows = [row for row in plan_payload.get("rows", []) if isinstance(row, dict)]
    evaluation_index = _diagnostic_index(evaluation_payload.get("rows", []))
    calibration_index = _diagnostic_index(calibration_payload.get("rows", []))
    raw_rows: list[FormalizationGapPlannerRefinementQueueRow] = []
    for plan_row in plan_rows:
        evaluation_row = _match_diagnostic(plan_row, evaluation_index)
        calibration_row = _match_diagnostic(plan_row, calibration_index)
        for hook in _hooks_for_plan_row(plan_row, evaluation_row, calibration_row):
            raw_rows.append(
                _refinement_row(
                    plan_row,
                    hook,
                    evaluation_row=evaluation_row,
                    calibration_row=calibration_row,
                )
            )

    ranked_rows = _rank_rows(raw_rows)
    if max_items > 0:
        rows = ranked_rows[:max_items]
    else:
        rows = ranked_rows
    row_dicts = [asdict(row) for row in rows]
    work_item_schema = refinement_work_item_json_schema()
    row_schema_errors = [
        validate_refinement_work_item_row(row_dict, work_item_schema)
        for row_dict in row_dicts
    ]
    n_item_schema_valid = sum(1 for row_errors in row_schema_errors if not row_errors)
    n_item_schema_invalid = len(row_schema_errors) - n_item_schema_valid
    by_hook_kind = Counter(row.hook_kind for row in rows)
    by_stage = Counter(row.refinement_stage for row in rows)
    by_owner = Counter(row.owner_agent for row in rows)
    by_target = Counter(row.target_prover_family for row in rows)
    by_status = Counter(row.status for row in rows)
    payload: dict[str, object] = {
        "schema_version": FORMALIZATION_GAP_PLANNER_REFINEMENT_QUEUE_SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "component_name": "formalization_gap_planner_refinement_queue",
        "source_component": plan_payload.get("component_name", ""),
        "portable_schema_id": plan_payload.get("portable_schema_id", ""),
        "goal_conditioned_minimal_formalization_plan_dir": str(
            goal_conditioned_minimal_formalization_plan_dir
        ),
        "goal_conditioned_minimal_formalization_plan_manifest": str(plan_manifest_path),
        "formalization_gap_planner_evaluation_dir": str(
            formalization_gap_planner_evaluation_dir or ""
        ),
        "formalization_gap_planner_evaluation_manifest": str(
            evaluation_manifest_path or ""
        ),
        "formal_verifier_replay_calibration_dir": str(
            formal_verifier_replay_calibration_dir or ""
        ),
        "formal_verifier_replay_calibration_manifest": str(
            calibration_manifest_path or ""
        ),
        "n_plan_rows": len(plan_rows),
        "n_evaluation_rows": len(evaluation_payload.get("rows", []))
        if isinstance(evaluation_payload.get("rows", []), list)
        else 0,
        "n_calibration_rows": len(calibration_payload.get("rows", []))
        if isinstance(calibration_payload.get("rows", []), list)
        else 0,
        "max_items": max_items,
        "n_refinement_items": len(rows),
        "n_ready": by_status.get("READY_FOR_INTERACTIVE_REFINEMENT", 0),
        "n_blocked": sum(
            count for status, count in by_status.items() if status.startswith("BLOCKED_")
        ),
        "n_literature_discovery_items": by_hook_kind.get("literature_discovery", 0),
        "n_formal_library_grounding_items": (
            by_hook_kind.get("formal_library_grounding", 0)
            + by_hook_kind.get("lean_library_grounding", 0)
        ),
        "n_lean_library_grounding_items": by_hook_kind.get("lean_library_grounding", 0),
        "n_proof_state_feedback_items": by_hook_kind.get("proof_state_feedback", 0),
        "n_route_revision_items": by_hook_kind.get("route_revision", 0),
        "n_with_evaluation_signal": sum(
            1 for row in rows if row.evaluation_signal != "no_evaluation_signal"
        ),
        "n_with_prover_feedback": sum(
            1
            for row in rows
            if row.prover_feedback_status
            not in {"", "no_calibration_signal", "awaiting_full_route_attempt"}
        ),
        "n_with_failed_prover_feedback": sum(
            1
            for row in rows
            if _is_failed_prover_feedback(row.prover_feedback_status)
        ),
        "n_with_quality_controls": sum(1 for row in rows if row.quality_controls),
        "n_item_schema_valid": n_item_schema_valid,
        "n_item_schema_invalid": n_item_schema_invalid,
        "refinement_work_item_schema": work_item_schema,
        "n_ok": sum(1 for row in rows if row.ok),
        "all_ok": (
            not errors
            and bool(rows)
            and all(row.ok for row in rows)
            and n_item_schema_invalid == 0
        ),
        "errors": errors,
        "by_hook_kind": dict(sorted(by_hook_kind.items())),
        "by_refinement_stage": dict(sorted(by_stage.items())),
        "by_owner_agent": dict(sorted(by_owner.items())),
        "by_target_prover_family": dict(sorted(by_target.items())),
        "by_status": dict(sorted(by_status.items())),
        "rows": row_dicts,
        "refinement_queue_fingerprint": stable_hash(row_dicts),
        "proof_evidence_status": PROOF_EVIDENCE_STATUS,
        "proof_evidence_boundary": PROOF_EVIDENCE_BOUNDARY,
        "planner_proof_evidence_boundary": PLANNER_PROOF_EVIDENCE_BOUNDARY,
        "limitations": [
            "refinement queue rows are operational work items, not theorem proof evidence",
            "literature and formal-library search outputs must be recorded as route evidence until a prover verifies a theorem",
            "prover failures are diagnostic feedback for route revision, not disproofs of the informal theorem",
            "route revisions should be written back into the informal knowledge DAG and formal realization DAG before replay",
        ],
    }
    if out_dir is not None:
        out_dir.mkdir(parents=True, exist_ok=True)
        (
            out_dir / "formalization_gap_planner_refinement_queue_manifest.json"
        ).write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
        (
            out_dir / "formalization_gap_planner_refinement_work_item.schema.json"
        ).write_text(json.dumps(work_item_schema, indent=2), encoding="utf-8")
        (out_dir / "formalization_gap_planner_refinement_queue.jsonl").write_text(
            "\n".join(json.dumps(asdict(row), sort_keys=True) for row in rows)
            + ("\n" if rows else ""),
            encoding="utf-8",
        )
        (out_dir / "formalization_gap_planner_refinement_queue.md").write_text(
            _markdown_report(payload),
            encoding="utf-8",
        )
    return payload


def refinement_work_item_json_schema() -> dict[str, object]:
    """JSON Schema for public refinement work-request rows."""

    string_array = {"type": "array", "items": {"type": "string"}}
    object_array = {"type": "array", "items": {"type": "object"}}
    quality_controls = {
        "type": "object",
        "additionalProperties": string_array,
    }
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": REFINEMENT_WORK_ITEM_SCHEMA_ID,
        "title": "Formalization Gap Planner Refinement Work Item",
        "description": (
            "Tool-facing work-request contract for bounded literature search, "
            "formal-library grounding, proof-state feedback, and route revision. "
            "Rows are not theorem proof evidence."
        ),
        "type": "object",
        "additionalProperties": True,
        "required": [
            "schema_version",
            "refinement_item_id",
            "goal_plan_id",
            "route_id",
            "display_name",
            "hook_kind",
            "refinement_stage",
            "owner_agent",
            "target_primitives",
            "queries",
            "recommended_tools",
            "frontier_resource_adapters",
            "expected_artifacts",
            "execution_commands",
            "required_gate",
            "status",
            "priority_score",
            "rank",
            "proof_evidence_status",
            "proof_evidence_boundary",
            "ok",
        ],
        "properties": {
            "schema_version": {
                "type": "integer",
                "const": FORMALIZATION_GAP_PLANNER_REFINEMENT_QUEUE_SCHEMA_VERSION,
            },
            "refinement_item_id": {"type": "string", "minLength": 1},
            "goal_plan_id": {"type": "string", "minLength": 1},
            "route_id": {"type": "string", "minLength": 1},
            "display_name": {"type": "string", "minLength": 1},
            "theorem_skeleton": {"type": "string"},
            "theorem_statement": {"type": "string"},
            "route_class": {"type": "string"},
            "pareto_profile": {"type": "string"},
            "hook_kind": {"enum": list(REFINEMENT_HOOK_KINDS)},
            "refinement_stage": {"type": "string", "minLength": 1},
            "owner_agent": {"type": "string", "minLength": 1},
            "target_prover_family": {"type": "string"},
            "target_primitives": string_array,
            "trigger_kinds": string_array,
            "trigger_conditions": string_array,
            "trigger_next_actions": string_array,
            "queries": string_array,
            "recommended_tools": string_array,
            "frontier_resource_adapters": string_array,
            "resource_request_ids": string_array,
            "resource_ids": string_array,
            "resource_request_bindings": object_array,
            "quality_controls": quality_controls,
            "llm_route_planner_hook_trace": {"type": "object"},
            "evaluation_signal": {"type": "string"},
            "evaluation_route_missing_primitives": string_array,
            "evaluation_delta_missing_primitives": string_array,
            "evaluation_coverage_confusions": object_array,
            "prover_feedback_status": {"type": "string"},
            "prover_feedback_error_category": {"type": "string"},
            "prover_feedback_first_error": {"type": "string"},
            "acceptance_record": {"type": "string"},
            "expected_artifacts": string_array,
            "execution_commands": string_array,
            "required_gate": {"type": "string", "minLength": 1},
            "status": {"enum": list(REFINEMENT_QUEUE_STATUSES)},
            "priority_score": {"type": "integer"},
            "rank": {"type": "integer"},
            "proof_evidence_status": {
                "type": "string",
                "pattern": "NOT_PROOF_EVIDENCE",
            },
            "proof_evidence_boundary": {
                "type": "string",
                "pattern": "not theorem proof evidence",
            },
            "ok": {"type": "boolean"},
            "errors": string_array,
        },
    }


def validate_refinement_work_item_row(
    row: dict[str, Any],
    schema: dict[str, object] | None = None,
) -> tuple[str, ...]:
    """Validate a refinement work item against the published schema."""

    work_item_schema = schema or refinement_work_item_json_schema()
    errors: list[str] = []
    required = work_item_schema.get("required", [])
    if isinstance(required, list):
        for field_name in required:
            if isinstance(field_name, str) and field_name not in row:
                errors.append(f"{field_name} required")
    properties = work_item_schema.get("properties", {})
    if isinstance(properties, dict):
        for field_name, field_schema in properties.items():
            if not isinstance(field_name, str) or field_name not in row:
                continue
            if isinstance(field_schema, dict):
                errors.extend(
                    _schema_property_errors(field_name, row[field_name], field_schema)
                )
    return tuple(errors)


def _schema_property_errors(
    field_name: str,
    value: Any,
    field_schema: dict[str, Any],
) -> tuple[str, ...]:
    errors: list[str] = []
    expected_type = field_schema.get("type")
    if expected_type == "integer":
        if not isinstance(value, int) or isinstance(value, bool):
            errors.append(f"{field_name} must be integer")
    elif expected_type == "string":
        if not isinstance(value, str):
            errors.append(f"{field_name} must be string")
        elif field_schema.get("minLength") and len(value) < int(
            field_schema["minLength"]
        ):
            errors.append(f"{field_name} must be non-empty")
    elif expected_type == "boolean":
        if not isinstance(value, bool):
            errors.append(f"{field_name} must be boolean")
    elif expected_type == "object":
        if not isinstance(value, dict):
            errors.append(f"{field_name} must be object")
    elif expected_type == "array":
        if not isinstance(value, (list, tuple)):
            errors.append(f"{field_name} must be array")
        else:
            item_schema = field_schema.get("items", {})
            if isinstance(item_schema, dict) and item_schema.get("type") == "string":
                bad_indexes = [
                    idx for idx, item in enumerate(value) if not isinstance(item, str)
                ]
                if bad_indexes:
                    errors.append(
                        f"{field_name} items must be string at indexes "
                        + ",".join(str(idx) for idx in bad_indexes)
                    )
            if isinstance(item_schema, dict) and item_schema.get("type") == "object":
                bad_indexes = [
                    idx for idx, item in enumerate(value) if not isinstance(item, dict)
                ]
                if bad_indexes:
                    errors.append(
                        f"{field_name} items must be object at indexes "
                        + ",".join(str(idx) for idx in bad_indexes)
                    )
    if "const" in field_schema and value != field_schema["const"]:
        errors.append(f"{field_name} must equal {field_schema['const']!r}")
    enum_values = field_schema.get("enum")
    if isinstance(enum_values, list) and value not in enum_values:
        errors.append(f"{field_name} must be one of {','.join(map(str, enum_values))}")
    pattern = field_schema.get("pattern")
    if isinstance(pattern, str) and isinstance(value, str):
        if re.search(pattern, value) is None:
            errors.append(f"{field_name} must match /{pattern}/")
    return tuple(errors)


def _refinement_row(
    plan_row: dict[str, Any],
    hook: dict[str, Any],
    *,
    evaluation_row: dict[str, Any],
    calibration_row: dict[str, Any],
) -> FormalizationGapPlannerRefinementQueueRow:
    errors: list[str] = []
    goal_plan_id = str(plan_row.get("goal_plan_id", ""))
    route_id = str(plan_row.get("route_id", ""))
    display_name = str(plan_row.get("display_name", ""))
    target_prover_family = _target_prover_family(plan_row, hook)
    hook_kind = _target_scoped_hook_kind(
        str(hook.get("hook_kind", "")),
        target_prover_family=target_prover_family,
    )
    stage = _refinement_stage(hook_kind)
    target_primitives = _target_primitives(plan_row, hook, hook_kind, evaluation_row)
    triggers = _triggers_for_hook(plan_row, hook_kind, evaluation_row, calibration_row)
    queries = _queries_for_hook(plan_row, hook, hook_kind, evaluation_row, calibration_row)
    recommended_tools = _recommended_tools(
        hook,
        hook_kind,
        target_prover_family=target_prover_family,
    )
    adapters = _frontier_resource_adapters(
        hook_kind,
        target_prover_family=target_prover_family,
    )
    resource_request_ids = _str_tuple(hook.get("resource_request_ids", []))
    resource_ids = _str_tuple(hook.get("resource_ids", []))
    resource_request_bindings = _dict_tuple(
        hook.get("resource_request_bindings", [])
    )
    quality_controls = _quality_controls_from_hook(
        hook,
        resource_request_bindings=resource_request_bindings,
    )
    llm_route_planner_hook_trace = _llm_route_planner_hook_trace(hook)
    evaluation_signal = _evaluation_signal(evaluation_row)
    prover_status = _prover_feedback_status(calibration_row)
    acceptance_record = str(hook.get("acceptance_record", "")) or _acceptance_record(
        hook_kind
    )
    theorem_statement = str(plan_row.get("theorem_statement", "")).strip()
    theorem_skeleton = theorem_statement or str(plan_row.get("theorem_skeleton", ""))

    for field_name, value in (
        ("goal_plan_id", goal_plan_id),
        ("route_id", route_id),
        ("display_name", display_name),
        ("hook_kind", hook_kind),
        ("refinement_stage", stage),
    ):
        if not value:
            errors.append(f"{field_name} missing")
    if hook_kind not in {
        "literature_discovery",
        "formal_library_grounding",
        "lean_library_grounding",
        "proof_state_feedback",
        "route_revision",
    }:
        errors.append(f"unsupported hook_kind: {hook_kind}")
    if not recommended_tools:
        errors.append("recommended_tools missing")
    if not queries:
        errors.append("queries missing")
    if not target_primitives and hook_kind != "route_revision":
        errors.append("target_primitives missing")
    if hook_kind == "proof_state_feedback" and not theorem_skeleton:
        errors.append("theorem_skeleton missing for proof-state feedback")

    status = (
        "READY_FOR_INTERACTIVE_REFINEMENT"
        if not errors
        else "BLOCKED_INTERACTIVE_REFINEMENT_INPUT"
    )
    return FormalizationGapPlannerRefinementQueueRow(
        schema_version=FORMALIZATION_GAP_PLANNER_REFINEMENT_QUEUE_SCHEMA_VERSION,
        refinement_item_id=(
            "formalization_gap_planner_refinement:"
            + stable_hash([goal_plan_id, route_id, hook_kind, queries, triggers])[:16]
        ),
        goal_plan_id=goal_plan_id,
        route_id=route_id,
        display_name=display_name,
        theorem_skeleton=theorem_skeleton,
        theorem_statement=theorem_statement,
        route_class=str(plan_row.get("route_class", "")),
        pareto_profile=str(plan_row.get("pareto_profile", "")),
        hook_kind=hook_kind,
        refinement_stage=stage,
        owner_agent=_owner_agent(hook_kind),
        target_prover_family=target_prover_family,
        target_primitives=target_primitives,
        trigger_kinds=_str_tuple(item.get("trigger_kind", "") for item in triggers),
        trigger_conditions=_str_tuple(item.get("condition", "") for item in triggers),
        trigger_next_actions=_str_tuple(item.get("next_action", "") for item in triggers),
        queries=queries,
        recommended_tools=recommended_tools,
        frontier_resource_adapters=adapters,
        resource_request_ids=resource_request_ids,
        resource_ids=resource_ids,
        resource_request_bindings=resource_request_bindings,
        quality_controls=quality_controls,
        llm_route_planner_hook_trace=llm_route_planner_hook_trace,
        evaluation_signal=evaluation_signal,
        evaluation_route_missing_primitives=_str_tuple(
            evaluation_row.get("route_missing_primitives", [])
        ),
        evaluation_delta_missing_primitives=_str_tuple(
            evaluation_row.get("delta_missing_primitives", [])
        ),
        evaluation_coverage_confusions=_coverage_confusions(evaluation_row),
        prover_feedback_status=prover_status,
        prover_feedback_error_category=str(calibration_row.get("first_error_category", "")),
        prover_feedback_first_error=str(calibration_row.get("first_error", "")),
        acceptance_record=acceptance_record,
        expected_artifacts=_expected_artifacts(hook_kind),
        execution_commands=_execution_commands(
            hook_kind,
            target_prover_family=target_prover_family,
        ),
        required_gate=_required_gate(hook_kind),
        status=status,
        priority_score=_priority_score(
            hook_kind,
            plan_row,
            evaluation_signal=evaluation_signal,
            prover_feedback_status=prover_status,
        ),
        rank=0,
        proof_evidence_status=PROOF_EVIDENCE_STATUS,
        proof_evidence_boundary=PROOF_EVIDENCE_BOUNDARY,
        ok=not errors,
        errors=tuple(errors),
    )


def _hooks_for_plan_row(
    plan_row: dict[str, Any],
    evaluation_row: dict[str, Any],
    calibration_row: dict[str, Any],
) -> tuple[dict[str, Any], ...]:
    hooks = [
        hook
        for hook in plan_row.get("interactive_refinement_hooks", [])
        if isinstance(hook, dict)
    ]
    hook_kinds = {str(hook.get("hook_kind", "")) for hook in hooks}
    if _needs_route_revision(plan_row, evaluation_row, calibration_row) and (
        "route_revision" not in hook_kinds
    ):
        hooks.append(
            {
                "hook_kind": "route_revision",
                "recommended_tools": [
                    "literature_discovery",
                    "formal_library_grounding",
                    "proof_state_feedback",
                ],
                "queries": list(_str_tuple(plan_row.get("selected_primitives", [])))[:8],
                "acceptance_record": (
                    "revise the informal knowledge DAG, formal realization DAG, and "
                    "selected delta before the next replay attempt"
                ),
            }
        )
    return tuple(hooks)


def _needs_route_revision(
    plan_row: dict[str, Any],
    evaluation_row: dict[str, Any],
    calibration_row: dict[str, Any],
) -> bool:
    if _evaluation_signal(evaluation_row) != "no_evaluation_signal":
        return True
    prover_status = _prover_feedback_status(calibration_row)
    if _is_failed_prover_feedback(prover_status):
        return True
    return bool(plan_row.get("first_principles_nodes")) or bool(
        plan_row.get("source_discovery_nodes")
    )


def _triggers_for_hook(
    plan_row: dict[str, Any],
    hook_kind: str,
    evaluation_row: dict[str, Any],
    calibration_row: dict[str, Any],
) -> tuple[dict[str, object], ...]:
    triggers = [
        trigger
        for trigger in plan_row.get("route_revision_triggers", [])
        if isinstance(trigger, dict)
    ]
    selected: list[dict[str, object]] = []
    for trigger in triggers:
        trigger_kind = str(trigger.get("trigger_kind", ""))
        if _trigger_matches_hook(trigger_kind, hook_kind):
            selected.append(trigger)
    eval_signal = _evaluation_signal(evaluation_row)
    if eval_signal != "no_evaluation_signal":
        selected.append(
            {
                "trigger_kind": "evaluation_route_truth_mismatch",
                "condition": eval_signal,
                "next_action": (
                    "compare predicted route nodes with held-out route truth and "
                    "revise missing or extra primitives"
                ),
            }
        )
    prover_status = _prover_feedback_status(calibration_row)
    if _is_failed_prover_feedback(prover_status):
        selected.append(
            {
                "trigger_kind": "prover_feedback_residual",
                "condition": (
                    f"{prover_status}: "
                    f"{calibration_row.get('first_error_category', '')}"
                ),
                "next_action": (
                    "feed residual goals or verifier diagnostics back into the "
                    "route plan before expanding the formalization delta"
                ),
            }
        )
    if not selected:
        selected.append(
            {
                "trigger_kind": f"{hook_kind}_scheduled",
                "condition": "planner hook requested this refinement stage",
                "next_action": _required_gate(hook_kind),
            }
        )
    return tuple(selected)


def _is_formal_library_grounding_hook(hook_kind: str) -> bool:
    return hook_kind in {"formal_library_grounding", "lean_library_grounding"}


def _target_prover_family(plan_row: dict[str, Any], hook: dict[str, Any]) -> str:
    return str(
        hook.get("target_prover_family")
        or plan_row.get("target_prover_family")
        or plan_row.get("target_prover")
        or "lean4"
    ).strip()


def _target_scoped_hook_kind(
    hook_kind: str,
    *,
    target_prover_family: str,
) -> str:
    if (
        hook_kind == "lean_library_grounding"
        and _prover_family_key(target_prover_family) not in {"lean", "lean4"}
    ):
        return "formal_library_grounding"
    return hook_kind


def _prover_family_key(target_prover_family: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", str(target_prover_family).strip().lower()).strip("_")


def _trigger_matches_hook(trigger_kind: str, hook_kind: str) -> bool:
    if hook_kind == "literature_discovery":
        return trigger_kind in {
            "literature_route_evidence_needed",
            "source_port_or_external_declaration_needed",
            "new_theory_risk_review",
            "quality_control_evidence_required",
            "queued_resource_response_required",
            "resource_response_playbook_redispatch_required",
        }
    if _is_formal_library_grounding_hook(hook_kind):
        return trigger_kind in {
            "formal_library_grounding_required",
            "formal_leaf_attempt_required",
            "lean_leaf_attempt_required",
            "source_port_or_external_declaration_needed",
            "blocked_by_formal_side_condition",
            "new_theory_risk_review",
            "quality_control_evidence_required",
            "queued_resource_response_required",
            "resource_response_playbook_redispatch_required",
        }
    if hook_kind == "proof_state_feedback":
        return trigger_kind in {
            "lean_leaf_attempt_required",
            "blocked_by_formal_side_condition",
            "quality_control_evidence_required",
            "queued_resource_response_required",
            "resource_response_playbook_redispatch_required",
        }
    if hook_kind == "route_revision":
        return True
    return False


def _llm_route_planner_hook_trace(hook: dict[str, Any]) -> dict[str, object]:
    trace: dict[str, object] = {
        "trace_kind": "llm_route_planner_hook_trace",
    }
    for field_name in (
        "llm_route_planner_search_request_index",
        "llm_route_planner_search_request",
        "planner_next_actions",
        "llm_route_planner_planner_next_action_index",
        "llm_route_planner_planner_next_action",
        "llm_route_planner_formal_attempt_queue_index",
        "llm_route_planner_formal_attempt",
        "formal_attempt_id",
        "formal_node_id",
        "formal_attempt_kind",
        "prerequisite_formal_node_ids",
        "expected_feedback",
        "llm_route_planner_feedback_next_action_index",
        "llm_route_planner_feedback_next_action",
        "llm_route_planner_feedback_replan_required",
        "llm_route_planner_feedback_loop_summary",
        "llm_route_planner_realization_coverage_action_index",
        "llm_route_planner_realization_coverage_action",
        "llm_route_planner_realization_coverage_witness",
        "llm_route_planner_residual_interpretation_index",
        "llm_route_planner_residual_interpretation",
        "llm_route_planner_uncertainty_flags",
        "llm_route_planner_semantic_alignment_risks",
        "llm_route_planner_quality_control_obligations",
        "llm_route_planner_review_source",
    ):
        if field_name in hook:
            trace[field_name] = hook[field_name]
    if len(trace) == 1:
        return {}
    return trace


def _quality_controls_from_hook(
    hook: dict[str, Any],
    *,
    resource_request_bindings: tuple[dict[str, object], ...],
) -> dict[str, tuple[str, ...]]:
    return _merge_quality_controls(
        _quality_controls_from_payload(hook.get("quality_controls", {})),
        _quality_controls_from_resource_request_bindings(resource_request_bindings),
    )


def _merge_quality_controls(
    *values: dict[str, tuple[str, ...]],
) -> dict[str, tuple[str, ...]]:
    merged: dict[str, list[str]] = {}
    for item in values:
        if not isinstance(item, dict):
            continue
        for field_name in (
            "resource_contract_ids",
            "required_quality_signals",
            "quality_gates",
            "response_validation_signals",
            "stop_conditions",
        ):
            field_values = _str_tuple(item.get(field_name, []))
            if field_values:
                merged.setdefault(field_name, []).extend(field_values)
    return {
        field_name: _str_tuple(field_values)
        for field_name, field_values in merged.items()
        if _str_tuple(field_values)
    }


def _quality_controls_from_payload(value: Any) -> dict[str, tuple[str, ...]]:
    if not isinstance(value, dict):
        return {}
    return _merge_quality_controls(
        {
            field_name: _str_tuple(value.get(field_name, []))
            for field_name in (
                "resource_contract_ids",
                "required_quality_signals",
                "quality_gates",
                "response_validation_signals",
                "stop_conditions",
            )
        }
    )


def _quality_controls_from_resource_request_bindings(
    bindings: tuple[dict[str, object], ...],
) -> dict[str, tuple[str, ...]]:
    controls = [
        _quality_controls_from_payload(binding.get("quality_controls", {}))
        for binding in bindings
    ]
    return _merge_quality_controls(*controls)


def _queries_for_hook(
    plan_row: dict[str, Any],
    hook: dict[str, Any],
    hook_kind: str,
    evaluation_row: dict[str, Any],
    calibration_row: dict[str, Any],
) -> tuple[str, ...]:
    queries: list[str] = [str(item) for item in hook.get("queries", []) if str(item)]
    display_name = str(plan_row.get("display_name", ""))
    theorem_skeleton = str(plan_row.get("theorem_skeleton", ""))
    theorem_statement = str(plan_row.get("theorem_statement", ""))
    selected_primitives = _str_tuple(plan_row.get("selected_primitives", []))
    missing = _str_tuple(
        [
            *evaluation_row.get("route_missing_primitives", []),
            *evaluation_row.get("delta_missing_primitives", []),
        ]
    )
    confused = tuple(
        str(item.get("primitive", ""))
        for item in _coverage_confusions(evaluation_row)
        if str(item.get("primitive", ""))
    )
    if hook_kind == "literature_discovery":
        queries.extend(
            item
            for item in (
                f"{display_name} theorem assumptions proof route",
                " ".join((*selected_primitives[:6], *missing[:4])),
                f"{display_name} measurability integrability side conditions",
            )
            if item.strip()
        )
    elif _is_formal_library_grounding_hook(hook_kind):
        queries.extend((*selected_primitives[:8], *missing, *confused))
    elif hook_kind == "proof_state_feedback":
        queries.extend(
            item
            for item in (
                theorem_statement,
                theorem_skeleton,
                " ".join(selected_primitives[:8]),
                str(calibration_row.get("first_error", "")),
                str(calibration_row.get("repair_prompt", "")),
            )
            if item.strip()
        )
    elif hook_kind == "route_revision":
        queries.extend(
            item
            for item in (
                display_name,
                " ".join((*selected_primitives[:8], *missing, *confused)),
                str(calibration_row.get("repair_prompt", "")),
            )
            if item.strip()
        )
    return _str_tuple(queries)


def _target_primitives(
    plan_row: dict[str, Any],
    hook: dict[str, Any],
    hook_kind: str,
    evaluation_row: dict[str, Any],
) -> tuple[str, ...]:
    hook_targets = _str_tuple(hook.get("target_primitives", []))
    if hook_targets:
        return hook_targets
    selected = _str_tuple(plan_row.get("selected_primitives", []))
    missing = _str_tuple(
        [
            *evaluation_row.get("route_missing_primitives", []),
            *evaluation_row.get("delta_missing_primitives", []),
        ]
    )
    if hook_kind == "literature_discovery":
        source = _node_primitives(plan_row.get("source_discovery_nodes", []))
        first = _node_primitives(plan_row.get("first_principles_nodes", []))
        return _str_tuple([*source, *first, *missing, *selected[:6]])
    if _is_formal_library_grounding_hook(hook_kind):
        return _str_tuple([*missing, *selected])
    if hook_kind == "proof_state_feedback":
        minimal = _node_primitives(plan_row.get("minimal_additional_formalization_nodes", []))
        return _str_tuple([*minimal, *selected])
    if hook_kind == "route_revision":
        return _str_tuple([*missing, *selected])
    return selected


def _recommended_tools(
    hook: dict[str, Any],
    hook_kind: str,
    *,
    target_prover_family: str,
) -> tuple[str, ...]:
    tools = _target_scoped_recommended_tools(
        _str_tuple(hook.get("recommended_tools", [])),
        target_prover_family=target_prover_family,
    )
    if tools:
        return tools
    return _frontier_resource_adapters(
        hook_kind,
        target_prover_family=target_prover_family,
    )


def _target_scoped_recommended_tools(
    tools: tuple[str, ...],
    *,
    target_prover_family: str,
) -> tuple[str, ...]:
    if _prover_family_key(target_prover_family) in {"lean", "lean4"}:
        return tools
    return tuple(tool for tool in tools if not _lean_only_tool_hint(tool))


def _lean_only_tool_hint(tool: object) -> bool:
    text = str(tool or "").strip().lower()
    return any(
        token in text
        for token in (
            "leansearch",
            "lean search",
            "leanexplore",
            "loogle",
            "lean lsp",
            "lean-lsp",
            "lake build",
            "lake env lean",
            "local lean rag",
        )
    )


def _frontier_resource_adapters(
    hook_kind: str,
    *,
    target_prover_family: str = "",
) -> tuple[str, ...]:
    if hook_kind == "proof_state_feedback":
        return _proof_state_tools_for_target_prover(target_prover_family)
    if hook_kind == "route_revision":
        return _route_revision_tools_for_target_prover(target_prover_family)
    if hook_kind == "formal_library_grounding":
        return _formal_library_tools_for_target_prover(target_prover_family)
    if hook_kind == "lean_library_grounding" and _prover_family_key(
        target_prover_family
    ) not in {"lean", "lean4"}:
        return _formal_library_tools_for_target_prover(target_prover_family)
    return {
        "literature_discovery": (
            "Paperclip MCP/CLI",
            "PaperQA2",
            "OpenScholar",
            "Semantic Scholar API",
            "OpenAlex Works API",
            "arXiv",
            "GROBID",
            "Nougat",
            "olmOCR",
            "Marker",
        ),
        "lean_library_grounding": (
            "local Lean RAG DB",
            "LeanSearch",
            "LeanExplore",
            "Loogle",
            "lake env lean",
        ),
    }.get(hook_kind, tuple())


def _formal_library_tools_for_target_prover(
    target_prover_family: str,
) -> tuple[str, ...]:
    target = _prover_family_key(target_prover_family)
    if target in {"lean", "lean4"}:
        return (
            "local Lean RAG DB",
            "LeanSearch",
            "LeanExplore",
            "Loogle",
            "lake env lean",
        )
    if target in {"rocq", "coq"}:
        return (
            "local formal-source index",
            "Rocq/coq-lsp/SerAPI search",
            "target-prover library search/RAG",
        )
    if target in {"isabelle", "isabelle_hol", "hol"}:
        return (
            "local formal-source index",
            "Isabelle find_theorems/Sledgehammer",
            "target-prover library search/RAG",
        )
    if target == "agda":
        return (
            "local formal-source index",
            "Agda standard-library search",
            "target-prover library search/RAG",
        )
    return (
        "local formal-source index",
        "target prover library search",
        "target-prover library search/RAG",
    )


def _route_revision_tools_for_target_prover(
    target_prover_family: str,
) -> tuple[str, ...]:
    tools = (
        "Paperclip MCP/CLI",
        "PaperQA2",
        "OpenScholar",
        "local formal-source index",
        "target-prover library search/RAG",
    )
    return _str_tuple(
        [*tools, *_proof_state_tools_for_target_prover(target_prover_family)]
    )


def _proof_state_tools_for_target_prover(target_prover_family: str) -> tuple[str, ...]:
    target = _prover_family_key(target_prover_family)
    if target in {"lean", "lean4"}:
        return (
            "lean-lsp-mcp",
            "Lean LSP",
            "lake build",
        )
    if target in {"rocq", "coq"}:
        return (
            "Rocq/coq-lsp proof-state adapter",
            "SerAPI/sertop",
            "rocq/coq build command",
        )
    if target in {"isabelle", "isabelle_hol", "hol"}:
        return (
            "Isabelle server proof-state adapter",
            "find_theorems/Sledgehammer",
            "isabelle build",
        )
    if target == "agda":
        return (
            "Agda interaction-mode proof-state adapter",
            "agda --interaction-json",
            "agda type-check command",
        )
    return (
        "target-prover proof-state adapter",
        "target-prover LSP/kernel diagnostics",
        "target-prover build/check command",
    )


def _refinement_stage(hook_kind: str) -> str:
    return {
        "literature_discovery": "literature_evidence_search",
        "formal_library_grounding": "formal_library_coverage_mapping",
        "lean_library_grounding": "lean_coverage_mapping",
        "proof_state_feedback": "leaf_prover_attempts",
        "route_revision": "residual_feedback_revision",
    }.get(hook_kind, "")


def _owner_agent(hook_kind: str) -> str:
    return {
        "literature_discovery": "rag_retrieval",
        "formal_library_grounding": "formal_retrieval",
        "lean_library_grounding": "formal_retrieval",
        "proof_state_feedback": "formal_verifier",
        "route_revision": "planner",
    }.get(hook_kind, "planner")


def _acceptance_record(hook_kind: str) -> str:
    return {
        "literature_discovery": (
            "record theorem variants, assumptions, proof-step citations, and "
            "source passages as route evidence only"
        ),
        "formal_library_grounding": (
            "classify each informal node as exact_exists, near_exists, "
            "wrapper_needed, bridge_needed, definition_missing, or theory_missing"
        ),
        "lean_library_grounding": (
            "classify each informal node as exact_exists, near_exists, "
            "wrapper_needed, bridge_needed, definition_missing, or theory_missing"
        ),
        "proof_state_feedback": (
            "record residual goals, missing side conditions, typeclass failures, "
            "and diagnostics as route-revision evidence"
        ),
        "route_revision": (
            "update the informal knowledge DAG, formal realization DAG, selected "
            "delta, and do-not-formalize hints"
        ),
    }.get(hook_kind, "")


def _expected_artifacts(hook_kind: str) -> tuple[str, ...]:
    return {
        "literature_discovery": (
            "source-backed route evidence JSONL",
            "paper/source identifiers and cited theorem variants",
            "updated informal knowledge DAG nodes",
        ),
        "formal_library_grounding": (
            "formal declaration search hits",
            "coverage classification updates",
            "updated formal realization DAG nodes",
        ),
        "lean_library_grounding": (
            "Lean declaration search hits",
            "coverage classification updates",
            "updated Lean realization DAG nodes",
        ),
        "proof_state_feedback": (
            "leaf proof-attempt log or LSP diagnostic transcript",
            "residual goals and side-condition diagnostics",
            "route revision trigger updates",
        ),
        "route_revision": (
            "revised route plan manifest",
            "revised informal knowledge DAG",
            "revised formal realization DAG",
            "rerun-ready formal verifier queue or replay task",
        ),
    }.get(hook_kind, tuple())


def _execution_commands(
    hook_kind: str,
    *,
    target_prover_family: str = "",
) -> tuple[str, ...]:
    target = target_prover_family or "target prover"
    proof_state_attempt = (
        f"attempt selected theorem skeleton or bridge leaves with {target} "
        "proof-state and kernel-check tools"
    )
    return {
        "literature_discovery": (
            "run bounded literature search for the listed queries and attach source passages to route nodes",
            "rerun primitive-source coverage after accepting source evidence",
        ),
        "formal_library_grounding": (
            "query local formal-source indexes and target-prover library search for each target primitive",
            "update coverage labels before proposing new definitions or bridge lemmas",
        ),
        "lean_library_grounding": (
            "query local Lean RAG DB, LeanSearch, LeanExplore, and Loogle for each target primitive",
            "update coverage labels before proposing new definitions or bridge lemmas",
        ),
        "proof_state_feedback": (
            proof_state_attempt,
            "record residual goals, diagnostics, and missing side conditions as route feedback",
        ),
        "route_revision": (
            "revise the route DAG alignment using source, formal-library, and prover-feedback evidence",
            "rerun goal-conditioned minimal formalization planning before replay",
        ),
    }.get(hook_kind, tuple())


def _required_gate(hook_kind: str) -> str:
    return {
        "literature_discovery": (
            "accepted only as source evidence after citations are attached to "
            "informal route DAG nodes"
        ),
        "formal_library_grounding": (
            "accepted only after every searched primitive receives a coverage "
            "classification and candidate declaration reference"
        ),
        "lean_library_grounding": (
            "accepted only after every searched primitive receives a coverage "
            "classification and candidate declaration reference"
        ),
        "proof_state_feedback": (
            "accepted only as diagnostic feedback unless the target prover kernel "
            "verifies the theorem or bridge lemma"
        ),
        "route_revision": (
            "accepted only after the informal knowledge DAG, formal realization DAG, "
            "selected delta, and next work packets are regenerated"
        ),
    }.get(hook_kind, "")


def _priority_score(
    hook_kind: str,
    plan_row: dict[str, Any],
    *,
    evaluation_signal: str,
    prover_feedback_status: str,
) -> int:
    base = {
        "proof_state_feedback": 75,
        "formal_library_grounding": 70,
        "lean_library_grounding": 70,
        "literature_discovery": 65,
        "route_revision": 60,
    }.get(hook_kind, 40)
    if evaluation_signal != "no_evaluation_signal":
        base += 15
    if _is_failed_prover_feedback(prover_feedback_status):
        base += 20
    if plan_row.get("source_discovery_nodes"):
        base += 8
    if plan_row.get("first_principles_nodes"):
        base += 12
    base += min(10, int(plan_row.get("goal_conditioned_cost", 0) or 0) // 4)
    return base


def _evaluation_signal(row: dict[str, Any]) -> str:
    if not row:
        return "no_evaluation_signal"
    signals: list[str] = []
    if not bool(row.get("ok", True)):
        signals.append("evaluation_row_not_ok")
    if row.get("route_missing_primitives"):
        signals.append("route_missing_primitives")
    if row.get("route_extra_primitives"):
        signals.append("route_extra_primitives")
    if row.get("delta_missing_primitives"):
        signals.append("delta_missing_primitives")
    if row.get("delta_unnecessary_primitives"):
        signals.append("delta_unnecessary_primitives")
    if row.get("coverage_classification_confusions"):
        signals.append("coverage_classification_confusions")
    return ",".join(signals) if signals else "no_evaluation_signal"


def _prover_feedback_status(row: dict[str, Any]) -> str:
    if not row:
        return "no_calibration_signal"
    return str(row.get("replay_calibration_status", "")) or "no_calibration_signal"


def _is_failed_prover_feedback(status: str) -> bool:
    return status not in {
        "",
        "no_calibration_signal",
        "awaiting_full_route_attempt",
        "full_route_kernel_verified",
    }


def _coverage_confusions(row: dict[str, Any]) -> tuple[dict[str, object], ...]:
    confusions = row.get("coverage_classification_confusions", [])
    if not isinstance(confusions, list):
        return tuple()
    return tuple(item for item in confusions if isinstance(item, dict))


def _rank_rows(
    rows: list[FormalizationGapPlannerRefinementQueueRow],
) -> list[FormalizationGapPlannerRefinementQueueRow]:
    ranked = sorted(
        rows,
        key=lambda row: (
            -row.priority_score,
            row.display_name,
            row.hook_kind,
            row.refinement_item_id,
        ),
    )
    return [
        FormalizationGapPlannerRefinementQueueRow(**{**asdict(row), "rank": index})
        for index, row in enumerate(ranked, start=1)
    ]


def _diagnostic_index(rows: Any) -> dict[str, dict[str, Any]]:
    index: dict[str, dict[str, Any]] = {}
    if not isinstance(rows, list):
        return index
    for row in rows:
        if not isinstance(row, dict):
            continue
        for field_name in ("route_id", "goal_plan_id", "display_name"):
            value = str(row.get(field_name, ""))
            if value:
                index[f"{field_name}:{value}"] = row
    return index


def _match_diagnostic(
    plan_row: dict[str, Any],
    index: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    for field_name in ("route_id", "goal_plan_id", "display_name"):
        value = str(plan_row.get(field_name, ""))
        if value and f"{field_name}:{value}" in index:
            return index[f"{field_name}:{value}"]
    return {}


def _node_primitives(nodes: Any) -> tuple[str, ...]:
    primitives: list[str] = []
    if not isinstance(nodes, (list, tuple)):
        return tuple()
    for node in nodes:
        if not isinstance(node, dict):
            continue
        primitive = str(node.get("primitive", "") or node.get("label", ""))
        if primitive:
            primitives.append(primitive)
    return _str_tuple(primitives)


def _str_tuple(values: Any) -> tuple[str, ...]:
    if isinstance(values, str):
        return (values,) if values else tuple()
    try:
        iterator = iter(values)
    except TypeError:
        return tuple()
    items: list[str] = []
    for item in iterator:
        value = str(item)
        if value:
            items.append(value)
    return tuple(sorted(dict.fromkeys(items)))


def _dict_tuple(values: Any) -> tuple[dict[str, object], ...]:
    if not isinstance(values, (list, tuple)):
        return tuple()
    return tuple(dict(value) for value in values if isinstance(value, dict))


def _read_json(path: Path | None, errors: list[str]) -> dict[str, Any]:
    if path is None:
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        errors.append(f"missing JSON file: {path}")
        return {}
    except Exception as exc:
        errors.append(f"failed to parse {path}: {type(exc).__name__}: {exc}")
        return {}
    return payload if isinstance(payload, dict) else {}


def _markdown_report(payload: dict[str, object]) -> str:
    lines = [
        "# Formalization Gap Planner Refinement Queue",
        "",
        f"- Source plan rows: {payload.get('n_plan_rows')}",
        f"- Refinement items: {payload.get('n_refinement_items')}",
        f"- Ready: {payload.get('n_ready')}",
        f"- Literature discovery: {payload.get('n_literature_discovery_items')}",
        f"- Formal library grounding: {payload.get('n_formal_library_grounding_items')}",
        f"- Lean library grounding: {payload.get('n_lean_library_grounding_items')}",
        f"- Proof-state feedback: {payload.get('n_proof_state_feedback_items')}",
        f"- Route revision: {payload.get('n_route_revision_items')}",
        f"- Target prover families: {payload.get('by_target_prover_family')}",
        f"- Evaluation signals: {payload.get('n_with_evaluation_signal')}",
        f"- Prover feedback signals: {payload.get('n_with_prover_feedback')}",
        f"- Work-item schema valid: {payload.get('n_item_schema_valid')}/{payload.get('n_refinement_items')}",
        f"- All OK: {payload.get('all_ok')}",
        "",
        "## Boundary",
        "",
        "These rows are interactive refinement work orders, not theorem proof evidence.",
        "",
        "## Rows",
        "",
    ]
    for row in payload.get("rows", []):
        if not isinstance(row, dict):
            continue
        lines.append(
            f"- #{row.get('rank')} `{row.get('display_name')}` "
            f"{row.get('hook_kind')} target={row.get('target_prover_family')} "
            f"priority={row.get('priority_score')} "
            f"status={row.get('status')}"
        )
        if row.get("target_primitives"):
            lines.append(
                "  target primitives: "
                + ", ".join(str(item) for item in row.get("target_primitives", [])[:8])
            )
        if row.get("evaluation_signal") != "no_evaluation_signal":
            lines.append(f"  evaluation signal: {row.get('evaluation_signal')}")
        if row.get("prover_feedback_status") not in {
            "",
            "no_calibration_signal",
        }:
            lines.append(f"  prover feedback: {row.get('prover_feedback_status')}")
    return "\n".join(lines) + "\n"
