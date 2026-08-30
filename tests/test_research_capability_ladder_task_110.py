from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path

from ai_statistician.fingerprint import stable_hash
from ai_statistician.research_gold_evaluation import (
    _visible_question_hash_payload,
    validate_research_gold_benchmark_manifest,
)
from ai_statistician.research_schema import load_open_research_questions


LADDER_PATH = Path("benchmarks/research_capability_ladder_20260814.json")
VISIBLE_PATH = Path(
    "benchmarks/research_l0_dirichlet_multinomial_predictive_questions_20260830.json"
)
LEDGER_PATH = Path(
    "docs/evaluation_activations/task110_dirichlet_multinomial_predictive_preactivation.json"
)
OPERATOR_AUDIT = Path(
    "docs/operator_audits/dirichlet_multinomial_predictive_l0_v1.md"
)
GOLD_MANIFEST = Path(
    "/Users/yukangzengcmac/.codex/evaluator_authority/AI-Statistician/"
    "research-l0-dirichlet-multinomial-predictive-20260830-v1/gold_manifest.json"
)
RUN_PATH = Path(
    "runs/main_worker_research_l0_dirichlet_multinomial_predictive_20260830_v1_"
    "codex_workspace_exact_haiku"
)
RUNTIME_RESULT = RUN_PATH / (
    "dirichlet_multinomial_posterior_predictive_known_result_runtime_result.json"
)
GOLD_EVALUATION = RUN_PATH / "research_capability_gold_evaluation.json"
PROGRESS = RUN_PATH / "runtime_progress.jsonl"
TASK_ID = "dirichlet_multinomial_posterior_predictive_known_result"
SHARED_MECHANISM_COMMIT = "9597b52d44a80e36ed541d0dc49035c83c3cbbb2"
LATEST_SHARED_MECHANISM_COMMIT = "2124ee6e598a58885e11d9458e10316815b69952"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_dirichlet_multinomial_task110_is_consumed_once_and_failed_closed() -> None:
    ladder = json.loads(LADDER_PATH.read_text(encoding="utf-8"))
    candidates = [
        row for row in ladder["initial_candidate_queue"] if row["id"] == TASK_ID
    ]
    assert len(candidates) == 1
    candidate = candidates[0]
    evidence = candidate["activation_evidence"]
    visible_payload = json.loads(VISIBLE_PATH.read_text(encoding="utf-8"))
    visible_question = visible_payload["questions"][0]
    loaded_question = load_open_research_questions(VISIBLE_PATH)[0]
    descriptor = validate_research_gold_benchmark_manifest(GOLD_MANIFEST)

    readiness = ladder["current_readiness"]
    assert len(ladder["initial_candidate_queue"]) == 111
    assert ladder["initial_candidate_queue"][-2]["id"] == TASK_ID
    assert readiness["scored_tasks_total"] == 111
    assert readiness["unconsumed_scored_tasks"] == 0
    assert readiness["consumed_scored_tasks"] == 111
    assert readiness["fully_gold_configured_tasks"] == 111
    assert readiness["fully_gold_passed_tasks"] == 7
    assert readiness["operator_invalid_tasks"] == 18
    assert readiness["latest_shared_mechanism_head"] == LATEST_SHARED_MECHANISM_COMMIT

    assert candidate["level"] == "L0"
    assert candidate["family"] == (
        "bayesian_categorical_dirichlet_multinomial_prediction"
    )
    assert candidate["status"] == "consumed_scored"
    assert candidate["activation_status"] == (
        "fresh_live_v1_consumed_exact_haiku_runtime_accepted_"
        "hidden_full_task_failed"
    )
    assert loaded_question.id == TASK_ID
    assert loaded_question.task_intent == candidate["task_intent"]
    assert candidate["task_intent"] == {
        "source_replication": "not_applicable",
        "theory": "required",
        "scientific_code": "required",
        "empirical": "required",
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
    assert evidence["mechanical_algorithm_authority_checks_correct"] == "10/10"
    assert evidence["mechanical_algorithm_valid_cases_correct"] == "24/24"
    assert evidence["mechanical_algorithm_invalid_cases_correct"] == "34/34"
    assert evidence["mechanical_empirical_authority_checks_correct"] == "13/13"
    assert evidence["mechanical_negative_evaluator_controls_rejected"] == "5/5"
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

    progress = [
        json.loads(line) for line in PROGRESS.read_text(encoding="utf-8").splitlines()
    ]
    model_turns = [
        row for row in progress
        if row["event_type"] == "substage_start"
        and row["substage"] == "client_tool_model_turn"
    ]
    tool_finishes = [
        row for row in progress
        if row["event_type"] == "substage_finish"
        and row["substage"] == "client_tool_execution"
    ]
    workspace_counts = Counter(
        row["metadata"]["workspace_subsystem"] for row in model_turns
    )
    assert len(model_turns) == evidence["runtime_client_tool_model_turns"] == 77
    assert len(tool_finishes) == evidence["runtime_client_tool_executions"] == 83
    assert sum(
        row["metadata"]["tool_result_is_error"] is True for row in tool_finishes
    ) == evidence["runtime_client_tool_errors"] == 4
    assert workspace_counts == {
        "TheoryDeveloper": 12,
        "ArchitectMetricSemanticReviewer": 27,
        "AlgorithmEngineer": 10,
        "GeneratedCodeSemanticReviewer": 7,
        "SimulationEvaluator": 14,
        "CriticEvaluator": 7,
    }
    assert evidence["runtime_product_model_calls"] == 78
    assert evidence["runtime_direct_model_calls"] == 1
    assert sum(evidence["runtime_model_calls_by_workspace"].values()) == 78

    runtime = json.loads(RUNTIME_RESULT.read_text(encoding="utf-8"))
    assert runtime["status"] == evidence["runtime_status"] == "ACCEPTED"
    assert runtime["runtime_steps_executed"] == evidence["runtime_steps"] == 14
    assert runtime["outer_graph_iterations_consumed"] == 13
    assert runtime["same_owner_workspace_continuations_consumed"] == 1
    assert runtime["pending_task"] is None
    assert evidence["runtime_terminal_subsystem"] == "CriticEvaluator"
    assert evidence["runtime_mode_conformant"] is True
    assert evidence["runtime_research_eval_complete"] is True
    assert evidence["runtime_serious_theory_completed"] is True
    assert evidence["runtime_theory_preexecution_review_accepted"] is True
    assert evidence["runtime_critic_research_acceptance"] is True

    assert evidence["theory_packets_committed"] == 1
    assert evidence["independent_theory_preflight_invocations"] == 1
    assert evidence["independent_theory_report_count"] == 1
    assert evidence["independent_theory_preflight_acceptances"] == 1
    assert evidence["theory_document_lines"] == 401
    assert evidence["theory_document_bytes"] == 17_061
    assert _sha256(Path(evidence["theory_document_path"])) == evidence[
        "theory_document_sha256"
    ]
    assert evidence["referee_report_sha256"] == [
        "ad637032f6b7f7f7ca8082e2d19b4f309ec169e4cde950b8d00d3eea73c5669b"
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
    assert len(task["hidden_theory_check_results"]) == 7
    assert task["hidden_theory_semantic_candidate_status"] == "PASS"
    assert task["hidden_theory_semantic_claim_count"] == 8
    assert all(
        row["status"] == "SATISFIED"
        for row in task["hidden_theory_semantic_claim_assessments"]
    )
    assert task["hidden_theory_combined_passed"] is True
    assert sum(row["passed"] for row in task["hidden_check_results"]) == 8
    assert len(task["hidden_check_results"]) == 10
    assert task["hidden_harness_estimator_invocation_count"] == 60
    assert sum(
        row["passed"] for row in task["hidden_empirical_check_results"]
    ) == 13
    assert task["hidden_empirical_estimator_invocation_count"] == 3
    assert task["runtime_research_eval_complete"] is True
    assert task["dimension_status"]["theory"]["status"] == "passed"
    assert task["dimension_status"]["scientific_code"]["status"] == "failed"
    assert task["dimension_status"]["empirical"]["status"] == "passed"
    assert task["task_passed"] is False
    assert gold["runtime_feedback_generated"] is False

    assert evidence["operator_disposition"] == "FAILED"
    assert evidence["operator_invalid"] is False
    assert evidence["post_run_shared_mechanism_commit"] == SHARED_MECHANISM_COMMIT
    assert evidence["automated_full_task_passed"] is False
    assert evidence["full_task_passed"] is False
    assert evidence["trusted_capability_credit"] is False
    assert evidence["ladder_score_after_consumption"] == "7/110"
    assert evidence["model_draw_resampling_blocked"] is True
    assert evidence["formalization_requirement"] == "not_applicable"
    assert evidence["formalizer_executed"] is False
    assert evidence["generated_algorithm_executed"] is True
    assert evidence["generated_simulation_executed"] is True
    assert evidence["critic_executed"] is True
    assert evidence["sonnet_product_calls"] == 0
    assert evidence["opus_product_calls"] == 0
    assert OPERATOR_AUDIT.is_file()

    runtime_visible = json.dumps(
        {"candidate": candidate, "question": visible_question}, sort_keys=True
    )
    for hidden_name in (
        "semantic_reference.md",
        "candidate_mode_near_miss.md",
        "hidden_algorithm_harness.py",
        "hidden_empirical_harness.py",
    ):
        assert hidden_name not in runtime_visible
