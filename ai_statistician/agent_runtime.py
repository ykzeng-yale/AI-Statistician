from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Literal, Mapping, Protocol


RuntimeStatus = Literal[
    "ACCEPTED",
    "REROUTE",
    "REVISE",
    "BLOCKED",
    "FAILED",
    "MAX_ITERATIONS_REACHED",
]


class ModelBackend(Protocol):
    """Replaceable LLM/coding-agent backend used by runtime subsystems."""

    def complete(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        model: str,
        max_tokens: int,
        temperature: float,
    ) -> str:
        ...


@dataclass(frozen=True)
class AgentTask:
    task_id: str
    owner_subsystem: str
    objective: str
    inputs: dict[str, Any] = field(default_factory=dict)
    allowed_tools: tuple[str, ...] = ()
    budget: dict[str, Any] = field(default_factory=dict)
    expected_artifacts: tuple[str, ...] = ()
    acceptance_gate: str = ""
    stop_condition: str = ""


@dataclass(frozen=True)
class ToolCallRecord:
    tool_name: str
    inputs: dict[str, Any] = field(default_factory=dict)
    output_paths: tuple[str, ...] = ()
    input_hash: str = ""
    output_hash: str = ""
    exit_status: str = "not_run"
    stdout_summary: str = ""
    stderr_summary: str = ""
    safety_boundary: str = ""
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass(frozen=True)
class EnvironmentObservation:
    observation_type: str
    summary: str
    payload: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass(frozen=True)
class EvidenceLedgerEntry:
    evidence_id: str
    task_id: str
    artifact_id: str
    evidence_type: str
    status: str
    boundary: str
    payload: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class BlackboardState:
    project_id: str
    artifacts: dict[str, Any] = field(default_factory=dict)
    evidence_ledger: list[EvidenceLedgerEntry] = field(default_factory=list)
    active_blockers: list[str] = field(default_factory=list)
    task_history: list[str] = field(default_factory=list)

    def to_json(self) -> dict[str, Any]:
        return {
            "project_id": self.project_id,
            "artifacts": self.artifacts,
            "evidence_ledger": [asdict(row) for row in self.evidence_ledger],
            "active_blockers": list(self.active_blockers),
            "task_history": list(self.task_history),
        }


@dataclass(frozen=True)
class AgentStepResult:
    status: RuntimeStatus
    rationale: str
    produced_artifacts: dict[str, Any] = field(default_factory=dict)
    observations: tuple[EnvironmentObservation, ...] = ()
    tool_calls: tuple[ToolCallRecord, ...] = ()
    evidence_entries: tuple[EvidenceLedgerEntry, ...] = ()
    next_task: AgentTask | None = None
    failure_classification: str = ""


@dataclass(frozen=True)
class RuntimeIterationTrace:
    iteration: int
    task: AgentTask
    subsystem: str
    status: RuntimeStatus
    rationale: str
    observations: tuple[EnvironmentObservation, ...] = ()
    tool_calls: tuple[ToolCallRecord, ...] = ()
    produced_artifact_ids: tuple[str, ...] = ()
    evidence_ids: tuple[str, ...] = ()
    next_task_id: str = ""
    failure_classification: str = ""
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_json(self) -> dict[str, Any]:
        row = asdict(self)
        row["task"] = asdict(self.task)
        row["observations"] = [asdict(obs) for obs in self.observations]
        row["tool_calls"] = [asdict(call) for call in self.tool_calls]
        return row


class AgentSubsystem(Protocol):
    name: str

    def run(self, task: AgentTask, blackboard: BlackboardState) -> AgentStepResult:
        ...


@dataclass(frozen=True)
class AgentRuntimeResult:
    status: RuntimeStatus
    final_task_id: str
    blackboard: BlackboardState
    traces: tuple[RuntimeIterationTrace, ...]

    def to_json(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "final_task_id": self.final_task_id,
            "blackboard": self.blackboard.to_json(),
            "traces": [row.to_json() for row in self.traces],
        }


