"""Typed-role intervention conformance with opaque source, never science credit."""

from copy import deepcopy
from dataclasses import replace

import pytest

from ai_statistician.agent_runtime import AgentRuntime, AgentStepResult, AgentTask, BlackboardState, EnvironmentObservation
from ai_statistician.architect_coordinator_llm import ARCHITECT_FEEDBACK_ROUTE_OPERATION
from ai_statistician.research_agent_runtime import ResearchAgentRuntimeConfig
from benchmarks.publication.feedback_ablation import no_cross_role_revision_policy


def scripted_draw(roles, *, ablated, final_next=None):
    calls = []
    next_steps = list(zip(roles, roles[1:] + [None]))

    class Role:
        def __init__(self, name):
            self.name = name

        def run(self, task, blackboard):
            index = len(calls)
            owner, following = next_steps[index]
            assert owner == self.name
            calls.append(owner)
            next_task = AgentTask(str(index + 1), following, "Opaque next.") if following else final_next
            observation = EnvironmentObservation(observation_type="opaque_feedback", summary="No prescribed repair.",
                payload={"unrecognized_key": ["arbitrary finding", 41], "source_bytes": "UNCHANGED"}, created_at="fixture-time")
            return AgentStepResult(status="REROUTE" if next_task else "BLOCKED", rationale="Opaque outcome.",
                next_task=next_task, observations=(observation,),
                produced_artifacts={"source-" + str(index): {"artifact_kind": "OpaqueSource", "source": "UNCHANGED"}})

    # There is no required product plan here: the canonical policy preserves
    # these opaque transitions, without fabricated production acceptance receipts.
    policy = no_cross_role_revision_policy(ResearchAgentRuntimeConfig()) if ablated else None
    result = AgentRuntime(subsystems={role: Role(role) for role in set(roles)},
        blackboard=BlackboardState(project_id="opaque-study"), handoff_policy=policy).run(
        AgentTask("0", roles[0], "Opaque initial."), max_iterations=20)
    return result, calls


@pytest.mark.parametrize("author", ["TheoryDeveloper", "AlgorithmEngineer", "SimulationEvaluator", "FormalizationEvaluator"])
def test_reverse_author_reentry_is_withheld_before_invocation_and_source_is_unchanged(author):
    roles = [author, "IndependentReader", author]
    full, full_calls = scripted_draw(roles, ablated=False)
    result, calls = scripted_draw(roles, ablated=True)
    assert full_calls == roles and calls == roles[:2]
    assert result.status == "BLOCKED" and result.pending_task is None
    last = result.traces[-1]
    assert last.failure_classification == "publication_cross_role_revision_disabled" and not last.next_task_id
    assert last.observations[0] == full.traces[1].observations[0]
    assert last.observations[-1].payload["withheld_next_task_ref"]["owner_subsystem"] == author
    assert result.blackboard.artifacts == {key: value for key, value in full.blackboard.artifacts.items() if key in {"source-0", "source-1"}}
    assert result.blackboard.evidence_ledger == []


@pytest.mark.parametrize("roles", [
    ["TheoryDeveloper", "TheoryDeveloper", "AlgorithmEngineer", "SimulationEvaluator", "CriticEvaluator"],
    ["TheoryDeveloper", "RetrievalMemory", "TheoryDeveloper", "AlgorithmEngineer", "CriticEvaluator"],
    ["ArchitectCoordinator", "TheoryDeveloper", "ArchitectCoordinator", "AlgorithmEngineer", "GeneratedCodeSemanticReviewer", "SimulationEvaluator"],
])
def test_local_iteration_tool_return_and_forward_review_still_execute(roles):
    full, full_calls = scripted_draw(roles, ablated=False)
    result, calls = scripted_draw(roles, ablated=True)
    assert calls == full_calls == roles and result.status == full.status
    assert result.blackboard.artifacts == full.blackboard.artifacts
    assert [row.observations for row in result.traces] == [row.observations for row in full.traces]


def test_another_roles_revision_cannot_be_laundered_through_retrieval():
    roles = ["TheoryDeveloper", "IndependentReader", "RetrievalMemory", "TheoryDeveloper"]
    result, calls = scripted_draw(roles, ablated=True)
    assert calls == roles[:3] and result.traces[-1].failure_classification == "publication_cross_role_revision_disabled"


