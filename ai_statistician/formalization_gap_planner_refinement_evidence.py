from __future__ import annotations

import json
import re
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .fingerprint import stable_hash


FORMALIZATION_GAP_PLANNER_REFINEMENT_EVIDENCE_SCHEMA_VERSION = 2
PROOF_EVIDENCE_STATUS = "FORMALIZATION_GAP_PLANNER_REFINEMENT_EVIDENCE_NOT_PROOF_EVIDENCE"
PROOF_EVIDENCE_BOUNDARY = (
    "Formalization gap planner refinement evidence records literature search, "
    "formal-library grounding, prover diagnostics, and route-revision proposals. "
    "These rows may revise the route plan, but they are not theorem proof "
    "evidence. Only target-prover kernel verification can prove a theorem or "
    "bridge lemma."
)
REFINEMENT_TOOL_RESPONSE_SCHEMA_ID = (
    "urn:ai-statistician:schemas:"
    "formalization-gap-planner-refinement-tool-response:1"
)
REFINEMENT_EVIDENCE_ROW_SCHEMA_ID = (
    "urn:ai-statistician:schemas:"
    "formalization-gap-planner-refinement-evidence-row:1"
)


@dataclass(frozen=True)
class FormalizationGapPlannerRefinementEvidenceRow:
    schema_version: int
    refinement_evidence_id: str
    refinement_item_id: str
    goal_plan_id: str
    route_id: str
    display_name: str
    hook_kind: str
    refinement_stage: str
    owner_agent: str
    response_present: bool
    response_contract_ok: bool
    evidence_kind: str
    tool_name: str
    resource_request_ids: tuple[str, ...]
    resource_ids: tuple[str, ...]
    resource_request_bindings: tuple[dict[str, object], ...]
    llm_route_planner_hook_trace: dict[str, object]
    source_refs: tuple[str, ...]
    route_evidence_nodes: tuple[dict[str, object], ...]
    source_snippets: tuple[dict[str, object], ...]
    formal_declaration_hits: tuple[dict[str, object], ...]
    lean_declaration_hits: tuple[dict[str, object], ...]
    coverage_updates: dict[str, str]
    prover_diagnostics: tuple[str, ...]
    residual_goals: tuple[str, ...]
    prover_attempt_status: str
    prover_attempt_class: str
    target_prover_family: str
    prover_diagnostic_signature: str
    route_revision_summary: str
    revised_selected_primitives: tuple[str, ...]
    revised_delta_primitives: tuple[str, ...]
    revised_informal_knowledge_dag_nodes: tuple[dict[str, object], ...]
    revised_formal_realization_dag_nodes: tuple[dict[str, object], ...]
    revised_lean_realization_dag_nodes: tuple[dict[str, object], ...]
    route_revision_recommended: bool
    route_revision_reasons: tuple[str, ...]
    acceptance_status: str
    proof_evidence_status: str
    proof_evidence_boundary: str
    ok: bool
    errors: tuple[str, ...] = ()


