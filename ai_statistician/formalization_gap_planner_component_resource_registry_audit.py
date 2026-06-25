from __future__ import annotations

import json
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .fingerprint import stable_hash
from .formalization_gap_planner_component_resource_registry import (
    PORTABLE_REUSE_TARGETS,
    PROOF_EVIDENCE_BOUNDARY as REGISTRY_PROOF_EVIDENCE_BOUNDARY,
    PROOF_EVIDENCE_STATUS as REGISTRY_PROOF_EVIDENCE_STATUS,
    component_resource_contract_row_json_schema,
    component_resource_registry_component_row_json_schema,
    component_resource_registry_resource_row_json_schema,
    component_resource_execution_plan_json_schema,
    validate_component_resource_contract_row,
    validate_component_resource_registry_component_row,
    validate_component_resource_registry_resource_row,
    validate_component_resource_execution_plan_row,
)


FORMALIZATION_GAP_PLANNER_COMPONENT_RESOURCE_REGISTRY_AUDIT_SCHEMA_VERSION = 1
PROOF_EVIDENCE_STATUS = (
    "FORMALIZATION_GAP_PLANNER_COMPONENT_RESOURCE_REGISTRY_AUDIT_NOT_PROOF_EVIDENCE"
)
PROOF_EVIDENCE_BOUNDARY = (
    "Formalization gap planner component-resource registry audit rows validate "
    "planner-component resource coverage, local fallbacks, frontier-tool hooks, "
    "cross-prover reuse surfaces, and proof-boundary discipline. They are not "
    "theorem proof evidence."
)
REQUIRED_COMPONENT_IDS = (
    "target_theorem_intake",
    "literature_grounded_route_synthesis",
    "informal_route_dag_decomposition",
    "formal_library_coverage_mapping",
    "minimal_delta_and_or_planning",
    "prover_feedback_refinement",
    "route_revision_handoff",
    "cross_prover_public_reuse",
)
REQUIRED_RESOURCE_IDS = (
    "paperclip_cli_mcp",
    "paperqa2_local_library",
    "openscholar_semantic_scholar",
    "dependency_graph_autoformalization",
    "local_formal_source_index",
    "loogle_leansearch",
    "leanexplore_mcp",
    "local_lake_lean",
    "source_theorem_semantic_primitive_bridge",
    "source_theorem_formal_environment_bridge",
    "exact_source_theorem_proof_body_executor",
    "lean_lsp_mcp",
    "leandojo_reprover",
    "rocq_lsp_serapi",
    "isabelle_sledgehammer_afp",
    "agda_search_auto",
    "hol4_tactic_kernel_tools",
    "hol_light_tactic_search",
    "mizar_mml_search",
    "metamath_set_mm",
    "publication_bundle_audit",
)


@dataclass(frozen=True)
class FormalizationGapPlannerComponentResourceRegistryAuditCheck:
    schema_version: int
    check_id: str
    check_name: str
    category: str
    expected: str
    observed: str
    ok: bool
    severity: str
    errors: tuple[str, ...] = ()


