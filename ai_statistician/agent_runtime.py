from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
from copy import deepcopy
from dataclasses import asdict, dataclass, field, replace
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

RUNTIME_OUTER_GRAPH_BUDGET_SCOPE = "outer_research_graph"
RUNTIME_SAME_OWNER_WORKSPACE_BUDGET_SCOPE = "same_owner_workspace"
RUNTIME_CONTINUATION_BUDGET_MARKER_KEY = "runtime_same_owner_workspace_continuation"


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


def mark_same_owner_workspace_continuation(
    *,
    parent_task: AgentTask,
    next_task: AgentTask,
) -> AgentTask:
    """Mark one exact same-owner checkpoint without spending graph budget."""

    if next_task.owner_subsystem != parent_task.owner_subsystem:
        raise ValueError("same-owner workspace continuation cannot change owner")
    budget = deepcopy(dict(next_task.budget))
    budget[RUNTIME_CONTINUATION_BUDGET_MARKER_KEY] = {
        "scope": RUNTIME_SAME_OWNER_WORKSPACE_BUDGET_SCOPE,
        "parent_task_id": parent_task.task_id,
        "next_task_id": next_task.task_id,
        "owner_subsystem": next_task.owner_subsystem,
    }
    return replace(next_task, budget=budget)


def _runtime_iteration_budget_scope(task: AgentTask, result: AgentStepResult) -> str:
    next_task = result.next_task
    if (
        result.status != "REVISE"
        or next_task is None
        or next_task.owner_subsystem != task.owner_subsystem
    ):
        return RUNTIME_OUTER_GRAPH_BUDGET_SCOPE
    marker = next_task.budget.get(RUNTIME_CONTINUATION_BUDGET_MARKER_KEY, {})
    if not isinstance(marker, Mapping):
        return RUNTIME_OUTER_GRAPH_BUDGET_SCOPE
    if marker != {
        "scope": RUNTIME_SAME_OWNER_WORKSPACE_BUDGET_SCOPE,
        "parent_task_id": task.task_id,
        "next_task_id": next_task.task_id,
        "owner_subsystem": next_task.owner_subsystem,
    }:
        return RUNTIME_OUTER_GRAPH_BUDGET_SCOPE
    return RUNTIME_SAME_OWNER_WORKSPACE_BUDGET_SCOPE


class RuntimeArtifactReferenceError(ValueError):
    """A task-bound artifact reference is missing, stale, or cyclic."""


def runtime_artifact_reference(
    artifact_id: str,
    artifact: Any,
) -> dict[str, Any]:
    """Reference one authoritative blackboard artifact without copying it."""

    normalized_id = str(artifact_id or "").strip()
    if not normalized_id:
        raise ValueError("runtime artifact reference requires an artifact_id")
    return {
        "artifact_kind": "RuntimeArtifactRef",
        "reference_scope": "runtime_blackboard",
        "artifact_id": normalized_id,
        "content_hash": stable_hash(artifact),
        "payload_kind": (
            str(artifact.get("artifact_kind", "") or "")
            if isinstance(artifact, Mapping)
            else ""
        ),
        "evidence_status": "REFERENCE_ONLY_NOT_EVIDENCE",
    }


def _resolve_runtime_artifact_references(
    value: Any,
    artifacts: Mapping[str, Any],
    *,
    bindings: dict[str, dict[str, Any]] | None = None,
) -> Any:
    active: set[str] = set()

    def resolve(child: Any) -> Any:
        if isinstance(child, Mapping):
            if (
                child.get("artifact_kind") == "RuntimeArtifactRef"
                and child.get("reference_scope") == "runtime_blackboard"
            ):
                artifact_id = str(child.get("artifact_id", "") or "").strip()
                expected_hash = str(child.get("content_hash", "") or "").strip()
                if not artifact_id or not expected_hash:
                    raise RuntimeArtifactReferenceError(
                        "runtime artifact reference is missing identity or hash"
                    )
                if artifact_id in active:
                    raise RuntimeArtifactReferenceError(
                        "cyclic runtime artifact reference"
                    )
                artifact = artifacts.get(artifact_id)
                if artifact is None or stable_hash(artifact) != expected_hash:
                    raise RuntimeArtifactReferenceError(
                        f"runtime artifact reference unavailable or stale: {artifact_id}"
                    )
                payload_kind = str(child.get("payload_kind", "") or "")
                if (
                    payload_kind
                    and isinstance(artifact, Mapping)
                    and str(artifact.get("artifact_kind", "") or "")
                    != payload_kind
                ):
                    raise RuntimeArtifactReferenceError(
                        f"runtime artifact reference kind mismatch: {artifact_id}"
                    )
                active.add(artifact_id)
                try:
                    resolved_artifact = resolve(deepcopy(artifact))
                finally:
                    active.remove(artifact_id)
                if bindings is not None:
                    bindings.setdefault(
                        stable_hash(resolved_artifact),
                        deepcopy(dict(child)),
                    )
                return resolved_artifact
            return {str(key): resolve(item) for key, item in child.items()}
        if isinstance(child, list):
            return [resolve(item) for item in child]
        if isinstance(child, tuple):
            return tuple(resolve(item) for item in child)
        return deepcopy(child)

    return resolve(value)


