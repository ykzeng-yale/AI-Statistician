from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping


ROUTE_ADOPTION_BLOCKER_TAXONOMY_SCHEMA_VERSION = 1
ROUTE_ADOPTION_BLOCKER_TAXONOMY_SCHEMA_ID = (
    "urn:ai-statistician:schemas:"
    "formalization-gap-planner-route-adoption-blocker-taxonomy:1"
)
ROUTE_ADOPTION_BLOCKER_TAXONOMY_ID = (
    "formalization_gap_planner_route_adoption_blocker_taxonomy:1"
)
ROUTE_ADOPTION_BLOCKER_TAXONOMY_COMPONENT = (
    "formalization_gap_planner_route_adoption_blocker_taxonomy"
)
ROUTE_ADOPTION_BLOCKER_TAXONOMY_PROOF_EVIDENCE_STATUS = (
    "FORMALIZATION_GAP_PLANNER_LLM_ROUTE_PLANNER_NOT_PROOF_EVIDENCE"
)
ROUTE_ADOPTION_BLOCKER_TAXONOMY_PROOF_EVIDENCE_BOUNDARY = (
    "Route-adoption blocker taxonomy artifacts define reusable planner "
    "readiness vocabulary only. They are not theorem proof evidence."
)
ROUTE_ADOPTION_BLOCKER_TAXONOMY_MANIFEST_SCHEMA_ID = (
    "urn:ai-statistician:schemas:"
    "formalization-gap-planner-route-adoption-blocker-taxonomy-manifest:1"
)
ROUTE_ADOPTION_BLOCKER_TAXONOMY_MANIFEST_SCHEMA_FILENAME = (
    "formalization_gap_planner_route_adoption_blocker_taxonomy_manifest.schema.json"
)
ROUTE_ADOPTION_BLOCKER_TAXONOMY_SCHEMA_FILENAME = (
    "formalization_gap_planner_route_adoption_blocker_taxonomy.schema.json"
)
ROUTE_ADOPTION_BLOCKER_TAXONOMY_FILENAME = (
    "formalization_gap_planner_route_adoption_blocker_taxonomy.json"
)
ROUTE_ADOPTION_BLOCKER_TAXONOMY_MANIFEST_FILENAME = (
    "formalization_gap_planner_route_adoption_blocker_taxonomy_manifest.json"
)

ROUTE_ADOPTION_READY_STATUS = "READY_FOR_STANDALONE_REPLAY"
ROUTE_ADOPTION_PENDING_STATUS = "PENDING_REFINEMENT_BEFORE_ROUTE_ADOPTION"
ROUTE_ADOPTION_AWAITING_STATUS = "AWAITING_LLM_ROUTE_PLANNER_RESPONSE"
ROUTE_ADOPTION_REJECTED_STATUS = "REJECTED_LLM_ROUTE_PLAN"
ROUTE_ADOPTION_STATUSES = (
    ROUTE_ADOPTION_READY_STATUS,
    ROUTE_ADOPTION_PENDING_STATUS,
    ROUTE_ADOPTION_AWAITING_STATUS,
    ROUTE_ADOPTION_REJECTED_STATUS,
)

