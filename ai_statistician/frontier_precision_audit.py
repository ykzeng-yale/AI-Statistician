from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .frontier_coverage_audit import audit_frontier_coverage
from .research_intake_audit import UNSUPPORTED_PROBLEM_CLASS


CLASS_EVIDENCE_TERMS: dict[str, tuple[str, ...]] = {
    "semiparametric_causal_ate": (
        "average treatment effect",
        "treatment effect",
        "treatment-effect",
        "principal stratification",
        "unmeasured confounding",
        "individual treatment effect",
        "policy value",
        "causal",
        "cate",
        "ate",
    ),
    "design_based_variance_inference": (
        "conservative variance",
        "variance estimation",
        "estimable variance bound",
        "design-based",
        "randomization variance",
        "complex experimental designs",
    ),
    "experimental_design_optimization": (
        "space-filling",
        "space filling",
        "maximin",
        "maximin distance criterion",
        "oracle arrays",
        "hamming-distance array",
        "order-of-addition",
        "order of addition",
        "stratum orthogonality",
        "covariate balance",
        "gaussianized",
        "design optimization",
    ),
    "distribution_free_conformal_prediction": (
        "conformal",
        "prediction interval",
        "prediction set",
        "coverage guarantee",
        "marginal coverage",
    ),
    "right_censored_survival_inference": (
        "right-censored",
        "right censored",
        "censored data",
        "survival",
        "hazard",
        "time-to-event",
        "time to event",
    ),
    "robust_mean_inference": (
        "sub-gaussian mean",
        "subgaussian mean",
        "robust sub-gaussian",
        "robust mean",
        "mean estimation under",
        "star-shaped constraint",
        "star shaped constraint",
    ),
    "differential_privacy_learning": (
        "differential privacy",
        "differentially private",
        "local differential privacy",
        "privacy composition",
        "privacy-loss",
        "privacy loss",
        "private mechanisms",
        "privacy accountant",
        "edgeworth accountant",
        "general loss functions",
    ),
    "nonparametric_regression_inference": (
        "generalized nonparametric",
        "deep neural network",
        "deep neural networks",
        "dnn estimator",
        "deep p-spline",
        "penalized spline",
        "neural-network architecture selection",
        "basis-expansion analogy",
        "knot selection",
        "subject-specific mean",
        "subject-specific means",
    ),
    "network_graph_inference": (
        "mixed-membership",
        "mixed membership",
        "degree-corrected mixed-membership",
        "node mixing probabilities",
        "signed network",
        "signed networks",
        "dynamic networks",
        "autoregressive networks",
        "dependent edges",
        "network vector autoregression",
        "binary graphical models",
        "dependence graph density",
        "graph connectivity parameter",
    ),
    "bayesian_posterior_calibration": (
        "predictive distributions into informative priors",
        "predictive distributions from one analysis",
        "predictive distribution",
        "informative priors",
        "prior elicitation",
        "uncertainty propagation",
        "predictive uncertainty",
        "bayesian model",
    ),
    "measurement_bias_ranking_inference": (
        "measurement bias",
        "country ranking",
        "country rankings",
        "educational assessments",
        "item response theory ranking",
        "cultural or linguistic bias",
        "ranking uncertainty",
        "measurement noninvariance",
    ),
    "heteroskedastic_regression_inference": (
        "heteroskedastic",
        "sandwich",
        "hc1",
        "robust standard",
    ),
    "multiple_testing_fdr": (
        "false discovery",
        "false discoveries",
        "fdr",
        "multiple testing",
        "multiple hypotheses",
        "knockoff",
    ),
    "sequential_anytime_inference": (
        "anytime",
        "anytime-valid",
        "anytime valid",
        "optional stopping",
        "e-process",
        "filtration",
        "sequential test",
    ),
    "high_dimensional_pca_inference": (
        "pca",
        "principal component",
        "principal components",
        "eigenvector",
        "eigenvalue",
        "eigenspace",
        "spectrum",
        "fpca",
    ),
    "extreme_tail_quantile_inference": (
        "tail index",
        "high quantile",
        "high quantiles",
        "extreme quantile",
        "extreme quantiles",
        "regular variation",
        "value-at-risk",
        "value at risk",
    ),
}


