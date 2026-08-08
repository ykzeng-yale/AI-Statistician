from __future__ import annotations

import json

from ai_statistician.agent_runtime import AgentTask, BlackboardState
from ai_statistician.architect_coordinator_llm import (
    ARCHITECT_FEEDBACK_ROUTE_JSON_SCHEMA,
    ARCHITECT_FEEDBACK_ROUTE_OPERATION,
    ArchitectCoordinatorConfig,
    LLMArchitectCoordinatorAgent,
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
        "parent_source": "x" * 100_000,
        "runtime_errors": ["NameError: estimate is not defined"],
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
            }
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
    assert len(request.user_prompt) < 35_000
    assert "regenerate the full research plan" in request.user_prompt


def test_runtime_binds_full_feedback_after_model_owned_route() -> None:
    question = _question()
    theory_packet_id = "theory:generic"
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
        "theory_packet_id": theory_packet_id,
        "simulation_manifest_id": simulation_manifest_id,
        "implementation_gaps": [
            {
                "estimator_id": "new-estimator",
                "status": "REQUIRES_ALGORITHM_ENGINEER_ADAPTER",
            }
        ],
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
                theory_packet_id: {"packet_id": theory_packet_id},
                simulation_manifest_id: {"manifest_id": simulation_manifest_id},
            },
        ),
    )

    assert result.status == "REROUTE"
    assert coordinator.route_calls == 1
    assert coordinator.plan_calls == 0
    assert result.next_task is not None
    assert result.next_task.owner_subsystem == "AlgorithmEngineer"
    assert result.next_task.inputs["environment_feedback"] == full_feedback
    assert result.next_task.objective.startswith("Regenerate one complete candidate")
    observation = result.observations[0]
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
