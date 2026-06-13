from __future__ import annotations

import json
import os
import signal
import threading
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Mapping, Protocol


SUPPORTED_LIVE_GENERATOR_PROVIDERS = ("anthropic", "openai", "static")
PROHIBITED_AGENT_GENERATOR_PROVIDERS = (
    "codex",
    "codex_exec",
    "claude_code",
    "cursor",
    "gemini_cli",
)
DEFAULT_LIVE_GENERATOR_PROVIDER = "anthropic"
DEFAULT_CLAUDE_OPUS_GENERATOR_MODEL = "claude-opus-4-8"
DEFAULT_CLAUDE_HAIKU_GENERATOR_MODEL = "claude-haiku-4-5-20251001"
DEFAULT_CLAUDE_SONNET_GENERATOR_MODEL = "claude-sonnet-4-6"
DEFAULT_CLAUDE_FABLE_GENERATOR_MODEL = "claude-fable-5"
DEFAULT_CLAUDE_MYTHOS_GENERATOR_MODEL = "claude-mythos-5"
DEFAULT_ANTHROPIC_GENERATOR_MODEL = DEFAULT_CLAUDE_SONNET_GENERATOR_MODEL
DEFAULT_STATIC_GENERATOR_MODEL = "static"
DEFAULT_LIVE_GENERATOR_TIMEOUT_SECONDS = 120.0
DEFAULT_CLAUDE_GENERATOR_MODELS_BY_TIER = {
    "haiku": DEFAULT_CLAUDE_HAIKU_GENERATOR_MODEL,
    "sonnet": DEFAULT_CLAUDE_SONNET_GENERATOR_MODEL,
    "opus": DEFAULT_CLAUDE_OPUS_GENERATOR_MODEL,
}
DEFAULT_CLAUDE_GENERATOR_MODEL_ALIASES_BY_TIER = {
    "haiku": "claude-haiku-4-5",
    "sonnet": DEFAULT_CLAUDE_SONNET_GENERATOR_MODEL,
    "opus": DEFAULT_CLAUDE_OPUS_GENERATOR_MODEL,
}
CLAUDE_FAMILY_MODELS_OUTSIDE_COST_TIERS = {
    "fable": DEFAULT_CLAUDE_FABLE_GENERATOR_MODEL,
    "mythos_limited_availability": DEFAULT_CLAUDE_MYTHOS_GENERATOR_MODEL,
}
CLAUDE_MODEL_TIERS = tuple(DEFAULT_CLAUDE_GENERATOR_MODELS_BY_TIER)
ANTHROPIC_CLAUDE_TIER_ENV_VARS = {
    "haiku": (
        "AI_STATISTICIAN_CLAUDE_HAIKU_MODEL",
        "AI_STATISTICIAN_ANTHROPIC_HAIKU_MODEL",
    ),
    "sonnet": (
        "AI_STATISTICIAN_CLAUDE_SONNET_MODEL",
        "AI_STATISTICIAN_ANTHROPIC_SONNET_MODEL",
    ),
    "opus": (
        "AI_STATISTICIAN_CLAUDE_OPUS_MODEL",
        "AI_STATISTICIAN_ANTHROPIC_OPUS_MODEL",
    ),
}
ANTHROPIC_MODEL_SOURCE_CHECKED_DATE = "2026-06-12"
ANTHROPIC_MODELS_OVERVIEW_URL = (
    "https://platform.claude.com/docs/en/about-claude/models/overview"
)
ANTHROPIC_MODEL_IDS_AND_VERSIONING_URL = (
    "https://platform.claude.com/docs/en/about-claude/models/model-ids-and-versions"
)
ANTHROPIC_MODEL_ID_VERSIONING_POLICY = (
    "Claude model IDs are pinned snapshots. Starting with Claude 4.6, dateless "
    "IDs such as claude-sonnet-4-6 are canonical release IDs, not evergreen "
    "aliases; newer releases require explicit constant updates."
)
ANTHROPIC_MODEL_SOURCE_EVIDENCE = {
    "source_checked_date": ANTHROPIC_MODEL_SOURCE_CHECKED_DATE,
    "source": "Anthropic Claude API docs Models overview and Model IDs and versioning",
    "models_overview_url": ANTHROPIC_MODELS_OVERVIEW_URL,
    "model_ids_and_versioning_url": ANTHROPIC_MODEL_IDS_AND_VERSIONING_URL,
    "verified_latest_cost_tier_api_ids": dict(DEFAULT_CLAUDE_GENERATOR_MODELS_BY_TIER),
    "verified_api_aliases_by_tier": dict(DEFAULT_CLAUDE_GENERATOR_MODEL_ALIASES_BY_TIER),
    "verified_outside_cost_tier_models": dict(CLAUDE_FAMILY_MODELS_OUTSIDE_COST_TIERS),
    "claims": [
        (
            "The latest Opus/Sonnet/Haiku comparison lists Claude API IDs "
            "claude-opus-4-8, claude-sonnet-4-6, and "
            "claude-haiku-4-5-20251001."
        ),
        (
            "Claude Fable 5 and Claude Mythos 5 are tracked separately from "
            "the Opus/Sonnet/Haiku cost-aware tier contract."
        ),
        (
            "Claude 4.6+ dateless model IDs are pinned snapshots, not "
            "evergreen aliases."
        ),
    ],
}
ANTHROPIC_CLAUDE_MODEL_SELECTION_POLICY = {
    "source_checked_date": ANTHROPIC_MODEL_SOURCE_CHECKED_DATE,
    "source_evidence": ANTHROPIC_MODEL_SOURCE_EVIDENCE,
    "models_overview_url": ANTHROPIC_MODELS_OVERVIEW_URL,
    "model_ids_and_versioning_url": ANTHROPIC_MODEL_IDS_AND_VERSIONING_URL,
    "default_provider": DEFAULT_LIVE_GENERATOR_PROVIDER,
    "default_model_tier": "sonnet",
    "models_by_tier": DEFAULT_CLAUDE_GENERATOR_MODELS_BY_TIER,
    "api_aliases_by_tier": DEFAULT_CLAUDE_GENERATOR_MODEL_ALIASES_BY_TIER,
    "runtime_model_id_policy": (
        "AI Statistician resolves runtime calls to the Claude API IDs in "
        "models_by_tier. API aliases are recorded for operator reference only "
        "and are not used to collapse pinned runtime model IDs."
    ),
    "models_outside_opus_sonnet_haiku_cost_tiers": (
        CLAUDE_FAMILY_MODELS_OUTSIDE_COST_TIERS
    ),
    "outside_tier_model_policy": (
        "Claude Fable/Mythos family IDs are tracked as outside the "
        "Haiku/Sonnet/Opus cost-aware tier contract. They are not automatic "
        "runtime tiers for AI Statistician; using them under a Haiku, Sonnet, "
        "or Opus tier request is treated as a routing mismatch."
    ),
    "tier_specific_model_env_vars": ANTHROPIC_CLAUDE_TIER_ENV_VARS,
    "global_model_override_policy": (
        "AI_STATISTICIAN_LLM_MODEL, AI_STATISTICIAN_ANTHROPIC_MODEL, and "
        "AI_STATISTICIAN_THEORY_MODEL are treated as Sonnet-tier defaults only. "
        "They must not collapse Haiku/Sonnet/Opus cost-aware routing; use "
        "tier-specific Claude env vars to override helper tiers."
    ),
    "model_id_versioning": ANTHROPIC_MODEL_ID_VERSIONING_POLICY,
    "cost_split": {
        "sonnet": [
            "ArchitectCoordinator",
            "TheoryDeveloper",
            "FormalizerProofEngineer",
            "formalization_gap_planner_route_synthesis",
        ],
        "haiku": [
            "theory_intake",
            "SimulationEngineer",
            "AlgorithmEngineer",
            "CriticEvaluator",
            "bounded_route_triage",
        ],
        "opus": ["operator_explicit_only"],
    },
}


