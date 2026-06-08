from __future__ import annotations

import json
import re
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .fingerprint import stable_hash


FORMALIZATION_GAP_PLANNER_COMPONENT_RESOURCE_REGISTRY_SCHEMA_VERSION = 1
COMPONENT_RESOURCE_REGISTRY_RESOURCE_ROW_SCHEMA_ID = (
    "urn:ai-statistician:schemas:"
    "formalization-gap-planner-component-resource-registry-resource-row:1"
)
COMPONENT_RESOURCE_REGISTRY_COMPONENT_ROW_SCHEMA_ID = (
    "urn:ai-statistician:schemas:"
    "formalization-gap-planner-component-resource-registry-component-row:1"
)
COMPONENT_RESOURCE_EXECUTION_PLAN_SCHEMA_ID = (
    "urn:ai-statistician:schemas:"
    "formalization-gap-planner-component-execution-plan:1"
)
COMPONENT_RESOURCE_CONTRACT_ROW_SCHEMA_ID = (
    "urn:ai-statistician:schemas:"
    "formalization-gap-planner-component-resource-contract-row:1"
)
PROOF_EVIDENCE_STATUS = (
    "FORMALIZATION_GAP_PLANNER_COMPONENT_RESOURCE_REGISTRY_NOT_PROOF_EVIDENCE"
)
PROOF_EVIDENCE_BOUNDARY = (
    "Formalization gap planner component-resource registry rows describe "
    "which local fallbacks, frontier tools, MCP surfaces, and prover resources "
    "should feed each planner component. They are not theorem proof evidence."
)
PORTABLE_REUSE_TARGETS = ("lean4", "rocq", "isabelle", "agda")


@dataclass(frozen=True)
class FormalizationGapPlannerResourceRow:
    schema_version: int
    resource_id: str
    resource_name: str
    resource_kind: str
    surface: str
    role: str
    resource_urls: tuple[str, ...]
    local_dependency: bool
    online_dependency: bool
    mcp_compatible: bool
    target_prover_families: tuple[str, ...]
    evidence_contract: tuple[str, ...]
    capability_tags: tuple[str, ...]
    validation_signals: tuple[str, ...]
    proof_evidence_status: str
    proof_evidence_boundary: str
    ok: bool
    errors: tuple[str, ...] = ()


@dataclass(frozen=True)
class FormalizationGapPlannerComponentResourceRow:
    schema_version: int
    component_id: str
    component_name: str
    planner_stage: str
    role: str
    required_capabilities: tuple[str, ...]
    local_fallback_resource_ids: tuple[str, ...]
    frontier_resource_ids: tuple[str, ...]
    adapter_ids: tuple[str, ...]
    detected_adapter_statuses: dict[str, str]
    integration_contract_fields: tuple[str, ...]
    required_quality_signals: tuple[str, ...]
    evidence_inputs: tuple[str, ...]
    expected_outputs: tuple[str, ...]
    feedback_actions: tuple[str, ...]
    evaluation_hooks: tuple[str, ...]
    portable_to_prover_families: tuple[str, ...]
    readiness_summary: str
    proof_evidence_status: str
    proof_evidence_boundary: str
    ok: bool
    errors: tuple[str, ...] = ()


@dataclass(frozen=True)
class FormalizationGapPlannerComponentExecutionPlanRow:
    schema_version: int
    execution_plan_id: str
    component_id: str
    component_name: str
    planner_stage: str
    local_first_resource_ids: tuple[str, ...]
    frontier_escalation_resource_ids: tuple[str, ...]
    adapter_ids: tuple[str, ...]
    evidence_inputs: tuple[str, ...]
    expected_outputs: tuple[str, ...]
    quality_gates: tuple[str, ...]
    escalation_triggers: tuple[str, ...]
    stop_conditions: tuple[str, ...]
    reproduction_surface: str
    proof_evidence_status: str
    proof_evidence_boundary: str
    ok: bool
    errors: tuple[str, ...] = ()


@dataclass(frozen=True)
class FormalizationGapPlannerResourceContractRow:
    schema_version: int
    resource_contract_id: str
    resource_id: str
    resource_name: str
    resource_kind: str
    surface: str
    target_prover_families: tuple[str, ...]
    request_contract_fields: tuple[str, ...]
    response_contract_fields: tuple[str, ...]
    response_validation_signals: tuple[str, ...]
    acceptance_gate: str
    escalation_policy: str
    credential_or_installation_requirements: tuple[str, ...]
    output_artifact_kind: str
    proof_evidence_status: str
    proof_evidence_boundary: str
    ok: bool
    errors: tuple[str, ...] = ()