ROUTE_ADOPTION_BLOCKER_RESPONSE_NOT_ACCEPTED = "response_not_accepted"
ROUTE_ADOPTION_BLOCKER_RESPONSE_MISSING = "llm_route_planner_response_missing"
ROUTE_ADOPTION_BLOCKER_SEARCH_REQUESTS = "search_requests_pending_evidence"
ROUTE_ADOPTION_BLOCKER_PLANNER_NEXT_ACTIONS = (
    "planner_next_actions_pending_evidence"
)
ROUTE_ADOPTION_BLOCKER_UNCERTAINTY_FLAGS = "uncertainty_flags_require_review"
ROUTE_ADOPTION_BLOCKER_SEMANTIC_ALIGNMENT_RISKS = (
    "semantic_alignment_risks_require_review"
)
ROUTE_ADOPTION_BLOCKER_RESIDUAL_INTERPRETATIONS = (
    "residual_interpretations_require_route_replay"
)
ROUTE_ADOPTION_BLOCKER_FEEDBACK_ACTIONS = (
    "feedback_summary_actions_pending_resolution"
)
ROUTE_ADOPTION_BLOCKER_RESOURCE_PLAYBOOK_REDISPATCH = (
    "resource_response_playbook_redispatch_pending"
)
ROUTE_ADOPTION_BLOCKER_RESOURCE_REQUEST_QUEUE = (
    "resource_request_queue_pending_response"
)
ROUTE_ADOPTION_BLOCKER_FEEDBACK_REPLAN = "feedback_loop_replan_required"
ROUTE_ADOPTION_BLOCKER_REALIZATION_COVERAGE = "realization_coverage_incomplete"
ROUTE_ADOPTION_BLOCKER_PRIMITIVE_EVIDENCE_MATRIX = (
    "primitive_evidence_matrix_incomplete"
)
ROUTE_ADOPTION_BLOCKER_OMITTED_COST_HINT_PRIMITIVES = (
    "omitted_cost_hint_primitives_require_review"
)
ROUTE_ADOPTION_BLOCKER_FORMAL_GAP_BOUNDARIES = (
    "formal_gap_boundaries_require_resolution"
)
ROUTE_ADOPTION_BLOCKER_SOURCE_GROUNDING = "source_grounding_obligations_pending"
ROUTE_ADOPTION_BLOCKER_QUALITY_CONTROLS = "quality_control_obligations_pending"

ROUTE_ADOPTION_BLOCKER_VALUES = (
    ROUTE_ADOPTION_BLOCKER_RESPONSE_NOT_ACCEPTED,
    ROUTE_ADOPTION_BLOCKER_RESPONSE_MISSING,
    ROUTE_ADOPTION_BLOCKER_SEARCH_REQUESTS,
    ROUTE_ADOPTION_BLOCKER_PLANNER_NEXT_ACTIONS,
    ROUTE_ADOPTION_BLOCKER_UNCERTAINTY_FLAGS,
    ROUTE_ADOPTION_BLOCKER_SEMANTIC_ALIGNMENT_RISKS,
    ROUTE_ADOPTION_BLOCKER_RESIDUAL_INTERPRETATIONS,
    ROUTE_ADOPTION_BLOCKER_FEEDBACK_ACTIONS,
    ROUTE_ADOPTION_BLOCKER_RESOURCE_PLAYBOOK_REDISPATCH,
    ROUTE_ADOPTION_BLOCKER_RESOURCE_REQUEST_QUEUE,
    ROUTE_ADOPTION_BLOCKER_FEEDBACK_REPLAN,
    ROUTE_ADOPTION_BLOCKER_REALIZATION_COVERAGE,
    ROUTE_ADOPTION_BLOCKER_PRIMITIVE_EVIDENCE_MATRIX,
    ROUTE_ADOPTION_BLOCKER_OMITTED_COST_HINT_PRIMITIVES,
    ROUTE_ADOPTION_BLOCKER_FORMAL_GAP_BOUNDARIES,
    ROUTE_ADOPTION_BLOCKER_SOURCE_GROUNDING,
    ROUTE_ADOPTION_BLOCKER_QUALITY_CONTROLS,
)

