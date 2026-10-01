from __future__ import annotations

import json
import os
from dataclasses import replace
from io import BytesIO
from urllib.error import HTTPError

import pytest

from ai_statistician.cli import _build_theory_generator_backend, build_parser
from ai_statistician.local_model_backend import LocalChatGeneratorBackend, _chat_messages
from ai_statistician.model_backend import (
    ClientToolDefinition, ClientToolTurnRequest, GeneratorRequest,
    default_generator_model, default_generator_provider,
)


def _request():
    return ClientToolTurnRequest(
        system_prompt="Use the supplied tools.", model="Qwen3-4B-Instruct-2507",
        messages=({"role": "user", "content": "Inspect the artifact."},),
        tools=(ClientToolDefinition(name="observe", description="Read an observation.",
                                   input_schema={"type": "object"}),),
    )


def test_local_default_has_no_cloud_escalation(monkeypatch):
    monkeypatch.delenv("AI_STATISTICIAN_LLM_PROVIDER", raising=False)
    assert default_generator_provider() == "local"
    assert default_generator_model("local", env={}) == "Qwen3-4B-Instruct-2507"
    backend, provider = _build_theory_generator_backend(provider_name="local")
    assert isinstance(backend, LocalChatGeneratorBackend)
    assert provider == "local"
    assert build_parser().parse_args(["research-agent-runtime"]).provider == "local"


@pytest.mark.parametrize("url", ["https://api.openai.com/v1", "http://example.org/v1",
                                "http://secret@127.0.0.1/v1", "http://127.0.0.1/v1?key=x"])
def test_local_endpoint_never_uses_cloud_or_credentials(url):
    with pytest.raises(ValueError, match="loopback"):
        LocalChatGeneratorBackend(base_url=url)


def test_retained_history_preserves_tool_identity_and_raw_failure():
    request = replace(_request(), messages=(
        {"role": "assistant", "content": [
            {"type": "text", "text": "Inspecting."},
            {"type": "tool_use", "id": "opaque-id", "name": "observe", "input": {"path": "x"}}]},
        {"role": "user", "content": [{"type": "tool_result", "tool_use_id": "opaque-id",
            "is_error": True, "content": "unmodified diagnostic\nline 12"}]},
    ))
    rows = _chat_messages(request)
    assert rows[1]["tool_calls"][0]["id"] == "opaque-id"
    assert json.loads(rows[1]["tool_calls"][0]["function"]["arguments"]) == {"path": "x"}
    assert rows[2]["role"] == "tool"
    assert rows[2]["tool_call_id"] == "opaque-id"
    assert json.loads(rows[2]["content"]) == {
        "content": "unmodified diagnostic\nline 12", "is_error": True,
    }


def test_http_failure_keeps_server_diagnostic_and_does_not_retry(monkeypatch):
    requests = []
    class Opener:
        def open(self, request, *, timeout):
            requests.append(request)
            raise HTTPError(request.full_url, 400, "Bad Request", {},
                            BytesIO(b'{"error":"raw server diagnostic"}'))
    monkeypatch.setattr("urllib.request.build_opener", lambda *args: Opener())
    with pytest.raises(RuntimeError, match='HTTP 400:.*raw server diagnostic'):
        LocalChatGeneratorBackend().generate(GeneratorRequest(
            system_prompt="Check transport.", user_prompt="Return text.", model="local-fixture",
        ))
    assert len(requests) == 1


def test_tool_transport_does_not_execute_or_repair_calls(monkeypatch):
    seen = []
    raw = {"model": "Qwen3-4B-Instruct-2507", "choices": [{"message": {
        "content": "Inspect first.", "tool_calls": [{"id": "native-id", "function": {
            "name": "observe", "arguments": '{"path":"candidate.md"}'}}]}}]}
    def complete(_self, payload):
        seen.append(payload)
        return raw, {"tools_executed_by_backend": False}
    monkeypatch.setattr(LocalChatGeneratorBackend, "_complete", complete)
    response = LocalChatGeneratorBackend().generate_client_tool_turn(_request())
    assert seen[0]["tool_choice"] == "required"
    assert response.tool_calls[0].input == {"path": "candidate.md"}
    assert response.content_blocks[1]["id"] == "native-id"
    assert response.metadata["tools_executed_by_backend"] is False
    raw["choices"][0]["message"]["tool_calls"][0]["function"]["arguments"] = "broken json"
    with pytest.raises(json.JSONDecodeError):
        LocalChatGeneratorBackend().generate_client_tool_turn(_request())


