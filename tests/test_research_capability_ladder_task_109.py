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
    "benchmarks/research_l0_known_propensity_ipw_missing_mean_questions_20260830.json"
)
LEDGER_PATH = Path(
    "docs/evaluation_activations/task109_known_propensity_ipw_preactivation.json"
)
OPERATOR_AUDIT = Path(
    "docs/operator_audits/known_propensity_ipw_missing_mean_l0_v1.md"
)
GOLD_MANIFEST = Path(
    "/Users/yukangzengcmac/.codex/evaluator_authority/AI-Statistician/"
    "research-l0-known-propensity-ipw-missing-mean-20260830-v1/"
    "gold_manifest.json"
)
RUN_PATH = Path(
    "runs/main_worker_research_l0_known_propensity_ipw_missing_mean_20260830_v1_"
    "codex_workspace_exact_haiku"
)
RUNTIME_RESULT = RUN_PATH / (
    "known_propensity_ipw_missing_mean_known_result_runtime_result.json"
)
GOLD_EVALUATION = RUN_PATH / "research_capability_gold_evaluation.json"
TASK_ID = "known_propensity_ipw_missing_mean_known_result"
SHARED_MECHANISM_COMMIT = "94f18d2f949312f67b3d1c77cbbb6bbf237172d3"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_known_propensity_ipw_task109_is_consumed_once_and_failed_closed() -> None:
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
    assert len(ladder["initial_candidate_queue"]) == 109
    assert ladder["initial_candidate_queue"][-1]["id"] == TASK_ID
    assert readiness["scored_tasks_total"] == 109
    assert readiness["unconsumed_scored_tasks"] == 0
    assert readiness["consumed_scored_tasks"] == 109
    assert readiness["fully_gold_configured_tasks"] == 109
    assert readiness["fully_gold_passed_tasks"] == 7
    assert readiness["operator_invalid_tasks"] == 18
    assert readiness["latest_shared_mechanism_head"] == SHARED_MECHANISM_COMMIT

    assert candidate["level"] == "L0"
    assert candidate["family"] == "missing_at_random_known_propensity_ipw"
    assert candidate["status"] == "consumed_scored"
    assert candidate["activation_status"] == (
        "fresh_live_v1_consumed_exact_haiku_runtime_blocked_hidden_full_task_failed"
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
    assert evidence["mechanical_algorithm_authority_checks_correct"] == "9/9"
    assert evidence["mechanical_algorithm_valid_cases_correct"] == "21/21"
    assert evidence["mechanical_algorithm_invalid_cases_correct"] == "31/31"
    assert evidence["mechanical_empirical_authority_checks_correct"] == "12/12"
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

    assert evidence["first_runtime_model_call_occurred"] is True
    assert evidence["fresh_live_runs"] == 1
    assert evidence["runtime_invocations"] == 1
    assert evidence["single_fresh_draw_only"] is True
    assert evidence["runtime_model"] == "claude-haiku-4-5-20251001"
    assert evidence["runtime_product_model_calls"] == 78
    assert evidence["runtime_client_tool_model_turns"] == 77
    assert evidence["runtime_direct_model_calls"] == 1
    assert evidence["runtime_client_tool_executions"] == 80
    assert evidence["runtime_client_tool_errors"] == 3
    assert evidence["runtime_model_calls_by_workspace"] == {
        "ArchitectCoordinator": 1,
        "TheoryDeveloper": 22,
        "ArchitectTheoryExecutionPreflight": 15,
        "AlgorithmEngineer": 11,
        "GeneratedCodeSemanticReviewer": 4,
        "SimulationEngineer": 16,
        "CriticEvaluator": 9,
    }

    runtime = json.loads(RUNTIME_RESULT.read_text(encoding="utf-8"))
    assert runtime["status"] == evidence["runtime_status"] == "BLOCKED"
    assert runtime["runtime_steps_executed"] == evidence["runtime_steps"] == 11
    assert runtime["outer_graph_iterations_consumed"] == 11
    assert runtime["same_owner_workspace_continuations_consumed"] == 0
    assert runtime["pending_task"] is None
    assert evidence["runtime_terminal_subsystem"] == "CriticEvaluator"
    assert evidence["runtime_terminal_classification"] == (
        "required_research_evidence_missing"
    )
    assert evidence["runtime_mode_conformant"] is True
    assert evidence["runtime_research_eval_complete"] is False
    assert evidence["runtime_serious_theory_completed"] is True
    assert evidence["runtime_theory_preexecution_review_accepted"] is True
    assert evidence["runtime_critic_research_acceptance"] is False

    assert evidence["theory_packets_committed"] == 1
    assert evidence["independent_theory_preflight_invocations"] == 1
    assert evidence["independent_theory_report_count"] == 1
    assert evidence["independent_theory_preflight_acceptances"] == 1
    assert evidence["theory_document_lines"] == 299
    assert evidence["theory_document_bytes"] == 11_567
    assert evidence["theory_document_sha256"] == (
        "f7793c93755eded2d763ca5e92dcc8a2dcb12a8c41a86860cc8540e965373a51"
    )
    assert evidence["referee_report_sha256"] == [
        "95e0490e0a4bdffd21fb2aca40600299c80587a1af7d6153e98c9bc0c37dc09c"
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
    assert sum(row["passed"] for row in task["hidden_check_results"]) == 7
    assert len(task["hidden_check_results"]) == 9
    assert sum(row["passed"] for row in task["hidden_empirical_check_results"]) == 12
    assert task["hidden_empirical_estimator_invocation_count"] == 6000
    assert task["unresolved_gap_disclosure_present"] is False
    assert task["runtime_research_eval_complete"] is False
    assert task["task_passed"] is False
    assert gold["runtime_feedback_generated"] is False

    assert evidence["operator_disposition"] == "FAILED"
    assert evidence["operator_invalid"] is False
    assert evidence["post_run_shared_mechanism_commit"] == SHARED_MECHANISM_COMMIT
    assert evidence["automated_full_task_passed"] is False
    assert evidence["full_task_passed"] is False
    assert evidence["trusted_capability_credit"] is False
    assert evidence["ladder_score_after_consumption"] == "7/109"
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