def resolve_runtime_artifact_references(
    value: Any,
    artifacts: Mapping[str, Any],
) -> Any:
    """Resolve explicit refs for a subsystem-owned restored task."""

    return _resolve_runtime_artifact_references(value, artifacts)


def _reapply_runtime_artifact_references(
    value: Any,
    bindings: Mapping[str, Mapping[str, Any]],
) -> Any:
    """Preserve existing refs when a subsystem forwards an unchanged payload."""

    def compact(child: Any) -> Any:
        if isinstance(child, Mapping):
            if child.get("artifact_kind") == "RuntimeArtifactRef":
                return deepcopy(dict(child))
            reference = bindings.get(stable_hash(dict(child)))
            if isinstance(reference, Mapping):
                return deepcopy(dict(reference))
            return {str(key): compact(item) for key, item in child.items()}
        if isinstance(child, list):
            return [compact(item) for item in child]
        if isinstance(child, tuple):
            return tuple(compact(item) for item in child)
        return deepcopy(child)

    return compact(value)


def compact_runtime_artifact_references(
    value: Any,
    artifacts: Mapping[str, Any],
    *,
    artifact_kinds: frozenset[str] | None = None,
) -> Any:
    """Replace exact authoritative payload copies with existing artifact refs."""

    candidate_kinds = set(artifact_kinds or ())
    if artifact_kinds is None:
        def collect_kinds(child: Any) -> None:
            if isinstance(child, Mapping):
                artifact_kind = str(child.get("artifact_kind", "") or "")
                if artifact_kind and artifact_kind != "RuntimeArtifactRef":
                    candidate_kinds.add(artifact_kind)
                for item in child.values():
                    collect_kinds(item)
            elif isinstance(child, (list, tuple)):
                for item in child:
                    collect_kinds(item)

        collect_kinds(value)
    if not candidate_kinds:
        return deepcopy(value)
    bindings: dict[str, dict[str, Any]] = {}
    for raw_artifact_id, artifact in sorted(
        artifacts.items(),
        key=lambda item: str(item[0]),
    ):
        if not isinstance(artifact, Mapping):
            continue
        if str(
            artifact.get("artifact_kind", "") or ""
        ) not in candidate_kinds:
            continue
        try:
            resolved = _resolve_runtime_artifact_references(artifact, artifacts)
        except RuntimeArtifactReferenceError:
            continue
        bindings.setdefault(
            stable_hash(resolved),
            runtime_artifact_reference(str(raw_artifact_id), artifact),
        )
    return _reapply_runtime_artifact_references(value, bindings)


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
            if artifact_kind == "RuntimeArtifactRef":
                hydrated_inputs[str(key)] = _resolve_runtime_artifact_references(
                    value,
                    artifacts,
                )
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


def restore_agent_task_continuation_reference(
    reference: Mapping[str, Any],
    artifacts: Mapping[str, Any],
) -> AgentTask:
    """Resolve and verify one compact continuation reference."""

    continuation_id = str(reference.get("continuation_id", "") or "").strip()
    continuation = artifacts.get(continuation_id, {})
    if (
        reference.get("artifact_kind") != "RuntimeAgentTaskContinuationRef"
        or not continuation_id
        or not isinstance(continuation, Mapping)
        or stable_hash(dict(continuation))
        != str(reference.get("continuation_hash", "") or "")
        or continuation.get("task_ref") != reference.get("task_ref")
    ):
        raise RuntimeArtifactReferenceError(
            "runtime task continuation reference mismatch"
        )
    task = restore_agent_task_continuation(continuation, artifacts)
    if agent_task_reference(task) != reference.get("task_ref"):
        raise RuntimeArtifactReferenceError(
            "restored runtime task continuation identity mismatch"
        )
    return task


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


PERSISTED_TOOL_CALL_SUMMARY_CHAR_LIMIT = 16_000
_PERSISTED_TOOL_CALL_TRUNCATION_MARKER = (
    "\n...[persisted trace summary truncated; exact value is hash-bound]...\n"
)


