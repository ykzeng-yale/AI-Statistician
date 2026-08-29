from __future__ import annotations

import hashlib
import json
from pathlib import Path

from ai_statistician.fingerprint import stable_hash
from ai_statistician.research_gold_evaluation import _visible_question_hash_payload


LADDER_PATH = Path("benchmarks/research_capability_ladder_20260814.json")
TASK_ID = "fisher_combined_pvalue_exact_null_theory_known_result"


def test_fisher_combination_l0_theory_records_sole_consumed_draw() -> None:
    ladder = json.loads(LADDER_PATH.read_text(encoding="utf-8"))
    candidate = next(
        row for row in ladder["initial_candidate_queue"] if row["id"] == TASK_ID
    )
    evidence = candidate["activation_evidence"]

    assert candidate["level"] == "L0"
    assert candidate["family"] == "independent_pvalue_combination_exact_null"
    assert candidate["status"] == "consumed_scored"
    assert candidate["activation_status"] == (
        "fresh_live_v1_consumed_exact_haiku_gold_passed"
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
    assert evidence["first_runtime_model_call_occurred"] is True
    assert evidence["fresh_live_runs"] == 1
    assert evidence["runtime_invocations"] == 1
    assert evidence["runtime_model"] == "claude-haiku-4-5-20251001"
    assert evidence["product_model_response_events"] == 38
    assert evidence["theory_developer_model_turns"] == 8
    assert evidence["theory_referee_model_turns"] == 10
    assert evidence["critic_evaluator_model_turns"] == 20
    assert evidence["post_runtime_evaluator_model_calls"] == 1
    assert evidence["sonnet_product_calls"] == 0
    assert evidence["opus_product_calls"] == 0
    assert evidence["formalization_requirement"] == "not_applicable"
    assert evidence["formalizer_executed"] is False
    assert evidence["theory_developer_executed"] is True
    assert evidence["generated_algorithm_executed"] is False
    assert evidence["generated_simulation_executed"] is False
    assert evidence["activation_ledger_commit"] == (
        "0f037fc494225cd26a7bd4cb26a5218173abf760"
    )
    assert evidence["activation_push_confirmed_on_work_branch_and_main"] is True
    assert evidence["model_draw_resampling_blocked"] is True
    assert evidence["product_code_head"] == (
        "cad888f239b23c023f4c416d0472d95a98d7b55c"
    )
    assert evidence["runtime_status"] == "ACCEPTED"
    assert evidence["runtime_outer_graph_iterations"] == 3
    assert evidence["runtime_research_contract_passed"] is True
    assert evidence["runtime_mode_conformant"] is True
    assert evidence["runtime_manifest_sha256"] == (
        "dcd86e1212c082d118972a2d56aa72be779764a7976811ea1bcf8ea5069d7311"
    )
    assert evidence["runtime_result_sha256"] == (
        "01957035c87a39820332e2a65c89a6da4f8ff783c82d503a674c1bff55fc767e"
    )
    assert evidence["gold_evaluation_sha256"] == (
        "a72072ab8e4b9428df0038f97f84900e63ad81e3b10e5899fbbcaaf9f9f68759"
    )
    assert evidence["accepted_theory_document_sha256"] == (
        "6903156402f2444728308d7b4971c052fa2e7e71ca1c9430249115a263cc5379"
    )
    assert evidence["accepted_theory_document_lines"] == 314
    assert evidence["theory_referee_report_sha256"] == (
        "27290010a0e26154b7953dff20889f3903b5186de0a265e00eb6cdf8eda00a2d"
    )
    assert evidence["theory_referee_report_lines"] == 253
    assert evidence["hidden_theory_exact_checks_passed"] == 7
    assert evidence["hidden_theory_semantic_claims_satisfied"] == 7
    assert evidence["hidden_theory_combined_passed"] is True
    assert evidence["hidden_runtime_feedback_generated"] is False
    assert evidence["closeout_evidence_commit"] == (
        "f12504b0d7a0b0fadc4cf762a2bfee04f4bf00ba"
    )
    assert evidence["automated_full_task_passed"] is True
    assert evidence["full_task_passed"] is True
    assert evidence["trusted_capability_credit"] is True
    assert evidence["ladder_score_before_activation"] == "6/92"
    assert evidence["ladder_score_after_activation"] == "6/93"
    assert evidence["ladder_score_after_consumption"] == "7/93"

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
    assert readiness["scored_tasks_total"] == 96
    assert readiness["unconsumed_scored_tasks"] == 1
    assert readiness["consumed_scored_tasks"] == 95
    assert readiness["fully_gold_configured_tasks"] == 96
    assert readiness["fully_gold_passed_tasks"] == 7
