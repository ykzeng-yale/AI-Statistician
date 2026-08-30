from __future__ import annotations

import hashlib
import json
from collections import Counter
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
    "benchmarks/research_l0_wishart_sample_covariance_questions_20260830.json"
)
LEDGER_PATH = Path(
    "docs/evaluation_activations/task111_wishart_sample_covariance_preactivation.json"
)
OPERATOR_AUDIT = Path(
    "docs/operator_audits/wishart_sample_covariance_l0_v1.md"
)
GOLD_MANIFEST = Path(
    "/Users/yukangzengcmac/.codex/evaluator_authority/AI-Statistician/"
    "research-l0-wishart-sample-covariance-20260830-v1/gold_manifest.json"
)
RUN_PATH = Path(
    "runs/main_worker_research_l0_wishart_sample_covariance_20260830_v1_"
    "codex_workspace_exact_haiku"
)
RUNTIME_RESULT = RUN_PATH / (
    "multivariate_normal_sample_covariance_wishart_known_result_runtime_result.json"
)
GOLD_EVALUATION = RUN_PATH / "research_capability_gold_evaluation.json"
ARTIFACT_INDEX = RUN_PATH / "runtime_artifact_store/indexes/" / (
    "multivariate_normal_sample_covariance_wishart_known_result.json"
)
PROGRESS = RUN_PATH / "runtime_progress.jsonl"
TASK_ID = "multivariate_normal_sample_covariance_wishart_known_result"
SHARED_MECHANISM_COMMIT = "2124ee6e598a58885e11d9458e10316815b69952"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_artifacts() -> list[tuple[dict[str, object], dict[str, object]]]:
    index = json.loads(ARTIFACT_INDEX.read_text(encoding="utf-8"))
    return [
        (ref, json.loads(Path(ref["path"]).read_text(encoding="utf-8")))
        for ref in index["artifacts"].values()
    ]


