from __future__ import annotations

import json
import re
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .fingerprint import stable_hash
from .formalization_gap_planner_resource_request_queue import (
    RESOURCE_REQUEST_QUEUE_ROW_SCHEMA_ID,
    validate_resource_request_queue_row,
)
from .formalization_gap_planner_target_summary import target_prover_family_summary


FORMALIZATION_GAP_PLANNER_RESOURCE_RESPONSE_LEDGER_SCHEMA_VERSION = 6
QUALITY_CONTROL_FIELDS = (
    "resource_contract_ids",
    "required_quality_signals",
    "quality_gates",
    "response_validation_signals",
    "stop_conditions",
)
RESOURCE_RESPONSE_SCHEMA_ID = (
    "urn:ai-statistician:schemas:"
    "formalization-gap-planner-resource-response:1"
)
RESOURCE_RESPONSE_LEDGER_ROW_SCHEMA_ID = (
    "urn:ai-statistician:schemas:"
    "formalization-gap-planner-resource-response-ledger-row:6"
)
PROOF_EVIDENCE_STATUS = (
    "FORMALIZATION_GAP_PLANNER_RESOURCE_RESPONSE_LEDGER_NOT_PROOF_EVIDENCE"
)
PROOF_EVIDENCE_BOUNDARY = (
    "Formalization gap planner resource-response ledger rows validate local "
    "and frontier resource outputs against request contracts and route-revision "
    "handoff fields. They are adapter evidence and planner feedback, not "
    "theorem proof evidence."
)


@dataclass(frozen=True)
class FormalizationGapPlannerResourceResponseLedgerRow:
    schema_version: int
    resource_response_ledger_id: str
    resource_request_id: str
    action_resource_plan_id: str
    primitive_action_id: str
    coverage_map_id: str
    goal_plan_id: str
    route_id: str
    display_name: str
    primitive: str
    target_primitives: tuple[str, ...]
    coverage_bucket: str
    queue_action_kind: str
    target_prover_family: str
    library_snapshot_ref: str
    candidate_declaration_rows: tuple[dict[str, object], ...]
    request_phase: str
    component_ids: tuple[str, ...]
    resource_id: str
    resource_contract_ids: tuple[str, ...]
    stop_conditions: tuple[str, ...]
    quality_controls: dict[str, tuple[str, ...]]
    expected_response_artifact: str
    acceptance_gate: str
    dispatch_spec: dict[str, object]
    response_present: bool
    response_contract_fields: tuple[str, ...]
    response_contract_minimum_met: bool
    response_contract_ok: bool
    request_playbook_present: bool
    response_playbook_grounded: bool
    response_playbook_grounding_terms: tuple[str, ...]
    response_payload: dict[str, object]
    response_summary: str
    response_artifacts: tuple[str, ...]
    matched_response_contract_fields: tuple[str, ...]
    missing_response_contract_fields: tuple[str, ...]
    source_refs: tuple[str, ...]
    route_evidence_nodes: tuple[dict[str, object], ...]
    lean_declaration_hits: tuple[dict[str, object], ...]
    coverage_updates: dict[str, str]
    prover_diagnostics: tuple[str, ...]
    residual_goals: tuple[str, ...]
    prover_attempt_status: str
    prover_diagnostic_signature: str
    route_revision_recommended: bool
    route_revision_reasons: tuple[str, ...]
    acceptance_status: str
    proof_evidence_status: str
    proof_evidence_boundary: str
    ok: bool
    errors: tuple[str, ...] = ()


