from __future__ import annotations

import json
import re
import shlex
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
from .formalization_gap_planner_standalone import (
    FORMALIZATION_GAP_PLANNER_STANDALONE_INPUT_COMPONENT,
    FORMALIZATION_GAP_PLANNER_STANDALONE_INPUT_SCHEMA_VERSION,
    standalone_input_json_schema,
)


FORMALIZATION_GAP_PLANNER_ROUTE_REPLAN_HANDOFF_SCHEMA_VERSION = 1
QUALITY_CONTROL_FIELDS = (
    "resource_contract_ids",
    "required_quality_signals",
    "quality_gates",
    "response_validation_signals",
    "stop_conditions",
)
PROOF_EVIDENCE_STATUS = "FORMALIZATION_GAP_PLANNER_ROUTE_REPLAN_HANDOFF_NOT_PROOF_EVIDENCE"
PROOF_EVIDENCE_BOUNDARY = (
    "Formalization gap planner route-replan handoff rows turn accepted "
    "route-revision overlays into a replayable standalone planner seed. They "
    "are next-round planning input, not theorem proof evidence."
)
ROUTE_REPLAN_HANDOFF_ROW_SCHEMA_ID = (
    "urn:ai-statistician:schemas:"
    "formalization-gap-planner-route-replan-handoff-row:1"
)
ROUTE_REVISION_STATUSES = (
    "ROUTE_REVISION_APPLIED",
    "NO_ROUTE_REVISION_PROPOSAL",
    "ORPHAN_ROUTE_REVISION_PROPOSAL",
)


@dataclass(frozen=True)
class FormalizationGapPlannerRouteReplanHandoffRow:
    schema_version: int
    route_replan_handoff_id: str
    route_revision_overlay_id: str
    goal_plan_id: str
    route_id: str
    display_name: str
    revision_status: str
    stability_decision: str
    requires_replan: bool
    original_selected_primitives: tuple[str, ...]
    revised_selected_primitives: tuple[str, ...]
    original_delta_primitives: tuple[str, ...]
    revised_delta_primitives: tuple[str, ...]
    added_primitives: tuple[str, ...]
    added_delta_primitives: tuple[str, ...]
    residual_goals: tuple[str, ...]
    applied_proposal_ids: tuple[str, ...]
    applied_refinement_evidence_ids: tuple[str, ...]
    applied_hook_kinds: tuple[str, ...]
    applied_resource_response_traces: tuple[dict[str, object], ...]
    applied_llm_route_planner_hook_traces: tuple[dict[str, object], ...]
    quality_controls: dict[str, tuple[str, ...]]
    resource_response_awaiting_request_ids: tuple[str, ...]
    resource_response_rejected_request_ids: tuple[str, ...]
    applied_prover_attempt_statuses: tuple[str, ...]
    applied_prover_diagnostic_signatures: tuple[str, ...]
    route_revision_reasons: tuple[str, ...]
    route_revision_summaries: tuple[str, ...]
    source_refs: tuple[str, ...]
    source_snippets: tuple[dict[str, object], ...]
    formal_declaration_hits: tuple[dict[str, object], ...]
    lean_declaration_hits: tuple[dict[str, object], ...]
    revised_informal_knowledge_dag_nodes: tuple[dict[str, object], ...]
    revised_formal_realization_dag_nodes: tuple[dict[str, object], ...]
    revised_lean_realization_dag_nodes: tuple[dict[str, object], ...]
    revised_route_alignment_edges: tuple[dict[str, object], ...]
    unaligned_primitives: tuple[str, ...]
    standalone_route_id: str
    standalone_route: dict[str, object]
    next_commands: tuple[str, ...]
    proof_evidence_status: str
    proof_evidence_boundary: str
    ok: bool
    errors: tuple[str, ...] = ()


