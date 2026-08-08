from __future__ import annotations

import json

from ai_statistician.agent_runtime import AgentTask, BlackboardState
from ai_statistician.architect_coordinator_llm import (
    ARCHITECT_FEEDBACK_ROUTE_JSON_SCHEMA,
    ARCHITECT_FEEDBACK_ROUTE_OPERATION,
    ARCHITECT_FEEDBACK_ROUTE_SUBSYSTEMS,
    ArchitectCoordinatorConfig,
    LLMArchitectCoordinatorAgent,
    build_architect_coordinator_prompt,
    build_architect_feedback_route_prompt,
    validate_architect_feedback_route_packet,
)
from ai_statistician.fingerprint import stable_hash
from ai_statistician.model_backend import GeneratorResponse
from ai_statistician.research_agent_runtime import (
    ArchitectCoordinatorRuntimeSubsystem,
    ResearchAgentRuntimeConfig,
)
from ai_statistician.research_schema import OpenResearchQuestion


EXACT_HAIKU_MODEL = "claude-haiku-4-5-20251001"


def _question() -> OpenResearchQuestion:
    return OpenResearchQuestion(
        id="generic-statistical-task",
        title="Generic statistical task",
        description="Develop and evaluate a new estimator without task-specific rules.",
        tags=("held-out-family",),
    )


def test_bridge_only_gap_planner_is_not_a_generic_feedback_owner() -> None:
    assert "FormalizationGapPlanner" not in ARCHITECT_FEEDBACK_ROUTE_SUBSYSTEMS
    assert "FormalizationGapPlanner" not in (
        ARCHITECT_FEEDBACK_ROUTE_JSON_SCHEMA["properties"]["selected_subsystem"][
            "enum"
        ]
    )
    route_prompt = build_architect_feedback_route_prompt(
        question=_question(),
        architect_context={},
        environment_feedback={"feedback_type": "current_observation"},
    )
    route_payload = json.loads(route_prompt.rsplit("\n\n", 1)[1])
    assert "FormalizationGapPlanner" not in route_payload[
        "available_route_subsystems"
    ]
    assert "Route missing mathematical assumptions" in route_prompt
    assert "Lean must not substitute" in route_prompt
    invalid_route = {
        "decision": "ROUTE",
        "selected_subsystem": "FormalizationGapPlanner",
        "objective": "Plan around a gap without a bridge.",
        "rationale": "A bridge does not exist.",
        "operation": ARCHITECT_FEEDBACK_ROUTE_OPERATION,
        "environment_feedback_fingerprint": "feedback-hash",
    }
    assert "ROUTE requires one available selected_subsystem" in (
        validate_architect_feedback_route_packet(invalid_route)
    )


def test_formal_requirement_does_not_force_bridge_only_gap_planner() -> None:
    prompt = build_architect_coordinator_prompt(
        question=_question(),
        architect_context={},
        runtime_config={
            "formal_verification_policy": "required",
            "formal_required_for_final": True,
        },
    )
    payload = json.loads(prompt.rsplit("\n\n", 1)[1])
    required = payload["execution_plan_contract"]["required_subsystems"]
    assert "FormalizationEvaluator" in required
    assert "ProofEngineer" in required
    assert "FormalizationGapPlanner" not in required


class _RouteBackend:
    provider_name = "anthropic"

    def __init__(self, payload: dict[str, object]) -> None:
        self.payload = payload
        self.requests = []

    def generate(self, request):  # type: ignore[no-untyped-def]
        self.requests.append(request)
        return GeneratorResponse(
            text=json.dumps(self.payload),
            provider="anthropic",
            model=EXACT_HAIKU_MODEL,
            metadata={
                "provider_structured_output_requested": bool(request.schema),
                "provider_structured_output_applied": bool(request.schema),
            },
        )