class AgentRuntime:
    """Small plan-act-observe-revise loop for AI Statistician subsystems."""

    def __init__(
        self,
        *,
        subsystems: Mapping[str, AgentSubsystem],
        blackboard: BlackboardState,
    ) -> None:
        self.subsystems = dict(subsystems)
        self.blackboard = blackboard

    def run(
        self,
        initial_task: AgentTask,
        *,
        max_iterations: int = 4,
        max_transient_subsystem_retries: int = 0,
        progress_callback: Callable[[dict[str, Any]], None] | None = None,
    ) -> AgentRuntimeResult:
        task = initial_task
        traces: list[RuntimeIterationTrace] = []
        final_status: RuntimeStatus = "MAX_ITERATIONS_REACHED"
        max_retries = max(0, int(max_transient_subsystem_retries))

        for iteration in range(1, max_iterations + 1):
            subsystem = self.subsystems.get(task.owner_subsystem)
            self.blackboard.task_history.append(task.task_id)
            _emit_progress(
                progress_callback,
                event_type="subsystem_start",
                iteration=iteration,
                task=task,
                subsystem=task.owner_subsystem if subsystem is None else getattr(subsystem, "name", task.owner_subsystem),
            )
            if subsystem is None:
                trace = RuntimeIterationTrace(
                    iteration=iteration,
                    task=task,
                    subsystem=task.owner_subsystem,
                    status="BLOCKED",
                    rationale=f"no registered subsystem: {task.owner_subsystem}",
                    failure_classification="missing_subsystem",
                )
                traces.append(trace)
                self.blackboard.active_blockers.append(trace.rationale)
                _emit_progress(
                    progress_callback,
                    event_type="subsystem_finish",
                    iteration=iteration,
                    task=task,
                    subsystem=task.owner_subsystem,
                    status=trace.status,
                    rationale=trace.rationale,
                    produced_artifact_ids=(),
                    evidence_ids=(),
                    next_task_id="",
                    failure_classification=trace.failure_classification,
                )
                final_status = "BLOCKED"
                break

            retry_observations: list[EnvironmentObservation] = []
            for attempt in range(max_retries + 1):
                try:
                    result = subsystem.run(task, self.blackboard)
                    if retry_observations:
                        result = AgentStepResult(
                            status=result.status,
                            rationale=result.rationale,
                            produced_artifacts=result.produced_artifacts,
                            observations=tuple(retry_observations) + result.observations,
                            tool_calls=result.tool_calls,
                            evidence_entries=result.evidence_entries,
                            next_task=result.next_task,
                            failure_classification=result.failure_classification,
                        )
                    break
                except Exception as exc:  # pragma: no cover - defensive runtime boundary
                    retryable = _is_transient_subsystem_exception(exc)
                    if retryable and attempt < max_retries:
                        retry_observations.append(
                            EnvironmentObservation(
                                observation_type="subsystem_exception_retry",
                                summary=(
                                    f"{exc.__class__.__name__}: {exc}; "
                                    f"retrying subsystem attempt {attempt + 1}/{max_retries}"
                                ),
                                payload={
                                    "exception_type": exc.__class__.__name__,
                                    "exception_module": exc.__class__.__module__,
                                    **_exception_debug_payload(exc),
                                    "retry_attempt": attempt + 1,
                                    "max_retries": max_retries,
                                    "retryable": True,
                                },
                            )
                        )
                        _emit_progress(
                            progress_callback,
                            event_type="subsystem_retry",
                            iteration=iteration,
                            task=task,
                            subsystem=getattr(subsystem, "name", task.owner_subsystem),
                            status="FAILED",
                            rationale=f"retrying after {exc.__class__.__name__}",
                            failure_classification="transient_subsystem_exception_retry",
                            retry_attempt=attempt + 1,
                            max_retries=max_retries,
                        )
                        continue
                    failure_classification = (
                        "transient_subsystem_exception_exhausted"
                        if retry_observations and retryable
                        else "subsystem_exception"
                    )
                    result = AgentStepResult(
                        status="FAILED",
                        rationale=f"subsystem raised {exc.__class__.__name__}: {exc}",
                        observations=tuple(retry_observations)
                        + (
                            EnvironmentObservation(
                                observation_type="subsystem_exception",
                                summary=str(exc),
                                payload={
                                    "exception_type": exc.__class__.__name__,
                                    "exception_module": exc.__class__.__module__,
                                    **_exception_debug_payload(exc),
                                    "retryable": retryable,
                                    "retry_attempts": len(retry_observations),
                                },
                            ),
                        ),
                        failure_classification=failure_classification,
                    )
                    _emit_progress(
                        progress_callback,
                        event_type="subsystem_exception",
                        iteration=iteration,
                        task=task,
                        subsystem=getattr(subsystem, "name", task.owner_subsystem),
                        status=result.status,
                        rationale=result.rationale,
                        failure_classification=failure_classification,
                    )
                    break

            self.blackboard.artifacts.update(result.produced_artifacts)
            self.blackboard.evidence_ledger.extend(result.evidence_entries)
            if result.status in {"BLOCKED", "FAILED"} and result.rationale:
                self.blackboard.active_blockers.append(result.rationale)
            trace = RuntimeIterationTrace(
                iteration=iteration,
                task=task,
                subsystem=getattr(subsystem, "name", task.owner_subsystem),
                status=result.status,
                rationale=result.rationale,
                observations=result.observations,
                tool_calls=result.tool_calls,
                produced_artifact_ids=tuple(result.produced_artifacts.keys()),
                evidence_ids=tuple(row.evidence_id for row in result.evidence_entries),
                next_task_id=result.next_task.task_id if result.next_task is not None else "",
                failure_classification=result.failure_classification,
            )
            traces.append(trace)
            _emit_progress(
                progress_callback,
                event_type="subsystem_finish",
                iteration=iteration,
                task=task,
                subsystem=trace.subsystem,
                status=trace.status,
                rationale=trace.rationale,
                produced_artifact_ids=trace.produced_artifact_ids,
                evidence_ids=trace.evidence_ids,
                next_task_id=trace.next_task_id,
                failure_classification=trace.failure_classification,
            )

            if result.status == "ACCEPTED":
                final_status = "ACCEPTED"
                break
            if result.status in {"BLOCKED", "FAILED"}:
                final_status = result.status
                break
            if result.next_task is None:
                final_status = result.status
                break
            task = result.next_task

        return AgentRuntimeResult(
            status=final_status,
            final_task_id=task.task_id,
            blackboard=self.blackboard,
            traces=tuple(traces),
        )


