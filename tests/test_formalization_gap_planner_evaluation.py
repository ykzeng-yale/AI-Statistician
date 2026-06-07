from __future__ import annotations

import json
import shutil
from pathlib import Path

from ai_statistician.formalization_gap_planner_evaluation import (
    evaluation_row_json_schema,
    evaluate_formalization_gap_planner,
    validate_evaluation_row,
)
from ai_statistician.formalization_gap_planner_standalone import (
    export_formalization_gap_planner_standalone_plan,
)


def test_evaluation_scores_route_alignment_contract() -> None:
    root = Path("runs/test_formalization_gap_planner_evaluation")
    input_json = root / "standalone_input.json"
    plan_dir = root / "plan"
    truth_json = root / "ground_truth.json"
    out_dir = root / "evaluation"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "component_name": "formalization_gap_planner_standalone_input",
                "target_prover_family": "lean4",
                "library_snapshot_ref": "lean_alignment_fixture",
                "routes": [
                    {
                        "route_id": "route:alignment_fixture",
                        "display_name": "alignment fixture theorem",
                        "theorem_statement": "A sourced bridge route proves the target.",
                        "primitives": [
                            {
                                "primitive": "existing_exchangeability",
                                "coverage_status": "exact_exists",
                                "candidate_declarations": ["Probability.exchangeable"],
                            },
                            {
                                "primitive": "rank_bridge",
                                "coverage_status": "bridge_needed",
                                "side_conditions": [
                                    "rank_bridge: missing order-statistic side condition"
                                ],
                            },
                            {
                                "primitive": "coverage_source_port",
                                "coverage_status": "source_port_needed",
                                "source_refs": ["fixture#coverage"],
                            },
                        ],
                    }
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    truth_json.write_text(
        json.dumps(
            {
                "routes": [
                    {
                        "route_id": "route:alignment_fixture",
                        "required_primitives": [
                            "existing_exchangeability",
                            "rank_bridge",
                            "coverage_source_port",
                        ],
                        "actual_existing_reuse_primitives": ["existing_exchangeability"],
                        "actual_delta_primitives": [
                            "rank_bridge",
                            "coverage_source_port",
                        ],
                        "expected_residual_primitives": ["rank_bridge"],
                        "expected_residual_goals": [
                            "rank_bridge: missing order-statistic side condition"
                        ],
                    }
                ]
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    export_formalization_gap_planner_standalone_plan(input_json, plan_dir)

    payload = evaluate_formalization_gap_planner(plan_dir, truth_json, out_dir)

    assert payload["all_ok"]
    assert payload["n_alignment_contract_ok"] == payload["n_evaluation_rows"] == 1
    assert (
        payload["n_evaluation_row_schema_valid"]
        == payload["n_evaluation_rows"]
    )
    assert payload["n_evaluation_row_schema_invalid"] == 0
    assert payload["evaluation_row_schema"]["$id"] == evaluation_row_json_schema()["$id"]
    assert payload["n_unaligned_primitives"] == 0
    assert payload["mean_alignment_coverage"] == 1.0
    assert payload["n_ground_truth_residual_rows"] == 1
    assert payload["mean_residual_precision"] == 1.0
    assert payload["mean_residual_recall"] == 1.0
    row = payload["rows"][0]
    assert row["alignment_contract_ok"]
    assert not validate_evaluation_row(row)
    broken_row = dict(row)
    broken_row.pop("proof_evidence_boundary")
    assert "proof_evidence_boundary required" in validate_evaluation_row(broken_row)
    assert row["alignment_coverage"] == 1.0
    assert set(row["aligned_primitives"]) == set(row["predicted_route_primitives"])
    assert row["predicted_residual_primitives"] == ("rank_bridge",)
    assert row["ground_truth_residual_primitives"] == ("rank_bridge",)
    assert row["residual_true_positive_primitives"] == ("rank_bridge",)
    assert row["residual_precision"] == 1.0
    assert row["residual_recall"] == 1.0
    assert row["predicted_residual_goals"] == (
        "rank_bridge: missing order-statistic side condition",
    )
    assert not row["unaligned_primitives"]
    assert (
        out_dir / "formalization_gap_planner_evaluation_manifest.json"
    ).exists()
    assert (
        out_dir / "formalization_gap_planner_evaluation_row.schema.json"
    ).exists()
    assert (
        out_dir / "formalization_gap_planner_evaluation_ground_truth.json"
    ).exists()


def test_evaluation_reports_minimal_delta_cost_graph_trace() -> None:
    root = Path("runs/test_formalization_gap_planner_evaluation_cost_graph")
    input_json = root / "standalone_input.json"
    plan_dir = root / "plan"
    truth_json = root / "ground_truth.json"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    cost_graph = {
        "graph_kind": "AND_OR_ROUTE_COST_GRAPH",
        "selected_route_option_id": "route_option:bridge_rank",
        "route_options": [
            {
                "route_option_id": "route_option:bridge_rank",
                "selected": True,
                "selected_primitives": ["exchangeability", "rank_uniformity"],
                "route_cost": 4,
                "cost_rationale": "Reuse exchangeability and prove one bridge.",
            },
            {
                "route_option_id": "route_option:source_port_rank",
                "selected": False,
                "selected_primitives": ["exchangeability", "rank_uniformity"],
                "route_cost": 7,
                "cost_rationale": "Source port is broader than the bridge.",
            },
        ],
    }
    realization_witness = {
        "selected_primitives": ["exchangeability", "rank_uniformity"],
        "delta_primitives": ["rank_uniformity"],
        "introduced_primitives": [],
        "aligned_primitives": ["exchangeability", "rank_uniformity"],
        "selected_primitives_missing_formal_realization_node": [],
        "delta_primitives_missing_route_alignment_edge": [],
        "introduced_primitives_missing_route_alignment_edge": [],
        "realization_coverage_complete": True,
    }
    input_json.write_text(
        json.dumps(
            {
                "component_name": "formalization_gap_planner_standalone_input",
                "library_snapshot_ref": "mathlib4:evaluation-cost-graph",
                "routes": [
                    {
                        "route_id": "rank_route",
                        "display_name": "rank_route",
                        "theorem_statement": "Rank uniformity follows from exchangeability.",
                        "minimal_delta_and_or_cost_graph": cost_graph,
                        "realization_coverage_witness": realization_witness,
                        "replan_metadata": {
                            "minimal_delta_and_or_cost_graph": cost_graph,
                            "llm_route_planner_realization_coverage_witness": (
                                realization_witness
                            ),
                            "llm_route_planner_minimal_delta_plan": {
                                "selected_primitives": [
                                    "exchangeability",
                                    "rank_uniformity",
                                ],
                                "route_cost": 4,
                                "and_or_cost_graph": cost_graph,
                                "primitive_costs": [
                                    {
                                        "primitive": "exchangeability",
                                        "total_cost": 0,
                                    },
                                    {
                                        "primitive": "rank_uniformity",
                                        "total_cost": 4,
                                    },
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
                            },
                        ],
                    }
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    truth_json.write_text(
        json.dumps(
            {
                "routes": [
                    {
                        "route_id": "rank_route",
                        "required_primitives": ["exchangeability", "rank_uniformity"],
                        "actual_existing_reuse_primitives": ["exchangeability"],
                        "actual_delta_primitives": ["rank_uniformity"],
                    }
                ]
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    export_formalization_gap_planner_standalone_plan(input_json, plan_dir)

    payload = evaluate_formalization_gap_planner(plan_dir, truth_json)

    assert payload["n_rows_with_minimal_delta_cost_graph"] == 1
    assert payload["n_rows_with_realization_coverage_witness"] == 1
    assert payload["n_rows_with_complete_realization_coverage"] == 1
    assert payload["n_realization_missing_selected_formal_primitives"] == 0
    assert payload["n_realization_missing_delta_alignment_primitives"] == 0
    assert payload["n_minimal_delta_route_options"] == 2
    assert payload["mean_minimal_delta_selected_route_cost"] == 4.0
    row = payload["rows"][0]
    assert row["minimal_delta_cost_graph_present"] is True
    assert row["minimal_delta_route_option_count"] == 2
    assert row["minimal_delta_selected_route_option_id"] == "route_option:bridge_rank"
    assert row["minimal_delta_selected_route_cost"] == 4.0
    assert row["realization_coverage_witness_present"] is True
    assert row["realization_coverage_complete"] is True
    assert row["realization_missing_selected_formal_primitives"] == ()
    assert row["realization_missing_delta_alignment_primitives"] == ()
    assert validate_evaluation_row(row) == ()


def test_evaluation_rejects_missing_route_alignment() -> None:
    root = Path("runs/test_formalization_gap_planner_evaluation_alignment_rejects")
    input_json = root / "standalone_input.json"
    plan_dir = root / "plan"
    truth_json = root / "ground_truth.json"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json.write_text(
        json.dumps(
            {
                "library_snapshot_ref": "lean_alignment_fixture",
                "routes": [
                    {
                        "route_id": "route:alignment_rejects",
                        "display_name": "alignment rejects theorem",
                        "primitives": [
                            {
                                "primitive": "demo_existing",
                                "coverage_status": "exact_exists",
                                "candidate_declarations": ["Demo.existing"],
                            },
                            {
                                "primitive": "demo_source_port",
                                "coverage_status": "source_port_needed",
                                "source_refs": ["fixture#source"],
                            },
                        ],
                    }
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    truth_json.write_text(
        json.dumps(
            {
                "routes": [
                    {
                        "route_id": "route:alignment_rejects",
                        "required_primitives": ["demo_existing", "demo_source_port"],
                        "actual_existing_reuse_primitives": ["demo_existing"],
                        "actual_delta_primitives": ["demo_source_port"],
                    }
                ]
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    export_formalization_gap_planner_standalone_plan(input_json, plan_dir)
    manifest_path = plan_dir / "goal_conditioned_minimal_formalization_plan_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["rows"][0]["route_alignment_edges"] = [
        edge
        for edge in manifest["rows"][0]["route_alignment_edges"]
        if edge["primitive"] != "demo_source_port"
    ]
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    payload = evaluate_formalization_gap_planner(plan_dir, truth_json)

    assert not payload["all_ok"]
    assert (
        payload["n_evaluation_row_schema_valid"]
        == payload["n_evaluation_rows"]
    )
    assert payload["n_evaluation_row_schema_invalid"] == 0
    assert payload["n_alignment_contract_ok"] == 0
    assert payload["n_unaligned_primitives"] == 1
    assert payload["mean_alignment_coverage"] == 0.5
    row = payload["rows"][0]
    assert not row["alignment_contract_ok"]
    assert row["unaligned_primitives"] == ("demo_source_port",)
    assert "route alignment contract is incomplete" in row["errors"]
