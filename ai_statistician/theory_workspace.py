from __future__ import annotations

import json
from copy import deepcopy
from dataclasses import dataclass
from typing import Any, Callable, Mapping, Sequence

import jsonpatch

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
THEORY_WORKSPACE_JSON_PATCH_TRANSPORT = "rfc6902_json_patch"
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
        "model_edit_operations": [],
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

    def evaluate_model_write(
        candidate_artifacts: Mapping[str, Any],
        *,
        edit_operations: Sequence[Mapping[str, Any]] = (),
    ) -> ClientToolExecutionResult:
        state["submissions"] += 1
        state_changed = stable_hash(candidate_artifacts) != stable_hash(
            state["artifacts"]
        )
        state["artifacts"] = deepcopy(dict(candidate_artifacts))
        if state_changed and edit_operations:
            state["model_edit_operations"].extend(
                [
                    {
                        "submission_index": state["submissions"] - 1,
                        **deepcopy(dict(row)),
                    }
                    for row in edit_operations
                ]
            )
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
        remaining_submissions = max_submissions - state["submissions"]
        common_content = {
            "ok": True,
            "state_changed": state_changed,
            "candidate_hash": candidate_hash,
            "changed_artifact_names": list(changed),
            "submissions": state["submissions"],
            "remaining_submissions": remaining_submissions,
            "write_transport": THEORY_WORKSPACE_JSON_PATCH_TRANSPORT,
            "model_edit_operations_applied": len(edit_operations),
            "runtime_edited_theory": False,
        }
        if errors:
            content = {
                **common_content,
                "write_accepted": True,
                "workspace_valid": False,
                "validation_errors": errors,
                "omitted_artifacts_retained": True,
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
                **common_content,
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

        if call.name == "edit_theory_workspace":
            if state["submissions"] >= max_submissions:
                raise ClientToolInputError(
                    "theory workspace submission budget is exhausted"
                )
            candidate_artifacts, operation_records = (
                _apply_theory_workspace_json_patch(
                    state["artifacts"],
                    tool_input.get("operations"),
                    writable_artifact_shapes=parent_shapes,
                )
            )
            return evaluate_model_write(
                candidate_artifacts,
                edit_operations=operation_records,
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
    write_guidance = (
        "Use edit_theory_workspace to apply model-authored RFC 6902 add, "
        "remove, or replace operations to writable artifacts. Each path is "
        "an RFC 6901 JSON Pointer inside the named artifact; path '' addresses "
        "the artifact root and '/-' appends one element to an array. Preserve "
        "each artifact's catalog shape: populate an array with '/-' operations "
        "or replace its root with an array, never with a single object. Put every "
        "mutually dependent edit you already know into one atomic operations "
        "array. The runtime applies those exact operations without inventing "
        "content. "
    )
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
                    + write_guidance
                    + "Each structurally valid model write is retained even when the "
                    "combined workspace still fails validation, so a validator "
                    "observation is not a rollback and later calls should contain only "
                    "artifacts that still need to be added or revised. "
                    "The runtime returns "
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
        enable_prompt_caching=True,
        metadata={
            **dict(request_metadata or {}),
            "model_tier": model_tier,
            "workspace_id": workspace_id,
            "question_id": question_id,
            "authoring_binding_id": authoring_binding_id,
            "workspace_operation": workspace_operation,
            "write_transport": THEORY_WORKSPACE_JSON_PATCH_TRANSPORT,
            "parent_workspace_hash": parent_hash,
        },
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
            "write_transport": THEORY_WORKSPACE_JSON_PATCH_TRANSPORT,
            "parent_workspace_hash": parent_hash,
            "current_workspace_hash": stable_hash(current_artifacts),
            "current_artifacts": current_artifacts,
            "changed_artifact_names": list(
                changed_artifact_names(current_artifacts)
            ),
            "reads": state["reads"],
            "submissions": state["submissions"],
            "model_edit_operations": deepcopy(
                state["model_edit_operations"]
            ),
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
        "write_transport": THEORY_WORKSPACE_JSON_PATCH_TRANSPORT,
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
        "n_model_edit_operations": len(state["model_edit_operations"]),
        "model_edit_operations": deepcopy(
            state["model_edit_operations"]
        ),
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
    read_tool = ClientToolDefinition(
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
    )
    return (
        read_tool,
        ClientToolDefinition(
            name="edit_theory_workspace",
            description=(
                "Atomically apply model-authored RFC 6902 add, remove, or replace "
                "operations. artifact_name selects one writable JSON artifact and "
                "path is an RFC 6901 pointer inside it. Use an empty path to replace "
                "an artifact root or '/-' to append one element to an array. Every "
                "add or replace operation requires value; remove must omit value. "
                "The runtime applies these exact operations and does not infer edits."
            ),
            input_schema={
                "type": "object",
                "additionalProperties": False,
                "required": ["operations"],
                "properties": {
                    "operations": {
                        "type": "array",
                        "minItems": 1,
                        "items": {
                            "type": "object",
                            "additionalProperties": False,
                            "required": ["op", "artifact_name", "path"],
                            "properties": {
                                "op": {
                                    "type": "string",
                                    "enum": ["add", "remove", "replace"],
                                },
                                "artifact_name": {
                                    "type": "string",
                                    "enum": sorted(writable_artifact_shapes),
                                },
                                "path": {"type": "string"},
                                "value": {
                                    "type": [
                                        "object",
                                        "array",
                                        "string",
                                        "number",
                                        "boolean",
                                        "null",
                                    ]
                                },
                            },
                        },
                    }
                },
            },
            terminal=True,
        ),
    )


def _apply_theory_workspace_json_patch(
    current_artifacts: Mapping[str, Any],
    raw_operations: Any,
    *,
    writable_artifact_shapes: Mapping[str, str],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Apply model-authored RFC 6902 edits atomically to local candidates."""

    if not isinstance(raw_operations, list) or not raw_operations:
        raise ClientToolInputError(
            "edit_theory_workspace requires a nonempty operations array"
        )
    if len(raw_operations) > 64:
        raise ClientToolInputError(
            "edit_theory_workspace accepts at most 64 operations per atomic write"
        )
    candidate = deepcopy(dict(current_artifacts))
    records: list[dict[str, Any]] = []
    for index, raw_operation in enumerate(raw_operations):
        if not isinstance(raw_operation, Mapping):
            raise ClientToolInputError(
                f"theory edit operation {index} must be an object"
            )
        operation = dict(raw_operation)
        unexpected = sorted(
            set(operation) - {"op", "artifact_name", "path", "value"}
        )
        if unexpected:
            raise ClientToolInputError(
                f"theory edit operation {index} has unknown fields: "
                + ", ".join(unexpected)
            )
        op = str(operation.get("op", "") or "").strip()
        if op not in {"add", "remove", "replace"}:
            raise ClientToolInputError(
                f"theory edit operation {index} has unsupported op {op!r}"
            )
        artifact_name = str(
            operation.get("artifact_name", "") or ""
        ).strip()
        if artifact_name not in writable_artifact_shapes:
            raise ClientToolInputError(
                f"theory edit operation {index} names unknown writable artifact "
                f"{artifact_name!r}"
            )
        path = operation.get("path")
        if not isinstance(path, str):
            raise ClientToolInputError(
                f"theory edit operation {index} path must be a string"
            )
        has_value = "value" in operation
        if op in {"add", "replace"} and not has_value:
            raise ClientToolInputError(
                f"theory edit operation {index} {op} requires value"
            )
        if op == "remove" and has_value:
            raise ClientToolInputError(
                f"theory edit operation {index} remove must omit value"
            )
        patch_operation = {"op": op, "path": path}
        if has_value:
            patch_operation["value"] = deepcopy(operation["value"])
        try:
            candidate[artifact_name] = jsonpatch.apply_patch(
                candidate[artifact_name],
                [patch_operation],
                in_place=False,
            )
        except (jsonpatch.JsonPatchException, TypeError, ValueError) as exc:
            raise ClientToolInputError(
                f"theory edit operation {index} was rejected: {exc}"
            ) from exc
        expected_shape = writable_artifact_shapes[artifact_name]
        if _artifact_shape(candidate[artifact_name]) != expected_shape:
            raise ClientToolInputError(
                f"theory edit operation {index} changed {artifact_name} from "
                f"{expected_shape} to {_artifact_shape(candidate[artifact_name])}"
            )
        record = {
            "operation_index": index,
            "op": op,
            "artifact_name": artifact_name,
            "path": path,
        }
        if has_value:
            record["value_hash"] = stable_hash(operation["value"])
        records.append(record)
    return candidate, records


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
