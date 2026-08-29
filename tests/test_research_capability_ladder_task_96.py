from __future__ import annotations

import hashlib
import json
from pathlib import Path

from ai_statistician.fingerprint import stable_hash
from ai_statistician.research_gold_evaluation import _visible_question_hash_payload


LADDER_PATH = Path("benchmarks/research_capability_ladder_20260814.json")
TASK_ID = "moran_i_randomization_expectation_known_result"


def test_moran_i_integrated_l0_is_frozen_before_its_sole_draw() -> None:
    ladder = json.loads(LADDER_PATH.read_text(encoding="utf-8"))
    candidate = next(
        row for row in ladder["initial_candidate_queue"] if row["id"] == TASK_ID
    )
    evidence = candidate["activation_evidence"]

    assert candidate["level"] == "L0"
    assert candidate["family"] == "spatial_randomization_autocorrelation"
    assert candidate["status"] == "active_scored"
    assert candidate["activation_status"] == (
        "frozen_ready_schema_v4_exact_haiku_single_draw"
    )
    assert candidate["gold_bundle_id"] == (
        "research-l0-moran-i-randomization-20260829-v1"
    )
    assert candidate["gold_manifest_sha256"] == (
        "a42a9d931a94b921e5b75f0cc89bd82d12da6277b9affa1375ee5ef137ad3d67"
    )
    assert candidate["gold_descriptor_hash"] == (
        "978a0a6b7d9c5a15d9bfffd5688b8809881772a2764692ff6081c01decf64c07"
    )
    assert evidence["visible_question_activation_commit"] == (
        "1dffb2203d60a51a3b174f636a169f6fd6514270"
    )
    assert evidence["estimator_execution_contract_id"] == (
        "frozen_estimator_execution_contract:fed33f308908b86a648c"
    )
    assert evidence["activation_schema_version"] == 4
    assert evidence["theory_authority_exact_checks"] == 7
    assert evidence["theory_authority_exact_checks_correct"] == 7
    assert evidence["algorithm_authority_checks"] == 7
    assert evidence["algorithm_authority_checks_correct"] == 7
    assert evidence["empirical_authority_checks"] == 10
    assert evidence["empirical_authority_checks_correct"] == 10
    assert evidence["semantic_protocol_version"] == 10
    assert evidence["semantic_calibration_total_model_calls"] == 8
    assert evidence["semantic_calibration_cases"] == 6
    assert evidence["semantic_calibration_cases_correct"] == 6
    assert evidence["semantic_candidate_mode_negative_cases"] == 1
    assert evidence["semantic_candidate_mode_negative_cases_correct"] == 1
    assert evidence["semantic_reference_claims"] == 8
    assert evidence["semantic_reference_candidate_passed"] is True
    assert evidence["semantic_activation_judgment_hash"] == (
        "68c7ca1a2fbf2dca43e317b6784e2e25eaa9a25798c609aa5098ff25bd481622"
    )
    assert evidence["semantic_calibration_model"] == (
        "claude-haiku-4-5-20251001"
    )
    assert evidence["activation_reference_tasks_passed"] == 1
    assert evidence["activation_negative_controls_rejected"] == 4
    assert evidence["activation_semantic_reference_documents_passed"] == 1
    assert evidence[
        "activation_semantic_candidate_mode_negative_controls_rejected"
    ] == 1
    assert evidence["activation_semantic_model_calls"] == 0
    assert evidence["activation_semantic_qualification_model_calls"] == 8
    assert evidence["activation_semantic_qualification_reused"] is True
    assert evidence["hidden_gold_manifest_validated"] is True
    assert evidence["gold_frozen_before_first_runtime_model_call"] is True
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
    assert evidence["activation_ledger_commit"] == "pending_activation_commit"
    assert evidence["activation_push_confirmed_on_work_branch_and_main"] is False
    assert evidence["model_draw_resampling_blocked"] is True
    assert evidence["automated_full_task_passed"] is False
    assert evidence["full_task_passed"] is False
    assert evidence["trusted_capability_credit"] is False
    assert evidence["ladder_score_before_activation"] == "7/95"
    assert evidence["ladder_score_after_activation"] == "7/96"

    visible_path = Path(candidate["visible_questions_path"])
    assert hashlib.sha256(visible_path.read_bytes()).hexdigest() == (
        evidence["visible_questions_sha256"]
    )
    question = json.loads(visible_path.read_text(encoding="utf-8"))["questions"][0]
    assert question["id"] == TASK_ID
    assert stable_hash(question) == evidence["visible_question_full_hash"]
    assert stable_hash(_visible_question_hash_payload(question)) == (
        evidence["runtime_visible_question_hash"]
    )
    assert question["task_intent"] == candidate["task_intent"]
    assert question["task_intent"]["formal"] == "not_applicable"
    assert question["source"]["primary_paper"]["doi"] == (
        "10.1093/biomet/37.1-2.17"
    )
    assert question["source"]["open_source_implementation"]["commit"] == (
        "dcd9c74bb2b78563c45d4f4a7977da9315d45c56"
    )

    runtime_visible = json.dumps(
        {"candidate": candidate, "question": question}, sort_keys=True
    )
    for hidden_identity in (
        "gold_manifest.json",
        "semantic_reference.md",
        "semantic_rubric.json",
        "semantic_calibration_cases.json",
        "candidate_mode_near_miss.md",
        "candidate_mode_negative_cases.json",
        "reference_estimator.py",
        "negative_missing_global_normalization.py",
        "negative_zero_null_expectation.py",
    ):
        assert hidden_identity not in runtime_visible

    readiness = ladder["current_readiness"]
    assert readiness["scored_tasks_total"] == 96
    assert readiness["unconsumed_scored_tasks"] == 1
    assert readiness["consumed_scored_tasks"] == 95
    assert readiness["fully_gold_configured_tasks"] == 96
    assert readiness["fully_gold_passed_tasks"] == 7
