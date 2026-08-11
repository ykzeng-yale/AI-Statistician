from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
from copy import deepcopy
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from time import perf_counter
from typing import Any, Callable, Iterator, Literal, Mapping, Protocol

from .fingerprint import stable_hash


RuntimeStatus = Literal[
    "ACCEPTED",
    "REROUTE",
    "REVISE",
    "BLOCKED",
    "FAILED",
    "MAX_ITERATIONS_REACHED",
]


_ACTIVE_PROGRESS_CONTEXT: ContextVar[dict[str, Any] | None] = ContextVar(
    "ai_statistician_active_progress_context",
    default=None,
)


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


def agent_task_reference(task: AgentTask | None) -> dict[str, Any] | None:
    """Return a content-addressed task reference without copying its payload."""

    if task is None:
        return None
    inputs_hash = stable_hash(task.inputs)
    snapshot = {
        "task_id": task.task_id,
        "owner_subsystem": task.owner_subsystem,
        "objective": task.objective,
        "inputs_hash": inputs_hash,
        "allowed_tools": task.allowed_tools,
        "budget": task.budget,
        "expected_artifacts": task.expected_artifacts,
        "acceptance_gate": task.acceptance_gate,
        "stop_condition": task.stop_condition,
    }
    return {
        "artifact_kind": "AgentTaskRef",
        "task_id": task.task_id,
        "owner_subsystem": task.owner_subsystem,
        "objective_ref": "task_objective:" + stable_hash(task.objective)[:20],
        "task_snapshot_hash": stable_hash(snapshot),
        "inputs_hash": inputs_hash,
        "input_keys": sorted(str(key) for key in task.inputs),
        "budget": deepcopy(task.budget),
        "allowed_tools": list(task.allowed_tools),
        "expected_artifacts": list(task.expected_artifacts),
        "acceptance_gate_ref": (
            "task_acceptance_gate:" + stable_hash(task.acceptance_gate)[:20]
            if task.acceptance_gate
            else ""
        ),
        "stop_condition_ref": (
            "task_stop_condition:" + stable_hash(task.stop_condition)[:20]
            if task.stop_condition
            else ""
        ),
    }


def agent_task_from_payload(payload: Mapping[str, Any]) -> AgentTask:
    """Reconstruct one validated AgentTask from a persisted payload."""

    task_id = str(payload.get("task_id", "") or "")
    owner_subsystem = str(payload.get("owner_subsystem", "") or "")
    if not task_id or not owner_subsystem:
        raise ValueError(
            "runtime task payload must include task_id and owner_subsystem"
        )
    return AgentTask(
        task_id=task_id,
        owner_subsystem=owner_subsystem,
        objective=str(payload.get("objective", "") or ""),
        inputs=(
            dict(payload.get("inputs", {}))
            if isinstance(payload.get("inputs", {}), Mapping)
            else {}
        ),
        allowed_tools=tuple(
            str(item)
            for item in (
                payload.get("allowed_tools", [])
                if isinstance(payload.get("allowed_tools", []), (list, tuple))
                else []
            )
        ),
        budget=(
            dict(payload.get("budget", {}))
            if isinstance(payload.get("budget", {}), Mapping)
            else {}
        ),
        expected_artifacts=tuple(
            str(item)
            for item in (
                payload.get("expected_artifacts", [])
                if isinstance(
                    payload.get("expected_artifacts", []), (list, tuple)
                )
                else []
            )
        ),
        acceptance_gate=str(payload.get("acceptance_gate", "") or ""),
        stop_condition=str(payload.get("stop_condition", "") or ""),
    )


def agent_task_continuation_reference(
    continuation: Mapping[str, Any],
) -> dict[str, Any]:
    """Return a compact immutable reference to a task continuation artifact."""

    continuation_id = str(continuation.get("continuation_id", "") or "")
    if (
        not continuation_id
        or continuation.get("artifact_kind") != "RuntimeAgentTaskContinuation"
    ):
        raise ValueError("invalid runtime agent task continuation")
    return {
        "artifact_kind": "RuntimeAgentTaskContinuationRef",
        "continuation_id": continuation_id,
        "continuation_hash": stable_hash(dict(continuation)),
        "task_ref": deepcopy(dict(continuation.get("task_ref", {}) or {})),
    }