@dataclass(frozen=True)
class FrontierPrecisionRow:
    question_id: str
    title: str
    topic: str
    problem_class: str
    evidence_terms: tuple[str, ...]
    ok: bool
    reason: str


def audit_frontier_precision(
    out_dir: Path | None = None,
    *,
    benchmark_file: Path = Path("docs/frontier_stat_theory_benchmark.md"),
) -> dict[str, object]:
    """Audit whether supported frontier classifications have direct evidence.

    This is intentionally stricter than the coverage audit. Coverage says how
    many rows the deterministic formalizer can route. Precision asks whether the
    routed rows contain class-specific evidence in the paper body fields
    (title/open question/assumptions/expected results), not merely in broad topic
    tags such as "multiple_testing_conformal_selection".
    """

    coverage = audit_frontier_coverage(benchmark_file=benchmark_file)
    rows: list[FrontierPrecisionRow] = []
    for row in coverage["rows"]:  # type: ignore[index]
        if not isinstance(row, dict) or row.get("problem_class") == UNSUPPORTED_PROBLEM_CLASS:
            continue
        problem_class = str(row.get("problem_class"))
        terms = CLASS_EVIDENCE_TERMS.get(problem_class, ())
        body = _body_text(row)
        hits = tuple(term for term in terms if _term_present(term, body))
        ok = bool(terms) and bool(hits)
        rows.append(
            FrontierPrecisionRow(
                question_id=str(row.get("question_id")),
                title=str(row.get("title")),
                topic=str(row.get("topic")),
                problem_class=problem_class,
                evidence_terms=hits,
                ok=ok,
                reason=(
                    "direct body evidence found"
                    if ok
                    else "supported classification lacks class-specific body evidence"
                ),
            )
        )

    payload = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "benchmark_file": str(benchmark_file),
        "coverage_manifest": {
            "n_questions": coverage["n_questions"],
            "n_supported": coverage["n_supported"],
            "n_unsupported": coverage["n_unsupported"],
            "supported_rate": coverage["supported_rate"],
            "by_problem_class": coverage["by_problem_class"],
        },
        "n_supported": len(rows),
        "n_ok": sum(1 for row in rows if row.ok),
        "n_flagged": sum(1 for row in rows if not row.ok),
        "all_ok": bool(rows) and all(row.ok for row in rows),
        "rows": [asdict(row) for row in rows],
    }
    if out_dir is not None:
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "frontier_precision_manifest.json").write_text(
            json.dumps(payload, indent=2, default=str),
            encoding="utf-8",
        )
        (out_dir / "frontier_precision.md").write_text(_markdown_report(payload), encoding="utf-8")
    return payload


def _body_text(row: dict[str, Any]) -> str:
    expected = row.get("expected_results") or ()
    if not isinstance(expected, (list, tuple)):
        expected = (str(expected),)
    return " ".join(
        [
            str(row.get("title", "")),
            str(row.get("open_question", "")),
            str(row.get("assumptions", "")),
            " ".join(str(item) for item in expected),
        ]
    ).lower()


def _term_present(term: str, body: str) -> bool:
    normalized = term.lower()
    if re.fullmatch(r"[a-z0-9_]+", normalized):
        return normalized in set(re.findall(r"[a-z0-9_]+", body))
    return normalized in body


def _markdown_report(payload: dict[str, object]) -> str:
    lines = [
        "# Frontier Classification Precision Audit",
        "",
        f"- Benchmark file: `{payload.get('benchmark_file')}`",
        f"- Supported rows with body evidence: {payload.get('n_ok')}/{payload.get('n_supported')}",
        f"- Flagged rows: {payload.get('n_flagged')}",
        f"- All ok: `{payload.get('all_ok')}`",
        "",
        "| OK | Question | Class | Evidence terms |",
        "|---:|---|---|---|",
    ]
    for row in payload.get("rows", []):
        if not isinstance(row, dict):
            continue
        evidence = ", ".join(row.get("evidence_terms", ())) or row.get("reason", "")
        lines.append(
            f"| {row.get('ok')} | `{row.get('question_id')}` | `{row.get('problem_class')}` | {evidence} |"
        )
    return "\n".join(lines) + "\n"
