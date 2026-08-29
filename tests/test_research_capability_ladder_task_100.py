from __future__ import annotations

import hashlib
import json
from pathlib import Path

from ai_statistician.estimator_interface_contract import (
    frozen_estimator_execution_contract_id,
)
from ai_statistician.fingerprint import stable_hash
from ai_statistician.research_gold_evaluation import (
    _visible_question_hash_payload,
    validate_research_gold_benchmark_manifest,
)
from ai_statistician.research_schema import load_open_research_questions


LADDER_PATH = Path("benchmarks/research_capability_ladder_20260814.json")
VISIBLE_PATH = Path(
    "benchmarks/research_l3_scalar_linear_gaussian_filter_questions_20260829.json"
)
GOLD_MANIFEST = Path(
    "/Users/yukangzengcmac/.codex/evaluator_authority/AI-Statistician/"
    "research-l3-scalar-linear-gaussian-filter-20260829-v1/gold_manifest.json"
)
TASK_ID = "scalar_linear_gaussian_filter_known_theory_rederivation"


def test_scalar_linear_gaussian_filter_task100_is_consumed_once() -> None:
    ladder = json.loads(LADDER_PATH.read_text(encoding="utf-8"))
    candidate = next(
        row for row in ladder["initial_candidate_queue"] if row["id"] == TASK_ID
    )
    evidence = candidate["activation_evidence"]
    visible_payload = json.loads(VISIBLE_PATH.read_text(encoding="utf-8"))
    visible_question = visible_payload["questions"][0]
    loaded_question = load_open_research_questions(VISIBLE_PATH)[0]
    descriptor = validate_research_gold_benchmark_manifest(GOLD_MANIFEST)

    assert candidate["level"] == "L3"
    assert candidate["family"] == "scalar_linear_gaussian_state_space_filtering"
    assert candidate["status"] == "consumed_scored"
    assert candidate["activation_status"] == (
        "fresh_live_v1_consumed_exact_haiku_runtime_accepted_gold_failed_"
        "closed_input_contract"
    )
    assert loaded_question.id == TASK_ID
    assert loaded_question.task_intent == candidate["task_intent"]
    assert hashlib.sha256(VISIBLE_PATH.read_bytes()).hexdigest() == (
        evidence["visible_questions_sha256"]
    )
    assert stable_hash(visible_payload) == evidence["visible_question_full_hash"]
    assert stable_hash(_visible_question_hash_payload(visible_question)) == (
        evidence["runtime_visible_question_hash"]
    )
    assert frozen_estimator_execution_contract_id(
        visible_question["estimator_execution_contract"]
    ) == evidence["estimator_execution_contract_id"]
    assert hashlib.sha256(GOLD_MANIFEST.read_bytes()).hexdigest() == (
        candidate["gold_manifest_sha256"]
    )
    assert descriptor["benchmark_manifest_hash"] == candidate["gold_descriptor_hash"]
    assert descriptor["active_task_ids"] == [TASK_ID]
    assert evidence["activation_schema_version"] == 4
    assert evidence["algorithm_authority_checks_correct"] == "10/10"
    assert evidence["empirical_authority_checks_correct"] == "11/11"
    assert evidence["semantic_protocol_version"] == 11
    assert evidence["semantic_candidate_adjudication_strategy"] == (
        "integrated_plus_adversarial"
    )
    assert evidence["semantic_calibration_cases_correct"] == "6/6"
    assert evidence["semantic_candidate_mode_negative_cases_correct"] == "1/1"
    assert evidence["semantic_successful_qualification_model_calls"] == 16
    assert evidence["semantic_calibration_model"] == "claude-haiku-4-5-20251001"
    assert evidence["hidden_gold_manifest_validated"] is True
    assert evidence["gold_frozen_before_first_runtime_model_call"] is True
    assert evidence["preactivation_product_model_calls"] == 0
    assert evidence["first_runtime_model_call_occurred"] is True
    assert evidence["fresh_live_runs"] == 1
    assert evidence["runtime_invocations"] == 1
    assert evidence["activation_ledger_commit"] == (
        "674112311c05e240ce2e2fe27f1c3cdc9bce0bde"
    )
    assert evidence["runtime_model"] == "claude-haiku-4-5-20251001"
    assert evidence["runtime_product_model_calls"] == 119
    assert evidence["runtime_client_tool_model_turns"] == 118
    assert evidence["runtime_direct_model_calls"] == 1
    assert evidence["runtime_client_tool_executions"] == 132
    assert evidence["sonnet_product_calls"] == 0
    assert evidence["opus_product_calls"] == 0
    assert evidence["formalization_requirement"] == "not_applicable"
    assert evidence["formalizer_executed"] is False
    assert evidence["accepted_theory_packet_id"] == (
        "theory_derivation:3f9d48e257630534d3c3ad28"
    )
    assert evidence["hidden_theory_exact_checks_passed"] == 7
    assert evidence["hidden_theory_semantic_claims_passed"] == 8
    assert evidence["accepted_algorithm_handoff_id"] == (
        "accepted_algorithm_handoff:159509991d63d51e74ce"
    )
    assert evidence["generated_algorithm_explicit_commit"] is True
    assert evidence["generated_algorithm_handoff_accepted"] is True
    assert evidence["hidden_algorithm_checks_passed"] == 8
    assert evidence["hidden_algorithm_checks_total"] == 10
    assert evidence["hidden_algorithm_valid_cases_passed"] == 21
    assert evidence["hidden_algorithm_closed_input_contract_passed"] is False
    assert evidence["generated_simulation_confirmatory_passed"] is True
    assert evidence["simulation_upstream_algorithm_handoff_receipt_present"] is True
    assert evidence["hidden_empirical_checks_passed"] == 11
    assert evidence["hidden_empirical_checks_total"] == 11
    assert evidence["critic_research_acceptance"] is True
    assert evidence["critic_contract_gap_conflicted_with_acceptance"] is True
    assert evidence["closeout_evidence_commit"] == (
        "34b3136cce4cf5332b2d33959289a0bc819c3c74"
    )
    assert evidence["automated_full_task_passed"] is False
    assert evidence["full_task_passed"] is False
    assert evidence["trusted_capability_credit"] is False
    assert evidence["ladder_score_after_consumption"] == "7/100"
    readiness = ladder["current_readiness"]
    assert readiness["scored_tasks_total"] == 100
    assert readiness["unconsumed_scored_tasks"] == 0
    assert readiness["consumed_scored_tasks"] == 100
    assert readiness["fully_gold_configured_tasks"] == 100
    assert readiness["fully_gold_passed_tasks"] == 7
