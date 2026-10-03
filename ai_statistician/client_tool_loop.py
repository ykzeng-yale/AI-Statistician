from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from dataclasses import asdict, dataclass, field, replace
from pathlib import Path, PurePosixPath
from typing import Any, Callable, Generic, Mapping, Sequence, TypeVar

from .agent_runtime import agent_runtime_substage
from .cross_family_eval_protocol import withhold_confirmatory_evaluation_seed
from .fingerprint import stable_hash
from .model_backend import (
    ClientToolCall,
    ClientToolDefinition,
    ClientToolTurnRequest,
    ClientToolTurnResponse,
)


@dataclass(frozen=True)
class ClientToolExecutionContext:
    turn_index: int
    call_index: int
    calls_in_turn: int
    total_calls_before: int


@dataclass(frozen=True)
class ClientToolExecutionResult:
    """One caller-executed tool result returned to the same model context."""

    content: Any
    is_error: bool = False
    state_changed: bool = False
    terminal: bool = False
    terminal_payload: Mapping[str, Any] | None = None
    observation_key: str = ""
    model_content_blocks: tuple[Mapping[str, Any], ...] = ()


@dataclass(frozen=True)
class ClientToolLoopResult:
    """Terminal bounded loop result; acceptance remains caller-owned."""

    terminal_payload: Mapping[str, Any]
    messages: tuple[Mapping[str, Any], ...]
    history: tuple[Mapping[str, Any], ...]
    provider: str
    model: str
    turns: int
    tool_calls: int
    runtime_executed_tool_calls: int
    transcript_fingerprint: str
    provider_usage: Mapping[str, int] = field(default_factory=dict)
    final_response_metadata: Mapping[str, Any] = field(default_factory=dict)
    observation_refs: tuple[Mapping[str, Any], ...] = ()


def read_hash_bound_utf8_file(
    reference: Mapping[str, Any],
) -> tuple[str, tuple[str, ...]]:
    """Read exact referenced text while keeping identity failures caller-owned."""

    try:
        encoded = Path(str(reference.get("path", "") or "")).expanduser().resolve().read_bytes()
        content = encoded.decode("utf-8")
    except (OSError, UnicodeError) as exc:
        return "", (type(exc).__name__,)
    errors = []
    if hashlib.sha256(encoded).hexdigest() != str(reference.get("sha256", "") or ""):
        errors.append("sha256_mismatch")
    if len(encoded) != reference.get("byte_size"):
        errors.append("byte_size_mismatch")
    return (content if not errors else ""), tuple(errors)


def externalize_client_tool_text_documents(
    value: Any,
    *,
    min_characters: int,
    path_prefix: str,
) -> tuple[Any, dict[str, str], list[dict[str, Any]]]:
    """Replace long exact strings with content-addressed read/search references."""

    if isinstance(min_characters, bool) or int(min_characters) < 1:
        raise ValueError("client-tool document threshold must be positive")
    prefix = PurePosixPath(str(path_prefix or "").strip())
    if (
        not str(prefix)
        or prefix.is_absolute()
        or any(part in {"", ".", ".."} for part in prefix.parts)
    ):
        raise ValueError("client-tool document prefix must be canonical and relative")
    documents: dict[str, str] = {}
    catalog: list[dict[str, Any]] = []

    def externalize(current: Any, json_path: str) -> Any:
        if isinstance(current, str) and len(current) >= int(min_characters):
            document_path = (
                prefix.as_posix()
                + "/"
                + stable_hash([json_path, stable_hash(current)])[:20]
                + ".md"
            )
            documents[document_path] = current
            row = {
                "path": document_path,
                "json_path": json_path,
                "content_hash": stable_hash(current),
                "character_count": len(current),
                "line_count": max(1, len(current.splitlines())),
            }
            catalog.append(row)
            return {
                "client_tool_evidence_document_ref": document_path,
                **row,
                "content_externalized_without_loss": True,
            }
        if isinstance(current, Mapping):
            return {
                str(key): externalize(child, f"{json_path}/{key}")
                for key, child in current.items()
            }
        if isinstance(current, (list, tuple)):
            return [
                externalize(child, f"{json_path}/{index}")
                for index, child in enumerate(current)
            ]
        return deepcopy(current)

    return externalize(value, "$"), documents, catalog


class ClientToolLoopError(RuntimeError):
    def __init__(
        self,
        *,
        reason: str,
        turns: int,
        tool_calls: int,
        runtime_executed_tool_calls: int,
        history: list[Mapping[str, Any]],
        messages: list[Mapping[str, Any]] | None = None,
        provider: str = "",
        model: str = "",
        final_response_metadata: Mapping[str, Any] | None = None,
        observation_refs: Sequence[Mapping[str, Any]] = (),
    ) -> None:
        self.reason = str(reason)
        self.turns = int(turns)
        self.tool_calls = int(tool_calls)
        self.runtime_executed_tool_calls = int(runtime_executed_tool_calls)
        self.history = [deepcopy(dict(row)) for row in history]
        self.messages = [
            deepcopy(dict(message)) for message in (messages or [])
        ]
        self.provider = str(provider)
        self.model = str(model)
        self.final_response_metadata = deepcopy(
            dict(final_response_metadata or {})
        )
        self.provider_usage = _provider_usage_totals(self.history)
        self.transcript_fingerprint = stable_hash(self.messages)
        self.observation_refs = tuple(deepcopy(dict(ref)) for ref in observation_refs)
        super().__init__(
            f"bounded client-tool loop stopped after {turns} turn(s) and "
            f"{tool_calls} call(s): {reason}"
        )


class ClientToolInputError(ValueError):
    """A caller-reviewed tool error whose detail is safe for the model."""


def model_exact_text_edit_json_schema() -> dict[str, Any]:
    """Shared schema for one model-authored exact text replacement."""

    return {
        "type": "object",
        "additionalProperties": False,
        "required": ["old_text", "new_text"],
        "properties": {
            "old_text": {"type": "string", "minLength": 1},
            "new_text": {"type": "string"},
            "expected_occurrences": {"type": "integer", "minimum": 1},
        },
    }


def model_exact_text_edits_json_schema() -> dict[str, Any]:
    """Shared model-authored atomic exact-edit batch schema."""

    return {
        "type": "array",
        "minItems": 1,
        "items": model_exact_text_edit_json_schema(),
    }


