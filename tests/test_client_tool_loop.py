from __future__ import annotations

import json
from contextlib import contextmanager
from dataclasses import replace

import pytest

from ai_statistician.client_tool_loop import (
    CLIENT_TOOL_AUTHORIZATION_FINGERPRINT_METADATA_KEY,
    CLIENT_TOOL_CHECKPOINT_WINDOW_POLICY,
    CLIENT_TOOL_RECENT_HISTORY_WINDOW_POLICY,
    CLIENT_TOOL_TRANSCRIPT_POLICY,
    ClientToolExecutionResult,
    ClientToolInputError,
    ClientToolLoopError,
    ClientToolRuntimeError,
    apply_model_exact_text_edits,
    model_exact_text_edit_json_schema,
    model_exact_text_edits_json_schema,
    load_client_tool_session,
    persist_client_tool_session,
    resume_client_tool_session_from_checkpoint,
    run_bounded_client_tool_loop,
)
from ai_statistician import client_tool_loop
from ai_statistician.model_backend import (
    ClientToolCall,
    ClientToolDefinition,
    ClientToolTurnRequest,
    ClientToolTurnResponse,
    LiveGeneratorTimeoutError,
)


class ScriptedToolTurnBackend:
    provider_name = "scripted_tool_turn"

    def __init__(
        self,
        responses: list[ClientToolTurnResponse | Exception],
    ) -> None:
        self.responses = list(responses)
        self.requests: list[ClientToolTurnRequest] = []

    def generate_client_tool_turn(
        self,
        request: ClientToolTurnRequest,
    ) -> ClientToolTurnResponse:
        self.requests.append(request)
        if not self.responses:
            raise AssertionError("ScriptedToolTurnBackend exhausted")
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


def _tool(name: str, *, terminal: bool = False) -> ClientToolDefinition:
    return ClientToolDefinition(
        name=name,
        description=f"Execute {name}.",
        input_schema={
            "type": "object",
            "additionalProperties": False,
            "properties": {},
        },
        terminal=terminal,
    )


def _response(
    *calls: ClientToolCall,
    text: str = "",
    stop_reason: str = "tool_use",
) -> ClientToolTurnResponse:
    blocks = []
    if text:
        blocks.append({"type": "text", "text": text})
    blocks.extend(
        {
            "type": "tool_use",
            "id": call.call_id,
            "name": call.name,
            "input": dict(call.input),
        }
        for call in calls
    )
    return ClientToolTurnResponse(
        content_blocks=tuple(blocks),
        tool_calls=tuple(calls),
        text=text,
        provider="anthropic",
        model="claude-haiku-4-5-20251001",
        metadata={
            "client_tool_transport": True,
            "tools_executed_by_backend": False,
            "provider_stop_reason": stop_reason,
            "provider_usage": {"input_tokens": 11, "output_tokens": 3},
        },
    )


def _request() -> ClientToolTurnRequest:
    return ClientToolTurnRequest(
        system_prompt="Use runtime tools.",
        messages=({"role": "user", "content": "Repair the artifact."},),
        tools=(
            _tool("edit"),
            _tool("check"),
            _tool("submit", terminal=True),
        ),
        model="claude-haiku-4-5-20251001",
        metadata={
            "model_tier": "haiku",
            CLIENT_TOOL_AUTHORIZATION_FINGERPRINT_METADATA_KEY: "auth:q1:v1",
        },
    )


def test_exact_text_edits_support_count_checked_repeated_literals() -> None:
    revised, records = apply_model_exact_text_edits(
        '{"lower":"-2.0","upper":"2.0","copy":"-2.0"}',
        edits=[
            {
                "old_text": '"-2.0"',
                "new_text": "-2.0",
                "expected_occurrences": 2,
            },
            {"old_text": '"2.0"', "new_text": "2.0"},
        ],
        replacement_key="new_text",
    )

    assert revised == '{"lower":-2.0,"upper":2.0,"copy":-2.0}'
    assert records[0]["occurrences_replaced"] == 2
    assert "occurrences_replaced" not in records[1]
    with pytest.raises(ClientToolInputError, match="expected 3, observed 2"):
        apply_model_exact_text_edits(
            '"x" "x"',
            edits=[{
                "old_text": '"x"',
                "new_text": '"y"',
                "expected_occurrences": 3,
            }],
            replacement_key="new_text",
        )


def test_exact_text_edit_batch_schema_is_shared_and_strict() -> None:
    single = model_exact_text_edit_json_schema()
    schema = model_exact_text_edits_json_schema()

    assert single["type"] == "object"
    assert single["required"] == ["old_text", "new_text"]
    assert single["additionalProperties"] is False
    assert schema["type"] == "array"
    assert schema["minItems"] == 1
    assert schema["items"] == single
    assert set(single["properties"]) == {
        "old_text",
        "new_text",
        "expected_occurrences",
    }
    assert not {"oneOf", "anyOf", "allOf"}.intersection(schema)


def test_exact_text_edit_errors_name_missing_and_unexpected_fields() -> None:
    with pytest.raises(ClientToolInputError) as exc_info:
        apply_model_exact_text_edits(
            "old",
            edits=[{
                " old_text": "old",
                "new_text": "new",
                "expected_occurrences": 1,
            }],
            replacement_key="new_text",
        )

    detail = str(exc_info.value)
    assert "missing=['old_text']" in detail
    assert "unexpected=[' old_text']" in detail
    assert "optional=['expected_occurrences']" in detail


def test_long_tool_observation_preserves_head_tail_and_size_metadata() -> None:
    text = "diagnostic-start\n" + ("middle\n" * 80) + "diagnostic-end"

    bounded = client_tool_loop._client_tool_result_text(text, max_chars=120)

    assert len(bounded) == 120
    assert bounded.startswith("diagnostic-start")
    assert bounded.endswith("diagnostic-end")
    assert "truncated in middle by runtime" in bounded
    assert f"original_chars={len(text)}" in bounded
    assert f"original_lines={len(text.splitlines())}" in bounded


