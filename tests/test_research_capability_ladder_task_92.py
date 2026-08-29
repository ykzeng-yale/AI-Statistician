from __future__ import annotations

import hashlib
import json
from pathlib import Path

from ai_statistician.fingerprint import stable_hash
from ai_statistician.research_gold_evaluation import _visible_question_hash_payload


LADDER_PATH = Path("benchmarks/research_capability_ladder_20260814.json")
TASK_ID = "efron_stein_replacement_variance_theory_known_result"


def test_efron_stein_l0_theory_task_is_frozen_before_sole_product_draw() -> None:
    ladder = json.loads(LADDER_PATH.read_text(encoding="utf-8"))
    candidate = next(
        row for row in ladder["initial_candidate_queue"] if row["id"] == TASK_ID
    )
    evidence = candidate["activation_evidence"]

    assert candidate["level"] == "L0"
    assert candidate["family"] == "independent_coordinate_variance_inequality"
    assert candidate["status"] == "active_scored"
    assert candidate["activation_status"] == (
        "frozen_ready_exact_haiku_product_draw_not_started"
    )
    assert candidate["gold_bundle_id"] == (
        "research-l0-efron-stein-variance-theory-20260829-v1"
    )
    assert candidate["gold_manifest_sha256"] == (
        "4950bc3fa601aad70cfa15629de4ef37c275fd527abd8c934c0862e8cdc90b7a"
    )
    assert candidate["gold_descriptor_hash"] == (
        "f5c5e0f802acd0358cc7a5a271611cc68ccaae3f74232a732d6fc58ecaf9abb6"
    )
    assert evidence["visible_question_activation_commit"] == (
        "45cf096ed60c89dd81dd3423bad79cdbb6502312"
    )
    assert evidence["activation_schema_version"] == 4
    assert evidence["theory_authority_exact_checks"] == 4
    assert evidence["theory_authority_exact_checks_correct"] == 4
    assert evidence["semantic_protocol_version"] == 10
    assert evidence["semantic_activation_attempts"] == 1
    assert evidence["semantic_calibration_total_model_calls"] == 8
    assert evidence["semantic_calibration_cases"] == 6
    assert evidence["semantic_calibration_cases_correct"] == 6
    assert evidence["semantic_candidate_mode_negative_cases"] == 1
    assert evidence["semantic_candidate_mode_negative_cases_correct"] == 1
    assert evidence["semantic_reference_claims"] == 8
    assert evidence["semantic_reference_candidate_passed"] is True
    assert evidence["semantic_calibration_model"] == (
        "claude-haiku-4-5-20251001"
    )
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
    assert evidence["theory_developer_executed"] is False
    assert evidence["generated_algorithm_executed"] is False
    assert evidence["generated_simulation_executed"] is False
    assert evidence["activation_ledger_commit"] == (
        "a9fa2b9efbda4933326f0a20a0bfdf8fe17a9280"
    )
    assert evidence["activation_push_confirmed_on_work_branch_and_main"] is True
    assert evidence["model_draw_resampling_blocked"] is True
    assert evidence["full_task_passed"] is False
    assert evidence["trusted_capability_credit"] is False
    assert evidence["ladder_score_before_activation"] == "6/91"
    assert evidence["ladder_score_after_activation"] == "6/92"

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
    assert question["task_intent"]["theory"] == "required"
    assert question["task_intent"]["scientific_code"] == "not_applicable"
    assert question["task_intent"]["empirical"] == "not_applicable"
    assert question["task_intent"]["formal"] == "not_applicable"
    assert question["source"]["doi"] == "10.1214/aos/1176345462"
    assert "factor 1/2" in question["description"]
    assert "interaction example" in question["description"]

    runtime_visible = json.dumps(
        {"candidate": candidate, "question": question}, sort_keys=True
    )
    for hidden_identity in (
        "reference.md",
        "rubric.json",
        "calibration_cases.json",
        "long_form_near_miss.md",
        "candidate_mode_negative_cases.json",
        "martingale_proxy_derivation",
        "replacement_identity_and_half_factor",
    ):
        assert hidden_identity not in runtime_visible

    readiness = ladder["current_readiness"]
    assert readiness["scored_tasks_total"] == 92
    assert readiness["unconsumed_scored_tasks"] == 1
    assert readiness["consumed_scored_tasks"] == 91
    assert readiness["fully_gold_configured_tasks"] == 92
    assert readiness["fully_gold_passed_tasks"] == 6
