from __future__ import annotations

import hashlib
import json
from pathlib import Path


LADDER_PATH = Path("benchmarks/research_capability_ladder_20260814.json")


def _load_ladder() -> dict:
    return json.loads(LADDER_PATH.read_text(encoding="utf-8"))


def test_research_ladder_separates_product_and_strict_formal_authority() -> None:
    ladder = _load_ladder()
    authority = ladder["authority_boundary"]

    assert authority["product_research_authority"] is True
    assert authority["strict_formal_protocol_unchanged"] is True
    assert authority["aggregate_score_may_override_required_dimension"] is False
    assert authority["open_problem_model_agreement_is_correctness_evidence"] is False
    assert Path(authority["strict_formal_capability_protocol"]).exists()


def test_research_ladder_has_progressive_evidence_and_no_fixed_replication_rule() -> None:
    ladder = _load_ladder()

    assert [level["id"] for level in ladder["levels"]] == [
        "L0",
        "L1",
        "L2",
        "L3",
        "L4",
        "L5",
        "L6",
    ]
    assert ladder["levels"][-1]["correctness_scored"] is False
    assert ladder["simulation_precision_contract"][
        "universal_fixed_replication_count"
    ] is None
    assert ladder["simulation_precision_contract"][
        "confirmatory_rule_frozen_before_outcomes"
    ] is True
    assert ladder["formalization_contract"]["optional_gap_blocks_nonformal_dimensions"] is False
    assert ladder["formalization_contract"]["nonproof_evidence_may_be_promoted_to_proof"] is False


def test_ladder_counts_fully_configured_active_tasks_without_embedding_gold() -> None:
    ladder = _load_ladder()
    candidates = ladder["initial_candidate_queue"]

    assert candidates
    scored = [
        candidate
        for candidate in candidates
        if candidate["status"] in {"active_scored", "consumed_scored"}
    ]
    pending = [
        candidate
        for candidate in candidates
        if candidate["status"].startswith("proposed_pending_")
    ]
    assert scored
    assert ladder["current_readiness"]["active_scored_tasks"] == len(scored)
    assert ladder["current_readiness"]["fully_gold_configured_tasks"] == len(scored)
    assert ladder["current_readiness"]["fully_gold_passed_tasks"] == sum(
        candidate["activation_evidence"].get("full_task_passed") is True
        for candidate in scored
    )
    assert len({candidate["id"] for candidate in candidates}) == len(candidates)
    for candidate in scored:
        assert candidate["gold_runtime_visibility"] == "evaluator_only_after_runtime"
        assert candidate["activation_status"].startswith(
            ("full_task_gold_", "fresh_live_v1_", "frozen_ready_")
        )
        assert Path(candidate["visible_questions_path"]).is_file()
        assert "gold_manifest" not in candidate
        assert candidate["gold_authority"] == (
            "operator_provisioned_outside_repository_and_model_workspace"
        )
        assert len(candidate["gold_manifest_sha256"]) == 64
    assert len(scored) + len(pending) == len(candidates)
    forbidden_keys = {
        "expected_answer",
        "expected_results",
        "theorem_statement",
        "proof",
        "reference_code",
    }
    assert all(forbidden_keys.isdisjoint(candidate) for candidate in candidates)
    assert all(candidate["level"] in {"L0", "L1", "L2"} for candidate in candidates)


def test_ladder_live_evaluation_policy_is_exact_haiku() -> None:
    model_policy = _load_ladder()["model_policy"]

    assert model_policy["live_evaluation_model"] == "claude-haiku-4-5-20251001"
    assert model_policy["live_evaluation_model_tier"] == "haiku"
    assert model_policy["sonnet_live_calls_allowed"] is False
    assert model_policy["opus_live_calls_allowed"] is False
    assert model_policy["automatic_tier_escalation_allowed"] is False


def test_quantile_l0_freezes_theory_only_failure_without_resampling() -> None:
    ladder = _load_ladder()
    candidate = next(
        row
        for row in ladder["initial_candidate_queue"]
        if row["id"] == "sample_quantile_clt_known_result"
    )

    assert candidate["level"] == "L0"
    assert candidate["status"] == "active_scored"
    assert candidate["activation_evidence"]["fresh_live_runs"] == 1
    assert candidate["activation_evidence"]["fresh_live_runtime_status"] == "BLOCKED"
    assert candidate["activation_evidence"]["fresh_live_hidden_gold_result"].startswith(
        "0/1"
    )
    assert candidate["activation_evidence"]["model_draw_resampling_blocked"] is True
    assert candidate["activation_evidence"]["full_task_passed"] is False
    assert candidate["task_intent"] == {
        "source_replication": "not_applicable",
        "theory": "required",
        "scientific_code": "not_applicable",
        "empirical": "not_applicable",
        "formal": "not_applicable",
        "novelty": "not_applicable",
        "unresolved_gaps": "required",
    }
    visible_path = Path(candidate["visible_questions_path"])
    assert visible_path.is_file()
    assert hashlib.sha256(visible_path.read_bytes()).hexdigest() == (
        candidate["activation_evidence"]["visible_questions_sha256"]
    )


def test_doubleml_l1_freezes_exact_replication_without_conflating_l2() -> None:
    ladder = _load_ladder()
    candidate = next(
        row
        for row in ladder["initial_candidate_queue"]
        if row["id"] == "double_machine_learning_public_replication"
    )

    assert candidate["level"] == "L1"
    assert candidate["status"] == "active_scored"
    assert candidate["activation_status"] == (
        "fresh_live_v1_blocked_before_checkpoint_promotion"
    )
    assert candidate["activation_evidence"]["fresh_live_runs"] == 1
    assert candidate["activation_evidence"]["fresh_live_runtime_status"] == (
        "BLOCKED"
    )
    assert candidate["activation_evidence"][
        "fresh_live_source_execution_status"
    ] == "EXECUTED"
    assert candidate["activation_evidence"][
        "fresh_live_hidden_gold_result"
    ].startswith("0/1")
    assert candidate["activation_evidence"][
        "runtime_source_replication_lane_available"
    ] is True
    assert candidate["activation_evidence"][
        "source_only_checkpoint_runtime_regression_passed"
    ] is True
    assert candidate["activation_evidence"]["mechanism_exact_source_runs"] == 1
    assert candidate["activation_evidence"][
        "mechanism_stdout_hash_matched_frozen_rerun"
    ] is True
    assert candidate["task_intent"] == {
        "source_replication": "required",
        "theory": "optional",
        "scientific_code": "not_applicable",
        "empirical": "not_applicable",
        "formal": "not_applicable",
        "novelty": "not_applicable",
        "unresolved_gaps": "required",
    }
    visible_path = Path(candidate["visible_questions_path"])
    assert visible_path.is_file()
    assert hashlib.sha256(visible_path.read_bytes()).hexdigest() == (
        candidate["activation_evidence"]["visible_questions_sha256"]
    )
    assert len(candidate["source_snapshot_hash"]) == 64
    assert len(candidate["source_manifest_sha256"]) == 64
    assert len(candidate["gold_manifest_sha256"]) == 64


def test_model_x_l2_hides_author_code_and_freezes_gold_before_first_draw() -> None:
    ladder = _load_ladder()
    candidate = next(
        row
        for row in ladder["initial_candidate_queue"]
        if row["id"] == "model_x_public_paper_to_code_reproduction"
    )

    assert candidate["level"] == "L2"
    assert candidate["status"] == "active_scored"
    assert candidate["activation_status"] == (
        "fresh_live_v1_blocked_by_theory_progress_context_binding"
    )
    evidence = candidate["activation_evidence"]
    assert evidence["author_implementation_hidden_from_l2_runtime"] is True
    assert evidence["gold_activated_before_first_runtime_model_call"] is True
    assert evidence["fresh_live_runs"] == 1
    assert evidence["fresh_live_runtime_status"] == "BLOCKED"
    assert evidence["fresh_live_runtime_research_eval"] == "0/1 complete"
    assert evidence["fresh_live_accepted_theory_packet"] is False
    assert evidence["fresh_live_algorithm_executions"] == 0
    assert evidence["fresh_live_simulation_executions"] == 0
    assert evidence["fresh_live_formalizer_executions"] == 0
    assert evidence["model_draw_resampling_blocked"] is True
    assert len(evidence["post_run_shared_continuation_fix_commit"]) == 40
    assert evidence["semantic_calibration_cases"] == 10
    assert evidence["semantic_calibration_cases_correct"] == 10
    assert evidence["algorithm_reference_checks"] == "7/7"
    assert evidence["algorithm_negative_variants_rejected"] == 4
    assert evidence["full_task_passed"] is False
    assert candidate["task_intent"] == {
        "source_replication": "not_applicable",
        "theory": "required",
        "scientific_code": "required",
        "empirical": "required",
        "formal": "not_applicable",
        "novelty": "not_applicable",
        "unresolved_gaps": "required",
    }
    assert len(candidate["source_snapshot_hash"]) == 64
    assert len(candidate["source_manifest_sha256"]) == 64
    assert len(candidate["gold_manifest_sha256"]) == 64
    visible_path = Path(candidate["visible_questions_path"])
    assert visible_path.is_file()
    assert hashlib.sha256(visible_path.read_bytes()).hexdigest() == (
        evidence["visible_questions_sha256"]
    )
    question = json.loads(visible_path.read_text(encoding="utf-8"))["questions"][0]
    assert "author implementation and gold outcomes are withheld" in question[
        "description"
    ]
    assert "downstream knockoff-filter FDR theorem" in question["description"]


def test_horvitz_thompson_l0_freezes_gold_without_embedding_evaluator() -> None:
    ladder = _load_ladder()
    candidate = next(
        row
        for row in ladder["initial_candidate_queue"]
        if row["id"] == "poisson_horvitz_thompson_total_known_result"
    )

    assert candidate["level"] == "L0"
    assert candidate["family"] == "survey_sampling"
    assert candidate["status"] == "active_scored"
    assert candidate["activation_status"] == (
        "fresh_live_v1_blocked_by_redundant_nonformal_theorem_handoff"
    )
    evidence = candidate["activation_evidence"]
    assert evidence["gold_frozen_before_first_runtime_model_call"] is True
    assert evidence["hidden_gold_manifest_validated"] is True
    assert evidence["fresh_live_runs"] == 1
    assert evidence["fresh_live_runtime_status"] == "BLOCKED"
    assert evidence["fresh_live_research_eval_result"] == "0/1"
    assert evidence["fresh_live_hidden_gold_result"].startswith(
        "0/1_not_executed"
    )
    assert evidence["fresh_live_accepted_theory_packet"] is False
    assert evidence["fresh_live_algorithm_executions"] == 0
    assert evidence["fresh_live_simulation_executions"] == 0
    assert evidence["model_draw_resampling_blocked"] is True
    assert evidence["semantic_calibration_cases"] == 10
    assert evidence["semantic_calibration_cases_correct"] == 10
    assert evidence["algorithm_reference_checks"] == "8/8"
    assert evidence["algorithm_negative_variants_rejected"] == 4
    assert evidence["full_task_passed"] is False
    assert candidate["task_intent"] == {
        "source_replication": "not_applicable",
        "theory": "required",
        "scientific_code": "required",
        "empirical": "required",
        "formal": "not_applicable",
        "novelty": "not_applicable",
        "unresolved_gaps": "required",
    }
    assert len(candidate["source_snapshot_hash"]) == 64
    assert len(candidate["source_manifest_sha256"]) == 64
    assert len(candidate["gold_manifest_sha256"]) == 64
    visible_path = Path(candidate["visible_questions_path"])
    assert hashlib.sha256(visible_path.read_bytes()).hexdigest() == (
        evidence["visible_questions_sha256"]
    )
    question = json.loads(visible_path.read_text(encoding="utf-8"))["questions"][0]
    assert question["id"] == candidate["id"]
    assert "est_poisson_horvitz_thompson" in question["description"]
    assert "Lean formalization" in question["description"]

    runtime_visible = json.dumps(
        {"candidate": candidate, "question": question}, sort_keys=True
    )
    for hidden_name in (
        "gold_manifest.json",
        "reference_estimator.py",
        "negative_unweighted.py",
        "negative_hajek.py",
        "negative_variance_denominator.py",
        "semantic_reference.md",
        "semantic_calibration_cases.json",
    ):
        assert hidden_name not in runtime_visible


def test_normal_sample_variance_l0_records_operator_invalidated_single_draw() -> None:
    ladder = _load_ladder()
    candidate = next(
        row
        for row in ladder["initial_candidate_queue"]
        if row["id"] == "normal_sample_variance_chi_square_known_result"
    )

    assert candidate["level"] == "L0"
    assert candidate["family"] == "mathematical_statistics"
    assert candidate["status"] == "active_scored"
    assert candidate["activation_status"] == (
        "fresh_live_v1_operator_invalidated_theory_review_false_positive"
    )
    evidence = candidate["activation_evidence"]
    assert evidence["gold_frozen_before_first_runtime_model_call"] is True
    assert evidence["hidden_gold_manifest_validated"] is True
    assert evidence["fresh_live_runs"] == 1
    assert evidence["fresh_live_runtime_status"] == (
        "ACCEPTED_AUTOMATED_FALSE_POSITIVE"
    )
    assert evidence["operator_audit_disposition"] == "INVALIDATED"
    assert evidence["fresh_live_algorithm_executions"] == 1
    assert evidence["fresh_live_simulation_executions"] == 1
    assert evidence["fresh_live_formalizer_executions"] == 0
    assert evidence["algorithm_reference_checks"] == "8/8"
    assert evidence["algorithm_negative_variants_rejected"] == 4
    assert evidence["empirical_reference_dgps_passed"] == 3
    assert evidence["semantic_calibration_cases"] == 10
    assert evidence["semantic_calibration_cases_correct"] == 10
    assert evidence["model_draw_resampling_blocked"] is True
    assert evidence["full_task_passed"] is False
    assert Path(evidence["operator_audit_path"]).is_file()
    assert candidate["task_intent"] == {
        "source_replication": "not_applicable",
        "theory": "required",
        "scientific_code": "required",
        "empirical": "required",
        "formal": "not_applicable",
        "novelty": "not_applicable",
        "unresolved_gaps": "required",
    }
    for field in (
        "source_snapshot_hash",
        "source_manifest_sha256",
        "gold_manifest_sha256",
        "gold_descriptor_hash",
    ):
        assert len(candidate[field]) == 64
    visible_path = Path(candidate["visible_questions_path"])
    assert visible_path.is_file()
    assert hashlib.sha256(visible_path.read_bytes()).hexdigest() == (
        evidence["visible_questions_sha256"]
    )
    question = json.loads(visible_path.read_text(encoding="utf-8"))["questions"][0]
    assert question["id"] == candidate["id"]
    assert "authoritative Markdown/LaTeX theory workspace" in question["description"]
    assert "est_normal_sample_variance" in question["description"]
    assert "Lean formalization" in question["description"]

    runtime_visible = json.dumps(
        {"candidate": candidate, "question": question}, sort_keys=True
    )
    for hidden_name in (
        "gold_manifest.json",
        "reference_estimator.py",
        "negative_divisor_n.py",
        "negative_uncentered.py",
        "negative_wrong_pivot.py",
        "semantic_reference.md",
        "semantic_calibration_cases.json",
    ):
        assert hidden_name not in runtime_visible


