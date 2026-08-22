from __future__ import annotations

import argparse
import json
from pathlib import Path

import pytest

from ai_statistician.agent_runtime import AgentTask, agent_task_reference
from ai_statistician.architect_coordinator_llm import (
    _architect_metric_authoring_deferred_for_active_replan,
    _architect_runtime_owned_evidence_contract,
    _architect_runtime_evaluation_contract,
    _required_architect_plan_subsystems,
)
from ai_statistician.cli import (
    _apply_research_agent_runtime_capability_eval_preset,
    _apply_research_agent_runtime_evaluation_model_policy,
    _apply_research_agent_runtime_research_eval_profile,
    _lean_project_import_preflight_errors,
    _load_runtime_resume_task_from_manifest,
    _research_agent_runtime_research_eval_ready,
    build_parser,
)
from ai_statistician.fingerprint import stable_hash
from ai_statistician.generated_code_semantic_reviewer_llm import (
    GeneratedCodeSemanticReviewerConfig,
    LLMGeneratedCodeSemanticReviewerAgent,
)
from ai_statistician.model_backend import (
    LIVE_EVALUATION_CLAUDE_MODEL_TIER,
    StaticJSONGeneratorBackend,
)
from ai_statistician.research_agent_runtime import (
    ResearchAgentRuntimeConfig,
    _post_empirical_evidence_task,
    _runtime_retire_resolved_generated_code_semantic_review_replan,
    _runtime_requested_evidence_contract,
    _runtime_simulation_metric_protocol_guard,
    run_research_agent_runtime,
)
from ai_statistician.research_architect import (
    LLMTheoryDeveloperAgent,
    ResearchArchitectConfig,
    THEORY_PROMPT_MODE_SERIOUS_CAPABILITY,
    _theory_developer_prompt_mode,
)
from ai_statistician.research_evaluation import (
    build_research_evaluation_summary,
)
from ai_statistician.research_schema import OpenResearchQuestion


def test_research_eval_contract_requires_research_lane_without_formalizer() -> None:
    research = _architect_runtime_evaluation_contract(
        {"evaluation_mode": "research_eval", "n_runs": 100}
    )
    strict = _architect_runtime_evaluation_contract(
        {"evaluation_mode": "capability_eval", "n_runs": 100}
    )

    assert research["research_evaluation_requires_generated_algorithm_code"] is True
    assert research["research_evaluation_requires_generated_simulation_code"] is True
    assert research[
        "research_evaluation_requires_generated_code_semantic_review"
    ] is True
    assert research["research_evaluation_requires_typed_metric_contracts"] is True
    assert research["generated_sandbox_runtime_replicates"] == 100
    assert research["generated_sandbox_max_runtime_replicates"] == 100_000
    assert research["generated_simulation_timeout_seconds"] == 60
    assert research["formal_evaluation_requires_formalizer_lean_candidate"] is False
    assert strict["formal_evaluation_requires_formalizer_lean_candidate"] is True

    required = set(_required_architect_plan_subsystems(research))
    assert {
        "RetrievalMemory",
        "TheoryDeveloper",
        "AlgorithmEngineer",
        "SimulationEvaluator",
        "GeneratedCodeSemanticReviewer",
        "CriticEvaluator",
    } <= required
    assert "FormalizationEvaluator" not in required


def test_source_only_checkpoint_completes_without_unrelated_critic() -> None:
    question = {
        "id": "source-only-evaluation",
        "title": "Source only",
        "description": "Replicate one immutable source.",
        "tags": [],
        "task_intent": {
            "source_replication": "required",
            "theory": "not_applicable",
            "scientific_code": "not_applicable",
            "empirical": "not_applicable",
            "formal": "not_applicable",
            "unresolved_gaps": "required",
        },
    }
    checkpoint_id = "source_replication_checkpoint:test"
    artifacts = {
        "question-metadata": {
            "artifact_kind": "RuntimeQuestionMetadata",
            "question": question,
        },
        checkpoint_id: {
            "artifact_kind": "SourceReplicationCheckpoint",
            "checkpoint_id": checkpoint_id,
            "question_id": question["id"],
            "runtime_completion_status": (
                "SOURCE_EXECUTION_RECORDED_REQUIRES_HIDDEN_EVALUATION"
            ),
            "report_document": {"relative_path": "report.md"},
            "unresolved_gaps": [],
            "model_authored_report": True,
            "runtime_edited_report": False,
            "runtime_edited_source": False,
        },
    }

    summary = build_research_evaluation_summary(
        [
            {
                "status": "ACCEPTED",
                "blackboard": {"artifacts": artifacts},
                "traces": (
                    {
                        "subsystem": "TheoryDeveloper",
                        "status": "ACCEPTED",
                        "produced_artifact_ids": (checkpoint_id,),
                    },
                ),
            }
        ],
        evaluation_mode="research_eval",
        schema_version="test",
    )

    row = summary["rows"][0]
    assert row["research_eval_complete"] is True
    assert row["required_capability_checks"] == [
        "source_replication_checkpoint_recorded",
        "source_replication_unresolved_gap_disclosure_present",
    ]
    assert row["requirements"]["critic_research_acceptance"] is False
    assert row["dimension_requirements"]["source_replication"] == "required"


