from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict

import pytest

from ai_statistician.agent_runtime import (
    AgentRuntime,
    AgentStepResult,
    AgentTask,
    BlackboardState,
    EnvironmentObservation,
    EvidenceLedgerEntry,
    RUNTIME_OUTER_GRAPH_BUDGET_SCOPE,
    RUNTIME_SAME_OWNER_WORKSPACE_BUDGET_SCOPE,
    ToolCallRecord,
    agent_task_continuation_reference,
    agent_runtime_substage,
    materialize_agent_task_continuation,
    mark_same_owner_workspace_continuation,
    restore_agent_task_continuation,
    runtime_artifact_reference,
)
from ai_statistician.fingerprint import stable_hash


class TheorySubsystem:
    name = "TheoryDeveloper"

    def run(self, task: AgentTask, blackboard: BlackboardState) -> AgentStepResult:
        return AgentStepResult(
            status="REROUTE",
            rationale="theory proposal needs executable simulation feedback",
            produced_artifacts={"theory_packet:q1": {"claim": "candidate coverage theorem"}},
            observations=(
                EnvironmentObservation(
                    observation_type="theory_derivation",
                    summary="candidate theorem derived with open simulation risk",
                ),
            ),
            next_task=AgentTask(
                task_id="simulate:q1",
                owner_subsystem="SimulatorDesigner",
                objective="write and run falsification simulation",
                inputs={"theory_packet": "theory_packet:q1"},
                allowed_tools=("python",),
                expected_artifacts=("simulation_manifest",),
                acceptance_gate="reproducible simulation manifest",
            ),
        )


class SimulatorSubsystem:
    name = "SimulatorDesigner"

    def run(self, task: AgentTask, blackboard: BlackboardState) -> AgentStepResult:
        return AgentStepResult(
            status="ACCEPTED",
            rationale="simulation manifest supports rerouting to formalization",
            produced_artifacts={"simulation_manifest:q1": {"passed": True}},
            observations=(
                EnvironmentObservation(
                    observation_type="simulation_result",
                    summary="coverage diagnostic passed under declared DGP",
                ),
            ),
            tool_calls=(
                ToolCallRecord(
                    tool_name="python",
                    inputs={"script": "simulate_q1.py"},
                    exit_status="0",
                    stdout_summary="coverage=0.95",
                    safety_boundary="simulation is not proof evidence",
                ),
            ),
            evidence_entries=(
                EvidenceLedgerEntry(
                    evidence_id="evidence:simulation:q1",
                    task_id=task.task_id,
                    artifact_id="simulation_manifest:q1",
                    evidence_type="simulation",
                    status="EXECUTED_REPRODUCIBLY",
                    boundary="empirical support, not theorem proof",
                ),
            ),
        )


def test_agent_task_continuation_deduplicates_and_restores_structured_inputs() -> None:
    shared = {"workspace": "x" * 10_000}
    deferred = AgentTask(
        task_id="formalize:q1",
        owner_subsystem="FormalizationEvaluator",
        objective="continue the formalization workspace",
        inputs={"shared_under_any_name": shared},
    )
    _, deferred_continuation, deferred_artifacts = (
        materialize_agent_task_continuation(deferred)
    )
    source = AgentTask(
        task_id="algorithm:q1",
        owner_subsystem="AlgorithmEngineer",
        objective="continue the scientific coding workspace",
        inputs={
            "first_arbitrary_mapping": shared,
            "second_arbitrary_mapping": shared,
            "next_workspace": asdict(deferred),
        },
    )
    _, source_continuation, source_artifacts = materialize_agent_task_continuation(
        source,
        linked_input_references={
            stable_hash(asdict(deferred)): agent_task_continuation_reference(
                deferred_continuation
            )
        },
    )
    artifacts = {**deferred_artifacts, **source_artifacts}

    assert restore_agent_task_continuation(source_continuation, artifacts) == source
    assert restore_agent_task_continuation(
        deferred_continuation,
        artifacts,
    ) == deferred
    mapping_artifacts = [
        row
        for row in artifacts.values()
        if row.get("artifact_kind") == "RuntimeAgentTaskInputMapping"
    ]
    assert len(mapping_artifacts) == 1


