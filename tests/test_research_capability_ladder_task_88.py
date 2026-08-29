from __future__ import annotations

import hashlib
import json
from pathlib import Path

from ai_statistician.estimator_interface_contract import (
    frozen_estimator_execution_contract_id,
)
from ai_statistician.fingerprint import stable_hash


LADDER_PATH = Path("benchmarks/research_capability_ladder_20260814.json")
TASK_ID = "glmnet_gaussian_elastic_net_paper_to_code"


def test_glmnet_gaussian_l2_task_records_immutable_consumed_result() -> None:
    ladder = json.loads(LADDER_PATH.read_text(encoding="utf-8"))
    candidate = next(
        row for row in ladder["initial_candidate_queue"] if row["id"] == TASK_ID
    )
    evidence = candidate["activation_evidence"]

    assert candidate["level"] == "L2"
    assert candidate["family"] == "gaussian_elastic_net_coordinate_descent"
    assert candidate["status"] == "consumed_scored"
    assert candidate["activation_status"] == (
        "fresh_live_v1_consumed_runtime_blocked_hidden_theory_semantic_"
        "and_algorithm_handoff_failed"
    )
    assert candidate["gold_bundle_id"] == (
        "research-l2-glmnet-gaussian-20260828-v1"
    )
    assert candidate["gold_manifest_sha256"] == (
        "2fc7c5496f206114ee3497681f80a298b10ff4fb0f65773e2f3665167ff53acd"
    )
    assert candidate["gold_descriptor_hash"] == (
        "c816d74c01b35240984073ab426d751208b4b1db440620705e2247c631f8edb2"
    )
    assert evidence["visible_question_activation_commit"] == (
        "23e7afc2376a49fac7e9994b9a6ca5f3ea3c19f9"
    )
    assert evidence["research_source_snapshot_hash"] == (
        "e0fc962da5417a3cb22832f21b79c9a1bae8d8136be549bd75bc38b3ec714779"
    )
    assert evidence["activation_schema_version"] == 4
    assert evidence["reference_algorithm_contract_checks_passed"] is True
    assert evidence["reference_algorithm_valid_cases"] == 5
    assert evidence["reference_algorithm_kkt_cases"] == 5
    assert evidence["reference_algorithm_invalid_cases"] == 12
    assert evidence["algorithm_negative_variants_rejected"] == 3
    assert evidence["reference_empirical_designs_passed"] == 2
    assert evidence["reference_empirical_replicates_per_design"] == 1000
    assert evidence["semantic_protocol_version"] == 10
    assert evidence["semantic_activation_attempts"] == 1
    assert evidence["semantic_calibration_total_model_calls"] == 8
    assert evidence["semantic_calibration_cases_correct"] == 6
    assert evidence["semantic_candidate_mode_negative_cases_correct"] == 1
    assert evidence["semantic_reference_claims"] == 7
    assert evidence["semantic_reference_candidate_passed"] is True
    assert evidence["semantic_calibration_model"] == (
        "claude-haiku-4-5-20251001"
    )
    assert evidence["activation_reference_tasks_passed"] == 1
    assert evidence["activation_negative_controls_rejected"] == 4
    assert evidence["activation_semantic_reference_documents_passed"] == 1
    assert (
        evidence[
            "activation_semantic_candidate_mode_negative_controls_rejected"
        ]
        == 1
    )
    assert evidence["activation_semantic_model_calls"] == 0
    assert evidence["activation_semantic_qualification_model_calls"] == 8
    assert evidence["activation_semantic_qualification_reused"] is True
    assert evidence["hidden_gold_manifest_validated"] is True
    assert evidence["gold_frozen_before_first_runtime_model_call"] is True
    assert evidence["activation_ledger_commit"] == (
        "2370a4d2f6f3ec977c73b50d458deef6dd20ca74"
    )
    assert evidence["activation_push_confirmed_on_work_branch_and_main"] is True
    assert evidence["preactivation_product_model_calls"] == 0
    assert evidence["preactivation_evaluator_model_calls"] == 8
    assert evidence["first_runtime_model_call_occurred"] is True
    assert evidence["fresh_live_runs"] == 1
    assert evidence["runtime_invocations"] == 1
    assert evidence["runtime_model"] == "claude-haiku-4-5-20251001"
    assert evidence["sonnet_product_calls"] == 0
    assert evidence["opus_product_calls"] == 0
    assert evidence["product_code_head"] == (
        "5f4a1cf5178211180fadcd3f6b704ec050b798bd"
    )
    assert evidence["runtime_status"] == "BLOCKED"
    assert evidence["runtime_failure_classification"] == (
        "architect_feedback_route_blocked"
    )
    assert evidence["runtime_research_loop_complete"] is False
    assert evidence["runtime_mode_conformant"] is True
    assert evidence["runtime_outer_graph_iterations"] == 10
    assert evidence["runtime_handoffs"] == 9
    assert evidence["runtime_observations"] == 12
    assert evidence["runtime_outer_tool_calls"] == 20
    assert evidence["runtime_client_tool_model_turns"] == 127
    assert evidence["runtime_total_product_model_requests"] == 129
    assert evidence["runtime_workspace_tool_executions"] == 135
    assert evidence["theory_workspace_model_turns"] == 45
    assert evidence["independent_theory_preflight_model_turns"] == 27
    assert evidence["algorithm_workspace_model_turns"] == 50
    assert evidence["generated_code_semantic_reviewer_model_turns"] == 5
    assert evidence["theory_developer_executed"] is True
    assert evidence["generated_algorithm_executed"] is True
    assert evidence["generated_simulation_executed"] is False
    assert evidence["formalization_requirement"] == "not_applicable"
    assert evidence["formalizer_executed"] is False
    assert evidence["hidden_theory_mechanical_checks"] == "7/7"
    assert evidence["hidden_theory_semantic_candidate_status"] == "INCONCLUSIVE"
    assert evidence["hidden_theory_combined_passed"] is False
    assert evidence["hidden_algorithm_harness_attempted"] is False
    assert evidence["hidden_empirical_harness_attempted"] is False
    assert evidence["post_run_shared_mechanism_commit"] == (
        "b8583b9e40dbbcc00cb335fdb78b6c2f2cb3b3da"
    )
    assert "1033/1033" in evidence["closeout_verification"]
    assert evidence["post_run_score_changed"] is False
    assert evidence["model_draw_resampling_blocked"] is True
    assert evidence["automated_full_task_passed"] is False
    assert evidence["full_task_passed"] is False
    assert evidence["trusted_capability_credit"] is False

    visible_path = Path(candidate["visible_questions_path"])
    assert hashlib.sha256(visible_path.read_bytes()).hexdigest() == (
        evidence["visible_questions_sha256"]
    )
    question = json.loads(visible_path.read_text(encoding="utf-8"))["questions"][0]
    assert question["id"] == TASK_ID
    assert question["task_intent"] == candidate["task_intent"]
    assert question["task_intent"]["theory"] == "required"
    assert question["task_intent"]["scientific_code"] == "required"
    assert question["task_intent"]["empirical"] == "required"
    assert question["task_intent"]["formal"] == "not_applicable"
    assert question["source"]["research_source_snapshot_hash"] == (
        evidence["research_source_snapshot_hash"]
    )
    contract = question["estimator_execution_contract"]
    assert frozen_estimator_execution_contract_id(contract) == (
        evidence["estimator_execution_contract_id"]
    )
    assert stable_hash(contract) == evidence["estimator_execution_contract_hash"]
    assert "unpenalized-intercept Gaussian elastic-net objective" in (
        question["description"]
    )
    assert "at least 1000 fresh replicates per design" in question["description"]
    assert "Lean formalization are not applicable" in question["description"]

    runtime_visible = json.dumps(
        {"candidate": candidate, "question": question}, sort_keys=True
    )
    for hidden_name in (
        "gold_manifest.json",
        "hidden_algorithm_harness.py",
        "hidden_empirical_harness.py",
        "reference_estimator.py",
        "semantic_reference.md",
        "semantic_rubric.json",
    ):
        assert hidden_name not in runtime_visible

    readiness = ladder["current_readiness"]
    assert readiness["scored_tasks_total"] == 95
    assert readiness["unconsumed_scored_tasks"] == 1
    assert readiness["consumed_scored_tasks"] == 94
    assert readiness["fully_gold_configured_tasks"] == 95
    assert readiness["fully_gold_passed_tasks"] == 7
