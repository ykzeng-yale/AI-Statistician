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
    semantic_import_incompatible_terms: tuple[str, ...] = ()
    semantic_import_incompatible_status: str = (
        "SEMANTIC_MISMATCH_NOT_EXACT_SEMANTIC_DEFINITION"
    )
    semantic_import_incompatible_reason: str = ""
    semantic_import_required_signal_terms: tuple[str, ...] = ()
    semantic_import_allowed_declaration_names: tuple[str, ...] = ()
    semantic_import_allowed_declaration_prefixes: tuple[str, ...] = ()
    semantic_import_missing_required_signal_status: str = (
        "SEMANTIC_REVIEW_REQUIRED_EXACT_SEMANTIC_SIGNAL_NOT_EXPOSED"
    )
    semantic_import_missing_required_signal_reason: str = ""


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
        semantic_import_incompatible_terms=(
            "samplemean",
            "trimmedmean",
            "winsorizedmean",
            "lstatistic",
            "interquantilerange",
            "samplerange",
            "conditionalcdf",
            "cdf",
            "projection",
            "variance",
        ),
        semantic_import_incompatible_status=(
            "SEMANTIC_MISMATCH_NOT_EXACT_ORDER_STATISTIC"
        ),
        semantic_import_incompatible_reason=(
            "declaration name matches order-statistic literature but defines an "
            "aggregate/range/CDF display, not the rank-k conformal orderStat "
            "placeholder"
        ),
        semantic_import_required_signal_terms=("k", "rank"),
        semantic_import_allowed_declaration_names=("orderstat", "orderstatistic"),
        semantic_import_allowed_declaration_prefixes=("orderstatreview",),
        semantic_import_missing_required_signal_status=(
            "SEMANTIC_REVIEW_REQUIRED_ORDER_STATISTIC_RANK_NOT_EXPOSED"
        ),
        semantic_import_missing_required_signal_reason=(
            "candidate declaration does not visibly expose the requested rank "
            "parameter for orderStat"
        ),
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


def exact_semantic_definition_import_policy_blocker(
    placeholder_symbol: str,
    *,
    snippet: str = "",
    declaration_name: str = "",
    require_required_signal: bool = False,
) -> dict[str, str]:
    policy = exact_semantic_definition_placeholder_policy(placeholder_symbol)
    snippet_text = str(snippet or "")
    declaration_text = str(declaration_name or "")
    snippet_key = compact_exact_semantic_placeholder_key(snippet_text)
    declaration_key = compact_exact_semantic_placeholder_key(declaration_text)
    haystack = f"{declaration_key} {snippet_key}"
    incompatible_terms = tuple(
        compact_exact_semantic_placeholder_key(term)
        for term in policy.semantic_import_incompatible_terms
        if compact_exact_semantic_placeholder_key(term)
    )
    if incompatible_terms and any(term in haystack for term in incompatible_terms):
        return {
            "source_semantic_review_status": (
                policy.semantic_import_incompatible_status
            ),
            "source_semantic_review_reason": (
                policy.semantic_import_incompatible_reason
                or "candidate declaration is incompatible with the placeholder policy"
            ),
        }
    if require_required_signal and not _semantic_import_required_signal_present(
        policy,
        snippet=snippet_text,
        declaration_name=declaration_text,
    ):
        return {
            "source_semantic_review_status": (
                policy.semantic_import_missing_required_signal_status
            ),
            "source_semantic_review_reason": (
                policy.semantic_import_missing_required_signal_reason
                or "candidate declaration does not expose a required semantic signal"
            ),
        }
    return {}


def _semantic_import_required_signal_present(
    policy: ExactSemanticDefinitionPlaceholderPolicy,
    *,
    snippet: str,
    declaration_name: str,
) -> bool:
    required_terms = tuple(
        compact_exact_semantic_placeholder_key(term)
        for term in policy.semantic_import_required_signal_terms
        if compact_exact_semantic_placeholder_key(term)
    )
    if not required_terms:
        return True
    declaration_key = compact_exact_semantic_placeholder_key(declaration_name)
    allowed_names = {
        compact_exact_semantic_placeholder_key(value)
        for value in policy.semantic_import_allowed_declaration_names
        if compact_exact_semantic_placeholder_key(value)
    }
    if declaration_key in allowed_names:
        return True
    allowed_prefixes = tuple(
        compact_exact_semantic_placeholder_key(value)
        for value in policy.semantic_import_allowed_declaration_prefixes
        if compact_exact_semantic_placeholder_key(value)
    )
    if allowed_prefixes and any(
        declaration_key.startswith(prefix) for prefix in allowed_prefixes
    ):
        return True
    snippet_key = compact_exact_semantic_placeholder_key(snippet)
    if "k" in required_terms and (" k " in f" {snippet} " or "(k :" in snippet):
        return True
    return any(term != "k" and term in snippet_key for term in required_terms)
