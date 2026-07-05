from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from .fingerprint import stable_hash


EVALUATION_BENCHMARK_GUIDANCE_SCHEMA_VERSION = 1
ARCHITECT_DEFERRED_META_RESOLUTION_REQUIREMENT_ID = (
    "architect_deferred_meta_capability_gaps_resolved"
)


@dataclass(frozen=True)
class BenchmarkSuiteGuidanceRow:
    suite_id: str
    exercised: bool
    status: str
    evidence_paths: tuple[str, ...]
    key_counts: dict[str, object]
    honesty_boundary: str
    issues: tuple[str, ...]


def build_evaluation_benchmark_guidance(
    out_dir: Path | None = None,
    *,
    system_audit_payload: Mapping[str, Any],
    strategy_doc: Path = Path("docs/evaluation_benchmark_strategy.md"),
    suites_file: Path = Path("benchmarks/capability_eval_suites.json"),
    frontier_benchmark_file: Path = Path("benchmarks/frontier_stat_theory_benchmark.json"),
    research_questions_file: Path = Path("examples/research_questions.json"),
) -> dict[str, object]:
    """Summarize whether evaluation artifacts guide capacity improvement.

    This audit is intentionally diagnostic. It does not claim the statistical
    theory lab is complete; it turns release/audit counts into a ranked agenda
    for the next capacity improvements and preserves the boundary between
    routing, retrieval, simulation, and Lean proof evidence.
    """

    counts = dict(system_audit_payload.get("counts", {}) or {})
    artifacts = dict(system_audit_payload.get("artifacts", {}) or {})
    gates = dict(system_audit_payload.get("gates", {}) or {})
    suite_config = _read_json(suites_file)
    frontier_config = _read_json(frontier_benchmark_file)
    research_questions = _read_json(research_questions_file)
    strategy_exists = strategy_doc.exists()
    suite_rows = _suite_rows(
        counts=counts,
        artifacts=artifacts,
        gates=gates,
        suites_file=suites_file,
        frontier_benchmark_file=frontier_benchmark_file,
        research_questions_file=research_questions_file,
    )
    stale_rows = [row for row in suite_rows if row.status in {"STALE_OR_MISSING", "UNDER_SPECIFIED"}]
    misaligned_rows = [row for row in suite_rows if row.status in {"SATURATED", "CAPACITY_GAP"}]
    top_actions = _top_actions(suite_rows, counts)
    payload: dict[str, object] = {
        "schema_version": EVALUATION_BENCHMARK_GUIDANCE_SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "strategy_doc": str(strategy_doc),
        "strategy_doc_present": strategy_exists,
        "suites_file": str(suites_file),
        "suites_defined": len(suite_config.get("suites", [])) if isinstance(suite_config, dict) else 0,
        "frontier_benchmark_file": str(frontier_benchmark_file),
        "frontier_entries": len(frontier_config.get("flat_entries", []))
        if isinstance(frontier_config, dict)
        else 0,
        "research_questions_file": str(research_questions_file),
        "core_research_questions": len(research_questions) if isinstance(research_questions, list) else 0,
        "suites": [asdict(row) for row in suite_rows],
        "n_suites": len(suite_rows),
        "n_exercised": sum(1 for row in suite_rows if row.exercised),
        "n_stale_or_missing": len(stale_rows),
        "n_saturated_or_capacity_gap": len(misaligned_rows),
        "stale_or_missing_suites": tuple(row.suite_id for row in stale_rows),
        "saturated_or_capacity_gap_suites": tuple(row.suite_id for row in misaligned_rows),
        "top_actions": top_actions,
        "all_ok": strategy_exists
        and isinstance(suite_config, dict)
        and len(suite_config.get("suites", [])) >= 9
        and len(suite_rows) >= 9
        and len(top_actions) >= 3,
        "honesty_boundaries": [
            "frontier_supported is routing/scaffold coverage, not solved frontier papers",
            "retrieval/RAG hits are premise suggestions, not Lean proof evidence",
            "simulation diagnostics are empirical evidence, not theorem proofs",
            "formal gaps remain gaps until AXLE/Lean kernel verifies a proof obligation",
        ],
        "guidance_fingerprint": stable_hash(
            {
                "counts": {
                    key: counts.get(key)
                    for key in sorted(counts)
                    if key
                    in {
                        "frontier_questions",
                        "frontier_smoke_questions",
                        "frontier_theory_expected_result_coverage_rate",
                        "formal_gaps",
                        "missing_formal_primitives",
                        "proofs_kernel_verified",
                        "proof_search_kernel_verified",
                        "proof_search_solved",
                        "proof_search_retrieval_ablation_candidate_delta",
                        "proof_search_retrieval_no_registered_ablation_candidate_delta",
                        "proof_search_retrieval_no_registered_ablation_solved_delta",
                        "research_traces_ok",
                        "research_algorithms_ok",
                        "research_agent_runtime_exact_semantic_definition_authoring_required",
                        "research_agent_runtime_exact_semantic_definition_authoring_live_llm_attempted",
                        "research_agent_runtime_exact_semantic_definition_authoring_backend_provider_names",
                        "research_agent_runtime_exact_semantic_definition_authoring_post_runtime_worker_lineage_ok",
                        "research_agent_runtime_exact_semantic_definition_authoring_post_runtime_worker_live_llm_attempted",
                        "research_agent_runtime_exact_semantic_definition_authoring_post_runtime_materializer_lineage_ok",
                        "research_agent_runtime_exact_semantic_definition_authoring_post_runtime_materialized_lean_repair_tasks",
                        "research_agent_runtime_exact_semantic_definition_authoring_post_runtime_lean_repair_lineage_ok",
                        "research_agent_runtime_exact_semantic_definition_authoring_post_runtime_local_lean_checked",
                        "research_agent_runtime_exact_semantic_definition_authoring_post_runtime_local_lean_compiled",
                        "research_agent_runtime_exact_semantic_definition_authoring_post_runtime_proofengineer_state",
                        "research_agent_runtime_exact_semantic_definition_authoring_post_runtime_proof_evidence_status",
                        "research_agent_runtime_architect_deferred_meta_capability_gaps",
                        "research_agent_runtime_architect_deferred_meta_capability_gap_owners",
                        "research_agent_runtime_architect_deferred_meta_capability_gap_requirement_ids",
                        "research_agent_runtime_architect_deferred_meta_capability_gaps_visible",
                        "research_agent_runtime_architect_deferred_meta_capability_gaps_resolved",
                        "research_agent_runtime_architect_deferred_meta_capability_gap_resolution_replay_priority_pinned",
                        "research_agent_runtime_architect_deferred_meta_capability_gap_resolution_replay_priority_pinned_evidence",
                        "research_agent_runtime_architect_deferred_meta_capability_gap_resolution_replay_priority_pinned_blocker",
                        "research_agent_runtime_pseudo_formal_block_routing_contract_complete",
                        "research_agent_runtime_pseudo_formal_block_routing_rows",
                        "research_agent_runtime_pseudo_formal_block_routing_effective_rows",
                        "research_agent_runtime_pseudo_formal_block_routing_diagnostic_rows",
                        "research_agent_runtime_pseudo_formal_block_routing_row_kinds",
                        "research_agent_runtime_pseudo_formal_block_routing_diagnostic_row_kinds",
                        "research_agent_runtime_pseudo_formal_block_routing_effective_target_lanes",
                        "research_agent_runtime_pseudo_formal_block_routing_diagnostic_target_lanes",
                        "research_agent_runtime_pseudo_formalization_required_formalization_manifests",
                        "research_agent_runtime_pseudo_formalization_required_missing_routing_rows",
                        "research_agent_runtime_pseudo_formalization_required_manifest_ids",
                        "research_agent_runtime_pseudo_formalization_required_missing_routing_manifest_ids",
                        "research_agent_runtime_pseudo_formalization_routed_manifests",
                        "research_agent_runtime_pseudo_formalization_effective_routed_manifests",
                        "research_agent_runtime_pseudo_formalization_routed_manifest_ids",
                        "research_agent_runtime_pseudo_formalization_effective_routed_manifest_ids",
                        "research_agent_runtime_pseudo_formal_block_routing_rows_missing_method_lineage",
                        "research_agent_runtime_pseudo_formal_block_routing_rows_missing_scope_parent",
                        "research_agent_runtime_pseudo_formal_block_routing_rows_invalid_scope_parent",
                        "research_agent_runtime_pseudo_formal_block_routing_rows_missing_inherited_scope",
                        "research_agent_runtime_pseudo_formal_block_routing_rows_missing_row_kind",
                        "research_agent_runtime_pseudo_formal_block_routing_rows_missing_or_wrong_nonproof_boundary",
                        "pseudo_formal_block_verifier_component_gate_capability_evidence_ok",
                        "pseudo_formal_block_verifier_component_gate_live_generator",
                        "pseudo_formal_block_verifier_component_gate_static_or_fixture_only",
                        "pseudo_formal_block_verifier_component_gate_prompt_packets",
                        "pseudo_formal_block_verifier_component_gate_valid_responses",
                        "pseudo_formal_block_verifier_component_gate_runtime_learning_rows",
                        "formalizer_pseudo_formal_packet_component_gate_capability_evidence_ok",
                        "formalizer_pseudo_formal_packet_component_gate_live_generator",
                        "formalizer_pseudo_formal_packet_component_gate_static_or_fixture_only",
                        "formalizer_pseudo_formal_packet_component_gate_pseudo_formal_packets",
                        "formalizer_pseudo_formal_packet_component_gate_work_order_rows",
                        "formalizer_pseudo_formal_packet_component_gate_routable_work_order_rows",
                        "formalizer_pseudo_formal_packet_component_gate_routable_row_kinds",
                        "formalizer_pseudo_formal_packet_component_gate_routable_target_lanes",
                        "formalizer_pseudo_formal_packet_component_gate_nonproof_boundary_preserved",
                        "formalizer_pseudo_formal_packet_component_gate_raw_model_output_written",
                        "formalizer_pseudo_formal_packet_component_gate_exact_semantic_definition_lane_present",
                        "formalizer_pseudo_formal_packet_component_gate_exact_semantic_definition_rows",
                        "formalizer_pseudo_formal_packet_component_gate_exact_semantic_definition_rows_with_source_anchors",
                        "formalizer_pseudo_formal_packet_component_gate_exact_semantic_definition_rows_with_semantic_requirements",
                        "formalizer_pseudo_formal_packet_component_gate_exact_semantic_definition_rows_with_lineage",
                        "formalizer_pseudo_formal_packet_component_gate_exact_semantic_definition_rows_source_anchored",
                        "formalizer_pseudo_formal_packet_component_gate_exact_semantic_definition_rows_semantic_requirements_present",
                        "formalizer_pseudo_formal_packet_component_gate_exact_semantic_definition_rows_lineage_complete",
                        "formalizer_pseudo_formal_packet_component_gate_proof_evidence_status_ok",
                        "formalizer_pseudo_formal_packet_component_gate_no_theorem_proof_claim",
                        "research_agent_runtime_pseudo_formal_block_verifier_component_gate_attached",
                        "research_agent_runtime_pseudo_formal_block_verifier_component_gate_capability_evidence_ok",
                        "research_agent_runtime_pseudo_formal_block_verifier_component_gate_live_generator",
                        "research_agent_runtime_pseudo_formal_block_verifier_component_gate_static_or_fixture_only",
                        "research_agent_runtime_pseudo_formal_block_verifier_component_gate_prompt_packets",
                        "research_agent_runtime_pseudo_formal_block_verifier_component_gate_valid_responses",
                        "research_agent_runtime_pseudo_formal_block_verifier_component_gate_runtime_learning_rows",
                        "research_agent_runtime_pseudo_formal_block_verifier_component_gate_source_runtime_learning_jsonl_path_count",
                        "research_agent_runtime_pseudo_formal_block_verifier_component_gate_source_runtime_learning_lineage_ok",
                        "research_agent_runtime_formalizer_pseudo_formal_packet_component_gate_attached",
                        "research_agent_runtime_formalizer_pseudo_formal_packet_component_gate_capability_evidence_ok",
                        "research_agent_runtime_formalizer_pseudo_formal_packet_component_gate_live_generator",
                        "research_agent_runtime_formalizer_pseudo_formal_packet_component_gate_static_or_fixture_only",
                        "research_agent_runtime_formalizer_pseudo_formal_packet_component_gate_pseudo_formal_packets",
                        "research_agent_runtime_formalizer_pseudo_formal_packet_component_gate_work_order_rows",
                        "research_agent_runtime_formalizer_pseudo_formal_packet_component_gate_routable_work_order_rows",
                        "research_agent_runtime_formalizer_pseudo_formal_packet_component_gate_routable_row_kinds",
                        "research_agent_runtime_formalizer_pseudo_formal_packet_component_gate_routable_target_lanes",
                        "research_agent_runtime_formalizer_pseudo_formal_packet_component_gate_nonproof_boundary_preserved",
                        "research_agent_runtime_formalizer_pseudo_formal_packet_component_gate_raw_model_output_written",
                        "research_agent_runtime_formalizer_pseudo_formal_packet_component_gate_exact_semantic_definition_lane_present",
                        "research_agent_runtime_formalizer_pseudo_formal_packet_component_gate_exact_semantic_definition_rows",
                        "research_agent_runtime_formalizer_pseudo_formal_packet_component_gate_exact_semantic_definition_rows_with_source_anchors",
                        "research_agent_runtime_formalizer_pseudo_formal_packet_component_gate_exact_semantic_definition_rows_with_semantic_requirements",
                        "research_agent_runtime_formalizer_pseudo_formal_packet_component_gate_exact_semantic_definition_rows_with_lineage",
                        "research_agent_runtime_formalizer_pseudo_formal_packet_component_gate_exact_semantic_definition_rows_source_anchored",
                        "research_agent_runtime_formalizer_pseudo_formal_packet_component_gate_exact_semantic_definition_rows_semantic_requirements_present",
                        "research_agent_runtime_formalizer_pseudo_formal_packet_component_gate_exact_semantic_definition_rows_lineage_complete",
                        "research_agent_runtime_formalizer_pseudo_formal_packet_component_gate_proof_evidence_status_ok",
                        "research_agent_runtime_formalizer_pseudo_formal_packet_component_gate_no_theorem_proof_claim",
                        "research_agent_runtime_formalizer_pseudo_formal_packet_component_gate_attachment_gate_recomputed",
                        "research_agent_runtime_formalizer_pseudo_formal_packet_component_gate_learning_consumed",
                        "research_agent_runtime_formalizer_pseudo_formal_packet_component_gate_learning_rows",
                        "research_agent_runtime_formalizer_pseudo_formal_packet_component_gate_learning_consumed_rows",
                        "research_agent_runtime_runtime_formalizer_pseudo_formal_packet_component_gate_learning_consumed",
                        "research_agent_runtime_runtime_formalizer_pseudo_formal_packet_component_gate_learning_rows",
                        "research_agent_runtime_runtime_formalizer_pseudo_formal_packet_component_gate_learning_consumed_rows",
                        "runtime_formalizer_pseudo_formal_packet_component_gate_learning_consumed",
                        "n_runtime_formalizer_pseudo_formal_packet_component_gate_learning_rows",
                        "n_runtime_formalizer_pseudo_formal_packet_component_gate_learning_consumed_rows",
                        "research_agent_runtime_internal_formalizer_pseudo_formal_packet_eval_attached",
                        "research_agent_runtime_internal_formalizer_pseudo_formal_packet_eval_capability_evidence_ok",
                        "research_agent_runtime_internal_formalizer_pseudo_formal_packet_eval_pseudo_formal_packets",
                        "research_agent_runtime_internal_formalizer_pseudo_formal_packet_eval_work_order_rows",
                        "research_agent_runtime_internal_formalizer_pseudo_formal_packet_eval_routable_work_order_rows",
                        "research_agent_runtime_internal_formalizer_pseudo_formal_packet_eval_routable_row_kinds",
                        "research_agent_runtime_internal_formalizer_pseudo_formal_packet_eval_routable_target_lanes",
                        "research_agent_runtime_internal_formalizer_pseudo_formal_packet_eval_nonproof_boundary_preserved",
                        "research_agent_runtime_internal_formalizer_pseudo_formal_packet_eval_raw_model_output_written",
                        "research_agent_runtime_internal_formalizer_pseudo_formal_packet_eval_exact_semantic_definition_lane_present",
                        "research_agent_runtime_internal_formalizer_pseudo_formal_packet_eval_exact_semantic_definition_rows",
                        "research_agent_runtime_internal_formalizer_pseudo_formal_packet_eval_exact_semantic_definition_rows_with_source_anchors",
                        "research_agent_runtime_internal_formalizer_pseudo_formal_packet_eval_exact_semantic_definition_rows_with_semantic_requirements",
                        "research_agent_runtime_internal_formalizer_pseudo_formal_packet_eval_exact_semantic_definition_rows_with_lineage",
                        "research_agent_runtime_internal_formalizer_pseudo_formal_packet_eval_exact_semantic_definition_rows_source_anchored",
                        "research_agent_runtime_internal_formalizer_pseudo_formal_packet_eval_exact_semantic_definition_rows_semantic_requirements_present",
                        "research_agent_runtime_internal_formalizer_pseudo_formal_packet_eval_exact_semantic_definition_rows_lineage_complete",
                        "research_agent_runtime_internal_formalizer_pseudo_formal_packet_eval_proof_evidence_status_ok",
                        "research_agent_runtime_internal_formalizer_pseudo_formal_packet_eval_no_theorem_proof_claim",
                        "research_agent_runtime_internal_formalizer_pseudo_formal_packet_eval_attachment_gate_recomputed",
                        "research_agent_runtime_pseudo_formal_semantic_primitive_work_orders",
                        "research_agent_runtime_pseudo_formal_semantic_primitives_reach_source_semantic_bridge",
                        "research_agent_runtime_pseudo_formal_exact_semantic_definition_work_orders",
                        "research_agent_runtime_pseudo_formal_exact_semantic_definitions_reach_exact_definition_source_lookup",
                        "research_agent_runtime_source_semantic_proofengineer_bridge_requested",
                        "research_agent_runtime_source_semantic_proofengineer_bridge_ran",
                        "research_agent_runtime_source_semantic_proofengineer_bridge_proof_evidence_status",
                        "research_agent_runtime_source_theorem_formal_environment_proof_body_executor_ran",
                        "research_agent_runtime_source_theorem_formal_environment_proof_body_executor_local_lean_requested",
                        "research_agent_runtime_source_theorem_formal_environment_proof_body_executor_n_result_rows",
                        "research_agent_runtime_source_theorem_formal_environment_proof_body_executor_n_local_lean_checked",
                        "research_agent_runtime_source_theorem_formal_environment_proof_body_executor_n_source_theorem_kernel_verified",
                        "research_agent_runtime_source_theorem_exact_proof_body_repair_executor_ran",
                        "research_agent_runtime_source_theorem_exact_proof_body_repair_executor_n_result_rows",
                        "research_agent_runtime_source_theorem_exact_proof_body_repair_executor_n_local_lean_checked",
                        "research_agent_runtime_source_theorem_exact_proof_body_repair_executor_n_proof_body_goal_reached",
                        "research_agent_runtime_source_theorem_exact_proof_body_repair_executor_n_proof_body_goal_reached_with_semantic_blockers",
                        "research_agent_runtime_source_theorem_exact_proof_body_repair_executor_n_source_theorem_kernel_verified",
                        "research_agent_runtime_source_theorem_exact_semantic_definition_typechecked_review_verifier_approved_proof_body_recheck_executor_ran",
                        "research_agent_runtime_source_theorem_exact_semantic_definition_typechecked_review_verifier_approved_proof_body_recheck_executor_n_result_rows",
                        "research_agent_runtime_source_theorem_exact_semantic_definition_typechecked_review_verifier_approved_proof_body_recheck_executor_n_source_theorem_kernel_verified",
                        "research_agent_runtime_source_theorem_proof_body_result_row_count",
                        "research_agent_runtime_source_theorem_proof_body_goal_reached_evidence_count",
                        "research_agent_runtime_source_theorem_proof_body_goal_reached_with_semantic_blockers",
                        "research_agent_runtime_source_theorem_signature_probe_reached_proof_body_scorecard_present",
                        "research_agent_runtime_source_theorem_signature_probe_reached_proof_body_scorecard_ok",
                        "research_agent_runtime_source_theorem_signature_probe_reached_proof_body_scorecard_evidence",
                        "research_agent_runtime_source_theorem_signature_probe_reached_proof_body_scorecard_blocker",
                        "research_agent_runtime_source_theorem_proof_body_semantic_review_blockers_not_hidden_scorecard_present",
                        "research_agent_runtime_source_theorem_proof_body_semantic_review_blockers_not_hidden_scorecard_ok",
                        "research_agent_runtime_source_theorem_proof_body_semantic_review_blockers_not_hidden_scorecard_evidence",
                        "research_agent_runtime_source_theorem_proof_body_semantic_review_blockers_not_hidden_scorecard_blocker",
                        "research_agent_runtime_source_theorem_proof_body_local_lean_gate_scorecard_present",
                        "research_agent_runtime_source_theorem_proof_body_local_lean_gate_scorecard_ok",
                        "research_agent_runtime_source_theorem_proof_body_local_lean_gate_scorecard_evidence",
                        "research_agent_runtime_source_theorem_proof_body_local_lean_gate_scorecard_blocker",
                        "research_agent_runtime_source_theorem_kernel_verified_count",
                        "research_agent_runtime_source_theorem_proof_body_executor_ran_scorecard_present",
                        "research_agent_runtime_source_theorem_proof_body_executor_ran_scorecard_ok",
                        "research_agent_runtime_source_theorem_proof_body_executor_ran_scorecard_evidence",
                        "research_agent_runtime_source_theorem_proof_body_executor_ran_scorecard_blocker",
                        "research_agent_runtime_source_theorem_proof_body_same_lane_verifier_evidence_present",
                        "research_agent_runtime_source_theorem_proof_body_same_lane_verifier_evidence",
                        "research_agent_runtime_source_theorem_proof_body_same_lane_verifier_scorecard_evidence",
                        "research_agent_runtime_source_theorem_proof_body_same_lane_verifier_scorecard_blocker",
                        "research_agent_runtime_live_lean_lsp_mcp_called_scorecard_present",
                        "research_agent_runtime_live_lean_lsp_mcp_called_scorecard_ok",
                        "research_agent_runtime_live_lean_lsp_mcp_called_scorecard_evidence",
                        "research_agent_runtime_live_lean_lsp_mcp_called_scorecard_blocker",
                        "research_agent_runtime_real_kernel_subclaim_verified_scorecard_present",
                        "research_agent_runtime_real_kernel_subclaim_verified_scorecard_ok",
                        "research_agent_runtime_real_kernel_subclaim_verified_scorecard_evidence",
                        "research_agent_runtime_real_kernel_subclaim_verified_scorecard_blocker",
                        "research_agent_runtime_full_frontier_theorem_kernel_proved_scorecard_present",
                        "research_agent_runtime_full_frontier_theorem_kernel_proved_scorecard_ok",
                        "research_agent_runtime_full_frontier_theorem_kernel_proved_scorecard_evidence",
                        "research_agent_runtime_full_frontier_theorem_kernel_proved_scorecard_blocker",
                        "research_agent_runtime_formal_gap_planner_handoff_rows",
                        "research_agent_runtime_formal_gap_planner_handoff_rows_missing_execution_context",
                        "research_agent_runtime_formal_gap_planner_executable_handoff_context_complete",
                        "research_agent_runtime_formal_gap_planner_live_route_planner_followthrough",
                        "research_agent_runtime_formal_gap_planner_live_route_planner_invocations",
                        "research_agent_runtime_formal_gap_planner_live_route_planner_response_contract_ok",
                        "research_agent_runtime_formal_gap_planner_live_route_planner_target_prover_replay_all_ok",
                        "research_agent_runtime_formal_gap_planner_target_prover_replay_route_revision_proposals",
                        "research_agent_runtime_formal_gap_planner_target_prover_replay_route_revision_complete_feedback_proposal_ids",
                        "research_agent_runtime_capability_gap_routing_input_rows",
                        "research_agent_runtime_capability_gap_routing_input_rows_seen",
                        "research_agent_runtime_capability_gap_routing_input_retention_policy",
                        "research_agent_runtime_capability_gap_routing_input_retention_selection_counts",
                        "research_agent_runtime_capability_gap_routing_input_requirement_ids",
                        "research_agent_runtime_capability_gap_routing_input_priority_pinned_requirement_ids",
                        "research_agent_runtime_capability_gap_routing_input_owner_subsystems",
                        "research_agent_runtime_capability_gap_routing_followup_commands",
                        "research_agent_runtime_capability_gap_routing_input_rows_missing_retention_selection",
                        "research_agent_runtime_capability_gap_routing_input_rows_missing_retention_selection_boundary",
                        "research_agent_runtime_cross_task_theorem_family_rows",
                        "research_agent_runtime_cross_task_theorem_family_rows_with_explicit_family",
                        "research_agent_runtime_cross_task_theorem_family_rows_with_target_bound_kernel",
                        "research_agent_runtime_cross_task_theorem_family_rows_with_open_formal_gaps",
                    }
                },
                "suite_rows": [asdict(row) for row in suite_rows],
                "top_actions": top_actions,
            }
        ),
    }
    if out_dir is not None:
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "evaluation_benchmark_guidance_manifest.json").write_text(
            json.dumps(payload, indent=2, default=str),
            encoding="utf-8",
        )
        (out_dir / "evaluation_benchmark_guidance.md").write_text(
            _markdown_report(payload),
            encoding="utf-8",
        )
    return payload


