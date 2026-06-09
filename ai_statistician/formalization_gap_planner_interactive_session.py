from __future__ import annotations

import json
import re
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from .fingerprint import stable_hash
from .formalization_gap_planner_contract import (
    LIBRARY_AWARE_FORMALIZATION_GAP_PLANNER_NAME,
    PORTABLE_FORMALIZATION_GAP_PLAN_SCHEMA_ID,
    PROOF_EVIDENCE_BOUNDARY as PLANNER_PROOF_EVIDENCE_BOUNDARY,
)
from .formalization_gap_planner_component_resource_registry import (
    COMPONENT_RESOURCE_CONTRACT_ROW_SCHEMA_ID,
    COMPONENT_RESOURCE_EXECUTION_PLAN_SCHEMA_ID,
    COMPONENT_RESOURCE_REGISTRY_COMPONENT_ROW_SCHEMA_ID,
    COMPONENT_RESOURCE_REGISTRY_RESOURCE_ROW_SCHEMA_ID,
)


FORMALIZATION_GAP_PLANNER_INTERACTIVE_SESSION_SCHEMA_VERSION = 1
PROOF_EVIDENCE_STATUS = "FORMALIZATION_GAP_PLANNER_INTERACTIVE_SESSION_NOT_PROOF_EVIDENCE"
PROOF_EVIDENCE_BOUNDARY = (
    "Formalization gap planner interactive-session rows summarize bounded "
    "literature, library-grounding, proof-state, and route-replanning actions. "
    "They are orchestration and route-planning evidence, not theorem proof "
    "evidence. A theorem or bridge lemma is proved only by target-prover kernel "
    "verification."
)
INTERACTIVE_SESSION_ROW_SCHEMA_ID = (
    "urn:ai-statistician:schemas:"
    "formalization-gap-planner-interactive-session-row:1"
)
INTERACTIVE_DECISION_POLICY_ROW_SCHEMA_ID = (
    "urn:ai-statistician:schemas:"
    "formalization-gap-planner-interactive-decision-policy-row:1"
)
SESSION_STATES = (
    "BUILD_REFINEMENT_QUEUE",
    "RUN_REFINEMENT_ADAPTERS",
    "RUN_ROUTE_STABILITY_AUDIT",
    "REVIEW_ROUTE_STABILITY_DECISION",
    "AWAITING_REFINEMENT_RESPONSES",
    "EXPAND_LITERATURE_EVIDENCE",
    "EXPAND_FORMAL_LIBRARY_GROUNDING",
    "EXPAND_LEAN_LIBRARY_GROUNDING",
    "EXPAND_PROOF_STATE_FEEDBACK",
    "ROUTE_REPLAN_REQUIRED",
    "ROUTE_STABLE_READY_FOR_REPLAY",
)
NEXT_INTERACTION_KINDS = (
    "build_refinement_queue",
    "refinement_adapter_execution",
    "route_stability_audit",
    "await_refinement_response",
    "literature_discovery",
    "formal_library_grounding",
    "lean_library_grounding",
    "proof_state_feedback",
    "route_revision",
    "route_replan",
    "target_prover_replay",
)


@dataclass(frozen=True)
class FormalizationGapPlannerInteractiveSessionRow:
    schema_version: int
    interactive_session_row_id: str
    goal_plan_id: str
    route_id: str
    display_name: str
    route_class: str
    pareto_profile: str
    session_state: str
    next_interaction_kind: str
    next_owner_agent: str
    next_tools: tuple[str, ...]
    next_queries: tuple[str, ...]
    next_commands: tuple[str, ...]
    user_checkpoint: str
    evidence_summary: dict[str, int]
    coverage_summary: dict[str, int]
    stability_decision: str
    stable_under_current_evidence_bound: bool
    needs_more_literature: bool
    needs_more_formal_grounding: bool
    needs_more_lean_grounding: bool
    needs_more_proof_state_feedback: bool
    needs_route_replanning: bool
    awaiting_hook_kinds: tuple[str, ...]
    rejected_hook_kinds: tuple[str, ...]
    responded_hook_kinds: tuple[str, ...]
    resource_response_awaiting_request_ids: tuple[str, ...]
    resource_response_rejected_request_ids: tuple[str, ...]
    residual_goals: tuple[str, ...]
    source_refs: tuple[str, ...]
    formal_declaration_hits: tuple[dict[str, object], ...]
    lean_declaration_hits: tuple[dict[str, object], ...]
    route_revision_reasons: tuple[str, ...]
    triage_class: str
    prover_triage_class: str
    applied_prover_attempt_classes: tuple[str, ...]
    target_prover_families: tuple[str, ...]
    triage_required_gate: str
    replan_required: bool
    standalone_seed_route_id: str
    route_cost: float
    proof_evidence_status: str
    proof_evidence_boundary: str
    ok: bool
    errors: tuple[str, ...] = ()


@dataclass(frozen=True)
class FormalizationGapPlannerInteractiveDecisionPolicyRow:
    schema_version: int
    decision_policy_row_id: str
    interactive_session_row_id: str
    goal_plan_id: str
    route_id: str
    display_name: str
    session_state: str
    next_interaction_kind: str
    decision_rationale: str
    trigger_signals: tuple[str, ...]
    evidence_inputs: tuple[str, ...]
    required_tool_contracts: tuple[str, ...]
    component_ids: tuple[str, ...]
    local_first_resource_ids: tuple[str, ...]
    frontier_escalation_resource_ids: tuple[str, ...]
    resource_contract_ids: tuple[str, ...]
    required_quality_signals: tuple[str, ...]
    quality_gates: tuple[str, ...]
    response_validation_signals: tuple[str, ...]
    stop_conditions: tuple[str, ...]
    fallback_actions: tuple[str, ...]
    bounded_evidence_claim: str
    resource_selection_rationale: str
    proof_evidence_status: str
    proof_evidence_boundary: str
    ok: bool
    errors: tuple[str, ...] = ()


