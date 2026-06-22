from __future__ import annotations

import json
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .fingerprint import stable_hash
from .formalization_gap_planner_contract import (
    LIBRARY_AWARE_FORMALIZATION_GAP_PLANNER_NAME,
    PORTABLE_FORMALIZATION_GAP_PLAN_SCHEMA_ID,
)
from .formalization_gap_planner_route_adoption_blockers import (
    ROUTE_ADOPTION_AWAITING_STATUS,
    ROUTE_ADOPTION_BLOCKER_FORMAL_ATTEMPT_QUEUE,
    ROUTE_ADOPTION_BLOCKER_PRIMITIVE_EVIDENCE_MATRIX,
    ROUTE_ADOPTION_BLOCKER_QUALITY_CONTROLS,
    ROUTE_ADOPTION_BLOCKER_SOURCE_GROUNDING,
    ROUTE_ADOPTION_BLOCKER_VALUES,
    ROUTE_ADOPTION_PENDING_STATUS,
    ROUTE_ADOPTION_READY_STATUS,
    ROUTE_ADOPTION_REJECTED_STATUS,
)


FORMALIZATION_GAP_PLANNER_EVALUATION_SCHEMA_VERSION = 1
EVALUATION_ROW_SCHEMA_ID = (
    "urn:ai-statistician:schemas:formalization-gap-planner-evaluation-row:1"
)
PROOF_EVIDENCE_STATUS = "FORMALIZATION_GAP_PLANNER_EVALUATION_NOT_PROOF_EVIDENCE"
PROOF_EVIDENCE_BOUNDARY = (
    "Formalization gap planner evaluation rows score route predictions against "
    "route-truth labels. They are evaluation diagnostics, not theorem proof "
    "evidence."
)
QUALITY_CONTROL_FIELDS = (
    "resource_contract_ids",
    "required_quality_signals",
    "quality_gates",
    "response_validation_signals",
    "stop_conditions",
)


@dataclass(frozen=True)
class FormalizationGapPlannerEvaluationRow:
    schema_version: int
    evaluation_id: str
    goal_plan_id: str
    route_id: str
    display_name: str
    matched_ground_truth: bool
    match_key: str
    predicted_route_primitives: tuple[str, ...]
    ground_truth_route_primitives: tuple[str, ...]
    route_true_positive_primitives: tuple[str, ...]
    route_missing_primitives: tuple[str, ...]
    route_extra_primitives: tuple[str, ...]
    route_recall: float
    route_precision: float
    predicted_delta_primitives: tuple[str, ...]
    ground_truth_delta_primitives: tuple[str, ...]
    delta_true_positive_primitives: tuple[str, ...]
    delta_unnecessary_primitives: tuple[str, ...]
    delta_missing_primitives: tuple[str, ...]
    delta_precision: float
    delta_recall: float
    predicted_residual_primitives: tuple[str, ...]
    ground_truth_residual_primitives: tuple[str, ...]
    residual_true_positive_primitives: tuple[str, ...]
    residual_missing_primitives: tuple[str, ...]
    residual_extra_primitives: tuple[str, ...]
    residual_precision: float
    residual_recall: float
    predicted_residual_goals: tuple[str, ...]
    ground_truth_residual_goals: tuple[str, ...]
    predicted_existing_reuse_primitives: tuple[str, ...]
    ground_truth_existing_reuse_primitives: tuple[str, ...]
    existing_reuse_precision: float
    existing_reuse_recall: float
    coverage_classification_accuracy: float
    n_coverage_classification_checked: int
    coverage_classification_confusions: tuple[dict[str, object], ...]
    two_dag_contract_ok: bool
    alignment_contract_ok: bool
    alignment_coverage: float
    aligned_primitives: tuple[str, ...]
    unaligned_primitives: tuple[str, ...]
    feedback_loop_ready: bool
    minimal_delta_cost_graph_present: bool
    minimal_delta_route_option_count: int
    minimal_delta_selected_route_option_id: str
    minimal_delta_selected_route_cost: float
    realization_coverage_witness_present: bool
    realization_coverage_complete: bool
    realization_missing_selected_formal_primitives: tuple[str, ...]
    realization_missing_delta_alignment_primitives: tuple[str, ...]
    realization_cost_hint_baseline_primitives: tuple[str, ...]
    realization_omitted_cost_hint_primitives: tuple[str, ...]
    realization_cost_hint_baseline_coverage_complete: bool
    llm_route_planner_trace_present: bool
    llm_route_planner_row_id: str
    llm_route_planner_provider: str
    llm_route_planner_model: str
    llm_route_planner_model_tier: str
    llm_route_planner_model_tier_decision_basis: str
    llm_route_planner_model_tier_decision_sonnet_triggers: tuple[str, ...]
    llm_route_planner_model_tier_decision_sonnet_trigger_count: int
    llm_route_planner_source_feedback_row_count: int
    llm_route_planner_source_feedback_unverified_semantic_primitive_row_count: int
    llm_route_planner_source_feedback_proof_body_execution_failure_count: int
    llm_route_planner_source_feedback_formal_environment_blocker_count: int
    llm_route_planner_interactive_formal_attempt_queue_row_count: int
    llm_route_planner_interactive_formal_attempt_queue_item_count: int
    llm_route_planner_interactive_formal_attempt_queue_ready_item_count: int
    llm_route_planner_interactive_formal_attempt_queue_blocked_item_count: int
    llm_route_planner_interactive_formal_attempt_queue_execution_command_count: int
    llm_route_planner_residual_goal_context_count: int
    llm_route_planner_residual_goal_context_residual_goals: tuple[str, ...]
    llm_route_planner_residual_goal_context_source_ref_count: int
    llm_route_planner_residual_goal_context_provenance_count: int
    llm_route_planner_residual_goals_with_context_count: int
    llm_route_planner_residual_goals_without_context: tuple[str, ...]
    llm_route_planner_route_option_selection_brief_present: bool
    llm_route_planner_route_option_selection_candidate_count: int
    llm_route_planner_route_option_selection_candidate_primitive_count: int
    llm_route_planner_route_option_selection_candidates_with_residual_goals: int
    llm_route_planner_route_option_selection_candidate_residual_goal_count: int
    llm_route_planner_route_option_selection_lower_bound_selected_route_option_id: str
    llm_route_planner_route_option_selected_route_option_id: str
    llm_route_planner_route_option_selection_lower_bound_residual_goal_count: int
    llm_route_planner_route_option_selection_minimal_delta_selected_residual_goal_count: int
    llm_route_planner_route_option_selection_lower_bound_matches_minimal_delta: bool
    llm_route_planner_route_option_selected_matches_lower_bound: bool
    llm_route_planner_route_option_selected_matches_minimal_delta: bool
    llm_route_planner_route_adoption_status: str
    llm_route_planner_route_adoption_blockers: tuple[str, ...]
    llm_route_planner_primitive_evidence_matrix_witness_present: bool
    llm_route_planner_primitive_evidence_matrix_accounting_complete: bool
    llm_route_planner_primitive_evidence_matrix_repair_obligation_count: int
    llm_route_planner_primitive_evidence_matrix_unaccounted_primitive_count: int
    llm_route_planner_primitive_evidence_matrix_selected_without_matrix_row_count: int
    llm_route_planner_primitive_evidence_matrix_source_backed_missing_response_source_snippet_count: int
    llm_route_planner_primitive_evidence_matrix_formal_supported_missing_reuse_count: int
    llm_route_planner_primitive_evidence_matrix_delta_needed_missing_accounting_count: int
    llm_route_planner_route_adoption_preconditions: dict[str, object]
    llm_route_planner_route_adoption_precondition_present: bool
    llm_route_planner_route_adoption_precondition_blocked_before_response: bool
    llm_route_planner_route_adoption_precondition_known_blockers: tuple[str, ...]
    llm_route_planner_route_adoption_precondition_required_response_fields: tuple[str, ...]
    llm_route_planner_route_adoption_precondition_target_primitives: tuple[str, ...]
    llm_route_planner_route_adoption_precondition_known_blocker_count: int
    llm_route_planner_route_adoption_precondition_required_response_field_count: int
    llm_route_planner_route_adoption_precondition_target_primitive_count: int
    llm_route_planner_acceptance_status: str
    llm_route_planner_model_selection_rationale: str
    llm_route_planner_has_generator_metadata: bool
    llm_route_planner_generator_metadata_keys: tuple[str, ...]
    llm_route_planner_has_provider_usage: bool
    llm_route_planner_provider_input_tokens: int
    llm_route_planner_provider_output_tokens: int
    llm_route_planner_provider_cache_creation_input_tokens: int
    llm_route_planner_provider_cache_read_input_tokens: int
    llm_route_planner_provider_total_tokens: int
    llm_route_planner_request_contract_blocked: bool
    llm_route_planner_errors: tuple[str, ...]
    llm_route_planner_generation_errors: tuple[str, ...]
    quality_controls_present: bool
    quality_controls: dict[str, tuple[str, ...]]
    quality_control_fields: tuple[str, ...]
    quality_control_resource_contract_ids: tuple[str, ...]
    quality_control_response_validation_signals: tuple[str, ...]
    quality_control_stop_conditions: tuple[str, ...]
    portable_schema_id: str
    proof_evidence_boundary_ok: bool
    kernel_verified_ground_truth: bool
    kernel_verification_witnesses: tuple[dict[str, object], ...]
    proof_evidence_status: str
    proof_evidence_boundary: str
    ok: bool
    errors: tuple[str, ...] = ()