def _suite_rows(
    *,
    counts: Mapping[str, Any],
    artifacts: Mapping[str, Any],
    gates: Mapping[str, Any],
    suites_file: Path,
    frontier_benchmark_file: Path,
    research_questions_file: Path,
) -> tuple[BenchmarkSuiteGuidanceRow, ...]:
    frontier_questions = _int(counts.get("frontier_questions"))
    frontier_smoke_questions = _int(counts.get("frontier_smoke_questions"))
    theory_coverage = _float(counts.get("frontier_theory_expected_result_coverage_rate"))
    missing_primitives = _int(counts.get("missing_formal_primitives"))
    proof_search_candidate_delta = _int(counts.get("proof_search_retrieval_ablation_candidate_delta"))
    proof_search_hard_candidate_delta = _int(
        counts.get("proof_search_retrieval_no_registered_ablation_candidate_delta")
    )
    proof_search_hard_solved_delta = _int(
        counts.get("proof_search_retrieval_no_registered_ablation_solved_delta")
    )
    proofs_kernel_verified = _int(counts.get("proofs_kernel_verified"))
    proof_search_kernel_verified = _int(counts.get("proof_search_kernel_verified"))
    proof_search_kernel_rerun_verified = _int(
        counts.get("proof_search_kernel_rerun_local_lean_verified")
    )
    proof_kernel_evidence = (
        proofs_kernel_verified + proof_search_kernel_verified + proof_search_kernel_rerun_verified
    )
    proof_search_solved = _int(counts.get("proof_search_solved"))
    proof_search_obligations = _int(counts.get("proof_search_obligations"))
    algorithm_promotion_ready = _int(counts.get("algorithm_repair_sandbox_patch_eval_promotion_ready"))
    runtime_pf_bv_rows = _int(
        counts.get("research_agent_runtime_pseudo_formal_block_routing_rows")
    )
    runtime_pf_bv_effective_rows = _int(
        counts.get(
            "research_agent_runtime_pseudo_formal_block_routing_effective_rows"
        )
    )
    runtime_pf_bv_diagnostic_rows = _int(
        counts.get(
            "research_agent_runtime_pseudo_formal_block_routing_diagnostic_rows"
        )
    )
    runtime_pf_bv_missing_method_lineage = _int(
        counts.get(
            "research_agent_runtime_pseudo_formal_block_routing_rows_missing_method_lineage"
        )
    )
    runtime_pf_bv_missing_scope_parent = _int(
        counts.get(
            "research_agent_runtime_pseudo_formal_block_routing_rows_missing_scope_parent"
        )
    )
    runtime_pf_bv_invalid_scope_parent = _int(
        counts.get(
            "research_agent_runtime_pseudo_formal_block_routing_rows_invalid_scope_parent"
        )
    )
    runtime_pf_bv_missing_inherited_scope = _int(
        counts.get(
            "research_agent_runtime_pseudo_formal_block_routing_rows_missing_inherited_scope"
        )
    )
    runtime_pf_bv_missing_row_kind = _int(
        counts.get(
            "research_agent_runtime_pseudo_formal_block_routing_rows_missing_row_kind"
        )
    )
    runtime_pf_bv_required_manifests = _int(
        counts.get(
            "research_agent_runtime_pseudo_formalization_required_formalization_manifests"
        )
    )
    runtime_pf_bv_required_missing_routing = _int(
        counts.get(
            "research_agent_runtime_pseudo_formalization_required_missing_routing_rows"
        )
    )
    runtime_pf_bv_routed_manifests = _int(
        counts.get("research_agent_runtime_pseudo_formalization_routed_manifests")
    )
    runtime_pf_bv_effective_routed_manifests = _int(
        counts.get(
            "research_agent_runtime_pseudo_formalization_effective_routed_manifests"
        )
    )
    runtime_pf_bv_bad_nonproof_boundary = _int(
        counts.get(
            "research_agent_runtime_pseudo_formal_block_routing_rows_missing_or_wrong_nonproof_boundary"
        )
    )
    runtime_pf_bv_contract_complete = bool(
        counts.get(
            "research_agent_runtime_pseudo_formal_block_routing_contract_complete"
        )
    )
    runtime_pf_bv_row_split_keys = (
        "research_agent_runtime_pseudo_formal_block_routing_effective_rows",
        "research_agent_runtime_pseudo_formal_block_routing_diagnostic_rows",
        "research_agent_runtime_pseudo_formal_block_routing_row_kinds",
        "research_agent_runtime_pseudo_formal_block_routing_diagnostic_row_kinds",
        "research_agent_runtime_pseudo_formal_block_routing_effective_target_lanes",
        "research_agent_runtime_pseudo_formal_block_routing_diagnostic_target_lanes",
    )
    runtime_pf_bv_row_split_present = all(
        key in counts for key in runtime_pf_bv_row_split_keys
    )
    runtime_pf_bv_row_split_ok = (
        runtime_pf_bv_rows <= 0
        or (
            runtime_pf_bv_row_split_present
            and runtime_pf_bv_effective_rows + runtime_pf_bv_diagnostic_rows
            == runtime_pf_bv_rows
        )
    )
    runtime_pf_bv_manifest_keys = (
        "research_agent_runtime_pseudo_formalization_required_manifest_ids",
        "research_agent_runtime_pseudo_formalization_required_missing_routing_manifest_ids",
        "research_agent_runtime_pseudo_formalization_routed_manifests",
        "research_agent_runtime_pseudo_formalization_effective_routed_manifests",
        "research_agent_runtime_pseudo_formalization_routed_manifest_ids",
        "research_agent_runtime_pseudo_formalization_effective_routed_manifest_ids",
    )
    runtime_pf_bv_manifest_telemetry_present = all(
        key in counts for key in runtime_pf_bv_manifest_keys
    )
    runtime_pf_bv_required_manifest_ids = _string_set(
        counts.get("research_agent_runtime_pseudo_formalization_required_manifest_ids")
    )
    runtime_pf_bv_required_missing_manifest_ids = _string_set(
        counts.get(
            "research_agent_runtime_pseudo_formalization_required_missing_routing_manifest_ids"
        )
    )
    runtime_pf_bv_effective_routed_manifest_ids = _string_set(
        counts.get(
            "research_agent_runtime_pseudo_formalization_effective_routed_manifest_ids"
        )
    )
    runtime_pf_bv_routed_manifest_ids = _string_set(
        counts.get("research_agent_runtime_pseudo_formalization_routed_manifest_ids")
    )
    runtime_pf_bv_manifest_required = (
        runtime_pf_bv_required_manifests > 0
        or bool(runtime_pf_bv_required_manifest_ids)
        or runtime_pf_bv_required_missing_routing > 0
    )
    runtime_pf_bv_manifest_coverage_ok = (
        not runtime_pf_bv_manifest_required
        or (
            runtime_pf_bv_manifest_telemetry_present
            and len(runtime_pf_bv_required_manifest_ids)
            == runtime_pf_bv_required_manifests
            and not runtime_pf_bv_required_missing_manifest_ids
            and runtime_pf_bv_routed_manifests
            == len(runtime_pf_bv_routed_manifest_ids)
            and runtime_pf_bv_effective_routed_manifests
            == len(runtime_pf_bv_effective_routed_manifest_ids)
            and runtime_pf_bv_required_manifest_ids.issubset(
                runtime_pf_bv_effective_routed_manifest_ids
            )
            and runtime_pf_bv_effective_routed_manifest_ids.issubset(
                runtime_pf_bv_routed_manifest_ids
            )
        )
    )
    runtime_pf_bv_telemetry_present = any(
        key in counts
        for key in (
            "research_agent_runtime_pseudo_formal_block_routing_contract_complete",
            "research_agent_runtime_pseudo_formal_block_routing_rows",
            *runtime_pf_bv_row_split_keys,
            "research_agent_runtime_pseudo_formalization_required_formalization_manifests",
            "research_agent_runtime_pseudo_formalization_required_missing_routing_rows",
            *runtime_pf_bv_manifest_keys,
            "research_agent_runtime_pseudo_formal_block_routing_rows_missing_method_lineage",
            "research_agent_runtime_pseudo_formal_block_routing_rows_missing_scope_parent",
            "research_agent_runtime_pseudo_formal_block_routing_rows_invalid_scope_parent",
            "research_agent_runtime_pseudo_formal_block_routing_rows_missing_inherited_scope",
            "research_agent_runtime_pseudo_formal_block_routing_rows_missing_row_kind",
            "research_agent_runtime_pseudo_formal_block_routing_rows_missing_or_wrong_nonproof_boundary",
        )
    )
    runtime_pf_bv_contract_ok = (
        not runtime_pf_bv_telemetry_present
        or (
            runtime_pf_bv_rows == 0
            and runtime_pf_bv_required_missing_routing == 0
        )
        or (
            runtime_pf_bv_contract_complete
            and runtime_pf_bv_required_missing_routing == 0
            and runtime_pf_bv_missing_method_lineage == 0
            and runtime_pf_bv_missing_scope_parent == 0
            and runtime_pf_bv_invalid_scope_parent == 0
            and runtime_pf_bv_missing_inherited_scope == 0
            and runtime_pf_bv_missing_row_kind == 0
            and runtime_pf_bv_bad_nonproof_boundary == 0
            and runtime_pf_bv_row_split_ok
            and runtime_pf_bv_manifest_coverage_ok
        )
    )
    standalone_pf_bv_component_exercised = bool(
        artifacts.get("pseudo_formal_block_verifier_component_gate")
    )
    runtime_pf_bv_component_exercised = bool(
        counts.get(
            "research_agent_runtime_pseudo_formal_block_verifier_component_gate_attached"
        )
    )
    pf_bv_component_prompt_packets = max(
        _int(counts.get("pseudo_formal_block_verifier_component_gate_prompt_packets")),
        _int(
            counts.get(
                "research_agent_runtime_pseudo_formal_block_verifier_component_gate_prompt_packets"
            )
        ),
    )
    pf_bv_component_valid_responses = max(
        _int(counts.get("pseudo_formal_block_verifier_component_gate_valid_responses")),
        _int(
            counts.get(
                "research_agent_runtime_pseudo_formal_block_verifier_component_gate_valid_responses"
            )
        ),
    )
    pf_bv_component_runtime_learning_rows = max(
        _int(
            counts.get(
                "pseudo_formal_block_verifier_component_gate_runtime_learning_rows"
            )
        ),
        _int(
            counts.get(
                "research_agent_runtime_pseudo_formal_block_verifier_component_gate_runtime_learning_rows"
            )
        ),
    )
    pf_bv_component_accepted_blocks = max(
        _int(counts.get("pseudo_formal_block_verifier_component_gate_accepted_blocks")),
        _int(
            counts.get(
                "research_agent_runtime_pseudo_formal_block_verifier_component_gate_accepted_blocks"
            )
        ),
    )
    pf_bv_component_failed_blocks = max(
        _int(counts.get("pseudo_formal_block_verifier_component_gate_failed_blocks")),
        _int(
            counts.get(
                "research_agent_runtime_pseudo_formal_block_verifier_component_gate_failed_blocks"
            )
        ),
    )
    pf_bv_component_capability_evidence_ok = bool(
        counts.get("pseudo_formal_block_verifier_component_gate_capability_evidence_ok")
    ) or bool(
        counts.get(
            "research_agent_runtime_pseudo_formal_block_verifier_component_gate_capability_evidence_ok"
        )
    )
    pf_bv_component_ok = bool(
        pf_bv_component_capability_evidence_ok
        and pf_bv_component_prompt_packets > 0
        and pf_bv_component_valid_responses > 0
        and pf_bv_component_runtime_learning_rows > 0
    )
    standalone_formalizer_pf_packet_component_exercised = bool(
        artifacts.get("formalizer_pseudo_formal_packet_eval")
    )
    runtime_formalizer_pf_packet_component_exercised = bool(
        counts.get(
            "research_agent_runtime_formalizer_pseudo_formal_packet_component_gate_attached"
        )
        or counts.get(
            "research_agent_runtime_internal_formalizer_pseudo_formal_packet_eval_attached"
        )
    )
    runtime_formalizer_pf_packet_component_capability_evidence_ok = bool(
        counts.get(
            "research_agent_runtime_formalizer_pseudo_formal_packet_component_gate_capability_evidence_ok"
        )
        or counts.get(
            "research_agent_runtime_internal_formalizer_pseudo_formal_packet_eval_capability_evidence_ok"
        )
    )
    runtime_formalizer_pf_packet_component_packets = max(
        _int(
            counts.get(
                "research_agent_runtime_formalizer_pseudo_formal_packet_component_gate_pseudo_formal_packets"
            )
        ),
        _int(
            counts.get(
                "research_agent_runtime_internal_formalizer_pseudo_formal_packet_eval_pseudo_formal_packets"
            )
        ),
    )
    runtime_formalizer_pf_packet_component_routable_rows = max(
        _int(
            counts.get(
                "research_agent_runtime_formalizer_pseudo_formal_packet_component_gate_routable_work_order_rows"
            )
        ),
        _int(
            counts.get(
                "research_agent_runtime_internal_formalizer_pseudo_formal_packet_eval_routable_work_order_rows"
            )
        ),
    )
    runtime_formalizer_pf_packet_component_target_lanes = (
        _string_set(
            counts.get(
                "research_agent_runtime_formalizer_pseudo_formal_packet_component_gate_routable_target_lanes"
            )
        )
        | _string_set(
            counts.get(
                "research_agent_runtime_internal_formalizer_pseudo_formal_packet_eval_routable_target_lanes"
            )
        )
    )
    runtime_formalizer_pf_packet_component_exact_lane_present = bool(
        counts.get(
            "research_agent_runtime_formalizer_pseudo_formal_packet_component_gate_exact_semantic_definition_lane_present"
        )
        or counts.get(
            "research_agent_runtime_internal_formalizer_pseudo_formal_packet_eval_exact_semantic_definition_lane_present"
        )
    )
    runtime_formalizer_pf_packet_component_exact_rows = max(
        _int(
            counts.get(
                "research_agent_runtime_formalizer_pseudo_formal_packet_component_gate_exact_semantic_definition_rows"
            )
        ),
        _int(
            counts.get(
                "research_agent_runtime_internal_formalizer_pseudo_formal_packet_eval_exact_semantic_definition_rows"
            )
        ),
    )
    runtime_formalizer_pf_packet_component_exact_rows_source_anchored = bool(
        counts.get(
            "research_agent_runtime_formalizer_pseudo_formal_packet_component_gate_exact_semantic_definition_rows_source_anchored"
        )
        or counts.get(
            "research_agent_runtime_internal_formalizer_pseudo_formal_packet_eval_exact_semantic_definition_rows_source_anchored"
        )
    )
    runtime_formalizer_pf_packet_component_exact_rows_semantic_requirements_present = bool(
        counts.get(
            "research_agent_runtime_formalizer_pseudo_formal_packet_component_gate_exact_semantic_definition_rows_semantic_requirements_present"
        )
        or counts.get(
            "research_agent_runtime_internal_formalizer_pseudo_formal_packet_eval_exact_semantic_definition_rows_semantic_requirements_present"
        )
    )
    runtime_formalizer_pf_packet_component_exact_rows_lineage_complete = bool(
        counts.get(
            "research_agent_runtime_formalizer_pseudo_formal_packet_component_gate_exact_semantic_definition_rows_lineage_complete"
        )
        or counts.get(
            "research_agent_runtime_internal_formalizer_pseudo_formal_packet_eval_exact_semantic_definition_rows_lineage_complete"
        )
    )
    runtime_formalizer_pf_packet_component_nonproof_boundary = bool(
        counts.get(
            "research_agent_runtime_formalizer_pseudo_formal_packet_component_gate_nonproof_boundary_preserved"
        )
        or counts.get(
            "research_agent_runtime_internal_formalizer_pseudo_formal_packet_eval_nonproof_boundary_preserved"
        )
    )
    runtime_formalizer_pf_packet_component_raw_output_written = bool(
        counts.get(
            "research_agent_runtime_formalizer_pseudo_formal_packet_component_gate_raw_model_output_written"
        )
        or counts.get(
            "research_agent_runtime_internal_formalizer_pseudo_formal_packet_eval_raw_model_output_written"
        )
    )
    runtime_formalizer_pf_packet_component_proof_evidence_status_ok = bool(
        counts.get(
            "research_agent_runtime_formalizer_pseudo_formal_packet_component_gate_proof_evidence_status_ok"
        )
        or counts.get(
            "research_agent_runtime_internal_formalizer_pseudo_formal_packet_eval_proof_evidence_status_ok"
        )
    )
    runtime_formalizer_pf_packet_component_no_theorem_proof_claim = bool(
        counts.get(
            "research_agent_runtime_formalizer_pseudo_formal_packet_component_gate_no_theorem_proof_claim"
        )
        or counts.get(
            "research_agent_runtime_internal_formalizer_pseudo_formal_packet_eval_no_theorem_proof_claim"
        )
    )
    runtime_formalizer_pf_packet_component_attachment_gate_recomputed = bool(
        counts.get(
            "research_agent_runtime_formalizer_pseudo_formal_packet_component_gate_attachment_gate_recomputed"
        )
        or counts.get(
            "research_agent_runtime_internal_formalizer_pseudo_formal_packet_eval_attachment_gate_recomputed"
        )
    )
    runtime_formalizer_pf_packet_component_learning_consumed = bool(
        counts.get(
            "research_agent_runtime_formalizer_pseudo_formal_packet_component_gate_learning_consumed"
        )
        or counts.get(
            "research_agent_runtime_runtime_formalizer_pseudo_formal_packet_component_gate_learning_consumed"
        )
        or counts.get(
            "runtime_formalizer_pseudo_formal_packet_component_gate_learning_consumed"
        )
    )
    runtime_formalizer_pf_packet_component_learning_rows = max(
        _int(
            counts.get(
                "research_agent_runtime_formalizer_pseudo_formal_packet_component_gate_learning_rows"
            )
        ),
        _int(
            counts.get(
                "research_agent_runtime_runtime_formalizer_pseudo_formal_packet_component_gate_learning_rows"
            )
        ),
        _int(
            counts.get(
                "n_runtime_formalizer_pseudo_formal_packet_component_gate_learning_rows"
            )
        ),
    )
    runtime_formalizer_pf_packet_component_learning_consumed_rows = max(
        _int(
            counts.get(
                "research_agent_runtime_formalizer_pseudo_formal_packet_component_gate_learning_consumed_rows"
            )
        ),
        _int(
            counts.get(
                "research_agent_runtime_runtime_formalizer_pseudo_formal_packet_component_gate_learning_consumed_rows"
            )
        ),
        _int(
            counts.get(
                "n_runtime_formalizer_pseudo_formal_packet_component_gate_learning_consumed_rows"
            )
        ),
    )
    runtime_formalizer_pf_packet_component_ok = bool(
        runtime_formalizer_pf_packet_component_exercised
        and runtime_formalizer_pf_packet_component_capability_evidence_ok
        and runtime_formalizer_pf_packet_component_packets > 0
        and runtime_formalizer_pf_packet_component_routable_rows > 0
        and runtime_formalizer_pf_packet_component_exact_lane_present
        and runtime_formalizer_pf_packet_component_exact_rows > 0
        and runtime_formalizer_pf_packet_component_exact_rows_source_anchored
        and runtime_formalizer_pf_packet_component_exact_rows_semantic_requirements_present
        and runtime_formalizer_pf_packet_component_exact_rows_lineage_complete
        and runtime_formalizer_pf_packet_component_nonproof_boundary
        and not runtime_formalizer_pf_packet_component_raw_output_written
        and runtime_formalizer_pf_packet_component_proof_evidence_status_ok
        and runtime_formalizer_pf_packet_component_no_theorem_proof_claim
        and runtime_formalizer_pf_packet_component_attachment_gate_recomputed
        and runtime_formalizer_pf_packet_component_learning_consumed
        and runtime_formalizer_pf_packet_component_learning_rows > 0
        and runtime_formalizer_pf_packet_component_learning_consumed_rows > 0
        and "source_theorem_exact_semantic_definition"
        in runtime_formalizer_pf_packet_component_target_lanes
    )
    standalone_formalizer_pf_packet_component_capability_evidence_ok = bool(
        counts.get(
            "formalizer_pseudo_formal_packet_component_gate_capability_evidence_ok"
        )
    )
    standalone_formalizer_pf_packet_component_packets = _int(
        counts.get(
            "formalizer_pseudo_formal_packet_component_gate_pseudo_formal_packets"
        )
    )
    standalone_formalizer_pf_packet_component_routable_rows = _int(
        counts.get(
            "formalizer_pseudo_formal_packet_component_gate_routable_work_order_rows"
        )
    )
    standalone_formalizer_pf_packet_component_target_lanes = _string_set(
        counts.get(
            "formalizer_pseudo_formal_packet_component_gate_routable_target_lanes"
        )
    )
    standalone_formalizer_pf_packet_component_exact_lane_present = bool(
        counts.get(
            "formalizer_pseudo_formal_packet_component_gate_exact_semantic_definition_lane_present"
        )
        or "source_theorem_exact_semantic_definition"
        in standalone_formalizer_pf_packet_component_target_lanes
    )
    standalone_formalizer_pf_packet_component_exact_rows = _int(
        counts.get(
            "formalizer_pseudo_formal_packet_component_gate_exact_semantic_definition_rows"
        )
    )
    standalone_formalizer_pf_packet_component_exact_rows_source_anchored = bool(
        counts.get(
            "formalizer_pseudo_formal_packet_component_gate_exact_semantic_definition_rows_source_anchored"
        )
    )
    standalone_formalizer_pf_packet_component_exact_rows_semantic_requirements_present = bool(
        counts.get(
            "formalizer_pseudo_formal_packet_component_gate_exact_semantic_definition_rows_semantic_requirements_present"
        )
    )
    standalone_formalizer_pf_packet_component_exact_rows_lineage_complete = bool(
        counts.get(
            "formalizer_pseudo_formal_packet_component_gate_exact_semantic_definition_rows_lineage_complete"
        )
    )
    standalone_formalizer_pf_packet_component_nonproof_boundary = bool(
        counts.get(
            "formalizer_pseudo_formal_packet_component_gate_nonproof_boundary_preserved"
        )
    )
    standalone_formalizer_pf_packet_component_raw_output_written = bool(
        counts.get(
            "formalizer_pseudo_formal_packet_component_gate_raw_model_output_written"
        )
    )
    standalone_formalizer_pf_packet_component_proof_evidence_status_ok = bool(
        counts.get(
            "formalizer_pseudo_formal_packet_component_gate_proof_evidence_status_ok"
        )
    )
    standalone_formalizer_pf_packet_component_no_theorem_proof_claim = bool(
        counts.get(
            "formalizer_pseudo_formal_packet_component_gate_no_theorem_proof_claim"
        )
    )
    standalone_formalizer_pf_packet_component_ok = bool(
        standalone_formalizer_pf_packet_component_exercised
        and standalone_formalizer_pf_packet_component_capability_evidence_ok
        and standalone_formalizer_pf_packet_component_packets > 0
        and standalone_formalizer_pf_packet_component_routable_rows > 0
        and standalone_formalizer_pf_packet_component_exact_lane_present
        and standalone_formalizer_pf_packet_component_exact_rows > 0
        and standalone_formalizer_pf_packet_component_exact_rows_source_anchored
        and standalone_formalizer_pf_packet_component_exact_rows_semantic_requirements_present
        and standalone_formalizer_pf_packet_component_exact_rows_lineage_complete
        and standalone_formalizer_pf_packet_component_nonproof_boundary
        and not standalone_formalizer_pf_packet_component_raw_output_written
        and standalone_formalizer_pf_packet_component_proof_evidence_status_ok
        and standalone_formalizer_pf_packet_component_no_theorem_proof_claim
        and "source_theorem_exact_semantic_definition"
        in standalone_formalizer_pf_packet_component_target_lanes
    )
    formalizer_pf_packet_packets = max(
        _int(
            counts.get(
                "formalizer_pseudo_formal_packet_component_gate_pseudo_formal_packets"
            )
        ),
        _int(
            counts.get(
                "research_agent_runtime_formalizer_pseudo_formal_packet_component_gate_pseudo_formal_packets"
            )
        ),
        _int(
            counts.get(
                "research_agent_runtime_internal_formalizer_pseudo_formal_packet_eval_pseudo_formal_packets"
            )
        ),
    )
    formalizer_pf_packet_routable_rows = max(
        _int(
            counts.get(
                "formalizer_pseudo_formal_packet_component_gate_routable_work_order_rows"
            )
        ),
        _int(
            counts.get(
                "research_agent_runtime_formalizer_pseudo_formal_packet_component_gate_routable_work_order_rows"
            )
        ),
        _int(
            counts.get(
                "research_agent_runtime_internal_formalizer_pseudo_formal_packet_eval_routable_work_order_rows"
            )
        ),
    )
    formalizer_pf_packet_target_lanes = (
        _string_set(
            counts.get(
                "formalizer_pseudo_formal_packet_component_gate_routable_target_lanes"
            )
        )
        | runtime_formalizer_pf_packet_component_target_lanes
    )
    formalizer_pf_packet_exact_lane_present = bool(
        counts.get(
            "formalizer_pseudo_formal_packet_component_gate_exact_semantic_definition_lane_present"
        )
        or runtime_formalizer_pf_packet_component_exact_lane_present
        or "source_theorem_exact_semantic_definition"
        in formalizer_pf_packet_target_lanes
    )
    formalizer_pf_packet_exact_rows = max(
        standalone_formalizer_pf_packet_component_exact_rows,
        runtime_formalizer_pf_packet_component_exact_rows,
    )
    formalizer_pf_packet_exact_rows_source_anchored = bool(
        standalone_formalizer_pf_packet_component_exact_rows_source_anchored
        or runtime_formalizer_pf_packet_component_exact_rows_source_anchored
    )
    formalizer_pf_packet_exact_rows_semantic_requirements_present = bool(
        standalone_formalizer_pf_packet_component_exact_rows_semantic_requirements_present
        or runtime_formalizer_pf_packet_component_exact_rows_semantic_requirements_present
    )
    formalizer_pf_packet_exact_rows_lineage_complete = bool(
        standalone_formalizer_pf_packet_component_exact_rows_lineage_complete
        or runtime_formalizer_pf_packet_component_exact_rows_lineage_complete
    )
    formalizer_pf_packet_nonproof_boundary = bool(
        counts.get(
            "formalizer_pseudo_formal_packet_component_gate_nonproof_boundary_preserved"
        )
        or counts.get(
            "research_agent_runtime_formalizer_pseudo_formal_packet_component_gate_nonproof_boundary_preserved"
        )
        or counts.get(
            "research_agent_runtime_internal_formalizer_pseudo_formal_packet_eval_nonproof_boundary_preserved"
        )
    )
    formalizer_pf_packet_capability_evidence_ok = bool(
        counts.get(
            "formalizer_pseudo_formal_packet_component_gate_capability_evidence_ok"
        )
        or counts.get(
            "research_agent_runtime_formalizer_pseudo_formal_packet_component_gate_capability_evidence_ok"
        )
        or counts.get(
            "research_agent_runtime_internal_formalizer_pseudo_formal_packet_eval_capability_evidence_ok"
        )
    )
    formalizer_pf_packet_raw_output_written = bool(
        counts.get(
            "formalizer_pseudo_formal_packet_component_gate_raw_model_output_written"
        )
        or runtime_formalizer_pf_packet_component_raw_output_written
    )
    formalizer_pf_packet_proof_evidence_status_ok = bool(
        counts.get(
            "formalizer_pseudo_formal_packet_component_gate_proof_evidence_status_ok"
        )
        or runtime_formalizer_pf_packet_component_proof_evidence_status_ok
    )
    formalizer_pf_packet_no_theorem_proof_claim = bool(
        counts.get(
            "formalizer_pseudo_formal_packet_component_gate_no_theorem_proof_claim"
        )
        or runtime_formalizer_pf_packet_component_no_theorem_proof_claim
    )
    formalizer_pf_packet_component_ok = bool(
        standalone_formalizer_pf_packet_component_ok
        or runtime_formalizer_pf_packet_component_ok
    )
    pf_bv_component_issues = tuple(
        issue
        for issue in (
            "no live Claude/OpenAI PF/BV BlockVerifier prompt-response-validation evidence is present"
            if not pf_bv_component_capability_evidence_ok
            else "",
            "PF/BV BlockVerifier gate has no prompt packets"
            if pf_bv_component_prompt_packets <= 0
            else "",
            "PF/BV BlockVerifier gate has no valid responses"
            if pf_bv_component_valid_responses <= 0
            else "",
            "PF/BV BlockVerifier gate has no validated runtime learning rows"
            if pf_bv_component_runtime_learning_rows <= 0
            else "",
        )
        if issue
    )
    runtime_pf_semantic_work_orders = _int(
        counts.get(
            "research_agent_runtime_pseudo_formal_semantic_primitive_work_orders"
        )
    )
    runtime_pf_semantic_bridge_consumed = bool(
        counts.get(
            "research_agent_runtime_pseudo_formal_semantic_primitives_reach_source_semantic_bridge",
            True,
        )
    )
    runtime_pf_semantic_bridge_ok = (
        runtime_pf_semantic_work_orders <= 0 or runtime_pf_semantic_bridge_consumed
    )
    runtime_pf_exact_semantic_work_orders = _int(
        counts.get(
            "research_agent_runtime_pseudo_formal_exact_semantic_definition_work_orders"
        )
    )
    runtime_pf_exact_semantic_source_lookup_consumed = bool(
        counts.get(
            "research_agent_runtime_pseudo_formal_exact_semantic_definitions_reach_exact_definition_source_lookup",
            True,
        )
    )
    runtime_pf_exact_semantic_source_lookup_ok = (
        runtime_pf_exact_semantic_work_orders <= 0
        or runtime_pf_exact_semantic_source_lookup_consumed
    )
    runtime_source_theorem_formal_environment_proof_body_executor_ran = bool(
        counts.get(
            "research_agent_runtime_source_theorem_formal_environment_proof_body_executor_ran"
        )
    )
    runtime_source_theorem_formal_environment_proof_body_local_lean_requested = bool(
        counts.get(
            "research_agent_runtime_source_theorem_formal_environment_proof_body_executor_local_lean_requested"
        )
    )
    runtime_source_theorem_formal_environment_proof_body_result_rows = _int(
        counts.get(
            "research_agent_runtime_source_theorem_formal_environment_proof_body_executor_n_result_rows"
        )
    )
    runtime_source_theorem_formal_environment_proof_body_local_lean_checked = _int(
        counts.get(
            "research_agent_runtime_source_theorem_formal_environment_proof_body_executor_n_local_lean_checked"
        )
    )
    runtime_source_theorem_formal_environment_proof_body_kernel_verified = _int(
        counts.get(
            "research_agent_runtime_source_theorem_formal_environment_proof_body_executor_n_source_theorem_kernel_verified"
        )
    )
    runtime_source_theorem_exact_proof_body_repair_executor_ran = bool(
        counts.get(
            "research_agent_runtime_source_theorem_exact_proof_body_repair_executor_ran"
        )
    )
    runtime_source_theorem_exact_proof_body_repair_result_rows = _int(
        counts.get(
            "research_agent_runtime_source_theorem_exact_proof_body_repair_executor_n_result_rows"
        )
    )
    runtime_source_theorem_exact_proof_body_repair_local_lean_checked = _int(
        counts.get(
            "research_agent_runtime_source_theorem_exact_proof_body_repair_executor_n_local_lean_checked"
        )
    )
    runtime_source_theorem_exact_proof_body_repair_goal_reached = _int(
        counts.get(
            "research_agent_runtime_source_theorem_exact_proof_body_repair_executor_n_proof_body_goal_reached"
        )
    )
    runtime_source_theorem_exact_proof_body_repair_goal_reached_with_semantic_blockers = _int(
        counts.get(
            "research_agent_runtime_source_theorem_exact_proof_body_repair_executor_n_proof_body_goal_reached_with_semantic_blockers"
        )
    )
    runtime_source_theorem_exact_proof_body_repair_kernel_verified = _int(
        counts.get(
            "research_agent_runtime_source_theorem_exact_proof_body_repair_executor_n_source_theorem_kernel_verified"
        )
    )
    runtime_source_theorem_approved_proof_body_recheck_executor_ran = bool(
        counts.get(
            "research_agent_runtime_source_theorem_exact_semantic_definition_typechecked_review_verifier_approved_proof_body_recheck_executor_ran"
        )
    )
    runtime_source_theorem_approved_proof_body_recheck_result_rows = _int(
        counts.get(
            "research_agent_runtime_source_theorem_exact_semantic_definition_typechecked_review_verifier_approved_proof_body_recheck_executor_n_result_rows"
        )
    )
    runtime_source_theorem_approved_proof_body_recheck_kernel_verified = _int(
        counts.get(
            "research_agent_runtime_source_theorem_exact_semantic_definition_typechecked_review_verifier_approved_proof_body_recheck_executor_n_source_theorem_kernel_verified"
        )
    )
    runtime_source_theorem_proof_body_result_rows = max(
        runtime_source_theorem_formal_environment_proof_body_result_rows,
        runtime_source_theorem_exact_proof_body_repair_result_rows,
        runtime_source_theorem_approved_proof_body_recheck_result_rows,
        _int(counts.get("research_agent_runtime_source_theorem_proof_body_result_row_count")),
    )
    runtime_source_theorem_proof_body_local_lean_checked = max(
        runtime_source_theorem_formal_environment_proof_body_local_lean_checked,
        runtime_source_theorem_exact_proof_body_repair_local_lean_checked,
    )
    runtime_source_theorem_proof_body_goal_reached = max(
        runtime_source_theorem_exact_proof_body_repair_goal_reached,
        _int(
            counts.get(
                "research_agent_runtime_source_theorem_proof_body_goal_reached_evidence_count"
            )
        ),
    )
    runtime_source_theorem_proof_body_goal_reached_with_semantic_blockers = max(
        runtime_source_theorem_exact_proof_body_repair_goal_reached_with_semantic_blockers,
        _int(
            counts.get(
                "research_agent_runtime_source_theorem_proof_body_goal_reached_with_semantic_blockers"
            )
        ),
    )
    runtime_source_theorem_signature_probe_scorecard_present = bool(
        counts.get(
            "research_agent_runtime_source_theorem_signature_probe_reached_proof_body_scorecard_present",
            "research_agent_runtime_source_theorem_signature_probe_reached_proof_body_scorecard_ok"
            in counts,
        )
    )
    runtime_source_theorem_signature_probe_scorecard_ok = bool(
        counts.get(
            "research_agent_runtime_source_theorem_signature_probe_reached_proof_body_scorecard_ok",
            False,
        )
    )
    runtime_source_theorem_signature_probe_scorecard_evidence = str(
        counts.get(
            "research_agent_runtime_source_theorem_signature_probe_reached_proof_body_scorecard_evidence",
            "",
        )
        or ""
    )
    runtime_source_theorem_signature_probe_scorecard_blocker = str(
        counts.get(
            "research_agent_runtime_source_theorem_signature_probe_reached_proof_body_scorecard_blocker",
            "",
        )
        or ""
    )
    runtime_source_theorem_proof_body_authoritative_goal_reached = (
        runtime_source_theorem_signature_probe_scorecard_ok
        if runtime_source_theorem_signature_probe_scorecard_present
        else runtime_source_theorem_proof_body_goal_reached > 0
    )
    runtime_source_theorem_semantic_blockers_scorecard_present = bool(
        counts.get(
            "research_agent_runtime_source_theorem_proof_body_semantic_review_blockers_not_hidden_scorecard_present",
            "research_agent_runtime_source_theorem_proof_body_semantic_review_blockers_not_hidden_scorecard_ok"
            in counts,
        )
    )
    runtime_source_theorem_semantic_blockers_scorecard_ok = bool(
        counts.get(
            "research_agent_runtime_source_theorem_proof_body_semantic_review_blockers_not_hidden_scorecard_ok",
            False,
        )
    )
    runtime_source_theorem_semantic_blockers_scorecard_evidence = str(
        counts.get(
            "research_agent_runtime_source_theorem_proof_body_semantic_review_blockers_not_hidden_scorecard_evidence",
            "",
        )
        or ""
    )
    runtime_source_theorem_semantic_blockers_scorecard_blocker = str(
        counts.get(
            "research_agent_runtime_source_theorem_proof_body_semantic_review_blockers_not_hidden_scorecard_blocker",
            "",
        )
        or ""
    )
    runtime_source_theorem_semantic_blockers_authoritative_ok = (
        runtime_source_theorem_semantic_blockers_scorecard_ok
        if runtime_source_theorem_semantic_blockers_scorecard_present
        else runtime_source_theorem_proof_body_goal_reached_with_semantic_blockers <= 0
    )
    runtime_source_theorem_kernel_verified = max(
        runtime_source_theorem_formal_environment_proof_body_kernel_verified,
        runtime_source_theorem_exact_proof_body_repair_kernel_verified,
        runtime_source_theorem_approved_proof_body_recheck_kernel_verified,
        _int(counts.get("research_agent_runtime_source_theorem_kernel_verified_count")),
    )
    runtime_source_theorem_proof_body_executor_ran = bool(
        runtime_source_theorem_formal_environment_proof_body_executor_ran
        or runtime_source_theorem_exact_proof_body_repair_executor_ran
        or runtime_source_theorem_approved_proof_body_recheck_executor_ran
        or runtime_source_theorem_proof_body_result_rows > 0
    )
    runtime_source_theorem_proof_body_executor_scorecard_present = bool(
        counts.get(
            "research_agent_runtime_source_theorem_proof_body_executor_ran_scorecard_present",
            "research_agent_runtime_source_theorem_proof_body_executor_ran_scorecard_ok"
            in counts,
        )
    )
    runtime_source_theorem_proof_body_executor_scorecard_ok = bool(
        counts.get(
            "research_agent_runtime_source_theorem_proof_body_executor_ran_scorecard_ok",
            False,
        )
    )
    runtime_source_theorem_proof_body_executor_scorecard_evidence = str(
        counts.get(
            "research_agent_runtime_source_theorem_proof_body_executor_ran_scorecard_evidence",
            "",
        )
        or ""
    )
    runtime_source_theorem_proof_body_executor_scorecard_blocker = str(
        counts.get(
            "research_agent_runtime_source_theorem_proof_body_executor_ran_scorecard_blocker",
            "",
        )
        or ""
    )
    runtime_source_theorem_proof_body_authoritative_executor_ran = (
        runtime_source_theorem_proof_body_executor_scorecard_ok
        if runtime_source_theorem_proof_body_executor_scorecard_present
        else runtime_source_theorem_proof_body_executor_ran
    )
    runtime_source_theorem_formal_environment_proof_body_lane_ok = (
        runtime_source_theorem_formal_environment_proof_body_result_rows > 0
        and (
            runtime_source_theorem_formal_environment_proof_body_local_lean_checked > 0
            or runtime_source_theorem_formal_environment_proof_body_kernel_verified > 0
        )
    )
    runtime_source_theorem_exact_proof_body_repair_lane_ok = (
        runtime_source_theorem_exact_proof_body_repair_result_rows > 0
        and (
            runtime_source_theorem_exact_proof_body_repair_local_lean_checked > 0
            or runtime_source_theorem_exact_proof_body_repair_kernel_verified > 0
        )
    )
    runtime_source_theorem_approved_proof_body_recheck_lane_ok = (
        runtime_source_theorem_approved_proof_body_recheck_result_rows > 0
        and runtime_source_theorem_approved_proof_body_recheck_kernel_verified > 0
    )
    runtime_source_theorem_proof_body_same_lane_gate_ok = bool(
        runtime_source_theorem_formal_environment_proof_body_lane_ok
        or runtime_source_theorem_exact_proof_body_repair_lane_ok
        or runtime_source_theorem_approved_proof_body_recheck_lane_ok
    )
    runtime_source_theorem_proof_body_same_lane_scorecard_present = bool(
        counts.get(
            "research_agent_runtime_source_theorem_proof_body_same_lane_verifier_evidence_present",
            "research_agent_runtime_source_theorem_proof_body_same_lane_verifier_evidence"
            in counts,
        )
    )
    runtime_source_theorem_proof_body_same_lane_scorecard_ok = bool(
        counts.get(
            "research_agent_runtime_source_theorem_proof_body_same_lane_verifier_evidence",
            False,
        )
    )
    runtime_source_theorem_proof_body_same_lane_scorecard_evidence = str(
        counts.get(
            "research_agent_runtime_source_theorem_proof_body_same_lane_verifier_scorecard_evidence",
            "",
        )
        or ""
    )
    runtime_source_theorem_proof_body_same_lane_scorecard_blocker = str(
        counts.get(
            "research_agent_runtime_source_theorem_proof_body_same_lane_verifier_scorecard_blocker",
            "",
        )
        or ""
    )
    runtime_source_theorem_proof_body_authoritative_same_lane_gate_ok = (
        runtime_source_theorem_proof_body_same_lane_scorecard_ok
        if runtime_source_theorem_proof_body_same_lane_scorecard_present
        else runtime_source_theorem_proof_body_same_lane_gate_ok
    )
    runtime_source_theorem_proof_body_aggregate_local_lean_gate_ok = (
        runtime_source_theorem_proof_body_result_rows > 0
        and (
            runtime_source_theorem_proof_body_local_lean_checked > 0
            or runtime_source_theorem_kernel_verified > 0
        )
    )
    runtime_source_theorem_proof_body_local_lean_gate_ok = (
        runtime_source_theorem_proof_body_same_lane_scorecard_ok
        if runtime_source_theorem_proof_body_same_lane_scorecard_present
        else (
            runtime_source_theorem_proof_body_aggregate_local_lean_gate_ok
            and runtime_source_theorem_proof_body_same_lane_gate_ok
        )
    )
    runtime_source_theorem_local_lean_gate_scorecard_present = bool(
        counts.get(
            "research_agent_runtime_source_theorem_proof_body_local_lean_gate_scorecard_present",
            "research_agent_runtime_source_theorem_proof_body_local_lean_gate_scorecard_ok"
            in counts,
        )
    )
    runtime_source_theorem_local_lean_gate_scorecard_ok = bool(
        counts.get(
            "research_agent_runtime_source_theorem_proof_body_local_lean_gate_scorecard_ok",
            False,
        )
    )
    runtime_source_theorem_local_lean_gate_scorecard_evidence = str(
        counts.get(
            "research_agent_runtime_source_theorem_proof_body_local_lean_gate_scorecard_evidence",
            "",
        )
        or ""
    )
    runtime_source_theorem_local_lean_gate_scorecard_blocker = str(
        counts.get(
            "research_agent_runtime_source_theorem_proof_body_local_lean_gate_scorecard_blocker",
            "",
        )
        or ""
    )
    runtime_source_theorem_proof_body_authoritative_local_lean_gate_ok = (
        runtime_source_theorem_local_lean_gate_scorecard_ok
        if runtime_source_theorem_local_lean_gate_scorecard_present
        else runtime_source_theorem_proof_body_local_lean_gate_ok
    )
    runtime_live_lean_lsp_mcp_scorecard_present = bool(
        counts.get(
            "research_agent_runtime_live_lean_lsp_mcp_called_scorecard_present",
            "research_agent_runtime_live_lean_lsp_mcp_called_scorecard_ok" in counts,
        )
    )
    runtime_live_lean_lsp_mcp_scorecard_ok = bool(
        counts.get(
            "research_agent_runtime_live_lean_lsp_mcp_called_scorecard_ok",
            False,
        )
    )
    runtime_live_lean_lsp_mcp_scorecard_evidence = str(
        counts.get(
            "research_agent_runtime_live_lean_lsp_mcp_called_scorecard_evidence",
            "",
        )
        or ""
    )
    runtime_live_lean_lsp_mcp_scorecard_blocker = str(
        counts.get(
            "research_agent_runtime_live_lean_lsp_mcp_called_scorecard_blocker",
            "",
        )
        or ""
    )
    runtime_real_kernel_subclaim_scorecard_present = bool(
        counts.get(
            "research_agent_runtime_real_kernel_subclaim_verified_scorecard_present",
            "research_agent_runtime_real_kernel_subclaim_verified_scorecard_ok"
            in counts,
        )
    )
    runtime_real_kernel_subclaim_scorecard_ok = bool(
        counts.get(
            "research_agent_runtime_real_kernel_subclaim_verified_scorecard_ok",
            False,
        )
    )
    runtime_real_kernel_subclaim_scorecard_evidence = str(
        counts.get(
            "research_agent_runtime_real_kernel_subclaim_verified_scorecard_evidence",
            "",
        )
        or ""
    )
    runtime_real_kernel_subclaim_scorecard_blocker = str(
        counts.get(
            "research_agent_runtime_real_kernel_subclaim_verified_scorecard_blocker",
            "",
        )
        or ""
    )
    runtime_full_frontier_theorem_kernel_scorecard_present = bool(
        counts.get(
            "research_agent_runtime_full_frontier_theorem_kernel_proved_scorecard_present",
            "research_agent_runtime_full_frontier_theorem_kernel_proved_scorecard_ok"
            in counts,
        )
    )
    runtime_full_frontier_theorem_kernel_scorecard_ok = bool(
        counts.get(
            "research_agent_runtime_full_frontier_theorem_kernel_proved_scorecard_ok",
            False,
        )
    )
    runtime_full_frontier_theorem_kernel_scorecard_evidence = str(
        counts.get(
            "research_agent_runtime_full_frontier_theorem_kernel_proved_scorecard_evidence",
            "",
        )
        or ""
    )
    runtime_full_frontier_theorem_kernel_scorecard_blocker = str(
        counts.get(
            "research_agent_runtime_full_frontier_theorem_kernel_proved_scorecard_blocker",
            "",
        )
        or ""
    )
    runtime_formal_gap_planner_handoff_rows = _int(
        counts.get("research_agent_runtime_formal_gap_planner_handoff_rows")
    )
    runtime_formal_gap_planner_missing_execution_context = _int(
        counts.get(
            "research_agent_runtime_formal_gap_planner_handoff_rows_missing_execution_context"
        )
    )
    runtime_formal_gap_planner_context_complete = bool(
        counts.get(
            "research_agent_runtime_formal_gap_planner_executable_handoff_context_complete",
            runtime_formal_gap_planner_handoff_rows <= 0,
        )
    )
    runtime_formal_gap_planner_followthrough = bool(
        counts.get(
            "research_agent_runtime_formal_gap_planner_live_route_planner_followthrough",
            runtime_formal_gap_planner_handoff_rows <= 0,
        )
    )
    runtime_formal_gap_planner_ok = (
        runtime_formal_gap_planner_handoff_rows <= 0
        or (
            runtime_formal_gap_planner_missing_execution_context == 0
            and runtime_formal_gap_planner_context_complete
            and runtime_formal_gap_planner_followthrough
        )
    )
    runtime_gap_routing_input_rows = _int(
        counts.get("research_agent_runtime_capability_gap_routing_input_rows")
    )
    runtime_gap_routing_input_rows_seen = _int(
        counts.get("research_agent_runtime_capability_gap_routing_input_rows_seen")
    )
    runtime_gap_routing_input_retention_policy = str(
        counts.get(
            "research_agent_runtime_capability_gap_routing_input_retention_policy",
            "",
        )
        or ""
    )
    runtime_gap_routing_retention_ok = (
        runtime_gap_routing_input_rows_seen <= runtime_gap_routing_input_rows
        or runtime_gap_routing_input_retention_policy == "priority_pinned_latest_rows"
    )
    runtime_gap_routing_selection_counts = counts.get(
        "research_agent_runtime_capability_gap_routing_input_retention_selection_counts",
        {},
    )
    runtime_gap_routing_selected_rows = 0
    if isinstance(runtime_gap_routing_selection_counts, Mapping):
        runtime_gap_routing_selected_rows = sum(
            _int(value) for value in runtime_gap_routing_selection_counts.values()
        )
    runtime_gap_routing_missing_selection = _int(
        counts.get(
            "research_agent_runtime_capability_gap_routing_input_rows_missing_retention_selection"
        )
    )
    runtime_gap_routing_missing_selection_boundary = _int(
        counts.get(
            "research_agent_runtime_capability_gap_routing_input_rows_missing_retention_selection_boundary"
        )
    )
    runtime_gap_routing_selection_required = (
        runtime_gap_routing_input_rows_seen > runtime_gap_routing_input_rows
        or runtime_gap_routing_input_retention_policy == "priority_pinned_latest_rows"
    )
    runtime_gap_routing_retention_selection_ok = (
        not runtime_gap_routing_selection_required
        or (
            runtime_gap_routing_missing_selection == 0
            and runtime_gap_routing_missing_selection_boundary == 0
            and runtime_gap_routing_selected_rows >= runtime_gap_routing_input_rows
        )
    )
    runtime_deferred_meta_gap_count = _int(
        counts.get("research_agent_runtime_architect_deferred_meta_capability_gaps")
    )
    runtime_deferred_meta_gap_owners = counts.get(
        "research_agent_runtime_architect_deferred_meta_capability_gap_owners",
        {},
    )
    runtime_deferred_meta_gap_requirement_ids = counts.get(
        "research_agent_runtime_architect_deferred_meta_capability_gap_requirement_ids",
        [],
    )
    runtime_deferred_meta_gap_details_present = (
        runtime_deferred_meta_gap_count <= 0
        or (
            isinstance(runtime_deferred_meta_gap_owners, Mapping)
            and bool(runtime_deferred_meta_gap_owners)
            and isinstance(runtime_deferred_meta_gap_requirement_ids, (list, tuple))
            and bool(runtime_deferred_meta_gap_requirement_ids)
        )
    )
    runtime_deferred_meta_gaps_visible = bool(
        counts.get(
            "research_agent_runtime_architect_deferred_meta_capability_gaps_visible",
            runtime_deferred_meta_gap_details_present,
        )
    )
    runtime_deferred_meta_gaps_resolved = bool(
        counts.get(
            "research_agent_runtime_architect_deferred_meta_capability_gaps_resolved",
            runtime_deferred_meta_gap_count <= 0,
        )
    )
    runtime_gap_routing_priority_pinned_requirement_ids = _string_set(
        counts.get(
            "research_agent_runtime_capability_gap_routing_input_priority_pinned_requirement_ids",
            [],
        )
    )
    runtime_deferred_meta_gap_resolution_replay_priority_pinned = bool(
        counts.get(
            "research_agent_runtime_architect_deferred_meta_capability_gap_resolution_replay_priority_pinned",
            runtime_deferred_meta_gap_count <= 0
            or ARCHITECT_DEFERRED_META_RESOLUTION_REQUIREMENT_ID
            in runtime_gap_routing_priority_pinned_requirement_ids,
        )
    )
    runtime_deferred_meta_gaps_ok = (
        runtime_deferred_meta_gaps_resolved
        and runtime_deferred_meta_gaps_visible
        and runtime_deferred_meta_gap_resolution_replay_priority_pinned
    )
    s13_capability_ready = bool(
        counts.get("research_agent_runtime_capability_ready_for_full_ai_statistician")
    )
    runtime_exact_semantic_authoring_required = bool(
        counts.get("research_agent_runtime_exact_semantic_definition_authoring_required")
    )
    runtime_exact_semantic_authoring_live_attempted = _int(
        counts.get(
            "research_agent_runtime_exact_semantic_definition_authoring_live_llm_attempted"
        )
    )
    runtime_exact_semantic_authoring_post_runtime_local_checked = _int(
        counts.get(
            "research_agent_runtime_exact_semantic_definition_authoring_post_runtime_local_lean_checked"
        )
    )
    runtime_exact_semantic_authoring_post_runtime_local_compiled = _int(
        counts.get(
            "research_agent_runtime_exact_semantic_definition_authoring_post_runtime_local_lean_compiled"
        )
    )
    runtime_pf_bv_component_attached = bool(
        counts.get(
            "research_agent_runtime_pseudo_formal_block_verifier_component_gate_attached"
        )
    )
    runtime_pf_bv_component_capability_evidence_ok = bool(
        counts.get(
            "research_agent_runtime_pseudo_formal_block_verifier_component_gate_capability_evidence_ok"
        )
    )
    runtime_pf_bv_component_prompt_packets = _int(
        counts.get(
            "research_agent_runtime_pseudo_formal_block_verifier_component_gate_prompt_packets"
        )
    )
    runtime_pf_bv_component_valid_responses = _int(
        counts.get(
            "research_agent_runtime_pseudo_formal_block_verifier_component_gate_valid_responses"
        )
    )
    runtime_pf_bv_component_runtime_learning_rows = _int(
        counts.get(
            "research_agent_runtime_pseudo_formal_block_verifier_component_gate_runtime_learning_rows"
        )
    )
    runtime_pf_bv_component_source_runtime_learning_path_count = _int(
        counts.get(
            "research_agent_runtime_pseudo_formal_block_verifier_component_gate_source_runtime_learning_jsonl_path_count"
        )
    )
    runtime_pf_bv_component_source_runtime_learning_lineage_ok = bool(
        counts.get(
            "research_agent_runtime_pseudo_formal_block_verifier_component_gate_source_runtime_learning_lineage_ok"
        )
    )
    runtime_pf_bv_component_ok = bool(
        runtime_pf_bv_component_attached
        and runtime_pf_bv_component_capability_evidence_ok
        and runtime_pf_bv_component_prompt_packets > 0
        and runtime_pf_bv_component_valid_responses > 0
        and runtime_pf_bv_component_runtime_learning_rows > 0
        and runtime_pf_bv_component_source_runtime_learning_path_count > 0
        and runtime_pf_bv_component_source_runtime_learning_lineage_ok
    )
    s13_issues: list[str] = []
    if not s13_capability_ready:
        s13_issues.append(
            "no single live Architect-orchestrated AgentRuntime run has yet satisfied the full capability scorecard, including aggregate live exact semantic-definition authoring when required"
        )
    if (
        not s13_capability_ready
        and runtime_exact_semantic_authoring_required
        and runtime_exact_semantic_authoring_live_attempted <= 0
    ):
        s13_issues.append(
            "exact semantic-definition authoring is required but no lineage-checked live LLM attempt is visible to the system audit"
        )
    if (
        not s13_capability_ready
        and runtime_exact_semantic_authoring_post_runtime_local_checked > 0
        and runtime_exact_semantic_authoring_post_runtime_local_compiled <= 0
    ):
        s13_issues.append(
            "post-runtime exact semantic-definition candidates reached local Lean but still require Lean repair before proof-body search can resume"
        )
    if not runtime_pf_bv_contract_ok:
        s13_issues.append(
            "integrated pseudo-formal/block-verification routing is incomplete: required PF/BV activations must produce effective routed rows; blocked, pending, or quarantine diagnostics do not satisfy activation, and emitted rows need explicit row kinds, effective/diagnostic split telemetry, complete PF+BV method lineage, scope-parent forest, and non-proof boundary"
        )
    if not runtime_pf_semantic_bridge_ok:
        s13_issues.append(
            "pseudo-formal source-to-bridge semantic primitive work orders did not reach the source-semantic ProofEngineer bridge with a semantic-support/not-source-theorem-proof boundary"
        )
    if not runtime_pf_exact_semantic_source_lookup_ok:
        s13_issues.append(
            "pseudo-formal exact semantic-definition work orders did not reach the exact semantic-definition source lookup/review loop as non-proof definition-authoring work"
        )
    if not runtime_formal_gap_planner_ok:
        s13_issues.append(
            "formal-gap planner handoff rows lost executable target-intake/route-planner/reuse-smoke context or did not produce live route-planner target-prover replay route-revision feedback"
        )
    if not runtime_gap_routing_retention_ok:
        s13_issues.append(
            "capability-gap routing input was truncated without priority-pinned retention, so older high-impact runtime obligations may not reach the next Architect turn"
        )
    if not runtime_gap_routing_retention_selection_ok:
        s13_issues.append(
            "capability-gap routing input lacks row-level retention_selection/non-evidence boundary metadata, so Architect cannot distinguish priority-pinned obligations from latest/backfill context in compressed views"
        )
    if not runtime_deferred_meta_gaps_visible:
        s13_issues.append(
            "AgentRuntime/Architect deferred meta capability gap telemetry is counted but missing owner and requirement visibility, so control-plane debt can disappear from readiness planning"
        )
    elif not runtime_deferred_meta_gaps_resolved:
        s13_issues.append(
            "unresolved AgentRuntime/Architect control-plane capability gaps remain deferred; close or explicitly re-run them before claiming integrated runtime readiness"
        )
    if (
        runtime_deferred_meta_gaps_visible
        and not runtime_deferred_meta_gap_resolution_replay_priority_pinned
    ):
        s13_issues.append(
            "unresolved AgentRuntime/Architect control-plane capability gaps are not priority-pinned in capability-gap routing replay, so the next Architect turn may lose the runtime/Architect repair obligation"
        )
    if not runtime_pf_bv_component_ok:
        s13_issues.append(
            "integrated AgentRuntime has not attached live PF/BV BlockVerifier component-gate evidence with prompt packets, valid responses, validated non-proof runtime learning rows, and source runtime-learning lineage checked to the current runtime output; standalone S11b evidence does not substitute for in-loop calibration"
        )
    if not runtime_formalizer_pf_packet_component_ok:
        s13_issues.append(
            "integrated AgentRuntime has not attached and consumed live Formalizer PF/BV packet-emission evidence into non-proof runtime learning memory with source-anchored pseudo-formal packets, exact-semantic-definition lane routing, nonzero routable work-order rows, no raw model output leakage, preserved non-proof boundary, no theorem-proof claim, and a recomputed attachment gate; standalone S11c evidence or unattached harness evidence does not substitute for in-loop calibration"
        )
    if not runtime_source_theorem_proof_body_authoritative_executor_ran:
        s13_issues.append(
            runtime_source_theorem_proof_body_executor_scorecard_blocker
            if runtime_source_theorem_proof_body_executor_scorecard_present
            and runtime_source_theorem_proof_body_executor_scorecard_blocker
            else "integrated AgentRuntime has not run an exact source-theorem proof-body executor after exact semantic-definition/source lookup work; Formalizer local Lean feedback is still calibration unless a proof-body worker attempts the source theorem boundary in-loop"
        )
    elif not runtime_source_theorem_proof_body_authoritative_goal_reached:
        s13_issues.append(
            runtime_source_theorem_signature_probe_scorecard_blocker
            if runtime_source_theorem_signature_probe_scorecard_present
            and runtime_source_theorem_signature_probe_scorecard_blocker
            else "exact source-theorem proof-body executor produced rows, but the runtime has not shown that the signature/proof-body goal was reached; result rows remain pre-proof-body feedback until that boundary is explicit"
        )
    elif not runtime_source_theorem_semantic_blockers_authoritative_ok:
        s13_issues.append(
            runtime_source_theorem_semantic_blockers_scorecard_blocker
            if runtime_source_theorem_semantic_blockers_scorecard_present
            and runtime_source_theorem_semantic_blockers_scorecard_blocker
            else "exact source-theorem proof-body goal was reached with semantic-review blockers, but the runtime has not exposed exact semantic-definition repair routing or source-theorem kernel closure"
        )
    elif (
        runtime_source_theorem_local_lean_gate_scorecard_present
        and not runtime_source_theorem_local_lean_gate_scorecard_ok
    ):
        s13_issues.append(
            runtime_source_theorem_local_lean_gate_scorecard_blocker
            or "runtime capability scorecard reports that exact source-theorem proof-body execution did not reach local Lean/AXLE feedback or source-theorem kernel verification"
        )
    elif (
        runtime_source_theorem_proof_body_same_lane_scorecard_present
        and not runtime_source_theorem_proof_body_same_lane_scorecard_ok
    ):
        s13_issues.append(
            runtime_source_theorem_proof_body_same_lane_scorecard_blocker
            or "runtime capability scorecard reports that exact source-theorem proof-body executor evidence is not bound to local Lean/AXLE or source-theorem kernel evidence in the same lane"
        )
    elif not runtime_source_theorem_proof_body_aggregate_local_lean_gate_ok:
        s13_issues.append(
            "exact source-theorem proof-body executor result rows exist, but no local Lean/AXLE check or source-theorem kernel verification is visible; proof-body rows must stay non-proof feedback until the verifier boundary is exercised"
        )
    elif not runtime_source_theorem_proof_body_authoritative_same_lane_gate_ok:
        s13_issues.append(
            "exact source-theorem proof-body executor evidence is split across lanes; one proof-body executor lane must show result rows plus local Lean/AXLE feedback or source-theorem kernel verification before S13 can count the path as integrated"
        )
    if (
        runtime_live_lean_lsp_mcp_scorecard_present
        and not runtime_live_lean_lsp_mcp_scorecard_ok
    ):
        s13_issues.append(
            runtime_live_lean_lsp_mcp_scorecard_blocker
            or "runtime capability scorecard reports that live Lean LSP/MCP proof-state diagnostics did not run"
        )
    if (
        runtime_real_kernel_subclaim_scorecard_present
        and not runtime_real_kernel_subclaim_scorecard_ok
    ):
        s13_issues.append(
            runtime_real_kernel_subclaim_scorecard_blocker
            or "runtime capability scorecard reports that no real AXLE/local Lean kernel-verified subclaim or source/frontier target evidence was recorded"
        )
    if (
        runtime_full_frontier_theorem_kernel_scorecard_present
        and not runtime_full_frontier_theorem_kernel_scorecard_ok
    ):
        s13_issues.append(
            runtime_full_frontier_theorem_kernel_scorecard_blocker
            or "runtime capability scorecard reports that the current source/frontier theorem target was not kernel-proved"
        )
    rows = [
        BenchmarkSuiteGuidanceRow(
            suite_id="S0_release_sanity",
            exercised=bool(gates),
            status="OK" if bool(system_gate := gates) and all(bool(v) for v in system_gate.values()) else "CAPACITY_GAP",
            evidence_paths=("research_system_audit_manifest.json",),
            key_counts={
                "all_gates_passed": all(bool(v) for v in gates.values()) if gates else False,
                "proofs_kernel_verified": counts.get("proofs_kernel_verified"),
            },
            honesty_boundary="Release sanity checks scaffold coherence, not autonomous frontier theory discovery.",
            issues=()
            if gates and all(bool(v) for v in gates.values())
            else ("one or more release gates did not pass",),
        ),
        BenchmarkSuiteGuidanceRow(
            suite_id="S1_core_method_e2e",
            exercised=bool(artifacts.get("research_benchmark")),
            status="OK"
            if _int(counts.get("research_ready_with_gaps")) == _int(counts.get("questions"))
            and _int(counts.get("research_simulation_flagged")) == 0
            else "CAPACITY_GAP",
            evidence_paths=(str(artifacts.get("research_benchmark", "")), str(research_questions_file)),
            key_counts={
                "questions": counts.get("questions"),
                "ready_with_gaps": counts.get("research_ready_with_gaps"),
                "simulation_flagged": counts.get("research_simulation_flagged"),
            },
            honesty_boundary="Ready-with-gaps means trace completion with explicit gaps, not full theorem closure.",
            issues=()
            if _int(counts.get("research_simulation_flagged")) == 0
            else ("nominal core simulations still have flagged traces",),
        ),
        BenchmarkSuiteGuidanceRow(
            suite_id="S2_frontier_static_coverage",
            exercised=bool(artifacts.get("frontier_coverage_audit"))
            and bool(artifacts.get("frontier_precision_audit")),
            status="OK"
            if _int(counts.get("frontier_supported")) == frontier_questions
            and _int(counts.get("frontier_precision_flagged")) == 0
            else "CAPACITY_GAP",
            evidence_paths=(
                str(frontier_benchmark_file),
                str(artifacts.get("frontier_coverage_audit", "")),
                str(artifacts.get("frontier_precision_audit", "")),
            ),
            key_counts={
                "frontier_questions": frontier_questions,
                "frontier_supported": counts.get("frontier_supported"),
                "frontier_precision_flagged": counts.get("frontier_precision_flagged"),
            },
            honesty_boundary="60/60 frontier support is routing and scoped-surrogate coverage only.",
            issues=("static frontier routing is saturated; do not use it as proof of capability",)
            if _int(counts.get("frontier_supported")) == frontier_questions
            else ("frontier routing has unsupported or flagged entries",),
        ),
        BenchmarkSuiteGuidanceRow(
            suite_id="S3_frontier_blind_theory_target",
            exercised=bool(artifacts.get("frontier_smoke_benchmark")),
            status="CAPACITY_GAP"
            if frontier_smoke_questions < frontier_questions or theory_coverage < 0.9
            else "OK",
            evidence_paths=(str(artifacts.get("frontier_smoke_benchmark", "")),),
            key_counts={
                "frontier_smoke_questions": frontier_smoke_questions,
                "frontier_questions": frontier_questions,
                "expected_result_coverage_rate": theory_coverage,
            },
            honesty_boundary="Theory-target recovery is semantic planning evidence, not Lean proof evidence.",
            issues=tuple(
                issue
                for issue in (
                    "release smoke is not all-60 frontier scoring"
                    if frontier_smoke_questions < frontier_questions
                    else "",
                    "expected-result coverage remains below the 90% next milestone"
                    if theory_coverage < 0.9
                    else "",
                )
                if issue
            ),
        ),
        BenchmarkSuiteGuidanceRow(
            suite_id="S4_formal_primitive_ladder",
            exercised=bool(artifacts.get("formalization_target_audit"))
            and bool(artifacts.get("proof_bank_expansion")),
            status="CAPACITY_GAP" if missing_primitives > 0 else "OK",
            evidence_paths=(
                str(artifacts.get("formalization_target_audit", "")),
                str(artifacts.get("proof_bank_expansion", "")),
                str(artifacts.get("primitive_source_coverage", "")),
            ),
            key_counts={
                "formal_gaps": counts.get("formal_gaps"),
                "formalized_gaps": counts.get("formalized_gaps"),
                "missing_formal_primitives": missing_primitives,
                "proof_bank_expansion_bridge_ready": counts.get("proof_bank_expansion_bridge_ready"),
                "primitive_source_coverage_direct_wrapper_possible": counts.get(
                    "primitive_source_coverage_direct_wrapper_possible"
                ),
                "primitive_source_coverage_bridge_lemma_needed": counts.get(
                    "primitive_source_coverage_bridge_lemma_needed"
                ),
                "primitive_source_coverage_source_only_not_importable": counts.get(
                    "primitive_source_coverage_source_only_not_importable"
                ),
                "primitive_source_coverage_no_source_found": counts.get(
                    "primitive_source_coverage_no_source_found"
                ),
                "lean_rag_dependency_graph_enabled": counts.get("lean_rag_dependency_graph_enabled"),
                "formal_source_retrieval_ablation_dependency_sensitive_cases": counts.get(
                    "formal_source_retrieval_ablation_dependency_sensitive_cases"
                ),
                "formal_source_retrieval_ablation_dependency_sensitive_new_hits": counts.get(
                    "formal_source_retrieval_ablation_dependency_sensitive_new_hits"
                ),
            },
            honesty_boundary="Formalization targets and skeletons are backlog evidence until kernel-verified.",
            issues=(f"{missing_primitives} missing formal primitives remain",)
            if missing_primitives > 0
            else (),
        ),
        BenchmarkSuiteGuidanceRow(
            suite_id="S5_proof_bank_and_search",
            exercised=bool(artifacts.get("proof_audit"))
            and bool(artifacts.get("proof_search_retrieval_ablation"))
            and bool(artifacts.get("proof_search_retrieval_no_registered_ablation")),
            status=(
                "CAPACITY_GAP"
                if proof_kernel_evidence == 0
                and (proof_search_solved > 0 or proof_search_obligations > 0)
                else (
                    "SATURATED"
                    if proof_search_candidate_delta == 0
                    and proof_search_hard_candidate_delta == 0
                    and proof_search_solved == proof_search_obligations
                    else "OK"
                )
            ),
            evidence_paths=(
                str(artifacts.get("proof_audit", "")),
                str(artifacts.get("proof_search_audit", "")),
                str(artifacts.get("proof_search_kernel_rerun_local_lean", "")),
                str(artifacts.get("proof_search_retrieval_ablation", "")),
                str(artifacts.get("proof_search_retrieval_no_registered_ablation", "")),
            ),
            key_counts={
                "proofs_kernel_verified": proofs_kernel_verified,
                "proof_search_kernel_verified": proof_search_kernel_verified,
                "proof_search_kernel_rerun_local_lean_verified": proof_search_kernel_rerun_verified,
                "proof_search_kernel_rerun_local_lean_total": counts.get(
                    "proof_search_kernel_rerun_local_lean_total"
                ),
                "proof_search_kernel_rerun_local_lean_verifier": counts.get(
                    "proof_search_kernel_rerun_local_lean_verifier"
                ),
                "proof_search_solved": proof_search_solved,
                "proof_search_obligations": proof_search_obligations,
                "proof_search_retrieval_ablation_candidate_delta": proof_search_candidate_delta,
                "proof_search_retrieval_no_registered_ablation_candidate_delta": proof_search_hard_candidate_delta,
                "proof_search_retrieval_no_registered_ablation_solved_delta": proof_search_hard_solved_delta,
                "proof_search_retrieval_no_registered_ablation_include_registered_proof": counts.get(
                    "proof_search_retrieval_no_registered_ablation_include_registered_proof"
                ),
                "lean_rag_dependency_graph_enabled": counts.get("lean_rag_dependency_graph_enabled"),
            },
            honesty_boundary=(
                "Kernel-verified registered obligations are proof evidence; ordinary and no-registered "
                "retrieval ablations are search evidence unless run with AXLE/local Lean verification. "
                "Focused local-rerun proof-search overlay counts are evidence only for their selected obligations."
            ),
            issues=tuple(
                issue
                for issue in (
                    "proof-search and proof-bank evidence lacks AXLE/local Lean kernel verification"
                    if proof_kernel_evidence == 0
                    and (proof_search_solved > 0 or proof_search_obligations > 0)
                    else "",
                    "current bounded proof-search suite is saturated; stronger RAG shows no downstream lift"
                    if proof_search_candidate_delta == 0 and proof_search_hard_candidate_delta == 0
                    else "",
                )
                if issue
            ),
        ),
        BenchmarkSuiteGuidanceRow(
            suite_id="S6_algorithm_simulation_stress",
            exercised=bool(artifacts.get("algorithm_simulation_stress_audit")),
            status="OK"
            if bool(counts.get("algorithm_simulation_stress_multi_seed_checked"))
            and bool(counts.get("algorithm_simulation_stress_all_passed"))
            and bool(counts.get("algorithm_simulation_stress_all_finite_metrics"))
            and bool(counts.get("algorithm_simulation_stress_all_stress_ledgers_ok"))
            and bool(counts.get("algorithm_simulation_stress_all_diagnoses_ok"))
            else "UNDER_SPECIFIED",
            evidence_paths=(
                str(artifacts.get("algorithm_simulation_stress_audit", "")),
                str(artifacts.get("research_algorithm_audit", "")),
            ),
            key_counts={
                "research_algorithms_ok": counts.get("research_algorithms_ok"),
                "research_algorithms_total": counts.get("research_algorithms_total"),
                "algorithm_simulation_stress_cases": counts.get("algorithm_simulation_stress_cases"),
                "algorithm_simulation_stress_seeds": counts.get("algorithm_simulation_stress_seeds"),
                "algorithm_simulation_stress_all_passed": counts.get(
                    "algorithm_simulation_stress_all_passed"
                ),
                "algorithm_simulation_stress_all_finite_metrics": counts.get(
                    "algorithm_simulation_stress_all_finite_metrics"
                ),
                "algorithm_simulation_stress_all_stress_ledgers_ok": counts.get(
                    "algorithm_simulation_stress_all_stress_ledgers_ok"
                ),
                "research_report_simulations_passed": counts.get("research_report_simulations_passed"),
                "research_report_simulations": counts.get("research_report_simulations"),
            },
            honesty_boundary="Simulation diagnostics are empirical checks, not guarantees.",
            issues=()
            if bool(counts.get("algorithm_simulation_stress_multi_seed_checked"))
            and bool(counts.get("algorithm_simulation_stress_all_passed"))
            and bool(counts.get("algorithm_simulation_stress_all_finite_metrics"))
            and bool(counts.get("algorithm_simulation_stress_all_stress_ledgers_ok"))
            and bool(counts.get("algorithm_simulation_stress_all_diagnoses_ok"))
            else ("needs passing multi-seed stress ledgers and finite metric checks",),
        ),
        BenchmarkSuiteGuidanceRow(
            suite_id="S7_feedback_loop_repair",
            exercised=bool(artifacts.get("research_loop"))
            and bool(artifacts.get("algorithm_repair_sandbox_patch_eval")),
            status="CAPACITY_GAP" if algorithm_promotion_ready == 0 else "OK",
            evidence_paths=(
                str(artifacts.get("research_loop", "")),
                str(artifacts.get("research_loop_repair_audit", "")),
                str(artifacts.get("algorithm_repair_sandbox_patch_eval", "")),
            ),
            key_counts={
                "research_loop_theory_revisions": counts.get("research_loop_theory_revisions"),
                "algorithm_repair_patch_eval_promotion_ready": algorithm_promotion_ready,
                "algorithm_repair_production_patch_applied": counts.get(
                    "algorithm_repair_production_patch_applied"
                ),
            },
            honesty_boundary="Queued or sandboxed repair is not the same as autonomous corrected theory/procedure convergence.",
            issues=("algorithm repair has no promotion-ready patch in the current audit",)
            if algorithm_promotion_ready == 0
            else (),
        ),
        BenchmarkSuiteGuidanceRow(
            suite_id="S8_adversarial_unsupported_intake",
            exercised=bool(artifacts.get("adversarial_intake_audit")),
            status="OK"
            if _int(counts.get("adversarial_intake_cases")) > 0
            and _int(counts.get("adversarial_intake_ok")) == _int(counts.get("adversarial_intake_cases"))
            else "STALE_OR_MISSING",
            evidence_paths=(
                str(artifacts.get("adversarial_intake_audit", "")),
                "benchmarks/adversarial_unsupported_intake.json",
            ),
            key_counts={
                "adversarial_intake_cases": counts.get("adversarial_intake_cases"),
                "adversarial_intake_ok": counts.get("adversarial_intake_ok"),
                "adversarial_intake_rejected": counts.get("adversarial_intake_rejected"),
                "research_intake_unsupported": counts.get("research_intake_unsupported"),
                "research_intake_unsupported_rejected": counts.get("research_intake_unsupported_rejected"),
            },
            honesty_boundary="Unsupported rejection tests protect against overclaiming autonomous capability.",
            issues=()
            if _int(counts.get("adversarial_intake_cases")) > 0
            and _int(counts.get("adversarial_intake_ok")) == _int(counts.get("adversarial_intake_cases"))
            else ("no passing dedicated adversarial/prompt-leakage suite is wired into the release audit",),
        ),
        BenchmarkSuiteGuidanceRow(
            suite_id="S9_fresh_holdout_frontier",
            exercised=bool(artifacts.get("fresh_holdout_frontier_audit")),
            status="OK"
            if bool(counts.get("fresh_holdout_frontier_all_ok"))
            and _int(counts.get("fresh_holdout_frontier_entries")) > 0
            and _int(counts.get("fresh_holdout_frontier_scored_traces")) > 0
            and bool(counts.get("fresh_holdout_frontier_identity_withheld"))
            and not bool(counts.get("fresh_holdout_frontier_source_leakage_detected"))
            else "STALE_OR_MISSING",
            evidence_paths=(
                str(artifacts.get("fresh_holdout_frontier_audit", "")),
                "benchmarks/fresh_holdout_frontier_benchmark.md",
            ),
            key_counts={
                "fresh_holdout_frontier_entries": counts.get("fresh_holdout_frontier_entries"),
                "fresh_holdout_frontier_supported": counts.get("fresh_holdout_frontier_supported"),
                "fresh_holdout_frontier_unsupported": counts.get("fresh_holdout_frontier_unsupported"),
                "fresh_holdout_frontier_scored_traces": counts.get("fresh_holdout_frontier_scored_traces"),
                "fresh_holdout_frontier_expected_results": counts.get(
                    "fresh_holdout_frontier_expected_results"
                ),
                "fresh_holdout_frontier_expected_results_covered": counts.get(
                    "fresh_holdout_frontier_expected_results_covered"
                ),
                "fresh_holdout_frontier_expected_result_coverage_rate": counts.get(
                    "fresh_holdout_frontier_expected_result_coverage_rate"
                ),
                "fresh_holdout_frontier_identity_withheld": counts.get(
                    "fresh_holdout_frontier_identity_withheld"
                ),
                "fresh_holdout_frontier_source_leakage_detected": counts.get(
                    "fresh_holdout_frontier_source_leakage_detected"
                ),
            },
            honesty_boundary="Fresh holdout papers are needed before claiming generalization beyond curated templates.",
            issues=()
            if bool(counts.get("fresh_holdout_frontier_all_ok"))
            and _int(counts.get("fresh_holdout_frontier_entries")) > 0
            and _int(counts.get("fresh_holdout_frontier_scored_traces")) > 0
            and bool(counts.get("fresh_holdout_frontier_identity_withheld"))
            and not bool(counts.get("fresh_holdout_frontier_source_leakage_detected"))
            else ("no passing source-withheld fresh holdout frontier suite is currently present",),
        ),
        BenchmarkSuiteGuidanceRow(
            suite_id="S10_live_coding_agent_generated_repair",
            exercised=bool(artifacts.get("coding_agent_generated_code_repair_eval")),
            status="OK"
            if bool(counts.get("coding_agent_generated_code_repair_capability_evidence_ok"))
            else "CAPACITY_GAP",
            evidence_paths=(
                str(artifacts.get("coding_agent_generated_code_repair_eval", "")),
                "runs/coding_agent_generated_code_repair_eval/coding_agent_generated_code_repair_eval_manifest.json",
            ),
            key_counts={
                "coding_agent_generated_code_repair_capability_evidence_ok": counts.get(
                    "coding_agent_generated_code_repair_capability_evidence_ok"
                ),
                "coding_agent_algorithm_capability_evidence_ok": counts.get(
                    "coding_agent_algorithm_capability_evidence_ok"
                ),
                "coding_agent_simulation_capability_evidence_ok": counts.get(
                    "coding_agent_simulation_capability_evidence_ok"
                ),
                "coding_agent_algorithm_repair_sequences": counts.get(
                    "coding_agent_algorithm_repair_sequences"
                ),
                "coding_agent_simulation_repair_sequences": counts.get(
                    "coding_agent_simulation_repair_sequences"
                ),
            },
            honesty_boundary=(
                "Static fixture plumbing and registered templates do not count as coding-agent "
                "capacity. This suite checks generated implementation/simulation repair only; "
                "it is not theorem proof evidence."
            ),
            issues=()
            if bool(counts.get("coding_agent_generated_code_repair_capability_evidence_ok"))
            else (
                "no live Claude/OpenAI combined AlgorithmEngineer+SimulationEngineer generated-code fail-then-pass repair evidence is present",
            ),
        ),
        BenchmarkSuiteGuidanceRow(
            suite_id="S11_live_formalizer_lean_candidate_repair",
            exercised=bool(artifacts.get("formalizer_lean_candidate_repair_eval")),
            status="OK"
            if bool(counts.get("formalizer_lean_candidate_repair_capability_evidence_ok"))
            else "CAPACITY_GAP",
            evidence_paths=(
                str(artifacts.get("formalizer_lean_candidate_repair_eval", "")),
                "runs/formalizer_lean_candidate_repair_eval/formalizer_lean_candidate_repair_eval_manifest.json",
            ),
            key_counts={
                "formalizer_lean_candidate_repair_capability_evidence_ok": counts.get(
                    "formalizer_lean_candidate_repair_capability_evidence_ok"
                ),
                "formalizer_lean_candidate_repair_sequences": counts.get(
                    "formalizer_lean_candidate_repair_sequences"
                ),
                "formalizer_lean_candidate_repair_local_lean_checked": counts.get(
                    "formalizer_lean_candidate_repair_local_lean_checked"
                ),
                "formalizer_lean_candidate_repair_local_lean_compiled": counts.get(
                    "formalizer_lean_candidate_repair_local_lean_compiled"
                ),
                "formalizer_lean_candidate_repair_candidate_kernel_verified": counts.get(
                    "formalizer_lean_candidate_repair_candidate_kernel_verified"
                ),
                "formalizer_lean_candidate_repair_source_theorem_kernel_verified": counts.get(
                    "formalizer_lean_candidate_repair_source_theorem_kernel_verified"
                ),
            },
            honesty_boundary=(
                "This suite checks live Formalizer/ProofEngineer response to local Lean "
                "candidate diagnostics. A compiled candidate is kernel evidence only "
                "for that exact helper artifact; it is not source theorem proof and "
                "static fixture plumbing cannot count as capability."
            ),
            issues=()
            if bool(counts.get("formalizer_lean_candidate_repair_capability_evidence_ok"))
            else (
                "no live Claude/OpenAI Formalizer Lean-candidate fail-then-pass repair evidence is present",
            ),
        ),
        BenchmarkSuiteGuidanceRow(
            suite_id="S11c_live_formalizer_pseudo_formal_packet",
            exercised=standalone_formalizer_pf_packet_component_exercised
            or runtime_formalizer_pf_packet_component_exercised,
            status="OK"
            if formalizer_pf_packet_component_ok
            else "CAPACITY_GAP",
            evidence_paths=(
                str(artifacts.get("formalizer_pseudo_formal_packet_eval", "")),
                str(
                    counts.get(
                        "research_agent_runtime_formalizer_pseudo_formal_packet_component_gate_manifest_path",
                        "",
                    )
                    or counts.get(
                        "research_agent_runtime_internal_formalizer_pseudo_formal_packet_eval_manifest_path",
                        "",
                    )
                    or ""
                ),
                "runs/formalizer_pseudo_formal_packet_eval/formalizer_pseudo_formal_packet_eval_manifest.json",
            ),
            key_counts={
                "formalizer_pseudo_formal_packet_component_gate_capability_evidence_ok": counts.get(
                    "formalizer_pseudo_formal_packet_component_gate_capability_evidence_ok"
                ),
                "formalizer_pseudo_formal_packet_component_gate_live_generator": counts.get(
                    "formalizer_pseudo_formal_packet_component_gate_live_generator"
                ),
                "formalizer_pseudo_formal_packet_component_gate_static_or_fixture_only": counts.get(
                    "formalizer_pseudo_formal_packet_component_gate_static_or_fixture_only"
                ),
                "formalizer_pseudo_formal_packet_component_gate_pseudo_formal_packets": counts.get(
                    "formalizer_pseudo_formal_packet_component_gate_pseudo_formal_packets"
                ),
                "formalizer_pseudo_formal_packet_component_gate_work_order_rows": counts.get(
                    "formalizer_pseudo_formal_packet_component_gate_work_order_rows"
                ),
                "formalizer_pseudo_formal_packet_component_gate_routable_work_order_rows": counts.get(
                    "formalizer_pseudo_formal_packet_component_gate_routable_work_order_rows"
                ),
                "formalizer_pseudo_formal_packet_component_gate_routable_row_kinds": counts.get(
                    "formalizer_pseudo_formal_packet_component_gate_routable_row_kinds"
                ),
                "formalizer_pseudo_formal_packet_component_gate_routable_target_lanes": counts.get(
                    "formalizer_pseudo_formal_packet_component_gate_routable_target_lanes"
                ),
                "formalizer_pseudo_formal_packet_component_gate_nonproof_boundary_preserved": counts.get(
                    "formalizer_pseudo_formal_packet_component_gate_nonproof_boundary_preserved"
                ),
                "formalizer_pseudo_formal_packet_component_gate_raw_model_output_written": counts.get(
                    "formalizer_pseudo_formal_packet_component_gate_raw_model_output_written"
                ),
                "formalizer_pseudo_formal_packet_component_gate_exact_semantic_definition_lane_present": counts.get(
                    "formalizer_pseudo_formal_packet_component_gate_exact_semantic_definition_lane_present"
                ),
                "formalizer_pseudo_formal_packet_component_gate_exact_semantic_definition_rows": counts.get(
                    "formalizer_pseudo_formal_packet_component_gate_exact_semantic_definition_rows"
                ),
                "formalizer_pseudo_formal_packet_component_gate_exact_semantic_definition_rows_with_source_anchors": counts.get(
                    "formalizer_pseudo_formal_packet_component_gate_exact_semantic_definition_rows_with_source_anchors"
                ),
                "formalizer_pseudo_formal_packet_component_gate_exact_semantic_definition_rows_with_semantic_requirements": counts.get(
                    "formalizer_pseudo_formal_packet_component_gate_exact_semantic_definition_rows_with_semantic_requirements"
                ),
                "formalizer_pseudo_formal_packet_component_gate_exact_semantic_definition_rows_with_lineage": counts.get(
                    "formalizer_pseudo_formal_packet_component_gate_exact_semantic_definition_rows_with_lineage"
                ),
                "formalizer_pseudo_formal_packet_component_gate_exact_semantic_definition_rows_source_anchored": counts.get(
                    "formalizer_pseudo_formal_packet_component_gate_exact_semantic_definition_rows_source_anchored"
                ),
                "formalizer_pseudo_formal_packet_component_gate_exact_semantic_definition_rows_semantic_requirements_present": counts.get(
                    "formalizer_pseudo_formal_packet_component_gate_exact_semantic_definition_rows_semantic_requirements_present"
                ),
                "formalizer_pseudo_formal_packet_component_gate_exact_semantic_definition_rows_lineage_complete": counts.get(
                    "formalizer_pseudo_formal_packet_component_gate_exact_semantic_definition_rows_lineage_complete"
                ),
                "formalizer_pseudo_formal_packet_component_gate_proof_evidence_status_ok": counts.get(
                    "formalizer_pseudo_formal_packet_component_gate_proof_evidence_status_ok"
                ),
                "formalizer_pseudo_formal_packet_component_gate_no_theorem_proof_claim": counts.get(
                    "formalizer_pseudo_formal_packet_component_gate_no_theorem_proof_claim"
                ),
                "research_agent_runtime_formalizer_pseudo_formal_packet_component_gate_attached": counts.get(
                    "research_agent_runtime_formalizer_pseudo_formal_packet_component_gate_attached"
                ),
                "research_agent_runtime_formalizer_pseudo_formal_packet_component_gate_capability_evidence_ok": counts.get(
                    "research_agent_runtime_formalizer_pseudo_formal_packet_component_gate_capability_evidence_ok"
                ),
                "research_agent_runtime_formalizer_pseudo_formal_packet_component_gate_pseudo_formal_packets": counts.get(
                    "research_agent_runtime_formalizer_pseudo_formal_packet_component_gate_pseudo_formal_packets"
                ),
                "research_agent_runtime_formalizer_pseudo_formal_packet_component_gate_routable_work_order_rows": counts.get(
                    "research_agent_runtime_formalizer_pseudo_formal_packet_component_gate_routable_work_order_rows"
                ),
                "research_agent_runtime_formalizer_pseudo_formal_packet_component_gate_routable_target_lanes": counts.get(
                    "research_agent_runtime_formalizer_pseudo_formal_packet_component_gate_routable_target_lanes"
                ),
                "research_agent_runtime_formalizer_pseudo_formal_packet_component_gate_nonproof_boundary_preserved": counts.get(
                    "research_agent_runtime_formalizer_pseudo_formal_packet_component_gate_nonproof_boundary_preserved"
                ),
                "research_agent_runtime_formalizer_pseudo_formal_packet_component_gate_raw_model_output_written": counts.get(
                    "research_agent_runtime_formalizer_pseudo_formal_packet_component_gate_raw_model_output_written"
                ),
                "research_agent_runtime_formalizer_pseudo_formal_packet_component_gate_exact_semantic_definition_lane_present": counts.get(
                    "research_agent_runtime_formalizer_pseudo_formal_packet_component_gate_exact_semantic_definition_lane_present"
                ),
                "research_agent_runtime_formalizer_pseudo_formal_packet_component_gate_exact_semantic_definition_rows": counts.get(
                    "research_agent_runtime_formalizer_pseudo_formal_packet_component_gate_exact_semantic_definition_rows"
                ),
                "research_agent_runtime_formalizer_pseudo_formal_packet_component_gate_exact_semantic_definition_rows_source_anchored": counts.get(
                    "research_agent_runtime_formalizer_pseudo_formal_packet_component_gate_exact_semantic_definition_rows_source_anchored"
                ),
                "research_agent_runtime_formalizer_pseudo_formal_packet_component_gate_exact_semantic_definition_rows_semantic_requirements_present": counts.get(
                    "research_agent_runtime_formalizer_pseudo_formal_packet_component_gate_exact_semantic_definition_rows_semantic_requirements_present"
                ),
                "research_agent_runtime_formalizer_pseudo_formal_packet_component_gate_exact_semantic_definition_rows_lineage_complete": counts.get(
                    "research_agent_runtime_formalizer_pseudo_formal_packet_component_gate_exact_semantic_definition_rows_lineage_complete"
                ),
                "research_agent_runtime_formalizer_pseudo_formal_packet_component_gate_proof_evidence_status_ok": counts.get(
                    "research_agent_runtime_formalizer_pseudo_formal_packet_component_gate_proof_evidence_status_ok"
                ),
                "research_agent_runtime_formalizer_pseudo_formal_packet_component_gate_no_theorem_proof_claim": counts.get(
                    "research_agent_runtime_formalizer_pseudo_formal_packet_component_gate_no_theorem_proof_claim"
                ),
                "research_agent_runtime_formalizer_pseudo_formal_packet_component_gate_attachment_gate_recomputed": counts.get(
                    "research_agent_runtime_formalizer_pseudo_formal_packet_component_gate_attachment_gate_recomputed"
                ),
                "research_agent_runtime_formalizer_pseudo_formal_packet_component_gate_learning_consumed": counts.get(
                    "research_agent_runtime_formalizer_pseudo_formal_packet_component_gate_learning_consumed",
                    runtime_formalizer_pf_packet_component_learning_consumed,
                ),
                "research_agent_runtime_formalizer_pseudo_formal_packet_component_gate_learning_rows": counts.get(
                    "research_agent_runtime_formalizer_pseudo_formal_packet_component_gate_learning_rows",
                    runtime_formalizer_pf_packet_component_learning_rows,
                ),
                "research_agent_runtime_formalizer_pseudo_formal_packet_component_gate_learning_consumed_rows": counts.get(
                    "research_agent_runtime_formalizer_pseudo_formal_packet_component_gate_learning_consumed_rows",
                    runtime_formalizer_pf_packet_component_learning_consumed_rows,
                ),
                "research_agent_runtime_internal_formalizer_pseudo_formal_packet_eval_capability_evidence_ok": counts.get(
                    "research_agent_runtime_internal_formalizer_pseudo_formal_packet_eval_capability_evidence_ok"
                ),
                "research_agent_runtime_internal_formalizer_pseudo_formal_packet_eval_routable_target_lanes": counts.get(
                    "research_agent_runtime_internal_formalizer_pseudo_formal_packet_eval_routable_target_lanes"
                ),
                "research_agent_runtime_internal_formalizer_pseudo_formal_packet_eval_exact_semantic_definition_lane_present": counts.get(
                    "research_agent_runtime_internal_formalizer_pseudo_formal_packet_eval_exact_semantic_definition_lane_present"
                ),
                "research_agent_runtime_internal_formalizer_pseudo_formal_packet_eval_exact_semantic_definition_rows": counts.get(
                    "research_agent_runtime_internal_formalizer_pseudo_formal_packet_eval_exact_semantic_definition_rows"
                ),
                "research_agent_runtime_internal_formalizer_pseudo_formal_packet_eval_exact_semantic_definition_rows_source_anchored": counts.get(
                    "research_agent_runtime_internal_formalizer_pseudo_formal_packet_eval_exact_semantic_definition_rows_source_anchored"
                ),
                "research_agent_runtime_internal_formalizer_pseudo_formal_packet_eval_exact_semantic_definition_rows_semantic_requirements_present": counts.get(
                    "research_agent_runtime_internal_formalizer_pseudo_formal_packet_eval_exact_semantic_definition_rows_semantic_requirements_present"
                ),
                "research_agent_runtime_internal_formalizer_pseudo_formal_packet_eval_exact_semantic_definition_rows_lineage_complete": counts.get(
                    "research_agent_runtime_internal_formalizer_pseudo_formal_packet_eval_exact_semantic_definition_rows_lineage_complete"
                ),
                "research_agent_runtime_internal_formalizer_pseudo_formal_packet_eval_proof_evidence_status_ok": counts.get(
                    "research_agent_runtime_internal_formalizer_pseudo_formal_packet_eval_proof_evidence_status_ok"
                ),
                "research_agent_runtime_internal_formalizer_pseudo_formal_packet_eval_no_theorem_proof_claim": counts.get(
                    "research_agent_runtime_internal_formalizer_pseudo_formal_packet_eval_no_theorem_proof_claim"
                ),
                "research_agent_runtime_internal_formalizer_pseudo_formal_packet_eval_attachment_gate_recomputed": counts.get(
                    "research_agent_runtime_internal_formalizer_pseudo_formal_packet_eval_attachment_gate_recomputed"
                ),
                "effective_pseudo_formal_packets": formalizer_pf_packet_packets,
                "effective_routable_work_order_rows": formalizer_pf_packet_routable_rows,
                "effective_routable_target_lanes": sorted(
                    formalizer_pf_packet_target_lanes
                ),
                "effective_exact_semantic_definition_lane_present": formalizer_pf_packet_exact_lane_present,
                "effective_exact_semantic_definition_rows": formalizer_pf_packet_exact_rows,
                "effective_runtime_component_learning_consumed": runtime_formalizer_pf_packet_component_learning_consumed,
                "effective_runtime_component_learning_rows": runtime_formalizer_pf_packet_component_learning_rows,
                "effective_runtime_component_learning_consumed_rows": runtime_formalizer_pf_packet_component_learning_consumed_rows,
                "effective_exact_semantic_definition_rows_source_anchored": formalizer_pf_packet_exact_rows_source_anchored,
                "effective_exact_semantic_definition_rows_semantic_requirements_present": formalizer_pf_packet_exact_rows_semantic_requirements_present,
                "effective_exact_semantic_definition_rows_lineage_complete": formalizer_pf_packet_exact_rows_lineage_complete,
                "effective_nonproof_boundary_preserved": formalizer_pf_packet_nonproof_boundary,
                "effective_proof_evidence_status_ok": formalizer_pf_packet_proof_evidence_status_ok,
                "effective_no_theorem_proof_claim": formalizer_pf_packet_no_theorem_proof_claim,
                "effective_raw_model_output_written": formalizer_pf_packet_raw_output_written,
            },
            honesty_boundary=(
                "Formalizer PF/BV packet emission is decomposition and routing "
                "capacity only. A valid packet with routable rows is not Lean/AXLE "
                "kernel evidence, source theorem proof, or full frontier theorem "
                "closure."
            ),
            issues=()
            if formalizer_pf_packet_component_ok
            else (
                "no live Claude/OpenAI Formalizer PF/BV packet-emission evidence with exact-semantic-definition lane routing, actionable source-anchored exact rows, nonzero routable rows, preserved non-proof boundary, no theorem-proof claim, and integrated runtime-consumed non-proof learning memory when using AgentRuntime evidence is present",
            ),
        ),
        BenchmarkSuiteGuidanceRow(
            suite_id="S11b_live_pseudo_formal_block_verifier",
            exercised=standalone_pf_bv_component_exercised
            or runtime_pf_bv_component_exercised,
            status="OK" if pf_bv_component_ok else "CAPACITY_GAP",
            evidence_paths=(
                str(artifacts.get("pseudo_formal_block_verifier_component_gate", "")),
                str(
                    counts.get(
                        "research_agent_runtime_pseudo_formal_block_verifier_component_gate_manifest_path",
                        "",
                    )
                    or ""
                ),
                "runs/pseudo_formal_block_verifier_component_gate/pseudo_formal_block_verifier_component_gate_manifest.json",
            ),
            key_counts={
                "pseudo_formal_block_verifier_component_gate_capability_evidence_ok": counts.get(
                    "pseudo_formal_block_verifier_component_gate_capability_evidence_ok"
                ),
                "pseudo_formal_block_verifier_component_gate_live_generator": counts.get(
                    "pseudo_formal_block_verifier_component_gate_live_generator"
                ),
                "pseudo_formal_block_verifier_component_gate_static_or_fixture_only": counts.get(
                    "pseudo_formal_block_verifier_component_gate_static_or_fixture_only"
                ),
                "pseudo_formal_block_verifier_component_gate_prompt_packets": counts.get(
                    "pseudo_formal_block_verifier_component_gate_prompt_packets"
                ),
                "pseudo_formal_block_verifier_component_gate_valid_responses": counts.get(
                    "pseudo_formal_block_verifier_component_gate_valid_responses"
                ),
                "pseudo_formal_block_verifier_component_gate_runtime_learning_rows": counts.get(
                    "pseudo_formal_block_verifier_component_gate_runtime_learning_rows"
                ),
                "research_agent_runtime_pseudo_formal_block_verifier_component_gate_attached": counts.get(
                    "research_agent_runtime_pseudo_formal_block_verifier_component_gate_attached"
                ),
                "research_agent_runtime_pseudo_formal_block_verifier_component_gate_capability_evidence_ok": counts.get(
                    "research_agent_runtime_pseudo_formal_block_verifier_component_gate_capability_evidence_ok"
                ),
                "research_agent_runtime_pseudo_formal_block_verifier_component_gate_prompt_packets": counts.get(
                    "research_agent_runtime_pseudo_formal_block_verifier_component_gate_prompt_packets"
                ),
                "research_agent_runtime_pseudo_formal_block_verifier_component_gate_valid_responses": counts.get(
                    "research_agent_runtime_pseudo_formal_block_verifier_component_gate_valid_responses"
                ),
                "research_agent_runtime_pseudo_formal_block_verifier_component_gate_runtime_learning_rows": counts.get(
                    "research_agent_runtime_pseudo_formal_block_verifier_component_gate_runtime_learning_rows"
                ),
                "research_agent_runtime_pseudo_formal_block_verifier_component_gate_source_runtime_learning_jsonl_path_count": counts.get(
                    "research_agent_runtime_pseudo_formal_block_verifier_component_gate_source_runtime_learning_jsonl_path_count"
                ),
                "research_agent_runtime_pseudo_formal_block_verifier_component_gate_source_runtime_learning_lineage_ok": counts.get(
                    "research_agent_runtime_pseudo_formal_block_verifier_component_gate_source_runtime_learning_lineage_ok"
                ),
                "effective_prompt_packets": pf_bv_component_prompt_packets,
                "effective_valid_responses": pf_bv_component_valid_responses,
                "effective_runtime_learning_rows": pf_bv_component_runtime_learning_rows,
                "effective_accepted_blocks": pf_bv_component_accepted_blocks,
                "effective_failed_blocks": pf_bv_component_failed_blocks,
            },
            honesty_boundary=(
                "PF/BV decomposes and checks pseudo-formal natural-language "
                "blocks as verifier feedback. Accepted blocks are still "
                "non-proof runtime learning rows and cannot count as Lean/AXLE "
                "kernel evidence or source theorem proof."
            ),
            issues=pf_bv_component_issues,
        ),
        BenchmarkSuiteGuidanceRow(
            suite_id="S12_live_architect_research_path_policy",
            exercised=bool(artifacts.get("architect_research_path_policy_eval")),
            status="OK"
            if bool(counts.get("architect_research_path_policy_capability_evidence_ok"))
            else "CAPACITY_GAP",
            evidence_paths=(
                str(artifacts.get("architect_research_path_policy_eval", "")),
                "runs/architect_research_path_policy_eval/architect_research_path_policy_eval_manifest.json",
            ),
            key_counts={
                "architect_research_path_policy_capability_evidence_ok": counts.get(
                    "architect_research_path_policy_capability_evidence_ok"
                ),
                "architect_research_path_policy_cases": counts.get(
                    "architect_research_path_policy_cases"
                ),
                "architect_research_path_policy_cases_ok": counts.get(
                    "architect_research_path_policy_cases_ok"
                ),
                "architect_research_path_policy_problem_analysis": counts.get(
                    "architect_research_path_policy_problem_analysis"
                ),
                "architect_research_path_policy_knowledge_bank_plan": counts.get(
                    "architect_research_path_policy_knowledge_bank_plan"
                ),
                "architect_research_path_policy_literature_fair_comparison_plan": counts.get(
                    "architect_research_path_policy_literature_fair_comparison_plan"
                ),
            },
            honesty_boundary=(
                "This suite checks live Architect evidence-policy and research-path "
                "planning only. It does not execute downstream agents, run "
                "simulations, or prove theorems; static replay cannot count as "
                "Architect capability."
            ),
            issues=()
            if bool(counts.get("architect_research_path_policy_capability_evidence_ok"))
            else (
                "no live Claude/OpenAI Architect research-path policy evidence is present",
            ),
        ),
        BenchmarkSuiteGuidanceRow(
            suite_id="S13_live_integrated_agent_runtime_capability",
            exercised=bool(counts.get("research_agent_runtime_audit_requested"))
            or bool(artifacts.get("research_agent_runtime_audit")),
            status="OK"
            if (
                s13_capability_ready
                and runtime_pf_bv_component_ok
                and runtime_formalizer_pf_packet_component_ok
                and runtime_pf_bv_contract_ok
                and runtime_pf_semantic_bridge_ok
                and runtime_pf_exact_semantic_source_lookup_ok
                and runtime_formal_gap_planner_ok
                and runtime_gap_routing_retention_ok
                and runtime_gap_routing_retention_selection_ok
                and runtime_deferred_meta_gaps_ok
                and runtime_source_theorem_proof_body_authoritative_executor_ran
                and runtime_source_theorem_proof_body_authoritative_goal_reached
                and runtime_source_theorem_semantic_blockers_authoritative_ok
                and runtime_source_theorem_proof_body_authoritative_local_lean_gate_ok
                and (
                    not runtime_live_lean_lsp_mcp_scorecard_present
                    or runtime_live_lean_lsp_mcp_scorecard_ok
                )
                and (
                    not runtime_real_kernel_subclaim_scorecard_present
                    or runtime_real_kernel_subclaim_scorecard_ok
                )
                and (
                    not runtime_full_frontier_theorem_kernel_scorecard_present
                    or runtime_full_frontier_theorem_kernel_scorecard_ok
                )
            )
            else "CAPACITY_GAP",
            evidence_paths=(
                str(artifacts.get("research_agent_runtime_audit", "")),
                "runs/research_agent_runtime_audit/research_agent_runtime_audit_manifest.json",
            ),
            key_counts={
                "research_agent_runtime_capability_ready_for_full_ai_statistician": counts.get(
                    "research_agent_runtime_capability_ready_for_full_ai_statistician"
                ),
                "research_agent_runtime_capability_status": counts.get(
                    "research_agent_runtime_capability_status"
                ),
                "research_agent_runtime_architect_enabled": counts.get(
                    "research_agent_runtime_architect_enabled"
                ),
                "research_agent_runtime_live_generator_agents_enabled": counts.get(
                    "research_agent_runtime_live_generator_agents_enabled"
                ),
                "research_agent_runtime_exact_semantic_definition_authoring_required": counts.get(
                    "research_agent_runtime_exact_semantic_definition_authoring_required"
                ),
                "research_agent_runtime_exact_semantic_definition_authoring_llm_attempted": counts.get(
                    "research_agent_runtime_exact_semantic_definition_authoring_llm_attempted"
                ),
                "research_agent_runtime_exact_semantic_definition_authoring_live_llm_attempted": counts.get(
                    "research_agent_runtime_exact_semantic_definition_authoring_live_llm_attempted"
                ),
                "research_agent_runtime_exact_semantic_definition_authoring_backend_provider_names": counts.get(
                    "research_agent_runtime_exact_semantic_definition_authoring_backend_provider_names"
                ),
                "research_agent_runtime_exact_semantic_definition_authoring_post_runtime_worker_attached": counts.get(
                    "research_agent_runtime_exact_semantic_definition_authoring_post_runtime_worker_attached"
                ),
                "research_agent_runtime_exact_semantic_definition_authoring_post_runtime_worker_lineage_ok": counts.get(
                    "research_agent_runtime_exact_semantic_definition_authoring_post_runtime_worker_lineage_ok"
                ),
                "research_agent_runtime_exact_semantic_definition_authoring_post_runtime_worker_live_llm_attempted": counts.get(
                    "research_agent_runtime_exact_semantic_definition_authoring_post_runtime_worker_live_llm_attempted"
                ),
                "research_agent_runtime_exact_semantic_definition_authoring_post_runtime_worker_candidate_packets": counts.get(
                    "research_agent_runtime_exact_semantic_definition_authoring_post_runtime_worker_candidate_packets"
                ),
                "research_agent_runtime_exact_semantic_definition_authoring_post_runtime_materializer_lineage_ok": counts.get(
                    "research_agent_runtime_exact_semantic_definition_authoring_post_runtime_materializer_lineage_ok"
                ),
                "research_agent_runtime_exact_semantic_definition_authoring_post_runtime_materialized_lean_repair_tasks": counts.get(
                    "research_agent_runtime_exact_semantic_definition_authoring_post_runtime_materialized_lean_repair_tasks"
                ),
                "research_agent_runtime_exact_semantic_definition_authoring_post_runtime_lean_repair_lineage_ok": counts.get(
                    "research_agent_runtime_exact_semantic_definition_authoring_post_runtime_lean_repair_lineage_ok"
                ),
                "research_agent_runtime_exact_semantic_definition_authoring_post_runtime_local_lean_checked": counts.get(
                    "research_agent_runtime_exact_semantic_definition_authoring_post_runtime_local_lean_checked"
                ),
                "research_agent_runtime_exact_semantic_definition_authoring_post_runtime_local_lean_compiled": counts.get(
                    "research_agent_runtime_exact_semantic_definition_authoring_post_runtime_local_lean_compiled"
                ),
                "research_agent_runtime_exact_semantic_definition_authoring_post_runtime_proofengineer_state": counts.get(
                    "research_agent_runtime_exact_semantic_definition_authoring_post_runtime_proofengineer_state"
                ),
                "research_agent_runtime_exact_semantic_definition_authoring_post_runtime_proof_evidence_status": counts.get(
                    "research_agent_runtime_exact_semantic_definition_authoring_post_runtime_proof_evidence_status"
                ),
                "research_agent_runtime_generated_code_sandbox_executed": counts.get(
                    "research_agent_runtime_generated_code_sandbox_executed"
                ),
                "research_agent_runtime_generated_simulation_sandbox_executed": counts.get(
                    "research_agent_runtime_generated_simulation_sandbox_executed"
                ),
                "research_agent_runtime_formalizer_lean_candidate_local_lean_checked": counts.get(
                    "research_agent_runtime_formalizer_lean_candidate_local_lean_checked"
                ),
                "research_agent_runtime_formalizer_lean_candidate_local_lean_compiled": counts.get(
                    "research_agent_runtime_formalizer_lean_candidate_local_lean_compiled"
                ),
                "research_agent_runtime_formal_gaps": counts.get(
                    "research_agent_runtime_formal_gaps"
                ),
                "research_agent_runtime_full_frontier_theorem_proved": counts.get(
                    "research_agent_runtime_full_frontier_theorem_proved"
                ),
                "research_agent_runtime_pseudo_formal_block_verifier_component_gate_attached": counts.get(
                    "research_agent_runtime_pseudo_formal_block_verifier_component_gate_attached"
                ),
                "research_agent_runtime_pseudo_formal_block_verifier_component_gate_capability_evidence_ok": counts.get(
                    "research_agent_runtime_pseudo_formal_block_verifier_component_gate_capability_evidence_ok"
                ),
                "research_agent_runtime_pseudo_formal_block_verifier_component_gate_live_generator": counts.get(
                    "research_agent_runtime_pseudo_formal_block_verifier_component_gate_live_generator"
                ),
                "research_agent_runtime_pseudo_formal_block_verifier_component_gate_static_or_fixture_only": counts.get(
                    "research_agent_runtime_pseudo_formal_block_verifier_component_gate_static_or_fixture_only"
                ),
                "research_agent_runtime_pseudo_formal_block_verifier_component_gate_prompt_packets": counts.get(
                    "research_agent_runtime_pseudo_formal_block_verifier_component_gate_prompt_packets"
                ),
                "research_agent_runtime_pseudo_formal_block_verifier_component_gate_valid_responses": counts.get(
                    "research_agent_runtime_pseudo_formal_block_verifier_component_gate_valid_responses"
                ),
                "research_agent_runtime_pseudo_formal_block_verifier_component_gate_runtime_learning_rows": counts.get(
                    "research_agent_runtime_pseudo_formal_block_verifier_component_gate_runtime_learning_rows"
                ),
                "research_agent_runtime_pseudo_formal_block_verifier_component_gate_source_runtime_learning_jsonl_paths": counts.get(
                    "research_agent_runtime_pseudo_formal_block_verifier_component_gate_source_runtime_learning_jsonl_paths"
                ),
                "research_agent_runtime_pseudo_formal_block_verifier_component_gate_source_runtime_learning_jsonl_path_count": counts.get(
                    "research_agent_runtime_pseudo_formal_block_verifier_component_gate_source_runtime_learning_jsonl_path_count"
                ),
                "research_agent_runtime_pseudo_formal_block_verifier_component_gate_source_runtime_learning_lineage_reference_dir": counts.get(
                    "research_agent_runtime_pseudo_formal_block_verifier_component_gate_source_runtime_learning_lineage_reference_dir"
                ),
                "research_agent_runtime_pseudo_formal_block_verifier_component_gate_source_runtime_learning_lineage_ok": counts.get(
                    "research_agent_runtime_pseudo_formal_block_verifier_component_gate_source_runtime_learning_lineage_ok"
                ),
                "research_agent_runtime_pseudo_formal_block_verifier_component_gate_accepted_blocks": counts.get(
                    "research_agent_runtime_pseudo_formal_block_verifier_component_gate_accepted_blocks"
                ),
                "research_agent_runtime_pseudo_formal_block_verifier_component_gate_failed_blocks": counts.get(
                    "research_agent_runtime_pseudo_formal_block_verifier_component_gate_failed_blocks"
                ),
                "research_agent_runtime_pseudo_formal_block_verifier_component_gate_provider": counts.get(
                    "research_agent_runtime_pseudo_formal_block_verifier_component_gate_provider"
                ),
                "research_agent_runtime_pseudo_formal_block_verifier_component_gate_backend_provider": counts.get(
                    "research_agent_runtime_pseudo_formal_block_verifier_component_gate_backend_provider"
                ),
                "research_agent_runtime_pseudo_formal_block_verifier_component_gate_manifest_path": counts.get(
                    "research_agent_runtime_pseudo_formal_block_verifier_component_gate_manifest_path"
                ),
                "research_agent_runtime_formalizer_pseudo_formal_packet_component_gate_attached": counts.get(
                    "research_agent_runtime_formalizer_pseudo_formal_packet_component_gate_attached",
                    runtime_formalizer_pf_packet_component_exercised,
                ),
                "research_agent_runtime_formalizer_pseudo_formal_packet_component_gate_capability_evidence_ok": counts.get(
                    "research_agent_runtime_formalizer_pseudo_formal_packet_component_gate_capability_evidence_ok",
                    runtime_formalizer_pf_packet_component_capability_evidence_ok,
                ),
                "research_agent_runtime_formalizer_pseudo_formal_packet_component_gate_live_generator": counts.get(
                    "research_agent_runtime_formalizer_pseudo_formal_packet_component_gate_live_generator"
                ),
                "research_agent_runtime_formalizer_pseudo_formal_packet_component_gate_static_or_fixture_only": counts.get(
                    "research_agent_runtime_formalizer_pseudo_formal_packet_component_gate_static_or_fixture_only"
                ),
                "research_agent_runtime_formalizer_pseudo_formal_packet_component_gate_pseudo_formal_packets": counts.get(
                    "research_agent_runtime_formalizer_pseudo_formal_packet_component_gate_pseudo_formal_packets",
                    runtime_formalizer_pf_packet_component_packets,
                ),
                "research_agent_runtime_formalizer_pseudo_formal_packet_component_gate_work_order_rows": counts.get(
                    "research_agent_runtime_formalizer_pseudo_formal_packet_component_gate_work_order_rows"
                ),
                "research_agent_runtime_formalizer_pseudo_formal_packet_component_gate_routable_work_order_rows": counts.get(
                    "research_agent_runtime_formalizer_pseudo_formal_packet_component_gate_routable_work_order_rows",
                    runtime_formalizer_pf_packet_component_routable_rows,
                ),
                "research_agent_runtime_formalizer_pseudo_formal_packet_component_gate_routable_row_kinds": counts.get(
                    "research_agent_runtime_formalizer_pseudo_formal_packet_component_gate_routable_row_kinds"
                ),
                "research_agent_runtime_formalizer_pseudo_formal_packet_component_gate_routable_target_lanes": counts.get(
                    "research_agent_runtime_formalizer_pseudo_formal_packet_component_gate_routable_target_lanes",
                    sorted(runtime_formalizer_pf_packet_component_target_lanes),
                ),
                "research_agent_runtime_formalizer_pseudo_formal_packet_component_gate_nonproof_boundary_preserved": counts.get(
                    "research_agent_runtime_formalizer_pseudo_formal_packet_component_gate_nonproof_boundary_preserved",
                    runtime_formalizer_pf_packet_component_nonproof_boundary,
                ),
                "research_agent_runtime_formalizer_pseudo_formal_packet_component_gate_raw_model_output_written": counts.get(
                    "research_agent_runtime_formalizer_pseudo_formal_packet_component_gate_raw_model_output_written",
                    runtime_formalizer_pf_packet_component_raw_output_written,
                ),
                "research_agent_runtime_formalizer_pseudo_formal_packet_component_gate_exact_semantic_definition_lane_present": counts.get(
                    "research_agent_runtime_formalizer_pseudo_formal_packet_component_gate_exact_semantic_definition_lane_present",
                    runtime_formalizer_pf_packet_component_exact_lane_present,
                ),
                "research_agent_runtime_formalizer_pseudo_formal_packet_component_gate_proof_evidence_status_ok": counts.get(
                    "research_agent_runtime_formalizer_pseudo_formal_packet_component_gate_proof_evidence_status_ok",
                    runtime_formalizer_pf_packet_component_proof_evidence_status_ok,
                ),
                "research_agent_runtime_formalizer_pseudo_formal_packet_component_gate_no_theorem_proof_claim": counts.get(
                    "research_agent_runtime_formalizer_pseudo_formal_packet_component_gate_no_theorem_proof_claim",
                    runtime_formalizer_pf_packet_component_no_theorem_proof_claim,
                ),
                "research_agent_runtime_formalizer_pseudo_formal_packet_component_gate_attachment_gate_recomputed": counts.get(
                    "research_agent_runtime_formalizer_pseudo_formal_packet_component_gate_attachment_gate_recomputed",
                    runtime_formalizer_pf_packet_component_attachment_gate_recomputed,
                ),
                "research_agent_runtime_formalizer_pseudo_formal_packet_component_gate_learning_consumed": counts.get(
                    "research_agent_runtime_formalizer_pseudo_formal_packet_component_gate_learning_consumed",
                    runtime_formalizer_pf_packet_component_learning_consumed,
                ),
                "research_agent_runtime_formalizer_pseudo_formal_packet_component_gate_learning_rows": counts.get(
                    "research_agent_runtime_formalizer_pseudo_formal_packet_component_gate_learning_rows",
                    runtime_formalizer_pf_packet_component_learning_rows,
                ),
                "research_agent_runtime_formalizer_pseudo_formal_packet_component_gate_learning_consumed_rows": counts.get(
                    "research_agent_runtime_formalizer_pseudo_formal_packet_component_gate_learning_consumed_rows",
                    runtime_formalizer_pf_packet_component_learning_consumed_rows,
                ),
                "research_agent_runtime_formalizer_pseudo_formal_packet_component_gate_provider": counts.get(
                    "research_agent_runtime_formalizer_pseudo_formal_packet_component_gate_provider"
                ),
                "research_agent_runtime_formalizer_pseudo_formal_packet_component_gate_backend_provider": counts.get(
                    "research_agent_runtime_formalizer_pseudo_formal_packet_component_gate_backend_provider"
                ),
                "research_agent_runtime_capability_gaps": counts.get(
                    "research_agent_runtime_capability_gaps"
                ),
                "research_agent_runtime_capability_gap_routing_input_rows": counts.get(
                    "research_agent_runtime_capability_gap_routing_input_rows"
                ),
                "research_agent_runtime_capability_gap_routing_input_rows_seen": counts.get(
                    "research_agent_runtime_capability_gap_routing_input_rows_seen"
                ),
                "research_agent_runtime_capability_gap_routing_input_retention_policy": counts.get(
                    "research_agent_runtime_capability_gap_routing_input_retention_policy"
                ),
                "research_agent_runtime_capability_gap_routing_input_retention_selection_counts": counts.get(
                    "research_agent_runtime_capability_gap_routing_input_retention_selection_counts"
                ),
                "research_agent_runtime_capability_gap_routing_input_requirement_ids": counts.get(
                    "research_agent_runtime_capability_gap_routing_input_requirement_ids"
                ),
                "research_agent_runtime_capability_gap_routing_input_priority_pinned_requirement_ids": counts.get(
                    "research_agent_runtime_capability_gap_routing_input_priority_pinned_requirement_ids"
                ),
                "research_agent_runtime_capability_gap_routing_input_owner_subsystems": counts.get(
                    "research_agent_runtime_capability_gap_routing_input_owner_subsystems"
                ),
                "research_agent_runtime_capability_gap_routing_followup_commands": counts.get(
                    "research_agent_runtime_capability_gap_routing_followup_commands"
                ),
                "research_agent_runtime_capability_gap_routing_input_rows_missing_retention_selection": counts.get(
                    "research_agent_runtime_capability_gap_routing_input_rows_missing_retention_selection"
                ),
                "research_agent_runtime_capability_gap_routing_input_rows_missing_retention_selection_boundary": counts.get(
                    "research_agent_runtime_capability_gap_routing_input_rows_missing_retention_selection_boundary"
                ),
                "research_agent_runtime_architect_deferred_meta_capability_gaps": counts.get(
                    "research_agent_runtime_architect_deferred_meta_capability_gaps"
                ),
                "research_agent_runtime_architect_deferred_meta_capability_gap_owners": counts.get(
                    "research_agent_runtime_architect_deferred_meta_capability_gap_owners"
                ),
                "research_agent_runtime_architect_deferred_meta_capability_gap_requirement_ids": counts.get(
                    "research_agent_runtime_architect_deferred_meta_capability_gap_requirement_ids"
                ),
                "research_agent_runtime_architect_deferred_meta_capability_gaps_visible": counts.get(
                    "research_agent_runtime_architect_deferred_meta_capability_gaps_visible"
                ),
                "research_agent_runtime_architect_deferred_meta_capability_gaps_resolved": counts.get(
                    "research_agent_runtime_architect_deferred_meta_capability_gaps_resolved"
                ),
                "research_agent_runtime_architect_deferred_meta_capability_gap_resolution_replay_priority_pinned": (
                    runtime_deferred_meta_gap_resolution_replay_priority_pinned
                ),
                "research_agent_runtime_architect_deferred_meta_capability_gap_resolution_replay_priority_pinned_evidence": counts.get(
                    "research_agent_runtime_architect_deferred_meta_capability_gap_resolution_replay_priority_pinned_evidence"
                ),
                "research_agent_runtime_architect_deferred_meta_capability_gap_resolution_replay_priority_pinned_blocker": counts.get(
                    "research_agent_runtime_architect_deferred_meta_capability_gap_resolution_replay_priority_pinned_blocker"
                ),
                "research_agent_runtime_cross_task_theorem_family_rows": counts.get(
                    "research_agent_runtime_cross_task_theorem_family_rows"
                ),
                "research_agent_runtime_cross_task_theorem_family_rows_with_explicit_family": counts.get(
                    "research_agent_runtime_cross_task_theorem_family_rows_with_explicit_family"
                ),
                "research_agent_runtime_cross_task_theorem_family_rows_with_target_bound_kernel": counts.get(
                    "research_agent_runtime_cross_task_theorem_family_rows_with_target_bound_kernel"
                ),
                "research_agent_runtime_cross_task_theorem_family_rows_with_open_formal_gaps": counts.get(
                    "research_agent_runtime_cross_task_theorem_family_rows_with_open_formal_gaps"
                ),
                "research_agent_runtime_pseudo_formal_block_routing_contract_complete": counts.get(
                    "research_agent_runtime_pseudo_formal_block_routing_contract_complete"
                ),
                "research_agent_runtime_pseudo_formal_block_routing_rows": counts.get(
                    "research_agent_runtime_pseudo_formal_block_routing_rows"
                ),
                "research_agent_runtime_pseudo_formal_block_routing_effective_rows": counts.get(
                    "research_agent_runtime_pseudo_formal_block_routing_effective_rows"
                ),
                "research_agent_runtime_pseudo_formal_block_routing_diagnostic_rows": counts.get(
                    "research_agent_runtime_pseudo_formal_block_routing_diagnostic_rows"
                ),
                "research_agent_runtime_pseudo_formal_block_routing_row_kinds": counts.get(
                    "research_agent_runtime_pseudo_formal_block_routing_row_kinds"
                ),
                "research_agent_runtime_pseudo_formal_block_routing_diagnostic_row_kinds": counts.get(
                    "research_agent_runtime_pseudo_formal_block_routing_diagnostic_row_kinds"
                ),
                "research_agent_runtime_pseudo_formal_block_routing_effective_target_lanes": counts.get(
                    "research_agent_runtime_pseudo_formal_block_routing_effective_target_lanes"
                ),
                "research_agent_runtime_pseudo_formal_block_routing_diagnostic_target_lanes": counts.get(
                    "research_agent_runtime_pseudo_formal_block_routing_diagnostic_target_lanes"
                ),
                "research_agent_runtime_pseudo_formalization_required_formalization_manifests": counts.get(
                    "research_agent_runtime_pseudo_formalization_required_formalization_manifests"
                ),
                "research_agent_runtime_pseudo_formalization_required_missing_routing_rows": counts.get(
                    "research_agent_runtime_pseudo_formalization_required_missing_routing_rows"
                ),
                "research_agent_runtime_pseudo_formalization_required_manifest_ids": counts.get(
                    "research_agent_runtime_pseudo_formalization_required_manifest_ids"
                ),
                "research_agent_runtime_pseudo_formalization_required_missing_routing_manifest_ids": counts.get(
                    "research_agent_runtime_pseudo_formalization_required_missing_routing_manifest_ids"
                ),
                "research_agent_runtime_pseudo_formalization_routed_manifests": counts.get(
                    "research_agent_runtime_pseudo_formalization_routed_manifests"
                ),
                "research_agent_runtime_pseudo_formalization_effective_routed_manifests": counts.get(
                    "research_agent_runtime_pseudo_formalization_effective_routed_manifests"
                ),
                "research_agent_runtime_pseudo_formalization_routed_manifest_ids": counts.get(
                    "research_agent_runtime_pseudo_formalization_routed_manifest_ids"
                ),
                "research_agent_runtime_pseudo_formalization_effective_routed_manifest_ids": counts.get(
                    "research_agent_runtime_pseudo_formalization_effective_routed_manifest_ids"
                ),
                "research_agent_runtime_pseudo_formal_block_routing_rows_missing_method_lineage": counts.get(
                    "research_agent_runtime_pseudo_formal_block_routing_rows_missing_method_lineage"
                ),
                "research_agent_runtime_pseudo_formal_block_routing_rows_missing_scope_parent": counts.get(
                    "research_agent_runtime_pseudo_formal_block_routing_rows_missing_scope_parent"
                ),
                "research_agent_runtime_pseudo_formal_block_routing_rows_invalid_scope_parent": counts.get(
                    "research_agent_runtime_pseudo_formal_block_routing_rows_invalid_scope_parent"
                ),
                "research_agent_runtime_pseudo_formal_block_routing_rows_missing_inherited_scope": counts.get(
                    "research_agent_runtime_pseudo_formal_block_routing_rows_missing_inherited_scope"
                ),
                "research_agent_runtime_pseudo_formal_block_routing_rows_missing_row_kind": counts.get(
                    "research_agent_runtime_pseudo_formal_block_routing_rows_missing_row_kind"
                ),
                "research_agent_runtime_pseudo_formal_block_routing_rows_missing_or_wrong_nonproof_boundary": counts.get(
                    "research_agent_runtime_pseudo_formal_block_routing_rows_missing_or_wrong_nonproof_boundary"
                ),
                "research_agent_runtime_pseudo_formal_block_routing_issues": counts.get(
                    "research_agent_runtime_pseudo_formal_block_routing_issues"
                ),
                "research_agent_runtime_pseudo_formal_semantic_primitive_work_orders": counts.get(
                    "research_agent_runtime_pseudo_formal_semantic_primitive_work_orders"
                ),
                "research_agent_runtime_pseudo_formal_semantic_primitives_reach_source_semantic_bridge": counts.get(
                    "research_agent_runtime_pseudo_formal_semantic_primitives_reach_source_semantic_bridge"
                ),
                "research_agent_runtime_pseudo_formal_exact_semantic_definition_work_orders": counts.get(
                    "research_agent_runtime_pseudo_formal_exact_semantic_definition_work_orders"
                ),
                "research_agent_runtime_pseudo_formal_exact_semantic_definition_lean_environment_repair_tasks": counts.get(
                    "research_agent_runtime_pseudo_formal_exact_semantic_definition_lean_environment_repair_tasks"
                ),
                "research_agent_runtime_pseudo_formal_exact_semantic_definition_lean_environment_repair_results": counts.get(
                    "research_agent_runtime_pseudo_formal_exact_semantic_definition_lean_environment_repair_results"
                ),
                "research_agent_runtime_pseudo_formal_late_exact_semantic_definition_lean_environment_repair_tasks": counts.get(
                    "research_agent_runtime_pseudo_formal_late_exact_semantic_definition_lean_environment_repair_tasks"
                ),
                "research_agent_runtime_pseudo_formal_late_exact_semantic_definition_lean_environment_repair_results": counts.get(
                    "research_agent_runtime_pseudo_formal_late_exact_semantic_definition_lean_environment_repair_results"
                ),
                "research_agent_runtime_pseudo_formal_exact_semantic_definition_lean_environment_repair_ready_for_proof_body": counts.get(
                    "research_agent_runtime_pseudo_formal_exact_semantic_definition_lean_environment_repair_ready_for_proof_body"
                ),
                "research_agent_runtime_pseudo_formal_late_exact_semantic_definition_lean_environment_repair_ready_for_proof_body": counts.get(
                    "research_agent_runtime_pseudo_formal_late_exact_semantic_definition_lean_environment_repair_ready_for_proof_body"
                ),
                "research_agent_runtime_pseudo_formal_exact_semantic_definitions_reach_exact_definition_source_lookup": counts.get(
                    "research_agent_runtime_pseudo_formal_exact_semantic_definitions_reach_exact_definition_source_lookup"
                ),
                "research_agent_runtime_source_semantic_proofengineer_bridge_requested": counts.get(
                    "research_agent_runtime_source_semantic_proofengineer_bridge_requested"
                ),
                "research_agent_runtime_source_semantic_proofengineer_bridge_ran": counts.get(
                    "research_agent_runtime_source_semantic_proofengineer_bridge_ran"
                ),
                "research_agent_runtime_source_semantic_proofengineer_bridge_proof_evidence_status": counts.get(
                    "research_agent_runtime_source_semantic_proofengineer_bridge_proof_evidence_status"
                ),
                "research_agent_runtime_source_theorem_formal_environment_proof_body_executor_ran": counts.get(
                    "research_agent_runtime_source_theorem_formal_environment_proof_body_executor_ran"
                ),
                "research_agent_runtime_source_theorem_formal_environment_proof_body_executor_local_lean_requested": counts.get(
                    "research_agent_runtime_source_theorem_formal_environment_proof_body_executor_local_lean_requested"
                ),
                "research_agent_runtime_source_theorem_formal_environment_proof_body_executor_n_result_rows": counts.get(
                    "research_agent_runtime_source_theorem_formal_environment_proof_body_executor_n_result_rows"
                ),
                "research_agent_runtime_source_theorem_formal_environment_proof_body_executor_n_local_lean_checked": counts.get(
                    "research_agent_runtime_source_theorem_formal_environment_proof_body_executor_n_local_lean_checked"
                ),
                "research_agent_runtime_source_theorem_formal_environment_proof_body_executor_n_source_theorem_kernel_verified": counts.get(
                    "research_agent_runtime_source_theorem_formal_environment_proof_body_executor_n_source_theorem_kernel_verified"
                ),
                "research_agent_runtime_source_theorem_exact_proof_body_repair_executor_ran": counts.get(
                    "research_agent_runtime_source_theorem_exact_proof_body_repair_executor_ran"
                ),
                "research_agent_runtime_source_theorem_exact_proof_body_repair_executor_n_result_rows": counts.get(
                    "research_agent_runtime_source_theorem_exact_proof_body_repair_executor_n_result_rows"
                ),
                "research_agent_runtime_source_theorem_exact_proof_body_repair_executor_n_local_lean_checked": counts.get(
                    "research_agent_runtime_source_theorem_exact_proof_body_repair_executor_n_local_lean_checked"
                ),
                "research_agent_runtime_source_theorem_exact_proof_body_repair_executor_n_proof_body_goal_reached": counts.get(
                    "research_agent_runtime_source_theorem_exact_proof_body_repair_executor_n_proof_body_goal_reached"
                ),
                "research_agent_runtime_source_theorem_exact_proof_body_repair_executor_n_proof_body_goal_reached_with_semantic_blockers": counts.get(
                    "research_agent_runtime_source_theorem_exact_proof_body_repair_executor_n_proof_body_goal_reached_with_semantic_blockers"
                ),
                "research_agent_runtime_source_theorem_exact_proof_body_repair_executor_n_source_theorem_kernel_verified": counts.get(
                    "research_agent_runtime_source_theorem_exact_proof_body_repair_executor_n_source_theorem_kernel_verified"
                ),
                "research_agent_runtime_source_theorem_exact_semantic_definition_typechecked_review_verifier_approved_proof_body_recheck_executor_ran": counts.get(
                    "research_agent_runtime_source_theorem_exact_semantic_definition_typechecked_review_verifier_approved_proof_body_recheck_executor_ran"
                ),
                "research_agent_runtime_source_theorem_exact_semantic_definition_typechecked_review_verifier_approved_proof_body_recheck_executor_n_result_rows": counts.get(
                    "research_agent_runtime_source_theorem_exact_semantic_definition_typechecked_review_verifier_approved_proof_body_recheck_executor_n_result_rows"
                ),
                "research_agent_runtime_source_theorem_exact_semantic_definition_typechecked_review_verifier_approved_proof_body_recheck_executor_n_source_theorem_kernel_verified": counts.get(
                    "research_agent_runtime_source_theorem_exact_semantic_definition_typechecked_review_verifier_approved_proof_body_recheck_executor_n_source_theorem_kernel_verified"
                ),
                "research_agent_runtime_source_theorem_proof_body_result_row_count": counts.get(
                    "research_agent_runtime_source_theorem_proof_body_result_row_count"
                ),
                "research_agent_runtime_source_theorem_proof_body_goal_reached_evidence_count": counts.get(
                    "research_agent_runtime_source_theorem_proof_body_goal_reached_evidence_count"
                ),
                "research_agent_runtime_source_theorem_proof_body_goal_reached_with_semantic_blockers": counts.get(
                    "research_agent_runtime_source_theorem_proof_body_goal_reached_with_semantic_blockers"
                ),
                "research_agent_runtime_source_theorem_proof_body_authoritative_goal_reached": runtime_source_theorem_proof_body_authoritative_goal_reached,
                "research_agent_runtime_source_theorem_signature_probe_reached_proof_body_scorecard_present": runtime_source_theorem_signature_probe_scorecard_present,
                "research_agent_runtime_source_theorem_signature_probe_reached_proof_body_scorecard_ok": runtime_source_theorem_signature_probe_scorecard_ok,
                "research_agent_runtime_source_theorem_signature_probe_reached_proof_body_scorecard_evidence": runtime_source_theorem_signature_probe_scorecard_evidence,
                "research_agent_runtime_source_theorem_signature_probe_reached_proof_body_scorecard_blocker": runtime_source_theorem_signature_probe_scorecard_blocker,
                "research_agent_runtime_source_theorem_proof_body_semantic_review_blockers_authoritative_ok": runtime_source_theorem_semantic_blockers_authoritative_ok,
                "research_agent_runtime_source_theorem_proof_body_semantic_review_blockers_not_hidden_scorecard_present": runtime_source_theorem_semantic_blockers_scorecard_present,
                "research_agent_runtime_source_theorem_proof_body_semantic_review_blockers_not_hidden_scorecard_ok": runtime_source_theorem_semantic_blockers_scorecard_ok,
                "research_agent_runtime_source_theorem_proof_body_semantic_review_blockers_not_hidden_scorecard_evidence": runtime_source_theorem_semantic_blockers_scorecard_evidence,
                "research_agent_runtime_source_theorem_proof_body_semantic_review_blockers_not_hidden_scorecard_blocker": runtime_source_theorem_semantic_blockers_scorecard_blocker,
                "research_agent_runtime_source_theorem_kernel_verified_count": counts.get(
                    "research_agent_runtime_source_theorem_kernel_verified_count"
                ),
                "research_agent_runtime_source_theorem_proof_body_raw_executor_ran": runtime_source_theorem_proof_body_executor_ran,
                "research_agent_runtime_source_theorem_proof_body_authoritative_executor_ran": runtime_source_theorem_proof_body_authoritative_executor_ran,
                "research_agent_runtime_source_theorem_proof_body_executor_ran_scorecard_present": runtime_source_theorem_proof_body_executor_scorecard_present,
                "research_agent_runtime_source_theorem_proof_body_executor_ran_scorecard_ok": runtime_source_theorem_proof_body_executor_scorecard_ok,
                "research_agent_runtime_source_theorem_proof_body_executor_ran_scorecard_evidence": runtime_source_theorem_proof_body_executor_scorecard_evidence,
                "research_agent_runtime_source_theorem_proof_body_executor_ran_scorecard_blocker": runtime_source_theorem_proof_body_executor_scorecard_blocker,
                "research_agent_runtime_source_theorem_proof_body_effective_result_rows": runtime_source_theorem_proof_body_result_rows,
                "research_agent_runtime_source_theorem_proof_body_effective_local_lean_requested": runtime_source_theorem_formal_environment_proof_body_local_lean_requested,
                "research_agent_runtime_source_theorem_proof_body_effective_local_lean_checked": runtime_source_theorem_proof_body_local_lean_checked,
                "research_agent_runtime_source_theorem_proof_body_effective_goal_reached": runtime_source_theorem_proof_body_goal_reached,
                "research_agent_runtime_source_theorem_proof_body_effective_goal_reached_with_semantic_blockers": runtime_source_theorem_proof_body_goal_reached_with_semantic_blockers,
                "research_agent_runtime_source_theorem_effective_kernel_verified": runtime_source_theorem_kernel_verified,
                "research_agent_runtime_source_theorem_proof_body_aggregate_local_lean_or_kernel_ok": runtime_source_theorem_proof_body_aggregate_local_lean_gate_ok,
                "research_agent_runtime_source_theorem_proof_body_authoritative_local_lean_gate_ok": runtime_source_theorem_proof_body_authoritative_local_lean_gate_ok,
                "research_agent_runtime_source_theorem_proof_body_local_lean_gate_scorecard_present": runtime_source_theorem_local_lean_gate_scorecard_present,
                "research_agent_runtime_source_theorem_proof_body_local_lean_gate_scorecard_ok": runtime_source_theorem_local_lean_gate_scorecard_ok,
                "research_agent_runtime_source_theorem_proof_body_local_lean_gate_scorecard_evidence": runtime_source_theorem_local_lean_gate_scorecard_evidence,
                "research_agent_runtime_source_theorem_proof_body_local_lean_gate_scorecard_blocker": runtime_source_theorem_local_lean_gate_scorecard_blocker,
                "research_agent_runtime_source_theorem_proof_body_same_lane_local_lean_or_kernel_ok": runtime_source_theorem_proof_body_same_lane_gate_ok,
                "research_agent_runtime_source_theorem_proof_body_authoritative_same_lane_local_lean_or_kernel_ok": runtime_source_theorem_proof_body_authoritative_same_lane_gate_ok,
                "research_agent_runtime_source_theorem_proof_body_same_lane_verifier_evidence_present": runtime_source_theorem_proof_body_same_lane_scorecard_present,
                "research_agent_runtime_source_theorem_proof_body_same_lane_verifier_evidence": runtime_source_theorem_proof_body_same_lane_scorecard_ok,
                "research_agent_runtime_source_theorem_proof_body_same_lane_verifier_scorecard_evidence": runtime_source_theorem_proof_body_same_lane_scorecard_evidence,
                "research_agent_runtime_source_theorem_proof_body_same_lane_verifier_scorecard_blocker": runtime_source_theorem_proof_body_same_lane_scorecard_blocker,
                "research_agent_runtime_live_lean_lsp_mcp_called_scorecard_present": runtime_live_lean_lsp_mcp_scorecard_present,
                "research_agent_runtime_live_lean_lsp_mcp_called_scorecard_ok": runtime_live_lean_lsp_mcp_scorecard_ok,
                "research_agent_runtime_live_lean_lsp_mcp_called_scorecard_evidence": runtime_live_lean_lsp_mcp_scorecard_evidence,
                "research_agent_runtime_live_lean_lsp_mcp_called_scorecard_blocker": runtime_live_lean_lsp_mcp_scorecard_blocker,
                "research_agent_runtime_real_kernel_subclaim_verified_scorecard_present": runtime_real_kernel_subclaim_scorecard_present,
                "research_agent_runtime_real_kernel_subclaim_verified_scorecard_ok": runtime_real_kernel_subclaim_scorecard_ok,
                "research_agent_runtime_real_kernel_subclaim_verified_scorecard_evidence": runtime_real_kernel_subclaim_scorecard_evidence,
                "research_agent_runtime_real_kernel_subclaim_verified_scorecard_blocker": runtime_real_kernel_subclaim_scorecard_blocker,
                "research_agent_runtime_full_frontier_theorem_kernel_proved_scorecard_present": runtime_full_frontier_theorem_kernel_scorecard_present,
                "research_agent_runtime_full_frontier_theorem_kernel_proved_scorecard_ok": runtime_full_frontier_theorem_kernel_scorecard_ok,
                "research_agent_runtime_full_frontier_theorem_kernel_proved_scorecard_evidence": runtime_full_frontier_theorem_kernel_scorecard_evidence,
                "research_agent_runtime_full_frontier_theorem_kernel_proved_scorecard_blocker": runtime_full_frontier_theorem_kernel_scorecard_blocker,
                "research_agent_runtime_source_theorem_formal_environment_proof_body_lane_ok": runtime_source_theorem_formal_environment_proof_body_lane_ok,
                "research_agent_runtime_source_theorem_exact_proof_body_repair_lane_ok": runtime_source_theorem_exact_proof_body_repair_lane_ok,
                "research_agent_runtime_source_theorem_approved_proof_body_recheck_lane_ok": runtime_source_theorem_approved_proof_body_recheck_lane_ok,
                "research_agent_runtime_formal_gap_planner_handoff_rows": counts.get(
                    "research_agent_runtime_formal_gap_planner_handoff_rows"
                ),
                "research_agent_runtime_formal_gap_planner_handoff_rows_missing_execution_context": counts.get(
                    "research_agent_runtime_formal_gap_planner_handoff_rows_missing_execution_context"
                ),
                "research_agent_runtime_formal_gap_planner_executable_handoff_context_complete": counts.get(
                    "research_agent_runtime_formal_gap_planner_executable_handoff_context_complete"
                ),
                "research_agent_runtime_formal_gap_planner_live_route_planner_followthrough": counts.get(
                    "research_agent_runtime_formal_gap_planner_live_route_planner_followthrough"
                ),
                "research_agent_runtime_formal_gap_planner_live_route_planner_invocations": counts.get(
                    "research_agent_runtime_formal_gap_planner_live_route_planner_invocations"
                ),
                "research_agent_runtime_formal_gap_planner_live_route_planner_response_contract_ok": counts.get(
                    "research_agent_runtime_formal_gap_planner_live_route_planner_response_contract_ok"
                ),
                "research_agent_runtime_formal_gap_planner_live_route_planner_target_prover_replay_all_ok": counts.get(
                    "research_agent_runtime_formal_gap_planner_live_route_planner_target_prover_replay_all_ok"
                ),
                "research_agent_runtime_formal_gap_planner_target_prover_replay_route_revision_proposals": counts.get(
                    "research_agent_runtime_formal_gap_planner_target_prover_replay_route_revision_proposals"
                ),
                "research_agent_runtime_formal_gap_planner_target_prover_replay_route_revision_complete_feedback_proposal_ids": counts.get(
                    "research_agent_runtime_formal_gap_planner_target_prover_replay_route_revision_complete_feedback_proposal_ids"
                ),
            },
            honesty_boundary=(
                "This is the integrated live AgentRuntime gate. Component gates "
                "S10/S11/S12 do not imply this suite passes. Static/no-Architect/"
                "template-only runs cannot count, and this suite still separates "
                "runtime capability from full theorem proof. Pseudo-formal/"
                "block-verification rows are bridge-verification and routing "
                "feedback only; when emitted, they must preserve PF+BV method "
                "lineage, attach the live PF/BV component gate in-loop, reach a "
                "source-semantic ProofEngineer bridge, and "
                "retain the non-proof boundary. Formalizer PF/BV packet-emission "
                "gates are source-anchored decomposition/routing evidence only "
                "and must reach exact semantic-definition lanes before any proof "
                "claim. Formal-gap planner rows are "
                "route-planning feedback; when staged they must preserve "
                "executable context and route-revision feedback, not proof "
                "evidence. Post-runtime exact semantic-definition attachments "
                "are lineage-checked live handoff and local Lean diagnostic "
                "evidence only; local Lean failure is a repair signal, not "
                "source theorem proof. Exact source-theorem proof-body executor "
                "rows are proof-search feedback until local Lean/AXLE checks them, "
                "and only source-theorem kernel verification closes the proof "
                "claim."
            ),
            issues=tuple(s13_issues),
        ),
    ]
    return tuple(rows)


