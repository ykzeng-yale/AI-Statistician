from __future__ import annotations

import json
import re
import tempfile
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from .fingerprint import stable_hash
from .formalization_gap_planner_component_resource_registry import (
    export_formalization_gap_planner_component_resource_registry,
)
from .formalization_gap_planner_llm_route_planner import (
    export_formalization_gap_planner_llm_route_planner,
)
from .formalization_gap_planner_standalone import (
    FORMALIZATION_GAP_PLANNER_STANDALONE_INPUT_COMPONENT,
    FORMALIZATION_GAP_PLANNER_STANDALONE_INPUT_SCHEMA_ID,
    export_formalization_gap_planner_standalone_plan,
    validate_standalone_input_payload,
)
from .formalization_gap_planner_target_intake import (
    FORMALIZATION_GAP_PLANNER_TARGET_INTAKE_COMPONENT,
    normalize_formalization_gap_planner_target_intake,
)


FORMALIZATION_GAP_PLANNER_RUNTIME_HANDOFF_AUDIT_SCHEMA_VERSION = 1
RUNTIME_HANDOFF_AUDIT_ROW_SCHEMA_ID = (
    "urn:ai-statistician:schemas:"
    "formalization-gap-planner-runtime-handoff-audit-row:1"
)
RUNTIME_HANDOFF_EXECUTION_PLAN_SCHEMA_ID = (
    "urn:ai-statistician:schemas:"
    "formalization-gap-planner-runtime-handoff-execution-plan:1"
)
PROOF_EVIDENCE_STATUS = (
    "FORMALIZATION_GAP_PLANNER_RUNTIME_HANDOFF_AUDIT_NOT_PROOF_EVIDENCE"
)
PROOF_EVIDENCE_BOUNDARY = (
    "Formalization gap planner runtime handoff audit rows validate that AI "
    "Statistician runtime bridge artifacts are replayable as standalone "
    "formalization-gap planner input and that LLM route-planner handoffs remain "
    "cost-controlled until explicitly invoked. They are audit evidence, not "
    "theorem proof evidence."
)
RUNTIME_BRIDGE_PROOF_EVIDENCE_STATUS = (
    "RUNTIME_FORMALIZATION_GAP_PLANNER_BRIDGE_NOT_PROOF_EVIDENCE"
)


@dataclass(frozen=True)
class FormalizationGapPlannerRuntimeHandoffAuditCheck:
    schema_version: int
    check_id: str
    check_name: str
    category: str
    handoff_id: str
    bridge_id: str
    expected: str
    observed: str
    ok: bool
    severity: str
    errors: tuple[str, ...] = ()


def audit_formalization_gap_planner_runtime_handoffs(
    runtime_formalization_gap_planner_handoffs_jsonl: Path,
    out_dir: Path | None = None,
    *,
    run_smoke: bool = True,
) -> dict[str, object]:
    """Audit runtime-to-standalone formalization-gap planner handoff rows.

    The smoke path is intentionally offline. It replays the standalone planner
    and stages Anthropic LLM route-planner request packets without
    ``--invoke-provider`` or API calls.
    """

    errors: list[str] = []
    handoffs_path = runtime_formalization_gap_planner_handoffs_jsonl
    handoff_rows = _read_jsonl(handoffs_path, errors)
    smoke_root = out_dir / "runtime_handoff_smoke" if out_dir is not None else None
    checks: list[FormalizationGapPlannerRuntimeHandoffAuditCheck] = [
        _check(
            "handoff_jsonl_exists",
            "artifacts",
            "",
            "",
            "handoff JSONL file exists",
            str(handoffs_path.exists()),
            handoffs_path.exists(),
        ),
        _check(
            "handoff_rows_present",
            "artifacts",
            "",
            "",
            "at least one runtime handoff row",
            str(len(handoff_rows)),
            bool(handoff_rows),
        ),
    ]
    smoke_summaries: list[dict[str, object]] = []
    for idx, handoff in enumerate(handoff_rows):
        row_checks, smoke_summary = _audit_handoff_row(
            handoff,
            row_index=idx,
            run_smoke=run_smoke,
            smoke_root=smoke_root,
        )
        checks.extend(row_checks)
        smoke_summaries.append(smoke_summary)

    check_dicts = [asdict(check) for check in checks]
    row_schema = runtime_handoff_audit_row_json_schema()
    row_schema_errors = [
        validate_runtime_handoff_audit_row(row, row_schema) for row in check_dicts
    ]
    n_row_schema_valid = sum(1 for row_errors in row_schema_errors if not row_errors)
    execution_plan_rows = _runtime_handoff_execution_plan_rows(handoff_rows)
    execution_plan_row_schema_errors = [
        validate_runtime_handoff_execution_plan(row)
        for row in execution_plan_rows
    ]
    n_execution_plan_row_schema_valid = sum(
        1 for row_errors in execution_plan_row_schema_errors if not row_errors
    )
    by_category: dict[str, int] = {}
    for check in checks:
        by_category[check.category] = by_category.get(check.category, 0) + 1
    payload: dict[str, object] = {
        "schema_version": FORMALIZATION_GAP_PLANNER_RUNTIME_HANDOFF_AUDIT_SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "component_name": "formalization_gap_planner_runtime_handoff_audit",
        "runtime_formalization_gap_planner_handoffs_jsonl": str(handoffs_path),
        "run_smoke": run_smoke,
        "smoke_root": str(smoke_root or ""),
        "n_handoffs": len(handoff_rows),
        "n_checks": len(checks),
        "n_ok": sum(1 for check in checks if check.ok),
        "n_failed": sum(1 for check in checks if not check.ok),
        "n_row_schema_valid": n_row_schema_valid,
        "n_row_schema_invalid": len(row_schema_errors) - n_row_schema_valid,
        "n_seed_schema_valid": sum(
            1 for summary in smoke_summaries if summary.get("seed_schema_ok")
        ),
        "n_execution_plans": sum(
            1 for summary in smoke_summaries if summary.get("execution_plan_present")
        ),
        "n_execution_plan_stage_rows": sum(
            int(summary.get("execution_plan_stage_count", 0) or 0)
            for summary in smoke_summaries
        ),
        "n_execution_plan_schema_valid": sum(
            1
            for summary in smoke_summaries
            if summary.get("execution_plan_schema_valid")
        ),
        "n_execution_plan_rows": len(execution_plan_rows),
        "n_execution_plan_row_schema_valid": n_execution_plan_row_schema_valid,
        "n_execution_plan_row_schema_invalid": (
            len(execution_plan_row_schema_errors)
            - n_execution_plan_row_schema_valid
        ),
        "n_execution_plan_prompt_stage_cost_control_ok": sum(
            1
            for summary in smoke_summaries
            if summary.get("execution_plan_prompt_stage_cost_control_ok")
        ),
        "n_execution_plan_live_stage_explicit_ok": sum(
            1
            for summary in smoke_summaries
            if summary.get("execution_plan_live_stage_explicit_ok")
        ),
        "n_execution_plan_reuse_smoke_stage_cost_control_ok": sum(
            1
            for summary in smoke_summaries
            if summary.get("execution_plan_reuse_smoke_stage_cost_control_ok")
        ),
        "n_cost_control_ok": sum(
            1 for summary in smoke_summaries if summary.get("cost_control_ok")
        ),
        "n_live_explicit_ok": sum(
            1 for summary in smoke_summaries if summary.get("live_explicit_ok")
        ),
        "n_reuse_smoke_cost_control_ok": sum(
            1
            for summary in smoke_summaries
            if summary.get("reuse_smoke_cost_control_ok")
        ),
        "n_component_resource_registry_smoke_ok": sum(
            1
            for summary in smoke_summaries
            if summary.get("component_resource_registry_smoke_ok")
        ),
        "n_component_resource_registry_components_in_prompt": sum(
            int(
                summary.get(
                    "llm_prompt_component_resource_registry_components",
                    0,
                )
                or 0
            )
            for summary in smoke_summaries
        ),
        "n_component_resource_registry_resources_in_prompt": sum(
            int(
                summary.get(
                    "llm_prompt_component_resource_registry_resources",
                    0,
                )
                or 0
            )
            for summary in smoke_summaries
        ),
        "n_component_resource_registry_contracts_in_prompt": sum(
            int(
                summary.get(
                    "llm_prompt_component_resource_registry_contracts",
                    0,
                )
                or 0
            )
            for summary in smoke_summaries
        ),
        "n_target_intake_smoke_ok": sum(
            1 for summary in smoke_summaries if summary.get("target_intake_smoke_ok")
        ),
        "n_target_intake_targets": sum(
            int(summary.get("target_intake_targets", 0) or 0)
            for summary in smoke_summaries
        ),
        "n_target_intake_primitive_seeds": sum(
            int(summary.get("target_intake_primitive_seeds", 0) or 0)
            for summary in smoke_summaries
        ),
        "n_standalone_smoke_ok": sum(
            1 for summary in smoke_summaries if summary.get("standalone_smoke_ok")
        ),
        "n_llm_prompt_smoke_ok": sum(
            1 for summary in smoke_summaries if summary.get("llm_prompt_smoke_ok")
        ),
        "n_llm_prompt_packets": sum(
            int(summary.get("llm_prompt_packets", 0) or 0)
            for summary in smoke_summaries
        ),
        "n_llm_prompt_awaiting_response": sum(
            int(summary.get("llm_prompt_awaiting_response", 0) or 0)
            for summary in smoke_summaries
        ),
        "n_llm_prompt_requests_with_minimal_delta_cost_hints": sum(
            int(
                summary.get(
                    "llm_prompt_requests_with_minimal_delta_cost_hints",
                    0,
                )
                or 0
            )
            for summary in smoke_summaries
        ),
        "n_llm_prompt_primitive_cost_hints": sum(
            int(summary.get("llm_prompt_primitive_cost_hints", 0) or 0)
            for summary in smoke_summaries
        ),
        "n_llm_prompt_route_option_cost_hints": sum(
            int(summary.get("llm_prompt_route_option_cost_hints", 0) or 0)
            for summary in smoke_summaries
        ),
        "n_llm_prompt_requests_with_target_intake_rows": sum(
            int(summary.get("llm_prompt_requests_with_target_intake_rows", 0) or 0)
            for summary in smoke_summaries
        ),
        "n_llm_prompt_target_intake_rows": sum(
            int(summary.get("llm_prompt_target_intake_rows", 0) or 0)
            for summary in smoke_summaries
        ),
        "n_llm_prompt_model_tier_mismatches": sum(
            int(summary.get("llm_prompt_model_tier_mismatches", 0) or 0)
            for summary in smoke_summaries
        ),
        "n_llm_prompt_model_tier_haiku": sum(
            int(summary.get("llm_prompt_model_tier_haiku", 0) or 0)
            for summary in smoke_summaries
        ),
        "n_llm_prompt_model_tier_sonnet": sum(
            int(summary.get("llm_prompt_model_tier_sonnet", 0) or 0)
            for summary in smoke_summaries
        ),
        "n_llm_prompt_model_tier_opus": sum(
            int(summary.get("llm_prompt_model_tier_opus", 0) or 0)
            for summary in smoke_summaries
        ),
        "n_seed_routes": sum(
            int(summary.get("seed_routes", 0) or 0) for summary in smoke_summaries
        ),
        "n_seed_primitives": sum(
            int(summary.get("seed_primitives", 0) or 0)
            for summary in smoke_summaries
        ),
        "n_seed_residual_goals": sum(
            int(summary.get("seed_residual_goals", 0) or 0)
            for summary in smoke_summaries
        ),
        "n_seed_candidate_declaration_rows": sum(
            int(summary.get("seed_candidate_declaration_rows", 0) or 0)
            for summary in smoke_summaries
        ),
        "n_seed_primitives_with_candidate_declaration_rows": sum(
            int(summary.get("seed_primitives_with_candidate_declaration_rows", 0) or 0)
            for summary in smoke_summaries
        ),
        "n_seed_target_prover_family_compatible_with_handoff": sum(
            1
            for summary in smoke_summaries
            if summary.get("seed_target_prover_family_compatible_with_handoff")
        ),
        "n_mixed_seed_target_prover_families": sum(
            1
            for summary in smoke_summaries
            if int(summary.get("seed_n_target_prover_families", 0) or 0) > 1
        ),
        "by_category": dict(sorted(by_category.items())),
        "checks": check_dicts,
        "row_schema_errors": row_schema_errors,
        "runtime_handoff_audit_row_schema": row_schema,
        "execution_plan_rows": execution_plan_rows,
        "execution_plan_row_schema_errors": execution_plan_row_schema_errors,
        "runtime_handoff_execution_plan_schema": (
            runtime_handoff_execution_plan_json_schema()
        ),
        "smoke_summaries": smoke_summaries,
        "all_ok": (
            not errors
            and bool(handoff_rows)
            and all(check.ok for check in checks)
            and n_row_schema_valid == len(row_schema_errors)
            and n_execution_plan_row_schema_valid
            == len(execution_plan_row_schema_errors)
        ),
        "errors": errors,
        "runtime_handoff_audit_fingerprint": stable_hash(check_dicts),
        "proof_evidence_status": PROOF_EVIDENCE_STATUS,
        "proof_evidence_boundary": PROOF_EVIDENCE_BOUNDARY,
        "limitations": [
            "prompt smoke runs stage request packets only and do not call Anthropic",
            "standalone planner replay is route-planning evidence, not proof evidence",
            "semantic adequacy still requires source-grounding and target-prover replay",
        ],
    }
    if out_dir is not None:
        _write_outputs(out_dir, payload)
    return payload


