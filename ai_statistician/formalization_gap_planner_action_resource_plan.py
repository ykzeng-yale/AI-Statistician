from __future__ import annotations

import json
import re
from collections.abc import Iterable
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .fingerprint import stable_hash
from .formalization_gap_planner_component_resource_registry import (
    COMPONENT_RESOURCE_CONTRACT_ROW_SCHEMA_ID,
    COMPONENT_RESOURCE_EXECUTION_PLAN_SCHEMA_ID,
    COMPONENT_RESOURCE_REGISTRY_COMPONENT_ROW_SCHEMA_ID,
    COMPONENT_RESOURCE_REGISTRY_RESOURCE_ROW_SCHEMA_ID,
    validate_component_resource_contract_row,
    validate_component_resource_execution_plan_row,
    validate_component_resource_registry_component_row,
    validate_component_resource_registry_resource_row,
)
from .formalization_gap_planner_primitive_action_queue import (
    PRIMITIVE_ACTION_QUEUE_ROW_SCHEMA_ID,
    QUEUE_ACTION_KINDS,
    validate_primitive_action_queue_row,
)
from .formalization_gap_planner_target_summary import target_prover_family_summary


FORMALIZATION_GAP_PLANNER_ACTION_RESOURCE_PLAN_SCHEMA_VERSION = 1
ACTION_RESOURCE_PLAN_ROW_SCHEMA_ID = (
    "urn:ai-statistician:schemas:"
    "formalization-gap-planner-action-resource-plan-row:1"
)
PROOF_EVIDENCE_STATUS = (
    "FORMALIZATION_GAP_PLANNER_ACTION_RESOURCE_PLAN_NOT_PROOF_EVIDENCE"
)
PROOF_EVIDENCE_BOUNDARY = (
    "Formalization gap planner action-resource plan rows join primitive proof "
    "work orders to concrete local-first resources, frontier escalation tools, "
    "MCP or CLI adapters, and request/response contracts. They are resource "
    "execution plans, not theorem proof evidence."
)


ACTION_KIND_COMPONENT_IDS: dict[str, tuple[str, ...]] = {
    "target_prover_replay": (
        "cross_prover_public_reuse",
        "prover_feedback_refinement",
    ),
    "compose_existing_declarations": (
        "formal_library_coverage_mapping",
        "prover_feedback_refinement",
    ),
    "write_wrapper": (
        "minimal_delta_and_or_planning",
        "prover_feedback_refinement",
    ),
    "prove_bridge_lemma": (
        "formal_library_coverage_mapping",
        "minimal_delta_and_or_planning",
        "prover_feedback_refinement",
    ),
    "source_port": (
        "literature_grounded_route_synthesis",
        "informal_route_dag_decomposition",
        "formal_library_coverage_mapping",
    ),
    "design_new_theory_fragment": (
        "minimal_delta_and_or_planning",
        "formal_library_coverage_mapping",
        "prover_feedback_refinement",
    ),
    "rerun_library_alignment": (
        "formal_library_coverage_mapping",
        "route_revision_handoff",
    ),
    "route_revision": (
        "route_revision_handoff",
        "prover_feedback_refinement",
    ),
}


@dataclass(frozen=True)
class FormalizationGapPlannerActionResourcePlanRow:
    schema_version: int
    action_resource_plan_id: str
    primitive_action_id: str
    coverage_map_id: str
    goal_plan_id: str
    route_id: str
    display_name: str
    primitive: str
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
    component_ids: tuple[str, ...]
    local_first_resource_ids: tuple[str, ...]
    frontier_escalation_resource_ids: tuple[str, ...]
    adapter_ids: tuple[str, ...]
    resource_contract_ids: tuple[str, ...]
    resource_contracts_by_resource: dict[str, tuple[str, ...]]
    request_contract_fields_by_resource: dict[str, tuple[str, ...]]
    response_contract_fields_by_resource: dict[str, tuple[str, ...]]
    request_contract_fields: tuple[str, ...]
    response_contract_fields: tuple[str, ...]
    actionable_work_items: tuple[str, ...]
    evidence_inputs: tuple[str, ...]
    expected_outputs: tuple[str, ...]
    escalation_triggers: tuple[str, ...]
    stop_conditions: tuple[str, ...]
    acceptance_gate: str
    reproduction_surface: str
    execution_commands: tuple[str, ...]
    resource_selection_reason: str
    proof_evidence_status: str
    proof_evidence_boundary: str
    ok: bool
    errors: tuple[str, ...] = ()


