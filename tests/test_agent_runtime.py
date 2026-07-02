from __future__ import annotations

from ai_statistician.agent_runtime import (
    AgentRuntime,
    AgentStepResult,
    AgentTask,
    BlackboardState,
    EnvironmentObservation,
    EvidenceLedgerEntry,
    ToolCallRecord,
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