@pytest.mark.parametrize("owner", ["CriticEvaluator", "SimulationEvaluator", "GeneratedCodeSemanticReviewer"])
def test_architect_feedback_route_is_withheld_without_changing_the_observation(owner):
    next_task = AgentTask("feedback-route", "ArchitectCoordinator", "Route the opaque finding.",
        inputs={"runtime_architect_operation": ARCHITECT_FEEDBACK_ROUTE_OPERATION})
    result, calls = scripted_draw([owner], ablated=True, final_next=next_task)
    assert calls == [owner] and result.status == "BLOCKED"
    assert result.traces[0].observations[0].payload["unrecognized_key"] == ["arbitrary finding", 41]
    assert result.traces[0].observations[-1].payload["withheld_next_task_ref"]["task_id"] == next_task.task_id


def test_canonical_lineage_rejection_precedes_the_ablation_and_is_not_reinterpreted():
    from ai_statistician.research_agent_runtime import _runtime_transition_policy

    task = AgentTask("invalid-review", "GeneratedCodeSemanticReviewer", "Opaque invalid lineage.")
    board = BlackboardState(project_id="opaque-invalid")
    candidate = AgentStepResult(status="REVISE", rationale="Original rejected candidate.",
        next_task=AgentTask("source-return", "AlgorithmEngineer", "No valid source binding."),
        produced_artifacts={"opaque": {"source": "UNCHANGED"}})
    config = ResearchAgentRuntimeConfig()
    kwargs = dict(iteration=1, task=task, subsystem_name=task.owner_subsystem, result=candidate, blackboard=board)
    expected = _runtime_transition_policy(**kwargs, runtime_config=config)
    before = deepcopy(candidate)
    observed = no_cross_role_revision_policy(config)(**kwargs)
    expected = replace(expected, observations=tuple(replace(row, created_at="fixture-time") for row in expected.observations))
    observed = replace(observed, observations=tuple(replace(row, created_at="fixture-time") for row in observed.observations))
    assert observed == expected and candidate == before
    assert observed.status == "BLOCKED" and observed.failure_classification == "generated_code_semantic_review_source_lineage_invalid"


@pytest.mark.parametrize("owner", ["AlgorithmEngineer", "SimulationEvaluator"])
def test_a_valid_bound_reviewer_return_is_withheld_without_weakening_its_identity_gate(owner):
    from ai_statistician.agent_runtime import agent_task_reference, materialize_agent_task_continuation
    from ai_statistician.fingerprint import stable_hash
    from ai_statistician.research_agent_runtime import _runtime_transition_policy

    source = AgentTask("opaque-producer", owner, "Write an opaque source.")
    continuation_id, continuation, payloads = materialize_agent_task_continuation(source)
    work_order = {"artifact_kind": "RuntimeGeneratedCodeSemanticReviewWorkOrder", "source_subsystem": owner,
        "source_task_id": source.task_id, "source_task_ref": agent_task_reference(source),
        "source_task_continuation_id": continuation_id, "source_task_continuation_hash": stable_hash(continuation)}
    board = BlackboardState(project_id="opaque-bound-review")
    board.artifacts.update(payloads)
    board.artifacts["work-order"] = work_order
    reviewer = AgentTask("reviewer", "GeneratedCodeSemanticReviewer", "Review opaque data.",
        inputs={"work_order_id": "work-order", "work_order_hash": stable_hash(work_order)})
    next_task = replace(source, task_id="source-revision", inputs={"generated_code_semantic_review_revision_count": 1,
        "environment_feedback": {"feedback_type": "generated_code_semantic_review_feedback", "source_subsystem": owner,
            "semantic_review_execution_id": "opaque-execution", "semantic_review_packet_id": "opaque-review",
            "semantic_review_packet_hash": "opaque-hash", "unknown_content": "No prescribed source patch."}})
    result = AgentStepResult(status="REVISE", rationale="Actual hash-bound source return.", next_task=next_task,
        produced_artifacts={"source": {"bytes": "UNCHANGED"}})
    config = ResearchAgentRuntimeConfig()
    policy = no_cross_role_revision_policy(config)
    assert policy(iteration=1, task=source, subsystem_name=owner, blackboard=board,
        result=AgentStepResult(status="REROUTE", rationale="Initial forward handoff.", next_task=reviewer)).next_task == reviewer
    kwargs = dict(iteration=2, task=reviewer, subsystem_name=reviewer.owner_subsystem, result=result, blackboard=board)
    assert _runtime_transition_policy(**kwargs, runtime_config=config) == result
    observed = policy(**kwargs)
    assert observed.status == "BLOCKED" and observed.failure_classification == "publication_cross_role_revision_disabled"
    assert observed.produced_artifacts == result.produced_artifacts
    assert observed.observations[-1].payload["withheld_next_task_ref"] == agent_task_reference(next_task)