def audit_formalization_gap_planner_component_resource_registry(
    formalization_gap_planner_component_resource_registry_dir: Path,
    out_dir: Path | None = None,
) -> dict[str, object]:
    """Audit component-resource coverage for public planner reuse."""

    errors: list[str] = []
    registry_dir = formalization_gap_planner_component_resource_registry_dir
    manifest_path = (
        registry_dir
        / "formalization_gap_planner_component_resource_registry_manifest.json"
    )
    jsonl_path = (
        registry_dir / "formalization_gap_planner_component_resource_registry.jsonl"
    )
    resource_jsonl_path = (
        registry_dir / "formalization_gap_planner_component_resource_resources.jsonl"
    )
    execution_plan_jsonl_path = (
        registry_dir
        / "formalization_gap_planner_component_resource_execution_plans.jsonl"
    )
    resource_contract_jsonl_path = (
        registry_dir / "formalization_gap_planner_component_resource_contracts.jsonl"
    )
    resource_row_schema_path = (
        registry_dir
        / "formalization_gap_planner_component_resource_resource_row.schema.json"
    )
    component_row_schema_path = (
        registry_dir
        / "formalization_gap_planner_component_resource_component_row.schema.json"
    )
    execution_plan_schema_path = (
        registry_dir
        / "formalization_gap_planner_component_resource_execution_plan.schema.json"
    )
    resource_contract_row_schema_path = (
        registry_dir
        / "formalization_gap_planner_component_resource_contract_row.schema.json"
    )
    report_path = (
        registry_dir / "formalization_gap_planner_component_resource_registry.md"
    )
    manifest = _read_json(manifest_path, errors)
    resources = _dict_rows(manifest.get("resource_rows", []))
    components = _dict_rows(manifest.get("component_rows", []))
    execution_plans = _dict_rows(manifest.get("execution_plan_rows", []))
    resource_contracts = _dict_rows(manifest.get("resource_contract_rows", []))
    checks: list[FormalizationGapPlannerComponentResourceRegistryAuditCheck] = []
    checks.extend(
        _manifest_checks(manifest_path, manifest, resources, components, execution_plans)
    )
    checks.extend(_coverage_checks(resources, components, execution_plans))
    checks.extend(_component_contract_checks(resources, components))
    checks.extend(_execution_plan_contract_checks(resources, components, execution_plans))
    checks.extend(_resource_contract_checks(resources))
    checks.extend(_resource_request_response_contract_checks(resources, resource_contracts))
    checks.extend(
        _artifact_checks(
            jsonl_path,
            resource_jsonl_path,
            execution_plan_jsonl_path,
            resource_contract_jsonl_path,
            resource_row_schema_path,
            component_row_schema_path,
            execution_plan_schema_path,
            resource_contract_row_schema_path,
            report_path,
        )
    )
    by_category = Counter(check.category for check in checks)
    by_resource_kind = Counter(str(row.get("resource_kind", "")) for row in resources)
    by_capability_tag = Counter(
        tag for row in resources for tag in _str_tuple(row.get("capability_tags", []))
    )
    by_validation_signal = Counter(
        signal
        for row in resources
        for signal in _str_tuple(row.get("validation_signals", []))
    )
    payload: dict[str, object] = {
        "schema_version": FORMALIZATION_GAP_PLANNER_COMPONENT_RESOURCE_REGISTRY_AUDIT_SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "component_name": "formalization_gap_planner_component_resource_registry_audit",
        "formalization_gap_planner_component_resource_registry_dir": str(registry_dir),
        "formalization_gap_planner_component_resource_registry_manifest": str(
            manifest_path
        ),
        "n_checks": len(checks),
        "n_ok": sum(1 for check in checks if check.ok),
        "n_failed": sum(1 for check in checks if not check.ok),
        "n_component_rows": len(components),
        "n_component_row_schema_valid": sum(
            1
            for check in checks
            if check.check_name.startswith("component_")
            and check.check_name.endswith("_schema_valid")
            and check.ok
        ),
        "n_component_row_schema_invalid": sum(
            1
            for check in checks
            if check.check_name.startswith("component_")
            and check.check_name.endswith("_schema_valid")
            and not check.ok
        ),
        "n_execution_plan_rows": len(execution_plans),
        "n_execution_plan_rows_ok": sum(
            1 for row in execution_plans if bool(row.get("ok", False))
        ),
        "n_execution_plan_schema_valid": sum(
            1
            for check in checks
            if check.check_name.startswith("execution_plan_")
            and check.check_name.endswith("_schema_valid")
            and check.ok
        ),
        "n_execution_plan_schema_invalid": sum(
            1
            for check in checks
            if check.check_name.startswith("execution_plan_")
            and check.check_name.endswith("_schema_valid")
            and not check.ok
        ),
        "n_resource_contract_rows": len(resource_contracts),
        "n_resource_contract_rows_ok": sum(
            1 for row in resource_contracts if bool(row.get("ok", False))
        ),
        "n_resource_contract_row_schema_valid": sum(
            1
            for check in checks
            if check.check_name.startswith("resource_contract_")
            and check.check_name.endswith("_schema_valid")
            and check.ok
        ),
        "n_resource_contract_row_schema_invalid": sum(
            1
            for check in checks
            if check.check_name.startswith("resource_contract_")
            and check.check_name.endswith("_schema_valid")
            and not check.ok
        ),
        "n_resources_with_contract": len(
            _resource_ids(resources)
            & {
                str(row.get("resource_id", ""))
                for row in resource_contracts
                if row.get("resource_id")
            }
        ),
        "n_components_with_execution_plan": len(
            _component_ids(components)
            & {
                str(row.get("component_id", ""))
                for row in execution_plans
                if row.get("component_id")
            }
        ),
        "n_required_component_ids": len(REQUIRED_COMPONENT_IDS),
        "n_required_component_ids_present": len(
            set(REQUIRED_COMPONENT_IDS) & _component_ids(components)
        ),
        "n_resource_rows": len(resources),
        "n_resource_row_schema_valid": sum(
            1
            for check in checks
            if check.check_name.startswith("resource_")
            and not check.check_name.startswith("resource_contract_")
            and check.check_name.endswith("_schema_valid")
            and check.ok
        ),
        "n_resource_row_schema_invalid": sum(
            1
            for check in checks
            if check.check_name.startswith("resource_")
            and not check.check_name.startswith("resource_contract_")
            and check.check_name.endswith("_schema_valid")
            and not check.ok
        ),
        "n_required_resource_ids": len(REQUIRED_RESOURCE_IDS),
        "n_required_resource_ids_present": len(
            set(REQUIRED_RESOURCE_IDS) & _resource_ids(resources)
        ),
        "n_local_fallback_resources": by_resource_kind.get("local_fallback", 0),
        "n_frontier_resources": sum(
            1
            for row in resources
            if row.get("resource_kind") in {"frontier_tool", "frontier_method"}
        ),
        "n_mcp_or_cli_resources": sum(
            1
            for row in resources
            if row.get("mcp_compatible")
            or "mcp" in str(row.get("surface", "")).lower()
            or "cli" in str(row.get("surface", "")).lower()
        ),
        "n_online_resources": sum(1 for row in resources if row.get("online_dependency")),
        "n_resources_with_capability_tags": sum(
            1 for row in resources if _str_tuple(row.get("capability_tags", []))
        ),
        "n_resources_with_validation_signals": sum(
            1 for row in resources if _str_tuple(row.get("validation_signals", []))
        ),
        "n_component_rows_with_required_quality_signals": sum(
            1
            for row in components
            if _str_tuple(row.get("required_quality_signals", []))
        ),
        "n_execution_plans_with_quality_gates": sum(
            1
            for row in execution_plans
            if _str_tuple(row.get("quality_gates", []))
        ),
        "n_resource_contracts_with_response_validation_signals": sum(
            1
            for row in resource_contracts
            if _str_tuple(row.get("response_validation_signals", []))
        ),
        "by_check_category": dict(sorted(by_category.items())),
        "by_resource_kind": dict(sorted(by_resource_kind.items())),
        "by_capability_tag": dict(sorted(by_capability_tag.items())),
        "by_validation_signal": dict(sorted(by_validation_signal.items())),
        "all_ok": not errors and bool(checks) and all(check.ok for check in checks),
        "errors": errors,
        "checks": [asdict(check) for check in checks],
        "component_resource_registry_audit_fingerprint": stable_hash(
            [asdict(check) for check in checks]
        ),
        "proof_evidence_status": PROOF_EVIDENCE_STATUS,
        "proof_evidence_boundary": PROOF_EVIDENCE_BOUNDARY,
        "registry_proof_evidence_status": REGISTRY_PROOF_EVIDENCE_STATUS,
        "registry_proof_evidence_boundary": REGISTRY_PROOF_EVIDENCE_BOUNDARY,
        "limitations": (
            "component-resource audit validates coverage and contracts only",
            "remote resources still require live credentials, licensing review, and tool-specific tests",
            "adapter outputs remain route evidence until target-prover kernel replay succeeds",
        ),
    }
    if out_dir is not None:
        out_dir.mkdir(parents=True, exist_ok=True)
        (
            out_dir
            / "formalization_gap_planner_component_resource_registry_audit_manifest.json"
        ).write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
        (
            out_dir / "formalization_gap_planner_component_resource_registry_audit.jsonl"
        ).write_text(
            "\n".join(json.dumps(asdict(check), sort_keys=True) for check in checks)
            + ("\n" if checks else ""),
            encoding="utf-8",
        )
        (
            out_dir / "formalization_gap_planner_component_resource_registry_audit.md"
        ).write_text(_markdown_report(payload), encoding="utf-8")
    return payload


