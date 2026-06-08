from __future__ import annotations

import json
import shutil
from pathlib import Path

from ai_statistician.formalization_gap_planner_minimal_delta_audit import (
    audit_formalization_gap_planner_minimal_delta,
    minimal_delta_decision_row_json_schema,
    validate_minimal_delta_decision_row,
)
from ai_statistician.formalization_gap_planner_standalone import (
    export_formalization_gap_planner_standalone_plan,
)


def test_minimal_delta_audit_accepts_costed_standalone_plan() -> None:
    root = Path("runs/test_formalization_gap_planner_minimal_delta_audit")
    input_json = root / "standalone_input.json"
    plan_dir = root / "plan"
    audit_dir = root / "audit"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "component_name": "formalization_gap_planner_standalone_input",
                "target_prover_family": "lean4",
                "library_snapshot_ref": "mathlib4:minimal-delta",
                "background_primitives": ["unrelated_large_measure_theory"],
                "routes": [
                    {
                        "display_name": "demo_minimal_delta_route",
                        "theorem_statement": "A route follows from reuse and one bridge.",
                        "minimal_delta_plan": {
                            "selected_primitives": [
                                "existing_rank_order",
                                "rank_uniformity_bridge",
                            ],
                            "cost_model_version": (
                                "formalization_gap_planner_minimal_delta_cost_policy:1"
                            ),
                            "route_cost": 4,
                            "primitive_costs": [
                                {
                                    "primitive": "existing_rank_order",
                                    "base_cost": 0,
                                    "proof_difficulty_cost": 0,
                                    "import_cone_cost": 0,
                                    "definition_or_typeclass_cost": 0,
                                    "semantic_risk_cost": 0,
                                    "reuse_credit": 0,
                                    "total_cost": 0,
                                    "cost_rationale": "exact reuse from current library",
                                },
                                {
                                    "primitive": "rank_uniformity_bridge",
                                    "base_cost": 4,
                                    "proof_difficulty_cost": 0,
                                    "import_cone_cost": 0,
                                    "definition_or_typeclass_cost": 0,
                                    "semantic_risk_cost": 0,
                                    "reuse_credit": 0,
                                    "total_cost": 4,
                                    "cost_rationale": "one bridge lemma is cheaper than source port",
                                },
                            ],
                            "and_or_cost_graph": {
                                "graph_kind": "AND_OR_ROUTE_COST_GRAPH",
                                "selected_route_option_id": "route_option:reuse_bridge",
                                "route_options": [
                                    {
                                        "route_option_id": "route_option:reuse_bridge",
                                        "selected": True,
                                        "selected_primitives": [
                                            "existing_rank_order",
                                            "rank_uniformity_bridge",
                                        ],
                                        "route_cost": 4,
                                        "cost_rationale": "reuse plus one bridge is cheapest",
                                    },
                                    {
                                        "route_option_id": "route_option:source_port",
                                        "selected": False,
                                        "selected_primitives": [
                                            "rank_uniformity_source_port"
                                        ],
                                        "route_cost": 7,
                                        "cost_rationale": "source port has higher cost",
                                    },
                                ],
                                "or_nodes": [
                                    {
                                        "node_id": "route_choice",
                                        "choices": [
                                            "route_option:reuse_bridge",
                                            "route_option:source_port",
                                        ],
                                        "selection_rationale": (
                                            "reuse bridge has the lower current delta cost"
                                        ),
                                    }
                                ],
                                "and_edges": [
                                    {
                                        "route_option_id": "route_option:reuse_bridge",
                                        "requires": [
                                            "existing_rank_order",
                                            "rank_uniformity_bridge",
                                        ],
                                    },
                                    {
                                        "route_option_id": "route_option:source_port",
                                        "requires": ["rank_uniformity_source_port"],
                                    },
                                ],
                            },
                            "minimality_rationale": "Cost graph rejects the source-port route.",
                        },
                        "primitives": [
                            {
                                "primitive": "existing_rank_order",
                                "coverage_status": "exact_exists",
                                "candidate_declarations": ["Existing.rank_order"],
                            },
                            {
                                "primitive": "rank_uniformity_bridge",
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
    export_formalization_gap_planner_standalone_plan(input_json, plan_dir)

    payload = audit_formalization_gap_planner_minimal_delta(plan_dir, audit_dir)

    assert payload["all_ok"]
    assert payload["n_plan_rows"] == 1
    assert payload["n_failed"] == 0
    assert payload["n_rows_with_cost_formula_ok"] == 1
    assert payload["n_rows_with_node_cost_accounting_ok"] == 1
    assert payload["n_rows_with_work_packet_cut_ok"] == 1
    assert payload["n_rows_with_do_not_formalize_disjoint"] == 1
    assert payload["n_rows_with_connected_delta_nodes"] == 1
    assert payload["n_rows_with_minimal_delta_cost_graph"] == 1
    assert payload["n_rows_with_cost_graph_selection_ok"] == 1
    assert payload["n_minimal_delta_route_options"] == 2
    assert payload["n_minimal_delta_rejected_route_options"] == 1
    assert payload["n_dominated_route_witnesses"] == 0
    assert payload["n_minimal_delta_decision_rows"] == payload["n_plan_rows"]
    assert (
        payload["n_minimal_delta_decision_row_schema_valid"]
        == payload["n_minimal_delta_decision_rows"]
    )
    assert payload["n_minimal_delta_decision_row_schema_invalid"] == 0
    assert (
        payload["minimal_delta_decision_row_schema"]["$id"]
        == "urn:ai-statistician:schemas:formalization-gap-planner-minimal-delta-decision-row:1"
    )
    decision_row = payload["minimal_delta_decision_rows"][0]
    assert decision_row["dominance_status"] == (
        "NON_DOMINATED_UNDER_CURRENT_STRUCTURAL_PROXY"
    )
    assert decision_row["has_minimal_delta_and_or_cost_graph"]
    assert decision_row["minimal_delta_route_option_count"] == 2
    assert decision_row["minimal_delta_selected_route_option_id"] == (
        "route_option:reuse_bridge"
    )
    assert decision_row["minimal_delta_selected_route_cost"] == 4
    assert decision_row["cost_graph_selection_ok"]
    assert len(decision_row["minimal_delta_rejected_route_options"]) == 1
    assert (
        decision_row["minimal_delta_rejected_route_options"][0]["route_option_id"]
        == "route_option:source_port"
    )
    bad_row = dict(decision_row)
    bad_row.pop("route_cost_breakdown")
    assert validate_minimal_delta_decision_row(
        bad_row,
        minimal_delta_decision_row_json_schema(),
    )
    assert "not theorem proof evidence" in payload["proof_evidence_boundary"]
    assert (
        audit_dir / "formalization_gap_planner_minimal_delta_audit_manifest.json"
    ).exists()
    assert (
        audit_dir / "formalization_gap_planner_minimal_delta_audit.jsonl"
    ).exists()
    assert (
        audit_dir / "formalization_gap_planner_minimal_delta_decisions.jsonl"
    ).exists()
    assert (
        audit_dir / "formalization_gap_planner_minimal_delta_decision_row.schema.json"
    ).exists()
    assert (
        audit_dir / "formalization_gap_planner_minimal_delta_audit.md"
    ).exists()


def test_minimal_delta_audit_rejects_cost_formula_drift() -> None:
    root = Path("runs/test_formalization_gap_planner_minimal_delta_audit_rejects")
    input_json = root / "standalone_input.json"
    plan_dir = root / "plan"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json.write_text(
        json.dumps(
            {
                "library_snapshot_ref": "mathlib4:minimal-delta",
                "routes": [
                    {
                        "display_name": "demo_broken_cost",
                        "primitives": [
                            {
                                "primitive": "demo_bridge",
                                "coverage_status": "bridge_needed",
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
    manifest_path = plan_dir / "goal_conditioned_minimal_formalization_plan_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["rows"][0]["route_cost_breakdown"]["final_goal_conditioned_cost"] += 1
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    payload = audit_formalization_gap_planner_minimal_delta(plan_dir)

    assert not payload["all_ok"]
    failed = [row for row in payload["checks"] if not row["ok"]]
    assert any(row["check_name"].endswith(":cost_formula") for row in failed)


def test_minimal_delta_audit_rejects_nonminimal_selected_cost_graph_option() -> None:
    root = Path("runs/test_formalization_gap_planner_minimal_delta_audit_cost_graph_rejects")
    input_json = root / "standalone_input.json"
    plan_dir = root / "plan"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json.write_text(
        json.dumps(
            {
                "library_snapshot_ref": "mathlib4:minimal-delta",
                "routes": [
                    {
                        "display_name": "demo_nonminimal_graph_selection",
                        "minimal_delta_plan": {
                            "selected_primitives": ["expensive_bridge"],
                            "cost_model_version": (
                                "formalization_gap_planner_minimal_delta_cost_policy:1"
                            ),
                            "route_cost": 10,
                            "primitive_costs": [
                                {
                                    "primitive": "expensive_bridge",
                                    "base_cost": 10,
                                    "proof_difficulty_cost": 0,
                                    "import_cone_cost": 0,
                                    "definition_or_typeclass_cost": 0,
                                    "semantic_risk_cost": 0,
                                    "reuse_credit": 0,
                                    "total_cost": 10,
                                    "cost_rationale": "incorrectly selected route",
                                }
                            ],
                            "and_or_cost_graph": {
                                "graph_kind": "AND_OR_ROUTE_COST_GRAPH",
                                "selected_route_option_id": "route_option:expensive",
                                "route_options": [
                                    {
                                        "route_option_id": "route_option:expensive",
                                        "selected": True,
                                        "selected_primitives": ["expensive_bridge"],
                                        "route_cost": 10,
                                        "cost_rationale": "not actually cheapest",
                                    },
                                    {
                                        "route_option_id": "route_option:cheap",
                                        "selected": False,
                                        "selected_primitives": ["cheap_wrapper"],
                                        "route_cost": 3,
                                        "cost_rationale": "cheaper alternative",
                                    },
                                ],
                                "or_nodes": [
                                    {
                                        "node_id": "choice",
                                        "choices": [
                                            "route_option:expensive",
                                            "route_option:cheap",
                                        ],
                                        "selection_rationale": "bad choice",
                                    }
                                ],
                                "and_edges": [
                                    {
                                        "route_option_id": "route_option:expensive",
                                        "requires": ["expensive_bridge"],
                                    },
                                    {
                                        "route_option_id": "route_option:cheap",
                                        "requires": ["cheap_wrapper"],
                                    },
                                ],
                            },
                            "minimality_rationale": "This graph should be rejected.",
                        },
                        "primitives": [
                            {
                                "primitive": "expensive_bridge",
                                "coverage_status": "bridge_needed",
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

    payload = audit_formalization_gap_planner_minimal_delta(plan_dir)

    assert not payload["all_ok"]
    assert payload["n_rows_with_cost_graph_selection_ok"] == 0
    failed = [row for row in payload["checks"] if not row["ok"]]
    assert any(
        row["check_name"].endswith(":cost_graph_selected_route_minimal")
        for row in failed
    )
    decision_row = payload["minimal_delta_decision_rows"][0]
    assert decision_row["has_minimal_delta_and_or_cost_graph"]
    assert not decision_row["cost_graph_selection_ok"]
    assert decision_row["minimal_delta_rejected_route_options"][0]["route_cost"] == 3