def test_median_of_means_l0_is_frozen_after_its_only_live_draw() -> None:
    ladder = _load_ladder()
    candidate = next(
        row
        for row in ladder["initial_candidate_queue"]
        if row["id"] == "median_of_means_finite_variance_known_result"
    )

    assert candidate["level"] == "L0"
    assert candidate["family"] == "robust_statistics"
    assert candidate["status"] == "active_scored"
    assert candidate["activation_status"] == (
        "full_task_gold_frozen_v1_failed_preflight_transport_and_operator_math_audit"
    )
    evidence = candidate["activation_evidence"]
    assert evidence["gold_frozen_before_first_runtime_model_call"] is True
    assert evidence["hidden_gold_manifest_validated"] is True
    assert evidence["first_runtime_model_call_occurred"] is True
    assert evidence["fresh_live_runs"] == 1
    assert evidence["fresh_v1_runtime_status"] == "FAILED"
    assert evidence["fresh_v1_runtime_research_eval"] == "0/1 complete"
    assert len(evidence["fresh_v1_runtime_manifest_sha256"]) == 64
    assert evidence["fresh_v1_independent_preflight_verdict"] == "not produced"
    assert evidence["fresh_v1_algorithm_executions"] == 0
    assert evidence["fresh_v1_simulation_executions"] == 0
    assert evidence["fresh_v1_formalizer_executions"] == 0
    assert evidence["operator_audit_disposition"] == "FAILED_CLOSED"
    assert Path(evidence["operator_audit_path"]).is_file()
    assert evidence["algorithm_reference_checks"] == "8/8"
    assert evidence["algorithm_negative_variants_rejected"] == 4
    assert evidence["empirical_reference_dgps_passed"] == 3
    assert evidence["empirical_reference_replicates_per_dgp"] == 12000
    assert evidence["semantic_calibration_cases"] == 11
    assert evidence["semantic_calibration_cases_correct"] == 11
    assert evidence["model_draw_resampling_blocked"] is True
    assert evidence["full_task_passed"] is False
    assert candidate["task_intent"] == {
        "source_replication": "not_applicable",
        "theory": "required",
        "scientific_code": "required",
        "empirical": "required",
        "formal": "not_applicable",
        "novelty": "not_applicable",
        "unresolved_gaps": "required",
    }
    for field in (
        "source_snapshot_hash",
        "source_manifest_sha256",
        "gold_manifest_sha256",
        "gold_descriptor_hash",
    ):
        assert len(candidate[field]) == 64
    visible_path = Path(candidate["visible_questions_path"])
    assert visible_path.is_file()
    assert hashlib.sha256(visible_path.read_bytes()).hexdigest() == (
        evidence["visible_questions_sha256"]
    )
    question = json.loads(visible_path.read_text(encoding="utf-8"))["questions"][0]
    assert question["id"] == candidate["id"]
    assert "authoritative Markdown/LaTeX theory workspace" in question["description"]
    assert "est_median_of_means" in question["description"]
    assert "Lean formalization" in question["description"]

    runtime_visible = json.dumps(
        {"candidate": candidate, "question": question}, sort_keys=True
    )
    for hidden_name in (
        "gold_manifest.json",
        "reference_estimator.py",
        "negative_sample_mean.py",
        "negative_radius.py",
        "negative_failure_exponent.py",
        "negative_block_layout.py",
        "semantic_reference.md",
        "semantic_calibration_cases.json",
    ):
        assert hidden_name not in runtime_visible


def test_benjamini_hochberg_l0_single_live_draw_is_frozen_failed() -> None:
    ladder = _load_ladder()
    candidate = next(
        row
        for row in ladder["initial_candidate_queue"]
        if row["id"] == "benjamini_hochberg_independence_known_result"
    )

    assert candidate["level"] == "L0"
    assert candidate["family"] == "multiple_testing"
    assert candidate["status"] == "active_scored"
    assert candidate["activation_status"] == (
        "full_task_gold_frozen_v1_failed_theory_index_anchor_transport"
    )
    evidence = candidate["activation_evidence"]
    assert evidence["gold_frozen_before_first_runtime_model_call"] is True
    assert evidence["hidden_gold_manifest_validated"] is True
    assert evidence["first_runtime_model_call_occurred"] is True
    assert evidence["fresh_live_runs"] == 1
    assert evidence["algorithm_reference_checks"] == "10/10"
    assert evidence["algorithm_negative_variants_rejected"] == 4
    assert evidence["empirical_reference_dgps_passed"] == 3
    assert evidence["empirical_reference_replicates_per_dgp"] == 12000
    assert evidence["semantic_calibration_cases"] == 11
    assert evidence["semantic_calibration_cases_correct"] == 11
    assert evidence["runtime_status"] == "BLOCKED"
    assert evidence["runtime_terminal_classification"] == (
        "theory_developer_reported_gap"
    )
    assert evidence["research_eval_complete"] is False
    assert evidence["hidden_gold_tasks_evaluated"] == 0
    assert evidence["runtime_traces"] == 3
    assert evidence["theory_model_turns"] == 10
    assert evidence["theory_tool_executions"] == 10
    assert evidence["theory_workspace_submissions"] == 5
    assert evidence["authoritative_theory_documents"] == 1
    assert evidence["theory_document_lines"] == 192
    assert evidence["theory_document_bytes"] == 10051
    assert evidence["accepted_theory_packet"] is False
    assert evidence["algorithm_executions"] == 0
    assert evidence["simulation_executions"] == 0
    assert evidence["formalizer_executions"] == 0
    assert evidence["operator_audit"] == (
        "docs/operator_audits/benjamini_hochberg_l0_v1.md"
    )
    assert evidence["post_run_shared_fix_verification"] == "761 passed"
    assert evidence["model_draw_resampling_blocked"] is True
    assert evidence["full_task_passed"] is False
    for field in (
        "runtime_manifest_sha256",
        "hidden_gold_report_sha256",
        "theory_document_sha256",
    ):
        assert len(evidence[field]) == 64
    assert candidate["task_intent"] == {
        "source_replication": "not_applicable",
        "theory": "required",
        "scientific_code": "required",
        "empirical": "required",
        "formal": "optional",
        "novelty": "not_applicable",
        "unresolved_gaps": "required",
    }
    for field in (
        "source_snapshot_hash",
        "source_manifest_sha256",
        "gold_manifest_sha256",
        "gold_descriptor_hash",
    ):
        assert len(candidate[field]) == 64
    visible_path = Path(candidate["visible_questions_path"])
    assert visible_path.is_file()
    assert hashlib.sha256(visible_path.read_bytes()).hexdigest() == (
        evidence["visible_questions_sha256"]
    )
    question = json.loads(visible_path.read_text(encoding="utf-8"))["questions"][0]
    assert question["id"] == candidate["id"]
    assert "authoritative Markdown/LaTeX theory workspace" in question["description"]
    assert "est_benjamini_hochberg" in question["description"]
    assert "Lean formalization is optional" in question["description"]

    runtime_visible = json.dumps(
        {"candidate": candidate, "question": question}, sort_keys=True
    )
    for hidden_name in (
        "gold_manifest.json",
        "reference_estimator.py",
        "negative_step_down.py",
        "negative_strict_boundary.py",
        "negative_sorted_output.py",
        "negative_unadjusted_values.py",
        "semantic_reference.md",
        "semantic_calibration_cases.json",
    ):
        assert hidden_name not in runtime_visible


def test_wilson_score_l0_single_live_draw_is_frozen_failed() -> None:
    ladder = _load_ladder()
    candidate = next(
        row
        for row in ladder["initial_candidate_queue"]
        if row["id"] == "wilson_score_binomial_interval_known_result"
    )

    assert candidate["level"] == "L0"
    assert candidate["family"] == "binomial_inference"
    assert candidate["status"] == "active_scored"
    assert candidate["activation_status"] == (
        "full_task_gold_frozen_v1_failed_preflight_transport_and_operator_math_audit"
    )
    evidence = candidate["activation_evidence"]
    assert evidence["gold_frozen_before_first_runtime_model_call"] is True
    assert evidence["hidden_gold_manifest_validated"] is True
    assert evidence["first_runtime_model_call_occurred"] is True
    assert evidence["fresh_live_runs"] == 1
    assert evidence["algorithm_reference_checks"] == "10/10"
    assert evidence["algorithm_negative_variants_rejected"] == 4
    assert evidence["empirical_reference_dgps_passed"] == 3
    assert evidence["empirical_reference_replicates_per_dgp"] == 12000
    assert evidence["semantic_calibration_cases"] == 11
    assert evidence["semantic_calibration_cases_correct"] == 11
    assert evidence["semantic_reference_claims"] == 8
    assert evidence["runtime_status"] == "BLOCKED"
    assert evidence["runtime_terminal_classification"] == (
        "architect_theory_execution_preflight_packet_validation_failed"
    )
    assert evidence["research_eval_complete"] is False
    assert evidence["hidden_gold_tasks_evaluated"] == 0
    assert evidence["runtime_traces"] == 4
    assert evidence["theory_model_turns"] == 11
    assert evidence["theory_tool_executions"] == 11
    assert evidence["theory_workspace_submissions"] == 3
    assert evidence["theory_workspace_checkpoint_committed"] is True
    assert evidence["authoritative_theory_documents"] == 1
    assert evidence["theory_document_lines"] == 347
    assert evidence["theory_document_bytes"] == 13964
    assert evidence["independent_theory_preflight_accepted"] is False
    assert evidence["accepted_theory_packet"] is False
    assert evidence["algorithm_executions"] == 0
    assert evidence["simulation_executions"] == 0
    assert evidence["formalizer_executions"] == 0
    assert evidence["operator_audit"] == (
        "docs/operator_audits/wilson_score_l0_v1.md"
    )
    assert evidence["post_run_shared_fix_commit"] == (
        "fe65d1f3fb3c5bbdb58e040c15e11fcc8bdc2fc8"
    )
    assert evidence["post_run_shared_fix_verification"] == "763 passed"
    assert evidence["model_draw_resampling_blocked"] is True
    assert evidence["full_task_passed"] is False
    for field in (
        "runtime_manifest_sha256",
        "hidden_gold_report_sha256",
        "runtime_failure_summary_sha256",
        "theory_document_sha256",
    ):
        assert len(evidence[field]) == 64
    assert Path(evidence["operator_audit"]).is_file()
    assert candidate["task_intent"] == {
        "source_replication": "not_applicable",
        "theory": "required",
        "scientific_code": "required",
        "empirical": "required",
        "formal": "optional",
        "novelty": "not_applicable",
        "unresolved_gaps": "required",
    }
    for field in (
        "source_snapshot_hash",
        "source_manifest_sha256",
        "gold_manifest_sha256",
        "gold_descriptor_hash",
    ):
        assert len(candidate[field]) == 64
    visible_path = Path(candidate["visible_questions_path"])
    assert visible_path.is_file()
    assert hashlib.sha256(visible_path.read_bytes()).hexdigest() == (
        evidence["visible_questions_sha256"]
    )
    question = json.loads(visible_path.read_text(encoding="utf-8"))["questions"][0]
    assert question["id"] == candidate["id"]
    assert "authoritative Markdown/LaTeX theory workspace" in question["description"]
    assert "est_wilson_score_interval" in question["description"]
    assert "Lean formalization is optional" in question["description"]

    runtime_visible = json.dumps(
        {"candidate": candidate, "question": question}, sort_keys=True
    )
    for hidden_name in (
        "gold_manifest.json",
        "reference_estimator.py",
        "negative_wald.py",
        "negative_missing_denominator.py",
        "negative_one_sided_quantile.py",
        "negative_linear_adjustment.py",
        "semantic_reference.md",
        "semantic_calibration_cases.json",
    ):
        assert hidden_name not in runtime_visible


def test_jackknife_mean_l0_freezes_invalid_design_and_terminal_budget_block() -> None:
    ladder = _load_ladder()
    candidate = next(
        row
        for row in ladder["initial_candidate_queue"]
        if row["id"] == "jackknife_sample_mean_variance_known_result"
    )

    assert candidate["level"] == "L0"
    assert candidate["family"] == "resampling"
    assert candidate["status"] == "active_scored"
    assert candidate["activation_status"] == (
        "fresh_live_v1_invalid_evaluation_design_and_theory_terminal_budget_blocked"
    )
    evidence = candidate["activation_evidence"]
    assert evidence["hidden_gold_manifest_validated"] is True
    assert evidence["gold_frozen_before_first_runtime_model_call"] is True
    assert evidence["first_runtime_model_call_occurred"] is True
    assert evidence["fresh_live_runs"] == 1
    assert evidence["algorithm_reference_checks"] == "10/10"
    assert evidence["algorithm_negative_variants_rejected"] == 4
    assert evidence["empirical_reference_dgps_passed"] == 3
    assert evidence["empirical_reference_identity_agreements"] == 12000
    assert evidence["semantic_calibration_cases"] == 12
    assert evidence["semantic_calibration_cases_correct"] == 12
    assert evidence["semantic_reference_claims"] == 7
    assert evidence["fresh_live_runtime_status"] == "BLOCKED"
    assert evidence["fresh_live_terminal_classification"] == (
        "theory_developer_packet_validation_failed"
    )
    assert evidence["fresh_live_runtime_traces"] == 3
    assert evidence["fresh_live_theory_model_turns"] == 11
    assert evidence["fresh_live_theory_tool_executions"] == 12
    assert evidence["fresh_live_theory_document_lines"] == 240
    assert evidence["fresh_live_theory_document_bytes"] == 8521
    assert evidence["fresh_live_last_write_workspace_valid"] is True
    assert evidence["fresh_live_last_write_checkpoint_commit_ready"] is True
    assert evidence["fresh_live_last_write_model_tool_calls_remaining"] == 0
    assert evidence["fresh_live_last_write_standard_turns_remaining"] == 1
    assert evidence["fresh_live_next_model_tool_blocked_before_execution"] is True
    assert evidence["fresh_live_independent_theory_review_attempted"] is False
    assert evidence["fresh_live_accepted_theory_packet"] is False
    assert evidence["fresh_live_algorithm_executions"] == 0
    assert evidence["fresh_live_simulation_executions"] == 0
    assert evidence["fresh_live_formalizer_executions"] == 0
    assert evidence["evaluator_design_valid"] is False
    assert evidence["hidden_algorithm_failure_attribution_allowed"] is False
    assert evidence["post_run_shared_mechanism_fix_commit"] == (
        "0d8a01e5a2af00a3223df413f1909a11a56e6997"
    )
    assert evidence["model_draw_resampling_blocked"] is True
    assert evidence["formalization_requirement"] == "not_applicable"
    assert evidence["full_task_passed"] is False
    for field in (
        "fresh_live_runtime_manifest_sha256",
        "fresh_live_hidden_gold_report_sha256",
        "fresh_live_runtime_failure_summary_sha256",
        "fresh_live_theory_document_sha256",
    ):
        assert len(evidence[field]) == 64
    assert Path(evidence["operator_audit_path"]).is_file()
    assert candidate["task_intent"] == {
        "source_replication": "not_applicable",
        "theory": "required",
        "scientific_code": "required",
        "empirical": "required",
        "formal": "not_applicable",
        "novelty": "not_applicable",
        "unresolved_gaps": "required",
    }
    for field in (
        "source_snapshot_hash",
        "source_manifest_sha256",
        "gold_manifest_sha256",
        "gold_descriptor_hash",
    ):
        assert len(candidate[field]) == 64
    visible_path = Path(candidate["visible_questions_path"])
    assert hashlib.sha256(visible_path.read_bytes()).hexdigest() == (
        evidence["visible_questions_sha256"]
    )
    question = json.loads(visible_path.read_text(encoding="utf-8"))["questions"][0]
    assert question["id"] == candidate["id"]
    assert "authoritative Markdown/LaTeX theory workspace" in question["description"]
    assert "est_jackknife_mean_variance" in question["description"]
    assert "Lean formalization is not applicable" in question["description"]

    runtime_visible = json.dumps(
        {"candidate": candidate, "question": question}, sort_keys=True
    )
    for hidden_name in (
        "gold_manifest.json",
        "reference_estimator.py",
        "negative_wrong_prefactor.py",
        "negative_wrong_delete_denominator.py",
        "negative_returns_sample_variance.py",
        "negative_duplicate_replicate.py",
        "semantic_reference.md",
        "semantic_calibration_cases.json",
    ):
        assert hidden_name not in runtime_visible


