from __future__ import annotations

import hashlib
import json
from pathlib import Path

from ai_statistician.estimator_interface_contract import (
    frozen_estimator_execution_contract_id,
)
from ai_statistician.fingerprint import stable_hash


LADDER_PATH = Path("benchmarks/research_capability_ladder_20260814.json")
TASK_ID = "poisson_loglinear_irls_known_implementation"


def test_poisson_loglinear_l0_task_is_consumed_after_sole_product_draw() -> None:
    ladder = json.loads(LADDER_PATH.read_text(encoding="utf-8"))
    candidate = next(
        row for row in ladder["initial_candidate_queue"] if row["id"] == TASK_ID
    )
    evidence = candidate["activation_evidence"]

    assert candidate["level"] == "L0"
    assert candidate["family"] == "poisson_loglinear_glm_irls"
    assert candidate["status"] == "consumed_scored"
    assert candidate["activation_status"] == (
        "fresh_live_v1_consumed_runtime_blocked_no_source_authored_hidden_not_attempted"
    )
    assert candidate["gold_bundle_id"] == (
        "research-l0-poisson-loglinear-irls-20260828-v1"
    )
    assert candidate["gold_manifest_sha256"] == (
        "cf05bcbe50992825c5dad0f0faff4b5dfb2f0f9832ab5d60fe25395d72944cd1"
    )
    assert candidate["gold_descriptor_hash"] == (
        "08d8ca4e01cee37201e29c716add68b70df3b0de19426f4af4a6987086f7cdbd"
    )
    assert evidence["visible_question_activation_commit"] == (
        "4be4516435cf70ecbc725dbe7396b59e11e4d8f7"
    )
    assert evidence["research_source_snapshot_hash"] == (
        "09b04e1ea313063bf190e222424c74e29633a62b5dc4ab2592667bebec81aa2d"
    )
    assert evidence["activation_schema_version"] == 4
    assert evidence["reference_algorithm_contract_checks_passed"] is True
    assert evidence["reference_algorithm_valid_cases"] == 4
    assert evidence["reference_algorithm_invalid_cases"] == 20
    assert evidence["algorithm_negative_variants_rejected"] == 3
    assert evidence["reference_empirical_designs_passed"] == 2
    assert evidence["reference_empirical_replicates_per_design"] == 1000
    assert evidence["reference_empirical_invocations"] == 2000
    assert evidence["activation_reference_tasks_passed"] == 1
    assert evidence["activation_negative_controls_rejected"] == 4
    assert evidence["activation_semantic_model_calls"] == 0
    assert evidence["activation_semantic_qualification_model_calls"] == 0
    assert evidence["hidden_gold_manifest_validated"] is True
    assert evidence["gold_frozen_before_first_runtime_model_call"] is True
    assert evidence["activation_ledger_commit"] == (
        "c2a07d37e35d41429930e7fbfad6f13fe0cc733a"
    )
    assert evidence["activation_push_confirmed_on_work_branch_and_main"] is True
    assert evidence["preactivation_product_model_calls"] == 0
    assert evidence["preactivation_evaluator_model_calls"] == 0
    assert evidence["first_runtime_model_call_occurred"] is True
    assert evidence["fresh_live_runs"] == 1
    assert evidence["runtime_invocations"] == 1
    assert evidence["runtime_model"] == "claude-haiku-4-5-20251001"
    assert evidence["product_model_turns"] == 29
    assert evidence["algorithm_client_tool_model_turns"] == 26
    assert evidence["algorithm_source_search_calls"] == 10
    assert evidence["algorithm_source_read_calls"] == 14
    assert evidence["algorithm_terminal_commit_calls"] == 2
    assert evidence["algorithm_source_updates"] == 0
    assert evidence["algorithm_sandbox_checks"] == 0
    assert evidence["hidden_candidate_execution_attempted"] is False
    assert evidence["hidden_evaluator_model_calls"] == 0
    assert evidence["sonnet_product_calls"] == 0
    assert evidence["opus_product_calls"] == 0
    assert evidence["formalization_requirement"] == "not_applicable"
    assert evidence["formalizer_executed"] is False
    assert evidence["automated_full_task_passed"] is False
    assert evidence["full_task_passed"] is False
    assert evidence["trusted_capability_credit"] is False
    assert evidence["model_draw_resampling_blocked"] is True
    assert evidence["post_run_shared_mechanism_commit"] == (
        "c3a754e2cde4a264b4f9b54f14b39a78fb1bf499"
    )

    visible_path = Path(candidate["visible_questions_path"])
    assert hashlib.sha256(visible_path.read_bytes()).hexdigest() == (
        evidence["visible_questions_sha256"]
    )
    question = json.loads(visible_path.read_text(encoding="utf-8"))["questions"][0]
    assert question["id"] == TASK_ID
    assert question["task_intent"] == candidate["task_intent"]
    assert question["task_intent"]["theory"] == "not_applicable"
    assert question["task_intent"]["scientific_code"] == "required"
    assert question["task_intent"]["empirical"] == "required"
    assert question["task_intent"]["formal"] == "not_applicable"
    assert question["source"]["research_source_snapshot_hash"] == (
        evidence["research_source_snapshot_hash"]
    )
    contract = question["estimator_execution_contract"]
    assert frozen_estimator_execution_contract_id(contract) == (
        evidence["estimator_execution_contract_id"]
    )
    assert stable_hash(contract) == evidence["estimator_execution_contract_hash"]
    assert "Poisson log-link model" in question["description"]
    assert "exactly 1000 fresh replicates" in question["description"]
    assert "formalization" in question["description"]

    runtime_visible = json.dumps(
        {"candidate": candidate, "question": question}, sort_keys=True
    )
    for hidden_name in (
        "gold_manifest.json",
        "hidden_algorithm_harness.py",
        "hidden_empirical_harness.py",
        "reference_estimator.py",
        "negative_half_standard_errors.py",
    ):
        assert hidden_name not in runtime_visible

    readiness = ladder["current_readiness"]
    assert readiness["scored_tasks_total"] == 99
    assert readiness["unconsumed_scored_tasks"] == 0
    assert readiness["consumed_scored_tasks"] == 99
    assert readiness["fully_gold_configured_tasks"] == 99
    assert readiness["fully_gold_passed_tasks"] == 7
