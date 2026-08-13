from __future__ import annotations

import json

from ai_statistician.agent_runtime import AgentTask, BlackboardState
from ai_statistician.architect_coordinator_llm import (
    ARCHITECT_COORDINATOR_JSON_SCHEMA,
    ARCHITECT_FEEDBACK_ROUTE_JSON_SCHEMA,
    ARCHITECT_FEEDBACK_ROUTE_OPERATION,
    ARCHITECT_FEEDBACK_ROUTE_SUBSYSTEMS,
    ArchitectCoordinatorConfig,
    LLMArchitectCoordinatorAgent,
    _normalize_architect_packet,
    build_architect_coordinator_prompt,
    build_architect_feedback_route_prompt,
    validate_architect_coordinator_packet,
    validate_architect_feedback_route_packet,
)
from ai_statistician.fingerprint import stable_hash
from ai_statistician.cross_family_eval_protocol import (
    resolve_confirmatory_evaluation_cohort,
)
from ai_statistician.model_backend import GeneratorResponse
from ai_statistician.research_agent_runtime import (
    ArchitectCoordinatorRuntimeSubsystem,
    ResearchAgentRuntimeConfig,
)
from ai_statistician.research_schema import OpenResearchQuestion
from ai_statistician.scientific_code_workspace import (
    SCIENTIFIC_CONSUMER_REVISION_BUDGET_KEY,
)


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
    assert "candidate-source failures" in route_prompt
    assert "missing proof dependencies" in route_prompt
    assert "Selecting CriticEvaluator is terminal" in route_prompt
    assert "numbers or empirical outcomes mentioned inside reviewer prose" in (
        route_prompt
    )
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


def test_formal_requirement_keeps_workspace_topology_runtime_owned() -> None:
    prompt = build_architect_coordinator_prompt(
        question=_question(),
        architect_context={},
        runtime_config={
            "formal_verification_policy": "required",
            "formal_required_for_final": True,
        },
    )
    payload = json.loads(prompt.rsplit("\n\n", 1)[1])
    assert "execution_plan_contract" not in payload
    orchestration = payload["orchestration_contract"]
    assert "required workspace topology" in orchestration["runtime_owns"]
    assert "Do not enumerate a global subsystem schedule" in orchestration[
        "planning_rule"
    ]
    assert "subsystem_execution_plan" not in payload["required_output_contract"]
    path_semantics = payload["requested_evidence_contract"][
        "research_path_semantics"
    ]
    assert "not prerequisites" in path_semantics["proof_first"]
    assert "neither lane is a prerequisite" in path_semantics["dual_track"]


def test_full_architect_prompt_withholds_confirmatory_evaluator_seed() -> None:
    prompt = build_architect_coordinator_prompt(
        question=_question(),
        architect_context={
            "runtime_confirmatory_evaluation_cohort": {
                "cohort_id": "cohort:1",
                "seed": 1042,
                "cohort_index": 1,
            },
            "runtime_execution_plan": {"seed": 1042, "replicates": 12},
        },
        runtime_config={
            "formal_verification_policy": "required",
            "formal_required_for_final": True,
            "seed": 1042,
        },
    )
    payload = json.loads(prompt.rsplit("\n\n", 1)[1])
    context = payload["architect_context"]
    assert context["runtime_confirmatory_evaluation_cohort"]["seed"] == (
        "EVALUATOR_WITHHELD"
    )
    assert context["runtime_execution_plan"]["seed"] == "EVALUATOR_WITHHELD"
    assert context["runtime_execution_plan"]["replicates"] == 12
    assert payload["runtime_config"]["seed"] == "EVALUATOR_WITHHELD"


