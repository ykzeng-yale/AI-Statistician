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
    LEGACY_FORMAL_REALIZATION_FIELD_ALIASES,
)


FORMALIZATION_GAP_PLANNER_ROUTE_REVISION_OVERLAY_SCHEMA_VERSION = 2
QUALITY_CONTROL_FIELDS = (
    "resource_contract_ids",
    "required_quality_signals",
    "quality_gates",
    "response_validation_signals",
    "stop_conditions",
)
PROOF_EVIDENCE_STATUS = "FORMALIZATION_GAP_PLANNER_ROUTE_REVISION_OVERLAY_NOT_PROOF_EVIDENCE"
PROOF_EVIDENCE_BOUNDARY = (
    "Formalization gap planner route-revision overlays apply refinement "
    "evidence back to route plans as planning state. They are not theorem proof "
    "evidence. Only target-prover kernel verification can prove a theorem or "
    "bridge lemma."
)
ROUTE_REVISION_OVERLAY_ROW_SCHEMA_ID = (
    "urn:ai-statistician:schemas:"
    "formalization-gap-planner-route-revision-overlay-row:1"
)
ROUTE_REVISION_STATUSES = (
    "ROUTE_REVISION_APPLIED",
    "NO_ROUTE_REVISION_PROPOSAL",
    "ORPHAN_ROUTE_REVISION_PROPOSAL",
)


@dataclass(frozen=True)
class FormalizationGapPlannerRouteRevisionOverlayRow:
    schema_version: int
    route_revision_overlay_id: str
    goal_plan_id: str
    route_id: str
    display_name: str
    revision_status: str
    original_selected_primitives: tuple[str, ...]
    revised_selected_primitives: tuple[str, ...]
    added_primitives: tuple[str, ...]
    removed_primitives: tuple[str, ...]
    original_delta_primitives: tuple[str, ...]
    revised_delta_primitives: tuple[str, ...]
    added_delta_primitives: tuple[str, ...]
    applied_proposal_ids: tuple[str, ...]
    applied_refinement_evidence_ids: tuple[str, ...]
    applied_hook_kinds: tuple[str, ...]
    applied_resource_response_traces: tuple[dict[str, object], ...]
    applied_llm_route_planner_hook_traces: tuple[dict[str, object], ...]
    quality_controls: dict[str, tuple[str, ...]]
    resource_response_summary: dict[str, int]
    resource_response_summary_by_acceptance_status: dict[str, int]
    resource_response_awaiting_request_ids: tuple[str, ...]
    resource_response_rejected_request_ids: tuple[str, ...]
    route_revision_reasons: tuple[str, ...]
    route_revision_summaries: tuple[str, ...]
    source_refs: tuple[str, ...]
    source_snippets: tuple[dict[str, object], ...]
    formal_declaration_hits: tuple[dict[str, object], ...]
    lean_declaration_hits: tuple[dict[str, object], ...]
    residual_goals: tuple[str, ...]
    applied_prover_attempt_statuses: tuple[str, ...]
    applied_prover_attempt_classes: tuple[str, ...]
    target_prover_families: tuple[str, ...]
    applied_prover_diagnostic_signatures: tuple[str, ...]
    revised_informal_knowledge_dag_nodes: tuple[dict[str, object], ...]
    revised_formal_realization_dag_nodes: tuple[dict[str, object], ...]
    revised_lean_realization_dag_nodes: tuple[dict[str, object], ...]
    revised_route_alignment_edges: tuple[dict[str, object], ...]
    unaligned_primitives: tuple[str, ...]
    next_required_gate: str
    proof_evidence_status: str
    proof_evidence_boundary: str
    ok: bool
    errors: tuple[str, ...] = ()


