from __future__ import annotations

import json
import shutil
from pathlib import Path

from ai_statistician.formalization_gap_planner_contract import (
    PORTABLE_FORMALIZATION_GAP_PLAN_SCHEMA_ID,
    PORTABLE_FORMALIZATION_GAP_PLAN_ROW_SCHEMA_ID,
    ROUTE_ALIGNMENT_EDGE_SCHEMA_ID,
    portable_gap_plan_row_json_schema,
    route_alignment_edge_json_schema,
    validate_portable_gap_plan_row,
    validate_route_alignment_edge,
    validate_portable_gap_plan_payload,
)
from ai_statistician.formalization_gap_planner_prover_adapter_contract import (
    export_formalization_gap_planner_prover_adapter_contract,
)
from ai_statistician.formalization_gap_planner_library_coverage_map import (
    export_formalization_gap_planner_library_coverage_map,
)
from ai_statistician.formalization_gap_planner_standalone import (
    FORMALIZATION_GAP_PLANNER_STANDALONE_INPUT_SCHEMA_ID,
    export_formalization_gap_planner_standalone_plan,
    standalone_input_json_schema,
    validate_standalone_input_payload,
)


def test_standalone_gap_planner_exports_portable_plan_for_external_prover() -> None:
    root = Path("runs/test_formalization_gap_planner_standalone")
    input_json = root / "standalone_input.json"
    out_dir = root / "plan"
    prover_contract_dir = root / "prover_contract"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "component_name": "formalization_gap_planner_standalone_input",
                "target_prover_family": "rocq",
                "library_snapshot_ref": "rocq_mathcomp_probability_snapshot",
                "background_primitives": [
                    "conditional_expectation",
                    "exchangeability",
                    "unrelated_measure_theory_chapter",
                ],
                "routes": [
                    {
                        "display_name": "split_conformal_finite_sample_coverage",
                        "theorem_statement": (
                            "For exchangeable calibration/test scores, split conformal "
                            "prediction has finite-sample marginal coverage."
                        ),
                        "theorem_skeleton": (
                            "Theorem split_conformal_finite_sample_coverage : True."
                        ),
                        "import_cone_size": 18,
                        "dependency_graph_depth": 2,
                        "source_trust_level": "local_candidate_declarations",
                        "primitives": [
                            {
                                "primitive": "exchangeability",
                                "coverage_status": "exact_exists",
                                "candidate_declarations": ["Probability.exchangeable"],
                                "cost": 1,
                            },
                            {
                                "primitive": "rank_uniformity",
                                "coverage_status": "bridge_needed",
                                "expected_premises": ["exchangeability"],
                                "cost": 5,
                            },
                            {
                                "primitive": "quantile_wrapper",
                                "coverage_status": "wrapper_needed",
                                "candidate_declarations": ["Order.quantile"],
                            },
                            {
                                "primitive": "coverage_inequality",
                                "coverage_status": "source_port_needed",
                                "source_refs": ["vovk_gammerman_shafer_conformal"],
                            },
                        ],
                    }
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    payload = export_formalization_gap_planner_standalone_plan(input_json, out_dir)

    assert payload["all_ok"]
    assert payload["portable_schema_id"] == PORTABLE_FORMALIZATION_GAP_PLAN_SCHEMA_ID
    assert payload["standalone_input_schema_id"] == FORMALIZATION_GAP_PLANNER_STANDALONE_INPUT_SCHEMA_ID
    assert payload["target_prover_family"] == "rocq"
    assert payload["n_goal_plans"] == 1
    assert payload["n_existing_reuse_nodes"] == 1
    assert payload["n_wrapper_nodes"] == 1
    assert payload["n_bridge_nodes"] == 1
    assert payload["n_source_discovery_nodes"] == 1
    assert payload["n_portable_work_packets"] >= 1
    assert payload["n_route_alignment_edge_schema_valid"] == payload["n_route_alignment_edges"]
    assert payload["n_route_alignment_edge_schema_invalid"] == 0
    assert payload["n_formal_realization_dag_nodes"] > 0
    assert payload["n_lean_realization_dag_nodes"] == 0
    assert payload["n_formal_realization_dag_edges"] > 0
    assert payload["n_lean_realization_dag_edges"] == 0
    assert payload["n_standalone_input_traces"] == payload["n_goal_plans"]
    assert payload["n_standalone_input_traces_with_replan_metadata"] == 0
    assert payload["n_standalone_input_trace_primitive_source_refs"] == 1
    assert payload["n_goal_plan_row_schema_valid"] == payload["n_goal_plans"]
    assert payload["n_goal_plan_row_schema_invalid"] == 0
    assert payload["route_alignment_edge_schema"]["$id"] == ROUTE_ALIGNMENT_EDGE_SCHEMA_ID
    assert payload["goal_plan_row_schema"]["$id"] == PORTABLE_FORMALIZATION_GAP_PLAN_ROW_SCHEMA_ID
    assert not validate_portable_gap_plan_payload(payload)
    row = payload["rows"][0]
    assert validate_portable_gap_plan_row(row, portable_gap_plan_row_json_schema()) == []
    malformed_row = dict(row)
    malformed_row.pop("portable_work_packet_contract")
    assert validate_portable_gap_plan_row(malformed_row, portable_gap_plan_row_json_schema())
    assert row["target_prover_family"] == "rocq"
    assert "unrelated_measure_theory_chapter" in row["do_not_formalize_now"]
    assert row["informal_knowledge_dag_nodes"]
    assert row["formal_realization_dag_nodes"]
    assert row["lean_realization_dag_nodes"] == []
    assert row["lean_realization_dag_edges"] == []
    assert row["route_alignment_edges"]
    assert row["standalone_input_trace"]["trace_kind"] == "standalone_input_route_trace"
    assert row["standalone_input_trace"]["source_route_id"] == row["route_id"]
    assert row["standalone_input_trace"]["target_prover_family"] == "rocq"
    assert not row["standalone_input_trace"]["has_replan_metadata"]
    assert row["standalone_input_trace"]["primitive_source_refs"] == [
        {
            "primitive": "coverage_inequality",
            "source_refs": ["vovk_gammerman_shafer_conformal"],
        }
    ]
    assert {
        edge["primitive"] for edge in row["route_alignment_edges"]
    } == set(row["selected_primitives"])
    assert all(
        edge["kind"] == "aligned_to_formal_realization_candidate"
        for edge in row["route_alignment_edges"]
    )
    malformed_edge = dict(row["route_alignment_edges"][0])
    malformed_edge.pop("proof_evidence_boundary")
    assert validate_route_alignment_edge(
        malformed_edge,
        route_alignment_edge_json_schema(),
    )
    assert row["interactive_refinement_hooks"]
    assert "not theorem proof evidence" in row["proof_evidence_boundary"]
    assert (
        out_dir / "goal_conditioned_minimal_formalization_plan_manifest.json"
    ).exists()
    assert (
        out_dir / "formalization_gap_planner_standalone_input.schema.json"
    ).exists()
    assert (
        out_dir / "formalization_gap_planner_route_alignment_edge.schema.json"
    ).exists()
    assert (
        out_dir / "library_aware_formalization_gap_plan_row.schema.json"
    ).exists()
    standalone_schema = standalone_input_json_schema()
    assert (
        standalone_schema["$id"]
        == FORMALIZATION_GAP_PLANNER_STANDALONE_INPUT_SCHEMA_ID
    )
    route_schema = standalone_schema["$defs"]["route"]
    route_props = route_schema["properties"]
    assert route_props["target_prover_family"]["type"] == "string"
    assert (
        route_props["candidate_declaration_rows"]["items"]["$ref"]
        == "#/$defs/candidate_declaration_row"
    )
    primitive_props = standalone_schema["$defs"]["primitive"]["properties"]
    assert (
        primitive_props["candidate_declaration_rows"]["items"]["$ref"]
        == "#/$defs/candidate_declaration_row"
    )
    candidate_row_schema = standalone_schema["$defs"]["candidate_declaration_row"]
    assert {"required": ["declaration"]} in candidate_row_schema["anyOf"]
    assert candidate_row_schema["properties"]["target_prover_family"]["type"] == "string"
    assert (
        route_props["revised_informal_knowledge_dag_nodes"]["items"]["$ref"]
        == "#/$defs/dag_node"
    )
    assert (
        route_props["revised_formal_realization_dag_nodes"]["items"]["$ref"]
        == "#/$defs/dag_node"
    )
    assert (
        route_props["revised_lean_realization_dag_nodes"]["items"]["$ref"]
        == "#/$defs/dag_node"
    )
    assert (
        route_props["revised_route_alignment_edges"]["items"]["$ref"]
        == "#/$defs/route_alignment_edge"
    )
    assert (
        route_props["minimal_delta_and_or_cost_graph"]["$ref"]
        == "#/$defs/minimal_delta_and_or_cost_graph"
    )
    assert route_props["replan_metadata"]["$ref"] == "#/$defs/replan_metadata"
    metadata_props = standalone_schema["$defs"]["replan_metadata"]["properties"]
    assert metadata_props["target_prover_family"]["type"] == "string"
    assert (
        metadata_props["formal_declaration_hits"]["items"]["$ref"]
        == "#/$defs/formal_declaration_hit"
    )
    assert (
        metadata_props["lean_declaration_hits"]["items"]["$ref"]
        == "#/$defs/lean_declaration_hit"
    )
    assert (
        metadata_props["revised_route_alignment_edges"]["items"]["$ref"]
        == "#/$defs/route_alignment_edge"
    )
    assert (
        metadata_props["minimal_delta_and_or_cost_graph"]["$ref"]
        == "#/$defs/minimal_delta_and_or_cost_graph"
    )
    assert (
        standalone_schema["$defs"]["minimal_delta_and_or_cost_graph"]["properties"][
            "route_options"
        ]["items"]["$ref"]
        == "#/$defs/route_option_cost"
    )
    assert (
        metadata_props["revised_formal_realization_dag_nodes"]["items"]["$ref"]
        == "#/$defs/dag_node"
    )
    assert metadata_props["alignment_edge_primitives"]["items"]["type"] == "string"

    prover_payload = export_formalization_gap_planner_prover_adapter_contract(
        out_dir,
        prover_contract_dir,
        target_prover_family="isabelle",
        library_snapshot_ref="isabelle_probability_snapshot",
    )

    assert prover_payload["all_ok"]
    assert prover_payload["target_prover_family"] == "isabelle"
    assert prover_payload["n_packets"] == payload["n_portable_work_packets"]


def test_standalone_gap_planner_preserves_llm_minimal_delta_cost_graph_trace() -> None:
    root = Path("runs/test_formalization_gap_planner_standalone_cost_graph_trace")
    input_json = root / "standalone_input.json"
    out_dir = root / "plan"
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
                "schema_version": 1,
                "component_name": "formalization_gap_planner_standalone_input",
                "target_prover_family": "lean4",
                "library_snapshot_ref": "mathlib4:cost-graph-fixture",
                "routes": [
                    {
                        "route_id": "rank_route",
                        "display_name": "rank_route",
                        "theorem_statement": "Rank uniformity follows from exchangeability.",
                        "source_refs": ["conformal_prediction_textbook"],
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
                                "expected_premises": ["exchangeability"],
                            },
                        ],
                    }
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    payload = export_formalization_gap_planner_standalone_plan(input_json, out_dir)

    assert payload["all_ok"]
    assert payload["n_standalone_input_traces_with_replan_metadata"] == 1
    assert payload["n_standalone_input_traces_with_minimal_delta_cost_graph"] == 1
    assert payload["n_standalone_input_traces_with_realization_coverage_witness"] == 1
    assert (
        payload["n_standalone_input_traces_with_complete_realization_coverage"] == 1
    )
    assert (
        payload[
            "n_standalone_input_trace_selected_primitives_missing_formal_realization"
        ]
        == 0
    )
    assert (
        payload["n_standalone_input_trace_delta_primitives_missing_route_alignment"]
        == 0
    )
    assert payload["n_standalone_input_trace_route_options"] == 2
    row = payload["rows"][0]
    assert row["best_route_cost"] == 4
    action_cost_by_primitive = {
        packet["primitive"]: packet["expected_cost"]
        for packet in row["next_work_packets"]
    }
    assert action_cost_by_primitive["rank_uniformity"] == 4
    trace = row["standalone_input_trace"]
    assert trace["has_minimal_delta_and_or_cost_graph"] is True
    assert trace["minimal_delta_route_option_count"] == 2
    assert trace["minimal_delta_selected_route_option_id"] == "route_option:bridge_rank"
    assert trace["minimal_delta_selected_route_cost"] == 4
    assert trace["minimal_delta_and_or_cost_graph"] == cost_graph
    assert trace["has_realization_coverage_witness"] is True
    assert trace["realization_coverage_complete"] is True
    assert trace["realization_coverage_witness"] == realization_witness
    assert trace["realization_selected_primitives_missing_formal_realization"] == []
    assert trace["realization_delta_primitives_missing_route_alignment"] == []


