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
VISIBLE_PATH = Path("benchmarks/research_l0_lognormal_mean_questions_20260830.json")
LEDGER_PATH = Path(
    "docs/evaluation_activations/task113_lognormal_mean_preactivation.json"
)
OPERATOR_AUDIT = Path("docs/operator_audits/lognormal_mean_mle_wald_l0_v1.md")
GOLD_MANIFEST = Path(
    "/Users/yukangzengcmac/.codex/evaluator_authority/AI-Statistician/"
    "research-l0-lognormal-mean-20260830-v1/gold_manifest.json"
)
RUN_PATH = Path(
    "runs/main_worker_research_l0_lognormal_mean_20260830_v1_"
    "codex_workspace_exact_haiku"
)
TASK_ID = "lognormal_arithmetic_mean_mle_wald_interval_known_result"
RUNTIME_RESULT = RUN_PATH / f"{TASK_ID}_runtime_result.json"
RUNTIME_MANIFEST = RUN_PATH / "research_agent_runtime_manifest.json"
GOLD_EVALUATION = RUN_PATH / "research_capability_gold_evaluation.json"
ARTIFACT_INDEX = RUN_PATH / "runtime_artifact_store/indexes" / f"{TASK_ID}.json"
PROGRESS = RUN_PATH / "runtime_progress.jsonl"
THEORY_DOCUMENT = RUN_PATH / (
    "theory_workspaces/theory_workspace-7adfecfd71b3e5a474e1/"
    "lognormal_mle_theory.md"
)
FINAL_SOURCE = RUN_PATH / (
    "algorithm_sandbox/lognormal_arithmetic_mean_mle_wald_interval_known_result/"
    "c4e43174f790/"
    "est_lognormal_mean_wald_interval_4815a3ae812f84c4_generated_draft.py"
)
SHARED_MECHANISM_COMMIT = "6c129e8f4c758b2f10097e7d2817c2bf97af92e1"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_artifacts() -> list[tuple[dict[str, object], dict[str, object]]]:
    index = json.loads(ARTIFACT_INDEX.read_text(encoding="utf-8"))
    return [
        (ref, json.loads(Path(ref["path"]).read_text(encoding="utf-8")))
        for ref in index["artifacts"].values()
    ]


