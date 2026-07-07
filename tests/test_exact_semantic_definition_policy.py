from __future__ import annotations

from pathlib import Path

import ai_statistician.exact_semantic_definition_policy as policy_module
from ai_statistician.exact_semantic_definition_policy import (
    compact_exact_semantic_placeholder_key,
    exact_semantic_definition_candidate_risks,
    exact_semantic_definition_contract,
    exact_semantic_definition_draft_definition,
    exact_semantic_definition_draft_semantic_risk,
    exact_semantic_definition_import_policy_blocker,
    exact_semantic_definition_policy_pack_ids,
    exact_semantic_definition_placeholder_policy,
    exact_semantic_definition_source_lookup_aliases,
    exact_semantic_definition_source_lookup_terms,
)


def test_split_conformal_placeholder_policy_is_data_pack_owned() -> None:
    module_source = Path(policy_module.__file__).read_text(encoding="utf-8")
    policy_pack_source = (
        Path(policy_module.__file__).with_name("policies")
        / "source_theorem_exact_semantic_definition_placeholders.split_conformal.json"
    ).read_text(encoding="utf-8")
    pyproject_source = (
        Path(policy_module.__file__).resolve().parents[1] / "pyproject.toml"
    ).read_text(encoding="utf-8")

    assert "_SPLIT_CONFORMAL_POLICIES" not in module_source
    assert "_split_conformal_registry" not in module_source
    assert "split_conformal_coverage.covered" not in module_source
    assert "split_conformal_coverage.covered" in policy_pack_source
    assert 'ai_statistician = ["policies/*.json"]' in pyproject_source


def test_split_conformal_placeholder_policy_resolves_required_binders() -> None:
    assert "split_conformal_exact_semantic_definition_placeholder_policies_v1" in (
        exact_semantic_definition_policy_pack_ids()
    )

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


def test_placeholder_policy_owns_draft_definitions_and_search_aliases() -> None:
    exchangeable = exact_semantic_definition_placeholder_policy("Exchangeable")
    assert exchangeable.policy_id == "split_conformal_coverage.exchangeable"
    assert exchangeable.required_anchor_names == ("P", "s")

    exchangeable_draft = exact_semantic_definition_draft_definition("Exchangeable")
    assert "Equiv.Perm" in exchangeable_draft
    assert "MeasureTheory.Measure.map" in exchangeable_draft
    assert "joint-law exchangeability" in exact_semantic_definition_draft_semantic_risk(
        "Exchangeable"
    )
    assert exact_semantic_definition_source_lookup_terms("Exchangeable") == (
        "exchangeability",
        "exchangeab",
    )

    order_stat_draft = exact_semantic_definition_draft_definition("orderStat")
    assert "mergeSort" in order_stat_draft
    assert "getD k" in order_stat_draft
    assert exact_semantic_definition_source_lookup_terms("orderStat") == (
        "orderStatistic",
        "order statistic",
        "quantile",
    )
    assert "alpha" in exact_semantic_definition_source_lookup_terms("\u03b1_total")
    assert "alpha" in exact_semantic_definition_source_lookup_aliases("\u03b1_total")
    assert "alphatotal" in exact_semantic_definition_source_lookup_aliases(
        "\u03b1_total"
    )
    order_stat_contract = exact_semantic_definition_contract("orderStat")
    assert "conformal quantile" in order_stat_contract["semantic_intent"]
    assert "rank index matches" in order_stat_contract["required_properties"][1]

    generic_contract = exact_semantic_definition_contract("newDomainObject")
    assert "newDomainObject" in generic_contract["semantic_intent"]
    assert "do not assume the target theorem" in generic_contract["forbidden_shortcuts"]


def test_placeholder_policy_owns_candidate_semantic_risk_rules() -> None:
    pairwise_exchangeability = (
        "def Exchangeable {Ω : Type _} (P : MeasureTheory.Measure Ω)"
        " (s : Nat -> Ω -> ℝ) : Prop := P.real {ω | s 0 ω <= s 1 ω} = 1"
    )
    exchangeability_risks = exact_semantic_definition_candidate_risks(
        "Exchangeable",
        definition_block=pairwise_exchangeability,
    )
    assert any("pairwise" in risk for risk in exchangeability_risks)
    assert any("permutation" in risk for risk in exchangeability_risks)

    finite_max_order_stat = (
        "def orderStat (scores : Finset Nat) : Nat := scores.max' (by simp)"
    )
    order_stat_risks = exact_semantic_definition_candidate_risks(
        "orderStat",
        definition_block=finite_max_order_stat,
    )
    assert any("finite maximum" in risk for risk in order_stat_risks)
    assert any("rank parameter k" in risk for risk in order_stat_risks)

    reviewed_order_stat = (
        "def orderStat (scores : List Nat) (k : Nat) : Nat := scores.getD k 0"
    )
    assert (
        exact_semantic_definition_candidate_risks(
            "orderStat",
            definition_block=reviewed_order_stat,
        )
        == []
    )


def test_policy_pack_string_false_case_sensitive_is_case_insensitive() -> None:
    rule = policy_module._risk_rule_from_mapping(
        {
            "message": "semantic_definition_risk: missing permutation",
            "absent_all": ["permutation"],
            "case_sensitive": "false",
        }
    )

    assert rule.case_sensitive is False
    assert (
        policy_module._candidate_risk_rule_matches(
            rule,
            definition_block="def Exchangeable : Prop := PermutationInvariantLaw",
        )
        is False
    )
    assert (
        policy_module._candidate_risk_rule_matches(
            rule,
            definition_block="def Exchangeable : Prop := pairwiseScoreOrderOnly",
        )
        is True
    )
