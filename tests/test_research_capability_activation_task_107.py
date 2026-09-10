from __future__ import annotations

import hashlib
import json
from pathlib import Path

from ai_statistician.fingerprint import stable_hash
from ai_statistician.research_gold_evaluation import (
    _visible_question_hash_payload,
    validate_research_gold_benchmark_manifest,
)
from ai_statistician.research_schema import load_open_research_questions


VISIBLE_PATH = Path("benchmarks/research_l3_stein_sure_questions_20260829.json")
LEDGER_PATH = Path(
    "docs/evaluation_activations/task107_stein_sure_preactivation.json"
)
GOLD_ROOT = Path(
    "/Users/yukangzengcmac/.codex/evaluator_authority/AI-Statistician/"
    "research-l3-stein-sure-theory-20260829-v1"
)
GOLD_MANIFEST = GOLD_ROOT / "gold_manifest.json"
TASK_ID = "gaussian_stein_sure_james_stein_known_theory_rederivation"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_task107_is_frozen_and_qualified_before_its_only_product_draw() -> None:
    ledger = json.loads(LEDGER_PATH.read_text(encoding="utf-8"))
    visible_payload = json.loads(VISIBLE_PATH.read_text(encoding="utf-8"))
    visible_question = visible_payload["questions"][0]
    loaded_question = load_open_research_questions(VISIBLE_PATH)[0]
    descriptor = validate_research_gold_benchmark_manifest(GOLD_MANIFEST)
    # Historical evidence is inspected, never reactivated by the current judge.
    qualification = json.loads(
        (GOLD_ROOT / "semantic_activation_attempt_1_protocol_v11.json").read_text(encoding="utf-8")
    )["judgment"]

    assert ledger["status"] == "frozen_qualified_pre_first_product_call"
    assert ledger["family"] == "gaussian_stein_unbiased_risk_estimation"
    assert ledger["harness_mechanism_commit"] == (
        "3f21792407ce8b575399db2ffe85090217f8d36e"
    )
    assert loaded_question.id == TASK_ID
    assert loaded_question.task_intent == {
        "source_replication": "not_applicable",
        "theory": "required",
        "scientific_code": "not_applicable",
        "empirical": "not_applicable",
        "formal": "not_applicable",
        "novelty": "not_applicable",
        "unresolved_gaps": "required",
    }
    assert visible_question["source"]["doi"] == "10.1214/aos/1176345632"
    assert "estimator_execution_contract" not in visible_question
    assert "formal_target_contract" not in visible_question

    assert _sha256(VISIBLE_PATH) == ledger["visible_questions_sha256"]
    assert stable_hash(visible_payload) == ledger["visible_question_full_hash"]
    assert stable_hash(_visible_question_hash_payload(visible_question)) == ledger[
        "runtime_visible_question_hash"
    ]
    assert _sha256(GOLD_MANIFEST) == ledger["gold_manifest_sha256"]
    assert descriptor["benchmark_manifest_hash"] == ledger[
        "gold_manifest_stable_hash"
    ]
    assert descriptor["active_task_ids"] == [TASK_ID]
    assert descriptor["n_full_task_gold_configured"] == 1

    for name, expected in ledger["hidden_artifact_sha256"].items():
        assert _sha256(GOLD_ROOT / name) == expected

    assert ledger["preactivation_product_model_calls"] == 0
    assert ledger["preactivation_evaluator_model_calls"] == 16
    assert ledger["mechanical_qualification"] == {
        "reference_checks_passed": "7/7",
        "negative_variants_rejected": "7/7",
    }
    assert ledger["semantic_qualification"]["protocol_version"] == 11
    assert ledger["semantic_qualification"]["model"] == (
        "claude-haiku-4-5-20251001"
    )
    assert ledger["semantic_qualification"]["model_calls"] == 16
    assert ledger["semantic_qualification"]["calibration_cases_correct"] == "6/6"
    assert ledger["semantic_qualification"][
        "candidate_mode_negative_cases_correct"
    ] == "1/1"
    assert ledger["semantic_qualification"]["reference_claims_satisfied"] == "8/8"

    assert qualification["protocol_version"] == 11
    assert qualification["passed"] is True
    assert qualification["n_model_calls"] == 16
    assert qualification["n_calibration_cases_correct"] == 6
    assert qualification["n_candidate_mode_negative_cases_correct"] == 1
    assert qualification["candidate_claim_status_counts"] == {
        "SATISFIED": 8, "VIOLATED": 0, "INCONCLUSIVE": 0,
    }

    policy = ledger["single_draw_policy"]
    assert policy["product_model"] == "claude-haiku-4-5-20251001"
    assert policy["automatic_tier_escalation_allowed"] is False
    assert policy["sonnet_allowed"] is False
    assert policy["opus_allowed"] is False
    assert policy["fresh_product_draws"] == 1
    assert policy["post_runtime_assessments"] == 1
    assert policy["resume_or_rerun_allowed"] is False
    assert ledger["formalization_requirement"] == "not_applicable"