def test_accepted_metric_rows_replace_the_exploratory_replicate_fallback() -> None:
    theory_material = {
        "artifact_kind": "RuntimeTheoryInformedMetricProtocolMaterial",
        "source_theory_packet_id": "theory:reviewed-precision",
        "source_theory_packet_hash": "theory-hash:reviewed-precision",
        "execution_results_available": False,
        "theory_semantic_material": {"claim_index": [{"claim_id": "C1"}]},
    }
    contract = _architect_runtime_owned_evidence_contract(
        architect_context={
            "architect_metric_protocol_theory_material": theory_material,
            "architect_metric_requirement_authoring": {
                "empirical_metric_requirements": [
                    {
                        "requirement_id": "reviewed-precision",
                        "target_subsystems": ["SimulationEngineer"],
                        "required_runtime_replicates": 7_300,
                    }
                ],
                "semantic_review_status": "ACCEPT",
                "semantic_review_independent_agent": True,
                "semantic_review_independent_invocation": True,
                "source_theory_packet_id": theory_material["source_theory_packet_id"],
                "source_theory_packet_hash": theory_material[
                    "source_theory_packet_hash"
                ],
            },
        },
        runtime_config={"evaluation_mode": "research_eval", "n_runs": 11},
    )

    assert contract["generated_sandbox_runtime_replicates"] == 7_300
    assert contract["generated_sandbox_runtime_replicates_source"] == (
        "accepted_model_authored_metric_requirements"
    )


def test_explicit_theory_only_intent_does_not_require_unused_lanes() -> None:
    contract = _runtime_requested_evidence_contract(
        formal_verification_policy="required",
        evaluation_mode="research_eval",
        task_intent={
            "theory": "required",
            "scientific_code": "not_applicable",
            "empirical": "not_applicable",
            "formal": "not_applicable",
        },
    )

    assert contract["formal_verification_policy"] == "optional"
    assert contract["formal_target_authoring_required"] is False
    assert contract["simulation_target_authoring_required"] is False
    assert contract["research_evaluation_requires_generated_algorithm_code"] is False
    assert contract["research_evaluation_requires_generated_simulation_code"] is False
    assert contract["research_evaluation_requires_typed_metric_contracts"] is False
    assert set(_required_architect_plan_subsystems(contract)) == {
        "RetrievalMemory",
        "TheoryDeveloper",
        "CriticEvaluator",
    }


def test_research_eval_cli_uses_frozen_gold_scope_when_configured() -> None:
    incomplete_full_loop = {"all_questions_research_eval_complete": False}

    assert _research_agent_runtime_research_eval_ready(
        summary=incomplete_full_loop,
        gold={"all_active_tasks_passed": True},
        research_gold_manifest="gold.json",
    )
    assert not _research_agent_runtime_research_eval_ready(
        summary={"all_questions_research_eval_complete": True},
        gold={"all_active_tasks_passed": False},
        research_gold_manifest="gold.json",
    )
    assert not _research_agent_runtime_research_eval_ready(
        summary=incomplete_full_loop,
        gold={},
        research_gold_manifest="",
    )


def test_fresh_accepted_artifact_retires_only_its_exact_stale_replan() -> None:
    stale_replan = {
        "source_subsystem": "AlgorithmEngineer",
        "source_manifest_id": "algorithm:rejected",
        "review_execution_id": "review-execution:rejected",
    }
    context = {
        "runtime_generated_code_semantic_review_replan": stale_replan,
        "environment_feedback": {
            "feedback_type": "generated_code_semantic_review_feedback",
            "source_manifest_id": "algorithm:rejected",
            "semantic_review_execution_id": "review-execution:rejected",
        },
        "runtime_feedback_loop": {
            "semantic_review_execution_id": "review-execution:rejected"
        },
    }
    accepted_review = {
        "source_subsystem": "AlgorithmEngineer",
        "source_manifest_id": "algorithm:fresh",
        "source_manifest_hash": "fresh-hash",
        "execution_id": "review-execution:accepted",
        "review_packet_id": "review-packet:accepted",
        "overall_verdict": "ACCEPT",
    }

    resolved = _runtime_retire_resolved_generated_code_semantic_review_replan(
        architect_context=context,
        accepted_review=accepted_review,
    )

    assert "runtime_generated_code_semantic_review_replan" not in resolved
    assert "environment_feedback" not in resolved
    assert "runtime_feedback_loop" not in resolved
    resolution = resolved[
        "runtime_generated_code_semantic_review_replan_resolution"
    ]
    assert resolution["rejected_source_manifest_id"] == "algorithm:rejected"
    assert resolution["accepted_source_manifest_id"] == "algorithm:fresh"

    defensive_context = {
        "runtime_generated_code_semantic_review_replan": stale_replan,
        "runtime_generated_code_semantic_review_replan_resolution": resolution,
    }
    assert _architect_metric_authoring_deferred_for_active_replan(
        defensive_context
    ) is False
    assert _architect_metric_authoring_deferred_for_active_replan(context) is True

    unrelated_acceptance = {
        **accepted_review,
        "source_subsystem": "SimulationEvaluator",
    }
    unchanged = _runtime_retire_resolved_generated_code_semantic_review_replan(
        architect_context=context,
        accepted_review=unrelated_acceptance,
    )
    assert unchanged["runtime_generated_code_semantic_review_replan"] == (
        stale_replan
    )


