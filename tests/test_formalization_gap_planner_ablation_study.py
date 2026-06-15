from __future__ import annotations

import json
import shutil
from pathlib import Path

from ai_statistician.formalization_gap_planner_ablation_study import (
    ablation_study_row_json_schema,
    export_formalization_gap_planner_ablation_study,
    validate_ablation_study_row,
)


def test_ablation_study_compares_literature_lean_feedback_and_null_baselines() -> None:
    root = Path("runs/test_formalization_gap_planner_ablation_study")
    plan_dir = root / "plan"
    evaluation_dir = root / "evaluation"
    session_dir = root / "session"
    out_dir = root / "ablation"
    shutil.rmtree(root, ignore_errors=True)
    plan_dir.mkdir(parents=True, exist_ok=True)
    evaluation_dir.mkdir(parents=True, exist_ok=True)
    session_dir.mkdir(parents=True, exist_ok=True)

    plan_rows = [
        {
            "goal_plan_id": "goal:split_conformal",
            "route_id": "route:split_conformal",
            "display_name": "split conformal coverage",
            "existing_reuse_nodes": [
                {
                    "primitive": "exchangeability",
                    "coverage_status": "exact_exists",
                    "candidate_declarations": ["Probability.exchangeable"],
                }
            ],
            "formal_realization_dag_nodes": [
                {
                    "node_id": "formal:rank_uniformity",
                    "primitive": "rank_uniformity",
                    "coverage_status": "exact_exists",
                    "candidate_declarations": ["GenericRank.uniformity"],
                }
            ],
            "minimal_additional_formalization_nodes": [
                {
                    "primitive": "rank_uniformity",
                    "action_class": "bridge_needed",
                    "source_refs": ["Lei-Wasserman#rank"],
                },
                {
                    "primitive": "finite_sample_quantile",
                    "action_class": "source_port_needed",
                    "source_refs": ["Lei-Wasserman#quantile"],
                },
            ],
        }
    ]
    (plan_dir / "goal_conditioned_minimal_formalization_plan_manifest.json").write_text(
        json.dumps(
            {
                "component_name": "library_aware_formalization_gap_planner",
                "portable_schema_id": "urn:ai-statistician:schemas:library-aware-formalization-gap-plan:1",
                "rows": plan_rows,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    evaluation_rows = [
        {
            "goal_plan_id": "goal:split_conformal",
            "route_id": "route:split_conformal",
            "display_name": "split conformal coverage",
            "matched_ground_truth": True,
            "predicted_route_primitives": [
                "exchangeability",
                "rank_uniformity",
                "finite_sample_quantile",
            ],
            "ground_truth_route_primitives": [
                "exchangeability",
                "rank_uniformity",
                "finite_sample_quantile",
            ],
            "predicted_delta_primitives": [
                "rank_uniformity",
                "finite_sample_quantile",
            ],
            "ground_truth_delta_primitives": [
                "rank_uniformity",
                "finite_sample_quantile",
            ],
            "predicted_residual_primitives": ["rank_uniformity"],
            "ground_truth_residual_primitives": ["rank_uniformity"],
            "predicted_existing_reuse_primitives": ["exchangeability"],
            "ground_truth_existing_reuse_primitives": ["exchangeability"],
            "coverage_classification_accuracy": 1.0,
            "feedback_loop_ready": True,
            "minimal_delta_cost_graph_present": False,
            "minimal_delta_route_option_count": 0,
            "minimal_delta_selected_route_option_id": "",
            "minimal_delta_selected_route_cost": 0.0,
            "realization_coverage_witness_present": False,
            "realization_coverage_complete": False,
            "realization_missing_selected_formal_primitives": [],
            "realization_missing_delta_alignment_primitives": [],
            "llm_route_planner_trace_present": True,
            "llm_route_planner_route_adoption_status": (
                "READY_FOR_STANDALONE_REPLAY"
            ),
            "llm_route_planner_route_adoption_blockers": [],
        }
    ]
    (evaluation_dir / "formalization_gap_planner_evaluation_manifest.json").write_text(
        json.dumps(
            {
                "component_name": "formalization_gap_planner_evaluation",
                "rows": evaluation_rows,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    (session_dir / "formalization_gap_planner_interactive_session_manifest.json").write_text(
        json.dumps(
            {
                "component_name": "formalization_gap_planner_interactive_session",
                "rows": [
                    {
                        "goal_plan_id": "goal:split_conformal",
                        "route_id": "route:split_conformal",
                        "display_name": "split conformal coverage",
                        "next_interaction_kind": "route_replan",
                        "residual_goals": ["rank_uniformity: missing order-statistic side condition"],
                        "route_revision_reasons": [
                            "proof-state residual exposed order-statistic side condition"
                        ],
                    }
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    payload = export_formalization_gap_planner_ablation_study(
        plan_dir,
        evaluation_dir,
        out_dir,
        formalization_gap_planner_interactive_session_dir=session_dir,
    )

    assert payload["all_ok"]
    assert payload["n_ablation_variants"] == 5
    assert payload["n_row_schema_valid"] == payload["n_ablation_variants"]
    assert payload["n_row_schema_invalid"] == 0
    assert payload["ablation_study_row_schema"]["$id"] == (
        "urn:ai-statistician:schemas:formalization-gap-planner-ablation-study-row:1"
    )
    by_variant = {row["ablation_variant"]: row for row in payload["rows"]}
    assert by_variant["full_planner_observed"]["mean_route_recall"] == 1.0
    assert by_variant["full_planner_observed"]["route_adoption_ready_rate"] == 1.0
    assert (
        by_variant["full_planner_observed"][
            "route_adoption_pending_refinement_rate"
        ]
        == 0.0
    )
    assert by_variant["full_planner_observed"]["mean_route_adoption_blockers"] == 0.0
    assert (
        by_variant["full_planner_observed"][
            "mean_route_adoption_precondition_known_blockers"
        ]
        == 0.0
    )
    assert (
        by_variant["full_planner_observed"][
            "mean_route_adoption_precondition_required_response_fields"
        ]
        == 0.0
    )
    assert (
        by_variant["full_planner_observed"][
            "mean_route_adoption_pending_quality_control_blockers"
        ]
        == 0.0
    )
    assert (
        by_variant["full_planner_observed"][
            "mean_route_adoption_pending_source_grounding_blockers"
        ]
        == 0.0
    )
    assert by_variant["no_literature_evidence"]["mean_route_recall"] < 1.0
    assert by_variant["no_literature_evidence"]["n_impacted_primitives"] == 2
    assert by_variant["no_literature_evidence"]["route_adoption_ready_rate"] == 0.0
    assert (
        by_variant["no_literature_evidence"][
            "route_adoption_pending_refinement_rate"
        ]
        == 1.0
    )
    assert by_variant["no_literature_evidence"]["mean_route_adoption_blockers"] == 1.0
    assert (
        by_variant["no_literature_evidence"][
            "mean_route_adoption_pending_quality_control_blockers"
        ]
        == 0.0
    )
    assert (
        by_variant["no_literature_evidence"][
            "mean_route_adoption_pending_source_grounding_blockers"
        ]
        == 0.0
    )
    assert (
        by_variant["no_literature_evidence"][
            "relative_route_adoption_ready_drop"
        ]
        == 1.0
    )
    assert by_variant["no_formal_grounding"]["mean_existing_reuse_recall"] == 0.0
    assert by_variant["no_formal_grounding"]["n_impacted_primitives"] == 2
    assert "rank_uniformity" in by_variant["no_formal_grounding"]["impacted_primitives"]
    assert by_variant["no_formal_grounding"]["route_adoption_ready_rate"] == 0.0
    assert by_variant["full_planner_observed"]["mean_residual_recall"] == 1.0
    assert by_variant["no_proof_state_feedback"]["feedback_loop_readiness"] == 0.0
    assert by_variant["no_proof_state_feedback"]["next_action_replan_rate"] == 0.0
    assert by_variant["no_proof_state_feedback"]["mean_residual_recall"] == 0.0
    assert by_variant["no_proof_state_feedback"]["route_adoption_ready_rate"] == 0.0
    assert (
        by_variant["no_proof_state_feedback"][
            "route_adoption_pending_refinement_rate"
        ]
        == 1.0
    )
    assert (
        payload["largest_residual_recall_drop_variant"]
        == "no_proof_state_feedback"
    )
    assert (
        payload["largest_route_adoption_ready_drop_variant"]
        == "no_literature_evidence"
    )
    assert by_variant["no_route_planner"]["mean_route_recall"] == 0.0
    assert by_variant["no_route_planner"]["route_adoption_ready_rate"] == 0.0
    assert (
        by_variant["no_route_planner"][
            "mean_route_adoption_precondition_known_blockers"
        ]
        == 0.0
    )
    assert (
        by_variant["no_route_planner"][
            "mean_route_adoption_precondition_required_response_fields"
        ]
        == 0.0
    )
    assert (
        by_variant["no_route_planner"]["relative_route_adoption_ready_drop"]
        == 1.0
    )
    assert any("no_formal_grounding" in item for item in payload["limitations"])
    assert not any("no_lean" in item for item in payload["limitations"])
    assert "not theorem proof evidence" in payload["proof_evidence_boundary"]
    assert (
        out_dir / "formalization_gap_planner_ablation_study_manifest.json"
    ).exists()
    assert (out_dir / "formalization_gap_planner_ablation_study.jsonl").exists()
    assert (
        out_dir / "formalization_gap_planner_ablation_study_row.schema.json"
    ).exists()
    assert "ablation_variant required" in validate_ablation_study_row(
        {"schema_version": 1},
        ablation_study_row_json_schema(),
    )


def test_ablation_study_tracks_quality_control_route_adoption_blockers() -> None:
    root = Path("runs/test_formalization_gap_planner_ablation_study_quality_blockers")
    plan_dir = root / "plan"
    evaluation_dir = root / "evaluation"
    out_dir = root / "ablation"
    shutil.rmtree(root, ignore_errors=True)
    plan_dir.mkdir(parents=True, exist_ok=True)
    evaluation_dir.mkdir(parents=True, exist_ok=True)
    (plan_dir / "goal_conditioned_minimal_formalization_plan_manifest.json").write_text(
        json.dumps(
            {
                "component_name": "library_aware_formalization_gap_planner",
                "portable_schema_id": "urn:ai-statistician:schemas:library-aware-formalization-gap-plan:1",
                "rows": [
                    {
                        "goal_plan_id": "goal:qc",
                        "route_id": "route:qc",
                        "display_name": "quality-control blocked route",
                        "formal_realization_dag_nodes": [
                            {
                                "primitive": "rank_uniformity",
                                "coverage_status": "bridge_needed",
                            }
                        ],
                        "minimal_additional_formalization_nodes": [
                            {
                                "primitive": "rank_uniformity",
                                "action_class": "bridge_needed",
                            }
                        ],
                    }
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    (evaluation_dir / "formalization_gap_planner_evaluation_manifest.json").write_text(
        json.dumps(
            {
                "component_name": "formalization_gap_planner_evaluation",
                "rows": [
                    {
                        "goal_plan_id": "goal:qc",
                        "route_id": "route:qc",
                        "display_name": "quality-control blocked route",
                        "matched_ground_truth": True,
                        "predicted_route_primitives": ["rank_uniformity"],
                        "ground_truth_route_primitives": ["rank_uniformity"],
                        "predicted_delta_primitives": ["rank_uniformity"],
                        "ground_truth_delta_primitives": ["rank_uniformity"],
                        "predicted_residual_primitives": [],
                        "ground_truth_residual_primitives": [],
                        "predicted_existing_reuse_primitives": [],
                        "ground_truth_existing_reuse_primitives": [],
                        "coverage_classification_accuracy": 1.0,
                        "feedback_loop_ready": False,
                        "llm_route_planner_trace_present": True,
                        "llm_route_planner_route_adoption_status": (
                            "PENDING_REFINEMENT_BEFORE_ROUTE_ADOPTION"
                        ),
                        "llm_route_planner_route_adoption_blockers": [
                            "quality_control_obligations_pending"
                        ],
                        "llm_route_planner_route_adoption_preconditions": {
                            "precondition_kind": (
                                "formalization_gap_planner_llm_route_planner_route_adoption_preconditions"
                            ),
                            "blocked_before_response": True,
                            "known_pre_response_blockers": [
                                "quality_control_obligations_pending"
                            ],
                            "n_known_pre_response_blockers": 1,
                            "response_required_fields": [
                                "search_requests",
                                "planner_next_actions",
                            ],
                            "n_response_required_fields": 2,
                        },
                        "llm_route_planner_route_adoption_precondition_present": True,
                        "llm_route_planner_route_adoption_precondition_blocked_before_response": True,
                        "llm_route_planner_route_adoption_precondition_known_blockers": [
                            "quality_control_obligations_pending"
                        ],
                        "llm_route_planner_route_adoption_precondition_required_response_fields": [
                            "planner_next_actions",
                            "search_requests",
                        ],
                        "llm_route_planner_route_adoption_precondition_known_blocker_count": 1,
                        "llm_route_planner_route_adoption_precondition_required_response_field_count": 2,
                    }
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    payload = export_formalization_gap_planner_ablation_study(
        plan_dir,
        evaluation_dir,
        out_dir,
    )

    assert payload["all_ok"]
    by_variant = {row["ablation_variant"]: row for row in payload["rows"]}
    full = by_variant["full_planner_observed"]
    assert full["route_adoption_ready_rate"] == 0.0
    assert full["route_adoption_pending_refinement_rate"] == 1.0
    assert full["mean_route_adoption_blockers"] == 1.0
    assert (
        full["mean_route_adoption_pending_quality_control_blockers"]
        == 1.0
    )
    assert (
        full["mean_route_adoption_pending_source_grounding_blockers"]
        == 0.0
    )
    assert full["mean_route_adoption_precondition_known_blockers"] == 1.0
    assert (
        full["mean_route_adoption_precondition_required_response_fields"]
        == 2.0
    )
    assert (
        by_variant["no_route_planner"][
            "mean_route_adoption_precondition_known_blockers"
        ]
        == 0.0
    )
    assert (
        by_variant["no_route_planner"][
            "mean_route_adoption_precondition_required_response_fields"
        ]
        == 0.0
    )
    assert all(
        row["mean_route_adoption_pending_quality_control_blockers"] == 1.0
        for row in payload["rows"]
    )
    assert all(
        row["mean_route_adoption_pending_source_grounding_blockers"] == 0.0
        for row in payload["rows"]
    )