def evaluate_formalization_gap_planner(
    goal_conditioned_minimal_formalization_plan_dir: Path,
    ground_truth_path: Path,
    out_dir: Path | None = None,
) -> dict[str, object]:
    """Evaluate a portable formalization-gap plan against held-out route truth.

    The ground truth file is intentionally lightweight and prover-agnostic. It
    may contain `routes`, `rows`, or `ground_truth_routes`; each item should be
    keyed by `route_id`, `display_name`, or `goal_plan_id`, and may provide:
    `required_primitives`, `actual_dependencies`, `actual_delta_primitives`,
    `actual_existing_reuse_primitives`, `coverage_by_primitive`,
    `expected_residual_primitives`, and `expected_residual_goals`.
    """

    errors: list[str] = []
    plan_manifest_path = (
        goal_conditioned_minimal_formalization_plan_dir
        / "goal_conditioned_minimal_formalization_plan_manifest.json"
    )
    plan_payload = _read_json(plan_manifest_path, errors)
    truth_payload = _read_json(ground_truth_path, errors)
    plan_rows = [row for row in plan_payload.get("rows", []) if isinstance(row, dict)]
    n_formal_realization_dag_nodes = sum(
        _node_field_count(row, "formal_realization_dag_nodes") for row in plan_rows
    )
    n_legacy_lean_realization_dag_nodes = sum(
        _node_field_count(row, "lean_realization_dag_nodes") for row in plan_rows
    )
    truth_rows = _truth_rows(truth_payload)
    truth_index = _truth_index(truth_rows)
    evaluation_rows = [
        _evaluate_row(row, truth_index, plan_payload)
        for row in plan_rows
    ]
    evaluation_row_dicts = [asdict(row) for row in evaluation_rows]
    evaluation_row_schema = evaluation_row_json_schema()
    evaluation_row_schema_errors = [
        validate_evaluation_row(row, evaluation_row_schema)
        for row in evaluation_row_dicts
    ]
    n_evaluation_row_schema_valid = sum(
        1 for row_errors in evaluation_row_schema_errors if not row_errors
    )
    matched_rows = [row for row in evaluation_rows if row.matched_ground_truth]
    matched_truth_keys = {
        row.match_key for row in matched_rows if row.match_key
    }
    truth_coverage_ok = not truth_rows or len(matched_truth_keys) >= len(truth_rows)
    by_ok = {True: 0, False: 0}
    for row in evaluation_rows:
        by_ok[row.ok] = by_ok.get(row.ok, 0) + 1
    by_llm_model_tier = _llm_model_tier_summary(evaluation_rows)
    by_llm_model_tier_decision_basis = (
        _llm_model_tier_decision_basis_summary(evaluation_rows)
    )
    llm_route_planner_provider_usage_rows = _llm_provider_usage_rows(
        evaluation_rows
    )
    llm_route_planner_provider_usage_summary = _llm_provider_usage_summary(
        llm_route_planner_provider_usage_rows
    )
    by_llm_route_adoption_status = _llm_route_adoption_status_summary(evaluation_rows)
    by_llm_route_adoption_blocker = _llm_route_adoption_blocker_summary(
        evaluation_rows
    )
    llm_route_adoption_blocker_counts = _llm_route_adoption_blocker_counts(
        evaluation_rows
    )
    llm_route_adoption_blockers = _unique_row_attr_strings(
        evaluation_rows,
        "llm_route_planner_route_adoption_blockers",
    )
    llm_route_adoption_precondition_blockers = _unique_row_attr_strings(
        evaluation_rows,
        "llm_route_planner_route_adoption_precondition_known_blockers",
    )
    llm_route_adoption_precondition_required_fields = _unique_row_attr_strings(
        evaluation_rows,
        "llm_route_planner_route_adoption_precondition_required_response_fields",
    )
    llm_route_adoption_precondition_target_primitives = _unique_row_attr_strings(
        evaluation_rows,
        "llm_route_planner_route_adoption_precondition_target_primitives",
    )
    quality_control_fields = _unique_row_attr_strings(
        evaluation_rows,
        "quality_control_fields",
    )
    quality_control_resource_contract_ids = _unique_row_attr_strings(
        evaluation_rows,
        "quality_control_resource_contract_ids",
    )
    quality_control_response_validation_signals = _unique_row_attr_strings(
        evaluation_rows,
        "quality_control_response_validation_signals",
    )
    quality_control_stop_conditions = _unique_row_attr_strings(
        evaluation_rows,
        "quality_control_stop_conditions",
    )
    realization_missing_selected = _unique_row_attr_strings(
        evaluation_rows,
        "realization_missing_selected_formal_primitives",
    )
    realization_missing_delta = _unique_row_attr_strings(
        evaluation_rows,
        "realization_missing_delta_alignment_primitives",
    )
    realization_cost_hint_baseline = _unique_row_attr_strings(
        evaluation_rows,
        "realization_cost_hint_baseline_primitives",
    )
    realization_omitted_cost_hint = _unique_row_attr_strings(
        evaluation_rows,
        "realization_omitted_cost_hint_primitives",
    )
    payload: dict[str, object] = {
        "schema_version": FORMALIZATION_GAP_PLANNER_EVALUATION_SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "component_name": "formalization_gap_planner_evaluation",
        "evaluated_component": plan_payload.get("component_name", ""),
        "portable_schema_id": plan_payload.get("portable_schema_id", ""),
        "expected_portable_schema_id": PORTABLE_FORMALIZATION_GAP_PLAN_SCHEMA_ID,
        "goal_conditioned_minimal_formalization_plan_dir": str(
            goal_conditioned_minimal_formalization_plan_dir
        ),
        "goal_conditioned_minimal_formalization_plan_manifest": str(plan_manifest_path),
        "ground_truth_path": str(ground_truth_path),
        "bundled_ground_truth_filename": "formalization_gap_planner_evaluation_ground_truth.json",
        "n_plan_rows": len(plan_rows),
        "n_plan_rows_with_formal_realization_dag_nodes": sum(
            1 for row in plan_rows if _node_field_count(row, "formal_realization_dag_nodes")
        ),
        "n_plan_rows_with_legacy_lean_realization_dag_nodes": sum(
            1 for row in plan_rows if _node_field_count(row, "lean_realization_dag_nodes")
        ),
        "n_formal_realization_dag_nodes": n_formal_realization_dag_nodes,
        "n_legacy_lean_realization_dag_nodes": n_legacy_lean_realization_dag_nodes,
        "n_ground_truth_rows": len(truth_rows),
        "n_evaluation_rows": len(evaluation_rows),
        "n_evaluation_row_schema_valid": n_evaluation_row_schema_valid,
        "n_evaluation_row_schema_invalid": len(evaluation_row_schema_errors)
        - n_evaluation_row_schema_valid,
        "n_matched_ground_truth": sum(1 for row in evaluation_rows if row.matched_ground_truth),
        "n_missing_ground_truth": sum(1 for row in evaluation_rows if not row.matched_ground_truth),
        "n_unlabeled_plan_rows": sum(1 for row in evaluation_rows if not row.matched_ground_truth),
        "n_matched_ground_truth_ok": sum(row.ok for row in matched_rows),
        "n_ground_truth_rows_matched_by_plan": len(matched_truth_keys),
        "ground_truth_coverage_ok": truth_coverage_ok,
        "n_ok": sum(1 for row in evaluation_rows if row.ok),
        "n_two_dag_contract_ok": sum(1 for row in evaluation_rows if row.two_dag_contract_ok),
        "n_alignment_contract_ok": sum(
            1 for row in evaluation_rows if row.alignment_contract_ok
        ),
        "n_feedback_loop_ready": sum(1 for row in evaluation_rows if row.feedback_loop_ready),
        "n_rows_with_minimal_delta_cost_graph": sum(
            1 for row in evaluation_rows if row.minimal_delta_cost_graph_present
        ),
        "n_rows_with_realization_coverage_witness": sum(
            1 for row in evaluation_rows if row.realization_coverage_witness_present
        ),
        "n_rows_with_complete_realization_coverage": sum(
            1 for row in evaluation_rows if row.realization_coverage_complete
        ),
        "n_rows_with_incomplete_cost_hint_baseline_coverage": sum(
            1
            for row in evaluation_rows
            if not row.realization_cost_hint_baseline_coverage_complete
        ),
        "n_rows_with_llm_route_planner_trace": sum(
            1 for row in evaluation_rows if row.llm_route_planner_trace_present
        ),
        "n_rows_with_llm_route_planner_model_tier": sum(
            1 for row in evaluation_rows if row.llm_route_planner_model_tier
        ),
        "n_rows_with_llm_route_planner_model_tier_decision_basis": sum(
            1
            for row in evaluation_rows
            if row.llm_route_planner_model_tier_decision_basis
        ),
        "n_llm_route_planner_model_tier_decision_sonnet_triggers": sum(
            row.llm_route_planner_model_tier_decision_sonnet_trigger_count
            for row in evaluation_rows
        ),
        "n_rows_with_llm_route_planner_source_feedback_tier_signal": sum(
            1
            for row in evaluation_rows
            if row.llm_route_planner_source_feedback_row_count
        ),
        "n_llm_route_planner_source_feedback_rows": sum(
            row.llm_route_planner_source_feedback_row_count
            for row in evaluation_rows
        ),
        "n_llm_route_planner_source_feedback_unverified_semantic_primitive_rows": (
            sum(
                row.llm_route_planner_source_feedback_unverified_semantic_primitive_row_count
                for row in evaluation_rows
            )
        ),
        "n_llm_route_planner_source_feedback_proof_body_execution_failures": sum(
            row.llm_route_planner_source_feedback_proof_body_execution_failure_count
            for row in evaluation_rows
        ),
        "n_llm_route_planner_source_feedback_formal_environment_blockers": sum(
            row.llm_route_planner_source_feedback_formal_environment_blocker_count
            for row in evaluation_rows
        ),
        "n_rows_with_llm_route_planner_interactive_formal_attempt_queue_tier_signal": sum(
            1
            for row in evaluation_rows
            if row.llm_route_planner_interactive_formal_attempt_queue_item_count
            or row.llm_route_planner_interactive_formal_attempt_queue_execution_command_count
        ),
        "n_llm_route_planner_interactive_formal_attempt_queue_rows": sum(
            row.llm_route_planner_interactive_formal_attempt_queue_row_count
            for row in evaluation_rows
        ),
        "n_llm_route_planner_interactive_formal_attempt_queue_items": sum(
            row.llm_route_planner_interactive_formal_attempt_queue_item_count
            for row in evaluation_rows
        ),
        "n_llm_route_planner_interactive_formal_attempt_queue_ready_items": sum(
            row.llm_route_planner_interactive_formal_attempt_queue_ready_item_count
            for row in evaluation_rows
        ),
        "n_llm_route_planner_interactive_formal_attempt_queue_blocked_items": sum(
            row.llm_route_planner_interactive_formal_attempt_queue_blocked_item_count
            for row in evaluation_rows
        ),
        "n_llm_route_planner_interactive_formal_attempt_queue_execution_commands": sum(
            row.llm_route_planner_interactive_formal_attempt_queue_execution_command_count
            for row in evaluation_rows
        ),
        "n_rows_with_llm_route_planner_residual_goal_contexts": sum(
            1
            for row in evaluation_rows
            if row.llm_route_planner_residual_goal_context_count
        ),
        "n_llm_route_planner_residual_goal_contexts": sum(
            row.llm_route_planner_residual_goal_context_count
            for row in evaluation_rows
        ),
        "n_llm_route_planner_residual_goal_context_source_refs": sum(
            row.llm_route_planner_residual_goal_context_source_ref_count
            for row in evaluation_rows
        ),
        "n_llm_route_planner_residual_goal_context_provenance_values": sum(
            row.llm_route_planner_residual_goal_context_provenance_count
            for row in evaluation_rows
        ),
        "n_llm_route_planner_residual_goals_with_context": sum(
            row.llm_route_planner_residual_goals_with_context_count
            for row in evaluation_rows
        ),
        "n_llm_route_planner_residual_goals_without_context": sum(
            len(row.llm_route_planner_residual_goals_without_context)
            for row in evaluation_rows
        ),
        "n_rows_with_llm_route_planner_route_option_selection_brief": sum(
            1
            for row in evaluation_rows
            if row.llm_route_planner_route_option_selection_brief_present
        ),
        "n_llm_route_planner_route_option_selection_candidate_options": sum(
            row.llm_route_planner_route_option_selection_candidate_count
            for row in evaluation_rows
        ),
        "n_llm_route_planner_route_option_selection_candidate_primitives": sum(
            row.llm_route_planner_route_option_selection_candidate_primitive_count
            for row in evaluation_rows
        ),
        "n_llm_route_planner_route_option_selection_candidates_with_residual_goals": sum(
            row.llm_route_planner_route_option_selection_candidates_with_residual_goals
            for row in evaluation_rows
        ),
        "n_llm_route_planner_route_option_selection_candidate_residual_goals": sum(
            row.llm_route_planner_route_option_selection_candidate_residual_goal_count
            for row in evaluation_rows
        ),
        "n_llm_route_planner_route_option_selection_lower_bound_residual_goals": sum(
            row.llm_route_planner_route_option_selection_lower_bound_residual_goal_count
            for row in evaluation_rows
        ),
        "n_rows_with_llm_route_planner_route_option_selected_route_option": sum(
            1
            for row in evaluation_rows
            if row.llm_route_planner_route_option_selected_route_option_id
        ),
        "n_llm_route_planner_route_option_selection_minimal_delta_selected_residual_goals": sum(
            row.llm_route_planner_route_option_selection_minimal_delta_selected_residual_goal_count
            for row in evaluation_rows
        ),
        "n_llm_route_planner_route_option_selection_lower_bound_matches_minimal_delta": sum(
            1
            for row in evaluation_rows
            if row.llm_route_planner_route_option_selection_brief_present
            and row.llm_route_planner_route_option_selection_lower_bound_matches_minimal_delta
        ),
        "n_llm_route_planner_route_option_selection_lower_bound_mismatches_minimal_delta": sum(
            1
            for row in evaluation_rows
            if row.llm_route_planner_route_option_selection_brief_present
            and not row.llm_route_planner_route_option_selection_lower_bound_matches_minimal_delta
        ),
        "n_llm_route_planner_route_option_selected_matches_lower_bound": sum(
            1
            for row in evaluation_rows
            if row.llm_route_planner_route_option_selected_route_option_id
            and row.llm_route_planner_route_option_selected_matches_lower_bound
        ),
        "n_llm_route_planner_route_option_selected_mismatches_lower_bound": sum(
            1
            for row in evaluation_rows
            if row.llm_route_planner_route_option_selected_route_option_id
            and row.llm_route_planner_route_option_selection_lower_bound_selected_route_option_id
            and not row.llm_route_planner_route_option_selected_matches_lower_bound
        ),
        "n_llm_route_planner_route_option_selected_matches_minimal_delta": sum(
            1
            for row in evaluation_rows
            if row.llm_route_planner_route_option_selected_route_option_id
            and row.llm_route_planner_route_option_selected_matches_minimal_delta
        ),
        "n_llm_route_planner_route_option_selected_mismatches_minimal_delta": sum(
            1
            for row in evaluation_rows
            if row.llm_route_planner_route_option_selected_route_option_id
            and row.minimal_delta_selected_route_option_id
            and not row.llm_route_planner_route_option_selected_matches_minimal_delta
        ),
        "n_rows_with_llm_route_planner_route_adoption_status": sum(
            1
            for row in evaluation_rows
            if row.llm_route_planner_route_adoption_status
        ),
        "n_rows_ready_for_route_adoption": sum(
            1
            for row in evaluation_rows
            if row.llm_route_planner_route_adoption_status
            == ROUTE_ADOPTION_READY_STATUS
        ),
        "n_rows_pending_refinement_before_route_adoption": sum(
            1
            for row in evaluation_rows
            if row.llm_route_planner_route_adoption_status
            == ROUTE_ADOPTION_PENDING_STATUS
        ),
        "n_rows_awaiting_llm_route_planner_response": sum(
            1
            for row in evaluation_rows
            if row.llm_route_planner_route_adoption_status
            == ROUTE_ADOPTION_AWAITING_STATUS
        ),
        "n_rows_rejected_llm_route_plan": sum(
            1
            for row in evaluation_rows
            if row.llm_route_planner_route_adoption_status
            == ROUTE_ADOPTION_REJECTED_STATUS
        ),
        "n_llm_route_adoption_blockers": sum(
            len(row.llm_route_planner_route_adoption_blockers)
            for row in evaluation_rows
        ),
        "n_llm_route_adoption_pending_quality_control_blockers": sum(
            1
            for row in evaluation_rows
            if ROUTE_ADOPTION_BLOCKER_QUALITY_CONTROLS
            in row.llm_route_planner_route_adoption_blockers
        ),
        "n_llm_route_adoption_pending_source_grounding_blockers": sum(
            1
            for row in evaluation_rows
            if ROUTE_ADOPTION_BLOCKER_SOURCE_GROUNDING
            in row.llm_route_planner_route_adoption_blockers
        ),
        "n_llm_route_adoption_pending_formal_attempt_queue_blockers": sum(
            1
            for row in evaluation_rows
            if ROUTE_ADOPTION_BLOCKER_FORMAL_ATTEMPT_QUEUE
            in row.llm_route_planner_route_adoption_blockers
        ),
        "n_llm_route_adoption_pending_primitive_evidence_matrix_blockers": sum(
            1
            for row in evaluation_rows
            if ROUTE_ADOPTION_BLOCKER_PRIMITIVE_EVIDENCE_MATRIX
            in row.llm_route_planner_route_adoption_blockers
        ),
        "n_rows_with_llm_route_planner_primitive_evidence_matrix_witness": sum(
            1
            for row in evaluation_rows
            if row.llm_route_planner_primitive_evidence_matrix_witness_present
        ),
        "n_rows_with_complete_llm_route_planner_primitive_evidence_matrix_accounting": sum(
            1
            for row in evaluation_rows
            if row.llm_route_planner_primitive_evidence_matrix_accounting_complete
        ),
        "n_llm_route_planner_primitive_evidence_matrix_repair_obligations": sum(
            row.llm_route_planner_primitive_evidence_matrix_repair_obligation_count
            for row in evaluation_rows
        ),
        "n_llm_route_planner_primitive_evidence_matrix_unaccounted_primitives": sum(
            row.llm_route_planner_primitive_evidence_matrix_unaccounted_primitive_count
            for row in evaluation_rows
        ),
        "n_llm_route_planner_primitive_evidence_matrix_selected_without_matrix_rows": sum(
            row.llm_route_planner_primitive_evidence_matrix_selected_without_matrix_row_count
            for row in evaluation_rows
        ),
        "n_llm_route_planner_primitive_evidence_matrix_source_backed_missing_response_source_snippets": sum(
            row.llm_route_planner_primitive_evidence_matrix_source_backed_missing_response_source_snippet_count
            for row in evaluation_rows
        ),
        "n_llm_route_planner_primitive_evidence_matrix_formal_supported_missing_reuse": sum(
            row.llm_route_planner_primitive_evidence_matrix_formal_supported_missing_reuse_count
            for row in evaluation_rows
        ),
        "n_llm_route_planner_primitive_evidence_matrix_delta_needed_missing_accounting": sum(
            row.llm_route_planner_primitive_evidence_matrix_delta_needed_missing_accounting_count
            for row in evaluation_rows
        ),
        "n_rows_with_llm_route_planner_route_adoption_preconditions": sum(
            1
            for row in evaluation_rows
            if row.llm_route_planner_route_adoption_precondition_present
        ),
        "n_rows_with_llm_route_planner_blocking_route_adoption_preconditions": sum(
            1
            for row in evaluation_rows
            if row.llm_route_planner_route_adoption_precondition_blocked_before_response
        ),
        "n_llm_route_planner_route_adoption_precondition_known_blockers": sum(
            row.llm_route_planner_route_adoption_precondition_known_blocker_count
            for row in evaluation_rows
        ),
        "n_llm_route_planner_route_adoption_precondition_required_response_fields": sum(
            row.llm_route_planner_route_adoption_precondition_required_response_field_count
            for row in evaluation_rows
        ),
        "n_llm_route_planner_route_adoption_precondition_target_primitives": sum(
            row.llm_route_planner_route_adoption_precondition_target_primitive_count
            for row in evaluation_rows
        ),
        "llm_route_planner_route_adoption_precondition_known_blockers": (
            llm_route_adoption_precondition_blockers
        ),
        "llm_route_planner_route_adoption_precondition_required_response_fields": (
            llm_route_adoption_precondition_required_fields
        ),
        "llm_route_planner_route_adoption_precondition_target_primitives": (
            llm_route_adoption_precondition_target_primitives
        ),
        "llm_route_adoption_blockers": llm_route_adoption_blockers,
        "llm_route_adoption_blocker_counts": llm_route_adoption_blocker_counts,
        "evaluation_by_llm_route_adoption_status": by_llm_route_adoption_status,
        "evaluation_by_llm_route_adoption_blocker": by_llm_route_adoption_blocker,
        "n_rows_with_llm_route_planner_generator_metadata": sum(
            1
            for row in evaluation_rows
            if row.llm_route_planner_has_generator_metadata
        ),
        "llm_route_planner_provider_usage_rows": (
            llm_route_planner_provider_usage_rows
        ),
        "llm_route_planner_provider_usage_summary": (
            llm_route_planner_provider_usage_summary
        ),
        "n_rows_with_llm_route_planner_provider_usage": int(
            llm_route_planner_provider_usage_summary.get("row_count", 0) or 0
        ),
        "total_llm_route_planner_provider_input_tokens": int(
            llm_route_planner_provider_usage_summary.get("input_tokens", 0) or 0
        ),
        "total_llm_route_planner_provider_output_tokens": int(
            llm_route_planner_provider_usage_summary.get("output_tokens", 0) or 0
        ),
        "total_llm_route_planner_provider_cache_creation_input_tokens": int(
            llm_route_planner_provider_usage_summary.get(
                "cache_creation_input_tokens",
                0,
            )
            or 0
        ),
        "total_llm_route_planner_provider_cache_read_input_tokens": int(
            llm_route_planner_provider_usage_summary.get(
                "cache_read_input_tokens",
                0,
            )
            or 0
        ),
        "total_llm_route_planner_provider_total_tokens": int(
            llm_route_planner_provider_usage_summary.get("total_tokens", 0) or 0
        ),
        "n_rows_with_llm_route_planner_request_contract_blocked": sum(
            1
            for row in evaluation_rows
            if row.llm_route_planner_request_contract_blocked
        ),
        "n_rows_with_llm_route_planner_errors": sum(
            1 for row in evaluation_rows if row.llm_route_planner_errors
        ),
        "n_llm_route_planner_errors": sum(
            len(row.llm_route_planner_errors) for row in evaluation_rows
        ),
        "n_llm_route_planner_generation_errors": sum(
            len(row.llm_route_planner_generation_errors) for row in evaluation_rows
        ),
        "evaluation_by_llm_model_tier": by_llm_model_tier,
        "evaluation_by_llm_model_tier_decision_basis": (
            by_llm_model_tier_decision_basis
        ),
        "n_rows_with_quality_controls": sum(
            1 for row in evaluation_rows if row.quality_controls_present
        ),
        "n_quality_control_fields": sum(
            len(row.quality_control_fields) for row in evaluation_rows
        ),
        "quality_control_fields": quality_control_fields,
        "quality_control_resource_contract_ids": quality_control_resource_contract_ids,
        "quality_control_response_validation_signals": (
            quality_control_response_validation_signals
        ),
        "quality_control_stop_conditions": quality_control_stop_conditions,
        "evaluation_by_quality_control_field": _quality_control_field_summary(
            evaluation_rows
        ),
        "n_realization_missing_selected_formal_primitives": sum(
            len(row.realization_missing_selected_formal_primitives)
            for row in evaluation_rows
        ),
        "realization_missing_selected_formal_primitives": realization_missing_selected,
        "n_realization_missing_delta_alignment_primitives": sum(
            len(row.realization_missing_delta_alignment_primitives)
            for row in evaluation_rows
        ),
        "realization_missing_delta_alignment_primitives": realization_missing_delta,
        "n_realization_cost_hint_baseline_primitives": sum(
            len(row.realization_cost_hint_baseline_primitives)
            for row in evaluation_rows
        ),
        "realization_cost_hint_baseline_primitives": realization_cost_hint_baseline,
        "n_realization_omitted_cost_hint_primitives": sum(
            len(row.realization_omitted_cost_hint_primitives)
            for row in evaluation_rows
        ),
        "realization_omitted_cost_hint_primitives": realization_omitted_cost_hint,
        "realization_missing_primitives_by_route": (
            _realization_missing_primitives_by_route(evaluation_rows)
        ),
        "n_minimal_delta_route_options": sum(
            row.minimal_delta_route_option_count for row in evaluation_rows
        ),
        "mean_minimal_delta_selected_route_cost": _mean(
            row.minimal_delta_selected_route_cost
            for row in evaluation_rows
            if row.minimal_delta_cost_graph_present
        ),
        "n_unaligned_primitives": sum(
            len(row.unaligned_primitives) for row in evaluation_rows
        ),
        "n_kernel_verified_ground_truth": sum(
            1 for row in evaluation_rows if row.kernel_verified_ground_truth
        ),
        "n_kernel_verification_witnesses": sum(
            len(row.kernel_verification_witnesses) for row in evaluation_rows
        ),
        "n_kernel_verified_ground_truth_with_witnesses": sum(
            1
            for row in evaluation_rows
            if row.kernel_verified_ground_truth and row.kernel_verification_witnesses
        ),
        "mean_route_recall": _mean(row.route_recall for row in matched_rows),
        "mean_route_precision": _mean(row.route_precision for row in matched_rows),
        "mean_delta_precision": _mean(row.delta_precision for row in matched_rows),
        "mean_delta_recall": _mean(row.delta_recall for row in matched_rows),
        "n_ground_truth_residual_rows": sum(
            1 for row in matched_rows if row.ground_truth_residual_primitives
        ),
        "n_predicted_residual_primitives": sum(
            len(row.predicted_residual_primitives) for row in matched_rows
        ),
        "n_ground_truth_residual_primitives": sum(
            len(row.ground_truth_residual_primitives) for row in matched_rows
        ),
        "mean_residual_precision": _mean(
            row.residual_precision
            for row in matched_rows
            if row.ground_truth_residual_primitives
            or row.predicted_residual_primitives
        ),
        "mean_residual_recall": _mean(
            row.residual_recall
            for row in matched_rows
            if row.ground_truth_residual_primitives
        ),
        "mean_existing_reuse_precision": _mean(
            row.existing_reuse_precision for row in matched_rows
        ),
        "mean_existing_reuse_recall": _mean(
            row.existing_reuse_recall for row in matched_rows
        ),
        "mean_coverage_classification_accuracy": _mean(
            row.coverage_classification_accuracy
            for row in matched_rows
            if row.n_coverage_classification_checked > 0
        ),
        "mean_alignment_coverage": _mean(
            row.alignment_coverage for row in evaluation_rows
        ),
        "all_ok": (
            not errors
            and bool(evaluation_rows)
            and all(row.ok for row in evaluation_rows)
            and truth_coverage_ok
            and len(evaluation_row_schema_errors) == n_evaluation_row_schema_valid
        ),
        "errors": errors,
        "evaluation_row_schema": evaluation_row_schema,
        "rows": evaluation_row_dicts,
        "evaluation_fingerprint": stable_hash(evaluation_row_dicts),
        "proof_evidence_status": PROOF_EVIDENCE_STATUS,
        "proof_evidence_boundary": PROOF_EVIDENCE_BOUNDARY,
        "limitations": [
            "evaluation scores planner predictions against supplied route truth; it is not proof evidence",
            "route recall and delta precision depend on the quality and granularity of the ground truth file",
            "minimality proxy is structural; final proof status still requires target-prover kernel verification",
        ],
    }
    if out_dir is not None:
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "formalization_gap_planner_evaluation_manifest.json").write_text(
            json.dumps(payload, indent=2, default=str),
            encoding="utf-8",
        )
        (out_dir / "formalization_gap_planner_evaluation.jsonl").write_text(
            "\n".join(json.dumps(row, sort_keys=True) for row in evaluation_row_dicts)
            + ("\n" if evaluation_rows else ""),
            encoding="utf-8",
        )
        (out_dir / "formalization_gap_planner_evaluation_row.schema.json").write_text(
            json.dumps(evaluation_row_schema, indent=2),
            encoding="utf-8",
        )
        (
            out_dir / "formalization_gap_planner_evaluation_ground_truth.json"
        ).write_text(
            json.dumps(truth_payload, indent=2, default=str),
            encoding="utf-8",
        )
        (out_dir / "formalization_gap_planner_evaluation.md").write_text(
            _markdown_report(payload),
            encoding="utf-8",
        )
    return payload