def _manifest_checks(
    manifest_path: Path,
    manifest: dict[str, Any],
    resources: list[dict[str, Any]],
    components: list[dict[str, Any]],
    execution_plans: list[dict[str, Any]],
) -> list[FormalizationGapPlannerComponentResourceRegistryAuditCheck]:
    return [
        _check(
            "component_resource_registry_manifest_exists",
            "manifest",
            "manifest file exists",
            str(manifest_path.exists()),
            manifest_path.exists(),
        ),
        _check(
            "component_resource_registry_component",
            "manifest",
            "formalization_gap_planner_component_resource_registry",
            str(manifest.get("component_name", "")),
            manifest.get("component_name")
            == "formalization_gap_planner_component_resource_registry",
        ),
        _check(
            "component_resource_registry_all_ok",
            "manifest",
            "all_ok true",
            str(manifest.get("all_ok", "")),
            bool(manifest.get("all_ok", False)),
        ),
        _check(
            "component_rows_present",
            "manifest",
            "at least required component count",
            str(len(components)),
            len(components) >= len(REQUIRED_COMPONENT_IDS),
        ),
        _check(
            "execution_plan_rows_present",
            "manifest",
            "one execution plan per component row",
            f"{len(execution_plans)}/{len(components)}",
            bool(components) and len(execution_plans) == len(components),
        ),
        _check(
            "execution_plan_rows_ok",
            "manifest",
            "all execution plan rows ok",
            f"{sum(1 for row in execution_plans if row.get('ok'))}/{len(execution_plans)}",
            bool(execution_plans)
            and all(bool(row.get("ok", False)) for row in execution_plans),
        ),
        _check(
            "resource_rows_present",
            "manifest",
            "at least required resource count",
            str(len(resources)),
            len(resources) >= len(REQUIRED_RESOURCE_IDS),
        ),
        _check(
            "component_resource_registry_boundary",
            "proof_boundary",
            "not theorem proof evidence",
            str(manifest.get("proof_evidence_boundary", ""))[:160],
            "not theorem proof evidence"
            in str(manifest.get("proof_evidence_boundary", "")),
        ),
        _check(
            "component_resource_registry_proof_status",
            "proof_boundary",
            "not proof evidence status",
            str(manifest.get("proof_evidence_status", "")),
            "NOT_PROOF_EVIDENCE" in str(manifest.get("proof_evidence_status", "")),
        ),
    ]