def _emit_progress(
    progress_callback: Callable[[dict[str, Any]], None] | None,
    *,
    event_type: str,
    iteration: int,
    task: AgentTask,
    subsystem: str,
    status: RuntimeStatus | str = "",
    rationale: str = "",
    produced_artifact_ids: tuple[str, ...] = (),
    evidence_ids: tuple[str, ...] = (),
    next_task_id: str = "",
    failure_classification: str = "",
    retry_attempt: int = 0,
    max_retries: int = 0,
) -> None:
    if progress_callback is None:
        return
    progress_callback(
        {
            "created_at": datetime.now(timezone.utc).isoformat(),
            "event_type": event_type,
            "iteration": iteration,
            "task_id": task.task_id,
            "owner_subsystem": task.owner_subsystem,
            "subsystem": subsystem,
            "status": status,
            "rationale": rationale,
            "produced_artifact_ids": list(produced_artifact_ids),
            "evidence_ids": list(evidence_ids),
            "next_task_id": next_task_id,
            "failure_classification": failure_classification,
            "retry_attempt": retry_attempt,
            "max_retries": max_retries,
        }
    )


def _is_transient_subsystem_exception(exc: Exception) -> bool:
    name = type(exc).__name__.lower()
    module = type(exc).__module__.lower()
    text = str(exc).lower()
    haystack = f"{module}.{name} {text}"
    retry_markers = (
        "apiconnectionerror",
        "api_connection_error",
        "ratelimiterror",
        "rate_limit_error",
        "timeout",
        "connection",
        "temporarily unavailable",
        "server error",
        "overloaded",
    )
    return any(marker in haystack for marker in retry_markers)


def _exception_debug_payload(exc: Exception) -> dict[str, str]:
    """Compact exception diagnostics for traces without prompts or secrets."""

    payload = {"exception_repr": _truncate_debug_text(repr(exc), 500)}
    cause = exc.__cause__
    context = exc.__context__
    if cause is not None:
        payload["cause_type"] = cause.__class__.__name__
        payload["cause_module"] = cause.__class__.__module__
        payload["cause_summary"] = _truncate_debug_text(str(cause), 500)
        payload["cause_repr"] = _truncate_debug_text(repr(cause), 500)
    if context is not None and context is not cause:
        payload["context_type"] = context.__class__.__name__
        payload["context_module"] = context.__class__.__module__
        payload["context_summary"] = _truncate_debug_text(str(context), 500)
        payload["context_repr"] = _truncate_debug_text(repr(context), 500)
    return payload


def _truncate_debug_text(value: str, limit: int) -> str:
    return value if len(value) <= limit else value[: max(0, limit - 3)] + "..."
