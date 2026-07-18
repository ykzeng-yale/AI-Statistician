from __future__ import annotations

import json
import os
import signal
import threading
import time
from copy import deepcopy
from dataclasses import dataclass, field
from typing import Any, Callable, Mapping, Protocol

from .fingerprint import stable_hash


SUPPORTED_LIVE_GENERATOR_PROVIDERS = ("anthropic", "openai")
SUPPORTED_STATIC_REPLAY_GENERATOR_PROVIDERS = ("static",)
SUPPORTED_GENERATOR_PROVIDERS = (
    SUPPORTED_LIVE_GENERATOR_PROVIDERS
    + SUPPORTED_STATIC_REPLAY_GENERATOR_PROVIDERS
)
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
PROVIDER_STRUCTURED_OUTPUT_METADATA_KEY = "provider_structured_output"
MAX_LIVE_ANTHROPIC_MODEL_TIER = "sonnet"
ALLOWED_LIVE_ANTHROPIC_MODEL_TIERS = frozenset({"haiku", "sonnet"})
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
AI_STATISTICIAN_LLM_SUBSYSTEM_MODEL_TIER_POLICY = {
    "ArchitectCoordinator": "sonnet",
    "TheoryDeveloper": "sonnet",
    "FormalizerProofEngineer": "sonnet",
    "PseudoFormalBlockVerifier": "sonnet",
    "formalization_gap_planner_route_synthesis": "auto",
    "TheoryIntake": "haiku",
    "SimulationEngineer": "sonnet",
    "SimulatorEngineer": "sonnet",
    "AlgorithmEngineer": "sonnet",
    "ArchitectMetricSemanticReviewer": "sonnet",
    "ArchitectMetricRepairOwnershipRouter": "sonnet",
    "GeneratedCodeSemanticReviewer": "sonnet",
    "FormalTargetSemanticReviewer": "sonnet",
    "CriticEvaluator": "haiku",
    "bounded_route_triage": "haiku",
}
AI_STATISTICIAN_LLM_CONTEXTUAL_MODEL_TIER_POLICY = {
    "TheoryDeveloper:serious": "sonnet",
}
CLAUDE_FAMILY_MODELS_OUTSIDE_COST_TIERS = {
    "fable": DEFAULT_CLAUDE_FABLE_GENERATOR_MODEL,
    "mythos_limited_availability": DEFAULT_CLAUDE_MYTHOS_GENERATOR_MODEL,
}
CLAUDE_MODEL_TIERS = tuple(DEFAULT_CLAUDE_GENERATOR_MODELS_BY_TIER)
LIVE_CLAUDE_MODEL_TIERS = ("haiku", "sonnet")
ANTHROPIC_CLAUDE_TIER_ENV_VARS = {
    "haiku": (
        "AI_STATISTICIAN_CLAUDE_HAIKU_MODEL",
        "AI_STATISTICIAN_ANTHROPIC_HAIKU_MODEL",
    ),
    "sonnet": (
        "AI_STATISTICIAN_CLAUDE_SONNET_MODEL",
        "AI_STATISTICIAN_ANTHROPIC_SONNET_MODEL",
    ),
}
ANTHROPIC_MODEL_SOURCE_CHECKED_DATE = "2026-06-17"
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


def normalize_generator_provider_name(provider_name: object) -> str:
    return str(provider_name or "").strip().lower()


def generator_backend_provider_name(
    provider: object,
    configured_provider_name: str = "",
) -> str:
    return normalize_generator_provider_name(
        getattr(provider, "provider_name", configured_provider_name)
    )


