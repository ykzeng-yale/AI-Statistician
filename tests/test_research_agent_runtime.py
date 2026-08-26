from __future__ import annotations

import inspect
import json
from copy import deepcopy
from dataclasses import asdict, fields, replace
from pathlib import Path
from types import SimpleNamespace

import pytest

import ai_statistician.research_agent_runtime as runtime_module
from ai_statistician.agent_runtime import (
    AgentStepResult,
    AgentTask,
    BlackboardState,
    TaskHandoffRecord,
    ToolCallRecord,
    restore_agent_task_continuation,
    resolve_runtime_artifact_references,
    runtime_artifact_reference,
)
from ai_statistician.algorithm_engineer_llm import (
    ALGORITHM_ENGINEER_CODE_WORKSPACE_SYSTEM_PROMPT,
)
from ai_statistician.generated_code_semantic_reviewer_llm import (
    GeneratedCodeSemanticReviewerConfig,
    LLMGeneratedCodeSemanticReviewerAgent,
)
from ai_statistician.model_backend import (
    LIVE_EVALUATION_CLAUDE_MODEL,
    LIVE_EVALUATION_CLAUDE_MODEL_TIER,
    StaticJSONGeneratorBackend,
)
from ai_statistician.research_agent_runtime import (
    CriticEvaluatorRuntimeSubsystem,
    ResearchAgentRuntimeConfig,
    _normalized_runtime_evaluation_model_config,
    _runtime_generated_code_semantic_review_dispatch,
    _runtime_transition_policy,
    formalizer_workspace_runtime_bindings,
)
from ai_statistician.research_agent_runtime_audit import (
    _formalizer_revision_summary,
)
from ai_statistician.research_architect import ResearchArchitectConfig
from ai_statistician.research_schema import OpenResearchQuestion
from ai_statistician.scientific_code_workspace import ScientificCodeWorkspaceResult
from ai_statistician.simulation_engineer_llm import (
    SIMULATION_ENGINEER_CODE_WORKSPACE_SYSTEM_PROMPT,
    build_simulation_engineer_prompt,
)
from ai_statistician.structured_output_retry import PacketValidationError
from ai_statistician.theory_revision_lineage import (
    THEORY_CLAIM_REVISION_DELTA_KIND,
)
from ai_statistician.theory_workspace import THEORY_WORKSPACE_CONTENT_AUTHORITY


def test_formalization_has_one_model_owned_runtime_role() -> None:
    workspace = object()

    bindings = formalizer_workspace_runtime_bindings(workspace)  # type: ignore[arg-type]

    assert set(bindings) == {"FormalizationEvaluator"}
    assert bindings["FormalizationEvaluator"] is workspace


def test_research_evaluation_is_pinned_to_exact_haiku_snapshot() -> None:
    normalized = _normalized_runtime_evaluation_model_config(
        ResearchAgentRuntimeConfig(evaluation_mode="capability_eval")
    )

    assert normalized.evaluation_claude_model_tier == (
        LIVE_EVALUATION_CLAUDE_MODEL_TIER
    )
    assert normalized.evaluation_claude_model == LIVE_EVALUATION_CLAUDE_MODEL

    with pytest.raises(ValueError, match="requires evaluation_claude_model"):
        _normalized_runtime_evaluation_model_config(
            ResearchAgentRuntimeConfig(
                evaluation_mode="research_eval",
                evaluation_claude_model="claude-sonnet-4-5-20250929",
            )
        )


def test_theory_topology_records_shared_workspace_budget() -> None:
    config = ResearchArchitectConfig(
        provider_name="static",
        model="static-theory-model",
        serious_model="static-theory-model",
        theory_workspace_max_turns=17,
        theory_workspace_max_tool_calls=41,
    )
    agent = SimpleNamespace(
        config=config,
        provider=SimpleNamespace(provider_name="static"),
    )

    row = runtime_module._llm_agent_topology_row(
        "TheoryDeveloper",
        agent,
        role="model-owned mathematical workspace",
    )

    assert row["theory_workspace_max_turns"] == 17
    assert row["theory_workspace_max_tool_calls"] == 41
    assert row["theory_workspace_budget_policy"] == (
        "one_shared_ordinary_tool_call_budget"
    )


def test_required_source_replication_precedes_non_applicable_model_route() -> None:
    question = OpenResearchQuestion(
        id="source-routing",
        title="Source routing",
        description="Replicate one bound source without unrelated lanes.",
        task_intent={
            "source_replication": "required",
            "theory": "not_applicable",
            "scientific_code": "not_applicable",
            "empirical": "not_applicable",
            "formal": "not_applicable",
            "unresolved_gaps": "required",
        },
    )
    contract = runtime_module._runtime_requested_evidence_contract(
        formal_verification_policy="advisory",
        evaluation_mode="research_eval",
        task_intent=question.task_intent,
    )

    selected = runtime_module._architect_feasible_initial_subsystem(
        "SimulationEvaluator",
        architect_context={"runtime_requested_evidence_contract": contract},
        blackboard=BlackboardState(project_id=question.id),
        question_id=question.id,
    )

    assert contract["source_replication_requirement"] == "required"
    assert selected == "TheoryDeveloper"


def test_retrieval_memory_skips_lean_search_only_when_formal_is_not_applicable() -> None:
    class RecordingFormalSourceRetriever:
        name = "recording_formal_source"

        def __init__(self) -> None:
            self.calls: list[tuple[str, int]] = []

        def descriptor(self) -> dict[str, object]:
            return {"name": self.name, "provider": "test"}

        def search(self, query: str, *, k: int) -> list[object]:
            self.calls.append((query, k))
            return []

    def run_with_formal_requirement(
        requirement: str,
    ) -> tuple[RecordingFormalSourceRetriever, AgentStepResult, dict[str, object]]:
        retriever = RecordingFormalSourceRetriever()
        subsystem = runtime_module.RetrievalMemoryRuntimeSubsystem(
            formal_source_retriever=retriever
        )
        question = OpenResearchQuestion(
            id=f"retrieval-{requirement}",
            title="Task-intent retrieval",
            description="Develop a source-grounded statistical result.",
            task_intent={"formal": requirement},
        )
        result = subsystem.run(
            AgentTask(
                task_id=f"retrieval:{question.id}",
                owner_subsystem="RetrievalMemory",
                objective="Collect permitted research context.",
                inputs={"question": runtime_module._question_to_payload(question)},
            ),
            BlackboardState(project_id=question.id),
        )
        manifest = next(
            artifact
            for artifact in result.produced_artifacts.values()
            if artifact.get("artifact_kind") == "RuntimeRetrievalMemoryManifest"
        )
        return retriever, result, manifest

    skipped_retriever, skipped_result, skipped_manifest = (
        run_with_formal_requirement("not_applicable")
    )
    assert skipped_retriever.calls == []
    assert skipped_result.tool_calls == ()
    assert skipped_manifest["formal_source_retrieval_status"] == (
        "skipped_formal_not_applicable"
    )
    assert skipped_manifest["formal_source_hits"] == []
    assert skipped_manifest["formal_source_provider_topology"] == {}
    assert skipped_manifest["counts"]["formal_source_provider_calls"] == 0

    optional_retriever, optional_result, optional_manifest = (
        run_with_formal_requirement("optional")
    )
    assert optional_retriever.calls
    assert len(optional_result.tool_calls) == 1
    assert optional_manifest["formal_source_retrieval_status"] == "executed"


def test_theory_scratch_budget_allows_failure_correction_and_recheck() -> None:
    assert ResearchAgentRuntimeConfig().theory_scratch_max_runs >= 3


def test_confirmatory_simulation_prompt_can_withhold_the_execution_seed() -> None:
    question = OpenResearchQuestion(
        id="generic-seed-blind",
        title="Seed-blind confirmatory candidate",
        description="Author source before the evaluator reveals its cohort seed.",
    )

    prompt = build_simulation_engineer_prompt(
        question=question,
        theory_packet={},
        registered_problem={},
        registered_procedures=[],
        n_runs=8,
        seed=None,
        environment_feedback={},
    )
    payload = json.loads(prompt.rsplit("\n\n", 1)[1])

    assert payload["runtime_execution_budget"]["seed"] == "EVALUATOR_WITHHELD"
    assert payload["runtime_execution_budget"]["seed_binding"] == (
        "runtime_injected_after_candidate_authoring"
    )


def test_scientific_workspace_receives_the_complete_metric_output_abi() -> None:
    projected = runtime_module._scientific_workspace_metric_contracts(
        [
            {
                "contract_id": "coverage",
                "requirement_id": "coverage-requirement",
                "artifact_id": "simulation",
                "metric_path": ["coverage"],
                "metric_semantics": "Per-replicate interval coverage",
                "measurement_protocol": "Return one raw predicate per replicate.",
                "metric_value_kind": "boolean",
                "operator": "==",
                "aggregation": "at_least_fraction",
                "threshold": 1,
                "lower": None,
                "upper": None,
                "tolerance": 0.0,
                "minimum_pass_count": None,
                "minimum_pass_fraction": 0.92,
                "required_runtime_replicates": 80,
                "acceptance_authority_rationale": "not needed by source author",
            }
        ]
    )

    assert projected == [
        {
            "contract_id": "coverage",
            "requirement_id": "coverage-requirement",
            "artifact_id": "simulation",
            "metric_path": ["coverage"],
            "metric_semantics": "Per-replicate interval coverage",
            "measurement_protocol": "Return one raw predicate per replicate.",
            "metric_value_kind": "boolean",
            "operator": "==",
            "aggregation": "at_least_fraction",
            "threshold": 1,
            "lower": None,
            "upper": None,
            "tolerance": 0.0,
            "minimum_pass_count": None,
            "minimum_pass_fraction": 0.92,
            "required_runtime_replicates": 80,
        }
    ]


def test_required_formal_policy_does_not_hardcode_proof_first_execution() -> None:
    contract = runtime_module._runtime_requested_evidence_contract(
        formal_verification_policy="required",
        evaluation_mode="capability_eval",
    )

    assert contract["recommended_research_path"] == "dual_track"
    assert contract["formal_target_authoring_required"] is True


def test_optional_formal_policy_defaults_to_simulation_first() -> None:
    contract = runtime_module._runtime_requested_evidence_contract(
        formal_verification_policy="optional",
        evaluation_mode="debug",
    )

    assert contract["recommended_research_path"] == "simulation_first"
    assert contract["formal_required_for_final"] is False
    assert contract["formal_target_authoring_required"] is False


def test_task_intent_contract_cannot_be_resurrected_by_stale_feedback() -> None:
    contract = runtime_module._runtime_requested_evidence_contract(
        formal_verification_policy="optional",
        evaluation_mode="research_eval",
        task_intent={
            "theory": "required",
            "scientific_code": "not_applicable",
            "empirical": "not_applicable",
            "formal": "not_applicable",
        },
    )
    context = {"runtime_requested_evidence_contract": contract}
    stale_feedback = {
        "architect_evidence_contract": {
            "research_evaluation_requires_generated_algorithm_code": True,
            "research_evaluation_requires_generated_simulation_code": True,
            "research_evaluation_requires_typed_metric_contracts": True,
        }
    }

    merged = runtime_module._runtime_context_with_environment_feedback_contract(
        context,
        stale_feedback,
        subsystem="SimulationEvaluator",
    )

    merged_contract = merged["runtime_requested_evidence_contract"]
    assert merged_contract[
        "research_evaluation_requires_generated_algorithm_code"
    ] is False
    assert merged_contract[
        "research_evaluation_requires_generated_simulation_code"
    ] is False
    assert runtime_module._runtime_requires_generated_algorithm_code(
        merged,
        stale_feedback,
    ) is False
    assert runtime_module._runtime_requires_generated_simulation_code(
        merged,
        stale_feedback,
    ) is False


def test_theory_only_path_compiles_directly_to_critic() -> None:
    context = {
        "architect_runtime_plan": {
            "evidence_contract": {
                "recommended_research_path": "simulation_first",
                "formal_verification_policy": "optional",
                "formal_required_for_final": False,
                "research_evaluation_requires_generated_algorithm_code": False,
                "dimension_requirements": {
                    "theory": "required",
                    "scientific_code": "not_applicable",
                    "empirical": "not_applicable",
                    "formal": "not_applicable",
                },
            },
            "subsystem_execution_plan": [
                {"subsystem": "RetrievalMemory"},
                {"subsystem": "TheoryDeveloper"},
                {"subsystem": "CriticEvaluator"},
            ],
        }
    }

    assert runtime_module._compiled_post_theory_workspace_owner(
        context,
        implementation_gaps=[],
    ) == "CriticEvaluator"

    context["architect_runtime_plan"]["evidence_contract"].update(
        {
            "simulation_targets": ["run one model-selected diagnostic"],
            "dimension_requirements": {
                "theory": "required",
                "scientific_code": "not_applicable",
                "empirical": "optional",
                "formal": "not_applicable",
            },
        }
    )
    assert runtime_module._compiled_post_theory_workspace_owner(
        context,
        implementation_gaps=[],
    ) == "SimulationEvaluator"


def test_accepted_theory_only_preflight_compiles_without_empirical_gate() -> None:
    question = OpenResearchQuestion(
        id="accepted-theory-only-preflight",
        title="Accepted theory only preflight",
        description="Review exact theory before terminal criticism.",
        task_intent={
            "theory": "required",
            "scientific_code": "not_applicable",
            "empirical": "not_applicable",
            "formal": "not_applicable",
        },
    )
    theory_packet_id = "theory_derivation:accepted-theory-only"
    theory_packet = {
        "artifact_kind": "TheoryDerivationPacket",
        "packet_id": theory_packet_id,
        "question": runtime_module._question_to_payload(question),
    }
    theory_packet_hash = runtime_module.stable_hash(theory_packet)
    contract = runtime_module._runtime_requested_evidence_contract(
        formal_verification_policy="optional",
        evaluation_mode="research_eval",
        task_intent=question.task_intent,
    )
    context = {
        "architect_coordinator_proposal_id": "architect:theory-only",
        "architect_runtime_plan": {
            "packet_id": "architect:theory-only",
            "evidence_contract": contract,
            "subsystem_execution_plan": [
                {"subsystem": "TheoryDeveloper"},
                {"subsystem": "CriticEvaluator"},
            ],
        },
        "runtime_requested_evidence_contract": contract,
        "architect_metric_protocol_theory_material": {
            "source_theory_packet_id": theory_packet_id,
            "source_theory_packet_hash": theory_packet_hash,
        },
    }
    preflight = {
        "artifact_kind": "ArchitectTheoryExecutionPreflightReviewPacket",
        "packet_id": "theory_preflight:accepted-theory-only",
        "source_theory_packet_id": theory_packet_id,
        "source_theory_packet_hash": theory_packet_hash,
        "overall_verdict": "ACCEPT",
        "active_unresolved_finding_ids": [],
    }

    result = runtime_module._architect_theory_preflight_accepted_result(
        task=AgentTask(
            task_id="architect-theory-preflight:accepted-theory-only",
            owner_subsystem="ArchitectCoordinator",
            objective="Review exact theory.",
            inputs={"question": runtime_module._question_to_payload(question)},
        ),
        question=question,
        architect_context=context,
        preflight_packet=preflight,
        runtime_config=ResearchAgentRuntimeConfig(),
        blackboard=BlackboardState(
            project_id=question.id,
            artifacts={theory_packet_id: theory_packet},
        ),
    )

    assert result.status == "REROUTE"
    assert result.next_task is not None
    assert result.next_task.owner_subsystem == "CriticEvaluator"
    next_context = result.next_task.inputs["architect_context"]
    assert "architect_metric_protocol_gate" not in next_context
    acceptance = next(
        artifact
        for artifact in result.produced_artifacts.values()
        if artifact.get("artifact_kind")
        == "RuntimeArchitectTheoryExecutionPreflightAcceptance"
    )
    assert acceptance["algorithm_execution_available"] is False
    assert acceptance["empirical_evaluation_available"] is False
    assert acceptance["formalization_evaluation_available"] is False
    observation = next(
        artifact
        for artifact in result.produced_artifacts.values()
        if artifact.get("artifact_kind")
        == "RuntimeArchitectTheoryExecutionPreflightAcceptedObservation"
    )
    assert observation["metric_authoring_deferred"] is False


def test_runtime_config_has_no_legacy_prover_authoring_plane() -> None:
    names = {field.name for field in fields(ResearchAgentRuntimeConfig)}
    forbidden_fragments = (
        "bridge",
        "executor",
        "fallback",
        "learning_memory",
        "pseudo_formal",
        "theorem_reduction",
    )

    assert not {
        name
        for name in names
        if any(fragment in name for fragment in forbidden_fragments)
    }
    for removed_symbol in (
        "PseudoFormalBlockVerifierRuntimeSubsystem",
        "ExactSourceTheoremProofBodyRuntimeSubsystem",
        "SourceTheoremPromotionRuntimeSubsystem",
        "FormalizationGapPlannerRuntimeSubsystem",
    ):
        assert not hasattr(runtime_module, removed_symbol)


def test_canonical_runtime_has_no_outer_same_owner_source_retry_tasks() -> None:
    source = inspect.getsource(runtime_module)
    forbidden_task_prefixes = (
        "algorithm-revise:",
        "algorithm-regenerate:",
        "simulation-revise:",
        "simulation-packet-regenerate:",
        "formalize-lean-revision:",
        "formalizer-regenerate:",
        "theory-validation-retry:",
        "critic-regenerate:",
        "architect-plan-repair:",
        "theory-trace-repair:",
    )

    assert not {
        prefix for prefix in forbidden_task_prefixes if prefix in source
    }
    assert not hasattr(runtime_module, "_formalizer_workspace_architect_replan_task")
    assert not hasattr(runtime_module, "_source_workspace_architect_replan_task")
    assert not hasattr(runtime_module, "_workspace_architect_replan_task")

    config_fields = {field.name for field in fields(ResearchAgentRuntimeConfig)}
    removed_retry_controls = {
        "algorithm_engineer_generated_code_repair_yield_after_attempts",
        "simulation_evaluator_generated_code_repair_yield_after_attempts",
        "formalizer_lean_candidate_revision_max_attempts",
        "coding_agent_packet_validation_replan_after_attempts",
        "coding_agent_packet_validation_max_lineage_failures",
    }
    assert config_fields.isdisjoint(removed_retry_controls)


def test_source_owner_packet_exhaustion_blocks_without_architect_routing() -> None:
    question = OpenResearchQuestion(
        id="owner-local-packet-failure",
        title="Keep packet failures local",
        description="A source owner exhausted its model-visible validation loop.",
    )
    error = PacketValidationError(
        validation_label="source packet",
        attempts=2,
        errors=["required field is missing"],
        history=[],
        last_invalid_packet={"candidate": "incomplete"},
    )
    results = (
        runtime_module._theory_developer_packet_validation_failure_result(
            task=AgentTask(
                task_id="theory:owner-local-packet-failure",
                owner_subsystem="TheoryDeveloper",
                objective="Develop the theory artifact.",
                inputs={},
            ),
            question=question,
            exc=error,
        ),
        runtime_module._algorithm_engineer_packet_validation_failure_result(
            task=AgentTask(
                task_id="algorithm:owner-local-packet-failure",
                owner_subsystem="AlgorithmEngineer",
                objective="Develop and execute the algorithm artifact.",
                inputs={},
            ),
            question=question,
            theory_packet_id="theory:owner-local-packet-failure",
            simulation_manifest_id="",
            implementation_gaps=[],
            exc=error,
        ),
        runtime_module._simulation_engineer_packet_validation_failure_result(
            task=AgentTask(
                task_id="simulation:owner-local-packet-failure",
                owner_subsystem="SimulationEvaluator",
                objective="Develop and execute the simulation artifact.",
                inputs={
                    "architect_context": {
                        "empirical_evaluation_phase": "exploratory"
                    }
                },
            ),
            question=question,
            theory_packet_id="theory:owner-local-packet-failure",
            exc=error,
        ),
    )

    for result in results:
        assert result.status == "BLOCKED"
        assert result.next_task is None
        assert result.produced_artifacts
        assert result.failure_classification
        assert "Architect routing loop" in result.rationale


def test_model_reported_theory_gap_blocks_without_validation_or_repair_route() -> None:
    question = OpenResearchQuestion(
        id="honest-theory-gap",
        title="Preserve an unresolved mathematical blocker",
        description="The source model cannot identify the target from the assumptions.",
    )
    error = runtime_module.TheoryWorkspaceGapError(
        theory_gap={
            "summary": "The requested estimand is not identified.",
            "blocking_claims": ["identification"],
            "evidence_refs": ["workspace:problem_card"],
            "next_step": "Supply an identifying restriction.",
        },
        evidence={
            "artifact_kind": "TheoryDeveloperWorkspaceEvidence",
            "accepted": False,
            "model_owned_theory": True,
            "runtime_edited_theory": False,
        },
    )

    result = runtime_module._theory_developer_gap_result(
        task=AgentTask(
            task_id="theory:honest-theory-gap",
            owner_subsystem="TheoryDeveloper",
            objective="Develop the theory artifact.",
            inputs={},
        ),
        question=question,
        exc=error,
    )

    assert result.status == "BLOCKED"
    assert result.next_task is None
    assert result.failure_classification == "theory_developer_reported_gap"
    artifact = next(
        value
        for value in result.produced_artifacts.values()
        if value.get("artifact_kind") == "RuntimeTheoryDeveloperGap"
    )
    assert artifact["artifact_kind"] == "RuntimeTheoryDeveloperGap"
    assert artifact["model_owned_theory"] is True
    assert artifact["runtime_edited_theory"] is False
    assert artifact["kernel_verified"] is False
    assert "workspace_evidence" not in artifact
    assert artifact["workspace_evidence_id"] in result.produced_artifacts
    assert runtime_module.stable_hash(
        result.produced_artifacts[artifact["workspace_evidence_id"]]
    ) == artifact["workspace_evidence_hash"]
    assert result.evidence_entries[0].status == (
        "THEORY_GAP_RECORDED_NOT_ACCEPTED"
    )


def test_model_owned_theory_progress_continues_same_owner_by_reference() -> None:
    question = OpenResearchQuestion(
        id="long-horizon-theory",
        title="Continue a document-backed derivation",
        description="Preserve partial mathematics and continue without routing.",
    )
    checkpoint = {
        "artifact_kind": runtime_module.THEORY_WORKSPACE_PROGRESS_CHECKPOINT_KIND,
        "checkpoint_id": "theory_progress_checkpoint:phase-one",
        "question_id": question.id,
        "accepted": False,
        "kernel_verified": False,
        "progress": {
            "summary": "Established the leading expansion.",
            "next_step": "Control the remainder uniformly.",
        },
        "changed_artifact_names": ["theory_derivation_packet"],
        "changed_document_paths": ["derivations/main.md"],
        "proof_evidence_status": (
            "THEORY_PROGRESS_CHECKPOINT_NOT_PROOF_EVIDENCE"
        ),
    }
    error = runtime_module.TheoryWorkspaceProgressError(
        progress_checkpoint=checkpoint,
        evidence={
            "artifact_kind": "TheoryDeveloperWorkspaceEvidence",
            "artifact_id": "theory_workspace_progress:phase-one",
            "accepted": False,
            "kernel_verified": False,
        },
    )
    task = AgentTask(
        task_id="theory:long-horizon-theory",
        owner_subsystem="TheoryDeveloper",
        objective="Develop the theory artifact.",
        inputs={"question": runtime_module._question_to_payload(question)},
    )

    result = runtime_module._theory_developer_progress_result(
        task=task,
        question=question,
        exc=error,
    )

    assert result.status == "REVISE"
    assert result.next_task is not None
    assert result.next_task.owner_subsystem == "TheoryDeveloper"
    assert result.next_task.inputs["theory_progress_continuation_count"] == 1
    checkpoint_ref = result.next_task.inputs["theory_progress_checkpoint"]
    assert checkpoint_ref["artifact_kind"] == "RuntimeArtifactRef"
    assert checkpoint_ref["artifact_id"] == checkpoint["checkpoint_id"]
    assert "current_artifacts" not in checkpoint_ref
    assert checkpoint["checkpoint_id"] in result.produced_artifacts
    assert result.evidence_entries[0].status == (
        "THEORY_PROGRESS_RECORDED_NOT_ACCEPTED"
    )
    assert result.failure_classification == ""


