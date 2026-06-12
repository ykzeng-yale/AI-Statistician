from __future__ import annotations

import json
import shutil
from pathlib import Path

from ai_statistician.formalization_gap_planner_reuse_smoke import (
    FORMALIZATION_GAP_PLANNER_REUSE_SMOKE_COMPONENT,
    run_formalization_gap_planner_reuse_smoke,
)
from ai_statistician.formalization_gap_planner_local_formal_source_adapter import (
    LEGACY_FORMAL_SOURCE_ADAPTER_FIELD_ALIASES,
)
from ai_statistician.formalization_gap_planner_llm_route_planner import (
    PROOF_EVIDENCE_BOUNDARY as LLM_ROUTE_PLANNER_PROOF_EVIDENCE_BOUNDARY,
)


def _reviewed_llm_route_response_payload() -> dict[str, object]:
    current_route_baseline_primitives = [
        "calibration_scores",
        "coverage_inequality",
        "exchangeability",
        "exchangeable_calibration_and_test_scores",
        "finite_calibration_sample",
        "finite_sample_bound",
        "finite_sample_marginal_coverage_inequality",
        "rank_uniformity",
        "split_conformal_prediction_set",
        "test_score",
    ]
    return {
        "informal_knowledge_dag_nodes": [
            {
                "node_id": "informal:exchangeability",
                "claim": "Calibration and test scores are exchangeable.",
                "depends_on": [],
                "source_refs": ["conformal_prediction_textbook"],
                "source_search_status": "SOURCE_BACKED",
                "semantic_role": "assumption",
            },
            {
                "node_id": "informal:rank_uniformity",
                "claim": "Exchangeability yields the finite rank bound.",
                "depends_on": ["informal:exchangeability"],
                "source_refs": ["conformal_prediction_textbook"],
                "source_search_status": "SOURCE_BACKED",
                "semantic_role": "lemma",
            },
        ],
        "lean_realization_dag_nodes": [
            {
                "node_id": "formal:exchangeability",
                "primitive": "exchangeability",
                "coverage_bucket": "already_exists",
                "candidate_declaration_rows": [
                    {
                        "declaration": "Probability.exchangeable",
                        "target_prover_family": "lean4",
                        "source_field": "available_formal_declaration_rows",
                    }
                ],
                "formalization_action": "reuse",
            },
            {
                "node_id": "formal:rank_uniformity_bridge",
                "primitive": "rank_uniformity",
                "coverage_bucket": "bridge_needed",
                "candidate_declarations": [],
                "formalization_action": "prove_bridge",
            },
        ],
        "route_alignment_edges": [
            {
                "informal_node_id": "informal:rank_uniformity",
                "formal_node_id": "formal:rank_uniformity_bridge",
                "alignment_status": "bridge_needed",
                "alignment_rationale": (
                    "Existing exchangeability support can be reused, while the "
                    "finite-rank statement remains the minimal bridge lemma."
                ),
            }
        ],
        "minimal_delta_plan": {
            "selected_primitives": ["exchangeability", "rank_uniformity"],
            "cost_model_version": "formalization_gap_planner_minimal_delta_cost_policy:1",
            "route_cost": 4,
            "primitive_costs": [
                {
                    "primitive": "exchangeability",
                    "coverage_bucket": "already_exists",
                    "base_cost": 0,
                    "proof_difficulty_cost": 0,
                    "import_cone_cost": 0,
                    "definition_or_typeclass_cost": 0,
                    "semantic_risk_cost": 0,
                    "reuse_credit": 0,
                    "total_cost": 0,
                    "cost_rationale": "Existing exchangeability support is reused.",
                },
                {
                    "primitive": "rank_uniformity",
                    "coverage_bucket": "bridge_needed",
                    "base_cost": 4,
                    "proof_difficulty_cost": 0,
                    "import_cone_cost": 0,
                    "definition_or_typeclass_cost": 0,
                    "semantic_risk_cost": 0,
                    "reuse_credit": 0,
                    "total_cost": 4,
                    "cost_rationale": "Only a focused rank-uniformity bridge is added.",
                },
            ],
            "new_definitions": [],
            "wrapper_lemmas": [],
            "bridge_lemmas": [
                (
                    "rank_uniformity: prove the focused finite-rank uniformity "
                    "bridge from exchangeability"
                )
            ],
            "source_port_lemmas": [],
            "do_not_formalize_now": ["full conformal prediction API"],
            "and_or_cost_graph": {
                "graph_kind": "AND_OR_ROUTE_COST_GRAPH",
                "selected_route_option_id": "route_option:reuse_exchangeability_bridge_rank",
                "route_options": [
                    {
                        "route_option_id": "route_option:reuse_exchangeability_bridge_rank",
                        "selected": True,
                        "selected_primitives": ["exchangeability", "rank_uniformity"],
                        "route_cost": 4,
                        "cost_rationale": "Reuse exchangeability and add one focused bridge.",
                    },
                    {
                        "route_option_id": "route_option:source_port_rank_theory",
                        "selected": False,
                        "selected_primitives": ["exchangeability", "rank_uniformity"],
                        "route_cost": 7,
                        "cost_rationale": "A source port is broader than the selected bridge.",
                    },
                    {
                        "route_option_id": "route_option:current_route_min_delta_baseline",
                        "selected": False,
                        "selected_primitives": current_route_baseline_primitives,
                        "route_cost": 164,
                        "cost_rationale": (
                            "Request-bound baseline preserving the full current "
                            "target route is broader than the selected rank bridge."
                        ),
                    },
                ],
                "or_nodes": [
                    {
                        "node_id": "or:rank_uniformity_realization",
                        "choices": [
                            "route_option:reuse_exchangeability_bridge_rank",
                            "route_option:source_port_rank_theory",
                            "route_option:current_route_min_delta_baseline",
                        ],
                        "selection_rationale": "The selected bridge route has lower cost.",
                    }
                ],
                "and_edges": [
                    {
                        "route_option_id": "route_option:reuse_exchangeability_bridge_rank",
                        "requires": ["exchangeability", "rank_uniformity"],
                    },
                    {
                        "route_option_id": "route_option:current_route_min_delta_baseline",
                        "requires": current_route_baseline_primitives,
                    }
                ],
            },
            "minimality_rationale": (
                "Reuse exchangeability and add only a rank-uniformity bridge."
            ),
        },
        "residual_interpretations": [
            {
                "residual_goal": "exchangeability: non-Lean theorem skeleton",
                "interpretation": (
                    "The route needs a Lean theorem skeleton before proof-state "
                    "feedback can distinguish missing assumptions from missing syntax."
                ),
                "repair_action": "materialize theorem skeleton",
                "formal_gap_boundary": (
                    "Non-Lean theorem skeleton is a formalization boundary before "
                    "proof-state feedback, not source evidence for a new theorem."
                ),
            },
            {
                "residual_goal": "rank_uniformity: non-Lean theorem skeleton",
                "interpretation": (
                    "The rank bridge should be stated as a focused lemma before "
                    "attempting kernel replay."
                ),
                "repair_action": "state focused rank_uniformity bridge lemma",
                "formal_gap_boundary": (
                    "Focused rank bridge skeleton is a formalization boundary before "
                    "kernel replay, not source evidence for a new theorem."
                ),
            },
        ],
        "search_requests": [
            {
                "request_kind": "prover_feedback",
                "query": "try the rank_uniformity bridge against exchangeability",
                "reason": "confirm side conditions before route adoption",
            }
        ],
        "uncertainty_flags": ["tie-breaking convention requires review"],
        "semantic_alignment_risks": ["rank convention may differ across libraries"],
        "planner_next_actions": [
            {
                "owner": "lean_lsp_mcp",
                "action": "attempt a focused rank_uniformity bridge lemma",
            }
        ],
        "standalone_route": {
            "route_id": "llm_rank_route",
            "display_name": "llm_reviewed_rank_route",
            "theorem_statement": (
                "Split conformal coverage follows from exchangeability plus a "
                "finite-rank bridge lemma."
            ),
            "source_refs": ["conformal_prediction_textbook"],
            "primitives": [
                {
                    "primitive": "exchangeability",
                    "coverage_status": "exact_exists",
                    "candidate_declaration_rows": [
                        {
                            "declaration": "Probability.exchangeable",
                            "target_prover_family": "lean4",
                            "source_field": "available_formal_declaration_rows",
                        }
                    ],
                    "source_refs": ["conformal_prediction_textbook"],
                },
                {
                    "primitive": "rank_uniformity",
                    "coverage_status": "bridge_needed",
                    "source_refs": ["conformal_prediction_textbook"],
                },
            ],
        },
        "proof_evidence_boundary": LLM_ROUTE_PLANNER_PROOF_EVIDENCE_BOUNDARY,
    }


