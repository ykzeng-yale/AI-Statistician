from __future__ import annotations

import json
import shlex
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .fingerprint import stable_hash
from .formalization_gap_planner_adapter_registry import (
    export_formalization_gap_planner_adapter_registry,
)
from .formalization_gap_planner_adapter_registry_audit import (
    audit_formalization_gap_planner_adapter_registry,
)
from .formalization_gap_planner_component_resource_registry import (
    export_formalization_gap_planner_component_resource_registry,
)
from .formalization_gap_planner_component_resource_registry_audit import (
    audit_formalization_gap_planner_component_resource_registry,
)
from .formalization_gap_planner_ablation_study import (
    export_formalization_gap_planner_ablation_study,
)
from .formalization_gap_planner_evaluation import (
    evaluate_formalization_gap_planner,
)
from .formalization_gap_planner_interactive_session import (
    export_formalization_gap_planner_interactive_session,
)
from .formalization_gap_planner_local_formal_source_adapter import (
    LEGACY_FORMAL_SOURCE_ADAPTER_FIELD_ALIASES,
    export_formalization_gap_planner_local_formal_source_adapter_responses,
)
from .formalization_gap_planner_local_literature_adapter import (
    export_formalization_gap_planner_local_literature_adapter_responses,
)
from .formalization_gap_planner_local_proof_state_adapter import (
    export_formalization_gap_planner_local_proof_state_adapter_responses,
)
from .formalization_gap_planner_library_coverage_map import (
    export_formalization_gap_planner_library_coverage_map,
)
from .formalization_gap_planner_llm_route_planner import (
    export_formalization_gap_planner_llm_route_planner,
    validate_formalization_gap_planner_llm_route_planner_response_payloads,
)
from .formalization_gap_planner_primitive_action_queue import (
    export_formalization_gap_planner_primitive_action_queue,
)
from .formalization_gap_planner_action_resource_plan import (
    export_formalization_gap_planner_action_resource_plan,
)
from .formalization_gap_planner_resource_request_queue import (
    export_formalization_gap_planner_resource_request_queue,
)
from .formalization_gap_planner_resource_response_ledger import (
    export_formalization_gap_planner_resource_response_ledger,
)
from .formalization_gap_planner_portable_plan_audit import (
    audit_formalization_gap_planner_portable_plan,
)
from .formalization_gap_planner_cross_prover_matrix_audit import (
    DEFAULT_REUSE_TARGETS,
    audit_formalization_gap_planner_cross_prover_matrix,
)
from .formalization_gap_planner_minimal_delta_audit import (
    audit_formalization_gap_planner_minimal_delta,
)
from .formalization_gap_planner_minimal_delta_audit_feedback_adapter import (
    export_formalization_gap_planner_minimal_delta_audit_feedback_responses,
)
from .formalization_gap_planner_source_grounding_audit import (
    audit_formalization_gap_planner_source_grounding,
)
from .formalization_gap_planner_prover_adapter_contract import (
    export_formalization_gap_planner_prover_adapter_contract,
)
from .formalization_gap_planner_publication_bundle import (
    export_formalization_gap_planner_publication_bundle,
)
from .formalization_gap_planner_publication_bundle_audit import (
    audit_formalization_gap_planner_publication_bundle,
)
from .formalization_gap_planner_proof_state_triage import (
    export_formalization_gap_planner_proof_state_triage,
)
from .formalization_gap_planner_prover_adapter_feedback_adapter import (
    export_formalization_gap_planner_prover_adapter_feedback_responses,
)
from .formalization_gap_planner_refinement_adapters import (
    export_formalization_gap_planner_refinement_adapter_responses,
)
from .formalization_gap_planner_refinement_evidence import (
    export_formalization_gap_planner_refinement_evidence,
)
from .formalization_gap_planner_refinement_queue import (
    export_formalization_gap_planner_refinement_queue,
)
from .formalization_gap_planner_route_revision_overlay import (
    export_formalization_gap_planner_route_revision_overlay,
)
from .formalization_gap_planner_route_replan_handoff import (
    export_formalization_gap_planner_route_replan_handoff,
)
from .formalization_gap_planner_route_replan_handoff_audit import (
    audit_formalization_gap_planner_route_replan_handoff,
)
from .formalization_gap_planner_route_stability_audit import (
    audit_formalization_gap_planner_route_stability,
)
from .formalization_gap_planner_standalone import (
    export_formalization_gap_planner_standalone_plan,
)
from .formalization_gap_planner_target_intake import (
    normalize_formalization_gap_planner_target_intake,
)


FORMALIZATION_GAP_PLANNER_REUSE_SMOKE_SCHEMA_VERSION = 1
FORMALIZATION_GAP_PLANNER_REUSE_SMOKE_COMPONENT = (
    "formalization_gap_planner_reuse_smoke"
)
PROOF_EVIDENCE_STATUS = "FORMALIZATION_GAP_PLANNER_REUSE_SMOKE_NOT_PROOF_EVIDENCE"
PROOF_EVIDENCE_BOUNDARY = (
    "The reuse smoke test validates that the public planner path can produce "
    "portable contracts, work packets, a publication bundle, and packaging "
    "audits. It is not theorem proof evidence."
)
SUMMARY_KEYS_BY_STAGE = {
    "formalization_gap_planner_target_intake": (
        "n_targets",
        "n_ok",
        "n_primitive_seed_rows",
        "n_literature_queries",
        "n_formal_library_grounding_queries",
        "n_lean_grounding_queries",
        "n_missing_proof_sources",
        "n_missing_theorem_skeleton",
    ),
    "formalization_gap_planner_llm_route_planner": (
        "provider_name",
        "invoke_provider",
        "model_tier_selection_mode",
        "by_request_model_tier",
        "n_request_model_tier_haiku",
        "n_request_model_tier_sonnet",
        "n_request_model_tier_opus",
        "n_request_model_tier_mismatches",
        "n_routes",
        "n_request_packets",
        "n_requests_with_context_packet_inventory",
        "n_request_context_inventory_total_rows",
        "n_rows_with_context_packet_inventory",
        "n_requests_with_quality_control_obligation_inventory",
        "n_requests_with_pending_quality_control_obligation_inventory",
        "n_request_quality_control_obligation_fields",
        "n_request_quality_control_obligation_values",
        "n_request_pending_quality_control_fields",
        "n_request_pending_quality_control_values",
        "n_request_discharged_quality_control_fields",
        "n_request_discharged_quality_control_values",
        "n_request_schema_valid",
        "n_request_schema_invalid",
        "n_response_present",
        "n_awaiting_llm_response",
        "n_response_contract_ok",
        "n_accepted_route_plans",
        "n_route_adoption_ready",
        "n_route_adoption_pending_refinement",
        "n_route_adoption_awaiting_llm_response",
        "n_route_adoption_rejected",
        "n_route_adoption_pending_search_request_blockers",
        "n_route_adoption_pending_planner_next_action_blockers",
        "n_route_adoption_pending_uncertainty_blockers",
        "n_route_adoption_pending_residual_repair_blockers",
        "n_route_adoption_pending_feedback_action_blockers",
        "n_route_adoption_pending_resource_playbook_redispatch_blockers",
        "n_route_adoption_pending_resource_request_queue_blockers",
        "n_route_adoption_pending_feedback_replan_blockers",
        "n_route_adoption_pending_realization_coverage_blockers",
        "n_route_adoption_pending_omitted_cost_hint_primitive_blockers",
        "n_route_adoption_pending_formal_gap_boundary_blockers",
        "n_route_adoption_pending_source_grounding_blockers",
        "n_route_adoption_pending_quality_control_blockers",
        "n_route_adoption_omitted_cost_hint_primitives",
        "n_rejected",
        "n_informal_knowledge_dag_nodes",
        "n_formal_realization_dag_nodes",
        "legacy_response_field_aliases",
        "n_lean_realization_dag_nodes",
        "n_route_alignment_edges",
        "n_rows_with_realization_coverage_witness",
        "n_rows_with_complete_realization_coverage",
        "n_selected_primitives_missing_formal_realization",
        "n_delta_primitives_missing_route_alignment",
        "n_feedback_loop_summary_realization_witnesses",
        "n_feedback_loop_summary_incomplete_realization_coverage",
        "n_feedback_loop_summary_incomplete_cost_hint_baseline_coverage",
        "n_feedback_loop_summary_missing_selected_formal_primitives",
        "n_feedback_loop_summary_missing_delta_alignment_primitives",
        "n_feedback_loop_summary_omitted_cost_hint_primitives",
        "n_search_requests",
        "n_planner_next_actions",
        "n_rows_with_planner_next_actions",
        "n_row_schema_valid",
        "n_row_schema_invalid",
    ),
    "formalization_gap_planner_feedback_llm_route_planner": (
        "provider_name",
        "invoke_provider",
        "model_tier_selection_mode",
        "by_request_model_tier",
        "n_request_model_tier_haiku",
        "n_request_model_tier_sonnet",
        "n_request_model_tier_opus",
        "n_request_model_tier_mismatches",
        "n_routes",
        "n_request_packets",
        "n_requests_with_context_packet_inventory",
        "n_request_context_inventory_total_rows",
        "n_rows_with_context_packet_inventory",
        "n_requests_with_quality_control_obligation_inventory",
        "n_requests_with_pending_quality_control_obligation_inventory",
        "n_request_quality_control_obligation_fields",
        "n_request_quality_control_obligation_values",
        "n_request_pending_quality_control_fields",
        "n_request_pending_quality_control_values",
        "n_request_discharged_quality_control_fields",
        "n_request_discharged_quality_control_values",
        "n_request_schema_valid",
        "n_request_schema_invalid",
        "n_response_present",
        "n_awaiting_llm_response",
        "n_response_contract_ok",
        "n_accepted_route_plans",
        "n_route_adoption_ready",
        "n_route_adoption_pending_refinement",
        "n_route_adoption_awaiting_llm_response",
        "n_route_adoption_rejected",
        "n_route_adoption_pending_search_request_blockers",
        "n_route_adoption_pending_planner_next_action_blockers",
        "n_route_adoption_pending_uncertainty_blockers",
        "n_route_adoption_pending_residual_repair_blockers",
        "n_route_adoption_pending_feedback_action_blockers",
        "n_route_adoption_pending_resource_playbook_redispatch_blockers",
        "n_route_adoption_pending_resource_request_queue_blockers",
        "n_route_adoption_pending_feedback_replan_blockers",
        "n_route_adoption_pending_realization_coverage_blockers",
        "n_route_adoption_pending_omitted_cost_hint_primitive_blockers",
        "n_route_adoption_pending_formal_gap_boundary_blockers",
        "n_route_adoption_pending_source_grounding_blockers",
        "n_route_adoption_pending_quality_control_blockers",
        "n_route_adoption_omitted_cost_hint_primitives",
        "n_rejected",
        "n_informal_knowledge_dag_nodes",
        "n_formal_realization_dag_nodes",
        "legacy_response_field_aliases",
        "n_lean_realization_dag_nodes",
        "n_route_alignment_edges",
        "n_rows_with_realization_coverage_witness",
        "n_rows_with_complete_realization_coverage",
        "n_selected_primitives_missing_formal_realization",
        "n_delta_primitives_missing_route_alignment",
        "n_feedback_loop_summary_realization_witnesses",
        "n_feedback_loop_summary_incomplete_realization_coverage",
        "n_feedback_loop_summary_incomplete_cost_hint_baseline_coverage",
        "n_feedback_loop_summary_missing_selected_formal_primitives",
        "n_feedback_loop_summary_missing_delta_alignment_primitives",
        "n_feedback_loop_summary_omitted_cost_hint_primitives",
        "n_search_requests",
        "n_planner_next_actions",
        "n_rows_with_planner_next_actions",
        "n_row_schema_valid",
        "n_row_schema_invalid",
    ),
    "formalization_gap_planner_llm_route_planner_response_payload_validation": (
        "n_payloads",
        "n_valid_payloads",
        "n_invalid_payloads",
        "n_request_context_packets",
        "n_request_contexts_with_context_packet_inventory",
        "n_request_context_inventory_total_rows",
        "n_request_bound_payloads",
        "n_request_bound_payloads_with_context_packet_inventory",
        "n_request_bound_payload_context_inventory_total_rows",
        "all_ok",
    ),
    "goal_conditioned_minimal_formalization_plan": (
        "n_goal_plans",
        "n_ok",
        "target_prover_family",
        "n_target_prover_families",
        "by_target_prover_family",
        "library_snapshot_ref",
        "n_standalone_input_traces_with_llm_route_adoption_status",
        "n_standalone_input_traces_ready_for_route_adoption",
        "n_standalone_input_traces_pending_refinement_before_route_adoption",
        "n_standalone_input_trace_route_adoption_blockers",
        "n_portable_work_packets",
        "n_existing_reuse_nodes",
        "n_wrapper_nodes",
        "n_bridge_nodes",
        "n_source_discovery_nodes",
        "n_first_principles_nodes",
        "n_route_alignment_edges",
        "n_route_alignment_edge_schema_valid",
        "n_route_alignment_edge_schema_invalid",
    ),
    "formalization_gap_planner_portable_plan_audit": (
        "n_checks",
        "n_ok",
        "n_failed",
        "n_row_schema_valid",
        "n_row_schema_invalid",
        "n_plan_rows",
        "n_contract_errors",
        "n_rows_with_two_dag",
        "n_rows_with_alignment_edges",
        "n_route_alignment_edges",
        "n_route_alignment_edge_schema_valid",
        "n_route_alignment_edge_schema_invalid",
        "n_rows_with_work_packets",
        "n_rows_without_kernel_claims",
    ),
    "formalization_gap_planner_library_coverage_map": (
        "n_coverage_rows",
        "n_ok",
        "n_failed",
        "n_exact_exists",
        "n_near_exists",
        "n_wrapper_needed",
        "n_bridge_needed",
        "n_source_port_needed",
        "n_definition_or_theory_missing",
        "n_unknown_or_unaligned",
        "n_reusable_without_new_declaration",
        "n_needs_prover_feedback",
        "n_needs_source_search",
        "n_needs_new_definition_or_theory",
        "n_rows_with_candidate_declarations",
        "n_rows_with_candidate_declaration_rows",
        "n_candidate_declaration_rows",
        "n_rows_with_alignment",
        "n_row_schema_valid",
        "n_row_schema_invalid",
    ),
    "formalization_gap_planner_primitive_action_queue": (
        "n_action_items",
        "n_ok",
        "n_failed",
        "n_target_prover_replay",
        "n_compose_existing_declarations",
        "n_write_wrapper",
        "n_prove_bridge_lemma",
        "n_source_port",
        "n_design_new_theory_fragment",
        "n_rerun_library_alignment",
        "n_with_candidate_declarations",
        "n_with_candidate_declaration_rows",
        "n_candidate_declaration_rows",
        "n_with_source_refs",
        "n_with_bridge_obligations",
        "n_row_schema_valid",
        "n_row_schema_invalid",
    ),
    "formalization_gap_planner_minimal_delta_audit": (
        "n_checks",
        "n_ok",
        "n_failed",
        "n_plan_rows",
        "n_rows_with_cost_formula_ok",
        "n_rows_with_node_cost_accounting_ok",
        "n_rows_with_work_packet_cut_ok",
        "n_dominated_route_witnesses",
        "n_minimal_delta_decision_rows",
        "n_minimal_delta_decision_row_schema_valid",
        "n_minimal_delta_decision_row_schema_invalid",
    ),
    "formalization_gap_planner_source_grounding_audit": (
        "n_source_grounding_rows",
        "n_ok",
        "n_failed",
        "n_source_backed",
        "n_source_search_pending",
        "n_formal_boundary_declared",
        "n_unaccounted",
        "n_row_schema_valid",
        "n_row_schema_invalid",
    ),
    "formalization_gap_planner_evaluation": (
        "n_plan_rows",
        "n_ground_truth_rows",
        "n_evaluation_rows",
        "n_evaluation_row_schema_valid",
        "n_evaluation_row_schema_invalid",
        "n_matched_ground_truth",
        "n_missing_ground_truth",
        "n_alignment_contract_ok",
        "n_feedback_loop_ready",
        "n_unaligned_primitives",
        "mean_route_recall",
        "mean_delta_precision",
        "mean_alignment_coverage",
    ),
    "formalization_gap_planner_prover_adapter_contract": (
        "target_prover_family",
        "n_packets",
        "n_packet_ok",
        "n_packet_schema_valid",
        "n_response_present",
        "n_awaiting_adapter_mapping",
        "n_response_contract_ok",
        "n_response_validation_row_schema_valid",
        "n_response_validation_row_schema_invalid",
        "n_rejected",
        "n_kernel_verified_claims_rejected",
    ),
    "formalization_gap_planner_adapter_registry": (
        "n_adapters",
        "n_adapter_row_schema_valid",
        "n_adapter_row_schema_invalid",
        "n_ready_local_or_configured",
        "n_contract_only",
        "n_needs_install",
        "n_needs_credentials",
        "n_needs_configuration",
    ),
    "formalization_gap_planner_adapter_registry_audit": (
        "n_checks",
        "n_ok",
        "n_failed",
        "n_registry_rows",
        "n_adapter_row_schema_valid",
        "n_adapter_row_schema_invalid",
        "n_adapter_jsonl_row_schema_valid",
        "n_adapter_jsonl_row_schema_invalid",
        "n_required_adapter_ids_present",
        "n_ready_local_or_configured",
        "n_mcp_or_cli_surfaces",
    ),
    "formalization_gap_planner_component_resource_registry": (
        "n_component_rows",
        "n_component_rows_ok",
        "n_component_row_schema_valid",
        "n_component_row_schema_invalid",
        "n_execution_plan_rows",
        "n_execution_plan_rows_ok",
        "n_execution_plan_row_schema_valid",
        "n_execution_plan_row_schema_invalid",
        "n_resources",
        "n_resource_rows_ok",
        "n_resource_row_schema_valid",
        "n_resource_row_schema_invalid",
        "n_frontier_resources",
        "n_mcp_or_cli_resources",
    ),
    "formalization_gap_planner_component_resource_registry_audit": (
        "n_checks",
        "n_ok",
        "n_failed",
        "n_component_rows",
        "n_component_row_schema_valid",
        "n_component_row_schema_invalid",
        "n_execution_plan_rows",
        "n_execution_plan_rows_ok",
        "n_execution_plan_schema_valid",
        "n_execution_plan_schema_invalid",
        "n_components_with_execution_plan",
        "n_required_component_ids_present",
        "n_resource_rows",
        "n_resource_row_schema_valid",
        "n_resource_row_schema_invalid",
        "n_required_resource_ids_present",
        "n_frontier_resources",
        "n_mcp_or_cli_resources",
    ),
    "formalization_gap_planner_action_resource_plan": (
        "n_resource_plan_rows",
        "n_ok",
        "n_failed",
        "n_with_local_first_resources",
        "n_with_frontier_escalation_resources",
        "n_with_resource_contracts",
        "n_with_candidate_declaration_rows",
        "n_candidate_declaration_rows",
        "n_row_schema_valid",
        "n_row_schema_invalid",
        "n_prove_bridge_lemma",
        "n_source_port",
    ),
    "formalization_gap_planner_resource_request_queue": (
        "n_resource_request_rows",
        "n_ok",
        "n_failed",
        "n_local_first_requests",
        "n_frontier_escalation_requests",
        "n_distinct_resources",
        "n_with_mcp_or_cli_hint",
        "n_with_candidate_declaration_rows",
        "n_candidate_declaration_rows",
        "n_row_schema_valid",
        "n_row_schema_invalid",
    ),
    "formalization_gap_planner_resource_response_ledger": (
        "n_ledger_rows",
        "n_ok",
        "n_response_present",
        "n_awaiting_response",
        "n_response_contract_ok",
        "n_route_revision_recommended",
        "n_rejected",
        "n_ledger_row_schema_valid",
        "n_ledger_row_schema_invalid",
    ),
    "formalization_gap_planner_refinement_queue": (
        "n_refinement_items",
        "n_item_schema_valid",
        "n_item_schema_invalid",
        "n_ready",
        "n_blocked",
        "n_literature_discovery_items",
        "n_formal_library_grounding_items",
        "n_lean_library_grounding_items",
        "n_proof_state_feedback_items",
        "n_route_revision_items",
    ),
    "formalization_gap_planner_refinement_adapter_responses": (
        "n_queue_rows",
        "n_responses",
        "n_ground_truth_matched",
        "n_ground_truth_unmatched",
        "n_formal_grounding_responses",
        "n_lean_grounding_responses",
        "n_route_revision_recommended",
        "n_response_schema_valid",
        "n_response_schema_invalid",
    ),
    "formalization_gap_planner_minimal_delta_audit_feedback_adapter": (
        "n_queue_rows",
        "n_route_revision_rows",
        "n_minimal_delta_decision_rows",
        "n_failed_minimal_delta_decision_rows",
        "n_generated_feedback_responses",
        "n_merged_responses",
        "n_matched_route_revision_rows",
        "n_unmatched_route_revision_rows",
        "n_route_revision_recommended",
        "n_response_schema_valid",
        "n_response_schema_invalid",
        "n_merged_response_schema_valid",
        "n_merged_response_schema_invalid",
    ),
    "formalization_gap_planner_local_literature_adapter": (
        "n_queue_rows",
        "n_literature_discovery_rows",
        "n_documents_indexed",
        "n_local_literature_responses",
        "n_source_hits",
        "n_literature_gap_responses",
        "n_merged_responses",
        "n_local_response_schema_valid",
        "n_local_response_schema_invalid",
        "n_merged_response_schema_valid",
        "n_merged_response_schema_invalid",
    ),
    "formalization_gap_planner_local_formal_source_adapter": (
        "n_queue_rows",
        "n_formal_library_grounding_rows",
        "n_lean_library_grounding_rows",
        "search_backend",
        "lean_rag_dependency_graph_enabled",
        "n_local_formal_source_responses",
        "n_hits",
        "n_exact_exists",
        "n_merged_responses",
        "n_local_response_schema_valid",
        "n_local_response_schema_invalid",
        "n_merged_response_schema_valid",
        "n_merged_response_schema_invalid",
    ),
    "formalization_gap_planner_local_proof_state_adapter": (
        "n_queue_rows",
        "n_proof_state_feedback_rows",
        "n_target_proof_state_feedback_rows",
        "n_skipped_non_target_proof_state_feedback_rows",
        "lean_command_available",
        "n_local_proof_state_responses",
        "n_target_prover_scaffold_accepted",
        "n_target_prover_failed",
        "n_target_prover_unavailable",
        "n_non_target_prover_skeleton",
        "n_local_lean_unavailable",
        "n_placeholder_blocked",
        "n_formal_gap_scaffold_blocked",
        "n_non_lean_skeleton",
        "n_missing_skeleton",
        "n_merged_responses",
        "n_local_response_schema_valid",
        "n_local_response_schema_invalid",
        "n_merged_response_schema_valid",
        "n_merged_response_schema_invalid",
    ),
    "formalization_gap_planner_prover_adapter_feedback_adapter": (
        "n_queue_rows",
        "n_proof_state_feedback_rows",
        "n_validation_sources",
        "n_validation_rows",
        "n_validation_rows_with_response",
        "n_validation_rows_contract_ok",
        "n_generated_feedback_responses",
        "n_merged_responses",
        "n_matched_proof_state_feedback_rows",
        "n_unmatched_proof_state_feedback_rows",
        "n_route_revision_recommended",
        "n_response_schema_valid",
        "n_response_schema_invalid",
        "n_merged_response_schema_valid",
        "n_merged_response_schema_invalid",
    ),
    "formalization_gap_planner_refinement_evidence": (
        "n_evidence_rows",
        "n_response_present",
        "n_contract_ok",
        "n_response_schema_valid",
        "n_response_schema_invalid",
        "n_awaiting_tool_response",
        "n_formal_grounding_evidence",
        "n_lean_grounding_evidence",
        "n_route_revision_recommended",
        "n_rejected",
    ),
    "formalization_gap_planner_route_revision_overlay": (
        "n_overlay_rows",
        "n_row_schema_valid",
        "n_row_schema_invalid",
        "n_routes_with_revision",
        "n_routes_without_revision",
        "n_orphan_route_revision_proposals",
        "n_added_primitives",
        "n_added_delta_primitives",
    ),
    "formalization_gap_planner_route_stability_audit": (
        "n_stability_rows",
        "n_stable",
        "n_needs_expansion",
        "n_awaiting_responses",
        "n_apply_route_revision",
        "n_new_primitives_since_plan",
    ),
    "formalization_gap_planner_route_replan_handoff": (
        "n_handoff_rows",
        "n_row_schema_valid",
        "n_row_schema_invalid",
        "n_routes_requiring_replan",
        "n_routes_without_replan",
        "n_standalone_seed_routes",
        "n_route_alignment_edges",
        "n_revised_informal_knowledge_dag_nodes",
        "n_revised_formal_realization_dag_nodes",
        "n_revised_lean_realization_dag_nodes",
        "n_unaligned_primitives",
        "n_routes_with_residual_goals",
    ),
    "formalization_gap_planner_route_replan_handoff_audit": (
        "n_checks",
        "n_ok",
        "n_failed",
        "n_handoff_rows",
        "n_seed_routes",
        "n_roundtrip_goal_plans",
        "n_roundtrip_route_alignment_edges",
        "n_roundtrip_standalone_input_traces",
        "n_roundtrip_standalone_input_traces_with_replan_metadata",
        "n_roundtrip_standalone_input_trace_llm_route_planner_hook_traces",
        "n_roundtrip_standalone_input_traces_with_llm_route_planner_hook_traces",
        "n_row_schema_valid",
        "n_row_schema_invalid",
        "roundtrip_all_ok",
    ),
    "formalization_gap_planner_proof_state_triage": (
        "n_overlay_rows",
        "n_triage_items",
        "n_formal_gap_scaffold_items",
        "n_target_prover_failed_items",
        "n_target_prover_unavailable_items",
        "n_non_target_prover_skeleton_items",
        "n_local_lean_failed_items",
        "n_non_lean_skeleton_items",
        "n_with_residual_goals",
    ),
    "formalization_gap_planner_interactive_session": (
        "n_session_rows",
        "n_row_schema_valid",
        "n_row_schema_invalid",
        "n_decision_policy_rows",
        "n_decision_policy_rows_with_resource_contracts",
        "n_decision_policy_rows_with_frontier_resources",
        "n_decision_policy_row_schema_valid",
        "n_decision_policy_row_schema_invalid",
        "n_run_literature_search",
        "n_run_formal_grounding",
        "n_run_lean_grounding",
        "n_run_proof_state_feedback",
        "n_run_route_replan",
        "n_run_target_prover_replay",
    ),
    "formalization_gap_planner_ablation_study": (
        "n_plan_rows",
        "n_evaluation_rows",
        "n_session_rows",
        "n_ablation_variants",
        "n_ok",
        "n_row_schema_valid",
        "n_row_schema_invalid",
        "best_variant_by_route_recall",
        "largest_route_recall_drop_variant",
        "largest_delta_recall_drop_variant",
    ),
    "formalization_gap_planner_cross_prover_matrix_audit": (
        "n_targets",
        "n_targets_ok",
        "n_matrix_row_schema_valid",
        "n_matrix_row_schema_invalid",
        "n_total_packets",
        "n_total_packet_ok",
        "n_total_packet_schema_valid",
        "n_total_packets_schema_invalid",
        "n_packet_row_schema_valid",
        "n_packet_row_schema_invalid",
        "n_response_validation_row_schema_valid",
        "n_response_validation_row_schema_invalid",
        "n_total_packets_with_alignment",
        "n_total_packets_missing_alignment",
        "n_awaiting_adapter_mapping",
        "n_rejected",
        "packet_count_consistent",
        "alignment_packet_count_consistent",
    ),
    "formalization_gap_planner_publication_bundle": (
        "bundle_id",
        "n_core_artifacts",
        "n_core_artifacts_ok",
        "n_optional_artifacts_requested",
        "n_optional_artifact_files_copied",
        "n_docs_copied",
        "portable_reuse_targets",
        "llm_route_planner_summary",
        "feedback_llm_route_planner_summary",
    ),
    "formalization_gap_planner_publication_bundle_audit": (
        "n_checks",
        "n_ok",
        "n_failed",
        "n_bundle_llm_route_planner_summary_checked",
        "n_bundle_llm_route_planner_summary_valid",
        "n_bundle_feedback_llm_route_planner_summary_checked",
        "n_bundle_feedback_llm_route_planner_summary_valid",
        "n_component_execution_plan_schema_checked",
        "n_component_execution_plan_schema_valid",
        "n_component_resource_component_row_schema_checked",
        "n_component_resource_component_row_schema_valid",
        "n_component_resource_resource_row_schema_checked",
        "n_component_resource_resource_row_schema_valid",
        "n_benchmark_route_row_schema_checked",
        "n_benchmark_route_row_schema_valid",
        "n_optional_evaluation_row_schema_checked",
        "n_optional_evaluation_row_schema_valid",
        "n_optional_evaluation_ground_truth_file_checked",
        "n_optional_evaluation_ground_truth_file_valid",
        "n_optional_evaluation_ground_truth_match_checked",
        "n_optional_evaluation_ground_truth_match_valid",
        "n_optional_evaluation_ground_truth_primitive_checked",
        "n_optional_evaluation_ground_truth_primitive_valid",
        "n_optional_interactive_decision_policy_row_schema_checked",
        "n_optional_interactive_decision_policy_row_schema_valid",
        "n_optional_interactive_decision_policy_link_checked",
        "n_optional_interactive_decision_policy_link_valid",
        "n_optional_interactive_session_row_schema_checked",
        "n_optional_interactive_session_row_schema_valid",
        "n_optional_interactive_session_resource_response_status_checked",
        "n_optional_interactive_session_resource_response_status_valid",
        "n_optional_interactive_session_generic_prover_fields_checked",
        "n_optional_interactive_session_generic_prover_fields_valid",
        "n_optional_refinement_evidence_row_schema_checked",
        "n_optional_refinement_evidence_row_schema_valid",
        "n_optional_refinement_adapter_response_schema_checked",
        "n_optional_refinement_adapter_response_schema_valid",
        "n_optional_local_adapter_response_schema_checked",
        "n_optional_local_adapter_response_schema_valid",
        "n_optional_route_stability_audit_row_schema_checked",
        "n_optional_route_stability_audit_row_schema_valid",
        "n_optional_route_stability_resource_response_status_checked",
        "n_optional_route_stability_resource_response_status_valid",
        "n_optional_route_stability_generic_prover_fields_checked",
        "n_optional_route_stability_generic_prover_fields_valid",
        "n_optional_route_revision_resource_response_evidence_ref_checked",
        "n_optional_route_revision_resource_response_evidence_ref_valid",
        "n_optional_route_revision_resource_response_status_checked",
        "n_optional_route_revision_resource_response_status_valid",
        "n_optional_route_replan_handoff_audit_row_schema_checked",
        "n_optional_route_replan_handoff_audit_row_schema_valid",
        "n_optional_llm_route_planner_response_payload_validation_manifest_contract_checked",
        "n_optional_llm_route_planner_response_payload_validation_manifest_contract_valid",
        "n_optional_llm_route_planner_response_payload_validation_count_checked",
        "n_optional_llm_route_planner_response_payload_validation_count_valid",
        "n_optional_llm_route_planner_response_payload_validation_row_schema_checked",
        "n_optional_llm_route_planner_response_payload_validation_row_schema_valid",
        "n_optional_ablation_study_row_schema_checked",
        "n_optional_ablation_study_row_schema_valid",
        "n_optional_proof_state_triage_row_schema_checked",
        "n_optional_proof_state_triage_row_schema_valid",
        "n_optional_proof_state_triage_generic_prover_fields_checked",
        "n_optional_proof_state_triage_generic_prover_fields_valid",
        "n_optional_library_coverage_map_row_schema_checked",
        "n_optional_library_coverage_map_row_schema_valid",
        "n_optional_resource_request_queue_row_schema_checked",
        "n_optional_resource_request_queue_row_schema_valid",
        "n_optional_resource_request_contract_alignment_checked",
        "n_optional_resource_request_contract_alignment_valid",
        "n_optional_resource_request_action_plan_ref_checked",
        "n_optional_resource_request_action_plan_ref_valid",
        "n_optional_resource_response_ledger_row_schema_checked",
        "n_optional_resource_response_ledger_row_schema_valid",
        "n_optional_resource_response_request_ref_checked",
        "n_optional_resource_response_request_ref_valid",
        "n_optional_resource_response_contract_field_accounting_checked",
        "n_optional_resource_response_contract_field_accounting_valid",
        "n_prover_adapter_packet_schema_checked",
        "n_prover_adapter_packet_schema_valid",
        "n_bundle_files",
        "bundle_id",
    ),
}


@dataclass(frozen=True)
class FormalizationGapPlannerReuseSmokeStage:
    schema_version: int
    stage_id: str
    stage_name: str
    component_name: str
    artifact_dir: str
    manifest_path: str
    ok: bool
    proof_boundary_ok: bool
    proof_evidence_status: str
    proof_evidence_boundary: str
    summary: dict[str, object]
    errors: tuple[str, ...] = ()


