from __future__ import annotations

import json
import re
from collections import Counter
from collections.abc import Iterable
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .fingerprint import stable_hash
from .formalization_gap_planner_action_resource_plan import (
    ACTION_RESOURCE_PLAN_ROW_SCHEMA_ID,
    PROOF_EVIDENCE_BOUNDARY as ACTION_RESOURCE_PROOF_EVIDENCE_BOUNDARY,
    validate_action_resource_plan_row,
)


FORMALIZATION_GAP_PLANNER_RESOURCE_REQUEST_QUEUE_SCHEMA_VERSION = 3
RESOURCE_REQUEST_QUEUE_ROW_SCHEMA_ID = (
    "urn:ai-statistician:schemas:"
    "formalization-gap-planner-resource-request-queue-row:3"
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
    coverage_bucket: str
    queue_action_kind: str
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
    rows = tuple(
        request_row
        for action_row in action_rows
        for request_row in _resource_request_rows(action_row)
    )
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
    n_self_contained_request_payloads = sum(
        1 for row in row_dicts if not _request_payload_identity_errors(row)
    )
    n_dispatch_spec_identity_valid = sum(
        1 for row in row_dicts if not _dispatch_spec_identity_errors(row)
    )
    n_request_playbook_identity_valid = sum(
        1 for row in row_dicts if not _request_playbook_identity_errors(row)
    )
    payload: dict[str, object] = {
        "schema_version": (
            FORMALIZATION_GAP_PLANNER_RESOURCE_REQUEST_QUEUE_SCHEMA_VERSION
        ),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "component_name": "formalization_gap_planner_resource_request_queue",
        "source_components": (str(action_manifest.get("component_name", "")),),
        "action_resource_plan_dir": str(action_resource_plan_dir),
        "action_resource_plan_manifest": str(action_manifest_path),
        "target_prover_family": str(action_manifest.get("target_prover_family", "")),
        "library_snapshot_ref": str(action_manifest.get("library_snapshot_ref", "")),
        "n_action_resource_plan_rows": len(action_rows),
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
        "coverage_bucket",
        "queue_action_kind",
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
            "coverage_bucket": {"type": "string", "minLength": 1},
            "queue_action_kind": {"type": "string", "minLength": 1},
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
            "queue_action_kind",
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
    if "not theorem proof evidence" not in str(
        row.get("proof_evidence_boundary", "")
    ).lower():
        errors.append("proof_evidence_boundary must say not theorem proof evidence")
    return errors


def _resource_request_rows(
    action_row: dict[str, Any],
) -> tuple[FormalizationGapPlannerResourceRequestQueueRow, ...]:
    action_errors = validate_action_resource_plan_row(action_row)
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
                coverage_bucket=str(action_row.get("coverage_bucket", "")),
                queue_action_kind=str(action_row.get("queue_action_kind", "")),
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
        "coverage_bucket": str(action_row.get("coverage_bucket", "")),
        "queue_action_kind": str(action_row.get("queue_action_kind", "")),
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
    return (
        f"Use {resource_id} for {action_kind} on primitive {primitive} "
        f"in route {route_id}; return {expected_response_artifact} with "
        f"{response_fields}."
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
        "coverage_bucket",
        "queue_action_kind",
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
    if "lsp" in resource:
        return "target_prover_lsp_mcp"
    if "serapi" in resource:
        return "rocq_serapi"
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
        if "lsp" in resource:
            return "target-prover LSP MCP adapter"
        if "reprover" in resource:
            return "ReProver or LeanDojo prover-feedback adapter"
        if "serapi" in resource:
            return "Rocq SerAPI/LSP adapter"
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
        f"- Local-first requests: {payload.get('n_local_first_requests')}",
        f"- Frontier escalation requests: {payload.get('n_frontier_escalation_requests')}",
        f"- Distinct resources: {payload.get('n_distinct_resources')}",
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
