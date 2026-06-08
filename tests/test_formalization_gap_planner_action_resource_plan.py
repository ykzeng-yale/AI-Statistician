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
    assert (
        payload["action_resource_plan_row_schema"]["$id"]
        == ACTION_RESOURCE_PLAN_ROW_SCHEMA_ID
    )
    assert (
        payload["n_with_frontier_escalation_resources"]
        == payload["n_resource_plan_rows"]
    )
    assert payload["n_with_resource_contracts"] == payload["n_resource_plan_rows"]
    by_primitive = {row["primitive"]: row for row in payload["rows"]}
    exact_row = by_primitive["exchangeability"]
    assert exact_row["candidate_declaration_rows"] == (
        {
            "declaration": "Probability.exchangeable",
            "target_prover_family": "lean4",
            "source_field": "candidate_declarations",
        },
    )
    bridge_row = by_primitive["rank_uniformity"]
    assert bridge_row["queue_action_kind"] == "prove_bridge_lemma"
    assert "formal_library_coverage_mapping" in bridge_row["component_ids"]
    assert "minimal_delta_and_or_planning" in bridge_row["component_ids"]
    assert "prover_feedback_refinement" in bridge_row["component_ids"]
    assert "lean_lsp_mcp" in bridge_row["frontier_escalation_resource_ids"]
    assert "formal_declaration_hits" in bridge_row["response_contract_fields"]
    assert "lean_declaration_hits" in bridge_row["response_contract_fields"]
    assert "prover_diagnostics" in bridge_row["response_contract_fields"]
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
    assert "literature_grounded_route_synthesis" in source_row["component_ids"]
    assert "paperclip_cli_mcp" in source_row["frontier_escalation_resource_ids"]
    assert "local_literature_corpus" in source_row["local_first_resource_ids"]
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
