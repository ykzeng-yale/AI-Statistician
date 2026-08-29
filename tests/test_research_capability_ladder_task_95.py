from __future__ import annotations

import hashlib
import json
from pathlib import Path

from ai_statistician.fingerprint import stable_hash
from ai_statistician.research_gold_evaluation import _visible_question_hash_payload


LADDER_PATH = Path("benchmarks/research_capability_ladder_20260814.json")
TASK_ID = "delong_single_auc_variance_known_result"


def test_delong_integrated_l0_sole_draw_is_consumed_without_credit() -> None:
    ladder = json.loads(LADDER_PATH.read_text(encoding="utf-8"))
    candidate = next(
        row for row in ladder["initial_candidate_queue"] if row["id"] == TASK_ID
    )
    evidence = candidate["activation_evidence"]

    assert candidate["level"] == "L0"
    assert candidate["family"] == "diagnostic_accuracy_auc_inference"
    assert candidate["status"] == "consumed_scored"
    assert candidate["activation_status"] == (
        "fresh_live_v1_consumed_exact_haiku_critic_scientific_inconclusive_gold_failed"
    )
    assert candidate["gold_bundle_id"] == (
        "research-l0-delong-single-auc-variance-20260829-v1"
    )
    assert candidate["gold_manifest_sha256"] == (
        "cd784110a4d3bdd67ca631f23a0a008ee3132ffed6cb18a20243d54fe9732a7f"
    )
    assert candidate["gold_descriptor_hash"] == (
        "388a59ce8a789aed4339e0bc9033154bc565f2abe4307dbbefa9df02ab7a3b69"
    )
    assert evidence["codex_harness_mechanism_head"] == (
        "07448d9d14eef3253bee82647eeccd535d77f107"
    )
    assert evidence["visible_question_activation_commit"] == (
        "9507796c609d4125154dcd118b480a384ffec625"
    )
    assert evidence["research_source_manifest_sha256"] == (
        "5d8b70141930db165e29b9c88ed5f7ad1bb8885e69e6f55e99e3f586b705ff3f"
    )
    assert evidence["estimator_execution_contract_id"] == (
        "frozen_estimator_execution_contract:878cc41201ffebc3a192"
    )
    assert evidence["activation_schema_version"] == 4
    assert evidence["theory_authority_exact_checks"] == 7
    assert evidence["theory_authority_exact_checks_correct"] == 7
    assert evidence["algorithm_authority_checks"] == 13
    assert evidence["algorithm_authority_checks_correct"] == 13
    assert evidence["empirical_authority_checks"] == 8
    assert evidence["empirical_authority_checks_correct"] == 8
    assert evidence["semantic_protocol_version"] == 10
    assert evidence["semantic_activation_attempts"] == 1
    assert evidence["semantic_calibration_total_model_calls"] == 8
    assert evidence["semantic_calibration_cases"] == 6
    assert evidence["semantic_calibration_cases_correct"] == 6
    assert evidence["semantic_candidate_mode_negative_cases"] == 1
    assert evidence["semantic_candidate_mode_negative_cases_correct"] == 1
    assert evidence["semantic_reference_claims"] == 10
    assert evidence["semantic_reference_candidate_passed"] is True
    assert evidence["semantic_activation_judgment_hash"] == (
        "d1d3459081e5917134110a61736619b769498dce3956979e474f180a41ad2617"
    )
    assert evidence["semantic_calibration_model"] == (
        "claude-haiku-4-5-20251001"
    )
    assert evidence["activation_reference_tasks_passed"] == 1
    assert evidence["activation_negative_controls_rejected"] == 3
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
    assert evidence["runtime_product_model_calls"] == 77
    assert evidence["runtime_client_tool_model_turns"] == 75
    assert evidence["runtime_direct_model_calls"] == 2
    assert evidence["runtime_client_tool_executions"] == 82
    assert evidence["sonnet_product_calls"] == 0
    assert evidence["opus_product_calls"] == 0
    assert evidence["formalization_requirement"] == "not_applicable"
    assert evidence["formalizer_executed"] is False
    assert evidence["theory_developer_executed"] is True
    assert evidence["independently_accepted_theory_packet"] is True
    assert evidence["hidden_theory_exact_checks_passed"] == 7
    assert evidence["hidden_theory_exact_checks_total"] == 7
    assert evidence["hidden_theory_semantic_claims_passed"] == 10
    assert evidence["hidden_theory_semantic_claims_total"] == 10
    assert evidence["hidden_theory_combined_passed"] is True
    assert evidence["generated_algorithm_execution_attempted"] is True
    assert evidence[
        "generated_algorithm_sandbox_accepted_before_commit_failure"
    ] is True
    assert evidence["generated_algorithm_explicit_commit"] is False
    assert evidence["generated_algorithm_handoff_accepted"] is False
    assert evidence["generated_simulation_execution_attempted"] is True
    assert evidence[
        "generated_simulation_sandbox_accepted_before_commit_failure"
    ] is True
    assert evidence["generated_simulation_explicit_commit"] is False
    assert evidence["generated_simulation_handoff_accepted"] is False
    assert evidence["hidden_algorithm_execution_attempted"] is False
    assert evidence["hidden_empirical_execution_attempted"] is False
    assert evidence["activation_ledger_commit"] == (
        "70c5678a3cbc1d294cbbcdfab1ba2ab34cc06dc9"
    )
    assert evidence["activation_push_confirmed_on_work_branch_and_main"] is True
    assert evidence["product_code_head"] == (
        "b83893652e1805668b7f58f1e8f1d91f12294aa4"
    )
    assert evidence["model_draw_resampling_blocked"] is True
    assert evidence["runtime_status"] == "BLOCKED"
    assert evidence["runtime_terminal_classification"] == (
        "critic_scientific_inconclusive"
    )
    assert evidence["runtime_max_iterations_reached"] is False
    assert evidence["runtime_outer_graph_iterations"] == 6
    assert evidence["runtime_trace_steps"] == 8
    assert evidence["runtime_same_owner_workspace_continuations"] == 2
    assert evidence["post_runtime_evaluator_model_calls"] == 1
    assert evidence["hidden_expected_values_disclosed"] is False
    assert evidence["runtime_feedback_generated"] is False
    assert evidence["hidden_leak_match_count"] == 0
    assert evidence["closeout_evidence_commit"] == (
        "82cfc09190312964254a69cf7c6ad17c2523d202"
    )
    assert evidence["automated_full_task_passed"] is False
    assert evidence["full_task_passed"] is False
    assert evidence["trusted_capability_credit"] is False
    assert evidence["ladder_score_before_activation"] == "7/94"
    assert evidence["ladder_score_after_activation"] == "7/95"
    assert evidence["ladder_score_after_consumption"] == "7/95"

    run_path = Path(evidence["run_path"])
    immutable_files = {
        "research_agent_runtime_manifest.json": evidence[
            "runtime_manifest_sha256"
        ],
        "delong_single_auc_variance_known_result_runtime_result.json": evidence[
            "runtime_result_sha256"
        ],
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
    assert evaluated["hidden_harness_execution_attempted"] is False
    assert evaluated["hidden_empirical_execution_attempted"] is False

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
    assert question["task_intent"]["theory"] == "required"
    assert question["task_intent"]["scientific_code"] == "required"
    assert question["task_intent"]["empirical"] == "required"
    assert question["task_intent"]["formal"] == "not_applicable"
    assert question["source"]["primary_paper"]["doi"] == "10.2307/2531595"
    assert question["source"]["algorithm_paper"]["doi"] == (
        "10.1109/LSP.2014.2337313"
    )
    assert question["source"]["implementation_convention"]["commit"] == (
        "be0475b49cb353318703f9e48aa9eb9cd125d677"
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
        "negative_open_request_contract.py",
        "negative_strict_greater.py",
    ):
        assert hidden_identity not in runtime_visible

    readiness = ladder["current_readiness"]
    assert readiness["scored_tasks_total"] == 98
    assert readiness["unconsumed_scored_tasks"] == 0
    assert readiness["consumed_scored_tasks"] == 98
    assert readiness["fully_gold_configured_tasks"] == 98
    assert readiness["fully_gold_passed_tasks"] == 7