def test_ar1_ols_l0_freezes_consumed_collaboration_failure_without_resampling() -> None:
    ladder = _load_ladder()
    candidate = next(
        row
        for row in ladder["initial_candidate_queue"]
        if row["id"] == "stationary_ar1_zero_mean_ols_known_result"
    )

    assert candidate["level"] == "L0"
    assert candidate["family"] == "time_series"
    assert candidate["status"] == "active_scored"
    assert candidate["activation_status"] == "full_task_gold_frozen_consumed_closed"
    evidence = candidate["activation_evidence"]
    assert evidence["gold_frozen_before_first_runtime_model_call"] is True
    assert evidence["first_runtime_model_call_occurred"] is True
    assert evidence["fresh_live_runs"] == 1
    assert evidence["fresh_live_runtime_status"] == "MAX_ITERATIONS_REACHED"
    assert evidence["fresh_live_runtime_terminal_kind"] == (
        "budget_exhausted_with_pending_next_task"
    )
    assert evidence["fresh_live_theory_checkpoint_committed"] is True
    assert evidence["fresh_live_independent_theory_review_accepted"] is True
    assert evidence["fresh_live_algorithm_execution_passed"] is True
    assert evidence["fresh_live_algorithm_semantic_review_accepted"] is True
    assert evidence["fresh_live_metric_protocol_preexecution_review_accepted"] is True
    assert evidence["fresh_live_simulation_accepted"] is False
    assert evidence["fresh_live_critic_accepted"] is False
    assert evidence["fresh_live_formalizer_executions"] == 0
    assert evidence["model_draw_resampling_blocked"] is True
    assert evidence["formalization_requirement"] == "not_applicable"
    assert evidence["full_task_passed"] is False
    assert Path(evidence["operator_audit_path"]).is_file()
    for field in (
        "fresh_live_runtime_manifest_sha256",
        "fresh_live_hidden_gold_report_sha256",
        "fresh_live_runtime_failure_summary_sha256",
        "fresh_live_runtime_completion_summary_sha256",
    ):
        assert len(evidence[field]) == 64
    assert candidate["task_intent"] == {
        "source_replication": "not_applicable",
        "theory": "required",
        "scientific_code": "required",
        "empirical": "required",
        "formal": "not_applicable",
        "novelty": "not_applicable",
        "unresolved_gaps": "required",
    }


def test_fisher_z_l0_is_consumed_closed_after_one_runtime_draw() -> None:
    ladder = _load_ladder()
    candidate = next(
        row
        for row in ladder["initial_candidate_queue"]
        if row["id"] == "bivariate_normal_fisher_z_known_result"
    )

    assert candidate["level"] == "L0"
    assert candidate["family"] == "correlation_multivariate"
    assert candidate["status"] == "active_scored"
    assert candidate["activation_status"] == "full_task_gold_consumed_closed"
    evidence = candidate["activation_evidence"]
    assert evidence["hidden_gold_manifest_validated"] is True
    assert evidence["gold_frozen_before_first_runtime_model_call"] is True
    assert evidence["first_runtime_model_call_occurred"] is True
    assert evidence["fresh_live_runs"] == 1
    assert evidence["algorithm_reference_contract_checks"] == "12/12"
    assert evidence["algorithm_negative_variants_rejected"] == 4
    assert evidence["empirical_reference_dgps_passed"] == 3
    assert evidence["empirical_reference_identity_agreements"] == 9000
    assert evidence["semantic_calibration_cases"] == 12
    assert evidence["semantic_calibration_cases_correct"] == 12
    assert evidence["semantic_reference_claims"] == 10
    assert evidence["fresh_live_runtime_status"] == "BLOCKED"
    assert evidence["fresh_live_runtime_terminal_kind"] == "blocked"
    assert evidence["fresh_live_runtime_terminal_classification"] == (
        "architect_metric_requirement_packet_validation_failed"
    )
    assert evidence["fresh_live_theory_checkpoint_committed"] is True
    assert evidence["fresh_live_independent_theory_review_accepted"] is True
    assert evidence["fresh_live_hidden_theory_semantic_passed"] is False
    assert evidence["fresh_live_algorithm_execution_passed"] is True
    assert evidence["fresh_live_algorithm_semantic_review_accepted"] is True
    assert evidence["fresh_live_metric_protocol_preexecution_review_accepted"] is False
    assert evidence["fresh_live_simulation_accepted"] is False
    assert evidence["fresh_live_critic_accepted"] is False
    assert evidence["fresh_live_formalizer_executions"] == 0
    assert evidence["model_draw_resampling_blocked"] is True
    assert evidence["formalization_requirement"] == "not_applicable"
    assert evidence["full_task_passed"] is False
    assert evidence["activation_commit"] == (
        "6b871aa078f61e08c495cdf1753c40c3b9867f43"
    )
    for field in (
        "source_snapshot_hash",
        "source_manifest_sha256",
        "gold_manifest_sha256",
        "gold_descriptor_hash",
    ):
        assert len(candidate[field]) == 64
    for field in (
        "fresh_live_runtime_manifest_sha256",
        "fresh_live_hidden_gold_report_sha256",
        "fresh_live_runtime_failure_summary_sha256",
        "fresh_live_runtime_completion_summary_sha256",
    ):
        assert len(evidence[field]) == 64
    assert Path(evidence["operator_audit_path"]).is_file()
    visible_path = Path(candidate["visible_questions_path"])
    assert hashlib.sha256(visible_path.read_bytes()).hexdigest() == (
        evidence["visible_questions_sha256"]
    )
    question = json.loads(visible_path.read_text(encoding="utf-8"))["questions"][0]
    assert question["id"] == candidate["id"]
    assert "authoritative Markdown/LaTeX derivation" in question["description"]
    assert "est_fisher_pearson_z" in question["description"]
    assert "Lean formalization is not applicable" in question["description"]
    assert candidate["task_intent"] == question["task_intent"]

    runtime_visible = json.dumps(
        {"candidate": candidate, "question": question}, sort_keys=True
    )
    for hidden_name in (
        "gold_manifest.json",
        "reference_estimator.py",
        "negative_uncentered_correlation.py",
        "negative_double_fisher_z.py",
        "negative_clipped_correlation.py",
        "negative_asymptotic_standard_error.py",
        "semantic_reference.md",
        "semantic_calibration_cases.json",
    ):
        assert hidden_name not in runtime_visible


def test_paired_ratio_l0_draw_is_consumed_and_hash_bound() -> None:
    ladder = _load_ladder()
    candidate = next(
        row
        for row in ladder["initial_candidate_queue"]
        if row["id"] == "paired_ratio_of_means_delta_method_known_result"
    )

    assert candidate["level"] == "L0"
    assert candidate["family"] == "ratio_metrics"
    assert candidate["status"] == "active_scored"
    assert candidate["activation_status"] == (
        "full_task_gold_frozen_v1_failed_shared_terminal_disposition_budget"
    )
    evidence = candidate["activation_evidence"]
    assert evidence["hidden_gold_manifest_validated"] is True
    assert evidence["gold_frozen_before_first_runtime_model_call"] is True
    assert evidence["first_runtime_model_call_occurred"] is True
    assert evidence["fresh_live_runs"] == 1
    assert evidence["algorithm_reference_contract_checks"] == "14/14"
    assert evidence["algorithm_negative_variants_rejected"] == 4
    assert evidence["empirical_reference_dgps_passed"] == 3
    assert evidence["empirical_reference_identity_agreements"] == 9000
    assert evidence["semantic_calibration_cases"] == 12
    assert evidence["semantic_calibration_cases_correct"] == 12
    assert evidence["semantic_reference_claims"] == 10
    assert evidence["activation_commit"] == (
        "bc5eb28c6e09ddffda15e4d6c0d32108cea2c273"
    )
    assert evidence["activation_push_confirmed_on_work_branch_and_main"] is True
    assert evidence["runtime_status"] == "BLOCKED"
    assert evidence["runtime_terminal_classification"] == (
        "theory_developer_packet_validation_failed"
    )
    assert evidence["final_workspace_valid"] is True
    assert evidence["final_checkpoint_commit_ready"] is True
    assert evidence["final_terminal_tool_call_returned_by_model"] is True
    assert evidence["final_terminal_tool_call_executed_by_runtime"] is False
    assert evidence["independently_accepted_theory_packet"] is False
    assert evidence["hidden_theory_execution_attempted"] is False
    assert evidence["hidden_algorithm_execution_attempted"] is False
    assert evidence["hidden_empirical_execution_attempted"] is False
    assert evidence["post_run_shared_mechanism_fix_commit"] == (
        "3bfa8daa378480fdd1e11acae3b229abf3abd3d7"
    )
    assert evidence["model_draw_resampling_blocked"] is True
    assert evidence["formalization_requirement"] == "not_applicable"
    assert evidence["full_task_passed"] is False
    for field in (
        "source_snapshot_hash",
        "source_manifest_sha256",
        "gold_manifest_sha256",
        "gold_descriptor_hash",
    ):
        assert len(candidate[field]) == 64

    visible_path = Path(candidate["visible_questions_path"])
    assert hashlib.sha256(visible_path.read_bytes()).hexdigest() == (
        evidence["visible_questions_sha256"]
    )
    question = json.loads(visible_path.read_text(encoding="utf-8"))["questions"][0]
    assert question["id"] == candidate["id"]
    assert "authoritative Markdown/LaTeX derivation" in question["description"]
    assert "est_paired_ratio_delta" in question["description"]
    assert "Lean formalization is not applicable" in question["description"]
    assert candidate["task_intent"] == question["task_intent"]

    runtime_visible = json.dumps(
        {"candidate": candidate, "question": question}, sort_keys=True
    )
    for hidden_name in (
        "gold_manifest.json",
        "reference_estimator.py",
        "negative_mean_of_ratios.py",
        "negative_omit_covariance.py",
        "negative_population_normalization.py",
        "negative_standard_error_scaling.py",
        "semantic_reference.md",
        "semantic_calibration_cases.json",
    ):
        assert hidden_name not in runtime_visible


def test_scalar_control_variate_l0_frozen_draw_is_consumed_and_closed() -> None:
    ladder = _load_ladder()
    candidate = next(
        row
        for row in ladder["initial_candidate_queue"]
        if row["id"] == "scalar_control_variate_known_result"
    )

    assert candidate["level"] == "L0"
    assert candidate["family"] == "monte_carlo_variance_reduction"
    assert candidate["status"] == "active_scored"
    assert candidate["activation_status"] == (
        "full_task_gold_frozen_v1_failed_shared_simulation_prompt_artifact_expansion"
    )
    evidence = candidate["activation_evidence"]
    assert evidence["hidden_gold_manifest_validated"] is True
    assert evidence["gold_frozen_before_first_runtime_model_call"] is True
    assert evidence["first_runtime_model_call_occurred"] is True
    assert evidence["fresh_live_runs"] == 1
    assert evidence["algorithm_reference_contract_checks"] == "13/13"
    assert evidence["algorithm_negative_variants_rejected"] == 4
    assert evidence["empirical_reference_dgps_passed"] == 3
    assert evidence["empirical_reference_identity_agreements"] == 9000
    assert evidence["semantic_calibration_cases"] == 12
    assert evidence["semantic_calibration_cases_correct"] == 12
    assert evidence["semantic_reference_claims"] == 10
    assert evidence["activation_commit"] == (
        "e1e1f975322b4eaafc2809a112ac30b445753aa5"
    )
    assert evidence["activation_push_confirmed_on_work_branch_and_main"] is True
    assert evidence["runtime_status"] == "BLOCKED"
    assert evidence["runtime_traces"] == 10
    assert evidence["runtime_task_handoffs"] == 9
    assert evidence["theory_checkpoint_committed"] is True
    assert evidence["independent_theory_preflight_accepted"] is True
    assert evidence["generated_algorithm_executions"] == 1
    assert evidence["independent_algorithm_semantic_review_accepted"] is True
    assert evidence["independent_metric_protocol_accepted"] is True
    assert evidence["generated_simulation_executions"] == 0
    assert evidence["hidden_theory_semantic_status"] == "INCONCLUSIVE"
    assert evidence["hidden_algorithm_acceptance_checks_passed"] is False
    assert evidence["hidden_empirical_checks_passed"] is True
    assert evidence["post_run_shared_mechanism_fix_commit"] == (
        "dd3cb36c236e360c52f397998464997b0c08c7c8"
    )
    assert evidence["model_draw_resampling_blocked"] is True
    assert evidence["formalization_requirement"] == "not_applicable"
    assert evidence["full_task_passed"] is False
    for field in (
        "source_snapshot_hash",
        "source_manifest_sha256",
        "gold_manifest_sha256",
        "gold_descriptor_hash",
    ):
        assert len(candidate[field]) == 64

    visible_path = Path(candidate["visible_questions_path"])
    assert hashlib.sha256(visible_path.read_bytes()).hexdigest() == (
        evidence["visible_questions_sha256"]
    )
    question = json.loads(visible_path.read_text(encoding="utf-8"))["questions"][0]
    assert question["id"] == candidate["id"]
    assert "authoritative Markdown/LaTeX derivation" in question["description"]
    assert "est_scalar_control_variate" in question["description"]
    assert "Lean formalization is not applicable" in question["description"]
    assert candidate["task_intent"] == question["task_intent"]

    runtime_visible = json.dumps(
        {"candidate": candidate, "question": question}, sort_keys=True
    )
    for hidden_name in (
        "gold_manifest.json",
        "reference_estimator.py",
        "negative_wrong_adjustment_sign.py",
        "negative_population_normalization.py",
        "negative_omit_covariance.py",
        "negative_standard_error_scaling.py",
        "semantic_reference.md",
        "semantic_calibration_cases.json",
    ):
        assert hidden_name not in runtime_visible


