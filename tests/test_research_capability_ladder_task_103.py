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
    "benchmarks/research_l2_lowess_local_linear_questions_20260829.json"
)
SOURCE_MANIFEST = Path(
    "benchmarks/research_sources/lowess_local_linear_20260829/source_manifest.json"
)
GOLD_MANIFEST = Path(
    "/Users/yukangzengcmac/.codex/evaluator_authority/AI-Statistician/"
    "research-l2-lowess-local-linear-20260829-v1/gold_manifest.json"
)
RUN_DIR = Path(
    "runs/main_worker_research_l2_lowess_local_linear_20260829_v1_"
    "codex_workspace_exact_haiku"
)
TASK_ID = "lowess_local_linear_nonrobust_paper_to_code"


def test_lowess_task103_is_consumed_after_its_only_product_draw() -> None:
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

    assert TASK_ID not in {
        row["id"] for row in ladder["evidence_dimensions"]
    }
    assert candidate["level"] == "L2"
    assert candidate["family"] == "nonparametric_local_linear_smoothing"
    assert candidate["status"] == "consumed_scored"
    assert candidate["activation_status"] == (
        "fresh_live_v1_consumed_exact_haiku_runtime_blocked_"
        "critic_packet_validation_and_hidden_closed_abi_failure"
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
    assert evidence["algorithm_reference_invalid_cases"] == 22
    assert evidence["algorithm_behavioral_negative_candidates_rejected"] == 3
    assert evidence["statsmodels_implementation_version"] == "0.14.6"
    assert evidence["statsmodels_implementation_commit"] == (
        "40e6a84d26ac74623c6b94b718f0987ef0351c53"
    )
    assert evidence["statsmodels_parity_cases_correct"] == "5/5"
    assert evidence["statsmodels_parity_maximum_absolute_error"] < 3.6e-15
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
        "866ec7a94c2f745623ff61babd53858fc39e1312"
    )
    assert evidence["activation_push_confirmed_on_work_branch_and_main"] is True
    assert evidence["single_fresh_draw_only"] is True
    assert evidence["runtime_model"] == "claude-haiku-4-5-20251001"
    assert evidence["product_code_head"] == (
        "8c4461130b15fe06a86bd113e6f190e4e02bedbf"
    )
    assert evidence["runtime_product_model_calls"] == 46
    assert evidence["runtime_client_tool_model_turns"] == 45
    assert evidence["runtime_direct_model_calls"] == 1
    assert evidence["runtime_client_tool_executions"] == 42
    assert evidence["runtime_model_calls_by_workspace"] == {
        "ArchitectCoordinator": 1,
        "AlgorithmEngineer": 13,
        "GeneratedCodeSemanticReviewer": 7,
        "CriticEvaluator": 25,
    }
    assert evidence["runtime_status"] == "BLOCKED"
    assert evidence["runtime_terminal_classification"] == (
        "critic_packet_validation_failed"
    )
    assert evidence["runtime_mode_conformant"] is True
    assert evidence["runtime_research_eval_complete"] is False
    assert evidence["runtime_outer_graph_iterations"] == 4
    assert evidence["runtime_same_owner_workspace_continuations"] == 0
    assert evidence["algorithm_source_edits"] == 3
    assert evidence["algorithm_source_executions"] == 3
    assert evidence["algorithm_source_terminal_commit_submitted"] is True
    assert evidence["algorithm_handoff_materialized"] is True
    assert evidence["accepted_algorithm_handoff_id"] == (
        "accepted_algorithm_handoff:a5b6098435daf9ba9cdc"
    )
    assert evidence["accepted_algorithm_handoff_hash"] == (
        "5a83f9c39f95ec8cf2716e39259e25e762a9ef4454d8465fc6882e8ebd0d0028"
    )
    assert evidence["algorithm_semantic_reviewer_executed"] is True
    assert evidence["algorithm_semantic_review_accepted"] is True
    assert evidence["reviewer_probe_executions"] == 2
    assert evidence["reviewer_successful_exact_probes"] == 1
    assert evidence["hidden_gold_tasks_evaluated"] == 1
    assert evidence["hidden_algorithm_execution_attempted"] is True
    assert evidence["hidden_algorithm_execution_passed"] is True
    assert evidence["hidden_algorithm_estimator_invocations"] == 16
    assert evidence["hidden_algorithm_checks_passed"] == "11/13"
    assert evidence["hidden_candidate_source_hash"] == (
        "67bac620c83b1c8e2b504163c1392a2ef65ce432a7c5d590f10cd7162ad622db"
    )
    assert evidence["hidden_harness_result_hash"] == (
        "e3a25e1ead805b266b51a42dbe7021cec61434b076fa3f196583e53fae5e2080"
    )
    assert evidence["hidden_evaluator_source_hash"] == (
        "f0169d7b4a5df3dbbabe37698d9053d9fb56e1cb8cbe1582b447722b5976cef8"
    )
    assert evidence["runtime_feedback_generated"] is False
    assert evidence["post_run_shared_mechanism_commit"] == (
        "a97a35153013c733987f652a32bea23cfb4f5713"
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
    assert evidence["ladder_score_after_consumption"] == "7/103"

    expected_runtime_hashes = {
        "lowess_local_linear_nonrobust_paper_to_code_runtime_result.json": (
            "5d532b32852f322adef94086a2998145323fc3b202e15c8911771e57172d6148"
        ),
        "research_agent_runtime_manifest.json": (
            "c042936a69b2f8c72461b76abe89c614efe0ea2c39a5b8f3cbcfda9809316bb3"
        ),
        "research_capability_gold_evaluation.json": (
            "d1c496652e09a36afc6cc87ca546209d0ccb21780890751d7a1f1b6b1b0241bd"
        ),
        "runtime_failure_summary.json": (
            "39c09135593cc5dd420a06917e60888b6ec10e812a83a546311df176fc0aeeda"
        ),
        "runtime_llm_topology.json": (
            "efdb9d07b2470ca29fb2dfc5a56cc6b5e9fe80a9ca9b32743b44c059d0853f5c"
        ),
    }
    for name, expected_hash in expected_runtime_hashes.items():
        assert hashlib.sha256((RUN_DIR / name).read_bytes()).hexdigest() == expected_hash

    runtime_visible = json.dumps(
        {"candidate": candidate, "question": visible_question}, sort_keys=True
    )
    for hidden_name in (
        str(GOLD_MANIFEST),
        "reference_estimator.py",
        "hidden_algorithm_harness.py",
        "statsmodels_parity_record.json",
        "negative_global_linear.py",
        "negative_local_constant.py",
        "negative_all_points.py",
    ):
        assert hidden_name not in runtime_visible

    readiness = ladder["current_readiness"]
    assert readiness["scored_tasks_total"] == 106
    assert readiness["unconsumed_scored_tasks"] == 1
    assert readiness["consumed_scored_tasks"] == 105
    assert readiness["fully_gold_configured_tasks"] == 106
    assert readiness["fully_gold_passed_tasks"] == 7
