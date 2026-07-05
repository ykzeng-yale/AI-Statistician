from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Mapping


@dataclass(frozen=True)
class ExactSemanticDefinitionPlaceholderPolicy:
    policy_id: str
    policy_scope: str
    placeholder_key: str
    semantic_goal: str
    required_anchor_names: tuple[str, ...] = ()
    required_adapter_object_names: tuple[str, ...] = ()


def compact_exact_semantic_placeholder_key(value: str) -> str:
    return "".join(ch.lower() for ch in str(value or "") if ch.isalnum())


_GENERIC_POLICY = ExactSemanticDefinitionPlaceholderPolicy(
    policy_id="generic_exact_semantic_definition_placeholder",
    policy_scope="generic",
    placeholder_key="",
    semantic_goal=(
        "Define the exact semantic replacement for the placeholder from the "
        "listed source theorem binders and semantic constraints."
    ),
)


_SPLIT_CONFORMAL_POLICIES: tuple[
    ExactSemanticDefinitionPlaceholderPolicy,
    ...,
] = (
    ExactSemanticDefinitionPlaceholderPolicy(
        policy_id="split_conformal_coverage.covered",
        policy_scope="split_conformal_coverage",
        placeholder_key="covered",
        semantic_goal=(
            "Define the source coverage event/object from the exact source theorem "
            "coverage binder hC and threshold q_hat, matching the held-out score "
            "event {\u03c9 | s (Fin.last n2) \u03c9 \u2264 q_hat \u03c9}."
        ),
        required_anchor_names=("s", "q_hat", "C", "hC"),
    ),
    ExactSemanticDefinitionPlaceholderPolicy(
        policy_id="split_conformal_coverage.rank",
        policy_scope="split_conformal_coverage",
        placeholder_key="rank",
        semantic_goal=(
            "Define the rank object from the exact score process s and the "
            "order-statistic threshold equation hq; it must support good-rank "
            "containment and bad-rank probability premises."
        ),
        required_anchor_names=("n2", "s", "q_hat", "hq"),
    ),
    ExactSemanticDefinitionPlaceholderPolicy(
        policy_id="split_conformal_coverage.order_statistic_threshold",
        policy_scope="split_conformal_coverage",
        placeholder_key="orderstat",
        semantic_goal=(
            "Define the finite-sample conformal order-statistic threshold from "
            "the exact score process s and the order-statistic threshold equation "
            "hq. The definition must preserve the requested rank, duplicate score "
            "multiplicities, and the reviewed tie policy instead of collapsing "
            "scores through a set/image shortcut."
        ),
        required_anchor_names=("n2", "s", "q_hat", "hq"),
    ),
    ExactSemanticDefinitionPlaceholderPolicy(
        policy_id="split_conformal_coverage.BadRanks",
        policy_scope="split_conformal_coverage",
        placeholder_key="badranks",
        semantic_goal=(
            "Define the finite bad-rank set from n2, alpha, halpha, and hq so it "
            "matches the ranks that violate conformal coverage containment."
        ),
        required_anchor_names=("n2", "alpha", "halpha", "s", "q_hat", "hq"),
        required_adapter_object_names=("rank",),
    ),
    ExactSemanticDefinitionPlaceholderPolicy(
        policy_id="split_conformal_coverage.alpha",
        policy_scope="split_conformal_coverage",
        placeholder_key="alpha",
        semantic_goal=(
            "Define the rank-indexed probability budget \u03b1 from the exact source "
            "miscoverage level alpha and rank-uniformity/exchangeability anchor hexch."
        ),
        required_anchor_names=("P", "n2", "alpha", "s", "hexch"),
    ),
    ExactSemanticDefinitionPlaceholderPolicy(
        policy_id="split_conformal_coverage.alpha_total",
        policy_scope="split_conformal_coverage",
        placeholder_key="alphatotal",
        semantic_goal=(
            "Define the total bad-rank budget \u03b1_total from alpha and BadRanks, "
            "with the intended downstream finite-sum bound."
        ),
        required_anchor_names=("n2", "alpha", "halpha"),
        required_adapter_object_names=("BadRanks",),
    ),
)


def _split_conformal_registry() -> dict[str, ExactSemanticDefinitionPlaceholderPolicy]:
    registry: dict[str, ExactSemanticDefinitionPlaceholderPolicy] = {}
    for policy in _SPLIT_CONFORMAL_POLICIES:
        registry[policy.placeholder_key] = policy
    registry["\u03b1"] = registry["alpha"]
    registry["\u03b1total"] = registry["alphatotal"]
    return registry


EXACT_SEMANTIC_DEFINITION_PLACEHOLDER_POLICIES: Mapping[
    str,
    ExactSemanticDefinitionPlaceholderPolicy,
] = _split_conformal_registry()


def exact_semantic_definition_placeholder_policy(
    placeholder_symbol: str,
) -> ExactSemanticDefinitionPlaceholderPolicy:
    key = compact_exact_semantic_placeholder_key(placeholder_symbol)
    policy = EXACT_SEMANTIC_DEFINITION_PLACEHOLDER_POLICIES.get(key)
    if policy is not None:
        return policy
    return replace(_GENERIC_POLICY, placeholder_key=key)
