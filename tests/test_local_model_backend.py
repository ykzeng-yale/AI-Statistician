from __future__ import annotations

import json
import os
from dataclasses import replace
from io import BytesIO
from urllib.error import HTTPError

import pytest

from ai_statistician.cli import (
    _apply_research_agent_runtime_evaluation_model_policy,
    _build_theory_generator_backend, _runtime_evaluation_model_name, build_parser,
)
from ai_statistician.agent_runtime import (
    AgentRuntime, AgentStepResult, AgentTask, BlackboardState,
    mark_workspace_continuation,
)
from ai_statistician.client_tool_loop import (
    ClientToolExecutionResult, ClientToolLoopError, load_client_tool_session,
    persist_client_tool_session, run_bounded_client_tool_loop,
)
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


@pytest.mark.parametrize("mode", ["--research-eval", "--capability-eval"])
@pytest.mark.parametrize("flag", ["--provider", "--algorithm-engineer-provider", "--formalizer-provider"])
@pytest.mark.parametrize("cloud", ["anthropic", "openai"])
def test_evaluation_rejects_cloud_before_backend_construction(mode, flag, cloud):
    args = build_parser().parse_args(["research-agent-runtime", mode])
    setattr(args, flag.removeprefix("--").replace("-", "_"), cloud)
    with pytest.raises(ValueError, match="require local Qwen"):
        _apply_research_agent_runtime_evaluation_model_policy(args)


def test_server_cannot_substitute_model_identity(monkeypatch):
    requests = []
    class Opener:
        def open(self, request, *, timeout):
            requests.append(request)
            return BytesIO(json.dumps({"model": "another-model"}).encode())
    monkeypatch.setattr("urllib.request.build_opener", lambda *args: Opener())
    with pytest.raises(ValueError, match="model identity mismatch"):
        LocalChatGeneratorBackend().generate(GeneratorRequest(
            system_prompt="Check identity.", user_prompt="Return text.",
            model="Qwen3-4B-Instruct-2507",
        ))
    assert len(requests) == 1


@pytest.mark.parametrize("mode", ["--research-eval", "--capability-eval"])
def test_evaluation_honors_the_explicit_local_pin_without_role_substitution(mode):
    args = build_parser().parse_args([
        "research-agent-runtime", mode, "--llm-model", "opaque-local-checkpoint",
    ])
    _apply_research_agent_runtime_evaluation_model_policy(args)
    assert args.evaluation_model == "opaque-local-checkpoint"
    for configured in ("", "opaque-local-checkpoint"):
        assert _runtime_evaluation_model_name(
            args, provider_choice="same", configured_model=configured,
        ) == "opaque-local-checkpoint"
    with pytest.raises(ValueError, match="differs from the frozen evaluation model"):
        _runtime_evaluation_model_name(
            args, provider_choice="same", configured_model="an-unselected-local-checkpoint",
        )


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


def test_inline_critic_uses_required_single_tool_on_actual_local_wire(monkeypatch):
    from ai_statistician.critic_evaluator_llm import (
        CRITIC_EVALUATION_SUBMIT_TOOL, CriticEvaluatorConfig, LLMCriticEvaluatorAgent,
    )
    from ai_statistician.packet_validation import PacketValidationError
    from ai_statistician.research_schema import OpenResearchQuestion

    requests = _mock_local_completion(monkeypatch, error=True)
    critic = LLMCriticEvaluatorAgent(provider=LocalChatGeneratorBackend(), config=CriticEvaluatorConfig(
        provider_name="local", model="Qwen3-4B-Instruct-2507", model_tier="local",
    ))
    with pytest.raises(PacketValidationError):
        critic.propose(
            question=OpenResearchQuestion(id="opaque-inline", title="Opaque audit", description="No scientific claim."),
            retrieval_manifest={}, theory_packet={}, simulation_manifest={}, algorithm_manifest={},
            formalization_manifest={}, canonical_evidence_view={"artifact_kind": "CriticCanonicalEvidenceView",
                "view_hash": "opaque-inline-view", "dimension_requirements": {"theory": "required"}},
        )
    assert len(requests) == 1
    assert requests[0]["tool_choice"] == "required"
    assert [row["function"]["name"] for row in requests[0]["tools"]] == [CRITIC_EVALUATION_SUBMIT_TOOL]


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