def test_agent_task_continuation_restores_linked_artifact_reference() -> None:
    artifact_id = "manifest:q1"
    artifact = {
        "artifact_kind": "RuntimeExampleManifest",
        "manifest_id": artifact_id,
        "payload": {"value": 7},
    }
    task = AgentTask(
        task_id="resume:q1",
        owner_subsystem="ExampleSubsystem",
        objective="Resume from one exact artifact.",
        inputs={"source_manifest": artifact},
    )
    _, continuation, continuation_artifacts = materialize_agent_task_continuation(
        task,
        linked_input_references={
            stable_hash(artifact): runtime_artifact_reference(
                artifact_id,
                artifact,
            )
        },
    )

    restored = restore_agent_task_continuation(
        continuation,
        {artifact_id: artifact, **continuation_artifacts},
    )

    assert restored == task


def test_agent_task_continuation_rejects_tampered_input_artifact() -> None:
    task = AgentTask(
        task_id="theory:q1",
        owner_subsystem="TheoryDeveloper",
        objective="continue a theory workspace",
        inputs={"workspace": {"claim": "original"}},
    )
    _, continuation, artifacts = materialize_agent_task_continuation(task)
    tampered = deepcopy(artifacts)
    mapping_id = next(
        artifact_id
        for artifact_id, row in tampered.items()
        if row.get("artifact_kind") == "RuntimeAgentTaskInputMapping"
    )
    tampered[mapping_id]["mapping"]["claim"] = "changed"

    with pytest.raises(ValueError, match="input mapping hash mismatch"):
        restore_agent_task_continuation(continuation, tampered)


def test_agent_runtime_resolves_and_preserves_explicit_artifact_refs() -> None:
    workspace = {
        "artifact_kind": "RuntimeModelOwnedWorkspace",
        "artifact_id": "workspace:q1",
        "source": "x" * 10_000,
    }

    class Producer:
        name = "Producer"

        def run(
            self,
            task: AgentTask,
            blackboard: BlackboardState,
        ) -> AgentStepResult:
            return AgentStepResult(
                status="REROUTE",
                rationale="publish one authoritative workspace",
                produced_artifacts={"workspace:q1": workspace},
                next_task=AgentTask(
                    task_id="consume:q1",
                    owner_subsystem="Consumer",
                    objective="consume the workspace",
                    inputs={"workspace": workspace},
                ),
            )

    class Consumer:
        name = "Consumer"

        def run(
            self,
            task: AgentTask,
            blackboard: BlackboardState,
        ) -> AgentStepResult:
            assert task.inputs["workspace"] == workspace
            return AgentStepResult(
                status="REROUTE",
                rationale="forward the unchanged workspace",
                next_task=AgentTask(
                    task_id="finish:q1",
                    owner_subsystem="Finisher",
                    objective="finish from the same workspace",
                    inputs={"workspace": task.inputs["workspace"]},
                ),
            )

    class Finisher:
        name = "Finisher"

        def run(
            self,
            task: AgentTask,
            blackboard: BlackboardState,
        ) -> AgentStepResult:
            assert task.inputs["workspace"] == workspace
            return AgentStepResult(status="ACCEPTED", rationale="workspace consumed")

    result = AgentRuntime(
        subsystems={
            "Producer": Producer(),
            "Consumer": Consumer(),
            "Finisher": Finisher(),
        },
        blackboard=BlackboardState(project_id="artifact-ref-test"),
    ).run(
        AgentTask(
            task_id="produce:q1",
            owner_subsystem="Producer",
            objective="publish the workspace",
        ),
        max_iterations=3,
    )

    assert result.status == "ACCEPTED"
    for trace in result.traces[1:]:
        reference = trace.task.inputs["workspace"]
        assert reference["artifact_kind"] == "RuntimeArtifactRef"
        assert reference["artifact_id"] == "workspace:q1"
        assert "source" not in reference
    assert result.traces[1].next_task is not None
    assert result.traces[1].next_task.inputs["workspace"]["artifact_kind"] == (
        "RuntimeArtifactRef"
    )


