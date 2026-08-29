from __future__ import annotations

import hashlib
import json
from pathlib import Path

from ai_statistician.fingerprint import stable_hash
from ai_statistician.research_gold_evaluation import _visible_question_hash_payload


LADDER_PATH = Path("benchmarks/research_capability_ladder_20260814.json")
TASK_ID = "newey_west_mean_hac_known_result"


def test_newey_west_integrated_l0_sole_draw_is_consumed_and_failed() -> None:
    ladder = json.loads(LADDER_PATH.read_text(encoding="utf-8"))
    candidate = next(
        row for row in ladder["initial_candidate_queue"] if row["id"] == TASK_ID
    )
    evidence = candidate["activation_evidence"]

    assert candidate["level"] == "L0"
    assert candidate["family"] == "stationary_mean_hac_inference"
    assert candidate["status"] == "consumed_scored"
    assert candidate["activation_status"] == (
        "fresh_live_v1_consumed_exact_haiku_theory_preflight_blocked_gold_failed"
    )
    assert candidate["gold_bundle_id"] == (
        "research-l0-newey-west-mean-hac-20260829-v1"
    )
    assert candidate["gold_manifest_sha256"] == (
        "27ec83cebf7f4cc5ac80732eaa2708841ac7cfcd1245a9aa25ecd66d4c1b87a0"
    )
    assert candidate["gold_descriptor_hash"] == (
        "f0d1b81d9e5d92728c5c4cd12f178b61722cf494327e82fe7cbe2155b2038393"
    )
    assert evidence["codex_harness_mechanism_head"] == (
        "e734732e2c71d68107a879b20fb839dad831645e"
    )
    assert evidence["visible_question_activation_commit"] == (
        "bb00c72f8b078380594add02f65e127a569bf04e"
    )
    assert evidence["research_source_manifest_sha256"] == (
        "5229036d207a3cbe1a1da21f3456015a1da364f949d055a341b5d060af37a8ef"
    )
    assert evidence["estimator_execution_contract_id"] == (
        "frozen_estimator_execution_contract:1054b33b7de60c0ebdee"
    )
    assert evidence["activation_schema_version"] == 4
    assert evidence["theory_authority_exact_checks"] == 7
    assert evidence["theory_authority_exact_checks_correct"] == 7
    assert evidence["algorithm_authority_checks"] == 11
    assert evidence["algorithm_authority_checks_correct"] == 11
    assert evidence["empirical_authority_checks"] == 9
    assert evidence["empirical_authority_checks_correct"] == 9
    assert evidence["semantic_protocol_version"] == 10
    assert evidence["semantic_activation_attempts"] == 2
    assert evidence["semantic_calibration_total_model_calls"] == 23
    assert evidence["semantic_first_attempt_model_calls"] == 15
    assert evidence["semantic_first_attempt_cases"] == 13
    assert evidence["semantic_first_attempt_cases_correct"] == 12
    assert evidence["semantic_successful_qualification_model_calls"] == 8
    assert evidence["semantic_calibration_cases"] == 6
    assert evidence["semantic_calibration_cases_correct"] == 6
    assert evidence["semantic_candidate_mode_negative_cases"] == 1
    assert evidence["semantic_candidate_mode_negative_cases_correct"] == 1
    assert evidence["semantic_reference_claims"] == 10
    assert evidence["semantic_reference_candidate_passed"] is True
    assert evidence["semantic_calibration_model"] == (
        "claude-haiku-4-5-20251001"
    )
    assert evidence["activation_reference_tasks_passed"] == 1
    assert evidence["activation_negative_controls_rejected"] == 3
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
    assert evidence["preactivation_evaluator_model_calls"] == 23
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
    assert evidence["generated_simulation_executed"] is False
    assert evidence["activation_ledger_commit"] == (
        "67f0b88b05094e568cd44091dec2a21234d583ca"
    )
    assert evidence["activation_push_confirmed_on_work_branch_and_main"] is True
    assert evidence["model_draw_resampling_blocked"] is True
    assert evidence["product_code_head"] == (
        "262b593f287917081b5fe51572375f946c02ca45"
    )
    assert evidence["runtime_status"] == "BLOCKED"
    assert evidence["runtime_terminal_classification"] == (
        "architect_theory_execution_preflight_stalled"
    )
    assert evidence["runtime_outer_graph_iterations"] == 5
    assert evidence["product_model_response_events"] == 54
    assert evidence["product_model_call_breakdown"] == {
        "theory_developer": 30,
        "independent_theory_preflight": 24,
    }
    assert evidence["client_tool_executions"] == 64
    assert evidence["codex_style_read_batches_observed"] is True
    assert evidence["independently_accepted_theory_packet"] is False
    assert evidence["hidden_theory_execution_attempted"] is False
    assert evidence["hidden_algorithm_execution_attempted"] is False
    assert evidence["hidden_empirical_execution_attempted"] is False
    assert evidence["post_runtime_evaluator_model_calls"] == 0
    assert evidence["hidden_leak_match_count"] == 0
    assert evidence["operator_disposition"] == "FAILED"
    assert evidence["operator_audit_path"] == (
        "docs/operator_audits/newey_west_mean_hac_l0_v1.md"
    )
    assert evidence["runtime_manifest_sha256"] == (
        "40ba5feab05a9267d5f6913221bcd2c83c00c5da6f69345e9783adb5cb1468e2"
    )
    assert evidence["gold_evaluation_sha256"] == (
        "c3b3a0772fc081bd618dc86ff6e0314ea350a39bb49e49294eaf08ab6f266195"
    )
    assert evidence["automated_full_task_passed"] is False
    assert evidence["full_task_passed"] is False
    assert evidence["trusted_capability_credit"] is False
    assert evidence["ladder_score_before_activation"] == "7/93"
    assert evidence["ladder_score_after_activation"] == "7/94"
    assert evidence["ladder_score_after_consumption"] == "7/94"

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
    assert question["task_intent"]["scientific_code"] == "required"
    assert question["task_intent"]["empirical"] == "required"
    assert question["task_intent"]["formal"] == "not_applicable"
    assert question["source"]["primary_paper"]["doi"] == "10.2307/1913610"
    assert question["source"]["implementation_convention"]["commit"] == (
        "b24082f15d7603ffb250c282f34df7df3db10cb2"
    )

    runtime_visible = json.dumps(
        {"candidate": candidate, "question": question}, sort_keys=True
    )
    for hidden_identity in (
        "semantic_reference.md",
        "semantic_rubric.json",
        "semantic_calibration_cases.json",
        "candidate_mode_near_miss.md",
        "candidate_mode_negative_cases.json",
        "reference_estimator.py",
        "negative_open_request_contract.py",
        "negative_iid_only.py",
    ):
        assert hidden_identity not in runtime_visible

    readiness = ladder["current_readiness"]
    assert readiness["scored_tasks_total"] == 98
    assert readiness["unconsumed_scored_tasks"] == 1
    assert readiness["consumed_scored_tasks"] == 97
    assert readiness["fully_gold_configured_tasks"] == 98
    assert readiness["fully_gold_passed_tasks"] == 7