def _mock_local_completion(monkeypatch, *, usage=None, tool_calls=None, error=False, finish_reason="stop"):
    requests = []
    raw = {"model": "Qwen3-4B-Instruct-2507", "choices": [{
        "message": {"content": "transport fixture", "tool_calls": tool_calls or []},
        "finish_reason": finish_reason,
    }], "timings": {"prompt_n": 10, "cache_n": 20, "prompt_ms": 12.5,
                     "predicted_ms": 8.0, "not_a_timing": "omitted"}}
    if usage is not None:
        raw["usage"] = usage

    class Opener:
        def open(self, request, *, timeout):
            requests.append(json.loads(request.data))
            if error:
                raise HTTPError(request.full_url, 400, "Bad Request", {},
                                BytesIO(b'{"error":"opaque transport failure"}'))
            return BytesIO(json.dumps(raw).encode())

    monkeypatch.setattr("urllib.request.build_opener", lambda *args: Opener())
    return requests


@pytest.mark.parametrize("finish_reason", ["length", "stop", "tool_calls", "content_filter", "unknown"])
def test_local_transport_preserves_raw_finish_and_normalizes_output_limit(monkeypatch, finish_reason):
    _mock_local_completion(monkeypatch, finish_reason=finish_reason)
    response = LocalChatGeneratorBackend().generate_client_tool_turn(_request())
    assert response.raw["choices"][0]["finish_reason"] == finish_reason
    assert response.metadata["finish_reason"] == finish_reason
    assert response.metadata["provider_stop_reason"] == ("max_tokens" if finish_reason == "length" else finish_reason)


@pytest.mark.parametrize("with_call", [False, True])
def test_local_output_limit_reaches_shared_loop_without_executing_truncated_turn(monkeypatch, with_call):
    calls = [{"id": "opaque", "function": {"name": "observe", "arguments": "{}"}}] if with_call else []
    requests = _mock_local_completion(monkeypatch, tool_calls=calls, finish_reason="length")
    executed = []
    with pytest.raises(ClientToolLoopError) as stopped:
        run_bounded_client_tool_loop(backend=LocalChatGeneratorBackend(), request=_request(),
            execute_tool=lambda call, context: executed.append(call),
            max_turns=1, max_tool_calls=1, max_no_progress_turns=1)
    assert len(requests) == 1
    assert executed == []
    row = stopped.value.history[0]
    assert row["stop_reason"] == "max_tokens" and row["provider_output_truncated"] is True
    if with_call:
        assert row["tool_calls"][0]["executed_by_runtime"] is False
        assert "provider_tool_input_truncated" in row["tool_calls"][0]["result_excerpt"]
    else:
        assert "ended at max_tokens" in stopped.value.reason