def test_runtime_promotes_only_hash_bound_source_replication_evidence() -> None:
    body = {
        "artifact_kind": "SourceReplicationManifest",
        "artifact_id": "source_replication:q1",
        "question_id": "q1",
        "execution_status": "EXECUTED",
        "source_snapshot_hash": "a" * 64,
        "stdout_sha256": "b" * 64,
        "raw_stdout": "author output\n",
        "runtime_generated": True,
        "model_authored": False,
        "proof_evidence_status": (
            "SOURCE_REPLICATION_EXECUTION_NOT_PROOF_EVIDENCE"
        ),
    }
    manifest = {**body, "manifest_hash": runtime_module.stable_hash(body)}

    artifacts, refs = (
        runtime_module._source_replication_artifacts_from_theory_workspace(
            {"source_replication_manifests": [manifest]},
            question_id="q1",
        )
    )

    assert artifacts == {"source_replication:q1": manifest}
    assert refs == [
        {
            "artifact_id": "source_replication:q1",
            "manifest_hash": manifest["manifest_hash"],
            "execution_status": "EXECUTED",
            "source_snapshot_hash": "a" * 64,
            "stdout_sha256": "b" * 64,
            "proof_evidence_status": (
                "SOURCE_REPLICATION_EXECUTION_NOT_PROOF_EVIDENCE"
            ),
        }
    ]
    tampered = {**manifest, "raw_stdout": "changed\n"}
    assert runtime_module._source_replication_artifacts_from_theory_workspace(
        {"source_replication_manifests": [tampered]},
        question_id="q1",
    ) == ({}, [])


def _source_replication_checkpoint_packet(
    question: OpenResearchQuestion,
) -> dict[str, object]:
    source_body = {
        "artifact_kind": "SourceReplicationManifest",
        "artifact_id": f"source_replication:{question.id}",
        "question_id": question.id,
        "execution_status": "EXECUTED",
        "source_snapshot_hash": "a" * 64,
        "stdout_sha256": "b" * 64,
        "raw_stdout": "published output\n",
        "runtime_generated": True,
        "model_authored": False,
        "proof_evidence_status": (
            "SOURCE_REPLICATION_EXECUTION_NOT_PROOF_EVIDENCE"
        ),
    }
    source = {**source_body, "manifest_hash": runtime_module.stable_hash(source_body)}
    report = {
        "relative_path": "replication/report.md",
        "sha256": "c" * 64,
        "n_bytes": 128,
    }
    checkpoint_body = {
        "schema_version": 1,
        "artifact_kind": "SourceReplicationCheckpoint",
        "question_id": question.id,
        "workspace_id": f"source-workspace:{question.id}",
        "task_intent": dict(question.task_intent),
        "source_replication_manifest_ref": {
            "artifact_id": source["artifact_id"],
            "manifest_hash": source["manifest_hash"],
            "execution_status": "EXECUTED",
            "stdout_sha256": "b" * 64,
        },
        "report_document": report,
        "unresolved_gaps": [],
        "readiness_rationale": "The immutable source run is recorded.",
        "runtime_edited_source": False,
        "runtime_edited_report": False,
        "model_authored_report": True,
        "proof_evidence_status": (
            "SOURCE_REPLICATION_CHECKPOINT_NOT_PROOF_EVIDENCE"
        ),
        "kernel_verified": False,
    }
    checkpoint = {
        **checkpoint_body,
        "checkpoint_id": "source_replication_checkpoint:"
        + runtime_module.stable_hash(checkpoint_body)[:20],
    }
    workspace = {
        "schema_version": 1,
        "artifact_kind": "TheoryDeveloperWorkspaceEvidence",
        "artifact_id": f"source_replication_workspace:{question.id}",
        "workspace_id": checkpoint["workspace_id"],
        "question_id": question.id,
        "disposition": "SOURCE_REPLICATION_CHECKPOINT_COMMITTED",
        "checkpoint_committed": True,
        "model_owned_source_report": True,
        "model_owned_theory": False,
        "runtime_edited_source": False,
        "runtime_edited_theory": False,
        "kernel_verified": False,
        "submitted_core_packet_hash": runtime_module.stable_hash(checkpoint),
        "changed_document_paths": [report["relative_path"]],
        "theory_workspace_manifest": {"documents": [report]},
        "source_replication_runs": 1,
        "source_replication_manifests": [source],
    }
    return {**checkpoint, "llm_client_tool_loop": workspace}


def test_source_only_checkpoint_ends_runtime_without_fixed_pipeline_handoff() -> None:
    question = OpenResearchQuestion(
        id="source-only-runtime",
        title="Source-only runtime",
        description="Run and report one immutable published source.",
        task_intent={
            "source_replication": "required",
            "theory": "optional",
            "scientific_code": "not_applicable",
            "empirical": "not_applicable",
            "formal": "not_applicable",
            "unresolved_gaps": "required",
        },
    )
    packet = _source_replication_checkpoint_packet(question)

    class SourceOnlyTheoryDeveloper:
        config = None
        provider = None
        research_source_execution = object()

        def derive(self, *_args, **_kwargs):
            return packet

    subsystem = runtime_module.TheoryDeveloperRuntimeSubsystem(
        theory_developer=SourceOnlyTheoryDeveloper(),  # type: ignore[arg-type]
        n_runs=10,
        seed=17,
    )
    task = AgentTask(
        task_id="theory:source-only-runtime",
        owner_subsystem="TheoryDeveloper",
        objective="Complete the source-only task.",
        inputs={
            "question": runtime_module._question_to_payload(question),
            "architect_context": {},
        },
    )

    result = subsystem.run(
        task,
        BlackboardState(project_id="source-only-runtime"),
    )

    assert result.status == "ACCEPTED"
    assert result.next_task is None
    assert result.failure_classification == ""
    assert any(
        artifact.get("artifact_kind") == "SourceReplicationCheckpoint"
        for artifact in result.produced_artifacts.values()
    )
    assert any(
        artifact.get("artifact_kind") == "SourceReplicationManifest"
        for artifact in result.produced_artifacts.values()
    )
    assert all(
        artifact.get("artifact_kind")
        not in {
            "TheoryDerivationPacket",
            "SimulationManifest",
            "FormalizationManifest",
        }
        for artifact in result.produced_artifacts.values()
    )
    assert result.evidence_entries[0].status == (
        "SOURCE_EXECUTION_RECORDED_REQUIRES_HIDDEN_EVALUATION"
    )


def test_full_runtime_honors_required_source_replication_before_model_route(
    tmp_path: Path,
) -> None:
    question = OpenResearchQuestion(
        id="integrated-source-only-runtime",
        title="Integrated source-only runtime",
        description="Run and report one immutable published source.",
        task_intent={
            "source_replication": "required",
            "theory": "not_applicable",
            "scientific_code": "not_applicable",
            "empirical": "not_applicable",
            "formal": "not_applicable",
            "novelty": "not_applicable",
            "unresolved_gaps": "required",
        },
    )
    exact_haiku_config = SimpleNamespace(
        provider_name="anthropic",
        model=LIVE_EVALUATION_CLAUDE_MODEL,
        model_tier=LIVE_EVALUATION_CLAUDE_MODEL_TIER,
        serious_model=LIVE_EVALUATION_CLAUDE_MODEL,
        serious_model_tier=LIVE_EVALUATION_CLAUDE_MODEL_TIER,
        max_tokens=1_000,
        serious_max_tokens=1_000,
        temperature=0.0,
    )

    class Provider:
        provider_name = "anthropic"

    class SimulationRequestingArchitect:
        config = exact_haiku_config
        provider = Provider()
        metric_semantic_reviewer = None

        @staticmethod
        def propose(*, question, architect_context, runtime_config):  # type: ignore[no-untyped-def]
            del question, runtime_config
            evidence_contract = dict(
                architect_context["runtime_requested_evidence_contract"]
            )
            return {
                "packet_id": "architect:integrated-source-only",
                "problem_analysis": {},
                "evidence_contract": evidence_contract,
                "subsystem_execution_plan": [
                    {
                        "subsystem": "TheoryDeveloper",
                        "objective": "Execute and report the immutable source.",
                        "expected_artifacts": [
                            "source_replication_checkpoint"
                        ],
                        "acceptance_gate": (
                            "a source-replication checkpoint is recorded"
                        ),
                    }
                ],
                "retrieval_strategy": {},
                "iteration_policy": {},
                "next_actions": [
                    {
                        "owner_agent": "SimulationEvaluator",
                        "action": "Run an unrelated simulation lane.",
                        "acceptance_gate": "simulation evidence is recorded",
                    }
                ],
                "evidence_boundary": "Architect routing is not scientific evidence.",
            }

    class SourceOnlyTheoryDeveloper:
        config = exact_haiku_config
        provider = Provider()
        research_sources = None
        research_source_execution = object()

        @staticmethod
        def derive(question, **_kwargs):  # type: ignore[no-untyped-def]
            return _source_replication_checkpoint_packet(question)

    manifest = runtime_module.run_research_agent_runtime(
        [question],
        tmp_path,
        theory_developer=SourceOnlyTheoryDeveloper(),  # type: ignore[arg-type]
        architect_coordinator=SimulationRequestingArchitect(),  # type: ignore[arg-type]
        config=ResearchAgentRuntimeConfig(
            evaluation_mode="research_eval",
            formal_verification_policy="optional",
            max_iterations=4,
            theory_scratch_max_runs=0,
        ),
    )

    runtime_result = json.loads(
        Path(manifest["artifacts"]["per_question_results"][0]).read_text(
            encoding="utf-8"
        )
    )
    traces = runtime_result["traces"]
    assert [(row["subsystem"], row["status"]) for row in traces] == [
        ("ArchitectCoordinator", "REROUTE"),
        ("TheoryDeveloper", "ACCEPTED"),
    ]
    initial_routing = traces[0]["observations"][0]["payload"][
        "initial_routing"
    ]
    assert initial_routing["requested_subsystem"] == "SimulationEvaluator"
    assert initial_routing["selected_subsystem"] == "TheoryDeveloper"
    assert initial_routing["model_route_honored_exactly"] is False
    assert manifest["status_counts"] == {"ACCEPTED": 1}
    assert manifest["research_evaluation_summary"][
        "all_questions_research_eval_complete"
    ] is True
    row = manifest["research_evaluation_summary"]["rows"][0]
    assert row["required_capability_checks"] == [
        "source_replication_checkpoint_recorded",
        "source_replication_unresolved_gap_disclosure_present",
    ]
    assert row["requirements"]["critic_research_acceptance"] is False
    assert manifest["n_runtime_architect_coordinator_traces"] == 1
    assert manifest["n_generated_simulation_sandbox_executed"] == 0
    assert manifest["n_kernel_verified_subclaims"] == 0
    assert manifest["formal_closure_summary"]["formal_closure_status"] == (
        "FORMAL_CLOSURE_NOT_APPLICABLE"
    )


def test_runtime_stores_theory_tool_history_as_separate_evidence() -> None:
    question = OpenResearchQuestion(
        id="detached-theory-evidence",
        title="Detached theory evidence",
        description="Keep mathematical content separate from tool history.",
        task_intent={
            "theory": "required",
            "scientific_code": "not_applicable",
            "empirical": "not_applicable",
            "formal": "not_applicable",
        },
    )
    packet_id = "theory_derivation:detached"
    workspace_id = "theory_workspace:detached"
    packet = {
        "artifact_kind": "TheoryDerivationPacket",
        "packet_id": packet_id,
        "question": runtime_module._question_to_payload(question),
        "theory_derivation_contract": {},
        "theory_derivation_packet": {},
        "estimator_specs": [],
        "theorem_cards": [],
        "formalization_requests": [],
        "llm_client_tool_loop": {
            "artifact_kind": "TheoryDeveloperWorkspaceEvidence",
            "artifact_id": workspace_id,
            "workspace_id": workspace_id,
            "workspace_operation": "initial_discovery",
            "accepted": True,
            "model_owned_theory": True,
            "runtime_edited_theory": False,
            "history": [{"large_transport_payload": "x" * 2000}],
        },
    }

    class StaticTheoryDeveloper:
        config = None
        provider = None
        research_source_execution = None

        def derive(self, *_args, **_kwargs):
            return packet

    result = runtime_module.TheoryDeveloperRuntimeSubsystem(
        theory_developer=StaticTheoryDeveloper(),  # type: ignore[arg-type]
        n_runs=10,
        seed=17,
    ).run(
        AgentTask(
            task_id="theory:detached-theory-evidence",
            owner_subsystem="TheoryDeveloper",
            objective="Author theory.",
            inputs={
                "question": runtime_module._question_to_payload(question),
                "architect_context": {
                    "architect_runtime_plan": {
                        "evidence_contract": {
                            "dimension_requirements": {
                                "theory": "required",
                                "scientific_code": "not_applicable",
                                "empirical": "not_applicable",
                                "formal": "not_applicable",
                            }
                        }
                    },
                    "runtime_requested_evidence_contract": (
                        runtime_module._runtime_requested_evidence_contract(
                            formal_verification_policy="optional",
                            evaluation_mode="research_eval",
                            task_intent=question.task_intent,
                        )
                    )
                },
            },
        ),
        BlackboardState(project_id=question.id),
    )

    stored_packet = result.produced_artifacts[packet_id]
    stored_workspace = result.produced_artifacts[workspace_id]
    assert "llm_client_tool_loop" not in stored_packet
    assert "large_transport_payload" not in str(stored_packet)
    assert stored_workspace["history"][0]["large_transport_payload"] == (
        "x" * 2000
    )
    assert stored_workspace["runtime_source_theory_packet_id"] == packet_id
    assert stored_workspace["runtime_source_theory_packet_hash"] == (
        runtime_module.stable_hash(stored_packet)
    )
    assert stored_workspace["runtime_storage_role"] == (
        "SEPARATE_WORKSPACE_EVIDENCE_NOT_THEORY_CONTENT"
    )
    assert result.next_task is not None
    assert result.next_task.owner_subsystem == "ArchitectCoordinator"
    assert result.next_task.inputs["runtime_architect_operation"] == (
        runtime_module.RUNTIME_ARCHITECT_OPERATION_THEORY_PREFLIGHT
    )
    assert "architect_metric_protocol_gate" not in result.next_task.inputs[
        "architect_context"
    ]


def test_optional_theory_compiles_existing_plan_without_architect_replan() -> None:
    question = OpenResearchQuestion(
        id="optional-theory-direct-plan-transition",
        title="Optional theory direct plan transition",
        description="Build an executable estimator from supporting theory.",
        task_intent={
            "theory": "optional",
            "scientific_code": "required",
            "empirical": "not_applicable",
            "formal": "not_applicable",
        },
    )
    packet_id = "theory_derivation:optional-direct-transition"
    packet = {
        "artifact_kind": "TheoryDerivationPacket",
        "packet_id": packet_id,
        "question": runtime_module._question_to_payload(question),
        "theory_derivation_contract": {},
        "theory_derivation_packet": {},
        "estimator_specs": [{"id": "estimator:optional-direct-transition"}],
        "theorem_cards": [],
        "formalization_requests": [],
    }

    class StaticTheoryDeveloper:
        config = None
        provider = None
        research_source_execution = None

        def derive(self, *_args, **_kwargs):
            return packet

    contract = runtime_module._runtime_requested_evidence_contract(
        formal_verification_policy="optional",
        evaluation_mode="research_eval",
        task_intent=question.task_intent,
    )
    result = runtime_module.TheoryDeveloperRuntimeSubsystem(
        theory_developer=StaticTheoryDeveloper(),  # type: ignore[arg-type]
        n_runs=37,
        seed=19,
    ).run(
        AgentTask(
            task_id="theory:optional-direct-transition",
            owner_subsystem="TheoryDeveloper",
            objective="Author supporting theory and an estimator interface.",
            inputs={
                "question": runtime_module._question_to_payload(question),
                "architect_context": {
                    "architect_coordinator_proposal_id": "architect:optional-direct",
                    "architect_runtime_plan": {
                        "packet_id": "architect:optional-direct",
                        "evidence_contract": contract,
                        "subsystem_execution_plan": [
                            {"subsystem": "TheoryDeveloper"},
                            {"subsystem": "AlgorithmEngineer"},
                            {"subsystem": "GeneratedCodeSemanticReviewer"},
                            {"subsystem": "CriticEvaluator"},
                        ],
                    },
                    "runtime_requested_evidence_contract": contract,
                },
            },
        ),
        BlackboardState(project_id=question.id),
    )

    assert result.status == "REROUTE"
    assert result.next_task is not None
    assert result.next_task.owner_subsystem == "AlgorithmEngineer"
    assert result.next_task.inputs["theory_packet_id"] == packet_id
    assert result.next_task.inputs["n_runs"] == 37
    assert result.next_task.inputs["seed"] == 19
    assert "runtime_architect_operation" not in result.next_task.inputs
    next_context = result.next_task.inputs["architect_context"]
    assert next_context["environment_feedback"]["compiled_next_owner"] == (
        "AlgorithmEngineer"
    )
    assert next_context["runtime_feedback_loop"]["handoff"] == (
        "validated_theory_to_planned_workspace"
    )
    assert "without another model routing call" in result.rationale


def test_runtime_records_claim_revision_delta_against_exact_packet_bytes() -> None:
    question = OpenResearchQuestion(
        id="claim-revision-runtime",
        title="Claim revision runtime",
        description="Expose a document-authoritative theory revision by reference.",
        task_intent={
            "theory": "required",
            "scientific_code": "not_applicable",
            "empirical": "not_applicable",
            "formal": "not_applicable",
        },
    )

    def packet(packet_id: str, *, status: str, depends_on: list[str]) -> dict:
        return {
            "artifact_kind": "TheoryDerivationPacket",
            "packet_id": packet_id,
            "question": runtime_module._question_to_payload(question),
            "theory_content_authority": THEORY_WORKSPACE_CONTENT_AUTHORITY,
            "theory_derivation_contract": {},
            "theory_derivation_packet": {
                "claim_index": [
                    {
                        "id": "C0",
                        "kind": "assumption",
                        "document_path": "theory.md",
                        "anchor": "C0",
                        "depends_on": [],
                        "status": "SUPPORTED",
                    },
                    {
                        "id": "C1",
                        "kind": "theorem",
                        "document_path": "theory.md",
                        "anchor": "C1",
                        "depends_on": depends_on,
                        "status": status,
                    },
                ]
            },
            "estimator_specs": [],
            "theorem_cards": [],
            "formalization_requests": [],
            "theory_workspace_manifest": {
                "document_set_hash": "d" * 64,
                "documents": [
                    {
                        "document_id": "theory-document",
                        "relative_path": "theory.md",
                        "sha256": "e" * 64,
                        "byte_size": 100,
                    }
                ],
            },
        }

    parent_packet = packet(
        "theory_derivation:claim-parent",
        status="OPEN",
        depends_on=["C0"],
    )
    revised_packet = packet(
        "theory_derivation:claim-revised",
        status="SUPPORTED",
        depends_on=[],
    )

    class StaticTheoryDeveloper:
        config = None
        provider = None
        research_source_execution = None

        def derive(self, *_args, **_kwargs):
            return revised_packet

    blackboard = BlackboardState(
        project_id=question.id,
        artifacts={parent_packet["packet_id"]: parent_packet},
    )
    result = runtime_module.TheoryDeveloperRuntimeSubsystem(
        theory_developer=StaticTheoryDeveloper(),  # type: ignore[arg-type]
        n_runs=10,
        seed=17,
    ).run(
        AgentTask(
            task_id="theory:claim-revision-runtime",
            owner_subsystem="TheoryDeveloper",
            objective="Revise the theory.",
            inputs={
                "question": runtime_module._question_to_payload(question),
                "architect_context": {
                    "previous_theory_packet_id": parent_packet["packet_id"],
                    "theory_packet_id": parent_packet["packet_id"],
                    "runtime_requested_evidence_contract": (
                        runtime_module._runtime_requested_evidence_contract(
                            formal_verification_policy="optional",
                            evaluation_mode="research_eval",
                            task_intent=question.task_intent,
                        )
                    ),
                },
            },
        ),
        blackboard,
    )

    stored_packet = result.produced_artifacts[revised_packet["packet_id"]]
    deltas = [
        artifact
        for artifact in result.produced_artifacts.values()
        if artifact.get("artifact_kind")
        == THEORY_CLAIM_REVISION_DELTA_KIND
    ]
    assert len(deltas) == 1
    delta = deltas[0]
    assert delta["parent_theory_packet_hash"] == runtime_module.stable_hash(
        parent_packet
    )
    assert delta["revised_theory_packet_hash"] == runtime_module.stable_hash(
        stored_packet
    )
    assert delta["changed_claim_refs"][0]["claim_id"] == "C1"
    materials = [
        artifact
        for artifact in result.produced_artifacts.values()
        if artifact.get("artifact_kind")
        == "RuntimeTheoryInformedMetricProtocolMaterial"
    ]
    assert len(materials) == 1
    assert materials[0]["theory_claim_revision_delta"] == delta
    assert "theorem statement" not in str(delta).lower()


def test_resumed_theory_revision_hydrates_compact_parent_reference_once() -> None:
    question = OpenResearchQuestion(
        id="compact-parent-resume",
        title="Compact parent resume",
        description="Resolve the exact parent only inside TheoryDeveloper execution.",
        task_intent={
            "theory": "required",
            "scientific_code": "not_applicable",
            "empirical": "not_applicable",
            "formal": "not_applicable",
        },
    )
    sentinel = "LARGE_PARENT_SENTINEL:" + "parent-mathematics-" * 200
    parent_packet = {
        "artifact_kind": "TheoryDerivationPacket",
        "packet_id": "theory_derivation:compact-parent",
        "question": runtime_module._question_to_payload(question),
        "problem_card": {"research_setup": sentinel},
        "theory_derivation_contract": {},
        "theory_derivation_packet": {"workspace_summary": sentinel},
        "estimator_specs": [],
        "theorem_cards": [],
        "formalization_requests": [],
    }
    revised_packet = deepcopy(parent_packet)
    revised_packet["packet_id"] = "theory_derivation:compact-revised"
    revised_packet["problem_card"] = {"research_setup": "Revised setup."}
    revised_packet["theory_derivation_packet"] = {
        "workspace_summary": "A fresh model-authored revision."
    }
    feedback = {
        "artifact_kind": "RuntimeMetricProtocolPreExecutionReviewObservation",
        "feedback_id": "metric-protocol-theory-feedback:compact-parent",
        "question_id": question.id,
        "source_theory_packet_id": parent_packet["packet_id"],
        "source_theory_packet_hash": runtime_module.stable_hash(parent_packet),
        "source_metric_protocol_rejection_manifest_id": (
            "metric-rejection:compact-parent"
        ),
        "execution_authorized": False,
        "upstream_theory_revision_count": 1,
        "continuation_budget_authority": "AgentRuntime.max_iterations",
        "findings": [
            {
                "finding_id": "metric-finding:compact-parent",
                "summary": "One assumption requires a model-authored revision.",
            }
        ],
    }
    task = AgentTask(
        task_id="theory:compact-parent-resume",
        owner_subsystem="TheoryDeveloper",
        objective="Revise the exact parent theory from independent feedback.",
        inputs={
            "question": runtime_module._question_to_payload(question),
            "architect_context": {
                "previous_theory_packet_id": parent_packet["packet_id"],
                "theory_packet_id": parent_packet["packet_id"],
                "environment_feedback": feedback,
                "runtime_requested_evidence_contract": (
                    runtime_module._runtime_requested_evidence_contract(
                        formal_verification_policy="optional",
                        evaluation_mode="research_eval",
                        task_intent=question.task_intent,
                    )
                ),
            },
        },
    )
    _, continuation, continuation_artifacts = (
        runtime_module.materialize_agent_task_continuation(task)
    )
    assert sentinel not in json.dumps(
        {"continuation": continuation, "artifacts": continuation_artifacts}
    )
    resumed_task = restore_agent_task_continuation(
        continuation,
        continuation_artifacts,
    )

    captured_context: dict[str, object] = {}
    model_calls: list[str] = []

    class CapturingTheoryDeveloper:
        config = None
        provider = None
        research_source_execution = None

        def derive(self, _question, **kwargs):
            model_calls.append("derive")
            captured_context.update(
                deepcopy(dict(kwargs.get("architect_context", {})))
            )
            return deepcopy(revised_packet)

    result = runtime_module.TheoryDeveloperRuntimeSubsystem(
        theory_developer=CapturingTheoryDeveloper(),  # type: ignore[arg-type]
        n_runs=10,
        seed=17,
    ).run(
        resumed_task,
        BlackboardState(
            project_id=question.id,
            artifacts={parent_packet["packet_id"]: parent_packet},
        ),
    )

    binding_key = runtime_module.THEORY_DEVELOPER_REVISION_BINDING_CONTEXT_KEY
    resolved_key = (
        runtime_module.THEORY_DEVELOPER_RESOLVED_PARENT_MATERIAL_CONTEXT_KEY
    )
    binding = captured_context[binding_key]
    assert isinstance(binding, dict)
    assert "theory_material" not in binding
    assert binding["parent_theory_packet_ref"] == runtime_artifact_reference(
        parent_packet["packet_id"],
        parent_packet,
    )
    assert sentinel not in json.dumps(binding)
    assert sentinel in json.dumps(captured_context[resolved_key])

    assert result.next_task is not None
    downstream_context = result.next_task.inputs["architect_context"]
    assert binding_key not in downstream_context
    assert resolved_key not in downstream_context
    assert "metric_protocol_prior_theory_material" not in downstream_context
    assert sentinel not in json.dumps(asdict(result), default=str)

    blocked = runtime_module.TheoryDeveloperRuntimeSubsystem(
        theory_developer=CapturingTheoryDeveloper(),  # type: ignore[arg-type]
        n_runs=10,
        seed=17,
    ).run(
        resumed_task,
        BlackboardState(project_id=question.id),
    )
    assert blocked.status == "BLOCKED"
    assert len(model_calls) == 1


