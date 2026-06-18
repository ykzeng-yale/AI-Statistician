from __future__ import annotations

import json
import shutil
from pathlib import Path

from ai_statistician.formalization_gap_planner_route_replan_handoff import (
    export_formalization_gap_planner_route_replan_handoff,
    route_replan_handoff_row_json_schema,
    validate_route_replan_handoff_row,
)
from ai_statistician.formalization_gap_planner_contract import (
    LEGACY_FORMAL_REALIZATION_FIELD_ALIASES,
    LIBRARY_AWARE_FORMALIZATION_GAP_PLANNER_NAME,
    PORTABLE_FORMALIZATION_GAP_PLAN_SCHEMA_ID,
)
from ai_statistician.formalization_gap_planner_standalone import (
    export_formalization_gap_planner_standalone_plan,
    standalone_input_json_schema,
)


def test_route_replan_handoff_exports_replayable_standalone_seed() -> None:
    root = Path("runs/test_formalization_gap_planner_route_replan_handoff")
    input_json = root / "standalone_input.json"
    plan_dir = root / "plan"
    overlay_dir = root / "overlay"
    stability_dir = root / "stability"
    handoff_dir = root / "handoff"
    next_plan_dir = root / "next_plan"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    overlay_dir.mkdir(parents=True, exist_ok=True)
    stability_dir.mkdir(parents=True, exist_ok=True)
    route_planning_brief = {
        "brief_kind": "formalization_gap_planner_llm_route_planner_route_planning_brief",
        "route_id": "route:split_conformal_seed",
        "display_name": "split_conformal_finite_sample_coverage",
        "target_prover_family": "lean4",
        "planner_focus": [
            {
                "focus_id": "preserve_rank_route",
                "priority": 1,
                "action": "keep the rank-uniformity route under exchangeability",
                "reason": "proof-state feedback should refine, not replace, the target theorem",
                "target_primitives": ["rank_uniformity"],
            }
        ],
        "evidence_gaps": [
            {
                "gap_id": "conditional_rank_argument_source",
                "gap_kind": "source_grounding",
                "recommended_action": "search source proof for the conditional rank argument",
                "target_primitives": ["conditional_rank_argument"],
            }
        ],
        "proof_evidence_status": (
            "FORMALIZATION_GAP_PLANNER_LLM_ROUTE_PLANNER_NOT_PROOF_EVIDENCE"
        ),
    }
    route_adoption_preconditions = {
        "precondition_kind": (
            "formalization_gap_planner_llm_route_planner_route_adoption_preconditions"
        ),
        "status": "PENDING_CONTEXT_OBLIGATIONS",
        "blocked_before_response": True,
        "known_pre_response_blockers": ["source_grounding_obligations_pending"],
        "n_known_pre_response_blockers": 1,
        "response_required_fields": ["search_requests", "planner_next_actions"],
        "n_response_required_fields": 2,
        "target_primitives": ["rank_uniformity"],
        "n_target_primitives": 1,
        "proof_evidence_status": (
            "FORMALIZATION_GAP_PLANNER_LLM_ROUTE_PLANNER_NOT_PROOF_EVIDENCE"
        ),
    }
    route_option_selection_brief = {
        "brief_kind": (
            "formalization_gap_planner_llm_route_planner_route_option_selection_brief"
        ),
        "route_id": "route:split_conformal_seed",
        "display_name": "split_conformal_finite_sample_coverage",
        "target_prover_family": "lean4",
        "library_snapshot_ref": "mathlib4:replan-fixture",
        "cost_policy_id": (
            "formalization_gap_planner_minimal_delta_cost_policy:1"
        ),
        "selection_rule": (
            "Choose the route option with the lowest library-aware route cost."
        ),
        "n_candidate_route_options": 1,
        "n_candidate_route_option_primitives": 2,
        "n_lower_bound_tied_route_options": 1,
        "lower_bound_selected_route_option_id": "route_option:rank_bridge",
        "lower_bound_selected_route_cost": 6.0,
        "candidate_route_options": [
            {
                "route_option_id": "route_option:rank_bridge",
                "route_cost": 6.0,
                "selected_primitives": ["exchangeability", "rank_uniformity"],
                "n_selected_primitives": 2,
                "selected_by_lower_bound_policy": True,
                "lower_bound_tied_for_best": True,
                "primitive_costs": [
                    {"primitive": "exchangeability", "cost": 1.0},
                    {"primitive": "rank_uniformity", "cost": 5.0},
                ],
                "cost_rationale": (
                    "Reuse exchangeability and add one rank-uniformity bridge."
                ),
            }
        ],
        "required_response_bindings": [
            {
                "field": (
                    "minimal_delta_plan.and_or_cost_graph."
                    "selected_route_option_id"
                ),
                "required_value": "route_option:rank_bridge",
            }
        ],
        "proof_evidence_status": (
            "FORMALIZATION_GAP_PLANNER_LLM_ROUTE_PLANNER_NOT_PROOF_EVIDENCE"
        ),
        "proof_evidence_boundary": "not theorem proof evidence",
    }
    primitive_evidence_matrix_witness = {
        "witness_kind": (
            "formalization_gap_planner_llm_route_planner_primitive_evidence_matrix_witness"
        ),
        "route_id": "route:split_conformal_seed",
        "primitive_evidence_matrix": [
            {
                "primitive": "exchangeability",
                "source_evidence_status": "source_backed",
                "formal_reuse_status": "exact_exists",
                "delta_status": "reuse_only",
            },
            {
                "primitive": "rank_uniformity",
                "source_evidence_status": "source_backed",
                "formal_reuse_status": "bridge_needed",
                "delta_status": "delta_needed",
            },
        ],
        "matrix_accounting_complete": True,
        "matrix_unaccounted_primitives": [],
        "selected_primitives_without_matrix_row": [],
        "source_backed_matrix_primitives_missing_response_source_snippet": [],
        "formal_supported_matrix_primitives_missing_reuse": [],
        "delta_needed_matrix_primitives_missing_accounting": [],
        "proof_evidence_status": (
            "FORMALIZATION_GAP_PLANNER_LLM_ROUTE_PLANNER_NOT_PROOF_EVIDENCE"
        ),
        "proof_evidence_boundary": "not theorem proof evidence",
    }
    target_context_summary = {
        "summary_kind": (
            "formalization_gap_planner_llm_route_planner_target_context_summary"
        ),
        "route_id": "route:split_conformal_seed",
        "normalized_objects": ["calibration scores", "test score rank"],
        "normalized_assumptions": [
            "exchangeable calibration and test scores"
        ],
        "normalized_procedures": ["rank-based conformal calibration"],
        "desired_conclusions": ["rank uniformity"],
        "desired_theorem_shapes": ["finite sample rank identity"],
        "proof_source_refs": ["Lei-Wasserman distribution-free prediction"],
        "proof_evidence_status": (
            "FORMALIZATION_GAP_PLANNER_LLM_ROUTE_PLANNER_NOT_PROOF_EVIDENCE"
        ),
        "proof_evidence_boundary": "not theorem proof evidence",
    }
    legacy_target_context_summary = dict(target_context_summary)
    legacy_target_context_summary["normalized_statistical_procedures"] = (
        legacy_target_context_summary.pop("normalized_procedures")
    )
    legacy_target_context_summary["normalized_desired_conclusions"] = (
        legacy_target_context_summary.pop("desired_conclusions")
    )
    legacy_target_context_summary["normalized_theorem_shapes"] = (
        legacy_target_context_summary.pop("desired_theorem_shapes")
    )
    input_json.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "component_name": "formalization_gap_planner_standalone_input",
                "target_prover_family": "lean4",
                "library_snapshot_ref": "mathlib4:replan-fixture",
                "routes": [
                    {
                        "display_name": "split_conformal_finite_sample_coverage",
                        "theorem_statement": "Split conformal has finite sample coverage.",
                        "llm_route_planner_route_planning_brief": route_planning_brief,
                        "llm_route_planner_route_option_selection_brief": (
                            route_option_selection_brief
                        ),
                        "llm_route_planner_primitive_evidence_matrix_witness": (
                            primitive_evidence_matrix_witness
                        ),
                        "llm_route_planner_route_adoption_preconditions": (
                            route_adoption_preconditions
                        ),
                        "llm_route_planner_target_context_summary": (
                            legacy_target_context_summary
                        ),
                        "source_refs": ["Lei-Wasserman distribution-free prediction"],
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
                                "source_refs": ["Lei-Wasserman distribution-free prediction"],
                                "cost": 5,
                            },
                        ],
                    }
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    plan_payload = export_formalization_gap_planner_standalone_plan(input_json, plan_dir)
    assert (
        plan_payload["n_standalone_input_traces_with_llm_route_planning_brief"]
        == 1
    )
    assert (
        plan_payload[
            "n_standalone_input_traces_with_llm_route_option_selection_brief"
        ]
        == 1
    )
    assert (
        plan_payload[
            "n_standalone_input_traces_with_llm_primitive_evidence_matrix_witness"
        ]
        == 1
    )
    assert (
        plan_payload[
            "n_standalone_input_traces_with_complete_llm_primitive_evidence_matrix_accounting"
        ]
        == 1
    )
    assert (
        plan_payload[
            "n_standalone_input_traces_with_llm_route_adoption_preconditions"
        ]
        == 1
    )
    assert (
        plan_payload[
            "n_standalone_input_traces_with_llm_target_context_summary"
        ]
        == 1
    )
    plan_row = plan_payload["rows"][0]
    revised_selected = [
        *plan_row["selected_primitives"],
        "conditional_rank_argument",
    ]
    revised_delta = [
        node["primitive"]
        for node in plan_row["minimal_additional_formalization_nodes"]
    ] + ["conditional_rank_argument"]
    revised_dag_source_ref = "Vovk-Gammerman-Shafer revised rank node"
    resource_response_trace = {
        "resource_response_ledger_id": "conditional_rank_argument",
        "resource_request_id": "request:conditional_rank_argument",
        "action_resource_plan_id": "action-resource-plan:conditional_rank_argument",
        "primitive_action_id": "primitive-action:conditional_rank_argument",
        "coverage_map_id": "coverage:conditional_rank_argument",
        "goal_plan_id": plan_row["goal_plan_id"],
        "route_id": plan_row["route_id"],
        "primitive": "conditional_rank_argument",
        "target_primitives": ["conditional_rank_argument"],
        "priority_score": 77,
        "minimal_delta_cost_score": 60,
        "reuse_readiness_score": 35,
        "evidence_readiness_score": 90,
        "priority_rationale": [
            "coverage_status=source_port_needed",
            "minimal_delta_cost_score=60",
            "reuse_readiness_score=35",
            "evidence_readiness_score=90",
        ],
        "resource_id": "lean_lsp_mcp",
        "request_phase": "frontier_escalation",
        "expected_response_artifact": "proof_state_or_prover_feedback_response",
        "acceptance_status": "ACCEPTED_WITH_ROUTE_REVISION",
        "matched_response_contract_fields": ["residual_goals"],
        "missing_response_contract_fields": [],
        "prover_attempt_status": "local_lean_failed",
        "prover_diagnostic_signature": "missing_source_statement",
        "proof_evidence_boundary": "not theorem proof evidence",
    }
    llm_route_planner_hook_trace = {
        "trace_source": "resource_response_ledger",
        "resource_response_ledger_id": "conditional_rank_argument",
        "resource_request_id": "request:conditional_rank_argument",
        "route_id": plan_row["route_id"],
        "goal_plan_id": plan_row["goal_plan_id"],
        "target_primitives": ["conditional_rank_argument"],
        "priority_score": 77,
        "minimal_delta_cost_score": 60,
        "reuse_readiness_score": 35,
        "evidence_readiness_score": 90,
        "priority_rationale": [
            "coverage_status=source_port_needed",
            "minimal_delta_cost_score=60",
            "reuse_readiness_score=35",
            "evidence_readiness_score=90",
        ],
        "resource_id": "lean_lsp_mcp",
        "acceptance_status": "ACCEPTED_WITH_ROUTE_REVISION",
        "llm_route_planner_row_id": "llm_route_row:conditional_rank",
        "llm_route_planner_request_id": "llm_route_request:conditional_rank",
        "llm_route_planner_source_kind": "planner_next_action",
        "llm_route_planner_source_index": 0,
        "llm_route_planner_hook_kind": "proof_state_feedback",
        "llm_route_planner_queries": [
            "ask Lean LSP for conditional_rank_argument residual goals"
        ],
        "llm_route_planner_source_item": {
            "action": "ask Lean LSP for conditional_rank_argument residual goals",
            "resource_id": "lean_lsp_mcp",
            "target_primitives": ["conditional_rank_argument"],
        },
        "residual_goal_context": {
            "source_kind": "planner_next_action",
            "residual_goal": (
                "conditional_rank_argument: missing source-backed statement"
            ),
            "residual_goals": [
                "conditional_rank_argument: missing source-backed statement"
            ],
            "residual_primitives": ["conditional_rank_argument"],
            "target_primitives": ["conditional_rank_argument"],
            "interpretation": (
                "Lean feedback requires a source-backed conditional rank "
                "argument before replay"
            ),
            "route_repair": (
                "add conditional_rank_argument to the informal and formal DAGs"
            ),
            "repair_action": "rerun route planning with conditional_rank_argument",
            "source_refs": ["Lei-Wasserman theorem proof route"],
            "queries": [
                "ask Lean LSP for conditional_rank_argument residual goals"
            ],
        },
        "llm_route_planner_response_trace_grounded": True,
        "llm_route_planner_response_trace_mismatches": [],
        "proof_evidence_boundary": "not theorem proof evidence",
    }
    overlay_row = {
        "route_revision_overlay_id": "overlay:split_conformal",
        "goal_plan_id": plan_row["goal_plan_id"],
        "route_id": plan_row["route_id"],
        "display_name": plan_row["display_name"],
        "revision_status": "ROUTE_REVISION_APPLIED",
        "original_selected_primitives": plan_row["selected_primitives"],
        "revised_selected_primitives": revised_selected,
        "added_primitives": ["conditional_rank_argument"],
        "removed_primitives": [],
        "original_delta_primitives": [
            node["primitive"]
            for node in plan_row["minimal_additional_formalization_nodes"]
        ],
        "revised_delta_primitives": revised_delta,
        "added_delta_primitives": ["conditional_rank_argument"],
        "source_refs": ["Lei-Wasserman theorem proof route"],
        "source_snippets": [
            {
                "source_ref": "Lei-Wasserman theorem proof route",
                "claim": "conditional rank argument follows from exchangeability",
                "excerpt": "The source route proves the conditional rank argument before applying the split conformal bound.",
                "target_primitives": ["conditional_rank_argument"],
            }
        ],
        "lean_declaration_hits": [
            {
                "primitive": "conditional_rank_argument",
                "coverage_status": "source_discovery_needed",
                "declaration": "",
            }
        ],
        "residual_goals": ["conditional_rank_argument: missing source-backed statement"],
        "applied_proposal_ids": ["proposal:resource-ledger-conditional-rank"],
        "applied_refinement_evidence_ids": [
            "resource_response_ledger:conditional_rank_argument"
        ],
        "applied_hook_kinds": ["resource_response_ledger"],
        "applied_resource_response_traces": [resource_response_trace],
        "applied_llm_route_planner_hook_traces": [llm_route_planner_hook_trace],
        "applied_prover_attempt_statuses": ["local_lean_failed"],
        "applied_prover_diagnostic_signatures": ["missing_source_statement"],
        "route_revision_reasons": ["residual proof state exposed a missing rank argument"],
        "route_revision_summaries": ["add conditional rank argument before replay"],
        "revised_informal_knowledge_dag_nodes": [
            {
                "node_id": "informal:conditional_rank_argument",
                "label": "conditional_rank_argument",
                "primitive": "conditional_rank_argument",
                "source_ref": "Lei-Wasserman theorem proof route",
                "source_refs": [revised_dag_source_ref],
            }
        ],
        "revised_lean_realization_dag_nodes": [
            {
                "node_id": "lean:conditional_rank_argument",
                "label": "conditional_rank_argument",
                "primitive": "conditional_rank_argument",
                "coverage_status": "source_port_needed",
            }
        ],
        "revised_route_alignment_edges": [
            *plan_row["route_alignment_edges"],
            {
                "source": "informal:conditional_rank_argument",
                "target": "lean:conditional_rank_argument",
                "kind": "aligned_to_formal_realization_candidate",
                "edge_type": "revised_informal_to_formal_alignment",
                "primitive": "conditional_rank_argument",
                "alignment_status": "source_port_delta",
            },
        ],
        "unaligned_primitives": [],
    }
    (overlay_dir / "formalization_gap_planner_route_revision_overlay_manifest.json").write_text(
        json.dumps(
            {
                "component_name": "formalization_gap_planner_route_revision_overlay",
                "rows": [overlay_row],
                "all_ok": True,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    (stability_dir / "formalization_gap_planner_route_stability_audit_manifest.json").write_text(
        json.dumps(
            {
                "component_name": "formalization_gap_planner_route_stability_audit",
                "rows": [
                    {
                        "goal_plan_id": plan_row["goal_plan_id"],
                        "route_id": plan_row["route_id"],
                        "display_name": plan_row["display_name"],
                        "stability_decision": "APPLY_ROUTE_REVISION_AND_REPLAN",
                        "stopping_rule_evidence": ["new primitive added by overlay"],
                        "next_actions": ["rerun standalone planner"],
                        "resource_response_awaiting_request_ids": [
                            "request:awaiting-literature"
                        ],
                        "resource_response_rejected_request_ids": [
                            "request:rejected-proof-state"
                        ],
                    }
                ],
                "all_ok": True,
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    payload = export_formalization_gap_planner_route_replan_handoff(
        plan_dir,
        overlay_dir,
        handoff_dir,
        formalization_gap_planner_route_stability_audit_dir=stability_dir,
    )

    assert payload["all_ok"]
    assert payload["n_handoff_rows"] == 1
    assert payload["n_routes_requiring_replan"] == 1
    assert payload["n_standalone_seed_routes"] == 1
    assert payload["n_resource_response_awaiting_request_ids"] == 1
    assert payload["n_resource_response_rejected_request_ids"] == 1
    assert payload["n_applied_llm_route_planner_hook_traces"] == 1
    assert (
        payload[
            "n_applied_resource_response_traces_with_minimal_delta_priority"
        ]
        == 1
    )
    assert (
        payload[
            "average_applied_resource_response_reuse_readiness_score"
        ]
        == 35
    )
    assert (
        payload[
            "average_applied_resource_response_evidence_readiness_score"
        ]
        == 90
    )
    assert payload["n_routes_with_llm_route_planner_hook_trace"] == 1
    assert payload["n_residual_goal_contexts"] == 1
    assert payload["n_routes_with_residual_goal_contexts"] == 1
    assert payload["n_standalone_seed_residual_goal_contexts"] == 1
    assert payload["n_standalone_seed_routes_with_residual_goal_contexts"] == 1
    assert payload["n_source_snippets"] == 1
    assert payload["n_routes_with_source_snippets"] == 1
    assert payload["n_routes_with_llm_route_planning_brief"] == 1
    assert payload["n_standalone_seed_routes_with_llm_route_planning_brief"] == 1
    assert payload["n_routes_with_llm_route_option_selection_brief"] == 1
    assert (
        payload["n_standalone_seed_routes_with_llm_route_option_selection_brief"]
        == 1
    )
    assert payload["n_routes_with_llm_primitive_evidence_matrix_witness"] == 1
    assert (
        payload[
            "n_standalone_seed_routes_with_llm_primitive_evidence_matrix_witness"
        ]
        == 1
    )
    assert payload["n_routes_with_llm_route_adoption_preconditions"] == 1
    assert (
        payload["n_standalone_seed_routes_with_llm_route_adoption_preconditions"]
        == 1
    )
    assert payload["n_routes_with_llm_target_context_summary"] == 1
    assert payload["n_standalone_seed_routes_with_llm_target_context_summary"] == 1
    assert payload["n_route_alignment_edges"] >= 1
    assert payload["n_revised_informal_knowledge_dag_nodes"] >= 1
    assert payload["n_revised_formal_realization_dag_nodes"] >= 1
    assert payload["n_revised_lean_realization_dag_nodes"] >= 1
    assert payload["n_unaligned_primitives"] == 0
    assert payload["n_row_schema_valid"] == payload["n_handoff_rows"]
    assert payload["n_row_schema_invalid"] == 0
    assert (
        payload["route_replan_handoff_row_schema"]["$id"]
        == "urn:ai-statistician:schemas:formalization-gap-planner-route-replan-handoff-row:1"
    )
    assert (
        payload["legacy_formal_realization_field_aliases"]
        == LEGACY_FORMAL_REALIZATION_FIELD_ALIASES
    )
    row = payload["rows"][0]
    assert row["requires_replan"]
    assert row["stability_decision"] == "APPLY_ROUTE_REVISION_AND_REPLAN"
    next_commands = "\n".join(row["next_commands"])
    assert "formalization-gap-planner-llm-route-planner" in next_commands
    assert "--provider anthropic" in next_commands
    assert "--model-tier auto" in next_commands
    assert "--max-repair-attempts 1" in next_commands
    assert "--formalization-gap-planner-route-revision-overlay-dir" in next_commands
    assert str(overlay_dir) in next_commands
    assert "--formalization-gap-planner-route-replan-handoff-dir" in next_commands
    assert str(handoff_dir) in next_commands
    assert "--formalization-gap-planner-component-resource-registry-dir" in next_commands
    llm_commands = [
        command
        for command in row["next_commands"]
        if "formalization-gap-planner-llm-route-planner" in command
    ]
    assert len(llm_commands) == 2
    assert any("--invoke-provider" not in command for command in llm_commands)
    assert any("--invoke-provider" in command for command in llm_commands)
    assert row["applied_hook_kinds"] == ("resource_response_ledger",)
    assert row["applied_refinement_evidence_ids"] == (
        "resource_response_ledger:conditional_rank_argument",
    )
    assert row["applied_resource_response_traces"][0]["resource_request_id"] == (
        "request:conditional_rank_argument"
    )
    assert row["applied_resource_response_traces"][0]["priority_score"] == 77
    assert row["applied_resource_response_traces"][0][
        "minimal_delta_cost_score"
    ] == 60
    assert row["applied_resource_response_traces"][0][
        "reuse_readiness_score"
    ] == 35
    assert row["applied_resource_response_traces"][0][
        "evidence_readiness_score"
    ] == 90
    assert tuple(row["applied_resource_response_traces"][0]["priority_rationale"]) == (
        "coverage_status=source_port_needed",
        "minimal_delta_cost_score=60",
        "reuse_readiness_score=35",
        "evidence_readiness_score=90",
    )
    assert row["applied_llm_route_planner_hook_traces"][0][
        "llm_route_planner_row_id"
    ] == "llm_route_row:conditional_rank"
    assert row["applied_llm_route_planner_hook_traces"][0][
        "llm_route_planner_hook_kind"
    ] == "proof_state_feedback"
    assert row["applied_llm_route_planner_hook_traces"][0][
        "llm_route_planner_source_index"
    ] == 0
    assert row["residual_goal_contexts"][0]["residual_goal"].startswith(
        "conditional_rank_argument"
    )
    assert row["residual_goal_contexts"][0]["residual_primitives"] == (
        "conditional_rank_argument",
    )
    assert row["resource_response_awaiting_request_ids"] == (
        "request:awaiting-literature",
    )
    assert row["resource_response_rejected_request_ids"] == (
        "request:rejected-proof-state",
    )
    assert row["applied_prover_diagnostic_signatures"] == (
        "missing_source_statement",
    )
    assert {
        edge["primitive"] for edge in row["revised_route_alignment_edges"]
    } == set(row["revised_selected_primitives"])
    assert row["revised_informal_knowledge_dag_nodes"]
    assert row["revised_formal_realization_dag_nodes"] == row[
        "revised_lean_realization_dag_nodes"
    ]
    assert row["revised_lean_realization_dag_nodes"]
    assert row["source_snippets"][0]["source_ref"] == (
        "Lei-Wasserman theorem proof route"
    )
    assert revised_dag_source_ref in row["source_refs"]
    assert row["formal_declaration_hits"] == row["lean_declaration_hits"]
    assert row["standalone_route"]["target_prover_family"] == "lean4"
    assert row["standalone_route"]["replan_metadata"]["target_prover_family"] == "lean4"
    assert row["route_planning_brief"] == route_planning_brief
    assert row["route_option_selection_brief"] == route_option_selection_brief
    assert row["primitive_evidence_matrix_witness"] == (
        primitive_evidence_matrix_witness
    )
    assert row["route_adoption_preconditions"] == route_adoption_preconditions
    assert row["target_context_summary"] == target_context_summary
    assert row["standalone_route"]["llm_route_planner_route_planning_brief"] == (
        route_planning_brief
    )
    assert row["standalone_route"][
        "llm_route_planner_route_option_selection_brief"
    ] == route_option_selection_brief
    assert row["standalone_route"][
        "llm_route_planner_primitive_evidence_matrix_witness"
    ] == primitive_evidence_matrix_witness
    assert row["standalone_route"][
        "llm_route_planner_route_adoption_preconditions"
    ] == route_adoption_preconditions
    assert row["standalone_route"][
        "llm_route_planner_target_context_summary"
    ] == target_context_summary
    assert row["standalone_route"]["replan_metadata"][
        "llm_route_planner_route_planning_brief"
    ] == route_planning_brief
    assert row["standalone_route"]["replan_metadata"][
        "llm_route_planner_route_option_selection_brief"
    ] == route_option_selection_brief
    assert row["standalone_route"]["replan_metadata"][
        "llm_route_planner_primitive_evidence_matrix_witness"
    ] == primitive_evidence_matrix_witness
    assert row["standalone_route"]["replan_metadata"][
        "llm_route_planner_route_adoption_preconditions"
    ] == route_adoption_preconditions
    assert row["standalone_route"]["replan_metadata"][
        "llm_route_planner_target_context_summary"
    ] == target_context_summary
    seed = json.loads(
        (handoff_dir / "formalization_gap_planner_route_replan_standalone_seed.json").read_text(
            encoding="utf-8"
        )
    )
    assert seed["component_name"] == "formalization_gap_planner_standalone_input"
    assert seed["target_prover_family"] == "lean4"
    assert seed["routes"][0]["target_prover_family"] == "lean4"
    assert seed["routes"][0]["replan_metadata"]["target_prover_family"] == "lean4"
    assert seed["routes"][0]["llm_route_planner_route_planning_brief"] == (
        route_planning_brief
    )
    assert seed["routes"][0]["llm_route_planner_route_option_selection_brief"] == (
        route_option_selection_brief
    )
    assert seed["routes"][0][
        "llm_route_planner_primitive_evidence_matrix_witness"
    ] == primitive_evidence_matrix_witness
    assert seed["routes"][0]["llm_route_planner_route_adoption_preconditions"] == (
        route_adoption_preconditions
    )
    assert seed["routes"][0]["llm_route_planner_target_context_summary"] == (
        target_context_summary
    )
    assert seed["routes"][0]["replan_metadata"][
        "llm_route_planner_route_planning_brief"
    ] == route_planning_brief
    assert seed["routes"][0]["replan_metadata"][
        "llm_route_planner_route_option_selection_brief"
    ] == route_option_selection_brief
    assert seed["routes"][0]["replan_metadata"][
        "llm_route_planner_primitive_evidence_matrix_witness"
    ] == primitive_evidence_matrix_witness
    assert seed["routes"][0]["replan_metadata"][
        "llm_route_planner_route_adoption_preconditions"
    ] == route_adoption_preconditions
    assert seed["routes"][0]["replan_metadata"][
        "llm_route_planner_target_context_summary"
    ] == target_context_summary
    assert seed["routes"][0]["revised_informal_knowledge_dag_nodes"]
    assert seed["routes"][0]["revised_formal_realization_dag_nodes"] == seed[
        "routes"
    ][0]["revised_lean_realization_dag_nodes"]
    assert seed["routes"][0]["revised_lean_realization_dag_nodes"]
    assert seed["routes"][0]["source_snippets"][0]["source_ref"] == (
        "Lei-Wasserman theorem proof route"
    )
    assert revised_dag_source_ref in seed["routes"][0]["source_refs"]
    assert (
        revised_dag_source_ref
        in seed["routes"][0]["replan_metadata"]["source_refs"]
    )
    assert seed["routes"][0]["replan_metadata"]["alignment_edge_primitives"]
    handoff_schema = route_replan_handoff_row_json_schema()
    assert "route_planning_brief" in handoff_schema["properties"]
    assert "route_option_selection_brief" in handoff_schema["properties"]
    assert "primitive_evidence_matrix_witness" in handoff_schema["properties"]
    assert "route_adoption_preconditions" in handoff_schema["properties"]
    assert "target_context_summary" in handoff_schema["properties"]
    assert "source_snippets" in handoff_schema["properties"]
    assert "source_snippets" not in handoff_schema["required"]
    assert "formal_declaration_hits" in handoff_schema["required"]
    assert "lean_declaration_hits" not in handoff_schema["required"]
    assert "revised_formal_realization_dag_nodes" in handoff_schema["required"]
    assert "revised_lean_realization_dag_nodes" not in handoff_schema["required"]
    legacy_free_row = dict(row)
    legacy_free_row.pop("revised_lean_realization_dag_nodes", None)
    legacy_free_row.pop("lean_declaration_hits", None)
    assert validate_route_replan_handoff_row(legacy_free_row, handoff_schema) == ()
    missing_generic_row = dict(row)
    missing_generic_row.pop("revised_formal_realization_dag_nodes", None)
    assert "revised_formal_realization_dag_nodes required" in validate_route_replan_handoff_row(
        missing_generic_row,
        handoff_schema,
    )
    dropped_brief_row = dict(row)
    dropped_brief_route = dict(row["standalone_route"])
    dropped_brief_route.pop("llm_route_planner_route_planning_brief", None)
    dropped_brief_row["standalone_route"] = dropped_brief_route
    assert (
        "standalone_route.llm_route_planner_route_planning_brief missing"
        in validate_route_replan_handoff_row(
            dropped_brief_row,
            handoff_schema,
        )
    )
    dropped_route_option_brief_row = dict(row)
    dropped_route_option_brief_route = dict(row["standalone_route"])
    dropped_route_option_brief_route.pop(
        "llm_route_planner_route_option_selection_brief",
        None,
    )
    dropped_route_option_brief_row["standalone_route"] = (
        dropped_route_option_brief_route
    )
    assert (
        "standalone_route.llm_route_planner_route_option_selection_brief missing"
        in validate_route_replan_handoff_row(
            dropped_route_option_brief_row,
            handoff_schema,
        )
    )
    dropped_matrix_witness_row = dict(row)
    dropped_matrix_witness_route = dict(row["standalone_route"])
    dropped_matrix_witness_route.pop(
        "llm_route_planner_primitive_evidence_matrix_witness",
        None,
    )
    dropped_matrix_witness_row["standalone_route"] = dropped_matrix_witness_route
    assert (
        "standalone_route.llm_route_planner_primitive_evidence_matrix_witness missing"
        in validate_route_replan_handoff_row(
            dropped_matrix_witness_row,
            handoff_schema,
        )
    )
    dropped_preconditions_row = dict(row)
    dropped_preconditions_route = dict(row["standalone_route"])
    dropped_preconditions_route.pop(
        "llm_route_planner_route_adoption_preconditions",
        None,
    )
    dropped_preconditions_row["standalone_route"] = dropped_preconditions_route
    assert (
        "standalone_route.llm_route_planner_route_adoption_preconditions missing"
        in validate_route_replan_handoff_row(
            dropped_preconditions_row,
            handoff_schema,
        )
    )
    dropped_target_summary_row = dict(row)
    dropped_target_summary_route = dict(row["standalone_route"])
    dropped_target_summary_route.pop(
        "llm_route_planner_target_context_summary",
        None,
    )
    dropped_target_summary_row["standalone_route"] = (
        dropped_target_summary_route
    )
    assert (
        "standalone_route.llm_route_planner_target_context_summary missing"
        in validate_route_replan_handoff_row(
            dropped_target_summary_row,
            handoff_schema,
        )
    )
    assert seed["routes"][0]["replan_metadata"][
        "revised_informal_knowledge_dag_nodes"
    ] == seed["routes"][0]["revised_informal_knowledge_dag_nodes"]
    assert seed["routes"][0]["replan_metadata"][
        "formal_declaration_hits"
    ] == list(row["formal_declaration_hits"])
    assert seed["routes"][0]["replan_metadata"][
        "revised_formal_realization_dag_nodes"
    ] == seed["routes"][0]["revised_formal_realization_dag_nodes"]
    assert seed["routes"][0]["replan_metadata"][
        "revised_lean_realization_dag_nodes"
    ] == seed["routes"][0]["revised_lean_realization_dag_nodes"]
    assert seed["routes"][0]["replan_metadata"][
        "revised_route_alignment_edges"
    ] == seed["routes"][0]["revised_route_alignment_edges"]
    assert seed["routes"][0]["replan_metadata"]["applied_hook_kinds"] == [
        "resource_response_ledger"
    ]
    assert seed["routes"][0]["replan_metadata"][
        "applied_refinement_evidence_ids"
    ] == ["resource_response_ledger:conditional_rank_argument"]
    assert seed["routes"][0]["replan_metadata"][
        "applied_resource_response_traces"
    ][0]["resource_id"] == "lean_lsp_mcp"
    assert seed["routes"][0]["replan_metadata"][
        "applied_llm_route_planner_hook_traces"
    ][0]["llm_route_planner_row_id"] == "llm_route_row:conditional_rank"
    assert seed["routes"][0]["replan_metadata"][
        "applied_llm_route_planner_hook_traces"
    ][0]["llm_route_planner_source_item"]["resource_id"] == "lean_lsp_mcp"
    assert seed["routes"][0]["replan_metadata"]["residual_goal_contexts"][0][
        "route_repair"
    ] == "add conditional_rank_argument to the informal and formal DAGs"
    assert seed["routes"][0]["replan_metadata"][
        "llm_route_planner_residual_goal_contexts"
    ] == seed["routes"][0]["replan_metadata"]["residual_goal_contexts"]
    assert seed["routes"][0]["residual_goal_contexts"][0][
        "residual_goal"
    ].startswith("conditional_rank_argument")
    assert seed["routes"][0]["replan_metadata"][
        "resource_response_awaiting_request_ids"
    ] == ["request:awaiting-literature"]
    assert seed["routes"][0]["replan_metadata"][
        "resource_response_rejected_request_ids"
    ] == ["request:rejected-proof-state"]
    assert seed["routes"][0]["replan_metadata"][
        "applied_prover_diagnostic_signatures"
    ] == ["missing_source_statement"]
    assert seed["routes"][0]["replan_metadata"]["source_snippets"][0][
        "source_ref"
    ] == "Lei-Wasserman theorem proof route"
    assert (
        "conditional_rank_argument"
        in seed["routes"][0]["replan_metadata"]["alignment_edge_primitives"]
    )
    primitive_by_name = {
        primitive["primitive"]: primitive for primitive in seed["routes"][0]["primitives"]
    }
    assert (
        primitive_by_name["conditional_rank_argument"]["coverage_status"]
        == "source_port_needed"
    )
    assert (
        "conditional_rank_argument: missing source-backed statement"
        in primitive_by_name["conditional_rank_argument"]["side_conditions"]
    )
    assert primitive_by_name["conditional_rank_argument"]["source_snippets"][0][
        "source_ref"
    ] == "Lei-Wasserman theorem proof route"
    assert (
        revised_dag_source_ref
        in primitive_by_name["conditional_rank_argument"]["source_refs"]
    )
    invalid = dict(row)
    invalid.pop("standalone_route")
    assert "standalone_route required" in validate_route_replan_handoff_row(
        invalid,
        route_replan_handoff_row_json_schema(),
    )
    assert (
        handoff_dir / "formalization_gap_planner_route_replan_handoff_row.schema.json"
    ).exists()
    seed_schema = json.loads(
        (
            handoff_dir
            / "formalization_gap_planner_route_replan_standalone_seed.schema.json"
        ).read_text(encoding="utf-8")
    )
    assert seed_schema["$id"] == standalone_input_json_schema()["$id"]
    route_schema = seed_schema["$defs"]["route"]
    assert "source_snippets" in route_schema["properties"]
    assert "source_snippets" in seed_schema["$defs"]["primitive"]["properties"]
    assert (
        "source_snippets"
        in seed_schema["$defs"]["replan_metadata"]["properties"]
    )
    assert (
        route_schema["properties"]["revised_informal_knowledge_dag_nodes"]["items"][
            "$ref"
        ]
        == "#/$defs/dag_node"
    )
    assert (
        route_schema["properties"]["revised_route_alignment_edges"]["items"]["$ref"]
        == "#/$defs/route_alignment_edge"
    )
    assert (
        seed_schema["$defs"]["replan_metadata"]["properties"][
            "revised_formal_realization_dag_nodes"
        ]["items"]["$ref"]
        == "#/$defs/dag_node"
    )
    assert (
        seed_schema["$defs"]["replan_metadata"]["properties"][
            "revised_lean_realization_dag_nodes"
        ]["items"]["$ref"]
        == "#/$defs/dag_node"
    )
    assert "not theorem proof evidence" in payload["proof_evidence_boundary"]

    next_plan = export_formalization_gap_planner_standalone_plan(
        handoff_dir / "formalization_gap_planner_route_replan_standalone_seed.json",
        next_plan_dir,
    )

    assert next_plan["all_ok"]
    assert next_plan["n_goal_plans"] == 1
    assert next_plan["n_route_alignment_edges"] >= 1
    assert next_plan["n_standalone_input_traces"] == 1
    assert next_plan["n_standalone_input_traces_with_replan_metadata"] == 1
    assert next_plan["n_standalone_input_traces_with_source_snippets"] == 1
    assert next_plan["n_standalone_input_traces_with_llm_route_planning_brief"] == 1
    assert (
        next_plan[
            "n_standalone_input_traces_with_llm_route_option_selection_brief"
        ]
        == 1
    )
    assert (
        next_plan[
            "n_standalone_input_traces_with_llm_primitive_evidence_matrix_witness"
        ]
        == 1
    )
    assert (
        next_plan[
            "n_standalone_input_traces_with_complete_llm_primitive_evidence_matrix_accounting"
        ]
        == 1
    )
    assert (
        next_plan[
            "n_standalone_input_traces_with_llm_route_adoption_preconditions"
        ]
        == 1
    )
    assert (
        next_plan[
            "n_standalone_input_traces_with_llm_target_context_summary"
        ]
        == 1
    )
    assert next_plan["n_standalone_input_trace_source_snippets"] == 1
    assert (
        next_plan["n_standalone_input_traces_with_llm_route_planner_hook_traces"]
        == 1
    )
    assert next_plan["n_standalone_input_trace_llm_route_planner_hook_traces"] == 1
    assert next_plan["n_standalone_input_traces_with_residual_goal_contexts"] == 1
    assert next_plan["n_standalone_input_trace_residual_goal_contexts"] == 1
    assert next_plan["n_primitive_source_snippets"] == 1
    next_row = next_plan["rows"][0]
    trace = next_row["standalone_input_trace"]
    assert trace["source_route_id"] == seed["routes"][0]["route_id"]
    assert trace["has_replan_metadata"]
    assert trace["has_llm_route_planner_route_planning_brief"]
    assert trace["llm_route_planner_route_planning_brief"] == route_planning_brief
    assert trace["has_llm_route_planner_route_option_selection_brief"]
    assert trace["llm_route_planner_route_option_selection_brief"] == (
        route_option_selection_brief
    )
    assert trace["has_llm_route_planner_primitive_evidence_matrix_witness"]
    assert trace["llm_route_planner_primitive_evidence_matrix_witness"] == (
        primitive_evidence_matrix_witness
    )
    assert (
        trace[
            "llm_route_planner_primitive_evidence_matrix_accounting_complete"
        ]
        is True
    )
    assert trace["has_llm_route_planner_route_adoption_preconditions"]
    assert trace["llm_route_planner_route_adoption_preconditions"] == (
        route_adoption_preconditions
    )
    assert trace["has_llm_route_planner_target_context_summary"]
    assert trace["llm_route_planner_target_context_summary"] == (
        target_context_summary
    )
    assert trace["replan_metadata"][
        "llm_route_planner_route_planning_brief"
    ] == route_planning_brief
    assert trace["replan_metadata"][
        "llm_route_planner_route_option_selection_brief"
    ] == route_option_selection_brief
    assert trace["replan_metadata"][
        "llm_route_planner_primitive_evidence_matrix_witness"
    ] == primitive_evidence_matrix_witness
    assert trace["replan_metadata"][
        "llm_route_planner_route_adoption_preconditions"
    ] == route_adoption_preconditions
    assert trace["replan_metadata"][
        "llm_route_planner_target_context_summary"
    ] == target_context_summary
    assert trace["has_source_snippets"]
    assert trace["source_snippets"][0]["source_ref"] == (
        "Lei-Wasserman theorem proof route"
    )
    assert trace["primitive_source_snippets"][0]["primitive"] == (
        "conditional_rank_argument"
    )
    assert trace["primitive_source_snippets"][0]["source_snippets"][0][
        "source_ref"
    ] == "Lei-Wasserman theorem proof route"
    assert trace["applied_hook_kinds"] == ["resource_response_ledger"]
    assert trace["applied_refinement_evidence_ids"] == [
        "resource_response_ledger:conditional_rank_argument"
    ]
    assert trace["applied_resource_response_traces"][0]["resource_request_id"] == (
        "request:conditional_rank_argument"
    )
    assert trace["applied_resource_response_traces"][0][
        "minimal_delta_cost_score"
    ] == 60
    assert trace["applied_llm_route_planner_hook_traces"][0][
        "llm_route_planner_request_id"
    ] == "llm_route_request:conditional_rank"
    assert trace["applied_llm_route_planner_hook_traces"][0][
        "minimal_delta_cost_score"
    ] == 60
    assert trace["applied_llm_route_planner_hook_traces"][0][
        "llm_route_planner_queries"
    ] == ["ask Lean LSP for conditional_rank_argument residual goals"]
    assert trace["has_residual_goal_contexts"]
    assert trace["residual_goal_contexts"][0]["repair_action"] == (
        "rerun route planning with conditional_rank_argument"
    )
    assert trace["replan_metadata"]["residual_goal_contexts"] == trace[
        "residual_goal_contexts"
    ]
    assert trace["resource_response_awaiting_request_ids"] == [
        "request:awaiting-literature"
    ]
    assert trace["resource_response_rejected_request_ids"] == [
        "request:rejected-proof-state"
    ]
    assert trace["applied_prover_diagnostic_signatures"] == [
        "missing_source_statement"
    ]
    assert trace["revised_informal_knowledge_dag_nodes"]
    assert trace["revised_formal_realization_dag_nodes"] == trace[
        "revised_lean_realization_dag_nodes"
    ]
    assert trace["revised_lean_realization_dag_nodes"]
    assert trace["revised_route_alignment_edges"]
    assert any(
        packet["primitive"] == "conditional_rank_argument"
        for packet in next_plan["rows"][0]["portable_work_packets"]
    )
    conditional_nodes = [
        node
        for node in next_row["source_discovery_nodes"]
        if node["primitive"] == "conditional_rank_argument"
    ]
    assert conditional_nodes[0]["source_snippets"][0]["source_ref"] == (
        "Lei-Wasserman theorem proof route"
    )


def test_route_replan_handoff_preserves_overlay_target_prover_family_for_rocq() -> None:
    root = Path("runs/test_formalization_gap_planner_route_replan_handoff_rocq")
    input_json = root / "standalone_input.json"
    plan_dir = root / "plan"
    overlay_dir = root / "overlay"
    handoff_dir = root / "handoff"
    next_plan_dir = root / "next_plan"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    overlay_dir.mkdir(parents=True, exist_ok=True)
    input_json.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "component_name": "formalization_gap_planner_standalone_input",
                "target_prover_family": "lean4",
                "library_snapshot_ref": "mixed-prover:fixture",
                "routes": [
                    {
                        "display_name": "rocq_exchangeability_bridge",
                        "theorem_statement": "A Rocq exchangeability bridge is needed.",
                        "theorem_skeleton": "Theorem rocq_exchangeability_bridge : True.",
                        "source_refs": ["rocq exchangeability note"],
                        "primitives": [
                            {
                                "primitive": "rocq_exchangeability_bridge",
                                "coverage_status": "bridge_needed",
                                "candidate_declarations": [
                                    "Rocq.Probability.exchangeable"
                                ],
                                "source_refs": ["rocq exchangeability note"],
                                "cost": 5,
                            }
                        ],
                    }
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    plan_payload = export_formalization_gap_planner_standalone_plan(input_json, plan_dir)
    plan_row = plan_payload["rows"][0]
    overlay_row = {
        "route_revision_overlay_id": "overlay:rocq_exchangeability_bridge",
        "goal_plan_id": plan_row["goal_plan_id"],
        "route_id": plan_row["route_id"],
        "display_name": plan_row["display_name"],
        "target_prover_family": "rocq",
        "revision_status": "ROUTE_REVISION_APPLIED",
        "original_selected_primitives": plan_row["selected_primitives"],
        "revised_selected_primitives": plan_row["selected_primitives"],
        "added_primitives": [],
        "removed_primitives": [],
        "original_delta_primitives": [
            node["primitive"]
            for node in plan_row["minimal_additional_formalization_nodes"]
        ],
        "revised_delta_primitives": [
            node["primitive"]
            for node in plan_row["minimal_additional_formalization_nodes"]
        ],
        "added_delta_primitives": [],
        "source_refs": ["rocq exchangeability note"],
        "formal_declaration_hits": [
            {
                "primitive": "rocq_exchangeability_bridge",
                "coverage_status": "bridge_needed",
                "declaration": "Rocq.Probability.exchangeable",
            }
        ],
        "route_revision_reasons": ["Rocq declaration search selected the target library"],
        "route_revision_summaries": ["preserve Rocq target for replay"],
        "revised_informal_knowledge_dag_nodes": [
            {
                "node_id": "informal:rocq_exchangeability_bridge",
                "label": "rocq_exchangeability_bridge",
                "primitive": "rocq_exchangeability_bridge",
                "source_ref": "rocq exchangeability note",
            }
        ],
        "revised_formal_realization_dag_nodes": [
            {
                "node_id": "formal:rocq_exchangeability_bridge",
                "label": "rocq_exchangeability_bridge",
                "primitive": "rocq_exchangeability_bridge",
                "coverage_status": "bridge_needed",
            }
        ],
        "revised_route_alignment_edges": [
            {
                "source": "informal:rocq_exchangeability_bridge",
                "target": "formal:rocq_exchangeability_bridge",
                "kind": "aligned_to_formal_realization_candidate",
                "edge_type": "revised_informal_to_formal_alignment",
                "primitive": "rocq_exchangeability_bridge",
                "alignment_status": "bridge_needed",
            }
        ],
        "unaligned_primitives": [],
    }
    (overlay_dir / "formalization_gap_planner_route_revision_overlay_manifest.json").write_text(
        json.dumps(
            {
                "component_name": "formalization_gap_planner_route_revision_overlay",
                "rows": [overlay_row],
                "all_ok": True,
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    payload = export_formalization_gap_planner_route_replan_handoff(
        plan_dir,
        overlay_dir,
        handoff_dir,
    )

    assert payload["all_ok"]
    assert payload["n_revised_formal_realization_dag_nodes"] >= 1
    assert payload["n_revised_lean_realization_dag_nodes"] == 0
    row = payload["rows"][0]
    assert row["revised_formal_realization_dag_nodes"]
    assert row["revised_lean_realization_dag_nodes"] == ()
    assert row["formal_declaration_hits"] == (
        {
            "primitive": "rocq_exchangeability_bridge",
            "coverage_status": "bridge_needed",
            "declaration": "Rocq.Probability.exchangeable",
        },
    )
    assert row["lean_declaration_hits"] == ()
    assert row["standalone_route"]["target_prover_family"] == "rocq"
    assert row["standalone_route"]["replan_metadata"]["target_prover_family"] == "rocq"
    assert row["standalone_route"]["revised_formal_realization_dag_nodes"]
    assert row["standalone_route"]["revised_lean_realization_dag_nodes"] == ()
    assert row["standalone_route"]["replan_metadata"][
        "revised_formal_realization_dag_nodes"
    ]
    assert row["standalone_route"]["replan_metadata"][
        "revised_lean_realization_dag_nodes"
    ] == ()
    seed_path = handoff_dir / "formalization_gap_planner_route_replan_standalone_seed.json"
    seed = json.loads(seed_path.read_text(encoding="utf-8"))
    assert seed["target_prover_family"] == "rocq"
    assert seed["routes"][0]["target_prover_family"] == "rocq"
    assert seed["routes"][0]["replan_metadata"]["target_prover_family"] == "rocq"
    assert seed["routes"][0]["revised_formal_realization_dag_nodes"]
    assert seed["routes"][0]["revised_lean_realization_dag_nodes"] == []
    assert seed["routes"][0]["replan_metadata"][
        "revised_formal_realization_dag_nodes"
    ]
    assert seed["routes"][0]["replan_metadata"][
        "revised_lean_realization_dag_nodes"
    ] == []
    assert seed["routes"][0]["replan_metadata"]["formal_declaration_hits"] == [
        {
            "primitive": "rocq_exchangeability_bridge",
            "coverage_status": "bridge_needed",
            "declaration": "Rocq.Probability.exchangeable",
        }
    ]
    assert seed["routes"][0]["replan_metadata"]["lean_declaration_hits"] == []
    bad_legacy_alias_row = dict(row)
    bad_legacy_alias_row["lean_declaration_hits"] = [
        {
            "primitive": "rocq_exchangeability_bridge",
            "declaration": "Rocq.Probability.exchangeable",
            "target_prover_family": "rocq",
        }
    ]
    assert (
        "lean_declaration_hits is a Lean-only legacy alias; non-Lean route replan "
        "handoff rows must use formal_declaration_hits only"
        in validate_route_replan_handoff_row(
            bad_legacy_alias_row,
            route_replan_handoff_row_json_schema(),
        )
    )
    bad_source_type_row = dict(row)
    bad_source_type_row["formal_declaration_hits"] = [
        {
            "primitive": "rocq_exchangeability_bridge",
            "declaration": "Mathlib.Probability.exchangeable",
            "source_type": "lean_library",
        }
    ]
    assert (
        "formal_declaration_hits[0].source_type implies lean4 "
        "but row target_prover_family is rocq"
        in validate_route_replan_handoff_row(
            bad_source_type_row,
            route_replan_handoff_row_json_schema(),
        )
    )
    coq_alias_row = dict(row)
    coq_alias_row["formal_declaration_hits"] = [
        {
            "primitive": "rocq_exchangeability_bridge",
            "declaration": "Rocq.Probability.exchangeable",
            "target_prover_family": "coq",
        }
    ]
    assert validate_route_replan_handoff_row(
        coq_alias_row,
        route_replan_handoff_row_json_schema(),
    ) == ()

    next_plan = export_formalization_gap_planner_standalone_plan(
        seed_path,
        next_plan_dir,
    )

    assert next_plan["all_ok"]
    assert next_plan["target_prover_family"] == "rocq"
    assert next_plan["rows"][0]["target_prover_family"] == "rocq"
    assert next_plan["rows"][0]["standalone_input_trace"][
        "target_prover_family"
    ] == "rocq"
    assert next_plan["rows"][0]["standalone_input_trace"][
        "revised_formal_realization_dag_nodes"
    ]
    assert next_plan["rows"][0]["standalone_input_trace"][
        "revised_lean_realization_dag_nodes"
    ] == []