def run_formalization_gap_planner_reuse_smoke(
    target_intake_input: Path,
    out_dir: Path,
    *,
    target_prover_family: str = "rocq",
    target_library_snapshot_ref: str = "",
    max_routes: int = 20,
    ground_truth_path: Path | None = None,
    lean_rag_db_path: Path | None = None,
    paper_library_dir: Path | None = None,
    llm_route_planner_provider: str = "anthropic",
    llm_route_planner_model: str = "",
    llm_route_planner_model_tier: str = "auto",
    llm_route_planner_max_tokens: int = 9000,
    llm_route_planner_max_repair_attempts: int = 1,
    llm_route_planner_temperature: float = 0.1,
    llm_route_planner_invoke_provider: bool = False,
    llm_route_planner_response_json: Path | None = None,
    llm_route_planner_static_response_json: Path | None = None,
    feedback_llm_route_planner_provider: str = "anthropic",
    feedback_llm_route_planner_model: str = "",
    feedback_llm_route_planner_model_tier: str = "auto",
    feedback_llm_route_planner_max_tokens: int = 9000,
    feedback_llm_route_planner_max_repair_attempts: int = 1,
    feedback_llm_route_planner_temperature: float = 0.1,
    feedback_llm_route_planner_invoke_provider: bool = False,
    feedback_llm_route_planner_response_json: Path | None = None,
    feedback_llm_route_planner_static_response_json: Path | None = None,
) -> dict[str, object]:
    """Run the public gap-planner path as one reproducible smoke test.

    The smoke path is intentionally proof-boundary preserving: it validates
    portable route planning, target-prover mapping packets, and publication
    bundle packaging, but it does not claim that any theorem has been proved.
    """

    out_dir.mkdir(parents=True, exist_ok=True)
    target_intake_dir = out_dir / "formalization_gap_planner_target_intake"
    llm_route_planner_dir = out_dir / "formalization_gap_planner_llm_route_planner"
    plan_dir = out_dir / "goal_conditioned_minimal_formalization_plan"
    portable_plan_audit_dir = out_dir / "formalization_gap_planner_portable_plan_audit"
    library_coverage_map_dir = (
        out_dir / "formalization_gap_planner_library_coverage_map"
    )
    primitive_action_queue_dir = (
        out_dir / "formalization_gap_planner_primitive_action_queue"
    )
    minimal_delta_audit_dir = out_dir / "formalization_gap_planner_minimal_delta_audit"
    source_grounding_audit_dir = out_dir / "formalization_gap_planner_source_grounding_audit"
    evaluation_dir = out_dir / "formalization_gap_planner_evaluation"
    prover_adapter_contract_dir = (
        out_dir / "formalization_gap_planner_prover_adapter_contract"
    )
    adapter_registry_dir = out_dir / "formalization_gap_planner_adapter_registry"
    adapter_registry_audit_dir = (
        out_dir / "formalization_gap_planner_adapter_registry_audit"
    )
    component_resource_registry_dir = (
        out_dir / "formalization_gap_planner_component_resource_registry"
    )
    component_resource_registry_audit_dir = (
        out_dir / "formalization_gap_planner_component_resource_registry_audit"
    )
    action_resource_plan_dir = (
        out_dir / "formalization_gap_planner_action_resource_plan"
    )
    resource_request_queue_dir = (
        out_dir / "formalization_gap_planner_resource_request_queue"
    )
    resource_response_ledger_dir = (
        out_dir / "formalization_gap_planner_resource_response_ledger"
    )
    refinement_queue_dir = out_dir / "formalization_gap_planner_refinement_queue"
    refinement_adapter_dir = out_dir / "formalization_gap_planner_refinement_adapter"
    minimal_delta_audit_feedback_adapter_dir = (
        out_dir / "formalization_gap_planner_minimal_delta_audit_feedback_adapter"
    )
    local_literature_adapter_dir = (
        out_dir / "formalization_gap_planner_local_literature_adapter"
    )
    local_formal_source_adapter_dir = (
        out_dir / "formalization_gap_planner_local_formal_source_adapter"
    )
    local_proof_state_adapter_dir = (
        out_dir / "formalization_gap_planner_local_proof_state_adapter"
    )
    prover_adapter_feedback_adapter_dir = (
        out_dir / "formalization_gap_planner_prover_adapter_feedback_adapter"
    )
    refinement_evidence_dir = out_dir / "formalization_gap_planner_refinement_evidence"
    route_revision_overlay_dir = (
        out_dir / "formalization_gap_planner_route_revision_overlay"
    )
    route_stability_audit_dir = (
        out_dir / "formalization_gap_planner_route_stability_audit"
    )
    route_replan_handoff_dir = (
        out_dir / "formalization_gap_planner_route_replan_handoff"
    )
    route_replan_handoff_audit_dir = (
        out_dir / "formalization_gap_planner_route_replan_handoff_audit"
    )
    feedback_llm_route_planner_dir = (
        out_dir / "formalization_gap_planner_feedback_llm_route_planner"
    )
    proof_state_triage_dir = out_dir / "formalization_gap_planner_proof_state_triage"
    interactive_session_dir = (
        out_dir / "formalization_gap_planner_interactive_session"
    )
    ablation_study_dir = out_dir / "formalization_gap_planner_ablation_study"
    cross_prover_matrix_audit_dir = (
        out_dir / "formalization_gap_planner_cross_prover_matrix_audit"
    )
    publication_bundle_dir = out_dir / "formalization_gap_planner_publication_bundle"
    publication_bundle_audit_dir = (
        out_dir / "formalization_gap_planner_publication_bundle_audit"
    )
    llm_response_payload_validation_dir = (
        out_dir
        / "formalization_gap_planner_llm_route_planner_response_payload_validation"
    )

    adapter_registry_payload = export_formalization_gap_planner_adapter_registry(
        adapter_registry_dir,
        lean_rag_db_path=lean_rag_db_path,
        paper_library_dir=paper_library_dir,
    )
    adapter_registry_audit_payload = audit_formalization_gap_planner_adapter_registry(
        adapter_registry_dir,
        adapter_registry_audit_dir,
    )
    component_resource_registry_payload = (
        export_formalization_gap_planner_component_resource_registry(
            component_resource_registry_dir,
            formalization_gap_planner_adapter_registry_dir=adapter_registry_dir,
        )
    )
    component_resource_registry_audit_payload = (
        audit_formalization_gap_planner_component_resource_registry(
            component_resource_registry_dir,
            component_resource_registry_audit_dir,
        )
    )

    intake_payload = normalize_formalization_gap_planner_target_intake(
        target_intake_input,
        target_intake_dir,
    )
    standalone_seed_path = (
        target_intake_dir / "formalization_gap_planner_target_intake_standalone_seed.json"
    )
    llm_route_planner_payload = export_formalization_gap_planner_llm_route_planner(
        standalone_seed_path,
        llm_route_planner_dir,
        provider_name=llm_route_planner_provider,
        model=llm_route_planner_model,
        model_tier=llm_route_planner_model_tier,
        max_tokens=llm_route_planner_max_tokens,
        max_repair_attempts=llm_route_planner_max_repair_attempts,
        temperature=llm_route_planner_temperature,
        invoke_provider=llm_route_planner_invoke_provider,
        response_json=llm_route_planner_response_json,
        static_response_json=llm_route_planner_static_response_json,
        formalization_gap_planner_target_intake_dir=target_intake_dir,
        formalization_gap_planner_component_resource_registry_dir=(
            component_resource_registry_dir
        ),
    )
    llm_route_planner_seed_path = (
        llm_route_planner_dir
        / "formalization_gap_planner_llm_route_planner_standalone_seed.json"
    )
    plan_payload = export_formalization_gap_planner_standalone_plan(
        llm_route_planner_seed_path,
        plan_dir,
        max_routes=max_routes,
    )
    portable_plan_audit_payload = audit_formalization_gap_planner_portable_plan(
        plan_dir,
        portable_plan_audit_dir,
    )
    library_coverage_map_payload = (
        export_formalization_gap_planner_library_coverage_map(
            plan_dir,
            library_coverage_map_dir,
        )
    )
    primitive_action_queue_payload = (
        export_formalization_gap_planner_primitive_action_queue(
            library_coverage_map_dir,
            primitive_action_queue_dir,
        )
    )
    minimal_delta_audit_payload = audit_formalization_gap_planner_minimal_delta(
        plan_dir,
        minimal_delta_audit_dir,
    )
    source_grounding_audit_payload = audit_formalization_gap_planner_source_grounding(
        plan_dir,
        source_grounding_audit_dir,
    )
    evaluation_ground_truth_path, evaluation_ground_truth_mode = (
        _evaluation_ground_truth_path(
            plan_payload,
            out_dir,
            supplied_ground_truth_path=ground_truth_path,
        )
    )
    evaluation_payload = evaluate_formalization_gap_planner(
        plan_dir,
        evaluation_ground_truth_path,
        evaluation_dir,
    )
    adapter_snapshot_ref = (
        target_library_snapshot_ref
        or f"{target_prover_family}:formalization_gap_planner_reuse_smoke"
    )
    prover_adapter_contract_payload = (
        export_formalization_gap_planner_prover_adapter_contract(
            plan_dir,
            prover_adapter_contract_dir,
            target_prover_family=target_prover_family,
            library_snapshot_ref=adapter_snapshot_ref,
        )
    )
    cross_prover_matrix_payload = audit_formalization_gap_planner_cross_prover_matrix(
        plan_dir,
        cross_prover_matrix_audit_dir,
        target_prover_families=DEFAULT_REUSE_TARGETS,
        library_snapshot_ref_prefix="formalization_gap_planner_reuse_smoke",
    )
    action_resource_plan_payload = (
        export_formalization_gap_planner_action_resource_plan(
            primitive_action_queue_dir,
            component_resource_registry_dir,
            action_resource_plan_dir,
        )
    )
    resource_request_queue_payload = (
        export_formalization_gap_planner_resource_request_queue(
            action_resource_plan_dir,
            resource_request_queue_dir,
        )
    )
    resource_response_ledger_payload = (
        export_formalization_gap_planner_resource_response_ledger(
            resource_request_queue_dir,
            resource_response_ledger_dir,
        )
    )
    refinement_queue_payload = export_formalization_gap_planner_refinement_queue(
        plan_dir,
        refinement_queue_dir,
    )
    refinement_adapter_payload = (
        export_formalization_gap_planner_refinement_adapter_responses(
            refinement_queue_dir,
            refinement_adapter_dir,
            ground_truth_path=ground_truth_path,
        )
    )
    refinement_response_jsonl = (
        refinement_adapter_dir
        / "formalization_gap_planner_refinement_evidence_responses.jsonl"
    )
    minimal_delta_audit_feedback_adapter_payload = (
        export_formalization_gap_planner_minimal_delta_audit_feedback_responses(
            refinement_queue_dir,
            minimal_delta_audit_dir,
            minimal_delta_audit_feedback_adapter_dir,
            base_response_jsonl=refinement_response_jsonl,
        )
    )
    minimal_delta_audit_feedback_response_jsonl = (
        minimal_delta_audit_feedback_adapter_dir
        / "formalization_gap_planner_refinement_evidence_responses.jsonl"
    )
    local_literature_adapter_payload = (
        export_formalization_gap_planner_local_literature_adapter_responses(
            refinement_queue_dir,
            local_literature_adapter_dir,
            literature_roots=(paper_library_dir,) if paper_library_dir else tuple(),
            base_response_jsonl=minimal_delta_audit_feedback_response_jsonl,
        )
    )
    local_literature_response_jsonl = (
        local_literature_adapter_dir
        / "formalization_gap_planner_refinement_evidence_responses.jsonl"
    )
    local_formal_source_adapter_payload = (
        export_formalization_gap_planner_local_formal_source_adapter_responses(
            refinement_queue_dir,
            local_formal_source_adapter_dir,
            lean_rag_db_path=lean_rag_db_path,
            base_response_jsonl=local_literature_response_jsonl,
        )
    )
    local_formal_source_response_jsonl = (
        local_formal_source_adapter_dir
        / "formalization_gap_planner_refinement_evidence_responses.jsonl"
    )
    local_proof_state_adapter_payload = (
        export_formalization_gap_planner_local_proof_state_adapter_responses(
            refinement_queue_dir,
            local_proof_state_adapter_dir,
            base_response_jsonl=local_formal_source_response_jsonl,
        )
    )
    local_proof_state_response_jsonl = (
        local_proof_state_adapter_dir
        / "formalization_gap_planner_refinement_evidence_responses.jsonl"
    )
    prover_adapter_feedback_payload = (
        export_formalization_gap_planner_prover_adapter_feedback_responses(
            refinement_queue_dir,
            prover_adapter_feedback_adapter_dir,
            formalization_gap_planner_prover_adapter_contract_dir=(
                prover_adapter_contract_dir
            ),
            formalization_gap_planner_cross_prover_matrix_audit_dir=(
                cross_prover_matrix_audit_dir
            ),
            base_response_jsonl=local_proof_state_response_jsonl,
            target_prover_family=target_prover_family,
        )
    )
    prover_adapter_feedback_response_jsonl = (
        prover_adapter_feedback_adapter_dir
        / "formalization_gap_planner_refinement_evidence_responses.jsonl"
    )
    refinement_evidence_payload = export_formalization_gap_planner_refinement_evidence(
        refinement_queue_dir,
        refinement_evidence_dir,
        response_jsonl=prover_adapter_feedback_response_jsonl,
    )
    route_revision_overlay_payload = (
        export_formalization_gap_planner_route_revision_overlay(
            plan_dir,
            refinement_evidence_dir,
            route_revision_overlay_dir,
            formalization_gap_planner_resource_response_ledger_dir=(
                resource_response_ledger_dir
            ),
        )
    )
    route_stability_audit_payload = audit_formalization_gap_planner_route_stability(
        plan_dir,
        refinement_evidence_dir,
        route_revision_overlay_dir,
        route_stability_audit_dir,
    )
    route_replan_handoff_payload = export_formalization_gap_planner_route_replan_handoff(
        plan_dir,
        route_revision_overlay_dir,
        route_replan_handoff_dir,
        formalization_gap_planner_route_stability_audit_dir=route_stability_audit_dir,
    )
    route_replan_handoff_audit_payload = (
        audit_formalization_gap_planner_route_replan_handoff(
            route_replan_handoff_dir,
            route_replan_handoff_audit_dir,
        )
    )
    route_replan_seed_path = (
        route_replan_handoff_dir
        / "formalization_gap_planner_route_replan_standalone_seed.json"
    )
    proof_state_triage_payload = export_formalization_gap_planner_proof_state_triage(
        route_revision_overlay_dir,
        proof_state_triage_dir,
    )
    interactive_session_payload = (
        export_formalization_gap_planner_interactive_session(
            plan_dir,
            interactive_session_dir,
            formalization_gap_planner_refinement_queue_dir=refinement_queue_dir,
            formalization_gap_planner_refinement_evidence_dir=refinement_evidence_dir,
            formalization_gap_planner_route_stability_audit_dir=route_stability_audit_dir,
            formalization_gap_planner_route_replan_handoff_dir=route_replan_handoff_dir,
            formalization_gap_planner_proof_state_triage_dir=proof_state_triage_dir,
            formalization_gap_planner_component_resource_registry_dir=(
                component_resource_registry_dir
            ),
        )
    )
    feedback_llm_route_planner_payload = (
        export_formalization_gap_planner_llm_route_planner(
            route_replan_seed_path,
            feedback_llm_route_planner_dir,
            provider_name=feedback_llm_route_planner_provider,
            model=feedback_llm_route_planner_model,
            model_tier=feedback_llm_route_planner_model_tier,
            max_tokens=feedback_llm_route_planner_max_tokens,
            max_repair_attempts=feedback_llm_route_planner_max_repair_attempts,
            temperature=feedback_llm_route_planner_temperature,
            invoke_provider=feedback_llm_route_planner_invoke_provider,
            response_json=feedback_llm_route_planner_response_json,
            static_response_json=feedback_llm_route_planner_static_response_json,
            formalization_gap_planner_target_intake_dir=target_intake_dir,
            goal_conditioned_minimal_formalization_plan_dir=plan_dir,
            formalization_gap_planner_library_coverage_map_dir=library_coverage_map_dir,
            formalization_gap_planner_source_grounding_audit_dir=source_grounding_audit_dir,
            formalization_gap_planner_resource_request_queue_dir=resource_request_queue_dir,
            formalization_gap_planner_resource_response_ledger_dir=resource_response_ledger_dir,
            formalization_gap_planner_refinement_evidence_dir=refinement_evidence_dir,
            formalization_gap_planner_route_revision_overlay_dir=route_revision_overlay_dir,
            formalization_gap_planner_interactive_session_dir=interactive_session_dir,
            formalization_gap_planner_component_resource_registry_dir=(
                component_resource_registry_dir
            ),
        )
    )
    llm_response_payload_validation_payload = (
        _maybe_validate_llm_route_planner_response_payloads(
            (llm_route_planner_payload, feedback_llm_route_planner_payload),
            llm_response_payload_validation_dir,
        )
    )
    ablation_study_payload = export_formalization_gap_planner_ablation_study(
        plan_dir,
        evaluation_dir,
        ablation_study_dir,
        formalization_gap_planner_interactive_session_dir=interactive_session_dir,
    )
    publication_snapshot_ref = (
        str(plan_payload.get("library_snapshot_ref", "")).strip()
        or str(intake_payload.get("library_snapshot_ref", "")).strip()
        or adapter_snapshot_ref
    )
    publication_bundle_payload = export_formalization_gap_planner_publication_bundle(
        publication_bundle_dir,
        ground_truth_path=ground_truth_path,
        lean_rag_db_path=lean_rag_db_path,
        paper_library_dir=paper_library_dir,
        formalization_gap_planner_target_intake_dir=target_intake_dir,
        formalization_gap_planner_llm_route_planner_dir=llm_route_planner_dir,
        formalization_gap_planner_feedback_llm_route_planner_dir=(
            feedback_llm_route_planner_dir
        ),
        formalization_gap_planner_llm_route_planner_response_payload_validation_dir=(
            llm_response_payload_validation_dir
            if llm_response_payload_validation_payload is not None
            else None
        ),
        goal_conditioned_minimal_formalization_plan_dir=plan_dir,
        formalization_gap_planner_portable_plan_audit_dir=portable_plan_audit_dir,
        formalization_gap_planner_library_coverage_map_dir=library_coverage_map_dir,
        formalization_gap_planner_primitive_action_queue_dir=primitive_action_queue_dir,
        formalization_gap_planner_action_resource_plan_dir=action_resource_plan_dir,
        formalization_gap_planner_resource_request_queue_dir=resource_request_queue_dir,
        formalization_gap_planner_resource_response_ledger_dir=resource_response_ledger_dir,
        formalization_gap_planner_minimal_delta_audit_dir=minimal_delta_audit_dir,
        formalization_gap_planner_minimal_delta_audit_feedback_adapter_dir=(
            minimal_delta_audit_feedback_adapter_dir
        ),
        formalization_gap_planner_source_grounding_audit_dir=source_grounding_audit_dir,
        formalization_gap_planner_evaluation_dir=evaluation_dir,
        formalization_gap_planner_refinement_queue_dir=refinement_queue_dir,
        formalization_gap_planner_refinement_adapter_dir=refinement_adapter_dir,
        formalization_gap_planner_local_literature_adapter_dir=local_literature_adapter_dir,
        formalization_gap_planner_local_formal_source_adapter_dir=local_formal_source_adapter_dir,
        formalization_gap_planner_local_proof_state_adapter_dir=local_proof_state_adapter_dir,
        formalization_gap_planner_prover_adapter_feedback_adapter_dir=(
            prover_adapter_feedback_adapter_dir
        ),
        formalization_gap_planner_refinement_evidence_dir=refinement_evidence_dir,
        formalization_gap_planner_route_revision_overlay_dir=route_revision_overlay_dir,
        formalization_gap_planner_route_stability_audit_dir=route_stability_audit_dir,
        formalization_gap_planner_route_replan_handoff_dir=route_replan_handoff_dir,
        formalization_gap_planner_route_replan_handoff_audit_dir=route_replan_handoff_audit_dir,
        formalization_gap_planner_proof_state_triage_dir=proof_state_triage_dir,
        formalization_gap_planner_interactive_session_dir=interactive_session_dir,
        formalization_gap_planner_ablation_study_dir=ablation_study_dir,
        formalization_gap_planner_prover_adapter_contract_dir=prover_adapter_contract_dir,
        formalization_gap_planner_cross_prover_matrix_audit_dir=cross_prover_matrix_audit_dir,
        formalization_gap_planner_adapter_registry_audit_dir=adapter_registry_audit_dir,
        formalization_gap_planner_component_resource_registry_audit_dir=component_resource_registry_audit_dir,
        library_snapshot_ref=publication_snapshot_ref,
    )
    publication_bundle_audit_payload = audit_formalization_gap_planner_publication_bundle(
        publication_bundle_dir,
        publication_bundle_audit_dir,
    )

    stages = (
        _stage_row(
            "formalization_gap_planner_target_intake",
            target_intake_dir,
            target_intake_dir / "formalization_gap_planner_target_intake_manifest.json",
            intake_payload,
        ),
        _stage_row(
            "formalization_gap_planner_llm_route_planner",
            llm_route_planner_dir,
            llm_route_planner_dir
            / "formalization_gap_planner_llm_route_planner_manifest.json",
            llm_route_planner_payload,
        ),
        _stage_row(
            "goal_conditioned_minimal_formalization_plan",
            plan_dir,
            plan_dir / "goal_conditioned_minimal_formalization_plan_manifest.json",
            plan_payload,
        ),
        _stage_row(
            "formalization_gap_planner_portable_plan_audit",
            portable_plan_audit_dir,
            portable_plan_audit_dir
            / "formalization_gap_planner_portable_plan_audit_manifest.json",
            portable_plan_audit_payload,
        ),
        _stage_row(
            "formalization_gap_planner_library_coverage_map",
            library_coverage_map_dir,
            library_coverage_map_dir
            / "formalization_gap_planner_library_coverage_map_manifest.json",
            library_coverage_map_payload,
        ),
        _stage_row(
            "formalization_gap_planner_primitive_action_queue",
            primitive_action_queue_dir,
            primitive_action_queue_dir
            / "formalization_gap_planner_primitive_action_queue_manifest.json",
            primitive_action_queue_payload,
        ),
        _stage_row(
            "formalization_gap_planner_minimal_delta_audit",
            minimal_delta_audit_dir,
            minimal_delta_audit_dir
            / "formalization_gap_planner_minimal_delta_audit_manifest.json",
            minimal_delta_audit_payload,
        ),
        _stage_row(
            "formalization_gap_planner_source_grounding_audit",
            source_grounding_audit_dir,
            source_grounding_audit_dir
            / "formalization_gap_planner_source_grounding_audit_manifest.json",
            source_grounding_audit_payload,
        ),
        _stage_row(
            "formalization_gap_planner_evaluation",
            evaluation_dir,
            evaluation_dir / "formalization_gap_planner_evaluation_manifest.json",
            evaluation_payload,
        ),
        _stage_row(
            "formalization_gap_planner_prover_adapter_contract",
            prover_adapter_contract_dir,
            prover_adapter_contract_dir
            / "formalization_gap_planner_prover_adapter_contract_manifest.json",
            prover_adapter_contract_payload,
        ),
        _stage_row(
            "formalization_gap_planner_adapter_registry",
            adapter_registry_dir,
            adapter_registry_dir
            / "formalization_gap_planner_adapter_registry_manifest.json",
            adapter_registry_payload,
        ),
        _stage_row(
            "formalization_gap_planner_adapter_registry_audit",
            adapter_registry_audit_dir,
            adapter_registry_audit_dir
            / "formalization_gap_planner_adapter_registry_audit_manifest.json",
            adapter_registry_audit_payload,
        ),
        _stage_row(
            "formalization_gap_planner_component_resource_registry",
            component_resource_registry_dir,
            component_resource_registry_dir
            / "formalization_gap_planner_component_resource_registry_manifest.json",
            component_resource_registry_payload,
        ),
        _stage_row(
            "formalization_gap_planner_component_resource_registry_audit",
            component_resource_registry_audit_dir,
            component_resource_registry_audit_dir
            / "formalization_gap_planner_component_resource_registry_audit_manifest.json",
            component_resource_registry_audit_payload,
        ),
        _stage_row(
            "formalization_gap_planner_action_resource_plan",
            action_resource_plan_dir,
            action_resource_plan_dir
            / "formalization_gap_planner_action_resource_plan_manifest.json",
            action_resource_plan_payload,
        ),
        _stage_row(
            "formalization_gap_planner_resource_request_queue",
            resource_request_queue_dir,
            resource_request_queue_dir
            / "formalization_gap_planner_resource_request_queue_manifest.json",
            resource_request_queue_payload,
        ),
        _stage_row(
            "formalization_gap_planner_resource_response_ledger",
            resource_response_ledger_dir,
            resource_response_ledger_dir
            / "formalization_gap_planner_resource_response_ledger_manifest.json",
            resource_response_ledger_payload,
        ),
        _stage_row(
            "formalization_gap_planner_refinement_queue",
            refinement_queue_dir,
            refinement_queue_dir
            / "formalization_gap_planner_refinement_queue_manifest.json",
            refinement_queue_payload,
        ),
        _stage_row(
            "formalization_gap_planner_refinement_adapter_responses",
            refinement_adapter_dir,
            refinement_adapter_dir
            / "formalization_gap_planner_refinement_adapter_manifest.json",
            refinement_adapter_payload,
        ),
        _stage_row(
            "formalization_gap_planner_minimal_delta_audit_feedback_adapter",
            minimal_delta_audit_feedback_adapter_dir,
            minimal_delta_audit_feedback_adapter_dir
            / "formalization_gap_planner_minimal_delta_audit_feedback_adapter_manifest.json",
            minimal_delta_audit_feedback_adapter_payload,
        ),
        _stage_row(
            "formalization_gap_planner_local_literature_adapter",
            local_literature_adapter_dir,
            local_literature_adapter_dir
            / "formalization_gap_planner_local_literature_adapter_manifest.json",
            local_literature_adapter_payload,
        ),
        _stage_row(
            "formalization_gap_planner_local_formal_source_adapter",
            local_formal_source_adapter_dir,
            local_formal_source_adapter_dir
            / "formalization_gap_planner_local_formal_source_adapter_manifest.json",
            local_formal_source_adapter_payload,
        ),
        _stage_row(
            "formalization_gap_planner_local_proof_state_adapter",
            local_proof_state_adapter_dir,
            local_proof_state_adapter_dir
            / "formalization_gap_planner_local_proof_state_adapter_manifest.json",
            local_proof_state_adapter_payload,
        ),
        _stage_row(
            "formalization_gap_planner_prover_adapter_feedback_adapter",
            prover_adapter_feedback_adapter_dir,
            prover_adapter_feedback_adapter_dir
            / "formalization_gap_planner_prover_adapter_feedback_adapter_manifest.json",
            prover_adapter_feedback_payload,
        ),
        _stage_row(
            "formalization_gap_planner_refinement_evidence",
            refinement_evidence_dir,
            refinement_evidence_dir
            / "formalization_gap_planner_refinement_evidence_manifest.json",
            refinement_evidence_payload,
        ),
        _stage_row(
            "formalization_gap_planner_route_revision_overlay",
            route_revision_overlay_dir,
            route_revision_overlay_dir
            / "formalization_gap_planner_route_revision_overlay_manifest.json",
            route_revision_overlay_payload,
        ),
        _stage_row(
            "formalization_gap_planner_route_stability_audit",
            route_stability_audit_dir,
            route_stability_audit_dir
            / "formalization_gap_planner_route_stability_audit_manifest.json",
            route_stability_audit_payload,
        ),
        _stage_row(
            "formalization_gap_planner_route_replan_handoff",
            route_replan_handoff_dir,
            route_replan_handoff_dir
            / "formalization_gap_planner_route_replan_handoff_manifest.json",
            route_replan_handoff_payload,
        ),
        _stage_row(
            "formalization_gap_planner_route_replan_handoff_audit",
            route_replan_handoff_audit_dir,
            route_replan_handoff_audit_dir
            / "formalization_gap_planner_route_replan_handoff_audit_manifest.json",
            route_replan_handoff_audit_payload,
        ),
        _stage_row(
            "formalization_gap_planner_feedback_llm_route_planner",
            feedback_llm_route_planner_dir,
            feedback_llm_route_planner_dir
            / "formalization_gap_planner_llm_route_planner_manifest.json",
            feedback_llm_route_planner_payload,
        ),
        *(
            (
                _stage_row(
                    "formalization_gap_planner_llm_route_planner_response_payload_validation",
                    llm_response_payload_validation_dir,
                    llm_response_payload_validation_dir
                    / "formalization_gap_planner_llm_route_planner_response_payload_validation_manifest.json",
                    llm_response_payload_validation_payload,
                ),
            )
            if llm_response_payload_validation_payload is not None
            else ()
        ),
        _stage_row(
            "formalization_gap_planner_proof_state_triage",
            proof_state_triage_dir,
            proof_state_triage_dir
            / "formalization_gap_planner_proof_state_triage_manifest.json",
            proof_state_triage_payload,
        ),
        _stage_row(
            "formalization_gap_planner_interactive_session",
            interactive_session_dir,
            interactive_session_dir
            / "formalization_gap_planner_interactive_session_manifest.json",
            interactive_session_payload,
        ),
        _stage_row(
            "formalization_gap_planner_ablation_study",
            ablation_study_dir,
            ablation_study_dir
            / "formalization_gap_planner_ablation_study_manifest.json",
            ablation_study_payload,
        ),
        _stage_row(
            "formalization_gap_planner_cross_prover_matrix_audit",
            cross_prover_matrix_audit_dir,
            cross_prover_matrix_audit_dir
            / "formalization_gap_planner_cross_prover_matrix_audit_manifest.json",
            cross_prover_matrix_payload,
        ),
        _stage_row(
            "formalization_gap_planner_publication_bundle",
            publication_bundle_dir,
            publication_bundle_dir
            / "formalization_gap_planner_publication_bundle_manifest.json",
            publication_bundle_payload,
        ),
        _stage_row(
            "formalization_gap_planner_publication_bundle_audit",
            publication_bundle_audit_dir,
            publication_bundle_audit_dir
            / "formalization_gap_planner_publication_bundle_audit_manifest.json",
            publication_bundle_audit_payload,
        ),
    )
    stage_dicts = [asdict(stage) for stage in stages]
    stage_errors = [
        f"{stage.stage_name}: {error}"
        for stage in stages
        for error in stage.errors
    ]
    publication_bundle_llm_route_planner_summary = (
        publication_bundle_payload.get("llm_route_planner_summary", {})
        if isinstance(
            publication_bundle_payload.get("llm_route_planner_summary"),
            dict,
        )
        else {}
    )
    publication_bundle_feedback_llm_route_planner_summary = (
        publication_bundle_payload.get("feedback_llm_route_planner_summary", {})
        if isinstance(
            publication_bundle_payload.get("feedback_llm_route_planner_summary"),
            dict,
        )
        else {}
    )
    payload: dict[str, object] = {
        "schema_version": FORMALIZATION_GAP_PLANNER_REUSE_SMOKE_SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "component_name": FORMALIZATION_GAP_PLANNER_REUSE_SMOKE_COMPONENT,
        "target_intake_input": str(target_intake_input),
        "out_dir": str(out_dir),
        "evaluation_ground_truth_path": str(evaluation_ground_truth_path),
        "evaluation_ground_truth_mode": evaluation_ground_truth_mode,
        "target_prover_family": str(
            prover_adapter_contract_payload.get("target_prover_family", target_prover_family)
        ),
        "source_target_prover_family": str(
            plan_payload.get("target_prover_family", "")
        ),
        "n_source_target_prover_families": plan_payload.get(
            "n_target_prover_families",
            0,
        ),
        "source_by_target_prover_family": plan_payload.get(
            "by_target_prover_family",
            {},
        ),
        "source_library_snapshot_ref": str(plan_payload.get("library_snapshot_ref", "")),
        "target_library_snapshot_ref": adapter_snapshot_ref,
        "publication_library_snapshot_ref": publication_snapshot_ref,
        "n_goal_plan_standalone_input_traces_with_llm_route_planner_metadata": (
            plan_payload.get(
                "n_standalone_input_traces_with_llm_route_planner_metadata",
                0,
            )
        ),
        "n_goal_plan_standalone_input_traces_with_llm_model_tier": (
            plan_payload.get(
                "n_standalone_input_traces_with_llm_model_tier",
                0,
            )
        ),
        "goal_plan_standalone_input_trace_by_llm_model_tier": plan_payload.get(
            "standalone_input_trace_by_llm_model_tier",
            {},
        ),
        "n_goal_plan_standalone_input_traces_with_llm_generator_metadata": (
            plan_payload.get(
                "n_standalone_input_traces_with_llm_generator_metadata",
                0,
            )
        ),
        "n_goal_plan_standalone_input_traces_with_llm_route_adoption_status": (
            plan_payload.get(
                "n_standalone_input_traces_with_llm_route_adoption_status",
                0,
            )
        ),
        "goal_plan_standalone_input_trace_by_llm_route_adoption_status": (
            plan_payload.get(
                "standalone_input_trace_by_llm_route_adoption_status",
                {},
            )
        ),
        "n_goal_plan_standalone_input_traces_ready_for_route_adoption": (
            plan_payload.get(
                "n_standalone_input_traces_ready_for_route_adoption",
                0,
            )
        ),
        "n_goal_plan_standalone_input_traces_pending_refinement_before_route_adoption": (
            plan_payload.get(
                "n_standalone_input_traces_pending_refinement_before_route_adoption",
                0,
            )
        ),
        "n_goal_plan_standalone_input_trace_route_adoption_blockers": (
            plan_payload.get(
                "n_standalone_input_trace_route_adoption_blockers",
                0,
            )
        ),
        "n_goal_plan_standalone_input_traces_with_llm_seed_selection": (
            plan_payload.get(
                "n_standalone_input_traces_with_llm_seed_selection",
                0,
            )
        ),
        "n_goal_plan_standalone_input_traces_llm_seed_selected": (
            plan_payload.get(
                "n_standalone_input_traces_llm_seed_selected",
                0,
            )
        ),
        "n_goal_plan_standalone_input_traces_llm_seed_adoptable_for_standalone_replay": (
            plan_payload.get(
                "n_standalone_input_traces_llm_seed_adoptable_for_standalone_replay",
                0,
            )
        ),
        "n_goal_plan_standalone_input_traces_llm_seed_selected_not_adoptable": (
            plan_payload.get(
                "n_standalone_input_traces_llm_seed_selected_not_adoptable",
                0,
            )
        ),
        "goal_plan_standalone_input_trace_by_llm_seed_selection_rank": (
            plan_payload.get(
                "standalone_input_trace_by_llm_seed_selection_rank",
                {},
            )
        ),
        "n_goal_plan_standalone_input_traces_with_llm_seed_minimal_delta_route_cost": (
            plan_payload.get(
                "n_standalone_input_traces_with_llm_seed_minimal_delta_route_cost",
                0,
            )
        ),
        "max_routes": max_routes,
        "llm_route_planner_provider": llm_route_planner_provider,
        "llm_route_planner_model": str(llm_route_planner_payload.get("model", "")),
        "llm_route_planner_invoke_provider": llm_route_planner_invoke_provider,
        "llm_route_planner_provider_execution_mode": (
            _llm_provider_execution_mode(
                llm_route_planner_provider,
                invoke_provider=llm_route_planner_invoke_provider,
            )
        ),
        "n_llm_route_planner_live_provider_calls_requested": (
            _llm_live_provider_call_count(
                llm_route_planner_payload,
                provider_name=llm_route_planner_provider,
                invoke_provider=llm_route_planner_invoke_provider,
            )
        ),
        "feedback_llm_route_planner_provider": feedback_llm_route_planner_provider,
        "feedback_llm_route_planner_model": str(
            feedback_llm_route_planner_payload.get("model", "")
        ),
        "feedback_llm_route_planner_invoke_provider": (
            feedback_llm_route_planner_invoke_provider
        ),
        "feedback_llm_route_planner_provider_execution_mode": (
            _llm_provider_execution_mode(
                feedback_llm_route_planner_provider,
                invoke_provider=feedback_llm_route_planner_invoke_provider,
            )
        ),
        "n_feedback_llm_route_planner_live_provider_calls_requested": (
            _llm_live_provider_call_count(
                feedback_llm_route_planner_payload,
                provider_name=feedback_llm_route_planner_provider,
                invoke_provider=feedback_llm_route_planner_invoke_provider,
            )
        ),
        "has_llm_route_planner_response_payload_validation": (
            llm_response_payload_validation_payload is not None
        ),
        "n_llm_route_planner_response_payload_validation_payloads": (
            _optional_int(
                llm_response_payload_validation_payload,
                "n_payloads",
            )
        ),
        "n_llm_route_planner_response_payload_validation_valid_payloads": (
            _optional_int(
                llm_response_payload_validation_payload,
                "n_valid_payloads",
            )
        ),
        "n_llm_route_planner_response_payload_validation_invalid_payloads": (
            _optional_int(
                llm_response_payload_validation_payload,
                "n_invalid_payloads",
            )
        ),
        "n_llm_route_planner_response_payload_validation_request_context_packets": (
            _optional_int(
                llm_response_payload_validation_payload,
                "n_request_context_packets",
            )
        ),
        "n_llm_route_planner_response_payload_validation_request_context_inventories": (
            _optional_int(
                llm_response_payload_validation_payload,
                "n_request_contexts_with_context_packet_inventory",
            )
        ),
        "n_llm_route_planner_response_payload_validation_request_context_inventory_total_rows": (
            _optional_int(
                llm_response_payload_validation_payload,
                "n_request_context_inventory_total_rows",
            )
        ),
        "n_llm_route_planner_response_payload_validation_request_bound_payloads": (
            _optional_int(
                llm_response_payload_validation_payload,
                "n_request_bound_payloads",
            )
        ),
        "n_llm_route_planner_response_payload_validation_request_bound_payloads_with_context_inventory": (
            _optional_int(
                llm_response_payload_validation_payload,
                "n_request_bound_payloads_with_context_packet_inventory",
            )
        ),
        "n_llm_route_planner_response_payload_validation_request_bound_context_inventory_total_rows": (
            _optional_int(
                llm_response_payload_validation_payload,
                "n_request_bound_payload_context_inventory_total_rows",
            )
        ),
        "n_llm_route_planner_response_payload_validation_declared_target_prover_payloads": (
            _optional_int(
                llm_response_payload_validation_payload,
                "n_payloads_with_declared_target_prover_family",
            )
        ),
        "n_llm_route_planner_response_payload_validation_target_prover_mismatches": (
            _optional_int(
                llm_response_payload_validation_payload,
                "n_request_bound_payloads_with_target_prover_family_mismatch",
            )
        ),
        "llm_route_planner_response_payload_validation_by_payload_target_prover_family": (
            _optional_dict(
                llm_response_payload_validation_payload,
                "by_payload_target_prover_family",
            )
        ),
        "llm_route_planner_response_payload_validation_by_request_context_target_prover_family": (
            _optional_dict(
                llm_response_payload_validation_payload,
                "by_request_context_target_prover_family",
            )
        ),
        "n_llm_route_planner_response_payload_validation_schema_errors": (
            _optional_int(
                llm_response_payload_validation_payload,
                "n_schema_errors",
            )
        ),
        "n_llm_route_planner_response_payload_validation_request_context_errors": (
            _optional_int(
                llm_response_payload_validation_payload,
                "n_request_context_errors",
            )
        ),
        "n_total_llm_route_planner_live_provider_calls_requested": (
            _llm_live_provider_call_count(
                llm_route_planner_payload,
                provider_name=llm_route_planner_provider,
                invoke_provider=llm_route_planner_invoke_provider,
            )
            + _llm_live_provider_call_count(
                feedback_llm_route_planner_payload,
                provider_name=feedback_llm_route_planner_provider,
                invoke_provider=feedback_llm_route_planner_invoke_provider,
            )
        ),
        "n_stages": len(stages),
        "n_ok": sum(1 for stage in stages if stage.ok),
        "n_failed": sum(1 for stage in stages if not stage.ok),
        "n_proof_boundary_ok": sum(1 for stage in stages if stage.proof_boundary_ok),
        "n_publication_bundle_audit_checks": publication_bundle_audit_payload.get(
            "n_checks",
            0,
        ),
        "n_publication_bundle_audit_failed": publication_bundle_audit_payload.get(
            "n_failed",
            0,
        ),
        "n_publication_bundle_schema_catalog_entries": (
            publication_bundle_payload.get("schema_catalog_summary", {}).get(
                "n_schema_entries",
                0,
            )
            if isinstance(
                publication_bundle_payload.get("schema_catalog_summary"), dict
            )
            else 0
        ),
        "n_publication_bundle_schema_catalog_contract_errors": (
            publication_bundle_payload.get("schema_catalog_summary", {}).get(
                "n_schema_catalog_contract_errors",
                0,
            )
            if isinstance(
                publication_bundle_payload.get("schema_catalog_summary"), dict
            )
            else 0
        ),
        "publication_bundle_schema_catalog_all_ok": (
            bool(
                publication_bundle_payload.get("schema_catalog_summary", {}).get(
                    "all_ok",
                    False,
                )
            )
            if isinstance(
                publication_bundle_payload.get("schema_catalog_summary"), dict
            )
            else False
        ),
        "publication_bundle_llm_route_planner_summary_requested": bool(
            publication_bundle_llm_route_planner_summary.get("requested", False)
        ),
        "n_publication_bundle_llm_route_planner_summary_request_packets": (
            publication_bundle_llm_route_planner_summary.get("n_request_packets", 0)
        ),
        "n_publication_bundle_llm_route_planner_summary_context_packet_inventories": (
            publication_bundle_llm_route_planner_summary.get(
                "n_requests_with_context_packet_inventory",
                0,
            )
        ),
        "n_publication_bundle_llm_route_planner_summary_context_inventory_total_rows": (
            publication_bundle_llm_route_planner_summary.get(
                "n_request_context_inventory_total_rows",
                0,
            )
        ),
        "n_publication_bundle_llm_route_planner_summary_rows_with_context_packet_inventory": (
            publication_bundle_llm_route_planner_summary.get(
                "n_rows_with_context_packet_inventory",
                0,
            )
        ),
        "n_publication_bundle_llm_route_planner_summary_quality_control_obligation_inventories": (
            publication_bundle_llm_route_planner_summary.get(
                "n_requests_with_quality_control_obligation_inventory",
                0,
            )
        ),
        "n_publication_bundle_llm_route_planner_summary_pending_quality_control_obligation_inventories": (
            publication_bundle_llm_route_planner_summary.get(
                "n_requests_with_pending_quality_control_obligation_inventory",
                0,
            )
        ),
        "n_publication_bundle_llm_route_planner_summary_request_quality_control_obligation_fields": (
            publication_bundle_llm_route_planner_summary.get(
                "n_request_quality_control_obligation_fields",
                0,
            )
        ),
        "n_publication_bundle_llm_route_planner_summary_request_quality_control_obligation_values": (
            publication_bundle_llm_route_planner_summary.get(
                "n_request_quality_control_obligation_values",
                0,
            )
        ),
        "n_publication_bundle_llm_route_planner_summary_request_pending_quality_control_fields": (
            publication_bundle_llm_route_planner_summary.get(
                "n_request_pending_quality_control_fields",
                0,
            )
        ),
        "n_publication_bundle_llm_route_planner_summary_request_pending_quality_control_values": (
            publication_bundle_llm_route_planner_summary.get(
                "n_request_pending_quality_control_values",
                0,
            )
        ),
        "n_publication_bundle_llm_route_planner_summary_request_discharged_quality_control_fields": (
            publication_bundle_llm_route_planner_summary.get(
                "n_request_discharged_quality_control_fields",
                0,
            )
        ),
        "n_publication_bundle_llm_route_planner_summary_request_discharged_quality_control_values": (
            publication_bundle_llm_route_planner_summary.get(
                "n_request_discharged_quality_control_values",
                0,
            )
        ),
        "n_publication_bundle_llm_route_planner_summary_prior_llm_hook_traces": (
            publication_bundle_llm_route_planner_summary.get(
                "n_feedback_loop_summary_prior_llm_route_planner_hook_traces",
                0,
            )
        ),
        "n_publication_bundle_llm_route_planner_summary_requests_with_prior_llm_hook_traces": (
            publication_bundle_llm_route_planner_summary.get(
                "n_requests_with_feedback_loop_summary_prior_llm_route_planner_hook_traces",
                0,
            )
        ),
        "n_publication_bundle_llm_route_planner_summary_rows": (
            publication_bundle_llm_route_planner_summary.get("n_rows", 0)
        ),
        "n_publication_bundle_llm_route_planner_summary_response_present": (
            publication_bundle_llm_route_planner_summary.get("n_response_present", 0)
        ),
        "n_publication_bundle_llm_route_planner_summary_response_contract_ok": (
            publication_bundle_llm_route_planner_summary.get(
                "n_response_contract_ok",
                0,
            )
        ),
        "n_publication_bundle_llm_route_planner_summary_informal_knowledge_dag_nodes": (
            publication_bundle_llm_route_planner_summary.get(
                "n_informal_knowledge_dag_nodes",
                0,
            )
        ),
        "n_publication_bundle_llm_route_planner_summary_formal_realization_dag_nodes": (
            publication_bundle_llm_route_planner_summary.get(
                "n_formal_realization_dag_nodes",
                0,
            )
        ),
        "n_publication_bundle_llm_route_planner_summary_lean_realization_dag_nodes": (
            publication_bundle_llm_route_planner_summary.get(
                "n_lean_realization_dag_nodes",
                0,
            )
        ),
        "n_publication_bundle_llm_route_planner_summary_route_alignment_edges": (
            publication_bundle_llm_route_planner_summary.get(
                "n_route_alignment_edges",
                0,
            )
        ),
        "n_publication_bundle_llm_route_planner_summary_accepted_route_plans": (
            publication_bundle_llm_route_planner_summary.get(
                "n_accepted_route_plans",
                0,
            )
        ),
        "n_publication_bundle_llm_route_planner_summary_route_adoption_ready": (
            publication_bundle_llm_route_planner_summary.get(
                "n_route_adoption_ready",
                0,
            )
        ),
        "n_publication_bundle_llm_route_planner_summary_route_adoption_pending_refinement": (
            publication_bundle_llm_route_planner_summary.get(
                "n_route_adoption_pending_refinement",
                0,
            )
        ),
        "n_publication_bundle_llm_route_planner_summary_route_adoption_pending_formal_gap_boundary_blockers": (
            publication_bundle_llm_route_planner_summary.get(
                "n_route_adoption_pending_formal_gap_boundary_blockers",
                0,
            )
        ),
        "n_publication_bundle_llm_route_planner_summary_route_adoption_blockers": (
            publication_bundle_llm_route_planner_summary.get(
                "n_route_adoption_blockers",
                0,
            )
        ),
        "publication_bundle_llm_route_planner_summary_route_adoption_blocker_counts": (
            publication_bundle_llm_route_planner_summary.get(
                "route_adoption_blocker_counts",
                {},
            )
        ),
        "publication_bundle_llm_route_planner_summary_by_route_adoption_status": (
            publication_bundle_llm_route_planner_summary.get(
                "by_route_adoption_status",
                {},
            )
        ),
        "publication_bundle_llm_route_planner_summary_by_route_adoption_blocker": (
            publication_bundle_llm_route_planner_summary.get(
                "by_route_adoption_blocker",
                {},
            )
        ),
        "publication_bundle_feedback_llm_route_planner_summary_requested": bool(
            publication_bundle_feedback_llm_route_planner_summary.get(
                "requested",
                False,
            )
        ),
        "n_publication_bundle_feedback_llm_route_planner_summary_request_packets": (
            publication_bundle_feedback_llm_route_planner_summary.get(
                "n_request_packets",
                0,
            )
        ),
        "n_publication_bundle_feedback_llm_route_planner_summary_context_packet_inventories": (
            publication_bundle_feedback_llm_route_planner_summary.get(
                "n_requests_with_context_packet_inventory",
                0,
            )
        ),
        "n_publication_bundle_feedback_llm_route_planner_summary_context_inventory_total_rows": (
            publication_bundle_feedback_llm_route_planner_summary.get(
                "n_request_context_inventory_total_rows",
                0,
            )
        ),
        "n_publication_bundle_feedback_llm_route_planner_summary_rows_with_context_packet_inventory": (
            publication_bundle_feedback_llm_route_planner_summary.get(
                "n_rows_with_context_packet_inventory",
                0,
            )
        ),
        "n_publication_bundle_feedback_llm_route_planner_summary_quality_control_obligation_inventories": (
            publication_bundle_feedback_llm_route_planner_summary.get(
                "n_requests_with_quality_control_obligation_inventory",
                0,
            )
        ),
        "n_publication_bundle_feedback_llm_route_planner_summary_pending_quality_control_obligation_inventories": (
            publication_bundle_feedback_llm_route_planner_summary.get(
                "n_requests_with_pending_quality_control_obligation_inventory",
                0,
            )
        ),
        "n_publication_bundle_feedback_llm_route_planner_summary_request_quality_control_obligation_fields": (
            publication_bundle_feedback_llm_route_planner_summary.get(
                "n_request_quality_control_obligation_fields",
                0,
            )
        ),
        "n_publication_bundle_feedback_llm_route_planner_summary_request_quality_control_obligation_values": (
            publication_bundle_feedback_llm_route_planner_summary.get(
                "n_request_quality_control_obligation_values",
                0,
            )
        ),
        "n_publication_bundle_feedback_llm_route_planner_summary_request_pending_quality_control_fields": (
            publication_bundle_feedback_llm_route_planner_summary.get(
                "n_request_pending_quality_control_fields",
                0,
            )
        ),
        "n_publication_bundle_feedback_llm_route_planner_summary_request_pending_quality_control_values": (
            publication_bundle_feedback_llm_route_planner_summary.get(
                "n_request_pending_quality_control_values",
                0,
            )
        ),
        "n_publication_bundle_feedback_llm_route_planner_summary_request_discharged_quality_control_fields": (
            publication_bundle_feedback_llm_route_planner_summary.get(
                "n_request_discharged_quality_control_fields",
                0,
            )
        ),
        "n_publication_bundle_feedback_llm_route_planner_summary_request_discharged_quality_control_values": (
            publication_bundle_feedback_llm_route_planner_summary.get(
                "n_request_discharged_quality_control_values",
                0,
            )
        ),
        "n_publication_bundle_feedback_llm_route_planner_summary_prior_llm_hook_traces": (
            publication_bundle_feedback_llm_route_planner_summary.get(
                "n_feedback_loop_summary_prior_llm_route_planner_hook_traces",
                0,
            )
        ),
        "n_publication_bundle_feedback_llm_route_planner_summary_requests_with_prior_llm_hook_traces": (
            publication_bundle_feedback_llm_route_planner_summary.get(
                "n_requests_with_feedback_loop_summary_prior_llm_route_planner_hook_traces",
                0,
            )
        ),
        "n_publication_bundle_feedback_llm_route_planner_summary_rows": (
            publication_bundle_feedback_llm_route_planner_summary.get("n_rows", 0)
        ),
        "n_publication_bundle_feedback_llm_route_planner_summary_response_present": (
            publication_bundle_feedback_llm_route_planner_summary.get(
                "n_response_present",
                0,
            )
        ),
        "n_publication_bundle_feedback_llm_route_planner_summary_response_contract_ok": (
            publication_bundle_feedback_llm_route_planner_summary.get(
                "n_response_contract_ok",
                0,
            )
        ),
        "n_publication_bundle_feedback_llm_route_planner_summary_informal_knowledge_dag_nodes": (
            publication_bundle_feedback_llm_route_planner_summary.get(
                "n_informal_knowledge_dag_nodes",
                0,
            )
        ),
        "n_publication_bundle_feedback_llm_route_planner_summary_formal_realization_dag_nodes": (
            publication_bundle_feedback_llm_route_planner_summary.get(
                "n_formal_realization_dag_nodes",
                0,
            )
        ),
        "n_publication_bundle_feedback_llm_route_planner_summary_lean_realization_dag_nodes": (
            publication_bundle_feedback_llm_route_planner_summary.get(
                "n_lean_realization_dag_nodes",
                0,
            )
        ),
        "n_publication_bundle_feedback_llm_route_planner_summary_route_alignment_edges": (
            publication_bundle_feedback_llm_route_planner_summary.get(
                "n_route_alignment_edges",
                0,
            )
        ),
        "n_publication_bundle_feedback_llm_route_planner_summary_accepted_route_plans": (
            publication_bundle_feedback_llm_route_planner_summary.get(
                "n_accepted_route_plans",
                0,
            )
        ),
        "n_publication_bundle_feedback_llm_route_planner_summary_route_adoption_ready": (
            publication_bundle_feedback_llm_route_planner_summary.get(
                "n_route_adoption_ready",
                0,
            )
        ),
        "n_publication_bundle_feedback_llm_route_planner_summary_route_adoption_pending_refinement": (
            publication_bundle_feedback_llm_route_planner_summary.get(
                "n_route_adoption_pending_refinement",
                0,
            )
        ),
        "n_publication_bundle_feedback_llm_route_planner_summary_route_adoption_pending_formal_gap_boundary_blockers": (
            publication_bundle_feedback_llm_route_planner_summary.get(
                "n_route_adoption_pending_formal_gap_boundary_blockers",
                0,
            )
        ),
        "n_publication_bundle_feedback_llm_route_planner_summary_route_adoption_blockers": (
            publication_bundle_feedback_llm_route_planner_summary.get(
                "n_route_adoption_blockers",
                0,
            )
        ),
        "publication_bundle_feedback_llm_route_planner_summary_route_adoption_blocker_counts": (
            publication_bundle_feedback_llm_route_planner_summary.get(
                "route_adoption_blocker_counts",
                {},
            )
        ),
        "publication_bundle_feedback_llm_route_planner_summary_by_route_adoption_status": (
            publication_bundle_feedback_llm_route_planner_summary.get(
                "by_route_adoption_status",
                {},
            )
        ),
        "publication_bundle_feedback_llm_route_planner_summary_by_route_adoption_blocker": (
            publication_bundle_feedback_llm_route_planner_summary.get(
                "by_route_adoption_blocker",
                {},
            )
        ),
        "n_publication_bundle_llm_route_planner_summary_checked": publication_bundle_audit_payload.get(
            "n_bundle_llm_route_planner_summary_checked",
            0,
        ),
        "n_publication_bundle_llm_route_planner_summary_valid": publication_bundle_audit_payload.get(
            "n_bundle_llm_route_planner_summary_valid",
            0,
        ),
        "n_publication_bundle_feedback_llm_route_planner_summary_checked": publication_bundle_audit_payload.get(
            "n_bundle_feedback_llm_route_planner_summary_checked",
            0,
        ),
        "n_publication_bundle_feedback_llm_route_planner_summary_valid": publication_bundle_audit_payload.get(
            "n_bundle_feedback_llm_route_planner_summary_valid",
            0,
        ),
        "n_llm_route_planner_request_packets": llm_route_planner_payload.get(
            "n_request_packets",
            0,
        ),
        "n_llm_route_planner_context_packet_inventories": llm_route_planner_payload.get(
            "n_requests_with_context_packet_inventory",
            0,
        ),
        "n_llm_route_planner_context_inventory_total_rows": llm_route_planner_payload.get(
            "n_request_context_inventory_total_rows",
            0,
        ),
        "n_llm_route_planner_rows_with_context_packet_inventory": llm_route_planner_payload.get(
            "n_rows_with_context_packet_inventory",
            0,
        ),
        "n_llm_route_planner_quality_control_obligation_inventories": (
            llm_route_planner_payload.get(
                "n_requests_with_quality_control_obligation_inventory",
                0,
            )
        ),
        "n_llm_route_planner_pending_quality_control_obligation_inventories": (
            llm_route_planner_payload.get(
                "n_requests_with_pending_quality_control_obligation_inventory",
                0,
            )
        ),
        "n_llm_route_planner_request_quality_control_obligation_fields": (
            llm_route_planner_payload.get(
                "n_request_quality_control_obligation_fields",
                0,
            )
        ),
        "n_llm_route_planner_request_quality_control_obligation_values": (
            llm_route_planner_payload.get(
                "n_request_quality_control_obligation_values",
                0,
            )
        ),
        "n_llm_route_planner_request_pending_quality_control_fields": (
            llm_route_planner_payload.get(
                "n_request_pending_quality_control_fields",
                0,
            )
        ),
        "n_llm_route_planner_request_pending_quality_control_values": (
            llm_route_planner_payload.get(
                "n_request_pending_quality_control_values",
                0,
            )
        ),
        "n_llm_route_planner_request_discharged_quality_control_fields": (
            llm_route_planner_payload.get(
                "n_request_discharged_quality_control_fields",
                0,
            )
        ),
        "n_llm_route_planner_request_discharged_quality_control_values": (
            llm_route_planner_payload.get(
                "n_request_discharged_quality_control_values",
                0,
            )
        ),
        "llm_route_planner_model_tier_selection_mode": llm_route_planner_payload.get(
            "model_tier_selection_mode",
            "",
        ),
        "llm_route_planner_by_request_model_tier": llm_route_planner_payload.get(
            "by_request_model_tier",
            {},
        ),
        "n_llm_route_planner_request_model_tier_haiku": llm_route_planner_payload.get(
            "n_request_model_tier_haiku",
            0,
        ),
        "n_llm_route_planner_request_model_tier_sonnet": llm_route_planner_payload.get(
            "n_request_model_tier_sonnet",
            0,
        ),
        "n_llm_route_planner_request_model_tier_opus": llm_route_planner_payload.get(
            "n_request_model_tier_opus",
            0,
        ),
        "n_llm_route_planner_request_model_tier_mismatches": (
            llm_route_planner_payload.get(
                "n_request_model_tier_mismatches",
                0,
            )
        ),
        "llm_route_planner_request_model_tier_mismatches": (
            llm_route_planner_payload.get(
                "request_model_tier_mismatches",
                [],
            )
        ),
        "n_llm_route_planner_generation_preflight_blocked": (
            llm_route_planner_payload.get(
                "n_generation_preflight_blocked",
                0,
            )
        ),
        "llm_route_planner_generation_preflight_errors": (
            llm_route_planner_payload.get(
                "generation_preflight_errors",
                [],
            )
        ),
        "llm_route_planner_max_repair_attempts": llm_route_planner_payload.get(
            "max_repair_attempts",
            0,
        ),
        "n_llm_route_planner_generated_response_repair_attempts": llm_route_planner_payload.get(
            "n_generated_response_repair_attempts",
            0,
        ),
        "n_llm_route_planner_generated_responses_repaired": llm_route_planner_payload.get(
            "n_generated_responses_repaired",
            0,
        ),
        "n_llm_route_planner_request_schema_valid": llm_route_planner_payload.get(
            "n_request_schema_valid",
            0,
        ),
        "n_llm_route_planner_request_schema_invalid": llm_route_planner_payload.get(
            "n_request_schema_invalid",
            0,
        ),
        "n_llm_route_planner_response_present": llm_route_planner_payload.get(
            "n_response_present",
            0,
        ),
        "n_llm_route_planner_provider_failures": llm_route_planner_payload.get(
            "n_provider_failures",
            0,
        ),
        "n_llm_route_planner_rows_with_generator_metadata": (
            llm_route_planner_payload.get(
                "n_rows_with_generator_metadata",
                0,
            )
        ),
        "n_llm_route_planner_rows_with_generation_errors": (
            llm_route_planner_payload.get(
                "n_rows_with_generation_errors",
                0,
            )
        ),
        "n_llm_route_planner_awaiting": llm_route_planner_payload.get(
            "n_awaiting_llm_response",
            0,
        ),
        "n_llm_route_planner_response_contract_ok": llm_route_planner_payload.get(
            "n_response_contract_ok",
            0,
        ),
        "n_llm_route_planner_informal_knowledge_dag_nodes": (
            llm_route_planner_payload.get("n_informal_knowledge_dag_nodes", 0)
        ),
        "n_llm_route_planner_formal_realization_dag_nodes": (
            llm_route_planner_payload.get("n_formal_realization_dag_nodes", 0)
        ),
        "n_llm_route_planner_lean_realization_dag_nodes": (
            llm_route_planner_payload.get("n_lean_realization_dag_nodes", 0)
        ),
        "n_llm_route_planner_route_alignment_edges": (
            llm_route_planner_payload.get("n_route_alignment_edges", 0)
        ),
        "n_llm_route_planner_accepted_route_plans": llm_route_planner_payload.get(
            "n_accepted_route_plans",
            0,
        ),
        "n_llm_route_planner_route_adoption_ready": llm_route_planner_payload.get(
            "n_route_adoption_ready",
            0,
        ),
        "n_llm_route_planner_route_adoption_pending_refinement": (
            llm_route_planner_payload.get("n_route_adoption_pending_refinement", 0)
        ),
        "n_llm_route_planner_route_adoption_awaiting_llm_response": (
            llm_route_planner_payload.get("n_route_adoption_awaiting_llm_response", 0)
        ),
        "n_llm_route_planner_route_adoption_rejected": llm_route_planner_payload.get(
            "n_route_adoption_rejected",
            0,
        ),
        "llm_route_planner_route_adoption_blocker_counts": (
            llm_route_planner_payload.get("route_adoption_blocker_counts", {})
        ),
        "llm_route_planner_by_route_adoption_blocker": (
            llm_route_planner_payload.get("by_route_adoption_blocker", {})
        ),
        "n_llm_route_planner_route_adoption_pending_search_request_blockers": (
            llm_route_planner_payload.get(
                "n_route_adoption_pending_search_request_blockers",
                0,
            )
        ),
        "n_llm_route_planner_route_adoption_pending_planner_next_action_blockers": (
            llm_route_planner_payload.get(
                "n_route_adoption_pending_planner_next_action_blockers",
                0,
            )
        ),
        "n_llm_route_planner_route_adoption_pending_uncertainty_blockers": (
            llm_route_planner_payload.get(
                "n_route_adoption_pending_uncertainty_blockers",
                0,
            )
        ),
        "n_llm_route_planner_route_adoption_pending_residual_repair_blockers": (
            llm_route_planner_payload.get(
                "n_route_adoption_pending_residual_repair_blockers",
                0,
            )
        ),
        "n_llm_route_planner_route_adoption_pending_feedback_action_blockers": (
            llm_route_planner_payload.get(
                "n_route_adoption_pending_feedback_action_blockers",
                0,
            )
        ),
        "n_llm_route_planner_route_adoption_pending_resource_playbook_redispatch_blockers": (
            llm_route_planner_payload.get(
                "n_route_adoption_pending_resource_playbook_redispatch_blockers",
                0,
            )
        ),
        "n_llm_route_planner_route_adoption_pending_resource_request_queue_blockers": (
            llm_route_planner_payload.get(
                "n_route_adoption_pending_resource_request_queue_blockers",
                0,
            )
        ),
        "n_llm_route_planner_route_adoption_pending_feedback_replan_blockers": (
            llm_route_planner_payload.get(
                "n_route_adoption_pending_feedback_replan_blockers",
                0,
            )
        ),
        "n_llm_route_planner_route_adoption_pending_realization_coverage_blockers": (
            llm_route_planner_payload.get(
                "n_route_adoption_pending_realization_coverage_blockers",
                0,
            )
        ),
        "n_llm_route_planner_route_adoption_pending_omitted_cost_hint_primitive_blockers": (
            llm_route_planner_payload.get(
                "n_route_adoption_pending_omitted_cost_hint_primitive_blockers",
                0,
            )
        ),
        "n_llm_route_planner_route_adoption_pending_formal_gap_boundary_blockers": (
            llm_route_planner_payload.get(
                "n_route_adoption_pending_formal_gap_boundary_blockers",
                0,
            )
        ),
        "n_llm_route_planner_route_adoption_pending_source_grounding_blockers": (
            llm_route_planner_payload.get(
                "n_route_adoption_pending_source_grounding_blockers",
                0,
            )
        ),
        "n_llm_route_planner_route_adoption_pending_quality_control_blockers": (
            llm_route_planner_payload.get(
                "n_route_adoption_pending_quality_control_blockers",
                0,
            )
        ),
        "n_llm_route_planner_route_adoption_omitted_cost_hint_primitives": (
            llm_route_planner_payload.get(
                "n_route_adoption_omitted_cost_hint_primitives",
                0,
            )
        ),
        "n_llm_route_planner_row_schema_valid": llm_route_planner_payload.get(
            "n_row_schema_valid",
            0,
        ),
        "n_llm_route_planner_row_schema_invalid": llm_route_planner_payload.get(
            "n_row_schema_invalid",
            0,
        ),
        "n_llm_route_planner_search_requests": llm_route_planner_payload.get(
            "n_search_requests",
            0,
        ),
        "n_llm_route_planner_planner_next_actions": llm_route_planner_payload.get(
            "n_planner_next_actions",
            0,
        ),
        "n_llm_route_planner_rows_with_planner_next_actions": (
            llm_route_planner_payload.get(
                "n_rows_with_planner_next_actions",
                0,
            )
        ),
        "n_llm_route_planner_rows_with_realization_coverage_witness": (
            llm_route_planner_payload.get(
                "n_rows_with_realization_coverage_witness",
                0,
            )
        ),
        "n_llm_route_planner_rows_with_complete_realization_coverage": (
            llm_route_planner_payload.get(
                "n_rows_with_complete_realization_coverage",
                0,
            )
        ),
        "n_llm_route_planner_selected_primitives_missing_formal_realization": (
            llm_route_planner_payload.get(
                "n_selected_primitives_missing_formal_realization",
                0,
            )
        ),
        "n_llm_route_planner_delta_primitives_missing_route_alignment": (
            llm_route_planner_payload.get(
                "n_delta_primitives_missing_route_alignment",
                0,
            )
        ),
        "n_llm_route_planner_feedback_loop_realization_witnesses": (
            llm_route_planner_payload.get(
                "n_feedback_loop_summary_realization_witnesses",
                0,
            )
        ),
        "n_llm_route_planner_feedback_loop_incomplete_realization_coverage": (
            llm_route_planner_payload.get(
                "n_feedback_loop_summary_incomplete_realization_coverage",
                0,
            )
        ),
        "n_llm_route_planner_feedback_loop_incomplete_cost_hint_baseline_coverage": (
            llm_route_planner_payload.get(
                "n_feedback_loop_summary_incomplete_cost_hint_baseline_coverage",
                0,
            )
        ),
        "n_llm_route_planner_feedback_loop_missing_selected_formal_primitives": (
            llm_route_planner_payload.get(
                "n_feedback_loop_summary_missing_selected_formal_primitives",
                0,
            )
        ),
        "n_llm_route_planner_feedback_loop_missing_delta_alignment_primitives": (
            llm_route_planner_payload.get(
                "n_feedback_loop_summary_missing_delta_alignment_primitives",
                0,
            )
        ),
        "n_llm_route_planner_feedback_loop_omitted_cost_hint_primitives": (
            llm_route_planner_payload.get(
                "n_feedback_loop_summary_omitted_cost_hint_primitives",
                0,
            )
        ),
        "n_llm_route_planner_feedback_loop_prior_llm_hook_traces": (
            llm_route_planner_payload.get(
                "n_feedback_loop_summary_prior_llm_route_planner_hook_traces",
                0,
            )
        ),
        "n_llm_route_planner_requests_with_feedback_loop_prior_llm_hook_traces": (
            llm_route_planner_payload.get(
                "n_requests_with_feedback_loop_summary_prior_llm_route_planner_hook_traces",
                0,
            )
        ),
        "n_llm_route_planner_requests_with_component_resource_registry_context": (
            llm_route_planner_payload.get(
                "n_requests_with_component_resource_registry_context",
                0,
            )
        ),
        "n_llm_route_planner_component_resource_registry_resources_in_prompt": (
            llm_route_planner_payload.get(
                "n_component_resource_registry_resources_in_prompt",
                0,
            )
        ),
        "n_llm_route_planner_component_resource_registry_contracts_in_prompt": (
            llm_route_planner_payload.get(
                "n_component_resource_registry_contracts_in_prompt",
                0,
            )
        ),
        "n_feedback_llm_route_planner_request_packets": feedback_llm_route_planner_payload.get(
            "n_request_packets",
            0,
        ),
        "n_feedback_llm_route_planner_context_packet_inventories": (
            feedback_llm_route_planner_payload.get(
                "n_requests_with_context_packet_inventory",
                0,
            )
        ),
        "n_feedback_llm_route_planner_context_inventory_total_rows": (
            feedback_llm_route_planner_payload.get(
                "n_request_context_inventory_total_rows",
                0,
            )
        ),
        "n_feedback_llm_route_planner_rows_with_context_packet_inventory": (
            feedback_llm_route_planner_payload.get(
                "n_rows_with_context_packet_inventory",
                0,
            )
        ),
        "n_feedback_llm_route_planner_quality_control_obligation_inventories": (
            feedback_llm_route_planner_payload.get(
                "n_requests_with_quality_control_obligation_inventory",
                0,
            )
        ),
        "n_feedback_llm_route_planner_pending_quality_control_obligation_inventories": (
            feedback_llm_route_planner_payload.get(
                "n_requests_with_pending_quality_control_obligation_inventory",
                0,
            )
        ),
        "n_feedback_llm_route_planner_request_quality_control_obligation_fields": (
            feedback_llm_route_planner_payload.get(
                "n_request_quality_control_obligation_fields",
                0,
            )
        ),
        "n_feedback_llm_route_planner_request_quality_control_obligation_values": (
            feedback_llm_route_planner_payload.get(
                "n_request_quality_control_obligation_values",
                0,
            )
        ),
        "n_feedback_llm_route_planner_request_pending_quality_control_fields": (
            feedback_llm_route_planner_payload.get(
                "n_request_pending_quality_control_fields",
                0,
            )
        ),
        "n_feedback_llm_route_planner_request_pending_quality_control_values": (
            feedback_llm_route_planner_payload.get(
                "n_request_pending_quality_control_values",
                0,
            )
        ),
        "n_feedback_llm_route_planner_request_discharged_quality_control_fields": (
            feedback_llm_route_planner_payload.get(
                "n_request_discharged_quality_control_fields",
                0,
            )
        ),
        "n_feedback_llm_route_planner_request_discharged_quality_control_values": (
            feedback_llm_route_planner_payload.get(
                "n_request_discharged_quality_control_values",
                0,
            )
        ),
        "feedback_llm_route_planner_model_tier_selection_mode": (
            feedback_llm_route_planner_payload.get(
                "model_tier_selection_mode",
                "",
            )
        ),
        "feedback_llm_route_planner_by_request_model_tier": (
            feedback_llm_route_planner_payload.get(
                "by_request_model_tier",
                {},
            )
        ),
        "n_feedback_llm_route_planner_request_model_tier_haiku": (
            feedback_llm_route_planner_payload.get(
                "n_request_model_tier_haiku",
                0,
            )
        ),
        "n_feedback_llm_route_planner_request_model_tier_sonnet": (
            feedback_llm_route_planner_payload.get(
                "n_request_model_tier_sonnet",
                0,
            )
        ),
        "n_feedback_llm_route_planner_request_model_tier_opus": (
            feedback_llm_route_planner_payload.get(
                "n_request_model_tier_opus",
                0,
            )
        ),
        "n_feedback_llm_route_planner_request_model_tier_mismatches": (
            feedback_llm_route_planner_payload.get(
                "n_request_model_tier_mismatches",
                0,
            )
        ),
        "feedback_llm_route_planner_request_model_tier_mismatches": (
            feedback_llm_route_planner_payload.get(
                "request_model_tier_mismatches",
                [],
            )
        ),
        "n_feedback_llm_route_planner_generation_preflight_blocked": (
            feedback_llm_route_planner_payload.get(
                "n_generation_preflight_blocked",
                0,
            )
        ),
        "feedback_llm_route_planner_generation_preflight_errors": (
            feedback_llm_route_planner_payload.get(
                "generation_preflight_errors",
                [],
            )
        ),
        "feedback_llm_route_planner_max_repair_attempts": (
            feedback_llm_route_planner_payload.get(
                "max_repair_attempts",
                0,
            )
        ),
        "n_feedback_llm_route_planner_generated_response_repair_attempts": (
            feedback_llm_route_planner_payload.get(
                "n_generated_response_repair_attempts",
                0,
            )
        ),
        "n_feedback_llm_route_planner_generated_responses_repaired": (
            feedback_llm_route_planner_payload.get(
                "n_generated_responses_repaired",
                0,
            )
        ),
        "n_feedback_llm_route_planner_request_schema_valid": feedback_llm_route_planner_payload.get(
            "n_request_schema_valid",
            0,
        ),
        "n_feedback_llm_route_planner_request_schema_invalid": feedback_llm_route_planner_payload.get(
            "n_request_schema_invalid",
            0,
        ),
        "n_feedback_llm_route_planner_response_present": feedback_llm_route_planner_payload.get(
            "n_response_present",
            0,
        ),
        "n_feedback_llm_route_planner_provider_failures": feedback_llm_route_planner_payload.get(
            "n_provider_failures",
            0,
        ),
        "n_feedback_llm_route_planner_rows_with_generator_metadata": (
            feedback_llm_route_planner_payload.get(
                "n_rows_with_generator_metadata",
                0,
            )
        ),
        "n_feedback_llm_route_planner_rows_with_generation_errors": (
            feedback_llm_route_planner_payload.get(
                "n_rows_with_generation_errors",
                0,
            )
        ),
        "n_feedback_llm_route_planner_awaiting": feedback_llm_route_planner_payload.get(
            "n_awaiting_llm_response",
            0,
        ),
        "n_feedback_llm_route_planner_response_contract_ok": feedback_llm_route_planner_payload.get(
            "n_response_contract_ok",
            0,
        ),
        "n_feedback_llm_route_planner_informal_knowledge_dag_nodes": (
            feedback_llm_route_planner_payload.get(
                "n_informal_knowledge_dag_nodes",
                0,
            )
        ),
        "n_feedback_llm_route_planner_formal_realization_dag_nodes": (
            feedback_llm_route_planner_payload.get(
                "n_formal_realization_dag_nodes",
                0,
            )
        ),
        "n_feedback_llm_route_planner_lean_realization_dag_nodes": (
            feedback_llm_route_planner_payload.get(
                "n_lean_realization_dag_nodes",
                0,
            )
        ),
        "n_feedback_llm_route_planner_route_alignment_edges": (
            feedback_llm_route_planner_payload.get("n_route_alignment_edges", 0)
        ),
        "n_feedback_llm_route_planner_accepted_route_plans": feedback_llm_route_planner_payload.get(
            "n_accepted_route_plans",
            0,
        ),
        "n_feedback_llm_route_planner_route_adoption_ready": (
            feedback_llm_route_planner_payload.get("n_route_adoption_ready", 0)
        ),
        "n_feedback_llm_route_planner_route_adoption_pending_refinement": (
            feedback_llm_route_planner_payload.get(
                "n_route_adoption_pending_refinement",
                0,
            )
        ),
        "n_feedback_llm_route_planner_route_adoption_awaiting_llm_response": (
            feedback_llm_route_planner_payload.get(
                "n_route_adoption_awaiting_llm_response",
                0,
            )
        ),
        "n_feedback_llm_route_planner_route_adoption_rejected": (
            feedback_llm_route_planner_payload.get("n_route_adoption_rejected", 0)
        ),
        "feedback_llm_route_planner_route_adoption_blocker_counts": (
            feedback_llm_route_planner_payload.get("route_adoption_blocker_counts", {})
        ),
        "feedback_llm_route_planner_by_route_adoption_blocker": (
            feedback_llm_route_planner_payload.get("by_route_adoption_blocker", {})
        ),
        "n_feedback_llm_route_planner_route_adoption_pending_search_request_blockers": (
            feedback_llm_route_planner_payload.get(
                "n_route_adoption_pending_search_request_blockers",
                0,
            )
        ),
        "n_feedback_llm_route_planner_route_adoption_pending_planner_next_action_blockers": (
            feedback_llm_route_planner_payload.get(
                "n_route_adoption_pending_planner_next_action_blockers",
                0,
            )
        ),
        "n_feedback_llm_route_planner_route_adoption_pending_uncertainty_blockers": (
            feedback_llm_route_planner_payload.get(
                "n_route_adoption_pending_uncertainty_blockers",
                0,
            )
        ),
        "n_feedback_llm_route_planner_route_adoption_pending_residual_repair_blockers": (
            feedback_llm_route_planner_payload.get(
                "n_route_adoption_pending_residual_repair_blockers",
                0,
            )
        ),
        "n_feedback_llm_route_planner_route_adoption_pending_feedback_action_blockers": (
            feedback_llm_route_planner_payload.get(
                "n_route_adoption_pending_feedback_action_blockers",
                0,
            )
        ),
        "n_feedback_llm_route_planner_route_adoption_pending_resource_playbook_redispatch_blockers": (
            feedback_llm_route_planner_payload.get(
                "n_route_adoption_pending_resource_playbook_redispatch_blockers",
                0,
            )
        ),
        "n_feedback_llm_route_planner_route_adoption_pending_resource_request_queue_blockers": (
            feedback_llm_route_planner_payload.get(
                "n_route_adoption_pending_resource_request_queue_blockers",
                0,
            )
        ),
        "n_feedback_llm_route_planner_route_adoption_pending_feedback_replan_blockers": (
            feedback_llm_route_planner_payload.get(
                "n_route_adoption_pending_feedback_replan_blockers",
                0,
            )
        ),
        "n_feedback_llm_route_planner_route_adoption_pending_realization_coverage_blockers": (
            feedback_llm_route_planner_payload.get(
                "n_route_adoption_pending_realization_coverage_blockers",
                0,
            )
        ),
        "n_feedback_llm_route_planner_route_adoption_pending_omitted_cost_hint_primitive_blockers": (
            feedback_llm_route_planner_payload.get(
                "n_route_adoption_pending_omitted_cost_hint_primitive_blockers",
                0,
            )
        ),
        "n_feedback_llm_route_planner_route_adoption_pending_formal_gap_boundary_blockers": (
            feedback_llm_route_planner_payload.get(
                "n_route_adoption_pending_formal_gap_boundary_blockers",
                0,
            )
        ),
        "n_feedback_llm_route_planner_route_adoption_pending_source_grounding_blockers": (
            feedback_llm_route_planner_payload.get(
                "n_route_adoption_pending_source_grounding_blockers",
                0,
            )
        ),
        "n_feedback_llm_route_planner_route_adoption_pending_quality_control_blockers": (
            feedback_llm_route_planner_payload.get(
                "n_route_adoption_pending_quality_control_blockers",
                0,
            )
        ),
        "n_feedback_llm_route_planner_route_adoption_omitted_cost_hint_primitives": (
            feedback_llm_route_planner_payload.get(
                "n_route_adoption_omitted_cost_hint_primitives",
                0,
            )
        ),
        "n_feedback_llm_route_planner_row_schema_valid": feedback_llm_route_planner_payload.get(
            "n_row_schema_valid",
            0,
        ),
        "n_feedback_llm_route_planner_row_schema_invalid": feedback_llm_route_planner_payload.get(
            "n_row_schema_invalid",
            0,
        ),
        "n_feedback_llm_route_planner_search_requests": feedback_llm_route_planner_payload.get(
            "n_search_requests",
            0,
        ),
        "n_feedback_llm_route_planner_planner_next_actions": (
            feedback_llm_route_planner_payload.get(
                "n_planner_next_actions",
                0,
            )
        ),
        "n_feedback_llm_route_planner_rows_with_planner_next_actions": (
            feedback_llm_route_planner_payload.get(
                "n_rows_with_planner_next_actions",
                0,
            )
        ),
        "n_feedback_llm_route_planner_rows_with_realization_coverage_witness": (
            feedback_llm_route_planner_payload.get(
                "n_rows_with_realization_coverage_witness",
                0,
            )
        ),
        "n_feedback_llm_route_planner_rows_with_complete_realization_coverage": (
            feedback_llm_route_planner_payload.get(
                "n_rows_with_complete_realization_coverage",
                0,
            )
        ),
        "n_feedback_llm_route_planner_selected_primitives_missing_formal_realization": (
            feedback_llm_route_planner_payload.get(
                "n_selected_primitives_missing_formal_realization",
                0,
            )
        ),
        "n_feedback_llm_route_planner_delta_primitives_missing_route_alignment": (
            feedback_llm_route_planner_payload.get(
                "n_delta_primitives_missing_route_alignment",
                0,
            )
        ),
        "n_feedback_llm_route_planner_feedback_loop_realization_witnesses": (
            feedback_llm_route_planner_payload.get(
                "n_feedback_loop_summary_realization_witnesses",
                0,
            )
        ),
        "n_feedback_llm_route_planner_feedback_loop_incomplete_realization_coverage": (
            feedback_llm_route_planner_payload.get(
                "n_feedback_loop_summary_incomplete_realization_coverage",
                0,
            )
        ),
        "n_feedback_llm_route_planner_feedback_loop_incomplete_cost_hint_baseline_coverage": (
            feedback_llm_route_planner_payload.get(
                "n_feedback_loop_summary_incomplete_cost_hint_baseline_coverage",
                0,
            )
        ),
        "n_feedback_llm_route_planner_feedback_loop_missing_selected_formal_primitives": (
            feedback_llm_route_planner_payload.get(
                "n_feedback_loop_summary_missing_selected_formal_primitives",
                0,
            )
        ),
        "n_feedback_llm_route_planner_feedback_loop_missing_delta_alignment_primitives": (
            feedback_llm_route_planner_payload.get(
                "n_feedback_loop_summary_missing_delta_alignment_primitives",
                0,
            )
        ),
        "n_feedback_llm_route_planner_feedback_loop_omitted_cost_hint_primitives": (
            feedback_llm_route_planner_payload.get(
                "n_feedback_loop_summary_omitted_cost_hint_primitives",
                0,
            )
        ),
        "n_feedback_llm_route_planner_feedback_loop_prior_llm_hook_traces": (
            feedback_llm_route_planner_payload.get(
                "n_feedback_loop_summary_prior_llm_route_planner_hook_traces",
                0,
            )
        ),
        "n_feedback_llm_route_planner_requests_with_feedback_loop_prior_llm_hook_traces": (
            feedback_llm_route_planner_payload.get(
                "n_requests_with_feedback_loop_summary_prior_llm_route_planner_hook_traces",
                0,
            )
        ),
        "n_feedback_llm_route_planner_requests_with_component_resource_registry_context": (
            feedback_llm_route_planner_payload.get(
                "n_requests_with_component_resource_registry_context",
                0,
            )
        ),
        "n_feedback_llm_route_planner_component_resource_registry_resources_in_prompt": (
            feedback_llm_route_planner_payload.get(
                "n_component_resource_registry_resources_in_prompt",
                0,
            )
        ),
        "n_feedback_llm_route_planner_component_resource_registry_contracts_in_prompt": (
            feedback_llm_route_planner_payload.get(
                "n_component_resource_registry_contracts_in_prompt",
                0,
            )
        ),
        "n_feedback_llm_route_planner_request_residual_goals": feedback_llm_route_planner_payload.get(
            "n_request_residual_goals",
            0,
        ),
        "n_feedback_llm_route_planner_requests_with_library_coverage_rows": feedback_llm_route_planner_payload.get(
            "n_requests_with_library_coverage_rows",
            0,
        ),
        "n_feedback_llm_route_planner_requests_with_source_grounding_rows": feedback_llm_route_planner_payload.get(
            "n_requests_with_source_grounding_rows",
            0,
        ),
        "n_feedback_llm_route_planner_requests_with_resource_request_queue_rows": feedback_llm_route_planner_payload.get(
            "n_requests_with_resource_request_queue_rows",
            0,
        ),
        "n_feedback_llm_route_planner_resource_request_queue_rows": feedback_llm_route_planner_payload.get(
            "n_request_resource_request_queue_rows",
            0,
        ),
        "n_feedback_llm_route_planner_requests_with_resource_response_ledger_rows": feedback_llm_route_planner_payload.get(
            "n_requests_with_resource_response_ledger_rows",
            0,
        ),
        "n_feedback_llm_route_planner_requests_with_refinement_evidence_rows": feedback_llm_route_planner_payload.get(
            "n_requests_with_refinement_evidence_rows",
            0,
        ),
        "n_feedback_llm_route_planner_requests_with_route_revision_overlay_rows": feedback_llm_route_planner_payload.get(
            "n_requests_with_route_revision_overlay_rows",
            0,
        ),
        "n_feedback_llm_route_planner_requests_with_interactive_session_rows": feedback_llm_route_planner_payload.get(
            "n_requests_with_interactive_session_rows",
            0,
        ),
        "n_feedback_llm_route_planner_requests_with_interactive_decision_policy_rows": feedback_llm_route_planner_payload.get(
            "n_requests_with_interactive_decision_policy_rows",
            0,
        ),
        "n_publication_bundle_optional_llm_route_planner_request_schema_checked": publication_bundle_audit_payload.get(
            "n_optional_llm_route_planner_request_schema_checked",
            0,
        ),
        "n_publication_bundle_optional_llm_route_planner_request_schema_valid": publication_bundle_audit_payload.get(
            "n_optional_llm_route_planner_request_schema_valid",
            0,
        ),
        "n_publication_bundle_optional_llm_route_planner_request_model_tier_mismatch_checked": publication_bundle_audit_payload.get(
            "n_optional_llm_route_planner_request_model_tier_mismatch_checked",
            0,
        ),
        "n_publication_bundle_optional_llm_route_planner_request_model_tier_mismatch_valid": publication_bundle_audit_payload.get(
            "n_optional_llm_route_planner_request_model_tier_mismatch_valid",
            0,
        ),
        "n_publication_bundle_optional_llm_route_planner_request_generation_policy_checked": publication_bundle_audit_payload.get(
            "n_optional_llm_route_planner_request_generation_policy_checked",
            0,
        ),
        "n_publication_bundle_optional_llm_route_planner_request_generation_policy_valid": publication_bundle_audit_payload.get(
            "n_optional_llm_route_planner_request_generation_policy_valid",
            0,
        ),
        "n_publication_bundle_optional_llm_route_planner_generation_preflight_checked": publication_bundle_audit_payload.get(
            "n_optional_llm_route_planner_generation_preflight_checked",
            0,
        ),
        "n_publication_bundle_optional_llm_route_planner_generation_preflight_valid": publication_bundle_audit_payload.get(
            "n_optional_llm_route_planner_generation_preflight_valid",
            0,
        ),
        "n_publication_bundle_optional_llm_route_planner_route_adoption_blocker_summary_checked": publication_bundle_audit_payload.get(
            "n_optional_llm_route_planner_route_adoption_blocker_summary_checked",
            0,
        ),
        "n_publication_bundle_optional_llm_route_planner_route_adoption_blocker_summary_valid": publication_bundle_audit_payload.get(
            "n_optional_llm_route_planner_route_adoption_blocker_summary_valid",
            0,
        ),
        "n_publication_bundle_optional_llm_route_planner_row_schema_checked": publication_bundle_audit_payload.get(
            "n_optional_llm_route_planner_row_schema_checked",
            0,
        ),
        "n_publication_bundle_optional_llm_route_planner_row_schema_valid": publication_bundle_audit_payload.get(
            "n_optional_llm_route_planner_row_schema_valid",
            0,
        ),
        "n_publication_bundle_optional_llm_route_planner_realization_witness_schema_checked": publication_bundle_audit_payload.get(
            "n_optional_llm_route_planner_realization_witness_schema_checked",
            0,
        ),
        "n_publication_bundle_optional_llm_route_planner_realization_witness_schema_valid": publication_bundle_audit_payload.get(
            "n_optional_llm_route_planner_realization_witness_schema_valid",
            0,
        ),
        "n_publication_bundle_optional_llm_route_planner_seed_realization_witness_checked": publication_bundle_audit_payload.get(
            "n_optional_llm_route_planner_seed_realization_witness_checked",
            0,
        ),
        "n_publication_bundle_optional_llm_route_planner_seed_realization_witness_valid": publication_bundle_audit_payload.get(
            "n_optional_llm_route_planner_seed_realization_witness_valid",
            0,
        ),
        "n_publication_bundle_optional_llm_route_planner_seed_model_provenance_checked": publication_bundle_audit_payload.get(
            "n_optional_llm_route_planner_seed_model_provenance_checked",
            0,
        ),
        "n_publication_bundle_optional_llm_route_planner_seed_model_provenance_valid": publication_bundle_audit_payload.get(
            "n_optional_llm_route_planner_seed_model_provenance_valid",
            0,
        ),
        "n_publication_bundle_optional_llm_route_planner_seed_route_adoption_readiness_checked": publication_bundle_audit_payload.get(
            "n_optional_llm_route_planner_seed_route_adoption_readiness_checked",
            0,
        ),
        "n_publication_bundle_optional_llm_route_planner_seed_route_adoption_readiness_valid": publication_bundle_audit_payload.get(
            "n_optional_llm_route_planner_seed_route_adoption_readiness_valid",
            0,
        ),
        "n_publication_bundle_optional_llm_route_planner_seed_route_selection_summary_checked": publication_bundle_audit_payload.get(
            "n_optional_llm_route_planner_seed_route_selection_summary_checked",
            0,
        ),
        "n_publication_bundle_optional_llm_route_planner_seed_route_selection_summary_valid": publication_bundle_audit_payload.get(
            "n_optional_llm_route_planner_seed_route_selection_summary_valid",
            0,
        ),
        "n_publication_bundle_optional_llm_route_planner_seed_route_selection_contract_checked": publication_bundle_audit_payload.get(
            "n_optional_llm_route_planner_seed_route_selection_contract_checked",
            0,
        ),
        "n_publication_bundle_optional_llm_route_planner_seed_route_selection_contract_valid": publication_bundle_audit_payload.get(
            "n_optional_llm_route_planner_seed_route_selection_contract_valid",
            0,
        ),
        "n_publication_bundle_optional_llm_route_planner_seed_route_selection_schema_checked": publication_bundle_audit_payload.get(
            "n_optional_llm_route_planner_seed_route_selection_schema_checked",
            0,
        ),
        "n_publication_bundle_optional_llm_route_planner_seed_route_selection_schema_valid": publication_bundle_audit_payload.get(
            "n_optional_llm_route_planner_seed_route_selection_schema_valid",
            0,
        ),
        "n_publication_bundle_optional_llm_route_planner_seed_route_selection_checked": publication_bundle_audit_payload.get(
            "n_optional_llm_route_planner_seed_route_selection_checked",
            0,
        ),
        "n_publication_bundle_optional_llm_route_planner_seed_route_selection_valid": publication_bundle_audit_payload.get(
            "n_optional_llm_route_planner_seed_route_selection_valid",
            0,
        ),
        "n_publication_bundle_optional_llm_route_planner_seed_route_selection_candidates": publication_bundle_audit_payload.get(
            "n_optional_llm_route_planner_seed_route_selection_candidates",
            0,
        ),
        "n_publication_bundle_optional_llm_route_planner_seed_route_selection_adoptable_candidates": publication_bundle_audit_payload.get(
            "n_optional_llm_route_planner_seed_route_selection_adoptable_candidates",
            0,
        ),
        "n_publication_bundle_optional_llm_route_planner_seed_route_selection_selected_adoptable": publication_bundle_audit_payload.get(
            "n_optional_llm_route_planner_seed_route_selection_selected_adoptable",
            0,
        ),
        "n_publication_bundle_optional_llm_route_planner_seed_route_selection_selected_not_adoptable": publication_bundle_audit_payload.get(
            "n_optional_llm_route_planner_seed_route_selection_selected_not_adoptable",
            0,
        ),
        "n_publication_bundle_optional_feedback_llm_route_planner_request_schema_checked": publication_bundle_audit_payload.get(
            "n_optional_feedback_llm_route_planner_request_schema_checked",
            0,
        ),
        "n_publication_bundle_optional_feedback_llm_route_planner_request_schema_valid": publication_bundle_audit_payload.get(
            "n_optional_feedback_llm_route_planner_request_schema_valid",
            0,
        ),
        "n_publication_bundle_optional_feedback_llm_route_planner_request_model_tier_mismatch_checked": publication_bundle_audit_payload.get(
            "n_optional_feedback_llm_route_planner_request_model_tier_mismatch_checked",
            0,
        ),
        "n_publication_bundle_optional_feedback_llm_route_planner_request_model_tier_mismatch_valid": publication_bundle_audit_payload.get(
            "n_optional_feedback_llm_route_planner_request_model_tier_mismatch_valid",
            0,
        ),
        "n_publication_bundle_optional_feedback_llm_route_planner_request_generation_policy_checked": publication_bundle_audit_payload.get(
            "n_optional_feedback_llm_route_planner_request_generation_policy_checked",
            0,
        ),
        "n_publication_bundle_optional_feedback_llm_route_planner_request_generation_policy_valid": publication_bundle_audit_payload.get(
            "n_optional_feedback_llm_route_planner_request_generation_policy_valid",
            0,
        ),
        "n_publication_bundle_optional_feedback_llm_route_planner_generation_preflight_checked": publication_bundle_audit_payload.get(
            "n_optional_feedback_llm_route_planner_generation_preflight_checked",
            0,
        ),
        "n_publication_bundle_optional_feedback_llm_route_planner_generation_preflight_valid": publication_bundle_audit_payload.get(
            "n_optional_feedback_llm_route_planner_generation_preflight_valid",
            0,
        ),
        "n_publication_bundle_optional_feedback_llm_route_planner_route_adoption_blocker_summary_checked": publication_bundle_audit_payload.get(
            "n_optional_feedback_llm_route_planner_route_adoption_blocker_summary_checked",
            0,
        ),
        "n_publication_bundle_optional_feedback_llm_route_planner_route_adoption_blocker_summary_valid": publication_bundle_audit_payload.get(
            "n_optional_feedback_llm_route_planner_route_adoption_blocker_summary_valid",
            0,
        ),
        "n_publication_bundle_optional_feedback_llm_route_planner_row_schema_checked": publication_bundle_audit_payload.get(
            "n_optional_feedback_llm_route_planner_row_schema_checked",
            0,
        ),
        "n_publication_bundle_optional_feedback_llm_route_planner_row_schema_valid": publication_bundle_audit_payload.get(
            "n_optional_feedback_llm_route_planner_row_schema_valid",
            0,
        ),
        "n_publication_bundle_optional_feedback_llm_route_planner_realization_witness_schema_checked": publication_bundle_audit_payload.get(
            "n_optional_feedback_llm_route_planner_realization_witness_schema_checked",
            0,
        ),
        "n_publication_bundle_optional_feedback_llm_route_planner_realization_witness_schema_valid": publication_bundle_audit_payload.get(
            "n_optional_feedback_llm_route_planner_realization_witness_schema_valid",
            0,
        ),
        "n_publication_bundle_optional_feedback_llm_route_planner_seed_realization_witness_checked": publication_bundle_audit_payload.get(
            "n_optional_feedback_llm_route_planner_seed_realization_witness_checked",
            0,
        ),
        "n_publication_bundle_optional_feedback_llm_route_planner_seed_realization_witness_valid": publication_bundle_audit_payload.get(
            "n_optional_feedback_llm_route_planner_seed_realization_witness_valid",
            0,
        ),
        "n_publication_bundle_optional_feedback_llm_route_planner_seed_model_provenance_checked": publication_bundle_audit_payload.get(
            "n_optional_feedback_llm_route_planner_seed_model_provenance_checked",
            0,
        ),
        "n_publication_bundle_optional_feedback_llm_route_planner_seed_model_provenance_valid": publication_bundle_audit_payload.get(
            "n_optional_feedback_llm_route_planner_seed_model_provenance_valid",
            0,
        ),
        "n_publication_bundle_optional_feedback_llm_route_planner_seed_route_adoption_readiness_checked": publication_bundle_audit_payload.get(
            "n_optional_feedback_llm_route_planner_seed_route_adoption_readiness_checked",
            0,
        ),
        "n_publication_bundle_optional_feedback_llm_route_planner_seed_route_adoption_readiness_valid": publication_bundle_audit_payload.get(
            "n_optional_feedback_llm_route_planner_seed_route_adoption_readiness_valid",
            0,
        ),
        "n_publication_bundle_optional_feedback_llm_route_planner_seed_route_selection_summary_checked": publication_bundle_audit_payload.get(
            "n_optional_feedback_llm_route_planner_seed_route_selection_summary_checked",
            0,
        ),
        "n_publication_bundle_optional_feedback_llm_route_planner_seed_route_selection_summary_valid": publication_bundle_audit_payload.get(
            "n_optional_feedback_llm_route_planner_seed_route_selection_summary_valid",
            0,
        ),
        "n_publication_bundle_optional_feedback_llm_route_planner_seed_route_selection_contract_checked": publication_bundle_audit_payload.get(
            "n_optional_feedback_llm_route_planner_seed_route_selection_contract_checked",
            0,
        ),
        "n_publication_bundle_optional_feedback_llm_route_planner_seed_route_selection_contract_valid": publication_bundle_audit_payload.get(
            "n_optional_feedback_llm_route_planner_seed_route_selection_contract_valid",
            0,
        ),
        "n_publication_bundle_optional_feedback_llm_route_planner_seed_route_selection_schema_checked": publication_bundle_audit_payload.get(
            "n_optional_feedback_llm_route_planner_seed_route_selection_schema_checked",
            0,
        ),
        "n_publication_bundle_optional_feedback_llm_route_planner_seed_route_selection_schema_valid": publication_bundle_audit_payload.get(
            "n_optional_feedback_llm_route_planner_seed_route_selection_schema_valid",
            0,
        ),
        "n_publication_bundle_optional_feedback_llm_route_planner_seed_route_selection_checked": publication_bundle_audit_payload.get(
            "n_optional_feedback_llm_route_planner_seed_route_selection_checked",
            0,
        ),
        "n_publication_bundle_optional_feedback_llm_route_planner_seed_route_selection_valid": publication_bundle_audit_payload.get(
            "n_optional_feedback_llm_route_planner_seed_route_selection_valid",
            0,
        ),
        "n_publication_bundle_optional_feedback_llm_route_planner_seed_route_selection_candidates": publication_bundle_audit_payload.get(
            "n_optional_feedback_llm_route_planner_seed_route_selection_candidates",
            0,
        ),
        "n_publication_bundle_optional_feedback_llm_route_planner_seed_route_selection_adoptable_candidates": publication_bundle_audit_payload.get(
            "n_optional_feedback_llm_route_planner_seed_route_selection_adoptable_candidates",
            0,
        ),
        "n_publication_bundle_optional_feedback_llm_route_planner_seed_route_selection_selected_adoptable": publication_bundle_audit_payload.get(
            "n_optional_feedback_llm_route_planner_seed_route_selection_selected_adoptable",
            0,
        ),
        "n_publication_bundle_optional_feedback_llm_route_planner_seed_route_selection_selected_not_adoptable": publication_bundle_audit_payload.get(
            "n_optional_feedback_llm_route_planner_seed_route_selection_selected_not_adoptable",
            0,
        ),
        "n_publication_bundle_optional_llm_route_planner_response_payload_validation_manifest_contract_checked": publication_bundle_audit_payload.get(
            "n_optional_llm_route_planner_response_payload_validation_manifest_contract_checked",
            0,
        ),
        "n_publication_bundle_optional_llm_route_planner_response_payload_validation_manifest_contract_valid": publication_bundle_audit_payload.get(
            "n_optional_llm_route_planner_response_payload_validation_manifest_contract_valid",
            0,
        ),
        "n_publication_bundle_optional_llm_route_planner_response_payload_validation_count_checked": publication_bundle_audit_payload.get(
            "n_optional_llm_route_planner_response_payload_validation_count_checked",
            0,
        ),
        "n_publication_bundle_optional_llm_route_planner_response_payload_validation_count_valid": publication_bundle_audit_payload.get(
            "n_optional_llm_route_planner_response_payload_validation_count_valid",
            0,
        ),
        "n_publication_bundle_optional_llm_route_planner_response_payload_validation_request_bound_accounting_checked": publication_bundle_audit_payload.get(
            "n_optional_llm_route_planner_response_payload_validation_request_bound_accounting_checked",
            0,
        ),
        "n_publication_bundle_optional_llm_route_planner_response_payload_validation_request_bound_accounting_valid": publication_bundle_audit_payload.get(
            "n_optional_llm_route_planner_response_payload_validation_request_bound_accounting_valid",
            0,
        ),
        "n_publication_bundle_optional_llm_route_planner_response_payload_validation_request_bound_coverage_checked": publication_bundle_audit_payload.get(
            "n_optional_llm_route_planner_response_payload_validation_request_bound_coverage_checked",
            0,
        ),
        "n_publication_bundle_optional_llm_route_planner_response_payload_validation_request_bound_coverage_valid": publication_bundle_audit_payload.get(
            "n_optional_llm_route_planner_response_payload_validation_request_bound_coverage_valid",
            0,
        ),
        "n_publication_bundle_optional_llm_route_planner_response_payload_validation_row_schema_checked": publication_bundle_audit_payload.get(
            "n_optional_llm_route_planner_response_payload_validation_row_schema_checked",
            0,
        ),
        "n_publication_bundle_optional_llm_route_planner_response_payload_validation_row_schema_valid": publication_bundle_audit_payload.get(
            "n_optional_llm_route_planner_response_payload_validation_row_schema_valid",
            0,
        ),
        "n_minimal_delta_audit_failed": minimal_delta_audit_payload.get("n_failed", 0),
        "n_minimal_delta_decision_rows": minimal_delta_audit_payload.get(
            "n_minimal_delta_decision_rows",
            0,
        ),
        "n_minimal_delta_decision_row_schema_valid": minimal_delta_audit_payload.get(
            "n_minimal_delta_decision_row_schema_valid",
            0,
        ),
        "n_minimal_delta_decision_row_schema_invalid": minimal_delta_audit_payload.get(
            "n_minimal_delta_decision_row_schema_invalid",
            0,
        ),
        "n_source_grounding_unaccounted": source_grounding_audit_payload.get(
            "n_unaccounted",
            0,
        ),
        "n_source_grounding_source_backed": source_grounding_audit_payload.get(
            "n_source_backed",
            0,
        ),
        "n_source_grounding_pending": source_grounding_audit_payload.get(
            "n_source_search_pending",
            0,
        ),
        "n_source_grounding_rows": source_grounding_audit_payload.get(
            "n_source_grounding_rows",
            0,
        ),
        "n_source_grounding_row_schema_valid": source_grounding_audit_payload.get(
            "n_row_schema_valid",
            0,
        ),
        "n_source_grounding_row_schema_invalid": source_grounding_audit_payload.get(
            "n_row_schema_invalid",
            0,
        ),
        "n_dominated_route_witnesses": minimal_delta_audit_payload.get(
            "n_dominated_route_witnesses",
            0,
        ),
        "n_portable_work_packets": prover_adapter_contract_payload.get("n_packets", 0),
        "n_prover_adapter_packet_schema_valid": prover_adapter_contract_payload.get(
            "n_packet_schema_valid",
            0,
        ),
        "n_awaiting_adapter_mapping": prover_adapter_contract_payload.get(
            "n_awaiting_adapter_mapping",
            0,
        ),
        "n_kernel_verified_claims_rejected": prover_adapter_contract_payload.get(
            "n_kernel_verified_claims_rejected",
            0,
        ),
        "n_prover_adapter_response_validation_row_schema_valid": prover_adapter_contract_payload.get(
            "n_response_validation_row_schema_valid",
            0,
        ),
        "n_prover_adapter_response_validation_row_schema_invalid": prover_adapter_contract_payload.get(
            "n_response_validation_row_schema_invalid",
            0,
        ),
        "n_adapter_registry_adapters": adapter_registry_payload.get("n_adapters", 0),
        "n_adapter_registry_row_schema_valid": adapter_registry_payload.get(
            "n_adapter_row_schema_valid",
            0,
        ),
        "n_adapter_registry_row_schema_invalid": adapter_registry_payload.get(
            "n_adapter_row_schema_invalid",
            0,
        ),
        "n_adapter_registry_ready": adapter_registry_payload.get(
            "n_ready_local_or_configured",
            0,
        ),
        "n_adapter_registry_audit_failed": adapter_registry_audit_payload.get(
            "n_failed",
            0,
        ),
        "n_adapter_registry_audit_row_schema_valid": adapter_registry_audit_payload.get(
            "n_adapter_row_schema_valid",
            0,
        ),
        "n_adapter_registry_audit_row_schema_invalid": adapter_registry_audit_payload.get(
            "n_adapter_row_schema_invalid",
            0,
        ),
        "n_adapter_registry_audit_jsonl_row_schema_valid": adapter_registry_audit_payload.get(
            "n_adapter_jsonl_row_schema_valid",
            0,
        ),
        "n_adapter_registry_audit_jsonl_row_schema_invalid": adapter_registry_audit_payload.get(
            "n_adapter_jsonl_row_schema_invalid",
            0,
        ),
        "n_adapter_registry_required_ids_present": adapter_registry_audit_payload.get(
            "n_required_adapter_ids_present",
            0,
        ),
        "n_adapter_registry_required_ids": adapter_registry_audit_payload.get(
            "n_required_adapter_ids",
            0,
        ),
        "n_component_resource_components": component_resource_registry_payload.get(
            "n_component_rows",
            0,
        ),
        "n_component_resource_component_row_schema_valid": component_resource_registry_payload.get(
            "n_component_row_schema_valid",
            0,
        ),
        "n_component_resource_component_row_schema_invalid": component_resource_registry_payload.get(
            "n_component_row_schema_invalid",
            0,
        ),
        "n_component_resource_resources": component_resource_registry_payload.get(
            "n_resources",
            0,
        ),
        "n_component_resource_resource_row_schema_valid": component_resource_registry_payload.get(
            "n_resource_row_schema_valid",
            0,
        ),
        "n_component_resource_resource_row_schema_invalid": component_resource_registry_payload.get(
            "n_resource_row_schema_invalid",
            0,
        ),
        "n_component_resource_contracts": component_resource_registry_payload.get(
            "n_resource_contract_rows",
            0,
        ),
        "n_component_resource_contracts_ok": component_resource_registry_payload.get(
            "n_resource_contract_rows_ok",
            0,
        ),
        "n_component_resource_contract_row_schema_valid": component_resource_registry_audit_payload.get(
            "n_resource_contract_row_schema_valid",
            0,
        ),
        "n_component_resource_contract_row_schema_invalid": component_resource_registry_audit_payload.get(
            "n_resource_contract_row_schema_invalid",
            0,
        ),
        "n_component_resource_execution_plans": component_resource_registry_payload.get(
            "n_execution_plan_rows",
            0,
        ),
        "n_component_resource_execution_plans_ok": component_resource_registry_payload.get(
            "n_execution_plan_rows_ok",
            0,
        ),
        "n_component_resource_execution_plan_schema_valid": component_resource_registry_audit_payload.get(
            "n_execution_plan_schema_valid",
            0,
        ),
        "n_component_resource_execution_plan_schema_invalid": component_resource_registry_audit_payload.get(
            "n_execution_plan_schema_invalid",
            0,
        ),
        "n_component_resource_frontier": component_resource_registry_payload.get(
            "n_frontier_resources",
            0,
        ),
        "n_component_resource_mcp_cli": component_resource_registry_payload.get(
            "n_mcp_or_cli_resources",
            0,
        ),
        "n_component_resource_resources_with_capability_tags": component_resource_registry_payload.get(
            "n_resources_with_capability_tags",
            0,
        ),
        "n_component_resource_resources_with_validation_signals": component_resource_registry_payload.get(
            "n_resources_with_validation_signals",
            0,
        ),
        "n_component_resource_components_with_quality_signals": component_resource_registry_payload.get(
            "n_component_rows_with_required_quality_signals",
            0,
        ),
        "n_component_resource_execution_plans_with_quality_gates": component_resource_registry_payload.get(
            "n_execution_plans_with_quality_gates",
            0,
        ),
        "n_component_resource_contracts_with_response_validation_signals": component_resource_registry_payload.get(
            "n_resource_contracts_with_response_validation_signals",
            0,
        ),
        "n_component_resource_audit_failed": component_resource_registry_audit_payload.get(
            "n_failed",
            0,
        ),
        "n_component_resource_required_components_present": component_resource_registry_audit_payload.get(
            "n_required_component_ids_present",
            0,
        ),
        "n_component_resource_components_with_execution_plan": component_resource_registry_audit_payload.get(
            "n_components_with_execution_plan",
            0,
        ),
        "n_component_resource_audit_component_row_schema_valid": component_resource_registry_audit_payload.get(
            "n_component_row_schema_valid",
            0,
        ),
        "n_component_resource_audit_component_row_schema_invalid": component_resource_registry_audit_payload.get(
            "n_component_row_schema_invalid",
            0,
        ),
        "n_component_resource_required_components": component_resource_registry_audit_payload.get(
            "n_required_component_ids",
            0,
        ),
        "n_component_resource_required_resources_present": component_resource_registry_audit_payload.get(
            "n_required_resource_ids_present",
            0,
        ),
        "n_component_resource_required_resources": component_resource_registry_audit_payload.get(
            "n_required_resource_ids",
            0,
        ),
        "n_component_resource_audit_resource_row_schema_valid": component_resource_registry_audit_payload.get(
            "n_resource_row_schema_valid",
            0,
        ),
        "n_component_resource_audit_resource_row_schema_invalid": component_resource_registry_audit_payload.get(
            "n_resource_row_schema_invalid",
            0,
        ),
        "n_publication_bundle_execution_plan_schema_checked": publication_bundle_audit_payload.get(
            "n_component_execution_plan_schema_checked",
            0,
        ),
        "n_publication_bundle_execution_plan_schema_valid": publication_bundle_audit_payload.get(
            "n_component_execution_plan_schema_valid",
            0,
        ),
        "n_publication_bundle_component_row_schema_checked": publication_bundle_audit_payload.get(
            "n_component_resource_component_row_schema_checked",
            0,
        ),
        "n_publication_bundle_component_row_schema_valid": publication_bundle_audit_payload.get(
            "n_component_resource_component_row_schema_valid",
            0,
        ),
        "n_publication_bundle_resource_row_schema_checked": publication_bundle_audit_payload.get(
            "n_component_resource_resource_row_schema_checked",
            0,
        ),
        "n_publication_bundle_resource_row_schema_valid": publication_bundle_audit_payload.get(
            "n_component_resource_resource_row_schema_valid",
            0,
        ),
        "n_publication_bundle_contract_row_schema_checked": publication_bundle_audit_payload.get(
            "n_component_resource_contract_row_schema_checked",
            0,
        ),
        "n_publication_bundle_contract_row_schema_valid": publication_bundle_audit_payload.get(
            "n_component_resource_contract_row_schema_valid",
            0,
        ),
        "n_publication_bundle_prover_adapter_packet_schema_checked": publication_bundle_audit_payload.get(
            "n_prover_adapter_packet_schema_checked",
            0,
        ),
        "n_publication_bundle_prover_adapter_packet_schema_valid": publication_bundle_audit_payload.get(
            "n_prover_adapter_packet_schema_valid",
            0,
        ),
        "n_publication_bundle_optional_cross_prover_packet_trace_checked": publication_bundle_audit_payload.get(
            "n_optional_cross_prover_packet_trace_checked",
            0,
        ),
        "n_publication_bundle_optional_cross_prover_packet_trace_valid": publication_bundle_audit_payload.get(
            "n_optional_cross_prover_packet_trace_valid",
            0,
        ),
        "n_publication_bundle_benchmark_routes": publication_bundle_payload.get(
            "benchmark_summary",
            {},
        ).get("n_routes", 0),
        "n_publication_bundle_benchmark_route_schema_checked": publication_bundle_audit_payload.get(
            "n_benchmark_route_row_schema_checked",
            0,
        ),
        "n_publication_bundle_benchmark_route_schema_valid": publication_bundle_audit_payload.get(
            "n_benchmark_route_row_schema_valid",
            0,
        ),
        "n_publication_bundle_optional_evaluation_row_schema_checked": publication_bundle_audit_payload.get(
            "n_optional_evaluation_row_schema_checked",
            0,
        ),
        "n_publication_bundle_optional_evaluation_row_schema_valid": publication_bundle_audit_payload.get(
            "n_optional_evaluation_row_schema_valid",
            0,
        ),
        "n_publication_bundle_optional_evaluation_ground_truth_file_checked": publication_bundle_audit_payload.get(
            "n_optional_evaluation_ground_truth_file_checked",
            0,
        ),
        "n_publication_bundle_optional_evaluation_ground_truth_file_valid": publication_bundle_audit_payload.get(
            "n_optional_evaluation_ground_truth_file_valid",
            0,
        ),
        "n_publication_bundle_optional_evaluation_ground_truth_match_checked": publication_bundle_audit_payload.get(
            "n_optional_evaluation_ground_truth_match_checked",
            0,
        ),
        "n_publication_bundle_optional_evaluation_ground_truth_match_valid": publication_bundle_audit_payload.get(
            "n_optional_evaluation_ground_truth_match_valid",
            0,
        ),
        "n_publication_bundle_optional_evaluation_ground_truth_primitive_checked": publication_bundle_audit_payload.get(
            "n_optional_evaluation_ground_truth_primitive_checked",
            0,
        ),
        "n_publication_bundle_optional_evaluation_ground_truth_primitive_valid": publication_bundle_audit_payload.get(
            "n_optional_evaluation_ground_truth_primitive_valid",
            0,
        ),
        "n_evaluation_rows": evaluation_payload.get("n_evaluation_rows", 0),
        "n_evaluation_row_schema_valid": evaluation_payload.get(
            "n_evaluation_row_schema_valid",
            0,
        ),
        "n_evaluation_row_schema_invalid": evaluation_payload.get(
            "n_evaluation_row_schema_invalid",
            0,
        ),
        "n_evaluation_matched_ground_truth": evaluation_payload.get(
            "n_matched_ground_truth",
            0,
        ),
        "n_evaluation_missing_ground_truth": evaluation_payload.get(
            "n_missing_ground_truth",
            0,
        ),
        "n_evaluation_alignment_contract_ok": evaluation_payload.get(
            "n_alignment_contract_ok",
            0,
        ),
        "n_evaluation_feedback_loop_ready": evaluation_payload.get(
            "n_feedback_loop_ready",
            0,
        ),
        "n_evaluation_unaligned_primitives": evaluation_payload.get(
            "n_unaligned_primitives",
            0,
        ),
        "n_evaluation_realization_missing_selected_formal_primitives": evaluation_payload.get(
            "n_realization_missing_selected_formal_primitives",
            0,
        ),
        "n_evaluation_realization_missing_delta_alignment_primitives": evaluation_payload.get(
            "n_realization_missing_delta_alignment_primitives",
            0,
        ),
        "n_evaluation_rows_with_incomplete_cost_hint_baseline_coverage": evaluation_payload.get(
            "n_rows_with_incomplete_cost_hint_baseline_coverage",
            0,
        ),
        "n_evaluation_realization_cost_hint_baseline_primitives": evaluation_payload.get(
            "n_realization_cost_hint_baseline_primitives",
            0,
        ),
        "n_evaluation_realization_omitted_cost_hint_primitives": evaluation_payload.get(
            "n_realization_omitted_cost_hint_primitives",
            0,
        ),
        "evaluation_realization_missing_selected_formal_primitives": evaluation_payload.get(
            "realization_missing_selected_formal_primitives",
            (),
        ),
        "evaluation_realization_missing_delta_alignment_primitives": evaluation_payload.get(
            "realization_missing_delta_alignment_primitives",
            (),
        ),
        "evaluation_realization_cost_hint_baseline_primitives": evaluation_payload.get(
            "realization_cost_hint_baseline_primitives",
            (),
        ),
        "evaluation_realization_omitted_cost_hint_primitives": evaluation_payload.get(
            "realization_omitted_cost_hint_primitives",
            (),
        ),
        "evaluation_realization_missing_primitives_by_route": evaluation_payload.get(
            "realization_missing_primitives_by_route",
            (),
        ),
        "n_evaluation_rows_with_llm_route_planner_trace": evaluation_payload.get(
            "n_rows_with_llm_route_planner_trace",
            0,
        ),
        "n_evaluation_rows_with_llm_route_planner_model_tier": evaluation_payload.get(
            "n_rows_with_llm_route_planner_model_tier",
            0,
        ),
        "n_evaluation_rows_with_llm_route_planner_route_adoption_status": (
            evaluation_payload.get(
                "n_rows_with_llm_route_planner_route_adoption_status",
                0,
            )
        ),
        "n_evaluation_rows_ready_for_route_adoption": evaluation_payload.get(
            "n_rows_ready_for_route_adoption",
            0,
        ),
        "n_evaluation_rows_pending_refinement_before_route_adoption": (
            evaluation_payload.get(
                "n_rows_pending_refinement_before_route_adoption",
                0,
            )
        ),
        "n_evaluation_llm_route_adoption_blockers": evaluation_payload.get(
            "n_llm_route_adoption_blockers",
            0,
        ),
        "n_evaluation_llm_route_adoption_pending_quality_control_blockers": (
            evaluation_payload.get(
                "n_llm_route_adoption_pending_quality_control_blockers",
                0,
            )
        ),
        "n_evaluation_llm_route_adoption_pending_source_grounding_blockers": (
            evaluation_payload.get(
                "n_llm_route_adoption_pending_source_grounding_blockers",
                0,
            )
        ),
        "evaluation_llm_route_adoption_blockers": evaluation_payload.get(
            "llm_route_adoption_blockers",
            (),
        ),
        "evaluation_llm_route_adoption_blocker_counts": evaluation_payload.get(
            "llm_route_adoption_blocker_counts",
            {},
        ),
        "evaluation_by_llm_route_adoption_status": evaluation_payload.get(
            "evaluation_by_llm_route_adoption_status",
            {},
        ),
        "evaluation_by_llm_route_adoption_blocker": evaluation_payload.get(
            "evaluation_by_llm_route_adoption_blocker",
            {},
        ),
        "n_evaluation_rows_with_llm_route_planner_generator_metadata": evaluation_payload.get(
            "n_rows_with_llm_route_planner_generator_metadata",
            0,
        ),
        "n_evaluation_rows_with_llm_route_planner_request_contract_blocked": evaluation_payload.get(
            "n_rows_with_llm_route_planner_request_contract_blocked",
            0,
        ),
        "n_evaluation_rows_with_llm_route_planner_errors": evaluation_payload.get(
            "n_rows_with_llm_route_planner_errors",
            0,
        ),
        "n_evaluation_llm_route_planner_errors": evaluation_payload.get(
            "n_llm_route_planner_errors",
            0,
        ),
        "n_evaluation_llm_route_planner_generation_errors": evaluation_payload.get(
            "n_llm_route_planner_generation_errors",
            0,
        ),
        "evaluation_by_llm_model_tier": evaluation_payload.get(
            "evaluation_by_llm_model_tier",
            {},
        ),
        "mean_evaluation_route_recall": evaluation_payload.get(
            "mean_route_recall",
            0.0,
        ),
        "mean_evaluation_delta_precision": evaluation_payload.get(
            "mean_delta_precision",
            0.0,
        ),
        "mean_evaluation_alignment_coverage": evaluation_payload.get(
            "mean_alignment_coverage",
            0.0,
        ),
        "n_publication_bundle_optional_interactive_decision_policy_row_schema_checked": publication_bundle_audit_payload.get(
            "n_optional_interactive_decision_policy_row_schema_checked",
            0,
        ),
        "n_publication_bundle_optional_interactive_decision_policy_row_schema_valid": publication_bundle_audit_payload.get(
            "n_optional_interactive_decision_policy_row_schema_valid",
            0,
        ),
        "n_publication_bundle_optional_interactive_decision_policy_link_checked": publication_bundle_audit_payload.get(
            "n_optional_interactive_decision_policy_link_checked",
            0,
        ),
        "n_publication_bundle_optional_interactive_decision_policy_link_valid": publication_bundle_audit_payload.get(
            "n_optional_interactive_decision_policy_link_valid",
            0,
        ),
        "n_publication_bundle_optional_interactive_session_row_schema_checked": publication_bundle_audit_payload.get(
            "n_optional_interactive_session_row_schema_checked",
            0,
        ),
        "n_publication_bundle_optional_interactive_session_row_schema_valid": publication_bundle_audit_payload.get(
            "n_optional_interactive_session_row_schema_valid",
            0,
        ),
        "n_publication_bundle_optional_interactive_session_resource_response_status_checked": publication_bundle_audit_payload.get(
            "n_optional_interactive_session_resource_response_status_checked",
            0,
        ),
        "n_publication_bundle_optional_interactive_session_resource_response_status_valid": publication_bundle_audit_payload.get(
            "n_optional_interactive_session_resource_response_status_valid",
            0,
        ),
        "n_publication_bundle_optional_interactive_session_generic_prover_fields_checked": publication_bundle_audit_payload.get(
            "n_optional_interactive_session_generic_prover_fields_checked",
            0,
        ),
        "n_publication_bundle_optional_interactive_session_generic_prover_fields_valid": publication_bundle_audit_payload.get(
            "n_optional_interactive_session_generic_prover_fields_valid",
            0,
        ),
        "n_publication_bundle_optional_refinement_evidence_row_schema_checked": publication_bundle_audit_payload.get(
            "n_optional_refinement_evidence_row_schema_checked",
            0,
        ),
        "n_publication_bundle_optional_refinement_evidence_row_schema_valid": publication_bundle_audit_payload.get(
            "n_optional_refinement_evidence_row_schema_valid",
            0,
        ),
        "n_publication_bundle_optional_refinement_adapter_response_schema_checked": publication_bundle_audit_payload.get(
            "n_optional_refinement_adapter_response_schema_checked",
            0,
        ),
        "n_publication_bundle_optional_refinement_adapter_response_schema_valid": publication_bundle_audit_payload.get(
            "n_optional_refinement_adapter_response_schema_valid",
            0,
        ),
        "n_publication_bundle_optional_minimal_delta_audit_feedback_response_schema_checked": publication_bundle_audit_payload.get(
            "n_optional_minimal_delta_audit_feedback_response_schema_checked",
            0,
        ),
        "n_publication_bundle_optional_minimal_delta_audit_feedback_response_schema_valid": publication_bundle_audit_payload.get(
            "n_optional_minimal_delta_audit_feedback_response_schema_valid",
            0,
        ),
        "n_publication_bundle_optional_prover_adapter_feedback_response_schema_checked": publication_bundle_audit_payload.get(
            "n_optional_prover_adapter_feedback_response_schema_checked",
            0,
        ),
        "n_publication_bundle_optional_prover_adapter_feedback_response_schema_valid": publication_bundle_audit_payload.get(
            "n_optional_prover_adapter_feedback_response_schema_valid",
            0,
        ),
        "n_publication_bundle_optional_local_adapter_response_schema_checked": publication_bundle_audit_payload.get(
            "n_optional_local_adapter_response_schema_checked",
            0,
        ),
        "n_publication_bundle_optional_local_adapter_response_schema_valid": publication_bundle_audit_payload.get(
            "n_optional_local_adapter_response_schema_valid",
            0,
        ),
        "n_publication_bundle_optional_route_stability_audit_row_schema_checked": publication_bundle_audit_payload.get(
            "n_optional_route_stability_audit_row_schema_checked",
            0,
        ),
        "n_publication_bundle_optional_route_stability_audit_row_schema_valid": publication_bundle_audit_payload.get(
            "n_optional_route_stability_audit_row_schema_valid",
            0,
        ),
        "n_publication_bundle_optional_route_stability_resource_response_status_checked": publication_bundle_audit_payload.get(
            "n_optional_route_stability_resource_response_status_checked",
            0,
        ),
        "n_publication_bundle_optional_route_stability_resource_response_status_valid": publication_bundle_audit_payload.get(
            "n_optional_route_stability_resource_response_status_valid",
            0,
        ),
        "n_publication_bundle_optional_route_stability_generic_prover_fields_checked": publication_bundle_audit_payload.get(
            "n_optional_route_stability_generic_prover_fields_checked",
            0,
        ),
        "n_publication_bundle_optional_route_stability_generic_prover_fields_valid": publication_bundle_audit_payload.get(
            "n_optional_route_stability_generic_prover_fields_valid",
            0,
        ),
        "n_publication_bundle_optional_route_revision_overlay_row_schema_checked": publication_bundle_audit_payload.get(
            "n_optional_route_revision_overlay_row_schema_checked",
            0,
        ),
        "n_publication_bundle_optional_route_revision_overlay_row_schema_valid": publication_bundle_audit_payload.get(
            "n_optional_route_revision_overlay_row_schema_valid",
            0,
        ),
        "n_publication_bundle_optional_route_revision_resource_response_evidence_ref_checked": publication_bundle_audit_payload.get(
            "n_optional_route_revision_resource_response_evidence_ref_checked",
            0,
        ),
        "n_publication_bundle_optional_route_revision_resource_response_evidence_ref_valid": publication_bundle_audit_payload.get(
            "n_optional_route_revision_resource_response_evidence_ref_valid",
            0,
        ),
        "n_publication_bundle_optional_route_revision_resource_response_trace_checked": publication_bundle_audit_payload.get(
            "n_optional_route_revision_resource_response_trace_checked",
            0,
        ),
        "n_publication_bundle_optional_route_revision_resource_response_trace_valid": publication_bundle_audit_payload.get(
            "n_optional_route_revision_resource_response_trace_valid",
            0,
        ),
        "n_publication_bundle_optional_route_revision_resource_response_status_checked": publication_bundle_audit_payload.get(
            "n_optional_route_revision_resource_response_status_checked",
            0,
        ),
        "n_publication_bundle_optional_route_revision_resource_response_status_valid": publication_bundle_audit_payload.get(
            "n_optional_route_revision_resource_response_status_valid",
            0,
        ),
        "n_publication_bundle_optional_route_replan_handoff_row_schema_checked": publication_bundle_audit_payload.get(
            "n_optional_route_replan_handoff_row_schema_checked",
            0,
        ),
        "n_publication_bundle_optional_route_replan_handoff_row_schema_valid": publication_bundle_audit_payload.get(
            "n_optional_route_replan_handoff_row_schema_valid",
            0,
        ),
        "n_publication_bundle_optional_route_replan_handoff_seed_alignment_checked": publication_bundle_audit_payload.get(
            "n_optional_route_replan_handoff_seed_alignment_checked",
            0,
        ),
        "n_publication_bundle_optional_route_replan_handoff_seed_alignment_valid": publication_bundle_audit_payload.get(
            "n_optional_route_replan_handoff_seed_alignment_valid",
            0,
        ),
        "n_publication_bundle_optional_route_replan_handoff_seed_dag_checked": publication_bundle_audit_payload.get(
            "n_optional_route_replan_handoff_seed_dag_checked",
            0,
        ),
        "n_publication_bundle_optional_route_replan_handoff_seed_dag_valid": publication_bundle_audit_payload.get(
            "n_optional_route_replan_handoff_seed_dag_valid",
            0,
        ),
        "n_publication_bundle_optional_route_replan_handoff_audit_row_schema_checked": publication_bundle_audit_payload.get(
            "n_optional_route_replan_handoff_audit_row_schema_checked",
            0,
        ),
        "n_publication_bundle_optional_route_replan_handoff_audit_row_schema_valid": publication_bundle_audit_payload.get(
            "n_optional_route_replan_handoff_audit_row_schema_valid",
            0,
        ),
        "n_publication_bundle_optional_ablation_study_row_schema_checked": publication_bundle_audit_payload.get(
            "n_optional_ablation_study_row_schema_checked",
            0,
        ),
        "n_publication_bundle_optional_ablation_study_row_schema_valid": publication_bundle_audit_payload.get(
            "n_optional_ablation_study_row_schema_valid",
            0,
        ),
        "n_ablation_variants": ablation_study_payload.get(
            "n_ablation_variants",
            0,
        ),
        "n_ablation_ok": ablation_study_payload.get("n_ok", 0),
        "n_ablation_row_schema_valid": ablation_study_payload.get(
            "n_row_schema_valid",
            0,
        ),
        "n_ablation_row_schema_invalid": ablation_study_payload.get(
            "n_row_schema_invalid",
            0,
        ),
        "ablation_best_variant_by_route_recall": ablation_study_payload.get(
            "best_variant_by_route_recall",
            "",
        ),
        "ablation_largest_route_recall_drop_variant": ablation_study_payload.get(
            "largest_route_recall_drop_variant",
            "",
        ),
        "ablation_largest_delta_recall_drop_variant": ablation_study_payload.get(
            "largest_delta_recall_drop_variant",
            "",
        ),
        "n_publication_bundle_optional_portable_plan_audit_row_schema_checked": publication_bundle_audit_payload.get(
            "n_optional_portable_plan_audit_row_schema_checked",
            0,
        ),
        "n_publication_bundle_optional_portable_plan_audit_row_schema_valid": publication_bundle_audit_payload.get(
            "n_optional_portable_plan_audit_row_schema_valid",
            0,
        ),
        "n_publication_bundle_optional_proof_state_triage_row_schema_checked": publication_bundle_audit_payload.get(
            "n_optional_proof_state_triage_row_schema_checked",
            0,
        ),
        "n_publication_bundle_optional_proof_state_triage_row_schema_valid": publication_bundle_audit_payload.get(
            "n_optional_proof_state_triage_row_schema_valid",
            0,
        ),
        "n_publication_bundle_optional_proof_state_triage_generic_prover_fields_checked": publication_bundle_audit_payload.get(
            "n_optional_proof_state_triage_generic_prover_fields_checked",
            0,
        ),
        "n_publication_bundle_optional_proof_state_triage_generic_prover_fields_valid": publication_bundle_audit_payload.get(
            "n_optional_proof_state_triage_generic_prover_fields_valid",
            0,
        ),
        "n_publication_bundle_optional_library_coverage_map_row_schema_checked": publication_bundle_audit_payload.get(
            "n_optional_library_coverage_map_row_schema_checked",
            0,
        ),
        "n_publication_bundle_optional_library_coverage_map_row_schema_valid": publication_bundle_audit_payload.get(
            "n_optional_library_coverage_map_row_schema_valid",
            0,
        ),
        "n_publication_bundle_optional_primitive_action_queue_row_schema_checked": publication_bundle_audit_payload.get(
            "n_optional_primitive_action_queue_row_schema_checked",
            0,
        ),
        "n_publication_bundle_optional_primitive_action_queue_row_schema_valid": publication_bundle_audit_payload.get(
            "n_optional_primitive_action_queue_row_schema_valid",
            0,
        ),
        "n_publication_bundle_optional_action_resource_plan_row_schema_checked": publication_bundle_audit_payload.get(
            "n_optional_action_resource_plan_row_schema_checked",
            0,
        ),
        "n_publication_bundle_optional_action_resource_plan_row_schema_valid": publication_bundle_audit_payload.get(
            "n_optional_action_resource_plan_row_schema_valid",
            0,
        ),
        "n_publication_bundle_optional_resource_request_queue_row_schema_checked": publication_bundle_audit_payload.get(
            "n_optional_resource_request_queue_row_schema_checked",
            0,
        ),
        "n_publication_bundle_optional_resource_request_queue_row_schema_valid": publication_bundle_audit_payload.get(
            "n_optional_resource_request_queue_row_schema_valid",
            0,
        ),
        "n_publication_bundle_optional_resource_request_contract_alignment_checked": publication_bundle_audit_payload.get(
            "n_optional_resource_request_contract_alignment_checked",
            0,
        ),
        "n_publication_bundle_optional_resource_request_contract_alignment_valid": publication_bundle_audit_payload.get(
            "n_optional_resource_request_contract_alignment_valid",
            0,
        ),
        "n_publication_bundle_optional_resource_request_action_plan_ref_checked": publication_bundle_audit_payload.get(
            "n_optional_resource_request_action_plan_ref_checked",
            0,
        ),
        "n_publication_bundle_optional_resource_request_action_plan_ref_valid": publication_bundle_audit_payload.get(
            "n_optional_resource_request_action_plan_ref_valid",
            0,
        ),
        "n_publication_bundle_optional_resource_request_payload_identity_checked": publication_bundle_audit_payload.get(
            "n_optional_resource_request_payload_identity_checked",
            0,
        ),
        "n_publication_bundle_optional_resource_request_payload_identity_valid": publication_bundle_audit_payload.get(
            "n_optional_resource_request_payload_identity_valid",
            0,
        ),
        "n_publication_bundle_optional_resource_request_dispatch_spec_checked": publication_bundle_audit_payload.get(
            "n_optional_resource_request_dispatch_spec_checked",
            0,
        ),
        "n_publication_bundle_optional_resource_request_dispatch_spec_valid": publication_bundle_audit_payload.get(
            "n_optional_resource_request_dispatch_spec_valid",
            0,
        ),
        "n_publication_bundle_optional_resource_response_ledger_row_schema_checked": publication_bundle_audit_payload.get(
            "n_optional_resource_response_ledger_row_schema_checked",
            0,
        ),
        "n_publication_bundle_optional_resource_response_ledger_row_schema_valid": publication_bundle_audit_payload.get(
            "n_optional_resource_response_ledger_row_schema_valid",
            0,
        ),
        "n_publication_bundle_optional_resource_response_request_ref_checked": publication_bundle_audit_payload.get(
            "n_optional_resource_response_request_ref_checked",
            0,
        ),
        "n_publication_bundle_optional_resource_response_request_ref_valid": publication_bundle_audit_payload.get(
            "n_optional_resource_response_request_ref_valid",
            0,
        ),
        "n_publication_bundle_optional_resource_response_contract_field_accounting_checked": publication_bundle_audit_payload.get(
            "n_optional_resource_response_contract_field_accounting_checked",
            0,
        ),
        "n_publication_bundle_optional_resource_response_contract_field_accounting_valid": publication_bundle_audit_payload.get(
            "n_optional_resource_response_contract_field_accounting_valid",
            0,
        ),
        "n_library_coverage_rows": library_coverage_map_payload.get(
            "n_coverage_rows",
            0,
        ),
        "n_library_coverage_ok": library_coverage_map_payload.get("n_ok", 0),
        "n_library_coverage_failed": library_coverage_map_payload.get("n_failed", 0),
        "n_library_coverage_exact_exists": library_coverage_map_payload.get(
            "n_exact_exists",
            0,
        ),
        "n_library_coverage_near_exists": library_coverage_map_payload.get(
            "n_near_exists",
            0,
        ),
        "n_library_coverage_wrapper_needed": library_coverage_map_payload.get(
            "n_wrapper_needed",
            0,
        ),
        "n_library_coverage_bridge_needed": library_coverage_map_payload.get(
            "n_bridge_needed",
            0,
        ),
        "n_library_coverage_source_port_needed": library_coverage_map_payload.get(
            "n_source_port_needed",
            0,
        ),
        "n_library_coverage_definition_or_theory_missing": library_coverage_map_payload.get(
            "n_definition_or_theory_missing",
            0,
        ),
        "n_library_coverage_unknown_or_unaligned": library_coverage_map_payload.get(
            "n_unknown_or_unaligned",
            0,
        ),
        "n_library_coverage_rows_with_alignment": library_coverage_map_payload.get(
            "n_rows_with_alignment",
            0,
        ),
        "n_library_coverage_rows_with_candidate_declaration_rows": library_coverage_map_payload.get(
            "n_rows_with_candidate_declaration_rows",
            0,
        ),
        "n_library_coverage_candidate_declaration_rows": library_coverage_map_payload.get(
            "n_candidate_declaration_rows",
            0,
        ),
        "n_library_coverage_row_schema_valid": library_coverage_map_payload.get(
            "n_row_schema_valid",
            0,
        ),
        "n_library_coverage_row_schema_invalid": library_coverage_map_payload.get(
            "n_row_schema_invalid",
            0,
        ),
        "n_primitive_action_queue_items": primitive_action_queue_payload.get(
            "n_action_items",
            0,
        ),
        "n_primitive_action_queue_ok": primitive_action_queue_payload.get("n_ok", 0),
        "n_primitive_action_queue_failed": primitive_action_queue_payload.get(
            "n_failed",
            0,
        ),
        "n_primitive_action_queue_target_prover_replay": primitive_action_queue_payload.get(
            "n_target_prover_replay",
            0,
        ),
        "n_primitive_action_queue_compose_existing_declarations": primitive_action_queue_payload.get(
            "n_compose_existing_declarations",
            0,
        ),
        "n_primitive_action_queue_write_wrapper": primitive_action_queue_payload.get(
            "n_write_wrapper",
            0,
        ),
        "n_primitive_action_queue_prove_bridge_lemma": primitive_action_queue_payload.get(
            "n_prove_bridge_lemma",
            0,
        ),
        "n_primitive_action_queue_source_port": primitive_action_queue_payload.get(
            "n_source_port",
            0,
        ),
        "n_primitive_action_queue_design_new_theory_fragment": primitive_action_queue_payload.get(
            "n_design_new_theory_fragment",
            0,
        ),
        "n_primitive_action_queue_rerun_library_alignment": primitive_action_queue_payload.get(
            "n_rerun_library_alignment",
            0,
        ),
        "n_primitive_action_queue_with_candidate_declaration_rows": primitive_action_queue_payload.get(
            "n_with_candidate_declaration_rows",
            0,
        ),
        "n_primitive_action_queue_candidate_declaration_rows": primitive_action_queue_payload.get(
            "n_candidate_declaration_rows",
            0,
        ),
        "n_primitive_action_queue_row_schema_valid": primitive_action_queue_payload.get(
            "n_row_schema_valid",
            0,
        ),
        "n_primitive_action_queue_row_schema_invalid": primitive_action_queue_payload.get(
            "n_row_schema_invalid",
            0,
        ),
        "n_action_resource_plan_rows": action_resource_plan_payload.get(
            "n_resource_plan_rows",
            0,
        ),
        "n_action_resource_plan_ok": action_resource_plan_payload.get("n_ok", 0),
        "n_action_resource_plan_failed": action_resource_plan_payload.get(
            "n_failed",
            0,
        ),
        "n_action_resource_plan_row_schema_valid": action_resource_plan_payload.get(
            "n_row_schema_valid",
            0,
        ),
        "n_action_resource_plan_row_schema_invalid": action_resource_plan_payload.get(
            "n_row_schema_invalid",
            0,
        ),
        "n_action_resource_plan_with_local_first_resources": action_resource_plan_payload.get(
            "n_with_local_first_resources",
            0,
        ),
        "n_action_resource_plan_with_frontier_resources": action_resource_plan_payload.get(
            "n_with_frontier_escalation_resources",
            0,
        ),
        "n_action_resource_plan_with_resource_contracts": action_resource_plan_payload.get(
            "n_with_resource_contracts",
            0,
        ),
        "n_action_resource_plan_with_candidate_declaration_rows": action_resource_plan_payload.get(
            "n_with_candidate_declaration_rows",
            0,
        ),
        "n_action_resource_plan_candidate_declaration_rows": action_resource_plan_payload.get(
            "n_candidate_declaration_rows",
            0,
        ),
        "n_resource_request_rows": resource_request_queue_payload.get(
            "n_resource_request_rows",
            0,
        ),
        "n_resource_request_ok": resource_request_queue_payload.get("n_ok", 0),
        "n_resource_request_failed": resource_request_queue_payload.get("n_failed", 0),
        "n_resource_request_local_first": resource_request_queue_payload.get(
            "n_local_first_requests",
            0,
        ),
        "n_resource_request_frontier_escalation": resource_request_queue_payload.get(
            "n_frontier_escalation_requests",
            0,
        ),
        "n_resource_request_distinct_resources": resource_request_queue_payload.get(
            "n_distinct_resources",
            0,
        ),
        "n_resource_request_self_contained_payloads": resource_request_queue_payload.get(
            "n_self_contained_request_payloads",
            0,
        ),
        "n_resource_request_payload_identity_mismatches": resource_request_queue_payload.get(
            "n_request_payload_identity_mismatches",
            0,
        ),
        "n_resource_request_dispatch_specs": resource_request_queue_payload.get(
            "n_with_dispatch_specs",
            0,
        ),
        "n_resource_request_dispatch_spec_identity_valid": resource_request_queue_payload.get(
            "n_dispatch_spec_identity_valid",
            0,
        ),
        "n_resource_request_dispatch_spec_identity_mismatches": resource_request_queue_payload.get(
            "n_dispatch_spec_identity_mismatches",
            0,
        ),
        "n_resource_request_with_candidate_declaration_rows": resource_request_queue_payload.get(
            "n_with_candidate_declaration_rows",
            0,
        ),
        "n_resource_request_candidate_declaration_rows": resource_request_queue_payload.get(
            "n_candidate_declaration_rows",
            0,
        ),
        "n_resource_request_row_schema_valid": resource_request_queue_payload.get(
            "n_row_schema_valid",
            0,
        ),
        "n_resource_request_row_schema_invalid": resource_request_queue_payload.get(
            "n_row_schema_invalid",
            0,
        ),
        "n_resource_response_ledger_rows": resource_response_ledger_payload.get(
            "n_ledger_rows",
            0,
        ),
        "n_resource_response_ledger_ok": resource_response_ledger_payload.get(
            "n_ok",
            0,
        ),
        "n_resource_response_ledger_response_present": resource_response_ledger_payload.get(
            "n_response_present",
            0,
        ),
        "n_resource_response_ledger_awaiting": resource_response_ledger_payload.get(
            "n_awaiting_response",
            0,
        ),
        "n_resource_response_ledger_contract_ok": resource_response_ledger_payload.get(
            "n_response_contract_ok",
            0,
        ),
        "n_resource_response_ledger_request_playbook_present": resource_response_ledger_payload.get(
            "n_request_playbook_present",
            0,
        ),
        "n_resource_response_ledger_playbook_grounded": resource_response_ledger_payload.get(
            "n_response_playbook_grounded",
            0,
        ),
        "n_resource_response_ledger_playbook_grounding_failures": resource_response_ledger_payload.get(
            "n_response_playbook_grounding_failures",
            0,
        ),
        "n_resource_response_ledger_request_mismatches": resource_response_ledger_payload.get(
            "n_response_request_mismatches",
            0,
        ),
        "n_resource_response_ledger_route_revision_recommended": resource_response_ledger_payload.get(
            "n_route_revision_recommended",
            0,
        ),
        "n_resource_response_ledger_rejected": resource_response_ledger_payload.get(
            "n_rejected",
            0,
        ),
        "n_resource_response_ledger_row_schema_valid": resource_response_ledger_payload.get(
            "n_ledger_row_schema_valid",
            0,
        ),
        "n_resource_response_ledger_row_schema_invalid": resource_response_ledger_payload.get(
            "n_ledger_row_schema_invalid",
            0,
        ),
        "n_route_alignment_edges": plan_payload.get("n_route_alignment_edges", 0),
        "n_route_alignment_edge_schema_valid": plan_payload.get(
            "n_route_alignment_edge_schema_valid",
            0,
        ),
        "n_route_alignment_edge_schema_invalid": plan_payload.get(
            "n_route_alignment_edge_schema_invalid",
            0,
        ),
        "n_portable_plan_audit_route_alignment_edges": portable_plan_audit_payload.get(
            "n_route_alignment_edges",
            0,
        ),
        "n_portable_plan_audit_route_alignment_edge_schema_valid": portable_plan_audit_payload.get(
            "n_route_alignment_edge_schema_valid",
            0,
        ),
        "n_portable_plan_audit_route_alignment_edge_schema_invalid": portable_plan_audit_payload.get(
            "n_route_alignment_edge_schema_invalid",
            0,
        ),
        "n_portable_plan_audit_row_schema_valid": portable_plan_audit_payload.get(
            "n_row_schema_valid",
            0,
        ),
        "n_portable_plan_audit_row_schema_invalid": portable_plan_audit_payload.get(
            "n_row_schema_invalid",
            0,
        ),
        "n_refinement_items": refinement_queue_payload.get("n_refinement_items", 0),
        "n_refinement_ready": refinement_queue_payload.get("n_ready", 0),
        "n_refinement_item_schema_valid": refinement_queue_payload.get(
            "n_item_schema_valid",
            0,
        ),
        "n_refinement_item_schema_invalid": refinement_queue_payload.get(
            "n_item_schema_invalid",
            0,
        ),
        "n_refinement_formal_library_grounding_items": (
            refinement_queue_payload.get("n_formal_library_grounding_items", 0)
        ),
        "n_refinement_lean_library_grounding_items": (
            refinement_queue_payload.get("n_lean_library_grounding_items", 0)
        ),
        "n_refinement_responses": refinement_adapter_payload.get("n_responses", 0),
        "n_refinement_adapter_formal_grounding_responses": (
            refinement_adapter_payload.get("n_formal_grounding_responses", 0)
        ),
        "n_refinement_adapter_lean_grounding_responses": (
            refinement_adapter_payload.get("n_lean_grounding_responses", 0)
        ),
        "n_refinement_adapter_response_schema_valid": refinement_adapter_payload.get(
            "n_response_schema_valid",
            0,
        ),
        "n_refinement_adapter_response_schema_invalid": refinement_adapter_payload.get(
            "n_response_schema_invalid",
            0,
        ),
        "n_minimal_delta_audit_feedback_generated_responses": (
            minimal_delta_audit_feedback_adapter_payload.get(
                "n_generated_feedback_responses",
                0,
            )
        ),
        "n_minimal_delta_audit_feedback_merged_responses": (
            minimal_delta_audit_feedback_adapter_payload.get("n_merged_responses", 0)
        ),
        "n_minimal_delta_audit_feedback_response_schema_valid": (
            minimal_delta_audit_feedback_adapter_payload.get(
                "n_response_schema_valid",
                0,
            )
        ),
        "n_minimal_delta_audit_feedback_response_schema_invalid": (
            minimal_delta_audit_feedback_adapter_payload.get(
                "n_response_schema_invalid",
                0,
            )
        ),
        "n_minimal_delta_audit_feedback_merged_response_schema_valid": (
            minimal_delta_audit_feedback_adapter_payload.get(
                "n_merged_response_schema_valid",
                0,
            )
        ),
        "n_minimal_delta_audit_feedback_merged_response_schema_invalid": (
            minimal_delta_audit_feedback_adapter_payload.get(
                "n_merged_response_schema_invalid",
                0,
            )
        ),
        "n_local_literature_responses": local_literature_adapter_payload.get(
            "n_local_literature_responses",
            0,
        ),
        "n_local_literature_source_hits": local_literature_adapter_payload.get(
            "n_source_hits",
            0,
        ),
        "n_local_literature_response_schema_valid": local_literature_adapter_payload.get(
            "n_local_response_schema_valid",
            0,
        ),
        "n_local_literature_response_schema_invalid": local_literature_adapter_payload.get(
            "n_local_response_schema_invalid",
            0,
        ),
        "n_local_formal_source_responses": local_formal_source_adapter_payload.get(
            "n_local_formal_source_responses",
            0,
        ),
        "n_local_formal_source_formal_grounding_rows": (
            local_formal_source_adapter_payload.get(
                "n_formal_library_grounding_rows",
                0,
            )
        ),
        "n_local_formal_source_legacy_lean_grounding_rows": (
            local_formal_source_adapter_payload.get(
                "n_lean_library_grounding_rows",
                0,
            )
        ),
        "n_local_formal_source_legacy_lean_declaration_hit_responses": (
            local_formal_source_adapter_payload.get(
                "n_responses_with_legacy_lean_declaration_hits",
                0,
            )
        ),
        "local_formal_source_adapter_legacy_field_aliases": (
            local_formal_source_adapter_payload.get(
                "legacy_formal_source_adapter_field_aliases",
                dict(LEGACY_FORMAL_SOURCE_ADAPTER_FIELD_ALIASES),
            )
        ),
        "n_local_formal_source_hits": local_formal_source_adapter_payload.get(
            "n_hits",
            0,
        ),
        "n_local_formal_source_response_schema_valid": local_formal_source_adapter_payload.get(
            "n_local_response_schema_valid",
            0,
        ),
        "n_local_formal_source_response_schema_invalid": local_formal_source_adapter_payload.get(
            "n_local_response_schema_invalid",
            0,
        ),
        "n_local_proof_state_responses": local_proof_state_adapter_payload.get(
            "n_local_proof_state_responses",
            0,
        ),
        "n_local_proof_state_target_proof_state_feedback_rows": (
            local_proof_state_adapter_payload.get(
                "n_target_proof_state_feedback_rows",
                0,
            )
        ),
        "n_local_proof_state_skipped_non_target_proof_state_feedback_rows": (
            local_proof_state_adapter_payload.get(
                "n_skipped_non_target_proof_state_feedback_rows",
                0,
            )
        ),
        "n_local_proof_state_target_prover_scaffold_accepted": (
            local_proof_state_adapter_payload.get("n_target_prover_scaffold_accepted", 0)
        ),
        "n_local_proof_state_target_prover_failed": (
            local_proof_state_adapter_payload.get("n_target_prover_failed", 0)
        ),
        "n_local_proof_state_target_prover_unavailable": (
            local_proof_state_adapter_payload.get("n_target_prover_unavailable", 0)
        ),
        "n_local_proof_state_non_target_prover_skeleton": (
            local_proof_state_adapter_payload.get("n_non_target_prover_skeleton", 0)
        ),
        "n_local_proof_state_unavailable": local_proof_state_adapter_payload.get(
            "n_local_lean_unavailable",
            0,
        ),
        "n_local_proof_state_placeholder_blocked": (
            local_proof_state_adapter_payload.get("n_placeholder_blocked", 0)
        ),
        "n_local_proof_state_formal_gap_scaffold_blocked": (
            local_proof_state_adapter_payload.get("n_formal_gap_scaffold_blocked", 0)
        ),
        "n_local_proof_state_missing_skeleton": (
            local_proof_state_adapter_payload.get("n_missing_skeleton", 0)
        ),
        "n_local_adapter_merged_responses": local_proof_state_adapter_payload.get(
            "n_merged_responses",
            0,
        ),
        "n_local_proof_state_response_schema_valid": local_proof_state_adapter_payload.get(
            "n_local_response_schema_valid",
            0,
        ),
        "n_local_proof_state_response_schema_invalid": local_proof_state_adapter_payload.get(
            "n_local_response_schema_invalid",
            0,
        ),
        "n_local_adapter_response_schema_valid": sum(
            int(payload.get("n_local_response_schema_valid", 0) or 0)
            for payload in (
                local_literature_adapter_payload,
                local_formal_source_adapter_payload,
                local_proof_state_adapter_payload,
            )
        ),
        "n_local_adapter_response_schema_invalid": sum(
            int(payload.get("n_local_response_schema_invalid", 0) or 0)
            for payload in (
                local_literature_adapter_payload,
                local_formal_source_adapter_payload,
                local_proof_state_adapter_payload,
            )
        ),
        "n_local_adapter_merged_response_schema_valid": local_proof_state_adapter_payload.get(
            "n_merged_response_schema_valid",
            0,
        ),
        "n_local_adapter_merged_response_schema_invalid": local_proof_state_adapter_payload.get(
            "n_merged_response_schema_invalid",
            0,
        ),
        "n_prover_adapter_feedback_generated_responses": (
            prover_adapter_feedback_payload.get("n_generated_feedback_responses", 0)
        ),
        "n_prover_adapter_feedback_merged_responses": (
            prover_adapter_feedback_payload.get("n_merged_responses", 0)
        ),
        "n_prover_adapter_feedback_validation_sources": (
            prover_adapter_feedback_payload.get("n_validation_sources", 0)
        ),
        "n_prover_adapter_feedback_validation_rows": (
            prover_adapter_feedback_payload.get("n_validation_rows", 0)
        ),
        "n_prover_adapter_feedback_matched_rows": (
            prover_adapter_feedback_payload.get("n_matched_proof_state_feedback_rows", 0)
        ),
        "n_prover_adapter_feedback_route_revision_recommended": (
            prover_adapter_feedback_payload.get("n_route_revision_recommended", 0)
        ),
        "n_prover_adapter_feedback_response_schema_valid": (
            prover_adapter_feedback_payload.get("n_response_schema_valid", 0)
        ),
        "n_prover_adapter_feedback_response_schema_invalid": (
            prover_adapter_feedback_payload.get("n_response_schema_invalid", 0)
        ),
        "n_prover_adapter_feedback_merged_response_schema_valid": (
            prover_adapter_feedback_payload.get("n_merged_response_schema_valid", 0)
        ),
        "n_prover_adapter_feedback_merged_response_schema_invalid": (
            prover_adapter_feedback_payload.get("n_merged_response_schema_invalid", 0)
        ),
        "n_refinement_contract_ok": refinement_evidence_payload.get(
            "n_contract_ok",
            0,
        ),
        "n_refinement_response_schema_valid": refinement_evidence_payload.get(
            "n_response_schema_valid",
            0,
        ),
        "n_refinement_response_schema_invalid": refinement_evidence_payload.get(
            "n_response_schema_invalid",
            0,
        ),
        "n_refinement_evidence_rows": refinement_evidence_payload.get(
            "n_evidence_rows",
            0,
        ),
        "n_refinement_evidence_formal_grounding": (
            refinement_evidence_payload.get("n_formal_grounding_evidence", 0)
        ),
        "n_refinement_evidence_lean_grounding": (
            refinement_evidence_payload.get("n_lean_grounding_evidence", 0)
        ),
        "n_refinement_evidence_row_schema_valid": refinement_evidence_payload.get(
            "n_evidence_row_schema_valid",
            0,
        ),
        "n_refinement_evidence_row_schema_invalid": refinement_evidence_payload.get(
            "n_evidence_row_schema_invalid",
            0,
        ),
        "n_route_revision_recommended": refinement_evidence_payload.get(
            "n_route_revision_recommended",
            0,
        ),
        "n_routes_with_revision": route_revision_overlay_payload.get(
            "n_routes_with_revision",
            0,
        ),
        "n_route_revision_overlay_refinement_evidence_proposals": (
            route_revision_overlay_payload.get(
                "n_refinement_evidence_route_revision_proposals",
                0,
            )
        ),
        "n_route_revision_overlay_resource_response_ledger_proposals": (
            route_revision_overlay_payload.get(
                "n_resource_response_ledger_route_revision_proposals",
                0,
            )
        ),
        "n_route_revision_overlay_row_schema_valid": route_revision_overlay_payload.get(
            "n_row_schema_valid",
            0,
        ),
        "n_route_revision_overlay_row_schema_invalid": route_revision_overlay_payload.get(
            "n_row_schema_invalid",
            0,
        ),
        "n_route_stability_needs_expansion": route_stability_audit_payload.get(
            "n_needs_expansion",
            0,
        ),
        "n_route_stability_stable": route_stability_audit_payload.get("n_stable", 0),
        "n_route_stability_rows": route_stability_audit_payload.get(
            "n_stability_rows",
            0,
        ),
        "n_route_stability_row_schema_valid": route_stability_audit_payload.get(
            "n_row_schema_valid",
            0,
        ),
        "n_route_stability_row_schema_invalid": route_stability_audit_payload.get(
            "n_row_schema_invalid",
            0,
        ),
        "n_route_replan_handoff_rows": route_replan_handoff_payload.get(
            "n_handoff_rows",
            0,
        ),
        "n_route_replan_handoff_row_schema_valid": route_replan_handoff_payload.get(
            "n_row_schema_valid",
            0,
        ),
        "n_route_replan_handoff_row_schema_invalid": route_replan_handoff_payload.get(
            "n_row_schema_invalid",
            0,
        ),
        "n_routes_requiring_replan": route_replan_handoff_payload.get(
            "n_routes_requiring_replan",
            0,
        ),
        "n_replan_seed_routes": route_replan_handoff_payload.get(
            "n_standalone_seed_routes",
            0,
        ),
        "n_route_replan_alignment_edges": route_replan_handoff_payload.get(
            "n_route_alignment_edges",
            0,
        ),
        "n_route_replan_revised_informal_knowledge_dag_nodes": route_replan_handoff_payload.get(
            "n_revised_informal_knowledge_dag_nodes",
            0,
        ),
        "n_route_replan_revised_formal_realization_dag_nodes": route_replan_handoff_payload.get(
            "n_revised_formal_realization_dag_nodes",
            0,
        ),
        "n_route_replan_revised_lean_realization_dag_nodes": route_replan_handoff_payload.get(
            "n_revised_lean_realization_dag_nodes",
            0,
        ),
        "n_route_replan_unaligned_primitives": route_replan_handoff_payload.get(
            "n_unaligned_primitives",
            0,
        ),
        "n_route_replan_resource_response_ledger_feedback": (
            route_replan_handoff_payload.get(
                "n_routes_with_resource_response_ledger_feedback",
                0,
            )
        ),
        "n_route_replan_distinct_prover_diagnostic_signatures": (
            route_replan_handoff_payload.get(
                "n_distinct_prover_diagnostic_signatures",
                0,
            )
        ),
        "n_route_replan_handoff_audit_failed": route_replan_handoff_audit_payload.get(
            "n_failed",
            0,
        ),
        "n_route_replan_handoff_audit_checks": route_replan_handoff_audit_payload.get(
            "n_checks",
            0,
        ),
        "n_route_replan_handoff_audit_row_schema_valid": route_replan_handoff_audit_payload.get(
            "n_row_schema_valid",
            0,
        ),
        "n_route_replan_handoff_audit_row_schema_invalid": route_replan_handoff_audit_payload.get(
            "n_row_schema_invalid",
            0,
        ),
        "route_replan_roundtrip_all_ok": route_replan_handoff_audit_payload.get(
            "roundtrip_all_ok",
            False,
        ),
        "n_route_replan_roundtrip_goal_plans": route_replan_handoff_audit_payload.get(
            "n_roundtrip_goal_plans",
            0,
        ),
        "n_route_replan_roundtrip_alignment_edges": route_replan_handoff_audit_payload.get(
            "n_roundtrip_route_alignment_edges",
            0,
        ),
        "n_route_replan_roundtrip_standalone_input_traces": route_replan_handoff_audit_payload.get(
            "n_roundtrip_standalone_input_traces",
            0,
        ),
        "n_route_replan_roundtrip_standalone_input_traces_with_replan_metadata": route_replan_handoff_audit_payload.get(
            "n_roundtrip_standalone_input_traces_with_replan_metadata",
            0,
        ),
        "n_route_replan_roundtrip_standalone_input_trace_llm_route_planner_hook_traces": route_replan_handoff_audit_payload.get(
            "n_roundtrip_standalone_input_trace_llm_route_planner_hook_traces",
            0,
        ),
        "n_route_replan_roundtrip_standalone_input_traces_with_llm_route_planner_hook_traces": route_replan_handoff_audit_payload.get(
            "n_roundtrip_standalone_input_traces_with_llm_route_planner_hook_traces",
            0,
        ),
        "n_proof_state_triage_items": proof_state_triage_payload.get(
            "n_triage_items",
            0,
        ),
        "n_proof_state_triage_target_prover_failed_items": (
            proof_state_triage_payload.get("n_target_prover_failed_items", 0)
        ),
        "n_proof_state_triage_target_prover_unavailable_items": (
            proof_state_triage_payload.get("n_target_prover_unavailable_items", 0)
        ),
        "n_proof_state_triage_non_target_prover_skeleton_items": (
            proof_state_triage_payload.get("n_non_target_prover_skeleton_items", 0)
        ),
        "n_proof_state_triage_local_lean_failed_items": (
            proof_state_triage_payload.get("n_local_lean_failed_items", 0)
        ),
        "n_proof_state_triage_non_lean_skeleton_items": (
            proof_state_triage_payload.get("n_non_lean_skeleton_items", 0)
        ),
        "n_proof_state_triage_row_schema_valid": proof_state_triage_payload.get(
            "n_row_schema_valid",
            0,
        ),
        "n_proof_state_triage_row_schema_invalid": proof_state_triage_payload.get(
            "n_row_schema_invalid",
            0,
        ),
        "n_interactive_session_rows": interactive_session_payload.get(
            "n_session_rows",
            0,
        ),
        "n_interactive_session_row_schema_valid": interactive_session_payload.get(
            "n_row_schema_valid",
            0,
        ),
        "n_interactive_session_row_schema_invalid": interactive_session_payload.get(
            "n_row_schema_invalid",
            0,
        ),
        "n_interactive_decision_policy_rows": interactive_session_payload.get(
            "n_decision_policy_rows",
            0,
        ),
        "n_interactive_decision_policy_row_schema_valid": interactive_session_payload.get(
            "n_decision_policy_row_schema_valid",
            0,
        ),
        "n_interactive_decision_policy_row_schema_invalid": interactive_session_payload.get(
            "n_decision_policy_row_schema_invalid",
            0,
        ),
        "n_interactive_decision_policy_rows_with_resource_contracts": interactive_session_payload.get(
            "n_decision_policy_rows_with_resource_contracts",
            0,
        ),
        "n_interactive_decision_policy_rows_with_frontier_resources": interactive_session_payload.get(
            "n_decision_policy_rows_with_frontier_resources",
            0,
        ),
        "n_interactive_decision_policy_rows_with_required_quality_signals": interactive_session_payload.get(
            "n_decision_policy_rows_with_required_quality_signals",
            0,
        ),
        "n_interactive_decision_policy_rows_with_quality_gates": interactive_session_payload.get(
            "n_decision_policy_rows_with_quality_gates",
            0,
        ),
        "n_interactive_decision_policy_rows_with_response_validation_signals": interactive_session_payload.get(
            "n_decision_policy_rows_with_response_validation_signals",
            0,
        ),
        "n_interactive_session_replan": interactive_session_payload.get(
            "n_run_route_replan",
            0,
        ),
        "n_interactive_session_run_formal_grounding": interactive_session_payload.get(
            "n_run_formal_grounding",
            0,
        ),
        "n_interactive_session_run_lean_grounding": interactive_session_payload.get(
            "n_run_lean_grounding",
            0,
        ),
        "n_interactive_session_waiting_for_adapter_responses": interactive_session_payload.get(
            "n_waiting_for_adapter_responses",
            0,
        ),
        "n_interactive_session_rows_requiring_replan": interactive_session_payload.get(
            "n_rows_requiring_replan",
            0,
        ),
        "n_interactive_session_replay": interactive_session_payload.get(
            "n_run_target_prover_replay",
            0,
        ),
        "n_cross_prover_targets_ok": cross_prover_matrix_payload.get(
            "n_targets_ok",
            0,
        ),
        "n_cross_prover_targets": cross_prover_matrix_payload.get("n_targets", 0),
        "n_cross_prover_matrix_row_schema_valid": cross_prover_matrix_payload.get(
            "n_matrix_row_schema_valid",
            0,
        ),
        "n_cross_prover_matrix_row_schema_invalid": cross_prover_matrix_payload.get(
            "n_matrix_row_schema_invalid",
            0,
        ),
        "n_cross_prover_total_packets": cross_prover_matrix_payload.get(
            "n_total_packets",
            0,
        ),
        "n_cross_prover_total_packet_schema_valid": cross_prover_matrix_payload.get(
            "n_total_packet_schema_valid",
            0,
        ),
        "n_cross_prover_packets_schema_invalid": cross_prover_matrix_payload.get(
            "n_total_packets_schema_invalid",
            0,
        ),
        "n_cross_prover_packet_row_schema_valid": cross_prover_matrix_payload.get(
            "n_packet_row_schema_valid",
            0,
        ),
        "n_cross_prover_packet_row_schema_invalid": cross_prover_matrix_payload.get(
            "n_packet_row_schema_invalid",
            0,
        ),
        "n_cross_prover_response_validation_row_schema_valid": cross_prover_matrix_payload.get(
            "n_response_validation_row_schema_valid",
            0,
        ),
        "n_cross_prover_response_validation_row_schema_invalid": cross_prover_matrix_payload.get(
            "n_response_validation_row_schema_invalid",
            0,
        ),
        "n_cross_prover_total_packets_with_alignment": cross_prover_matrix_payload.get(
            "n_total_packets_with_alignment",
            0,
        ),
        "n_cross_prover_packets_missing_alignment": cross_prover_matrix_payload.get(
            "n_total_packets_missing_alignment",
            0,
        ),
        "n_cross_prover_total_packets_with_standalone_input_trace": cross_prover_matrix_payload.get(
            "n_total_packets_with_standalone_input_trace",
            0,
        ),
        "n_cross_prover_packets_missing_standalone_input_trace": cross_prover_matrix_payload.get(
            "n_total_packets_missing_standalone_input_trace",
            0,
        ),
        "n_cross_prover_total_packets_with_replan_metadata_trace": cross_prover_matrix_payload.get(
            "n_total_packets_with_replan_metadata_trace",
            0,
        ),
        "n_cross_prover_target_summary_rows": (
            cross_prover_matrix_payload.get("target_summary", {}).get(
                "n_target_rows",
                0,
            )
            if isinstance(cross_prover_matrix_payload.get("target_summary"), dict)
            else 0
        ),
        "n_cross_prover_target_summary_contract_errors": (
            cross_prover_matrix_payload.get("n_target_summary_contract_errors", 0)
        ),
        "n_cross_prover_rejected": cross_prover_matrix_payload.get("n_rejected", 0),
        "cross_prover_packet_count_consistent": cross_prover_matrix_payload.get(
            "packet_count_consistent",
            False,
        ),
        "cross_prover_alignment_packet_count_consistent": cross_prover_matrix_payload.get(
            "alignment_packet_count_consistent",
            False,
        ),
        "cross_prover_standalone_input_trace_packet_count_consistent": cross_prover_matrix_payload.get(
            "standalone_input_trace_packet_count_consistent",
            False,
        ),
        "stages": stage_dicts,
        "artifacts": _artifact_paths(out_dir),
        "reuse_targets": tuple(
            publication_bundle_payload.get(
                "portable_reuse_targets",
                ("lean4", "rocq", "isabelle", "agda"),
            )
        ),
        "reproduction_commands": _reproduction_commands(
            target_intake_input,
            out_dir,
            target_prover_family,
            adapter_snapshot_ref,
            max_routes,
            llm_route_planner_provider=llm_route_planner_provider,
            llm_route_planner_model=llm_route_planner_model,
            llm_route_planner_model_tier=llm_route_planner_model_tier,
            llm_route_planner_max_tokens=llm_route_planner_max_tokens,
            llm_route_planner_max_repair_attempts=(
                llm_route_planner_max_repair_attempts
            ),
            llm_route_planner_temperature=llm_route_planner_temperature,
            llm_route_planner_invoke_provider=llm_route_planner_invoke_provider,
            llm_route_planner_response_json=llm_route_planner_response_json,
            llm_route_planner_static_response_json=llm_route_planner_static_response_json,
            feedback_llm_route_planner_provider=feedback_llm_route_planner_provider,
            feedback_llm_route_planner_model=feedback_llm_route_planner_model,
            feedback_llm_route_planner_model_tier=feedback_llm_route_planner_model_tier,
            feedback_llm_route_planner_max_tokens=feedback_llm_route_planner_max_tokens,
            feedback_llm_route_planner_max_repair_attempts=(
                feedback_llm_route_planner_max_repair_attempts
            ),
            feedback_llm_route_planner_temperature=(
                feedback_llm_route_planner_temperature
            ),
            feedback_llm_route_planner_invoke_provider=(
                feedback_llm_route_planner_invoke_provider
            ),
            feedback_llm_route_planner_response_json=(
                feedback_llm_route_planner_response_json
            ),
            feedback_llm_route_planner_static_response_json=(
                feedback_llm_route_planner_static_response_json
            ),
        ),
        "reuse_smoke_fingerprint": stable_hash(stage_dicts),
        "all_ok": (
            not stage_errors
            and bool(stages)
            and all(stage.ok for stage in stages)
            and all(stage.proof_boundary_ok for stage in stages)
        ),
        "errors": stage_errors,
        "proof_evidence_status": PROOF_EVIDENCE_STATUS,
        "proof_evidence_boundary": PROOF_EVIDENCE_BOUNDARY,
        "limitations": [
            "this smoke test checks public artifact interoperability, not theorem truth",
            "self-labeled smoke route truth exercises evaluation contracts but is not independent planner-quality evidence",
            "adapter mappings without response rows remain awaiting target-prover mapping",
            "kernel proof status still requires a separate replay/calibration gate in the target prover",
            "local literature/formal-source/proof-state adapters are fallback diagnostics when frontier services are unavailable",
        ],
    }
    manifest_path = out_dir / "formalization_gap_planner_reuse_smoke_manifest.json"
    jsonl_path = out_dir / "formalization_gap_planner_reuse_smoke.jsonl"
    report_path = out_dir / "formalization_gap_planner_reuse_smoke.md"
    payload["manifest_path"] = str(manifest_path)
    payload["jsonl_path"] = str(jsonl_path)
    payload["report_path"] = str(report_path)
    manifest_path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    jsonl_path.write_text(
        "\n".join(json.dumps(stage, sort_keys=True) for stage in stage_dicts)
        + ("\n" if stage_dicts else ""),
        encoding="utf-8",
    )
    report_path.write_text(_markdown_report(payload), encoding="utf-8")
    return payload


