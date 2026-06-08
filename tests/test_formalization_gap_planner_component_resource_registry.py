from __future__ import annotations

import json
import shutil
from pathlib import Path

from ai_statistician.formalization_gap_planner_adapter_registry import (
    export_formalization_gap_planner_adapter_registry,
)
from ai_statistician.formalization_gap_planner_component_resource_registry import (
    component_resource_contract_row_json_schema,
    component_resource_registry_component_row_json_schema,
    component_resource_registry_resource_row_json_schema,
    export_formalization_gap_planner_component_resource_registry,
    validate_component_resource_contract_row,
    validate_component_resource_registry_component_row,
    validate_component_resource_registry_resource_row,
)
from ai_statistician.formalization_gap_planner_component_resource_registry_audit import (
    audit_formalization_gap_planner_component_resource_registry,
)


def test_component_resource_registry_covers_planner_components_and_frontier_tools() -> None:
    root = Path("runs/test_formalization_gap_planner_component_resource_registry")
    registry_dir = root / "adapter_registry"
    component_dir = root / "component_registry"
    audit_dir = root / "component_audit"
    reject_dir = root / "component_reject"
    shutil.rmtree(root, ignore_errors=True)

    export_formalization_gap_planner_adapter_registry(registry_dir)
    payload = export_formalization_gap_planner_component_resource_registry(
        component_dir,
        formalization_gap_planner_adapter_registry_dir=registry_dir,
    )
    audit_payload = audit_formalization_gap_planner_component_resource_registry(
        component_dir,
        audit_dir,
    )

    assert payload["all_ok"]
    assert payload["n_component_rows"] >= 8
    assert payload["n_execution_plan_rows"] == payload["n_component_rows"]
    assert payload["n_execution_plan_rows_ok"] == payload["n_execution_plan_rows"]
    assert payload["n_component_row_schema_valid"] == payload["n_component_rows"]
    assert payload["n_component_row_schema_invalid"] == 0
    assert payload["n_execution_plan_row_schema_valid"] == payload["n_execution_plan_rows"]
    assert payload["n_execution_plan_row_schema_invalid"] == 0
    assert payload["n_resource_contract_rows"] == payload["n_resources"]
    assert payload["n_resource_contract_rows_ok"] == payload["n_resource_contract_rows"]
    assert (
        payload["n_resource_contract_row_schema_valid"]
        == payload["n_resource_contract_rows"]
    )
    assert payload["n_resource_contract_row_schema_invalid"] == 0
    assert payload["n_resources"] >= 20
    assert payload["n_frontier_resources"] >= 10
    assert payload["n_mcp_or_cli_resources"] >= 5
    assert payload["n_resources_with_capability_tags"] == payload["n_resources"]
    assert payload["n_resources_with_validation_signals"] == payload["n_resources"]
    assert (
        payload["n_component_rows_with_required_quality_signals"]
        == payload["n_component_rows"]
    )
    assert (
        payload["n_execution_plans_with_quality_gates"]
        == payload["n_execution_plan_rows"]
    )
    assert (
        payload["n_resource_contracts_with_response_validation_signals"]
        == payload["n_resource_contract_rows"]
    )
    assert payload["n_resource_row_schema_valid"] == payload["n_resources"]
    assert payload["n_resource_row_schema_invalid"] == 0
    resource_schema = component_resource_registry_resource_row_json_schema()
    component_schema = component_resource_registry_component_row_json_schema()
    resource_contract_schema = component_resource_contract_row_json_schema()
    assert payload["resource_row_schema"]["$id"] == resource_schema["$id"]
    assert payload["component_row_schema"]["$id"] == component_schema["$id"]
    assert (
        payload["resource_contract_row_schema"]["$id"]
        == resource_contract_schema["$id"]
    )
    invalid_resource_row = dict(payload["resource_rows"][0])
    invalid_resource_row.pop("capability_tags")
    assert validate_component_resource_registry_resource_row(
        invalid_resource_row,
        resource_schema,
    )
    invalid_component_row = dict(payload["component_rows"][0])
    invalid_component_row.pop("local_fallback_resource_ids")
    assert validate_component_resource_registry_component_row(
        invalid_component_row,
        component_schema,
    )
    invalid_contract_row = dict(payload["resource_contract_rows"][0])
    invalid_contract_row.pop("response_contract_fields")
    assert validate_component_resource_contract_row(
        invalid_contract_row,
        resource_contract_schema,
    )
    component_ids = {row["component_id"] for row in payload["component_rows"]}
    resource_ids = {row["resource_id"] for row in payload["resource_rows"]}
    assert "literature_grounded_route_synthesis" in component_ids
    assert "formal_library_coverage_mapping" in component_ids
    assert "prover_feedback_refinement" in component_ids
    assert "target_intake_schema" in resource_ids
    assert "target_intake_row_schema" in resource_ids
    assert "portable_gap_plan_row_schema" in resource_ids
    assert "local_target_formal_source_index" in resource_ids
    by_resource = {row["resource_id"]: row for row in payload["resource_rows"]}
    assert by_resource["local_target_formal_source_index"]["target_prover_families"] == (
        "lean4",
        "rocq",
        "isabelle",
        "agda",
    )
    assert "lean_declaration_hits" not in by_resource[
        "local_target_formal_source_index"
    ]["evidence_contract"]
    assert by_resource["lean_blueprint_leanarchitect"]["target_prover_families"] == (
        "lean4",
    )
    assert "literature_source_grounding" in by_resource["paperclip_cli_mcp"][
        "capability_tags"
    ]
    assert "mcp_surface" in by_resource["paperclip_cli_mcp"]["capability_tags"]
    assert "source_refs_present" in by_resource["paperclip_cli_mcp"][
        "validation_signals"
    ]
    assert "proof_state_feedback" in by_resource["lean_lsp_mcp"]["capability_tags"]
    assert "proof_state_diagnostics_or_residuals_present" in by_resource[
        "lean_lsp_mcp"
    ]["validation_signals"]
    by_component = {row["component_id"]: row for row in payload["component_rows"]}
    assert "target_intake_row_schema" in by_component["target_theorem_intake"][
        "local_fallback_resource_ids"
    ]
    assert "portable_gap_plan_row_schema" in by_component["cross_prover_public_reuse"][
        "local_fallback_resource_ids"
    ]
    assert "paperclip_cli_mcp" in by_component["literature_grounded_route_synthesis"][
        "frontier_resource_ids"
    ]
    assert "source_refs_or_literature_gap_recorded" in by_component[
        "literature_grounded_route_synthesis"
    ]["required_quality_signals"]
    assert "leanexplore_mcp" in by_component["formal_library_coverage_mapping"][
        "frontier_resource_ids"
    ]
    assert "local_target_formal_source_index" in by_component[
        "formal_library_coverage_mapping"
    ]["local_fallback_resource_ids"]
    assert "formal_coverage_classification_recorded" in by_component[
        "formal_library_coverage_mapping"
    ]["required_quality_signals"]
    assert "lean_lsp_mcp" in by_component["prover_feedback_refinement"][
        "frontier_resource_ids"
    ]
    assert "proof_state_residuals_classified" in by_component[
        "prover_feedback_refinement"
    ]["required_quality_signals"]
    assert (
        by_component["formal_library_coverage_mapping"]["detected_adapter_statuses"][
            "local_formal_source_index"
        ]
        == "READY_LOCAL"
    )
    assert "not theorem proof evidence" in payload["proof_evidence_boundary"]
    by_plan = {row["component_id"]: row for row in payload["execution_plan_rows"]}
    assert set(by_plan) == component_ids
    assert by_plan["literature_grounded_route_synthesis"]["local_first_resource_ids"]
    assert "paperclip_cli_mcp" in by_plan["literature_grounded_route_synthesis"][
        "frontier_escalation_resource_ids"
    ]
    assert "no_kernel_claim_without_replay" in by_plan[
        "literature_grounded_route_synthesis"
    ]["quality_gates"]
    assert by_plan["prover_feedback_refinement"]["escalation_triggers"]
    assert by_plan["cross_prover_public_reuse"]["stop_conditions"]
    contracts_by_resource = {
        row["resource_id"]: row for row in payload["resource_contract_rows"]
    }
    assert set(contracts_by_resource) == {row["resource_id"] for row in payload["resource_rows"]}
    assert "source_refs" in contracts_by_resource["paperclip_cli_mcp"][
        "response_contract_fields"
    ]
    assert "schema_valid_response" in contracts_by_resource["paperclip_cli_mcp"][
        "response_validation_signals"
    ]
    assert "mcp_tool_call" in contracts_by_resource["paperclip_cli_mcp"][
        "request_contract_fields"
    ]
    assert "not theorem proof evidence" in contracts_by_resource["lean_lsp_mcp"][
        "acceptance_gate"
    ]

    assert audit_payload["all_ok"]
    assert audit_payload["n_failed"] == 0
    assert audit_payload["n_execution_plan_rows"] == audit_payload["n_component_rows"]
    assert (
        audit_payload["n_execution_plan_schema_valid"]
        == audit_payload["n_execution_plan_rows"]
    )
    assert audit_payload["n_execution_plan_schema_invalid"] == 0
    assert audit_payload["n_resource_contract_rows"] == audit_payload["n_resource_rows"]
    assert audit_payload["n_resource_contract_rows_ok"] == audit_payload["n_resource_contract_rows"]
    assert (
        audit_payload["n_resource_contract_row_schema_valid"]
        == audit_payload["n_resource_contract_rows"]
    )
    assert audit_payload["n_resource_contract_row_schema_invalid"] == 0
    assert (
        audit_payload["n_resources_with_contract"]
        == audit_payload["n_resource_rows"]
    )
    assert audit_payload["n_component_row_schema_valid"] == audit_payload["n_component_rows"]
    assert audit_payload["n_component_row_schema_invalid"] == 0
    assert audit_payload["n_resource_row_schema_valid"] == audit_payload["n_resource_rows"]
    assert audit_payload["n_resource_row_schema_invalid"] == 0
    assert (
        audit_payload["n_components_with_execution_plan"]
        == audit_payload["n_component_rows"]
    )
    assert (
        audit_payload["n_required_component_ids_present"]
        == audit_payload["n_required_component_ids"]
    )
    assert (
        audit_payload["n_required_resource_ids_present"]
        == audit_payload["n_required_resource_ids"]
    )
    assert audit_payload["n_resources_with_capability_tags"] == audit_payload[
        "n_resource_rows"
    ]
    assert audit_payload["n_resources_with_validation_signals"] == audit_payload[
        "n_resource_rows"
    ]
    assert audit_payload["n_component_rows_with_required_quality_signals"] == audit_payload[
        "n_component_rows"
    ]
    assert audit_payload["n_execution_plans_with_quality_gates"] == audit_payload[
        "n_execution_plan_rows"
    ]
    assert audit_payload["n_resource_contracts_with_response_validation_signals"] == audit_payload[
        "n_resource_contract_rows"
    ]
    assert any(
        check["check_name"] == "frontier_resource_floor" and check["ok"]
        for check in audit_payload["checks"]
    )
    assert any(
        check["check_name"] == "resource_validation_signal_coverage" and check["ok"]
        for check in audit_payload["checks"]
    )
    assert any(
        check["check_name"] == "execution_plan_component_coverage" and check["ok"]
        for check in audit_payload["checks"]
    )
    assert any(
        check["check_name"] == "execution_plan_0_schema_valid" and check["ok"]
        for check in audit_payload["checks"]
    )
    assert any(
        check["check_name"] == "resource_contract_0_schema_valid" and check["ok"]
        for check in audit_payload["checks"]
    )
    assert any(
        check["check_name"] == "resource_contract_resource_coverage" and check["ok"]
        for check in audit_payload["checks"]
    )
    assert (
        audit_dir
        / "formalization_gap_planner_component_resource_registry_audit_manifest.json"
    ).exists()
    assert (
        component_dir
        / "formalization_gap_planner_component_resource_execution_plans.jsonl"
    ).exists()
    assert (
        component_dir
        / "formalization_gap_planner_component_resource_contracts.jsonl"
    ).exists()
    assert (
        component_dir / "formalization_gap_planner_component_resource_resources.jsonl"
    ).exists()
    assert (
        component_dir
        / "formalization_gap_planner_component_resource_resource_row.schema.json"
    ).exists()
    assert (
        component_dir
        / "formalization_gap_planner_component_resource_component_row.schema.json"
    ).exists()
    assert (
        component_dir
        / "formalization_gap_planner_component_resource_execution_plan.schema.json"
    ).exists()
    assert (
        component_dir
        / "formalization_gap_planner_component_resource_contract_row.schema.json"
    ).exists()

    manifest_path = (
        component_dir
        / "formalization_gap_planner_component_resource_registry_manifest.json"
    )
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["component_rows"] = [
        row
        for row in manifest["component_rows"]
        if row.get("component_id") != "literature_grounded_route_synthesis"
    ]
    manifest["execution_plan_rows"][0].pop("stop_conditions", None)
    manifest["execution_plan_rows"][0].pop("quality_gates", None)
    manifest["resource_contract_rows"][0].pop("response_contract_fields", None)
    manifest["resource_rows"][0].pop("validation_signals", None)
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    rejected = audit_formalization_gap_planner_component_resource_registry(
        component_dir,
        reject_dir,
    )

    assert not rejected["all_ok"]
    failed = {check["check_name"] for check in rejected["checks"] if not check["ok"]}
    assert "required_component_ids" in failed
    assert "execution_plan_0_schema_valid" in failed
    assert "execution_plan_0_quality_gates" in failed
    assert "resource_contract_0_schema_valid" in failed
    assert "resource_0_schema_valid" in failed