def export_formalization_gap_planner_action_resource_plan(
    formalization_gap_planner_primitive_action_queue_dir: Path,
    formalization_gap_planner_component_resource_registry_dir: Path,
    out_dir: Path | None = None,
) -> dict[str, object]:
    """Export concrete resource plans for primitive formalization actions."""

    errors: list[str] = []
    action_queue_dir = formalization_gap_planner_primitive_action_queue_dir
    component_resource_registry_dir = (
        formalization_gap_planner_component_resource_registry_dir
    )
    action_manifest_path = (
        action_queue_dir
        / "formalization_gap_planner_primitive_action_queue_manifest.json"
    )
    registry_manifest_path = (
        component_resource_registry_dir
        / "formalization_gap_planner_component_resource_registry_manifest.json"
    )
    action_manifest = _read_json(action_manifest_path, errors)
    registry_manifest = _read_json(registry_manifest_path, errors)

    if action_manifest.get("component_name") != (
        "formalization_gap_planner_primitive_action_queue"
    ):
        errors.append("input manifest is not the primitive action queue component")
    if action_manifest.get("primitive_action_queue_row_schema", {}).get(
        "$id"
    ) != PRIMITIVE_ACTION_QUEUE_ROW_SCHEMA_ID:
        errors.append("input manifest primitive action-queue row schema id mismatch")
    if registry_manifest.get("component_name") != (
        "formalization_gap_planner_component_resource_registry"
    ):
        errors.append(
            "input manifest is not the component-resource registry component"
        )
    if registry_manifest.get("component_row_schema", {}).get(
        "$id"
    ) != COMPONENT_RESOURCE_REGISTRY_COMPONENT_ROW_SCHEMA_ID:
        errors.append("component-resource registry component-row schema id mismatch")
    if registry_manifest.get("resource_row_schema", {}).get(
        "$id"
    ) != COMPONENT_RESOURCE_REGISTRY_RESOURCE_ROW_SCHEMA_ID:
        errors.append("component-resource registry resource-row schema id mismatch")
    if registry_manifest.get("execution_plan_row_schema", {}).get(
        "$id"
    ) != COMPONENT_RESOURCE_EXECUTION_PLAN_SCHEMA_ID:
        errors.append("component-resource registry execution-plan schema id mismatch")
    if registry_manifest.get("resource_contract_row_schema", {}).get(
        "$id"
    ) != COMPONENT_RESOURCE_CONTRACT_ROW_SCHEMA_ID:
        errors.append("component-resource registry contract-row schema id mismatch")

    action_rows = [
        row for row in action_manifest.get("rows", []) if isinstance(row, dict)
    ]
    registry = _registry_indexes(registry_manifest)
    rows = tuple(_action_resource_plan_row(row, registry) for row in action_rows)
    row_dicts = [asdict(row) for row in rows]
    row_schema = action_resource_plan_row_json_schema()
    row_schema_errors = [
        validate_action_resource_plan_row(row, row_schema) for row in row_dicts
    ]
    n_row_schema_valid = sum(1 for row_errors in row_schema_errors if not row_errors)
    n_row_schema_invalid = len(row_schema_errors) - n_row_schema_valid
    by_action_kind = Counter(row.queue_action_kind for row in rows)
    target_summary = target_prover_family_summary(
        rows,
        fallback_target_prover_family=action_manifest.get("target_prover_family", ""),
    )
    payload: dict[str, object] = {
        "schema_version": (
            FORMALIZATION_GAP_PLANNER_ACTION_RESOURCE_PLAN_SCHEMA_VERSION
        ),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "component_name": "formalization_gap_planner_action_resource_plan",
        "source_components": (
            str(action_manifest.get("component_name", "")),
            str(registry_manifest.get("component_name", "")),
        ),
        "primitive_action_queue_dir": str(action_queue_dir),
        "primitive_action_queue_manifest": str(action_manifest_path),
        "component_resource_registry_dir": str(component_resource_registry_dir),
        "component_resource_registry_manifest": str(registry_manifest_path),
        "target_prover_family": target_summary["target_prover_family"],
        "n_target_prover_families": target_summary["n_target_prover_families"],
        "by_target_prover_family": target_summary["by_target_prover_family"],
        "library_snapshot_ref": str(action_manifest.get("library_snapshot_ref", "")),
        "n_action_rows": len(action_rows),
        "n_resource_plan_rows": len(rows),
        "n_ok": sum(1 for row in rows if row.ok),
        "n_failed": sum(1 for row in rows if not row.ok),
        "n_with_local_first_resources": sum(
            1 for row in rows if row.local_first_resource_ids
        ),
        "n_with_frontier_escalation_resources": sum(
            1 for row in rows if row.frontier_escalation_resource_ids
        ),
        "n_with_resource_contracts": sum(
            1 for row in rows if row.resource_contract_ids
        ),
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
        "n_row_schema_valid": n_row_schema_valid,
        "n_row_schema_invalid": n_row_schema_invalid,
        "n_target_prover_replay": by_action_kind.get("target_prover_replay", 0),
        "n_compose_existing_declarations": by_action_kind.get(
            "compose_existing_declarations",
            0,
        ),
        "n_write_wrapper": by_action_kind.get("write_wrapper", 0),
        "n_prove_bridge_lemma": by_action_kind.get("prove_bridge_lemma", 0),
        "n_source_port": by_action_kind.get("source_port", 0),
        "n_design_new_theory_fragment": by_action_kind.get(
            "design_new_theory_fragment",
            0,
        ),
        "n_rerun_library_alignment": by_action_kind.get(
            "rerun_library_alignment",
            0,
        ),
        "action_resource_plan_row_schema": row_schema,
        "by_action_kind": dict(sorted(by_action_kind.items())),
        "rows": row_dicts,
        "all_ok": (
            not errors
            and bool(rows)
            and all(row.ok for row in rows)
            and n_row_schema_invalid == 0
        ),
        "errors": errors,
        "action_resource_plan_fingerprint": stable_hash(row_dicts),
        "proof_evidence_status": PROOF_EVIDENCE_STATUS,
        "proof_evidence_boundary": PROOF_EVIDENCE_BOUNDARY,
        "limitations": [
            "action-resource plans route work to tools and contracts, not theorem proof evidence",
            "frontier resources require deployment-specific credentials, licenses, or MCP configuration",
            "target-prover acceptance still requires kernel replay or a certified checker",
        ],
    }
    if out_dir is not None:
        out_dir.mkdir(parents=True, exist_ok=True)
        (
            out_dir
            / "formalization_gap_planner_action_resource_plan_manifest.json"
        ).write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
        (out_dir / "formalization_gap_planner_action_resource_plan.jsonl").write_text(
            "\n".join(json.dumps(row, sort_keys=True) for row in row_dicts)
            + ("\n" if rows else ""),
            encoding="utf-8",
        )
        (
            out_dir / "formalization_gap_planner_action_resource_plan_row.schema.json"
        ).write_text(json.dumps(row_schema, indent=2), encoding="utf-8")
        (out_dir / "formalization_gap_planner_action_resource_plan.md").write_text(
            _markdown_report(payload),
            encoding="utf-8",
        )
    return payload