def evaluation_row_json_schema() -> dict[str, object]:
    string_array = {"type": "array", "items": {"type": "string"}}
    route_adoption_blocker_array = {
        "type": "array",
        "items": {
            "type": "string",
            "enum": list(ROUTE_ADOPTION_BLOCKER_VALUES),
        },
    }
    object_array = {"type": "array", "items": {"type": "object"}}
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": EVALUATION_ROW_SCHEMA_ID,
        "title": "Formalization Gap Planner Evaluation Row",
        "description": (
            "Per-route evaluation diagnostics comparing planner route and "
            "minimal-delta predictions against route-truth labels. Rows are not "
            "theorem proof evidence."
        ),
        "type": "object",
        "additionalProperties": True,
        "required": [
            "schema_version",
            "evaluation_id",
            "goal_plan_id",
            "route_id",
            "display_name",
            "matched_ground_truth",
            "match_key",
            "predicted_route_primitives",
            "ground_truth_route_primitives",
            "route_true_positive_primitives",
            "route_missing_primitives",
            "route_extra_primitives",
            "route_recall",
            "route_precision",
            "predicted_delta_primitives",
            "ground_truth_delta_primitives",
            "delta_true_positive_primitives",
            "delta_unnecessary_primitives",
            "delta_missing_primitives",
            "delta_precision",
            "delta_recall",
            "predicted_residual_primitives",
            "ground_truth_residual_primitives",
            "residual_true_positive_primitives",
            "residual_missing_primitives",
            "residual_extra_primitives",
            "residual_precision",
            "residual_recall",
            "predicted_residual_goals",
            "ground_truth_residual_goals",
            "predicted_existing_reuse_primitives",
            "ground_truth_existing_reuse_primitives",
            "existing_reuse_precision",
            "existing_reuse_recall",
            "coverage_classification_accuracy",
            "n_coverage_classification_checked",
            "coverage_classification_confusions",
            "two_dag_contract_ok",
            "alignment_contract_ok",
            "alignment_coverage",
            "aligned_primitives",
            "unaligned_primitives",
            "feedback_loop_ready",
            "minimal_delta_cost_graph_present",
            "minimal_delta_route_option_count",
            "minimal_delta_selected_route_option_id",
            "minimal_delta_selected_route_cost",
            "realization_coverage_witness_present",
            "realization_coverage_complete",
            "realization_missing_selected_formal_primitives",
            "realization_missing_delta_alignment_primitives",
            "realization_cost_hint_baseline_primitives",
            "realization_omitted_cost_hint_primitives",
            "realization_cost_hint_baseline_coverage_complete",
            "llm_route_planner_trace_present",
            "llm_route_planner_row_id",
            "llm_route_planner_provider",
            "llm_route_planner_model",
            "llm_route_planner_model_tier",
            "llm_route_planner_model_tier_decision_basis",
            "llm_route_planner_model_tier_decision_sonnet_triggers",
            "llm_route_planner_model_tier_decision_sonnet_trigger_count",
            "llm_route_planner_source_feedback_row_count",
            "llm_route_planner_source_feedback_unverified_semantic_primitive_row_count",
            "llm_route_planner_source_feedback_proof_body_execution_failure_count",
            "llm_route_planner_source_feedback_formal_environment_blocker_count",
            "llm_route_planner_interactive_formal_attempt_queue_row_count",
            "llm_route_planner_interactive_formal_attempt_queue_item_count",
            "llm_route_planner_interactive_formal_attempt_queue_ready_item_count",
            "llm_route_planner_interactive_formal_attempt_queue_blocked_item_count",
            "llm_route_planner_interactive_formal_attempt_queue_execution_command_count",
            "llm_route_planner_residual_goal_context_count",
            "llm_route_planner_residual_goal_context_residual_goals",
            "llm_route_planner_residual_goal_context_source_ref_count",
            "llm_route_planner_residual_goal_context_provenance_count",
            "llm_route_planner_residual_goals_with_context_count",
            "llm_route_planner_residual_goals_without_context",
            "llm_route_planner_route_option_selection_brief_present",
            "llm_route_planner_route_option_selection_candidate_count",
            "llm_route_planner_route_option_selection_candidate_primitive_count",
            "llm_route_planner_route_option_selection_candidates_with_residual_goals",
            "llm_route_planner_route_option_selection_candidate_residual_goal_count",
            "llm_route_planner_route_option_selection_lower_bound_selected_route_option_id",
            "llm_route_planner_route_option_selected_route_option_id",
            "llm_route_planner_route_option_selection_lower_bound_residual_goal_count",
            "llm_route_planner_route_option_selection_minimal_delta_selected_residual_goal_count",
            "llm_route_planner_route_option_selection_lower_bound_matches_minimal_delta",
            "llm_route_planner_route_option_selected_matches_lower_bound",
            "llm_route_planner_route_option_selected_matches_minimal_delta",
            "llm_route_planner_route_adoption_status",
            "llm_route_planner_route_adoption_blockers",
            "llm_route_planner_route_adoption_preconditions",
            "llm_route_planner_route_adoption_precondition_present",
            "llm_route_planner_route_adoption_precondition_blocked_before_response",
            "llm_route_planner_route_adoption_precondition_known_blockers",
            "llm_route_planner_route_adoption_precondition_required_response_fields",
            "llm_route_planner_route_adoption_precondition_target_primitives",
            "llm_route_planner_route_adoption_precondition_known_blocker_count",
            "llm_route_planner_route_adoption_precondition_required_response_field_count",
            "llm_route_planner_route_adoption_precondition_target_primitive_count",
            "llm_route_planner_acceptance_status",
            "llm_route_planner_model_selection_rationale",
            "llm_route_planner_has_generator_metadata",
            "llm_route_planner_generator_metadata_keys",
            "llm_route_planner_request_contract_blocked",
            "llm_route_planner_errors",
            "llm_route_planner_generation_errors",
            "quality_controls_present",
            "quality_controls",
            "quality_control_fields",
            "quality_control_resource_contract_ids",
            "quality_control_response_validation_signals",
            "quality_control_stop_conditions",
            "portable_schema_id",
            "proof_evidence_boundary_ok",
            "kernel_verified_ground_truth",
            "kernel_verification_witnesses",
            "proof_evidence_status",
            "proof_evidence_boundary",
            "ok",
        ],
        "properties": {
            "schema_version": {
                "type": "integer",
                "const": FORMALIZATION_GAP_PLANNER_EVALUATION_SCHEMA_VERSION,
            },
            "evaluation_id": {"type": "string", "minLength": 1},
            "goal_plan_id": {"type": "string", "minLength": 1},
            "route_id": {"type": "string", "minLength": 1},
            "display_name": {"type": "string", "minLength": 1},
            "matched_ground_truth": {"type": "boolean"},
            "match_key": {"type": "string"},
            "predicted_route_primitives": string_array,
            "ground_truth_route_primitives": string_array,
            "route_true_positive_primitives": string_array,
            "route_missing_primitives": string_array,
            "route_extra_primitives": string_array,
            "route_recall": {"type": "number"},
            "route_precision": {"type": "number"},
            "predicted_delta_primitives": string_array,
            "ground_truth_delta_primitives": string_array,
            "delta_true_positive_primitives": string_array,
            "delta_unnecessary_primitives": string_array,
            "delta_missing_primitives": string_array,
            "delta_precision": {"type": "number"},
            "delta_recall": {"type": "number"},
            "predicted_residual_primitives": string_array,
            "ground_truth_residual_primitives": string_array,
            "residual_true_positive_primitives": string_array,
            "residual_missing_primitives": string_array,
            "residual_extra_primitives": string_array,
            "residual_precision": {"type": "number"},
            "residual_recall": {"type": "number"},
            "predicted_residual_goals": string_array,
            "ground_truth_residual_goals": string_array,
            "predicted_existing_reuse_primitives": string_array,
            "ground_truth_existing_reuse_primitives": string_array,
            "existing_reuse_precision": {"type": "number"},
            "existing_reuse_recall": {"type": "number"},
            "coverage_classification_accuracy": {"type": "number"},
            "n_coverage_classification_checked": {"type": "integer"},
            "coverage_classification_confusions": object_array,
            "two_dag_contract_ok": {"type": "boolean"},
            "alignment_contract_ok": {"type": "boolean"},
            "alignment_coverage": {"type": "number"},
            "aligned_primitives": string_array,
            "unaligned_primitives": string_array,
            "feedback_loop_ready": {"type": "boolean"},
            "minimal_delta_cost_graph_present": {"type": "boolean"},
            "minimal_delta_route_option_count": {"type": "integer", "minimum": 0},
            "minimal_delta_selected_route_option_id": {"type": "string"},
            "minimal_delta_selected_route_cost": {"type": "number", "minimum": 0},
            "realization_coverage_witness_present": {"type": "boolean"},
            "realization_coverage_complete": {"type": "boolean"},
            "realization_missing_selected_formal_primitives": string_array,
            "realization_missing_delta_alignment_primitives": string_array,
            "realization_cost_hint_baseline_primitives": string_array,
            "realization_omitted_cost_hint_primitives": string_array,
            "realization_cost_hint_baseline_coverage_complete": {"type": "boolean"},
            "llm_route_planner_trace_present": {"type": "boolean"},
            "llm_route_planner_row_id": {"type": "string"},
            "llm_route_planner_provider": {"type": "string"},
            "llm_route_planner_model": {"type": "string"},
            "llm_route_planner_model_tier": {"type": "string"},
            "llm_route_planner_model_tier_decision_basis": {"type": "string"},
            "llm_route_planner_model_tier_decision_sonnet_triggers": (
                string_array
            ),
            "llm_route_planner_model_tier_decision_sonnet_trigger_count": {
                "type": "integer",
                "minimum": 0,
            },
            "llm_route_planner_source_feedback_row_count": {
                "type": "integer",
                "minimum": 0,
            },
            "llm_route_planner_source_feedback_unverified_semantic_primitive_row_count": {
                "type": "integer",
                "minimum": 0,
            },
            "llm_route_planner_source_feedback_proof_body_execution_failure_count": {
                "type": "integer",
                "minimum": 0,
            },
            "llm_route_planner_source_feedback_formal_environment_blocker_count": {
                "type": "integer",
                "minimum": 0,
            },
            "llm_route_planner_interactive_formal_attempt_queue_row_count": {
                "type": "integer",
                "minimum": 0,
            },
            "llm_route_planner_interactive_formal_attempt_queue_item_count": {
                "type": "integer",
                "minimum": 0,
            },
            "llm_route_planner_interactive_formal_attempt_queue_ready_item_count": {
                "type": "integer",
                "minimum": 0,
            },
            "llm_route_planner_interactive_formal_attempt_queue_blocked_item_count": {
                "type": "integer",
                "minimum": 0,
            },
            "llm_route_planner_interactive_formal_attempt_queue_execution_command_count": {
                "type": "integer",
                "minimum": 0,
            },
            "llm_route_planner_residual_goal_context_count": {
                "type": "integer",
                "minimum": 0,
            },
            "llm_route_planner_residual_goal_context_residual_goals": string_array,
            "llm_route_planner_residual_goal_context_source_ref_count": {
                "type": "integer",
                "minimum": 0,
            },
            "llm_route_planner_residual_goal_context_provenance_count": {
                "type": "integer",
                "minimum": 0,
            },
            "llm_route_planner_residual_goals_with_context_count": {
                "type": "integer",
                "minimum": 0,
            },
            "llm_route_planner_residual_goals_without_context": string_array,
            "llm_route_planner_route_option_selection_brief_present": {
                "type": "boolean"
            },
            "llm_route_planner_route_option_selection_candidate_count": {
                "type": "integer",
                "minimum": 0,
            },
            "llm_route_planner_route_option_selection_candidate_primitive_count": {
                "type": "integer",
                "minimum": 0,
            },
            "llm_route_planner_route_option_selection_candidates_with_residual_goals": {
                "type": "integer",
                "minimum": 0,
            },
            "llm_route_planner_route_option_selection_candidate_residual_goal_count": {
                "type": "integer",
                "minimum": 0,
            },
            "llm_route_planner_route_option_selection_lower_bound_selected_route_option_id": {
                "type": "string"
            },
            "llm_route_planner_route_option_selected_route_option_id": {
                "type": "string"
            },
            "llm_route_planner_route_option_selection_lower_bound_residual_goal_count": {
                "type": "integer",
                "minimum": 0,
            },
            "llm_route_planner_route_option_selection_minimal_delta_selected_residual_goal_count": {
                "type": "integer",
                "minimum": 0,
            },
            "llm_route_planner_route_option_selection_lower_bound_matches_minimal_delta": {
                "type": "boolean"
            },
            "llm_route_planner_route_option_selected_matches_lower_bound": {
                "type": "boolean"
            },
            "llm_route_planner_route_option_selected_matches_minimal_delta": {
                "type": "boolean"
            },
            "llm_route_planner_route_adoption_status": {"type": "string"},
            "llm_route_planner_route_adoption_blockers": (
                route_adoption_blocker_array
            ),
            "llm_route_planner_primitive_evidence_matrix_witness_present": {
                "type": "boolean"
            },
            "llm_route_planner_primitive_evidence_matrix_accounting_complete": {
                "type": "boolean"
            },
            "llm_route_planner_primitive_evidence_matrix_repair_obligation_count": {
                "type": "integer",
                "minimum": 0,
            },
            "llm_route_planner_primitive_evidence_matrix_unaccounted_primitive_count": {
                "type": "integer",
                "minimum": 0,
            },
            "llm_route_planner_primitive_evidence_matrix_selected_without_matrix_row_count": {
                "type": "integer",
                "minimum": 0,
            },
            "llm_route_planner_primitive_evidence_matrix_source_backed_missing_response_source_snippet_count": {
                "type": "integer",
                "minimum": 0,
            },
            "llm_route_planner_primitive_evidence_matrix_formal_supported_missing_reuse_count": {
                "type": "integer",
                "minimum": 0,
            },
            "llm_route_planner_primitive_evidence_matrix_delta_needed_missing_accounting_count": {
                "type": "integer",
                "minimum": 0,
            },
            "llm_route_planner_route_adoption_preconditions": {"type": "object"},
            "llm_route_planner_route_adoption_precondition_present": {
                "type": "boolean"
            },
            "llm_route_planner_route_adoption_precondition_blocked_before_response": {
                "type": "boolean"
            },
            "llm_route_planner_route_adoption_precondition_known_blockers": (
                route_adoption_blocker_array
            ),
            "llm_route_planner_route_adoption_precondition_required_response_fields": (
                string_array
            ),
            "llm_route_planner_route_adoption_precondition_target_primitives": (
                string_array
            ),
            "llm_route_planner_route_adoption_precondition_known_blocker_count": {
                "type": "integer",
                "minimum": 0,
            },
            "llm_route_planner_route_adoption_precondition_required_response_field_count": {
                "type": "integer",
                "minimum": 0,
            },
            "llm_route_planner_route_adoption_precondition_target_primitive_count": {
                "type": "integer",
                "minimum": 0,
            },
            "llm_route_planner_acceptance_status": {"type": "string"},
            "llm_route_planner_model_selection_rationale": {"type": "string"},
            "llm_route_planner_has_generator_metadata": {"type": "boolean"},
            "llm_route_planner_generator_metadata_keys": string_array,
            "llm_route_planner_has_provider_usage": {"type": "boolean"},
            "llm_route_planner_provider_input_tokens": {
                "type": "integer",
                "minimum": 0,
            },
            "llm_route_planner_provider_output_tokens": {
                "type": "integer",
                "minimum": 0,
            },
            "llm_route_planner_provider_cache_creation_input_tokens": {
                "type": "integer",
                "minimum": 0,
            },
            "llm_route_planner_provider_cache_read_input_tokens": {
                "type": "integer",
                "minimum": 0,
            },
            "llm_route_planner_provider_total_tokens": {
                "type": "integer",
                "minimum": 0,
            },
            "llm_route_planner_request_contract_blocked": {"type": "boolean"},
            "llm_route_planner_errors": string_array,
            "llm_route_planner_generation_errors": string_array,
            "quality_controls_present": {"type": "boolean"},
            "quality_controls": {"type": "object"},
            "quality_control_fields": string_array,
            "quality_control_resource_contract_ids": string_array,
            "quality_control_response_validation_signals": string_array,
            "quality_control_stop_conditions": string_array,
            "portable_schema_id": {"type": "string", "minLength": 1},
            "proof_evidence_boundary_ok": {"type": "boolean"},
            "kernel_verified_ground_truth": {"type": "boolean"},
            "kernel_verification_witnesses": object_array,
            "proof_evidence_status": {"const": PROOF_EVIDENCE_STATUS},
            "proof_evidence_boundary": {
                "type": "string",
                "pattern": "not theorem proof evidence",
            },
            "ok": {"type": "boolean"},
            "errors": string_array,
        },
    }


def validate_evaluation_row(
    row: dict[str, Any],
    schema: dict[str, object] | None = None,
) -> tuple[str, ...]:
    row_schema = schema or evaluation_row_json_schema()
    if not isinstance(row, dict):
        return ("evaluation row must be object",)
    errors: list[str] = []
    required = row_schema.get("required", [])
    if isinstance(required, list):
        for field_name in required:
            if isinstance(field_name, str) and field_name not in row:
                errors.append(f"{field_name} required")
    properties = row_schema.get("properties", {})
    if isinstance(properties, dict):
        for field_name, field_schema in properties.items():
            if not isinstance(field_name, str) or field_name not in row:
                continue
            if isinstance(field_schema, dict):
                errors.extend(_schema_property_errors(field_name, row[field_name], field_schema))
    return tuple(errors)


