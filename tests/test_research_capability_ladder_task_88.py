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


def test_glmnet_gaussian_l2_task_is_frozen_before_product_draw() -> None:
    ladder = json.loads(LADDER_PATH.read_text(encoding="utf-8"))
    candidate = next(
        row for row in ladder["initial_candidate_queue"] if row["id"] == TASK_ID
    )
    evidence = candidate["activation_evidence"]

    assert candidate["level"] == "L2"
    assert candidate["family"] == "gaussian_elastic_net_coordinate_descent"
    assert candidate["status"] == "active_scored"
    assert candidate["activation_status"] == (
        "frozen_ready_exact_haiku_product_draw_not_started"
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
        "pending_current_activation_commit"
    )
    assert evidence["activation_push_confirmed_on_work_branch_and_main"] is False
    assert evidence["preactivation_product_model_calls"] == 0
    assert evidence["preactivation_evaluator_model_calls"] == 8
    assert evidence["first_runtime_model_call_occurred"] is False
    assert evidence["fresh_live_runs"] == 0
    assert evidence["runtime_invocations"] == 0
    assert evidence["runtime_model"] == "claude-haiku-4-5-20251001"
    assert evidence["sonnet_product_calls"] == 0
    assert evidence["opus_product_calls"] == 0
    assert evidence["formalization_requirement"] == "not_applicable"
    assert evidence["formalizer_executed"] is False
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
    assert readiness["scored_tasks_total"] == 88
    assert readiness["unconsumed_scored_tasks"] == 1
    assert readiness["consumed_scored_tasks"] == 87
    assert readiness["fully_gold_configured_tasks"] == 88
    assert readiness["fully_gold_passed_tasks"] == 5