def _coverage_checks(
    resources: list[dict[str, Any]],
    components: list[dict[str, Any]],
    execution_plans: list[dict[str, Any]],
) -> list[FormalizationGapPlannerComponentResourceRegistryAuditCheck]:
    resource_ids = _resource_ids(resources)
    component_ids = _component_ids(components)
    execution_component_ids = {
        str(row.get("component_id", ""))
        for row in execution_plans
        if row.get("component_id")
    }
    reuse_targets = set()
    for row in components:
        reuse_targets.update(_str_tuple(row.get("portable_to_prover_families", [])))
    return [
        _check(
            "required_component_ids",
            "coverage",
            ",".join(REQUIRED_COMPONENT_IDS),
            ",".join(sorted(component_ids)),
            set(REQUIRED_COMPONENT_IDS).issubset(component_ids),
        ),
        _check(
            "required_resource_ids",
            "coverage",
            ",".join(REQUIRED_RESOURCE_IDS),
            ",".join(sorted(resource_ids)),
            set(REQUIRED_RESOURCE_IDS).issubset(resource_ids),
        ),
        _check(
            "portable_reuse_targets",
            "coverage",
            ",".join(PORTABLE_REUSE_TARGETS),
            ",".join(sorted(reuse_targets)),
            set(PORTABLE_REUSE_TARGETS).issubset(reuse_targets),
        ),
        _check(
            "execution_plan_component_coverage",
            "coverage",
            "all required components have execution plans",
            ",".join(sorted(execution_component_ids)),
            set(REQUIRED_COMPONENT_IDS).issubset(execution_component_ids)
            and component_ids.issubset(execution_component_ids),
        ),
        _check(
            "local_fallback_floor",
            "coverage",
            "at least six local fallback resources",
            str(
                sum(1 for row in resources if row.get("resource_kind") == "local_fallback")
            ),
            sum(1 for row in resources if row.get("resource_kind") == "local_fallback")
            >= 6,
        ),
        _check(
            "frontier_resource_floor",
            "coverage",
            "at least ten frontier resources/methods",
            str(
                sum(
                    1
                    for row in resources
                    if row.get("resource_kind") in {"frontier_tool", "frontier_method"}
                )
            ),
            sum(
                1
                for row in resources
                if row.get("resource_kind") in {"frontier_tool", "frontier_method"}
            )
            >= 10,
        ),
        _check(
            "mcp_or_cli_resource_floor",
            "coverage",
            "at least five MCP/CLI resources",
            str(
                sum(
                    1
                    for row in resources
                    if row.get("mcp_compatible")
                    or "mcp" in str(row.get("surface", "")).lower()
                    or "cli" in str(row.get("surface", "")).lower()
                )
            ),
            sum(
                1
                for row in resources
                if row.get("mcp_compatible")
                or "mcp" in str(row.get("surface", "")).lower()
                or "cli" in str(row.get("surface", "")).lower()
            )
            >= 5,
        ),
        _check(
            "resource_capability_metadata_coverage",
            "coverage",
            "all resources have capability tags",
            str(
                sum(
                    1
                    for row in resources
                    if _str_tuple(row.get("capability_tags", []))
                )
            ),
            bool(resources)
            and all(_str_tuple(row.get("capability_tags", [])) for row in resources),
        ),
        _check(
            "resource_validation_signal_coverage",
            "coverage",
            "all resources have validation signals",
            str(
                sum(
                    1
                    for row in resources
                    if _str_tuple(row.get("validation_signals", []))
                )
            ),
            bool(resources)
            and all(_str_tuple(row.get("validation_signals", [])) for row in resources),
        ),
    ]


