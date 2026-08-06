from __future__ import annotations

import re
import sys
import time
from pathlib import Path
from types import SimpleNamespace

import pytest

from ai_statistician.model_backend import (
    AI_STATISTICIAN_LLM_CONTEXTUAL_MODEL_TIER_POLICY,
    AI_STATISTICIAN_LLM_SUBSYSTEM_MODEL_TIER_POLICY,
    ANTHROPIC_CLAUDE_MODEL_SELECTION_POLICY,
    ANTHROPIC_CLAUDE_TIER_ENV_VARS,
    ANTHROPIC_MODEL_ID_VERSIONING_POLICY,
    ANTHROPIC_MODEL_SOURCE_CHECKED_DATE,
    ANTHROPIC_MODEL_SOURCE_EVIDENCE,
    DEFAULT_CLAUDE_GENERATOR_MODEL_ALIASES_BY_TIER,
    DEFAULT_LIVE_GENERATOR_TIMEOUT_SECONDS,
    SUPPORTED_GENERATOR_PROVIDERS,
    SUPPORTED_LIVE_GENERATOR_PROVIDERS,
    SUPPORTED_STATIC_REPLAY_GENERATOR_PROVIDERS,
    AnthropicGeneratorBackend,
    ClientToolDefinition,
    ClientToolTurnRequest,
    GeneratorRequest,
    LiveGeneratorTimeoutError,
    OpenAIResponsesGeneratorBackend,
    StaticJSONGeneratorBackend,
    _call_with_wall_clock_timeout,
    _prune_unreferenced_json_schema_defs,
    claude_model_freshness_warnings,
    claude_model_tier_for_model,
    claude_model_tier_mismatch,
    claude_model_tier_policy_violations,
    claude_tier_routing_contract,
    default_generator_model,
    default_generator_provider,
    llm_subsystem_expected_model_tier,
    resolved_claude_models_by_tier,
    resolve_live_evaluation_model,
)


def _request() -> GeneratorRequest:
    return GeneratorRequest(
        system_prompt="Return JSON.",
        user_prompt="Produce a theory packet.",
        model="claude-sonnet-4-6",
        max_tokens=128,
        temperature=0.0,
        schema={"type": "object", "properties": {"ok": {"type": "boolean"}}},
    )


def test_live_evaluation_model_resolver_pins_current_haiku() -> None:
    assert resolve_live_evaluation_model(
        "anthropic",
        "claude-sonnet-4-6",
        env={"AI_STATISTICIAN_CLAUDE_HAIKU_MODEL": "claude-haiku-old"},
    ) == "claude-haiku-4-5-20251001"


def test_static_json_generator_backend_returns_text_without_tools() -> None:
    response = StaticJSONGeneratorBackend({"ok": True}).generate(_request())

    assert response.provider == "static"
    assert response.model == "claude-sonnet-4-6"
    assert '"ok": true' in response.text
    assert response.metadata["generator_only"] is True
    assert response.metadata["tools_available"] is False


def test_anthropic_generator_backend_calls_messages_api_without_tools(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}

    class FakeMessages:
        def create(self, **kwargs):
            captured["kwargs"] = kwargs
            return SimpleNamespace(
                content=[SimpleNamespace(text='{"ok": true}')],
                stop_reason="end_turn",
                usage=SimpleNamespace(input_tokens=11, output_tokens=5),
            )

    class FakeAnthropicClient:
        def __init__(self, *, api_key: str, timeout: float, max_retries: int) -> None:
            captured["api_key"] = api_key
            captured["timeout"] = timeout
            captured["max_retries"] = max_retries
            self.messages = FakeMessages()

    fake_anthropic_module = SimpleNamespace(Anthropic=FakeAnthropicClient)
    monkeypatch.setitem(sys.modules, "anthropic", fake_anthropic_module)

    response = AnthropicGeneratorBackend(api_key="test-anthropic-key").generate(
        _request()
    )

    assert captured["api_key"] == "test-anthropic-key"
    assert captured["timeout"] == 120.0
    assert captured["max_retries"] == 0
    kwargs = captured["kwargs"]
    assert kwargs["model"] == "claude-sonnet-4-6"
    assert kwargs["max_tokens"] == 128
    assert kwargs["temperature"] == 0.0
    assert kwargs["system"] == "Return JSON."
    assert kwargs["messages"] == [
        {
            "role": "user",
            "content": (
                "Produce a theory packet.\n\n"
                "Return exactly one valid JSON object. Do not wrap it in Markdown. "
                "Do not include commentary outside JSON."
            ),
        }
    ]
    assert "tools" not in kwargs
    assert response.text == '{"ok": true}'
    assert response.provider == "anthropic"
    assert response.metadata["generator_only"] is True
    assert response.metadata["tools_available"] is False
    assert response.metadata["schema_supplied"] is True
    assert response.metadata["json_prompt_hint_used"] is True
    assert response.metadata["timeout_seconds"] == 120.0
    assert response.metadata["retry_count"] == 0
    assert response.metadata["provider_stop_reason"] == "end_turn"
    assert response.metadata["provider_usage"] == {
        "input_tokens": 11,
        "output_tokens": 5,
    }