def default_generator_provider(env: Mapping[str, str] | None = None) -> str:
    """Default live generator provider for AI Statistician LLM use.

    Anthropic is the default live provider. Other providers remain overrideable
    so the same prompts/contracts can run against OpenAI or static replay.
    """

    env = env or os.environ
    provider = (env.get("AI_STATISTICIAN_LLM_PROVIDER") or DEFAULT_LIVE_GENERATOR_PROVIDER).strip().lower()
    if provider in SUPPORTED_LIVE_GENERATOR_PROVIDERS:
        return provider
    return DEFAULT_LIVE_GENERATOR_PROVIDER


def generator_provider_override_warnings(
    env: Mapping[str, str] | None = None,
) -> list[str]:
    """Return operator warnings for unsupported generator provider overrides."""

    env = env or os.environ
    raw_provider = str(env.get("AI_STATISTICIAN_LLM_PROVIDER", "") or "").strip()
    if not raw_provider:
        return []
    provider = raw_provider.lower()
    if provider in SUPPORTED_LIVE_GENERATOR_PROVIDERS:
        return []
    if provider in PROHIBITED_AGENT_GENERATOR_PROVIDERS:
        return [
            (
                "AI_STATISTICIAN_LLM_PROVIDER is set to agent-style provider "
                f"{raw_provider!r}; Codex/Claude Code/Cursor/Gemini CLI-style "
                "agents are not accepted as pure LLM generator backends. The "
                f"runtime falls back to {DEFAULT_LIVE_GENERATOR_PROVIDER!r}."
            )
        ]
    return [
        (
            "AI_STATISTICIAN_LLM_PROVIDER is set to unsupported provider "
            f"{raw_provider!r}; supported generator-only providers are "
            + ", ".join(SUPPORTED_LIVE_GENERATOR_PROVIDERS)
            + f". The runtime falls back to {DEFAULT_LIVE_GENERATOR_PROVIDER!r}."
        )
    ]