def apply_model_exact_text_edits(
    text: str,
    *,
    edits: Any,
    replacement_key: str,
) -> tuple[str, list[dict[str, Any]]]:
    """Apply an ordered exact-edit batch atomically in caller-owned state."""

    if not isinstance(edits, list) or not edits:
        raise ClientToolInputError("exact edits must be a nonempty array")
    revised, records = text, []
    for index, edit in enumerate(edits):
        required_fields = {"old_text", replacement_key}
        optional_fields = {"expected_occurrences"}
        if not isinstance(edit, Mapping):
            raise ClientToolInputError(f"exact edit index {index} must be an object")
        edit_fields = set(edit)
        missing_fields = sorted(required_fields - edit_fields)
        unexpected_fields = sorted(edit_fields - required_fields - optional_fields)
        if missing_fields or unexpected_fields:
            raise ClientToolInputError(
                f"exact edit index {index} has invalid fields; "
                f"missing={missing_fields}, unexpected={unexpected_fields}, "
                f"required={sorted(required_fields)}, optional={sorted(optional_fields)}"
            )
        old_text, replacement = edit["old_text"], edit[replacement_key]
        if not isinstance(old_text, str) or not old_text:
            raise ClientToolInputError(f"exact edit index {index} old_text is empty")
        if not isinstance(replacement, str):
            raise ClientToolInputError(f"exact edit index {index} replacement is not text")
        expected_occurrences = edit.get("expected_occurrences", 1)
        if (
            isinstance(expected_occurrences, bool)
            or not isinstance(expected_occurrences, int)
            or expected_occurrences < 1
        ):
            raise ClientToolInputError(
                f"exact edit index {index} expected_occurrences must be a positive integer"
            )
        positions = [
            i for i in range(len(revised)) if revised.startswith(old_text, i)
        ]
        observed_occurrences = len(positions)
        if observed_occurrences != expected_occurrences:
            if "expected_occurrences" not in edit:
                raise ClientToolInputError(
                    "old_text must match the exact current artifact once; observed "
                    f"{observed_occurrences} matches at edit index {index}"
                )
            raise ClientToolInputError(
                "old_text must match the exact current artifact the declared number "
                f"of times; expected {expected_occurrences}, observed "
                f"{observed_occurrences} at edit index {index}"
            )
        if any(
            right - left < len(old_text)
            for left, right in zip(positions, positions[1:])
        ):
            raise ClientToolInputError(
                f"exact edit index {index} has overlapping matches"
            )
        updated = revised.replace(old_text, replacement)
        if updated == revised:
            raise ClientToolInputError(f"exact edit index {index} makes no byte change")
        revised = updated
        record = {
            "old_text_hash": stable_hash(old_text),
            "replacement_hash": stable_hash(replacement),
            "old_text_chars": len(old_text),
            "replacement_chars": len(replacement),
        }
        if "expected_occurrences" in edit:
            record["occurrences_replaced"] = expected_occurrences
        records.append(record)
    return revised, records


class ClientToolRuntimeError(ClientToolLoopError):
    """A non-model-actionable tool failure with secret-free diagnostics."""

    def __init__(
        self,
        *,
        tool_name: str,
        turn_index: int,
        call_index: int,
        exception_type: str,
        turns: int,
        tool_calls: int,
        runtime_executed_tool_calls: int,
        history: list[Mapping[str, Any]],
        messages: list[Mapping[str, Any]],
        provider: str,
        model: str,
        final_response_metadata: Mapping[str, Any],
        observation_refs: Sequence[Mapping[str, Any]] = (),
    ) -> None:
        self.tool_name = str(tool_name)
        self.turn_index = int(turn_index)
        self.call_index = int(call_index)
        self.exception_type = str(exception_type)
        super().__init__(
            reason=(
                "client tool runtime failed outside the model-actionable boundary: "
                f"{self.tool_name} raised {self.exception_type} at turn "
                f"{self.turn_index}, call {self.call_index}; detail withheld; "
                "pending workspace state preserved for explicit continuation"
            ),
            turns=turns,
            tool_calls=tool_calls,
            runtime_executed_tool_calls=runtime_executed_tool_calls,
            history=history,
            messages=messages,
            provider=provider,
            model=model,
            final_response_metadata=final_response_metadata,
            observation_refs=observation_refs,
        )


ClientToolExecutor = Callable[
    [ClientToolCall, ClientToolExecutionContext],
    ClientToolExecutionResult,
]

WorkspaceResultT = TypeVar("WorkspaceResultT")


@dataclass(frozen=True)
class PreparedClientToolWorkspace(Generic[WorkspaceResultT]):
    """Executable single-owner binding, without a model driver.

    Composing actions grants no additional authority. Result handlers remain
    bound to this request; unrelated histories cannot become owner receipts.
    """

    request: ClientToolTurnRequest
    execute_tool: ClientToolExecutor
    on_success: Callable[[ClientToolLoopResult], WorkspaceResultT]
    on_error: Callable[[ClientToolLoopError], WorkspaceResultT]
    max_turns: int
    max_tool_calls: int
    max_no_progress_turns: int
    session_dir: Path | None
    session_id: str
    initial_context: Mapping[str, Any] = field(default_factory=dict)


def run_client_tool_workspace(
    *, backend: Any, workspace: PreparedClientToolWorkspace[WorkspaceResultT],
) -> WorkspaceResultT:
    """Use the sole retained loop; the source owner still validates its result."""

    try:
        loop = run_bounded_client_tool_loop(
            backend=backend,
            request=workspace.request,
            execute_tool=workspace.execute_tool,
            max_turns=workspace.max_turns,
            max_tool_calls=workspace.max_tool_calls,
            max_no_progress_turns=workspace.max_no_progress_turns,
            session_dir=workspace.session_dir,
            session_id=workspace.session_id,
        )
    except ClientToolLoopError as exc:
        return workspace.on_error(exc)
    return workspace.on_success(loop)