def export_formalization_gap_planner_resource_response_ledger(
    formalization_gap_planner_resource_request_queue_dir: Path,
    out_dir: Path | None = None,
    *,
    response_jsonl: Path | None = None,
) -> dict[str, object]:
    """Validate resource responses against resource-request queue rows."""

    errors: list[str] = []
    request_queue_dir = formalization_gap_planner_resource_request_queue_dir
    request_manifest_path = (
        request_queue_dir
        / "formalization_gap_planner_resource_request_queue_manifest.json"
    )
    request_manifest = _read_json(request_manifest_path, errors)
    if request_manifest.get("component_name") != (
        "formalization_gap_planner_resource_request_queue"
    ):
        errors.append("input manifest is not the resource request-queue component")
    if request_manifest.get("resource_request_queue_row_schema", {}).get(
        "$id"
    ) != RESOURCE_REQUEST_QUEUE_ROW_SCHEMA_ID:
        errors.append("input manifest resource request-queue row schema id mismatch")

    request_rows = [
        row for row in request_manifest.get("rows", []) if isinstance(row, dict)
    ]
    response_jsonl_path = (
        response_jsonl
        if response_jsonl is not None
        else request_queue_dir
        / "formalization_gap_planner_resource_responses.jsonl"
    )
    responses, response_file_exists = _read_response_jsonl(response_jsonl_path, errors)
    response_schema = resource_response_json_schema()
    response_schema_errors = [
        validate_resource_response_row(response, response_schema)
        for response in responses
    ]
    response_by_request = _response_index(responses, request_rows, errors)
    rows = tuple(
        _ledger_row(
            request_row,
            response=response_by_request.get(str(request_row.get("resource_request_id", ""))),
        )
        for request_row in request_rows
    )
    row_dicts = [asdict(row) for row in rows]
    ledger_schema = resource_response_ledger_row_json_schema()
    ledger_schema_errors = [
        validate_resource_response_ledger_row(row, ledger_schema) for row in row_dicts
    ]
    n_response_schema_valid = sum(
        1 for row_errors in response_schema_errors if not row_errors
    )
    n_ledger_row_schema_valid = sum(
        1 for row_errors in ledger_schema_errors if not row_errors
    )
    by_acceptance_status = Counter(row.acceptance_status for row in rows)
    by_resource_id = Counter(row.resource_id for row in rows)
    by_expected_artifact = Counter(row.expected_response_artifact for row in rows)
    target_summary = target_prover_family_summary(
        rows,
        fallback_target_prover_family=request_manifest.get("target_prover_family", ""),
    )
    payload: dict[str, object] = {
        "schema_version": (
            FORMALIZATION_GAP_PLANNER_RESOURCE_RESPONSE_LEDGER_SCHEMA_VERSION
        ),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "component_name": "formalization_gap_planner_resource_response_ledger",
        "source_components": (str(request_manifest.get("component_name", "")),),
        "resource_request_queue_dir": str(request_queue_dir),
        "resource_request_queue_manifest": str(request_manifest_path),
        "response_jsonl": str(response_jsonl_path),
        "response_jsonl_exists": response_file_exists,
        "target_prover_family": target_summary["target_prover_family"],
        "n_target_prover_families": target_summary["n_target_prover_families"],
        "by_target_prover_family": target_summary["by_target_prover_family"],
        "library_snapshot_ref": str(request_manifest.get("library_snapshot_ref", "")),
        "n_resource_requests": len(request_rows),
        "n_input_responses": len(responses),
        "n_response_schema_valid": n_response_schema_valid,
        "n_response_schema_invalid": len(response_schema_errors)
        - n_response_schema_valid,
        "n_ledger_rows": len(rows),
        "n_ledger_row_schema_valid": n_ledger_row_schema_valid,
        "n_ledger_row_schema_invalid": len(ledger_schema_errors)
        - n_ledger_row_schema_valid,
        "n_response_present": sum(1 for row in rows if row.response_present),
        "n_awaiting_response": by_acceptance_status.get(
            "AWAITING_RESOURCE_RESPONSE",
            0,
        ),
        "n_response_contract_minimum_met": sum(
            1 for row in rows if row.response_contract_minimum_met
        ),
        "n_response_contract_ok": sum(1 for row in rows if row.response_contract_ok),
        "n_request_playbook_present": sum(
            1 for row in rows if row.request_playbook_present
        ),
        "n_response_playbook_grounded": sum(
            1 for row in rows if row.response_playbook_grounded
        ),
        "n_response_playbook_grounding_failures": sum(
            1
            for row in rows
            if row.response_present
            and row.request_playbook_present
            and not row.response_playbook_grounded
        ),
        "n_missing_response_contract_field_rows": sum(
            1
            for row in rows
            if row.response_present and row.missing_response_contract_fields
        ),
        "n_response_request_mismatches": by_acceptance_status.get(
            "REJECTED_RESPONSE_REQUEST_MISMATCH",
            0,
        ),
        "n_with_dispatch_specs": sum(1 for row in rows if row.dispatch_spec),
        "n_with_resource_contract_ids": sum(
            1 for row in rows if row.resource_contract_ids
        ),
        "n_with_stop_conditions": sum(1 for row in rows if row.stop_conditions),
        "n_with_quality_controls": sum(1 for row in rows if row.quality_controls),
        "n_with_candidate_declaration_rows": sum(
            1 for row in rows if row.candidate_declaration_rows
        ),
        "n_candidate_declaration_rows": sum(
            len(row.candidate_declaration_rows) for row in rows
        ),
        "n_rows_with_target_primitives": sum(
            1 for row in rows if row.target_primitives
        ),
        "n_target_primitives": sum(len(row.target_primitives) for row in rows),
        "n_route_revision_recommended": sum(
            1 for row in rows if row.route_revision_recommended
        ),
        "n_rejected": sum(
            count
            for status, count in by_acceptance_status.items()
            if status.startswith("REJECTED_")
        ),
        "n_ok": sum(1 for row in rows if row.ok),
        "all_ok": (
            not errors
            and bool(rows)
            and all(not row_errors for row_errors in response_schema_errors)
            and all(not row_errors for row_errors in ledger_schema_errors)
            and all(row.ok for row in rows)
        ),
        "errors": errors,
        "by_acceptance_status": dict(sorted(by_acceptance_status.items())),
        "by_resource_id": dict(sorted(by_resource_id.items())),
        "by_expected_response_artifact": dict(sorted(by_expected_artifact.items())),
        "rows": row_dicts,
        "resource_response_schema": response_schema,
        "resource_response_ledger_row_schema": ledger_schema,
        "resource_response_ledger_fingerprint": stable_hash(row_dicts),
        "proof_evidence_status": PROOF_EVIDENCE_STATUS,
        "proof_evidence_boundary": PROOF_EVIDENCE_BOUNDARY,
        "limitations": [
            "awaiting response rows are not failures because resource execution may be interactive or external",
            "accepted resource responses are planner feedback, not theorem proof evidence",
            "kernel proof claims are rejected in this layer and must be replayed by a target prover gate",
            "request rows carry resource-specific contract fields, so matched fields validate request-contract coverage rather than full semantic certification",
            "a present response must match at least one queued response_contract_field before it can be accepted",
            "present responses must echo the requested resource and expected artifact before they can be accepted",
            "present responses for request-playbook rows must overlap the bounded playbook ask before they can be accepted",
        ],
    }
    if out_dir is not None:
        out_dir.mkdir(parents=True, exist_ok=True)
        (
            out_dir
            / "formalization_gap_planner_resource_response_ledger_manifest.json"
        ).write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
        (
            out_dir / "formalization_gap_planner_resource_response_ledger.jsonl"
        ).write_text(
            "\n".join(json.dumps(row, sort_keys=True) for row in row_dicts)
            + ("\n" if rows else ""),
            encoding="utf-8",
        )
        (
            out_dir / "formalization_gap_planner_resource_response.schema.json"
        ).write_text(json.dumps(response_schema, indent=2), encoding="utf-8")
        (
            out_dir
            / "formalization_gap_planner_resource_response_ledger_row.schema.json"
        ).write_text(json.dumps(ledger_schema, indent=2), encoding="utf-8")
        (
            out_dir / "formalization_gap_planner_resource_response_ledger.md"
        ).write_text(
            _markdown_report(payload),
            encoding="utf-8",
        )
    return payload