def test_pearson_multinomial_gof_l0_frozen_draw_is_consumed_and_closed() -> None:
    ladder = _load_ladder()
    candidate = next(
        row
        for row in ladder["initial_candidate_queue"]
        if row["id"] == "pearson_multinomial_gof_known_result"
    )

    assert ladder["model_policy"] == {
        "provider": "anthropic",
        "live_evaluation_model_tier": "haiku",
        "live_evaluation_model": "claude-haiku-4-5-20251001",
        "sonnet_live_calls_allowed": False,
        "opus_live_calls_allowed": False,
        "automatic_tier_escalation_allowed": False,
    }
    assert candidate["level"] == "L0"
    assert candidate["family"] == "categorical_inference"
    assert candidate["status"] == "active_scored"
    assert candidate["activation_status"] == "full_task_gold_frozen_consumed_closed"
    evidence = candidate["activation_evidence"]
    assert evidence["hidden_gold_manifest_validated"] is True
    assert evidence["gold_frozen_before_first_runtime_model_call"] is True
    assert evidence["first_runtime_model_call_occurred"] is True
    assert evidence["fresh_live_runs"] == 1
    assert evidence["fresh_live_terminal_status"] == "BLOCKED"
    assert evidence["fresh_live_terminal_classification"] == (
        "generated_code_semantic_review_input_invalid"
    )
    assert evidence["fresh_live_outer_traces"] == 9
    assert evidence["fresh_live_generated_algorithm_executions"] == 1
    assert evidence["fresh_live_generated_simulation_executions"] == 1
    assert evidence["fresh_live_runtime_metric_contracts_passed"] == "8/8"
    assert evidence["fresh_live_simulation_estimator_invocations"] == 75006
    assert evidence["fresh_live_theory_structural_checks_passed"] is True
    assert evidence["fresh_live_theory_semantic_status"] == "INCONCLUSIVE"
    assert evidence["fresh_live_algorithm_harness_execution_passed"] is True
    assert evidence["fresh_live_algorithm_acceptance_checks_passed"] is False
    assert evidence["fresh_live_empirical_checks_passed"] is True
    assert evidence["fresh_live_empirical_estimator_invocations"] == 15000
    assert evidence["post_run_shared_mechanism_commit"] == "f4fe83ed"
    assert evidence["model_draw_resampling_blocked"] is True
    assert evidence["formalization_requirement"] == "not_applicable"
    assert evidence["full_task_passed"] is False
    for field in (
        "source_snapshot_hash",
        "source_manifest_sha256",
        "gold_manifest_sha256",
        "gold_descriptor_hash",
    ):
        assert len(candidate[field]) == 64

    visible_path = Path(candidate["visible_questions_path"])
    assert hashlib.sha256(visible_path.read_bytes()).hexdigest() == (
        evidence["visible_questions_sha256"]
    )
    question = json.loads(visible_path.read_text(encoding="utf-8"))["questions"][0]
    assert question["id"] == candidate["id"]
    assert "authoritative Markdown/LaTeX derivation" in question["description"]
    assert "est_multinomial_pearson_gof" in question["description"]
    assert "Lean formalization is not applicable" in question["description"]
    assert candidate["task_intent"] == question["task_intent"]

    runtime_visible = json.dumps(
        {"candidate": candidate, "question": question}, sort_keys=True
    )
    for hidden_name in (
        "gold_manifest.json",
        "reference_estimator.py",
        "negative_absolute_residual.py",
        "negative_pvalue_cdf.py",
        "negative_uniform_null.py",
        "negative_wrong_df.py",
        "semantic_reference.md",
        "semantic_calibration_cases.json",
    ):
        assert hidden_name not in runtime_visible


def test_exponential_rate_mle_l0_authority_is_consumed_after_one_draw() -> None:
    ladder = _load_ladder()
    candidate = next(
        row
        for row in ladder["initial_candidate_queue"]
        if row["id"] == "exponential_rate_mle_pivot_known_result"
    )

    assert candidate["level"] == "L0"
    assert candidate["family"] == "lifetime_rate_inference"
    assert candidate["status"] == "active_scored"
    assert (
        candidate["activation_status"]
        == "full_task_gold_frozen_consumed_closed"
    )
    evidence = candidate["activation_evidence"]
    assert evidence["hidden_gold_manifest_validated"] is True
    assert evidence["gold_frozen_before_first_runtime_model_call"] is True
    assert evidence["activation_commit"] == (
        "2097c3102b7a4b936a1a0669bdb5e4f8f716f5ba"
    )
    assert evidence["activation_push_confirmed_on_work_branch_and_main"] is True
    assert evidence["first_runtime_model_call_occurred"] is True
    assert evidence["fresh_live_runs"] == 1
    assert evidence["fresh_live_terminal_status"] == "ACCEPTED"
    assert evidence["fresh_live_outer_traces"] == 11
    assert evidence["fresh_live_task_handoffs"] == 10
    assert evidence["fresh_live_client_tool_model_turns"] == 24
    assert evidence["fresh_live_generated_algorithm_executions"] == 1
    assert evidence["fresh_live_generated_simulation_executions"] == 1
    assert evidence["fresh_live_runtime_metric_contracts_passed"] == "8/8"
    assert evidence["fresh_live_simulation_estimator_invocations"] == 65020
    assert evidence["fresh_live_research_eval_ready"] is True
    assert evidence["fresh_live_theory_structural_checks_passed"] is True
    assert evidence["fresh_live_theory_semantic_status"] == "FAIL"
    assert evidence["fresh_live_theory_gold_validated"] is False
    assert evidence["fresh_live_algorithm_harness_execution_passed"] is True
    assert evidence["fresh_live_algorithm_acceptance_checks_passed"] is False
    assert evidence["fresh_live_algorithm_acceptance_checks"] == "5/7"
    assert evidence["fresh_live_algorithm_invalid_requests_rejected"] is False
    assert evidence["fresh_live_empirical_checks_passed"] is True
    assert evidence["fresh_live_empirical_acceptance_checks"] == "8/8"
    assert evidence["fresh_live_empirical_estimator_invocations"] == 15000
    assert evidence["post_run_shared_mechanism_change"] == "none"
    assert evidence["algorithm_reference_contract_checks"] == "11/11"
    assert evidence["algorithm_negative_variants_rejected"] == 4
    assert evidence["empirical_reference_dgps_passed"] == 3
    assert evidence["empirical_reference_identity_agreements"] == 15000
    assert evidence["semantic_calibration_cases"] == 12
    assert evidence["semantic_calibration_cases_correct"] == 12
    assert evidence["semantic_reference_claims"] == 10
    assert evidence["semantic_reference_candidate_passed"] is True
    assert evidence["model_draw_resampling_blocked"] is True
    assert evidence["formalization_requirement"] == "not_applicable"
    assert evidence["full_task_passed"] is False
    for field in (
        "source_snapshot_hash",
        "source_manifest_sha256",
        "gold_manifest_sha256",
        "gold_descriptor_hash",
    ):
        assert len(candidate[field]) == 64

    visible_path = Path(candidate["visible_questions_path"])
    assert hashlib.sha256(visible_path.read_bytes()).hexdigest() == (
        evidence["visible_questions_sha256"]
    )
    question = json.loads(visible_path.read_text(encoding="utf-8"))["questions"][0]
    assert question["id"] == candidate["id"]
    assert "authoritative Markdown/LaTeX derivation" in question["description"]
    assert "est_exponential_rate_interval" in question["description"]
    assert "Lean formalization is not applicable" in question["description"]
    assert candidate["task_intent"] == question["task_intent"]

    runtime_visible = json.dumps(
        {"candidate": candidate, "question": question}, sort_keys=True
    )
    for hidden_name in (
        "gold_manifest.json",
        "reference_estimator.py",
        "negative_scale_parameter.py",
        "negative_unbiased_as_mle.py",
        "negative_missing_factor_two.py",
        "negative_wald_interval.py",
        "semantic_reference.md",
        "semantic_calibration_cases.json",
    ):
        assert hidden_name not in runtime_visible


def test_its_time_l1_draw_is_consumed_without_posthoc_rescore() -> None:
    ladder = _load_ladder()
    candidate = next(
        row
        for row in ladder["initial_candidate_queue"]
        if row["id"] == "its_time_niv_figure5_public_replication"
    )

    assert candidate["level"] == "L1"
    assert candidate["family"] == "instrumental_time_series"
    assert candidate["status"] == "consumed_scored"
    assert candidate["activation_status"] == (
        "fresh_live_v1_blocked_before_source_replication"
    )
    assert candidate["gold_runtime_visibility"] == "evaluator_only_after_runtime"
    evidence = candidate["activation_evidence"]
    assert evidence["hidden_gold_manifest_validated"] is True
    assert evidence["hidden_gold_activated_before_first_product_model_call"] is True
    assert evidence["preactivation_product_model_calls"] == 0
    assert evidence["fresh_live_runs"] == 1
    assert evidence["independent_reruns"] == "4/4"
    assert evidence["source_replication_calibration_cases"] == "8/8"
    assert evidence["semantic_calibration_cases"] == "6/6"
    assert evidence["semantic_calibration_model"] == "claude-haiku-4-5-20251001"
    assert evidence["semantic_calibration_model_calls"] == 2
    assert evidence["dynamic_report_evidence_binding"] is True
    assert evidence["runtime_model"] == "claude-haiku-4-5-20251001"
    assert evidence["runtime_enabled_model_roles"] == 7
    assert evidence["runtime_status"] == "BLOCKED"
    assert evidence["runtime_source_replication_manifest_observed"] is False
    assert evidence["hidden_gold_full_task_result"] == "0/1"
    assert "never rerun" in evidence["post_run_policy"].lower()
    assert evidence["full_task_passed"] is False

    visible_path = Path(candidate["visible_questions_path"])
    assert hashlib.sha256(visible_path.read_bytes()).hexdigest() == (
        evidence["visible_questions_sha256"]
    )
    question = json.loads(visible_path.read_text(encoding="utf-8"))["questions"][0]
    assert question["id"] == candidate["id"]
    assert "operator-pinned source without editing or wrapping it" in question["description"]
    assert question["task_intent"]["formal"] == "not_applicable"
    assert candidate["task_intent"] == question["task_intent"]
    assert question["task_intent"] == {
        "source_replication": "required",
        "theory": "not_applicable",
        "scientific_code": "not_applicable",
        "empirical": "not_applicable",
        "formal": "not_applicable",
        "novelty": "not_applicable",
        "unresolved_gaps": "required",
    }

    runtime_visible = json.dumps(
        {"candidate": candidate, "question": question}, sort_keys=True
    )
    for hidden_name in (
        "gold_manifest.json",
        "hidden_source_replication_harness.py",
        "semantic_reference.md",
        "semantic_rubric.json",
        "semantic_calibration_cases.json",
    ):
        assert hidden_name not in runtime_visible


def test_statlib_formal_l0_draw_is_consumed_without_proof_credit() -> None:
    ladder = _load_ladder()
    candidate = next(
        row
        for row in ladder["initial_candidate_queue"]
        if row["id"]
        == "statlib_uniform_consistency_implies_consistency_formal_known_result"
    )
    evidence = candidate["activation_evidence"]

    assert candidate["status"] == "active_scored"
    assert candidate["activation_status"] == "fresh_live_v1_hidden_gold_failed"
    assert evidence["gold_frozen_before_first_runtime_model_call"] is True
    assert evidence["first_runtime_model_call_occurred"] is True
    assert evidence["fresh_live_runs"] == 1
    assert evidence["fresh_live_model"] == "claude-haiku-4-5-20251001"
    assert evidence["fresh_live_terminal_status"] == "BLOCKED"
    assert evidence["formalizer_source_updates"] == 24
    assert evidence["formalizer_local_lean_checks"] == 24
    assert evidence["formalizer_formal_rag_calls"] == 10
    assert evidence["kernel_verified_subclaims"] == 0
    assert evidence["full_theorem_proved"] is False
    assert evidence["hidden_evaluator_runs"] == 1
    assert evidence["runtime_manifest_sha256"] == (
        "290038d990aed7fbac801cf0cd1a71296cdd678e5addc0642f896a7b3ee18ea0"
    )
    assert evidence["hidden_gold_report_sha256"] == (
        "1c23f19bd19b23fee40e9f2c0f4e4c857c535ccb99ceb05d0b84d1c09a7e5739"
    )
    assert evidence["hidden_formal_harness_calibration_cases"] == "5/5"
    assert evidence["hidden_gold_kernel_compiled"] is True
    assert evidence["formalization_requirement"] == "required"
    assert candidate["gold_runtime_visibility"] == (
        "evaluator_only_after_runtime"
    )

    visible_path = Path(candidate["visible_questions_path"])
    assert hashlib.sha256(visible_path.read_bytes()).hexdigest() == (
        evidence["visible_questions_sha256"]
    )
    question = json.loads(visible_path.read_text(encoding="utf-8"))["questions"][0]
    contract = question["formal_target_contract"]
    assert question["id"] == candidate["id"]
    assert question["task_intent"] == candidate["task_intent"]
    assert question["task_intent"] == {
        "source_replication": "not_applicable",
        "theory": "not_applicable",
        "scientific_code": "not_applicable",
        "empirical": "not_applicable",
        "formal": "required",
        "novelty": "not_applicable",
        "unresolved_gaps": "required",
    }
    assert contract["proof_visibility"] == "hidden"
    assert contract["declaration_name"] == (
        "AIStatisticianBench.uniformlyConsistent_implies_consistent"
    )
    assert hashlib.sha256(
        contract["lean_source_prefix"].encode("utf-8")
    ).hexdigest() == contract["lean_source_prefix_sha256"]
    assert contract["lean_source_prefix"].rstrip().endswith(":= by")
    assert "tendsto_of_tendsto" not in contract["lean_source_prefix"]
    assert evidence["activation_push_confirmed_on_work_branch_and_main"] is True