def test_client_tool_session_roundtrips_exact_transcript(tmp_path) -> None:
    request = _request()
    messages = (
        *request.messages,
        {
            "role": "assistant",
            "content": [
                {
                    "type": "tool_use",
                    "id": "call-edit",
                    "name": "edit",
                    "input": {"value": 2},
                }
            ],
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "tool_use_id": "call-edit",
                    "content": '{"ok":true,"value":2}',
                    "is_error": False,
                }
            ],
        },
    )

    reference = persist_client_tool_session(
        session_dir=tmp_path,
        session_id="theory:q1",
        request=request,
        messages=messages,
    )

    assert reference["message_count"] == len(messages)
    assert reference["root_path"] == str(tmp_path.resolve())
    assert reference["relative_path"].startswith(".client_tool_sessions/")
    assert reference["authorization_fingerprint"] == "auth:q1:v1"
    assert load_client_tool_session(
        reference,
        session_dir=tmp_path,
        session_id="theory:q1",
        request=request,
    ) == messages


def test_checkpoint_window_validates_parent_without_replaying_it(tmp_path) -> None:
    request = _request()
    prior_messages = (
        *request.messages,
        {
            "role": "assistant",
            "content": [
                {
                    "type": "tool_use",
                    "id": "prior-private-call",
                    "name": "edit",
                    "input": {"value": 2},
                }
            ],
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "tool_use_id": "prior-private-call",
                    "content": '{"ok":true,"value":2}',
                    "is_error": False,
                }
            ],
        },
    )
    reference = persist_client_tool_session(
        session_dir=tmp_path,
        session_id="theory:q1",
        request=request,
        messages=prior_messages,
    )

    resumed_request, window = resume_client_tool_session_from_checkpoint(
        reference,
        session_dir=tmp_path,
        session_id="theory:q1",
        checkpoint_identity="theory-checkpoint:q1",
        request=request,
    )

    assert len(resumed_request.messages) == len(request.messages) == 1
    resumed_content = str(resumed_request.messages[0]["content"])
    assert "prior-private-call" not in resumed_content
    assert "Repair the artifact." in resumed_content
    assert "authoritative current checkpoint state" in resumed_content
    assert window == resumed_request.metadata["client_tool_checkpoint_window"]
    assert window["policy"] == CLIENT_TOOL_CHECKPOINT_WINDOW_POLICY
    assert window["parent_message_count"] == len(prior_messages)
    assert window["checkpoint_identity"] == "theory-checkpoint:q1"
    assert window["authorization_fingerprint"] == "auth:q1:v1"
    assert window["parent_transcript_fingerprint"] == reference[
        "transcript_fingerprint"
    ]
    assert window["prior_transcript_replayed"] is False
    assert window["summary_used"] is False
    assert CLIENT_TOOL_TRANSCRIPT_POLICY.endswith("checkpoint_windows_v2")
    with pytest.raises(ValueError, match="requires checkpoint identity"):
        resume_client_tool_session_from_checkpoint(
            reference,
            session_dir=tmp_path,
            session_id="theory:q1",
            checkpoint_identity="",
            request=request,
        )
    missing_authorization = replace(
        request,
        metadata={"model_tier": "haiku"},
    )
    with pytest.raises(ValueError, match="root authorization fingerprint"):
        resume_client_tool_session_from_checkpoint(
            reference,
            session_dir=tmp_path,
            session_id="theory:q1",
            checkpoint_identity="theory-checkpoint:q1",
            request=missing_authorization,
        )


def test_checkpoint_window_replays_recent_complete_tool_rounds(tmp_path) -> None:
    request = _request()
    prior_messages = (
        *request.messages,
        {
            "role": "assistant",
            "content": [
                {
                    "type": "tool_use",
                    "id": "prior-complete-call",
                    "name": "edit",
                    "input": {"value": 2},
                }
            ],
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "tool_use_id": "prior-complete-call",
                    "content": '{"ok":true,"value":2}',
                    "is_error": False,
                }
            ],
        },
    )
    reference = persist_client_tool_session(
        session_dir=tmp_path,
        session_id="theory:q1",
        request=request,
        messages=prior_messages,
    )

    resumed_request, window = resume_client_tool_session_from_checkpoint(
        reference,
        session_dir=tmp_path,
        session_id="theory:q1",
        checkpoint_identity="theory-checkpoint:q1",
        request=request,
        replay_recent_tool_rounds=1,
    )

    assert window["policy"] == CLIENT_TOOL_RECENT_HISTORY_WINDOW_POLICY
    assert window["prior_transcript_replayed"] is True
    assert window["replayed_tool_rounds"] == 1
    assert window["replayed_message_count"] == 2
    assert window["replayed_messages_fingerprint"]
    assert len(resumed_request.messages) == 3
    assert [row["role"] for row in resumed_request.messages] == [
        "user",
        "assistant",
        "user",
    ]
    resumed_text = str(resumed_request.messages)
    assert "prior-complete-call" in resumed_text
    assert "Repair the artifact." in resumed_text
    assert "budget counters in them belong to the old window" in resumed_text


