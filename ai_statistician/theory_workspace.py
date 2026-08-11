from __future__ import annotations

import json
from copy import deepcopy
from dataclasses import dataclass
from typing import Any, Callable, Mapping, Sequence

from .client_tool_loop import (
    ClientToolExecutionResult,
    ClientToolInputError,
    ClientToolLoopError,
    run_bounded_client_tool_loop,
)
from .fingerprint import stable_hash
from .model_backend import ClientToolDefinition, ClientToolTurnRequest
from .structured_output_retry import PacketValidationError


THEORY_WORKSPACE_CHECKPOINT_KIND = "TheoryDeveloperWorkspaceCheckpoint"
TheoryWorkspaceCandidateBuilder = Callable[
    [Mapping[str, Any], tuple[str, ...]],
    Mapping[str, Any],
]
TheoryWorkspaceCandidateValidator = Callable[[Mapping[str, Any]], Sequence[str]]


@dataclass(frozen=True)
class TheoryWorkspaceResult:
    core_packet: Mapping[str, Any]
    evidence: Mapping[str, Any]


def run_theory_artifact_workspace(
    *,
    provider: Any,
    system_prompt: str,
    user_prompt: str,
    model: str,
    model_tier: str,
    temperature: float,
    max_tokens: int,
    max_turns: int,
    max_reads: int,
    max_submissions: int,
    max_no_progress_turns: int,
    workspace_id: str,
    question_id: str,
    authoring_binding_id: str,
    workspace_operation: str,
    initial_artifacts: Mapping[str, Any],
    read_only_artifacts: Mapping[str, Any] | None = None,
    build_candidate: TheoryWorkspaceCandidateBuilder,
    validate_candidate: TheoryWorkspaceCandidateValidator,
    request_metadata: Mapping[str, Any] | None = None,
) -> TheoryWorkspaceResult:
    """Let one model author authoritative theory artifacts in place."""

    if not all(
        str(value).strip()
        for value in (
            workspace_id,
            question_id,
            authoring_binding_id,
            workspace_operation,
        )
    ):
        raise ValueError(
            "theory workspace requires workspace, question, authoring, and "
            "operation identity"
        )
    for value, label in (
        (max_turns, "turn"),
        (max_reads, "read"),
        (max_submissions, "submission"),
        (max_no_progress_turns, "no-progress"),
    ):
        if value < 1:
            raise ValueError(f"theory workspace {label} budget must be positive")

    parent = {
        str(name): deepcopy(value)
        for name, value in initial_artifacts.items()
        if str(name).strip()
    }
    if not parent:
        raise ValueError("theory workspace requires initial artifacts")
    read_only = {
        str(name): deepcopy(value)
        for name, value in (read_only_artifacts or {}).items()
        if str(name).strip()
    }
    overlapping_names = sorted(set(parent).intersection(read_only))
    if overlapping_names:
        raise ValueError(
            "theory workspace read-only names overlap writable artifacts: "
            + ", ".join(overlapping_names)
        )
    parent_hash = stable_hash(parent)
    artifact_names = tuple(sorted({*parent, *read_only}))
    writable_artifact_names = tuple(sorted(parent))
    parent_shapes = {
        name: _artifact_shape(value) for name, value in parent.items()
    }
    state: dict[str, Any] = {
        "artifacts": deepcopy(parent),
        "reads": 0,
        "submissions": 0,
        "last_validation_errors": [],
        "last_candidate": {},
    }
    tools = _theory_workspace_tools(
        artifact_names,
        parent_shapes,
    )

    def changed_artifact_names(artifacts: Mapping[str, Any]) -> tuple[str, ...]:
        return tuple(
            name
            for name in writable_artifact_names
            if stable_hash(artifacts[name]) != stable_hash(parent[name])
        )

    def readable_artifact(name: str) -> Any:
        if name in read_only:
            return read_only[name]
        return state["artifacts"][name]

    def execute_tool(call, context):
        del context
        tool_input = dict(call.input)
        if call.name == "read_theory_workspace":
            if state["reads"] >= max_reads:
                raise ClientToolInputError("theory workspace read budget is exhausted")
            requested = tool_input.get("artifact_names", [])
            if (
                not isinstance(requested, Sequence)
                or isinstance(requested, (str, bytes))
                or not requested
            ):
                raise ClientToolInputError(
                    "read_theory_workspace requires a nonempty artifact_names array"
                )
            names = [str(name) for name in requested]
            if len(names) != len(set(names)):
                raise ClientToolInputError("theory workspace read names must be unique")
            unknown = sorted(set(names) - set(artifact_names))
            if unknown:
                raise ClientToolInputError(
                    "unknown theory workspace artifacts: " + ", ".join(unknown)
                )
            selected = {
                name: deepcopy(readable_artifact(name)) for name in names
            }
            if len(_compact_json(selected)) > 55_000:
                raise ClientToolInputError(
                    "selected theory artifacts exceed one observation; read fewer artifacts"
                )
            state["reads"] += 1
            return ClientToolExecutionResult(
                content={
                    "ok": True,
                    "artifacts": selected,
                    "artifact_hashes": {
                        name: stable_hash(selected[name]) for name in names
                    },
                    "reads": state["reads"],
                    "remaining_reads": max_reads - state["reads"],
                    "proof_evidence_status": (
                        "THEORY_WORKSPACE_READ_NOT_PROOF_EVIDENCE"
                    ),
                },
                observation_key="theory-workspace-read:"
                + stable_hash(
                    [
                        workspace_id,
                        [(name, stable_hash(selected[name])) for name in names],
                    ]
                ),
            )

        if call.name == "submit_theory_artifacts":
            if state["submissions"] >= max_submissions:
                raise ClientToolInputError(
                    "theory workspace submission budget is exhausted"
                )
            if not tool_input:
                raise ClientToolInputError(
                    "submit_theory_artifacts requires at least one "
                    "artifact-name field"
                )
            candidate_artifacts = deepcopy(dict(state["artifacts"]))
            for raw_name, raw_artifact in tool_input.items():
                name = str(raw_name or "")
                if name not in parent:
                    raise ClientToolInputError(
                        f"unknown theory workspace artifact: {name}"
                    )
                artifact = deepcopy(raw_artifact)
                if _artifact_shape(artifact) != parent_shapes[name]:
                    raise ClientToolInputError(
                        f"theory artifact {name} must remain {parent_shapes[name]}"
                    )
                candidate_artifacts[name] = artifact

            state["submissions"] += 1
            state_changed = stable_hash(candidate_artifacts) != stable_hash(
                state["artifacts"]
            )
            state["artifacts"] = candidate_artifacts
            changed = changed_artifact_names(candidate_artifacts)
            if not changed:
                errors = [
                    "the submitted theory workspace is unchanged from its parent"
                ]
                candidate: dict[str, Any] = {}
            else:
                raw_candidate = build_candidate(candidate_artifacts, changed)
                if not isinstance(raw_candidate, Mapping):
                    raise ClientToolInputError(
                        "theory workspace candidate builder returned a non-object"
                    )
                candidate = deepcopy(dict(raw_candidate))
                errors = [
                    str(error)
                    for error in validate_candidate(candidate)
                    if str(error).strip()
                ]
            state["last_candidate"] = candidate
            state["last_validation_errors"] = errors
            candidate_hash = stable_hash(candidate) if candidate else ""
            if errors:
                remaining_submissions = max_submissions - state["submissions"]
                content = {
                    "ok": True,
                    "write_accepted": True,
                    "state_changed": state_changed,
                    "workspace_valid": False,
                    "validation_errors": errors,
                    "candidate_hash": candidate_hash,
                    "changed_artifact_names": list(changed),
                    "omitted_artifacts_retained": True,
                    "submissions": state["submissions"],
                    "remaining_submissions": remaining_submissions,
                    "runtime_edited_theory": False,
                    "proof_evidence_status": (
                        "THEORY_WORKSPACE_VALIDATION_NOT_PROOF_EVIDENCE"
                    ),
                }
                return ClientToolExecutionResult(
                    content=content,
                    state_changed=state_changed,
                    terminal=remaining_submissions == 0,
                    terminal_payload=(
                        {
                            "core_packet": candidate,
                            "core_packet_hash": candidate_hash,
                            "workspace_hash": stable_hash(candidate_artifacts),
                            "changed_artifact_names": list(changed),
                            "workspace_valid": False,
                            "validation_errors": list(errors),
                        }
                        if remaining_submissions == 0
                        else None
                    ),
                    observation_key="theory-workspace-validation:"
                    + stable_hash([candidate_hash, errors]),
                )
            return ClientToolExecutionResult(
                content={
                    "ok": True,
                    "candidate_hash": candidate_hash,
                    "changed_artifact_names": list(changed),
                    "submissions": state["submissions"],
                    "remaining_submissions": max_submissions - state["submissions"],
                    "runtime_edited_theory": False,
                    "proof_evidence_status": (
                        "THEORY_WORKSPACE_SUBMISSION_NOT_PROOF_EVIDENCE"
                    ),
                },
                state_changed=state_changed,
                terminal=True,
                terminal_payload={
                    "core_packet": candidate,
                    "core_packet_hash": candidate_hash,
                    "workspace_hash": stable_hash(candidate_artifacts),
                    "changed_artifact_names": list(changed),
                },
                observation_key="theory-workspace-accepted:" + candidate_hash,
            )

        raise ClientToolInputError("unsupported theory workspace tool")

    catalog = {
        name: {
            "shape": _artifact_shape(readable_artifact(name)),
            "content_hash": stable_hash(readable_artifact(name)),
            "byte_size": len(
                _compact_json(readable_artifact(name)).encode("utf-8")
            ),
            "writable": name in parent,
        }
        for name in artifact_names
    }
    request = ClientToolTurnRequest(
        system_prompt=system_prompt,
        messages=(
            {
                "role": "user",
                "content": (
                    user_prompt
                    + "\n\nAuthoritative theory workspace catalog:\n"
                    + _compact_json(catalog)
                    + "\n\nRead the artifacts needed for mathematical judgment. "
                    "Submit complete replacements only for artifacts you choose to "
                    "change; read-only observations cannot be replaced and all omitted "
                    "writable artifacts retain their exact current bytes. Each "
                    "structurally valid replacement write is retained even when the "
                    "combined workspace still fails validation, so a validator "
                    "observation is not a rollback and later calls should contain only "
                    "artifacts that still need to be added or revised. "
                    "The runtime stores your replacements unchanged and returns "
                    "validator observations to this same model context."
                ),
            },
        ),
        tools=tools,
        model=model,
        max_tokens=max_tokens,
        temperature=temperature,
        tool_choice="any",
        disable_parallel_tool_use=True,
        metadata={
            **dict(request_metadata or {}),
            "model_tier": model_tier,
            "workspace_id": workspace_id,
            "question_id": question_id,
            "authoring_binding_id": authoring_binding_id,
            "workspace_operation": workspace_operation,
            "parent_workspace_hash": parent_hash,
        },
    )

    def select_tools(_turn_index, available_tools):
        enabled = {
            "read_theory_workspace": state["reads"] < max_reads,
            "submit_theory_artifacts": (
                state["submissions"] < max_submissions
            ),
        }
        selected = tuple(tool for tool in available_tools if enabled[tool.name])
        return selected or tuple(
            tool
            for tool in available_tools
            if tool.name == "submit_theory_artifacts"
        )

    def recovery_checkpoint() -> dict[str, Any]:
        current_artifacts = deepcopy(dict(state["artifacts"]))
        return {
            "schema_version": 1,
            "artifact_kind": THEORY_WORKSPACE_CHECKPOINT_KIND,
            "workspace_id": workspace_id,
            "question_id": question_id,
            "authoring_binding_id": authoring_binding_id,
            "workspace_operation": workspace_operation,
            "parent_workspace_hash": parent_hash,
            "current_workspace_hash": stable_hash(current_artifacts),
            "current_artifacts": current_artifacts,
            "changed_artifact_names": list(
                changed_artifact_names(current_artifacts)
            ),
            "reads": state["reads"],
            "submissions": state["submissions"],
            "last_validation_errors": list(state["last_validation_errors"]),
            "model_owned_theory": True,
            "runtime_edited_theory": False,
            "proof_evidence_status": (
                "THEORY_WORKSPACE_CHECKPOINT_NOT_PROOF_EVIDENCE"
            ),
            "kernel_verified": False,
        }

    try:
        loop = run_bounded_client_tool_loop(
            backend=provider,
            request=request,
            execute_tool=execute_tool,
            max_turns=max_turns,
            max_tool_calls=max(max_turns, max_reads + max_submissions),
            max_no_progress_turns=max_no_progress_turns,
            select_tools=select_tools,
        )
    except ClientToolLoopError as exc:
        raise PacketValidationError(
            validation_label="LLM TheoryDeveloper artifact workspace",
            attempts=exc.turns,
            errors=list(
                dict.fromkeys(
                    [exc.reason, *state["last_validation_errors"]]
                )
            ),
            history=[deepcopy(dict(row)) for row in exc.history],
            last_invalid_packet=(
                deepcopy(dict(state["last_candidate"]))
                if state["last_candidate"]
                else None
            ),
            recovery_checkpoint=recovery_checkpoint(),
        ) from exc

    terminal = dict(loop.terminal_payload)
    core_packet = terminal.get("core_packet", {})
    if not isinstance(core_packet, Mapping):
        raise PacketValidationError(
            validation_label="LLM TheoryDeveloper artifact workspace",
            attempts=loop.turns,
            errors=["terminal theory workspace packet is not an object"],
            history=[deepcopy(dict(row)) for row in loop.history],
        )
    packet = deepcopy(dict(core_packet))
    packet_hash = stable_hash(packet)
    terminal_errors = [
        str(error)
        for error in validate_candidate(packet)
        if str(error).strip()
    ]
    terminal_errors = list(
        dict.fromkeys(
            [
                *[
                    str(error)
                    for error in terminal.get("validation_errors", []) or []
                    if str(error).strip()
                ],
                *terminal_errors,
            ]
        )
    )
    if terminal.get("core_packet_hash") != packet_hash or terminal_errors:
        raise PacketValidationError(
            validation_label="LLM TheoryDeveloper artifact workspace",
            attempts=loop.turns,
            errors=(
                terminal_errors
                or ["terminal theory workspace packet hash does not match"]
            ),
            history=[deepcopy(dict(row)) for row in loop.history],
            last_invalid_packet=packet,
            recovery_checkpoint=recovery_checkpoint(),
        )

    evidence_id = "theory_workspace:" + stable_hash(
        [
            workspace_id,
            workspace_operation,
            parent_hash,
            packet_hash,
            loop.transcript_fingerprint,
        ]
    )[:20]
    evidence = {
        "schema_version": 1,
        "artifact_kind": "TheoryDeveloperWorkspaceEvidence",
        "artifact_id": evidence_id,
        "workspace_id": workspace_id,
        "question_id": question_id,
        "authoring_binding_id": authoring_binding_id,
        "workspace_operation": workspace_operation,
        "transport": "native_client_tools",
        "parent_workspace_hash": parent_hash,
        "submitted_workspace_hash": str(terminal.get("workspace_hash", "") or ""),
        "submitted_core_packet_hash": packet_hash,
        "read_only_artifact_hashes": {
            name: stable_hash(value) for name, value in sorted(read_only.items())
        },
        "changed_artifact_names": list(
            terminal.get("changed_artifact_names", []) or []
        ),
        "reads": state["reads"],
        "submissions": state["submissions"],
        "turns": loop.turns,
        "tool_calls": loop.tool_calls,
        "runtime_executed_tool_calls": loop.runtime_executed_tool_calls,
        "provider": loop.provider,
        "model": loop.model,
        "model_tier": model_tier,
        "provider_usage": dict(loop.provider_usage),
        "history": [deepcopy(dict(row)) for row in loop.history],
        "transcript_fingerprint": loop.transcript_fingerprint,
        "model_owned_theory": True,
        "runtime_edited_theory": False,
        "accepted": True,
        "proof_evidence_status": "THEORY_WORKSPACE_NOT_PROOF_EVIDENCE",
        "kernel_verified": False,
    }
    return TheoryWorkspaceResult(core_packet=packet, evidence=evidence)