def export_formalization_gap_planner_route_revision_overlay(
    goal_conditioned_minimal_formalization_plan_dir: Path,
    formalization_gap_planner_refinement_evidence_dir: Path,
    out_dir: Path | None = None,
    *,
    formalization_gap_planner_resource_response_ledger_dir: Path | None = None,
) -> dict[str, object]:
    """Apply accepted refinement evidence as a route-plan overlay."""

    errors: list[str] = []
    plan_manifest_path = (
        goal_conditioned_minimal_formalization_plan_dir
        / "goal_conditioned_minimal_formalization_plan_manifest.json"
    )
    evidence_manifest_path = (
        formalization_gap_planner_refinement_evidence_dir
        / "formalization_gap_planner_refinement_evidence_manifest.json"
    )
    plan_payload = _read_json(plan_manifest_path, errors)
    evidence_payload = _read_json(evidence_manifest_path, errors)
    plan_rows = [
        _plan_row_with_manifest_context(row, plan_payload)
        for row in plan_payload.get("rows", [])
        if isinstance(row, dict)
    ]
    refinement_evidence_rows = [
        row for row in evidence_payload.get("rows", []) if isinstance(row, dict)
    ]
    all_refinement_evidence_proposals = [
        row
        for row in evidence_payload.get("route_revision_proposals", [])
        if isinstance(row, dict)
    ]
    usable_refinement_evidence_ids = _usable_refinement_evidence_ids(
        refinement_evidence_rows
    )
    has_refinement_evidence_rows = bool(refinement_evidence_rows)
    refinement_evidence_proposals = [
        proposal
        for proposal in all_refinement_evidence_proposals
        if _refinement_evidence_proposal_is_usable(
            proposal,
            usable_refinement_evidence_ids,
            has_refinement_evidence_rows=has_refinement_evidence_rows,
        )
    ]
    rejected_refinement_evidence_proposals = [
        proposal
        for proposal in all_refinement_evidence_proposals
        if proposal not in refinement_evidence_proposals
    ]
    resource_response_ledger_manifest_path: Path | None = None
    resource_response_ledger_payload: dict[str, Any] = {}
    resource_response_ledger_rows: list[dict[str, Any]] = []
    resource_response_ledger_proposals: list[dict[str, object]] = []
    if formalization_gap_planner_resource_response_ledger_dir is not None:
        resource_response_ledger_manifest_path = (
            formalization_gap_planner_resource_response_ledger_dir
            / "formalization_gap_planner_resource_response_ledger_manifest.json"
        )
        resource_response_ledger_payload = _read_json(
            resource_response_ledger_manifest_path,
            errors,
        )
        resource_response_ledger_rows = [
            row
            for row in resource_response_ledger_payload.get("rows", [])
            if isinstance(row, dict)
        ]
        resource_response_ledger_proposals = _resource_response_ledger_proposals(
            resource_response_ledger_rows
        )
    proposals = refinement_evidence_proposals + resource_response_ledger_proposals
    proposal_index = _proposal_index(proposals)
    resource_response_ledger_index = _resource_response_ledger_index(
        resource_response_ledger_rows
    )
    matched_proposal_ids: set[str] = set()
    rows: list[FormalizationGapPlannerRouteRevisionOverlayRow] = []
    for plan_row in plan_rows:
        matched = _match_proposals(plan_row, proposal_index)
        matched_proposal_ids.update(str(row.get("proposal_id", "")) for row in matched)
        rows.append(
            _overlay_row(
                plan_row,
                matched,
                _match_resource_response_ledger_rows(
                    plan_row,
                    resource_response_ledger_index,
                ),
            )
        )

    orphan_proposals = [
        proposal
        for proposal in proposals
        if str(proposal.get("proposal_id", "")) not in matched_proposal_ids
    ]
    for proposal in orphan_proposals:
        rows.append(_orphan_overlay_row(proposal))

    by_revision_status = Counter(row.revision_status for row in rows)
    by_prover_attempt_status = Counter(
        status for row in rows for status in row.applied_prover_attempt_statuses
    )
    by_prover_attempt_class = Counter(
        attempt_class
        for row in rows
        for attempt_class in row.applied_prover_attempt_classes
    )
    applied_llm_trace_by_source_kind = Counter(
        str(trace.get("llm_route_planner_source_kind", ""))
        for row in rows
        for trace in row.applied_llm_route_planner_hook_traces
        if str(trace.get("llm_route_planner_source_kind", ""))
    )
    applied_resource_response_trace_by_llm_source_kind = Counter(
        str(trace.get("llm_route_planner_source_kind", ""))
        for row in rows
        for trace in row.applied_resource_response_traces
        if str(trace.get("llm_route_planner_source_kind", ""))
    )
    row_dicts = [asdict(row) for row in rows]
    overlay_row_schema = route_revision_overlay_row_json_schema()
    row_schema_errors = [
        validate_route_revision_overlay_row(row_dict, overlay_row_schema)
        for row_dict in row_dicts
    ]
    n_row_schema_valid = sum(1 for row_errors in row_schema_errors if not row_errors)
    n_row_schema_invalid = len(row_schema_errors) - n_row_schema_valid
    payload: dict[str, object] = {
        "schema_version": FORMALIZATION_GAP_PLANNER_ROUTE_REVISION_OVERLAY_SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "component_name": "formalization_gap_planner_route_revision_overlay",
        "goal_conditioned_minimal_formalization_plan_dir": str(
            goal_conditioned_minimal_formalization_plan_dir
        ),
        "goal_conditioned_minimal_formalization_plan_manifest": str(plan_manifest_path),
        "formalization_gap_planner_refinement_evidence_dir": str(
            formalization_gap_planner_refinement_evidence_dir
        ),
        "formalization_gap_planner_refinement_evidence_manifest": str(
            evidence_manifest_path
        ),
        "formalization_gap_planner_resource_response_ledger_dir": (
            str(formalization_gap_planner_resource_response_ledger_dir)
            if formalization_gap_planner_resource_response_ledger_dir is not None
            else ""
        ),
        "formalization_gap_planner_resource_response_ledger_manifest": (
            str(resource_response_ledger_manifest_path)
            if resource_response_ledger_manifest_path is not None
            else ""
        ),
        "n_plan_rows": len(plan_rows),
        "n_refinement_evidence_rows": len(refinement_evidence_rows),
        "n_refinement_evidence_usable_rows": len(usable_refinement_evidence_ids),
        "n_refinement_evidence_route_revision_proposals_total": len(
            all_refinement_evidence_proposals
        ),
        "n_refinement_evidence_route_revision_proposals": len(
            refinement_evidence_proposals
        ),
        "n_refinement_evidence_route_revision_proposals_status_only": len(
            rejected_refinement_evidence_proposals
        ),
        "n_resource_response_ledger_rows": len(resource_response_ledger_rows),
        "n_resource_response_ledger_route_revision_proposals": len(
            resource_response_ledger_proposals
        ),
        "n_applied_resource_response_traces": sum(
            len(row.applied_resource_response_traces) for row in rows
        ),
        "n_applied_resource_response_formal_attempt_context_traces": sum(
            1
            for row in rows
            for trace in row.applied_resource_response_traces
            if _dict_value(trace, "formal_attempt_context")
        ),
        "n_applied_resource_response_traces_with_minimal_delta_priority": sum(
            1
            for row in rows
            for trace in row.applied_resource_response_traces
            if "minimal_delta_cost_score" in trace
        ),
        "average_applied_resource_response_reuse_readiness_score": _average_int(
            trace.get("reuse_readiness_score", 0)
            for row in rows
            for trace in row.applied_resource_response_traces
            if "reuse_readiness_score" in trace
        ),
        "average_applied_resource_response_evidence_readiness_score": _average_int(
            trace.get("evidence_readiness_score", 0)
            for row in rows
            for trace in row.applied_resource_response_traces
            if "evidence_readiness_score" in trace
        ),
        "n_applied_llm_route_planner_hook_traces": sum(
            len(row.applied_llm_route_planner_hook_traces) for row in rows
        ),
        "n_applied_llm_route_planner_route_planning_brief_evidence_gap_traces": (
            applied_llm_trace_by_source_kind.get(
                "route_planning_brief_evidence_gap",
                0,
            )
        ),
        "n_applied_resource_response_route_planning_brief_evidence_gap_traces": (
            applied_resource_response_trace_by_llm_source_kind.get(
                "route_planning_brief_evidence_gap",
                0,
            )
        ),
        "applied_llm_route_planner_hook_trace_by_source_kind": dict(
            sorted(applied_llm_trace_by_source_kind.items())
        ),
        "applied_resource_response_trace_by_llm_source_kind": dict(
            sorted(applied_resource_response_trace_by_llm_source_kind.items())
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
        "n_routes_with_resource_response_status": sum(
            1 for row in rows if row.resource_response_summary.get("queued", 0)
        ),
        "n_resource_response_ledger_status_rows": sum(
            row.resource_response_summary.get("queued", 0) for row in rows
        ),
        "n_resource_response_ledger_awaiting": sum(
            row.resource_response_summary.get("awaiting", 0) for row in rows
        ),
        "n_resource_response_ledger_rejected": sum(
            row.resource_response_summary.get("rejected", 0) for row in rows
        ),
        "n_routes_with_resource_response_awaiting": sum(
            1 for row in rows if row.resource_response_awaiting_request_ids
        ),
        "n_routes_with_resource_response_rejected": sum(
            1 for row in rows if row.resource_response_rejected_request_ids
        ),
        "n_route_revision_proposals": len(proposals),
        "n_orphan_route_revision_proposals": len(orphan_proposals),
        "n_overlay_rows": len(rows),
        "n_routes_with_revision": by_revision_status.get("ROUTE_REVISION_APPLIED", 0),
        "n_routes_without_revision": by_revision_status.get("NO_ROUTE_REVISION_PROPOSAL", 0),
        "n_orphan_rows": by_revision_status.get("ORPHAN_ROUTE_REVISION_PROPOSAL", 0),
        "n_added_primitives": sum(len(row.added_primitives) for row in rows),
        "n_added_delta_primitives": sum(len(row.added_delta_primitives) for row in rows),
        "n_source_snippets": sum(len(row.source_snippets) for row in rows),
        "n_routes_with_source_snippets": sum(1 for row in rows if row.source_snippets),
        "n_routes_with_prover_attempt_status": sum(
            1 for row in rows if row.applied_prover_attempt_statuses
        ),
        "n_routes_with_prover_attempt_class": sum(
            1 for row in rows if row.applied_prover_attempt_classes
        ),
        "target_prover_families": _str_tuple(
            family for row in rows for family in row.target_prover_families
        ),
        "n_distinct_prover_diagnostic_signatures": len(
            {
                signature
                for row in rows
                for signature in row.applied_prover_diagnostic_signatures
                if signature
            }
        ),
        "n_informal_dag_nodes": sum(
            len(row.revised_informal_knowledge_dag_nodes) for row in rows
        ),
        "legacy_formal_realization_field_aliases": dict(
            LEGACY_FORMAL_REALIZATION_FIELD_ALIASES
        ),
        "n_lean_realization_dag_nodes": sum(
            len(row.revised_lean_realization_dag_nodes) for row in rows
        ),
        "n_formal_realization_dag_nodes": sum(
            len(row.revised_formal_realization_dag_nodes) for row in rows
        ),
        "n_route_alignment_edges": sum(
            len(row.revised_route_alignment_edges) for row in rows
        ),
        "n_rows_with_alignment_contract": sum(
            1 for row in rows if not row.unaligned_primitives
        ),
        "n_unaligned_primitives": sum(len(row.unaligned_primitives) for row in rows),
        "n_row_schema_valid": n_row_schema_valid,
        "n_row_schema_invalid": n_row_schema_invalid,
        "route_revision_overlay_row_schema": overlay_row_schema,
        "n_ok": sum(1 for row in rows if row.ok),
        "all_ok": (
            not errors
            and bool(rows)
            and all(row.ok for row in rows)
            and n_row_schema_invalid == 0
            and all(
                "resource_response_ledger" not in row.applied_hook_kinds
                or bool(row.applied_resource_response_traces)
                for row in rows
            )
        ),
        "errors": errors,
        "by_revision_status": dict(sorted(by_revision_status.items())),
        "by_prover_attempt_status": dict(sorted(by_prover_attempt_status.items())),
        "by_prover_attempt_class": dict(sorted(by_prover_attempt_class.items())),
        "rows": row_dicts,
        "route_revision_overlay_fingerprint": stable_hash(row_dicts),
        "next_required_gate": (
            "rerun goal-conditioned minimal formalization planning, refinement "
            "queue generation, and verifier replay before any proof claim"
        ),
        "proof_evidence_status": PROOF_EVIDENCE_STATUS,
        "proof_evidence_boundary": PROOF_EVIDENCE_BOUNDARY,
        "limitations": [
            "route-revision overlays are planning state, not proof evidence",
            "proposal application is conservative and does not mutate the original planner manifest",
            "kernel proof status still requires target-prover replay and calibration after the revised route is selected",
        ],
    }
    if out_dir is not None:
        out_dir.mkdir(parents=True, exist_ok=True)
        (
            out_dir / "formalization_gap_planner_route_revision_overlay_manifest.json"
        ).write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
        (
            out_dir / "formalization_gap_planner_route_revision_overlay_row.schema.json"
        ).write_text(json.dumps(overlay_row_schema, indent=2), encoding="utf-8")
        (out_dir / "formalization_gap_planner_route_revision_overlay.jsonl").write_text(
            "\n".join(json.dumps(asdict(row), sort_keys=True) for row in rows)
            + ("\n" if rows else ""),
            encoding="utf-8",
        )
        (out_dir / "formalization_gap_planner_route_revision_overlay.md").write_text(
            _markdown_report(payload),
            encoding="utf-8",
        )
    return payload


def route_revision_overlay_row_json_schema() -> dict[str, object]:
    """JSON Schema for route-revision overlay rows."""

    string_array = {"type": "array", "items": {"type": "string"}}
    object_array = {"type": "array", "items": {"type": "object"}}
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": ROUTE_REVISION_OVERLAY_ROW_SCHEMA_ID,
        "title": "Formalization Gap Planner Route-Revision Overlay Row",
        "description": (
            "Contract for applying accepted refinement evidence back to the "
            "informal route DAG, formal realization DAG, selected primitives, "
            "and alignment edges. Rows are not theorem proof evidence."
        ),
        "type": "object",
        "additionalProperties": True,
        "required": [
            "schema_version",
            "route_revision_overlay_id",
            "goal_plan_id",
            "route_id",
            "display_name",
            "revision_status",
            "original_selected_primitives",
            "revised_selected_primitives",
            "original_delta_primitives",
            "revised_delta_primitives",
            "applied_resource_response_traces",
            "revised_informal_knowledge_dag_nodes",
            "revised_formal_realization_dag_nodes",
            "revised_route_alignment_edges",
            "unaligned_primitives",
            "next_required_gate",
            "proof_evidence_status",
            "proof_evidence_boundary",
            "ok",
        ],
        "properties": {
            "schema_version": {
                "type": "integer",
                "const": FORMALIZATION_GAP_PLANNER_ROUTE_REVISION_OVERLAY_SCHEMA_VERSION,
            },
            "route_revision_overlay_id": {"type": "string", "minLength": 1},
            "goal_plan_id": {"type": "string", "minLength": 1},
            "route_id": {"type": "string", "minLength": 1},
            "display_name": {"type": "string", "minLength": 1},
            "revision_status": {"enum": list(ROUTE_REVISION_STATUSES)},
            "original_selected_primitives": string_array,
            "revised_selected_primitives": string_array,
            "added_primitives": string_array,
            "removed_primitives": string_array,
            "original_delta_primitives": string_array,
            "revised_delta_primitives": string_array,
            "added_delta_primitives": string_array,
            "applied_proposal_ids": string_array,
            "applied_refinement_evidence_ids": string_array,
            "applied_hook_kinds": string_array,
            "applied_resource_response_traces": object_array,
            "applied_llm_route_planner_hook_traces": object_array,
            "quality_controls": {"type": "object"},
            "resource_response_summary": {"type": "object"},
            "resource_response_summary_by_acceptance_status": {"type": "object"},
            "resource_response_awaiting_request_ids": string_array,
            "resource_response_rejected_request_ids": string_array,
            "route_revision_reasons": string_array,
            "route_revision_summaries": string_array,
            "source_refs": string_array,
            "source_snippets": object_array,
            "formal_declaration_hits": object_array,
            "lean_declaration_hits": object_array,
            "residual_goals": string_array,
            "applied_prover_attempt_statuses": string_array,
            "applied_prover_attempt_classes": string_array,
            "target_prover_families": string_array,
            "applied_prover_diagnostic_signatures": string_array,
            "revised_informal_knowledge_dag_nodes": object_array,
            "revised_formal_realization_dag_nodes": object_array,
            "revised_lean_realization_dag_nodes": object_array,
            "revised_route_alignment_edges": object_array,
            "unaligned_primitives": string_array,
            "next_required_gate": {"type": "string", "minLength": 1},
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


def validate_route_revision_overlay_row(
    row: dict[str, Any],
    schema: dict[str, object] | None = None,
) -> tuple[str, ...]:
    """Validate a route-revision overlay row against the published schema."""

    overlay_row_schema = schema or route_revision_overlay_row_json_schema()
    errors: list[str] = []
    required = overlay_row_schema.get("required", [])
    if isinstance(required, list):
        for field_name in required:
            if isinstance(field_name, str) and field_name not in row:
                errors.append(f"{field_name} required")
    properties = overlay_row_schema.get("properties", {})
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


def _plan_row_with_manifest_context(
    row: dict[str, Any],
    manifest: dict[str, Any],
) -> dict[str, Any]:
    contextualized = dict(row)
    for field_name in ("target_prover_family", "library_snapshot_ref"):
        if not str(contextualized.get(field_name, "") or "").strip():
            value = str(manifest.get(field_name, "") or "").strip()
            if value:
                contextualized[field_name] = value
    return contextualized


def _overlay_row(
    plan_row: dict[str, Any],
    proposals: list[dict[str, Any]],
    resource_response_rows: list[dict[str, Any]],
) -> FormalizationGapPlannerRouteRevisionOverlayRow:
    original_selected = _str_tuple(plan_row.get("selected_primitives", []))
    original_delta = _str_tuple(
        node.get("primitive", "")
        for node in plan_row.get("minimal_additional_formalization_nodes", [])
        if isinstance(node, dict)
    )
    resource_response_summary = _resource_response_summary(resource_response_rows)
    resource_response_summary_by_status = (
        _resource_response_summary_by_acceptance_status(resource_response_rows)
    )
    quality_controls = _quality_controls_from_rows(
        [*proposals, *resource_response_rows]
    )
    resource_response_awaiting_request_ids = _resource_response_request_ids_by_status(
        resource_response_rows,
        awaiting=True,
    )
    resource_response_rejected_request_ids = _resource_response_request_ids_by_status(
        resource_response_rows,
        rejected=True,
    )
    if not proposals:
        target_prover_family = _target_prover_family_for_overlay(plan_row, ())
        informal_nodes = _existing_graph_nodes(plan_row.get("informal_knowledge_dag", {}))
        legacy_lean_nodes = _existing_graph_nodes(plan_row.get("lean_realization_dag", {}))
        formal_nodes = _existing_formal_realization_nodes(plan_row, legacy_lean_nodes)
        lean_nodes = _lean_alias_nodes_for_target(
            target_prover_family,
            legacy_lean_nodes,
            fallback_nodes=formal_nodes,
        )
        alignment_edges, unaligned = _route_alignment_edges(
            selected_primitives=original_selected,
            informal_nodes=informal_nodes,
            lean_nodes=formal_nodes,
        )
        return FormalizationGapPlannerRouteRevisionOverlayRow(
            schema_version=FORMALIZATION_GAP_PLANNER_ROUTE_REVISION_OVERLAY_SCHEMA_VERSION,
            route_revision_overlay_id=_overlay_id(plan_row, proposals),
            goal_plan_id=str(plan_row.get("goal_plan_id", "")),
            route_id=str(plan_row.get("route_id", "")),
            display_name=str(plan_row.get("display_name", "")),
            revision_status="NO_ROUTE_REVISION_PROPOSAL",
            original_selected_primitives=original_selected,
            revised_selected_primitives=original_selected,
            added_primitives=(),
            removed_primitives=(),
            original_delta_primitives=original_delta,
            revised_delta_primitives=original_delta,
            added_delta_primitives=(),
            applied_proposal_ids=(),
            applied_refinement_evidence_ids=(),
            applied_hook_kinds=(),
            applied_resource_response_traces=(),
            applied_llm_route_planner_hook_traces=(),
            quality_controls=quality_controls,
            resource_response_summary=resource_response_summary,
            resource_response_summary_by_acceptance_status=(
                resource_response_summary_by_status
            ),
            resource_response_awaiting_request_ids=(
                resource_response_awaiting_request_ids
            ),
            resource_response_rejected_request_ids=(
                resource_response_rejected_request_ids
            ),
            route_revision_reasons=(),
            route_revision_summaries=(),
            source_refs=(),
            source_snippets=(),
            formal_declaration_hits=(),
            lean_declaration_hits=(),
            residual_goals=(),
            applied_prover_attempt_statuses=(),
            applied_prover_attempt_classes=(),
            target_prover_families=(),
            applied_prover_diagnostic_signatures=(),
            revised_informal_knowledge_dag_nodes=informal_nodes,
            revised_formal_realization_dag_nodes=formal_nodes,
            revised_lean_realization_dag_nodes=lean_nodes,
            revised_route_alignment_edges=alignment_edges,
            unaligned_primitives=unaligned,
            next_required_gate="no route revision proposal recorded",
            proof_evidence_status=PROOF_EVIDENCE_STATUS,
            proof_evidence_boundary=PROOF_EVIDENCE_BOUNDARY,
            ok=not unaligned,
            errors=(
                ("unaligned revised primitives: " + ",".join(unaligned),)
                if unaligned
                else ()
            ),
        )

    selected_candidates = _nonempty_tuples(
        proposal.get("revised_selected_primitives", []) for proposal in proposals
    )
    delta_candidates = _nonempty_tuples(
        proposal.get("revised_delta_primitives", []) for proposal in proposals
    )
    revised_selected = _prefer_largest_tuple(selected_candidates) or original_selected
    revised_delta = _prefer_largest_tuple(delta_candidates) or original_delta
    informal_nodes = _merge_nodes(
        _existing_graph_nodes(plan_row.get("informal_knowledge_dag", {})),
        *(
            _dict_tuple(proposal.get("revised_informal_knowledge_dag_nodes", []))
            for proposal in proposals
        ),
    )
    target_prover_family = _target_prover_family_for_overlay(plan_row, proposals)
    existing_lean_nodes = _lean_alias_nodes_for_target(
        target_prover_family,
        _existing_graph_nodes(plan_row.get("lean_realization_dag", {})),
    )
    existing_formal_nodes = _existing_formal_realization_nodes(
        plan_row,
        _existing_graph_nodes(plan_row.get("lean_realization_dag", {})),
    )
    formal_nodes = _merge_nodes(
        existing_formal_nodes,
        *(
            _proposal_formal_realization_dag_nodes(proposal)
            for proposal in proposals
        ),
    )
    lean_nodes = _merge_nodes(
        existing_lean_nodes,
        *(
            _proposal_lean_realization_dag_nodes(
                proposal,
                target_prover_family=target_prover_family,
            )
            for proposal in proposals
        ),
    )
    alignment_edges, unaligned = _route_alignment_edges(
        selected_primitives=revised_selected,
        informal_nodes=informal_nodes,
        lean_nodes=formal_nodes,
    )
    return FormalizationGapPlannerRouteRevisionOverlayRow(
        schema_version=FORMALIZATION_GAP_PLANNER_ROUTE_REVISION_OVERLAY_SCHEMA_VERSION,
        route_revision_overlay_id=_overlay_id(plan_row, proposals),
        goal_plan_id=str(plan_row.get("goal_plan_id", "")),
        route_id=str(plan_row.get("route_id", "")),
        display_name=str(plan_row.get("display_name", "")),
        revision_status="ROUTE_REVISION_APPLIED",
        original_selected_primitives=original_selected,
        revised_selected_primitives=revised_selected,
        added_primitives=_tuple_diff(revised_selected, original_selected),
        removed_primitives=_tuple_diff(original_selected, revised_selected),
        original_delta_primitives=original_delta,
        revised_delta_primitives=revised_delta,
        added_delta_primitives=_tuple_diff(revised_delta, original_delta),
        applied_proposal_ids=_str_tuple(
            proposal.get("proposal_id", "") for proposal in proposals
        ),
        applied_refinement_evidence_ids=_str_tuple(
            proposal.get("refinement_evidence_id", "") for proposal in proposals
        ),
        applied_hook_kinds=_str_tuple(proposal.get("hook_kind", "") for proposal in proposals),
        applied_resource_response_traces=_merge_dicts(
            *(_proposal_resource_response_traces(proposal) for proposal in proposals)
        ),
        applied_llm_route_planner_hook_traces=_merge_dicts(
            *(_proposal_llm_route_planner_hook_traces(proposal) for proposal in proposals)
        ),
        quality_controls=quality_controls,
        resource_response_summary=resource_response_summary,
        resource_response_summary_by_acceptance_status=(
            resource_response_summary_by_status
        ),
        resource_response_awaiting_request_ids=resource_response_awaiting_request_ids,
        resource_response_rejected_request_ids=resource_response_rejected_request_ids,
        route_revision_reasons=_str_tuple(
            reason
            for proposal in proposals
            for reason in proposal.get("route_revision_reasons", [])
        ),
        route_revision_summaries=_str_tuple(
            proposal.get("route_revision_summary", "") for proposal in proposals
        ),
        source_refs=_str_tuple(
            source_ref
            for proposal in proposals
            for source_ref in proposal.get("source_refs", [])
        ),
        source_snippets=_merge_dicts(
            *(_dict_tuple(proposal.get("source_snippets", [])) for proposal in proposals)
        ),
        formal_declaration_hits=_merge_nodes(
            *(
                _formal_declaration_hits_for_target(
                    proposal,
                    _target_prover_family_for_overlay(
                        plan_row,
                        (proposal,),
                    ),
                )
                for proposal in proposals
            )
        ),
        lean_declaration_hits=_merge_nodes(
            *(
                _lean_declaration_hits_for_target(
                    proposal,
                    _target_prover_family_for_overlay(
                        plan_row,
                        (proposal,),
                    ),
                )
                for proposal in proposals
            )
        ),
        residual_goals=_str_tuple(
            residual
            for proposal in proposals
            for residual in proposal.get("residual_goals", [])
        ),
        applied_prover_attempt_statuses=_str_tuple(
            proposal.get("prover_attempt_status", "") for proposal in proposals
        ),
        applied_prover_attempt_classes=_str_tuple(
            proposal.get(
                "prover_attempt_class",
                _prover_attempt_class(str(proposal.get("prover_attempt_status", ""))),
            )
            for proposal in proposals
        ),
        target_prover_families=_str_tuple(
            _target_prover_family_for_overlay(plan_row, (proposal,))
            for proposal in proposals
        ),
        applied_prover_diagnostic_signatures=_str_tuple(
            proposal.get("prover_diagnostic_signature", "") for proposal in proposals
        ),
        revised_informal_knowledge_dag_nodes=informal_nodes,
        revised_formal_realization_dag_nodes=formal_nodes,
        revised_lean_realization_dag_nodes=lean_nodes,
        revised_route_alignment_edges=alignment_edges,
        unaligned_primitives=unaligned,
        next_required_gate=(
            "rerun goal-conditioned minimal formalization planning and verifier "
            "replay on the revised route overlay"
        ),
        proof_evidence_status=PROOF_EVIDENCE_STATUS,
        proof_evidence_boundary=PROOF_EVIDENCE_BOUNDARY,
        ok=not unaligned,
        errors=(
            ("unaligned revised primitives: " + ",".join(unaligned),)
            if unaligned
            else ()
        ),
    )


def _orphan_overlay_row(
    proposal: dict[str, Any],
) -> FormalizationGapPlannerRouteRevisionOverlayRow:
    errors = ("route revision proposal did not match any current plan row",)
    resource_response_traces = _proposal_resource_response_traces(proposal)
    resource_response_summary = _resource_response_summary(resource_response_traces)
    quality_controls = _quality_controls_from_rows(
        [proposal, *resource_response_traces]
    )
    target_prover_family = _target_prover_family_for_overlay({}, (proposal,))
    formal_nodes = _proposal_formal_realization_dag_nodes(proposal)
    lean_nodes = _proposal_lean_realization_dag_nodes(
        proposal,
        target_prover_family=target_prover_family,
    )
    return FormalizationGapPlannerRouteRevisionOverlayRow(
        schema_version=FORMALIZATION_GAP_PLANNER_ROUTE_REVISION_OVERLAY_SCHEMA_VERSION,
        route_revision_overlay_id="formalization_gap_planner_route_revision_overlay:"
        + stable_hash([proposal])[:16],
        goal_plan_id=str(proposal.get("goal_plan_id", "")),
        route_id=str(proposal.get("route_id", "")),
        display_name=str(proposal.get("display_name", "")),
        revision_status="ORPHAN_ROUTE_REVISION_PROPOSAL",
        original_selected_primitives=(),
        revised_selected_primitives=_str_tuple(proposal.get("revised_selected_primitives", [])),
        added_primitives=_str_tuple(proposal.get("revised_selected_primitives", [])),
        removed_primitives=(),
        original_delta_primitives=(),
        revised_delta_primitives=_str_tuple(proposal.get("revised_delta_primitives", [])),
        added_delta_primitives=_str_tuple(proposal.get("revised_delta_primitives", [])),
        applied_proposal_ids=_str_tuple([proposal.get("proposal_id", "")]),
        applied_refinement_evidence_ids=_str_tuple(
            [proposal.get("refinement_evidence_id", "")]
        ),
        applied_hook_kinds=_str_tuple([proposal.get("hook_kind", "")]),
        applied_resource_response_traces=_merge_dicts(
            resource_response_traces
        ),
        applied_llm_route_planner_hook_traces=_merge_dicts(
            _proposal_llm_route_planner_hook_traces(proposal)
        ),
        quality_controls=quality_controls,
        resource_response_summary=resource_response_summary,
        resource_response_summary_by_acceptance_status=(
            _resource_response_summary_by_acceptance_status(resource_response_traces)
        ),
        resource_response_awaiting_request_ids=_resource_response_request_ids_by_status(
            resource_response_traces,
            awaiting=True,
        ),
        resource_response_rejected_request_ids=_resource_response_request_ids_by_status(
            resource_response_traces,
            rejected=True,
        ),
        route_revision_reasons=_str_tuple(proposal.get("route_revision_reasons", [])),
        route_revision_summaries=_str_tuple([proposal.get("route_revision_summary", "")]),
        source_refs=_str_tuple(proposal.get("source_refs", [])),
        source_snippets=_dict_tuple(proposal.get("source_snippets", [])),
        formal_declaration_hits=_formal_declaration_hits_for_target(
            proposal,
            target_prover_family,
        ),
        lean_declaration_hits=_lean_declaration_hits_for_target(
            proposal,
            target_prover_family,
        ),
        residual_goals=_str_tuple(proposal.get("residual_goals", [])),
        applied_prover_attempt_statuses=_str_tuple(
            [proposal.get("prover_attempt_status", "")]
        ),
        applied_prover_attempt_classes=_str_tuple(
            [
                proposal.get(
                    "prover_attempt_class",
                    _prover_attempt_class(
                        str(proposal.get("prover_attempt_status", ""))
                    ),
                )
            ]
        ),
        target_prover_families=_str_tuple([target_prover_family]),
        applied_prover_diagnostic_signatures=_str_tuple(
            [proposal.get("prover_diagnostic_signature", "")]
        ),
        revised_informal_knowledge_dag_nodes=_dict_tuple(
            proposal.get("revised_informal_knowledge_dag_nodes", [])
        ),
        revised_formal_realization_dag_nodes=formal_nodes,
        revised_lean_realization_dag_nodes=lean_nodes,
        revised_route_alignment_edges=(),
        unaligned_primitives=_str_tuple(proposal.get("revised_selected_primitives", [])),
        next_required_gate="match proposal to an active route plan before replay",
        proof_evidence_status=PROOF_EVIDENCE_STATUS,
        proof_evidence_boundary=PROOF_EVIDENCE_BOUNDARY,
        ok=False,
        errors=errors,
    )


def _resource_response_ledger_proposals(
    rows: list[dict[str, Any]],
) -> list[dict[str, object]]:
    proposals: list[dict[str, object]] = []
    for row in rows:
        if not _ledger_row_is_usable_feedback(row):
            continue
        proposal = _resource_response_ledger_proposal(row)
        if proposal is not None:
            proposals.append(proposal)
    return proposals


def _resource_response_ledger_index(
    rows: list[dict[str, Any]],
) -> dict[str, list[dict[str, Any]]]:
    index: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        for key in _proposal_keys(row):
            index.setdefault(key, []).append(row)
    return index


def _match_resource_response_ledger_rows(
    plan_row: dict[str, Any],
    ledger_index: dict[str, list[dict[str, Any]]],
) -> list[dict[str, Any]]:
    seen: set[str] = set()
    matched: list[dict[str, Any]] = []
    for key in _plan_keys(plan_row):
        for row in ledger_index.get(key, []):
            row_id = str(row.get("resource_response_ledger_id", "")) or stable_hash(row)
            if row_id in seen:
                continue
            seen.add(row_id)
            matched.append(row)
    return sorted(
        matched,
        key=lambda row: (
            str(row.get("acceptance_status", "")),
            str(row.get("resource_request_id", "")),
            str(row.get("resource_response_ledger_id", "")),
        ),
    )


def _resource_response_summary(
    rows: tuple[dict[str, object], ...] | list[dict[str, Any]],
) -> dict[str, int]:
    summary = {
        "queued": 0,
        "responded": 0,
        "contract_ok": 0,
        "awaiting": 0,
        "rejected": 0,
        "accepted": 0,
        "route_revision_recommended": 0,
    }
    for row in rows:
        if not isinstance(row, dict):
            continue
        status = str(row.get("acceptance_status", ""))
        summary["queued"] += 1
        if bool(row.get("response_present", False)) or (
            bool(status) and status != "AWAITING_RESOURCE_RESPONSE"
        ):
            summary["responded"] += 1
        if bool(row.get("response_contract_ok", False)) or status.startswith("ACCEPTED_"):
            summary["contract_ok"] += 1
        if status == "AWAITING_RESOURCE_RESPONSE":
            summary["awaiting"] += 1
        if status.startswith("REJECTED_"):
            summary["rejected"] += 1
        if status.startswith("ACCEPTED_"):
            summary["accepted"] += 1
        if bool(row.get("route_revision_recommended", False)):
            summary["route_revision_recommended"] += 1
    return summary


def _resource_response_summary_by_acceptance_status(
    rows: tuple[dict[str, object], ...] | list[dict[str, Any]],
) -> dict[str, int]:
    statuses = Counter(
        str(row.get("acceptance_status", ""))
        for row in rows
        if isinstance(row, dict) and str(row.get("acceptance_status", ""))
    )
    return dict(sorted(statuses.items()))


def _resource_response_request_ids_by_status(
    rows: tuple[dict[str, object], ...] | list[dict[str, Any]],
    *,
    awaiting: bool = False,
    rejected: bool = False,
) -> tuple[str, ...]:
    ids: list[str] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        status = str(row.get("acceptance_status", ""))
        if awaiting and status != "AWAITING_RESOURCE_RESPONSE":
            continue
        if rejected and not status.startswith("REJECTED_"):
            continue
        if not awaiting and not rejected:
            continue
        row_id = str(row.get("resource_request_id", "")) or str(
            row.get("resource_response_ledger_id", "")
        )
        if row_id:
            ids.append(row_id)
    return _str_tuple(ids)


def _ledger_row_is_usable_feedback(row: dict[str, Any]) -> bool:
    acceptance_status = str(row.get("acceptance_status", ""))
    if acceptance_status.startswith("REJECTED_"):
        return False
    if not row.get("ok", False):
        return False
    if not row.get("response_present", False):
        return False
    if not row.get("response_contract_ok", False):
        return False
    if str(row.get("goal_plan_id", "")) and str(row.get("route_id", "")):
        return _ledger_row_has_actionable_feedback(row)
    return False


def _ledger_row_has_actionable_feedback(row: dict[str, Any]) -> bool:
    return any(
        (
            bool(row.get("route_revision_recommended", False)),
            bool(_str_tuple(row.get("source_refs", []))),
            bool(_dict_tuple(row.get("route_evidence_nodes", []))),
            bool(
                _formal_declaration_hits_for_target(
                    row,
                    str(row.get("target_prover_family", "")),
                )
            ),
            bool(_dict_value(row, "coverage_updates")),
            bool(_str_tuple(row.get("residual_goals", []))),
            bool(str(row.get("prover_attempt_status", ""))),
            bool(str(row.get("prover_diagnostic_signature", ""))),
            bool(_str_tuple(row.get("route_revision_reasons", []))),
        )
    )


def _resource_response_ledger_proposal(
    row: dict[str, Any],
) -> dict[str, object] | None:
    resource_response_ledger_id = str(row.get("resource_response_ledger_id", ""))
    resource_request_id = str(row.get("resource_request_id", ""))
    primitive = str(row.get("primitive", ""))
    if not resource_response_ledger_id or not resource_request_id or not primitive:
        return None
    response_payload = _dict_value(row, "response_payload")
    revised_selected_primitives = _str_tuple(
        response_payload.get("revised_selected_primitives", [])
    )
    revised_delta_primitives = _str_tuple(
        response_payload.get("revised_delta_primitives", [])
    )
    informal_nodes = _resource_response_informal_nodes(row)
    target_prover_family = str(row.get("target_prover_family", ""))
    formal_nodes = _resource_response_formal_nodes(row)
    lean_nodes = _lean_alias_nodes_for_target(
        target_prover_family,
        formal_nodes,
    )
    route_revision_reasons = _resource_response_route_revision_reasons(row)
    route_revision_summary = str(row.get("response_summary", "")) or (
        f"resource response feedback for {primitive}"
    )
    return {
        "proposal_id": "formalization_gap_planner_resource_response_route_revision:"
        + stable_hash(
            [
                resource_response_ledger_id,
                resource_request_id,
                str(row.get("resource_id", "")),
                route_revision_reasons,
            ]
        )[:16],
        "refinement_evidence_id": (
            "resource_response_ledger:" + resource_response_ledger_id
        ),
        "refinement_item_id": resource_request_id,
        "goal_plan_id": str(row.get("goal_plan_id", "")),
        "route_id": str(row.get("route_id", "")),
        "display_name": str(row.get("display_name", "")),
        "hook_kind": "resource_response_ledger",
        "quality_controls": _quality_controls_from_rows([row]),
        "target_primitives": _str_tuple(row.get("target_primitives", [])),
        "resource_response_trace": _resource_response_trace(row),
        "llm_route_planner_hook_trace": _resource_response_llm_route_planner_trace(
            row
        ),
        "route_revision_summary": route_revision_summary,
        "route_revision_reasons": route_revision_reasons,
        "revised_selected_primitives": revised_selected_primitives,
        "revised_delta_primitives": revised_delta_primitives,
        "revised_informal_knowledge_dag_nodes": informal_nodes,
        "revised_formal_realization_dag_nodes": formal_nodes,
        "revised_lean_realization_dag_nodes": lean_nodes,
        "source_refs": _str_tuple(row.get("source_refs", [])),
        "source_snippets": _resource_response_source_snippets(row),
        "formal_declaration_hits": _formal_declaration_hits_for_target(
            row,
            target_prover_family,
        ),
        "lean_declaration_hits": _lean_declaration_hits_for_target(
            row,
            target_prover_family,
        ),
        "residual_goals": _str_tuple(row.get("residual_goals", [])),
        "prover_attempt_status": str(row.get("prover_attempt_status", "")),
        "prover_attempt_class": str(
            row.get(
                "prover_attempt_class",
                _prover_attempt_class(str(row.get("prover_attempt_status", ""))),
            )
        ),
        "target_prover_family": target_prover_family,
        "prover_diagnostic_signature": str(
            row.get("prover_diagnostic_signature", "")
        ),
        "required_gate": (
            "rerun route planning and target-prover replay after applying "
            "resource-response feedback"
        ),
        "proof_evidence_status": PROOF_EVIDENCE_STATUS,
        "proof_evidence_boundary": PROOF_EVIDENCE_BOUNDARY,
    }


def _resource_response_source_snippets(
    row: dict[str, Any],
) -> tuple[dict[str, object], ...]:
    response_payload = _dict_value(row, "response_payload")
    snippets = _dict_tuple(row.get("source_snippets", []))
    if response_payload:
        snippets = _merge_dicts(
            snippets,
            _dict_tuple(response_payload.get("source_snippets", [])),
        )
    if snippets:
        return snippets
    derived: list[dict[str, object]] = []
    for index, node in enumerate(_dict_tuple(row.get("route_evidence_nodes", []))):
        source_ref = str(node.get("source_ref", "")).strip()
        if not source_ref:
            source_ref = (_str_tuple(node.get("source_refs", [])) or ("",))[0]
        claim = str(node.get("claim", "") or node.get("label", "")).strip()
        excerpt = str(node.get("excerpt", "")).strip()
        if not source_ref or not (claim or excerpt):
            continue
        derived.append(
            {
                "source_ref": source_ref,
                "claim": claim,
                "excerpt": excerpt,
                "evidence_role": str(
                    node.get("evidence_role", "source-backed informal route evidence")
                ),
                "target_primitives": _str_tuple(node.get("target_primitives", [])),
                "snippet_id": "resource_response_source_snippet:"
                + stable_hash(
                    [
                        row.get("resource_response_ledger_id", ""),
                        index,
                        source_ref,
                        claim,
                        excerpt,
                    ]
                )[:16],
            }
        )
    return tuple(derived)


def _resource_response_trace(row: dict[str, Any]) -> dict[str, object]:
    return {
        "resource_response_ledger_id": str(row.get("resource_response_ledger_id", "")),
        "resource_request_id": str(row.get("resource_request_id", "")),
        "action_resource_plan_id": str(row.get("action_resource_plan_id", "")),
        "primitive_action_id": str(row.get("primitive_action_id", "")),
        "coverage_map_id": str(row.get("coverage_map_id", "")),
        "goal_plan_id": str(row.get("goal_plan_id", "")),
        "route_id": str(row.get("route_id", "")),
        "primitive": str(row.get("primitive", "")),
        "target_primitives": _str_tuple(row.get("target_primitives", [])),
        "actionable_work_items": _str_tuple(row.get("actionable_work_items", [])),
        "priority_score": _int_value(row.get("priority_score", 0), default=0),
        "minimal_delta_cost_score": _int_value(
            row.get("minimal_delta_cost_score", 100),
            default=100,
        ),
        "reuse_readiness_score": _int_value(
            row.get("reuse_readiness_score", 0),
            default=0,
        ),
        "evidence_readiness_score": _int_value(
            row.get("evidence_readiness_score", 0),
            default=0,
        ),
        "priority_rationale": _str_tuple(row.get("priority_rationale", [])),
        "resource_id": str(row.get("resource_id", "")),
        "request_phase": str(row.get("request_phase", "")),
        "expected_response_artifact": str(row.get("expected_response_artifact", "")),
        "acceptance_gate": str(row.get("acceptance_gate", "")),
        "dispatch_spec": _dict_value(row, "dispatch_spec"),
        "quality_controls": _quality_controls_from_rows([row]),
        "candidate_declaration_rows": _dict_tuple(
            row.get("candidate_declaration_rows", [])
        ),
        "formal_declaration_hits": _formal_declaration_hits_for_target(
            row,
            str(row.get("target_prover_family", "")),
        ),
        "lean_declaration_hits": _lean_declaration_hits_for_target(
            row,
            str(row.get("target_prover_family", "")),
        ),
        "response_present": bool(row.get("response_present", False)),
        "response_contract_fields": _str_tuple(
            row.get("response_contract_fields", [])
        ),
        "response_contract_minimum_met": bool(
            row.get("response_contract_minimum_met", False)
        ),
        "response_contract_ok": bool(row.get("response_contract_ok", False)),
        "acceptance_status": str(row.get("acceptance_status", "")),
        "matched_response_contract_fields": _str_tuple(
            row.get("matched_response_contract_fields", [])
        ),
        "missing_response_contract_fields": _str_tuple(
            row.get("missing_response_contract_fields", [])
        ),
        "response_artifacts": _str_tuple(row.get("response_artifacts", [])),
        "route_revision_recommended": bool(
            row.get("route_revision_recommended", False)
        ),
        "prover_attempt_status": str(row.get("prover_attempt_status", "")),
        "prover_attempt_class": str(
            row.get(
                "prover_attempt_class",
                _prover_attempt_class(str(row.get("prover_attempt_status", ""))),
            )
        ),
        "target_prover_family": str(row.get("target_prover_family", "")),
        "prover_diagnostic_signature": str(
            row.get("prover_diagnostic_signature", "")
        ),
        "proof_evidence_status": str(row.get("proof_evidence_status", "")),
        "proof_evidence_boundary": str(row.get("proof_evidence_boundary", "")),
        "llm_route_planner_trace_present": bool(
            row.get("llm_route_planner_trace_present", False)
        ),
        "llm_route_planner_row_id": str(row.get("llm_route_planner_row_id", "")),
        "llm_route_planner_request_id": str(
            row.get("llm_route_planner_request_id", "")
        ),
        "llm_route_planner_source_kind": str(
            row.get("llm_route_planner_source_kind", "")
        ),
        "llm_route_planner_source_index": _int_value(
            row.get("llm_route_planner_source_index", -1),
            default=-1,
        ),
        "llm_route_planner_hook_kind": str(
            row.get("llm_route_planner_hook_kind", "")
        ),
        "residual_goal_context": _residual_goal_context_value(
            _dict_value(row, "residual_goal_context")
        ),
        "formal_attempt_context": _dict_value(row, "formal_attempt_context"),
        "llm_route_planner_response_trace_grounded": bool(
            row.get("llm_route_planner_response_trace_grounded", False)
        ),
        "llm_route_planner_response_trace_mismatches": _str_tuple(
            row.get("llm_route_planner_response_trace_mismatches", [])
        ),
    }


def _resource_response_llm_route_planner_trace(
    row: dict[str, Any],
) -> dict[str, object]:
    if not bool(row.get("llm_route_planner_trace_present", False)):
        return {}
    return {
        "trace_source": "resource_response_ledger",
        "resource_response_ledger_id": str(row.get("resource_response_ledger_id", "")),
        "resource_request_id": str(row.get("resource_request_id", "")),
        "route_id": str(row.get("route_id", "")),
        "goal_plan_id": str(row.get("goal_plan_id", "")),
        "target_primitives": _str_tuple(row.get("target_primitives", [])),
        "actionable_work_items": _str_tuple(row.get("actionable_work_items", [])),
        "priority_score": _int_value(row.get("priority_score", 0), default=0),
        "minimal_delta_cost_score": _int_value(
            row.get("minimal_delta_cost_score", 100),
            default=100,
        ),
        "reuse_readiness_score": _int_value(
            row.get("reuse_readiness_score", 0),
            default=0,
        ),
        "evidence_readiness_score": _int_value(
            row.get("evidence_readiness_score", 0),
            default=0,
        ),
        "priority_rationale": _str_tuple(row.get("priority_rationale", [])),
        "resource_id": str(row.get("resource_id", "")),
        "acceptance_status": str(row.get("acceptance_status", "")),
        "llm_route_planner_row_id": str(row.get("llm_route_planner_row_id", "")),
        "llm_route_planner_request_id": str(
            row.get("llm_route_planner_request_id", "")
        ),
        "llm_route_planner_source_kind": str(
            row.get("llm_route_planner_source_kind", "")
        ),
        "llm_route_planner_source_index": _int_value(
            row.get("llm_route_planner_source_index", -1),
            default=-1,
        ),
        "llm_route_planner_hook_kind": str(
            row.get("llm_route_planner_hook_kind", "")
        ),
        "llm_route_planner_queries": _str_tuple(
            row.get("llm_route_planner_queries", [])
        ),
        "llm_route_planner_source_item": _dict_value(
            row,
            "llm_route_planner_source_item",
        ),
        "residual_goal_context": _residual_goal_context_value(
            _dict_value(row, "residual_goal_context")
        ),
        "formal_attempt_context": _dict_value(row, "formal_attempt_context"),
        "llm_route_planner_response_trace_grounded": bool(
            row.get("llm_route_planner_response_trace_grounded", False)
        ),
        "llm_route_planner_response_trace_mismatches": _str_tuple(
            row.get("llm_route_planner_response_trace_mismatches", [])
        ),
        "proof_evidence_status": str(row.get("proof_evidence_status", "")),
        "proof_evidence_boundary": str(row.get("proof_evidence_boundary", "")),
    }


def _proposal_resource_response_traces(
    proposal: dict[str, Any],
) -> tuple[dict[str, object], ...]:
    traces = _dict_tuple(proposal.get("resource_response_traces", []))
    single = proposal.get("resource_response_trace")
    if isinstance(single, dict):
        traces = (*traces, single)
    return traces


def _proposal_llm_route_planner_hook_traces(
    proposal: dict[str, Any],
) -> tuple[dict[str, object], ...]:
    residual_goal_context = _residual_goal_context_value(
        _dict_value(proposal, "residual_goal_context")
    )
    traces = tuple(
        trace
        for trace in _dict_tuple(proposal.get("llm_route_planner_hook_traces", []))
        if trace
    )
    single = proposal.get("llm_route_planner_hook_trace")
    if isinstance(single, dict) and single:
        single = dict(single)
        if residual_goal_context and not single.get("residual_goal_context"):
            single["residual_goal_context"] = residual_goal_context
        traces = (*traces, single)
    elif residual_goal_context:
        traces = (
            *traces,
            {
                "trace_source": "refinement_evidence",
                "refinement_evidence_id": str(
                    proposal.get("refinement_evidence_id", "")
                ),
                "refinement_item_id": str(proposal.get("refinement_item_id", "")),
                "route_id": str(proposal.get("route_id", "")),
                "goal_plan_id": str(proposal.get("goal_plan_id", "")),
                "hook_kind": str(proposal.get("hook_kind", "")),
                "residual_goal_context": residual_goal_context,
                "proof_evidence_status": str(
                    proposal.get("proof_evidence_status", PROOF_EVIDENCE_STATUS)
                ),
                "proof_evidence_boundary": str(
                    proposal.get("proof_evidence_boundary", PROOF_EVIDENCE_BOUNDARY)
                ),
            },
        )
    return traces


def _quality_controls_from_rows(
    rows: list[dict[str, Any]] | tuple[dict[str, object], ...],
) -> dict[str, tuple[str, ...]]:
    controls: list[dict[str, tuple[str, ...]]] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        controls.append(_quality_controls_from_payload(row))
        controls.append(_quality_controls_from_payload(row.get("quality_controls", {})))
        for binding in _dict_tuple(row.get("resource_request_bindings", [])):
            controls.append(
                _quality_controls_from_payload(binding.get("quality_controls", {}))
            )
        for trace_field in (
            "resource_response_trace",
            "llm_route_planner_hook_trace",
        ):
            trace = row.get(trace_field)
            if isinstance(trace, dict):
                controls.append(_quality_controls_from_payload(trace))
                controls.append(
                    _quality_controls_from_payload(trace.get("quality_controls", {}))
                )
        for trace_field in (
            "resource_response_traces",
            "llm_route_planner_hook_traces",
            "applied_resource_response_traces",
            "applied_llm_route_planner_hook_traces",
        ):
            for trace in _dict_tuple(row.get(trace_field, [])):
                controls.append(_quality_controls_from_payload(trace))
                controls.append(
                    _quality_controls_from_payload(trace.get("quality_controls", {}))
                )
        controls.append(_quality_controls_from_payload(_dict_value(row, "request_playbook")))
        controls.append(_quality_controls_from_payload(_dict_value(row, "response_payload")))
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


def _proposal_formal_realization_dag_nodes(
    proposal: dict[str, Any],
) -> tuple[dict[str, object], ...]:
    return _dict_tuple(
        proposal.get(
            "revised_formal_realization_dag_nodes",
            proposal.get("revised_lean_realization_dag_nodes", []),
        )
    )


def _proposal_lean_realization_dag_nodes(
    proposal: dict[str, Any],
    *,
    target_prover_family: str,
) -> tuple[dict[str, object], ...]:
    if not _is_lean_target_prover(target_prover_family):
        return tuple()
    return _dict_tuple(
        proposal.get(
            "revised_lean_realization_dag_nodes",
            proposal.get("revised_formal_realization_dag_nodes", []),
        )
    )


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
            "route revision overlay rows must use formal_declaration_hits only"
        )
    for field_name in ("formal_declaration_hits", "lean_declaration_hits"):
        for index, hit in enumerate(_dict_tuple(row.get(field_name, []))):
            hit_family = str(hit.get("target_prover_family", "") or "").strip()
            if hit_family and target_keys and _target_prover_key(hit_family) not in target_keys:
                errors.append(
                    f"{field_name}[{index}].target_prover_family must match "
                    "row target_prover_families"
                )
            source_type_family = _declaration_hit_source_type_target_key(hit)
            if (
                not hit_family
                and source_type_family
                and target_keys
                and source_type_family not in target_keys
            ):
                errors.append(
                    f"{field_name}[{index}].source_type implies "
                    f"{source_type_family} but row target_prover_families are "
                    + ",".join(sorted(target_keys))
                )
    return tuple(errors)


def _row_target_prover_families(row: dict[str, Any]) -> tuple[str, ...]:
    values = _str_tuple(row.get("target_prover_families", []))
    if values:
        return values
    return _str_tuple(row.get("target_prover_family", ""))


def _target_prover_family_for_overlay(
    plan_row: dict[str, Any],
    proposals: tuple[dict[str, Any], ...],
) -> str:
    plan_metadata = _dict_value(plan_row, "standalone_input_trace")
    replan_metadata = _dict_value(plan_row, "replan_metadata")
    route_summary = _dict_value(plan_row, "route_summary")
    values = [
        plan_row.get("target_prover_family", ""),
        plan_metadata.get("target_prover_family", ""),
        replan_metadata.get("target_prover_family", ""),
        route_summary.get("target_prover_family", ""),
        *(
            value
            for proposal in proposals
            for value in _target_prover_family_values_from_proposal(proposal)
        ),
    ]
    for value in values:
        text = str(value or "").strip()
        if text:
            return text
    return "lean4"


def _target_prover_family_values_from_proposal(
    proposal: dict[str, Any],
) -> tuple[object, ...]:
    route_summary = _dict_value(proposal, "route_summary")
    replan_metadata = _dict_value(proposal, "replan_metadata")
    values: list[object] = [
        proposal.get("target_prover_family", ""),
        route_summary.get("target_prover_family", ""),
        replan_metadata.get("target_prover_family", ""),
    ]
    for field_name in (
        "revised_formal_realization_dag_nodes",
        "revised_lean_realization_dag_nodes",
        "formal_declaration_hits",
        "lean_declaration_hits",
    ):
        values.extend(
            node.get("target_prover_family", "")
            for node in _dict_tuple(proposal.get(field_name, []))
        )
    return tuple(values)


def _is_lean_target_prover(target_prover_family: str) -> bool:
    key = _target_prover_key(target_prover_family)
    return key in {"lean", "lean4", "lean_4"} or key.startswith(
        ("lean4_", "lean_4_", "lean_")
    )


def _target_prover_key(target_prover_family: object) -> str:
    key = re.sub(
        r"[^a-z0-9]+",
        "_",
        str(target_prover_family).strip().lower(),
    ).strip("_")
    aliases = {
        "coq": "rocq",
        "coq8": "rocq",
        "lean": "lean4",
        "lean_4": "lean4",
        "isabelle_hol": "isabelle",
    }
    return aliases.get(key, key)


def _declaration_hit_source_type_target_key(row: dict[str, object]) -> str:
    source_type = (
        row.get("source_type")
        or row.get("source_kind")
        or row.get("library_family")
        or row.get("source_prover_family")
        or row.get("prover_family")
        or ""
    )
    return _source_type_target_prover_key(source_type)


def _source_type_target_prover_key(value: object) -> str:
    key = _target_prover_key(value)
    if not key:
        return ""
    tokens = {token for token in re.split(r"[^a-z0-9]+", key) if token}
    if key in {"mathlib", "lean4_library"} or {"lean", "lean4", "mathlib"} & tokens:
        return "lean4"
    if key in {"coq", "coq8", "coq_library", "rocq_library"} or {
        "coq",
        "coq8",
        "rocq",
    } & tokens:
        return "rocq"
    if key in {"isabelle_hol", "isabelle_library"} or "isabelle" in tokens:
        return "isabelle"
    if key in {"agda_library"} or "agda" in tokens:
        return "agda"
    return ""


def _usable_refinement_evidence_ids(
    rows: list[dict[str, Any]],
) -> set[str]:
    ids: set[str] = set()
    for row in rows:
        if not _refinement_evidence_row_is_usable_feedback(row):
            continue
        for field_name in ("refinement_evidence_id", "refinement_item_id"):
            value = str(row.get(field_name, "")).strip()
            if value:
                ids.add(value)
    return ids


def _refinement_evidence_row_is_usable_feedback(row: dict[str, Any]) -> bool:
    status = str(row.get("acceptance_status", "")).strip()
    if status.startswith("AWAITING_") or status.startswith("REJECTED_"):
        return False
    if "response_present" in row and not bool(row.get("response_present", False)):
        return False
    if "response_contract_ok" in row and not bool(row.get("response_contract_ok", False)):
        return False
    if "ok" in row and not bool(row.get("ok", False)):
        return False
    return True


def _refinement_evidence_proposal_is_usable(
    proposal: dict[str, Any],
    usable_refinement_evidence_ids: set[str],
    *,
    has_refinement_evidence_rows: bool,
) -> bool:
    if not has_refinement_evidence_rows:
        return True
    proposal_ids = {
        str(proposal.get("refinement_evidence_id", "")).strip(),
        str(proposal.get("refinement_item_id", "")).strip(),
    }
    return bool(proposal_ids.intersection(usable_refinement_evidence_ids))


def _resource_response_route_revision_reasons(
    row: dict[str, Any],
) -> tuple[str, ...]:
    reasons = list(_str_tuple(row.get("route_revision_reasons", [])))
    if row.get("route_revision_recommended", False) and not reasons:
        reasons.append("resource response recommended route revision")
    if _str_tuple(row.get("residual_goals", [])):
        reasons.append("resource response preserved residual prover goals")
    if _dict_value(row, "coverage_updates"):
        reasons.append("resource response updated library coverage status")
    if _formal_declaration_hits_for_target(
        row,
        str(row.get("target_prover_family", "")),
    ):
        reasons.append("resource response identified reusable formal declarations")
    if _str_tuple(row.get("source_refs", [])) or _dict_tuple(
        row.get("route_evidence_nodes", [])
    ):
        reasons.append("resource response supplied source-backed route evidence")
    if str(row.get("prover_diagnostic_signature", "")):
        reasons.append("resource response supplied prover diagnostic signature")
    return _str_tuple(reasons)


def _resource_response_informal_nodes(
    row: dict[str, Any],
) -> tuple[dict[str, object], ...]:
    primitive = str(row.get("primitive", ""))
    ledger_id = str(row.get("resource_response_ledger_id", ""))
    nodes: list[dict[str, object]] = []
    for index, node in enumerate(_dict_tuple(row.get("route_evidence_nodes", []))):
        normalized = dict(node)
        normalized.setdefault(
            "node_id",
            "resource_response_informal:"
            + stable_hash([ledger_id, "route_evidence", index, node])[:16],
        )
        normalized.setdefault("kind", "resource_response_route_evidence")
        normalized.setdefault("label", primitive)
        normalized.setdefault("primitive", primitive)
        normalized.setdefault("resource_response_ledger_id", ledger_id)
        normalized.setdefault("resource_id", str(row.get("resource_id", "")))
        nodes.append(normalized)
    if _str_tuple(row.get("source_refs", [])) and not nodes:
        nodes.append(
            {
                "node_id": "resource_response_informal:"
                + stable_hash([ledger_id, primitive, row.get("source_refs", [])])[:16],
                "kind": "resource_response_source_evidence",
                "label": primitive,
                "primitive": primitive,
                "resource_response_ledger_id": ledger_id,
                "resource_id": str(row.get("resource_id", "")),
                "source_refs": _str_tuple(row.get("source_refs", [])),
                "proof_evidence_status": PROOF_EVIDENCE_STATUS,
                "proof_evidence_boundary": PROOF_EVIDENCE_BOUNDARY,
            }
        )
    return _merge_nodes(tuple(nodes))


def _resource_response_formal_nodes(
    row: dict[str, Any],
) -> tuple[dict[str, object], ...]:
    primitive = str(row.get("primitive", ""))
    ledger_id = str(row.get("resource_response_ledger_id", ""))
    target_prover_family = str(row.get("target_prover_family", ""))
    is_lean_target = _is_lean_target_prover(target_prover_family)
    coverage_updates = _dict_value(row, "coverage_updates")
    nodes: list[dict[str, object]] = []
    hits = _formal_declaration_hits_for_target(row, target_prover_family)
    for index, hit in enumerate(_dict_tuple(hits)):
        declaration = str(
            hit.get("declaration", "")
            or hit.get("declaration_name", "")
            or hit.get("name", "")
        )
        normalized = dict(hit)
        hit_hash_kind = "lean_hit" if is_lean_target else "formal_hit"
        normalized.setdefault(
            "node_id",
            (
                "resource_response_lean:"
                if is_lean_target
                else "resource_response_formal:"
            )
            + stable_hash([ledger_id, hit_hash_kind, index, hit])[:16],
        )
        normalized.setdefault(
            "kind",
            (
                "resource_response_lean_declaration_hit"
                if is_lean_target
                else "resource_response_formal_declaration_hit"
            ),
        )
        normalized.setdefault("label", primitive)
        normalized.setdefault("primitive", primitive)
        normalized.setdefault("declaration", declaration)
        normalized.setdefault("resource_response_ledger_id", ledger_id)
        normalized.setdefault("resource_id", str(row.get("resource_id", "")))
        if primitive in coverage_updates:
            normalized.setdefault("coverage_status", str(coverage_updates[primitive]))
        nodes.append(normalized)
    for coverage_primitive, coverage_status in coverage_updates.items():
        coverage_primitive_str = str(coverage_primitive)
        coverage_status_str = str(coverage_status)
        nodes.append(
            {
                "node_id": "resource_response_coverage_update:"
                + stable_hash([ledger_id, coverage_primitive_str, coverage_status_str])[
                    :16
                ],
                "kind": "resource_response_coverage_update",
                "label": coverage_primitive_str,
                "primitive": coverage_primitive_str,
                "coverage_status": coverage_status_str,
                "resource_response_ledger_id": ledger_id,
                "resource_id": str(row.get("resource_id", "")),
                "proof_evidence_status": PROOF_EVIDENCE_STATUS,
                "proof_evidence_boundary": PROOF_EVIDENCE_BOUNDARY,
            }
        )
    return _merge_nodes(tuple(nodes))


def _proposal_index(proposals: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    index: dict[str, list[dict[str, Any]]] = {}
    for proposal in proposals:
        for key in _proposal_keys(proposal):
            index.setdefault(key, []).append(proposal)
    return index


def _match_proposals(
    plan_row: dict[str, Any],
    proposal_index: dict[str, list[dict[str, Any]]],
) -> list[dict[str, Any]]:
    seen: set[str] = set()
    matched: list[dict[str, Any]] = []
    for key in _plan_keys(plan_row):
        for proposal in proposal_index.get(key, []):
            proposal_id = str(proposal.get("proposal_id", ""))
            if proposal_id in seen:
                continue
            seen.add(proposal_id)
            matched.append(proposal)
    return sorted(
        matched,
        key=lambda proposal: (
            str(proposal.get("hook_kind", "")) != "route_revision",
            -len(_str_tuple(proposal.get("revised_selected_primitives", []))),
            str(proposal.get("proposal_id", "")),
        ),
    )


def _plan_keys(row: dict[str, Any]) -> tuple[str, ...]:
    return _prefixed_keys(
        (
            ("goal_plan_id", row.get("goal_plan_id", "")),
            ("route_id", row.get("route_id", "")),
            ("display_name", row.get("display_name", "")),
        )
    )


def _proposal_keys(row: dict[str, Any]) -> tuple[str, ...]:
    return _prefixed_keys(
        (
            ("goal_plan_id", row.get("goal_plan_id", "")),
            ("route_id", row.get("route_id", "")),
            ("display_name", row.get("display_name", "")),
        )
    )


def _prefixed_keys(values: tuple[tuple[str, Any], ...]) -> tuple[str, ...]:
    return tuple(
        f"{prefix}:{value}"
        for prefix, raw_value in values
        for value in (str(raw_value),)
        if value
    )


def _overlay_id(plan_row: dict[str, Any], proposals: list[dict[str, Any]]) -> str:
    return "formalization_gap_planner_route_revision_overlay:" + stable_hash(
        [
            plan_row.get("goal_plan_id", ""),
            plan_row.get("route_id", ""),
            plan_row.get("display_name", ""),
            [proposal.get("proposal_id", "") for proposal in proposals],
        ]
    )[:16]


def _existing_graph_nodes(graph: Any) -> tuple[dict[str, object], ...]:
    if not isinstance(graph, dict):
        return tuple()
    return _dict_tuple(graph.get("nodes", []))


def _existing_formal_realization_nodes(
    plan_row: dict[str, Any],
    fallback_lean_nodes: tuple[dict[str, object], ...],
) -> tuple[dict[str, object], ...]:
    formal_nodes = _dict_tuple(plan_row.get("formal_realization_dag_nodes", []))
    if formal_nodes:
        return formal_nodes
    graph_nodes = _existing_graph_nodes(plan_row.get("formal_realization_dag", {}))
    if graph_nodes:
        return graph_nodes
    return fallback_lean_nodes


def _merge_nodes(*node_groups: tuple[dict[str, object], ...]) -> tuple[dict[str, object], ...]:
    merged: dict[str, dict[str, object]] = {}
    fallback_index = 0
    for nodes in node_groups:
        for node in nodes:
            key = str(node.get("node_id", "")) or str(node.get("declaration", ""))
            if not key:
                key = "node:" + stable_hash([fallback_index, node])[:12]
                fallback_index += 1
            merged[key] = dict(node)
    return tuple(merged[key] for key in sorted(merged))


def _merge_dicts(*groups: tuple[dict[str, object], ...]) -> tuple[dict[str, object], ...]:
    merged: dict[str, dict[str, object]] = {}
    fallback_index = 0
    for group in groups:
        for item in group:
            key = (
                str(item.get("resource_response_ledger_id", ""))
                or str(item.get("resource_request_id", ""))
            )
            if not key:
                key = "dict:" + stable_hash([fallback_index, item])[:12]
                fallback_index += 1
            merged[key] = dict(item)
    return tuple(merged[key] for key in sorted(merged))


def _route_alignment_edges(
    *,
    selected_primitives: tuple[str, ...],
    informal_nodes: tuple[dict[str, object], ...],
    lean_nodes: tuple[dict[str, object], ...],
) -> tuple[tuple[dict[str, object], ...], tuple[str, ...]]:
    informal_by_label = _nodes_by_label(informal_nodes)
    lean_by_label = _nodes_by_label(lean_nodes)
    edges: list[dict[str, object]] = []
    unaligned: list[str] = []
    for primitive in selected_primitives:
        informal_node = informal_by_label.get(primitive)
        lean_node = lean_by_label.get(primitive)
        if not informal_node or not lean_node:
            unaligned.append(primitive)
            continue
        edge = {
            "source": str(informal_node.get("node_id", "")),
            "target": str(lean_node.get("node_id", "")),
            "kind": "aligned_to_formal_realization_candidate",
            "edge_type": "revised_informal_to_formal_alignment",
            "primitive": primitive,
            "alignment_status": _alignment_status(lean_node),
            "proof_evidence_status": PROOF_EVIDENCE_STATUS,
            "proof_evidence_boundary": PROOF_EVIDENCE_BOUNDARY,
        }
        edges.append(edge)
    return (
        tuple(
            sorted(
                edges,
                key=lambda edge: (
                    str(edge.get("primitive", "")),
                    str(edge.get("target", "")),
                ),
            )
        ),
        tuple(sorted(dict.fromkeys(unaligned))),
    )


def _nodes_by_label(
    nodes: tuple[dict[str, object], ...],
) -> dict[str, dict[str, object]]:
    by_label: dict[str, dict[str, object]] = {}
    for node in nodes:
        label = str(node.get("label", "") or node.get("primitive", ""))
        node_id = str(node.get("node_id", ""))
        if label and node_id and label not in by_label:
            by_label[label] = node
    return by_label


def _alignment_status(node: dict[str, object]) -> str:
    for field_name in ("alignment_status", "coverage_status", "planned_action", "kind"):
        value = str(node.get(field_name, ""))
        if value:
            return value
    return "revised_realization_candidate"


def _nonempty_tuples(values: Any) -> tuple[tuple[str, ...], ...]:
    return tuple(item for item in (_str_tuple(value) for value in values) if item)


def _prefer_largest_tuple(values: tuple[tuple[str, ...], ...]) -> tuple[str, ...]:
    if not values:
        return tuple()
    return sorted(values, key=lambda item: (-len(item), item))[0]


def _tuple_diff(left: tuple[str, ...], right: tuple[str, ...]) -> tuple[str, ...]:
    right_set = set(right)
    return tuple(item for item in left if item not in right_set)


def _dict_tuple(values: Any) -> tuple[dict[str, object], ...]:
    if not isinstance(values, (list, tuple)):
        return tuple()
    return tuple(item for item in values if isinstance(item, dict))


def _dict_value(row: dict[str, Any], key: str) -> dict[str, Any]:
    value = row.get(key, {})
    return value if isinstance(value, dict) else {}


def _residual_goal_context_value(value: Any) -> dict[str, object]:
    if not isinstance(value, dict):
        return {}
    context: dict[str, object] = dict(value)
    for field_name in (
        "residual_goals",
        "residual_primitives",
        "target_primitives",
        "source_refs",
        "queries",
        "source_search_queries",
        "literature_queries",
    ):
        if field_name in context:
            context[field_name] = _str_tuple(context.get(field_name, []))
    if "source_snippets" in context:
        context["source_snippets"] = _dict_tuple(context.get("source_snippets", []))
    for field_name in (
        "source_kind",
        "residual_goal",
        "interpretation",
        "route_repair",
        "repair_action",
        "source_search_status",
        "formal_gap_boundary",
    ):
        if field_name in context:
            context[field_name] = str(context.get(field_name, "") or "")
    return context


def _int_value(value: Any, *, default: int = -1) -> int:
    try:
        return int(value)
    except Exception:
        return default


def _average_int(values: Any) -> int:
    items: list[int] = []
    for value in values:
        try:
            items.append(int(value))
        except (TypeError, ValueError):
            continue
    if not items:
        return 0
    return round(sum(items) / len(items))


def _prover_attempt_class(attempt_status: str) -> str:
    return {
        "local_lean_scaffold_accepted": "target_prover_scaffold_accepted",
        "local_lean_failed": "target_prover_failed",
        "local_lean_unavailable": "target_prover_unavailable",
        "non_lean_skeleton": "non_target_prover_skeleton",
        "failed_with_residual_goals": "target_prover_failed",
        "placeholder_blocked": "placeholder_blocked",
        "formal_gap_scaffold_blocked": "formal_gap_scaffold_blocked",
        "missing_theorem_skeleton": "missing_theorem_skeleton",
    }.get(attempt_status, attempt_status)


def _str_tuple(values: Any) -> tuple[str, ...]:
    if isinstance(values, str):
        return (values,) if values else tuple()
    if not isinstance(values, (list, tuple, set)):
        try:
            values = tuple(values)
        except TypeError:
            return tuple()
    return tuple(sorted(dict.fromkeys(str(item) for item in values if str(item))))


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


def _markdown_report(payload: dict[str, object]) -> str:
    lines = [
        "# Formalization Gap Planner Route Revision Overlay",
        "",
        f"- Plan rows: {payload.get('n_plan_rows')}",
        f"- Proposals: {payload.get('n_route_revision_proposals')}",
        f"- Refinement evidence proposals: {payload.get('n_refinement_evidence_route_revision_proposals')}",
        f"- Refinement evidence proposals total: {payload.get('n_refinement_evidence_route_revision_proposals_total')}",
        f"- Refinement evidence proposals status-only: {payload.get('n_refinement_evidence_route_revision_proposals_status_only')}",
        f"- Resource-response ledger proposals: {payload.get('n_resource_response_ledger_route_revision_proposals')}",
        f"- Applied resource-response traces: {payload.get('n_applied_resource_response_traces')}",
        (
            "- Applied resource-response formal-attempt context traces: "
            f"{payload.get('n_applied_resource_response_formal_attempt_context_traces')}"
        ),
        (
            "- Applied resource-response route-brief evidence-gap traces: "
            f"{payload.get('n_applied_resource_response_route_planning_brief_evidence_gap_traces')}"
        ),
        (
            "- Applied resource-response traces with minimal-delta priority: "
            f"{payload.get('n_applied_resource_response_traces_with_minimal_delta_priority')}"
        ),
        (
            "- Applied resource-response reuse/evidence readiness: "
            f"{payload.get('average_applied_resource_response_reuse_readiness_score')}/"
            f"{payload.get('average_applied_resource_response_evidence_readiness_score')}"
        ),
        f"- Applied LLM route-planner hook traces: {payload.get('n_applied_llm_route_planner_hook_traces')}",
        (
            "- Applied LLM route-planner route-brief evidence-gap traces: "
            f"{payload.get('n_applied_llm_route_planner_route_planning_brief_evidence_gap_traces')}"
        ),
        (
            "- Applied LLM route-planner hook traces by source kind: "
            f"{payload.get('applied_llm_route_planner_hook_trace_by_source_kind')}"
        ),
        f"- Source snippets: {payload.get('n_source_snippets')}",
        f"- Resource-response status rows: {payload.get('n_resource_response_ledger_status_rows')}",
        f"- Resource responses awaiting: {payload.get('n_resource_response_ledger_awaiting')}",
        f"- Resource responses rejected: {payload.get('n_resource_response_ledger_rejected')}",
        f"- Routes revised: {payload.get('n_routes_with_revision')}",
        f"- Routes without revision: {payload.get('n_routes_without_revision')}",
        f"- Orphan proposals: {payload.get('n_orphan_route_revision_proposals')}",
        f"- Prover attempt statuses: {payload.get('by_prover_attempt_status')}",
        f"- Alignment edges: {payload.get('n_route_alignment_edges')}",
        f"- Unaligned primitives: {payload.get('n_unaligned_primitives')}",
        f"- Row schema valid: {payload.get('n_row_schema_valid')}/{payload.get('n_overlay_rows')}",
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
            f"- `{row.get('display_name')}` status={row.get('revision_status')} "
            f"added={len(row.get('added_primitives', []))} "
            f"attempts={row.get('applied_prover_attempt_statuses', [])} "
            f"proposals={len(row.get('applied_proposal_ids', []))}"
        )
    return "\n".join(lines) + "\n"