def test_architect_source_escalation_requires_independent_semantic_conflict() -> None:
    question = OpenResearchQuestion(
        id="reject-routine-architect-routing",
        title="Reject routine Architect routing",
        description="Only independent cross-workspace conflicts may escalate.",
    )
    task = AgentTask(
        task_id="algorithm:reject-routine-architect-routing",
        owner_subsystem="AlgorithmEngineer",
        objective="Own the generated source.",
        inputs={},
    )

    with pytest.raises(ValueError, match="independent semantic-review conflict"):
        runtime_module._independent_semantic_review_architect_escalation_task(
            task=task,
            question=question,
            context={},
            revision_feedback={
                "feedback_source": "AlgorithmEngineer",
                "failure_classification": "sandbox_execution_failed",
            },
            source_artifact_id="algorithm:failed",
        )


def test_terminal_critic_blocks_unreviewed_required_theory_before_model_call() -> None:
    question = OpenResearchQuestion(
        id="critic-requires-independent-theory-review",
        title="Require isolated theory review",
        description="Do not let a terminal critic self-ratify an unreviewed theory.",
        task_intent={
            "theory": "required",
            "scientific_code": "not_applicable",
            "empirical": "not_applicable",
            "formal": "not_applicable",
        },
    )
    theory_packet_id = "theory_derivation:unreviewed"
    theory_packet = {
        "artifact_kind": "TheoryDerivationPacket",
        "packet_id": theory_packet_id,
        "question": runtime_module._question_to_payload(question),
    }

    class NeverCalledCritic:
        def __init__(self) -> None:
            self.calls: list[dict] = []

        def propose(self, **kwargs):
            self.calls.append(kwargs)
            raise AssertionError("Critic model must not see unreviewed required theory")

    critic = NeverCalledCritic()
    result = CriticEvaluatorRuntimeSubsystem(
        proposal_agent=critic,  # type: ignore[arg-type]
    ).run(
        AgentTask(
            task_id="critic:unreviewed-theory",
            owner_subsystem="CriticEvaluator",
            objective="Evaluate the requested theory evidence.",
            inputs={
                "question": runtime_module._question_to_payload(question),
                "theory_packet_id": theory_packet_id,
                "architect_context": {
                    "runtime_requested_evidence_contract": (
                        runtime_module._runtime_requested_evidence_contract(
                            formal_verification_policy="optional",
                            evaluation_mode="research_eval",
                            task_intent=question.task_intent,
                        )
                    )
                },
            },
        ),
        BlackboardState(
            project_id=question.id,
            artifacts={theory_packet_id: theory_packet},
        ),
    )

    assert critic.calls == []
    assert result.status == "BLOCKED"
    assert result.failure_classification == (
        "required_independent_theory_review_missing"
    )
    missing = next(iter(result.produced_artifacts.values()))
    assert missing["artifact_kind"] == "RuntimeRequiredTheoryReviewMissing"
    assert missing["model_call_authorized"] is False
    assert result.evidence_entries[0].status == (
        "MISSING_BLOCKED_BEFORE_CRITIC_MODEL_CALL"
    )


def test_final_critic_does_not_restart_exhausted_formalizer_for_missing_proof() -> None:
    question = OpenResearchQuestion(
        id="terminal-critic-formal-gap",
        title="Stop after the bounded formal workspace",
        description="Record a required but unproved theorem without restarting Lean.",
    )
    artifact_ids = {
        "retrieval_memory_manifest_id": "retrieval_memory_manifest:terminal",
        "theory_packet_id": "theory_derivation:terminal",
        "simulation_manifest_id": "simulation_manifest:terminal",
        "algorithm_sandbox_manifest_id": "algorithm_sandbox_manifest:terminal",
        "formalization_manifest_id": "formalization_manifest:terminal",
    }
    artifacts = {
        artifact_ids["retrieval_memory_manifest_id"]: {
            "manifest_id": artifact_ids["retrieval_memory_manifest_id"],
        },
        artifact_ids["theory_packet_id"]: {
            "packet_id": artifact_ids["theory_packet_id"],
        },
        artifact_ids["simulation_manifest_id"]: {
            "manifest_id": artifact_ids["simulation_manifest_id"],
        },
        artifact_ids["algorithm_sandbox_manifest_id"]: {
            "manifest_id": artifact_ids["algorithm_sandbox_manifest_id"],
        },
        artifact_ids["formalization_manifest_id"]: {
            "manifest_id": artifact_ids["formalization_manifest_id"],
            "counts": {"formal_gap": 1, "kernel_verified": 0},
            "full_frontier_theorem_proved": False,
        },
    }
    result = CriticEvaluatorRuntimeSubsystem(
        runtime_config=ResearchAgentRuntimeConfig(
            formal_verification_policy="required"
        )
    ).run(
        AgentTask(
            task_id="critic:terminal-formal-gap",
            owner_subsystem="CriticEvaluator",
            objective="Record the final evidence decision.",
            inputs={
                "question": {
                    "id": question.id,
                    "title": question.title,
                    "description": question.description,
                    "tags": [],
                },
                **artifact_ids,
                "architect_context": {
                    "architect_runtime_plan": {
                        "evidence_contract": {
                            "formal_verification_policy": "required",
                            "formal_required_for_final": True,
                        },
                        "subsystem_execution_plan": [
                            {
                                "subsystem": "CriticEvaluator",
                                "objective": "Audit final evidence.",
                                "acceptance_gate": "Respect kernel authority.",
                            }
                        ],
                    }
                },
            },
        ),
        BlackboardState(project_id="terminal-critic", artifacts=artifacts),
    )

    assert result.status == "BLOCKED"
    assert result.next_task is None
    assert result.failure_classification == "formal_required_unverified"
    critic_manifest = next(
        artifact
        for artifact in result.produced_artifacts.values()
        if isinstance(artifact, dict)
        and artifact.get("artifact_kind") == "RuntimeCriticEvaluatorManifest"
    )
    assert critic_manifest["research_source_audit"] == {
        "snapshot_hash": "",
        "author_read_ref_count": 0,
        "cited_ref_count": 0,
        "resolved_exact_source_count": 0,
        "unresolved_cited_ref_count": 0,
        "source_text_persisted": False,
    }


def test_summary_flags_and_subclaims_do_not_satisfy_exact_theorem_gate() -> None:
    decision = runtime_module._critic_evidence_contract_decision(
        critic_control={
            "evidence_contract": {"formal_verification_policy": "required"}
        },
        formalization_manifest={
            "counts": {"formal_gap": 0, "kernel_verified": 12},
            "full_frontier_theorem_proved": True,
        },
        revision_required=False,
    )

    assert decision["kernel_verified"] == 12
    assert decision["source_theorem_kernel_verified"] is False
    assert decision["formal_satisfied"] is False
    assert decision["runtime_status"] == "BLOCKED"
    assert decision["failure_classification"] == "formal_required_unverified"


@pytest.mark.parametrize(
    ("disposition", "failure_classification"),
    (
        ("REJECT", "critic_scientific_rejected"),
        ("INCONCLUSIVE", "critic_scientific_inconclusive"),
    ),
)
def test_critic_scientific_disposition_blocks_without_retry(
    disposition: str,
    failure_classification: str,
) -> None:
    decision = runtime_module._critic_evidence_contract_decision(
        critic_control={
            "evidence_contract": {"formal_verification_policy": "optional"}
        },
        formalization_manifest={"counts": {"formal_gap": 1}},
        revision_required=False,
        scientific_disposition=disposition,
    )

    assert decision["runtime_status"] == "BLOCKED"
    assert decision["scientific_disposition"] == disposition
    assert decision["failure_classification"] == failure_classification


def test_critic_acceptance_keeps_optional_formalization_nonblocking() -> None:
    decision = runtime_module._critic_evidence_contract_decision(
        critic_control={
            "evidence_contract": {"formal_verification_policy": "optional"}
        },
        formalization_manifest={"counts": {"formal_gap": 1}},
        revision_required=False,
        scientific_disposition="ACCEPT",
    )

    assert decision["runtime_status"] == "ACCEPTED"
    assert decision["scientific_disposition"] == "ACCEPT"
    assert decision["final_acceptance_status"] == (
        "RESEARCH_CANDIDATE_ACCEPTED_WITH_FORMAL_GAPS"
    )


def test_workspace_parent_lineage_reopens_only_after_parent_artifact_changes() -> None:
    formalizer_parents = runtime_module._runtime_workspace_parent_artifact_ids(
        "FormalizationEvaluator",
        {
            "theory_packet_id": "theory:a",
            "algorithm_sandbox_manifest_id": "algorithm:a",
            "simulation_manifest_id": "simulation:a",
        },
    )

    assert formalizer_parents == {"theory_packet_id": "theory:a"}


def test_source_workspace_prompts_give_tools_to_the_source_owner() -> None:
    for prompt in (
        ALGORITHM_ENGINEER_CODE_WORKSPACE_SYSTEM_PROMPT,
        SIMULATION_ENGINEER_CODE_WORKSPACE_SYSTEM_PROMPT,
    ):
        assert "complete executable Python or R" in prompt
        assert "Use the supplied\nclient tools" in prompt
        assert "Do not run tools" not in prompt
    assert "never supplies a correction rule" in prompt
    assert "test the complete\nimmutable public ABI" in (
        ALGORITHM_ENGINEER_CODE_WORKSPACE_SYSTEM_PROMPT
    )
    assert "valid and rejected requests" in (
        ALGORITHM_ENGINEER_CODE_WORKSPACE_SYSTEM_PROMPT
    )
    assert "request's data scope" in SIMULATION_ENGINEER_CODE_WORKSPACE_SYSTEM_PROMPT
    assert "consumer control flow" in SIMULATION_ENGINEER_CODE_WORKSPACE_SYSTEM_PROMPT
    assert "literal,\npunctuation-sensitive JSON key" in (
        SIMULATION_ENGINEER_CODE_WORKSPACE_SYSTEM_PROMPT
    )
    assert "measurement_interface_failure is a failed\nsource ABI" in (
        SIMULATION_ENGINEER_CODE_WORKSPACE_SYSTEM_PROMPT
    )


def test_unreviewed_compiled_lean_candidate_cannot_claim_generic_kernel_proof() -> None:
    fields = runtime_module._formalizer_candidate_kernel_scope_fields(
        local_lean_compiled=True
    )

    assert fields["kernel_verified"] is False
    assert fields["candidate_kernel_verified"] is True
    assert fields["candidate_kernel_verified_scope"] == "candidate_artifact_only"


def test_zero_materialized_gap_rows_do_not_claim_formal_closure() -> None:
    summary = runtime_module._runtime_formal_closure_summary(
        completion_summary={
            "rows": [
                {"question_id": "q1", "formal_satisfied": False},
                {"question_id": "q2", "formal_satisfied": True},
            ]
        },
        n_materialized_formal_gap_rows=0,
    )

    assert summary["n_materialized_formal_gap_rows"] == 0
    assert summary["formal_gap_inventory_status"] == (
        "NO_MATERIALIZED_GAP_ROWS"
    )
    assert summary["n_questions_formal_unverified"] == 1
    assert summary["formal_closure_status"] == "FORMAL_CLOSURE_UNVERIFIED"
    assert summary["formal_closure_verified_for_all_questions"] is False


def test_formal_not_applicable_is_not_reported_as_unverified() -> None:
    summary = runtime_module._runtime_formal_closure_summary(
        completion_summary={
            "rows": [
                {
                    "question_id": "empirical-only",
                    "formal_requirement": "not_applicable",
                    "formal_satisfied": False,
                }
            ]
        },
        n_materialized_formal_gap_rows=0,
    )

    assert summary["n_questions_formal_applicable"] == 0
    assert summary["n_questions_formal_not_applicable"] == 1
    assert summary["n_questions_formal_unverified"] == 0
    assert summary["formal_closure_status"] == (
        "FORMAL_CLOSURE_NOT_APPLICABLE"
    )
    assert summary["formal_closure_verified_for_all_questions"] is False


def test_formalizer_observation_summary_keeps_distinct_workspace_history() -> None:
    base_payload = {
        "model_owned_lean_code": True,
        "runtime_selected_lean_code": False,
        "candidate_source_hash": "source-hash",
        "source_updates": 1,
        "local_lean_checks": 2,
        "n_formal_rag_tool_calls": 3,
        "latest_check_compiled": True,
    }
    first = {
        "question_id": "generic-formalizer-summary",
        "evidence_id": "evidence:first",
        "artifact_id": "workspace:first",
        "evidence_type": "formalizer_lean_candidate_client_tool_loop",
        "payload": base_payload,
    }
    second = {
        "question_id": "generic-formalizer-summary",
        "evidence_id": "evidence:second",
        "artifact_id": "workspace:second",
        "evidence_type": "formalizer_lean_candidate_client_tool_loop",
        "payload": {
            **base_payload,
            "source_updates": 0,
            "local_lean_checks": 1,
            "n_formal_rag_tool_calls": 2,
        },
    }

    summary = runtime_module._runtime_formalizer_client_tool_observation_summary(
        [first, second, first]
    )

    assert summary["n_workspaces_observed"] == 2
    assert summary["n_source_updates"] == 1
    assert summary["n_local_lean_checks"] == 3
    assert summary["n_formal_rag_tool_calls"] == 5
    assert summary["n_compiled_checkpoints"] == 2


@pytest.mark.parametrize(
    "evidence_type",
    [
        "formalizer_lean_candidate_client_tool_loop",
        "formalizer_packet_validation_failure",
    ],
)
def test_formalizer_raw_feedback_revision_does_not_require_final_compile(
    evidence_type: str,
) -> None:
    observed, loops, revisions = _formalizer_revision_summary(
        [
            {
                "evidence_type": evidence_type,
                "payload": {
                    "candidate_source_hash": "source-hash",
                    "source_changed": True,
                    "source_updates": 2,
                    "local_lean_checks": 3,
                    "latest_check_compiled": False,
                    "provider": "anthropic",
                    "model": "claude-haiku-4-5-20251001",
                    "model_owned_lean_code": True,
                    "runtime_selected_lean_code": False,
                },
            }
        ]
    )

    assert (observed, loops, revisions) == (True, 1, 1)


def _full_evidence_context(question_id: str) -> dict[str, object]:
    return {
        "architect_coordinator_proposal_id": "architect:generic",
        "theory_packet_id": "theory:generic",
        "implementation_gaps": [{"estimator_id": "estimator:generic"}],
        "empirical_evaluation_phase": "exploratory",
        "architect_metric_protocol_gate": {
            "algorithm_execution_available": True,
            "confirmatory_simulation_authorized": False,
            "execution_authorized": False,
            "preflight_acceptance_id": "preflight:generic",
        },
        "architect_runtime_plan": {
            "evidence_contract": {
                "evaluation_mode": "capability_eval",
                "formal_verification_policy": "required",
                "formal_required_for_final": True,
                "recommended_research_path": "proof_first",
                "research_evaluation_requires_generated_algorithm_code": True,
                "research_evaluation_requires_generated_simulation_code": True,
            },
            "subsystem_execution_plan": [
                {"subsystem": "AlgorithmEngineer"},
                {"subsystem": "SimulationEvaluator"},
                {"subsystem": "FormalizationEvaluator"},
                {"subsystem": "CriticEvaluator"},
            ],
            "question_id": question_id,
        },
    }


def test_formal_blocker_does_not_starve_unvisited_empirical_lanes() -> None:
    question = OpenResearchQuestion(
        id="generic-cross-lane-task",
        title="Generic cross-lane task",
        description="Collect independent empirical and formal evidence.",
    )
    task = AgentTask(
        task_id="formalize:generic-cross-lane-task",
        owner_subsystem="FormalizationEvaluator",
        objective="Attempt the exact formal target.",
        inputs={
            "question": runtime_module._question_to_payload(question),
            "theory_packet_id": "theory:generic",
            "architect_context": _full_evidence_context(question.id),
        },
    )
    blackboard = BlackboardState(
        project_id=question.id,
        artifacts={"theory:generic": {"packet_id": "theory:generic"}},
    )

    continued = _runtime_transition_policy(
        iteration=4,
        task=task,
        subsystem_name="FormalizationEvaluator",
        result=AgentStepResult(
            status="BLOCKED",
            rationale="Lean workspace budget exhausted.",
            failure_classification="formalizer_client_tool_loop_exhausted",
        ),
        blackboard=blackboard,
        runtime_config=ResearchAgentRuntimeConfig(
            evaluation_mode="capability_eval",
            formal_verification_policy="required",
        ),
    )

    assert continued.status == "REROUTE"
    assert continued.next_task is not None
    assert continued.next_task.owner_subsystem == "AlgorithmEngineer"
    assert "Lean workspace budget exhausted." in blackboard.active_blockers
    outcomes = continued.next_task.inputs["architect_context"][
        "runtime_outer_graph_workspace_outcomes"
    ]
    assert outcomes[-1]["source_subsystem"] == "FormalizationEvaluator"
    assert outcomes[-1]["local_status"] == "BLOCKED"
    assert continued.observations[-1].payload["model_routing_call_used"] is False


def test_final_critic_waits_for_unvisited_required_lanes() -> None:
    question = OpenResearchQuestion(
        id="generic-critic-after-required-lanes",
        title="Critic follows required evidence lanes",
        description="Do not finalize before every planned evidence lane runs.",
    )
    context = _full_evidence_context(question.id)
    formal_task = AgentTask(
        task_id="formalize:generic-critic-after-required-lanes",
        owner_subsystem="FormalizationEvaluator",
        objective="Attempt the exact formal target.",
        inputs={
            "question": runtime_module._question_to_payload(question),
            "theory_packet_id": "theory:generic",
            "architect_context": context,
        },
    )
    critic_task = AgentTask(
        task_id="critic:generic-critic-after-required-lanes",
        owner_subsystem="CriticEvaluator",
        objective="Review the collected evidence.",
        inputs={
            "question": runtime_module._question_to_payload(question),
            "theory_packet_id": "theory:generic",
            "formalization_manifest_id": "formalization:generic",
            "architect_context": context,
        },
    )
    blackboard = BlackboardState(
        project_id=question.id,
        artifacts={"theory:generic": {"packet_id": "theory:generic"}},
    )

    continued = _runtime_transition_policy(
        iteration=4,
        task=formal_task,
        subsystem_name="FormalizationEvaluator",
        result=AgentStepResult(
            status="REROUTE",
            rationale="Formal workspace recorded an unclosed target.",
            produced_artifacts={
                "formalization:generic": {
                    "artifact_kind": "RuntimeFormalizationManifest",
                    "manifest_id": "formalization:generic",
                }
            },
            next_task=critic_task,
        ),
        blackboard=blackboard,
        runtime_config=ResearchAgentRuntimeConfig(
            evaluation_mode="capability_eval",
            formal_verification_policy="required",
        ),
    )

    assert continued.status == "REROUTE"
    assert continued.next_task is not None
    assert continued.next_task.owner_subsystem == "AlgorithmEngineer"
    coverage = continued.observations[-1]
    assert coverage.observation_type == "runtime_required_evidence_lane_continuation"
    assert coverage.payload["next_owner_subsystem"] == "AlgorithmEngineer"
    assert coverage.payload["model_routing_call_used"] is False


def test_architect_repeat_cannot_starve_runnable_unvisited_primary_lane() -> None:
    question = OpenResearchQuestion(
        id="generic-initial-lane-coverage",
        title="Generic initial lane coverage",
        description="Visit independent evidence workspaces before reopening one.",
    )
    context = _full_evidence_context(question.id)
    context["architect_runtime_plan"]["evidence_contract"][
        "recommended_research_path"
    ] = "dual_track"
    context["runtime_outer_graph_workspace_outcomes"] = [
        {
            "source_subsystem": "AlgorithmEngineer",
            "parent_artifact_ids": {"theory_packet_id": "theory:generic"},
        }
    ]
    architect_task = AgentTask(
        task_id="architect:generic-initial-lane-coverage",
        owner_subsystem="ArchitectCoordinator",
        objective="Route the next workspace.",
        inputs={
            "question": runtime_module._question_to_payload(question),
            "architect_context": context,
        },
    )
    repeated_algorithm = AgentTask(
        task_id="algorithm:generic-initial-lane-coverage:repeat",
        owner_subsystem="AlgorithmEngineer",
        objective="Reopen the algorithm workspace on a revised theory.",
        inputs={
            "question": runtime_module._question_to_payload(question),
            "theory_packet_id": "theory:generic",
            "architect_context": context,
        },
    )
    blackboard = BlackboardState(
        project_id=question.id,
        artifacts={"theory:generic": {"packet_id": "theory:generic"}},
    )
    blackboard.handoff_ledger.append(
        TaskHandoffRecord(
            handoff_id="handoff:architect-algorithm",
            from_task_id="architect:initial",
            to_task_id="algorithm:initial",
            from_subsystem="ArchitectCoordinator",
            to_subsystem="AlgorithmEngineer",
            status="REROUTE",
            rationale="Initial algorithm workspace visit.",
        )
    )

    continued = _runtime_transition_policy(
        iteration=9,
        task=architect_task,
        subsystem_name="ArchitectCoordinator",
        result=AgentStepResult(
            status="REROUTE",
            rationale="Architect proposed another algorithm workspace.",
            next_task=repeated_algorithm,
        ),
        blackboard=blackboard,
        runtime_config=ResearchAgentRuntimeConfig(
            evaluation_mode="capability_eval",
            formal_verification_policy="required",
        ),
    )

    assert continued.next_task is not None
    assert continued.next_task.owner_subsystem == "SimulationEvaluator"
    assert continued.failure_classification == (
        "runtime_required_evidence_lane_continuation"
    )
    coverage = continued.observations[-1]
    assert coverage.observation_type == "runtime_required_evidence_lane_continuation"
    assert coverage.payload["initial_lane_coverage_override"] is True
    assert coverage.payload["next_owner_subsystem"] == "SimulationEvaluator"
    assert coverage.payload["runtime_authored_research_content"] is False


def test_architect_feedback_route_is_not_replaced_by_initial_lane_coverage() -> None:
    question = OpenResearchQuestion(
        id="generic-feedback-owner",
        title="Generic feedback owner",
        description="Resolve an active cross-artifact observation first.",
    )
    context = _full_evidence_context(question.id)
    context["runtime_outer_graph_workspace_outcomes"] = [
        {
            "source_subsystem": "AlgorithmEngineer",
            "parent_artifact_ids": {"theory_packet_id": "theory:generic"},
        }
    ]
    selected_owner_task = AgentTask(
        task_id="algorithm-feedback:generic-feedback-owner",
        owner_subsystem="AlgorithmEngineer",
        objective="Resolve the active observation in the selected workspace.",
        inputs={
            "question": runtime_module._question_to_payload(question),
            "theory_packet_id": "theory:generic",
            "architect_context": context,
        },
    )
    result = AgentStepResult(
        status="REROUTE",
        rationale="Architect selected the evidence-bound source owner.",
        next_task=selected_owner_task,
    )

    transitioned = _runtime_transition_policy(
        iteration=12,
        task=AgentTask(
            task_id="architect-feedback:generic-feedback-owner",
            owner_subsystem="ArchitectCoordinator",
            objective="Route the active observation.",
            inputs={
                "question": runtime_module._question_to_payload(question),
                "architect_context": context,
                "environment_feedback": {
                    "feedback_type": "workspace_replan_observation_ref"
                },
                "runtime_architect_operation": (
                    runtime_module.ARCHITECT_FEEDBACK_ROUTE_OPERATION
                ),
            },
        ),
        subsystem_name="ArchitectCoordinator",
        result=result,
        blackboard=BlackboardState(
            project_id=question.id,
            artifacts={"theory:generic": {"packet_id": "theory:generic"}},
        ),
        runtime_config=ResearchAgentRuntimeConfig(
            evaluation_mode="capability_eval",
            formal_verification_policy="required",
        ),
    )

    assert transitioned is result
    assert transitioned.next_task is selected_owner_task
    assert transitioned.next_task.owner_subsystem == "AlgorithmEngineer"


