from __future__ import annotations

import json
import shutil
from pathlib import Path

from ai_statistician.formalization_gap_planner_adapter_registry import (
    export_formalization_gap_planner_adapter_registry,
)
from ai_statistician.formalization_gap_planner_component_resource_registry import (
    PORTABLE_REUSE_TARGETS,
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
    assert "llm_route_planner_static_replay" in resource_ids
    assert "anthropic_claude_api_generator" in resource_ids
    assert "local_target_formal_source_index" in resource_ids
    assert "source_theorem_semantic_primitive_bridge" in resource_ids
    assert (
        "source_theorem_semantic_primitive_from_proof_body_executor_bridge"
        in resource_ids
    )
    assert "source_theorem_formal_environment_bridge" in resource_ids
    assert "exact_source_theorem_proof_body_executor" in resource_ids
    assert "hol4_tactic_kernel_tools" in resource_ids
    assert "hol_light_tactic_search" in resource_ids
    assert "mizar_mml_search" in resource_ids
    assert "metamath_set_mm" in resource_ids
    by_resource = {row["resource_id"]: row for row in payload["resource_rows"]}
    assert payload["portable_reuse_targets"] == PORTABLE_REUSE_TARGETS
    assert by_resource["local_target_formal_source_index"][
        "target_prover_families"
    ] == PORTABLE_REUSE_TARGETS
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
    assert "llm_route_planning" in by_resource[
        "anthropic_claude_api_generator"
    ]["capability_tags"]
    assert "generator_only_llm" in by_resource[
        "anthropic_claude_api_generator"
    ]["capability_tags"]
    assert "model_tier_routing" in by_resource[
        "anthropic_claude_api_generator"
    ]["capability_tags"]
    assert "json_only_response_validated" in by_resource[
        "anthropic_claude_api_generator"
    ]["validation_signals"]
    assert "model_tier_decision_recorded" in by_resource[
        "anthropic_claude_api_generator"
    ]["validation_signals"]
    assert "provider_usage_recorded" in by_resource[
        "anthropic_claude_api_generator"
    ]["validation_signals"]
    assert "model_tier_routing" in by_resource[
        "llm_route_planner_static_replay"
    ]["capability_tags"]
    semantic_bridge = by_resource["source_theorem_semantic_primitive_bridge"]
    assert semantic_bridge["target_prover_families"] == ("lean4",)
    assert "source_theorem_semantic_bridge" in semantic_bridge["capability_tags"]
    assert "semantic_primitive_support_classified" in semantic_bridge[
        "validation_signals"
    ]
    assert "runtime_learning_rows_boundary_preserved" in semantic_bridge[
        "validation_signals"
    ]
    post_proof_body_semantic_bridge = by_resource[
        "source_theorem_semantic_primitive_from_proof_body_executor_bridge"
    ]
    assert post_proof_body_semantic_bridge["target_prover_families"] == ("lean4",)
    assert "source_theorem_semantic_bridge_from_proof_body_feedback" in (
        post_proof_body_semantic_bridge["capability_tags"]
    )
    assert "proof_body_feedback_semantic_primitive_repair_classified" in (
        post_proof_body_semantic_bridge["validation_signals"]
    )
    assert "runtime_learning_rows_boundary_preserved" in (
        post_proof_body_semantic_bridge["validation_signals"]
    )
    formal_environment_bridge = by_resource["source_theorem_formal_environment_bridge"]
    assert formal_environment_bridge["target_prover_families"] == ("lean4",)
    assert "source_theorem_formal_environment_bridge" in formal_environment_bridge[
        "capability_tags"
    ]
    assert "formal_environment_repair_classified" in formal_environment_bridge[
        "validation_signals"
    ]
    assert "runtime_learning_rows_boundary_preserved" in formal_environment_bridge[
        "validation_signals"
    ]
    proof_body_executor = by_resource["exact_source_theorem_proof_body_executor"]
    assert proof_body_executor["target_prover_families"] == ("lean4",)
    assert "exact_source_theorem_proof_body_execution" in proof_body_executor[
        "capability_tags"
    ]
    assert "proof_body_execution_status_classified" in proof_body_executor[
        "validation_signals"
    ]
    assert "source_theorem_kernel_status_preserved" in proof_body_executor[
        "validation_signals"
    ]
    assert by_resource["hol4_tactic_kernel_tools"]["target_prover_families"] == (
        "hol4",
    )
    assert "formal_library_search" in by_resource["hol4_tactic_kernel_tools"][
        "capability_tags"
    ]
    assert "proof_state_feedback" in by_resource["hol4_tactic_kernel_tools"][
        "capability_tags"
    ]
    assert "formal_hits_or_premises_present" in by_resource[
        "hol_light_tactic_search"
    ]["validation_signals"]
    assert by_resource["mizar_mml_search"]["target_prover_families"] == ("mizar",)
    assert by_resource["metamath_set_mm"]["target_prover_families"] == (
        "metamath",
    )
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
    assert "llm_route_planner_static_replay" in by_component[
        "llm_route_planner_generator"
    ]["local_fallback_resource_ids"]
    assert "anthropic_claude_api_generator" in by_component[
        "llm_route_planner_generator"
    ]["frontier_resource_ids"]
    assert "json_only_route_plan_response_validated" in by_component[
        "llm_route_planner_generator"
    ]["required_quality_signals"]
    assert "model_tier_and_provider_usage_recorded" in by_component[
        "llm_route_planner_generator"
    ]["required_quality_signals"]
    assert "leanexplore_mcp" in by_component["formal_library_coverage_mapping"][
        "frontier_resource_ids"
    ]
    assert "hol4_tactic_kernel_tools" in by_component[
        "formal_library_coverage_mapping"
    ]["frontier_resource_ids"]
    assert "mizar_mml_search" in by_component["formal_library_coverage_mapping"][
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
    assert "source_theorem_semantic_primitive_bridge" in by_component[
        "prover_feedback_refinement"
    ]["local_fallback_resource_ids"]
    assert "source_theorem_semantic_primitive_from_proof_body_executor_bridge" in (
        by_component["prover_feedback_refinement"]["local_fallback_resource_ids"]
    )
    assert "source_theorem_formal_environment_bridge" in by_component[
        "prover_feedback_refinement"
    ]["local_fallback_resource_ids"]
    assert "exact_source_theorem_proof_body_executor" in by_component[
        "prover_feedback_refinement"
    ]["local_fallback_resource_ids"]
    assert "metamath_set_mm" in by_component["prover_feedback_refinement"][
        "frontier_resource_ids"
    ]
    assert "proof_state_residuals_classified" in by_component[
        "prover_feedback_refinement"
    ]["required_quality_signals"]
    assert "source_theorem_semantic_support_classified" in by_component[
        "prover_feedback_refinement"
    ]["required_quality_signals"]
    assert "source_theorem_formal_environment_repair_classified" in by_component[
        "prover_feedback_refinement"
    ]["required_quality_signals"]
    assert "exact_source_theorem_proof_body_execution_classified" in by_component[
        "prover_feedback_refinement"
    ]["required_quality_signals"]
    assert "proof_body_feedback_semantic_repair_classified" in by_component[
        "prover_feedback_refinement"
    ]["required_quality_signals"]
    assert "source_theorem_semantic_primitive_bridge" in by_component[
        "route_revision_handoff"
    ]["local_fallback_resource_ids"]
    assert "source_theorem_semantic_primitive_from_proof_body_executor_bridge" in (
        by_component["route_revision_handoff"]["local_fallback_resource_ids"]
    )
    assert "source_theorem_formal_environment_bridge" in by_component[
        "route_revision_handoff"
    ]["local_fallback_resource_ids"]
    assert "exact_source_theorem_proof_body_executor" in by_component[
        "route_revision_handoff"
    ]["local_fallback_resource_ids"]
    assert "source_theorem_semantic_support_classified" in by_component[
        "route_revision_handoff"
    ]["required_quality_signals"]
    assert "exact_source_theorem_proof_body_execution_classified" in by_component[
        "route_revision_handoff"
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
    assert "prompt_packet" in contracts_by_resource[
        "anthropic_claude_api_generator"
    ]["request_contract_fields"]
    assert "response_schema" in contracts_by_resource[
        "anthropic_claude_api_generator"
    ]["request_contract_fields"]
    assert "model_tier" in contracts_by_resource[
        "anthropic_claude_api_generator"
    ]["request_contract_fields"]
    assert "json_only_route_plan_response" in contracts_by_resource[
        "anthropic_claude_api_generator"
    ]["response_contract_fields"]
    assert "model_tier_decision_recorded" in contracts_by_resource[
        "anthropic_claude_api_generator"
    ]["response_validation_signals"]
    assert contracts_by_resource[
        "anthropic_claude_api_generator"
    ]["output_artifact_kind"] == "llm_route_planner_response_or_static_replay"
    assert "not theorem proof evidence" in contracts_by_resource["lean_lsp_mcp"][
        "acceptance_gate"
    ]
    assert "source_theorem_semantic_primitive_work_orders" in contracts_by_resource[
        "source_theorem_semantic_primitive_bridge"
    ]["request_contract_fields"]
    assert "runtime_learning_rows" in contracts_by_resource[
        "source_theorem_semantic_primitive_bridge"
    ]["response_contract_fields"]
    assert "semantic_primitive_support_classified" in contracts_by_resource[
        "source_theorem_semantic_primitive_bridge"
    ]["response_validation_signals"]
    assert contracts_by_resource[
        "source_theorem_semantic_primitive_bridge"
    ]["output_artifact_kind"] == "source_theorem_semantic_primitive_bridge_response"
    assert "exact_source_theorem_proof_body_execution_feedback_rows" in (
        contracts_by_resource[
            "source_theorem_semantic_primitive_from_proof_body_executor_bridge"
        ]["request_contract_fields"]
    )
    assert "source_theorem_semantic_primitive_work_orders_from_proof_body_executor" in (
        contracts_by_resource[
            "source_theorem_semantic_primitive_from_proof_body_executor_bridge"
        ]["request_contract_fields"]
    )
    assert "proof_body_feedback_semantic_primitive_repair_classified" in (
        contracts_by_resource[
            "source_theorem_semantic_primitive_from_proof_body_executor_bridge"
        ]["response_validation_signals"]
    )
    assert contracts_by_resource[
        "source_theorem_semantic_primitive_from_proof_body_executor_bridge"
    ]["output_artifact_kind"] == (
        "source_theorem_semantic_primitive_from_proof_body_executor_bridge_response"
    )
    assert "source_theorem_formal_environment_work_orders" in contracts_by_resource[
        "source_theorem_formal_environment_bridge"
    ]["request_contract_fields"]
    assert "repair_packets" in contracts_by_resource[
        "source_theorem_formal_environment_bridge"
    ]["response_contract_fields"]
    assert "formal_environment_repair_classified" in contracts_by_resource[
        "source_theorem_formal_environment_bridge"
    ]["response_validation_signals"]
    assert contracts_by_resource[
        "source_theorem_formal_environment_bridge"
    ]["output_artifact_kind"] == "source_theorem_formal_environment_bridge_response"
    assert "exact_source_theorem_proof_body_execution_queue_rows" in contracts_by_resource[
        "exact_source_theorem_proof_body_executor"
    ]["request_contract_fields"]
    assert "exact_source_theorem_proof_body_execution_result_rows" in contracts_by_resource[
        "exact_source_theorem_proof_body_executor"
    ]["response_contract_fields"]
    assert "proof_body_execution_status_classified" in contracts_by_resource[
        "exact_source_theorem_proof_body_executor"
    ]["response_validation_signals"]
    assert contracts_by_resource[
        "exact_source_theorem_proof_body_executor"
    ]["output_artifact_kind"] == "exact_source_theorem_proof_body_execution_response"
    assert "target_prover_family" in contracts_by_resource[
        "hol4_tactic_kernel_tools"
    ]["request_contract_fields"]
    assert "formal_declaration_hits" in contracts_by_resource[
        "mizar_mml_search"
    ]["response_contract_fields"]

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