ROUTE_ADOPTION_BLOCKER_DEFINITIONS = {
    ROUTE_ADOPTION_BLOCKER_RESPONSE_NOT_ACCEPTED: (
        "The LLM route-planner response was rejected or failed response "
        "contract validation."
    ),
    ROUTE_ADOPTION_BLOCKER_RESPONSE_MISSING: (
        "The route has no LLM route-planner response yet."
    ),
    ROUTE_ADOPTION_BLOCKER_SEARCH_REQUESTS: (
        "The accepted route asks for additional literature, source, library, "
        "or prover search evidence before adoption."
    ),
    ROUTE_ADOPTION_BLOCKER_PLANNER_NEXT_ACTIONS: (
        "The accepted route carries unresolved planner next-action hooks."
    ),
    ROUTE_ADOPTION_BLOCKER_UNCERTAINTY_FLAGS: (
        "The accepted route carries uncertainty flags requiring review."
    ),
    ROUTE_ADOPTION_BLOCKER_SEMANTIC_ALIGNMENT_RISKS: (
        "The accepted route carries semantic-alignment risks requiring review."
    ),
    ROUTE_ADOPTION_BLOCKER_RESIDUAL_INTERPRETATIONS: (
        "The accepted route interpreted prover residual goals and must be "
        "replayed through route repair before standalone adoption."
    ),
    ROUTE_ADOPTION_BLOCKER_FEEDBACK_ACTIONS: (
        "The feedback-loop summary recommends unresolved follow-up actions."
    ),
    ROUTE_ADOPTION_BLOCKER_RESOURCE_PLAYBOOK_REDISPATCH: (
        "A resource response must be redispatched with its request playbook "
        "before the route can use it."
    ),
    ROUTE_ADOPTION_BLOCKER_RESOURCE_REQUEST_QUEUE: (
        "The resource request queue still has pending responses."
    ),
    ROUTE_ADOPTION_BLOCKER_FEEDBACK_REPLAN: (
        "The feedback loop explicitly requires route replanning."
    ),
    ROUTE_ADOPTION_BLOCKER_REALIZATION_COVERAGE: (
        "The formal-realization coverage witness is incomplete."
    ),
    ROUTE_ADOPTION_BLOCKER_PRIMITIVE_EVIDENCE_MATRIX: (
        "The selected route does not account for all request-side primitive "
        "evidence-matrix rows, or it selects a primitive with no corresponding "
        "matrix row."
    ),
    ROUTE_ADOPTION_BLOCKER_OMITTED_COST_HINT_PRIMITIVES: (
        "The selected route omits one or more primitives from the request-bound "
        "minimal-delta cost-hint baseline and needs review before standalone "
        "route adoption."
    ),
    ROUTE_ADOPTION_BLOCKER_FORMAL_GAP_BOUNDARIES: (
        "The accepted route carries explicit formal-gap boundaries that must be "
        "resolved, searched, or replayed before standalone adoption."
    ),
    ROUTE_ADOPTION_BLOCKER_SOURCE_GROUNDING: (
        "The request context contains source-grounding audit rows whose claims "
        "or prover residual repairs remain unaccounted, source-search pending, "
        "or explicitly failed."
    ),
    ROUTE_ADOPTION_BLOCKER_QUALITY_CONTROLS: (
        "The route carries quality-control obligations whose required gates, "
        "signals, or stop conditions have not been discharged by admissible "
        "resource-response or refinement evidence."
    ),
}