def test_research_eval_routes_accepted_empirical_artifacts_to_critic() -> None:
    question = OpenResearchQuestion(
        id="generic_research_eval",
        title="Generic research evaluation",
        description="Develop and evaluate a new statistical procedure.",
    )
    context = {
        "runtime_requested_evidence_contract": {
            "evaluation_mode": "research_eval"
        }
    }
    task = _post_empirical_evidence_task(
        question=question,
        packet_id="theory:1",
        simulation_manifest_id="simulation:1",
        algorithm_sandbox_manifest_id="algorithm:1",
        architect_context=context,
    )

    assert task.owner_subsystem == "CriticEvaluator"
    assert task.inputs["theory_packet_id"] == "theory:1"
    assert task.inputs["simulation_manifest_id"] == "simulation:1"
    assert task.inputs["algorithm_sandbox_manifest_id"] == "algorithm:1"

    debug_task = _post_empirical_evidence_task(
        question=question,
        packet_id="theory:1",
        simulation_manifest_id="simulation:1",
        algorithm_sandbox_manifest_id="algorithm:1",
        architect_context={},
    )
    assert debug_task.owner_subsystem == "FormalizationEvaluator"


def test_research_eval_keeps_serious_theory_and_independent_review_gate(
    tmp_path,
) -> None:
    contract = _runtime_requested_evidence_contract(
        formal_verification_policy="advisory",
        recommended_research_path="simulation_first",
        evaluation_mode="research_eval",
    )
    assert contract["research_evaluation_requires_generated_algorithm_code"] is True
    assert contract["research_evaluation_requires_generated_simulation_code"] is True
    assert contract["research_evaluation_requires_generated_code_semantic_review"] is True
    assert contract["research_evaluation_requires_generated_algorithm_code"] is True
    assert contract["research_evaluation_requires_generated_simulation_code"] is True
    assert contract[
        "research_evaluation_requires_generated_code_semantic_review"
    ] is True
    assert contract["research_evaluation_requires_typed_metric_contracts"] is True
    assert contract["formal_evaluation_requires_formalizer_lean_candidate"] is False
    assert contract["formal_target_authoring_required"] is False
    assert (
        _theory_developer_prompt_mode(
            {
                "architect_runtime_plan": {
                    "evidence_contract": {"evaluation_mode": "research_eval"}
                }
            }
        )
        == THEORY_PROMPT_MODE_SERIOUS_CAPABILITY
    )

    with pytest.raises(ValueError, match="GeneratedCodeSemanticReviewer"):
        run_research_agent_runtime(
            [],
            tmp_path,
            theory_developer=None,
            config=ResearchAgentRuntimeConfig(evaluation_mode="research_eval"),
        )


def test_research_eval_returns_before_formal_postprocessing(tmp_path) -> None:
    theory_developer = LLMTheoryDeveloperAgent(
        provider=StaticJSONGeneratorBackend({}),
        config=ResearchArchitectConfig(
            provider_name="static",
            model="static",
            model_tier=LIVE_EVALUATION_CLAUDE_MODEL_TIER,
            serious_model="static",
            serious_model_tier=LIVE_EVALUATION_CLAUDE_MODEL_TIER,
        ),
    )
    semantic_reviewer = LLMGeneratedCodeSemanticReviewerAgent(
        provider=StaticJSONGeneratorBackend({}),
        config=GeneratedCodeSemanticReviewerConfig(
            provider_name="static",
            model="static",
            model_tier=LIVE_EVALUATION_CLAUDE_MODEL_TIER,
        ),
    )

    manifest = run_research_agent_runtime(
        [],
        tmp_path,
        theory_developer=theory_developer,
        generated_code_semantic_reviewer=semantic_reviewer,
        config=ResearchAgentRuntimeConfig(evaluation_mode="research_eval"),
    )

    assert manifest["runtime_endpoint"] == "typed_agent_runtime"
    assert manifest["runtime_formal_capability_source"] == (
        "integrated_agent_runtime_only"
    )
    assert not any(key.startswith("post_runtime_") for key in manifest)
    assert manifest["runtime_evaluation_mode"] == "research_eval"
    assert "runtime_stage" not in manifest
    assert "runtime_theorem_reduction_closure_work_orders_jsonl" not in (
        manifest["artifacts"]
    )


def test_nonformal_run_does_not_materialize_lean_provider_inventory(
    monkeypatch,
    tmp_path,
) -> None:
    def unexpected_formal_provider_materialization():
        raise AssertionError("nonformal tasks must not materialize Lean providers")

    monkeypatch.setattr(
        "ai_statistician.research_agent_runtime."
        "build_default_formal_source_retriever",
        unexpected_formal_provider_materialization,
    )
    monkeypatch.setattr(
        "ai_statistician.research_agent_runtime."
        "ai4slt_proof_state_trace_rag_descriptor",
        unexpected_formal_provider_materialization,
    )
    theory_developer = LLMTheoryDeveloperAgent(
        provider=StaticJSONGeneratorBackend({}),
        config=ResearchArchitectConfig(
            provider_name="static",
            model="static",
            model_tier=LIVE_EVALUATION_CLAUDE_MODEL_TIER,
            serious_model="static",
            serious_model_tier=LIVE_EVALUATION_CLAUDE_MODEL_TIER,
        ),
    )
    question = OpenResearchQuestion(
        id="nonformal-topology",
        title="Nonformal topology",
        description="Develop a theory without Lean authoring.",
        task_intent={
            "theory": "required",
            "scientific_code": "not_applicable",
            "empirical": "not_applicable",
            "formal": "not_applicable",
        },
    )

    manifest = run_research_agent_runtime(
        [question],
        tmp_path,
        theory_developer=theory_developer,
        config=ResearchAgentRuntimeConfig(
            evaluation_mode="research_eval",
            max_iterations=1,
        ),
    )

    topology = manifest["lean_provider_topology"]
    assert topology["activated_for_selected_tasks"] is False
    assert topology["formal_source_retriever"] == {
        "configured": True,
        "provider_instantiated": False,
        "activated_for_selected_tasks": False,
        "activation_status": "all_selected_tasks_formal_not_applicable",
    }
    assert "providers" not in str(topology)
    assert len(json.dumps(topology)) < 2_000


