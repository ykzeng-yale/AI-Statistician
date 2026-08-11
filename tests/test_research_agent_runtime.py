from __future__ import annotations

import inspect
import json
from dataclasses import asdict, fields, replace

import pytest

import ai_statistician.research_agent_runtime as runtime_module
from ai_statistician.agent_runtime import (
    AgentStepResult,
    AgentTask,
    BlackboardState,
    TaskHandoffRecord,
    restore_agent_task_continuation,
    resolve_runtime_artifact_references,
    runtime_artifact_reference,
)
from ai_statistician.algorithm_engineer_llm import (
    ALGORITHM_ENGINEER_CODE_WORKSPACE_SYSTEM_PROMPT,
)
from ai_statistician.model_backend import (
    LIVE_EVALUATION_CLAUDE_MODEL,
    LIVE_EVALUATION_CLAUDE_MODEL_TIER,
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


def test_required_formal_policy_does_not_hardcode_proof_first_execution() -> None:
    contract = runtime_module._runtime_requested_evidence_contract(
        formal_verification_policy="required",
        evaluation_mode="capability_eval",
    )

    assert contract["recommended_research_path"] == "dual_track"


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
    assert not any(
        artifact.get("artifact_kind") == "RuntimeCriticFormalizationObservation"
        for artifact in result.produced_artifacts.values()
        if isinstance(artifact, dict)
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
    assert "request's data scope" in SIMULATION_ENGINEER_CODE_WORKSPACE_SYSTEM_PROMPT
    assert "consumer control flow" in SIMULATION_ENGINEER_CODE_WORKSPACE_SYSTEM_PROMPT


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


def test_formalizer_raw_feedback_revision_does_not_require_final_compile() -> None:
    observed, loops, revisions = _formalizer_revision_summary(
        [
            {
                "evidence_type": "formalizer_packet_validation_failure",
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
            failure_classification="formalizer_workspace_continuation_exhausted",
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