ROUTE_ADOPTION_BLOCKER_TRIGGER_FIELDS = {
    ROUTE_ADOPTION_BLOCKER_RESPONSE_NOT_ACCEPTED: (
        "request_errors",
        "provider_failure",
        "response_contract_ok",
    ),
    ROUTE_ADOPTION_BLOCKER_RESPONSE_MISSING: ("response_present",),
    ROUTE_ADOPTION_BLOCKER_SEARCH_REQUESTS: ("response_payload.search_requests",),
    ROUTE_ADOPTION_BLOCKER_PLANNER_NEXT_ACTIONS: (
        "response_payload.planner_next_actions",
    ),
    ROUTE_ADOPTION_BLOCKER_UNCERTAINTY_FLAGS: (
        "response_payload.uncertainty_flags",
    ),
    ROUTE_ADOPTION_BLOCKER_SEMANTIC_ALIGNMENT_RISKS: (
        "response_payload.semantic_alignment_risks",
    ),
    ROUTE_ADOPTION_BLOCKER_RESIDUAL_INTERPRETATIONS: (
        "response_payload.residual_interpretations",
    ),
    ROUTE_ADOPTION_BLOCKER_FEEDBACK_ACTIONS: (
        "context_packet.feedback_loop_summary.recommended_next_actions",
    ),
    ROUTE_ADOPTION_BLOCKER_RESOURCE_PLAYBOOK_REDISPATCH: (
        "context_packet.feedback_loop_summary.recommended_next_actions[].action",
    ),
    ROUTE_ADOPTION_BLOCKER_RESOURCE_REQUEST_QUEUE: (
        "context_packet.feedback_loop_summary.recommended_next_actions[].source",
    ),
    ROUTE_ADOPTION_BLOCKER_FEEDBACK_REPLAN: (
        "context_packet.feedback_loop_summary.replan_required",
    ),
    ROUTE_ADOPTION_BLOCKER_REALIZATION_COVERAGE: (
        "rows[].realization_coverage_witness.realization_coverage_complete",
        "context_packet.feedback_loop_summary.realization_coverage.complete",
    ),
    ROUTE_ADOPTION_BLOCKER_PRIMITIVE_EVIDENCE_MATRIX: (
        "rows[].primitive_evidence_matrix_witness.matrix_accounting_complete",
        "context_packet.route_planning_brief.primitive_evidence_matrix",
    ),
    ROUTE_ADOPTION_BLOCKER_OMITTED_COST_HINT_PRIMITIVES: (
        "rows[].realization_coverage_witness.omitted_cost_hint_primitives",
        "context_packet.minimal_delta_cost_hints.route_option_hints",
    ),
    ROUTE_ADOPTION_BLOCKER_FORMAL_GAP_BOUNDARIES: (
        "response_payload.informal_knowledge_dag_nodes[].formal_gap_boundary",
        "response_payload.formal_realization_dag_nodes[].formal_gap_boundary",
        "response_payload.residual_interpretations[].formal_gap_boundary",
        "response_payload.standalone_route.primitives[].formal_gap_boundary",
    ),
    ROUTE_ADOPTION_BLOCKER_SOURCE_GROUNDING: (
        "context_packet.source_grounding_obligations.pending",
        "context_packet.source_grounding_rows[].grounding_status",
        "context_packet.source_grounding_rows[].ok",
    ),
    ROUTE_ADOPTION_BLOCKER_QUALITY_CONTROLS: (
        "context_packet.quality_control_obligations.pending",
        "context_packet.context_packet_inventory.pending_quality_control_value_count",
    ),
}


def _str_tuple(values: Any) -> tuple[str, ...]:
    if not isinstance(values, (list, tuple)):
        return tuple()
    return tuple(str(value) for value in values)


def route_adoption_blocker_array_json_schema() -> dict[str, object]:
    return {
        "type": "array",
        "items": {
            "type": "string",
            "enum": list(ROUTE_ADOPTION_BLOCKER_VALUES),
        },
    }


def route_adoption_blocker_taxonomy_json_schema() -> dict[str, object]:
    string_array = {"type": "array", "items": {"type": "string"}}
    trigger_field_properties = {
        blocker: {
            "type": "array",
            "items": {"type": "string"},
            "const": list(fields),
        }
        for blocker, fields in ROUTE_ADOPTION_BLOCKER_TRIGGER_FIELDS.items()
    }
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": ROUTE_ADOPTION_BLOCKER_TAXONOMY_SCHEMA_ID,
        "title": "Formalization Gap Planner Route Adoption Blocker Taxonomy",
        "description": (
            "Portable vocabulary for explaining why an LLM route-planner row "
            "is not yet ready for standalone route replay."
        ),
        "type": "object",
        "additionalProperties": False,
        "required": [
            "schema_version",
            "schema_id",
            "component_name",
            "taxonomy_id",
            "status_values",
            "blocker_values",
            "blocker_definitions",
            "blocker_trigger_fields",
            "proof_evidence_status",
            "proof_evidence_boundary",
            "all_ok",
            "errors",
        ],
        "properties": {
            "schema_version": {
                "type": "integer",
                "const": ROUTE_ADOPTION_BLOCKER_TAXONOMY_SCHEMA_VERSION,
            },
            "schema_id": {"const": ROUTE_ADOPTION_BLOCKER_TAXONOMY_SCHEMA_ID},
            "component_name": {"const": ROUTE_ADOPTION_BLOCKER_TAXONOMY_COMPONENT},
            "taxonomy_id": {"const": ROUTE_ADOPTION_BLOCKER_TAXONOMY_ID},
            "status_values": {
                "type": "array",
                "items": {"type": "string", "enum": list(ROUTE_ADOPTION_STATUSES)},
            },
            "blocker_values": route_adoption_blocker_array_json_schema(),
            "blocker_definitions": {
                "type": "object",
                "additionalProperties": {"type": "string"},
            },
            "blocker_trigger_fields": {
                "type": "object",
                "additionalProperties": False,
                "required": list(ROUTE_ADOPTION_BLOCKER_VALUES),
                "properties": trigger_field_properties,
            },
            "proof_evidence_status": {
                "const": ROUTE_ADOPTION_BLOCKER_TAXONOMY_PROOF_EVIDENCE_STATUS
            },
            "proof_evidence_boundary": {
                "type": "string",
                "pattern": "not theorem proof evidence",
            },
            "all_ok": {"type": "boolean"},
            "errors": string_array,
        },
    }