def test_lognormal_task113_is_consumed_once_and_failed_closed() -> None:
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
    assert len(ladder["initial_candidate_queue"]) == 113
    assert ladder["initial_candidate_queue"][-1]["id"] == TASK_ID
    assert readiness["scored_tasks_total"] == 113
    assert readiness["unconsumed_scored_tasks"] == 0
    assert readiness["consumed_scored_tasks"] == 113
    assert readiness["fully_gold_configured_tasks"] == 113
    assert readiness["fully_gold_passed_tasks"] == 7
    assert readiness["operator_invalid_tasks"] == 18
    assert readiness["latest_shared_mechanism_head"] == SHARED_MECHANISM_COMMIT

    assert candidate["level"] == "L0"
    assert candidate["family"] == "lognormal_mean_parametric_inference"
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
    assert descriptor["benchmark_manifest_hash"] == candidate["gold_descriptor_hash"]
    assert descriptor["active_task_ids"] == [TASK_ID]

    assert evidence["mechanical_algorithm_authority_checks_correct"] == "9/9"
    assert evidence["mechanical_algorithm_valid_cases_correct"] == "28/28"
    assert evidence["mechanical_algorithm_invalid_cases_correct"] == "79/79"
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
    assert len(tool_finishes) == evidence["runtime_client_tool_executions"] == 69
    assert sum(tool_error_counts.values()) == evidence["runtime_client_tool_errors"] == 8
    assert workspace_counts == {
        "AlgorithmEngineer": 32,
        "ArchitectMetricSemanticReviewer": 10,
        "GeneratedCodeSemanticReviewer": 14,
        "TheoryDeveloper": 15,
    }
    assert tool_counts == {
        "commit_scientific_source": 3,
        "commit_theory_checkpoint": 1,
        "edit_current_scientific_source": 5,
        "read_current_generated_source": 2,
        "read_theory_document": 18,
        "read_theory_workspace": 2,
        "run_current_scientific_source": 10,
        "run_exact_estimator_review_probe": 5,
        "run_theory_scratchpad": 6,
        "submit_generated_code_semantic_review": 6,
        "submit_scientific_source": 4,
        "submit_theory_preflight_review": 2,
        "write_theory_document": 1,
        "write_theory_preflight_report": 1,
        "write_theory_workspace": 3,
    }
    assert tool_error_counts == {
        "run_current_scientific_source": 1,
        "run_exact_estimator_review_probe": 3,
        "submit_generated_code_semantic_review": 3,
        "submit_theory_preflight_review": 1,
    }
    assert {row["metadata"]["model"] for row in model_turns} == {
        "claude-haiku-4-5-20251001"
    }
    assert evidence["runtime_product_model_calls"] == 72
    assert evidence["runtime_direct_model_calls"] == 1
    assert sum(evidence["runtime_model_calls_by_workspace"].values()) == 72

    runtime = json.loads(RUNTIME_RESULT.read_text(encoding="utf-8"))
    manifest = json.loads(RUNTIME_MANIFEST.read_text(encoding="utf-8"))
    failure = manifest["runtime_failure_summary"]
    research = manifest["research_evaluation_summary"]
    assert runtime["status"] == evidence["runtime_status"] == "BLOCKED"
    assert runtime["runtime_steps_executed"] == evidence["runtime_steps"] == 9
    assert runtime["outer_graph_iterations_consumed"] == 9
    assert runtime["same_owner_workspace_continuations_consumed"] == 0
    assert runtime["pending_task"] is None
    assert failure["terminal_subsystem"] == "GeneratedCodeSemanticReviewer"
    assert failure["terminal_classification"] == (
        "generated_code_semantic_review_lineage_budget_exhausted"
    )
    assert research["n_questions_research_loop_complete"] == 0
    assert research["all_questions_mode_conformant"] is True
    assert research["all_questions_research_eval_complete"] is False
    requirements = research["rows"][0]["requirements"]
    assert requirements["serious_theory_completed"] is True
    assert requirements["theory_preexecution_review_accepted"] is True
    assert requirements["generated_algorithm_executed_and_passed"] is False
    assert requirements["algorithm_semantic_review_accepted"] is False
    assert research["rows"][0]["formalization_status"][
        "strict_formal_lane_executed"
    ] is False

    artifacts = _load_artifacts()
    kind_counts = Counter(ref["payload_kind"] for ref, _ in artifacts)
    assert kind_counts["TheoryDerivationPacket"] == 1
    assert kind_counts["TheoryDeveloperWorkspaceEvidence"] == 1
    assert kind_counts["RuntimeAlgorithmSandboxManifest"] == 3
    assert kind_counts["GeneratedCodeSemanticReviewPacket"] == 3
    assert kind_counts["GeneratedCodeSemanticReviewDocument"] == 3
    assert kind_counts["RuntimeGeneratedCodeSemanticReviewExecutionManifest"] == 3
    assert kind_counts["RuntimeGeneratedCodeSemanticReviewWorkOrder"] == 3
    assert kind_counts["RuntimeGeneratedCodeSemanticReviewMaterialization"] == 3

    algorithm_manifests = [
        payload
        for ref, payload in artifacts
        if ref["payload_kind"] == "RuntimeAlgorithmSandboxManifest"
    ]
    assert len(algorithm_manifests) == 3
    assert all(row["n_executed"] == 1 for row in algorithm_manifests)
    assert all(row["n_passed"] == 1 for row in algorithm_manifests)
    assert all(row["n_generated_code_executed"] == 1 for row in algorithm_manifests)
    assert all(row["n_generated_code_passed"] == 1 for row in algorithm_manifests)
    assert all(row["promotion_ready"] is False for row in algorithm_manifests)
    assert all(
        row["generated_code_semantic_review_pending"] is True
        for row in algorithm_manifests
    )
    assert {row["prototypes"][0]["script_hash"] for row in algorithm_manifests} == {
        "d4c8fae1c88f6eb44f00f3ddbae0e9cb6eb0a28f4b783b6c0966f4217b3d013b",
        "6522ed624d27fd0c70782f0bdd50a8f739e3ced097f0e0aa6423e7ef2825d620",
        "e9ffcde4b3d0d95eb8158f9a6e7e173b311afe3ebacbab7265b910f548b65315",
    }

    review_packets = {
        payload["packet_id"]: payload
        for ref, payload in artifacts
        if ref["payload_kind"] == "GeneratedCodeSemanticReviewPacket"
    }
    first_review = review_packets["generated_code_semantic_review:5dd6407f597bbb055d90cf3c"]
    assert first_review["overall_verdict"] == "REVISE"
    assert "fully implements" in first_review["source_revision_assessment"][
        "rationale"
    ]
    assert len(first_review["client_tool_loop"]["review_probe_executions"]) == 3
    assert all(
        probe["target_source_invoked"] is False
        and probe["failed_probe_is_target_source_evidence"] is False
        for probe in first_review["client_tool_loop"]["review_probe_executions"]
    )

    later_reviews = [
        review_packets["generated_code_semantic_review:3afacc7c8edd1f75287352b5"],
        review_packets["generated_code_semantic_review:3390731cbd6e01608d3a53c4"],
    ]
    assert all(row["overall_verdict"] == "REVISE" for row in later_reviews)
    assert all(
        row["client_tool_loop"]["review_probe_executions"][0][
            "target_source_invoked"
        ]
        is True
        for row in later_reviews
    )
    assert all(
        "tuple" in row["findings"][0]["summary"].lower() for row in later_reviews
    )

    final_source = FINAL_SOURCE.read_text(encoding="utf-8")
    assert "if not isinstance(observations, list)" in final_source
    assert "request.get('observations')" in final_source
    assert "np.array(observations, dtype=float)" in final_source
    assert len(final_source.splitlines()) == evidence["final_source_lines"] == 318
    assert len(FINAL_SOURCE.read_bytes()) == evidence["final_source_bytes"] == 13237
    assert _sha256(FINAL_SOURCE) == evidence["final_source_sha256"]

    assert len(THEORY_DOCUMENT.read_text(encoding="utf-8").splitlines()) == 340
    assert len(THEORY_DOCUMENT.read_bytes()) == 13651
    assert _sha256(THEORY_DOCUMENT) == evidence["theory_document_sha256"]
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
    assert _sha256(ARTIFACT_INDEX) == evidence["runtime_artifact_index_sha256"]
    assert _sha256(GOLD_EVALUATION) == evidence["hidden_assessment_record_sha256"]

    topology = json.loads((RUN_PATH / "runtime_llm_topology.json").read_text())
    enabled_agents = [row for row in topology["llm_agents"] if row["enabled"]]
    assert topology["policy_status"] == "OK"
    assert topology["model_tier_counts"] == {"haiku": 7}
    assert {row["model"] for row in enabled_agents} == {
        "claude-haiku-4-5-20251001"
    }

    gold = json.loads(GOLD_EVALUATION.read_text(encoding="utf-8"))
    task = gold["tasks"][0]
    assert gold["n_tasks_evaluated"] == 1
    assert gold["n_tasks_passed"] == 0
    assert gold["hidden_expected_values_disclosed"] is False
    assert gold["runtime_feedback_generated"] is False
    assert task["hidden_theory_execution_attempted"] is True
    assert task["hidden_theory_execution_passed"] is True
    assert task["hidden_theory_checks_passed"] is True
    assert task["hidden_theory_semantic_passed"] is True
    assert task["hidden_theory_semantic_calibration_cases_correct"] == 6
    assert task["hidden_theory_semantic_candidate_mode_negative_cases_correct"] == 1
    assert task["hidden_theory_semantic_claim_count"] == 8
    assert {row["status"] for row in task["hidden_theory_semantic_claim_assessments"]} == {
        "SATISFIED"
    }
    assert task["hidden_harness_execution_attempted"] is False
    assert task["hidden_empirical_execution_attempted"] is False
    assert task["dimension_status"]["theory"]["status"] == "passed"
    assert task["dimension_status"]["scientific_code"]["status"] == "failed"
    assert task["dimension_status"]["empirical"]["status"] == "failed"
    assert task["failure_reasons"] == [
        "no independently accepted algorithm handoff was observed"
    ]
    assert task["task_passed"] is False

    assert evidence["operator_disposition"] == "FAILED"
    assert evidence["operator_invalid"] is False
    assert evidence["post_run_shared_mechanism_commit"] == SHARED_MECHANISM_COMMIT
    assert evidence["full_task_passed"] is False
    assert evidence["trusted_capability_credit"] is False
    assert evidence["ladder_score_after_consumption"] == "7/113"
    assert evidence["model_draw_resampling_blocked"] is True
    assert evidence["formalization_requirement"] == "not_applicable"
    assert evidence["formalizer_executed"] is False
    assert evidence["generated_algorithm_executed"] is True
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
