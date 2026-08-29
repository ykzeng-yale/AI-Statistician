from __future__ import annotations

import hashlib
import json
from pathlib import Path

from ai_statistician.fingerprint import stable_hash
from ai_statistician.research_gold_evaluation import _visible_question_hash_payload


LADDER_PATH = Path("benchmarks/research_capability_ladder_20260814.json")
TASK_ID = "moran_i_randomization_expectation_known_result"


def test_moran_i_integrated_l0_consumed_result_is_immutable() -> None:
    ladder = json.loads(LADDER_PATH.read_text(encoding="utf-8"))
    candidate = next(
        row for row in ladder["initial_candidate_queue"] if row["id"] == TASK_ID
    )
    evidence = candidate["activation_evidence"]

    assert candidate["level"] == "L0"
    assert candidate["family"] == "spatial_randomization_autocorrelation"
    assert candidate["status"] == "consumed_scored"
    assert candidate["activation_status"] == (
        "fresh_live_v1_consumed_exact_haiku_runtime_accepted_gold_failed_"
        "closed_input_contract"
    )
    assert candidate["gold_bundle_id"] == (
        "research-l0-moran-i-randomization-20260829-v1"
    )
    assert candidate["gold_manifest_sha256"] == (
        "a42a9d931a94b921e5b75f0cc89bd82d12da6277b9affa1375ee5ef137ad3d67"
    )
    assert candidate["gold_descriptor_hash"] == (
        "978a0a6b7d9c5a15d9bfffd5688b8809881772a2764692ff6081c01decf64c07"
    )
    assert evidence["visible_question_activation_commit"] == (
        "1dffb2203d60a51a3b174f636a169f6fd6514270"
    )
    assert evidence["estimator_execution_contract_id"] == (
        "frozen_estimator_execution_contract:fed33f308908b86a648c"
    )
    assert evidence["activation_schema_version"] == 4
    assert evidence["theory_authority_exact_checks"] == 7
    assert evidence["theory_authority_exact_checks_correct"] == 7
    assert evidence["algorithm_authority_checks"] == 7
    assert evidence["algorithm_authority_checks_correct"] == 7
    assert evidence["empirical_authority_checks"] == 10
    assert evidence["empirical_authority_checks_correct"] == 10
    assert evidence["semantic_protocol_version"] == 10
    assert evidence["semantic_calibration_total_model_calls"] == 8
    assert evidence["semantic_calibration_cases"] == 6
    assert evidence["semantic_calibration_cases_correct"] == 6
    assert evidence["semantic_candidate_mode_negative_cases"] == 1
    assert evidence["semantic_candidate_mode_negative_cases_correct"] == 1
    assert evidence["semantic_reference_claims"] == 8
    assert evidence["semantic_reference_candidate_passed"] is True
    assert evidence["semantic_activation_judgment_hash"] == (
        "68c7ca1a2fbf2dca43e317b6784e2e25eaa9a25798c609aa5098ff25bd481622"
    )
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
    assert evidence["activation_semantic_qualification_model_calls"] == 8
    assert evidence["activation_semantic_qualification_reused"] is True
    assert evidence["hidden_gold_manifest_validated"] is True
    assert evidence["gold_frozen_before_first_runtime_model_call"] is True
    assert evidence["preactivation_product_model_calls"] == 0
    assert evidence["preactivation_evaluator_model_calls"] == 8
    assert evidence["first_runtime_model_call_occurred"] is True
    assert evidence["fresh_live_runs"] == 1
    assert evidence["runtime_invocations"] == 1
    assert evidence["runtime_model"] == "claude-haiku-4-5-20251001"
    assert evidence["runtime_product_model_calls"] == 72
    assert evidence["runtime_client_tool_model_turns"] == 72
    assert evidence["runtime_direct_model_calls"] == 0
    assert evidence["runtime_client_tool_executions"] == 79
    assert evidence["runtime_model_calls_by_subsystem"] == {
        "AlgorithmEngineer": 14,
        "ArchitectCoordinator": 11,
        "CriticEvaluator": 5,
        "GeneratedCodeSemanticReviewer": 18,
        "SimulationEvaluator": 14,
        "TheoryDeveloper": 10,
    }
    assert evidence["sonnet_product_calls"] == 0
    assert evidence["opus_product_calls"] == 0
    assert evidence["formalization_requirement"] == "not_applicable"
    assert evidence["formalizer_executed"] is False
    assert evidence["theory_developer_executed"] is True
    assert evidence["independently_accepted_theory_packet"] is True
    assert evidence["accepted_theory_packet_id"] == (
        "theory_derivation:49a3b69a55fc1cba1fb8cabc"
    )
    assert evidence["accepted_theory_packet_hash"] == (
        "79c2a5c1d1643eebad952ae41e27a77eb88c2a5aebe55971b608f2737f748bbf"
    )
    assert evidence["accepted_theory_document_sha256"] == (
        "5817c2a73d6475b4b1ea7ed03f19e84c5a5da0b8f4d9f5c27e1a4f3d1e00a60e"
    )
    assert evidence["accepted_theory_document_lines"] == 240
    assert evidence["theory_referee_report_sha256"] == (
        "1f4a53f0c3e4e7f4a8b5e77e193f7394abe9ada10612f7ddb43b22626d7815b3"
    )
    assert evidence["theory_referee_report_lines"] == 121
    assert evidence["hidden_theory_execution_attempted"] is True
    assert evidence["hidden_theory_exact_checks_passed"] == 7
    assert evidence["hidden_theory_exact_checks_total"] == 7
    assert evidence["hidden_theory_semantic_claims_passed"] == 8
    assert evidence["hidden_theory_semantic_claims_total"] == 8
    assert evidence["hidden_theory_combined_passed"] is True
    assert evidence["generated_algorithm_executed"] is True
    assert evidence["generated_algorithm_explicit_commit"] is True
    assert evidence["generated_algorithm_handoff_accepted"] is True
    assert evidence["accepted_algorithm_handoff_id"] == (
        "accepted_algorithm_handoff:ba4099a7fc101cb84907"
    )
    assert evidence["accepted_algorithm_handoff_hash"] == (
        "98fc9ece628268e6229fcb75b37fa19900477ac6434b5d24af1d777cd358b24c"
    )
    assert evidence["generated_algorithm_source_hash"] == (
        "573791bedc0de88a1e74642949b09ea580988eeeb00f23b4f4317ffc9ff5192b"
    )
    assert evidence["hidden_algorithm_execution_attempted"] is True
    assert evidence["hidden_algorithm_execution_passed"] is True
    assert evidence["hidden_algorithm_checks_passed"] == 6
    assert evidence["hidden_algorithm_checks_total"] == 7
    assert evidence["hidden_algorithm_closed_input_contract_passed"] is False
    assert evidence["generated_simulation_executed"] is True
    assert evidence["generated_simulation_explicit_commit"] is True
    assert evidence["generated_simulation_handoff_accepted"] is True
    assert evidence["generated_simulation_semantic_review_accepted"] is True
    assert evidence["hidden_empirical_execution_attempted"] is True
    assert evidence["hidden_empirical_execution_passed"] is True
    assert evidence["hidden_empirical_checks_passed"] == 10
    assert evidence["hidden_empirical_checks_total"] == 10
    assert evidence["post_runtime_evaluator_model_calls"] == 1
    assert evidence["activation_ledger_commit"] == (
        "9092ea5da6519fc3f931f0bd3332ecd6f2aaefe3"
    )
    assert evidence["activation_push_confirmed_on_work_branch_and_main"] is True
    assert evidence["product_code_head"] == (
        "11db881dccc077a640db535b25b74186528658d8"
    )
    assert evidence["model_draw_resampling_blocked"] is True
    assert evidence["runtime_status"] == "ACCEPTED"
    assert evidence["runtime_max_iterations_reached"] is False
    assert evidence["runtime_outer_graph_iterations"] == 11
    assert evidence["runtime_trace_steps"] == 11
    assert evidence["runtime_same_owner_workspace_continuations"] == 0
    assert evidence["hidden_expected_values_disclosed"] is False
    assert evidence["runtime_feedback_generated"] is False
    assert evidence["hidden_leak_match_count"] == 0
    assert evidence["operator_disposition"] == "FAILED"
    assert evidence["closeout_evidence_commit"] == (
        "9862788bc9618c38501f57dc8c7301b56a5b481c"
    )
    assert evidence["automated_full_task_passed"] is False
    assert evidence["full_task_passed"] is False
    assert evidence["trusted_capability_credit"] is False
    assert evidence["ladder_score_before_activation"] == "7/95"
    assert evidence["ladder_score_after_activation"] == "7/96"
    assert evidence["ladder_score_after_consumption"] == "7/96"

    run_path = Path(evidence["run_path"])
    immutable_files = {
        "research_agent_runtime_manifest.json": evidence[
            "runtime_manifest_sha256"
        ],
        "moran_i_randomization_expectation_known_result_runtime_result.json": (
            evidence["runtime_result_sha256"]
        ),
        "research_capability_gold_evaluation.json": evidence[
            "gold_evaluation_sha256"
        ],
        "runtime_llm_topology.json": evidence["runtime_topology_sha256"],
    }
    for name, expected_sha256 in immutable_files.items():
        assert hashlib.sha256((run_path / name).read_bytes()).hexdigest() == (
            expected_sha256
        )

    gold = json.loads(
        (run_path / "research_capability_gold_evaluation.json").read_text(
            encoding="utf-8"
        )
    )
    assert gold["hidden_expected_values_disclosed"] is False
    assert gold["runtime_feedback_generated"] is False
    assert gold["n_tasks_passed"] == 0
    evaluated = gold["tasks"][0]
    assert evaluated["task_id"] == TASK_ID
    assert evaluated["task_passed"] is False
    assert evaluated["hidden_theory_combined_passed"] is True
    assert evaluated["hidden_harness_execution_attempted"] is True
    assert evaluated["hidden_harness_execution_passed"] is True
    assert sum(row["passed"] for row in evaluated["hidden_check_results"]) == 6
    assert len(evaluated["hidden_check_results"]) == 7
    assert evaluated["hidden_empirical_execution_attempted"] is True
    assert evaluated["hidden_empirical_checks_passed"] is True
    assert sum(
        row["passed"] for row in evaluated["hidden_empirical_check_results"]
    ) == 10
    assert evaluated["dimension_status"]["theory"]["status"] == "passed"
    assert evaluated["dimension_status"]["scientific_code"]["status"] == (
        "failed"
    )
    assert evaluated["dimension_status"]["empirical"]["status"] == "passed"

    visible_path = Path(candidate["visible_questions_path"])
    assert hashlib.sha256(visible_path.read_bytes()).hexdigest() == (
        evidence["visible_questions_sha256"]
    )
    question = json.loads(visible_path.read_text(encoding="utf-8"))["questions"][0]
    assert question["id"] == TASK_ID
    assert stable_hash(question) == evidence["visible_question_full_hash"]
    assert stable_hash(_visible_question_hash_payload(question)) == (
        evidence["runtime_visible_question_hash"]
    )
    assert question["task_intent"] == candidate["task_intent"]
    assert question["task_intent"]["formal"] == "not_applicable"
    assert question["source"]["primary_paper"]["doi"] == (
        "10.1093/biomet/37.1-2.17"
    )
    assert question["source"]["open_source_implementation"]["commit"] == (
        "dcd9c74bb2b78563c45d4f4a7977da9315d45c56"
    )

    runtime_visible = json.dumps(
        {"candidate": candidate, "question": question}, sort_keys=True
    )
    for hidden_identity in (
        "gold_manifest.json",
        "semantic_reference.md",
        "semantic_rubric.json",
        "semantic_calibration_cases.json",
        "candidate_mode_near_miss.md",
        "candidate_mode_negative_cases.json",
        "reference_estimator.py",
        "negative_missing_global_normalization.py",
        "negative_zero_null_expectation.py",
    ):
        assert hidden_identity not in runtime_visible

    readiness = ladder["current_readiness"]
    assert readiness["scored_tasks_total"] == 99
    assert readiness["unconsumed_scored_tasks"] == 1
    assert readiness["consumed_scored_tasks"] == 98
    assert readiness["fully_gold_configured_tasks"] == 99
    assert readiness["fully_gold_passed_tasks"] == 7
