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
    assert ladder["current_readiness"]["consumed_scored_tasks"] == 25
    assert ladder["current_readiness"]["fully_gold_passed_tasks"] == 0
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
    assert ladder["current_readiness"]["consumed_scored_tasks"] == 25
    assert ladder["current_readiness"]["fully_gold_passed_tasks"] == 0
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
    assert ladder["current_readiness"]["active_scored_tasks"] == 26
    assert ladder["current_readiness"]["consumed_scored_tasks"] == 25
    assert ladder["current_readiness"]["fully_gold_configured_tasks"] == 26
    assert ladder["current_readiness"]["fully_gold_passed_tasks"] == 0
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
    assert ladder["current_readiness"]["active_scored_tasks"] == 26
    assert ladder["current_readiness"]["consumed_scored_tasks"] == 25
    assert ladder["current_readiness"]["fully_gold_configured_tasks"] == 26
    assert ladder["current_readiness"]["fully_gold_passed_tasks"] == 0

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
    assert ladder["current_readiness"]["active_scored_tasks"] == 26
    assert ladder["current_readiness"]["consumed_scored_tasks"] == 25
    assert ladder["current_readiness"]["fully_gold_configured_tasks"] == 26


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
    assert ladder["current_readiness"]["consumed_scored_tasks"] == 25
    assert ladder["current_readiness"]["fully_gold_passed_tasks"] == 0

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


def test_basu_theory_l0_authority_is_frozen_before_product_call() -> None:
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
        "frozen_ready_gold_validated_no_product_call"
    )
    assert candidate["gold_runtime_visibility"] == (
        "evaluator_only_after_runtime"
    )
    assert evidence["hidden_gold_manifest_validated"] is True
    assert evidence["gold_frozen_before_first_runtime_model_call"] is True
    assert evidence["first_runtime_model_call_occurred"] is False
    assert evidence["product_model_calls"] == 0
    assert evidence["fresh_live_runs"] == 0
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
    assert evidence["formalization_requirement"] == "not_applicable"
    assert evidence["full_task_passed"] is False
    assert ladder["current_readiness"]["active_scored_tasks"] == 26
    assert ladder["current_readiness"]["consumed_scored_tasks"] == 25
    assert ladder["current_readiness"]["fully_gold_configured_tasks"] == 26
    assert ladder["current_readiness"]["fully_gold_passed_tasks"] == 0

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
    assert ladder["current_readiness"]["consumed_scored_tasks"] == 25
    assert ladder["current_readiness"]["fully_gold_passed_tasks"] == 0

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