def _component_contract_checks(
    resources: list[dict[str, Any]],
    components: list[dict[str, Any]],
) -> list[FormalizationGapPlannerComponentResourceRegistryAuditCheck]:
    resource_ids = _resource_ids(resources)
    component_row_schema = component_resource_registry_component_row_json_schema()
    checks: list[FormalizationGapPlannerComponentResourceRegistryAuditCheck] = []
    for idx, row in enumerate(components):
        component_id = str(row.get("component_id", f"row:{idx}"))
        schema_errors = validate_component_resource_registry_component_row(
            row,
            component_row_schema,
        )
        local_fallbacks = set(_str_tuple(row.get("local_fallback_resource_ids", [])))
        frontier_resources = set(_str_tuple(row.get("frontier_resource_ids", [])))
        all_refs = local_fallbacks | frontier_resources
        contract_fields = set(_str_tuple(row.get("integration_contract_fields", [])))
        quality_signals = set(_str_tuple(row.get("required_quality_signals", [])))
        targets = set(_str_tuple(row.get("portable_to_prover_families", [])))
        boundary = str(row.get("proof_evidence_boundary", ""))
        checks.extend(
            [
                _check(
                    f"component_{idx}_schema_valid",
                    "component_contract",
                    "row satisfies component-resource row schema",
                    "; ".join(schema_errors) if schema_errors else "ok",
                    not schema_errors,
                    errors=schema_errors,
                ),
                _check(
                    f"component_{idx}_local_fallback",
                    "component_contract",
                    "local fallback resources present",
                    f"{component_id}: {','.join(sorted(local_fallbacks))}",
                    bool(local_fallbacks),
                ),
                _check(
                    f"component_{idx}_frontier_resources",
                    "component_contract",
                    "frontier resources present",
                    f"{component_id}: {','.join(sorted(frontier_resources))}",
                    bool(frontier_resources),
                ),
                _check(
                    f"component_{idx}_resource_refs_resolve",
                    "component_contract",
                    "all resource refs resolve",
                    f"{component_id}: {','.join(sorted(all_refs - resource_ids))}",
                    all_refs.issubset(resource_ids),
                ),
                _check(
                    f"component_{idx}_contract_fields",
                    "component_contract",
                    "integration contract fields present",
                    f"{component_id}: {','.join(sorted(contract_fields))}",
                    bool(contract_fields),
                ),
                _check(
                    f"component_{idx}_required_quality_signals",
                    "component_contract",
                    "required quality signals present",
                    f"{component_id}: {','.join(sorted(quality_signals))}",
                    {"schema_valid_outputs", "proof_boundary_preserved"}.issubset(
                        quality_signals
                    ),
                ),
                _check(
                    f"component_{idx}_portable_targets",
                    "component_contract",
                    ",".join(PORTABLE_REUSE_TARGETS),
                    f"{component_id}: {','.join(sorted(targets))}",
                    set(PORTABLE_REUSE_TARGETS).issubset(targets),
                ),
                _check(
                    f"component_{idx}_proof_boundary",
                    "proof_boundary",
                    "not theorem proof evidence",
                    boundary[:160],
                    "not theorem proof evidence" in boundary,
                ),
                _check(
                    f"component_{idx}_no_kernel_claim_output",
                    "proof_boundary",
                    "component outputs do not claim kernel proof",
                    f"{component_id}: {','.join(_str_tuple(row.get('expected_outputs', [])))}",
                    "kernel_verified_theorem"
                    not in " ".join(_str_tuple(row.get("expected_outputs", []))),
                ),
            ]
        )
    return checks