def default_generator_model(
    provider_name: str = "",
    requested_model: str = "",
    env: Mapping[str, str] | None = None,
    *,
    model_tier: str = "sonnet",
) -> str:
    """Return the model for a provider.

    Anthropic uses a cost-aware tier split: Sonnet for theorem/math/proof-route
    planning and Haiku for cheaper structured helper tasks.
    """

    requested = str(requested_model or "").strip()
    if requested:
        return requested
    env = env or os.environ
    provider = (provider_name or default_generator_provider(env)).strip().lower()
    global_model = (
        (env.get("AI_STATISTICIAN_LLM_MODEL") or "").strip()
        if _global_model_override_applies(env, provider)
        else ""
    )
    global_theory_model = (
        (env.get("AI_STATISTICIAN_THEORY_MODEL") or "").strip()
        if _global_model_override_applies(env, provider)
        else ""
    )
    if provider == "anthropic":
        tier = (model_tier or "sonnet").strip().lower()
        if tier == "haiku":
            tier_default = DEFAULT_CLAUDE_HAIKU_GENERATOR_MODEL
        elif tier == "opus":
            tier_default = DEFAULT_CLAUDE_OPUS_GENERATOR_MODEL
        else:
            tier = "sonnet"
            tier_default = DEFAULT_CLAUDE_SONNET_GENERATOR_MODEL
        tier_env_keys = ANTHROPIC_CLAUDE_TIER_ENV_VARS[tier]
        tier_model = (
            env.get(tier_env_keys[0])
            or env.get(tier_env_keys[1])
            or tier_default
        )
        if tier == "sonnet":
            return (
                env.get(tier_env_keys[0])
                or env.get(tier_env_keys[1])
                or env.get("AI_STATISTICIAN_ANTHROPIC_MODEL")
                or global_theory_model
                or global_model
                or tier_default
            ).strip()
        return str(tier_model or "").strip()
    if provider == "openai":
        return (
            env.get("AI_STATISTICIAN_OPENAI_MODEL")
            or global_model
            or env.get("OPENAI_MODEL")
            or ""
        ).strip()
    if provider == "static":
        return DEFAULT_STATIC_GENERATOR_MODEL
    return ""


