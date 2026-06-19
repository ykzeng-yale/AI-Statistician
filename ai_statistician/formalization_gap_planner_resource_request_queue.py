from __future__ import annotations

import json
import re
from collections import Counter
from collections.abc import Iterable
from dataclasses import asdict, dataclass, replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .fingerprint import stable_hash
from .formalization_gap_planner_action_resource_plan import (
    ACTION_RESOURCE_PLAN_ROW_SCHEMA_ID,
    FORMALIZATION_GAP_PLANNER_ACTION_RESOURCE_PLAN_SCHEMA_VERSION,
    PROOF_EVIDENCE_BOUNDARY as ACTION_RESOURCE_PROOF_EVIDENCE_BOUNDARY,
    PROOF_EVIDENCE_STATUS as ACTION_RESOURCE_PROOF_EVIDENCE_STATUS,
    validate_action_resource_plan_row,
)
from .formalization_gap_planner_target_summary import target_prover_family_summary


FORMALIZATION_GAP_PLANNER_RESOURCE_REQUEST_QUEUE_SCHEMA_VERSION = 6
RESOURCE_REQUEST_QUEUE_ROW_SCHEMA_ID = (
    "urn:ai-statistician:schemas:"
    "formalization-gap-planner-resource-request-queue-row:6"
)
PROOF_EVIDENCE_STATUS = (
    "FORMALIZATION_GAP_PLANNER_RESOURCE_REQUEST_QUEUE_NOT_PROOF_EVIDENCE"
)
PROOF_EVIDENCE_BOUNDARY = (
    "Formalization gap planner resource-request queue rows are executable "
    "dispatch packets for local-first resources, frontier MCP or CLI tools, "
    "and prover feedback adapters. They record what evidence should be "
    "requested and how responses should be accepted, but they are not "
    "theorem proof evidence."
)
REQUEST_PHASES = ("local_first", "frontier_escalation")


@dataclass(frozen=True)
class FormalizationGapPlannerResourceRequestQueueRow:
    schema_version: int
    resource_request_id: str
    action_resource_plan_id: str
    primitive_action_id: str
    coverage_map_id: str
    goal_plan_id: str
    route_id: str
    display_name: str
    primitive: str
    target_primitives: tuple[str, ...]
    actionable_work_items: tuple[str, ...]
    coverage_bucket: str
    queue_action_kind: str
    priority_score: int
    minimal_delta_cost_score: int
    reuse_readiness_score: int
    evidence_readiness_score: int
    priority_rationale: tuple[str, ...]
    target_prover_family: str
    library_snapshot_ref: str
    candidate_declaration_rows: tuple[dict[str, object], ...]
    request_phase: str
    request_rank: int
    component_ids: tuple[str, ...]
    resource_id: str
    resource_contract_ids: tuple[str, ...]
    request_contract_fields: tuple[str, ...]
    response_contract_fields: tuple[str, ...]
    request_playbook: dict[str, object]
    request_payload: dict[str, object]
    expected_response_artifact: str
    acceptance_gate: str
    escalation_triggers: tuple[str, ...]
    stop_conditions: tuple[str, ...]
    execution_command: str
    mcp_or_cli_hint: str
    dispatch_spec: dict[str, object]
    proof_evidence_status: str
    proof_evidence_boundary: str
    ok: bool
    errors: tuple[str, ...] = ()


def export_formalization_gap_planner_resource_request_queue(
    formalization_gap_planner_action_resource_plan_dir: Path,
    out_dir: Path | None = None,
    *,
    formalization_gap_planner_llm_route_planner_dir: Path | None = None,
) -> dict[str, object]:
    """Export executable resource requests from action-resource plans."""

    errors: list[str] = []
    action_resource_plan_dir = formalization_gap_planner_action_resource_plan_dir
    action_manifest_path = (
        action_resource_plan_dir
        / "formalization_gap_planner_action_resource_plan_manifest.json"
    )
    action_manifest = _read_json(action_manifest_path, errors)
    if action_manifest.get("component_name") != (
        "formalization_gap_planner_action_resource_plan"
    ):
        errors.append("input manifest is not the action-resource plan component")
    if action_manifest.get("action_resource_plan_row_schema", {}).get(
        "$id"
    ) != ACTION_RESOURCE_PLAN_ROW_SCHEMA_ID:
        errors.append("input manifest action-resource plan row schema id mismatch")

    action_rows = [
        row for row in action_manifest.get("rows", []) if isinstance(row, dict)
    ]
    action_resource_request_rows = tuple(
        request_row
        for action_row in action_rows
        for request_row in _resource_request_rows(action_row)
    )
    llm_manifest: dict[str, Any] = {}
    llm_route_planner_rows: tuple[dict[str, Any], ...] = tuple()
    llm_request_packets: tuple[dict[str, Any], ...] = tuple()
    llm_resource_request_rows: tuple[
        FormalizationGapPlannerResourceRequestQueueRow, ...
    ] = tuple()
    llm_route_planning_brief_resource_request_rows: tuple[
        FormalizationGapPlannerResourceRequestQueueRow, ...
    ] = tuple()
    llm_route_planner_manifest_path = None
    if formalization_gap_planner_llm_route_planner_dir is not None:
        llm_route_planner_manifest_path = (
            formalization_gap_planner_llm_route_planner_dir
            / "formalization_gap_planner_llm_route_planner_manifest.json"
        )
        llm_manifest = _read_json(llm_route_planner_manifest_path, errors)
        if llm_manifest.get("component_name") != (
            "formalization_gap_planner_llm_route_planner"
        ):
            errors.append("input manifest is not the LLM route-planner component")
        llm_route_planner_rows = tuple(
            row for row in llm_manifest.get("rows", []) if isinstance(row, dict)
        )
        llm_request_packets = tuple(
            packet
            for packet in llm_manifest.get("request_packets", [])
            if isinstance(packet, dict)
        )
        llm_resource_request_rows = _llm_route_planner_resource_request_rows(
            llm_route_planner_rows,
            fallback_target_prover_family=str(
                action_manifest.get("target_prover_family", "")
            ),
            fallback_library_snapshot_ref=str(
                action_manifest.get("library_snapshot_ref", "")
            ),
        )
        llm_route_planning_brief_resource_request_rows = (
            _llm_route_planner_route_planning_brief_resource_request_rows(
                llm_request_packets,
                fallback_target_prover_family=str(
                    action_manifest.get("target_prover_family", "")
                ),
                fallback_library_snapshot_ref=str(
                    action_manifest.get("library_snapshot_ref", "")
                ),
            )
        )
    all_llm_resource_request_rows = (
        *llm_resource_request_rows,
        *llm_route_planning_brief_resource_request_rows,
    )
    rows = (*action_resource_request_rows, *all_llm_resource_request_rows)
    row_dicts = [asdict(row) for row in rows]
    row_schema = resource_request_queue_row_json_schema()
    row_schema_errors = [
        validate_resource_request_queue_row(row, row_schema) for row in row_dicts
    ]
    n_row_schema_valid = sum(1 for row_errors in row_schema_errors if not row_errors)
    n_row_schema_invalid = len(row_schema_errors) - n_row_schema_valid
    by_request_phase = Counter(row.request_phase for row in rows)
    by_action_kind = Counter(row.queue_action_kind for row in rows)
    by_resource_id = Counter(row.resource_id for row in rows)
    target_summary = target_prover_family_summary(
        rows,
        fallback_target_prover_family=action_manifest.get("target_prover_family", ""),
    )
    n_self_contained_request_payloads = sum(
        1 for row in row_dicts if not _request_payload_identity_errors(row)
    )
    n_dispatch_spec_identity_valid = sum(
        1 for row in row_dicts if not _dispatch_spec_identity_errors(row)
    )
    n_request_playbook_identity_valid = sum(
        1 for row in row_dicts if not _request_playbook_identity_errors(row)
    )
    source_components = [str(action_manifest.get("component_name", ""))]
    if llm_manifest:
        source_components.append(str(llm_manifest.get("component_name", "")))
    payload: dict[str, object] = {
        "schema_version": (
            FORMALIZATION_GAP_PLANNER_RESOURCE_REQUEST_QUEUE_SCHEMA_VERSION
        ),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "component_name": "formalization_gap_planner_resource_request_queue",
        "source_components": tuple(
            dict.fromkeys(component for component in source_components if component)
        ),
        "action_resource_plan_dir": str(action_resource_plan_dir),
        "action_resource_plan_manifest": str(action_manifest_path),
        "llm_route_planner_dir": (
            str(formalization_gap_planner_llm_route_planner_dir)
            if formalization_gap_planner_llm_route_planner_dir is not None
            else ""
        ),
        "llm_route_planner_manifest": (
            str(llm_route_planner_manifest_path)
            if llm_route_planner_manifest_path is not None
            else ""
        ),
        "target_prover_family": target_summary["target_prover_family"],
        "n_target_prover_families": target_summary["n_target_prover_families"],
        "by_target_prover_family": target_summary["by_target_prover_family"],
        "library_snapshot_ref": str(action_manifest.get("library_snapshot_ref", "")),
        "n_action_resource_plan_rows": len(action_rows),
        "n_action_resource_plan_resource_request_rows": len(
            action_resource_request_rows
        ),
        "n_llm_route_planner_rows": len(llm_route_planner_rows),
        "n_llm_route_planner_request_packets": len(llm_request_packets),
        "n_llm_route_planner_request_route_planning_briefs": sum(
            1
            for packet in llm_request_packets
            if _route_planning_brief_from_request_packet(packet)
        ),
        "n_llm_route_planner_route_planning_brief_evidence_gaps": sum(
            len(
                _dict_tuple(
                    _route_planning_brief_from_request_packet(packet).get(
                        "evidence_gaps",
                        [],
                    )
                )
            )
            for packet in llm_request_packets
        ),
        "n_llm_route_planner_rows_with_search_requests": sum(
            1 for row in llm_route_planner_rows if _dict_tuple(row.get("search_requests", []))
        ),
        "n_llm_route_planner_rows_with_planner_next_actions": sum(
            1
            for row in llm_route_planner_rows
            if _dict_tuple(row.get("planner_next_actions", []))
        ),
        "n_llm_route_planner_rows_with_residual_interpretations": sum(
            1
            for row in llm_route_planner_rows
            if _dict_tuple(row.get("residual_interpretations", []))
        ),
        "n_llm_route_planner_search_requests": sum(
            len(_dict_tuple(row.get("search_requests", [])))
            for row in llm_route_planner_rows
        ),
        "n_llm_route_planner_planner_next_actions": sum(
            len(_dict_tuple(row.get("planner_next_actions", [])))
            for row in llm_route_planner_rows
        ),
        "n_llm_route_planner_residual_interpretations": sum(
            len(_dict_tuple(row.get("residual_interpretations", [])))
            for row in llm_route_planner_rows
        ),
        "n_llm_route_planner_rows_with_formal_attempt_queue": sum(
            1
            for row in llm_route_planner_rows
            if _dict_tuple(row.get("formal_attempt_queue", []))
        ),
        "n_llm_route_planner_formal_attempt_queue_items": sum(
            len(_dict_tuple(row.get("formal_attempt_queue", [])))
            for row in llm_route_planner_rows
        ),
        "n_llm_route_planner_formal_attempt_queue_ready_items": sum(
            len(_llm_formal_attempt_queue_source_items(row))
            for row in llm_route_planner_rows
        ),
        "n_llm_route_planner_formal_attempt_queue_waiting_items": sum(
            len(
                _llm_formal_attempt_queue_items_by_schedule_status(
                    row,
                    status="waiting_for_formal_prerequisite_attempts",
                )
            )
            for row in llm_route_planner_rows
        ),
        "n_llm_route_planner_formal_attempt_queue_missing_prerequisite_items": sum(
            len(
                _llm_formal_attempt_queue_items_by_schedule_status(
                    row,
                    status="missing_prerequisite_attempts",
                )
            )
            for row in llm_route_planner_rows
        ),
        "n_llm_route_planner_rows_with_route_adoption_preconditions": sum(
            1 for row in llm_route_planner_rows if _llm_route_adoption_preconditions(row)
        ),
        "n_llm_route_planner_route_adoption_precondition_known_blockers": sum(
            _route_adoption_precondition_known_blocker_count(
                _llm_route_adoption_preconditions(row)
            )
            for row in llm_route_planner_rows
        ),
        "n_llm_route_planner_route_adoption_precondition_required_response_fields": sum(
            _route_adoption_precondition_required_response_field_count(
                _llm_route_adoption_preconditions(row)
            )
            for row in llm_route_planner_rows
        ),
        "n_llm_route_planner_route_adoption_precondition_target_primitives": sum(
            _route_adoption_precondition_target_primitive_count(
                _llm_route_adoption_preconditions(row)
            )
            for row in llm_route_planner_rows
        ),
        "n_llm_route_planner_resource_request_rows": len(llm_resource_request_rows),
        "n_llm_route_planner_route_planning_brief_resource_request_rows": len(
            llm_route_planning_brief_resource_request_rows
        ),
        "n_llm_route_planner_total_resource_request_rows": len(
            all_llm_resource_request_rows
        ),
        "n_llm_route_planner_resource_request_rows_with_route_adoption_preconditions": sum(
            1
            for row in all_llm_resource_request_rows
            if _llm_request_payload_route_adoption_preconditions(row.request_payload)
        ),
        "n_llm_route_planner_resource_request_route_adoption_precondition_target_primitives": sum(
            _route_adoption_precondition_target_primitive_count(
                _llm_request_payload_route_adoption_preconditions(row.request_payload)
            )
            for row in all_llm_resource_request_rows
        ),
        "n_llm_route_planner_search_request_rows": sum(
            1
            for row in all_llm_resource_request_rows
            if row.request_payload.get("llm_route_planner_source_kind")
            == "search_request"
        ),
        "n_llm_route_planner_planner_next_action_rows": sum(
            1
            for row in all_llm_resource_request_rows
            if row.request_payload.get("llm_route_planner_source_kind")
            == "planner_next_action"
        ),
        "n_llm_route_planner_residual_interpretation_rows": sum(
            1
            for row in all_llm_resource_request_rows
            if row.request_payload.get("llm_route_planner_source_kind")
            == "residual_interpretation"
        ),
        "n_llm_route_planner_formal_attempt_queue_resource_request_rows": sum(
            1
            for row in all_llm_resource_request_rows
            if row.request_payload.get("llm_route_planner_source_kind")
            == "formal_attempt_queue"
        ),
        "n_llm_route_planner_route_planning_brief_evidence_gap_rows": sum(
            1
            for row in all_llm_resource_request_rows
            if row.request_payload.get("llm_route_planner_source_kind")
            == "route_planning_brief_evidence_gap"
        ),
        "n_resource_request_rows": len(rows),
        "n_ok": sum(1 for row in rows if row.ok),
        "n_failed": sum(1 for row in rows if not row.ok),
        "n_local_first_requests": by_request_phase.get("local_first", 0),
        "n_frontier_escalation_requests": by_request_phase.get(
            "frontier_escalation",
            0,
        ),
        "n_distinct_resources": len(by_resource_id),
        "n_with_mcp_or_cli_hint": sum(1 for row in rows if row.mcp_or_cli_hint),
        "n_with_dispatch_specs": sum(1 for row in rows if row.dispatch_spec),
        "n_with_request_playbooks": sum(1 for row in rows if row.request_playbook),
        "n_with_candidate_declaration_rows": sum(
            1 for row in rows if row.candidate_declaration_rows
        ),
        "n_candidate_declaration_rows": sum(
            len(row.candidate_declaration_rows) for row in rows
        ),
        "n_with_actionable_work_items": sum(
            1 for row in rows if row.actionable_work_items
        ),
        "n_actionable_work_items": sum(len(row.actionable_work_items) for row in rows),
        "n_minimal_delta_reuse_ready": sum(
            1 for row in rows if row.minimal_delta_cost_score <= 15
        ),
        "n_minimal_delta_light_bridge_or_wrapper": sum(
            1 for row in rows if 15 < row.minimal_delta_cost_score <= 45
        ),
        "n_minimal_delta_source_or_new_theory": sum(
            1 for row in rows if 45 < row.minimal_delta_cost_score < 100
        ),
        "n_minimal_delta_alignment_blocked": sum(
            1 for row in rows if row.minimal_delta_cost_score >= 100
        ),
        "average_reuse_readiness_score": _average_int(
            row.reuse_readiness_score for row in rows
        ),
        "average_evidence_readiness_score": _average_int(
            row.evidence_readiness_score for row in rows
        ),
        "n_dispatch_spec_identity_valid": n_dispatch_spec_identity_valid,
        "n_dispatch_spec_identity_mismatches": len(rows)
        - n_dispatch_spec_identity_valid,
        "n_request_playbook_identity_valid": n_request_playbook_identity_valid,
        "n_request_playbook_identity_mismatches": len(rows)
        - n_request_playbook_identity_valid,
        "n_self_contained_request_payloads": n_self_contained_request_payloads,
        "n_request_payload_identity_mismatches": len(rows)
        - n_self_contained_request_payloads,
        "n_row_schema_valid": n_row_schema_valid,
        "n_row_schema_invalid": n_row_schema_invalid,
        "resource_request_queue_row_schema": row_schema,
        "by_request_phase": dict(sorted(by_request_phase.items())),
        "by_queue_action_kind": dict(sorted(by_action_kind.items())),
        "by_resource_id": dict(sorted(by_resource_id.items())),
        "rows": row_dicts,
        "all_ok": (
            not errors
            and bool(rows)
            and all(row.ok for row in rows)
            and n_row_schema_invalid == 0
        ),
        "errors": errors,
        "resource_request_queue_fingerprint": stable_hash(row_dicts),
        "proof_evidence_status": PROOF_EVIDENCE_STATUS,
        "proof_evidence_boundary": PROOF_EVIDENCE_BOUNDARY,
        "limitations": [
            "resource requests dispatch evidence-gathering work and do not certify proofs",
            "frontier resources may require deployment-specific credentials, licenses, MCP servers, or CLI tools",
            "accepted responses still require downstream validation and target-prover replay before proof claims",
        ],
    }
    if out_dir is not None:
        out_dir.mkdir(parents=True, exist_ok=True)
        (
            out_dir
            / "formalization_gap_planner_resource_request_queue_manifest.json"
        ).write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
        (
            out_dir / "formalization_gap_planner_resource_request_queue.jsonl"
        ).write_text(
            "\n".join(json.dumps(row, sort_keys=True) for row in row_dicts)
            + ("\n" if rows else ""),
            encoding="utf-8",
        )
        (
            out_dir
            / "formalization_gap_planner_resource_request_queue_row.schema.json"
        ).write_text(json.dumps(row_schema, indent=2), encoding="utf-8")
        (
            out_dir / "formalization_gap_planner_resource_request_queue.md"
        ).write_text(
            _markdown_report(payload),
            encoding="utf-8",
        )
    return payload


