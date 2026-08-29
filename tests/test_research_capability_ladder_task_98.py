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
)
from ai_statistician.research_source_library import load_research_source_snapshot


LADDER_PATH = Path("benchmarks/research_capability_ladder_20260814.json")
TASK_ID = "gaussian_mixture_em_monotonicity_known_result"
VISIBLE_PATH = Path(
    "benchmarks/research_l0_gaussian_mixture_em_questions_20260829.json"
)
SOURCE_MANIFEST = Path(
    "benchmarks/research_sources/gaussian_mixture_em_20260829/source_manifest.json"
)
ACTIVATION_COMMIT = "16afb75ce8c33fed544972269bd3285a78d2ac96"
PRODUCT_CODE_HEAD = "d40f1b5c3473e15e883dcb3095c98e41f4f5542a"
CLOSEOUT_COMMIT = "061229673e27a7f719fc5ca6ee6c12fbb39e4b2c"


def test_gaussian_mixture_em_l0_consumed_result_is_immutable() -> None:
    ladder = json.loads(LADDER_PATH.read_text(encoding="utf-8"))
    candidate = next(
        row for row in ladder["initial_candidate_queue"] if row["id"] == TASK_ID
    )
    evidence = candidate["activation_evidence"]

    assert candidate["level"] == "L0"
    assert candidate["family"] == "latent_variable_likelihood_optimization"
    assert candidate["status"] == "consumed_scored"
    assert candidate["activation_status"] == (
        "fresh_live_v1_consumed_exact_haiku_runtime_blocked_gold_failed_"
        "closed_input_contract_and_empirical_handoff"
    )
    assert candidate["gold_bundle_id"] == (
        "research-l0-gaussian-mixture-em-20260829-v1"
    )
    assert evidence["activation_schema_version"] == 4
    assert evidence["semantic_protocol_version"] == 11
    assert evidence["semantic_candidate_adjudication_strategy"] == (
        "integrated_plus_adversarial"
    )
    assert evidence["semantic_activation_attempts"] == 2
    assert evidence["semantic_calibration_total_model_calls"] == 34
    assert evidence["semantic_successful_qualification_model_calls"] == 16
    assert evidence["semantic_calibration_cases_correct"] == 6
    assert evidence["semantic_calibration_cases"] == 6
    assert evidence["semantic_candidate_mode_negative_cases_correct"] == 1
    assert evidence["semantic_candidate_mode_negative_cases"] == 1
    assert evidence["semantic_reference_claims"] == 8
    assert evidence["semantic_reference_candidate_passed"] is True
    assert evidence["semantic_calibration_model"] == (
        "claude-haiku-4-5-20251001"
    )
    assert evidence["activation_reference_tasks_passed"] == 1
    assert evidence["activation_negative_controls_rejected"] == 5
    assert evidence["activation_semantic_reference_documents_passed"] == 1
    assert evidence[
        "activation_semantic_candidate_mode_negative_controls_rejected"
    ] == 1
    assert evidence["activation_semantic_model_calls"] == 0
    assert evidence["activation_semantic_qualification_model_calls"] == 16
    assert evidence["activation_semantic_qualification_reused"] is True
    assert evidence["hidden_gold_manifest_validated"] is True
    assert evidence["gold_frozen_before_first_runtime_model_call"] is True
    assert evidence["activation_ledger_commit"] == ACTIVATION_COMMIT
    assert evidence["activation_push_confirmed_on_work_branch_and_main"] is True
    assert evidence["preactivation_product_model_calls"] == 0
    assert evidence["preactivation_evaluator_model_calls"] == 34
    assert evidence["first_runtime_model_call_occurred"] is True
    assert evidence["fresh_live_runs"] == 1
    assert evidence["runtime_invocations"] == 1
    assert evidence["runtime_model"] == "claude-haiku-4-5-20251001"
    assert evidence["runtime_product_model_calls"] == 76
    assert evidence["runtime_client_tool_model_turns"] == 76
    assert evidence["runtime_direct_model_calls"] == 0
    assert evidence["runtime_client_tool_executions"] == 97
    assert evidence["runtime_tool_errors_returned_to_owner"] == 15
    assert evidence["runtime_model_calls_by_subsystem"] == {
        "AlgorithmEngineer": 15,
        "ArchitectCoordinator": 10,
        "CriticEvaluator": 11,
        "GeneratedCodeSemanticReviewer": 16,
        "SimulationEvaluator": 9,
        "TheoryDeveloper": 15,
    }
    assert evidence["sonnet_product_calls"] == 0
    assert evidence["opus_product_calls"] == 0
    assert evidence["formalization_requirement"] == "not_applicable"
    assert evidence["formalizer_executed"] is False
    assert evidence["theory_developer_executed"] is True
    assert evidence["hidden_theory_exact_checks_passed"] == 7
    assert evidence["hidden_theory_semantic_claims_passed"] == 8
    assert evidence["hidden_theory_combined_passed"] is True
    assert evidence["post_runtime_evaluator_model_calls"] == 2
    assert evidence["generated_algorithm_executed"] is True
    assert evidence["generated_algorithm_explicit_commit"] is True
    assert evidence["generated_algorithm_handoff_accepted"] is True
    assert evidence["hidden_algorithm_checks_passed"] == 9
    assert evidence["hidden_algorithm_checks_total"] == 11
    assert evidence["hidden_algorithm_closed_input_contract_passed"] is False
    assert evidence["generated_simulation_executed"] is True
    assert evidence["generated_simulation_explicit_commit"] is True
    assert evidence["generated_simulation_exploratory_passed"] is True
    assert evidence["generated_simulation_confirmatory_passed"] is False
    assert evidence["generated_simulation_confirmatory_evidence_eligible"] is False
    assert evidence["simulation_upstream_algorithm_handoff_receipt_present"] is False
    assert evidence["hidden_empirical_checks_passed"] == 10
    assert evidence["hidden_empirical_checks_total"] == 10
    assert evidence["hidden_empirical_estimator_invocations"] == 600
    assert evidence["product_code_head"] == PRODUCT_CODE_HEAD
    assert evidence["runtime_status"] == "BLOCKED"
    assert evidence["runtime_terminal_classification"] == (
        "critic_scientific_inconclusive"
    )
    assert evidence["runtime_steps_executed"] == 10
    assert evidence["runtime_outer_graph_iterations"] == 9
    assert evidence["runtime_trace_steps"] == 10
    assert evidence["runtime_same_owner_workspace_continuations"] == 1
    assert evidence["hidden_expected_values_disclosed"] is False
    assert evidence["runtime_feedback_generated"] is False
    assert evidence["hidden_leak_match_count"] == 0
    assert evidence["operator_disposition"] == "FAILED"
    assert evidence["closeout_evidence_commit"] == CLOSEOUT_COMMIT
    assert evidence["automated_full_task_passed"] is False
    assert evidence["full_task_passed"] is False
    assert evidence["trusted_capability_credit"] is False
    assert evidence["model_draw_resampling_blocked"] is True
    assert evidence["ladder_score_before_activation"] == "7/97"
    assert evidence["ladder_score_after_activation"] == "7/98"
    assert evidence["ladder_score_after_consumption"] == "7/98"
    assert evidence["runtime_manifest_sha256"] == (
        "e7cc13a66351212327390fa2d3c3acc773cdc24bc32269a358396a91fa7587ff"
    )
    assert evidence["gold_evaluation_sha256"] == (
        "dac761c00cfa0b62f9d20d5ac1ba1beec6ad6d322bcd9193f10d743b0f84bb41"
    )

    question_payload = json.loads(VISIBLE_PATH.read_text(encoding="utf-8"))
    question = question_payload["questions"][0]
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
    assert question["source"]["primary_paper"]["doi"] == (
        "10.1111/j.2517-6161.1977.tb01600.x"
    )
    assert question["source"]["open_source_implementation"]["commit"] == (
        "88552088fad33d6ec70e1aaf633389d08fffb970"
    )

    source = load_research_source_snapshot(SOURCE_MANIFEST)
    assert source.snapshot_hash == evidence["research_source_snapshot_hash"]
    assert source.manifest_sha256 == evidence["research_source_manifest_sha256"]
    assert len(source.documents) == 3

    runtime_visible = json.dumps(
        {"candidate": candidate, "question": question}, sort_keys=True
    )
    for hidden_identity in (
        "gold_manifest.json",
        "semantic_reference.md",
        "semantic_rubric.json",
        "semantic_calibration_cases.json",
        "candidate_mode_near_miss.md",
        "reference_estimator.py",
        "negative_initial_only.py",
        "negative_reversed_final_weights.py",
        "negative_permissive.py",
    ):
        assert hidden_identity not in runtime_visible