def action_resource_plan_row_json_schema() -> dict[str, object]:
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
        "action_resource_plan_id",
        "primitive_action_id",
        "coverage_map_id",
        "goal_plan_id",
        "route_id",
        "display_name",
        "primitive",
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
        "actionable_work_items",
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
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": ACTION_RESOURCE_PLAN_ROW_SCHEMA_ID,
        "title": "Formalization gap planner action-resource plan row",
        "description": (
            "Per-primitive local-first/frontier-escalation resource plan. Rows "
            "bind proof work orders to component resources and contracts, but "
            "are not theorem proof evidence."
        ),
        "type": "object",
        "additionalProperties": False,
        "required": required,
        "properties": {
            "schema_version": {
                "type": "integer",
                "const": (
                    FORMALIZATION_GAP_PLANNER_ACTION_RESOURCE_PLAN_SCHEMA_VERSION
                ),
            },
            "action_resource_plan_id": {"type": "string", "minLength": 1},
            "primitive_action_id": {"type": "string", "minLength": 1},
            "coverage_map_id": {"type": "string", "minLength": 1},
            "goal_plan_id": {"type": "string", "minLength": 1},
            "route_id": {"type": "string", "minLength": 1},
            "display_name": {"type": "string", "minLength": 1},
            "primitive": {"type": "string", "minLength": 1},
            "coverage_bucket": {"type": "string", "minLength": 1},
            "queue_action_kind": {"type": "string", "enum": list(QUEUE_ACTION_KINDS)},
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
            "component_ids": string_array,
            "local_first_resource_ids": string_array,
            "frontier_escalation_resource_ids": string_array,
            "adapter_ids": string_array,
            "resource_contract_ids": string_array,
            "resource_contracts_by_resource": {
                "type": "object",
                "additionalProperties": string_array,
            },
            "request_contract_fields_by_resource": {
                "type": "object",
                "additionalProperties": string_array,
            },
            "response_contract_fields_by_resource": {
                "type": "object",
                "additionalProperties": string_array,
            },
            "request_contract_fields": string_array,
            "response_contract_fields": string_array,
            "actionable_work_items": string_array,
            "evidence_inputs": string_array,
            "expected_outputs": string_array,
            "escalation_triggers": string_array,
            "stop_conditions": string_array,
            "acceptance_gate": {"type": "string", "minLength": 1},
            "reproduction_surface": {"type": "string", "minLength": 1},
            "execution_commands": string_array,
            "resource_selection_reason": {"type": "string", "minLength": 1},
            "proof_evidence_status": {"type": "string", "const": PROOF_EVIDENCE_STATUS},
            "proof_evidence_boundary": {
                "type": "string",
                "pattern": "not theorem proof evidence",
            },
            "ok": {"type": "boolean"},
            "errors": string_array,
        },
    }