def test_lane_coverage_does_not_count_invalidated_parent_lineage() -> None:
    question = OpenResearchQuestion(
        id="generic-revised-theory-lineage",
        title="Rebuild revised-theory descendants first",
        description="An old algorithm visit cannot satisfy a new theory parent.",
    )
    context = _full_evidence_context(question.id)
    context["architect_runtime_plan"]["evidence_contract"][
        "recommended_research_path"
    ] = "dual_track"
    context["theory_packet_id"] = "theory:revised"
    context["runtime_dependency_rebuild"] = {
        "artifact_kind": "RuntimeTheoryRevisionDependencyRebuild",
        "revised_theory_packet_id": "theory:revised",
    }
    context["runtime_outer_graph_workspace_outcomes"] = [
        {
            "source_subsystem": "AlgorithmEngineer",
            "parent_artifact_ids": {"theory_packet_id": "theory:parent"},
        }
    ]
    proposed_algorithm = AgentTask(
        task_id="algorithm:generic-revised-theory-lineage",
        owner_subsystem="AlgorithmEngineer",
        objective="Rebuild the algorithm against the revised theory.",
        inputs={
            "question": runtime_module._question_to_payload(question),
            "theory_packet_id": "theory:revised",
            "architect_context": context,
        },
    )
    result = AgentStepResult(
        status="REROUTE",
        rationale="Preflight accepted the revised theory lineage.",
        next_task=proposed_algorithm,
    )
    blackboard = BlackboardState(
        project_id=question.id,
        artifacts={"theory:revised": {"packet_id": "theory:revised"}},
    )
    blackboard.handoff_ledger.append(
        TaskHandoffRecord(
            handoff_id="handoff:old-algorithm",
            from_task_id="architect:old",
            to_task_id="algorithm:old",
            from_subsystem="ArchitectCoordinator",
            to_subsystem="AlgorithmEngineer",
            status="REROUTE",
            rationale="Algorithm ran against the invalidated parent theory.",
        )
    )

    transitioned = _runtime_transition_policy(
        iteration=14,
        task=AgentTask(
            task_id="architect:generic-revised-theory-lineage",
            owner_subsystem="ArchitectCoordinator",
            objective="Continue the revised lineage.",
            inputs={
                "question": runtime_module._question_to_payload(question),
                "architect_context": context,
            },
        ),
        subsystem_name="ArchitectCoordinator",
        result=result,
        blackboard=blackboard,
        runtime_config=ResearchAgentRuntimeConfig(
            evaluation_mode="capability_eval",
            formal_verification_policy="required",
        ),
    )

    assert transitioned is result
    assert transitioned.next_task is proposed_algorithm


def test_initial_lane_coverage_does_not_interrupt_bound_source_owner_loop() -> None:
    question = OpenResearchQuestion(
        id="generic-bound-source-owner",
        title="Generic bound source owner",
        description="Keep raw consumer feedback with its exact source owner.",
    )
    context = _full_evidence_context(question.id)
    context["architect_runtime_plan"]["evidence_contract"][
        "recommended_research_path"
    ] = "dual_track"
    source_owner_task = AgentTask(
        task_id="algorithm-consumer-observation:generic-bound-source-owner",
        owner_subsystem="AlgorithmEngineer",
        objective="Revise the exact source from its raw consumer observation.",
        inputs={
            "question": runtime_module._question_to_payload(question),
            "theory_packet_id": "theory:generic",
            "architect_context": context,
            "deferred_consumer_task_continuation_ref": {
                "artifact_kind": "RuntimeAgentTaskContinuationRef"
            },
        },
        budget={
            runtime_module.SCIENTIFIC_CONSUMER_REVISION_BUDGET_KEY: {
                "revisions_used": 1,
                "max_revisions": 2,
            }
        },
    )
    result = AgentStepResult(
        status="REROUTE",
        rationale="Return the raw observation to the exact source owner.",
        next_task=source_owner_task,
    )
    blackboard = BlackboardState(
        project_id=question.id,
        artifacts={"theory:generic": {"packet_id": "theory:generic"}},
    )
    blackboard.handoff_ledger.append(
        TaskHandoffRecord(
            handoff_id="handoff:architect-algorithm",
            from_task_id="architect:initial",
            to_task_id="algorithm:initial",
            from_subsystem="ArchitectCoordinator",
            to_subsystem="AlgorithmEngineer",
            status="REROUTE",
            rationale="Initial algorithm workspace visit.",
        )
    )

    continued = _runtime_transition_policy(
        iteration=9,
        task=AgentTask(
            task_id="architect:generic-bound-source-owner",
            owner_subsystem="ArchitectCoordinator",
            objective="Route exact feedback.",
        ),
        subsystem_name="ArchitectCoordinator",
        result=result,
        blackboard=blackboard,
        runtime_config=ResearchAgentRuntimeConfig(
            evaluation_mode="capability_eval",
            formal_verification_policy="required",
        ),
    )

    assert continued is result
    assert continued.next_task is source_owner_task


def test_lane_coverage_rejects_outcome_driven_confirmatory_source_revision() -> None:
    question = OpenResearchQuestion(
        id="generic-confirmatory-source-revision",
        title="Generic confirmatory source revision",
        description="Let the exact source owner revise from a reviewed outcome.",
    )
    theory_packet_id = "theory:generic"
    algorithm_manifest_id = "algorithm:accepted"
    simulation_manifest_id = "simulation:confirmatory-failed"
    cohort = {
        "artifact_kind": "RuntimeConfirmatoryEvaluationCohort",
        "cohort_id": "confirmatory-cohort:parent",
        "seed": 37,
    }
    source_manifest = {
        "artifact_kind": "RuntimeSimulationManifest",
        "manifest_id": simulation_manifest_id,
        "question": runtime_module._question_to_payload(question),
        "theory_packet_id": theory_packet_id,
        "confirmatory_evaluation_cohort": cohort,
        "simulation_passed": False,
    }
    source_manifest_hash = runtime_module.stable_hash(source_manifest)
    context = _full_evidence_context(question.id)
    context.update(
        {
            "theory_packet_id": theory_packet_id,
            "algorithm_sandbox_manifest_id": algorithm_manifest_id,
            "simulation_manifest_id": simulation_manifest_id,
            "accepted_generated_code_semantic_reviews": [
                {
                    "source_subsystem": "SimulationEvaluator",
                    "source_manifest_id": simulation_manifest_id,
                    "source_manifest_hash": source_manifest_hash,
                    "overall_verdict": "ACCEPT",
                    "parent_artifact_ids": {
                        "theory_packet_id": theory_packet_id,
                        "algorithm_sandbox_manifest_id": algorithm_manifest_id,
                    },
                }
            ],
        }
    )
    feedback = {
        "feedback_type": "confirmatory_simulation_outcome",
        "source_subsystem": "SimulationEvaluator",
        "source_manifest_id": simulation_manifest_id,
        "source_manifest_hash": source_manifest_hash,
        "question_id": question.id,
        "theory_packet_id": theory_packet_id,
        "confirmatory_evaluation_cohort": cohort,
        "source_execution_valid": True,
        "unchanged_source_retry_authorized": False,
        "runtime_edited_source": False,
    }
    source_revision_task = AgentTask(
        task_id="simulation-confirmatory-source-revision:generic",
        owner_subsystem="SimulationEvaluator",
        objective="Revise the exact source from the reviewed outcome.",
        inputs={
            "question": runtime_module._question_to_payload(question),
            "theory_packet_id": theory_packet_id,
            "architect_context": context,
            "environment_feedback": feedback,
        },
    )
    result = AgentStepResult(
        status="REROUTE",
        rationale="Independent review accepted the source and released its outcome.",
        next_task=source_revision_task,
    )
    blackboard = BlackboardState(
        project_id=question.id,
        artifacts={
            theory_packet_id: {"packet_id": theory_packet_id},
            simulation_manifest_id: source_manifest,
        },
    )

    continued = _runtime_transition_policy(
        iteration=9,
        task=AgentTask(
            task_id="review:confirmatory-source",
            owner_subsystem=(
                runtime_module.GENERATED_CODE_SEMANTIC_REVIEWER_SUBSYSTEM
            ),
            objective="Review the exact confirmatory source.",
        ),
        subsystem_name=(
            runtime_module.GENERATED_CODE_SEMANTIC_REVIEWER_SUBSYSTEM
        ),
        result=result,
        blackboard=blackboard,
        runtime_config=ResearchAgentRuntimeConfig(
            evaluation_mode="capability_eval",
            formal_verification_policy="required",
        ),
    )

    assert continued.next_task is not None
    assert continued.next_task is not source_revision_task
    assert continued.next_task.owner_subsystem == "FormalizationEvaluator"
    assert continued.failure_classification == (
        "runtime_required_evidence_lane_continuation"
    )


def test_theory_revision_retires_active_descendant_authority() -> None:
    context = {
        **_full_evidence_context("generic-parent-change"),
        "algorithm_sandbox_manifest_id": "algorithm:old",
        "simulation_manifest_id": "simulation:old",
        "formalization_manifest_id": "formalization:old",
        "formalizer_lean_candidate_materialization_manifest_id": "lean:old",
        "accepted_generated_code_semantic_reviews": [{"review_id": "review:old"}],
        "upstream_algorithm_handoff": {"handoff_id": "handoff:old"},
    }

    invalidated = runtime_module._context_with_invalidated_theory_descendants(
        context
    )

    assert invalidated["architect_runtime_plan"] == context["architect_runtime_plan"]
    assert invalidated["previous_algorithm_sandbox_manifest_id"] == "algorithm:old"
    assert invalidated["previous_simulation_manifest_id"] == "simulation:old"
    assert invalidated["previous_formalization_manifest_id"] == "formalization:old"
    assert (
        invalidated["previous_formalizer_lean_candidate_materialization_manifest_id"]
        == "lean:old"
    )
    assert "algorithm_sandbox_manifest_id" not in invalidated
    assert "simulation_manifest_id" not in invalidated
    assert "formalization_manifest_id" not in invalidated
    assert "accepted_generated_code_semantic_reviews" not in invalidated
    assert "upstream_algorithm_handoff" not in invalidated
    assert invalidated[
        "previous_accepted_generated_code_semantic_reviews"
    ] == [{"review_id": "review:old"}]
    assert invalidated["previous_upstream_algorithm_handoff"] == {
        "handoff_id": "handoff:old"
    }


def test_theory_revision_replays_only_exact_accepted_algorithm_source_seed() -> None:
    question = OpenResearchQuestion(
        id="generic-theory-source-seed",
        title="Generic theory source seed",
        description="Replay unchanged source against an unchanged estimator ABI.",
    )
    estimator_spec = {
        "id": "generic-estimator",
        "formula": "theta_hat = mean(X)",
        "inputs": ["observations"],
        "outputs": ["estimate"],
    }
    source = (
        "def run_estimator(request):\n"
        "    return {'estimate': request.get('value', 0.0)}\n\n"
        "def run_sandbox(seed, replicates):\n"
        "    return {'estimate': 0.0}\n"
    )
    manifest_id = "algorithm_sandbox_manifest:accepted-parent"
    manifest = {
        "artifact_kind": "RuntimeAlgorithmSandboxManifest",
        "manifest_id": manifest_id,
        "question": runtime_module._question_to_payload(question),
        "theory_packet_id": "theory:parent",
        "prototypes": [
            {
                "estimator_id": "generic-estimator",
                "prototype_status": "EXECUTED",
                "executor": "generated_python_sandbox",
                "language": "python",
                "requested_execution_profile": "stdlib",
                "executor_profile": "stdlib",
                "dependencies": [],
                "source_code": source,
                "script_hash": runtime_module.stable_hash(source),
                "spec": estimator_spec,
                "smoke_passed": True,
                "execution_smoke_passed": True,
            }
        ],
    }
    accepted_review = {
        "execution_id": "semantic-review-execution:accepted-parent",
        "review_packet_id": "semantic-review:accepted-parent",
        "source_subsystem": "AlgorithmEngineer",
        "source_manifest_id": manifest_id,
        "source_manifest_hash": runtime_module.stable_hash(manifest),
        "overall_verdict": "ACCEPT",
    }
    context = {
        "previous_algorithm_sandbox_manifest_id": manifest_id,
        "previous_accepted_generated_code_semantic_reviews": [accepted_review],
    }
    blackboard = BlackboardState(
        project_id=question.id,
        artifacts={manifest_id: manifest},
    )

    seeds, lineage = (
        runtime_module._runtime_theory_revision_algorithm_source_seeds(
            architect_context=context,
            blackboard=blackboard,
            question_id=question.id,
            theory_packet={"estimator_specs": [estimator_spec]},
        )
    )

    assert seeds["generic-estimator"]["code"] == source
    assert lineage["parent_manifest_id"] == manifest_id
    assert lineage["reuse_basis"] == "exact_estimator_spec_and_source_hash"
    changed_spec = {**estimator_spec, "formula": "theta_hat = median(X)"}
    changed_seeds, changed_lineage = (
        runtime_module._runtime_theory_revision_algorithm_source_seeds(
            architect_context=context,
            blackboard=blackboard,
            question_id=question.id,
            theory_packet={"estimator_specs": [changed_spec]},
        )
    )
    assert changed_seeds == {}
    assert changed_lineage == {}


def test_algorithm_workspace_executes_exact_theory_revision_seed_before_reauthoring(
    tmp_path: Path,
) -> None:
    question = OpenResearchQuestion(
        id="generic-theory-seed-execution",
        title="Generic theory seed execution",
        description="Execute accepted unchanged source before asking for new source.",
    )
    theory_packet_id = "theory:revised-source-seed"
    estimator_spec = {
        "id": "generic-estimator",
        "formula": "theta_hat = request value",
        "inputs": ["value"],
        "outputs": ["estimate"],
    }
    theory_packet = {
        "artifact_kind": "TheoryDerivationPacket",
        "packet_id": theory_packet_id,
        "estimator_specs": [estimator_spec],
    }
    source = (
        "def run_estimator(request):\n"
        "    return {'estimate': float(request.get('value', 0.0))}\n\n"
        "def run_sandbox(seed, replicates):\n"
        "    return {'estimate': 0.0}\n"
    )
    prior_manifest_id = "algorithm_sandbox_manifest:source-seed-parent"
    prior_manifest = {
        "artifact_kind": "RuntimeAlgorithmSandboxManifest",
        "manifest_id": prior_manifest_id,
        "question": runtime_module._question_to_payload(question),
        "theory_packet_id": "theory:source-seed-parent",
        "prototypes": [
            {
                "estimator_id": "generic-estimator",
                "prototype_status": "EXECUTED",
                "executor": "generated_python_sandbox",
                "language": "python",
                "requested_execution_profile": "stdlib",
                "executor_profile": "stdlib",
                "dependencies": [],
                "source_code": source,
                "script_hash": runtime_module.stable_hash(source),
                "spec": estimator_spec,
                "smoke_passed": True,
                "execution_smoke_passed": True,
            }
        ],
    }
    prior_review = {
        "execution_id": "semantic-review-execution:source-seed-parent",
        "review_packet_id": "semantic-review:source-seed-parent",
        "source_subsystem": "AlgorithmEngineer",
        "source_manifest_id": prior_manifest_id,
        "source_manifest_hash": runtime_module.stable_hash(prior_manifest),
        "overall_verdict": "ACCEPT",
    }

    class ProposalAgent:
        provider = object()

        def __init__(self) -> None:
            self.proposal_calls = 0
            self.source_calls = 0

        def propose(self, **_kwargs):
            self.proposal_calls += 1
            return {
                "artifact_kind": "AlgorithmEngineerProposalPacket",
                "packet_id": "algorithm-proposal:source-seed-rebind",
                "source_agent": "LLMAlgorithmEngineerAgent",
                "source_provider": "anthropic",
                "backend_provider_name": "anthropic",
                "model": "claude-haiku-4-5-20251001",
                "model_tier": "haiku",
                "scientific_source_transport": "native_client_tools",
                "implementation_targets": [
                    {"estimator_id": "generic-estimator"}
                ],
                "sandbox_code_drafts": [
                    {"estimator_id": "generic-estimator"}
                ],
            }

        def iterate_code_with_tools(self, **_kwargs):
            self.source_calls += 1
            raise AssertionError("passing source seed must not be regenerated")

    proposal_agent = ProposalAgent()
    context = _full_evidence_context(question.id)
    context.update(
        {
            "theory_packet_id": theory_packet_id,
            "previous_algorithm_sandbox_manifest_id": prior_manifest_id,
            "previous_accepted_generated_code_semantic_reviews": [prior_review],
            "empirical_evaluation_phase": (
                runtime_module.EMPIRICAL_EVALUATION_PHASE_EXPLORATORY
            ),
            "architect_metric_protocol_gate": {
                "artifact_kind": "RuntimeArchitectMetricProtocolGate",
                "algorithm_execution_authorized": True,
                "confirmatory_simulation_authorized": False,
                "execution_authorized": False,
                "preflight_acceptance_id": "preflight:accepted",
            },
        }
    )
    deferred_task = AgentTask(
        task_id="architect-metric-after-source-seed",
        owner_subsystem="ArchitectCoordinator",
        objective="Continue metric authoring after implementation review.",
        inputs={
            "question": runtime_module._question_to_payload(question),
            "architect_context": context,
            "runtime_architect_operation": (
                runtime_module.RUNTIME_ARCHITECT_OPERATION_POST_IMPLEMENTATION_METRIC
            ),
        },
    )
    task = AgentTask(
        task_id="algorithm-before-metric:source-seed",
        owner_subsystem="AlgorithmEngineer",
        objective="Execute the current estimator implementation.",
        inputs={
            "question": runtime_module._question_to_payload(question),
            "theory_packet_id": theory_packet_id,
            "architect_context": context,
            "implementation_gaps": [
                {"estimator_id": "generic-estimator"}
            ],
            "implementation_before_metric_freeze": True,
            "empirical_evaluation_phase": (
                runtime_module.EMPIRICAL_EVALUATION_PHASE_EXPLORATORY
            ),
            "deferred_metric_protocol_task": asdict(deferred_task),
            "n_runs": 2,
            "seed": 7,
        },
    )
    subsystem = runtime_module.AlgorithmEngineerRuntimeSubsystem(
        out_dir=tmp_path,
        n_runs=2,
        seed=7,
        proposal_agent=proposal_agent,
        semantic_reviewer_available=False,
    )

    result = subsystem.run(
        task,
        BlackboardState(
            project_id=question.id,
            artifacts={
                theory_packet_id: theory_packet,
                prior_manifest_id: prior_manifest,
            },
        ),
    )

    manifests = [
        row
        for row in result.produced_artifacts.values()
        if isinstance(row, dict)
        and row.get("artifact_kind") == "RuntimeAlgorithmSandboxManifest"
    ]
    assert len(manifests) == 1, (
        result.status,
        result.rationale,
        result.failure_classification,
        [observation.payload for observation in result.observations],
    )
    assert manifests[0]["n_theory_revision_source_seeds_replayed"] == 1
    replay = manifests[0]["prototypes"][0]["theory_revision_source_seed"]
    assert replay["replay_execution_attempted"] is True
    assert replay["replay_execution_passed"] is True
    assert proposal_agent.proposal_calls == 1
    assert proposal_agent.source_calls == 0


def test_outer_graph_reopens_algorithm_for_revised_theory_parent() -> None:
    question = OpenResearchQuestion(
        id="generic-revised-parent",
        title="Generic revised-parent task",
        description="Rebuild empirical descendants after theory changes.",
    )
    context = _full_evidence_context(question.id)
    context["theory_packet_id"] = "theory:new"
    context["runtime_outer_graph_workspace_outcomes"] = [
        {
            "source_task_id": "algorithm:old",
            "source_subsystem": "AlgorithmEngineer",
            "local_status": "COMPLETED",
            "parent_artifact_ids": {"theory_packet_id": "theory:old"},
        }
    ]
    task = AgentTask(
        task_id="formalize:revised-parent",
        owner_subsystem="FormalizationEvaluator",
        objective="Attempt formalization for the revised theory.",
        inputs={
            "question": runtime_module._question_to_payload(question),
            "theory_packet_id": "theory:new",
            "architect_context": context,
        },
    )

    continued = _runtime_transition_policy(
        iteration=7,
        task=task,
        subsystem_name="FormalizationEvaluator",
        result=AgentStepResult(
            status="BLOCKED",
            rationale="The formal workspace recorded a typed blocker.",
            failure_classification="formalizer_client_tool_loop_exhausted",
        ),
        blackboard=BlackboardState(
            project_id=question.id,
            artifacts={"theory:new": {"packet_id": "theory:new"}},
        ),
        runtime_config=ResearchAgentRuntimeConfig(
            evaluation_mode="capability_eval",
            formal_verification_policy="required",
        ),
    )

    assert continued.status == "REROUTE"
    assert continued.next_task is not None
    assert continued.next_task.owner_subsystem == "AlgorithmEngineer"
    routing = continued.next_task.inputs["architect_context"][
        "architect_initial_routing"
    ]
    assert routing["parent_artifact_ids"] == {
        "theory_packet_id": "theory:new"
    }
    observed = continued.observations[-1].payload
    assert "AlgorithmEngineer" not in observed["executed_subsystems"]


def test_accepted_code_review_closes_only_its_current_parent_lineage() -> None:
    context = _full_evidence_context("generic-reviewed-source")
    context["algorithm_sandbox_manifest_id"] = "algorithm:accepted"
    context["accepted_generated_code_semantic_reviews"] = [
        {
            "source_subsystem": "AlgorithmEngineer",
            "source_manifest_id": "algorithm:accepted",
            "overall_verdict": "ACCEPT",
            "parent_artifact_ids": {"theory_packet_id": "theory:generic"},
        }
    ]

    assert "AlgorithmEngineer" in runtime_module._runtime_executed_subsystems(
        architect_context=context
    )

    context["theory_packet_id"] = "theory:revised"
    assert "AlgorithmEngineer" not in runtime_module._runtime_executed_subsystems(
        architect_context=context
    )