def export_formalization_gap_planner_interactive_session(
    goal_conditioned_minimal_formalization_plan_dir: Path,
    out_dir: Path | None = None,
    *,
    formalization_gap_planner_refinement_queue_dir: Path | None = None,
    formalization_gap_planner_refinement_evidence_dir: Path | None = None,
    formalization_gap_planner_route_stability_audit_dir: Path | None = None,
    formalization_gap_planner_route_replan_handoff_dir: Path | None = None,
    formalization_gap_planner_proof_state_triage_dir: Path | None = None,
    formalization_gap_planner_component_resource_registry_dir: Path | None = None,
) -> dict[str, object]:
    """Export a route-level interaction ledger for the next planning round.

    The session ledger is intentionally thin: it joins existing planner,
    refinement, evidence, stability, handoff, and proof-state triage artifacts
    by route id and records the next bounded action for each route.
    """

    errors: list[str] = []
    plan_path = (
        goal_conditioned_minimal_formalization_plan_dir
        / "goal_conditioned_minimal_formalization_plan_manifest.json"
    )
    plan_payload = _read_json(plan_path, errors)
    if plan_payload.get("component_name") != LIBRARY_AWARE_FORMALIZATION_GAP_PLANNER_NAME:
        errors.append("input manifest is not the library-aware formalization gap planner")
    if plan_payload.get("portable_schema_id") != PORTABLE_FORMALIZATION_GAP_PLAN_SCHEMA_ID:
        errors.append("input manifest portable schema id mismatch")

    queue_payload = _optional_manifest(
        formalization_gap_planner_refinement_queue_dir,
        "formalization_gap_planner_refinement_queue_manifest.json",
        errors,
    )
    evidence_payload = _optional_manifest(
        formalization_gap_planner_refinement_evidence_dir,
        "formalization_gap_planner_refinement_evidence_manifest.json",
        errors,
    )
    stability_payload = _optional_manifest(
        formalization_gap_planner_route_stability_audit_dir,
        "formalization_gap_planner_route_stability_audit_manifest.json",
        errors,
    )
    handoff_payload = _optional_manifest(
        formalization_gap_planner_route_replan_handoff_dir,
        "formalization_gap_planner_route_replan_handoff_manifest.json",
        errors,
    )
    triage_payload = _optional_manifest(
        formalization_gap_planner_proof_state_triage_dir,
        "formalization_gap_planner_proof_state_triage_manifest.json",
        errors,
    )
    component_resource_registry_payload = _optional_manifest(
        formalization_gap_planner_component_resource_registry_dir,
        "formalization_gap_planner_component_resource_registry_manifest.json",
        errors,
    )
    resource_registry = _resource_registry_context(
        component_resource_registry_payload,
        registry_dir=formalization_gap_planner_component_resource_registry_dir,
        errors=errors,
    )

    plan_rows = [row for row in plan_payload.get("rows", []) if isinstance(row, dict)]
    queue_index = _row_index(queue_payload.get("rows", []))
    evidence_index = _row_index(evidence_payload.get("rows", []))
    stability_index = _row_index(stability_payload.get("rows", []))
    handoff_index = _row_index(handoff_payload.get("rows", []))
    triage_index = _row_index(triage_payload.get("rows", []))

    rows = [
        _session_row(
            plan_row,
            queue_index,
            evidence_index,
            stability_index,
            handoff_index,
            triage_index,
        )
        for plan_row in plan_rows
    ]
    row_dicts = [asdict(row) for row in rows]
    row_schema = interactive_session_row_json_schema()
    row_schema_errors = [
        validate_interactive_session_row(row_dict, row_schema)
        for row_dict in row_dicts
    ]
    n_row_schema_valid = sum(1 for row_errors in row_schema_errors if not row_errors)
    n_row_schema_invalid = len(row_schema_errors) - n_row_schema_valid
    decision_policy_rows = [
        _decision_policy_row(row, resource_registry) for row in rows
    ]
    decision_policy_row_dicts = [asdict(row) for row in decision_policy_rows]
    decision_policy_row_schema = interactive_decision_policy_row_json_schema()
    decision_policy_schema_errors = [
        validate_interactive_decision_policy_row(row_dict, decision_policy_row_schema)
        for row_dict in decision_policy_row_dicts
    ]
    n_decision_policy_schema_valid = sum(
        1 for row_errors in decision_policy_schema_errors if not row_errors
    )
    n_decision_policy_schema_invalid = (
        len(decision_policy_schema_errors) - n_decision_policy_schema_valid
    )
    by_state = Counter(row.session_state for row in rows)
    by_next = Counter(row.next_interaction_kind for row in rows)
    by_owner = Counter(row.next_owner_agent for row in rows)
    payload: dict[str, object] = {
        "schema_version": FORMALIZATION_GAP_PLANNER_INTERACTIVE_SESSION_SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "component_name": "formalization_gap_planner_interactive_session",
        "goal_conditioned_minimal_formalization_plan_dir": str(
            goal_conditioned_minimal_formalization_plan_dir
        ),
        "goal_conditioned_minimal_formalization_plan_manifest": str(plan_path),
        "formalization_gap_planner_refinement_queue_dir": str(
            formalization_gap_planner_refinement_queue_dir or ""
        ),
        "formalization_gap_planner_refinement_evidence_dir": str(
            formalization_gap_planner_refinement_evidence_dir or ""
        ),
        "formalization_gap_planner_route_stability_audit_dir": str(
            formalization_gap_planner_route_stability_audit_dir or ""
        ),
        "formalization_gap_planner_route_replan_handoff_dir": str(
            formalization_gap_planner_route_replan_handoff_dir or ""
        ),
        "formalization_gap_planner_proof_state_triage_dir": str(
            formalization_gap_planner_proof_state_triage_dir or ""
        ),
        "formalization_gap_planner_component_resource_registry_dir": str(
            formalization_gap_planner_component_resource_registry_dir or ""
        ),
        "n_plan_rows": len(plan_rows),
        "n_session_rows": len(rows),
        "n_ok": sum(1 for row in rows if row.ok),
        "n_build_refinement_queue": by_next.get("build_refinement_queue", 0),
        "n_run_literature_search": by_next.get("literature_discovery", 0),
        "n_run_formal_grounding": (
            by_next.get("formal_library_grounding", 0)
            + by_next.get("lean_library_grounding", 0)
        ),
        "n_run_lean_grounding": by_next.get("lean_library_grounding", 0),
        "n_run_proof_state_feedback": by_next.get("proof_state_feedback", 0),
        "n_run_route_replan": by_next.get("route_replan", 0),
        "n_run_target_prover_replay": by_next.get("target_prover_replay", 0),
        "n_waiting_for_adapter_responses": by_next.get("await_refinement_response", 0),
        "n_rows_with_source_refs": sum(1 for row in rows if row.source_refs),
        "n_rows_with_residual_goals": sum(1 for row in rows if row.residual_goals),
        "n_rows_requiring_replan": sum(1 for row in rows if row.replan_required),
        "n_row_schema_valid": n_row_schema_valid,
        "n_row_schema_invalid": n_row_schema_invalid,
        "n_decision_policy_rows": len(decision_policy_rows),
        "n_decision_policy_rows_with_resource_contracts": sum(
            1 for row in decision_policy_rows if row.resource_contract_ids
        ),
        "n_decision_policy_rows_with_frontier_resources": sum(
            1 for row in decision_policy_rows if row.frontier_escalation_resource_ids
        ),
        "n_decision_policy_rows_with_required_quality_signals": sum(
            1 for row in decision_policy_rows if row.required_quality_signals
        ),
        "n_decision_policy_rows_with_quality_gates": sum(
            1 for row in decision_policy_rows if row.quality_gates
        ),
        "n_decision_policy_rows_with_response_validation_signals": sum(
            1 for row in decision_policy_rows if row.response_validation_signals
        ),
        "n_decision_policy_row_schema_valid": n_decision_policy_schema_valid,
        "n_decision_policy_row_schema_invalid": n_decision_policy_schema_invalid,
        "interactive_session_row_schema": row_schema,
        "interactive_decision_policy_row_schema": decision_policy_row_schema,
        "all_ok": (
            not errors
            and bool(rows)
            and all(row.ok for row in rows)
            and n_row_schema_invalid == 0
            and n_decision_policy_schema_invalid == 0
        ),
        "errors": errors,
        "by_session_state": dict(sorted(by_state.items())),
        "by_next_interaction_kind": dict(sorted(by_next.items())),
        "by_next_owner_agent": dict(sorted(by_owner.items())),
        "rows": row_dicts,
        "decision_policy_rows": decision_policy_row_dicts,
        "interactive_session_fingerprint": stable_hash(row_dicts),
        "interactive_decision_policy_fingerprint": stable_hash(
            decision_policy_row_dicts
        ),
        "proof_evidence_status": PROOF_EVIDENCE_STATUS,
        "proof_evidence_boundary": PROOF_EVIDENCE_BOUNDARY,
        "planner_proof_evidence_boundary": PLANNER_PROOF_EVIDENCE_BOUNDARY,
        "bounded_interaction_policy": [
            "run only the next focused literature, library, proof-state, or replan action for each route",
            "do not broaden literature search when the stability audit says a route is stable under the current evidence bound",
            "do not treat route stability, local source hits, or proof-state diagnostics as kernel proof evidence",
            "rerun the standalone planner after accepted route revisions before exporting target-prover replay tasks",
        ],
        "limitations": [
            "session rows summarize existing planner artifacts and do not call external MCPs directly",
            "tool recommendations require separate adapter execution and evidence validation",
            "resource contract links are populated only when a component-resource registry manifest is provided",
            "target-prover replay and kernel verification remain outside this session ledger",
        ],
    }
    if out_dir is not None:
        out_dir.mkdir(parents=True, exist_ok=True)
        (
            out_dir / "formalization_gap_planner_interactive_session_manifest.json"
        ).write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
        (
            out_dir / "formalization_gap_planner_interactive_session_row.schema.json"
        ).write_text(json.dumps(row_schema, indent=2), encoding="utf-8")
        (
            out_dir
            / "formalization_gap_planner_interactive_decision_policy_row.schema.json"
        ).write_text(json.dumps(decision_policy_row_schema, indent=2), encoding="utf-8")
        (out_dir / "formalization_gap_planner_interactive_session.jsonl").write_text(
            "\n".join(json.dumps(asdict(row), sort_keys=True) for row in rows)
            + ("\n" if rows else ""),
            encoding="utf-8",
        )
        (
            out_dir
            / "formalization_gap_planner_interactive_decision_policy.jsonl"
        ).write_text(
            "\n".join(
                json.dumps(asdict(row), sort_keys=True)
                for row in decision_policy_rows
            )
            + ("\n" if decision_policy_rows else ""),
            encoding="utf-8",
        )
        (out_dir / "formalization_gap_planner_interactive_session.md").write_text(
            _markdown_report(payload),
            encoding="utf-8",
        )
    return payload


