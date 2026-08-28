from __future__ import annotations

import hashlib
import json
from pathlib import Path


LADDER_PATH = Path("benchmarks/research_capability_ladder_20260814.json")
TASK_ID = "bayesian_online_changepoint_gamma_poisson_paper_to_code"
LATEST_SHARED_MECHANISM_HEAD = "89a82b282f56a395437b0f3703fb72416d7ecec6"


def test_bocd_gamma_poisson_l2_is_frozen_before_first_product_call() -> None:
    ladder = json.loads(LADDER_PATH.read_text(encoding="utf-8"))
    candidate = next(
        row for row in ladder["initial_candidate_queue"] if row["id"] == TASK_ID
    )
    evidence = candidate["activation_evidence"]

    assert candidate["level"] == "L2"
    assert candidate["family"] == "bayesian_online_changepoint_gamma_poisson"
    assert candidate["status"] == "active_scored"
    assert candidate["activation_status"].startswith("frozen_ready_")
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
    assert evidence["first_runtime_model_call_occurred"] is False
    assert evidence["fresh_live_runs"] == 0
    assert evidence["formalization_requirement"] == "not_applicable"
    assert evidence["formalizer_executed"] is False
    assert evidence["trusted_capability_credit"] is False

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
    assert readiness["active_scored_tasks"] == 76
    assert readiness["consumed_scored_tasks"] == 75
    assert readiness["fully_gold_configured_tasks"] == 76
    assert readiness["fully_gold_passed_tasks"] == 4
    assert readiness["latest_shared_mechanism_head"] == (
        LATEST_SHARED_MECHANISM_HEAD
    )