def test_client_tool_session_rejects_contract_drift_and_tampering(tmp_path) -> None:
    request = _request()
    reference = persist_client_tool_session(
        session_dir=tmp_path,
        session_id="theory:q1",
        request=request,
        messages=request.messages,
    )

    changed_sampling = replace(request, max_tokens=request.max_tokens + 1)
    with pytest.raises(ValueError, match="identity mismatch"):
        load_client_tool_session(
            reference,
            session_dir=tmp_path,
            session_id="theory:q1",
            request=changed_sampling,
        )

    changed_authorization = replace(
        request,
        metadata={
            **dict(request.metadata),
            CLIENT_TOOL_AUTHORIZATION_FINGERPRINT_METADATA_KEY: "auth:q1:v2",
        },
    )
    with pytest.raises(ValueError, match="identity mismatch"):
        load_client_tool_session(
            reference,
            session_dir=tmp_path,
            session_id="theory:q1",
            request=changed_authorization,
        )

    changed_tools = replace(
        request,
        tools=(*request.tools, _tool("search")),
    )
    with pytest.raises(ValueError, match="identity mismatch"):
        load_client_tool_session(
            reference,
            session_dir=tmp_path,
            session_id="theory:q1",
            request=changed_tools,
        )

    changed_tool_description = replace(
        request,
        tools=(
            replace(request.tools[0], description="Use a changed edit contract."),
            *request.tools[1:],
        ),
    )
    with pytest.raises(ValueError, match="identity mismatch"):
        load_client_tool_session(
            reference,
            session_dir=tmp_path,
            session_id="theory:q1",
            request=changed_tool_description,
        )

    changed_tool_schema = replace(
        request,
        tools=(
            replace(
                request.tools[0],
                input_schema={
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {"value": {"type": "integer"}},
                    "required": ["value"],
                },
            ),
            *request.tools[1:],
        ),
    )
    with pytest.raises(ValueError, match="identity mismatch"):
        load_client_tool_session(
            reference,
            session_dir=tmp_path,
            session_id="theory:q1",
            request=changed_tool_schema,
        )

    for field_name, changed_value in (
        ("max_tokens", request.max_tokens + 1),
        ("temperature", 0.25),
        ("tool_choice", "submit"),
        ("disable_parallel_tool_use", True),
        ("enable_prompt_caching", True),
    ):
        changed_sampling_contract = replace(
            request,
            **{field_name: changed_value},
        )
        with pytest.raises(ValueError, match="identity mismatch"):
            load_client_tool_session(
                reference,
                session_dir=tmp_path,
                session_id="theory:q1",
                request=changed_sampling_contract,
            )

    with pytest.raises(ValueError, match="identity mismatch"):
        load_client_tool_session(
            reference,
            session_dir=tmp_path / "different-workspace",
            session_id="theory:q1",
            request=request,
        )

    session_path = tmp_path / reference["relative_path"]
    session_path.write_text("{}", encoding="utf-8")
    with pytest.raises(ValueError, match="bytes do not match"):
        load_client_tool_session(
            reference,
            session_dir=tmp_path,
            session_id="theory:q1",
            request=request,
        )


def test_bounded_client_tool_loop_returns_terminal_runtime_payload() -> None:
    backend = ScriptedToolTurnBackend(
        [
            _response(
                ClientToolCall("call-edit", "edit", {"value": 2}),
                ClientToolCall("call-check", "check", {}),
            ),
            _response(ClientToolCall("call-submit", "submit", {})),
        ]
    )
    state = {"value": 1}

    def execute(call, context):
        if call.name == "edit":
            state["value"] = call.input["value"]
            return ClientToolExecutionResult(
                content={"ok": True, "value": state["value"]},
                state_changed=True,
                observation_key="edited:2",
            )
        if call.name == "check":
            return ClientToolExecutionResult(
                content={"ok": state["value"] == 2},
                observation_key="check:passed",
            )
        assert context.call_index == context.calls_in_turn - 1
        return ClientToolExecutionResult(
            content={"ok": True, "submitted": True},
            terminal=True,
            terminal_payload={"value": state["value"]},
            observation_key="submitted:2",
        )

    result = run_bounded_client_tool_loop(
        backend=backend,
        request=_request(),
        execute_tool=execute,
        max_turns=3,
        max_tool_calls=5,
        max_no_progress_turns=2,
    )

    assert result.terminal_payload == {"value": 2}
    assert result.turns == 2
    assert result.tool_calls == 3
    assert result.runtime_executed_tool_calls == 3
    assert result.provider_usage == {"input_tokens": 22, "output_tokens": 6}
    assert result.transcript_fingerprint
    assert len(backend.requests) == 2
    second_messages = backend.requests[1].messages
    assert second_messages[-2]["role"] == "assistant"
    assert second_messages[-1]["content"][0]["type"] == "tool_result"
    first_observation = json.loads(
        second_messages[-1]["content"][0]["content"]
    )
    assert first_observation == {"ok": True, "value": 2}
    assert result.history[0]["tool_calls"][0]["name"] == "edit"
    assert '"value":2' in result.history[0]["tool_calls"][0][
        "result_excerpt"
    ]
    assert result.history[0]["response_metadata"][
        "tools_executed_by_backend"
    ] is False


def test_bounded_client_tool_loop_never_executes_truncated_tool_input() -> None:
    backend = ScriptedToolTurnBackend(
        [
            _response(
                ClientToolCall("call-truncated", "edit", {}),
                stop_reason="max_tokens",
            ),
            _response(ClientToolCall("call-submit", "submit", {})),
        ]
    )
    executed_tools: list[str] = []

    def execute(call, _context):
        executed_tools.append(call.name)
        return ClientToolExecutionResult(
            content={"ok": True},
            terminal=call.name == "submit",
            terminal_payload={"submitted": True} if call.name == "submit" else None,
            observation_key=call.name,
        )

    result = run_bounded_client_tool_loop(
        backend=backend,
        request=_request(),
        execute_tool=execute,
        max_turns=2,
        max_tool_calls=2,
        max_no_progress_turns=2,
    )

    assert result.terminal_payload == {"submitted": True}
    assert executed_tools == ["submit"]
    assert result.runtime_executed_tool_calls == 1
    truncated = result.history[0]
    assert truncated["provider_output_truncated"] is True
    assert truncated["tool_calls"][0]["executed_by_runtime"] is False
    assert truncated["tool_calls"][0]["is_error"] is True
    assert "provider_tool_input_truncated" in str(
        backend.requests[1].messages[-1]["content"]
    )


