from __future__ import annotations

import re
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from ai_statistician.model_backend import (
    ANTHROPIC_CLAUDE_MODEL_SELECTION_POLICY,
    ANTHROPIC_CLAUDE_TIER_ENV_VARS,
    ANTHROPIC_MODEL_ID_VERSIONING_POLICY,
    ANTHROPIC_MODEL_SOURCE_CHECKED_DATE,
    ANTHROPIC_MODEL_SOURCE_EVIDENCE,
    CLAUDE_FAMILY_MODELS_OUTSIDE_COST_TIERS,
    DEFAULT_CLAUDE_GENERATOR_MODEL_ALIASES_BY_TIER,
    DEFAULT_LIVE_GENERATOR_TIMEOUT_SECONDS,
    AnthropicGeneratorBackend,
    GeneratorRequest,
    OpenAIResponsesGeneratorBackend,
    StaticJSONGeneratorBackend,
    claude_outside_cost_tier_family_for_model,
    claude_model_tier_for_model,
    claude_model_tier_mismatch,
    claude_model_tier_policy_violations,
    default_generator_model,
    default_generator_provider,
)


def _request() -> GeneratorRequest:
    return GeneratorRequest(
        system_prompt="Return JSON.",
        user_prompt="Produce a theory packet.",
        model="test-model",
        max_tokens=128,
        temperature=0.0,
        schema={"type": "object", "properties": {"ok": {"type": "boolean"}}},
    )


def test_static_json_generator_backend_returns_text_without_tools() -> None:
    response = StaticJSONGeneratorBackend({"ok": True}).generate(_request())

    assert response.provider == "static"
    assert response.model == "test-model"
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
    assert kwargs["model"] == "test-model"
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
    assert response.metadata["requested_model"] == "test-model"
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
    assert default_generator_model("anthropic") == "claude-sonnet-4-6"
    assert default_generator_model("anthropic", model_tier="haiku") == "claude-haiku-4-5-20251001"
    assert default_generator_model("anthropic", model_tier="sonnet") == "claude-sonnet-4-6"
    assert default_generator_model("anthropic", model_tier="opus") == "claude-opus-4-8"
    assert ANTHROPIC_CLAUDE_MODEL_SELECTION_POLICY["models_by_tier"] == {
        "haiku": "claude-haiku-4-5-20251001",
        "sonnet": "claude-sonnet-4-6",
        "opus": "claude-opus-4-8",
    }
    assert (
        ANTHROPIC_CLAUDE_MODEL_SELECTION_POLICY["api_aliases_by_tier"]
        == DEFAULT_CLAUDE_GENERATOR_MODEL_ALIASES_BY_TIER
        == {
            "haiku": "claude-haiku-4-5",
            "sonnet": "claude-sonnet-4-6",
            "opus": "claude-opus-4-8",
        }
    )
    assert "runtime calls" in ANTHROPIC_CLAUDE_MODEL_SELECTION_POLICY[
        "runtime_model_id_policy"
    ]
    assert ANTHROPIC_MODEL_SOURCE_CHECKED_DATE == "2026-06-11"
    assert (
        ANTHROPIC_CLAUDE_MODEL_SELECTION_POLICY["source_evidence"]
        == ANTHROPIC_MODEL_SOURCE_EVIDENCE
    )
    assert ANTHROPIC_MODEL_SOURCE_EVIDENCE["verified_latest_cost_tier_api_ids"] == {
        "haiku": "claude-haiku-4-5-20251001",
        "sonnet": "claude-sonnet-4-6",
        "opus": "claude-opus-4-8",
    }
    assert "pinned snapshots" in " ".join(
        str(claim) for claim in ANTHROPIC_MODEL_SOURCE_EVIDENCE["claims"]
    )
    assert (
        ANTHROPIC_CLAUDE_MODEL_SELECTION_POLICY[
            "models_outside_opus_sonnet_haiku_cost_tiers"
        ]
        == CLAUDE_FAMILY_MODELS_OUTSIDE_COST_TIERS
        == {
            "fable": "claude-fable-5",
            "mythos_limited_availability": "claude-mythos-5",
        }
    )
    assert "not automatic runtime tiers" in ANTHROPIC_CLAUDE_MODEL_SELECTION_POLICY[
        "outside_tier_model_policy"
    ]
    assert ANTHROPIC_CLAUDE_MODEL_SELECTION_POLICY["tier_specific_model_env_vars"] == ANTHROPIC_CLAUDE_TIER_ENV_VARS
    assert "Sonnet-tier defaults only" in ANTHROPIC_CLAUDE_MODEL_SELECTION_POLICY["global_model_override_policy"]
    assert "pinned snapshots" in ANTHROPIC_MODEL_ID_VERSIONING_POLICY
    assert "not evergreen aliases" in ANTHROPIC_MODEL_ID_VERSIONING_POLICY
    assert default_generator_model("static") == "static"

    monkeypatch.setenv("AI_STATISTICIAN_LLM_PROVIDER", "codex_exec")
    monkeypatch.setenv("AI_STATISTICIAN_LLM_MODEL", "gpt-codex-test")
    assert default_generator_provider() == "anthropic"
    assert default_generator_model("codex") == ""
    assert default_generator_model("codex_exec") == ""

    monkeypatch.setenv("AI_STATISTICIAN_LLM_PROVIDER", "anthropic")
    monkeypatch.setenv("AI_STATISTICIAN_ANTHROPIC_MODEL", "claude-test")
    assert default_generator_provider() == "anthropic"
    assert default_generator_model("anthropic") == "claude-test"
    assert default_generator_model("anthropic", model_tier="haiku") == "claude-haiku-4-5-20251001"
    assert default_generator_model("anthropic", model_tier="opus") == "claude-opus-4-8"

    monkeypatch.delenv("AI_STATISTICIAN_ANTHROPIC_MODEL", raising=False)
    monkeypatch.setenv("AI_STATISTICIAN_CLAUDE_HAIKU_MODEL", "claude-haiku-test")
    monkeypatch.setenv("AI_STATISTICIAN_CLAUDE_SONNET_MODEL", "claude-sonnet-test")
    monkeypatch.setenv("AI_STATISTICIAN_CLAUDE_OPUS_MODEL", "claude-opus-test")
    assert default_generator_model("anthropic", model_tier="haiku") == "claude-haiku-test"
    assert default_generator_model("anthropic", model_tier="sonnet") == "claude-sonnet-test"
    assert default_generator_model("anthropic", model_tier="opus") == "claude-opus-test"