def resource_response_json_schema() -> dict[str, object]:
    string_array = {"type": "array", "items": {"type": "string"}}
    object_array = {"type": "array", "items": {"type": "object"}}
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
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": RESOURCE_RESPONSE_SCHEMA_ID,
        "title": "Formalization gap planner resource response",
        "description": (
            "Generic local/frontier resource response contract for resource "
            "request queue rows. Responses are not theorem proof evidence."
        ),
        "type": "object",
        "additionalProperties": True,
        "required": [
            "resource_request_id",
            "resource_id",
            "response_payload",
            "proof_evidence_boundary",
        ],
        "properties": {
            "resource_request_id": {"type": "string", "minLength": 1},
            "resource_id": {"type": "string", "minLength": 1},
            "tool_name": {"type": "string"},
            "expected_response_artifact": {"type": "string"},
            "response_payload": {"type": "object"},
            "response_summary": {"type": "string"},
            "response_artifacts": string_array,
            "source_refs": string_array,
            "target_primitives": string_array,
            "route_evidence_nodes": object_array,
            "lean_declaration_hits": object_array,
            "candidate_declaration_rows": {
                "type": "array",
                "items": candidate_declaration_row_schema,
            },
            "coverage_updates": {"type": "object"},
            "prover_diagnostics": string_array,
            "residual_goals": string_array,
            "prover_attempt_status": {"type": "string"},
            "prover_diagnostic_signature": {"type": "string"},
            "route_revision_recommended": {"type": "boolean"},
            "route_revision_reasons": string_array,
            "kernel_verified": {"type": "boolean", "const": False},
            "proof_evidence_boundary": {
                "type": "string",
                "pattern": "not theorem proof evidence",
            },
        },
    }