def test_anthropic_generator_backend_transports_client_tool_turn(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}

    class FakeMessages:
        def create(self, **kwargs):
            captured["kwargs"] = kwargs
            return SimpleNamespace(
                content=[
                    SimpleNamespace(type="text", text="I will inspect it."),
                    SimpleNamespace(
                        type="tool_use",
                        id="toolu_123",
                        name="inspect_artifact",
                        input={"path": ["problem_card", "estimand"]},
                    ),
                ],
                model="claude-haiku-4-5-20251001",
                stop_reason="tool_use",
                usage=SimpleNamespace(input_tokens=31, output_tokens=17),
            )

    class FakeAnthropicClient:
        def __init__(self, *, api_key: str, timeout: float, max_retries: int) -> None:
            self.messages = FakeMessages()

    monkeypatch.setitem(
        sys.modules,
        "anthropic",
        SimpleNamespace(Anthropic=FakeAnthropicClient),
    )
    request = ClientToolTurnRequest(
        system_prompt="Use tools.",
        messages=({"role": "user", "content": "Inspect the theory."},),
        tools=(
            ClientToolDefinition(
                name="inspect_artifact",
                description="Read one artifact path.",
                input_schema={
                    "type": "object",
                    "required": ["path"],
                    "properties": {"path": {"type": "array"}},
                },
            ),
        ),
        model="claude-haiku-4-5-20251001",
        max_tokens=256,
        disable_parallel_tool_use=True,
        metadata={"model_tier": "haiku"},
    )

    response = AnthropicGeneratorBackend(
        api_key="test-anthropic-key"
    ).generate_client_tool_turn(request)

    kwargs = captured["kwargs"]
    assert kwargs["messages"] == [
        {"role": "user", "content": "Inspect the theory."}
    ]
    assert kwargs["tools"] == [
        {
            "name": "inspect_artifact",
            "description": "Read one artifact path.",
            "input_schema": request.tools[0].input_schema,
        }
    ]
    assert kwargs["tool_choice"] == {
        "type": "any",
        "disable_parallel_tool_use": True,
    }
    assert "output_config" not in kwargs
    assert response.text == "I will inspect it."
    assert response.tool_calls[0].call_id == "toolu_123"
    assert response.tool_calls[0].name == "inspect_artifact"
    assert response.tool_calls[0].input == {
        "path": ["problem_card", "estimand"]
    }
    assert response.metadata["client_tool_transport"] is True
    assert response.metadata["generator_only"] is True
    assert response.metadata["tools_executed_by_backend"] is False
    assert response.metadata["disable_parallel_tool_use"] is True
    assert response.metadata["provider_stop_reason"] == "tool_use"


def test_anthropic_client_tool_turn_rejects_opus_before_client_creation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client_created = False

    class FakeAnthropicClient:
        def __init__(self, **kwargs) -> None:
            nonlocal client_created
            client_created = True

    monkeypatch.setitem(
        sys.modules,
        "anthropic",
        SimpleNamespace(Anthropic=FakeAnthropicClient),
    )
    request = ClientToolTurnRequest(
        system_prompt="Use tools.",
        messages=({"role": "user", "content": "Inspect."},),
        tools=(
            ClientToolDefinition(
                name="inspect",
                description="Inspect.",
                input_schema={"type": "object", "properties": {}},
            ),
        ),
        model="claude-opus-4-8",
        metadata={"model_tier": "opus"},
    )

    with pytest.raises(ValueError, match="capped at sonnet"):
        AnthropicGeneratorBackend(
            api_key="test-anthropic-key"
        ).generate_client_tool_turn(request)

    assert client_created is False


def test_anthropic_generator_backend_rejects_opus_before_client_creation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client_created = False

    class FakeAnthropicClient:
        def __init__(self, **kwargs) -> None:
            nonlocal client_created
            client_created = True

    monkeypatch.setitem(
        sys.modules,
        "anthropic",
        SimpleNamespace(Anthropic=FakeAnthropicClient),
    )
    request = GeneratorRequest(
        **{
            **_request().__dict__,
            "model": "claude-opus-4-8",
            "metadata": {"model_tier": "opus"},
        }
    )

    with pytest.raises(ValueError, match="capped at sonnet"):
        AnthropicGeneratorBackend(api_key="test-anthropic-key").generate(request)

    assert client_created is False


def test_anthropic_generator_backend_applies_opted_in_structured_output(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}

    class FakeMessages:
        def create(self, **kwargs):
            captured["kwargs"] = kwargs
            return SimpleNamespace(
                content=[SimpleNamespace(text='{"ok": true}')],
                stop_reason="end_turn",
            )

    class FakeAnthropicClient:
        def __init__(self, *, api_key: str, timeout: float, max_retries: int) -> None:
            self.messages = FakeMessages()

    def transform_schema(schema):
        captured["source_schema"] = schema
        return {
            "type": "object",
            "additionalProperties": False,
            "required": ["ok"],
            "properties": {"ok": {"type": "boolean"}},
        }

    monkeypatch.setitem(
        sys.modules,
        "anthropic",
        SimpleNamespace(
            Anthropic=FakeAnthropicClient,
            transform_schema=transform_schema,
        ),
    )
    request = GeneratorRequest(
        **{
            **_request().__dict__,
            "metadata": {"provider_structured_output": True},
        }
    )

    response = AnthropicGeneratorBackend(api_key="test-anthropic-key").generate(
        request
    )

    assert captured["source_schema"] == request.schema
    kwargs = captured["kwargs"]
    assert kwargs["messages"] == [
        {"role": "user", "content": "Produce a theory packet."}
    ]
    assert kwargs["output_config"] == {
        "format": {
            "type": "json_schema",
            "schema": {
                "type": "object",
                "additionalProperties": False,
                "required": ["ok"],
                "properties": {"ok": {"type": "boolean"}},
            },
        }
    }
    assert response.metadata["schema_supplied"] is True
    assert response.metadata["json_prompt_hint_used"] is False
    assert response.metadata["provider_structured_output_requested"] is True
    assert response.metadata["provider_structured_output_applied"] is True
    assert response.metadata[
        "provider_structured_output_schema_fingerprint"
    ]


