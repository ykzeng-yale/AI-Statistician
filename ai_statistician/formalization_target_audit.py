from __future__ import annotations

import json
import re
from collections import defaultdict
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .proof_bank import get_obligation
from .research_gap_audit import audit_research_gap_backlog


@dataclass(frozen=True)
class FormalizationTargetRow:
    primitive: str
    priority_score: int
    priority_band: str
    n_gaps: int
    problem_classes: tuple[str, ...]
    theorem_goals: tuple[str, ...]
    gap_ids: tuple[str, ...]
    candidate_declarations: tuple[str, ...]
    supporting_proof_obligations: tuple[str, ...]
    bridge_candidate_obligations: tuple[str, ...]
    bridge_candidate_score: int
    proof_bank_bridge_available: bool
    bridge_readiness: str
    suggested_next_step: str
    ok: bool
    errors: tuple[str, ...] = ()


def audit_formalization_targets(run_dir: Path, out_dir: Path | None = None) -> dict[str, object]:
    """Rank missing formal primitives into a theorem-development queue.

    `research-gap-audit` proves that gaps are honest and grounded. This audit
    turns the same rows into a prioritized work queue: which primitive should be
    formalized next, which theorem goals it unlocks, and what local
    Mathlib/StatInference declarations look reusable.
    """

    backlog = audit_research_gap_backlog(run_dir)
    rows = _target_rows(backlog)
    payload = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "run_dir": str(run_dir),
        "n_targets": len(rows),
        "n_ok": sum(1 for row in rows if row.ok),
        "n_with_proof_bank_bridge": sum(1 for row in rows if row.proof_bank_bridge_available),
        "n_with_ranked_bridge_candidate": sum(1 for row in rows if row.bridge_candidate_obligations),
        "by_bridge_readiness": _count_by_bridge_readiness(rows),
        "all_ok": bool(backlog.get("all_ok")) and bool(rows) and all(row.ok for row in rows),
        "top_targets": [asdict(row) for row in rows[:10]],
        "rows": [asdict(row) for row in rows],
        "source_gap_backlog": {
            "n_gaps": backlog.get("n_gaps"),
            "n_ok": backlog.get("n_ok"),
            "all_ok": backlog.get("all_ok"),
        },
    }
    if out_dir is not None:
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "formalization_target_manifest.json").write_text(
            json.dumps(payload, indent=2, default=str),
            encoding="utf-8",
        )
        (out_dir / "formalization_targets.md").write_text(_markdown_report(payload), encoding="utf-8")
    return payload


def _target_rows(backlog: dict[str, object]) -> list[FormalizationTargetRow]:
    grouped: dict[str, dict[str, Any]] = defaultdict(
        lambda: {
            "gap_ids": set(),
            "problem_classes": set(),
            "theorem_goals": set(),
            "candidate_declarations": [],
            "supporting_proof_obligations": set(),
        }
    )
    for raw in backlog.get("rows", []):
        if not isinstance(raw, dict):
            continue
        for primitive in raw.get("required_primitives", []) or []:
            key = str(primitive)
            bucket = grouped[key]
            bucket["gap_ids"].add(str(raw.get("gap_id", "")))
            bucket["problem_classes"].add(str(raw.get("problem_class", "")))
            bucket["theorem_goals"].add(str(raw.get("theorem_goal_id", "")))
            bucket["supporting_proof_obligations"].update(
                str(item) for item in raw.get("supporting_proof_obligations", []) or [] if str(item)
            )
            primitive_sources = raw.get("primitive_formal_sources", {})
            if isinstance(primitive_sources, dict):
                for candidate in primitive_sources.get(key, []) or []:
                    candidate_name = str(candidate)
                    if candidate_name and candidate_name not in bucket["candidate_declarations"]:
                        bucket["candidate_declarations"].append(candidate_name)

    rows: list[FormalizationTargetRow] = []
    for primitive, bucket in grouped.items():
        candidate_declarations = tuple(bucket["candidate_declarations"][:8])
        semantic_bridge_candidates = _semantic_bridge_candidates(primitive)
        supporting_proofs = _rank_supporting_proofs(
            primitive,
            tuple(sorted(set(bucket["supporting_proof_obligations"]) | set(semantic_bridge_candidates))),
        )
        bridge_candidates = tuple(
            obligation_id
            for obligation_id in supporting_proofs
            if _is_direct_bridge_candidate(primitive, obligation_id)
        )
        bridge_candidate_score = sum(
            _proof_bridge_score(primitive, obligation_id)
            for obligation_id in bridge_candidates
        )
        bridge_readiness = _bridge_readiness(candidate_declarations, supporting_proofs)
        n_gaps = len(bucket["gap_ids"])
        score = (
            100 * n_gaps
            + 10 * len(bucket["problem_classes"])
            + 3 * min(len(candidate_declarations), 8)
            + 2 * len(supporting_proofs)
            + 4 * len(bridge_candidates)
            + (15 if supporting_proofs and candidate_declarations else 0)
            + (10 if bridge_candidates else 0)
        )
        errors: list[str] = []
        if not candidate_declarations:
            errors.append("no local Lean/StatInference candidate declarations retrieved")
        if not bucket["theorem_goals"]:
            errors.append("no theorem goals attached")
        rows.append(
            FormalizationTargetRow(
                primitive=primitive,
                priority_score=score,
                priority_band=_priority_band(score, n_gaps, candidate_declarations, bridge_candidates),
                n_gaps=n_gaps,
                problem_classes=tuple(sorted(bucket["problem_classes"])),
                theorem_goals=tuple(sorted(bucket["theorem_goals"])),
                gap_ids=tuple(sorted(bucket["gap_ids"])),
                candidate_declarations=candidate_declarations,
                supporting_proof_obligations=supporting_proofs,
                bridge_candidate_obligations=bridge_candidates,
                bridge_candidate_score=bridge_candidate_score,
                proof_bank_bridge_available=bool(supporting_proofs),
                bridge_readiness=bridge_readiness,
                suggested_next_step=_suggest_next_step(
                    primitive,
                    candidate_declarations,
                    supporting_proofs,
                    bridge_candidates,
                ),
                ok=not errors,
                errors=tuple(errors),
            )
        )
    return sorted(rows, key=lambda row: (-row.priority_score, row.primitive))