def resource_response_ledger_row_json_schema() -> dict[str, object]:
    string_array = {"type": "array", "items": {"type": "string"}}
    object_array = {"type": "array", "items": {"type": "object"}}
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
        "resource_response_ledger_id",
        "resource_request_id",
        "action_resource_plan_id",
        "primitive_action_id",
        "coverage_map_id",
        "goal_plan_id",
        "route_id",
        "display_name",
        "primitive",
        "target_primitives",
        "coverage_bucket",
        "queue_action_kind",
        "target_prover_family",
        "library_snapshot_ref",
        "candidate_declaration_rows",
        "request_phase",
        "component_ids",
        "resource_id",
        "resource_contract_ids",
        "stop_conditions",
        "quality_controls",
        "expected_response_artifact",
        "acceptance_gate",
        "dispatch_spec",
        "response_present",
        "response_contract_fields",
        "response_contract_minimum_met",
        "response_contract_ok",
        "request_playbook_present",
        "response_playbook_grounded",
        "response_playbook_grounding_terms",
        "response_payload",
        "response_summary",
        "response_artifacts",
        "matched_response_contract_fields",
        "missing_response_contract_fields",
        "source_refs",
        "route_evidence_nodes",
        "lean_declaration_hits",
        "coverage_updates",
        "prover_diagnostics",
        "residual_goals",
        "prover_attempt_status",
        "prover_diagnostic_signature",
        "route_revision_recommended",
        "route_revision_reasons",
        "acceptance_status",
        "proof_evidence_status",
        "proof_evidence_boundary",
        "ok",
        "errors",
    ]
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": RESOURCE_RESPONSE_LEDGER_ROW_SCHEMA_ID,
        "title": "Formalization gap planner resource-response ledger row",
        "description": (
            "Validated response ledger row for one resource request. Rows are "
            "adapter evidence and planner feedback, not theorem proof evidence."
        ),
        "type": "object",
        "additionalProperties": False,
        "required": required,
        "properties": {
            "schema_version": {
                "type": "integer",
                "const": (
                    FORMALIZATION_GAP_PLANNER_RESOURCE_RESPONSE_LEDGER_SCHEMA_VERSION
                ),
            },
            "resource_response_ledger_id": {"type": "string", "minLength": 1},
            "resource_request_id": {"type": "string", "minLength": 1},
            "action_resource_plan_id": {"type": "string", "minLength": 1},
            "primitive_action_id": {"type": "string", "minLength": 1},
            "coverage_map_id": {"type": "string", "minLength": 1},
            "goal_plan_id": {"type": "string", "minLength": 1},
            "route_id": {"type": "string", "minLength": 1},
            "display_name": {"type": "string", "minLength": 1},
            "primitive": {"type": "string", "minLength": 1},
            "target_primitives": string_array,
            "coverage_bucket": {"type": "string", "minLength": 1},
            "queue_action_kind": {"type": "string", "minLength": 1},
            "target_prover_family": {"type": "string", "minLength": 1},
            "library_snapshot_ref": {"type": "string", "minLength": 1},
            "candidate_declaration_rows": {
                "type": "array",
                "items": candidate_declaration_row_schema,
            },
            "request_phase": {"type": "string", "minLength": 1},
            "component_ids": string_array,
            "resource_id": {"type": "string", "minLength": 1},
            "resource_contract_ids": string_array,
            "stop_conditions": string_array,
            "quality_controls": {"type": "object"},
            "expected_response_artifact": {"type": "string", "minLength": 1},
            "acceptance_gate": {"type": "string", "minLength": 1},
            "dispatch_spec": {"type": "object"},
            "response_present": {"type": "boolean"},
            "response_contract_fields": string_array,
            "response_contract_minimum_met": {"type": "boolean"},
            "response_contract_ok": {"type": "boolean"},
            "request_playbook_present": {"type": "boolean"},
            "response_playbook_grounded": {"type": "boolean"},
            "response_playbook_grounding_terms": string_array,
            "response_payload": {"type": "object"},
            "response_summary": {"type": "string"},
            "response_artifacts": string_array,
            "matched_response_contract_fields": string_array,
            "missing_response_contract_fields": string_array,
            "source_refs": string_array,
            "route_evidence_nodes": object_array,
            "lean_declaration_hits": object_array,
            "coverage_updates": {"type": "object"},
            "prover_diagnostics": string_array,
            "residual_goals": string_array,
            "prover_attempt_status": {"type": "string"},
            "prover_diagnostic_signature": {"type": "string"},
            "route_revision_recommended": {"type": "boolean"},
            "route_revision_reasons": string_array,
            "acceptance_status": {"type": "string", "minLength": 1},
            "proof_evidence_status": {"type": "string", "const": PROOF_EVIDENCE_STATUS},
            "proof_evidence_boundary": {
                "type": "string",
                "pattern": "not theorem proof evidence",
            },
            "ok": {"type": "boolean"},
            "errors": string_array,
        },
    }


def validate_resource_response_row(
    row: dict[str, object],
    schema: dict[str, object] | None = None,
) -> list[str]:
    if not isinstance(row, dict):
        return ["resource response row must be an object"]
    return _validate_with_schema(row, schema or resource_response_json_schema())


def validate_resource_response_ledger_row(
    row: dict[str, object],
    schema: dict[str, object] | None = None,
) -> list[str]:
    if not isinstance(row, dict):
        return ["resource response ledger row must be an object"]
    errors = _validate_with_schema(row, schema or resource_response_ledger_row_json_schema())
    if not _str_tuple(row.get("component_ids", [])):
        errors.append("component_ids must be non-empty")
    if not isinstance(row.get("dispatch_spec", {}), dict):
        errors.append("dispatch_spec must be object")
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
    if "not theorem proof evidence" not in str(
        row.get("proof_evidence_boundary", "")
    ).lower():
        errors.append("proof_evidence_boundary must say not theorem proof evidence")
    if (
        str(row.get("acceptance_status", "")).startswith("REJECTED_")
        and bool(row.get("response_contract_ok", False))
    ):
        errors.append("rejected resource response rows must not set response_contract_ok=true")
    return errors