def _theory_workspace_tools(
    artifact_names: Sequence[str],
    writable_artifact_shapes: Mapping[str, str],
) -> tuple[ClientToolDefinition, ...]:
    name_schema = {"type": "string", "enum": list(artifact_names)}
    replacement_properties = {
        name: _artifact_shape_schema(shape)
        for name, shape in sorted(writable_artifact_shapes.items())
    }
    return (
        ClientToolDefinition(
            name="read_theory_workspace",
            description=(
                "Read the exact current contents of one or more named theory "
                "workspace artifacts before deciding what to revise."
            ),
            input_schema={
                "type": "object",
                "additionalProperties": False,
                "required": ["artifact_names"],
                "properties": {
                    "artifact_names": {
                        "type": "array",
                        "minItems": 1,
                        "uniqueItems": True,
                        "items": name_schema,
                    }
                },
            },
        ),
        ClientToolDefinition(
            name="submit_theory_artifacts",
            description=(
                "Submit a flat object whose keys are the theory artifacts to change "
                "and whose values are their complete model-authored replacements. "
                "Object-valued artifacts require objects and array-valued artifacts "
                "require arrays. Do not add a replacements wrapper and do not JSON-encode "
                "an artifact as a string. Every accepted replacement is retained even "
                "if the combined workspace still fails validation. On later calls, "
                "omit retained artifacts unless you intend to revise them."
            ),
            input_schema={
                "type": "object",
                "additionalProperties": False,
                "minProperties": 1,
                "properties": replacement_properties,
            },
            terminal=True,
        ),
    )


def _artifact_shape_schema(shape: str) -> dict[str, Any]:
    if shape == "object":
        return {"type": "object"}
    if shape == "array":
        return {"type": "array"}
    return {
        "type": ["string", "number", "integer", "boolean", "null"]
    }


def _artifact_shape(value: Any) -> str:
    if isinstance(value, Mapping):
        return "object"
    if isinstance(value, list):
        return "array"
    return "scalar"


def _compact_json(value: Any) -> str:
    return json.dumps(
        value,
        separators=(",", ":"),
        default=str,
        ensure_ascii=False,
    )