@pytest.mark.parametrize("limit", [None, 4, 3])
def test_local_request_scope_spans_roles_and_workspace_continuations(monkeypatch, limit):
    requests = _mock_local_completion(monkeypatch, usage={
        "prompt_tokens": 30, "completion_tokens": 4, "total_tokens": 34,
        "prompt_tokens_details": {"cached_tokens": 20},
    })
    progress, routed = [], []

    class Subsystem:
        def __init__(self, name):
            self.name = name
            self.backend = LocalChatGeneratorBackend()

        def run(self, task, blackboard):
            if self.name == "Author":
                self.backend.generate_client_tool_turn(_request())
            else:
                self.backend.generate(GeneratorRequest(
                    system_prompt="fixture", user_prompt="opaque input",
                    model="Qwen3-4B-Instruct-2507",
                ))
            index = int(task.task_id)
            next_owner = ("Author", "Author", "Reviewer")[index] if index < 3 else ""
            next_task = AgentTask(str(index + 1), next_owner, "opaque objective") if next_owner else None
            if next_owner == task.owner_subsystem:
                next_task = mark_workspace_continuation(parent_task=task, next_task=next_task)
            return AgentStepResult(
                status="REROUTE" if next_task else "ACCEPTED", rationale="fixture observed",
                next_task=next_task,
                produced_artifacts={f"observed:{index}": {"opaque": index}},
            )

    def policy(**kwargs):
        routed.append(kwargs["subsystem_name"])
        return kwargs["result"]

    runtime = AgentRuntime(
        subsystems={name: Subsystem(name) for name in ("Planner", "Author", "Reviewer")},
        blackboard=BlackboardState(project_id="fixture"), handoff_policy=policy,
    )
    result = runtime.run(AgentTask("0", "Planner", "opaque objective"),
                         max_iterations=6, progress_callback=progress.append,
                         local_model_call_limit=limit)
    n = 4 if limit is None else limit
    denied = limit == 3
    assert len(requests) == n
    assert result.status == ("BLOCKED" if denied else "ACCEPTED")
    assert result.workspace_continuations_consumed == 1
    usage = result.local_model_usage
    assert usage["attempted_requests"] == n
    assert usage["denied_requests"] == int(denied)
    assert usage["requests_with_complete_token_usage"] == n
    assert usage["requests_with_reported_cache_usage"] == n
    assert usage["reported_usage_totals"] == {
        "input_tokens": 30 * n, "output_tokens": 4 * n, "total_tokens": 34 * n,
        "cache_read_input_tokens": 20 * n,
    }
    assert len(routed) == n
    finishes = [row for row in progress if row.get("substage") == "local_model_request"
                and row["event_type"] == "substage_finish"]
    assert len(finishes) == n
    assert [row["metadata"]["request_index"] for row in finishes] == list(range(1, n + 1))
    assert finishes[0]["metadata"]["server_timings"]["prompt_ms"] == 12.5
    assert "not_a_timing" not in finishes[0]["metadata"]["server_timings"]
    if denied:
        assert result.pending_task_checkpoint_reason == "local_model_call_budget_exhausted"
        assert result.pending_task.owner_subsystem == "Reviewer"
        assert "observed:2" in result.blackboard.artifacts
    before = dict(usage)
    LocalChatGeneratorBackend().generate(GeneratorRequest(
        system_prompt="external evaluation fixture", user_prompt="not product work",
        model="Qwen3-4B-Instruct-2507",
    ))
    assert result.local_model_usage == before
    assert len(requests) == n + 1


def test_shared_call_limit_keeps_source_and_retained_raw_observation(monkeypatch, tmp_path):
    requests = _mock_local_completion(monkeypatch, usage={
        "prompt_tokens": 30, "completion_tokens": 4, "total_tokens": 34,
    }, tool_calls=[{"id": "opaque-call", "function": {
        "name": "observe", "arguments": "{}",
    }}])
    source = tmp_path / "candidate.txt"
    model_source = "opaque model-owned source\n"
    raw_feedback = "unmodified environment failure\nline 12: opaque observation"
    request = _request()
    errors = []

    class SourceOwner:
        name = "SourceOwner"

        def run(self, task, blackboard):
            def execute(call, context):
                assert call.name == "observe"
                source.write_text(model_source)
                return ClientToolExecutionResult(
                    content=raw_feedback, is_error=True, state_changed=True,
                )

            try:
                run_bounded_client_tool_loop(
                    backend=LocalChatGeneratorBackend(), request=request,
                    execute_tool=execute, max_turns=3, max_tool_calls=3,
                    max_no_progress_turns=2,
                )
            except ClientToolLoopError as error:
                errors.append(error)
                ref = persist_client_tool_session(
                    session_dir=tmp_path, session_id="owner:fixture",
                    request=request, messages=error.messages,
                )
                return AgentStepResult(
                    status="BLOCKED", rationale="retained pending input",
                    produced_artifacts={"owner:session": ref},
                )
            pytest.fail("an extra model request must not be sent")

    result = AgentRuntime(subsystems={"SourceOwner": SourceOwner()},
                          blackboard=BlackboardState(project_id="fixture")).run(
        AgentTask("source", "SourceOwner", "opaque objective"), local_model_call_limit=1,
    )
    assert len(requests) == len(errors) == 1
    assert result.status == "BLOCKED"
    assert result.pending_task.owner_subsystem == "SourceOwner"
    assert result.pending_task_checkpoint_reason == "local_model_call_budget_exhausted"
    assert source.read_text() == model_source
    error = errors[0]
    assert error.provider_usage == {"input_tokens": 30, "output_tokens": 4, "total_tokens": 34}
    assert error.history[-1]["stop_reason"] == "provider_terminal_error"
    metadata = error.history[-1]["response_metadata"]
    assert metadata["exception_type"] == "LocalModelCallBudgetExceeded"
    assert metadata["automatic_turn_restart"] is False
    assert error.messages[-1]["content"] == [{
        "type": "tool_result", "tool_use_id": "opaque-call",
        "content": raw_feedback, "is_error": True,
    }]
    assert load_client_tool_session(
        result.blackboard.artifacts["owner:session"], session_dir=tmp_path,
        session_id="owner:fixture", request=request,
    ) == tuple(error.messages)