def _ledger_row(
    request_row: dict[str, Any],
    *,
    response: dict[str, Any] | None,
) -> FormalizationGapPlannerResourceResponseLedgerRow:
    row_errors = list(validate_resource_request_queue_row(request_row))
    response_present = response is not None
    response_errors: list[str] = []
    if response_present:
        response_errors = validate_resource_response_row(response or {})
    response_payload = _dict_value(response, "response_payload") if response else {}
    response_values = _merged_response_values(response or {}, response_payload)
    response_request_errors = (
        _response_request_identity_errors(request_row, response or {}, response_payload)
        if response_present
        else []
    )
    matched_fields, missing_fields = _contract_field_matches(
        _str_tuple(request_row.get("response_contract_fields", [])),
        response_values,
    )
    response_contract_fields = _str_tuple(request_row.get("response_contract_fields", []))
    resource_contract_ids = _str_tuple(request_row.get("resource_contract_ids", []))
    stop_conditions = _str_tuple(request_row.get("stop_conditions", []))
    request_target_primitives = _request_target_primitives(request_row)
    request_playbook = _dict_value(request_row, "request_playbook")
    request_playbook_present = bool(request_playbook)
    quality_controls = _quality_controls_for_ledger_row(
        request_row,
        request_playbook,
        response_values,
    )
    response_contract_minimum_met = bool(matched_fields)
    kernel_claimed = _kernel_verified_claimed(response or {}, response_payload)
    route_revision_reasons = _str_tuple(response_values.get("route_revision_reasons", []))
    residual_goals = _str_tuple(response_values.get("residual_goals", []))
    prover_diagnostics = _str_tuple(response_values.get("prover_diagnostics", []))
    route_revision_recommended = bool(
        response_values.get("route_revision_recommended", False)
    ) or bool(residual_goals) or bool(route_revision_reasons)
    response_target_primitives = _str_tuple(response_values.get("target_primitives", []))
    target_primitives = response_target_primitives or request_target_primitives
    expanded_target_primitives = sorted(
        set(response_target_primitives) - set(request_target_primitives)
    )
    response_playbook_grounded, response_playbook_grounding_terms = (
        _response_playbook_grounding(request_playbook, response_values)
        if response_present and request_playbook_present
        else (False, tuple())
    )
    if response_present and kernel_claimed:
        row_errors.append("resource response claims kernel verification in a non-proof layer")
    if response_present and response_errors:
        row_errors.extend(f"response: {error}" for error in response_errors)
    if response_present and response_request_errors:
        row_errors.extend(response_request_errors)
    if response_present and not response_contract_minimum_met:
        row_errors.append(
            "resource response missing all queued response_contract_fields: "
            + ",".join(response_contract_fields)
        )
    if response_present and expanded_target_primitives:
        row_errors.append(
            "target_primitives must not expand beyond resource request target_primitives: "
            + ", ".join(expanded_target_primitives[:8])
        )
    if (
        response_present
        and request_playbook_present
        and response_contract_minimum_met
        and not response_playbook_grounded
    ):
        row_errors.append(
            "resource response is not grounded in request_playbook "
            "operator_prompt, input_summary, expected_response_fields, or acceptance_checklist"
        )
    response_contract_ok = (
        response_present
        and not response_errors
        and not response_request_errors
        and not kernel_claimed
        and response_contract_minimum_met
        and not expanded_target_primitives
        and (not request_playbook_present or response_playbook_grounded)
    )
    if not response_present:
        acceptance_status = "AWAITING_RESOURCE_RESPONSE"
    elif kernel_claimed:
        acceptance_status = "REJECTED_KERNEL_PROOF_CLAIM"
    elif response_errors:
        acceptance_status = "REJECTED_MALFORMED_RESOURCE_RESPONSE"
    elif response_request_errors:
        acceptance_status = "REJECTED_RESPONSE_REQUEST_MISMATCH"
    elif not matched_fields:
        acceptance_status = "REJECTED_MISSING_RESPONSE_CONTRACT_FIELDS"
    elif expanded_target_primitives:
        acceptance_status = "REJECTED_RESPONSE_TARGET_SCOPE_EXPANSION"
    elif request_playbook_present and not response_playbook_grounded:
        acceptance_status = "REJECTED_RESPONSE_NOT_GROUNDED_IN_REQUEST_PLAYBOOK"
    elif route_revision_recommended:
        acceptance_status = "ACCEPTED_WITH_ROUTE_REVISION"
    else:
        acceptance_status = "ACCEPTED_RESOURCE_RESPONSE"
    resource_request_id = str(request_row.get("resource_request_id", ""))
    source_refs = _str_tuple(response_values.get("source_refs", []))
    route_evidence_nodes = _dict_tuple(response_values.get("route_evidence_nodes", []))
    lean_declaration_hits = _dict_tuple(response_values.get("lean_declaration_hits", []))
    coverage_updates = {
        str(key): str(value)
        for key, value in _dict_value(response_values, "coverage_updates").items()
    }
    return FormalizationGapPlannerResourceResponseLedgerRow(
        schema_version=FORMALIZATION_GAP_PLANNER_RESOURCE_RESPONSE_LEDGER_SCHEMA_VERSION,
        resource_response_ledger_id="formalization_gap_planner_resource_response:"
        + stable_hash(
            [
                resource_request_id,
                str(request_row.get("resource_id", "")),
                response_present,
                acceptance_status,
            ]
        )[:20],
        resource_request_id=resource_request_id,
        action_resource_plan_id=str(request_row.get("action_resource_plan_id", "")),
        primitive_action_id=str(request_row.get("primitive_action_id", "")),
        coverage_map_id=str(request_row.get("coverage_map_id", "")),
        goal_plan_id=str(request_row.get("goal_plan_id", "")),
        route_id=str(request_row.get("route_id", "")),
        display_name=str(request_row.get("display_name", "")),
        primitive=str(request_row.get("primitive", "")),
        target_primitives=target_primitives,
        coverage_bucket=str(request_row.get("coverage_bucket", "")),
        queue_action_kind=str(request_row.get("queue_action_kind", "")),
        target_prover_family=str(request_row.get("target_prover_family", "")),
        library_snapshot_ref=str(request_row.get("library_snapshot_ref", "")),
        candidate_declaration_rows=_candidate_declaration_rows(
            request_row.get("candidate_declaration_rows", [])
        ),
        request_phase=str(request_row.get("request_phase", "")),
        component_ids=_str_tuple(request_row.get("component_ids", [])),
        resource_id=str(request_row.get("resource_id", "")),
        resource_contract_ids=resource_contract_ids,
        stop_conditions=stop_conditions,
        quality_controls=quality_controls,
        expected_response_artifact=str(request_row.get("expected_response_artifact", "")),
        acceptance_gate=str(request_row.get("acceptance_gate", "")),
        dispatch_spec=_dict_value(request_row, "dispatch_spec"),
        response_present=response_present,
        response_contract_fields=response_contract_fields,
        response_contract_minimum_met=response_contract_minimum_met,
        response_contract_ok=response_contract_ok,
        request_playbook_present=request_playbook_present,
        response_playbook_grounded=response_playbook_grounded,
        response_playbook_grounding_terms=response_playbook_grounding_terms,
        response_payload=response_payload,
        response_summary=str(response_values.get("response_summary", "")),
        response_artifacts=_str_tuple(response_values.get("response_artifacts", [])),
        matched_response_contract_fields=matched_fields,
        missing_response_contract_fields=missing_fields,
        source_refs=source_refs,
        route_evidence_nodes=route_evidence_nodes,
        lean_declaration_hits=lean_declaration_hits,
        coverage_updates=coverage_updates,
        prover_diagnostics=prover_diagnostics,
        residual_goals=residual_goals,
        prover_attempt_status=str(response_values.get("prover_attempt_status", "")),
        prover_diagnostic_signature=str(
            response_values.get("prover_diagnostic_signature", "")
        ),
        route_revision_recommended=route_revision_recommended,
        route_revision_reasons=route_revision_reasons,
        acceptance_status=acceptance_status,
        proof_evidence_status=PROOF_EVIDENCE_STATUS,
        proof_evidence_boundary=PROOF_EVIDENCE_BOUNDARY,
        ok=(not row_errors and not acceptance_status.startswith("REJECTED_")),
        errors=tuple(row_errors),
    )


