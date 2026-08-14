from __future__ import annotations

import hashlib
import json
from pathlib import Path


LADDER_PATH = Path("benchmarks/research_capability_ladder_20260814.json")


def _load_ladder() -> dict:
    return json.loads(LADDER_PATH.read_text(encoding="utf-8"))


def test_research_ladder_separates_product_and_strict_formal_authority() -> None:
    ladder = _load_ladder()
    authority = ladder["authority_boundary"]

    assert authority["product_research_authority"] is True
    assert authority["strict_formal_protocol_unchanged"] is True
    assert authority["aggregate_score_may_override_required_dimension"] is False
    assert authority["open_problem_model_agreement_is_correctness_evidence"] is False
    assert Path(authority["strict_formal_capability_protocol"]).exists()


def test_research_ladder_has_progressive_evidence_and_no_fixed_replication_rule() -> None:
    ladder = _load_ladder()

    assert [level["id"] for level in ladder["levels"]] == [
        "L0",
        "L1",
        "L2",
        "L3",
        "L4",
        "L5",
        "L6",
    ]
    assert ladder["levels"][-1]["correctness_scored"] is False
    assert ladder["simulation_precision_contract"][
        "universal_fixed_replication_count"
    ] is None
    assert ladder["simulation_precision_contract"][
        "confirmatory_rule_frozen_before_outcomes"
    ] is True
    assert ladder["formalization_contract"]["optional_gap_blocks_nonformal_dimensions"] is False
    assert ladder["formalization_contract"]["nonproof_evidence_may_be_promoted_to_proof"] is False


def test_ladder_counts_fully_configured_active_tasks_without_embedding_gold() -> None:
    ladder = _load_ladder()
    candidates = ladder["initial_candidate_queue"]

    assert candidates
    active = [candidate for candidate in candidates if candidate["status"] == "active_scored"]
    pending = [
        candidate
        for candidate in candidates
        if candidate["status"].startswith("proposed_pending_")
    ]
    assert ladder["current_readiness"]["active_scored_tasks"] == len(active) == 2
    assert ladder["current_readiness"]["fully_gold_configured_tasks"] == 2
    assert ladder["current_readiness"]["fully_gold_passed_tasks"] == 0
    assert {candidate["id"] for candidate in active} == {
        "heteroskedastic_covariance_known_result",
        "kaplan_meier_greenwood_known_result",
    }
    for candidate in active:
        assert candidate["gold_runtime_visibility"] == "evaluator_only_after_runtime"
        assert candidate["activation_status"].startswith("full_task_gold_")
        assert Path(candidate["visible_questions_path"]).is_file()
        assert "gold_manifest" not in candidate
        assert candidate["gold_authority"] == (
            "operator_provisioned_outside_repository_and_model_workspace"
        )
        assert len(candidate["gold_manifest_sha256"]) == 64
    assert pending
    forbidden_keys = {
        "expected_answer",
        "expected_results",
        "theorem_statement",
        "proof",
        "reference_code",
    }
    assert all(forbidden_keys.isdisjoint(candidate) for candidate in candidates)
    assert all(candidate["level"] in {"L0", "L1", "L2"} for candidate in candidates)


def test_ladder_live_evaluation_policy_is_exact_haiku() -> None:
    model_policy = _load_ladder()["model_policy"]

    assert model_policy["live_evaluation_model"] == "claude-haiku-4-5-20251001"
    assert model_policy["live_evaluation_model_tier"] == "haiku"
    assert model_policy["sonnet_live_calls_allowed"] is False
    assert model_policy["opus_live_calls_allowed"] is False
    assert model_policy["automatic_tier_escalation_allowed"] is False


def test_doubleml_l1_freezes_exact_replication_without_conflating_l2() -> None:
    ladder = _load_ladder()
    candidate = next(
        row
        for row in ladder["initial_candidate_queue"]
        if row["id"] == "double_machine_learning_public_replication"
    )

    assert candidate["level"] == "L1"
    assert candidate["status"] == "proposed_pending_runtime_replication_lane"
    assert candidate["activation_evidence"]["fresh_live_runs"] == 0
    assert candidate["activation_evidence"][
        "runtime_source_replication_lane_available"
    ] is False
    assert candidate["task_intent"] == {
        "source_replication": "required",
        "theory": "optional",
        "scientific_code": "not_applicable",
        "empirical": "not_applicable",
        "formal": "not_applicable",
        "novelty": "not_applicable",
        "unresolved_gaps": "required",
    }
    visible_path = Path(candidate["visible_questions_path"])
    assert visible_path.is_file()
    assert hashlib.sha256(visible_path.read_bytes()).hexdigest() == (
        candidate["activation_evidence"]["visible_questions_sha256"]
    )
    assert len(candidate["source_snapshot_hash"]) == 64
    assert len(candidate["source_manifest_sha256"]) == 64
    assert len(candidate["gold_manifest_sha256"]) == 64