def validate_action_resource_plan_row(
    row: dict[str, object],
    schema: dict[str, object] | None = None,
) -> list[str]:
    if not isinstance(row, dict):
        return ["action resource plan row must be an object"]
    row_schema = schema or action_resource_plan_row_json_schema()
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
    if not _str_tuple(row.get("local_first_resource_ids", [])):
        errors.append("local_first_resource_ids must be non-empty")
    if not _str_tuple(row.get("frontier_escalation_resource_ids", [])):
        errors.append("frontier_escalation_resource_ids must be non-empty")
    if not _str_tuple(row.get("resource_contract_ids", [])):
        errors.append("resource_contract_ids must be non-empty")
    selected_resources = set(
        _str_tuple(row.get("local_first_resource_ids", []))
    ) | set(_str_tuple(row.get("frontier_escalation_resource_ids", [])))
    for map_field in (
        "resource_contracts_by_resource",
        "request_contract_fields_by_resource",
        "response_contract_fields_by_resource",
    ):
        value = row.get(map_field, {})
        if not isinstance(value, dict):
            errors.append(f"{map_field} must be object")
            continue
        missing = sorted(resource_id for resource_id in selected_resources if resource_id not in value)
        if missing:
            errors.append(f"{map_field} missing resources: {','.join(missing)}")
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


