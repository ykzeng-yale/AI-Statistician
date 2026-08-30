from __future__ import annotations

import hashlib
import json
from pathlib import Path

from ai_statistician.fingerprint import stable_hash
from ai_statistician.research_gold_evaluation import (
    _visible_question_hash_payload,
    validate_research_gold_benchmark_manifest,
)
from ai_statistician.research_schema import load_open_research_questions


LADDER_PATH = Path("benchmarks/research_capability_ladder_20260814.json")
VISIBLE_PATH = Path("benchmarks/research_l3_stein_sure_questions_20260829.json")
LEDGER_PATH = Path(
    "docs/evaluation_activations/task107_stein_sure_preactivation.json"
)
GOLD_MANIFEST = Path(
    "/Users/yukangzengcmac/.codex/evaluator_authority/AI-Statistician/"
    "research-l3-stein-sure-theory-20260829-v1/gold_manifest.json"
)
TASK_ID = "gaussian_stein_sure_james_stein_known_theory_rederivation"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_stein_sure_task107_is_consumed_once_and_failed_closed() -> None:
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
    assert candidate["family"] == "gaussian_stein_unbiased_risk_estimation"
    assert candidate["status"] == "consumed_scored"
    assert candidate["activation_status"] == (
        "fresh_live_v1_consumed_exact_haiku_theory_preflight_blocked_gold_failed"
    )
    assert loaded_question.id == TASK_ID
    assert loaded_question.task_intent == candidate["task_intent"]
    assert candidate["task_intent"] == {
        "source_replication": "not_applicable",
        "theory": "required",
        "scientific_code": "not_applicable",
        "empirical": "not_applicable",
        "formal": "not_applicable",
        "novelty": "not_applicable",
        "unresolved_gaps": "required",
    }

    assert _sha256(VISIBLE_PATH) == evidence["visible_questions_sha256"]
    assert stable_hash(visible_payload) == evidence["visible_question_full_hash"]
    assert stable_hash(_visible_question_hash_payload(visible_question)) == evidence[
        "runtime_visible_question_hash"
    ]
    assert _sha256(LEDGER_PATH) == evidence["public_preactivation_ledger_sha256"]
    assert _sha256(GOLD_MANIFEST) == candidate["gold_manifest_sha256"]
    assert descriptor["benchmark_manifest_hash"] == candidate[
        "gold_descriptor_hash"
    ]
    assert descriptor["active_task_ids"] == [TASK_ID]

    assert evidence["activation_schema_version"] == 4
    assert evidence["mechanical_authority_checks_correct"] == "7/7"
    assert evidence["mechanical_negative_variants_rejected"] == "7/7"
    assert evidence["semantic_protocol_version"] == 11
    assert evidence["semantic_candidate_adjudication_strategy"] == (
        "integrated_plus_adversarial"
    )
    assert evidence["semantic_calibration_cases_correct"] == "6/6"
    assert evidence["semantic_candidate_mode_negative_cases_correct"] == "1/1"
    assert evidence["semantic_reference_claims"] == 8
    assert evidence["semantic_successful_qualification_model_calls"] == 16
    assert evidence["preactivation_product_model_calls"] == 0
    assert evidence["preactivation_evaluator_model_calls"] == 16
    assert evidence["gold_frozen_before_first_runtime_model_call"] is True
    assert evidence["activation_push_confirmed_on_work_branch_and_main"] is True

    assert evidence["first_runtime_model_call_occurred"] is True
    assert evidence["fresh_live_runs"] == 1
    assert evidence["runtime_invocations"] == 1
    assert evidence["single_fresh_draw_only"] is True
    assert evidence["runtime_model"] == "claude-haiku-4-5-20251001"
    assert evidence["runtime_product_model_calls"] == 134
    assert evidence["runtime_client_tool_model_turns"] == 134
    assert evidence["runtime_direct_model_calls"] == 0
    assert evidence["runtime_client_tool_executions"] == 134
    assert evidence["runtime_client_tool_errors"] == 14
    assert evidence["runtime_model_calls_by_workspace"] == {
        "TheoryDeveloper": 55,
        "ArchitectMetricSemanticReviewer": 79,
    }

    assert evidence["runtime_status"] == "BLOCKED"
    assert evidence["runtime_terminal_subsystem"] == "TheoryDeveloper"
    assert evidence["runtime_terminal_classification"] == (
        "theory_developer_packet_validation_failed"
    )
    assert evidence["runtime_terminal_observation"] == (
        "repeated client-tool turns made no new progress"
    )
    assert evidence["runtime_steps"] == 8
    assert evidence["runtime_outer_graph_iterations"] == 7
    assert evidence["runtime_same_owner_workspace_continuations"] == 1
    assert evidence["runtime_recovery_checkpoint_available"] is True
    assert evidence["runtime_mode_conformant"] is True
    assert evidence["runtime_research_eval_complete"] is False
    assert evidence["theory_packets_committed"] == 3
    assert evidence["independent_theory_report_count"] == 3
    assert evidence["independent_theory_preflight_acceptances"] == 0

    assert evidence["theory_document_lines"] == 302
    assert evidence["theory_document_sha256"] == (
        "d67c664a7f9f29bd0e2ed5ec9ccb4257bca8728c5212eec5e05449388a34d5ee"
    )
    assert evidence["referee_report_sha256"] == [
        "b8b03ecd4eec74579dbf1d6993ae8e000216c1b149d8be27ac67ab1476177ce5",
        "f6ee2ab045fcbc34d3b4763ca9d5be1ef660092fa7c341740bacf501fd2ad69d",
        "bc47c5ce2c7e587a306ab353c916ca632a7aef7c639285f3d72cd3b7dd9a966a",
    ]
    assert evidence["runtime_manifest_sha256"] == (
        "a5bef637e8c12fd27089f8310bec1e8fc42599ddc337a6fefa1203001677bbf0"
    )
    assert evidence["runtime_result_sha256"] == (
        "567aa7e7eb4fb43c8a0ae336dec43e6e5a984cc4c60adc6d6d1c1a41ccd2da0f"
    )
    assert evidence["hidden_assessment_record_sha256"] == (
        "38593e9d86cfbd30bf59306fc4607fa09443dd6c2f3e8b6398ef8398ea60b2a4"
    )
    assert evidence["sole_hidden_assessment_invocations"] == 1
    assert evidence["hidden_gold_tasks_evaluated"] == 0
    assert evidence["hidden_evaluator_model_calls"] == 0
    assert evidence["hidden_theory_execution_attempted"] is False
    assert evidence["runtime_feedback_generated"] is False

    assert evidence["operator_disposition"] == "FAILED"
    assert evidence["operator_invalid"] is False
    assert evidence["post_run_shared_mechanism_commit"] == (
        "a27af9794f4dbccb089a8063c3a42edb0d509084"
    )
    assert evidence["automated_full_task_passed"] is False
    assert evidence["full_task_passed"] is False
    assert evidence["trusted_capability_credit"] is False
    assert evidence["ladder_score_after_consumption"] == "7/107"
    assert evidence["model_draw_resampling_blocked"] is True
    assert evidence["formalization_requirement"] == "not_applicable"
    assert evidence["formalizer_executed"] is False
    assert evidence["sonnet_product_calls"] == 0
    assert evidence["opus_product_calls"] == 0

    runtime_visible = json.dumps(
        {"candidate": candidate, "question": visible_question}, sort_keys=True
    )
    for hidden_name in (
        "semantic_reference.md",
        "candidate_mode_near_miss.md",
        "hidden_theory_harness.py",
    ):
        assert hidden_name not in runtime_visible
