from __future__ import annotations

import hashlib
import json
from pathlib import Path


LADDER_PATH = Path("benchmarks/research_capability_ladder_20260814.json")
TASK_ID = "bayesian_online_changepoint_gamma_poisson_paper_to_code"
TASK_76_SHARED_MECHANISM_HEAD = "b9297aef7574ab4670914ecb18e169ac251b85ef"
LATEST_SHARED_MECHANISM_HEAD = "1ebed16db58f8edb8e3658eb94f693ce1a14223a"


def test_bocd_gamma_poisson_l2_is_frozen_and_consumed_once() -> None:
    ladder = json.loads(LADDER_PATH.read_text(encoding="utf-8"))
    candidate = next(
        row for row in ladder["initial_candidate_queue"] if row["id"] == TASK_ID
    )
    evidence = candidate["activation_evidence"]

    assert candidate["level"] == "L2"
    assert candidate["family"] == "bayesian_online_changepoint_gamma_poisson"
    assert candidate["status"] == "consumed_scored"
    assert candidate["activation_status"].startswith("fresh_live_v1_consumed_")
    assert candidate["gold_bundle_id"] == (
        "research-l2-bocd-gamma-poisson-20260828-v1"
    )
    assert evidence["activation_schema_version"] == 4
    assert evidence["semantic_protocol_version"] == 8
    assert evidence["semantic_calibration_attempts"] == 1
    assert evidence["semantic_calibration_total_model_calls"] == 7
    assert evidence["semantic_calibration_cases_correct"] == 5
    assert evidence["semantic_candidate_mode_negative_cases_correct"] == 1
    assert evidence["semantic_reference_candidate_passed"] is True
    assert evidence["semantic_calibration_model"] == (
        "claude-haiku-4-5-20251001"
    )
    assert evidence["activation_reference_tasks_passed"] == 1
    assert evidence["activation_negative_controls_rejected"] == 4
    assert evidence["activation_semantic_model_calls"] == 0
    assert evidence["hidden_gold_manifest_validated"] is True
    assert evidence["gold_frozen_before_first_runtime_model_call"] is True
    assert evidence["preactivation_product_model_calls"] == 0
    assert evidence["first_runtime_model_call_occurred"] is True
    assert evidence["fresh_live_runs"] == 1
    assert evidence["runtime_status"] == "BLOCKED"
    assert evidence["runtime_research_eval_complete"] == "0/1"
    assert evidence["hidden_full_task_result"] == "0/1"
    assert evidence["enabled_model"] == "claude-haiku-4-5-20251001"
    assert evidence["enabled_sonnet_calls"] == 0
    assert evidence["enabled_opus_calls"] == 0
    assert evidence["hidden_theory_mechanical_checks"] == "7/7"
    assert evidence["hidden_theory_semantic_candidate_status"] == "PASS"
    assert evidence["operator_theory_disposition"].startswith("INVALIDATED_")
    assert evidence["hidden_algorithm_checks"] == "4/8"
    assert evidence["hidden_empirical_checks"] == "5/8"
    assert evidence["post_run_shared_mechanism_commit"] == (
        TASK_76_SHARED_MECHANISM_HEAD
    )
    assert "1001/1001" in evidence["post_run_regression_evidence"]
    assert evidence["formalization_requirement"] == "not_applicable"
    assert evidence["formalizer_executed"] is False
    assert evidence["trusted_capability_credit"] is False
    assert evidence["full_task_passed"] is False
    assert evidence["ladder_score_after_consumption"] == "4/76"
    assert "consumed and immutable" in evidence["boundary"]

    run_path = Path(evidence["immutable_run_path"])
    run_hashes = {
        "research_agent_runtime_manifest.json": evidence[
            "runtime_manifest_sha256"
        ],
        "bayesian_online_changepoint_gamma_poisson_paper_to_code_runtime_result.json": evidence[
            "runtime_result_sha256"
        ],
        "research_capability_gold_evaluation.json": evidence[
            "hidden_gold_evaluation_sha256"
        ],
        "runtime_llm_topology.json": evidence["runtime_llm_topology_sha256"],
        "runtime_evidence_ledger.jsonl": evidence[
            "runtime_evidence_ledger_sha256"
        ],
        "runtime_failure_summary.json": evidence[
            "runtime_failure_summary_sha256"
        ],
        "runtime_completion_summary.json": evidence[
            "runtime_completion_summary_sha256"
        ],
        "runtime_progress.jsonl": evidence["runtime_progress_sha256"],
        "runtime_traces.jsonl": evidence["runtime_traces_sha256"],
    }
    for filename, expected_sha256 in run_hashes.items():
        assert hashlib.sha256((run_path / filename).read_bytes()).hexdigest() == (
            expected_sha256
        )
    assert Path(evidence["operator_audit_path"]).is_file()

    visible_path = Path(candidate["visible_questions_path"])
    assert hashlib.sha256(visible_path.read_bytes()).hexdigest() == (
        evidence["visible_questions_sha256"]
    )
    question = json.loads(visible_path.read_text(encoding="utf-8"))["questions"][0]
    assert question["id"] == candidate["id"]
    assert question["task_intent"] == candidate["task_intent"]
    assert question["task_intent"]["formal"] == "not_applicable"
    assert question["source"]["research_source_snapshot_hash"] == (
        evidence["source_snapshot_hash"]
    )

    runtime_visible = json.dumps(
        {"candidate": candidate, "question": question}, sort_keys=True
    )
    for hidden_name in (
        "gold_manifest.json",
        "hidden_algorithm_harness.py",
        "hidden_empirical_harness.py",
        "hidden_theory_harness.py",
        "semantic_reference.md",
        "semantic_rubric.json",
    ):
        assert hidden_name not in runtime_visible

    readiness = ladder["current_readiness"]
    assert readiness["active_scored_tasks"] == 81
    assert readiness["consumed_scored_tasks"] == 80
    assert readiness["fully_gold_configured_tasks"] == 81
    assert readiness["fully_gold_passed_tasks"] == 4
    assert readiness["latest_shared_mechanism_head"] == (
        LATEST_SHARED_MECHANISM_HEAD
    )