def test_agent_runtime_rejects_stale_artifact_ref_before_subsystem_call() -> None:
    workspace = {
        "artifact_kind": "RuntimeModelOwnedWorkspace",
        "artifact_id": "workspace:q1",
        "source": "original",
    }
    reference = runtime_artifact_reference("workspace:q1", workspace)
    reference["content_hash"] = "stale"

    class NeverCalled:
        name = "Consumer"

        def __init__(self) -> None:
            self.calls = 0

        def run(
            self,
            task: AgentTask,
            blackboard: BlackboardState,
        ) -> AgentStepResult:
            self.calls += 1
            raise AssertionError("stale refs must fail before subsystem execution")

    subsystem = NeverCalled()
    result = AgentRuntime(
        subsystems={"Consumer": subsystem},
        blackboard=BlackboardState(
            project_id="stale-artifact-ref-test",
            artifacts={"workspace:q1": workspace},
        ),
    ).run(
        AgentTask(
            task_id="consume:q1",
            owner_subsystem="Consumer",
            objective="consume one workspace",
            inputs={"workspace": reference},
        )
    )

    assert result.status == "FAILED"
    assert subsystem.calls == 0
    assert result.traces[0].failure_classification == (
        "task_artifact_reference_invalid"
    )


def test_agent_runtime_leaves_non_blackboard_artifact_refs_opaque() -> None:
    identity_ref = {
        "artifact_kind": "RuntimeArtifactRef",
        "artifact_id": "external:source",
    }

    class Consumer:
        name = "Consumer"

        def run(
            self,
            task: AgentTask,
            blackboard: BlackboardState,
        ) -> AgentStepResult:
            assert task.inputs["source_artifact_ref"] == identity_ref
            return AgentStepResult(status="ACCEPTED", rationale="identity preserved")

    result = AgentRuntime(
        subsystems={"Consumer": Consumer()},
        blackboard=BlackboardState(project_id="opaque-artifact-ref-test"),
    ).run(
        AgentTask(
            task_id="consume:external-source",
            owner_subsystem="Consumer",
            objective="consume an opaque source identity",
            inputs={"source_artifact_ref": identity_ref},
        )
    )

    assert result.status == "ACCEPTED"


def test_agent_runtime_exposes_compound_substage_progress_without_new_scheduler() -> None:
    class CompoundSubsystem:
        name = "CompoundSubsystem"

        def run(
            self,
            task: AgentTask,
            blackboard: BlackboardState,
        ) -> AgentStepResult:
            with agent_runtime_substage(
                "independent_semantic_review",
                metadata={"model_tier": "sonnet", "attempt": 1},
            ) as progress_metadata:
                progress_metadata["verdict"] = "ACCEPT"
            return AgentStepResult(status="ACCEPTED", rationale="compound work complete")

    progress_rows: list[dict[str, object]] = []
    result = AgentRuntime(
        subsystems={"CompoundSubsystem": CompoundSubsystem()},
        blackboard=BlackboardState(project_id="substage-progress-test"),
    ).run(
        AgentTask(
            task_id="compound:q1",
            owner_subsystem="CompoundSubsystem",
            objective="run a visible compound stage",
        ),
        progress_callback=progress_rows.append,
    )

    assert result.status == "ACCEPTED"
    substage_rows = [
        row for row in progress_rows if row["substage"] == "independent_semantic_review"
    ]
    assert [row["event_type"] for row in substage_rows] == [
        "substage_start",
        "substage_finish",
    ]
    assert substage_rows[1]["status"] == "COMPLETED"
    assert float(substage_rows[1]["elapsed_seconds"]) >= 0.0
    assert substage_rows[1]["metadata"] == {
        "model_tier": "sonnet",
        "attempt": 1,
        "verdict": "ACCEPT",
    }