def runtime_handoff_audit_row_json_schema() -> dict[str, object]:
    required = [
        "schema_version",
        "check_id",
        "check_name",
        "category",
        "handoff_id",
        "bridge_id",
        "expected",
        "observed",
        "ok",
        "severity",
        "errors",
    ]
    string_array = {"type": "array", "items": {"type": "string"}}
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": RUNTIME_HANDOFF_AUDIT_ROW_SCHEMA_ID,
        "title": "Formalization gap planner runtime handoff audit check row",
        "type": "object",
        "additionalProperties": False,
        "required": required,
        "properties": {
            "schema_version": {
                "type": "integer",
                "const": FORMALIZATION_GAP_PLANNER_RUNTIME_HANDOFF_AUDIT_SCHEMA_VERSION,
            },
            "check_id": {"type": "string", "minLength": 1},
            "check_name": {"type": "string", "minLength": 1},
            "category": {
                "type": "string",
                "enum": [
                    "artifacts",
                    "component_resource_registry",
                    "cost_control",
                    "execution_plan",
                    "llm_prompt_smoke",
                    "proof_boundary",
                    "row",
                    "standalone_seed",
                    "standalone_smoke",
                    "reuse_smoke",
                    "target_intake",
                    "target_prover",
                ],
            },
            "handoff_id": {"type": "string"},
            "bridge_id": {"type": "string"},
            "expected": {"type": "string"},
            "observed": {"type": "string"},
            "ok": {"type": "boolean"},
            "severity": {"type": "string", "enum": ["error", "warning", "info"]},
            "errors": string_array,
        },
    }


def _runtime_handoff_execution_plan_rows(
    handoff_rows: tuple[dict[str, Any], ...] | list[dict[str, Any]],
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for row_index, handoff in enumerate(handoff_rows):
        if not isinstance(handoff, Mapping):
            continue
        if "execution_plan" not in handoff:
            continue
        execution_plan = handoff.get("execution_plan", {})
        if not isinstance(execution_plan, Mapping) or not execution_plan:
            continue
        plan_row = dict(execution_plan)
        plan_row.setdefault(
            "artifact_kind",
            "RuntimeFormalizationGapPlannerHandoffExecutionPlan",
        )
        plan_row["handoff_id"] = str(
            handoff.get("handoff_id", f"row:{row_index}")
        )
        plan_row["bridge_id"] = str(handoff.get("bridge_id", ""))
        plan_row["source_row_index"] = row_index
        rows.append(plan_row)
    return rows


def runtime_handoff_execution_plan_json_schema() -> dict[str, object]:
    """JSON Schema for replayable runtime handoff execution plans."""

    string_array = {"type": "array", "items": {"type": "string"}}
    execution_stage_schema = {
        "type": "object",
        "additionalProperties": True,
        "required": [
            "stage_id",
            "command",
            "cli",
            "argv",
            "requires_live_llm",
            "requires_operator_review_before_live",
            "required_inputs",
            "expected_outputs",
            "purpose",
            "proof_evidence_status",
            "proof_evidence_boundary",
        ],
        "properties": {
            "stage_id": {
                "type": "string",
                "enum": [
                    "standalone_plan",
                    "target_intake",
                    "component_resource_registry",
                    "llm_route_planner_prompt",
                    "llm_route_planner_live_optional",
                    "reuse_smoke",
                ],
            },
            "command": {"type": "string", "minLength": 1},
            "cli": {"type": "string", "minLength": 1},
            "argv": string_array,
            "requires_live_llm": {"type": "boolean"},
            "requires_operator_review_before_live": {"type": "boolean"},
            "required_inputs": string_array,
            "expected_outputs": string_array,
            "purpose": {"type": "string", "minLength": 1},
            "proof_evidence_status": {
                "type": "string",
                "const": RUNTIME_BRIDGE_PROOF_EVIDENCE_STATUS,
            },
            "proof_evidence_boundary": {
                "type": "string",
                "pattern": "not theorem proof evidence",
            },
        },
    }
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": RUNTIME_HANDOFF_EXECUTION_PLAN_SCHEMA_ID,
        "title": "Formalization gap planner runtime handoff execution plan",
        "description": (
            "Replayable, machine-readable execution plan for moving an AI "
            "Statistician runtime theorem route into the standalone "
            "library-aware formalization gap planner. The plan exposes offline "
            "prompt staging, optional live Claude invocation, expected inputs "
            "and outputs, and proof-evidence boundaries. It is integration "
            "metadata, not theorem proof evidence."
        ),
        "type": "object",
        "additionalProperties": True,
        "required": [
            "plan_kind",
            "schema_version",
            "recommended_llm_provider",
            "recommended_model_tier",
            "target_prover_family",
            "library_snapshot_ref",
            "stage_count",
            "stages",
            "cost_control_boundary",
            "proof_evidence_status",
            "proof_evidence_boundary",
        ],
        "properties": {
            "plan_kind": {
                "type": "string",
                "const": "runtime_formalization_gap_planner_handoff_execution_plan",
            },
            "schema_version": {"type": "integer"},
            "recommended_llm_provider": {"type": "string", "const": "anthropic"},
            "recommended_model_tier": {"type": "string", "const": "auto"},
            "target_prover_family": {"type": "string", "minLength": 1},
            "library_snapshot_ref": {"type": "string"},
            "stage_count": {"type": "integer"},
            "stages": {"type": "array", "items": execution_stage_schema},
            "cost_control_boundary": {
                "type": "string",
                "pattern": "live Claude API stage",
            },
            "proof_evidence_status": {
                "type": "string",
                "const": RUNTIME_BRIDGE_PROOF_EVIDENCE_STATUS,
            },
            "proof_evidence_boundary": {
                "type": "string",
                "pattern": "not theorem proof evidence",
            },
        },
    }


