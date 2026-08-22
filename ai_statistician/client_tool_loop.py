from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from dataclasses import dataclass, field, replace
from pathlib import Path, PurePosixPath
from typing import Any, Callable, Mapping, Sequence

from .agent_runtime import agent_runtime_substage
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
        super().__init__(
            f"bounded client-tool loop stopped after {turns} turn(s) and "
            f"{tool_calls} call(s): {reason}"
        )


class ClientToolInputError(ValueError):
    """A caller-reviewed tool error whose bounded detail is safe for the model."""


class ClientToolRuntimeError(RuntimeError):
    """A non-model-actionable tool failure with secret-free diagnostics."""

    def __init__(
        self,
        *,
        tool_name: str,
        turn_index: int,
        call_index: int,
        exception_type: str,
    ) -> None:
        self.tool_name = str(tool_name)
        self.turn_index = int(turn_index)
        self.call_index = int(call_index)
        self.exception_type = str(exception_type)
        super().__init__(
            "client tool runtime failed outside the model-actionable boundary: "
            f"{self.tool_name} raised {self.exception_type} at turn "
            f"{self.turn_index}, call {self.call_index}; detail withheld"
        )


ClientToolExecutor = Callable[
    [ClientToolCall, ClientToolExecutionContext],
    ClientToolExecutionResult,
]


CLIENT_TOOL_SESSION_KIND = "ClientToolWorkspaceSession"
CLIENT_TOOL_SESSION_DIRECTORY = ".client_tool_sessions"


def client_tool_session_contract_fingerprint(
    request: ClientToolTurnRequest,
) -> str:
    """Bind a resumable transcript to one model, system prompt, and tool surface."""

    return stable_hash(
        {
            "contract_schema_version": 2,
            "model": request.model,
            "system_prompt": request.system_prompt,
            "tools": [
                {
                    "name": tool.name,
                    "description": tool.description,
                    "input_schema": deepcopy(dict(tool.input_schema)),
                    "terminal": tool.terminal,
                    "strict": tool.strict,
                }
                for tool in request.tools
            ],
        }
    )