def route_adoption_blocker_taxonomy_payload() -> dict[str, object]:
    return {
        "schema_version": ROUTE_ADOPTION_BLOCKER_TAXONOMY_SCHEMA_VERSION,
        "schema_id": ROUTE_ADOPTION_BLOCKER_TAXONOMY_SCHEMA_ID,
        "component_name": ROUTE_ADOPTION_BLOCKER_TAXONOMY_COMPONENT,
        "taxonomy_id": ROUTE_ADOPTION_BLOCKER_TAXONOMY_ID,
        "status_values": list(ROUTE_ADOPTION_STATUSES),
        "blocker_values": list(ROUTE_ADOPTION_BLOCKER_VALUES),
        "blocker_definitions": dict(ROUTE_ADOPTION_BLOCKER_DEFINITIONS),
        "blocker_trigger_fields": {
            blocker: list(fields)
            for blocker, fields in ROUTE_ADOPTION_BLOCKER_TRIGGER_FIELDS.items()
        },
        "proof_evidence_status": ROUTE_ADOPTION_BLOCKER_TAXONOMY_PROOF_EVIDENCE_STATUS,
        "proof_evidence_boundary": (
            ROUTE_ADOPTION_BLOCKER_TAXONOMY_PROOF_EVIDENCE_BOUNDARY
        ),
        "all_ok": True,
        "errors": [],
    }


def route_adoption_blocker_taxonomy_manifest_json_schema() -> dict[str, object]:
    string_array = {"type": "array", "items": {"type": "string"}}
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": ROUTE_ADOPTION_BLOCKER_TAXONOMY_MANIFEST_SCHEMA_ID,
        "title": "Formalization Gap Planner Route Adoption Blocker Taxonomy Manifest",
        "description": (
            "Manifest schema for the standalone route-adoption blocker taxonomy "
            "export command."
        ),
        "type": "object",
        "additionalProperties": False,
        "required": [
            "schema_version",
            "schema_id",
            "created_at",
            "component_name",
            "taxonomy_id",
            "taxonomy_schema_id",
            "taxonomy_manifest_schema_id",
            "manifest_schema_path",
            "taxonomy_schema_path",
            "taxonomy_path",
            "n_status_values",
            "n_blocker_values",
            "status_values",
            "blocker_values",
            "proof_evidence_status",
            "proof_evidence_boundary",
            "taxonomy_payload_errors",
            "all_ok",
            "errors",
        ],
        "properties": {
            "schema_version": {
                "type": "integer",
                "const": ROUTE_ADOPTION_BLOCKER_TAXONOMY_SCHEMA_VERSION,
            },
            "schema_id": {
                "const": ROUTE_ADOPTION_BLOCKER_TAXONOMY_MANIFEST_SCHEMA_ID
            },
            "created_at": {"type": "string", "minLength": 1},
            "component_name": {"const": ROUTE_ADOPTION_BLOCKER_TAXONOMY_COMPONENT},
            "taxonomy_id": {"const": ROUTE_ADOPTION_BLOCKER_TAXONOMY_ID},
            "taxonomy_schema_id": {
                "const": ROUTE_ADOPTION_BLOCKER_TAXONOMY_SCHEMA_ID
            },
            "taxonomy_manifest_schema_id": {
                "const": ROUTE_ADOPTION_BLOCKER_TAXONOMY_MANIFEST_SCHEMA_ID
            },
            "manifest_schema_path": {"type": "string", "minLength": 1},
            "taxonomy_schema_path": {"type": "string", "minLength": 1},
            "taxonomy_path": {"type": "string", "minLength": 1},
            "n_status_values": {
                "type": "integer",
                "const": len(ROUTE_ADOPTION_STATUSES),
            },
            "n_blocker_values": {
                "type": "integer",
                "const": len(ROUTE_ADOPTION_BLOCKER_VALUES),
            },
            "status_values": {
                "type": "array",
                "items": {"type": "string", "enum": list(ROUTE_ADOPTION_STATUSES)},
            },
            "blocker_values": route_adoption_blocker_array_json_schema(),
            "proof_evidence_status": {
                "const": ROUTE_ADOPTION_BLOCKER_TAXONOMY_PROOF_EVIDENCE_STATUS
            },
            "proof_evidence_boundary": {
                "type": "string",
                "pattern": "not theorem proof evidence",
            },
            "taxonomy_payload_errors": string_array,
            "all_ok": {"type": "boolean"},
            "errors": string_array,
        },
    }