def validate_runtime_handoff_audit_row(
    row: Mapping[str, object],
    schema: Mapping[str, object] | None = None,
) -> list[str]:
    row_schema = schema or runtime_handoff_audit_row_json_schema()
    if not isinstance(row, Mapping):
        return ["row must be an object"]
    errors: list[str] = []
    required = tuple(row_schema.get("required", ()))
    for field_name in required:
        if field_name not in row:
            errors.append(f"{field_name} required")
    properties = row_schema.get("properties", {})
    if isinstance(properties, Mapping):
        for field_name, field_schema in properties.items():
            if field_name in row and isinstance(field_schema, Mapping):
                errors.extend(_schema_property_errors(field_name, row[field_name], field_schema))
    allowed = set(required)
    for field_name in row:
        if field_name not in allowed:
            errors.append(f"{field_name} unexpected")
    return sorted(set(errors))


def validate_runtime_handoff_execution_plan(
    plan: Mapping[str, object],
    schema: Mapping[str, object] | None = None,
) -> list[str]:
    plan_schema = schema or runtime_handoff_execution_plan_json_schema()
    if not isinstance(plan, Mapping):
        return ["execution_plan must be an object"]
    errors: list[str] = []
    for field_name in tuple(plan_schema.get("required", ())):
        if field_name not in plan:
            errors.append(f"{field_name} required")
    properties = plan_schema.get("properties", {})
    if isinstance(properties, Mapping):
        for field_name, field_schema in properties.items():
            if field_name in plan and isinstance(field_schema, Mapping):
                errors.extend(
                    _schema_property_errors(field_name, plan[field_name], field_schema)
                )

    stages = plan.get("stages", [])
    expected_stage_ids = [
        "standalone_plan",
        "target_intake",
        "component_resource_registry",
        "llm_route_planner_prompt",
        "llm_route_planner_live_optional",
        "reuse_smoke",
    ]
    if not isinstance(stages, list):
        errors.append("stages must be array")
        stages = []
    stage_rows = [stage for stage in stages if isinstance(stage, Mapping)]
    stage_ids = [str(stage.get("stage_id", "")).strip() for stage in stage_rows]
    if stage_ids != expected_stage_ids:
        errors.append("stages must follow the runtime handoff execution order")
    if plan.get("stage_count") != len(stage_rows):
        errors.append("stage_count must equal the number of stages")
    stage_schema = runtime_handoff_execution_plan_json_schema()["properties"][
        "stages"
    ]["items"]
    stage_required = (
        tuple(stage_schema["required"]) if isinstance(stage_schema, Mapping) else ()
    )
    for index, stage in enumerate(stage_rows):
        prefix = f"stages[{index}]"
        for field_name in stage_required:
            if field_name not in stage:
                errors.append(f"{prefix}.{field_name} required")
        argv = stage.get("argv", [])
        if not isinstance(argv, list) or not all(
            isinstance(item, str) for item in argv
        ):
            errors.append(f"{prefix}.argv must be array of strings")
        for field_name in ("requires_live_llm", "requires_operator_review_before_live"):
            if not isinstance(stage.get(field_name), bool):
                errors.append(f"{prefix}.{field_name} must be boolean")
        if (
            stage.get("proof_evidence_status")
            != RUNTIME_BRIDGE_PROOF_EVIDENCE_STATUS
        ):
            errors.append(f"{prefix}.proof_evidence_status must be not-proof evidence")

    by_stage = {
        str(stage.get("stage_id", "")).strip(): stage
        for stage in stage_rows
        if str(stage.get("stage_id", "")).strip()
    }
    prompt_argv = by_stage.get("llm_route_planner_prompt", {}).get("argv", [])
    prompt_argv = prompt_argv if isinstance(prompt_argv, list) else []
    live_argv = by_stage.get("llm_route_planner_live_optional", {}).get("argv", [])
    live_argv = live_argv if isinstance(live_argv, list) else []
    reuse_argv = by_stage.get("reuse_smoke", {}).get("argv", [])
    reuse_argv = reuse_argv if isinstance(reuse_argv, list) else []
    if "--invoke-provider" in prompt_argv:
        errors.append("llm_route_planner_prompt must not invoke the provider")
    if "--invoke-provider" not in live_argv:
        errors.append("llm_route_planner_live_optional must invoke the provider")
    if "--llm-route-planner-invoke-provider" in reuse_argv:
        errors.append("reuse_smoke must not invoke the primary route planner")
    if "--feedback-llm-route-planner-invoke-provider" in reuse_argv:
        errors.append("reuse_smoke must not invoke the feedback route planner")
    return sorted(set(errors))