def persisted_tool_call_projection(call: ToolCallRecord) -> dict[str, Any]:
    """Bound duplicate trace text while preserving exact identity and locations."""

    row = asdict(call)
    has_external_output = bool(call.output_paths and call.output_hash)
    for field_name in ("stdout_summary", "stderr_summary"):
        exact = str(row.get(field_name, "") or "")
        truncated = bool(
            has_external_output
            and len(exact) > PERSISTED_TOOL_CALL_SUMMARY_CHAR_LIMIT
        )
        if truncated:
            available = max(
                0,
                PERSISTED_TOOL_CALL_SUMMARY_CHAR_LIMIT
                - len(_PERSISTED_TOOL_CALL_TRUNCATION_MARKER),
            )
            head = available // 2
            tail = available - head
            exact_tail = exact[-tail:] if tail else ""
            row[field_name] = (
                exact[:head]
                + _PERSISTED_TOOL_CALL_TRUNCATION_MARKER
                + exact_tail
            )
        row[f"{field_name}_hash"] = stable_hash(exact)
        row[f"{field_name}_characters"] = len(exact)
        row[f"{field_name}_bytes"] = len(exact.encode("utf-8"))
        row[f"{field_name}_truncated"] = truncated
    row["summary_payload_policy"] = (
        "bounded_trace_projection"
        if has_external_output
        else "inline_exact_without_external_output"
    )
    return row


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
    iteration_budget_scope: str = RUNTIME_OUTER_GRAPH_BUDGET_SCOPE
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
            "iteration_budget_scope": self.iteration_budget_scope,
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
        row["tool_calls"] = [
            asdict(call)
            if include_task_payloads
            else persisted_tool_call_projection(call)
            for call in self.tool_calls
        ]
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
    pending_task: AgentTask | None = None
    pending_task_continuation_ref: dict[str, Any] = field(default_factory=dict)
    pending_task_checkpoint_reason: str = ""
    outer_graph_iterations_consumed: int = 0
    same_owner_workspace_continuations_consumed: int = 0

    def to_json(self, *, include_task_payloads: bool = False) -> dict[str, Any]:
        return {
            "status": self.status,
            "final_task_id": self.final_task_id,
            "pending_task": (
                asdict(self.pending_task)
                if include_task_payloads and self.pending_task is not None
                else agent_task_reference(self.pending_task)
            ),
            "pending_task_continuation_ref": deepcopy(
                self.pending_task_continuation_ref
            ),
            "pending_task_checkpoint_reason": self.pending_task_checkpoint_reason,
            "runtime_steps_executed": len(self.traces),
            "outer_graph_iterations_consumed": self.outer_graph_iterations_consumed,
            "same_owner_workspace_continuations_consumed": self.same_owner_workspace_continuations_consumed,
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
        progress_callback: Callable[[dict[str, Any]], None] | None = None,
    ) -> AgentRuntimeResult:
        task = deepcopy(initial_task)
        traces: list[RuntimeIterationTrace] = []
        final_status: RuntimeStatus = "MAX_ITERATIONS_REACHED"
        outer_graph_iterations_consumed = 0
        same_owner_workspace_continuations_consumed = 0
        iteration = 0
        budget_exhaustion_reason = (
            "outer_iteration_budget_exhausted" if max_iterations < 1 else ""
        )

        while not budget_exhaustion_reason:
            iteration += 1
            subsystem = self.subsystems.get(task.owner_subsystem)
            execution_task = task
            task_artifact_bindings: dict[str, dict[str, Any]] = {}
            self.blackboard.task_history.append(task.task_id)
            _emit_progress(
                progress_callback,
                event_type="subsystem_start",
                iteration=iteration,
                task=task,
                subsystem=task.owner_subsystem if subsystem is None else getattr(subsystem, "name", task.owner_subsystem),
            )
            if subsystem is None:
                outer_graph_iterations_consumed += 1
                trace = RuntimeIterationTrace(
                    iteration=iteration,
                    task=task,
                    subsystem=task.owner_subsystem,
                    status="BLOCKED",
                    rationale=f"no registered subsystem: {task.owner_subsystem}",
                    iteration_budget_scope=RUNTIME_OUTER_GRAPH_BUDGET_SCOPE,
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

            progress_token = _ACTIVE_PROGRESS_CONTEXT.set(
                {
                    "progress_callback": progress_callback,
                    "iteration": iteration,
                    "task": task,
                    "subsystem": getattr(subsystem, "name", task.owner_subsystem),
                }
            )
            try:
                execution_inputs = _resolve_runtime_artifact_references(
                    task.inputs,
                    self.blackboard.artifacts,
                    bindings=task_artifact_bindings,
                )
                execution_task = replace(task, inputs=execution_inputs)
                result = subsystem.run(execution_task, self.blackboard)
            except Exception as exc:  # pragma: no cover - defensive runtime boundary
                artifact_reference_failure = isinstance(
                    exc, RuntimeArtifactReferenceError
                )
                failure_classification = (
                    "task_artifact_reference_invalid"
                    if artifact_reference_failure
                    else "subsystem_exception"
                )
                rationale = (
                    f"task artifact reference invalid: {exc}"
                    if artifact_reference_failure
                    else f"subsystem raised {exc.__class__.__name__}: {exc}"
                )
                result = AgentStepResult(
                    status="FAILED",
                    rationale=rationale,
                    observations=(
                        EnvironmentObservation(
                            observation_type=failure_classification,
                            summary=str(exc),
                            payload={
                                "exception_type": exc.__class__.__name__,
                                "exception_module": exc.__class__.__module__,
                                **_exception_debug_payload(exc),
                                "automatic_subsystem_restart": False,
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
            finally:
                _ACTIVE_PROGRESS_CONTEXT.reset(progress_token)

            subsystem_name = getattr(subsystem, "name", task.owner_subsystem)
            if self.handoff_policy is not None:
                result = self.handoff_policy(
                    iteration=iteration,
                    task=execution_task,
                    subsystem_name=subsystem_name,
                    result=result,
                    blackboard=self.blackboard,
                )

            if result.next_task is not None:
                next_inputs = result.next_task.inputs
                if task_artifact_bindings:
                    next_inputs = _reapply_runtime_artifact_references(
                        next_inputs,
                        task_artifact_bindings,
                    )
                result = replace(
                    result,
                    next_task=replace(
                        result.next_task,
                        inputs=compact_runtime_artifact_references(
                            next_inputs,
                            {
                                **self.blackboard.artifacts,
                                **result.produced_artifacts,
                            },
                        ),
                    ),
                )

            result = _snapshot_agent_step_result(result)
            iteration_budget_scope = _runtime_iteration_budget_scope(task, result)
            if iteration_budget_scope == RUNTIME_SAME_OWNER_WORKSPACE_BUDGET_SCOPE:
                same_owner_workspace_continuations_consumed += 1
            else:
                outer_graph_iterations_consumed += 1
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
                iteration_budget_scope=iteration_budget_scope,
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
                metadata={
                    "iteration_budget_scope": iteration_budget_scope,
                    "outer_graph_iterations_consumed": outer_graph_iterations_consumed,
                    "same_owner_workspace_continuations_consumed": same_owner_workspace_continuations_consumed,
                },
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
            if (
                iteration_budget_scope
                == RUNTIME_SAME_OWNER_WORKSPACE_BUDGET_SCOPE
                and same_owner_workspace_continuations_consumed
                >= max_iterations
            ):
                final_status = "MAX_ITERATIONS_REACHED"
                budget_exhaustion_reason = "same_owner_workspace_continuation_budget_exhausted"
                break
            if (
                iteration_budget_scope == RUNTIME_OUTER_GRAPH_BUDGET_SCOPE
                and outer_graph_iterations_consumed >= max_iterations
            ):
                final_status = "MAX_ITERATIONS_REACHED"
                budget_exhaustion_reason = "outer_iteration_budget_exhausted"
                break

        terminal_failure_classification = (
            traces[-1].failure_classification if traces else ""
        )
        pending_task_checkpoint_reason = ""
        if final_status == "MAX_ITERATIONS_REACHED":
            pending_task_checkpoint_reason = (
                budget_exhaustion_reason or "outer_iteration_budget_exhausted"
            )
        elif (
            final_status == "FAILED"
            and terminal_failure_classification == "subsystem_exception"
        ):
            pending_task_checkpoint_reason = "terminal_subsystem_error"
        pending_task = (
            deepcopy(task) if pending_task_checkpoint_reason else None
        )
        pending_task_continuation_ref: dict[str, Any] = {}
        if pending_task is not None:
            (
                _continuation_id,
                continuation,
                continuation_artifacts,
            ) = materialize_agent_task_continuation(pending_task)
            self.blackboard.artifacts.update(continuation_artifacts)
            pending_task_continuation_ref = agent_task_continuation_reference(
                continuation
            )

        return AgentRuntimeResult(
            status=final_status,
            final_task_id=task.task_id,
            blackboard=self.blackboard,
            traces=tuple(traces),
            pending_task=pending_task,
            pending_task_continuation_ref=pending_task_continuation_ref,
            pending_task_checkpoint_reason=pending_task_checkpoint_reason,
            outer_graph_iterations_consumed=outer_graph_iterations_consumed,
            same_owner_workspace_continuations_consumed=same_owner_workspace_continuations_consumed,
        )


@contextmanager
def agent_runtime_substage(
    substage: str,
    *,
    metadata: Mapping[str, Any] | None = None,
) -> Iterator[dict[str, Any]]:
    """Expose work inside a subsystem through its existing progress callback."""

    context = _ACTIVE_PROGRESS_CONTEXT.get()
    if not context:
        yield dict(metadata or {})
        return
    callback = context.get("progress_callback")
    task = context.get("task")
    if not callable(callback) or not isinstance(task, AgentTask):
        yield dict(metadata or {})
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
        yield details
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
