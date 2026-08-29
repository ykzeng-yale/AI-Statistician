from __future__ import annotations

import hashlib
import json
from pathlib import Path


LADDER_PATH = Path("benchmarks/research_capability_ladder_20260814.json")
TASK_ID = "pingouin_joss_rmcorr_public_replication"


def test_pingouin_rmcorr_l1_provider_environment_failure_is_consumed() -> None:
    ladder = json.loads(LADDER_PATH.read_text(encoding="utf-8"))
    candidate = next(
        row for row in ladder["initial_candidate_queue"] if row["id"] == TASK_ID
    )
    evidence = candidate["activation_evidence"]

    assert candidate["level"] == "L1"
    assert candidate["family"] == "repeated_measures_correlation_source_replication"
    assert candidate["status"] == "consumed_scored"
    assert candidate["activation_status"].startswith("fresh_live_v1_consumed_")
    assert candidate["gold_bundle_id"] == (
        "research-l1-pingouin-joss-rmcorr-20260828-v1"
    )
    assert evidence["activation_schema_version"] == 4
    assert evidence["source_harness_calibration_cases_correct"] == 12
    assert evidence["independent_source_reruns"].startswith("3/3")
    assert evidence["semantic_protocol_version"] == 10
    assert evidence["semantic_final_calibration_cases_correct"] == 8
    assert evidence["semantic_candidate_mode_negative_cases_correct"] == 1
    assert evidence["semantic_reference_candidate_passed"] is True
    assert evidence["semantic_calibration_model"] == (
        "claude-haiku-4-5-20251001"
    )
    assert evidence["activation_semantic_reference_documents_passed"] == 1
    assert (
        evidence[
            "activation_semantic_candidate_mode_negative_controls_rejected"
        ]
        == 1
    )
    assert evidence["activation_semantic_model_calls"] == 0
    assert evidence["activation_semantic_qualification_reused"] is True
    assert evidence["hidden_gold_manifest_validated"] is True
    assert evidence["gold_frozen_before_first_runtime_model_call"] is True
    assert evidence["preactivation_product_model_calls"] == 0
    assert evidence["first_runtime_model_call_occurred"] is False
    assert evidence["fresh_live_runs"] == 1
    assert evidence["runtime_invocations"] == 1
    assert evidence["runtime_status"] == "FAILED"
    assert evidence["runtime_terminal_subsystem"] == "ArchitectCoordinator"
    assert evidence["runtime_product_model_calls"] == 0
    assert evidence["runtime_outer_graph_iterations"] == 1
    assert evidence["runtime_same_owner_workspace_continuations"] == 0
    assert evidence["runtime_llm_topology_policy_ok"] is True
    assert evidence["post_runtime_hidden_assessment_reports"] == 1
    assert evidence["hidden_gold_tasks_evaluated"] == 0
    assert evidence["hidden_source_harness_execution_attempted"] is False
    assert evidence["hidden_source_semantic_execution_attempted"] is False
    assert evidence["trusted_capability_credit"] is False
    assert evidence["full_task_passed"] is False
    assert evidence["ladder_score_after_consumption"] == "4/83"
    assert evidence["post_run_shared_mechanism_commit"] == (
        "05d64366ede9186b466e11b84d413b6e6788bf7a"
    )
    assert evidence["post_run_score_changed"] is False
    assert evidence["formalization_requirement"] == "not_applicable"
    assert evidence["formalizer_executed"] is False

    visible_path = Path(candidate["visible_questions_path"])
    assert hashlib.sha256(visible_path.read_bytes()).hexdigest() == (
        evidence["visible_questions_sha256"]
    )
    question = json.loads(visible_path.read_text(encoding="utf-8"))["questions"][0]
    assert question["id"] == TASK_ID
    assert question["task_intent"] == candidate["task_intent"]
    assert question["source"]["research_source_snapshot_hash"] == (
        candidate["source_snapshot_hash"]
    )

    runtime_visible = json.dumps(
        {"candidate": candidate, "question": question}, sort_keys=True
    )
    for hidden_name in (
        "gold_manifest.json",
        "hidden_source_replication_harness.py",
        "semantic_reference.md",
        "semantic_rubric.json",
        "candidate_mode_near_miss.md",
    ):
        assert hidden_name not in runtime_visible

    readiness = ladder["current_readiness"]
    assert readiness["scored_tasks_total"] == 91
    assert readiness["unconsumed_scored_tasks"] == 0
    assert readiness["consumed_scored_tasks"] == 91
    assert readiness["fully_gold_configured_tasks"] == 91
    assert readiness["fully_gold_passed_tasks"] == 6
    assert readiness["latest_shared_mechanism_head"] == (
        "63b527e54d9b5e4df4ea63a19827c8e817e688ab"
    )