def _audit_handoff_row(
    handoff: Mapping[str, Any],
    *,
    row_index: int,
    run_smoke: bool,
    smoke_root: Path | None,
) -> tuple[list[FormalizationGapPlannerRuntimeHandoffAuditCheck], dict[str, object]]:
    handoff_id = str(handoff.get("handoff_id", f"row:{row_index}"))
    bridge_id = str(handoff.get("bridge_id", ""))
    seed_path_text = str(handoff.get("standalone_seed_path", "")).strip()
    target_intake_path_text = str(handoff.get("target_intake_path", "")).strip()
    target_intake_dir_text = str(handoff.get("target_intake_dir", "")).strip()
    seed_path = Path(seed_path_text)
    target_intake_path = Path(target_intake_path_text)
    target_intake_dir = Path(target_intake_dir_text)
    standalone_plan_cli = str(handoff.get("standalone_plan_cli", ""))
    target_intake_cli = str(handoff.get("target_intake_cli", ""))
    prompt_cli = str(handoff.get("llm_route_planner_prompt_cli", ""))
    live_cli = str(handoff.get("llm_route_planner_live_cli", ""))
    reuse_smoke_cli = str(handoff.get("reuse_smoke_cli", ""))
    component_resource_registry_cli = str(
        handoff.get("component_resource_registry_cli", "")
    )
    component_resource_registry_dir_text = str(
        handoff.get("component_resource_registry_dir", "")
    ).strip()
    handoff_target = str(handoff.get("target_prover_family", "")).strip()
    execution_plan = handoff.get("execution_plan", {})
    execution_plan = execution_plan if isinstance(execution_plan, Mapping) else {}
    execution_plan_schema_errors = validate_runtime_handoff_execution_plan(
        execution_plan
    )
    execution_plan_stages = [
        dict(stage)
        for stage in execution_plan.get("stages", [])
        if isinstance(stage, Mapping)
    ]
    execution_plan_stage_ids = [
        str(stage.get("stage_id", "")).strip()
        for stage in execution_plan_stages
    ]
    expected_execution_plan_stage_ids = [
        "standalone_plan",
        "target_intake",
        "component_resource_registry",
        "llm_route_planner_prompt",
        "llm_route_planner_live_optional",
        "reuse_smoke",
    ]
    execution_stage_by_id = {
        str(stage.get("stage_id", "")).strip(): stage
        for stage in execution_plan_stages
        if str(stage.get("stage_id", "")).strip()
    }
    prompt_stage = execution_stage_by_id.get("llm_route_planner_prompt", {})
    live_stage = execution_stage_by_id.get("llm_route_planner_live_optional", {})
    reuse_smoke_stage = execution_stage_by_id.get("reuse_smoke", {})
    prompt_stage_argv = prompt_stage.get("argv", [])
    prompt_stage_argv = prompt_stage_argv if isinstance(prompt_stage_argv, list) else []
    live_stage_argv = live_stage.get("argv", [])
    live_stage_argv = live_stage_argv if isinstance(live_stage_argv, list) else []
    reuse_stage_argv = reuse_smoke_stage.get("argv", [])
    reuse_stage_argv = reuse_stage_argv if isinstance(reuse_stage_argv, list) else []
    summary: dict[str, object] = {
        "handoff_id": handoff_id,
        "bridge_id": bridge_id,
        "standalone_seed_path": seed_path_text,
        "target_intake_path": target_intake_path_text,
        "target_intake_dir": target_intake_dir_text,
        "target_prover_family": handoff_target,
        "seed_exists": bool(seed_path_text) and seed_path.exists(),
        "target_intake_exists": (
            bool(target_intake_path_text) and target_intake_path.exists()
        ),
        "target_intake_dir_exists": (
            bool(target_intake_dir_text) and target_intake_dir.exists()
        ),
        "execution_plan_present": bool(execution_plan),
        "execution_plan_stage_count": len(execution_plan_stages),
        "execution_plan_stage_ids": execution_plan_stage_ids,
        "execution_plan_schema_valid": not execution_plan_schema_errors,
        "execution_plan_schema_errors": execution_plan_schema_errors,
        "execution_plan_prompt_stage_cost_control_ok": False,
        "execution_plan_live_stage_explicit_ok": False,
        "execution_plan_reuse_smoke_stage_cost_control_ok": False,
        "seed_schema_ok": False,
        "cost_control_ok": False,
        "live_explicit_ok": False,
        "reuse_smoke_cost_control_ok": False,
        "component_resource_registry_smoke_ok": False,
        "llm_prompt_component_resource_registry_components": 0,
        "llm_prompt_component_resource_registry_resources": 0,
        "llm_prompt_component_resource_registry_contracts": 0,
        "target_intake_smoke_ok": False,
        "target_intake_targets": 0,
        "target_intake_primitive_seeds": 0,
        "standalone_smoke_ok": False,
        "llm_prompt_smoke_ok": False,
        "llm_prompt_packets": 0,
        "llm_prompt_awaiting_response": 0,
        "llm_prompt_requests_with_minimal_delta_cost_hints": 0,
        "llm_prompt_primitive_cost_hints": 0,
        "llm_prompt_route_option_cost_hints": 0,
        "llm_prompt_requests_with_target_intake_rows": 0,
        "llm_prompt_target_intake_rows": 0,
        "llm_prompt_model_tier_mismatches": 0,
        "llm_prompt_model_tier_haiku": 0,
        "llm_prompt_model_tier_sonnet": 0,
        "llm_prompt_model_tier_opus": 0,
        "seed_routes": 0,
        "seed_primitives": 0,
        "seed_residual_goals": 0,
        "seed_candidate_declaration_rows": 0,
        "seed_primitives_with_candidate_declaration_rows": 0,
    }
    seed_errors: list[str] = []
    seed_payload = _read_json(seed_path, seed_errors)
    validation_errors = validate_standalone_input_payload(seed_payload)
    seed_schema_ok = not seed_errors and not validation_errors
    summary["seed_schema_ok"] = seed_schema_ok
    summary.update(_seed_context_counts(seed_payload))
    seed_target_summary = _seed_target_prover_summary(seed_payload)
    summary.update(seed_target_summary)
    seed_target = str(seed_target_summary.get("seed_target_prover_family", ""))
    seed_target_compatible = _seed_target_compatible_with_handoff(
        handoff_target,
        seed_target_summary,
    )
    summary["seed_target_prover_family_compatible_with_handoff"] = (
        seed_target_compatible
    )
    seed_snapshot = str(seed_payload.get("library_snapshot_ref", "")).strip()
    cost_control_ok = _prompt_cli_cost_control_ok(
        prompt_cli,
        target_intake_dir_text=target_intake_dir_text,
        component_resource_registry_dir_text=component_resource_registry_dir_text,
    )
    live_explicit_ok = _live_cli_explicit_ok(
        live_cli,
        target_intake_dir_text=target_intake_dir_text,
        component_resource_registry_dir_text=component_resource_registry_dir_text,
    )
    reuse_smoke_cost_control_ok = _reuse_smoke_cli_cost_control_ok(
        reuse_smoke_cli,
        target_intake_path_text=target_intake_path_text,
        target_prover_family=handoff_target,
        library_snapshot_ref=seed_snapshot,
    )
    execution_plan_prompt_stage_cost_control_ok = (
        bool(prompt_stage)
        and prompt_stage.get("cli") == prompt_cli
        and prompt_stage.get("requires_live_llm") is False
        and prompt_stage.get("requires_operator_review_before_live") is False
        and "--invoke-provider" not in prompt_stage_argv
        and "--model-tier" in prompt_stage_argv
        and "auto" in prompt_stage_argv
        and _prompt_cli_cost_control_ok(
            str(prompt_stage.get("cli", "")),
            target_intake_dir_text=target_intake_dir_text,
            component_resource_registry_dir_text=component_resource_registry_dir_text,
        )
    )
    execution_plan_live_stage_explicit_ok = (
        bool(live_stage)
        and live_stage.get("cli") == live_cli
        and live_stage.get("requires_live_llm") is True
        and live_stage.get("requires_operator_review_before_live") is True
        and "--invoke-provider" in live_stage_argv
        and "--model-tier" in live_stage_argv
        and "auto" in live_stage_argv
        and _live_cli_explicit_ok(
            str(live_stage.get("cli", "")),
            target_intake_dir_text=target_intake_dir_text,
            component_resource_registry_dir_text=component_resource_registry_dir_text,
        )
    )
    execution_plan_reuse_smoke_stage_cost_control_ok = (
        bool(reuse_smoke_stage)
        and reuse_smoke_stage.get("cli") == reuse_smoke_cli
        and reuse_smoke_stage.get("requires_live_llm") is False
        and reuse_smoke_stage.get("requires_operator_review_before_live") is False
        and "--llm-route-planner-invoke-provider" not in reuse_stage_argv
        and "--feedback-llm-route-planner-invoke-provider" not in reuse_stage_argv
        and _reuse_smoke_cli_cost_control_ok(
            str(reuse_smoke_stage.get("cli", "")),
            target_intake_path_text=target_intake_path_text,
            target_prover_family=handoff_target,
            library_snapshot_ref=seed_snapshot,
        )
    )
    summary["cost_control_ok"] = cost_control_ok
    summary["live_explicit_ok"] = live_explicit_ok
    summary["reuse_smoke_cost_control_ok"] = reuse_smoke_cost_control_ok
    summary["execution_plan_prompt_stage_cost_control_ok"] = (
        execution_plan_prompt_stage_cost_control_ok
    )
    summary["execution_plan_live_stage_explicit_ok"] = (
        execution_plan_live_stage_explicit_ok
    )
    summary["execution_plan_reuse_smoke_stage_cost_control_ok"] = (
        execution_plan_reuse_smoke_stage_cost_control_ok
    )
    checks = [
        _row_check(
            "row_artifact_kind",
            "row",
            handoff_id,
            bridge_id,
            "RuntimeFormalizationGapPlannerHandoff",
            str(handoff.get("artifact_kind", "")),
            handoff.get("artifact_kind") == "RuntimeFormalizationGapPlannerHandoff",
        ),
        _row_check(
            "row_bridge_id_present",
            "row",
            handoff_id,
            bridge_id,
            "bridge_id nonempty",
            bridge_id,
            bool(bridge_id),
        ),
        _row_check(
            "row_seed_path_exists",
            "standalone_seed",
            handoff_id,
            bridge_id,
            "standalone seed path exists",
            str(seed_path.exists()),
            seed_path.exists(),
        ),
        _row_check(
            "row_target_intake_path_exists",
            "target_intake",
            handoff_id,
            bridge_id,
            "target intake path exists",
            str(bool(target_intake_path_text) and target_intake_path.exists()),
            bool(target_intake_path_text) and target_intake_path.exists(),
        ),
        _row_check(
            "row_seed_component",
            "standalone_seed",
            handoff_id,
            bridge_id,
            FORMALIZATION_GAP_PLANNER_STANDALONE_INPUT_COMPONENT,
            str(seed_payload.get("component_name", "")),
            seed_payload.get("component_name")
            == FORMALIZATION_GAP_PLANNER_STANDALONE_INPUT_COMPONENT,
        ),
        _row_check(
            "row_target_prover_family_present",
            "target_prover",
            handoff_id,
            bridge_id,
            "handoff target_prover_family nonempty",
            handoff_target,
            bool(handoff_target),
        ),
        _row_check(
            "row_seed_target_prover_family_present",
            "target_prover",
            handoff_id,
            bridge_id,
            "standalone seed target_prover_family nonempty",
            seed_target,
            bool(seed_target),
        ),
        _row_check(
            "row_seed_target_prover_family_matches_handoff",
            "target_prover",
            handoff_id,
            bridge_id,
            "handoff target compatible with standalone seed target family",
            seed_target,
            seed_target_compatible,
        ),
        _row_check(
            "row_seed_schema_valid",
            "standalone_seed",
            handoff_id,
            bridge_id,
            "validate_standalone_input_payload has no errors",
            "; ".join([*seed_errors, *validation_errors]),
            seed_schema_ok,
        ),
        _row_check(
            "row_seed_routes_present",
            "standalone_seed",
            handoff_id,
            bridge_id,
            "at least one seed route",
            str(len(seed_payload.get("routes", [])) if isinstance(seed_payload.get("routes"), list) else 0),
            isinstance(seed_payload.get("routes"), list) and bool(seed_payload.get("routes")),
        ),
        _row_check(
            "row_recommended_provider",
            "cost_control",
            handoff_id,
            bridge_id,
            "anthropic",
            str(handoff.get("recommended_llm_provider", "")),
            handoff.get("recommended_llm_provider") == "anthropic",
        ),
        _row_check(
            "row_recommended_model_tier",
            "cost_control",
            handoff_id,
            bridge_id,
            "auto",
            str(handoff.get("recommended_model_tier", "")),
            handoff.get("recommended_model_tier") == "auto",
        ),
        _row_check(
            "row_standalone_cli_present",
            "row",
            handoff_id,
            bridge_id,
            "formalization-gap-planner-standalone-plan command",
            standalone_plan_cli,
            "formalization-gap-planner-standalone-plan" in standalone_plan_cli,
        ),
        _row_check(
            "row_target_intake_cli_present",
            "target_intake",
            handoff_id,
            bridge_id,
            "formalization-gap-planner-target-intake command",
            target_intake_cli,
            "formalization-gap-planner-target-intake" in target_intake_cli
            and target_intake_path_text in target_intake_cli
            and (
                not target_intake_dir_text
                or target_intake_dir_text in target_intake_cli
            ),
        ),
        _row_check(
            "row_reuse_smoke_cli_present",
            "reuse_smoke",
            handoff_id,
            bridge_id,
            "formalization-gap-planner-reuse-smoke command",
            reuse_smoke_cli,
            "formalization-gap-planner-reuse-smoke" in reuse_smoke_cli,
        ),
        _row_check(
            "row_component_resource_registry_cli_present",
            "component_resource_registry",
            handoff_id,
            bridge_id,
            "formalization-gap-planner-component-resource-registry command",
            component_resource_registry_cli,
            "formalization-gap-planner-component-resource-registry"
            in component_resource_registry_cli,
        ),
        _row_check(
            "row_prompt_cli_has_target_intake_context",
            "target_intake",
            handoff_id,
            bridge_id,
            "--formalization-gap-planner-target-intake-dir",
            prompt_cli,
            "--formalization-gap-planner-target-intake-dir" in prompt_cli
            and (not target_intake_dir_text or target_intake_dir_text in prompt_cli),
        ),
        _row_check(
            "row_live_cli_has_target_intake_context",
            "target_intake",
            handoff_id,
            bridge_id,
            "--formalization-gap-planner-target-intake-dir",
            live_cli,
            "--formalization-gap-planner-target-intake-dir" in live_cli
            and (not target_intake_dir_text or target_intake_dir_text in live_cli),
        ),
        _row_check(
            "row_prompt_cli_has_component_resource_registry_context",
            "component_resource_registry",
            handoff_id,
            bridge_id,
            "--formalization-gap-planner-component-resource-registry-dir",
            prompt_cli,
            "--formalization-gap-planner-component-resource-registry-dir"
            in prompt_cli
            and (
                not component_resource_registry_dir_text
                or component_resource_registry_dir_text in prompt_cli
            ),
        ),
        _row_check(
            "row_live_cli_has_component_resource_registry_context",
            "component_resource_registry",
            handoff_id,
            bridge_id,
            "--formalization-gap-planner-component-resource-registry-dir",
            live_cli,
            "--formalization-gap-planner-component-resource-registry-dir"
            in live_cli
            and (
                not component_resource_registry_dir_text
                or component_resource_registry_dir_text in live_cli
            ),
        ),
        _row_check(
            "row_prompt_cli_cost_control",
            "cost_control",
            handoff_id,
            bridge_id,
            "Anthropic auto prompt-only command without --invoke-provider",
            prompt_cli,
            cost_control_ok,
        ),
        _row_check(
            "row_reuse_smoke_cli_cost_control",
            "cost_control",
            handoff_id,
            bridge_id,
            "Anthropic auto reuse-smoke command without live provider flags",
            reuse_smoke_cli,
            reuse_smoke_cost_control_ok,
        ),
        _row_check(
            "row_live_cli_explicit",
            "cost_control",
            handoff_id,
            bridge_id,
            "Anthropic auto command with explicit --invoke-provider",
            live_cli,
            live_explicit_ok,
        ),
        _row_check(
            "row_execution_plan_present",
            "execution_plan",
            handoff_id,
            bridge_id,
            "execution_plan present",
            str(bool(execution_plan)),
            bool(execution_plan),
        ),
        _row_check(
            "row_execution_plan_kind",
            "execution_plan",
            handoff_id,
            bridge_id,
            "runtime_formalization_gap_planner_handoff_execution_plan",
            str(execution_plan.get("plan_kind", "")),
            execution_plan.get("plan_kind")
            == "runtime_formalization_gap_planner_handoff_execution_plan",
        ),
        _row_check(
            "row_execution_plan_schema_valid",
            "execution_plan",
            handoff_id,
            bridge_id,
            RUNTIME_HANDOFF_EXECUTION_PLAN_SCHEMA_ID,
            "; ".join(execution_plan_schema_errors),
            not execution_plan_schema_errors,
        ),
        _row_check(
            "row_execution_plan_stage_ids",
            "execution_plan",
            handoff_id,
            bridge_id,
            ",".join(expected_execution_plan_stage_ids),
            ",".join(execution_plan_stage_ids),
            execution_plan_stage_ids == expected_execution_plan_stage_ids,
        ),
        _row_check(
            "row_execution_plan_stage_count",
            "execution_plan",
            handoff_id,
            bridge_id,
            str(len(expected_execution_plan_stage_ids)),
            str(execution_plan.get("stage_count", "")),
            execution_plan.get("stage_count") == len(execution_plan_stages)
            and len(execution_plan_stages) == len(expected_execution_plan_stage_ids),
        ),
        _row_check(
            "row_execution_plan_provider",
            "execution_plan",
            handoff_id,
            bridge_id,
            "anthropic/auto",
            (
                f"{execution_plan.get('recommended_llm_provider', '')}/"
                f"{execution_plan.get('recommended_model_tier', '')}"
            ),
            execution_plan.get("recommended_llm_provider") == "anthropic"
            and execution_plan.get("recommended_model_tier") == "auto",
        ),
        _row_check(
            "row_execution_plan_prompt_stage_cost_control",
            "execution_plan",
            handoff_id,
            bridge_id,
            "prompt stage has argv, model-tier auto, no --invoke-provider",
            str(prompt_stage_argv),
            execution_plan_prompt_stage_cost_control_ok,
        ),
        _row_check(
            "row_execution_plan_live_stage_explicit",
            "execution_plan",
            handoff_id,
            bridge_id,
            "live stage requires operator review and --invoke-provider",
            str(live_stage_argv),
            execution_plan_live_stage_explicit_ok,
        ),
        _row_check(
            "row_execution_plan_reuse_smoke_stage_cost_control",
            "execution_plan",
            handoff_id,
            bridge_id,
            "reuse-smoke stage has no live route-planner flags",
            str(reuse_stage_argv),
            execution_plan_reuse_smoke_stage_cost_control_ok,
        ),
        _row_check(
            "row_execution_plan_proof_evidence_status",
            "execution_plan",
            handoff_id,
            bridge_id,
            RUNTIME_BRIDGE_PROOF_EVIDENCE_STATUS,
            str(execution_plan.get("proof_evidence_status", "")),
            execution_plan.get("proof_evidence_status")
            == RUNTIME_BRIDGE_PROOF_EVIDENCE_STATUS,
        ),
        _row_check(
            "row_cost_control_text",
            "cost_control",
            handoff_id,
            bridge_id,
            "cost_control explains prompt first and explicit live execution",
            str(handoff.get("cost_control", "")),
            "prompt" in str(handoff.get("cost_control", "")).lower()
            and "explicit" in str(handoff.get("cost_control", "")).lower(),
        ),
        _row_check(
            "row_proof_evidence_status",
            "proof_boundary",
            handoff_id,
            bridge_id,
            RUNTIME_BRIDGE_PROOF_EVIDENCE_STATUS,
            str(handoff.get("proof_evidence_status", "")),
            handoff.get("proof_evidence_status") == RUNTIME_BRIDGE_PROOF_EVIDENCE_STATUS,
        ),
        _row_check(
            "row_proof_evidence_boundary",
            "proof_boundary",
            handoff_id,
            bridge_id,
            "not theorem proof evidence",
            str(handoff.get("proof_evidence_boundary", ""))[:180],
            "not theorem proof evidence"
            in str(handoff.get("proof_evidence_boundary", "")).lower(),
        ),
        _row_check(
            "row_no_kernel_proof_claim",
            "proof_boundary",
            handoff_id,
            bridge_id,
            "no kernel-verified/proved claim",
            _proof_claim_observed(handoff),
            not _has_kernel_proof_claim(handoff),
        ),
    ]
    target_intake_smoke_dir = (
        _smoke_dir(smoke_root, handoff_id) / "target_intake"
        if smoke_root is not None
        else None
    )
    llm_prompt_target_intake_dir: Path | None = None
    if run_smoke and bool(target_intake_path_text) and target_intake_path.exists():
        target_ok, target_observed, target_counts = _run_target_intake_smoke(
            target_intake_path,
            handoff_id=handoff_id,
            smoke_root=smoke_root,
        )
        summary.update(target_counts)
        summary["target_intake_smoke_ok"] = target_ok
        if target_ok:
            llm_prompt_target_intake_dir = target_intake_smoke_dir
        checks.append(
            _row_check(
                "row_target_intake_smoke",
                "target_intake",
                handoff_id,
                bridge_id,
                "target intake normalizes to standalone seed",
                target_observed,
                target_ok,
            )
        )
    elif run_smoke:
        checks.append(
            _row_check(
                "row_target_intake_smoke",
                "target_intake",
                handoff_id,
                bridge_id,
                "target intake normalizes to standalone seed",
                "skipped because target intake path missing",
                False,
            )
        )
    if run_smoke and seed_schema_ok:
        registry_ok, registry_observed, registry_dir = (
            _run_component_resource_registry_smoke(
                handoff_id=handoff_id,
                smoke_root=smoke_root,
            )
        )
        summary["component_resource_registry_smoke_ok"] = registry_ok
        checks.append(
            _row_check(
                "row_component_resource_registry_smoke",
                "component_resource_registry",
                handoff_id,
                bridge_id,
                "component-resource registry exports reusable tool contracts",
                registry_observed,
                registry_ok,
            )
        )
        standalone_ok, standalone_observed = _run_standalone_smoke(
            seed_path,
            handoff_id=handoff_id,
            smoke_root=smoke_root,
        )
        summary["standalone_smoke_ok"] = standalone_ok
        checks.append(
            _row_check(
                "row_standalone_smoke",
                "standalone_smoke",
                handoff_id,
                bridge_id,
                "standalone planner all_ok true",
                standalone_observed,
                standalone_ok,
            )
        )
        llm_ok, llm_observed, llm_counts = _run_llm_prompt_smoke(
            seed_path,
            handoff_id=handoff_id,
            smoke_root=smoke_root,
            target_intake_dir=llm_prompt_target_intake_dir,
            component_resource_registry_dir=registry_dir if registry_ok else None,
        )
        summary.update(llm_counts)
        summary["llm_prompt_smoke_ok"] = llm_ok
        checks.append(
            _row_check(
                "row_llm_prompt_smoke",
                "llm_prompt_smoke",
                handoff_id,
                bridge_id,
                "prompt-only Anthropic route planner stages awaiting requests",
                llm_observed,
                llm_ok,
            )
        )
        checks.append(
            _row_check(
                "row_llm_prompt_has_component_resource_registry_context",
                "component_resource_registry",
                handoff_id,
                bridge_id,
                "prompt packets include component/resource/contract rows",
                llm_observed,
                llm_ok
                and int(
                    llm_counts.get(
                        "llm_prompt_component_resource_registry_components",
                        0,
                    )
                    or 0
                )
                > 0
                and int(
                    llm_counts.get(
                        "llm_prompt_component_resource_registry_resources",
                        0,
                    )
                    or 0
                )
                > 0
                and int(
                    llm_counts.get(
                        "llm_prompt_component_resource_registry_contracts",
                        0,
                    )
                    or 0
                )
                > 0,
            )
        )
        target_intake_context_ok = (
            llm_ok
            and int(
                llm_counts.get(
                    "llm_prompt_requests_with_target_intake_rows",
                    0,
                )
                or 0
            )
            == int(llm_counts.get("llm_prompt_packets", 0) or 0)
            and int(llm_counts.get("llm_prompt_target_intake_rows", 0) or 0) > 0
        )
        checks.append(
            _row_check(
                "row_llm_prompt_has_target_intake_context",
                "target_intake",
                handoff_id,
                bridge_id,
                "prompt packets include normalized target-intake rows",
                llm_observed,
                target_intake_context_ok,
            )
        )
        cost_hint_ok = (
            llm_ok
            and int(
                llm_counts.get(
                    "llm_prompt_requests_with_minimal_delta_cost_hints",
                    0,
                )
                or 0
            )
            == int(llm_counts.get("llm_prompt_packets", 0) or 0)
            and int(llm_counts.get("llm_prompt_primitive_cost_hints", 0) or 0) > 0
            and int(llm_counts.get("llm_prompt_route_option_cost_hints", 0) or 0)
            > 0
            and int(llm_counts.get("llm_prompt_model_tier_mismatches", 0) or 0)
            == 0
        )
        checks.append(
            _row_check(
                "row_llm_prompt_has_minimal_delta_cost_hints",
                "cost_control",
                handoff_id,
                bridge_id,
                "prompt packets include minimal-delta cost hints and no tier mismatches",
                llm_observed,
                cost_hint_ok,
            )
        )
    elif run_smoke:
        checks.extend(
            [
                _row_check(
                    "row_component_resource_registry_smoke",
                    "component_resource_registry",
                    handoff_id,
                    bridge_id,
                    "component-resource registry exports reusable tool contracts",
                    "skipped because seed schema invalid",
                    False,
                ),
                _row_check(
                    "row_standalone_smoke",
                    "standalone_smoke",
                    handoff_id,
                    bridge_id,
                    "standalone planner all_ok true",
                    "skipped because seed schema invalid",
                    False,
                ),
                _row_check(
                    "row_llm_prompt_smoke",
                    "llm_prompt_smoke",
                    handoff_id,
                    bridge_id,
                    "prompt-only Anthropic route planner stages awaiting requests",
                    "skipped because seed schema invalid",
                    False,
                ),
                _row_check(
                    "row_llm_prompt_has_component_resource_registry_context",
                    "component_resource_registry",
                    handoff_id,
                    bridge_id,
                    "prompt packets include component/resource/contract rows",
                    "skipped because seed schema invalid",
                    False,
                ),
                _row_check(
                    "row_llm_prompt_has_minimal_delta_cost_hints",
                    "cost_control",
                    handoff_id,
                    bridge_id,
                    "prompt packets include minimal-delta cost hints and no tier mismatches",
                    "skipped because seed schema invalid",
                    False,
                ),
            ]
        )
    return checks, summary


