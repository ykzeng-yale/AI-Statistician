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


LADDER_PATH = Path("benchmarks/research_capability_ladder_20260814.json")
VISIBLE_PATH = Path(
    "benchmarks/research_l3_scalar_mean_empirical_likelihood_questions_20260829.json"
)
GOLD_MANIFEST = Path(
    "/Users/yukangzengcmac/.codex/evaluator_authority/AI-Statistician/"
    "research-l3-scalar-mean-empirical-likelihood-20260829-v1/gold_manifest.json"
)
TASK_ID = "scalar_mean_empirical_likelihood_known_theory_rederivation"


def test_scalar_mean_empirical_likelihood_task101_is_frozen_before_use() -> None:
    ladder = json.loads(LADDER_PATH.read_text(encoding="utf-8"))
    candidate = next(
        row for row in ladder["initial_candidate_queue"] if row["id"] == TASK_ID
    )
    evidence = candidate["activation_evidence"]
    visible_payload = json.loads(VISIBLE_PATH.read_text(encoding="utf-8"))
    visible_question = visible_payload["questions"][0]
    loaded_question = load_open_research_questions(VISIBLE_PATH)[0]
    descriptor = validate_research_gold_benchmark_manifest(GOLD_MANIFEST)

    assert candidate["level"] == "L3"
    assert candidate["family"] == "scalar_mean_empirical_likelihood_inference"
    assert candidate["status"] == "active_scored"
    assert candidate["activation_status"] == (
        "preactivated_schema_v4_exact_haiku_ready_for_single_fresh_live_draw"
    )
    assert loaded_question.id == TASK_ID
    assert loaded_question.task_intent == candidate["task_intent"]
    assert candidate["task_intent"] == {
        "source_replication": "not_applicable",
        "theory": "required",
        "scientific_code": "required",
        "empirical": "required",
        "formal": "not_applicable",
        "novelty": "not_applicable",
        "unresolved_gaps": "required",
    }

    assert hashlib.sha256(VISIBLE_PATH.read_bytes()).hexdigest() == (
        evidence["visible_questions_sha256"]
    )
    assert stable_hash(visible_payload) == evidence["visible_question_full_hash"]
    assert stable_hash(_visible_question_hash_payload(visible_question)) == (
        evidence["runtime_visible_question_hash"]
    )
    assert frozen_estimator_execution_contract_id(
        visible_question["estimator_execution_contract"]
    ) == evidence["estimator_execution_contract_id"]

    assert hashlib.sha256(GOLD_MANIFEST.read_bytes()).hexdigest() == (
        candidate["gold_manifest_sha256"]
    )
    assert candidate["gold_manifest_sha256"] == evidence[
        "gold_manifest_file_sha256"
    ]
    assert descriptor["benchmark_manifest_hash"] == candidate[
        "gold_descriptor_hash"
    ]
    assert candidate["gold_descriptor_hash"] == evidence[
        "gold_manifest_stable_hash"
    ]
    assert descriptor["active_task_ids"] == [TASK_ID]

    assert evidence["activation_schema_version"] == 4
    assert evidence["algorithm_authority_checks_correct"] == "16/16"
    assert evidence["algorithm_reference_valid_cases"] == 8
    assert evidence["algorithm_reference_invalid_cases"] == 24
    assert evidence["empirical_authority_checks_correct"] == "10/10"
    assert evidence["empirical_reference_designs"] == 3
    assert evidence["empirical_reference_replicates_per_design"] == 2000
    assert evidence["empirical_reference_total_estimator_invocations"] == 6000
    assert evidence["semantic_protocol_version"] == 11
    assert evidence["semantic_candidate_adjudication_strategy"] == (
        "integrated_plus_adversarial"
    )
    assert evidence["semantic_calibration_cases_correct"] == "6/6"
    assert evidence["semantic_candidate_mode_negative_cases_correct"] == "1/1"
    assert evidence["semantic_successful_qualification_model_calls"] == 16
    assert evidence["semantic_calibration_model"] == "claude-haiku-4-5-20251001"
    assert evidence["activation_reference_tasks_passed"] == 1
    assert evidence["activation_negative_controls_rejected"] == 4
    assert evidence["activation_semantic_reference_documents_passed"] == 1
    assert (
        evidence[
            "activation_semantic_candidate_mode_negative_controls_rejected"
        ]
        == 1
    )

    assert evidence["hidden_gold_manifest_validated"] is True
    assert evidence["gold_frozen_before_first_runtime_model_call"] is True
    assert evidence["preactivation_product_model_calls"] == 0
    assert evidence["preactivation_evaluator_model_calls"] == 16
    assert evidence["activation_push_required_before_first_runtime_model_call"] is True
    assert evidence["activation_ledger_commit"] == (
        "22673253fad6adeaf5578cd34753b73ab00860e7"
    )
    assert evidence["activation_push_confirmed_on_work_branch_and_main"] is True
    assert evidence["codex_harness_mechanism_head"] == (
        "22673253fad6adeaf5578cd34753b73ab00860e7"
    )
    assert evidence["official_codex_checkout_head"] == (
        "6478a751fde8884b2fdc76486fe23175a8e795d4"
    )
    assert evidence["first_runtime_model_call_occurred"] is False
    assert evidence["fresh_live_runs"] == 0
    assert evidence["runtime_invocations"] == 0
    assert evidence["single_fresh_draw_only"] is True
    assert evidence["runtime_model"] == "claude-haiku-4-5-20251001"
    assert evidence["sonnet_product_calls"] == 0
    assert evidence["opus_product_calls"] == 0
    assert evidence["formalization_requirement"] == "not_applicable"
    assert evidence["formalizer_executed"] is False
    assert evidence["trusted_capability_credit"] is False

    readiness = ladder["current_readiness"]
    assert readiness["scored_tasks_total"] == 101
    assert readiness["unconsumed_scored_tasks"] == 1
    assert readiness["consumed_scored_tasks"] == 100
    assert readiness["fully_gold_configured_tasks"] == 101
    assert readiness["fully_gold_passed_tasks"] == 7

    runtime_visible = json.dumps(
        {"candidate": candidate, "question": visible_question}, sort_keys=True
    )
    for hidden_path in (
        str(GOLD_MANIFEST),
        "reference_estimator.R",
        "semantic_reference.md",
        "candidate_mode_near_miss.md",
    ):
        assert hidden_path not in runtime_visible