def _registry_indexes(registry_manifest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    component_rows = [
        row
        for row in registry_manifest.get("component_rows", [])
        if isinstance(row, dict)
    ]
    execution_plan_rows = [
        row
        for row in registry_manifest.get("execution_plan_rows", [])
        if isinstance(row, dict)
    ]
    resource_rows = [
        row
        for row in registry_manifest.get("resource_rows", [])
        if isinstance(row, dict)
    ]
    resource_contract_rows = [
        row
        for row in registry_manifest.get("resource_contract_rows", [])
        if isinstance(row, dict)
    ]
    return {
        "components": {
            str(row.get("component_id", "")): row for row in component_rows
        },
        "execution_plans": {
            str(row.get("component_id", "")): row for row in execution_plan_rows
        },
        "resources": {
            str(row.get("resource_id", "")): row for row in resource_rows
        },
        "contracts": {
            str(row.get("resource_id", "")): row for row in resource_contract_rows
        },
    }


def _action_resource_plan_row(
    action_row: dict[str, Any],
    registry: dict[str, dict[str, Any]],
) -> FormalizationGapPlannerActionResourcePlanRow:
    row_errors = list(validate_primitive_action_queue_row(action_row))
    action_kind = str(action_row.get("queue_action_kind", ""))
    component_ids = ACTION_KIND_COMPONENT_IDS.get(action_kind, ())
    if not component_ids:
        row_errors.append(f"no component mapping for action kind: {action_kind}")

    component_index = registry.get("components", {})
    execution_plan_index = registry.get("execution_plans", {})
    resource_index = registry.get("resources", {})
    contract_index = registry.get("contracts", {})

    component_rows: list[dict[str, Any]] = []
    execution_plan_rows: list[dict[str, Any]] = []
    for component_id in component_ids:
        component_row = component_index.get(component_id)
        if component_row is None:
            row_errors.append(f"missing component row: {component_id}")
            continue
        component_errors = validate_component_resource_registry_component_row(
            component_row
        )
        row_errors.extend(
            f"component {component_id}: {error}" for error in component_errors
        )
        component_rows.append(component_row)
        execution_plan_row = execution_plan_index.get(component_id)
        if execution_plan_row is None:
            row_errors.append(f"missing execution plan row: {component_id}")
            continue
        execution_errors = validate_component_resource_execution_plan_row(
            execution_plan_row
        )
        row_errors.extend(
            f"execution plan {component_id}: {error}" for error in execution_errors
        )
        execution_plan_rows.append(execution_plan_row)

    local_first_resource_ids = _unique(
        resource_id
        for row in execution_plan_rows
        for resource_id in _str_tuple(row.get("local_first_resource_ids", []))
    )
    frontier_escalation_resource_ids = _unique(
        resource_id
        for row in execution_plan_rows
        for resource_id in _str_tuple(
            row.get("frontier_escalation_resource_ids", [])
        )
    )
    adapter_ids = _unique(
        adapter_id
        for row in execution_plan_rows
        for adapter_id in _str_tuple(row.get("adapter_ids", []))
    )
    target_prover_family = str(action_row.get("target_prover_family", ""))
    local_first_resource_ids = _target_compatible_resource_ids(
        local_first_resource_ids,
        resource_index,
        target_prover_family=target_prover_family,
    )
    frontier_escalation_resource_ids = _target_compatible_resource_ids(
        frontier_escalation_resource_ids,
        resource_index,
        target_prover_family=target_prover_family,
    )
    selected_resource_ids = _unique(
        (*local_first_resource_ids, *frontier_escalation_resource_ids)
    )
    for resource_id in selected_resource_ids:
        resource_row = resource_index.get(resource_id)
        if resource_row is None:
            row_errors.append(f"missing selected resource row: {resource_id}")
            continue
        resource_errors = validate_component_resource_registry_resource_row(
            resource_row
        )
        row_errors.extend(f"resource {resource_id}: {error}" for error in resource_errors)

    contract_rows: list[dict[str, Any]] = []
    for resource_id in selected_resource_ids:
        contract_row = contract_index.get(resource_id)
        if contract_row is None:
            row_errors.append(f"missing resource contract row: {resource_id}")
            continue
        contract_errors = validate_component_resource_contract_row(contract_row)
        row_errors.extend(f"contract {resource_id}: {error}" for error in contract_errors)
        contract_rows.append(contract_row)

    resource_contract_ids = _unique(
        str(row.get("resource_contract_id", "")) for row in contract_rows
    )
    resource_contracts_by_resource = {
        resource_id: _str_tuple(contract_index.get(resource_id, {}).get("resource_contract_id", ""))
        for resource_id in selected_resource_ids
    }
    request_contract_fields_by_resource = {
        resource_id: _str_tuple(
            contract_index.get(resource_id, {}).get("request_contract_fields", [])
        )
        for resource_id in selected_resource_ids
    }
    response_contract_fields_by_resource = {
        resource_id: _str_tuple(
            contract_index.get(resource_id, {}).get("response_contract_fields", [])
        )
        for resource_id in selected_resource_ids
    }
    request_contract_fields = _unique(
        field
        for row in contract_rows
        for field in _str_tuple(row.get("request_contract_fields", []))
    )
    response_contract_fields = _unique(
        field
        for row in contract_rows
        for field in _str_tuple(row.get("response_contract_fields", []))
    )
    evidence_inputs = _unique(
        (
            *_str_tuple(action_row.get("required_inputs", [])),
            *(
                field
                for row in execution_plan_rows
                for field in _str_tuple(row.get("evidence_inputs", []))
            ),
        )
    )
    expected_outputs = _unique(
        (
            *_str_tuple(action_row.get("expected_outputs", [])),
            *(
                field
                for row in execution_plan_rows
                for field in _str_tuple(row.get("expected_outputs", []))
            ),
        )
    )
    escalation_triggers = _unique(
        trigger
        for row in execution_plan_rows
        for trigger in _str_tuple(row.get("escalation_triggers", []))
    )
    stop_conditions = _unique(
        (
            *(
                condition
                for row in execution_plan_rows
                for condition in _str_tuple(row.get("stop_conditions", []))
            ),
            "primitive acceptance gate passes: "
            + str(action_row.get("acceptance_gate", "")),
        )
    )
    contract_gates = _unique(
        str(row.get("acceptance_gate", "")) for row in contract_rows
    )
    acceptance_gate = "; ".join(
        _unique(
            (
                "primitive gate: " + str(action_row.get("acceptance_gate", "")),
                *(f"resource gate: {gate}" for gate in contract_gates if gate),
            )
        )
    )
    reproduction_surface = "; ".join(
        _unique(str(row.get("reproduction_surface", "")) for row in execution_plan_rows)
    )
    execution_commands = _unique(action_row.get("execution_commands", []))
    resource_selection_reason = (
        f"{action_kind} uses planner components {', '.join(component_ids)}; "
        "component resources are filtered by the row target_prover_family before "
        "local-first resources, frontier escalation resources, adapter ids, and "
        "resource contracts are selected from the public registry"
    )
    primitive_action_id = str(action_row.get("primitive_action_id", ""))
    return FormalizationGapPlannerActionResourcePlanRow(
        schema_version=FORMALIZATION_GAP_PLANNER_ACTION_RESOURCE_PLAN_SCHEMA_VERSION,
        action_resource_plan_id="formalization_gap_planner_action_resource_plan:"
        + stable_hash(
            [
                primitive_action_id,
                action_kind,
                component_ids,
                local_first_resource_ids,
                frontier_escalation_resource_ids,
            ]
        )[:20],
        primitive_action_id=primitive_action_id,
        coverage_map_id=str(action_row.get("coverage_map_id", "")),
        goal_plan_id=str(action_row.get("goal_plan_id", "")),
        route_id=str(action_row.get("route_id", "")),
        display_name=str(action_row.get("display_name", "")),
        primitive=str(action_row.get("primitive", "")),
        coverage_bucket=str(action_row.get("coverage_bucket", "")),
        queue_action_kind=action_kind,
        priority_score=_bounded_int(action_row.get("priority_score", 0)),
        minimal_delta_cost_score=_bounded_int(
            action_row.get("minimal_delta_cost_score", 100)
        ),
        reuse_readiness_score=_bounded_int(action_row.get("reuse_readiness_score", 0)),
        evidence_readiness_score=_bounded_int(
            action_row.get("evidence_readiness_score", 0)
        ),
        priority_rationale=_str_tuple(action_row.get("priority_rationale", [])),
        target_prover_family=target_prover_family,
        library_snapshot_ref=str(action_row.get("library_snapshot_ref", "")),
        candidate_declaration_rows=_candidate_declaration_rows(action_row),
        component_ids=component_ids,
        local_first_resource_ids=local_first_resource_ids,
        frontier_escalation_resource_ids=frontier_escalation_resource_ids,
        adapter_ids=adapter_ids,
        resource_contract_ids=resource_contract_ids,
        resource_contracts_by_resource=resource_contracts_by_resource,
        request_contract_fields_by_resource=request_contract_fields_by_resource,
        response_contract_fields_by_resource=response_contract_fields_by_resource,
        request_contract_fields=request_contract_fields,
        response_contract_fields=response_contract_fields,
        actionable_work_items=_str_tuple(action_row.get("actionable_work_items", [])),
        evidence_inputs=evidence_inputs,
        expected_outputs=expected_outputs,
        escalation_triggers=escalation_triggers,
        stop_conditions=stop_conditions,
        acceptance_gate=acceptance_gate,
        reproduction_surface=reproduction_surface,
        execution_commands=execution_commands,
        resource_selection_reason=resource_selection_reason,
        proof_evidence_status=PROOF_EVIDENCE_STATUS,
        proof_evidence_boundary=PROOF_EVIDENCE_BOUNDARY,
        ok=bool(action_row.get("ok", False)) and not row_errors,
        errors=tuple(row_errors),
    )


def _target_compatible_resource_ids(
    resource_ids: tuple[str, ...],
    resource_index: dict[str, dict[str, Any]],
    *,
    target_prover_family: str,
) -> tuple[str, ...]:
    return _unique(
        resource_id
        for resource_id in resource_ids
        if _resource_supports_target(
            resource_index.get(resource_id, {}),
            target_prover_family=target_prover_family,
        )
    )


def _resource_supports_target(
    resource_row: dict[str, Any],
    *,
    target_prover_family: str,
) -> bool:
    target_key = _target_prover_key(target_prover_family)
    if not target_key:
        return True
    supported_targets = _str_tuple(resource_row.get("target_prover_families", []))
    if not supported_targets:
        return True
    supported_keys = {_target_prover_key(target) for target in supported_targets}
    supported_keys.discard("")
    return not supported_keys or target_key in supported_keys


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
    elif expected_type == "object":
        if not isinstance(value, dict):
            errors.append(f"{field_name} must be object")
            return errors
        additional = schema.get("additionalProperties")
        if isinstance(additional, dict) and additional.get("type") == "array":
            item_schema = additional.get("items", {})
            for key, items in value.items():
                if not isinstance(items, (list, tuple)):
                    errors.append(f"{field_name}.{key} must be array")
                    continue
                if isinstance(item_schema, dict) and item_schema.get("type") == "string":
                    for index, item in enumerate(items):
                        if not isinstance(item, str):
                            errors.append(f"{field_name}.{key}[{index}] must be string")
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


def _average_int(values: Any) -> int:
    items = [int(value) for value in values]
    if not items:
        return 0
    return round(sum(items) / len(items))


def _candidate_declaration_rows(
    action_row: dict[str, object],
) -> tuple[dict[str, object], ...]:
    rows: list[dict[str, object]] = []
    target_prover_family = str(action_row.get("target_prover_family", "")).strip()
    for item in _dict_tuple(action_row.get("candidate_declaration_rows", [])):
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
                    or target_prover_family
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


def _unique(values: Any) -> tuple[str, ...]:
    result: list[str] = []
    seen: set[str] = set()
    for value in _flatten_strings(values):
        if value and value not in seen:
            result.append(value)
            seen.add(value)
    return tuple(result)


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
        "# Formalization Gap Planner Action Resource Plan",
        "",
        f"- Resource plans: {payload.get('n_ok')}/{payload.get('n_resource_plan_rows')}",
        f"- Target prover family: {payload.get('target_prover_family')}",
        f"- Target prover families: {payload.get('n_target_prover_families')}",
        f"- Local-first coverage: {payload.get('n_with_local_first_resources')}",
        f"- Frontier escalation coverage: {payload.get('n_with_frontier_escalation_resources')}",
        f"- Resource-contract coverage: {payload.get('n_with_resource_contracts')}",
        f"- Rows with actionable work items: {payload.get('n_with_actionable_work_items')}",
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
            f"{payload.get('n_resource_plan_rows')}"
        ),
        f"- All OK: {payload.get('all_ok')}",
        "",
        "## Boundary",
        "",
        str(payload.get("proof_evidence_boundary", PROOF_EVIDENCE_BOUNDARY)),
        "",
        "## Action Kinds",
        "",
    ]
    for action_kind, count in sorted((payload.get("by_action_kind", {}) or {}).items()):
        lines.append(f"- `{action_kind}`: {count}")
    return "\n".join(lines) + "\n"