def export_formalization_gap_planner_refinement_evidence(
    formalization_gap_planner_refinement_queue_dir: Path,
    out_dir: Path | None = None,
    *,
    response_jsonl: Path | None = None,
) -> dict[str, object]:
    """Validate tool responses to formalization-gap refinement queue rows."""

    errors: list[str] = []
    queue_manifest_path = (
        formalization_gap_planner_refinement_queue_dir
        / "formalization_gap_planner_refinement_queue_manifest.json"
    )
    queue_payload = _read_json(queue_manifest_path, errors)
    queue_rows = [row for row in queue_payload.get("rows", []) if isinstance(row, dict)]
    response_jsonl_path = (
        response_jsonl
        if response_jsonl is not None
        else formalization_gap_planner_refinement_queue_dir
        / "formalization_gap_planner_refinement_evidence_responses.jsonl"
    )
    responses, response_file_exists = _read_response_jsonl(response_jsonl_path, errors)
    response_schema = refinement_tool_response_json_schema()
    response_schema_errors = [
        validate_refinement_tool_response_row(response, response_schema)
        for response in responses
    ]
    response_by_item = _match_responses_to_queue_rows(responses, queue_rows, errors)
    rows = [
        _evidence_row(
            queue_row,
            response=response_by_item.get(str(queue_row.get("refinement_item_id", ""))),
        )
        for queue_row in queue_rows
    ]
    row_dicts = [asdict(row) for row in rows]
    evidence_row_schema = refinement_evidence_row_json_schema()
    evidence_row_schema_errors = [
        validate_refinement_evidence_row(row, evidence_row_schema)
        for row in row_dicts
    ]
    n_evidence_row_schema_valid = sum(
        1 for row_errors in evidence_row_schema_errors if not row_errors
    )
    by_hook_kind = Counter(row.hook_kind for row in rows)
    by_acceptance_status = Counter(row.acceptance_status for row in rows)
    by_prover_attempt_status = Counter(
        row.prover_attempt_status for row in rows if row.prover_attempt_status
    )
    by_prover_attempt_class = Counter(
        row.prover_attempt_class for row in rows if row.prover_attempt_class
    )
    route_revision_proposals = [
        _route_revision_proposal(row)
        for row in rows
        if row.route_revision_recommended
        or row.hook_kind == "route_revision"
        or row.prover_attempt_status
    ]
    payload: dict[str, object] = {
        "schema_version": FORMALIZATION_GAP_PLANNER_REFINEMENT_EVIDENCE_SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "component_name": "formalization_gap_planner_refinement_evidence",
        "formalization_gap_planner_refinement_queue_dir": str(
            formalization_gap_planner_refinement_queue_dir
        ),
        "formalization_gap_planner_refinement_queue_manifest": str(queue_manifest_path),
        "response_jsonl": str(response_jsonl_path),
        "response_jsonl_exists": response_file_exists,
        "n_refinement_items": len(queue_rows),
        "n_responses": len(responses),
        "n_response_schema_valid": sum(
            1 for row_errors in response_schema_errors if not row_errors
        ),
        "n_response_schema_invalid": sum(
            1 for row_errors in response_schema_errors if row_errors
        ),
        "n_evidence_rows": len(rows),
        "n_evidence_row_schema_valid": n_evidence_row_schema_valid,
        "n_evidence_row_schema_invalid": len(evidence_row_schema_errors)
        - n_evidence_row_schema_valid,
        "n_response_present": sum(1 for row in rows if row.response_present),
        "n_awaiting_tool_response": sum(
            1 for row in rows if row.acceptance_status == "AWAITING_REFINEMENT_TOOL_RESPONSE"
        ),
        "n_contract_ok": sum(1 for row in rows if row.response_contract_ok),
        "n_literature_evidence": by_hook_kind.get("literature_discovery", 0),
        "n_source_snippets": sum(len(row.source_snippets) for row in rows),
        "n_literature_rows_with_source_snippets": sum(
            1
            for row in rows
            if row.hook_kind == "literature_discovery" and row.source_snippets
        ),
        "n_formal_grounding_evidence": (
            by_hook_kind.get("formal_library_grounding", 0)
            + by_hook_kind.get("lean_library_grounding", 0)
        ),
        "n_lean_grounding_evidence": by_hook_kind.get("lean_library_grounding", 0),
        "n_prover_feedback_evidence": by_hook_kind.get("proof_state_feedback", 0),
        "n_route_revision_evidence": by_hook_kind.get("route_revision", 0),
        "n_route_revision_recommended": sum(
            1 for row in rows if row.route_revision_recommended
        ),
        "n_route_revision_proposals": len(route_revision_proposals),
        "n_rejected": sum(1 for row in rows if row.acceptance_status.startswith("REJECTED_")),
        "n_ok": sum(1 for row in rows if row.ok),
        "all_ok": not errors
        and all(not row_errors for row_errors in response_schema_errors)
        and all(not row_errors for row_errors in evidence_row_schema_errors)
        and all(row.ok for row in rows),
        "errors": errors,
        "by_hook_kind": dict(sorted(by_hook_kind.items())),
        "by_acceptance_status": dict(sorted(by_acceptance_status.items())),
        "by_prover_attempt_status": dict(sorted(by_prover_attempt_status.items())),
        "by_prover_attempt_class": dict(sorted(by_prover_attempt_class.items())),
        "n_prover_attempt_status_records": sum(
            1 for row in rows if row.prover_attempt_status
        ),
        "n_prover_attempt_class_records": sum(
            1 for row in rows if row.prover_attempt_class
        ),
        "n_distinct_prover_diagnostic_signatures": len(
            {row.prover_diagnostic_signature for row in rows if row.prover_diagnostic_signature}
        ),
        "rows": row_dicts,
        "route_revision_proposals": route_revision_proposals,
        "refinement_tool_response_schema": response_schema,
        "refinement_evidence_row_schema": evidence_row_schema,
        "evidence_fingerprint": stable_hash(row_dicts),
        "proof_evidence_status": PROOF_EVIDENCE_STATUS,
        "proof_evidence_boundary": PROOF_EVIDENCE_BOUNDARY,
        "limitations": [
            "refinement evidence rows are tool-output records, not theorem proof evidence",
            "literature evidence must be attached to informal route DAG nodes before it can justify a route revision",
            "formal declaration hits and coverage updates are library-grounding evidence, not proof evidence",
            "prover diagnostics are feedback for route repair unless a separate kernel verifier closes the target",
        ],
    }
    if out_dir is not None:
        out_dir.mkdir(parents=True, exist_ok=True)
        (
            out_dir / "formalization_gap_planner_refinement_evidence_manifest.json"
        ).write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
        (
            out_dir / "formalization_gap_planner_refinement_tool_response.schema.json"
        ).write_text(json.dumps(response_schema, indent=2), encoding="utf-8")
        (
            out_dir / "formalization_gap_planner_refinement_evidence_row.schema.json"
        ).write_text(json.dumps(evidence_row_schema, indent=2), encoding="utf-8")
        (out_dir / "formalization_gap_planner_refinement_evidence.jsonl").write_text(
            "\n".join(json.dumps(asdict(row), sort_keys=True) for row in rows)
            + ("\n" if rows else ""),
            encoding="utf-8",
        )
        (
            out_dir / "formalization_gap_planner_route_revision_proposals.jsonl"
        ).write_text(
            "\n".join(json.dumps(row, sort_keys=True) for row in route_revision_proposals)
            + ("\n" if route_revision_proposals else ""),
            encoding="utf-8",
        )
        (out_dir / "formalization_gap_planner_refinement_evidence.md").write_text(
            _markdown_report(payload),
            encoding="utf-8",
        )
    return payload