def _evaluate_row(
    row: dict[str, Any],
    truth_index: dict[str, dict[str, Any]],
    plan_payload: dict[str, Any],
) -> FormalizationGapPlannerEvaluationRow:
    errors: list[str] = []
    row = _row_with_manifest_target(row, plan_payload)
    goal_plan_id = str(row.get("goal_plan_id", ""))
    route_id = str(row.get("route_id", ""))
    display_name = str(row.get("display_name", ""))
    truth, match_key = _match_truth(goal_plan_id, route_id, display_name, truth_index)

    predicted_route = _predicted_route_primitives(row)
    truth_route = _truth_route_primitives(truth)
    route_tp = tuple(sorted(set(predicted_route) & set(truth_route)))
    route_missing = tuple(sorted(set(truth_route) - set(predicted_route)))
    route_extra = tuple(sorted(set(predicted_route) - set(truth_route)))

    predicted_delta = _node_primitives(row.get("minimal_additional_formalization_nodes", []))
    truth_delta = _truth_delta_primitives(truth)
    delta_tp = tuple(sorted(set(predicted_delta) & set(truth_delta)))
    delta_unnecessary = tuple(sorted(set(predicted_delta) - set(truth_delta)))
    delta_missing = tuple(sorted(set(truth_delta) - set(predicted_delta)))

    predicted_residual_goals = _predicted_residual_goals(row)
    truth_residual_goals = _truth_residual_goals(truth)
    predicted_residual = _predicted_residual_primitives(
        row,
        predicted_route,
        predicted_residual_goals,
    )
    truth_residual = _truth_residual_primitives(truth)
    residual_tp = tuple(sorted(set(predicted_residual) & set(truth_residual)))
    residual_missing = tuple(sorted(set(truth_residual) - set(predicted_residual)))
    residual_extra = tuple(sorted(set(predicted_residual) - set(truth_residual)))

    predicted_existing = _node_primitives(row.get("existing_reuse_nodes", []))
    truth_existing = _str_tuple(truth.get("actual_existing_reuse_primitives", []))
    existing_tp = set(predicted_existing) & set(truth_existing)

    coverage_accuracy, coverage_checked, coverage_confusions = _coverage_accuracy(row, truth)
    two_dag_ok = bool(row.get("informal_knowledge_dag_nodes")) and bool(
        _formal_realization_nodes(row)
    )
    alignment_ok, alignment_coverage, aligned, unaligned = _alignment_contract(row)
    feedback_ready = _feedback_loop_ready(row)
    cost_graph_trace = _minimal_delta_cost_graph_trace(row)
    realization_trace = _realization_coverage_witness_trace(row)
    llm_trace = _llm_route_planner_trace(
        row,
        predicted_residual_goals=predicted_residual_goals,
        minimal_delta_selected_route_option_id=str(
            cost_graph_trace["selected_route_option_id"]
        ),
    )
    quality_trace = _quality_control_trace(row)
    portable_schema_id = str(plan_payload.get("portable_schema_id", ""))
    proof_boundary_ok = "not theorem proof evidence" in str(
        row.get("proof_evidence_boundary", "")
    )
    if plan_payload.get("component_name") != LIBRARY_AWARE_FORMALIZATION_GAP_PLANNER_NAME:
        errors.append("evaluated manifest is not the library-aware planner component")
    if portable_schema_id != PORTABLE_FORMALIZATION_GAP_PLAN_SCHEMA_ID:
        errors.append("portable schema id mismatch")
    if not two_dag_ok:
        errors.append("two-DAG contract is incomplete")
    if not alignment_ok:
        errors.append("route alignment contract is incomplete")
    if not feedback_ready:
        errors.append("feedback-loop hooks are incomplete")
    if not proof_boundary_ok:
        errors.append("proof evidence boundary is missing")

    return FormalizationGapPlannerEvaluationRow(
        schema_version=FORMALIZATION_GAP_PLANNER_EVALUATION_SCHEMA_VERSION,
        evaluation_id="formalization_gap_planner_evaluation:"
        + stable_hash([goal_plan_id, route_id, match_key])[:16],
        goal_plan_id=goal_plan_id,
        route_id=route_id,
        display_name=display_name,
        matched_ground_truth=bool(truth),
        match_key=match_key,
        predicted_route_primitives=predicted_route,
        ground_truth_route_primitives=truth_route,
        route_true_positive_primitives=route_tp,
        route_missing_primitives=route_missing,
        route_extra_primitives=route_extra,
        route_recall=_ratio(len(route_tp), len(truth_route), empty_value=1.0),
        route_precision=_ratio(len(route_tp), len(predicted_route), empty_value=1.0),
        predicted_delta_primitives=predicted_delta,
        ground_truth_delta_primitives=truth_delta,
        delta_true_positive_primitives=delta_tp,
        delta_unnecessary_primitives=delta_unnecessary,
        delta_missing_primitives=delta_missing,
        delta_precision=_ratio(len(delta_tp), len(predicted_delta), empty_value=1.0),
        delta_recall=_ratio(len(delta_tp), len(truth_delta), empty_value=1.0),
        predicted_residual_primitives=predicted_residual,
        ground_truth_residual_primitives=truth_residual,
        residual_true_positive_primitives=residual_tp,
        residual_missing_primitives=residual_missing,
        residual_extra_primitives=residual_extra,
        residual_precision=_ratio(
            len(residual_tp),
            len(predicted_residual),
            empty_value=1.0,
        ),
        residual_recall=_ratio(
            len(residual_tp),
            len(truth_residual),
            empty_value=1.0,
        ),
        predicted_residual_goals=predicted_residual_goals,
        ground_truth_residual_goals=truth_residual_goals,
        predicted_existing_reuse_primitives=predicted_existing,
        ground_truth_existing_reuse_primitives=truth_existing,
        existing_reuse_precision=_ratio(
            len(existing_tp),
            len(predicted_existing),
            empty_value=1.0,
        ),
        existing_reuse_recall=_ratio(
            len(existing_tp),
            len(truth_existing),
            empty_value=1.0,
        ),
        coverage_classification_accuracy=coverage_accuracy,
        n_coverage_classification_checked=coverage_checked,
        coverage_classification_confusions=coverage_confusions,
        two_dag_contract_ok=two_dag_ok,
        alignment_contract_ok=alignment_ok,
        alignment_coverage=alignment_coverage,
        aligned_primitives=aligned,
        unaligned_primitives=unaligned,
        feedback_loop_ready=feedback_ready,
        minimal_delta_cost_graph_present=bool(cost_graph_trace["present"]),
        minimal_delta_route_option_count=int(cost_graph_trace["route_option_count"]),
        minimal_delta_selected_route_option_id=str(
            cost_graph_trace["selected_route_option_id"]
        ),
        minimal_delta_selected_route_cost=float(
            cost_graph_trace["selected_route_cost"]
        ),
        realization_coverage_witness_present=bool(realization_trace["present"]),
        realization_coverage_complete=bool(realization_trace["complete"]),
        realization_missing_selected_formal_primitives=_str_tuple(
            realization_trace["missing_selected_formal_primitives"]
        ),
        realization_missing_delta_alignment_primitives=_str_tuple(
            realization_trace["missing_delta_alignment_primitives"]
        ),
        realization_cost_hint_baseline_primitives=_str_tuple(
            realization_trace["cost_hint_baseline_primitives"]
        ),
        realization_omitted_cost_hint_primitives=_str_tuple(
            realization_trace["omitted_cost_hint_primitives"]
        ),
        realization_cost_hint_baseline_coverage_complete=bool(
            realization_trace["cost_hint_baseline_coverage_complete"]
        ),
        llm_route_planner_trace_present=bool(llm_trace["trace_present"]),
        llm_route_planner_row_id=str(llm_trace["row_id"]),
        llm_route_planner_provider=str(llm_trace["provider"]),
        llm_route_planner_model=str(llm_trace["model"]),
        llm_route_planner_model_tier=str(llm_trace["model_tier"]),
        llm_route_planner_model_tier_decision_basis=str(
            llm_trace["model_tier_decision_basis"]
        ),
        llm_route_planner_model_tier_decision_sonnet_triggers=_str_tuple(
            llm_trace["model_tier_decision_sonnet_triggers"]
        ),
        llm_route_planner_model_tier_decision_sonnet_trigger_count=int(
            llm_trace["model_tier_decision_sonnet_trigger_count"]
        ),
        llm_route_planner_source_feedback_row_count=int(
            llm_trace["source_feedback_row_count"]
        ),
        llm_route_planner_source_feedback_unverified_semantic_primitive_row_count=int(
            llm_trace["source_feedback_unverified_semantic_primitive_row_count"]
        ),
        llm_route_planner_source_feedback_proof_body_execution_failure_count=int(
            llm_trace["source_feedback_proof_body_execution_failure_count"]
        ),
        llm_route_planner_source_feedback_formal_environment_blocker_count=int(
            llm_trace["source_feedback_formal_environment_blocker_count"]
        ),
        llm_route_planner_interactive_formal_attempt_queue_row_count=int(
            llm_trace["interactive_formal_attempt_queue_row_count"]
        ),
        llm_route_planner_interactive_formal_attempt_queue_item_count=int(
            llm_trace["interactive_formal_attempt_queue_item_count"]
        ),
        llm_route_planner_interactive_formal_attempt_queue_ready_item_count=int(
            llm_trace["interactive_formal_attempt_queue_ready_item_count"]
        ),
        llm_route_planner_interactive_formal_attempt_queue_blocked_item_count=int(
            llm_trace["interactive_formal_attempt_queue_blocked_item_count"]
        ),
        llm_route_planner_interactive_formal_attempt_queue_execution_command_count=int(
            llm_trace["interactive_formal_attempt_queue_execution_command_count"]
        ),
        llm_route_planner_residual_goal_context_count=int(
            llm_trace["residual_goal_context_count"]
        ),
        llm_route_planner_residual_goal_context_residual_goals=_str_tuple(
            llm_trace["residual_goal_context_residual_goals"]
        ),
        llm_route_planner_residual_goal_context_source_ref_count=int(
            llm_trace["residual_goal_context_source_ref_count"]
        ),
        llm_route_planner_residual_goal_context_provenance_count=int(
            llm_trace["residual_goal_context_provenance_count"]
        ),
        llm_route_planner_residual_goals_with_context_count=int(
            llm_trace["residual_goals_with_context_count"]
        ),
        llm_route_planner_residual_goals_without_context=_str_tuple(
            llm_trace["residual_goals_without_context"]
        ),
        llm_route_planner_route_option_selection_brief_present=bool(
            llm_trace["route_option_selection_brief_present"]
        ),
        llm_route_planner_route_option_selection_candidate_count=int(
            llm_trace["route_option_selection_candidate_count"]
        ),
        llm_route_planner_route_option_selection_candidate_primitive_count=int(
            llm_trace["route_option_selection_candidate_primitive_count"]
        ),
        llm_route_planner_route_option_selection_candidates_with_residual_goals=int(
            llm_trace[
                "route_option_selection_candidates_with_residual_goals"
            ]
        ),
        llm_route_planner_route_option_selection_candidate_residual_goal_count=int(
            llm_trace["route_option_selection_candidate_residual_goal_count"]
        ),
        llm_route_planner_route_option_selection_lower_bound_selected_route_option_id=str(
            llm_trace[
                "route_option_selection_lower_bound_selected_route_option_id"
            ]
        ),
        llm_route_planner_route_option_selected_route_option_id=str(
            llm_trace["route_option_selected_route_option_id"]
        ),
        llm_route_planner_route_option_selection_lower_bound_residual_goal_count=int(
            llm_trace[
                "route_option_selection_lower_bound_residual_goal_count"
            ]
        ),
        llm_route_planner_route_option_selection_minimal_delta_selected_residual_goal_count=int(
            llm_trace[
                "route_option_selection_minimal_delta_selected_residual_goal_count"
            ]
        ),
        llm_route_planner_route_option_selection_lower_bound_matches_minimal_delta=bool(
            llm_trace[
                "route_option_selection_lower_bound_matches_minimal_delta"
            ]
        ),
        llm_route_planner_route_option_selected_matches_lower_bound=bool(
            llm_trace["route_option_selected_matches_lower_bound"]
        ),
        llm_route_planner_route_option_selected_matches_minimal_delta=bool(
            llm_trace["route_option_selected_matches_minimal_delta"]
        ),
        llm_route_planner_route_adoption_status=str(
            llm_trace["route_adoption_status"]
        ),
        llm_route_planner_route_adoption_blockers=_str_tuple(
            llm_trace["route_adoption_blockers"]
        ),
        llm_route_planner_primitive_evidence_matrix_witness_present=bool(
            llm_trace["primitive_evidence_matrix_witness_present"]
        ),
        llm_route_planner_primitive_evidence_matrix_accounting_complete=bool(
            llm_trace["primitive_evidence_matrix_accounting_complete"]
        ),
        llm_route_planner_primitive_evidence_matrix_repair_obligation_count=int(
            llm_trace["primitive_evidence_matrix_repair_obligation_count"]
        ),
        llm_route_planner_primitive_evidence_matrix_unaccounted_primitive_count=int(
            llm_trace["primitive_evidence_matrix_unaccounted_primitive_count"]
        ),
        llm_route_planner_primitive_evidence_matrix_selected_without_matrix_row_count=int(
            llm_trace[
                "primitive_evidence_matrix_selected_without_matrix_row_count"
            ]
        ),
        llm_route_planner_primitive_evidence_matrix_source_backed_missing_response_source_snippet_count=int(
            llm_trace[
                "primitive_evidence_matrix_source_backed_missing_response_source_snippet_count"
            ]
        ),
        llm_route_planner_primitive_evidence_matrix_formal_supported_missing_reuse_count=int(
            llm_trace[
                "primitive_evidence_matrix_formal_supported_missing_reuse_count"
            ]
        ),
        llm_route_planner_primitive_evidence_matrix_delta_needed_missing_accounting_count=int(
            llm_trace[
                "primitive_evidence_matrix_delta_needed_missing_accounting_count"
            ]
        ),
        llm_route_planner_route_adoption_preconditions=dict(
            llm_trace["route_adoption_preconditions"]
        ),
        llm_route_planner_route_adoption_precondition_present=bool(
            llm_trace["route_adoption_precondition_present"]
        ),
        llm_route_planner_route_adoption_precondition_blocked_before_response=bool(
            llm_trace["route_adoption_precondition_blocked_before_response"]
        ),
        llm_route_planner_route_adoption_precondition_known_blockers=_str_tuple(
            llm_trace["route_adoption_precondition_known_blockers"]
        ),
        llm_route_planner_route_adoption_precondition_required_response_fields=(
            _str_tuple(
                llm_trace[
                    "route_adoption_precondition_required_response_fields"
                ]
            )
        ),
        llm_route_planner_route_adoption_precondition_target_primitives=(
            _str_tuple(
                llm_trace[
                    "route_adoption_precondition_target_primitives"
                ]
            )
        ),
        llm_route_planner_route_adoption_precondition_known_blocker_count=int(
            llm_trace["route_adoption_precondition_known_blocker_count"]
        ),
        llm_route_planner_route_adoption_precondition_required_response_field_count=int(
            llm_trace[
                "route_adoption_precondition_required_response_field_count"
            ]
        ),
        llm_route_planner_route_adoption_precondition_target_primitive_count=int(
            llm_trace[
                "route_adoption_precondition_target_primitive_count"
            ]
        ),
        llm_route_planner_acceptance_status=str(llm_trace["acceptance_status"]),
        llm_route_planner_model_selection_rationale=str(
            llm_trace["model_selection_rationale"]
        ),
        llm_route_planner_has_generator_metadata=bool(
            llm_trace["has_generator_metadata"]
        ),
        llm_route_planner_generator_metadata_keys=_str_tuple(
            llm_trace["generator_metadata_keys"]
        ),
        llm_route_planner_has_provider_usage=bool(
            llm_trace["has_provider_usage"]
        ),
        llm_route_planner_provider_input_tokens=int(
            llm_trace["provider_input_tokens"]
        ),
        llm_route_planner_provider_output_tokens=int(
            llm_trace["provider_output_tokens"]
        ),
        llm_route_planner_provider_cache_creation_input_tokens=int(
            llm_trace["provider_cache_creation_input_tokens"]
        ),
        llm_route_planner_provider_cache_read_input_tokens=int(
            llm_trace["provider_cache_read_input_tokens"]
        ),
        llm_route_planner_provider_total_tokens=int(
            llm_trace["provider_total_tokens"]
        ),
        llm_route_planner_request_contract_blocked=bool(
            llm_trace["request_contract_blocked"]
        ),
        llm_route_planner_errors=_str_tuple(llm_trace["errors"]),
        llm_route_planner_generation_errors=_str_tuple(
            llm_trace["generation_errors"]
        ),
        quality_controls_present=bool(quality_trace["present"]),
        quality_controls=quality_trace["quality_controls"],
        quality_control_fields=_str_tuple(quality_trace["fields"]),
        quality_control_resource_contract_ids=_str_tuple(
            quality_trace["resource_contract_ids"]
        ),
        quality_control_response_validation_signals=_str_tuple(
            quality_trace["response_validation_signals"]
        ),
        quality_control_stop_conditions=_str_tuple(
            quality_trace["stop_conditions"]
        ),
        portable_schema_id=portable_schema_id,
        proof_evidence_boundary_ok=proof_boundary_ok,
        kernel_verified_ground_truth=bool(truth.get("kernel_verified", False)),
        kernel_verification_witnesses=_truth_kernel_verification_witnesses(truth),
        proof_evidence_status=PROOF_EVIDENCE_STATUS,
        proof_evidence_boundary=PROOF_EVIDENCE_BOUNDARY,
        ok=not errors,
        errors=tuple(errors),
    )


def _predicted_route_primitives(row: dict[str, Any]) -> tuple[str, ...]:
    primitives = set(_str_tuple(row.get("selected_primitives", [])))
    primitives.update(_node_primitives(row.get("existing_reuse_nodes", [])))
    primitives.update(_node_primitives(row.get("minimal_additional_formalization_nodes", [])))
    return tuple(sorted(item for item in primitives if item))


def _truth_route_primitives(truth: dict[str, Any]) -> tuple[str, ...]:
    for field_name in ("required_primitives", "actual_dependencies", "route_primitives"):
        values = _str_tuple(truth.get(field_name, []))
        if values:
            return values
    return tuple()


def _truth_delta_primitives(truth: dict[str, Any]) -> tuple[str, ...]:
    explicit = _str_tuple(truth.get("actual_delta_primitives", []))
    if explicit:
        return explicit
    route = set(_truth_route_primitives(truth))
    existing = set(_str_tuple(truth.get("actual_existing_reuse_primitives", [])))
    return tuple(sorted(route - existing))


def _truth_residual_primitives(truth: dict[str, Any]) -> tuple[str, ...]:
    for field_name in (
        "expected_residual_primitives",
        "actual_residual_primitives",
        "residual_primitives",
        "expected_side_condition_primitives",
    ):
        values = _str_tuple(truth.get(field_name, []))
        if values:
            return values
    return tuple()