def test_compact_architect_decision_builds_runtime_workspace_topology() -> None:
    compact_decision = {
        "problem_analysis": {
            "theorem_family": "generic limit theorem",
            "statistical_objects": ["estimator"],
            "assumption_dimensions": ["sampling law"],
            "likely_analogy_classes": ["empirical process"],
            "key_obstacles": ["unknown sharp condition"],
            "missing_information": ["source theorem"],
        },
        "evidence_contract": {
            "recommended_research_path": "dual_track",
            "formal_targets": [
                "For every admissible law, the estimator converges to its estimand."
            ],
            "simulation_targets": ["Evaluate finite-sample calibration."],
        },
        "retrieval_strategy": {
            "paper_queries": ["generic estimator limit theorem"],
            "formal_source_queries": ["convergence in probability"],
            "lean_rag_priorities": ["Statlib inference"],
        },
        "iteration_policy": {
            "max_revision_rounds": 2,
            "stop_conditions": ["requested evidence is accepted"],
        },
        "next_actions": [
            {
                "owner_agent": "RetrievalMemory",
                "action": "Retrieve mathematical and formal sources.",
                "acceptance_gate": "Relevant sources and assumptions are recorded.",
            }
        ],
    }

    packet = _normalize_architect_packet(
        compact_decision,
        question=_question(),
        model=EXACT_HAIKU_MODEL,
        model_tier="haiku",
        provider_name="anthropic",
        raw_response=json.dumps(compact_decision),
        runtime_config={
            "evaluation_mode": "capability_eval",
            "formal_verification_policy": "required",
            "formal_required_for_final": True,
            "formal_target_semantic_review_required": True,
            "n_runs": 10,
        },
        architect_context={
            "runtime_requested_evidence_contract": {
                "acceptance_modes": ["independent review and runtime execution"],
                "disclosure_requirements": ["report unresolved formal gaps"],
            }
        },
    )

    planned = [row["subsystem"] for row in packet["subsystem_execution_plan"]]
    assert planned == [
        "RetrievalMemory",
        "TheoryDeveloper",
        "AlgorithmEngineer",
        "SimulationEvaluator",
        "GeneratedCodeSemanticReviewer",
        "FormalizationEvaluator",
        "FormalTargetSemanticReviewer",
        "CriticEvaluator",
    ]
    assert packet["subsystem_execution_plan_provenance"][
        "runtime_owns_required_workspace_topology"
    ] is True
    assert packet["subsystem_execution_plan_provenance"][
        "llm_authored_subsystems"
    ] == []
    assert validate_architect_coordinator_packet(packet) == []


def test_architect_provider_schema_is_compact_and_has_one_action() -> None:
    encoded = json.dumps(ARCHITECT_COORDINATOR_JSON_SCHEMA, separators=(",", ":"))
    assert len(encoded) < 3000
    assert "subsystem_execution_plan" not in ARCHITECT_COORDINATOR_JSON_SCHEMA[
        "properties"
    ]
    assert ARCHITECT_COORDINATOR_JSON_SCHEMA["properties"]["next_actions"][
        "maxItems"
    ] == 1


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