def test_score_information_l0_draw_is_consumed_without_review_credit() -> None:
    ladder = _load_ladder()
    candidate = next(
        row
        for row in ladder["initial_candidate_queue"]
        if row["id"] == "scalar_score_information_bound_known_result"
    )
    evidence = candidate["activation_evidence"]

    assert candidate["level"] == "L0"
    assert candidate["family"] == "parametric_information_bounds"
    assert candidate["status"] == "active_scored"
    assert candidate["activation_status"] == (
        "fresh_live_v1_hidden_gold_failed_missing_independent_theory_review"
    )
    assert candidate["gold_runtime_visibility"] == (
        "evaluator_only_after_runtime"
    )
    assert evidence["gold_frozen_before_first_runtime_model_call"] is True
    assert evidence["first_runtime_model_call_occurred"] is True
    assert evidence["fresh_live_runs"] == 1
    assert evidence["fresh_live_model"] == "claude-haiku-4-5-20251001"
    assert evidence["fresh_live_terminal_status"] == "ACCEPTED"
    assert evidence["fresh_live_research_eval_ready"] is True
    assert evidence["fresh_live_runtime_traces"] == 4
    assert evidence["fresh_live_theory_model_turns"] == 10
    assert evidence["fresh_live_theory_checkpoint_committed"] is True
    assert evidence["fresh_live_independent_theory_review_attempted"] is False
    assert evidence["fresh_live_independent_theory_review_accepted"] is False
    assert evidence["fresh_live_critic_accepted"] is True
    assert evidence["fresh_live_hidden_theory_execution_attempted"] is False
    assert evidence["fresh_live_hidden_theory_semantic_execution_attempted"] is False
    assert evidence["runtime_manifest_sha256"] == (
        "7431cd7af241a48712eab0f18128aa23ac5119c0b01d32f2c0ca1439b50f2a8c"
    )
    assert evidence["hidden_gold_report_sha256"] == (
        "908efc77f125bbe44e779bf0a353881ca1b22f57ffbf53fedcc067d346f12e59"
    )
    assert evidence["model_draw_resampling_blocked"] is True
    assert evidence["full_task_passed"] is False
    assert evidence["mechanical_reference_checks"] == "7/7"
    assert evidence["mechanical_negative_variants_rejected"] == 6
    assert evidence["semantic_calibration_cases"] == 12
    assert evidence["semantic_calibration_cases_correct"] == 12
    assert evidence["semantic_reference_claims"] == 8
    assert evidence["semantic_reference_candidate_passed"] is True
    assert evidence["semantic_calibration_model"] == (
        "claude-haiku-4-5-20251001"
    )
    assert evidence["semantic_calibration_model_calls"] == 2
    assert evidence["hidden_gold_manifest_validated"] is True
    assert evidence["authority_binding_commit"] == (
        "c0065450d8d8e0b0b79ca79a74444391f9394857"
    )
    assert evidence[
        "authority_binding_push_confirmed_on_work_branch_and_main"
    ] is True
    assert evidence["post_run_shared_mechanism_fix_commit"] == (
        "9fbbeaba610a48bfbce84a80b4b91802fe301ba9"
    )
    assert evidence["post_run_shared_mechanism_fix_verification"] == (
        "214 focused tests and 860/860 full-suite tests passed"
    )
    assert evidence["formalization_requirement"] == "not_applicable"

    visible_path = Path(candidate["visible_questions_path"])
    assert hashlib.sha256(visible_path.read_bytes()).hexdigest() == (
        evidence["visible_questions_sha256"]
    )
    question = json.loads(visible_path.read_text(encoding="utf-8"))["questions"][0]
    assert question["id"] == candidate["id"]
    assert question["task_intent"] == candidate["task_intent"]
    assert question["task_intent"] == {
        "source_replication": "not_applicable",
        "theory": "required",
        "scientific_code": "not_applicable",
        "empirical": "not_applicable",
        "formal": "not_applicable",
        "novelty": "not_applicable",
        "unresolved_gaps": "required",
    }

    runtime_visible = json.dumps(
        {"candidate": candidate, "question": question}, sort_keys=True
    )
    for hidden_name in (
        "gold_manifest.json",
        "hidden_theory_harness.py",
        "semantic_reference.md",
        "semantic_rubric.json",
        "semantic_calibration_cases.json",
    ):
        assert hidden_name not in runtime_visible


def test_basu_theory_l0_draw_is_consumed_after_missing_routed_review() -> None:
    ladder = _load_ladder()
    candidate = next(
        row
        for row in ladder["initial_candidate_queue"]
        if row["id"]
        == "basu_complete_sufficient_ancillary_independence_known_result"
    )
    evidence = candidate["activation_evidence"]

    assert candidate["level"] == "L0"
    assert candidate["family"] == "statistical_structure_and_ancillarity"
    assert candidate["status"] == "active_scored"
    assert candidate["activation_status"] == (
        "fresh_live_v1_hidden_gold_failed_missing_routed_independent_theory_review"
    )
    assert candidate["gold_runtime_visibility"] == (
        "evaluator_only_after_runtime"
    )
    assert evidence["hidden_gold_manifest_validated"] is True
    assert evidence["gold_frozen_before_first_runtime_model_call"] is True
    assert evidence["first_runtime_model_call_occurred"] is True
    assert evidence["product_model_calls"] == 13
    assert evidence["fresh_live_runs"] == 1
    assert evidence["mechanical_reference_checks"] == "7/7"
    assert evidence["mechanical_negative_variants_rejected"] == 7
    assert evidence["semantic_calibration_cases"] == 13
    assert evidence["semantic_calibration_cases_correct"] == 13
    assert evidence["semantic_reference_claims"] == 8
    assert evidence["semantic_reference_candidate_passed"] is True
    assert evidence["semantic_calibration_model"] == (
        "claude-haiku-4-5-20251001"
    )
    assert evidence["semantic_calibration_model_calls"] == 2
    assert evidence["authority_binding_commit"] == (
        "7a0ee06b1b0f4507df40aaaf53c7092cde4e48d5"
    )
    assert evidence[
        "authority_binding_push_confirmed_on_work_branch_and_main"
    ] is True
    assert evidence["runtime_status"] == "BLOCKED"
    assert evidence["runtime_failure_classification"] == (
        "required_independent_theory_review_missing"
    )
    assert evidence["independent_theory_review_attempted"] is False
    assert evidence["critic_model_call_attempted"] is False
    assert evidence["hidden_theory_execution_attempted"] is False
    assert evidence["model_draw_resampling_blocked"] is True
    assert evidence["operator_audit_path"] == (
        "docs/operator_audits/basu_independence_l0_v1.md"
    )
    assert evidence["post_run_shared_mechanism_fix_commit"] == (
        "8ef61b0b9625bf99e4f783dad7781b4c1bfdba77"
    )
    assert evidence["post_run_shared_mechanism_fix_verification"] == (
        "123 focused tests and 861/861 full-suite tests passed"
    )
    assert evidence["formalization_requirement"] == "not_applicable"
    assert evidence["full_task_passed"] is False

    visible_path = Path(candidate["visible_questions_path"])
    assert hashlib.sha256(visible_path.read_bytes()).hexdigest() == (
        evidence["visible_questions_sha256"]
    )
    question = json.loads(visible_path.read_text(encoding="utf-8"))["questions"][0]
    assert question["id"] == candidate["id"]
    assert question["task_intent"] == candidate["task_intent"]
    assert question["task_intent"] == {
        "source_replication": "not_applicable",
        "theory": "required",
        "scientific_code": "not_applicable",
        "empirical": "not_applicable",
        "formal": "not_applicable",
        "novelty": "not_applicable",
        "unresolved_gaps": "required",
    }

    runtime_visible = json.dumps(
        {"candidate": candidate, "question": question}, sort_keys=True
    )
    for hidden_name in (
        "gold_manifest.json",
        "hidden_theory_harness.py",
        "semantic_reference.md",
        "semantic_rubric.json",
        "semantic_calibration_cases.json",
    ):
        assert hidden_name not in runtime_visible


def test_uniform_endpoint_l0_draw_is_consumed_after_hidden_gold_failure() -> None:
    ladder = _load_ladder()
    candidate = next(
        row
        for row in ladder["initial_candidate_queue"]
        if row["id"] == "uniform_endpoint_maximum_exact_interval_known_result"
    )
    evidence = candidate["activation_evidence"]

    assert candidate["level"] == "L0"
    assert candidate["family"] == "nonregular_endpoint_inference"
    assert candidate["status"] == "active_scored"
    assert candidate["activation_status"] == (
        "fresh_live_v1_hidden_gold_failed_theory_semantics_and_executable_interface"
    )
    assert candidate["gold_runtime_visibility"] == "evaluator_only_after_runtime"
    assert candidate["gold_manifest_sha256"] == (
        "9da0e97e77651d97994823a0c94d883a387680e8640bdc374c1c30b55f59ca45"
    )
    assert candidate["gold_descriptor_hash"] == (
        "6d971a027858bce4dd91c2af1a6dfc09a497899f148b1726790837439f42ab1e"
    )
    assert evidence["hidden_gold_manifest_validated"] is True
    assert evidence["gold_frozen_before_first_runtime_model_call"] is True
    assert evidence["first_runtime_model_call_occurred"] is True
    assert evidence["product_model_calls"] == 24
    assert evidence["fresh_live_runs"] == 1
    assert evidence["runtime_model"] == "claude-haiku-4-5-20251001"
    assert evidence["runtime_status"] == "ACCEPTED"
    assert evidence["runtime_iterations"] == 10
    assert evidence["visible_research_evaluation"] == (
        "1/1_complete_mode_conformant_ready"
    )
    assert evidence["hidden_gold_evaluation"] == "0/1_failed"
    assert evidence["hidden_theory_mechanical_checks"] == "7/7"
    assert evidence["hidden_theory_semantic_calibration"] == "12/12"
    assert evidence["hidden_theory_semantic_candidate_status"] == "FAIL"
    assert evidence["hidden_algorithm_acceptance_checks"] == "6/8"
    assert evidence["hidden_algorithm_failure"] == "invalid_requests_rejected"
    assert evidence["hidden_empirical_checks"] == "8/8"
    assert evidence["hidden_empirical_estimator_invocations"] == 15000
    assert evidence["runtime_manifest_sha256"] == (
        "01085f72d445675faaea88cce6de93fa84f1359e9c65f38e42293305a14ac2b8"
    )
    assert evidence["hidden_gold_report_sha256"] == (
        "30a0b5e1fa2fc27d9bb72283ac967e66a225a6b856ce16d785390ceb7e8bc396"
    )
    assert evidence["operator_audit_path"] == (
        "docs/operator_audits/uniform_endpoint_l0_v1.md"
    )
    assert evidence["post_run_shared_mechanism_fix_commit"] == "b49a8f5a"
    assert evidence["model_draw_resampling_blocked"] is True
    assert evidence["formalization_requirement"] == "not_applicable"
    assert evidence["full_task_passed"] is False

    visible_path = Path(candidate["visible_questions_path"])
    assert hashlib.sha256(visible_path.read_bytes()).hexdigest() == (
        evidence["visible_questions_sha256"]
    )
    question = json.loads(visible_path.read_text(encoding="utf-8"))["questions"][0]
    assert question["id"] == candidate["id"]
    assert candidate["task_intent"] == question["task_intent"]
    assert question["task_intent"] == {
        "source_replication": "not_applicable",
        "theory": "required",
        "scientific_code": "required",
        "empirical": "required",
        "formal": "not_applicable",
        "novelty": "not_applicable",
        "unresolved_gaps": "required",
    }
    contract = question["estimator_execution_contract"]
    assert contract["estimator_id"] == "est_uniform_endpoint_interval"
    assert contract["entrypoint"] == "run_estimator"
    assert [row["name"] for row in contract["request_fields"]] == ["sample", "alpha"]
    assert [row["name"] for row in contract["response_fields"]] == [
        "sample_size",
        "sample_maximum",
        "mle_endpoint",
        "unbiased_endpoint",
        "confidence_level",
        "exact_ci_lower",
        "exact_ci_upper",
    ]

    runtime_visible = json.dumps(
        {"candidate": candidate, "question": question}, sort_keys=True
    )
    for hidden_name in (
        "gold_manifest.json",
        "hidden_theory_harness.py",
        "hidden_harness.py",
        "hidden_empirical_harness.py",
        "semantic_reference.md",
        "semantic_rubric.json",
        "semantic_calibration_cases.json",
    ):
        assert hidden_name not in runtime_visible


