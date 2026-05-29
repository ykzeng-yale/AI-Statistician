from __future__ import annotations

import json
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .frontier_coverage_audit import audit_frontier_coverage


@dataclass(frozen=True)
class FrontierBacklogRow:
    question_id: str
    topic: str
    title: str
    source: str
    roadmap_domain: str
    missing_problem_class: str
    why_unsupported: str
    required_primitives: tuple[str, ...]
    likely_methods: tuple[str, ...]
    expected_results: tuple[str, ...]
    ok: bool
    errors: tuple[str, ...] = ()


@dataclass(frozen=True)
class RoadmapDomainSpec:
    domain: str
    missing_problem_class: str
    keywords: tuple[str, ...]
    required_primitives: tuple[str, ...]
    likely_methods: tuple[str, ...]


DOMAIN_SPECS: tuple[RoadmapDomainSpec, ...] = (
    RoadmapDomainSpec(
        domain="experimental_design_optimization",
        missing_problem_class="space_filling_order_addition_covariate_balance_designs",
        keywords=(
            "space-filling",
            "oracle arrays",
            "order-of-addition",
            "covariate balance",
            "gaussianized",
            "design optimization",
            "adaptive assignment",
        ),
        required_primitives=(
            "finite_design_space",
            "maximin_distance_criterion",
            "orthogonal_array_construction",
            "covariate_balance_objective",
            "randomized_design_precision_order",
        ),
        likely_methods=("combinatorial_design_theory", "randomization_inference", "convex_design_optimization"),
    ),
    RoadmapDomainSpec(
        domain="sequential_changepoint_functional_time_series",
        missing_problem_class="functional_time_series_changepoint_and_post_detection_inference",
        keywords=(
            "structural breaks",
            "changepoint",
            "post-detection",
            "functional time series",
            "sequential model confidence",
            "locally stationary",
            "measurement error",
        ),
        required_primitives=(
            "functional_time_series_process",
            "locally_stationary_array",
            "changepoint_stopping_rule",
            "post_selection_inference",
            "bootstrap_validity_for_dependent_data",
        ),
        likely_methods=("sequential_empirical_process", "bootstrap_changepoint_test", "post_selection_inference"),
    ),
    RoadmapDomainSpec(
        domain="high_dimensional_latent_structure",
        missing_problem_class="sufficient_dimension_reduction_tensor_and_membership_models",
        keywords=(
            "grade-of-membership",
            "sufficient dimension",
            "tensor-valued",
            "dimension association",
            "locally dependent",
            "variable selection",
        ),
        required_primitives=(
            "latent_membership_model",
            "sufficient_dimension_reduction_target",
            "tensor_covariate_operator",
            "local_dependence_condition",
            "high_dimensional_selection_consistency",
        ),
        likely_methods=("latent_variable_inference", "sufficient_dimension_reduction", "tensor_regression_asymptotics"),
    ),
    RoadmapDomainSpec(
        domain="statistical_learning_nonparametric",
        missing_problem_class="deep_nonparametric_transfer_active_preference_learning",
        keywords=(
            "deep neural network",
            "nonparametric",
            "transfer learning",
            "multi-task",
            "p-spline",
            "preference learning",
            "active learning",
            "human feedback",
        ),
        required_primitives=(
            "nonparametric_function_class",
            "neural_network_sieve_space",
            "covering_number_entropy_bound",
            "excess_risk_decomposition",
            "adaptive_data_dependence",
        ),
        likely_methods=("sieve_m_estimation", "empirical_process_bounds", "online_learning_regret_inference"),
    ),
    RoadmapDomainSpec(
        domain="privacy_distributed_robust_learning",
        missing_problem_class="differential_privacy_byzantine_distributed_and_model_privacy",
        keywords=(
            "differential privacy",
            "privacy",
            "byzantine",
            "distributed",
            "model stealing",
            "edgeworth accountant",
            "federated",
            "general loss",
        ),
        required_primitives=(
            "differential_privacy_definition",
            "privacy_composition_accountant",
            "distributed_estimator_aggregation",
            "byzantine_contamination_model",
            "general_loss_stability_bound",
        ),
        likely_methods=("privacy_accounting", "robust_distributed_m_estimation", "model_stealing_risk_formalization"),
    ),
    RoadmapDomainSpec(
        domain="bayesian_computation_posterior_calibration",
        missing_problem_class="bayesian_trees_priors_mcmc_and_manifold_sampling",
        keywords=(
            "bayesian",
            "bart",
            "prior",
            "posterior",
            "metropolis",
            "picard",
            "slice sampling",
            "riemannian",
        ),
        required_primitives=(
            "prior_posterior_kernel",
            "markov_chain_transition_kernel",
            "mcmc_stationary_distribution",
            "posterior_predictive_calibration",
            "manifold_measure_sampling",
        ),
        likely_methods=("posterior_contraction", "mcmc_convergence", "bayesian_nonparametric_trees"),
    ),
    RoadmapDomainSpec(
        domain="network_graph_dependence",
        missing_problem_class="network_mixed_membership_signed_and_dynamic_graph_inference",
        keywords=(
            "network",
            "graph",
            "mixed-membership",
            "signed networks",
            "dependent edges",
            "time-varying network",
            "binary graphical models",
        ),
        required_primitives=(
            "random_graph_model",
            "graph_dependence_structure",
            "mixed_membership_parameter",
            "network_autoregression",
            "graph_functional_asymptotic_normality",
        ),
        likely_methods=("network_u_statistics", "spectral_graph_inference", "dependent_edge_empirical_process"),
    ),
    RoadmapDomainSpec(
        domain="geometric_spatial_point_process",
        missing_problem_class="spatial_fields_metric_graphs_manifolds_and_point_processes",
        keywords=(
            "spatial",
            "gaussian fields",
            "metric graphs",
            "matérn",
            "whittle",
            "point process",
            "palm",
            "manifold",
        ),
        required_primitives=(
            "metric_graph_space",
            "gaussian_random_field",
            "spde_matern_covariance",
            "point_process_palm_distribution",
            "manifold_asymptotic_delta_method",
        ),
        likely_methods=("spatial_likelihood_asymptotics", "point_process_inference", "manifold_statistics"),
    ),
    RoadmapDomainSpec(
        domain="heavy_tail_time_series_extremal_dependence",
        missing_problem_class="infinite_mean_time_series_extremal_dependence_and_tail_factor_models",
        keywords=(
            "infinite-mean",
            "autoregressive conditional durations",
            "extremal dependence",
            "hyperplane",
            "tail-robust",
            "factor modelling",
            "vector and tensor time series",
        ),
        required_primitives=(
            "regular_variation_for_processes",
            "infinite_mean_limit_theory",
            "extremal_dependence_measure",
            "tail_robust_factor_model",
            "heavy_tail_time_series_limit",
        ),
        likely_methods=("stable_limit_theory", "multivariate_extreme_value_theory", "tail_factor_model_asymptotics"),
    ),
    RoadmapDomainSpec(
        domain="missing_measurement_mediation_data_integration",
        missing_problem_class="measurement_bias_nonignorable_missingness_mediation_and_deconvolution",
        keywords=(
            "measurement bias",
            "country ranking",
            "nonignorable missing",
            "missing confounders",
            "mediation",
            "cell type deconvolution",
            "data integration",
        ),
        required_primitives=(
            "measurement_error_model",
            "nonignorable_missingness_model",
            "mediation_identification_functional",
            "data_integration_estimand",
            "deconvolution_inverse_problem",
        ),
        likely_methods=("semiparametric_missing_data", "measurement_error_correction", "inverse_problem_regularization"),
    ),
)