def test_architect_feedback_route_is_small_same_model_decision() -> None:
    backend = _RouteBackend(
        {
            "decision": "ROUTE",
            "selected_subsystem": "AlgorithmEngineer",
            "objective": "Regenerate the complete executable candidate from diagnostics.",
            "rationale": "The observations concern the executed candidate semantics.",
        }
    )
    agent = LLMArchitectCoordinatorAgent(
        provider=backend,
        config=ArchitectCoordinatorConfig(
            provider_name="anthropic",
            model=EXACT_HAIKU_MODEL,
            model_tier="haiku",
            max_tokens=5000,
        ),
    )
    feedback = {
        "feedback_type": "generated_code_execution_feedback",
        "observation_status": "CURRENT_ACTIVE_OBSERVATION",
        "parent_source": "x" * 100_000,
        "runtime_errors": ["NameError: estimate is not defined"],
        "superseded_observations": [
            {
                "observation_status": (
                    "SUPERSEDED_BY_SUBSEQUENT_CANDIDATE_REVIEW"
                ),
                "observation": {
                    "runtime_errors": ["SyntaxError: historical only"]
                },
            }
        ],
        "findings": [
            {
                "finding_id": "finding:route-owner",
                "summary": "The stochastic diagnostic may not identify a code defect.",
            }
        ],
    }

    packet = agent.route_environment_feedback(
        question=_question(),
        architect_context={
            "architect_runtime_plan": {
                "problem_analysis": {"key_obstacles": ["implementation"]},
                "subsystem_execution_plan": [
                    {
                        "subsystem": "AlgorithmEngineer",
                        "objective": "produce executable code",
                        "acceptance_gate": "sandbox execution is recorded",
                    }
                ],
            },
            "runtime_progress_snapshot": {
                "available_artifact_ids": [
                    "retrieval_memory_manifest:existing",
                    "theory_derivation:current",
                ],
                "recent_task_ids": ["retrieve:done", "theory:done"],
                "recent_handoffs": [],
                "active_blockers": [],
            },
            "runtime_coding_agent_revision_budget_replan": {
                "historical_context": "y" * 100_000,
            },
        },
        environment_feedback=feedback,
    )

    assert packet["selected_subsystem"] == "AlgorithmEngineer"
    assert packet["model"] == EXACT_HAIKU_MODEL
    assert validate_architect_feedback_route_packet(packet) == []
    assert len(backend.requests) == 1
    request = backend.requests[0]
    assert request.metadata["operation"] == ARCHITECT_FEEDBACK_ROUTE_OPERATION
    assert request.schema == ARCHITECT_FEEDBACK_ROUTE_JSON_SCHEMA
    assert request.max_tokens == 2000
    assert len(request.user_prompt) < 100_000
    assert "regenerate the full research plan" in request.user_prompt
    assert "runtime_progress_snapshot" in request.user_prompt
    assert "retrieval_memory_manifest:existing" in request.user_prompt
    assert "prior intent" in request.user_prompt
    assert "NameError: estimate is not defined" in request.user_prompt
    assert "The stochastic diagnostic may not identify a code defect" in (
        request.user_prompt
    )
    assert "Never propose a new repair, patch, correction, or adapter agent" in (
        request.user_prompt
    )
    assert "automatic same-producer retry budget" in request.user_prompt
    assert "statistically non-diagnostic result does not" in (
        request.user_prompt
    )
    assert "Superseded observations are complete attempt history" in (
        request.user_prompt
    )
    assert "historical_error_is_not_an_active_blocker_unless_reobserved" not in (
        request.user_prompt
    )
    assert "SUPERSEDED_BY_SUBSEQUENT_CANDIDATE_REVIEW" in request.user_prompt
    assert "prompt-budget-exhausted" not in request.user_prompt