def _top_actions(
    suite_rows: tuple[BenchmarkSuiteGuidanceRow, ...],
    counts: Mapping[str, Any],
) -> list[dict[str, object]]:
    rows_by_id = {row.suite_id: row for row in suite_rows}
    s13_followup_command_rows = _command_rows(
        counts.get(
            "research_agent_runtime_capability_gap_routing_followup_commands",
            [],
        )
    )
    s13_followup_commands = _command_strings(s13_followup_command_rows)
    proof_search_frontier_delta = _int(counts.get("proof_search_retrieval_ablation_candidate_delta")) + _int(
        counts.get("proof_search_retrieval_no_registered_ablation_candidate_delta")
    )
    proof_kernel_evidence = (
        _int(counts.get("proofs_kernel_verified"))
        + _int(counts.get("proof_search_kernel_verified"))
        + _int(counts.get("proof_search_kernel_rerun_local_lean_verified"))
    )
    actions = [
        {
            "rank": 1,
            "owner_suite": "S4_formal_primitive_ladder",
            "action": "Close or upgrade the top formal primitives into reusable AXLE/Lean proof obligations.",
            "why": f"{_int(counts.get('missing_formal_primitives'))} missing formal primitives remain; this is the main theorem-capacity bottleneck.",
            "success_metric": "missing_formal_primitives decreases or proof_bank_expansion_bridge_ready increases with kernel-verified obligations.",
        },
        {
            "rank": 2,
            "owner_suite": "S3_frontier_blind_theory_target",
            "action": "Run and gate all-60 frontier theory-target scoring with per-topic triage, not only the release smoke subset.",
            "why": "Frontier routing is saturated, but target recovery remains below the next 90% milestone and the smoke set is smaller than the full benchmark.",
            "success_metric": "all-60 expected-result coverage reaches at least 90% while formal gaps remain explicit.",
        },
        {
            "rank": 3,
            "owner_suite": "S5_proof_bank_and_search/S7_feedback_loop_repair",
            "action": (
                "Rerun hard RAG/proof-search candidates through AXLE/local Lean and seed feedback-loop failures where repair must change a decision."
                if proof_kernel_evidence == 0
                else "Add harder RAG/proof-search and seeded feedback-loop failures where stronger retrieval or repair must change a decision."
            ),
            "why": (
                "Search/retrieval artifacts are present, but the current audit has no proof-bank or proof-search kernel evidence; "
                "algorithm repair also has no promotion-ready patch."
                if proof_kernel_evidence == 0
                else (
                    "The current proof-search/RAG ablations still show no candidate-frontier lift and "
                    "algorithm repair has no promotion-ready patch."
                    if proof_search_frontier_delta == 0
                    else (
                        f"Proof-search/RAG hard-mode candidate-frontier lift is {proof_search_frontier_delta}; "
                        "the next bottleneck is turning that search signal into verifier-checked harder obligations, "
                        "while algorithm repair still has no promotion-ready patch."
                    )
                )
            ),
            "success_metric": (
                "proof_search_kernel_verified, proof_search_kernel_rerun_local_lean_verified, or proofs_kernel_verified becomes positive under AXLE/local Lean, and at least one seeded simulation/proof failure yields a verified changed trace."
                if proof_kernel_evidence == 0
                else "dependency-graph retrieval improves candidate frontier or solved count on hard obligations, and at least one seeded simulation/proof failure yields a verified changed trace."
            ),
        },
    ]
    if (
        rows_by_id.get("S13_live_integrated_agent_runtime_capability", None) is not None
        and rows_by_id["S13_live_integrated_agent_runtime_capability"].status != "OK"
    ):
        s13_action: dict[str, object] = {
            "rank": len(actions) + 1,
            "owner_suite": "S13_live_integrated_agent_runtime_capability",
            "action": "Run one integrated live AgentRuntime capability gate with Architect enabled, generated algorithm/simulation repair, Formalizer local Lean feedback, attached Formalizer PF/BV packet-emission calibration, attached PF/BV BlockVerifier calibration, aggregate exact semantic-definition authoring, and internal ProofEngineer handoffs in the same run.",
            "why": "S10/S11/S11c/S11b/S12 prove component capabilities separately, but they do not prove the full Claude/OpenAI-driven AI Statistician loop works end to end without static/no-Architect/template-only substitution or staged-only semantic authoring.",
            "success_metric": "research_agent_runtime_capability_ready_for_full_ai_statistician=true with zero static providers, ArchitectCoordinator enabled, generated code and simulation repair evidence, Formalizer local Lean feedback, attached Formalizer PF/BV packet-emission evidence with capability_evidence_ok=true, pseudo_formal_packets>0, routable_work_order_rows>0, source_theorem_exact_semantic_definition in target lanes, exact_semantic_definition_lane_present=true, nonproof_boundary_preserved=true, proof_evidence_status_ok=true, no_theorem_proof_claim=true, raw_model_output_written=false, attachment_gate_recomputed=true, and runtime_formalizer_pseudo_formal_packet_component_gate_learning_consumed=true with consumed_rows>0, attached internal_pseudo_formal_block_verifier_eval_capability_evidence_ok=true with prompt_packets>0, valid_responses>0, and runtime_learning_rows>0 from a live backend, zero unresolved AgentRuntime/Architect deferred meta capability gaps with owner/requirement telemetry if any are detected, architect_deferred_meta_capability_gaps_resolved priority-pinned in capability-gap replay whenever such a gap remains open, aggregate primary/retry/late/post-runtime exact semantic-definition authoring n_live_llm_attempted>0 when required, post-runtime exact semantic candidates materialized and locally Lean-checked with repair state exposed, exact source-theorem proof-body executor evidence with result rows plus local Lean/AXLE feedback or source-theorem kernel verification, ProofEngineer handoff feedback, explicit theorem-proof boundary fields, PF+BV row-kind/effective-vs-diagnostic split/method-lineage/non-proof contract complete for any pseudo-formal routing rows, source-semantic ProofEngineer bridge consumption for pseudo-formal semantic primitive work orders with semantic-support/not-source-theorem-proof status, FormalizationGapPlanner executable handoff context plus live route-planner target-prover route-revision followthrough, and priority_pinned_latest_rows retention plus row-level retention_selection whenever capability-gap routing input is truncated.",
        }
        if s13_followup_commands:
            s13_action["recommended_commands"] = s13_followup_commands
            s13_action["recommended_command_rows"] = s13_followup_command_rows
        actions.append(s13_action)
    if (
        rows_by_id.get("S10_live_coding_agent_generated_repair", None) is not None
        and rows_by_id["S10_live_coding_agent_generated_repair"].status != "OK"
    ):
        actions.append(
            {
                "rank": 4,
                "owner_suite": "S10_live_coding_agent_generated_repair",
                "action": "Run the combined live coding-agent generated-code repair gate with Claude/OpenAI and require both AlgorithmEngineer and SimulationEngineer fail-then-pass repair evidence.",
                "why": "Static fixtures and registered templates are plumbing/baseline evidence only; the system still needs live generated-code repair evidence for autonomous implementation and simulation capacity.",
                "success_metric": "coding_agent_generated_code_repair_capability_evidence_ok=true with nonzero algorithm and simulation repair sequences from a live provider.",
            }
        )
    if (
        rows_by_id.get("S11_live_formalizer_lean_candidate_repair", None) is not None
        and rows_by_id["S11_live_formalizer_lean_candidate_repair"].status != "OK"
    ):
        actions.append(
            {
                "rank": len(actions) + 1,
                "owner_suite": "S11_live_formalizer_lean_candidate_repair",
                "action": "Run the live Formalizer Lean-candidate repair gate with Claude/OpenAI and require local Lean fail-then-pass repair evidence.",
                "why": "Formalizer/ProofEngineer candidate materialization and local Lean feedback are plumbing unless a live generator repairs a failed candidate into a locally checked one.",
                "success_metric": "formalizer_lean_candidate_repair_capability_evidence_ok=true with a nonzero repair sequence and local_lean_compiled > 0 from a live provider.",
            }
        )
    if (
        rows_by_id.get("S11c_live_formalizer_pseudo_formal_packet", None)
        is not None
        and rows_by_id["S11c_live_formalizer_pseudo_formal_packet"].status != "OK"
    ):
        actions.append(
            {
                "rank": len(actions) + 1,
                "owner_suite": "S11c_live_formalizer_pseudo_formal_packet",
                "action": "Run the live Formalizer PF/BV packet-emission gate with Claude/OpenAI and require schema-valid source-anchored packets with nonzero lane-routable work-order rows.",
                "why": "Formalizer must reliably turn proof-body semantic blockers into PF/BV work packets before the BlockVerifier, RAG, source-to-bridge, or exact semantic-definition lanes can help.",
                "success_metric": "formalizer_pseudo_formal_packet_component_gate_capability_evidence_ok=true with pseudo_formal_packets>0, routable_work_order_rows>0, source_theorem_exact_semantic_definition in target lanes, exact_semantic_definition_lane_present=true, nonproof_boundary_preserved=true, proof_evidence_status_ok=true, no_theorem_proof_claim=true, and raw_model_output_written=false for standalone S11c; for integrated S13 the runtime attachment must also report attachment_gate_recomputed=true and runtime_formalizer_pseudo_formal_packet_component_gate_learning_consumed=true with consumed_rows>0.",
            }
        )
    if (
        rows_by_id.get("S11b_live_pseudo_formal_block_verifier", None) is not None
        and rows_by_id["S11b_live_pseudo_formal_block_verifier"].status != "OK"
    ):
        actions.append(
            {
                "rank": len(actions) + 1,
                "owner_suite": "S11b_live_pseudo_formal_block_verifier",
                "action": "Run the live PF/BV BlockVerifier component gate with Claude/OpenAI and require prompt packets, live verifier responses, and validated non-proof runtime learning rows.",
                "why": "Pseudo-formal block verification should smooth Formalizer feedback and capability-gap routing, but accepted PF/BV blocks remain verifier feedback unless Lean/AXLE kernel replay proves a target obligation.",
                "success_metric": "pseudo_formal_block_verifier_component_gate_capability_evidence_ok=true for standalone S11b, or research_agent_runtime_pseudo_formal_block_verifier_component_gate_capability_evidence_ok=true with prompt_packets>0, valid_responses>0, runtime_learning_rows>0, and source_runtime_learning_lineage_ok=true for integrated S13.",
            }
        )
    if (
        rows_by_id.get("S12_live_architect_research_path_policy", None) is not None
        and rows_by_id["S12_live_architect_research_path_policy"].status != "OK"
    ):
        actions.append(
            {
                "rank": len(actions) + 1,
                "owner_suite": "S12_live_architect_research_path_policy",
                "action": "Run the live Architect research-path policy gate with Claude/OpenAI and require required/advisory/optional cases to produce valid evidence contracts.",
                "why": "Architect prompt contracts are not enough unless a live generator can actually choose and preserve proof-first, simulation-first, and optional evidence policies.",
                "success_metric": "architect_research_path_policy_capability_evidence_ok=true with all cases OK and problem-analysis/knowledge-bank/fair-comparison fields present.",
            }
        )
    if (
        rows_by_id.get("S8_adversarial_unsupported_intake", None) is not None
        and rows_by_id["S8_adversarial_unsupported_intake"].status != "OK"
    ):
        actions.append(
            {
                "rank": len(actions) + 1,
                "owner_suite": "S8_adversarial_unsupported_intake",
                "action": "Wire adversarial unsupported-intake and prompt-leakage cases into the release audit.",
                "why": "The current benchmark stack has no dedicated guardrail suite for vague, contradictory, or gold-leaking frontier prompts.",
                "success_metric": "unsupported/adversarial cases are rejected or scoped without increasing false support claims.",
            }
        )
    return actions[:4]