def export_route_adoption_blocker_taxonomy(out_dir: Path | str) -> dict[str, object]:
    """Write the portable route-adoption blocker taxonomy contract artifacts."""

    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    schema = route_adoption_blocker_taxonomy_json_schema()
    payload = route_adoption_blocker_taxonomy_payload()
    manifest_schema = route_adoption_blocker_taxonomy_manifest_json_schema()
    validation_errors = validate_route_adoption_blocker_taxonomy_payload(payload)
    schema_path = out_path / ROUTE_ADOPTION_BLOCKER_TAXONOMY_SCHEMA_FILENAME
    taxonomy_path = out_path / ROUTE_ADOPTION_BLOCKER_TAXONOMY_FILENAME
    manifest_schema_path = (
        out_path / ROUTE_ADOPTION_BLOCKER_TAXONOMY_MANIFEST_SCHEMA_FILENAME
    )
    manifest_path = out_path / ROUTE_ADOPTION_BLOCKER_TAXONOMY_MANIFEST_FILENAME
    schema_path.write_text(json.dumps(schema, indent=2), encoding="utf-8")
    taxonomy_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    manifest_schema_path.write_text(
        json.dumps(manifest_schema, indent=2),
        encoding="utf-8",
    )
    manifest: dict[str, object] = {
        "schema_version": ROUTE_ADOPTION_BLOCKER_TAXONOMY_SCHEMA_VERSION,
        "schema_id": ROUTE_ADOPTION_BLOCKER_TAXONOMY_MANIFEST_SCHEMA_ID,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "component_name": ROUTE_ADOPTION_BLOCKER_TAXONOMY_COMPONENT,
        "taxonomy_id": ROUTE_ADOPTION_BLOCKER_TAXONOMY_ID,
        "taxonomy_schema_id": ROUTE_ADOPTION_BLOCKER_TAXONOMY_SCHEMA_ID,
        "taxonomy_manifest_schema_id": (
            ROUTE_ADOPTION_BLOCKER_TAXONOMY_MANIFEST_SCHEMA_ID
        ),
        "manifest_schema_path": str(manifest_schema_path),
        "taxonomy_schema_path": str(schema_path),
        "taxonomy_path": str(taxonomy_path),
        "n_status_values": len(ROUTE_ADOPTION_STATUSES),
        "n_blocker_values": len(ROUTE_ADOPTION_BLOCKER_VALUES),
        "status_values": list(ROUTE_ADOPTION_STATUSES),
        "blocker_values": list(ROUTE_ADOPTION_BLOCKER_VALUES),
        "proof_evidence_status": (
            ROUTE_ADOPTION_BLOCKER_TAXONOMY_PROOF_EVIDENCE_STATUS
        ),
        "proof_evidence_boundary": (
            ROUTE_ADOPTION_BLOCKER_TAXONOMY_PROOF_EVIDENCE_BOUNDARY
        ),
        "taxonomy_payload_errors": list(validation_errors),
        "all_ok": not validation_errors,
        "errors": list(validation_errors),
    }
    manifest_validation_errors = (
        validate_route_adoption_blocker_taxonomy_manifest_payload(manifest)
    )
    if manifest_validation_errors:
        errors = sorted(set((*validation_errors, *manifest_validation_errors)))
        manifest["all_ok"] = False
        manifest["errors"] = errors
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