def test_agent_runtime_dispatches_subsystems_and_records_observations() -> None:
    blackboard = BlackboardState(project_id="runtime-test")
    runtime = AgentRuntime(
        subsystems={
            "TheoryDeveloper": TheorySubsystem(),
            "SimulatorDesigner": SimulatorSubsystem(),
        },
        blackboard=blackboard,
    )
    progress_rows: list[dict[str, object]] = []

    result = runtime.run(
        AgentTask(
            task_id="theory:q1",
            owner_subsystem="TheoryDeveloper",
            objective="derive candidate frontier theorem",
            expected_artifacts=("theory_packet",),
        ),
        max_iterations=3,
        progress_callback=progress_rows.append,
    )

    assert result.status == "ACCEPTED"
    assert result.final_task_id == "simulate:q1"
    assert result.blackboard.task_history == ["theory:q1", "simulate:q1"]
    assert set(result.blackboard.artifacts) == {"theory_packet:q1", "simulation_manifest:q1"}
    assert [row.status for row in result.traces] == ["REROUTE", "ACCEPTED"]
    assert result.traces[0].next_task_id == "simulate:q1"
    assert result.traces[0].handoff_id == "handoff:1:theory:q1->simulate:q1"
    assert result.traces[1].tool_calls[0].safety_boundary == "simulation is not proof evidence"
    assert result.blackboard.evidence_ledger[0].boundary == "empirical support, not theorem proof"
    assert len(result.blackboard.handoff_ledger) == 1
    handoff = result.blackboard.handoff_ledger[0]
    assert handoff.handoff_id == result.traces[0].handoff_id
    assert handoff.from_task_id == "theory:q1"
    assert handoff.to_task_id == "simulate:q1"
    assert handoff.from_subsystem == "TheoryDeveloper"
    assert handoff.to_subsystem == "SimulatorDesigner"
    assert handoff.status == "REROUTE"
    assert handoff.produced_artifact_ids == ("theory_packet:q1",)
    assert handoff.evidence_ids == ()
    assert handoff.next_task_input_keys == ("theory_packet",)
    assert handoff.next_task_allowed_tools == ("python",)
    assert handoff.next_task_expected_artifacts == ("simulation_manifest",)
    assert handoff.next_task_acceptance_gate == "reproducible simulation manifest"
    finish_rows = [
        row for row in progress_rows if row["event_type"] == "subsystem_finish"
    ]
    assert finish_rows[0]["handoff_id"] == handoff.handoff_id
    assert finish_rows[0]["next_task_id"] == "simulate:q1"
    assert finish_rows[1]["handoff_id"] == ""
    payload = result.to_json(include_task_payloads=True)
    assert payload["traces"][0]["next_task"]["task_id"] == "simulate:q1"
    assert payload["traces"][0]["next_task"]["inputs"] == {
        "theory_packet": "theory_packet:q1"
    }
    assert payload["traces"][0]["handoff_id"] == handoff.handoff_id
    assert payload["blackboard"]["handoff_ledger"][0]["to_subsystem"] == "SimulatorDesigner"
    assert payload["traces"][1]["observations"][0]["observation_type"] == "simulation_result"

    compact_payload = result.to_json()
    task_ref = compact_payload["traces"][0]["task"]
    next_task_ref = compact_payload["traces"][0]["next_task"]
    assert task_ref["artifact_kind"] == "AgentTaskRef"
    assert task_ref["task_id"] == "theory:q1"
    assert "inputs" not in task_ref
    assert next_task_ref["artifact_kind"] == "AgentTaskRef"
    assert next_task_ref["task_id"] == "simulate:q1"
    assert next_task_ref["input_keys"] == ["theory_packet"]
    assert "inputs" not in next_task_ref