def _response_index(
    responses: list[dict[str, Any]],
    request_rows: list[dict[str, Any]],
    errors: list[str],
) -> dict[str, dict[str, Any]]:
    request_ids = {str(row.get("resource_request_id", "")) for row in request_rows}
    indexed: dict[str, dict[str, Any]] = {}
    for response in responses:
        request_id = str(response.get("resource_request_id", ""))
        if request_id not in request_ids:
            errors.append(f"response references unknown resource_request_id: {request_id}")
            continue
        if request_id in indexed:
            errors.append(f"duplicate response for resource_request_id: {request_id}")
            continue
        indexed[request_id] = response
    return indexed


def _response_request_identity_errors(
    request_row: dict[str, Any],
    response: dict[str, Any],
    response_payload: dict[str, Any],
) -> list[str]:
    errors: list[str] = []
    expected_values = {
        "resource_request_id": str(request_row.get("resource_request_id", "")),
        "resource_id": str(request_row.get("resource_id", "")),
        "expected_response_artifact": str(
            request_row.get("expected_response_artifact", "")
        ),
    }
    for field_name, expected in expected_values.items():
        observed = response.get(field_name)
        if not _has_value(observed):
            if field_name == "expected_response_artifact":
                errors.append(
                    "response.expected_response_artifact required to match request"
                )
            continue
        if str(observed) != expected:
            errors.append(f"response.{field_name} must match request.{field_name}")
    for field_name, expected in expected_values.items():
        observed = response_payload.get(field_name)
        if _has_value(observed) and str(observed) != expected:
            errors.append(
                f"response_payload.{field_name} must match request.{field_name}"
            )
    response_dispatch_spec = response.get("dispatch_spec")
    payload_dispatch_spec = response_payload.get("dispatch_spec")
    request_dispatch_spec = _dict_value(request_row, "dispatch_spec")
    if isinstance(response_dispatch_spec, dict) and response_dispatch_spec != request_dispatch_spec:
        errors.append("response.dispatch_spec must match request.dispatch_spec")
    if isinstance(payload_dispatch_spec, dict) and payload_dispatch_spec != request_dispatch_spec:
        errors.append("response_payload.dispatch_spec must match request.dispatch_spec")
    request_declaration_rows = _candidate_declaration_rows(
        request_row.get("candidate_declaration_rows", [])
    )
    response_declaration_rows = _candidate_declaration_rows(
        response.get("candidate_declaration_rows", [])
    )
    payload_declaration_rows = _candidate_declaration_rows(
        response_payload.get("candidate_declaration_rows", [])
    )
    if response_declaration_rows and response_declaration_rows != request_declaration_rows:
        errors.append(
            "response.candidate_declaration_rows must match request.candidate_declaration_rows"
        )
    if payload_declaration_rows and payload_declaration_rows != request_declaration_rows:
        errors.append(
            "response_payload.candidate_declaration_rows must match request.candidate_declaration_rows"
        )
    return errors