def _maybe_validate_llm_route_planner_response_payloads(
    planner_payloads: tuple[dict[str, Any], ...],
    out_dir: Path,
) -> dict[str, object] | None:
    responses: list[dict[str, object]] = []
    request_contexts: list[dict[str, object]] = []
    for planner_payload in planner_payloads:
        for request in planner_payload.get("request_packets", []):
            if isinstance(request, dict):
                request_contexts.append(dict(request))
        for row in planner_payload.get("rows", []):
            if not isinstance(row, dict):
                continue
            if not row.get("response_present"):
                continue
            response_payload = _llm_route_planner_response_payload_from_row(row)
            if not response_payload:
                continue
            responses.append(
                {
                    "request_id": str(row.get("request_id", "")),
                    "route_id": str(row.get("route_id", "")),
                    "response_payload": response_payload,
                    "proof_evidence_boundary": str(
                        row.get(
                            "proof_evidence_boundary",
                            "not theorem proof evidence",
                        )
                    ),
                }
            )
    if not responses:
        return None
    out_dir.mkdir(parents=True, exist_ok=True)
    input_path = (
        out_dir
        / "formalization_gap_planner_llm_route_planner_response_payload_validation_input.json"
    )
    input_path.write_text(
        json.dumps({"responses": responses}, indent=2, default=str),
        encoding="utf-8",
    )
    request_context_path: Path | None = None
    if request_contexts:
        request_context_path = (
            out_dir
            / "formalization_gap_planner_llm_route_planner_response_payload_validation_request_context.json"
        )
        request_context_path.write_text(
            json.dumps(
                {"request_packets": request_contexts},
                indent=2,
                default=str,
            ),
            encoding="utf-8",
        )
    return validate_formalization_gap_planner_llm_route_planner_response_payloads(
        input_path,
        out_dir,
        request_context_json=request_context_path,
    )