def interactive_session_row_json_schema() -> dict[str, object]:
    """JSON Schema for public interactive next-action rows."""

    string_array = {"type": "array", "items": {"type": "string"}}
    object_array = {"type": "array", "items": {"type": "object"}}
    integer_map = {"type": "object", "additionalProperties": {"type": "integer"}}
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": INTERACTIVE_SESSION_ROW_SCHEMA_ID,
        "title": "Formalization Gap Planner Interactive Session Row",
        "description": (
            "Route-level next-action contract for bounded literature search, "
            "formal-library grounding, proof-state feedback, route replanning, "
            "or target-prover replay. Rows are not theorem proof evidence."
        ),
        "type": "object",
        "additionalProperties": True,
        "required": [
            "schema_version",
            "interactive_session_row_id",
            "goal_plan_id",
            "route_id",
            "display_name",
            "session_state",
            "next_interaction_kind",
            "next_owner_agent",
            "next_tools",
            "next_queries",
            "next_commands",
            "user_checkpoint",
            "evidence_summary",
            "coverage_summary",
            "stable_under_current_evidence_bound",
            "needs_more_literature",
            "needs_more_formal_grounding",
            "needs_more_lean_grounding",
            "needs_more_proof_state_feedback",
            "needs_route_replanning",
            "awaiting_hook_kinds",
            "rejected_hook_kinds",
            "responded_hook_kinds",
            "resource_response_awaiting_request_ids",
            "resource_response_rejected_request_ids",
            "replan_required",
            "route_cost",
            "proof_evidence_status",
            "proof_evidence_boundary",
            "ok",
        ],
        "properties": {
            "schema_version": {
                "type": "integer",
                "const": FORMALIZATION_GAP_PLANNER_INTERACTIVE_SESSION_SCHEMA_VERSION,
            },
            "interactive_session_row_id": {"type": "string", "minLength": 1},
            "goal_plan_id": {"type": "string", "minLength": 1},
            "route_id": {"type": "string", "minLength": 1},
            "display_name": {"type": "string", "minLength": 1},
            "route_class": {"type": "string"},
            "pareto_profile": {"type": "string"},
            "session_state": {"enum": list(SESSION_STATES)},
            "next_interaction_kind": {"enum": list(NEXT_INTERACTION_KINDS)},
            "next_owner_agent": {"type": "string", "minLength": 1},
            "next_tools": string_array,
            "next_queries": string_array,
            "next_commands": string_array,
            "user_checkpoint": {"type": "string", "minLength": 1},
            "evidence_summary": integer_map,
            "coverage_summary": integer_map,
            "stability_decision": {"type": "string"},
            "stable_under_current_evidence_bound": {"type": "boolean"},
            "needs_more_literature": {"type": "boolean"},
            "needs_more_formal_grounding": {"type": "boolean"},
            "needs_more_lean_grounding": {"type": "boolean"},
            "needs_more_proof_state_feedback": {"type": "boolean"},
            "needs_route_replanning": {"type": "boolean"},
            "awaiting_hook_kinds": string_array,
            "rejected_hook_kinds": string_array,
            "responded_hook_kinds": string_array,
            "resource_response_awaiting_request_ids": string_array,
            "resource_response_rejected_request_ids": string_array,
            "residual_goals": string_array,
            "source_refs": string_array,
            "formal_declaration_hits": object_array,
            "lean_declaration_hits": object_array,
            "route_revision_reasons": string_array,
            "triage_class": {"type": "string"},
            "prover_triage_class": {"type": "string"},
            "applied_prover_attempt_classes": string_array,
            "target_prover_families": string_array,
            "triage_required_gate": {"type": "string"},
            "replan_required": {"type": "boolean"},
            "standalone_seed_route_id": {"type": "string"},
            "route_cost": {"type": "number"},
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


def interactive_decision_policy_row_json_schema() -> dict[str, object]:
    """JSON Schema for public interactive decision-policy rows."""

    string_array = {"type": "array", "items": {"type": "string"}}
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": INTERACTIVE_DECISION_POLICY_ROW_SCHEMA_ID,
        "title": "Formalization Gap Planner Interactive Decision Policy Row",
        "description": (
            "Route-level policy justification for why the next bounded action "
            "should be literature search, formal-library grounding, proof-state "
            "feedback, route replan, or target-prover replay. Rows are not "
            "theorem proof evidence."
        ),
        "type": "object",
        "additionalProperties": True,
        "required": [
            "schema_version",
            "decision_policy_row_id",
            "interactive_session_row_id",
            "goal_plan_id",
            "route_id",
            "display_name",
            "session_state",
            "next_interaction_kind",
            "decision_rationale",
            "trigger_signals",
            "evidence_inputs",
            "required_tool_contracts",
            "component_ids",
            "local_first_resource_ids",
            "frontier_escalation_resource_ids",
            "resource_contract_ids",
            "required_quality_signals",
            "quality_gates",
            "response_validation_signals",
            "stop_conditions",
            "fallback_actions",
            "bounded_evidence_claim",
            "resource_selection_rationale",
            "proof_evidence_status",
            "proof_evidence_boundary",
            "ok",
        ],
        "properties": {
            "schema_version": {
                "type": "integer",
                "const": FORMALIZATION_GAP_PLANNER_INTERACTIVE_SESSION_SCHEMA_VERSION,
            },
            "decision_policy_row_id": {"type": "string", "minLength": 1},
            "interactive_session_row_id": {"type": "string", "minLength": 1},
            "goal_plan_id": {"type": "string", "minLength": 1},
            "route_id": {"type": "string", "minLength": 1},
            "display_name": {"type": "string", "minLength": 1},
            "session_state": {"enum": list(SESSION_STATES)},
            "next_interaction_kind": {"enum": list(NEXT_INTERACTION_KINDS)},
            "decision_rationale": {"type": "string", "minLength": 1},
            "trigger_signals": string_array,
            "evidence_inputs": string_array,
            "required_tool_contracts": string_array,
            "component_ids": string_array,
            "local_first_resource_ids": string_array,
            "frontier_escalation_resource_ids": string_array,
            "resource_contract_ids": string_array,
            "required_quality_signals": string_array,
            "quality_gates": string_array,
            "response_validation_signals": string_array,
            "stop_conditions": string_array,
            "fallback_actions": string_array,
            "bounded_evidence_claim": {"type": "string", "minLength": 1},
            "resource_selection_rationale": {"type": "string", "minLength": 1},
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


def validate_interactive_session_row(
    row: dict[str, Any],
    schema: dict[str, object] | None = None,
) -> tuple[str, ...]:
    """Validate an interactive next-action row against the public schema."""

    row_schema = schema or interactive_session_row_json_schema()
    errors: list[str] = []
    required = row_schema.get("required", [])
    if isinstance(required, list):
        for field_name in required:
            if isinstance(field_name, str) and field_name not in row:
                errors.append(f"{field_name} required")
    properties = row_schema.get("properties", {})
    if isinstance(properties, dict):
        for field_name, field_schema in properties.items():
            if not isinstance(field_name, str) or field_name not in row:
                continue
            if isinstance(field_schema, dict):
                errors.extend(
                    _schema_property_errors(field_name, row[field_name], field_schema)
                )
    errors.extend(_declaration_hit_scope_errors(row))
    return tuple(errors)


def validate_interactive_decision_policy_row(
    row: dict[str, Any],
    schema: dict[str, object] | None = None,
) -> tuple[str, ...]:
    """Validate an interactive decision-policy row against the public schema."""

    row_schema = schema or interactive_decision_policy_row_json_schema()
    errors: list[str] = []
    required = row_schema.get("required", [])
    if isinstance(required, list):
        for field_name in required:
            if isinstance(field_name, str) and field_name not in row:
                errors.append(f"{field_name} required")
    properties = row_schema.get("properties", {})
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
    elif expected_type == "number":
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            errors.append(f"{field_name} must be number")
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
    elif expected_type == "object":
        if not isinstance(value, dict):
            errors.append(f"{field_name} must be object")
        else:
            additional = field_schema.get("additionalProperties")
            if isinstance(additional, dict) and additional.get("type") == "integer":
                bad_keys = [
                    str(key)
                    for key, item in value.items()
                    if not isinstance(item, int) or isinstance(item, bool)
                ]
                if bad_keys:
                    errors.append(
                        f"{field_name} values must be integer for keys "
                        + ",".join(bad_keys)
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


def _decision_policy_row(
    row: FormalizationGapPlannerInteractiveSessionRow,
    resource_registry: dict[str, Any],
) -> FormalizationGapPlannerInteractiveDecisionPolicyRow:
    trigger_signals = _decision_trigger_signals(row)
    evidence_inputs = _decision_evidence_inputs(row)
    required_contracts = _required_tool_contracts(row.next_interaction_kind)
    resource_selection = _resource_selection_for_interaction(
        row,
        resource_registry,
    )
    stop_conditions = _stop_conditions(row.next_interaction_kind)
    fallback_actions = _fallback_actions(row.next_interaction_kind)
    errors: list[str] = []
    if not trigger_signals:
        errors.append("trigger_signals missing")
    if not evidence_inputs:
        errors.append("evidence_inputs missing")
    if not required_contracts:
        errors.append("required_tool_contracts missing")
    errors.extend(resource_selection["errors"])
    if not stop_conditions:
        errors.append("stop_conditions missing")
    rationale = _decision_rationale(row, trigger_signals)
    return FormalizationGapPlannerInteractiveDecisionPolicyRow(
        schema_version=FORMALIZATION_GAP_PLANNER_INTERACTIVE_SESSION_SCHEMA_VERSION,
        decision_policy_row_id="formalization_gap_planner_interactive_decision_policy:"
        + stable_hash(
            [
                row.interactive_session_row_id,
                row.next_interaction_kind,
                trigger_signals,
                evidence_inputs,
            ]
        )[:16],
        interactive_session_row_id=row.interactive_session_row_id,
        goal_plan_id=row.goal_plan_id,
        route_id=row.route_id,
        display_name=row.display_name,
        session_state=row.session_state,
        next_interaction_kind=row.next_interaction_kind,
        decision_rationale=rationale,
        trigger_signals=trigger_signals,
        evidence_inputs=evidence_inputs,
        required_tool_contracts=required_contracts,
        component_ids=resource_selection["component_ids"],
        local_first_resource_ids=resource_selection["local_first_resource_ids"],
        frontier_escalation_resource_ids=resource_selection[
            "frontier_escalation_resource_ids"
        ],
        resource_contract_ids=resource_selection["resource_contract_ids"],
        required_quality_signals=resource_selection["required_quality_signals"],
        quality_gates=resource_selection["quality_gates"],
        response_validation_signals=resource_selection[
            "response_validation_signals"
        ],
        stop_conditions=stop_conditions,
        fallback_actions=fallback_actions,
        bounded_evidence_claim=(
            "This row justifies the next bounded planner action under the "
            "current evidence snapshot; it does not certify route truth or "
            "kernel proof status."
        ),
        resource_selection_rationale=resource_selection[
            "resource_selection_rationale"
        ],
        proof_evidence_status=PROOF_EVIDENCE_STATUS,
        proof_evidence_boundary=PROOF_EVIDENCE_BOUNDARY,
        ok=not errors,
        errors=tuple(errors),
    )


NEXT_INTERACTION_COMPONENT_IDS: dict[str, tuple[str, ...]] = {
    "build_refinement_queue": (
        "literature_grounded_route_synthesis",
        "formal_library_coverage_mapping",
        "prover_feedback_refinement",
    ),
    "refinement_adapter_execution": (
        "literature_grounded_route_synthesis",
        "formal_library_coverage_mapping",
        "prover_feedback_refinement",
    ),
    "await_refinement_response": (
        "literature_grounded_route_synthesis",
        "formal_library_coverage_mapping",
        "prover_feedback_refinement",
    ),
    "literature_discovery": ("literature_grounded_route_synthesis",),
    "formal_library_grounding": ("formal_library_coverage_mapping",),
    "lean_library_grounding": ("formal_library_coverage_mapping",),
    "proof_state_feedback": ("prover_feedback_refinement",),
    "route_revision": ("route_revision_handoff",),
    "route_replan": (
        "route_revision_handoff",
        "informal_route_dag_decomposition",
        "minimal_delta_and_or_planning",
    ),
    "target_prover_replay": (
        "cross_prover_public_reuse",
        "prover_feedback_refinement",
    ),
    "route_stability_audit": ("route_revision_handoff",),
}


def _resource_registry_context(
    payload: dict[str, Any],
    *,
    registry_dir: Path | None,
    errors: list[str],
) -> dict[str, Any]:
    if registry_dir is None:
        return {
            "available": False,
            "component_index": {},
            "execution_plan_index": {},
            "resource_contract_index": {},
        }
    if payload.get("component_name") != "formalization_gap_planner_component_resource_registry":
        errors.append(
            "component-resource registry manifest is not the component-resource registry"
        )
    if payload.get("component_row_schema", {}).get(
        "$id"
    ) != COMPONENT_RESOURCE_REGISTRY_COMPONENT_ROW_SCHEMA_ID:
        errors.append("component-resource registry component-row schema id mismatch")
    if payload.get("resource_row_schema", {}).get(
        "$id"
    ) != COMPONENT_RESOURCE_REGISTRY_RESOURCE_ROW_SCHEMA_ID:
        errors.append("component-resource registry resource-row schema id mismatch")
    if payload.get("execution_plan_row_schema", {}).get(
        "$id"
    ) != COMPONENT_RESOURCE_EXECUTION_PLAN_SCHEMA_ID:
        errors.append("component-resource registry execution-plan schema id mismatch")
    if payload.get("resource_contract_row_schema", {}).get(
        "$id"
    ) != COMPONENT_RESOURCE_CONTRACT_ROW_SCHEMA_ID:
        errors.append("component-resource registry contract-row schema id mismatch")
    return {
        "available": True,
        "component_index": {
            str(row.get("component_id", "")): row
            for row in payload.get("component_rows", [])
            if isinstance(row, dict) and row.get("component_id")
        },
        "execution_plan_index": {
            str(row.get("component_id", "")): row
            for row in payload.get("execution_plan_rows", [])
            if isinstance(row, dict) and row.get("component_id")
        },
        "resource_contract_index": {
            str(row.get("resource_id", "")): row
            for row in payload.get("resource_contract_rows", [])
            if isinstance(row, dict) and row.get("resource_id")
        },
    }


def _resource_selection_for_interaction(
    row: FormalizationGapPlannerInteractiveSessionRow,
    resource_registry: dict[str, Any],
) -> dict[str, Any]:
    component_ids = NEXT_INTERACTION_COMPONENT_IDS.get(
        row.next_interaction_kind,
        (),
    )
    if not resource_registry.get("available"):
        return {
            "component_ids": _str_tuple(component_ids),
            "local_first_resource_ids": (),
            "frontier_escalation_resource_ids": (),
            "resource_contract_ids": (),
            "required_quality_signals": (),
            "quality_gates": (),
            "response_validation_signals": (),
            "resource_selection_rationale": (
                "No component-resource registry manifest was supplied; this "
                "decision row records schema contracts but no concrete "
                "resource contract ids."
            ),
            "errors": (),
        }

    component_index = resource_registry.get("component_index", {})
    execution_plan_index = resource_registry.get("execution_plan_index", {})
    contract_index = resource_registry.get("resource_contract_index", {})
    local_first: list[str] = []
    frontier: list[str] = []
    contract_ids: list[str] = []
    required_quality_signals: list[str] = []
    quality_gates: list[str] = []
    response_validation_signals: list[str] = []
    errors: list[str] = []
    for component_id in component_ids:
        component_row = component_index.get(component_id, {})
        execution_plan_row = execution_plan_index.get(component_id, {})
        if not component_row:
            errors.append(f"missing component-resource row: {component_id}")
        if not execution_plan_row:
            errors.append(f"missing component execution-plan row: {component_id}")
        required_quality_signals.extend(
            _str_tuple(component_row.get("required_quality_signals", ()))
        )
        quality_gates.extend(_str_tuple(execution_plan_row.get("quality_gates", ())))
        local_first.extend(
            _str_tuple(
                execution_plan_row.get("local_first_resource_ids", ())
                or component_row.get("local_fallback_resource_ids", ())
            )
        )
        frontier.extend(
            _str_tuple(
                execution_plan_row.get("frontier_escalation_resource_ids", ())
                or component_row.get("frontier_resource_ids", ())
            )
        )
    local_first_tuple = _str_tuple(local_first)
    frontier_tuple = _str_tuple(frontier)
    for resource_id in (*local_first_tuple, *frontier_tuple):
        contract_row = contract_index.get(resource_id, {})
        contract_id = str(contract_row.get("resource_contract_id", ""))
        if contract_id:
            contract_ids.append(contract_id)
            response_validation_signals.extend(
                _str_tuple(contract_row.get("response_validation_signals", ()))
            )
        else:
            errors.append(f"missing resource contract row: {resource_id}")
    if component_ids and not local_first_tuple:
        errors.append("local_first_resource_ids missing for selected components")
    if component_ids and not frontier_tuple:
        errors.append(
            "frontier_escalation_resource_ids missing for selected components"
        )
    if component_ids and not contract_ids:
        errors.append("resource_contract_ids missing for selected components")
    if component_ids and not required_quality_signals:
        errors.append("required_quality_signals missing for selected components")
    if component_ids and not quality_gates:
        errors.append("quality_gates missing for selected components")
    if component_ids and not response_validation_signals:
        errors.append(
            "response_validation_signals missing for selected resource contracts"
        )
    return {
        "component_ids": _str_tuple(component_ids),
        "local_first_resource_ids": local_first_tuple,
        "frontier_escalation_resource_ids": frontier_tuple,
        "resource_contract_ids": _str_tuple(contract_ids),
        "required_quality_signals": _str_tuple(required_quality_signals),
        "quality_gates": _str_tuple(quality_gates),
        "response_validation_signals": _str_tuple(response_validation_signals),
        "resource_selection_rationale": (
            f"Next interaction `{row.next_interaction_kind}` is mapped to "
            f"component-resource registry components "
            f"{', '.join(component_ids) or 'none'}; local-first resources are "
            "used before frontier escalation."
        ),
        "errors": tuple(errors),
    }


def _decision_trigger_signals(
    row: FormalizationGapPlannerInteractiveSessionRow,
) -> tuple[str, ...]:
    signals: list[str] = [f"session_state:{row.session_state}"]
    if row.needs_more_literature:
        signals.append("needs_more_literature")
    if row.needs_more_formal_grounding:
        signals.append("needs_more_formal_grounding")
    if row.needs_more_lean_grounding:
        signals.append("needs_more_lean_grounding")
    if row.needs_more_proof_state_feedback:
        signals.append("needs_more_proof_state_feedback")
    if row.needs_route_replanning or row.replan_required:
        signals.append("needs_route_replanning")
    if row.awaiting_hook_kinds:
        signals.append("awaiting_refinement_hooks")
    if row.rejected_hook_kinds:
        signals.append("rejected_refinement_hooks")
    if row.resource_response_awaiting_request_ids:
        signals.append("awaiting_resource_response_requests")
    if row.resource_response_rejected_request_ids:
        signals.append("rejected_resource_response_requests")
    if row.stable_under_current_evidence_bound:
        signals.append("stable_under_current_evidence_bound")
    if row.residual_goals:
        signals.append("residual_goals_present")
    if row.route_revision_reasons:
        signals.append("route_revision_reasons_present")
    if row.prover_triage_class:
        signals.append("prover_triage_class:" + row.prover_triage_class)
    if row.applied_prover_attempt_classes:
        signals.append("prover_attempt_classes_present")
    if row.coverage_summary.get("source_discovery_needed", 0):
        signals.append("source_discovery_needed")
    if row.coverage_summary.get("new_theory_needed", 0) or row.coverage_summary.get(
        "first_principles", 0
    ):
        signals.append("new_theory_or_first_principles_needed")
    return _str_tuple(signals)


def _decision_evidence_inputs(
    row: FormalizationGapPlannerInteractiveSessionRow,
) -> tuple[str, ...]:
    inputs = ["goal_conditioned_minimal_formalization_plan"]
    if row.awaiting_hook_kinds or row.rejected_hook_kinds or row.responded_hook_kinds:
        inputs.append("refinement_queue_or_evidence_hooks")
    if (
        row.resource_response_awaiting_request_ids
        or row.resource_response_rejected_request_ids
    ):
        inputs.append("resource_response_ledger_request_status")
    if row.source_refs:
        inputs.append("source_refs")
    if row.formal_declaration_hits:
        inputs.append("formal_declaration_hits")
    if row.lean_declaration_hits:
        inputs.append("lean_declaration_hits")
    if row.residual_goals:
        inputs.append("proof_state_residual_goals")
    if row.stability_decision:
        inputs.append("route_stability_audit")
    if row.route_revision_reasons:
        inputs.append("route_revision_evidence")
    if row.replan_required or row.standalone_seed_route_id:
        inputs.append("route_replan_handoff")
    if row.triage_class or row.triage_required_gate:
        inputs.append("proof_state_triage")
    if row.prover_triage_class:
        inputs.append("prover_triage_class")
    if row.applied_prover_attempt_classes:
        inputs.append("prover_attempt_classes")
    if row.target_prover_families:
        inputs.append("target_prover_families")
    return _str_tuple(inputs)


def _required_tool_contracts(next_kind: str) -> tuple[str, ...]:
    return _str_tuple(
        {
            "build_refinement_queue": (
                "formalization_gap_planner_refinement_work_item.schema.json",
                "formalization_gap_planner_route_alignment_edge.schema.json",
            ),
            "refinement_adapter_execution": (
                "formalization_gap_planner_refinement_work_item.schema.json",
                "formalization_gap_planner_refinement_tool_response.schema.json",
            ),
            "await_refinement_response": (
                "formalization_gap_planner_refinement_work_item.schema.json",
                "formalization_gap_planner_refinement_tool_response.schema.json",
                "formalization_gap_planner_resource_request_queue_row.schema.json",
                "formalization_gap_planner_resource_response.schema.json",
                "formalization_gap_planner_resource_response_ledger_row.schema.json",
            ),
            "literature_discovery": (
                "formalization_gap_planner_refinement_work_item.schema.json",
                "formalization_gap_planner_refinement_tool_response.schema.json",
                "formalization_gap_planner_source_grounding_row.schema.json",
            ),
            "formal_library_grounding": (
                "formalization_gap_planner_refinement_work_item.schema.json",
                "formalization_gap_planner_refinement_tool_response.schema.json",
                "formalization_gap_planner_route_alignment_edge.schema.json",
            ),
            "lean_library_grounding": (
                "formalization_gap_planner_refinement_work_item.schema.json",
                "formalization_gap_planner_refinement_tool_response.schema.json",
                "formalization_gap_planner_route_alignment_edge.schema.json",
            ),
            "proof_state_feedback": (
                "formalization_gap_planner_refinement_work_item.schema.json",
                "formalization_gap_planner_refinement_tool_response.schema.json",
                "formalization_gap_planner_prover_adapter_packet.schema.json",
            ),
            "route_revision": (
                "formalization_gap_planner_route_revision_overlay_row.schema.json",
                "formalization_gap_planner_route_alignment_edge.schema.json",
            ),
            "route_replan": (
                "formalization_gap_planner_route_stability_audit_row.schema.json",
                "formalization_gap_planner_route_replan_handoff_row.schema.json",
                "formalization_gap_planner_proof_state_triage_row.schema.json",
                "formalization_gap_planner_standalone_input.schema.json",
            ),
            "target_prover_replay": (
                "formalization_gap_planner_prover_adapter_packet.schema.json",
                "target_prover_kernel_replay",
            ),
            "route_stability_audit": (
                "formalization_gap_planner_refinement_tool_response.schema.json",
                "formalization_gap_planner_route_stability_audit_row.schema.json",
                "formalization_gap_planner_route_alignment_edge.schema.json",
            ),
        }.get(next_kind, ())
    )


def _stop_conditions(next_kind: str) -> tuple[str, ...]:
    return _str_tuple(
        {
            "build_refinement_queue": (
                "refinement work-item rows exist and validate",
                "every selected route primitive has a bounded hook or explicit no-op reason",
            ),
            "refinement_adapter_execution": (
                "adapter responses validate against the tool-response schema",
                "missing live-tool responses are marked awaiting rather than inferred",
            ),
            "await_refinement_response": (
                "required hook response arrives or the row remains awaiting",
                "resource-response rows echo the requested resource id, expected artifact, and dispatch spec",
                "no route revision is accepted without evidence rows",
            ),
            "literature_discovery": (
                "source-backed statement/assumption evidence is attached or a source gap remains explicit",
                "search is bounded to the current route primitive and theorem family",
            ),
            "formal_library_grounding": (
                "candidate declarations are attached with statement-shape notes",
                "unmatched primitives remain bridge/source-port/new-theory deltas",
            ),
            "lean_library_grounding": (
                "candidate Lean declarations are attached with statement-shape notes",
                "unmatched primitives remain bridge/source-port/new-theory deltas",
            ),
            "proof_state_feedback": (
                "residual goals and side conditions are recorded",
                "kernel proof status is not promoted by diagnostics alone",
            ),
            "route_revision": (
                "route revision overlay rows validate",
                "accepted revisions preserve route-alignment evidence",
            ),
            "route_replan": (
                "standalone replan seed validates",
                "roundtrip plan preserves revised route-alignment edges",
            ),
            "target_prover_replay": (
                "target prover replay is attempted through its kernel or certified checker",
                "proof promotion is handled outside the session ledger",
            ),
            "route_stability_audit": (
                "stability decision records evidence-bound status",
                "unstable routes produce exactly one next bounded action class",
            ),
        }.get(next_kind, ("next action has an explicit validated result row",))
    )


def _fallback_actions(next_kind: str) -> tuple[str, ...]:
    return _str_tuple(
        {
            "build_refinement_queue": ("run portable-plan audit", "inspect missing hooks"),
            "refinement_adapter_execution": (
                "use deterministic local adapter",
                "mark live adapter response awaiting",
            ),
            "await_refinement_response": (
                "rerun missing adapter response",
                "repair rejected resource-response JSONL rows against the request contract",
                "defer route revision until response evidence exists",
            ),
            "literature_discovery": (
                "narrow query to missing primitive",
                "mark source_search_pending",
            ),
            "formal_library_grounding": (
                "rerun formal-source adapter with primitive aliases",
                "open wrapper or bridge lemma",
            ),
            "lean_library_grounding": (
                "rerun formal-source adapter with primitive aliases",
                "open wrapper or bridge lemma",
            ),
            "proof_state_feedback": (
                "rerun local proof-state adapter",
                "convert residual goals to route revision reasons",
            ),
            "route_revision": ("rerun route stability audit", "handoff to replan"),
            "route_replan": (
                "rerun standalone planner",
                "audit route-replan handoff roundtrip",
            ),
            "target_prover_replay": (
                "export prover-adapter packets",
                "send residual failures back to proof-state feedback",
            ),
            "route_stability_audit": (
                "run refinement evidence aggregation",
                "request missing response rows",
            ),
        }.get(next_kind, ("keep route status explicit",))
    )


def _decision_rationale(
    row: FormalizationGapPlannerInteractiveSessionRow,
    trigger_signals: tuple[str, ...],
) -> str:
    return (
        f"Route `{row.route_id}` is in `{row.session_state}`; next action "
        f"`{row.next_interaction_kind}` follows from "
        + ", ".join(trigger_signals)
        + "."
    )


def _session_row(
    plan_row: dict[str, Any],
    queue_index: dict[tuple[str, str], list[dict[str, Any]]],
    evidence_index: dict[tuple[str, str], list[dict[str, Any]]],
    stability_index: dict[tuple[str, str], list[dict[str, Any]]],
    handoff_index: dict[tuple[str, str], list[dict[str, Any]]],
    triage_index: dict[tuple[str, str], list[dict[str, Any]]],
) -> FormalizationGapPlannerInteractiveSessionRow:
    errors: list[str] = []
    goal_plan_id = str(plan_row.get("goal_plan_id", ""))
    route_id = str(plan_row.get("route_id", ""))
    display_name = str(plan_row.get("display_name", ""))
    for field_name, value in (
        ("goal_plan_id", goal_plan_id),
        ("route_id", route_id),
        ("display_name", display_name),
    ):
        if not value:
            errors.append(f"{field_name} missing")
    key = (goal_plan_id, route_id)
    queue_rows = queue_index.get(key, [])
    evidence_rows = evidence_index.get(key, [])
    stability_row = _best_row(stability_index.get(key, []), "route_stability_audit_id")
    handoff_row = _best_row(handoff_index.get(key, []), "route_replan_handoff_id")
    triage_rows = _sort_by_rank(triage_index.get(key, []))
    primary_triage = triage_rows[0] if triage_rows else {}

    source_refs = _str_tuple(
        [
            *(source for row in evidence_rows for source in row.get("source_refs", [])),
            *stability_row.get("source_refs", []),
        ]
    )
    if not source_refs:
        source_refs = _source_refs_from_plan(plan_row)
    target_prover_families = _target_prover_families_for_session(
        plan_row,
        evidence_rows,
        stability_row,
        primary_triage,
    )
    route_target_prover_family = _primary_target_prover_family(target_prover_families)
    errors.extend(
        _input_declaration_hit_scope_errors(
            [*evidence_rows, stability_row],
            route_target_prover_family,
        )
    )
    formal_hits = _merge_dicts(
        *(
            _formal_declaration_hits_for_target(row, route_target_prover_family)
            for row in evidence_rows
        ),
        _formal_declaration_hits_for_target(stability_row, route_target_prover_family),
    )
    lean_hits = _merge_dicts(
        *(
            _lean_declaration_hits_for_target(row, route_target_prover_family)
            for row in evidence_rows
        ),
        _lean_declaration_hits_for_target(stability_row, route_target_prover_family),
    )
    residual_goals = _str_tuple(
        [
            *(
                residual
                for row in evidence_rows
                for residual in row.get("residual_goals", [])
            ),
            *stability_row.get("residual_goals", []),
        ]
    )
    if primary_triage:
        residual_goals = _str_tuple(
            [*residual_goals, *primary_triage.get("residual_goals", [])]
        )
    route_revision_reasons = _str_tuple(
        [
            *(
                reason
                for row in evidence_rows
                for reason in row.get("route_revision_reasons", [])
            ),
            *stability_row.get("route_revision_reasons", []),
        ]
    )
    triage_class = str(primary_triage.get("triage_class", ""))
    prover_triage_class = str(
        primary_triage.get(
            "prover_triage_class",
            _prover_triage_class_for_legacy(triage_class),
        )
    )
    applied_prover_attempt_classes = _str_tuple(
        [
            *(
                row.get("prover_attempt_class", "")
                for row in evidence_rows
            ),
            *stability_row.get("prover_attempt_classes", []),
            *primary_triage.get("applied_prover_attempt_classes", []),
        ]
    )
    coverage_summary = _coverage_summary(plan_row)
    stability_decision = str(stability_row.get("stability_decision", ""))
    stable = bool(stability_row.get("stable_under_current_evidence_bound", False))
    needs_literature = bool(stability_row.get("needs_more_literature", False))
    needs_formal = bool(
        stability_row.get(
            "needs_more_formal_grounding",
            stability_row.get("needs_more_lean_grounding", False),
        )
    )
    needs_lean = bool(stability_row.get("needs_more_lean_grounding", False))
    needs_proof = bool(stability_row.get("needs_more_proof_state_feedback", False))
    needs_replan = bool(stability_row.get("needs_route_replanning", False))
    replan_required = bool(handoff_row.get("requires_replan", False)) or needs_replan
    awaiting = _str_tuple(stability_row.get("awaiting_hook_kinds", []))
    rejected = _str_tuple(stability_row.get("rejected_hook_kinds", []))
    responded = _str_tuple(stability_row.get("responded_hook_kinds", []))
    resource_response_awaiting_request_ids = _str_tuple(
        stability_row.get("resource_response_awaiting_request_ids", [])
    )
    resource_response_rejected_request_ids = _str_tuple(
        stability_row.get("resource_response_rejected_request_ids", [])
    )
    has_resource_response_status = bool(
        resource_response_awaiting_request_ids
        or resource_response_rejected_request_ids
    )

    session_state = _session_state(
        stability_decision=stability_decision,
        stable=stable,
        needs_literature=needs_literature,
        needs_formal=needs_formal,
        needs_lean=needs_lean,
        needs_proof=needs_proof,
        replan_required=replan_required,
        awaiting=awaiting,
        rejected=rejected,
        has_resource_response_status=has_resource_response_status,
        queue_rows=queue_rows,
        evidence_rows=evidence_rows,
    )
    next_kind = _next_interaction_kind(
        session_state=session_state,
        needs_literature=needs_literature,
        needs_formal=needs_formal,
        needs_lean=needs_lean,
        needs_proof=needs_proof,
        replan_required=replan_required,
        stable=stable,
        awaiting=awaiting,
        rejected=rejected,
        has_resource_response_status=has_resource_response_status,
    )
    selected_queue_rows = _queue_rows_for_next(queue_rows, next_kind)
    next_owner = _next_owner_agent(primary_triage, selected_queue_rows, next_kind)
    next_tools = _str_tuple(
        [
            *primary_triage.get("recommended_tools", []),
            *(
                ["resource_response_ledger"]
                if (
                    resource_response_awaiting_request_ids
                    or resource_response_rejected_request_ids
                )
                else []
            ),
            *[
                tool
                for row in selected_queue_rows
                for tool in row.get("recommended_tools", [])
            ],
            *[
                adapter
                for row in selected_queue_rows
                for adapter in row.get("frontier_resource_adapters", [])
            ],
        ]
    )
    next_queries = _str_tuple(
        query for row in selected_queue_rows for query in row.get("queries", [])
    )
    next_commands = _next_commands(
        primary_triage=primary_triage,
        queue_rows=selected_queue_rows,
        handoff_row=handoff_row,
        next_kind=next_kind,
        resource_response_awaiting_request_ids=resource_response_awaiting_request_ids,
        resource_response_rejected_request_ids=resource_response_rejected_request_ids,
    )
    user_checkpoint = _user_checkpoint(next_kind, session_state)

    return FormalizationGapPlannerInteractiveSessionRow(
        schema_version=FORMALIZATION_GAP_PLANNER_INTERACTIVE_SESSION_SCHEMA_VERSION,
        interactive_session_row_id="formalization_gap_planner_interactive_session:"
        + stable_hash(
            [
                goal_plan_id,
                route_id,
                session_state,
                next_kind,
                stability_decision,
                next_commands,
            ]
        )[:16],
        goal_plan_id=goal_plan_id,
        route_id=route_id,
        display_name=display_name,
        route_class=str(plan_row.get("route_class", "")),
        pareto_profile=str(plan_row.get("pareto_profile", "")),
        session_state=session_state,
        next_interaction_kind=next_kind,
        next_owner_agent=next_owner,
        next_tools=next_tools,
        next_queries=next_queries,
        next_commands=next_commands,
        user_checkpoint=user_checkpoint,
        evidence_summary={
            "queued_items": len(queue_rows),
            "evidence_rows": len(evidence_rows),
            "source_refs": len(source_refs),
            "formal_declaration_hits": len(formal_hits),
            "lean_declaration_hits": len(lean_hits),
            "residual_goals": len(residual_goals),
            "triage_items": len(triage_rows),
            "prover_attempt_classes": len(applied_prover_attempt_classes),
            "target_prover_families": len(target_prover_families),
            "resource_response_awaiting_requests": len(
                resource_response_awaiting_request_ids
            ),
            "resource_response_rejected_requests": len(
                resource_response_rejected_request_ids
            ),
        },
        coverage_summary=coverage_summary,
        stability_decision=stability_decision,
        stable_under_current_evidence_bound=stable,
        needs_more_literature=needs_literature,
        needs_more_formal_grounding=needs_formal,
        needs_more_lean_grounding=needs_lean,
        needs_more_proof_state_feedback=needs_proof,
        needs_route_replanning=needs_replan,
        awaiting_hook_kinds=awaiting,
        rejected_hook_kinds=rejected,
        responded_hook_kinds=responded,
        resource_response_awaiting_request_ids=(
            resource_response_awaiting_request_ids
        ),
        resource_response_rejected_request_ids=(
            resource_response_rejected_request_ids
        ),
        residual_goals=residual_goals,
        source_refs=source_refs,
        formal_declaration_hits=formal_hits,
        lean_declaration_hits=lean_hits,
        route_revision_reasons=route_revision_reasons,
        triage_class=triage_class,
        prover_triage_class=prover_triage_class,
        applied_prover_attempt_classes=applied_prover_attempt_classes,
        target_prover_families=target_prover_families,
        triage_required_gate=str(primary_triage.get("required_gate", "")),
        replan_required=replan_required,
        standalone_seed_route_id=str(handoff_row.get("standalone_route_id", "")),
        route_cost=_float(plan_row.get("best_route_cost", 0.0)),
        proof_evidence_status=PROOF_EVIDENCE_STATUS,
        proof_evidence_boundary=PROOF_EVIDENCE_BOUNDARY,
        ok=not errors,
        errors=tuple(errors),
    )


def _session_state(
    *,
    stability_decision: str,
    stable: bool,
    needs_literature: bool,
    needs_formal: bool,
    needs_lean: bool,
    needs_proof: bool,
    replan_required: bool,
    awaiting: tuple[str, ...],
    rejected: tuple[str, ...],
    has_resource_response_status: bool,
    queue_rows: list[dict[str, Any]],
    evidence_rows: list[dict[str, Any]],
) -> str:
    if awaiting or rejected or has_resource_response_status:
        return "AWAITING_REFINEMENT_RESPONSES"
    if replan_required:
        return "ROUTE_REPLAN_REQUIRED"
    if needs_literature:
        return "EXPAND_LITERATURE_EVIDENCE"
    if needs_formal:
        return "EXPAND_FORMAL_LIBRARY_GROUNDING"
    if needs_lean:
        return "EXPAND_LEAN_LIBRARY_GROUNDING"
    if needs_proof:
        return "EXPAND_PROOF_STATE_FEEDBACK"
    if stable:
        return "ROUTE_STABLE_READY_FOR_REPLAY"
    if stability_decision:
        return "REVIEW_ROUTE_STABILITY_DECISION"
    if evidence_rows:
        return "RUN_ROUTE_STABILITY_AUDIT"
    if queue_rows:
        return "RUN_REFINEMENT_ADAPTERS"
    return "BUILD_REFINEMENT_QUEUE"


def _next_interaction_kind(
    *,
    session_state: str,
    needs_literature: bool,
    needs_formal: bool,
    needs_lean: bool,
    needs_proof: bool,
    replan_required: bool,
    stable: bool,
    awaiting: tuple[str, ...],
    rejected: tuple[str, ...],
    has_resource_response_status: bool,
) -> str:
    if awaiting or rejected or has_resource_response_status:
        return "await_refinement_response"
    if replan_required:
        return "route_replan"
    if needs_literature:
        return "literature_discovery"
    if needs_formal:
        return "formal_library_grounding"
    if needs_lean:
        return "lean_library_grounding"
    if needs_proof:
        return "proof_state_feedback"
    if stable:
        return "target_prover_replay"
    if session_state == "RUN_ROUTE_STABILITY_AUDIT":
        return "route_stability_audit"
    if session_state == "RUN_REFINEMENT_ADAPTERS":
        return "refinement_adapter_execution"
    return "build_refinement_queue"


def _queue_rows_for_next(
    queue_rows: list[dict[str, Any]],
    next_kind: str,
) -> list[dict[str, Any]]:
    if next_kind in {
        "literature_discovery",
        "formal_library_grounding",
        "lean_library_grounding",
        "proof_state_feedback",
        "route_revision",
    }:
        if next_kind == "formal_library_grounding":
            selected = [
                row
                for row in queue_rows
                if row.get("hook_kind")
                in {"formal_library_grounding", "lean_library_grounding"}
            ]
        else:
            selected = [row for row in queue_rows if row.get("hook_kind") == next_kind]
        return selected or queue_rows
    return queue_rows


def _next_owner_agent(
    primary_triage: dict[str, Any],
    queue_rows: list[dict[str, Any]],
    next_kind: str,
) -> str:
    if next_kind in {
        "build_refinement_queue",
        "route_replan",
        "route_stability_audit",
    }:
        return _default_owner(next_kind)
    if primary_triage and next_kind in {"proof_state_feedback", "target_prover_replay"}:
        return str(primary_triage.get("owner_agent", "")) or "formal_verifier"
    if queue_rows:
        return str(queue_rows[0].get("owner_agent", "")) or _default_owner(next_kind)
    return _default_owner(next_kind)


def _default_owner(next_kind: str) -> str:
    return {
        "build_refinement_queue": "formalization_planner",
        "literature_discovery": "literature",
        "formal_library_grounding": "formal_library_grounder",
        "lean_library_grounding": "formal_library_grounder",
        "proof_state_feedback": "formal_verifier",
        "route_replan": "formalization_planner",
        "target_prover_replay": "formal_verifier",
        "route_stability_audit": "formalization_planner",
        "refinement_adapter_execution": "adapter_orchestrator",
        "await_refinement_response": "adapter_orchestrator",
    }.get(next_kind, "formalization_planner")


def _next_commands(
    *,
    primary_triage: dict[str, Any],
    queue_rows: list[dict[str, Any]],
    handoff_row: dict[str, Any],
    next_kind: str,
    resource_response_awaiting_request_ids: tuple[str, ...] = (),
    resource_response_rejected_request_ids: tuple[str, ...] = (),
) -> tuple[str, ...]:
    commands: list[str] = []
    if next_kind == "route_replan":
        commands.extend(_str_tuple(handoff_row.get("next_commands", [])))
    if next_kind in {"proof_state_feedback", "target_prover_replay"} and primary_triage:
        commands.extend(_str_tuple(primary_triage.get("execution_commands", [])))
    if next_kind == "await_refinement_response":
        commands.extend(
            _resource_response_status_commands(
                resource_response_awaiting_request_ids,
                resource_response_rejected_request_ids,
            )
        )
    for row in queue_rows:
        commands.extend(_str_tuple(row.get("execution_commands", [])))
    return _str_tuple(commands)


def _resource_response_status_commands(
    awaiting_request_ids: tuple[str, ...],
    rejected_request_ids: tuple[str, ...],
) -> tuple[str, ...]:
    commands: list[str] = []
    for request_id in awaiting_request_ids:
        commands.append(
            "dispatch resource response for resource_request_id="
            + request_id
            + " and append a contract-valid row to formalization_gap_planner_resource_responses.jsonl"
        )
    for request_id in rejected_request_ids:
        commands.append(
            "repair resource response for resource_request_id="
            + request_id
            + " so resource_id, expected_response_artifact, dispatch_spec, and response contract fields match the request"
        )
    if commands:
        commands.append(
            "rerun formalization-gap-planner-resource-response-ledger and route-stability audit after resource response updates"
        )
    return _str_tuple(commands)


def _user_checkpoint(next_kind: str, session_state: str) -> str:
    return {
        "build_refinement_queue": "materialize the refinement queue before calling live tools",
        "literature_discovery": "review source-backed theorem variants and assumptions before accepting route changes",
        "formal_library_grounding": "review declaration hits for statement-shape compatibility before changing coverage labels",
        "lean_library_grounding": "review declaration hits for statement-shape compatibility before changing coverage labels",
        "proof_state_feedback": "review residual goals and side conditions before revising the route DAG",
        "route_replan": "rerun standalone planning from the replan seed before exporting target-prover packets",
        "target_prover_replay": "run target-prover replay; do not promote proof status from the session ledger",
        "route_stability_audit": "audit whether evidence has stabilized before replay or expansion",
        "refinement_adapter_execution": "run adapter responses and validate them through refinement evidence",
        "await_refinement_response": "wait for or rerun the missing adapter responses before route revision",
    }.get(next_kind, f"review session state {session_state}")


def _prover_triage_class_for_legacy(triage_class: str) -> str:
    return {
        "repair_local_lean_proof_state": "repair_target_prover_proof_state",
        "materialize_lean_command": "materialize_target_prover_command",
        "configure_local_lean_environment": "configure_target_prover_environment",
    }.get(triage_class, triage_class)


def _coverage_summary(plan_row: dict[str, Any]) -> dict[str, int]:
    coverage = Counter()
    for node in _all_node_dicts(plan_row):
        status = str(
            node.get("coverage_status", "")
            or node.get("action_class", "")
            or node.get("node_type", "")
        )
        if status:
            coverage[status] += 1
    return {
        "selected_primitives": len(_str_tuple(plan_row.get("selected_primitives", []))),
        "minimal_delta_nodes": len(
            [node for node in plan_row.get("minimal_additional_formalization_nodes", []) if isinstance(node, dict)]
        ),
        "exact_exists": coverage.get("exact_exists", 0),
        "wrapper_needed": coverage.get("wrapper_needed", 0),
        "bridge_needed": coverage.get("bridge_needed", 0),
        "source_port_needed": coverage.get("source_port_needed", 0),
        "source_discovery_needed": coverage.get("source_discovery_needed", 0),
        "new_theory_needed": coverage.get("new_theory_needed", 0),
        "first_principles": coverage.get("first_principles", 0),
    }


def _all_node_dicts(plan_row: dict[str, Any]) -> list[dict[str, Any]]:
    fields = (
        "existing_reuse_nodes",
        "wrapper_nodes",
        "bridge_nodes",
        "source_discovery_nodes",
        "first_principles_nodes",
        "minimal_additional_formalization_nodes",
        "lean_realization_dag_nodes",
    )
    nodes: list[dict[str, Any]] = []
    for field in fields:
        nodes.extend(
            node for node in plan_row.get(field, []) if isinstance(node, dict)
        )
    return nodes


def _optional_manifest(
    root: Path | None,
    filename: str,
    errors: list[str],
) -> dict[str, Any]:
    if root is None:
        return {}
    return _read_json(root / filename, errors)


def _read_json(path: Path, errors: list[str]) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        errors.append(f"missing file: {path}")
    except json.JSONDecodeError as exc:
        errors.append(f"invalid json: {path}: {exc}")
    return {}


def _row_index(rows: object) -> dict[tuple[str, str], list[dict[str, Any]]]:
    index: dict[tuple[str, str], list[dict[str, Any]]] = {}
    if not isinstance(rows, list):
        return index
    for row in rows:
        if not isinstance(row, dict):
            continue
        key = (str(row.get("goal_plan_id", "")), str(row.get("route_id", "")))
        if not all(key):
            continue
        index.setdefault(key, []).append(row)
    return index


def _best_row(rows: list[dict[str, Any]], id_field: str) -> dict[str, Any]:
    if not rows:
        return {}
    return sorted(rows, key=lambda row: str(row.get(id_field, "")))[0]


def _sort_by_rank(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(rows, key=lambda row: (_int(row.get("rank", 9999)), str(row.get("triage_item_id", ""))))


def _source_refs_from_plan(plan_row: dict[str, Any]) -> tuple[str, ...]:
    refs: list[str] = []
    refs.extend(_str_tuple(plan_row.get("source_refs", [])))
    for node in _all_node_dicts(plan_row):
        refs.extend(_str_tuple(node.get("source_refs", [])))
    for dag_node in plan_row.get("informal_knowledge_dag_nodes", []):
        if isinstance(dag_node, dict):
            refs.extend(_str_tuple(dag_node.get("source_refs", [])))
    return _str_tuple(refs)


def _target_prover_families_for_session(
    plan_row: dict[str, Any],
    evidence_rows: list[dict[str, Any]],
    stability_row: dict[str, Any],
    triage_row: dict[str, Any],
) -> tuple[str, ...]:
    values: list[object] = [
        plan_row.get("target_prover_family", ""),
        *stability_row.get("target_prover_families", []),
        *triage_row.get("target_prover_families", []),
    ]
    for container_name in ("standalone_input_trace", "replan_metadata", "route_summary"):
        container = plan_row.get(container_name, {})
        if isinstance(container, dict):
            values.append(container.get("target_prover_family", ""))
    for row in evidence_rows:
        values.append(row.get("target_prover_family", ""))
        values.extend(_target_prover_family_values_from_declaration_hits(row))
    values.extend(_target_prover_family_values_from_declaration_hits(stability_row))
    if not any(str(value or "").strip() for value in values):
        if any(
            _dict_tuple(row.get("lean_declaration_hits", []))
            for row in [*evidence_rows, stability_row]
        ):
            values.append("lean4")
    return _str_tuple(values)


def _target_prover_family_values_from_declaration_hits(
    row: dict[str, Any],
) -> tuple[object, ...]:
    values: list[object] = []
    for field_name in ("formal_declaration_hits", "lean_declaration_hits"):
        values.extend(
            hit.get("target_prover_family", "")
            for hit in _dict_tuple(row.get(field_name, []))
        )
    return tuple(values)


def _primary_target_prover_family(target_prover_families: tuple[str, ...]) -> str:
    for family in target_prover_families:
        text = str(family or "").strip()
        if text:
            return text
    return ""


def _formal_declaration_hits_for_target(
    row: dict[str, Any],
    target_prover_family: str,
) -> tuple[dict[str, object], ...]:
    if "formal_declaration_hits" in row:
        return _dict_tuple(row.get("formal_declaration_hits", []))
    if _is_lean_target_prover(target_prover_family):
        return _dict_tuple(row.get("lean_declaration_hits", []))
    return tuple()


def _lean_declaration_hits_for_target(
    row: dict[str, Any],
    target_prover_family: str,
) -> tuple[dict[str, object], ...]:
    if not _is_lean_target_prover(target_prover_family):
        return tuple()
    if "lean_declaration_hits" in row:
        return _dict_tuple(row.get("lean_declaration_hits", []))
    return _dict_tuple(row.get("formal_declaration_hits", []))


def _declaration_hit_scope_errors(row: dict[str, Any]) -> tuple[str, ...]:
    errors: list[str] = []
    target_families = _str_tuple(row.get("target_prover_families", []))
    target_family = _primary_target_prover_family(target_families)
    target_key = _target_prover_key(target_family)
    if (
        target_key
        and not _is_lean_target_prover(target_family)
        and _dict_tuple(row.get("lean_declaration_hits", []))
    ):
        errors.append(
            "lean_declaration_hits is a Lean-only legacy alias; non-Lean "
            "interactive session rows must use formal_declaration_hits only"
        )
    errors.extend(
        _declaration_hit_target_mismatch_errors(
            row,
            target_key=target_key,
            target_label="row target_prover_families",
        )
    )
    return tuple(errors)


def _input_declaration_hit_scope_errors(
    rows: list[dict[str, Any]],
    route_target_prover_family: str,
) -> tuple[str, ...]:
    errors: list[str] = []
    target_key = _target_prover_key(route_target_prover_family)
    for index, row in enumerate(rows):
        if not row:
            continue
        if (
            target_key
            and not _is_lean_target_prover(route_target_prover_family)
            and _dict_tuple(row.get("lean_declaration_hits", []))
        ):
            errors.append(
                f"input row {index} uses lean_declaration_hits for non-Lean "
                "interactive session target"
            )
        errors.extend(
            f"input row {index} {error}"
            for error in _declaration_hit_target_mismatch_errors(
                row,
                target_key=target_key,
                target_label="route target_prover_family",
            )
        )
    return tuple(errors)


def _declaration_hit_target_mismatch_errors(
    row: dict[str, Any],
    *,
    target_key: str,
    target_label: str,
) -> tuple[str, ...]:
    if not target_key:
        return tuple()
    errors: list[str] = []
    for field_name in ("formal_declaration_hits", "lean_declaration_hits"):
        for index, hit in enumerate(_dict_tuple(row.get(field_name, []))):
            hit_family = str(hit.get("target_prover_family", "") or "").strip()
            if hit_family and _target_prover_key(hit_family) != target_key:
                errors.append(
                    f"{field_name}[{index}].target_prover_family must match "
                    f"{target_label}"
                )
    return tuple(errors)


def _merge_dicts(
    *groups: tuple[dict[str, object], ...],
) -> tuple[dict[str, object], ...]:
    return _dict_tuple(item for group in groups for item in group)


def _is_lean_target_prover(target_prover_family: str) -> bool:
    key = _target_prover_key(target_prover_family)
    return key in {"lean", "lean4", "lean_4"} or key.startswith(
        ("lean4_", "lean_4_", "lean_")
    )


def _target_prover_key(target_prover_family: object) -> str:
    return re.sub(
        r"[^a-z0-9]+",
        "_",
        str(target_prover_family).strip().lower(),
    ).strip("_")


def _str_tuple(values: Iterable[object] | object) -> tuple[str, ...]:
    if values is None:
        return ()
    if isinstance(values, (str, bytes)):
        iterable: Iterable[object] = [values]
    elif isinstance(values, dict):
        iterable = values.values()
    else:
        try:
            iterable = iter(values)  # type: ignore[arg-type]
        except TypeError:
            iterable = [values]
    result: list[str] = []
    seen: set[str] = set()
    for value in iterable:
        item = str(value).strip()
        if item and item not in seen:
            result.append(item)
            seen.add(item)
    return tuple(result)


def _dict_tuple(values: Iterable[object]) -> tuple[dict[str, object], ...]:
    result: list[dict[str, object]] = []
    seen: set[str] = set()
    for value in values:
        if not isinstance(value, dict):
            continue
        key = stable_hash(value)
        if key in seen:
            continue
        result.append(dict(value))
        seen.add(key)
    return tuple(result)


def _float(value: object) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _int(value: object) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 9999


def _markdown_report(payload: dict[str, object]) -> str:
    lines = [
        "# Formalization Gap Planner Interactive Session",
        "",
        f"- Component: {payload.get('component_name')}",
        f"- Rows: {payload.get('n_session_rows')}",
        f"- OK rows: {payload.get('n_ok')}",
        f"- Row schema valid: {payload.get('n_row_schema_valid')}/{payload.get('n_session_rows')}",
        f"- Decision policy row schema valid: {payload.get('n_decision_policy_row_schema_valid')}/{payload.get('n_decision_policy_rows')}",
        f"- Decision policy quality signals: {payload.get('n_decision_policy_rows_with_required_quality_signals')}/{payload.get('n_decision_policy_rows')}",
        f"- Decision policy quality gates: {payload.get('n_decision_policy_rows_with_quality_gates')}/{payload.get('n_decision_policy_rows')}",
        f"- Decision policy response-validation signals: {payload.get('n_decision_policy_rows_with_response_validation_signals')}/{payload.get('n_decision_policy_rows')}",
        f"- All OK: {payload.get('all_ok')}",
        f"- Next literature searches: {payload.get('n_run_literature_search')}",
        f"- Next formal grounding actions: {payload.get('n_run_formal_grounding')}",
        f"- Next Lean grounding actions (legacy): {payload.get('n_run_lean_grounding')}",
        f"- Next proof-state actions: {payload.get('n_run_proof_state_feedback')}",
        f"- Routes requiring replan: {payload.get('n_rows_requiring_replan')}",
        f"- Rows ready for target-prover replay: {payload.get('n_run_target_prover_replay')}",
        "",
        "## Proof Boundary",
        "",
        str(payload.get("proof_evidence_boundary", "")),
        "",
        "## Session Rows",
        "",
    ]
    for row in payload.get("rows", []):
        if not isinstance(row, dict):
            continue
        lines.extend(
            [
                f"### {row.get('display_name')}",
                "",
                f"- Route: `{row.get('route_id')}`",
                f"- State: `{row.get('session_state')}`",
                f"- Next interaction: `{row.get('next_interaction_kind')}`",
                f"- Owner: `{row.get('next_owner_agent')}`",
                f"- User checkpoint: {row.get('user_checkpoint')}",
                "",
            ]
        )
    return "\n".join(lines)