def _seed_context_counts(seed_payload: Mapping[str, Any]) -> dict[str, int]:
    routes = [
        dict(route)
        for route in seed_payload.get("routes", [])
        if isinstance(route, Mapping)
    ]
    primitives = [
        dict(primitive)
        for route in routes
        for primitive in route.get("primitives", [])
        if isinstance(primitive, Mapping)
    ]
    residual_goals = [
        residual_goal
        for route in routes
        for residual_goal in _str_tuple(
            _dict_value(route.get("replan_metadata", {})).get("residual_goals", [])
        )
    ]
    candidate_declaration_rows = [
        row
        for primitive in primitives
        for row in _dict_tuple(primitive.get("candidate_declaration_rows", []))
    ]
    return {
        "seed_routes": len(routes),
        "seed_primitives": len(primitives),
        "seed_residual_goals": len(residual_goals),
        "seed_candidate_declaration_rows": len(candidate_declaration_rows),
        "seed_primitives_with_candidate_declaration_rows": sum(
            1 for primitive in primitives if primitive.get("candidate_declaration_rows")
        ),
    }


def _seed_target_prover_summary(seed_payload: Mapping[str, Any]) -> dict[str, object]:
    top_level_target = str(seed_payload.get("target_prover_family", "")).strip()
    route_targets = _seed_route_target_prover_families(seed_payload)
    by_target = Counter(route_targets)
    unique_targets: list[str] = []
    seen: set[str] = set()
    for target in route_targets:
        key = _target_prover_key(target)
        if not key or key in seen:
            continue
        seen.add(key)
        unique_targets.append(target)
    top_mixed_keys = _mixed_target_prover_keys(top_level_target)
    if len(unique_targets) == 1:
        effective_target = unique_targets[0]
    elif len(unique_targets) > 1:
        effective_target = "mixed:" + ",".join(sorted(unique_targets))
    else:
        effective_target = top_level_target
    target_keys = (
        {_target_prover_key(target) for target in unique_targets}
        if unique_targets
        else top_mixed_keys or {_target_prover_key(top_level_target)}
    )
    target_keys.discard("")
    return {
        "seed_declared_target_prover_family": top_level_target,
        "seed_target_prover_family": effective_target,
        "seed_n_target_prover_families": len(target_keys),
        "seed_by_target_prover_family": dict(sorted(by_target.items())),
        "seed_target_prover_family_keys": tuple(sorted(target_keys)),
    }


