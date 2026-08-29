from __future__ import annotations

import hashlib
import json
from pathlib import Path


LADDER_PATH = Path("benchmarks/research_capability_ladder_20260814.json")
TASK_ID = "karlin_rubin_mlr_ump_known_result"


def test_karlin_rubin_l0_theory_task_is_consumed_and_immutable() -> None:
    ladder = json.loads(LADDER_PATH.read_text(encoding="utf-8"))
    candidate = next(
        row for row in ladder["initial_candidate_queue"] if row["id"] == TASK_ID
    )
    evidence = candidate["activation_evidence"]

    assert candidate["level"] == "L0"
    assert candidate["family"] == "monotone_likelihood_ratio_composite_testing"
    assert candidate["status"] == "consumed_scored"
    assert candidate["activation_status"] == (
        "fresh_live_v1_consumed_runtime_accepted_hidden_theory_semantic_failed"
    )
    assert candidate["gold_bundle_id"] == (
        "research-l0-karlin-rubin-mlr-ump-20260828-v1"
    )
    assert candidate["gold_manifest_sha256"] == (
        "31cf5407a2ad19be1341d82bd6d041d4e6239861940db807e743b3f4ca05631a"
    )
    assert candidate["gold_descriptor_hash"] == (
        "5ad8e07d3acb5b963a5aed6fee0158b31d39825eaf314a94d3cd7abbb5044e4e"
    )

    assert evidence["activation_schema_version"] == 4
    assert evidence["mechanical_reference_checks"] == "7/7"
    assert evidence["mechanical_negative_variants_rejected"] == "7/7"
    assert evidence["semantic_protocol_version"] == 10
    assert evidence["semantic_activation_attempts"] == 2
    assert evidence["semantic_calibration_total_model_calls"] == 12
    assert evidence["semantic_final_calibration_cases_correct"] == 4
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
    assert evidence["activation_semantic_qualification_model_calls"] == 6
    assert evidence["activation_semantic_qualification_reused"] is True
    assert evidence["hidden_gold_manifest_validated"] is True
    assert evidence["gold_frozen_before_first_runtime_model_call"] is True
    assert evidence["activation_ledger_commit"] == (
        "bbd3bafdcafa8c2b29eea73094b4f89fcd96edb3"
    )
    assert evidence["activation_push_confirmed_on_work_branch_and_main"] is True
    assert evidence["preactivation_product_model_calls"] == 0

    assert evidence["first_runtime_model_call_occurred"] is True
    assert evidence["fresh_live_runs"] == 1
    assert evidence["runtime_invocations"] == 1
    assert evidence["runtime_head"] == (
        "96ece9c0005b2fdc860c8929e54d8504df8a0acf"
    )
    assert evidence["runtime_status"] == "ACCEPTED"
    assert evidence["runtime_research_loop_complete"] == "1/1"
    assert evidence["runtime_mode_conformant"] == "1/1"
    assert evidence["runtime_outer_graph_iterations"] == 3
    assert evidence["runtime_model_calls"] == 57
    assert evidence["architect_plan_model_calls"] == 0
    assert evidence["theory_workspace_model_calls"] == 18
    assert evidence["independent_theory_preflight_model_calls"] == 13
    assert evidence["critic_workspace_model_calls"] == 26
    assert evidence["runtime_model"] == "claude-haiku-4-5-20251001"
    assert evidence["sonnet_product_calls"] == 0
    assert evidence["opus_product_calls"] == 0

    assert evidence["hidden_theory_mechanical_checks"] == "7/7"
    assert evidence["hidden_theory_semantic_claims"] == "7/8"
    assert evidence["hidden_theory_semantic_candidate_status"] == "FAIL"
    assert evidence["automated_full_task_passed"] is False
    assert evidence["full_task_passed"] is False
    assert evidence["trusted_capability_credit"] is False
    assert evidence["ladder_score_after_consumption"] == "4/84"
    assert evidence["model_draw_resampling_blocked"] is True
    assert evidence["formalization_requirement"] == "not_applicable"
    assert evidence["formalizer_executed"] is False
    assert evidence["operator_audit_path"] == (
        "docs/operator_audits/karlin_rubin_mlr_ump_theory_l0_v1.md"
    )
    assert evidence["runtime_manifest_sha256"] == (
        "5570b65e22c83dacdd7ab2b7f1124fe10bdcd3455c8b21fc2bc18a3af55ce393"
    )
    assert evidence["gold_evaluation_sha256"] == (
        "67c9db8f43a0ca489f003fd601209e1a9f1f8b34bad87b80ba266370c245fb19"
    )

    visible_path = Path(candidate["visible_questions_path"])
    assert hashlib.sha256(visible_path.read_bytes()).hexdigest() == (
        evidence["visible_questions_sha256"]
    )
    question = json.loads(visible_path.read_text(encoding="utf-8"))["questions"][0]
    assert question["id"] == TASK_ID
    assert question["task_intent"] == candidate["task_intent"]
    assert question["task_intent"]["theory"] == "required"
    assert question["task_intent"]["formal"] == "not_applicable"
    assert question["source"]["doi"] == "10.1214/aoms/1177728259"

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
    assert readiness["scored_tasks_total"] == 90
    assert readiness["unconsumed_scored_tasks"] == 0
    assert readiness["consumed_scored_tasks"] == 90
    assert readiness["fully_gold_configured_tasks"] == 90
    assert readiness["fully_gold_passed_tasks"] == 5
