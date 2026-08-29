from __future__ import annotations

import hashlib
import json
from pathlib import Path

from ai_statistician.fingerprint import stable_hash
from ai_statistician.research_gold_evaluation import _visible_question_hash_payload
from ai_statistician.research_schema import frozen_formal_target_contract_errors


LADDER_PATH = Path("benchmarks/research_capability_ladder_20260814.json")
TASK_ID = "statlib_measure_constant_kernel_embedding_formal_known_result"


def test_statlib_kernel_embedding_l0_is_frozen_before_sole_product_draw() -> None:
    ladder = json.loads(LADDER_PATH.read_text(encoding="utf-8"))
    candidate = next(
        row for row in ladder["initial_candidate_queue"] if row["id"] == TASK_ID
    )
    evidence = candidate["activation_evidence"]

    assert candidate["level"] == "L0"
    assert candidate["family"] == "measure_to_kernel_inference_formalization"
    assert candidate["status"] == "active_scored"
    assert candidate["activation_status"] == (
        "frozen_ready_exact_haiku_product_draw_not_started"
    )
    assert candidate["gold_bundle_id"] == (
        "research-l0-statlib-kernel-embedding-formal-20260829-v1"
    )
    assert candidate["gold_manifest_sha256"] == (
        "8b7ad834c74c976aa2f11217b2a90a2cb2753fa48e136ea74e732af99e589073"
    )
    assert candidate["gold_descriptor_hash"] == (
        "f5165ae3452b7623af40603bb01fd2cc3f600b917e54ed87945142daa02fd783"
    )
    assert evidence["formal_authority_calibration_cases"] == 5
    assert evidence["formal_authority_calibration_cases_correct"] == 5
    assert evidence["positive_control_kernel_and_axiom_clean"] is True
    assert evidence["sorry_and_custom_axiom_negatives_rejected"] is True
    assert (
        evidence["weakened_statement_and_extra_assumption_negatives_rejected"]
        is True
    )
    assert evidence["formal_rag_source_snapshot_status"] == "BOUND_MATCH"
    assert evidence["formal_rag_query_disclosed_closing_names"] is False
    assert evidence["formal_rag_required_map_retrieved"] is True
    assert evidence["formal_rag_required_measurability_result_retrieved"] is True
    assert evidence["formal_rag_required_injectivity_result_retrieved"] is True
    assert evidence["hidden_gold_manifest_validated"] is True
    assert evidence["gold_frozen_before_first_runtime_model_call"] is True
    assert evidence["preactivation_product_model_calls"] == 0
    assert evidence["preactivation_evaluator_model_calls"] == 0
    assert evidence["first_runtime_model_call_occurred"] is False
    assert evidence["fresh_live_runs"] == 0
    assert evidence["runtime_invocations"] == 0
    assert evidence["runtime_model"] == "claude-haiku-4-5-20251001"
    assert evidence["sonnet_product_calls"] == 0
    assert evidence["opus_product_calls"] == 0
    assert evidence["formalization_requirement"] == "required"
    assert evidence["formalizer_executed"] is False
    assert evidence["theory_developer_executed"] is False
    assert evidence["generated_algorithm_executed"] is False
    assert evidence["generated_simulation_executed"] is False
    assert evidence["second_kernel_or_statement_verifier_added"] is False
    assert evidence["activation_push_required_before_first_runtime_model_call"] is True
    assert evidence["activation_ledger_commit"] == (
        "56db75e8b4639dbb78c901955e84598591dc7d12"
    )
    assert evidence["activation_push_confirmed_on_work_branch_and_main"] is True
    assert evidence["model_draw_resampling_blocked"] is True
    assert evidence["full_task_passed"] is False
    assert evidence["trusted_capability_credit"] is False
    assert evidence["ladder_score_before_activation"] == "5/90"
    assert evidence["ladder_score_after_activation"] == "5/91"

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
    assert question["task_intent"]["formal"] == "required"
    assert frozen_formal_target_contract_errors(
        question["formal_target_contract"]
    ) == []
    contract = question["formal_target_contract"]
    assert contract["lean_source_prefix_sha256"] == (
        evidence["lean_source_prefix_sha256"]
    )
    assert contract["declaration_name"] == (
        "AIStatisticianBench.measure_to_constant_kernel_embedding"
    )

    runtime_visible = json.dumps(
        {"candidate": candidate, "question": question}, sort_keys=True
    )
    for hidden_name in (
        "gold.lean",
        "negative_sorry.lean",
        "negative_custom_axiom.lean",
        "negative_weakened_conclusion.lean",
        "negative_extra_assumption.lean",
        "measurable_kernel_of_measure",
        "injective_kernel_of_measure",
    ):
        assert hidden_name not in runtime_visible

    readiness = ladder["current_readiness"]
    assert readiness["scored_tasks_total"] == 91
    assert readiness["unconsumed_scored_tasks"] == 1
    assert readiness["consumed_scored_tasks"] == 90
    assert readiness["fully_gold_configured_tasks"] == 91
    assert readiness["fully_gold_passed_tasks"] == 5