def _llm_route_planner_response_payload_from_row(row: dict[str, Any]) -> dict[str, Any]:
    response_payload = row.get("response_payload", {})
    if isinstance(response_payload, dict) and response_payload:
        return response_payload

    raw_response_text = str(row.get("raw_response_text", "")).strip()
    if raw_response_text:
        try:
            raw_response_payload = json.loads(raw_response_text)
        except json.JSONDecodeError:
            raw_response_payload = {}
        if isinstance(raw_response_payload, dict):
            nested_payload = raw_response_payload.get("response_payload", {})
            if isinstance(nested_payload, dict) and nested_payload:
                return nested_payload
            if raw_response_payload:
                return raw_response_payload

    payload_keys = (
        "informal_knowledge_dag_nodes",
        "formal_realization_dag_nodes",
        "lean_realization_dag_nodes",
        "route_alignment_edges",
        "minimal_delta_plan",
        "residual_interpretations",
        "search_requests",
        "uncertainty_flags",
        "semantic_alignment_risks",
        "planner_next_actions",
        "standalone_route",
        "source_snippets",
        "proof_evidence_boundary",
    )
    return {
        key: row[key]
        for key in payload_keys
        if key in row
    }


def _optional_int(payload: dict[str, object] | None, key: str) -> int:
    if payload is None:
        return 0
    return int(payload.get(key, 0) or 0)