def test_bounded_client_tool_loop_keeps_one_linear_model_tool_history() -> None:
    backend = ScriptedToolTurnBackend(
        [
            _response(ClientToolCall("call-edit-1", "edit", {"value": 1})),
            _response(ClientToolCall("call-edit-2", "edit", {"value": 2})),
            _response(ClientToolCall("call-submit", "submit", {})),
        ]
    )
    state = {"value": 0}

    def execute(call, _context):
        if call.name == "edit":
            state["value"] = int(call.input["value"])
            return ClientToolExecutionResult(
                content={"ok": True, "value": state["value"]},
                state_changed=True,
                observation_key=f"edited:{state['value']}",
            )
        return ClientToolExecutionResult(
            content={"ok": True},
            terminal=True,
            terminal_payload={"value": state["value"]},
            observation_key="submitted",
        )

    result = run_bounded_client_tool_loop(
        backend=backend,
        request=_request(),
        execute_tool=execute,
        max_turns=3,
        max_tool_calls=3,
        max_no_progress_turns=2,
    )

    assert result.terminal_payload == {"value": 2}
    assert [len(request.messages) for request in backend.requests] == [1, 3, 5]
    assert backend.requests[-1].messages[0] == backend.requests[0].messages[0]
    final_context = str(backend.requests[-1].messages)
    assert "<rollout_budget>" not in final_context
    assert "call-edit-1" in final_context
    assert "call-edit-2" in final_context
    assert "'value': 1" in final_context
    assert "'value': 2" in final_context


def test_bounded_client_tool_loop_stops_without_forced_terminal_phase() -> None:
    response = _response(text="I will describe the change instead.")
    backend = ScriptedToolTurnBackend([response, response, response, response])

    with pytest.raises(
        ClientToolLoopError,
        match="model ended the workspace turn without a client tool call",
    ) as exc:
        run_bounded_client_tool_loop(
            backend=backend,
            request=_request(),
            execute_tool=lambda call, context: ClientToolExecutionResult({}),
            max_turns=4,
            max_tool_calls=5,
            max_no_progress_turns=2,
        )

    assert exc.value.tool_calls == 0
    assert exc.value.turns == 1
    assert len(backend.requests) == 1
    assert exc.value.messages
    assert exc.value.messages[-1] == {
        "role": "assistant",
        "content": [{"type": "text", "text": response.text}],
    }
    assert exc.value.provider == "anthropic"
    assert exc.value.model == "claude-haiku-4-5-20251001"
    assert exc.value.transcript_fingerprint


def test_bounded_client_tool_loop_does_not_accept_early_terminal_call() -> None:
    backend = ScriptedToolTurnBackend(
        [
            _response(
                ClientToolCall("call-submit", "submit", {}),
                ClientToolCall("call-edit", "edit", {}),
            ),
            _response(ClientToolCall("call-submit-final", "submit", {})),
        ]
    )

    executed_tools = []

    def execute(call, context):
        executed_tools.append(call.name)
        if call.name == "submit":
            return ClientToolExecutionResult(
                content={"ok": True},
                terminal=True,
                terminal_payload={"accepted": True},
            )
        return ClientToolExecutionResult(
            content={"ok": True},
            observation_key="edit-after-submit",
        )

    result = run_bounded_client_tool_loop(
        backend=backend,
        request=replace(
            _request(),
            tools=(_tool("edit"), _tool("submit", terminal=True)),
        ),
        execute_tool=execute,
        max_turns=2,
        max_tool_calls=3,
        max_no_progress_turns=2,
    )

    first_turn = backend.requests[0]
    assert first_turn.tool_choice == "any"
    assert [tool.name for tool in first_turn.tools] == ["edit", "submit"]
    assert first_turn.disable_parallel_tool_use is False
    assert executed_tools == ["edit", "submit"]
    assert result.terminal_payload == {"accepted": True}


def test_bounded_client_tool_loop_keeps_normal_final_turn_model_directed() -> None:
    backend = ScriptedToolTurnBackend(
        [
            _response(ClientToolCall("call-edit", "edit", {"value": 2})),
            _response(ClientToolCall("call-submit", "submit", {})),
        ]
    )

    result = run_bounded_client_tool_loop(
        backend=backend,
        request=_request(),
        execute_tool=lambda call, context: ClientToolExecutionResult(
            content={"ok": True},
            state_changed=call.name == "edit",
            terminal=call.name == "submit",
            terminal_payload=(
                {"submitted": True} if call.name == "submit" else None
            ),
            observation_key=call.name,
        ),
        max_turns=2,
        max_tool_calls=2,
        max_no_progress_turns=1,
    )

    assert result.terminal_payload == {"submitted": True}
    assert [tool.name for tool in backend.requests[0].tools] == [
        "edit",
        "check",
        "submit",
    ]
    assert [tool.name for tool in backend.requests[1].tools] == [
        "edit",
        "check",
        "submit",
    ]
    assert backend.requests[1].tool_choice == "any"
    assert backend.requests[1].disable_parallel_tool_use is False


def test_terminal_call_does_not_consume_workspace_action_budget() -> None:
    backend = ScriptedToolTurnBackend(
        [
            _response(ClientToolCall("call-edit", "edit", {"value": 2})),
            _response(ClientToolCall("call-submit", "submit", {})),
        ]
    )

    result = run_bounded_client_tool_loop(
        backend=backend,
        request=_request(),
        execute_tool=lambda call, context: ClientToolExecutionResult(
            content={"ok": True},
            state_changed=call.name == "edit",
            terminal=call.name == "submit",
            terminal_payload=(
                {"submitted": True} if call.name == "submit" else None
            ),
            observation_key=call.name,
        ),
        max_turns=3,
        max_tool_calls=1,
        max_no_progress_turns=1,
    )

    assert result.terminal_payload == {"submitted": True}
    assert result.turns == 2
    assert result.tool_calls == 2
    assert result.runtime_executed_tool_calls == 2
    final_action_observation = json.loads(
        backend.requests[1].messages[-1]["content"][0]["content"]
    )
    assert final_action_observation == {"ok": True}
    assert "client_tool_loop_terminal_decision_turn" not in backend.requests[1].metadata