def test_wishart_task111_is_consumed_once_and_failed_closed() -> None:
    ladder = json.loads(LADDER_PATH.read_text(encoding="utf-8"))
    candidates = [
        row for row in ladder["initial_candidate_queue"] if row["id"] == TASK_ID
    ]
    assert len(candidates) == 1
    candidate = candidates[0]
    evidence = candidate["activation_evidence"]
    visible_payload = json.loads(VISIBLE_PATH.read_text(encoding="utf-8"))
    visible_question = visible_payload["questions"][0]
    loaded_question = load_open_research_questions(VISIBLE_PATH)[0]
    descriptor = validate_research_gold_benchmark_manifest(GOLD_MANIFEST)

    readiness = ladder["current_readiness"]
    assert len(ladder["evidence_dimensions"]) == 7
    assert len(ladder["initial_candidate_queue"]) == 111
    assert ladder["initial_candidate_queue"][-1]["id"] == TASK_ID
    assert readiness["scored_tasks_total"] == 111
    assert readiness["unconsumed_scored_tasks"] == 0
    assert readiness["consumed_scored_tasks"] == 111
    assert readiness["fully_gold_configured_tasks"] == 111
    assert readiness["fully_gold_passed_tasks"] == 7
    assert readiness["operator_invalid_tasks"] == 18
    assert readiness["latest_shared_mechanism_head"] == SHARED_MECHANISM_COMMIT

    assert candidate["level"] == "L0"
    assert candidate["family"] == (
        "multivariate_normal_sample_covariance_moments"
    )
    assert candidate["status"] == "consumed_scored"
    assert candidate["activation_status"] == (
        "fresh_live_v1_consumed_exact_haiku_runtime_blocked_"
        "hidden_full_task_failed"
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

    assert _sha256(VISIBLE_PATH) == evidence["visible_questions_sha256"]
    assert stable_hash(visible_question) == evidence["visible_question_full_hash"]
    assert stable_hash(_visible_question_hash_payload(visible_question)) == evidence[
        "runtime_visible_question_hash"
    ]
    assert frozen_estimator_execution_contract_id(
        visible_question["estimator_execution_contract"]
    ) == evidence["estimator_execution_contract_id"]
    assert _sha256(LEDGER_PATH) == evidence["public_preactivation_ledger_sha256"]
    assert _sha256(GOLD_MANIFEST) == candidate["gold_manifest_sha256"]
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
    assert evidence["mechanical_algorithm_authority_checks_correct"] == "11/11"
    assert evidence["mechanical_algorithm_valid_cases_correct"] == "24/24"
    assert evidence["mechanical_algorithm_invalid_cases_correct"] == "35/35"
    assert evidence["mechanical_empirical_authority_checks_correct"] == "15/15"
    assert evidence["mechanical_negative_evaluator_controls_rejected"] == "5/5"
    assert evidence["semantic_protocol_version"] == 11
    assert evidence["semantic_candidate_adjudication_strategy"] == (
        "integrated_plus_adversarial"
    )
    assert evidence["semantic_calibration_cases_correct"] == "6/6"
    assert evidence["semantic_candidate_mode_negative_cases_correct"] == "1/1"
    assert evidence["semantic_reference_claims"] == 8
    assert evidence["semantic_successful_qualification_model_calls"] == 16
    assert evidence["preactivation_product_model_calls"] == 0
    assert evidence["preactivation_evaluator_model_calls"] == 16
    assert evidence["gold_frozen_before_first_runtime_model_call"] is True
    assert evidence["activation_push_confirmed_on_work_branch_and_main"] is True
    assert evidence["single_fresh_draw_only"] is True

    progress = [
        json.loads(line) for line in PROGRESS.read_text(encoding="utf-8").splitlines()
    ]
    model_turns = [
        row
        for row in progress
        if row["event_type"] == "substage_start"
        and row["substage"] == "client_tool_model_turn"
    ]
    tool_finishes = [
        row
        for row in progress
        if row["event_type"] == "substage_finish"
        and row["substage"] == "client_tool_execution"
    ]
    workspace_counts = Counter(
        row["metadata"]["workspace_subsystem"] for row in model_turns
    )
    tool_counts = Counter(row["metadata"]["tool_name"] for row in tool_finishes)
    tool_error_counts = Counter(
        row["metadata"]["tool_name"]
        for row in tool_finishes
        if row["metadata"]["tool_result_is_error"] is True
    )
    assert len(model_turns) == evidence["runtime_client_tool_model_turns"] == 163
    assert len(tool_finishes) == evidence["runtime_client_tool_executions"] == 173
    assert sum(tool_error_counts.values()) == evidence["runtime_client_tool_errors"] == 20
    assert workspace_counts == {
        "TheoryDeveloper": 81,
        "ArchitectMetricSemanticReviewer": 82,
    }
    assert tool_counts["commit_theory_checkpoint"] == 5
    assert tool_counts["submit_theory_preflight_review"] == 9
    assert tool_counts["edit_theory_document"] == 19
    assert tool_error_counts["edit_theory_document"] == 14
    assert {row["metadata"]["model"] for row in model_turns} == {
        "claude-haiku-4-5-20251001"
    }
    assert evidence["runtime_product_model_calls"] == 164
    assert evidence["runtime_direct_model_calls"] == 1
    assert sum(evidence["runtime_model_calls_by_workspace"].values()) == 164

    runtime = json.loads(RUNTIME_RESULT.read_text(encoding="utf-8"))
    assert runtime["status"] == evidence["runtime_status"] == "BLOCKED"
    assert runtime["runtime_steps_executed"] == evidence["runtime_steps"] == 12
    assert runtime["outer_graph_iterations_consumed"] == 12
    assert runtime["same_owner_workspace_continuations_consumed"] == 0
    assert runtime["pending_task"] is None
    assert evidence["runtime_terminal_subsystem"] == "TheoryDeveloper"
    assert evidence["runtime_terminal_classification"] == (
        "theory_developer_packet_validation_failed"
    )
    assert evidence["runtime_recovery_checkpoint_available"] is True
    assert evidence["runtime_mode_conformant"] is True
    assert evidence["runtime_research_eval_complete"] is False
    assert evidence["runtime_theory_preexecution_review_accepted"] is False
    assert evidence["runtime_critic_research_acceptance"] is False

    artifacts = _load_artifacts()
    kind_counts = Counter(ref["payload_kind"] for ref, _ in artifacts)
    assert kind_counts["TheoryDerivationPacket"] == 5
    assert kind_counts["TheoryDeveloperWorkspaceEvidence"] == 5
    assert kind_counts["RuntimeArchitectMetricProtocolPreExecutionRejection"] == 5
    assert kind_counts["RuntimeMetricProtocolPreExecutionReviewObservation"] == 5
    assert kind_counts["RuntimeTheoryDeveloperValidationFailure"] == 1

    rejections = sorted(
        (
            payload
            for ref, payload in artifacts
            if ref["payload_kind"]
            == "RuntimeArchitectMetricProtocolPreExecutionRejection"
        ),
        key=lambda row: row["upstream_theory_revision_count"],
    )
    assert [row["upstream_theory_revision_count"] for row in rejections] == [
        0,
        1,
        2,
        3,
        4,
    ]
    assert all(row["final_overall_verdict"] == "REVISE" for row in rejections)
    assert all(row["execution_authorized"] is False for row in rejections)
    for row in rejections[1:]:
        summary = row["prior_finding_resolution_summary"]
        assert row["prior_finding_progress_made"] is False
        assert summary["progress_made"] is False
        assert summary["stalled"] is True
        assert summary["closed_prior_finding_ids"] == []
        assert row["preflight_revision_progressed"] is True
        assert row["preflight_revision_stalled"] is False

    review_observations = sorted(
        (
            payload
            for ref, payload in artifacts
            if ref["payload_kind"]
            == "RuntimeMetricProtocolPreExecutionReviewObservation"
        ),
        key=lambda row: row["upstream_theory_revision_count"],
    )
    report_refs = [row["review_document_ref"] for row in review_observations]
    assert [row["sha256"] for row in report_refs] == evidence[
        "referee_report_sha256"
    ]
    assert all(_sha256(Path(row["path"])) == row["sha256"] for row in report_refs)

    theory_path = Path(evidence["latest_committed_theory_document_path"])
    estimator_path = Path(evidence["estimator_handoff_document_path"])
    recovery_path = Path(evidence["terminal_recovery_document_path"])
    for path, prefix in (
        (theory_path, "latest_committed_theory_document"),
        (estimator_path, "estimator_handoff_document"),
        (recovery_path, "terminal_recovery_document"),
    ):
        assert len(path.read_text(encoding="utf-8").splitlines()) == evidence[
            f"{prefix}_lines"
        ]
        assert len(path.read_bytes()) == evidence[f"{prefix}_bytes"]
        assert _sha256(path) == evidence[f"{prefix}_sha256"]
    assert evidence["latest_committed_theory_document_sha256"] != evidence[
        "terminal_recovery_document_sha256"
    ]

    assert _sha256(RUNTIME_RESULT) == evidence["runtime_result_sha256"]
    assert _sha256(RUN_PATH / "research_agent_runtime_manifest.json") == evidence[
        "runtime_manifest_sha256"
    ]
    assert _sha256(RUN_PATH / "runtime_completion_summary.json") == evidence[
        "runtime_completion_summary_sha256"
    ]
    assert _sha256(RUN_PATH / "runtime_failure_summary.json") == evidence[
        "runtime_failure_summary_sha256"
    ]
    assert _sha256(RUN_PATH / "runtime_llm_topology.json") == evidence[
        "runtime_llm_topology_sha256"
    ]
    assert _sha256(PROGRESS) == evidence["runtime_progress_sha256"]
    assert _sha256(GOLD_EVALUATION) == evidence[
        "hidden_assessment_record_sha256"
    ]

    gold = json.loads(GOLD_EVALUATION.read_text(encoding="utf-8"))
    task = gold["tasks"][0]
    assert gold["n_tasks_evaluated"] == 0
    assert gold["n_tasks_passed"] == 0
    assert gold["hidden_expected_values_disclosed"] is False
    assert gold["runtime_feedback_generated"] is False
    assert evidence["sole_hidden_assessment_invocations"] == 1
    assert evidence["hidden_evaluator_model_calls"] == 0
    assert task["hidden_theory_execution_attempted"] is False
    assert task["hidden_harness_execution_attempted"] is False
    assert task["hidden_empirical_execution_attempted"] is False
    assert task["task_passed"] is False

    assert evidence["operator_disposition"] == "FAILED"
    assert evidence["operator_invalid"] is False
    assert evidence["post_run_shared_mechanism_commit"] == SHARED_MECHANISM_COMMIT
    assert evidence["automated_full_task_passed"] is False
    assert evidence["full_task_passed"] is False
    assert evidence["trusted_capability_credit"] is False
    assert evidence["ladder_score_after_consumption"] == "7/111"
    assert evidence["model_draw_resampling_blocked"] is True
    assert evidence["formalization_requirement"] == "not_applicable"
    assert evidence["formalizer_executed"] is False
    assert evidence["generated_algorithm_executed"] is False
    assert evidence["generated_simulation_executed"] is False
    assert evidence["critic_executed"] is False
    assert evidence["sonnet_product_calls"] == 0
    assert evidence["opus_product_calls"] == 0
    assert OPERATOR_AUDIT.is_file()

    runtime_visible = json.dumps(
        {"candidate": candidate, "question": visible_question}, sort_keys=True
    )
    for hidden_name in (
        "semantic_reference.md",
        "candidate_mode_near_miss.md",
        "hidden_algorithm_harness.py",
        "hidden_empirical_harness.py",
    ):
        assert hidden_name not in runtime_visible
