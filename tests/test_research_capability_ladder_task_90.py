from __future__ import annotations

import hashlib
import json
from pathlib import Path

from ai_statistician.estimator_interface_contract import (
    frozen_estimator_execution_contract_id,
)
from ai_statistician.fingerprint import stable_hash


LADDER_PATH = Path("benchmarks/research_capability_ladder_20260814.json")
TASK_ID = "binary_runs_fixed_counts_known_result"


def test_binary_runs_l0_task_is_frozen_and_unconsumed() -> None:
    ladder = json.loads(LADDER_PATH.read_text(encoding="utf-8"))
    candidate = next(
        row for row in ladder["initial_candidate_queue"] if row["id"] == TASK_ID
    )
    evidence = candidate["activation_evidence"]

    assert candidate["level"] == "L0"
    assert candidate["family"] == "fixed_count_binary_runs"
    assert candidate["status"] == "active_scored"
    assert candidate["activation_status"] == (
        "frozen_ready_preactivated_unconsumed"
    )
    assert candidate["gold_bundle_id"] == (
        "research-l0-binary-runs-20260828-v1"
    )
    assert candidate["gold_manifest_sha256"] == (
        "84c9dbbe3abe9edd9d5903761e0bea741740449fe34cd36a57084fb3bb0040d0"
    )
    assert candidate["gold_descriptor_hash"] == (
        "36131f46a58951815bdd2d6941b84fe6e0b20fcffe32bb9f2ab1fd44aeb84610"
    )
    assert evidence["visible_question_activation_commit"] == (
        "a15fef2f40416b354f64ffeedb00d4b88fcc3a8a"
    )
    assert evidence["activation_schema_version"] == 4
    assert evidence["reference_algorithm_contract_checks_passed"] is True
    assert evidence["reference_algorithm_valid_cases"] == 4
    assert evidence["reference_algorithm_invalid_cases"] == 16
    assert evidence["reference_algorithm_invariance_checks"] == 8
    assert evidence["algorithm_negative_variants"] == 4
    assert evidence["reference_empirical_designs_passed"] == 2
    assert evidence["reference_empirical_replicates_per_design"] == 4000
    assert evidence["reference_empirical_invocations"] == 8000
    assert evidence["semantic_protocol_version"] == 10
    assert evidence["semantic_activation_attempts"] == 1
    assert evidence["semantic_calibration_total_model_calls"] == 4
    assert evidence["semantic_calibration_cases_correct"] == 2
    assert evidence["semantic_candidate_mode_negative_cases_correct"] == 1
    assert evidence["semantic_reference_claims"] == 6
    assert evidence["semantic_reference_candidate_passed"] is True
    assert evidence["semantic_calibration_model"] == (
        "claude-haiku-4-5-20251001"
    )
    assert evidence["activation_reference_tasks_passed"] == 1
    assert evidence["activation_negative_controls_rejected"] == 5
    assert evidence["activation_semantic_reference_documents_passed"] == 1
    assert (
        evidence[
            "activation_semantic_candidate_mode_negative_controls_rejected"
        ]
        == 1
    )
    assert evidence["activation_semantic_model_calls"] == 0
    assert evidence["activation_semantic_qualification_model_calls"] == 4
    assert evidence["activation_semantic_qualification_reused"] is True
    assert evidence["hidden_gold_manifest_validated"] is True
    assert evidence["gold_frozen_before_first_runtime_model_call"] is True
    assert evidence["activation_ledger_commit"] == (
        "fa3e0f930da1c709d068ae1f467eb4d46e37c037"
    )
    assert evidence["preactivation_product_model_calls"] == 0
    assert evidence["preactivation_evaluator_model_calls"] == 4
    assert evidence["first_runtime_model_call_occurred"] is False
    assert evidence["fresh_live_runs"] == 0
    assert evidence["runtime_invocations"] == 0
    assert evidence["activation_push_confirmed_on_work_branch_and_main"] is True
    assert evidence["formalization_requirement"] == "not_applicable"
    assert evidence["formalizer_executed"] is False
    assert evidence["model_draw_resampling_blocked"] is False
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
    contract = question["estimator_execution_contract"]
    assert frozen_estimator_execution_contract_id(contract) == (
        evidence["estimator_execution_contract_id"]
    )
    assert stable_hash(contract) == evidence["estimator_execution_contract_hash"]
    assert "authoritative Markdown/LaTeX Theory workspace" in question["description"]
    assert "exactly 4000 fresh" in question["description"]
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
        "candidate_mode_near_miss.md",
    ):
        assert hidden_name not in runtime_visible

    readiness = ladder["current_readiness"]
    assert readiness["scored_tasks_total"] == 90
    assert readiness["unconsumed_scored_tasks"] == 1
    assert readiness["consumed_scored_tasks"] == 89
    assert readiness["fully_gold_configured_tasks"] == 90
    assert readiness["fully_gold_passed_tasks"] == 5
