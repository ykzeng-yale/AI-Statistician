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
from ai_statistician.research_source_library import load_research_source_snapshot


LADDER_PATH = Path("benchmarks/research_capability_ladder_20260814.json")
VISIBLE_PATH = Path(
    "benchmarks/research_l2_lowess_local_linear_questions_20260829.json"
)
SOURCE_MANIFEST = Path(
    "benchmarks/research_sources/lowess_local_linear_20260829/source_manifest.json"
)
GOLD_MANIFEST = Path(
    "/Users/yukangzengcmac/.codex/evaluator_authority/AI-Statistician/"
    "research-l2-lowess-local-linear-20260829-v1/gold_manifest.json"
)
TASK_ID = "lowess_local_linear_nonrobust_paper_to_code"


def test_lowess_task103_is_frozen_before_its_only_product_draw() -> None:
    ladder = json.loads(LADDER_PATH.read_text(encoding="utf-8"))
    candidate = next(
        row for row in ladder["initial_candidate_queue"] if row["id"] == TASK_ID
    )
    evidence = candidate["activation_evidence"]
    visible_payload = json.loads(VISIBLE_PATH.read_text(encoding="utf-8"))
    visible_question = visible_payload["questions"][0]
    loaded_question = load_open_research_questions(VISIBLE_PATH)[0]
    source = load_research_source_snapshot(SOURCE_MANIFEST)
    descriptor = validate_research_gold_benchmark_manifest(GOLD_MANIFEST)

    assert TASK_ID not in {
        row["id"] for row in ladder["evidence_dimensions"]
    }
    assert candidate["level"] == "L2"
    assert candidate["family"] == "nonparametric_local_linear_smoothing"
    assert candidate["status"] == "active_scored"
    assert candidate["activation_status"] == (
        "frozen_ready_schema_v4_exact_haiku_single_draw"
    )
    assert loaded_question.id == TASK_ID
    assert loaded_question.task_intent == candidate["task_intent"]
    assert candidate["task_intent"] == {
        "source_replication": "not_applicable",
        "theory": "not_applicable",
        "scientific_code": "required",
        "empirical": "not_applicable",
        "formal": "not_applicable",
        "novelty": "not_applicable",
        "unresolved_gaps": "required",
    }

    assert hashlib.sha256(VISIBLE_PATH.read_bytes()).hexdigest() == evidence[
        "visible_questions_sha256"
    ]
    assert stable_hash(visible_question) == evidence["visible_question_full_hash"]
    assert stable_hash(_visible_question_hash_payload(visible_question)) == evidence[
        "runtime_visible_question_hash"
    ]
    assert frozen_estimator_execution_contract_id(
        visible_question["estimator_execution_contract"]
    ) == evidence["estimator_execution_contract_id"]

    assert source.snapshot_hash == candidate["source_snapshot_hash"]
    assert source.manifest_sha256 == candidate["source_manifest_sha256"]
    assert len(source.documents) == 2
    assert {document.source_kind for document in source.documents} == {
        "paper_method_index",
        "public_replication_data",
    }

    assert hashlib.sha256(GOLD_MANIFEST.read_bytes()).hexdigest() == candidate[
        "gold_manifest_sha256"
    ]
    assert descriptor["benchmark_manifest_hash"] == candidate[
        "gold_descriptor_hash"
    ]
    assert descriptor["active_task_ids"] == [TASK_ID]
    assert descriptor["n_full_task_gold_configured"] == 1

    assert evidence["activation_schema_version"] == 4
    assert evidence["algorithm_authority_checks_correct"] == "13/13"
    assert evidence["algorithm_reference_valid_cases"] == 6
    assert evidence["algorithm_reference_invalid_cases"] == 22
    assert evidence["algorithm_behavioral_negative_candidates_rejected"] == 3
    assert evidence["statsmodels_implementation_version"] == "0.14.6"
    assert evidence["statsmodels_implementation_commit"] == (
        "40e6a84d26ac74623c6b94b718f0987ef0351c53"
    )
    assert evidence["statsmodels_parity_cases_correct"] == "5/5"
    assert evidence["statsmodels_parity_maximum_absolute_error"] < 3.6e-15
    assert evidence["activation_reference_tasks_passed"] == 1
    assert evidence["activation_negative_controls_rejected"] == 3
    assert evidence["activation_semantic_model_calls"] == 0
    assert evidence["hidden_gold_manifest_validated"] is True
    assert evidence["gold_frozen_before_first_runtime_model_call"] is True
    assert evidence["preactivation_product_model_calls"] == 0
    assert evidence["preactivation_evaluator_model_calls"] == 0
    assert evidence["first_runtime_model_call_occurred"] is False
    assert evidence["fresh_live_runs"] == 0
    assert evidence["runtime_invocations"] == 0
    assert evidence["activation_push_required_before_first_runtime_model_call"] is True
    assert evidence["activation_ledger_commit"] == "pending_activation_commit"
    assert evidence["activation_push_confirmed_on_work_branch_and_main"] is False
    assert evidence["single_fresh_draw_only"] is True
    assert evidence["runtime_model"] == "claude-haiku-4-5-20251001"
    assert evidence["sonnet_product_calls"] == 0
    assert evidence["opus_product_calls"] == 0
    assert evidence["formalization_requirement"] == "not_applicable"
    assert evidence["formalizer_executed"] is False
    assert evidence["model_draw_resampling_blocked"] is True

    runtime_visible = json.dumps(
        {"candidate": candidate, "question": visible_question}, sort_keys=True
    )
    for hidden_name in (
        str(GOLD_MANIFEST),
        "reference_estimator.py",
        "hidden_algorithm_harness.py",
        "statsmodels_parity_record.json",
        "negative_global_linear.py",
        "negative_local_constant.py",
        "negative_all_points.py",
    ):
        assert hidden_name not in runtime_visible

    readiness = ladder["current_readiness"]
    assert readiness["scored_tasks_total"] == 103
    assert readiness["unconsumed_scored_tasks"] == 1
    assert readiness["consumed_scored_tasks"] == 102
    assert readiness["fully_gold_configured_tasks"] == 103
    assert readiness["fully_gold_passed_tasks"] == 7
