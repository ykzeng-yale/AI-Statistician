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
VISIBLE_PATH = Path(
    "benchmarks/research_l3_bahadur_quantile_questions_20260829.json"
)
LEDGER_PATH = Path(
    "docs/evaluation_activations/task108_bahadur_quantile_preactivation.json"
)
GOLD_MANIFEST = Path(
    "/Users/yukangzengcmac/.codex/evaluator_authority/AI-Statistician/"
    "research-l3-bahadur-quantile-theory-20260829-v1/gold_manifest.json"
)
RUN_PATH = Path(
    "runs/main_worker_research_l3_bahadur_quantile_theory_20260829_v1_"
    "codex_workspace_exact_haiku"
)
RUNTIME_RESULT = RUN_PATH / (
    "iid_sample_quantile_bahadur_known_theory_rederivation_runtime_result.json"
)
GOLD_EVALUATION = RUN_PATH / "research_capability_gold_evaluation.json"
TASK_ID = "iid_sample_quantile_bahadur_known_theory_rederivation"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_bahadur_quantile_task108_is_consumed_once_and_failed_closed() -> None:
    ladder = json.loads(LADDER_PATH.read_text(encoding="utf-8"))
    candidate = next(
        row for row in ladder["initial_candidate_queue"] if row["id"] == TASK_ID
    )
    evidence = candidate["activation_evidence"]
    visible_payload = json.loads(VISIBLE_PATH.read_text(encoding="utf-8"))
    visible_question = visible_payload["questions"][0]
    loaded_question = load_open_research_questions(VISIBLE_PATH)[0]
    descriptor = validate_research_gold_benchmark_manifest(GOLD_MANIFEST)

    assert ladder["current_readiness"]["scored_tasks_total"] == 108
    assert ladder["current_readiness"]["consumed_scored_tasks"] == 108
    assert ladder["current_readiness"]["fully_gold_passed_tasks"] == 7
    assert ladder["current_readiness"]["latest_shared_mechanism_head"] == (
        "8e3a58c76c58b42685d6a47dea96199af5df8997"
    )
    assert candidate["level"] == "L3"
    assert candidate["family"] == "iid_quantile_asymptotic_linearity"
    assert candidate["status"] == "consumed_scored"
    assert candidate["activation_status"] == (
        "fresh_live_v1_consumed_exact_haiku_theory_accepted_critic_blocked_"
        "gold_failed"
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

    assert evidence["startup_preflight_failures_before_product_call"] == 1
    assert evidence["startup_preflight_product_model_calls"] == 0
    assert evidence["startup_preflight_artifacts_created"] == 0
    assert evidence["first_runtime_model_call_occurred"] is True
    assert evidence["fresh_live_runs"] == 1
    assert evidence["runtime_invocations"] == 1
    assert evidence["single_fresh_draw_only"] is True
    assert evidence["runtime_model"] == "claude-haiku-4-5-20251001"
    assert evidence["runtime_product_model_calls"] == 70
    assert evidence["runtime_client_tool_model_turns"] == 70
    assert evidence["runtime_direct_model_calls"] == 0
    assert evidence["runtime_client_tool_executions"] == 78
    assert evidence["runtime_client_tool_errors"] == 10
    assert evidence["runtime_model_calls_by_workspace"] == {
        "TheoryDeveloper": 22,
        "ArchitectMetricSemanticReviewer": 27,
        "CriticEvaluator": 21,
    }

    runtime = json.loads(RUNTIME_RESULT.read_text(encoding="utf-8"))
    assert runtime["status"] == evidence["runtime_status"] == "BLOCKED"
    assert runtime["runtime_steps_executed"] == evidence["runtime_steps"] == 4
    assert runtime["outer_graph_iterations_consumed"] == 3
    assert runtime["same_owner_workspace_continuations_consumed"] == 1
    assert evidence["runtime_terminal_subsystem"] == "CriticEvaluator"
    assert evidence["runtime_terminal_classification"] == (
        "critic_packet_validation_failed"
    )
    assert evidence["runtime_terminal_observation"] == (
        "repeated client-tool turns made no new progress"
    )
    assert evidence["runtime_mode_conformant"] is True
    assert evidence["runtime_research_eval_complete"] is False
    assert evidence["runtime_serious_theory_completed"] is True
    assert evidence["runtime_theory_preexecution_review_accepted"] is True
    assert evidence["runtime_critic_research_acceptance"] is False

    assert evidence["theory_packets_committed"] == 1
    assert evidence["independent_theory_report_count"] == 1
    assert evidence["independent_theory_preflight_acceptances"] == 1
    assert evidence["theory_document_lines"] == 460
    assert evidence["theory_document_bytes"] == 19_960
    assert evidence["theory_document_sha256"] == (
        "b27352e66f90915ca071a4d0a3b45070d279ff598a2475f1646818b14f37f248"
    )
    assert evidence["referee_report_sha256"] == [
        "a077a98e5090c83a51f8749711c72668e91c73f9f282de3dc2eeb42f1f259b5b"
    ]
    assert _sha256(RUNTIME_RESULT) == evidence["runtime_result_sha256"]
    assert _sha256(RUN_PATH / "research_agent_runtime_manifest.json") == evidence[
        "runtime_manifest_sha256"
    ]
    assert _sha256(GOLD_EVALUATION) == evidence[
        "hidden_assessment_record_sha256"
    ]

    gold = json.loads(GOLD_EVALUATION.read_text(encoding="utf-8"))
    task = gold["tasks"][0]
    assert gold["n_tasks_evaluated"] == 1
    assert gold["n_tasks_passed"] == 0
    assert evidence["sole_hidden_assessment_invocations"] == 1
    assert evidence["hidden_evaluator_model_calls"] == 2
    assert task["hidden_theory_execution_attempted"] is True
    assert task["hidden_theory_checks_passed"] is True
    assert task["hidden_theory_semantic_candidate_status"] == "FAIL"
    assert task["hidden_theory_semantic_claim_count"] == 8
    assert sum(
        row["status"] == "SATISFIED"
        for row in task["hidden_theory_semantic_claim_assessments"]
    ) == 5
    assert task["hidden_theory_combined_passed"] is False
    assert task["task_passed"] is False
    assert gold["runtime_feedback_generated"] is False

    assert evidence["operator_disposition"] == "FAILED"
    assert evidence["operator_invalid"] is False
    assert evidence["post_run_shared_mechanism_commit"] == (
        "8e3a58c76c58b42685d6a47dea96199af5df8997"
    )
    assert evidence["automated_full_task_passed"] is False
    assert evidence["full_task_passed"] is False
    assert evidence["trusted_capability_credit"] is False
    assert evidence["ladder_score_after_consumption"] == "7/108"
    assert evidence["model_draw_resampling_blocked"] is True
    assert evidence["formalization_requirement"] == "not_applicable"
    assert evidence["formalizer_executed"] is False
    assert evidence["critic_executed"] is True
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