def export_formalization_gap_planner_route_replan_handoff(
    goal_conditioned_minimal_formalization_plan_dir: Path,
    formalization_gap_planner_route_revision_overlay_dir: Path,
    out_dir: Path | None = None,
    *,
    formalization_gap_planner_route_stability_audit_dir: Path | None = None,
    target_prover_family: str = "",
    library_snapshot_ref: str = "",
) -> dict[str, object]:
    """Export a revised standalone seed from route-revision overlay rows."""

    errors: list[str] = []
    plan_path = (
        goal_conditioned_minimal_formalization_plan_dir
        / "goal_conditioned_minimal_formalization_plan_manifest.json"
    )
    overlay_path = (
        formalization_gap_planner_route_revision_overlay_dir
        / "formalization_gap_planner_route_revision_overlay_manifest.json"
    )
    stability_path = (
        formalization_gap_planner_route_stability_audit_dir
        / "formalization_gap_planner_route_stability_audit_manifest.json"
        if formalization_gap_planner_route_stability_audit_dir is not None
        else None
    )
    plan_payload = _read_json(plan_path, errors)
    overlay_payload = _read_json(overlay_path, errors)
    stability_payload = (
        _read_json(stability_path, errors) if stability_path is not None else {}
    )
    if plan_payload.get("component_name") != LIBRARY_AWARE_FORMALIZATION_GAP_PLANNER_NAME:
        errors.append("input manifest is not the library-aware formalization gap planner")
    if plan_payload.get("portable_schema_id") != PORTABLE_FORMALIZATION_GAP_PLAN_SCHEMA_ID:
        errors.append("input manifest portable schema id mismatch")

    plan_rows = [row for row in plan_payload.get("rows", []) if isinstance(row, dict)]
    overlay_rows = [
        row for row in overlay_payload.get("rows", []) if isinstance(row, dict)
    ]
    stability_rows = [
        row for row in stability_payload.get("rows", []) if isinstance(row, dict)
    ]
    plan_index = _row_index(plan_rows)
    stability_index = _row_index(stability_rows)
    rows = [
        _handoff_row(
            overlay_row,
            _first_match(overlay_row, plan_index),
            _first_match(overlay_row, stability_index),
            route_revision_overlay_dir=(
                formalization_gap_planner_route_revision_overlay_dir
            ),
        )
        for overlay_row in overlay_rows
    ]
    row_dicts = [asdict(row) for row in rows]
    handoff_row_schema = route_replan_handoff_row_json_schema()
    row_schema_errors = [
        validate_route_replan_handoff_row(row_dict, handoff_row_schema)
        for row_dict in row_dicts
    ]
    n_row_schema_valid = sum(1 for row_errors in row_schema_errors if not row_errors)
    n_row_schema_invalid = len(row_schema_errors) - n_row_schema_valid
    standalone_seed = _standalone_seed(
        rows,
        plan_payload,
        target_prover_family=target_prover_family,
        library_snapshot_ref=library_snapshot_ref,
    )
    by_revision_status = Counter(row.revision_status for row in rows)
    by_stability_decision = Counter(row.stability_decision for row in rows)
    by_applied_hook_kind = Counter(
        hook_kind for row in rows for hook_kind in row.applied_hook_kinds
    )
    payload: dict[str, object] = {
        "schema_version": FORMALIZATION_GAP_PLANNER_ROUTE_REPLAN_HANDOFF_SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "component_name": "formalization_gap_planner_route_replan_handoff",
        "goal_conditioned_minimal_formalization_plan_dir": str(
            goal_conditioned_minimal_formalization_plan_dir
        ),
        "goal_conditioned_minimal_formalization_plan_manifest": str(plan_path),
        "formalization_gap_planner_route_revision_overlay_dir": str(
            formalization_gap_planner_route_revision_overlay_dir
        ),
        "formalization_gap_planner_route_revision_overlay_manifest": str(overlay_path),
        "formalization_gap_planner_route_stability_audit_dir": str(
            formalization_gap_planner_route_stability_audit_dir or ""
        ),
        "formalization_gap_planner_route_stability_audit_manifest": str(
            stability_path or ""
        ),
        "n_plan_rows": len(plan_rows),
        "n_overlay_rows": len(overlay_rows),
        "n_stability_rows": len(stability_rows),
        "n_handoff_rows": len(rows),
        "n_routes_requiring_replan": sum(1 for row in rows if row.requires_replan),
        "n_routes_without_replan": sum(1 for row in rows if not row.requires_replan),
        "n_standalone_seed_routes": len(standalone_seed.get("routes", [])),
        "n_added_primitives": sum(len(row.added_primitives) for row in rows),
        "n_added_delta_primitives": sum(len(row.added_delta_primitives) for row in rows),
        "n_source_snippets": sum(len(row.source_snippets) for row in rows),
        "n_routes_with_source_snippets": sum(1 for row in rows if row.source_snippets),
        "n_routes_with_residual_goals": sum(1 for row in rows if row.residual_goals),
        "n_routes_with_prover_attempt_status": sum(
            1 for row in rows if row.applied_prover_attempt_statuses
        ),
        "n_routes_with_resource_response_ledger_feedback": sum(
            1 for row in rows if "resource_response_ledger" in row.applied_hook_kinds
        ),
        "n_applied_resource_response_traces": sum(
            len(row.applied_resource_response_traces) for row in rows
        ),
        "n_applied_llm_route_planner_hook_traces": sum(
            len(row.applied_llm_route_planner_hook_traces) for row in rows
        ),
        "n_routes_with_quality_controls": sum(
            1 for row in rows if row.quality_controls
        ),
        "n_routes_with_llm_route_planner_hook_trace": sum(
            1 for row in rows if row.applied_llm_route_planner_hook_traces
        ),
        "n_routes_with_resource_response_trace": sum(
            1 for row in rows if row.applied_resource_response_traces
        ),
        "n_resource_response_awaiting_request_ids": sum(
            len(row.resource_response_awaiting_request_ids) for row in rows
        ),
        "n_resource_response_rejected_request_ids": sum(
            len(row.resource_response_rejected_request_ids) for row in rows
        ),
        "n_distinct_prover_diagnostic_signatures": len(
            {
                signature
                for row in rows
                for signature in row.applied_prover_diagnostic_signatures
                if signature
            }
        ),
        "n_route_alignment_edges": sum(
            len(row.revised_route_alignment_edges) for row in rows
        ),
        "n_revised_informal_knowledge_dag_nodes": sum(
            len(row.revised_informal_knowledge_dag_nodes) for row in rows
        ),
        "n_revised_lean_realization_dag_nodes": sum(
            len(row.revised_lean_realization_dag_nodes) for row in rows
        ),
        "n_revised_formal_realization_dag_nodes": sum(
            len(row.revised_formal_realization_dag_nodes) for row in rows
        ),
        "n_unaligned_primitives": sum(len(row.unaligned_primitives) for row in rows),
        "n_row_schema_valid": n_row_schema_valid,
        "n_row_schema_invalid": n_row_schema_invalid,
        "route_replan_handoff_row_schema": handoff_row_schema,
        "n_ok": sum(1 for row in rows if row.ok),
        "all_ok": (
            not errors
            and bool(rows)
            and all(row.ok for row in rows)
            and n_row_schema_invalid == 0
        ),
        "errors": errors,
        "by_revision_status": dict(sorted(by_revision_status.items())),
        "by_stability_decision": dict(sorted(by_stability_decision.items())),
        "by_applied_hook_kind": dict(sorted(by_applied_hook_kind.items())),
        "rows": row_dicts,
        "standalone_seed": standalone_seed,
        "route_replan_handoff_fingerprint": stable_hash(row_dicts),
        "standalone_seed_fingerprint": stable_hash(standalone_seed),
        "proof_evidence_status": PROOF_EVIDENCE_STATUS,
        "proof_evidence_boundary": PROOF_EVIDENCE_BOUNDARY,
        "planner_proof_evidence_boundary": PLANNER_PROOF_EVIDENCE_BOUNDARY,
        "limitations": [
            "handoff routes are replayable planner input, not accepted revisions to theorem truth",
            "standalone seed coverage labels are derived from route evidence and must be replaced by live library/prover evidence when available",
            "rerunning the standalone planner and target-prover replay is required before any proof promotion",
        ],
    }
    if out_dir is not None:
        out_dir.mkdir(parents=True, exist_ok=True)
        (
            out_dir / "formalization_gap_planner_route_replan_handoff_manifest.json"
        ).write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
        (
            out_dir
            / "formalization_gap_planner_route_replan_handoff_row.schema.json"
        ).write_text(json.dumps(handoff_row_schema, indent=2), encoding="utf-8")
        (
            out_dir
            / "formalization_gap_planner_route_replan_standalone_seed.schema.json"
        ).write_text(
            json.dumps(standalone_input_json_schema(), indent=2),
            encoding="utf-8",
        )
        (out_dir / "formalization_gap_planner_route_replan_handoff.jsonl").write_text(
            "\n".join(json.dumps(asdict(row), sort_keys=True) for row in rows)
            + ("\n" if rows else ""),
            encoding="utf-8",
        )
        (
            out_dir / "formalization_gap_planner_route_replan_standalone_seed.json"
        ).write_text(json.dumps(standalone_seed, indent=2, default=str), encoding="utf-8")
        (out_dir / "formalization_gap_planner_route_replan_handoff.md").write_text(
            _markdown_report(payload),
            encoding="utf-8",
        )
    return payload