def resource_request_queue_row_json_schema() -> dict[str, object]:
    string_array = {"type": "array", "items": {"type": "string"}}
    candidate_declaration_row_schema: dict[str, object] = {
        "type": "object",
        "additionalProperties": False,
        "required": [
            "declaration",
            "target_prover_family",
            "source_field",
        ],
        "properties": {
            "declaration": {"type": "string", "minLength": 1},
            "target_prover_family": {"type": "string", "minLength": 1},
            "source_field": {"type": "string", "minLength": 1},
        },
    }
    required = [
        "schema_version",
        "resource_request_id",
        "action_resource_plan_id",
        "primitive_action_id",
        "coverage_map_id",
        "goal_plan_id",
        "route_id",
        "display_name",
        "primitive",
        "target_primitives",
        "actionable_work_items",
        "coverage_bucket",
        "queue_action_kind",
        "priority_score",
        "minimal_delta_cost_score",
        "reuse_readiness_score",
        "evidence_readiness_score",
        "priority_rationale",
        "target_prover_family",
        "library_snapshot_ref",
        "candidate_declaration_rows",
        "request_phase",
        "request_rank",
        "component_ids",
        "resource_id",
        "resource_contract_ids",
        "request_contract_fields",
        "response_contract_fields",
        "request_playbook",
        "request_payload",
        "expected_response_artifact",
        "acceptance_gate",
        "escalation_triggers",
        "stop_conditions",
        "execution_command",
        "mcp_or_cli_hint",
        "dispatch_spec",
        "proof_evidence_status",
        "proof_evidence_boundary",
        "ok",
        "errors",
    ]
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": RESOURCE_REQUEST_QUEUE_ROW_SCHEMA_ID,
        "title": "Formalization gap planner resource-request queue row",
        "description": (
            "Per-resource dispatch packet for local-first and frontier "
            "formalization-planner resources. Rows are not theorem proof evidence."
        ),
        "type": "object",
        "additionalProperties": False,
        "required": required,
        "properties": {
            "schema_version": {
                "type": "integer",
                "const": (
                    FORMALIZATION_GAP_PLANNER_RESOURCE_REQUEST_QUEUE_SCHEMA_VERSION
                ),
            },
            "resource_request_id": {"type": "string", "minLength": 1},
            "action_resource_plan_id": {"type": "string", "minLength": 1},
            "primitive_action_id": {"type": "string", "minLength": 1},
            "coverage_map_id": {"type": "string", "minLength": 1},
            "goal_plan_id": {"type": "string", "minLength": 1},
            "route_id": {"type": "string", "minLength": 1},
            "display_name": {"type": "string", "minLength": 1},
            "primitive": {"type": "string", "minLength": 1},
            "target_primitives": string_array,
            "actionable_work_items": string_array,
            "coverage_bucket": {"type": "string", "minLength": 1},
            "queue_action_kind": {"type": "string", "minLength": 1},
            "priority_score": {"type": "integer"},
            "minimal_delta_cost_score": {"type": "integer"},
            "reuse_readiness_score": {"type": "integer"},
            "evidence_readiness_score": {"type": "integer"},
            "priority_rationale": string_array,
            "target_prover_family": {"type": "string", "minLength": 1},
            "library_snapshot_ref": {"type": "string", "minLength": 1},
            "candidate_declaration_rows": {
                "type": "array",
                "items": candidate_declaration_row_schema,
            },
            "request_phase": {"type": "string", "enum": list(REQUEST_PHASES)},
            "request_rank": {"type": "integer"},
            "component_ids": string_array,
            "resource_id": {"type": "string", "minLength": 1},
            "resource_contract_ids": string_array,
            "request_contract_fields": string_array,
            "response_contract_fields": string_array,
            "request_playbook": {"type": "object"},
            "request_payload": {"type": "object"},
            "expected_response_artifact": {"type": "string", "minLength": 1},
            "acceptance_gate": {"type": "string", "minLength": 1},
            "escalation_triggers": string_array,
            "stop_conditions": string_array,
            "execution_command": {"type": "string", "minLength": 1},
            "mcp_or_cli_hint": {"type": "string"},
            "dispatch_spec": {"type": "object"},
            "proof_evidence_status": {"type": "string", "const": PROOF_EVIDENCE_STATUS},
            "proof_evidence_boundary": {
                "type": "string",
                "pattern": "not theorem proof evidence",
            },
            "ok": {"type": "boolean"},
            "errors": string_array,
        },
    }


def validate_resource_request_queue_row(
    row: dict[str, object],
    schema: dict[str, object] | None = None,
) -> list[str]:
    if not isinstance(row, dict):
        return ["resource request queue row must be an object"]
    row_schema = schema or resource_request_queue_row_json_schema()
    required = tuple(row_schema.get("required", ()))
    errors: list[str] = []
    for field_name in required:
        if field_name not in row:
            errors.append(f"{field_name} required")
    properties = row_schema.get("properties", {})
    if isinstance(properties, dict):
        for field_name, field_schema in properties.items():
            if field_name in row and isinstance(field_schema, dict):
                errors.extend(
                    _schema_property_errors(field_name, row[field_name], field_schema)
                )
    allowed = set(required)
    for field_name in row:
        if field_name not in allowed:
            errors.append(f"{field_name} unexpected")
    if not _str_tuple(row.get("component_ids", [])):
        errors.append("component_ids must be non-empty")
    if not _str_tuple(row.get("resource_contract_ids", [])):
        errors.append("resource_contract_ids must be non-empty")
    if not _str_tuple(row.get("request_contract_fields", [])):
        errors.append("request_contract_fields must be non-empty")
    if not _str_tuple(row.get("response_contract_fields", [])):
        errors.append("response_contract_fields must be non-empty")
    if int(row.get("request_rank", 0) or 0) < 1:
        errors.append("request_rank must be positive")
    row_target = _target_prover_key(row.get("target_prover_family", ""))
    for index, declaration_row in enumerate(
        row.get("candidate_declaration_rows", []) or []
    ):
        if not isinstance(declaration_row, dict):
            continue
        declaration_target = _target_prover_key(
            declaration_row.get("target_prover_family", "")
        )
        if row_target and declaration_target and declaration_target != row_target:
            errors.append(
                "candidate_declaration_rows"
                f"[{index}].target_prover_family must match row target_prover_family"
            )
    request_payload = row.get("request_payload")
    if not isinstance(request_payload, dict):
        errors.append("request_payload must be object")
    else:
        for field_name in (
            "resource_request_id",
            "action_resource_plan_id",
            "primitive_action_id",
            "goal_plan_id",
            "route_id",
            "primitive",
            "target_primitives",
            "actionable_work_items",
            "queue_action_kind",
            "priority_score",
            "minimal_delta_cost_score",
            "reuse_readiness_score",
            "evidence_readiness_score",
            "priority_rationale",
            "target_prover_family",
            "library_snapshot_ref",
            "candidate_declaration_rows",
            "resource_id",
            "request_phase",
            "request_rank",
            "expected_response_artifact",
            "component_ids",
            "evidence_inputs",
            "expected_outputs",
            "request_contract_fields",
            "response_contract_fields",
            "execution_command",
            "mcp_or_cli_hint",
            "dispatch_spec",
            "request_playbook",
            "proof_evidence_boundary",
        ):
            if field_name not in request_payload:
                errors.append(f"request_payload.{field_name} required")
        errors.extend(_request_payload_identity_errors(row))
        errors.extend(_dispatch_spec_identity_errors(row))
    errors.extend(_request_playbook_identity_errors(row))
    for field_name in (
        "priority_score",
        "minimal_delta_cost_score",
        "reuse_readiness_score",
        "evidence_readiness_score",
    ):
        value = row.get(field_name)
        if isinstance(value, int) and not isinstance(value, bool):
            if value < 0 or value > 100:
                errors.append(f"{field_name} must be between 0 and 100")
    if "not theorem proof evidence" not in str(
        row.get("proof_evidence_boundary", "")
    ).lower():
        errors.append("proof_evidence_boundary must say not theorem proof evidence")
    return errors