def test_policy_role_history_does_not_leak_into_another_research_graph():
    policy = no_cross_role_revision_policy(ResearchAgentRuntimeConfig())
    board = BlackboardState(project_id="opaque-first")
    source = AgentTask("first-source", "TheoryDeveloper", "Opaque first.")
    policy(iteration=1, task=source, subsystem_name=source.owner_subsystem, blackboard=board,
        result=AgentStepResult(status="BLOCKED", rationale="Unresolved first graph."))
    architect = AgentTask("second-plan", "ArchitectCoordinator", "Fresh second graph.")
    next_task = replace(source, task_id="second-source")
    candidate = AgentStepResult(status="REROUTE", rationale="Fresh forward handoff.", next_task=next_task)
    assert policy(iteration=1, task=architect, subsystem_name=architect.owner_subsystem,
        blackboard=BlackboardState(project_id="opaque-second"), result=candidate) == candidate


@pytest.mark.parametrize("deferred_owner,tampered,allowed", [
    ("SimulationEvaluator", False, True),
    ("TheoryDeveloper", False, False),
    ("SimulationEvaluator", True, False),
])
def test_exact_accepted_source_phase_resume_is_not_a_revision_but_upstream_feedback_is(deferred_owner, tampered, allowed):
    from ai_statistician.agent_runtime import agent_task_reference, materialize_agent_task_continuation
    from ai_statistician.fingerprint import stable_hash
    from ai_statistician.generated_code_semantic_review_scope import accepted_semantic_review_deferred_continuation

    deferred = AgentTask("deferred", deferred_owner, "Continue the exact opaque phase.", inputs={"opaque_binding": "UNCHANGED"})
    cid, continuation, artifacts = materialize_agent_task_continuation(deferred)
    work_order = {"artifact_kind": "RuntimeGeneratedCodeSemanticReviewWorkOrder", "source_subsystem": "SimulationEvaluator",
        "source_manifest_id": "opaque-source", "source_manifest_hash": "opaque-source-hash",
        "deferred_next_task_continuation_id": cid, "deferred_next_task_continuation_hash": stable_hash(continuation),
        "deferred_next_task_ref": agent_task_reference(deferred)}
    reviewer = AgentTask("reviewer", "GeneratedCodeSemanticReviewer", "Read the exact opaque source.",
        inputs={"work_order_id": "work-order", "work_order_hash": stable_hash(work_order)})
    board = BlackboardState(project_id="opaque-accepted-phase", artifacts={**artifacts, "work-order": work_order})
    policy = no_cross_role_revision_policy(ResearchAgentRuntimeConfig())
    for index, owner in enumerate(["TheoryDeveloper", "SimulationEvaluator"], 1):
        policy(iteration=index, task=AgentTask(str(index), owner, "Initial opaque source."), subsystem_name=owner,
            blackboard=board, result=AgentStepResult(status="REROUTE", rationale="Forward review.", next_task=reviewer))
    execution = {"artifact_kind": "RuntimeGeneratedCodeSemanticReviewExecutionManifest",
        "work_order_id": "work-order", "work_order_hash": reviewer.inputs["work_order_hash"],
        "source_subsystem": "SimulationEvaluator", "source_manifest_id": "opaque-source",
        "source_manifest_hash": "opaque-source-hash", "semantic_review_accepted": True,
        "independent_agent": True, "independent_invocation": True}
    candidate = AgentStepResult(status="REROUTE", rationale="Restore the exact deferred phase.", next_task=deferred,
        produced_artifacts={"opaque-review-execution": execution})
    if tampered:
        candidate = replace(candidate, next_task=replace(deferred, objective="Unbound phase."))
    assert accepted_semantic_review_deferred_continuation(task=reviewer, result=candidate,
        next_task=candidate.next_task, blackboard=board) is (not tampered)
    observed = policy(iteration=3, task=reviewer, subsystem_name=reviewer.owner_subsystem, blackboard=board, result=candidate)
    assert observed.produced_artifacts == candidate.produced_artifacts
    if allowed:
        assert observed == candidate
    else:
        assert observed.status == "BLOCKED" and observed.next_task is None
        assert observed.failure_classification == "publication_cross_role_revision_disabled"