def _truth_residual_goals(truth: dict[str, Any]) -> tuple[str, ...]:
    for field_name in (
        "expected_residual_goals",
        "actual_residual_goals",
        "residual_goals",
        "expected_side_conditions",
    ):
        values = _str_tuple(truth.get(field_name, []))
        if values:
            return values
    return tuple()


def _truth_kernel_verification_witnesses(
    truth: dict[str, Any],
) -> tuple[dict[str, object], ...]:
    values = truth.get(
        "kernel_verification_witnesses",
        truth.get("kernel_verification_refs", truth.get("kernel_proof_witnesses", [])),
    )
    if isinstance(values, dict):
        values = [values]
    if not isinstance(values, (list, tuple)):
        return tuple()
    witnesses: list[dict[str, object]] = []
    for value in values:
        if isinstance(value, dict):
            witness = {
                str(key): value_item
                for key, value_item in value.items()
                if str(key)
            }
            if witness:
                witnesses.append(witness)
    return tuple(witnesses)


def _predicted_residual_primitives(
    row: dict[str, Any],
    predicted_route: tuple[str, ...],
    predicted_residual_goals: tuple[str, ...],
) -> tuple[str, ...]:
    explicit = _str_tuple(
        [
            *_str_tuple(row.get("predicted_residual_primitives", [])),
            *_str_tuple(row.get("residual_primitives", [])),
        ]
    )
    from_goals = _residual_primitives_from_texts(
        predicted_residual_goals,
        predicted_route,
    )
    return _str_tuple([*explicit, *from_goals])


def _predicted_residual_goals(row: dict[str, Any]) -> tuple[str, ...]:
    goals: list[str] = []
    goals.extend(_str_tuple(row.get("residual_goals", [])))
    goals.extend(_str_tuple(row.get("blocked_only_by", [])))
    trace = row.get("standalone_input_trace", {})
    if isinstance(trace, dict):
        goals.extend(_str_tuple(trace.get("residual_goals", [])))
        metadata = trace.get("replan_metadata", {})
        if isinstance(metadata, dict):
            goals.extend(_str_tuple(metadata.get("residual_goals", [])))
    for trigger in row.get("route_revision_triggers", []):
        if not isinstance(trigger, dict):
            continue
        if str(trigger.get("trigger_kind", "")) in {
            "blocked_by_formal_side_condition",
            "prover_feedback_residual",
            "proof_state_residual",
        }:
            goals.extend(
                _str_tuple(
                    [
                        trigger.get("condition", ""),
                        trigger.get("residual_goal", ""),
                    ]
                )
            )
    for node in _all_node_dicts(row):
        goals.extend(_str_tuple(node.get("side_conditions", [])))
        goals.extend(_str_tuple(node.get("blocked_reasons", [])))
    for packet in row.get("portable_work_packets", []):
        if not isinstance(packet, dict):
            continue
        goals.extend(_str_tuple(packet.get("residual_goals", [])))
        goals.extend(_str_tuple(packet.get("side_conditions", [])))
    return _str_tuple(goals)


def _residual_primitives_from_texts(
    texts: tuple[str, ...],
    candidate_primitives: tuple[str, ...],
) -> tuple[str, ...]:
    candidates = tuple(sorted(set(candidate_primitives), key=len, reverse=True))
    primitives: list[str] = []
    for text in texts:
        normalized = str(text)
        prefix = normalized.split(":", 1)[0].strip()
        if prefix and " " not in prefix and prefix in candidate_primitives:
            primitives.append(prefix)
        for primitive in candidates:
            if primitive and primitive in normalized:
                primitives.append(primitive)
    return _str_tuple(primitives)


def _coverage_accuracy(
    row: dict[str, Any],
    truth: dict[str, Any],
) -> tuple[float, int, tuple[dict[str, object], ...]]:
    truth_coverage = truth.get("coverage_by_primitive", {})
    if not isinstance(truth_coverage, dict):
        return 1.0, 0, tuple()
    predicted = _predicted_coverage_by_primitive(row)
    checked = 0
    correct = 0
    confusions: list[dict[str, object]] = []
    for primitive, expected_status_raw in truth_coverage.items():
        expected_status = _normalize_coverage_status(str(expected_status_raw))
        predicted_status = _normalize_coverage_status(predicted.get(str(primitive), ""))
        if not predicted_status:
            continue
        checked += 1
        if predicted_status == expected_status:
            correct += 1
        else:
            confusions.append(
                {
                    "primitive": str(primitive),
                    "expected": expected_status,
                    "predicted": predicted_status,
                }
            )
    return _ratio(correct, checked, empty_value=1.0), checked, tuple(confusions)


def _predicted_coverage_by_primitive(row: dict[str, Any]) -> dict[str, str]:
    coverage: dict[str, str] = {}
    for primitive in _node_primitives(row.get("existing_reuse_nodes", [])):
        coverage[primitive] = "exact_exists"
    for primitive in _node_primitives(row.get("wrapper_nodes", [])):
        coverage[primitive] = "wrapper_needed"
    for primitive in _node_primitives(row.get("bridge_nodes", [])):
        coverage[primitive] = "bridge_needed"
    for primitive in _node_primitives(row.get("source_discovery_nodes", [])):
        coverage[primitive] = "definition_missing"
    for primitive in _node_primitives(row.get("first_principles_nodes", [])):
        coverage[primitive] = "theory_missing"
    return coverage


def _all_node_dicts(row: dict[str, Any]) -> tuple[dict[str, Any], ...]:
    nodes: list[dict[str, Any]] = []
    for field_name in (
        "existing_reuse_nodes",
        "wrapper_nodes",
        "bridge_nodes",
        "source_discovery_nodes",
        "first_principles_nodes",
        "minimal_additional_formalization_nodes",
        "informal_knowledge_dag_nodes",
        "formal_realization_dag_nodes",
    ):
        for node in row.get(field_name, []):
            if isinstance(node, dict):
                nodes.append(node)
    if _is_lean_target_prover(row.get("target_prover_family", "")):
        for node in row.get("lean_realization_dag_nodes", []):
            if isinstance(node, dict):
                nodes.append(node)
    return tuple(nodes)


def _feedback_loop_ready(row: dict[str, Any]) -> bool:
    triggers = row.get("route_revision_triggers", [])
    hooks = row.get("interactive_refinement_hooks", [])
    hook_kinds = {
        str(item.get("hook_kind", ""))
        for item in hooks
        if isinstance(item, dict)
    }
    has_formal_grounding = bool(
        {"formal_library_grounding", "lean_library_grounding"} & hook_kinds
    )
    return (
        bool(triggers)
        and "literature_discovery" in hook_kinds
        and has_formal_grounding
        and "proof_state_feedback" in hook_kinds
    )


def _minimal_delta_cost_graph_trace(row: dict[str, Any]) -> dict[str, object]:
    trace = row.get("standalone_input_trace", {})
    trace = trace if isinstance(trace, dict) else {}
    graph = trace.get("minimal_delta_and_or_cost_graph", {})
    graph = graph if isinstance(graph, dict) else {}
    options = [
        option
        for option in graph.get("route_options", [])
        if isinstance(option, dict)
    ]
    selected_id = str(trace.get("minimal_delta_selected_route_option_id", "")).strip()
    selected_cost = trace.get("minimal_delta_selected_route_cost", 0.0)
    if not selected_id or not isinstance(selected_cost, (int, float)) or isinstance(selected_cost, bool):
        selected = {}
        graph_selected_id = str(graph.get("selected_route_option_id", "")).strip()
        for option in options:
            if bool(option.get("selected", False)):
                selected = option
                break
        if not selected and graph_selected_id:
            for option in options:
                if str(option.get("route_option_id", "")).strip() == graph_selected_id:
                    selected = option
                    break
        if selected:
            selected_id = str(selected.get("route_option_id", selected_id)).strip()
            selected_cost = selected.get("route_cost", selected_cost)
    if not isinstance(selected_cost, (int, float)) or isinstance(selected_cost, bool):
        selected_cost = 0.0
    count = trace.get("minimal_delta_route_option_count", len(options))
    if not isinstance(count, int) or isinstance(count, bool):
        count = len(options)
    return {
        "present": bool(
            trace.get("has_minimal_delta_and_or_cost_graph", False) or graph
        ),
        "route_option_count": max(0, count),
        "selected_route_option_id": selected_id,
        "selected_route_cost": max(0.0, float(selected_cost)),
    }


def _realization_coverage_witness_trace(row: dict[str, Any]) -> dict[str, object]:
    trace = row.get("standalone_input_trace", {})
    trace = trace if isinstance(trace, dict) else {}
    witness = trace.get("realization_coverage_witness", {})
    witness = witness if isinstance(witness, dict) else {}
    missing_selected = _str_tuple(
        trace.get(
            "realization_selected_primitives_missing_formal_realization",
            witness.get("selected_primitives_missing_formal_realization_node", []),
        )
    )
    missing_delta = _str_tuple(
        trace.get(
            "realization_delta_primitives_missing_route_alignment",
            witness.get("delta_primitives_missing_route_alignment_edge", []),
        )
    )
    return {
        "present": bool(
            trace.get("has_realization_coverage_witness", False) or witness
        ),
        "complete": bool(
            trace.get(
                "realization_coverage_complete",
                witness.get("realization_coverage_complete", False),
            )
        ),
        "missing_selected_formal_primitives": missing_selected,
        "missing_delta_alignment_primitives": missing_delta,
        "cost_hint_baseline_primitives": _str_tuple(
            witness.get("cost_hint_baseline_primitives", [])
        ),
        "omitted_cost_hint_primitives": _str_tuple(
            witness.get("omitted_cost_hint_primitives", [])
        ),
        "cost_hint_baseline_coverage_complete": bool(
            witness.get(
                "cost_hint_baseline_coverage_complete",
                not _str_tuple(witness.get("omitted_cost_hint_primitives", [])),
            )
        ),
    }


def _quality_control_trace(row: dict[str, Any]) -> dict[str, object]:
    trace = row.get("standalone_input_trace", {})
    trace = trace if isinstance(trace, dict) else {}
    replan_metadata = trace.get("replan_metadata", {})
    replan_metadata = replan_metadata if isinstance(replan_metadata, dict) else {}
    controls = _merge_quality_controls(
        _quality_controls_from_payload(replan_metadata.get("quality_controls", {})),
        _quality_controls_from_payload(trace.get("quality_controls", {})),
    )
    return {
        "present": bool(controls),
        "quality_controls": controls,
        "fields": tuple(sorted(controls)),
        "resource_contract_ids": controls.get("resource_contract_ids", tuple()),
        "response_validation_signals": controls.get(
            "response_validation_signals",
            tuple(),
        ),
        "stop_conditions": controls.get("stop_conditions", tuple()),
    }


def _quality_controls_from_payload(value: Any) -> dict[str, tuple[str, ...]]:
    if not isinstance(value, dict):
        return {}
    return {
        field_name: _str_tuple(value.get(field_name, []))
        for field_name in QUALITY_CONTROL_FIELDS
        if _str_tuple(value.get(field_name, []))
    }


def _merge_quality_controls(
    *controls: dict[str, tuple[str, ...]],
) -> dict[str, tuple[str, ...]]:
    merged: dict[str, list[str]] = {}
    for control in controls:
        if not isinstance(control, dict):
            continue
        for field_name in QUALITY_CONTROL_FIELDS:
            values = _str_tuple(control.get(field_name, []))
            if values:
                merged.setdefault(field_name, []).extend(values)
    return {
        field_name: _str_tuple(values)
        for field_name, values in merged.items()
        if _str_tuple(values)
    }


def _llm_route_planner_trace(
    row: dict[str, Any],
    *,
    predicted_residual_goals: tuple[str, ...] = (),
    minimal_delta_selected_route_option_id: str = "",
) -> dict[str, object]:
    trace = row.get("standalone_input_trace", {})
    trace = trace if isinstance(trace, dict) else {}
    generator_metadata = trace.get("llm_route_planner_generator_metadata", {})
    generator_metadata = generator_metadata if isinstance(generator_metadata, dict) else {}
    generator_keys = _str_tuple(
        trace.get("llm_route_planner_generator_metadata_keys", [])
    )
    if not generator_keys:
        generator_keys = tuple(sorted(str(key) for key in generator_metadata))
    provider_usage = _llm_provider_usage_from_trace(trace, generator_metadata)
    row_id = str(trace.get("llm_route_planner_row_id", "")).strip()
    provider = str(trace.get("llm_route_planner_provider", "")).strip()
    model = str(trace.get("llm_route_planner_model", "")).strip()
    model_tier = str(trace.get("llm_route_planner_model_tier", "")).strip()
    model_tier_decision_evidence = _dict_value(
        trace,
        "llm_route_planner_model_tier_decision_evidence",
    )
    route_signal_counts = _dict_value(
        model_tier_decision_evidence,
        "route_signal_counts",
    )
    source_feedback_counts = _dict_value(
        model_tier_decision_evidence,
        "source_theorem_feedback_counts",
    )
    sonnet_triggers = _str_tuple(
        trace.get(
            "llm_route_planner_model_tier_decision_sonnet_triggers",
            model_tier_decision_evidence.get("sonnet_triggers", []),
        )
    )
    route_adoption_status = str(
        trace.get("llm_route_planner_route_adoption_status", "")
    ).strip()
    route_adoption_preconditions = _dict_value(
        trace,
        "llm_route_planner_route_adoption_preconditions",
    )
    if not route_adoption_preconditions:
        route_adoption_preconditions = _dict_value(
            trace,
            "route_adoption_preconditions",
        )
    precondition_known_blockers = _str_tuple(
        route_adoption_preconditions.get("known_pre_response_blockers", [])
    )
    precondition_required_fields = _str_tuple(
        route_adoption_preconditions.get("response_required_fields", [])
    )
    precondition_target_primitives = _str_tuple(
        route_adoption_preconditions.get("target_primitives", [])
    )
    precondition_known_count = _int_value(
        route_adoption_preconditions.get(
            "n_known_pre_response_blockers",
            trace.get(
                "llm_route_adoption_precondition_blocker_count",
                len(precondition_known_blockers),
            ),
        )
    )
    if not precondition_known_count:
        precondition_known_count = len(precondition_known_blockers)
    precondition_required_count = _int_value(
        route_adoption_preconditions.get(
            "n_response_required_fields",
            trace.get(
                "llm_route_adoption_precondition_required_response_field_count",
                len(precondition_required_fields),
            ),
        )
    )
    if not precondition_required_count:
        precondition_required_count = len(precondition_required_fields)
    precondition_target_count = _int_value(
        route_adoption_preconditions.get(
            "n_target_primitives",
            trace.get(
                "llm_route_adoption_precondition_target_primitive_count",
                len(precondition_target_primitives),
            ),
        )
    )
    if not precondition_target_count:
        precondition_target_count = len(precondition_target_primitives)
    primitive_matrix_witness = _dict_value(
        trace,
        "llm_route_planner_primitive_evidence_matrix_witness",
    )
    matrix_unaccounted_primitives = _str_tuple(
        primitive_matrix_witness.get("matrix_unaccounted_primitives", [])
    )
    matrix_selected_without_row = _str_tuple(
        primitive_matrix_witness.get(
            "selected_primitives_without_matrix_row",
            [],
        )
    )
    matrix_source_missing = _str_tuple(
        primitive_matrix_witness.get(
            "source_backed_matrix_primitives_missing_response_source_snippet",
            [],
        )
    )
    matrix_formal_missing_reuse = _str_tuple(
        primitive_matrix_witness.get(
            "formal_supported_matrix_primitives_missing_reuse",
            [],
        )
    )
    matrix_delta_missing_accounting = _str_tuple(
        primitive_matrix_witness.get(
            "delta_needed_matrix_primitives_missing_accounting",
            [],
        )
    )
    matrix_unaccounted_count = _int_value(
        trace.get(
            "llm_route_planner_primitive_evidence_matrix_unaccounted_primitive_count",
            len(matrix_unaccounted_primitives),
        )
    )
    matrix_selected_without_count = _int_value(
        trace.get(
            "llm_route_planner_primitive_evidence_matrix_selected_without_matrix_row_count",
            len(matrix_selected_without_row),
        )
    )
    matrix_source_missing_count = _int_value(
        trace.get(
            "llm_route_planner_primitive_evidence_matrix_source_backed_missing_response_source_snippet_count",
            len(matrix_source_missing),
        )
    )
    matrix_formal_missing_reuse_count = _int_value(
        trace.get(
            "llm_route_planner_primitive_evidence_matrix_formal_supported_missing_reuse_count",
            len(matrix_formal_missing_reuse),
        )
    )
    matrix_delta_missing_accounting_count = _int_value(
        trace.get(
            "llm_route_planner_primitive_evidence_matrix_delta_needed_missing_accounting_count",
            len(matrix_delta_missing_accounting),
        )
    )
    matrix_repair_obligation_count = _int_value(
        trace.get(
            "llm_route_planner_primitive_evidence_matrix_repair_obligation_count",
            matrix_unaccounted_count
            + matrix_selected_without_count
            + matrix_source_missing_count
            + matrix_formal_missing_reuse_count
            + matrix_delta_missing_accounting_count,
        )
    )
    residual_goal_contexts = _llm_route_planner_residual_goal_contexts(row, trace)
    residual_context_goals = _residual_goal_context_goal_strings(
        residual_goal_contexts
    )
    residual_context_source_refs = _residual_goal_context_source_refs(
        residual_goal_contexts
    )
    residual_context_provenance = _residual_goal_context_provenance_values(
        residual_goal_contexts
    )
    residual_goals_with_context = _residual_goals_with_context(
        predicted_residual_goals,
        residual_context_goals,
    )
    residual_goals_without_context = tuple(
        goal
        for goal in predicted_residual_goals
        if goal not in set(residual_goals_with_context)
    )
    route_option_selection_trace = _llm_route_option_selection_brief_trace(
        trace,
        minimal_delta_selected_route_option_id=(
            minimal_delta_selected_route_option_id
        ),
    )
    return {
        "trace_present": bool(
            row_id
            or provider
            or model
            or model_tier
            or route_adoption_status
            or route_adoption_preconditions
            or provider_usage
            or residual_goal_contexts
            or route_option_selection_trace["route_option_selection_brief_present"]
            or route_option_selection_trace["route_option_selected_route_option_id"]
        ),
        "row_id": row_id,
        "provider": provider,
        "model": model,
        "model_tier": model_tier,
        "model_tier_decision_basis": str(
            trace.get(
                "llm_route_planner_model_tier_decision_basis",
                model_tier_decision_evidence.get("decision_basis", ""),
            )
        ).strip(),
        "model_tier_decision_sonnet_triggers": sonnet_triggers,
        "model_tier_decision_sonnet_trigger_count": _int_value(
            trace.get(
                "llm_route_planner_model_tier_decision_sonnet_trigger_count",
                len(sonnet_triggers),
            )
        ),
        "source_feedback_row_count": _int_value(
            trace.get(
                "llm_route_planner_source_feedback_row_count",
                source_feedback_counts.get(
                    "total_count",
                    route_signal_counts.get(
                        "source_theorem_feedback_row_count",
                        0,
                    ),
                ),
            )
        ),
        "source_feedback_unverified_semantic_primitive_row_count": _int_value(
            trace.get(
                "llm_route_planner_source_feedback_unverified_semantic_primitive_row_count",
                source_feedback_counts.get(
                    "unverified_semantic_primitive_row_count",
                    route_signal_counts.get(
                        "source_theorem_unverified_semantic_primitive_row_count",
                        0,
                    ),
                ),
            )
        ),
        "source_feedback_proof_body_execution_failure_count": _int_value(
            trace.get(
                "llm_route_planner_source_feedback_proof_body_execution_failure_count",
                source_feedback_counts.get(
                    "proof_body_execution_failure_count",
                    route_signal_counts.get(
                        "source_theorem_proof_body_execution_failure_count",
                        0,
                    ),
                ),
            )
        ),
        "source_feedback_formal_environment_blocker_count": _int_value(
            trace.get(
                "llm_route_planner_source_feedback_formal_environment_blocker_count",
                source_feedback_counts.get(
                    "formal_environment_blocker_count",
                    route_signal_counts.get(
                        "source_theorem_formal_environment_blocker_count",
                        0,
                    ),
                ),
            )
        ),
        "interactive_formal_attempt_queue_row_count": _int_value(
            trace.get(
                "llm_route_planner_interactive_formal_attempt_queue_row_count",
                route_signal_counts.get(
                    "interactive_session_formal_attempt_queue_row_count",
                    0,
                ),
            )
        ),
        "interactive_formal_attempt_queue_item_count": _int_value(
            trace.get(
                "llm_route_planner_interactive_formal_attempt_queue_item_count",
                route_signal_counts.get(
                    "interactive_session_formal_attempt_queue_item_count",
                    0,
                ),
            )
        ),
        "interactive_formal_attempt_queue_ready_item_count": _int_value(
            trace.get(
                "llm_route_planner_interactive_formal_attempt_queue_ready_item_count",
                route_signal_counts.get(
                    "interactive_session_formal_attempt_queue_ready_item_count",
                    0,
                ),
            )
        ),
        "interactive_formal_attempt_queue_blocked_item_count": _int_value(
            trace.get(
                "llm_route_planner_interactive_formal_attempt_queue_blocked_item_count",
                route_signal_counts.get(
                    "interactive_session_formal_attempt_queue_blocked_item_count",
                    0,
                ),
            )
        ),
        "interactive_formal_attempt_queue_execution_command_count": _int_value(
            trace.get(
                "llm_route_planner_interactive_formal_attempt_queue_execution_command_count",
                route_signal_counts.get(
                    "interactive_session_formal_attempt_queue_execution_command_count",
                    0,
                ),
            )
        ),
        "residual_goal_context_count": len(residual_goal_contexts),
        "residual_goal_context_residual_goals": residual_context_goals,
        "residual_goal_context_source_ref_count": len(residual_context_source_refs),
        "residual_goal_context_provenance_count": len(
            residual_context_provenance
        ),
        "residual_goals_with_context_count": len(residual_goals_with_context),
        "residual_goals_without_context": residual_goals_without_context,
        **route_option_selection_trace,
        "route_adoption_status": route_adoption_status,
        "route_adoption_blockers": _str_tuple(
            trace.get("llm_route_planner_route_adoption_blockers", [])
        ),
        "primitive_evidence_matrix_witness_present": bool(
            primitive_matrix_witness
            or trace.get("has_llm_route_planner_primitive_evidence_matrix_witness")
        ),
        "primitive_evidence_matrix_accounting_complete": bool(
            trace.get(
                "llm_route_planner_primitive_evidence_matrix_accounting_complete",
                primitive_matrix_witness.get("matrix_accounting_complete", False),
            )
        ),
        "primitive_evidence_matrix_repair_obligation_count": (
            matrix_repair_obligation_count
        ),
        "primitive_evidence_matrix_unaccounted_primitive_count": (
            matrix_unaccounted_count
        ),
        "primitive_evidence_matrix_selected_without_matrix_row_count": (
            matrix_selected_without_count
        ),
        "primitive_evidence_matrix_source_backed_missing_response_source_snippet_count": (
            matrix_source_missing_count
        ),
        "primitive_evidence_matrix_formal_supported_missing_reuse_count": (
            matrix_formal_missing_reuse_count
        ),
        "primitive_evidence_matrix_delta_needed_missing_accounting_count": (
            matrix_delta_missing_accounting_count
        ),
        "route_adoption_preconditions": route_adoption_preconditions,
        "route_adoption_precondition_present": bool(route_adoption_preconditions),
        "route_adoption_precondition_blocked_before_response": bool(
            route_adoption_preconditions.get("blocked_before_response", False)
        ),
        "route_adoption_precondition_known_blockers": precondition_known_blockers,
        "route_adoption_precondition_required_response_fields": (
            precondition_required_fields
        ),
        "route_adoption_precondition_target_primitives": (
            precondition_target_primitives
        ),
        "route_adoption_precondition_known_blocker_count": (
            precondition_known_count
        ),
        "route_adoption_precondition_required_response_field_count": (
            precondition_required_count
        ),
        "route_adoption_precondition_target_primitive_count": (
            precondition_target_count
        ),
        "acceptance_status": str(
            trace.get("llm_route_planner_acceptance_status", "")
        ).strip(),
        "model_selection_rationale": str(
            trace.get("llm_route_planner_model_selection_rationale", "")
        ).strip(),
        "has_generator_metadata": bool(
            trace.get("llm_route_planner_has_generator_metadata", False)
            or generator_metadata
        ),
        "generator_metadata_keys": generator_keys,
        "has_provider_usage": bool(provider_usage),
        "provider_input_tokens": provider_usage.get("input_tokens", 0),
        "provider_output_tokens": provider_usage.get("output_tokens", 0),
        "provider_cache_creation_input_tokens": provider_usage.get(
            "cache_creation_input_tokens",
            0,
        ),
        "provider_cache_read_input_tokens": provider_usage.get(
            "cache_read_input_tokens",
            0,
        ),
        "provider_total_tokens": provider_usage.get("total_tokens", 0),
        "request_contract_blocked": bool(
            trace.get("llm_route_planner_request_contract_blocked", False)
        ),
        "errors": _str_tuple(trace.get("llm_route_planner_errors", [])),
        "generation_errors": _str_tuple(
            trace.get("llm_route_planner_generation_errors", [])
        ),
    }