def materialize_agent_task_continuation(
    task: AgentTask,
    *,
    schema_version: int = 1,
    linked_input_references: Mapping[str, Mapping[str, Any]] | None = None,
) -> tuple[str, dict[str, Any], dict[str, dict[str, Any]]]:
    """Persist a resumable task without recursively copying large input payloads."""

    full_payload = asdict(task)
    compact_inputs: dict[str, Any] = {}
    artifacts: dict[str, dict[str, Any]] = {}
    linked = {
        str(key): dict(value)
        for key, value in (linked_input_references or {}).items()
        if isinstance(value, Mapping)
    }
    for key, value in task.inputs.items():
        input_key = str(key)
        if isinstance(value, Mapping):
            mapping = deepcopy(dict(value))
            mapping_hash = stable_hash(mapping)
            linked_ref = linked.get(mapping_hash)
            if linked_ref is not None:
                compact_inputs[input_key] = deepcopy(linked_ref)
                continue
            mapping_id = "agent_task_input_mapping:" + mapping_hash[:20]
            mapping_artifact = {
                "schema_version": schema_version,
                "artifact_kind": "RuntimeAgentTaskInputMapping",
                "mapping_id": mapping_id,
                "mapping_hash": mapping_hash,
                "mapping": mapping,
            }
            artifacts[mapping_id] = mapping_artifact
            compact_inputs[input_key] = {
                "artifact_kind": "RuntimeAgentTaskInputMappingRef",
                "mapping_id": mapping_id,
                "mapping_hash": mapping_hash,
                "artifact_hash": stable_hash(mapping_artifact),
            }
            continue
        compact_inputs[input_key] = deepcopy(value)
    task_template = {
        **full_payload,
        "inputs": compact_inputs,
    }
    original_task_hash = stable_hash(full_payload)
    continuation_id = "agent_task_continuation:" + original_task_hash[:20]
    continuation = {
        "schema_version": schema_version,
        "artifact_kind": "RuntimeAgentTaskContinuation",
        "continuation_id": continuation_id,
        "original_task_hash": original_task_hash,
        "task_ref": agent_task_reference(task),
        "task_template": task_template,
        "payload_policy": "content_addressed_input_refs",
    }
    artifacts[continuation_id] = continuation
    return continuation_id, continuation, artifacts


def restore_agent_task_continuation(
    continuation: Mapping[str, Any],
    artifacts: Mapping[str, Any],
) -> AgentTask:
    """Hydrate and verify a content-addressed task continuation."""

    visited: set[str] = set()

    def restore(current: Mapping[str, Any]) -> AgentTask:
        continuation_id = str(current.get("continuation_id", "") or "")
        if (
            current.get("artifact_kind") != "RuntimeAgentTaskContinuation"
            or not continuation_id
            or continuation_id in visited
        ):
            raise ValueError("invalid or cyclic runtime agent task continuation")
        visited.add(continuation_id)
        template = current.get("task_template", {})
        if not isinstance(template, Mapping):
            raise ValueError("runtime task continuation template missing")
        payload = deepcopy(dict(template))
        inputs = payload.get("inputs", {})
        if not isinstance(inputs, Mapping):
            raise ValueError("runtime task continuation inputs missing")
        hydrated_inputs: dict[str, Any] = {}
        for key, value in inputs.items():
            if not isinstance(value, Mapping):
                hydrated_inputs[str(key)] = deepcopy(value)
                continue
            artifact_kind = str(value.get("artifact_kind", "") or "")
            if artifact_kind == "RuntimeAgentTaskInputMappingRef":
                mapping_id = str(value.get("mapping_id", "") or "")
                raw_mapping = artifacts.get(mapping_id, {})
                if not isinstance(raw_mapping, Mapping):
                    raise ValueError("runtime task input mapping missing")
                mapping_artifact = dict(raw_mapping)
                mapping = mapping_artifact.get("mapping", {})
                if (
                    mapping_artifact.get("artifact_kind")
                    != "RuntimeAgentTaskInputMapping"
                    or str(mapping_artifact.get("mapping_id", "") or "")
                    != mapping_id
                    or stable_hash(mapping_artifact)
                    != str(value.get("artifact_hash", "") or "")
                    or not isinstance(mapping, Mapping)
                    or stable_hash(dict(mapping))
                    != str(value.get("mapping_hash", "") or "")
                ):
                    raise ValueError("runtime task input mapping hash mismatch")
                hydrated_inputs[str(key)] = deepcopy(dict(mapping))
                continue
            if artifact_kind == "RuntimeAgentTaskContinuationRef":
                nested_id = str(value.get("continuation_id", "") or "")
                raw_nested = artifacts.get(nested_id, {})
                if not isinstance(raw_nested, Mapping):
                    raise ValueError("nested runtime task continuation missing")
                nested = dict(raw_nested)
                if (
                    stable_hash(nested)
                    != str(value.get("continuation_hash", "") or "")
                    or nested.get("task_ref") != value.get("task_ref")
                ):
                    raise ValueError("nested runtime task continuation mismatch")
                hydrated_inputs[str(key)] = asdict(restore(nested))
                continue
            hydrated_inputs[str(key)] = deepcopy(dict(value))
        payload["inputs"] = hydrated_inputs
        task = agent_task_from_payload(payload)
        original_task_hash = stable_hash(asdict(task))
        if (
            original_task_hash
            != str(current.get("original_task_hash", "") or "")
            or continuation_id
            != "agent_task_continuation:" + original_task_hash[:20]
            or agent_task_reference(task) != current.get("task_ref")
        ):
            raise ValueError("runtime task continuation identity mismatch")
        visited.remove(continuation_id)
        return task

    return restore(continuation)


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