def _seed_route_target_prover_families(
    seed_payload: Mapping[str, Any],
) -> tuple[str, ...]:
    targets: list[str] = []
    for route in seed_payload.get("routes", []):
        if not isinstance(route, Mapping):
            continue
        metadata = _dict_value(route.get("replan_metadata", {}))
        target = str(
            route.get("target_prover_family")
            or route.get("target_prover")
            or metadata.get("target_prover_family")
            or metadata.get("target_prover")
            or ""
        ).strip()
        if target:
            targets.append(target)
    return tuple(targets)


def _seed_target_compatible_with_handoff(
    handoff_target: str,
    seed_target_summary: Mapping[str, object],
) -> bool:
    handoff_keys = _mixed_target_prover_keys(handoff_target)
    handoff_key = _target_prover_key(handoff_target)
    seed_keys = {
        str(key)
        for key in seed_target_summary.get("seed_target_prover_family_keys", [])
        if str(key)
    }
    if not seed_keys or not (handoff_keys or handoff_key):
        return False
    if handoff_keys:
        return seed_keys == handoff_keys
    return handoff_key in seed_keys


def _mixed_target_prover_keys(value: object) -> set[str]:
    target = str(value or "").strip()
    if not target.lower().startswith("mixed:"):
        return set()
    return {
        key
        for key in (
            _target_prover_key(part)
            for part in target.split(":", 1)[1].split(",")
        )
        if key
    }


def _target_prover_key(value: object) -> str:
    target = re.sub(
        r"[^a-z0-9]+",
        "_",
        str(value or "").strip().lower(),
    ).strip("_")
    aliases = {
        "lean": "lean4",
        "lean_4": "lean4",
        "coq": "rocq",
        "coq8": "rocq",
        "rocq_coq": "rocq",
        "coq_rocq": "rocq",
        "isabelle_hol": "isabelle",
    }
    return aliases.get(target, target)


def _run_component_resource_registry_smoke(
    *,
    handoff_id: str,
    smoke_root: Path | None,
) -> tuple[bool, str, Path | None]:
    registry_dir = (
        _smoke_dir(smoke_root, handoff_id) / "component_resource_registry"
        if smoke_root is not None
        else Path(tempfile.mkdtemp(prefix="fgp_runtime_registry_"))
    )
    try:
        payload = export_formalization_gap_planner_component_resource_registry(
            registry_dir,
        )
    except Exception as exc:  # pragma: no cover - defensive audit surface
        return False, f"{type(exc).__name__}: {exc}", None
    ok = (
        bool(payload.get("all_ok", False))
        and int(payload.get("n_component_rows", 0) or 0) > 0
        and int(payload.get("n_resources", 0) or 0) > 0
        and int(payload.get("n_resource_contract_rows", 0) or 0) > 0
        and (registry_dir is None or registry_dir.exists())
    )
    return ok, (
        f"all_ok={payload.get('all_ok')} "
        f"components={payload.get('n_component_rows')} "
        f"resources={payload.get('n_resources')} "
        f"contracts={payload.get('n_resource_contract_rows')} "
        f"errors={payload.get('errors')}"
    ), registry_dir


def _run_standalone_smoke(
    seed_path: Path,
    *,
    handoff_id: str,
    smoke_root: Path | None,
) -> tuple[bool, str]:
    try:
        payload = export_formalization_gap_planner_standalone_plan(
            seed_path,
            _smoke_dir(smoke_root, handoff_id) / "standalone_plan"
            if smoke_root is not None
            else None,
            max_routes=20,
        )
    except Exception as exc:  # pragma: no cover - defensive audit surface
        return False, f"{type(exc).__name__}: {exc}"
    return bool(payload.get("all_ok", False)), (
        f"all_ok={payload.get('all_ok')} "
        f"goal_plans={payload.get('n_goal_plans')} "
        f"errors={payload.get('errors')}"
    )