def _llm_route_option_selection_brief_trace(
    trace: dict[str, Any],
    *,
    minimal_delta_selected_route_option_id: str = "",
) -> dict[str, object]:
    brief = _dict_value(
        trace,
        "llm_route_planner_route_option_selection_brief",
    )
    if not brief:
        brief = _dict_value(trace, "route_option_selection_brief")
    candidates = _dict_tuple(brief.get("candidate_route_options", []))
    candidate_count = _int_value(
        brief.get("n_candidate_route_options", len(candidates))
    )
    if not candidate_count and candidates:
        candidate_count = len(candidates)
    candidate_primitive_count = _int_value(
        brief.get(
            "n_candidate_route_option_primitives",
            sum(
                _int_value(option.get("n_selected_primitives", 0))
                for option in candidates
            ),
        )
    )
    candidates_with_residual_goals = _int_value(
        brief.get(
            "n_candidate_route_options_with_residual_goals",
            sum(
                1
                for option in candidates
                if _int_value(option.get("n_residual_goals", 0)) > 0
            ),
        )
    )
    candidate_residual_goal_count = _int_value(
        brief.get(
            "n_candidate_route_option_residual_goals",
            sum(
                _int_value(option.get("n_residual_goals", 0))
                for option in candidates
            ),
        )
    )
    lower_bound_selected_id = str(
        brief.get("lower_bound_selected_route_option_id", "")
    ).strip()
    metadata = _dict_value(trace, "replan_metadata")
    route_option_selected_id = str(
        trace.get(
            "llm_route_planner_route_option_selected_route_option_id",
            metadata.get(
                "llm_route_planner_route_option_selected_route_option_id",
                "",
            ),
        )
        or ""
    ).strip()
    lower_bound_residual_goal_count = _int_value(
        brief.get("lower_bound_selected_residual_goal_count", 0)
    )
    minimal_delta_selected_id = str(
        minimal_delta_selected_route_option_id or ""
    ).strip()
    minimal_delta_selected_residual_goal_count = 0
    for option in candidates:
        if (
            str(option.get("route_option_id", "")).strip()
            == minimal_delta_selected_id
        ):
            minimal_delta_selected_residual_goal_count = _int_value(
                option.get("n_residual_goals", 0)
            )
            break
    return {
        "route_option_selection_brief_present": bool(brief),
        "route_option_selection_candidate_count": candidate_count,
        "route_option_selection_candidate_primitive_count": (
            candidate_primitive_count
        ),
        "route_option_selection_candidates_with_residual_goals": (
            candidates_with_residual_goals
        ),
        "route_option_selection_candidate_residual_goal_count": (
            candidate_residual_goal_count
        ),
        "route_option_selection_lower_bound_selected_route_option_id": (
            lower_bound_selected_id
        ),
        "route_option_selected_route_option_id": route_option_selected_id,
        "route_option_selection_lower_bound_residual_goal_count": (
            lower_bound_residual_goal_count
        ),
        "route_option_selection_minimal_delta_selected_residual_goal_count": (
            minimal_delta_selected_residual_goal_count
        ),
        "route_option_selection_lower_bound_matches_minimal_delta": bool(
            lower_bound_selected_id
            and minimal_delta_selected_id
            and lower_bound_selected_id == minimal_delta_selected_id
        ),
        "route_option_selected_matches_lower_bound": bool(
            route_option_selected_id
            and lower_bound_selected_id
            and route_option_selected_id == lower_bound_selected_id
        ),
        "route_option_selected_matches_minimal_delta": bool(
            route_option_selected_id
            and minimal_delta_selected_id
            and route_option_selected_id == minimal_delta_selected_id
        ),
    }


def _llm_route_planner_residual_goal_contexts(
    row: dict[str, Any],
    trace: dict[str, Any],
) -> tuple[dict[str, object], ...]:
    contexts: list[dict[str, object]] = []
    metadata = _dict_value(trace, "replan_metadata")
    row_metadata = _dict_value(row, "replan_metadata")
    for source in (
        trace.get("residual_goal_context", {}),
        *_dict_tuple(trace.get("residual_goal_contexts", [])),
        *_dict_tuple(trace.get("llm_route_planner_residual_goal_contexts", [])),
        *_dict_tuple(metadata.get("residual_goal_contexts", [])),
        *_dict_tuple(metadata.get("llm_route_planner_residual_goal_contexts", [])),
        row.get("residual_goal_context", {}),
        *_dict_tuple(row.get("residual_goal_contexts", [])),
        *_dict_tuple(row.get("llm_route_planner_residual_goal_contexts", [])),
        *_dict_tuple(row_metadata.get("residual_goal_contexts", [])),
        *_dict_tuple(row_metadata.get("llm_route_planner_residual_goal_contexts", [])),
    ):
        context = _residual_goal_context_value(source)
        if context:
            contexts.append(context)
    seen: set[str] = set()
    deduped: list[dict[str, object]] = []
    for context in contexts:
        key = stable_hash(context)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(context)
    return tuple(deduped)


def _residual_goal_context_value(value: Any) -> dict[str, object]:
    if not isinstance(value, dict):
        return {}
    context: dict[str, object] = dict(value)
    for field_name in (
        "residual_goals",
        "residual_primitives",
        "target_primitives",
        "source_refs",
        "queries",
        "source_search_queries",
        "literature_queries",
        "evidence_ids",
        "residual_evidence_ids",
        "refinement_evidence_ids",
        "prover_attempt_ids",
        "resource_response_ledger_ids",
        "resource_request_ids",
        "applied_refinement_evidence_ids",
        "applied_prover_diagnostic_signatures",
    ):
        if field_name in context:
            context[field_name] = _str_tuple(context.get(field_name, []))
    if "source_snippets" in context:
        context["source_snippets"] = _dict_tuple(context.get("source_snippets", []))
    for field_name in (
        "source_kind",
        "residual_goal",
        "interpretation",
        "route_repair",
        "repair_action",
        "source_search_status",
        "formal_gap_boundary",
        "resource_response_ledger_id",
        "resource_request_id",
        "refinement_evidence_id",
        "prover_attempt_id",
        "diagnostic_signature",
        "residual_diagnostic_signature",
        "provider_diagnostic_signature",
        "prover_diagnostic_signature",
    ):
        if field_name in context:
            context[field_name] = str(context.get(field_name, "") or "")
    return context


def _residual_goal_context_goal_strings(
    contexts: tuple[dict[str, object], ...],
) -> tuple[str, ...]:
    goals: list[str] = []
    for context in contexts:
        goals.extend(_str_tuple(context.get("residual_goal", "")))
        goals.extend(_str_tuple(context.get("residual_goals", [])))
    return _str_tuple(goals)


def _residual_goal_context_source_refs(
    contexts: tuple[dict[str, object], ...],
) -> tuple[str, ...]:
    refs: list[str] = []
    for context in contexts:
        refs.extend(_source_refs(context))
        refs.extend(_source_refs_from_snippets(context.get("source_snippets", [])))
    return _str_tuple(refs)


def _residual_goal_context_provenance_values(
    contexts: tuple[dict[str, object], ...],
) -> tuple[str, ...]:
    provenance: list[str] = []
    for context in contexts:
        for field_name in (
            "evidence_ids",
            "residual_evidence_ids",
            "refinement_evidence_ids",
            "prover_attempt_ids",
            "resource_response_ledger_ids",
            "resource_request_ids",
            "applied_refinement_evidence_ids",
            "applied_prover_diagnostic_signatures",
        ):
            provenance.extend(_str_tuple(context.get(field_name, [])))
        for field_name in (
            "resource_response_ledger_id",
            "resource_request_id",
            "refinement_evidence_id",
            "prover_attempt_id",
            "diagnostic_signature",
            "residual_diagnostic_signature",
            "provider_diagnostic_signature",
            "prover_diagnostic_signature",
        ):
            provenance.extend(_str_tuple(context.get(field_name, "")))
    return _str_tuple(provenance)


def _residual_goals_with_context(
    residual_goals: tuple[str, ...],
    context_goals: tuple[str, ...],
) -> tuple[str, ...]:
    context_keys = {_residual_goal_key(goal) for goal in context_goals}
    context_prefixes = {_residual_goal_prefix(goal) for goal in context_goals}
    matched: list[str] = []
    for goal in residual_goals:
        key = _residual_goal_key(goal)
        prefix = _residual_goal_prefix(goal)
        if key in context_keys or (prefix and prefix in context_prefixes):
            matched.append(goal)
    return _str_tuple(matched)


def _residual_goal_key(value: str) -> str:
    return " ".join(str(value or "").strip().lower().split())


def _residual_goal_prefix(value: str) -> str:
    return _residual_goal_key(str(value or "").split(":", 1)[0])


def _source_refs(node: dict[str, object]) -> tuple[str, ...]:
    refs: list[str] = []
    for field_name in ("source_refs", "source_ref", "source_gap_ids", "source_task_ids"):
        refs.extend(_str_tuple(node.get(field_name, [])))
    return _str_tuple(refs)


def _source_refs_from_snippets(value: Any) -> tuple[str, ...]:
    refs: list[str] = []
    for snippet in _dict_tuple(value):
        refs.extend(_source_refs(snippet))
    return _str_tuple(refs)


def _llm_provider_usage_from_trace(
    trace: dict[str, Any],
    generator_metadata: dict[str, Any],
) -> dict[str, int]:
    usage = _dict_value(trace, "llm_route_planner_provider_usage")
    if not usage:
        usage = _dict_value(trace, "provider_usage")
    if not usage:
        usage = _dict_value(generator_metadata, "provider_usage")
    if not usage:
        usage = {
            "input_tokens": trace.get(
                "llm_route_planner_provider_input_tokens",
                trace.get("provider_input_tokens", 0),
            ),
            "output_tokens": trace.get(
                "llm_route_planner_provider_output_tokens",
                trace.get("provider_output_tokens", 0),
            ),
            "cache_creation_input_tokens": trace.get(
                "llm_route_planner_provider_cache_creation_input_tokens",
                trace.get("provider_cache_creation_input_tokens", 0),
            ),
            "cache_read_input_tokens": trace.get(
                "llm_route_planner_provider_cache_read_input_tokens",
                trace.get("provider_cache_read_input_tokens", 0),
            ),
            "total_tokens": trace.get(
                "llm_route_planner_provider_total_tokens",
                trace.get("provider_total_tokens", 0),
            ),
        }
    return _llm_provider_usage_from_mapping(usage)


def _llm_provider_usage_from_mapping(usage: dict[str, Any]) -> dict[str, int]:
    input_tokens = _nonnegative_int(
        usage.get("input_tokens", usage.get("prompt_tokens", 0))
    )
    output_tokens = _nonnegative_int(
        usage.get("output_tokens", usage.get("completion_tokens", 0))
    )
    cache_creation_tokens = _nonnegative_int(
        usage.get("cache_creation_input_tokens", 0)
    )
    cache_read_tokens = _nonnegative_int(usage.get("cache_read_input_tokens", 0))
    total_tokens = _nonnegative_int(usage.get("total_tokens", 0))
    if total_tokens == 0:
        total_tokens = (
            input_tokens
            + output_tokens
            + cache_creation_tokens
            + cache_read_tokens
        )
    parsed = {
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "cache_creation_input_tokens": cache_creation_tokens,
        "cache_read_input_tokens": cache_read_tokens,
        "total_tokens": total_tokens,
    }
    if not any(parsed.values()):
        return {}
    return parsed