@dataclass(frozen=True)
class TaskHandoffRecord:
    handoff_id: str
    from_task_id: str
    to_task_id: str
    from_subsystem: str
    to_subsystem: str
    status: RuntimeStatus
    rationale: str
    produced_artifact_ids: tuple[str, ...] = ()
    evidence_ids: tuple[str, ...] = ()
    next_task_input_keys: tuple[str, ...] = ()
    next_task_allowed_tools: tuple[str, ...] = ()
    next_task_expected_artifacts: tuple[str, ...] = ()
    next_task_acceptance_gate: str = ""
    failure_classification: str = ""
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class BlackboardState:
    project_id: str
    artifacts: dict[str, Any] = field(default_factory=dict)
    evidence_ledger: list[EvidenceLedgerEntry] = field(default_factory=list)
    handoff_ledger: list[TaskHandoffRecord] = field(default_factory=list)
    active_blockers: list[str] = field(default_factory=list)
    task_history: list[str] = field(default_factory=list)

    def to_json(self) -> dict[str, Any]:
        return {
            "project_id": self.project_id,
            "artifacts": deepcopy(self.artifacts),
            "evidence_ledger": [asdict(row) for row in self.evidence_ledger],
            "handoff_ledger": [asdict(row) for row in self.handoff_ledger],
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
    handoff_id: str = ""
    next_task_id: str = ""
    next_task: AgentTask | None = None
    failure_classification: str = ""
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_json(self, *, include_task_payloads: bool = False) -> dict[str, Any]:
        row = {
            "iteration": self.iteration,
            "subsystem": self.subsystem,
            "status": self.status,
            "rationale": self.rationale,
            "produced_artifact_ids": list(self.produced_artifact_ids),
            "evidence_ids": list(self.evidence_ids),
            "handoff_id": self.handoff_id,
            "next_task_id": self.next_task_id,
            "failure_classification": self.failure_classification,
            "created_at": self.created_at,
        }
        row["task"] = (
            asdict(self.task)
            if include_task_payloads
            else agent_task_reference(self.task)
        )
        row["next_task"] = (
            asdict(self.next_task)
            if include_task_payloads and self.next_task is not None
            else agent_task_reference(self.next_task)
        )
        row["observations"] = [asdict(obs) for obs in self.observations]
        row["tool_calls"] = [asdict(call) for call in self.tool_calls]
        return row


class AgentSubsystem(Protocol):
    name: str

    def run(self, task: AgentTask, blackboard: BlackboardState) -> AgentStepResult:
        ...


class HandoffPolicy(Protocol):
    def __call__(
        self,
        *,
        iteration: int,
        task: AgentTask,
        subsystem_name: str,
        result: AgentStepResult,
        blackboard: BlackboardState,
    ) -> AgentStepResult:
        ...


@dataclass(frozen=True)
class AgentRuntimeResult:
    status: RuntimeStatus
    final_task_id: str
    blackboard: BlackboardState
    traces: tuple[RuntimeIterationTrace, ...]

    def to_json(self, *, include_task_payloads: bool = False) -> dict[str, Any]:
        return {
            "status": self.status,
            "final_task_id": self.final_task_id,
            "blackboard": self.blackboard.to_json(),
            "traces": [
                row.to_json(include_task_payloads=include_task_payloads)
                for row in self.traces
            ],
        }


class AgentRuntime:
    """Small plan-act-observe-revise loop for AI Statistician subsystems."""

    def __init__(
        self,
        *,
        subsystems: Mapping[str, AgentSubsystem],
        blackboard: BlackboardState,
        handoff_policy: HandoffPolicy | None = None,
    ) -> None:
        self.subsystems = dict(subsystems)
        self.blackboard = blackboard
        self.handoff_policy = handoff_policy

    def run(
        self,
        initial_task: AgentTask,
        *,
        max_iterations: int = 4,
        max_transient_subsystem_retries: int = 0,
        progress_callback: Callable[[dict[str, Any]], None] | None = None,
    ) -> AgentRuntimeResult:
        task = deepcopy(initial_task)
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
                max_retries=max_retries,
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
                progress_token = _ACTIVE_PROGRESS_CONTEXT.set(
                    {
                        "progress_callback": progress_callback,
                        "iteration": iteration,
                        "task": task,
                        "subsystem": getattr(
                            subsystem,
                            "name",
                            task.owner_subsystem,
                        ),
                    }
                )
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
                        retry_attempt=len(retry_observations),
                        max_retries=max_retries,
                    )
                    break
                finally:
                    _ACTIVE_PROGRESS_CONTEXT.reset(progress_token)

            subsystem_name = getattr(subsystem, "name", task.owner_subsystem)
            if self.handoff_policy is not None:
                result = self.handoff_policy(
                    iteration=iteration,
                    task=task,
                    subsystem_name=subsystem_name,
                    result=result,
                    blackboard=self.blackboard,
                )

            result = _snapshot_agent_step_result(result)
            self.blackboard.artifacts.update(result.produced_artifacts)
            self.blackboard.evidence_ledger.extend(result.evidence_entries)
            produced_artifact_ids = tuple(result.produced_artifacts.keys())
            evidence_ids = tuple(row.evidence_id for row in result.evidence_entries)
            handoff_record = (
                _build_task_handoff_record(
                    iteration=iteration,
                    task=task,
                    subsystem_name=subsystem_name,
                    result=result,
                    produced_artifact_ids=produced_artifact_ids,
                    evidence_ids=evidence_ids,
                )
                if result.next_task is not None
                else None
            )
            if handoff_record is not None:
                self.blackboard.handoff_ledger.append(handoff_record)
            if result.status in {"BLOCKED", "FAILED"} and result.rationale:
                self.blackboard.active_blockers.append(result.rationale)
            trace = RuntimeIterationTrace(
                iteration=iteration,
                task=deepcopy(task),
                subsystem=subsystem_name,
                status=result.status,
                rationale=result.rationale,
                observations=result.observations,
                tool_calls=result.tool_calls,
                produced_artifact_ids=produced_artifact_ids,
                evidence_ids=evidence_ids,
                handoff_id=handoff_record.handoff_id if handoff_record is not None else "",
                next_task_id=result.next_task.task_id if result.next_task is not None else "",
                next_task=deepcopy(result.next_task),
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
                handoff_id=trace.handoff_id,
                next_task_id=trace.next_task_id,
                failure_classification=trace.failure_classification,
                retry_attempt=len(retry_observations),
                max_retries=max_retries,
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
            task = deepcopy(result.next_task)

        return AgentRuntimeResult(
            status=final_status,
            final_task_id=task.task_id,
            blackboard=self.blackboard,
            traces=tuple(traces),
        )


@contextmanager
def agent_runtime_substage(
    substage: str,
    *,
    metadata: Mapping[str, Any] | None = None,
) -> Iterator[None]:
    """Expose work inside a subsystem through its existing progress callback."""

    context = _ACTIVE_PROGRESS_CONTEXT.get()
    if not context:
        yield
        return
    callback = context.get("progress_callback")
    task = context.get("task")
    if not callable(callback) or not isinstance(task, AgentTask):
        yield
        return
    iteration = int(context.get("iteration", 0) or 0)
    subsystem = str(context.get("subsystem", "") or task.owner_subsystem)
    details = dict(metadata or {})
    started = perf_counter()
    _emit_progress(
        callback,
        event_type="substage_start",
        iteration=iteration,
        task=task,
        subsystem=subsystem,
        substage=substage,
        metadata=details,
    )
    try:
        yield
    except Exception as exc:
        _emit_progress(
            callback,
            event_type="substage_finish",
            iteration=iteration,
            task=task,
            subsystem=subsystem,
            status="FAILED",
            rationale=f"{exc.__class__.__name__}: {exc}",
            substage=substage,
            elapsed_seconds=perf_counter() - started,
            metadata={**details, "exception_type": exc.__class__.__name__},
        )
        raise
    else:
        _emit_progress(
            callback,
            event_type="substage_finish",
            iteration=iteration,
            task=task,
            subsystem=subsystem,
            status="COMPLETED",
            substage=substage,
            elapsed_seconds=perf_counter() - started,
            metadata=details,
        )


def _snapshot_agent_step_result(result: AgentStepResult) -> AgentStepResult:
    """Break mutable aliases before artifacts and handoffs cross runtime ownership."""

    return AgentStepResult(
        status=result.status,
        rationale=result.rationale,
        produced_artifacts=deepcopy(result.produced_artifacts),
        observations=deepcopy(result.observations),
        tool_calls=deepcopy(result.tool_calls),
        evidence_entries=deepcopy(result.evidence_entries),
        next_task=deepcopy(result.next_task),
        failure_classification=result.failure_classification,
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
    handoff_id: str = "",
    next_task_id: str = "",
    failure_classification: str = "",
    retry_attempt: int = 0,
    max_retries: int = 0,
    substage: str = "",
    elapsed_seconds: float = 0.0,
    metadata: Mapping[str, Any] | None = None,
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
            "handoff_id": handoff_id,
            "next_task_id": next_task_id,
            "failure_classification": failure_classification,
            "retry_attempt": retry_attempt,
            "max_retries": max_retries,
            "substage": substage,
            "elapsed_seconds": max(0.0, float(elapsed_seconds or 0.0)),
            "metadata": dict(metadata or {}),
        }
    )


