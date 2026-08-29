from __future__ import annotations

import hashlib
import json
from pathlib import Path

from ai_statistician.fingerprint import stable_hash
from ai_statistician.research_gold_evaluation import _visible_question_hash_payload


LADDER_PATH = Path("benchmarks/research_capability_ladder_20260814.json")
TASK_ID = "efron_stein_replacement_variance_theory_known_result"


def test_efron_stein_l0_theory_task_records_sole_consumed_failure() -> None:
    ladder = json.loads(LADDER_PATH.read_text(encoding="utf-8"))
    candidate = next(
        row for row in ladder["initial_candidate_queue"] if row["id"] == TASK_ID
    )
    evidence = candidate["activation_evidence"]

    assert candidate["level"] == "L0"
    assert candidate["family"] == "independent_coordinate_variance_inequality"
    assert candidate["status"] == "consumed_scored"
    assert candidate["activation_status"] == (
        "fresh_live_v1_consumed_exact_haiku_blocked_gold_failed"
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
    assert evidence["first_runtime_model_call_occurred"] is True
    assert evidence["fresh_live_runs"] == 1
    assert evidence["runtime_invocations"] == 1
    assert evidence["runtime_model"] == "claude-haiku-4-5-20251001"
    assert evidence["sonnet_product_calls"] == 0
    assert evidence["opus_product_calls"] == 0
    assert evidence["formalization_requirement"] == "not_applicable"
    assert evidence["formalizer_executed"] is False
    assert evidence["theory_developer_executed"] is True
    assert evidence["generated_algorithm_executed"] is False
    assert evidence["generated_simulation_executed"] is True
    assert evidence["activation_ledger_commit"] == (
        "a9fa2b9efbda4933326f0a20a0bfdf8fe17a9280"
    )
    assert evidence["activation_push_confirmed_on_work_branch_and_main"] is True
    assert evidence["model_draw_resampling_blocked"] is True
    assert evidence["product_code_head"] == (
        "03ca4b52041d1f9281e357c20093289e744a38eb"
    )
    assert evidence["runtime_status"] == "BLOCKED"
    assert evidence["runtime_research_eval_result"] == "0/1"
    assert evidence["post_runtime_gold_result"] == "0/1"
    assert evidence["post_runtime_gold_assessments"] == 1
    assert evidence["post_runtime_evaluator_model_calls"] == 1
    assert evidence["product_model_calls"] == 60
    assert evidence["theory_developer_workspace_model_turns"] == 35
    assert evidence["theory_developer_workspace_tool_calls"] == 35
    assert evidence["theory_preflight_reviewer_model_turns"] == 22
    assert evidence["theory_preflight_reviewer_tool_calls"] == 22
    assert evidence["theory_preflight_reviews"] == 2
    assert evidence["theory_preflight_rejections"] == 1
    assert evidence["theory_preflight_acceptances"] == 1
    assert evidence["simulation_engineer_model_calls"] == 1
    assert evidence["generated_simulation_sandbox_executions"] == 7
    assert evidence["generated_code_semantic_reviewer_model_calls"] == 1
    assert evidence["architect_feedback_route_model_calls"] == 1
    assert evidence["critic_model_calls"] == 0
    assert evidence["runtime_outer_graph_iterations"] == 7
    assert evidence["runtime_traces"] == 7
    assert evidence["runtime_task_handoffs"] == 6
    assert evidence["runtime_observations"] == 10
    assert evidence["accepted_theory_packet_hash"] == (
        "954644b9fddeb412c5a7dac4ef785ee81a639039f975b3d10e340967895edf40"
    )
    assert evidence["accepted_theory_document_count"] == 1
    assert evidence["accepted_theory_document_set_hash"] == (
        "b405afa6402c70b5d08f3c28d51d29a59ed60ca7651f810ae7abb8daab8764fd"
    )
    assert evidence["accepted_theory_document_sha256"] == (
        "4011a401514c3274dc665f5a8c78a744ba23a202efc44444296422d61515483e"
    )
    assert evidence["accepted_theory_document_lines"] == 469
    assert evidence["hidden_theory_semantic_candidate_status"] == "FAIL"
    assert evidence["hidden_theory_semantic_claims"] == 8
    assert evidence["hidden_theory_semantic_claims_satisfied"] == 7
    assert evidence["hidden_theory_semantic_claims_violated"] == 1
    assert evidence["hidden_theory_semantic_violated_claim"] == (
        "general_proxy_bound"
    )
    assert evidence["hidden_gold_content_visible_to_model"] is False
    assert evidence["hidden_leakage_scan_match_count"] == 0
    assert evidence["hidden_expected_values_disclosed"] is False
    assert evidence["runtime_feedback_generated_from_hidden_gold"] is False
    assert evidence["unresolved_gap_disclosure_present"] is False
    assert evidence["task_intent_routing_conformant"] is False
    assert evidence["runtime_manifest_sha256"] == (
        "81fbd22860c0b28991b2e189d2f5ec5672f3411d9bf9d04fd39e9cc526ea436f"
    )
    assert evidence["runtime_result_sha256"] == (
        "0741621aa15b7a667c3a27c1f62e326d165a2ac8cf86f391be49fe076a70e821"
    )
    assert evidence["gold_evaluation_sha256"] == (
        "39466d06b0760de5c57081f56905ff9c081375ac9eb0f514445eec63d4d57d93"
    )
    assert evidence["closeout_evidence_commit"] == (
        "2e5edb5b7ba46eaf89dcff14347423981847450d"
    )
    assert evidence["full_task_passed"] is False
    assert evidence["trusted_capability_credit"] is False
    assert evidence["ladder_score_before_activation"] == "6/91"
    assert evidence["ladder_score_after_activation"] == "6/92"
    assert evidence["ladder_score_after_consumption"] == "6/92"
    assert evidence["post_run_shared_mechanism_change"].startswith(
        "The existing architect plan boundary"
    )
    for forbidden in ("rerun", "resume", "repair", "rescore", "resample"):
        assert forbidden in evidence["boundary"]

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
    assert readiness["scored_tasks_total"] == 95
    assert readiness["unconsumed_scored_tasks"] == 0
    assert readiness["consumed_scored_tasks"] == 95
    assert readiness["fully_gold_configured_tasks"] == 95
    assert readiness["fully_gold_passed_tasks"] == 7