def test_huber_location_l0_draw_is_consumed_after_review_packet_failure() -> None:
    ladder = _load_ladder()
    candidate = next(
        row
        for row in ladder["initial_candidate_queue"]
        if row["id"] == "huber_location_m_estimator_known_result"
    )

    assert candidate["level"] == "L0"
    assert candidate["family"] == "robust_location_m_estimation"
    assert candidate["status"] == "active_scored"
    assert candidate["activation_status"] == (
        "fresh_live_v1_blocked_invalid_generated_code_semantic_review_packet"
    )
    evidence = candidate["activation_evidence"]
    assert evidence["gold_frozen_before_first_runtime_model_call"] is True
    assert evidence["hidden_gold_manifest_validated"] is True
    assert evidence["authority_binding_commit"] == (
        "03558bacee39ea28d00fa962383f1d1aaaabc31d"
    )
    assert evidence[
        "authority_binding_push_confirmed_on_work_branch_and_main"
    ] is True
    assert evidence["first_runtime_model_call_occurred"] is True
    assert evidence["product_model_calls"] == 30
    assert evidence["fresh_live_runs"] == 1
    assert evidence["runtime_model"] == "claude-haiku-4-5-20251001"
    assert evidence["runtime_status"] == "BLOCKED"
    assert evidence["runtime_failure_classification"] == (
        "generated_code_semantic_review_packet_invalid"
    )
    assert evidence["theory_model_tool_turns"] == 13
    assert evidence["independent_theory_review_model_tool_turns"] == 10
    assert evidence["independent_theory_review_accepted"] is True
    assert evidence["algorithm_model_tool_turns"] == 3
    assert evidence["algorithm_source_executions"] == 2
    assert evidence["algorithm_source_owner_revision_observed"] is True
    assert evidence["generated_code_semantic_review_attempts"] == 3
    assert evidence["generated_code_semantic_review_accepted"] is False
    assert evidence["generated_code_semantic_review_validation_error"] == (
        "dimension_reviews must cover each required dimension in order"
    )
    assert evidence["generated_simulation_executed"] is False
    assert evidence["visible_research_evaluation"] == (
        "0/1_incomplete_mode_conformant"
    )
    assert evidence["hidden_gold_evaluation"] == "0/1_failed"
    assert evidence["hidden_theory_mechanical_checks"] == "7/7"
    assert evidence["hidden_theory_semantic_calibration"] == "12/12"
    assert evidence["hidden_theory_semantic_claims_satisfied"] == "8/9"
    assert evidence["hidden_theory_semantic_candidate_status"] == "INCONCLUSIVE"
    assert evidence["hidden_theory_semantic_inconclusive_claim"] == (
        "empirical_targets"
    )
    assert evidence["hidden_algorithm_execution_attempted"] is False
    assert evidence["hidden_empirical_execution_attempted"] is False
    assert evidence["operator_audit_path"] == (
        "docs/operator_audits/huber_location_l0_v1.md"
    )
    assert evidence["model_draw_resampling_blocked"] is True
    assert evidence["full_task_passed"] is False
    assert evidence["post_run_shared_mechanism_fix_commits"] == [
        "82083807eb29b57453a9819f308a60e9b27feeda",
        "f5822f58",
        "a73be809",
    ]
    assert "No second model draw occurred" in evidence[
        "post_run_generic_transport_calibration"
    ]
    assert "remains 0/1" in evidence["post_run_shared_mechanism_boundary"]
    assert evidence["algorithm_reference_contract_checks"] == "7/7"
    assert evidence["algorithm_negative_variants_rejected"] == 4
    assert evidence["empirical_negative_variants_rejected"] == 3
    assert evidence["semantic_calibration_cases_correct"] == 12
    assert evidence["semantic_reference_candidate_passed"] is True
    assert evidence["formalization_requirement"] == "not_applicable"
    assert candidate["task_intent"] == {
        "source_replication": "not_applicable",
        "theory": "required",
        "scientific_code": "required",
        "empirical": "required",
        "formal": "not_applicable",
        "novelty": "not_applicable",
        "unresolved_gaps": "required",
    }
    visible_path = Path(candidate["visible_questions_path"])
    assert visible_path.is_file()
    assert hashlib.sha256(visible_path.read_bytes()).hexdigest() == (
        evidence["visible_questions_sha256"]
    )
    question = json.loads(visible_path.read_text(encoding="utf-8"))["questions"][0]
    contract = question["estimator_execution_contract"]
    assert contract["estimator_id"] == "est_huber_location"
    assert [row["name"] for row in contract["request_fields"]] == [
        "sample",
        "tuning_constant",
    ]
    assert contract["entrypoint"] == "run_estimator"
    assert [row["name"] for row in contract["response_fields"]] == [
        "sample_size",
        "tuning_constant",
        "location_estimate",
        "active_fraction",
        "asymptotic_variance_factor",
        "standard_error",
    ]

    runtime_visible = json.dumps(
        {"candidate": candidate, "question": question}, sort_keys=True
    )
    for hidden_name in (
        "gold_manifest.json",
        "hidden_theory_harness.py",
        "hidden_harness.py",
        "hidden_empirical_harness.py",
        "semantic_reference.md",
        "semantic_rubric.json",
        "semantic_calibration_cases.json",
    ):
        assert hidden_name not in runtime_visible


def test_ridge_bias_variance_l0_draw_is_consumed_after_review_tool_failure() -> None:
    ladder = _load_ladder()
    candidate = next(
        row
        for row in ladder["initial_candidate_queue"]
        if row["id"] == "fixed_design_ridge_bias_variance_known_result"
    )

    assert candidate["level"] == "L0"
    assert candidate["family"] == "fixed_design_ridge_regression"
    assert candidate["status"] == "active_scored"
    assert candidate["activation_status"] == (
        "fresh_live_v1_blocked_invalid_generated_code_semantic_review_packet"
    )
    assert candidate["gold_manifest_sha256"] == (
        "6f977e367f5c110f9960767718f8e8c38af16501a5d797e8432cb3b15c4bb800"
    )
    assert candidate["gold_descriptor_hash"] == (
        "a46c2e1edcddb7495baa80188ffc312085c491af94568a780b372c67de5a75bc"
    )
    evidence = candidate["activation_evidence"]
    assert evidence["gold_frozen_before_first_runtime_model_call"] is True
    assert evidence["hidden_gold_manifest_validated"] is True
    assert evidence["visible_question_activation_commit"] == (
        "bf599f4b19ae45bc0ebe8e0b707360188b64c721"
    )
    assert evidence[
        "visible_question_activation_push_confirmed_on_work_branch_and_main"
    ] is True
    assert evidence["first_runtime_model_call_occurred"] is True
    assert evidence["product_model_calls"] == 26
    assert evidence["fresh_live_runs"] == 1
    assert evidence["runtime_model"] == "claude-haiku-4-5-20251001"
    assert evidence["runtime_status"] == "BLOCKED"
    assert evidence["runtime_failure_classification"] == (
        "generated_code_semantic_review_packet_invalid"
    )
    assert evidence["runtime_iterations"] == 6
    assert evidence["runtime_traces"] == 6
    assert evidence["runtime_task_handoffs"] == 5
    assert evidence["theory_model_tool_turns"] == 12
    assert evidence["theory_derivation_lines"] == 206
    assert evidence["theory_derivation_sha256"] == (
        "4301d0e2d265968925c39d1b1ee9e3b4a106668d294e403fda804022d1b5dc1a"
    )
    assert evidence["independent_theory_review_model_tool_turns"] == 10
    assert evidence["independent_theory_review_accepted"] is True
    assert evidence["independent_theory_review_lines"] == 281
    assert evidence["independent_theory_review_sha256"] == (
        "fdc6a5b4c598004f8003ffb30ae5ff5dedc40ddd8a35956a7b22f21328627e13"
    )
    assert evidence["algorithm_model_tool_turns"] == 2
    assert evidence["algorithm_source_executions"] == 1
    assert evidence["algorithm_final_source_lines"] == 202
    assert evidence["algorithm_final_source_sha256"] == (
        "f84a9e96b6b8b26e642eda9cd6cccb128b33f5ef446e99dfe4a49c72098d5691"
    )
    assert evidence["generated_code_semantic_review_attempts"] == 1
    assert evidence["generated_code_semantic_review_substantive_verdict"] == (
        "ACCEPT"
    )
    assert evidence["generated_code_semantic_review_accepted"] is False
    assert "RFC 6901" in evidence[
        "generated_code_semantic_review_validation_error"
    ]
    assert evidence["generated_simulation_executed"] is False
    assert evidence["hidden_theory_mechanical_checks"] == "7/7"
    assert evidence["hidden_theory_semantic_calibration"] == "12/12"
    assert evidence["hidden_theory_semantic_claims_satisfied"] == "8/9"
    assert evidence["hidden_theory_semantic_candidate_status"] == "INCONCLUSIVE"
    assert evidence["hidden_theory_combined_passed"] is False
    assert evidence["hidden_algorithm_execution_attempted"] is False
    assert evidence["hidden_empirical_execution_attempted"] is False
    assert evidence["post_run_shared_mechanism_fix_commit"] == (
        "cb9dcbe9d1d1cd38d73f43c6892c2234d9bca7be"
    )
    assert "same isolated reviewer context" in evidence[
        "post_run_shared_mechanism_fix"
    ]
    assert "remains 0/1" in evidence["post_run_shared_mechanism_boundary"]
    assert evidence["operator_audit_path"] == (
        "docs/operator_audits/ridge_bias_variance_l0_v1.md"
    )
    assert evidence["model_draw_resampling_blocked"] is True
    assert evidence["formalization_requirement"] == "not_applicable"
    assert evidence["formalizer_executed"] is False
    assert evidence["full_task_passed"] is False
    assert candidate["task_intent"] == {
        "source_replication": "not_applicable",
        "theory": "required",
        "scientific_code": "required",
        "empirical": "required",
        "formal": "not_applicable",
        "novelty": "not_applicable",
        "unresolved_gaps": "required",
    }

    visible_path = Path(candidate["visible_questions_path"])
    assert visible_path.is_file()
    assert hashlib.sha256(visible_path.read_bytes()).hexdigest() == (
        evidence["visible_questions_sha256"]
    )
    question = json.loads(visible_path.read_text(encoding="utf-8"))["questions"][0]
    contract = question["estimator_execution_contract"]
    assert question["id"] == candidate["id"]
    assert candidate["task_intent"] == question["task_intent"]
    assert contract["estimator_id"] == "est_fixed_design_ridge"
    assert contract["entrypoint"] == "run_estimator"
    assert [row["name"] for row in contract["request_fields"]] == [
        "design_matrix",
        "response",
        "penalty",
    ]
    assert [row["name"] for row in contract["response_fields"]] == [
        "n_observations",
        "n_features",
        "penalty",
        "coefficients",
        "fitted_values",
        "residual_sum_squares",
        "effective_degrees_of_freedom",
    ]
    assert "authoritative Markdown/LaTeX derivation" in question["description"]
    assert "Lean formalization is not applicable" in question["description"]

    runtime_visible = json.dumps(
        {"candidate": candidate, "question": question}, sort_keys=True
    )
    for hidden_name in (
        "gold_manifest.json",
        "hidden_theory_harness.py",
        "hidden_harness.py",
        "hidden_empirical_harness.py",
        "semantic_reference.md",
        "semantic_rubric.json",
        "semantic_calibration_cases.json",
    ):
        assert hidden_name not in runtime_visible


def test_trimmed_match_l1_draw_is_consumed_without_posthoc_rescore() -> None:
    ladder = _load_ladder()
    candidate = next(
        row
        for row in ladder["initial_candidate_queue"]
        if row["id"] == "trimmed_match_aoas_example_dataset_public_replication"
    )

    assert candidate["level"] == "L1"
    assert candidate["family"] == "causal_geo_experiment_source_replication"
    assert candidate["status"] == "consumed_scored"
    assert candidate["activation_status"] == "fresh_live_v1_hidden_gold_failed"
    assert candidate["gold_runtime_visibility"] == "evaluator_only_after_runtime"
    evidence = candidate["activation_evidence"]
    assert evidence["preactivation_code_head"] == (
        "f290118eaf043f10d28acfc5b93f8ef884c71711"
    )
    assert evidence["activation_commit"] == (
        "68b59afce691fb975d9a35ea48545412f6c076da"
    )
    assert evidence["activation_push_confirmed_before_product_run"] is True
    assert evidence["hidden_gold_manifest_validated"] is True
    assert evidence["hidden_gold_activated_before_first_product_model_call"] is True
    assert evidence["preactivation_product_model_calls"] == 0
    assert evidence["fresh_live_runs"] == 1
    assert evidence["fresh_live_model"] == "claude-haiku-4-5-20251001"
    assert evidence["fresh_live_model_tier"] == "haiku"
    assert evidence["runtime_status"] == "ACCEPTED"
    assert evidence["runtime_iterations"] == 3
    assert evidence["visible_research_evaluation"] == (
        "1/1_complete_conformant_ready"
    )
    assert evidence["hidden_gold_evaluation"] == "0/1_failed"
    assert evidence["independent_reruns"] == "3/3_byte_identical"
    assert evidence["source_replication_calibration_cases"] == "8/8"
    assert evidence["semantic_calibration_cases"] == "6/6"
    assert evidence["semantic_calibration_model"] == "claude-haiku-4-5-20251001"
    assert evidence["semantic_calibration_model_calls"] == 2
    assert evidence["bounded_source_result_projection"] is True
    assert evidence["hash_bound_result_line_reader"] is True
    assert evidence["hidden_identity_harness_execution_attempted"] is False
    assert evidence["hidden_identity_harness_transport_failure"] == (
        "generated code draft exceeds artifact-size boundary"
    )
    assert evidence["hidden_source_report_semantic_judge_calibrated"] is True
    assert evidence["hidden_source_report_semantic_calibration_cases"] == "6/6"
    assert evidence["hidden_source_report_semantic_candidate_status"] == "FAIL"
    assert evidence["post_consumption_shared_harness_fix_commit"] == (
        "c653295a3314589e4bea224c5b56635aaa4750ec"
    )
    assert evidence["post_consumption_score_changed"] is False
    assert evidence["rerun_resume_repair_or_rescore_performed"] is False
    assert evidence["formalization_requirement"] == "not_applicable"
    assert evidence["full_task_passed"] is False

    visible_path = Path(candidate["visible_questions_path"])
    assert hashlib.sha256(visible_path.read_bytes()).hexdigest() == (
        evidence["visible_questions_sha256"]
    )
    question = json.loads(visible_path.read_text(encoding="utf-8"))["questions"][0]
    assert question["id"] == candidate["id"]
    assert candidate["task_intent"] == question["task_intent"]
    assert question["task_intent"] == {
        "source_replication": "required",
        "theory": "not_applicable",
        "scientific_code": "not_applicable",
        "empirical": "not_applicable",
        "formal": "not_applicable",
        "novelty": "not_applicable",
        "unresolved_gaps": "required",
    }

    runtime_visible = json.dumps(
        {"candidate": candidate, "question": question}, sort_keys=True
    )
    for hidden_name in (
        "gold_manifest.json",
        "hidden_source_replication_harness.py",
        "semantic_reference.md",
        "semantic_rubric.json",
        "semantic_calibration_cases.json",
    ):
        assert hidden_name not in runtime_visible