def test_last_workspace_action_does_not_trigger_hidden_terminal_turn() -> None:
    backend = ScriptedToolTurnBackend(
        [
            _response(ClientToolCall("call-edit", "edit", {"value": 2})),
            _response(ClientToolCall("call-submit", "submit", {})),
        ]
    )
    executed_tools: list[str] = []

    def execute(call, _context):
        executed_tools.append(call.name)
        return ClientToolExecutionResult(
            content={"ok": True},
            state_changed=call.name == "edit",
            terminal=call.name == "submit",
            terminal_payload=(
                {"submitted": True} if call.name == "submit" else None
            ),
            observation_key=call.name,
        )

    with pytest.raises(ClientToolLoopError, match="turn budget exhausted") as exc:
        run_bounded_client_tool_loop(
            backend=backend,
            request=_request(),
            execute_tool=execute,
            max_turns=1,
            max_tool_calls=4,
            max_no_progress_turns=2,
        )

    assert exc.value.turns == 1
    assert executed_tools == ["edit"]
    assert len(backend.requests) == 1
    assert "client_tool_loop_terminal_continuation" not in (
        backend.requests[0].metadata
    )


def test_rejected_terminal_at_explicit_limit_is_not_retried() -> None:
    backend = ScriptedToolTurnBackend(
        [
            _response(ClientToolCall("call-edit", "edit", {"value": 2})),
            _response(ClientToolCall("call-submit-invalid", "submit", {})),
            _response(ClientToolCall("call-submit-valid", "submit", {})),
        ]
    )
    terminal_attempts = 0

    def execute(call, _context):
        nonlocal terminal_attempts
        if call.name == "edit":
            return ClientToolExecutionResult(
                content={"ok": True},
                state_changed=True,
                observation_key="edited",
            )
        terminal_attempts += 1
        if terminal_attempts == 1:
            raise ClientToolInputError("terminal packet is incomplete")
        return ClientToolExecutionResult(
            content={"ok": True},
            terminal=True,
            terminal_payload={"submitted": True},
            observation_key="submitted",
        )

    with pytest.raises(ClientToolLoopError, match="turn budget exhausted") as exc:
        run_bounded_client_tool_loop(
            backend=backend,
            request=_request(),
            execute_tool=execute,
            max_turns=2,
            max_tool_calls=4,
            max_no_progress_turns=2,
        )

    assert terminal_attempts == 1
    assert len(backend.requests) == 2
    assert "terminal packet is incomplete" in str(exc.value.messages[-1])
    assert all(
        [tool.name for tool in request.tools] == ["edit", "check", "submit"]
        for request in backend.requests
    )
    assert all(
        "client_tool_loop_terminal_rejection_followup" not in request.metadata
        for request in backend.requests
    )


def test_rejected_terminal_is_an_ordinary_same_model_observation() -> None:
    backend = ScriptedToolTurnBackend(
        [
            _response(ClientToolCall("call-edit", "edit", {"value": 2})),
            _response(ClientToolCall("call-submit-invalid", "submit", {})),
            _response(ClientToolCall("call-submit-valid", "submit", {})),
        ]
    )
    terminal_attempts = 0

    def execute(call, context):
        nonlocal terminal_attempts
        if call.name == "edit":
            return ClientToolExecutionResult(
                content={"ok": True},
                state_changed=True,
                observation_key="edited",
            )
        terminal_attempts += 1
        if terminal_attempts == 1:
            raise ClientToolInputError("submitted packet is incomplete")
        return ClientToolExecutionResult(
            content={"ok": True},
            terminal=True,
            terminal_payload={"submitted": True},
            observation_key="submitted",
        )

    result = run_bounded_client_tool_loop(
        backend=backend,
        request=_request(),
        execute_tool=execute,
        max_turns=3,
        max_tool_calls=3,
        max_no_progress_turns=1,
    )

    assert result.terminal_payload == {"submitted": True}
    assert result.turns == 3
    assert terminal_attempts == 2
    assert [tool.name for tool in backend.requests[2].tools] == [
        "edit",
        "check",
        "submit",
    ]
    assert backend.requests[2].tool_choice == "any"
    assert "client_tool_loop_terminal_decision_turn" not in backend.requests[2].metadata


def test_rejected_terminal_can_be_followed_by_model_selected_edit() -> None:
    backend = ScriptedToolTurnBackend(
        [
            _response(ClientToolCall("call-edit-initial", "edit", {"value": 1})),
            _response(ClientToolCall("call-submit-invalid", "submit", {})),
            _response(ClientToolCall("call-edit-recovery", "edit", {"value": 2})),
            _response(ClientToolCall("call-submit-valid", "submit", {})),
        ]
    )
    submissions = 0
    executed_tools: list[str] = []

    def execute(call, _context):
        nonlocal submissions
        executed_tools.append(call.name)
        if call.name == "edit":
            return ClientToolExecutionResult(
                content={"ok": True, "value": call.input["value"]},
                state_changed=True,
                observation_key=f"edit:{call.input['value']}",
            )
        submissions += 1
        if submissions == 1:
            raise ClientToolInputError("parser rejected the current file")
        return ClientToolExecutionResult(
            content={"ok": True},
            terminal=True,
            terminal_payload={"submitted": True},
            observation_key="submitted",
        )

    result = run_bounded_client_tool_loop(
        backend=backend,
        request=_request(),
        execute_tool=execute,
        max_turns=4,
        max_tool_calls=2,
        max_no_progress_turns=1,
    )

    assert result.terminal_payload == {"submitted": True}
    assert result.turns == 4
    assert executed_tools == ["edit", "submit", "edit", "submit"]
    assert "client_tool_loop_terminal_recovery_action_allowed" not in backend.requests[2].metadata
    assert "client_tool_loop_terminal_recovery_action_allowed" not in backend.requests[3].metadata
    recovery_call = result.history[2]["tool_calls"][0]
    assert recovery_call["executed_by_runtime"] is True
    assert recovery_call["state_changed"] is True
    assert "parser rejected the current file" in str(
        backend.requests[2].messages[-1]["content"]
    )


