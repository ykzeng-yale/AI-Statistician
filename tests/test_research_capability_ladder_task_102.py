from __future__ import annotations

import hashlib
import json
from pathlib import Path

from ai_statistician.estimator_interface_contract import (
    frozen_estimator_execution_contract_id,
)
from ai_statistician.fingerprint import stable_hash
from ai_statistician.research_gold_evaluation import (
    _visible_question_hash_payload,
    validate_research_gold_benchmark_manifest,
)
from ai_statistician.research_schema import load_open_research_questions
from ai_statistician.research_source_library import load_research_source_snapshot


LADDER_PATH = Path("benchmarks/research_capability_ladder_20260814.json")
VISIBLE_PATH = Path(
    "benchmarks/research_l2_dame_flame_nonadaptive_questions_20260829.json"
)
SOURCE_MANIFEST = Path(
    "benchmarks/research_sources/dame_flame_20260829/source_manifest.json"
)
GOLD_MANIFEST = Path(
    "/Users/yukangzengcmac/.codex/evaluator_authority/AI-Statistician/"
    "research-l2-dame-flame-nonadaptive-20260829-v1/gold_manifest.json"
)
TASK_ID = "dame_flame_nonadaptive_matching_paper_to_code"


def test_dame_flame_task102_is_consumed_after_its_only_product_draw() -> None:
    ladder = json.loads(LADDER_PATH.read_text(encoding="utf-8"))
    candidate = next(
        row for row in ladder["initial_candidate_queue"] if row["id"] == TASK_ID
    )
    evidence = candidate["activation_evidence"]
    visible_payload = json.loads(VISIBLE_PATH.read_text(encoding="utf-8"))
    visible_question = visible_payload["questions"][0]
    loaded_question = load_open_research_questions(VISIBLE_PATH)[0]
    source = load_research_source_snapshot(SOURCE_MANIFEST)
    descriptor = validate_research_gold_benchmark_manifest(GOLD_MANIFEST)

    assert candidate["level"] == "L2"
    assert candidate["family"] == "causal_discrete_covariate_matching"
    assert candidate["status"] == "consumed_scored"
    assert candidate["activation_status"] == (
        "fresh_live_v1_consumed_exact_haiku_runtime_blocked_postcommit_"
        "frozen_abi_authority_mismatch_gold_not_attempted"
    )
    assert loaded_question.id == TASK_ID
    assert loaded_question.task_intent == candidate["task_intent"]
    assert candidate["task_intent"] == {
        "source_replication": "not_applicable",
        "theory": "not_applicable",
        "scientific_code": "required",
        "empirical": "not_applicable",
        "formal": "not_applicable",
        "novelty": "not_applicable",
        "unresolved_gaps": "required",
    }

    assert hashlib.sha256(VISIBLE_PATH.read_bytes()).hexdigest() == evidence[
        "visible_questions_sha256"
    ]
    assert stable_hash(visible_question) == evidence["visible_question_full_hash"]
    assert stable_hash(_visible_question_hash_payload(visible_question)) == evidence[
        "runtime_visible_question_hash"
    ]
    assert frozen_estimator_execution_contract_id(
        visible_question["estimator_execution_contract"]
    ) == evidence["estimator_execution_contract_id"]

    assert source.snapshot_hash == candidate["source_snapshot_hash"]
    assert source.manifest_sha256 == candidate["source_manifest_sha256"]
    assert len(source.documents) == 2
    assert {document.source_kind for document in source.documents} == {
        "paper_method_index",
        "public_replication_data",
    }

    assert hashlib.sha256(GOLD_MANIFEST.read_bytes()).hexdigest() == candidate[
        "gold_manifest_sha256"
    ]
    assert descriptor["benchmark_manifest_hash"] == candidate[
        "gold_descriptor_hash"
    ]
    assert descriptor["active_task_ids"] == [TASK_ID]
    assert descriptor["n_full_task_gold_configured"] == 1

    assert evidence["activation_schema_version"] == 4
    assert evidence["algorithm_authority_checks_correct"] == "13/13"
    assert evidence["algorithm_reference_valid_cases"] == 6
    assert evidence["algorithm_reference_invalid_cases"] == 18
    assert evidence["algorithm_behavioral_negative_candidates_rejected"] == 3
    assert evidence["author_parity_cases_correct"] == "5/5"
    assert evidence["activation_reference_tasks_passed"] == 1
    assert evidence["activation_negative_controls_rejected"] == 3
    assert evidence["activation_semantic_model_calls"] == 0
    assert evidence["hidden_gold_manifest_validated"] is True
    assert evidence["gold_frozen_before_first_runtime_model_call"] is True
    assert evidence["preactivation_product_model_calls"] == 0
    assert evidence["preactivation_evaluator_model_calls"] == 0
    assert evidence["first_runtime_model_call_occurred"] is True
    assert evidence["fresh_live_runs"] == 1
    assert evidence["runtime_invocations"] == 1
    assert evidence["activation_push_required_before_first_runtime_model_call"] is True
    assert evidence["activation_ledger_commit"] == (
        "901b6856e09f0594e7c5c99509660aa4da3d1359"
    )
    assert evidence["activation_push_confirmed_on_work_branch_and_main"] is True
    assert evidence["single_fresh_draw_only"] is True
    assert evidence["runtime_model"] == "claude-haiku-4-5-20251001"
    assert evidence["product_code_head"] == (
        "a2ec09f3cd89418aa5826d8c8102244ed2442d17"
    )
    assert evidence["runtime_product_model_calls"] == 25
    assert evidence["runtime_client_tool_model_turns"] == 24
    assert evidence["runtime_direct_model_calls"] == 1
    assert evidence["runtime_client_tool_executions"] == 24
    assert evidence["runtime_model_calls_by_workspace"] == {
        "ArchitectCoordinator": 1,
        "AlgorithmEngineer": 22,
        "CriticEvaluator": 2,
    }
    assert evidence["runtime_status"] == "BLOCKED"
    assert evidence["runtime_terminal_classification"] == (
        "critic_scientific_inconclusive"
    )
    assert evidence["runtime_mode_conformant"] is True
    assert evidence["runtime_research_eval_complete"] is False
    assert evidence["algorithm_source_executions"] == 6
    assert evidence["algorithm_source_terminal_commit_submitted"] is True
    assert evidence["algorithm_final_developer_checks"] == "14/14"
    assert evidence["algorithm_handoff_materialized"] is False
    assert evidence["algorithm_semantic_reviewer_executed"] is False
    assert evidence["hidden_gold_tasks_evaluated"] == 0
    assert evidence["hidden_algorithm_execution_attempted"] is False
    assert evidence["runtime_feedback_generated"] is False
    assert evidence["post_run_shared_mechanism_commit"] == (
        "e3aebe8b42a2fa7785c213c043ca017f46f55267"
    )
    assert evidence["operator_disposition"] == "FAILED"
    assert Path(evidence["operator_audit"]).exists()
    assert evidence["sonnet_product_calls"] == 0
    assert evidence["opus_product_calls"] == 0
    assert evidence["formalization_requirement"] == "not_applicable"
    assert evidence["formalizer_executed"] is False
    assert evidence["model_draw_resampling_blocked"] is True
    assert evidence["automated_full_task_passed"] is False
    assert evidence["full_task_passed"] is False
    assert evidence["trusted_capability_credit"] is False
    assert evidence["ladder_score_after_consumption"] == "7/102"

    runtime_visible = json.dumps(
        {"candidate": candidate, "question": visible_question}, sort_keys=True
    )
    for hidden_name in (
        str(GOLD_MANIFEST),
        "reference_estimator.py",
        "hidden_algorithm_harness.py",
        "author_parity_record.json",
        "negative_exact_only.py",
        "negative_pure_cells.py",
        "negative_largest_weight_first.py",
    ):
        assert hidden_name not in runtime_visible

    readiness = ladder["current_readiness"]
    assert readiness["scored_tasks_total"] == 102
    assert readiness["unconsumed_scored_tasks"] == 0
    assert readiness["consumed_scored_tasks"] == 102
    assert readiness["fully_gold_configured_tasks"] == 102
    assert readiness["fully_gold_passed_tasks"] == 7
