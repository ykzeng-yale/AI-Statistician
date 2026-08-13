from __future__ import annotations

import json
from copy import deepcopy
from dataclasses import dataclass, field, replace
from typing import Any, Callable, Mapping

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


ClientToolExecutor = Callable[
    [ClientToolCall, ClientToolExecutionContext],
    ClientToolExecutionResult,
]
ClientToolSelector = Callable[
    [int, tuple[ClientToolDefinition, ...]],
    tuple[ClientToolDefinition, ...],
]
WorkspaceSnapshotBuilder = Callable[[int], Mapping[str, Any] | None]


def run_bounded_client_tool_loop(
    *,
    backend: Any,
    request: ClientToolTurnRequest,
    execute_tool: ClientToolExecutor,
    max_turns: int,
    max_tool_calls: int,
    max_no_progress_turns: int,
    max_terminal_recovery_turns: int = 0,
    select_tools: ClientToolSelector | None = None,
    max_retained_tool_turns: int | None = None,
    build_workspace_snapshot: WorkspaceSnapshotBuilder | None = None,
) -> ClientToolLoopResult:
    """Run model -> client tool -> observation turns under caller-owned bounds.

    A positive ``max_terminal_recovery_turns`` enables one same-model terminal
    disposition plus that many rejected-disposition retries. It does not invoke a
    separate repair agent.
    """

    if max_turns < 1 or max_tool_calls < 1 or max_no_progress_turns < 1:
        raise ValueError("client-tool loop budgets must all be positive")
    if max_terminal_recovery_turns < 0:
        raise ValueError("terminal recovery turn budget cannot be negative")
    if max_retained_tool_turns is not None and max_retained_tool_turns < 1:
        raise ValueError("retained client-tool turn budget must be positive")
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
        1 + max_terminal_recovery_turns
        if terminal_tools and max_terminal_recovery_turns
        else 0
    )
    total_turn_budget = max_turns + terminal_decision_budget
    terminal_decision_pending = False
    terminal_decision_reason = ""
    terminal_decision_turns_used = 0
    initial_message_count = len(messages)

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
            turn_tools = terminal_tools
        elif select_tools is None:
            turn_tools = request.tools
        else:
            turn_tools = tuple(select_tools(turn_index, request.tools))
            selected_names = [tool.name for tool in turn_tools]
            if (
                not selected_names
                or len(set(selected_names)) != len(selected_names)
                or any(name not in tool_definitions for name in selected_names)
            ):
                raise ValueError(
                    "client-tool selector must return a nonempty subset of "
                    "the request tools"
                )
            turn_tools = tuple(
                tool_definitions[name] for name in selected_names
            )
        terminal_only_turn = bool(
            turn_tools and all(tool.terminal for tool in turn_tools)
        )
        turn_allowed_tools = {tool.name for tool in turn_tools}
        model_messages = messages
        if max_retained_tool_turns is not None and turn_index > 0:
            interaction_messages = messages[initial_message_count:]
            model_messages = [
                *messages[:initial_message_count],
                *interaction_messages[-2 * max_retained_tool_turns :],
            ]
        workspace_snapshot: Mapping[str, Any] | None = None
        if build_workspace_snapshot is not None:
            workspace_snapshot = build_workspace_snapshot(
                max_turns if terminal_decision_turn else turn_index
            )
            if workspace_snapshot is not None:
                model_messages = _with_workspace_snapshot(
                    model_messages,
                    initial_message_count=initial_message_count,
                    snapshot=workspace_snapshot,
                )
        with agent_runtime_substage(
            "client_tool_model_turn",
            metadata={
                "turn_index": turn_index,
                "max_turns": max_turns,
                "max_terminal_recovery_turns": max_terminal_recovery_turns,
                "max_total_turns": total_turn_budget,
                "model_tool_calls_before": total_calls,
                "max_model_tool_calls": max_tool_calls,
                "model": request.model,
                "n_available_tools": len(turn_tools),
                "terminal_only_turn": terminal_only_turn,
                "n_transcript_messages": len(messages),
                "n_model_context_messages": len(model_messages),
                "max_retained_tool_turns": max_retained_tool_turns,
                "workspace_snapshot_supplied": workspace_snapshot is not None,
                "terminal_decision_reason": (
                    terminal_decision_reason if terminal_decision_turn else ""
                ),
                "workspace_snapshot_fingerprint": (
                    stable_hash(workspace_snapshot)
                    if workspace_snapshot is not None
                    else ""
                ),
            },
        ):
            response = generate_turn(
                replace(
                    request,
                    messages=tuple(model_messages),
                    tools=turn_tools,
                    tool_choice=(
                        turn_tools[0].name
                        if terminal_only_turn and len(turn_tools) == 1
                        else request.tool_choice
                    ),
                    disable_parallel_tool_use=(
                        True
                        if terminal_only_turn
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
                        "client_tool_loop_terminal_only_turn": (
                            terminal_only_turn
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
        turn_row: dict[str, Any] = {
            "turn_index": turn_index,
            "provider": response.provider,
            "model": response.model,
            "stop_reason": str(
                response.metadata.get("provider_stop_reason", "") or ""
            ),
            "n_tool_calls": len(calls),
            "tool_calls": [],
            "response_metadata": _compact_tool_response_metadata(
                response.metadata
            ),
        }
        history.append(turn_row)

        if not calls:
            observation_key = "no_tool_call:" + stable_hash(
                [response.text, assistant_blocks]
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
                        "No client tool was called. Continue by calling one of "
                        "the supplied tools; prose alone cannot change or submit "
                        "the runtime artifact."
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
            if (
                not terminal_decision_turn
                and call.name in tool_definitions
                and tool_definitions[call.name].terminal
            ):
                # A submission in the standard loop is the initial disposition;
                # only the explicitly budgeted recovery turns remain afterward.
                terminal_decision_turns_used = max(
                    1,
                    terminal_decision_turns_used,
                )
            total_calls += 1
            if total_calls > max_tool_calls:
                raise loop_error(
                    "global client-tool call budget exhausted",
                    turns=turn_index + 1,
                    tool_calls=total_calls - 1,
                )
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
            result_text = _client_tool_result_text(execution.content)
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


def _with_workspace_snapshot(
    messages: list[Mapping[str, Any]],
    *,
    initial_message_count: int,
    snapshot: Mapping[str, Any],
) -> list[Mapping[str, Any]]:
    """Inject one current-state view without retaining another history copy."""

    if initial_message_count < 1 or len(messages) < initial_message_count:
        raise ValueError("workspace snapshot requires an initial model message")
    result = [deepcopy(dict(message)) for message in messages]
    message = result[initial_message_count - 1]
    if str(message.get("role", "") or "") != "user":
        raise ValueError("workspace snapshot requires a final initial user message")
    snapshot_text = (
        "\n\n<CURRENT_WORKSPACE_SNAPSHOT>\n"
        + json.dumps(
            snapshot,
            sort_keys=True,
            separators=(",", ":"),
            default=str,
            ensure_ascii=False,
        )
        + "\n</CURRENT_WORKSPACE_SNAPSHOT>"
    )
    content = message.get("content", "")
    if isinstance(content, str):
        message["content"] = content + snapshot_text
    elif isinstance(content, (list, tuple)):
        message["content"] = [
            *[deepcopy(dict(block)) for block in content],
            {"type": "text", "text": snapshot_text},
        ]
    else:
        raise ValueError("workspace snapshot requires string or block-list content")
    return result


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
