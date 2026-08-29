from __future__ import annotations

import hashlib
import json
from pathlib import Path


LADDER_PATH = Path("benchmarks/research_capability_ladder_20260814.json")
TASK_ID = "statlib_qmd_score_mean_zero_univ_formal_known_result"


def test_statlib_qmd_l0_formal_task_records_sole_kernel_closed_draw() -> None:
    ladder = json.loads(LADDER_PATH.read_text(encoding="utf-8"))
    candidate = next(
        row for row in ladder["initial_candidate_queue"] if row["id"] == TASK_ID
    )
    evidence = candidate["activation_evidence"]

    assert candidate["level"] == "L0"
    assert candidate["family"] == (
        "quadratic_mean_differentiability_score_formalization"
    )
    assert candidate["status"] == "consumed_scored"
    assert candidate["activation_status"] == (
        "fresh_live_v1_consumed_exact_haiku_kernel_closed_gold_passed"
    )
    assert candidate["gold_bundle_id"] == (
        "research-l0-statlib-qmd-score-mean-zero-formal-20260828-v1"
    )
    assert candidate["gold_manifest_sha256"] == (
        "12144b70d037f36de48a6606fc0fe43b484f64d2681f0503dd71fa3f7d0cb746"
    )
    assert candidate["gold_descriptor_hash"] == (
        "950706fb4efd1a4712baf8cea2f2f4768855b9686201ab5224dc2566c0148b66"
    )
    assert evidence["shared_formal_gold_mechanism_commit"] == (
        "f34f4f04d34c5986224f77edb5dacc52c8f2207a"
    )
    assert evidence["formal_authority_calibration_cases"] == 5
    assert evidence["formal_authority_calibration_cases_correct"] == 5
    assert evidence["positive_control_kernel_and_axiom_clean"] is True
    assert evidence["sorry_and_custom_axiom_negatives_rejected"] is True
    assert (
        evidence["weakened_statement_and_extra_assumption_negatives_rejected"]
        is True
    )
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
    assert evidence["model_draw_resampling_blocked"] is True
    assert evidence["activation_ledger_commit"] == (
        "d10c8ec28803a32e1b2d87606c4ed761ec0238fe"
    )
    assert evidence["activation_push_confirmed_on_work_branch_and_main"] is True
    assert evidence["product_code_head"] == (
        "b277cdd9b7ed2ec8e8522900569642347f544936"
    )
    assert evidence["runtime_status"] == "ACCEPTED"
    assert evidence["runtime_research_eval_result"] == "1/1"
    assert evidence["post_runtime_gold_result"] == "1/1"
    assert evidence["post_runtime_gold_assessments"] == 1
    assert evidence["post_runtime_evaluator_model_calls"] == 0
    assert evidence["product_model_calls"] == 6
    assert evidence["formalizer_workspace_model_turns"] == 4
    assert evidence["formalizer_workspace_tool_calls"] == 5
    assert evidence["formalizer_declaration_inspections"] == 2
    assert evidence["formalizer_lean_scratch_checks"] == 2
    assert evidence["formalizer_source_submissions"] == 1
    assert evidence["formal_target_semantic_reviewer_model_calls"] == 1
    assert evidence["critic_model_calls"] == 1
    assert evidence["architect_model_calls"] == 0
    assert evidence["runtime_outer_graph_iterations"] == 5
    assert evidence["runtime_traces"] == 5
    assert evidence["runtime_task_handoffs"] == 4
    assert evidence["initial_formal_rag_provider_calls"] == 2
    assert evidence["initial_formal_rag_provider_failures"] == 0
    assert evidence["initial_formal_rag_fused_hits"] == 4
    assert evidence["retrieved_closing_declaration"] == (
        "QMD.integral_score_eq_zero_of_mem_nhds"
    )
    assert (
        evidence["retrieved_closing_declaration_disclosed_in_visible_question"]
        is False
    )
    assert evidence["model_authored_candidate_source_hash"] == (
        "d695c50d32f4ef6766eb5cf106d98300b0a136d2a46a4571336ad109dd96fef3"
    )
    assert evidence["model_candidate_differs_from_hidden_gold_bytes"] is True
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
        "e725916416ebac9909a999e08f73048086804cd6ffed6ac091c396589a539f27"
    )
    assert evidence["gold_evaluation_sha256"] == (
        "678af48b252651cd5ab4890dde1d9d51cc14004d920956d97f901f07d49f7352"
    )
    assert evidence["closeout_evidence_commit"] == (
        "b3c3036654dd137ef0ba229a1ebb9cda27a593b4"
    )
    assert evidence["automated_full_task_passed"] is True
    assert evidence["full_task_passed"] is True
    assert evidence["trusted_capability_credit"] is True
    assert evidence["ladder_score_after_consumption"] == "5/85"
    assert evidence["post_run_shared_mechanism_change"].startswith("none;")
    for forbidden in ("rerun", "resume", "repair", "rescore", "resample"):
        assert forbidden in evidence["boundary"]

    visible_path = Path(candidate["visible_questions_path"])
    assert hashlib.sha256(visible_path.read_bytes()).hexdigest() == (
        evidence["visible_questions_sha256"]
    )
    question = json.loads(visible_path.read_text(encoding="utf-8"))["questions"][0]
    assert question["id"] == TASK_ID
    assert question["task_intent"] == candidate["task_intent"]
    assert question["task_intent"] == {
        "source_replication": "not_applicable",
        "theory": "not_applicable",
        "scientific_code": "not_applicable",
        "empirical": "not_applicable",
        "formal": "required",
        "novelty": "not_applicable",
        "unresolved_gaps": "not_applicable",
    }
    contract = question["formal_target_contract"]
    assert contract["declaration_name"] == (
        "AIStatisticianBench.qmd_score_mean_zero_univ"
    )
    assert contract["lean_source_prefix_sha256"] == (
        evidence["lean_source_prefix_sha256"]
    )
    assert contract["proof_visibility"] == "hidden"
    assert contract["lean_environment"]["statlib_commit"] == (
        "6575d611b5d32ef6013e9560d30b1a82a1972fb6"
    )
    assert "integral_score_eq_zero_of_mem_nhds" not in json.dumps(question)

    runtime_visible = json.dumps(
        {"candidate": candidate, "question": question}, sort_keys=True
    )
    for hidden_name in (
        "gold.lean",
        "negative_sorry.lean",
        "negative_custom_axiom.lean",
        "negative_weakened_conclusion.lean",
        "negative_extra_assumption.lean",
        "calibration.json",
    ):
        assert hidden_name not in runtime_visible

    readiness = ladder["current_readiness"]
    assert readiness["scored_tasks_total"] == 94
    assert readiness["unconsumed_scored_tasks"] == 0
    assert readiness["consumed_scored_tasks"] == 94
    assert readiness["fully_gold_configured_tasks"] == 94
    assert readiness["fully_gold_passed_tasks"] == 7
    assert readiness["latest_shared_mechanism_head"] == (
        "e734732e2c71d68107a879b20fb839dad831645e"
    )
