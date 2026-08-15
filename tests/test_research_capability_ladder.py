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
    active = [candidate for candidate in candidates if candidate["status"] == "active_scored"]
    pending = [
        candidate
        for candidate in candidates
        if candidate["status"].startswith("proposed_pending_")
    ]
    assert active
    assert ladder["current_readiness"]["active_scored_tasks"] == len(active)
    assert ladder["current_readiness"]["fully_gold_configured_tasks"] == len(active)
    assert ladder["current_readiness"]["fully_gold_passed_tasks"] == sum(
        candidate["activation_evidence"].get("full_task_passed") is True
        for candidate in active
    )
    assert len({candidate["id"] for candidate in candidates}) == len(candidates)
    for candidate in active:
        assert candidate["gold_runtime_visibility"] == "evaluator_only_after_runtime"
        assert candidate["activation_status"].startswith(
            ("full_task_gold_", "fresh_live_v1_")
        )
        assert Path(candidate["visible_questions_path"]).is_file()
        assert "gold_manifest" not in candidate
        assert candidate["gold_authority"] == (
            "operator_provisioned_outside_repository_and_model_workspace"
        )
        assert len(candidate["gold_manifest_sha256"]) == 64
    assert pending
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


def test_median_of_means_l0_is_frozen_before_its_only_live_draw() -> None:
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
        "full_task_gold_calibrated_frozen_pending_first_live_run"
    )
    evidence = candidate["activation_evidence"]
    assert evidence["gold_frozen_before_first_runtime_model_call"] is True
    assert evidence["hidden_gold_manifest_validated"] is True
    assert evidence["first_runtime_model_call_occurred"] is False
    assert evidence["fresh_live_runs"] == 0
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
