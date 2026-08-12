from __future__ import annotations

import inspect
import json
from dataclasses import asdict, fields, replace
from pathlib import Path

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
from ai_statistician.architect_coordinator_llm import (
    _architect_feedback_route_subsystems,
)
from ai_statistician.generated_code_semantic_reviewer_llm import (
    GENERATED_CODE_SEMANTIC_REVIEW_DIMENSIONS,
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
from ai_statistician.research_schema import OpenResearchQuestion
from ai_statistician.scientific_code_workspace import ScientificCodeWorkspaceResult
from ai_statistician.simulation_engineer_llm import (
    SIMULATION_ENGINEER_CODE_WORKSPACE_SYSTEM_PROMPT,
    build_simulation_engineer_prompt,
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
        "dependency_artifact_ids": ["failed-estimator"],
        "dependency_artifact_hashes": {
            "failed-estimator": failed_parent["script_hash"]
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
            ]
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

        @classmethod
        def propose(cls, **_kwargs):
            cls.propose_calls += 1
            raise AssertionError("consumer revision must bypass planning")

        @classmethod
        def iterate_code_with_tools(cls, **kwargs):
            cls.source_calls.append(str(kwargs["artifact_id"]))
            cls.initial_observations.append(
                dict(kwargs["initial_observation"])
            )
            candidate = {
                **dict(kwargs["code_draft"]),
                "code": source_for("failed-estimator", revised=True),
            }
            check = dict(kwargs["check_candidate"](candidate))
            return ScientificCodeWorkspaceResult(
                code_draft=candidate,
                check_result=check,
                evidence={
                    "workspace_operation": "targeted_revision",
                    "model_owned_source": True,
                    "runtime_edited_source": False,
                    "accepted": True,
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

    monkeypatch.setattr(
        runtime_module,
        "_run_generated_code_sandbox",
        run_generated_code_sandbox,
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
            "source_revision_artifact_ids": ["failed-estimator"],
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
        "generic-targeted-consumer:failed-estimator"
    ]
    assert SourceAgent.initial_observations[0]["consumer_observations"][0][
        "observation"
    ]["stderr_summary"] == "KeyError: value"
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
    assert manifest["n_executed"] == 1
    rows = {row["estimator_id"]: row for row in manifest["prototypes"]}
    assert rows["stable-estimator"]["prototype_status"] == (
        "REUSED_REVIEWED_SOURCE"
    )
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
    context["empirical_evaluation_phase"] = "exploratory"
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
    context["cross_family_evaluation_protocol"] = {
        "protocol_fingerprint": "protocol:generic-confirmatory-blinding",
        "candidate_gate_independence_required": True,
        "post_outcome_fresh_cohort_required": True,
        "confirmatory_candidate_seed_blinding_required": True,
    }
    source_checks: list[dict[str, object]] = []
    proposal_calls: list[dict[str, object]] = []

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
        source = str(kwargs["code_draft"]["code"])
        metrics = {"generic_metric": 0.2}
        source_path = tmp_path / "confirmatory.py"
        result_path = tmp_path / "confirmatory.json"
        source_path.write_text(source, encoding="utf-8")
        result_path.write_text(json.dumps(metrics), encoding="utf-8")
        return (
            {
                "simulation_id": str(kwargs["simulation_id"]),
                "prototype_status": "FAILED_METRIC_GATE",
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
                "smoke_passed": False,
                "execution_smoke_passed": True,
                "execution_attempted": True,
                "returncode": 0,
                "stdout_summary": "generic_metric=0.2",
                "metric_gate_errors": ["observed 0.2 is below frozen 0.9"],
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
                    "n_passed": 0,
                    "n_failed": 1,
                    "evaluations": [
                        {
                            "contract_id": "frozen-gate",
                            "passed": False,
                            "resolved_values_preview": [0.2],
                            "aggregate_value": 0.2,
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
    )
    blackboard = BlackboardState(
        project_id=question.id,
        artifacts={theory_packet_id: theory_packet},
    )

    result = subsystem.run(task, blackboard)

    assert SimulationAgent.propose_calls == 1
    assert proposal_calls[0]["withhold_seed_from_model"] is True
    assert SimulationAgent.source_calls == 1
    assert source_checks[0]["accepted"] is True
    source_observation = source_checks[0]["prototype"]
    assert source_observation["empirical_outcomes_withheld"] is True
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
    assert deferred_task.owner_subsystem == "ArchitectCoordinator"
    feedback_ref = deferred_task.inputs["environment_feedback"]
    assert feedback_ref["artifact_kind"] == "RuntimeArtifactRef"
    feedback = resolve_runtime_artifact_references(
        feedback_ref,
        all_artifacts,
    )
    assert feedback["feedback_type"] == "confirmatory_simulation_outcome"
    assert feedback["source_subsystem"] == "SimulationEvaluator"
    assert feedback["confirmatory_evaluation_cohort"] == cohort
    assert feedback["unchanged_source_retry_authorized"] is False
    assert feedback["empirical_outcomes"][0]["metric_gate_errors"]
    assert "SimulationEvaluator" not in (
        _architect_feedback_route_subsystems(
            architect_context=deferred_task.inputs["architect_context"],
            environment_feedback=feedback,
        )
    )
    cohort_ref = deferred_task.inputs["architect_context"][
        runtime_module.CONFIRMATORY_EVALUATION_COHORT_CONTEXT_KEY
    ]
    assert resolve_runtime_artifact_references(cohort_ref, all_artifacts) == cohort


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
        "source_revision_artifact_ids": ["generic-estimator"],
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
    assert observation["unchanged_source_retry_authorized"] is False
    assert next_task.inputs["architect_context"]["workspace_replan"][
        "failure_classification"
    ] == observation["failure_classification"]
    assert next_task.inputs["architect_context"]["workspace_replan"][
        "unchanged_source_retry_authorized"
    ] is False


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
        "dimension_reviews": {
            dimension: {
                "status": (
                    "FAIL" if dimension == "metric_semantics_alignment" else "PASS"
                ),
                "rationale": "The cited artifacts establish this judgment.",
                "evidence_refs": [
                    "/exact_executed_artifacts/0/exact_source_code"
                ],
            }
            for dimension in GENERATED_CODE_SEMANTIC_REVIEW_DIMENSIONS
        },
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
