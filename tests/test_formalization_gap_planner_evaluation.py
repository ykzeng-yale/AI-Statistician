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
from ai_statistician.formalization_gap_planner_llm_route_planner import (
    ROUTE_ADOPTION_BLOCKER_VALUES,
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
                        "kernel_verified": True,
                        "kernel_verification_witnesses": [
                            {
                                "target_prover_family": "lean4",
                                "verification_status": "kernel_verified",
                                "artifact_refs": ["Proofs/AlignmentFixture.lean"],
                                "declaration_names": ["AlignmentFixture.rank_bridge"],
                                "proof_hash": "sha256:alignment-fixture",
                                "checker": "lake build",
                                "no_sorry_or_admit": True,
                            }
                        ],
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
    for row in manifest["rows"]:
        row.pop("lean_realization_dag_nodes", None)
        trace = row.setdefault("standalone_input_trace", {})
        trace["llm_route_planner_row_id"] = "llm-route-row:alignment"
        trace["llm_route_planner_model_tier"] = "sonnet"
        trace["llm_route_planner_residual_goal_contexts"] = [
            {
                "source_kind": "lean_lsp_proof_state_feedback",
                "residual_goal": (
                    "rank_bridge: missing order-statistic side condition"
                ),
                "target_primitives": ["rank_bridge"],
                "source_refs": ["fixture#coverage"],
                "source_snippets": [
                    {
                        "source_ref": "fixture#coverage",
                        "quote": "rank bridge requires the side condition",
                    }
                ],
                "evidence_ids": ["evidence:rank-bridge-side-condition"],
                "resource_response_ledger_id": "ledger:rank-bridge",
                "resource_request_id": "request:rank-bridge",
                "prover_diagnostic_signature": (
                    "prover_diagnostic_signature:rank-bridge"
                ),
            }
        ]
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    payload = evaluate_formalization_gap_planner(plan_dir, truth_json, out_dir)

    assert payload["all_ok"]
    assert payload["n_alignment_contract_ok"] == payload["n_evaluation_rows"] == 1
    assert payload["n_plan_rows_with_formal_realization_dag_nodes"] == 1
    assert payload["n_plan_rows_with_legacy_lean_realization_dag_nodes"] == 0
    assert payload["n_formal_realization_dag_nodes"] >= 1
    assert payload["n_legacy_lean_realization_dag_nodes"] == 0
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
    assert payload["n_kernel_verified_ground_truth"] == 1
    assert payload["n_kernel_verification_witnesses"] == 1
    assert payload["n_kernel_verified_ground_truth_with_witnesses"] == 1
    assert payload["n_rows_with_llm_route_planner_residual_goal_contexts"] == 1
    assert payload["n_llm_route_planner_residual_goal_contexts"] == 1
    assert payload["n_llm_route_planner_residual_goal_context_source_refs"] == 1
    assert (
        payload["n_llm_route_planner_residual_goal_context_provenance_values"]
        == 4
    )
    assert payload["n_llm_route_planner_residual_goals_with_context"] == 1
    assert payload["n_llm_route_planner_residual_goals_without_context"] == 0
    row = payload["rows"][0]
    assert row["alignment_contract_ok"]
    assert not validate_evaluation_row(row)
    broken_row = dict(row)
    broken_row.pop("proof_evidence_boundary")
    assert "proof_evidence_boundary required" in validate_evaluation_row(broken_row)
    broken_context_row = dict(row)
    broken_context_row.pop("llm_route_planner_residual_goal_context_count")
    assert (
        "llm_route_planner_residual_goal_context_count required"
        in validate_evaluation_row(broken_context_row)
    )
    assert row["alignment_coverage"] == 1.0
    assert set(row["aligned_primitives"]) == set(row["predicted_route_primitives"])
    assert row["predicted_residual_primitives"] == ("rank_bridge",)
    assert row["ground_truth_residual_primitives"] == ("rank_bridge",)
    assert row["residual_true_positive_primitives"] == ("rank_bridge",)
    assert row["residual_precision"] == 1.0
    assert row["residual_recall"] == 1.0
    assert row["kernel_verified_ground_truth"] is True
    assert row["kernel_verification_witnesses"][0]["proof_hash"] == (
        "sha256:alignment-fixture"
    )
    assert row["predicted_residual_goals"] == (
        "rank_bridge: missing order-statistic side condition",
    )
    assert row["llm_route_planner_residual_goal_context_count"] == 1
    assert row["llm_route_planner_residual_goal_context_residual_goals"] == (
        "rank_bridge: missing order-statistic side condition",
    )
    assert row["llm_route_planner_residual_goal_context_source_ref_count"] == 1
    assert row["llm_route_planner_residual_goal_context_provenance_count"] == 4
    assert row["llm_route_planner_residual_goals_with_context_count"] == 1
    assert row["llm_route_planner_residual_goals_without_context"] == ()
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
    report = (
        out_dir / "formalization_gap_planner_evaluation.md"
    ).read_text(encoding="utf-8")
    assert "Kernel verification witnesses: 1" in report
    assert "LLM residual-goal contexts rows/contexts/source-refs/provenance/without-context: 1/1/1/4/0" in report


def test_evaluation_rejects_non_lean_legacy_lean_realization_alias() -> None:
    root = Path("runs/test_formalization_gap_planner_evaluation_rejects_lean_alias")
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
                "target_prover_family": "rocq",
                "library_snapshot_ref": "rocq_alignment_fixture",
                "routes": [
                    {
                        "route_id": "route:rocq_alias_fixture",
                        "display_name": "rocq alias fixture theorem",
                        "theorem_statement": "A rank bound follows from exchangeability.",
                        "primitives": [
                            {
                                "primitive": "exchangeability",
                                "coverage_status": "exact_exists",
                                "candidate_declarations": [
                                    "Probability.Exchangeable"
                                ],
                            },
                            {
                                "primitive": "rank_bound",
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
                        "route_id": "route:rocq_alias_fixture",
                        "required_primitives": ["exchangeability", "rank_bound"],
                        "actual_existing_reuse_primitives": ["exchangeability"],
                        "actual_delta_primitives": ["rank_bound"],
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
    row = manifest["rows"][0]
    row["lean_realization_dag_nodes"] = list(row["formal_realization_dag_nodes"])
    row["lean_realization_dag_edges"] = list(row["formal_realization_dag_edges"])
    row["formal_realization_dag_nodes"] = []
    row["formal_realization_dag_edges"] = []
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    payload = evaluate_formalization_gap_planner(plan_dir, truth_json, out_dir)

    assert not payload["all_ok"]
    assert payload["n_plan_rows_with_formal_realization_dag_nodes"] == 0
    assert payload["n_plan_rows_with_legacy_lean_realization_dag_nodes"] == 1
    assert payload["n_formal_realization_dag_nodes"] == 0
    assert payload["n_legacy_lean_realization_dag_nodes"] >= 1
    assert payload["n_alignment_contract_ok"] == 0
    assert payload["mean_alignment_coverage"] == 0.0
    row = payload["rows"][0]
    assert row["two_dag_contract_ok"] is False
    assert row["alignment_contract_ok"] is False
    assert row["alignment_coverage"] == 0.0
    assert set(row["unaligned_primitives"]) == {"exchangeability", "rank_bound"}
    assert "two-DAG contract is incomplete" in row["errors"]
    assert "route alignment contract is incomplete" in row["errors"]


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
    route_option_selection_brief = {
        "schema_version": 1,
        "brief_kind": (
            "formalization_gap_planner_llm_route_planner_route_option_selection_brief"
        ),
        "route_id": "rank_route",
        "display_name": "rank_route",
        "target_prover_family": "lean4",
        "library_snapshot_ref": "mathlib4:evaluation-cost-graph",
        "cost_policy_id": "minimal_delta_route_cost_v1",
        "selection_rule": (
            "Rank route options by minimum_route_base_cost, then residual coverage."
        ),
        "n_candidate_route_options": 2,
        "n_candidate_route_option_primitives": 4,
        "n_candidate_route_options_with_residual_goals": 1,
        "n_candidate_route_option_residual_goals": 1,
        "n_lower_bound_tied_route_options": 1,
        "lower_bound_selected_route_option_id": "route_option:bridge_rank",
        "lower_bound_selected_route_cost": 4,
        "lower_bound_selected_residual_goal_count": 1,
        "candidate_route_options": [
            {
                "route_option_id": "route_option:bridge_rank",
                "source_route_option_index": 0,
                "selection_rank": 1,
                "selected_by_lower_bound_policy": True,
                "lower_bound_tied_for_best": True,
                "selected_primitives": ["exchangeability", "rank_uniformity"],
                "n_selected_primitives": 2,
                "minimum_route_base_cost": 4,
                "n_bridge_or_harder_primitives": 1,
                "n_target_compatible_reuse_declarations": 1,
                "n_residual_goals": 1,
                "n_residual_goal_contexts": 1,
                "residual_target_primitives": ["rank_uniformity"],
                "residual_goal_samples": [
                    "rank_uniformity: missing bridge proof"
                ],
            },
            {
                "route_option_id": "route_option:source_port_rank",
                "source_route_option_index": 1,
                "selection_rank": 2,
                "selected_by_lower_bound_policy": False,
                "lower_bound_tied_for_best": False,
                "selected_primitives": ["exchangeability", "rank_uniformity"],
                "n_selected_primitives": 2,
                "minimum_route_base_cost": 7,
                "n_bridge_or_harder_primitives": 1,
                "n_target_compatible_reuse_declarations": 1,
                "n_residual_goals": 0,
                "n_residual_goal_contexts": 0,
                "residual_target_primitives": [],
                "residual_goal_samples": [],
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
        "cost_hint_baseline_primitives": ["exchangeability", "rank_uniformity"],
        "omitted_cost_hint_primitives": [],
        "cost_hint_baseline_coverage_complete": True,
        "realization_coverage_complete": True,
    }
    route_quality_controls = {
        "resource_contract_ids": ["lean_lsp:proof_state_feedback"],
        "quality_gates": ["residual_goals_source_grounded"],
    }
    metadata_quality_controls = {
        "required_quality_signals": ["diagnostic_signature"],
        "response_validation_signals": ["residual_goals_or_diagnostics_present"],
        "stop_conditions": ["residual interpreted or source search requested"],
    }
    route_adoption_preconditions = {
        "precondition_kind": (
            "formalization_gap_planner_llm_route_planner_route_adoption_preconditions"
        ),
        "blocked_before_response": True,
        "known_pre_response_blockers": [
            "quality_control_obligations_pending",
            "source_grounding_obligations_pending",
        ],
        "n_known_pre_response_blockers": 2,
        "response_required_fields": [
            "search_requests",
            "planner_next_actions",
        ],
        "n_response_required_fields": 2,
        "target_primitives": ["rank_uniformity"],
        "n_target_primitives": 1,
    }
    expected_quality_controls = {
        field_name: tuple(values)
        for field_name, values in {
            **route_quality_controls,
            **metadata_quality_controls,
        }.items()
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
                        "quality_controls": route_quality_controls,
                        "minimal_delta_and_or_cost_graph": cost_graph,
                        "realization_coverage_witness": realization_witness,
                        "replan_metadata": {
                            "quality_controls": metadata_quality_controls,
                            "llm_route_planner_row_id": "llm-route-row:rank",
                            "llm_route_planner_provider": "anthropic",
                            "llm_route_planner_model": "claude-sonnet-4-6",
                            "llm_route_planner_model_tier": "sonnet",
                            "llm_route_planner_route_adoption_status": (
                                "PENDING_REFINEMENT_BEFORE_ROUTE_ADOPTION"
                            ),
                            "llm_route_planner_route_adoption_blockers": [
                                "quality_control_obligations_pending",
                                "source_grounding_obligations_pending",
                                "search_requests_pending_evidence",
                            ],
                            "llm_route_planner_route_adoption_preconditions": (
                                route_adoption_preconditions
                            ),
                            "llm_route_planner_route_option_selection_brief": (
                                route_option_selection_brief
                            ),
                            "llm_route_planner_route_option_selected_route_option_id": (
                                "route_option:bridge_rank"
                            ),
                            "llm_route_planner_acceptance_status": (
                                "ACCEPTED_SOURCE_GROUNDED_ROUTE_PLAN"
                            ),
                            "llm_route_planner_model_selection_rationale": (
                                "auto selected Sonnet because the route needs a bridge"
                            ),
                            "llm_route_planner_model_tier_decision_evidence": {
                                "decision_basis": "auto_sonnet_triggers",
                                "selection_mode": "auto",
                                "selected_model_tier": "sonnet",
                                "effective_model_tier": "sonnet",
                                "sonnet_triggers": [
                                    (
                                        "1 source-theorem proof-body execution "
                                        "failure(s)"
                                    ),
                                    (
                                        "3 source-theorem formal-environment "
                                        "blocker(s)"
                                    ),
                                    "2 interactive formal-attempt queue item(s)",
                                    "1 interactive formal-attempt queue ready item(s)",
                                    "1 interactive formal-attempt queue blocked item(s)",
                                    (
                                        "3 interactive formal-attempt execution "
                                        "command(s)"
                                    ),
                                ],
                                "route_signal_counts": {
                                    "source_theorem_feedback_row_count": 4,
                                    "source_theorem_unverified_semantic_primitive_row_count": 2,
                                    "source_theorem_proof_body_execution_failure_count": 1,
                                    "source_theorem_formal_environment_blocker_count": 3,
                                    "interactive_session_formal_attempt_queue_row_count": 1,
                                    "interactive_session_formal_attempt_queue_item_count": 2,
                                    "interactive_session_formal_attempt_queue_ready_item_count": 1,
                                    "interactive_session_formal_attempt_queue_blocked_item_count": 1,
                                    "interactive_session_formal_attempt_queue_execution_command_count": 3,
                                },
                                "source_theorem_feedback_counts": {
                                    "total_count": 4,
                                    "unverified_semantic_primitive_row_count": 2,
                                    "proof_body_execution_failure_count": 1,
                                    "formal_environment_blocker_count": 3,
                                },
                            },
                            "llm_route_planner_generator_metadata": {
                                "generator_only": True,
                                "provider_usage": {
                                    "input_tokens": 120,
                                    "output_tokens": 34,
                                    "cache_creation_input_tokens": 5,
                                    "cache_read_input_tokens": 6,
                                },
                                "retry_count": 0,
                            },
                            "llm_route_planner_generator_metadata_keys": [
                                "generator_only",
                                "provider_usage",
                                "retry_count",
                            ],
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
    assert payload["n_rows_with_llm_route_planner_trace"] == 1
    assert payload["n_rows_with_llm_route_planner_model_tier"] == 1
    assert payload["n_rows_with_llm_route_planner_model_tier_decision_basis"] == 1
    assert payload["n_llm_route_planner_model_tier_decision_sonnet_triggers"] == 6
    assert payload["n_rows_with_llm_route_planner_source_feedback_tier_signal"] == 1
    assert payload["n_llm_route_planner_source_feedback_rows"] == 4
    assert (
        payload[
            "n_llm_route_planner_source_feedback_unverified_semantic_primitive_rows"
        ]
        == 2
    )
    assert (
        payload[
            "n_llm_route_planner_source_feedback_proof_body_execution_failures"
        ]
        == 1
    )
    assert (
        payload[
            "n_llm_route_planner_source_feedback_formal_environment_blockers"
        ]
        == 3
    )
    assert (
        payload[
            "n_rows_with_llm_route_planner_interactive_formal_attempt_queue_tier_signal"
        ]
        == 1
    )
    assert payload["n_llm_route_planner_interactive_formal_attempt_queue_rows"] == 1
    assert payload["n_llm_route_planner_interactive_formal_attempt_queue_items"] == 2
    assert (
        payload[
            "n_llm_route_planner_interactive_formal_attempt_queue_ready_items"
        ]
        == 1
    )
    assert (
        payload[
            "n_llm_route_planner_interactive_formal_attempt_queue_blocked_items"
        ]
        == 1
    )
    assert (
        payload[
            "n_llm_route_planner_interactive_formal_attempt_queue_execution_commands"
        ]
        == 3
    )
    assert payload["n_rows_with_llm_route_planner_route_option_selection_brief"] == 1
    assert payload["n_llm_route_planner_route_option_selection_candidate_options"] == 2
    assert payload["n_llm_route_planner_route_option_selection_candidate_primitives"] == 4
    assert (
        payload[
            "n_llm_route_planner_route_option_selection_candidates_with_residual_goals"
        ]
        == 1
    )
    assert (
        payload[
            "n_llm_route_planner_route_option_selection_candidate_residual_goals"
        ]
        == 1
    )
    assert (
        payload[
            "n_llm_route_planner_route_option_selection_lower_bound_residual_goals"
        ]
        == 1
    )
    assert (
        payload[
            "n_rows_with_llm_route_planner_route_option_selected_route_option"
        ]
        == 1
    )
    assert (
        payload[
            "n_llm_route_planner_route_option_selection_minimal_delta_selected_residual_goals"
        ]
        == 1
    )
    assert (
        payload[
            "n_llm_route_planner_route_option_selection_lower_bound_matches_minimal_delta"
        ]
        == 1
    )
    assert (
        payload[
            "n_llm_route_planner_route_option_selection_lower_bound_mismatches_minimal_delta"
        ]
        == 0
    )
    assert (
        payload[
            "n_llm_route_planner_route_option_selected_matches_lower_bound"
        ]
        == 1
    )
    assert (
        payload[
            "n_llm_route_planner_route_option_selected_mismatches_lower_bound"
        ]
        == 0
    )
    assert (
        payload[
            "n_llm_route_planner_route_option_selected_matches_minimal_delta"
        ]
        == 1
    )
    assert (
        payload[
            "n_llm_route_planner_route_option_selected_mismatches_minimal_delta"
        ]
        == 0
    )
    assert payload["n_rows_with_llm_route_planner_route_adoption_status"] == 1
    assert payload["n_rows_ready_for_route_adoption"] == 0
    assert payload["n_rows_pending_refinement_before_route_adoption"] == 1
    assert payload["n_rows_awaiting_llm_route_planner_response"] == 0
    assert payload["n_rows_rejected_llm_route_plan"] == 0
    assert payload["n_llm_route_adoption_blockers"] == 3
    assert payload["n_llm_route_adoption_pending_quality_control_blockers"] == 1
    assert payload["n_llm_route_adoption_pending_source_grounding_blockers"] == 1
    assert (
        payload["n_llm_route_adoption_pending_formal_attempt_queue_blockers"]
        == 0
    )
    assert (
        payload["n_rows_with_llm_route_planner_route_adoption_preconditions"] == 1
    )
    assert (
        payload[
            "n_rows_with_llm_route_planner_blocking_route_adoption_preconditions"
        ]
        == 1
    )
    assert (
        payload[
            "n_llm_route_planner_route_adoption_precondition_known_blockers"
        ]
        == 2
    )
    assert (
        payload[
            "n_llm_route_planner_route_adoption_precondition_required_response_fields"
        ]
        == 2
    )
    assert (
        payload[
            "n_llm_route_planner_route_adoption_precondition_target_primitives"
        ]
        == 1
    )
    assert payload[
        "llm_route_planner_route_adoption_precondition_known_blockers"
    ] == (
        "quality_control_obligations_pending",
        "source_grounding_obligations_pending",
    )
    assert payload[
        "llm_route_planner_route_adoption_precondition_required_response_fields"
    ] == (
        "planner_next_actions",
        "search_requests",
    )
    assert payload[
        "llm_route_planner_route_adoption_precondition_target_primitives"
    ] == ("rank_uniformity",)
    assert payload["llm_route_adoption_blockers"] == (
        "quality_control_obligations_pending",
        "search_requests_pending_evidence",
        "source_grounding_obligations_pending",
    )
    assert payload["llm_route_adoption_blocker_counts"] == {
        "quality_control_obligations_pending": 1,
        "search_requests_pending_evidence": 1,
        "source_grounding_obligations_pending": 1,
    }
    assert payload["evaluation_by_llm_route_adoption_status"] == {
        "PENDING_REFINEMENT_BEFORE_ROUTE_ADOPTION": {
            "n_rows": 1,
            "n_ok": 0,
            "n_matched_ground_truth": 1,
            "n_route_adoption_blockers": 3,
            "mean_route_recall": 1.0,
            "mean_delta_precision": 1.0,
        }
    }
    assert payload["evaluation_by_llm_route_adoption_blocker"][
        "quality_control_obligations_pending"
    ] == {
        "n_rows": 1,
        "n_blocker_occurrences": 1,
        "n_ok": 0,
        "n_matched_ground_truth": 1,
        "by_route_adoption_status": {
            "PENDING_REFINEMENT_BEFORE_ROUTE_ADOPTION": 1
        },
        "mean_route_recall": 1.0,
        "mean_delta_precision": 1.0,
    }
    assert payload["evaluation_by_llm_route_adoption_blocker"][
        "source_grounding_obligations_pending"
    ] == {
        "n_rows": 1,
        "n_blocker_occurrences": 1,
        "n_ok": 0,
        "n_matched_ground_truth": 1,
        "by_route_adoption_status": {
            "PENDING_REFINEMENT_BEFORE_ROUTE_ADOPTION": 1
        },
        "mean_route_recall": 1.0,
        "mean_delta_precision": 1.0,
    }
    assert payload["n_rows_with_llm_route_planner_generator_metadata"] == 1
    assert payload["n_rows_with_llm_route_planner_provider_usage"] == 1
    assert payload["total_llm_route_planner_provider_input_tokens"] == 120
    assert payload["total_llm_route_planner_provider_output_tokens"] == 34
    assert payload[
        "total_llm_route_planner_provider_cache_creation_input_tokens"
    ] == 5
    assert payload["total_llm_route_planner_provider_cache_read_input_tokens"] == 6
    assert payload["total_llm_route_planner_provider_total_tokens"] == 165
    assert payload["llm_route_planner_provider_usage_summary"]["row_count"] == 1
    assert payload["llm_route_planner_provider_usage_summary"]["by_provider"][
        "anthropic"
    ]["total_tokens"] == 165
    assert payload["llm_route_planner_provider_usage_summary"]["by_model_tier"][
        "sonnet"
    ]["input_tokens"] == 120
    assert payload["llm_route_planner_provider_usage_summary"]["by_model"][
        "claude-sonnet-4-6"
    ]["output_tokens"] == 34
    assert payload["llm_route_planner_provider_usage_rows"][0][
        "proof_evidence_status"
    ] == "FORMALIZATION_GAP_PLANNER_EVALUATION_NOT_PROOF_EVIDENCE"
    assert payload["n_rows_with_llm_route_planner_request_contract_blocked"] == 0
    assert payload["n_rows_with_llm_route_planner_errors"] == 0
    assert payload["n_llm_route_planner_errors"] == 0
    assert payload["n_llm_route_planner_generation_errors"] == 0
    assert payload["evaluation_by_llm_model_tier"] == {
        "sonnet": {
            "n_rows": 1,
            "n_ok": 0,
            "n_matched_ground_truth": 1,
            "mean_route_recall": 1.0,
            "mean_delta_precision": 1.0,
            "mean_alignment_coverage": 1.0,
            "n_rows_with_generator_metadata": 1,
            "n_rows_with_provider_usage": 1,
            "provider_input_tokens": 120,
            "provider_output_tokens": 34,
            "provider_cache_creation_input_tokens": 5,
            "provider_cache_read_input_tokens": 6,
            "provider_total_tokens": 165,
            "n_rows_with_request_contract_blocked": 0,
            "n_rows_with_errors": 0,
            "n_sonnet_triggers": 6,
            "n_source_feedback_rows": 4,
            "n_source_feedback_proof_body_execution_failures": 1,
            "n_source_feedback_formal_environment_blockers": 3,
            "n_interactive_formal_attempt_queue_rows": 1,
            "n_interactive_formal_attempt_queue_items": 2,
            "n_interactive_formal_attempt_queue_ready_items": 1,
            "n_interactive_formal_attempt_queue_blocked_items": 1,
            "n_interactive_formal_attempt_queue_execution_commands": 3,
            "n_rows_with_route_option_selection_brief": 1,
            "n_route_option_selection_candidate_options": 2,
            "n_route_option_selection_candidate_primitives": 4,
            "n_route_option_selection_candidates_with_residual_goals": 1,
            "n_route_option_selection_candidate_residual_goals": 1,
            "n_route_option_selection_lower_bound_residual_goals": 1,
            "n_rows_with_route_option_selected_route_option": 1,
            "n_route_option_selection_minimal_delta_selected_residual_goals": 1,
            "n_route_option_selection_lower_bound_matches_minimal_delta": 1,
            "n_route_option_selection_lower_bound_mismatches_minimal_delta": 0,
            "n_route_option_selected_matches_lower_bound": 1,
            "n_route_option_selected_mismatches_lower_bound": 0,
            "n_route_option_selected_matches_minimal_delta": 1,
            "n_route_option_selected_mismatches_minimal_delta": 0,
        }
    }
    assert payload["evaluation_by_llm_model_tier_decision_basis"] == {
        "auto_sonnet_triggers": {
            "n_rows": 1,
            "n_ok": 0,
            "n_matched_ground_truth": 1,
            "by_model_tier": {"sonnet": 1},
            "n_sonnet_triggers": 6,
            "n_source_feedback_rows": 4,
            "n_source_feedback_proof_body_execution_failures": 1,
            "n_source_feedback_formal_environment_blockers": 3,
            "n_interactive_formal_attempt_queue_rows": 1,
            "n_interactive_formal_attempt_queue_items": 2,
            "n_interactive_formal_attempt_queue_ready_items": 1,
            "n_interactive_formal_attempt_queue_blocked_items": 1,
            "n_interactive_formal_attempt_queue_execution_commands": 3,
            "n_rows_with_provider_usage": 1,
            "provider_input_tokens": 120,
            "provider_output_tokens": 34,
            "provider_cache_creation_input_tokens": 5,
            "provider_cache_read_input_tokens": 6,
            "provider_total_tokens": 165,
            "mean_route_recall": 1.0,
            "mean_delta_precision": 1.0,
            "n_rows_with_route_option_selection_brief": 1,
            "n_route_option_selection_candidate_options": 2,
            "n_route_option_selection_candidate_primitives": 4,
            "n_route_option_selection_candidates_with_residual_goals": 1,
            "n_route_option_selection_candidate_residual_goals": 1,
            "n_route_option_selection_lower_bound_residual_goals": 1,
            "n_rows_with_route_option_selected_route_option": 1,
            "n_route_option_selection_minimal_delta_selected_residual_goals": 1,
            "n_route_option_selection_lower_bound_matches_minimal_delta": 1,
            "n_route_option_selection_lower_bound_mismatches_minimal_delta": 0,
            "n_route_option_selected_matches_lower_bound": 1,
            "n_route_option_selected_mismatches_lower_bound": 0,
            "n_route_option_selected_matches_minimal_delta": 1,
            "n_route_option_selected_mismatches_minimal_delta": 0,
        }
    }
    assert payload["n_rows_with_quality_controls"] == 1
    assert payload["n_quality_control_fields"] == 5
    assert payload["quality_control_fields"] == (
        "quality_gates",
        "required_quality_signals",
        "resource_contract_ids",
        "response_validation_signals",
        "stop_conditions",
    )
    assert payload["quality_control_resource_contract_ids"] == (
        "lean_lsp:proof_state_feedback",
    )
    assert payload["quality_control_response_validation_signals"] == (
        "residual_goals_or_diagnostics_present",
    )
    assert payload["quality_control_stop_conditions"] == (
        "residual interpreted or source search requested",
    )
    assert payload["evaluation_by_quality_control_field"]["resource_contract_ids"] == {
        "n_rows": 1,
        "n_values": 1,
        "values": ("lean_lsp:proof_state_feedback",),
    }
    assert payload["n_realization_missing_selected_formal_primitives"] == 0
    assert payload["n_realization_missing_delta_alignment_primitives"] == 0
    assert payload["realization_missing_selected_formal_primitives"] == ()
    assert payload["realization_missing_delta_alignment_primitives"] == ()
    assert payload["n_rows_with_incomplete_cost_hint_baseline_coverage"] == 0
    assert payload["n_realization_cost_hint_baseline_primitives"] == 2
    assert payload["realization_cost_hint_baseline_primitives"] == (
        "exchangeability",
        "rank_uniformity",
    )
    assert payload["n_realization_omitted_cost_hint_primitives"] == 0
    assert payload["realization_omitted_cost_hint_primitives"] == ()
    assert payload["realization_missing_primitives_by_route"] == ()
    assert payload["n_minimal_delta_route_options"] == 2
    assert payload["mean_minimal_delta_selected_route_cost"] == 4.0
    row = payload["rows"][0]
    assert row["minimal_delta_cost_graph_present"] is True
    assert row["minimal_delta_route_option_count"] == 2
    assert row["minimal_delta_selected_route_option_id"] == "route_option:bridge_rank"
    assert row["minimal_delta_selected_route_cost"] == 4.0
    assert row["llm_route_planner_route_option_selection_brief_present"] is True
    assert row["llm_route_planner_route_option_selection_candidate_count"] == 2
    assert (
        row["llm_route_planner_route_option_selection_candidate_primitive_count"]
        == 4
    )
    assert (
        row[
            "llm_route_planner_route_option_selection_candidates_with_residual_goals"
        ]
        == 1
    )
    assert (
        row[
            "llm_route_planner_route_option_selection_candidate_residual_goal_count"
        ]
        == 1
    )
    assert (
        row[
            "llm_route_planner_route_option_selection_lower_bound_selected_route_option_id"
        ]
        == "route_option:bridge_rank"
    )
    assert (
        row["llm_route_planner_route_option_selected_route_option_id"]
        == "route_option:bridge_rank"
    )
    assert (
        row[
            "llm_route_planner_route_option_selection_lower_bound_residual_goal_count"
        ]
        == 1
    )
    assert (
        row[
            "llm_route_planner_route_option_selection_minimal_delta_selected_residual_goal_count"
        ]
        == 1
    )
    assert (
        row[
            "llm_route_planner_route_option_selection_lower_bound_matches_minimal_delta"
        ]
        is True
    )
    assert row["llm_route_planner_route_option_selected_matches_lower_bound"] is True
    assert (
        row["llm_route_planner_route_option_selected_matches_minimal_delta"]
        is True
    )
    assert row["realization_coverage_witness_present"] is True
    assert row["realization_coverage_complete"] is True
    assert row["realization_missing_selected_formal_primitives"] == ()
    assert row["realization_missing_delta_alignment_primitives"] == ()
    assert row["realization_cost_hint_baseline_primitives"] == (
        "exchangeability",
        "rank_uniformity",
    )
    assert row["realization_omitted_cost_hint_primitives"] == ()
    assert row["realization_cost_hint_baseline_coverage_complete"] is True
    assert row["llm_route_planner_trace_present"] is True
    assert row["llm_route_planner_row_id"] == "llm-route-row:rank"
    assert row["llm_route_planner_provider"] == "anthropic"
    assert row["llm_route_planner_model"] == "claude-sonnet-4-6"
    assert row["llm_route_planner_model_tier"] == "sonnet"
    assert (
        row["llm_route_planner_model_tier_decision_basis"]
        == "auto_sonnet_triggers"
    )
    assert row["llm_route_planner_model_tier_decision_sonnet_triggers"] == (
        "1 interactive formal-attempt queue blocked item(s)",
        "1 interactive formal-attempt queue ready item(s)",
        "1 source-theorem proof-body execution failure(s)",
        "2 interactive formal-attempt queue item(s)",
        "3 interactive formal-attempt execution command(s)",
        "3 source-theorem formal-environment blocker(s)",
    )
    assert row["llm_route_planner_model_tier_decision_sonnet_trigger_count"] == 6
    assert row["llm_route_planner_source_feedback_row_count"] == 4
    assert (
        row[
            "llm_route_planner_source_feedback_unverified_semantic_primitive_row_count"
        ]
        == 2
    )
    assert (
        row[
            "llm_route_planner_source_feedback_proof_body_execution_failure_count"
        ]
        == 1
    )
    assert (
        row[
            "llm_route_planner_source_feedback_formal_environment_blocker_count"
        ]
        == 3
    )
    assert row["llm_route_planner_interactive_formal_attempt_queue_row_count"] == 1
    assert row["llm_route_planner_interactive_formal_attempt_queue_item_count"] == 2
    assert (
        row["llm_route_planner_interactive_formal_attempt_queue_ready_item_count"]
        == 1
    )
    assert (
        row["llm_route_planner_interactive_formal_attempt_queue_blocked_item_count"]
        == 1
    )
    assert (
        row[
            "llm_route_planner_interactive_formal_attempt_queue_execution_command_count"
        ]
        == 3
    )
    assert row["llm_route_planner_route_adoption_status"] == (
        "PENDING_REFINEMENT_BEFORE_ROUTE_ADOPTION"
    )
    assert row["llm_route_planner_route_adoption_blockers"] == (
        "quality_control_obligations_pending",
        "search_requests_pending_evidence",
        "source_grounding_obligations_pending",
    )
    assert (
        row["llm_route_planner_route_adoption_preconditions"]
        == route_adoption_preconditions
    )
    assert row["llm_route_planner_route_adoption_precondition_present"] is True
    assert (
        row[
            "llm_route_planner_route_adoption_precondition_blocked_before_response"
        ]
        is True
    )
    assert row[
        "llm_route_planner_route_adoption_precondition_known_blockers"
    ] == (
        "quality_control_obligations_pending",
        "source_grounding_obligations_pending",
    )
    assert row[
        "llm_route_planner_route_adoption_precondition_required_response_fields"
    ] == (
        "planner_next_actions",
        "search_requests",
    )
    assert row[
        "llm_route_planner_route_adoption_precondition_target_primitives"
    ] == ("rank_uniformity",)
    assert (
        row[
            "llm_route_planner_route_adoption_precondition_known_blocker_count"
        ]
        == 2
    )
    assert (
        row[
            "llm_route_planner_route_adoption_precondition_required_response_field_count"
        ]
        == 2
    )
    assert (
        row[
            "llm_route_planner_route_adoption_precondition_target_primitive_count"
        ]
        == 1
    )
    assert row["llm_route_planner_has_generator_metadata"] is True
    assert row["llm_route_planner_generator_metadata_keys"] == (
        "generator_only",
        "provider_usage",
        "retry_count",
    )
    assert row["llm_route_planner_has_provider_usage"] is True
    assert row["llm_route_planner_provider_input_tokens"] == 120
    assert row["llm_route_planner_provider_output_tokens"] == 34
    assert row["llm_route_planner_provider_cache_creation_input_tokens"] == 5
    assert row["llm_route_planner_provider_cache_read_input_tokens"] == 6
    assert row["llm_route_planner_provider_total_tokens"] == 165
    assert row["llm_route_planner_request_contract_blocked"] is False
    assert row["llm_route_planner_errors"] == ()
    assert row["llm_route_planner_generation_errors"] == ()
    assert row["quality_controls_present"] is True
    assert row["quality_controls"] == expected_quality_controls
    assert row["quality_control_fields"] == tuple(sorted(expected_quality_controls))
    assert row["quality_control_resource_contract_ids"] == (
        "lean_lsp:proof_state_feedback",
    )
    assert row["quality_control_response_validation_signals"] == (
        "residual_goals_or_diagnostics_present",
    )
    assert row["quality_control_stop_conditions"] == (
        "residual interpreted or source search requested",
    )
    row_schema = evaluation_row_json_schema()
    assert set(
        row_schema["properties"]["llm_route_planner_route_adoption_blockers"][
            "items"
        ]["enum"]
    ) == set(ROUTE_ADOPTION_BLOCKER_VALUES)
    assert set(
        row_schema["properties"][
            "llm_route_planner_route_adoption_precondition_known_blockers"
        ]["items"]["enum"]
    ) == set(ROUTE_ADOPTION_BLOCKER_VALUES)
    assert validate_evaluation_row(row) == ()
    invented_blocker_row = dict(row)
    invented_blocker_row["llm_route_planner_route_adoption_blockers"] = (
        "invented_route_adoption_blocker",
    )
    assert (
        "llm_route_planner_route_adoption_blockers items contain unsupported "
        "values: invented_route_adoption_blocker"
        in validate_evaluation_row(invented_blocker_row)
    )
    invented_precondition_row = dict(row)
    invented_precondition_row[
        "llm_route_planner_route_adoption_precondition_known_blockers"
    ] = ("invented_route_adoption_blocker",)
    assert (
        "llm_route_planner_route_adoption_precondition_known_blockers items "
        "contain unsupported values: invented_route_adoption_blocker"
        in validate_evaluation_row(invented_precondition_row)
    )


def test_evaluation_surfaces_realization_missing_primitives_by_route() -> None:
    root = Path("runs/test_formalization_gap_planner_evaluation_realization_gaps")
    input_json = root / "standalone_input.json"
    plan_dir = root / "plan"
    truth_json = root / "ground_truth.json"
    out_dir = root / "evaluation"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    realization_witness = {
        "selected_primitives": ["exchangeability", "rank_uniformity"],
        "delta_primitives": ["rank_uniformity"],
        "introduced_primitives": [],
        "aligned_primitives": ["exchangeability"],
        "selected_primitives_missing_formal_realization_node": [
            "rank_uniformity"
        ],
        "delta_primitives_missing_route_alignment_edge": ["rank_uniformity"],
        "introduced_primitives_missing_route_alignment_edge": [],
        "cost_hint_baseline_primitives": ["exchangeability", "rank_uniformity"],
        "omitted_cost_hint_primitives": ["rank_uniformity"],
        "cost_hint_baseline_coverage_complete": False,
        "realization_coverage_complete": False,
    }
    input_json.write_text(
        json.dumps(
            {
                "component_name": "formalization_gap_planner_standalone_input",
                "target_prover_family": "lean4",
                "library_snapshot_ref": "mathlib4:evaluation-realization-gaps",
                "routes": [
                    {
                        "route_id": "rank_route",
                        "display_name": "rank_route",
                        "theorem_statement": "Rank uniformity follows from exchangeability.",
                        "realization_coverage_witness": realization_witness,
                        "replan_metadata": {
                            "llm_route_planner_row_id": "llm-route-row:rank",
                            "llm_route_planner_model_tier": "sonnet",
                            "realization_coverage_witness": realization_witness,
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

    payload = evaluate_formalization_gap_planner(plan_dir, truth_json, out_dir)

    assert payload["n_realization_missing_selected_formal_primitives"] == 1
    assert payload["n_realization_missing_delta_alignment_primitives"] == 1
    assert payload["realization_missing_selected_formal_primitives"] == (
        "rank_uniformity",
    )
    assert payload["realization_missing_delta_alignment_primitives"] == (
        "rank_uniformity",
    )
    assert payload["n_rows_with_incomplete_cost_hint_baseline_coverage"] == 1
    assert payload["n_realization_cost_hint_baseline_primitives"] == 2
    assert payload["realization_cost_hint_baseline_primitives"] == (
        "exchangeability",
        "rank_uniformity",
    )
    assert payload["n_realization_omitted_cost_hint_primitives"] == 1
    assert payload["realization_omitted_cost_hint_primitives"] == (
        "rank_uniformity",
    )
    assert payload["realization_missing_primitives_by_route"] == (
        {
            "route_id": "rank_route",
            "display_name": "rank_route",
            "goal_plan_id": payload["rows"][0]["goal_plan_id"],
            "missing_selected_formal_primitives": ("rank_uniformity",),
            "missing_delta_alignment_primitives": ("rank_uniformity",),
            "omitted_cost_hint_primitives": ("rank_uniformity",),
            "llm_route_planner_row_id": "llm-route-row:rank",
            "llm_route_planner_model_tier": "sonnet",
        },
    )
    report = (
        out_dir / "formalization_gap_planner_evaluation.md"
    ).read_text(encoding="utf-8")
    assert "Missing selected formal primitives" in report
    assert "Omitted cost-hint primitives" in report
    assert "rank_uniformity" in report


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