def test_compact_runtime_trace_bounds_duplicate_tool_output() -> None:
    exact_stdout = "stdout-head\n" + ("x" * 100_000) + "\nstdout-tail"
    unbound_stderr = "stderr-head\n" + ("y" * 100_000) + "\nstderr-tail"

    class LargeOutputSubsystem:
        name = "LargeOutputSubsystem"

        def run(
            self,
            task: AgentTask,
            blackboard: BlackboardState,
        ) -> AgentStepResult:
            return AgentStepResult(
                status="ACCEPTED",
                rationale="large exact output is stored by the execution artifact",
                tool_calls=(
                    ToolCallRecord(
                        tool_name="python.generated_algorithm_sandbox",
                        output_paths=("sandbox/exact-result.json",),
                        output_hash="exact-result-hash",
                        exit_status="0",
                        stdout_summary=exact_stdout,
                        safety_boundary="execution evidence, not proof",
                    ),
                    ToolCallRecord(
                        tool_name="remote.provider_without_output_artifact",
                        exit_status="failed",
                        stderr_summary=unbound_stderr,
                        safety_boundary="unique raw failure observation",
                    ),
                ),
            )

    runtime = AgentRuntime(
        subsystems={"LargeOutputSubsystem": LargeOutputSubsystem()},
        blackboard=BlackboardState(project_id="large-tool-output"),
    )
    result = runtime.run(
        AgentTask(
            task_id="large-output:q1",
            owner_subsystem="LargeOutputSubsystem",
            objective="record one exact execution",
        )
    )

    full_call = result.to_json(include_task_payloads=True)["traces"][0][
        "tool_calls"
    ][0]
    compact_call = result.to_json()["traces"][0]["tool_calls"][0]
    unbound_call = result.to_json()["traces"][0]["tool_calls"][1]

    assert full_call["stdout_summary"] == exact_stdout
    assert "stdout_summary_hash" not in full_call
    assert len(compact_call["stdout_summary"]) <= 16_000
    assert compact_call["stdout_summary"].startswith("stdout-head")
    assert compact_call["stdout_summary"].endswith("stdout-tail")
    assert compact_call["stdout_summary_hash"] == stable_hash(exact_stdout)
    assert compact_call["stdout_summary_characters"] == len(exact_stdout)
    assert compact_call["stdout_summary_bytes"] == len(
        exact_stdout.encode("utf-8")
    )
    assert compact_call["stdout_summary_truncated"] is True
    assert compact_call["stderr_summary_truncated"] is False
    assert compact_call["summary_payload_policy"] == "bounded_trace_projection"
    assert compact_call["output_paths"] == ("sandbox/exact-result.json",)
    assert compact_call["output_hash"] == "exact-result-hash"
    assert unbound_call["stderr_summary"] == unbound_stderr
    assert unbound_call["stderr_summary_truncated"] is False
    assert unbound_call["summary_payload_policy"] == (
        "inline_exact_without_external_output"
    )


def test_agent_runtime_checkpoints_exact_pending_task_at_budget_boundary() -> None:
    runtime = AgentRuntime(
        subsystems={"TheoryDeveloper": TheorySubsystem()},
        blackboard=BlackboardState(project_id="runtime-checkpoint-test"),
    )

    result = runtime.run(
        AgentTask(
            task_id="theory:q1",
            owner_subsystem="TheoryDeveloper",
            objective="derive candidate frontier theorem",
        ),
        max_iterations=1,
    )

    assert result.status == "MAX_ITERATIONS_REACHED"
    assert result.pending_task_checkpoint_reason == (
        "outer_iteration_budget_exhausted"
    )
    assert result.pending_task is not None
    assert result.pending_task.task_id == "simulate:q1"
    continuation_ref = result.pending_task_continuation_ref
    continuation = result.blackboard.artifacts[
        continuation_ref["continuation_id"]
    ]
    assert stable_hash(continuation) == continuation_ref["continuation_hash"]
    restored = restore_agent_task_continuation(
        continuation,
        result.blackboard.artifacts,
    )
    assert restored == result.pending_task

    compact = result.to_json()
    assert compact["pending_task"] == continuation_ref["task_ref"]
    assert "inputs" not in compact["pending_task"]
    assert compact["pending_task_continuation_ref"] == continuation_ref