def _build_task_handoff_record(
    *,
    iteration: int,
    task: AgentTask,
    subsystem_name: str,
    result: AgentStepResult,
    produced_artifact_ids: tuple[str, ...],
    evidence_ids: tuple[str, ...],
) -> TaskHandoffRecord:
    next_task = result.next_task
    if next_task is None:  # pragma: no cover - caller guards this.
        raise ValueError("cannot build task handoff record without next_task")
    return TaskHandoffRecord(
        handoff_id=f"handoff:{iteration}:{task.task_id}->{next_task.task_id}",
        from_task_id=task.task_id,
        to_task_id=next_task.task_id,
        from_subsystem=subsystem_name,
        to_subsystem=next_task.owner_subsystem,
        status=result.status,
        rationale=result.rationale,
        produced_artifact_ids=produced_artifact_ids,
        evidence_ids=evidence_ids,
        next_task_input_keys=tuple(sorted(next_task.inputs.keys())),
        next_task_allowed_tools=next_task.allowed_tools,
        next_task_expected_artifacts=next_task.expected_artifacts,
        next_task_acceptance_gate=next_task.acceptance_gate,
        failure_classification=result.failure_classification,
    )


def _is_transient_subsystem_exception(exc: Exception) -> bool:
    name = type(exc).__name__.lower()
    module = type(exc).__module__.lower()
    text = str(exc).lower()
    haystack = f"{module}.{name} {text}"
    if name == "apitimeouterror" and (
        module.startswith("anthropic") or module.startswith("openai")
    ):
        return True
    if "timeout" in haystack or "timed out" in haystack:
        return False
    retry_markers = (
        "apiconnectionerror",
        "api_connection_error",
        "ratelimiterror",
        "rate_limit_error",
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