def _run_llm_prompt_smoke(
    seed_path: Path,
    *,
    handoff_id: str,
    smoke_root: Path | None,
    target_intake_dir: Path | None = None,
    component_resource_registry_dir: Path | None = None,
) -> tuple[bool, str, dict[str, int]]:
    try:
        payload = export_formalization_gap_planner_llm_route_planner(
            seed_path,
            _smoke_dir(smoke_root, handoff_id) / "llm_route_planner_prompt"
            if smoke_root is not None
            else None,
            provider_name="anthropic",
            model_tier="auto",
            max_repair_attempts=1,
            invoke_provider=False,
            formalization_gap_planner_target_intake_dir=target_intake_dir,
            formalization_gap_planner_component_resource_registry_dir=(
                component_resource_registry_dir
            ),
        )
    except Exception as exc:  # pragma: no cover - defensive audit surface
        return (
            False,
            f"{type(exc).__name__}: {exc}",
            {
                "llm_prompt_packets": 0,
                "llm_prompt_awaiting_response": 0,
                "llm_prompt_requests_with_minimal_delta_cost_hints": 0,
                "llm_prompt_primitive_cost_hints": 0,
                "llm_prompt_route_option_cost_hints": 0,
                "llm_prompt_requests_with_target_intake_rows": 0,
                "llm_prompt_target_intake_rows": 0,
                "llm_prompt_model_tier_mismatches": 0,
                "llm_prompt_model_tier_haiku": 0,
                "llm_prompt_model_tier_sonnet": 0,
                "llm_prompt_model_tier_opus": 0,
                "llm_prompt_component_resource_registry_components": 0,
                "llm_prompt_component_resource_registry_resources": 0,
                "llm_prompt_component_resource_registry_contracts": 0,
            },
        )
    n_packets = int(payload.get("n_request_packets", 0) or 0)
    n_awaiting = int(payload.get("n_awaiting_llm_response", 0) or 0)
    n_registry_components = int(
        payload.get("n_component_resource_registry_components_in_prompt", 0) or 0
    )
    n_registry_resources = int(
        payload.get("n_component_resource_registry_resources_in_prompt", 0) or 0
    )
    n_registry_contracts = int(
        payload.get("n_component_resource_registry_contracts_in_prompt", 0) or 0
    )
    n_requests_with_cost_hints = int(
        payload.get("n_requests_with_minimal_delta_cost_hints", 0) or 0
    )
    n_primitive_cost_hints = int(
        payload.get("n_request_primitive_cost_hints", 0) or 0
    )
    n_route_option_cost_hints = int(
        payload.get("n_request_route_option_cost_hints", 0) or 0
    )
    n_requests_with_target_intake = int(
        payload.get("n_requests_with_target_intake_rows", 0) or 0
    )
    n_target_intake_rows = int(payload.get("n_request_target_intake_rows", 0) or 0)
    n_model_tier_mismatches = int(
        payload.get("n_request_model_tier_mismatches", 0) or 0
    )
    n_tier_haiku = int(payload.get("n_request_model_tier_haiku", 0) or 0)
    n_tier_sonnet = int(payload.get("n_request_model_tier_sonnet", 0) or 0)
    n_tier_opus = int(payload.get("n_request_model_tier_opus", 0) or 0)
    n_tier_accounted = n_tier_haiku + n_tier_sonnet + n_tier_opus
    ok = (
        bool(payload.get("all_ok", False))
        and n_packets > 0
        and n_awaiting == n_packets
        and bool(payload.get("invoke_provider", True)) is False
        and str(payload.get("provider_name", "")) == "anthropic"
        and str(payload.get("model_tier_selection_mode", "")) == "auto"
        and n_requests_with_cost_hints == n_packets
        and n_primitive_cost_hints > 0
        and n_route_option_cost_hints > 0
        and (
            target_intake_dir is None
            or (
                n_requests_with_target_intake == n_packets
                and n_target_intake_rows > 0
            )
        )
        and n_model_tier_mismatches == 0
        and n_tier_accounted == n_packets
    )
    return ok, (
        f"all_ok={payload.get('all_ok')} provider={payload.get('provider_name')} "
        f"invoke_provider={payload.get('invoke_provider')} "
        f"tier_mode={payload.get('model_tier_selection_mode')} "
        f"packets={n_packets} awaiting={n_awaiting} "
        f"cost_hint_requests={n_requests_with_cost_hints} "
        f"primitive_cost_hints={n_primitive_cost_hints} "
        f"route_option_cost_hints={n_route_option_cost_hints} "
        f"target_intake_requests={n_requests_with_target_intake} "
        f"target_intake_rows={n_target_intake_rows} "
        f"model_tier_mismatches={n_model_tier_mismatches} "
        f"model_tiers=haiku:{n_tier_haiku},sonnet:{n_tier_sonnet},opus:{n_tier_opus} "
        f"registry_components={n_registry_components} "
        f"registry_resources={n_registry_resources} "
        f"registry_contracts={n_registry_contracts} "
        f"errors={payload.get('errors')}"
    ), {
        "llm_prompt_packets": n_packets,
        "llm_prompt_awaiting_response": n_awaiting,
        "llm_prompt_requests_with_minimal_delta_cost_hints": n_requests_with_cost_hints,
        "llm_prompt_primitive_cost_hints": n_primitive_cost_hints,
        "llm_prompt_route_option_cost_hints": n_route_option_cost_hints,
        "llm_prompt_requests_with_target_intake_rows": n_requests_with_target_intake,
        "llm_prompt_target_intake_rows": n_target_intake_rows,
        "llm_prompt_model_tier_mismatches": n_model_tier_mismatches,
        "llm_prompt_model_tier_haiku": n_tier_haiku,
        "llm_prompt_model_tier_sonnet": n_tier_sonnet,
        "llm_prompt_model_tier_opus": n_tier_opus,
        "llm_prompt_component_resource_registry_components": n_registry_components,
        "llm_prompt_component_resource_registry_resources": n_registry_resources,
        "llm_prompt_component_resource_registry_contracts": n_registry_contracts,
    }


def _run_target_intake_smoke(
    target_intake_path: Path,
    *,
    handoff_id: str,
    smoke_root: Path | None,
) -> tuple[bool, str, dict[str, int]]:
    try:
        payload = normalize_formalization_gap_planner_target_intake(
            target_intake_path,
            _smoke_dir(smoke_root, handoff_id) / "target_intake"
            if smoke_root is not None
            else None,
        )
    except Exception as exc:  # pragma: no cover - defensive audit surface
        return (
            False,
            f"{type(exc).__name__}: {exc}",
            {"target_intake_targets": 0, "target_intake_primitive_seeds": 0},
        )
    standalone_seed = payload.get("standalone_seed", {})
    standalone_component = (
        str(standalone_seed.get("component_name", ""))
        if isinstance(standalone_seed, Mapping)
        else ""
    )
    n_targets = int(payload.get("n_targets", 0) or 0)
    n_primitive_seeds = int(payload.get("n_primitive_seed_rows", 0) or 0)
    ok = (
        bool(payload.get("all_ok", False))
        and str(payload.get("component_name", ""))
        == FORMALIZATION_GAP_PLANNER_TARGET_INTAKE_COMPONENT
        and standalone_component == FORMALIZATION_GAP_PLANNER_STANDALONE_INPUT_COMPONENT
        and n_targets > 0
        and n_primitive_seeds > 0
    )
    return ok, (
        f"all_ok={payload.get('all_ok')} component={payload.get('component_name')} "
        f"standalone_component={standalone_component} targets={n_targets} "
        f"primitive_seeds={n_primitive_seeds} errors={payload.get('errors')}"
    ), {
        "target_intake_targets": n_targets,
        "target_intake_primitive_seeds": n_primitive_seeds,
    }


def _prompt_cli_cost_control_ok(
    prompt_cli: str,
    *,
    target_intake_dir_text: str,
    component_resource_registry_dir_text: str,
) -> bool:
    return (
        "formalization-gap-planner-llm-route-planner" in prompt_cli
        and "--provider anthropic" in prompt_cli
        and "--model-tier auto" in prompt_cli
        and "--max-repair-attempts 1" in prompt_cli
        and "--formalization-gap-planner-target-intake-dir" in prompt_cli
        and (
            not target_intake_dir_text
            or target_intake_dir_text in prompt_cli
        )
        and "--formalization-gap-planner-component-resource-registry-dir" in prompt_cli
        and (
            not component_resource_registry_dir_text
            or component_resource_registry_dir_text in prompt_cli
        )
        and "--invoke-provider" not in prompt_cli
    )


def _reuse_smoke_cli_cost_control_ok(
    reuse_smoke_cli: str,
    *,
    target_intake_path_text: str,
    target_prover_family: str,
    library_snapshot_ref: str,
) -> bool:
    return (
        "formalization-gap-planner-reuse-smoke" in reuse_smoke_cli
        and target_intake_path_text in reuse_smoke_cli
        and f"--target-prover-family {target_prover_family}" in reuse_smoke_cli
        and f"--target-library-snapshot-ref {library_snapshot_ref}" in reuse_smoke_cli
        and "--llm-route-planner-provider anthropic" in reuse_smoke_cli
        and "--llm-route-planner-model-tier auto" in reuse_smoke_cli
        and "--llm-route-planner-max-repair-attempts 1" in reuse_smoke_cli
        and "--feedback-llm-route-planner-provider anthropic" in reuse_smoke_cli
        and "--feedback-llm-route-planner-model-tier auto" in reuse_smoke_cli
        and "--feedback-llm-route-planner-max-repair-attempts 1" in reuse_smoke_cli
        and "--llm-route-planner-invoke-provider" not in reuse_smoke_cli
        and "--feedback-llm-route-planner-invoke-provider" not in reuse_smoke_cli
    )


def _live_cli_explicit_ok(
    live_cli: str,
    *,
    target_intake_dir_text: str,
    component_resource_registry_dir_text: str,
) -> bool:
    return (
        "formalization-gap-planner-llm-route-planner" in live_cli
        and "--provider anthropic" in live_cli
        and "--model-tier auto" in live_cli
        and "--max-repair-attempts 1" in live_cli
        and "--formalization-gap-planner-target-intake-dir" in live_cli
        and (not target_intake_dir_text or target_intake_dir_text in live_cli)
        and "--formalization-gap-planner-component-resource-registry-dir" in live_cli
        and (
            not component_resource_registry_dir_text
            or component_resource_registry_dir_text in live_cli
        )
        and "--invoke-provider" in live_cli
    )


def _smoke_dir(smoke_root: Path | None, handoff_id: str) -> Path:
    root = smoke_root or Path()
    return root / _safe_identifier(handoff_id)


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