def _llm_provider_usage_rows(
    rows: list[FormalizationGapPlannerEvaluationRow],
) -> tuple[dict[str, object], ...]:
    usage_rows: list[dict[str, object]] = []
    for row in rows:
        if not row.llm_route_planner_has_provider_usage:
            continue
        usage_row = {
            "usage_row_id": (
                "formalization_gap_planner_evaluation_llm_provider_usage:"
                + stable_hash(
                    [
                        row.evaluation_id,
                        row.goal_plan_id,
                        row.route_id,
                        row.llm_route_planner_row_id,
                        row.llm_route_planner_provider,
                        row.llm_route_planner_model,
                        row.llm_route_planner_model_tier,
                        row.llm_route_planner_provider_total_tokens,
                    ]
                )[:20]
            ),
            "evaluation_id": row.evaluation_id,
            "goal_plan_id": row.goal_plan_id,
            "route_id": row.route_id,
            "display_name": row.display_name,
            "llm_route_planner_row_id": row.llm_route_planner_row_id,
            "provider_name": row.llm_route_planner_provider,
            "model": row.llm_route_planner_model,
            "model_tier": row.llm_route_planner_model_tier,
            "matched_ground_truth": row.matched_ground_truth,
            "ok": row.ok,
            "route_recall": row.route_recall,
            "delta_precision": row.delta_precision,
            "route_adoption_status": row.llm_route_planner_route_adoption_status,
            "input_tokens": row.llm_route_planner_provider_input_tokens,
            "output_tokens": row.llm_route_planner_provider_output_tokens,
            "cache_creation_input_tokens": (
                row.llm_route_planner_provider_cache_creation_input_tokens
            ),
            "cache_read_input_tokens": (
                row.llm_route_planner_provider_cache_read_input_tokens
            ),
            "total_tokens": row.llm_route_planner_provider_total_tokens,
            "proof_evidence_status": PROOF_EVIDENCE_STATUS,
            "proof_evidence_boundary": PROOF_EVIDENCE_BOUNDARY,
        }
        usage_rows.append(usage_row)
    return tuple(usage_rows)


def _llm_provider_usage_summary(
    usage_rows: tuple[dict[str, object], ...],
) -> dict[str, object]:
    by_provider: dict[str, dict[str, int]] = {}
    by_model_tier: dict[str, dict[str, int]] = {}
    by_model: dict[str, dict[str, int]] = {}
    totals = _empty_provider_usage_bucket()
    for row in usage_rows:
        _add_provider_usage_to_bucket(totals, row)
        _add_provider_usage_to_bucket(
            by_provider.setdefault(
                str(row.get("provider_name", "") or "unknown"),
                _empty_provider_usage_bucket(),
            ),
            row,
        )
        _add_provider_usage_to_bucket(
            by_model_tier.setdefault(
                str(row.get("model_tier", "") or "unknown"),
                _empty_provider_usage_bucket(),
            ),
            row,
        )
        _add_provider_usage_to_bucket(
            by_model.setdefault(
                str(row.get("model", "") or "unknown"),
                _empty_provider_usage_bucket(),
            ),
            row,
        )
    return {
        "summary_kind": (
            "formalization_gap_planner_evaluation_llm_provider_usage_summary"
        ),
        "row_count": len(usage_rows),
        **totals,
        "by_provider": dict(sorted(by_provider.items())),
        "by_model_tier": dict(sorted(by_model_tier.items())),
        "by_model": dict(sorted(by_model.items())),
        "usage_boundary": (
            "Provider token usage is runtime/cost accounting metadata, not "
            "mathematical or theorem proof evidence."
        ),
        "proof_evidence_status": PROOF_EVIDENCE_STATUS,
        "proof_evidence_boundary": PROOF_EVIDENCE_BOUNDARY,
    }


def _empty_provider_usage_bucket() -> dict[str, int]:
    return {
        "n_rows": 0,
        "input_tokens": 0,
        "output_tokens": 0,
        "cache_creation_input_tokens": 0,
        "cache_read_input_tokens": 0,
        "total_tokens": 0,
    }


def _add_provider_usage_to_bucket(
    bucket: dict[str, int],
    row: dict[str, object],
) -> None:
    bucket["n_rows"] = int(bucket.get("n_rows", 0) or 0) + 1
    for key in (
        "input_tokens",
        "output_tokens",
        "cache_creation_input_tokens",
        "cache_read_input_tokens",
        "total_tokens",
    ):
        bucket[key] = int(bucket.get(key, 0) or 0) + _nonnegative_int(row.get(key))


def _llm_route_adoption_status_summary(
    rows: list[FormalizationGapPlannerEvaluationRow],
) -> dict[str, dict[str, object]]:
    by_status = Counter(
        row.llm_route_planner_route_adoption_status
        for row in rows
        if row.llm_route_planner_route_adoption_status
    )
    return {
        status: {
            "n_rows": by_status[status],
            "n_ok": sum(
                1
                for row in rows
                if row.llm_route_planner_route_adoption_status == status and row.ok
            ),
            "n_matched_ground_truth": sum(
                1
                for row in rows
                if row.llm_route_planner_route_adoption_status == status
                and row.matched_ground_truth
            ),
            "n_route_adoption_blockers": sum(
                len(row.llm_route_planner_route_adoption_blockers)
                for row in rows
                if row.llm_route_planner_route_adoption_status == status
            ),
            "mean_route_recall": _mean(
                row.route_recall
                for row in rows
                if row.llm_route_planner_route_adoption_status == status
                and row.matched_ground_truth
            ),
            "mean_delta_precision": _mean(
                row.delta_precision
                for row in rows
                if row.llm_route_planner_route_adoption_status == status
                and row.matched_ground_truth
            ),
        }
        for status in sorted(by_status)
    }


def _llm_route_adoption_blocker_counts(
    rows: list[FormalizationGapPlannerEvaluationRow],
) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for row in rows:
        counts.update(row.llm_route_planner_route_adoption_blockers)
    return dict(sorted(counts.items()))


def _llm_route_adoption_blocker_summary(
    rows: list[FormalizationGapPlannerEvaluationRow],
) -> dict[str, dict[str, object]]:
    counts = _llm_route_adoption_blocker_counts(rows)
    return {
        blocker: {
            "n_rows": len(blocker_rows),
            "n_blocker_occurrences": counts[blocker],
            "n_ok": sum(1 for row in blocker_rows if row.ok),
            "n_matched_ground_truth": sum(
                1 for row in blocker_rows if row.matched_ground_truth
            ),
            "by_route_adoption_status": dict(
                sorted(
                    Counter(
                        row.llm_route_planner_route_adoption_status
                        for row in blocker_rows
                        if row.llm_route_planner_route_adoption_status
                    ).items()
                )
            ),
            "mean_route_recall": _mean(
                row.route_recall for row in blocker_rows if row.matched_ground_truth
            ),
            "mean_delta_precision": _mean(
                row.delta_precision for row in blocker_rows if row.matched_ground_truth
            ),
        }
        for blocker in sorted(counts)
        for blocker_rows in [
            [
                row
                for row in rows
                if blocker in row.llm_route_planner_route_adoption_blockers
            ]
        ]
    }


def _llm_model_tier_summary(
    rows: list[FormalizationGapPlannerEvaluationRow],
) -> dict[str, dict[str, object]]:
    tiers = sorted(
        {
            row.llm_route_planner_model_tier
            for row in rows
            if row.llm_route_planner_model_tier
        }
    )
    return {
        tier: {
            "n_rows": len(tier_rows),
            "n_ok": sum(1 for row in tier_rows if row.ok),
            "n_matched_ground_truth": sum(
                1 for row in tier_rows if row.matched_ground_truth
            ),
            "mean_route_recall": _mean(
                row.route_recall for row in tier_rows if row.matched_ground_truth
            ),
            "mean_delta_precision": _mean(
                row.delta_precision for row in tier_rows if row.matched_ground_truth
            ),
            "mean_alignment_coverage": _mean(
                row.alignment_coverage for row in tier_rows
            ),
            "n_rows_with_generator_metadata": sum(
                1 for row in tier_rows if row.llm_route_planner_has_generator_metadata
            ),
            "n_rows_with_provider_usage": sum(
                1 for row in tier_rows if row.llm_route_planner_has_provider_usage
            ),
            "provider_input_tokens": sum(
                row.llm_route_planner_provider_input_tokens for row in tier_rows
            ),
            "provider_output_tokens": sum(
                row.llm_route_planner_provider_output_tokens for row in tier_rows
            ),
            "provider_cache_creation_input_tokens": sum(
                row.llm_route_planner_provider_cache_creation_input_tokens
                for row in tier_rows
            ),
            "provider_cache_read_input_tokens": sum(
                row.llm_route_planner_provider_cache_read_input_tokens
                for row in tier_rows
            ),
            "provider_total_tokens": sum(
                row.llm_route_planner_provider_total_tokens for row in tier_rows
            ),
            "n_rows_with_request_contract_blocked": sum(
                1
                for row in tier_rows
                if row.llm_route_planner_request_contract_blocked
            ),
            "n_rows_with_errors": sum(
                1 for row in tier_rows if row.llm_route_planner_errors
            ),
            "n_sonnet_triggers": sum(
                row.llm_route_planner_model_tier_decision_sonnet_trigger_count
                for row in tier_rows
            ),
            "n_source_feedback_rows": sum(
                row.llm_route_planner_source_feedback_row_count
                for row in tier_rows
            ),
            "n_source_feedback_proof_body_execution_failures": sum(
                row.llm_route_planner_source_feedback_proof_body_execution_failure_count
                for row in tier_rows
            ),
            "n_source_feedback_formal_environment_blockers": sum(
                row.llm_route_planner_source_feedback_formal_environment_blocker_count
                for row in tier_rows
            ),
            "n_interactive_formal_attempt_queue_rows": sum(
                row.llm_route_planner_interactive_formal_attempt_queue_row_count
                for row in tier_rows
            ),
            "n_interactive_formal_attempt_queue_items": sum(
                row.llm_route_planner_interactive_formal_attempt_queue_item_count
                for row in tier_rows
            ),
            "n_interactive_formal_attempt_queue_ready_items": sum(
                row.llm_route_planner_interactive_formal_attempt_queue_ready_item_count
                for row in tier_rows
            ),
            "n_interactive_formal_attempt_queue_blocked_items": sum(
                row.llm_route_planner_interactive_formal_attempt_queue_blocked_item_count
                for row in tier_rows
            ),
            "n_interactive_formal_attempt_queue_execution_commands": sum(
                row.llm_route_planner_interactive_formal_attempt_queue_execution_command_count
                for row in tier_rows
            ),
            **_llm_route_option_selection_summary(tier_rows),
        }
        for tier in tiers
        for tier_rows in [
            [row for row in rows if row.llm_route_planner_model_tier == tier]
        ]
    }


def _llm_model_tier_decision_basis_summary(
    rows: list[FormalizationGapPlannerEvaluationRow],
) -> dict[str, dict[str, object]]:
    bases = sorted(
        {
            row.llm_route_planner_model_tier_decision_basis
            for row in rows
            if row.llm_route_planner_model_tier_decision_basis
        }
    )
    return {
        basis: {
            "n_rows": len(basis_rows),
            "n_ok": sum(1 for row in basis_rows if row.ok),
            "n_matched_ground_truth": sum(
                1 for row in basis_rows if row.matched_ground_truth
            ),
            "by_model_tier": dict(
                Counter(
                    row.llm_route_planner_model_tier
                    for row in basis_rows
                    if row.llm_route_planner_model_tier
                )
            ),
            "n_sonnet_triggers": sum(
                row.llm_route_planner_model_tier_decision_sonnet_trigger_count
                for row in basis_rows
            ),
            "n_source_feedback_rows": sum(
                row.llm_route_planner_source_feedback_row_count
                for row in basis_rows
            ),
            "n_source_feedback_proof_body_execution_failures": sum(
                row.llm_route_planner_source_feedback_proof_body_execution_failure_count
                for row in basis_rows
            ),
            "n_source_feedback_formal_environment_blockers": sum(
                row.llm_route_planner_source_feedback_formal_environment_blocker_count
                for row in basis_rows
            ),
            "n_interactive_formal_attempt_queue_rows": sum(
                row.llm_route_planner_interactive_formal_attempt_queue_row_count
                for row in basis_rows
            ),
            "n_interactive_formal_attempt_queue_items": sum(
                row.llm_route_planner_interactive_formal_attempt_queue_item_count
                for row in basis_rows
            ),
            "n_interactive_formal_attempt_queue_ready_items": sum(
                row.llm_route_planner_interactive_formal_attempt_queue_ready_item_count
                for row in basis_rows
            ),
            "n_interactive_formal_attempt_queue_blocked_items": sum(
                row.llm_route_planner_interactive_formal_attempt_queue_blocked_item_count
                for row in basis_rows
            ),
            "n_interactive_formal_attempt_queue_execution_commands": sum(
                row.llm_route_planner_interactive_formal_attempt_queue_execution_command_count
                for row in basis_rows
            ),
            "n_rows_with_provider_usage": sum(
                1 for row in basis_rows if row.llm_route_planner_has_provider_usage
            ),
            "provider_input_tokens": sum(
                row.llm_route_planner_provider_input_tokens for row in basis_rows
            ),
            "provider_output_tokens": sum(
                row.llm_route_planner_provider_output_tokens for row in basis_rows
            ),
            "provider_cache_creation_input_tokens": sum(
                row.llm_route_planner_provider_cache_creation_input_tokens
                for row in basis_rows
            ),
            "provider_cache_read_input_tokens": sum(
                row.llm_route_planner_provider_cache_read_input_tokens
                for row in basis_rows
            ),
            "provider_total_tokens": sum(
                row.llm_route_planner_provider_total_tokens for row in basis_rows
            ),
            "mean_route_recall": _mean(
                row.route_recall for row in basis_rows if row.matched_ground_truth
            ),
            "mean_delta_precision": _mean(
                row.delta_precision for row in basis_rows if row.matched_ground_truth
            ),
            **_llm_route_option_selection_summary(basis_rows),
        }
        for basis in bases
        for basis_rows in [
            [
                row
                for row in rows
                if row.llm_route_planner_model_tier_decision_basis == basis
            ]
        ]
    }


def _llm_route_option_selection_summary(
    rows: list[FormalizationGapPlannerEvaluationRow],
) -> dict[str, int]:
    return {
        "n_rows_with_route_option_selection_brief": sum(
            1
            for row in rows
            if row.llm_route_planner_route_option_selection_brief_present
        ),
        "n_route_option_selection_candidate_options": sum(
            row.llm_route_planner_route_option_selection_candidate_count
            for row in rows
        ),
        "n_route_option_selection_candidate_primitives": sum(
            row.llm_route_planner_route_option_selection_candidate_primitive_count
            for row in rows
        ),
        "n_route_option_selection_candidates_with_residual_goals": sum(
            row.llm_route_planner_route_option_selection_candidates_with_residual_goals
            for row in rows
        ),
        "n_route_option_selection_candidate_residual_goals": sum(
            row.llm_route_planner_route_option_selection_candidate_residual_goal_count
            for row in rows
        ),
        "n_route_option_selection_lower_bound_residual_goals": sum(
            row.llm_route_planner_route_option_selection_lower_bound_residual_goal_count
            for row in rows
        ),
        "n_rows_with_route_option_selected_route_option": sum(
            1
            for row in rows
            if row.llm_route_planner_route_option_selected_route_option_id
        ),
        "n_route_option_selection_minimal_delta_selected_residual_goals": sum(
            row.llm_route_planner_route_option_selection_minimal_delta_selected_residual_goal_count
            for row in rows
        ),
        "n_route_option_selection_lower_bound_matches_minimal_delta": sum(
            1
            for row in rows
            if row.llm_route_planner_route_option_selection_brief_present
            and row.llm_route_planner_route_option_selection_lower_bound_matches_minimal_delta
        ),
        "n_route_option_selection_lower_bound_mismatches_minimal_delta": sum(
            1
            for row in rows
            if row.llm_route_planner_route_option_selection_brief_present
            and not row.llm_route_planner_route_option_selection_lower_bound_matches_minimal_delta
        ),
        "n_route_option_selected_matches_lower_bound": sum(
            1
            for row in rows
            if row.llm_route_planner_route_option_selected_route_option_id
            and row.llm_route_planner_route_option_selected_matches_lower_bound
        ),
        "n_route_option_selected_mismatches_lower_bound": sum(
            1
            for row in rows
            if row.llm_route_planner_route_option_selected_route_option_id
            and row.llm_route_planner_route_option_selection_lower_bound_selected_route_option_id
            and not row.llm_route_planner_route_option_selected_matches_lower_bound
        ),
        "n_route_option_selected_matches_minimal_delta": sum(
            1
            for row in rows
            if row.llm_route_planner_route_option_selected_route_option_id
            and row.llm_route_planner_route_option_selected_matches_minimal_delta
        ),
        "n_route_option_selected_mismatches_minimal_delta": sum(
            1
            for row in rows
            if row.llm_route_planner_route_option_selected_route_option_id
            and row.minimal_delta_selected_route_option_id
            and not row.llm_route_planner_route_option_selected_matches_minimal_delta
        ),
    }


def _quality_control_field_summary(
    rows: list[FormalizationGapPlannerEvaluationRow],
) -> dict[str, dict[str, object]]:
    return {
        field_name: {
            "n_rows": sum(
                1 for row in rows if field_name in row.quality_control_fields
            ),
            "n_values": len(
                {
                    value
                    for row in rows
                    for value in row.quality_controls.get(field_name, tuple())
                    if value
                }
            ),
            "values": tuple(
                sorted(
                    {
                        value
                        for row in rows
                        for value in row.quality_controls.get(field_name, tuple())
                        if value
                    }
                )
            ),
        }
        for field_name in QUALITY_CONTROL_FIELDS
        if any(field_name in row.quality_control_fields for row in rows)
    }


def _unique_row_attr_strings(
    rows: list[FormalizationGapPlannerEvaluationRow],
    attr_name: str,
) -> tuple[str, ...]:
    return tuple(
        sorted(
            {
                str(item)
                for row in rows
                for item in getattr(row, attr_name)
                if str(item)
            }
        )
    )


def _realization_missing_primitives_by_route(
    rows: list[FormalizationGapPlannerEvaluationRow],
) -> tuple[dict[str, object], ...]:
    diagnostics: list[dict[str, object]] = []
    for row in rows:
        missing_selected = _str_tuple(
            row.realization_missing_selected_formal_primitives
        )
        missing_delta = _str_tuple(row.realization_missing_delta_alignment_primitives)
        omitted_cost_hint = _str_tuple(row.realization_omitted_cost_hint_primitives)
        if not missing_selected and not missing_delta and not omitted_cost_hint:
            continue
        diagnostics.append(
            {
                "route_id": row.route_id,
                "display_name": row.display_name,
                "goal_plan_id": row.goal_plan_id,
                "missing_selected_formal_primitives": missing_selected,
                "missing_delta_alignment_primitives": missing_delta,
                "omitted_cost_hint_primitives": omitted_cost_hint,
                "llm_route_planner_row_id": row.llm_route_planner_row_id,
                "llm_route_planner_model_tier": row.llm_route_planner_model_tier,
            }
        )
    return tuple(diagnostics)