def test_reuse_smoke_runs_public_publication_path() -> None:
    root = Path("runs/test_formalization_gap_planner_reuse_smoke")
    input_path = root / "target_request.json"
    out_dir = root / "reuse_smoke"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "component_name": "formalization_gap_planner_target_intake",
                "target_prover_family": "lean4",
                "library_snapshot_ref": "mathlib4:reuse-smoke",
                "target_id": "split_conformal_coverage",
                "title": "Split conformal finite-sample coverage",
                "domain": "distribution-free prediction",
                "theorem_statement": (
                    "For exchangeable calibration and test scores, split "
                    "conformal prediction has finite sample marginal coverage."
                ),
                "objects": ["calibration scores", "test score"],
                "assumptions": [
                    "exchangeable calibration and test scores",
                    "finite calibration sample",
                ],
                "statistical_procedure": "split conformal prediction set",
                "desired_conclusion": "finite sample marginal coverage inequality",
                "desired_theorem_shape": "coverage probability lower bound",
                "known_proof_sources": ["Lei-Wasserman distribution-free prediction"],
                "candidate_primitives": [
                    {
                        "primitive": "rank uniformity",
                        "coverage_status": "bridge_needed",
                    }
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    payload = run_formalization_gap_planner_reuse_smoke(
        input_path,
        out_dir,
        target_prover_family="rocq",
        target_library_snapshot_ref="rocq:reuse-smoke",
    )

    assert payload["all_ok"]
    assert payload["component_name"] == FORMALIZATION_GAP_PLANNER_REUSE_SMOKE_COMPONENT
    assert payload["n_stages"] == 36
    assert payload["n_failed"] == 0
    assert payload["n_proof_boundary_ok"] == payload["n_stages"]
    assert payload["target_prover_family"] == "rocq"
    assert payload["source_target_prover_family"] == "lean4"
    assert payload["n_source_target_prover_families"] == 1
    assert payload["source_by_target_prover_family"] == {"lean4": 1}
    assert (
        payload[
            "n_goal_plan_standalone_input_traces_with_llm_route_planner_metadata"
        ]
        == 1
    )
    assert payload["n_goal_plan_standalone_input_traces_with_llm_model_tier"] == 1
    assert payload["goal_plan_standalone_input_trace_by_llm_model_tier"] == {
        "sonnet": 1
    }
    assert payload["goal_plan_standalone_input_trace_by_llm_route_adoption_status"] == {
        "AWAITING_LLM_ROUTE_PLANNER_RESPONSE": 1
    }
    assert (
        payload[
            "n_goal_plan_standalone_input_traces_with_llm_generator_metadata"
        ]
        == 0
    )
    assert payload["n_goal_plan_standalone_input_traces_with_llm_seed_selection"] == 1
    assert payload["n_goal_plan_standalone_input_traces_llm_seed_selected"] == 1
    assert (
        payload[
            "n_goal_plan_standalone_input_traces_llm_seed_adoptable_for_standalone_replay"
        ]
        == 0
    )
    assert (
        payload[
            "n_goal_plan_standalone_input_traces_llm_seed_selected_not_adoptable"
        ]
        == 1
    )
    assert payload[
        "goal_plan_standalone_input_trace_by_llm_seed_selection_rank"
    ] == {"1": 1}
    assert (
        payload[
            "n_goal_plan_standalone_input_traces_with_llm_seed_minimal_delta_route_cost"
        ]
        == 0
    )
    assert payload["n_llm_route_planner_request_packets"] > 0
    assert payload["llm_route_planner_model_tier_selection_mode"] == "auto"
    assert (
        payload["llm_route_planner_provider_execution_mode"]
        == "staged_live_provider_prompt_no_api_call"
    )
    assert payload["n_llm_route_planner_live_provider_calls_requested"] == 0
    assert payload["llm_route_planner_max_repair_attempts"] == 1
    assert payload["llm_route_planner_by_request_model_tier"]
    assert (
        payload["n_llm_route_planner_request_model_tier_haiku"]
        + payload["n_llm_route_planner_request_model_tier_sonnet"]
        + payload["n_llm_route_planner_request_model_tier_opus"]
        == payload["n_llm_route_planner_request_packets"]
    )
    assert payload["n_llm_route_planner_request_model_tier_mismatches"] == 0
    assert payload["llm_route_planner_request_model_tier_mismatches"] == []
    assert (
        payload["n_llm_route_planner_requests_with_model_tier_decision_evidence"]
        == payload["n_llm_route_planner_request_packets"]
    )
    assert (
        payload[
            "n_llm_route_planner_request_model_tier_decision_auto_haiku_bounded"
        ]
        + payload[
            "n_llm_route_planner_request_model_tier_decision_auto_sonnet_triggered"
        ]
        + payload[
            "n_llm_route_planner_request_model_tier_decision_operator_override"
        ]
        == payload["n_llm_route_planner_request_packets"]
    )
    assert (
        payload[
            "n_llm_route_planner_request_model_tier_decision_evidence_invalid"
        ]
        == 0
    )
    assert payload["llm_route_planner_by_request_model_tier_decision_basis"]
    assert (
        payload["n_llm_route_planner_requests_with_llm_generation_policy"]
        == payload["n_llm_route_planner_request_packets"]
    )
    assert (
        payload[
            "n_llm_route_planner_request_llm_generation_policy_tier_model_matches"
        ]
        == payload["n_llm_route_planner_request_packets"]
    )
    assert (
        payload[
            "n_llm_route_planner_request_llm_generation_policy_codex_exclusions"
        ]
        == payload["n_llm_route_planner_request_packets"]
    )
    assert (
        payload[
            "n_llm_route_planner_request_llm_generation_policy_current_claude_tier_source"
        ]
        == payload["n_llm_route_planner_request_packets"]
    )
    assert (
        payload["n_llm_route_planner_requests_with_library_alignment_summary"]
        == payload["n_llm_route_planner_request_packets"]
    )
    assert payload["n_llm_route_planner_request_library_alignment_primitives"] > 0
    assert (
        payload[
            "n_llm_route_planner_request_library_alignment_bridge_or_harder_primitives"
        ]
        >= 0
    )
    assert payload["llm_route_planner_by_request_library_alignment_delta_class"]
    assert payload[
        "llm_route_planner_by_request_library_alignment_minimum_coverage_bucket"
    ]
    assert payload["n_llm_route_planner_generation_preflight_blocked"] == 0
    assert payload["llm_route_planner_generation_preflight_errors"] == []
    assert (
        payload["n_llm_route_planner_request_schema_valid"]
        == payload["n_llm_route_planner_request_packets"]
    )
    assert payload["n_llm_route_planner_request_schema_invalid"] == 0
    assert payload["n_llm_route_planner_response_present"] == 0
    assert not payload["has_llm_route_planner_response_payload_validation"]
    assert payload["n_llm_route_planner_response_payload_validation_payloads"] == 0
    assert (
        payload["n_llm_route_planner_response_payload_validation_valid_payloads"]
        == 0
    )
    assert (
        payload["n_llm_route_planner_response_payload_validation_invalid_payloads"]
        == 0
    )
    assert (
        payload[
            "n_llm_route_planner_response_payload_validation_request_context_inventories"
        ]
        == 0
    )
    assert (
        payload[
            "n_llm_route_planner_response_payload_validation_request_bound_payloads_with_context_inventory"
        ]
        == 0
    )
    assert (
        payload[
            "n_llm_route_planner_response_payload_validation_declared_target_prover_payloads"
        ]
        == 0
    )
    assert (
        payload[
            "n_llm_route_planner_response_payload_validation_target_prover_mismatches"
        ]
        == 0
    )
    assert (
        payload[
            "llm_route_planner_response_payload_validation_by_payload_target_prover_family"
        ]
        == {}
    )
    assert (
        payload[
            "llm_route_planner_response_payload_validation_by_request_context_target_prover_family"
        ]
        == {}
    )
    assert payload["n_llm_route_planner_provider_failures"] == 0
    assert payload["n_llm_route_planner_rows_with_generator_metadata"] == 0
    assert payload["n_llm_route_planner_rows_with_generation_errors"] == 0
    assert (
        payload["n_llm_route_planner_awaiting"]
        == payload["n_llm_route_planner_request_packets"]
    )
    assert payload["n_llm_route_planner_accepted_route_plans"] == 0
    assert (
        payload["n_llm_route_planner_row_schema_valid"]
        == payload["n_llm_route_planner_request_packets"]
    )
    assert payload["n_llm_route_planner_row_schema_invalid"] == 0
    report_text = (
        out_dir / "formalization_gap_planner_reuse_smoke.md"
    ).read_text(encoding="utf-8")
    assert "Source prover targets: `lean4` families=1 by={'lean4': 1}" in report_text
    assert "cost-hint-incomplete" in report_text

    assert (
        payload["n_llm_route_planner_rows_with_realization_coverage_witness"]
        == payload["n_llm_route_planner_request_packets"]
    )
    assert payload["n_llm_route_planner_rows_with_complete_realization_coverage"] == 0
    assert (
        payload["n_llm_route_planner_selected_primitives_missing_formal_realization"]
        == 0
    )
    assert payload["n_llm_route_planner_delta_primitives_missing_route_alignment"] == 0
    assert payload["n_llm_route_planner_feedback_loop_realization_witnesses"] == 0
    assert (
        payload["n_llm_route_planner_feedback_loop_incomplete_realization_coverage"]
        == 0
    )
    assert (
        payload[
            "n_llm_route_planner_feedback_loop_incomplete_cost_hint_baseline_coverage"
        ]
        == 0
    )
    assert (
        payload[
            "n_llm_route_planner_feedback_loop_missing_selected_formal_primitives"
        ]
        == 0
    )
    assert (
        payload[
            "n_llm_route_planner_feedback_loop_missing_delta_alignment_primitives"
        ]
        == 0
    )
    assert (
        payload["n_llm_route_planner_feedback_loop_omitted_cost_hint_primitives"]
        == 0
    )
    assert (
        payload[
            "n_llm_route_planner_requests_with_component_resource_registry_context"
        ]
        == payload["n_llm_route_planner_request_packets"]
    )
    assert payload["n_llm_route_planner_component_resource_registry_resources_in_prompt"] > 0
    assert payload["n_llm_route_planner_component_resource_registry_contracts_in_prompt"] > 0
    assert payload["n_feedback_llm_route_planner_request_packets"] > 0
    assert payload["feedback_llm_route_planner_model_tier_selection_mode"] == "auto"
    assert (
        payload["feedback_llm_route_planner_provider_execution_mode"]
        == "staged_live_provider_prompt_no_api_call"
    )
    assert payload["n_feedback_llm_route_planner_live_provider_calls_requested"] == 0
    assert payload["n_total_llm_route_planner_live_provider_calls_requested"] == 0
    assert payload["feedback_llm_route_planner_max_repair_attempts"] == 1
    assert payload["feedback_llm_route_planner_by_request_model_tier"]
    assert (
        payload["n_feedback_llm_route_planner_request_model_tier_haiku"]
        + payload["n_feedback_llm_route_planner_request_model_tier_sonnet"]
        + payload["n_feedback_llm_route_planner_request_model_tier_opus"]
        == payload["n_feedback_llm_route_planner_request_packets"]
    )
    assert payload["n_feedback_llm_route_planner_request_model_tier_mismatches"] == 0
    assert payload["feedback_llm_route_planner_request_model_tier_mismatches"] == []
    assert (
        payload[
            "n_feedback_llm_route_planner_requests_with_model_tier_decision_evidence"
        ]
        == payload["n_feedback_llm_route_planner_request_packets"]
    )
    assert (
        payload[
            "n_feedback_llm_route_planner_request_model_tier_decision_auto_haiku_bounded"
        ]
        + payload[
            "n_feedback_llm_route_planner_request_model_tier_decision_auto_sonnet_triggered"
        ]
        + payload[
            "n_feedback_llm_route_planner_request_model_tier_decision_operator_override"
        ]
        == payload["n_feedback_llm_route_planner_request_packets"]
    )
    assert (
        payload[
            "n_feedback_llm_route_planner_request_model_tier_decision_evidence_invalid"
        ]
        == 0
    )
    assert payload["feedback_llm_route_planner_by_request_model_tier_decision_basis"]
    assert (
        payload["n_feedback_llm_route_planner_requests_with_llm_generation_policy"]
        == payload["n_feedback_llm_route_planner_request_packets"]
    )
    assert (
        payload[
            "n_feedback_llm_route_planner_request_llm_generation_policy_tier_model_matches"
        ]
        == payload["n_feedback_llm_route_planner_request_packets"]
    )
    assert (
        payload[
            "n_feedback_llm_route_planner_request_llm_generation_policy_codex_exclusions"
        ]
        == payload["n_feedback_llm_route_planner_request_packets"]
    )
    assert (
        payload[
            "n_feedback_llm_route_planner_request_llm_generation_policy_current_claude_tier_source"
        ]
        == payload["n_feedback_llm_route_planner_request_packets"]
    )
    assert (
        payload[
            "n_feedback_llm_route_planner_requests_with_library_alignment_summary"
        ]
        == payload["n_feedback_llm_route_planner_request_packets"]
    )
    assert (
        payload[
            "n_feedback_llm_route_planner_request_library_alignment_primitives"
        ]
        > 0
    )
    assert payload[
        "feedback_llm_route_planner_by_request_library_alignment_delta_class"
    ]
    assert payload[
        "feedback_llm_route_planner_by_request_library_alignment_minimum_coverage_bucket"
    ]
    assert payload["n_feedback_llm_route_planner_generation_preflight_blocked"] == 0
    assert payload["feedback_llm_route_planner_generation_preflight_errors"] == []
    assert (
        payload["n_feedback_llm_route_planner_request_schema_valid"]
        == payload["n_feedback_llm_route_planner_request_packets"]
    )
    assert payload["n_feedback_llm_route_planner_request_schema_invalid"] == 0
    assert payload["n_feedback_llm_route_planner_response_present"] == 0
    assert payload["n_feedback_llm_route_planner_provider_failures"] == 0
    assert payload["n_feedback_llm_route_planner_rows_with_generator_metadata"] == 0
    assert payload["n_feedback_llm_route_planner_rows_with_generation_errors"] == 0
    assert payload["n_feedback_llm_route_planner_awaiting"] == payload[
        "n_feedback_llm_route_planner_request_packets"
    ]
    assert payload["n_feedback_llm_route_planner_accepted_route_plans"] == 0
    assert payload["llm_route_planner_provider"] == "anthropic"
    assert payload["feedback_llm_route_planner_provider"] == "anthropic"
    stage_by_name = {stage["stage_name"]: stage for stage in payload["stages"]}
    assert (
        "formalization_gap_planner_llm_route_planner_response_payload_validation"
        not in stage_by_name
    )
    llm_stage_summary = stage_by_name[
        "formalization_gap_planner_llm_route_planner"
    ]["summary"]
    assert llm_stage_summary["model_tier_selection_mode"] == "auto"
    assert llm_stage_summary["by_request_model_tier"] == payload[
        "llm_route_planner_by_request_model_tier"
    ]
    assert llm_stage_summary[
        "n_route_adoption_pending_omitted_cost_hint_primitive_blockers"
    ] == payload[
        "n_llm_route_planner_route_adoption_pending_omitted_cost_hint_primitive_blockers"
    ]
    assert "n_formal_realization_dag_nodes" in llm_stage_summary
    assert llm_stage_summary["n_route_adoption_omitted_cost_hint_primitives"] == (
        payload["n_llm_route_planner_route_adoption_omitted_cost_hint_primitives"]
    )
    assert llm_stage_summary["n_planner_next_actions"] == payload[
        "n_llm_route_planner_planner_next_actions"
    ]
    assert llm_stage_summary["n_rows_with_planner_next_actions"] == payload[
        "n_llm_route_planner_rows_with_planner_next_actions"
    ]
    feedback_llm_stage_summary = stage_by_name[
        "formalization_gap_planner_feedback_llm_route_planner"
    ]["summary"]
    assert feedback_llm_stage_summary["model_tier_selection_mode"] == "auto"
    assert "n_formal_realization_dag_nodes" in feedback_llm_stage_summary
    assert feedback_llm_stage_summary["by_request_model_tier"] == payload[
        "feedback_llm_route_planner_by_request_model_tier"
    ]
    assert feedback_llm_stage_summary[
        "n_route_adoption_pending_omitted_cost_hint_primitive_blockers"
    ] == payload[
        "n_feedback_llm_route_planner_route_adoption_pending_omitted_cost_hint_primitive_blockers"
    ]
    assert feedback_llm_stage_summary[
        "n_route_adoption_omitted_cost_hint_primitives"
    ] == payload[
        "n_feedback_llm_route_planner_route_adoption_omitted_cost_hint_primitives"
    ]
    assert feedback_llm_stage_summary["n_planner_next_actions"] == payload[
        "n_feedback_llm_route_planner_planner_next_actions"
    ]
    assert feedback_llm_stage_summary["n_rows_with_planner_next_actions"] == payload[
        "n_feedback_llm_route_planner_rows_with_planner_next_actions"
    ]
    reproduction_command = payload["reproduction_commands"][0]
    assert "--llm-route-planner-model-tier auto" in reproduction_command
    assert "--llm-route-planner-max-repair-attempts 1" in reproduction_command
    assert "--feedback-llm-route-planner-model-tier auto" in reproduction_command
    assert "--feedback-llm-route-planner-max-repair-attempts 1" in reproduction_command
    assert (
        payload["n_feedback_llm_route_planner_row_schema_valid"]
        == payload["n_feedback_llm_route_planner_request_packets"]
    )
    assert payload["n_feedback_llm_route_planner_row_schema_invalid"] == 0
    assert (
        payload["n_feedback_llm_route_planner_rows_with_realization_coverage_witness"]
        == payload["n_feedback_llm_route_planner_request_packets"]
    )
    assert (
        payload["n_feedback_llm_route_planner_rows_with_complete_realization_coverage"]
        == 0
    )
    assert (
        payload[
            "n_feedback_llm_route_planner_selected_primitives_missing_formal_realization"
        ]
        == 0
    )
    assert (
        payload["n_feedback_llm_route_planner_delta_primitives_missing_route_alignment"]
        == 0
    )
    assert payload["n_feedback_llm_route_planner_feedback_loop_realization_witnesses"] == 0
    assert (
        payload[
            "n_feedback_llm_route_planner_feedback_loop_incomplete_realization_coverage"
        ]
        == 0
    )
    assert (
        payload[
            "n_feedback_llm_route_planner_feedback_loop_incomplete_cost_hint_baseline_coverage"
        ]
        == 0
    )
    assert (
        payload[
            "n_feedback_llm_route_planner_feedback_loop_missing_selected_formal_primitives"
        ]
        == 0
    )
    assert (
        payload[
            "n_feedback_llm_route_planner_feedback_loop_missing_delta_alignment_primitives"
        ]
        == 0
    )
    assert (
        payload[
            "n_feedback_llm_route_planner_feedback_loop_omitted_cost_hint_primitives"
        ]
        == 0
    )
    assert payload["n_feedback_llm_route_planner_request_residual_goals"] > 0
    assert (
        payload["n_feedback_llm_route_planner_requests_with_library_coverage_rows"]
        > 0
    )
    assert (
        payload["n_feedback_llm_route_planner_requests_with_source_grounding_rows"]
        > 0
    )
    assert (
        payload[
            "n_feedback_llm_route_planner_requests_with_resource_request_queue_rows"
        ]
        > 0
    )
    assert (
        payload["n_feedback_llm_route_planner_resource_request_queue_rows"]
        >= payload[
            "n_feedback_llm_route_planner_requests_with_resource_request_queue_rows"
        ]
    )
    assert (
        payload[
            "n_feedback_llm_route_planner_requests_with_resource_response_ledger_rows"
        ]
        > 0
    )
    assert (
        payload["n_feedback_llm_route_planner_requests_with_refinement_evidence_rows"]
        > 0
    )
    assert (
        payload[
            "n_feedback_llm_route_planner_requests_with_route_revision_overlay_rows"
        ]
        > 0
    )
    assert payload["n_feedback_llm_route_planner_requests_with_interactive_session_rows"] > 0
    assert (
        payload[
            "n_feedback_llm_route_planner_requests_with_interactive_decision_policy_rows"
        ]
        > 0
    )
    assert (
        payload[
            "n_feedback_llm_route_planner_requests_with_component_resource_registry_context"
        ]
        == payload["n_feedback_llm_route_planner_request_packets"]
    )
    assert (
        payload[
            "n_feedback_llm_route_planner_component_resource_registry_resources_in_prompt"
        ]
        > 0
    )
    assert (
        payload[
            "n_feedback_llm_route_planner_component_resource_registry_contracts_in_prompt"
        ]
        > 0
    )
    assert (
        payload[
            "n_publication_bundle_optional_llm_route_planner_request_schema_valid"
        ]
        == payload[
            "n_publication_bundle_optional_llm_route_planner_request_schema_checked"
        ]
        == payload["n_llm_route_planner_request_packets"]
    )
    assert (
        payload[
            "n_publication_bundle_optional_llm_route_planner_request_model_tier_mismatch_valid"
        ]
        == payload[
            "n_publication_bundle_optional_llm_route_planner_request_model_tier_mismatch_checked"
        ]
        == 1
    )
    assert (
        payload[
            "n_publication_bundle_optional_llm_route_planner_request_generation_policy_valid"
        ]
        == payload[
            "n_publication_bundle_optional_llm_route_planner_request_generation_policy_checked"
        ]
        == payload["n_llm_route_planner_request_packets"]
    )
    assert (
        payload[
            "n_publication_bundle_optional_llm_route_planner_generation_preflight_valid"
        ]
        == payload[
            "n_publication_bundle_optional_llm_route_planner_generation_preflight_checked"
        ]
        == 1
    )
    assert (
        payload["n_publication_bundle_optional_llm_route_planner_row_schema_valid"]
        == payload["n_publication_bundle_optional_llm_route_planner_row_schema_checked"]
        == payload["n_llm_route_planner_request_packets"]
    )
    assert (
        payload[
            "n_publication_bundle_optional_llm_route_planner_realization_witness_schema_valid"
        ]
        == payload[
            "n_publication_bundle_optional_llm_route_planner_realization_witness_schema_checked"
        ]
        == 1
    )
    assert (
        payload[
            "n_publication_bundle_optional_llm_route_planner_seed_realization_witness_valid"
        ]
        == payload[
            "n_publication_bundle_optional_llm_route_planner_seed_realization_witness_checked"
        ]
        == 0
    )
    assert (
        payload[
            "n_publication_bundle_optional_llm_route_planner_seed_model_provenance_valid"
        ]
        == payload[
            "n_publication_bundle_optional_llm_route_planner_seed_model_provenance_checked"
        ]
        == 0
    )
    assert (
        payload[
            "n_publication_bundle_optional_llm_route_planner_seed_route_selection_summary_valid"
        ]
        == payload[
            "n_publication_bundle_optional_llm_route_planner_seed_route_selection_summary_checked"
        ]
        == 1
    )
    assert (
        payload[
            "n_publication_bundle_optional_llm_route_planner_seed_route_selection_contract_valid"
        ]
        == payload[
            "n_publication_bundle_optional_llm_route_planner_seed_route_selection_contract_checked"
        ]
        == 1
    )
    assert (
        payload[
            "n_publication_bundle_optional_llm_route_planner_seed_route_selection_schema_valid"
        ]
        == payload[
            "n_publication_bundle_optional_llm_route_planner_seed_route_selection_schema_checked"
        ]
        == 1
    )
    assert (
        payload[
            "n_publication_bundle_optional_llm_route_planner_seed_route_selection_valid"
        ]
        == payload[
            "n_publication_bundle_optional_llm_route_planner_seed_route_selection_checked"
        ]
        == 0
    )
    assert (
        payload[
            "n_publication_bundle_optional_llm_route_planner_seed_route_selection_candidates"
        ]
        == 1
    )
    assert (
        payload[
            "n_publication_bundle_optional_llm_route_planner_seed_route_selection_adoptable_candidates"
        ]
        == 0
    )
    assert (
        payload[
            "n_publication_bundle_optional_llm_route_planner_seed_route_selection_selected_adoptable"
        ]
        == 0
    )
    assert (
        payload[
            "n_publication_bundle_optional_llm_route_planner_seed_route_selection_selected_not_adoptable"
        ]
        == 1
    )
    assert (
        payload[
            "n_publication_bundle_optional_feedback_llm_route_planner_request_schema_valid"
        ]
        == payload[
            "n_publication_bundle_optional_feedback_llm_route_planner_request_schema_checked"
        ]
        == payload["n_feedback_llm_route_planner_request_packets"]
    )
    assert (
        payload[
            "n_publication_bundle_optional_feedback_llm_route_planner_request_model_tier_mismatch_valid"
        ]
        == payload[
            "n_publication_bundle_optional_feedback_llm_route_planner_request_model_tier_mismatch_checked"
        ]
        == 1
    )
    assert (
        payload[
            "n_publication_bundle_optional_feedback_llm_route_planner_request_generation_policy_valid"
        ]
        == payload[
            "n_publication_bundle_optional_feedback_llm_route_planner_request_generation_policy_checked"
        ]
        == payload["n_feedback_llm_route_planner_request_packets"]
    )
    assert (
        payload[
            "n_publication_bundle_optional_feedback_llm_route_planner_generation_preflight_valid"
        ]
        == payload[
            "n_publication_bundle_optional_feedback_llm_route_planner_generation_preflight_checked"
        ]
        == 1
    )
    assert (
        payload[
            "n_publication_bundle_optional_feedback_llm_route_planner_realization_witness_schema_valid"
        ]
        == payload[
            "n_publication_bundle_optional_feedback_llm_route_planner_realization_witness_schema_checked"
        ]
        == 1
    )
    assert (
        payload[
            "n_publication_bundle_optional_feedback_llm_route_planner_seed_realization_witness_valid"
        ]
        == payload[
            "n_publication_bundle_optional_feedback_llm_route_planner_seed_realization_witness_checked"
        ]
        == 0
    )
    assert (
        payload[
            "n_publication_bundle_optional_feedback_llm_route_planner_seed_model_provenance_valid"
        ]
        == payload[
            "n_publication_bundle_optional_feedback_llm_route_planner_seed_model_provenance_checked"
        ]
        == 0
    )
    assert (
        payload[
            "n_publication_bundle_optional_feedback_llm_route_planner_seed_route_selection_summary_valid"
        ]
        == payload[
            "n_publication_bundle_optional_feedback_llm_route_planner_seed_route_selection_summary_checked"
        ]
        == 1
    )
    assert (
        payload[
            "n_publication_bundle_optional_feedback_llm_route_planner_seed_route_selection_contract_valid"
        ]
        == payload[
            "n_publication_bundle_optional_feedback_llm_route_planner_seed_route_selection_contract_checked"
        ]
        == 1
    )
    assert (
        payload[
            "n_publication_bundle_optional_feedback_llm_route_planner_seed_route_selection_schema_valid"
        ]
        == payload[
            "n_publication_bundle_optional_feedback_llm_route_planner_seed_route_selection_schema_checked"
        ]
        == 1
    )
    assert (
        payload[
            "n_publication_bundle_optional_feedback_llm_route_planner_seed_route_selection_valid"
        ]
        == payload[
            "n_publication_bundle_optional_feedback_llm_route_planner_seed_route_selection_checked"
        ]
        == 0
    )
    assert (
        payload[
            "n_publication_bundle_optional_feedback_llm_route_planner_seed_route_selection_candidates"
        ]
        == 1
    )
    assert (
        payload[
            "n_publication_bundle_optional_feedback_llm_route_planner_seed_route_selection_adoptable_candidates"
        ]
        == 0
    )
    assert (
        payload[
            "n_publication_bundle_optional_feedback_llm_route_planner_seed_route_selection_selected_adoptable"
        ]
        == 0
    )
    assert (
        payload[
            "n_publication_bundle_optional_feedback_llm_route_planner_seed_route_selection_selected_not_adoptable"
        ]
        == 1
    )
    assert (
        payload[
            "n_publication_bundle_optional_feedback_llm_route_planner_row_schema_valid"
        ]
        == payload[
            "n_publication_bundle_optional_feedback_llm_route_planner_row_schema_checked"
        ]
        == payload["n_feedback_llm_route_planner_request_packets"]
    )
    assert (
        payload[
            "n_publication_bundle_optional_llm_route_planner_response_payload_validation_manifest_contract_checked"
        ]
        == 0
    )
    assert (
        payload[
            "n_publication_bundle_optional_llm_route_planner_response_payload_validation_row_schema_checked"
        ]
        == 0
    )
    assert payload["n_portable_work_packets"] > 0
    assert payload["n_route_alignment_edges"] >= payload["n_portable_work_packets"]
    assert (
        payload["n_route_alignment_edge_schema_valid"]
        == payload["n_route_alignment_edges"]
    )
    assert payload["n_route_alignment_edge_schema_invalid"] == 0
    assert (
        payload["n_portable_plan_audit_route_alignment_edge_schema_valid"]
        == payload["n_portable_plan_audit_route_alignment_edges"]
    )
    assert payload["n_portable_plan_audit_route_alignment_edge_schema_invalid"] == 0
    assert (
        payload["n_portable_plan_audit_row_schema_valid"]
        == payload[
            "n_publication_bundle_optional_portable_plan_audit_row_schema_checked"
        ]
    )
    assert payload["n_portable_plan_audit_row_schema_invalid"] == 0
    assert (
        payload["n_publication_bundle_optional_portable_plan_audit_row_schema_valid"]
        == payload[
            "n_publication_bundle_optional_portable_plan_audit_row_schema_checked"
        ]
    )
    assert payload["n_library_coverage_rows"] == payload["n_route_alignment_edges"]
    assert payload["n_library_coverage_ok"] == payload["n_library_coverage_rows"]
    assert payload["n_library_coverage_failed"] == 0
    assert (
        payload["n_library_coverage_row_schema_valid"]
        == payload["n_library_coverage_rows"]
    )
    assert payload["n_library_coverage_row_schema_invalid"] == 0
    assert payload["n_library_coverage_unknown_or_unaligned"] == 0
    assert (
        payload["n_library_coverage_rows_with_alignment"]
        == payload["n_library_coverage_rows"]
    )
    assert (
        payload[
            "n_publication_bundle_optional_library_coverage_map_row_schema_valid"
        ]
        == payload[
            "n_publication_bundle_optional_library_coverage_map_row_schema_checked"
        ]
        == payload["n_library_coverage_rows"]
    )
    assert payload["n_primitive_action_queue_items"] == payload["n_library_coverage_rows"]
    assert (
        payload["n_primitive_action_queue_ok"]
        == payload["n_primitive_action_queue_items"]
    )
    assert payload["n_primitive_action_queue_failed"] == 0
    assert (
        payload["n_primitive_action_queue_row_schema_valid"]
        == payload["n_primitive_action_queue_items"]
    )
    assert payload["n_primitive_action_queue_row_schema_invalid"] == 0
    assert (
        payload[
            "n_publication_bundle_optional_primitive_action_queue_row_schema_valid"
        ]
        == payload[
            "n_publication_bundle_optional_primitive_action_queue_row_schema_checked"
        ]
        == payload["n_primitive_action_queue_items"]
    )
    assert payload["n_action_resource_plan_rows"] == payload["n_primitive_action_queue_items"]
    assert payload["n_action_resource_plan_ok"] == payload["n_action_resource_plan_rows"]
    assert payload["n_action_resource_plan_failed"] == 0
    assert (
        payload["n_action_resource_plan_row_schema_valid"]
        == payload["n_action_resource_plan_rows"]
    )
    assert payload["n_action_resource_plan_row_schema_invalid"] == 0
    assert (
        payload["n_action_resource_plan_with_frontier_resources"]
        == payload["n_action_resource_plan_rows"]
    )
    assert (
        payload["n_action_resource_plan_with_resource_contracts"]
        == payload["n_action_resource_plan_rows"]
    )
    assert (
        payload[
            "n_publication_bundle_optional_action_resource_plan_row_schema_valid"
        ]
        == payload[
            "n_publication_bundle_optional_action_resource_plan_row_schema_checked"
        ]
        == payload["n_action_resource_plan_rows"]
    )
    assert payload["n_resource_request_rows"] > payload["n_action_resource_plan_rows"]
    assert payload["n_resource_request_ok"] == payload["n_resource_request_rows"]
    assert payload["n_resource_request_failed"] == 0
    assert payload["n_resource_request_local_first"] > 0
    assert payload["n_resource_request_frontier_escalation"] > 0
    assert payload["n_resource_request_distinct_resources"] > 0
    assert (
        payload["n_resource_request_self_contained_payloads"]
        == payload["n_resource_request_rows"]
    )
    assert payload["n_resource_request_payload_identity_mismatches"] == 0
    assert payload["n_resource_request_dispatch_specs"] == payload[
        "n_resource_request_rows"
    ]
    assert (
        payload["n_resource_request_dispatch_spec_identity_valid"]
        == payload["n_resource_request_rows"]
    )
    assert payload["n_resource_request_dispatch_spec_identity_mismatches"] == 0
    assert (
        payload["n_resource_request_row_schema_valid"]
        == payload["n_resource_request_rows"]
    )
    assert payload["n_resource_request_row_schema_invalid"] == 0
    assert (
        payload[
            "n_publication_bundle_optional_resource_request_queue_row_schema_valid"
        ]
        == payload[
            "n_publication_bundle_optional_resource_request_queue_row_schema_checked"
        ]
        == payload["n_resource_request_rows"]
    )
    assert (
        payload[
            "n_publication_bundle_optional_resource_request_action_plan_ref_valid"
        ]
        == payload[
            "n_publication_bundle_optional_resource_request_action_plan_ref_checked"
        ]
        == payload["n_resource_request_rows"]
    )
    assert (
        payload[
            "n_publication_bundle_optional_resource_request_payload_identity_valid"
        ]
        == payload[
            "n_publication_bundle_optional_resource_request_payload_identity_checked"
        ]
        == payload["n_resource_request_rows"]
    )
    assert (
        payload[
            "n_publication_bundle_optional_resource_request_dispatch_spec_valid"
        ]
        == payload[
            "n_publication_bundle_optional_resource_request_dispatch_spec_checked"
        ]
        == payload["n_resource_request_rows"]
    )
    assert (
        payload[
            "n_publication_bundle_optional_resource_request_contract_alignment_valid"
        ]
        == payload[
            "n_publication_bundle_optional_resource_request_contract_alignment_checked"
        ]
        == payload["n_resource_request_rows"]
    )
    assert payload["n_resource_response_ledger_rows"] == payload["n_resource_request_rows"]
    assert (
        payload["n_resource_response_ledger_ok"]
        == payload["n_resource_response_ledger_rows"]
    )
    assert payload["n_resource_response_ledger_response_present"] == 0
    assert (
        payload["n_resource_response_ledger_awaiting"]
        == payload["n_resource_response_ledger_rows"]
    )
    assert payload["n_resource_response_ledger_contract_ok"] == 0
    assert (
        payload["n_resource_response_ledger_request_playbook_present"]
        == payload["n_resource_response_ledger_rows"]
    )
    assert payload["n_resource_response_ledger_playbook_grounded"] == 0
    assert payload["n_resource_response_ledger_playbook_grounding_failures"] == 0
    assert payload["n_resource_response_ledger_request_mismatches"] == 0
    assert payload["n_resource_response_ledger_route_revision_recommended"] == 0
    assert payload["n_resource_response_ledger_rejected"] == 0
    assert (
        payload["n_resource_response_ledger_row_schema_valid"]
        == payload["n_resource_response_ledger_rows"]
    )
    assert payload["n_resource_response_ledger_row_schema_invalid"] == 0
    assert (
        payload[
            "n_publication_bundle_optional_resource_response_ledger_row_schema_valid"
        ]
        == payload[
            "n_publication_bundle_optional_resource_response_ledger_row_schema_checked"
        ]
        == payload["n_resource_response_ledger_rows"]
    )
    assert (
        payload["n_publication_bundle_optional_resource_response_request_ref_valid"]
        == payload["n_publication_bundle_optional_resource_response_request_ref_checked"]
        == payload["n_resource_response_ledger_rows"]
    )
    assert (
        payload[
            "n_publication_bundle_optional_resource_response_contract_field_accounting_valid"
        ]
        == payload[
            "n_publication_bundle_optional_resource_response_contract_field_accounting_checked"
        ]
        == payload["n_resource_response_ledger_rows"]
    )
    assert payload["n_prover_adapter_packet_schema_valid"] == payload["n_portable_work_packets"]
    assert payload["n_awaiting_adapter_mapping"] == payload["n_portable_work_packets"]
    assert payload["n_adapter_registry_adapters"] >= 16
    assert payload["n_adapter_registry_ready"] >= 3
    assert (
        payload["n_adapter_registry_row_schema_valid"]
        == payload["n_adapter_registry_adapters"]
    )
    assert payload["n_adapter_registry_row_schema_invalid"] == 0
    assert payload["n_adapter_registry_audit_failed"] == 0
    assert (
        payload["n_adapter_registry_audit_row_schema_valid"]
        == payload["n_adapter_registry_adapters"]
    )
    assert payload["n_adapter_registry_audit_row_schema_invalid"] == 0
    assert (
        payload["n_adapter_registry_audit_jsonl_row_schema_valid"]
        == payload["n_adapter_registry_adapters"]
    )
    assert payload["n_adapter_registry_audit_jsonl_row_schema_invalid"] == 0
    assert (
        payload["n_adapter_registry_required_ids_present"]
        == payload["n_adapter_registry_required_ids"]
    )
    assert payload["n_component_resource_components"] >= 8
    assert payload["n_component_resource_resources"] >= 20
    assert (
        payload["n_component_resource_component_row_schema_valid"]
        == payload["n_component_resource_components"]
    )
    assert payload["n_component_resource_component_row_schema_invalid"] == 0
    assert (
        payload["n_component_resource_resource_row_schema_valid"]
        == payload["n_component_resource_resources"]
    )
    assert payload["n_component_resource_resource_row_schema_invalid"] == 0
    assert payload["n_component_resource_contracts"] == payload["n_component_resource_resources"]
    assert payload["n_component_resource_contracts_ok"] == payload["n_component_resource_contracts"]
    assert (
        payload["n_component_resource_contract_row_schema_valid"]
        == payload["n_component_resource_contracts"]
    )
    assert payload["n_component_resource_contract_row_schema_invalid"] == 0
    assert payload["n_component_resource_execution_plans"] == payload["n_component_resource_components"]
    assert payload["n_component_resource_execution_plans_ok"] == payload["n_component_resource_execution_plans"]
    assert (
        payload["n_component_resource_execution_plan_schema_valid"]
        == payload["n_component_resource_execution_plans"]
    )
    assert payload["n_component_resource_execution_plan_schema_invalid"] == 0
    assert payload["n_component_resource_frontier"] >= 10
    assert payload["n_component_resource_mcp_cli"] >= 5
    assert (
        payload["n_component_resource_resources_with_capability_tags"]
        == payload["n_component_resource_resources"]
    )
    assert (
        payload["n_component_resource_resources_with_validation_signals"]
        == payload["n_component_resource_resources"]
    )
    assert (
        payload["n_component_resource_components_with_quality_signals"]
        == payload["n_component_resource_components"]
    )
    assert (
        payload["n_component_resource_execution_plans_with_quality_gates"]
        == payload["n_component_resource_execution_plans"]
    )
    assert (
        payload["n_component_resource_contracts_with_response_validation_signals"]
        == payload["n_component_resource_contracts"]
    )
    assert payload["n_component_resource_audit_failed"] == 0
    assert (
        payload["n_component_resource_required_components_present"]
        == payload["n_component_resource_required_components"]
    )
    assert (
        payload["n_component_resource_components_with_execution_plan"]
        == payload["n_component_resource_components"]
    )
    assert (
        payload["n_component_resource_audit_component_row_schema_valid"]
        == payload["n_component_resource_components"]
    )
    assert payload["n_component_resource_audit_component_row_schema_invalid"] == 0
    assert (
        payload["n_component_resource_required_resources_present"]
        == payload["n_component_resource_required_resources"]
    )
    assert (
        payload["n_component_resource_audit_resource_row_schema_valid"]
        == payload["n_component_resource_resources"]
    )
    assert payload["n_component_resource_audit_resource_row_schema_invalid"] == 0
    assert payload["n_publication_bundle_audit_failed"] == 0
    assert payload["n_publication_bundle_schema_catalog_entries"] >= 30
    assert payload["n_publication_bundle_schema_catalog_contract_errors"] == 0
    assert payload["publication_bundle_schema_catalog_all_ok"]
    assert (
        payload["n_publication_bundle_execution_plan_schema_valid"]
        == payload["n_publication_bundle_execution_plan_schema_checked"]
        == payload["n_component_resource_execution_plans"]
    )
    assert (
        payload["n_publication_bundle_component_row_schema_valid"]
        == payload["n_publication_bundle_component_row_schema_checked"]
        == payload["n_component_resource_components"]
    )
    assert (
        payload["n_publication_bundle_resource_row_schema_valid"]
        == payload["n_publication_bundle_resource_row_schema_checked"]
        == payload["n_component_resource_resources"]
    )
    assert (
        payload["n_publication_bundle_contract_row_schema_valid"]
        == payload["n_publication_bundle_contract_row_schema_checked"]
        == payload["n_component_resource_contracts"]
    )
    assert (
        payload["n_publication_bundle_prover_adapter_packet_schema_valid"]
        == payload["n_publication_bundle_prover_adapter_packet_schema_checked"]
        == payload["n_portable_work_packets"]
    )
    assert (
        payload["n_publication_bundle_benchmark_route_schema_valid"]
        == payload["n_publication_bundle_benchmark_route_schema_checked"]
        == payload["n_publication_bundle_benchmark_routes"]
    )
    assert (
        payload["n_publication_bundle_optional_evaluation_row_schema_valid"]
        == payload["n_publication_bundle_optional_evaluation_row_schema_checked"]
        == payload["n_evaluation_rows"]
    )
    assert (
        payload["n_publication_bundle_optional_evaluation_ground_truth_file_valid"]
        == payload["n_publication_bundle_optional_evaluation_ground_truth_file_checked"]
        == 2
    )
    assert (
        payload["n_publication_bundle_optional_evaluation_ground_truth_match_valid"]
        == payload["n_publication_bundle_optional_evaluation_ground_truth_match_checked"]
        == payload["n_evaluation_rows"]
    )
    assert (
        payload["n_publication_bundle_optional_evaluation_ground_truth_primitive_valid"]
        == payload[
            "n_publication_bundle_optional_evaluation_ground_truth_primitive_checked"
        ]
        == payload["n_evaluation_rows"]
    )
    assert payload["evaluation_ground_truth_mode"] == "self_labeled_contract_smoke"
    assert payload["n_evaluation_rows"] > 0
    assert payload["n_evaluation_row_schema_valid"] == payload["n_evaluation_rows"]
    assert payload["n_evaluation_row_schema_invalid"] == 0
    assert payload["n_evaluation_matched_ground_truth"] == payload["n_evaluation_rows"]
    assert payload["n_evaluation_missing_ground_truth"] == 0
    assert payload["n_evaluation_alignment_contract_ok"] == payload["n_evaluation_rows"]
    assert payload["n_evaluation_feedback_loop_ready"] == payload["n_evaluation_rows"]
    assert payload["n_evaluation_unaligned_primitives"] == 0
    assert payload["n_evaluation_realization_missing_selected_formal_primitives"] == 0
    assert payload["n_evaluation_realization_missing_delta_alignment_primitives"] == 0
    assert payload["n_evaluation_rows_with_incomplete_cost_hint_baseline_coverage"] == 0
    assert payload["n_evaluation_realization_cost_hint_baseline_primitives"] == 0
    assert payload["n_evaluation_realization_omitted_cost_hint_primitives"] == 0
    assert payload["evaluation_realization_missing_selected_formal_primitives"] == ()
    assert payload["evaluation_realization_missing_delta_alignment_primitives"] == ()
    assert payload["evaluation_realization_cost_hint_baseline_primitives"] == ()
    assert payload["evaluation_realization_omitted_cost_hint_primitives"] == ()
    assert payload["evaluation_realization_missing_primitives_by_route"] == ()
    assert payload["n_evaluation_rows_with_llm_route_planner_trace"] == 1
    assert payload["n_evaluation_rows_with_llm_route_planner_model_tier"] == 1
    assert payload["n_evaluation_rows_with_llm_route_planner_generator_metadata"] == 0
    assert payload["n_evaluation_rows_with_llm_route_planner_request_contract_blocked"] == 0
    assert payload["n_evaluation_rows_with_llm_route_planner_errors"] == 0
    assert payload["n_evaluation_llm_route_planner_errors"] == 0
    assert payload["n_evaluation_llm_route_planner_generation_errors"] == 0
    assert payload["evaluation_by_llm_model_tier"] == {
        "sonnet": {
            "n_rows": 1,
            "n_ok": 1,
            "n_matched_ground_truth": 1,
            "mean_route_recall": 1.0,
            "mean_delta_precision": 1.0,
            "mean_alignment_coverage": 1.0,
            "n_rows_with_generator_metadata": 0,
            "n_rows_with_request_contract_blocked": 0,
            "n_rows_with_errors": 0,
        }
    }
    assert payload["evaluation_by_llm_route_adoption_status"] == {
        "AWAITING_LLM_ROUTE_PLANNER_RESPONSE": {
            "n_rows": 1,
            "n_ok": 1,
            "n_matched_ground_truth": 1,
            "n_route_adoption_blockers": 1,
            "mean_route_recall": 1.0,
            "mean_delta_precision": 1.0,
        }
    }
    assert payload["mean_evaluation_route_recall"] == 1.0
    assert payload["mean_evaluation_alignment_coverage"] == 1.0
    assert (
        payload[
            "n_publication_bundle_optional_interactive_decision_policy_row_schema_valid"
        ]
        == payload[
            "n_publication_bundle_optional_interactive_decision_policy_row_schema_checked"
        ]
        == payload["n_interactive_decision_policy_rows"]
    )
    assert (
        payload[
            "n_publication_bundle_optional_interactive_decision_policy_link_valid"
        ]
        == payload[
            "n_publication_bundle_optional_interactive_decision_policy_link_checked"
        ]
        == payload["n_interactive_decision_policy_rows"] * 4
    )
    assert (
        payload[
            "n_publication_bundle_optional_interactive_session_row_schema_valid"
        ]
        == payload[
            "n_publication_bundle_optional_interactive_session_row_schema_checked"
        ]
        == payload["n_interactive_session_rows"]
    )
    assert (
        payload[
            "n_publication_bundle_optional_interactive_session_resource_response_status_valid"
        ]
        == payload[
            "n_publication_bundle_optional_interactive_session_resource_response_status_checked"
        ]
    )
    assert (
        payload[
            "n_publication_bundle_optional_refinement_evidence_row_schema_valid"
        ]
        == payload[
            "n_publication_bundle_optional_refinement_evidence_row_schema_checked"
        ]
        == payload["n_refinement_evidence_rows"]
    )
    assert (
        payload[
            "n_publication_bundle_optional_refinement_adapter_response_schema_valid"
        ]
        == payload[
            "n_publication_bundle_optional_refinement_adapter_response_schema_checked"
        ]
        == payload["n_refinement_responses"]
    )
    assert (
        payload[
            "n_publication_bundle_optional_local_adapter_response_schema_valid"
        ]
        == payload[
            "n_publication_bundle_optional_local_adapter_response_schema_checked"
        ]
        >= payload["n_local_adapter_merged_responses"]
    )
    assert (
        payload[
            "n_publication_bundle_optional_route_stability_audit_row_schema_valid"
        ]
        == payload[
            "n_publication_bundle_optional_route_stability_audit_row_schema_checked"
        ]
        == payload["n_route_stability_rows"]
    )
    assert (
        payload[
            "n_publication_bundle_optional_route_stability_resource_response_status_valid"
        ]
        == payload[
            "n_publication_bundle_optional_route_stability_resource_response_status_checked"
        ]
    )
    assert (
        payload[
            "n_publication_bundle_optional_route_stability_resource_response_status_checked"
        ]
        >= payload["n_route_stability_rows"]
    )
    assert (
        payload[
            "n_publication_bundle_optional_route_revision_overlay_row_schema_valid"
        ]
        == payload[
            "n_publication_bundle_optional_route_revision_overlay_row_schema_checked"
        ]
        == payload["n_route_revision_overlay_row_schema_valid"]
    )
    assert (
        payload[
            "n_publication_bundle_optional_route_revision_resource_response_evidence_ref_valid"
        ]
        == payload[
            "n_publication_bundle_optional_route_revision_resource_response_evidence_ref_checked"
        ]
    )
    assert (
        payload[
            "n_publication_bundle_optional_route_revision_resource_response_trace_valid"
        ]
        == payload[
            "n_publication_bundle_optional_route_revision_resource_response_trace_checked"
        ]
    )
    assert (
        payload[
            "n_publication_bundle_optional_route_revision_resource_response_status_valid"
        ]
        == payload[
            "n_publication_bundle_optional_route_revision_resource_response_status_checked"
        ]
    )
    assert (
        payload[
            "n_publication_bundle_optional_route_revision_resource_response_status_checked"
        ]
        >= payload["n_route_revision_overlay_row_schema_valid"]
    )
    assert (
        payload[
            "n_publication_bundle_optional_route_replan_handoff_row_schema_valid"
        ]
        == payload[
            "n_publication_bundle_optional_route_replan_handoff_row_schema_checked"
        ]
        == payload["n_route_replan_handoff_rows"]
    )
    assert (
        payload[
            "n_publication_bundle_optional_route_replan_handoff_seed_alignment_valid"
        ]
        == payload[
            "n_publication_bundle_optional_route_replan_handoff_seed_alignment_checked"
        ]
        == payload["n_route_replan_handoff_rows"]
    )
    assert (
        payload["n_publication_bundle_optional_route_replan_handoff_seed_dag_valid"]
        == payload[
            "n_publication_bundle_optional_route_replan_handoff_seed_dag_checked"
        ]
        == payload["n_route_replan_handoff_rows"]
    )
    assert (
        payload[
            "n_publication_bundle_optional_route_replan_handoff_audit_row_schema_valid"
        ]
        == payload[
            "n_publication_bundle_optional_route_replan_handoff_audit_row_schema_checked"
        ]
        == payload["n_route_replan_handoff_audit_checks"]
    )
    assert (
        payload[
            "n_publication_bundle_optional_proof_state_triage_row_schema_valid"
        ]
        == payload[
            "n_publication_bundle_optional_proof_state_triage_row_schema_checked"
        ]
        == payload["n_proof_state_triage_items"]
    )
    assert payload["n_minimal_delta_audit_failed"] == 0
    assert payload["n_minimal_delta_decision_rows"] > 0
    assert (
        payload["n_minimal_delta_decision_row_schema_valid"]
        == payload["n_minimal_delta_decision_rows"]
    )
    assert payload["n_minimal_delta_decision_row_schema_invalid"] == 0
    assert (
        payload["n_minimal_delta_audit_feedback_merged_response_schema_valid"]
        == payload["n_minimal_delta_audit_feedback_merged_responses"]
    )
    assert payload["n_minimal_delta_audit_feedback_merged_response_schema_invalid"] == 0
    assert payload["n_source_grounding_unaccounted"] == 0
    assert payload["n_source_grounding_source_backed"] > 0
    assert payload["n_source_grounding_row_schema_valid"] == payload["n_source_grounding_rows"]
    assert payload["n_source_grounding_row_schema_invalid"] == 0
    assert payload["n_dominated_route_witnesses"] == 0
    assert (
        payload["n_prover_adapter_response_validation_row_schema_valid"]
        == payload["n_portable_work_packets"]
    )
    assert payload["n_prover_adapter_response_validation_row_schema_invalid"] == 0
    assert payload["n_prover_adapter_feedback_generated_responses"] > 0
    assert (
        payload["n_prover_adapter_feedback_merged_response_schema_valid"]
        == payload["n_prover_adapter_feedback_merged_responses"]
    )
    assert payload["n_prover_adapter_feedback_merged_response_schema_invalid"] == 0
    assert (
        payload[
            "n_publication_bundle_optional_prover_adapter_feedback_response_schema_valid"
        ]
        == payload[
            "n_publication_bundle_optional_prover_adapter_feedback_response_schema_checked"
        ]
        == (
            payload["n_prover_adapter_feedback_generated_responses"]
            + payload["n_prover_adapter_feedback_merged_responses"]
        )
    )
    assert payload["n_cross_prover_targets_ok"] == payload["n_cross_prover_targets"] == 4
    assert payload["n_cross_prover_total_packets"] == 4 * payload["n_portable_work_packets"]
    assert payload["n_cross_prover_total_packet_schema_valid"] == payload["n_cross_prover_total_packets"]
    assert payload["n_cross_prover_packets_schema_invalid"] == 0
    assert (
        payload["n_cross_prover_matrix_row_schema_valid"]
        == payload["n_cross_prover_targets"]
    )
    assert payload["n_cross_prover_matrix_row_schema_invalid"] == 0
    assert (
        payload["n_cross_prover_packet_row_schema_valid"]
        == payload["n_cross_prover_total_packets"]
    )
    assert payload["n_cross_prover_packet_row_schema_invalid"] == 0
    assert (
        payload["n_cross_prover_response_validation_row_schema_valid"]
        == payload["n_cross_prover_total_packets"]
    )
    assert payload["n_cross_prover_response_validation_row_schema_invalid"] == 0
    assert payload["n_cross_prover_total_packets_with_alignment"] == payload["n_cross_prover_total_packets"]
    assert payload["n_cross_prover_packets_missing_alignment"] == 0
    assert (
        payload["n_cross_prover_total_packets_with_standalone_input_trace"]
        == payload["n_cross_prover_total_packets"]
    )
    assert payload["n_cross_prover_packets_missing_standalone_input_trace"] == 0
    assert payload["n_cross_prover_total_packets_with_replan_metadata_trace"] >= 0
    assert payload["n_cross_prover_rejected"] == 0
    assert payload["cross_prover_packet_count_consistent"]
    assert payload["cross_prover_alignment_packet_count_consistent"]
    assert payload["cross_prover_standalone_input_trace_packet_count_consistent"]
    assert (
        payload["n_publication_bundle_optional_cross_prover_packet_trace_valid"]
        == payload["n_publication_bundle_optional_cross_prover_packet_trace_checked"]
        == payload["n_cross_prover_total_packets"]
    )
    assert payload["n_cross_prover_target_summary_rows"] == payload["n_cross_prover_targets"]
    assert payload["n_cross_prover_target_summary_contract_errors"] == 0
    assert payload["n_refinement_items"] > 0
    assert payload["n_refinement_ready"] == payload["n_refinement_items"]
    assert payload["n_refinement_item_schema_valid"] == payload["n_refinement_items"]
    assert payload["n_refinement_item_schema_invalid"] == 0
    assert payload["n_refinement_formal_library_grounding_items"] > 0
    assert payload["n_refinement_lean_library_grounding_items"] == 0
    assert payload["n_refinement_responses"] == payload["n_refinement_items"]
    assert payload["n_refinement_adapter_formal_grounding_responses"] == payload[
        "n_refinement_formal_library_grounding_items"
    ]
    assert payload["n_refinement_adapter_lean_grounding_responses"] == 0
    assert (
        payload["n_refinement_adapter_response_schema_valid"]
        == payload["n_refinement_responses"]
    )
    assert payload["n_refinement_adapter_response_schema_invalid"] == 0
    assert payload["n_local_literature_responses"] > 0
    assert payload["n_local_formal_source_responses"] > 0
    assert payload["n_local_formal_source_formal_grounding_rows"] == payload[
        "n_local_formal_source_responses"
    ]
    assert payload["n_local_formal_source_legacy_lean_grounding_rows"] == 0
    assert (
        payload["local_formal_source_adapter_legacy_field_aliases"]
        == LEGACY_FORMAL_SOURCE_ADAPTER_FIELD_ALIASES
    )
    assert (
        payload["n_local_formal_source_legacy_lean_declaration_hit_responses"]
        == payload["n_local_formal_source_responses"]
    )
    assert payload["n_local_proof_state_responses"] > 0
    assert (
        payload["n_local_proof_state_target_proof_state_feedback_rows"]
        == payload["n_local_proof_state_responses"]
    )
    assert (
        payload["n_local_proof_state_skipped_non_target_proof_state_feedback_rows"]
        == 0
    )
    assert (
        payload["n_local_proof_state_target_prover_scaffold_accepted"]
        + payload["n_local_proof_state_target_prover_failed"]
        + payload["n_local_proof_state_target_prover_unavailable"]
        + payload["n_local_proof_state_non_target_prover_skeleton"]
        + payload["n_local_proof_state_placeholder_blocked"]
        + payload["n_local_proof_state_formal_gap_scaffold_blocked"]
        + payload["n_local_proof_state_missing_skeleton"]
        == payload["n_local_proof_state_responses"]
    )
    assert payload["n_local_proof_state_target_prover_unavailable"] == payload[
        "n_local_proof_state_unavailable"
    ]
    assert (
        payload["n_local_literature_response_schema_valid"]
        == payload["n_local_literature_responses"]
    )
    assert payload["n_local_literature_response_schema_invalid"] == 0
    assert (
        payload["n_local_formal_source_response_schema_valid"]
        == payload["n_local_formal_source_responses"]
    )
    assert payload["n_local_formal_source_response_schema_invalid"] == 0
    assert (
        payload["n_local_proof_state_response_schema_valid"]
        == payload["n_local_proof_state_responses"]
    )
    assert payload["n_local_proof_state_response_schema_invalid"] == 0
    assert payload["n_local_adapter_response_schema_invalid"] == 0
    assert payload["n_local_adapter_merged_responses"] == payload["n_refinement_items"]
    assert (
        payload["n_local_adapter_merged_response_schema_valid"]
        == payload["n_local_adapter_merged_responses"]
    )
    assert payload["n_local_adapter_merged_response_schema_invalid"] == 0
    assert payload["n_refinement_contract_ok"] == payload["n_refinement_items"]
    assert payload["n_refinement_response_schema_valid"] == payload["n_refinement_responses"]
    assert payload["n_refinement_response_schema_invalid"] == 0
    assert payload["n_refinement_evidence_row_schema_valid"] == payload[
        "n_refinement_evidence_rows"
    ]
    assert payload["n_refinement_evidence_row_schema_invalid"] == 0
    assert payload["n_refinement_evidence_formal_grounding"] == payload[
        "n_refinement_formal_library_grounding_items"
    ]
    assert payload["n_refinement_evidence_lean_grounding"] == 0
    assert payload["n_routes_with_revision"] > 0
    assert payload["n_route_revision_overlay_row_schema_valid"] >= payload["n_routes_with_revision"]
    assert payload["n_route_revision_overlay_row_schema_invalid"] == 0
    assert payload["n_route_stability_needs_expansion"] > 0
    assert payload["n_route_stability_row_schema_valid"] == payload[
        "n_route_stability_rows"
    ]
    assert payload["n_route_stability_row_schema_invalid"] == 0
    assert payload["n_routes_requiring_replan"] > 0
    assert payload["n_replan_seed_routes"] > 0
    assert payload["n_route_replan_handoff_audit_failed"] == 0
    assert (
        payload["n_route_replan_handoff_audit_row_schema_valid"]
        == payload["n_route_replan_handoff_audit_checks"]
    )
    assert payload["n_route_replan_handoff_audit_row_schema_invalid"] == 0
    assert payload["route_replan_roundtrip_all_ok"]
    assert payload["n_route_replan_handoff_row_schema_valid"] == payload["n_route_replan_handoff_rows"]
    assert payload["n_route_replan_handoff_row_schema_invalid"] == 0
    assert payload["n_route_replan_roundtrip_goal_plans"] == payload["n_replan_seed_routes"]
    assert payload["n_route_replan_alignment_edges"] >= payload["n_route_replan_handoff_rows"]
    assert (
        payload["n_route_replan_revised_informal_knowledge_dag_nodes"]
        >= payload["n_route_replan_handoff_rows"]
    )
    assert (
        payload["n_route_replan_revised_formal_realization_dag_nodes"]
        >= payload["n_route_replan_handoff_rows"]
    )
    assert (
        payload["n_route_replan_revised_lean_realization_dag_nodes"]
        >= payload["n_route_replan_handoff_rows"]
    )
    assert payload["n_route_replan_revised_formal_realization_dag_nodes"] == payload[
        "n_route_replan_revised_lean_realization_dag_nodes"
    ]
    assert payload["n_route_replan_unaligned_primitives"] == 0
    assert payload["n_route_replan_roundtrip_alignment_edges"] >= payload["n_replan_seed_routes"]
    assert (
        payload["n_route_replan_roundtrip_standalone_input_traces"]
        == payload["n_replan_seed_routes"]
    )
    assert (
        payload[
            "n_route_replan_roundtrip_standalone_input_traces_with_replan_metadata"
        ]
        == payload["n_replan_seed_routes"]
    )
    assert (
        payload[
            "n_route_replan_roundtrip_standalone_input_trace_llm_route_planner_hook_traces"
        ]
        >= 0
    )
    assert (
        payload[
            "n_route_replan_roundtrip_standalone_input_traces_with_llm_route_planner_hook_traces"
        ]
        >= 0
    )
    assert payload["n_proof_state_triage_items"] > 0
    assert payload["n_proof_state_triage_row_schema_valid"] == payload[
        "n_proof_state_triage_items"
    ]
    assert payload["n_proof_state_triage_row_schema_invalid"] == 0
    assert payload["n_proof_state_triage_target_prover_failed_items"] >= payload[
        "n_proof_state_triage_local_lean_failed_items"
    ]
    assert payload["n_proof_state_triage_non_target_prover_skeleton_items"] >= payload[
        "n_proof_state_triage_non_lean_skeleton_items"
    ]
    assert payload["n_interactive_session_rows"] > 0
    assert payload["n_interactive_session_row_schema_valid"] == payload["n_interactive_session_rows"]
    assert payload["n_interactive_session_row_schema_invalid"] == 0
    assert payload["n_interactive_decision_policy_rows"] == payload["n_interactive_session_rows"]
    assert (
        payload["n_interactive_decision_policy_row_schema_valid"]
        == payload["n_interactive_decision_policy_rows"]
    )
    assert payload["n_interactive_decision_policy_row_schema_invalid"] == 0
    assert (
        payload["n_interactive_decision_policy_rows_with_resource_contracts"]
        == payload["n_interactive_decision_policy_rows"]
    )
    assert (
        payload["n_interactive_decision_policy_rows_with_frontier_resources"]
        == payload["n_interactive_decision_policy_rows"]
    )
    assert (
        payload["n_interactive_decision_policy_rows_with_required_quality_signals"]
        == payload["n_interactive_decision_policy_rows"]
    )
    assert (
        payload["n_interactive_decision_policy_rows_with_quality_gates"]
        == payload["n_interactive_decision_policy_rows"]
    )
    assert (
        payload["n_interactive_decision_policy_rows_with_response_validation_signals"]
        == payload["n_interactive_decision_policy_rows"]
    )
    assert payload["n_interactive_session_replan"] == 0
    assert payload["n_interactive_session_run_formal_grounding"] >= 0
    assert payload["n_interactive_session_run_lean_grounding"] == 0
    assert payload["n_interactive_session_waiting_for_adapter_responses"] > 0
    assert payload["n_interactive_session_rows_requiring_replan"] > 0
    assert payload["n_ablation_variants"] == 5
    assert payload["n_ablation_ok"] == payload["n_ablation_variants"]
    assert payload["n_ablation_row_schema_valid"] == payload["n_ablation_variants"]
    assert payload["n_ablation_row_schema_invalid"] == 0
    assert payload["ablation_best_variant_by_route_recall"] == "full_planner_observed"
    assert (
        payload["n_publication_bundle_optional_ablation_study_row_schema_valid"]
        == payload["n_publication_bundle_optional_ablation_study_row_schema_checked"]
        == payload["n_ablation_variants"]
    )
    assert payload["n_kernel_verified_claims_rejected"] == 0
    assert "not theorem proof evidence" in payload["proof_evidence_boundary"]
    stage_names = {stage["stage_name"] for stage in payload["stages"]}
    assert stage_names == {
        "formalization_gap_planner_target_intake",
        "formalization_gap_planner_llm_route_planner",
        "goal_conditioned_minimal_formalization_plan",
        "formalization_gap_planner_portable_plan_audit",
        "formalization_gap_planner_library_coverage_map",
        "formalization_gap_planner_primitive_action_queue",
        "formalization_gap_planner_minimal_delta_audit",
        "formalization_gap_planner_source_grounding_audit",
        "formalization_gap_planner_evaluation",
        "formalization_gap_planner_prover_adapter_contract",
        "formalization_gap_planner_adapter_registry",
        "formalization_gap_planner_adapter_registry_audit",
        "formalization_gap_planner_component_resource_registry",
        "formalization_gap_planner_component_resource_registry_audit",
        "formalization_gap_planner_action_resource_plan",
        "formalization_gap_planner_resource_request_queue",
        "formalization_gap_planner_resource_response_ledger",
        "formalization_gap_planner_refinement_queue",
        "formalization_gap_planner_refinement_adapter_responses",
        "formalization_gap_planner_minimal_delta_audit_feedback_adapter",
        "formalization_gap_planner_local_literature_adapter",
        "formalization_gap_planner_local_formal_source_adapter",
        "formalization_gap_planner_local_proof_state_adapter",
        "formalization_gap_planner_prover_adapter_feedback_adapter",
        "formalization_gap_planner_refinement_evidence",
        "formalization_gap_planner_route_revision_overlay",
        "formalization_gap_planner_route_stability_audit",
        "formalization_gap_planner_route_replan_handoff",
        "formalization_gap_planner_route_replan_handoff_audit",
        "formalization_gap_planner_feedback_llm_route_planner",
        "formalization_gap_planner_proof_state_triage",
        "formalization_gap_planner_interactive_session",
        "formalization_gap_planner_ablation_study",
        "formalization_gap_planner_cross_prover_matrix_audit",
        "formalization_gap_planner_publication_bundle",
        "formalization_gap_planner_publication_bundle_audit",
    }
    assert all(stage["proof_boundary_ok"] for stage in payload["stages"])
    stage_by_name = {stage["stage_name"]: stage for stage in payload["stages"]}
    refinement_queue_summary = stage_by_name[
        "formalization_gap_planner_refinement_queue"
    ]["summary"]
    refinement_adapter_summary = stage_by_name[
        "formalization_gap_planner_refinement_adapter_responses"
    ]["summary"]
    refinement_evidence_summary = stage_by_name[
        "formalization_gap_planner_refinement_evidence"
    ]["summary"]
    local_proof_state_summary = stage_by_name[
        "formalization_gap_planner_local_proof_state_adapter"
    ]["summary"]
    proof_state_triage_summary = stage_by_name[
        "formalization_gap_planner_proof_state_triage"
    ]["summary"]
    interactive_summary = stage_by_name["formalization_gap_planner_interactive_session"][
        "summary"
    ]
    handoff_summary = stage_by_name["formalization_gap_planner_route_replan_handoff"][
        "summary"
    ]
    assert handoff_summary["n_revised_formal_realization_dag_nodes"] == payload[
        "n_route_replan_revised_formal_realization_dag_nodes"
    ]
    assert handoff_summary["n_revised_lean_realization_dag_nodes"] == payload[
        "n_route_replan_revised_lean_realization_dag_nodes"
    ]
    assert refinement_queue_summary["n_formal_library_grounding_items"] == payload[
        "n_refinement_formal_library_grounding_items"
    ]
    assert refinement_queue_summary["n_lean_library_grounding_items"] == payload[
        "n_refinement_lean_library_grounding_items"
    ]
    assert refinement_adapter_summary["n_formal_grounding_responses"] == payload[
        "n_refinement_adapter_formal_grounding_responses"
    ]
    assert refinement_adapter_summary["n_lean_grounding_responses"] == payload[
        "n_refinement_adapter_lean_grounding_responses"
    ]
    assert refinement_evidence_summary["n_formal_grounding_evidence"] == payload[
        "n_refinement_evidence_formal_grounding"
    ]
    assert refinement_evidence_summary["n_lean_grounding_evidence"] == payload[
        "n_refinement_evidence_lean_grounding"
    ]
    assert local_proof_state_summary["n_target_prover_failed"] == payload[
        "n_local_proof_state_target_prover_failed"
    ]
    assert local_proof_state_summary["n_target_prover_unavailable"] == payload[
        "n_local_proof_state_target_prover_unavailable"
    ]
    assert local_proof_state_summary["n_non_target_prover_skeleton"] == payload[
        "n_local_proof_state_non_target_prover_skeleton"
    ]
    assert local_proof_state_summary["n_target_proof_state_feedback_rows"] == payload[
        "n_local_proof_state_target_proof_state_feedback_rows"
    ]
    assert (
        local_proof_state_summary["n_skipped_non_target_proof_state_feedback_rows"]
        == payload[
            "n_local_proof_state_skipped_non_target_proof_state_feedback_rows"
        ]
    )
    assert local_proof_state_summary["n_local_lean_unavailable"] == payload[
        "n_local_proof_state_unavailable"
    ]
    assert proof_state_triage_summary["n_target_prover_failed_items"] == payload[
        "n_proof_state_triage_target_prover_failed_items"
    ]
    assert proof_state_triage_summary["n_non_target_prover_skeleton_items"] == payload[
        "n_proof_state_triage_non_target_prover_skeleton_items"
    ]
    assert proof_state_triage_summary["n_local_lean_failed_items"] == payload[
        "n_proof_state_triage_local_lean_failed_items"
    ]
    assert proof_state_triage_summary["n_non_lean_skeleton_items"] == payload[
        "n_proof_state_triage_non_lean_skeleton_items"
    ]
    assert interactive_summary["n_run_formal_grounding"] == payload[
        "n_interactive_session_run_formal_grounding"
    ]
    assert interactive_summary["n_run_lean_grounding"] == payload[
        "n_interactive_session_run_lean_grounding"
    ]
    assert (
        out_dir / "formalization_gap_planner_reuse_smoke_manifest.json"
    ).exists()
    assert (
        out_dir
        / "formalization_gap_planner_publication_bundle"
        / "formalization_gap_planner_publication_bundle_manifest.json"
    ).exists()
    assert (
        out_dir
        / "formalization_gap_planner_publication_bundle_audit"
        / "formalization_gap_planner_publication_bundle_audit_manifest.json"
    ).exists()
    assert Path(payload["artifacts"]["publication_bundle_schema_catalog"]).exists()
    assert Path(payload["artifacts"]["publication_bundle_schema_catalog_schema"]).exists()
    assert (
        out_dir
        / "formalization_gap_planner_adapter_registry_audit"
        / "formalization_gap_planner_adapter_registry_audit_manifest.json"
    ).exists()
    assert (
        out_dir
        / "formalization_gap_planner_component_resource_registry"
        / "formalization_gap_planner_component_resource_registry_manifest.json"
    ).exists()
    assert (
        out_dir
        / "formalization_gap_planner_component_resource_registry"
        / "formalization_gap_planner_component_resource_execution_plans.jsonl"
    ).exists()
    assert (
        out_dir
        / "formalization_gap_planner_component_resource_registry_audit"
        / "formalization_gap_planner_component_resource_registry_audit_manifest.json"
    ).exists()
    assert (
        out_dir
        / "formalization_gap_planner_cross_prover_matrix_audit"
        / "formalization_gap_planner_cross_prover_packets.jsonl"
    ).exists()
    assert Path(payload["artifacts"]["prover_adapter_packet_schema"]).exists()
    assert Path(payload["artifacts"]["prover_adapter_response_schema"]).exists()
    assert Path(
        payload["artifacts"]["prover_adapter_response_validation_row_schema"]
    ).exists()
    assert Path(payload["artifacts"]["route_alignment_edge_schema"]).exists()
    assert Path(
        payload["artifacts"]["portable_plan_audit_route_alignment_edge_schema"]
    ).exists()
    assert Path(payload["artifacts"]["portable_plan_audit_row_schema"]).exists()
    assert Path(payload["artifacts"]["library_coverage_map_manifest"]).exists()
    assert Path(payload["artifacts"]["library_coverage_map_jsonl"]).exists()
    assert Path(payload["artifacts"]["library_coverage_map_row_schema"]).exists()
    assert Path(payload["artifacts"]["primitive_action_queue_manifest"]).exists()
    assert Path(payload["artifacts"]["primitive_action_queue_jsonl"]).exists()
    assert Path(payload["artifacts"]["primitive_action_queue_row_schema"]).exists()
    assert Path(payload["artifacts"]["action_resource_plan_manifest"]).exists()
    assert Path(payload["artifacts"]["action_resource_plan_jsonl"]).exists()
    assert Path(payload["artifacts"]["action_resource_plan_row_schema"]).exists()
    assert Path(payload["artifacts"]["resource_response_ledger_manifest"]).exists()
    assert Path(payload["artifacts"]["resource_response_ledger_jsonl"]).exists()
    assert Path(payload["artifacts"]["resource_response_schema"]).exists()
    assert Path(payload["artifacts"]["resource_response_ledger_row_schema"]).exists()
    assert Path(payload["artifacts"]["resource_response_ledger_report"]).exists()
    assert Path(payload["artifacts"]["minimal_delta_decisions_jsonl"]).exists()
    assert Path(payload["artifacts"]["minimal_delta_decision_row_schema"]).exists()
    assert Path(payload["artifacts"]["source_grounding_row_schema"]).exists()
    assert Path(payload["evaluation_ground_truth_path"]).exists()
    assert Path(payload["artifacts"]["reuse_smoke_route_truth"]).exists()
    assert Path(payload["artifacts"]["evaluation_manifest"]).exists()
    assert Path(payload["artifacts"]["evaluation_jsonl"]).exists()
    assert Path(payload["artifacts"]["evaluation_row_schema"]).exists()
    assert Path(payload["artifacts"]["evaluation_ground_truth"]).exists()
    assert Path(payload["artifacts"]["evaluation_report"]).exists()
    assert Path(payload["artifacts"]["adapter_registry_jsonl"]).exists()
    assert Path(payload["artifacts"]["adapter_registry_row_schema"]).exists()
    assert Path(payload["artifacts"]["component_resource_resources_jsonl"]).exists()
    assert Path(payload["artifacts"]["component_resource_resource_row_schema"]).exists()
    assert Path(payload["artifacts"]["component_resource_component_row_schema"]).exists()
    assert Path(payload["artifacts"]["component_resource_execution_plan_schema"]).exists()
    assert Path(payload["artifacts"]["component_resource_contracts_jsonl"]).exists()
    assert Path(payload["artifacts"]["component_resource_contract_row_schema"]).exists()
    assert Path(payload["artifacts"]["cross_prover_matrix_row_schema"]).exists()
    assert Path(payload["artifacts"]["cross_prover_packet_schema"]).exists()
    assert Path(payload["artifacts"]["cross_prover_response_validation_jsonl"]).exists()
    assert Path(
        payload["artifacts"]["cross_prover_response_validation_row_schema"]
    ).exists()
    assert Path(payload["artifacts"]["cross_prover_target_summary"]).exists()
    assert Path(payload["artifacts"]["cross_prover_target_summary_schema"]).exists()
    assert Path(payload["artifacts"]["refinement_adapter_response_schema"]).exists()
    assert Path(payload["artifacts"]["local_literature_response_schema"]).exists()
    assert Path(payload["artifacts"]["local_formal_source_response_schema"]).exists()
    assert Path(payload["artifacts"]["local_proof_state_response_schema"]).exists()
    assert Path(payload["artifacts"]["prover_adapter_feedback_adapter_manifest"]).exists()
    assert Path(payload["artifacts"]["prover_adapter_feedback_responses_jsonl"]).exists()
    assert Path(
        payload["artifacts"]["prover_adapter_feedback_merged_responses_jsonl"]
    ).exists()
    assert Path(payload["artifacts"]["prover_adapter_feedback_response_schema"]).exists()
    assert (
        out_dir
        / "formalization_gap_planner_source_grounding_audit"
        / "formalization_gap_planner_source_grounding_audit_manifest.json"
    ).exists()
    assert (
        out_dir
        / "formalization_gap_planner_refinement_queue"
        / "formalization_gap_planner_refinement_queue_manifest.json"
    ).exists()
    assert Path(payload["artifacts"]["refinement_work_item_schema"]).exists()
    assert (
        out_dir
        / "formalization_gap_planner_refinement_adapter"
        / "formalization_gap_planner_refinement_evidence_responses.jsonl"
    ).exists()
    assert Path(payload["artifacts"]["refinement_tool_response_schema"]).exists()
    assert Path(payload["artifacts"]["refinement_evidence_row_schema"]).exists()
    assert (
        out_dir
        / "formalization_gap_planner_local_literature_adapter"
        / "formalization_gap_planner_local_literature_adapter_manifest.json"
    ).exists()
    assert (
        out_dir
        / "formalization_gap_planner_local_formal_source_adapter"
        / "formalization_gap_planner_local_formal_source_adapter_manifest.json"
    ).exists()
    assert (
        out_dir
        / "formalization_gap_planner_local_proof_state_adapter"
        / "formalization_gap_planner_local_proof_state_adapter_manifest.json"
    ).exists()
    assert (
        out_dir
        / "formalization_gap_planner_route_stability_audit"
        / "formalization_gap_planner_route_stability_audit_manifest.json"
    ).exists()
    assert Path(payload["artifacts"]["route_revision_overlay_row_schema"]).exists()
    assert Path(payload["artifacts"]["route_stability_audit_row_schema"]).exists()
    assert (
        out_dir
        / "formalization_gap_planner_route_replan_handoff"
        / "formalization_gap_planner_route_replan_standalone_seed.json"
    ).exists()
    assert (
        out_dir
        / "formalization_gap_planner_route_replan_handoff"
        / "formalization_gap_planner_route_replan_standalone_seed.schema.json"
    ).exists()
    assert Path(payload["artifacts"]["route_replan_handoff_row_schema"]).exists()
    assert Path(payload["artifacts"]["route_replan_standalone_seed_schema"]).exists()
    assert (
        out_dir
        / "formalization_gap_planner_route_replan_handoff_audit"
        / "formalization_gap_planner_route_replan_handoff_audit_manifest.json"
    ).exists()
    assert Path(payload["artifacts"]["route_replan_handoff_audit_row_schema"]).exists()
    feedback_request_rows = [
        json.loads(line)
        for line in Path(
            payload["artifacts"]["feedback_llm_route_planner_requests_jsonl"]
        ).read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert feedback_request_rows
    feedback_context = feedback_request_rows[0]["context_packet"]
    assert feedback_context["library_coverage_rows"]
    assert feedback_context["source_grounding_rows"]
    assert feedback_context["refinement_evidence_rows"]
    assert feedback_context["route_revision_overlay_rows"]
    assert feedback_context["interactive_session_rows"]
    assert feedback_context["interactive_decision_policy_rows"]
    assert feedback_context["residual_goals"]
    assert (
        out_dir
        / "formalization_gap_planner_publication_bundle"
        / "artifacts"
        / "formalization_gap_planner_library_coverage_map"
        / "formalization_gap_planner_library_coverage_map_manifest.json"
    ).exists()
    assert (
        out_dir
        / "formalization_gap_planner_publication_bundle"
        / "artifacts"
        / "formalization_gap_planner_primitive_action_queue"
        / "formalization_gap_planner_primitive_action_queue_manifest.json"
    ).exists()
    assert (
        out_dir
        / "formalization_gap_planner_publication_bundle"
        / "artifacts"
        / "formalization_gap_planner_action_resource_plan"
        / "formalization_gap_planner_action_resource_plan_manifest.json"
    ).exists()
    assert (
        out_dir
        / "formalization_gap_planner_publication_bundle"
        / "artifacts"
        / "formalization_gap_planner_resource_response_ledger"
        / "formalization_gap_planner_resource_response_ledger_manifest.json"
    ).exists()
    assert (
        out_dir
        / "formalization_gap_planner_publication_bundle"
        / "artifacts"
        / "formalization_gap_planner_adapter_registry_audit"
        / "formalization_gap_planner_adapter_registry_audit_manifest.json"
    ).exists()
    assert (
        out_dir
        / "formalization_gap_planner_publication_bundle"
        / "artifacts"
        / "formalization_gap_planner_component_resource_registry_audit"
        / "formalization_gap_planner_component_resource_registry_audit_manifest.json"
    ).exists()
    assert (
        Path(payload["artifacts"]["component_resource_execution_plans_jsonl"]).exists()
    )
    assert (
        out_dir
        / "formalization_gap_planner_route_replan_handoff_audit"
        / "formalization_gap_planner_route_replan_roundtrip_plan"
        / "goal_conditioned_minimal_formalization_plan_manifest.json"
    ).exists()
    assert (
        out_dir
        / "formalization_gap_planner_interactive_session"
        / "formalization_gap_planner_interactive_session_manifest.json"
    ).exists()
    assert (
        out_dir
        / "formalization_gap_planner_publication_bundle"
        / "artifacts"
        / "formalization_gap_planner_feedback_llm_route_planner"
        / "formalization_gap_planner_llm_route_planner_manifest.json"
    ).exists()
    assert (
        out_dir
        / "formalization_gap_planner_publication_bundle"
        / "artifacts"
        / "formalization_gap_planner_feedback_llm_route_planner"
        / "formalization_gap_planner_llm_route_planner_requests.jsonl"
    ).exists()
    assert Path(payload["artifacts"]["interactive_session_row_schema"]).exists()
    assert Path(payload["artifacts"]["interactive_decision_policy_jsonl"]).exists()
    assert Path(payload["artifacts"]["interactive_decision_policy_row_schema"]).exists()
    interactive_policy_rows = [
        json.loads(line)
        for line in Path(payload["artifacts"]["interactive_decision_policy_jsonl"])
        .read_text(encoding="utf-8")
        .splitlines()
        if line.strip()
    ]
    assert interactive_policy_rows
    assert all(row["resource_contract_ids"] for row in interactive_policy_rows)
    assert all(row["frontier_escalation_resource_ids"] for row in interactive_policy_rows)
    assert Path(payload["artifacts"]["ablation_study_manifest"]).exists()
    assert Path(payload["artifacts"]["ablation_study_jsonl"]).exists()
    assert Path(payload["artifacts"]["ablation_study_row_schema"]).exists()
    assert Path(payload["artifacts"]["ablation_study_report"]).exists()
    assert Path(payload["artifacts"]["proof_state_triage_row_schema"]).exists()
    assert (
        out_dir
        / "formalization_gap_planner_publication_bundle"
        / "artifacts"
        / "formalization_gap_planner_evaluation"
        / "formalization_gap_planner_evaluation_ground_truth.json"
    ).exists()
    assert (
        out_dir
        / "formalization_gap_planner_publication_bundle"
        / "artifacts"
        / "formalization_gap_planner_local_literature_adapter"
        / "formalization_gap_planner_local_literature_adapter_manifest.json"
    ).exists()
    assert (
        out_dir
        / "formalization_gap_planner_publication_bundle"
        / "artifacts"
        / "formalization_gap_planner_local_formal_source_adapter"
        / "formalization_gap_planner_local_formal_source_adapter_manifest.json"
    ).exists()
    assert (
        out_dir
        / "formalization_gap_planner_publication_bundle"
        / "artifacts"
        / "formalization_gap_planner_local_proof_state_adapter"
        / "formalization_gap_planner_local_proof_state_adapter_manifest.json"
    ).exists()
    assert (
        out_dir
        / "formalization_gap_planner_publication_bundle"
        / "artifacts"
        / "formalization_gap_planner_route_replan_handoff"
        / "formalization_gap_planner_route_replan_handoff_manifest.json"
    ).exists()
    assert (
        out_dir
        / "formalization_gap_planner_publication_bundle"
        / "artifacts"
        / "formalization_gap_planner_route_replan_handoff_audit"
        / "formalization_gap_planner_route_replan_handoff_audit_manifest.json"
    ).exists()
    assert (
        out_dir
        / "formalization_gap_planner_publication_bundle"
        / "artifacts"
        / "formalization_gap_planner_proof_state_triage"
        / "formalization_gap_planner_proof_state_triage_manifest.json"
    ).exists()
    assert (
        out_dir
        / "formalization_gap_planner_publication_bundle"
        / "artifacts"
        / "formalization_gap_planner_interactive_session"
        / "formalization_gap_planner_interactive_session_manifest.json"
    ).exists()


def test_reuse_smoke_surfaces_mixed_source_target_distribution() -> None:
    root = Path("runs/test_formalization_gap_planner_reuse_smoke_mixed_targets")
    input_path = root / "target_request.json"
    out_dir = root / "reuse_smoke"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "component_name": "formalization_gap_planner_target_intake",
                "library_snapshot_ref": "portable:probability-snapshots",
                "domain": "distribution-free prediction",
                "targets": [
                    {
                        "target_prover_family": "lean4",
                        "target_id": "lean_rank_bound",
                        "title": "Lean finite-rank route",
                        "theorem_statement": (
                            "Exchangeability implies a finite-rank coverage bound."
                        ),
                        "desired_theorem_shape": "finite-rank coverage bound",
                        "known_proof_sources": ["conformal prediction textbook"],
                        "candidate_primitives": [
                            {
                                "primitive": "exchangeability",
                                "coverage_status": "exact_exists",
                                "candidate_declarations": [
                                    "Probability.exchangeable"
                                ],
                            }
                        ],
                    },
                    {
                        "target_prover_family": "rocq",
                        "target_id": "rocq_rank_bound",
                        "title": "Rocq finite-rank route",
                        "theorem_statement": (
                            "Exchangeability implies a finite-rank coverage bound."
                        ),
                        "desired_theorem_shape": "finite-rank coverage bound",
                        "known_proof_sources": ["conformal prediction textbook"],
                        "candidate_primitives": [
                            {
                                "primitive": "exchangeability",
                                "coverage_status": "exact_exists",
                                "candidate_declarations": [
                                    "Rocq.Probability.exchangeable"
                                ],
                            }
                        ],
                    },
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    payload = run_formalization_gap_planner_reuse_smoke(
        input_path,
        out_dir,
        target_prover_family="rocq",
        target_library_snapshot_ref="rocq:reuse-smoke-mixed",
    )

    assert payload["all_ok"]
    assert payload["source_target_prover_family"] == "mixed:lean4,rocq"
    assert payload["n_source_target_prover_families"] == 2
    assert payload["source_by_target_prover_family"] == {"lean4": 1, "rocq": 1}
    goal_plan_stage = next(
        stage
        for stage in payload["stages"]
        if stage["stage_name"] == "goal_conditioned_minimal_formalization_plan"
    )
    assert goal_plan_stage["summary"]["target_prover_family"] == "mixed:lean4,rocq"
    assert goal_plan_stage["summary"]["n_target_prover_families"] == 2
    assert goal_plan_stage["summary"]["by_target_prover_family"] == {
        "lean4": 1,
        "rocq": 1,
    }
    report_text = (
        out_dir / "formalization_gap_planner_reuse_smoke.md"
    ).read_text(encoding="utf-8")
    assert (
        "Source prover targets: `mixed:lean4,rocq` families=2 "
        "by={'lean4': 1, 'rocq': 1}"
    ) in report_text


def test_reuse_smoke_consumes_reviewed_llm_route_response_end_to_end() -> None:
    root = Path("runs/test_formalization_gap_planner_reuse_smoke_llm_static")
    input_path = root / "target_request.json"
    response_path = root / "reviewed_llm_response.json"
    feedback_response_path = root / "reviewed_feedback_llm_response.json"
    out_dir = root / "reuse_smoke"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "component_name": "formalization_gap_planner_target_intake",
                "target_prover_family": "lean4",
                "library_snapshot_ref": "mathlib4:reuse-smoke-llm-static",
                "target_id": "split_conformal_coverage_static_llm",
                "title": "Split conformal finite-sample coverage static LLM",
                "domain": "distribution-free prediction",
                "theorem_statement": (
                    "For exchangeable calibration and test scores, split "
                    "conformal prediction has finite sample marginal coverage."
                ),
                "objects": ["calibration scores", "test score"],
                "assumptions": [
                    "exchangeable calibration and test scores",
                    "finite calibration sample",
                ],
                "statistical_procedure": "split conformal prediction set",
                "desired_conclusion": "finite sample marginal coverage inequality",
                "desired_theorem_shape": "coverage probability lower bound",
                "known_proof_sources": ["conformal prediction textbook"],
                "candidate_primitives": [
                        {
                            "primitive": "exchangeability",
                            "coverage_status": "exact_exists",
                            "candidate_declarations": ["Probability.exchangeable"],
                        },
                    {
                        "primitive": "rank uniformity",
                        "coverage_status": "bridge_needed",
                    },
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    initial_response = _reviewed_llm_route_response_payload()
    initial_response["residual_interpretations"] = []
    response_path.write_text(
        json.dumps(initial_response, indent=2),
        encoding="utf-8",
    )
    feedback_response = _reviewed_llm_route_response_payload()
    feedback_response["lean_realization_dag_nodes"][0]["coverage_bucket"] = (
        "wrapper_needed"
    )
    feedback_response["lean_realization_dag_nodes"][0]["formalization_action"] = (
        "write_wrapper"
    )
    feedback_response["route_alignment_edges"].append(
        {
            "informal_node_id": "informal:exchangeability",
            "formal_node_id": "formal:exchangeability",
            "alignment_status": "wrapper_needed",
            "alignment_rationale": (
                "The Rocq feedback pass needs a target-prover wrapper for the "
                "exchangeability declaration before reuse."
            ),
        }
    )
    feedback_response["minimal_delta_plan"]["route_cost"] = 6
    feedback_response["minimal_delta_plan"]["primitive_costs"][0][
        "coverage_bucket"
    ] = "wrapper_needed"
    feedback_response["minimal_delta_plan"]["primitive_costs"][0]["base_cost"] = 2
    feedback_response["minimal_delta_plan"]["primitive_costs"][0]["total_cost"] = 2
    feedback_response["minimal_delta_plan"]["primitive_costs"][0][
        "cost_rationale"
    ] = "The feedback pass requires a target-prover exchangeability wrapper."
    feedback_response["minimal_delta_plan"]["wrapper_lemmas"] = [
        (
            "exchangeability: write the target-prover wrapper around the "
            "available exchangeability declaration"
        )
    ]
    feedback_response["minimal_delta_plan"]["and_or_cost_graph"]["route_options"][0][
        "route_cost"
    ] = 6
    feedback_response["minimal_delta_plan"]["and_or_cost_graph"]["route_options"][0][
        "cost_rationale"
    ] = "Add a target-prover exchangeability wrapper and one focused rank bridge."
    for option in feedback_response["minimal_delta_plan"]["and_or_cost_graph"][
        "route_options"
    ]:
        if (
            option["route_option_id"]
            == "route_option:current_route_min_delta_baseline"
        ):
            option["route_cost"] = 166
            option["cost_rationale"] = (
                "Request-bound baseline preserving the full current target route "
                "includes the target-prover exchangeability wrapper."
            )
    feedback_response["standalone_route"]["primitives"][0][
        "coverage_status"
    ] = "wrapper_needed"
    feedback_response["residual_interpretations"] = [
        {
            "residual_goal": "rocq:rank_uniformity: awaiting prover adapter mapping",
            "interpretation": (
                "The target Rocq route still needs a prover-adapter mapping for "
                "rank_uniformity before any kernel replay can be claimed."
            ),
            "repair_action": "run target-prover adapter mapping for rank_uniformity",
            "formal_gap_boundary": (
                "Awaiting Rocq adapter mapping is target-prover feedback, not "
                "source evidence or theorem proof evidence."
            ),
        }
    ]
    feedback_response_path.write_text(
        json.dumps(feedback_response, indent=2),
        encoding="utf-8",
    )

    payload = run_formalization_gap_planner_reuse_smoke(
        input_path,
        out_dir,
        target_prover_family="rocq",
        target_library_snapshot_ref="rocq:reuse-smoke-llm-static",
        llm_route_planner_provider="static",
        llm_route_planner_invoke_provider=True,
        llm_route_planner_static_response_json=response_path,
        feedback_llm_route_planner_provider="static",
        feedback_llm_route_planner_invoke_provider=True,
        feedback_llm_route_planner_static_response_json=feedback_response_path,
    )

    assert payload["n_llm_route_planner_response_present"] == 1
    assert payload["has_llm_route_planner_response_payload_validation"]
    assert payload["n_llm_route_planner_response_payload_validation_payloads"] == 2
    assert (
        payload["n_llm_route_planner_response_payload_validation_valid_payloads"]
        == 2
    )
    assert (
        payload["n_llm_route_planner_response_payload_validation_invalid_payloads"]
        == 0
    )
    assert (
        payload[
            "n_llm_route_planner_response_payload_validation_request_context_packets"
        ]
        == 2
    )
    assert (
        payload[
            "n_llm_route_planner_response_payload_validation_request_context_inventories"
        ]
        == 2
    )
    assert (
        payload[
            "n_llm_route_planner_response_payload_validation_request_context_inventory_total_rows"
        ]
        >= 2
    )
    assert (
        payload[
            "n_llm_route_planner_response_payload_validation_request_bound_payloads"
        ]
        == 2
    )
    assert (
        payload[
            "n_llm_route_planner_response_payload_validation_request_bound_payloads_with_context_inventory"
        ]
        == 2
    )
    assert (
        payload[
            "n_llm_route_planner_response_payload_validation_request_bound_context_inventory_total_rows"
        ]
        >= 2
    )
    assert (
        payload[
            "n_llm_route_planner_response_payload_validation_request_context_errors"
        ]
        == 0
    )
    assert (
        payload[
            "n_llm_route_planner_response_payload_validation_declared_target_prover_payloads"
        ]
        == 2
    )
    assert (
        payload[
            "n_llm_route_planner_response_payload_validation_target_prover_mismatches"
        ]
        == 0
    )
    assert (
        payload[
            "llm_route_planner_response_payload_validation_by_payload_target_prover_family"
        ]
        == {"lean4": 2}
    )
    assert (
        payload[
            "llm_route_planner_response_payload_validation_by_request_context_target_prover_family"
        ]
        == {"lean4": 2}
    )
    assert (
        payload[
            "n_goal_plan_standalone_input_traces_with_llm_route_planner_metadata"
        ]
        == 1
    )
    assert payload["n_goal_plan_standalone_input_traces_with_llm_model_tier"] == 1
    assert payload["goal_plan_standalone_input_trace_by_llm_model_tier"] == {
        "sonnet": 1
    }
    assert (
        payload[
            "n_goal_plan_standalone_input_traces_with_llm_generator_metadata"
        ]
        == 1
    )
    assert payload["n_goal_plan_standalone_input_traces_with_llm_seed_selection"] == 1
    assert payload["n_goal_plan_standalone_input_traces_llm_seed_selected"] == 1
    assert (
        payload[
            "n_goal_plan_standalone_input_traces_llm_seed_adoptable_for_standalone_replay"
        ]
        == 0
    )
    assert (
        payload[
            "n_goal_plan_standalone_input_traces_llm_seed_selected_not_adoptable"
        ]
        == 1
    )
    assert payload[
        "goal_plan_standalone_input_trace_by_llm_seed_selection_rank"
    ] == {"1": 1}
    assert (
        payload[
            "n_goal_plan_standalone_input_traces_with_llm_seed_minimal_delta_route_cost"
        ]
        == 1
    )
    assert payload["n_evaluation_rows_with_llm_route_planner_trace"] == 1
    assert payload["n_evaluation_rows_with_llm_route_planner_model_tier"] == 1
    assert (
        payload[
            "n_evaluation_rows_with_llm_route_planner_route_adoption_status"
        ]
        == 1
    )
    assert payload["n_evaluation_rows_ready_for_route_adoption"] == 0
    assert (
        payload["n_evaluation_rows_pending_refinement_before_route_adoption"]
        == 1
    )
    assert payload["n_evaluation_llm_route_adoption_blockers"] == 5
    assert (
        payload[
            "n_evaluation_llm_route_adoption_pending_quality_control_blockers"
        ]
        == 0
    )
    assert (
        payload[
            "n_evaluation_llm_route_adoption_pending_source_grounding_blockers"
        ]
        == 0
    )
    assert set(payload["evaluation_llm_route_adoption_blockers"]) == {
        "omitted_cost_hint_primitives_require_review",
        "planner_next_actions_pending_evidence",
        "search_requests_pending_evidence",
        "semantic_alignment_risks_require_review",
        "uncertainty_flags_require_review",
    }
    assert payload["evaluation_llm_route_adoption_blocker_counts"] == {
        "omitted_cost_hint_primitives_require_review": 1,
        "planner_next_actions_pending_evidence": 1,
        "search_requests_pending_evidence": 1,
        "semantic_alignment_risks_require_review": 1,
        "uncertainty_flags_require_review": 1,
    }
    assert payload["evaluation_by_llm_route_adoption_status"] == {
        "PENDING_REFINEMENT_BEFORE_ROUTE_ADOPTION": {
            "n_rows": 1,
            "n_ok": 0,
            "n_matched_ground_truth": 1,
            "n_route_adoption_blockers": 5,
            "mean_route_recall": 1.0,
            "mean_delta_precision": 1.0,
        }
    }
    assert payload["evaluation_by_llm_route_adoption_blocker"][
        "search_requests_pending_evidence"
    ]["n_rows"] == 1
    assert payload["n_evaluation_rows_with_llm_route_planner_generator_metadata"] == 1
    sonnet_evaluation = payload["evaluation_by_llm_model_tier"]["sonnet"]
    assert sonnet_evaluation["n_rows"] == 1
    assert sonnet_evaluation["n_matched_ground_truth"] == 1
    assert sonnet_evaluation["mean_route_recall"] == 1.0
    assert sonnet_evaluation["n_rows_with_generator_metadata"] == 1
    assert payload["n_llm_route_planner_provider_failures"] == 0
    assert payload["n_llm_route_planner_request_model_tier_mismatches"] == 0
    assert payload["llm_route_planner_request_model_tier_mismatches"] == []
    assert (
        payload["n_llm_route_planner_requests_with_model_tier_decision_evidence"]
        == payload["n_llm_route_planner_request_packets"]
    )
    assert (
        payload[
            "n_llm_route_planner_request_model_tier_decision_auto_haiku_bounded"
        ]
        + payload[
            "n_llm_route_planner_request_model_tier_decision_auto_sonnet_triggered"
        ]
        + payload[
            "n_llm_route_planner_request_model_tier_decision_operator_override"
        ]
        == payload["n_llm_route_planner_request_packets"]
    )
    assert (
        payload[
            "n_llm_route_planner_request_model_tier_decision_evidence_invalid"
        ]
        == 0
    )
    assert payload["llm_route_planner_by_request_model_tier_decision_basis"]
    assert (
        payload["n_llm_route_planner_requests_with_llm_generation_policy"]
        == payload["n_llm_route_planner_request_packets"]
    )
    assert (
        payload[
            "n_llm_route_planner_request_llm_generation_policy_tier_model_matches"
        ]
        == payload["n_llm_route_planner_request_packets"]
    )
    assert (
        payload[
            "n_llm_route_planner_request_llm_generation_policy_codex_exclusions"
        ]
        == payload["n_llm_route_planner_request_packets"]
    )
    assert (
        payload[
            "n_llm_route_planner_request_llm_generation_policy_current_claude_tier_source"
        ]
        == payload["n_llm_route_planner_request_packets"]
    )
    assert (
        payload["n_llm_route_planner_requests_with_library_alignment_summary"]
        == payload["n_llm_route_planner_request_packets"]
    )
    assert payload["n_llm_route_planner_request_library_alignment_primitives"] > 0
    assert payload["llm_route_planner_by_request_library_alignment_delta_class"]
    assert payload[
        "llm_route_planner_by_request_library_alignment_minimum_coverage_bucket"
    ]
    assert payload["n_llm_route_planner_rows_with_generator_metadata"] == 1
    assert payload["n_llm_route_planner_rows_with_generation_errors"] == 0
    assert payload["n_llm_route_planner_response_contract_ok"] == 1
    assert payload["n_llm_route_planner_accepted_route_plans"] == 1
    assert payload["n_llm_route_planner_route_adoption_ready"] == 0
    assert payload["n_llm_route_planner_route_adoption_pending_refinement"] == 1
    assert payload["llm_route_planner_route_adoption_blocker_counts"][
        "search_requests_pending_evidence"
    ] == 1
    assert payload["llm_route_planner_by_route_adoption_blocker"][
        "search_requests_pending_evidence"
    ]["n_rows"] == 1
    assert payload["n_llm_route_planner_route_adoption_pending_search_request_blockers"] == 1
    assert payload["n_llm_route_planner_route_adoption_pending_feedback_action_blockers"] == 0
    assert (
        payload[
            "n_llm_route_planner_route_adoption_pending_resource_playbook_redispatch_blockers"
        ]
        == 0
    )
    assert (
        payload[
            "n_llm_route_planner_route_adoption_pending_resource_request_queue_blockers"
        ]
        == 0
    )
    assert payload["n_llm_route_planner_route_adoption_pending_feedback_replan_blockers"] == 0
    assert payload["n_llm_route_planner_route_adoption_pending_realization_coverage_blockers"] == 0
    assert (
        payload[
            "n_llm_route_planner_route_adoption_pending_omitted_cost_hint_primitive_blockers"
        ]
        == 1
    )
    assert (
        payload[
            "n_llm_route_planner_route_adoption_pending_formal_gap_boundary_blockers"
        ]
        == 0
    )
    assert (
        payload[
            "n_llm_route_planner_route_adoption_pending_quality_control_blockers"
        ]
        == 0
    )
    assert (
        payload[
            "n_llm_route_planner_route_adoption_pending_source_grounding_blockers"
        ]
        == 0
    )
    assert payload["n_llm_route_planner_route_adoption_omitted_cost_hint_primitives"] > 0
    assert payload["n_llm_route_planner_awaiting"] == 0
    assert payload["n_llm_route_planner_search_requests"] == 1
    assert payload["n_feedback_llm_route_planner_response_present"] == 1
    assert payload["n_feedback_llm_route_planner_provider_failures"] == 0
    assert payload["n_feedback_llm_route_planner_request_model_tier_mismatches"] == 0
    assert payload["feedback_llm_route_planner_request_model_tier_mismatches"] == []
    assert (
        payload[
            "n_feedback_llm_route_planner_requests_with_model_tier_decision_evidence"
        ]
        == payload["n_feedback_llm_route_planner_request_packets"]
    )
    assert (
        payload[
            "n_feedback_llm_route_planner_request_model_tier_decision_auto_haiku_bounded"
        ]
        + payload[
            "n_feedback_llm_route_planner_request_model_tier_decision_auto_sonnet_triggered"
        ]
        + payload[
            "n_feedback_llm_route_planner_request_model_tier_decision_operator_override"
        ]
        == payload["n_feedback_llm_route_planner_request_packets"]
    )
    assert (
        payload[
            "n_feedback_llm_route_planner_request_model_tier_decision_evidence_invalid"
        ]
        == 0
    )
    assert payload["feedback_llm_route_planner_by_request_model_tier_decision_basis"]
    assert (
        payload["n_feedback_llm_route_planner_requests_with_llm_generation_policy"]
        == payload["n_feedback_llm_route_planner_request_packets"]
    )
    assert (
        payload[
            "n_feedback_llm_route_planner_request_llm_generation_policy_tier_model_matches"
        ]
        == payload["n_feedback_llm_route_planner_request_packets"]
    )
    assert (
        payload[
            "n_feedback_llm_route_planner_request_llm_generation_policy_codex_exclusions"
        ]
        == payload["n_feedback_llm_route_planner_request_packets"]
    )
    assert (
        payload[
            "n_feedback_llm_route_planner_request_llm_generation_policy_current_claude_tier_source"
        ]
        == payload["n_feedback_llm_route_planner_request_packets"]
    )
    assert (
        payload[
            "n_feedback_llm_route_planner_requests_with_library_alignment_summary"
        ]
        == payload["n_feedback_llm_route_planner_request_packets"]
    )
    assert (
        payload[
            "n_feedback_llm_route_planner_request_library_alignment_primitives"
        ]
        > 0
    )
    assert payload[
        "feedback_llm_route_planner_by_request_library_alignment_delta_class"
    ]
    assert payload[
        "feedback_llm_route_planner_by_request_library_alignment_minimum_coverage_bucket"
    ]
    assert payload["n_feedback_llm_route_planner_rows_with_generator_metadata"] == 1
    assert payload["n_feedback_llm_route_planner_rows_with_generation_errors"] == 0
    assert payload["n_feedback_llm_route_planner_response_contract_ok"] == 1
    assert payload["n_feedback_llm_route_planner_accepted_route_plans"] == 1
    assert payload["n_feedback_llm_route_planner_route_adoption_ready"] == 0
    assert (
        payload["n_feedback_llm_route_planner_route_adoption_pending_refinement"]
        == 1
    )
    assert payload["feedback_llm_route_planner_route_adoption_blocker_counts"][
        "feedback_loop_replan_required"
    ] == 1
    assert payload["feedback_llm_route_planner_by_route_adoption_blocker"][
        "feedback_summary_actions_pending_resolution"
    ]["n_rows"] == 1
    assert (
        payload[
            "n_feedback_llm_route_planner_route_adoption_pending_search_request_blockers"
        ]
        == 1
    )
    assert (
        payload[
            "n_feedback_llm_route_planner_route_adoption_pending_feedback_action_blockers"
        ]
        == 1
    )
    assert (
        payload[
            "n_feedback_llm_route_planner_route_adoption_pending_resource_playbook_redispatch_blockers"
        ]
        == 0
    )
    assert (
        payload[
            "n_feedback_llm_route_planner_route_adoption_pending_resource_request_queue_blockers"
        ]
        == 1
    )
    assert (
        payload[
            "n_feedback_llm_route_planner_route_adoption_pending_feedback_replan_blockers"
        ]
        == 1
    )
    assert (
        payload[
            "n_feedback_llm_route_planner_route_adoption_pending_realization_coverage_blockers"
        ]
        == 0
    )
    assert (
        payload[
            "n_feedback_llm_route_planner_route_adoption_pending_omitted_cost_hint_primitive_blockers"
        ]
        == 1
    )
    assert (
        payload[
            "n_feedback_llm_route_planner_route_adoption_pending_formal_gap_boundary_blockers"
        ]
        == 1
    )
    assert (
        payload[
            "n_feedback_llm_route_planner_route_adoption_pending_quality_control_blockers"
        ]
        == 1
    )
    assert (
        payload[
            "n_feedback_llm_route_planner_route_adoption_pending_source_grounding_blockers"
        ]
        == 0
    )
    assert (
        payload[
            "n_feedback_llm_route_planner_route_adoption_omitted_cost_hint_primitives"
        ]
        > 0
    )
    assert payload["n_feedback_llm_route_planner_awaiting"] == 0
    assert payload["n_feedback_llm_route_planner_search_requests"] == 1
    assert payload["n_llm_route_planner_feedback_loop_realization_witnesses"] == 0
    assert payload["n_feedback_llm_route_planner_feedback_loop_realization_witnesses"] == 1
    assert payload["n_library_coverage_rows_with_candidate_declaration_rows"] > 0
    assert payload["n_library_coverage_candidate_declaration_rows"] > 0
    assert payload["n_primitive_action_queue_with_candidate_declaration_rows"] > 0
    assert payload["n_primitive_action_queue_candidate_declaration_rows"] > 0
    assert payload["n_action_resource_plan_with_candidate_declaration_rows"] > 0
    assert payload["n_action_resource_plan_candidate_declaration_rows"] > 0
    assert payload["n_resource_request_with_candidate_declaration_rows"] > 0
    assert payload["n_resource_request_candidate_declaration_rows"] > 0
    stage_by_name = {stage["stage_name"]: stage for stage in payload["stages"]}
    llm_stage_summary = stage_by_name[
        "formalization_gap_planner_llm_route_planner"
    ]["summary"]
    feedback_llm_stage_summary = stage_by_name[
        "formalization_gap_planner_feedback_llm_route_planner"
    ]["summary"]
    assert llm_stage_summary["n_formal_realization_dag_nodes"] > 0
    assert feedback_llm_stage_summary["n_formal_realization_dag_nodes"] > 0
    validation_summary = stage_by_name[
        "formalization_gap_planner_llm_route_planner_response_payload_validation"
    ]["summary"]
    assert validation_summary["n_payloads"] == 2
    assert validation_summary["n_valid_payloads"] == 2
    assert validation_summary["n_invalid_payloads"] == 0
    coverage_summary = stage_by_name[
        "formalization_gap_planner_library_coverage_map"
    ]["summary"]
    action_summary = stage_by_name[
        "formalization_gap_planner_primitive_action_queue"
    ]["summary"]
    resource_plan_summary = stage_by_name[
        "formalization_gap_planner_action_resource_plan"
    ]["summary"]
    resource_request_summary = stage_by_name[
        "formalization_gap_planner_resource_request_queue"
    ]["summary"]
    publication_bundle_summary = stage_by_name[
        "formalization_gap_planner_publication_bundle"
    ]["summary"]
    publication_bundle_audit_summary = stage_by_name[
        "formalization_gap_planner_publication_bundle_audit"
    ]["summary"]
    assert coverage_summary["n_candidate_declaration_rows"] == payload[
        "n_library_coverage_candidate_declaration_rows"
    ]
    assert action_summary["n_candidate_declaration_rows"] == payload[
        "n_primitive_action_queue_candidate_declaration_rows"
    ]
    assert resource_plan_summary["n_candidate_declaration_rows"] == payload[
        "n_action_resource_plan_candidate_declaration_rows"
    ]
    assert resource_request_summary["n_candidate_declaration_rows"] == payload[
        "n_resource_request_candidate_declaration_rows"
    ]
    assert publication_bundle_summary["llm_route_planner_summary"][
        "n_accepted_route_plans"
    ] == payload["n_publication_bundle_llm_route_planner_summary_accepted_route_plans"]
    assert publication_bundle_summary["feedback_llm_route_planner_summary"][
        "n_accepted_route_plans"
    ] == payload[
        "n_publication_bundle_feedback_llm_route_planner_summary_accepted_route_plans"
    ]
    assert (
        publication_bundle_audit_summary[
            "n_bundle_llm_route_planner_summary_valid"
        ]
        == payload["n_publication_bundle_llm_route_planner_summary_valid"]
        == 1
    )
    assert (
        publication_bundle_audit_summary[
            "n_bundle_feedback_llm_route_planner_summary_valid"
        ]
        == payload["n_publication_bundle_feedback_llm_route_planner_summary_valid"]
        == 1
    )
    assert (
        payload[
            "n_feedback_llm_route_planner_feedback_loop_incomplete_realization_coverage"
        ]
        == 0
    )
    assert (
        payload[
            "n_feedback_llm_route_planner_feedback_loop_incomplete_cost_hint_baseline_coverage"
        ]
        == 1
    )
    assert (
        payload[
            "n_feedback_llm_route_planner_feedback_loop_missing_selected_formal_primitives"
        ]
        == 0
    )
    assert (
        payload[
            "n_feedback_llm_route_planner_feedback_loop_missing_delta_alignment_primitives"
        ]
        == 0
    )
    assert (
        payload[
            "n_feedback_llm_route_planner_feedback_loop_omitted_cost_hint_primitives"
        ]
        == 8
    )
    assert payload["feedback_llm_route_planner_provider"] == "static"
    reproduction_command = payload["reproduction_commands"][0]
    assert "--llm-route-planner-model-tier auto" in reproduction_command
    assert "--llm-route-planner-max-repair-attempts 1" in reproduction_command
    assert "--feedback-llm-route-planner-provider static" in reproduction_command
    assert "--feedback-llm-route-planner-model-tier auto" in reproduction_command
    assert "--feedback-llm-route-planner-max-repair-attempts 1" in reproduction_command
    assert "--feedback-llm-route-planner-invoke-provider" in reproduction_command
    assert "--feedback-llm-route-planner-static-response-file" in reproduction_command
    assert payload["publication_bundle_llm_route_planner_summary_requested"]
    assert (
        payload["n_publication_bundle_llm_route_planner_summary_request_packets"]
        == payload["n_llm_route_planner_request_packets"]
        == 1
    )
    assert (
        payload[
            "n_publication_bundle_llm_route_planner_summary_context_packet_inventories"
        ]
        == payload["n_llm_route_planner_context_packet_inventories"]
        == 1
    )
    assert (
        payload[
            "n_publication_bundle_llm_route_planner_summary_context_inventory_total_rows"
        ]
        == payload["n_llm_route_planner_context_inventory_total_rows"]
        >= 1
    )
    assert (
        payload[
            "n_publication_bundle_llm_route_planner_summary_rows_with_context_packet_inventory"
        ]
        == payload["n_llm_route_planner_rows_with_context_packet_inventory"]
        == 1
    )
    assert (
        payload[
            "n_publication_bundle_llm_route_planner_summary_quality_control_obligation_inventories"
        ]
        == payload["n_llm_route_planner_quality_control_obligation_inventories"]
    )
    assert (
        payload[
            "n_publication_bundle_llm_route_planner_summary_pending_quality_control_obligation_inventories"
        ]
        == payload[
            "n_llm_route_planner_pending_quality_control_obligation_inventories"
        ]
    )
    assert (
        payload[
            "n_publication_bundle_llm_route_planner_summary_request_pending_quality_control_values"
        ]
        == payload["n_llm_route_planner_request_pending_quality_control_values"]
    )
    assert (
        payload[
            "n_publication_bundle_llm_route_planner_summary_request_discharged_quality_control_values"
        ]
        == payload["n_llm_route_planner_request_discharged_quality_control_values"]
    )
    assert (
        payload[
            "n_publication_bundle_llm_route_planner_summary_prior_llm_hook_traces"
        ]
        == payload["n_llm_route_planner_feedback_loop_prior_llm_hook_traces"]
    )
    assert (
        payload[
            "n_publication_bundle_llm_route_planner_summary_requests_with_prior_llm_hook_traces"
        ]
        == payload[
            "n_llm_route_planner_requests_with_feedback_loop_prior_llm_hook_traces"
        ]
    )
    assert (
        payload["n_publication_bundle_llm_route_planner_summary_rows"]
        == payload["n_llm_route_planner_request_packets"]
        == 1
    )
    assert (
        payload["n_publication_bundle_llm_route_planner_summary_response_present"]
        == payload["n_llm_route_planner_response_present"]
        == 1
    )
    assert (
        payload[
            "n_publication_bundle_llm_route_planner_summary_response_contract_ok"
        ]
        == payload["n_llm_route_planner_response_contract_ok"]
        == 1
    )
    assert (
        payload[
            "n_publication_bundle_llm_route_planner_summary_informal_knowledge_dag_nodes"
        ]
        == payload["n_llm_route_planner_informal_knowledge_dag_nodes"]
        >= 1
    )
    assert (
        payload[
            "n_publication_bundle_llm_route_planner_summary_formal_realization_dag_nodes"
        ]
        == payload["n_llm_route_planner_formal_realization_dag_nodes"]
        >= 1
    )
    assert (
        payload[
            "n_publication_bundle_llm_route_planner_summary_lean_realization_dag_nodes"
        ]
        == payload["n_llm_route_planner_lean_realization_dag_nodes"]
        >= 1
    )
    assert (
        payload[
            "n_publication_bundle_llm_route_planner_summary_route_alignment_edges"
        ]
        == payload["n_llm_route_planner_route_alignment_edges"]
        >= 1
    )
    assert (
        payload[
            "n_publication_bundle_llm_route_planner_summary_accepted_route_plans"
        ]
        == payload["n_llm_route_planner_accepted_route_plans"]
        == 1
    )
    assert (
        payload[
            "n_publication_bundle_llm_route_planner_summary_route_adoption_pending_refinement"
        ]
        == payload["n_llm_route_planner_route_adoption_pending_refinement"]
        == 1
    )
    assert (
        payload[
            "n_publication_bundle_llm_route_planner_summary_route_adoption_pending_formal_gap_boundary_blockers"
        ]
        == payload[
            "n_llm_route_planner_route_adoption_pending_formal_gap_boundary_blockers"
        ]
        == 0
    )
    assert (
        payload[
            "publication_bundle_llm_route_planner_summary_route_adoption_blocker_counts"
        ]["search_requests_pending_evidence"]
        == 1
    )
    assert (
        payload[
            "publication_bundle_llm_route_planner_summary_by_route_adoption_status"
        ]["PENDING_REFINEMENT_BEFORE_ROUTE_ADOPTION"]
        == 1
    )
    assert (
        payload[
            "publication_bundle_llm_route_planner_summary_by_route_adoption_blocker"
        ]["search_requests_pending_evidence"]["n_rows"]
        == 1
    )
    assert (
        payload[
            "n_publication_bundle_llm_route_planner_summary_requests_with_model_tier_decision_evidence"
        ]
        == payload["n_llm_route_planner_requests_with_model_tier_decision_evidence"]
    )
    assert (
        payload[
            "n_publication_bundle_llm_route_planner_summary_request_model_tier_decision_auto_haiku_bounded"
        ]
        == payload[
            "n_llm_route_planner_request_model_tier_decision_auto_haiku_bounded"
        ]
    )
    assert (
        payload[
            "n_publication_bundle_llm_route_planner_summary_request_model_tier_decision_auto_sonnet_triggered"
        ]
        == payload[
            "n_llm_route_planner_request_model_tier_decision_auto_sonnet_triggered"
        ]
    )
    assert (
        payload[
            "n_publication_bundle_llm_route_planner_summary_request_model_tier_decision_operator_override"
        ]
        == payload[
            "n_llm_route_planner_request_model_tier_decision_operator_override"
        ]
    )
    assert (
        payload[
            "n_publication_bundle_llm_route_planner_summary_request_model_tier_decision_sonnet_triggers"
        ]
        == payload[
            "n_llm_route_planner_request_model_tier_decision_sonnet_triggers"
        ]
    )
    assert (
        payload[
            "n_publication_bundle_llm_route_planner_summary_request_model_tier_decision_evidence_invalid"
        ]
        == payload[
            "n_llm_route_planner_request_model_tier_decision_evidence_invalid"
        ]
        == 0
    )
    assert (
        payload[
            "publication_bundle_llm_route_planner_summary_by_request_model_tier_decision_basis"
        ]
        == payload["llm_route_planner_by_request_model_tier_decision_basis"]
    )
    assert (
        payload[
            "n_publication_bundle_llm_route_planner_summary_requests_with_library_alignment_summary"
        ]
        == payload["n_llm_route_planner_requests_with_library_alignment_summary"]
    )
    assert (
        payload[
            "n_publication_bundle_llm_route_planner_summary_request_library_alignment_primitives"
        ]
        == payload["n_llm_route_planner_request_library_alignment_primitives"]
    )
    assert (
        payload[
            "n_publication_bundle_llm_route_planner_summary_request_library_alignment_bridge_or_harder_primitives"
        ]
        == payload[
            "n_llm_route_planner_request_library_alignment_bridge_or_harder_primitives"
        ]
    )
    assert (
        payload[
            "n_publication_bundle_llm_route_planner_summary_request_library_alignment_target_compatible_reuse_declarations"
        ]
        == payload[
            "n_llm_route_planner_request_library_alignment_target_compatible_reuse_declarations"
        ]
    )
    assert (
        payload[
            "publication_bundle_llm_route_planner_summary_by_request_library_alignment_delta_class"
        ]
        == payload["llm_route_planner_by_request_library_alignment_delta_class"]
    )
    assert (
        payload[
            "publication_bundle_llm_route_planner_summary_by_request_library_alignment_minimum_coverage_bucket"
        ]
        == payload[
            "llm_route_planner_by_request_library_alignment_minimum_coverage_bucket"
        ]
    )
    assert (
        payload[
            "publication_bundle_llm_route_planner_summary_standalone_replay_gate_ok"
        ]
        == payload["llm_route_planner_standalone_replay_gate_ok"]
        is False
    )
    assert (
        payload[
            "n_publication_bundle_llm_route_planner_summary_standalone_replay_route_candidates"
        ]
        == payload["n_llm_route_planner_standalone_replay_route_candidates"]
        == 1
    )
    assert (
        payload[
            "n_publication_bundle_llm_route_planner_summary_standalone_replay_adoptable_route_candidates"
        ]
        == payload["n_llm_route_planner_standalone_replay_adoptable_route_candidates"]
        == 0
    )
    assert (
        payload[
            "n_publication_bundle_llm_route_planner_summary_standalone_replay_blocked_route_candidates"
        ]
        == payload["n_llm_route_planner_standalone_replay_blocked_route_candidates"]
        == 1
    )
    assert payload[
        "publication_bundle_llm_route_planner_summary_standalone_replay_gate_blockers"
    ] == payload["llm_route_planner_standalone_replay_gate_blockers"]
    assert (
        "search_requests_pending_evidence"
        in payload["publication_bundle_llm_route_planner_summary_standalone_replay_gate_blockers"]
    )
    assert payload["publication_bundle_feedback_llm_route_planner_summary_requested"]
    assert (
        payload[
            "n_publication_bundle_feedback_llm_route_planner_summary_request_packets"
        ]
        == payload["n_feedback_llm_route_planner_request_packets"]
        == 1
    )
    assert (
        payload[
            "n_publication_bundle_feedback_llm_route_planner_summary_context_packet_inventories"
        ]
        == payload["n_feedback_llm_route_planner_context_packet_inventories"]
        == 1
    )
    assert (
        payload[
            "n_publication_bundle_feedback_llm_route_planner_summary_context_inventory_total_rows"
        ]
        == payload["n_feedback_llm_route_planner_context_inventory_total_rows"]
        >= 1
    )
    assert (
        payload[
            "n_publication_bundle_feedback_llm_route_planner_summary_rows_with_context_packet_inventory"
        ]
        == payload["n_feedback_llm_route_planner_rows_with_context_packet_inventory"]
        == 1
    )
    assert (
        payload[
            "n_publication_bundle_feedback_llm_route_planner_summary_quality_control_obligation_inventories"
        ]
        == payload[
            "n_feedback_llm_route_planner_quality_control_obligation_inventories"
        ]
    )
    assert (
        payload[
            "n_publication_bundle_feedback_llm_route_planner_summary_pending_quality_control_obligation_inventories"
        ]
        == payload[
            "n_feedback_llm_route_planner_pending_quality_control_obligation_inventories"
        ]
    )
    assert (
        payload[
            "n_publication_bundle_feedback_llm_route_planner_summary_request_pending_quality_control_values"
        ]
        == payload[
            "n_feedback_llm_route_planner_request_pending_quality_control_values"
        ]
    )
    assert (
        payload[
            "n_publication_bundle_feedback_llm_route_planner_summary_request_discharged_quality_control_values"
        ]
        == payload[
            "n_feedback_llm_route_planner_request_discharged_quality_control_values"
        ]
    )
    assert (
        payload[
            "n_publication_bundle_feedback_llm_route_planner_summary_prior_llm_hook_traces"
        ]
        == payload[
            "n_feedback_llm_route_planner_feedback_loop_prior_llm_hook_traces"
        ]
    )
    assert (
        payload[
            "n_publication_bundle_feedback_llm_route_planner_summary_requests_with_prior_llm_hook_traces"
        ]
        == payload[
            "n_feedback_llm_route_planner_requests_with_feedback_loop_prior_llm_hook_traces"
        ]
    )
    assert (
        payload[
            "n_publication_bundle_feedback_llm_route_planner_summary_response_present"
        ]
        == payload["n_feedback_llm_route_planner_response_present"]
        == 1
    )
    assert (
        payload[
            "n_publication_bundle_feedback_llm_route_planner_summary_informal_knowledge_dag_nodes"
        ]
        == payload["n_feedback_llm_route_planner_informal_knowledge_dag_nodes"]
        >= 1
    )
    assert (
        payload[
            "n_publication_bundle_feedback_llm_route_planner_summary_formal_realization_dag_nodes"
        ]
        == payload["n_feedback_llm_route_planner_formal_realization_dag_nodes"]
        >= 1
    )
    assert (
        payload[
            "n_publication_bundle_feedback_llm_route_planner_summary_lean_realization_dag_nodes"
        ]
        == payload["n_feedback_llm_route_planner_lean_realization_dag_nodes"]
        >= 1
    )
    assert (
        payload[
            "n_publication_bundle_feedback_llm_route_planner_summary_route_alignment_edges"
        ]
        == payload["n_feedback_llm_route_planner_route_alignment_edges"]
        >= 1
    )
    assert (
        payload[
            "n_publication_bundle_feedback_llm_route_planner_summary_accepted_route_plans"
        ]
        == payload["n_feedback_llm_route_planner_accepted_route_plans"]
        == 1
    )
    assert (
        payload[
            "n_publication_bundle_feedback_llm_route_planner_summary_route_adoption_pending_refinement"
        ]
        == payload["n_feedback_llm_route_planner_route_adoption_pending_refinement"]
        == 1
    )
    assert (
        payload[
            "n_publication_bundle_feedback_llm_route_planner_summary_route_adoption_pending_formal_gap_boundary_blockers"
        ]
        == payload[
            "n_feedback_llm_route_planner_route_adoption_pending_formal_gap_boundary_blockers"
        ]
        == 1
    )
    assert (
        payload[
            "publication_bundle_feedback_llm_route_planner_summary_route_adoption_blocker_counts"
        ]["feedback_loop_replan_required"]
        == 1
    )
    assert (
        payload[
            "publication_bundle_feedback_llm_route_planner_summary_by_route_adoption_blocker"
        ]["feedback_summary_actions_pending_resolution"]["n_rows"]
        == 1
    )
    assert (
        payload[
            "n_publication_bundle_feedback_llm_route_planner_summary_requests_with_model_tier_decision_evidence"
        ]
        == payload[
            "n_feedback_llm_route_planner_requests_with_model_tier_decision_evidence"
        ]
    )
    assert (
        payload[
            "n_publication_bundle_feedback_llm_route_planner_summary_request_model_tier_decision_auto_haiku_bounded"
        ]
        == payload[
            "n_feedback_llm_route_planner_request_model_tier_decision_auto_haiku_bounded"
        ]
    )
    assert (
        payload[
            "n_publication_bundle_feedback_llm_route_planner_summary_request_model_tier_decision_auto_sonnet_triggered"
        ]
        == payload[
            "n_feedback_llm_route_planner_request_model_tier_decision_auto_sonnet_triggered"
        ]
    )
    assert (
        payload[
            "n_publication_bundle_feedback_llm_route_planner_summary_request_model_tier_decision_operator_override"
        ]
        == payload[
            "n_feedback_llm_route_planner_request_model_tier_decision_operator_override"
        ]
    )
    assert (
        payload[
            "n_publication_bundle_feedback_llm_route_planner_summary_request_model_tier_decision_sonnet_triggers"
        ]
        == payload[
            "n_feedback_llm_route_planner_request_model_tier_decision_sonnet_triggers"
        ]
    )
    assert (
        payload[
            "n_publication_bundle_feedback_llm_route_planner_summary_request_model_tier_decision_evidence_invalid"
        ]
        == payload[
            "n_feedback_llm_route_planner_request_model_tier_decision_evidence_invalid"
        ]
        == 0
    )
    assert (
        payload[
            "publication_bundle_feedback_llm_route_planner_summary_by_request_model_tier_decision_basis"
        ]
        == payload[
            "feedback_llm_route_planner_by_request_model_tier_decision_basis"
        ]
    )
    assert (
        payload[
            "n_publication_bundle_feedback_llm_route_planner_summary_requests_with_library_alignment_summary"
        ]
        == payload[
            "n_feedback_llm_route_planner_requests_with_library_alignment_summary"
        ]
    )
    assert (
        payload[
            "n_publication_bundle_feedback_llm_route_planner_summary_request_library_alignment_primitives"
        ]
        == payload[
            "n_feedback_llm_route_planner_request_library_alignment_primitives"
        ]
    )
    assert (
        payload[
            "n_publication_bundle_feedback_llm_route_planner_summary_request_library_alignment_bridge_or_harder_primitives"
        ]
        == payload[
            "n_feedback_llm_route_planner_request_library_alignment_bridge_or_harder_primitives"
        ]
    )
    assert (
        payload[
            "n_publication_bundle_feedback_llm_route_planner_summary_request_library_alignment_target_compatible_reuse_declarations"
        ]
        == payload[
            "n_feedback_llm_route_planner_request_library_alignment_target_compatible_reuse_declarations"
        ]
    )
    assert (
        payload[
            "publication_bundle_feedback_llm_route_planner_summary_by_request_library_alignment_delta_class"
        ]
        == payload[
            "feedback_llm_route_planner_by_request_library_alignment_delta_class"
        ]
    )
    assert (
        payload[
            "publication_bundle_feedback_llm_route_planner_summary_by_request_library_alignment_minimum_coverage_bucket"
        ]
        == payload[
            "feedback_llm_route_planner_by_request_library_alignment_minimum_coverage_bucket"
        ]
    )
    assert (
        payload[
            "publication_bundle_feedback_llm_route_planner_summary_standalone_replay_gate_ok"
        ]
        == payload["feedback_llm_route_planner_standalone_replay_gate_ok"]
        is False
    )
    assert (
        payload[
            "n_publication_bundle_feedback_llm_route_planner_summary_standalone_replay_route_candidates"
        ]
        == payload["n_feedback_llm_route_planner_standalone_replay_route_candidates"]
        == 1
    )
    assert (
        payload[
            "n_publication_bundle_feedback_llm_route_planner_summary_standalone_replay_adoptable_route_candidates"
        ]
        == payload[
            "n_feedback_llm_route_planner_standalone_replay_adoptable_route_candidates"
        ]
        == 0
    )
    assert (
        payload[
            "n_publication_bundle_feedback_llm_route_planner_summary_standalone_replay_blocked_route_candidates"
        ]
        == payload[
            "n_feedback_llm_route_planner_standalone_replay_blocked_route_candidates"
        ]
        == 1
    )
    assert payload[
        "publication_bundle_feedback_llm_route_planner_summary_standalone_replay_gate_blockers"
    ] == payload["feedback_llm_route_planner_standalone_replay_gate_blockers"]
    assert (
        payload["n_publication_bundle_llm_route_planner_summary_valid"]
        == payload["n_publication_bundle_llm_route_planner_summary_checked"]
        == 1
    )
    assert (
        payload["n_publication_bundle_feedback_llm_route_planner_summary_valid"]
        == payload["n_publication_bundle_feedback_llm_route_planner_summary_checked"]
        == 1
    )
    assert (
        payload["n_publication_bundle_optional_llm_route_planner_row_schema_valid"]
        == payload["n_publication_bundle_optional_llm_route_planner_row_schema_checked"]
        == 1
    )
    assert (
        payload[
            "n_publication_bundle_optional_llm_route_planner_request_model_tier_mismatch_valid"
        ]
        == payload[
            "n_publication_bundle_optional_llm_route_planner_request_model_tier_mismatch_checked"
        ]
        == 1
    )
    assert (
        payload[
            "n_publication_bundle_optional_llm_route_planner_request_generation_policy_valid"
        ]
        == payload[
            "n_publication_bundle_optional_llm_route_planner_request_generation_policy_checked"
        ]
        == 1
    )
    assert (
        payload[
            "n_publication_bundle_optional_llm_route_planner_generation_preflight_valid"
        ]
        == payload[
            "n_publication_bundle_optional_llm_route_planner_generation_preflight_checked"
        ]
        == 1
    )
    assert (
        payload[
            "n_publication_bundle_optional_llm_route_planner_route_adoption_blocker_summary_valid"
        ]
        == payload[
            "n_publication_bundle_optional_llm_route_planner_route_adoption_blocker_summary_checked"
        ]
        == 1
    )
    assert (
        payload[
            "n_publication_bundle_optional_llm_route_planner_seed_model_provenance_valid"
        ]
        == payload[
            "n_publication_bundle_optional_llm_route_planner_seed_model_provenance_checked"
        ]
        == 1
    )
    assert (
        payload[
            "n_publication_bundle_optional_llm_route_planner_seed_route_adoption_readiness_valid"
        ]
        == payload[
            "n_publication_bundle_optional_llm_route_planner_seed_route_adoption_readiness_checked"
        ]
        == 1
    )
    assert (
        payload[
            "n_publication_bundle_optional_llm_route_planner_seed_route_selection_summary_valid"
        ]
        == payload[
            "n_publication_bundle_optional_llm_route_planner_seed_route_selection_summary_checked"
        ]
        == 1
    )
    assert (
        payload[
            "n_publication_bundle_optional_llm_route_planner_seed_route_selection_contract_valid"
        ]
        == payload[
            "n_publication_bundle_optional_llm_route_planner_seed_route_selection_contract_checked"
        ]
        == 1
    )
    assert (
        payload[
            "n_publication_bundle_optional_llm_route_planner_seed_route_selection_schema_valid"
        ]
        == payload[
            "n_publication_bundle_optional_llm_route_planner_seed_route_selection_schema_checked"
        ]
        == 1
    )
    assert (
        payload[
            "n_publication_bundle_optional_llm_route_planner_seed_route_selection_valid"
        ]
        == payload[
            "n_publication_bundle_optional_llm_route_planner_seed_route_selection_checked"
        ]
        == 1
    )
    assert (
        payload[
            "n_publication_bundle_optional_llm_route_planner_seed_route_selection_candidates"
        ]
        == 1
    )
    assert (
        payload[
            "n_publication_bundle_optional_llm_route_planner_seed_route_selection_adoptable_candidates"
        ]
        == 0
    )
    assert (
        payload[
            "n_publication_bundle_optional_llm_route_planner_seed_route_selection_selected_adoptable"
        ]
        == 0
    )
    assert (
        payload[
            "n_publication_bundle_optional_llm_route_planner_seed_route_selection_selected_not_adoptable"
        ]
        == 1
    )
    assert (
        payload["n_publication_bundle_optional_feedback_llm_route_planner_row_schema_valid"]
        == payload["n_publication_bundle_optional_feedback_llm_route_planner_row_schema_checked"]
        == 1
    )
    assert (
        payload[
            "n_publication_bundle_optional_feedback_llm_route_planner_request_model_tier_mismatch_valid"
        ]
        == payload[
            "n_publication_bundle_optional_feedback_llm_route_planner_request_model_tier_mismatch_checked"
        ]
        == 1
    )
    assert (
        payload[
            "n_publication_bundle_optional_feedback_llm_route_planner_request_generation_policy_valid"
        ]
        == payload[
            "n_publication_bundle_optional_feedback_llm_route_planner_request_generation_policy_checked"
        ]
        == 1
    )
    assert (
        payload[
            "n_publication_bundle_optional_feedback_llm_route_planner_generation_preflight_valid"
        ]
        == payload[
            "n_publication_bundle_optional_feedback_llm_route_planner_generation_preflight_checked"
        ]
        == 1
    )
    assert (
        payload[
            "n_publication_bundle_optional_feedback_llm_route_planner_route_adoption_blocker_summary_valid"
        ]
        == payload[
            "n_publication_bundle_optional_feedback_llm_route_planner_route_adoption_blocker_summary_checked"
        ]
        == 1
    )
    assert (
        payload[
            "n_publication_bundle_optional_feedback_llm_route_planner_seed_model_provenance_valid"
        ]
        == payload[
            "n_publication_bundle_optional_feedback_llm_route_planner_seed_model_provenance_checked"
        ]
        == 1
    )
    assert (
        payload[
            "n_publication_bundle_optional_feedback_llm_route_planner_seed_route_adoption_readiness_valid"
        ]
        == payload[
            "n_publication_bundle_optional_feedback_llm_route_planner_seed_route_adoption_readiness_checked"
        ]
        == 1
    )
    assert (
        payload[
            "n_publication_bundle_optional_feedback_llm_route_planner_seed_route_selection_summary_valid"
        ]
        == payload[
            "n_publication_bundle_optional_feedback_llm_route_planner_seed_route_selection_summary_checked"
        ]
        == 1
    )
    assert (
        payload[
            "n_publication_bundle_optional_feedback_llm_route_planner_seed_route_selection_contract_valid"
        ]
        == payload[
            "n_publication_bundle_optional_feedback_llm_route_planner_seed_route_selection_contract_checked"
        ]
        == 1
    )
    assert (
        payload[
            "n_publication_bundle_optional_feedback_llm_route_planner_seed_route_selection_schema_valid"
        ]
        == payload[
            "n_publication_bundle_optional_feedback_llm_route_planner_seed_route_selection_schema_checked"
        ]
        == 1
    )
    assert (
        payload[
            "n_publication_bundle_optional_feedback_llm_route_planner_seed_route_selection_valid"
        ]
        == payload[
            "n_publication_bundle_optional_feedback_llm_route_planner_seed_route_selection_checked"
        ]
        == 1
    )
    assert (
        payload[
            "n_publication_bundle_optional_feedback_llm_route_planner_seed_route_selection_candidates"
        ]
        == 1
    )
    assert (
        payload[
            "n_publication_bundle_optional_feedback_llm_route_planner_seed_route_selection_adoptable_candidates"
        ]
        == 0
    )
    assert (
        payload[
            "n_publication_bundle_optional_feedback_llm_route_planner_seed_route_selection_selected_adoptable"
        ]
        == 0
    )
    assert (
        payload[
            "n_publication_bundle_optional_feedback_llm_route_planner_seed_route_selection_selected_not_adoptable"
        ]
        == 1
    )
    assert (
        payload[
            "n_publication_bundle_optional_llm_route_planner_response_payload_validation_manifest_contract_valid"
        ]
        == payload[
            "n_publication_bundle_optional_llm_route_planner_response_payload_validation_manifest_contract_checked"
        ]
        == 1
    )
    assert (
        payload[
            "n_publication_bundle_optional_llm_route_planner_response_payload_validation_count_valid"
        ]
        == payload[
            "n_publication_bundle_optional_llm_route_planner_response_payload_validation_count_checked"
        ]
        == 1
    )
    assert (
        payload[
            "n_publication_bundle_optional_llm_route_planner_response_payload_validation_request_bound_accounting_valid"
        ]
        == payload[
            "n_publication_bundle_optional_llm_route_planner_response_payload_validation_request_bound_accounting_checked"
        ]
        == 1
    )
    assert (
        payload[
            "n_publication_bundle_optional_llm_route_planner_response_payload_validation_request_bound_coverage_valid"
        ]
        == payload[
            "n_publication_bundle_optional_llm_route_planner_response_payload_validation_request_bound_coverage_checked"
        ]
        == 1
    )
    assert (
        payload[
            "n_publication_bundle_optional_llm_route_planner_response_payload_validation_row_schema_valid"
        ]
        == payload[
            "n_publication_bundle_optional_llm_route_planner_response_payload_validation_row_schema_checked"
        ]
        == 2
    )
    assert Path(
        payload["artifacts"][
            "llm_route_planner_response_payload_validation_manifest"
        ]
    ).exists()
    report_text = (
        out_dir / "formalization_gap_planner_reuse_smoke.md"
    ).read_text(encoding="utf-8")
    assert "target_mismatch=0" in report_text
    assert (
        out_dir
        / "formalization_gap_planner_publication_bundle"
        / "artifacts"
        / "formalization_gap_planner_llm_route_planner_response_payload_validation"
        / "formalization_gap_planner_llm_route_planner_response_payload_validation_manifest.json"
    ).exists()
    seed_payload = json.loads(
        (
            out_dir
            / "formalization_gap_planner_llm_route_planner"
            / "formalization_gap_planner_llm_route_planner_standalone_seed.json"
        ).read_text(encoding="utf-8")
    )
    assert seed_payload["routes"][0]["display_name"] == "llm_reviewed_rank_route"
    seed_primitive = seed_payload["routes"][0]["primitives"][0]
    assert seed_primitive["candidate_declaration_rows"] == [
        {
            "declaration": "Probability.exchangeable",
            "target_prover_family": "lean4",
            "source_field": "available_formal_declaration_rows",
        }
    ]
    assert seed_primitive["candidate_declarations"] == ["Probability.exchangeable"]
    plan_rows = [
        json.loads(line)
        for line in (
            out_dir
            / "goal_conditioned_minimal_formalization_plan"
            / "goal_conditioned_minimal_formalization_plan.jsonl"
        ).read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert plan_rows
    assert plan_rows[0]["display_name"] == "llm_reviewed_rank_route"
    assert plan_rows[0]["selected_primitives"] == [
        "exchangeability",
        "rank_uniformity",
    ]
    assert plan_rows[0]["existing_reuse_nodes"][0]["candidate_declaration_rows"] == [
        {
            "declaration": "Probability.exchangeable",
            "target_prover_family": "lean4",
            "source_field": "available_formal_declaration_rows",
        }
    ]
    standalone_trace = plan_rows[0]["standalone_input_trace"]
    assert standalone_trace["llm_route_planner_model_tier"] == "sonnet"
    assert standalone_trace["llm_route_planner_route_adoption_status"] == (
        "PENDING_REFINEMENT_BEFORE_ROUTE_ADOPTION"
    )
    assert "search_requests_pending_evidence" in standalone_trace[
        "llm_route_planner_route_adoption_blockers"
    ]
    assert standalone_trace["llm_route_planner_has_generator_metadata"] is True
    assert standalone_trace["llm_route_planner_generator_metadata"]["generator_only"] is True
    report_text = (
        out_dir / "formalization_gap_planner_reuse_smoke.md"
    ).read_text(encoding="utf-8")
    assert "Structured candidate declaration rows:" in report_text
    assert "LLM route payload validation payloads valid/invalid: 2/0" in report_text
    feedback_seed_payload = json.loads(
        (
            out_dir
            / "formalization_gap_planner_feedback_llm_route_planner"
            / "formalization_gap_planner_llm_route_planner_standalone_seed.json"
        ).read_text(encoding="utf-8")
    )
    assert feedback_seed_payload["routes"][0]["display_name"] == "llm_reviewed_rank_route"


def test_reuse_smoke_surfaces_llm_route_planner_provider_failure() -> None:
    root = Path("runs/test_formalization_gap_planner_reuse_smoke_llm_provider_failure")
    input_path = root / "target_request.json"
    failure_response_path = root / "provider_failure_response.json"
    out_dir = root / "reuse_smoke"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "component_name": "formalization_gap_planner_target_intake",
                "target_prover_family": "lean4",
                "library_snapshot_ref": "mathlib4:reuse-smoke-llm-provider-failure",
                "target_id": "split_conformal_coverage_provider_failure",
                "title": "Split conformal finite-sample coverage provider failure",
                "domain": "distribution-free prediction",
                "theorem_statement": (
                    "For exchangeable calibration and test scores, split "
                    "conformal prediction has finite sample marginal coverage."
                ),
                "objects": ["calibration scores", "test score"],
                "assumptions": [
                    "exchangeable calibration and test scores",
                    "finite calibration sample",
                ],
                "statistical_procedure": "split conformal prediction set",
                "desired_conclusion": "finite sample marginal coverage inequality",
                "desired_theorem_shape": "coverage probability lower bound",
                "known_proof_sources": ["conformal prediction textbook"],
                "candidate_primitives": [
                    {
                        "primitive": "exchangeability",
                        "coverage_status": "exact_exists",
                        "candidate_declarations": ["Probability.exchangeable"],
                    },
                    {
                        "primitive": "rank uniformity",
                        "coverage_status": "bridge_needed",
                    },
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    failure_response_path.write_text(
        json.dumps(
            {
                "provider_name": "anthropic",
                "model": "claude-sonnet-4-6",
                "response_payload": {},
                "raw_response_text": "",
                "generator_metadata": {
                    "generator_only": True,
                    "tools_available": False,
                    "provider_failure": True,
                    "exception_type": "TimeoutError",
                    "exception_message": "simulated Anthropic timeout",
                    "repair_attempt": 0,
                },
                "provider_failure": True,
                "kernel_verified": False,
                "proof_evidence_boundary": LLM_ROUTE_PLANNER_PROOF_EVIDENCE_BOUNDARY,
                "repair_attempts": 0,
                "repair_error_history": [],
                "generation_errors": [
                    "provider exception: TimeoutError: simulated Anthropic timeout"
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    payload = run_formalization_gap_planner_reuse_smoke(
        input_path,
        out_dir,
        target_prover_family="rocq",
        target_library_snapshot_ref="rocq:reuse-smoke-llm-provider-failure",
        llm_route_planner_response_json=failure_response_path,
    )

    assert not payload["all_ok"]
    assert (
        payload[
            "n_goal_plan_standalone_input_traces_with_llm_route_planner_metadata"
        ]
        == 1
    )
    assert payload["n_goal_plan_standalone_input_traces_with_llm_model_tier"] == 1
    assert payload["goal_plan_standalone_input_trace_by_llm_model_tier"] == {
        "sonnet": 1
    }
    assert payload["goal_plan_standalone_input_trace_by_llm_route_adoption_status"] == {
        "REJECTED_LLM_ROUTE_PLAN": 1
    }
    assert (
        payload[
            "n_goal_plan_standalone_input_traces_with_llm_generator_metadata"
        ]
        == 1
    )
    assert payload["n_goal_plan_standalone_input_traces_with_llm_seed_selection"] == 1
    assert payload["n_goal_plan_standalone_input_traces_llm_seed_selected"] == 1
    assert (
        payload[
            "n_goal_plan_standalone_input_traces_llm_seed_adoptable_for_standalone_replay"
        ]
        == 0
    )
    assert (
        payload[
            "n_goal_plan_standalone_input_traces_llm_seed_selected_not_adoptable"
        ]
        == 1
    )
    assert payload[
        "goal_plan_standalone_input_trace_by_llm_seed_selection_rank"
    ] == {"1": 1}
    assert (
        payload[
            "n_goal_plan_standalone_input_traces_with_llm_seed_minimal_delta_route_cost"
        ]
        == 0
    )
    assert payload["n_evaluation_rows_with_llm_route_planner_trace"] == 1
    assert payload["n_evaluation_rows_with_llm_route_planner_generator_metadata"] == 1
    assert payload["n_evaluation_rows_with_llm_route_planner_request_contract_blocked"] == 0
    assert payload["n_evaluation_rows_with_llm_route_planner_errors"] == 1
    assert payload["n_evaluation_llm_route_planner_errors"] == 1
    assert payload["n_evaluation_llm_route_planner_generation_errors"] == 1
    assert payload["evaluation_by_llm_route_adoption_status"] == {
        "REJECTED_LLM_ROUTE_PLAN": {
            "n_rows": 1,
            "n_ok": 1,
            "n_matched_ground_truth": 1,
            "n_route_adoption_blockers": 1,
            "mean_route_recall": 1.0,
            "mean_delta_precision": 1.0,
        }
    }
    assert payload["evaluation_by_llm_model_tier"]["sonnet"][
        "n_rows_with_errors"
    ] == 1
    assert payload["n_llm_route_planner_request_packets"] == 1
    assert payload["n_llm_route_planner_response_present"] == 0
    assert payload["n_llm_route_planner_provider_failures"] == 1
    assert payload["n_llm_route_planner_rows_with_generator_metadata"] == 1
    assert payload["n_llm_route_planner_rows_with_generation_errors"] == 1
    assert payload["n_llm_route_planner_awaiting"] == 0
    assert payload["n_llm_route_planner_accepted_route_plans"] == 0
    assert payload["n_llm_route_planner_row_schema_valid"] == 1
    assert payload["n_llm_route_planner_row_schema_invalid"] == 0
    assert payload["n_feedback_llm_route_planner_provider_failures"] == 0
    assert payload["n_feedback_llm_route_planner_rows_with_generation_errors"] == 0
    assert (
        payload["n_feedback_llm_route_planner_awaiting"]
        == payload["n_feedback_llm_route_planner_request_packets"]
    )
    llm_manifest = json.loads(
        (
            out_dir
            / "formalization_gap_planner_llm_route_planner"
            / "formalization_gap_planner_llm_route_planner_manifest.json"
        ).read_text(encoding="utf-8")
    )
    assert llm_manifest["n_provider_failures"] == 1
    assert llm_manifest["rows"][0]["acceptance_status"] == (
        "REJECTED_LLM_ROUTE_PLANNER_PROVIDER_FAILURE"
    )
    assert llm_manifest["rows"][0]["generator_metadata"]["exception_type"] == (
        "TimeoutError"
    )
    report = (
        out_dir / "formalization_gap_planner_reuse_smoke.md"
    ).read_text(encoding="utf-8")
    assert "provider_failures=1" in report