def test_terminal_rejection_can_be_inspected_edited_and_resubmitted() -> None:
    backend = ScriptedToolTurnBackend(
        [
            _response(ClientToolCall("call-edit-initial", "edit", {"value": 1})),
            _response(ClientToolCall("call-submit-invalid", "submit", {})),
            _response(ClientToolCall("call-check-recovery", "check", {})),
            _response(ClientToolCall("call-edit-recovery", "edit", {"value": 2})),
            _response(ClientToolCall("call-submit-valid", "submit", {})),
        ]
    )
    submissions = 0
    executed_tools: list[str] = []

    def execute(call, _context):
        nonlocal submissions
        executed_tools.append(call.name)
        if call.name == "check":
            return ClientToolExecutionResult(
                content={"ok": True, "current_value": 1},
                observation_key="checked:1",
            )
        if call.name == "edit":
            return ClientToolExecutionResult(
                content={"ok": True, "value": call.input["value"]},
                state_changed=True,
                observation_key=f"edit:{call.input['value']}",
            )
        submissions += 1
        if submissions == 1:
            return ClientToolExecutionResult(
                content={
                    "ok": False,
                    "error": "validator rejected the forced commit",
                },
                is_error=True,
                observation_key="forced-commit-rejected",
            )
        return ClientToolExecutionResult(
            content={"ok": True},
            terminal=True,
            terminal_payload={"submitted": True},
            observation_key="submitted",
        )

    result = run_bounded_client_tool_loop(
        backend=backend,
        request=_request(),
        execute_tool=execute,
        max_turns=5,
        max_tool_calls=3,
        max_no_progress_turns=2,
    )

    assert result.terminal_payload == {"submitted": True}
    assert result.turns == 5
    assert executed_tools == ["edit", "submit", "check", "edit", "submit"]
    assert all(
        "client_tool_loop_terminal_recovery_action_allowed" not in request.metadata
        for request in backend.requests
    )
    assert "validator rejected the forced commit" in str(
        backend.requests[2].messages[-1]["content"]
    )


def test_duplicate_terminal_rejection_hits_generic_no_progress_bound() -> None:
    backend = ScriptedToolTurnBackend(
        [
            _response(ClientToolCall("call-submit-standard", "submit", {})),
            _response(ClientToolCall("call-submit-recovery", "submit", {})),
            _response(ClientToolCall("call-submit-final", "submit", {})),
        ]
    )

    with pytest.raises(ClientToolLoopError) as raised:
        run_bounded_client_tool_loop(
            backend=backend,
            request=_request(),
            execute_tool=lambda _call, _context: ClientToolExecutionResult(
                content={"ok": False, "error": "same validator rejection"},
                is_error=True,
                observation_key="same-validator-rejection",
            ),
            max_turns=3,
            max_tool_calls=1,
            max_no_progress_turns=1,
        )

    assert "no new progress" in raised.value.reason
    assert len(backend.requests) == 2


def test_duplicate_ordinary_no_progress_has_no_hidden_terminal_turn() -> None:
    backend = ScriptedToolTurnBackend(
        [
            _response(ClientToolCall("call-edit-first", "edit", {})),
            _response(ClientToolCall("call-edit-duplicate", "edit", {})),
            _response(ClientToolCall("call-submit", "submit", {})),
        ]
    )

    def execute(call, _context):
        if call.name == "submit":
            return ClientToolExecutionResult(
                content={"ok": True},
                terminal=True,
                terminal_payload={"submitted": True},
                observation_key="submitted",
            )
        return ClientToolExecutionResult(
            content={"ok": False, "error": "same invalid ordinary action"},
            is_error=True,
            observation_key="same-invalid-ordinary-action",
        )

    with pytest.raises(ClientToolLoopError, match="no new progress") as exc:
        run_bounded_client_tool_loop(
            backend=backend,
            request=_request(),
            execute_tool=execute,
            max_turns=5,
            max_tool_calls=5,
            max_no_progress_turns=1,
        )

    assert exc.value.turns == 2
    assert len(backend.requests) == 2


def test_terminal_only_tool_surface_remains_model_directed() -> None:
    backend = ScriptedToolTurnBackend([_response(text="The workspace is not ready.")])
    request = replace(
        _request(),
        tools=(_tool("submit", terminal=True),),
        tool_choice="auto",
        disable_parallel_tool_use=False,
    )

    with pytest.raises(ClientToolLoopError, match="model ended the workspace turn"):
        run_bounded_client_tool_loop(
            backend=backend,
            request=request,
            execute_tool=lambda call, context: pytest.fail("no tool was selected"),
            max_turns=1,
            max_tool_calls=1,
            max_no_progress_turns=1,
        )

    observed = backend.requests[0]
    assert observed.tool_choice == "auto"
    assert observed.disable_parallel_tool_use is False
    assert "client_tool_loop_terminal_only_turn" not in observed.metadata


def test_no_tool_response_requires_explicit_workspace_continuation() -> None:
    backend = ScriptedToolTurnBackend(
        [
            _response(ClientToolCall("call-edit", "edit", {})),
            _response(text="I am not ready."),
            _response(ClientToolCall("call-submit", "submit", {})),
        ]
    )

    with pytest.raises(
        ClientToolLoopError,
        match="model ended the workspace turn without a client tool call",
    ) as exc:
        run_bounded_client_tool_loop(
            backend=backend,
            request=_request(),
            execute_tool=lambda call, context: ClientToolExecutionResult(
                content={"ok": True},
                state_changed=call.name == "edit",
                terminal=call.name == "submit",
                terminal_payload=(
                    {"submitted": True} if call.name == "submit" else None
                ),
                observation_key=call.name,
            ),
            max_turns=3,
            max_tool_calls=3,
            max_no_progress_turns=2,
        )

    assert exc.value.turns == 2
    assert exc.value.tool_calls == 1
    assert len(backend.requests) == 2
    assert [tool.name for tool in backend.requests[-1].tools] == [
        "edit",
        "check",
        "submit",
    ]
    assert backend.requests[-1].messages[-1]["role"] == "user"
    assert "No client tool was called" not in str(exc.value.messages)