def test_standalone_gap_planner_preserves_candidate_declaration_rows_into_coverage_map() -> None:
    root = Path("runs/test_formalization_gap_planner_standalone_candidate_rows")
    input_json = root / "standalone_input.json"
    out_dir = root / "plan"
    coverage_dir = root / "coverage"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    declaration_row = {
        "declaration": "Probability.exchangeable",
        "target_prover_family": "lean4",
        "source_field": "route_candidate_declaration_rows",
    }
    input_json.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "component_name": "formalization_gap_planner_standalone_input",
                "target_prover_family": "lean4",
                "library_snapshot_ref": "mathlib4:candidate-row-fixture",
                "routes": [
                    {
                        "route_id": "exchangeability_route",
                        "display_name": "exchangeability_route",
                        "theorem_statement": "Exchangeability is available in the library.",
                        "primitives": [
                            {
                                "primitive": "exchangeability",
                                "coverage_status": "exact_exists",
                                "candidate_declaration_rows": [declaration_row],
                            }
                        ],
                    }
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    payload = export_formalization_gap_planner_standalone_plan(input_json, out_dir)

    assert payload["all_ok"]
    assert payload["n_lean_realization_dag_nodes"] == payload[
        "n_formal_realization_dag_nodes"
    ]
    row = payload["rows"][0]
    assert row["lean_realization_dag_nodes"] == row["formal_realization_dag_nodes"]
    assert row["lean_realization_dag_edges"] == row["formal_realization_dag_edges"]
    reuse_node = row["existing_reuse_nodes"][0]
    assert reuse_node["candidate_declaration_rows"] == [declaration_row]
    assert reuse_node["candidate_declarations"] == ["Probability.exchangeable"]
    realization_node = next(
        node
        for node in row["formal_realization_dag_nodes"]
        if node.get("label") == "exchangeability"
    )
    assert realization_node["candidate_declaration_rows"] == [declaration_row]
    assert "Probability.exchangeable" in realization_node["declaration_sources"]
    assert row["standalone_input_trace"]["primitive_candidate_declaration_rows"] == [
        {
            "primitive": "exchangeability",
            "candidate_declaration_rows": [declaration_row],
        }
    ]

    coverage_payload = export_formalization_gap_planner_library_coverage_map(
        out_dir,
        coverage_dir,
    )

    assert coverage_payload["all_ok"]
    assert coverage_payload["n_rows_with_candidate_declaration_rows"] == 1
    coverage_row = coverage_payload["rows"][0]
    assert coverage_row["primitive"] == "exchangeability"
    assert coverage_row["candidate_declaration_rows"] == (declaration_row,)
    assert coverage_row["candidate_declarations"] == ("Probability.exchangeable",)


def test_standalone_input_rejects_cross_prover_candidate_declaration_rows() -> None:
    root = Path("runs/test_formalization_gap_planner_standalone_bad_candidate_target")
    input_json = root / "standalone_input.json"
    out_dir = root / "plan"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": 1,
        "component_name": "formalization_gap_planner_standalone_input",
        "target_prover_family": "rocq",
        "library_snapshot_ref": "rocq:cross-prover-guard",
        "routes": [
            {
                "route_id": "rocq_rank_route",
                "display_name": "rocq_rank_route",
                "target_prover_family": "rocq",
                "theorem_statement": "A Rocq rank lemma should use Rocq evidence.",
                "candidate_declaration_rows": [
                    {
                        "declaration": "Mathlib.Probability.exchangeable",
                        "target_prover_family": "lean4",
                        "source_field": "route_level_formal_context",
                    }
                ],
                "primitives": [
                    {
                        "primitive": "exchangeability",
                        "coverage_status": "exact_exists",
                        "candidate_declaration_rows": [
                            {
                                "declaration": "Mathlib.Probability.exchangeable",
                                "target_prover_family": "lean4",
                                "source_field": "route_candidate_declaration_rows",
                            }
                        ],
                    }
                ],
            }
        ],
    }
    input_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    errors = validate_standalone_input_payload(payload)

    assert any(
        "routes[0].candidate_declaration_rows[0].target_prover_family lean4 "
        "does not match target_prover_family rocq" in error
        for error in errors
    )
    assert any(
        "routes[0].primitives[0].candidate_declaration_rows[0]"
        ".target_prover_family lean4 does not match target_prover_family rocq"
        in error
        for error in errors
    )
    payload = export_formalization_gap_planner_standalone_plan(input_json, out_dir)
    assert not payload["all_ok"]
    assert payload["errors"]


def test_standalone_input_accepts_target_prover_aliases_for_declaration_rows() -> None:
    payload = {
        "schema_version": 1,
        "component_name": "formalization_gap_planner_standalone_input",
        "target_prover_family": "rocq",
        "library_snapshot_ref": "rocq:alias-guard",
        "routes": [
            {
                "route_id": "rocq_rank_route",
                "display_name": "rocq_rank_route",
                "target_prover_family": "coq",
                "replan_metadata": {"target_prover_family": "coq8"},
                "theorem_statement": "Coq/Rocq aliases should remain compatible.",
                "primitives": [
                    {
                        "primitive": "exchangeability",
                        "coverage_status": "exact_exists",
                        "candidate_declaration_rows": [
                            {
                                "declaration": "Rocq.Probability.exchangeable",
                                "target_prover_family": "coq8",
                                "source_field": "route_candidate_declaration_rows",
                            }
                        ],
                    }
                ],
            }
        ],
    }

    assert validate_standalone_input_payload(payload) == []