def _execution_plan_contract_checks(
    resources: list[dict[str, Any]],
    components: list[dict[str, Any]],
    execution_plans: list[dict[str, Any]],
) -> list[FormalizationGapPlannerComponentResourceRegistryAuditCheck]:
    resource_ids = _resource_ids(resources)
    component_ids = _component_ids(components)
    execution_plan_schema = component_resource_execution_plan_json_schema()
    checks: list[FormalizationGapPlannerComponentResourceRegistryAuditCheck] = []
    for idx, row in enumerate(execution_plans):
        component_id = str(row.get("component_id", f"row:{idx}"))
        schema_errors = validate_component_resource_execution_plan_row(
            row,
            execution_plan_schema,
        )
        local_first = set(_str_tuple(row.get("local_first_resource_ids", [])))
        frontier = set(_str_tuple(row.get("frontier_escalation_resource_ids", [])))
        all_refs = local_first | frontier
        evidence_inputs = set(_str_tuple(row.get("evidence_inputs", [])))
        expected_outputs = set(_str_tuple(row.get("expected_outputs", [])))
        quality_gates = set(_str_tuple(row.get("quality_gates", [])))
        triggers = set(_str_tuple(row.get("escalation_triggers", [])))
        stop_conditions = set(_str_tuple(row.get("stop_conditions", [])))
        boundary = str(row.get("proof_evidence_boundary", ""))
        checks.extend(
            [
                _check(
                    f"execution_plan_{idx}_schema_valid",
                    "execution_plan_contract",
                    "row satisfies component execution-plan schema",
                    "; ".join(schema_errors) if schema_errors else "ok",
                    not schema_errors,
                    errors=schema_errors,
                ),
                _check(
                    f"execution_plan_{idx}_component_ref",
                    "execution_plan_contract",
                    "execution plan component ref resolves",
                    component_id,
                    component_id in component_ids,
                ),
                _check(
                    f"execution_plan_{idx}_local_first",
                    "execution_plan_contract",
                    "local-first resources present",
                    f"{component_id}: {','.join(sorted(local_first))}",
                    bool(local_first),
                ),
                _check(
                    f"execution_plan_{idx}_frontier_escalation",
                    "execution_plan_contract",
                    "frontier escalation resources present",
                    f"{component_id}: {','.join(sorted(frontier))}",
                    bool(frontier),
                ),
                _check(
                    f"execution_plan_{idx}_resource_refs_resolve",
                    "execution_plan_contract",
                    "execution resource refs resolve",
                    f"{component_id}: {','.join(sorted(all_refs - resource_ids))}",
                    all_refs.issubset(resource_ids),
                ),
                _check(
                    f"execution_plan_{idx}_evidence_io",
                    "execution_plan_contract",
                    "evidence inputs and expected outputs present",
                    f"{component_id}: inputs={len(evidence_inputs)} outputs={len(expected_outputs)}",
                    bool(evidence_inputs) and bool(expected_outputs),
                ),
                _check(
                    f"execution_plan_{idx}_quality_gates",
                    "execution_plan_contract",
                    "quality gates include schema and proof-boundary checks",
                    f"{component_id}: {','.join(sorted(quality_gates))}",
                    {
                        "schema_valid_outputs",
                        "proof_boundary_preserved",
                        "no_kernel_claim_without_replay",
                    }.issubset(quality_gates),
                ),
                _check(
                    f"execution_plan_{idx}_triggers_and_stops",
                    "execution_plan_contract",
                    "escalation triggers and stop conditions present",
                    f"{component_id}: triggers={len(triggers)} stops={len(stop_conditions)}",
                    bool(triggers) and bool(stop_conditions),
                ),
                _check(
                    f"execution_plan_{idx}_proof_boundary",
                    "proof_boundary",
                    "not theorem proof evidence",
                    boundary[:160],
                    "not theorem proof evidence" in boundary,
                ),
            ]
        )
    return checks


def _resource_contract_checks(
    resources: list[dict[str, Any]],
) -> list[FormalizationGapPlannerComponentResourceRegistryAuditCheck]:
    checks: list[FormalizationGapPlannerComponentResourceRegistryAuditCheck] = []
    resource_row_schema = component_resource_registry_resource_row_json_schema()
    for idx, row in enumerate(resources):
        resource_id = str(row.get("resource_id", f"row:{idx}"))
        schema_errors = validate_component_resource_registry_resource_row(
            row,
            resource_row_schema,
        )
        resource_kind = str(row.get("resource_kind", ""))
        urls = _str_tuple(row.get("resource_urls", []))
        evidence_contract = _str_tuple(row.get("evidence_contract", []))
        capability_tags = set(_str_tuple(row.get("capability_tags", [])))
        validation_signals = set(_str_tuple(row.get("validation_signals", [])))
        boundary = str(row.get("proof_evidence_boundary", ""))
        needs_url = resource_kind in {"frontier_tool", "frontier_method"} or bool(
            row.get("online_dependency")
        ) or bool(row.get("mcp_compatible"))
        checks.extend(
            [
                _check(
                    f"resource_{idx}_schema_valid",
                    "resource_contract",
                    "row satisfies component-resource registry resource schema",
                    "; ".join(schema_errors) if schema_errors else "ok",
                    not schema_errors,
                    errors=schema_errors,
                ),
                _check(
                    f"resource_{idx}_evidence_contract",
                    "resource_contract",
                    "evidence contract present",
                    f"{resource_id}: {','.join(evidence_contract)}",
                    bool(evidence_contract),
                ),
                _check(
                    f"resource_{idx}_capability_tags",
                    "resource_contract",
                    "capability tags present",
                    f"{resource_id}: {','.join(sorted(capability_tags))}",
                    bool(capability_tags),
                ),
                _check(
                    f"resource_{idx}_validation_signals",
                    "resource_contract",
                    "validation signals include schema and proof-boundary checks",
                    f"{resource_id}: {','.join(sorted(validation_signals))}",
                    {"schema_valid_response", "proof_boundary_preserved"}.issubset(
                        validation_signals
                    ),
                ),
                _check(
                    f"resource_{idx}_url_if_frontier",
                    "resource_contract",
                    "frontier/online/MCP resources have URLs",
                    f"{resource_id}: {','.join(urls)}",
                    bool(urls) if needs_url else True,
                ),
                _check(
                    f"resource_{idx}_proof_boundary",
                    "proof_boundary",
                    "not theorem proof evidence",
                    boundary[:160],
                    "not theorem proof evidence" in boundary,
                ),
            ]
        )
    return checks


