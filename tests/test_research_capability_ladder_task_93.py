from __future__ import annotations

import hashlib
import json
from pathlib import Path

from ai_statistician.fingerprint import stable_hash
from ai_statistician.research_gold_evaluation import _visible_question_hash_payload


LADDER_PATH = Path("benchmarks/research_capability_ladder_20260814.json")
TASK_ID = "fisher_combined_pvalue_exact_null_theory_known_result"


def test_fisher_combination_l0_theory_is_frozen_before_sole_draw() -> None:
    ladder = json.loads(LADDER_PATH.read_text(encoding="utf-8"))
    candidate = next(
        row for row in ladder["initial_candidate_queue"] if row["id"] == TASK_ID
    )
    evidence = candidate["activation_evidence"]

    assert candidate["level"] == "L0"
    assert candidate["family"] == "independent_pvalue_combination_exact_null"
    assert candidate["status"] == "active_scored"
    assert candidate["activation_status"] == (
        "frozen_ready_exact_haiku_product_draw_not_started"
    )
    assert candidate["gold_bundle_id"] == (
        "research-l0-fisher-combined-pvalue-theory-20260829-v1"
    )
    assert candidate["gold_manifest_sha256"] == (
        "c93ed7b5e6264a99fa0e79d1f9287e4ac8b50d2faf63a60d3c5792e9bb0e8a19"
    )
    assert candidate["gold_descriptor_hash"] == (
        "a6e59a8f2003b43df9ce801aff8de673a3f05dd356f4792290c47bb1e4b271e2"
    )
    assert evidence["visible_question_activation_commit"] == (
        "b86b3b066f93423240fc1e86ad5de33dc2c4ad9c"
    )
    assert evidence["activation_schema_version"] == 4
    assert evidence["theory_authority_exact_checks"] == 7
    assert evidence["theory_authority_exact_checks_correct"] == 7
    assert evidence["semantic_protocol_version"] == 10
    assert evidence["semantic_activation_attempts"] == 1
    assert evidence["semantic_calibration_total_model_calls"] == 8
    assert evidence["semantic_calibration_cases"] == 6
    assert evidence["semantic_calibration_cases_correct"] == 6
    assert evidence["semantic_candidate_mode_negative_cases"] == 1
    assert evidence["semantic_candidate_mode_negative_cases_correct"] == 1
    assert evidence["semantic_reference_claims"] == 7
    assert evidence["semantic_reference_candidate_passed"] is True
    assert evidence["semantic_calibration_model"] == (
        "claude-haiku-4-5-20251001"
    )
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
    assert evidence["theory_developer_executed"] is False
    assert evidence["generated_algorithm_executed"] is False
    assert evidence["generated_simulation_executed"] is False
    assert evidence["activation_ledger_commit"] == (
        "0f037fc494225cd26a7bd4cb26a5218173abf760"
    )
    assert evidence["activation_push_confirmed_on_work_branch_and_main"] is True
    assert evidence["model_draw_resampling_blocked"] is True
    assert evidence["full_task_passed"] is False
    assert evidence["trusted_capability_credit"] is False
    assert evidence["ladder_score_before_activation"] == "6/92"
    assert evidence["ladder_score_after_activation"] == "6/93"

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
    assert question["source"]["doi"] == "10.2307/2681650"
    assert "upper-tail combined p-value" in question["description"]
    assert "k=1 reduction" in question["description"]

    runtime_visible = json.dumps(
        {"candidate": candidate, "question": question}, sort_keys=True
    )
    for hidden_identity in (
        "semantic_reference.md",
        "semantic_rubric.json",
        "semantic_calibration_cases.json",
        "candidate_mode_near_miss.md",
        "candidate_mode_negative_cases.json",
        "claim:upper_tail_formula",
        "candidate-mode:fisher-polished-tail-off-by-one",
    ):
        assert hidden_identity not in runtime_visible

    readiness = ladder["current_readiness"]
    assert readiness["scored_tasks_total"] == 93
    assert readiness["unconsumed_scored_tasks"] == 1
    assert readiness["consumed_scored_tasks"] == 92
    assert readiness["fully_gold_configured_tasks"] == 93
    assert readiness["fully_gold_passed_tasks"] == 6