def _read_response_jsonl(
    path: Path,
    errors: list[str],
) -> tuple[list[dict[str, Any]], bool]:
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return [], False
    rows: list[dict[str, Any]] = []
    for index, line in enumerate(text.splitlines(), start=1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except Exception as exc:
            errors.append(f"failed to parse response JSONL line {index}: {exc}")
            continue
        if isinstance(value, dict):
            rows.append(value)
        else:
            errors.append(f"response JSONL line {index} is not an object")
    return rows, True


def _contract_field_matches(
    contract_fields: tuple[str, ...],
    response_values: dict[str, Any],
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    matched: list[str] = []
    missing: list[str] = []
    for field in contract_fields:
        value = response_values.get(field)
        if _has_value(value):
            matched.append(field)
        else:
            missing.append(field)
    return tuple(matched), tuple(missing)


def _merged_response_values(
    response: dict[str, Any],
    response_payload: dict[str, Any],
) -> dict[str, Any]:
    values = dict(response_payload)
    for key, value in response.items():
        if key not in values and key != "response_payload":
            values[key] = value
    return values


def _request_target_primitives(request_row: dict[str, Any]) -> tuple[str, ...]:
    explicit = _str_tuple(request_row.get("target_primitives", []))
    primitive = str(request_row.get("primitive", "")).strip()
    return tuple(dict.fromkeys([*explicit, *([primitive] if primitive else [])]))


def _quality_controls_for_ledger_row(
    request_row: dict[str, Any],
    request_playbook: dict[str, Any],
    response_values: dict[str, Any],
) -> dict[str, tuple[str, ...]]:
    return _merge_quality_controls(
        _quality_controls_from_payload(request_row),
        _quality_controls_from_payload(request_playbook),
        _quality_controls_from_payload(response_values),
        _quality_controls_from_payload(response_values.get("quality_controls", {})),
    )


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


def _response_playbook_grounding(
    request_playbook: dict[str, Any],
    response_values: dict[str, Any],
) -> tuple[bool, tuple[str, ...]]:
    playbook_tokens = _grounding_tokens(
        " ".join(
            [
                str(request_playbook.get("operator_prompt", "")),
                str(request_playbook.get("expected_response_artifact", "")),
                " ".join(_str_tuple(request_playbook.get("required_inputs", []))),
                " ".join(
                    _str_tuple(request_playbook.get("expected_response_fields", []))
                ),
                " ".join(_str_tuple(request_playbook.get("acceptance_checklist", []))),
                " ".join(_str_tuple(request_playbook.get("rejection_triggers", []))),
                " ".join(_str_tuple(request_playbook.get("stop_conditions", []))),
                json.dumps(_dict_value(request_playbook, "input_summary"), default=str),
            ]
        )
    )
    response_tokens = _grounding_tokens(
        " ".join(
            [
                str(response_values.get("response_summary", "")),
                " ".join(_str_tuple(response_values.get("source_refs", []))),
                json.dumps(
                    _dict_tuple(response_values.get("route_evidence_nodes", [])),
                    default=str,
                ),
                json.dumps(
                    _dict_tuple(response_values.get("lean_declaration_hits", [])),
                    default=str,
                ),
                json.dumps(_dict_value(response_values, "coverage_updates"), default=str),
                " ".join(_str_tuple(response_values.get("prover_diagnostics", []))),
                " ".join(_str_tuple(response_values.get("residual_goals", []))),
                " ".join(
                    _str_tuple(response_values.get("route_revision_reasons", []))
                ),
                str(response_values.get("prover_attempt_status", "")),
                str(response_values.get("prover_diagnostic_signature", "")),
            ]
        )
    )
    overlap = tuple(sorted(playbook_tokens & response_tokens))
    return (bool(overlap), overlap)


def _grounding_tokens(text: str) -> set[str]:
    stopwords = {
        "action",
        "adapter",
        "artifact",
        "check",
        "claim",
        "contract",
        "dispatch",
        "evidence",
        "expected",
        "field",
        "fields",
        "found",
        "gate",
        "grounded",
        "informal",
        "literature",
        "node",
        "nodes",
        "planner",
        "prompt",
        "query",
        "queued",
        "refs",
        "request",
        "response",
        "resource",
        "route",
        "search",
        "source",
        "theorem",
        "tool",
    }
    tokens: set[str] = set()
    for token in re.findall(r"[a-z0-9_]+", str(text or "").lower()):
        if len(token) < 4 or token in stopwords:
            continue
        tokens.add(token)
        for part in token.split("_"):
            if len(part) >= 4 and part not in stopwords:
                tokens.add(part)
    return tokens


def _kernel_verified_claimed(
    response: dict[str, Any],
    response_payload: dict[str, Any],
) -> bool:
    return bool(response.get("kernel_verified")) or bool(
        response_payload.get("kernel_verified")
    )


def _has_value(value: Any) -> bool:
    if value is None:
        return False
    if value is False:
        return False
    if isinstance(value, (str, list, tuple, dict, set)):
        return bool(value)
    return True


def _validate_with_schema(
    row: dict[str, object],
    schema: dict[str, object],
) -> list[str]:
    required = tuple(schema.get("required", ()))
    errors: list[str] = []
    for field_name in required:
        if field_name not in row:
            errors.append(f"{field_name} required")
    properties = schema.get("properties", {})
    if isinstance(properties, dict):
        for field_name, field_schema in properties.items():
            if field_name in row and isinstance(field_schema, dict):
                errors.extend(
                    _schema_property_errors(field_name, row[field_name], field_schema)
                )
    if schema.get("additionalProperties") is False:
        allowed = set(required)
        for field_name in row:
            if field_name not in allowed:
                errors.append(f"{field_name} unexpected")
    if "proof_evidence_boundary" in row and "not theorem proof evidence" not in str(
        row.get("proof_evidence_boundary", "")
    ).lower():
        errors.append("proof_evidence_boundary must say not theorem proof evidence")
    return errors


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
        const = schema.get("const")
        if const is not None and value != const:
            errors.append(f"{field_name} must equal {const}")
    elif expected_type == "array":
        if not isinstance(value, (list, tuple)):
            errors.append(f"{field_name} must be array")
            return errors
        item_schema = schema.get("items", {})
        if isinstance(item_schema, dict) and item_schema.get("type") == "string":
            for index, item in enumerate(value):
                if not isinstance(item, str):
                    errors.append(f"{field_name}[{index}] must be string")
        if isinstance(item_schema, dict) and item_schema.get("type") == "object":
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
    enum = schema.get("enum")
    if isinstance(enum, list) and value not in enum:
        errors.append(f"{field_name} must be one of {enum}")
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


def _dict_tuple(values: Any) -> tuple[dict[str, object], ...]:
    if isinstance(values, dict):
        return (values,)
    if not isinstance(values, (list, tuple)):
        return tuple()
    return tuple(value for value in values if isinstance(value, dict))


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


def _dict_value(row: dict[str, Any], key: str) -> dict[str, Any]:
    value = row.get(key, {})
    return value if isinstance(value, dict) else {}


def _markdown_report(payload: dict[str, object]) -> str:
    lines = [
        "# Formalization Gap Planner Resource Response Ledger",
        "",
        f"- Ledger rows: {payload.get('n_ok')}/{payload.get('n_ledger_rows')}",
        f"- Target prover family: {payload.get('target_prover_family')}",
        f"- Target prover families: {payload.get('n_target_prover_families')}",
        f"- Input responses: {payload.get('n_input_responses')}",
        f"- Responses present: {payload.get('n_response_present')}",
        f"- Awaiting responses: {payload.get('n_awaiting_response')}",
        f"- Contract minimum met: {payload.get('n_response_contract_minimum_met')}",
        f"- Contract OK: {payload.get('n_response_contract_ok')}",
        f"- Rows with missing contract fields: {payload.get('n_missing_response_contract_field_rows')}",
        f"- Request mismatches: {payload.get('n_response_request_mismatches')}",
        f"- Route revisions recommended: {payload.get('n_route_revision_recommended')}",
        f"- Rejected: {payload.get('n_rejected')}",
        f"- All OK: {payload.get('all_ok')}",
        "",
        "## Boundary",
        "",
        str(payload.get("proof_evidence_boundary", PROOF_EVIDENCE_BOUNDARY)),
        "",
        "## Acceptance Status",
        "",
    ]
    for status, count in sorted((payload.get("by_acceptance_status", {}) or {}).items()):
        lines.append(f"- `{status}`: {count}")
    return "\n".join(lines) + "\n"