def prepare_shared_client_tool_workspace(
    *,
    request: ClientToolTurnRequest,
    workspaces: Mapping[str, PreparedClientToolWorkspace[Any]],
    control_tools: Sequence[ClientToolDefinition],
    execute_control_tool: ClientToolExecutor,
    observe_checkpoint: Callable[[str, ClientToolExecutionResult], Mapping[str, Any] | None],
    max_turns: int,
    max_tool_calls: int,
    max_no_progress_turns: int,
    session_dir: Path,
    session_id: str,
) -> PreparedClientToolWorkspace[ClientToolLoopResult]:
    """Bind actual component actions to one shared, non-independent conversation.

    The caller supplies the research objective, final action and artifact binding.
    Component checkpoints are observations, not outer-session stop decisions.
    No component model driver or isolated-owner result handler is invoked.
    """

    if not workspaces or not session_id.strip():
        raise ValueError("shared workspace requires components and a session identity")
    if request.tools or CLIENT_TOOL_PARENT_SESSION_METADATA_KEY in request.metadata:
        raise ValueError("shared request must not contain tools or an unrelated parent session")
    if not control_tools or not any(tool.terminal for tool in control_tools):
        raise ValueError("shared workspace requires explicit terminal actions")
    tools: list[ClientToolDefinition] = []
    routes: dict[str, tuple[str, PreparedClientToolWorkspace[Any], ClientToolDefinition]] = {}
    scopes = {}
    for scope, workspace in workspaces.items():
        if (not isinstance(scope, str) or not scope or not scope.isascii()
            or any(not (char.isalnum() or char == "_") for char in scope)
            or "__" in scope):
            raise ValueError("shared component scope must be a simple ASCII identifier")
        for field_name in ("model", "temperature", "thinking_budget_tokens"):
            if getattr(workspace.request, field_name) != getattr(request, field_name):
                raise ValueError("shared components must use the same model and sampling")
        original_names = [tool.name for tool in workspace.request.tools]
        if not original_names or len(set(original_names)) != len(original_names):
            raise ValueError("shared component tools must have unique nonempty names")
        for tool in workspace.request.tools:
            if tool.name == WORKSPACE_HISTORY_TOOL_NAME:
                continue
            qualified_name = scope + "__" + tool.name
            if not tool.name or len(qualified_name) > 64:
                raise ValueError("shared qualified tool name is empty or too long")
            routes[qualified_name] = (scope, workspace, tool)
            description = tool.description
            if tool.terminal:
                description += " This records a component checkpoint; the shared session remains open."
            tools.append(replace(tool, name=qualified_name, description=description, terminal=False))
        scopes[scope] = {
            "session_id": workspace.session_id,
            "component_request_contract": client_tool_session_contract_fingerprint(workspace.request),
            "initial_context_hash": stable_hash(workspace.initial_context),
            "tools": original_names,
        }
    control_names = [tool.name for tool in control_tools]
    if (len(set(control_names)) != len(control_names)
        or any(not name or name in routes or name == WORKSPACE_HISTORY_TOOL_NAME
               for name in control_names)):
        raise ValueError("shared control tool names collide with component actions")
    tools.extend(control_tools)
    tools.append(workspace_history_tool())
    shared_request = replace(
        request,
        tools=tuple(tools),
        messages=(*request.messages, {"role": "user", "content": json.dumps({
            "initial_workspace_contexts": {scope: deepcopy(dict(workspace.initial_context))
                                           for scope, workspace in workspaces.items()},
        }, sort_keys=True, ensure_ascii=False, default=str)}),
        metadata={
            **deepcopy(dict(request.metadata)),
            "workspace_context_mode": "shared_conversation",
            "independent_role_review": False,
            "shared_component_scopes": scopes,
            CLIENT_TOOL_AUTHORIZATION_FINGERPRINT_METADATA_KEY: stable_hash({
                "root_authorization": client_tool_authorization_fingerprint(request.metadata),
                "session_id": session_id,
                "scopes": scopes,
                "control_tools": [asdict(tool) for tool in control_tools],
            }),
        },
    )

    def execute(call: ClientToolCall, context: ClientToolExecutionContext) -> ClientToolExecutionResult:
        if call.name in control_names:
            return execute_control_tool(call, context)
        if call.name not in routes:
            raise ClientToolInputError("unknown shared workspace action")
        scope, workspace, original_tool = routes[call.name]
        result = workspace.execute_tool(replace(call, name=original_tool.name), context)
        if not original_tool.terminal:
            return replace(result, observation_key=scope + ":" + result.observation_key
                           if result.observation_key else "")
        if result.terminal and not result.is_error:
            if not isinstance(result.terminal_payload, Mapping):
                raise ValueError("component checkpoint returned no payload")
            checkpoint_ref = observe_checkpoint(scope, deepcopy(result))
            if checkpoint_ref is not None:
                result = replace(result, model_content_blocks=(*result.model_content_blocks, {
                    "type": "text", "text": json.dumps({"shared_checkpoint_ref": dict(checkpoint_ref)},
                                                        sort_keys=True, ensure_ascii=False),
                }))
        return replace(result, terminal=False,
                       observation_key=scope + ":" + result.observation_key
                       if result.observation_key else "")

    def record(result: ClientToolLoopResult | ClientToolLoopError) -> None:
        persist_client_tool_session(
            session_dir=session_dir, session_id=session_id, request=shared_request,
            messages=result.messages, observation_refs=result.observation_refs,
        )

    def on_success(loop: ClientToolLoopResult) -> ClientToolLoopResult:
        record(loop)
        return loop

    def on_error(exc: ClientToolLoopError) -> ClientToolLoopResult:
        record(exc)
        raise exc

    return PreparedClientToolWorkspace(
        request=shared_request, execute_tool=execute, on_success=on_success, on_error=on_error,
        max_turns=max_turns, max_tool_calls=max_tool_calls,
        max_no_progress_turns=max_no_progress_turns, session_dir=session_dir, session_id=session_id,
    )


CLIENT_TOOL_SESSION_KIND = "ClientToolWorkspaceSession"
CLIENT_TOOL_SESSION_DIRECTORY = ".client_tool_sessions"
CLIENT_TOOL_CHECKPOINT_WINDOW_POLICY = "fresh_context_from_hash_bound_checkpoint_v1"
CLIENT_TOOL_RECENT_HISTORY_WINDOW_POLICY = (
    "current_context_with_recent_complete_tool_rounds_from_hash_bound_checkpoint_v2"
)
CLIENT_TOOL_RECENT_HISTORY_ROUNDS = 8
CLIENT_TOOL_TRANSCRIPT_POLICY = "linear_with_state_bound_checkpoint_windows_v4"
CLIENT_TOOL_RESULT_MAX_CHARS = 60_000
CLIENT_TOOL_AUTHORIZATION_FINGERPRINT_METADATA_KEY = "client_tool_authorization_fingerprint"
CLIENT_TOOL_PARENT_SESSION_METADATA_KEY = "client_tool_parent_session_ref"
WORKSPACE_HISTORY_TOOL_NAME = "read_workspace_history"


def workspace_history_tool() -> ClientToolDefinition:
    return ClientToolDefinition(
        name=WORKSPACE_HISTORY_TOOL_NAME,
        description=(
            "Read tool observations from this workspace, not private model reasoning. "
            "Omit session_sha256 for the current window; an older window must belong to "
            "its validated parent chain. Omit observation_sha256 to read the observation "
            "catalog and parent window hash; otherwise select an exact observation hash. "
            "Without a window selector, that hash is found in the current or authorized older windows. "
            "Evaluator-owned metadata is withheld from this view; the audit record remains unchanged. "
            "observation_sha256 selects the stored record; sha256 identifies the returned view. "
            "Read up to 20000 characters of the serialized observation view or catalog; "
            "character_end is exclusive. "
            "Historical results are working context, not current scientific acceptance."
        ),
        input_schema={
            "type": "object", "additionalProperties": False,
            "properties": {
                "session_sha256": {"type": "string"},
                "observation_sha256": {"type": "string", "minLength": 1},
                "character_start": {"type": "integer", "minimum": 0},
                "character_end": {"type": "integer", "minimum": 1},
            },
        },
    )


def _persist_workspace_observation(
    session_dir: Path, call: ClientToolCall, execution: ClientToolExecutionResult,
) -> dict[str, Any]:
    text = json.dumps({
        "tool_name": call.name, "call_id": call.call_id, "input": dict(call.input),
        "is_error": execution.is_error, "content": execution.content,
        "model_content_blocks": list(execution.model_content_blocks),
        **({"terminal_payload": execution.terminal_payload}
           if execution.terminal_payload is not None else {}),
    }, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str)
    encoded = text.encode("utf-8")
    sha256 = hashlib.sha256(encoded).hexdigest()
    relative = PurePosixPath(CLIENT_TOOL_SESSION_DIRECTORY, "observations", sha256 + ".json")
    root = session_dir.resolve()
    path = (root / Path(relative)).resolve()
    if not path.is_relative_to(root):
        raise ValueError("workspace observation escapes its session directory")
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.read_bytes() != encoded:
            raise ValueError("workspace observation contains different bytes")
    else:
        path.write_bytes(encoded)
    return {
        "relative_path": relative.as_posix(), "sha256": sha256,
        "byte_size": len(encoded), "character_count": len(text),
        "tool_name": call.name, "call_id": call.call_id, "is_error": execution.is_error,
    }