def test_beta_binomial_l0_draw_is_consumed_as_first_full_task_pass() -> None:
    ladder = _load_ladder()
    candidate = next(
        row
        for row in ladder["initial_candidate_queue"]
        if row["id"] == "beta_binomial_conjugate_predictive_known_result"
    )

    assert candidate["level"] == "L0"
    assert candidate["family"] == "bayesian_conjugate_inference"
    assert candidate["status"] == "active_scored"
    assert candidate["activation_status"] == "fresh_live_v1_full_task_gold_passed"
    assert candidate["gold_manifest_sha256"] == (
        "0146a264fcdb3be8bf56d5ba266c9eab041cb64990060cbbeb17567bf22a4d5b"
    )
    assert candidate["gold_descriptor_hash"] == (
        "21d41355b5d992d38d5754e9965bc1335647d844386201f0f7aa81a5a1f10272"
    )
    evidence = candidate["activation_evidence"]
    assert evidence["gold_frozen_before_first_runtime_model_call"] is True
    assert evidence["hidden_gold_manifest_validated"] is True
    assert evidence["visible_question_activation_commit"] == (
        "9129db099bdc5bc475766277cb024d201dbc1bee"
    )
    assert evidence[
        "visible_question_activation_push_confirmed_on_work_branch_and_main"
    ] is True
    assert evidence["fresh_live_runs"] == 1
    assert evidence["runtime_model"] == "claude-haiku-4-5-20251001"
    assert evidence["runtime_model_policy_status"] == "OK"
    assert evidence["runtime_enabled_model_tiers"] == {"haiku": 7}
    assert evidence["runtime_status"] == "ACCEPTED"
    assert evidence["runtime_iterations"] == 10
    assert evidence["client_tool_model_turns"] == 29
    assert evidence["theory_document_count"] == 2
    assert evidence["theory_document_lines"] == 450
    assert evidence["theory_same_session_tool_error_corrected"] is True
    assert evidence["independent_theory_review_accepted"] is True
    assert evidence["algorithm_source_executions"] == 2
    assert evidence["algorithm_same_session_execution_feedback_corrected"] is True
    assert evidence["algorithm_semantic_review_accepted"] is True
    assert evidence["metric_protocol_preexecution_review_accepted"] is True
    assert evidence["runtime_metric_contracts_passed"] == "8/8"
    assert evidence["simulation_source_executions"] == 1
    assert evidence["simulation_semantic_review_accepted"] is True
    assert evidence["critic_research_disposition"] == "ACCEPT"
    assert evidence["critic_gap_disclosure"] == "COMPLETE"
    assert evidence["hidden_gold_evaluation"] == "1/1_passed"
    assert evidence["hidden_theory_mechanical_checks"] == "7/7"
    assert evidence["hidden_theory_semantic_calibration"] == "12/12"
    assert evidence["hidden_theory_semantic_claims_satisfied"] == "9/9"
    assert evidence["hidden_algorithm_checks"] == "10/10"
    assert evidence["hidden_empirical_checks"] == "10/10"
    assert evidence["post_run_generic_metric_review_fix_commit"] == (
        "91fff005efc8a49f4aacb3b3fcd5d619a8884e46"
    )
    assert "did not rerun" in evidence["post_run_shared_mechanism_boundary"]
    assert evidence["model_draw_resampling_blocked"] is True
    assert evidence["formalization_requirement"] == "not_applicable"
    assert evidence["formalizer_executed"] is False
    assert evidence["full_task_passed"] is True
    scored = [
        row
        for row in ladder["initial_candidate_queue"]
        if row["status"] in {"active_scored", "consumed_scored"}
    ]
    consumed = [
        row
        for row in scored
        if not row["activation_status"].startswith("frozen_ready_")
    ]
    readiness = ladder["current_readiness"]
    assert readiness["active_scored_tasks"] == len(scored)
    assert readiness["consumed_scored_tasks"] == len(consumed)
    assert readiness["fully_gold_configured_tasks"] == len(scored)
    assert readiness["fully_gold_passed_tasks"] == sum(
        row["activation_evidence"].get("full_task_passed") is True
        for row in scored
    )
    assert ladder["current_readiness"]["latest_shared_mechanism_head"] == (
        "be8d57ab6ec06ffa52f88e3a0e5ddd4a94ec9379"
    )

    visible_path = Path(candidate["visible_questions_path"])
    assert hashlib.sha256(visible_path.read_bytes()).hexdigest() == (
        evidence["visible_questions_sha256"]
    )
    question = json.loads(visible_path.read_text(encoding="utf-8"))["questions"][0]
    assert question["id"] == candidate["id"]
    assert question["task_intent"] == candidate["task_intent"]
    assert question["estimator_execution_contract"]["estimator_id"] == (
        "est_beta_binomial_posterior"
    )

    runtime_visible = json.dumps(
        {"candidate": candidate, "question": question}, sort_keys=True
    )
    for hidden_name in (
        "gold_manifest.json",
        "hidden_theory_harness.py",
        "hidden_harness.py",
        "hidden_empirical_harness.py",
        "semantic_reference.md",
        "semantic_rubric.json",
        "semantic_calibration_cases.json",
    ):
        assert hidden_name not in runtime_visible


def test_pymle_l1_draw_is_consumed_as_first_source_replication_pass() -> None:
    ladder = _load_ladder()
    candidate = next(
        row
        for row in ladder["initial_candidate_queue"]
        if row["id"] == "pymle_jss_cir_example_public_replication"
    )

    assert candidate["status"] == "consumed_scored"
    assert candidate["activation_status"] == (
        "fresh_live_v1_full_task_gold_passed_with_operator_semantic_caveat"
    )
    evidence = candidate["activation_evidence"]
    assert evidence["fresh_live_runs"] == 1
    assert evidence["runtime_model"] == "claude-haiku-4-5-20251001"
    assert evidence["runtime_enabled_model_tiers"] == {"haiku": 7}
    assert evidence["runtime_status"] == "ACCEPTED"
    assert evidence["runtime_iterations"] == 3
    assert evidence["source_replication_runs"] == 1
    assert evidence["runtime_outer_tool_calls"] == 0
    assert evidence["hidden_source_replication_checks"] == "11/11"
    assert evidence["hidden_source_report_semantic_calibration"] == "6/6"
    assert evidence["hidden_gold_evaluation"] == (
        "1/1_passed_under_frozen_evaluator"
    )
    assert "false-accepted" in evidence["operator_semantic_audit"]
    assert evidence["post_run_grounded_semantic_judgment_commit"] == (
        "3c00a515040dff2e21e4ec4666fce7e70b45a8b7"
    )
    assert evidence["model_draw_resampling_blocked"] is True
    assert evidence["formalization_requirement"] == "not_applicable"
    assert evidence["formalizer_executed"] is False
    assert evidence["full_task_passed"] is True
    readiness = ladder["current_readiness"]
    assert readiness["consumed_scored_tasks"] == 35
    assert readiness["fully_gold_passed_tasks"] == 2
    assert readiness["source_replication_components_passed"] == 1
    assert readiness["source_replication_full_tasks_passed"] == 1

    visible_path = Path(candidate["visible_questions_path"])
    assert hashlib.sha256(visible_path.read_bytes()).hexdigest() == (
        evidence["visible_questions_sha256"]
    )
    question = json.loads(visible_path.read_text(encoding="utf-8"))["questions"][0]
    assert question["id"] == candidate["id"]
    assert question["task_intent"] == candidate["task_intent"]


def test_poisson_garwood_r_l0_records_one_consumed_draw() -> None:
    ladder = _load_ladder()
    candidate = next(
        row
        for row in ladder["initial_candidate_queue"]
        if row["id"] == "poisson_garwood_rate_interval_r_known_result"
    )

    assert candidate["level"] == "L0"
    assert candidate["family"] == "poisson_exposure_rate_exact_inference_r"
    assert candidate["status"] == "active_scored"
    assert candidate["activation_status"] == (
        "fresh_live_v1_full_task_gold_failed_with_evaluator_scope_caveat"
    )
    assert candidate["gold_manifest_sha256"] == (
        "b19e33dabf7c585451a822833d3ab4729ca244130d89a2a4719ce4d1becdbfaa"
    )
    assert candidate["gold_descriptor_hash"] == (
        "f6c1ca29ca9be25ccd97e0a5030286640e21d00e041f55dce8ac6bcfc45fcdf1"
    )
    evidence = candidate["activation_evidence"]
    assert evidence["hidden_gold_manifest_validated"] is True
    assert evidence["gold_frozen_before_first_runtime_model_call"] is True
    assert evidence["preactivation_product_model_calls"] == 0
    assert evidence["first_runtime_model_call_occurred"] is True
    assert evidence["fresh_live_runs"] == 1
    assert evidence["activation_commit"] == (
        "158bb602cb5719ee611baad6865a16c70243f8e1"
    )
    assert evidence["activation_push_confirmed_on_work_branch_and_main"] is True
    assert evidence["required_model_owned_estimator_language"] == "r"
    assert evidence["required_model_owned_simulation_language"] == "r"
    assert evidence["webr_available"] is True
    assert evidence["algorithm_reference_contract_checks"] == "10/10"
    assert evidence["algorithm_negative_variants_rejected"] == 4
    assert evidence["empirical_reference_dgps_passed"] == 3
    assert evidence["empirical_reference_replicates_per_dgp"] == 16000
    assert evidence["semantic_calibration_attempts"] == 3
    assert evidence["semantic_calibration_model_calls"] == 6
    assert evidence["semantic_calibration_model"] == (
        "claude-haiku-4-5-20251001"
    )
    assert evidence["semantic_calibration_cases_correct"] == 12
    assert evidence["semantic_reference_claims"] == 8
    assert evidence["semantic_reference_candidate_passed"] is True
    assert evidence["runtime_model"] == "claude-haiku-4-5-20251001"
    assert evidence["runtime_enabled_model_tiers"] == {"haiku": 7}
    assert evidence["runtime_status"] == "ACCEPTED"
    assert evidence["visible_research_evaluation"] == (
        "1/1_complete_conformant_ready"
    )
    assert evidence["algorithm_final_source_language"] == "r"
    assert evidence["algorithm_final_source_backend"] == "webr"
    assert evidence["simulation_final_source_language"] == "r"
    assert evidence["simulation_final_source_backend"] == "webr"
    assert evidence["hidden_theory_mechanical_checks"] == "7/7"
    assert evidence["hidden_theory_semantic_claims_satisfied"] == "8/8"
    assert evidence["hidden_algorithm_checks"] == "8/10"
    assert evidence["hidden_algorithm_failed_atomic_check"] == (
        "invalid_requests_rejected"
    )
    assert evidence["hidden_empirical_checks"] == "6/6"
    assert evidence["hidden_gold_evaluation"] == "0/1_failed_scientific_code"
    assert evidence["model_draw_resampling_blocked"] is True
    assert evidence["formalization_requirement"] == "not_applicable"
    assert evidence["formalizer_executed"] is False
    assert evidence["full_task_passed"] is False

    readiness = ladder["current_readiness"]
    assert readiness["active_scored_tasks"] == 35
    assert readiness["consumed_scored_tasks"] == 35
    assert readiness["fully_gold_configured_tasks"] == 35
    assert readiness["fully_gold_passed_tasks"] == 2
    visible_path = Path(candidate["visible_questions_path"])
    assert hashlib.sha256(visible_path.read_bytes()).hexdigest() == (
        evidence["visible_questions_sha256"]
    )
    question = json.loads(visible_path.read_text(encoding="utf-8"))["questions"][0]
    assert question["id"] == candidate["id"]
    assert question["task_intent"] == candidate["task_intent"]
    assert question["estimator_execution_contract"]["estimator_id"] == (
        "est_poisson_garwood_rate"
    )
    assert "Do not substitute Python" in question["description"]

    runtime_visible = json.dumps(
        {"candidate": candidate, "question": question}, sort_keys=True
    )
    for hidden_name in (
        "gold_manifest.json",
        "hidden_theory_harness.py",
        "hidden_harness.R",
        "hidden_empirical_harness.R",
        "semantic_reference.md",
        "semantic_rubric.json",
        "semantic_calibration_cases.json",
    ):
        assert hidden_name not in runtime_visible


def test_complete_randomization_l0_draw_is_consumed_and_failed_closed() -> None:
    ladder = _load_ladder()
    candidate = next(
        row
        for row in ladder["initial_candidate_queue"]
        if row["id"] == "complete_randomization_neyman_variance_known_result"
    )

    assert candidate["level"] == "L0"
    assert candidate["family"] == "finite_population_randomization_inference"
    assert candidate["status"] == "active_scored"
    assert candidate["activation_status"] == (
        "fresh_live_v1_full_task_gold_failed_metric_protocol_and_operator_theory"
    )
    assert candidate["gold_manifest_sha256"] == (
        "fd54b0f306ab7d1a5cb31bc295a58f96a09103889550875d7f17f9ba3bfc9967"
    )
    assert candidate["gold_descriptor_hash"] == (
        "4dfb3bd9a11f4d81881286301cb35e05c0befb575aaa98322eee8518c19fa749"
    )
    evidence = candidate["activation_evidence"]
    assert evidence["hidden_gold_manifest_validated"] is True
    assert evidence["gold_frozen_before_first_runtime_model_call"] is True
    assert evidence["activation_commit"] == (
        "7db5330283f32cf4f296b3615568ac3de16b23d9"
    )
    assert evidence["activation_push_confirmed_on_work_branch_and_main"] is True
    assert evidence["preactivation_product_model_calls"] == 0
    assert evidence["first_runtime_model_call_occurred"] is True
    assert evidence["fresh_live_runs"] == 1
    assert evidence["runtime_model"] == "claude-haiku-4-5-20251001"
    assert evidence["runtime_model_policy_status"] == "OK"
    assert evidence["runtime_head"] == (
        "0ef27a25e97d24965d6df9d60a4ee46b3f0ea43d"
    )
    assert evidence["runtime_status"] == "BLOCKED"
    assert evidence["runtime_terminal_kind"] == "blocked"
    assert evidence["runtime_failure_classification"] == (
        "architect_metric_protocol_source_workspace_exhausted"
    )
    assert evidence["runtime_outer_iterations"] == 7
    assert evidence["runtime_task_handoffs"] == 6
    assert evidence["runtime_client_tool_model_turns"] == 35
    assert evidence["theory_developer_model_turns"] == 13
    assert evidence["theory_preflight_model_turns"] == 10
    assert evidence["algorithm_engineer_model_turns"] == 5
    assert evidence["generated_code_semantic_reviewer_model_turns"] == 2
    assert evidence["metric_author_model_turns"] == 2
    assert evidence["metric_semantic_reviewer_model_turns"] == 2
    assert evidence["architect_initial_model_turns"] == 1
    assert evidence["algorithm_reference_contract_checks"] == "15/15"
    assert evidence["algorithm_negative_variants_rejected"] == 4
    assert evidence["empirical_reference_populations_passed"] == 3
    assert evidence["empirical_reference_assignments_enumerated"] == 70
    assert evidence["empirical_reference_checks"] == "8/8"
    assert evidence["semantic_calibration_cases_correct"] == 12
    assert evidence["semantic_reference_claims"] == 9
    assert evidence["semantic_reference_candidate_passed"] is True
    assert evidence["theory_markdown_checkpoint_committed"] is True
    assert evidence["theory_preexecution_review_accepted"] is True
    assert evidence["generated_algorithm_executed"] is True
    assert evidence["generated_algorithm_runtime_review_accepted"] is True
    assert evidence["metric_protocol_independently_accepted"] is False
    assert evidence["metric_protocol_candidate_count"] == 2
    assert evidence["metric_protocol_unresolved_high_findings"] == 2
    assert evidence["generated_simulation_executed"] is False
    assert evidence["visible_research_evaluation"] == "0/1"
    assert evidence["hidden_algorithm_checks"] == "13/15"
    assert evidence["hidden_algorithm_failed_atomic_checks"] == [
        "reject_missing_or_extra_request_keys",
        "reject_outcome_entries",
    ]
    assert evidence["hidden_empirical_checks"] == "8/8"
    assert evidence["hidden_empirical_assignments_enumerated"] == 70
    assert evidence["hidden_theory_mechanical_checks"] == "7/7"
    assert evidence["hidden_theory_semantic_claims"] == "9/9 SATISFIED"
    assert "false intermediate" in evidence["operator_theory_audit"]
    assert evidence["hidden_gold_evaluation"] == "0/1"
    assert evidence["runtime_manifest_sha256"] == (
        "60c5d5b64aab812015bfcfcccf6f176ee3873f8f4ddf0f5e5b0eb00d83106b35"
    )
    assert evidence["hidden_gold_report_sha256"] == (
        "5f1a116d4bde2546d4d0a73cdd1015dab3d8b80976c51f5bd49eb4db55a32492"
    )
    assert evidence["runtime_result_sha256"] == (
        "b52959cde21e5d1dcdea436ac44f0316b8ba71a8bef3defb8dd3d5d6b587cdcc"
    )
    assert evidence["runtime_progress_sha256"] == (
        "ac29391b71af5e3a30d496893315a5bfd621d7e4538be02fc43cfb01c26dda55"
    )
    assert evidence["operator_audit_path"] == (
        "docs/operator_audits/complete_randomization_neyman_l0_v1.md"
    )
    assert evidence["post_consumption_shared_metric_source_loop_head"] == (
        "e7d0174a0028aa8ee9371bf2794660a045c465d0"
    )
    assert evidence["post_consumption_shared_metric_source_loop_evidence"] == (
        "future_tasks_regression_only_no_rerun_repair_rescore_or_capability_credit"
    )
    assert evidence["post_consumption_shared_theory_reconstruction_head"] == (
        "b9ece43923ab05cb1185e1493e360658ae14c8fb"
    )
    assert evidence["post_consumption_shared_theory_reconstruction_evidence"] == (
        "future_tasks_regression_only_no_rerun_repair_rescore_or_capability_credit"
    )
    assert evidence["model_draw_resampling_blocked"] is True
    assert evidence["formalization_requirement"] == "not_applicable"
    assert evidence["formalizer_executed"] is False
    assert evidence["full_task_passed"] is False

    readiness = ladder["current_readiness"]
    assert readiness["active_scored_tasks"] == 35
    assert readiness["consumed_scored_tasks"] == 35
    assert readiness["fully_gold_configured_tasks"] == 35
    assert readiness["fully_gold_passed_tasks"] == 2

    visible_path = Path(candidate["visible_questions_path"])
    assert hashlib.sha256(visible_path.read_bytes()).hexdigest() == (
        evidence["visible_questions_sha256"]
    )
    question = json.loads(visible_path.read_text(encoding="utf-8"))["questions"][0]
    assert question["id"] == candidate["id"]
    assert question["task_intent"] == candidate["task_intent"]
    contract = question["estimator_execution_contract"]
    assert contract["estimator_id"] == "est_complete_randomization_neyman"
    assert any(
        row["clause_id"] == "invariant.closed_object_contract"
        for row in contract["invariants"]
    )

    runtime_visible = json.dumps(
        {"candidate": candidate, "question": question}, sort_keys=True
    )
    for hidden_name in (
        "gold_manifest.json",
        "hidden_theory_harness.py",
        "hidden_harness.py",
        "hidden_empirical_harness.py",
        "semantic_reference.md",
        "semantic_rubric.json",
        "semantic_calibration_cases.json",
    ):
        assert hidden_name not in runtime_visible