def test_agent_runtime_separates_workspace_and_outer_graph_budgets() -> None:
    class WorkspaceSubsystem:
        name = "TheoryDeveloper"

        def __init__(self) -> None:
            self.calls = 0

        def run(
            self,
            task: AgentTask,
            blackboard: BlackboardState,
        ) -> AgentStepResult:
            self.calls += 1
            if self.calls == 1:
                next_task = AgentTask(
                    task_id="theory:q1:2",
                    owner_subsystem=self.name,
                    objective=task.objective,
                )
                return AgentStepResult(
                    status="REVISE",
                    rationale="checkpoint exact model-owned mathematics",
                    next_task=mark_same_owner_workspace_continuation(
                        parent_task=task,
                        next_task=next_task,
                    ),
                )
            return AgentStepResult(
                status="REROUTE",
                rationale="stable claim can now enter simulation",
                next_task=AgentTask(
                    task_id="simulate:q1",
                    owner_subsystem="SimulationEngineer",
                    objective="test the stable claim",
                ),
            )

    class SimulationSubsystem:
        name = "SimulationEngineer"

        def run(
            self,
            task: AgentTask,
            blackboard: BlackboardState,
        ) -> AgentStepResult:
            return AgentStepResult(status="ACCEPTED", rationale="simulation complete")

    result = AgentRuntime(
        subsystems={
            "TheoryDeveloper": WorkspaceSubsystem(),
            "SimulationEngineer": SimulationSubsystem(),
        },
        blackboard=BlackboardState(project_id="split-iteration-budgets"),
    ).run(
        AgentTask(
            task_id="theory:q1:1",
            owner_subsystem="TheoryDeveloper",
            objective="develop one durable claim",
        ),
        max_iterations=2,
    )

    assert result.status == "ACCEPTED"
    assert len(result.traces) == 3
    assert result.outer_graph_iterations_consumed == 2
    assert result.same_owner_workspace_continuations_consumed == 1
    assert [row.iteration_budget_scope for row in result.traces] == [
        RUNTIME_SAME_OWNER_WORKSPACE_BUDGET_SCOPE,
        RUNTIME_OUTER_GRAPH_BUDGET_SCOPE,
        RUNTIME_OUTER_GRAPH_BUDGET_SCOPE,
    ]
    payload = result.to_json()
    assert payload["runtime_steps_executed"] == 3
    assert payload["outer_graph_iterations_consumed"] == 2
    assert payload["same_owner_workspace_continuations_consumed"] == 1


def test_agent_runtime_unmarked_same_owner_revision_spends_outer_budget() -> None:
    class UnmarkedWorkspaceSubsystem:
        name = "TheoryDeveloper"

        def run(
            self,
            task: AgentTask,
            blackboard: BlackboardState,
        ) -> AgentStepResult:
            return AgentStepResult(
                status="REVISE",
                rationale="unmarked same-owner route",
                next_task=AgentTask(
                    task_id="theory:q1:unmarked",
                    owner_subsystem=self.name,
                    objective=task.objective,
                ),
            )

    result = AgentRuntime(
        subsystems={"TheoryDeveloper": UnmarkedWorkspaceSubsystem()},
        blackboard=BlackboardState(project_id="unmarked-workspace-budget"),
    ).run(
        AgentTask(
            task_id="theory:q1",
            owner_subsystem="TheoryDeveloper",
            objective="attempt an unmarked continuation",
        ),
        max_iterations=1,
    )

    assert result.status == "MAX_ITERATIONS_REACHED"
    assert result.pending_task_checkpoint_reason == (
        "outer_iteration_budget_exhausted"
    )
    assert result.outer_graph_iterations_consumed == 1
    assert result.same_owner_workspace_continuations_consumed == 0