def _resource_request_response_contract_checks(
    resources: list[dict[str, Any]],
    resource_contracts: list[dict[str, Any]],
) -> list[FormalizationGapPlannerComponentResourceRegistryAuditCheck]:
    resource_ids = _resource_ids(resources)
    contract_resource_ids = _resource_ids(resource_contracts)
    contract_schema = component_resource_contract_row_json_schema()
    checks = [
        _check(
            "resource_contract_rows_present",
            "resource_contract",
            "one resource contract row per resource row",
            f"{len(resource_contracts)}/{len(resources)}",
            bool(resources) and len(resource_contracts) == len(resources),
        ),
        _check(
            "resource_contract_resource_coverage",
            "resource_contract",
            "all resources have request/response contracts",
            ",".join(sorted(resource_ids - contract_resource_ids)),
            resource_ids.issubset(contract_resource_ids),
        ),
    ]
    for idx, row in enumerate(resource_contracts):
        resource_id = str(row.get("resource_id", f"row:{idx}"))
        schema_errors = validate_component_resource_contract_row(
            row,
            contract_schema,
        )
        request_fields = set(_str_tuple(row.get("request_contract_fields", [])))
        response_fields = set(_str_tuple(row.get("response_contract_fields", [])))
        response_validation_signals = set(
            _str_tuple(row.get("response_validation_signals", []))
        )
        acceptance_gate = str(row.get("acceptance_gate", ""))
        boundary = str(row.get("proof_evidence_boundary", ""))
        requirements = set(
            _str_tuple(row.get("credential_or_installation_requirements", []))
        )
        checks.extend(
            [
                _check(
                    f"resource_contract_{idx}_schema_valid",
                    "resource_contract",
                    "row satisfies component-resource contract schema",
                    "; ".join(schema_errors) if schema_errors else "ok",
                    not schema_errors,
                    errors=schema_errors,
                ),
                _check(
                    f"resource_contract_{idx}_resource_ref",
                    "resource_contract",
                    "contract resource ref resolves",
                    resource_id,
                    resource_id in resource_ids,
                ),
                _check(
                    f"resource_contract_{idx}_request_fields",
                    "resource_contract",
                    "request contract has route and component fields",
                    ",".join(sorted(request_fields)),
                    {"component_id", "route_id", "resource_id"}.issubset(
                        request_fields
                    ),
                ),
                _check(
                    f"resource_contract_{idx}_response_fields",
                    "resource_contract",
                    "response contract fields present",
                    ",".join(sorted(response_fields)),
                    bool(response_fields),
                ),
                _check(
                    f"resource_contract_{idx}_response_validation_signals",
                    "resource_contract",
                    "response validation signals include schema and proof-boundary checks",
                    f"{resource_id}: {','.join(sorted(response_validation_signals))}",
                    {
                        "schema_valid_response",
                        "proof_boundary_preserved",
                    }.issubset(response_validation_signals),
                ),
                _check(
                    f"resource_contract_{idx}_acceptance_gate_boundary",
                    "proof_boundary",
                    "acceptance gate does not promote proof evidence",
                    acceptance_gate[:160],
                    "not theorem proof evidence" in acceptance_gate
                    and "kernel replay" in acceptance_gate,
                ),
                _check(
                    f"resource_contract_{idx}_requirements",
                    "resource_contract",
                    "deployment requirements are explicit",
                    ",".join(sorted(requirements)),
                    bool(requirements),
                ),
                _check(
                    f"resource_contract_{idx}_proof_boundary",
                    "proof_boundary",
                    "not theorem proof evidence",
                    boundary[:160],
                    "not theorem proof evidence" in boundary,
                ),
            ]
        )
    return checks