def test_global_model_env_does_not_collapse_anthropic_cost_aware_tiers(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("AI_STATISTICIAN_LLM_MODEL", "claude-sonnet-4-6")
    models = {
        "haiku": default_generator_model("anthropic", model_tier="haiku"),
        "sonnet": default_generator_model("anthropic", model_tier="sonnet"),
        "opus": default_generator_model("anthropic", model_tier="opus"),
    }

    assert models == {
        "haiku": "claude-haiku-4-5-20251001",
        "sonnet": "claude-sonnet-4-6",
        "opus": "claude-opus-4-8",
    }
    assert claude_model_tier_policy_violations(models) == []


def test_claude_model_tier_policy_violations_detect_configured_model_collapse() -> None:
    models = {
        "haiku": "claude-sonnet-4-6",
        "sonnet": "claude-sonnet-4-6",
        "opus": "claude-sonnet-4-6",
    }
    violations = claude_model_tier_policy_violations(models)
    assert any("Claude haiku tier expected Claude haiku tier" in item for item in violations)
    assert any("Claude opus tier expected Claude opus tier" in item for item in violations)
    assert any("collapsed to one resolved model" in item for item in violations)

    outside_tier_violations = claude_model_tier_policy_violations(
        {
            "haiku": "claude-fable-5",
            "sonnet": "claude-sonnet-4-6",
            "opus": "claude-opus-4-8",
        }
    )
    assert any("outside-tier Claude fable model" in item for item in outside_tier_violations)


def test_claude_model_tier_helpers_detect_cross_tier_model_overrides() -> None:
    assert claude_model_tier_for_model("claude-haiku-4-5-20251001") == "haiku"
    assert claude_model_tier_for_model("claude-sonnet-4-6") == "sonnet"
    assert claude_model_tier_for_model("claude-opus-4-8") == "opus"
    assert claude_model_tier_for_model("custom-anthropic-model") == ""
    assert claude_outside_cost_tier_family_for_model("claude-fable-5") == "fable"
    assert (
        claude_outside_cost_tier_family_for_model("claude-mythos-5")
        == "mythos_limited_availability"
    )
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
        == "expected Claude sonnet tier but is configured with outside-tier Claude fable model claude-fable-5"
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