def test_consumer_failure_reopens_exact_accepted_source_owner() -> None:
    question = OpenResearchQuestion(
        id="generic-consumer-backedge",
        title="Return consumer failure to its source owner",
        description="A reviewed source fails inside a downstream consumer.",
    )
    context = _full_evidence_context(question.id)
    context["algorithm_sandbox_manifest_id"] = "algorithm:accepted"
    context["accepted_generated_code_semantic_reviews"] = [
        {
            "source_subsystem": "AlgorithmEngineer",
            "source_manifest_id": "algorithm:accepted",
            "overall_verdict": "ACCEPT",
            "parent_artifact_ids": {"theory_packet_id": "theory:generic"},
        }
    ]
    source_manifest = {
        "artifact_kind": "RuntimeAlgorithmSandboxManifest",
        "manifest_id": "algorithm:accepted",
        "theory_packet_id": "theory:generic",
    }
    failure_classification = "accepted_algorithm_estimator_runtime_failed"
    feedback = {
        "feedback_type": "algorithm_sandbox_execution_feedback",
        "algorithm_sandbox_manifest_id": "algorithm:accepted",
        "source_manifest_artifact_id": "algorithm:accepted",
        "source_manifest_content_hash": runtime_module.stable_hash(
            source_manifest
        ),
        "failure_classification": failure_classification,
        "consumer_execution_observation": {
            "stderr_summary": "accepted estimator returned a non-finite value"
        },
        "observation_transport": {
            "complete_candidate_rows": True,
            "runtime_interpreted_failure": False,
            "runtime_selected_source_edit": False,
            "same_source_producer_must_revise": True,
        },
    }
    source_task = AgentTask(
        task_id="algorithm-consumer-observation:generic",
        owner_subsystem="AlgorithmEngineer",
        objective="Revise the exact source from its raw consumer observation.",
        inputs={
            "question": runtime_module._question_to_payload(question),
            "theory_packet_id": "theory:generic",
            "architect_context": context,
            "environment_feedback": feedback,
        },
    )
    result = AgentStepResult(
        status="REROUTE",
        rationale="Return the raw consumer observation to its source owner.",
        next_task=source_task,
        failure_classification=failure_classification,
    )

    continued = _runtime_transition_policy(
        iteration=8,
        task=AgentTask(
            task_id="simulation:generic-consumer-backedge",
            owner_subsystem="SimulationEvaluator",
            objective="Execute the accepted estimator in a downstream consumer.",
            inputs={
                "question": runtime_module._question_to_payload(question),
                "theory_packet_id": "theory:generic",
                "algorithm_sandbox_manifest_id": "algorithm:accepted",
                "architect_context": context,
            },
        ),
        subsystem_name="SimulationEvaluator",
        result=result,
        blackboard=BlackboardState(
            project_id=question.id,
            artifacts={
                "theory:generic": {"packet_id": "theory:generic"},
                "algorithm:accepted": source_manifest,
            },
        ),
        runtime_config=ResearchAgentRuntimeConfig(
            evaluation_mode="capability_eval",
            formal_verification_policy="required",
        ),
    )

    assert continued is result
    assert continued.next_task is source_task
    assert continued.next_task.owner_subsystem == "AlgorithmEngineer"


