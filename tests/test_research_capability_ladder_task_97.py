from __future__ import annotations

import hashlib
import json
from pathlib import Path

from ai_statistician.fingerprint import stable_hash
from ai_statistician.research_gold_evaluation import _visible_question_hash_payload
from ai_statistician.research_source_library import (
    load_research_source_execution_spec,
    load_research_source_snapshot,
)


LADDER_PATH = Path("benchmarks/research_capability_ladder_20260814.json")
TASK_ID = "betareg_jss_2010_r_public_replication"
VISIBLE_PATH = Path(
    "benchmarks/research_l1_betareg_jss_r_replication_questions_20260829.json"
)
SOURCE_ROOT = Path("benchmarks/research_sources/betareg_jss_2010_20260829")
ACTIVATION_COMMIT = "e5fefa191dc11182738e153f71559a314d52e18e"


def test_betareg_jss_r_l1_is_frozen_before_its_single_product_draw() -> None:
    ladder = json.loads(LADDER_PATH.read_text(encoding="utf-8"))
    candidate = next(
        row for row in ladder["initial_candidate_queue"] if row["id"] == TASK_ID
    )
    evidence = candidate["activation_evidence"]

    assert candidate["level"] == "L1"
    assert candidate["family"] == "beta_regression_r_source_replication"
    assert candidate["status"] == "active_scored"
    assert candidate["activation_status"] == (
        "frozen_ready_task_97_exact_jss_r_source_replication"
    )
    assert candidate["gold_bundle_id"] == (
        "research-l1-betareg-jss-2010-r-20260829-v1"
    )
    assert candidate["gold_manifest_sha256"] == (
        "e576934c66eb8ecd59a41fb36cfcc5134ea91748ad598c169f5ce5fd314817ff"
    )
    assert candidate["gold_descriptor_hash"] == (
        "b0cf12d80ec3a5184572dd7d65ee3ea548d625c8d52973b800cd6b6877010c2f"
    )
    assert evidence["visible_question_activation_commit"] == ACTIVATION_COMMIT
    assert evidence["activation_ledger_commit"] == ACTIVATION_COMMIT
    assert evidence["activation_push_confirmed_on_work_branch_and_main"] is True
    assert evidence["activation_schema_version"] == 4
    assert evidence["source_harness_calibration_cases"] == 14
    assert evidence["source_harness_calibration_cases_correct"] == 14
    assert evidence["independent_source_reruns"] == "3/3"
    assert evidence["raw_pdf_hash_identity_required"] is False
    assert evidence["semantic_protocol_version"] == 10
    assert evidence["semantic_activation_attempts"] == 3
    assert evidence["semantic_calibration_total_model_calls"] == 24
    assert evidence["semantic_successful_qualification_model_calls"] == 8
    assert evidence["semantic_calibration_cases"] == 6
    assert evidence["semantic_calibration_cases_correct"] == 6
    assert evidence["semantic_candidate_mode_negative_cases"] == 1
    assert evidence["semantic_candidate_mode_negative_cases_correct"] == 1
    assert evidence["semantic_reference_claims"] == 12
    assert evidence["semantic_reference_candidate_passed"] is True
    assert evidence["semantic_calibration_model"] == (
        "claude-haiku-4-5-20251001"
    )
    assert evidence["activation_semantic_model_calls"] == 0
    assert evidence["activation_semantic_qualification_reused"] is True
    assert evidence["hidden_gold_manifest_validated"] is True
    assert evidence["gold_frozen_before_first_runtime_model_call"] is True
    assert evidence["preactivation_product_model_calls"] == 0
    assert evidence["preactivation_evaluator_model_calls"] == 24
    assert evidence["first_runtime_model_call_occurred"] is False
    assert evidence["fresh_live_runs"] == 0
    assert evidence["runtime_invocations"] == 0
    assert evidence["formalization_requirement"] == "not_applicable"
    assert evidence["formalizer_executed"] is False
    assert evidence["model_draw_resampling_blocked"] is True
    assert evidence["full_task_passed"] is False
    assert evidence["trusted_capability_credit"] is False
    assert evidence["ladder_score_before_activation"] == "7/96"
    assert evidence["ladder_score_after_activation"] == "7/97"

    assert hashlib.sha256(VISIBLE_PATH.read_bytes()).hexdigest() == evidence[
        "visible_questions_sha256"
    ]
    question = json.loads(VISIBLE_PATH.read_text(encoding="utf-8"))["questions"][0]
    assert question["id"] == TASK_ID
    assert question["task_intent"] == candidate["task_intent"]
    assert question["task_intent"] == {
        "source_replication": "required",
        "theory": "not_applicable",
        "scientific_code": "not_applicable",
        "empirical": "not_applicable",
        "formal": "not_applicable",
        "novelty": "not_applicable",
        "unresolved_gaps": "required",
    }
    assert question["source"]["doi"] == "10.18637/jss.v034.i02"
    assert stable_hash(question) == evidence["visible_question_full_hash"]
    assert stable_hash(_visible_question_hash_payload(question)) == evidence[
        "runtime_visible_question_hash"
    ]

    snapshot = load_research_source_snapshot(SOURCE_ROOT / "source_manifest.json")
    assert snapshot.snapshot_id == candidate["source_snapshot_id"]
    assert snapshot.snapshot_hash == candidate["source_snapshot_hash"]
    assert snapshot.manifest_sha256 == candidate["source_manifest_sha256"]
    assert len(snapshot.documents) == 15
    assert snapshot.document("betareg-jss-official-r-example").sha256 == (
        "0725416e1d260a76acf2f27db9a028ee5cf8366a1bb766e3e8115c5b381de57d"
    )
    execution = load_research_source_execution_spec(
        SOURCE_ROOT / "source_execution_manifest.json",
        research_sources=snapshot,
    )
    assert execution.manifest_sha256 == evidence["source_execution_spec_sha256"]
    assert execution.runtime_language == "r"
    assert execution.arguments == ()
    assert execution.execution_workspace_mode == "staged_copy_on_write"
    assert execution.result_artifact_paths == ("Rplots.pdf",)

    runtime_visible = json.dumps(
        {"candidate": candidate, "question": question}, sort_keys=True
    )
    for hidden_identity in (
        "gold_manifest.json",
        "hidden_source_replication_harness.py",
        "semantic_reference.md",
        "semantic_rubric.json",
        "semantic_calibration_cases.json",
        "candidate_mode_near_miss.md",
        "candidate_mode_negative_cases.json",
    ):
        assert hidden_identity not in runtime_visible
    assert not Path(
        "benchmarks/evaluator_only/betareg_jss_2010_20260829"
    ).exists()

    readiness = ladder["current_readiness"]
    assert readiness["scored_tasks_total"] == 97
    assert readiness["unconsumed_scored_tasks"] == 1
    assert readiness["consumed_scored_tasks"] == 96
    assert readiness["fully_gold_configured_tasks"] == 97
    assert readiness["fully_gold_passed_tasks"] == 7
    assert readiness["runtime_source_replication_components_ready"] == 9
    active = [
        row
        for row in ladder["initial_candidate_queue"]
        if row["status"] == "active_scored"
    ]
    assert [row["id"] for row in active] == [TASK_ID]