def _optional_dict(payload: dict[str, object] | None, key: str) -> dict[str, object]:
    if payload is None:
        return {}
    value = payload.get(key, {})
    if not isinstance(value, dict):
        return {}
    return dict(value)


def _evaluation_ground_truth_path(
    plan_payload: dict[str, Any],
    out_dir: Path,
    *,
    supplied_ground_truth_path: Path | None,
) -> tuple[Path, str]:
    if supplied_ground_truth_path is not None:
        return supplied_ground_truth_path, "supplied_route_truth"
    route_truth_path = out_dir / "formalization_gap_planner_reuse_smoke_route_truth.json"
    rows = [
        _smoke_route_truth_row(row)
        for row in plan_payload.get("rows", [])
        if isinstance(row, dict)
    ]
    route_truth_payload = {
        "schema_version": FORMALIZATION_GAP_PLANNER_REUSE_SMOKE_SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "component_name": "formalization_gap_planner_reuse_smoke_route_truth",
        "route_truth_mode": "self_labeled_contract_smoke",
        "description": (
            "Generated from the selected portable plan so reuse-smoke can "
            "exercise evaluation and ablation contracts without requiring a "
            "curated benchmark file. Use --ground-truth for independent "
            "publication metrics."
        ),
        "proof_evidence_status": PROOF_EVIDENCE_STATUS,
        "proof_evidence_boundary": PROOF_EVIDENCE_BOUNDARY,
        "routes": rows,
    }
    route_truth_path.write_text(
        json.dumps(route_truth_payload, indent=2, default=str),
        encoding="utf-8",
    )
    return route_truth_path, "self_labeled_contract_smoke"


