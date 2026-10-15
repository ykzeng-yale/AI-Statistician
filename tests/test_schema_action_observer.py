from dataclasses import replace
import json

import pytest
from ai_statistician.client_tool_loop import ClientToolExecutionResult, ClientToolLoopError, run_bounded_client_tool_loop
from ai_statistician.model_backend import ClientToolDefinition, ClientToolTurnRequest
from benchmarks.publication_tool_action_qualification_20261015.observe import SchemaActionBackend


def request():
    return ClientToolTurnRequest(
        system_prompt="Perform the opaque file task.", model="local-fixture",
        messages=({"role": "user", "content": "Inspect and finish."},),
        tools=(
            ClientToolDefinition("inspect", "Read the exact input.", {
                "type": "object", "properties": {}, "additionalProperties": False,
            }),
            ClientToolDefinition("finish", "Submit the exact observation.", {
                "type": "object", "properties": {"observed": {"type": "string"}},
                "required": ["observed"], "additionalProperties": False,
            }, terminal=True),
        ),
    )


def backend(monkeypatch, tmp_path, value, *, stopped=False):
    seen = []

    def complete(self, payload):
        self.attempts += 1
        seen.append(payload)
        return {"model": "local-fixture", "choices": [{"message": {
            "content": value if isinstance(value, str) else json.dumps(value),
        }}]}, {"provider_stop_reason": "max_tokens" if stopped else "stop",
               "provider_usage": {"input_tokens": 17, "output_tokens": 8}}

    monkeypatch.setattr(SchemaActionBackend, "_complete", complete)
    return SchemaActionBackend(tmp_path), seen


def test_schema_action_keeps_raw_arguments_and_shared_tool_result_history(monkeypatch, tmp_path):
    raw = "unmodified fixture failure\nline 12: opaque"
    instance, seen = backend(monkeypatch, tmp_path, {"actions": [
        {"name": "finish", "arguments": {"observed": raw}},
    ]})
    req = replace(request(), messages=(
        {"role": "assistant", "content": [{"type": "tool_use", "id": "old-call",
            "name": "inspect", "input": {}}]},
        {"role": "user", "content": [{"type": "tool_result", "tool_use_id": "old-call",
            "content": raw, "is_error": True}]},
    ))
    response = instance.generate_client_tool_turn(req)
    assert response.tool_calls[0].input == {"observed": raw}
    assert response.content_blocks[0]["id"] == response.tool_calls[0].call_id
    assert response.metadata["provider_usage"] == {"input_tokens": 17, "output_tokens": 8}
    assert response.metadata["tools_executed_by_backend"] is False
    assert json.loads(seen[0]["messages"][-1]["content"])["content"] == raw
    assert seen[0]["messages"][-1]["tool_call_id"] == "old-call"
    assert "tools" not in seen[0]
    assert seen[0]["response_format"]["type"] == "json_schema"
    assert (tmp_path / "action_protocol.json").is_file()
    assert sorted(p.name for p in tmp_path.iterdir()) == ["action_protocol.json", "turn-001.action.json"]


@pytest.mark.parametrize("value", [
    "malformed action response",
    {"actions": []},
    {"actions": [{"name": "unexposed", "arguments": {}}]},
    {"actions": [{"name": "finish", "arguments": {}}]},
    {"actions": [{"name": "finish", "arguments": {"observed": "raw", "repair": True}}]},
    {"actions": [{"name": "inspect", "arguments": {}}], "text": "done"},
])
def test_invalid_schema_action_is_not_repaired_or_dispatched(monkeypatch, tmp_path, value):
    instance, seen = backend(monkeypatch, tmp_path, value)
    response = instance.generate_client_tool_turn(request())
    assert response.tool_calls == ()
    assert response.text == (value if isinstance(value, str) else json.dumps(value))
    assert response.metadata["tool_action_error"].startswith(("JSONDecodeError:", "ValidationError:"))
    assert response.metadata["provider_usage"] == {"input_tokens": 17, "output_tokens": 8}
    assert len(seen) == 1


def test_truncated_response_remains_text_without_an_invented_tool_call(monkeypatch, tmp_path):
    partial = '{"actions":[{"name":"finish","arguments":{"observed":"unfinished'
    instance, seen = backend(monkeypatch, tmp_path, partial, stopped=True)
    response = instance.generate_client_tool_turn(request())
    assert response.tool_calls == ()
    assert response.text == partial
    assert response.content_blocks == ({"type": "text", "text": partial},)
    assert response.metadata["provider_stop_reason"] == "max_tokens"
    assert len(seen) == 1


def test_batch_actions_have_distinct_ids_and_single_call_request_is_enforced(monkeypatch, tmp_path):
    value = {"actions": [{"name": "inspect", "arguments": {}}] * 2}
    instance, seen = backend(monkeypatch, tmp_path, value)
    response = instance.generate_client_tool_turn(request())
    assert len({c.call_id for c in response.tool_calls}) == 2
    denied = instance.generate_client_tool_turn(replace(request(), disable_parallel_tool_use=True))
    assert denied.tool_calls == ()
    assert denied.metadata["tool_action_error"].startswith("ValidationError:")
    assert len(seen) == 2


def test_schema_actions_complete_through_shared_loop_with_unmodified_feedback(monkeypatch, tmp_path):
    raw = "opaque environment failure\nline 12"
    seen = []
    actions = iter([
        {"actions": [{"name": "inspect", "arguments": {}}]},
        {"actions": [{"name": "finish", "arguments": {"observed": raw}}]},
    ])

    def complete(self, payload):
        self.attempts += 1
        seen.append(payload)
        return {"model": "local-fixture", "choices": [{"message": {
            "content": json.dumps(next(actions)),
        }}]}, {"provider_stop_reason": "stop"}

    def execute(call, context):
        if call.name == "inspect":
            return ClientToolExecutionResult(content=raw, is_error=True)
        assert call.name == "finish" and call.input == {"observed": raw}
        return ClientToolExecutionResult(content="received", terminal=True,
                                         terminal_payload={"observed": raw})

    monkeypatch.setattr(SchemaActionBackend, "_complete", complete)
    result = run_bounded_client_tool_loop(
        backend=SchemaActionBackend(tmp_path), request=request(), execute_tool=execute,
        max_turns=3, max_tool_calls=3, max_no_progress_turns=2,
        session_dir=tmp_path / "session", session_id="schema-fixture",
    )
    assert result.terminal_payload == {"observed": raw}
    assert len(seen) == 2
    assert json.loads(seen[1]["messages"][-1]["content"]) == {"content": raw, "is_error": True}
    assert result.history[0]["tool_calls"][0]["is_error"] is True


def test_invalid_action_keeps_response_and_usage_in_retained_failure(monkeypatch, tmp_path):
    instance, seen = backend(monkeypatch, tmp_path, {"actions": []})

    def execute(call, context):
        pytest.fail("an invalid action must not execute")

    with pytest.raises(ClientToolLoopError) as caught:
        run_bounded_client_tool_loop(
            backend=instance, request=request(), execute_tool=execute,
            max_turns=3, max_tool_calls=3, max_no_progress_turns=2,
        )
    error = caught.value
    assert error.provider_usage == {"input_tokens": 17, "output_tokens": 8}
    assert error.messages[-1]["content"] == [{"type": "text", "text": '{"actions": []}'}]
    assert len(seen) == 1