def _llm_route_planner_resource_request_rows(
    llm_rows: tuple[dict[str, Any], ...],
    *,
    fallback_target_prover_family: str,
    fallback_library_snapshot_ref: str,
) -> tuple[FormalizationGapPlannerResourceRequestQueueRow, ...]:
    rows: list[FormalizationGapPlannerResourceRequestQueueRow] = []
    for planner_row in llm_rows:
        for source_kind, source_items in (
            ("search_request", _dict_tuple(planner_row.get("search_requests", []))),
            (
                "planner_next_action",
                _dict_tuple(planner_row.get("planner_next_actions", [])),
            ),
            (
                "residual_interpretation",
                _dict_tuple(planner_row.get("residual_interpretations", [])),
            ),
        ):
            for source_index, source_item in enumerate(source_items):
                action_row = _llm_route_planner_action_row(
                    planner_row,
                    source_item,
                    source_kind=source_kind,
                    source_index=source_index,
                    fallback_target_prover_family=fallback_target_prover_family,
                    fallback_library_snapshot_ref=fallback_library_snapshot_ref,
                )
                hook_kind = str(action_row.get("llm_hook_kind", ""))
                queries = _llm_query_tuple(source_item)
                for request_row in _resource_request_rows(
                    _action_resource_plan_projection(action_row)
                ):
                    rows.append(
                        _with_llm_route_planner_trace(
                            request_row,
                            planner_row,
                            source_item,
                            source_kind=source_kind,
                            source_index=source_index,
                            hook_kind=hook_kind,
                            queries=queries,
                        )
                    )
        for source_index, source_item in enumerate(
            _llm_formal_attempt_queue_source_items(planner_row)
        ):
            action_row = _llm_route_planner_action_row(
                planner_row,
                source_item,
                source_kind="formal_attempt_queue",
                source_index=source_index,
                fallback_target_prover_family=fallback_target_prover_family,
                fallback_library_snapshot_ref=fallback_library_snapshot_ref,
            )
            hook_kind = str(action_row.get("llm_hook_kind", ""))
            queries = _llm_query_tuple(source_item)
            for request_row in _resource_request_rows(
                _action_resource_plan_projection(action_row)
            ):
                rows.append(
                    _with_llm_route_planner_trace(
                        request_row,
                        planner_row,
                        source_item,
                        source_kind="formal_attempt_queue",
                        source_index=source_index,
                        hook_kind=hook_kind,
                        queries=queries,
                    )
                )
    return tuple(rows)


def _llm_route_planner_route_planning_brief_resource_request_rows(
    request_packets: tuple[dict[str, Any], ...],
    *,
    fallback_target_prover_family: str,
    fallback_library_snapshot_ref: str,
) -> tuple[FormalizationGapPlannerResourceRequestQueueRow, ...]:
    rows: list[FormalizationGapPlannerResourceRequestQueueRow] = []
    for request_packet in request_packets:
        route_planning_brief = _route_planning_brief_from_request_packet(
            request_packet
        )
        evidence_gaps = _dict_tuple(route_planning_brief.get("evidence_gaps", []))
        if not evidence_gaps:
            continue
        planner_row = _planner_row_from_request_packet(
            request_packet,
            route_planning_brief=route_planning_brief,
            fallback_target_prover_family=fallback_target_prover_family,
            fallback_library_snapshot_ref=fallback_library_snapshot_ref,
        )
        for source_index, evidence_gap in enumerate(evidence_gaps):
            source_item = _route_planning_brief_evidence_gap_source_item(
                request_packet,
                route_planning_brief,
                evidence_gap,
            )
            action_row = _llm_route_planner_action_row(
                planner_row,
                source_item,
                source_kind="route_planning_brief_evidence_gap",
                source_index=source_index,
                fallback_target_prover_family=fallback_target_prover_family,
                fallback_library_snapshot_ref=fallback_library_snapshot_ref,
            )
            hook_kind = str(action_row.get("llm_hook_kind", ""))
            queries = _llm_query_tuple(source_item)
            for request_row in _resource_request_rows(
                _action_resource_plan_projection(action_row)
            ):
                rows.append(
                    _with_llm_route_planner_trace(
                        request_row,
                        planner_row,
                        source_item,
                        source_kind="route_planning_brief_evidence_gap",
                        source_index=source_index,
                        hook_kind=hook_kind,
                        queries=queries,
                    )
                )
    return tuple(rows)


def _llm_formal_attempt_queue_source_items(
    planner_row: dict[str, Any],
) -> tuple[dict[str, object], ...]:
    items: list[dict[str, object]] = []
    formal_attempt_queue = _dict_tuple(planner_row.get("formal_attempt_queue", []))
    for queue_index, item in enumerate(formal_attempt_queue):
        schedule_row = _matching_formal_attempt_schedule_row(
            planner_row,
            item,
            queue_index=queue_index,
        )
        status = _formal_attempt_schedule_status(item, schedule_row)
        if status != "initial_ready":
            continue
        source_item = dict(item)
        source_item.update(
            {
                "request_kind": "proof_state_feedback",
                "kind": "proof_state_feedback",
                "formal_attempt_queue_index": queue_index,
                "llm_route_planner_formal_attempt_queue_index": queue_index,
                "formal_attempt_dependency_status": status,
                "formal_attempt_initial_ready": True,
                "formal_attempt_schedule_row": schedule_row,
                "formal_attempt_context": _formal_attempt_context(
                    source_item=item,
                    queue_index=queue_index,
                    schedule_row=schedule_row,
                    dependency_status=status,
                ),
                "queries": _formal_attempt_queries(item, schedule_row),
                "actionable_work_items": _formal_attempt_work_items(
                    item,
                    schedule_row,
                ),
            }
        )
        items.append(source_item)
    return tuple(items)


def _llm_formal_attempt_queue_items_by_schedule_status(
    planner_row: dict[str, Any],
    *,
    status: str,
) -> tuple[dict[str, object], ...]:
    rows: list[dict[str, object]] = []
    formal_attempt_queue = _dict_tuple(planner_row.get("formal_attempt_queue", []))
    for queue_index, item in enumerate(formal_attempt_queue):
        schedule_row = _matching_formal_attempt_schedule_row(
            planner_row,
            item,
            queue_index=queue_index,
        )
        if _formal_attempt_schedule_status(item, schedule_row) == status:
            rows.append(dict(item))
    return tuple(rows)


def _matching_formal_attempt_schedule_row(
    planner_row: dict[str, Any],
    item: dict[str, object],
    *,
    queue_index: int,
) -> dict[str, object]:
    schedule = _dict_value(
        planner_row,
        "formal_attempt_queue_schedule",
    ) or _dict_value(
        planner_row,
        "llm_route_planner_formal_attempt_queue_schedule",
    )
    rows = _dict_tuple(schedule.get("attempt_dependency_rows", []))
    attempt_id = str(item.get("attempt_id", "")).strip()
    formal_node_id = str(item.get("formal_node_id", "")).strip()
    for row in rows:
        if attempt_id and str(row.get("attempt_id", "")).strip() == attempt_id:
            return row
        if (
            formal_node_id
            and str(row.get("formal_node_id", "")).strip() == formal_node_id
        ):
            return row
        row_index = _parse_int(row.get("formal_attempt_queue_index", -1), -1)
        if row_index == queue_index:
            return row
    return {}


def _formal_attempt_schedule_status(
    item: dict[str, object],
    schedule_row: dict[str, object],
) -> str:
    raw_status = _normal_formal_attempt_status(
        str(schedule_row.get("dependency_status", "")).strip()
    )
    if raw_status:
        return raw_status
    if bool(schedule_row.get("initial_ready", False)):
        return "initial_ready"
    missing = _str_tuple(
        schedule_row.get("missing_prerequisite_formal_node_ids", [])
    ) or _str_tuple(item.get("formal_attempt_missing_prerequisite_formal_node_ids", []))
    if missing:
        return "missing_prerequisite_attempts"
    prerequisites = _str_tuple(
        schedule_row.get("prerequisite_formal_node_ids", [])
    ) or _str_tuple(item.get("prerequisite_formal_node_ids", []))
    if prerequisites:
        return "waiting_for_formal_prerequisite_attempts"
    return "initial_ready"


def _normal_formal_attempt_status(status: str) -> str:
    raw = str(status or "").strip()
    if raw in {"initial_ready", "ready_no_formal_prerequisites"}:
        return "initial_ready"
    if raw in {
        "missing_prerequisite_attempts",
        "missing_formal_prerequisite_attempts",
    }:
        return "missing_prerequisite_attempts"
    if raw == "waiting_for_formal_prerequisite_attempts":
        return raw
    return raw


def _formal_attempt_context(
    *,
    source_item: dict[str, object],
    queue_index: int,
    schedule_row: dict[str, object],
    dependency_status: str,
) -> dict[str, object]:
    return {
        "attempt_id": str(source_item.get("attempt_id", "")).strip(),
        "formal_node_id": str(source_item.get("formal_node_id", "")).strip(),
        "formal_attempt_queue_index": queue_index,
        "formal_attempt_dependency_status": dependency_status,
        "attempt_kind": str(source_item.get("attempt_kind", "")).strip(),
        "primitive": str(source_item.get("primitive", "")).strip(),
        "target_primitives": _str_tuple(source_item.get("target_primitives", [])),
        "target_prover_family": str(
            source_item.get("target_prover_family", "")
        ).strip(),
        "prerequisite_formal_node_ids": (
            _str_tuple(schedule_row.get("prerequisite_formal_node_ids", []))
            or _str_tuple(source_item.get("prerequisite_formal_node_ids", []))
        ),
        "prerequisite_attempt_ids": _str_tuple(
            schedule_row.get("prerequisite_attempt_ids", [])
        ),
        "missing_prerequisite_formal_node_ids": _str_tuple(
            schedule_row.get("missing_prerequisite_formal_node_ids", [])
        ),
        "expected_feedback": _str_tuple(source_item.get("expected_feedback", [])),
        "action": str(source_item.get("action", "")).strip(),
        "formal_attempt_schedule_row": dict(schedule_row),
    }


def _formal_attempt_queries(
    item: dict[str, object],
    schedule_row: dict[str, object],
) -> tuple[str, ...]:
    values: list[object] = [
        item.get("queries", []),
        item.get("query", []),
        item.get("action", ""),
        item.get("attempt_kind", ""),
        item.get("formal_node_id", ""),
        item.get("primitive", ""),
        item.get("expected_feedback", []),
        schedule_row.get("dependency_status", ""),
    ]
    primitive = str(item.get("primitive", "")).strip()
    if primitive:
        values.append(f"proof_state_feedback formal attempt {primitive}")
    return _str_tuple(_flatten_llm_strings(values))


def _formal_attempt_work_items(
    item: dict[str, object],
    schedule_row: dict[str, object],
) -> tuple[str, ...]:
    explicit = _str_tuple(item.get("actionable_work_items", []))
    if explicit:
        return explicit
    attempt_id = str(item.get("attempt_id", "")).strip()
    formal_node_id = str(item.get("formal_node_id", "")).strip()
    primitive = str(item.get("primitive", "")).strip() or "formal attempt"
    attempt_kind = str(item.get("attempt_kind", "")).strip()
    return _str_tuple(
        [
            (
                "run dependency-ready formal_attempt_queue item through "
                f"target prover feedback for {primitive}"
            ),
            f"attempt_id={attempt_id}" if attempt_id else "",
            f"formal_node_id={formal_node_id}" if formal_node_id else "",
            f"attempt_kind={attempt_kind}" if attempt_kind else "",
            (
                "schedule_dependency_status="
                + str(schedule_row.get("dependency_status", "")).strip()
            )
            if schedule_row
            else "",
        ]
    )


def _route_planning_brief_from_request_packet(
    request_packet: dict[str, Any],
) -> dict[str, Any]:
    context_packet = _dict_value(request_packet, "context_packet")
    return _dict_value(context_packet, "route_planning_brief")


def _planner_row_from_request_packet(
    request_packet: dict[str, Any],
    *,
    route_planning_brief: dict[str, Any],
    fallback_target_prover_family: str,
    fallback_library_snapshot_ref: str,
) -> dict[str, Any]:
    context_packet = _dict_value(request_packet, "context_packet")
    target_route = _dict_value(request_packet, "target_route")
    request_id = str(request_packet.get("request_id", "")).strip()
    route_id = (
        str(route_planning_brief.get("route_id", "")).strip()
        or str(target_route.get("route_id", "")).strip()
        or str(request_packet.get("route_id", "")).strip()
    )
    display_name = (
        str(route_planning_brief.get("display_name", "")).strip()
        or str(target_route.get("display_name", "")).strip()
        or route_id
    )
    target_prover_family = (
        str(route_planning_brief.get("target_prover_family", "")).strip()
        or str(request_packet.get("target_prover_family", "")).strip()
        or fallback_target_prover_family.strip()
        or "lean4"
    )
    library_snapshot_ref = (
        str(route_planning_brief.get("library_snapshot_ref", "")).strip()
        or str(request_packet.get("library_snapshot_ref", "")).strip()
        or fallback_library_snapshot_ref.strip()
        or "unspecified_library_snapshot"
    )
    target_context = _dict_value(route_planning_brief, "target_context")
    selected_primitives = _str_tuple(target_context.get("primitive_candidates", []))
    route_adoption_preconditions = _dict_value(
        context_packet,
        "route_adoption_preconditions",
    )
    return {
        "llm_route_planner_row_id": (
            "llm_route_planner_request_brief:"
            + stable_hash([request_id, route_id, route_planning_brief])[:20]
        ),
        "request_id": request_id,
        "route_id": route_id,
        "display_name": display_name,
        "target_prover_family": target_prover_family,
        "library_snapshot_ref": library_snapshot_ref,
        "minimal_delta_plan": {"selected_primitives": list(selected_primitives)},
        "standalone_route": target_route,
        "target_theorem_context_packet": target_context,
        "route_planning_brief": route_planning_brief,
        "route_adoption_preconditions": route_adoption_preconditions,
    }