def is_live_generator_backend(
    configured_provider_name: object,
    backend_provider_name: object | None = None,
) -> bool:
    configured = normalize_generator_provider_name(configured_provider_name)
    backend = normalize_generator_provider_name(
        configured_provider_name
        if backend_provider_name is None
        else backend_provider_name
    )
    return (
        configured in SUPPORTED_LIVE_GENERATOR_PROVIDERS
        and backend in SUPPORTED_LIVE_GENERATOR_PROVIDERS
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
    "max_live_anthropic_model_tier": MAX_LIVE_ANTHROPIC_MODEL_TIER,
    "allowed_live_anthropic_model_tiers": sorted(
        ALLOWED_LIVE_ANTHROPIC_MODEL_TIERS
    ),
    "models_by_tier": DEFAULT_CLAUDE_GENERATOR_MODELS_BY_TIER,
    "api_aliases_by_tier": DEFAULT_CLAUDE_GENERATOR_MODEL_ALIASES_BY_TIER,
    "subsystem_model_tier_policy": AI_STATISTICIAN_LLM_SUBSYSTEM_MODEL_TIER_POLICY,
    "contextual_model_tier_policy": AI_STATISTICIAN_LLM_CONTEXTUAL_MODEL_TIER_POLICY,
    "runtime_model_id_policy": (
        "AI Statistician resolves live runtime calls only for the Haiku and "
        "Sonnet tiers. The broader models_by_tier catalog and API aliases are "
        "recorded for source and historical audit only; they cannot authorize "
        "an Opus API request."
    ),
    "models_outside_opus_sonnet_haiku_cost_tiers": (
        CLAUDE_FAMILY_MODELS_OUTSIDE_COST_TIERS
    ),
    "outside_tier_model_policy": (
        "Claude Fable/Mythos family IDs are tracked as outside the "
        "Haiku/Sonnet/Opus cost-aware tier contract. They are not automatic "
        "runtime tiers for AI Statistician; live use of any tier outside "
        "Haiku/Sonnet is rejected before provider-client construction."
    ),
    "tier_specific_model_env_vars": ANTHROPIC_CLAUDE_TIER_ENV_VARS,
    "global_model_override_policy": (
        "AI_STATISTICIAN_LLM_MODEL, AI_STATISTICIAN_ANTHROPIC_MODEL, and "
        "AI_STATISTICIAN_THEORY_MODEL are treated as Sonnet-tier defaults only. "
        "They must not collapse live Haiku/Sonnet cost-aware routing; use the "
        "live tier-specific Claude env vars to override helper tiers."
    ),
    "model_id_versioning": ANTHROPIC_MODEL_ID_VERSIONING_POLICY,
    "cost_split": {
        "sonnet": [
            "ArchitectCoordinator",
            "TheoryDeveloper",
            "SimulationEngineer",
            "AlgorithmEngineer",
            "FormalizerProofEngineer",
            "PseudoFormalBlockVerifier",
            "formalization_gap_planner_route_synthesis",
        ],
        "haiku": [
            "theory_intake",
            "CriticEvaluator",
            "bounded_route_triage",
        ],
    },
}


def llm_subsystem_expected_model_tier(subsystem: str) -> str:
    """Return the expected Claude cost tier for a named LLM subsystem."""

    return AI_STATISTICIAN_LLM_SUBSYSTEM_MODEL_TIER_POLICY.get(
        str(subsystem or "").strip(),
        "",
    )