def read_client_tool_observation(reference: Mapping[str, Any], *, session_dir: Path) -> str:
    """Read exact stored text; the caller owns catalog authorization."""

    relative = PurePosixPath(str(reference.get("relative_path", "")))
    root = session_dir.resolve()
    path = (root / Path(relative)).resolve()
    if (relative.is_absolute() or ".." in relative.parts
        or relative.parts[:2] != (CLIENT_TOOL_SESSION_DIRECTORY, "observations")
        or not path.is_relative_to(root)):
        raise ValueError("workspace observation reference escapes its store")
    text, errors = read_hash_bound_utf8_file({**reference, "path": str(path)})
    if errors:
        raise ValueError("workspace observation identity mismatch: " + ",".join(errors))
    return text


def _read_workspace_history(
    tool_input: Mapping[str, Any], *, session_dir: Path, session_id: str,
    request: ClientToolTurnRequest, observation_refs: Sequence[Mapping[str, Any]],
) -> ClientToolExecutionResult:
    allowed = {"session_sha256", "observation_sha256", "character_start", "character_end"}
    if set(tool_input) - allowed:
        raise ClientToolInputError("unexpected workspace history fields")
    selected = tool_input.get("session_sha256", "")
    if not isinstance(selected, str):
        raise ClientToolInputError("session_sha256 must be a string")
    observation_sha = tool_input.get("observation_sha256")
    if observation_sha is not None and (not isinstance(observation_sha, str) or not observation_sha):
        raise ClientToolInputError("observation_sha256 must be a nonempty string")
    parent = request.metadata.get(CLIENT_TOOL_PARENT_SESSION_METADATA_KEY, {})
    refs = list(observation_refs)
    if selected or (observation_sha and not any(ref["sha256"] == observation_sha for ref in refs)):
        seen = set()
        while parent:
            sha = str(parent.get("sha256", ""))
            if sha in seen:
                raise ValueError("workspace session parent cycle")
            seen.add(sha)
            payload = _load_client_tool_session_payload(
                parent, session_dir=session_dir, session_id=session_id, request=request,
            )
            parent = payload.get("parent_session_ref", {})
            archived_refs = payload.get("observation_refs", [])
            if sha == selected or (not selected and any(ref["sha256"] == observation_sha for ref in archived_refs)):
                refs = archived_refs
                selected = sha
                break
        else:
            raise ClientToolInputError("selection is not in this workspace's authorized parent chain")
    if observation_sha is None:
        text = json.dumps(refs, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        sha = hashlib.sha256(text.encode()).hexdigest()
    else:
        ref = next((ref for ref in refs if ref["sha256"] == observation_sha), None)
        if ref is None:
            raise ClientToolInputError("observation_sha256 is outside this window's catalog")
        text = read_client_tool_observation(ref, session_dir=session_dir)
        sha = ref["sha256"]
        original = json.loads(text)
        projected = withhold_confirmatory_evaluation_seed(original)
        if projected != original:
            text = json.dumps(projected, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
            sha = hashlib.sha256(text.encode("utf-8")).hexdigest()
    start = tool_input.get("character_start", 0)
    end = tool_input.get("character_end", min(len(text), start + 20000) if type(start) is int else 0)
    if (type(start) is not int or type(end) is not int
        or not 0 <= start < end <= len(text) or end - start > 20000):
        raise ClientToolInputError("history character range must select 1..20000 characters within the document")
    return ClientToolExecutionResult(content={
        "ok": True, "session_sha256": selected, "observation_sha256": observation_sha,
        "parent_session_sha256": str(parent.get("sha256", "")),
        "observation_count": len(refs), "sha256": sha,
        "character_start": start, "character_end": end, "total_characters": len(text),
        "complete": start == 0 and end == len(text), "text": text[start:end],
        "evidence_role": "historical_tool_observation_not_current_acceptance",
    })


def client_tool_authorization_fingerprint(
    metadata: Mapping[str, Any] | None,
) -> str:
    return str((metadata or {}).get(CLIENT_TOOL_AUTHORIZATION_FINGERPRINT_METADATA_KEY, "") or "").strip()


def _client_tool_ids(content: Any, *, kind: str, identity: str) -> set[str]:
    if not isinstance(content, list):
        return set()
    return {
        str(block.get(identity, "") or "")
        for block in content
        if isinstance(block, Mapping)
        and block.get("type") == kind
        and str(block.get(identity, "") or "").strip()
    }


def _recent_complete_client_tool_rounds(
    messages: Sequence[Mapping[str, Any]],
    *,
    max_rounds: int,
) -> list[tuple[dict[str, Any], dict[str, Any]]]:
    """Select recent exact tool-call/result pairs without synthesizing content."""

    rounds = []
    for index in range(1, len(messages) - 1):
        assistant = messages[index]
        user = messages[index + 1]
        if (
            str(assistant.get("role", "") or "") != "assistant"
            or str(user.get("role", "") or "") != "user"
        ):
            continue
        call_ids = _client_tool_ids(
            assistant.get("content", []), kind="tool_use", identity="id"
        )
        result_ids = _client_tool_ids(
            user.get("content", []), kind="tool_result", identity="tool_use_id"
        )
        if call_ids and call_ids == result_ids:
            rounds.append((deepcopy(dict(assistant)), deepcopy(dict(user))))
    return rounds[-max_rounds:]


def _client_tool_content_blocks(content: Any) -> list[Any]:
    return deepcopy(content) if isinstance(content, list) else [{"type": "text", "text": str(content)}]


def client_tool_session_contract_fingerprint(
    request: ClientToolTurnRequest,
) -> str:
    """Bind a resumable transcript to one complete model sampling contract."""

    return stable_hash(
        {
            "contract_schema_version": 4,
            "model": request.model,
            "system_prompt": request.system_prompt,
            "max_tokens": request.max_tokens,
            "temperature": request.temperature,
            "tool_choice": request.tool_choice,
            "disable_parallel_tool_use": request.disable_parallel_tool_use,
            "enable_prompt_caching": request.enable_prompt_caching,
            **({"thinking_budget_tokens": request.thinking_budget_tokens}
               if request.thinking_budget_tokens else {}),
            "authorization_fingerprint": client_tool_authorization_fingerprint(request.metadata),
            "tools": [asdict(tool) for tool in request.tools],
        }
    )


def persist_client_tool_session(
    *,
    session_dir: Path | None,
    session_id: str,
    request: ClientToolTurnRequest,
    messages: Sequence[Mapping[str, Any]],
    durable_state_identity: str = "",
    observation_refs: Sequence[Mapping[str, Any]] = (),
) -> dict[str, Any]:
    """Persist one immutable transcript and return a compact integrity reference."""

    if session_dir is None:
        return {}
    normalized_session_id = str(session_id or "").strip()
    if not normalized_session_id:
        raise ValueError("client-tool session id is required")
    normalized_messages = [deepcopy(dict(message)) for message in messages]
    if not normalized_messages:
        raise ValueError("client-tool session requires at least one message")
    root = session_dir.resolve()
    normalized_state_identity = str(durable_state_identity or "").strip()
    transcript_fingerprint = stable_hash(normalized_messages)
    session_contract_fingerprint = client_tool_session_contract_fingerprint(
        request
    )
    authorization_fingerprint = client_tool_authorization_fingerprint(request.metadata)
    body = {
        "schema_version": 3,
        "artifact_kind": CLIENT_TOOL_SESSION_KIND,
        "session_id": normalized_session_id,
        "root_path": str(root),
        "session_contract_fingerprint": session_contract_fingerprint,
        "authorization_fingerprint": authorization_fingerprint,
        "durable_state_identity": normalized_state_identity,
        "transcript_fingerprint": transcript_fingerprint,
        "message_count": len(normalized_messages),
        "messages": normalized_messages,
        "observation_refs": [deepcopy(dict(ref)) for ref in observation_refs],
        "parent_session_ref": deepcopy(dict(request.metadata.get(CLIENT_TOOL_PARENT_SESSION_METADATA_KEY, {}))),
    }
    encoded = json.dumps(
        body,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    sha256 = hashlib.sha256(encoded).hexdigest()
    relative_path = PurePosixPath(
        CLIENT_TOOL_SESSION_DIRECTORY,
        f"{sha256}.json",
    )
    target = (root / Path(relative_path)).resolve()
    if root != target and root not in target.parents:
        raise ValueError("client-tool session path escapes its workspace")
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        if target.read_bytes() != encoded:
            raise ValueError("client-tool session path contains different bytes")
    else:
        target.write_bytes(encoded)
    return {
        "schema_version": 3,
        "artifact_kind": "ClientToolWorkspaceSessionRef",
        "session_id": normalized_session_id,
        "root_path": str(root),
        "relative_path": relative_path.as_posix(),
        "sha256": sha256,
        "message_count": len(normalized_messages),
        "transcript_fingerprint": transcript_fingerprint,
        "session_contract_fingerprint": session_contract_fingerprint,
        "authorization_fingerprint": authorization_fingerprint,
        "durable_state_identity": normalized_state_identity,
    }


def _load_client_tool_session_payload(
    reference: Mapping[str, Any],
    *,
    session_dir: Path,
    session_id: str,
    request: ClientToolTurnRequest,
    durable_state_identity: str | None = None,
) -> dict[str, Any]:
    """Load a transcript only when its workspace and tool contract still match."""

    ref = dict(reference)
    normalized_session_id = str(session_id or "").strip()
    expected_contract = client_tool_session_contract_fingerprint(request)
    expected_authorization = client_tool_authorization_fingerprint(request.metadata)
    expected_state_identity = (
        None
        if durable_state_identity is None
        else str(durable_state_identity or "").strip()
    )
    root = session_dir.resolve()
    relative_path = PurePosixPath(str(ref.get("relative_path", "") or ""))
    if (
        int(ref.get("schema_version", 0) or 0) != 3
        or ref.get("artifact_kind") != "ClientToolWorkspaceSessionRef"
        or str(ref.get("session_id", "") or "") != normalized_session_id
        or str(ref.get("root_path", "") or "") != str(root)
        or str(ref.get("session_contract_fingerprint", "") or "")
        != expected_contract
        or str(ref.get("authorization_fingerprint", "") or "")
        != expected_authorization
        or (
            expected_state_identity is not None
            and str(ref.get("durable_state_identity", "") or "")
            != expected_state_identity
        )
        or relative_path.is_absolute()
        or not relative_path.parts
        or relative_path.parts[0] != CLIENT_TOOL_SESSION_DIRECTORY
        or ".." in relative_path.parts
    ):
        raise ValueError("client-tool session reference identity mismatch")
    path = (root / Path(relative_path)).resolve()
    if root != path and root not in path.parents:
        raise ValueError("client-tool session reference escapes its workspace")
    encoded = path.read_bytes()
    if hashlib.sha256(encoded).hexdigest() != str(ref.get("sha256", "") or ""):
        raise ValueError("client-tool session bytes do not match their reference")
    payload = json.loads(encoded.decode("utf-8"))
    messages = payload.get("messages", []) if isinstance(payload, Mapping) else []
    if not (
        isinstance(payload, Mapping)
        and int(payload.get("schema_version", 0) or 0) == 3
        and payload.get("artifact_kind") == CLIENT_TOOL_SESSION_KIND
        and payload.get("session_id") == normalized_session_id
        and payload.get("root_path") == str(root)
        and payload.get("session_contract_fingerprint") == expected_contract
        and payload.get("authorization_fingerprint") == expected_authorization
        and payload.get("durable_state_identity")
        == ref.get("durable_state_identity")
        and (
            expected_state_identity is None
            or payload.get("durable_state_identity") == expected_state_identity
        )
        and isinstance(messages, list)
        and messages
        and all(isinstance(message, Mapping) for message in messages)
        and int(payload.get("message_count", 0) or 0) == len(messages)
        and int(ref.get("message_count", 0) or 0) == len(messages)
        and stable_hash(messages) == payload.get("transcript_fingerprint")
        and payload.get("transcript_fingerprint")
        == ref.get("transcript_fingerprint")
    ):
        raise ValueError("client-tool session payload identity mismatch")
    return dict(payload)


def load_client_tool_session(
    reference: Mapping[str, Any], *, session_dir: Path, session_id: str,
    request: ClientToolTurnRequest, durable_state_identity: str | None = None,
) -> tuple[Mapping[str, Any], ...]:
    payload = _load_client_tool_session_payload(
        reference, session_dir=session_dir, session_id=session_id,
        request=request, durable_state_identity=durable_state_identity,
    )
    return tuple(deepcopy(dict(message)) for message in payload["messages"])


def resume_client_tool_session_from_checkpoint(
    reference: Mapping[str, Any],
    *,
    session_dir: Path,
    session_id: str,
    checkpoint_identity: str,
    request: ClientToolTurnRequest,
    replay_recent_tool_rounds: int = 0,
    require_durable_state_binding: bool = False,
) -> tuple[ClientToolTurnRequest, dict[str, Any]]:
    """Resume from an exact checkpoint and optional recent complete tool rounds."""

    normalized_checkpoint_identity = str(checkpoint_identity or "").strip()
    if not normalized_checkpoint_identity:
        raise ValueError("checkpoint-window resume requires checkpoint identity")
    if replay_recent_tool_rounds < 0:
        raise ValueError("recent tool-round replay count cannot be negative")
    authorization_fingerprint = client_tool_authorization_fingerprint(request.metadata)
    if not authorization_fingerprint:
        raise ValueError(
            "checkpoint-window resume requires a root authorization fingerprint"
        )
    ref = dict(reference)
    bound_state_identity = str(ref.get("durable_state_identity", "") or "").strip()
    if require_durable_state_binding and not bound_state_identity:
        raise ValueError(
            "checkpoint-window resume requires a durable state identity"
        )
    prior_messages = load_client_tool_session(
        reference,
        session_dir=session_dir,
        session_id=session_id,
        request=request,
        durable_state_identity=(
            normalized_checkpoint_identity if bound_state_identity else None
        ),
    )
    messages = [deepcopy(dict(message)) for message in request.messages]
    if not messages or str(messages[0].get("role", "") or "") != "user":
        raise ValueError(
            "checkpoint-window resume requires an initial user workspace message"
        )
    replayed_rounds = _recent_complete_client_tool_rounds(
        prior_messages,
        max_rounds=replay_recent_tool_rounds,
    ) if replay_recent_tool_rounds else []
    replayed_messages = [message for pair in replayed_rounds for message in pair]
    replay_enabled = bool(replayed_messages)
    current_opening = deepcopy(dict(messages[0]))
    window = {
        "policy": (
            CLIENT_TOOL_RECENT_HISTORY_WINDOW_POLICY
            if replay_enabled
            else CLIENT_TOOL_CHECKPOINT_WINDOW_POLICY
        ),
        "parent_session_sha256": str(ref.get("sha256", "") or ""),
        "parent_transcript_fingerprint": str(
            ref.get("transcript_fingerprint", "") or ""
        ),
        "parent_message_count": len(prior_messages),
        "checkpoint_identity": normalized_checkpoint_identity,
        "parent_durable_state_identity": str(
            ref.get("durable_state_identity", "") or ""
        ),
        "authorization_fingerprint": authorization_fingerprint,
        "prior_transcript_replayed": replay_enabled,
        "replayed_tool_rounds": len(replayed_rounds),
        "replayed_message_count": len(replayed_messages),
        "replayed_messages_fingerprint": stable_hash(replayed_messages)
        if replayed_messages
        else "",
        "parent_opening_replayed": False,
        "current_opening_fingerprint": stable_hash(current_opening),
        "current_opening_authoritative": True,
        "summary_used": False,
        "authoritative_state_source": "hash_bound_checkpoint_and_current_workspace_tools",
        "evidence_role": "conversation_lineage_not_scientific_evidence",
    }
    notice = (
        "A previous model/tool context window ended at a hash-bound durable "
        "checkpoint. Its exact transcript was validated for lineage. "
        + (
            "Recent complete tool-call/result rounds are replayed below as working "
            "context; any budget counters in them belong to the old window. "
            if replay_enabled
            else "The prior conversation is not replayed in this window. "
        )
        + "Continue only from the authoritative current checkpoint state and current "
        "workspace tools; conversation history and this notice are not scientific "
        "evidence.\n"
        + json.dumps(window, sort_keys=True, separators=(",", ":"))
    )
    if any(tool.name == WORKSPACE_HISTORY_TOOL_NAME for tool in request.tools):
        notice += ("\nEarlier exact tool observations remain available through read_workspace_history; "
                   "select parent session_sha256=" + str(ref.get("sha256", "")) +
                   ". Current checkpoint and verifier authority are unchanged.")
    if replay_enabled:
        if str(prior_messages[0].get("role", "") or "") != "user":
            raise ValueError("recent-history resume requires a parent initial user message")
        messages = [current_opening, *replayed_messages]
        final_user = messages[-1]
        final_user["content"] = [
            *_client_tool_content_blocks(final_user.get("content", [])),
            {"type": "text", "text": notice},
        ]
        messages[-1] = final_user
    else:
        first_message = messages[0]
        content = first_message.get("content", "")
        if isinstance(content, list):
            first_message["content"] = [
                {"type": "text", "text": notice},
                *deepcopy(content),
            ]
        else:
            first_message["content"] = notice + "\n\n" + str(content)
        messages[0] = first_message
    return (
        replace(
            request,
            messages=tuple(messages),
            metadata={
                **dict(request.metadata),
                "resumed_client_tool_session_fingerprint": window[
                    "parent_transcript_fingerprint"
                ],
                "client_tool_checkpoint_window": deepcopy(window),
                CLIENT_TOOL_PARENT_SESSION_METADATA_KEY: deepcopy(ref),
            },
        ),
        window,
    )


def run_bounded_client_tool_loop(
    *,
    backend: Any,
    request: ClientToolTurnRequest,
    execute_tool: ClientToolExecutor,
    max_turns: int,
    max_tool_calls: int,
    max_no_progress_turns: int,
    session_dir: Path | None = None,
    session_id: str = "",
) -> ClientToolLoopResult:
    """Run one retained model/tool session under explicit caller-owned bounds.

    Every model turn sees the same tool surface. Tool results, including rejected
    terminal submissions, return to the same model context while ordinary turns
    remain. A model response without a tool call ends the current workspace
    segment; the exact session is preserved for explicit continuation instead of
    synthesizing a correction prompt or sampling again. Exhaustion follows the
    same checkpoint boundary.
    """

    if max_turns < 1 or max_tool_calls < 1 or max_no_progress_turns < 1:
        raise ValueError("client-tool loop budgets must all be positive")
    generate_turn = getattr(backend, "generate_client_tool_turn", None)
    if not callable(generate_turn):
        raise ValueError("backend does not support client-tool turns")
    allowed_tool_names = [tool.name for tool in request.tools]
    if (not allowed_tool_names
        or any(not str(name).strip() for name in allowed_tool_names)
        or len(set(allowed_tool_names)) != len(allowed_tool_names)):
        raise ValueError("client-tool definitions must have unique nonempty names")
    tool_definitions = {tool.name: tool for tool in request.tools}
    history_enabled = WORKSPACE_HISTORY_TOOL_NAME in tool_definitions
    if history_enabled and (session_dir is None or not session_id
                            or not client_tool_authorization_fingerprint(request.metadata)):
        raise ValueError("workspace history requires an authorized persistent session")
    observation_refs: list[Mapping[str, Any]] = []
    messages = [deepcopy(dict(message)) for message in request.messages]
    history: list[dict[str, Any]] = []
    seen_observations: set[str] = set()
    total_calls = runtime_executed_tool_calls = no_progress_turns = 0
    last_response: ClientToolTurnResponse | None = None
    terminal_tools = tuple(tool for tool in request.tools if tool.terminal)
    ordinary_tool_calls = 0
    progress_identity = {
        target: str(request.metadata.get(source, "") or "")
        for target, source in (
            ("workspace_subsystem", "subsystem"),
            ("workspace_agent", "agent"),
            ("workspace_stage", "review_stage"),
            ("workspace_operation", "workspace_operation"),
        )
        if str(request.metadata.get(source, "") or "").strip()
    }

    def loop_error(reason: str, *, turns: int, tool_calls: int) -> ClientToolLoopError:
        return ClientToolLoopError(
            reason=reason,
            turns=turns,
            tool_calls=tool_calls,
            runtime_executed_tool_calls=runtime_executed_tool_calls,
            history=history,
            messages=messages,
            provider=(last_response.provider if last_response else str(
                getattr(backend, "provider_name", "") or "")),
            model=(last_response.model if last_response else request.model),
            final_response_metadata=last_response.metadata if last_response else {},
            observation_refs=observation_refs,
        )

    for turn_index in range(max_turns):
        turn_tools = request.tools
        turn_allowed_tools = {tool.name for tool in turn_tools}
        with agent_runtime_substage(
            "client_tool_model_turn",
            metadata={
                "turn_index": turn_index,
                "max_turns": max_turns,
                "model": request.model,
                "thinking_budget_tokens": request.thinking_budget_tokens,
                **progress_identity,
            },
        ):
            provider_failure: tuple[str, str] | None = None
            try:
                response = generate_turn(
                    replace(
                        request,
                        messages=tuple(messages),
                        tools=turn_tools,
                        metadata={
                            **dict(request.metadata),
                            "client_tool_loop_max_turns": max_turns,
                            "client_tool_loop_max_calls": max_tool_calls,
                            "client_tool_loop_calls_before": total_calls,
                            "client_tool_loop_ordinary_calls_before": ordinary_tool_calls,
                        },
                    )
                )
            except Exception as exc:
                provider_failure = (type(exc).__name__, type(exc).__module__)
            if provider_failure is not None:
                exception_type, exception_module = provider_failure
                history.append(
                    {
                        "turn_index": turn_index,
                        "provider": str(
                            getattr(backend, "provider_name", "") or ""
                        ),
                        "model": request.model,
                        "stop_reason": "provider_terminal_error",
                        "provider_output_truncated": False,
                        "n_tool_calls": 0,
                        "tool_calls": [],
                        "response_metadata": {
                            "exception_type": exception_type,
                            "exception_module": exception_module,
                            "pending_workspace_input_preserved": True,
                            "automatic_turn_restart": False,
                        },
                    }
                )
                raise loop_error(
                    "provider turn ended with "
                    f"{exception_type}; pending workspace input preserved for "
                    "explicit continuation",
                    turns=turn_index + 1,
                    tool_calls=total_calls,
                )
        if not isinstance(response, ClientToolTurnResponse):
            raise TypeError("client-tool backend returned the wrong response type")
        last_response = response
        assistant_blocks = [deepcopy(dict(block)) for block in response.content_blocks]
        messages.append({"role": "assistant", "content": assistant_blocks})
        calls = list(response.tool_calls)
        provider_stop_reason = str(response.metadata.get("provider_stop_reason", "") or "")
        provider_output_truncated = provider_stop_reason == "max_tokens"
        turn_row: dict[str, Any] = {
            "turn_index": turn_index,
            "provider": response.provider,
            "model": response.model,
            "stop_reason": provider_stop_reason,
            "provider_output_truncated": provider_output_truncated,
            "n_tool_calls": len(calls),
            "tool_calls": [],
            "response_metadata": _compact_tool_response_metadata(response.metadata),
        }
        history.append(turn_row)

        if not calls:
            reason = (
                "provider turn ended at max_tokens before a complete client tool "
                "call; pending workspace state preserved for explicit continuation"
                if provider_output_truncated
                else "model ended the workspace turn without a client tool call; "
                "pending workspace state preserved for explicit continuation"
            )
            raise loop_error(
                reason,
                turns=turn_index + 1,
                tool_calls=total_calls,
            )

        tool_result_blocks: list[dict[str, Any]] = []
        turn_state_changed = False
        turn_new_observation = False
        terminal_payload: Mapping[str, Any] | None = None
        for call_index, call in enumerate(calls):
            call_definition = tool_definitions.get(call.name)
            total_calls += 1
            context = ClientToolExecutionContext(
                turn_index=turn_index,
                call_index=call_index,
                calls_in_turn=len(calls),
                total_calls_before=total_calls - 1,
            )
            executed_by_runtime = False
            if call.name not in turn_allowed_tools:
                execution = ClientToolExecutionResult(
                    content={
                        "ok": False,
                        "error": "client_tool_unavailable_this_turn",
                        "allowed_tools": sorted(turn_allowed_tools),
                    },
                    is_error=True,
                    observation_key=(
                        "client_tool_unavailable_this_turn:" + call.name
                    ),
                )
            elif call_definition is not None and (
                not call_definition.terminal
                and ordinary_tool_calls >= max_tool_calls
            ):
                execution = ClientToolExecutionResult(
                    content={
                        "ok": False,
                        "error": "workspace_action_budget_exhausted",
                        "terminal_tools": sorted(
                            tool.name for tool in terminal_tools
                        ),
                        "detail": (
                            "The ordinary workspace-action budget is exhausted. "
                            "The tool surface remains stable, but this action was "
                            "not executed. Submit the current workspace or let the "
                            "session end as an explicit checkpoint."
                        ),
                    },
                    is_error=True,
                    observation_key=(
                        "workspace_action_budget_exhausted:" + call.name
                    ),
                )
            elif provider_output_truncated:
                execution = ClientToolExecutionResult(
                    content={
                        "ok": False,
                        "error": "provider_tool_input_truncated",
                        "provider_stop_reason": provider_stop_reason,
                        "detail": (
                            "The provider stopped at max_tokens before completing "
                            "this tool input. Retry with a smaller complete call; "
                            "the partial input was not executed."
                        ),
                    },
                    is_error=True,
                    observation_key=(
                        "provider_tool_input_truncated:" + call.name
                    ),
                )
            elif (
                tool_definitions[call.name].terminal
                and call_index != len(calls) - 1
            ):
                execution = ClientToolExecutionResult(
                    content={
                        "ok": False,
                        "error": "terminal_tool_must_be_last_in_turn",
                    },
                    is_error=True,
                    observation_key="terminal_tool_must_be_last_in_turn",
                )
            else:
                if call_definition is not None and not call_definition.terminal:
                    ordinary_tool_calls += 1
                executed_by_runtime = True
                runtime_executed_tool_calls += 1
                runtime_failure: ClientToolRuntimeError | None = None
                with agent_runtime_substage(
                    "client_tool_execution",
                    metadata={
                        "turn_index": turn_index,
                        "call_index": call_index,
                        "calls_in_turn": len(calls),
                        "tool_name": call.name,
                    },
                ) as progress_metadata:
                    try:
                        execution = (
                            _read_workspace_history(call.input, session_dir=session_dir,
                                session_id=session_id, request=request, observation_refs=observation_refs)
                            if history_enabled and call.name == WORKSPACE_HISTORY_TOOL_NAME
                            else execute_tool(call, context)
                        )
                    except ClientToolInputError as exc:
                        execution = ClientToolExecutionResult(
                            content={
                                "ok": False,
                                "error": "client_tool_input_rejected",
                                "exception_type": type(exc).__name__,
                                "detail": str(exc),
                            },
                            is_error=True,
                            observation_key=(
                                "client_tool_input_rejected:"
                                + stable_hash(
                                    [call.name, type(exc).__name__, str(exc)]
                                )
                            ),
                        )
                    except Exception as exc:
                        execution = ClientToolExecutionResult(
                            content={
                                "ok": False,
                                "error": "client_tool_internal_failure",
                                "exception_type": type(exc).__name__,
                                "detail_withheld": True,
                            },
                            is_error=True,
                            observation_key=(
                                "client_tool_internal_failure:"
                                + stable_hash([call.name, type(exc).__name__])
                            ),
                        )
                        result_text, model_observation_complete = (
                            _client_tool_result_for_model(execution.content)
                        )
                        turn_row["tool_calls"].append(
                            {
                                "call_index": call_index,
                                "call_id": call.call_id,
                                "name": call.name,
                                "input_fingerprint": stable_hash(dict(call.input)),
                                "result_fingerprint": stable_hash(
                                    [execution.is_error, execution.content]
                                ),
                                "result_excerpt": result_text[:2000],
                                "is_error": True,
                                "model_observation_complete": (
                                    model_observation_complete
                                ),
                                "executed_by_runtime": True,
                                "state_changed": False,
                                "terminal": False,
                                "observation_key": execution.observation_key,
                            }
                        )
                        runtime_failure = ClientToolRuntimeError(
                            tool_name=call.name,
                            turn_index=turn_index,
                            call_index=call_index,
                            exception_type=type(exc).__name__,
                            turns=turn_index + 1,
                            tool_calls=total_calls,
                            runtime_executed_tool_calls=(
                                runtime_executed_tool_calls
                            ),
                            history=history,
                            messages=messages,
                            provider=response.provider,
                            model=response.model,
                            final_response_metadata=response.metadata,
                            observation_refs=observation_refs,
                        )
                    if isinstance(progress_metadata, dict):
                        progress_metadata.update(
                            {
                                "tool_result_is_error": bool(execution.is_error),
                                "tool_state_changed": bool(execution.state_changed),
                                "tool_terminal": bool(execution.terminal),
                            }
                        )
                    if runtime_failure is not None:
                        raise runtime_failure
            if execution.terminal and not tool_definitions[call.name].terminal:
                execution = ClientToolExecutionResult(
                    content={
                        "ok": False,
                        "error": "terminal_result_from_nonterminal_tool",
                    },
                    is_error=True,
                    observation_key="terminal_result_from_nonterminal_tool",
                )
            observation_key = execution.observation_key or stable_hash(
                [call.name, execution.is_error, execution.content,
                 execution.model_content_blocks]
            )
            observation_is_new = observation_key not in seen_observations
            if observation_is_new:
                turn_new_observation = True
                seen_observations.add(observation_key)
            turn_state_changed = turn_state_changed or execution.state_changed
            result_text, model_observation_complete = (
                _client_tool_result_for_model(execution.content)
            )
            observation_ref = {}
            if history_enabled and call.name != WORKSPACE_HISTORY_TOOL_NAME:
                try:
                    observation_ref = _persist_workspace_observation(session_dir, call, execution)
                except (OSError, ValueError, TypeError):
                    raise loop_error("workspace observation persistence failed; explicit continuation required",
                                     turns=turn_index + 1, tool_calls=total_calls) from None
                observation_refs.append(observation_ref)
                if not model_observation_complete:
                    result_text = json.dumps({
                        **json.loads(result_text),
                        "workspace_history": {"observation_sha256": observation_ref["sha256"]},
                        "read_tool": WORKSPACE_HISTORY_TOOL_NAME,
                    }, sort_keys=True, separators=(",", ":"))
            model_result_is_error = bool(
                execution.is_error or not model_observation_complete
            )
            model_content = (
                [{"type": "text", "text": result_text},
                 *deepcopy(list(execution.model_content_blocks))]
                if model_observation_complete and execution.model_content_blocks
                else result_text
            )
            tool_result_blocks.append(
                {
                    "type": "tool_result",
                    "tool_use_id": call.call_id,
                    "content": model_content,
                    "is_error": model_result_is_error,
                }
            )
            turn_row["tool_calls"].append(
                {
                    "call_index": call_index,
                    "call_id": call.call_id,
                    "name": call.name,
                    "input_fingerprint": stable_hash(dict(call.input)),
                    "result_fingerprint": stable_hash(
                        [execution.is_error, execution.content,
                         execution.model_content_blocks]
                    ),
                    "result_excerpt": result_text[:2000],
                    "is_error": model_result_is_error,
                    "model_observation_complete": model_observation_complete,
                    "executed_by_runtime": executed_by_runtime,
                    "state_changed": bool(execution.state_changed),
                    "terminal": bool(execution.terminal),
                    "observation_key": observation_key,
                    **({"observation_ref": observation_ref} if observation_ref else {}),
                }
            )
            if execution.terminal:
                if not isinstance(execution.terminal_payload, Mapping):
                    raise loop_error(
                        "terminal client tool returned no payload",
                        turns=turn_index + 1,
                        tool_calls=total_calls,
                    )
                terminal_payload = deepcopy(dict(execution.terminal_payload))

        messages.append({"role": "user", "content": tool_result_blocks})
        if terminal_payload is not None:
            return ClientToolLoopResult(
                terminal_payload=terminal_payload,
                messages=tuple(messages),
                history=tuple(history),
                provider=response.provider,
                model=response.model,
                turns=turn_index + 1,
                tool_calls=total_calls,
                runtime_executed_tool_calls=runtime_executed_tool_calls,
                transcript_fingerprint=stable_hash(messages),
                provider_usage=_provider_usage_totals(history),
                final_response_metadata=deepcopy(dict(response.metadata)),
                observation_refs=tuple(observation_refs),
            )

        if turn_state_changed or turn_new_observation:
            no_progress_turns = 0
        else:
            no_progress_turns += 1
        if no_progress_turns >= max_no_progress_turns:
            raise loop_error(
                "repeated client-tool turns made no new progress",
                turns=turn_index + 1,
                tool_calls=total_calls,
            )

    raise loop_error(
        (
            "client-tool turn budget exhausted before a terminal disposition"
            if terminal_tools
            else "client-tool turn budget exhausted"
        ),
        turns=len(history),
        tool_calls=total_calls,
    )


def _client_tool_result_text(
    value: Any, *, max_chars: int = CLIENT_TOOL_RESULT_MAX_CHARS
) -> str:
    return _client_tool_result_for_model(value, max_chars=max_chars)[0]


def _client_tool_result_for_model(
    value: Any, *, max_chars: int = CLIENT_TOOL_RESULT_MAX_CHARS
) -> tuple[str, bool]:
    """Keep one model observation complete or omit its payload atomically."""

    if isinstance(max_chars, bool) or max_chars < 256:
        raise ValueError("client tool result boundary must be at least 256 characters")
    if isinstance(value, str):
        serialized = value
    else:
        serialized = json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            default=str,
            ensure_ascii=False,
        )
    if len(serialized) <= max_chars:
        return serialized, True
    envelope = json.dumps(
        {
            "content_omitted_atomically": True,
            "detail": (
                "The complete tool observation exceeded the model boundary. "
                "No partial payload was delivered; use a narrower read or "
                "inspection action and do not infer success or authorization."
            ),
            "error": "client_tool_observation_exceeds_boundary",
            "observation_complete": False,
            "ok": False,
            "original_chars": len(serialized),
            "original_lines": len(serialized.splitlines()),
            "original_sha256": hashlib.sha256(
                serialized.encode("utf-8")
            ).hexdigest(),
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    if len(envelope) > max_chars:
        raise ValueError("client tool result boundary cannot hold its omission envelope")
    return envelope, False


def _compact_tool_response_metadata(
    metadata: Mapping[str, Any],
) -> dict[str, Any]:
    keys = (
        "client_tool_transport",
        "tools_executed_by_backend",
        "n_client_tool_calls",
        "provider_stop_reason",
        "provider_usage",
        "provider_usage_complete",
        "server_timings",
        "local_model_request_index",
        "prompt_caching_requested",
        "prompt_caching_applied",
        "retry_count",
        "provider_capability_fallback_count",
        "requested_model",
        "provider_reported_model",
        "request_model_tier",
        "provider_reported_model_tier",
    )
    return {
        key: deepcopy(metadata[key])
        for key in keys
        if key in metadata
    }


def _provider_usage_totals(
    history: list[Mapping[str, Any]] | tuple[Mapping[str, Any], ...],
) -> dict[str, int]:
    totals: dict[str, int] = {}
    for turn in history:
        metadata = turn.get("response_metadata", {})
        usage = (
            metadata.get("provider_usage", {})
            if isinstance(metadata, Mapping)
            else {}
        )
        if not isinstance(usage, Mapping):
            continue
        for key in (
            "input_tokens",
            "output_tokens",
            "cache_creation_input_tokens",
            "cache_read_input_tokens",
            "total_tokens",
        ):
            value = usage.get(key)
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                continue
            totals[key] = totals.get(key, 0) + max(0, int(value))
    return totals