def test_action_budget_keeps_tools_visible_but_does_not_execute_late_action() -> None:
    backend = ScriptedToolTurnBackend(
        [
            _response(ClientToolCall("call-edit", "edit", {"value": 2})),
            _response(ClientToolCall("call-check-late", "check", {})),
            _response(ClientToolCall("call-submit", "submit", {})),
        ]
    )
    executed_tools: list[str] = []

    def execute(call, _context):
        executed_tools.append(call.name)
        return ClientToolExecutionResult(
            content={"ok": True},
            state_changed=call.name == "edit",
            terminal=call.name == "submit",
            terminal_payload=(
                {"submitted": True} if call.name == "submit" else None
            ),
            observation_key=call.name,
        )

    result = run_bounded_client_tool_loop(
        backend=backend,
        request=_request(),
        execute_tool=execute,
        max_turns=3,
        max_tool_calls=1,
        max_no_progress_turns=2,
    )

    assert result.terminal_payload == {"submitted": True}
    assert executed_tools == ["edit", "submit"]
    rejected = result.history[1]["tool_calls"][0]
    assert rejected["executed_by_runtime"] is False
    assert "workspace_action_budget_exhausted" in rejected["result_excerpt"]
    assert all(
        [tool.name for tool in request.tools] == ["edit", "check", "submit"]
        for request in backend.requests
    )


def test_repeated_observation_can_still_be_followed_by_model_submission() -> None:
    backend = ScriptedToolTurnBackend(
        [
            _response(ClientToolCall("call-check-1", "check", {})),
            _response(ClientToolCall("call-check-2", "check", {})),
            _response(ClientToolCall("call-submit", "submit", {})),
        ]
    )

    result = run_bounded_client_tool_loop(
        backend=backend,
        request=_request(),
        execute_tool=lambda call, context: ClientToolExecutionResult(
            content={"ok": True},
            terminal=call.name == "submit",
            terminal_payload=(
                {"submitted": True} if call.name == "submit" else None
            ),
            observation_key=call.name,
        ),
        max_turns=5,
        max_tool_calls=3,
        max_no_progress_turns=2,
    )

    assert result.terminal_payload == {"submitted": True}
    assert result.turns == 3
    assert [tool.name for tool in backend.requests[-1].tools] == [
        "edit",
        "check",
        "submit",
    ]
    assert "client_tool_loop_terminal_decision_reason" not in backend.requests[-1].metadata


def test_rejected_submission_can_be_resubmitted_within_generic_turn_budget() -> None:
    backend = ScriptedToolTurnBackend(
        [
            _response(ClientToolCall("call-check-1", "check", {})),
            _response(ClientToolCall("call-check-2", "check", {})),
            _response(ClientToolCall("call-submit-invalid", "submit", {})),
            _response(ClientToolCall("call-submit-valid", "submit", {})),
        ]
    )
    submissions = 0

    def execute(call, _context):
        nonlocal submissions
        if call.name == "check":
            return ClientToolExecutionResult(
                content={"ok": True},
                observation_key="same-check",
            )
        submissions += 1
        if submissions == 1:
            raise ClientToolInputError("compiler rejected the first source")
        return ClientToolExecutionResult(
            content={"ok": True},
            terminal=True,
            terminal_payload={"submitted": True},
            observation_key="submitted",
        )

    result = run_bounded_client_tool_loop(
        backend=backend,
        request=_request(),
        execute_tool=execute,
        max_turns=5,
        max_tool_calls=4,
        max_no_progress_turns=2,
    )

    assert result.terminal_payload == {"submitted": True}
    assert result.turns == 4
    assert submissions == 2
    assert all(
        [tool.name for tool in request.tools] == ["edit", "check", "submit"]
        for request in backend.requests[-2:]
    )
    assert "compiler rejected the first source" in str(
        backend.requests[-1].messages[-1]["content"]
    )


def test_multiple_rejected_submissions_share_the_same_generic_turn_budget() -> None:
    backend = ScriptedToolTurnBackend(
        [
            _response(ClientToolCall("call-submit-early", "submit", {})),
            _response(ClientToolCall("call-check", "check", {})),
            _response(ClientToolCall("call-submit-final", "submit", {})),
            _response(ClientToolCall("call-submit-recovery", "submit", {})),
        ]
    )
    submissions = 0

    def execute(call, _context):
        nonlocal submissions
        if call.name == "check":
            return ClientToolExecutionResult(
                content={"ok": True, "observation": "new context"},
                observation_key="new-context",
            )
        submissions += 1
        if submissions < 3:
            raise ClientToolInputError(f"raw compiler failure {submissions}")
        return ClientToolExecutionResult(
            content={"ok": True},
            terminal=True,
            terminal_payload={"submitted": True},
            observation_key="submitted",
        )

    result = run_bounded_client_tool_loop(
        backend=backend,
        request=_request(),
        execute_tool=execute,
        max_turns=4,
        max_tool_calls=4,
        max_no_progress_turns=2,
    )

    assert result.terminal_payload == {"submitted": True}
    assert result.turns == 4
    assert submissions == 3
    assert all(
        [tool.name for tool in request.tools] == ["edit", "check", "submit"]
        for request in backend.requests[-2:]
    )
    assert "raw compiler failure 2" in str(
        backend.requests[-1].messages[-1]["content"]
    )