def refinement_tool_response_json_schema() -> dict[str, object]:
    """JSON Schema for frontier/local refinement-tool response rows."""

    string_array = {"type": "array", "items": {"type": "string"}}
    object_array = {"type": "array", "items": {"type": "object"}}
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": REFINEMENT_TOOL_RESPONSE_SCHEMA_ID,
        "title": "Formalization Gap Planner Refinement Tool Response",
        "description": (
            "Response contract for literature, formal-library, proof-state, "
            "and route-revision tools feeding the formalization-gap planner. "
            "Rows are not theorem proof evidence."
        ),
        "type": "object",
        "additionalProperties": True,
        "required": [
            "refinement_item_id",
            "evidence_kind",
            "tool_name",
        ],
        "properties": {
            "refinement_item_id": {"type": "string", "minLength": 1},
            "route_id": {"type": "string"},
            "display_name": {"type": "string"},
            "evidence_kind": {
                "enum": [
                    "literature_route_evidence",
                    "formal_library_grounding",
                    "lean_library_grounding",
                    "prover_feedback",
                    "route_revision_proposal",
                ]
            },
            "tool_name": {"type": "string", "minLength": 1},
            "resource_request_ids": string_array,
            "resource_ids": string_array,
            "resource_request_bindings": object_array,
            "llm_route_planner_hook_trace": {"type": "object"},
            "source_refs": string_array,
            "source_snippets": object_array,
            "route_evidence_nodes": object_array,
            "formal_declaration_hits": object_array,
            "lean_declaration_hits": object_array,
            "coverage_updates": {"type": "object"},
            "prover_diagnostics": string_array,
            "residual_goals": string_array,
            "attempt_status": {"type": "string"},
            "prover_attempt_class": {"type": "string"},
            "target_prover_family": {"type": "string"},
            "route_revision_summary": {"type": "string"},
            "revised_selected_primitives": string_array,
            "revised_delta_primitives": string_array,
            "revised_informal_knowledge_dag_nodes": object_array,
            "revised_formal_realization_dag_nodes": object_array,
            "revised_lean_realization_dag_nodes": object_array,
            "route_revision_recommended": {"type": "boolean"},
            "route_revision_reasons": string_array,
            "proof_evidence_status": {
                "type": "string",
                "pattern": "NOT_PROOF_EVIDENCE",
            },
            "proof_evidence_boundary": {
                "type": "string",
                "pattern": "not theorem proof evidence",
            },
        },
    }