def validate_route_adoption_blocker_taxonomy_manifest_payload(
    payload: Mapping[str, Any],
) -> tuple[str, ...]:
    errors: list[str] = []
    required = route_adoption_blocker_taxonomy_manifest_json_schema().get(
        "required",
        [],
    )
    if isinstance(required, list):
        for field_name in required:
            if isinstance(field_name, str) and field_name not in payload:
                errors.append(f"{field_name} required")
    if payload.get("schema_version") != ROUTE_ADOPTION_BLOCKER_TAXONOMY_SCHEMA_VERSION:
        errors.append("schema_version mismatch")
    if payload.get("schema_id") != ROUTE_ADOPTION_BLOCKER_TAXONOMY_MANIFEST_SCHEMA_ID:
        errors.append("schema_id mismatch")
    if payload.get("component_name") != ROUTE_ADOPTION_BLOCKER_TAXONOMY_COMPONENT:
        errors.append("component_name mismatch")
    if payload.get("taxonomy_id") != ROUTE_ADOPTION_BLOCKER_TAXONOMY_ID:
        errors.append("taxonomy_id mismatch")
    if payload.get("taxonomy_schema_id") != ROUTE_ADOPTION_BLOCKER_TAXONOMY_SCHEMA_ID:
        errors.append("taxonomy_schema_id mismatch")
    if (
        payload.get("taxonomy_manifest_schema_id")
        != ROUTE_ADOPTION_BLOCKER_TAXONOMY_MANIFEST_SCHEMA_ID
    ):
        errors.append("taxonomy_manifest_schema_id mismatch")
    for path_field in (
        "manifest_schema_path",
        "taxonomy_schema_path",
        "taxonomy_path",
    ):
        if not str(payload.get(path_field, "") or "").strip():
            errors.append(f"{path_field} required")
    if int(payload.get("n_status_values", -1) or -1) != len(
        ROUTE_ADOPTION_STATUSES
    ):
        errors.append("n_status_values mismatch")
    if int(payload.get("n_blocker_values", -1) or -1) != len(
        ROUTE_ADOPTION_BLOCKER_VALUES
    ):
        errors.append("n_blocker_values mismatch")
    if _str_tuple(payload.get("status_values", [])) != ROUTE_ADOPTION_STATUSES:
        errors.append("status_values must match route adoption status constants")
    if _str_tuple(payload.get("blocker_values", [])) != ROUTE_ADOPTION_BLOCKER_VALUES:
        errors.append("blocker_values must match route adoption blocker constants")
    if (
        payload.get("proof_evidence_status")
        != ROUTE_ADOPTION_BLOCKER_TAXONOMY_PROOF_EVIDENCE_STATUS
    ):
        errors.append("proof_evidence_status mismatch")
    if "not theorem proof evidence" not in str(
        payload.get("proof_evidence_boundary", "")
    ).lower():
        errors.append("proof_evidence_boundary must say not theorem proof evidence")
    taxonomy_payload_errors = payload.get("taxonomy_payload_errors", [])
    if not isinstance(taxonomy_payload_errors, list):
        errors.append("taxonomy_payload_errors must be array")
    payload_errors = payload.get("errors", [])
    if not isinstance(payload_errors, list):
        errors.append("errors must be array")
    if payload.get("all_ok") is True:
        if payload_errors not in ([], None):
            errors.append("all_ok manifest payload must not carry errors")
        if taxonomy_payload_errors not in ([], None):
            errors.append("all_ok manifest payload must not carry taxonomy errors")
    if payload.get("all_ok") is False and not payload_errors:
        errors.append("non-ok manifest payload must carry errors")
    return tuple(errors)


