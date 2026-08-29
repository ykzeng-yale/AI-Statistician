from __future__ import annotations

import hashlib
import json
from pathlib import Path

from ai_statistician.fingerprint import stable_hash
from ai_statistician.research_gold_evaluation import _visible_question_hash_payload
from ai_statistician.research_schema import frozen_formal_target_contract_errors


LADDER_PATH = Path("benchmarks/research_capability_ladder_20260814.json")
TASK_ID = "statlib_measure_constant_kernel_embedding_formal_known_result"


def test_statlib_kernel_embedding_l0_records_sole_kernel_closed_draw() -> None:
    ladder = json.loads(LADDER_PATH.read_text(encoding="utf-8"))
    candidate = next(
        row for row in ladder["initial_candidate_queue"] if row["id"] == TASK_ID
    )
    evidence = candidate["activation_evidence"]

    assert candidate["level"] == "L0"
    assert candidate["family"] == "measure_to_kernel_inference_formalization"
    assert candidate["status"] == "consumed_scored"
    assert candidate["activation_status"] == (
        "fresh_live_v1_consumed_exact_haiku_kernel_closed_gold_passed"
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
    assert evidence["first_runtime_model_call_occurred"] is True
    assert evidence["fresh_live_runs"] == 1
    assert evidence["runtime_invocations"] == 1
    assert evidence["runtime_model"] == "claude-haiku-4-5-20251001"
    assert evidence["sonnet_product_calls"] == 0
    assert evidence["opus_product_calls"] == 0
    assert evidence["formalization_requirement"] == "required"
    assert evidence["formalizer_executed"] is True
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
    assert evidence["product_code_head"] == (
        "a892ecef72a889f8ae6d55f9410ae2d0d595beed"
    )
    assert evidence["runtime_status"] == "ACCEPTED"
    assert evidence["runtime_research_eval_result"] == "1/1"
    assert evidence["post_runtime_gold_result"] == "1/1"
    assert evidence["post_runtime_gold_assessments"] == 1
    assert evidence["post_runtime_evaluator_model_calls"] == 0
    assert evidence["product_model_calls"] == 10
    assert evidence["formalizer_workspace_model_turns"] == 8
    assert evidence["formalizer_workspace_tool_calls"] == 9
    assert evidence["formalizer_declaration_inspections"] == 3
    assert evidence["formalizer_lean_scratch_checks"] == 3
    assert evidence["formalizer_formal_environment_searches"] == 2
    assert evidence["formalizer_source_submissions"] == 1
    assert evidence["formal_target_semantic_reviewer_model_calls"] == 1
    assert evidence["critic_model_calls"] == 1
    assert evidence["architect_model_calls"] == 0
    assert evidence["runtime_outer_graph_iterations"] == 5
    assert evidence["runtime_traces"] == 5
    assert evidence["runtime_task_handoffs"] == 4
    assert evidence["runtime_observations"] == 12
    assert evidence["initial_formal_rag_provider_calls"] == 2
    assert evidence["initial_formal_rag_provider_failures"] == 0
    assert evidence["initial_formal_rag_fused_hits"] == 4
    assert evidence["retrieved_closing_declarations"] == [
        "Kernel.measurable_kernel_of_measure",
        "Kernel.injective_kernel_of_measure",
    ]
    assert (
        evidence["retrieved_closing_declarations_disclosed_in_visible_question"]
        is False
    )
    assert evidence["model_authored_candidate_source_hash"] == (
        "8fbbb6c5caf6397371fdff855a540a7468aab1f70fbfa12b714867f12cf56dc9"
    )
    assert evidence["model_authored_candidate_file_sha256"] == (
        "fe13c98afd827447578ddcdbcb9546ad0a9f73e0360dc525ee8d7f1fac11b40c"
    )
    assert evidence["model_candidate_matches_hidden_gold_bytes"] is True
    assert evidence["hidden_gold_content_visible_to_model"] is False
    assert evidence["hidden_leakage_scan_match_count"] == 0
    assert evidence["formal_target_semantic_review_accepted"] is True
    assert evidence["formal_target_semantic_review_findings"] == 0
    assert evidence["source_theorem_kernel_verified"] is True
    assert evidence["full_frontier_theorems_proved"] == 1
    assert evidence["kernel_verified_subclaims"] == 0
    assert evidence["formal_gaps"] == 0
    assert evidence["lean_axiom_audit_clean"] is True
    assert evidence["lean_trusted_axioms"] == [
        "propext",
        "Classical.choice",
        "Quot.sound",
    ]
    assert evidence["proof_evidence_status"] == (
        "EXACT_MODEL_SOURCE_KERNEL_VERIFIED"
    )
    assert evidence["runtime_formal_status"] == (
        "EXACT_SOURCE_THEOREM_KERNEL_VERIFIED"
    )
    assert evidence["runtime_manifest_sha256"] == (
        "620c233ee8861c0d75b68bfdd142d28f34c8c82e960b730a030367d325a6b069"
    )
    assert evidence["runtime_result_sha256"] == (
        "bc744f6f6a92de3dc7a87aa5cee936a64b9d35927d92a7e09f5ccd2d587725ff"
    )
    assert evidence["gold_evaluation_sha256"] == (
        "6aacb81c6d3728fab811cf64dce4bdaee11fb0f728e63ef5d7553d037f29728c"
    )
    assert evidence["automated_full_task_passed"] is True
    assert evidence["full_task_passed"] is True
    assert evidence["trusted_capability_credit"] is True
    assert evidence["ladder_score_before_activation"] == "5/90"
    assert evidence["ladder_score_after_activation"] == "5/91"
    assert evidence["ladder_score_after_consumption"] == "6/91"
    assert evidence["post_run_shared_mechanism_change"].startswith("none;")
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

    runtime_visible = json.dumps(question, sort_keys=True)
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
    assert readiness["unconsumed_scored_tasks"] == 0
    assert readiness["consumed_scored_tasks"] == 91
    assert readiness["fully_gold_configured_tasks"] == 91
    assert readiness["fully_gold_passed_tasks"] == 6
