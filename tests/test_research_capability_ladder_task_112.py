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
    "benchmarks/research_l0_woolf_log_odds_ratio_questions_20260830.json"
)
LEDGER_PATH = Path(
    "docs/evaluation_activations/task112_woolf_log_odds_ratio_preactivation.json"
)
OPERATOR_AUDIT = Path("docs/operator_audits/woolf_log_odds_ratio_l0_v1.md")
GOLD_MANIFEST = Path(
    "/Users/yukangzengcmac/.codex/evaluator_authority/AI-Statistician/"
    "research-l0-woolf-log-odds-ratio-20260830-v1/gold_manifest.json"
)
RUN_PATH = Path(
    "runs/main_worker_research_l0_woolf_log_odds_ratio_20260830_v1_"
    "codex_workspace_exact_haiku"
)
RUNTIME_RESULT = RUN_PATH / (
    "woolf_two_by_two_log_odds_ratio_interval_known_result_runtime_result.json"
)
RUNTIME_MANIFEST = RUN_PATH / "research_agent_runtime_manifest.json"
GOLD_EVALUATION = RUN_PATH / "research_capability_gold_evaluation.json"
ARTIFACT_INDEX = RUN_PATH / "runtime_artifact_store/indexes/" / (
    "woolf_two_by_two_log_odds_ratio_interval_known_result.json"
)
PROGRESS = RUN_PATH / "runtime_progress.jsonl"
TASK_ID = "woolf_two_by_two_log_odds_ratio_interval_known_result"
SHARED_MECHANISM_COMMIT = "2e895af1f84dfbfc06c0da692bfc275710047b6b"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_artifacts() -> list[tuple[dict[str, object], dict[str, object]]]:
    index = json.loads(ARTIFACT_INDEX.read_text(encoding="utf-8"))
    return [
        (ref, json.loads(Path(ref["path"]).read_text(encoding="utf-8")))
        for ref in index["artifacts"].values()
    ]


