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
    validate_research_gold_benchmark_manifest,
)
from ai_statistician.research_schema import load_open_research_questions


VISIBLE_PATH = Path(
    "benchmarks/research_l0_dirichlet_multinomial_predictive_questions_20260830.json"
)
LEDGER_PATH = Path(
    "docs/evaluation_activations/task110_dirichlet_multinomial_predictive_preactivation.json"
)
GOLD_ROOT = Path(
    "/Users/yukangzengcmac/.codex/evaluator_authority/AI-Statistician/"
    "research-l0-dirichlet-multinomial-predictive-20260830-v1"
)
GOLD_MANIFEST = GOLD_ROOT / "gold_manifest.json"
TASK_ID = "dirichlet_multinomial_posterior_predictive_known_result"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_task110_is_frozen_and_qualified_before_its_only_product_draw() -> None:
    ledger = json.loads(LEDGER_PATH.read_text(encoding="utf-8"))
    visible_payload = json.loads(VISIBLE_PATH.read_text(encoding="utf-8"))
    visible_question = visible_payload["questions"][0]
    loaded_question = load_open_research_questions(VISIBLE_PATH)[0]
    descriptor = validate_research_gold_benchmark_manifest(GOLD_MANIFEST)

    assert ledger["status"] == "frozen_qualified_pre_first_product_call"
    assert ledger["family"] == (
        "bayesian_categorical_dirichlet_multinomial_prediction"
    )
    assert ledger["harness_mechanism_commit"] == (
        "94f18d2f949312f67b3d1c77cbbb6bbf237172d3"
    )
    assert ledger["visible_question_commit"] == (
        "c098167a62a784000332e21262895d3874a77f10"
    )
    assert loaded_question.id == TASK_ID
    assert loaded_question.task_intent == {
        "source_replication": "not_applicable",
        "theory": "required",
        "scientific_code": "required",
        "empirical": "required",
        "formal": "not_applicable",
        "novelty": "not_applicable",
        "unresolved_gaps": "required",
    }
    assert visible_question["source"]["primary_authority"].endswith(
        "10.1093/biomet/49.1-2.65"
    )
    assert "estimator_execution_contract" in visible_question
    assert "formal_target_contract" not in visible_question

    assert _sha256(VISIBLE_PATH) == ledger["visible_questions_sha256"]
    assert stable_hash(visible_payload) == ledger["visible_question_full_hash"]
    assert stable_hash(_visible_question_hash_payload(visible_question)) == ledger[
        "runtime_visible_question_hash"
    ]
    assert frozen_estimator_execution_contract_id(
        visible_question["estimator_execution_contract"]
    ) == ledger["estimator_execution_contract_id"]
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
        "algorithm_authority_checks_passed": "10/10",
        "algorithm_valid_cases_passed": "24/24",
        "algorithm_invalid_cases_rejected": "34/34",
        "empirical_authority_checks_passed": "13/13",
        "empirical_designs_passed": "3/3",
        "empirical_replicates_per_design": 4000,
        "activation_reference_tasks_passed": "1/1",
        "activation_negative_evaluator_controls_rejected": "5/5",
    }
    semantic = ledger["semantic_qualification"]
    assert semantic["protocol_version"] == 11
    assert semantic["candidate_adjudication_strategy"] == (
        "integrated_plus_adversarial"
    )
    assert semantic["model"] == "claude-haiku-4-5-20251001"
    assert semantic["model_calls"] == 16
    assert semantic["calibration_cases_correct"] == "6/6"
    assert semantic["candidate_mode_negative_cases_correct"] == "1/1"
    assert semantic["reference_claims_satisfied"] == "8/8"

    policy = ledger["single_draw_policy"]
    assert policy["product_model"] == "claude-haiku-4-5-20251001"
    assert policy["automatic_tier_escalation_allowed"] is False
    assert policy["sonnet_allowed"] is False
    assert policy["opus_allowed"] is False
    assert policy["fresh_product_draws"] == 1
    assert policy["post_runtime_assessments"] == 1
    assert policy["resume_or_rerun_allowed"] is False
    assert ledger["formalization_requirement"] == "not_applicable"