def export_formalization_gap_planner_component_resource_registry(
    out_dir: Path | None = None,
    *,
    formalization_gap_planner_adapter_registry_dir: Path | None = None,
) -> dict[str, object]:
    """Export the planner component-to-resource map for public reuse."""

    adapter_registry_manifest_path = (
        formalization_gap_planner_adapter_registry_dir
        / "formalization_gap_planner_adapter_registry_manifest.json"
        if formalization_gap_planner_adapter_registry_dir is not None
        else None
    )
    adapter_statuses = _adapter_statuses(adapter_registry_manifest_path)
    resources = tuple(_resource_row(spec) for spec in _resource_specs())
    resource_ids = {row.resource_id for row in resources}
    component_rows = tuple(
        _component_row(spec, resource_ids=resource_ids, adapter_statuses=adapter_statuses)
        for spec in _component_specs()
    )
    execution_plan_rows = tuple(
        _execution_plan_row(component_row, resource_ids=resource_ids)
        for component_row in component_rows
    )
    resource_contract_rows = tuple(_resource_contract_row(row) for row in resources)
    resource_row_dicts = [asdict(row) for row in resources]
    component_row_dicts = [asdict(row) for row in component_rows]
    execution_plan_row_dicts = [asdict(row) for row in execution_plan_rows]
    resource_contract_row_dicts = [asdict(row) for row in resource_contract_rows]
    resource_row_schema = component_resource_registry_resource_row_json_schema()
    component_row_schema = component_resource_registry_component_row_json_schema()
    execution_plan_schema = component_resource_execution_plan_json_schema()
    resource_contract_row_schema = component_resource_contract_row_json_schema()
    resource_row_schema_errors = [
        validate_component_resource_registry_resource_row(row, resource_row_schema)
        for row in resource_row_dicts
    ]
    component_row_schema_errors = [
        validate_component_resource_registry_component_row(row, component_row_schema)
        for row in component_row_dicts
    ]
    execution_plan_schema_errors = [
        validate_component_resource_execution_plan_row(row, execution_plan_schema)
        for row in execution_plan_row_dicts
    ]
    resource_contract_row_schema_errors = [
        validate_component_resource_contract_row(row, resource_contract_row_schema)
        for row in resource_contract_row_dicts
    ]
    n_resource_row_schema_valid = sum(
        1 for row_errors in resource_row_schema_errors if not row_errors
    )
    n_component_row_schema_valid = sum(
        1 for row_errors in component_row_schema_errors if not row_errors
    )
    n_execution_plan_row_schema_valid = sum(
        1 for row_errors in execution_plan_schema_errors if not row_errors
    )
    n_resource_contract_row_schema_valid = sum(
        1 for row_errors in resource_contract_row_schema_errors if not row_errors
    )
    by_resource_kind = Counter(row.resource_kind for row in resources)
    by_surface = Counter(row.surface for row in resources)
    by_capability_tag = Counter(
        tag for row in resources for tag in row.capability_tags
    )
    by_validation_signal = Counter(
        signal for row in resources for signal in row.validation_signals
    )
    payload: dict[str, object] = {
        "schema_version": FORMALIZATION_GAP_PLANNER_COMPONENT_RESOURCE_REGISTRY_SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "component_name": "formalization_gap_planner_component_resource_registry",
        "adapter_registry_manifest": str(adapter_registry_manifest_path or ""),
        "n_resources": len(resources),
        "n_resource_rows_ok": sum(1 for row in resources if row.ok),
        "n_resource_row_schema_valid": n_resource_row_schema_valid,
        "n_resource_row_schema_invalid": len(resource_row_schema_errors)
        - n_resource_row_schema_valid,
        "n_component_rows": len(component_rows),
        "n_component_rows_ok": sum(1 for row in component_rows if row.ok),
        "n_component_row_schema_valid": n_component_row_schema_valid,
        "n_component_row_schema_invalid": len(component_row_schema_errors)
        - n_component_row_schema_valid,
        "n_execution_plan_rows": len(execution_plan_rows),
        "n_execution_plan_rows_ok": sum(1 for row in execution_plan_rows if row.ok),
        "n_execution_plan_row_schema_valid": n_execution_plan_row_schema_valid,
        "n_execution_plan_row_schema_invalid": len(execution_plan_schema_errors)
        - n_execution_plan_row_schema_valid,
        "n_resource_contract_rows": len(resource_contract_rows),
        "n_resource_contract_rows_ok": sum(
            1 for row in resource_contract_rows if row.ok
        ),
        "n_resource_contract_row_schema_valid": n_resource_contract_row_schema_valid,
        "n_resource_contract_row_schema_invalid": len(
            resource_contract_row_schema_errors
        )
        - n_resource_contract_row_schema_valid,
        "n_local_fallback_resources": by_resource_kind.get("local_fallback", 0),
        "n_frontier_resources": sum(
            1 for row in resources if row.resource_kind in {"frontier_tool", "frontier_method"}
        ),
        "n_mcp_or_cli_resources": sum(
            1
            for row in resources
            if row.mcp_compatible
            or "mcp" in row.surface.lower()
            or "cli" in row.surface.lower()
        ),
        "n_online_resources": sum(1 for row in resources if row.online_dependency),
        "n_resources_with_capability_tags": sum(
            1 for row in resources if row.capability_tags
        ),
        "n_resources_with_validation_signals": sum(
            1 for row in resources if row.validation_signals
        ),
        "n_component_rows_with_required_quality_signals": sum(
            1 for row in component_rows if row.required_quality_signals
        ),
        "n_execution_plans_with_quality_gates": sum(
            1 for row in execution_plan_rows if row.quality_gates
        ),
        "n_resource_contracts_with_response_validation_signals": sum(
            1 for row in resource_contract_rows if row.response_validation_signals
        ),
        "by_resource_kind": dict(sorted(by_resource_kind.items())),
        "by_surface": dict(sorted(by_surface.items())),
        "by_capability_tag": dict(sorted(by_capability_tag.items())),
        "by_validation_signal": dict(sorted(by_validation_signal.items())),
        "portable_reuse_targets": PORTABLE_REUSE_TARGETS,
        "resource_row_schema": resource_row_schema,
        "component_row_schema": component_row_schema,
        "execution_plan_row_schema": execution_plan_schema,
        "resource_contract_row_schema": resource_contract_row_schema,
        "resource_rows": resource_row_dicts,
        "component_rows": component_row_dicts,
        "execution_plan_rows": execution_plan_row_dicts,
        "resource_contract_rows": resource_contract_row_dicts,
        "component_resource_registry_fingerprint": stable_hash(
            [
                resource_row_dicts,
                component_row_dicts,
                execution_plan_row_dicts,
                resource_contract_row_dicts,
            ]
        ),
        "all_ok": (
            bool(resources)
            and bool(component_rows)
            and bool(execution_plan_rows)
            and bool(resource_contract_rows)
            and all(row.ok for row in resources)
            and all(row.ok for row in component_rows)
            and all(row.ok for row in execution_plan_rows)
            and all(row.ok for row in resource_contract_rows)
            and len(resource_row_schema_errors) == n_resource_row_schema_valid
            and len(component_row_schema_errors) == n_component_row_schema_valid
            and len(execution_plan_schema_errors) == n_execution_plan_row_schema_valid
            and len(resource_contract_row_schema_errors)
            == n_resource_contract_row_schema_valid
        ),
        "errors": tuple(
            error
            for row in (
                *resources,
                *component_rows,
                *execution_plan_rows,
                *resource_contract_rows,
            )
            for error in row.errors
            if error
        ),
        "proof_evidence_status": PROOF_EVIDENCE_STATUS,
        "proof_evidence_boundary": PROOF_EVIDENCE_BOUNDARY,
        "usage_order": (
            "choose local fallback resources first for deterministic smoke tests",
            "use frontier literature resources when source coverage or route confidence is weak",
            "use formal-library resources before creating a new definition or bridge lemma",
            "feed proof-state resources bottom-up on route leaves and record residual goals",
            "revise the route only through accepted refinement evidence and replayable handoffs",
        ),
        "limitations": (
            "resource rows are integration guidance and readiness metadata, not tool outputs",
            "remote-resource availability and licensing must be checked in the deployment environment",
            "cross-prover reuse still requires a prover-family adapter and kernel replay",
        ),
    }
    if out_dir is not None:
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "formalization_gap_planner_component_resource_registry_manifest.json").write_text(
            json.dumps(payload, indent=2, default=str),
            encoding="utf-8",
        )
        (
            out_dir / "formalization_gap_planner_component_resource_resources.jsonl"
        ).write_text(
            "\n".join(json.dumps(row, sort_keys=True) for row in resource_row_dicts)
            + ("\n" if resource_row_dicts else ""),
            encoding="utf-8",
        )
        (out_dir / "formalization_gap_planner_component_resource_registry.jsonl").write_text(
            "\n".join(json.dumps(row, sort_keys=True) for row in component_row_dicts)
            + ("\n" if component_row_dicts else ""),
            encoding="utf-8",
        )
        (
            out_dir
            / "formalization_gap_planner_component_resource_execution_plans.jsonl"
        ).write_text(
            "\n".join(json.dumps(row, sort_keys=True) for row in execution_plan_row_dicts)
            + ("\n" if execution_plan_row_dicts else ""),
            encoding="utf-8",
        )
        (
            out_dir
            / "formalization_gap_planner_component_resource_contracts.jsonl"
        ).write_text(
            "\n".join(
                json.dumps(row, sort_keys=True)
                for row in resource_contract_row_dicts
            )
            + ("\n" if resource_contract_row_dicts else ""),
            encoding="utf-8",
        )
        (
            out_dir
            / "formalization_gap_planner_component_resource_resource_row.schema.json"
        ).write_text(
            json.dumps(resource_row_schema, indent=2),
            encoding="utf-8",
        )
        (
            out_dir
            / "formalization_gap_planner_component_resource_component_row.schema.json"
        ).write_text(
            json.dumps(component_row_schema, indent=2),
            encoding="utf-8",
        )
        (
            out_dir
            / "formalization_gap_planner_component_resource_execution_plan.schema.json"
        ).write_text(
            json.dumps(execution_plan_schema, indent=2),
            encoding="utf-8",
        )
        (
            out_dir
            / "formalization_gap_planner_component_resource_contract_row.schema.json"
        ).write_text(
            json.dumps(resource_contract_row_schema, indent=2),
            encoding="utf-8",
        )
        (out_dir / "formalization_gap_planner_component_resource_registry.md").write_text(
            _markdown_report(payload),
            encoding="utf-8",
        )
    return payload