def test_woolf_task112_is_consumed_once_and_failed_closed() -> None:
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

    assert candidate["level"] == "L0"
    assert candidate["family"] == "independent_two_group_log_odds_ratio_inference"
    assert candidate["status"] == "consumed_scored"
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
    assert descriptor["benchmark_manifest_hash"] == candidate[
        "gold_descriptor_hash"
    ]
    assert descriptor["active_task_ids"] == [TASK_ID]

    assert evidence["mechanical_algorithm_authority_checks_correct"] == "9/9"
    assert evidence["mechanical_algorithm_valid_cases_correct"] == "28/28"
    assert evidence["mechanical_algorithm_invalid_cases_correct"] == "44/44"
    assert evidence["mechanical_empirical_authority_checks_correct"] == "14/14"
    assert evidence["mechanical_empirical_designs_correct"] == "3/3"
    assert evidence["mechanical_empirical_replicates_per_design"] == 5000
    assert evidence["mechanical_empirical_estimator_invocations"] == 15000
    assert evidence["mechanical_negative_evaluator_controls_rejected"] == "7/7"
    assert evidence["semantic_protocol_version"] == 11
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
    assert len(model_turns) == evidence["runtime_client_tool_model_turns"] == 71
    assert len(tool_finishes) == evidence["runtime_client_tool_executions"] == 71
    assert sum(tool_error_counts.values()) == evidence["runtime_client_tool_errors"] == 3
    assert workspace_counts == {
        "TheoryDeveloper": 49,
        "ArchitectMetricSemanticReviewer": 22,
    }
    assert tool_counts == {
        "read_theory_document": 28,
        "run_theory_scratchpad": 11,
        "edit_theory_document": 8,
        "search_theory_documents": 5,
        "read_theory_workspace": 4,
        "write_theory_workspace": 4,
        "submit_theory_preflight_review": 3,
        "commit_theory_checkpoint": 2,
        "write_theory_preflight_report": 2,
        "read_theory_preflight_report": 2,
        "write_theory_document": 1,
        "edit_theory_preflight_report": 1,
    }
    assert tool_error_counts == {
        "edit_theory_document": 2,
        "submit_theory_preflight_review": 1,
    }
    assert {row["metadata"]["model"] for row in model_turns} == {
        "claude-haiku-4-5-20251001"
    }
    assert evidence["runtime_product_model_calls"] == 72
    assert evidence["runtime_direct_model_calls"] == 1
    assert sum(evidence["runtime_model_calls_by_workspace"].values()) == 72

    runtime = json.loads(RUNTIME_RESULT.read_text(encoding="utf-8"))
    failure = json.loads((RUN_PATH / "runtime_failure_summary.json").read_text())
    manifest = json.loads(RUNTIME_MANIFEST.read_text(encoding="utf-8"))
    research = manifest["research_evaluation_summary"]
    assert runtime["status"] == evidence["runtime_status"] == "BLOCKED"
    assert runtime["runtime_steps_executed"] == evidence["runtime_steps"] == 5
    assert runtime["outer_graph_iterations_consumed"] == 5
    assert runtime["same_owner_workspace_continuations_consumed"] == 0
    assert runtime["pending_task"] is None
    assert failure["terminal_subsystem"] == "ArchitectCoordinator"
    assert failure["terminal_classification"] == (
        "architect_theory_execution_preflight_stalled"
    )
    assert research["n_questions_research_loop_complete"] == 0
    assert research["all_questions_mode_conformant"] is True
    assert research["all_questions_research_eval_complete"] is False
    assert research["rows"][0]["requirements"]["serious_theory_completed"] is True
    assert research["rows"][0]["requirements"][
        "theory_preexecution_review_accepted"
    ] is False
    assert research["rows"][0]["formalization_status"][
        "strict_formal_lane_executed"
    ] is False

    artifacts = _load_artifacts()
    kind_counts = Counter(ref["payload_kind"] for ref, _ in artifacts)
    assert kind_counts["TheoryDerivationPacket"] == 2
    assert kind_counts["TheoryDeveloperWorkspaceEvidence"] == 2
    assert kind_counts["RuntimeArchitectMetricProtocolPreExecutionRejection"] == 2
    assert kind_counts["RuntimeMetricProtocolPreExecutionReviewObservation"] == 1
    assert not any(
        kind.startswith("Generated") or kind.startswith("Simulation")
        for kind in kind_counts
    )

    rejections = sorted(
        (
            payload
            for ref, payload in artifacts
            if ref["payload_kind"]
            == "RuntimeArchitectMetricProtocolPreExecutionRejection"
        ),
        key=lambda row: row["upstream_theory_revision_count"],
    )
    assert [row["upstream_theory_revision_count"] for row in rejections] == [0, 1]
    assert all(row["final_overall_verdict"] == "REVISE" for row in rejections)
    assert all(row["execution_authorized"] is False for row in rejections)
    assert rejections[0]["prior_finding_resolution_summary"]["progress_made"] is True
    assert rejections[1]["prior_finding_progress_made"] is False
    assert rejections[1]["preflight_revision_progressed"] is False
    assert rejections[1]["preflight_revision_stalled"] is True
    assert rejections[1]["prior_finding_resolution_summary"]["stalled"] is True
    assert rejections[1]["prior_finding_resolution_summary"][
        "closed_prior_finding_ids"
    ] == []

    report_refs = [row["semantic_review_history"][0]["review_report"] for row in rejections]
    assert [row["sha256"] for row in report_refs] == evidence[
        "referee_report_sha256"
    ]
    assert all(_sha256(Path(row["path"])) == row["sha256"] for row in report_refs)

    for index, path_value in enumerate(evidence["theory_document_paths"]):
        path = Path(path_value)
        assert len(path.read_text(encoding="utf-8").splitlines()) == evidence[
            "theory_document_lines"
        ][index]
        assert len(path.read_bytes()) == evidence["theory_document_bytes"][index]
        assert _sha256(path) == evidence["theory_document_sha256"][index]

    assert _sha256(RUNTIME_RESULT) == evidence["runtime_result_sha256"]
    assert _sha256(RUNTIME_MANIFEST) == evidence["runtime_manifest_sha256"]
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
    assert _sha256(RUN_PATH / "runtime_research_source_snapshot.json") == evidence[
        "runtime_source_snapshot_sha256"
    ]
    assert _sha256(GOLD_EVALUATION) == evidence[
        "hidden_assessment_record_sha256"
    ]

    topology = json.loads((RUN_PATH / "runtime_llm_topology.json").read_text())
    enabled_agents = [row for row in topology["llm_agents"] if row["enabled"]]
    assert topology["policy_status"] == "OK"
    assert topology["model_tier_counts"] == {"haiku": 7}
    assert {row["model"] for row in enabled_agents} == {
        "claude-haiku-4-5-20251001"
    }

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
    assert evidence["full_task_passed"] is False
    assert evidence["trusted_capability_credit"] is False
    assert evidence["ladder_score_after_consumption"] == "7/112"
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
