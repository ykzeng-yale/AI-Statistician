from __future__ import annotations

import hashlib
import json
from pathlib import Path

from ai_statistician.fingerprint import stable_hash
from ai_statistician.research_gold_evaluation import (
    _visible_question_hash_payload,
    validate_research_gold_benchmark_activation,
    validate_research_gold_benchmark_manifest,
)
from ai_statistician.research_schema import load_open_research_questions


VISIBLE_PATH = Path(
    "benchmarks/research_l3_bahadur_quantile_questions_20260829.json"
)
LEDGER_PATH = Path(
    "docs/evaluation_activations/task108_bahadur_quantile_preactivation.json"
)
GOLD_ROOT = Path(
    "/Users/yukangzengcmac/.codex/evaluator_authority/AI-Statistician/"
    "research-l3-bahadur-quantile-theory-20260829-v1"
)
GOLD_MANIFEST = GOLD_ROOT / "gold_manifest.json"
TASK_ID = "iid_sample_quantile_bahadur_known_theory_rederivation"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_task108_is_frozen_and_qualified_before_its_only_product_draw() -> None:
    ledger = json.loads(LEDGER_PATH.read_text(encoding="utf-8"))
    visible_payload = json.loads(VISIBLE_PATH.read_text(encoding="utf-8"))
    visible_question = visible_payload["questions"][0]
    loaded_question = load_open_research_questions(VISIBLE_PATH)[0]
    descriptor = validate_research_gold_benchmark_manifest(GOLD_MANIFEST)
    activation = validate_research_gold_benchmark_activation(
        GOLD_MANIFEST,
        visible_questions={TASK_ID: visible_question},
    )

    assert ledger["status"] == "frozen_qualified_pre_first_product_call"
    assert ledger["family"] == "iid_quantile_asymptotic_linearity"
    assert ledger["harness_mechanism_commit"] == (
        "a27af9794f4dbccb089a8063c3a42edb0d509084"
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
    assert visible_question["source"]["doi"] == "10.1214/aoms/1177699450"
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

    assert activation["activation_semantic_reference_documents_passed"] == 1
    assert activation[
        "activation_semantic_candidate_mode_negative_controls_rejected"
    ] == 1
    assert activation["activation_semantic_model_calls"] == 0
    assert activation["activation_semantic_qualification_model_calls"] == 16
    assert activation["activation_semantic_qualification_reused"] is True

    policy = ledger["single_draw_policy"]
    assert policy["product_model"] == "claude-haiku-4-5-20251001"
    assert policy["automatic_tier_escalation_allowed"] is False
    assert policy["sonnet_allowed"] is False
    assert policy["opus_allowed"] is False
    assert policy["fresh_product_draws"] == 1
    assert policy["post_runtime_assessments"] == 1
    assert policy["resume_or_rerun_allowed"] is False
    assert ledger["formalization_requirement"] == "not_applicable"