def test_agent_runtime_checkpoints_at_same_owner_workspace_budget() -> None:
    class ProgressingWorkspaceSubsystem:
        name = "Formalizer"

        def run(
            self,
            task: AgentTask,
            blackboard: BlackboardState,
        ) -> AgentStepResult:
            next_task = AgentTask(
                task_id=f"{task.task_id}:next",
                owner_subsystem=self.name,
                objective=task.objective,
            )
            return AgentStepResult(
                status="REVISE",
                rationale="new Lean workspace checkpoint",
                next_task=mark_same_owner_workspace_continuation(
                    parent_task=task,
                    next_task=next_task,
                ),
            )

    result = AgentRuntime(
        subsystems={"Formalizer": ProgressingWorkspaceSubsystem()},
        blackboard=BlackboardState(project_id="workspace-budget-checkpoint"),
    ).run(
        AgentTask(
            task_id="formalize:q1",
            owner_subsystem="Formalizer",
            objective="continue compiling model-authored Lean",
        ),
        max_iterations=2,
    )

    assert result.status == "MAX_ITERATIONS_REACHED"
    assert result.pending_task_checkpoint_reason == (
        "same_owner_workspace_continuation_budget_exhausted"
    )
    assert result.outer_graph_iterations_consumed == 0
    assert result.same_owner_workspace_continuations_consumed == 2
    assert result.pending_task is not None
    assert result.pending_task.task_id == "formalize:q1:next:next"


def test_agent_runtime_handoff_policy_can_rewrite_next_task() -> None:
    class ReviewSubsystem:
        name = "ReviewSubsystem"

        def run(
            self,
            task: AgentTask,
            blackboard: BlackboardState,
        ) -> AgentStepResult:
            return AgentStepResult(
                status="ACCEPTED",
                rationale="review accepted rewritten handoff",
                observations=(
                    EnvironmentObservation(
                        observation_type="review_task_received",
                        summary=str(task.inputs["original_next_task_id"]),
                    ),
                ),
            )

    def policy(
        *,
        iteration: int,
        task: AgentTask,
        subsystem_name: str,
        result: AgentStepResult,
        blackboard: BlackboardState,
    ) -> AgentStepResult:
        if result.next_task is None:
            return result
        assert iteration == 1
        assert task.task_id == "theory:q1"
        assert subsystem_name == "TheoryDeveloper"
        assert blackboard.project_id == "runtime-policy-test"
        return AgentStepResult(
            status="REROUTE",
            rationale="central policy routed handoff through review",
            produced_artifacts=result.produced_artifacts,
            observations=result.observations
            + (
                EnvironmentObservation(
                    observation_type="handoff_policy_rewrite",
                    summary="rewrote simulation handoff",
                ),
            ),
            tool_calls=result.tool_calls,
            evidence_entries=result.evidence_entries,
            next_task=AgentTask(
                task_id="review:q1",
                owner_subsystem="ReviewSubsystem",
                objective="review rewritten task",
                inputs={"original_next_task_id": result.next_task.task_id},
                expected_artifacts=("review_manifest",),
                acceptance_gate="review accepts rewritten handoff",
            ),
            failure_classification="handoff_policy_rewrite",
        )

    runtime = AgentRuntime(
        subsystems={
            "TheoryDeveloper": TheorySubsystem(),
            "ReviewSubsystem": ReviewSubsystem(),
        },
        blackboard=BlackboardState(project_id="runtime-policy-test"),
        handoff_policy=policy,
    )

    result = runtime.run(
        AgentTask(
            task_id="theory:q1",
            owner_subsystem="TheoryDeveloper",
            objective="derive candidate frontier theorem",
        ),
        max_iterations=2,
    )

    assert result.status == "ACCEPTED"
    assert result.traces[0].next_task_id == "review:q1"
    assert result.traces[0].failure_classification == "handoff_policy_rewrite"
    assert result.traces[0].observations[-1].observation_type == (
        "handoff_policy_rewrite"
    )
    assert result.traces[1].subsystem == "ReviewSubsystem"
    assert result.blackboard.handoff_ledger[0].to_subsystem == "ReviewSubsystem"
    assert result.blackboard.handoff_ledger[0].next_task_acceptance_gate == (
        "review accepts rewritten handoff"
    )
    assert result.blackboard.artifacts["theory_packet:q1"]["claim"] == (
        "candidate coverage theorem"
    )