def test_runtime_honors_model_owned_route_and_binds_full_feedback() -> None:
    question = _question()
    simulation_manifest_id = "simulation:generic"
    full_feedback = {
        "feedback_type": "generated_code_execution_feedback",
        "parent_source": "def run_sandbox(seed, replicates):\n    return missing_name\n",
        "runtime_errors": ["NameError: name 'missing_name' is not defined"],
        "failure_classification": "opaque_environment_observation",
    }

    class _Coordinator:
        def __init__(self) -> None:
            self.route_calls = 0
            self.plan_calls = 0

        def route_environment_feedback(self, **kwargs):  # type: ignore[no-untyped-def]
            self.route_calls += 1
            assert kwargs["environment_feedback"] == full_feedback
            progress = kwargs["architect_context"]["runtime_progress_snapshot"]
            assert simulation_manifest_id in progress["available_artifact_ids"]
            assert progress["boundary"].startswith(
                "This is an authoritative inventory"
            )
            return {
                "schema_version": 1,
                "artifact_kind": "ArchitectFeedbackRouteDecision",
                "route_decision_id": "architect_feedback_route:test",
                "question_id": question.id,
                "decision": "ROUTE",
                "selected_subsystem": "AlgorithmEngineer",
                "objective": "Regenerate one complete candidate from the exact observations.",
                "rationale": "The model selected the coding agent for this evidence.",
                "operation": ARCHITECT_FEEDBACK_ROUTE_OPERATION,
                "environment_feedback_fingerprint": stable_hash(full_feedback),
                "proof_evidence_status": "NOT_PROOF_EVIDENCE",
            }

        def propose(self, **_kwargs):  # type: ignore[no-untyped-def]
            self.plan_calls += 1
            raise AssertionError("a local feedback route must not regenerate a full plan")

    coordinator = _Coordinator()
    context = {
        "simulation_manifest_id": simulation_manifest_id,
        "architect_runtime_plan": {
            "evidence_contract": {},
            "subsystem_execution_plan": [
                {
                    "subsystem": "AlgorithmEngineer",
                    "objective": "produce executable code",
                    "expected_artifacts": ["algorithm_sandbox_manifest"],
                    "acceptance_gate": "sandbox execution is recorded",
                }
            ],
        },
    }
    result = ArchitectCoordinatorRuntimeSubsystem(
        coordinator=coordinator,  # type: ignore[arg-type]
        runtime_config=ResearchAgentRuntimeConfig(),
    ).run(
        AgentTask(
            task_id="architect-feedback-route:generic",
            owner_subsystem="ArchitectCoordinator",
            objective="Choose the next evidence-producing owner.",
            inputs={
                "question": {
                    "id": question.id,
                    "title": question.title,
                    "description": question.description,
                    "tags": list(question.tags),
                },
                "architect_context": context,
                "environment_feedback": full_feedback,
                "runtime_architect_operation": ARCHITECT_FEEDBACK_ROUTE_OPERATION,
            },
        ),
        BlackboardState(
            project_id="architect-feedback-route",
            artifacts={
                simulation_manifest_id: {"manifest_id": simulation_manifest_id},
            },
        ),
    )

    assert result.status == "REROUTE"
    assert coordinator.route_calls == 1
    assert coordinator.plan_calls == 0
    assert result.next_task is not None
    assert result.next_task.owner_subsystem == "AlgorithmEngineer"
    assert result.next_task.inputs["theory_packet_id"] == ""
    assert result.next_task.inputs["environment_feedback"] == full_feedback
    assert result.next_task.objective.startswith("Regenerate one complete candidate")
    observation = result.observations[0]
    assert observation.payload["model_requested_subsystem"] == "AlgorithmEngineer"
    assert observation.payload["selected_subsystem"] == "AlgorithmEngineer"
    assert observation.payload["runtime_owner_override_applied"] is False
    assert observation.payload["full_research_plan_regenerated"] is False
    assert observation.payload["runtime_authored_candidate_fix"] is False