def _markdown_report(payload: Mapping[str, Any]) -> str:
    lines = [
        "# Evaluation Benchmark Guidance",
        "",
        f"- Strategy doc present: `{payload.get('strategy_doc_present')}`",
        f"- Suites defined: {payload.get('suites_defined')}",
        f"- Frontier entries: {payload.get('frontier_entries')}",
        f"- Core research questions: {payload.get('core_research_questions')}",
        f"- Exercised suites: {payload.get('n_exercised')}/{payload.get('n_suites')}",
        f"- Stale or missing suites: {payload.get('n_stale_or_missing')}",
        f"- Saturated or capacity-gap suites: {payload.get('n_saturated_or_capacity_gap')}",
        "",
        "## Suite Status",
        "",
        "| Suite | Exercised | Status | Main issue |",
        "|---|---:|---|---|",
    ]
    for row in payload.get("suites", []):
        if not isinstance(row, dict):
            continue
        issues = row.get("issues") or ()
        main_issue = issues[0] if issues else ""
        lines.append(
            f"| `{row.get('suite_id')}` | `{row.get('exercised')}` | `{row.get('status')}` | {main_issue} |"
        )
    lines.extend(["", "## Top Actions", ""])
    for action in payload.get("top_actions", []):
        if not isinstance(action, dict):
            continue
        lines.append(
            f"{action.get('rank')}. **{action.get('owner_suite')}**: {action.get('action')}  \n"
            f"   Why: {action.get('why')}  \n"
            f"   Metric: {action.get('success_metric')}"
        )
        command_rows = _command_rows(action.get("recommended_command_rows", []))
        if command_rows:
            for row in command_rows:
                command = str(row.get("command", "") or "").strip()
                if not command:
                    continue
                requirement_id = str(row.get("requirement_id", "") or "").strip()
                owner_subsystem = str(row.get("owner_subsystem", "") or "").strip()
                context = ""
                if requirement_id or owner_subsystem:
                    context = (
                        " ("
                        + (f"`{requirement_id}`" if requirement_id else "unknown")
                        + " -> "
                        + (f"`{owner_subsystem}`" if owner_subsystem else "unknown")
                        + ")"
                    )
                metadata_parts = []
                scope = str(row.get("scope", "") or "").strip()
                priority = str(row.get("priority", "") or "").strip()
                retention_selection = str(
                    row.get("retention_selection", "") or ""
                ).strip()
                proof_evidence_status = str(
                    row.get("proof_evidence_status", "") or ""
                ).strip()
                if scope:
                    metadata_parts.append(f"scope=`{scope}`")
                if priority:
                    metadata_parts.append(f"priority=`{priority}`")
                if retention_selection:
                    metadata_parts.append(f"retention=`{retention_selection}`")
                if proof_evidence_status:
                    metadata_parts.append(f"evidence_status=`{proof_evidence_status}`")
                metadata = (
                    f" [{', '.join(metadata_parts)}]" if metadata_parts else ""
                )
                lines.append(f"   Command{context}{metadata}: `{command}`")
                boundary = str(
                    row.get("retention_selection_boundary", "")
                    or row.get("routing_boundary", "")
                    or ""
                ).strip()
                if boundary:
                    lines.append(f"   Boundary: {boundary}")
        else:
            for command in _command_strings(action.get("recommended_commands", [])):
                lines.append(f"   Command: `{command}`")
    lines.extend(["", "## Honesty Boundaries", ""])
    for boundary in payload.get("honesty_boundaries", []):
        lines.append(f"- {boundary}")
    lines.append("")
    return "\n".join(lines)


