from __future__ import annotations

from ai_statistician.exact_semantic_definition_policy import (
    compact_exact_semantic_placeholder_key,
    exact_semantic_definition_import_policy_blocker,
    exact_semantic_definition_placeholder_policy,
)


def test_split_conformal_placeholder_policy_resolves_required_binders() -> None:
    covered = exact_semantic_definition_placeholder_policy("covered")
    rank = exact_semantic_definition_placeholder_policy("rank")
    bad_ranks = exact_semantic_definition_placeholder_policy("BadRanks")
    alpha_total = exact_semantic_definition_placeholder_policy("alpha_total")

    assert covered.policy_id == "split_conformal_coverage.covered"
    assert covered.required_anchor_names == ("s", "q_hat", "C", "hC")
    assert "hC" in covered.semantic_goal

    assert rank.policy_id == "split_conformal_coverage.rank"
    assert rank.required_anchor_names == ("n2", "s", "q_hat", "hq")
    assert "order-statistic threshold equation hq" in rank.semantic_goal

    order_stat = exact_semantic_definition_placeholder_policy("orderStat")
    assert order_stat.policy_id == (
        "split_conformal_coverage.order_statistic_threshold"
    )
    assert order_stat.required_anchor_names == ("n2", "s", "q_hat", "hq")
    assert "duplicate score multiplicities" in order_stat.semantic_goal
    assert "samplemean" in order_stat.semantic_import_incompatible_terms
    assert order_stat.semantic_import_required_signal_terms == ("k", "rank")

    assert bad_ranks.policy_id == "split_conformal_coverage.BadRanks"
    assert bad_ranks.required_anchor_names == (
        "n2",
        "alpha",
        "halpha",
        "s",
        "q_hat",
        "hq",
    )
    assert bad_ranks.required_adapter_object_names == ("rank",)

    assert alpha_total.policy_id == "split_conformal_coverage.alpha_total"
    assert alpha_total.required_anchor_names == ("n2", "alpha", "halpha")
    assert alpha_total.required_adapter_object_names == ("BadRanks",)


def test_placeholder_policy_keeps_alpha_aliases_and_generic_fallback() -> None:
    assert compact_exact_semantic_placeholder_key("alpha_total") == "alphatotal"
    assert (
        exact_semantic_definition_placeholder_policy("\u03b1_total").policy_id
        == "split_conformal_coverage.alpha_total"
    )
    assert (
        exact_semantic_definition_placeholder_policy("\u03b1").policy_id
        == "split_conformal_coverage.alpha"
    )

    generic = exact_semantic_definition_placeholder_policy("newDomainObject")
    assert generic.policy_id == "generic_exact_semantic_definition_placeholder"
    assert generic.policy_scope == "generic"
    assert generic.placeholder_key == "newdomainobject"
    assert generic.required_anchor_names == ()
    assert generic.required_adapter_object_names == ()


def test_placeholder_policy_reviews_semantic_import_candidates() -> None:
    blocker = exact_semantic_definition_import_policy_blocker(
        "orderStat",
        declaration_name="vaart1998_orderStatisticSampleMean",
        snippet="def vaart1998_orderStatisticSampleMean (n i : Nat) := n + i",
        require_required_signal=True,
    )

    assert blocker["source_semantic_review_status"] == (
        "SEMANTIC_MISMATCH_NOT_EXACT_ORDER_STATISTIC"
    )
    assert "aggregate/range/CDF" in blocker["source_semantic_review_reason"]

    missing_rank = exact_semantic_definition_import_policy_blocker(
        "orderStat",
        declaration_name="candidateOrderStatistic",
        snippet="def candidateOrderStatistic (scores : Nat) := scores",
        require_required_signal=True,
    )

    assert missing_rank["source_semantic_review_status"] == (
        "SEMANTIC_REVIEW_REQUIRED_ORDER_STATISTIC_RANK_NOT_EXPOSED"
    )

    accepted = exact_semantic_definition_import_policy_blocker(
        "orderStat",
        declaration_name="conformalQuantile",
        snippet="def conformalQuantile (scores : Nat) (k : Nat) := scores + k",
        require_required_signal=True,
    )

    assert accepted == {}