@pytest.mark.parametrize(
    "structured_output_error",
    [
        (
            "The compiled grammar is too large, which would cause performance "
            "issues. Simplify your tool schemas or reduce the number of strict tools."
        ),
        (
            "Schema is too complex for compilation. Try reducing the number of "
            "tools or simplifying tool schemas."
        ),
    ],
)
def test_anthropic_generator_backend_falls_back_from_oversized_strict_schema(
    monkeypatch: pytest.MonkeyPatch,
    structured_output_error: str,
) -> None:
    calls: list[dict[str, object]] = []

    class BadRequestError(Exception):
        pass

    class FakeMessages:
        def create(self, **kwargs):
            calls.append(dict(kwargs))
            if "output_config" in kwargs:
                raise BadRequestError(structured_output_error)
            return SimpleNamespace(
                content=[SimpleNamespace(text='{"ok": true}')],
                model="claude-sonnet-4-6",
            )

    class FakeAnthropicClient:
        def __init__(self, *, api_key: str, timeout: float, max_retries: int) -> None:
            self.messages = FakeMessages()

    monkeypatch.setitem(
        sys.modules,
        "anthropic",
        SimpleNamespace(
            Anthropic=FakeAnthropicClient,
            transform_schema=lambda schema: schema,
        ),
    )
    request = GeneratorRequest(
        **{
            **_request().__dict__,
            "metadata": {
                "provider_structured_output": True,
                "model_tier": "sonnet",
            },
        }
    )
    backend = AnthropicGeneratorBackend(api_key="test-anthropic-key")

    response = backend.generate(request)

    assert len(calls) == 2
    assert calls[0]["model"] == calls[1]["model"] == "claude-sonnet-4-6"
    assert "output_config" in calls[0]
    assert "output_config" not in calls[1]
    assert "Return exactly one valid JSON object" in calls[1]["messages"][0][
        "content"
    ]
    assert response.metadata["provider_structured_output_requested"] is True
    assert response.metadata["provider_structured_output_applied"] is False
    assert response.metadata["provider_structured_output_fallback_count"] == 1
    assert response.metadata["provider_structured_output_fallback_reason"] == (
        "anthropic_compiled_grammar_too_large"
    )
    assert response.metadata["provider_structured_output_cached_fallback"] is False
    assert response.metadata["json_prompt_hint_used"] is True
    assert response.metadata["provider_reported_model_tier"] == "sonnet"

    cached_response = backend.generate(request)

    assert len(calls) == 3
    assert "output_config" not in calls[2]
    assert cached_response.metadata["provider_structured_output_applied"] is False
    assert cached_response.metadata["provider_structured_output_fallback_count"] == 0
    assert cached_response.metadata["provider_structured_output_cached_fallback"] is True
    assert cached_response.metadata["json_prompt_hint_used"] is True


