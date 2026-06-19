from __future__ import annotations

import json
import shutil
from pathlib import Path

from ai_statistician.formalization_gap_planner_route_replan_handoff import (
    PROOF_EVIDENCE_BOUNDARY,
    PROOF_EVIDENCE_STATUS,
)
from ai_statistician.formalization_gap_planner_route_replan_handoff_audit import (
    audit_formalization_gap_planner_route_replan_handoff,
    route_replan_handoff_audit_row_json_schema,
    validate_route_replan_handoff_audit_row,
)
from ai_statistician.formalization_gap_planner_standalone import (
    standalone_input_json_schema,
)


def test_route_replan_handoff_audit_roundtrips_seed_and_blocks_proof_claims() -> None:
    root = Path("runs/test_formalization_gap_planner_route_replan_handoff_audit")
    handoff_dir = root / "handoff"
    audit_dir = root / "audit"
    metadata_audit_dir = root / "metadata_audit"
    quality_audit_dir = root / "quality_audit"
    reject_audit_dir = root / "reject_audit"
    shutil.rmtree(root, ignore_errors=True)
    handoff_dir.mkdir(parents=True, exist_ok=True)
    route_id = "replan_route:rank_uniformity_fixture"
    route_planning_brief = {
        "brief_kind": "formalization_gap_planner_llm_route_planner_route_planning_brief",
        "route_id": "rank_uniformity_fixture",
        "display_name": "split_conformal_rank_uniformity",
        "target_prover_family": "lean4",
        "planner_focus": [
            {
                "focus_id": "close_rank_uniformity_bridge",
                "priority": 1,
                "action": "preserve rank_uniformity as the next bridge lemma",
                "reason": "the residual goal names the same primitive",
                "target_primitives": ["rank_uniformity"],
            }
        ],
        "evidence_gaps": [
            {
                "gap_id": "rank_uniformity_source_snippet",
                "gap_kind": "source_grounding",
                "recommended_action": "keep source-backed rank-uniformity snippets attached",
                "target_primitives": ["rank_uniformity"],
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
        "route_id": "rank_uniformity_fixture",
        "display_name": "split_conformal_rank_uniformity",
        "target_prover_family": "lean4",
        "library_snapshot_ref": "mathlib4:replan-audit-fixture",
        "cost_policy_id": (
            "formalization_gap_planner_minimal_delta_cost_policy:1"
        ),
        "selection_rule": (
            "Choose the route option with the lowest library-aware route cost."
        ),
        "n_candidate_route_options": 1,
        "n_candidate_route_option_primitives": 1,
        "n_lower_bound_tied_route_options": 1,
        "lower_bound_selected_route_option_id": "route_option:rank_bridge",
        "lower_bound_selected_route_cost": 5.0,
        "candidate_route_options": [
            {
                "route_option_id": "route_option:rank_bridge",
                "route_cost": 5.0,
                "selected_primitives": ["rank_uniformity"],
                "n_selected_primitives": 1,
                "selected_by_lower_bound_policy": True,
                "lower_bound_tied_for_best": True,
                "primitive_costs": [
                    {"primitive": "rank_uniformity", "cost": 5.0}
                ],
                "cost_rationale": "Add one rank-uniformity bridge.",
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
        "route_id": "rank_uniformity_fixture",
        "primitive_evidence_matrix": [
            {
                "primitive": "rank_uniformity",
                "source_evidence_status": "source_backed",
                "formal_reuse_status": "bridge_needed",
                "delta_status": "delta_needed",
            }
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
    alignment_edges = [
        {
            "source": "informal:rank_uniformity",
            "target": "lean:rank_uniformity",
            "kind": "aligned_to_formal_realization_candidate",
            "edge_type": "revised_informal_to_formal_alignment",
            "primitive": "rank_uniformity",
            "alignment_status": "bridge_needed",
        }
    ]
    informal_nodes = [
        {
            "node_id": "informal:rank_uniformity",
            "label": "rank_uniformity",
            "primitive": "rank_uniformity",
        }
    ]
    lean_nodes = [
        {
            "node_id": "lean:rank_uniformity",
            "label": "rank_uniformity",
            "primitive": "rank_uniformity",
            "coverage_status": "bridge_needed",
        }
    ]
    resource_response_trace = {
        "resource_response_ledger_id": "rank_uniformity",
        "resource_request_id": "request:rank_uniformity",
        "resource_id": "lean_lsp_mcp",
        "target_primitives": ["rank_uniformity"],
        "request_phase": "frontier_escalation",
        "expected_response_artifact": "proof_state_or_prover_feedback_response",
        "acceptance_status": "ACCEPTED_WITH_ROUTE_REVISION",
        "matched_response_contract_fields": ["residual_goals"],
        "missing_response_contract_fields": [],
        "prover_attempt_status": "failed_with_residual_goals",
        "prover_diagnostic_signature": "missing_rank_uniformity_bridge",
        "proof_evidence_boundary": "not theorem proof evidence",
    }
    llm_route_planner_hook_trace = {
        "trace_kind": "llm_route_planner_hook_trace",
        "llm_route_planner_row_id": "llm-route-row:rank-uniformity",
        "llm_route_planner_request_id": "llm-route-request:rank-uniformity",
        "llm_route_planner_hook_kind": "proof_state_feedback",
        "llm_route_planner_source_kind": "planner_next_action",
        "llm_route_planner_source_index": 0,
        "llm_route_planner_queries": [
            "inspect rank_uniformity proof-state residuals"
        ],
        "llm_route_planner_source_item": {
            "action": "inspect rank_uniformity proof-state residuals",
            "resource_id": "lean_lsp_mcp",
            "target_primitives": ["rank_uniformity"],
        },
        "target_primitives": ["rank_uniformity"],
        "resource_id": "lean_lsp_mcp",
        "proof_evidence_boundary": "not theorem proof evidence",
    }
    source_snippet = {
        "source_ref": "Lei-Wasserman distribution-free prediction",
        "claim": "exchangeability supports rank uniformity",
        "excerpt": "The source route supplies the rank-uniformity bridge used by the replan seed.",
        "target_primitives": ["rank_uniformity"],
    }
    quality_controls = {
        "resource_contract_ids": [
            "formalization_gap_planner_resource_response_contract:lean_lsp_residual_goals"
        ],
        "required_quality_signals": ["diagnostic_signature"],
        "quality_gates": ["residual_goals_source_grounded"],
        "response_validation_signals": ["residual_goals_or_diagnostics_present"],
        "stop_conditions": ["residual interpreted or source search requested"],
    }
    target_context_summary = {
        "summary_kind": (
            "formalization_gap_planner_llm_route_planner_target_context_summary"
        ),
        "route_id": route_id,
        "normalized_objects": ["calibration scores", "test score rank"],
        "normalized_assumptions": [
            "exchangeable calibration and test scores"
        ],
        "normalized_procedures": ["rank-based conformal calibration"],
        "desired_conclusions": ["rank uniformity"],
        "desired_theorem_shapes": ["finite sample rank identity"],
        "proof_source_refs": ["Lei-Wasserman distribution-free prediction"],
        "proof_evidence_status": PROOF_EVIDENCE_STATUS,
        "proof_evidence_boundary": PROOF_EVIDENCE_BOUNDARY,
    }
    route = {
        "route_id": route_id,
        "display_name": "split_conformal_rank_uniformity",
        "theorem_statement": "Split conformal rank is uniform under exchangeability.",
        "theorem_skeleton": "theorem split_conformal_rank_uniformity : True := by trivial",
        "route_class": "bridge_or_wrapper",
        "recommended_action": "rerun standalone planning on revised rank route",
        "llm_route_planner_route_planning_brief": route_planning_brief,
        "llm_route_planner_route_option_selection_brief": (
            route_option_selection_brief
        ),
        "llm_route_planner_route_option_selected_route_option_id": (
            "route_option:rank_bridge"
        ),
        "llm_route_planner_primitive_evidence_matrix_witness": (
            primitive_evidence_matrix_witness
        ),
        "llm_route_planner_route_adoption_preconditions": (
            route_adoption_preconditions
        ),
        "llm_route_planner_target_context_summary": target_context_summary,
        "source_refs": ["Lei-Wasserman distribution-free prediction"],
        "source_snippets": [source_snippet],
        "quality_controls": quality_controls,
        "revised_informal_knowledge_dag_nodes": informal_nodes,
        "revised_formal_realization_dag_nodes": lean_nodes,
        "revised_lean_realization_dag_nodes": lean_nodes,
        "revised_route_alignment_edges": alignment_edges,
        "informal_proof_steps": ["new rank-uniformity bridge is needed before replay"],
        "primitives": [
            {
                "primitive": "rank_uniformity",
                "coverage_status": "bridge_needed",
                "source_refs": ["Lei-Wasserman distribution-free prediction"],
                "source_snippets": [source_snippet],
                "cost": 5,
            }
        ],
        "replan_metadata": {
            "requires_replan": True,
            "applied_proposal_ids": ["proposal:rank_uniformity"],
            "applied_refinement_evidence_ids": [
                "resource_response_ledger:rank_uniformity"
            ],
            "applied_hook_kinds": ["resource_response_ledger"],
            "applied_resource_response_traces": [resource_response_trace],
            "applied_llm_route_planner_hook_traces": [
                llm_route_planner_hook_trace
            ],
            "resource_response_awaiting_request_ids": ["request:awaiting-rank-source"],
            "resource_response_rejected_request_ids": ["request:rejected-rank-proof"],
            "applied_prover_attempt_statuses": ["failed_with_residual_goals"],
            "applied_prover_diagnostic_signatures": ["missing_rank_uniformity_bridge"],
            "route_revision_reasons": ["proof-state feedback exposed rank bridge"],
            "route_revision_summaries": ["add rank-uniformity bridge before replay"],
            "residual_goals": ["rank_uniformity bridge remains open"],
            "source_refs": ["Lei-Wasserman distribution-free prediction"],
            "source_snippets": [source_snippet],
            "quality_controls": quality_controls,
            "llm_route_planner_route_planning_brief": route_planning_brief,
            "llm_route_planner_route_option_selection_brief": (
                route_option_selection_brief
            ),
            "llm_route_planner_route_option_selected_route_option_id": (
                "route_option:rank_bridge"
            ),
            "llm_route_planner_primitive_evidence_matrix_witness": (
                primitive_evidence_matrix_witness
            ),
            "llm_route_planner_route_adoption_preconditions": (
                route_adoption_preconditions
            ),
            "llm_route_planner_target_context_summary": (
                target_context_summary
            ),
            "lean_declaration_hits": [
                {"primitive": "rank_uniformity", "declaration": "Fintype.card"}
            ],
            "revised_informal_knowledge_dag_nodes": informal_nodes,
            "revised_formal_realization_dag_nodes": lean_nodes,
            "revised_lean_realization_dag_nodes": lean_nodes,
            "revised_route_alignment_edges": alignment_edges,
            "alignment_edge_primitives": ["rank_uniformity"],
            "proof_evidence_status": PROOF_EVIDENCE_STATUS,
        },
    }
    seed = {
        "schema_version": 1,
        "component_name": "formalization_gap_planner_standalone_input",
        "target_prover_family": "lean4",
        "library_snapshot_ref": "mathlib4:replan-audit-fixture",
        "routes": [route],
        "proof_evidence_status": PROOF_EVIDENCE_STATUS,
        "proof_evidence_boundary": PROOF_EVIDENCE_BOUNDARY,
    }
    row = {
        "route_replan_handoff_id": "formalization_gap_planner_route_replan_handoff:fixture",
        "route_revision_overlay_id": "overlay:fixture",
        "goal_plan_id": "goal:fixture",
        "route_id": "source_route:fixture",
        "display_name": "split_conformal_rank_uniformity",
        "revision_status": "ROUTE_REVISION_APPLIED",
        "stability_decision": "APPLY_ROUTE_REVISION_AND_REPLAN",
        "requires_replan": True,
        "added_primitives": ["rank_uniformity"],
        "added_delta_primitives": ["rank_uniformity"],
        "residual_goals": ["rank_uniformity bridge remains open"],
        "applied_proposal_ids": ["proposal:rank_uniformity"],
        "applied_refinement_evidence_ids": [
            "resource_response_ledger:rank_uniformity"
        ],
        "applied_hook_kinds": ["resource_response_ledger"],
        "applied_resource_response_traces": [resource_response_trace],
        "applied_llm_route_planner_hook_traces": [llm_route_planner_hook_trace],
        "resource_response_awaiting_request_ids": ["request:awaiting-rank-source"],
        "resource_response_rejected_request_ids": ["request:rejected-rank-proof"],
        "applied_prover_attempt_statuses": ["failed_with_residual_goals"],
        "applied_prover_diagnostic_signatures": ["missing_rank_uniformity_bridge"],
        "route_revision_reasons": ["proof-state feedback exposed rank bridge"],
        "route_revision_summaries": ["add rank-uniformity bridge before replay"],
        "route_planning_brief": route_planning_brief,
        "route_option_selection_brief": route_option_selection_brief,
        "primitive_evidence_matrix_witness": primitive_evidence_matrix_witness,
        "route_adoption_preconditions": route_adoption_preconditions,
        "target_context_summary": target_context_summary,
        "source_refs": ["Lei-Wasserman distribution-free prediction"],
        "source_snippets": [source_snippet],
        "quality_controls": quality_controls,
        "lean_declaration_hits": [
            {"primitive": "rank_uniformity", "declaration": "Fintype.card"}
        ],
        "revised_informal_knowledge_dag_nodes": informal_nodes,
        "revised_formal_realization_dag_nodes": lean_nodes,
        "revised_lean_realization_dag_nodes": lean_nodes,
        "revised_selected_primitives": ["rank_uniformity"],
        "revised_route_alignment_edges": alignment_edges,
        "unaligned_primitives": [],
        "standalone_route_id": route_id,
        "next_commands": [
            "formalization-gap-planner-standalone-plan --input formalization_gap_planner_route_replan_standalone_seed.json",
            "formalization-gap-planner-component-resource-registry --out <formalization_gap_planner_component_resource_registry_dir>",
            (
                "formalization-gap-planner-llm-route-planner "
                "--input formalization_gap_planner_route_replan_standalone_seed.json "
                "--provider anthropic --model-tier auto --max-repair-attempts 1 "
                "--formalization-gap-planner-route-revision-overlay-dir "
                "<formalization_gap_planner_route_revision_overlay_dir> "
                "--formalization-gap-planner-route-replan-handoff-dir "
                "<formalization_gap_planner_route_replan_handoff_dir> "
                "--formalization-gap-planner-component-resource-registry-dir "
                "<formalization_gap_planner_component_resource_registry_dir> "
                "--out <formalization_gap_planner_route_replan_llm_route_planner_prompt_dir>"
            ),
            (
                "formalization-gap-planner-llm-route-planner "
                "--input formalization_gap_planner_route_replan_standalone_seed.json "
                "--provider anthropic --model-tier auto --max-repair-attempts 1 "
                "--formalization-gap-planner-route-revision-overlay-dir "
                "<formalization_gap_planner_route_revision_overlay_dir> "
                "--formalization-gap-planner-route-replan-handoff-dir "
                "<formalization_gap_planner_route_replan_handoff_dir> "
                "--formalization-gap-planner-component-resource-registry-dir "
                "<formalization_gap_planner_component_resource_registry_dir> "
                "--invoke-provider "
                "--out <formalization_gap_planner_route_replan_llm_route_planner_live_dir>"
            ),
        ],
        "proof_evidence_status": PROOF_EVIDENCE_STATUS,
        "proof_evidence_boundary": PROOF_EVIDENCE_BOUNDARY,
        "ok": True,
        "errors": [],
    }
    manifest = {
        "schema_version": 1,
        "component_name": "formalization_gap_planner_route_replan_handoff",
        "n_handoff_rows": 1,
        "n_standalone_seed_routes": 1,
        "n_route_alignment_edges": 1,
        "n_unaligned_primitives": 0,
        "n_ok": 1,
        "all_ok": True,
        "rows": [row],
        "proof_evidence_status": PROOF_EVIDENCE_STATUS,
        "proof_evidence_boundary": PROOF_EVIDENCE_BOUNDARY,
    }
    (handoff_dir / "formalization_gap_planner_route_replan_handoff_manifest.json").write_text(
        json.dumps(manifest, indent=2),
        encoding="utf-8",
    )
    (handoff_dir / "formalization_gap_planner_route_replan_standalone_seed.json").write_text(
        json.dumps(seed, indent=2),
        encoding="utf-8",
    )
    (
        handoff_dir
        / "formalization_gap_planner_route_replan_standalone_seed.schema.json"
    ).write_text(
        json.dumps(standalone_input_json_schema(), indent=2),
        encoding="utf-8",
    )
    (handoff_dir / "formalization_gap_planner_route_replan_handoff.jsonl").write_text(
        json.dumps(row, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (handoff_dir / "formalization_gap_planner_route_replan_handoff.md").write_text(
        "# handoff\nnot theorem proof evidence\n",
        encoding="utf-8",
    )

    payload = audit_formalization_gap_planner_route_replan_handoff(
        handoff_dir,
        audit_dir,
    )

    assert payload["all_ok"]
    assert payload["n_failed"] == 0
    assert payload["n_row_schema_valid"] == payload["n_checks"]
    assert payload["n_row_schema_invalid"] == 0
    assert payload["route_replan_handoff_audit_row_schema"]["$id"] == (
        "urn:ai-statistician:schemas:formalization-gap-planner-route-replan-handoff-audit-row:1"
    )
    assert payload["roundtrip_all_ok"]
    assert payload["n_roundtrip_goal_plans"] == 1
    assert payload["n_roundtrip_route_alignment_edges"] >= 1
    assert payload["n_roundtrip_standalone_input_traces"] == 1
    assert payload["n_roundtrip_standalone_input_traces_with_replan_metadata"] == 1
    assert (
        payload["n_roundtrip_standalone_input_trace_llm_route_planner_hook_traces"]
        == 1
    )
    assert (
        payload[
            "n_roundtrip_standalone_input_traces_with_llm_route_planner_hook_traces"
        ]
        == 1
    )
    assert (
        payload[
            "n_roundtrip_standalone_input_traces_with_llm_route_planning_brief"
        ]
        == 1
    )
    assert (
        payload[
            "n_roundtrip_standalone_input_traces_with_llm_route_option_selection_brief"
        ]
        == 1
    )
    assert (
        payload[
            "n_roundtrip_standalone_input_traces_with_llm_primitive_evidence_matrix_witness"
        ]
        == 1
    )
    assert (
        payload[
            "n_roundtrip_standalone_input_traces_with_complete_llm_primitive_evidence_matrix_accounting"
        ]
        == 1
    )
    assert (
        payload[
            "n_roundtrip_standalone_input_traces_with_llm_route_adoption_preconditions"
        ]
        == 1
    )
    assert (
        payload[
            "n_roundtrip_standalone_input_traces_with_llm_target_context_summary"
        ]
        == 1
    )
    assert (
        payload[
            "n_roundtrip_standalone_input_trace_llm_route_adoption_precondition_blockers"
        ]
        == 1
    )
    assert (
        payload[
            "n_roundtrip_standalone_input_trace_llm_route_adoption_precondition_target_primitives"
        ]
        == 1
    )
    route_adoption_check = next(
        check
        for check in payload["checks"]
        if check["check_name"] == "roundtrip_llm_route_adoption_preconditions_trace"
    )
    assert "expected_target_primitives=1" in route_adoption_check["observed"]
    assert "roundtrip_target_primitives=1" in route_adoption_check["observed"]
    assert any(
        check["check_name"] == "standalone_seed_no_kernel_verified_claims" and check["ok"]
        for check in payload["checks"]
    )
    ok_checks = {
        check["check_name"]
        for check in payload["checks"]
        if check["ok"]
    }
    assert "handoff_alignment_edges_present" in ok_checks
    assert "handoff_no_unaligned_primitives" in ok_checks
    assert "standalone_seed_schema_id" in ok_checks
    assert "roundtrip_alignment_edges" in ok_checks
    assert "roundtrip_alignment_contract" in ok_checks
    assert "roundtrip_standalone_input_trace" in ok_checks
    assert "roundtrip_llm_route_planner_hook_trace" in ok_checks
    assert "row_0_next_llm_prompt_command" in ok_checks
    assert "row_0_next_llm_live_command" in ok_checks
    assert "row_0_seed_route_alignment_metadata" in ok_checks
    assert "row_0_seed_route_revised_dags" in ok_checks
    assert "row_0_seed_route_provenance_metadata" in ok_checks
    assert "row_0_seed_route_source_snippets" in ok_checks
    assert "row_0_seed_route_quality_controls" in ok_checks
    assert "row_0_seed_route_llm_route_planning_brief" in ok_checks
    assert "row_0_seed_route_llm_route_option_selection_brief" in ok_checks
    assert "row_0_seed_route_llm_primitive_evidence_matrix_witness" in ok_checks
    assert "row_0_seed_route_llm_route_adoption_preconditions" in ok_checks
    assert "row_0_seed_route_llm_target_context_summary" in ok_checks
    assert "roundtrip_llm_route_planning_brief_trace" in ok_checks
    assert "roundtrip_llm_route_option_selection_brief_trace" in ok_checks
    assert "roundtrip_llm_primitive_evidence_matrix_witness_trace" in ok_checks
    assert "roundtrip_llm_route_adoption_preconditions_trace" in ok_checks
    assert "roundtrip_llm_target_context_summary_trace" in ok_checks
    provenance_check = next(
        check
        for check in payload["checks"]
        if check["check_name"] == "row_0_seed_route_provenance_metadata"
    )
    assert "resource_response_awaiting_request_ids=1" in provenance_check["observed"]
    assert "resource_response_rejected_request_ids=1" in provenance_check["observed"]
    assert "applied_llm_route_planner_hook_traces=1" in provenance_check["observed"]
    snippet_check = next(
        check
        for check in payload["checks"]
        if check["check_name"] == "row_0_seed_route_source_snippets"
    )
    assert "metadata=1/1" in snippet_check["observed"]
    assert "primitive=1/1" in snippet_check["observed"]
    quality_check = next(
        check
        for check in payload["checks"]
        if check["check_name"] == "row_0_seed_route_quality_controls"
    )
    assert "row=resource_contract_ids=1" in quality_check["observed"]
    assert "metadata=resource_contract_ids=1" in quality_check["observed"]
    llm_hook_roundtrip_check = next(
        check
        for check in payload["checks"]
        if check["check_name"] == "roundtrip_llm_route_planner_hook_trace"
    )
    assert "expected=1" in llm_hook_roundtrip_check["observed"]
    assert "trace=1" in llm_hook_roundtrip_check["observed"]
    assert "trace_metadata=1" in llm_hook_roundtrip_check["observed"]
    brief_check = next(
        check
        for check in payload["checks"]
        if check["check_name"] == "row_0_seed_route_llm_route_planning_brief"
    )
    assert "row=True" in brief_check["observed"]
    assert "route=True" in brief_check["observed"]
    assert "metadata=True" in brief_check["observed"]
    route_option_brief_check = next(
        check
        for check in payload["checks"]
        if check["check_name"] == "row_0_seed_route_llm_route_option_selection_brief"
    )
    assert "row=True" in route_option_brief_check["observed"]
    assert "route=True" in route_option_brief_check["observed"]
    assert "metadata=True" in route_option_brief_check["observed"]
    assert "candidate_options=1" in route_option_brief_check["observed"]
    matrix_witness_check = next(
        check
        for check in payload["checks"]
        if check["check_name"]
        == "row_0_seed_route_llm_primitive_evidence_matrix_witness"
    )
    assert "row=True" in matrix_witness_check["observed"]
    assert "route=True" in matrix_witness_check["observed"]
    assert "metadata=True" in matrix_witness_check["observed"]
    assert "matrix_rows=1" in matrix_witness_check["observed"]
    assert "accounting_complete=True" in matrix_witness_check["observed"]
    precondition_check = next(
        check
        for check in payload["checks"]
        if check["check_name"] == "row_0_seed_route_llm_route_adoption_preconditions"
    )
    assert "row=True" in precondition_check["observed"]
    assert "route=True" in precondition_check["observed"]
    assert "metadata=True" in precondition_check["observed"]
    assert "blockers=1" in precondition_check["observed"]
    target_summary_check = next(
        check
        for check in payload["checks"]
        if check["check_name"] == "row_0_seed_route_llm_target_context_summary"
    )
    assert "row=True" in target_summary_check["observed"]
    assert "route=True" in target_summary_check["observed"]
    assert "metadata=True" in target_summary_check["observed"]
    assert "objects=2" in target_summary_check["observed"]
    assert "assumptions=1" in target_summary_check["observed"]
    brief_roundtrip_check = next(
        check
        for check in payload["checks"]
        if check["check_name"] == "roundtrip_llm_route_planning_brief_trace"
    )
    assert "seed_routes_with_brief=1" in brief_roundtrip_check["observed"]
    assert "trace_matches=1" in brief_roundtrip_check["observed"]
    assert "metadata_matches=1" in brief_roundtrip_check["observed"]
    route_option_brief_roundtrip_check = next(
        check
        for check in payload["checks"]
        if check["check_name"]
        == "roundtrip_llm_route_option_selection_brief_trace"
    )
    assert (
        "seed_routes_with_brief=1"
        in route_option_brief_roundtrip_check["observed"]
    )
    assert "trace_matches=1" in route_option_brief_roundtrip_check["observed"]
    assert "metadata_matches=1" in route_option_brief_roundtrip_check["observed"]
    matrix_witness_roundtrip_check = next(
        check
        for check in payload["checks"]
        if check["check_name"]
        == "roundtrip_llm_primitive_evidence_matrix_witness_trace"
    )
    assert "seed_routes_with_witness=1" in matrix_witness_roundtrip_check[
        "observed"
    ]
    assert "trace_matches=1" in matrix_witness_roundtrip_check["observed"]
    assert "metadata_matches=1" in matrix_witness_roundtrip_check["observed"]
    assert "expected_repair_obligations=0" in matrix_witness_roundtrip_check[
        "observed"
    ]
    precondition_roundtrip_check = next(
        check
        for check in payload["checks"]
        if check["check_name"] == "roundtrip_llm_route_adoption_preconditions_trace"
    )
    assert "seed_routes_with_preconditions=1" in precondition_roundtrip_check[
        "observed"
    ]
    assert "trace_matches=1" in precondition_roundtrip_check["observed"]
    assert "metadata_matches=1" in precondition_roundtrip_check["observed"]
    target_summary_roundtrip_check = next(
        check
        for check in payload["checks"]
        if check["check_name"] == "roundtrip_llm_target_context_summary_trace"
    )
    assert "seed_routes_with_summary=1" in target_summary_roundtrip_check[
        "observed"
    ]
    assert "trace_matches=1" in target_summary_roundtrip_check["observed"]
    assert "metadata_matches=1" in target_summary_roundtrip_check["observed"]
    assert (
        audit_dir
        / "formalization_gap_planner_route_replan_handoff_audit_row.schema.json"
    ).exists()
    assert (
        audit_dir
        / "formalization_gap_planner_route_replan_roundtrip_plan"
        / "goal_conditioned_minimal_formalization_plan_manifest.json"
    ).exists()
    assert "check_name required" in validate_route_replan_handoff_audit_row(
        {"schema_version": 1},
        route_replan_handoff_audit_row_json_schema(),
    )

    metadata_rejected_seed = json.loads(json.dumps(seed))
    metadata_rejected_seed["routes"][0]["replan_metadata"][
        "resource_response_awaiting_request_ids"
    ] = []
    (handoff_dir / "formalization_gap_planner_route_replan_standalone_seed.json").write_text(
        json.dumps(metadata_rejected_seed, indent=2),
        encoding="utf-8",
    )
    metadata_rejected = audit_formalization_gap_planner_route_replan_handoff(
        handoff_dir,
        metadata_audit_dir,
    )

    assert not metadata_rejected["all_ok"]
    metadata_failed = {
        check["check_name"]
        for check in metadata_rejected["checks"]
        if not check["ok"]
    }
    assert "row_0_seed_route_provenance_metadata" in metadata_failed

    snippet_rejected_seed = json.loads(json.dumps(seed))
    snippet_rejected_seed["routes"][0]["replan_metadata"]["source_snippets"] = []
    (handoff_dir / "formalization_gap_planner_route_replan_standalone_seed.json").write_text(
        json.dumps(snippet_rejected_seed, indent=2),
        encoding="utf-8",
    )
    snippet_rejected = audit_formalization_gap_planner_route_replan_handoff(
        handoff_dir,
        metadata_audit_dir,
    )

    assert not snippet_rejected["all_ok"]
    snippet_failed = {
        check["check_name"]
        for check in snippet_rejected["checks"]
        if not check["ok"]
    }
    assert "row_0_seed_route_source_snippets" in snippet_failed

    quality_rejected_seed = json.loads(json.dumps(seed))
    quality_rejected_seed["routes"][0]["replan_metadata"]["quality_controls"][
        "stop_conditions"
    ] = []
    (handoff_dir / "formalization_gap_planner_route_replan_standalone_seed.json").write_text(
        json.dumps(quality_rejected_seed, indent=2),
        encoding="utf-8",
    )
    quality_rejected = audit_formalization_gap_planner_route_replan_handoff(
        handoff_dir,
        quality_audit_dir,
    )

    assert not quality_rejected["all_ok"]
    quality_failed = {
        check["check_name"]
        for check in quality_rejected["checks"]
        if not check["ok"]
    }
    assert "row_0_seed_route_quality_controls" in quality_failed

    brief_rejected_seed = json.loads(json.dumps(seed))
    brief_rejected_seed["routes"][0]["replan_metadata"].pop(
        "llm_route_planner_route_planning_brief",
        None,
    )
    (handoff_dir / "formalization_gap_planner_route_replan_standalone_seed.json").write_text(
        json.dumps(brief_rejected_seed, indent=2),
        encoding="utf-8",
    )
    brief_rejected = audit_formalization_gap_planner_route_replan_handoff(
        handoff_dir,
        root / "brief_audit",
    )

    assert not brief_rejected["all_ok"]
    brief_failed = {
        check["check_name"]
        for check in brief_rejected["checks"]
        if not check["ok"]
    }
    assert "row_0_seed_route_llm_route_planning_brief" in brief_failed

    route_option_brief_rejected_seed = json.loads(json.dumps(seed))
    route_option_brief_rejected_seed["routes"][0]["replan_metadata"].pop(
        "llm_route_planner_route_option_selection_brief",
        None,
    )
    (
        handoff_dir
        / "formalization_gap_planner_route_replan_standalone_seed.json"
    ).write_text(
        json.dumps(route_option_brief_rejected_seed, indent=2),
        encoding="utf-8",
    )
    route_option_brief_rejected = (
        audit_formalization_gap_planner_route_replan_handoff(
            handoff_dir,
            root / "route_option_brief_audit",
        )
    )

    assert not route_option_brief_rejected["all_ok"]
    route_option_brief_failed = {
        check["check_name"]
        for check in route_option_brief_rejected["checks"]
        if not check["ok"]
    }
    assert "row_0_seed_route_llm_route_option_selection_brief" in (
        route_option_brief_failed
    )

    matrix_witness_rejected_seed = json.loads(json.dumps(seed))
    matrix_witness_rejected_seed["routes"][0]["replan_metadata"].pop(
        "llm_route_planner_primitive_evidence_matrix_witness",
        None,
    )
    (
        handoff_dir
        / "formalization_gap_planner_route_replan_standalone_seed.json"
    ).write_text(
        json.dumps(matrix_witness_rejected_seed, indent=2),
        encoding="utf-8",
    )
    matrix_witness_rejected = (
        audit_formalization_gap_planner_route_replan_handoff(
            handoff_dir,
            root / "matrix_witness_audit",
        )
    )

    assert not matrix_witness_rejected["all_ok"]
    matrix_witness_failed = {
        check["check_name"]
        for check in matrix_witness_rejected["checks"]
        if not check["ok"]
    }
    assert "row_0_seed_route_llm_primitive_evidence_matrix_witness" in (
        matrix_witness_failed
    )

    precondition_rejected_seed = json.loads(json.dumps(seed))
    precondition_rejected_seed["routes"][0]["replan_metadata"].pop(
        "llm_route_planner_route_adoption_preconditions",
        None,
    )
    (handoff_dir / "formalization_gap_planner_route_replan_standalone_seed.json").write_text(
        json.dumps(precondition_rejected_seed, indent=2),
        encoding="utf-8",
    )
    precondition_rejected = audit_formalization_gap_planner_route_replan_handoff(
        handoff_dir,
        root / "precondition_audit",
    )

    assert not precondition_rejected["all_ok"]
    precondition_failed = {
        check["check_name"]
        for check in precondition_rejected["checks"]
        if not check["ok"]
    }
    assert "row_0_seed_route_llm_route_adoption_preconditions" in precondition_failed

    target_summary_rejected_seed = json.loads(json.dumps(seed))
    target_summary_rejected_seed["routes"][0]["replan_metadata"].pop(
        "llm_route_planner_target_context_summary",
        None,
    )
    (
        handoff_dir
        / "formalization_gap_planner_route_replan_standalone_seed.json"
    ).write_text(
        json.dumps(target_summary_rejected_seed, indent=2),
        encoding="utf-8",
    )
    target_summary_rejected = audit_formalization_gap_planner_route_replan_handoff(
        handoff_dir,
        root / "target_summary_audit",
    )

    assert not target_summary_rejected["all_ok"]
    target_summary_failed = {
        check["check_name"]
        for check in target_summary_rejected["checks"]
        if not check["ok"]
    }
    assert "row_0_seed_route_llm_target_context_summary" in (
        target_summary_failed
    )

    llm_hook_rejected_seed = json.loads(json.dumps(seed))
    llm_hook_rejected_seed["routes"][0]["replan_metadata"][
        "applied_llm_route_planner_hook_traces"
    ] = []
    (handoff_dir / "formalization_gap_planner_route_replan_standalone_seed.json").write_text(
        json.dumps(llm_hook_rejected_seed, indent=2),
        encoding="utf-8",
    )
    llm_hook_rejected = audit_formalization_gap_planner_route_replan_handoff(
        handoff_dir,
        root / "llm_hook_audit",
    )

    assert not llm_hook_rejected["all_ok"]
    llm_hook_failed = {
        check["check_name"]
        for check in llm_hook_rejected["checks"]
        if not check["ok"]
    }
    assert "row_0_seed_route_provenance_metadata" in llm_hook_failed

    (handoff_dir / "formalization_gap_planner_route_replan_standalone_seed.json").write_text(
        json.dumps(seed, indent=2),
        encoding="utf-8",
    )
    seed["routes"][0]["kernel_verified"] = True
    (handoff_dir / "formalization_gap_planner_route_replan_standalone_seed.json").write_text(
        json.dumps(seed, indent=2),
        encoding="utf-8",
    )
    rejected = audit_formalization_gap_planner_route_replan_handoff(
        handoff_dir,
        reject_audit_dir,
    )

    assert not rejected["all_ok"]
    assert rejected["n_row_schema_valid"] == rejected["n_checks"]
    assert rejected["n_row_schema_invalid"] == 0
    failed = {
        check["check_name"]
        for check in rejected["checks"]
        if not check["ok"]
    }
    assert "standalone_seed_no_kernel_verified_claims" in failed


def test_route_replan_handoff_audit_rejects_non_lean_legacy_declaration_alias() -> None:
    root = Path("runs/test_formalization_gap_planner_route_replan_handoff_audit_rocq_alias")
    handoff_dir = root / "handoff"
    audit_dir = root / "audit"
    shutil.rmtree(root, ignore_errors=True)
    handoff_dir.mkdir(parents=True, exist_ok=True)
    route_id = "replan_route:rocq_rank_fixture"
    alignment_edges = [
        {
            "source": "informal:rank_uniformity",
            "target": "rocq:rank_uniformity",
            "kind": "aligned_to_formal_realization_candidate",
            "edge_type": "revised_informal_to_formal_alignment",
            "primitive": "rank_uniformity",
            "alignment_status": "bridge_needed",
        }
    ]
    formal_nodes = [
        {
            "node_id": "rocq:rank_uniformity",
            "label": "rank_uniformity",
            "primitive": "rank_uniformity",
            "coverage_status": "bridge_needed",
        }
    ]
    legacy_hits = [
        {
            "primitive": "rank_uniformity",
            "declaration": "Rocq.Conformal.rank_uniformity_bridge",
            "target_prover_family": "rocq",
        }
    ]
    route = {
        "route_id": route_id,
        "display_name": "rocq_rank_uniformity",
        "theorem_statement": "A Rocq rank route.",
        "target_prover_family": "rocq",
        "source_refs": ["rocq_conformal_notes"],
        "revised_formal_realization_dag_nodes": formal_nodes,
        "revised_route_alignment_edges": alignment_edges,
        "primitives": [
            {
                "primitive": "rank_uniformity",
                "coverage_status": "bridge_needed",
                "source_refs": ["rocq_conformal_notes"],
            }
        ],
        "replan_metadata": {
            "target_prover_family": "rocq",
            "requires_replan": True,
            "applied_proposal_ids": ["proposal:rocq-rank"],
            "applied_refinement_evidence_ids": ["resource_response_ledger:rocq-rank"],
            "applied_hook_kinds": ["resource_response_ledger"],
            "route_revision_reasons": ["Rocq library search exposed a bridge gap"],
            "route_revision_summaries": ["add the Rocq rank bridge before replay"],
            "source_refs": ["rocq_conformal_notes"],
            "lean_declaration_hits": legacy_hits,
            "revised_formal_realization_dag_nodes": formal_nodes,
            "revised_route_alignment_edges": alignment_edges,
            "alignment_edge_primitives": ["rank_uniformity"],
            "proof_evidence_status": PROOF_EVIDENCE_STATUS,
        },
    }
    seed = {
        "schema_version": 1,
        "component_name": "formalization_gap_planner_standalone_input",
        "target_prover_family": "rocq",
        "library_snapshot_ref": "rocq:replan-audit-fixture",
        "routes": [route],
        "proof_evidence_status": PROOF_EVIDENCE_STATUS,
        "proof_evidence_boundary": PROOF_EVIDENCE_BOUNDARY,
    }
    row = {
        "route_replan_handoff_id": "formalization_gap_planner_route_replan_handoff:rocq-fixture",
        "route_revision_overlay_id": "overlay:rocq-fixture",
        "goal_plan_id": "goal:rocq-fixture",
        "route_id": "source_route:rocq-fixture",
        "display_name": "rocq_rank_uniformity",
        "target_prover_family": "rocq",
        "revision_status": "ROUTE_REVISION_APPLIED",
        "stability_decision": "APPLY_ROUTE_REVISION_AND_REPLAN",
        "requires_replan": True,
        "added_primitives": ["rank_uniformity"],
        "added_delta_primitives": ["rank_uniformity"],
        "applied_proposal_ids": ["proposal:rocq-rank"],
        "applied_refinement_evidence_ids": ["resource_response_ledger:rocq-rank"],
        "applied_hook_kinds": ["resource_response_ledger"],
        "route_revision_reasons": ["Rocq library search exposed a bridge gap"],
        "route_revision_summaries": ["add the Rocq rank bridge before replay"],
        "source_refs": ["rocq_conformal_notes"],
        "lean_declaration_hits": legacy_hits,
        "revised_formal_realization_dag_nodes": formal_nodes,
        "revised_selected_primitives": ["rank_uniformity"],
        "revised_route_alignment_edges": alignment_edges,
        "unaligned_primitives": [],
        "standalone_route_id": route_id,
        "standalone_route": route,
        "next_commands": [
            "formalization-gap-planner-standalone-plan --input formalization_gap_planner_route_replan_standalone_seed.json"
        ],
        "proof_evidence_status": PROOF_EVIDENCE_STATUS,
        "proof_evidence_boundary": PROOF_EVIDENCE_BOUNDARY,
        "ok": True,
        "errors": [],
    }
    manifest = {
        "schema_version": 1,
        "component_name": "formalization_gap_planner_route_replan_handoff",
        "n_handoff_rows": 1,
        "n_standalone_seed_routes": 1,
        "n_route_alignment_edges": 1,
        "n_unaligned_primitives": 0,
        "n_ok": 1,
        "all_ok": True,
        "rows": [row],
        "proof_evidence_status": PROOF_EVIDENCE_STATUS,
        "proof_evidence_boundary": PROOF_EVIDENCE_BOUNDARY,
    }
    (handoff_dir / "formalization_gap_planner_route_replan_handoff_manifest.json").write_text(
        json.dumps(manifest, indent=2),
        encoding="utf-8",
    )
    (handoff_dir / "formalization_gap_planner_route_replan_standalone_seed.json").write_text(
        json.dumps(seed, indent=2),
        encoding="utf-8",
    )
    (
        handoff_dir
        / "formalization_gap_planner_route_replan_standalone_seed.schema.json"
    ).write_text(
        json.dumps(standalone_input_json_schema(), indent=2),
        encoding="utf-8",
    )
    (handoff_dir / "formalization_gap_planner_route_replan_handoff.jsonl").write_text(
        json.dumps(row, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (handoff_dir / "formalization_gap_planner_route_replan_handoff.md").write_text(
        "# handoff\nnot theorem proof evidence\n",
        encoding="utf-8",
    )

    payload = audit_formalization_gap_planner_route_replan_handoff(
        handoff_dir,
        audit_dir,
        run_roundtrip=False,
    )

    assert not payload["all_ok"]
    failed_checks = {
        check["check_name"]: check for check in payload["checks"] if not check["ok"]
    }
    assert "row_0_non_lean_no_lean_declaration_alias" in failed_checks
    observed = failed_checks[
        "row_0_non_lean_no_lean_declaration_alias"
    ]["observed"]
    assert "target_prover_families=rocq" in observed
    assert "lean_declaration_hits=" in observed