def _read_json(path: Path) -> Any:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def _int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _string_set(value: Any) -> set[str]:
    if not isinstance(value, (list, tuple, set)):
        return set()
    return {str(item).strip() for item in value if str(item).strip()}


def _command_strings(value: Any, *, limit: int = 4) -> list[str]:
    if not isinstance(value, (list, tuple, set)):
        return []
    commands: list[str] = []
    for item in value:
        if isinstance(item, Mapping):
            command = str(item.get("command", "") or "").strip()
        else:
            command = str(item or "").strip()
        if command and command not in commands:
            commands.append(command)
        if len(commands) >= limit:
            break
    return commands


def _command_rows(value: Any, *, limit: int = 4) -> list[dict[str, str]]:
    if not isinstance(value, (list, tuple, set)):
        return []
    rows: list[dict[str, str]] = []
    seen: set[tuple[str, str, str]] = set()
    for item in value:
        if isinstance(item, Mapping):
            command = str(item.get("command", "") or "").strip()
            requirement_id = str(item.get("requirement_id", "") or "").strip()
            owner_subsystem = str(item.get("owner_subsystem", "") or "").strip()
            scope = str(item.get("scope", "") or "").strip()
            priority = str(item.get("priority", "") or "").strip()
            retention_selection = str(
                item.get("retention_selection", "") or ""
            ).strip()
            retention_selection_boundary = str(
                item.get("retention_selection_boundary", "") or ""
            ).strip()
            proof_evidence_status = str(
                item.get("proof_evidence_status", "") or ""
            ).strip()
            routing_boundary = str(
                item.get("routing_boundary", "") or ""
            ).strip()
        else:
            command = str(item or "").strip()
            requirement_id = ""
            owner_subsystem = ""
            scope = ""
            priority = ""
            retention_selection = ""
            retention_selection_boundary = ""
            proof_evidence_status = ""
            routing_boundary = ""
        if not command:
            continue
        key = (requirement_id, owner_subsystem, command)
        if key in seen:
            continue
        seen.add(key)
        rows.append(
            {
                "requirement_id": requirement_id,
                "owner_subsystem": owner_subsystem,
                "scope": scope,
                "priority": priority,
                "retention_selection": retention_selection,
                "retention_selection_boundary": retention_selection_boundary,
                "proof_evidence_status": proof_evidence_status,
                "routing_boundary": routing_boundary,
                "command": command,
            }
        )
        if len(rows) >= limit:
            break
    return rows


def _float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0