def test_anthropic_generator_backend_does_not_mask_other_structured_output_errors(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = {"count": 0}

    class BadRequestError(Exception):
        pass

    class FakeMessages:
        def create(self, **kwargs):
            calls["count"] += 1
            raise BadRequestError("invalid schema keyword")

    class FakeAnthropicClient:
        def __init__(self, *, api_key: str, timeout: float, max_retries: int) -> None:
            self.messages = FakeMessages()

    monkeypatch.setitem(
        sys.modules,
        "anthropic",
        SimpleNamespace(
            Anthropic=FakeAnthropicClient,
            transform_schema=lambda schema: schema,
        ),
    )
    request = GeneratorRequest(
        **{
            **_request().__dict__,
            "metadata": {"provider_structured_output": True},
        }
    )

    with pytest.raises(BadRequestError, match="invalid schema keyword"):
        AnthropicGeneratorBackend(api_key="test-anthropic-key").generate(request)

    assert calls["count"] == 1


def test_structured_output_schema_prunes_only_unreachable_local_definitions() -> None:
    schema = {
        "type": "object",
        "required": ["value"],
        "properties": {"value": {"$ref": "#/$defs/used"}},
        "$defs": {
            "used": {
                "type": "object",
                "required": ["child"],
                "properties": {"child": {"$ref": "#/$defs/transitive"}},
            },
            "transitive": {"type": "string"},
            "unused": {"type": "number"},
        },
    }

    pruned = _prune_unreferenced_json_schema_defs(schema)

    assert set(pruned["$defs"]) == {"used", "transitive"}
    assert "unused" in schema["$defs"]


def test_anthropic_generator_backend_negotiates_rejected_optional_parameter(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[dict[str, object]] = []

    class BadRequestError(Exception):
        pass

    class FakeMessages:
        def create(self, **kwargs):
            calls.append(dict(kwargs))
            if len(calls) == 1:
                raise BadRequestError("`temperature` is deprecated for this model.")
            return SimpleNamespace(
                content=[SimpleNamespace(text='{"ok": true}')],
                model="claude-sonnet-4-6",
            )

    class FakeAnthropicClient:
        def __init__(self, *, api_key: str, timeout: float, max_retries: int) -> None:
            self.messages = FakeMessages()

    monkeypatch.setitem(
        sys.modules,
        "anthropic",
        SimpleNamespace(Anthropic=FakeAnthropicClient),
    )
    request = GeneratorRequest(
        **{
            **_request().__dict__,
            "model": "claude-sonnet-4-6",
            "metadata": {"model_tier": "sonnet"},
        }
    )

    backend = AnthropicGeneratorBackend(api_key="test-anthropic-key")
    response = backend.generate(request)

    assert len(calls) == 2
    assert calls[0]["temperature"] == 0.0
    assert "temperature" not in calls[1]
    assert response.text == '{"ok": true}'
    assert response.metadata["provider_capability_fallback_count"] == 1
    assert response.metadata["omitted_unsupported_request_parameters"] == [
        "temperature"
    ]
    assert response.metadata["retry_count"] == 0

    cached_response = backend.generate(request)

    assert len(calls) == 3
    assert "temperature" not in calls[2]
    assert cached_response.metadata["provider_capability_fallback_count"] == 0
    assert cached_response.metadata["cached_unsupported_request_parameters"] == [
        "temperature"
    ]


def test_anthropic_generator_backend_surfaces_provider_reported_model(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeMessages:
        def create(self, **kwargs):
            return SimpleNamespace(
                content=[SimpleNamespace(text='{"ok": true}')],
                model="claude-sonnet-provider-reported",
            )

    class FakeAnthropicClient:
        def __init__(self, *, api_key: str, timeout: float, max_retries: int) -> None:
            self.messages = FakeMessages()

    monkeypatch.setitem(
        sys.modules,
        "anthropic",
        SimpleNamespace(Anthropic=FakeAnthropicClient),
    )

    request = GeneratorRequest(
        **{
            **_request().__dict__,
            "model": "claude-sonnet-4-6",
            "metadata": {"model_tier": "sonnet", "requested_model_tier": "sonnet"},
        }
    )
    response = AnthropicGeneratorBackend(api_key="test-anthropic-key").generate(request)

    assert response.model == "claude-sonnet-provider-reported"
    assert response.metadata["requested_model"] == "claude-sonnet-4-6"
    assert (
        response.metadata["provider_reported_model"]
        == "claude-sonnet-provider-reported"
    )
    assert response.metadata["request_model_tier"] == "sonnet"
    assert response.metadata["requested_model_tier"] == "sonnet"
    assert response.metadata["request_model_family_tier"] == "sonnet"
    assert response.metadata["provider_reported_model_tier"] == "sonnet"
    assert response.metadata["provider_reported_model_tier_mismatch"] == ""
    assert response.metadata["requested_model_tier_mismatch"] == ""


def test_anthropic_generator_backend_records_provider_model_tier_mismatch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeMessages:
        def create(self, **kwargs):
            return SimpleNamespace(
                content=[SimpleNamespace(text='{"ok": true}')],
                model="claude-sonnet-4-6",
            )

    class FakeAnthropicClient:
        def __init__(self, *, api_key: str, timeout: float, max_retries: int) -> None:
            self.messages = FakeMessages()

    monkeypatch.setitem(
        sys.modules,
        "anthropic",
        SimpleNamespace(Anthropic=FakeAnthropicClient),
    )

    request = GeneratorRequest(
        **{
            **_request().__dict__,
            "model": "claude-haiku-4-5-20251001",
            "metadata": {"model_tier": "haiku", "requested_model_tier": "haiku"},
        }
    )
    response = AnthropicGeneratorBackend(api_key="test-anthropic-key").generate(request)

    assert response.metadata["request_model_tier"] == "haiku"
    assert response.metadata["requested_model_tier"] == "haiku"
    assert response.metadata["request_model_family_tier"] == "haiku"
    assert response.metadata["provider_reported_model_tier"] == "sonnet"
    assert (
        response.metadata["provider_reported_model_tier_mismatch"]
        == (
            "provider reported model expected Claude haiku tier but is "
            "configured with claude-sonnet-4-6"
        )
    )
    assert response.metadata["requested_model_tier_mismatch"] == ""


def test_openai_generator_backend_surfaces_provider_reported_model(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeResponses:
        def create(self, **kwargs):
            return SimpleNamespace(
                output_text='{"ok": true}',
                model="openai-provider-reported",
            )

    class FakeOpenAIClient:
        def __init__(self, *, api_key: str) -> None:
            self.responses = FakeResponses()

    monkeypatch.setitem(
        sys.modules,
        "openai",
        SimpleNamespace(OpenAI=FakeOpenAIClient),
    )

    response = OpenAIResponsesGeneratorBackend(api_key="test-openai-key").generate(
        _request()
    )

    assert response.model == "openai-provider-reported"
    assert response.metadata["requested_model"] == "claude-sonnet-4-6"
    assert (
        response.metadata["provider_reported_model"]
        == "openai-provider-reported"
    )


def test_anthropic_generator_backend_honors_explicit_timeout(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}

    class FakeMessages:
        def create(self, **kwargs):
            return SimpleNamespace(content=[SimpleNamespace(text='{"ok": true}')])

    class FakeAnthropicClient:
        def __init__(self, *, api_key: str, timeout: float, max_retries: int) -> None:
            captured["timeout"] = timeout
            captured["max_retries"] = max_retries
            self.messages = FakeMessages()

    monkeypatch.setitem(sys.modules, "anthropic", SimpleNamespace(Anthropic=FakeAnthropicClient))

    response = AnthropicGeneratorBackend(
        api_key="test-anthropic-key",
        timeout_s=17.5,
    ).generate(_request())

    assert captured["timeout"] == 17.5
    assert captured["max_retries"] == 0
    assert response.metadata["timeout_seconds"] == 17.5
    assert DEFAULT_LIVE_GENERATOR_TIMEOUT_SECONDS == 120.0


def test_anthropic_generator_backend_retries_transient_connection_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("AI_STATISTICIAN_LLM_MAX_RETRIES", "2")
    monkeypatch.setenv("AI_STATISTICIAN_LLM_RETRY_BACKOFF_SECONDS", "0")
    calls = {"count": 0}

    class APIConnectionError(Exception):
        pass

    class FakeMessages:
        def create(self, **kwargs):
            calls["count"] += 1
            if calls["count"] == 1:
                raise APIConnectionError("Connection error.")
            return SimpleNamespace(content=[SimpleNamespace(text='{"ok": true}')])

    class FakeAnthropicClient:
        def __init__(self, *, api_key: str, timeout: float, max_retries: int) -> None:
            self.messages = FakeMessages()

    monkeypatch.setitem(sys.modules, "anthropic", SimpleNamespace(Anthropic=FakeAnthropicClient))

    response = AnthropicGeneratorBackend(api_key="test-anthropic-key").generate(_request())

    assert calls["count"] == 2
    assert response.text == '{"ok": true}'
    assert response.metadata["retry_count"] == 1


def test_anthropic_generator_backend_does_not_retry_timeout_by_default(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("AI_STATISTICIAN_LLM_MAX_RETRIES", "2")
    monkeypatch.setenv("AI_STATISTICIAN_LLM_RETRY_BACKOFF_SECONDS", "0")
    calls = {"count": 0}

    class APITimeoutError(Exception):
        pass

    class FakeMessages:
        def create(self, **kwargs):
            calls["count"] += 1
            raise APITimeoutError("request timed out")

    class FakeAnthropicClient:
        def __init__(self, *, api_key: str, timeout: float, max_retries: int) -> None:
            self.messages = FakeMessages()

    monkeypatch.setitem(sys.modules, "anthropic", SimpleNamespace(Anthropic=FakeAnthropicClient))

    with pytest.raises(APITimeoutError, match="timed out"):
        AnthropicGeneratorBackend(api_key="test-anthropic-key").generate(_request())

    assert calls["count"] == 1


def test_anthropic_generator_backend_enforces_outer_wall_clock_timeout(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("AI_STATISTICIAN_LLM_MAX_RETRIES", "2")
    monkeypatch.setenv("AI_STATISTICIAN_LLM_RETRY_BACKOFF_SECONDS", "0")
    calls = {"count": 0}

    class FakeMessages:
        def create(self, **kwargs):
            calls["count"] += 1
            time.sleep(2.0)
            return SimpleNamespace(content=[SimpleNamespace(text='{"ok": true}')])

    class FakeAnthropicClient:
        def __init__(self, *, api_key: str, timeout: float, max_retries: int) -> None:
            self.messages = FakeMessages()

    monkeypatch.setitem(sys.modules, "anthropic", SimpleNamespace(Anthropic=FakeAnthropicClient))

    started = time.monotonic()
    with pytest.raises(LiveGeneratorTimeoutError, match="wall-clock timeout 1s"):
        AnthropicGeneratorBackend(
            api_key="test-anthropic-key",
            timeout_s=1.0,
        ).generate(_request())

    assert calls["count"] == 1
    assert time.monotonic() - started < 1.8


def test_wall_clock_timeout_respects_shorter_nested_deadline() -> None:
    started = time.monotonic()

    with pytest.raises(LiveGeneratorTimeoutError):
        _call_with_wall_clock_timeout(
            lambda: _call_with_wall_clock_timeout(
                lambda: time.sleep(2.0),
                timeout_s=5.0,
                provider_name="inner",
                model="slow-model",
            ),
            timeout_s=0.4,
            provider_name="outer",
            model="route-planner",
        )

    assert time.monotonic() - started < 1.3


def test_anthropic_generator_backend_does_not_retry_non_transport_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("AI_STATISTICIAN_LLM_MAX_RETRIES", "2")
    calls = {"count": 0}

    class FakeMessages:
        def create(self, **kwargs):
            calls["count"] += 1
            raise ValueError("invalid request shape")

    class FakeAnthropicClient:
        def __init__(self, *, api_key: str, timeout: float, max_retries: int) -> None:
            self.messages = FakeMessages()

    monkeypatch.setitem(sys.modules, "anthropic", SimpleNamespace(Anthropic=FakeAnthropicClient))

    with pytest.raises(ValueError, match="invalid request shape"):
        AnthropicGeneratorBackend(api_key="test-anthropic-key").generate(_request())

    assert calls["count"] == 1


def test_live_generator_defaults_to_anthropic_cost_aware_tiers(monkeypatch: pytest.MonkeyPatch) -> None:
    for key in (
        "AI_STATISTICIAN_LLM_PROVIDER",
        "AI_STATISTICIAN_LLM_MODEL",
        "AI_STATISTICIAN_ANTHROPIC_MODEL",
        "AI_STATISTICIAN_CLAUDE_HAIKU_MODEL",
        "AI_STATISTICIAN_ANTHROPIC_HAIKU_MODEL",
        "AI_STATISTICIAN_CLAUDE_SONNET_MODEL",
        "AI_STATISTICIAN_ANTHROPIC_SONNET_MODEL",
        "AI_STATISTICIAN_CLAUDE_OPUS_MODEL",
        "AI_STATISTICIAN_ANTHROPIC_OPUS_MODEL",
        "AI_STATISTICIAN_OPENAI_MODEL",
        "AI_STATISTICIAN_THEORY_MODEL",
        "OPENAI_MODEL",
    ):
        monkeypatch.delenv(key, raising=False)

    assert default_generator_provider() == "anthropic"
    assert default_generator_model("anthropic") == "claude-sonnet-5"
    assert default_generator_model("anthropic", model_tier="haiku") == "claude-haiku-4-5-20251001"
    assert default_generator_model("anthropic", model_tier="sonnet") == "claude-sonnet-5"
    with pytest.raises(ValueError, match="capped at sonnet"):
        default_generator_model("anthropic", model_tier="opus")
    assert set(ANTHROPIC_CLAUDE_TIER_ENV_VARS) == {"haiku", "sonnet"}
    assert ANTHROPIC_CLAUDE_MODEL_SELECTION_POLICY[
        "allowed_live_anthropic_model_tiers"
    ] == ["haiku", "sonnet"]
    assert ANTHROPIC_CLAUDE_MODEL_SELECTION_POLICY[
        "max_live_anthropic_model_tier"
    ] == "sonnet"
    assert ANTHROPIC_CLAUDE_MODEL_SELECTION_POLICY["models_by_tier"] == {
        "haiku": "claude-haiku-4-5-20251001",
        "sonnet": "claude-sonnet-5",
    }
    assert (
        ANTHROPIC_CLAUDE_MODEL_SELECTION_POLICY["api_aliases_by_tier"]
        == DEFAULT_CLAUDE_GENERATOR_MODEL_ALIASES_BY_TIER
        == {
            "haiku": "claude-haiku-4-5",
            "sonnet": "claude-sonnet-5",
        }
    )
    assert ANTHROPIC_CLAUDE_MODEL_SELECTION_POLICY[
        "prohibited_live_anthropic_model_tiers"
    ] == ["opus"]
    assert "runtime calls" in ANTHROPIC_CLAUDE_MODEL_SELECTION_POLICY[
        "runtime_model_id_policy"
    ]
    assert (
        ANTHROPIC_CLAUDE_MODEL_SELECTION_POLICY["subsystem_model_tier_policy"]
        == AI_STATISTICIAN_LLM_SUBSYSTEM_MODEL_TIER_POLICY
    )
    assert (
        ANTHROPIC_CLAUDE_MODEL_SELECTION_POLICY["contextual_model_tier_policy"]
        == AI_STATISTICIAN_LLM_CONTEXTUAL_MODEL_TIER_POLICY
        == {"TheoryDeveloper:serious": "sonnet"}
    )
    assert llm_subsystem_expected_model_tier("TheoryDeveloper") == "sonnet"
    assert llm_subsystem_expected_model_tier("FormalizerProofEngineer") == "sonnet"
    assert llm_subsystem_expected_model_tier(
        "ArchitectMetricRepairOwnershipRouter"
    ) == "sonnet"
    assert llm_subsystem_expected_model_tier("SimulationEngineer") == "sonnet"
    assert llm_subsystem_expected_model_tier("AlgorithmEngineer") == "sonnet"
    assert llm_subsystem_expected_model_tier("CriticEvaluator") == "haiku"
    assert llm_subsystem_expected_model_tier("unknown") == ""
    assert ANTHROPIC_MODEL_SOURCE_CHECKED_DATE == "2026-08-02"
    assert (
        ANTHROPIC_CLAUDE_MODEL_SELECTION_POLICY["source_evidence"]
        == ANTHROPIC_MODEL_SOURCE_EVIDENCE
    )
    assert ANTHROPIC_MODEL_SOURCE_EVIDENCE["verified_latest_cost_tier_api_ids"] == {
        "haiku": "claude-haiku-4-5-20251001",
        "sonnet": "claude-sonnet-5",
    }
    assert "pinned snapshots" in " ".join(
        str(claim) for claim in ANTHROPIC_MODEL_SOURCE_EVIDENCE["claims"]
    )
    assert "opus" not in ANTHROPIC_CLAUDE_MODEL_SELECTION_POLICY["models_by_tier"]
    assert "higher-tier model ID" in ANTHROPIC_CLAUDE_MODEL_SELECTION_POLICY[
        "runtime_model_id_policy"
    ]
    assert ANTHROPIC_CLAUDE_MODEL_SELECTION_POLICY["tier_specific_model_env_vars"] == ANTHROPIC_CLAUDE_TIER_ENV_VARS
    assert "Sonnet-tier defaults only" in ANTHROPIC_CLAUDE_MODEL_SELECTION_POLICY["global_model_override_policy"]
    assert "pinned snapshots" in ANTHROPIC_MODEL_ID_VERSIONING_POLICY
    assert "not evergreen aliases" in ANTHROPIC_MODEL_ID_VERSIONING_POLICY
    assert default_generator_model("static") == "static"

    monkeypatch.setenv("AI_STATISTICIAN_LLM_PROVIDER", "codex_exec")
    monkeypatch.setenv("AI_STATISTICIAN_LLM_MODEL", "gpt-codex-test")
    assert default_generator_provider() == "anthropic"
    assert default_generator_model("anthropic") == "claude-sonnet-5"
    assert default_generator_model("anthropic", model_tier="haiku") == "claude-haiku-4-5-20251001"
    assert default_generator_model("codex") == ""
    assert default_generator_model("codex_exec") == ""

    monkeypatch.setenv("AI_STATISTICIAN_LLM_PROVIDER", "static")
    assert default_generator_provider() == "anthropic"
    assert default_generator_model("static") == "static"
    static_warning_contract = claude_tier_routing_contract()
    assert static_warning_contract["effective_live_generator_provider"] == "anthropic"
    assert static_warning_contract["supported_live_generator_providers"] == (
        "anthropic",
        "openai",
    )
    assert static_warning_contract["supported_generator_providers"] == (
        "anthropic",
        "openai",
        "static",
    )
    assert static_warning_contract["static_replay_generator_providers"] == ("static",)
    assert set(SUPPORTED_LIVE_GENERATOR_PROVIDERS) == {"anthropic", "openai"}
    assert set(SUPPORTED_STATIC_REPLAY_GENERATOR_PROVIDERS) == {"static"}
    assert set(SUPPORTED_GENERATOR_PROVIDERS) == {"anthropic", "openai", "static"}
    assert static_warning_contract["environment_override_status"] == "WARN"
    assert any(
        "static is supported only as an explicit fixture/replay backend" in warning
        for warning in static_warning_contract["provider_override_warnings"]
    )

    monkeypatch.setenv("AI_STATISTICIAN_LLM_PROVIDER", "anthropic")
    monkeypatch.setenv("AI_STATISTICIAN_ANTHROPIC_MODEL", "claude-sonnet-test")
    assert default_generator_provider() == "anthropic"
    assert default_generator_model("anthropic") == "claude-sonnet-test"
    assert default_generator_model("anthropic", model_tier="haiku") == "claude-haiku-4-5-20251001"
    with pytest.raises(ValueError, match="capped at sonnet"):
        default_generator_model("anthropic", model_tier="opus")

    monkeypatch.delenv("AI_STATISTICIAN_ANTHROPIC_MODEL", raising=False)
    monkeypatch.setenv("AI_STATISTICIAN_CLAUDE_HAIKU_MODEL", "claude-haiku-test")
    monkeypatch.setenv("AI_STATISTICIAN_CLAUDE_SONNET_MODEL", "claude-sonnet-test")
    monkeypatch.setenv("AI_STATISTICIAN_CLAUDE_OPUS_MODEL", "claude-opus-test")
    assert default_generator_model("anthropic", model_tier="haiku") == "claude-haiku-test"
    assert default_generator_model("anthropic", model_tier="sonnet") == "claude-sonnet-test"
    with pytest.raises(ValueError, match="capped at sonnet"):
        default_generator_model("anthropic", model_tier="opus")


def test_global_model_env_does_not_collapse_anthropic_cost_aware_tiers(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("AI_STATISTICIAN_LLM_MODEL", "claude-sonnet-5")
    models = {
        "haiku": default_generator_model("anthropic", model_tier="haiku"),
        "sonnet": default_generator_model("anthropic", model_tier="sonnet"),
    }

    assert models == {
        "haiku": "claude-haiku-4-5-20251001",
        "sonnet": "claude-sonnet-5",
    }
    assert claude_model_tier_policy_violations(models) == []
    assert claude_model_freshness_warnings(models) == []


def test_claude_tier_routing_contract_reports_subsystem_policy_and_warnings(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    clean_env = {"AI_STATISTICIAN_LLM_PROVIDER": "anthropic"}

    assert resolved_claude_models_by_tier(clean_env) == {
        "haiku": "claude-haiku-4-5-20251001",
        "sonnet": "claude-sonnet-5",
    }
    clean_contract = claude_tier_routing_contract(clean_env)
    assert clean_contract["contract_name"] == "anthropic_claude_tier_routing_contract"
    assert clean_contract["effective_live_generator_provider"] == "anthropic"
    assert clean_contract["resolved_claude_models_by_tier"] == {
        "haiku": "claude-haiku-4-5-20251001",
        "sonnet": "claude-sonnet-5",
    }
    assert clean_contract["allowed_live_anthropic_model_tiers"] == (
        "haiku",
        "sonnet",
    )
    assert clean_contract["resolved_claude_model_tier_policy_status"] == "OK"
    assert clean_contract["environment_override_status"] == "OK"
    assert clean_contract["subsystem_model_tier_policy"] == (
        AI_STATISTICIAN_LLM_SUBSYSTEM_MODEL_TIER_POLICY
    )
    assert clean_contract["contextual_model_tier_policy"] == (
        AI_STATISTICIAN_LLM_CONTEXTUAL_MODEL_TIER_POLICY
    )
    assert clean_contract["all_ok"] is True

    monkeypatch.setenv("AI_STATISTICIAN_LLM_PROVIDER", "codex_exec")
    warning_contract = claude_tier_routing_contract()
    assert warning_contract["effective_live_generator_provider"] == "anthropic"
    assert warning_contract["environment_override_status"] == "WARN"
    assert any(
        "agent-style provider" in warning
        for warning in warning_contract["provider_override_warnings"]
    )


def test_claude_model_tier_policy_violations_detect_configured_model_collapse() -> None:
    models = {
        "haiku": "claude-sonnet-4-6",
        "sonnet": "claude-sonnet-4-6",
    }
    violations = claude_model_tier_policy_violations(models)
    assert any("Claude haiku tier expected Claude haiku tier" in item for item in violations)
    assert any("collapsed to one resolved model" in item for item in violations)

    outside_tier_violations = claude_model_tier_policy_violations(
        {
            "haiku": "claude-fable-5",
            "sonnet": "claude-sonnet-4-6",
        }
    )
    assert any("unapproved Claude model claude-fable-5" in item for item in outside_tier_violations)


def test_claude_model_freshness_warnings_detect_stale_same_tier_ids() -> None:
    warnings = claude_model_freshness_warnings(
        {
            "haiku": "claude-haiku-4-5",
            "sonnet": "claude-sonnet-4-5",
        }
    )

    assert len(warnings) == 2
    assert any(
        "Claude haiku tier resolves to claude-haiku-4-5" in item
        and "claude-haiku-4-5-20251001" in item
        for item in warnings
    )
    assert any(
        "Claude sonnet tier resolves to claude-sonnet-4-5" in item
        and "claude-sonnet-5" in item
        for item in warnings
    )


def test_claude_model_tier_helpers_detect_cross_tier_model_overrides() -> None:
    assert claude_model_tier_for_model("claude-haiku-4-5-20251001") == "haiku"
    assert claude_model_tier_for_model("claude-sonnet-4-6") == "sonnet"
    assert claude_model_tier_for_model("claude-opus-4-8") == "opus"
    assert claude_model_tier_for_model("custom-anthropic-model") == ""
    assert (
        claude_model_tier_mismatch(
            "claude-sonnet-4-6",
            "haiku",
            subject="SimulationEngineer",
        )
        == "SimulationEngineer expected Claude haiku tier but is configured with claude-sonnet-4-6"
    )
    assert claude_model_tier_mismatch("claude-haiku-4-5-20251001", "haiku") == ""
    assert (
        claude_model_tier_mismatch("claude-fable-5", "sonnet")
        == "expected Claude sonnet tier but is configured with unapproved Claude model claude-fable-5"
    )
    assert claude_model_tier_mismatch("custom-anthropic-model", "haiku") == ""


def test_operator_docs_preserve_claude_tier_env_contract() -> None:
    env_example = Path(".env.example").read_text(encoding="utf-8")
    production_design = Path("docs/production_design.md").read_text(encoding="utf-8")
    architect_goal = Path("docs/architect_llm_agent_goal.md").read_text(encoding="utf-8")
    readme = Path("README.md").read_text(encoding="utf-8")
    production_design_text = " ".join(production_design.split())
    architect_goal_text = " ".join(architect_goal.split())
    readme_text = " ".join(readme.split())

    for tier, env_vars in ANTHROPIC_CLAUDE_TIER_ENV_VARS.items():
        assert f"claude-{tier}" in env_example
        for env_var in env_vars[:1]:
            assert env_var in env_example
            assert env_var in production_design
    assert (
        f"source-checked {ANTHROPIC_MODEL_SOURCE_CHECKED_DATE}"
        in env_example
    )
    assert "Leave AI_STATISTICIAN_LLM_MODEL unset" in env_example
    assert "must not collapse cost-aware Haiku/Sonnet routing" in production_design_text
    assert "Codex/Codex exec are not accepted as pure LLM providers" in env_example
    assert "not normal pure-LLM" in architect_goal_text
    assert "not treated as normal pure-LLM" in readme_text


def test_legacy_demo_scripts_use_pinned_claude_haiku_snapshot() -> None:
    legacy_scripts = [
        Path("Preliminary Attempt/stat_agent.py"),
        Path("Preliminary Attempt/formal_proof_eval.py"),
        Path("Preliminary Attempt/stat_research_agent.py"),
    ]
    bare_haiku_alias = re.compile(r"(?<![A-Za-z0-9_-])claude-haiku-4-5(?!-[0-9])")

    for script in legacy_scripts:
        text = script.read_text(encoding="utf-8")
        assert "claude-haiku-4-5-20251001" in text
        assert bare_haiku_alias.search(text) is None