def test_bounded_client_tool_loop_never_executes_unknown_tool() -> None:
    backend = ScriptedToolTurnBackend(
        [
            _response(
                ClientToolCall("call-unknown", "shell", {"cmd": "rm -rf /"})
            ),
            _response(ClientToolCall("call-submit", "submit", {})),
        ]
    )
    executions = 0

    def execute(call, context):
        nonlocal executions
        executions += 1
        return ClientToolExecutionResult(
            content={"ok": True},
            terminal=call.name == "submit",
            terminal_payload=(
                {"submitted": True} if call.name == "submit" else None
            ),
        )

    result = run_bounded_client_tool_loop(
        backend=backend,
        request=_request(),
        execute_tool=execute,
        max_turns=2,
        max_tool_calls=2,
        max_no_progress_turns=1,
    )

    assert executions == 1
    assert result.runtime_executed_tool_calls == 1
    assert result.terminal_payload == {"submitted": True}
    assert result.history[0]["tool_calls"][0]["executed_by_runtime"] is False


def test_bounded_client_tool_loop_returns_only_declared_input_errors_to_model() -> None:
    safe_backend = ScriptedToolTurnBackend(
        [
            _response(ClientToolCall("call-safe", "edit", {})),
            _response(text="stop"),
            _response(ClientToolCall("call-submit", "submit", {})),
            _response(ClientToolCall("call-submit-followup", "submit", {})),
        ]
    )

    with pytest.raises(ClientToolLoopError):
        run_bounded_client_tool_loop(
            backend=safe_backend,
            request=_request(),
            execute_tool=lambda call, context: (_ for _ in ()).throw(
                ClientToolInputError("safe validator detail")
            ),
            max_turns=2,
            max_tool_calls=2,
            max_no_progress_turns=1,
        )

    internal_backend = ScriptedToolTurnBackend(
        [_response(ClientToolCall("call-internal", "edit", {}))]
    )
    secret = "private-runtime-detail"

    with pytest.raises(ClientToolRuntimeError) as exc:
        run_bounded_client_tool_loop(
            backend=internal_backend,
            request=_request(),
            execute_tool=lambda call, context: (_ for _ in ()).throw(
                RuntimeError(secret)
            ),
            max_turns=2,
            max_tool_calls=2,
            max_no_progress_turns=1,
        )

    safe_result = safe_backend.requests[1].messages[-1]["content"][0]
    assert "safe validator detail" in safe_result["content"]
    assert len(internal_backend.requests) == 1
    assert exc.value.tool_name == "edit"
    assert exc.value.exception_type == "RuntimeError"
    assert isinstance(exc.value, ClientToolLoopError)
    assert exc.value.turns == 1
    assert len(exc.value.messages) == 2
    assert exc.value.history[0]["tool_calls"][0]["is_error"] is True
    assert secret not in str(exc.value)
    assert exc.value.__context__ is None


def test_terminal_provider_error_preserves_pending_workspace_input(tmp_path) -> None:
    backend = ScriptedToolTurnBackend(
        [
            _response(ClientToolCall("call-edit", "edit", {})),
            LiveGeneratorTimeoutError("private provider detail"),
        ]
    )

    with pytest.raises(ClientToolLoopError) as exc_info:
        run_bounded_client_tool_loop(
            backend=backend,
            request=_request(),
            execute_tool=lambda call, context: ClientToolExecutionResult(
                content={"ok": True, "artifact_hash": "updated"},
                state_changed=True,
            ),
            max_turns=3,
            max_tool_calls=3,
            max_no_progress_turns=2,
        )

    error = exc_info.value
    assert len(backend.requests) == 2
    assert error.turns == 2
    assert error.tool_calls == 1
    assert [message["role"] for message in error.messages] == [
        "user",
        "assistant",
        "user",
    ]
    assert error.history[-1]["stop_reason"] == "provider_terminal_error"
    metadata = error.history[-1]["response_metadata"]
    assert metadata["pending_workspace_input_preserved"] is True
    assert metadata["automatic_turn_restart"] is False
    assert "private provider detail" not in str(error)

    reference = persist_client_tool_session(
        session_dir=tmp_path,
        session_id="theory:q1",
        request=_request(),
        messages=error.messages,
    )
    assert load_client_tool_session(
        reference,
        session_dir=tmp_path,
        session_id="theory:q1",
        request=_request(),
    ) == tuple(error.messages)


def test_bounded_client_tool_loop_uses_existing_runtime_substage(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    observed = []

    @contextmanager
    def record_substage(name, *, metadata):
        details = dict(metadata)
        observed.append(("start", name, dict(details)))
        yield details
        observed.append(("finish", name, dict(details)))

    monkeypatch.setattr(
        "ai_statistician.client_tool_loop.agent_runtime_substage",
        record_substage,
    )
    backend = ScriptedToolTurnBackend(
        [_response(ClientToolCall("call-submit", "submit", {}))]
    )

    result = run_bounded_client_tool_loop(
        backend=backend,
        request=replace(
            _request(),
            metadata={
                "model_tier": "haiku",
                "subsystem": "TheoryReferee",
                "agent": "IndependentTheoryRefereeAgent",
                "review_stage": "theory_execution_preflight",
            },
        ),
        execute_tool=lambda call, context: ClientToolExecutionResult(
            content={"ok": True},
            terminal=True,
            terminal_payload={"ok": True},
        ),
        max_turns=2,
        max_tool_calls=2,
        max_no_progress_turns=1,
    )

    assert result.terminal_payload == {"ok": True}
    assert [row[:2] for row in observed] == [
        ("start", "client_tool_model_turn"),
        ("finish", "client_tool_model_turn"),
        ("start", "client_tool_execution"),
        ("finish", "client_tool_execution"),
    ]
    assert observed[0][2]["turn_index"] == 0
    assert observed[0][2]["model"] == "claude-haiku-4-5-20251001"
    assert observed[0][2]["workspace_subsystem"] == "TheoryReferee"
    assert observed[0][2]["workspace_agent"] == (
        "IndependentTheoryRefereeAgent"
    )
    assert observed[0][2]["workspace_stage"] == (
        "theory_execution_preflight"
    )
    assert observed[2][2]["tool_name"] == "submit"
    assert observed[3][2]["tool_terminal"] is True
    assert observed[3][2]["tool_result_is_error"] is False