def _alignment_contract(row: dict[str, Any]) -> tuple[bool, float, tuple[str, ...], tuple[str, ...]]:
    selected = set(_str_tuple(row.get("selected_primitives", [])))
    edges = row.get("route_alignment_edges", [])
    if not selected:
        return False, 0.0, tuple(), tuple()
    if not isinstance(edges, (list, tuple)):
        return False, 0.0, tuple(), tuple(sorted(selected))
    informal_node_ids = {
        str(node.get("node_id", ""))
        for node in row.get("informal_knowledge_dag_nodes", [])
        if isinstance(node, dict)
    }
    formal_node_ids = {
        str(node.get("node_id", ""))
        for node in _formal_realization_nodes(row)
        if isinstance(node, dict)
    }
    aligned: set[str] = set()
    malformed = False
    for edge in edges:
        if not isinstance(edge, dict):
            malformed = True
            continue
        if str(edge.get("kind", "")) != "aligned_to_formal_realization_candidate":
            malformed = True
            continue
        primitive = str(edge.get("primitive", ""))
        source = str(edge.get("source", ""))
        target = str(edge.get("target", ""))
        if not primitive or source not in informal_node_ids or target not in formal_node_ids:
            malformed = True
            continue
        aligned.add(primitive)
    unaligned = tuple(sorted(item for item in selected - aligned if item))
    aligned_tuple = tuple(sorted(item for item in selected & aligned if item))
    coverage = _ratio(len(aligned_tuple), len(selected), empty_value=0.0)
    return not malformed and not unaligned, coverage, aligned_tuple, unaligned


def _formal_realization_nodes(row: dict[str, Any]) -> tuple[dict[str, Any], ...]:
    nodes = row.get("formal_realization_dag_nodes", [])
    if not isinstance(nodes, (list, tuple)) or not nodes:
        if _is_lean_target_prover(row.get("target_prover_family", "")):
            nodes = row.get("lean_realization_dag_nodes", [])
        else:
            nodes = []
    if not isinstance(nodes, (list, tuple)):
        return tuple()
    return tuple(node for node in nodes if isinstance(node, dict))


def _row_with_manifest_target(
    row: dict[str, Any],
    plan_payload: dict[str, Any],
) -> dict[str, Any]:
    row_target = str(
        row.get("target_prover_family", "") or row.get("target_prover", "")
    ).strip()
    if row_target:
        return row
    target = str(
        plan_payload.get("target_prover_family", "")
        or plan_payload.get("target_prover", "")
    ).strip()
    if not target:
        return row
    updated = dict(row)
    updated["target_prover_family"] = target
    return updated


def _is_lean_target_prover(value: object) -> bool:
    key = _target_prover_key(value)
    return key == "lean4" or key.startswith("lean4_")


def _target_prover_key(value: object) -> str:
    key = str(value).strip().lower().replace("-", "_")
    aliases = {
        "lean": "lean4",
        "lean_4": "lean4",
    }
    return aliases.get(key, key)


def _node_field_count(row: dict[str, Any], field_name: str) -> int:
    nodes = row.get(field_name, [])
    if not isinstance(nodes, (list, tuple)):
        return 0
    return sum(1 for node in nodes if isinstance(node, dict))


def _truth_rows(payload: dict[str, Any]) -> list[dict[str, Any]]:
    for field_name in ("routes", "rows", "ground_truth_routes"):
        rows = payload.get(field_name, [])
        if isinstance(rows, list):
            return [row for row in rows if isinstance(row, dict)]
    return []


def _truth_index(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    index: dict[str, dict[str, Any]] = {}
    for row in rows:
        for field_name in ("goal_plan_id", "route_id", "display_name"):
            value = str(row.get(field_name, ""))
            if value:
                index[f"{field_name}:{value}"] = row
    return index


def _match_truth(
    goal_plan_id: str,
    route_id: str,
    display_name: str,
    truth_index: dict[str, dict[str, Any]],
) -> tuple[dict[str, Any], str]:
    for field_name, value in (
        ("route_id", route_id),
        ("goal_plan_id", goal_plan_id),
        ("display_name", display_name),
    ):
        key = f"{field_name}:{value}"
        if value and key in truth_index:
            return truth_index[key], key
    return {}, ""


def _node_primitives(nodes: Any) -> tuple[str, ...]:
    primitives: list[str] = []
    if not isinstance(nodes, (list, tuple)):
        return tuple()
    for node in nodes:
        if not isinstance(node, dict):
            continue
        primitive = str(node.get("primitive", "") or node.get("label", ""))
        if primitive:
            primitives.append(primitive)
    return tuple(sorted(dict.fromkeys(primitives)))


def _normalize_coverage_status(value: str) -> str:
    aliases = {
        "already_exists": "exact_exists",
        "existing_in_library": "exact_exists",
        "exact_proof_bank_obligation_available": "exact_exists",
        "reuse_exact_proof_bank_obligation": "exact_exists",
        "near_match": "near_exists",
        "near_exists": "near_exists",
        "wrapper_needed": "wrapper_needed",
        "add_minimal_wrapper": "wrapper_needed",
        "bridge_needed": "bridge_needed",
        "design_bridge_lemma": "bridge_needed",
        "source_discovery_needed": "definition_missing",
        "source_port_needed": "definition_missing",
        "port_external_source": "definition_missing",
        "definition_missing": "definition_missing",
        "new_definition_or_theory_needed": "theory_missing",
        "design_from_first_principles": "theory_missing",
        "theory_missing": "theory_missing",
    }
    return aliases.get(value, value)


def _str_tuple(values: Any) -> tuple[str, ...]:
    if isinstance(values, str):
        return (values,) if values else tuple()
    if not isinstance(values, (list, tuple, set)):
        return tuple()
    return tuple(sorted(dict.fromkeys(str(item) for item in values if str(item))))


def _dict_tuple(values: Any) -> tuple[dict[str, Any], ...]:
    if isinstance(values, dict):
        values = (values,)
    if not isinstance(values, (list, tuple, set)):
        return tuple()
    rows: list[dict[str, Any]] = []
    for value in values:
        if not isinstance(value, dict):
            continue
        row = {str(key): item for key, item in value.items() if str(key)}
        if row:
            rows.append(row)
    return tuple(rows)


def _dict_value(row: Any, key: str) -> dict[str, Any]:
    if not isinstance(row, dict):
        return {}
    value = row.get(key, {})
    return dict(value) if isinstance(value, dict) else {}


def _int_value(value: Any) -> int:
    if isinstance(value, bool):
        return int(value)
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _nonnegative_int(value: Any) -> int:
    return max(0, _int_value(value))


def _ratio(numerator: int, denominator: int, *, empty_value: float) -> float:
    if denominator == 0:
        return empty_value
    return numerator / denominator


def _mean(values: Any) -> float:
    items = [float(value) for value in values]
    if not items:
        return 0.0
    return sum(items) / len(items)


def _schema_property_errors(
    field_name: str,
    value: Any,
    field_schema: dict[str, Any],
) -> tuple[str, ...]:
    errors: list[str] = []
    expected_type = field_schema.get("type")
    if expected_type == "integer":
        if not isinstance(value, int) or isinstance(value, bool):
            errors.append(f"{field_name} must be integer")
    elif expected_type == "number":
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            errors.append(f"{field_name} must be number")
    elif expected_type == "string":
        if not isinstance(value, str):
            errors.append(f"{field_name} must be string")
        elif field_schema.get("minLength") and len(value) < int(field_schema["minLength"]):
            errors.append(f"{field_name} must be non-empty")
    elif expected_type == "boolean":
        if not isinstance(value, bool):
            errors.append(f"{field_name} must be boolean")
    elif expected_type == "object":
        if not isinstance(value, dict):
            errors.append(f"{field_name} must be object")
    elif expected_type == "array":
        if not isinstance(value, (list, tuple)):
            errors.append(f"{field_name} must be array")
        else:
            item_schema = field_schema.get("items", {})
            if isinstance(item_schema, dict) and item_schema.get("type") == "string":
                bad = [idx for idx, item in enumerate(value) if not isinstance(item, str)]
                if bad:
                    errors.append(
                        f"{field_name} items must be string at indexes "
                        + ",".join(str(idx) for idx in bad)
                    )
            if isinstance(item_schema, dict) and item_schema.get("type") == "object":
                bad = [idx for idx, item in enumerate(value) if not isinstance(item, dict)]
                if bad:
                    errors.append(
                        f"{field_name} items must be object at indexes "
                        + ",".join(str(idx) for idx in bad)
                    )
            if isinstance(item_schema, dict) and isinstance(
                item_schema.get("enum"),
                list,
            ):
                allowed = item_schema["enum"]
                unsupported: list[Any] = []
                for item in value:
                    if item not in allowed and item not in unsupported:
                        unsupported.append(item)
                if unsupported:
                    errors.append(
                        f"{field_name} items contain unsupported values: "
                        + ", ".join(str(item) for item in unsupported[:8])
                    )
    if "const" in field_schema and value != field_schema["const"]:
        errors.append(f"{field_name} must equal {field_schema['const']!r}")
    enum_values = field_schema.get("enum")
    if isinstance(enum_values, list) and value not in enum_values:
        errors.append(f"{field_name} must be one of {enum_values!r}")
    pattern = field_schema.get("pattern")
    if isinstance(pattern, str) and isinstance(value, str) and pattern not in value:
        errors.append(f"{field_name} must contain {pattern!r}")
    return tuple(errors)


def _read_json(path: Path, errors: list[str]) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        errors.append(f"missing JSON file: {path}")
        return {}
    except Exception as exc:
        errors.append(f"failed to parse {path}: {type(exc).__name__}: {exc}")
        return {}
    return payload if isinstance(payload, dict) else {}


def _markdown_report(payload: dict[str, object]) -> str:
    lines = [
        "# Formalization Gap Planner Evaluation",
        "",
        f"- Evaluation rows: {payload.get('n_evaluation_rows')}",
        f"- Evaluation row schema valid: {payload.get('n_evaluation_row_schema_valid')}/{payload.get('n_evaluation_rows')}",
        f"- Matched ground truth: {payload.get('n_matched_ground_truth')}",
        f"- Ground-truth rows matched by plan: {payload.get('n_ground_truth_rows_matched_by_plan')}",
        f"- Unlabeled plan rows: {payload.get('n_unlabeled_plan_rows')}",
        f"- Plan rows with formal realization DAG nodes: {payload.get('n_plan_rows_with_formal_realization_dag_nodes')}",
        f"- Plan rows with legacy Lean realization DAG nodes: {payload.get('n_plan_rows_with_legacy_lean_realization_dag_nodes')}",
        f"- Mean route recall: {payload.get('mean_route_recall')}",
        f"- Mean route precision: {payload.get('mean_route_precision')}",
        f"- Mean delta precision: {payload.get('mean_delta_precision')}",
        f"- Mean delta recall: {payload.get('mean_delta_recall')}",
        f"- Mean residual precision: {payload.get('mean_residual_precision')}",
        f"- Mean residual recall: {payload.get('mean_residual_recall')}",
        f"- Mean coverage classification accuracy: {payload.get('mean_coverage_classification_accuracy')}",
        f"- Two-DAG ready: {payload.get('n_two_dag_contract_ok')}",
        f"- Alignment ready: {payload.get('n_alignment_contract_ok')}",
        f"- Mean alignment coverage: {payload.get('mean_alignment_coverage')}",
        f"- Feedback-loop ready: {payload.get('n_feedback_loop_ready')}",
        f"- Rows with minimal-delta cost graph: {payload.get('n_rows_with_minimal_delta_cost_graph')}",
        f"- Rows with realization coverage witness: {payload.get('n_rows_with_realization_coverage_witness')}",
        f"- Rows with complete realization coverage: {payload.get('n_rows_with_complete_realization_coverage')}",
        f"- Missing selected formal primitives: {payload.get('realization_missing_selected_formal_primitives')}",
        f"- Missing delta alignment primitives: {payload.get('realization_missing_delta_alignment_primitives')}",
        f"- Omitted cost-hint primitives: {payload.get('realization_omitted_cost_hint_primitives')}",
        f"- Rows with LLM route-planner trace: {payload.get('n_rows_with_llm_route_planner_trace')}",
        f"- Rows with LLM request-contract blocks: {payload.get('n_rows_with_llm_route_planner_request_contract_blocked')}",
        f"- LLM route-planner errors: {payload.get('n_llm_route_planner_errors')}",
        (
            f"- LLM provider usage rows/input/output/cache-read/total: "
            f"{payload.get('n_rows_with_llm_route_planner_provider_usage')}/"
            f"{payload.get('total_llm_route_planner_provider_input_tokens')}/"
            f"{payload.get('total_llm_route_planner_provider_output_tokens')}/"
            f"{payload.get('total_llm_route_planner_provider_cache_read_input_tokens')}/"
            f"{payload.get('total_llm_route_planner_provider_total_tokens')}"
        ),
        f"- Evaluation by LLM model tier: {payload.get('evaluation_by_llm_model_tier')}",
        f"- Evaluation by LLM model-tier decision basis: {payload.get('evaluation_by_llm_model_tier_decision_basis')}",
        f"- LLM source-feedback tier rows: {payload.get('n_llm_route_planner_source_feedback_rows')}",
        (
            "- LLM interactive formal-attempt queue tier items "
            f"ready/blocked/total: "
            f"{payload.get('n_llm_route_planner_interactive_formal_attempt_queue_ready_items')}/"
            f"{payload.get('n_llm_route_planner_interactive_formal_attempt_queue_blocked_items')}/"
            f"{payload.get('n_llm_route_planner_interactive_formal_attempt_queue_items')}"
        ),
        (
            "- LLM residual-goal contexts "
            f"rows/contexts/source-refs/provenance/without-context: "
            f"{payload.get('n_rows_with_llm_route_planner_residual_goal_contexts')}/"
            f"{payload.get('n_llm_route_planner_residual_goal_contexts')}/"
            f"{payload.get('n_llm_route_planner_residual_goal_context_source_refs')}/"
            f"{payload.get('n_llm_route_planner_residual_goal_context_provenance_values')}/"
            f"{payload.get('n_llm_route_planner_residual_goals_without_context')}"
        ),
        (
            "- LLM route-option selection "
            "rows/options/primitives/residual-options/residual-goals/"
            "lower-bound-residuals/selected-residuals/lb-md-matches/"
            "lb-md-mismatches/selected-ids/selected-lb-matches/"
            "selected-md-matches: "
            f"{payload.get('n_rows_with_llm_route_planner_route_option_selection_brief')}/"
            f"{payload.get('n_llm_route_planner_route_option_selection_candidate_options')}/"
            f"{payload.get('n_llm_route_planner_route_option_selection_candidate_primitives')}/"
            f"{payload.get('n_llm_route_planner_route_option_selection_candidates_with_residual_goals')}/"
            f"{payload.get('n_llm_route_planner_route_option_selection_candidate_residual_goals')}/"
            f"{payload.get('n_llm_route_planner_route_option_selection_lower_bound_residual_goals')}/"
            f"{payload.get('n_llm_route_planner_route_option_selection_minimal_delta_selected_residual_goals')}/"
            f"{payload.get('n_llm_route_planner_route_option_selection_lower_bound_matches_minimal_delta')}/"
            f"{payload.get('n_llm_route_planner_route_option_selection_lower_bound_mismatches_minimal_delta')}/"
            f"{payload.get('n_rows_with_llm_route_planner_route_option_selected_route_option')}/"
            f"{payload.get('n_llm_route_planner_route_option_selected_matches_lower_bound')}/"
            f"{payload.get('n_llm_route_planner_route_option_selected_matches_minimal_delta')}"
        ),
        f"- Evaluation by LLM route adoption status: {payload.get('evaluation_by_llm_route_adoption_status')}",
        f"- LLM route adoption blockers: {payload.get('llm_route_adoption_blockers')}",
        f"- Rows with LLM route-adoption preconditions: {payload.get('n_rows_with_llm_route_planner_route_adoption_preconditions')}",
        (
            "- LLM route-adoption precondition blockers/fields/target primitives: "
            f"{payload.get('n_llm_route_planner_route_adoption_precondition_known_blockers')}/"
            f"{payload.get('n_llm_route_planner_route_adoption_precondition_required_response_fields')}/"
            f"{payload.get('n_llm_route_planner_route_adoption_precondition_target_primitives')}"
        ),
        (
            f"- LLM primitive matrix complete/repair/source/reuse/delta gaps: "
            f"{payload.get('n_rows_with_complete_llm_route_planner_primitive_evidence_matrix_accounting')}/"
            f"{payload.get('n_llm_route_planner_primitive_evidence_matrix_repair_obligations')}/"
            f"{payload.get('n_llm_route_planner_primitive_evidence_matrix_source_backed_missing_response_source_snippets')}/"
            f"{payload.get('n_llm_route_planner_primitive_evidence_matrix_formal_supported_missing_reuse')}/"
            f"{payload.get('n_llm_route_planner_primitive_evidence_matrix_delta_needed_missing_accounting')}"
        ),
        f"- Rows with quality controls: {payload.get('n_rows_with_quality_controls')}",
        f"- Quality control fields: {payload.get('quality_control_fields')}",
        f"- Mean selected route-option cost: {payload.get('mean_minimal_delta_selected_route_cost')}",
        f"- Kernel-verified ground truth rows: {payload.get('n_kernel_verified_ground_truth')}",
        f"- Kernel verification witnesses: {payload.get('n_kernel_verification_witnesses')}",
        f"- All OK: {payload.get('all_ok')}",
        "",
        "## Boundary",
        "",
        str(payload.get("proof_evidence_boundary", PROOF_EVIDENCE_BOUNDARY)),
        "",
        "## Rows",
        "",
    ]
    for row in payload.get("rows", []):
        if not isinstance(row, dict):
            continue
        lines.append(
            f"- `{row.get('display_name')}` recall={row.get('route_recall')} "
            f"precision={row.get('route_precision')} delta_precision={row.get('delta_precision')} "
            f"delta_recall={row.get('delta_recall')} "
            f"llm_tier={row.get('llm_route_planner_model_tier')} "
            f"route_adoption={row.get('llm_route_planner_route_adoption_status')} "
            f"ok={row.get('ok')}"
        )
        if row.get("route_missing_primitives"):
            lines.append(
                "  missing route primitives: "
                + ", ".join(str(item) for item in row.get("route_missing_primitives", [])[:8])
            )
        if row.get("delta_unnecessary_primitives"):
            lines.append(
                "  unnecessary delta primitives: "
                + ", ".join(str(item) for item in row.get("delta_unnecessary_primitives", [])[:8])
            )
        if row.get("unaligned_primitives"):
            lines.append(
                "  unaligned primitives: "
                + ", ".join(str(item) for item in row.get("unaligned_primitives", [])[:8])
            )
    return "\n".join(lines) + "\n"