def _global_model_override_applies(env: Mapping[str, str], provider: str) -> bool:
    raw_provider = str(env.get("AI_STATISTICIAN_LLM_PROVIDER", "") or "").strip().lower()
    if not raw_provider:
        return True
    return raw_provider == str(provider or "").strip().lower()


def resolve_generator_model(
    *,
    provider_name: str,
    requested_model: str = "",
    model_tier: str = "sonnet",
    env: Mapping[str, str] | None = None,
) -> str:
    """Resolve a generator model at call time from provider and tier policy.

    LLM worker configs may leave ``requested_model`` empty so environment
    overrides and the Claude Haiku/Sonnet/Opus split are evaluated when a
    request is actually built, not when a module is imported.
    """

    return default_generator_model(
        provider_name,
        requested_model,
        env=env,
        model_tier=model_tier,
    )


def claude_model_tier_for_model(model: str) -> str:
    """Infer the Claude tier family from a model id."""

    key = str(model or "").strip().lower()
    for tier in CLAUDE_MODEL_TIERS:
        if tier in key:
            return tier
    return ""


def claude_outside_cost_tier_family_for_model(model: str) -> str:
    """Return the Claude family name for tracked outside-tier model ids."""

    key = str(model or "").strip().lower()
    if not key:
        return ""
    for family, model_id in CLAUDE_FAMILY_MODELS_OUTSIDE_COST_TIERS.items():
        if key == str(model_id).lower():
            return family
        if family.endswith("_limited_availability"):
            family_prefix = family.removesuffix("_limited_availability")
        else:
            family_prefix = family
        if key.startswith(f"claude-{family_prefix}-"):
            return family
    return ""


def claude_model_tier_mismatch(
    model: str,
    expected_model_tier: str,
    *,
    subject: str = "",
) -> str:
    """Return a policy violation when an Anthropic model id crosses tiers."""

    expected = str(expected_model_tier or "").strip().lower()
    actual = claude_model_tier_for_model(model)
    outside_family = claude_outside_cost_tier_family_for_model(model)
    if not expected or not actual or expected == actual:
        if expected and outside_family:
            prefix = f"{subject} " if subject else ""
            return (
                f"{prefix}expected Claude {expected} tier but is configured "
                f"with outside-tier Claude {outside_family} model {model}"
            )
        return ""
    prefix = f"{subject} " if subject else ""
    return f"{prefix}expected Claude {expected} tier but is configured with {model}"


def claude_model_tier_policy_violations(
    models_by_tier: Mapping[str, str],
) -> list[str]:
    """Return diagnostics when resolved Claude tiers defeat cost-aware routing."""

    violations: list[str] = []
    resolved_by_tier = {
        tier: str(models_by_tier.get(tier, "") or "").strip()
        for tier in CLAUDE_MODEL_TIERS
    }
    for tier, model in resolved_by_tier.items():
        mismatch = claude_model_tier_mismatch(
            model,
            tier,
            subject=f"Claude {tier} tier",
        )
        if mismatch:
            violations.append(mismatch)

    resolved_models = {
        model for model in resolved_by_tier.values() if model
    }
    if len(resolved_models) == 1 and all(resolved_by_tier.values()):
        only_model = next(iter(resolved_models))
        violations.append(
            "Claude cost-aware tier routing collapsed to one resolved model "
            f"({only_model}); use tier-specific model env vars or unset the "
            "global model override for Haiku/Sonnet switching."
        )
    return sorted(set(violations))


def claude_model_freshness_warnings(
    models_by_tier: Mapping[str, str],
) -> list[str]:
    """Warn when a Claude tier resolves to a non-current same-tier model ID."""

    warnings: list[str] = []
    for tier, current_model in DEFAULT_CLAUDE_GENERATOR_MODELS_BY_TIER.items():
        model = str(models_by_tier.get(tier, "") or "").strip()
        if not model or model == current_model:
            continue
        if claude_model_tier_for_model(model) != tier:
            continue
        warnings.append(
            f"Claude {tier} tier resolves to {model}; current source-checked "
            f"API ID is {current_model} as of {ANTHROPIC_MODEL_SOURCE_CHECKED_DATE}"
        )
    return sorted(set(warnings))