def route_replan_handoff_row_json_schema() -> dict[str, object]:
    """JSON Schema for route-replan handoff rows."""

    string_array = {"type": "array", "items": {"type": "string"}}
    object_array = {"type": "array", "items": {"type": "object"}}
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": ROUTE_REPLAN_HANDOFF_ROW_SCHEMA_ID,
        "title": "Formalization Gap Planner Route-Replan Handoff Row",
        "description": (
            "Contract for accepted route-revision handoffs that become "
            "replayable standalone planner seeds. Rows are not theorem proof "
            "evidence."
        ),
        "type": "object",
        "additionalProperties": True,
        "required": [
            "schema_version",
            "route_replan_handoff_id",
            "route_revision_overlay_id",
            "goal_plan_id",
            "route_id",
            "display_name",
            "revision_status",
            "requires_replan",
            "original_selected_primitives",
            "revised_selected_primitives",
            "original_delta_primitives",
            "revised_delta_primitives",
            "applied_proposal_ids",
            "applied_refinement_evidence_ids",
            "applied_hook_kinds",
            "applied_resource_response_traces",
            "resource_response_awaiting_request_ids",
            "resource_response_rejected_request_ids",
            "applied_prover_attempt_statuses",
            "applied_prover_diagnostic_signatures",
            "route_revision_reasons",
            "route_revision_summaries",
            "formal_declaration_hits",
            "revised_informal_knowledge_dag_nodes",
            "revised_formal_realization_dag_nodes",
            "revised_route_alignment_edges",
            "standalone_route_id",
            "standalone_route",
            "next_commands",
            "proof_evidence_status",
            "proof_evidence_boundary",
            "ok",
        ],
        "properties": {
            "schema_version": {
                "type": "integer",
                "const": FORMALIZATION_GAP_PLANNER_ROUTE_REPLAN_HANDOFF_SCHEMA_VERSION,
            },
            "route_replan_handoff_id": {"type": "string", "minLength": 1},
            "route_revision_overlay_id": {"type": "string", "minLength": 1},
            "goal_plan_id": {"type": "string", "minLength": 1},
            "route_id": {"type": "string", "minLength": 1},
            "display_name": {"type": "string", "minLength": 1},
            "revision_status": {"enum": list(ROUTE_REVISION_STATUSES)},
            "stability_decision": {"type": "string"},
            "requires_replan": {"type": "boolean"},
            "original_selected_primitives": string_array,
            "revised_selected_primitives": string_array,
            "original_delta_primitives": string_array,
            "revised_delta_primitives": string_array,
            "added_primitives": string_array,
            "added_delta_primitives": string_array,
            "residual_goals": string_array,
            "applied_proposal_ids": string_array,
            "applied_refinement_evidence_ids": string_array,
            "applied_hook_kinds": string_array,
            "applied_resource_response_traces": object_array,
            "applied_llm_route_planner_hook_traces": object_array,
            "quality_controls": {"type": "object"},
            "resource_response_awaiting_request_ids": string_array,
            "resource_response_rejected_request_ids": string_array,
            "applied_prover_attempt_statuses": string_array,
            "applied_prover_diagnostic_signatures": string_array,
            "route_revision_reasons": string_array,
            "route_revision_summaries": string_array,
            "source_refs": string_array,
            "source_snippets": object_array,
            "formal_declaration_hits": object_array,
            "lean_declaration_hits": object_array,
            "revised_informal_knowledge_dag_nodes": object_array,
            "revised_formal_realization_dag_nodes": object_array,
            "revised_lean_realization_dag_nodes": object_array,
            "revised_route_alignment_edges": object_array,
            "unaligned_primitives": string_array,
            "standalone_route_id": {"type": "string", "minLength": 1},
            "standalone_route": {"type": "object"},
            "next_commands": string_array,
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


def validate_route_replan_handoff_row(
    row: dict[str, Any],
    schema: dict[str, object] | None = None,
) -> tuple[str, ...]:
    """Validate a route-replan handoff row against the published schema."""

    handoff_row_schema = schema or route_replan_handoff_row_json_schema()
    errors: list[str] = []
    required = handoff_row_schema.get("required", [])
    if isinstance(required, list):
        for field_name in required:
            if isinstance(field_name, str) and field_name not in row:
                errors.append(f"{field_name} required")
    properties = handoff_row_schema.get("properties", {})
    if isinstance(properties, dict):
        for field_name, field_schema in properties.items():
            if not isinstance(field_name, str) or field_name not in row:
                continue
            if isinstance(field_schema, dict):
                errors.extend(
                    _schema_property_errors(field_name, row[field_name], field_schema)
                )
    if (
        "resource_response_ledger" in _str_tuple(row.get("applied_hook_kinds", []))
        and not _dict_tuple(row.get("applied_resource_response_traces", []))
    ):
        errors.append("resource_response_ledger hook missing applied_resource_response_traces")
    errors.extend(_declaration_hit_scope_errors(row))
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


def _handoff_row(
    overlay_row: dict[str, Any],
    plan_row: dict[str, Any] | None,
    stability_row: dict[str, Any] | None,
    *,
    route_revision_overlay_dir: Path,
) -> FormalizationGapPlannerRouteReplanHandoffRow:
    errors: list[str] = []
    plan_row = plan_row or {}
    stability_row = stability_row or {}
    overlay_id = str(overlay_row.get("route_revision_overlay_id", ""))
    goal_plan_id = str(overlay_row.get("goal_plan_id", plan_row.get("goal_plan_id", "")))
    route_id = str(overlay_row.get("route_id", plan_row.get("route_id", "")))
    display_name = str(overlay_row.get("display_name", plan_row.get("display_name", "")))
    revision_status = str(overlay_row.get("revision_status", ""))
    stability_decision = str(stability_row.get("stability_decision", ""))
    original_selected = _str_tuple(
        overlay_row.get("original_selected_primitives", plan_row.get("selected_primitives", []))
    )
    revised_selected = _str_tuple(
        overlay_row.get("revised_selected_primitives", original_selected)
    )
    original_delta = _str_tuple(
        overlay_row.get(
            "original_delta_primitives",
            _node_primitives(plan_row.get("minimal_additional_formalization_nodes", [])),
        )
    )
    revised_delta = _str_tuple(overlay_row.get("revised_delta_primitives", original_delta))
    added = _str_tuple(overlay_row.get("added_primitives", []))
    added_delta = _str_tuple(overlay_row.get("added_delta_primitives", []))
    residual_goals = _str_tuple(overlay_row.get("residual_goals", []))
    applied_proposal_ids = _str_tuple(overlay_row.get("applied_proposal_ids", []))
    applied_refinement_evidence_ids = _str_tuple(
        overlay_row.get("applied_refinement_evidence_ids", [])
    )
    applied_hook_kinds = _str_tuple(overlay_row.get("applied_hook_kinds", []))
    applied_resource_response_traces = _dict_tuple(
        overlay_row.get("applied_resource_response_traces", [])
    )
    applied_llm_route_planner_hook_traces = _dict_tuple(
        overlay_row.get("applied_llm_route_planner_hook_traces", [])
    )
    quality_controls = _quality_controls_for_handoff(overlay_row)
    resource_response_awaiting_request_ids = _str_tuple(
        _stability_or_overlay(
            "resource_response_awaiting_request_ids",
            stability_row,
            overlay_row,
        )
    )
    resource_response_rejected_request_ids = _str_tuple(
        _stability_or_overlay(
            "resource_response_rejected_request_ids",
            stability_row,
            overlay_row,
        )
    )
    attempt_statuses = _str_tuple(overlay_row.get("applied_prover_attempt_statuses", []))
    diagnostic_signatures = _str_tuple(
        overlay_row.get("applied_prover_diagnostic_signatures", [])
    )
    route_revision_reasons = _str_tuple(overlay_row.get("route_revision_reasons", []))
    route_revision_summaries = _str_tuple(
        overlay_row.get("route_revision_summaries", [])
    )
    target_prover_family = _target_prover_family_for_replan_route(
        plan_row,
        overlay_row,
    )
    source_refs = _merged_source_refs(plan_row, overlay_row)
    source_snippets = _dict_tuple(overlay_row.get("source_snippets", []))
    formal_declaration_hits = _formal_declaration_hits_for_target(
        overlay_row,
        target_prover_family,
    )
    lean_declaration_hits = _lean_declaration_hits_for_target(
        overlay_row,
        target_prover_family,
    )
    informal_nodes = _dict_tuple(
        overlay_row.get("revised_informal_knowledge_dag_nodes", [])
    )
    formal_nodes = _dict_tuple(
        overlay_row.get(
            "revised_formal_realization_dag_nodes",
            overlay_row.get("revised_lean_realization_dag_nodes", []),
        )
    )
    alignment_edges = _dict_tuple(overlay_row.get("revised_route_alignment_edges", []))
    unaligned_primitives = _str_tuple(overlay_row.get("unaligned_primitives", []))
    lean_nodes = _lean_alias_nodes_for_target(
        target_prover_family,
        _dict_tuple(overlay_row.get("revised_lean_realization_dag_nodes", [])),
        fallback_nodes=formal_nodes,
    )
    if not overlay_id:
        errors.append("route_revision_overlay_id missing")
    if not route_id:
        errors.append("route_id missing")
    if not display_name:
        errors.append("display_name missing")
    if not plan_row:
        errors.append("matching plan row missing")
    if not revised_selected and not revised_delta:
        errors.append("revised_selected_primitives or revised_delta_primitives missing")
    if unaligned_primitives:
        errors.append("overlay contains unaligned revised primitives")
    if "resource_response_ledger" in applied_hook_kinds and not applied_resource_response_traces:
        errors.append("resource_response_ledger hook missing applied_resource_response_traces")
    requires_replan = _requires_replan(
        revision_status=revision_status,
        stability_decision=stability_decision,
        added=added,
        added_delta=added_delta,
        removed=_str_tuple(overlay_row.get("removed_primitives", [])),
        residual_goals=residual_goals,
    )
    standalone_route_id = "replan_route:" + stable_hash(
        [route_id, overlay_id, revised_selected, revised_delta]
    )[:16]
    standalone_route = _standalone_route(
        standalone_route_id,
        plan_row,
        overlay_row,
        stability_row,
        revised_selected or revised_delta,
        source_refs,
        source_snippets,
        revised_informal_knowledge_dag_nodes=informal_nodes,
        revised_formal_realization_dag_nodes=formal_nodes,
        revised_lean_realization_dag_nodes=lean_nodes,
        revised_route_alignment_edges=alignment_edges,
        requires_replan=requires_replan,
        target_prover_family=target_prover_family,
        quality_controls=quality_controls,
    )
    if not standalone_route.get("primitives"):
        errors.append("standalone route primitives missing")
    return FormalizationGapPlannerRouteReplanHandoffRow(
        schema_version=FORMALIZATION_GAP_PLANNER_ROUTE_REPLAN_HANDOFF_SCHEMA_VERSION,
        route_replan_handoff_id="formalization_gap_planner_route_replan_handoff:"
        + stable_hash([overlay_id, route_id, stability_decision, standalone_route])[:16],
        route_revision_overlay_id=overlay_id,
        goal_plan_id=goal_plan_id,
        route_id=route_id,
        display_name=display_name,
        revision_status=revision_status,
        stability_decision=stability_decision,
        requires_replan=requires_replan,
        original_selected_primitives=original_selected,
        revised_selected_primitives=revised_selected,
        original_delta_primitives=original_delta,
        revised_delta_primitives=revised_delta,
        added_primitives=added,
        added_delta_primitives=added_delta,
        residual_goals=residual_goals,
        applied_proposal_ids=applied_proposal_ids,
        applied_refinement_evidence_ids=applied_refinement_evidence_ids,
        applied_hook_kinds=applied_hook_kinds,
        applied_resource_response_traces=applied_resource_response_traces,
        applied_llm_route_planner_hook_traces=applied_llm_route_planner_hook_traces,
        quality_controls=quality_controls,
        resource_response_awaiting_request_ids=resource_response_awaiting_request_ids,
        resource_response_rejected_request_ids=resource_response_rejected_request_ids,
        applied_prover_attempt_statuses=attempt_statuses,
        applied_prover_diagnostic_signatures=diagnostic_signatures,
        route_revision_reasons=route_revision_reasons,
        route_revision_summaries=route_revision_summaries,
        source_refs=source_refs,
        source_snippets=source_snippets,
        formal_declaration_hits=formal_declaration_hits,
        lean_declaration_hits=lean_declaration_hits,
        revised_informal_knowledge_dag_nodes=informal_nodes,
        revised_formal_realization_dag_nodes=formal_nodes,
        revised_lean_realization_dag_nodes=lean_nodes,
        revised_route_alignment_edges=alignment_edges,
        unaligned_primitives=unaligned_primitives,
        standalone_route_id=standalone_route_id,
        standalone_route=standalone_route,
        next_commands=_next_commands(route_revision_overlay_dir),
        proof_evidence_status=PROOF_EVIDENCE_STATUS,
        proof_evidence_boundary=PROOF_EVIDENCE_BOUNDARY,
        ok=not errors,
        errors=tuple(errors),
    )


def _next_commands(route_revision_overlay_dir: Path) -> tuple[str, ...]:
    seed_path = "formalization_gap_planner_route_replan_standalone_seed.json"
    registry_dir = "<formalization_gap_planner_component_resource_registry_dir>"
    overlay_arg = shlex.quote(str(route_revision_overlay_dir))
    common_llm_args = (
        f"--input {seed_path} --provider anthropic --model-tier auto "
        "--max-repair-attempts 1 "
        f"--formalization-gap-planner-route-revision-overlay-dir {overlay_arg} "
        "--formalization-gap-planner-component-resource-registry-dir "
        f"{registry_dir}"
    )
    return (
        f"formalization-gap-planner-standalone-plan --input {seed_path}",
        (
            "formalization-gap-planner-component-resource-registry "
            f"--out {registry_dir}"
        ),
        (
            "formalization-gap-planner-llm-route-planner "
            f"{common_llm_args} "
            "--out <formalization_gap_planner_route_replan_llm_route_planner_prompt_dir>"
        ),
        (
            "formalization-gap-planner-llm-route-planner "
            f"{common_llm_args} --invoke-provider "
            "--out <formalization_gap_planner_route_replan_llm_route_planner_live_dir>"
        ),
        (
            "formalization-gap-planner-portable-plan-audit "
            "--goal-conditioned-minimal-formalization-plan-dir <new_plan_dir>"
        ),
        (
            "formalization-gap-planner-minimal-delta-audit "
            "--goal-conditioned-minimal-formalization-plan-dir <new_plan_dir>"
        ),
        (
            "formalization-gap-planner-refinement-queue "
            "--goal-conditioned-minimal-formalization-plan-dir <new_plan_dir>"
        ),
    )


def _standalone_seed(
    rows: list[FormalizationGapPlannerRouteReplanHandoffRow],
    plan_payload: dict[str, Any],
    *,
    target_prover_family: str,
    library_snapshot_ref: str,
) -> dict[str, object]:
    route_targets = _str_tuple(
        row.standalone_route.get("target_prover_family", "")
        for row in rows
        if row.ok
    )
    seed_target = target_prover_family or (
        route_targets[0] if len(set(route_targets)) == 1 else ""
    )
    if not seed_target and not route_targets:
        seed_target = str(plan_payload.get("target_prover_family", ""))
    seed: dict[str, object] = {
        "schema_version": FORMALIZATION_GAP_PLANNER_STANDALONE_INPUT_SCHEMA_VERSION,
        "component_name": FORMALIZATION_GAP_PLANNER_STANDALONE_INPUT_COMPONENT,
        "library_snapshot_ref": library_snapshot_ref
        or str(plan_payload.get("library_snapshot_ref", "")),
        "background_primitives": _str_tuple(
            primitive
            for row in rows
            for primitive in row.original_selected_primitives
            if primitive not in set(row.revised_selected_primitives)
        ),
        "routes": [row.standalone_route for row in rows if row.ok],
        "handoff_source_component": "formalization_gap_planner_route_replan_handoff",
        "proof_evidence_status": PROOF_EVIDENCE_STATUS,
        "proof_evidence_boundary": PROOF_EVIDENCE_BOUNDARY,
    }
    if seed_target:
        seed["target_prover_family"] = seed_target
    return seed


def _standalone_route(
    standalone_route_id: str,
    plan_row: dict[str, Any],
    overlay_row: dict[str, Any],
    stability_row: dict[str, Any],
    primitives: tuple[str, ...],
    source_refs: tuple[str, ...],
    source_snippets: tuple[dict[str, object], ...],
    *,
    revised_informal_knowledge_dag_nodes: tuple[dict[str, object], ...],
    revised_formal_realization_dag_nodes: tuple[dict[str, object], ...],
    revised_lean_realization_dag_nodes: tuple[dict[str, object], ...],
    revised_route_alignment_edges: tuple[dict[str, object], ...],
    requires_replan: bool,
    target_prover_family: str,
    quality_controls: dict[str, tuple[str, ...]],
) -> dict[str, object]:
    node_index = _node_index(plan_row)
    lean_hit_index = _lean_hit_index(overlay_row)
    primitive_rows = [
        _primitive_row(
            primitive,
            node_index.get(primitive, {}),
            lean_hit_index.get(primitive, []),
            source_refs,
            source_snippets,
            overlay_row,
        )
        for primitive in primitives
    ]
    return {
        "route_id": standalone_route_id,
        "display_name": str(plan_row.get("display_name", overlay_row.get("display_name", ""))),
        "theorem_statement": str(plan_row.get("theorem_statement", "")),
        "theorem_skeleton": str(plan_row.get("theorem_skeleton", "")),
        "target_prover_family": target_prover_family,
        "route_class": str(plan_row.get("route_class", "")),
        "recommended_action": _recommended_action(requires_replan, stability_row),
        "source_refs": source_refs,
        "source_snippets": source_snippets,
        "quality_controls": quality_controls,
        "revised_informal_knowledge_dag_nodes": revised_informal_knowledge_dag_nodes,
        "revised_formal_realization_dag_nodes": revised_formal_realization_dag_nodes,
        "revised_lean_realization_dag_nodes": revised_lean_realization_dag_nodes,
        "revised_route_alignment_edges": revised_route_alignment_edges,
        "informal_proof_steps": _str_tuple(
            [
                *overlay_row.get("route_revision_summaries", []),
                *overlay_row.get("route_revision_reasons", []),
                *stability_row.get("stopping_rule_evidence", []),
            ]
        ),
        "import_cone_size": int(plan_row.get("import_cone_size", 0) or 0),
        "dependency_graph_depth": int(plan_row.get("dependency_graph_depth", 0) or 0),
        "blocker_count": len(_str_tuple(overlay_row.get("residual_goals", []))),
        "source_trust_level": "route_revision_overlay_handoff",
        "primitives": primitive_rows,
        "replan_metadata": {
            "source_route_id": str(overlay_row.get("route_id", "")),
            "source_goal_plan_id": str(overlay_row.get("goal_plan_id", "")),
            "target_prover_family": target_prover_family,
            "route_revision_overlay_id": str(overlay_row.get("route_revision_overlay_id", "")),
            "revision_status": str(overlay_row.get("revision_status", "")),
            "stability_decision": str(stability_row.get("stability_decision", "")),
            "requires_replan": requires_replan,
            "applied_proposal_ids": _str_tuple(
                overlay_row.get("applied_proposal_ids", [])
            ),
            "applied_refinement_evidence_ids": _str_tuple(
                overlay_row.get("applied_refinement_evidence_ids", [])
            ),
            "applied_hook_kinds": _str_tuple(
                overlay_row.get("applied_hook_kinds", [])
            ),
            "applied_resource_response_traces": _dict_tuple(
                overlay_row.get("applied_resource_response_traces", [])
            ),
            "applied_llm_route_planner_hook_traces": list(
                _dict_tuple(
                    overlay_row.get("applied_llm_route_planner_hook_traces", [])
                )
            ),
            "quality_controls": quality_controls,
            "resource_response_awaiting_request_ids": _str_tuple(
                _stability_or_overlay(
                    "resource_response_awaiting_request_ids",
                    stability_row,
                    overlay_row,
                )
            ),
            "resource_response_rejected_request_ids": _str_tuple(
                _stability_or_overlay(
                    "resource_response_rejected_request_ids",
                    stability_row,
                    overlay_row,
                )
            ),
            "applied_prover_attempt_statuses": _str_tuple(
                overlay_row.get("applied_prover_attempt_statuses", [])
            ),
            "applied_prover_diagnostic_signatures": _str_tuple(
                overlay_row.get("applied_prover_diagnostic_signatures", [])
            ),
            "route_revision_reasons": _str_tuple(
                overlay_row.get("route_revision_reasons", [])
            ),
            "route_revision_summaries": _str_tuple(
                overlay_row.get("route_revision_summaries", [])
            ),
            "residual_goals": _str_tuple(overlay_row.get("residual_goals", [])),
            "source_refs": source_refs,
            "source_snippets": source_snippets,
            "formal_declaration_hits": _formal_declaration_hits_for_target(
                overlay_row,
                target_prover_family,
            ),
            "lean_declaration_hits": _lean_declaration_hits_for_target(
                overlay_row,
                target_prover_family,
            ),
            "revised_informal_knowledge_dag_nodes": revised_informal_knowledge_dag_nodes,
            "revised_formal_realization_dag_nodes": revised_formal_realization_dag_nodes,
            "revised_lean_realization_dag_nodes": revised_lean_realization_dag_nodes,
            "revised_route_alignment_edges": revised_route_alignment_edges,
            "alignment_edge_primitives": _str_tuple(
                edge.get("primitive", "")
                for edge in revised_route_alignment_edges
            ),
            "proof_evidence_status": PROOF_EVIDENCE_STATUS,
        },
    }


def _primitive_row(
    primitive: str,
    node: dict[str, Any],
    lean_hits: list[dict[str, Any]],
    route_source_refs: tuple[str, ...],
    route_source_snippets: tuple[dict[str, object], ...],
    overlay_row: dict[str, Any],
) -> dict[str, object]:
    declarations = _str_tuple(
        [
            *node.get("candidate_declarations", []),
            *(hit.get("declaration", "") for hit in lean_hits),
        ]
    )
    coverage_status = _coverage_status(primitive, node, lean_hits)
    source_refs = _str_tuple(
        [
            *route_source_refs,
            *node.get("source_refs", []),
            *(
                hit.get("source_ref", "")
                for hit in lean_hits
                if isinstance(hit, dict)
            ),
        ]
    )
    residual_goals = _str_tuple(
        residual
        for residual in overlay_row.get("residual_goals", [])
        if primitive in str(residual)
    )
    row: dict[str, object] = {
        "primitive": primitive,
        "coverage_status": coverage_status,
        "candidate_declarations": declarations,
        "expected_premises": _str_tuple(node.get("expected_premises", [])),
        "bridge_candidate_obligations": _str_tuple(
            node.get("bridge_candidate_obligations", [])
        ),
        "source_refs": source_refs,
        "source_snippets": _source_snippets_for_primitive(
            primitive,
            route_source_snippets,
            source_refs,
        ),
        "cost": int(node.get("cost", _default_cost_for_status(coverage_status)) or 0),
        "next_step": str(node.get("next_step", "")) or _next_step(coverage_status, primitive),
        "side_conditions": residual_goals,
    }
    return row


def _source_snippets_for_primitive(
    primitive: str,
    source_snippets: tuple[dict[str, object], ...],
    source_refs: tuple[str, ...],
) -> tuple[dict[str, object], ...]:
    matched: list[dict[str, object]] = []
    source_ref_set = set(source_refs)
    for snippet in source_snippets:
        snippet_refs = set(_str_tuple(snippet.get("source_ref", ""))) | set(
            _str_tuple(snippet.get("source_refs", []))
        )
        snippet_primitives = set(_str_tuple(snippet.get("target_primitives", [])))
        text = " ".join(
            str(snippet.get(field_name, ""))
            for field_name in ("claim", "excerpt", "evidence_role")
        )
        if snippet_primitives:
            if primitive in snippet_primitives:
                matched.append(dict(snippet))
            continue
        if (
            primitive in text
            or bool(source_ref_set.intersection(snippet_refs))
        ):
            matched.append(dict(snippet))
    return _merge_dicts(tuple(matched))


def _coverage_status(
    primitive: str,
    node: dict[str, Any],
    lean_hits: list[dict[str, Any]],
) -> str:
    for hit in lean_hits:
        status = _normalize_coverage_status(str(hit.get("coverage_status", "")))
        if status:
            return status
    action_class = str(node.get("action_class", ""))
    return {
        "reuse_exact_proof_bank_obligation": "exact_exists",
        "compose_existing_bridge_chain": "composition_exists",
        "add_minimal_wrapper": "wrapper_needed",
        "formalize_assumption_interface": "assumption_interface_needed",
        "design_bridge_lemma": "bridge_needed",
        "port_external_source": "source_port_needed",
        "design_from_first_principles": "new_theory_needed",
    }.get(action_class, "needs_search" if primitive else "unknown")


def _normalize_coverage_status(status: str) -> str:
    normalized = status.strip().lower().replace("-", "_").replace(" ", "_")
    return {
        "source_discovery_needed": "source_port_needed",
        "benchmark_no_exact_declaration_label": "source_port_needed",
        "no_exact_declaration": "source_port_needed",
        "near_match": "composition_exists",
        "exact": "exact_exists",
    }.get(normalized, normalized)


def _requires_replan(
    *,
    revision_status: str,
    stability_decision: str,
    added: tuple[str, ...],
    added_delta: tuple[str, ...],
    removed: tuple[str, ...],
    residual_goals: tuple[str, ...],
) -> bool:
    if stability_decision == "APPLY_ROUTE_REVISION_AND_REPLAN":
        return True
    if revision_status == "ROUTE_REVISION_APPLIED":
        return True
    if added or added_delta or removed:
        return True
    return bool(residual_goals)


def _recommended_action(requires_replan: bool, stability_row: dict[str, Any]) -> str:
    if requires_replan:
        return "rerun standalone planning on the revised route overlay before prover replay"
    next_actions = _str_tuple(stability_row.get("next_actions", []))
    if next_actions:
        return next_actions[0]
    return "rerun route checks only if new literature, library, or prover evidence appears"


def _stability_or_overlay(
    field_name: str,
    stability_row: dict[str, Any],
    overlay_row: dict[str, Any],
) -> Any:
    if field_name in stability_row:
        return stability_row.get(field_name, [])
    return overlay_row.get(field_name, [])


def _quality_controls_for_handoff(
    overlay_row: dict[str, Any],
) -> dict[str, tuple[str, ...]]:
    controls: list[dict[str, tuple[str, ...]]] = [
        _quality_controls_from_payload(overlay_row),
        _quality_controls_from_payload(overlay_row.get("quality_controls", {})),
    ]
    for trace_field in (
        "applied_resource_response_traces",
        "applied_llm_route_planner_hook_traces",
    ):
        for trace in _dict_tuple(overlay_row.get(trace_field, [])):
            controls.append(_quality_controls_from_payload(trace))
            controls.append(
                _quality_controls_from_payload(trace.get("quality_controls", {}))
            )
    return _merge_quality_controls(*controls)


def _quality_controls_from_payload(value: Any) -> dict[str, tuple[str, ...]]:
    if not isinstance(value, dict):
        return {}
    return {
        field_name: _str_tuple(value.get(field_name, []))
        for field_name in QUALITY_CONTROL_FIELDS
        if _str_tuple(value.get(field_name, []))
    }


def _merge_quality_controls(
    *controls: dict[str, tuple[str, ...]],
) -> dict[str, tuple[str, ...]]:
    merged: dict[str, list[str]] = {}
    for control in controls:
        if not isinstance(control, dict):
            continue
        for field_name in QUALITY_CONTROL_FIELDS:
            values = _str_tuple(control.get(field_name, []))
            if values:
                merged.setdefault(field_name, []).extend(values)
    return {
        field_name: _str_tuple(values)
        for field_name, values in merged.items()
        if _str_tuple(values)
    }


def _node_index(plan_row: dict[str, Any]) -> dict[str, dict[str, Any]]:
    index: dict[str, dict[str, Any]] = {}
    for field_name in (
        "existing_reuse_nodes",
        "wrapper_nodes",
        "bridge_nodes",
        "source_discovery_nodes",
        "first_principles_nodes",
        "minimal_additional_formalization_nodes",
    ):
        for node in plan_row.get(field_name, []):
            if not isinstance(node, dict):
                continue
            primitive = str(node.get("primitive", ""))
            if primitive and primitive not in index:
                index[primitive] = node
    return index


def _lean_hit_index(overlay_row: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    index: dict[str, list[dict[str, Any]]] = {}
    hits = _formal_declaration_hits_for_target(
        overlay_row,
        _target_prover_family_for_replan_route({}, overlay_row),
    )
    for hit in hits:
        if not isinstance(hit, dict):
            continue
        primitive = str(hit.get("primitive", ""))
        if primitive:
            index.setdefault(primitive, []).append(hit)
    return index


def _merged_source_refs(
    plan_row: dict[str, Any],
    overlay_row: dict[str, Any],
) -> tuple[str, ...]:
    refs: list[str] = []
    refs.extend(_str_tuple(overlay_row.get("source_refs", [])))
    refs.extend(_source_refs_from_snippets(overlay_row.get("source_snippets", [])))
    for node in _node_index(plan_row).values():
        refs.extend(_source_refs_from_row(node))
    for node in _dict_tuple(
        overlay_row.get("revised_informal_knowledge_dag_nodes", [])
    ):
        refs.extend(_source_refs_from_row(node))
    return _str_tuple(refs)


def _source_refs_from_row(row: dict[str, object]) -> tuple[str, ...]:
    return _str_tuple(
        [
            *(_str_tuple(row.get("source_ref", ""))),
            *_str_tuple(row.get("source_refs", [])),
            *_source_refs_from_snippets(row.get("source_snippets", [])),
        ]
    )


def _source_refs_from_snippets(values: Any) -> tuple[str, ...]:
    refs: list[str] = []
    for snippet in _dict_tuple(values):
        refs.extend(_str_tuple(snippet.get("source_ref", "")))
        refs.extend(_str_tuple(snippet.get("source_refs", [])))
    return _str_tuple(refs)


def _target_prover_family_for_replan_route(
    plan_row: dict[str, Any],
    overlay_row: dict[str, Any],
) -> str:
    for value in (
        overlay_row.get("target_prover_family", ""),
        plan_row.get("target_prover_family", ""),
        _dict_value(plan_row.get("standalone_input_trace", {})).get(
            "target_prover_family",
            "",
        ),
        _dict_value(plan_row.get("replan_metadata", {})).get(
            "target_prover_family",
            "",
        ),
        _dict_value(plan_row.get("route_summary", {})).get(
            "target_prover_family",
            "",
        ),
    ):
        text = str(value or "").strip()
        if text:
            return text
    return "lean4"


def _lean_alias_nodes_for_target(
    target_prover_family: str,
    nodes: tuple[dict[str, object], ...],
    *,
    fallback_nodes: tuple[dict[str, object], ...] = (),
) -> tuple[dict[str, object], ...]:
    if not _is_lean_target_prover(target_prover_family):
        return tuple()
    return nodes or fallback_nodes


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
    target_families = _row_target_prover_families(row)
    target_keys = {_target_prover_key(family) for family in target_families}
    has_non_lean_only_target = bool(target_keys) and not any(
        _is_lean_target_prover(family) for family in target_families
    )
    if has_non_lean_only_target and _dict_tuple(row.get("lean_declaration_hits", [])):
        errors.append(
            "lean_declaration_hits is a Lean-only legacy alias; non-Lean "
            "route replan handoff rows must use formal_declaration_hits only"
        )
    for field_name in ("formal_declaration_hits", "lean_declaration_hits"):
        for index, hit in enumerate(_dict_tuple(row.get(field_name, []))):
            hit_family = str(hit.get("target_prover_family", "") or "").strip()
            if hit_family and target_keys and _target_prover_key(hit_family) not in target_keys:
                errors.append(
                    f"{field_name}[{index}].target_prover_family must match "
                    "row target_prover_family"
                )
    return tuple(errors)


def _row_target_prover_families(row: dict[str, Any]) -> tuple[str, ...]:
    families = _str_tuple(row.get("target_prover_family", ""))
    standalone_route = _dict_value(row.get("standalone_route", {}))
    families = _str_tuple(
        [
            *families,
            standalone_route.get("target_prover_family", ""),
            _dict_value(standalone_route.get("replan_metadata", {})).get(
                "target_prover_family",
                "",
            ),
        ]
    )
    return families


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


def _row_index(rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    index: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        for key in _row_keys(row):
            index.setdefault(key, []).append(row)
    return index


def _first_match(
    row: dict[str, Any],
    index: dict[str, list[dict[str, Any]]],
) -> dict[str, Any] | None:
    seen: set[int] = set()
    for key in _row_keys(row):
        for candidate in index.get(key, []):
            marker = id(candidate)
            if marker in seen:
                continue
            seen.add(marker)
            return candidate
    return None


def _row_keys(row: dict[str, Any]) -> tuple[str, ...]:
    return _str_tuple(
        [
            row.get("goal_plan_id", ""),
            row.get("route_id", ""),
            row.get("display_name", ""),
        ]
    )


def _node_primitives(nodes: Any) -> tuple[str, ...]:
    return _str_tuple(
        node.get("primitive", "") for node in nodes if isinstance(node, dict)
    )


def _default_cost_for_status(status: str) -> int:
    if status == "exact_exists":
        return 1
    if status == "composition_exists":
        return 2
    if status == "wrapper_needed":
        return 3
    if status in {"bridge_needed", "assumption_interface_needed"}:
        return 5
    if status == "source_port_needed":
        return 8
    if status == "new_theory_needed":
        return 13
    return 7


def _next_step(status: str, primitive: str) -> str:
    return {
        "exact_exists": f"reuse existing declaration or verified obligation for {primitive}",
        "composition_exists": f"compose existing declarations to realize {primitive}",
        "wrapper_needed": f"write a small wrapper statement for {primitive}",
        "bridge_needed": f"prove a focused bridge lemma for {primitive}",
        "assumption_interface_needed": f"formalize the assumption interface for {primitive}",
        "source_port_needed": f"attach source-backed statement and candidate port for {primitive}",
        "new_theory_needed": f"design the smallest new primitive needed for {primitive}",
    }.get(status, f"search library and sources for {primitive}")


def _read_json(path: Path | None, errors: list[str]) -> dict[str, Any]:
    if path is None:
        return {}
    if not path.exists():
        errors.append(f"missing json file: {path}")
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        errors.append(f"invalid json {path}: {exc}")
        return {}
    if not isinstance(payload, dict):
        errors.append(f"json payload is not object: {path}")
        return {}
    return payload


def _dict_tuple(values: Any) -> tuple[dict[str, object], ...]:
    if not isinstance(values, (list, tuple, set)):
        try:
            values = tuple(values)
        except TypeError:
            return tuple()
    rows: list[dict[str, object]] = []
    seen: set[str] = set()
    for value in values:
        if not isinstance(value, dict):
            continue
        key = stable_hash(value)
        if key in seen:
            continue
        seen.add(key)
        rows.append(dict(value))
    return tuple(rows)


def _dict_value(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


def _merge_dicts(
    *values: tuple[dict[str, object], ...],
) -> tuple[dict[str, object], ...]:
    rows: list[dict[str, object]] = []
    seen: set[str] = set()
    for group in values:
        for row in group:
            key = stable_hash(row)
            if key in seen:
                continue
            seen.add(key)
            rows.append(dict(row))
    return tuple(rows)


def _str_tuple(values: Any) -> tuple[str, ...]:
    if values is None:
        return ()
    if isinstance(values, str):
        values = [values]
    result: list[str] = []
    seen: set[str] = set()
    try:
        iterator = iter(values)
    except TypeError:
        iterator = iter([values])
    for value in iterator:
        item = str(value).strip()
        if not item or item in seen:
            continue
        seen.add(item)
        result.append(item)
    return tuple(result)


def _markdown_report(payload: dict[str, object]) -> str:
    lines = [
        "# Formalization Gap Planner Route-Replan Handoff",
        "",
        f"- Rows: {payload.get('n_ok')}/{payload.get('n_handoff_rows')}",
        f"- Routes requiring replan: {payload.get('n_routes_requiring_replan')}",
        f"- Standalone seed routes: {payload.get('n_standalone_seed_routes')}",
        f"- Residual-goal routes: {payload.get('n_routes_with_residual_goals')}",
        f"- Source snippets: {payload.get('n_source_snippets')}",
        f"- Resource-ledger feedback routes: {payload.get('n_routes_with_resource_response_ledger_feedback')}",
        f"- Applied resource-response traces: {payload.get('n_applied_resource_response_traces')}",
        f"- Applied LLM route-planner hook traces: {payload.get('n_applied_llm_route_planner_hook_traces')}",
        f"- Applied hook kinds: {payload.get('by_applied_hook_kind')}",
        f"- Row schema valid: {payload.get('n_row_schema_valid')}/{payload.get('n_handoff_rows')}",
        f"- All OK: {payload.get('all_ok')}",
        "",
        "## Boundary",
        "",
        str(payload.get("proof_evidence_boundary", PROOF_EVIDENCE_BOUNDARY)),
        "",
        "## Rows",
        "",
    ]
    for row in payload.get("rows", []):
        if not isinstance(row, dict):
            continue
        lines.append(
            f"- `{row.get('display_name')}` replan={row.get('requires_replan')} "
            f"revision={row.get('revision_status')} stability={row.get('stability_decision')} "
            f"seed_route={row.get('standalone_route_id')}"
        )
    lines.extend(
        [
            "",
            "## Replay",
            "",
            "Use `formalization_gap_planner_route_replan_standalone_seed.json` as "
            "the next `formalization-gap-planner-standalone-plan --input` value.",
        ]
    )
    return "\n".join(lines) + "\n"
