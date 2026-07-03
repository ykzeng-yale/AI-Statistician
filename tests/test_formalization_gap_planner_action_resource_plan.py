from __future__ import annotations

import json
import shutil
from pathlib import Path

from ai_statistician.formalization_gap_planner_action_resource_plan import (
    ACTION_RESOURCE_PLAN_ROW_SCHEMA_ID,
    action_resource_plan_row_json_schema,
    export_formalization_gap_planner_action_resource_plan,
    validate_action_resource_plan_row,
)
from ai_statistician.formalization_gap_planner_component_resource_registry import (
    export_formalization_gap_planner_component_resource_registry,
)
from ai_statistician.formalization_gap_planner_library_coverage_map import (
    export_formalization_gap_planner_library_coverage_map,
)
from ai_statistician.formalization_gap_planner_primitive_action_queue import (
    export_formalization_gap_planner_primitive_action_queue,
)
from ai_statistician.formalization_gap_planner_standalone import (
    export_formalization_gap_planner_standalone_plan,
)


def test_action_resource_plan_joins_actions_to_frontier_resources() -> None:
    root = Path("runs/test_formalization_gap_planner_action_resource_plan")
    input_json = root / "standalone_input.json"
    plan_dir = root / "plan"
    coverage_dir = root / "coverage"
    action_queue_dir = root / "action_queue"
    component_resource_registry_dir = root / "component_resource_registry"
    action_resource_plan_dir = root / "action_resource_plan"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "component_name": "formalization_gap_planner_standalone_input",
                "target_prover_family": "lean4",
                "library_snapshot_ref": "lean_mathlib_empirical_process_snapshot",
                "routes": [
                    {
                        "display_name": "distribution_free_rank_bound",
                        "theorem_statement": (
                            "A distribution-free rank bound follows from exchangeability."
                        ),
                        "source_refs": ["conformal_prediction_textbook"],
                        "replan_metadata": {
                            "llm_route_planner_row_id": "llm_route:rank_bound",
                            "llm_route_planner_minimal_delta_plan": {
                                "bridge_lemmas": [
                                    (
                                        "rank_uniformity: prove finite rank "
                                        "uniformity from exchangeability"
                                    )
                                ],
                                "source_port_lemmas": [
                                    (
                                        "coverage_inequality: port the "
                                        "source-backed coverage inequality"
                                    )
                                ],
                            },
                        },
                        "primitives": [
                            {
                                "primitive": "exchangeability",
                                "coverage_status": "exact_exists",
                                "candidate_declarations": ["Probability.exchangeable"],
                            },
                            {
                                "primitive": "rank_uniformity",
                                "coverage_status": "bridge_needed",
                                "expected_premises": ["exchangeability"],
                            },
                            {
                                "primitive": "coverage_inequality",
                                "coverage_status": "source_port_needed",
                                "source_refs": ["vovk_gammerman_shafer"],
                            },
                        ],
                    }
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    export_formalization_gap_planner_standalone_plan(input_json, plan_dir)
    coverage_payload = export_formalization_gap_planner_library_coverage_map(
        plan_dir,
        coverage_dir,
    )
    action_queue_payload = export_formalization_gap_planner_primitive_action_queue(
        coverage_dir,
        action_queue_dir,
    )
    export_formalization_gap_planner_component_resource_registry(
        component_resource_registry_dir
    )

    payload = export_formalization_gap_planner_action_resource_plan(
        action_queue_dir,
        component_resource_registry_dir,
        action_resource_plan_dir,
    )

    assert payload["all_ok"]
    assert payload["n_action_rows"] == action_queue_payload["n_action_items"]
    assert payload["n_resource_plan_rows"] == coverage_payload["n_coverage_rows"] == 3
    assert payload["n_ok"] == payload["n_resource_plan_rows"]
    assert payload["n_failed"] == 0
    assert payload["n_row_schema_valid"] == payload["n_resource_plan_rows"]
    assert payload["n_row_schema_invalid"] == 0
    assert payload["n_with_candidate_declaration_rows"] == 1
    assert payload["n_candidate_declaration_rows"] == 1
    assert payload["n_with_actionable_work_items"] == 2
    assert payload["n_actionable_work_items"] == 2
    assert payload["n_minimal_delta_reuse_ready"] == 1
    assert payload["n_minimal_delta_light_bridge_or_wrapper"] == 1
    assert payload["n_minimal_delta_source_or_new_theory"] == 1
    assert payload["n_minimal_delta_alignment_blocked"] == 0
    assert payload["average_reuse_readiness_score"] == 68
    assert payload["average_evidence_readiness_score"] == 72
    assert (
        payload["action_resource_plan_row_schema"]["$id"]
        == ACTION_RESOURCE_PLAN_ROW_SCHEMA_ID
    )
    assert "actionable_work_items" in payload[
        "action_resource_plan_row_schema"
    ]["required"]
    assert "minimal_delta_cost_score" in payload[
        "action_resource_plan_row_schema"
    ]["required"]
    assert "reuse_readiness_score" in payload[
        "action_resource_plan_row_schema"
    ]["required"]
    assert "evidence_readiness_score" in payload[
        "action_resource_plan_row_schema"
    ]["required"]
    assert "priority_rationale" in payload[
        "action_resource_plan_row_schema"
    ]["required"]
    assert (
        payload["n_with_frontier_escalation_resources"]
        == payload["n_resource_plan_rows"]
    )
    assert payload["n_with_resource_contracts"] == payload["n_resource_plan_rows"]
    by_primitive = {row["primitive"]: row for row in payload["rows"]}
    exact_row = by_primitive["exchangeability"]
    assert exact_row["minimal_delta_cost_score"] == 0
    assert exact_row["reuse_readiness_score"] == 100
    assert exact_row["evidence_readiness_score"] == 75
    assert (
        "prefer exact current-library reuse before adding declarations"
        in exact_row["priority_rationale"]
    )
    assert exact_row["candidate_declaration_rows"] == (
        {
            "declaration": "Probability.exchangeable",
            "target_prover_family": "lean4",
            "source_field": "candidate_declarations",
        },
    )
    bridge_row = by_primitive["rank_uniformity"]
    assert bridge_row["queue_action_kind"] == "prove_bridge_lemma"
    assert bridge_row["minimal_delta_cost_score"] == 40
    assert bridge_row["reuse_readiness_score"] == 70
    assert bridge_row["evidence_readiness_score"] == 75
    assert "formal_library_coverage_mapping" in bridge_row["component_ids"]
    assert "minimal_delta_and_or_planning" in bridge_row["component_ids"]
    assert "prover_feedback_refinement" in bridge_row["component_ids"]
    assert "lean_lsp_mcp" in bridge_row["frontier_escalation_resource_ids"]
    assert "formal_declaration_hits" in bridge_row["response_contract_fields"]
    assert "lean_declaration_hits" in bridge_row["response_contract_fields"]
    assert "prover_diagnostics" in bridge_row["response_contract_fields"]
    assert bridge_row["actionable_work_items"] == (
        "rank_uniformity: prove finite rank uniformity from exchangeability",
    )
    for resource_id in (
        "local_formal_source_index",
        "loogle_leansearch",
        "leanexplore_mcp",
    ):
        resource_fields = bridge_row["response_contract_fields_by_resource"][
            resource_id
        ]
        assert "formal_declaration_hits" in resource_fields
        assert "lean_declaration_hits" in resource_fields
    assert "lean_lsp_mcp" in bridge_row["resource_contracts_by_resource"]
    assert bridge_row["resource_contracts_by_resource"]["lean_lsp_mcp"]
    assert "mcp_tool_call" in bridge_row["request_contract_fields_by_resource"][
        "lean_lsp_mcp"
    ]
    assert "prover_diagnostics" in bridge_row["response_contract_fields_by_resource"][
        "lean_lsp_mcp"
    ]
    assert "bridge lemma statement" in bridge_row["expected_outputs"]
    source_row = by_primitive["coverage_inequality"]
    assert source_row["queue_action_kind"] == "source_port"
    assert source_row["minimal_delta_cost_score"] == 60
    assert source_row["reuse_readiness_score"] == 35
    assert source_row["evidence_readiness_score"] == 65
    assert "literature_grounded_route_synthesis" in source_row["component_ids"]
    assert "paperclip_cli_mcp" in source_row["frontier_escalation_resource_ids"]
    assert "local_literature_corpus" in source_row["local_first_resource_ids"]
    assert source_row["actionable_work_items"] == (
        "coverage_inequality: port the source-backed coverage inequality",
    )
    assert "source_refs" in source_row["response_contract_fields"]
    assert "paperclip_cli_mcp" in source_row["resource_contracts_by_resource"]
    assert "mcp_tool_call" in source_row["request_contract_fields_by_resource"][
        "paperclip_cli_mcp"
    ]
    assert "source_refs" in source_row["response_contract_fields_by_resource"][
        "paperclip_cli_mcp"
    ]
    assert "not theorem proof evidence" in source_row["proof_evidence_boundary"]
    assert validate_action_resource_plan_row(
        bridge_row,
        action_resource_plan_row_json_schema(),
    ) == []
    malformed = dict(bridge_row)
    malformed.pop("component_ids")
    assert "component_ids required" in validate_action_resource_plan_row(
        malformed,
        action_resource_plan_row_json_schema(),
    )
    wrong_target = dict(exact_row)
    wrong_target["candidate_declaration_rows"] = [
        {
            "declaration": "Probability.exchangeable",
            "target_prover_family": "rocq",
            "source_field": "candidate_declarations",
        }
    ]
    assert (
        "candidate_declaration_rows[0].target_prover_family must match row target_prover_family"
        in validate_action_resource_plan_row(
            wrong_target,
            action_resource_plan_row_json_schema(),
        )
    )
    assert (
        action_resource_plan_dir
        / "formalization_gap_planner_action_resource_plan_manifest.json"
    ).exists()
    assert (
        action_resource_plan_dir / "formalization_gap_planner_action_resource_plan.jsonl"
    ).exists()
    assert (
        action_resource_plan_dir
        / "formalization_gap_planner_action_resource_plan_row.schema.json"
    ).exists()
    assert (
        action_resource_plan_dir / "formalization_gap_planner_action_resource_plan.md"
    ).exists()


def test_action_resource_plan_reports_mixed_targets_from_rows() -> None:
    root = Path("runs/test_formalization_gap_planner_action_resource_plan_mixed")
    input_json = root / "standalone_input.json"
    plan_dir = root / "plan"
    coverage_dir = root / "coverage"
    action_queue_dir = root / "action_queue"
    component_resource_registry_dir = root / "component_resource_registry"
    action_resource_plan_dir = root / "action_resource_plan"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "component_name": "formalization_gap_planner_standalone_input",
                "library_snapshot_ref": "mixed:action-resource-target-summary",
                "routes": [
                    {
                        "route_id": "lean_rank_route",
                        "display_name": "lean_rank_route",
                        "target_prover_family": "lean4",
                        "theorem_statement": "A Lean route.",
                        "primitives": [
                            {
                                "primitive": "exchangeability",
                                "coverage_status": "exact_exists",
                                "candidate_declarations": ["Probability.exchangeable"],
                            }
                        ],
                    },
                    {
                        "route_id": "rocq_rank_route",
                        "display_name": "rocq_rank_route",
                        "target_prover_family": "rocq",
                        "theorem_statement": "A Rocq route.",
                        "source_refs": ["rocq_conformal_notes"],
                        "primitives": [
                            {
                                "primitive": "rank_uniformity",
                                "coverage_status": "source_port_needed",
                                "source_refs": ["rocq_conformal_notes"],
                            }
                        ],
                    },
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    export_formalization_gap_planner_standalone_plan(input_json, plan_dir)
    export_formalization_gap_planner_library_coverage_map(plan_dir, coverage_dir)
    action_queue_payload = export_formalization_gap_planner_primitive_action_queue(
        coverage_dir,
        action_queue_dir,
    )
    export_formalization_gap_planner_component_resource_registry(
        component_resource_registry_dir
    )

    payload = export_formalization_gap_planner_action_resource_plan(
        action_queue_dir,
        component_resource_registry_dir,
        action_resource_plan_dir,
    )

    assert action_queue_payload["all_ok"]
    assert action_queue_payload["target_prover_family"] == "mixed:lean4,rocq"
    assert action_queue_payload["n_target_prover_families"] == 2
    assert action_queue_payload["by_target_prover_family"] == {"lean4": 1, "rocq": 1}
    assert payload["all_ok"]
    assert payload["target_prover_family"] == "mixed:lean4,rocq"
    assert payload["n_target_prover_families"] == 2
    assert payload["by_target_prover_family"] == {"lean4": 1, "rocq": 1}
    rows_by_route = {row["route_id"]: row for row in payload["rows"]}
    assert rows_by_route["lean_rank_route"]["target_prover_family"] == "lean4"
    assert rows_by_route["rocq_rank_route"]["target_prover_family"] == "rocq"


def test_action_resource_plan_keeps_lean_resources_for_default_adapter_target() -> None:
    root = Path("runs/test_formalization_gap_planner_action_resource_plan_lean_adapter")
    input_json = root / "standalone_input.json"
    plan_dir = root / "plan"
    coverage_dir = root / "coverage"
    action_queue_dir = root / "action_queue"
    component_resource_registry_dir = root / "component_resource_registry"
    action_resource_plan_dir = root / "action_resource_plan"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "component_name": "formalization_gap_planner_standalone_input",
                "target_prover_family": "lean4_adapter_with_portable_gap_schema",
                "library_snapshot_ref": "lean_adapter_snapshot",
                "routes": [
                    {
                        "route_id": "lean_adapter_route",
                        "display_name": "lean_adapter_route",
                        "theorem_statement": "A Lean adapter replay route.",
                        "primitives": [
                            {
                                "primitive": "adapter_bridge",
                                "coverage_status": "exact_exists",
                                "candidate_declarations": ["True.intro"],
                            }
                        ],
                    }
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    export_formalization_gap_planner_standalone_plan(input_json, plan_dir)
    export_formalization_gap_planner_library_coverage_map(plan_dir, coverage_dir)
    export_formalization_gap_planner_primitive_action_queue(
        coverage_dir,
        action_queue_dir,
    )
    export_formalization_gap_planner_component_resource_registry(
        component_resource_registry_dir
    )

    payload = export_formalization_gap_planner_action_resource_plan(
        action_queue_dir,
        component_resource_registry_dir,
        action_resource_plan_dir,
    )

    assert payload["all_ok"]
    row = payload["rows"][0]
    assert row["target_prover_family"] == "lean4_adapter_with_portable_gap_schema"
    assert "local_lake_lean" in row["local_first_resource_ids"]
    assert "lean_lsp_mcp" in row["frontier_escalation_resource_ids"]
    assert row["resource_contract_ids"]
    assert "prover_diagnostics" in row["response_contract_fields_by_resource"][
        "local_lake_lean"
    ]


def test_action_resource_plan_filters_target_specific_resources_for_rocq_bridge() -> None:
    root = Path("runs/test_formalization_gap_planner_action_resource_plan_rocq")
    input_json = root / "standalone_input.json"
    plan_dir = root / "plan"
    coverage_dir = root / "coverage"
    action_queue_dir = root / "action_queue"
    component_resource_registry_dir = root / "component_resource_registry"
    action_resource_plan_dir = root / "action_resource_plan"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "component_name": "formalization_gap_planner_standalone_input",
                "target_prover_family": "rocq",
                "library_snapshot_ref": "rocq_conformal_snapshot",
                "routes": [
                    {
                        "route_id": "rocq_rank_route",
                        "display_name": "rocq_rank_route",
                        "theorem_statement": "A Rocq rank route.",
                        "primitives": [
                            {
                                "primitive": "rank_uniformity",
                                "coverage_status": "bridge_needed",
                                "expected_premises": ["exchangeability"],
                            }
                        ],
                    }
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    export_formalization_gap_planner_standalone_plan(input_json, plan_dir)
    export_formalization_gap_planner_library_coverage_map(plan_dir, coverage_dir)
    export_formalization_gap_planner_primitive_action_queue(
        coverage_dir,
        action_queue_dir,
    )
    export_formalization_gap_planner_component_resource_registry(
        component_resource_registry_dir
    )

    payload = export_formalization_gap_planner_action_resource_plan(
        action_queue_dir,
        component_resource_registry_dir,
        action_resource_plan_dir,
    )

    assert payload["all_ok"]
    row = payload["rows"][0]
    assert row["target_prover_family"] == "rocq"
    assert "local_target_formal_source_index" in row["local_first_resource_ids"]
    assert "rocq_lsp_serapi" in row["frontier_escalation_resource_ids"]
    lean_only_resources = {
        "local_formal_source_index",
        "local_lean_rag_dependency_graph",
        "loogle_leansearch",
        "leanexplore_mcp",
        "lean_blueprint_leanarchitect",
        "local_lake_lean",
        "lean_lsp_mcp",
        "leandojo_reprover",
    }
    selected_resources = set(row["local_first_resource_ids"]) | set(
        row["frontier_escalation_resource_ids"]
    )
    assert not selected_resources.intersection(lean_only_resources)
    assert "formal_declaration_hits" in row["response_contract_fields_by_resource"][
        "local_target_formal_source_index"
    ]
    assert "lean_declaration_hits" not in row["response_contract_fields_by_resource"][
        "local_target_formal_source_index"
    ]
    assert "prover_diagnostics" in row["response_contract_fields_by_resource"][
        "rocq_lsp_serapi"
    ]
    assert "target_prover_family" in row["request_contract_fields_by_resource"][
        "rocq_lsp_serapi"
    ]


def test_action_resource_plan_marks_missing_registry_as_blocker() -> None:
    root = Path("runs/test_formalization_gap_planner_action_resource_plan_rejects")
    input_json = root / "standalone_input.json"
    plan_dir = root / "plan"
    coverage_dir = root / "coverage"
    action_queue_dir = root / "action_queue"
    missing_registry_dir = root / "missing_component_resource_registry"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json.write_text(
        json.dumps(
            {
                "library_snapshot_ref": "lean_fixture",
                "routes": [
                    {
                        "display_name": "demo_target",
                        "primitives": [
                            {
                                "primitive": "demo_existing",
                                "coverage_status": "exact_exists",
                                "candidate_declarations": ["Demo.existing"],
                            }
                        ],
                    }
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    export_formalization_gap_planner_standalone_plan(input_json, plan_dir)
    export_formalization_gap_planner_library_coverage_map(plan_dir, coverage_dir)
    export_formalization_gap_planner_primitive_action_queue(
        coverage_dir,
        action_queue_dir,
    )

    payload = export_formalization_gap_planner_action_resource_plan(
        action_queue_dir,
        missing_registry_dir,
    )

    assert not payload["all_ok"]
    assert payload["n_resource_plan_rows"] == 1
    assert payload["n_failed"] == 1
    assert payload["n_row_schema_invalid"] == 1
    assert payload["errors"]
    assert payload["rows"][0]["errors"]