def _smoke_route_truth_row(row: dict[str, Any]) -> dict[str, object]:
    selected_primitives = _unique_strs(
        row.get("selected_primitives", [])
        or [
            *_node_primitives(row.get("existing_reuse_nodes", [])),
            *_node_primitives(row.get("minimal_additional_formalization_nodes", [])),
        ]
    )
    existing_primitives = _node_primitives(row.get("existing_reuse_nodes", []))
    delta_primitives = _node_primitives(
        row.get("minimal_additional_formalization_nodes", [])
    )
    coverage_by_primitive = _coverage_by_primitive(row)
    return {
        "goal_plan_id": str(row.get("goal_plan_id", "")),
        "route_id": str(row.get("route_id", "")),
        "display_name": str(row.get("display_name", "")),
        "route_truth_status": "reuse_smoke_self_labeled_contract_truth",
        "required_primitives": selected_primitives,
        "actual_existing_reuse_primitives": existing_primitives,
        "actual_delta_primitives": delta_primitives,
        "coverage_by_primitive": coverage_by_primitive,
        "kernel_verified": False,
        "notes": (
            "Self-labeled from the planner output for reuse-smoke contract "
            "validation; not independent route-truth evidence."
        ),
    }


def _coverage_by_primitive(row: dict[str, Any]) -> dict[str, str]:
    coverage: dict[str, str] = {}
    groups = (
        ("existing_reuse_nodes", "exact_exists"),
        ("wrapper_nodes", "wrapper_needed"),
        ("bridge_nodes", "bridge_needed"),
        ("source_discovery_nodes", "definition_missing"),
        ("first_principles_nodes", "theory_missing"),
    )
    for field_name, default_status in groups:
        for node in row.get(field_name, []):
            if not isinstance(node, dict):
                continue
            primitive = str(node.get("primitive", "") or node.get("label", ""))
            if not primitive:
                continue
            coverage[primitive] = str(
                node.get("coverage_status", "")
                or node.get("action_class", "")
                or default_status
            )
    for node in row.get("minimal_additional_formalization_nodes", []):
        if not isinstance(node, dict):
            continue
        primitive = str(node.get("primitive", "") or node.get("label", ""))
        if primitive and primitive not in coverage:
            coverage[primitive] = str(
                node.get("coverage_status", "")
                or node.get("action_class", "")
                or "bridge_needed"
            )
    return coverage


def _node_primitives(nodes: Any) -> tuple[str, ...]:
    if not isinstance(nodes, (list, tuple)):
        return tuple()
    return _unique_strs(
        str(node.get("primitive", "") or node.get("label", ""))
        for node in nodes
        if isinstance(node, dict)
    )


def _unique_strs(values: Any) -> tuple[str, ...]:
    if isinstance(values, str):
        return (values,) if values else tuple()
    if not isinstance(values, (list, tuple, set)):
        values = tuple(values) if values is not None else tuple()
    return tuple(dict.fromkeys(str(value) for value in values if str(value)))


def _stage_row(
    stage_name: str,
    artifact_dir: Path,
    manifest_path: Path,
    payload: dict[str, Any],
) -> FormalizationGapPlannerReuseSmokeStage:
    component_name = str(payload.get("component_name", ""))
    errors = tuple(str(error) for error in payload.get("errors", []) if str(error))
    return FormalizationGapPlannerReuseSmokeStage(
        schema_version=FORMALIZATION_GAP_PLANNER_REUSE_SMOKE_SCHEMA_VERSION,
        stage_id="formalization_gap_planner_reuse_smoke_stage:"
        + stable_hash([stage_name, str(manifest_path), _summary(stage_name, payload)])[:20],
        stage_name=stage_name,
        component_name=component_name,
        artifact_dir=str(artifact_dir),
        manifest_path=str(manifest_path),
        ok=bool(payload.get("all_ok", False)) and manifest_path.exists(),
        proof_boundary_ok=_proof_boundary_ok(payload),
        proof_evidence_status=str(payload.get("proof_evidence_status", "")),
        proof_evidence_boundary=str(payload.get("proof_evidence_boundary", "")),
        summary=_summary(stage_name, payload),
        errors=errors,
    )


def _summary(stage_name: str, payload: dict[str, Any]) -> dict[str, object]:
    return {
        key: payload.get(key)
        for key in SUMMARY_KEYS_BY_STAGE.get(stage_name, ())
        if key in payload
    }


def _llm_provider_execution_mode(provider_name: str, *, invoke_provider: bool) -> str:
    provider = str(provider_name or "").strip().lower()
    if provider in {"anthropic", "openai"}:
        if invoke_provider:
            return "live_provider_invoked"
        return "staged_live_provider_prompt_no_api_call"
    if provider == "static":
        return "static_replay_no_live_provider"
    if provider == "prompt_only":
        return "prompt_only_no_provider"
    return "unknown_provider_mode"


def _llm_live_provider_call_count(
    payload: dict[str, Any],
    *,
    provider_name: str,
    invoke_provider: bool,
) -> int:
    if str(provider_name or "").strip().lower() not in {"anthropic", "openai"}:
        return 0
    if not invoke_provider:
        return 0
    return int(payload.get("n_request_packets", 0) or 0)


def _proof_boundary_ok(payload: dict[str, Any]) -> bool:
    status = str(payload.get("proof_evidence_status", "")).lower()
    boundary = str(payload.get("proof_evidence_boundary", "")).lower()
    return "not_proof_evidence" in status or "not proof evidence" in boundary