def validate_route_adoption_blocker_taxonomy_payload(
    payload: Mapping[str, Any],
) -> tuple[str, ...]:
    errors: list[str] = []
    required = route_adoption_blocker_taxonomy_json_schema().get("required", [])
    if isinstance(required, list):
        for field_name in required:
            if isinstance(field_name, str) and field_name not in payload:
                errors.append(f"{field_name} required")
    if payload.get("schema_version") != ROUTE_ADOPTION_BLOCKER_TAXONOMY_SCHEMA_VERSION:
        errors.append("schema_version mismatch")
    if payload.get("schema_id") != ROUTE_ADOPTION_BLOCKER_TAXONOMY_SCHEMA_ID:
        errors.append("schema_id mismatch")
    if payload.get("component_name") != ROUTE_ADOPTION_BLOCKER_TAXONOMY_COMPONENT:
        errors.append("component_name mismatch")
    if payload.get("taxonomy_id") != ROUTE_ADOPTION_BLOCKER_TAXONOMY_ID:
        errors.append("taxonomy_id mismatch")
    if _str_tuple(payload.get("status_values", [])) != ROUTE_ADOPTION_STATUSES:
        errors.append("status_values must match route adoption status constants")
    if _str_tuple(payload.get("blocker_values", [])) != ROUTE_ADOPTION_BLOCKER_VALUES:
        errors.append("blocker_values must match route adoption blocker constants")
    definitions = payload.get("blocker_definitions", {})
    if not isinstance(definitions, Mapping):
        errors.append("blocker_definitions must be object")
    else:
        definition_keys = tuple(str(key) for key in definitions.keys())
        if set(definition_keys) != set(ROUTE_ADOPTION_BLOCKER_VALUES):
            errors.append("blocker_definitions keys must match blocker_values")
        empty_definitions = [
            key
            for key, value in definitions.items()
            if not isinstance(value, str) or not value.strip()
        ]
        if empty_definitions:
            errors.append(
                "blocker_definitions must be non-empty strings for: "
                + ", ".join(sorted(str(key) for key in empty_definitions))
            )
    trigger_fields = payload.get("blocker_trigger_fields", {})
    if not isinstance(trigger_fields, Mapping):
        errors.append("blocker_trigger_fields must be object")
    else:
        trigger_keys = tuple(str(key) for key in trigger_fields.keys())
        if set(trigger_keys) != set(ROUTE_ADOPTION_BLOCKER_VALUES):
            errors.append("blocker_trigger_fields keys must match blocker_values")
        empty_trigger_fields = [
            key
            for key, values in trigger_fields.items()
            if not _str_tuple(values)
        ]
        if empty_trigger_fields:
            errors.append(
                "blocker_trigger_fields must list at least one trigger field for: "
                + ", ".join(sorted(str(key) for key in empty_trigger_fields))
            )
        mismatched_trigger_fields = [
            blocker
            for blocker, expected in ROUTE_ADOPTION_BLOCKER_TRIGGER_FIELDS.items()
            if _str_tuple(trigger_fields.get(blocker, [])) != tuple(expected)
        ]
        if mismatched_trigger_fields:
            errors.append(
                "blocker_trigger_fields values must match route adoption "
                "blocker trigger constants for: "
                + ", ".join(sorted(mismatched_trigger_fields))
            )
    if (
        payload.get("proof_evidence_status")
        != ROUTE_ADOPTION_BLOCKER_TAXONOMY_PROOF_EVIDENCE_STATUS
    ):
        errors.append("proof_evidence_status mismatch")
    if "not theorem proof evidence" not in str(
        payload.get("proof_evidence_boundary", "")
    ).lower():
        errors.append("proof_evidence_boundary must say not theorem proof evidence")
    payload_errors = payload.get("errors", [])
    if payload.get("all_ok") is True and payload_errors not in ([], (), None):
        errors.append("all_ok taxonomy payload must not carry errors")
    if payload.get("all_ok") is False and not payload_errors:
        errors.append("non-ok taxonomy payload must carry errors")
    return tuple(errors)