@dataclass(frozen=True)
class GeneratorRequest:
    """One LLM generation request.

    The backend is intentionally not an agent interface: it receives prompts and
    an optional JSON schema, then returns text. Planning, tool use, file writes,
    shell execution, and environment iteration belong to AgentRuntime.
    """

    system_prompt: str
    user_prompt: str
    model: str
    max_tokens: int = 4096
    temperature: float = 0.0
    schema: Mapping[str, Any] | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class GeneratorResponse:
    text: str
    provider: str
    model: str
    raw: Any | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)


class GeneratorBackend(Protocol):
    """A restricted LLM backend used as a generator, not as an acting agent."""

    provider_name: str

    def generate(self, request: GeneratorRequest) -> GeneratorResponse:
        ...


class LiveGeneratorTimeoutError(TimeoutError):
    """Raised when a live generator exceeds the runtime wall-clock budget."""


class StaticJSONGeneratorBackend:
    """Offline generator for deterministic tests and reviewed replay."""

    provider_name = "static"

    def __init__(self, response: str | Mapping[str, Any]) -> None:
        self.response = (
            json.dumps(response, indent=2, default=str)
            if isinstance(response, Mapping)
            else str(response)
        )

    def generate(self, request: GeneratorRequest) -> GeneratorResponse:
        return GeneratorResponse(
            text=self.response,
            provider=self.provider_name,
            model=request.model,
            metadata={"generator_only": True, "tools_available": False},
        )


class AnthropicGeneratorBackend:
    """Anthropic Messages API backend with no tool exposure."""

    provider_name = "anthropic"

    def __init__(self, *, api_key: str | None = None, timeout_s: float | None = None) -> None:
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        self.timeout_s = timeout_s

    def generate(self, request: GeneratorRequest) -> GeneratorResponse:
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY is not set")
        try:
            import anthropic
        except Exception as exc:  # pragma: no cover - import depends on local env
            raise ValueError(f"failed to import anthropic package: {exc!r}") from exc
        timeout_s = _live_generator_timeout_seconds(self.timeout_s)
        client = anthropic.Anthropic(
            api_key=self.api_key,
            timeout=timeout_s,
            max_retries=0,
        )
        json_mode_hint = request.schema is not None
        user_prompt = request.user_prompt
        if json_mode_hint:
            user_prompt = (
                request.user_prompt
                + "\n\nReturn exactly one valid JSON object. Do not wrap it in Markdown. "
                "Do not include commentary outside JSON."
            )
        messages = [{"role": "user", "content": user_prompt}]
        response, retry_count = _call_with_generator_retries(
            lambda: _call_with_wall_clock_timeout(
                lambda: client.messages.create(
                    model=request.model,
                    max_tokens=request.max_tokens,
                    temperature=request.temperature,
                    system=request.system_prompt,
                    messages=messages,
                ),
                timeout_s=timeout_s,
                provider_name=self.provider_name,
                model=request.model,
            )
        )
        text = _anthropic_text(response)
        response_model = _response_model(response, fallback=request.model)
        return GeneratorResponse(
            text=text,
            provider=self.provider_name,
            model=response_model,
            raw=response,
            metadata={
                "generator_only": True,
                "tools_available": False,
                "schema_supplied": request.schema is not None,
                "json_prompt_hint_used": json_mode_hint,
                "timeout_seconds": timeout_s,
                "retry_count": retry_count,
                "requested_model": request.model,
                "provider_reported_model": response_model,
                **_claude_generator_model_tier_metadata(
                    request_model=request.model,
                    response_model=response_model,
                    request_metadata=request.metadata,
                ),
            },
        )


