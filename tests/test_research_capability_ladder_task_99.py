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
from ai_statistician.research_source_library import load_research_source_snapshot


LADDER_PATH = Path("benchmarks/research_capability_ladder_20260814.json")
VISIBLE_PATH = Path(
    "benchmarks/research_l2_ledoit_wolf_questions_20260829.json"
)
SOURCE_MANIFEST = Path(
    "benchmarks/research_sources/ledoit_wolf_20260829/source_manifest.json"
)
GOLD_MANIFEST = Path(
    "/Users/yukangzengcmac/.codex/evaluator_authority/AI-Statistician/"
    "research-l2-ledoit-wolf-20260829-v1/gold_manifest.json"
)
TASK_ID = "ledoit_wolf_linear_shrinkage_paper_to_code"
CLOSEOUT_COMMIT = "4b0ca7a6c96d156d59554802225331dc25bdfeb7"


def test_ledoit_wolf_l2_consumed_result_is_immutable() -> None:
    ladder = json.loads(LADDER_PATH.read_text(encoding="utf-8"))
    candidate = next(
        row for row in ladder["initial_candidate_queue"] if row["id"] == TASK_ID
    )
    evidence = candidate["activation_evidence"]

    assert candidate["level"] == "L2"
    assert candidate["family"] == "high_dimensional_covariance_shrinkage"
    assert candidate["status"] == "consumed_scored"
    assert candidate["activation_status"] == (
        "fresh_live_v1_consumed_exact_haiku_runtime_blocked_gold_failed_"
        "theory_semantics_and_uncommitted_algorithm"
    )
    assert evidence["codex_harness_mechanism_head"] == (
        "2a988ca8a86030d90e790530db22ea38138f3259"
    )
    assert evidence["official_codex_checkout_head"] == (
        "6478a751fde8884b2fdc76486fe23175a8e795d4"
    )
    assert evidence["activation_schema_version"] == 4
    assert evidence["semantic_protocol_version"] == 11
    assert evidence["semantic_candidate_adjudication_strategy"] == (
        "integrated_plus_adversarial"
    )
    assert evidence["algorithm_authority_checks_correct"] == "13/13"
    assert evidence["empirical_authority_checks_correct"] == "9/9"
    assert evidence["semantic_calibration_cases_correct"] == "6/6"
    assert evidence["semantic_candidate_mode_negative_cases_correct"] == "1/1"
    assert evidence["semantic_successful_qualification_model_calls"] == 16
    assert evidence["semantic_calibration_model"] == (
        "claude-haiku-4-5-20251001"
    )
    assert evidence["activation_reference_tasks_passed"] == 1
    assert evidence["activation_negative_controls_rejected"] == 4
    assert evidence["activation_semantic_reference_documents_passed"] == 1
    assert evidence[
        "activation_semantic_candidate_mode_negative_controls_rejected"
    ] == 1
    assert evidence["activation_semantic_model_calls"] == 0
    assert evidence["activation_semantic_qualification_reused"] is True
    assert evidence["hidden_gold_manifest_validated"] is True
    assert evidence["gold_frozen_before_first_runtime_model_call"] is True
    assert evidence["activation_ledger_commit"] == (
        "d08b8782600ab0ff246673d975153ab56e8e2bf2"
    )
    assert evidence["activation_push_confirmed_on_work_branch_and_main"] is True
    assert evidence["preactivation_product_model_calls"] == 0
    assert evidence["first_runtime_model_call_occurred"] is True
    assert evidence["fresh_live_runs"] == 1
    assert evidence["runtime_invocations"] == 1
    assert evidence["runtime_model"] == "claude-haiku-4-5-20251001"
    assert evidence["runtime_product_model_calls"] == 70
    assert evidence["runtime_client_tool_model_turns"] == 70
    assert evidence["runtime_direct_model_calls"] == 0
    assert evidence["runtime_client_tool_executions"] == 80
    assert evidence["runtime_tool_errors_returned_to_owner"] == 16
    assert evidence["runtime_model_calls_by_subsystem"] == {
        "AlgorithmEngineer": 13,
        "ArchitectCoordinator": 15,
        "CriticEvaluator": 8,
        "GeneratedCodeSemanticReviewer": 3,
        "SimulationEvaluator": 9,
        "TheoryDeveloper": 22,
    }
    assert evidence["sonnet_product_calls"] == 0
    assert evidence["opus_product_calls"] == 0
    assert evidence["formalization_requirement"] == "not_applicable"
    assert evidence["formalizer_executed"] is False
    assert evidence["hidden_theory_exact_checks_passed"] == 7
    assert evidence["hidden_theory_exact_checks_total"] == 7
    assert evidence["hidden_theory_semantic_claims_satisfied"] == 6
    assert evidence["hidden_theory_semantic_claims_violated"] == 1
    assert evidence["hidden_theory_semantic_claims_inconclusive"] == 1
    assert evidence["hidden_theory_combined_passed"] is False
    assert evidence["generated_algorithm_executed"] is True
    assert evidence["generated_algorithm_explicit_commit"] is False
    assert evidence["generated_algorithm_handoff_accepted"] is False
    assert evidence["hidden_algorithm_execution_attempted"] is False
    assert evidence["generated_simulation_executed"] is True
    assert evidence["generated_simulation_explicit_commit"] is True
    assert evidence["generated_simulation_exploratory_passed"] is True
    assert evidence["generated_simulation_confirmatory_passed"] is False
    assert evidence["simulation_upstream_algorithm_handoff_receipt_present"] is False
    assert evidence["hidden_empirical_execution_attempted"] is False
    assert evidence["post_runtime_evaluator_model_calls"] == 2
    assert evidence["runtime_status"] == "BLOCKED"
    assert evidence["runtime_terminal_classification"] == (
        "critic_scientific_inconclusive"
    )
    assert evidence["critic_unresolved_gap_disclosure_present"] is False
    assert evidence["hidden_expected_values_disclosed"] is False
    assert evidence["runtime_feedback_generated"] is False
    assert evidence["operator_disposition"] == "FAILED"
    assert evidence["closeout_evidence_commit"] == CLOSEOUT_COMMIT
    assert evidence["automated_full_task_passed"] is False
    assert evidence["full_task_passed"] is False
    assert evidence["trusted_capability_credit"] is False
    assert evidence["ladder_score_before_activation"] == "7/98"
    assert evidence["ladder_score_after_activation"] == "7/99"
    assert evidence["ladder_score_after_consumption"] == "7/99"
    assert evidence["runtime_manifest_sha256"] == (
        "234c87d87917053ad384773cc60f8cadcafdec42021677248c3b129321bb2f5d"
    )
    assert evidence["gold_evaluation_sha256"] == (
        "fe6a4efb2b646b59d804321ce5391a4ae92830bff7d64012a110ce7cb1f409e8"
    )
    assert evidence["model_draw_resampling_blocked"] is True

    question = json.loads(VISIBLE_PATH.read_text(encoding="utf-8"))["questions"][0]
    assert question["id"] == TASK_ID
    assert hashlib.sha256(VISIBLE_PATH.read_bytes()).hexdigest() == evidence[
        "visible_questions_sha256"
    ]
    assert stable_hash(question) == evidence["visible_question_full_hash"]
    assert stable_hash(_visible_question_hash_payload(question)) == evidence[
        "runtime_visible_question_hash"
    ]
    assert frozen_estimator_execution_contract_id(
        question["estimator_execution_contract"]
    ) == evidence["estimator_execution_contract_id"]
    assert question["task_intent"] == candidate["task_intent"]
    assert question["task_intent"]["theory"] == "required"
    assert question["task_intent"]["scientific_code"] == "required"
    assert question["task_intent"]["empirical"] == "required"
    assert question["task_intent"]["formal"] == "not_applicable"

    source = load_research_source_snapshot(SOURCE_MANIFEST)
    assert source.snapshot_hash == candidate["source_snapshot_hash"]
    assert source.manifest_sha256 == candidate["source_manifest_sha256"]
    assert len(source.documents) == 1

    descriptor = validate_research_gold_benchmark_manifest(GOLD_MANIFEST)
    assert descriptor["active_task_ids"] == [TASK_ID]
    assert descriptor["benchmark_manifest_hash"] == candidate[
        "gold_descriptor_hash"
    ]
    assert hashlib.sha256(GOLD_MANIFEST.read_bytes()).hexdigest() == candidate[
        "gold_manifest_sha256"
    ]

    runtime_visible = json.dumps(
        {"candidate": candidate, "question": question}, sort_keys=True
    )
    for hidden_name in (
        "gold_manifest.json",
        "reference_estimator.py",
        "hidden_algorithm_harness.py",
        "hidden_empirical_harness.py",
        "semantic_reference.md",
        "semantic_rubric.json",
        "candidate_mode_near_miss.md",
    ):
        assert hidden_name not in runtime_visible

    readiness = ladder["current_readiness"]
    assert readiness["scored_tasks_total"] == 99
    assert readiness["unconsumed_scored_tasks"] == 0
    assert readiness["consumed_scored_tasks"] == 99
    assert readiness["fully_gold_configured_tasks"] == 99
    assert readiness["fully_gold_passed_tasks"] == 7
