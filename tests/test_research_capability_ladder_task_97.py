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


def test_betareg_jss_r_l1_consumed_result_is_immutable() -> None:
    ladder = json.loads(LADDER_PATH.read_text(encoding="utf-8"))
    candidate = next(
        row for row in ladder["initial_candidate_queue"] if row["id"] == TASK_ID
    )
    evidence = candidate["activation_evidence"]

    assert candidate["level"] == "L1"
    assert candidate["family"] == "beta_regression_r_source_replication"
    assert candidate["status"] == "consumed_scored"
    assert candidate["activation_status"] == (
        "fresh_live_v1_consumed_exact_haiku_runtime_accepted_automated_"
        "gold_pass_operator_failed"
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
    assert evidence["first_runtime_model_call_occurred"] is True
    assert evidence["fresh_live_runs"] == 1
    assert evidence["runtime_invocations"] == 1
    assert evidence["product_code_head"] == (
        "708fe0f359056a353edad5ee1b6059e313fd95c0"
    )
    assert evidence["runtime_status"] == "ACCEPTED"
    assert evidence["runtime_outer_graph_iterations"] == 1
    assert evidence["runtime_trace_steps"] == 1
    assert evidence["runtime_same_owner_workspace_continuations"] == 0
    assert evidence["runtime_product_model_calls"] == 17
    assert evidence["runtime_client_tool_model_turns"] == 17
    assert evidence["runtime_direct_model_calls"] == 0
    assert evidence["runtime_client_tool_executions"] == 21
    assert evidence["runtime_model_calls_by_subsystem"] == {
        "TheoryDeveloper": 17
    }
    assert evidence["sonnet_product_calls"] == 0
    assert evidence["opus_product_calls"] == 0
    assert evidence["formalization_requirement"] == "not_applicable"
    assert evidence["formalizer_executed"] is False
    assert evidence["architect_executed"] is False
    assert evidence["algorithm_engineer_executed"] is False
    assert evidence["simulation_engineer_executed"] is False
    assert evidence["model_draw_resampling_blocked"] is True
    assert evidence["source_replication_execution_passed"] is True
    assert evidence["source_replication_component_passed"] is True
    assert evidence["automated_gold_tasks_passed"] == 1
    assert evidence["automated_gold_tasks_total"] == 1
    assert evidence["hidden_source_checks_passed"] == 13
    assert evidence["hidden_source_checks_total"] == 13
    assert evidence["hidden_source_semantic_claims_passed"] == 12
    assert evidence["hidden_source_semantic_claims_total"] == 12
    assert evidence["post_runtime_evaluator_model_calls"] == 1
    assert evidence["hidden_expected_values_disclosed"] is False
    assert evidence["runtime_feedback_generated"] is False
    assert evidence["operator_disposition"] == "FAILED"
    assert evidence["automated_semantic_evaluator_false_positive"] is True
    assert evidence["future_semantic_protocol"] == (
        "v11_integrated_plus_adversarial_exact_haiku"
    )
    assert evidence["closeout_evidence_commit"] == (
        "419efdbbc3dfd789a30451079b78f33e8a2d8c73"
    )
    assert evidence["automated_full_task_passed"] is True
    assert evidence["full_task_passed"] is False
    assert evidence["trusted_capability_credit"] is False
    assert evidence["ladder_score_before_activation"] == "7/96"
    assert evidence["ladder_score_after_activation"] == "7/97"
    assert evidence["ladder_score_after_consumption"] == "7/97"

    run_path = Path(evidence["run_path"])
    immutable_files = {
        "research_agent_runtime_manifest.json": evidence[
            "runtime_manifest_sha256"
        ],
        "betareg_jss_2010_r_public_replication_runtime_result.json": evidence[
            "runtime_result_sha256"
        ],
        "research_capability_gold_evaluation.json": evidence[
            "gold_evaluation_sha256"
        ],
        "runtime_llm_topology.json": evidence["runtime_topology_sha256"],
    }
    for name, expected_sha256 in immutable_files.items():
        assert hashlib.sha256((run_path / name).read_bytes()).hexdigest() == (
            expected_sha256
        )

    gold = json.loads(
        (run_path / "research_capability_gold_evaluation.json").read_text(
            encoding="utf-8"
        )
    )
    assert gold["n_tasks_passed"] == 1
    assert gold["hidden_expected_values_disclosed"] is False
    assert gold["runtime_feedback_generated"] is False
    evaluated = gold["tasks"][0]
    assert evaluated["task_passed"] is True
    assert evaluated["hidden_source_replication_combined_passed"] is True
    assert evaluated["hidden_source_report_semantic_candidate_model_calls"] == 1
    assert evaluated["hidden_source_report_semantic_candidate_status"] == "PASS"
    assert sum(
        row["status"] == "SATISFIED"
        for row in evaluated[
            "hidden_source_report_semantic_claim_assessments"
        ]
    ) == 12

    report = next(run_path.glob("theory_workspaces/*/source_replication_report.md"))
    assert hashlib.sha256(report.read_bytes()).hexdigest() == evidence[
        "source_report_sha256"
    ]
    report_text = report.read_text(encoding="utf-8")
    assert "loglog link produces the highest log-likelihood" in report_text
    assert "50.01105" in report_text
    operator_audit = Path(evidence["operator_audit"])
    assert operator_audit.is_file()
    assert "`FAILED` for full-task capability credit" in (
        operator_audit.read_text(encoding="utf-8")
    )

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
    assert readiness["scored_tasks_total"] == 98
    assert readiness["unconsumed_scored_tasks"] == 0
    assert readiness["consumed_scored_tasks"] == 98
    assert readiness["fully_gold_configured_tasks"] == 98
    assert readiness["fully_gold_passed_tasks"] == 7
    assert readiness["runtime_source_replication_components_ready"] == 9
    assert readiness["source_replication_components_passed"] == 2
    assert readiness["source_replication_full_tasks_passed"] == 1
    assert readiness["operator_invalid_tasks"] == 17
    active = [
        row
        for row in ladder["initial_candidate_queue"]
        if row["status"] == "active_scored"
    ]
    assert active == []