def _read_jsonl(path: Path, errors: list[str]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except FileNotFoundError:
        errors.append(f"missing JSONL file: {path}")
        return []
    except Exception as exc:
        errors.append(f"failed to read {path}: {type(exc).__name__}: {exc}")
        return []
    for idx, line in enumerate(lines, start=1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except Exception as exc:
            errors.append(f"failed to parse {path}:{idx}: {type(exc).__name__}: {exc}")
            continue
        if isinstance(value, dict):
            rows.append(value)
        else:
            errors.append(f"{path}:{idx} is not a JSON object")
    return rows


def _dict_value(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _dict_tuple(value: Any) -> tuple[dict[str, object], ...]:
    if not isinstance(value, (list, tuple, set)):
        return tuple()
    return tuple(dict(item) for item in value if isinstance(item, Mapping))


def _str_tuple(value: Any) -> tuple[str, ...]:
    if value is None:
        return tuple()
    if isinstance(value, str):
        return (value,) if value else tuple()
    if isinstance(value, Mapping):
        return tuple(str(key) for key in value if str(key))
    if isinstance(value, (list, tuple, set)):
        return tuple(str(item) for item in value if str(item))
    return (str(value),) if str(value) else tuple()


def _check(
    check_name: str,
    category: str,
    handoff_id: str,
    bridge_id: str,
    expected: str,
    observed: str,
    ok: bool,
    *,
    severity: str = "error",
) -> FormalizationGapPlannerRuntimeHandoffAuditCheck:
    return FormalizationGapPlannerRuntimeHandoffAuditCheck(
        schema_version=FORMALIZATION_GAP_PLANNER_RUNTIME_HANDOFF_AUDIT_SCHEMA_VERSION,
        check_id="formalization_gap_planner_runtime_handoff_audit:"
        + stable_hash([check_name, category, handoff_id, bridge_id, expected])[:16],
        check_name=check_name,
        category=category,
        handoff_id=handoff_id,
        bridge_id=bridge_id,
        expected=expected,
        observed=observed,
        ok=ok,
        severity=severity,
        errors=() if ok else (f"expected {expected}; observed {observed}",),
    )


def _row_check(
    check_name: str,
    category: str,
    handoff_id: str,
    bridge_id: str,
    expected: str,
    observed: str,
    ok: bool,
    *,
    severity: str = "error",
) -> FormalizationGapPlannerRuntimeHandoffAuditCheck:
    return _check(
        f"{check_name}:{_safe_identifier(handoff_id)[:40]}",
        category,
        handoff_id,
        bridge_id,
        expected,
        observed,
        ok,
        severity=severity,
    )


def _schema_property_errors(
    field_name: str,
    value: object,
    schema: Mapping[str, object],
) -> list[str]:
    errors: list[str] = []
    expected_type = schema.get("type")
    if expected_type == "string":
        if not isinstance(value, str):
            errors.append(f"{field_name} must be string")
            return errors
        if isinstance(schema.get("minLength"), int) and len(value) < int(schema["minLength"]):
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
        if isinstance(item_schema, Mapping) and item_schema.get("type") == "string":
            for index, item in enumerate(value):
                if not isinstance(item, str):
                    errors.append(f"{field_name}[{index}] must be string")
    return errors


def _has_kernel_proof_claim(value: Any) -> bool:
    if isinstance(value, Mapping):
        for key, item in value.items():
            key_text = str(key).lower()
            if key_text in {"kernel_verified", "full_frontier_theorem_proved"} and item is True:
                return True
            if key_text in {"proof_evidence_status", "claim_status"} and (
                "KERNEL_VERIFIED" in str(item) or "PROVED" in str(item)
            ):
                if "NOT_PROOF_EVIDENCE" not in str(item):
                    return True
            if _has_kernel_proof_claim(item):
                return True
    if isinstance(value, (list, tuple)):
        return any(_has_kernel_proof_claim(item) for item in value)
    return False


def _proof_claim_observed(value: Any) -> str:
    return "kernel/proved claim present" if _has_kernel_proof_claim(value) else "none"


def _safe_identifier(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", value).strip("._") or "runtime_handoff"


def _write_outputs(out_dir: Path, payload: Mapping[str, object]) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "formalization_gap_planner_runtime_handoff_audit_manifest.json").write_text(
        json.dumps(payload, indent=2, default=str),
        encoding="utf-8",
    )
    (out_dir / "formalization_gap_planner_runtime_handoff_audit.jsonl").write_text(
        "\n".join(
            json.dumps(row, sort_keys=True)
            for row in payload.get("checks", [])
            if isinstance(row, dict)
        )
        + ("\n" if payload.get("checks") else ""),
        encoding="utf-8",
    )
    execution_plan_rows = [
        row
        for row in payload.get("execution_plan_rows", [])
        if isinstance(row, dict)
    ]
    (
        out_dir / "formalization_gap_planner_runtime_handoff_execution_plans.jsonl"
    ).write_text(
        "\n".join(json.dumps(row, sort_keys=True) for row in execution_plan_rows)
        + ("\n" if execution_plan_rows else ""),
        encoding="utf-8",
    )
    (
        out_dir / "formalization_gap_planner_runtime_handoff_audit_row.schema.json"
    ).write_text(
        json.dumps(runtime_handoff_audit_row_json_schema(), indent=2),
        encoding="utf-8",
    )
    (
        out_dir / "formalization_gap_planner_runtime_handoff_execution_plan.schema.json"
    ).write_text(
        json.dumps(runtime_handoff_execution_plan_json_schema(), indent=2),
        encoding="utf-8",
    )
    (out_dir / "formalization_gap_planner_runtime_handoff_audit.md").write_text(
        _markdown_report(payload),
        encoding="utf-8",
    )


def _markdown_report(payload: Mapping[str, object]) -> str:
    lines = [
        "# Formalization Gap Planner Runtime Handoff Audit",
        "",
        f"- Handoffs: {payload.get('n_handoffs')}",
        f"- Checks: {payload.get('n_ok')}/{payload.get('n_checks')}",
        f"- Cost control OK: {payload.get('n_cost_control_ok')}",
        f"- Reuse-smoke cost control OK: {payload.get('n_reuse_smoke_cost_control_ok')}",
        f"- Execution plans: {payload.get('n_execution_plans')}",
        f"- Execution plan stages: {payload.get('n_execution_plan_stage_rows')}",
        f"- Execution plan schema valid: {payload.get('n_execution_plan_schema_valid')}",
        (
            f"- Execution plan JSONL schema valid: "
            f"{payload.get('n_execution_plan_row_schema_valid')}/"
            f"{payload.get('n_execution_plan_rows')}"
        ),
        (
            f"- Execution plan cost controls: "
            f"prompt={payload.get('n_execution_plan_prompt_stage_cost_control_ok')} "
            f"live={payload.get('n_execution_plan_live_stage_explicit_ok')} "
            f"reuse={payload.get('n_execution_plan_reuse_smoke_stage_cost_control_ok')}"
        ),
        f"- Target-intake smoke OK: {payload.get('n_target_intake_smoke_ok')}",
        f"- Target-intake targets/primitives: {payload.get('n_target_intake_targets')}/{payload.get('n_target_intake_primitive_seeds')}",
        f"- Standalone smoke OK: {payload.get('n_standalone_smoke_ok')}",
        f"- Component-resource registry smoke OK: {payload.get('n_component_resource_registry_smoke_ok')}",
        f"- LLM prompt smoke OK: {payload.get('n_llm_prompt_smoke_ok')}",
        (
            f"- Registry context in prompts: "
            f"components={payload.get('n_component_resource_registry_components_in_prompt')} "
            f"resources={payload.get('n_component_resource_registry_resources_in_prompt')} "
            f"contracts={payload.get('n_component_resource_registry_contracts_in_prompt')}"
        ),
        (
            f"- Target-intake context in prompts: "
            f"requests={payload.get('n_llm_prompt_requests_with_target_intake_rows')} "
            f"rows={payload.get('n_llm_prompt_target_intake_rows')}"
        ),
        f"- Prompt packets: {payload.get('n_llm_prompt_packets')}",
        f"- Awaiting LLM response: {payload.get('n_llm_prompt_awaiting_response')}",
        (
            f"- Minimal-delta cost hints in prompts: "
            f"requests={payload.get('n_llm_prompt_requests_with_minimal_delta_cost_hints')} "
            f"primitive_hints={payload.get('n_llm_prompt_primitive_cost_hints')} "
            f"route_option_hints={payload.get('n_llm_prompt_route_option_cost_hints')}"
        ),
        (
            f"- LLM prompt model-tier mismatches: "
            f"{payload.get('n_llm_prompt_model_tier_mismatches')}"
        ),
        (
            f"- LLM prompt model tiers: "
            f"haiku={payload.get('n_llm_prompt_model_tier_haiku')} "
            f"sonnet={payload.get('n_llm_prompt_model_tier_sonnet')} "
            f"opus={payload.get('n_llm_prompt_model_tier_opus')}"
        ),
        f"- Seed routes/primitives: {payload.get('n_seed_routes')}/{payload.get('n_seed_primitives')}",
        f"- Seed residual goals: {payload.get('n_seed_residual_goals')}",
        (
            f"- Seed candidate declaration rows: "
            f"{payload.get('n_seed_candidate_declaration_rows')} "
            f"across {payload.get('n_seed_primitives_with_candidate_declaration_rows')} primitives"
        ),
        f"- All OK: {payload.get('all_ok')}",
        "",
        "## Boundary",
        "",
        str(payload.get("proof_evidence_boundary", PROOF_EVIDENCE_BOUNDARY)),
        "",
        "## Failed Checks",
        "",
    ]
    failed = [
        check
        for check in payload.get("checks", [])
        if isinstance(check, Mapping) and not check.get("ok")
    ]
    if not failed:
        lines.append("- none")
    for check in failed:
        lines.append(
            f"- `{check.get('check_name')}` category={check.get('category')} "
            f"handoff={check.get('handoff_id')} observed={check.get('observed')}"
        )
    return "\n".join(lines) + "\n"