def _route_planning_brief_evidence_gap_source_item(
    request_packet: dict[str, Any],
    route_planning_brief: dict[str, Any],
    evidence_gap: dict[str, object],
) -> dict[str, object]:
    gap_kind = str(evidence_gap.get("gap_kind", "") or "").strip()
    gap_id = str(evidence_gap.get("gap_id", "") or "").strip()
    target_primitives = _str_tuple(evidence_gap.get("target_primitives", []))
    evidence_fields = _str_tuple(evidence_gap.get("evidence_fields", []))
    reason = str(evidence_gap.get("reason", "") or "").strip()
    recommended_action = str(evidence_gap.get("recommended_action", "") or "").strip()
    target_context = _dict_value(route_planning_brief, "target_context")
    theorem_statement = str(target_context.get("theorem_statement", "") or "").strip()
    query = _route_planning_brief_gap_query(
        gap_kind=gap_kind,
        gap_id=gap_id,
        reason=reason,
        recommended_action=recommended_action,
        target_primitives=target_primitives,
        theorem_statement=theorem_statement,
    )
    return {
        "request_kind": _route_planning_brief_gap_request_kind(gap_kind),
        "query": query,
        "queries": (query,),
        "reason": reason,
        "recommended_next_action": recommended_action,
        "action": recommended_action,
        "target_primitives": target_primitives,
        "route_planning_brief_gap_id": gap_id,
        "route_planning_brief_gap_kind": gap_kind,
        "route_planning_brief_evidence_fields": evidence_fields,
        "route_planning_brief_id": str(
            route_planning_brief.get("route_id", "")
        ),
        "llm_route_planner_request_id": str(request_packet.get("request_id", "")),
        "actionable_work_items": _route_planning_brief_gap_work_items(
            gap_kind=gap_kind,
            recommended_action=recommended_action,
            target_primitives=target_primitives,
        ),
    }


def _route_planning_brief_gap_request_kind(gap_kind: str) -> str:
    key = _text_key(gap_kind)
    if "source" in key or "literature" in key:
        return "literature_discovery"
    if "formal_library" in key or "library" in key or "declaration" in key:
        return "formal_library_grounding"
    if "proof_state" in key or "proof_body" in key or "prover" in key:
        return "proof_state_feedback"
    return "route_revision"


def _route_planning_brief_gap_query(
    *,
    gap_kind: str,
    gap_id: str,
    reason: str,
    recommended_action: str,
    target_primitives: tuple[str, ...],
    theorem_statement: str,
) -> str:
    primitive_text = ", ".join(target_primitives) or "route"
    request_kind = _route_planning_brief_gap_request_kind(gap_kind)
    theorem_hint = theorem_statement[:240]
    return " ".join(
        part
        for part in (
            request_kind,
            gap_id,
            f"target primitives: {primitive_text}",
            recommended_action,
            reason,
            theorem_hint,
        )
        if part
    )


def _route_planning_brief_gap_work_items(
    *,
    gap_kind: str,
    recommended_action: str,
    target_primitives: tuple[str, ...],
) -> tuple[str, ...]:
    primitive_text = ", ".join(target_primitives) or "route"
    action = recommended_action or _route_planning_brief_gap_request_kind(gap_kind)
    return (
        (
            "route_planning_brief evidence gap: "
            f"{action} for {primitive_text}"
        ),
    )


def _llm_route_planner_action_row(
    planner_row: dict[str, Any],
    source_item: dict[str, object],
    *,
    source_kind: str,
    source_index: int,
    fallback_target_prover_family: str,
    fallback_library_snapshot_ref: str,
) -> dict[str, Any]:
    target_prover_family = (
        str(planner_row.get("target_prover_family", "")).strip()
        or fallback_target_prover_family.strip()
        or "lean4"
    )
    library_snapshot_ref = (
        str(planner_row.get("library_snapshot_ref", "")).strip()
        or fallback_library_snapshot_ref.strip()
        or "unspecified_library_snapshot"
    )
    hook_kind = _target_scoped_llm_hook_kind(
        _llm_hook_kind(source_item, source_kind=source_kind),
        target_prover_family=target_prover_family,
    )
    local_resource_ids, frontier_resource_ids = _llm_resource_ids_for_hook(
        hook_kind,
        target_prover_family=target_prover_family,
    )
    resource_ids = tuple(dict.fromkeys((*local_resource_ids, *frontier_resource_ids)))
    request_contracts = {
        resource_id: _llm_request_contract_fields_for_hook(
            hook_kind,
            resource_id=resource_id,
        )
        for resource_id in resource_ids
    }
    response_contracts = {
        resource_id: _llm_response_contract_fields_for_hook(
            hook_kind,
            resource_id=resource_id,
        )
        for resource_id in resource_ids
    }
    resource_contracts = {
        resource_id: (
            "formalization_gap_planner_llm_route_planner_resource_contract:"
            + stable_hash([hook_kind, resource_id, target_prover_family])[:20],
        )
        for resource_id in resource_ids
    }
    route_adoption_preconditions = _llm_route_adoption_preconditions(planner_row)
    precondition_request_fields = (
        ("llm_route_planner_route_adoption_preconditions",)
        if route_adoption_preconditions
        else tuple()
    )
    formal_attempt_request_fields = (
        ("formal_attempt_context",)
        if source_kind == "formal_attempt_queue"
        else tuple()
    )
    request_contracts = {
        resource_id: tuple(
            dict.fromkeys(
                (*fields, *precondition_request_fields, *formal_attempt_request_fields)
            )
        )
        for resource_id, fields in request_contracts.items()
    }
    target_primitives = _llm_target_primitives(
        planner_row,
        source_item,
    )
    queries = _llm_query_tuple(source_item)
    primitive = target_primitives[0] if target_primitives else _llm_label(
        queries[0] if queries else hook_kind
    )
    planner_row_id = (
        str(planner_row.get("llm_route_planner_row_id", "")).strip()
        or str(planner_row.get("request_id", "")).strip()
        or "llm_route_planner_row:" + stable_hash(planner_row)[:16]
    )
    route_id = (
        str(planner_row.get("route_id", "")).strip()
        or "llm_route_planner_route:" + stable_hash(planner_row_id)[:16]
    )
    source_digest = stable_hash(
        [
            planner_row_id,
            route_id,
            source_kind,
            source_index,
            source_item,
            hook_kind,
        ]
    )[:20]
    evidence_inputs = _str_tuple(
        [
            f"llm_route_planner_row_id={planner_row_id}",
            f"llm_route_planner_source_kind={source_kind}",
            f"llm_route_planner_source_index={source_index}",
            f"llm_route_planner_hook_kind={hook_kind}",
            *queries,
        ]
    )
    return {
        "schema_version": FORMALIZATION_GAP_PLANNER_ACTION_RESOURCE_PLAN_SCHEMA_VERSION,
        "action_resource_plan_id": (
            "formalization_gap_planner_llm_route_planner_action:"
            + source_digest
        ),
        "primitive_action_id": (
            "formalization_gap_planner_llm_route_planner_primitive_action:"
            + source_digest
        ),
        "coverage_map_id": (
            "formalization_gap_planner_llm_route_planner_coverage_map:"
            + source_digest
        ),
        "goal_plan_id": (
            "formalization_gap_planner_llm_route_planner_goal_plan:"
            + source_digest
        ),
        "route_id": route_id,
        "display_name": (
            str(planner_row.get("display_name", "")).strip()
            or f"LLM route-planner follow-up for {route_id}"
        ),
        "primitive": primitive,
        "target_primitives": target_primitives,
        "actionable_work_items": _llm_actionable_work_items(
            source_item,
            hook_kind=hook_kind,
            queries=queries,
            target_primitives=target_primitives,
        ),
        "coverage_bucket": "llm_route_planner_pending_evidence",
        "queue_action_kind": _llm_queue_action_kind(hook_kind),
        "priority_score": 80,
        "minimal_delta_cost_score": 60,
        "reuse_readiness_score": 25,
        "evidence_readiness_score": 60 if queries else 35,
        "priority_rationale": (
            f"llm_route_planner_source_kind={source_kind}",
            f"llm_route_planner_hook_kind={hook_kind}",
            "planner follow-up request preserves route-revision context",
        ),
        "target_prover_family": target_prover_family,
        "library_snapshot_ref": library_snapshot_ref,
        "candidate_declaration_rows": _llm_candidate_declaration_rows(
            source_item,
            target_prover_family=target_prover_family,
        ),
        "component_ids": _llm_component_ids_for_hook(hook_kind),
        "local_first_resource_ids": local_resource_ids,
        "frontier_escalation_resource_ids": frontier_resource_ids,
        "adapter_ids": tuple(f"{resource_id}_adapter" for resource_id in resource_ids),
        "resource_contract_ids": tuple(
            dict.fromkeys(
                contract_id
                for contract_ids in resource_contracts.values()
                for contract_id in contract_ids
            )
        ),
        "resource_contracts_by_resource": resource_contracts,
        "request_contract_fields_by_resource": request_contracts,
        "response_contract_fields_by_resource": response_contracts,
        "request_contract_fields": tuple(
            dict.fromkeys(
                field
                for fields in request_contracts.values()
                for field in fields
            )
        ),
        "response_contract_fields": tuple(
            dict.fromkeys(
                field
                for fields in response_contracts.values()
                for field in fields
            )
        ),
        "evidence_inputs": evidence_inputs,
        "expected_outputs": tuple(
            dict.fromkeys(
                field
                for fields in response_contracts.values()
                for field in fields
            )
        ),
        "escalation_triggers": (
            "local-first resource cannot resolve LLM route-planner follow-up",
            "response omits source grounding, library hits, or prover diagnostics required by contract",
        ),
        "stop_conditions": (
            "schema-valid resource response is recorded in the resource-response ledger",
            "target-prover replay or source-grounding audit accepts the response boundary",
        ),
        "acceptance_gate": (
            "accept only bounded planner feedback that echoes the LLM "
            "route-planner row and resource request identity; this is not "
            "theorem proof evidence"
        ),
        "reproduction_surface": "formalization_gap_planner_llm_route_planner_manifest",
        "execution_commands": tuple(
            _execution_command(
                resource_id,
                "local_first" if resource_id in local_resource_ids else "frontier_escalation",
                target_prover_family,
            )
            for resource_id in resource_ids
        ),
        "resource_selection_reason": (
            f"LLM route-planner {source_kind} classified as {hook_kind} and "
            "converted to local-first/frontier evidence dispatch packets"
        ),
        "proof_evidence_status": ACTION_RESOURCE_PROOF_EVIDENCE_STATUS,
        "proof_evidence_boundary": ACTION_RESOURCE_PROOF_EVIDENCE_BOUNDARY,
        "ok": True,
        "errors": tuple(),
        "llm_hook_kind": hook_kind,
    }


def _action_resource_plan_projection(action_row: dict[str, Any]) -> dict[str, Any]:
    allowed_fields = set(
        [
            "schema_version",
            "action_resource_plan_id",
            "primitive_action_id",
            "coverage_map_id",
            "goal_plan_id",
            "route_id",
            "display_name",
            "primitive",
            "target_primitives",
            "actionable_work_items",
            "coverage_bucket",
            "queue_action_kind",
            "priority_score",
            "minimal_delta_cost_score",
            "reuse_readiness_score",
            "evidence_readiness_score",
            "priority_rationale",
            "target_prover_family",
            "library_snapshot_ref",
            "candidate_declaration_rows",
            "component_ids",
            "local_first_resource_ids",
            "frontier_escalation_resource_ids",
            "adapter_ids",
            "resource_contract_ids",
            "resource_contracts_by_resource",
            "request_contract_fields_by_resource",
            "response_contract_fields_by_resource",
            "request_contract_fields",
            "response_contract_fields",
            "evidence_inputs",
            "expected_outputs",
            "escalation_triggers",
            "stop_conditions",
            "acceptance_gate",
            "reproduction_surface",
            "execution_commands",
            "resource_selection_reason",
            "proof_evidence_status",
            "proof_evidence_boundary",
            "ok",
            "errors",
        ]
    )
    return {key: value for key, value in action_row.items() if key in allowed_fields}