class OpenAIResponsesGeneratorBackend:
    """OpenAI Responses API backend used without tools."""

    provider_name = "openai"

    def __init__(self, *, api_key: str | None = None, timeout_s: float | None = None) -> None:
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self.timeout_s = timeout_s

    def generate(self, request: GeneratorRequest) -> GeneratorResponse:
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY is not set")
        try:
            from openai import OpenAI
        except Exception as exc:  # pragma: no cover - import depends on local env
            raise ValueError(f"failed to import openai package: {exc!r}") from exc
        timeout_s = _live_generator_timeout_seconds(self.timeout_s)
        try:
            client = OpenAI(api_key=self.api_key, timeout=timeout_s)
        except TypeError:  # pragma: no cover - compatibility with older/fake clients
            client = OpenAI(api_key=self.api_key)
        kwargs: dict[str, Any] = {
            "model": request.model,
            "input": [
                {"role": "system", "content": request.system_prompt},
                {"role": "user", "content": request.user_prompt},
            ],
            "max_output_tokens": request.max_tokens,
            "temperature": request.temperature,
        }
        if request.schema is not None:
            kwargs["text"] = {
                "format": {
                    "type": "json_schema",
                    "name": "ai_statistician_generator_response",
                    "schema": dict(request.schema),
                    "strict": False,
                }
            }
        response, retry_count = _call_with_generator_retries(
            lambda: _call_with_wall_clock_timeout(
                lambda: client.responses.create(**kwargs),
                timeout_s=timeout_s,
                provider_name=self.provider_name,
                model=request.model,
            )
        )
        response_model = _response_model(response, fallback=request.model)
        return GeneratorResponse(
            text=_openai_response_text(response),
            provider=self.provider_name,
            model=response_model,
            raw=response,
            metadata={
                "generator_only": True,
                "tools_available": False,
                "schema_supplied": request.schema is not None,
                "retry_count": retry_count,
                "timeout_seconds": timeout_s,
                "requested_model": request.model,
                "provider_reported_model": response_model,
            },
        )


def _call_with_generator_retries(call: Callable[[], Any]) -> tuple[Any, int]:
    max_retries = max(0, _env_int("AI_STATISTICIAN_LLM_MAX_RETRIES", default=4))
    backoff = max(0.0, _env_float("AI_STATISTICIAN_LLM_RETRY_BACKOFF_SECONDS", default=1.0))
    retry_timeouts = _env_bool("AI_STATISTICIAN_LLM_RETRY_TIMEOUTS", default=False)
    last_exc: Exception | None = None
    for attempt in range(max_retries + 1):
        try:
            return call(), attempt
        except Exception as exc:
            last_exc = exc
            if _is_timeout_generator_exception(exc) and not retry_timeouts:
                raise
            if attempt >= max_retries:
                raise
            if not _is_retryable_generator_exception(exc):
                raise
            if backoff:
                time.sleep(backoff * (attempt + 1))
    raise last_exc or RuntimeError("generator call failed without an exception")


def _is_retryable_generator_exception(exc: Exception) -> bool:
    name = type(exc).__name__.lower()
    module = type(exc).__module__.lower()
    text = str(exc).lower()
    retry_markers = (
        "apiconnectionerror",
        "api_connection_error",
        "ratelimiterror",
        "rate_limit_error",
        "timeout",
        "connection",
        "temporarily unavailable",
        "server error",
    )
    haystack = f"{module}.{name} {text}"
    return any(marker in haystack for marker in retry_markers)


def _is_timeout_generator_exception(exc: Exception) -> bool:
    name = type(exc).__name__.lower()
    text = str(exc).lower()
    return "timeout" in name or "timed out" in text or "timeout" in text