def _artifact_checks(
    jsonl_path: Path,
    resource_jsonl_path: Path,
    execution_plan_jsonl_path: Path,
    resource_contract_jsonl_path: Path,
    resource_row_schema_path: Path,
    component_row_schema_path: Path,
    execution_plan_schema_path: Path,
    resource_contract_row_schema_path: Path,
    report_path: Path,
) -> list[FormalizationGapPlannerComponentResourceRegistryAuditCheck]:
    return [
        _check(
            "component_resource_registry_jsonl",
            "artifact",
            "component jsonl exists",
            str(jsonl_path.exists()),
            jsonl_path.exists(),
        ),
        _check(
            "component_resource_registry_resource_jsonl",
            "artifact",
            "resource jsonl exists",
            str(resource_jsonl_path.exists()),
            resource_jsonl_path.exists(),
        ),
        _check(
            "component_resource_execution_plan_jsonl",
            "artifact",
            "execution plan jsonl exists",
            str(execution_plan_jsonl_path.exists()),
            execution_plan_jsonl_path.exists(),
        ),
        _check(
            "component_resource_contract_jsonl",
            "artifact",
            "resource contract jsonl exists",
            str(resource_contract_jsonl_path.exists()),
            resource_contract_jsonl_path.exists(),
        ),
        _check(
            "component_resource_registry_resource_row_schema",
            "artifact",
            "resource-row schema exists",
            str(resource_row_schema_path.exists()),
            resource_row_schema_path.exists(),
        ),
        _check(
            "component_resource_registry_component_row_schema",
            "artifact",
            "component-row schema exists",
            str(component_row_schema_path.exists()),
            component_row_schema_path.exists(),
        ),
        _check(
            "component_resource_registry_execution_plan_schema",
            "artifact",
            "execution-plan schema exists",
            str(execution_plan_schema_path.exists()),
            execution_plan_schema_path.exists(),
        ),
        _check(
            "component_resource_registry_resource_contract_schema",
            "artifact",
            "resource-contract schema exists",
            str(resource_contract_row_schema_path.exists()),
            resource_contract_row_schema_path.exists(),
        ),
        _check(
            "component_resource_registry_report",
            "artifact",
            "markdown report exists",
            str(report_path.exists()),
            report_path.exists(),
        ),
    ]


def _check(
    check_name: str,
    category: str,
    expected: str,
    observed: str,
    ok: bool,
    *,
    severity: str = "error",
    errors: tuple[str, ...] = (),
) -> FormalizationGapPlannerComponentResourceRegistryAuditCheck:
    return FormalizationGapPlannerComponentResourceRegistryAuditCheck(
        schema_version=FORMALIZATION_GAP_PLANNER_COMPONENT_RESOURCE_REGISTRY_AUDIT_SCHEMA_VERSION,
        check_id="formalization_gap_planner_component_resource_registry_audit:"
        + stable_hash([check_name, category, expected])[:16],
        check_name=check_name,
        category=category,
        expected=expected,
        observed=observed,
        ok=ok,
        severity=severity,
        errors=errors if not ok else (),
    )


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


def _dict_rows(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [row for row in value if isinstance(row, dict)]


def _resource_ids(rows: list[dict[str, Any]]) -> set[str]:
    return {str(row.get("resource_id", "")) for row in rows if row.get("resource_id")}


def _component_ids(rows: list[dict[str, Any]]) -> set[str]:
    return {str(row.get("component_id", "")) for row in rows if row.get("component_id")}


def _str_tuple(values: Any) -> tuple[str, ...]:
    if isinstance(values, str):
        return (values,) if values else tuple()
    if not isinstance(values, (list, tuple, set)):
        return tuple()
    return tuple(dict.fromkeys(str(item) for item in values if str(item)))


def _markdown_report(payload: dict[str, object]) -> str:
    lines = [
        "# Formalization Gap Planner Component Resource Registry Audit",
        "",
        f"- Checks: {payload.get('n_ok')}/{payload.get('n_checks')}",
        f"- Failed: {payload.get('n_failed')}",
        f"- Components: {payload.get('n_required_component_ids_present')}/{payload.get('n_required_component_ids')}",
        f"- Component-row schema valid: {payload.get('n_component_row_schema_valid')}/{payload.get('n_component_rows')}",
        f"- Resources: {payload.get('n_required_resource_ids_present')}/{payload.get('n_required_resource_ids')}",
        f"- Resource-row schema valid: {payload.get('n_resource_row_schema_valid')}/{payload.get('n_resource_rows')}",
        f"- Resource-contract schema valid: {payload.get('n_resource_contract_row_schema_valid')}/{payload.get('n_resource_contract_rows')}",
        f"- Resources with contracts: {payload.get('n_resources_with_contract')}/{payload.get('n_resource_rows')}",
        f"- Execution-plan schema valid: {payload.get('n_execution_plan_schema_valid')}/{payload.get('n_execution_plan_rows')}",
        f"- Frontier resources: {payload.get('n_frontier_resources')}",
        f"- MCP/CLI resources: {payload.get('n_mcp_or_cli_resources')}",
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
        if isinstance(check, dict) and not check.get("ok")
    ]
    if not failed:
        lines.append("- None")
    for check in failed:
        lines.append(
            f"- `{check.get('check_name')}` expected={check.get('expected')} "
            f"observed={check.get('observed')}"
        )
    return "\n".join(lines) + "\n"
