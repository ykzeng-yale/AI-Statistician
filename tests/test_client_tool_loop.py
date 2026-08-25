from __future__ import annotations

import json
from contextlib import contextmanager
from dataclasses import replace

import pytest

from ai_statistician.client_tool_loop import (
    CLIENT_TOOL_CHECKPOINT_WINDOW_POLICY,
    CLIENT_TOOL_TRANSCRIPT_POLICY,
    ClientToolExecutionResult,
    ClientToolInputError,
    ClientToolLoopError,
    ClientToolRuntimeError,
    load_client_tool_session,
    persist_client_tool_session,
    resume_client_tool_session_from_checkpoint,
    run_bounded_client_tool_loop,
)
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
        metadata={"model_tier": "haiku"},
    )


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
    assert window["parent_transcript_fingerprint"] == reference[
        "transcript_fingerprint"
    ]
    assert window["prior_transcript_replayed"] is False
    assert window["summary_used"] is False
    assert CLIENT_TOOL_TRANSCRIPT_POLICY.endswith("checkpoint_windows_v1")
    with pytest.raises(ValueError, match="requires checkpoint identity"):
        resume_client_tool_session_from_checkpoint(
            reference,
            session_dir=tmp_path,
            session_id="theory:q1",
            checkpoint_identity="",
            request=request,
        )


def test_client_tool_session_rejects_contract_drift_and_tampering(tmp_path) -> None:
    request = _request()
    reference = persist_client_tool_session(
        session_dir=tmp_path,
        session_id="theory:q1",
        request=request,
        messages=request.messages,
    )

    changed_model = replace(request, model="claude-sonnet-4-20250514")
    with pytest.raises(ValueError, match="identity mismatch"):
        load_client_tool_session(
            reference,
            session_dir=tmp_path,
            session_id="theory:q1",
            request=changed_model,
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
    assert first_observation["_client_tool_budget"] == {
        "standard_turns_remaining_after_current_turn": 2,
        "model_tool_calls_remaining_after_current_call": 4,
        "terminal_disposition_calls_remaining_after_current_call": 1,
        "final_disposition_required": False,
    }
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
    assert "call-edit-1" in final_context
    assert "call-edit-2" in final_context
    assert "'value': 1" in final_context
    assert "'value': 2" in final_context


def test_bounded_client_tool_loop_forces_disposition_after_no_tool_turns() -> None:
    response = _response(text="I will describe the change instead.")
    backend = ScriptedToolTurnBackend([response, response, response, response])

    with pytest.raises(
        ClientToolLoopError,
        match="terminal client-tool turn omitted its decision",
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
    assert exc.value.turns == 4
    assert exc.value.messages
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
        max_turns=1,
        max_tool_calls=3,
        max_no_progress_turns=1,
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
    assert backend.requests[1].metadata[
        "client_tool_loop_terminal_only_turn"
    ] is False


def test_bounded_client_tool_loop_reserves_terminal_call_after_action_budget() -> None:
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
    assert final_action_observation["_client_tool_budget"] == {
        "standard_turns_remaining_after_current_turn": 2,
        "model_tool_calls_remaining_after_current_call": 0,
        "terminal_disposition_calls_remaining_after_current_call": 1,
        "final_disposition_required": True,
    }
    assert backend.requests[1].metadata[
        "client_tool_loop_terminal_decision_turn"
    ] is True
    assert backend.requests[1].metadata[
        "client_tool_loop_terminal_decision_reason"
    ] == "standard client-tool call budget exhausted"


def test_bounded_client_tool_loop_allows_one_rejected_terminal_recovery() -> None:
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
        max_turns=2,
        max_tool_calls=3,
        max_no_progress_turns=1,
        max_terminal_recovery_turns=1,
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
    assert backend.requests[2].metadata[
        "client_tool_loop_terminal_decision_turn"
    ] is True
    assert backend.requests[2].metadata[
        "client_tool_loop_max_terminal_recovery_turns"
    ] == 1


def test_bounded_client_tool_loop_requests_terminal_decision_at_standard_budget() -> None:
    backend = ScriptedToolTurnBackend(
        [
            _response(ClientToolCall("call-edit", "edit", {})),
            _response(text="I am not ready."),
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
        max_tool_calls=3,
        max_no_progress_turns=2,
        max_terminal_recovery_turns=1,
    )

    assert result.terminal_payload == {"submitted": True}
    assert result.turns == 3
    assert [tool.name for tool in backend.requests[-1].tools] == [
        "edit",
        "check",
        "submit",
    ]
    assert "final disposition" in str(backend.requests[-1].messages[-1]["content"])
    assert backend.requests[-1].metadata[
        "client_tool_loop_terminal_decision_reason"
    ] == "standard client-tool turn budget exhausted"


def test_terminal_decision_keeps_tools_visible_but_rejects_nonterminal_calls() -> None:
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
        max_turns=1,
        max_tool_calls=3,
        max_no_progress_turns=2,
        max_terminal_recovery_turns=1,
    )

    assert result.terminal_payload == {"submitted": True}
    assert executed_tools == ["edit", "submit"]
    rejected = result.history[1]["tool_calls"][0]
    assert rejected["executed_by_runtime"] is False
    assert "final_disposition_requires_terminal_tool" in rejected["result_excerpt"]
    assert all(
        [tool.name for tool in request.tools] == ["edit", "check", "submit"]
        for request in backend.requests
    )


def test_bounded_client_tool_loop_requests_terminal_decision_on_no_progress() -> None:
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
        max_no_progress_turns=1,
        max_terminal_recovery_turns=1,
    )

    assert result.terminal_payload == {"submitted": True}
    assert result.turns == 3
    assert [tool.name for tool in backend.requests[-1].tools] == [
        "edit",
        "check",
        "submit",
    ]
    assert backend.requests[-1].metadata[
        "client_tool_loop_terminal_decision_reason"
    ] == "repeated client-tool turns made no new progress"


def test_terminal_decision_keeps_one_same_model_recovery_turn() -> None:
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
        max_no_progress_turns=1,
        max_terminal_recovery_turns=1,
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


def test_standard_submission_does_not_consume_forced_terminal_recovery() -> None:
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
        max_turns=2,
        max_tool_calls=4,
        max_no_progress_turns=2,
        max_terminal_recovery_turns=1,
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
        max_turns=1,
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
        request=_request(),
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
    assert observed[2][2]["tool_name"] == "submit"
    assert observed[3][2]["tool_terminal"] is True
    assert observed[3][2]["tool_result_is_error"] is False