def audit_frontier_backlog(
    out_dir: Path | None = None,
    *,
    benchmark_file: Path = Path("docs/frontier_stat_theory_benchmark.md"),
) -> dict[str, object]:
    """Turn unsupported frontier benchmark rows into an explicit roadmap.

    This audit deliberately does not make unsupported papers executable.  It
    records why they remain outside the current registry and what theory
    primitives would be needed before the lab can support them.
    """

    coverage = audit_frontier_coverage(benchmark_file=benchmark_file)
    rows: list[FrontierBacklogRow] = []
    for raw in coverage["rows"]:  # type: ignore[index]
        if bool(raw.get("supported")):
            continue
        rows.append(_classify_backlog_row(raw))

    by_domain = Counter(row.roadmap_domain for row in rows)
    by_required_primitive = Counter(
        primitive
        for row in rows
        for primitive in row.required_primitives
    )
    payload = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "benchmark_file": str(benchmark_file),
        "n_frontier_questions": coverage["n_questions"],
        "n_supported": coverage["n_supported"],
        "n_backlog": len(rows),
        "n_ok": sum(1 for row in rows if row.ok),
        "all_ok": bool(coverage["all_ok"]) and all(row.ok for row in rows),
        "by_domain": dict(sorted(by_domain.items())),
        "by_required_primitive": dict(sorted(by_required_primitive.items())),
        "rows": [asdict(row) for row in rows],
    }
    if out_dir is not None:
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "frontier_backlog_manifest.json").write_text(
            json.dumps(payload, indent=2, default=str),
            encoding="utf-8",
        )
        (out_dir / "frontier_backlog.md").write_text(_markdown_report(payload), encoding="utf-8")
    return payload


