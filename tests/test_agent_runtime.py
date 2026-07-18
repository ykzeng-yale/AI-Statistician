from __future__ import annotations

from ai_statistician.agent_runtime import (
    AgentRuntime,
    AgentStepResult,
    AgentTask,
    BlackboardState,
    EnvironmentObservation,
    EvidenceLedgerEntry,
    ToolCallRecord,
    agent_runtime_substage,
)


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


class APIConnectionError(Exception):
    pass


class FlakySubsystem:
    name = "FlakyLLMSubsystem"

    def __init__(self) -> None:
        self.calls = 0

    def run(self, task: AgentTask, blackboard: BlackboardState) -> AgentStepResult:
        self.calls += 1
        if self.calls == 1:
            raise APIConnectionError("Connection error.")
        return AgentStepResult(
            status="ACCEPTED",
            rationale="subsystem succeeded after transient provider retry",
            produced_artifacts={"llm_packet:q1": {"ok": True}},
            observations=(
                EnvironmentObservation(
                    observation_type="llm_packet",
                    summary="validated packet returned after retry",
                ),
            ),
        )


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
            ):
                pass
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
    payload = result.to_json()
    assert payload["traces"][0]["next_task"]["task_id"] == "simulate:q1"
    assert payload["traces"][0]["next_task"]["inputs"] == {
        "theory_packet": "theory_packet:q1"
    }
    assert payload["traces"][0]["handoff_id"] == handoff.handoff_id
    assert payload["blackboard"]["handoff_ledger"][0]["to_subsystem"] == "SimulatorDesigner"
    assert payload["traces"][1]["observations"][0]["observation_type"] == "simulation_result"


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


def test_agent_runtime_retries_transient_subsystem_exception() -> None:
    subsystem = FlakySubsystem()
    result = AgentRuntime(
        subsystems={"FlakyLLMSubsystem": subsystem},
        blackboard=BlackboardState(project_id="runtime-test"),
    ).run(
        AgentTask(
            task_id="llm:q1",
            owner_subsystem="FlakyLLMSubsystem",
            objective="call live provider-backed subsystem",
        ),
        max_transient_subsystem_retries=1,
    )

    assert result.status == "ACCEPTED"
    assert subsystem.calls == 2
    assert "llm_packet:q1" in result.blackboard.artifacts
    assert result.traces[0].observations[0].observation_type == "subsystem_exception_retry"
    assert result.traces[0].observations[0].payload["retryable"] is True
    assert result.traces[0].observations[1].observation_type == "llm_packet"


def test_agent_runtime_retries_provider_api_timeout_once() -> None:
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
            if self.calls == 1:
                raise APITimeoutError("request timed out")
            return AgentStepResult(
                status="ACCEPTED",
                rationale="provider retry returned a theory packet",
                produced_artifacts={"theory_packet:q1": {"ok": True}},
            )

    subsystem = SlowProviderSubsystem()
    progress_rows: list[dict[str, object]] = []
    result = AgentRuntime(
        subsystems={"TheoryDeveloper": subsystem},
        blackboard=BlackboardState(project_id="provider-timeout-test"),
    ).run(
        AgentTask(
            task_id="theory:q1",
            owner_subsystem="TheoryDeveloper",
            objective="retry one provider API timeout",
        ),
        max_transient_subsystem_retries=1,
        progress_callback=progress_rows.append,
    )

    assert result.status == "ACCEPTED"
    assert subsystem.calls == 2
    assert result.traces[0].observations[0].observation_type == (
        "subsystem_exception_retry"
    )
    assert result.traces[0].observations[0].payload["exception_type"] == (
        "APITimeoutError"
    )
    retry_row = next(
        row for row in progress_rows if row["event_type"] == "subsystem_retry"
    )
    finish_row = next(
        row for row in progress_rows if row["event_type"] == "subsystem_finish"
    )
    assert retry_row["retry_attempt"] == 1
    assert retry_row["max_retries"] == 1
    assert finish_row["retry_attempt"] == 1
    assert finish_row["max_retries"] == 1


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