def test_architect_feedback_route_can_record_model_blocker() -> None:
    backend = _RouteBackend(
        {
            "decision": "BLOCK",
            "selected_subsystem": "NONE",
            "objective": "",
            "rationale": "The referenced parent artifact is unavailable.",
        }
    )
    packet = LLMArchitectCoordinatorAgent(
        provider=backend,
        config=ArchitectCoordinatorConfig(
            provider_name="anthropic",
            model=EXACT_HAIKU_MODEL,
            model_tier="haiku",
        ),
    ).route_environment_feedback(
        question=_question(),
        architect_context={},
        environment_feedback={"feedback_type": "missing_parent_artifact"},
    )

    assert packet["decision"] == "BLOCK"
    assert packet["selected_subsystem"] == "NONE"
    assert validate_architect_feedback_route_packet(packet) == []


def test_runtime_routes_formal_feedback_to_critic_without_restarting_theory() -> None:
    question = _question()
    full_feedback = {
        "feedback_type": "formalizer_proof_state_feedback",
        "failure_classification": (
            "formalizer_proof_state_revision_budget_architect_replan"
        ),
        "proof_state_feedback_rows": [
            {
                "subclaim_id": "generic:target",
                "diagnostics": ["exact compiler observation"],
            }
        ],
    }
    artifact_ids = {
        "theory_packet_id": "theory:generic",
        "simulation_manifest_id": "simulation:generic",
        "algorithm_sandbox_manifest_id": "algorithm:generic",
        "formalization_manifest_id": "formalization:generic",
    }

    class _Coordinator:
        def route_environment_feedback(self, **kwargs):  # type: ignore[no-untyped-def]
            assert kwargs["environment_feedback"] == full_feedback
            return {
                "schema_version": 1,
                "artifact_kind": "ArchitectFeedbackRouteDecision",
                "route_decision_id": "architect_feedback_route:critic",
                "question_id": question.id,
                "decision": "ROUTE",
                "selected_subsystem": "CriticEvaluator",
                "objective": "Independently audit the unresolved formal evidence.",
                "rationale": "The model selected independent evidence review.",
                "operation": ARCHITECT_FEEDBACK_ROUTE_OPERATION,
                "environment_feedback_fingerprint": stable_hash(full_feedback),
                "proof_evidence_status": "NOT_PROOF_EVIDENCE",
            }

        def propose(self, **_kwargs):  # type: ignore[no-untyped-def]
            raise AssertionError("feedback routing must not regenerate a full plan")

    result = ArchitectCoordinatorRuntimeSubsystem(
        coordinator=_Coordinator(),  # type: ignore[arg-type]
        runtime_config=ResearchAgentRuntimeConfig(),
    ).run(
        AgentTask(
            task_id="architect-formal-feedback:generic",
            owner_subsystem="ArchitectCoordinator",
            objective="Choose the next typed owner.",
            inputs={
                "question": {
                    "id": question.id,
                    "title": question.title,
                    "description": question.description,
                    "tags": list(question.tags),
                },
                "architect_context": {
                    "architect_runtime_plan": {
                        "subsystem_execution_plan": [
                            {
                                "subsystem": "CriticEvaluator",
                                "objective": "audit evidence boundaries",
                                "acceptance_gate": (
                                    "critic observations preserve evidence boundaries"
                                ),
                            }
                        ]
                    }
                },
                "environment_feedback": full_feedback,
                "runtime_architect_operation": ARCHITECT_FEEDBACK_ROUTE_OPERATION,
                **artifact_ids,
            },
        ),
        BlackboardState(
            project_id="architect-formal-feedback",
            artifacts={
                value: {"artifact_id": value}
                for value in artifact_ids.values()
            },
        ),
    )

    assert result.status == "REROUTE"
    assert result.next_task is not None
    assert result.next_task.owner_subsystem == "CriticEvaluator"
    assert result.next_task.inputs["environment_feedback"] == full_feedback
    for key, value in artifact_ids.items():
        assert result.next_task.inputs[key] == value
    assert result.observations[0].payload["full_research_plan_regenerated"] is False