def _artifact_paths(out_dir: Path) -> dict[str, str]:
    return {
        "reuse_smoke_manifest": str(
            out_dir / "formalization_gap_planner_reuse_smoke_manifest.json"
        ),
        "reuse_smoke_jsonl": str(
            out_dir / "formalization_gap_planner_reuse_smoke.jsonl"
        ),
        "reuse_smoke_report": str(
            out_dir / "formalization_gap_planner_reuse_smoke.md"
        ),
        "target_intake_manifest": str(
            out_dir
            / "formalization_gap_planner_target_intake"
            / "formalization_gap_planner_target_intake_manifest.json"
        ),
        "standalone_seed": str(
            out_dir
            / "formalization_gap_planner_target_intake"
            / "formalization_gap_planner_target_intake_standalone_seed.json"
        ),
        "llm_route_planner_manifest": str(
            out_dir
            / "formalization_gap_planner_llm_route_planner"
            / "formalization_gap_planner_llm_route_planner_manifest.json"
        ),
        "llm_route_planner_requests_jsonl": str(
            out_dir
            / "formalization_gap_planner_llm_route_planner"
            / "formalization_gap_planner_llm_route_planner_requests.jsonl"
        ),
        "llm_route_planner_jsonl": str(
            out_dir
            / "formalization_gap_planner_llm_route_planner"
            / "formalization_gap_planner_llm_route_planner.jsonl"
        ),
        "llm_route_planner_request_schema": str(
            out_dir
            / "formalization_gap_planner_llm_route_planner"
            / "formalization_gap_planner_llm_route_planner_request.schema.json"
        ),
        "llm_route_planner_response_schema": str(
            out_dir
            / "formalization_gap_planner_llm_route_planner"
            / "formalization_gap_planner_llm_route_planner_response.schema.json"
        ),
        "llm_route_planner_row_schema": str(
            out_dir
            / "formalization_gap_planner_llm_route_planner"
            / "formalization_gap_planner_llm_route_planner_row.schema.json"
        ),
        "llm_route_planner_standalone_seed": str(
            out_dir
            / "formalization_gap_planner_llm_route_planner"
            / "formalization_gap_planner_llm_route_planner_standalone_seed.json"
        ),
        "llm_route_planner_report": str(
            out_dir
            / "formalization_gap_planner_llm_route_planner"
            / "formalization_gap_planner_llm_route_planner.md"
        ),
        "feedback_llm_route_planner_manifest": str(
            out_dir
            / "formalization_gap_planner_feedback_llm_route_planner"
            / "formalization_gap_planner_llm_route_planner_manifest.json"
        ),
        "feedback_llm_route_planner_requests_jsonl": str(
            out_dir
            / "formalization_gap_planner_feedback_llm_route_planner"
            / "formalization_gap_planner_llm_route_planner_requests.jsonl"
        ),
        "feedback_llm_route_planner_jsonl": str(
            out_dir
            / "formalization_gap_planner_feedback_llm_route_planner"
            / "formalization_gap_planner_llm_route_planner.jsonl"
        ),
        "feedback_llm_route_planner_standalone_seed": str(
            out_dir
            / "formalization_gap_planner_feedback_llm_route_planner"
            / "formalization_gap_planner_llm_route_planner_standalone_seed.json"
        ),
        "llm_route_planner_response_payload_validation_manifest": str(
            out_dir
            / "formalization_gap_planner_llm_route_planner_response_payload_validation"
            / "formalization_gap_planner_llm_route_planner_response_payload_validation_manifest.json"
        ),
        "llm_route_planner_response_payload_validation_jsonl": str(
            out_dir
            / "formalization_gap_planner_llm_route_planner_response_payload_validation"
            / "formalization_gap_planner_llm_route_planner_response_payload_validation.jsonl"
        ),
        "llm_route_planner_response_payload_validation_row_schema": str(
            out_dir
            / "formalization_gap_planner_llm_route_planner_response_payload_validation"
            / "formalization_gap_planner_llm_route_planner_response_payload_validation_row.schema.json"
        ),
        "standalone_plan_manifest": str(
            out_dir
            / "goal_conditioned_minimal_formalization_plan"
            / "goal_conditioned_minimal_formalization_plan_manifest.json"
        ),
        "route_alignment_edge_schema": str(
            out_dir
            / "goal_conditioned_minimal_formalization_plan"
            / "formalization_gap_planner_route_alignment_edge.schema.json"
        ),
        "portable_plan_audit_manifest": str(
            out_dir
            / "formalization_gap_planner_portable_plan_audit"
            / "formalization_gap_planner_portable_plan_audit_manifest.json"
        ),
        "portable_plan_audit_row_schema": str(
            out_dir
            / "formalization_gap_planner_portable_plan_audit"
            / "formalization_gap_planner_portable_plan_audit_row.schema.json"
        ),
        "portable_plan_audit_route_alignment_edge_schema": str(
            out_dir
            / "formalization_gap_planner_portable_plan_audit"
            / "formalization_gap_planner_route_alignment_edge.schema.json"
        ),
        "library_coverage_map_manifest": str(
            out_dir
            / "formalization_gap_planner_library_coverage_map"
            / "formalization_gap_planner_library_coverage_map_manifest.json"
        ),
        "library_coverage_map_jsonl": str(
            out_dir
            / "formalization_gap_planner_library_coverage_map"
            / "formalization_gap_planner_library_coverage_map.jsonl"
        ),
        "library_coverage_map_row_schema": str(
            out_dir
            / "formalization_gap_planner_library_coverage_map"
            / "formalization_gap_planner_library_coverage_map_row.schema.json"
        ),
        "library_coverage_map_report": str(
            out_dir
            / "formalization_gap_planner_library_coverage_map"
            / "formalization_gap_planner_library_coverage_map.md"
        ),
        "primitive_action_queue_manifest": str(
            out_dir
            / "formalization_gap_planner_primitive_action_queue"
            / "formalization_gap_planner_primitive_action_queue_manifest.json"
        ),
        "primitive_action_queue_jsonl": str(
            out_dir
            / "formalization_gap_planner_primitive_action_queue"
            / "formalization_gap_planner_primitive_action_queue.jsonl"
        ),
        "primitive_action_queue_row_schema": str(
            out_dir
            / "formalization_gap_planner_primitive_action_queue"
            / "formalization_gap_planner_primitive_action_queue_row.schema.json"
        ),
        "primitive_action_queue_report": str(
            out_dir
            / "formalization_gap_planner_primitive_action_queue"
            / "formalization_gap_planner_primitive_action_queue.md"
        ),
        "action_resource_plan_manifest": str(
            out_dir
            / "formalization_gap_planner_action_resource_plan"
            / "formalization_gap_planner_action_resource_plan_manifest.json"
        ),
        "action_resource_plan_jsonl": str(
            out_dir
            / "formalization_gap_planner_action_resource_plan"
            / "formalization_gap_planner_action_resource_plan.jsonl"
        ),
        "action_resource_plan_row_schema": str(
            out_dir
            / "formalization_gap_planner_action_resource_plan"
            / "formalization_gap_planner_action_resource_plan_row.schema.json"
        ),
        "action_resource_plan_report": str(
            out_dir
            / "formalization_gap_planner_action_resource_plan"
            / "formalization_gap_planner_action_resource_plan.md"
        ),
        "resource_request_queue_manifest": str(
            out_dir
            / "formalization_gap_planner_resource_request_queue"
            / "formalization_gap_planner_resource_request_queue_manifest.json"
        ),
        "resource_request_queue_jsonl": str(
            out_dir
            / "formalization_gap_planner_resource_request_queue"
            / "formalization_gap_planner_resource_request_queue.jsonl"
        ),
        "resource_request_queue_row_schema": str(
            out_dir
            / "formalization_gap_planner_resource_request_queue"
            / "formalization_gap_planner_resource_request_queue_row.schema.json"
        ),
        "resource_request_queue_report": str(
            out_dir
            / "formalization_gap_planner_resource_request_queue"
            / "formalization_gap_planner_resource_request_queue.md"
        ),
        "resource_response_ledger_manifest": str(
            out_dir
            / "formalization_gap_planner_resource_response_ledger"
            / "formalization_gap_planner_resource_response_ledger_manifest.json"
        ),
        "resource_response_ledger_jsonl": str(
            out_dir
            / "formalization_gap_planner_resource_response_ledger"
            / "formalization_gap_planner_resource_response_ledger.jsonl"
        ),
        "resource_response_schema": str(
            out_dir
            / "formalization_gap_planner_resource_response_ledger"
            / "formalization_gap_planner_resource_response.schema.json"
        ),
        "resource_response_ledger_row_schema": str(
            out_dir
            / "formalization_gap_planner_resource_response_ledger"
            / "formalization_gap_planner_resource_response_ledger_row.schema.json"
        ),
        "resource_response_ledger_report": str(
            out_dir
            / "formalization_gap_planner_resource_response_ledger"
            / "formalization_gap_planner_resource_response_ledger.md"
        ),
        "minimal_delta_audit_manifest": str(
            out_dir
            / "formalization_gap_planner_minimal_delta_audit"
            / "formalization_gap_planner_minimal_delta_audit_manifest.json"
        ),
        "minimal_delta_decisions_jsonl": str(
            out_dir
            / "formalization_gap_planner_minimal_delta_audit"
            / "formalization_gap_planner_minimal_delta_decisions.jsonl"
        ),
        "minimal_delta_decision_row_schema": str(
            out_dir
            / "formalization_gap_planner_minimal_delta_audit"
            / "formalization_gap_planner_minimal_delta_decision_row.schema.json"
        ),
        "source_grounding_audit_manifest": str(
            out_dir
            / "formalization_gap_planner_source_grounding_audit"
            / "formalization_gap_planner_source_grounding_audit_manifest.json"
        ),
        "source_grounding_row_schema": str(
            out_dir
            / "formalization_gap_planner_source_grounding_audit"
            / "formalization_gap_planner_source_grounding_row.schema.json"
        ),
        "reuse_smoke_route_truth": str(
            out_dir / "formalization_gap_planner_reuse_smoke_route_truth.json"
        ),
        "evaluation_manifest": str(
            out_dir
            / "formalization_gap_planner_evaluation"
            / "formalization_gap_planner_evaluation_manifest.json"
        ),
        "evaluation_jsonl": str(
            out_dir
            / "formalization_gap_planner_evaluation"
            / "formalization_gap_planner_evaluation.jsonl"
        ),
        "evaluation_row_schema": str(
            out_dir
            / "formalization_gap_planner_evaluation"
            / "formalization_gap_planner_evaluation_row.schema.json"
        ),
        "evaluation_ground_truth": str(
            out_dir
            / "formalization_gap_planner_evaluation"
            / "formalization_gap_planner_evaluation_ground_truth.json"
        ),
        "evaluation_report": str(
            out_dir
            / "formalization_gap_planner_evaluation"
            / "formalization_gap_planner_evaluation.md"
        ),
        "refinement_queue_manifest": str(
            out_dir
            / "formalization_gap_planner_refinement_queue"
            / "formalization_gap_planner_refinement_queue_manifest.json"
        ),
        "refinement_work_item_schema": str(
            out_dir
            / "formalization_gap_planner_refinement_queue"
            / "formalization_gap_planner_refinement_work_item.schema.json"
        ),
        "refinement_adapter_manifest": str(
            out_dir
            / "formalization_gap_planner_refinement_adapter"
            / "formalization_gap_planner_refinement_adapter_manifest.json"
        ),
        "refinement_responses_jsonl": str(
            out_dir
            / "formalization_gap_planner_refinement_adapter"
            / "formalization_gap_planner_refinement_evidence_responses.jsonl"
        ),
        "refinement_adapter_response_schema": str(
            out_dir
            / "formalization_gap_planner_refinement_adapter"
            / "formalization_gap_planner_refinement_tool_response.schema.json"
        ),
        "minimal_delta_audit_feedback_adapter_manifest": str(
            out_dir
            / "formalization_gap_planner_minimal_delta_audit_feedback_adapter"
            / "formalization_gap_planner_minimal_delta_audit_feedback_adapter_manifest.json"
        ),
        "minimal_delta_audit_feedback_responses_jsonl": str(
            out_dir
            / "formalization_gap_planner_minimal_delta_audit_feedback_adapter"
            / "formalization_gap_planner_minimal_delta_audit_feedback_responses.jsonl"
        ),
        "minimal_delta_audit_feedback_merged_responses_jsonl": str(
            out_dir
            / "formalization_gap_planner_minimal_delta_audit_feedback_adapter"
            / "formalization_gap_planner_refinement_evidence_responses.jsonl"
        ),
        "minimal_delta_audit_feedback_response_schema": str(
            out_dir
            / "formalization_gap_planner_minimal_delta_audit_feedback_adapter"
            / "formalization_gap_planner_refinement_tool_response.schema.json"
        ),
        "local_literature_adapter_manifest": str(
            out_dir
            / "formalization_gap_planner_local_literature_adapter"
            / "formalization_gap_planner_local_literature_adapter_manifest.json"
        ),
        "local_literature_responses_jsonl": str(
            out_dir
            / "formalization_gap_planner_local_literature_adapter"
            / "formalization_gap_planner_local_literature_adapter_responses.jsonl"
        ),
        "local_literature_response_schema": str(
            out_dir
            / "formalization_gap_planner_local_literature_adapter"
            / "formalization_gap_planner_refinement_tool_response.schema.json"
        ),
        "local_formal_source_adapter_manifest": str(
            out_dir
            / "formalization_gap_planner_local_formal_source_adapter"
            / "formalization_gap_planner_local_formal_source_adapter_manifest.json"
        ),
        "local_formal_source_responses_jsonl": str(
            out_dir
            / "formalization_gap_planner_local_formal_source_adapter"
            / "formalization_gap_planner_local_formal_source_adapter_responses.jsonl"
        ),
        "local_formal_source_response_schema": str(
            out_dir
            / "formalization_gap_planner_local_formal_source_adapter"
            / "formalization_gap_planner_refinement_tool_response.schema.json"
        ),
        "local_proof_state_adapter_manifest": str(
            out_dir
            / "formalization_gap_planner_local_proof_state_adapter"
            / "formalization_gap_planner_local_proof_state_adapter_manifest.json"
        ),
        "local_proof_state_responses_jsonl": str(
            out_dir
            / "formalization_gap_planner_local_proof_state_adapter"
            / "formalization_gap_planner_local_proof_state_adapter_responses.jsonl"
        ),
        "local_proof_state_response_schema": str(
            out_dir
            / "formalization_gap_planner_local_proof_state_adapter"
            / "formalization_gap_planner_refinement_tool_response.schema.json"
        ),
        "prover_adapter_feedback_adapter_manifest": str(
            out_dir
            / "formalization_gap_planner_prover_adapter_feedback_adapter"
            / "formalization_gap_planner_prover_adapter_feedback_adapter_manifest.json"
        ),
        "prover_adapter_feedback_responses_jsonl": str(
            out_dir
            / "formalization_gap_planner_prover_adapter_feedback_adapter"
            / "formalization_gap_planner_prover_adapter_feedback_responses.jsonl"
        ),
        "prover_adapter_feedback_merged_responses_jsonl": str(
            out_dir
            / "formalization_gap_planner_prover_adapter_feedback_adapter"
            / "formalization_gap_planner_refinement_evidence_responses.jsonl"
        ),
        "prover_adapter_feedback_response_schema": str(
            out_dir
            / "formalization_gap_planner_prover_adapter_feedback_adapter"
            / "formalization_gap_planner_refinement_tool_response.schema.json"
        ),
        "refinement_evidence_manifest": str(
            out_dir
            / "formalization_gap_planner_refinement_evidence"
            / "formalization_gap_planner_refinement_evidence_manifest.json"
        ),
        "refinement_tool_response_schema": str(
            out_dir
            / "formalization_gap_planner_refinement_evidence"
            / "formalization_gap_planner_refinement_tool_response.schema.json"
        ),
        "refinement_evidence_row_schema": str(
            out_dir
            / "formalization_gap_planner_refinement_evidence"
            / "formalization_gap_planner_refinement_evidence_row.schema.json"
        ),
        "route_revision_overlay_manifest": str(
            out_dir
            / "formalization_gap_planner_route_revision_overlay"
            / "formalization_gap_planner_route_revision_overlay_manifest.json"
        ),
        "route_revision_overlay_row_schema": str(
            out_dir
            / "formalization_gap_planner_route_revision_overlay"
            / "formalization_gap_planner_route_revision_overlay_row.schema.json"
        ),
        "route_stability_audit_manifest": str(
            out_dir
            / "formalization_gap_planner_route_stability_audit"
            / "formalization_gap_planner_route_stability_audit_manifest.json"
        ),
        "route_stability_audit_row_schema": str(
            out_dir
            / "formalization_gap_planner_route_stability_audit"
            / "formalization_gap_planner_route_stability_audit_row.schema.json"
        ),
        "route_replan_handoff_manifest": str(
            out_dir
            / "formalization_gap_planner_route_replan_handoff"
            / "formalization_gap_planner_route_replan_handoff_manifest.json"
        ),
        "route_replan_handoff_row_schema": str(
            out_dir
            / "formalization_gap_planner_route_replan_handoff"
            / "formalization_gap_planner_route_replan_handoff_row.schema.json"
        ),
        "route_replan_standalone_seed": str(
            out_dir
            / "formalization_gap_planner_route_replan_handoff"
            / "formalization_gap_planner_route_replan_standalone_seed.json"
        ),
        "route_replan_standalone_seed_schema": str(
            out_dir
            / "formalization_gap_planner_route_replan_handoff"
            / "formalization_gap_planner_route_replan_standalone_seed.schema.json"
        ),
        "route_replan_handoff_audit_manifest": str(
            out_dir
            / "formalization_gap_planner_route_replan_handoff_audit"
            / "formalization_gap_planner_route_replan_handoff_audit_manifest.json"
        ),
        "route_replan_handoff_audit_jsonl": str(
            out_dir
            / "formalization_gap_planner_route_replan_handoff_audit"
            / "formalization_gap_planner_route_replan_handoff_audit.jsonl"
        ),
        "route_replan_handoff_audit_row_schema": str(
            out_dir
            / "formalization_gap_planner_route_replan_handoff_audit"
            / "formalization_gap_planner_route_replan_handoff_audit_row.schema.json"
        ),
        "route_replan_handoff_audit_report": str(
            out_dir
            / "formalization_gap_planner_route_replan_handoff_audit"
            / "formalization_gap_planner_route_replan_handoff_audit.md"
        ),
        "route_replan_handoff_audit_roundtrip_plan": str(
            out_dir
            / "formalization_gap_planner_route_replan_handoff_audit"
            / "formalization_gap_planner_route_replan_roundtrip_plan"
            / "goal_conditioned_minimal_formalization_plan_manifest.json"
        ),
        "proof_state_triage_manifest": str(
            out_dir
            / "formalization_gap_planner_proof_state_triage"
            / "formalization_gap_planner_proof_state_triage_manifest.json"
        ),
        "proof_state_triage_row_schema": str(
            out_dir
            / "formalization_gap_planner_proof_state_triage"
            / "formalization_gap_planner_proof_state_triage_row.schema.json"
        ),
        "interactive_session_manifest": str(
            out_dir
            / "formalization_gap_planner_interactive_session"
            / "formalization_gap_planner_interactive_session_manifest.json"
        ),
        "interactive_session_jsonl": str(
            out_dir
            / "formalization_gap_planner_interactive_session"
            / "formalization_gap_planner_interactive_session.jsonl"
        ),
        "interactive_session_row_schema": str(
            out_dir
            / "formalization_gap_planner_interactive_session"
            / "formalization_gap_planner_interactive_session_row.schema.json"
        ),
        "interactive_decision_policy_jsonl": str(
            out_dir
            / "formalization_gap_planner_interactive_session"
            / "formalization_gap_planner_interactive_decision_policy.jsonl"
        ),
        "interactive_decision_policy_row_schema": str(
            out_dir
            / "formalization_gap_planner_interactive_session"
            / "formalization_gap_planner_interactive_decision_policy_row.schema.json"
        ),
        "interactive_session_report": str(
            out_dir
            / "formalization_gap_planner_interactive_session"
            / "formalization_gap_planner_interactive_session.md"
        ),
        "ablation_study_manifest": str(
            out_dir
            / "formalization_gap_planner_ablation_study"
            / "formalization_gap_planner_ablation_study_manifest.json"
        ),
        "ablation_study_jsonl": str(
            out_dir
            / "formalization_gap_planner_ablation_study"
            / "formalization_gap_planner_ablation_study.jsonl"
        ),
        "ablation_study_row_schema": str(
            out_dir
            / "formalization_gap_planner_ablation_study"
            / "formalization_gap_planner_ablation_study_row.schema.json"
        ),
        "ablation_study_report": str(
            out_dir
            / "formalization_gap_planner_ablation_study"
            / "formalization_gap_planner_ablation_study.md"
        ),
        "prover_adapter_contract_manifest": str(
            out_dir
            / "formalization_gap_planner_prover_adapter_contract"
            / "formalization_gap_planner_prover_adapter_contract_manifest.json"
        ),
        "prover_adapter_packet_schema": str(
            out_dir
            / "formalization_gap_planner_prover_adapter_contract"
            / "formalization_gap_planner_prover_adapter_packet.schema.json"
        ),
        "prover_adapter_response_schema": str(
            out_dir
            / "formalization_gap_planner_prover_adapter_contract"
            / "formalization_gap_planner_prover_adapter_response.schema.json"
        ),
        "prover_adapter_response_validation_row_schema": str(
            out_dir
            / "formalization_gap_planner_prover_adapter_contract"
            / "formalization_gap_planner_prover_adapter_response_validation_row.schema.json"
        ),
        "adapter_registry_manifest": str(
            out_dir
            / "formalization_gap_planner_adapter_registry"
            / "formalization_gap_planner_adapter_registry_manifest.json"
        ),
        "adapter_registry_jsonl": str(
            out_dir
            / "formalization_gap_planner_adapter_registry"
            / "formalization_gap_planner_adapter_registry.jsonl"
        ),
        "adapter_registry_row_schema": str(
            out_dir
            / "formalization_gap_planner_adapter_registry"
            / "formalization_gap_planner_adapter_registry_row.schema.json"
        ),
        "adapter_registry_audit_manifest": str(
            out_dir
            / "formalization_gap_planner_adapter_registry_audit"
            / "formalization_gap_planner_adapter_registry_audit_manifest.json"
        ),
        "adapter_registry_audit_jsonl": str(
            out_dir
            / "formalization_gap_planner_adapter_registry_audit"
            / "formalization_gap_planner_adapter_registry_audit.jsonl"
        ),
        "adapter_registry_audit_report": str(
            out_dir
            / "formalization_gap_planner_adapter_registry_audit"
            / "formalization_gap_planner_adapter_registry_audit.md"
        ),
        "component_resource_registry_manifest": str(
            out_dir
            / "formalization_gap_planner_component_resource_registry"
            / "formalization_gap_planner_component_resource_registry_manifest.json"
        ),
        "component_resource_registry_jsonl": str(
            out_dir
            / "formalization_gap_planner_component_resource_registry"
            / "formalization_gap_planner_component_resource_registry.jsonl"
        ),
        "component_resource_resources_jsonl": str(
            out_dir
            / "formalization_gap_planner_component_resource_registry"
            / "formalization_gap_planner_component_resource_resources.jsonl"
        ),
        "component_resource_execution_plans_jsonl": str(
            out_dir
            / "formalization_gap_planner_component_resource_registry"
            / "formalization_gap_planner_component_resource_execution_plans.jsonl"
        ),
        "component_resource_contracts_jsonl": str(
            out_dir
            / "formalization_gap_planner_component_resource_registry"
            / "formalization_gap_planner_component_resource_contracts.jsonl"
        ),
        "component_resource_resource_row_schema": str(
            out_dir
            / "formalization_gap_planner_component_resource_registry"
            / "formalization_gap_planner_component_resource_resource_row.schema.json"
        ),
        "component_resource_component_row_schema": str(
            out_dir
            / "formalization_gap_planner_component_resource_registry"
            / "formalization_gap_planner_component_resource_component_row.schema.json"
        ),
        "component_resource_execution_plan_schema": str(
            out_dir
            / "formalization_gap_planner_component_resource_registry"
            / "formalization_gap_planner_component_resource_execution_plan.schema.json"
        ),
        "component_resource_contract_row_schema": str(
            out_dir
            / "formalization_gap_planner_component_resource_registry"
            / "formalization_gap_planner_component_resource_contract_row.schema.json"
        ),
        "component_resource_registry_report": str(
            out_dir
            / "formalization_gap_planner_component_resource_registry"
            / "formalization_gap_planner_component_resource_registry.md"
        ),
        "component_resource_registry_audit_manifest": str(
            out_dir
            / "formalization_gap_planner_component_resource_registry_audit"
            / "formalization_gap_planner_component_resource_registry_audit_manifest.json"
        ),
        "component_resource_registry_audit_jsonl": str(
            out_dir
            / "formalization_gap_planner_component_resource_registry_audit"
            / "formalization_gap_planner_component_resource_registry_audit.jsonl"
        ),
        "component_resource_registry_audit_report": str(
            out_dir
            / "formalization_gap_planner_component_resource_registry_audit"
            / "formalization_gap_planner_component_resource_registry_audit.md"
        ),
        "cross_prover_matrix_audit_manifest": str(
            out_dir
            / "formalization_gap_planner_cross_prover_matrix_audit"
            / "formalization_gap_planner_cross_prover_matrix_audit_manifest.json"
        ),
        "cross_prover_packets_jsonl": str(
            out_dir
            / "formalization_gap_planner_cross_prover_matrix_audit"
            / "formalization_gap_planner_cross_prover_packets.jsonl"
        ),
        "cross_prover_matrix_row_schema": str(
            out_dir
            / "formalization_gap_planner_cross_prover_matrix_audit"
            / "formalization_gap_planner_cross_prover_matrix_audit_row.schema.json"
        ),
        "cross_prover_packet_schema": str(
            out_dir
            / "formalization_gap_planner_cross_prover_matrix_audit"
            / "formalization_gap_planner_prover_adapter_packet.schema.json"
        ),
        "cross_prover_response_validation_jsonl": str(
            out_dir
            / "formalization_gap_planner_cross_prover_matrix_audit"
            / "formalization_gap_planner_cross_prover_response_validation.jsonl"
        ),
        "cross_prover_response_validation_row_schema": str(
            out_dir
            / "formalization_gap_planner_cross_prover_matrix_audit"
            / "formalization_gap_planner_prover_adapter_response_validation_row.schema.json"
        ),
        "cross_prover_target_summary": str(
            out_dir
            / "formalization_gap_planner_cross_prover_matrix_audit"
            / "formalization_gap_planner_cross_prover_target_summary.json"
        ),
        "cross_prover_target_summary_schema": str(
            out_dir
            / "formalization_gap_planner_cross_prover_matrix_audit"
            / "formalization_gap_planner_cross_prover_target_summary.schema.json"
        ),
        "prover_adapter_packets_jsonl": str(
            out_dir
            / "formalization_gap_planner_prover_adapter_contract"
            / "formalization_gap_planner_prover_adapter_packets.jsonl"
        ),
        "publication_bundle_manifest": str(
            out_dir
            / "formalization_gap_planner_publication_bundle"
            / "formalization_gap_planner_publication_bundle_manifest.json"
        ),
        "publication_bundle_contract": str(
            out_dir
            / "formalization_gap_planner_publication_bundle"
            / "contract"
            / "formalization_gap_planner_portable_contract.json"
        ),
        "publication_bundle_schema_catalog": str(
            out_dir
            / "formalization_gap_planner_publication_bundle"
            / "contract"
            / "formalization_gap_planner_schema_catalog.json"
        ),
        "publication_bundle_schema_catalog_schema": str(
            out_dir
            / "formalization_gap_planner_publication_bundle"
            / "contract"
            / "formalization_gap_planner_schema_catalog.schema.json"
        ),
        "publication_bundle_audit_manifest": str(
            out_dir
            / "formalization_gap_planner_publication_bundle_audit"
            / "formalization_gap_planner_publication_bundle_audit_manifest.json"
        ),
    }


def _reproduction_commands(
    target_intake_input: Path,
    out_dir: Path,
    target_prover_family: str,
    target_library_snapshot_ref: str,
    max_routes: int,
    *,
    llm_route_planner_provider: str,
    llm_route_planner_model: str,
    llm_route_planner_model_tier: str,
    llm_route_planner_max_tokens: int,
    llm_route_planner_max_repair_attempts: int,
    llm_route_planner_temperature: float,
    llm_route_planner_invoke_provider: bool,
    llm_route_planner_response_json: Path | None,
    llm_route_planner_static_response_json: Path | None,
    feedback_llm_route_planner_provider: str,
    feedback_llm_route_planner_model: str,
    feedback_llm_route_planner_model_tier: str,
    feedback_llm_route_planner_max_tokens: int,
    feedback_llm_route_planner_max_repair_attempts: int,
    feedback_llm_route_planner_temperature: float,
    feedback_llm_route_planner_invoke_provider: bool,
    feedback_llm_route_planner_response_json: Path | None,
    feedback_llm_route_planner_static_response_json: Path | None,
) -> tuple[str, ...]:
    command_parts = [
        "python3 -m ai_statistician.cli formalization-gap-planner-reuse-smoke",
        "--input",
        shlex.quote(str(target_intake_input)),
        "--target-prover-family",
        shlex.quote(target_prover_family),
        "--target-library-snapshot-ref",
        shlex.quote(target_library_snapshot_ref),
        "--max-routes",
        str(max_routes),
        "--llm-route-planner-provider",
        shlex.quote(llm_route_planner_provider),
        "--llm-route-planner-max-tokens",
        str(llm_route_planner_max_tokens),
        "--llm-route-planner-model-tier",
        shlex.quote(llm_route_planner_model_tier),
        "--llm-route-planner-max-repair-attempts",
        str(llm_route_planner_max_repair_attempts),
        "--llm-route-planner-temperature",
        str(llm_route_planner_temperature),
        "--feedback-llm-route-planner-provider",
        shlex.quote(feedback_llm_route_planner_provider),
        "--feedback-llm-route-planner-max-tokens",
        str(feedback_llm_route_planner_max_tokens),
        "--feedback-llm-route-planner-model-tier",
        shlex.quote(feedback_llm_route_planner_model_tier),
        "--feedback-llm-route-planner-max-repair-attempts",
        str(feedback_llm_route_planner_max_repair_attempts),
        "--feedback-llm-route-planner-temperature",
        str(feedback_llm_route_planner_temperature),
    ]
    if llm_route_planner_model:
        command_parts.extend(
            ("--llm-route-planner-model", shlex.quote(llm_route_planner_model))
        )
    if llm_route_planner_invoke_provider:
        command_parts.append("--llm-route-planner-invoke-provider")
    if llm_route_planner_response_json is not None:
        command_parts.extend(
            (
                "--llm-route-planner-response-json",
                shlex.quote(str(llm_route_planner_response_json)),
            )
        )
    if llm_route_planner_static_response_json is not None:
        command_parts.extend(
            (
                "--llm-route-planner-static-response-file",
                shlex.quote(str(llm_route_planner_static_response_json)),
            )
        )
    if feedback_llm_route_planner_model:
        command_parts.extend(
            (
                "--feedback-llm-route-planner-model",
                shlex.quote(feedback_llm_route_planner_model),
            )
        )
    if feedback_llm_route_planner_invoke_provider:
        command_parts.append("--feedback-llm-route-planner-invoke-provider")
    if feedback_llm_route_planner_response_json is not None:
        command_parts.extend(
            (
                "--feedback-llm-route-planner-response-json",
                shlex.quote(str(feedback_llm_route_planner_response_json)),
            )
        )
    if feedback_llm_route_planner_static_response_json is not None:
        command_parts.extend(
            (
                "--feedback-llm-route-planner-static-response-file",
                shlex.quote(str(feedback_llm_route_planner_static_response_json)),
            )
        )
    command_parts.extend(("--out", shlex.quote(str(out_dir))))
    return (
        " ".join(command_parts),
    )