def persist_client_tool_session(
    *,
    session_dir: Path | None,
    session_id: str,
    request: ClientToolTurnRequest,
    messages: Sequence[Mapping[str, Any]],
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
    transcript_fingerprint = stable_hash(normalized_messages)
    session_contract_fingerprint = client_tool_session_contract_fingerprint(
        request
    )
    body = {
        "schema_version": 2,
        "artifact_kind": CLIENT_TOOL_SESSION_KIND,
        "session_id": normalized_session_id,
        "root_path": str(root),
        "session_contract_fingerprint": session_contract_fingerprint,
        "transcript_fingerprint": transcript_fingerprint,
        "message_count": len(normalized_messages),
        "messages": normalized_messages,
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
        "schema_version": 2,
        "artifact_kind": "ClientToolWorkspaceSessionRef",
        "session_id": normalized_session_id,
        "root_path": str(root),
        "relative_path": relative_path.as_posix(),
        "sha256": sha256,
        "message_count": len(normalized_messages),
        "transcript_fingerprint": transcript_fingerprint,
        "session_contract_fingerprint": session_contract_fingerprint,
    }


def load_client_tool_session(
    reference: Mapping[str, Any],
    *,
    session_dir: Path,
    session_id: str,
    request: ClientToolTurnRequest,
) -> tuple[Mapping[str, Any], ...]:
    """Load a transcript only when its workspace and tool contract still match."""

    ref = dict(reference)
    normalized_session_id = str(session_id or "").strip()
    expected_contract = client_tool_session_contract_fingerprint(request)
    root = session_dir.resolve()
    relative_path = PurePosixPath(str(ref.get("relative_path", "") or ""))
    if (
        int(ref.get("schema_version", 0) or 0) != 2
        or ref.get("artifact_kind") != "ClientToolWorkspaceSessionRef"
        or str(ref.get("session_id", "") or "") != normalized_session_id
        or str(ref.get("root_path", "") or "") != str(root)
        or str(ref.get("session_contract_fingerprint", "") or "")
        != expected_contract
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
        and int(payload.get("schema_version", 0) or 0) == 2
        and payload.get("artifact_kind") == CLIENT_TOOL_SESSION_KIND
        and payload.get("session_id") == normalized_session_id
        and payload.get("root_path") == str(root)
        and payload.get("session_contract_fingerprint") == expected_contract
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
    return tuple(deepcopy(dict(message)) for message in messages)


def run_bounded_client_tool_loop(
    *,
    backend: Any,
    request: ClientToolTurnRequest,
    execute_tool: ClientToolExecutor,
    max_turns: int,
    max_tool_calls: int,
    max_no_progress_turns: int,
    max_terminal_recovery_turns: int = 0,
) -> ClientToolLoopResult:
    """Run model -> client tool -> observation turns under caller-owned bounds.

    ``max_tool_calls`` bounds ordinary workspace actions. When terminal tools are
    available, the loop separately reserves one same-model terminal disposition
    plus ``max_terminal_recovery_turns`` rejected-disposition retries. It does not
    invoke a separate repair agent.
    """

    if max_turns < 1 or max_tool_calls < 1 or max_no_progress_turns < 1:
        raise ValueError("client-tool loop budgets must all be positive")
    if max_terminal_recovery_turns < 0:
        raise ValueError("terminal recovery turn budget cannot be negative")
    generate_turn = getattr(backend, "generate_client_tool_turn", None)
    if not callable(generate_turn):
        raise ValueError("backend does not support client-tool turns")
    allowed_tool_names = [tool.name for tool in request.tools]
    if (
        not allowed_tool_names
        or any(not str(name).strip() for name in allowed_tool_names)
        or len(set(allowed_tool_names)) != len(allowed_tool_names)
    ):
        raise ValueError("client-tool definitions must have unique nonempty names")
    tool_definitions = {tool.name: tool for tool in request.tools}
    messages = [deepcopy(dict(message)) for message in request.messages]
    history: list[dict[str, Any]] = []
    seen_observations: set[str] = set()
    total_calls = 0
    runtime_executed_tool_calls = 0
    no_progress_turns = 0
    last_response: ClientToolTurnResponse | None = None
    terminal_tools = tuple(tool for tool in request.tools if tool.terminal)
    terminal_decision_budget = (
        1 + max_terminal_recovery_turns if terminal_tools else 0
    )
    total_turn_budget = max_turns + terminal_decision_budget
    standard_tool_calls = 0
    terminal_decision_tool_calls = 0
    terminal_decision_pending = False
    terminal_decision_reason = ""
    terminal_decision_turns_used = 0

    def request_terminal_decision(reason: str) -> None:
        nonlocal terminal_decision_pending, terminal_decision_reason
        terminal_decision_pending = True
        terminal_decision_reason = str(reason)
        instruction = (
            "The bounded workspace must now make its final disposition from the "
            "observations already gathered. On the next turn, call one of the "
            "supplied terminal tools. Do not request more context or answer only "
            "in prose."
        )
        last_message = deepcopy(dict(messages[-1]))
        content = last_message.get("content", "")
        if isinstance(content, list):
            last_message["content"] = [
                *deepcopy(content),
                {"type": "text", "text": instruction},
            ]
        else:
            last_message["content"] = str(content) + "\n\n" + instruction
        messages[-1] = last_message

    def loop_error(
        reason: str,
        *,
        turns: int,
        tool_calls: int,
    ) -> ClientToolLoopError:
        return ClientToolLoopError(
            reason=reason,
            turns=turns,
            tool_calls=tool_calls,
            runtime_executed_tool_calls=runtime_executed_tool_calls,
            history=history,
            messages=messages,
            provider=(last_response.provider if last_response else ""),
            model=(last_response.model if last_response else request.model),
            final_response_metadata=(
                last_response.metadata if last_response else {}
            ),
        )

    for turn_index in range(total_turn_budget):
        terminal_decision_turn = bool(
            terminal_tools
            and terminal_decision_turns_used < terminal_decision_budget
            and (terminal_decision_pending or turn_index >= max_turns)
        )
        if turn_index >= max_turns and not terminal_decision_turn:
            break
        if terminal_decision_turn:
            if not terminal_decision_pending:
                request_terminal_decision("standard client-tool turn budget exhausted")
            terminal_decision_pending = False
            terminal_decision_turns_used += 1
        # Keep one stable tool definition surface across the whole transcript so
        # provider prompt caches retain the accumulated workspace prefix. The
        # runtime still rejects nonterminal calls once final disposition is due.
        turn_tools = request.tools
        terminal_only_turn = bool(
            turn_tools and all(tool.terminal for tool in turn_tools)
        )
        turn_allowed_tools = {tool.name for tool in turn_tools}
        with agent_runtime_substage(
            "client_tool_model_turn",
            metadata={
                "turn_index": turn_index,
                "max_turns": max_turns,
                "max_terminal_recovery_turns": max_terminal_recovery_turns,
                "max_total_turns": total_turn_budget,
                "model_tool_calls_before": total_calls,
                "max_model_tool_calls": max_tool_calls,
                "standard_model_tool_calls_before": standard_tool_calls,
                "max_standard_model_tool_calls": max_tool_calls,
                "terminal_decision_tool_calls_before": (
                    terminal_decision_tool_calls
                ),
                "max_terminal_decision_tool_calls": terminal_decision_budget,
                "model": request.model,
                "n_available_tools": len(turn_tools),
                "terminal_only_turn": terminal_only_turn,
                "terminal_decision_turn": terminal_decision_turn,
                "n_transcript_messages": len(messages),
                "n_model_context_messages": len(messages),
                "terminal_decision_reason": (
                    terminal_decision_reason if terminal_decision_turn else ""
                ),
            },
        ):
            response = generate_turn(
                replace(
                    request,
                    messages=tuple(messages),
                    tools=turn_tools,
                    tool_choice=(
                        turn_tools[0].name
                        if terminal_only_turn and len(turn_tools) == 1
                        else request.tool_choice
                    ),
                    disable_parallel_tool_use=(
                        True
                        if terminal_only_turn or terminal_decision_turn
                        else request.disable_parallel_tool_use
                    ),
                    metadata={
                        **dict(request.metadata),
                        "client_tool_loop_turn_index": turn_index,
                        "client_tool_loop_max_turns": max_turns,
                        "client_tool_loop_max_terminal_recovery_turns": (
                            max_terminal_recovery_turns
                        ),
                        "client_tool_loop_max_total_turns": total_turn_budget,
                        "client_tool_loop_calls_before": total_calls,
                        "client_tool_loop_max_calls": max_tool_calls,
                        "client_tool_loop_standard_calls_before": (
                            standard_tool_calls
                        ),
                        "client_tool_loop_max_standard_calls": max_tool_calls,
                        "client_tool_loop_terminal_calls_before": (
                            terminal_decision_tool_calls
                        ),
                        "client_tool_loop_max_terminal_calls": (
                            terminal_decision_budget
                        ),
                        "client_tool_loop_terminal_only_turn": (
                            terminal_only_turn
                        ),
                        "client_tool_loop_terminal_decision_turn": (
                            terminal_decision_turn
                        ),
                        "client_tool_loop_terminal_decision_reason": (
                            terminal_decision_reason
                            if terminal_decision_turn
                            else ""
                        ),
                    },
                )
            )
        if not isinstance(response, ClientToolTurnResponse):
            raise TypeError(
                "client-tool backend returned the wrong response type"
            )
        last_response = response
        assistant_blocks = [
            deepcopy(dict(block)) for block in response.content_blocks
        ]
        messages.append({"role": "assistant", "content": assistant_blocks})
        calls = list(response.tool_calls)
        provider_stop_reason = str(
            response.metadata.get("provider_stop_reason", "") or ""
        )
        provider_output_truncated = provider_stop_reason == "max_tokens"
        turn_row: dict[str, Any] = {
            "turn_index": turn_index,
            "provider": response.provider,
            "model": response.model,
            "stop_reason": provider_stop_reason,
            "provider_output_truncated": provider_output_truncated,
            "n_tool_calls": len(calls),
            "tool_calls": [],
            "response_metadata": _compact_tool_response_metadata(
                response.metadata
            ),
        }
        history.append(turn_row)

        if not calls:
            observation_key = (
                "provider_tool_output_truncated"
                if provider_output_truncated
                else "no_tool_call:" + stable_hash([response.text, assistant_blocks])
            )
            new_observation = observation_key not in seen_observations
            seen_observations.add(observation_key)
            no_progress_turns = (
                0 if new_observation else no_progress_turns + 1
            )
            messages.append(
                {
                    "role": "user",
                    "content": (
                        "The provider stopped at max_tokens before completing a "
                        "client-tool call. Retry with a smaller complete tool input."
                        if provider_output_truncated
                        else (
                            "No client tool was called. Continue by calling one of "
                            "the supplied tools; prose alone cannot change or submit "
                            "the runtime artifact."
                        )
                    ),
                }
            )
            if terminal_decision_turn:
                if terminal_decision_turns_used < terminal_decision_budget:
                    request_terminal_decision(
                        terminal_decision_reason
                        or "terminal client-tool turn omitted its decision"
                    )
                    no_progress_turns = 0
                    continue
                raise loop_error(
                    (
                        terminal_decision_reason + "; "
                        if terminal_decision_reason
                        else ""
                    )
                    + "terminal client-tool turn omitted its decision",
                    turns=turn_index + 1,
                    tool_calls=total_calls,
                )
            if no_progress_turns >= max_no_progress_turns:
                if (
                    terminal_tools
                    and terminal_decision_turns_used
                    < terminal_decision_budget
                ):
                    request_terminal_decision(
                        "repeated turns without a client tool call"
                    )
                    no_progress_turns = 0
                    continue
                raise loop_error(
                    "repeated turns without a client tool call",
                    turns=turn_index + 1,
                    tool_calls=total_calls,
                )
            continue

        tool_result_blocks: list[dict[str, Any]] = []
        turn_state_changed = False
        turn_new_observation = False
        terminal_payload: Mapping[str, Any] | None = None
        for call_index, call in enumerate(calls):
            if terminal_decision_turn:
                if terminal_decision_tool_calls >= terminal_decision_budget:
                    raise loop_error(
                        "terminal client-tool call budget exhausted",
                        turns=turn_index + 1,
                        tool_calls=total_calls,
                    )
                terminal_decision_tool_calls += 1
            else:
                if standard_tool_calls >= max_tool_calls:
                    raise loop_error(
                        "standard client-tool call budget exhausted",
                        turns=turn_index + 1,
                        tool_calls=total_calls,
                    )
                standard_tool_calls += 1
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
            elif (
                terminal_decision_turn
                and not tool_definitions[call.name].terminal
            ):
                execution = ClientToolExecutionResult(
                    content={
                        "ok": False,
                        "error": "final_disposition_requires_terminal_tool",
                        "terminal_tools": sorted(
                            tool.name for tool in terminal_tools
                        ),
                        "detail": (
                            "The standard workspace budget is exhausted. Use one "
                            "of the supplied terminal tools for the final "
                            "disposition; nonterminal tools remain visible only to "
                            "preserve the stable model tool surface."
                        ),
                    },
                    is_error=True,
                    observation_key=(
                        "final_disposition_requires_terminal_tool:" + call.name
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
                        execution = execute_tool(call, context)
                    except ClientToolInputError as exc:
                        execution = ClientToolExecutionResult(
                            content={
                                "ok": False,
                                "error": "client_tool_input_rejected",
                                "exception_type": type(exc).__name__,
                                "detail": str(exc)[:1200],
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
                        runtime_failure = ClientToolRuntimeError(
                            tool_name=call.name,
                            turn_index=turn_index,
                            call_index=call_index,
                            exception_type=type(exc).__name__,
                        )
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
                [call.name, execution.is_error, execution.content]
            )
            if observation_key not in seen_observations:
                turn_new_observation = True
                seen_observations.add(observation_key)
            turn_state_changed = (
                turn_state_changed or execution.state_changed
            )
            model_result_content = _client_tool_result_with_budget(
                execution.content,
                turn_index=turn_index,
                max_turns=max_turns,
                standard_tool_calls=standard_tool_calls,
                max_tool_calls=max_tool_calls,
                terminal_decision_tool_calls=terminal_decision_tool_calls,
                terminal_decision_budget=terminal_decision_budget,
                final_disposition_required=(
                    terminal_decision_turn
                    or bool(
                        terminal_tools
                        and standard_tool_calls >= max_tool_calls
                    )
                ),
            )
            result_text = _client_tool_result_text(model_result_content)
            tool_result_blocks.append(
                {
                    "type": "tool_result",
                    "tool_use_id": call.call_id,
                    "content": result_text,
                    "is_error": bool(execution.is_error),
                }
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
                    "is_error": bool(execution.is_error),
                    "executed_by_runtime": executed_by_runtime,
                    "state_changed": bool(execution.state_changed),
                    "terminal": bool(execution.terminal),
                    "observation_key": observation_key,
                }
            )
            if execution.terminal:
                if not isinstance(execution.terminal_payload, Mapping):
                    raise loop_error(
                        "terminal client tool returned no payload",
                        turns=turn_index + 1,
                        tool_calls=total_calls,
                    )
                terminal_payload = deepcopy(
                    dict(execution.terminal_payload)
                )

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
            )

        if (
            not terminal_decision_turn
            and terminal_tools
            and standard_tool_calls >= max_tool_calls
        ):
            request_terminal_decision(
                "standard client-tool call budget exhausted"
            )
            no_progress_turns = 0
            continue

        if turn_state_changed or turn_new_observation:
            no_progress_turns = 0
        else:
            no_progress_turns += 1
        if terminal_decision_turn:
            if terminal_decision_turns_used < terminal_decision_budget:
                request_terminal_decision(
                    terminal_decision_reason
                    or "terminal client-tool decision was not accepted"
                )
                no_progress_turns = 0
                continue
            raise loop_error(
                (
                    terminal_decision_reason + "; "
                    if terminal_decision_reason
                    else ""
                )
                + "terminal client-tool decision did not produce an accepted payload",
                turns=turn_index + 1,
                tool_calls=total_calls,
            )
        if no_progress_turns >= max_no_progress_turns:
            if (
                terminal_tools
                and terminal_decision_turns_used < terminal_decision_budget
            ):
                request_terminal_decision(
                    "repeated client-tool turns made no new progress"
                )
                no_progress_turns = 0
                continue
            raise loop_error(
                "repeated client-tool turns made no new progress",
                turns=turn_index + 1,
                tool_calls=total_calls,
            )

    raise loop_error(
        "global client-tool turn budget exhausted",
        turns=len(history),
        tool_calls=total_calls,
    )


def _client_tool_result_text(value: Any, *, max_chars: int = 60000) -> str:
    if isinstance(value, str):
        text = value
    else:
        text = json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            default=str,
            ensure_ascii=False,
        )
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "\n[tool result truncated by runtime]"


def _client_tool_result_with_budget(
    value: Any,
    *,
    turn_index: int,
    max_turns: int,
    standard_tool_calls: int,
    max_tool_calls: int,
    terminal_decision_tool_calls: int,
    terminal_decision_budget: int,
    final_disposition_required: bool,
) -> Any:
    """Expose only generic remaining workspace budget in the next observation."""

    if not isinstance(value, Mapping):
        return value
    return {
        **deepcopy(dict(value)),
        "_client_tool_budget": {
            "standard_turns_remaining_after_current_turn": max(
                0, max_turns - turn_index - 1
            ),
            "model_tool_calls_remaining_after_current_call": max(
                0, max_tool_calls - standard_tool_calls
            ),
            "terminal_disposition_calls_remaining_after_current_call": max(
                0,
                terminal_decision_budget - terminal_decision_tool_calls,
            ),
            "final_disposition_required": bool(final_disposition_required),
        },
    }


def _compact_tool_response_metadata(
    metadata: Mapping[str, Any],
) -> dict[str, Any]:
    keys = (
        "client_tool_transport",
        "tools_executed_by_backend",
        "n_client_tool_calls",
        "provider_stop_reason",
        "provider_usage",
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
