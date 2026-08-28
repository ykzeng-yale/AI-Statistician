from __future__ import annotations

import hashlib
import json
from pathlib import Path


LADDER_PATH = Path("benchmarks/research_capability_ladder_20260814.json")
TASK_ID = "statlib_qmd_score_mean_zero_univ_formal_known_result"


def test_statlib_qmd_l0_formal_task_is_frozen_before_product_draw() -> None:
    ladder = json.loads(LADDER_PATH.read_text(encoding="utf-8"))
    candidate = next(
        row for row in ladder["initial_candidate_queue"] if row["id"] == TASK_ID
    )
    evidence = candidate["activation_evidence"]

    assert candidate["level"] == "L0"
    assert candidate["family"] == (
        "quadratic_mean_differentiability_score_formalization"
    )
    assert candidate["status"] == "active_scored"
    assert candidate["activation_status"] == (
        "frozen_ready_exact_haiku_product_draw_not_started"
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
    assert evidence["model_draw_resampling_blocked"] is True
    assert evidence["activation_push_confirmed_on_work_branch_and_main"] is False

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
    assert readiness["scored_tasks_total"] == 85
    assert readiness["unconsumed_scored_tasks"] == 1
    assert readiness["consumed_scored_tasks"] == 84
    assert readiness["fully_gold_configured_tasks"] == 85
    assert readiness["fully_gold_passed_tasks"] == 4
    assert readiness["latest_shared_mechanism_head"] == (
        "f34f4f04d34c5986224f77edb5dacc52c8f2207a"
    )