def _markdown_report(payload: dict[str, object]) -> str:
    lines = [
        "# Formalization Gap Planner Reuse Smoke",
        "",
        f"- Target prover: `{payload.get('target_prover_family')}`",
        (
            f"- Source prover targets: `{payload.get('source_target_prover_family')}` "
            f"families={payload.get('n_source_target_prover_families')} "
            f"by={payload.get('source_by_target_prover_family')}"
        ),
        f"- Stages: {payload.get('n_ok')}/{payload.get('n_stages')}",
        f"- Proof-boundary checks: {payload.get('n_proof_boundary_ok')}/{payload.get('n_stages')}",
        f"- Work packets: {payload.get('n_portable_work_packets')}",
        f"- Publication bundle schema catalog entries: {payload.get('n_publication_bundle_schema_catalog_entries')}",
        f"- Publication bundle schema catalog contract errors: {payload.get('n_publication_bundle_schema_catalog_contract_errors')}",
        (
            f"- Goal-plan LLM trace metadata/model-tier/generator-metadata: "
            f"{payload.get('n_goal_plan_standalone_input_traces_with_llm_route_planner_metadata')}/"
            f"{payload.get('n_goal_plan_standalone_input_traces_with_llm_model_tier')}/"
            f"{payload.get('n_goal_plan_standalone_input_traces_with_llm_generator_metadata')} "
            f"tiers={payload.get('goal_plan_standalone_input_trace_by_llm_model_tier')} "
            f"adoption={payload.get('goal_plan_standalone_input_trace_by_llm_route_adoption_status')}"
        ),
        (
            f"- Goal-plan LLM route-adoption ready/pending/blockers: "
            f"{payload.get('n_goal_plan_standalone_input_traces_ready_for_route_adoption')}/"
            f"{payload.get('n_goal_plan_standalone_input_traces_pending_refinement_before_route_adoption')}/"
            f"{payload.get('n_goal_plan_standalone_input_trace_route_adoption_blockers')}"
        ),
        (
            f"- Goal-plan LLM seed selection selected/with-rank/costs/adoptable/selected-not-adoptable: "
            f"{payload.get('n_goal_plan_standalone_input_traces_llm_seed_selected')}/"
            f"{payload.get('n_goal_plan_standalone_input_traces_with_llm_seed_selection')}/"
            f"{payload.get('n_goal_plan_standalone_input_traces_with_llm_seed_minimal_delta_route_cost')}/"
            f"{payload.get('n_goal_plan_standalone_input_traces_llm_seed_adoptable_for_standalone_replay')}/"
            f"{payload.get('n_goal_plan_standalone_input_traces_llm_seed_selected_not_adoptable')} "
            f"ranks={payload.get('goal_plan_standalone_input_trace_by_llm_seed_selection_rank')}"
        ),
        (
            f"- LLM route planner requests valid: "
            f"{payload.get('n_llm_route_planner_request_schema_valid')}/"
            f"{payload.get('n_llm_route_planner_request_packets')} "
            f"mode={payload.get('llm_route_planner_provider_execution_mode')} "
            f"live_calls={payload.get('n_llm_route_planner_live_provider_calls_requested')} "
            f"awaiting={payload.get('n_llm_route_planner_awaiting')} "
            f"provider_failures={payload.get('n_llm_route_planner_provider_failures')} "
            f"model_tier_mismatches={payload.get('n_llm_route_planner_request_model_tier_mismatches')} "
            f"preflight_blocks={payload.get('n_llm_route_planner_generation_preflight_blocked')} "
            f"generator_metadata_rows={payload.get('n_llm_route_planner_rows_with_generator_metadata')}"
        ),
        (
            f"- LLM route planner adoption ready/pending/search-blockers/action-blockers: "
            f"{payload.get('n_llm_route_planner_route_adoption_ready')}/"
            f"{payload.get('n_llm_route_planner_route_adoption_pending_refinement')}/"
            f"{payload.get('n_llm_route_planner_route_adoption_pending_search_request_blockers')}/"
            f"{payload.get('n_llm_route_planner_route_adoption_pending_planner_next_action_blockers')} "
            f"feedback_actions={payload.get('n_llm_route_planner_route_adoption_pending_feedback_action_blockers')} "
            f"playbook_redispatch={payload.get('n_llm_route_planner_route_adoption_pending_resource_playbook_redispatch_blockers')} "
            f"resource_queue={payload.get('n_llm_route_planner_route_adoption_pending_resource_request_queue_blockers')} "
            f"replan={payload.get('n_llm_route_planner_route_adoption_pending_feedback_replan_blockers')} "
            f"realization={payload.get('n_llm_route_planner_route_adoption_pending_realization_coverage_blockers')} "
            f"omitted_cost_hint={payload.get('n_llm_route_planner_route_adoption_pending_omitted_cost_hint_primitive_blockers')}/"
            f"{payload.get('n_llm_route_planner_route_adoption_omitted_cost_hint_primitives')} "
            f"formal_gap={payload.get('n_llm_route_planner_route_adoption_pending_formal_gap_boundary_blockers')} "
            f"source_grounding={payload.get('n_llm_route_planner_route_adoption_pending_source_grounding_blockers')} "
            f"quality_controls={payload.get('n_llm_route_planner_route_adoption_pending_quality_control_blockers')}"
        ),
        (
            f"- LLM route planner resource registry context/resources/contracts: "
            f"{payload.get('n_llm_route_planner_requests_with_component_resource_registry_context')}/"
            f"{payload.get('n_llm_route_planner_component_resource_registry_resources_in_prompt')}/"
            f"{payload.get('n_llm_route_planner_component_resource_registry_contracts_in_prompt')}"
        ),
        (
            f"- LLM route planner feedback realization witnesses/incomplete/cost-hint-incomplete/missing-selected/missing-alignment/omitted-cost-hints: "
            f"{payload.get('n_llm_route_planner_feedback_loop_realization_witnesses')}/"
            f"{payload.get('n_llm_route_planner_feedback_loop_incomplete_realization_coverage')}/"
            f"{payload.get('n_llm_route_planner_feedback_loop_incomplete_cost_hint_baseline_coverage')}/"
            f"{payload.get('n_llm_route_planner_feedback_loop_missing_selected_formal_primitives')}/"
            f"{payload.get('n_llm_route_planner_feedback_loop_missing_delta_alignment_primitives')}/"
            f"{payload.get('n_llm_route_planner_feedback_loop_omitted_cost_hint_primitives')}"
        ),
        (
            f"- Bundle LLM route planner rows valid: "
            f"{payload.get('n_publication_bundle_optional_llm_route_planner_row_schema_valid')}/"
            f"{payload.get('n_publication_bundle_optional_llm_route_planner_row_schema_checked')}"
        ),
        (
            f"- Bundle LLM route planner manifest summaries valid: "
            f"{payload.get('n_publication_bundle_llm_route_planner_summary_valid')}/"
            f"{payload.get('n_publication_bundle_llm_route_planner_summary_checked')} "
            f"feedback={payload.get('n_publication_bundle_feedback_llm_route_planner_summary_valid')}/"
            f"{payload.get('n_publication_bundle_feedback_llm_route_planner_summary_checked')} "
            f"primary_ready_pending_blockers="
            f"{payload.get('n_publication_bundle_llm_route_planner_summary_route_adoption_ready')}/"
            f"{payload.get('n_publication_bundle_llm_route_planner_summary_route_adoption_pending_refinement')}/"
            f"{payload.get('n_publication_bundle_llm_route_planner_summary_route_adoption_blockers')} "
            f"feedback_ready_pending_blockers="
            f"{payload.get('n_publication_bundle_feedback_llm_route_planner_summary_route_adoption_ready')}/"
            f"{payload.get('n_publication_bundle_feedback_llm_route_planner_summary_route_adoption_pending_refinement')}/"
            f"{payload.get('n_publication_bundle_feedback_llm_route_planner_summary_route_adoption_blockers')}"
        ),
        (
            f"- Bundle LLM route planner realization-witness schemas valid: "
            f"{payload.get('n_publication_bundle_optional_llm_route_planner_realization_witness_schema_valid')}/"
            f"{payload.get('n_publication_bundle_optional_llm_route_planner_realization_witness_schema_checked')} "
            f"feedback={payload.get('n_publication_bundle_optional_feedback_llm_route_planner_realization_witness_schema_valid')}/"
            f"{payload.get('n_publication_bundle_optional_feedback_llm_route_planner_realization_witness_schema_checked')}"
        ),
        (
            f"- Bundle LLM route planner seed realization witnesses preserved: "
            f"{payload.get('n_publication_bundle_optional_llm_route_planner_seed_realization_witness_valid')}/"
            f"{payload.get('n_publication_bundle_optional_llm_route_planner_seed_realization_witness_checked')} "
            f"feedback={payload.get('n_publication_bundle_optional_feedback_llm_route_planner_seed_realization_witness_valid')}/"
            f"{payload.get('n_publication_bundle_optional_feedback_llm_route_planner_seed_realization_witness_checked')}"
        ),
        (
            f"- Bundle LLM route planner seed model provenance preserved: "
            f"{payload.get('n_publication_bundle_optional_llm_route_planner_seed_model_provenance_valid')}/"
            f"{payload.get('n_publication_bundle_optional_llm_route_planner_seed_model_provenance_checked')} "
            f"feedback={payload.get('n_publication_bundle_optional_feedback_llm_route_planner_seed_model_provenance_valid')}/"
            f"{payload.get('n_publication_bundle_optional_feedback_llm_route_planner_seed_model_provenance_checked')}"
        ),
        (
            f"- Bundle LLM route planner seed route-adoption readiness preserved: "
            f"{payload.get('n_publication_bundle_optional_llm_route_planner_seed_route_adoption_readiness_valid')}/"
            f"{payload.get('n_publication_bundle_optional_llm_route_planner_seed_route_adoption_readiness_checked')} "
            f"feedback={payload.get('n_publication_bundle_optional_feedback_llm_route_planner_seed_route_adoption_readiness_valid')}/"
            f"{payload.get('n_publication_bundle_optional_feedback_llm_route_planner_seed_route_adoption_readiness_checked')}"
        ),
        (
            f"- Bundle LLM route planner seed route-selection schema/contract/summary/traces valid: "
            f"{payload.get('n_publication_bundle_optional_llm_route_planner_seed_route_selection_schema_valid')}/"
            f"{payload.get('n_publication_bundle_optional_llm_route_planner_seed_route_selection_schema_checked')} "
            f"contract={payload.get('n_publication_bundle_optional_llm_route_planner_seed_route_selection_contract_valid')}/"
            f"{payload.get('n_publication_bundle_optional_llm_route_planner_seed_route_selection_contract_checked')} "
            f"{payload.get('n_publication_bundle_optional_llm_route_planner_seed_route_selection_summary_valid')}/"
            f"{payload.get('n_publication_bundle_optional_llm_route_planner_seed_route_selection_summary_checked')} "
            f"adoptable={payload.get('n_publication_bundle_optional_llm_route_planner_seed_route_selection_adoptable_candidates')}/"
            f"{payload.get('n_publication_bundle_optional_llm_route_planner_seed_route_selection_candidates')} "
            f"selected_adoptable={payload.get('n_publication_bundle_optional_llm_route_planner_seed_route_selection_selected_adoptable')} "
            f"selected_not_adoptable={payload.get('n_publication_bundle_optional_llm_route_planner_seed_route_selection_selected_not_adoptable')} "
            f"traces={payload.get('n_publication_bundle_optional_llm_route_planner_seed_route_selection_valid')}/"
            f"{payload.get('n_publication_bundle_optional_llm_route_planner_seed_route_selection_checked')} "
            f"feedback_schema={payload.get('n_publication_bundle_optional_feedback_llm_route_planner_seed_route_selection_schema_valid')}/"
            f"{payload.get('n_publication_bundle_optional_feedback_llm_route_planner_seed_route_selection_schema_checked')} "
            f"feedback_contract={payload.get('n_publication_bundle_optional_feedback_llm_route_planner_seed_route_selection_contract_valid')}/"
            f"{payload.get('n_publication_bundle_optional_feedback_llm_route_planner_seed_route_selection_contract_checked')} "
            f"feedback={payload.get('n_publication_bundle_optional_feedback_llm_route_planner_seed_route_selection_summary_valid')}/"
            f"{payload.get('n_publication_bundle_optional_feedback_llm_route_planner_seed_route_selection_summary_checked')} "
            f"feedback_adoptable={payload.get('n_publication_bundle_optional_feedback_llm_route_planner_seed_route_selection_adoptable_candidates')}/"
            f"{payload.get('n_publication_bundle_optional_feedback_llm_route_planner_seed_route_selection_candidates')} "
            f"feedback_selected_adoptable={payload.get('n_publication_bundle_optional_feedback_llm_route_planner_seed_route_selection_selected_adoptable')} "
            f"feedback_selected_not_adoptable={payload.get('n_publication_bundle_optional_feedback_llm_route_planner_seed_route_selection_selected_not_adoptable')} "
            f"feedback_traces={payload.get('n_publication_bundle_optional_feedback_llm_route_planner_seed_route_selection_valid')}/"
            f"{payload.get('n_publication_bundle_optional_feedback_llm_route_planner_seed_route_selection_checked')}"
        ),
        (
            f"- Bundle feedback LLM route planner requests/rows valid: "
            f"{payload.get('n_publication_bundle_optional_feedback_llm_route_planner_request_schema_valid')}/"
            f"{payload.get('n_publication_bundle_optional_feedback_llm_route_planner_request_schema_checked')} "
            f"rows={payload.get('n_publication_bundle_optional_feedback_llm_route_planner_row_schema_valid')}/"
            f"{payload.get('n_publication_bundle_optional_feedback_llm_route_planner_row_schema_checked')}"
        ),
        (
            f"- Bundle LLM route planner request generation policy valid: "
            f"{payload.get('n_publication_bundle_optional_llm_route_planner_request_generation_policy_valid')}/"
            f"{payload.get('n_publication_bundle_optional_llm_route_planner_request_generation_policy_checked')} "
            f"feedback={payload.get('n_publication_bundle_optional_feedback_llm_route_planner_request_generation_policy_valid')}/"
            f"{payload.get('n_publication_bundle_optional_feedback_llm_route_planner_request_generation_policy_checked')}"
        ),
        (
            f"- Bundle LLM route planner model-tier mismatch policy valid: "
            f"{payload.get('n_publication_bundle_optional_llm_route_planner_request_model_tier_mismatch_valid')}/"
            f"{payload.get('n_publication_bundle_optional_llm_route_planner_request_model_tier_mismatch_checked')} "
            f"feedback={payload.get('n_publication_bundle_optional_feedback_llm_route_planner_request_model_tier_mismatch_valid')}/"
            f"{payload.get('n_publication_bundle_optional_feedback_llm_route_planner_request_model_tier_mismatch_checked')}"
        ),
        (
            f"- Bundle LLM route planner generation preflight policy valid: "
            f"{payload.get('n_publication_bundle_optional_llm_route_planner_generation_preflight_valid')}/"
            f"{payload.get('n_publication_bundle_optional_llm_route_planner_generation_preflight_checked')} "
            f"feedback={payload.get('n_publication_bundle_optional_feedback_llm_route_planner_generation_preflight_valid')}/"
            f"{payload.get('n_publication_bundle_optional_feedback_llm_route_planner_generation_preflight_checked')}"
        ),
        (
            f"- LLM route payload validation payloads valid/invalid: "
            f"{payload.get('n_llm_route_planner_response_payload_validation_valid_payloads')}/"
            f"{payload.get('n_llm_route_planner_response_payload_validation_invalid_payloads')} "
            f"request_bound={payload.get('n_llm_route_planner_response_payload_validation_request_bound_payloads')}/"
            f"{payload.get('n_llm_route_planner_response_payload_validation_payloads')} "
            f"target_mismatch={payload.get('n_llm_route_planner_response_payload_validation_target_prover_mismatches')} "
            f"present={payload.get('has_llm_route_planner_response_payload_validation')}"
        ),
        (
            f"- Bundle LLM route payload validation manifest/count/rows valid: "
            f"{payload.get('n_publication_bundle_optional_llm_route_planner_response_payload_validation_manifest_contract_valid')}/"
            f"{payload.get('n_publication_bundle_optional_llm_route_planner_response_payload_validation_manifest_contract_checked')} "
            f"count={payload.get('n_publication_bundle_optional_llm_route_planner_response_payload_validation_count_valid')}/"
            f"{payload.get('n_publication_bundle_optional_llm_route_planner_response_payload_validation_count_checked')} "
            f"bound={payload.get('n_publication_bundle_optional_llm_route_planner_response_payload_validation_request_bound_coverage_valid')}/"
            f"{payload.get('n_publication_bundle_optional_llm_route_planner_response_payload_validation_request_bound_coverage_checked')} "
            f"rows={payload.get('n_publication_bundle_optional_llm_route_planner_response_payload_validation_row_schema_valid')}/"
            f"{payload.get('n_publication_bundle_optional_llm_route_planner_response_payload_validation_row_schema_checked')}"
        ),
        (
            f"- Feedback LLM route planner requests valid: "
            f"{payload.get('n_feedback_llm_route_planner_request_schema_valid')}/"
            f"{payload.get('n_feedback_llm_route_planner_request_packets')} "
            f"mode={payload.get('feedback_llm_route_planner_provider_execution_mode')} "
            f"live_calls={payload.get('n_feedback_llm_route_planner_live_provider_calls_requested')} "
            f"awaiting={payload.get('n_feedback_llm_route_planner_awaiting')} "
            f"provider_failures={payload.get('n_feedback_llm_route_planner_provider_failures')} "
            f"model_tier_mismatches={payload.get('n_feedback_llm_route_planner_request_model_tier_mismatches')} "
            f"preflight_blocks={payload.get('n_feedback_llm_route_planner_generation_preflight_blocked')} "
            f"generator_metadata_rows={payload.get('n_feedback_llm_route_planner_rows_with_generator_metadata')} "
            f"accepted={payload.get('n_feedback_llm_route_planner_accepted_route_plans')} "
            f"residual_goals={payload.get('n_feedback_llm_route_planner_request_residual_goals')}"
        ),
        (
            f"- Feedback LLM route planner adoption ready/pending/search-blockers/action-blockers: "
            f"{payload.get('n_feedback_llm_route_planner_route_adoption_ready')}/"
            f"{payload.get('n_feedback_llm_route_planner_route_adoption_pending_refinement')}/"
            f"{payload.get('n_feedback_llm_route_planner_route_adoption_pending_search_request_blockers')}/"
            f"{payload.get('n_feedback_llm_route_planner_route_adoption_pending_planner_next_action_blockers')} "
            f"feedback_actions={payload.get('n_feedback_llm_route_planner_route_adoption_pending_feedback_action_blockers')} "
            f"playbook_redispatch={payload.get('n_feedback_llm_route_planner_route_adoption_pending_resource_playbook_redispatch_blockers')} "
            f"resource_queue={payload.get('n_feedback_llm_route_planner_route_adoption_pending_resource_request_queue_blockers')} "
            f"replan={payload.get('n_feedback_llm_route_planner_route_adoption_pending_feedback_replan_blockers')} "
            f"realization={payload.get('n_feedback_llm_route_planner_route_adoption_pending_realization_coverage_blockers')} "
            f"omitted_cost_hint={payload.get('n_feedback_llm_route_planner_route_adoption_pending_omitted_cost_hint_primitive_blockers')}/"
            f"{payload.get('n_feedback_llm_route_planner_route_adoption_omitted_cost_hint_primitives')} "
            f"formal_gap={payload.get('n_feedback_llm_route_planner_route_adoption_pending_formal_gap_boundary_blockers')} "
            f"source_grounding={payload.get('n_feedback_llm_route_planner_route_adoption_pending_source_grounding_blockers')} "
            f"quality_controls={payload.get('n_feedback_llm_route_planner_route_adoption_pending_quality_control_blockers')}"
        ),
        (
            f"- Feedback LLM route planner context coverage/source/request_queue/response_ledger/refinement/overlay/session/policy: "
            f"{payload.get('n_feedback_llm_route_planner_requests_with_library_coverage_rows')}/"
            f"{payload.get('n_feedback_llm_route_planner_requests_with_source_grounding_rows')}/"
            f"{payload.get('n_feedback_llm_route_planner_requests_with_resource_request_queue_rows')}/"
            f"{payload.get('n_feedback_llm_route_planner_requests_with_resource_response_ledger_rows')}/"
            f"{payload.get('n_feedback_llm_route_planner_requests_with_refinement_evidence_rows')}/"
            f"{payload.get('n_feedback_llm_route_planner_requests_with_route_revision_overlay_rows')}/"
            f"{payload.get('n_feedback_llm_route_planner_requests_with_interactive_session_rows')}/"
            f"{payload.get('n_feedback_llm_route_planner_requests_with_interactive_decision_policy_rows')}"
        ),
        (
            f"- Feedback LLM route planner realization feedback witnesses/incomplete/cost-hint-incomplete/missing-selected/missing-alignment/omitted-cost-hints: "
            f"{payload.get('n_feedback_llm_route_planner_feedback_loop_realization_witnesses')}/"
            f"{payload.get('n_feedback_llm_route_planner_feedback_loop_incomplete_realization_coverage')}/"
            f"{payload.get('n_feedback_llm_route_planner_feedback_loop_incomplete_cost_hint_baseline_coverage')}/"
            f"{payload.get('n_feedback_llm_route_planner_feedback_loop_missing_selected_formal_primitives')}/"
            f"{payload.get('n_feedback_llm_route_planner_feedback_loop_missing_delta_alignment_primitives')}/"
            f"{payload.get('n_feedback_llm_route_planner_feedback_loop_omitted_cost_hint_primitives')}"
        ),
        (
            f"- Feedback LLM route planner resource registry context/resources/contracts: "
            f"{payload.get('n_feedback_llm_route_planner_requests_with_component_resource_registry_context')}/"
            f"{payload.get('n_feedback_llm_route_planner_component_resource_registry_resources_in_prompt')}/"
            f"{payload.get('n_feedback_llm_route_planner_component_resource_registry_contracts_in_prompt')}"
        ),
        (
            f"- Route-alignment edge schema valid: "
            f"{payload.get('n_route_alignment_edge_schema_valid')}/"
            f"{payload.get('n_route_alignment_edges')}"
        ),
        (
            f"- Portable-plan audit row schema valid: "
            f"{payload.get('n_portable_plan_audit_row_schema_valid')}/"
            f"{payload.get('n_publication_bundle_optional_portable_plan_audit_row_schema_checked')}"
        ),
        (
            f"- Library-coverage map rows valid: "
            f"{payload.get('n_library_coverage_row_schema_valid')}/"
            f"{payload.get('n_library_coverage_rows')}"
        ),
        (
            f"- Structured candidate declaration rows: "
            f"coverage={payload.get('n_library_coverage_candidate_declaration_rows')} "
            f"actions={payload.get('n_primitive_action_queue_candidate_declaration_rows')} "
            f"resources={payload.get('n_resource_request_candidate_declaration_rows')}"
        ),
        (
            f"- Library-coverage unknown or unaligned: "
            f"{payload.get('n_library_coverage_unknown_or_unaligned')}"
        ),
        (
            f"- Primitive action-queue rows valid: "
            f"{payload.get('n_primitive_action_queue_row_schema_valid')}/"
            f"{payload.get('n_primitive_action_queue_items')}"
        ),
        (
            f"- Action-resource plan rows valid: "
            f"{payload.get('n_action_resource_plan_row_schema_valid')}/"
            f"{payload.get('n_action_resource_plan_rows')}"
        ),
        (
            f"- Resource request-queue rows valid: "
            f"{payload.get('n_resource_request_row_schema_valid')}/"
            f"{payload.get('n_resource_request_rows')}"
        ),
        (
            f"- Resource request payloads self-contained: "
            f"{payload.get('n_resource_request_self_contained_payloads')}/"
            f"{payload.get('n_resource_request_rows')}"
        ),
        (
            f"- Resource request dispatch specs valid: "
            f"{payload.get('n_resource_request_dispatch_spec_identity_valid')}/"
            f"{payload.get('n_resource_request_rows')}"
        ),
        (
            f"- Bundle resource request contract alignment valid: "
            f"{payload.get('n_publication_bundle_optional_resource_request_contract_alignment_valid')}/"
            f"{payload.get('n_publication_bundle_optional_resource_request_contract_alignment_checked')}"
        ),
        (
            f"- Bundle resource request payload identity valid: "
            f"{payload.get('n_publication_bundle_optional_resource_request_payload_identity_valid')}/"
            f"{payload.get('n_publication_bundle_optional_resource_request_payload_identity_checked')}"
        ),
        (
            f"- Bundle resource request dispatch specs valid: "
            f"{payload.get('n_publication_bundle_optional_resource_request_dispatch_spec_valid')}/"
            f"{payload.get('n_publication_bundle_optional_resource_request_dispatch_spec_checked')}"
        ),
        (
            f"- Resource response-ledger rows valid: "
            f"{payload.get('n_resource_response_ledger_row_schema_valid')}/"
            f"{payload.get('n_resource_response_ledger_rows')} "
            f"awaiting={payload.get('n_resource_response_ledger_awaiting')} "
            f"playbook_present={payload.get('n_resource_response_ledger_request_playbook_present')} "
            f"playbook_grounded={payload.get('n_resource_response_ledger_playbook_grounded')} "
            f"playbook_failures={payload.get('n_resource_response_ledger_playbook_grounding_failures')} "
            f"request_mismatch={payload.get('n_resource_response_ledger_request_mismatches')}"
        ),
        (
            f"- Bundle resource response contract accounting valid: "
            f"{payload.get('n_publication_bundle_optional_resource_response_contract_field_accounting_valid')}/"
            f"{payload.get('n_publication_bundle_optional_resource_response_contract_field_accounting_checked')}"
        ),
        f"- Resource request queue: local={payload.get('n_resource_request_local_first')} frontier={payload.get('n_resource_request_frontier_escalation')}",
        f"- Awaiting adapter mappings: {payload.get('n_awaiting_adapter_mapping')}",
        f"- Prover-adapter response-validation row schema valid: {payload.get('n_prover_adapter_response_validation_row_schema_valid')}/{payload.get('n_portable_work_packets')}",
        (
            f"- Prover-adapter feedback generated/merged/schema-valid: "
            f"{payload.get('n_prover_adapter_feedback_generated_responses')}/"
            f"{payload.get('n_prover_adapter_feedback_merged_responses')}/"
            f"{payload.get('n_prover_adapter_feedback_merged_response_schema_valid')}"
        ),
        f"- Adapter registry: {payload.get('n_adapter_registry_ready')}/{payload.get('n_adapter_registry_adapters')}",
        (
            f"- Adapter registry row schema valid: "
            f"{payload.get('n_adapter_registry_row_schema_valid')}/"
            f"{payload.get('n_adapter_registry_adapters')}"
        ),
        f"- Adapter registry audit failures: {payload.get('n_adapter_registry_audit_failed')}",
        f"- Minimal-delta audit failures: {payload.get('n_minimal_delta_audit_failed')}",
        (
            f"- Minimal-delta decision schema valid: "
            f"{payload.get('n_minimal_delta_decision_row_schema_valid')}/"
            f"{payload.get('n_minimal_delta_decision_rows')}"
        ),
        (
            f"- Minimal-delta audit feedback generated/merged/schema-valid: "
            f"{payload.get('n_minimal_delta_audit_feedback_generated_responses')}/"
            f"{payload.get('n_minimal_delta_audit_feedback_merged_responses')}/"
            f"{payload.get('n_minimal_delta_audit_feedback_merged_response_schema_valid')}"
        ),
        f"- Source-grounding unaccounted: {payload.get('n_source_grounding_unaccounted')}",
        (
            f"- Source-grounding row schema valid: "
            f"{payload.get('n_source_grounding_row_schema_valid')}/"
            f"{payload.get('n_source_grounding_rows')}"
        ),
        f"- Evaluation ground-truth mode: {payload.get('evaluation_ground_truth_mode')}",
        (
            f"- Evaluation row schema valid: "
            f"{payload.get('n_evaluation_row_schema_valid')}/"
            f"{payload.get('n_evaluation_rows')}"
        ),
        f"- Evaluation matched ground truth: {payload.get('n_evaluation_matched_ground_truth')}/{payload.get('n_evaluation_rows')}",
        (
            f"- Bundle evaluation truth primitive checks valid: "
            f"{payload.get('n_publication_bundle_optional_evaluation_ground_truth_primitive_valid')}/"
            f"{payload.get('n_publication_bundle_optional_evaluation_ground_truth_primitive_checked')}"
        ),
        f"- Evaluation alignment ready: {payload.get('n_evaluation_alignment_contract_ok')}/{payload.get('n_evaluation_rows')}",
        (
            f"- Evaluation realization missing selected/delta primitives: "
            f"{payload.get('n_evaluation_realization_missing_selected_formal_primitives')}/"
            f"{payload.get('n_evaluation_realization_missing_delta_alignment_primitives')} "
            f"selected={payload.get('evaluation_realization_missing_selected_formal_primitives')} "
            f"delta={payload.get('evaluation_realization_missing_delta_alignment_primitives')}"
        ),
        (
            f"- Evaluation omitted cost-hint primitives: "
            f"{payload.get('n_evaluation_realization_omitted_cost_hint_primitives')} "
            f"baseline={payload.get('evaluation_realization_cost_hint_baseline_primitives')} "
            f"omitted={payload.get('evaluation_realization_omitted_cost_hint_primitives')} "
            f"incomplete_rows={payload.get('n_evaluation_rows_with_incomplete_cost_hint_baseline_coverage')}"
        ),
        (
            f"- Evaluation LLM trace/model-tier/generator-metadata: "
            f"{payload.get('n_evaluation_rows_with_llm_route_planner_trace')}/"
            f"{payload.get('n_evaluation_rows_with_llm_route_planner_model_tier')}/"
            f"{payload.get('n_evaluation_rows_with_llm_route_planner_generator_metadata')} "
            f"request_blocks={payload.get('n_evaluation_rows_with_llm_route_planner_request_contract_blocked')} "
            f"errors={payload.get('n_evaluation_llm_route_planner_errors')} "
            f"tiers={payload.get('evaluation_by_llm_model_tier')}"
        ),
        (
            f"- Evaluation LLM route-adoption ready/pending/blockers: "
            f"{payload.get('n_evaluation_rows_ready_for_route_adoption')}/"
            f"{payload.get('n_evaluation_rows_pending_refinement_before_route_adoption')}/"
            f"{payload.get('n_evaluation_llm_route_adoption_blockers')} "
            f"source_grounding={payload.get('n_evaluation_llm_route_adoption_pending_source_grounding_blockers')} "
            f"quality_controls={payload.get('n_evaluation_llm_route_adoption_pending_quality_control_blockers')} "
            f"statuses={payload.get('evaluation_by_llm_route_adoption_status')}"
        ),
        f"- Evaluation mean route recall: {payload.get('mean_evaluation_route_recall')}",
        f"- Evaluation mean alignment coverage: {payload.get('mean_evaluation_alignment_coverage')}",
        (
            f"- Component-resource component schema valid: "
            f"{payload.get('n_component_resource_component_row_schema_valid')}/"
            f"{payload.get('n_component_resource_components')}"
        ),
        (
            f"- Component-resource resource schema valid: "
            f"{payload.get('n_component_resource_resource_row_schema_valid')}/"
            f"{payload.get('n_component_resource_resources')}"
        ),
        (
            f"- Component-resource contract schema valid: "
            f"{payload.get('n_component_resource_contract_row_schema_valid')}/"
            f"{payload.get('n_component_resource_contracts')}"
        ),
        (
            f"- Component-resource execution-plan schema valid: "
            f"{payload.get('n_component_resource_execution_plan_schema_valid')}/"
            f"{payload.get('n_component_resource_execution_plans')}"
        ),
        (
            f"- Component-resource capability metadata: "
            f"{payload.get('n_component_resource_resources_with_capability_tags')}/"
            f"{payload.get('n_component_resource_resources')}"
        ),
        (
            f"- Component-resource validation signals: "
            f"{payload.get('n_component_resource_resources_with_validation_signals')}/"
            f"{payload.get('n_component_resource_resources')}"
        ),
        (
            f"- Component-resource quality gates: "
            f"{payload.get('n_component_resource_execution_plans_with_quality_gates')}/"
            f"{payload.get('n_component_resource_execution_plans')}"
        ),
        f"- Refinement items: {payload.get('n_refinement_ready')}/{payload.get('n_refinement_items')}",
        f"- Refinement responses: {payload.get('n_refinement_responses')}",
        f"- Refinement evidence row schema valid: {payload.get('n_refinement_evidence_row_schema_valid')}/{payload.get('n_refinement_evidence_rows')}",
        f"- Routes with revision: {payload.get('n_routes_with_revision')}",
        f"- Bundle route-revision resource-response evidence refs valid: {payload.get('n_publication_bundle_optional_route_revision_resource_response_evidence_ref_valid')}/{payload.get('n_publication_bundle_optional_route_revision_resource_response_evidence_ref_checked')}",
        f"- Bundle route-revision resource-response traces valid: {payload.get('n_publication_bundle_optional_route_revision_resource_response_trace_valid')}/{payload.get('n_publication_bundle_optional_route_revision_resource_response_trace_checked')}",
        f"- Bundle route-revision resource-response status summaries valid: {payload.get('n_publication_bundle_optional_route_revision_resource_response_status_valid')}/{payload.get('n_publication_bundle_optional_route_revision_resource_response_status_checked')}",
        f"- Route-stability needs expansion: {payload.get('n_route_stability_needs_expansion')}",
        f"- Route-stability row schema valid: {payload.get('n_route_stability_row_schema_valid')}/{payload.get('n_route_stability_rows')}",
        f"- Bundle route-stability resource-response status consistent: {payload.get('n_publication_bundle_optional_route_stability_resource_response_status_valid')}/{payload.get('n_publication_bundle_optional_route_stability_resource_response_status_checked')}",
        f"- Routes requiring replan: {payload.get('n_routes_requiring_replan')}",
        f"- Replan seed routes: {payload.get('n_replan_seed_routes')}",
        (
            f"- Replan seed DAG/alignment preservation: "
            f"{payload.get('n_publication_bundle_optional_route_replan_handoff_seed_dag_valid')}/"
            f"{payload.get('n_publication_bundle_optional_route_replan_handoff_seed_dag_checked')} DAG, "
            f"{payload.get('n_publication_bundle_optional_route_replan_handoff_seed_alignment_valid')}/"
            f"{payload.get('n_publication_bundle_optional_route_replan_handoff_seed_alignment_checked')} alignment"
        ),
        (
            f"- Replan roundtrip seed traces: "
            f"{payload.get('n_route_replan_roundtrip_standalone_input_traces')}/"
            f"{payload.get('n_replan_seed_routes')} routes, "
            f"{payload.get('n_route_replan_roundtrip_standalone_input_traces_with_replan_metadata')} with metadata"
        ),
        f"- Replan handoff audit failures: {payload.get('n_route_replan_handoff_audit_failed')}",
        f"- Replan handoff-audit row schema valid: {payload.get('n_route_replan_handoff_audit_row_schema_valid')}/{payload.get('n_route_replan_handoff_audit_checks')}",
        f"- Replan roundtrip plans: {payload.get('n_route_replan_roundtrip_goal_plans')}",
        f"- Proof-state triage items: {payload.get('n_proof_state_triage_items')}",
        f"- Proof-state triage row schema valid: {payload.get('n_proof_state_triage_row_schema_valid')}/{payload.get('n_proof_state_triage_items')}",
        f"- Interactive session rows: {payload.get('n_interactive_session_rows')}",
        f"- Bundle interactive-session schema valid: {payload.get('n_publication_bundle_optional_interactive_session_row_schema_valid')}/{payload.get('n_publication_bundle_optional_interactive_session_row_schema_checked')}",
        f"- Bundle interactive-session resource-response status consistent: {payload.get('n_publication_bundle_optional_interactive_session_resource_response_status_valid')}/{payload.get('n_publication_bundle_optional_interactive_session_resource_response_status_checked')}",
        f"- Interactive decision-policy schema valid: {payload.get('n_interactive_decision_policy_row_schema_valid')}/{payload.get('n_interactive_decision_policy_rows')}",
        f"- Interactive decision-policy resource contracts: {payload.get('n_interactive_decision_policy_rows_with_resource_contracts')}/{payload.get('n_interactive_decision_policy_rows')}",
        f"- Interactive decision-policy frontier resources: {payload.get('n_interactive_decision_policy_rows_with_frontier_resources')}/{payload.get('n_interactive_decision_policy_rows')}",
        f"- Interactive decision-policy quality gates: {payload.get('n_interactive_decision_policy_rows_with_quality_gates')}/{payload.get('n_interactive_decision_policy_rows')}",
        f"- Interactive decision-policy bundle links valid: {payload.get('n_publication_bundle_optional_interactive_decision_policy_link_valid')}/{payload.get('n_publication_bundle_optional_interactive_decision_policy_link_checked')}",
        f"- Interactive session replans: {payload.get('n_interactive_session_replan')}",
        f"- Interactive session waiting for adapter responses: {payload.get('n_interactive_session_waiting_for_adapter_responses')}",
        f"- Interactive session rows requiring replan: {payload.get('n_interactive_session_rows_requiring_replan')}",
        f"- Interactive session replay-ready: {payload.get('n_interactive_session_replay')}",
        f"- Ablation variants valid: {payload.get('n_ablation_row_schema_valid')}/{payload.get('n_ablation_variants')}",
        f"- Ablation largest route-recall drop: {payload.get('ablation_largest_route_recall_drop_variant')}",
        f"- Cross-prover targets: {payload.get('n_cross_prover_targets_ok')}/{payload.get('n_cross_prover_targets')}",
        f"- Cross-prover target-summary contract errors: {payload.get('n_cross_prover_target_summary_contract_errors')}",
        f"- Cross-prover matrix row schema valid: {payload.get('n_cross_prover_matrix_row_schema_valid')}/{payload.get('n_cross_prover_targets')}",
        f"- Cross-prover packet row schema valid: {payload.get('n_cross_prover_packet_row_schema_valid')}/{payload.get('n_cross_prover_total_packets')}",
        f"- Cross-prover response-validation row schema valid: {payload.get('n_cross_prover_response_validation_row_schema_valid')}/{payload.get('n_cross_prover_total_packets')}",
        f"- Cross-prover packets with standalone trace: {payload.get('n_cross_prover_total_packets_with_standalone_input_trace')}/{payload.get('n_cross_prover_total_packets')}",
        f"- Cross-prover packets with replan metadata trace: {payload.get('n_cross_prover_total_packets_with_replan_metadata_trace')}/{payload.get('n_cross_prover_total_packets')}",
        f"- Publication bundle cross-prover packet trace valid: {payload.get('n_publication_bundle_optional_cross_prover_packet_trace_valid')}/{payload.get('n_publication_bundle_optional_cross_prover_packet_trace_checked')}",
        f"- All OK: {payload.get('all_ok')}",
        "",
        "## Boundary",
        "",
        str(payload.get("proof_evidence_boundary", PROOF_EVIDENCE_BOUNDARY)),
        "",
        "## Stages",
        "",
    ]
    for stage in payload.get("stages", []):
        if not isinstance(stage, dict):
            continue
        lines.append(
            f"- `{stage.get('stage_name')}` ok={stage.get('ok')} "
            f"boundary={stage.get('proof_boundary_ok')} "
            f"manifest={stage.get('manifest_path')}"
        )
    lines.extend(["", "## Artifacts", ""])
    for name, path in dict(payload.get("artifacts", {})).items():
        lines.append(f"- `{name}`: {path}")
    lines.extend(["", "## Reproduce", ""])
    for command in payload.get("reproduction_commands", []):
        lines.extend(["```bash", str(command), "```"])
    return "\n".join(lines) + "\n"