def test_unknown_token_usage_and_failed_transport_are_not_free_calls(monkeypatch):
    requests = _mock_local_completion(monkeypatch, error=True)

    class SourceOwner:
        name = "SourceOwner"

        def run(self, task, blackboard):
            backend = LocalChatGeneratorBackend()
            request = GeneratorRequest(system_prompt="fixture", user_prompt="opaque",
                                       model="Qwen3-4B-Instruct-2507")
            with pytest.raises(RuntimeError, match="opaque transport failure"):
                backend.generate(request)
            backend.generate(request)

    result = AgentRuntime(subsystems={"SourceOwner": SourceOwner()},
                          blackboard=BlackboardState(project_id="fixture")).run(
        AgentTask("source", "SourceOwner", "opaque objective"), local_model_call_limit=1,
    )
    assert result.status == "BLOCKED"
    assert len(requests) == 1
    assert result.local_model_usage["attempted_requests"] == 1
    assert result.local_model_usage["denied_requests"] == 1
    assert result.local_model_usage["requests_with_complete_token_usage"] == 0
    assert result.local_model_usage["reported_usage_totals"] == {}
    assert result.pending_task.task_id == "source"


def test_missing_usage_is_unknown_not_zero(monkeypatch):
    _mock_local_completion(monkeypatch)
    response = LocalChatGeneratorBackend().generate(GeneratorRequest(
        system_prompt="fixture", user_prompt="opaque", model="Qwen3-4B-Instruct-2507",
    ))
    assert response.metadata["provider_usage"] == {}
    assert response.metadata["provider_usage_complete"] is False


def test_partial_usage_preserves_only_reported_counts(monkeypatch):
    _mock_local_completion(monkeypatch, usage={
        "prompt_tokens": 10, "completion_tokens": -1,
        "prompt_tokens_details": {"cached_tokens": False},
    })
    response = LocalChatGeneratorBackend().generate(GeneratorRequest(
        system_prompt="fixture", user_prompt="opaque", model="Qwen3-4B-Instruct-2507",
    ))
    assert response.metadata["provider_usage"] == {"input_tokens": 10}
    assert response.metadata["provider_usage_complete"] is False


@pytest.mark.parametrize("limit", [0, -1, True, 1.5, "3"])
def test_local_call_limit_is_explicit_and_validated_before_work(limit):
    runtime = AgentRuntime(subsystems={}, blackboard=BlackboardState(project_id="fixture"))
    with pytest.raises(ValueError, match="positive integer"):
        runtime.run(AgentTask("source", "SourceOwner", "opaque"), local_model_call_limit=limit)
    args = build_parser().parse_args(["research-agent-runtime"])
    assert args.local_model_call_limit is None


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
