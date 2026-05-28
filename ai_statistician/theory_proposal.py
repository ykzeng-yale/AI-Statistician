from __future__ import annotations

import json
import os
import re
from dataclasses import asdict, dataclass
from typing import Any, Protocol


SUPPORTED_DGP_FAMILIES = ("normal", "bernoulli", "constant")
SUPPORTED_ESTIMATOR_FAMILIES = ("sample_mean", "sample_proportion", "constant_estimator")


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


class AnthropicTheoryProposer:
    """Haiku-backed proposer for mapping natural-language questions to supported families.

    This agent never expands the trusted estimator/proof surface. It can only
    propose one of the supported family IDs, and `question_from_json` validates
    the proposal before simulation or formal verification runs.
    """

    def __init__(
        self,
        *,
        model: str = "claude-haiku-4-5",
        api_key: str | None = None,
        max_tokens: int = 700,
    ) -> None:
        self.model = model
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        self.max_tokens = max_tokens

    def propose(self, raw_question: dict[str, Any]) -> TheoryProposal:
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY is not set")
        try:
            import anthropic
        except Exception as exc:
            raise ValueError(f"failed to import anthropic package: {exc!r}") from exc

        client = anthropic.Anthropic(api_key=self.api_key)
        response = client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            temperature=0,
            system=SYSTEM_PROMPT,
            messages=[
                {
                    "role": "user",
                    "content": "Classify this statistical question:\n"
                    + json.dumps(raw_question, indent=2),
                }
            ],
        )
        text = response.content[0].text
        payload = _extract_json(text)
        return proposal_from_payload(payload, source=f"anthropic:{self.model}").validated()


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


def proposal_to_json(proposal: TheoryProposal) -> dict[str, Any]:
    return asdict(proposal)