def _priority_band(
    score: int,
    n_gaps: int,
    candidates: tuple[str, ...],
    bridge_candidates: tuple[str, ...] = (),
) -> str:
    if n_gaps >= 2 and candidates and bridge_candidates:
        return "HIGH_REUSE_BRIDGE_READY"
    if candidates and bridge_candidates:
        return "BRIDGE_REUSE_READY"
    if n_gaps >= 2 and candidates:
        return "HIGH_REUSE_READY"
    if candidates:
        return "LOCAL_SOURCE_GROUNDED"
    if score >= 100:
        return "HIGH_REUSE_NEEDS_SEARCH"
    return "LIBRARY_DESIGN_REQUIRED"


def _bridge_readiness(
    candidate_declarations: tuple[str, ...],
    supporting_proofs: tuple[str, ...],
) -> str:
    if candidate_declarations and supporting_proofs:
        return "PROOF_BANK_AND_LOCAL_SOURCE"
    if supporting_proofs:
        return "PROOF_BANK_ONLY"
    if candidate_declarations:
        return "LOCAL_SOURCE_ONLY"
    return "SEARCH_OR_LIBRARY_DESIGN"


def _count_by_bridge_readiness(rows: list[FormalizationTargetRow]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        counts[row.bridge_readiness] = counts.get(row.bridge_readiness, 0) + 1
    return dict(sorted(counts.items()))


def _suggest_next_step(
    primitive: str,
    candidate_declarations: tuple[str, ...],
    supporting_proofs: tuple[str, ...],
    bridge_candidates: tuple[str, ...] = (),
) -> str:
    if candidate_declarations and bridge_candidates:
        return (
            f"Use ranked verified bridge {bridge_candidates[0]} with local declaration "
            f"{candidate_declarations[0]} to formalize `{primitive}`."
        )
    if bridge_candidates:
        return f"Start from ranked verified proof-bank bridge {bridge_candidates[0]} and add the missing Lean interface for `{primitive}`."
    if candidate_declarations and supporting_proofs:
        return (
            f"Mine {candidate_declarations[0]} with ranked supporting obligations "
            f"{', '.join(supporting_proofs[:3])} while designing a new proof-bank bridge for `{primitive}`."
        )
    if candidate_declarations:
        return f"Start from local declaration {candidate_declarations[0]} and add a minimal AXLE proof-bank obligation."
    return f"Search Mathlib/StatInference/OpenProver for `{primitive}` before designing a new Lean interface."


def _rank_supporting_proofs(
    primitive: str,
    supporting_proofs: tuple[str, ...],
) -> tuple[str, ...]:
    return tuple(
        sorted(
            supporting_proofs,
            key=lambda obligation_id: (-_proof_bridge_score(primitive, obligation_id), obligation_id),
        )
    )


_PRIMITIVE_PROOF_BRIDGE_HINTS: dict[str, tuple[str, ...]] = {
    # These are not full selective-inference theorems. They are verified finite
    # event/coverage bridges that the target queue should surface when a
    # frontier gap asks for post-selection or data-dependent coverage machinery.
    "post_selection_inference": (
        "selected_good_event_coverage_of_finite_union_budget",
        "selected_bad_event_probability_le_finite_union_budget",
    ),
    "selected_interval_coverage": (
        "selected_good_event_coverage_of_finite_union_budget",
        "selected_bad_event_probability_le_finite_union_budget",
        "coverage_lower_bound_of_complement_error",
    ),
    "model_confidence_set_coverage": (
        "simultaneous_coverage_of_union_error_bound",
        "selected_good_event_coverage_of_finite_union_budget",
        "selected_bad_event_probability_le_finite_union_budget",
    ),
    "finite_sample_coverage_counting": (
        "finite_conformal_rank_coverage_counting",
        "simultaneous_coverage_of_union_error_bound",
        "coverage_lower_bound_of_complement_error",
    ),
    "exchangeable_scores": (
        "uniform_rank_pmf_mass",
        "finite_conformal_rank_coverage_counting",
    ),
    "rank_uniformity": (
        "uniform_rank_pmf_mass",
        "finite_conformal_rank_coverage_counting",
        "simultaneous_coverage_of_union_error_bound",
    ),
    "order_statistic_quantile_rule": (
        "finite_conformal_rank_coverage_counting",
        "coverage_lower_bound_of_complement_error",
    ),
    "valid_null_pvalue_uniformity": (
        "finite_null_pvalue_no_false_rejection_probability",
        "finite_null_family_no_false_rejection_probability",
        "finite_union_budget_control",
    ),
    "ordered_pvalues": (
        "bh_threshold_grid_mono",
        "finite_null_pvalue_no_false_rejection_probability",
        "finite_null_family_no_false_rejection_probability",
    ),
    "bh_stepup_self_consistency": (
        "bh_threshold_grid_mono",
        "finite_null_pvalue_no_false_rejection_probability",
        "finite_null_family_no_false_rejection_probability",
    ),
    "bh_threshold_fixed_point": (
        "bh_threshold_grid_mono",
    ),
    "leave_one_out_fdr_decomposition": (
        "finite_null_pvalue_no_false_rejection_probability",
        "finite_null_family_no_false_rejection_probability",
    ),
    "finite_population_potential_outcomes": (
        "finite_population_potential_outcomes",
        "finite_population_ate_mean_difference",
    ),
    "potential_outcome_consistency": (
        "potential_outcome_consistency",
        "potential_outcome_observed_consistency",
        "finite_population_ate_mean_difference",
    ),
    "positivity": (
        "propensity_score_ne_zero_of_lower_bound",
        "propensity_weight_mul_cancel_of_lower_bound",
        "propensity_weight_cancel_left_of_lower_bound",
    ),
    "propensity_weight_identity": (
        "propensity_weight_mul_cancel_of_lower_bound",
        "propensity_weight_cancel_left_of_lower_bound",
        "propensity_score_ne_zero_of_lower_bound",
    ),
    "complete_randomization_distribution": (
        "complete_randomization_distribution",
        "complete_randomization_uniform_assignment_mass",
    ),
    "difference_in_means_unbiasedness": (
        "finite_population_ate_mean_difference",
        "difference_estimator_unbiased",
        "finite_sample_mean_unbiased",
    ),
    "randomization_variance_decomposition": (
        "randomization_variance_decomposition_bridge",
        "neyman_variance_conservative_algebra",
        "difference_estimator_variance_decompose",
    ),
    "neyman_bound_nonnegative_treatment_effect_variance": (
        "neyman_bound_conservative_of_variance_decomposition",
        "neyman_variance_conservative_algebra",
        "variance_nonneg",
    ),
    "block_mean_definition": (
        "median_of_means_failure_union_control",
        "block_estimator_chebyshev_bound",
        "finite_sample_mean_chebyshev_indep",
    ),
    "independent_blocks": (
        "median_of_means_failure_union_control",
        "block_estimator_chebyshev_bound",
        "finite_sample_mean_variance_indep",
    ),
    "median_of_means_deviation": (
        "median_of_means_failure_union_control",
        "block_estimator_chebyshev_bound",
    ),
    "chebyshev_block_failure_bound": (
        "median_of_means_failure_union_control",
        "block_estimator_chebyshev_bound",
    ),
    "sequential_elimination_rule": (
        "sequential_elimination_rule_finite_union_control",
        "selected_bad_event_probability_le_finite_union_budget",
        "finite_union_budget_control",
        "simultaneous_coverage_of_union_error_bound",
    ),
    "adapted_product_process": (
        "independent_event_indicator_condExp_filtration_eq_prob",
        "independent_event_indicator_product_lintegral_eq_mul",
        "event_indicator_product_integral_eq_inter",
        "independent_event_inter_probability",
        "event_indicator_expectation",
    ),
    "bernoulli_likelihood_ratio": (
        "independent_event_indicator_condExp_filtration_eq_prob",
        "independent_event_indicator_product_lintegral_eq_mul",
        "event_indicator_product_integral_eq_inter",
        "finite_event_indicator_mean_unbiased",
        "event_indicator_expectation",
    ),
    "conditional_expectation_product_step": (
        "martingale_ae_eq_condexp_limit_process",
        "integrable_l1_tendsto_condexp_filtration",
        "integrable_ae_tendsto_condexp_filtration",
        "independent_event_indicator_condExp_filtration_eq_prob",
        "independent_real_condExp_natural_eq_mean",
        "independent_event_indicator_product_lintegral_eq_mul",
        "event_indicator_product_integral_eq_inter",
        "independent_event_inter_probability",
    ),
    "independent_bernoulli_sequence": (
        "independent_event_indicator_condExp_filtration_eq_prob",
        "independent_event_indicator_product_lintegral_eq_mul",
        "independent_event_inter_probability",
        "event_indicator_product_integral_eq_inter",
    ),
    "martingale_definition": (
        "martingale_ae_eq_condexp_limit_process",
        "integrable_l1_tendsto_condexp_filtration",
        "integrable_ae_tendsto_condexp_filtration",
        "independent_event_indicator_condExp_filtration_eq_prob",
        "independent_real_condExp_natural_eq_mean",
        "independent_event_indicator_product_lintegral_eq_mul",
        "event_indicator_product_integral_eq_inter",
        "event_indicator_expectation",
    ),
    "survival_martingale_clt": (
        "martingale_ae_eq_condexp_limit_process",
        "submartingale_l1_tendsto_limit_process",
        "submartingale_ae_tendsto_limit_process",
        "submartingale_expected_stopped_value_mono",
        "supermartingale_expected_stopped_value_antimono",
        "submartingale_doob_maximal_probability_bound",
        "iid_real_clt_tendsto_distribution",
    ),
    "nelson_aalen_martingale_decomposition": (
        "martingale_ae_eq_condexp_limit_process",
        "submartingale_l1_tendsto_limit_process",
        "submartingale_ae_tendsto_limit_process",
        "submartingale_expected_stopped_value_mono",
        "submartingale_stopped_process",
        "event_indicator_expectation",
    ),
    "greenwood_variance_consistency": (
        "martingale_ae_eq_condexp_limit_process",
        "submartingale_l1_tendsto_limit_process",
        "submartingale_ae_tendsto_limit_process",
        "finite_sample_mean_variance_indep",
        "variance_nonneg",
    ),
    "iid_empirical_mean_clt": (
        "iid_real_clt_tendsto_distribution",
        "independent_real_condExp_natural_eq_mean",
        "finite_sample_mean_unbiased",
        "finite_sample_mean_variance_indep",
        "finite_sample_mean_chebyshev_indep",
    ),
    "sample_moment_lln": (
        "iid_real_clt_tendsto_distribution",
        "independent_real_condExp_natural_eq_mean",
        "finite_sample_mean_unbiased",
        "finite_sample_mean_variance_indep",
    ),
    "conditional_mean_residual_zero": (
        "conditional_mean_residual_zero_of_condExp_ae_eq",
        "condexp_integral_eq_integral_real",
        "conditional_mean_residual_zero_of_mean_eq",
        "aipw_score_expectation_target_of_zero_aug",
        "aipw_score_expectation_target_of_aug_cancel",
        "independent_real_condExp_natural_eq_mean",
    ),
    "integrability_of_score_terms": (
        "integrability_of_score_terms",
        "aipw_score_integrable_of_components",
    ),
    "exogeneity_moment_condition": (
        "integrable_l1_tendsto_condexp_filtration",
        "integrable_ae_tendsto_condexp_filtration",
        "conditional_mean_residual_zero_of_condExp_ae_eq",
        "condexp_tower_of_sub_sigma_real",
        "condexp_integral_eq_integral_real",
        "conditional_mean_residual_zero_of_mean_eq",
        "independent_real_condExp_natural_eq_mean",
        "mean2_estimator_unbiased",
        "mean2_estimator_variance_indep",
    ),
    "conditional_expectation": (
        "integrable_l1_tendsto_condexp_filtration",
        "integrable_ae_tendsto_condexp_filtration",
        "condexp_tower_of_sub_sigma_real",
        "condexp_integral_eq_integral_real",
        "independent_real_condExp_natural_eq_mean",
        "independent_event_indicator_condExp_filtration_eq_prob",
        "event_indicator_expectation",
    ),
    "iterated_expectation": (
        "integrable_l1_tendsto_condexp_filtration",
        "integrable_ae_tendsto_condexp_filtration",
        "condexp_tower_of_sub_sigma_real",
        "condexp_integral_eq_integral_real",
        "independent_real_condExp_natural_eq_mean",
        "independent_event_indicator_condExp_filtration_eq_prob",
    ),
    "multivariate_score_clt": (
        "iid_real_clt_tendsto_distribution",
        "tendsto_in_distribution_continuous_mapping",
        "slutsky_add_negligible_zero_real",
        "independent_real_condExp_natural_eq_mean",
        "variance_nonneg",
    ),
    "wald_interval_slutsky": (
        "slutsky_add_negligible_zero_real",
        "tendsto_in_distribution_continuous_mapping",
        "iid_real_clt_tendsto_distribution",
        "wald_interval_contains_iff_abs_error",
        "wald_interval_miscoverage_iff_abs_error_gt",
    ),
    "slutsky_theorem": (
        "slutsky_add_negligible_zero_real",
        "tendsto_in_distribution_continuous_mapping",
        "iid_real_clt_tendsto_distribution",
    ),
    "empirical_process_remainder_bound": (
        "slutsky_add_negligible_zero_real",
        "iid_real_clt_tendsto_distribution",
    ),
    "matrix_inverse_continuous_mapping": (
        "tendsto_in_distribution_continuous_mapping",
    ),
    "tail_quantile_continuous_mapping": (
        "tendsto_in_distribution_continuous_mapping",
    ),
    "graph_functional_delta_method": (
        "tendsto_in_distribution_continuous_mapping",
        "slutsky_add_negligible_zero_real",
    ),
    "rank_uncertainty_functional_delta_method": (
        "tendsto_in_distribution_continuous_mapping",
        "slutsky_add_negligible_zero_real",
    ),
    "product_limit_delta_method": (
        "tendsto_in_distribution_continuous_mapping",
        "slutsky_add_negligible_zero_real",
    ),
    "influence_function_variance": (
        "iid_real_clt_tendsto_distribution",
        "slutsky_add_negligible_zero_real",
        "difference_estimator_variance_decompose",
        "variance_nonneg",
    ),
}


def _semantic_bridge_candidates(primitive: str) -> tuple[str, ...]:
    candidates: list[str] = []
    for obligation_id in _PRIMITIVE_PROOF_BRIDGE_HINTS.get(primitive, ()):
        try:
            get_obligation(obligation_id)
        except KeyError:
            continue
        if obligation_id not in candidates:
            candidates.append(obligation_id)
    return tuple(candidates)


def _proof_bridge_score(primitive: str, obligation_id: str) -> int:
    primitive_tokens = _tokens(primitive)
    if not primitive_tokens:
        return 0
    try:
        obligation = get_obligation(obligation_id)
    except KeyError:
        return 0
    id_tokens = _tokens(obligation.id)
    tag_tokens = set().union(*(_tokens(tag) for tag in obligation.tags)) if obligation.tags else set()
    text_tokens = _tokens(
        " ".join(
            (
                obligation.id,
                obligation.title,
                obligation.english,
                obligation.formal_statement,
                " ".join(obligation.tags),
                " ".join(obligation.expected_lemmas),
            )
        )
    )
    overlap = primitive_tokens & text_tokens
    id_overlap = primitive_tokens & id_tokens
    tag_overlap = primitive_tokens & tag_tokens
    score = 0
    score += 8 * len(id_overlap)
    score += 5 * len(tag_overlap)
    score += 3 * len(overlap)
    if primitive_tokens <= text_tokens:
        score += 20
    if obligation.id == primitive:
        score += 50
    return score


_COMMON_PRIMITIVE_TOKENS = {
    "bound",
    "control",
    "definition",
    "deviation",
    "error",
    "event",
    "failure",
    "finite",
    "for",
    "horizon",
    "in",
    "inference",
    "inequality",
    "of",
    "probability",
    "tail",
    "theorem",
    "type1",
    "under",
    "with",
}


def _is_direct_bridge_candidate(primitive: str, obligation_id: str) -> bool:
    if obligation_id in _PRIMITIVE_PROOF_BRIDGE_HINTS.get(primitive, ()):
        return True
    primitive_tokens = _tokens(primitive)
    specific_tokens = primitive_tokens - _COMMON_PRIMITIVE_TOKENS
    if not specific_tokens:
        return _proof_bridge_score(primitive, obligation_id) > 0
    try:
        obligation = get_obligation(obligation_id)
    except KeyError:
        return False
    bridge_tokens = _tokens(
        " ".join(
            (
                obligation.id,
                obligation.title,
                " ".join(obligation.tags),
                " ".join(obligation.expected_lemmas),
            )
        )
    )
    return specific_tokens <= bridge_tokens


def _tokens(text: str) -> set[str]:
    words = re.findall(r"[a-z0-9]+", text.lower().replace("_", " "))
    aliases: set[str] = set()
    for word in words:
        aliases.add(word)
        if word == "type" or word == "i":
            continue
        if word == "type1":
            aliases.update({"type", "i"})
        if word == "eprocess":
            aliases.update({"e", "process"})
        if word == "chebyshev":
            aliases.add("tail")
        if word.endswith("s") and len(word) > 3:
            aliases.add(word[:-1])
        if word.endswith("ness") and len(word) > 6:
            aliases.add(word[:-4])
        if word == "decomposition":
            aliases.add("decompose")
    if "type" in words and "i" in words:
        aliases.add("type1")
    if "e" in words and "process" in words:
        aliases.add("eprocess")
    return aliases


def _markdown_report(payload: dict[str, object]) -> str:
    rows = payload.get("rows", [])
    lines = [
        "# Formalization Target Queue",
        "",
        f"- Run directory: `{payload.get('run_dir')}`",
        f"- Targets: {payload.get('n_ok')}/{payload.get('n_targets')} audit-clean",
        f"- Proof-bank bridges available: {payload.get('n_with_proof_bank_bridge')}/{payload.get('n_targets')}",
        f"- Source gaps: {payload.get('source_gap_backlog', {}).get('n_ok')}/{payload.get('source_gap_backlog', {}).get('n_gaps')}",
        "",
        "## Top Targets",
        "",
    ]
    if not rows:
        lines.append("No formalization targets found.")
        return "\n".join(lines) + "\n"
    for row in rows[:20]:
        if not isinstance(row, dict):
            continue
        lines.extend(
            [
                f"### `{row.get('primitive')}` [{row.get('priority_band')}]",
                "",
                f"- Priority score: {row.get('priority_score')}",
                f"- Bridge readiness: `{row.get('bridge_readiness')}`",
                f"- Gaps unlocked: {row.get('n_gaps')}",
                f"- Problem classes: {', '.join(f'`{item}`' for item in row.get('problem_classes', [])) or 'none'}",
                f"- Theorem goals: {', '.join(f'`{item}`' for item in row.get('theorem_goals', [])) or 'none'}",
                f"- Local candidates: {', '.join(f'`{item}`' for item in row.get('candidate_declarations', [])) or 'none'}",
                f"- Supporting proof obligations: {', '.join(f'`{item}`' for item in row.get('supporting_proof_obligations', [])) or 'none'}",
                f"- Ranked bridge candidates: {', '.join(f'`{item}`' for item in row.get('bridge_candidate_obligations', [])) or 'none'}",
                f"- Bridge candidate score: {row.get('bridge_candidate_score')}",
                f"- Suggested next step: {row.get('suggested_next_step')}",
                "",
            ]
        )
        for error in row.get("errors", []) or []:
            lines.append(f"  - Error: {error}")
        if row.get("errors"):
            lines.append("")
    return "\n".join(lines)