def _classify_backlog_row(raw: dict[str, Any]) -> FrontierBacklogRow:
    text = " ".join(
        [
            str(raw.get("topic", "")),
            str(raw.get("title", "")),
            str(raw.get("open_question", "")),
            str(raw.get("assumptions", "")),
            " ".join(str(item) for item in raw.get("expected_results", ())),
        ]
    ).lower()
    spec = _best_domain_spec(text, str(raw.get("topic", "")))
    errors: list[str] = []
    if not spec.required_primitives:
        errors.append("missing required_primitives")
    if not spec.likely_methods:
        errors.append("missing likely_methods")
    if not raw.get("expected_results"):
        errors.append("missing expected_results")
    return FrontierBacklogRow(
        question_id=str(raw.get("question_id", "")),
        topic=str(raw.get("topic", "")),
        title=str(raw.get("title", "")),
        source=str(raw.get("source", "")),
        roadmap_domain=spec.domain,
        missing_problem_class=spec.missing_problem_class,
        why_unsupported=(
            "No registered research problem class, theorem-goal template, vetted "
            "algorithm, simulator, or Lean proof-bank bridge currently covers this frontier topic."
        ),
        required_primitives=spec.required_primitives,
        likely_methods=spec.likely_methods,
        expected_results=tuple(str(item) for item in raw.get("expected_results", ())),
        ok=not errors,
        errors=tuple(errors),
    )


def _best_domain_spec(text: str, topic: str) -> RoadmapDomainSpec:
    scored: list[tuple[int, RoadmapDomainSpec]] = []
    for spec in DOMAIN_SPECS:
        score = sum(1 for keyword in spec.keywords if keyword.lower() in text)
        if spec.domain.replace("_", " ") in topic.replace("_", " "):
            score += 2
        scored.append((score, spec))
    best_score, best = max(scored, key=lambda item: (item[0], item[1].domain))
    if best_score > 0:
        return best
    return RoadmapDomainSpec(
        domain="manual_frontier_theory_triage",
        missing_problem_class="manual_problem_class_design_required",
        keywords=(),
        required_primitives=("manual_literature_review", "manual_formalization_design"),
        likely_methods=("human_theory_triage",),
    )


def _markdown_report(payload: dict[str, object]) -> str:
    rows = payload.get("rows", [])
    lines = [
        "# Frontier Unsupported-Theory Backlog",
        "",
        f"- Benchmark file: `{payload.get('benchmark_file')}`",
        f"- Supported now: {payload.get('n_supported')}/{payload.get('n_frontier_questions')}",
        f"- Backlog rows: {payload.get('n_ok')}/{payload.get('n_backlog')} audit-clean",
        "",
        "## Roadmap Domains",
        "",
    ]
    by_domain = payload.get("by_domain", {})
    if isinstance(by_domain, dict):
        for domain, count in sorted(by_domain.items()):
            lines.append(f"- `{domain}`: {count}")
    lines.extend(["", "## Backlog Rows", ""])
    if isinstance(rows, list):
        for row in rows:
            if not isinstance(row, dict):
                continue
            status = "OK" if row.get("ok") else "NEEDS_ATTENTION"
            lines.extend(
                [
                    f"### {row.get('question_id')} [{status}]",
                    "",
                    f"- Topic: `{row.get('topic')}`",
                    f"- Title: {row.get('title')}",
                    f"- Roadmap domain: `{row.get('roadmap_domain')}`",
                    f"- Missing problem class: `{row.get('missing_problem_class')}`",
                    f"- Required primitives: {', '.join(f'`{item}`' for item in row.get('required_primitives', []))}",
                    f"- Likely methods: {', '.join(f'`{item}`' for item in row.get('likely_methods', []))}",
                    "",
                ]
            )
            for error in row.get("errors") or []:
                lines.append(f"  - Error: {error}")
            if row.get("errors"):
                lines.append("")
    return "\n".join(lines) + "\n"