class _RouteSequenceBackend(_RouteBackend):
    def __init__(self, payloads: list[dict[str, object]]) -> None:
        super().__init__({})
        self.payloads = list(payloads)

    def generate(self, request):  # type: ignore[no-untyped-def]
        self.requests.append(request)
        payload = self.payloads.pop(0)
        return GeneratorResponse(
            text=json.dumps(payload),
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
            "workspace_replan": {
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
    assert "remaining_primary_subsystems" in request.user_prompt
    assert "the run is not ready for final audit" in request.user_prompt
    assert "retrieval_memory_manifest:existing" in request.user_prompt
    assert "prior intent" in request.user_prompt
    assert "NameError: estimate is not defined" in request.user_prompt
    assert "The stochastic diagnostic may not identify a code defect" in (
        request.user_prompt
    )
    assert "Never propose a new repair, patch, correction, or adapter agent" in (
        request.user_prompt
    )
    assert "unavailable_route_subsystems" in request.user_prompt
    assert "statistically non-diagnostic result does not" in (
        request.user_prompt
    )
    assert "never ask a worker to edit the currently frozen gate" in (
        request.user_prompt
    )
    assert "Simulation and algorithm artifacts are not prerequisites" in (
        request.user_prompt
    )
    assert "exactly one next task" in request.user_prompt
    assert "no other lane runs in the background" in request.user_prompt
    assert "Superseded observations are complete attempt history" in (
        request.user_prompt
    )
    assert "historical_error_is_not_an_active_blocker_unless_reobserved" not in (
        request.user_prompt
    )
    assert "SUPERSEDED_BY_SUBSEQUENT_CANDIDATE_REVIEW" in request.user_prompt
    assert "prompt-budget-exhausted" not in request.user_prompt
    assert "historical_context" not in request.user_prompt


def test_architect_route_transport_preserves_late_raw_execution_errors() -> None:
    prototype = {
        f"execution_metadata_{index}": f"value-{index}"
        for index in range(55)
    }
    prototype.update(
        {
            "runtime_errors": [
                "OpaqueRuntimeError: exact late diagnostic from the executor"
            ],
            "parent_source": "def run_sandbox(seed, replicates):\n    return {}\n",
        }
    )
    prompt = build_architect_feedback_route_prompt(
        question=_question(),
        architect_context={},
        environment_feedback={
            "feedback_type": "generated_code_execution_feedback",
            "observation_status": "CURRENT_ACTIVE_OBSERVATION",
            "generated_simulation_prototypes": [prototype],
        },
    )
    payload = json.loads(prompt.rsplit("\n\n", 1)[1])
    transported = payload["environment_observations"][
        "generated_simulation_prototypes"
    ][0]

    assert transported["runtime_errors"] == prototype["runtime_errors"]
    assert transported["parent_source"] == prototype["parent_source"]
    assert "_omitted_mapping_items" not in transported


def test_exhausted_candidate_lineage_cannot_immediately_route_to_same_producer() -> None:
    feedback = {
        "feedback_id": "feedback:unchanged-candidate",
        "feedback_type": "generated_simulation_sandbox_execution_feedback",
        "failure_classification": "generated_simulation_sandbox_metric_gate_failed",
        "parent_source": "def run_sandbox(seed, replicates):\n    return {}\n",
        "runtime_errors": ["metric_path /estimate resolved no values"],
    }
    context = {
        "candidate_lineage_budget": {
            "artifact_kind": "RuntimeCandidateLineageBudget",
            "feedback_id": feedback["feedback_id"],
            "failure_classification": feedback["failure_classification"],
            "source_subsystem": "SimulationEvaluator",
            "attempts_used": 2,
            "max_attempts": 2,
            "budget_exhausted": True,
        }
    }
    prompt = build_architect_feedback_route_prompt(
        question=_question(),
        architect_context=context,
        environment_feedback=feedback,
    )
    prompt_payload = json.loads(prompt.rsplit("\n\n", 1)[1])
    assert "SimulationEvaluator" not in prompt_payload[
        "available_route_subsystems"
    ]
    assert prompt_payload["unavailable_route_subsystems"] == [
        "SimulationEvaluator"
    ]
    assert prompt_payload["active_runtime_context"]["candidate_lineage_budget"][
        "budget_exhausted"
    ] is True

    critic_wrapped_feedback = {
        "feedback_id": "critic-wrapper:new-envelope",
        "active_observation_id": feedback["feedback_id"],
        "feedback_type": "critic_architect_replan_observations",
        "failure_classification": feedback["failure_classification"],
        "current_environment_observation": feedback,
    }
    wrapped_prompt = build_architect_feedback_route_prompt(
        question=_question(),
        architect_context=context,
        environment_feedback=critic_wrapped_feedback,
    )
    wrapped_payload = json.loads(wrapped_prompt.rsplit("\n\n", 1)[1])
    assert "SimulationEvaluator" not in wrapped_payload[
        "available_route_subsystems"
    ]
    assert wrapped_payload["unavailable_route_subsystems"] == [
        "SimulationEvaluator"
    ]

    backend = _RouteSequenceBackend(
        [
            {
                "decision": "ROUTE",
                "selected_subsystem": "SimulationEvaluator",
                "objective": "Try the unchanged candidate lineage again.",
                "rationale": "The prior implementation failed.",
            },
            {
                "decision": "ROUTE",
                "selected_subsystem": "TheoryDeveloper",
                "objective": "Reassess the assumptions using the empirical observations.",
                "rationale": "A new upstream artifact is needed before more code generation.",
            },
        ]
    )
    packet = LLMArchitectCoordinatorAgent(
        provider=backend,
        config=ArchitectCoordinatorConfig(
            provider_name="anthropic",
            model=EXACT_HAIKU_MODEL,
            model_tier="haiku",
            max_validation_retries=1,
        ),
    ).route_environment_feedback(
        question=_question(),
        architect_context=context,
        environment_feedback=feedback,
    )

    assert packet["selected_subsystem"] == "TheoryDeveloper"
    assert len(backend.requests) == 2
    assert "SimulationEvaluator" not in backend.requests[0].metadata[
        "available_route_subsystems"
    ]


def test_exhausted_consumer_budget_removes_only_bound_source_owner() -> None:
    feedback = {
        "feedback_type": "confirmatory_simulation_outcome",
        "failure_classification": "confirmatory_simulation_metric_gate_failed",
        "consumer_source_owner": {
            "source_owner_subsystem": "AlgorithmEngineer",
        },
        SCIENTIFIC_CONSUMER_REVISION_BUDGET_KEY: {
            "lineage_id": "scientific_consumer_lineage:exact",
            "revisions_used": 2,
            "max_revisions": 2,
            "budget_exhausted": False,
        },
    }

    prompt = build_architect_feedback_route_prompt(
        question=_question(),
        architect_context={},
        environment_feedback=feedback,
    )
    payload = json.loads(prompt.rsplit("\n\n", 1)[1])

    assert "AlgorithmEngineer" not in payload["available_route_subsystems"]
    assert "AlgorithmEngineer" in payload["unavailable_route_subsystems"]
    assert "TheoryDeveloper" in payload["available_route_subsystems"]
    assert "SimulationEvaluator" in payload["available_route_subsystems"]


def test_missing_consumer_budget_keeps_first_source_revision_available() -> None:
    feedback = {
        "feedback_type": "confirmatory_simulation_outcome",
        "failure_classification": "confirmatory_simulation_metric_gate_failed",
        "consumer_source_owner": {
            "source_owner_subsystem": "AlgorithmEngineer",
        },
    }

    prompt = build_architect_feedback_route_prompt(
        question=_question(),
        architect_context={},
        environment_feedback=feedback,
    )
    payload = json.loads(prompt.rsplit("\n\n", 1)[1])

    assert "AlgorithmEngineer" in payload["available_route_subsystems"]


def test_cross_artifact_review_keeps_true_source_owner_available_to_architect() -> None:
    feedback = {
        "feedback_id": "feedback:cross-artifact",
        "feedback_type": "workspace_replan_observation_ref",
        "source_subsystem": "AlgorithmEngineer",
        "source_artifact_id": "algorithm:rejected",
        "failure_classification": (
            "generated_code_semantic_review_requires_cross_artifact_resolution"
        ),
    }
    prompt = build_architect_feedback_route_prompt(
        question=_question(),
        architect_context={},
        environment_feedback=feedback,
    )
    payload = json.loads(prompt.rsplit("\n\n", 1)[1])

    assert payload["current_source_owner"] == "AlgorithmEngineer"
    assert "AlgorithmEngineer" in payload["available_route_subsystems"]
    assert payload["unavailable_route_subsystems"] == []

    backend = _RouteSequenceBackend(
        [
            {
                "decision": "ROUTE",
                "selected_subsystem": "AlgorithmEngineer",
                "objective": "Restart the unchanged source workspace.",
                "rationale": "Try another complete source.",
            },
        ]
    )
    packet = LLMArchitectCoordinatorAgent(
        provider=backend,
        config=ArchitectCoordinatorConfig(
            provider_name="anthropic",
            model=EXACT_HAIKU_MODEL,
            model_tier="haiku",
            max_validation_retries=1,
        ),
    ).route_environment_feedback(
        question=_question(),
        architect_context={},
        environment_feedback=feedback,
    )

    assert packet["selected_subsystem"] == "AlgorithmEngineer"
    assert len(backend.requests) == 1
    assert "Treat current_source_owner as the immutable identity" in (
        backend.requests[0].user_prompt
    )
    assert "do not rename another producer as that source owner" in (
        backend.requests[0].user_prompt
    )


def test_confirmatory_outcome_allows_only_a_new_source_on_a_fresh_cohort() -> None:
    feedback = {
        "feedback_id": "confirmatory-outcome:generic",
        "feedback_type": "confirmatory_simulation_outcome",
        "source_subsystem": "SimulationEvaluator",
        "failure_classification": "confirmatory_simulation_metric_gate_failed",
        "unchanged_source_retry_authorized": False,
    }
    prompt = build_architect_feedback_route_prompt(
        question=_question(),
        architect_context={},
        environment_feedback=feedback,
    )
    payload = json.loads(prompt.rsplit("\n\n", 1)[1])

    assert "SimulationEvaluator" in payload["available_route_subsystems"]
    assert payload["routing_contract"][
        "confirmatory_unchanged_source_retry_is_forbidden"
    ] is True
    assert payload["routing_contract"][
        "outcome_informed_new_source_requires_fresh_cohort"
    ] is True
    assert "does not itself prove" in prompt


def test_rejected_algorithm_lineage_is_not_a_simulation_handoff() -> None:
    feedback = {
        "feedback_id": "feedback:algorithm-review-exhausted",
        "feedback_type": "generated_code_semantic_review_feedback",
        "source_subsystem": "AlgorithmEngineer",
        "failure_classification": (
            "generated_code_semantic_review_lineage_budget_exhausted"
        ),
        "semantic_review_lineage_budget": {
            "source_subsystem": "AlgorithmEngineer",
            "candidate_regeneration_available": False,
            "lineage_budget_exhausted": True,
        },
    }
    context = {
        "architect_runtime_plan": {
            "evidence_contract": {
                "metric_protocol_execution_authorized": True,
                "research_evaluation_requires_generated_algorithm_code": True,
            }
        },
        "algorithm_sandbox_manifest_id": "algorithm:executed-not-accepted",
    }

    prompt = build_architect_feedback_route_prompt(
        question=_question(),
        architect_context=context,
        environment_feedback=feedback,
    )
    payload = json.loads(prompt.rsplit("\n\n", 1)[1])

    assert "AlgorithmEngineer" not in payload["available_route_subsystems"]
    assert "SimulationEvaluator" not in payload["available_route_subsystems"]
    assert payload["unavailable_route_subsystems"] == [
        "AlgorithmEngineer",
        "SimulationEvaluator",
    ]

    context["upstream_algorithm_handoff"] = {
        "handoff_id": "accepted_algorithm_handoff:generic",
        "exact_algorithm_artifacts": [
            {"estimator_id": "generic-estimator", "exact_source_hash": "abc"}
        ],
    }
    accepted_prompt = build_architect_feedback_route_prompt(
        question=_question(),
        architect_context=context,
        environment_feedback=feedback,
    )
    accepted_payload = json.loads(accepted_prompt.rsplit("\n\n", 1)[1])

    assert "AlgorithmEngineer" not in accepted_payload[
        "available_route_subsystems"
    ]
    assert "SimulationEvaluator" in accepted_payload[
        "available_route_subsystems"
    ]


def test_exploratory_simulation_does_not_require_algorithm_handoff() -> None:
    feedback = {
        "feedback_id": "feedback:algorithm-exploration-exhausted",
        "failure_classification": "algorithm_workspace_exhausted",
    }
    context = {
        "architect_runtime_plan": {
            "evidence_contract": {
                "metric_protocol_execution_authorized": False,
                "research_evaluation_requires_generated_algorithm_code": True,
            }
        },
        "candidate_lineage_budget": {
            "feedback_id": feedback["feedback_id"],
            "failure_classification": feedback["failure_classification"],
            "source_subsystem": "AlgorithmEngineer",
            "attempts_used": 1,
            "max_attempts": 1,
            "budget_exhausted": True,
        },
    }

    prompt = build_architect_feedback_route_prompt(
        question=_question(),
        architect_context=context,
        environment_feedback=feedback,
    )
    payload = json.loads(prompt.rsplit("\n\n", 1)[1])

    assert "AlgorithmEngineer" not in payload["available_route_subsystems"]
    assert "SimulationEvaluator" in payload["available_route_subsystems"]


def test_question_theory_revision_budget_does_not_reset_on_new_feedback() -> None:
    feedback = {
        "feedback_id": "feedback:new-post-simulation-observation",
        "feedback_type": "generated_simulation_sandbox_execution_feedback",
        "failure_classification": "generated_simulation_sandbox_metric_gate_failed",
        "runtime_errors": ["metric_path /estimate resolved no values"],
    }
    context = {
        "architect_metric_protocol_gate": {
            "artifact_kind": "RuntimeArchitectMetricProtocolGate",
            "upstream_theory_revision_count": 2,
            "max_upstream_theory_revisions": 2,
            "source_theory_packet_id": "theory:second-revision",
        }
    }

    prompt = build_architect_feedback_route_prompt(
        question=_question(),
        architect_context=context,
        environment_feedback=feedback,
    )
    payload = json.loads(prompt.rsplit("\n\n", 1)[1])

    assert "TheoryDeveloper" not in payload["available_route_subsystems"]
    assert "TheoryDeveloper" in payload["unavailable_route_subsystems"]
    assert payload["active_runtime_context"][
        "architect_metric_protocol_gate"
    ]["upstream_theory_revision_count"] == 2
    assert "does not reset when feedback is wrapped" in prompt

    reserved_feedback = {
        **feedback,
        "artifact_kind": "RuntimeMetricProtocolPreExecutionReviewObservation",
        "upstream_theory_revision_count": 2,
        "max_upstream_theory_revisions": 2,
    }
    reserved_prompt = build_architect_feedback_route_prompt(
        question=_question(),
        architect_context=context,
        environment_feedback=reserved_feedback,
    )
    reserved_payload = json.loads(reserved_prompt.rsplit("\n\n", 1)[1])
    assert "TheoryDeveloper" in reserved_payload["available_route_subsystems"]


def test_terminal_critic_waits_for_routable_required_workspace() -> None:
    feedback = {
        "feedback_id": "feedback:confirmatory-observation",
        "feedback_type": "confirmatory_simulation_outcome",
        "failure_classification": "generated_metric_contract_failed",
    }
    context = {
        "theory_packet_id": "theory:current",
        "runtime_progress_snapshot": {
            "evidence_lane_inventory": {
                "remaining_primary_subsystems": ["FormalizationEvaluator"],
                "critic_is_terminal": True,
            }
        },
    }

    prompt = build_architect_feedback_route_prompt(
        question=_question(),
        architect_context=context,
        environment_feedback=feedback,
    )
    payload = json.loads(prompt.rsplit("\n\n", 1)[1])

    assert "FormalizationEvaluator" in payload["available_route_subsystems"]
    assert "CriticEvaluator" not in payload["available_route_subsystems"]
    assert payload["unavailable_route_subsystems"] == ["CriticEvaluator"]

    context["runtime_outer_graph_workspace_outcomes"] = [
        {
            "source_subsystem": "FormalizationEvaluator",
            "local_status": "BLOCKED",
            "failure_classification": "formalizer_workspace_exhausted",
            "parent_artifact_ids": {"theory_packet_id": "theory:current"},
        }
    ]
    exhausted_prompt = build_architect_feedback_route_prompt(
        question=_question(),
        architect_context=context,
        environment_feedback=feedback,
    )
    exhausted_payload = json.loads(exhausted_prompt.rsplit("\n\n", 1)[1])

    assert "FormalizationEvaluator" not in exhausted_payload[
        "available_route_subsystems"
    ]
    assert "CriticEvaluator" in exhausted_payload["available_route_subsystems"]


def test_runtime_honors_model_owned_route_and_binds_full_feedback() -> None:
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
            progress = kwargs["architect_context"]["runtime_progress_snapshot"]
            assert simulation_manifest_id in progress["available_artifact_ids"]
            assert progress["evidence_lane_inventory"] == {
                "planned_primary_subsystems": [
                    "AlgorithmEngineer",
                    "SimulationEvaluator",
                    "FormalizationEvaluator",
                ],
                "executed_primary_subsystems": [
                    "AlgorithmEngineer",
                    "SimulationEvaluator",
                ],
                "remaining_primary_subsystems": ["FormalizationEvaluator"],
                "recommended_research_path": "dual_track",
                "formal_verification_policy": "required",
                "formal_required_for_final": True,
                "critic_is_terminal": True,
                "runtime_selected_next_owner": False,
            }
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
        "theory_packet_id": theory_packet_id,
        "simulation_manifest_id": simulation_manifest_id,
        "architect_runtime_plan": {
            "evidence_contract": {
                "recommended_research_path": "dual_track",
                "formal_verification_policy": "required",
                "formal_required_for_final": True,
            },
            "subsystem_execution_plan": [
                {
                    "subsystem": "AlgorithmEngineer",
                    "objective": "produce executable code",
                    "expected_artifacts": ["algorithm_sandbox_manifest"],
                    "acceptance_gate": "sandbox execution is recorded",
                },
                {
                    "subsystem": "SimulationEvaluator",
                    "objective": "evaluate the accepted implementation",
                    "expected_artifacts": ["simulation_manifest"],
                    "acceptance_gate": "simulation execution is recorded",
                },
                {
                    "subsystem": "FormalizationEvaluator",
                    "objective": "formalize and prove the mathematical target",
                    "expected_artifacts": ["formalization_manifest"],
                    "acceptance_gate": "kernel verification is recorded",
                },
                {
                    "subsystem": "CriticEvaluator",
                    "objective": "audit all collected evidence",
                    "expected_artifacts": ["critic_report"],
                    "acceptance_gate": "final evidence audit is recorded",
                },
            ],
        },
        "runtime_outer_graph_workspace_outcomes": [
            {
                "source_subsystem": "AlgorithmEngineer",
                "parent_artifact_ids": {
                    "theory_packet_id": theory_packet_id,
                },
            },
            {
                "source_subsystem": "SimulationEvaluator",
                "parent_artifact_ids": {
                    "theory_packet_id": theory_packet_id,
                },
            },
        ],
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
    assert result.next_task.inputs["theory_packet_id"] == theory_packet_id
    assert result.next_task.inputs["environment_feedback"] == full_feedback
    assert result.next_task.objective.startswith("Regenerate one complete candidate")
    observation = result.observations[0]
    assert observation.payload["model_requested_subsystem"] == "AlgorithmEngineer"
    assert observation.payload["selected_subsystem"] == "AlgorithmEngineer"
    assert observation.payload["runtime_owner_override_applied"] is False
    assert observation.payload["full_research_plan_regenerated"] is False
    assert observation.payload["runtime_authored_candidate_fix"] is False


def test_outcome_route_preserves_model_owner_and_advances_only_eval_cohort() -> None:
    question = _question()
    context = {
        "cross_family_evaluation_protocol": {
            "protocol_fingerprint": "protocol:generic",
            "candidate_gate_independence_required": True,
            "post_outcome_fresh_cohort_required": True,
            "confirmatory_candidate_seed_blinding_required": True,
        },
        "architect_runtime_plan": {
            "evidence_contract": {},
            "subsystem_execution_plan": [
                {
                    "subsystem": "TheoryDeveloper",
                    "objective": "revise theory from the released outcome",
                    "acceptance_gate": "a new theory lineage is recorded",
                }
            ],
        },
    }
    cohort, errors = resolve_confirmatory_evaluation_cohort(
        context,
        question_id=question.id,
        execution_seed=17,
    )
    assert errors == []
    context["runtime_confirmatory_evaluation_cohort"] = cohort
    feedback = {
        "artifact_kind": "RuntimeConfirmatorySimulationOutcome",
        "feedback_type": "confirmatory_simulation_outcome",
        "feedback_id": "confirmatory-outcome:generic",
        "question_id": question.id,
        "confirmatory_evaluation_cohort": cohort,
        "empirical_outcomes": [{"aggregate_value": 0.2}],
    }

    class _Coordinator:
        @staticmethod
        def route_environment_feedback(**kwargs):  # type: ignore[no-untyped-def]
            assert kwargs["environment_feedback"] == feedback
            return {
                "route_decision_id": "architect_feedback_route:cohort",
                "decision": "ROUTE",
                "selected_subsystem": "TheoryDeveloper",
                "objective": "Revise the theory from this immutable outcome.",
                "rationale": "The model selected a theory revision.",
                "environment_feedback_fingerprint": stable_hash(feedback),
            }

    result = ArchitectCoordinatorRuntimeSubsystem(
        coordinator=_Coordinator(),  # type: ignore[arg-type]
        runtime_config=ResearchAgentRuntimeConfig(seed=17),
    ).run(
        AgentTask(
            task_id="architect-confirmatory-outcome:generic",
            owner_subsystem="ArchitectCoordinator",
            objective="Choose the next owner.",
            inputs={
                "question": {
                    "id": question.id,
                    "title": question.title,
                    "description": question.description,
                    "tags": list(question.tags),
                },
                "architect_context": context,
                "environment_feedback": feedback,
                "runtime_architect_operation": ARCHITECT_FEEDBACK_ROUTE_OPERATION,
            },
        ),
        BlackboardState(project_id=question.id),
    )

    assert result.status == "REROUTE"
    assert result.next_task is not None
    assert result.next_task.owner_subsystem == "TheoryDeveloper"
    next_cohort = result.next_task.inputs["architect_context"][
        "runtime_confirmatory_evaluation_cohort"
    ]
    assert next_cohort["cohort_index"] == 1
    assert next_cohort["seed"] != cohort["seed"]
    transitions = [
        artifact
        for artifact in result.produced_artifacts.values()
        if isinstance(artifact, dict)
        and artifact.get("artifact_kind")
        == "RuntimeConfirmatoryEvaluationCohortTransition"
    ]
    assert len(transitions) == 1
    assert transitions[0]["runtime_selected_research_content"] is False
    assert any(
        row.evidence_type == "confirmatory_evaluation_cohort_transition"
        for row in result.evidence_entries
    )


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


def test_exhausted_workspace_reopens_only_on_materially_new_parent() -> None:
    context = {
        "theory_packet_id": "theory:a",
        "runtime_outer_graph_workspace_outcomes": [
            {
                "source_subsystem": "FormalizationEvaluator",
                "local_status": "BLOCKED",
                "failure_classification": "formalizer_workspace_exhausted",
                "parent_artifact_ids": {"theory_packet_id": "theory:a"},
            }
        ],
    }
    blocked_prompt = build_architect_feedback_route_prompt(
        question=_question(),
        architect_context=context,
        environment_feedback={"feedback_type": "critic_architect_replan_observations"},
    )
    blocked_payload = json.loads(blocked_prompt.rsplit("\n\n", 1)[1])

    assert "FormalizationEvaluator" not in blocked_payload[
        "available_route_subsystems"
    ]
    assert "FormalizationEvaluator" in blocked_payload[
        "unavailable_route_subsystems"
    ]

    context["theory_packet_id"] = "theory:b"
    fresh_prompt = build_architect_feedback_route_prompt(
        question=_question(),
        architect_context=context,
        environment_feedback={"feedback_type": "critic_architect_replan_observations"},
    )
    fresh_payload = json.loads(fresh_prompt.rsplit("\n\n", 1)[1])

    assert "FormalizationEvaluator" in fresh_payload["available_route_subsystems"]


def test_runtime_routes_formal_feedback_to_critic_without_restarting_theory() -> None:
    question = _question()
    full_feedback = {
        "feedback_type": "formalizer_workspace_observations",
        "failure_classification": "formalizer_workspace_exhausted",
        "candidate_diagnostics": [
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
