from __future__ import annotations

import hashlib
import json
from pathlib import Path


LADDER_PATH = Path("benchmarks/research_capability_ladder_20260814.json")
TASK_ID = "good_turing_missing_mass_bias_theory_known_result"


def test_good_turing_l0_theory_task_records_immutable_consumed_result() -> None:
    ladder = json.loads(LADDER_PATH.read_text(encoding="utf-8"))
    candidate = next(
        row for row in ladder["initial_candidate_queue"] if row["id"] == TASK_ID
    )
    evidence = candidate["activation_evidence"]

    assert candidate["level"] == "L0"
    assert candidate["family"] == "countable_occupancy_missing_mass_theory"
    assert candidate["status"] == "consumed_scored"
    assert candidate["activation_status"] == (
        "fresh_live_v1_consumed_runtime_accepted_hidden_theory_semantic_failed"
    )
    assert candidate["gold_bundle_id"] == (
        "research-l0-good-turing-missing-mass-theory-20260828-v1"
    )
    assert candidate["gold_manifest_sha256"] == (
        "0c9956c380a9ce0c3af16a430a480973b65c80f1223e7800aa18c40bf02ba390"
    )
    assert candidate["gold_descriptor_hash"] == (
        "5584a47099f192c6c3d3ba21ba61795050e632ca072951ed017cb087b061141e"
    )
    assert evidence["visible_question_activation_commit"] == (
        "a07ccad23f964df8b8bb83e08f30bd90f21b02f6"
    )
    assert evidence["activation_schema_version"] == 4
    assert evidence["mechanical_reference_checks"] == "7/7"
    assert evidence["mechanical_negative_variants_rejected"] == "7/7"
    assert evidence["semantic_protocol_version"] == 10
    assert evidence["semantic_activation_attempts"] == 1
    assert evidence["semantic_calibration_total_model_calls"] == 8
    assert evidence["semantic_calibration_cases_correct"] == 6
    assert evidence["semantic_candidate_mode_negative_cases_correct"] == 1
    assert evidence["semantic_reference_claims"] == 7
    assert evidence["semantic_reference_candidate_passed"] is True
    assert evidence["semantic_calibration_model"] == (
        "claude-haiku-4-5-20251001"
    )
    assert evidence["activation_reference_tasks_passed"] == 0
    assert evidence["activation_negative_controls_rejected"] == 0
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
    assert evidence["activation_ledger_commit"] == (
        "9bd948ab74ea4da67e048c6a7384c2fe8d6b7c3c"
    )
    assert evidence["activation_push_confirmed_on_work_branch_and_main"] is True
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
    assert evidence["generated_simulation_executed"] is False
    assert evidence["runtime_status"] == "ACCEPTED"
    assert evidence["runtime_research_loop_complete"] is True
    assert evidence["runtime_mode_conformant"] is True
    assert evidence["runtime_outer_graph_iterations"] == 3
    assert evidence["runtime_product_model_turns"] == 39
    assert evidence["theory_workspace_model_turns"] == 10
    assert evidence["independent_theory_preflight_model_turns"] == 6
    assert evidence["critic_workspace_model_turns"] == 23
    assert evidence["post_runtime_gold_model_calls"] == 1
    assert evidence["hidden_theory_mechanical_checks"] == "7/7"
    assert evidence["hidden_theory_semantic_claims"] == "5/7"
    assert evidence["hidden_theory_semantic_candidate_status"] == "FAIL"
    assert evidence["hidden_theory_combined_passed"] is False
    assert evidence["automated_full_task_passed"] is False
    assert evidence["full_task_passed"] is False
    assert evidence["trusted_capability_credit"] is False
    assert evidence["model_draw_resampling_blocked"] is True
    assert evidence["post_run_shared_mechanism_change"].startswith("None.")
    assert "1031/1031" in evidence["closeout_verification"]

    visible_path = Path(candidate["visible_questions_path"])
    assert hashlib.sha256(visible_path.read_bytes()).hexdigest() == (
        evidence["visible_questions_sha256"]
    )
    question = json.loads(visible_path.read_text(encoding="utf-8"))["questions"][0]
    assert question["id"] == TASK_ID
    assert question["task_intent"] == candidate["task_intent"]
    assert question["task_intent"]["theory"] == "required"
    assert question["task_intent"]["scientific_code"] == "not_applicable"
    assert question["task_intent"]["empirical"] == "not_applicable"
    assert question["task_intent"]["formal"] == "not_applicable"
    assert question["source"]["doi"] == "10.1093/biomet/40.3-4.237"
    assert "countably infinite alphabet" in question["description"]
    assert "n-1, n, and n+1" in question["description"]

    runtime_visible = json.dumps(
        {"candidate": candidate, "question": question}, sort_keys=True
    )
    for hidden_name in (
        "gold_manifest.json",
        "hidden_theory_harness.py",
        "semantic_reference.md",
        "semantic_rubric.json",
        "candidate_mode_near_miss.md",
    ):
        assert hidden_name not in runtime_visible

    readiness = ladder["current_readiness"]
    assert readiness["scored_tasks_total"] == 93
    assert readiness["unconsumed_scored_tasks"] == 0
    assert readiness["consumed_scored_tasks"] == 93
    assert readiness["fully_gold_configured_tasks"] == 93
    assert readiness["fully_gold_passed_tasks"] == 7