def refinement_evidence_row_json_schema() -> dict[str, object]:
    """JSON Schema for normalized refinement evidence rows."""

    string_array = {"type": "array", "items": {"type": "string"}}
    object_array = {"type": "array", "items": {"type": "object"}}
    string_map = {"type": "object", "additionalProperties": {"type": "string"}}
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": REFINEMENT_EVIDENCE_ROW_SCHEMA_ID,
        "title": "Formalization Gap Planner Refinement Evidence Row",
        "description": (
            "Normalized accepted-or-awaiting evidence row produced after "
            "matching refinement tool responses to queued route hooks. Rows are "
            "not theorem proof evidence."
        ),
        "type": "object",
        "additionalProperties": True,
        "required": [
            "schema_version",
            "refinement_evidence_id",
            "refinement_item_id",
            "goal_plan_id",
            "route_id",
            "display_name",
            "hook_kind",
            "refinement_stage",
            "owner_agent",
            "response_present",
            "response_contract_ok",
            "evidence_kind",
            "tool_name",
            "resource_request_ids",
            "resource_ids",
            "resource_request_bindings",
            "source_refs",
            "route_evidence_nodes",
            "formal_declaration_hits",
            "coverage_updates",
            "prover_diagnostics",
            "residual_goals",
            "prover_attempt_status",
            "prover_attempt_class",
            "target_prover_family",
            "prover_diagnostic_signature",
            "route_revision_summary",
            "revised_selected_primitives",
            "revised_delta_primitives",
            "revised_informal_knowledge_dag_nodes",
            "revised_formal_realization_dag_nodes",
            "route_revision_recommended",
            "route_revision_reasons",
            "acceptance_status",
            "proof_evidence_status",
            "proof_evidence_boundary",
            "ok",
        ],
        "properties": {
            "schema_version": {
                "type": "integer",
                "const": FORMALIZATION_GAP_PLANNER_REFINEMENT_EVIDENCE_SCHEMA_VERSION,
            },
            "refinement_evidence_id": {"type": "string", "minLength": 1},
            "refinement_item_id": {"type": "string", "minLength": 1},
            "goal_plan_id": {"type": "string", "minLength": 1},
            "route_id": {"type": "string", "minLength": 1},
            "display_name": {"type": "string", "minLength": 1},
            "hook_kind": {
                "enum": [
                    "literature_discovery",
                    "formal_library_grounding",
                    "lean_library_grounding",
                    "proof_state_feedback",
                    "route_revision",
                ]
            },
            "refinement_stage": {"type": "string"},
            "owner_agent": {"type": "string"},
            "response_present": {"type": "boolean"},
            "response_contract_ok": {"type": "boolean"},
            "evidence_kind": {"type": "string"},
            "tool_name": {"type": "string"},
            "resource_request_ids": string_array,
            "resource_ids": string_array,
            "resource_request_bindings": object_array,
            "source_refs": string_array,
            "source_snippets": object_array,
            "route_evidence_nodes": object_array,
            "formal_declaration_hits": object_array,
            "lean_declaration_hits": object_array,
            "coverage_updates": string_map,
            "prover_diagnostics": string_array,
            "residual_goals": string_array,
            "prover_attempt_status": {"type": "string"},
            "prover_attempt_class": {"type": "string"},
            "target_prover_family": {"type": "string"},
            "prover_diagnostic_signature": {"type": "string"},
            "route_revision_summary": {"type": "string"},
            "revised_selected_primitives": string_array,
            "revised_delta_primitives": string_array,
            "revised_informal_knowledge_dag_nodes": object_array,
            "revised_formal_realization_dag_nodes": object_array,
            "revised_lean_realization_dag_nodes": object_array,
            "route_revision_recommended": {"type": "boolean"},
            "route_revision_reasons": string_array,
            "acceptance_status": {"type": "string", "minLength": 1},
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


def validate_refinement_tool_response_row(
    row: dict[str, Any],
    schema: dict[str, object] | None = None,
) -> tuple[str, ...]:
    response_schema = schema or refinement_tool_response_json_schema()
    errors: list[str] = []
    required = response_schema.get("required", [])
    if isinstance(required, list):
        for field_name in required:
            if isinstance(field_name, str) and field_name not in row:
                errors.append(f"{field_name} required")
    properties = response_schema.get("properties", {})
    if isinstance(properties, dict):
        for field_name, field_schema in properties.items():
            if not isinstance(field_name, str) or field_name not in row:
                continue
            if isinstance(field_schema, dict):
                errors.extend(
                    _schema_property_errors(field_name, row[field_name], field_schema)
                )
    return tuple(errors)


def validate_refinement_evidence_row(
    row: dict[str, Any],
    schema: dict[str, object] | None = None,
) -> tuple[str, ...]:
    row_schema = schema or refinement_evidence_row_json_schema()
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


def _evidence_row(
    queue_row: dict[str, Any],
    *,
    response: dict[str, Any] | None,
) -> FormalizationGapPlannerRefinementEvidenceRow:
    refinement_item_id = str(queue_row.get("refinement_item_id", ""))
    goal_plan_id = str(queue_row.get("goal_plan_id", ""))
    route_id = str(queue_row.get("route_id", ""))
    display_name = str(queue_row.get("display_name", ""))
    hook_kind = str(queue_row.get("hook_kind", ""))
    refinement_stage = str(queue_row.get("refinement_stage", ""))
    owner_agent = str(queue_row.get("owner_agent", ""))
    resource_request_ids = _str_tuple(queue_row.get("resource_request_ids", []))
    resource_ids = _str_tuple(queue_row.get("resource_ids", []))
    resource_request_bindings = _dict_tuple(
        queue_row.get("resource_request_bindings", [])
    )
    llm_route_planner_hook_trace = _dict_value(
        queue_row,
        "llm_route_planner_hook_trace",
    )
    if response is None:
        return FormalizationGapPlannerRefinementEvidenceRow(
            schema_version=FORMALIZATION_GAP_PLANNER_REFINEMENT_EVIDENCE_SCHEMA_VERSION,
            refinement_evidence_id=_evidence_id(refinement_item_id, None),
            refinement_item_id=refinement_item_id,
            goal_plan_id=goal_plan_id,
            route_id=route_id,
            display_name=display_name,
            hook_kind=hook_kind,
            refinement_stage=refinement_stage,
            owner_agent=owner_agent,
            response_present=False,
            response_contract_ok=False,
            evidence_kind="",
            tool_name="",
            resource_request_ids=resource_request_ids,
            resource_ids=resource_ids,
            resource_request_bindings=resource_request_bindings,
            llm_route_planner_hook_trace=llm_route_planner_hook_trace,
            source_refs=(),
            route_evidence_nodes=(),
            source_snippets=(),
            formal_declaration_hits=(),
            lean_declaration_hits=(),
            coverage_updates={},
            prover_diagnostics=(),
            residual_goals=(),
            prover_attempt_status="",
            prover_attempt_class="",
            target_prover_family=str(queue_row.get("target_prover_family", "")),
            prover_diagnostic_signature="",
            route_revision_summary="",
            revised_selected_primitives=(),
            revised_delta_primitives=(),
            revised_informal_knowledge_dag_nodes=(),
            revised_formal_realization_dag_nodes=(),
            revised_lean_realization_dag_nodes=(),
            route_revision_recommended=False,
            route_revision_reasons=(),
            acceptance_status="AWAITING_REFINEMENT_TOOL_RESPONSE",
            proof_evidence_status="AWAITING_RESPONSE_NOT_PROOF_EVIDENCE",
            proof_evidence_boundary=(
                "No refinement tool response has been recorded. This awaiting "
                "state is not theorem proof evidence."
            ),
            ok=True,
            errors=(),
        )

    errors: list[str] = []
    _require_matching_field(response, queue_row, "refinement_item_id", errors)
    _require_matching_field(response, queue_row, "route_id", errors, required=False)
    _require_matching_field(response, queue_row, "display_name", errors, required=False)
    evidence_kind = str(response.get("evidence_kind", ""))
    tool_name = str(response.get("tool_name", ""))
    if not evidence_kind:
        errors.append("evidence_kind missing")
    if not tool_name:
        errors.append("tool_name missing")
    response_resource_request_ids = _str_tuple(
        response.get("resource_request_ids", [])
    )
    response_resource_ids = _str_tuple(response.get("resource_ids", []))
    response_resource_request_bindings = _dict_tuple(
        response.get("resource_request_bindings", [])
    )
    if response_resource_request_ids:
        resource_request_ids = _merge_str_tuples(
            resource_request_ids,
            response_resource_request_ids,
        )
    if response_resource_ids:
        resource_ids = _merge_str_tuples(resource_ids, response_resource_ids)
    if response_resource_request_bindings:
        resource_request_bindings = _merge_dict_tuples(
            resource_request_bindings,
            response_resource_request_bindings,
        )
    expected_kinds = _expected_evidence_kinds(hook_kind)
    if evidence_kind and expected_kinds and evidence_kind not in expected_kinds:
        errors.append(f"evidence_kind {evidence_kind} does not match hook {hook_kind}")

    source_refs = _str_tuple(response.get("source_refs", []))
    route_evidence_nodes = _dict_tuple(response.get("route_evidence_nodes", []))
    source_snippets = _dict_tuple(response.get("source_snippets", []))
    if not source_snippets:
        source_snippets = _source_snippets_from_route_evidence_nodes(
            route_evidence_nodes
        )
    formal_declaration_hits = _dict_tuple(
        response.get("formal_declaration_hits", response.get("lean_declaration_hits", []))
    )
    lean_declaration_hits = _dict_tuple(
        response.get("lean_declaration_hits", formal_declaration_hits)
    )
    coverage_updates = _coverage_updates(response.get("coverage_updates", {}), errors)
    prover_diagnostics = _str_tuple(response.get("prover_diagnostics", []))
    residual_goals = _str_tuple(response.get("residual_goals", []))
    prover_attempt_status = str(response.get("attempt_status", ""))
    prover_attempt_class = str(
        response.get(
            "prover_attempt_class",
            _prover_attempt_class(prover_attempt_status),
        )
    )
    target_prover_family = str(
        response.get(
            "target_prover_family",
            queue_row.get("target_prover_family", ""),
        )
    )
    route_revision_summary = str(response.get("route_revision_summary", ""))
    revised_selected_primitives = _str_tuple(
        response.get("revised_selected_primitives", [])
    )
    revised_delta_primitives = _str_tuple(response.get("revised_delta_primitives", []))
    revised_informal_nodes = _dict_tuple(
        response.get("revised_informal_knowledge_dag_nodes", [])
    )
    revised_formal_nodes = _dict_tuple(
        response.get(
            "revised_formal_realization_dag_nodes",
            response.get("revised_lean_realization_dag_nodes", []),
        )
    )
    revised_lean_nodes = _dict_tuple(
        response.get("revised_lean_realization_dag_nodes", revised_formal_nodes)
    )
    route_revision_recommended = bool(response.get("route_revision_recommended", False))
    route_revision_reasons = _str_tuple(response.get("route_revision_reasons", []))
    prover_diagnostic_signature = _prover_diagnostic_signature(
        prover_attempt_status,
        prover_diagnostics,
        residual_goals,
        route_revision_reasons,
    )
    if "route_revision_recommended" in response and not isinstance(
        response.get("route_revision_recommended"),
        bool,
    ):
        errors.append("route_revision_recommended must be boolean")

    if hook_kind == "literature_discovery":
        if not source_refs:
            errors.append("source_refs missing for literature_discovery")
        if not route_evidence_nodes:
            errors.append("route_evidence_nodes missing for literature_discovery")
    elif _is_formal_library_grounding_hook(hook_kind):
        if not formal_declaration_hits:
            errors.append(
                "formal_declaration_hits missing for formal_library_grounding"
            )
        if not coverage_updates:
            errors.append("coverage_updates missing for formal_library_grounding")
    elif hook_kind == "proof_state_feedback":
        if not prover_diagnostics and not residual_goals:
            errors.append(
                "prover_diagnostics or residual_goals required for proof_state_feedback"
            )
    elif hook_kind == "route_revision":
        if not route_revision_summary:
            errors.append("route_revision_summary missing for route_revision")
        if not revised_selected_primitives and not revised_delta_primitives:
            errors.append(
                "revised_selected_primitives or revised_delta_primitives required for route_revision"
            )
        route_revision_recommended = True
    else:
        errors.append(f"unsupported hook_kind: {hook_kind}")

    if route_revision_recommended and not route_revision_reasons:
        errors.append("route_revision_reasons missing when route_revision_recommended")
    acceptance_status = (
        "REFINEMENT_EVIDENCE_RECORDED_NOT_PROOF_EVIDENCE"
        if not errors
        else "REJECTED_REFINEMENT_EVIDENCE_CONTRACT"
    )
    return FormalizationGapPlannerRefinementEvidenceRow(
        schema_version=FORMALIZATION_GAP_PLANNER_REFINEMENT_EVIDENCE_SCHEMA_VERSION,
        refinement_evidence_id=_evidence_id(refinement_item_id, response),
        refinement_item_id=refinement_item_id,
        goal_plan_id=goal_plan_id,
        route_id=route_id,
        display_name=display_name,
        hook_kind=hook_kind,
        refinement_stage=refinement_stage,
        owner_agent=owner_agent,
        response_present=True,
        response_contract_ok=not errors,
        evidence_kind=evidence_kind,
        tool_name=tool_name,
        resource_request_ids=resource_request_ids,
        resource_ids=resource_ids,
        resource_request_bindings=resource_request_bindings,
        llm_route_planner_hook_trace=llm_route_planner_hook_trace,
        source_refs=source_refs,
        route_evidence_nodes=route_evidence_nodes,
        source_snippets=source_snippets,
        formal_declaration_hits=formal_declaration_hits,
        lean_declaration_hits=lean_declaration_hits,
        coverage_updates=coverage_updates,
        prover_diagnostics=prover_diagnostics,
        residual_goals=residual_goals,
        prover_attempt_status=prover_attempt_status,
        prover_attempt_class=prover_attempt_class,
        target_prover_family=target_prover_family,
        prover_diagnostic_signature=prover_diagnostic_signature,
        route_revision_summary=route_revision_summary,
        revised_selected_primitives=revised_selected_primitives,
        revised_delta_primitives=revised_delta_primitives,
        revised_informal_knowledge_dag_nodes=revised_informal_nodes,
        revised_formal_realization_dag_nodes=revised_formal_nodes,
        revised_lean_realization_dag_nodes=revised_lean_nodes,
        route_revision_recommended=route_revision_recommended,
        route_revision_reasons=route_revision_reasons,
        acceptance_status=acceptance_status,
        proof_evidence_status=PROOF_EVIDENCE_STATUS,
        proof_evidence_boundary=PROOF_EVIDENCE_BOUNDARY,
        ok=not errors,
        errors=tuple(errors),
    )


def _route_revision_proposal(
    row: FormalizationGapPlannerRefinementEvidenceRow,
) -> dict[str, object]:
    return {
        "proposal_id": "formalization_gap_planner_route_revision:"
        + stable_hash([row.refinement_evidence_id, row.route_revision_reasons])[:16],
        "refinement_evidence_id": row.refinement_evidence_id,
        "refinement_item_id": row.refinement_item_id,
        "goal_plan_id": row.goal_plan_id,
        "route_id": row.route_id,
        "display_name": row.display_name,
        "hook_kind": row.hook_kind,
        "resource_request_ids": row.resource_request_ids,
        "resource_ids": row.resource_ids,
        "resource_request_bindings": row.resource_request_bindings,
        "llm_route_planner_hook_trace": row.llm_route_planner_hook_trace,
        "route_revision_summary": row.route_revision_summary,
        "route_revision_reasons": row.route_revision_reasons,
        "revised_selected_primitives": row.revised_selected_primitives,
        "revised_delta_primitives": row.revised_delta_primitives,
        "revised_informal_knowledge_dag_nodes": row.revised_informal_knowledge_dag_nodes,
        "revised_formal_realization_dag_nodes": row.revised_formal_realization_dag_nodes,
        "revised_lean_realization_dag_nodes": row.revised_lean_realization_dag_nodes,
        "source_refs": row.source_refs,
        "formal_declaration_hits": row.formal_declaration_hits,
        "lean_declaration_hits": row.lean_declaration_hits,
        "residual_goals": row.residual_goals,
        "prover_attempt_status": row.prover_attempt_status,
        "prover_attempt_class": row.prover_attempt_class,
        "target_prover_family": row.target_prover_family,
        "prover_diagnostic_signature": row.prover_diagnostic_signature,
        "source_snippets": row.source_snippets,
        "required_gate": (
            "rerun goal-conditioned minimal formalization planning and replay "
            "before treating this revision as proof-relevant"
        ),
        "proof_evidence_status": PROOF_EVIDENCE_STATUS,
        "proof_evidence_boundary": PROOF_EVIDENCE_BOUNDARY,
    }


def _expected_evidence_kinds(hook_kind: str) -> tuple[str, ...]:
    return {
        "literature_discovery": ("literature_route_evidence",),
        "formal_library_grounding": (
            "formal_library_grounding",
            "lean_library_grounding",
        ),
        "lean_library_grounding": (
            "formal_library_grounding",
            "lean_library_grounding",
        ),
        "proof_state_feedback": ("prover_feedback",),
        "route_revision": ("route_revision_proposal",),
    }.get(hook_kind, tuple())


def _is_formal_library_grounding_hook(hook_kind: str) -> bool:
    return hook_kind in {"formal_library_grounding", "lean_library_grounding"}


def _match_responses_to_queue_rows(
    responses: list[dict[str, Any]],
    queue_rows: list[dict[str, Any]],
    errors: list[str],
) -> dict[str, dict[str, Any]]:
    known_ids = {
        str(row.get("refinement_item_id", ""))
        for row in queue_rows
        if str(row.get("refinement_item_id", ""))
    }
    matched: dict[str, dict[str, Any]] = {}
    for response in responses:
        response_id = str(response.get("refinement_item_id", ""))
        if not response_id:
            errors.append("response missing refinement_item_id")
            continue
        if response_id not in known_ids:
            errors.append(f"response references unknown refinement_item_id: {response_id}")
            continue
        if response_id in matched:
            errors.append(f"duplicate response for refinement_item_id: {response_id}")
            continue
        matched[response_id] = response
    return matched


def _require_matching_field(
    response: dict[str, Any],
    queue_row: dict[str, Any],
    field_name: str,
    errors: list[str],
    *,
    required: bool = True,
) -> None:
    response_value = str(response.get(field_name, ""))
    queue_value = str(queue_row.get(field_name, ""))
    if required and not response_value:
        errors.append(f"{field_name} missing")
    if response_value and queue_value and response_value != queue_value:
        errors.append(
            f"{field_name} mismatch: response={response_value} queue={queue_value}"
        )


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
            if isinstance(item_schema, dict):
                item_type = item_schema.get("type")
                bad_indexes = [
                    idx
                    for idx, item in enumerate(value)
                    if (item_type == "string" and not isinstance(item, str))
                    or (item_type == "object" and not isinstance(item, dict))
                ]
                if bad_indexes:
                    errors.append(
                        f"{field_name} items must be {item_type} at indexes "
                        + ",".join(str(idx) for idx in bad_indexes)
                    )
    if "enum" in field_schema and isinstance(field_schema["enum"], list):
        if value not in field_schema["enum"]:
            errors.append(
                f"{field_name} must be one of "
                + ",".join(str(item) for item in field_schema["enum"])
            )
    if "const" in field_schema and value != field_schema["const"]:
        errors.append(f"{field_name} must equal {field_schema['const']!r}")
    pattern = field_schema.get("pattern")
    if isinstance(pattern, str) and isinstance(value, str):
        if re.search(pattern, value) is None:
            errors.append(f"{field_name} must match /{pattern}/")
    return tuple(errors)


def _coverage_updates(values: Any, errors: list[str]) -> dict[str, str]:
    if not isinstance(values, dict):
        if values:
            errors.append("coverage_updates must be an object")
        return {}
    return {str(key): str(value) for key, value in values.items() if str(key) and str(value)}


def _source_snippets_from_route_evidence_nodes(
    route_evidence_nodes: tuple[dict[str, object], ...],
) -> tuple[dict[str, object], ...]:
    snippets: list[dict[str, object]] = []
    for node in route_evidence_nodes:
        if str(node.get("kind", "")) != "source_ref":
            continue
        source_ref = str(node.get("source_ref", "")).strip()
        excerpt = str(node.get("excerpt", "")).strip()
        if not source_ref or not excerpt:
            continue
        rank = node.get("rank", 0)
        snippets.append(
            {
                "snippet_id": "route_evidence_source_snippet:"
                + stable_hash([node.get("node_id", ""), source_ref, excerpt])[:16],
                "source_ref": source_ref,
                "source_path": str(node.get("source_path", "")).strip(),
                "rank": rank if isinstance(rank, (int, float)) and not isinstance(rank, bool) else 0,
                "claim": str(node.get("label", "")).strip(),
                "excerpt": excerpt,
                "matched_terms": _str_tuple(node.get("matched_terms", [])),
                "matched_primitive_phrases": _str_tuple(
                    node.get("matched_primitive_phrases", [])
                ),
                "target_primitives": _str_tuple(node.get("target_primitives", [])),
                "evidence_role": str(
                    node.get("evidence_role", "source-backed informal route evidence")
                ).strip(),
            }
        )
    return tuple(snippets)


def _dict_tuple(values: Any) -> tuple[dict[str, object], ...]:
    if not isinstance(values, (list, tuple)):
        return tuple()
    return tuple(item for item in values if isinstance(item, dict))


def _dict_value(row: dict[str, Any], field_name: str) -> dict[str, object]:
    value = row.get(field_name, {})
    return dict(value) if isinstance(value, dict) else {}


def _merge_str_tuples(*values: tuple[str, ...]) -> tuple[str, ...]:
    merged: list[str] = []
    for items in values:
        merged.extend(items)
    return _str_tuple(merged)


def _merge_dict_tuples(
    *values: tuple[dict[str, object], ...],
) -> tuple[dict[str, object], ...]:
    rows: list[dict[str, object]] = []
    seen: set[str] = set()
    for items in values:
        for item in items:
            key = stable_hash(item)
            if key in seen:
                continue
            seen.add(key)
            rows.append(dict(item))
    return tuple(rows)


def _str_tuple(values: Any) -> tuple[str, ...]:
    if isinstance(values, str):
        return (values,) if values else tuple()
    if not isinstance(values, (list, tuple, set)):
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


def _read_response_jsonl(path: Path, errors: list[str]) -> tuple[list[dict[str, Any]], bool]:
    if not path.exists():
        return [], False
    rows: list[dict[str, Any]] = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            payload = json.loads(line)
        except Exception as exc:
            errors.append(f"failed to parse response line {line_no}: {type(exc).__name__}: {exc}")
            continue
        if not isinstance(payload, dict):
            errors.append(f"response line {line_no} is not an object")
            continue
        rows.append(payload)
    return rows, True


def _evidence_id(refinement_item_id: str, response: dict[str, Any] | None) -> str:
    return "formalization_gap_planner_refinement_evidence:" + stable_hash(
        [refinement_item_id, response or {}]
    )[:16]


def _prover_diagnostic_signature(
    attempt_status: str,
    diagnostics: tuple[str, ...],
    residual_goals: tuple[str, ...],
    route_revision_reasons: tuple[str, ...],
) -> str:
    if not attempt_status and not diagnostics and not residual_goals:
        return ""
    return "prover_diagnostic_signature:" + stable_hash(
        [
            attempt_status,
            tuple(item[:200] for item in diagnostics[:8]),
            tuple(item[:200] for item in residual_goals[:8]),
            tuple(item[:200] for item in route_revision_reasons[:8]),
        ]
    )[:16]


def _prover_attempt_class(attempt_status: str) -> str:
    return {
        "local_lean_scaffold_accepted": "target_prover_scaffold_accepted",
        "local_lean_failed": "target_prover_failed",
        "local_lean_unavailable": "target_prover_unavailable",
        "non_lean_skeleton": "non_target_prover_skeleton",
        "placeholder_blocked": "placeholder_blocked",
        "formal_gap_scaffold_blocked": "formal_gap_scaffold_blocked",
        "missing_theorem_skeleton": "missing_theorem_skeleton",
    }.get(attempt_status, attempt_status)


def _markdown_report(payload: dict[str, object]) -> str:
    lines = [
        "# Formalization Gap Planner Refinement Evidence",
        "",
        f"- Refinement items: {payload.get('n_refinement_items')}",
        f"- Responses: {payload.get('n_responses')}",
        f"- Response schema valid: {payload.get('n_response_schema_valid')}/{payload.get('n_responses')}",
        f"- Evidence row schema valid: {payload.get('n_evidence_row_schema_valid')}/{payload.get('n_evidence_rows')}",
        f"- Contract OK: {payload.get('n_contract_ok')}",
        f"- Awaiting tool response: {payload.get('n_awaiting_tool_response')}",
        f"- Source snippets: {payload.get('n_source_snippets')}",
        f"- Route revision recommended: {payload.get('n_route_revision_recommended')}",
        f"- Route revision proposals: {payload.get('n_route_revision_proposals')}",
        f"- Prover attempt statuses: {payload.get('by_prover_attempt_status')}",
        f"- Prover attempt classes: {payload.get('by_prover_attempt_class')}",
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
            f"- `{row.get('display_name')}` {row.get('hook_kind')} "
            f"status={row.get('acceptance_status')} "
            f"attempt={row.get('prover_attempt_status') or 'n/a'} "
            f"revision={row.get('route_revision_recommended')}"
        )
        if row.get("route_revision_reasons"):
            lines.append(
                "  revision reasons: "
                + ", ".join(str(item) for item in row.get("route_revision_reasons", [])[:6])
            )
    return "\n".join(lines) + "\n"