def default_generator_provider(env: Mapping[str, str] | None = None) -> str:
    """Default live generator provider for AI Statistician LLM use.

    Anthropic is the default live provider. OpenAI remains overrideable for live
    calls; static replay must be selected explicitly by the command or subsystem
    that owns the replay fixture.
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
    if provider in SUPPORTED_STATIC_REPLAY_GENERATOR_PROVIDERS:
        return [
            (
                "AI_STATISTICIAN_LLM_PROVIDER is set to static replay provider "
                f"{raw_provider!r}; static is supported only as an explicit "
                "fixture/replay backend and is not accepted as the default live "
                f"provider. The runtime falls back to {DEFAULT_LIVE_GENERATOR_PROVIDER!r}."
            )
        ]
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
            f"{raw_provider!r}; supported external live generator-only providers are "
            + ", ".join(SUPPORTED_LIVE_GENERATOR_PROVIDERS)
            + "; static is available only through explicit replay provider flags"
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

    env = env or os.environ
    provider = (provider_name or default_generator_provider(env)).strip().lower()
    requested = str(requested_model or "").strip()
    if requested:
        if provider == "anthropic":
            violation = live_anthropic_model_ceiling_violation(
                requested,
                requested_model_tier=model_tier,
            )
            if violation:
                raise ValueError(violation)
        return requested
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
        if tier not in ALLOWED_LIVE_ANTHROPIC_MODEL_TIERS:
            raise ValueError(
                f"live Anthropic requests are capped at "
                f"{MAX_LIVE_ANTHROPIC_MODEL_TIER}; requested model_tier="
                f"{tier or 'unknown'}"
            )
        if tier == "haiku":
            tier_default = DEFAULT_CLAUDE_HAIKU_GENERATOR_MODEL
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
            model = (
                env.get(tier_env_keys[0])
                or env.get(tier_env_keys[1])
                or env.get("AI_STATISTICIAN_ANTHROPIC_MODEL")
                or global_theory_model
                or global_model
                or tier_default
            ).strip()
        else:
            model = str(tier_model or "").strip()
        violation = live_anthropic_model_ceiling_violation(
            model,
            requested_model_tier=tier,
        )
        if violation:
            raise ValueError(violation)
        return model
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
    overrides and the live Claude Haiku/Sonnet split are evaluated when a
    request is actually built, not when a module is imported. Opus remains in
    the source catalog for historical audit only and is rejected for live use.
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


def live_anthropic_model_ceiling_violation(
    model: str,
    *,
    requested_model_tier: str = "",
) -> str:
    """Reject live Claude requests above the project Sonnet ceiling."""

    requested_tier = str(requested_model_tier or "").strip().lower()
    actual_tier = claude_model_tier_for_model(model)
    if requested_tier and requested_tier not in ALLOWED_LIVE_ANTHROPIC_MODEL_TIERS:
        return (
            f"live Anthropic requests are capped at {MAX_LIVE_ANTHROPIC_MODEL_TIER}; "
            f"requested model_tier={requested_tier or 'unknown'}"
        )
    if actual_tier not in ALLOWED_LIVE_ANTHROPIC_MODEL_TIERS:
        return (
            f"live Anthropic requests are capped at {MAX_LIVE_ANTHROPIC_MODEL_TIER}; "
            f"model={model or 'unknown'} resolves to tier={actual_tier or 'unknown'}"
        )
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
        for tier in LIVE_CLAUDE_MODEL_TIERS
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
    for tier in LIVE_CLAUDE_MODEL_TIERS:
        current_model = DEFAULT_CLAUDE_GENERATOR_MODELS_BY_TIER[tier]
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


def resolved_claude_models_by_tier(
    env: Mapping[str, str] | None = None,
) -> dict[str, str]:
    """Return the concrete Anthropic model ID resolved for each Claude tier."""

    return {
        tier: resolve_generator_model(
            provider_name="anthropic",
            requested_model="",
            model_tier=tier,
            env=env,
        )
        for tier in LIVE_CLAUDE_MODEL_TIERS
    }


def claude_tier_routing_contract(
    env: Mapping[str, str] | None = None,
) -> dict[str, object]:
    """Machine-readable contract for live Claude Haiku/Sonnet routing.

    The wider model catalog remains available as source evidence, but active
    resolution is capped at Sonnet. This metadata function does not create a
    provider client or make a live API request.
    """

    env = env or os.environ
    provider = default_generator_provider(env)
    models_by_tier = resolved_claude_models_by_tier(env)
    tier_violations = claude_model_tier_policy_violations(models_by_tier)
    freshness_warnings = claude_model_freshness_warnings(models_by_tier)
    provider_warnings = generator_provider_override_warnings(env)
    global_override_keys = tuple(
        key
        for key in (
            "AI_STATISTICIAN_LLM_MODEL",
            "AI_STATISTICIAN_ANTHROPIC_MODEL",
            "AI_STATISTICIAN_THEORY_MODEL",
        )
        if str(env.get(key, "") or "").strip()
    )
    tier_override_keys = tuple(
        key
        for keys in ANTHROPIC_CLAUDE_TIER_ENV_VARS.values()
        for key in keys
        if str(env.get(key, "") or "").strip()
    )
    return {
        "contract_name": "anthropic_claude_tier_routing_contract",
        "source_checked_date": ANTHROPIC_MODEL_SOURCE_CHECKED_DATE,
        "source_evidence": ANTHROPIC_MODEL_SOURCE_EVIDENCE,
        "default_live_generator_provider": DEFAULT_LIVE_GENERATOR_PROVIDER,
        "effective_live_generator_provider": provider,
        "supported_live_generator_providers": tuple(SUPPORTED_LIVE_GENERATOR_PROVIDERS),
        "supported_generator_providers": tuple(SUPPORTED_GENERATOR_PROVIDERS),
        "static_replay_generator_providers": tuple(
            SUPPORTED_STATIC_REPLAY_GENERATOR_PROVIDERS
        ),
        "prohibited_agent_generator_providers": tuple(
            PROHIBITED_AGENT_GENERATOR_PROVIDERS
        ),
        "claude_model_selection": ANTHROPIC_CLAUDE_MODEL_SELECTION_POLICY,
        "latest_claude_models_by_tier": dict(DEFAULT_CLAUDE_GENERATOR_MODELS_BY_TIER),
        "latest_claude_api_aliases_by_tier": dict(
            DEFAULT_CLAUDE_GENERATOR_MODEL_ALIASES_BY_TIER
        ),
        "latest_claude_family_models_outside_cost_tiers": dict(
            CLAUDE_FAMILY_MODELS_OUTSIDE_COST_TIERS
        ),
        "resolved_claude_models_by_tier": models_by_tier,
        "allowed_live_anthropic_model_tiers": tuple(
            LIVE_CLAUDE_MODEL_TIERS
        ),
        "resolved_claude_model_tier_policy_status": (
            "OK" if not tier_violations else "POLICY_VIOLATION"
        ),
        "resolved_claude_model_tier_policy_violations": tuple(tier_violations),
        "resolved_claude_model_freshness_status": (
            "CURRENT" if not freshness_warnings else "NON_CURRENT"
        ),
        "resolved_claude_model_freshness_warnings": tuple(freshness_warnings),
        "environment_override_status": "OK" if not provider_warnings else "WARN",
        "provider_override_warnings": tuple(provider_warnings),
        "global_model_override_keys_present": global_override_keys,
        "tier_specific_model_override_keys_present": tier_override_keys,
        "global_model_override_policy": ANTHROPIC_CLAUDE_MODEL_SELECTION_POLICY[
            "global_model_override_policy"
        ],
        "tier_specific_model_env_vars": ANTHROPIC_CLAUDE_TIER_ENV_VARS,
        "subsystem_model_tier_policy": AI_STATISTICIAN_LLM_SUBSYSTEM_MODEL_TIER_POLICY,
        "contextual_model_tier_policy": (
            AI_STATISTICIAN_LLM_CONTEXTUAL_MODEL_TIER_POLICY
        ),
        "all_ok": (
            DEFAULT_LIVE_GENERATOR_PROVIDER == "anthropic"
            and not set(PROHIBITED_AGENT_GENERATOR_PROVIDERS).intersection(
                SUPPORTED_GENERATOR_PROVIDERS
            )
            and not set(SUPPORTED_STATIC_REPLAY_GENERATOR_PROVIDERS).intersection(
                SUPPORTED_LIVE_GENERATOR_PROVIDERS
            )
            and not tier_violations
        ),
    }


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


_ANTHROPIC_NEGOTIABLE_OPTIONAL_PARAMETERS = frozenset({"temperature"})


def _prune_unreferenced_json_schema_defs(
    schema: Mapping[str, Any],
) -> dict[str, Any]:
    """Keep only local ``$defs`` reachable from the response root."""

    definitions = schema.get("$defs", {})
    if not isinstance(definitions, Mapping) or not definitions:
        return deepcopy(dict(schema))

    def local_refs(value: Any, *, include_defs: bool) -> set[str]:
        refs: set[str] = set()
        if isinstance(value, Mapping):
            ref = value.get("$ref")
            if isinstance(ref, str) and ref.startswith("#/$defs/"):
                refs.add(ref.rsplit("/", 1)[-1])
            for key, child in value.items():
                if key == "$defs" and not include_defs:
                    continue
                refs.update(local_refs(child, include_defs=include_defs))
        elif isinstance(value, (list, tuple)):
            for child in value:
                refs.update(local_refs(child, include_defs=include_defs))
        return refs

    root = {key: value for key, value in schema.items() if key != "$defs"}
    pending = list(local_refs(root, include_defs=False))
    reachable: set[str] = set()
    while pending:
        name = pending.pop()
        if name in reachable or name not in definitions:
            continue
        reachable.add(name)
        pending.extend(
            local_refs(definitions[name], include_defs=True) - reachable
        )

    pruned = deepcopy(root)
    if reachable:
        pruned["$defs"] = {
            str(name): deepcopy(definitions[name])
            for name in definitions
            if str(name) in reachable
        }
    return pruned


def _anthropic_create_with_capability_fallback(
    messages_api: Any,
    *,
    request_kwargs: dict[str, Any],
    omitted_unsupported_parameters: list[str],
) -> Any:
    """Retry once per rejected optional parameter using provider feedback."""

    while True:
        try:
            return messages_api.create(**request_kwargs)
        except Exception as exc:
            parameter = _anthropic_rejected_optional_parameter(exc)
            if not parameter or parameter not in request_kwargs:
                raise
            request_kwargs.pop(parameter, None)
            if parameter not in omitted_unsupported_parameters:
                omitted_unsupported_parameters.append(parameter)


def _anthropic_rejected_optional_parameter(exc: Exception) -> str:
    error_text = str(exc).lower()
    rejection_markers = (
        "deprecated for this model",
        "not supported for this model",
        "unsupported parameter",
    )
    if not any(marker in error_text for marker in rejection_markers):
        return ""
    for parameter in _ANTHROPIC_NEGOTIABLE_OPTIONAL_PARAMETERS:
        if (
            f"`{parameter}`" in error_text
            or f"'{parameter}'" in error_text
            or f'"{parameter}"' in error_text
        ):
            return parameter
    return ""


class AnthropicGeneratorBackend:
    """Anthropic Messages API backend with no tool exposure."""

    provider_name = "anthropic"

    def __init__(self, *, api_key: str | None = None, timeout_s: float | None = None) -> None:
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        self.timeout_s = timeout_s
        self._capability_lock = threading.Lock()
        self._unsupported_optional_parameters_by_model: dict[str, set[str]] = {}

    def generate(self, request: GeneratorRequest) -> GeneratorResponse:
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY is not set")
        ceiling_violation = live_anthropic_model_ceiling_violation(
            request.model,
            requested_model_tier=str(
                request.metadata.get("model_tier", "") or ""
            ),
        )
        if ceiling_violation:
            raise ValueError(ceiling_violation)
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
        structured_output_requested = bool(
            request.schema is not None
            and request.metadata.get(PROVIDER_STRUCTURED_OUTPUT_METADATA_KEY)
            is True
        )
        structured_output_schema: dict[str, Any] = {}
        if structured_output_requested:
            transform_schema = getattr(anthropic, "transform_schema", None)
            if not callable(transform_schema):
                raise ValueError(
                    "installed anthropic SDK does not expose transform_schema "
                    "required for provider structured output"
                )
            try:
                structured_output_schema = transform_schema(
                    _prune_unreferenced_json_schema_defs(request.schema)
                )
            except Exception as exc:
                raise ValueError(
                    "failed to transform GeneratorRequest.schema for Anthropic "
                    f"structured output: {type(exc).__name__}: {exc}"
                ) from exc
        json_mode_hint = request.schema is not None and not structured_output_requested
        user_prompt = request.user_prompt
        if json_mode_hint:
            user_prompt = (
                request.user_prompt
                + "\n\nReturn exactly one valid JSON object. Do not wrap it in Markdown. "
                "Do not include commentary outside JSON."
            )
        messages = [{"role": "user", "content": user_prompt}]
        request_kwargs: dict[str, Any] = {
            "model": request.model,
            "max_tokens": request.max_tokens,
            "temperature": request.temperature,
            "system": request.system_prompt,
            "messages": messages,
        }
        if structured_output_requested:
            request_kwargs["output_config"] = {
                "format": {
                    "type": "json_schema",
                    "schema": structured_output_schema,
                }
            }
        with self._capability_lock:
            cached_unsupported_parameters = set(
                self._unsupported_optional_parameters_by_model.get(
                    request.model,
                    set(),
                )
            )
        for parameter in cached_unsupported_parameters:
            request_kwargs.pop(parameter, None)
        omitted_unsupported_parameters = sorted(cached_unsupported_parameters)
        response, retry_count = _call_with_generator_retries(
            lambda: _call_with_wall_clock_timeout(
                lambda: _anthropic_create_with_capability_fallback(
                    client.messages,
                    request_kwargs=request_kwargs,
                    omitted_unsupported_parameters=(
                        omitted_unsupported_parameters
                    ),
                ),
                timeout_s=timeout_s,
                provider_name=self.provider_name,
                model=request.model,
            )
        )
        with self._capability_lock:
            self._unsupported_optional_parameters_by_model.setdefault(
                request.model,
                set(),
            ).update(omitted_unsupported_parameters)
        capability_fallback_count = len(
            set(omitted_unsupported_parameters) - cached_unsupported_parameters
        )
        text = _anthropic_text(response)
        response_model = _response_model(response, fallback=request.model)
        response_ceiling_violation = live_anthropic_model_ceiling_violation(
            response_model,
            requested_model_tier=str(
                request.metadata.get("model_tier", "") or ""
            ),
        )
        if response_ceiling_violation:
            raise ValueError(
                "Anthropic returned a model outside the configured live ceiling: "
                + response_ceiling_violation
            )
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
                "provider_structured_output_requested": (
                    structured_output_requested
                ),
                "provider_structured_output_applied": bool(
                    structured_output_requested
                    and "output_config" in request_kwargs
                ),
                "provider_structured_output_schema_fingerprint": (
                    stable_hash(structured_output_schema)
                    if structured_output_schema
                    else ""
                ),
                "timeout_seconds": timeout_s,
                "retry_count": retry_count,
                "provider_capability_fallback_count": capability_fallback_count,
                "omitted_unsupported_request_parameters": list(
                    omitted_unsupported_parameters
                ),
                "cached_unsupported_request_parameters": sorted(
                    cached_unsupported_parameters
                ),
                "requested_model": request.model,
                "provider_reported_model": response_model,
                **_provider_response_diagnostics(response),
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
                **_provider_response_diagnostics(response),
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
    previous_delay, previous_interval = old_timer
    effective_timeout = timeout
    if previous_delay > 0:
        effective_timeout = min(timeout, previous_delay)
    started = time.monotonic()

    def _handle_timeout(_signum: int, _frame: Any) -> None:
        raise LiveGeneratorTimeoutError(
            f"{provider_name} generator request for {model} exceeded "
            f"wall-clock timeout {effective_timeout:g}s"
        )

    signal.signal(signal.SIGALRM, _handle_timeout)
    signal.setitimer(signal.ITIMER_REAL, effective_timeout)
    try:
        return call()
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, old_handler)
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


def _provider_response_diagnostics(response: Any) -> dict[str, object]:
    metadata: dict[str, object] = {}
    for attr in ("stop_reason", "stop_sequence", "status"):
        value = getattr(response, attr, None)
        if value not in (None, "", [], {}):
            metadata[f"provider_{attr}"] = str(value)
    incomplete = getattr(response, "incomplete_details", None)
    if incomplete not in (None, "", [], {}):
        metadata["provider_incomplete_details"] = _compact_provider_value(incomplete)
    usage = getattr(response, "usage", None)
    if usage not in (None, "", [], {}):
        metadata["provider_usage"] = _compact_provider_value(usage)
    return metadata


def _compact_provider_value(value: Any) -> object:
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if isinstance(value, Mapping):
        return {
            str(key): _compact_provider_value(child)
            for key, child in list(value.items())[:12]
            if child not in (None, "", [], {})
        }
    if hasattr(value, "model_dump"):
        try:
            dumped = value.model_dump()
            if isinstance(dumped, Mapping):
                return _compact_provider_value(dumped)
        except Exception:
            pass
    attrs: dict[str, object] = {}
    for attr in (
        "input_tokens",
        "output_tokens",
        "cache_creation_input_tokens",
        "cache_read_input_tokens",
        "total_tokens",
    ):
        child = getattr(value, attr, None)
        if child not in (None, "", [], {}):
            attrs[attr] = child
    if attrs:
        return attrs
    return str(value)[:400]


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