def test_consumer_backedge_revises_only_failed_source_and_defers_consumer(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    question = OpenResearchQuestion(
        id="generic-targeted-consumer",
        title="Revise one failed dependency",
        description="Keep the failed consumer as the exact deferred task.",
    )
    theory_packet_id = "theory:generic-targeted-consumer"
    theory_packet = {
        "artifact_kind": "TheoryDerivationPacket",
        "packet_id": theory_packet_id,
        "estimator_specs": [
            {"id": "failed-estimator", "formula": "model-authored formula"},
            {"id": "stable-estimator", "formula": "model-authored formula"},
        ],
    }
    proposal_id = "algorithm-proposal:generic-parent"
    proposal = {
        "artifact_kind": "AlgorithmEngineerProposalPacket",
        "packet_id": proposal_id,
        "source_agent": "LLMAlgorithmEngineerAgent",
        "source_provider": "anthropic",
        "backend_provider_name": "anthropic",
        "model": "claude-haiku-4-5-20251001",
        "model_tier": "haiku",
        "scientific_source_transport": "native_client_tools",
        "implementation_targets": [
            {"estimator_id": "failed-estimator"},
            {"estimator_id": "stable-estimator"},
        ],
        "sandbox_code_drafts": [
            {"estimator_id": "failed-estimator"},
            {"estimator_id": "stable-estimator"},
        ],
    }
    simulation_proposal_id = "simulation-proposal:generic-consumer"
    simulation_source = (
        "def run_sandbox(seed, replicates):\n"
        "    return {'generic_metric': float(replicates)}\n"
    )

    def source_for(estimator_id: str, *, revised: bool = False) -> str:
        lookup = "request.get('value', 0.0)" if revised else "request['value']"
        return (
            "def run_estimator(request):\n"
            f"    return {{'{estimator_id}': {lookup}}}\n\n"
            "def run_sandbox(seed, replicates):\n"
            f"    return {{'{estimator_id}': 1.0}}\n"
        )

    def executed_row(estimator_id: str, source: str) -> dict[str, object]:
        script_path = tmp_path / f"{estimator_id}.py"
        result_path = tmp_path / f"{estimator_id}.json"
        result = {estimator_id: 1.0}
        script_path.write_text(source, encoding="utf-8")
        result_path.write_text(json.dumps(result), encoding="utf-8")
        return {
            "estimator_id": estimator_id,
            "prototype_status": "EXECUTED",
            "executor": "generated_python_sandbox",
            "language": "python",
            "requested_execution_profile": "stdlib",
            "executor_profile": "stdlib",
            "dependencies": [],
            "source_code": source,
            "script_path": str(script_path),
            "script_hash": runtime_module.stable_hash(source),
            "result_path": str(result_path),
            "result_hash": runtime_module.stable_hash(result),
            "metrics": result,
            "smoke_passed": True,
            "execution_smoke_passed": True,
            "execution_attempted": True,
            "source_llm_proposal_id": proposal_id,
            "source_llm_proposal_agent": "LLMAlgorithmEngineerAgent",
            "source_llm_proposal_provider": "anthropic",
            "source_llm_proposal_backend_provider": "anthropic",
            "source_llm_proposal_model": "claude-haiku-4-5-20251001",
            "source_llm_proposal_model_tier": "haiku",
            "source_llm_proposal_live_generator": True,
            "llm_algorithm_engineer_target": {"estimator_id": estimator_id},
        }

    failed_parent = executed_row(
        "failed-estimator",
        source_for("failed-estimator"),
    )
    stable_parent = executed_row(
        "stable-estimator",
        source_for("stable-estimator"),
    )
    source_manifest_id = "algorithm:generic-parent"
    source_manifest = {
        "schema_version": 1,
        "artifact_kind": "RuntimeAlgorithmSandboxManifest",
        "manifest_id": source_manifest_id,
        "theory_packet_id": theory_packet_id,
        "llm_algorithm_engineer_proposal_id": proposal_id,
        "prototypes": [failed_parent, stable_parent],
        "boundary": "algorithm execution is not proof evidence",
    }
    simulation_manifest_id = "simulation:generic-failed-consumer"
    simulation_manifest = {
        "schema_version": 1,
        "artifact_kind": "RuntimeSimulationManifest",
        "manifest_id": simulation_manifest_id,
        "question": runtime_module._question_to_payload(question),
        "theory_packet_id": theory_packet_id,
        "llm_simulation_engineer_proposal_id": simulation_proposal_id,
        "generated_simulation_sandbox_prototypes": [
            {
                "simulation_id": "generic-consumer",
                "prototype_status": "FAILED",
                "language": "python",
                "requested_execution_profile": "stdlib",
                "executor_profile": "stdlib",
                "dependencies": [],
                "required_estimator_ids": ["failed-estimator"],
                "source_code": simulation_source,
                "script_hash": runtime_module.stable_hash(simulation_source),
            }
        ],
    }
    consumer_budget = {
        runtime_module.SCIENTIFIC_CONSUMER_REVISION_BUDGET_KEY: {
            "lineage_id": "scientific_consumer_lineage:generic",
            "revisions_used": 1,
            "max_revisions": 2,
        }
    }
    deferred_consumer = AgentTask(
        task_id="simulation-consumer-resume:generic",
        owner_subsystem="SimulationEvaluator",
        objective="Rerun the exact failed consumer.",
        inputs={
            "question": runtime_module._question_to_payload(question),
            "theory_packet_id": theory_packet_id,
            "consumer_resume_manifest": simulation_manifest,
            "architect_context": {},
        },
        budget=consumer_budget,
    )
    _, continuation, continuation_artifacts = (
        runtime_module.materialize_agent_task_continuation(
            deferred_consumer,
            linked_input_references={
                runtime_module.stable_hash(simulation_manifest): (
                    runtime_artifact_reference(
                        simulation_manifest_id,
                        simulation_manifest,
                    )
                )
            },
        )
    )
    continuation_ref = runtime_module.agent_task_continuation_reference(
        continuation
    )
    source_owner = {
        "source_owner_subsystem": "AlgorithmEngineer",
        "source_manifest_id": source_manifest_id,
        "source_manifest_hash": runtime_module.stable_hash(source_manifest),
        "dependency_artifact_ids": [
            "failed-estimator",
            "stable-estimator",
        ],
        "dependency_artifact_hashes": {
            "failed-estimator": failed_parent["script_hash"],
            "stable-estimator": stable_parent["script_hash"],
        },
        "consumer_observations_by_dependency": {
            "failed-estimator": [
                {
                    "consumer_artifact_id": "generic-consumer",
                    "consumer_source_hash": "consumer-source-hash",
                    "observation": {
                        "stderr_summary": "KeyError: value",
                    },
                }
            ],
            "stable-estimator": [
                {
                    "consumer_artifact_id": "generic-consumer",
                    "consumer_source_hash": "consumer-source-hash",
                    "observation": {
                        "summary": "Consumer also binds this dependency.",
                    },
                }
            ],
        },
    }
    feedback = {
        "feedback_id": "algorithm-feedback:generic-consumer",
        "feedback_type": "algorithm_sandbox_execution_feedback",
        "algorithm_sandbox_manifest_id": source_manifest_id,
        "source_manifest_artifact_id": source_manifest_id,
        "source_manifest_content_hash": runtime_module.stable_hash(
            source_manifest
        ),
        "failure_classification": (
            "accepted_algorithm_estimator_runtime_failed"
        ),
        "prototypes": [failed_parent],
        "consumer_source_owner": source_owner,
        "consumer_execution_observation": {
            "generated_simulation_prototypes": [
                {"estimator_runtime_errors": ["KeyError: value"]}
            ]
        },
        "observation_transport": {
            "same_source_producer_must_revise": True,
            "runtime_selected_source_edit": False,
        },
    }

    class Provider:
        @staticmethod
        def generate_client_tool_turn(*_args, **_kwargs):
            raise AssertionError("the fake source workspace owns model turns")

    class SourceAgent:
        provider = Provider()
        propose_calls = 0
        source_calls: list[str] = []
        initial_observations: list[dict[str, object]] = []
        candidate_checks: list[dict[str, object]] = []
        current_source_run_authorizations: list[bool] = []

        @classmethod
        def propose(cls, **_kwargs):
            cls.propose_calls += 1
            raise AssertionError("consumer revision must bypass planning")

        @classmethod
        def iterate_code_with_tools(cls, **kwargs):
            artifact_id = str(kwargs["artifact_id"])
            cls.source_calls.append(artifact_id)
            cls.current_source_run_authorizations.append(
                bool(kwargs["allow_current_source_run"])
            )
            cls.initial_observations.append(
                dict(kwargs["initial_observation"])
            )
            if artifact_id.endswith(":stable-estimator"):
                retained_candidate = dict(kwargs["code_draft"])
                retained_check = dict(
                    kwargs["check_candidate"](retained_candidate)
                )
                cls.candidate_checks.append(retained_check)
                return ScientificCodeWorkspaceResult(
                    code_draft=retained_candidate,
                    check_result=retained_check,
                    evidence={
                        "workspace_operation": "targeted_revision",
                        "model_owned_source": True,
                        "runtime_edited_source": False,
                        "source_changed": False,
                        "current_source_run_requested": True,
                        "accepted": retained_check["accepted"],
                    },
                )
            first_candidate = {
                **dict(kwargs["code_draft"]),
                "code": (
                    source_for("failed-estimator", revised=True)
                    + "\n# consumer_compatible = False\n"
                ),
            }
            first_check = dict(kwargs["check_candidate"](first_candidate))
            corrected_candidate = {
                **first_candidate,
                "code": (
                    source_for("failed-estimator", revised=True)
                    + "\n# consumer_compatible = True\n"
                ),
            }
            corrected_check = dict(
                kwargs["check_candidate"](corrected_candidate)
            )
            cls.candidate_checks.extend((first_check, corrected_check))
            return ScientificCodeWorkspaceResult(
                code_draft=corrected_candidate,
                check_result=corrected_check,
                evidence={
                    "workspace_operation": "targeted_revision",
                    "model_owned_source": True,
                    "runtime_edited_source": False,
                    "accepted": corrected_check["accepted"],
                },
            )

    def run_generated_code_sandbox(**kwargs):
        estimator_id = str(kwargs["estimator_id"])
        source = str(kwargs["code_draft"]["code"])
        return (
            executed_row(estimator_id, source),
            ToolCallRecord(
                tool_name="python.generated_algorithm_sandbox",
                exit_status="0",
            ),
        )

    integration_sources: list[str] = []

    def run_generated_simulation_sandbox(**kwargs):
        artifact = next(
            row
            for row in kwargs["upstream_algorithm_handoff"][
                "exact_algorithm_artifacts"
            ]
            if row["estimator_id"] == "failed-estimator"
        )
        source = str(artifact["exact_source_code"])
        integration_sources.append(source)
        passed = "consumer_compatible = True" in source
        row = {
            "simulation_id": str(kwargs["simulation_id"]),
            "prototype_status": "EXECUTED" if passed else "FAILED",
            "executor": "generated_simulation_sandbox",
            "language": "python",
            "requested_execution_profile": "stdlib",
            "executor_profile": "stdlib",
            "dependencies": [],
            "required_estimator_ids": ["failed-estimator"],
            "available_upstream_estimator_ids": [
                "failed-estimator",
                "stable-estimator",
            ],
            "source_code": simulation_source,
            "script_hash": runtime_module.stable_hash(simulation_source),
            "execution_attempted": True,
            "execution_smoke_passed": passed,
            "smoke_passed": passed,
            "estimator_runtime_failure_ids": (
                [] if passed else ["failed-estimator"]
            ),
            "estimator_runtime_errors": (
                []
                if passed
                else ["TypeError: generated estimator returned an invalid object"]
            ),
            "stderr_summary": (
                ""
                if passed
                else "TypeError: generated estimator returned an invalid object"
            ),
            "estimator_invocation_samples": {
                "failed-estimator": [
                    {
                        "request_shape": {"value": "number"},
                        "response_status": "ok" if passed else "error",
                        **({} if passed else {"error_type": "TypeError"}),
                    }
                ]
            },
        }
        return row, ToolCallRecord(
            tool_name="python.generated_simulation_sandbox",
            exit_status="0" if passed else "1",
        )

    monkeypatch.setattr(
        runtime_module,
        "_run_generated_code_sandbox",
        run_generated_code_sandbox,
    )
    monkeypatch.setattr(
        runtime_module,
        "_run_generated_simulation_sandbox",
        run_generated_simulation_sandbox,
    )
    blackboard = BlackboardState(
        project_id=question.id,
        artifacts={
            theory_packet_id: theory_packet,
            proposal_id: proposal,
            source_manifest_id: source_manifest,
            simulation_manifest_id: simulation_manifest,
            **continuation_artifacts,
        },
    )
    subsystem = runtime_module.AlgorithmEngineerRuntimeSubsystem(
        out_dir=tmp_path / "algorithm",
        n_runs=8,
        seed=11,
        proposal_agent=SourceAgent(),
        semantic_reviewer_available=True,
        semantic_review_max_revisions=2,
    )
    task = AgentTask(
        task_id="algorithm-consumer-observation:generic",
        owner_subsystem="AlgorithmEngineer",
        objective="Revise the exact failed dependency source.",
        inputs={
            "question": runtime_module._question_to_payload(question),
            "theory_packet_id": theory_packet_id,
            "simulation_manifest_id": simulation_manifest_id,
            "implementation_gaps": [
                {"estimator_id": "failed-estimator"},
                {"estimator_id": "stable-estimator"},
            ],
            "architect_context": {},
            "environment_feedback": feedback,
            "consumer_source_manifest": source_manifest,
            "source_revision_artifact_ids": [
                "failed-estimator",
                "stable-estimator",
            ],
            "deferred_consumer_task_continuation_ref": continuation_ref,
        },
        budget=consumer_budget,
    )

    unreviewed_result = runtime_module.AlgorithmEngineerRuntimeSubsystem(
        out_dir=tmp_path / "algorithm-unreviewed",
        n_runs=8,
        seed=11,
        proposal_agent=SourceAgent(),
        semantic_reviewer_available=False,
        semantic_review_max_revisions=2,
    ).run(task, blackboard)
    assert unreviewed_result.status == "BLOCKED"
    assert unreviewed_result.failure_classification == (
        "scientific_consumer_lineage_invalid"
    )
    assert "requires independent semantic review" in (
        unreviewed_result.observations[0].summary
    )
    assert SourceAgent.source_calls == []

    result = subsystem.run(task, blackboard)

    assert result.status == "REROUTE"
    assert SourceAgent.propose_calls == 0
    assert SourceAgent.source_calls == [
        "generic-targeted-consumer:failed-estimator",
        "generic-targeted-consumer:stable-estimator",
    ]
    assert SourceAgent.current_source_run_authorizations == [False, True]
    assert SourceAgent.initial_observations[0]["consumer_observations"][0][
        "observation"
    ]["stderr_summary"] == "KeyError: value"
    assert [
        check["accepted"] for check in SourceAgent.candidate_checks
    ] == [False, True, True]
    assert SourceAgent.candidate_checks[0]["prototype"][
        "empirical_outcomes_withheld"
    ] is True
    assert "invalid object" in str(
        SourceAgent.candidate_checks[0]["prototype"]
    )
    assert len(integration_sources) == 3
    manifests = [
        artifact
        for artifact in result.produced_artifacts.values()
        if isinstance(artifact, dict)
        and artifact.get("artifact_kind")
        == "RuntimeAlgorithmSandboxManifest"
    ]
    assert len(manifests) == 1
    manifest = manifests[0]
    assert manifest["n_consumer_source_artifacts_revised"] == 1
    assert manifest["n_consumer_source_artifacts_reused"] == 1
    assert manifest["n_executed"] == 2
    rows = {row["estimator_id"]: row for row in manifest["prototypes"]}
    assert rows["stable-estimator"]["prototype_status"] == "EXECUTED"
    assert rows["stable-estimator"]["script_hash"] == stable_parent["script_hash"]
    assert rows["failed-estimator"]["script_hash"] != failed_parent["script_hash"]
    assert result.next_task is not None
    assert result.next_task.owner_subsystem == (
        runtime_module.GENERATED_CODE_SEMANTIC_REVIEWER_SUBSYSTEM
    )
    work_orders = [
        artifact
        for artifact in result.produced_artifacts.values()
        if isinstance(artifact, dict)
        and artifact.get("artifact_kind")
        == "RuntimeGeneratedCodeSemanticReviewWorkOrder"
    ]
    assert len(work_orders) == 1
    work_order = work_orders[0]
    all_artifacts = {**blackboard.artifacts, **result.produced_artifacts}
    restored_consumer = restore_agent_task_continuation(
        all_artifacts[work_order["deferred_next_task_continuation_id"]],
        all_artifacts,
    )
    assert restored_consumer.owner_subsystem == "SimulationEvaluator"
    restored_resume_manifest = restored_consumer.inputs[
        "consumer_resume_manifest"
    ]
    assert (
        restored_resume_manifest.get("manifest_id")
        or restored_resume_manifest.get("artifact_id")
    ) == simulation_manifest_id
    assert restored_consumer.budget == consumer_budget


def test_simulation_consumer_resume_replays_exact_source_without_planning(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    question = OpenResearchQuestion(
        id="generic-consumer-replay",
        title="Replay one exact scientific consumer",
        description="Rerun model-authored source after a dependency revision.",
    )
    theory_packet_id = "theory:generic-consumer-replay"
    theory_packet = {
        "artifact_kind": "TheoryDerivationPacket",
        "packet_id": theory_packet_id,
        "problem_card": {"estimand": "a generic scalar"},
        "estimator_specs": [],
        "theorem_cards": [],
    }
    proposal_id = "simulation-proposal:generic-parent"
    proposal = {
        "artifact_kind": "SimulationEngineerProposalPacket",
        "packet_id": proposal_id,
        "source_agent": "LLMSimulationEngineerAgent",
        "source_provider": "anthropic",
        "backend_provider_name": "anthropic",
        "model": "claude-haiku-4-5-20251001",
        "model_tier": "haiku",
        "scientific_source_transport": "native_client_tools",
        "simulation_targets": [],
        "metric_contracts": [],
    }
    exact_source = (
        "def run_sandbox(seed, replicates):\n"
        "    return {'generic_metric': float(replicates)}\n"
    )
    prior_manifest_id = "simulation:generic-consumer-parent"
    prior_manifest = {
        "schema_version": 1,
        "artifact_kind": "RuntimeSimulationManifest",
        "manifest_id": prior_manifest_id,
        "question": runtime_module._question_to_payload(question),
        "theory_packet_id": theory_packet_id,
        "llm_simulation_engineer_proposal_id": proposal_id,
        "generated_simulation_sandbox_prototypes": [
            {
                "simulation_id": "generic-consumer",
                "prototype_status": "FAILED",
                "language": "python",
                "requested_execution_profile": "stdlib",
                "executor_profile": "stdlib",
                "dependencies": [],
                "required_estimator_ids": [],
                "source_code": exact_source,
                "script_hash": runtime_module.stable_hash(exact_source),
            }
        ],
    }
    context = _full_evidence_context(question.id)
    context["theory_packet_id"] = theory_packet_id
    context["empirical_evaluation_phase"] = (
        runtime_module.EMPIRICAL_EVALUATION_PHASE_EXPLORATORY
    )
    observed_sources: list[str] = []

    class Provider:
        @staticmethod
        def generate_client_tool_turn(*_args, **_kwargs):
            raise AssertionError("passing exact replay must not open a source turn")

    class SimulationAgent:
        provider = Provider()
        propose_calls = 0

        @classmethod
        def propose(cls, **_kwargs):
            cls.propose_calls += 1
            raise AssertionError("consumer replay must bypass planning")

        @staticmethod
        def iterate_code_with_tools(**_kwargs):
            raise AssertionError("passing exact replay must not revise source")

    def run_generated_simulation_sandbox(**kwargs):
        source = str(kwargs["code_draft"]["code"])
        observed_sources.append(source)
        return (
            {
                "simulation_id": str(kwargs["simulation_id"]),
                "prototype_status": "EXECUTED",
                "executor": "generated_simulation_sandbox",
                "language": "python",
                "requested_execution_profile": "stdlib",
                "executor_profile": "stdlib",
                "dependencies": [],
                "required_estimator_ids": [],
                "source_code": source,
                "script_hash": runtime_module.stable_hash(source),
                "smoke_passed": True,
                "execution_smoke_passed": True,
                "execution_attempted": True,
                "metrics": {"generic_metric": 8.0},
                "metric_contracts": [],
                "metric_contract_evaluation": {},
            },
            ToolCallRecord(
                tool_name="python.generated_simulation_sandbox",
                exit_status="0",
            ),
        )

    monkeypatch.setattr(
        runtime_module,
        "_run_generated_simulation_sandbox",
        run_generated_simulation_sandbox,
    )
    subsystem = runtime_module.SimulationEvaluatorRuntimeSubsystem(
        proposal_agent=SimulationAgent(),
        sandbox_root=tmp_path / "simulation",
        semantic_reviewer_available=False,
        semantic_review_max_revisions=2,
    )
    task = AgentTask(
        task_id="simulation-consumer-resume:generic",
        owner_subsystem="SimulationEvaluator",
        objective="Rerun the exact model-authored consumer source.",
        inputs={
            "question": runtime_module._question_to_payload(question),
            "theory_packet_id": theory_packet_id,
            "n_runs": 8,
            "seed": 11,
            "empirical_evaluation_phase": "exploratory",
            "consumer_resume_manifest": prior_manifest,
            "architect_context": context,
        },
        budget={
            runtime_module.SCIENTIFIC_CONSUMER_REVISION_BUDGET_KEY: {
                "lineage_id": "scientific_consumer_lineage:generic",
                "revisions_used": 1,
                "max_revisions": 2,
            }
        },
    )
    result = subsystem.run(
        task,
        BlackboardState(
            project_id=question.id,
            artifacts={
                theory_packet_id: theory_packet,
                proposal_id: proposal,
                prior_manifest_id: prior_manifest,
            },
        ),
    )

    assert SimulationAgent.propose_calls == 0
    assert observed_sources == [exact_source]
    manifests = [
        artifact
        for artifact in result.produced_artifacts.values()
        if isinstance(artifact, dict)
        and artifact.get("artifact_kind") == "RuntimeSimulationManifest"
    ]
    assert len(manifests) == 1
    assert manifests[0]["consumer_resume_manifest_id"] == prior_manifest_id
    assert manifests[0]["consumer_resume_exact_source_replayed"] is True
    assert any(
        observation.observation_type
        == "scientific_consumer_continuation_restored"
        for observation in result.observations
    )


def test_semantic_review_resumes_exact_simulation_source_without_planning(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    question = OpenResearchQuestion(
        id="generic-reviewed-source-resume",
        title="Revise one reviewed simulation source",
        description="Return an external semantic finding to its source workspace.",
    )
    theory_packet_id = "theory:generic-reviewed-source-resume"
    theory_packet = {
        "artifact_kind": "TheoryDerivationPacket",
        "packet_id": theory_packet_id,
        "problem_card": {"estimand": "a generic scalar"},
        "estimator_specs": [],
        "theorem_cards": [],
    }
    proposal_id = "simulation-proposal:generic-reviewed-source"
    proposal = {
        "artifact_kind": "SimulationEngineerProposalPacket",
        "packet_id": proposal_id,
        "source_agent": "LLMSimulationEngineerAgent",
        "model": "claude-haiku-4-5-20251001",
        "model_tier": "haiku",
        "simulation_code_drafts": [],
        "metric_contracts": [],
    }
    exact_source = (
        "def run_sandbox(seed, replicates):\n"
        "    return {'generic_metric': 0.0}\n"
    )
    revised_source = exact_source.replace("0.0", "1.0")
    parent_manifest_id = "simulation:generic-reviewed-source-parent"
    parent_manifest = {
        "artifact_kind": "RuntimeSimulationManifest",
        "manifest_id": parent_manifest_id,
        "question": runtime_module._question_to_payload(question),
        "theory_packet_id": theory_packet_id,
        "llm_simulation_engineer_proposal_id": proposal_id,
        "generated_simulation_sandbox_prototypes": [
            {
                "simulation_id": "generic-reviewed-source",
                "prototype_status": "EXECUTED",
                "language": "python",
                "requested_execution_profile": "stdlib",
                "executor_profile": "stdlib",
                "dependencies": [],
                "required_estimator_ids": [],
                "source_code": exact_source,
                "script_hash": runtime_module.stable_hash(exact_source),
            }
        ],
    }
    feedback = {
        "artifact_kind": "RuntimeGeneratedCodeSemanticReviewFeedback",
        "feedback_type": "generated_code_semantic_review_feedback",
        "question_id": question.id,
        "source_subsystem": "SimulationEvaluator",
        "source_manifest_id": parent_manifest_id,
        "source_lineage": {
            "source_manifest_hash": runtime_module.stable_hash(parent_manifest),
        },
        "overall_verdict": "REVISE",
        "findings": [
            {
                "summary": "The emitted metric has the wrong declared meaning.",
                "observed_behavior": "The source emits the unrelated scalar zero.",
                "expected_behavior": "The source should emit the target scalar.",
            }
        ],
        "source_revision_assessment": {
            "current_source_edit_sufficient": True,
        },
    }
    context = _full_evidence_context(question.id)
    context["theory_packet_id"] = theory_packet_id
    context["empirical_evaluation_phase"] = (
        runtime_module.EMPIRICAL_EVALUATION_PHASE_EXPLORATORY
    )
    source_inputs: list[dict[str, object]] = []
    source_observations: list[dict[str, object]] = []
    executed_sources: list[str] = []

    class Provider:
        @staticmethod
        def generate_client_tool_turn(*_args, **_kwargs):
            raise AssertionError("the fake source workspace owns model turns")

    class SimulationAgent:
        provider = Provider()
        propose_calls = 0

        @classmethod
        def propose(cls, **_kwargs):
            cls.propose_calls += 1
            raise AssertionError("semantic source continuation must bypass planning")

        @staticmethod
        def iterate_code_with_tools(**kwargs):
            source_inputs.append(dict(kwargs["code_draft"]))
            source_observations.append(dict(kwargs["initial_observation"]))
            candidate = {
                "language": "python",
                "execution_profile": "stdlib",
                "dependencies": [],
                "entrypoint": "run_sandbox",
                "code": revised_source,
            }
            check = dict(kwargs["check_candidate"](candidate))
            return ScientificCodeWorkspaceResult(
                code_draft=candidate,
                check_result=check,
                evidence={
                    "model_owned_source": True,
                    "runtime_edited_source": False,
                    "accepted": check["accepted"],
                },
            )

    def run_generated_simulation_sandbox(**kwargs):
        source = str(kwargs["code_draft"]["code"])
        executed_sources.append(source)
        return (
            {
                "simulation_id": str(kwargs["simulation_id"]),
                "prototype_status": "EXECUTED",
                "executor": "generated_simulation_sandbox",
                "language": "python",
                "requested_execution_profile": "stdlib",
                "executor_profile": "stdlib",
                "dependencies": [],
                "required_estimator_ids": [],
                "source_code": source,
                "script_hash": runtime_module.stable_hash(source),
                "smoke_passed": True,
                "execution_smoke_passed": True,
                "execution_attempted": True,
                "metrics": {"generic_metric": 1.0},
                "metric_contracts": [],
                "metric_contract_evaluation": {},
            },
            ToolCallRecord(tool_name="python.generated_simulation_sandbox"),
        )

    monkeypatch.setattr(
        runtime_module,
        "_run_generated_simulation_sandbox",
        run_generated_simulation_sandbox,
    )
    result = runtime_module.SimulationEvaluatorRuntimeSubsystem(
        proposal_agent=SimulationAgent(),
        sandbox_root=tmp_path / "simulation",
        semantic_reviewer_available=False,
    ).run(
        AgentTask(
            task_id="semantic-source-resume:generic",
            owner_subsystem="SimulationEvaluator",
            objective="Continue the exact reviewed source workspace.",
            inputs={
                "question": runtime_module._question_to_payload(question),
                "theory_packet_id": theory_packet_id,
                "n_runs": 8,
                "seed": 11,
                "empirical_evaluation_phase": (
                    runtime_module.EMPIRICAL_EVALUATION_PHASE_EXPLORATORY
                ),
                "architect_context": context,
                "environment_feedback": feedback,
            },
        ),
        BlackboardState(
            project_id=question.id,
            artifacts={
                theory_packet_id: theory_packet,
                proposal_id: proposal,
                parent_manifest_id: parent_manifest,
            },
        ),
    )

    assert SimulationAgent.propose_calls == 0
    assert source_inputs[0]["code"] == exact_source
    assert source_observations[0]["findings"] == feedback["findings"]
    assert executed_sources == [revised_source]
    manifest = next(
        artifact
        for artifact in result.produced_artifacts.values()
        if isinstance(artifact, dict)
        and artifact.get("artifact_kind") == "RuntimeSimulationManifest"
    )
    assert manifest["source_revision_parent_manifest_id"] == parent_manifest_id
    assert manifest["planning_model_call_used"] is False
    assert any(
        row.observation_type == "simulation_source_revision_restored"
        for row in result.observations
    )


def test_confirmatory_metric_failure_is_blind_to_source_and_reviewed_before_release(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    question = OpenResearchQuestion(
        id="generic-confirmatory-blinding",
        title="Blind one confirmatory outcome",
        description="Keep a frozen metric result away from its source author.",
    )
    theory_packet_id = "theory:generic-confirmatory-blinding"
    theory_packet = {
        "artifact_kind": "TheoryDerivationPacket",
        "packet_id": theory_packet_id,
        "problem_card": {"estimand": "a generic scalar"},
        "estimator_specs": [],
        "theorem_cards": [],
    }
    context = _full_evidence_context(question.id)
    context["theory_packet_id"] = theory_packet_id
    context["empirical_evaluation_phase"] = "confirmatory"
    context["architect_runtime_plan"]["evidence_contract"].update(
        {
            "evaluation_mode": "research_eval",
            "formal_verification_policy": "advisory",
            "formal_required_for_final": False,
        }
    )
    context["runtime_requested_evidence_contract"] = {
        "evaluation_mode": "research_eval"
    }
    context["cross_family_evaluation_protocol"] = {
        "protocol_fingerprint": "protocol:generic-confirmatory-blinding",
        "candidate_gate_independence_required": True,
        "post_outcome_fresh_cohort_required": True,
        "confirmatory_candidate_seed_blinding_required": True,
    }
    source_checks: list[dict[str, object]] = []
    source_initial_observations: list[dict[str, object]] = []
    source_workspace_operations: list[str] = []
    proposal_calls: list[dict[str, object]] = []
    sandbox_calls: list[dict[str, object]] = []

    class Provider:
        @staticmethod
        def generate_client_tool_turn(*_args, **_kwargs):
            raise AssertionError("the fake source workspace owns model turns")

    class SimulationAgent:
        provider = Provider()
        propose_calls = 0
        source_calls = 0

        @classmethod
        def propose(cls, **kwargs):
            cls.propose_calls += 1
            proposal_calls.append(dict(kwargs))
            return {
                "artifact_kind": "SimulationEngineerProposalPacket",
                "packet_id": "simulation-proposal:confirmatory-blinding",
                "source_agent": "LLMSimulationEngineerAgent",
                "provider": "anthropic",
                "provider_name": "anthropic",
                "backend_provider": "anthropic",
                "backend_provider_name": "anthropic",
                "model": "claude-haiku-4-5-20251001",
                "model_tier": "haiku",
                "scientific_source_transport": "native_client_tools",
                "simulation_targets": [
                    {"procedure_id": "confirmatory-simulation"}
                ],
                "simulation_code_drafts": [
                    {
                        "simulation_id": "confirmatory-simulation",
                        "required_estimator_ids": [],
                    }
                ],
                "metric_contracts": [],
            }

        @classmethod
        def iterate_code_with_tools(cls, **kwargs):
            cls.source_calls += 1
            source_initial_observations.append(
                dict(kwargs["initial_observation"])
            )
            source_workspace_operations.append(kwargs["workspace_operation"])
            candidate = {
                "language": "python",
                "execution_profile": "stdlib",
                "dependencies": [],
                "entrypoint": "run_sandbox",
                "code": (
                    "def run_sandbox(seed, replicates):\n"
                    "    return {'generic_metric': 0.2}\n"
                ),
            }
            check = dict(kwargs["check_candidate"](candidate))
            source_checks.append(check)
            return ScientificCodeWorkspaceResult(
                code_draft=candidate,
                check_result=check,
                evidence={
                    "workspace_operation": "initial_authoring",
                    "model_owned_source": True,
                    "runtime_edited_source": False,
                    "accepted": check["accepted"],
                },
            )

    def run_generated_simulation_sandbox(**kwargs):
        sandbox_calls.append(dict(kwargs))
        source = str(kwargs["code_draft"]["code"])
        diagnostic = bool(
            kwargs["validation_context"].get("source_authoring_diagnostic")
        )
        value = 0.95 if diagnostic else 0.2
        metrics = {"generic_metric": value}
        phase = "diagnostic" if diagnostic else "confirmatory"
        source_path = tmp_path / f"{phase}.py"
        result_path = tmp_path / f"{phase}.json"
        source_path.write_text(source, encoding="utf-8")
        result_path.write_text(json.dumps(metrics), encoding="utf-8")
        return (
            {
                "simulation_id": str(kwargs["simulation_id"]),
                "prototype_status": (
                    "EXECUTED" if diagnostic else "FAILED_METRIC_GATE"
                ),
                "executor": "generated_simulation_sandbox",
                "language": "python",
                "requested_execution_profile": "stdlib",
                "executor_profile": "stdlib",
                "dependencies": [],
                "required_estimator_ids": [],
                "source_code": source,
                "script_path": str(source_path),
                "script_hash": runtime_module.stable_hash(source),
                "result_path": str(result_path),
                "result_hash": runtime_module.stable_hash(metrics),
                "metrics": metrics,
                "runtime_seed": kwargs["seed"],
                "runtime_replicates": kwargs["n_runs"],
                "smoke_passed": diagnostic,
                "execution_smoke_passed": True,
                "execution_attempted": True,
                "returncode": 0,
                "stdout_summary": f"generic_metric={value}",
                "metric_gate_errors": (
                    []
                    if diagnostic
                    else ["observed 0.2 is below frozen 0.9"]
                ),
                "metric_contracts": [
                    {
                        "contract_id": "frozen-gate",
                        "metric_semantics": "generic scalar accuracy",
                    }
                ],
                "metric_contract_set_id": "metric-contracts:frozen",
                "metric_requirement_set_id": "metric-requirements:frozen",
                "metric_contract_evaluation": {
                    "n_contracts": 1,
                    "n_passed": 1 if diagnostic else 0,
                    "n_failed": 0 if diagnostic else 1,
                    "evaluations": [
                        {
                            "contract_id": "frozen-gate",
                            "passed": diagnostic,
                            "resolved_values_preview": [value],
                            "aggregate_value": value,
                        }
                    ],
                },
            },
            ToolCallRecord(
                tool_name="python.generated_simulation_sandbox",
                exit_status="0",
            ),
        )

    monkeypatch.setattr(
        runtime_module,
        "_runtime_simulation_metric_protocol_guard",
        lambda **_kwargs: None,
    )
    monkeypatch.setattr(
        runtime_module,
        "generated_metric_runtime_replicates_from_context",
        lambda *_args, **_kwargs: 7_300,
    )
    monkeypatch.setattr(
        runtime_module,
        "_runtime_requires_generated_simulation_code",
        lambda *_args, **_kwargs: True,
    )
    monkeypatch.setattr(
        runtime_module,
        "_runtime_requires_typed_metric_contracts",
        lambda *_args, **_kwargs: False,
    )
    monkeypatch.setattr(
        runtime_module,
        "_runtime_requires_generated_algorithm_code",
        lambda *_args, **_kwargs: False,
    )
    monkeypatch.setattr(
        runtime_module,
        "_run_generated_simulation_sandbox",
        run_generated_simulation_sandbox,
    )
    subsystem = runtime_module.SimulationEvaluatorRuntimeSubsystem(
        proposal_agent=SimulationAgent(),
        sandbox_root=tmp_path / "simulation",
        semantic_reviewer_available=True,
        semantic_review_max_revisions=1,
    )
    task = AgentTask(
        task_id="simulation:generic-confirmatory-blinding",
        owner_subsystem="SimulationEvaluator",
        objective="Execute one frozen confirmatory simulation.",
        inputs={
            "question": runtime_module._question_to_payload(question),
            "theory_packet_id": theory_packet_id,
            "n_runs": 8,
            "seed": 11,
            "empirical_evaluation_phase": "confirmatory",
            "architect_context": context,
        },
        budget={
            runtime_module.SCIENTIFIC_CONSUMER_REVISION_BUDGET_KEY: {
                "lineage_id": "scientific_consumer_lineage:preserved",
                "revisions_used": 1,
                "max_revisions": 2,
                "budget_exhausted": False,
            }
        },
    )
    blackboard = BlackboardState(
        project_id=question.id,
        artifacts={theory_packet_id: theory_packet},
    )

    result = subsystem.run(task, blackboard)

    assert SimulationAgent.propose_calls == 1
    assert proposal_calls[0]["withhold_seed_from_model"] is True
    assert proposal_calls[0]["n_runs"] == 7_300
    assert SimulationAgent.source_calls == 1
    assert source_checks[0]["accepted"] is True
    source_observation = source_checks[0]["prototype"]
    assert "empirical_outcomes_withheld" not in source_observation
    assert source_observation["metrics_preview"] == {"generic_metric": 0.95}
    assert source_observation["runtime_replicates"] == 7_300
    assert source_observation["runtime_seed"] != 11
    assert "0.2" not in str(source_observation)
    assert "metric_gate_errors" not in source_observation
    assert result.status == "REROUTE"
    assert result.next_task is not None
    assert result.next_task.owner_subsystem == (
        runtime_module.GENERATED_CODE_SEMANTIC_REVIEWER_SUBSYSTEM
    )
    manifest = next(
        artifact
        for artifact in result.produced_artifacts.values()
        if isinstance(artifact, dict)
        and artifact.get("artifact_kind") == "RuntimeSimulationManifest"
    )
    assert manifest["simulation_passed"] is False
    assert manifest["generated_simulation_source_valid"] is True
    assert manifest["confirmatory_outcomes_withheld_from_source"] is True
    assert manifest["confirmatory_candidate_seed_withheld_from_model"] is True
    cohort = manifest["confirmatory_evaluation_cohort"]
    assert cohort["cohort_index"] == 0
    assert cohort["seed"] == 11
    assert cohort["candidate_model_seed_disclosure"] == "WITHHELD"
    work_order = next(
        artifact
        for artifact in result.produced_artifacts.values()
        if isinstance(artifact, dict)
        and artifact.get("artifact_kind")
        == "RuntimeGeneratedCodeSemanticReviewWorkOrder"
    )
    all_artifacts = {**blackboard.artifacts, **result.produced_artifacts}
    deferred_task = restore_agent_task_continuation(
        all_artifacts[work_order["deferred_next_task_continuation_id"]],
        all_artifacts,
    )
    assert deferred_task.owner_subsystem == "CriticEvaluator"
    feedback_ref = deferred_task.inputs["environment_feedback"]
    assert feedback_ref["artifact_kind"] == "RuntimeArtifactRef"
    feedback = resolve_runtime_artifact_references(
        feedback_ref,
        all_artifacts,
    )
    assert feedback["feedback_type"] == "confirmatory_simulation_outcome"
    assert feedback["source_subsystem"] == "SimulationEvaluator"
    assert feedback["execution_results_observed"] is True
    assert feedback["confirmatory_evaluation_cohort"] == cohort
    assert feedback["unchanged_source_retry_authorized"] is False
    assert feedback["outcome_informed_source_revision_authorized"] is False
    assert feedback["terminal_gap_reporting_required"] is True
    assert runtime_module.SCIENTIFIC_CONSUMER_REVISION_BUDGET_KEY not in feedback
    assert feedback["empirical_outcomes"][0]["metric_gate_errors"]
    assert SimulationAgent.propose_calls == 1
    assert SimulationAgent.source_calls == 1
    assert source_workspace_operations == ["initial_authoring"]
    assert len(source_initial_observations) == 1
    assert len(sandbox_calls) == 2
    diagnostic_call, confirmatory_call = sandbox_calls
    assert diagnostic_call["n_runs"] == 7_300
    assert confirmatory_call["n_runs"] == 7_300
    assert diagnostic_call["seed"] != confirmatory_call["seed"] == 11
    assert diagnostic_call["validation_context"][
        "source_authoring_diagnostic"
    ] is True
    assert confirmatory_call["validation_context"][
        "source_authoring_diagnostic"
    ] is False
    assert "authoring-diagnostic" in str(diagnostic_call["sandbox_dir"])
    assert "authoring-diagnostic" not in str(confirmatory_call["sandbox_dir"])
    assert not any(
        isinstance(artifact, dict)
        and artifact.get("artifact_kind")
        == "RuntimeConfirmatoryEvaluationCohortTransition"
        for artifact in result.produced_artifacts.values()
    )
    assert any(
        observation.observation_type
        == "confirmatory_outcome_routed_to_terminal_evidence"
        for observation in result.observations
    )


def test_architect_algorithm_route_restores_source_and_frozen_simulation() -> None:
    question = OpenResearchQuestion(
        id="generic-confirmatory-source-route",
        title="Resume one model-owned algorithm source",
        description="Revalidate a revised dependency on a fresh cohort.",
    )
    theory_packet_id = "theory:generic-confirmatory-source-route"
    algorithm_manifest_id = "algorithm:generic-confirmatory-source-route"
    algorithm_manifest = {
        "artifact_kind": "RuntimeAlgorithmSandboxManifest",
        "manifest_id": algorithm_manifest_id,
        "theory_packet_id": theory_packet_id,
    }
    simulation_manifest_id = "simulation:generic-confirmatory-source-route"
    simulation_manifest = {
        "artifact_kind": "RuntimeSimulationManifest",
        "manifest_id": simulation_manifest_id,
        "question": runtime_module._question_to_payload(question),
        "theory_packet_id": theory_packet_id,
    }
    old_cohort = {
        "artifact_kind": "RuntimeConfirmatoryEvaluationCohort",
        "cohort_id": "cohort:old",
        "seed": 11,
    }
    new_cohort = {
        "artifact_kind": "RuntimeConfirmatoryEvaluationCohort",
        "cohort_id": "cohort:fresh",
        "seed": 1_000_014,
    }
    deferred_simulation = AgentTask(
        task_id="simulation-confirmatory-resume:generic",
        owner_subsystem="SimulationEvaluator",
        objective="Replay the exact frozen simulation source.",
        inputs={
            "question": runtime_module._question_to_payload(question),
            "theory_packet_id": theory_packet_id,
            "algorithm_sandbox_manifest_id": algorithm_manifest_id,
            "consumer_resume_manifest": simulation_manifest,
            "architect_context": {
                "theory_packet_id": theory_packet_id,
                "algorithm_sandbox_manifest_id": algorithm_manifest_id,
                "simulation_manifest_id": simulation_manifest_id,
                runtime_module.CONFIRMATORY_EVALUATION_COHORT_CONTEXT_KEY: (
                    old_cohort
                ),
            },
            "seed": 11,
        },
    )
    _, continuation, continuation_artifacts = (
        runtime_module.materialize_agent_task_continuation(
            deferred_simulation,
            linked_input_references={
                runtime_module.stable_hash(simulation_manifest): (
                    runtime_artifact_reference(
                        simulation_manifest_id,
                        simulation_manifest,
                    )
                )
            },
        )
    )
    continuation_ref = runtime_module.agent_task_continuation_reference(
        continuation
    )
    source_owner = {
        "source_owner_subsystem": "AlgorithmEngineer",
        "source_manifest_id": algorithm_manifest_id,
        "source_manifest_hash": runtime_module.stable_hash(algorithm_manifest),
        "dependency_artifact_ids": ["generic-estimator"],
        "dependency_artifact_hashes": {
            "generic-estimator": "algorithm-source-hash"
        },
        "consumer_source_artifacts": [
            {
                "artifact_id": "generic-simulation",
                "source_hash": "simulation-source-hash",
                "evaluation_contract_hash": "frozen-contract-hash",
            }
        ],
        "consumer_observations_by_dependency": {
            "generic-estimator": [
                {
                    "consumer_artifact_id": "generic-simulation",
                    "observation": {"metric_gate_errors": ["failed"]},
                }
            ]
        },
    }
    feedback = {
        "artifact_kind": "RuntimeConfirmatorySimulationOutcome",
        "feedback_type": "confirmatory_simulation_outcome",
        "failure_classification": "confirmatory_simulation_metric_gate_failed",
        "feedback_id": "confirmatory-outcome:generic",
        "question_id": question.id,
        "source_manifest_id": simulation_manifest_id,
        "consumer_source_owner": source_owner,
        "deferred_consumer_task_continuation_ref": continuation_ref,
    }
    context = _full_evidence_context(question.id)
    context.update(
        {
            "theory_packet_id": theory_packet_id,
            "algorithm_sandbox_manifest_id": algorithm_manifest_id,
            "simulation_manifest_id": simulation_manifest_id,
            "implementation_gaps": [
                {"estimator_id": "generic-estimator"}
            ],
            "environment_feedback": feedback,
            runtime_module.CONFIRMATORY_EVALUATION_COHORT_CONTEXT_KEY: (
                new_cohort
            ),
        }
    )
    context["architect_feedback_route_decision"] = {
        "artifact_kind": "ArchitectFeedbackRouteDecision",
        "decision": "ROUTE",
        "selected_subsystem": "AlgorithmEngineer",
        "environment_feedback_fingerprint": runtime_module.stable_hash(
            feedback
        ),
        "objective": "Revise the exact failed algorithm source.",
    }
    blackboard = BlackboardState(
        project_id=question.id,
        artifacts={
            theory_packet_id: {
                "artifact_kind": "TheoryDerivationPacket",
                "packet_id": theory_packet_id,
            },
            algorithm_manifest_id: algorithm_manifest,
            simulation_manifest_id: simulation_manifest,
            **continuation_artifacts,
        },
    )

    routing = runtime_module._architect_initial_routing_decision(
        question=question,
        packet={
            "packet_id": "architect:generic-confirmatory-source-route",
            "evidence_contract": {},
            "subsystem_execution_plan": [],
        },
        architect_context=context,
        packet_id="architect-route:generic-confirmatory-source-route",
        runtime_config=ResearchAgentRuntimeConfig(
            generated_code_semantic_review_max_revisions=2
        ),
        blackboard=blackboard,
        requested_subsystem_override="AlgorithmEngineer",
        routing_source_override="architect_feedback_route_model",
        honor_requested_subsystem=True,
    )

    task = routing["task"]
    assert task.owner_subsystem == "AlgorithmEngineer"
    assert task.inputs["source_revision_artifact_ids"] == [
        "generic-estimator"
    ]
    source_ref = task.inputs["consumer_source_manifest"]
    assert source_ref["artifact_kind"] == "RuntimeArtifactRef"
    assert resolve_runtime_artifact_references(
        source_ref,
        blackboard.artifacts,
    ) == algorithm_manifest
    assert task.inputs["confirmatory_source_route_errors"] == []
    budget = task.budget[
        runtime_module.SCIENTIFIC_CONSUMER_REVISION_BUDGET_KEY
    ]
    assert budget["revisions_used"] == 1
    assert budget["max_revisions"] == 2
    assert routing["record"][
        "confirmatory_simulation_revalidation_deferred"
    ] is True

    all_artifacts = {
        **blackboard.artifacts,
        **routing["produced_artifacts"],
    }
    resumed = runtime_module.restore_agent_task_continuation_reference(
        task.inputs["deferred_consumer_task_continuation_ref"],
        all_artifacts,
    )
    assert resumed.owner_subsystem == "SimulationEvaluator"
    assert resumed.inputs["consumer_resume_manifest"] == simulation_manifest
    assert resumed.inputs["seed"] == new_cohort["seed"]
    assert resumed.budget == task.budget
    assert resumed.inputs["architect_context"][
        runtime_module.CONFIRMATORY_EVALUATION_COHORT_CONTEXT_KEY
    ] == new_cohort


def test_confirmatory_output_interface_failure_stays_with_source_owner() -> None:
    question = OpenResearchQuestion(
        id="generic-output-interface",
        title="Generic generated output interface",
        description="Let one source owner correct its generated result shape.",
    )
    checks: list[dict[str, object]] = []

    class Provider:
        @staticmethod
        def generate_client_tool_turn(*_args, **_kwargs):
            raise AssertionError("the fake coding workspace owns model turns")

    class SimulationAgent:
        provider = Provider()

        @staticmethod
        def iterate_code_with_tools(**kwargs):
            wrong = {
                "language": "python",
                "execution_profile": "stdlib",
                "dependencies": [],
                "entrypoint": "run_sandbox",
                "code": "def run_sandbox(seed, replicates): return {'wrong': 0.2}",
            }
            corrected = {
                **wrong,
                "code": "def run_sandbox(seed, replicates): return {'metric': 0.2}",
            }
            first = dict(kwargs["check_candidate"](wrong))
            second = dict(kwargs["check_candidate"](corrected))
            checks.extend((first, second))
            return ScientificCodeWorkspaceResult(
                code_draft=corrected,
                check_result=second,
                evidence={
                    "model_owned_source": True,
                    "runtime_edited_source": False,
                    "accepted": second["accepted"],
                },
            )

    def execute_candidate(candidate):
        corrected = "{'metric': 0.2}" in str(candidate["code"])
        prototype = {
            "execution_attempted": True,
            "execution_smoke_passed": True,
            "smoke_passed": False,
            "metrics": {"metric" if corrected else "wrong": 0.2},
            "metric_contract_evaluation": {
                "evaluations": [
                    {
                        "contract_id": "frozen-gate",
                        "requirement_id": "frozen-requirement",
                        "metric_path": ["metric"],
                        "passed": False,
                        "measurement_interface_valid": corrected,
                        "measurement_interface_status": (
                            "VALID" if corrected else "PATH_UNRESOLVED"
                        ),
                        "measurement_interface_errors": (
                            []
                            if corrected
                            else [
                                "metric contract frozen-gate: metric_path "
                                "/metric resolved no values"
                            ]
                        ),
                    }
                ]
            },
        }
        return prototype, ToolCallRecord(tool_name="python.sandbox")

    prototype, tool_calls = runtime_module._run_source_owner_scientific_workspace(
        proposal_agent=SimulationAgent(),
        question=question,
        artifact_id="simulation:generic-output-interface",
        code_draft={},
        source_deferred=True,
        workspace_context={},
        execute_candidate=execute_candidate,
        failure_identity={},
        confirmatory_result_blind=True,
    )

    assert [row["accepted"] for row in checks] == [False, True]
    assert checks[0]["prototype"]["measurement_interface_failures"][0][
        "measurement_interface_status"
    ] == "PATH_UNRESOLVED"
    assert "0.2" not in str(checks[0]["prototype"])
    assert len(tool_calls) == 2
    assert prototype["scientific_code_workspace"]["runtime_edited_source"] is False


def test_confirmatory_source_validity_reuses_workspace_interface_gate() -> None:
    unresolved = {
        "execution_smoke_passed": True,
        "smoke_passed": False,
        "metric_contract_evaluation": {
            "evaluations": [
                {
                    "contract_id": "frozen-interface",
                    "metric_path": ["results", "literal_key"],
                    "measurement_interface_valid": False,
                    "measurement_interface_status": "PATH_UNRESOLVED",
                    "measurement_interface_errors": [
                        "metric_path /results/literal_key resolved no values"
                    ],
                }
            ]
        },
    }
    resolved_threshold_failure = {
        **unresolved,
        "metric_contract_evaluation": {
            "evaluations": [
                {
                    "contract_id": "frozen-threshold",
                    "metric_path": ["results", "literal_key"],
                    "measurement_interface_valid": True,
                    "measurement_interface_status": "VALID",
                    "measurement_interface_errors": [],
                    "passed": False,
                }
            ]
        },
    }

    assert runtime_module._scientific_source_candidate_accepted(
        unresolved,
        confirmatory_result_blind=True,
    ) is False
    assert runtime_module._scientific_source_candidate_accepted(
        resolved_threshold_failure,
        confirmatory_result_blind=True,
    ) is True


def test_exhausted_consumer_loop_does_not_continue_unrelated_outer_lane() -> None:
    question = OpenResearchQuestion(
        id="generic-consumer-exhausted",
        title="Stop an exhausted source loop",
        description="Do not hide an unresolved consumer failure.",
    )
    context = _full_evidence_context(question.id)
    task = AgentTask(
        task_id="simulation-consumer-resume:exhausted",
        owner_subsystem="SimulationEvaluator",
        objective="Rerun one failed consumer.",
        inputs={
            "question": runtime_module._question_to_payload(question),
            "theory_packet_id": "theory:generic-consumer-exhausted",
            "architect_context": context,
        },
    )
    result = AgentStepResult(
        status="BLOCKED",
        rationale="The source-owner iteration budget is exhausted.",
        failure_classification=(
            "scientific_consumer_revision_budget_exhausted"
        ),
    )

    transitioned = _runtime_transition_policy(
        iteration=12,
        task=task,
        subsystem_name="SimulationEvaluator",
        result=result,
        blackboard=BlackboardState(
            project_id=question.id,
            artifacts={
                "theory:generic-consumer-exhausted": {
                    "artifact_kind": "TheoryDerivationPacket",
                    "packet_id": "theory:generic-consumer-exhausted",
                }
            },
        ),
        runtime_config=ResearchAgentRuntimeConfig(
            evaluation_mode="capability_eval",
            formal_verification_policy="required",
        ),
    )

    assert transitioned is result
    assert transitioned.next_task is None


def test_accepted_source_review_restores_bound_consumer_without_architect() -> None:
    budget = {
        runtime_module.SCIENTIFIC_CONSUMER_REVISION_BUDGET_KEY: {
            "lineage_id": "scientific_consumer_lineage:generic",
            "revisions_used": 1,
            "max_revisions": 2,
        }
    }
    next_task = AgentTask(
        task_id="simulation-consumer-resume:reviewed",
        owner_subsystem="SimulationEvaluator",
        objective="Rerun the exact reviewed consumer.",
        inputs={
            "consumer_resume_manifest": {
                "artifact_kind": "RuntimeSimulationManifest",
                "manifest_id": "simulation:failed",
            },
            "architect_context": {
                "runtime_executed_subsystems": ["SimulationEvaluator"]
            },
        },
        budget=budget,
    )
    result = AgentStepResult(
        status="REROUTE",
        rationale="Independent source review accepted the revised artifact.",
        next_task=next_task,
    )

    transitioned = _runtime_transition_policy(
        iteration=9,
        task=AgentTask(
            task_id="review:algorithm-source",
            owner_subsystem=(
                runtime_module.GENERATED_CODE_SEMANTIC_REVIEWER_SUBSYSTEM
            ),
            objective="Review revised source semantics.",
        ),
        subsystem_name=(
            runtime_module.GENERATED_CODE_SEMANTIC_REVIEWER_SUBSYSTEM
        ),
        result=result,
        blackboard=BlackboardState(project_id="generic-reviewed-source"),
        runtime_config=ResearchAgentRuntimeConfig(
            evaluation_mode="capability_eval",
            formal_verification_policy="required",
        ),
    )

    assert transitioned is result
    assert transitioned.next_task is next_task
    assert transitioned.next_task.owner_subsystem == "SimulationEvaluator"


def test_accepted_review_ledger_preserves_distinct_workspace_lineages() -> None:
    current_algorithm_review = {
        "execution_id": "review:algorithm-current",
        "source_subsystem": "AlgorithmEngineer",
        "source_manifest_id": "algorithm:current",
        "overall_verdict": "ACCEPT",
        "parent_artifact_ids": {"theory_packet_id": "theory:generic"},
    }
    stale_top_level_review = {
        **current_algorithm_review,
        "execution_id": "review:algorithm-stale-copy",
        "source_manifest_id": "algorithm:stale",
    }
    simulation_review = {
        "execution_id": "review:simulation-current",
        "source_subsystem": "SimulationEvaluator",
        "source_manifest_id": "simulation:current",
        "overall_verdict": "ACCEPT",
        "parent_artifact_ids": {
            "theory_packet_id": "theory:generic",
            "algorithm_sandbox_manifest_id": "algorithm:current",
        },
    }

    ledger = runtime_module._runtime_merged_accepted_generated_code_reviews(
        deferred_task_inputs={
            "accepted_generated_code_semantic_reviews": [
                stale_top_level_review
            ],
            "architect_context": {
                "accepted_generated_code_semantic_reviews": [
                    current_algorithm_review
                ]
            },
        },
        accepted_review=simulation_review,
    )

    assert [row["execution_id"] for row in ledger] == [
        "review:algorithm-current",
        "review:simulation-current",
    ]
    context = _full_evidence_context("generic-two-accepted-workspaces")
    context.update(
        {
            "algorithm_sandbox_manifest_id": "algorithm:current",
            "simulation_manifest_id": "simulation:current",
            "accepted_generated_code_semantic_reviews": ledger,
        }
    )
    assert {
        "AlgorithmEngineer",
        "SimulationEvaluator",
    }.issubset(
        runtime_module._runtime_executed_subsystems(
            architect_context=context
        )
    )


def test_algorithm_workspace_blocks_partial_artifact_set_before_review(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    question = OpenResearchQuestion(
        id="generic-partial-algorithm-workspace",
        title="Complete every requested implementation artifact",
        description="Do not independently review a partial coding workspace.",
    )
    theory_packet_id = "theory:generic-partial-algorithm-workspace"
    simulation_manifest_id = "simulation:generic-partial-algorithm-workspace"
    theory_packet = {
        "artifact_kind": "TheoryDerivationPacket",
        "packet_id": theory_packet_id,
        "estimator_specs": [
            {"id": "passing-estimator"},
            {"id": "failed-estimator"},
        ],
    }
    simulation_manifest = {
        "artifact_kind": "RuntimeSimulationManifest",
        "manifest_id": simulation_manifest_id,
        "theory_packet_id": theory_packet_id,
    }

    class ProposalAgent:
        provider = object()

        @staticmethod
        def propose(**_kwargs):
            return {
                "artifact_kind": "AlgorithmEngineerProposalPacket",
                "packet_id": "algorithm-proposal:generic-partial-workspace",
                "source_agent": "LLMAlgorithmEngineerAgent",
                "model": "source-author",
                "model_tier": "haiku",
                "implementation_targets": [
                    {"estimator_id": "passing-estimator"},
                    {"estimator_id": "failed-estimator"},
                ],
                "sandbox_code_drafts": [
                    {"estimator_id": "passing-estimator", "code": "passing"},
                    {"estimator_id": "failed-estimator", "code": "failed"},
                ],
            }

    def run_source_workspace(**kwargs):
        estimator_id = str(kwargs["failure_identity"]["estimator_id"])
        passed = estimator_id == "passing-estimator"
        return {
            "estimator_id": estimator_id,
            "prototype_status": "EXECUTED" if passed else "FAILED",
            "executor": "generated_python_sandbox",
            "language": "python",
            "dependencies": [],
            "execution_attempted": True,
            "execution_smoke_passed": passed,
            "smoke_passed": passed,
            "stderr_summary": "" if passed else "raw execution failure",
        }, []

    monkeypatch.setattr(
        runtime_module,
        "_run_source_owner_scientific_workspace",
        run_source_workspace,
    )
    monkeypatch.setattr(
        runtime_module,
        "_runtime_generated_code_semantic_review_dispatch",
        lambda **_kwargs: pytest.fail(
            "partial implementation was sent to independent review"
        ),
    )
    context = _full_evidence_context(question.id)
    context["theory_packet_id"] = theory_packet_id
    result = runtime_module.AlgorithmEngineerRuntimeSubsystem(
        out_dir=tmp_path,
        n_runs=8,
        seed=7,
        proposal_agent=ProposalAgent(),
        semantic_reviewer_available=True,
    ).run(
        AgentTask(
            task_id="algorithm:generic-partial-workspace",
            owner_subsystem="AlgorithmEngineer",
            objective="Author every requested estimator source.",
            inputs={
                "question": runtime_module._question_to_payload(question),
                "theory_packet_id": theory_packet_id,
                "simulation_manifest_id": simulation_manifest_id,
                "implementation_gaps": [
                    {"estimator_id": "passing-estimator"},
                    {"estimator_id": "failed-estimator"},
                ],
                "architect_context": context,
            },
        ),
        BlackboardState(
            project_id=question.id,
            artifacts={
                theory_packet_id: theory_packet,
                simulation_manifest_id: simulation_manifest,
            },
        ),
    )

    assert result.status == "BLOCKED"
    assert result.next_task is None
    assert result.failure_classification == (
        "generated_algorithm_sandbox_execution_failed"
    )
    blocked = next(
        row
        for row in result.observations
        if row.observation_type == "algorithm_workspace_blocked"
    )
    assert blocked.payload["incomplete_estimator_ids"] == [
        "failed-estimator"
    ]


def test_accepted_simulation_review_completes_current_outer_graph_lane(
    tmp_path: Path,
) -> None:
    question = OpenResearchQuestion(
        id="generic-reviewed-simulation",
        title="Generic reviewed simulation",
        description="Do not rerun an accepted simulation lineage after formalization.",
    )
    theory_packet_id = "theory:generic"
    algorithm_manifest_id = "algorithm:accepted"
    simulation_manifest_id = "simulation:accepted"
    source = (
        "def run_sandbox(seed, replicates):\n"
        "    return {'generic_metric': 1.0}\n"
    )
    result_payload = {"generic_metric": 1.0}
    source_path = tmp_path / "simulation.py"
    result_path = tmp_path / "simulation.json"
    source_path.write_text(source, encoding="utf-8")
    result_path.write_text(json.dumps(result_payload), encoding="utf-8")
    theory_packet = {
        "artifact_kind": "TheoryDerivationPacket",
        "packet_id": theory_packet_id,
    }
    proposal_packet = {
        "artifact_kind": "SimulationEngineerProposalPacket",
        "packet_id": "simulation-proposal:accepted",
        "source_agent": "LLMSimulationEngineerAgent",
        "model": "static-author",
        "model_tier": "haiku",
    }
    source_manifest = {
        "artifact_kind": "RuntimeSimulationManifest",
        "manifest_id": simulation_manifest_id,
        "question": runtime_module._question_to_payload(question),
        "theory_packet_id": theory_packet_id,
        "llm_simulation_engineer_proposal_id": proposal_packet["packet_id"],
        "generated_simulation_sandbox_prototypes": [
            {
                "simulation_id": "generic-simulation",
                "prototype_status": "EXECUTED",
                "executor": "generated_simulation_sandbox",
                "language": "python",
                "source_code": source,
                "script_path": str(source_path),
                "script_hash": runtime_module.stable_hash(source),
                "result_path": str(result_path),
                "result_hash": runtime_module.stable_hash(result_payload),
                "metrics": result_payload,
                "smoke_passed": True,
                "execution_smoke_passed": True,
                "execution_attempted": True,
                "runtime_seed": 7,
                "runtime_replicates": 8,
            }
        ],
    }
    accepted_algorithm_review = {
        "execution_id": "review:algorithm-accepted",
        "source_subsystem": "AlgorithmEngineer",
        "source_manifest_id": algorithm_manifest_id,
        "overall_verdict": "ACCEPT",
        "parent_artifact_ids": {"theory_packet_id": theory_packet_id},
    }
    context = _full_evidence_context(question.id)
    context.update(
        {
            "theory_packet_id": theory_packet_id,
            "algorithm_sandbox_manifest_id": algorithm_manifest_id,
            "accepted_generated_code_semantic_reviews": [
                accepted_algorithm_review
            ],
        }
    )
    source_task = AgentTask(
        task_id="simulation:generic-reviewed-simulation",
        owner_subsystem="SimulationEvaluator",
        objective="Author and execute the simulation source.",
        inputs={
            "question": runtime_module._question_to_payload(question),
            "theory_packet_id": theory_packet_id,
            "algorithm_sandbox_manifest_id": algorithm_manifest_id,
            "architect_context": context,
        },
    )
    deferred_task = AgentTask(
        task_id="formalize:generic-reviewed-simulation",
        owner_subsystem="FormalizationEvaluator",
        objective="Formalize after accepted simulation evidence.",
        inputs={
            "question": runtime_module._question_to_payload(question),
            "theory_packet_id": theory_packet_id,
            "algorithm_sandbox_manifest_id": algorithm_manifest_id,
            "architect_context": context,
        },
    )
    base_artifacts = {
        theory_packet_id: theory_packet,
        proposal_packet["packet_id"]: proposal_packet,
        simulation_manifest_id: source_manifest,
    }
    dispatch = _runtime_generated_code_semantic_review_dispatch(
        task=source_task,
        question=question,
        source_subsystem="SimulationEvaluator",
        source_manifest=source_manifest,
        theory_packet=theory_packet,
        proposal_packet=proposal_packet,
        architect_context=context,
        deferred_next_task=deferred_task,
        blackboard_artifacts=base_artifacts,
        max_revisions=1,
    )
    assert dispatch is not None
    response = {
        "prior_finding_reviews": [],
        "overall_verdict": "ACCEPT",
        "review_document": (
            "# Independent Review\n\nThe exact executed source matches its "
            "supplied theory, interface, arguments, and measurement meaning."
        ),
        "findings": [],
        "source_revision_assessment": {
            "resolution_scope": "NO_PARENT_ARTIFACT_CHANGE_REQUIRED",
            "rationale": "No parent artifact change is required.",
            "evidence_refs": [
                "/exact_executed_artifacts/0/exact_source_code"
            ],
        },
    }
    reviewer = LLMGeneratedCodeSemanticReviewerAgent(
        provider=StaticJSONGeneratorBackend(response),
        config=GeneratedCodeSemanticReviewerConfig(
            provider_name="static",
            model=LIVE_EVALUATION_CLAUDE_MODEL,
            model_tier="haiku",
            max_validation_retries=0,
        ),
    )
    blackboard = BlackboardState(project_id=question.id)
    blackboard.artifacts.update(base_artifacts)
    blackboard.artifacts.update(dispatch["artifacts"])

    outcome = runtime_module.GeneratedCodeSemanticReviewerRuntimeSubsystem(
        reviewer=reviewer,
        max_revisions=1,
    ).run(dispatch["next_task"], blackboard)

    assert outcome.status == "REROUTE", (
        outcome.rationale,
        outcome.failure_classification,
        outcome.observations,
    )
    assert outcome.next_task is not None
    assert outcome.next_task.owner_subsystem == "FormalizationEvaluator"
    review_documents = [
        row
        for row in outcome.produced_artifacts.values()
        if isinstance(row, dict)
        and row.get("artifact_kind") == "GeneratedCodeSemanticReviewDocument"
    ]
    assert len(review_documents) == 1
    assert review_documents[0]["content"].startswith("# Independent Review")
    next_context = outcome.next_task.inputs["architect_context"]
    assert outcome.next_task.inputs["simulation_manifest_id"] == (
        simulation_manifest_id
    )
    assert next_context["simulation_manifest_id"] == simulation_manifest_id
    assert "SimulationEvaluator" in runtime_module._runtime_executed_subsystems(
        architect_context=next_context
    )

    after_formalization = _runtime_transition_policy(
        iteration=10,
        task=outcome.next_task,
        subsystem_name="FormalizationEvaluator",
        result=AgentStepResult(
            status="BLOCKED",
            rationale="The formal workspace recorded its exact blocker.",
            failure_classification="formalizer_client_tool_loop_exhausted",
        ),
        blackboard=BlackboardState(
            project_id=question.id,
            artifacts={
                **blackboard.artifacts,
                **outcome.produced_artifacts,
            },
        ),
        runtime_config=ResearchAgentRuntimeConfig(
            evaluation_mode="capability_eval",
            formal_verification_policy="required",
        ),
    )

    assert after_formalization.next_task is not None
    assert after_formalization.next_task.owner_subsystem == "CriticEvaluator"


def test_review_acceptance_does_not_reopen_the_same_algorithm_task() -> None:
    question = OpenResearchQuestion(
        id="generic-reviewed-continuation",
        title="Generic reviewed continuation",
        description="Continue after independent source acceptance.",
    )
    context = _full_evidence_context(question.id)
    context["algorithm_sandbox_manifest_id"] = "algorithm:accepted"
    context["accepted_generated_code_semantic_reviews"] = [
        {
            "source_subsystem": "AlgorithmEngineer",
            "source_manifest_id": "algorithm:accepted",
            "overall_verdict": "ACCEPT",
            "parent_artifact_ids": {"theory_packet_id": "theory:generic"},
        }
    ]
    context["runtime_outer_graph_workspace_outcomes"] = [
        {
            "source_task_id": "formalize:completed",
            "source_subsystem": "FormalizationEvaluator",
            "local_status": "BLOCKED",
            "parent_artifact_ids": {"theory_packet_id": "theory:generic"},
        }
    ]
    repeated_formal_task = AgentTask(
        task_id="formalize:completed",
        owner_subsystem="FormalizationEvaluator",
        objective="Resume the already observed formal lane.",
        inputs={
            "question": runtime_module._question_to_payload(question),
            "theory_packet_id": "theory:generic",
            "algorithm_sandbox_manifest_id": "algorithm:accepted",
            "architect_context": context,
        },
    )

    continued = _runtime_transition_policy(
        iteration=15,
        task=AgentTask(
            task_id="semantic-review:accepted",
            owner_subsystem="GeneratedCodeSemanticReviewer",
            objective="Record independent acceptance.",
            inputs={
                "question": runtime_module._question_to_payload(question),
                "architect_context": context,
            },
        ),
        subsystem_name="GeneratedCodeSemanticReviewer",
        result=AgentStepResult(
            status="REROUTE",
            rationale="Independent review accepted the current source.",
            next_task=repeated_formal_task,
        ),
        blackboard=BlackboardState(
            project_id=question.id,
            artifacts={"theory:generic": {"packet_id": "theory:generic"}},
        ),
        runtime_config=ResearchAgentRuntimeConfig(
            evaluation_mode="capability_eval",
            formal_verification_policy="required",
        ),
    )

    assert continued.status == "REROUTE"
    assert continued.next_task is not None
    assert continued.next_task.owner_subsystem == "SimulationEvaluator"
    assert continued.next_task.task_id != "algorithm:generic-reviewed-continuation"
    observed = continued.observations[-1].payload
    assert "AlgorithmEngineer" in observed["executed_subsystems"]
    assert "FormalizationEvaluator" in observed["executed_subsystems"]


def test_failed_theory_revision_does_not_continue_rejected_parent_lineage() -> None:
    question = OpenResearchQuestion(
        id="generic-rejected-theory-revision",
        title="Generic rejected theory revision",
        description="Do not execute downstream work from a rejected theory parent.",
    )
    task = AgentTask(
        task_id="theory:generic-rejected-theory-revision",
        owner_subsystem="TheoryDeveloper",
        objective="Revise a theory artifact rejected by independent preflight.",
        inputs={
            "question": runtime_module._question_to_payload(question),
            "theory_packet_id": "theory:rejected-parent",
            "architect_context": _full_evidence_context(question.id),
        },
    )
    result = AgentStepResult(
        status="BLOCKED",
        rationale="The model-owned theory workspace exhausted its tool budget.",
        failure_classification="theory_developer_packet_validation_failed",
    )

    stopped = _runtime_transition_policy(
        iteration=6,
        task=task,
        subsystem_name="TheoryDeveloper",
        result=result,
        blackboard=BlackboardState(
            project_id=question.id,
            artifacts={
                "theory:rejected-parent": {
                    "packet_id": "theory:rejected-parent"
                }
            },
        ),
        runtime_config=ResearchAgentRuntimeConfig(
            evaluation_mode="capability_eval",
            formal_verification_policy="required",
        ),
    )

    assert stopped is result
    assert stopped.status == "BLOCKED"
    assert stopped.next_task is None


def test_outer_graph_does_not_bypass_missing_theory_prerequisite() -> None:
    question = OpenResearchQuestion(
        id="generic-missing-theory",
        title="Generic missing theory prerequisite",
        description="Do not enter evidence workspaces before theory exists.",
    )
    context = _full_evidence_context(question.id)
    context.pop("theory_packet_id", None)
    task = AgentTask(
        task_id="retrieval:generic-missing-theory",
        owner_subsystem="RetrievalMemory",
        objective="Collect source context before theory development.",
        inputs={
            "question": runtime_module._question_to_payload(question),
            "architect_context": context,
        },
    )

    blocked = _runtime_transition_policy(
        iteration=2,
        task=task,
        subsystem_name="RetrievalMemory",
        result=AgentStepResult(
            status="BLOCKED",
            rationale="No source context was available.",
            failure_classification="retrieval_unavailable",
        ),
        blackboard=BlackboardState(project_id=question.id),
        runtime_config=ResearchAgentRuntimeConfig(
            evaluation_mode="capability_eval",
            formal_verification_policy="required",
        ),
    )

    assert blocked.status == "BLOCKED"
    assert blocked.next_task is None


def test_outer_graph_sends_all_observed_lanes_to_final_critic() -> None:
    question = OpenResearchQuestion(
        id="generic-final-review",
        title="Generic final review",
        description="Aggregate completed and blocked workspace outcomes.",
    )
    context = _full_evidence_context(question.id)
    context["runtime_outer_graph_workspace_outcomes"] = [
        {
            "source_task_id": "formalize:generic-final-review",
            "source_subsystem": "FormalizationEvaluator",
            "local_status": "BLOCKED",
            "parent_artifact_ids": {"theory_packet_id": "theory:generic"},
        },
        {
            "source_task_id": "algorithm:generic-final-review",
            "source_subsystem": "AlgorithmEngineer",
            "local_status": "COMPLETED",
            "parent_artifact_ids": {"theory_packet_id": "theory:generic"},
        },
    ]
    task = AgentTask(
        task_id="simulation:generic-final-review",
        owner_subsystem="SimulationEvaluator",
        objective="Run the final independent empirical lane.",
        inputs={
            "question": runtime_module._question_to_payload(question),
            "theory_packet_id": "theory:generic",
            "algorithm_sandbox_manifest_id": "algorithm:generic",
            "simulation_manifest_id": "simulation:generic",
            "architect_context": context,
        },
    )
    blackboard = BlackboardState(
        project_id=question.id,
        artifacts={"theory:generic": {"packet_id": "theory:generic"}},
    )
    blackboard.handoff_ledger.extend(
        [
            TaskHandoffRecord(
                handoff_id="handoff:formal-algorithm",
                from_task_id="formalize:generic-final-review",
                to_task_id="algorithm:generic-final-review",
                from_subsystem="FormalizationEvaluator",
                to_subsystem="AlgorithmEngineer",
                status="REROUTE",
                rationale="continue required lane",
            ),
            TaskHandoffRecord(
                handoff_id="handoff:algorithm-simulation",
                from_task_id="algorithm:generic-final-review",
                to_task_id=task.task_id,
                from_subsystem="AlgorithmEngineer",
                to_subsystem="SimulationEvaluator",
                status="REROUTE",
                rationale="continue required lane",
            ),
        ]
    )

    continued = _runtime_transition_policy(
        iteration=8,
        task=task,
        subsystem_name="SimulationEvaluator",
        result=AgentStepResult(
            status="BLOCKED",
            rationale="Simulation workspace recorded a typed blocker.",
            failure_classification="simulation_workspace_exhausted",
        ),
        blackboard=blackboard,
        runtime_config=ResearchAgentRuntimeConfig(
            evaluation_mode="capability_eval",
            formal_verification_policy="required",
        ),
    )

    assert continued.status == "REROUTE"
    assert continued.next_task is not None
    assert continued.next_task.owner_subsystem == "CriticEvaluator"
    feedback = continued.next_task.inputs["environment_feedback"]
    assert feedback["source_subsystem"] == "SimulationEvaluator"
    assert feedback["local_status"] == "BLOCKED"


def test_outer_graph_skips_a_downstream_repeat_of_an_exhausted_lane() -> None:
    question = OpenResearchQuestion(
        id="generic-no-repeat",
        title="Generic no-repeat task",
        description="Do not reopen an exhausted lane without Critic feedback.",
    )
    context = _full_evidence_context(question.id)
    context["runtime_outer_graph_workspace_outcomes"] = [
        {
            "source_task_id": "formalize:exhausted",
            "source_subsystem": "FormalizationEvaluator",
            "local_status": "BLOCKED",
            "parent_artifact_ids": {"theory_packet_id": "theory:generic"},
        },
        {
            "source_task_id": "algorithm:complete",
            "source_subsystem": "AlgorithmEngineer",
            "local_status": "COMPLETED",
            "parent_artifact_ids": {"theory_packet_id": "theory:generic"},
        },
    ]
    task = AgentTask(
        task_id="simulation:complete",
        owner_subsystem="SimulationEvaluator",
        objective="Complete empirical evidence.",
        inputs={
            "question": runtime_module._question_to_payload(question),
            "theory_packet_id": "theory:generic",
            "algorithm_sandbox_manifest_id": "algorithm:generic",
            "architect_context": context,
        },
    )
    repeated_formal_task = AgentTask(
        task_id="formalize:automatic-repeat",
        owner_subsystem="FormalizationEvaluator",
        objective="Automatically revisit formalization.",
        inputs={
            "question": runtime_module._question_to_payload(question),
            "theory_packet_id": "theory:generic",
            "algorithm_sandbox_manifest_id": "algorithm:generic",
            "simulation_manifest_id": "simulation:generic",
            "architect_context": context,
        },
    )
    blackboard = BlackboardState(
        project_id=question.id,
        artifacts={"theory:generic": {"packet_id": "theory:generic"}},
    )
    blackboard.handoff_ledger.extend(
        [
            TaskHandoffRecord(
                handoff_id="handoff:formal-algorithm",
                from_task_id="formalize:exhausted",
                to_task_id="algorithm:complete",
                from_subsystem="FormalizationEvaluator",
                to_subsystem="AlgorithmEngineer",
                status="REROUTE",
                rationale="continue required lane",
            ),
            TaskHandoffRecord(
                handoff_id="handoff:algorithm-simulation",
                from_task_id="algorithm:complete",
                to_task_id=task.task_id,
                from_subsystem="AlgorithmEngineer",
                to_subsystem="SimulationEvaluator",
                status="REROUTE",
                rationale="continue required lane",
            ),
        ]
    )

    continued = _runtime_transition_policy(
        iteration=9,
        task=task,
        subsystem_name="SimulationEvaluator",
        result=AgentStepResult(
            status="REROUTE",
            rationale="Empirical lane proposed its conventional formal handoff.",
            next_task=repeated_formal_task,
        ),
        blackboard=blackboard,
        runtime_config=ResearchAgentRuntimeConfig(
            evaluation_mode="capability_eval",
            formal_verification_policy="required",
        ),
    )

    assert continued.next_task is not None
    assert continued.next_task.owner_subsystem == "CriticEvaluator"
    feedback = continued.next_task.inputs["environment_feedback"]
    assert feedback["source_task_id"] == task.task_id
    assert feedback["source_subsystem"] == "SimulationEvaluator"
    assert feedback["local_status"] == "REROUTE"


def test_independent_semantic_review_escalation_keeps_source_out_of_task_payload() -> None:
    question = OpenResearchQuestion(
        id="compact-workspace-replan",
        title="Keep source in artifact storage",
        description="Route only a content reference through the control plane.",
    )
    task = AgentTask(
        task_id="algorithm:compact-workspace-replan",
        owner_subsystem="AlgorithmEngineer",
        objective="Own and execute the complete source.",
        inputs={"question": {"id": question.id}},
    )
    complete_source = "x" * 100_000
    next_task = runtime_module._independent_semantic_review_architect_escalation_task(
        task=task,
        question=question,
        context={"environment_feedback": {"stale": complete_source}},
        revision_feedback={
            "feedback_id": "feedback:compact",
            "feedback_source": "GeneratedCodeSemanticReviewer",
            "failure_classification": (
                "generated_code_semantic_review_lineage_budget_exhausted"
            ),
            "validation_errors": ["raw sandbox failure"],
            "rejected_candidate": {"code": complete_source},
            "proof_evidence_status": "NOT_PROOF_EVIDENCE",
        },
        source_artifact_id="algorithm_manifest:compact",
    )

    routed = next_task.inputs["environment_feedback"]
    assert routed["artifact_kind"] == "RuntimeWorkspaceObservationRef"
    assert routed["source_artifact_id"] == "algorithm_manifest:compact"
    assert routed["validation_errors"] == ["raw sandbox failure"]
    assert "rejected_candidate" not in routed
    assert "environment_feedback" not in next_task.inputs["architect_context"]
    assert complete_source not in repr(next_task.inputs)


def test_cross_artifact_review_assessment_can_escalate_before_budget_exhaustion() -> None:
    question = OpenResearchQuestion(
        id="cross-artifact-review",
        title="Resolve a cross-artifact semantic conflict",
        description="A source-only edit cannot reconcile immutable artifacts.",
    )
    source_task = AgentTask(
        task_id="algorithm:cross-artifact-review",
        owner_subsystem="AlgorithmEngineer",
        objective="Own and execute the complete source.",
        inputs={"question": runtime_module._question_to_payload(question)},
    )
    next_task = runtime_module._independent_semantic_review_architect_escalation_task(
        task=source_task,
        question=question,
        context={},
        revision_feedback={
            "feedback_id": "feedback:cross-artifact",
            "feedback_source": "GeneratedCodeSemanticReviewer",
            "failure_classification": (
                "generated_code_semantic_review_requires_cross_artifact_resolution"
            ),
            "semantic_review_packet_id": "review:cross-artifact",
            "source_revision_assessment": {
                "resolution_scope": "PARENT_ARTIFACT_CHANGE_REQUIRED",
                "rationale": "The immutable theory and protocol conflict.",
                "evidence_refs": [
                    "/review_material/theory_packet",
                    "/review_material/architect_frozen_evidence_contract",
                ],
            },
            "proof_evidence_status": "NOT_PROOF_EVIDENCE",
        },
        source_artifact_id="algorithm_manifest:cross-artifact",
    )

    assert next_task.owner_subsystem == "ArchitectCoordinator"
    observation = next_task.inputs["environment_feedback"]
    assert observation["failure_classification"] == (
        "generated_code_semantic_review_requires_cross_artifact_resolution"
    )
    assert observation["source_artifact_id"] == (
        "algorithm_manifest:cross-artifact"
    )
    assert "unchanged_source_retry_authorized" not in observation
    assert next_task.inputs["architect_context"]["workspace_replan"][
        "failure_classification"
    ] == observation["failure_classification"]
    assert "unchanged_source_retry_authorized" not in (
        next_task.inputs["architect_context"]["workspace_replan"]
    )


def test_cross_artifact_review_skips_another_source_regeneration(tmp_path) -> None:
    question = OpenResearchQuestion(
        id="cross-artifact-runtime-review",
        title="Resolve a cross-artifact semantic conflict",
        description="Review exact generated code against immutable parents.",
    )
    source = "def run_sandbox(seed, replicates):\n    return {'estimate': 1.0}\n"
    result_payload = {"estimate": 1.0}
    source_path = tmp_path / "candidate.py"
    result_path = tmp_path / "result.json"
    source_path.write_text(source, encoding="utf-8")
    result_path.write_text(json.dumps(result_payload), encoding="utf-8")
    theory_packet = {
        "artifact_kind": "TheoryDerivationPacket",
        "packet_id": "theory:cross-artifact-runtime-review",
        "claim": "The frozen meaning conflicts with the implemented statistic.",
    }
    proposal_packet = {
        "artifact_kind": "AlgorithmEngineerProposalPacket",
        "packet_id": "proposal:cross-artifact-runtime-review",
        "source_agent": "LLMAlgorithmEngineerAgent",
        "model": "static-author",
        "model_tier": "haiku",
    }
    source_manifest = {
        "artifact_kind": "RuntimeAlgorithmSandboxManifest",
        "manifest_id": "algorithm_manifest:cross-artifact-runtime-review",
        "prototypes": [
            {
                "estimator_id": "candidate",
                "smoke_passed": True,
                "execution_smoke_passed": True,
                "script_path": str(source_path),
                "script_hash": runtime_module.stable_hash(source),
                "result_path": str(result_path),
                "result_hash": runtime_module.stable_hash(result_payload),
                "metrics": result_payload,
                "runtime_seed": 7,
                "runtime_replicates": 20,
            }
        ],
    }
    deferred_task = AgentTask(
        task_id="formalize:cross-artifact-runtime-review",
        owner_subsystem="FormalizationEvaluator",
        objective="Continue only after accepted generated code.",
        inputs={"question": runtime_module._question_to_payload(question)},
    )
    source_task = AgentTask(
        task_id="algorithm:cross-artifact-runtime-review",
        owner_subsystem="AlgorithmEngineer",
        objective="Author and execute the complete estimator source.",
        inputs={
            "question": runtime_module._question_to_payload(question),
            "architect_context": {},
        },
    )
    base_artifacts = {
        theory_packet["packet_id"]: theory_packet,
        proposal_packet["packet_id"]: proposal_packet,
        source_manifest["manifest_id"]: source_manifest,
    }
    dispatch = _runtime_generated_code_semantic_review_dispatch(
        task=source_task,
        question=question,
        source_subsystem="AlgorithmEngineer",
        source_manifest=source_manifest,
        theory_packet=theory_packet,
        proposal_packet=proposal_packet,
        architect_context={},
        deferred_next_task=deferred_task,
        blackboard_artifacts=base_artifacts,
        max_revisions=3,
    )
    assert dispatch is not None
    response = {
        "prior_finding_reviews": [],
        "overall_verdict": "REVISE",
        "review_document": "# Review\n\nThe immutable parents conflict.",
        "findings": [
            {
                "severity": "high",
                "category": "cross_artifact_conflict",
                "summary": "The immutable theory and frozen meaning conflict.",
                "observed_behavior": "Source implements one supplied meaning.",
                "expected_behavior": "The parent artifacts must identify one meaning.",
                "evidence_refs": [
                    "/theory_packet",
                    "/architect_frozen_evidence_contract",
                ],
            }
        ],
        "source_revision_assessment": {
            "resolution_scope": "PARENT_ARTIFACT_CHANGE_REQUIRED",
            "rationale": "Editing this source cannot reconcile immutable parents.",
            "evidence_refs": [
                "/theory_packet",
                "/architect_frozen_evidence_contract",
            ],
        },
    }
    reviewer = LLMGeneratedCodeSemanticReviewerAgent(
        provider=StaticJSONGeneratorBackend(response),
        config=GeneratedCodeSemanticReviewerConfig(
            provider_name="static",
            model="static-reviewer",
            model_tier="haiku",
            max_validation_retries=0,
        ),
    )
    blackboard = BlackboardState(project_id="cross-artifact-runtime-review")
    blackboard.artifacts.update(base_artifacts)
    blackboard.artifacts.update(dispatch["artifacts"])

    outcome = runtime_module.GeneratedCodeSemanticReviewerRuntimeSubsystem(
        reviewer=reviewer,
        max_revisions=3,
    ).run(dispatch["next_task"], blackboard)

    assert outcome.status == "REROUTE"
    assert outcome.failure_classification == (
        "generated_code_semantic_review_requires_cross_artifact_resolution"
    )
    assert outcome.next_task is not None
    assert outcome.next_task.owner_subsystem == "ArchitectCoordinator"
    unresolved_feedback = outcome.next_task.inputs["environment_feedback"]
    assert unresolved_feedback["observation_artifact_ref"]["artifact_kind"] == (
        "RuntimeArtifactRef"
    )
    resolved_feedback = resolve_runtime_artifact_references(
        unresolved_feedback,
        {**blackboard.artifacts, **outcome.produced_artifacts},
    )
    assert resolved_feedback["observation_artifact_ref"][
        "source_revision_assessment"
    ]["current_source_edit_sufficient"] is False
    execution = next(
        artifact
        for artifact in outcome.produced_artifacts.values()
        if artifact.get("artifact_kind")
        == "RuntimeGeneratedCodeSemanticReviewExecutionManifest"
    )
    assert execution["semantic_review_lineage_budget"]["selected_action"] == (
        "architect_replan"
    )


def test_generated_code_review_dispatch_uses_content_addressed_task_refs() -> None:
    question = OpenResearchQuestion(
        id="generic-code-review",
        title="Review a generated estimator",
        description="Check whether executed code implements the stated estimator.",
        tags=("coding", "semantic-review"),
    )
    context_artifact_id = "retrieval_context:generic-code-review"
    context_artifact = {
        "artifact_kind": "RuntimeRetrievalContext",
        "context_id": context_artifact_id,
        "theory_workspace": "context-payload-" + "x" * 100_000,
    }
    large_context = {"retrieval_context": context_artifact}
    deferred_task = AgentTask(
        task_id="formalize:generic-code-review",
        owner_subsystem="FormalizationEvaluator",
        objective="Formalize the accepted theory target.",
        inputs={
            "question": {
                "id": question.id,
                "title": question.title,
                "description": question.description,
                "tags": list(question.tags),
            },
            "architect_context": large_context,
        },
    )
    source_task = AgentTask(
        task_id="algorithm:generic-code-review",
        owner_subsystem="AlgorithmEngineer",
        objective="Author and execute the complete estimator source.",
        inputs={
            "question": deferred_task.inputs["question"],
            "architect_context": large_context,
            "deferred_metric_protocol_task": asdict(deferred_task),
        },
        allowed_tools=("model_backend", "python"),
    )
    manifest = {
        "artifact_kind": "RuntimeAlgorithmSandboxManifest",
        "manifest_id": "algorithm_manifest:generic-code-review",
        "prototypes": [
            {
                "estimator_id": "candidate",
                "smoke_passed": True,
                "script_path": "/tmp/candidate.py",
                "script_hash": "source-hash",
                "result_path": "/tmp/candidate.json",
                "result_hash": "result-hash",
            }
        ],
    }
    theory_packet = {
        "artifact_kind": "TheoryDerivationPacket",
        "packet_id": "theory:generic-code-review",
    }
    proposal_packet = {
        "artifact_kind": "AlgorithmEngineerProposalPacket",
        "packet_id": "proposal:generic-code-review",
    }

    dispatch = _runtime_generated_code_semantic_review_dispatch(
        task=source_task,
        question=question,
        source_subsystem="AlgorithmEngineer",
        source_manifest=manifest,
        theory_packet=theory_packet,
        proposal_packet=proposal_packet,
        architect_context={},
        deferred_next_task=deferred_task,
        blackboard_artifacts={context_artifact_id: context_artifact},
        max_revisions=1,
    )

    assert dispatch is not None
    review_task = dispatch["next_task"]
    assert set(review_task.inputs) == {
        "question",
        "work_order_id",
        "work_order_hash",
    }
    assert "source_task" not in review_task.inputs
    assert "deferred_next_task" not in review_task.inputs
    work_order = dispatch["work_order"]
    assert work_order["source_task_ref"]["artifact_kind"] == "AgentTaskRef"
    assert work_order["deferred_next_task_ref"]["artifact_kind"] == "AgentTaskRef"
    continuations = [
        artifact
        for artifact in dispatch["artifacts"].values()
        if artifact.get("artifact_kind") == "RuntimeAgentTaskContinuation"
    ]
    assert len(continuations) == 2
    assert {row["task_ref"]["task_id"] for row in continuations} == {
        source_task.task_id,
        deferred_task.task_id,
    }
    all_artifacts = {
        context_artifact_id: context_artifact,
        **dispatch["artifacts"],
    }
    restored = {
        row["task_ref"]["task_id"]: replace(
            restored_task,
            inputs=resolve_runtime_artifact_references(
                restored_task.inputs,
                all_artifacts,
            ),
        )
        for row in continuations
        for restored_task in (
            restore_agent_task_continuation(row, all_artifacts),
        )
    }
    assert restored[source_task.task_id] == source_task
    assert restored[deferred_task.task_id] == deferred_task
    serialized = json.dumps(dispatch["artifacts"], sort_keys=True)
    assert context_artifact["theory_workspace"] not in serialized
    assert len(serialized) < 50_000
    assert "RuntimeAgentTaskSnapshot" not in serialized
    protected = runtime_module._runtime_task_hash_bound_artifact_ids(
        dispatch["next_task"],
        all_artifacts,
    )
    assert protected == frozenset(all_artifacts)


def test_metric_prior_rejection_context_does_not_copy_source_history() -> None:
    preflight_packet = {
        "artifact_kind": "ArchitectTheoryExecutionPreflightPacket",
        "packet_id": "preflight:q1",
        "source": "x" * 100_000,
    }
    final_review = {
        "review_stage": "theory_execution_preflight",
        "source_theory_packet_id": "theory:q1",
        "source_theory_packet_hash": "theory-hash",
        "theory_execution_preflight_packet": preflight_packet,
        "cumulative_finding_ledger": [
            {
                "finding_id": "finding:q1",
                "status": "ACTIVE",
                "summary": "one unresolved theory finding",
            }
        ],
        "findings": [
            {
                "finding_id": "finding:q1",
                "summary": "one unresolved theory finding",
            }
        ],
    }
    rejection_id = "metric_protocol_rejection:q1"
    rejection = {
        "artifact_kind": "RuntimeArchitectMetricProtocolPreExecutionRejection",
        "feedback_reusable_for_fresh_preexecution_authoring": True,
        "execution_authorized": False,
        "semantic_review_history": [final_review],
    }
    material = {
        "source_theory_packet_id": "theory:q1",
        "source_theory_packet_hash": "theory-hash",
    }

    context = runtime_module._architect_metric_protocol_prior_rejection_context(
        architect_context={
            "architect_metric_protocol_gate": {
                "rejection_manifest_ids": [rejection_id]
            }
        },
        blackboard=BlackboardState(
            project_id="prior-rejection-context-test",
            artifacts={rejection_id: rejection},
        ),
        current_theory_material=material,
    )

    assert context["source_rejection_manifest_id"] == rejection_id
    assert context["source_rejection_manifest_hash"] == runtime_module.stable_hash(
        rejection
    )
    assert context["semantic_review_history_count"] == 1
    assert "semantic_review_history" not in context
    projected_review = context["final_review"]
    assert "theory_execution_preflight_packet" not in projected_review
    assert projected_review["theory_execution_preflight_packet_id"] == (
        "preflight:q1"
    )
    assert projected_review["theory_execution_preflight_packet_hash"] == (
        runtime_module.stable_hash(preflight_packet)
    )
    assert context["cumulative_finding_ledger"] == (
        final_review["cumulative_finding_ledger"]
    )
    assert len(json.dumps(context, sort_keys=True)) < 5_000


def test_runtime_artifact_ref_is_protected_by_resume_closure() -> None:
    artifact_id = "workspace:q1"
    artifact = {
        "artifact_kind": "RuntimeModelOwnedWorkspace",
        "artifact_id": artifact_id,
        "source": "current model-authored source",
    }
    task = AgentTask(
        task_id="continue:q1",
        owner_subsystem="FormalizationEvaluator",
        objective="continue the same workspace",
        inputs={
            "workspace": runtime_artifact_reference(artifact_id, artifact)
        },
    )

    protected = runtime_module._runtime_task_hash_bound_artifact_ids(
        task,
        {artifact_id: artifact},
    )

    assert protected == frozenset({artifact_id})