def _with_llm_route_planner_trace(
    row: FormalizationGapPlannerResourceRequestQueueRow,
    planner_row: dict[str, Any],
    source_item: dict[str, object],
    *,
    source_kind: str,
    source_index: int,
    hook_kind: str,
    queries: tuple[str, ...],
) -> FormalizationGapPlannerResourceRequestQueueRow:
    planner_row_id = str(planner_row.get("llm_route_planner_row_id", "")).strip()
    request_id = str(planner_row.get("request_id", "")).strip()
    request_payload = dict(row.request_payload)
    request_playbook = dict(row.request_playbook)
    input_summary = dict(request_playbook.get("input_summary", {}))
    route_adoption_preconditions = _llm_route_adoption_preconditions(planner_row)
    input_summary.update(
        {
            "llm_route_planner_row_id": planner_row_id,
            "llm_route_planner_request_id": request_id,
            "llm_route_planner_source_kind": source_kind,
            "llm_route_planner_source_index": source_index,
            "llm_route_planner_hook_kind": hook_kind,
            "llm_route_planner_queries": queries,
        }
    )
    residual_goal_context = _llm_residual_goal_context(
        source_item,
        source_kind=source_kind,
    )
    formal_attempt_context = _dict_value(source_item, "formal_attempt_context")
    if route_adoption_preconditions:
        input_summary["llm_route_planner_route_adoption_preconditions"] = (
            route_adoption_preconditions
        )
    if residual_goal_context:
        input_summary["residual_goal_context"] = residual_goal_context
    if formal_attempt_context:
        input_summary["formal_attempt_context"] = formal_attempt_context
    request_playbook.update(
        {
            "input_summary": input_summary,
            "llm_route_planner_row_id": planner_row_id,
            "llm_route_planner_request_id": request_id,
            "llm_route_planner_source_kind": source_kind,
            "llm_route_planner_source_index": source_index,
            "llm_route_planner_hook_kind": hook_kind,
            "llm_route_planner_source_item": dict(source_item),
        }
    )
    if route_adoption_preconditions:
        request_playbook["llm_route_planner_route_adoption_preconditions"] = (
            route_adoption_preconditions
        )
        request_playbook["acceptance_checklist"] = tuple(
            dict.fromkeys(
                (
                    *_str_tuple(request_playbook.get("acceptance_checklist", [])),
                    (
                        "response addresses "
                        "llm_route_planner_route_adoption_preconditions before "
                        "route adoption"
                    ),
                )
            )
        )
    if residual_goal_context:
        request_playbook["residual_goal_context"] = residual_goal_context
    if formal_attempt_context:
        request_playbook["formal_attempt_context"] = formal_attempt_context
        request_playbook["acceptance_checklist"] = tuple(
            dict.fromkeys(
                (
                    *_str_tuple(request_playbook.get("acceptance_checklist", [])),
                    (
                        "response echoes formal_attempt_context and records "
                        "kernel status, residual goals, or blocker diagnostics "
                        "for that exact queue item"
                    ),
                )
            )
        )
    request_payload.update(
        {
            "llm_route_planner_row_id": planner_row_id,
            "llm_route_planner_request_id": request_id,
            "llm_route_planner_source_kind": source_kind,
            "llm_route_planner_source_index": source_index,
            "llm_route_planner_hook_kind": hook_kind,
            "llm_route_planner_queries": queries,
            "llm_route_planner_source_item": dict(source_item),
            "request_playbook": request_playbook,
        }
    )
    if route_adoption_preconditions:
        request_payload["llm_route_planner_route_adoption_preconditions"] = (
            route_adoption_preconditions
        )
    if residual_goal_context:
        request_payload["residual_goal_context"] = residual_goal_context
    if formal_attempt_context:
        request_payload["formal_attempt_context"] = formal_attempt_context
    return replace(
        row,
        request_payload=request_payload,
        request_playbook=request_playbook,
    )


def _llm_hook_kind(
    item: dict[str, object],
    *,
    source_kind: str,
) -> str:
    if source_kind == "residual_interpretation":
        residual_directive = _text_key(
            " ".join(
                [
                    *_str_tuple(item.get("request_kind", "")),
                    *_str_tuple(item.get("kind", "")),
                    *_str_tuple(item.get("route_repair", "")),
                    *_str_tuple(item.get("repair_action", "")),
                    *_str_tuple(item.get("interpretation", "")),
                    *_str_tuple(item.get("recommended_next_action", "")),
                    *_flatten_llm_strings(item.get("resource_id", [])),
                    *_flatten_llm_strings(item.get("resource_ids", [])),
                    *_flatten_llm_strings(item.get("tool_owner_ids", [])),
                ]
            )
        )
        if any(
            token in residual_directive
            for token in ("literature", "source", "paper", "paperclip", "paperqa")
        ):
            return "literature_discovery"
        if any(
            token in residual_directive
            for token in (
                "lean_search",
                "leansearch",
                "leanfinder",
                "loogle",
                "mathlib",
            )
        ):
            return "lean_library_grounding"
        if any(
            token in residual_directive
            for token in ("formal_library", "formal_source", "declaration", "library")
        ):
            return "formal_library_grounding"
        if any(
            token in residual_directive
            for token in (
                "proof_state",
                "prover",
                "diagnostic",
                "lean_lsp",
                "lsp",
                "lake",
                "serapi",
                "sledgehammer",
                "agda",
            )
        ):
            return "proof_state_feedback"
        return "route_revision"
    text = _text_key(
        " ".join(
            [
                source_kind,
                *_str_tuple(item.get("request_kind", "")),
                *_str_tuple(item.get("kind", "")),
                *_llm_query_tuple(item),
                *_flatten_llm_strings(item.get("resource_id", [])),
                *_flatten_llm_strings(item.get("resource_ids", [])),
                *_flatten_llm_strings(item.get("tool_owner_ids", [])),
            ]
        )
    )
    if any(
        token in text
        for token in (
            "proof_state",
            "prover",
            "diagnostic",
            "residual_goal",
            "lean_lsp",
            "lsp",
            "lake",
            "serapi",
            "sledgehammer",
            "agda",
        )
    ):
        return "proof_state_feedback"
    if any(
        token in text
        for token in ("lean_search", "leansearch", "leanfinder", "loogle", "mathlib")
    ):
        return "lean_library_grounding"
    if any(
        token in text
        for token in ("formal_library", "formal_source", "declaration", "library")
    ):
        return "formal_library_grounding"
    if any(
        token in text
        for token in ("literature", "source", "paper", "paperclip", "paperqa", "textbook")
    ):
        return "literature_discovery"
    return "route_revision"


def _target_scoped_llm_hook_kind(
    hook_kind: str,
    *,
    target_prover_family: str,
) -> str:
    if hook_kind == "lean_library_grounding":
        target = _target_prover_key(target_prover_family)
        if target and target != "lean4":
            return "formal_library_grounding"
    return hook_kind