def _call_with_wall_clock_timeout(
    call: Callable[[], Any],
    *,
    timeout_s: float,
    provider_name: str,
    model: str,
) -> Any:
    """Bound a synchronous provider call by wall-clock time when possible.

    SDK request timeouts can behave as socket/read timeouts rather than a hard
    total runtime cap. The AgentRuntime needs a stronger guard so one LLM
    subsystem cannot block the whole research loop for many minutes.
    """

    timeout = _live_generator_timeout_seconds(timeout_s)
    if (
        threading.current_thread() is not threading.main_thread()
        or not hasattr(signal, "setitimer")
        or not hasattr(signal, "SIGALRM")
    ):
        return call()

    old_handler = signal.getsignal(signal.SIGALRM)
    old_timer = signal.getitimer(signal.ITIMER_REAL)
    started = time.monotonic()

    def _handle_timeout(_signum: int, _frame: Any) -> None:
        raise LiveGeneratorTimeoutError(
            f"{provider_name} generator request for {model} exceeded "
            f"wall-clock timeout {timeout:g}s"
        )

    signal.signal(signal.SIGALRM, _handle_timeout)
    signal.setitimer(signal.ITIMER_REAL, timeout)
    try:
        return call()
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, old_handler)
        previous_delay, previous_interval = old_timer
        if previous_delay > 0:
            remaining = max(0.0, previous_delay - (time.monotonic() - started))
            if remaining > 0:
                signal.setitimer(signal.ITIMER_REAL, remaining, previous_interval)


def _live_generator_timeout_seconds(value: float | None = None) -> float:
    if value is not None:
        return max(1.0, float(value))
    return max(
        1.0,
        _env_float(
            "AI_STATISTICIAN_LLM_TIMEOUT_SECONDS",
            default=DEFAULT_LIVE_GENERATOR_TIMEOUT_SECONDS,
        ),
    )


def _env_bool(key: str, *, default: bool) -> bool:
    raw = os.environ.get(key)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _env_int(key: str, *, default: int) -> int:
    try:
        return int(os.environ.get(key, str(default)))
    except ValueError:
        return default


def _env_float(key: str, *, default: float) -> float:
    try:
        return float(os.environ.get(key, str(default)))
    except ValueError:
        return default


def _anthropic_text(response: Any) -> str:
    parts: list[str] = []
    for item in getattr(response, "content", []) or []:
        text = getattr(item, "text", None)
        if text is not None:
            parts.append(str(text))
    if parts:
        return "".join(parts)
    return str(response)


def _response_model(response: Any, *, fallback: str) -> str:
    model = getattr(response, "model", None)
    if model:
        return str(model)
    return str(fallback)


def _claude_generator_model_tier_metadata(
    *,
    request_model: str,
    response_model: str,
    request_metadata: Mapping[str, Any],
) -> dict[str, object]:
    request_tier = _request_model_tier_from_metadata(request_metadata)
    provider_tier = claude_model_tier_for_model(response_model)
    request_model_tier = claude_model_tier_for_model(request_model)
    metadata: dict[str, object] = {
        "request_model_tier": request_tier,
        "requested_model_tier": str(
            request_metadata.get("requested_model_tier", "") or request_tier
        ),
        "request_model_family_tier": request_model_tier,
        "provider_reported_model_tier": provider_tier,
        "provider_reported_model_tier_mismatch": "",
        "requested_model_tier_mismatch": "",
    }
    if request_tier:
        metadata["provider_reported_model_tier_mismatch"] = claude_model_tier_mismatch(
            response_model,
            request_tier,
            subject="provider reported model",
        )
        metadata["requested_model_tier_mismatch"] = claude_model_tier_mismatch(
            request_model,
            request_tier,
            subject="requested model",
        )
    return metadata


def _request_model_tier_from_metadata(metadata: Mapping[str, Any]) -> str:
    for key in ("effective_model_tier", "model_tier", "requested_model_tier"):
        tier = str(metadata.get(key, "") or "").strip().lower()
        if tier in CLAUDE_MODEL_TIERS:
            return tier
    return ""


def _openai_response_text(response: Any) -> str:
    output_text = getattr(response, "output_text", None)
    if output_text:
        return str(output_text)
    parts: list[str] = []
    for item in getattr(response, "output", []) or []:
        for content in getattr(item, "content", []) or []:
            text = getattr(content, "text", None)
            if text is not None:
                parts.append(str(text))
    if parts:
        return "".join(parts)
    if hasattr(response, "model_dump_json"):
        return response.model_dump_json()
    return str(response)