def test_stateless_structured_generation_uses_server_schema(monkeypatch):
    seen = []
    def complete(_self, payload):
        seen.append(payload)
        return {"choices": [{"message": {"content": '{"ok":true}'}}]}, {}
    monkeypatch.setattr(LocalChatGeneratorBackend, "_complete", complete)
    request = GeneratorRequest(system_prompt="Return JSON.", user_prompt="Check transport.",
                               model="Qwen3-4B-Instruct-2507", schema={"type": "object"})
    response = LocalChatGeneratorBackend().generate(request)
    assert seen[0]["response_format"]["json_schema"]["schema"] == request.schema
    assert response.provider == "local"


def test_unsupported_history_is_not_silently_dropped():
    request = replace(_request(), messages=({"role": "user", "content": [
        {"type": "image", "source": {"data": "opaque"}}]},))
    with pytest.raises(ValueError, match="does not support"):
        _chat_messages(request)


@pytest.mark.skipif(
    os.environ.get("AI_STATISTICIAN_LOCAL_MODEL_CONFORMANCE") != "1",
    reason="opt-in local model transport conformance, not scientific evaluation",
)
def test_live_local_schema_and_retained_raw_observation(tmp_path):
    from ai_statistician.client_tool_loop import (
        ClientToolExecutionResult, run_bounded_client_tool_loop,
    )

    backend = LocalChatGeneratorBackend()
    model = default_generator_model("local")
    response = backend.generate(GeneratorRequest(
        system_prompt="Return the requested JSON value.",
        user_prompt="Return transport_ok true.", model=model, max_tokens=64,
        schema={"type": "object", "properties": {"transport_ok": {"type": "boolean"}},
                "required": ["transport_ok"], "additionalProperties": False},
    ))
    assert json.loads(response.text) == {"transport_ok": True}
    assert response.provider == "local"
    assert response.model == model

    raw_observation = "opaque-feedback-6841\nline 12: fixture failed"
    invoked = []

    def execute(call, _context):
        invoked.append(call.name)
        if call.name == "read_observation":
            return ClientToolExecutionResult(content=raw_observation, is_error=True)
        assert call.name == "submit_observation"
        assert call.input["text"] == raw_observation
        return ClientToolExecutionResult(
            content="Received exact observation.", terminal=True,
            terminal_payload={"text": call.input["text"]},
        )

    request = ClientToolTurnRequest(
        system_prompt="First read_observation, then submit_observation with the exact observed text, including newlines. Do not correct the fixture failure.",
        messages=({"role": "user", "content": "Check tool feedback transport."},),
        model=model, max_tokens=256, temperature=0.0,
        disable_parallel_tool_use=True,
        tools=(
            ClientToolDefinition(name="read_observation", description="Read a raw fixture failure.",
                                 input_schema={"type": "object", "properties": {}, "additionalProperties": False}),
            ClientToolDefinition(name="submit_observation", description="Submit the exact raw text.", terminal=True,
                                 input_schema={"type": "object", "properties": {"text": {"type": "string"}},
                                               "required": ["text"], "additionalProperties": False}),
        ),
    )
    result = run_bounded_client_tool_loop(
        backend=backend, request=request, execute_tool=execute,
        max_turns=4, max_tool_calls=4, max_no_progress_turns=2,
        session_dir=tmp_path / "session", session_id="local-feedback-conformance",
    )
    assert result.provider == "local"
    assert result.model == model
    assert invoked[0] == "read_observation"
    assert invoked[-1] == "submit_observation"
    assert result.terminal_payload == {"text": raw_observation}
    assert result.provider_usage["input_tokens"] > 0
    assert result.provider_usage["output_tokens"] > 0
    print(json.dumps({"provider": result.provider, "model": result.model,
                      "turns": result.turns, "tool_calls": result.tool_calls,
                      "provider_usage": dict(result.provider_usage),
                      "transcript_fingerprint": result.transcript_fingerprint,
                      "session_root": str(tmp_path / "session")}))