def test_agent_runtime_snapshots_artifacts_and_handoffs_across_subsystems() -> None:
    shared_payload = {"nested": {"value": "original"}}
    caller_payload = {"value": "caller-original"}

    class Producer:
        name = "Producer"

        def run(
            self,
            task: AgentTask,
            blackboard: BlackboardState,
        ) -> AgentStepResult:
            task.inputs["caller_context"]["value"] = "mutated-inside-runtime"
            return AgentStepResult(
                status="REROUTE",
                rationale="publish an immutable artifact and route its context",
                produced_artifacts={"artifact:shared": shared_payload},
                next_task=AgentTask(
                    task_id="mutate:shared",
                    owner_subsystem="Mutator",
                    objective="exercise downstream mutable inputs",
                    inputs={"downstream_context": shared_payload},
                ),
            )

    class Mutator:
        name = "Mutator"

        def run(
            self,
            task: AgentTask,
            blackboard: BlackboardState,
        ) -> AgentStepResult:
            task.inputs["downstream_context"]["nested"]["value"] = "mutated"
            shared_payload["nested"]["value"] = "mutated-outside-runtime"
            return AgentStepResult(status="ACCEPTED", rationale="mutation attempted")

    result = AgentRuntime(
        subsystems={"Producer": Producer(), "Mutator": Mutator()},
        blackboard=BlackboardState(project_id="immutable-snapshot-test"),
    ).run(
        AgentTask(
            task_id="produce:shared",
            owner_subsystem="Producer",
            objective="publish one artifact",
            inputs={"caller_context": caller_payload},
        ),
        max_iterations=2,
    )

    assert result.status == "ACCEPTED"
    assert caller_payload == {"value": "caller-original"}
    assert result.blackboard.artifacts["artifact:shared"] == {
        "nested": {"value": "original"}
    }
    assert result.traces[0].next_task is not None
    assert result.traces[0].next_task.inputs["downstream_context"] == {
        "nested": {"value": "original"}
    }


def test_agent_runtime_preserves_failed_task_without_implicit_restart() -> None:
    class APITimeoutError(Exception):
        pass

    APITimeoutError.__module__ = "anthropic"

    class SlowProviderSubsystem:
        name = "TheoryDeveloper"

        def __init__(self) -> None:
            self.calls = 0

        def run(
            self,
            task: AgentTask,
            blackboard: BlackboardState,
        ) -> AgentStepResult:
            self.calls += 1
            raise APITimeoutError("request timed out")

    subsystem = SlowProviderSubsystem()
    progress_rows: list[dict[str, object]] = []
    initial_task = AgentTask(
        task_id="theory:q1",
        owner_subsystem="TheoryDeveloper",
        objective="preserve one terminal provider failure",
        inputs={"question": {"id": "q1"}},
    )
    result = AgentRuntime(
        subsystems={"TheoryDeveloper": subsystem},
        blackboard=BlackboardState(project_id="provider-timeout-test"),
    ).run(
        initial_task,
        progress_callback=progress_rows.append,
    )

    assert result.status == "FAILED"
    assert subsystem.calls == 1
    assert result.traces[0].failure_classification == "subsystem_exception"
    assert result.traces[0].observations[0].payload["exception_type"] == (
        "APITimeoutError"
    )
    assert result.pending_task == initial_task
    assert result.pending_task_checkpoint_reason == "terminal_subsystem_error"
    assert not any(
        row["event_type"] == "subsystem_retry" for row in progress_rows
    )
    continuation = result.blackboard.artifacts[
        result.pending_task_continuation_ref["continuation_id"]
    ]
    assert restore_agent_task_continuation(
        continuation,
        result.blackboard.artifacts,
    ) == initial_task


def test_agent_runtime_blocks_missing_subsystem() -> None:
    result = AgentRuntime(
        subsystems={},
        blackboard=BlackboardState(project_id="runtime-test"),
    ).run(
        AgentTask(
            task_id="formalize:q1",
            owner_subsystem="Formalizer",
            objective="formalize theorem card",
        )
    )

    assert result.status == "BLOCKED"
    assert result.traces[0].failure_classification == "missing_subsystem"
    assert "no registered subsystem: Formalizer" in result.blackboard.active_blockers
