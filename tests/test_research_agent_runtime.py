from __future__ import annotations

import inspect
from dataclasses import fields

import pytest

import ai_statistician.research_agent_runtime as runtime_module
from ai_statistician.agent_runtime import (
    AgentStepResult,
    AgentTask,
    BlackboardState,
    TaskHandoffRecord,
)
from ai_statistician.algorithm_engineer_llm import (
    ALGORITHM_ENGINEER_CODE_WORKSPACE_SYSTEM_PROMPT,
)
from ai_statistician.model_backend import (
    LIVE_EVALUATION_CLAUDE_MODEL,
    LIVE_EVALUATION_CLAUDE_MODEL_TIER,
)
from ai_statistician.research_agent_runtime import (
    ResearchAgentRuntimeConfig,
    _normalized_runtime_evaluation_model_config,
    _runtime_generated_code_semantic_review_dispatch,
    _runtime_transition_policy,
    formalizer_workspace_runtime_bindings,
)
from ai_statistician.research_schema import OpenResearchQuestion
from ai_statistician.simulation_engineer_llm import (
    SIMULATION_ENGINEER_CODE_WORKSPACE_SYSTEM_PROMPT,
)
from ai_statistician.structured_output_retry import PacketValidationError


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


def test_source_workspace_prompts_give_tools_to_the_source_owner() -> None:
    for prompt in (
        ALGORITHM_ENGINEER_CODE_WORKSPACE_SYSTEM_PROMPT,
        SIMULATION_ENGINEER_CODE_WORKSPACE_SYSTEM_PROMPT,
    ):
        assert "complete executable Python or R" in prompt
        assert "Use the supplied\nclient tools" in prompt
        assert "Do not run tools" not in prompt
        assert "never supplies a correction rule" in prompt


def test_unreviewed_compiled_lean_candidate_cannot_claim_generic_kernel_proof() -> None:
    fields = runtime_module._formalizer_candidate_kernel_scope_fields(
        local_lean_compiled=True
    )

    assert fields["kernel_verified"] is False
    assert fields["candidate_kernel_verified"] is True
    assert fields["candidate_kernel_verified_scope"] == "candidate_artifact_only"


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
            failure_classification="formalizer_workspace_continuation_exhausted",
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
        }
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
        }
    ]
    task = AgentTask(
        task_id="simulation:complete",
        owner_subsystem="SimulationEvaluator",
        objective="Complete empirical evidence.",
        inputs={
            "question": runtime_module._question_to_payload(question),
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


def test_generated_code_review_dispatch_uses_content_addressed_task_refs() -> None:
    question = OpenResearchQuestion(
        id="generic-code-review",
        title="Review a generated estimator",
        description="Check whether executed code implements the stated estimator.",
        tags=("coding", "semantic-review"),
    )
    source_task = AgentTask(
        task_id="algorithm:generic-code-review",
        owner_subsystem="AlgorithmEngineer",
        objective="Author and execute the complete estimator source.",
        inputs={
            "question": {
                "id": question.id,
                "title": question.title,
                "description": question.description,
                "tags": list(question.tags),
            },
            "architect_context": {},
        },
        allowed_tools=("model_backend", "python"),
    )
    deferred_task = AgentTask(
        task_id="formalize:generic-code-review",
        owner_subsystem="FormalizationEvaluator",
        objective="Formalize the accepted theory target.",
        inputs={"question": source_task.inputs["question"]},
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
    snapshots = [
        artifact
        for artifact in dispatch["artifacts"].values()
        if artifact.get("artifact_kind") == "RuntimeAgentTaskSnapshot"
    ]
    assert len(snapshots) == 2
    assert {row["task_ref"]["task_id"] for row in snapshots} == {
        source_task.task_id,
        deferred_task.task_id,
    }