def _llm_resource_ids_for_hook(
    hook_kind: str,
    *,
    target_prover_family: str,
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    target = _target_prover_key(target_prover_family)
    hook_kind = _target_scoped_llm_hook_kind(
        hook_kind,
        target_prover_family=target_prover_family,
    )
    if hook_kind == "literature_discovery":
        return ("local_literature_corpus",), (
            "paperclip_cli_mcp",
            "paperqa2_local_library",
        )
    if hook_kind == "lean_library_grounding" or (
        hook_kind == "formal_library_grounding" and target == "lean4"
    ):
        return (
            "local_formal_source_index",
            "local_lean_rag_dependency_graph",
        ), (
            "loogle_leansearch",
            "leanexplore_mcp",
        )
    if hook_kind == "formal_library_grounding":
        return ("local_target_formal_source_index",), (
            _target_library_frontier_resource(target),
        )
    if hook_kind == "proof_state_feedback":
        if target == "lean4":
            return ("local_lake_lean",), ("lean_lsp_mcp", "leandojo_reprover")
        return ("local_target_formal_source_index",), (
            _target_library_frontier_resource(target),
        )
    return ("local_route_revision_overlay",), ("frontier_route_revision_handoff",)


def _target_library_frontier_resource(target_prover_family: str) -> str:
    target = _target_prover_key(target_prover_family)
    return {
        "rocq": "rocq_lsp_serapi",
        "isabelle": "isabelle_sledgehammer_afp",
        "agda": "agda_search_auto",
        "lean4": "loogle_leansearch",
    }.get(target, "target_prover_library_search")


def _llm_queue_action_kind(hook_kind: str) -> str:
    if hook_kind == "literature_discovery":
        return "source_port"
    if hook_kind in {"lean_library_grounding", "formal_library_grounding"}:
        return "rerun_library_alignment"
    if hook_kind == "proof_state_feedback":
        return "prove_bridge_lemma"
    if hook_kind == "route_revision":
        return "route_revision"
    return "rerun_library_alignment"


def _llm_component_ids_for_hook(hook_kind: str) -> tuple[str, ...]:
    component_ids = ["formalization_gap_planner_llm_route_planner"]
    if hook_kind == "literature_discovery":
        component_ids.extend(
            [
                "literature_grounded_route_synthesis",
                "informal_route_dag_decomposition",
            ]
        )
    elif hook_kind in {"lean_library_grounding", "formal_library_grounding"}:
        component_ids.append("formal_library_coverage_mapping")
    elif hook_kind == "proof_state_feedback":
        component_ids.append("prover_feedback_refinement")
    else:
        component_ids.append("route_revision_handoff")
    return tuple(dict.fromkeys(component_ids))


def _llm_request_contract_fields_for_hook(
    hook_kind: str,
    *,
    resource_id: str,
) -> tuple[str, ...]:
    fields = [
        "resource_request_id",
        "llm_route_planner_row_id",
        "llm_route_planner_source_kind",
        "route_id",
        "target_prover_family",
        "target_primitives",
        "queries",
        "proof_evidence_boundary",
    ]
    if hook_kind in {"lean_library_grounding", "formal_library_grounding"}:
        fields.extend(["library_snapshot_ref", "candidate_declaration_rows"])
    if hook_kind == "proof_state_feedback":
        fields.extend(["candidate_declaration_rows", "residual_goal_context"])
    if hook_kind == "route_revision":
        fields.extend(
            ["minimal_delta_plan", "route_revision_trigger", "residual_goal_context"]
        )
    if resource_id:
        fields.append("resource_id")
    return tuple(dict.fromkeys(fields))


def _llm_response_contract_fields_for_hook(
    hook_kind: str,
    *,
    resource_id: str,
) -> tuple[str, ...]:
    if hook_kind == "literature_discovery":
        return (
            "source_refs",
            "source_snippets",
            "route_evidence_nodes",
            "assumption_or_theorem_variant_updates",
        )
    if hook_kind in {"lean_library_grounding", "formal_library_grounding"}:
        fields = [
            "formal_declaration_hits",
            "coverage_updates",
            "target_prover_family",
        ]
        if "lean" in resource_id.lower():
            fields.append("lean_declaration_hits")
        return tuple(dict.fromkeys(fields))
    if hook_kind == "proof_state_feedback":
        return (
            "prover_diagnostics",
            "residual_goals",
            "premise_candidates",
            "proof_attempts",
        )
    return (
        "route_revision_decision",
        "revised_informal_knowledge_dag_nodes",
        "revised_formal_realization_dag_nodes",
        "minimal_delta_plan",
    )


def _llm_route_adoption_preconditions(planner_row: dict[str, Any]) -> dict[str, object]:
    preconditions = _dict_value(planner_row, "route_adoption_preconditions")
    if not preconditions:
        preconditions = _dict_value(
            planner_row,
            "llm_route_planner_route_adoption_preconditions",
        )
    return preconditions


def _llm_request_payload_route_adoption_preconditions(
    request_payload: dict[str, object],
) -> dict[str, object]:
    return _dict_value(
        request_payload,
        "llm_route_planner_route_adoption_preconditions",
    )


def _route_adoption_precondition_known_blocker_count(
    preconditions: dict[str, object],
) -> int:
    return int(
        preconditions.get(
            "n_known_pre_response_blockers",
            len(_str_tuple(preconditions.get("known_pre_response_blockers", []))),
        )
        or 0
    )


def _route_adoption_precondition_required_response_field_count(
    preconditions: dict[str, object],
) -> int:
    return int(
        preconditions.get(
            "n_response_required_fields",
            len(_str_tuple(preconditions.get("response_required_fields", []))),
        )
        or 0
    )


def _route_adoption_precondition_target_primitive_count(
    preconditions: dict[str, object],
) -> int:
    return int(
        preconditions.get(
            "n_target_primitives",
            len(_str_tuple(preconditions.get("target_primitives", []))),
        )
        or 0
    )


def _llm_target_primitives(
    planner_row: dict[str, Any],
    source_item: dict[str, object],
) -> tuple[str, ...]:
    primitives: list[str] = []
    for field_name in (
        "target_primitives",
        "residual_primitives",
        "primitives",
        "primitive",
    ):
        primitives.extend(_str_tuple(source_item.get(field_name, [])))
    minimal_delta_plan = planner_row.get("minimal_delta_plan", {})
    if isinstance(minimal_delta_plan, dict):
        primitives.extend(_str_tuple(minimal_delta_plan.get("selected_primitives", [])))
    route = planner_row.get("standalone_route", {})
    if isinstance(route, dict):
        for primitive_row in _dict_tuple(route.get("primitives", [])):
            primitives.extend(_str_tuple(primitive_row.get("primitive", "")))
    for node_field in (
        "formal_realization_dag_nodes",
        "lean_realization_dag_nodes",
        "informal_knowledge_dag_nodes",
    ):
        for node in _dict_tuple(planner_row.get(node_field, [])):
            primitives.extend(
                _str_tuple(
                    [
                        node.get("primitive", ""),
                        node.get("label", ""),
                        node.get("node_id", ""),
                    ]
                )
            )
    return tuple(dict.fromkeys(item.strip() for item in primitives if item.strip()))[:8]


def _llm_candidate_declaration_rows(
    source_item: dict[str, object],
    *,
    target_prover_family: str,
) -> tuple[dict[str, object], ...]:
    rows: list[dict[str, object]] = []
    rows.extend(_candidate_declaration_rows(source_item.get("candidate_declaration_rows", [])))
    for field_name in (
        "candidate_declarations",
        "formal_declaration_hits",
        "lean_declaration_hits",
        "declarations",
    ):
        for value in _flatten_llm_strings(source_item.get(field_name, [])):
            rows.append(
                {
                    "declaration": value,
                    "target_prover_family": target_prover_family,
                    "source_field": field_name,
                }
            )
        for value in _dict_tuple(source_item.get(field_name, [])):
            rows.append(
                {
                    "declaration": str(
                        value.get("declaration")
                        or value.get("declaration_name")
                        or value.get("name")
                        or ""
                    ),
                    "target_prover_family": str(
                        value.get("target_prover_family", "")
                        or target_prover_family
                    ),
                    "source_field": field_name,
                }
            )
    return _candidate_declaration_rows(rows)


def _llm_query_tuple(item: dict[str, object]) -> tuple[str, ...]:
    values: list[object] = []
    for field_name in (
        "query",
        "queries",
        "reason",
        "rationale",
        "action",
        "next_action",
        "description",
        "residual_goal",
        "residual_goals",
        "route_repair",
        "repair_action",
        "interpretation",
        "recommended_next_action",
        "source_search_queries",
        "formal_library_queries",
        "prover_feedback_queries",
    ):
        values.append(item.get(field_name, []))
    return _str_tuple(_flatten_llm_strings(values))


def _llm_residual_goal_context(
    source_item: dict[str, object],
    *,
    source_kind: str,
) -> dict[str, object]:
    if source_kind != "residual_interpretation" and not any(
        key in source_item
        for key in (
            "residual_goal",
            "residual_goals",
            "residual_primitives",
            "route_repair",
            "repair_action",
        )
    ):
        return {}
    return {
        "source_kind": source_kind,
        "residual_goal": str(source_item.get("residual_goal", "") or ""),
        "residual_goals": _str_tuple(source_item.get("residual_goals", [])),
        "residual_primitives": _str_tuple(source_item.get("residual_primitives", [])),
        "target_primitives": _str_tuple(source_item.get("target_primitives", [])),
        "interpretation": str(source_item.get("interpretation", "") or ""),
        "route_repair": str(source_item.get("route_repair", "") or ""),
        "repair_action": str(source_item.get("repair_action", "") or ""),
        "source_refs": _str_tuple(source_item.get("source_refs", [])),
        "source_snippets": _dict_tuple(source_item.get("source_snippets", [])),
        "source_search_status": str(source_item.get("source_search_status", "") or ""),
        "formal_gap_boundary": str(source_item.get("formal_gap_boundary", "") or ""),
        "queries": _llm_query_tuple(source_item),
    }


def _llm_actionable_work_items(
    item: dict[str, object],
    *,
    hook_kind: str,
    queries: tuple[str, ...],
    target_primitives: tuple[str, ...],
) -> tuple[str, ...]:
    explicit_items: list[str] = []
    for field_name in (
        "actionable_work_items",
        "work_items",
        "formalization_work_items",
        "next_actions",
    ):
        explicit_items.extend(_flatten_llm_strings(item.get(field_name, [])))
    if explicit_items:
        return _str_tuple(explicit_items)
    if queries:
        return _str_tuple(queries)
    primitive_text = ", ".join(target_primitives) or "route"
    return (f"{hook_kind}: gather bounded evidence for {primitive_text}",)


def _flatten_llm_strings(values: object) -> tuple[str, ...]:
    if isinstance(values, str):
        return (values,) if values else tuple()
    if isinstance(values, dict):
        return tuple()
    if not isinstance(values, Iterable):
        return (str(values),) if str(values) else tuple()
    flattened: list[str] = []
    for value in values:
        if isinstance(value, dict):
            continue
        if isinstance(value, (list, tuple, set)):
            flattened.extend(_flatten_llm_strings(value))
        elif str(value):
            flattened.append(str(value))
    return tuple(flattened)


def _llm_label(value: str) -> str:
    label = re.sub(r"\s+", "_", value.strip().lower())
    label = re.sub(r"[^a-z0-9_]+", "", label).strip("_")
    return label[:72] or "llm_route_planner_followup"


def _text_key(value: object) -> str:
    return re.sub(r"[^a-z0-9]+", "_", str(value).lower())


def _resource_request_rows(
    action_row: dict[str, Any],
) -> tuple[FormalizationGapPlannerResourceRequestQueueRow, ...]:
    action_validation_row = dict(action_row)
    action_validation_row.pop("target_primitives", None)
    action_errors = validate_action_resource_plan_row(action_validation_row)
    rows: list[FormalizationGapPlannerResourceRequestQueueRow] = []
    ranked_resources = [
        ("local_first", resource_id)
        for resource_id in _str_tuple(action_row.get("local_first_resource_ids", []))
    ]
    ranked_resources.extend(
        (
            ("frontier_escalation", resource_id)
            for resource_id in _str_tuple(
                action_row.get("frontier_escalation_resource_ids", [])
            )
        )
    )
    for request_rank, (phase, resource_id) in enumerate(ranked_resources, start=1):
        row_errors = list(action_errors)
        if phase not in REQUEST_PHASES:
            row_errors.append(f"unknown request phase: {phase}")
        if not resource_id:
            row_errors.append("resource_id missing")
        resource_contract_ids = _resource_specific_tuple(
            action_row,
            "resource_contracts_by_resource",
            resource_id,
            "resource_contract_ids",
        )
        request_contract_fields = _resource_specific_tuple(
            action_row,
            "request_contract_fields_by_resource",
            resource_id,
            "request_contract_fields",
        )
        response_contract_fields = _resource_specific_tuple(
            action_row,
            "response_contract_fields_by_resource",
            resource_id,
            "response_contract_fields",
        )
        if not resource_contract_ids:
            row_errors.append(f"resource contract missing for {resource_id}")
        if not request_contract_fields:
            row_errors.append(f"request contract fields missing for {resource_id}")
        if not response_contract_fields:
            row_errors.append(f"response contract fields missing for {resource_id}")
        target_primitives = _target_primitives_from_action_row(action_row)
        actionable_work_items = _str_tuple(
            action_row.get("actionable_work_items", [])
        )
        resource_request_id = (
            "formalization_gap_planner_resource_request:"
            + stable_hash(
                [
                    action_row.get("action_resource_plan_id", ""),
                    request_rank,
                    phase,
                    resource_id,
                ]
            )[:20]
        )
        expected_response_artifact = _expected_response_artifact(resource_id)
        execution_command = _execution_command(
            resource_id,
            phase,
            str(action_row.get("target_prover_family", "")),
        )
        mcp_or_cli_hint = _mcp_or_cli_hint(resource_id, phase)
        dispatch_spec = _dispatch_spec(
            resource_id,
            phase,
            target_prover_family=str(action_row.get("target_prover_family", "")),
            execution_command=execution_command,
            mcp_or_cli_hint=mcp_or_cli_hint,
            expected_response_artifact=expected_response_artifact,
        )
        request_playbook = _request_playbook(
            action_row,
            phase,
            resource_id,
            resource_request_id=resource_request_id,
            expected_response_artifact=expected_response_artifact,
            execution_command=execution_command,
            mcp_or_cli_hint=mcp_or_cli_hint,
        )
        request_payload = _request_payload(
            action_row,
            phase,
            resource_id,
            resource_request_id=resource_request_id,
            request_rank=request_rank,
            expected_response_artifact=expected_response_artifact,
            execution_command=execution_command,
            mcp_or_cli_hint=mcp_or_cli_hint,
            dispatch_spec=dispatch_spec,
            request_playbook=request_playbook,
        )
        rows.append(
            FormalizationGapPlannerResourceRequestQueueRow(
                schema_version=(
                    FORMALIZATION_GAP_PLANNER_RESOURCE_REQUEST_QUEUE_SCHEMA_VERSION
                ),
                resource_request_id=resource_request_id,
                action_resource_plan_id=str(
                    action_row.get("action_resource_plan_id", "")
                ),
                primitive_action_id=str(action_row.get("primitive_action_id", "")),
                coverage_map_id=str(action_row.get("coverage_map_id", "")),
                goal_plan_id=str(action_row.get("goal_plan_id", "")),
                route_id=str(action_row.get("route_id", "")),
                display_name=str(action_row.get("display_name", "")),
                primitive=str(action_row.get("primitive", "")),
                target_primitives=target_primitives,
                actionable_work_items=actionable_work_items,
                coverage_bucket=str(action_row.get("coverage_bucket", "")),
                queue_action_kind=str(action_row.get("queue_action_kind", "")),
                priority_score=_bounded_int(action_row.get("priority_score", 0)),
                minimal_delta_cost_score=_bounded_int(
                    action_row.get("minimal_delta_cost_score", 100)
                ),
                reuse_readiness_score=_bounded_int(
                    action_row.get("reuse_readiness_score", 0)
                ),
                evidence_readiness_score=_bounded_int(
                    action_row.get("evidence_readiness_score", 0)
                ),
                priority_rationale=_str_tuple(action_row.get("priority_rationale", [])),
                target_prover_family=str(action_row.get("target_prover_family", "")),
                library_snapshot_ref=str(action_row.get("library_snapshot_ref", "")),
                candidate_declaration_rows=_candidate_declaration_rows(
                    action_row.get("candidate_declaration_rows", [])
                ),
                request_phase=phase,
                request_rank=request_rank,
                component_ids=_str_tuple(action_row.get("component_ids", [])),
                resource_id=resource_id,
                resource_contract_ids=resource_contract_ids,
                request_contract_fields=request_contract_fields,
                response_contract_fields=response_contract_fields,
                request_playbook=request_playbook,
                request_payload=request_payload,
                expected_response_artifact=expected_response_artifact,
                acceptance_gate=str(action_row.get("acceptance_gate", "")),
                escalation_triggers=_str_tuple(
                    action_row.get("escalation_triggers", [])
                ),
                stop_conditions=_str_tuple(action_row.get("stop_conditions", [])),
                execution_command=execution_command,
                mcp_or_cli_hint=mcp_or_cli_hint,
                dispatch_spec=dispatch_spec,
                proof_evidence_status=PROOF_EVIDENCE_STATUS,
                proof_evidence_boundary=PROOF_EVIDENCE_BOUNDARY,
                ok=bool(action_row.get("ok", False)) and not row_errors,
                errors=tuple(row_errors),
            )
        )
    return tuple(rows)


def _request_payload(
    action_row: dict[str, Any],
    phase: str,
    resource_id: str,
    *,
    resource_request_id: str,
    request_rank: int,
    expected_response_artifact: str,
    execution_command: str,
    mcp_or_cli_hint: str,
    dispatch_spec: dict[str, object],
    request_playbook: dict[str, object],
) -> dict[str, object]:
    resource_contract_ids = _resource_specific_tuple(
        action_row,
        "resource_contracts_by_resource",
        resource_id,
        "resource_contract_ids",
    )
    request_contract_fields = _resource_specific_tuple(
        action_row,
        "request_contract_fields_by_resource",
        resource_id,
        "request_contract_fields",
    )
    response_contract_fields = _resource_specific_tuple(
        action_row,
        "response_contract_fields_by_resource",
        resource_id,
        "response_contract_fields",
    )
    return {
        "resource_request_id": resource_request_id,
        "action_resource_plan_id": str(action_row.get("action_resource_plan_id", "")),
        "primitive_action_id": str(action_row.get("primitive_action_id", "")),
        "coverage_map_id": str(action_row.get("coverage_map_id", "")),
        "goal_plan_id": str(action_row.get("goal_plan_id", "")),
        "route_id": str(action_row.get("route_id", "")),
        "primitive": str(action_row.get("primitive", "")),
        "target_primitives": _target_primitives_from_action_row(action_row),
        "actionable_work_items": _str_tuple(
            action_row.get("actionable_work_items", [])
        ),
        "coverage_bucket": str(action_row.get("coverage_bucket", "")),
        "queue_action_kind": str(action_row.get("queue_action_kind", "")),
        "priority_score": _bounded_int(action_row.get("priority_score", 0)),
        "minimal_delta_cost_score": _bounded_int(
            action_row.get("minimal_delta_cost_score", 100)
        ),
        "reuse_readiness_score": _bounded_int(action_row.get("reuse_readiness_score", 0)),
        "evidence_readiness_score": _bounded_int(
            action_row.get("evidence_readiness_score", 0)
        ),
        "priority_rationale": _str_tuple(action_row.get("priority_rationale", [])),
        "target_prover_family": str(action_row.get("target_prover_family", "")),
        "library_snapshot_ref": str(action_row.get("library_snapshot_ref", "")),
        "candidate_declaration_rows": _candidate_declaration_rows(
            action_row.get("candidate_declaration_rows", [])
        ),
        "resource_id": resource_id,
        "request_phase": phase,
        "request_rank": request_rank,
        "expected_response_artifact": expected_response_artifact,
        "component_ids": _str_tuple(action_row.get("component_ids", [])),
        "evidence_inputs": _str_tuple(action_row.get("evidence_inputs", [])),
        "expected_outputs": _str_tuple(action_row.get("expected_outputs", [])),
        "request_contract_fields": request_contract_fields,
        "response_contract_fields": response_contract_fields,
        "resource_contract_ids": resource_contract_ids,
        "execution_command": execution_command,
        "mcp_or_cli_hint": mcp_or_cli_hint,
        "dispatch_spec": dispatch_spec,
        "request_playbook": request_playbook,
        "acceptance_gate": str(action_row.get("acceptance_gate", "")),
        "stop_conditions": _str_tuple(action_row.get("stop_conditions", [])),
        "action_resource_proof_evidence_boundary": (
            ACTION_RESOURCE_PROOF_EVIDENCE_BOUNDARY
        ),
        "proof_evidence_boundary": PROOF_EVIDENCE_BOUNDARY,
    }


def _request_playbook(
    action_row: dict[str, Any],
    phase: str,
    resource_id: str,
    *,
    resource_request_id: str,
    expected_response_artifact: str,
    execution_command: str,
    mcp_or_cli_hint: str,
) -> dict[str, object]:
    request_contract_fields = _resource_specific_tuple(
        action_row,
        "request_contract_fields_by_resource",
        resource_id,
        "request_contract_fields",
    )
    response_contract_fields = _resource_specific_tuple(
        action_row,
        "response_contract_fields_by_resource",
        resource_id,
        "response_contract_fields",
    )
    candidate_declarations = tuple(
        str(row.get("declaration", ""))
        for row in _candidate_declaration_rows(
            action_row.get("candidate_declaration_rows", [])
        )
        if str(row.get("declaration", ""))
    )
    return {
        "resource_request_id": resource_request_id,
        "resource_id": resource_id,
        "request_phase": phase,
        "target_prover_family": str(action_row.get("target_prover_family", "")),
        "operator_prompt": _playbook_operator_prompt(
            action_row,
            resource_id,
            expected_response_artifact,
            response_contract_fields,
        ),
        "input_summary": {
            "route_id": str(action_row.get("route_id", "")),
            "display_name": str(action_row.get("display_name", "")),
            "primitive": str(action_row.get("primitive", "")),
            "target_primitives": _target_primitives_from_action_row(action_row),
            "actionable_work_items": _str_tuple(
                action_row.get("actionable_work_items", [])
            ),
            "coverage_bucket": str(action_row.get("coverage_bucket", "")),
            "queue_action_kind": str(action_row.get("queue_action_kind", "")),
            "candidate_declarations": candidate_declarations,
            "evidence_inputs": _str_tuple(action_row.get("evidence_inputs", [])),
            "expected_outputs": _str_tuple(action_row.get("expected_outputs", [])),
        },
        "required_inputs": request_contract_fields,
        "expected_response_fields": response_contract_fields,
        "expected_response_artifact": expected_response_artifact,
        "acceptance_checklist": _playbook_acceptance_checklist(
            action_row,
            response_contract_fields,
            expected_response_artifact,
        ),
        "rejection_triggers": _playbook_rejection_triggers(action_row),
        "stop_conditions": _str_tuple(action_row.get("stop_conditions", [])),
        "execution_command": execution_command,
        "mcp_or_cli_hint": mcp_or_cli_hint,
        "proof_evidence_boundary": PROOF_EVIDENCE_BOUNDARY,
    }


def _playbook_operator_prompt(
    action_row: dict[str, Any],
    resource_id: str,
    expected_response_artifact: str,
    response_contract_fields: tuple[str, ...],
) -> str:
    response_fields = ", ".join(response_contract_fields) or "the response contract"
    primitive = str(action_row.get("primitive", "")).strip() or "<primitive>"
    route_id = str(action_row.get("route_id", "")).strip() or "<route>"
    action_kind = (
        str(action_row.get("queue_action_kind", "")).strip()
        or "<queue_action_kind>"
    )
    work_items = _str_tuple(action_row.get("actionable_work_items", []))
    work_item_clause = (
        " Actionable work items: " + " | ".join(work_items) + "."
        if work_items
        else ""
    )
    return (
        f"Use {resource_id} for {action_kind} on primitive {primitive} "
        f"in route {route_id}; return {expected_response_artifact} with "
        f"{response_fields}.{work_item_clause}"
    )


def _playbook_acceptance_checklist(
    action_row: dict[str, Any],
    response_contract_fields: tuple[str, ...],
    expected_response_artifact: str,
) -> tuple[str, ...]:
    checklist = [
        "response echoes resource_request_id and resource_id",
        f"response artifact equals {expected_response_artifact}",
        "response remains planner feedback and not theorem proof evidence",
    ]
    if response_contract_fields:
        checklist.append(
            "response covers required fields: " + ", ".join(response_contract_fields)
        )
    acceptance_gate = str(action_row.get("acceptance_gate", "")).strip()
    if acceptance_gate:
        checklist.append(f"action acceptance gate passes: {acceptance_gate}")
    if _candidate_declaration_rows(action_row.get("candidate_declaration_rows", [])):
        checklist.append(
            "candidate declarations are replayed, mapped, or rejected with diagnostics"
        )
    return tuple(checklist)


def _playbook_rejection_triggers(action_row: dict[str, Any]) -> tuple[str, ...]:
    triggers = list(_str_tuple(action_row.get("escalation_triggers", [])))
    triggers.extend(
        [
            "response omits request identity, resource identity, or expected artifact",
            "response claims theorem proof evidence without target-prover replay",
        ]
    )
    return tuple(dict.fromkeys(trigger for trigger in triggers if trigger))


def _request_payload_identity_errors(row: dict[str, Any]) -> list[str]:
    request_payload = row.get("request_payload")
    if not isinstance(request_payload, dict):
        return ["request_payload must be object"]
    errors: list[str] = []
    for field_name in (
        "resource_request_id",
        "action_resource_plan_id",
        "primitive_action_id",
        "coverage_map_id",
        "goal_plan_id",
        "route_id",
        "primitive",
        "target_primitives",
        "actionable_work_items",
        "coverage_bucket",
        "queue_action_kind",
        "priority_score",
        "minimal_delta_cost_score",
        "reuse_readiness_score",
        "evidence_readiness_score",
        "priority_rationale",
        "target_prover_family",
        "library_snapshot_ref",
        "resource_id",
        "request_phase",
        "expected_response_artifact",
        "execution_command",
        "mcp_or_cli_hint",
        "dispatch_spec",
        "request_playbook",
    ):
        if request_payload.get(field_name) != row.get(field_name):
            errors.append(f"request_payload.{field_name} must match row.{field_name}")
    if _candidate_declaration_rows(
        request_payload.get("candidate_declaration_rows", [])
    ) != _candidate_declaration_rows(row.get("candidate_declaration_rows", [])):
        errors.append(
            "request_payload.candidate_declaration_rows must match row.candidate_declaration_rows"
        )
    if request_payload.get("request_rank") != row.get("request_rank"):
        errors.append("request_payload.request_rank must match row.request_rank")
    return errors


def _request_playbook_identity_errors(row: dict[str, Any]) -> list[str]:
    request_playbook = row.get("request_playbook")
    if not isinstance(request_playbook, dict):
        return ["request_playbook must be object"]
    errors: list[str] = []
    for field_name in (
        "resource_request_id",
        "resource_id",
        "request_phase",
        "target_prover_family",
        "expected_response_artifact",
        "execution_command",
        "mcp_or_cli_hint",
        "proof_evidence_boundary",
    ):
        if request_playbook.get(field_name) != row.get(field_name):
            errors.append(f"request_playbook.{field_name} must match row.{field_name}")
    if _str_tuple(request_playbook.get("required_inputs", [])) != _str_tuple(
        row.get("request_contract_fields", [])
    ):
        errors.append(
            "request_playbook.required_inputs must match row.request_contract_fields"
        )
    if _str_tuple(
        request_playbook.get("expected_response_fields", [])
    ) != _str_tuple(row.get("response_contract_fields", [])):
        errors.append(
            "request_playbook.expected_response_fields must match row.response_contract_fields"
        )
    if not str(request_playbook.get("operator_prompt", "")).strip():
        errors.append("request_playbook.operator_prompt must be non-empty")
    if not isinstance(request_playbook.get("input_summary"), dict):
        errors.append("request_playbook.input_summary must be object")
    elif _str_tuple(
        request_playbook.get("input_summary", {}).get("target_primitives", [])
    ) != _str_tuple(row.get("target_primitives", [])):
        errors.append(
            "request_playbook.input_summary.target_primitives must match row.target_primitives"
        )
    if isinstance(request_playbook.get("input_summary"), dict) and _str_tuple(
        request_playbook.get("input_summary", {}).get("actionable_work_items", [])
    ) != _str_tuple(row.get("actionable_work_items", [])):
        errors.append(
            "request_playbook.input_summary.actionable_work_items must match row.actionable_work_items"
        )
    if not _str_tuple(request_playbook.get("acceptance_checklist", [])):
        errors.append("request_playbook.acceptance_checklist must be non-empty")
    request_payload = row.get("request_payload")
    if isinstance(request_payload, dict):
        if request_payload.get("request_playbook") != request_playbook:
            errors.append(
                "request_payload.request_playbook must match row.request_playbook"
            )
    return errors


def _dispatch_spec_identity_errors(row: dict[str, Any]) -> list[str]:
    dispatch_spec = row.get("dispatch_spec")
    if not isinstance(dispatch_spec, dict):
        return ["dispatch_spec must be object"]
    request_payload = row.get("request_payload", {})
    payload_dispatch_spec = (
        request_payload.get("dispatch_spec")
        if isinstance(request_payload, dict)
        else None
    )
    errors: list[str] = []
    for field_name in (
        "resource_id",
        "request_phase",
        "target_prover_family",
        "execution_command",
        "mcp_or_cli_hint",
        "expected_response_artifact",
        "response_jsonl_contract",
        "proof_evidence_boundary",
    ):
        expected = row.get(field_name)
        if field_name == "target_prover_family":
            expected = row.get("target_prover_family")
        elif field_name == "response_jsonl_contract":
            expected = "formalization_gap_planner_resource_responses.jsonl"
        elif field_name == "proof_evidence_boundary":
            expected = PROOF_EVIDENCE_BOUNDARY
        if dispatch_spec.get(field_name) != expected:
            errors.append(f"dispatch_spec.{field_name} must match row dispatch context")
    if dispatch_spec.get("dispatch_kind") != _dispatch_kind(
        str(row.get("resource_id", "")),
        str(row.get("request_phase", "")),
    ):
        errors.append("dispatch_spec.dispatch_kind must match resource_id/request_phase")
    if dispatch_spec.get("adapter_surface") != _adapter_surface(
        str(row.get("resource_id", "")),
        str(row.get("request_phase", "")),
    ):
        errors.append("dispatch_spec.adapter_surface must match resource_id/request_phase")
    if not isinstance(payload_dispatch_spec, dict):
        errors.append("request_payload.dispatch_spec must be object")
    elif payload_dispatch_spec != dispatch_spec:
        errors.append("request_payload.dispatch_spec must match row.dispatch_spec")
    return errors


def _resource_specific_tuple(
    action_row: dict[str, Any],
    map_field: str,
    resource_id: str,
    fallback_field: str,
) -> tuple[str, ...]:
    value = action_row.get(map_field, {})
    if isinstance(value, dict):
        mapped = _str_tuple(value.get(resource_id, []))
        if mapped:
            return mapped
    return _str_tuple(action_row.get(fallback_field, []))


def _target_primitives_from_action_row(action_row: dict[str, Any]) -> tuple[str, ...]:
    explicit = _str_tuple(action_row.get("target_primitives", []))
    primitive = str(action_row.get("primitive", "")).strip()
    return tuple(dict.fromkeys([*explicit, *([primitive] if primitive else [])]))


def _expected_response_artifact(resource_id: str) -> str:
    resource = resource_id.lower()
    if any(
        token in resource
        for token in (
            "loogle",
            "leansearch",
            "leanexplore",
            "formal_source",
            "dependency_graph",
            "rag",
        )
    ):
        return "formal_library_search_or_dependency_response"
    if any(token in resource for token in ("publication", "cross_prover")):
        return "publication_or_cross_prover_packet_response"
    if "route_revision" in resource:
        return "route_revision_response"
    if any(
        token in resource
        for token in (
            "literature",
            "paper",
            "scholar",
            "corpus",
            "benchmark",
        )
    ):
        return "literature_or_source_grounding_response"
    if any(
        token in resource
        for token in (
            "lsp",
            "lake",
            "prover",
            "reprover",
            "serapi",
            "sledgehammer",
            "agda",
        )
    ):
        return "proof_state_or_prover_feedback_response"
    return "planner_resource_response"


def _dispatch_spec(
    resource_id: str,
    phase: str,
    *,
    target_prover_family: str,
    execution_command: str,
    mcp_or_cli_hint: str,
    expected_response_artifact: str,
) -> dict[str, object]:
    return {
        "dispatch_kind": _dispatch_kind(resource_id, phase),
        "adapter_surface": _adapter_surface(resource_id, phase),
        "resource_id": resource_id,
        "request_phase": phase,
        "target_prover_family": target_prover_family,
        "execution_command": execution_command,
        "mcp_or_cli_hint": mcp_or_cli_hint,
        "expected_response_artifact": expected_response_artifact,
        "response_jsonl_contract": "formalization_gap_planner_resource_responses.jsonl",
        "proof_evidence_boundary": PROOF_EVIDENCE_BOUNDARY,
    }


def _dispatch_kind(resource_id: str, phase: str) -> str:
    resource = resource_id.lower()
    if phase == "local_first":
        return "local_cli"
    if "mcp" in resource or any(
        token in resource
        for token in (
            "lsp",
            "loogle",
            "leansearch",
            "leanexplore",
            "paperclip",
            "serapi",
            "sledgehammer",
            "agda",
        )
    ):
        return "frontier_mcp_or_cli"
    if any(token in resource for token in ("paperqa", "openscholar", "semantic")):
        return "frontier_literature_service"
    if any(token in resource for token in ("agentic", "reprover", "dependency_graph")):
        return "frontier_prover_orchestration"
    return "resource_specific_adapter"


def _adapter_surface(resource_id: str, phase: str) -> str:
    if phase == "local_first":
        return "ai_statistician_cli"
    resource = resource_id.lower()
    if "paperclip" in resource:
        return "paperclip_mcp_cli"
    if "paperqa" in resource:
        return "paperqa_api_or_cli"
    if "openscholar" in resource or "semantic" in resource:
        return "openscholar_semantic_scholar_api"
    if "loogle" in resource:
        return "loogle_api"
    if "leansearch" in resource:
        return "leansearch_api"
    if "leanexplore" in resource:
        return "leanexplore_mcp"
    if "serapi" in resource:
        return "rocq_serapi"
    if "lsp" in resource:
        return "target_prover_lsp_mcp"
    if "sledgehammer" in resource:
        return "isabelle_sledgehammer"
    if "agda" in resource:
        return "agda_search_or_automation"
    if "reprover" in resource:
        return "reprover_or_leandojo"
    if "agentic" in resource:
        return "agentic_prover_service"
    return "resource_specific_adapter"


def _execution_command(resource_id: str, phase: str, target_prover_family: str) -> str:
    resource = resource_id.lower()
    if any(token in resource for token in ("literature", "paperqa", "paperclip")):
        if phase == "local_first":
            return (
                "python3 -m ai_statistician.cli "
                "formalization-gap-planner-local-literature-adapter "
                "--formalization-gap-planner-refinement-queue-dir <refinement_queue_dir> "
                "--out <resource_response_dir>"
            )
        return f"dispatch resource request through {resource_id} MCP or CLI"
    if any(
        token in resource
        for token in ("formal_source", "lean_rag", "loogle", "leansearch", "leanexplore")
    ):
        if phase == "local_first":
            return (
                "python3 -m ai_statistician.cli "
                "formalization-gap-planner-local-formal-source-adapter "
                "--formalization-gap-planner-refinement-queue-dir <refinement_queue_dir> "
                "--out <resource_response_dir>"
            )
        return f"dispatch resource request through {resource_id} MCP or CLI"
    if any(
        token in resource
        for token in ("lake", "lsp", "prover", "reprover", "serapi", "sledgehammer")
    ):
        if phase == "local_first":
            return (
                "python3 -m ai_statistician.cli "
                "formalization-gap-planner-local-proof-state-adapter "
                "--formalization-gap-planner-refinement-queue-dir <refinement_queue_dir> "
                "--out <resource_response_dir>"
            )
        return (
            f"dispatch {target_prover_family or '<target-prover>'} proof-state "
            f"request through {resource_id}"
        )
    if "route_revision" in resource:
        return (
            "python3 -m ai_statistician.cli "
            "formalization-gap-planner-route-revision-overlay "
            "--goal-conditioned-minimal-formalization-plan-dir <planner_dir> "
            "--formalization-gap-planner-refinement-evidence-dir <refinement_evidence_dir> "
            "--formalization-gap-planner-resource-response-ledger-dir <resource_response_ledger_dir> "
            "--out <resource_response_dir>"
        )
    if any(token in resource for token in ("publication", "cross_prover")):
        return f"dispatch publication or cross-prover reuse audit request through {resource_id}"
    return f"dispatch resource request through {resource_id} adapter"


def _mcp_or_cli_hint(resource_id: str, phase: str) -> str:
    resource = resource_id.lower()
    if phase == "frontier_escalation":
        if "paperclip" in resource:
            return "PaperClip MCP/CLI literature search"
        if "openscholar" in resource:
            return "OpenScholar/Semantic Scholar search adapter"
        if "loogle" in resource or "leansearch" in resource:
            return "Loogle/LeanSearch query adapter"
        if "leanexplore" in resource:
            return "LeanExplore MCP adapter"
        if "serapi" in resource:
            return "Rocq SerAPI/LSP adapter"
        if "lsp" in resource:
            return "target-prover LSP MCP adapter"
        if "reprover" in resource:
            return "ReProver or LeanDojo prover-feedback adapter"
        if "sledgehammer" in resource:
            return "Isabelle/Sledgehammer adapter"
        if "agda" in resource:
            return "Agda search/automation adapter"
        if "agentic" in resource:
            return "agentic prover orchestration service"
    if "local_" in resource or resource.startswith("target_"):
        return "local CLI artifact adapter"
    return "resource-specific MCP or CLI adapter"


def _schema_property_errors(
    field_name: str,
    value: object,
    schema: dict[str, object],
) -> list[str]:
    errors: list[str] = []
    expected_type = schema.get("type")
    if expected_type == "string":
        if not isinstance(value, str):
            errors.append(f"{field_name} must be string")
            return errors
        min_length = schema.get("minLength")
        if isinstance(min_length, int) and len(value) < min_length:
            errors.append(f"{field_name} must be non-empty")
        pattern = schema.get("pattern")
        if isinstance(pattern, str) and not re.search(pattern, value):
            errors.append(f"{field_name} must match {pattern}")
        enum = schema.get("enum")
        if isinstance(enum, list) and value not in enum:
            errors.append(f"{field_name} must be one of {enum}")
        const = schema.get("const")
        if const is not None and value != const:
            errors.append(f"{field_name} must equal {const}")
    elif expected_type == "integer":
        if not isinstance(value, int) or isinstance(value, bool):
            errors.append(f"{field_name} must be integer")
            return errors
        const = schema.get("const")
        if const is not None and value != const:
            errors.append(f"{field_name} must equal {const}")
    elif expected_type == "boolean":
        if not isinstance(value, bool):
            errors.append(f"{field_name} must be boolean")
    elif expected_type == "array":
        if not isinstance(value, (list, tuple)):
            errors.append(f"{field_name} must be array")
            return errors
        item_schema = schema.get("items", {})
        if isinstance(item_schema, dict) and item_schema.get("type") == "string":
            for index, item in enumerate(value):
                if not isinstance(item, str):
                    errors.append(f"{field_name}[{index}] must be string")
        elif isinstance(item_schema, dict) and item_schema.get("type") == "object":
            for index, item in enumerate(value):
                if not isinstance(item, dict):
                    errors.append(f"{field_name}[{index}] must be object")
                    continue
                required = tuple(item_schema.get("required", ()))
                properties = item_schema.get("properties", {})
                allowed = set(required)
                for required_field in required:
                    if required_field not in item:
                        errors.append(
                            f"{field_name}[{index}].{required_field} required"
                        )
                if isinstance(properties, dict):
                    allowed = set(properties)
                    for child_name, child_schema in properties.items():
                        if child_name in item and isinstance(child_schema, dict):
                            errors.extend(
                                _schema_property_errors(
                                    f"{field_name}[{index}].{child_name}",
                                    item[child_name],
                                    child_schema,
                                )
                            )
                if item_schema.get("additionalProperties") is False:
                    for child_name in item:
                        if child_name not in allowed:
                            errors.append(
                                f"{field_name}[{index}].{child_name} unexpected"
                            )
    elif expected_type == "object" and not isinstance(value, dict):
        errors.append(f"{field_name} must be object")
    return errors


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


def _str_tuple(values: Any) -> tuple[str, ...]:
    if isinstance(values, str):
        return (values,) if values else tuple()
    if not isinstance(values, (list, tuple, set)):
        return tuple()
    return tuple(str(value) for value in values if str(value))


def _bounded_int(value: Any, *, lower: int = 0, upper: int = 100) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        parsed = lower
    return max(lower, min(upper, parsed))


def _parse_int(value: Any, fallback: int = 0) -> int:
    if isinstance(value, bool):
        return fallback
    try:
        return int(value)
    except (TypeError, ValueError):
        return fallback


def _average_int(values: Any) -> int:
    items = [int(value) for value in values]
    if not items:
        return 0
    return round(sum(items) / len(items))


def _candidate_declaration_rows(values: object) -> tuple[dict[str, object], ...]:
    rows: list[dict[str, object]] = []
    for item in _dict_tuple(values):
        declaration = str(
            item.get("declaration")
            or item.get("declaration_name")
            or item.get("lean_declaration")
            or ""
        ).strip()
        if not declaration:
            continue
        rows.append(
            {
                "declaration": declaration,
                "target_prover_family": str(
                    item.get("target_prover_family", "")
                    or item.get("target_prover", "")
                ).strip(),
                "source_field": str(
                    item.get("source_field", "") or "candidate_declaration_rows"
                ).strip(),
            }
        )
    compact: list[dict[str, object]] = []
    seen: set[tuple[str, str]] = set()
    for row in rows:
        declaration = str(row.get("declaration", "")).strip()
        if not declaration:
            continue
        row_target = str(row.get("target_prover_family", "")).strip()
        key = (_formal_declaration_key(declaration), _target_prover_key(row_target))
        if key in seen:
            continue
        seen.add(key)
        compact.append(
            {
                "declaration": declaration,
                "target_prover_family": row_target,
                "source_field": str(row.get("source_field", "")).strip()
                or "candidate_declaration_rows",
            }
        )
    return tuple(compact)


def _dict_tuple(values: Any) -> tuple[dict[str, object], ...]:
    if isinstance(values, dict):
        return (values,)
    if not isinstance(values, (list, tuple, set)):
        return tuple()
    return tuple(value for value in values if isinstance(value, dict))


def _dict_value(mapping: Any, key: str) -> dict[str, object]:
    value = mapping.get(key, {}) if isinstance(mapping, dict) else {}
    return dict(value) if isinstance(value, dict) else {}


def _formal_declaration_key(value: object) -> str:
    return re.sub(r"\s+", " ", str(value).strip()).lower()


def _target_prover_key(value: object) -> str:
    key = str(value).strip().lower().replace("-", "_")
    aliases = {
        "coq": "rocq",
        "coq8": "rocq",
        "lean": "lean4",
        "lean_4": "lean4",
        "isabelle_hol": "isabelle",
    }
    return aliases.get(key, key)


def _flatten_strings(values: Any) -> tuple[str, ...]:
    if isinstance(values, str):
        return (values,) if values else tuple()
    if not isinstance(values, Iterable):
        return tuple()
    flattened: list[str] = []
    for value in values:
        if isinstance(value, (list, tuple, set)):
            flattened.extend(_flatten_strings(value))
        elif str(value):
            flattened.append(str(value))
    return tuple(flattened)


def _markdown_report(payload: dict[str, object]) -> str:
    lines = [
        "# Formalization Gap Planner Resource Request Queue",
        "",
        f"- Resource requests: {payload.get('n_ok')}/{payload.get('n_resource_request_rows')}",
        (
            f"- Action-resource request rows: "
            f"{payload.get('n_action_resource_plan_resource_request_rows')}"
        ),
        (
            f"- LLM route-planner request rows: "
            f"{payload.get('n_llm_route_planner_resource_request_rows')}"
        ),
        (
            f"- LLM route-planning brief evidence gaps/request rows: "
            f"{payload.get('n_llm_route_planner_route_planning_brief_evidence_gaps')}/"
            f"{payload.get('n_llm_route_planner_route_planning_brief_resource_request_rows')}"
        ),
        f"- LLM search requests: {payload.get('n_llm_route_planner_search_requests')}",
        (
            f"- LLM planner next actions: "
            f"{payload.get('n_llm_route_planner_planner_next_actions')}"
        ),
        (
            f"- LLM residual interpretations: "
            f"{payload.get('n_llm_route_planner_residual_interpretations')}"
        ),
        (
            f"- LLM formal attempt queue items ready/waiting/missing/request rows: "
            f"{payload.get('n_llm_route_planner_formal_attempt_queue_ready_items')}/"
            f"{payload.get('n_llm_route_planner_formal_attempt_queue_waiting_items')}/"
            f"{payload.get('n_llm_route_planner_formal_attempt_queue_missing_prerequisite_items')}/"
            f"{payload.get('n_llm_route_planner_formal_attempt_queue_resource_request_rows')}"
        ),
        (
            f"- LLM route-adoption preconditions rows/blockers/required-fields/target-primitives/request-packets/request-targets: "
            f"{payload.get('n_llm_route_planner_rows_with_route_adoption_preconditions')}/"
            f"{payload.get('n_llm_route_planner_route_adoption_precondition_known_blockers')}/"
            f"{payload.get('n_llm_route_planner_route_adoption_precondition_required_response_fields')}/"
            f"{payload.get('n_llm_route_planner_route_adoption_precondition_target_primitives')}/"
            f"{payload.get('n_llm_route_planner_resource_request_rows_with_route_adoption_preconditions')}/"
            f"{payload.get('n_llm_route_planner_resource_request_route_adoption_precondition_target_primitives')}"
        ),
        f"- Target prover family: {payload.get('target_prover_family')}",
        f"- Target prover families: {payload.get('n_target_prover_families')}",
        f"- Local-first requests: {payload.get('n_local_first_requests')}",
        f"- Frontier escalation requests: {payload.get('n_frontier_escalation_requests')}",
        f"- Distinct resources: {payload.get('n_distinct_resources')}",
        (
            f"- Requests with actionable work items: "
            f"{payload.get('n_with_actionable_work_items')}/"
            f"{payload.get('n_resource_request_rows')}"
        ),
        f"- Actionable work items: {payload.get('n_actionable_work_items')}",
        f"- Minimal-delta reuse ready: {payload.get('n_minimal_delta_reuse_ready')}",
        (
            "- Minimal-delta light bridge/wrapper: "
            f"{payload.get('n_minimal_delta_light_bridge_or_wrapper')}"
        ),
        (
            "- Minimal-delta source/new-theory: "
            f"{payload.get('n_minimal_delta_source_or_new_theory')}"
        ),
        (
            "- Minimal-delta alignment blocked: "
            f"{payload.get('n_minimal_delta_alignment_blocked')}"
        ),
        (
            "- Average reuse/evidence readiness: "
            f"{payload.get('average_reuse_readiness_score')}/"
            f"{payload.get('average_evidence_readiness_score')}"
        ),
        (
            f"- Row schema valid: {payload.get('n_row_schema_valid')}/"
            f"{payload.get('n_resource_request_rows')}"
        ),
        (
            f"- Self-contained request payloads: "
            f"{payload.get('n_self_contained_request_payloads')}/"
            f"{payload.get('n_resource_request_rows')}"
        ),
        (
            f"- Dispatch specs valid: "
            f"{payload.get('n_dispatch_spec_identity_valid')}/"
            f"{payload.get('n_resource_request_rows')}"
        ),
        (
            f"- Request playbooks valid: "
            f"{payload.get('n_request_playbook_identity_valid')}/"
            f"{payload.get('n_resource_request_rows')}"
        ),
        f"- All OK: {payload.get('all_ok')}",
        "",
        "## Boundary",
        "",
        str(payload.get("proof_evidence_boundary", PROOF_EVIDENCE_BOUNDARY)),
        "",
        "## Request Phases",
        "",
    ]
    for phase, count in sorted((payload.get("by_request_phase", {}) or {}).items()):
        lines.append(f"- `{phase}`: {count}")
    lines.extend(["", "## Resources", ""])
    for resource_id, count in sorted((payload.get("by_resource_id", {}) or {}).items()):
        lines.append(f"- `{resource_id}`: {count}")
    return "\n".join(lines) + "\n"