def test_research_eval_exports_pending_continuations_for_every_question(
    tmp_path,
) -> None:
    theory_developer = LLMTheoryDeveloperAgent(
        provider=StaticJSONGeneratorBackend({}),
        config=ResearchArchitectConfig(
            provider_name="static",
            model="static",
            model_tier=LIVE_EVALUATION_CLAUDE_MODEL_TIER,
            serious_model="static",
            serious_model_tier=LIVE_EVALUATION_CLAUDE_MODEL_TIER,
        ),
    )
    semantic_reviewer = LLMGeneratedCodeSemanticReviewerAgent(
        provider=StaticJSONGeneratorBackend({}),
        config=GeneratedCodeSemanticReviewerConfig(
            provider_name="static",
            model="static",
            model_tier=LIVE_EVALUATION_CLAUDE_MODEL_TIER,
        ),
    )
    questions = [
        OpenResearchQuestion("pending_q1", "Pending one", "", ()),
        OpenResearchQuestion("pending_q2", "Pending two", "", ()),
    ]
    initial_tasks = {
        question.id: AgentTask(
            task_id=f"simulation:{question.id}",
            owner_subsystem="SimulationEvaluator",
            objective="Exercise question-bound continuation export.",
            inputs={
                "question": {
                    "id": question.id,
                    "title": question.title,
                    "description": question.description,
                    "tags": list(question.tags),
                },
                "theory_packet_id": "",
                "architect_context": {},
            },
        )
        for question in questions
    }

    manifest = run_research_agent_runtime(
        questions,
        tmp_path,
        theory_developer=theory_developer,
        generated_code_semantic_reviewer=semantic_reviewer,
        initial_task_overrides=initial_tasks,
        config=ResearchAgentRuntimeConfig(
            evaluation_mode="research_eval",
            max_iterations=1,
        ),
    )

    assert manifest["n_incomplete_pending_next_tasks"] == 2
    pending = manifest["incomplete_pending_next_tasks"]
    assert {row["question_id"] for row in pending} == {
        "pending_q1",
        "pending_q2",
    }
    assert all(row["pending_next_task"]["artifact_kind"] == "AgentTaskRef" for row in pending)
    assert all("inputs" not in row["pending_next_task"] for row in pending)
    assert all(
        row["pending_task_continuation_ref"]["artifact_kind"]
        == "RuntimeAgentTaskContinuationRef"
        for row in pending
    )
    assert all(
        row["pending_task_checkpoint_reason"]
        == "outer_iteration_budget_exhausted"
        for row in pending
    )
    pending_rows = [
        json.loads(line)
        for line in Path(
            manifest["artifacts"]["runtime_pending_next_tasks_jsonl"]
        ).read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert [row["question_id"] for row in pending_rows] == [
        "pending_q1",
        "pending_q2",
    ]
    assert all(
        row["pending_next_task"]["owner_subsystem"] == "TheoryDeveloper"
        for row in pending_rows
    )
    assert len(json.dumps(pending_rows)) < 10_000

    pending_q1 = next(
        row for row in pending_rows if row["question_id"] == "pending_q1"
    )
    single_pending_path = tmp_path / "single_pending.jsonl"
    single_pending_path.write_text(
        json.dumps(pending_q1) + "\n",
        encoding="utf-8",
    )
    resume_manifest = dict(manifest)
    resume_manifest["runtime_failure_summary"] = {
        "terminal_question_id": "unrelated_blocked_question"
    }
    resume_manifest["artifacts"] = {
        **manifest["artifacts"],
        "runtime_pending_next_tasks_jsonl": str(single_pending_path),
    }
    resume_manifest_path = tmp_path / "single_pending_manifest.json"
    resume_manifest_path.write_text(
        json.dumps(resume_manifest),
        encoding="utf-8",
    )
    question_id, restored_task, restored_artifacts = (
        _load_runtime_resume_task_from_manifest(resume_manifest_path)
    )
    assert question_id == "pending_q1"
    assert restored_task.owner_subsystem == "TheoryDeveloper"
    restored_ref = agent_task_reference(restored_task)
    expected_ref = next(
        row["pending_next_task"]
        for row in pending_rows
        if row["question_id"] == "pending_q1"
    )
    assert restored_ref == expected_ref
    continuation_id = next(
        row["pending_task_continuation_ref"]["continuation_id"]
        for row in pending_rows
        if row["question_id"] == "pending_q1"
    )
    assert restored_artifacts[continuation_id]["artifact_kind"] == (
        "RuntimeAgentTaskContinuation"
    )

    q1_result = next(
        json.loads(Path(result_path).read_text(encoding="utf-8"))
        for result_path in manifest["artifacts"]["per_question_results"]
        if "pending_q1" in Path(result_path).name
    )
    continuation_blob = Path(
        q1_result["blackboard"]["artifacts"][continuation_id]["path"]
    )
    continuation_blob.write_text("{}", encoding="utf-8")
    with pytest.raises(ValueError, match="artifact payload hash mismatch"):
        _load_runtime_resume_task_from_manifest(resume_manifest_path)


def test_research_eval_profile_enables_live_research_agents_only() -> None:
    args = argparse.Namespace(
        research_eval=True,
        capability_eval=False,
        capability_eval_preset="none",
        provider="anthropic",
        architect_coordinator_provider="same",
        simulation_engineer_provider="same",
        algorithm_engineer_provider="same",
        critic_evaluator_provider="same",
        generated_code_semantic_reviewer_provider="none",
        formalizer_provider="same",
        formal_target_semantic_reviewer_provider="same",
        formal_target_semantic_review_required=True,
        formal_verification_policy="required",
        recommended_research_path="proof_first",
        architect_max_tokens=1000,
        serious_theory_model_tier=LIVE_EVALUATION_CLAUDE_MODEL_TIER,
        serious_theory_max_tokens=1000,
        llm_timeout_seconds=120.0,
    )

    _apply_research_agent_runtime_research_eval_profile(args)
    _apply_research_agent_runtime_evaluation_model_policy(args)

    assert args.generated_code_semantic_reviewer_provider == "same"
    assert args.formalizer_provider == "none"
    assert args.formal_target_semantic_reviewer_provider == "none"
    assert args.formal_target_semantic_review_required is False
    assert args.formal_verification_policy == "advisory"
    assert args.recommended_research_path == "simulation_first"
    assert args.architect_max_tokens == 3000
    assert args.architect_metric_semantic_reviewer_max_tokens == 16000
    assert args.serious_theory_model_tier == "haiku"
    assert args.evaluation_claude_model_tier == "haiku"
    assert args.evaluation_claude_model == "claude-haiku-4-5-20251001"
    assert args.serious_theory_max_tokens >= 16000
    assert args.llm_timeout_seconds == 360.0
    assert args.max_iterations == 24

    parsed = build_parser().parse_args(
        ["research-agent-runtime", "--research-eval"]
    )
    assert parsed.research_eval is True
    assert parsed.capability_eval is False
    with pytest.raises(SystemExit):
        build_parser().parse_args(
            [
                "research-agent-runtime",
                "--research-eval",
                "--capability-eval",
            ]
        )


def test_full_live_outer_iteration_ceiling_governs_revision_paths() -> None:
    args = build_parser().parse_args(
        [
            "research-agent-runtime",
            "--capability-eval",
            "--capability-eval-preset",
            "full-live",
        ]
    )

    _apply_research_agent_runtime_capability_eval_preset(args)

    assert args.max_iterations == 40
    assert args.generated_code_semantic_review_max_revisions == 2


def test_runtime_defaults_shared_lean_retrieval_to_canonical_main() -> None:
    parsed = build_parser().parse_args(["research-agent-runtime"])

    assert parsed.emperical_process_lean_rag_source == "main"


def test_lean_project_preflight_imports_topology_entry_module(
    tmp_path,
    monkeypatch,
) -> None:
    project = tmp_path / "EmpericalProcessLEAN"
    project.mkdir()
    observed: list[list[str]] = []

    class Result:
        returncode = 0
        stdout = ""
        stderr = ""

    def fake_run(command, **kwargs):
        observed.append(list(command))
        return Result()

    entry_source = project / "StatInference.lean"
    entry_source.write_text("import StatInference.Foundation\n", encoding="utf-8")
    monkeypatch.setattr("ai_statistician.cli.subprocess.run", fake_run)

    assert _lean_project_import_preflight_errors(
        project,
        timeout_seconds=30,
    ) == []
    assert observed == [["lake", "env", "lean", str(entry_source)]]
    assert entry_source.read_text(encoding="utf-8") == (
        "import StatInference.Foundation\n"
    )


def test_lean_project_preflight_fails_closed_with_raw_diagnostics(
    tmp_path,
    monkeypatch,
) -> None:
    project = tmp_path / "generic-lake-project"
    project.mkdir()

    def fake_run(command, **kwargs):
        return type(
            "LeanResult",
            (),
            {
                "returncode": 1,
                "stdout": "",
                "stderr": "Main.lean:1:0: error: unknown module prefix",
            },
        )()

    monkeypatch.setattr("ai_statistician.cli.subprocess.run", fake_run)

    errors = _lean_project_import_preflight_errors(
        project,
        timeout_seconds=30,
    )

    assert len(errors) == 1
    assert "import preflight failed" in errors[0]
    assert "unknown module prefix" in errors[0]


def test_simulation_guard_blocks_before_proposal_or_execution() -> None:
    question = OpenResearchQuestion(
        id="generic_simulation_guard",
        title="Guard confirmatory execution",
        description="Require a reviewed theory-bound metric protocol.",
    )
    task = AgentTask(
        task_id="simulation:guard",
        owner_subsystem="SimulationEvaluator",
        objective="run confirmatory simulation",
        inputs={
            "question": {
                "id": question.id,
                "title": question.title,
                "description": question.description,
                "tags": [],
            },
            "theory_packet_id": "theory:guard",
        },
    )
    context = {
        "architect_runtime_plan": {
            "evidence_contract": {
                "research_evaluation_requires_typed_metric_contracts": True,
                "empirical_metric_requirements": [],
                "metric_protocol_execution_authorized": False,
            }
        }
    }

    result = _runtime_simulation_metric_protocol_guard(
        task=task,
        question=question,
        theory_packet_id="theory:guard",
        theory_packet={"packet_id": "theory:guard"},
        architect_context=context,
        exploratory_diagnostic=False,
    )

    assert result is not None
    assert result.status == "REROUTE"
    assert result.next_task is not None
    assert result.next_task.owner_subsystem == "ArchitectCoordinator"
    block = next(iter(result.produced_artifacts.values()))
    assert block["execution_attempted"] is False
    assert block["execution_authorized"] is False


def test_research_evaluation_summary_requires_every_research_artifact() -> None:
    question = {"id": "generic_research_eval"}
    artifacts = {
        "theory": {
            "artifact_kind": "TheoryDerivationPacket",
            "packet_id": "theory",
            "question": question,
            "serious_theory_mode": True,
            "provider": "anthropic",
        },
        "architect": {
            "artifact_kind": "ArchitectCoordinatorProposalPacket",
            "packet_id": "architect",
            "evidence_contract": {
                "empirical_metric_protocol_phase": "preexecution_review_accepted",
                "metric_protocol_execution_authorized": True,
                "empirical_metric_requirement_set_id": "metric-set:1",
                "empirical_metric_requirements": [{"requirement_id": "metric:1"}],
                "empirical_metric_requirements_preexecution_review": {
                    "overall_verdict": "ACCEPT",
                    "independent_agent": True,
                    "independent_invocation": True,
                    "independent_model": True,
                    "independent_model_tier": True,
                },
            },
        },
        "algorithm": {
            "artifact_kind": "RuntimeAlgorithmSandboxManifest",
            "manifest_id": "algorithm",
            "theory_packet_id": "theory",
            "n_live_generated_code_executed": 1,
            "n_passed": 1,
            "n_live_generated_code_execution_failed": 0,
        },
        "simulation": {
            "artifact_kind": "RuntimeSimulationManifest",
            "manifest_id": "simulation",
            "theory_packet_id": "theory",
            "runtime_architect_control": {
                "architect_coordinator_proposal_id": "architect"
            },
            "n_live_generated_simulation_sandbox_executed": 1,
            "generated_simulation_passed": True,
            "simulation_passed": True,
            "n_generated_simulation_typed_metric_contracts_declared": 1,
            "n_generated_simulation_typed_metric_contracts_evaluated": 1,
            "n_generated_simulation_typed_metric_contracts_passed": 1,
            "n_generated_simulation_typed_metric_contracts_failed": 0,
            "generated_simulation_sandbox_prototypes": [
                {
                    "smoke_passed": True,
                    "metric_requirement_set_id": "metric-set:1",
                    "metric_requirement_authority_validated": True,
                    "metric_contract_evaluation": {
                        "metric_requirement_set_id": "metric-set:1",
                        "metric_requirement_authority_validated": True,
                        "n_contracts": 1,
                        "n_passed": 1,
                        "n_failed": 0,
                        "all_required_passed": True,
                    },
                }
            ],
        },
        "critic": {
            "artifact_kind": "RuntimeCriticEvaluatorManifest",
            "manifest_id": "critic",
            "question": question,
            "theory_packet_id": "theory",
            "algorithm_sandbox_manifest_id": "algorithm",
            "simulation_manifest_id": "simulation",
            "llm_critic_evaluator_proposal_id": "critic_proposal",
            "evidence_contract_decision": {
                "runtime_status": "ACCEPTED",
                "scientific_disposition": "ACCEPT",
            },
        },
        "critic_proposal": {
            "artifact_kind": "CriticEvaluatorProposalPacket",
            "critic_findings": [],
            "dimension_assessments": [
                {
                    "dimension": dimension,
                    "status": (
                        "NOT_REQUESTED" if dimension == "formal" else "SUPPORTED"
                    ),
                }
                for dimension in (
                    "theory",
                    "scientific_code",
                    "empirical",
                    "formal",
                )
            ],
            "gap_disclosure": {
                "status": "COMPLETE",
                "disclosed_gaps": [],
                "evidence_refs": ["critic-canonical-view"],
                "rationale": "All observed gaps are disclosed.",
            },
            "research_disposition": {
                "status": "ACCEPT",
                "blocking_dimensions": [],
                "rationale": "The requested research dimensions are supported.",
            },
        },
    }
    preflight = {
        "artifact_kind": "ArchitectTheoryExecutionPreflightReviewPacket",
        "source_theory_packet_id": "theory",
        "source_theory_packet_hash": stable_hash(artifacts["theory"]),
        "overall_verdict": "ACCEPT",
        "active_unresolved_finding_ids": [],
    }
    artifacts["theory_preflight"] = preflight
    artifacts["theory_preflight_acceptance"] = {
        "artifact_kind": "RuntimeArchitectTheoryExecutionPreflightAcceptance",
        "source_theory_packet_id": "theory",
        "source_theory_packet_hash": stable_hash(artifacts["theory"]),
        "preflight_packet_id": "theory_preflight",
        "preflight_packet_hash": stable_hash(preflight),
    }
    accepted_review = {
        "artifact_kind": "RuntimeGeneratedCodeSemanticReviewExecutionManifest",
        "semantic_review_accepted": True,
        "independent_agent": True,
        "independent_invocation": True,
        "independent_model": True,
        "reviewer_model_tier": LIVE_EVALUATION_CLAUDE_MODEL_TIER,
        "confirmatory_empirical_evidence_eligible": True,
    }
    artifacts["algorithm_review"] = {
        **accepted_review,
        "source_subsystem": "AlgorithmEngineer",
        "source_manifest_id": "algorithm",
        "source_manifest_hash": stable_hash(artifacts["algorithm"]),
        "confirmatory_empirical_evidence_eligible": False,
    }
    artifacts["simulation_review"] = {
        **accepted_review,
        "source_subsystem": "SimulationEvaluator",
        "source_manifest_id": "simulation",
        "source_manifest_hash": stable_hash(artifacts["simulation"]),
    }
    result = {
        "status": "ACCEPTED",
        "blackboard": {"artifacts": artifacts},
        "traces": (
            {
                "subsystem": "CriticEvaluator",
                "status": "ACCEPTED",
                "produced_artifact_ids": ("critic",),
            },
        ),
    }

    summary = build_research_evaluation_summary(
        [result], evaluation_mode="research_eval", schema_version="test"
    )
    assert summary["all_questions_research_loop_complete"] is True
    assert summary["rows"][0]["requirements"][
        "critic_unresolved_gap_disclosure_present"
    ] is True

    preflight_acceptance = artifacts.pop("theory_preflight_acceptance")
    summary = build_research_evaluation_summary(
        [result], evaluation_mode="research_eval", schema_version="test"
    )
    assert summary["all_questions_research_loop_complete"] is False
    assert summary["rows"][0]["requirements"][
        "theory_preexecution_review_accepted"
    ] is False
    artifacts["theory_preflight_acceptance"] = preflight_acceptance

    artifacts["critic_proposal"]["gap_disclosure"].pop("evidence_refs")
    summary = build_research_evaluation_summary(
        [result], evaluation_mode="research_eval", schema_version="test"
    )
    assert summary["all_questions_research_loop_complete"] is False
    artifacts["critic_proposal"]["gap_disclosure"]["evidence_refs"] = [
        "critic-canonical-view"
    ]
    artifacts["critic_proposal"]["research_disposition"]["status"] = (
        "INCONCLUSIVE"
    )
    summary = build_research_evaluation_summary(
        [result], evaluation_mode="research_eval", schema_version="test"
    )
    assert summary["all_questions_research_loop_complete"] is False
    artifacts["critic_proposal"]["research_disposition"]["status"] = "ACCEPT"

    artifacts["simulation"].update(
        {
            "n_generated_simulation_typed_metric_contracts_declared": 2,
            "n_generated_simulation_typed_metric_contracts_evaluated": 2,
            "n_generated_simulation_typed_metric_contracts_passed": 1,
            "n_generated_simulation_typed_metric_contracts_failed": 1,
        }
    )
    metric_evaluation = artifacts["simulation"][
        "generated_simulation_sandbox_prototypes"
    ][0]["metric_contract_evaluation"]
    metric_evaluation.update(
        {
            "n_contracts": 2,
            "n_passed": 1,
            "n_failed": 1,
            "all_required_passed": True,
        }
    )
    artifacts["simulation_review"]["source_manifest_hash"] = stable_hash(
        artifacts["simulation"]
    )
    summary = build_research_evaluation_summary(
        [result], evaluation_mode="research_eval", schema_version="test"
    )
    assert summary["all_questions_research_loop_complete"] is True
    assert summary["rows"][0]["requirements"][
        "simulation_metric_evidence_nonvacuous_and_bound"
    ] is True

    artifacts["simulation_review"][
        "confirmatory_empirical_evidence_eligible"
    ] = False
    summary = build_research_evaluation_summary(
        [result], evaluation_mode="research_eval", schema_version="test"
    )
    assert summary["all_questions_research_loop_complete"] is False
    artifacts["simulation_review"][
        "confirmatory_empirical_evidence_eligible"
    ] = True

    artifacts["stale_algorithm"] = {
        **artifacts["algorithm"],
        "manifest_id": "stale_algorithm",
    }
    artifacts["algorithm"]["n_passed"] = 0
    summary = build_research_evaluation_summary(
        [result], evaluation_mode="research_eval", schema_version="test"
    )
    assert summary["all_questions_research_loop_complete"] is False
    assert summary["all_questions_mode_conformant"] is True
    assert summary["all_questions_research_eval_complete"] is False

    artifacts["algorithm"]["n_passed"] = 1
    artifacts["algorithm_review"]["source_manifest_hash"] = stable_hash(
        artifacts["algorithm"]
    )
    result["traces"] = (
        *result["traces"],
        {"subsystem": "FormalizationEvaluator"},
    )
    summary = build_research_evaluation_summary(
        [result], evaluation_mode="research_eval", schema_version="test"
    )
    assert summary["all_questions_research_loop_complete"] is True
    assert summary["all_questions_mode_conformant"] is False
    assert summary["all_questions_research_eval_complete"] is True
    assert summary["rows"][0]["mode_conformance"][
        "strict_formal_lane_not_executed"
    ] is False


def test_research_summary_honors_theory_only_task_intent() -> None:
    question = {
        "id": "theory_only",
        "task_intent": {
            "theory": "required",
            "scientific_code": "not_applicable",
            "empirical": "not_applicable",
            "formal": "not_applicable",
        },
    }
    theory = {
        "artifact_kind": "TheoryDerivationPacket",
        "packet_id": "theory",
        "question": question,
        "serious_theory_mode": True,
        "provider": "anthropic",
    }
    critic_proposal = {
        "artifact_kind": "CriticEvaluatorProposalPacket",
        "dimension_requirements": dict(question["task_intent"]),
        "dimension_assessments": [
            {
                "dimension": dimension,
                "status": "SUPPORTED" if dimension == "theory" else "NOT_REQUESTED",
            }
            for dimension in ("theory", "scientific_code", "empirical", "formal")
        ],
        "research_disposition": {
            "status": "ACCEPT",
            "blocking_dimensions": [],
            "rationale": "The requested theory is supported.",
        },
        "gap_disclosure": {
            "status": "COMPLETE",
            "disclosed_gaps": [],
            "evidence_refs": ["theory"],
            "rationale": "No unresolved requested-dimension gaps.",
        },
    }
    critic = {
        "artifact_kind": "RuntimeCriticEvaluatorManifest",
        "manifest_id": "critic",
        "question": question,
        "theory_packet_id": "theory",
        "algorithm_sandbox_manifest_id": "",
        "simulation_manifest_id": "",
        "llm_critic_evaluator_proposal_id": "critic_proposal",
        "evidence_contract_decision": {
            "runtime_status": "ACCEPTED",
            "scientific_disposition": "ACCEPT",
        },
    }
    result = {
        "status": "ACCEPTED",
        "blackboard": {
            "artifacts": {
                "question": {
                    "artifact_kind": "RuntimeQuestionMetadata",
                    "question": question,
                },
                "theory": theory,
                "critic_proposal": critic_proposal,
                "critic": critic,
            }
        },
        "traces": (
            {
                "subsystem": "CriticEvaluator",
                "status": "ACCEPTED",
                "produced_artifact_ids": ("critic",),
            },
        ),
    }

    summary = build_research_evaluation_summary(
        [result], evaluation_mode="research_eval", schema_version="test"
    )

    row = summary["rows"][0]
    assert row["research_loop_complete"] is True
    assert row["required_capability_checks"] == [
        "serious_theory_completed",
        "critic_research_acceptance",
        "critic_unresolved_gap_disclosure_present",
    ]
    assert row["requirements"]["generated_algorithm_executed_and_passed"] is False
    assert row["requirements"]["generated_simulation_executed_and_passed"] is False


def test_research_summary_preserves_reviewed_theory_and_code_before_critic() -> None:
    question = {"id": "blocked_after_reviewed_code"}
    theory = {
        "artifact_kind": "TheoryDerivationPacket",
        "packet_id": "theory",
        "question": question,
        "serious_theory_mode": True,
        "provider": "anthropic",
    }
    preflight = {
        "artifact_kind": "ArchitectTheoryExecutionPreflightReviewPacket",
        "source_theory_packet_id": "theory",
        "source_theory_packet_hash": stable_hash(theory),
        "overall_verdict": "ACCEPT",
        "source_grounding_verified": True,
        "active_unresolved_finding_ids": [],
    }
    algorithm = {
        "artifact_kind": "RuntimeAlgorithmSandboxManifest",
        "manifest_id": "algorithm",
        "theory_packet_id": "theory",
        "n_live_generated_code_executed": 1,
        "n_passed": 1,
        "n_live_generated_code_execution_failed": 0,
    }
    artifacts = {
        "question_metadata": {
            "artifact_kind": "RuntimeQuestionMetadata",
            "question": question,
        },
        "theory": theory,
        "preflight": preflight,
        "preflight_acceptance": {
            "artifact_kind": (
                "RuntimeArchitectTheoryExecutionPreflightAcceptance"
            ),
            "source_theory_packet_id": "theory",
            "source_theory_packet_hash": stable_hash(theory),
            "preflight_packet_id": "preflight",
            "preflight_packet_hash": stable_hash(preflight),
        },
        "algorithm": algorithm,
        "algorithm_review": {
            "artifact_kind": (
                "RuntimeGeneratedCodeSemanticReviewExecutionManifest"
            ),
            "source_subsystem": "AlgorithmEngineer",
            "source_manifest_id": "algorithm",
            "source_manifest_hash": stable_hash(algorithm),
            "semantic_review_accepted": True,
            "independent_agent": True,
            "independent_invocation": True,
            "reviewer_model_tier": LIVE_EVALUATION_CLAUDE_MODEL_TIER,
            "confirmatory_empirical_evidence_eligible": False,
        },
        "architect": {
            "artifact_kind": "ArchitectCoordinatorProposalPacket",
            "packet_id": "architect",
            "metric_requirement_authoring": {
                "source_theory_packet_id": "theory",
                "source_theory_packet_hash": stable_hash(theory),
            },
            "evidence_contract": {
                "empirical_metric_protocol_phase": "preexecution_review_accepted",
                "metric_protocol_execution_authorized": True,
                "empirical_metric_requirement_set_id": "metric-set:1",
                "empirical_metric_requirements": [
                    {"requirement_id": "metric:1"}
                ],
                "empirical_metric_requirements_preexecution_review": {
                    "overall_verdict": "ACCEPT",
                    "independent_agent": True,
                    "independent_invocation": True,
                },
            },
        },
    }
    result = {
        "status": "BLOCKED",
        "blackboard": {"artifacts": artifacts},
        "traces": (
            {
                "subsystem": "ArchitectCoordinator",
                "status": "REROUTE",
                "task": {"inputs_ref": "persisted-task-input"},
                "produced_artifact_ids": (),
            },
        ),
    }

    summary = build_research_evaluation_summary(
        [result], evaluation_mode="research_eval", schema_version="test"
    )

    row = summary["rows"][0]
    assert row["question_id"] == question["id"]
    assert row["requirements"]["serious_theory_completed"] is True
    assert row["requirements"]["theory_preexecution_review_accepted"] is True
    assert row["requirements"][
        "generated_algorithm_executed_and_passed"
    ] is True
    assert row["requirements"]["algorithm_semantic_review_accepted"] is True
    assert row["requirements"]["metric_protocol_independently_accepted"] is True
    assert row["requirements"][
        "generated_simulation_executed_and_passed"
    ] is False
    assert row["research_eval_complete"] is False