def test_bootstrap_mean_l0_records_one_consumed_draw() -> None:
    ladder = _load_ladder()
    candidate = next(
        row
        for row in ladder["initial_candidate_queue"]
        if row["id"] == "nonparametric_bootstrap_mean_variance_known_result"
    )

    assert candidate["level"] == "L0"
    assert candidate["family"] == "nonparametric_bootstrap"
    assert candidate["status"] == "active_scored"
    assert candidate["activation_status"] == (
        "fresh_live_v1_full_task_gold_failed_scientific_code_and_simulation"
    )
    assert candidate["gold_manifest_sha256"] == (
        "0ba332fbcb78cd99803ba6bec40bb7c4e215cc2a824ff0d667da4a279c450402"
    )
    assert candidate["gold_descriptor_hash"] == (
        "7c1c5be3b4df99de1adb31d53dc74f244cceff8db988928bc81a7a952eb26bb0"
    )
    evidence = candidate["activation_evidence"]
    assert evidence["hidden_gold_manifest_validated"] is True
    assert evidence["gold_frozen_before_first_runtime_model_call"] is True
    assert evidence["activation_commit"] == (
        "6034652636448eaf76bcd3eefe1b8fea00501130"
    )
    assert evidence["activation_push_confirmed_on_work_branch_and_main"] is True
    assert evidence["preactivation_product_model_calls"] == 0
    assert evidence["first_runtime_model_call_occurred"] is True
    assert evidence["fresh_live_runs"] == 1
    assert evidence["runtime_model"] == "claude-haiku-4-5-20251001"
    assert evidence["runtime_model_policy_status"] == "OK"
    assert evidence["runtime_enabled_model_tiers"] == {"haiku": 7}
    assert evidence["runtime_status"] == "BLOCKED"
    assert evidence["runtime_failure_classification"] == (
        "critic_scientific_rejected"
    )
    assert evidence["runtime_iterations"] == 10
    assert evidence["runtime_architect_traces"] == 3
    assert evidence["algorithm_reference_contract_checks"] == "13/13"
    assert evidence["algorithm_negative_variants_rejected"] == 3
    assert evidence["empirical_reference_samples_passed"] == 4
    assert evidence["empirical_reference_resamples_enumerated"] == 3664
    assert evidence["empirical_reference_checks"] == "6/6"
    assert evidence["semantic_calibration_cases"] == 9
    assert evidence["semantic_calibration_cases_correct"] == 9
    assert evidence["semantic_reference_claims"] == 7
    assert evidence["semantic_reference_candidate_passed"] is True
    assert evidence["blind_reconstruction_mechanism_head"] == (
        "b9ece43923ab05cb1185e1493e360658ae14c8fb"
    )
    assert evidence["metric_source_owner_mechanism_head"] == (
        "e7d0174a0028aa8ee9371bf2794660a045c465d0"
    )
    assert evidence["theory_model_tool_turns"] == 12
    assert evidence["theory_document_count"] == 2
    assert evidence["theory_checkpoint_explicitly_committed"] is True
    assert evidence["independent_theory_review_accepted"] is True
    assert evidence["independent_theory_candidate_document_reads"] == 7
    assert evidence["hidden_theory_mechanical_checks"] == "7/7"
    assert evidence["hidden_theory_semantic_calibration"] == "9/9"
    assert evidence["hidden_theory_semantic_claims_satisfied"] == "7/7"
    assert evidence["hidden_algorithm_checks"] == "12/13"
    assert evidence["hidden_algorithm_failed_public_clause"] == (
        "request_fields.sample.edge_cases:no_silent_coercion"
    )
    assert evidence["hidden_empirical_checks"] == "6/6"
    assert evidence["runtime_metric_contracts_passed"] == "7/8"
    assert evidence["runtime_metric_contract_failed"] == "location_equivariant"
    assert evidence["simulation_semantic_review_target_focus_valid"] is False
    assert evidence["hidden_gold_evaluation"] == (
        "0/1_failed_scientific_code_and_runtime_empirical_acceptance"
    )
    assert evidence["post_consumption_shared_diagnostic_boundary_head"] == (
        "26b8e12449aac0f4b6f031cf65896768ae7316ac"
    )
    assert evidence["model_draw_resampling_blocked"] is True
    assert evidence["formalization_requirement"] == "not_applicable"
    assert evidence["formalizer_executed"] is False
    assert evidence["full_task_passed"] is False

    readiness = ladder["current_readiness"]
    assert readiness["active_scored_tasks"] == 35
    assert readiness["consumed_scored_tasks"] == 35
    assert readiness["fully_gold_configured_tasks"] == 35
    assert readiness["fully_gold_passed_tasks"] == 2
    assert candidate["id"] not in {
        row["id"] for row in ladder["evidence_dimensions"]
    }

    visible_path = Path(candidate["visible_questions_path"])
    assert hashlib.sha256(visible_path.read_bytes()).hexdigest() == (
        evidence["visible_questions_sha256"]
    )
    question = json.loads(visible_path.read_text(encoding="utf-8"))["questions"][0]
    assert question["id"] == candidate["id"]
    assert question["task_intent"] == candidate["task_intent"]
    assert question["source"]["doi"] == "10.1214/aos/1176344552"
    contract = question["estimator_execution_contract"]
    assert contract["estimator_id"] == "est_bootstrap_mean_variance"
    assert {row["clause_id"] for row in contract["empirical_claims"]} == {
        "claim.empirical.protocol_identity",
        "claim.empirical.conditional_mean",
        "claim.empirical.conditional_variance",
        "claim.empirical.normalization_link",
        "claim.empirical.constant_boundary",
    }

    runtime_visible = json.dumps(
        {"candidate": candidate, "question": question}, sort_keys=True
    )
    for hidden_name in (
        "gold_manifest.json",
        "hidden_theory_harness.py",
        "hidden_harness.py",
        "hidden_empirical_harness.py",
        "semantic_reference.md",
        "semantic_rubric.json",
        "semantic_calibration_cases.json",
    ):
        assert hidden_name not in runtime_visible


def test_mann_whitney_u_r_l0_records_sole_consumed_draw() -> None:
    ladder = _load_ladder()
    candidate = next(
        row
        for row in ladder["initial_candidate_queue"]
        if row["id"] == "mann_whitney_u_null_moments_r_known_result"
    )

    assert candidate["level"] == "L0"
    assert candidate["family"] == "two_sample_rank_inference_r"
    assert candidate["status"] == "active_scored"
    assert candidate["activation_status"] == (
        "fresh_live_v1_full_task_gold_failed_metric_protocol_liveness"
    )
    assert candidate["gold_manifest_sha256"] == (
        "798d7289053073417c44922f0fe8f7f21c91da6015ed8d701a9188598c167994"
    )
    assert candidate["gold_descriptor_hash"] == (
        "677c9b8330d4ee88ca16b4d5f620773b4449af665f5c9dea61a4840fa87a7193"
    )
    evidence = candidate["activation_evidence"]
    assert evidence["hidden_gold_manifest_validated"] is True
    assert evidence["gold_frozen_before_first_runtime_model_call"] is True
    assert evidence["activation_commit"] == (
        "8e8d2e7db9328298eb1215cb5b137c70e8f07c33"
    )
    assert evidence["activation_push_confirmed_on_work_branch_and_main"] is True
    assert evidence["preactivation_product_model_calls"] == 0
    assert evidence["first_runtime_model_call_occurred"] is True
    assert evidence["fresh_live_runs"] == 1
    assert evidence["runtime_model"] == "claude-haiku-4-5-20251001"
    assert evidence["runtime_model_policy_status"] == "OK"
    assert evidence["required_model_owned_estimator_language"] == "r"
    assert evidence["required_model_owned_simulation_language"] == "r"
    assert evidence["webr_available"] is True
    assert evidence["algorithm_reference_contract_checks"] == "14/14"
    assert evidence["algorithm_negative_variants_rejected"] == 3
    assert evidence["empirical_reference_configurations_passed"] == 4
    assert evidence["empirical_reference_assignments_enumerated"] == 41
    assert evidence["empirical_reference_checks"] == "6/6"
    assert evidence["semantic_calibration_cases"] == 9
    assert evidence["semantic_calibration_cases_correct"] == 9
    assert evidence["semantic_reference_claims"] == 7
    assert evidence["semantic_reference_candidate_passed"] is True
    assert evidence["exact_estimator_reviewer_probe_mechanism_head"] == (
        "5daec039b8564100b9d2f812bfefdc8cb6e2b24b"
    )
    assert evidence["runtime_status"] == "BLOCKED"
    assert evidence["runtime_failure_classification"] == (
        "architect_metric_requirement_packet_validation_failed"
    )
    assert evidence["runtime_research_evaluation"] == "0/1"
    assert evidence["hidden_gold_evaluation"] == "0/1"
    assert evidence["hidden_theory_checks"] == "7/7"
    assert evidence["hidden_theory_semantic_checks"] == "7/7"
    assert evidence["hidden_algorithm_checks"] == "14/14"
    assert evidence["hidden_empirical_checks"] == "6/6"
    assert evidence["generated_code_reviewer_exact_estimator_probes"] == 2
    assert evidence["post_consumption_external_metric_workspace_head"] == (
        "be8d57ab6ec06ffa52f88e3a0e5ddd4a94ec9379"
    )
    assert evidence["metric_protocol_truncated_terminal_inputs"] == 4
    assert evidence["metric_protocol_executed_rejected_submissions"] == 1
    assert evidence["model_draw_resampling_blocked"] is True
    assert evidence["formalization_requirement"] == "not_applicable"
    assert evidence["formalizer_executed"] is False
    assert evidence["full_task_passed"] is False

    readiness = ladder["current_readiness"]
    assert readiness["active_scored_tasks"] == 35
    assert readiness["consumed_scored_tasks"] == 35
    assert readiness["fully_gold_configured_tasks"] == 35
    assert readiness["fully_gold_passed_tasks"] == 2
    assert candidate["id"] not in {
        row["id"] for row in ladder["evidence_dimensions"]
    }

    visible_path = Path(candidate["visible_questions_path"])
    assert hashlib.sha256(visible_path.read_bytes()).hexdigest() == (
        evidence["visible_questions_sha256"]
    )
    question = json.loads(visible_path.read_text(encoding="utf-8"))["questions"][0]
    assert question["id"] == candidate["id"]
    assert question["task_intent"] == candidate["task_intent"]
    assert question["source"]["doi"] == "10.1214/aoms/1177730491"
    contract = question["estimator_execution_contract"]
    assert contract["estimator_id"] == "est_mann_whitney_u_moments"
    assert "using language=r" in question["description"]
    assert {row["clause_id"] for row in contract["empirical_claims"]} == {
        "claim.empirical.protocol_identity",
        "claim.empirical.exact_mean",
        "claim.empirical.exact_variance",
        "claim.empirical.complement_symmetry",
    }

    runtime_visible = json.dumps(
        {"candidate": candidate, "question": question}, sort_keys=True
    )
    for hidden_name in (
        "gold_manifest.json",
        "hidden_theory_harness.py",
        "hidden_harness.R",
        "hidden_empirical_harness.R",
        "semantic_reference.md",
        "semantic_rubric.json",
        "semantic_calibration_cases.json",
    ):
        assert hidden_name not in runtime_visible
