from __future__ import annotations

import json
import os
import re
from dataclasses import asdict, dataclass
from typing import Any, Protocol

from .model_backend import (
    AnthropicGeneratorBackend,
    GeneratorBackend,
    GeneratorRequest,
    PROHIBITED_AGENT_GENERATOR_PROVIDERS,
    resolve_generator_model,
)


SUPPORTED_DGP_FAMILIES = ("normal", "bernoulli", "constant")
SUPPORTED_ESTIMATOR_FAMILIES = ("sample_mean", "sample_proportion", "constant_estimator")
PROHIBITED_THEORY_PROPOSER_PROVIDERS = PROHIBITED_AGENT_GENERATOR_PROVIDERS


@dataclass(frozen=True)
class TheoryProposal:
    dgp_family: str
    estimator_family: str
    true_params: dict[str, float]
    tags: tuple[str, ...] = ()
    rationale: str = ""
    confidence: float = 0.0
    source: str = "unknown"

    def validated(self) -> "TheoryProposal":
        if self.dgp_family not in SUPPORTED_DGP_FAMILIES:
            raise ValueError(
                f"LLM proposed unsupported dgp_family {self.dgp_family!r}; "
                f"supported: {', '.join(SUPPORTED_DGP_FAMILIES)}"
            )
        if self.estimator_family not in SUPPORTED_ESTIMATOR_FAMILIES:
            raise ValueError(
                f"LLM proposed unsupported estimator_family {self.estimator_family!r}; "
                f"supported: {', '.join(SUPPORTED_ESTIMATOR_FAMILIES)}"
            )
        return self


class TheoryProposer(Protocol):
    def propose(self, raw_question: dict[str, Any]) -> TheoryProposal:
        ...


class MockTheoryProposer:
    """Deterministic test double for the optional LLM theory proposer."""

    def __init__(self, proposal: TheoryProposal):
        self.proposal = proposal

    def propose(self, raw_question: dict[str, Any]) -> TheoryProposal:
        return self.proposal


class GeneratorTheoryProposer:
    """Generator-backed proposer for mapping questions to supported families.

    This is an LLM generator use case, not an acting agent. It never expands the
    trusted estimator/proof surface; it can only propose one of the supported
    family IDs, and `question_from_json` validates the proposal before
    simulation or formal verification runs.
    """

    def __init__(
        self,
        *,
        provider: GeneratorBackend,
        model: str = "",
        model_tier: str = "haiku",
        provider_name: str = "",
        max_tokens: int = 700,
    ) -> None:
        self.provider = provider
        self.model = model
        self.model_tier = model_tier
        self.provider_name = provider_name
        self.max_tokens = max_tokens

    def propose(self, raw_question: dict[str, Any]) -> TheoryProposal:
        provider_name = _resolved_provider_name(self.provider_name, self.provider)
        request_model = resolve_generator_model(
            provider_name=provider_name,
            requested_model=self.model,
            model_tier=self.model_tier,
        )
        response = self.provider.generate(
            GeneratorRequest(
                system_prompt=SYSTEM_PROMPT,
                user_prompt="Classify this statistical question:\n" + json.dumps(raw_question, indent=2),
                model=request_model,
                max_tokens=self.max_tokens,
                temperature=0,
                schema=THEORY_PROPOSAL_JSON_SCHEMA,
                metadata={
                    "subsystem": "TheoryIntake",
                    "agent": "GeneratorTheoryProposer",
                    "provider_name": provider_name,
                    "model_tier": self.model_tier,
                    "resolved_model": request_model,
                },
            )
        )
        payload = _extract_json(response.text)
        return proposal_from_payload(
            payload,
            source=f"{provider_name}:{response.model or request_model or 'default'}",
        ).validated()


class AnthropicTheoryProposer(GeneratorTheoryProposer):
    """Compatibility wrapper for the old Anthropic-only theory intake path."""

    def __init__(
        self,
        *,
        model: str = "",
        api_key: str | None = None,
        max_tokens: int = 700,
    ) -> None:
        super().__init__(
            provider=AnthropicGeneratorBackend(api_key=api_key or os.environ.get("ANTHROPIC_API_KEY")),
            max_tokens=max_tokens,
            model=model,
            model_tier="haiku",
            provider_name="anthropic",
        )


SYSTEM_PROMPT = """\
You are a conservative theory-intake agent for a production AI statistician.

Your only job is to map a statistical question to one of the SUPPORTED
registered families. Do not invent a new estimator family. Do not claim full
formal guarantees.

Supported dgp_family:
- normal
- bernoulli
- constant

Supported estimator_family:
- sample_mean
- sample_proportion
- constant_estimator

Return ONLY compact JSON:
{
  "dgp_family": "...",
  "estimator_family": "...",
  "true_params": {"...": number},
  "tags": ["..."],
  "confidence": 0.0,
  "rationale": "short reason"
}

If the question is outside the supported set, return the closest unsupported
label in dgp_family or estimator_family. The caller will reject it.
"""


THEORY_PROPOSAL_JSON_SCHEMA: dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "additionalProperties": True,
    "required": ["dgp_family", "estimator_family", "true_params"],
    "properties": {
        "dgp_family": {"type": "string"},
        "estimator_family": {"type": "string"},
        "true_params": {"type": "object"},
        "tags": {"type": "array", "items": {"type": "string"}},
        "confidence": {"type": "number"},
        "rationale": {"type": "string"},
    },
}


def proposal_from_payload(payload: dict[str, Any], *, source: str) -> TheoryProposal:
    params = payload.get("true_params") or {}
    if not isinstance(params, dict):
        raise ValueError("proposal true_params must be an object")
    tags = payload.get("tags") or ()
    if isinstance(tags, str):
        tags = (tags,)
    return TheoryProposal(
        dgp_family=str(payload.get("dgp_family") or ""),
        estimator_family=str(payload.get("estimator_family") or ""),
        true_params={str(k): float(v) for k, v in params.items()},
        tags=tuple(str(tag) for tag in tags),
        rationale=str(payload.get("rationale") or ""),
        confidence=float(payload.get("confidence") or 0.0),
        source=source,
    )


def _extract_json(text: str) -> dict[str, Any]:
    stripped = text.strip()
    if stripped.startswith("{") and stripped.endswith("}"):
        return json.loads(stripped)
    match = re.search(r"\{.*\}", stripped, flags=re.DOTALL)
    if not match:
        raise ValueError(f"LLM response did not contain JSON: {text[:200]!r}")
    return json.loads(match.group(0))


def _resolved_provider_name(
    configured_provider_name: str,
    provider: GeneratorBackend,
) -> str:
    provider_name = str(
        configured_provider_name or getattr(provider, "provider_name", "") or ""
    ).strip().lower()
    if not provider_name:
        raise ValueError(
            "GeneratorTheoryProposer requires an explicit provider_name or a "
            "backend.provider_name before resolving a model tier"
        )
    if provider_name in PROHIBITED_THEORY_PROPOSER_PROVIDERS:
        raise ValueError(
            "Agent-style CLI providers are not accepted as pure LLM theory "
            "proposer providers"
        )
    return provider_name


def proposal_to_json(proposal: TheoryProposal) -> dict[str, Any]:
    return asdict(proposal)