def component_resource_execution_plan_json_schema() -> dict[str, object]:
    """JSON Schema for public component execution-plan rows."""

    string_array = {"type": "array", "items": {"type": "string"}}
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": COMPONENT_RESOURCE_EXECUTION_PLAN_SCHEMA_ID,
        "title": "Formalization Gap Planner Component Execution Plan",
        "description": (
            "Machine-readable local-first/frontier-escalation plan for one "
            "formalization-gap planner component. Rows are not theorem proof "
            "evidence."
        ),
        "type": "object",
        "additionalProperties": True,
        "required": [
            "schema_version",
            "execution_plan_id",
            "component_id",
            "component_name",
            "planner_stage",
            "local_first_resource_ids",
            "frontier_escalation_resource_ids",
            "evidence_inputs",
            "expected_outputs",
            "quality_gates",
            "escalation_triggers",
            "stop_conditions",
            "proof_evidence_status",
            "proof_evidence_boundary",
            "ok",
        ],
        "properties": {
            "schema_version": {
                "type": "integer",
                "const": FORMALIZATION_GAP_PLANNER_COMPONENT_RESOURCE_REGISTRY_SCHEMA_VERSION,
            },
            "execution_plan_id": {"type": "string", "minLength": 1},
            "component_id": {"type": "string", "minLength": 1},
            "component_name": {"type": "string", "minLength": 1},
            "planner_stage": {"type": "string", "minLength": 1},
            "local_first_resource_ids": string_array,
            "frontier_escalation_resource_ids": string_array,
            "adapter_ids": string_array,
            "evidence_inputs": string_array,
            "expected_outputs": string_array,
            "quality_gates": string_array,
            "escalation_triggers": string_array,
            "stop_conditions": string_array,
            "reproduction_surface": {"type": "string"},
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


def component_resource_contract_row_json_schema() -> dict[str, object]:
    """JSON Schema for public resource request/response contract rows."""

    string_array = {"type": "array", "items": {"type": "string"}}
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": COMPONENT_RESOURCE_CONTRACT_ROW_SCHEMA_ID,
        "title": "Formalization Gap Planner Component Resource Contract",
        "description": (
            "Machine-readable request/response and acceptance-gate contract "
            "for one local fallback, frontier tool, MCP surface, or prover "
            "resource. Rows are integration metadata, not theorem proof "
            "evidence."
        ),
        "type": "object",
        "additionalProperties": True,
        "required": [
            "schema_version",
            "resource_contract_id",
            "resource_id",
            "resource_name",
            "resource_kind",
            "surface",
            "target_prover_families",
            "request_contract_fields",
            "response_contract_fields",
            "response_validation_signals",
            "acceptance_gate",
            "escalation_policy",
            "credential_or_installation_requirements",
            "output_artifact_kind",
            "proof_evidence_status",
            "proof_evidence_boundary",
            "ok",
        ],
        "properties": {
            "schema_version": {
                "type": "integer",
                "const": FORMALIZATION_GAP_PLANNER_COMPONENT_RESOURCE_REGISTRY_SCHEMA_VERSION,
            },
            "resource_contract_id": {"type": "string", "minLength": 1},
            "resource_id": {"type": "string", "minLength": 1},
            "resource_name": {"type": "string", "minLength": 1},
            "resource_kind": {"type": "string", "minLength": 1},
            "surface": {"type": "string", "minLength": 1},
            "target_prover_families": string_array,
            "request_contract_fields": string_array,
            "response_contract_fields": string_array,
            "response_validation_signals": string_array,
            "acceptance_gate": {
                "type": "string",
                "pattern": "not theorem proof evidence",
            },
            "escalation_policy": {"type": "string", "minLength": 1},
            "credential_or_installation_requirements": string_array,
            "output_artifact_kind": {"type": "string", "minLength": 1},
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


def component_resource_registry_resource_row_json_schema() -> dict[str, object]:
    """JSON Schema for public planner resource rows."""

    string_array = {"type": "array", "items": {"type": "string"}}
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": COMPONENT_RESOURCE_REGISTRY_RESOURCE_ROW_SCHEMA_ID,
        "title": "Formalization Gap Planner Component Resource",
        "description": (
            "Reusable registry row describing one local fallback, frontier "
            "tool, MCP/CLI surface, or prover resource used by planner "
            "components. Rows are integration metadata, not theorem proof "
            "evidence."
        ),
        "type": "object",
        "additionalProperties": True,
        "required": [
            "schema_version",
            "resource_id",
            "resource_name",
            "resource_kind",
            "surface",
            "role",
            "resource_urls",
            "local_dependency",
            "online_dependency",
            "mcp_compatible",
            "target_prover_families",
            "evidence_contract",
            "capability_tags",
            "validation_signals",
            "proof_evidence_status",
            "proof_evidence_boundary",
            "ok",
        ],
        "properties": {
            "schema_version": {
                "type": "integer",
                "const": FORMALIZATION_GAP_PLANNER_COMPONENT_RESOURCE_REGISTRY_SCHEMA_VERSION,
            },
            "resource_id": {"type": "string", "minLength": 1},
            "resource_name": {"type": "string", "minLength": 1},
            "resource_kind": {"type": "string", "minLength": 1},
            "surface": {"type": "string", "minLength": 1},
            "role": {"type": "string", "minLength": 1},
            "resource_urls": string_array,
            "local_dependency": {"type": "boolean"},
            "online_dependency": {"type": "boolean"},
            "mcp_compatible": {"type": "boolean"},
            "target_prover_families": string_array,
            "evidence_contract": string_array,
            "capability_tags": string_array,
            "validation_signals": string_array,
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


def component_resource_registry_component_row_json_schema() -> dict[str, object]:
    """JSON Schema for public planner component rows."""

    string_array = {"type": "array", "items": {"type": "string"}}
    string_map = {"type": "object", "additionalProperties": {"type": "string"}}
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": COMPONENT_RESOURCE_REGISTRY_COMPONENT_ROW_SCHEMA_ID,
        "title": "Formalization Gap Planner Component Resource Mapping",
        "description": (
            "Reusable row mapping one planner component to local fallbacks, "
            "frontier resources, adapter ids, evidence inputs, expected "
            "outputs, and evaluation hooks. Rows are not theorem proof evidence."
        ),
        "type": "object",
        "additionalProperties": True,
        "required": [
            "schema_version",
            "component_id",
            "component_name",
            "planner_stage",
            "role",
            "required_capabilities",
            "local_fallback_resource_ids",
            "frontier_resource_ids",
            "adapter_ids",
            "detected_adapter_statuses",
            "integration_contract_fields",
            "required_quality_signals",
            "evidence_inputs",
            "expected_outputs",
            "feedback_actions",
            "evaluation_hooks",
            "portable_to_prover_families",
            "readiness_summary",
            "proof_evidence_status",
            "proof_evidence_boundary",
            "ok",
        ],
        "properties": {
            "schema_version": {
                "type": "integer",
                "const": FORMALIZATION_GAP_PLANNER_COMPONENT_RESOURCE_REGISTRY_SCHEMA_VERSION,
            },
            "component_id": {"type": "string", "minLength": 1},
            "component_name": {"type": "string", "minLength": 1},
            "planner_stage": {"type": "string", "minLength": 1},
            "role": {"type": "string", "minLength": 1},
            "required_capabilities": string_array,
            "local_fallback_resource_ids": string_array,
            "frontier_resource_ids": string_array,
            "adapter_ids": string_array,
            "detected_adapter_statuses": string_map,
            "integration_contract_fields": string_array,
            "required_quality_signals": string_array,
            "evidence_inputs": string_array,
            "expected_outputs": string_array,
            "feedback_actions": string_array,
            "evaluation_hooks": string_array,
            "portable_to_prover_families": string_array,
            "readiness_summary": {"type": "string", "minLength": 1},
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


def validate_component_resource_registry_resource_row(
    row: dict[str, Any],
    schema: dict[str, object] | None = None,
) -> tuple[str, ...]:
    """Validate a resource row against the published reusable schema."""

    return _validate_schema_row(
        row,
        schema or component_resource_registry_resource_row_json_schema(),
    )


def validate_component_resource_registry_component_row(
    row: dict[str, Any],
    schema: dict[str, object] | None = None,
) -> tuple[str, ...]:
    """Validate a component-resource row against the published reusable schema."""

    return _validate_schema_row(
        row,
        schema or component_resource_registry_component_row_json_schema(),
    )


def validate_component_resource_execution_plan_row(
    row: dict[str, Any],
    schema: dict[str, object] | None = None,
) -> tuple[str, ...]:
    """Validate an execution-plan row against the published reusable schema."""

    return _validate_schema_row(
        row,
        schema or component_resource_execution_plan_json_schema(),
    )


def validate_component_resource_contract_row(
    row: dict[str, Any],
    schema: dict[str, object] | None = None,
) -> tuple[str, ...]:
    """Validate a resource contract row against the published reusable schema."""

    return _validate_schema_row(
        row,
        schema or component_resource_contract_row_json_schema(),
    )


def _validate_schema_row(
    row: dict[str, Any],
    row_schema: dict[str, object],
) -> tuple[str, ...]:
    errors: list[str] = []
    if not isinstance(row, dict):
        return ("row must be object",)
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
                non_strings = [
                    idx for idx, item in enumerate(value) if not isinstance(item, str)
                ]
                if non_strings:
                    errors.append(
                        f"{field_name} items must be string at indexes "
                        + ",".join(str(idx) for idx in non_strings)
                    )
    elif expected_type == "object":
        if not isinstance(value, dict):
            errors.append(f"{field_name} must be object")
        else:
            additional = field_schema.get("additionalProperties")
            if isinstance(additional, dict) and additional.get("type") == "string":
                non_strings = [
                    key for key, item in value.items() if not isinstance(item, str)
                ]
                if non_strings:
                    errors.append(
                        f"{field_name} values must be string for keys "
                        + ",".join(str(key) for key in sorted(non_strings))
                    )
    if "const" in field_schema and value != field_schema["const"]:
        errors.append(f"{field_name} must equal {field_schema['const']!r}")
    pattern = field_schema.get("pattern")
    if isinstance(pattern, str) and isinstance(value, str):
        if re.search(pattern, value) is None:
            errors.append(f"{field_name} must match /{pattern}/")
    return tuple(errors)


def _resource_row(spec: dict[str, Any]) -> FormalizationGapPlannerResourceRow:
    errors = []
    for field_name in ("resource_id", "resource_name", "resource_kind", "surface", "role"):
        if not str(spec.get(field_name, "")):
            errors.append(f"{field_name} missing")
    if spec.get("online_dependency") or spec.get("mcp_compatible") or spec.get("resource_kind") in {
        "frontier_tool",
        "frontier_method",
    }:
        if not _str_tuple(spec.get("resource_urls", [])):
            errors.append("resource_urls missing for frontier/online resource")
    evidence_contract = _str_tuple(spec.get("evidence_contract", []))
    capability_tags = _resource_capability_tags(spec, evidence_contract)
    validation_signals = _resource_validation_signals(spec, evidence_contract)
    return FormalizationGapPlannerResourceRow(
        schema_version=FORMALIZATION_GAP_PLANNER_COMPONENT_RESOURCE_REGISTRY_SCHEMA_VERSION,
        resource_id=str(spec.get("resource_id", "")),
        resource_name=str(spec.get("resource_name", "")),
        resource_kind=str(spec.get("resource_kind", "")),
        surface=str(spec.get("surface", "")),
        role=str(spec.get("role", "")),
        resource_urls=_str_tuple(spec.get("resource_urls", [])),
        local_dependency=bool(spec.get("local_dependency", False)),
        online_dependency=bool(spec.get("online_dependency", False)),
        mcp_compatible=bool(spec.get("mcp_compatible", False)),
        target_prover_families=_str_tuple(
            spec.get("target_prover_families", PORTABLE_REUSE_TARGETS)
        ),
        evidence_contract=evidence_contract,
        capability_tags=capability_tags,
        validation_signals=validation_signals,
        proof_evidence_status=PROOF_EVIDENCE_STATUS,
        proof_evidence_boundary=PROOF_EVIDENCE_BOUNDARY,
        ok=not errors,
        errors=tuple(errors),
    )


def _resource_contract_row(
    row: FormalizationGapPlannerResourceRow,
) -> FormalizationGapPlannerResourceContractRow:
    response_fields = _str_tuple(row.evidence_contract)
    request_fields = _resource_request_contract_fields(row)
    requirements = _resource_requirements(row)
    response_validation_signals = _str_tuple(row.validation_signals)
    errors: list[str] = []
    if not request_fields:
        errors.append("request_contract_fields missing")
    if not response_fields:
        errors.append("response_contract_fields missing")
    if not requirements:
        errors.append("credential_or_installation_requirements missing")
    acceptance_gate = (
        "accept only schema-valid route evidence; this is not theorem proof "
        "evidence and any proof claim must wait for target-prover kernel replay"
    )
    return FormalizationGapPlannerResourceContractRow(
        schema_version=FORMALIZATION_GAP_PLANNER_COMPONENT_RESOURCE_REGISTRY_SCHEMA_VERSION,
        resource_contract_id="formalization_gap_planner_component_resource_contract:"
        + stable_hash(
            [
                row.resource_id,
                row.surface,
                request_fields,
                response_fields,
                row.target_prover_families,
            ]
        )[:20],
        resource_id=row.resource_id,
        resource_name=row.resource_name,
        resource_kind=row.resource_kind,
        surface=row.surface,
        target_prover_families=row.target_prover_families,
        request_contract_fields=request_fields,
        response_contract_fields=response_fields,
        response_validation_signals=response_validation_signals,
        acceptance_gate=acceptance_gate,
        escalation_policy=_resource_escalation_policy(row),
        credential_or_installation_requirements=requirements,
        output_artifact_kind=_resource_output_artifact_kind(row),
        proof_evidence_status=PROOF_EVIDENCE_STATUS,
        proof_evidence_boundary=PROOF_EVIDENCE_BOUNDARY,
        ok=not errors,
        errors=tuple(errors),
    )


def _resource_request_contract_fields(
    row: FormalizationGapPlannerResourceRow,
) -> tuple[str, ...]:
    fields = [
        "component_id",
        "route_id",
        "resource_id",
        "evidence_inputs",
        "proof_evidence_boundary",
    ]
    if row.target_prover_families != PORTABLE_REUSE_TARGETS:
        fields.extend(["target_prover_family", "library_snapshot_ref"])
    if row.online_dependency:
        fields.append("source_query_or_search_plan")
    if row.mcp_compatible or "mcp" in row.surface.lower():
        fields.append("mcp_tool_call")
    return _str_tuple(fields)


def _resource_requirements(
    row: FormalizationGapPlannerResourceRow,
) -> tuple[str, ...]:
    requirements = []
    if row.local_dependency:
        requirements.append("local command, package, corpus, index, or prover project configured")
    if row.online_dependency:
        requirements.append("network access, API key, license, or hosted service configured")
    if row.mcp_compatible or "mcp" in row.surface.lower():
        requirements.append("MCP server configured and reachable")
    if not requirements:
        requirements.append("no extra runtime dependency beyond the published contract")
    return _str_tuple(requirements)


def _resource_escalation_policy(row: FormalizationGapPlannerResourceRow) -> str:
    if row.resource_kind == "local_fallback":
        return (
            "use before frontier escalation; escalate when local evidence is empty, "
            "schema-invalid, stale, or insufficient for route stability"
        )
    if row.target_prover_families != PORTABLE_REUSE_TARGETS:
        return (
            "use for the named target prover family after portable work packets "
            "are exported and before any kernel-replay acceptance decision"
        )
    return (
        "use when local-first evidence is missing or ambiguous, then normalize "
        "responses into the published planner evidence contract"
    )


def _resource_output_artifact_kind(row: FormalizationGapPlannerResourceRow) -> str:
    if "prover_diagnostics" in row.evidence_contract or "residual_goals" in row.evidence_contract:
        return "proof_state_or_prover_feedback_response"
    if "source_refs" in row.evidence_contract:
        return "literature_or_source_grounding_response"
    if (
        "formal_declaration_hits" in row.evidence_contract
        or "lean_declaration_hits" in row.evidence_contract
        or "premise_candidates" in row.evidence_contract
    ):
        return "formal_library_search_response"
    if "portable_work_packets" in row.evidence_contract:
        return "cross_prover_adapter_packet_response"
    return "planner_resource_response"


def _component_row(
    spec: dict[str, Any],
    *,
    resource_ids: set[str],
    adapter_statuses: dict[str, str],
) -> FormalizationGapPlannerComponentResourceRow:
    local_fallbacks = _str_tuple(spec.get("local_fallback_resource_ids", []))
    frontier_resources = _str_tuple(spec.get("frontier_resource_ids", []))
    adapters = _str_tuple(spec.get("adapter_ids", []))
    errors = []
    for field_name in ("component_id", "component_name", "planner_stage", "role"):
        if not str(spec.get(field_name, "")):
            errors.append(f"{field_name} missing")
    if not local_fallbacks:
        errors.append("local_fallback_resource_ids missing")
    if not frontier_resources:
        errors.append("frontier_resource_ids missing")
    missing_resource_ids = [
        resource_id
        for resource_id in (*local_fallbacks, *frontier_resources)
        if resource_id not in resource_ids
    ]
    if missing_resource_ids:
        errors.append("unknown resource ids: " + ", ".join(missing_resource_ids))
    if not _str_tuple(spec.get("integration_contract_fields", [])):
        errors.append("integration_contract_fields missing")
    required_quality_signals = _component_required_quality_signals(spec)
    detected_adapter_statuses = {
        adapter_id: adapter_statuses.get(adapter_id, "ADAPTER_REGISTRY_NOT_PROVIDED")
        for adapter_id in adapters
    }
    readiness_summary = _readiness_summary(local_fallbacks, frontier_resources, detected_adapter_statuses)
    return FormalizationGapPlannerComponentResourceRow(
        schema_version=FORMALIZATION_GAP_PLANNER_COMPONENT_RESOURCE_REGISTRY_SCHEMA_VERSION,
        component_id=str(spec.get("component_id", "")),
        component_name=str(spec.get("component_name", "")),
        planner_stage=str(spec.get("planner_stage", "")),
        role=str(spec.get("role", "")),
        required_capabilities=_str_tuple(spec.get("required_capabilities", [])),
        local_fallback_resource_ids=local_fallbacks,
        frontier_resource_ids=frontier_resources,
        adapter_ids=adapters,
        detected_adapter_statuses=detected_adapter_statuses,
        integration_contract_fields=_str_tuple(spec.get("integration_contract_fields", [])),
        required_quality_signals=required_quality_signals,
        evidence_inputs=_str_tuple(spec.get("evidence_inputs", [])),
        expected_outputs=_str_tuple(spec.get("expected_outputs", [])),
        feedback_actions=_str_tuple(spec.get("feedback_actions", [])),
        evaluation_hooks=_str_tuple(spec.get("evaluation_hooks", [])),
        portable_to_prover_families=_str_tuple(
            spec.get("portable_to_prover_families", PORTABLE_REUSE_TARGETS)
        ),
        readiness_summary=readiness_summary,
        proof_evidence_status=PROOF_EVIDENCE_STATUS,
        proof_evidence_boundary=PROOF_EVIDENCE_BOUNDARY,
        ok=not errors,
        errors=tuple(errors),
    )


def _execution_plan_row(
    component_row: FormalizationGapPlannerComponentResourceRow,
    *,
    resource_ids: set[str],
) -> FormalizationGapPlannerComponentExecutionPlanRow:
    local_ids = component_row.local_fallback_resource_ids
    frontier_ids = component_row.frontier_resource_ids
    errors: list[str] = []
    if not local_ids:
        errors.append("local_first_resource_ids missing")
    if not frontier_ids:
        errors.append("frontier_escalation_resource_ids missing")
    unresolved = [
        resource_id
        for resource_id in (*local_ids, *frontier_ids)
        if resource_id not in resource_ids
    ]
    if unresolved:
        errors.append("unknown execution resource ids: " + ", ".join(unresolved))
    if not component_row.evidence_inputs:
        errors.append("evidence_inputs missing")
    if not component_row.expected_outputs:
        errors.append("expected_outputs missing")
    triggers = _execution_escalation_triggers(component_row)
    stop_conditions = _execution_stop_conditions(component_row)
    quality_gates = _execution_quality_gates(component_row)
    return FormalizationGapPlannerComponentExecutionPlanRow(
        schema_version=FORMALIZATION_GAP_PLANNER_COMPONENT_RESOURCE_REGISTRY_SCHEMA_VERSION,
        execution_plan_id="formalization_gap_planner_component_execution_plan:"
        + stable_hash(
            [
                component_row.component_id,
                local_ids,
                frontier_ids,
                component_row.adapter_ids,
                component_row.expected_outputs,
            ]
        )[:20],
        component_id=component_row.component_id,
        component_name=component_row.component_name,
        planner_stage=component_row.planner_stage,
        local_first_resource_ids=local_ids,
        frontier_escalation_resource_ids=frontier_ids,
        adapter_ids=component_row.adapter_ids,
        evidence_inputs=component_row.evidence_inputs,
        expected_outputs=component_row.expected_outputs,
        quality_gates=quality_gates,
        escalation_triggers=triggers,
        stop_conditions=stop_conditions,
        reproduction_surface=_reproduction_surface(component_row),
        proof_evidence_status=PROOF_EVIDENCE_STATUS,
        proof_evidence_boundary=PROOF_EVIDENCE_BOUNDARY,
        ok=not errors,
        errors=tuple(errors),
    )


def _execution_escalation_triggers(
    row: FormalizationGapPlannerComponentResourceRow,
) -> tuple[str, ...]:
    defaults = [
        "local fallback returns no evidence rows",
        "source, library, or proof-state confidence is below the route-stability threshold",
        "residual goals introduce a primitive not aligned to the current route DAG",
    ]
    return _str_tuple([*row.feedback_actions, *defaults])


def _execution_quality_gates(
    row: FormalizationGapPlannerComponentResourceRow,
) -> tuple[str, ...]:
    return _str_tuple(
        [
            *row.required_quality_signals,
            "schema_valid_outputs",
            "proof_boundary_preserved",
            "no_kernel_claim_without_replay",
        ]
    )


def _execution_stop_conditions(
    row: FormalizationGapPlannerComponentResourceRow,
) -> tuple[str, ...]:
    return _str_tuple(
        [
            "all expected outputs are present and schema-valid",
            "proof-boundary text is preserved and no kernel-proof claim is promoted",
            "component audit checks pass for " + row.component_id,
        ]
    )


def _resource_capability_tags(
    spec: dict[str, Any],
    evidence_contract: tuple[str, ...],
) -> tuple[str, ...]:
    fields = set(evidence_contract)
    tags: list[str] = []
    if fields & {"target_id", "theorem_statement", "candidate_primitives"}:
        tags.append("target_intake")
    if fields & {"source_refs", "route_evidence_nodes", "answer_contexts", "retrieved_papers"}:
        tags.append("literature_source_grounding")
    if fields & {"informal_knowledge_dag_nodes", "semantic_grounding_checks", "blueprint_nodes"}:
        tags.append("informal_route_dag_decomposition")
    if fields & {"formal_declaration_hits", "lean_declaration_hits", "declaration_hits", "premise_candidates", "coverage_updates", "definition_hits"}:
        tags.append("formal_library_search")
    if fields & {"prover_diagnostics", "residual_goals", "completion_candidates"}:
        tags.append("proof_state_feedback")
    if fields & {"proof_attempts", "attempt_traces", "retrieved_premises"}:
        tags.append("agentic_prover_attempts")
    if fields & {"route_revision_summary", "revised_dag_nodes", "replan_seed"}:
        tags.append("route_revision_handoff")
    if fields & {"portable_work_packets", "adapter_response_contract", "target_prover_family"}:
        tags.append("cross_prover_mapping")
    if fields & {"core_artifacts", "reproduction_commands", "audit_checks"}:
        tags.append("publication_reuse_audit")
    if spec.get("local_dependency"):
        tags.append("local_reproducible")
    if spec.get("online_dependency"):
        tags.append("frontier_or_online")
    if spec.get("mcp_compatible") or "mcp" in str(spec.get("surface", "")).lower():
        tags.append("mcp_surface")
    return _str_tuple(tags)


def _resource_validation_signals(
    spec: dict[str, Any],
    evidence_contract: tuple[str, ...],
) -> tuple[str, ...]:
    fields = set(evidence_contract)
    signals = ["schema_valid_response", "proof_boundary_preserved"]
    if "source_refs" in fields:
        signals.append("source_refs_present")
    if "route_evidence_nodes" in fields:
        signals.append("route_evidence_nodes_present")
    if fields & {"answer_contexts", "retrieved_papers"}:
        signals.append("citation_contexts_present")
    if fields & {"formal_declaration_hits", "lean_declaration_hits", "declaration_hits", "premise_candidates", "definition_hits"}:
        signals.append("formal_hits_or_premises_present")
    if "coverage_updates" in fields:
        signals.append("coverage_updates_present")
    if fields & {"prover_diagnostics", "residual_goals", "completion_candidates"}:
        signals.append("proof_state_diagnostics_or_residuals_present")
    if fields & {"proof_attempts", "attempt_traces"}:
        signals.append("attempt_trace_present")
    if fields & {"residual_goals", "route_revision_proposals"}:
        signals.append("residuals_or_revision_reasons_classified")
    if fields & {"portable_work_packets", "adapter_response_contract", "target_prover_family"}:
        signals.append("target_prover_family_and_adapter_contract_present")
    if fields & {"core_artifacts", "reproduction_commands", "audit_checks"}:
        signals.append("publication_artifacts_and_reproduction_commands_present")
    if spec.get("online_dependency"):
        signals.append("credential_license_or_network_status_recorded")
    if spec.get("mcp_compatible") or "mcp" in str(spec.get("surface", "")).lower():
        signals.append("mcp_tool_call_recorded")
    return _str_tuple(signals)


def _component_required_quality_signals(spec: dict[str, Any]) -> tuple[str, ...]:
    fields = set(_str_tuple(spec.get("integration_contract_fields", [])))
    fields.update(_str_tuple(spec.get("expected_outputs", [])))
    signals = ["schema_valid_outputs", "proof_boundary_preserved"]
    if fields & {"source_refs", "route_evidence_nodes", "source_confidence"}:
        signals.append("source_refs_or_literature_gap_recorded")
    if fields & {"informal_knowledge_dag_nodes", "route alternatives", "lemma candidates", "revised_informal_knowledge_dag_nodes"}:
        signals.append("informal_dag_nodes_have_source_or_search_status")
    if fields & {"formal_declaration_hits", "lean_declaration_hits", "coverage_updates", "existing declarations", "coverage_status"}:
        signals.append("formal_coverage_classification_recorded")
    if fields & {"residual_goals", "prover_diagnostics", "diagnostic signatures"}:
        signals.append("proof_state_residuals_classified")
    if fields & {"route_revision_summary", "revised_dag_nodes", "standalone_seed"}:
        signals.append("route_revision_is_replayable")
    if fields & {"portable_work_packets", "adapter_response_schema", "reproduction_commands", "publication bundle"}:
        signals.append("portable_contract_artifacts_present")
    if fields & {"node_cost", "route_cost", "selected route", "minimal delta witness"}:
        signals.append("minimal_delta_cost_witness_present")
    return _str_tuple(signals)


def _reproduction_surface(row: FormalizationGapPlannerComponentResourceRow) -> str:
    return (
        f"{row.component_id}: local_first={','.join(row.local_fallback_resource_ids)}; "
        f"frontier_escalation={','.join(row.frontier_resource_ids)}; "
        f"adapters={','.join(row.adapter_ids) or 'none'}"
    )


def _resource_specs() -> tuple[dict[str, Any], ...]:
    return (
        {
            "resource_id": "target_intake_schema",
            "resource_name": "Portable target-intake schema",
            "resource_kind": "local_fallback",
            "surface": "json_schema_and_python_module",
            "role": "normalize theorem requests into route seeds and bounded missing-information fields",
            "local_dependency": True,
            "evidence_contract": ("target_id", "theorem_statement", "candidate_primitives"),
        },
        {
            "resource_id": "target_intake_row_schema",
            "resource_name": "Portable target-intake row schema",
            "resource_kind": "local_fallback",
            "surface": "json_schema_and_python_module",
            "role": "validate normalized theorem-request JSONL rows before standalone route planning",
            "local_dependency": True,
            "evidence_contract": (
                "target_intake_id",
                "standalone_route_id",
                "primitive_seed_rows",
                "literature_queries",
                "formal_library_grounding_queries",
            ),
        },
        {
            "resource_id": "portable_gap_plan_row_schema",
            "resource_name": "Portable gap-plan row schema",
            "resource_kind": "local_fallback",
            "surface": "json_schema_and_python_module",
            "role": "validate streamed goal-conditioned gap-plan JSONL rows for external prover adapters",
            "local_dependency": True,
            "evidence_contract": (
                "goal_plan_id",
                "route_alignment_edges",
                "minimal_delta_summary",
                "portable_work_packet_contract",
            ),
        },
        {
            "resource_id": "local_route_truth_benchmark",
            "resource_name": "Packaged route-truth benchmark",
            "resource_kind": "local_fallback",
            "surface": "json_benchmark",
            "role": "deterministic route and refinement regression labels",
            "local_dependency": True,
            "evidence_contract": ("required_primitives", "coverage_status", "expected_route_delta"),
        },
        {
            "resource_id": "local_literature_corpus",
            "resource_name": "Local literature corpus",
            "resource_kind": "local_fallback",
            "surface": "filesystem_text_markdown_json",
            "role": "offline source refs and route-evidence nodes from user-provided corpora",
            "local_dependency": True,
            "evidence_contract": ("source_refs", "route_evidence_nodes"),
        },
        {
            "resource_id": "paperclip_cli_mcp",
            "resource_name": "Paperclip CLI/MCP",
            "resource_kind": "frontier_tool",
            "surface": "cli_or_mcp",
            "role": "agent-first search and reading over large scientific literature corpora",
            "resource_urls": ("https://paperclip.gxl.ai/", "https://paperclip.gxl.ai/mcp"),
            "online_dependency": True,
            "mcp_compatible": True,
            "evidence_contract": ("source_refs", "route_evidence_nodes"),
        },
        {
            "resource_id": "paperqa2_local_library",
            "resource_name": "PaperQA2 local-library QA",
            "resource_kind": "frontier_tool",
            "surface": "python_package_or_cli",
            "role": "citation-grounded QA over local PDFs and text documents",
            "resource_urls": ("https://github.com/Future-House/paper-qa",),
            "local_dependency": True,
            "evidence_contract": ("source_refs", "answer_contexts", "route_evidence_nodes"),
        },
        {
            "resource_id": "openscholar_semantic_scholar",
            "resource_name": "OpenScholar plus Semantic Scholar",
            "resource_kind": "frontier_tool",
            "surface": "external_api_or_local_retriever",
            "role": "large-scale citation-backed literature synthesis and passage retrieval",
            "resource_urls": (
                "https://github.com/akariasai/openscholar",
                "https://www.semanticscholar.org/product/api",
                "https://arxiv.org/abs/2411.14199",
            ),
            "online_dependency": True,
            "evidence_contract": ("retrieved_papers", "source_refs", "route_evidence_nodes"),
        },
        {
            "resource_id": "dependency_graph_autoformalization",
            "resource_name": "Dependency-graph autoformalization methods",
            "resource_kind": "frontier_method",
            "surface": "agent_or_blueprint_tool",
            "role": "decompose source-backed statements into definition, lemma, and proof-step DAGs",
            "resource_urls": (
                "https://arxiv.org/abs/2510.04520",
                "https://arxiv.org/abs/2510.10815",
                "https://arxiv.org/abs/2510.15981",
            ),
            "online_dependency": True,
            "evidence_contract": ("informal_knowledge_dag_nodes", "semantic_grounding_checks"),
        },
        {
            "resource_id": "lean_blueprint_leanarchitect",
            "resource_name": "Lean blueprint and LeanArchitect-style dependency metadata",
            "resource_kind": "frontier_method",
            "surface": "blueprint_dependency_graph",
            "role": "synchronize informal exposition, dependency graphs, and formal declarations",
            "resource_urls": (
                "https://github.com/PatrickMassot/leanblueprint",
                "https://huggingface.co/papers/2601.22554",
            ),
            "local_dependency": True,
            "target_prover_families": ("lean4",),
            "evidence_contract": ("blueprint_nodes", "formal_declaration_links", "dependency_edges"),
        },
        {
            "resource_id": "local_target_formal_source_index",
            "resource_name": "Portable target formal-source index",
            "resource_kind": "local_fallback",
            "surface": "python_module_and_sqlite",
            "role": (
                "local declaration search over target-prover source roots using "
                "the portable formal_declaration_hits contract"
            ),
            "local_dependency": True,
            "target_prover_families": PORTABLE_REUSE_TARGETS,
            "evidence_contract": (
                "formal_declaration_hits",
                "coverage_updates",
                "target_prover_family",
            ),
        },
        {
            "resource_id": "local_formal_source_index",
            "resource_name": "AI Statistician formal-source index",
            "resource_kind": "local_fallback",
            "surface": "python_module_and_sqlite",
            "role": "local declaration search over formal source roots",
            "local_dependency": True,
            "evidence_contract": (
                "formal_declaration_hits",
                "lean_declaration_hits",
                "coverage_updates",
            ),
            "target_prover_families": ("lean4",),
        },
        {
            "resource_id": "local_lean_rag_dependency_graph",
            "resource_name": "Local Lean RAG dependency graph",
            "resource_kind": "local_fallback",
            "surface": "sqlite_dependency_graph",
            "role": "declaration signatures, FTS search, and graph neighborhoods for reuse estimates",
            "local_dependency": True,
            "evidence_contract": ("declaration_hits", "dependency_neighbors", "reuse_cost_features"),
            "target_prover_families": ("lean4",),
        },
        {
            "resource_id": "loogle_leansearch",
            "resource_name": "Loogle and LeanSearch",
            "resource_kind": "frontier_tool",
            "surface": "web_api_cli_or_lean_command",
            "role": "retrieve Lean declarations by name, type shape, expression, and conclusion",
            "resource_urls": (
                "https://loogle.lean-lang.org/",
                "https://arxiv.org/abs/2403.13310",
                "https://arxiv.org/abs/2605.13137",
            ),
            "online_dependency": True,
            "evidence_contract": (
                "formal_declaration_hits",
                "lean_declaration_hits",
                "premise_candidates",
            ),
            "target_prover_families": ("lean4",),
        },
        {
            "resource_id": "leanexplore_mcp",
            "resource_name": "LeanExplore MCP/API",
            "resource_kind": "frontier_tool",
            "surface": "mcp_or_python_api",
            "role": "semantic and lexical Lean declaration retrieval for theorem-proving agents",
            "resource_urls": ("https://arxiv.org/abs/2506.11085",),
            "online_dependency": True,
            "mcp_compatible": True,
            "evidence_contract": (
                "formal_declaration_hits",
                "lean_declaration_hits",
                "semantic_match_scores",
            ),
            "target_prover_families": ("lean4",),
        },
        {
            "resource_id": "rocq_lsp_serapi",
            "resource_name": "Rocq LSP and SerAPI-family interfaces",
            "resource_kind": "frontier_tool",
            "surface": "lsp_or_serapi",
            "role": "Rocq/Coq goal-state, AST, and library interaction for portable adapters",
            "resource_urls": (
                "https://docs.rocq-prover.org/master/refman/",
                "https://github.com/ejgallego/coq-lsp",
            ),
            "local_dependency": True,
            "evidence_contract": ("prover_diagnostics", "residual_goals", "library_hits"),
            "target_prover_families": ("rocq",),
        },
        {
            "resource_id": "isabelle_sledgehammer_afp",
            "resource_name": "Isabelle/Sledgehammer/AFP interfaces",
            "resource_kind": "frontier_tool",
            "surface": "isabelle_tooling",
            "role": "Isabelle theorem search, proof-state automation, and library reuse mapping",
            "resource_urls": ("https://isabelle.in.tum.de/", "https://www.isa-afp.org/"),
            "local_dependency": True,
            "evidence_contract": ("prover_diagnostics", "premise_candidates", "residual_goals"),
            "target_prover_families": ("isabelle",),
        },
        {
            "resource_id": "agda_search_auto",
            "resource_name": "Agda Search About, Auto, and interaction JSON",
            "resource_kind": "frontier_tool",
            "surface": "agda_cli_or_interaction_json",
            "role": "Agda definition search, type-checking, goal interaction, and proof assistance",
            "resource_urls": (
                "https://agda.readthedocs.io/en/v2.6.1.3/tools/search-about.html",
                "https://agda.readthedocs.io/en/v2.5.3/tools/auto.html",
            ),
            "local_dependency": True,
            "evidence_contract": ("definition_hits", "prover_diagnostics", "residual_goals"),
            "target_prover_families": ("agda",),
        },
        {
            "resource_id": "local_lake_lean",
            "resource_name": "Local Lake/Lean compiler feedback",
            "resource_kind": "local_fallback",
            "surface": "cli",
            "role": "compile skeletons and leaf lemmas to collect diagnostics and residual obligations",
            "resource_urls": ("https://lean-lang.org/",),
            "local_dependency": True,
            "evidence_contract": ("prover_diagnostics", "residual_goals"),
            "target_prover_families": ("lean4",),
        },
        {
            "resource_id": "lean_lsp_mcp",
            "resource_name": "Lean LSP MCP",
            "resource_kind": "frontier_tool",
            "surface": "mcp",
            "role": "Lean diagnostics, goal states, completions, and project build feedback through LSP",
            "resource_urls": ("https://github.com/oOo0oOo/lean-lsp-mcp",),
            "local_dependency": True,
            "mcp_compatible": True,
            "evidence_contract": ("prover_diagnostics", "residual_goals", "completion_candidates"),
            "target_prover_families": ("lean4",),
        },
        {
            "resource_id": "leandojo_reprover",
            "resource_name": "LeanDojo/ReProver",
            "resource_kind": "frontier_tool",
            "surface": "python_package",
            "role": "programmatic Lean interaction and retrieval-augmented proof attempts",
            "resource_urls": ("https://github.com/lean-dojo/ReProver", "https://arxiv.org/abs/2306.15626"),
            "local_dependency": True,
            "evidence_contract": ("proof_attempts", "retrieved_premises", "residual_goals"),
            "target_prover_families": ("lean4",),
        },
        {
            "resource_id": "agentic_prover_orchestration",
            "resource_name": "Agentic prover orchestration methods",
            "resource_kind": "frontier_method",
            "surface": "agent_or_mcp_workflow",
            "role": "multi-attempt prover loops that return compiler feedback and repair traces to the planner",
            "resource_urls": (
                "https://arxiv.org/abs/2510.12787",
                "https://arxiv.org/abs/2605.17283",
                "https://arxiv.org/abs/2605.22763",
            ),
            "online_dependency": True,
            "mcp_compatible": True,
            "evidence_contract": ("prover_diagnostics", "attempt_traces", "route_revision_proposals"),
        },
        {
            "resource_id": "route_revision_overlay",
            "resource_name": "Built-in route-revision overlay and replan handoff",
            "resource_kind": "local_fallback",
            "surface": "python_module",
            "role": "apply accepted refinement evidence and export replayable replan seeds",
            "local_dependency": True,
            "evidence_contract": ("route_revision_summary", "revised_dag_nodes", "replan_seed"),
        },
        {
            "resource_id": "publication_bundle_audit",
            "resource_name": "Publication bundle and audit",
            "resource_kind": "local_fallback",
            "surface": "json_markdown_bundle",
            "role": "package contracts, examples, benchmarks, registries, and reproduction commands",
            "local_dependency": True,
            "evidence_contract": ("core_artifacts", "reproduction_commands", "audit_checks"),
        },
        {
            "resource_id": "cross_prover_matrix_audit",
            "resource_name": "Cross-prover matrix audit",
            "resource_kind": "local_fallback",
            "surface": "python_module",
            "role": "exercise portable work packets across Lean, Rocq, Isabelle, and Agda adapters",
            "local_dependency": True,
            "evidence_contract": ("portable_work_packets", "target_prover_family", "adapter_response_contract"),
        },
    )


def _component_specs() -> tuple[dict[str, Any], ...]:
    return (
        {
            "component_id": "target_theorem_intake",
            "component_name": "Target theorem intake",
            "planner_stage": "target theorem -> normalized route seed",
            "role": "extract theorem statement, assumptions, objects, procedure, conclusion, and missing-information obligations",
            "required_capabilities": ("schema validation", "assumption extraction", "missing-field surfacing"),
            "local_fallback_resource_ids": (
                "target_intake_schema",
                "target_intake_row_schema",
            ),
            "frontier_resource_ids": ("paperclip_cli_mcp", "openscholar_semantic_scholar"),
            "adapter_ids": (),
            "integration_contract_fields": ("target_id", "theorem_statement", "assumptions", "candidate_primitives"),
            "evidence_inputs": ("raw theorem request", "known proof sources"),
            "expected_outputs": ("standalone planner seed", "bounded source queries", "candidate primitive rows"),
            "feedback_actions": ("request missing theorem sources", "request missing skeleton", "normalize target prover family"),
            "evaluation_hooks": ("target_intake_manifest", "adversarial_intake_audit"),
        },
        {
            "component_id": "literature_grounded_route_synthesis",
            "component_name": "Literature-grounded informal route synthesis",
            "planner_stage": "normalized target -> source-backed informal knowledge DAG",
            "role": "identify definitions, assumptions, intermediate lemmas, and proof routes with bounded source evidence",
            "required_capabilities": ("paper search", "source citation", "route evidence extraction"),
            "local_fallback_resource_ids": ("local_literature_corpus",),
            "frontier_resource_ids": (
                "paperclip_cli_mcp",
                "paperqa2_local_library",
                "openscholar_semantic_scholar",
            ),
            "adapter_ids": (
                "local_literature_corpus",
                "paperclip_cli_mcp",
                "paperqa2_local_library",
                "openscholar_semantic_scholar",
                "paper2agent_formalization_mcp",
            ),
            "integration_contract_fields": ("source_refs", "route_evidence_nodes", "source_confidence"),
            "evidence_inputs": ("literature_discovery_items", "known_proof_sources", "source_search_pending nodes"),
            "expected_outputs": ("source_refs", "route_evidence_nodes", "route_revision_proposals"),
            "feedback_actions": ("expand literature search", "replace intuition-only DAG node", "flag source gaps"),
            "evaluation_hooks": ("source_grounding_audit", "refinement_evidence"),
        },
        {
            "component_id": "informal_route_dag_decomposition",
            "component_name": "Informal route DAG decomposition",
            "planner_stage": "source-backed route -> AND/OR route graph",
            "role": "turn source-backed proof sketches into dependency nodes, lemma candidates, and route alternatives",
            "required_capabilities": ("dependency graph construction", "lemma extraction", "semantic grounding"),
            "local_fallback_resource_ids": ("local_route_truth_benchmark", "route_revision_overlay"),
            "frontier_resource_ids": (
                "dependency_graph_autoformalization",
                "lean_blueprint_leanarchitect",
            ),
            "adapter_ids": ("dependency_graph_route_decomposition", "route_revision_overlay"),
            "integration_contract_fields": (
                "revised_informal_knowledge_dag_nodes",
                "revised_formal_realization_dag_nodes",
                "route_revision_summary",
            ),
            "evidence_inputs": ("source_refs", "informal proof steps", "existing planner route"),
            "expected_outputs": ("informal_knowledge_dag_nodes", "route alternatives", "lemma candidates"),
            "feedback_actions": ("split overloaded DAG node", "add bridge lemma", "reorder leaves bottom-up"),
            "evaluation_hooks": ("portable_plan_audit", "route_stability_audit"),
        },
        {
            "component_id": "formal_library_coverage_mapping",
            "component_name": "Formal library coverage mapping",
            "planner_stage": "informal DAG -> target-prover realization DAG",
            "role": "classify each informal node against available formal libraries and estimate minimal new theory",
            "required_capabilities": ("declaration search", "dependency graph traversal", "cross-prover library mapping"),
            "local_fallback_resource_ids": (
                "local_target_formal_source_index",
                "local_formal_source_index",
                "local_lean_rag_dependency_graph",
            ),
            "frontier_resource_ids": (
                "loogle_leansearch",
                "leanexplore_mcp",
                "rocq_lsp_serapi",
                "isabelle_sledgehammer_afp",
                "agda_search_auto",
            ),
            "adapter_ids": (
                "local_formal_source_index",
                "local_lean_rag_dependency_graph",
                "loogle_leansearchclient",
                "leanexplore_mcp",
            ),
            "integration_contract_fields": (
                "formal_declaration_hits",
                "lean_declaration_hits",
                "coverage_updates",
                "reuse_cost_features",
            ),
            "evidence_inputs": ("primitive labels", "theorem skeletons", "library snapshot ref"),
            "expected_outputs": ("coverage_status", "existing declarations", "wrapper/bridge/new-definition classification"),
            "feedback_actions": ("prefer existing formulation", "add wrapper", "add bridge lemma", "open substantial-theory gap"),
            "evaluation_hooks": ("minimal_delta_audit", "cross_prover_matrix_audit"),
        },
        {
            "component_id": "minimal_delta_and_or_planning",
            "component_name": "Minimal formalization delta planner",
            "planner_stage": "coverage map -> costed minimal route cut",
            "role": "choose the route that minimizes new formal work under source, library, and proof-state constraints",
            "required_capabilities": ("AND/OR graph costing", "dominance checking", "semantic-risk accounting"),
            "local_fallback_resource_ids": (
                "local_route_truth_benchmark",
                "local_lean_rag_dependency_graph",
            ),
            "frontier_resource_ids": ("lean_blueprint_leanarchitect", "dependency_graph_autoformalization"),
            "adapter_ids": (),
            "integration_contract_fields": ("node_cost", "route_cost", "selected_primitives", "delta_primitives"),
            "evidence_inputs": ("informal_knowledge_dag", "formal_realization_dag", "coverage_updates"),
            "expected_outputs": ("selected route", "portable work packets", "minimal delta witness"),
            "feedback_actions": ("reject dominated route", "increase source evidence bound", "prefer lower semantic risk"),
            "evaluation_hooks": ("minimal_delta_audit", "formalization_gap_planner_evaluation"),
        },
        {
            "component_id": "prover_feedback_refinement",
            "component_name": "Prover feedback and refinement",
            "planner_stage": "route leaves -> proof-state diagnostics -> route revision evidence",
            "role": "try leaves bottom-up, collect residual goals, and feed missing assumptions back to the route planner",
            "required_capabilities": ("kernel-adjacent diagnostics", "proof-state extraction", "attempt trace normalization"),
            "local_fallback_resource_ids": ("local_lake_lean",),
            "frontier_resource_ids": (
                "lean_lsp_mcp",
                "leandojo_reprover",
                "agentic_prover_orchestration",
                "rocq_lsp_serapi",
                "isabelle_sledgehammer_afp",
                "agda_search_auto",
            ),
            "adapter_ids": (
                "local_lake_lean",
                "lean_lsp_mcp",
                "leandojo_reprover",
                "agentic_prover_orchestration",
            ),
            "integration_contract_fields": ("prover_diagnostics", "residual_goals", "kernel_verified"),
            "evidence_inputs": ("proof_state_feedback_items", "theorem_skeleton", "library_snapshot_ref"),
            "expected_outputs": ("residual_goals", "diagnostic signatures", "route_revision_proposals"),
            "feedback_actions": ("add missing measurability/integrability/topology assumption", "repair theorem skeleton", "rerun library grounding"),
            "evaluation_hooks": ("proof_state_triage", "route_replan_handoff_audit"),
        },
        {
            "component_id": "route_revision_handoff",
            "component_name": "Route revision and replan handoff",
            "planner_stage": "accepted evidence -> revised route seed",
            "role": "apply accepted refinement evidence without mutating the original plan and export a replayable next-round seed",
            "required_capabilities": ("evidence validation", "non-mutating overlay", "round-trip replan seed"),
            "local_fallback_resource_ids": ("route_revision_overlay",),
            "frontier_resource_ids": ("agentic_prover_orchestration", "dependency_graph_autoformalization"),
            "adapter_ids": ("route_revision_overlay",),
            "integration_contract_fields": ("route_revision_summary", "revised_dag_nodes", "standalone_seed"),
            "evidence_inputs": ("refinement_evidence", "route_stability_decisions", "prover residual goals"),
            "expected_outputs": ("route overlay", "stability audit", "standalone replan seed"),
            "feedback_actions": ("expand search", "rerun formal-source grounding", "rerun prover feedback", "stop when stable"),
            "evaluation_hooks": ("route_stability_audit", "route_replan_handoff_audit"),
        },
        {
            "component_id": "cross_prover_public_reuse",
            "component_name": "Cross-prover publication and reuse",
            "planner_stage": "portable plan -> reusable bundle and prover work packets",
            "role": "make the planner reusable outside Lean and outside the AI Statistician system",
            "required_capabilities": ("portable schemas", "target-prover packets", "bundle audit", "example inputs"),
            "local_fallback_resource_ids": (
                "portable_gap_plan_row_schema",
                "publication_bundle_audit",
                "cross_prover_matrix_audit",
            ),
            "frontier_resource_ids": (
                "rocq_lsp_serapi",
                "isabelle_sledgehammer_afp",
                "agda_search_auto",
                "lean_lsp_mcp",
            ),
            "adapter_ids": (),
            "integration_contract_fields": ("portable_work_packets", "adapter_response_schema", "reproduction_commands"),
            "evidence_inputs": ("portable plan manifest", "target prover family", "library snapshot ref"),
            "expected_outputs": ("publication bundle", "prover adapter packets", "bundle audit manifest"),
            "feedback_actions": ("reject kernel claims from adapters", "mark awaiting adapter mapping", "ship examples and schemas"),
            "evaluation_hooks": ("publication_bundle_audit", "reuse_smoke"),
        },
    )


def _adapter_statuses(manifest_path: Path | None) -> dict[str, str]:
    if manifest_path is None:
        return {}
    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    rows = payload.get("rows", [])
    if not isinstance(rows, list):
        return {}
    statuses: dict[str, str] = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        adapter_id = str(row.get("adapter_id", ""))
        if adapter_id:
            statuses[adapter_id] = str(row.get("readiness_status", "UNKNOWN"))
    return statuses


def _readiness_summary(
    local_fallbacks: tuple[str, ...],
    frontier_resources: tuple[str, ...],
    adapter_statuses: dict[str, str],
) -> str:
    ready = sum(
        1
        for status in adapter_statuses.values()
        if status in {"READY_LOCAL", "READY_CONFIGURED"}
    )
    if adapter_statuses:
        return (
            f"local_fallbacks={len(local_fallbacks)} "
            f"frontier_resources={len(frontier_resources)} "
            f"ready_adapters={ready}/{len(adapter_statuses)}"
        )
    return (
        f"local_fallbacks={len(local_fallbacks)} "
        f"frontier_resources={len(frontier_resources)} "
        "adapter_registry_not_provided"
    )


def _str_tuple(values: Any) -> tuple[str, ...]:
    if isinstance(values, str):
        return (values,) if values else tuple()
    if not isinstance(values, (list, tuple, set)):
        return tuple()
    return tuple(dict.fromkeys(str(item) for item in values if str(item)))


def _markdown_report(payload: dict[str, object]) -> str:
    lines = [
        "# Formalization Gap Planner Component Resource Registry",
        "",
        f"- Components: {payload.get('n_component_rows_ok')}/{payload.get('n_component_rows')}",
        (
            f"- Component row schema valid: "
            f"{payload.get('n_component_row_schema_valid')}/"
            f"{payload.get('n_component_rows')}"
        ),
        f"- Execution plans: {payload.get('n_execution_plan_rows_ok')}/{payload.get('n_execution_plan_rows')}",
        (
            f"- Execution-plan row schema valid: "
            f"{payload.get('n_execution_plan_row_schema_valid')}/"
            f"{payload.get('n_execution_plan_rows')}"
        ),
        f"- Resources: {payload.get('n_resource_rows_ok')}/{payload.get('n_resources')}",
        (
            f"- Resource row schema valid: "
            f"{payload.get('n_resource_row_schema_valid')}/"
            f"{payload.get('n_resources')}"
        ),
        (
            f"- Resource contract row schema valid: "
            f"{payload.get('n_resource_contract_row_schema_valid')}/"
            f"{payload.get('n_resource_contract_rows')}"
        ),
        f"- Resources with capability tags: {payload.get('n_resources_with_capability_tags')}",
        f"- Resources with validation signals: {payload.get('n_resources_with_validation_signals')}",
        f"- Components with quality signals: {payload.get('n_component_rows_with_required_quality_signals')}",
        f"- Execution plans with quality gates: {payload.get('n_execution_plans_with_quality_gates')}",
        f"- Frontier resources: {payload.get('n_frontier_resources')}",
        f"- MCP/CLI resources: {payload.get('n_mcp_or_cli_resources')}",
        f"- Online resources: {payload.get('n_online_resources')}",
        f"- All OK: {payload.get('all_ok')}",
        "",
        "## Boundary",
        "",
        str(payload.get("proof_evidence_boundary", PROOF_EVIDENCE_BOUNDARY)),
        "",
        "## Components",
        "",
    ]
    for row in payload.get("component_rows", []):
        if not isinstance(row, dict):
            continue
        lines.append(
            f"- `{row.get('component_id')}` local={len(row.get('local_fallback_resource_ids', []))} "
            f"frontier={len(row.get('frontier_resource_ids', []))} "
            f"adapters={len(row.get('adapter_ids', []))}"
        )
    lines.extend(["", "## Execution Plans", ""])
    for row in payload.get("execution_plan_rows", []):
        if not isinstance(row, dict):
            continue
        lines.append(
            f"- `{row.get('component_id')}` local_first={len(row.get('local_first_resource_ids', []))} "
            f"frontier={len(row.get('frontier_escalation_resource_ids', []))} "
            f"stop={len(row.get('stop_conditions', []))}"
        )
    return "\n".join(lines) + "\n"
