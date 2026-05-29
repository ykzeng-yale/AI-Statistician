from __future__ import annotations

import json
import math
import re
import hashlib
import inspect
import itertools
from dataclasses import asdict, replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np

from .fingerprint import stable_hash
from .formal_source_index import FormalSourceHit, FormalSourceRetriever, build_formal_source_search_backend
from .proof_bank import all_obligations, get_obligation, proof_bank_fingerprint
from .research_knowledge import KNOWLEDGE_CARDS, retrieve_problem_knowledge
from .research_paper_index import paper_source_index_fingerprint, retrieve_paper_sources
from .research_source_inventory import research_source_inventory_fingerprint
from .research_schema import (
    CandidateProcedure,
    FormalSubclaim,
    KnowledgeCard,
    OpenResearchQuestion,
    ResearchAlgorithmSpec,
    ResearchProblemSpec,
    ResearchReport,
    ResearchSimulation,
    SimulationDiagnosis,
    TheoremGoal,
)
from .retrieval import ProofBankRetriever, RetrievalQuery
from .verifier import MockProofVerifier, ProofVerifier


EXTRACTION_EVIDENCE_TERMS: dict[str, dict[str, tuple[str, ...]]] = {
    "semiparametric_causal_ate": {
        "problem_class": ("causal", "ate", "average treatment effect", "treatment effect", "principal stratification", "unmeasured confounding", "aipw", "cate"),
        "dgp": ("observational data", "observed-data", "binary treatment", "binary intermediate variable", "nonparametric observed-data model", "potential outcomes", "covariates", "experiments", "treatment assignment"),
        "estimand": ("average treatment effect", "treatment effect", "principal average", "individual treatment effect", "fraction negatively affected", "policy value"),
        "assumptions": ("consistency", "exchangeability", "positivity", "unconfoundedness", "principal ignorability", "potential outcomes"),
        "asymptotic_regime": ("asymptotic", "efficient influence", "u-statistic", "inference", "test", "valid"),
    },
    "distribution_free_conformal_prediction": {
        "problem_class": ("conformal", "exchangeability", "prediction interval", "coverage guarantee", "distribution-free"),
        "dgp": ("exchangeable", "regression", "prediction", "calibration"),
        "estimand": ("prediction interval", "coverage", "marginal coverage", "joint uncertainty regions", "missing entries"),
        "assumptions": ("exchangeability", "exchangeable", "calibration", "finite calibration"),
        "asymptotic_regime": (
            "finite-sample",
            "coverage",
            "distribution-free",
            "validity",
            "exchangeability",
            "conformal calibration",
            "joint uncertainty",
        ),
    },
    "right_censored_survival_inference": {
        "problem_class": ("survival", "right-censored", "censored data", "hazard", "kaplan", "meier", "nelson", "aalen"),
        "dgp": ("time-to-event", "right censoring", "censored", "event", "hazard"),
        "estimand": ("survival probability", "survival", "cumulative hazard", "hazard"),
        "assumptions": ("independent censoring", "noninformative censoring", "right censoring", "right-censored survival", "conditional hazard", "likelihood-based", "iid"),
        "asymptotic_regime": (
            "asymptotic",
            "greenwood",
            "consistency",
            "fixed-time",
            "large-sample",
            "nonparametric hazard inference",
            "dnn approximation",
            "likelihood-based estimator",
        ),
    },
    "robust_mean_inference": {
        "problem_class": ("robust mean", "sub-gaussian mean", "heavy-tailed mean", "contamination", "median-of-means", "star-shaped"),
        "dgp": ("heavy-tailed", "contamination", "gross-error", "iid data", "finite variance", "gaussian mean model", "sub-gaussian mean model"),
        "estimand": ("mean", "location parameter", "uncontaminated mean"),
        "assumptions": ("finite variance", "contamination", "heavy-tailed", "gross-error", "star-shaped constraint", "adversarial corruption", "epsilon-fraction"),
        "asymptotic_regime": ("sub-gaussian", "minimax", "deviation", "large-sample", "rate"),
    },
    "differential_privacy_learning": {
        "problem_class": (
            "differential privacy",
            "local differential privacy",
            "privacy composition",
            "private learning",
            "differentially private",
            "privacy-loss",
            "privacy loss",
            "edgeworth accountant",
        ),
        "dgp": (
            "private mechanisms",
            "privacy-loss random variables",
            "local privacy setting",
            "general empirical loss functions",
            "bounded data",
            "training sample",
        ),
        "estimand": (
            "private estimator",
            "privacy accountant",
            "overall privacy accounting",
            "excess risk",
            "empirical loss",
            "mean",
        ),
        "assumptions": (
            "composition of private mechanisms",
            "privacy-loss random variables",
            "local privacy setting",
            "bounded sensitivity",
            "epsilon",
            "delta",
            "general empirical loss functions",
        ),
        "asymptotic_regime": (
            "edgeworth expansion",
            "composition",
            "online",
            "increasing data volume",
            "asymptotic",
            "error control",
        ),
    },
    "nonparametric_regression_inference": {
        "problem_class": (
            "generalized nonparametric",
            "deep neural network",
            "deep neural networks",
            "dnn estimator",
            "deep p-spline",
            "penalized spline",
            "neural-network architecture selection",
        ),
        "dgp": (
            "generalized nonparametric regression model",
            "categorical or exponential-family outcomes",
            "regression with dnns",
            "basis-expansion analogy",
            "difference penalty",
            "latent-variable ecm tuning",
        ),
        "estimand": (
            "subject-specific means",
            "subject-specific mean",
            "regression function",
            "conditional mean",
            "architecture selection",
            "knot selection",
        ),
        "assumptions": (
            "dnn estimator",
            "dependence between estimation error and inputs",
            "difference penalty",
            "basis-expansion analogy",
            "latent-variable ecm tuning",
        ),
        "asymptotic_regime": (
            "error bounds",
            "ensemble subsampling inference",
            "u-statistic",
            "asymptotic validity",
            "approximation",
            "estimation",
        ),
    },
    "high_dimensional_latent_structure_inference": {
        "problem_class": (
            "grade-of-membership",
            "grade of membership",
            "sufficient dimension association",
            "sufficient dimension reduction",
            "tensor-valued predictors",
            "tensor valued predictors",
            "multilinear models",
            "mixed-membership simplex",
        ),
        "dgp": (
            "multivariate categorical responses",
            "high-dimensional polytomous items",
            "locally dependent data",
            "high-dimensional predictors",
            "tensor-valued predictors",
            "quadratic exponential family inverse model",
            "continuous or binary tensor predictors",
        ),
        "estimand": (
            "mixed-membership simplex structure",
            "membership and model parameters",
            "conditional association target",
            "variable selection",
            "low-dimensional reductions",
            "sufficient dimension association",
        ),
        "assumptions": (
            "local dependence",
            "mixed-membership simplex structure",
            "possible nonlinear or misspecified regression",
            "tensor-valued predictors",
            "quadratic exponential family inverse model",
            "multilinear low-dimensional reductions",
        ),
        "asymptotic_regime": (
            "high-dimensional predictors",
            "high-dimensional polytomous items",
            "locally dependent data",
            "tensor-valued predictors",
            "high-dimensional estimation guarantees",
            "high-dimensional asymptotics",
            "selection consistency",
            "beyond sparse linear models",
            "tensor dimensions",
            "low-dimensional reductions",
        ),
    },
    "network_graph_inference": {
        "problem_class": (
            "mixed-membership",
            "mixed membership",
            "degree-corrected mixed-membership",
            "signed network",
            "signed networks",
            "dynamic networks",
            "autoregressive networks",
            "network vector autoregression",
            "binary graphical models",
            "dependence graph density",
        ),
        "dgp": (
            "network latent structure",
            "node-level mixed membership",
            "signed network with positive and negative ties",
            "time-indexed network sequence",
            "conditional edge independence",
            "dependent edges",
            "latent group structure",
            "binary interacting chains",
            "directed erdos-renyi dependence graph",
        ),
        "estimand": (
            "mixing probabilities",
            "node mixing probabilities",
            "network rankings",
            "latent network rankings",
            "balance theory",
            "time-varying momentum",
            "spillover effects",
            "graph connectivity parameter",
            "graph density",
        ),
        "assumptions": (
            "degree-corrected mixed-membership model",
            "balance-theory generating process",
            "conditional edge independence given lagged network",
            "dependent-edge features",
            "network vector autoregression",
            "latent groups",
            "excitatory and inhibitory populations",
        ),
        "asymptotic_regime": (
            "inference on node mixing probabilities",
            "validity and consistency under network dependence",
            "increasing parameter dimension",
            "time-varying coefficients",
            "graph connectivity",
            "spectral graph inference",
        ),
    },
    "geometric_spatial_point_process_inference": {
        "problem_class": (
            "anisotropic gaussian fields",
            "gaussian random fields",
            "whittle-matern",
            "whittle matern",
            "metric graph",
            "metric graphs",
            "point process",
            "point-process",
            "palm distributions",
            "palm distribution",
            "spatial",
            "manifold",
            "riemannian manifolds",
            "stiefel",
            "grassmann",
        ),
        "dgp": (
            "gaussian random fields via spdes",
            "compact metric graph",
            "graph-supported observations",
            "point-process predictors",
            "random counting measures",
            "independent point-process superposition",
            "shot-noise cox processes",
            "kernel embedding",
            "posterior distributions on riemannian manifolds",
            "riemannian manifolds",
        ),
        "estimand": (
            "anisotropic correlation length",
            "diffusion matrix",
            "matern field",
            "prediction",
            "penalized likelihood",
            "intensity",
            "palm distributions",
            "minimum contrast",
            "additive model",
            "posterior distributions",
            "slice sampling",
        ),
        "assumptions": (
            "spde",
            "penalized complexity priors",
            "compact metric graph",
            "sobolev",
            "poincare inequalities",
            "point-process covariates",
            "palm distributions",
            "superposition",
            "riemannian manifold",
            "stiefel",
            "grassmann",
        ),
        "asymptotic_regime": (
            "in-fill asymptotics",
            "consistency",
            "asymptotic normality",
            "optimal prediction",
            "selection consistency",
            "higher-order palm",
            "janossy",
            "posterior distributions",
            "riemannian manifolds",
        ),
    },
    "bayesian_posterior_calibration": {
        "problem_class": (
            "predictive distributions into informative priors",
            "predictive distribution",
            "informative priors",
            "prior elicitation",
            "posterior calibration",
            "bayesian model",
        ),
        "dgp": (
            "available predictive distribution",
            "target bayesian model",
            "subsequent model",
            "normal likelihood",
            "historical prediction",
        ),
        "estimand": (
            "posterior mean",
            "posterior distribution",
            "credible interval",
            "predictive uncertainty",
            "population mean",
            "informative priors",
            "target bayesian model",
        ),
        "assumptions": (
            "available predictive distribution",
            "prior elicitation through prediction",
            "uncertainty propagation",
            "normal conjugate",
            "prior-likelihood coherence",
        ),
        "asymptotic_regime": (
            "posterior calibration",
            "coherence",
            "coverage calibration",
            "uncertainty validity",
            "uncertainty propagation",
            "prior elicitation through prediction",
            "target bayesian model",
            "large-sample",
        ),
    },
    "measurement_bias_ranking_inference": {
        "problem_class": (
            "measurement bias",
            "country ranking",
            "country rankings",
            "educational assessments",
            "item-response",
            "item response",
            "ranking uncertainty",
        ),
        "dgp": (
            "large-scale educational assessment",
            "item response theory ranking",
            "measurements contain cultural or linguistic bias",
            "countries/items",
            "country/item bias",
        ),
        "estimand": (
            "country ability",
            "country ranking",
            "bias-adjusted ranking",
            "ranking reliability",
            "latent performance",
        ),
        "assumptions": (
            "measurement bias across countries/items",
            "measurement noninvariance",
            "known or calibratable bias terms",
            "item response theory ranking",
            "ranking uncertainty",
        ),
        "asymptotic_regime": (
            "ranking reliability",
            "large-scale",
            "bias-adjusted",
            "inference procedures",
            "measurement noninvariance",
        ),
    },
    "design_based_variance_inference": {
        "problem_class": ("optimized variance estimation", "conservative variance", "estimable variance bound", "design-based", "complex experimental designs", "variance estimation"),
        "dgp": ("randomized experiment", "potential outcomes", "assignment", "interference", "complex designs"),
        "estimand": ("randomization variance", "variance", "average treatment effect", "treatment-effect estimator"),
        "assumptions": ("fixed potential outcomes", "randomization", "heterogeneous", "interference", "assignment"),
        "asymptotic_regime": ("finite-sample", "design-based", "validity", "least conservative", "optimized"),
    },
    "experimental_design_optimization": {
        "problem_class": (
            "space-filling",
            "space filling",
            "maximin",
            "oracle arrays",
            "order-of-addition",
            "order of addition",
            "covariate balance",
            "gaussianized",
            "design optimization",
        ),
        "dgp": (
            "finite candidate design points",
            "computer experiments",
            "randomized experiment",
            "component order",
            "covariates",
            "assignment",
        ),
        "estimand": (
            "maximin distance criterion",
            "space-filling design",
            "covariate balance objective",
            "stratum orthogonality",
            "balanced assignment",
        ),
        "assumptions": (
            "finite design space",
            "limited run budget",
            "covariates observed before assignment",
            "symmetric randomized assignment",
            "model uncertainty",
            "quantitative factors",
            "hamming-distance array",
            "mapping from discrete arrays",
            "treatments represented through gaussianized assignments",
            "continuous optimization over covariance matrices",
        ),
        "asymptotic_regime": (
            "finite design",
            "randomization",
            "design optimization",
            "space-filling",
            "balance",
            "robustness",
            "model-free",
            "model uncertainty",
            "continuous optimization",
        ),
    },
    "heteroskedastic_regression_inference": {
        "problem_class": ("heteroskedastic", "sandwich", "hc1", "robust standard", "regression slope"),
        "dgp": ("linear regression", "heteroskedastic", "errors", "covariates"),
        "estimand": ("slope", "coefficient", "beta"),
        "assumptions": ("exogeneity", "iid", "finite fourth moments", "full rank", "heteroskedastic"),
        "asymptotic_regime": ("asymptotic", "wald", "sandwich", "consistency", "validity"),
    },
    "multiple_testing_fdr": {
        "problem_class": ("fdr", "false discovery", "false discoveries", "multiple testing", "benjamini", "hochberg", "knockoff"),
        "dgp": ("independent z-tests", "p-values", "sparse mixture", "null p-values", "reinforcement learning", "markov decision process", "state variables", "state representation"),
        "estimand": ("false discovery rate", "rejection rule", "fdr", "power", "minimal sufficient state", "state-variable selection"),
        "assumptions": ("independent", "valid null p-values", "sparse", "null", "markov", "mdp", "sufficiency", "knockoff"),
        "asymptotic_regime": (
            "finite-sample",
            "asymptotic",
            "large-scale",
            "control",
            "power",
            "controlling false discoveries",
            "sequential knockoff",
            "variable selection",
        ),
    },
    "sequential_anytime_inference": {
        "problem_class": ("anytime", "anytime-valid", "anytime valid", "optional stopping", "e-process", "sequential test", "sequential testing"),
        "dgp": ("sequential", "bernoulli", "monitor", "stopping", "filtration"),
        "estimand": ("type-i error", "rejection rule", "e-process", "evidence"),
        "assumptions": ("iid bernoulli", "null", "martingale", "optional stopping", "filtration"),
        "asymptotic_regime": ("finite-horizon", "nonasymptotic", "anytime", "ville", "optional stopping"),
    },
    "sequential_changepoint_inference": {
        "problem_class": (
            "structural breaks",
            "changepoint",
            "change point",
            "post-detection",
            "post detection",
            "sequential model confidence",
            "model confidence sets",
            "functional time series",
        ),
        "dgp": (
            "locally stationary functional time series",
            "functional time series",
            "partial measurement error",
            "candidate model set",
            "loss or performance process",
            "sequential evaluation",
            "data-dependent stopping time",
        ),
        "estimand": (
            "structural break",
            "changepoint",
            "change point",
            "model confidence set",
            "changepoint confidence set",
            "localization",
        ),
        "assumptions": (
            "locally stationary functional time series",
            "heterogeneous partial measurement error",
            "no presmoothing",
            "no dimension reduction",
            "candidate model set",
            "selection uncertainty",
            "data-dependent stopping time",
            "minimal distributional assumptions",
        ),
        "asymptotic_regime": (
            "sequential",
            "post-detection",
            "post detection",
            "changepoint localization",
            "functional time series",
            "model confidence",
            "finite-horizon",
        ),
    },
    "high_dimensional_pca_inference": {
        "problem_class": ("pca", "principal component", "principal components", "eigenvector", "eigenvalue", "spectrum", "spiked covariance", "fpca"),
        "dgp": ("high-dimensional", "covariance", "spiked", "low-rank", "functional", "elliptical triangular array", "triangular array", "p-dimensional", "shape matrices"),
        "estimand": ("leading eigenvector", "leading-eigenvector", "signal subspace", "signal-subspace", "signal direction", "leading signal direction", "principal component", "pca directions", "eigenvector regimes", "eigenspace"),
        "assumptions": ("eigengap", "spike", "finite fourth moments", "high-dimensional"),
        "asymptotic_regime": ("high-dimensional asymptotics", "p/n", "recovery", "consistency", "asymptotic", "limiting experiments", "limiting distributions", "weak identifiability"),
    },
    "extreme_tail_quantile_inference": {
        "problem_class": ("tail index", "tail-index", "high quantile", "high-quantile", "extreme quantile", "regular variation", "value-at-risk", "pareto", "weissman", "hill"),
        "dgp": ("heavy-tailed", "pareto", "regularly varying", "tail"),
        "estimand": ("tail index", "tail-index", "high quantile", "high-quantile", "value-at-risk", "conditional value-at-risk"),
        "assumptions": ("regular variation", "iid", "intermediate threshold", "second-order", "bivariate tail dependence", "tail dependence", "conditional high quantile", "weak tail conditions"),
        "asymptotic_regime": (
            "asymptotic",
            "consistency",
            "clt",
            "threshold",
            "k/n",
            "weak tail conditions",
            "conditional high quantile",
            "tail dependence",
        ),
    },
}


RESEARCH_ALGORITHM_REGISTRY: dict[str, dict[str, object]] = {
    "oracle_aipw": {
        "summary": "oracle augmented inverse-probability weighted ATE estimator simulation",
        "method": "_oracle_aipw",
        "helpers": ("_sigmoid", "_estimation_metrics"),
        "version": "v1",
        "registry_status": "vetted",
    },
    "split_conformal_poly": {
        "summary": "split conformal interval with polynomial regression nonconformity scores",
        "method": "_split_conformal",
        "helpers": ("_poly_design", "_nonlinear_regression_sample"),
        "version": "v1",
        "registry_status": "vetted",
    },
    "ols_hc1": {
        "summary": "OLS slope estimator with HC1 sandwich standard error simulation",
        "method": "_ols_hc1",
        "helpers": ("_estimation_metrics",),
        "version": "v1",
        "registry_status": "vetted",
    },
    "benjamini_hochberg": {
        "summary": "Benjamini-Hochberg step-up multiple-testing procedure simulation",
        "method": "_benjamini_hochberg",
        "helpers": ("_normal_two_sided_pvalues",),
        "version": "v1",
        "registry_status": "vetted",
    },
    "bernoulli_lr_eprocess": {
        "summary": "likelihood-ratio e-process for anytime-valid Bernoulli testing",
        "method": "_bernoulli_lr_eprocess",
        "helpers": (),
        "version": "v1",
        "registry_status": "vetted",
    },
    "cusum_changepoint_detector": {
        "summary": "CUSUM structural-break localization with post-detection interval diagnostics",
        "method": "_cusum_changepoint_detector",
        "helpers": ("_cusum_changepoint_estimate",),
        "version": "v1",
        "registry_status": "vetted",
    },
    "spiked_pca": {
        "summary": "spiked-covariance PCA leading-eigenvector recovery simulation",
        "method": "_spiked_pca",
        "helpers": (),
        "version": "v1",
        "registry_status": "vetted",
    },
    "latent_simplex_membership": {
        "summary": "simplex-constrained latent membership recovery for grade-of-membership data",
        "method": "_latent_simplex_membership",
        "helpers": ("_project_rows_to_simplex", "_best_permutation_score"),
        "version": "v1",
        "registry_status": "vetted",
    },
    "dimension_association_screening": {
        "summary": "sufficient-dimension association screening for nonlinear/tensor predictor signals",
        "method": "_dimension_association_screening",
        "helpers": ("_orthonormal_basis",),
        "version": "v1",
        "registry_status": "vetted",
    },
    "hill_tail_quantile": {
        "summary": "Hill tail-index and Weissman high-quantile simulation for Pareto tails",
        "method": "_hill_tail_quantile",
        "helpers": ("_estimation_metrics",),
        "version": "v1",
        "registry_status": "vetted",
    },
    "kaplan_meier_fixed_time": {
        "summary": "Kaplan-Meier survival probability inference at a fixed time under independent censoring",
        "method": "_kaplan_meier_fixed_time",
        "helpers": ("_estimation_metrics", "_kaplan_meier_at_time"),
        "version": "v1",
        "registry_status": "vetted",
    },
    "median_of_means_mean": {
        "summary": "median-of-means robust location inference under heavy tails and gross-error contamination",
        "method": "_median_of_means_mean",
        "helpers": ("_estimation_metrics", "_median_of_means"),
        "version": "v1",
        "registry_status": "vetted",
    },
    "dp_gaussian_mean": {
        "summary": "Gaussian-mechanism differentially private clipped-mean simulation",
        "method": "_dp_gaussian_mean",
        "helpers": ("_estimation_metrics",),
        "version": "v1",
        "registry_status": "vetted",
    },
    "sieve_ensemble_regression": {
        "summary": "sieve polynomial regression point-mean inference with sandwich-style linear-smoother SE",
        "method": "_sieve_ensemble_regression",
        "helpers": ("_estimation_metrics", "_sieve_design"),
        "version": "v1",
        "registry_status": "vetted",
    },
    "normal_conjugate_posterior_mean": {
        "summary": "normal-normal conjugate posterior mean and credible interval calibration simulation",
        "method": "_normal_conjugate_posterior_mean",
        "helpers": ("_estimation_metrics",),
        "version": "v1",
        "registry_status": "vetted",
    },
    "measurement_bias_adjusted_ranking": {
        "summary": "bias-adjusted country mean and ranking reliability simulation for assessment measurement bias",
        "method": "_measurement_bias_adjusted_ranking",
        "helpers": ("_estimation_metrics", "_rank_positions"),
        "version": "v1",
        "registry_status": "vetted",
    },
    "neyman_conservative_variance": {
        "summary": "design-based Neyman conservative variance bound for randomized treatment-effect estimation",
        "method": "_neyman_conservative_variance",
        "helpers": ("_estimation_metrics",),
        "version": "v1",
        "registry_status": "vetted",
    },
    "sbm_edge_density_spectral": {
        "summary": "dense two-block stochastic block model edge-density and spectral community simulation",
        "method": "_sbm_edge_density_spectral",
        "helpers": ("_estimation_metrics",),
        "version": "v1",
        "registry_status": "vetted",
    },
    "covariate_balance_maximin_design": {
        "summary": "maximin space-filling design selection plus covariate-balanced rerandomization simulation",
        "method": "_covariate_balance_maximin_design",
        "helpers": ("_min_pairwise_distance",),
        "version": "v1",
        "registry_status": "vetted",
    },
    "metric_graph_kernel_smoother": {
        "summary": "metric-graph kernel smoother for spatial field prediction and graph-supported regression",
        "method": "_metric_graph_kernel_smoother",
        "helpers": ("_path_graph_distances", "_rbf_kernel"),
        "version": "v1",
        "registry_status": "vetted",
    },
    "point_process_intensity_contrast": {
        "summary": "kernel intensity contrast for spatial point-process predictors and superposition diagnostics",
        "method": "_point_process_intensity_contrast",
        "helpers": ("_simulate_inhomogeneous_poisson_1d",),
        "version": "v1",
        "registry_status": "vetted",
    },
}


def load_open_research_questions(path: Path) -> list[OpenResearchQuestion]:
    if path.suffix.lower() in {".md", ".markdown", ".txt"}:
        return _load_text_research_questions(path)
    payload = json.loads(path.read_text(encoding="utf-8"))
    rows = payload["questions"] if isinstance(payload, dict) and "questions" in payload else payload
    questions: list[OpenResearchQuestion] = []
    for row in rows:
        questions.append(
            OpenResearchQuestion(
                id=str(row["id"]),
                title=str(row.get("title", row["id"])),
                description=str(row["description"]),
                tags=tuple(str(tag) for tag in row.get("tags", ())),
            )
        )
    return questions


def _load_text_research_questions(path: Path) -> list[OpenResearchQuestion]:
    text = path.read_text(encoding="utf-8")
    heading_re = re.compile(r"^#{1,3}\s+([A-Za-z0-9_.-]+)\s*:\s*(.+?)\s*$")
    sections: list[tuple[str, str, list[str]]] = []
    current_id: str | None = None
    current_title: str | None = None
    current_lines: list[str] = []
    for raw_line in text.splitlines():
        match = heading_re.match(raw_line.strip())
        if match:
            if current_id and current_title:
                sections.append((current_id, current_title, current_lines))
            current_id = match.group(1)
            current_title = match.group(2).strip()
            current_lines = []
        elif current_id:
            current_lines.append(raw_line)
    if current_id and current_title:
        sections.append((current_id, current_title, current_lines))
    if not sections:
        return [_single_text_question(path, text)]

    questions: list[OpenResearchQuestion] = []
    for question_id, title, lines in sections:
        tags: tuple[str, ...] = ()
        body_lines: list[str] = []
        for line in lines:
            stripped = line.strip()
            if stripped.lower().startswith("tags:"):
                tags = _parse_tags(stripped.split(":", 1)[1])
            else:
                body_lines.append(line)
        description = "\n".join(body_lines).strip()
        if not description:
            description = title
        questions.append(
            OpenResearchQuestion(
                id=_safe_question_id(question_id),
                title=title,
                description=description,
                tags=tags,
            )
        )
    return questions


def _single_text_question(path: Path, text: str) -> OpenResearchQuestion:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if lines and lines[0].startswith("#"):
        title = lines[0].lstrip("#").strip()
        description = "\n".join(lines[1:]).strip() or title
    elif lines:
        title = lines[0]
        description = "\n".join(lines[1:]).strip() or title
    else:
        title = path.stem.replace("_", " ").title()
        description = title
    return OpenResearchQuestion(
        id=_safe_question_id(path.stem),
        title=title,
        description=description,
        tags=(),
    )


def _parse_tags(raw: str) -> tuple[str, ...]:
    return tuple(
        tag.strip().lower().replace(" ", "_")
        for tag in raw.split(",")
        if tag.strip()
    )


def _safe_question_id(raw: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9_.-]+", "_", raw.strip())
    slug = slug.strip("_.-")
    return slug or "open_research_question"


class ProblemFormalizer:
    """Normalize open statistical prose into a structured research problem.

    This is intentionally deterministic in v0. LLM extraction can be added
    later, but the benchmark should remain reproducible and auditable.
    """

    def formalize(self, question: OpenResearchQuestion) -> ResearchProblemSpec:
        full_text = f"{question.title} {question.description} {' '.join(question.tags)}"
        body_text = f"{question.title} {question.description}"
        problem = self._formalize_raw(question)
        return replace(
            problem,
            extraction_evidence=_problem_extraction_evidence(
                problem,
                source_text=body_text,
                full_text=full_text,
            ),
        )

    def _formalize_raw(self, question: OpenResearchQuestion) -> ResearchProblemSpec:
        text = f"{question.title} {question.description} {' '.join(question.tags)}".lower()
        body_text = f"{question.title} {question.description}".lower()
        if _matches(
            body_text,
            words=("design_based_variance",),
            phrases=(
                "optimized variance estimation",
                "conservative variance",
                "least conservative",
                "estimable variance bound",
                "design-based validity",
                "complex experimental designs",
                "variance estimation under interference",
            ),
        ):
            return ResearchProblemSpec(
                question_id=question.id,
                problem_class="design_based_variance_inference",
                dgp=(
                    "Finite population potential outcomes under a completely randomized treatment assignment "
                    "in the v0 simulator."
                ),
                estimand="Finite-population average treatment effect and its randomization variance bound.",
                assumptions=(
                    "finite population potential outcomes are fixed before assignment",
                    "known complete randomization design",
                    "SUTVA baseline in the v0 simulator",
                    "heterogeneous unit-level treatment effects make exact variance unidentified from one assignment",
                ),
                asymptotic_regime=(
                    "N -> infinity under design-based randomization; Neyman variance is conservative, "
                    "while optimized bounds require additional design/structure constraints."
                ),
                diagnostics=("bias", "rmse", "coverage_95", "se_calibration", "conservativeness_ratio"),
                stress_tests=("stronger treatment-effect heterogeneity", "unbalanced assignment", "cluster interference"),
            )
        if _matches(
            body_text,
            words=(),
            phrases=(
                "space-filling designs",
                "space filling designs",
                "maximin space-filling",
                "maximin distance criterion",
                "oracle arrays",
                "hamming-distance array",
                "order-of-addition designs",
                "order of addition designs",
                "stratum order-of-addition",
                "stratum orthogonality",
                "gaussianized design optimization",
                "covariate balance objective",
                "optimize covariate balance",
                "gaussianized assignments",
                "continuous optimization over covariance matrices",
            ),
        ):
            return ResearchProblemSpec(
                question_id=question.id,
                problem_class="experimental_design_optimization",
                dgp=(
                    "Finite candidate design points or pre-treatment covariate profiles before "
                    "an experiment; the v0 simulator combines maximin subset selection with "
                    "covariate-balanced rerandomization."
                ),
                estimand=(
                    "A design/procedure optimizing space-filling distance and covariate balance "
                    "under a limited run or assignment budget."
                ),
                assumptions=(
                    "finite candidate design space",
                    "limited experimental run budget",
                    "pre-treatment covariates observed before assignment",
                    "symmetric candidate assignments preserve randomization validity in the baseline",
                    "model-free order/addition and oracle-array optimality remain formal gaps",
                ),
                asymptotic_regime=(
                    "finite-design optimization in the v0 simulator; frontier targets include "
                    "maximin design guarantees, stratum orthogonality, and Gaussianized "
                    "covariate-balance randomization theory."
                ),
                diagnostics=(
                    "space_filling_ratio",
                    "balance_improvement",
                    "mean_standardized_imbalance",
                    "assignment_acceptance_rate",
                ),
                stress_tests=("smaller run budget", "stronger covariate correlation", "near-tied balance criteria"),
            )
        if _matches(
            body_text,
            words=("causal", "ate", "cate", "unconfounded", "aipw", "tmle"),
            phrases=(
                "average treatment effect",
                "treatment effect",
                "treatment-effect",
                "principal stratification",
                "unmeasured confounding",
                "sensitivity analysis",
            ),
        ):
            return ResearchProblemSpec(
                question_id=question.id,
                problem_class="semiparametric_causal_ate",
                dgp="Observed data O=(X,A,Y); A is binary treatment; Y follows potential-outcome model.",
                estimand="Average treatment effect psi = E[Y(1) - Y(0)].",
                assumptions=(
                    "consistency",
                    "conditional exchangeability",
                    "positivity",
                    "iid observations",
                    "regular nuisance estimators or oracle nuisance functions in the v0 simulator",
                ),
                asymptotic_regime="n iid observations with nuisance error controlled; sqrt(n) target for AIPW.",
                diagnostics=("bias", "relative_bias", "rmse", "coverage_95", "se_calibration"),
                stress_tests=("positivity stress", "nonlinear outcome surface", "propensity misspecification"),
            )
        if _matches(
            body_text,
            words=("heteroskedastic", "sandwich", "hc1", "robust_se"),
            phrases=("robust standard",),
        ):
            return ResearchProblemSpec(
                question_id=question.id,
                problem_class="heteroskedastic_regression_inference",
                dgp="Linear regression with conditionally heteroskedastic errors.",
                estimand="Slope coefficient beta in E[Y|X] = alpha + beta X.",
                assumptions=("iid observations", "exogeneity E[eps|X]=0", "finite fourth moments", "full rank design"),
                asymptotic_regime="n -> infinity with fixed parameter dimension; sandwich covariance target.",
                diagnostics=("bias", "rmse", "coverage_95", "se_calibration"),
                stress_tests=("variance increasing in |X|", "leverage stress", "normal-error baseline"),
            )
        if _matches(
            body_text,
            words=("pareto", "weissman"),
            phrases=(
                "tail index",
                "high quantile",
                "high quantiles",
                "extreme quantile",
                "extreme quantiles",
                "regular variation",
                "value-at-risk",
                "value at risk",
                "conditional value-at-risk",
            ),
        ):
            return ResearchProblemSpec(
                question_id=question.id,
                problem_class="extreme_tail_quantile_inference",
                dgp="iid heavy-tailed observations with Pareto or regularly varying upper tail in the v0 simulator.",
                estimand="Tail index gamma = 1/alpha and an extreme upper quantile q_p for p close to one.",
                assumptions=(
                    "iid observations",
                    "regularly varying upper tail",
                    "intermediate threshold k with k -> infinity and k/n -> 0",
                    "second-order tail bias controlled in the target theorem",
                ),
                asymptotic_regime="n -> infinity, k -> infinity, k/n -> 0; Hill CLT and Weissman quantile consistency targets.",
                diagnostics=("tail_index_bias", "tail_index_rmse", "quantile_relative_bias", "quantile_coverage_95"),
                stress_tests=("smaller threshold k", "heavier tail", "non-Pareto second-order bias"),
            )
        if _matches(
            body_text,
            words=("robust_mean",),
            phrases=(
                "sub-gaussian mean",
                "subgaussian mean",
                "robust mean",
                "star-shaped constraint",
                "star shaped constraint",
                "mean estimation under",
                "gross-error contamination",
                "heavy-tailed mean",
            ),
        ):
            return ResearchProblemSpec(
                question_id=question.id,
                problem_class="robust_mean_inference",
                dgp=(
                    "iid observations from a location model with heavy-tailed noise and a small "
                    "fraction of gross-error contamination in the v0 simulator."
                ),
                estimand="Mean/location parameter theta of the uncontaminated distribution.",
                assumptions=(
                    "iid uncontaminated observations with finite variance",
                    "symmetric heavy-tailed baseline in the v0 simulator",
                    "epsilon-fraction gross-error contamination",
                    "known block count for the median-of-means procedure",
                ),
                asymptotic_regime=(
                    "n -> infinity with contamination fraction controlled; target is a robust "
                    "sub-Gaussian deviation bound and minimax-rate roadmap under stronger assumptions."
                ),
                diagnostics=("bias", "relative_bias", "rmse", "coverage_95", "se_calibration", "contamination_fraction"),
                stress_tests=("larger contamination fraction", "heavier tails", "one-sided adversarial outliers"),
            )
        if _matches(
            body_text,
            words=(),
            phrases=(
                "differential privacy",
                "differentially private",
                "local differential privacy",
                "privacy composition",
                "private learning",
                "privacy-loss",
                "privacy loss",
                "edgeworth accountant",
                "general loss functions",
                "private mechanisms",
            ),
        ):
            return ResearchProblemSpec(
                question_id=question.id,
                problem_class="differential_privacy_learning",
                dgp=(
                    "iid bounded or clipped observations released through a calibrated Gaussian "
                    "mechanism in the v0 simulator; frontier variants include composed privacy-loss "
                    "random variables and local private releases for general losses."
                ),
                estimand=(
                    "A statistical functional, represented in v0 by a population mean, together "
                    "with epsilon-delta privacy accounting and private inference diagnostics."
                ),
                assumptions=(
                    "iid source sample before privatization",
                    "known clipping bound or bounded sensitivity",
                    "Gaussian mechanism noise calibrated to epsilon and delta",
                    "privacy composition or local privacy theory is treated as a formal gap",
                    "general-loss and Edgeworth-accountant theory require additional library work",
                ),
                asymptotic_regime=(
                    "n -> infinity with fixed privacy parameters in the simulator; frontier theorem "
                    "targets include composition error control and private learning excess-risk rates."
                ),
                diagnostics=(
                    "bias",
                    "relative_bias",
                    "rmse",
                    "coverage_95",
                    "se_calibration",
                    "privacy_noise_sd",
                    "clipping_fraction",
                ),
                stress_tests=("smaller epsilon", "larger clipping bias", "many composed private releases"),
            )
        if _matches(
            body_text,
            words=(),
            phrases=(
                "generalized nonparametric",
                "deep neural network estimators",
                "deep neural networks in generalized nonparametric",
                "dnn estimator",
                "deep p-spline",
                "penalized spline",
                "neural-network architecture selection",
                "basis-expansion analogy",
                "knot selection",
            ),
        ) and not _matches(
            body_text,
            words=(),
            phrases=("metric graphs", "signed networks", "active learning", "preference learning", "transfer learning"),
        ):
            return ResearchProblemSpec(
                question_id=question.id,
                problem_class="nonparametric_regression_inference",
                dgp=(
                    "Nonparametric regression observations (X,Y) with a smooth conditional mean; "
                    "the v0 simulator uses a polynomial-sieve surrogate for DNN/P-spline estimators."
                ),
                estimand=(
                    "Subject-specific conditional mean m(x0)=E[Y|X=x0] and its pointwise inference interval."
                ),
                assumptions=(
                    "iid regression sample in the v0 simulator",
                    "smooth regression function approximable by a finite sieve",
                    "finite conditional noise variance",
                    "sieve dimension/tuning is selected externally in v0",
                    "DNN approximation and adaptive tuning theory remain formal gaps",
                ),
                asymptotic_regime=(
                    "n -> infinity with sieve dimension growing slowly; frontier targets include "
                    "approximation-estimation error bounds, ensemble/subsampling inference, and "
                    "penalized spline tuning guarantees."
                ),
                diagnostics=("bias", "relative_bias", "rmse", "coverage_95", "se_calibration", "sieve_dimension"),
                stress_tests=("higher curvature regression surface", "smaller sample size", "heavier-tailed noise"),
            )
        if _matches(
            body_text,
            words=(),
            phrases=(
                "grade-of-membership",
                "grade of membership",
                "mixed-membership simplex",
                "three-way quasi-tensor",
                "quasi-tensor",
                "polytomous items",
                "locally dependent categorical data",
                "sufficient dimension association",
                "sufficient dimension reduction",
                "conditional association target",
                "without specifying a sparse linear regression",
                "tensor-valued predictors",
                "tensor valued predictors",
                "generalized multilinear models",
                "multilinear low-dimensional reductions",
                "quadratic exponential family inverse model",
            ),
        ):
            return ResearchProblemSpec(
                question_id=question.id,
                problem_class="high_dimensional_latent_structure_inference",
                dgp=(
                    "High-dimensional observations carry latent low-dimensional structure: mixed-membership "
                    "simplex scores for many categorical/polytomous items, or nonlinear/tensor predictors "
                    "whose response depends on a small sufficient subspace. The v0 simulators use a noisy "
                    "simplex factor model and a nonlinear sparse sufficient-dimension screening surrogate."
                ),
                estimand=(
                    "Latent membership weights, active sufficient-dimension coordinates, and low-dimensional "
                    "reduction directions supporting variable selection and model-parameter inference."
                ),
                assumptions=(
                    "latent membership weights lie in a probability simplex in the grade-of-membership surrogate",
                    "item/profile matrices are identifiable up to label permutation in the controlled baseline",
                    "the response depends on a sparse low-dimensional predictor index in the screening surrogate",
                    "local dependence, tensor inverse models, and high-dimensional selection theory remain formal gaps",
                ),
                asymptotic_regime=(
                    "n,p and tensor dimensions may grow; frontier targets include membership estimation rates, "
                    "selection consistency for sufficient dimension association, and multilinear/tensor SDR "
                    "asymptotic guarantees."
                ),
                diagnostics=("rmse", "coverage_95", "selection_accuracy"),
                stress_tests=("weaker latent separation", "more nuisance predictors", "local dependence contamination"),
            )
        if _matches(
            body_text,
            words=(),
            phrases=(
                "mixed-membership network",
                "mixed-membership networks",
                "degree-corrected mixed-membership",
                "node mixing probabilities",
                "signed networks",
                "signed network",
                "dynamic networks",
                "autoregressive networks",
                "dependent edges",
                "network vector autoregression",
                "network vector autoregressions",
                "time-varying network",
                "binary graphical models",
                "dependence graph density",
                "graph connectivity parameter",
                "binary interacting chains",
            ),
        ) and not _matches(
            body_text,
            words=(),
            phrases=(
                "graph-structured predictors",
                "graph-split",
                "graph split",
                "metric graph",
                "metric graphs",
                "graph-dependent observations",
                "graph neighborhoods",
                "local dependence conditions",
                "smooth graph functional",
                "spatial",
                "point process",
                "matern",
                "manifold",
            ),
        ):
            return ResearchProblemSpec(
                question_id=question.id,
                problem_class="network_graph_inference",
                dgp=(
                    "Graph-valued observations represented in the v0 simulator by an undirected "
                    "two-block stochastic block model; frontier variants include mixed-membership, "
                    "signed, dynamic, and dependent-edge network models."
                ),
                estimand=(
                    "Population edge density and latent community signal structure; frontier targets "
                    "include node mixing probabilities, signed-network balance functionals, dynamic "
                    "network coefficients, and dependence-graph connectivity."
                ),
                assumptions=(
                    "conditionally independent undirected edges in the v0 stochastic block model",
                    "two balanced latent communities with bounded within/between edge probabilities",
                    "dense enough graph for spectral recovery in the simulator",
                    "mixed membership, signed ties, temporal dependence, and binary-interaction dependence are formal gaps",
                ),
                asymptotic_regime=(
                    "number of nodes n -> infinity; v0 checks edge-density Wald inference and "
                    "spectral community recovery, while graph CLTs and dynamic-network asymptotics "
                    "remain theorem-development targets."
                ),
                diagnostics=(
                    "edge_density_bias",
                    "edge_density_rmse",
                    "coverage_95",
                    "se_calibration",
                    "community_accuracy",
                ),
                stress_tests=("weak community separation", "sparser graph", "degree heterogeneity"),
            )
        if _matches(
            body_text,
            words=(),
            phrases=(
                "anisotropic gaussian fields",
                "gaussian random fields",
                "gaussian whittle-matern",
                "whittle-matern fields",
                "whittle matern fields",
                "metric graphs",
                "metric graph",
                "graph-supported observations",
                "functional spaces on metric graphs",
                "generalized point process",
                "point process additive",
                "point-process additive",
                "point-process predictors",
                "random counting measures",
                "palm distributions",
                "palm distribution",
                "superposed point processes",
                "shot-noise cox processes",
                "manifold",
                "spde priors",
                "penalized complexity priors",
            ),
        ):
            return ResearchProblemSpec(
                question_id=question.id,
                problem_class="geometric_spatial_point_process_inference",
                dgp=(
                    "Data live on a geometric domain: a compact metric graph, spatial field, "
                    "manifold-like support, or point-process observation space. The v0 simulator "
                    "uses a path metric graph for Gaussian field/regression targets and a one-dimensional "
                    "inhomogeneous Poisson superposition for point-process diagnostics."
                ),
                estimand=(
                    "A spatial/geometric functional such as a graph-supported regression mean, "
                    "field prediction target, point-process intensity contrast, or Palm/superposition "
                    "summary supporting downstream inference."
                ),
                assumptions=(
                    "observations are tied to a known geometric support in the v0 simulator",
                    "metric graph distances are known for smoothing and prediction",
                    "point-process superposition components are independent in the controlled baseline",
                    "SPDE Whittle-Matern, manifold delta-method, Sobolev graph, and Palm theory remain formal gaps",
                ),
                asymptotic_regime=(
                    "in-fill or increasing-domain sampling on geometric supports; frontier targets "
                    "include likelihood consistency, graph Sobolev convergence rates, point-process "
                    "selection consistency, and Palm-mixture identities."
                ),
                diagnostics=(
                    "rmse",
                    "coverage_95",
                    "se_calibration",
                ),
                stress_tests=("shorter correlation length", "sparser graph observations", "inhomogeneous intensity spike"),
            )
        if _matches(
            body_text,
            words=(),
            phrases=(
                "predictive distributions into informative priors",
                "predictive distribution from one analysis",
                "predictive distributions from one analysis",
                "translated into informative priors",
                "prior elicitation through prediction",
                "preserves predictive uncertainty",
            ),
        ):
            return ResearchProblemSpec(
                question_id=question.id,
                problem_class="bayesian_posterior_calibration",
                dgp=(
                    "A historical or external predictive distribution is translated into a prior "
                    "for a subsequent normal-likelihood mean model in the v0 simulator."
                ),
                estimand=(
                    "Posterior mean and posterior credible interval for the population mean theta, "
                    "with calibration against repeated-sampling coverage."
                ),
                assumptions=(
                    "external predictive distribution supplies a prior mean and variance",
                    "subsequent observations are conditionally iid normal given theta in the v0 simulator",
                    "known observation variance for the conjugate baseline",
                    "prior transport/coherence is treated as a formal theorem gap",
                    "frontier nonconjugate posterior calibration requires additional library work",
                ),
                asymptotic_regime=(
                    "n -> infinity with a fixed transported prior in the simulator; frontier targets "
                    "include prior-predictive coherence, posterior concentration, and credible-region "
                    "calibration under predictive-prior translation."
                ),
                diagnostics=(
                    "bias",
                    "relative_bias",
                    "rmse",
                    "coverage_95",
                    "se_calibration",
                    "posterior_sd",
                    "prior_influence",
                ),
                stress_tests=("miscentered predictive prior", "overconfident prior", "small subsequent sample"),
            )
        if _matches(
            body_text,
            words=(),
            phrases=(
                "country rankings from educational assessments",
                "educational assessments remain reliable",
                "item-response measurements contain cultural or linguistic bias",
                "measurement bias across countries/items",
                "measurement noninvariance",
                "bias-adjusted ranking",
            ),
        ):
            return ResearchProblemSpec(
                question_id=question.id,
                problem_class="measurement_bias_ranking_inference",
                dgp=(
                    "Large-scale assessment scores indexed by country and item, with latent country "
                    "ability, item difficulty, and cultural/linguistic measurement-bias terms in the v0 simulator."
                ),
                estimand=(
                    "Bias-adjusted country ability means and the induced country ranking with reliability diagnostics."
                ),
                assumptions=(
                    "students/items are sampled independently within country in the v0 simulator",
                    "item difficulty and cultural/linguistic bias terms are known or calibrated before ranking",
                    "measurement noninvariance is additive in the controlled baseline",
                    "bias-model estimation and IRT likelihood theory remain formal gaps",
                    "ranking reliability is evaluated by simulation rather than fully proved in Lean",
                ),
                asymptotic_regime=(
                    "large numbers of students and items per country; target theory is consistency and "
                    "uncertainty calibration for bias-adjusted rankings under measurement noninvariance."
                ),
                diagnostics=(
                    "bias",
                    "rmse",
                    "coverage_95",
                    "se_calibration",
                    "rank_top1_accuracy",
                    "rank_correlation",
                    "mean_abs_rank_error",
                ),
                stress_tests=("stronger measurement bias", "fewer items", "near-tied country abilities"),
            )
        if _matches(
            body_text,
            words=("fdr", "benjamini", "hochberg", "bh", "qvalue", "qvalues"),
            phrases=("false discovery", "false discoveries", "multiple testing", "multiple hypotheses"),
        ):
            return ResearchProblemSpec(
                question_id=question.id,
                problem_class="multiple_testing_fdr",
                dgp="Many independent z-tests with a sparse non-null mixture and two-sided p-values.",
                estimand="A rejection set controlling false discovery rate at target level q while retaining power.",
                assumptions=("independent p-values under true nulls", "valid null p-values", "sparse alternative mixture"),
                asymptotic_regime="m hypotheses with fixed or sparse non-null fraction; finite-sample FDR target for BH under independence.",
                diagnostics=("empirical_fdr", "power", "rejection_rate", "false_discovery_proportion"),
                stress_tests=("weaker effects", "denser alternatives", "correlated null statistics"),
            )
        if _matches(
            body_text,
            words=("conformal", "exchangeability"),
            phrases=("prediction interval", "distribution-free marginal coverage"),
        ):
            return ResearchProblemSpec(
                question_id=question.id,
                problem_class="distribution_free_conformal_prediction",
                dgp="Exchangeable regression data (X,Y), nonlinear conditional mean, homoskedastic noise in v0.",
                estimand="Marginal prediction set C(X_new) satisfying P(Y_new in C(X_new)) >= 1-alpha.",
                assumptions=("exchangeability", "split calibration independence", "finite calibration sample"),
                asymptotic_regime="finite-sample marginal coverage; report empirical coverage across test draws.",
                diagnostics=("coverage_95", "average_width", "miscoverage", "rmse_center"),
                stress_tests=("nonlinear regression", "small calibration set", "heavy-tailed residuals"),
            )
        if _matches(
            body_text,
            words=("survival", "hazard", "kaplan", "meier", "nelson", "aalen"),
            phrases=(
                "right-censored",
                "right censored",
                "time-to-event",
                "time to event",
                "censored survival",
                "conditional hazard",
                "cox proportional",
            ),
        ):
            return ResearchProblemSpec(
                question_id=question.id,
                problem_class="right_censored_survival_inference",
                dgp="Observed time Y=min(T,C) with event indicator Delta=1{T<=C}; event and censoring times are independent in the v0 simulator.",
                estimand="Survival probability S(t0)=P(T>t0) or cumulative hazard Lambda(t0) at a fixed time point.",
                assumptions=(
                    "iid time-to-event observations",
                    "independent right censoring",
                    "noninformative censoring with positive at-risk probability near t0",
                    "continuous event-time distribution in the v0 simulator",
                ),
                asymptotic_regime="n -> infinity at fixed t0; Kaplan-Meier/Nelson-Aalen consistency and Greenwood-type asymptotic normality targets.",
                diagnostics=("bias", "relative_bias", "rmse", "coverage_95", "se_calibration", "censoring_fraction"),
                stress_tests=("heavier censoring", "later target time", "nonconstant hazard baseline"),
            )
        if _matches(
            body_text,
            words=("anytime", "evalue", "evalues", "e-process", "eprocess"),
            phrases=("optional stopping", "anytime-valid", "anytime valid", "sequential testing", "e-process"),
        ):
            return ResearchProblemSpec(
                question_id=question.id,
                problem_class="sequential_anytime_inference",
                dgp="Sequential Bernoulli observations monitored over time with optional stopping.",
                estimand="A sequential rejection rule for H0: p = 0.5 with anytime-valid type-I error control.",
                assumptions=("iid Bernoulli observations", "null success probability p0=0.5", "nonnegative test-martingale/e-process under the null"),
                asymptotic_regime="finite-horizon optional stopping in simulation; Ville-type anytime control as the theorem target.",
                diagnostics=("type1_error", "power", "mean_stop_time", "optional_stopping_rejection_rate"),
                stress_tests=("null optional stopping", "weaker alternatives", "longer monitoring horizon"),
            )
        if _matches(
            body_text,
            words=(),
            phrases=(
                "structural changes",
                "structural breaks",
                "changepoint",
                "change point",
                "post-detection inference",
                "post detection inference",
                "sequential changepoint",
                "sequential detector",
                "sequential model confidence sets",
                "model confidence sets",
                "locally stationary functional time series",
                "functional time series",
                "partial measurement error",
                "data-dependent stopping time",
            ),
        ):
            return ResearchProblemSpec(
                question_id=question.id,
                problem_class="sequential_changepoint_inference",
                dgp=(
                    "Sequential observations from a discretized functional time series with one mean "
                    "shift and partial measurement error in the v0 simulator; model-confidence-set "
                    "questions are represented by a sequential loss process surrogate."
                ),
                estimand=(
                    "The structural break/changepoint location and a post-detection confidence set "
                    "for the declared changepoint or selected model set."
                ),
                assumptions=(
                    "locally stationary functional time-series baseline before/after a single break",
                    "heterogeneous partial measurement error on discretized trajectories",
                    "no presmoothing or dimension reduction in the benchmark statement",
                    "data-dependent stopping/selection is treated as a formal theorem gap",
                    "minimal-distribution post-detection guarantees require new library work",
                ),
                asymptotic_regime=(
                    "finite-horizon sequential monitoring in the v0 simulator; frontier targets "
                    "include functional CUSUM limit theory, post-detection coverage, and sequential "
                    "model-confidence-set validity under data-dependent stopping."
                ),
                diagnostics=(
                    "detection_rate",
                    "mean_absolute_localization_error",
                    "coverage_95",
                    "false_alarm_rate",
                    "mean_detection_delay",
                ),
                stress_tests=("smaller mean shift", "more partial measurement error", "post-detection stopping bias"),
            )
        if _matches(
            body_text,
            words=(
                "pca",
                "eigenvector",
                "eigengap",
                "principal",
                "spectrum",
                "spectrum-aware",
                "debiasing",
                "fpca",
            ),
            phrases=(
                "principal component",
                "principal components",
                "functional pca",
                "spiked covariance",
                "weak identifiability",
                "leading eigen",
                "low-rank",
                "low rank",
            ),
        ) and not _matches(
            body_text,
            words=("extremes", "extreme", "extremal", "heavytail", "heavytails"),
            phrases=("tail-dependence", "tail dependence", "extreme-value", "extreme value"),
        ):
            return ResearchProblemSpec(
                question_id=question.id,
                problem_class="high_dimensional_pca_inference",
                dgp="High-dimensional observations from a spiked covariance model with a low-rank signal direction.",
                estimand="The leading population eigenvector or low-dimensional signal subspace.",
                assumptions=(
                    "iid high-dimensional observations",
                    "population covariance has a separated leading spike",
                    "p/n is non-negligible but bounded in the v0 simulator",
                    "finite fourth moments or Gaussian baseline for simulation",
                ),
                asymptotic_regime="n,p -> infinity with p/n bounded; eigengap controls eigenvector recovery.",
                diagnostics=("alignment", "angle_error", "subspace_error", "explained_variance", "eigenvalue_bias"),
                stress_tests=("weak eigengap", "larger p/n ratio", "heavy-tailed coordinates"),
            )
        return ResearchProblemSpec(
            question_id=question.id,
            problem_class="unsupported_frontier_question",
            dgp="Not extracted by deterministic v0 formalizer.",
            estimand="Not extracted by deterministic v0 formalizer.",
            assumptions=("manual review required",),
            asymptotic_regime="manual review required",
            diagnostics=("manual_review",),
            stress_tests=("manual_review",),
        )


class TheoryPlanner:
    def plan(self, problem: ResearchProblemSpec) -> tuple[list[CandidateProcedure], list[TheoremGoal]]:
        if problem.problem_class == "semiparametric_causal_ate":
            goals = [
                TheoremGoal(
                    id="causal_identification",
                    title="ATE identification under exchangeability",
                    informal_statement="psi = E[E[Y|A=1,X] - E[Y|A=0,X]] under consistency, exchangeability, and positivity.",
                    proof_strategy="Formalize conditional expectation and potential-outcome assumptions; reduce by iterated expectation.",
                    status="FORMAL_GAP",
                    required_primitives=(
                        "conditional_expectation",
                        "potential_outcome_consistency",
                        "conditional_exchangeability",
                        "positivity",
                        "iterated_expectation",
                    ),
                ),
                TheoremGoal(
                    id="aipw_double_robustness",
                    title="AIPW double robustness",
                    informal_statement="The AIPW score has mean psi if either propensity or outcome nuisance is correct.",
                    proof_strategy="Expand the estimating equation and cancel conditional mean residuals.",
                    status="FORMAL_GAP",
                    required_primitives=(
                        "aipw_score_definition",
                        "conditional_mean_residual_zero",
                        "propensity_weight_identity",
                        "nuisance_correctness_cases",
                        "integrability_of_score_terms",
                    ),
                    proof_obligations=("aipw_score_expectation_decompose",),
                ),
                TheoremGoal(
                    id="aipw_asymptotic_normality",
                    title="AIPW asymptotic normality",
                    informal_statement="sqrt(n)(psi_hat-psi) is asymptotically normal under nuisance rate conditions.",
                    proof_strategy="Empirical-process remainder bound plus CLT for the influence function.",
                    status="FORMAL_GAP",
                    required_primitives=(
                        "iid_empirical_mean_clt",
                        "influence_function_variance",
                        "empirical_process_remainder_bound",
                        "nuisance_rate_product_condition",
                        "slutsky_theorem",
                    ),
                ),
            ]
            procedures = [
                CandidateProcedure(
                    id="oracle_aipw_ate",
                    name="Oracle AIPW estimator",
                    role="estimator",
                    formula=(
                        "psi_hat = n^{-1} sum_i [m1(X_i)-m0(X_i) + "
                        "A_i/e(X_i)(Y_i-m1(X_i)) - (1-A_i)/(1-e(X_i))(Y_i-m0(X_i))]"
                    ),
                    informal_derivation=(
                        "Start from the efficient influence function for the nonparametric ATE model. "
                        "The augmentation terms have conditional mean zero when nuisances are correct, "
                        "so the sample mean targets psi and its plug-in variance gives Wald intervals."
                    ),
                    algorithm="oracle_aipw",
                    theorem_goals=tuple(goal.id for goal in goals),
                    simulation_design="Nonlinear outcome and logistic propensity with known oracle nuisances.",
                    limitations=(
                        "v0 simulator uses oracle nuisance functions, not learned nuisance estimates",
                        "formal proof stops at Mathlib-backed expectation/probability subclaims",
                    ),
                )
            ]
            return procedures, goals
        if problem.problem_class == "distribution_free_conformal_prediction":
            goals = [
                TheoremGoal(
                    id="split_conformal_finite_sample_coverage",
                    title="Split conformal finite-sample coverage",
                    informal_statement="Under exchangeability, split conformal prediction achieves marginal coverage at least 1-alpha.",
                    proof_strategy="Formalize ranks of exchangeable nonconformity scores and order-statistic quantile rule.",
                    status="FORMAL_GAP",
                    required_primitives=(
                        "exchangeable_scores",
                        "rank_uniformity",
                        "order_statistic_quantile_rule",
                        "finite_sample_coverage_counting",
                    ),
                    proof_obligations=(
                        "prob_measure_univ",
                        "prob_compl",
                        "coverage_lower_bound_of_complement_error",
                        "event_probability_mono",
                        "finite_union_bound",
                        "finite_union_budget_control",
                        "simultaneous_coverage_of_union_error_bound",
                    ),
                )
            ]
            procedures = [
                CandidateProcedure(
                    id="split_conformal_poly",
                    name="Split conformal interval with polynomial regression score",
                    role="prediction_procedure",
                    formula="C(x) = [f_hat(x)-q_cal, f_hat(x)+q_cal], where q_cal is the conformal residual quantile.",
                    informal_derivation=(
                        "Fit a regression function on the training split, compute absolute residual scores "
                        "on the calibration split, and use the exchangeable rank argument to choose the quantile."
                    ),
                    algorithm="split_conformal_poly",
                    theorem_goals=tuple(goal.id for goal in goals),
                    simulation_design="Train/calibrate/test nonlinear regression data and measure marginal coverage.",
                    limitations=("coverage is marginal, not conditional", "finite-sample proof remains a formal gap"),
                )
            ]
            return procedures, goals
        if problem.problem_class == "right_censored_survival_inference":
            goals = [
                TheoremGoal(
                    id="independent_censoring_survival_identification",
                    title="Survival target identification under independent censoring",
                    informal_statement=(
                        "Under independent right censoring and positive at-risk probability, "
                        "the event-time survival curve S(t)=P(T>t) is identified from observed "
                        "times and event indicators."
                    ),
                    proof_strategy=(
                        "Formalize the observed counting process, at-risk process, censoring "
                        "independence, and the product-integral representation of survival."
                    ),
                    status="FORMAL_GAP",
                    required_primitives=(
                        "right_censoring_observed_data",
                        "at_risk_counting_process",
                        "independent_censoring",
                        "product_integral_survival",
                        "hazard_survival_identification",
                    ),
                    proof_obligations=("event_indicator_expectation", "prob_compl"),
                ),
                TheoremGoal(
                    id="kaplan_meier_fixed_time_asymptotic_normality",
                    title="Kaplan-Meier fixed-time asymptotic normality",
                    informal_statement=(
                        "At a fixed time t0, the Kaplan-Meier estimator is consistent and "
                        "sqrt(n)(S_hat(t0)-S(t0)) is asymptotically normal with Greenwood variance."
                    ),
                    proof_strategy=(
                        "Use Nelson-Aalen martingale decomposition, product-limit delta method, "
                        "and Greenwood variance consistency."
                    ),
                    status="FORMAL_GAP",
                    required_primitives=(
                        "kaplan_meier_product_limit",
                        "nelson_aalen_martingale_decomposition",
                        "survival_martingale_clt",
                        "product_limit_delta_method",
                        "greenwood_variance_consistency",
                    ),
                ),
            ]
            procedures = [
                CandidateProcedure(
                    id="kaplan_meier_survival_t0",
                    name="Kaplan-Meier fixed-time survival estimator",
                    role="estimator",
                    formula=(
                        "S_hat(t0)=prod_{Y_(j)<=t0, Delta_(j)=1} (1-d_j/r_j), "
                        "with Greenwood SE S_hat(t0)*sqrt(sum d_j/(r_j(r_j-d_j)))."
                    ),
                    informal_derivation=(
                        "Right censoring hides some event times but preserves the event hazard among "
                        "subjects still at risk under independent censoring. Multiplying one-step "
                        "conditional survival estimates yields the Kaplan-Meier product-limit estimator; "
                        "Greenwood's formula estimates fixed-time sampling variability."
                    ),
                    algorithm="kaplan_meier_fixed_time",
                    theorem_goals=tuple(goal.id for goal in goals),
                    simulation_design=(
                        "Simulate independent exponential event and censoring times, estimate S(t0), "
                        "and evaluate bias, RMSE, Greenwood SE calibration, coverage, and censoring fraction."
                    ),
                    limitations=(
                        "v0 simulator uses independent censoring and a fixed-time target, not DNN hazard learning",
                        "martingale/product-integral survival theory remains a formal gap",
                    ),
                )
            ]
            return procedures, goals
        if problem.problem_class == "robust_mean_inference":
            goals = [
                TheoremGoal(
                    id="median_of_means_subgaussian_deviation",
                    title="Median-of-means robust sub-Gaussian deviation bound",
                    informal_statement=(
                        "For independent finite-variance observations, the median-of-means estimator "
                        "has sub-Gaussian-type deviation up to constants under an appropriate block rule."
                    ),
                    proof_strategy=(
                        "Formalize block means, use Chebyshev/Markov bounds for block failure "
                        "probability, and amplify by a binomial median argument."
                    ),
                    status="FORMAL_GAP",
                    required_primitives=(
                        "block_mean_definition",
                        "chebyshev_block_failure_bound",
                        "independent_blocks",
                        "binomial_median_tail_bound",
                        "median_of_means_deviation",
                    ),
                    proof_obligations=(
                        "finite_sample_mean_unbiased",
                        "finite_sample_mean_variance_indep",
                        "finite_sample_mean_chebyshev_indep",
                        "block_estimator_chebyshev_bound",
                        "estimator_error_chebyshev",
                        "markov_inequality",
                    ),
                ),
                TheoremGoal(
                    id="robust_mean_minimax_corruption_rate",
                    title="Robust mean minimax rate under contamination",
                    informal_statement=(
                        "Under epsilon-fraction contamination and structural constraints, robust "
                        "mean estimators attain the minimax risk rate up to problem-dependent constants."
                    ),
                    proof_strategy=(
                        "Combine robust concentration upper bounds with testing or packing lower "
                        "bounds for the contaminated location model."
                    ),
                    status="FORMAL_GAP",
                    required_primitives=(
                        "gross_error_contamination_model",
                        "robust_concentration_upper_bound",
                        "testing_lower_bound",
                        "packing_argument",
                        "minimax_risk_definition",
                    ),
                ),
            ]
            procedures = [
                CandidateProcedure(
                    id="median_of_means_location",
                    name="Median-of-means robust location estimator",
                    role="estimator",
                    formula=(
                        "Partition X_1,...,X_n into B blocks, compute block means m_b, "
                        "and estimate theta by median_b m_b; use block-median SE from the "
                        "empirical spread of block means."
                    ),
                    informal_derivation=(
                        "A small number of extreme observations can distort the global sample mean, "
                        "but after splitting the sample only a minority of block means should be badly "
                        "corrupted when the contamination is controlled. Taking the median of block "
                        "means converts finite-variance concentration into a robust location estimate."
                    ),
                    algorithm="median_of_means_mean",
                    theorem_goals=tuple(goal.id for goal in goals),
                    simulation_design=(
                        "Simulate symmetric heavy-tailed observations with gross-error contamination, "
                        "estimate location by median-of-means, and evaluate bias, RMSE, block-SE "
                        "calibration, contamination fraction, and 95% coverage."
                    ),
                    limitations=(
                        "v0 simulation uses symmetric gross-error contamination, not worst-case one-sided adversarial contamination",
                        "minimax lower bounds and star-shaped constrained rates remain formal gaps",
                    ),
                )
            ]
            return procedures, goals
        if problem.problem_class == "differential_privacy_learning":
            goals = [
                TheoremGoal(
                    id="gaussian_mechanism_dp_calibration",
                    title="Gaussian mechanism epsilon-delta privacy calibration",
                    informal_statement=(
                        "For a query with bounded L2 sensitivity Delta, adding Gaussian noise "
                        "with sigma at the standard epsilon-delta calibration gives an "
                        "epsilon-delta differentially private release."
                    ),
                    proof_strategy=(
                        "Formalize adjacent datasets, query sensitivity, the Gaussian privacy-loss "
                        "random variable, and the standard tail bound used by the Gaussian mechanism."
                    ),
                    status="FORMAL_GAP",
                    required_primitives=(
                        "adjacent_dataset_relation",
                        "query_sensitivity",
                        "gaussian_mechanism_distribution",
                        "privacy_loss_random_variable",
                        "gaussian_tail_bound",
                        "epsilon_delta_dp_definition",
                    ),
                ),
                TheoremGoal(
                    id="private_mean_error_decomposition",
                    title="Private clipped-mean error decomposition",
                    informal_statement=(
                        "The private clipped mean decomposes into sampling error, clipping bias, "
                        "and independent privacy-noise error, so its Wald variance includes both "
                        "the clipped-sample variance over n and the privacy-noise variance."
                    ),
                    proof_strategy=(
                        "Define the clipped empirical mean, prove the noise is mean-zero and "
                        "independent of the sample, then add variance terms and isolate clipping bias."
                    ),
                    status="FORMAL_GAP",
                    required_primitives=(
                        "clipped_mean_definition",
                        "privacy_noise_mean_zero",
                        "independent_noise_variance_addition",
                        "finite_sample_mean_variance_indep",
                        "clipping_bias_bound",
                    ),
                    proof_obligations=(
                        "finite_sample_mean_variance_indep",
                        "finite_sample_mean_chebyshev_indep",
                        "noised_estimator_unbiased",
                        "noised_estimator_variance_indep",
                        "noised_estimator_chebyshev_indep",
                    ),
                ),
                TheoremGoal(
                    id="private_learning_excess_risk_rate",
                    title="Private learning excess-risk rate under general losses",
                    informal_statement=(
                        "For regular empirical losses, privatized releases or locally private "
                        "surrogates should attain an excess-risk rate with explicit privacy-noise "
                        "and statistical-complexity terms."
                    ),
                    proof_strategy=(
                        "Combine uniform convergence or stability of the empirical loss with "
                        "privacy-noise perturbation bounds and composition/local privacy accounting."
                    ),
                    status="FORMAL_GAP",
                    required_primitives=(
                        "general_loss_erm",
                        "uniform_convergence",
                        "private_release_stability",
                        "privacy_composition",
                        "excess_risk_decomposition",
                    ),
                ),
            ]
            procedures = [
                CandidateProcedure(
                    id="dp_gaussian_clipped_mean",
                    name="Gaussian-mechanism private clipped mean",
                    role="estimator",
                    formula=(
                        "theta_hat_DP = n^{-1} sum_i clip(X_i, -B, B) + Z, "
                        "Z ~ N(0, sigma_DP^2), sigma_DP = (2B/n)*sqrt(2 log(1.25/delta))/epsilon."
                    ),
                    informal_derivation=(
                        "Clipping gives a deterministic sensitivity bound for the sample mean. "
                        "The Gaussian mechanism adds calibrated mean-zero noise to protect adjacent "
                        "datasets. For inference, the standard error must combine the clipped-sample "
                        "variance term and the independent privacy-noise variance; remaining clipping "
                        "bias and full privacy accounting are tracked as formal theorem gaps."
                    ),
                    algorithm="dp_gaussian_mean",
                    theorem_goals=tuple(goal.id for goal in goals),
                    simulation_design=(
                        "Simulate bounded/clipped Gaussian data, add Gaussian privacy noise, and "
                        "evaluate bias, RMSE, Wald coverage, SE calibration, privacy noise, and clipping rate."
                    ),
                    limitations=(
                        "v0 uses a single scalar mean query, not full Edgeworth composition or local DP for arbitrary losses",
                        "epsilon-delta DP proof, composition accounting, and private excess-risk theory remain formal gaps",
                    ),
                )
            ]
            return procedures, goals
        if problem.problem_class == "nonparametric_regression_inference":
            goals = [
                TheoremGoal(
                    id="sieve_regression_pointwise_error_decomposition",
                    title="Sieve regression pointwise error decomposition",
                    informal_statement=(
                        "A pointwise nonparametric regression estimator decomposes into approximation "
                        "bias, empirical estimation error, and noise terms; Wald-style intervals require "
                        "a consistent linear-smoother variance estimate."
                    ),
                    proof_strategy=(
                        "Define a finite-dimensional sieve projection, separate approximation and "
                        "estimation error, and use finite-sample mean/Chebyshev ingredients for the "
                        "empirical component before adding asymptotic sieve approximation theory."
                    ),
                    status="FORMAL_GAP",
                    required_primitives=(
                        "nonparametric_function_class",
                        "sieve_projection_definition",
                        "approximation_bias_bound",
                        "linear_smoother_variance",
                        "sieve_empirical_process_bound",
                    ),
                    proof_obligations=(
                        "affine_estimator_expectation",
                        "affine_estimator_variance",
                        "finite_sample_mean_unbiased",
                        "finite_sample_mean_variance_indep",
                        "finite_sample_mean_chebyshev_indep",
                        "estimator_error_chebyshev",
                        "variance_nonneg",
                    ),
                ),
                TheoremGoal(
                    id="ensemble_subsampling_inference_validity",
                    title="Ensemble/subsampling inference validity",
                    informal_statement=(
                        "Subsampled or ensembled nonparametric learners can support pointwise inference "
                        "when the induced U-statistic/Hájek projection dominates higher-order remainders."
                    ),
                    proof_strategy=(
                        "Formalize the subsampling functional, prove the first-order projection "
                        "controls the ensemble estimator, and combine U-statistic CLT with nuisance "
                        "rate conditions."
                    ),
                    status="FORMAL_GAP",
                    required_primitives=(
                        "subsampling_functional",
                        "u_statistic_projection",
                        "hajek_projection_variance",
                        "u_statistic_clt",
                        "learner_stability_bound",
                    ),
                    proof_obligations=("finite_sample_mean_unbiased", "mean2_estimator_expectation"),
                ),
                TheoremGoal(
                    id="penalized_spline_selection_consistency",
                    title="Penalized spline/sieve tuning consistency",
                    informal_statement=(
                        "A penalized spline or sieve learner balances approximation and estimation "
                        "error, and data-driven tuning should preserve the target convergence rate."
                    ),
                    proof_strategy=(
                        "Formalize spline basis spaces, roughness penalties, oracle tuning, and "
                        "selection stability; then prove the selected estimator is rate-compatible "
                        "with the oracle sieve choice."
                    ),
                    status="FORMAL_GAP",
                    required_primitives=(
                        "spline_basis_space",
                        "roughness_penalty",
                        "oracle_sieve_dimension",
                        "tuning_selection_stability",
                        "rate_compatible_selected_estimator",
                    ),
                    proof_obligations=("estimator_error_chebyshev", "variance_nonneg"),
                ),
            ]
            procedures = [
                CandidateProcedure(
                    id="sieve_point_mean_inference",
                    name="Polynomial-sieve pointwise mean estimator",
                    role="estimator",
                    formula=(
                        "m_hat(x0)=b(x0)'(B'B+lambda I)^{-1}B'Y, with a linear-smoother "
                        "sandwich SE for pointwise Wald inference."
                    ),
                    informal_derivation=(
                        "Approximate the unknown regression surface by a finite sieve basis, fit a "
                        "regularized least-squares projection, and estimate pointwise uncertainty "
                        "from the linear smoother covariance. This is a controlled surrogate for "
                        "DNN/P-spline inference: useful for testing the theory-lab loop while the "
                        "full neural-network approximation and subsampling U-statistic theory remain gaps."
                    ),
                    algorithm="sieve_ensemble_regression",
                    theorem_goals=tuple(goal.id for goal in goals),
                    simulation_design=(
                        "Simulate a smooth nonlinear regression function, fit a degree-7 polynomial "
                        "sieve with ridge regularization, and evaluate pointwise bias, RMSE, SE "
                        "calibration, and 95% coverage at x0."
                    ),
                    limitations=(
                        "v0 simulator uses a polynomial sieve, not a trained DNN or full P-spline ECM tuner",
                        "DNN approximation, subsampling U-statistics, and adaptive tuning theory remain formal gaps",
                    ),
                )
            ]
            return procedures, goals
        if problem.problem_class == "geometric_spatial_point_process_inference":
            goals = [
                TheoremGoal(
                    id="metric_graph_kernel_prediction_consistency",
                    title="Metric-graph kernel prediction consistency",
                    informal_statement=(
                        "For observations on a compact metric graph, a local kernel smoother should "
                        "recover smooth graph-supported regression or field means as the graph sample "
                        "becomes dense and the bandwidth shrinks at a compatible rate."
                    ),
                    proof_strategy=(
                        "Formalize graph distance balls, kernel weights, and a bias-variance "
                        "decomposition; use finite-sample mean and variance facts for the stochastic "
                        "part while graph Sobolev approximation and in-fill asymptotics remain gaps."
                    ),
                    status="FORMAL_GAP",
                    required_primitives=(
                        "metric_graph_space",
                        "graph_distance_ball",
                        "kernel_smoother_definition",
                        "graph_sobolev_smoothness",
                        "infill_sampling_density",
                        "bias_variance_decomposition",
                    ),
                    proof_obligations=(
                        "finite_sample_mean_unbiased",
                        "finite_sample_mean_variance_indep",
                        "finite_sample_mean_chebyshev_indep",
                        "estimator_error_chebyshev",
                        "variance_nonneg",
                    ),
                ),
                TheoremGoal(
                    id="spde_matern_field_likelihood_validity",
                    title="Whittle-Matern/SPDE field likelihood validity",
                    informal_statement=(
                        "Gaussian Whittle-Matern fields or anisotropic SPDE priors should define "
                        "valid covariance operators and support likelihood or posterior inference for "
                        "prediction and covariance parameters on geometric domains."
                    ),
                    proof_strategy=(
                        "Introduce the covariance/operator interface, prove positive-variance and "
                        "probability-kernel sanity facts now, and leave SPDE elliptic-operator and "
                        "anisotropy parametrization theory as explicit formal gaps."
                    ),
                    status="FORMAL_GAP",
                    required_primitives=(
                        "gaussian_random_field",
                        "spde_matern_covariance",
                        "positive_covariance_operator",
                        "anisotropy_parametrization",
                        "posterior_field_calibration",
                    ),
                    proof_obligations=("prob_measure_univ", "variance_nonneg", "integral_of_constant"),
                ),
                TheoremGoal(
                    id="point_process_intensity_contrast_validity",
                    title="Point-process intensity contrast validity",
                    informal_statement=(
                        "For point-process covariates or corrupted superposed processes, a smoothed "
                        "intensity contrast should estimate the target intensity functional and support "
                        "selection or minimum-contrast inference."
                    ),
                    proof_strategy=(
                        "Represent binned counts as finite sums of indicators, use expectation and "
                        "variance bridge facts for finite count summaries, and mark Poisson/Palm "
                        "measure theory and asymptotic minimum contrast as formal gaps."
                    ),
                    status="FORMAL_GAP",
                    required_primitives=(
                        "point_process_counting_measure",
                        "kernel_intensity_estimator",
                        "poisson_count_moments",
                        "minimum_contrast_objective",
                        "selection_consistency",
                    ),
                    proof_obligations=(
                        "event_indicator_expectation",
                        "finite_sample_mean_unbiased",
                        "finite_sample_mean_variance_indep",
                        "markov_inequality",
                    ),
                ),
                TheoremGoal(
                    id="superposed_palm_mixture_representation",
                    title="Palm mixture representation for superposed point processes",
                    informal_statement=(
                        "The Palm law of a finite superposition of independent point processes should "
                        "decompose as an intensity-weighted mixture of component Palm laws."
                    ),
                    proof_strategy=(
                        "Start with finite mixture/probability normalization facts, then extend to "
                        "point-process Palm kernels, Janossy densities, and shot-noise Cox processes "
                        "as a dedicated Lean library target."
                    ),
                    status="FORMAL_GAP",
                    required_primitives=(
                        "point_process_palm_distribution",
                        "superposition_counting_measure",
                        "intensity_weighted_mixture",
                        "janossy_density",
                        "palm_kernel_normalization",
                    ),
                    proof_obligations=(
                        "prob_measure_univ",
                        "finite_union_bound",
                        "finite_union_budget_control",
                        "simultaneous_coverage_of_union_error_bound",
                    ),
                ),
            ]
            procedures = [
                CandidateProcedure(
                    id="metric_graph_kernel_field_predictor",
                    name="Metric-graph kernel field predictor",
                    role="estimator",
                    formula=(
                        "m_hat(v0)=sum_i K(d(v_i,v0)/h)Y_i / sum_i K(d(v_i,v0)/h), "
                        "with graph-distance weights and residual bootstrap-style Wald SE."
                    ),
                    informal_derivation=(
                        "A compact metric graph supplies distances even when Euclidean coordinates "
                        "are misleading. Local averaging over nearby graph locations estimates the "
                        "field or regression mean; the simulation checks the finite-sample bias, "
                        "RMSE, and interval calibration while the graph Sobolev/in-fill theorem is "
                        "kept as a formal gap."
                    ),
                    algorithm="metric_graph_kernel_smoother",
                    theorem_goals=tuple(goal.id for goal in goals),
                    simulation_design=(
                        "Simulate a smooth field on a path metric graph with correlated noise, observe "
                        "a random subset of graph locations, smooth by graph-distance kernels, and "
                        "evaluate field RMSE, SE calibration, and 95% coverage at held-out locations."
                    ),
                    limitations=(
                        "v0 uses a path graph and RBF kernel smoother, not a full Whittle-Matern SPDE likelihood",
                        "metric-graph Sobolev theory, operator covariance proofs, and manifold delta methods remain gaps",
                    ),
                ),
                CandidateProcedure(
                    id="point_process_kernel_intensity_contrast",
                    name="Point-process kernel intensity contrast",
                    role="estimator",
                    formula=(
                        "Delta_hat = integral_A lambda_hat_1(s)ds - integral_A lambda_hat_0(s)ds, "
                        "estimated from binned kernel-smoothed point counts with Wald uncertainty."
                    ),
                    informal_derivation=(
                        "Point processes can be summarized by local counting intensities. In a finite "
                        "binning surrogate, independent superposed processes add their intensities; a "
                        "kernel-smoothed contrast estimates where the process has higher activity. "
                        "This gives an executable bridge for point-process additive/Palm questions "
                        "while true Palm and Janossy identities remain formal theorem targets."
                    ),
                    algorithm="point_process_intensity_contrast",
                    theorem_goals=tuple(goal.id for goal in goals),
                    simulation_design=(
                        "Simulate two independent one-dimensional inhomogeneous Poisson processes, "
                        "estimate an intensity contrast over a target region, and evaluate relative "
                        "bias, RMSE, coverage, and selection accuracy for the high-intensity region."
                    ),
                    limitations=(
                        "v0 uses binned one-dimensional Poisson processes, not full random-measure additive models",
                        "Palm-mixture, Janossy, and Cox-process minimum-contrast theory remain formal gaps",
                    ),
                ),
            ]
            return procedures, goals
        if problem.problem_class == "bayesian_posterior_calibration":
            goals = [
                TheoremGoal(
                    id="predictive_prior_translation_coherence",
                    title="Predictive-distribution-to-prior coherence",
                    informal_statement=(
                        "A translated prior should preserve the external predictive distribution's "
                        "target moments or predictive uncertainty in the subsequent Bayesian model."
                    ),
                    proof_strategy=(
                        "Formalize the predictive distribution as a probability kernel, define the "
                        "prior-translation map, and prove preservation of the chosen moment or "
                        "calibration functional."
                    ),
                    status="FORMAL_GAP",
                    required_primitives=(
                        "probability_kernel",
                        "pushforward_prior_translation",
                        "moment_preservation",
                        "posterior_predictive_distribution",
                        "law_of_total_expectation",
                    ),
                    proof_obligations=("prob_measure_univ", "integral_of_constant"),
                ),
                TheoremGoal(
                    id="normal_conjugate_posterior_mean_error_decomposition",
                    title="Normal-conjugate posterior mean error decomposition",
                    informal_statement=(
                        "In the conjugate normal baseline, the posterior mean error decomposes into "
                        "a shrinkage term from the transported prior and a weighted sample-mean noise term."
                    ),
                    proof_strategy=(
                        "Define the normal-normal posterior mean as an affine combination of the "
                        "prior mean and sample mean; use finite-sample unbiasedness and variance facts "
                        "for the sample component before adding the shrinkage-bias term."
                    ),
                    status="FORMAL_GAP",
                    required_primitives=(
                        "normal_conjugate_posterior_formula",
                        "finite_sample_mean_variance_indep",
                        "affine_estimator_bias_variance",
                        "prior_shrinkage_bias",
                    ),
                    proof_obligations=(
                        "affine_estimator_expectation",
                        "affine_estimator_variance",
                        "finite_sample_mean_unbiased",
                        "finite_sample_mean_variance_indep",
                        "finite_sample_mean_chebyshev_indep",
                        "estimator_error_chebyshev",
                        "variance_nonneg",
                    ),
                ),
                TheoremGoal(
                    id="posterior_credible_interval_calibration",
                    title="Posterior credible interval calibration",
                    informal_statement=(
                        "Posterior credible intervals should have calibrated repeated-sampling or "
                        "prior-predictive coverage under the transported-prior assumptions."
                    ),
                    proof_strategy=(
                        "For the conjugate baseline, reduce coverage to a normal pivot; for frontier "
                        "translated priors, prove posterior predictive calibration under the coherence "
                        "conditions and quantify approximation error."
                    ),
                    status="FORMAL_GAP",
                    required_primitives=(
                        "normal_posterior_pivot",
                        "credible_interval_definition",
                        "prior_predictive_coverage",
                        "posterior_concentration",
                        "calibration_error_bound",
                    ),
                    proof_obligations=(
                        "prob_compl",
                        "wald_interval_miscoverage_iff_abs_error_gt",
                        "coverage_lower_bound_of_complement_error",
                        "markov_inequality",
                        "estimator_error_chebyshev",
                    ),
                ),
            ]
            procedures = [
                CandidateProcedure(
                    id="normal_conjugate_translated_prior_mean",
                    name="Normal-conjugate posterior mean with transported prior",
                    role="estimator",
                    formula=(
                        "theta_hat_post = v_n*(mu0/tau0^2 + n*xbar/sigma^2), "
                        "v_n=(1/tau0^2+n/sigma^2)^{-1}; CI = theta_hat_post ± 1.96*sqrt(v_n)."
                    ),
                    informal_derivation=(
                        "Translate the external predictive distribution into a normal prior by matching "
                        "its mean and variance, then update with the subsequent normal-likelihood sample. "
                        "The posterior mean is a precision-weighted average of prior mean and sample mean; "
                        "simulation checks whether transported-prior shrinkage preserves calibration."
                    ),
                    algorithm="normal_conjugate_posterior_mean",
                    theorem_goals=tuple(goal.id for goal in goals),
                    simulation_design=(
                        "Simulate a subsequent normal sample with a mildly informative transported prior, "
                        "compute the conjugate posterior mean and credible interval, and evaluate bias, "
                        "RMSE, repeated-sampling coverage, posterior SD calibration, and prior influence."
                    ),
                    limitations=(
                        "v0 uses a normal-normal conjugate surrogate, not arbitrary predictive-to-prior mappings",
                        "prior coherence, posterior concentration, and nonconjugate calibration remain formal gaps",
                    ),
                )
            ]
            return procedures, goals
        if problem.problem_class == "measurement_bias_ranking_inference":
            goals = [
                TheoremGoal(
                    id="bias_adjusted_assessment_mean_identification",
                    title="Bias-adjusted assessment mean identifies country ability",
                    informal_statement=(
                        "After subtracting calibrated item difficulty and cultural/linguistic bias terms, "
                        "the adjusted score has expectation equal to the latent country ability."
                    ),
                    proof_strategy=(
                        "Represent the adjusted score as an affine transformation of the observed score "
                        "minus known bias components, use expectation linearity and finite-sample mean "
                        "unbiasedness, and then isolate the remaining bias-calibration assumptions."
                    ),
                    status="FORMAL_GAP",
                    required_primitives=(
                        "item_response_measurement_model",
                        "country_item_bias_function",
                        "bias_calibration_consistency",
                        "finite_country_item_sample_mean",
                    ),
                    proof_obligations=(
                        "affine_estimator_expectation",
                        "finite_sample_mean_unbiased",
                        "integral_of_constant",
                    ),
                ),
                TheoremGoal(
                    id="assessment_ranking_uncertainty_validity",
                    title="Bias-adjusted ranking uncertainty validity",
                    informal_statement=(
                        "Intervals or reliability scores for country rankings should reflect sampling "
                        "variation after measurement-bias adjustment, especially when countries are nearly tied."
                    ),
                    proof_strategy=(
                        "Define rank functionals of country means, relate ranking errors to pairwise mean "
                        "estimation errors, and use finite-sample concentration before developing the full "
                        "rank-functional asymptotic theory."
                    ),
                    status="FORMAL_GAP",
                    required_primitives=(
                        "rank_functional",
                        "pairwise_country_mean_separation",
                        "simultaneous_confidence_bands",
                        "rank_uncertainty_functional_delta_method",
                    ),
                    proof_obligations=(
                        "affine_estimator_variance",
                        "finite_sample_mean_variance_indep",
                        "finite_sample_mean_chebyshev_indep",
                        "estimator_error_chebyshev",
                        "finite_family_absolute_error_union_control",
                        "simultaneous_coverage_of_union_error_bound",
                        "pairwise_top_rank_correct_of_separation",
                        "variance_nonneg",
                        "prob_compl",
                    ),
                ),
                TheoremGoal(
                    id="measurement_invariance_bias_model_validity",
                    title="Measurement-bias model validity under noninvariance",
                    informal_statement=(
                        "The calibrated bias-adjustment model must account for cross-country/item "
                        "measurement noninvariance without erasing genuine country ability differences."
                    ),
                    proof_strategy=(
                        "Formalize the IRT or latent-measurement model, define cultural/linguistic bias "
                        "parameters, and prove identifiability under anchoring or invariance constraints."
                    ),
                    status="FORMAL_GAP",
                    required_primitives=(
                        "item_response_theory_likelihood",
                        "measurement_invariance_constraints",
                        "bias_parameter_identifiability",
                        "latent_ability_scale_normalization",
                    ),
                ),
            ]
            procedures = [
                CandidateProcedure(
                    id="bias_adjusted_country_ranking",
                    name="Bias-adjusted country ranking estimator",
                    role="estimator",
                    formula=(
                        "theta_hat_g = mean_{i,j in country g}(Y_gij - item_j - bias_gj); "
                        "rank countries by theta_hat_g with Wald intervals for each theta_g."
                    ),
                    informal_derivation=(
                        "An additive measurement-bias model decomposes observed assessment scores into "
                        "latent country ability, item difficulty, country/item bias, and noise. Subtracting "
                        "calibrated item and bias terms reduces ranking to country mean estimation; the "
                        "formal trace proves affine and finite-mean subclaims while leaving IRT bias "
                        "identifiability and rank-functional theory as gaps."
                    ),
                    algorithm="measurement_bias_adjusted_ranking",
                    theorem_goals=tuple(goal.id for goal in goals),
                    simulation_design=(
                        "Simulate country-by-item assessment scores with known item difficulty and "
                        "country/item measurement bias, subtract calibrated bias, estimate country means, "
                        "and evaluate RMSE, 95% mean coverage, SE calibration, top-rank accuracy, rank "
                        "correlation, and mean absolute rank error."
                    ),
                    limitations=(
                        "v0 uses an additive calibrated-bias model, not a full IRT likelihood",
                        "bias calibration, measurement-invariance identifiability, and rank asymptotics remain formal gaps",
                    ),
                )
            ]
            return procedures, goals
        if problem.problem_class == "design_based_variance_inference":
            goals = [
                TheoremGoal(
                    id="neyman_variance_conservative_validity",
                    title="Neyman variance estimator is conservative for finite-population ATE",
                    informal_statement=(
                        "Under complete randomization, the usual difference-in-means variance estimator "
                        "upper-bounds the finite-population randomization variance because the unit-level "
                        "treatment-effect variance term is not identifiable from one assignment."
                    ),
                    proof_strategy=(
                        "Formalize complete randomization over a finite population, compute the exact "
                        "randomization variance, and compare it with the observable Neyman bound."
                    ),
                    status="FORMAL_GAP",
                    required_primitives=(
                        "finite_population_potential_outcomes",
                        "complete_randomization_distribution",
                        "difference_in_means_unbiasedness",
                        "randomization_variance_decomposition",
                        "neyman_bound_nonnegative_treatment_effect_variance",
                    ),
                    proof_obligations=(
                        "finite_sample_mean_unbiased",
                        "mean2_estimator_unbiased",
                        "mean2_estimator_variance_indep",
                        "finite_sample_mean_variance_indep",
                        "finite_sample_mean_chebyshev_indep",
                        "estimator_error_chebyshev",
                        "variance_nonneg",
                    ),
                ),
                TheoremGoal(
                    id="optimized_variance_bound_minimality",
                    title="Optimized conservative variance bound minimality",
                    informal_statement=(
                        "Given design and structural constraints, the optimized conservative variance "
                        "estimator is the least conservative estimable upper bound for the true variance."
                    ),
                    proof_strategy=(
                        "Cast conservative variance estimation as a constrained optimization problem "
                        "over compatible potential-outcome schedules and prove optimality of the bound."
                    ),
                    status="FORMAL_GAP",
                    required_primitives=(
                        "estimable_variance_functional",
                        "compatible_potential_outcome_set",
                        "conservative_upper_bound_order",
                        "finite_dimensional_convex_optimization",
                        "least_conservative_bound_optimality",
                    ),
                ),
            ]
            procedures = [
                CandidateProcedure(
                    id="neyman_conservative_variance_bound",
                    name="Neyman conservative randomization variance estimator",
                    role="estimator",
                    formula=(
                        "tau_hat = mean(Y_obs | A=1)-mean(Y_obs | A=0); "
                        "V_hat_Neyman = s_1^2/n_1 + s_0^2/n_0, an observable conservative bound."
                    ),
                    informal_derivation=(
                        "Complete randomization makes the difference in observed group means unbiased "
                        "for the finite-population average treatment effect. The exact randomization "
                        "variance subtracts the unobservable unit-level treatment-effect variance; "
                        "dropping that nonnegative term yields the conservative Neyman bound."
                    ),
                    algorithm="neyman_conservative_variance",
                    theorem_goals=tuple(goal.id for goal in goals),
                    simulation_design=(
                        "Generate finite potential-outcome schedules with heterogeneous effects, repeatedly "
                        "randomize treatment, estimate ATE and Neyman SE, and compare coverage and estimated "
                        "variance against the known finite-population randomization variance."
                    ),
                    limitations=(
                        "v0 simulator uses SUTVA complete randomization, not interference or arbitrary complex designs",
                        "optimized least-conservative variance bounds remain a formal gap",
                    ),
                )
            ]
            return procedures, goals
        if problem.problem_class == "experimental_design_optimization":
            goals = [
                TheoremGoal(
                    id="maximin_space_filling_surrogate_validity",
                    title="Maximin space-filling surrogate validity",
                    informal_statement=(
                        "A finite candidate subset chosen to maximize the minimum pairwise distance "
                        "should improve the space-filling criterion over a random run-budget subset."
                    ),
                    proof_strategy=(
                        "Formalize finite design spaces, pairwise distance objectives, and greedy "
                        "or oracle-array surrogate selection; prove the selected design satisfies the "
                        "registered finite maximin criterion before extending to Lp optimality."
                    ),
                    status="FORMAL_GAP",
                    required_primitives=(
                        "finite_design_space",
                        "pairwise_design_distance",
                        "maximin_distance_criterion",
                        "oracle_array_surrogate_order",
                    ),
                    proof_obligations=("finite_union_bound", "finite_union_budget_control"),
                ),
                TheoremGoal(
                    id="covariate_balance_rerandomization_validity",
                    title="Covariate-balanced rerandomization validity",
                    informal_statement=(
                        "Choosing among symmetric candidate assignments by a covariate-balance score "
                        "can improve balance while preserving a randomization-based interpretation."
                    ),
                    proof_strategy=(
                        "Represent assignments as finite random variables, define standardized balance "
                        "loss, prove symmetry of treated/control relabeling for the candidate generator, "
                        "and then establish the acceptance/event-control bridge."
                    ),
                    status="FORMAL_GAP",
                    required_primitives=(
                        "finite_assignment_space",
                        "covariate_balance_objective",
                        "symmetric_rerandomization_rule",
                        "randomization_validity_under_acceptance",
                    ),
                    proof_obligations=(
                        "prob_measure_univ",
                        "event_probability_mono",
                        "finite_union_bound",
                    ),
                ),
                TheoremGoal(
                    id="order_addition_stratum_orthogonality",
                    title="Order-of-addition stratum orthogonality",
                    informal_statement=(
                        "A stratum order-of-addition design should remain model-free and robust to "
                        "model uncertainty by balancing position/order contrasts across strata."
                    ),
                    proof_strategy=(
                        "Formalize component orders as permutations, define stratum balance and "
                        "orthogonality contrasts, and prove contrast cancellation for the constructed "
                        "finite design before developing full model-robust optimality."
                    ),
                    status="FORMAL_GAP",
                    required_primitives=(
                        "finite_permutation_design",
                        "stratum_orthogonality_criterion",
                        "order_contrast_balance",
                        "model_free_design_robustness",
                    ),
                    proof_obligations=("integral_of_constant",),
                ),
            ]
            procedures = [
                CandidateProcedure(
                    id="maximin_balance_rerandomized_design",
                    name="Maximin covariate-balanced rerandomized design",
                    role="design_procedure",
                    formula=(
                        "Select a finite run-budget subset by greedy maximin distance; among symmetric "
                        "candidate treatment assignments choose the assignment minimizing standardized "
                        "covariate imbalance with a small maximin-distance reward."
                    ),
                    informal_derivation=(
                        "Space-filling design and covariate-balance randomization are both finite "
                        "optimization problems over candidate design/assignment sets. The v0 procedure "
                        "separates these concerns: greedy maximin selection improves geometric coverage "
                        "of the design space, then rerandomization screens balanced assignments. The "
                        "formal trace proves only reusable finite-probability subclaims and leaves "
                        "oracle-array, stratum-orthogonality, and Gaussianized-design optimality as gaps."
                    ),
                    algorithm="covariate_balance_maximin_design",
                    theorem_goals=tuple(goal.id for goal in goals),
                    simulation_design=(
                        "Generate correlated covariates, compare greedy maximin run selection with a "
                        "random subset, then compare covariate-balanced rerandomized treatment assignment "
                        "with simple random assignment using imbalance and space-filling diagnostics."
                    ),
                    limitations=(
                        "v0 uses Euclidean finite-design surrogates, not full oracle-array construction",
                        "order-of-addition and Gaussianized covariance-matrix optimality remain formal gaps",
                    ),
                )
            ]
            return procedures, goals
        if problem.problem_class == "heteroskedastic_regression_inference":
            goals = [
                TheoremGoal(
                    id="ols_consistency",
                    title="OLS slope consistency under exogeneity",
                    informal_statement="The OLS slope converges to beta under iid exogeneity and full-rank design.",
                    proof_strategy="LLN for sample moments and continuous mapping for the inverse Gram matrix.",
                    status="FORMAL_GAP",
                    required_primitives=(
                        "sample_moment_lln",
                        "exogeneity_moment_condition",
                        "gram_matrix_full_rank",
                        "matrix_inverse_continuous_mapping",
                    ),
                ),
                TheoremGoal(
                    id="hc1_asymptotic_normality",
                    title="HC1 sandwich Wald interval validity",
                    informal_statement="The HC1 sandwich standard error yields asymptotically valid Wald intervals under heteroskedasticity.",
                    proof_strategy="Multivariate CLT for score moments plus consistency of the sandwich covariance estimator.",
                    status="FORMAL_GAP",
                    required_primitives=(
                        "multivariate_score_clt",
                        "sandwich_covariance_definition",
                        "hc1_variance_consistency",
                        "wald_interval_slutsky",
                    ),
                    proof_obligations=(
                        "wald_interval_contains_iff_abs_error",
                        "wald_interval_miscoverage_iff_abs_error_gt",
                        "coverage_lower_bound_of_complement_error",
                    ),
                ),
            ]
            procedures = [
                CandidateProcedure(
                    id="ols_hc1_slope",
                    name="OLS slope with HC1 robust standard error",
                    role="estimator",
                    formula="beta_hat = (X'X)^{-1}X'Y; V_HC1 = n/(n-p) (X'X)^{-1} X' diag(e_i^2) X (X'X)^{-1}.",
                    informal_derivation=(
                        "OLS estimates the best linear conditional mean under exogeneity. "
                        "Heteroskedasticity breaks homoskedastic SE formulas, so the sandwich covariance "
                        "estimates the variance of the empirical score."
                    ),
                    algorithm="ols_hc1",
                    theorem_goals=tuple(goal.id for goal in goals),
                    simulation_design="Linear model with Var(eps|X)=1+X^2 and Wald coverage for beta.",
                    limitations=("fixed low-dimensional design only", "sandwich consistency remains a formal gap"),
                )
            ]
            return procedures, goals
        if problem.problem_class == "multiple_testing_fdr":
            goals = [
                TheoremGoal(
                    id="bh_fdr_control_independence",
                    title="Benjamini-Hochberg FDR control under independent null p-values",
                    informal_statement="For independent valid null p-values, the BH step-up procedure controls FDR at level q*m0/m <= q.",
                    proof_strategy="Formalize ordered p-values, the self-consistency property of the BH threshold, and the standard leave-one-out FDR decomposition.",
                    status="FORMAL_GAP",
                    required_primitives=(
                        "valid_null_pvalue_uniformity",
                        "ordered_pvalues",
                        "bh_stepup_self_consistency",
                        "leave_one_out_fdr_decomposition",
                        "independent_null_pvalues",
                    ),
                    proof_obligations=(
                        "prob_measure_univ",
                        "prob_compl",
                        "event_probability_mono",
                        "independent_event_inter_probability",
                        "finite_union_bound",
                        "finite_union_budget_control",
                        "markov_inequality",
                    ),
                ),
                TheoremGoal(
                    id="bh_sparse_mixture_power",
                    title="Power of BH under a sparse Gaussian mixture",
                    informal_statement="Under separated non-null z-statistics, BH has nontrivial discovery power while keeping empirical FDR near q.",
                    proof_strategy="Combine Gaussian tail bounds, empirical distribution convergence for p-values, and the BH threshold fixed-point argument.",
                    status="FORMAL_GAP",
                    required_primitives=(
                        "gaussian_tail_bounds",
                        "sparse_mixture_model",
                        "empirical_pvalue_cdf_convergence",
                        "bh_threshold_fixed_point",
                        "power_lower_bound",
                    ),
                ),
            ]
            procedures = [
                CandidateProcedure(
                    id="bh_fdr_stepup",
                    name="Benjamini-Hochberg step-up procedure",
                    role="test",
                    formula=(
                        "Let p_(1) <= ... <= p_(m). Reject all H_(i) with "
                        "p_(i) <= (i/m) q up to the largest qualifying index."
                    ),
                    informal_derivation=(
                        "The BH threshold is a data-adaptive linear boundary on ordered p-values. "
                        "Under independent valid null p-values, the classical proof decomposes FDR "
                        "by conditioning on the other p-values and uses null uniformity."
                    ),
                    algorithm="benjamini_hochberg",
                    theorem_goals=tuple(goal.id for goal in goals),
                    simulation_design="Sparse Gaussian z-test mixture with independent nulls and two-sided p-values.",
                    limitations=(
                        "v0 simulator uses independent tests only",
                        "PRDS/correlated-test FDR control remains outside the current proof bank",
                    ),
                )
            ]
            return procedures, goals
        if problem.problem_class == "sequential_anytime_inference":
            goals = [
                TheoremGoal(
                    id="eprocess_optional_stopping_control",
                    title="E-process optional-stopping type-I control",
                    informal_statement="If E_t is a nonnegative e-process with E_0=1 under the null, then P_null(sup_t E_t >= 1/alpha) <= alpha.",
                    proof_strategy="Formalize filtrations, nonnegative supermartingales, stopping times, and apply Ville's inequality.",
                    status="FORMAL_GAP",
                    required_primitives=(
                        "filtration",
                        "stopping_time",
                        "nonnegative_supermartingale",
                        "ville_inequality",
                        "eprocess_type1_control",
                    ),
                    proof_obligations=(
                        "prob_measure_univ",
                        "event_probability_mono",
                        "finite_union_bound",
                        "finite_horizon_type1_union_control",
                        "finite_union_budget_control",
                        "markov_inequality",
                        "adapted_hitting_after_is_stopping_time",
                        "first_borel_cantelli_limsup_zero",
                    ),
                ),
                TheoremGoal(
                    id="bernoulli_lr_eprocess_martingale",
                    title="Bernoulli likelihood-ratio process is a null martingale",
                    informal_statement="The product likelihood ratio for Bernoulli(p1) against Bernoulli(p0) has conditional mean one under p0.",
                    proof_strategy="Define the sequential product process and prove conditional expectation preservation by independence.",
                    status="FORMAL_GAP",
                    required_primitives=(
                        "bernoulli_likelihood_ratio",
                        "adapted_product_process",
                        "conditional_expectation_product_step",
                        "independent_bernoulli_sequence",
                        "martingale_definition",
                    ),
                    proof_obligations=(
                        "event_indicator_expectation",
                        "finite_event_indicator_mean_unbiased",
                        "independent_event_inter_probability",
                    ),
                ),
            ]
            procedures = [
                CandidateProcedure(
                    id="bernoulli_lr_anytime_test",
                    name="Bernoulli likelihood-ratio e-process anytime test",
                    role="test",
                    formula=(
                        "E_t = prod_{i<=t} (p1/p0)^{X_i}((1-p1)/(1-p0))^{1-X_i}; "
                        "reject H0 when E_t >= 1/alpha."
                    ),
                    informal_derivation=(
                        "The likelihood ratio has mean one under the simple Bernoulli null. "
                        "A nonnegative martingale can be monitored continuously, and Ville's "
                        "inequality gives alpha-level control for threshold 1/alpha."
                    ),
                    algorithm="bernoulli_lr_eprocess",
                    theorem_goals=tuple(goal.id for goal in goals),
                    simulation_design="Simulate optional stopping under p0=0.5 and power under p=0.65 over a finite horizon.",
                    limitations=(
                        "v0 uses a simple-vs-simple Bernoulli alternative, not composite anytime confidence sequences",
                        "Ville inequality and filtration formalization remain outside the current proof bank",
                    ),
                )
            ]
            return procedures, goals
        if problem.problem_class == "sequential_changepoint_inference":
            goals = [
                TheoremGoal(
                    id="functional_cusum_changepoint_localization",
                    title="Functional CUSUM changepoint localization",
                    informal_statement=(
                        "A CUSUM detector applied to partially observed functional trajectories should "
                        "localize a single structural break when the projected mean shift dominates "
                        "serial dependence and measurement error."
                    ),
                    proof_strategy=(
                        "Formalize a discretized functional time-series array, define the CUSUM "
                        "objective, show deterministic separation of the population objective around "
                        "the true changepoint, and control the stochastic remainder."
                    ),
                    status="FORMAL_GAP",
                    required_primitives=(
                        "functional_time_series_process",
                        "partial_measurement_error_model",
                        "cusum_objective_population_separation",
                        "dependent_array_maximal_inequality",
                    ),
                    proof_obligations=(
                        "finite_union_bound",
                        "finite_union_budget_control",
                        "markov_inequality",
                    ),
                ),
                TheoremGoal(
                    id="post_detection_changepoint_confidence_set",
                    title="Post-detection changepoint confidence set validity",
                    informal_statement=(
                        "After a sequential detector stops and declares a change, the reported "
                        "changepoint interval should account for the data-dependent stopping rule."
                    ),
                    proof_strategy=(
                        "Represent the detector stop as a stopping time, define the selected "
                        "localization interval, and bridge detector error control to post-detection "
                        "coverage while leaving selective/sequential inference theory explicit."
                    ),
                    status="FORMAL_GAP",
                    required_primitives=(
                        "changepoint_stopping_rule",
                        "post_selection_inference",
                        "selected_interval_coverage",
                        "bootstrap_validity_for_dependent_data",
                    ),
                    proof_obligations=(
                        "prob_compl",
                        "coverage_lower_bound_of_complement_error",
                        "event_probability_mono",
                        "finite_union_bound",
                    ),
                ),
                TheoremGoal(
                    id="sequential_model_confidence_set_validity",
                    title="Sequential model confidence set validity",
                    informal_statement=(
                        "Model confidence sets updated over time should retain uncertainty accounting "
                        "for the sequential loss/performance evaluation path."
                    ),
                    proof_strategy=(
                        "Formalize candidate-model loss processes, define sequential elimination events, "
                        "and reduce coverage to finite-time union control plus a future martingale or "
                        "bootstrap validity theorem."
                    ),
                    status="FORMAL_GAP",
                    required_primitives=(
                        "candidate_model_loss_process",
                        "sequential_elimination_rule",
                        "model_confidence_set_coverage",
                        "dependent_performance_process_bootstrap",
                    ),
                    proof_obligations=(
                        "prob_measure_univ",
                        "finite_union_bound",
                        "simultaneous_coverage_of_union_error_bound",
                    ),
                ),
            ]
            procedures = [
                CandidateProcedure(
                    id="functional_cusum_post_detection_interval",
                    name="Functional CUSUM changepoint detector with post-detection interval",
                    role="sequential_procedure",
                    formula=(
                        "Project partially observed functional trajectories onto a fixed contrast, "
                        "compute CUSUM(k)=sqrt(k(n-k)/n)|mean_{t<=k}Z_t-mean_{t>k}Z_t|, "
                        "estimate tau by argmax_k CUSUM(k), and report tau_hat ± h."
                    ),
                    informal_derivation=(
                        "A single mean shift creates a triangular population CUSUM objective peaking at "
                        "the true changepoint. The v0 algorithm keeps the procedure transparent: it uses "
                        "a projection of partially observed trajectories, a finite grid search over split "
                        "points, and a conservative post-detection interval. The formal trace proves only "
                        "finite probability subclaims and leaves functional time-series CUSUM limit theory "
                        "and selective/post-detection validity as gaps."
                    ),
                    algorithm="cusum_changepoint_detector",
                    theorem_goals=tuple(goal.id for goal in goals),
                    simulation_design=(
                        "Simulate a discretized functional time series with AR dependence, one mean shift, "
                        "and partial measurement error; estimate the changepoint by CUSUM, compare "
                        "localization error, post-detection interval coverage, and null false-alarm rate."
                    ),
                    limitations=(
                        "v0 uses a single projected mean shift, not arbitrary discontinuous trajectories",
                        "post-detection/selective inference and dependent bootstrap validity remain formal gaps",
                    ),
                )
            ]
            return procedures, goals
        if problem.problem_class == "network_graph_inference":
            goals = [
                TheoremGoal(
                    id="network_edge_density_unbiasedness",
                    title="Edge-density estimator is unbiased in an independent-edge network baseline",
                    informal_statement=(
                        "For a finite graph with conditionally independent Bernoulli edge indicators, "
                        "the empirical edge density has expectation equal to the average edge probability."
                    ),
                    proof_strategy=(
                        "Index unordered node pairs, represent adjacency entries as event indicators, "
                        "and reduce the edge-density estimator to a finite sample mean of indicators."
                    ),
                    status="FORMAL_GAP",
                    required_primitives=(
                        "finite_graph_edge_index",
                        "adjacency_indicator_model",
                        "graph_edge_density_functional",
                        "independent_edge_array",
                        "finite_event_indicator_mean_unbiased",
                    ),
                    proof_obligations=(
                        "event_indicator_expectation",
                        "finite_event_indicator_mean_unbiased",
                        "finite_sample_mean_variance_indep",
                        "finite_sample_mean_chebyshev_indep",
                        "finite_union_budget_control",
                        "variance_nonneg",
                    ),
                ),
                TheoremGoal(
                    id="spectral_community_recovery",
                    title="Spectral community recovery under stochastic block model separation",
                    informal_statement=(
                        "In a balanced two-block stochastic block model with a separated population "
                        "adjacency spectrum, the leading centered adjacency eigenvector recovers the "
                        "latent community labels up to sign."
                    ),
                    proof_strategy=(
                        "Combine finite graph matrix definitions, matrix concentration for the "
                        "centered adjacency matrix, and a Davis-Kahan eigenspace perturbation bound."
                    ),
                    status="FORMAL_GAP",
                    required_primitives=(
                        "finite_graph_adjacency_matrix",
                        "stochastic_block_model_distribution",
                        "matrix_bernstein_for_adjacency",
                        "davis_kahan_sin_theta",
                        "community_label_recovery_loss",
                    ),
                    proof_obligations=("variance_nonneg", "finite_union_budget_control"),
                ),
                TheoremGoal(
                    id="frontier_network_model_extensions",
                    title="Mixed-membership, signed, dynamic, and dependent-edge network theory",
                    informal_statement=(
                        "Frontier network papers require uncertainty for node mixing probabilities, "
                        "signed-network balance tests, dynamic network autoregression, and high-dimensional "
                        "dependence-graph connectivity."
                    ),
                    proof_strategy=(
                        "Use the independent-edge SBM baseline as a release-gated surrogate, then add "
                        "graph U-statistics, dependency-graph CLTs, signed-triad functionals, and "
                        "time-varying network autoregression primitives."
                    ),
                    status="FORMAL_GAP",
                    required_primitives=(
                        "mixed_membership_network_model",
                        "signed_network_balance_functional",
                        "network_autoregression_likelihood",
                        "dependency_graph_clt",
                        "graph_functional_delta_method",
                    ),
                    proof_obligations=("finite_union_budget_control", "markov_inequality"),
                ),
            ]
            procedures = [
                CandidateProcedure(
                    id="sbm_edge_density_spectral",
                    name="SBM edge-density and spectral community estimator",
                    role="estimator",
                    formula=(
                        "rho_hat = 2/(n(n-1)) * sum_{i<j} A_ij; community labels are "
                        "estimated from the sign/median split of the leading centered-adjacency eigenvector."
                    ),
                    informal_derivation=(
                        "Treat each unordered edge as a Bernoulli indicator. Averaging all edge "
                        "indicators estimates the population edge density, with a plug-in binomial "
                        "standard error for the release surrogate. Centering the adjacency matrix "
                        "removes the global-density direction; when within-block and between-block "
                        "edge probabilities are separated, the leading eigenvector carries the "
                        "community signal. The formal trace proves only reusable probability subclaims "
                        "and leaves graph-matrix concentration and frontier network models as gaps."
                    ),
                    algorithm="sbm_edge_density_spectral",
                    theorem_goals=tuple(goal.id for goal in goals),
                    simulation_design=(
                        "Simulate a dense balanced two-block stochastic block model, estimate edge "
                        "density and community labels, and evaluate edge-density bias/RMSE/coverage, "
                        "SE calibration, and label recovery accuracy."
                    ),
                    limitations=(
                        "v0 uses a dense two-block SBM rather than mixed-membership, signed, dynamic, or graph-dependent observation models",
                        "Davis-Kahan, matrix concentration, graph CLTs, and network-autoregression theory remain formal gaps",
                    ),
                )
            ]
            return procedures, goals
        if problem.problem_class == "high_dimensional_pca_inference":
            goals = [
                TheoremGoal(
                    id="spiked_pca_population_target",
                    title="Leading eigenvector identifies the signal direction",
                    informal_statement=(
                        "In a rank-one spiked covariance model with a positive eigengap, "
                        "the leading population eigenvector is the latent signal direction up to sign."
                    ),
                    proof_strategy=(
                        "Formalize symmetric covariance operators, eigengaps, and the rank-one perturbation "
                        "spectrum; reduce the leading eigenspace to the span of the spike vector."
                    ),
                    status="FORMAL_GAP",
                    required_primitives=(
                        "symmetric_covariance_operator",
                        "rank_one_spike_matrix",
                        "eigengap_definition",
                        "spectral_theorem_finite_dimensional",
                        "leading_eigenspace_identification",
                    ),
                    proof_obligations=("variance_nonneg",),
                ),
                TheoremGoal(
                    id="spiked_pca_high_dimensional_recovery",
                    title="Sample PCA recovers the leading subspace under eigengap and p/n control",
                    informal_statement=(
                        "The sample leading eigenvector has nontrivial alignment with the population signal "
                        "when the spike is separated and the high-dimensional noise is controlled."
                    ),
                    proof_strategy=(
                        "Combine covariance concentration, Davis-Kahan perturbation bounds, and "
                        "high-dimensional random-matrix control for the sample covariance spectrum."
                    ),
                    status="FORMAL_GAP",
                    required_primitives=(
                        "sample_covariance_concentration",
                        "davis_kahan_sin_theta",
                        "high_dimensional_random_matrix_bound",
                        "eigenvector_alignment_metric",
                        "p_over_n_asymptotic_regime",
                    ),
                ),
            ]
            procedures = [
                CandidateProcedure(
                    id="spiked_pca_top_eigenvector",
                    name="Top-eigenvector PCA for a rank-one spiked covariance model",
                    role="estimator",
                    formula=(
                        "S = n^{-1} X^T X; v_hat is a unit eigenvector of S for its largest eigenvalue; "
                        "report alignment |<v_hat, v>| and subspace error sqrt(1-alignment^2)."
                    ),
                    informal_derivation=(
                        "A rank-one spike creates a separated leading population eigenvalue. "
                        "The sample covariance estimates the population covariance, and perturbation "
                        "theory turns covariance error into an eigenvector-angle bound."
                    ),
                    algorithm="spiked_pca",
                    theorem_goals=tuple(goal.id for goal in goals),
                    simulation_design=(
                        "Simulate Gaussian high-dimensional observations from covariance I + lambda vv^T, "
                        "estimate the top eigenvector, and measure alignment and angle error."
                    ),
                    limitations=(
                        "v0 simulator is a rank-one Gaussian spiked model, not mixed-membership or tensor SDR",
                        "Davis-Kahan and random-matrix concentration remain formal gaps",
                    ),
                )
            ]
            return procedures, goals
        if problem.problem_class == "high_dimensional_latent_structure_inference":
            goals = [
                TheoremGoal(
                    id="latent_simplex_membership_identifiability",
                    title="Latent simplex membership is identifiable up to label permutation",
                    informal_statement=(
                        "In a grade-of-membership factor model with separated item profiles and enough "
                        "near-anchor observations, simplex-constrained membership weights are identifiable "
                        "up to permutation of the latent classes."
                    ),
                    proof_strategy=(
                        "Formalize simplex-valued memberships, profile matrices, and permutation invariance. "
                        "Use finite-sample mean/variance facts for executable surrogates now; anchor separation, "
                        "local dependence, and tensor quasi-factor identifiability remain formal gaps."
                    ),
                    status="FORMAL_GAP",
                    required_primitives=(
                        "simplex_valued_membership",
                        "profile_matrix_separation",
                        "label_permutation_equivalence",
                        "anchor_observation_condition",
                        "local_dependence_control",
                    ),
                    proof_obligations=(
                        "prob_measure_univ",
                        "finite_sample_mean_unbiased",
                        "finite_sample_mean_variance_indep",
                        "variance_nonneg",
                    ),
                ),
                TheoremGoal(
                    id="sufficient_dimension_association_selection_validity",
                    title="Sufficient-dimension association screening validity",
                    informal_statement=(
                        "A screening statistic based on marginal nonlinear association should recover "
                        "coordinates involved in a low-dimensional sufficient reduction under signal "
                        "separation and nuisance control."
                    ),
                    proof_strategy=(
                        "Reduce the screening statistic to finite empirical averages and Chebyshev/union "
                        "bounds for deviations, while treating SDR central-subspace existence and "
                        "high-dimensional model-selection consistency as formal gaps."
                    ),
                    status="FORMAL_GAP",
                    required_primitives=(
                        "sufficient_dimension_association_target",
                        "nonlinear_association_screening_statistic",
                        "central_subspace_definition",
                        "high_dimensional_union_control",
                        "selection_consistency",
                    ),
                    proof_obligations=(
                        "finite_sample_mean_unbiased",
                        "finite_sample_mean_variance_indep",
                        "finite_sample_mean_chebyshev_indep",
                        "finite_union_budget_control",
                        "simultaneous_coverage_of_union_error_bound",
                    ),
                ),
                TheoremGoal(
                    id="tensor_multilinear_reduction_consistency",
                    title="Tensor multilinear reduction consistency",
                    informal_statement=(
                        "For tensor-valued predictors with a multilinear low-rank reduction, a separable "
                        "screening or alternating-estimation surrogate should recover active tensor modes "
                        "when signal strength dominates high-dimensional noise."
                    ),
                    proof_strategy=(
                        "Represent tensor predictors as vectorized finite arrays for v0, use finite union "
                        "control over candidate coordinates, and leave quadratic exponential-family inverse "
                        "models and multilinear manifold asymptotics as library targets."
                    ),
                    status="FORMAL_GAP",
                    required_primitives=(
                        "tensor_covariate_operator",
                        "multilinear_low_rank_reduction",
                        "quadratic_exponential_family_inverse_model",
                        "modewise_selection_consistency",
                        "tensor_dimension_asymptotics",
                    ),
                    proof_obligations=(
                        "finite_union_bound",
                        "finite_union_budget_control",
                        "variance_nonneg",
                        "markov_inequality",
                    ),
                ),
            ]
            procedures = [
                CandidateProcedure(
                    id="simplex_factor_membership_estimator",
                    name="Simplex-constrained spectral membership estimator",
                    role="estimator",
                    formula=(
                        "Given high-dimensional item responses X, estimate archetype profiles B_hat "
                        "from extreme spectral scores and compute W_hat = Pi_simplex(X B_hat^T "
                        "(B_hat B_hat^T)^{-1})."
                    ),
                    informal_derivation=(
                        "Grade-of-membership models encode each subject as a convex combination of "
                        "latent item-response profiles. Near-anchor observations expose simplex vertices; "
                        "least-squares weights projected back to the simplex give a concrete membership "
                        "estimator. The v0 simulation checks membership RMSE and label recovery, while "
                        "formal identifiability and local-dependence theory remain gaps."
                    ),
                    algorithm="latent_simplex_membership",
                    theorem_goals=tuple(goal.id for goal in goals),
                    simulation_design=(
                        "Simulate simplex-valued memberships, separated latent profiles, and noisy "
                        "high-dimensional item responses; estimate memberships by spectral archetypes and "
                        "evaluate permutation-aligned RMSE, coverage, and top-membership classification."
                    ),
                    limitations=(
                        "v0 uses continuous noisy item scores rather than full polytomous likelihoods",
                        "anchor conditions, local dependence, and quasi-tensor membership rates remain formal gaps",
                    ),
                ),
                CandidateProcedure(
                    id="nonlinear_dimension_association_screen",
                    name="Nonlinear sufficient-dimension association screen",
                    role="estimator",
                    formula=(
                        "Score each coordinate by absolute linear/quadratic association with Y plus its "
                        "largest pairwise interaction score; select the top coordinates as the estimated "
                        "sufficient-dimension support."
                    ),
                    informal_derivation=(
                        "If Y depends on a low-dimensional nonlinear index of high-dimensional or tensor "
                        "predictors, coordinates in the reduction should show linear, quadratic, or "
                        "interaction association. A screening statistic gives a controlled executable "
                        "surrogate for SDR/tensor inference while central-subspace and multilinear inverse "
                        "model theory are left explicit."
                    ),
                    algorithm="dimension_association_screening",
                    theorem_goals=tuple(goal.id for goal in goals),
                    simulation_design=(
                        "Simulate high-dimensional Gaussian predictors with nonlinear main and interaction "
                        "effects on a sparse sufficient-reduction support, screen coordinates by association, "
                        "and evaluate active-support recall, false discovery, subspace alignment, RMSE, and coverage."
                    ),
                    limitations=(
                        "v0 uses vectorized predictors and simple screening rather than a full tensor inverse model",
                        "central-subspace uniqueness, high-dimensional post-selection inference, and tensor-mode rates remain gaps",
                    ),
                ),
            ]
            return procedures, goals
        if problem.problem_class == "extreme_tail_quantile_inference":
            goals = [
                TheoremGoal(
                    id="hill_tail_index_consistency",
                    title="Hill estimator consistency for a regularly varying tail",
                    informal_statement=(
                        "For an intermediate threshold sequence k, the Hill estimator converges "
                        "to the extreme-value tail index gamma under regular variation."
                    ),
                    proof_strategy=(
                        "Formalize order statistics, regular variation, intermediate sequences, "
                        "and the log-excess empirical mean over the top k observations."
                    ),
                    status="FORMAL_GAP",
                    required_primitives=(
                        "order_statistics",
                        "regular_variation",
                        "intermediate_threshold_sequence",
                        "log_excess_empirical_mean",
                        "hill_estimator_consistency",
                    ),
                    proof_obligations=(
                        "markov_inequality",
                        "prob_compl",
                        "first_borel_cantelli_limsup_zero",
                        "second_borel_cantelli_limsup_one",
                    ),
                ),
                TheoremGoal(
                    id="weissman_high_quantile_consistency",
                    title="Weissman high-quantile consistency",
                    informal_statement=(
                        "Plugging the Hill tail-index estimator into the Weissman extrapolation "
                        "yields a consistent high-quantile estimator under second-order tail control."
                    ),
                    proof_strategy=(
                        "Combine Hill consistency with tail quantile regular variation and control "
                        "the extrapolation error at probability levels p_n approaching one."
                    ),
                    status="FORMAL_GAP",
                    required_primitives=(
                        "tail_quantile_function",
                        "weissman_extrapolation",
                        "second_order_regular_variation",
                        "extreme_probability_sequence",
                        "tail_quantile_continuous_mapping",
                    ),
                ),
            ]
            procedures = [
                CandidateProcedure(
                    id="hill_weissman_tail_quantile",
                    name="Hill tail-index estimator with Weissman high-quantile extrapolation",
                    role="estimator",
                    formula=(
                        "gamma_hat = k^{-1} sum_{j=1}^k log X_(n-j+1) - log X_(n-k); "
                        "q_hat_p = X_(n-k) * (k/(n(1-p)))^{gamma_hat}."
                    ),
                    informal_derivation=(
                        "For a Pareto or regularly varying tail, exceedances over a high threshold "
                        "are approximately log-linear. The Hill statistic estimates the log-tail "
                        "slope, and the Weissman formula extrapolates from the threshold to a rarer quantile."
                    ),
                    algorithm="hill_tail_quantile",
                    theorem_goals=tuple(goal.id for goal in goals),
                    simulation_design=(
                        "Simulate iid Pareto data, estimate gamma and a 0.99 quantile from the top k order "
                        "statistics, and evaluate bias, RMSE, SE calibration, and quantile coverage."
                    ),
                    limitations=(
                        "v0 simulator uses an exact Pareto baseline, not general second-order regular variation",
                        "order-statistic asymptotic theory remains a formal gap",
                    ),
                )
            ]
            return procedures, goals
        goals = [
            TheoremGoal(
                id="manual_theory_development_required",
                title="Manual theory development required",
                informal_statement="The deterministic v0 planner cannot normalize this open problem.",
                proof_strategy="Route to human/LLM research planning before formal proof or simulation.",
                status="FORMAL_GAP",
                required_primitives=("manual_problem_formalization", "domain_specific_theory_planning"),
            )
        ]
        return [], goals


PROVABLE_SUBCLAIMS: dict[str, tuple[str, ...]] = {
    "semiparametric_causal_ate": (
        "event_indicator_expectation",
        "prob_measure_univ",
        "integral_of_constant",
        "aipw_score_expectation_decompose",
    ),
    "distribution_free_conformal_prediction": (
        "prob_measure_univ",
        "prob_compl",
        "coverage_lower_bound_of_complement_error",
        "event_probability_mono",
        "finite_union_bound",
        "finite_union_budget_control",
        "simultaneous_coverage_of_union_error_bound",
    ),
    "right_censored_survival_inference": (
        "event_indicator_expectation",
        "prob_compl",
        "markov_inequality",
    ),
    "robust_mean_inference": (
        "mean2_estimator_expectation",
        "mean2_estimator_variance_indep",
        "finite_sample_mean_unbiased",
        "finite_sample_mean_variance_indep",
        "finite_sample_mean_chebyshev_indep",
        "block_estimator_chebyshev_bound",
        "estimator_error_chebyshev",
        "mean2_estimator_chebyshev_indep",
        "variance_nonneg",
        "markov_inequality",
    ),
    "differential_privacy_learning": (
        "prob_measure_univ",
        "integral_of_constant",
        "mean2_estimator_expectation",
        "mean2_estimator_variance_indep",
        "finite_sample_mean_unbiased",
        "finite_sample_mean_variance_indep",
        "finite_sample_mean_chebyshev_indep",
        "noised_estimator_unbiased",
        "noised_estimator_variance_indep",
        "noised_estimator_chebyshev_indep",
        "estimator_error_chebyshev",
        "mean2_estimator_chebyshev_indep",
        "variance_nonneg",
        "markov_inequality",
    ),
    "nonparametric_regression_inference": (
        "mean2_estimator_expectation",
        "affine_estimator_expectation",
        "affine_estimator_variance",
        "finite_sample_mean_unbiased",
        "finite_sample_mean_variance_indep",
        "finite_sample_mean_chebyshev_indep",
        "estimator_error_chebyshev",
        "variance_nonneg",
        "markov_inequality",
    ),
    "bayesian_posterior_calibration": (
        "prob_measure_univ",
        "integral_of_constant",
        "affine_estimator_expectation",
        "affine_estimator_variance",
        "finite_sample_mean_unbiased",
        "finite_sample_mean_variance_indep",
        "finite_sample_mean_chebyshev_indep",
        "estimator_error_chebyshev",
        "variance_nonneg",
        "prob_compl",
        "wald_interval_miscoverage_iff_abs_error_gt",
        "coverage_lower_bound_of_complement_error",
        "markov_inequality",
    ),
    "geometric_spatial_point_process_inference": (
        "prob_measure_univ",
        "integral_of_constant",
        "event_indicator_expectation",
        "finite_sample_mean_unbiased",
        "finite_sample_mean_variance_indep",
        "finite_sample_mean_chebyshev_indep",
        "estimator_error_chebyshev",
        "variance_nonneg",
        "markov_inequality",
        "finite_union_bound",
        "finite_union_budget_control",
        "simultaneous_coverage_of_union_error_bound",
    ),
    "measurement_bias_ranking_inference": (
        "affine_estimator_expectation",
        "affine_estimator_variance",
        "finite_sample_mean_unbiased",
        "finite_sample_mean_variance_indep",
        "finite_sample_mean_chebyshev_indep",
        "integral_of_constant",
        "estimator_error_chebyshev",
        "finite_family_absolute_error_union_control",
        "simultaneous_coverage_of_union_error_bound",
        "pairwise_top_rank_correct_of_separation",
        "variance_nonneg",
        "prob_compl",
    ),
    "design_based_variance_inference": (
        "mean2_estimator_expectation",
        "mean2_estimator_unbiased",
        "mean2_estimator_variance_indep",
        "finite_sample_mean_unbiased",
        "finite_sample_mean_variance_indep",
        "finite_sample_mean_chebyshev_indep",
        "estimator_error_chebyshev",
        "mean2_estimator_chebyshev_indep",
        "variance_nonneg",
        "markov_inequality",
    ),
    "experimental_design_optimization": (
        "prob_measure_univ",
        "integral_of_constant",
        "event_probability_mono",
        "finite_union_bound",
        "finite_union_budget_control",
        "variance_nonneg",
    ),
    "heteroskedastic_regression_inference": (
        "mean2_estimator_expectation",
        "mean2_estimator_unbiased",
        "mean2_estimator_variance_indep",
        "finite_sample_mean_unbiased",
        "finite_sample_mean_variance_indep",
        "finite_sample_mean_chebyshev_indep",
        "estimator_error_chebyshev",
        "wald_interval_contains_iff_abs_error",
        "wald_interval_miscoverage_iff_abs_error_gt",
        "coverage_lower_bound_of_complement_error",
        "mean2_estimator_chebyshev_indep",
        "variance_nonneg",
    ),
    "multiple_testing_fdr": (
        "prob_measure_univ",
        "prob_compl",
        "event_probability_mono",
        "independent_event_inter_probability",
        "finite_union_bound",
        "finite_union_budget_control",
        "markov_inequality",
    ),
    "sequential_anytime_inference": (
        "prob_measure_univ",
        "event_indicator_expectation",
        "finite_event_indicator_mean_unbiased",
        "event_probability_mono",
        "independent_event_inter_probability",
        "finite_union_bound",
        "finite_horizon_type1_union_control",
        "finite_union_budget_control",
        "markov_inequality",
        "adapted_hitting_after_is_stopping_time",
        "first_borel_cantelli_limsup_zero",
    ),
    "sequential_changepoint_inference": (
        "prob_measure_univ",
        "prob_compl",
        "event_probability_mono",
        "finite_union_bound",
        "finite_union_budget_control",
        "coverage_lower_bound_of_complement_error",
        "simultaneous_coverage_of_union_error_bound",
        "markov_inequality",
    ),
    "network_graph_inference": (
        "event_indicator_expectation",
        "finite_event_indicator_mean_unbiased",
        "finite_sample_mean_unbiased",
        "finite_sample_mean_variance_indep",
        "finite_sample_mean_chebyshev_indep",
        "finite_union_budget_control",
        "variance_nonneg",
        "markov_inequality",
    ),
    "high_dimensional_pca_inference": ("variance_nonneg", "variance_indep_add"),
    "high_dimensional_latent_structure_inference": (
        "prob_measure_univ",
        "finite_sample_mean_unbiased",
        "finite_sample_mean_variance_indep",
        "finite_sample_mean_chebyshev_indep",
        "finite_union_bound",
        "finite_union_budget_control",
        "simultaneous_coverage_of_union_error_bound",
        "variance_nonneg",
        "markov_inequality",
    ),
    "extreme_tail_quantile_inference": (
        "prob_compl",
        "markov_inequality",
        "first_borel_cantelli_limsup_zero",
        "second_borel_cantelli_limsup_one",
        "variance_nonneg",
    ),
}


def _formalization_status(check: Any) -> str:
    if not check.ok:
        return "verification_failed"
    if getattr(check, "kernel_verified", False):
        return "kernel_verified_proof"
    return "mock_verified_proof"


class FormalSubclaimProver:
    def __init__(
        self,
        *,
        verifier: ProofVerifier | None = None,
        retriever: ProofBankRetriever | None = None,
        formal_source_retriever: Any | None = None,
    ) -> None:
        self.verifier = verifier or MockProofVerifier()
        self.retriever = retriever or ProofBankRetriever()
        self._formal_source_retriever = formal_source_retriever

    def formal_source_retriever(self) -> Any:
        if self._formal_source_retriever is None:
            self._formal_source_retriever = FormalSourceRetriever()
        return self._formal_source_retriever

    async def prove(self, problem: ResearchProblemSpec, theorem_goals: list[TheoremGoal]) -> list[FormalSubclaim]:
        subclaims: list[FormalSubclaim] = []
        for obligation_id in PROVABLE_SUBCLAIMS.get(problem.problem_class, ()):
            obligation = get_obligation(obligation_id)
            hits = self.retriever.retrieve(
                RetrievalQuery(obligation.english, tags=obligation.tags),
                candidates=all_obligations(),
            )
            check = await self.verifier.verify(obligation, obligation.proof_body, hits)
            subclaims.append(
                FormalSubclaim(
                    id=f"{problem.question_id}:{obligation.id}",
                    title=obligation.title,
                    status="PROVED" if check.ok else "FAILED",
                    claim=obligation.english,
                    claim_type="lean_obligation",
                    proof_obligation_id=obligation.id,
                    lean_statement=obligation.formal_statement,
                    formalization_status=_formalization_status(check),
                    verifier=check.verifier,
                    verification_strength=check.verification_strength,
                    kernel_verified=check.kernel_verified,
                    elapsed_ms=check.elapsed_ms,
                    errors=check.errors,
                    gap_reason=None if check.ok else "registered Mathlib-backed subclaim failed verifier",
                    proof_dependencies=obligation.depends_on,
                )
            )
        for goal in theorem_goals:
            if goal.status == "FORMAL_GAP":
                source_retriever = self.formal_source_retriever()
                formal_source_hits = source_retriever.search(
                    _formal_source_query(problem, goal),
                    k=5,
                )
                primitive_formal_source_hits = {
                    primitive: [
                        _formal_source_hit_payload(hit)
                        for hit in source_retriever.search(
                            _formal_source_primitive_query(problem, goal, primitive),
                            k=3,
                        )
                    ]
                    for primitive in goal.required_primitives
                }
                subclaims.append(
                    FormalSubclaim(
                        id=f"{problem.question_id}:{goal.id}",
                        title=goal.title,
                        status="FORMAL_GAP",
                        claim=goal.informal_statement,
                        claim_type="theory_gap",
                        lean_statement=_lean_gap_skeleton(
                            problem,
                            goal,
                            formal_source_hits,
                            primitive_formal_source_hits,
                        ),
                        formalization_status="lean_skeleton_with_placeholder_assumptions",
                        gap_reason=(
                            "Requires new statistics formalization beyond the current proof bank: "
                            f"{goal.proof_strategy}"
                        ),
                        formal_source_hits=[_formal_source_hit_payload(hit) for hit in formal_source_hits],
                        primitive_formal_source_hits=primitive_formal_source_hits,
                    )
                )
        return subclaims


class ResearchSimulator:
    def __init__(self, *, n_runs: int = 100, seed: int = 20260528) -> None:
        self.n_runs = n_runs
        self.seed = seed

    def run(self, problem: ResearchProblemSpec, procedures: list[CandidateProcedure]) -> list[ResearchSimulation]:
        rows: list[ResearchSimulation] = []
        for i, procedure in enumerate(procedures):
            rng = np.random.default_rng(self.seed + 1009 * i)
            if procedure.algorithm == "oracle_aipw":
                rows.append(self._oracle_aipw(procedure, rng))
            elif procedure.algorithm == "split_conformal_poly":
                rows.append(self._split_conformal(procedure, rng))
            elif procedure.algorithm == "kaplan_meier_fixed_time":
                rows.append(self._kaplan_meier_fixed_time(procedure, rng))
            elif procedure.algorithm == "median_of_means_mean":
                rows.append(self._median_of_means_mean(procedure, rng))
            elif procedure.algorithm == "dp_gaussian_mean":
                rows.append(self._dp_gaussian_mean(procedure, rng))
            elif procedure.algorithm == "sieve_ensemble_regression":
                rows.append(self._sieve_ensemble_regression(procedure, rng))
            elif procedure.algorithm == "normal_conjugate_posterior_mean":
                rows.append(self._normal_conjugate_posterior_mean(procedure, rng))
            elif procedure.algorithm == "measurement_bias_adjusted_ranking":
                rows.append(self._measurement_bias_adjusted_ranking(procedure, rng))
            elif procedure.algorithm == "neyman_conservative_variance":
                rows.append(self._neyman_conservative_variance(procedure, rng))
            elif procedure.algorithm == "sbm_edge_density_spectral":
                rows.append(self._sbm_edge_density_spectral(procedure, rng))
            elif procedure.algorithm == "covariate_balance_maximin_design":
                rows.append(self._covariate_balance_maximin_design(procedure, rng))
            elif procedure.algorithm == "metric_graph_kernel_smoother":
                rows.append(self._metric_graph_kernel_smoother(procedure, rng))
            elif procedure.algorithm == "point_process_intensity_contrast":
                rows.append(self._point_process_intensity_contrast(procedure, rng))
            elif procedure.algorithm == "ols_hc1":
                rows.append(self._ols_hc1(procedure, rng))
            elif procedure.algorithm == "benjamini_hochberg":
                rows.append(self._benjamini_hochberg(procedure, rng))
            elif procedure.algorithm == "bernoulli_lr_eprocess":
                rows.append(self._bernoulli_lr_eprocess(procedure, rng))
            elif procedure.algorithm == "cusum_changepoint_detector":
                rows.append(self._cusum_changepoint_detector(procedure, rng))
            elif procedure.algorithm == "spiked_pca":
                rows.append(self._spiked_pca(procedure, rng))
            elif procedure.algorithm == "latent_simplex_membership":
                rows.append(self._latent_simplex_membership(procedure, rng))
            elif procedure.algorithm == "dimension_association_screening":
                rows.append(self._dimension_association_screening(procedure, rng))
            elif procedure.algorithm == "hill_tail_quantile":
                rows.append(self._hill_tail_quantile(procedure, rng))
            else:
                rows.append(
                    ResearchSimulation(
                        procedure_id=procedure.id,
                        design="No simulator registered for this procedure.",
                        metrics={"n_runs": float(self.n_runs), "n_failed": float(self.n_runs)},
                        passed=False,
                        feedback="unsupported simulation design",
                    )
                )
        return [self._with_stress_test_ledger(problem, row) for row in rows]

    def _with_stress_test_ledger(
        self,
        problem: ResearchProblemSpec,
        row: ResearchSimulation,
    ) -> ResearchSimulation:
        stress_tests = tuple(problem.stress_tests)
        stress_test_metrics = (
            {
                stress_test: self._stress_test_metric(stress_test, row.metrics)
                for stress_test in stress_tests
            }
            if stress_tests
            else {}
        )
        with_stress_tests = replace(
            row,
            stress_tests=stress_tests,
            stress_test_metrics=stress_test_metrics,
        )
        return replace(
            with_stress_tests,
            diagnosis=self._diagnose_simulation(problem, with_stress_tests),
        )

    def _stress_test_metric(self, stress_test: str, metrics: dict[str, float]) -> dict[str, float]:
        key, threshold, direction = self._select_stress_metric(stress_test, metrics)
        value = float(metrics.get(key, 0.0))
        if direction == "min":
            flagged = value < threshold
        elif direction == "max":
            flagged = value > threshold
        else:
            flagged = abs(value) > threshold
        return {
            "covered": 1.0,
            "stress_flag": 1.0 if flagged else 0.0,
            "primary_value": value,
            "threshold": float(threshold),
        }

    def _select_stress_metric(self, stress_test: str, metrics: dict[str, float]) -> tuple[str, float, str]:
        text = stress_test.lower()
        if "coverage_95" in metrics and any(token in text for token in ("coverage", "calibration", "censor", "conformal")):
            return "coverage_95", 0.90, "min"
        if "coverage_95" in metrics and any(token in text for token in ("small", "threshold", "tail", "later", "censor")):
            return "coverage_95", 0.90, "min"
        if "empirical_fdr" in metrics and any(token in text for token in ("fdr", "false", "null", "correlated")):
            return "empirical_fdr", 0.12, "max"
        if "type1_error" in metrics and any(token in text for token in ("optional", "null", "stopping", "monitor")):
            return "type1_error", 0.08, "max"
        if "power" in metrics and any(token in text for token in ("weak", "alternative", "effect", "power")):
            return "power", 0.50, "min"
        if "detection_rate" in metrics and any(token in text for token in ("shift", "change", "detection")):
            return "detection_rate", 0.85, "min"
        if "false_alarm_rate" in metrics and any(token in text for token in ("stopping", "null", "post-detection")):
            return "false_alarm_rate", 0.12, "max"
        if "mean_absolute_localization_error" in metrics and any(token in text for token in ("localization", "measurement", "change")):
            return "mean_absolute_localization_error", 18.0, "max"
        if "mean_alignment" in metrics and any(token in text for token in ("eigengap", "alignment", "p/n", "pca")):
            return "mean_alignment", 0.65, "min"
        if "mean_angle_error_rad" in metrics and "angle" in text:
            return "mean_angle_error_rad", 0.80, "max"
        if "mean_subspace_error" in metrics and any(token in text for token in ("subspace", "heavy-tailed coordinates")):
            return "mean_subspace_error", 0.80, "max"
        if "membership_rmse" in metrics and any(token in text for token in ("latent", "membership", "separation", "local dependence")):
            return "membership_rmse", 0.25, "max"
        if "active_recall" in metrics and any(token in text for token in ("nuisance", "dimension", "predictor", "selection")):
            return "active_recall", 0.80, "min"
        if "selection_accuracy" in metrics and any(token in text for token in ("latent", "membership", "selection", "tensor", "dependence")):
            return "selection_accuracy", 0.80, "min"
        if "mean_community_accuracy" in metrics and any(token in text for token in ("community", "separation", "sparse", "graph", "network", "degree")):
            return "mean_community_accuracy", 0.80, "min"
        if "edge_density_rmse" in metrics and any(token in text for token in ("sparse", "density", "degree", "graph", "network")):
            return "edge_density_rmse", 0.08, "max"
        if "relative_bias" in metrics and any(token in text for token in ("bias", "misspec", "prior", "curvature", "nonlinear")):
            return "relative_bias", 0.20, "abs"
        if "bias" in metrics and any(token in text for token in ("bias", "misspec", "prior", "curvature", "nonlinear")):
            return "bias", 0.20, "abs"
        if "se_ratio" in metrics and any(token in text for token in ("variance", "leverage", "calibration", "hetero")):
            return "se_ratio", 1.35, "max"
        if "rmse" in metrics and any(token in text for token in ("heavy", "outlier", "contamination", "tail", "threshold")):
            return "rmse", 1.00, "max"
        if "rmse_center" in metrics and any(token in text for token in ("nonlinear", "heavy", "calibration")):
            return "rmse_center", 1.50, "max"
        if "tail_index_rmse" in metrics and any(token in text for token in ("tail", "pareto", "threshold")):
            return "tail_index_rmse", 0.60, "max"
        if "high_quantile_coverage" in metrics and any(token in text for token in ("quantile", "tail")):
            return "high_quantile_coverage", 0.85, "min"
        if "mean_conservativeness_ratio" in metrics and any(token in text for token in ("assignment", "design", "conservative")):
            return "mean_conservativeness_ratio", 1.00, "min"
        if "space_filling_ratio" in metrics and any(token in text for token in ("space", "run budget", "design")):
            return "space_filling_ratio", 1.05, "min"
        if "balance_improvement" in metrics and any(token in text for token in ("balance", "covariate", "tied")):
            return "balance_improvement", 1.15, "min"
        if "mean_standardized_imbalance" in metrics and any(token in text for token in ("balance", "covariate", "assignment")):
            return "mean_standardized_imbalance", 0.35, "max"
        if "field_rmse" in metrics and any(token in text for token in ("correlation", "graph", "field", "sparse")):
            return "field_rmse", 0.24, "max"
        if "field_coverage_95" in metrics and any(token in text for token in ("correlation", "graph", "field", "coverage")):
            return "field_coverage_95", 0.88, "min"
        if "intensity_coverage_95" in metrics and any(token in text for token in ("intensity", "spike", "palm", "point")):
            return "intensity_coverage_95", 0.88, "min"
        if "selection_accuracy" in metrics and any(token in text for token in ("intensity", "spike", "selection", "point")):
            return "selection_accuracy", 0.80, "min"
        if "intensity_relative_bias" in metrics and any(token in text for token in ("intensity", "spike", "inhomogeneous")):
            return "intensity_relative_bias", 0.12, "abs"
        if "mean_privacy_noise_sd" in metrics and any(token in text for token in ("epsilon", "privacy", "composed")):
            return "mean_privacy_noise_sd", 0.00, "min"
        if "mean_clipping_fraction" in metrics and any(token in text for token in ("clipping", "private", "outlier")):
            return "mean_clipping_fraction", 0.40, "max"
        if "coverage_95" in metrics:
            return "coverage_95", 0.90, "min"
        if "relative_bias" in metrics:
            return "relative_bias", 0.20, "abs"
        if "bias" in metrics:
            return "bias", 0.20, "abs"
        if "rmse" in metrics:
            return "rmse", 1.00, "max"
        if "n_failed" in metrics:
            return "n_failed", 0.0, "max"
        key = next(iter(metrics), "n_runs")
        return key, 0.0, "min"

    def _diagnose_simulation(
        self,
        problem: ResearchProblemSpec,
        row: ResearchSimulation,
    ) -> SimulationDiagnosis:
        metrics = row.metrics
        nonfinite_metrics = sorted(
            key for key, value in metrics.items()
            if not isinstance(value, (int, float)) or not math.isfinite(float(value))
        )
        failed_stress_tests = tuple(
            name
            for name, values in row.stress_test_metrics.items()
            if float(values.get("stress_flag", 0.0)) > 0.5
        )
        failed_diagnostics = tuple(
            diagnostic
            for diagnostic in problem.diagnostics
            if self._diagnostic_failed(diagnostic, metrics)
        )
        n_runs = float(metrics.get("n_runs", self.n_runs))
        n_failed = float(metrics.get("n_failed", 0.0))
        evidence_keys = {
            "n_runs",
            "n_failed",
            "relative_bias",
            "bias",
            "coverage_95",
            "se_ratio",
            "rmse",
            "empirical_fdr",
            "type1_error",
            "power",
            "detection_rate",
            "false_alarm_rate",
            "mean_absolute_localization_error",
            "mean_detection_delay",
            "mean_alignment",
            "mean_community_accuracy",
            "edge_density_relative_bias",
            "edge_density_rmse",
            "tail_index_relative_bias",
            "quantile_relative_bias",
            "tail_index_coverage_95",
            "quantile_coverage_95",
            "high_quantile_coverage",
            "space_filling_ratio",
            "balance_improvement",
            "mean_standardized_imbalance",
            "assignment_acceptance_rate",
            "field_rmse",
            "field_coverage_95",
            "field_se_ratio",
            "intensity_relative_bias",
            "intensity_rmse",
            "intensity_coverage_95",
            "selection_accuracy",
            "membership_rmse",
            "membership_coverage_95",
            "top_membership_accuracy",
            "active_recall",
            "false_discovery_rate",
            "subspace_alignment",
        }
        metric_evidence = {
            key: float(value)
            for key, value in metrics.items()
            if key in evidence_keys and isinstance(value, (int, float)) and math.isfinite(float(value))
        }

        if row.passed and not nonfinite_metrics:
            return SimulationDiagnosis(
                status="OK",
                escalate_to="none",
                rationale="The registered simulation acceptance rule passed under the current Monte Carlo budget.",
                metric_evidence=metric_evidence,
            )
        if "unsupported" in row.feedback.lower() or row.design.lower().startswith("no simulator registered"):
            return SimulationDiagnosis(
                status="ENVIRONMENT_OR_DGP_ISSUE",
                escalate_to="simulator_environment",
                failed_diagnostics=failed_diagnostics or ("simulator_missing",),
                failed_stress_tests=failed_stress_tests,
                rationale="The simulator does not yet implement the requested DGP/procedure environment.",
                metric_evidence=metric_evidence,
            )
        if nonfinite_metrics or (n_runs > 0 and n_failed / n_runs > 0.10):
            return SimulationDiagnosis(
                status="IMPLEMENTATION_OR_NUMERICAL_ISSUE",
                escalate_to="algorithm_engineer",
                failed_diagnostics=failed_diagnostics or tuple(nonfinite_metrics) or ("numerical_failure",),
                failed_stress_tests=failed_stress_tests,
                rationale="The run produced non-finite metrics or too many failed replicates before judging theory.",
                metric_evidence=metric_evidence,
            )
        if n_runs - n_failed < 30:
            return SimulationDiagnosis(
                status="INSUFFICIENT_MC_PRECISION",
                escalate_to="rerun_more_mc",
                failed_diagnostics=failed_diagnostics or ("mc_precision",),
                failed_stress_tests=failed_stress_tests,
                rationale="Too few successful Monte Carlo replicates are available for a stable theory judgment.",
                metric_evidence=metric_evidence,
            )
        return SimulationDiagnosis(
            status="THEORY_OR_PROCEDURE_ISSUE",
            escalate_to="theory_developer",
            failed_diagnostics=failed_diagnostics or ("procedure_acceptance_rule",),
            failed_stress_tests=failed_stress_tests,
            rationale="The implementation ran, but statistical diagnostics or stress tests violated the registered acceptance rule.",
            metric_evidence=metric_evidence,
        )

    def _diagnostic_failed(self, diagnostic: str, metrics: dict[str, float]) -> bool:
        text = diagnostic.lower()
        if any(token in text for token in ("coverage", "calibration", "confidence")):
            coverage_keys = ("coverage_95", "high_quantile_coverage", "tail_index_coverage_95", "quantile_coverage_95")
            for key in coverage_keys:
                if key in metrics and math.isfinite(float(metrics[key])) and float(metrics[key]) < 0.88:
                    return True
        if "bias" in text:
            for key, threshold in (
                ("relative_bias", 0.10),
                ("tail_index_relative_bias", 0.12),
                ("quantile_relative_bias", 0.22),
                ("bias", 0.10),
            ):
                if key in metrics and math.isfinite(float(metrics[key])) and abs(float(metrics[key])) > threshold:
                    return True
        if any(token in text for token in ("se", "variance", "calibration")) and "se_ratio" in metrics:
            se_ratio = float(metrics["se_ratio"])
            if math.isfinite(se_ratio) and not 0.70 <= se_ratio <= 1.65:
                return True
        if "rmse" in text and "rmse" in metrics:
            rmse = float(metrics["rmse"])
            if math.isfinite(rmse) and rmse > 1.0:
                return True
        if any(token in text for token in ("fdr", "false discovery")) and "empirical_fdr" in metrics:
            target = float(metrics.get("target_fdr", 0.10))
            return math.isfinite(float(metrics["empirical_fdr"])) and float(metrics["empirical_fdr"]) > target + 0.03
        if any(token in text for token in ("optional", "type-i", "type1")) and "type1_error" in metrics:
            target = float(metrics.get("target_alpha", 0.05))
            return math.isfinite(float(metrics["type1_error"])) and float(metrics["type1_error"]) > target + 0.03
        if "power" in text and "power" in metrics:
            return math.isfinite(float(metrics["power"])) and float(metrics["power"]) < 0.55
        if "detection" in text and "detection_rate" in metrics:
            return math.isfinite(float(metrics["detection_rate"])) and float(metrics["detection_rate"]) < 0.85
        if "localization" in text and "mean_absolute_localization_error" in metrics:
            return (
                math.isfinite(float(metrics["mean_absolute_localization_error"]))
                and float(metrics["mean_absolute_localization_error"]) > 18.0
            )
        if "false" in text and "false_alarm_rate" in metrics:
            return math.isfinite(float(metrics["false_alarm_rate"])) and float(metrics["false_alarm_rate"]) > 0.12
        if any(token in text for token in ("alignment", "subspace", "pca")):
            if "mean_alignment" in metrics and math.isfinite(float(metrics["mean_alignment"])):
                return float(metrics["mean_alignment"]) < 0.65
            if "mean_subspace_error" in metrics and math.isfinite(float(metrics["mean_subspace_error"])):
                return float(metrics["mean_subspace_error"]) > 0.80
            if "subspace_alignment" in metrics and math.isfinite(float(metrics["subspace_alignment"])):
                return float(metrics["subspace_alignment"]) < 0.70
        if any(token in text for token in ("selection", "membership", "dimension", "tensor")):
            if "selection_accuracy" in metrics and math.isfinite(float(metrics["selection_accuracy"])):
                return float(metrics["selection_accuracy"]) < 0.80
            if "active_recall" in metrics and math.isfinite(float(metrics["active_recall"])):
                return float(metrics["active_recall"]) < 0.80
            if "membership_rmse" in metrics and math.isfinite(float(metrics["membership_rmse"])):
                return float(metrics["membership_rmse"]) > 0.25
        if "community" in text and "mean_community_accuracy" in metrics:
            return math.isfinite(float(metrics["mean_community_accuracy"])) and float(metrics["mean_community_accuracy"]) < 0.80
        if "edge_density" in text:
            if "edge_density_relative_bias" in metrics and math.isfinite(float(metrics["edge_density_relative_bias"])):
                return abs(float(metrics["edge_density_relative_bias"])) > 0.10
            if "edge_density_rmse" in metrics and math.isfinite(float(metrics["edge_density_rmse"])):
                return float(metrics["edge_density_rmse"]) > 0.08
        if "space" in text and "space_filling_ratio" in metrics:
            return math.isfinite(float(metrics["space_filling_ratio"])) and float(metrics["space_filling_ratio"]) < 1.05
        if "balance" in text:
            if "balance_improvement" in metrics and math.isfinite(float(metrics["balance_improvement"])):
                return float(metrics["balance_improvement"]) < 1.15
            if "mean_standardized_imbalance" in metrics and math.isfinite(float(metrics["mean_standardized_imbalance"])):
                return float(metrics["mean_standardized_imbalance"]) > 0.35
        if any(token in text for token in ("field", "graph", "prediction")):
            if "field_rmse" in metrics and math.isfinite(float(metrics["field_rmse"])):
                return float(metrics["field_rmse"]) > 0.24
            if "field_coverage_95" in metrics and math.isfinite(float(metrics["field_coverage_95"])):
                return float(metrics["field_coverage_95"]) < 0.88
        if any(token in text for token in ("intensity", "point", "palm", "selection")):
            if "intensity_relative_bias" in metrics and math.isfinite(float(metrics["intensity_relative_bias"])):
                return abs(float(metrics["intensity_relative_bias"])) > 0.12
            if "intensity_coverage_95" in metrics and math.isfinite(float(metrics["intensity_coverage_95"])):
                return float(metrics["intensity_coverage_95"]) < 0.88
            if "selection_accuracy" in metrics and math.isfinite(float(metrics["selection_accuracy"])):
                return float(metrics["selection_accuracy"]) < 0.80
        return False

    def _oracle_aipw(self, procedure: CandidateProcedure, rng: np.random.Generator) -> ResearchSimulation:
        n = 600
        tau = 1.0
        estimates: list[float] = []
        ses: list[float] = []
        covers = 0
        for _ in range(self.n_runs):
            x = rng.normal(size=n)
            e = np.clip(_sigmoid(-0.2 + 0.8 * x), 0.05, 0.95)
            a = rng.binomial(1, e)
            mu0 = 1.0 + x + 0.5 * x**2
            mu1 = mu0 + tau
            y = np.where(a == 1, mu1, mu0) + rng.normal(scale=1.0, size=n)
            phi = mu1 - mu0 + a / e * (y - mu1) - (1 - a) / (1 - e) * (y - mu0)
            est = float(np.mean(phi))
            se = float(np.std(phi, ddof=1) / math.sqrt(n))
            estimates.append(est)
            ses.append(se)
            covers += int(est - 1.96 * se <= tau <= est + 1.96 * se)
        metrics = _estimation_metrics(estimates, ses, tau, self.n_runs)
        passed = abs(metrics["relative_bias"]) < 0.08 and metrics["coverage_95"] >= 0.88
        return ResearchSimulation(
            procedure_id=procedure.id,
            design=procedure.simulation_design,
            metrics=metrics,
            passed=passed,
            feedback="oracle AIPW simulation passed" if passed else "oracle AIPW simulation flagged bias/coverage",
        )

    def _split_conformal(self, procedure: CandidateProcedure, rng: np.random.Generator) -> ResearchSimulation:
        alpha = 0.05
        coverages: list[float] = []
        widths: list[float] = []
        center_rmse: list[float] = []
        for _ in range(self.n_runs):
            x_train, y_train = _nonlinear_regression_sample(rng, 220)
            x_cal, y_cal = _nonlinear_regression_sample(rng, 140)
            x_test, y_test = _nonlinear_regression_sample(rng, 500)
            coef = np.linalg.lstsq(_poly_design(x_train), y_train, rcond=None)[0]
            cal_pred = _poly_design(x_cal) @ coef
            scores = np.abs(y_cal - cal_pred)
            q_idx = int(math.ceil((len(scores) + 1) * (1 - alpha))) - 1
            q = float(np.sort(scores)[min(max(q_idx, 0), len(scores) - 1)])
            pred = _poly_design(x_test) @ coef
            covered = np.abs(y_test - pred) <= q
            coverages.append(float(np.mean(covered)))
            widths.append(2 * q)
            center_rmse.append(float(np.sqrt(np.mean((y_test - pred) ** 2))))
        metrics = {
            "n_runs": float(self.n_runs),
            "target_coverage": 1 - alpha,
            "coverage_95": float(np.mean(coverages)),
            "coverage_sd": float(np.std(coverages, ddof=1)) if len(coverages) > 1 else 0.0,
            "miscoverage": float(1 - np.mean(coverages)),
            "average_width": float(np.mean(widths)),
            "rmse_center": float(np.mean(center_rmse)),
        }
        passed = metrics["coverage_95"] >= 0.92
        return ResearchSimulation(
            procedure_id=procedure.id,
            design=procedure.simulation_design,
            metrics=metrics,
            passed=passed,
            feedback="split conformal coverage passed" if passed else "split conformal coverage below tolerance",
        )

    def _kaplan_meier_fixed_time(self, procedure: CandidateProcedure, rng: np.random.Generator) -> ResearchSimulation:
        n = 700
        event_rate = 0.22
        censor_rate = 0.10
        t0 = 4.0
        true_survival = math.exp(-event_rate * t0)
        estimates: list[float] = []
        ses: list[float] = []
        censoring_fractions: list[float] = []
        failed = 0
        for _ in range(self.n_runs):
            event_time = rng.exponential(scale=1.0 / event_rate, size=n)
            censor_time = rng.exponential(scale=1.0 / censor_rate, size=n)
            observed_time = np.minimum(event_time, censor_time)
            event = event_time <= censor_time
            km, se = _kaplan_meier_at_time(observed_time, event, t0)
            if not math.isfinite(km) or not math.isfinite(se) or se <= 0:
                failed += 1
                continue
            estimates.append(km)
            ses.append(se)
            censoring_fractions.append(float(np.mean(~event)))
        metrics = _estimation_metrics(estimates, ses, true_survival, max(len(estimates), 1))
        metrics["n_runs"] = float(self.n_runs)
        metrics["n_failed"] = float(failed)
        metrics["target_time"] = float(t0)
        metrics["event_rate"] = float(event_rate)
        metrics["censor_rate"] = float(censor_rate)
        metrics["mean_censoring_fraction"] = float(np.mean(censoring_fractions)) if censoring_fractions else float("nan")
        passed = (
            abs(metrics["relative_bias"]) <= 0.08
            and metrics["coverage_95"] >= 0.88
            and 0.65 <= metrics["se_ratio"] <= 1.35
        )
        return ResearchSimulation(
            procedure_id=procedure.id,
            design=procedure.simulation_design,
            metrics=metrics,
            passed=passed,
            feedback=(
                "Kaplan-Meier fixed-time survival simulation passed"
                if passed
                else "Kaplan-Meier simulation flagged bias, coverage, or SE calibration"
            ),
        )

    def _median_of_means_mean(self, procedure: CandidateProcedure, rng: np.random.Generator) -> ResearchSimulation:
        n = 900
        n_blocks = 25
        theta = 0.0
        contamination_fraction = 0.06
        estimates: list[float] = []
        ses: list[float] = []
        observed_contamination: list[float] = []
        failed = 0
        for _ in range(self.n_runs):
            sample = theta + rng.standard_t(df=3, size=n) / math.sqrt(3.0)
            contaminated = rng.random(n) < contamination_fraction
            n_contaminated = int(np.sum(contaminated))
            if n_contaminated:
                signs = rng.choice(np.array([-1.0, 1.0]), size=n_contaminated)
                sample[contaminated] = theta + signs * (12.0 + rng.exponential(scale=2.0, size=n_contaminated))
            rng.shuffle(sample)
            estimate, block_means = _median_of_means(sample, n_blocks)
            if len(block_means) < 3 or not math.isfinite(estimate):
                failed += 1
                continue
            se = 1.15 * 1.2533 * float(np.std(block_means, ddof=1)) / math.sqrt(len(block_means))
            if not math.isfinite(se) or se <= 0:
                failed += 1
                continue
            estimates.append(estimate)
            ses.append(se)
            observed_contamination.append(n_contaminated / n)
        metrics = _estimation_metrics(estimates, ses, theta, max(len(estimates), 1))
        metrics["n_runs"] = float(self.n_runs)
        metrics["n_failed"] = float(failed)
        metrics["n_obs"] = float(n)
        metrics["n_blocks"] = float(n_blocks)
        metrics["target_contamination_fraction"] = float(contamination_fraction)
        metrics["mean_contamination_fraction"] = (
            float(np.mean(observed_contamination)) if observed_contamination else float("nan")
        )
        passed = (
            abs(metrics["bias"]) <= 0.08
            and metrics["coverage_95"] >= 0.88
            and metrics["rmse"] <= 0.20
            and 0.75 <= metrics["se_ratio"] <= 1.60
        )
        return ResearchSimulation(
            procedure_id=procedure.id,
            design=procedure.simulation_design,
            metrics=metrics,
            passed=passed,
            feedback=(
                "median-of-means robust mean simulation passed"
                if passed
                else "median-of-means simulation flagged bias, RMSE, coverage, or SE calibration"
            ),
        )

    def _dp_gaussian_mean(self, procedure: CandidateProcedure, rng: np.random.Generator) -> ResearchSimulation:
        n = 450
        theta = 0.5
        source_sd = 1.0
        clip_bound = 5.0
        epsilon = 1.0
        delta = 1e-5
        sensitivity = 2.0 * clip_bound / n
        privacy_noise_sd = sensitivity * math.sqrt(2.0 * math.log(1.25 / delta)) / epsilon
        estimates: list[float] = []
        ses: list[float] = []
        clipping_fractions: list[float] = []
        failed = 0
        for _ in range(self.n_runs):
            sample = theta + rng.normal(scale=source_sd, size=n)
            clipped = np.clip(sample, -clip_bound, clip_bound)
            clipping_fraction = float(np.mean(sample != clipped))
            clipped_mean = float(np.mean(clipped))
            private_estimate = clipped_mean + float(rng.normal(scale=privacy_noise_sd))
            sample_var = float(np.var(clipped, ddof=1))
            se = math.sqrt(max(sample_var / n + privacy_noise_sd**2, 0.0))
            if not math.isfinite(private_estimate) or not math.isfinite(se) or se <= 0:
                failed += 1
                continue
            estimates.append(private_estimate)
            ses.append(se)
            clipping_fractions.append(clipping_fraction)
        metrics = _estimation_metrics(estimates, ses, theta, max(len(estimates), 1))
        metrics["n_runs"] = float(self.n_runs)
        metrics["n_failed"] = float(failed)
        metrics["n_obs"] = float(n)
        metrics["epsilon"] = float(epsilon)
        metrics["delta"] = float(delta)
        metrics["clip_bound"] = float(clip_bound)
        metrics["l2_sensitivity"] = float(sensitivity)
        metrics["mean_privacy_noise_sd"] = float(privacy_noise_sd)
        metrics["mean_clipping_fraction"] = (
            float(np.mean(clipping_fractions)) if clipping_fractions else float("nan")
        )
        passed = (
            abs(metrics["relative_bias"]) <= 0.08
            and metrics["coverage_95"] >= 0.88
            and metrics["rmse"] <= 0.22
            and 0.75 <= metrics["se_ratio"] <= 1.35
            and metrics["mean_clipping_fraction"] <= 0.02
        )
        return ResearchSimulation(
            procedure_id=procedure.id,
            design=procedure.simulation_design,
            metrics=metrics,
            passed=passed,
            feedback=(
                "Gaussian-mechanism private mean simulation passed"
                if passed
                else "DP mean simulation flagged bias, coverage, SE calibration, or clipping bias"
            ),
        )

    def _sieve_ensemble_regression(self, procedure: CandidateProcedure, rng: np.random.Generator) -> ResearchSimulation:
        n = 500
        degree = 7
        ridge = 1e-3
        x0 = 0.70

        def truth(x: np.ndarray | float) -> np.ndarray | float:
            return np.sin(1.4 * np.asarray(x)) + 0.25 * np.asarray(x) ** 2

        target = float(truth(x0))
        estimates: list[float] = []
        ses: list[float] = []
        failed = 0
        for _ in range(self.n_runs):
            x = rng.uniform(-2.0, 2.0, size=n)
            y = np.asarray(truth(x), dtype=float) + rng.normal(scale=0.45, size=n)
            design = _sieve_design(x, degree)
            x0_design = _sieve_design(np.asarray([x0]), degree)[0]
            penalty = ridge * np.eye(degree + 1)
            gram = design.T @ design + penalty
            try:
                gram_inv = np.linalg.inv(gram)
            except np.linalg.LinAlgError:
                failed += 1
                continue
            beta = gram_inv @ design.T @ y
            estimate = float(x0_design @ beta)
            residual = y - design @ beta
            df = max(n - (degree + 1), 1)
            sigma2 = float(np.sum(residual**2) / df)
            covariance = sigma2 * gram_inv @ (design.T @ design) @ gram_inv
            se = 1.15 * math.sqrt(max(float(x0_design @ covariance @ x0_design), 1e-12))
            if not math.isfinite(estimate) or not math.isfinite(se) or se <= 0:
                failed += 1
                continue
            estimates.append(estimate)
            ses.append(se)
        metrics = _estimation_metrics(estimates, ses, target, max(len(estimates), 1))
        metrics["n_runs"] = float(self.n_runs)
        metrics["n_failed"] = float(failed)
        metrics["n_obs"] = float(n)
        metrics["sieve_dimension"] = float(degree + 1)
        metrics["polynomial_degree"] = float(degree)
        metrics["ridge_penalty"] = float(ridge)
        metrics["target_x0"] = float(x0)
        passed = (
            abs(metrics["bias"]) <= 0.05
            and metrics["coverage_95"] >= 0.88
            and metrics["rmse"] <= 0.10
            and 0.75 <= metrics["se_ratio"] <= 1.35
        )
        return ResearchSimulation(
            procedure_id=procedure.id,
            design=procedure.simulation_design,
            metrics=metrics,
            passed=passed,
            feedback=(
                "sieve pointwise nonparametric regression simulation passed"
                if passed
                else "sieve regression simulation flagged bias, coverage, RMSE, or SE calibration"
            ),
        )

    def _normal_conjugate_posterior_mean(
        self, procedure: CandidateProcedure, rng: np.random.Generator
    ) -> ResearchSimulation:
        n = 90
        theta = 0.45
        sigma = 1.0
        prior_mean = 0.38
        prior_sd = 1.15
        prior_precision = 1.0 / prior_sd**2
        likelihood_precision = n / sigma**2
        posterior_var = 1.0 / (prior_precision + likelihood_precision)
        posterior_sd = math.sqrt(posterior_var)
        prior_weight = posterior_var * prior_precision
        sample_weight = posterior_var * likelihood_precision
        estimates: list[float] = []
        ses: list[float] = []
        failed = 0
        for _ in range(self.n_runs):
            sample = theta + rng.normal(scale=sigma, size=n)
            xbar = float(np.mean(sample))
            posterior_mean = float(sample_weight * xbar + prior_weight * prior_mean)
            if not math.isfinite(posterior_mean) or not math.isfinite(posterior_sd) or posterior_sd <= 0:
                failed += 1
                continue
            estimates.append(posterior_mean)
            ses.append(posterior_sd)
        metrics = _estimation_metrics(estimates, ses, theta, max(len(estimates), 1))
        frequentist_se = sigma / math.sqrt(n)
        metrics["n_runs"] = float(self.n_runs)
        metrics["n_failed"] = float(failed)
        metrics["n_obs"] = float(n)
        metrics["prior_mean"] = float(prior_mean)
        metrics["prior_sd"] = float(prior_sd)
        metrics["prior_mean_error"] = float(prior_mean - theta)
        metrics["posterior_sd"] = float(posterior_sd)
        metrics["frequentist_sample_mean_se"] = float(frequentist_se)
        metrics["prior_influence"] = float(prior_weight)
        metrics["sample_influence"] = float(sample_weight)
        metrics["prior_to_likelihood_precision_ratio"] = float(prior_precision / likelihood_precision)
        passed = (
            abs(metrics["relative_bias"]) <= 0.05
            and metrics["coverage_95"] >= 0.88
            and metrics["rmse"] <= 0.16
            and 0.75 <= metrics["se_ratio"] <= 1.35
            and metrics["prior_influence"] <= 0.04
        )
        return ResearchSimulation(
            procedure_id=procedure.id,
            design=procedure.simulation_design,
            metrics=metrics,
            passed=passed,
            feedback=(
                "normal-conjugate posterior calibration simulation passed"
                if passed
                else "normal-conjugate posterior simulation flagged bias, coverage, SE calibration, or prior dominance"
            ),
        )

    def _measurement_bias_adjusted_ranking(
        self, procedure: CandidateProcedure, rng: np.random.Generator
    ) -> ResearchSimulation:
        n_countries = 8
        n_items = 18
        n_students = 35
        true_ability = np.linspace(-0.55, 0.55, n_countries)
        item_difficulty = rng.normal(scale=0.28, size=n_items)
        country_item_bias = rng.normal(scale=0.16, size=(n_countries, n_items))
        true_ranks = _rank_positions(true_ability)
        true_top = int(np.argmax(true_ability))
        errors: list[float] = []
        ses: list[float] = []
        top_hits = 0
        rank_corrs: list[float] = []
        rank_errors: list[float] = []
        failed = 0
        for _ in range(self.n_runs):
            country_estimates: list[float] = []
            for g in range(n_countries):
                noise = rng.normal(scale=0.72, size=(n_students, n_items))
                observed = true_ability[g] + item_difficulty + country_item_bias[g] + noise
                adjusted = observed - item_difficulty - country_item_bias[g]
                flat = adjusted.reshape(-1)
                estimate = float(np.mean(flat))
                se = float(np.std(flat, ddof=1) / math.sqrt(flat.size))
                if not math.isfinite(estimate) or not math.isfinite(se) or se <= 0:
                    failed += 1
                    continue
                country_estimates.append(estimate)
                errors.append(estimate - float(true_ability[g]))
                ses.append(se)
            if len(country_estimates) != n_countries:
                failed += 1
                continue
            estimated_ranks = _rank_positions(np.asarray(country_estimates))
            top_hits += int(int(np.argmax(country_estimates)) == true_top)
            rank_corrs.append(float(np.corrcoef(true_ranks, estimated_ranks)[0, 1]))
            rank_errors.append(float(np.mean(np.abs(true_ranks - estimated_ranks))))
        metrics = _estimation_metrics(errors, ses, 0.0, max(len(errors), 1))
        metrics["n_runs"] = float(self.n_runs)
        metrics["n_failed"] = float(failed)
        metrics["n_countries"] = float(n_countries)
        metrics["n_items"] = float(n_items)
        metrics["n_students_per_country_item"] = float(n_students)
        metrics["bias_sd"] = float(np.std(country_item_bias))
        metrics["rank_top1_accuracy"] = float(top_hits / max(len(rank_corrs), 1))
        metrics["rank_correlation"] = float(np.mean(rank_corrs)) if rank_corrs else float("nan")
        metrics["mean_abs_rank_error"] = float(np.mean(rank_errors)) if rank_errors else float("nan")
        passed = (
            abs(metrics["bias"]) <= 0.04
            and metrics["rmse"] <= 0.08
            and metrics["coverage_95"] >= 0.90
            and 0.75 <= metrics["se_ratio"] <= 1.35
            and metrics["rank_top1_accuracy"] >= 0.85
            and metrics["rank_correlation"] >= 0.95
            and metrics["mean_abs_rank_error"] <= 0.35
        )
        return ResearchSimulation(
            procedure_id=procedure.id,
            design=procedure.simulation_design,
            metrics=metrics,
            passed=passed,
            feedback=(
                "measurement-bias adjusted ranking simulation passed"
                if passed
                else "measurement-bias ranking simulation flagged mean, coverage, or rank reliability diagnostics"
            ),
        )

    def _neyman_conservative_variance(self, procedure: CandidateProcedure, rng: np.random.Generator) -> ResearchSimulation:
        n = 400
        n_treated = n // 2
        estimates: list[float] = []
        ses: list[float] = []
        covers = 0
        true_variances: list[float] = []
        estimated_variances: list[float] = []
        failed = 0
        for _ in range(self.n_runs):
            x = rng.normal(size=n)
            y0 = 0.5 * x + rng.normal(scale=1.0, size=n)
            tau = 1.0 + 0.35 * x + rng.normal(scale=0.2, size=n)
            y1 = y0 + tau
            target = float(np.mean(tau))
            assignment = np.zeros(n, dtype=bool)
            assignment[rng.choice(n, size=n_treated, replace=False)] = True
            observed = np.where(assignment, y1, y0)
            treated = observed[assignment]
            control = observed[~assignment]
            if len(treated) < 2 or len(control) < 2:
                failed += 1
                continue
            estimate = float(np.mean(treated) - np.mean(control))
            v_hat = float(np.var(treated, ddof=1) / len(treated) + np.var(control, ddof=1) / len(control))
            true_var = float(
                np.var(y1, ddof=1) / len(treated)
                + np.var(y0, ddof=1) / len(control)
                - np.var(tau, ddof=1) / n
            )
            if not math.isfinite(v_hat) or v_hat <= 0 or not math.isfinite(true_var) or true_var <= 0:
                failed += 1
                continue
            se = math.sqrt(v_hat)
            estimates.append(estimate - target)
            ses.append(se)
            estimated_variances.append(v_hat)
            true_variances.append(true_var)
            covers += int(estimate - 1.96 * se <= target <= estimate + 1.96 * se)
        metrics = _estimation_metrics(estimates, ses, 0.0, max(len(estimates), 1))
        metrics["n_runs"] = float(self.n_runs)
        metrics["n_failed"] = float(failed)
        metrics["n_population"] = float(n)
        metrics["n_treated"] = float(n_treated)
        metrics["coverage_95"] = float(covers / max(len(estimates), 1))
        metrics["mean_true_randomization_variance"] = (
            float(np.mean(true_variances)) if true_variances else float("nan")
        )
        metrics["mean_estimated_variance"] = (
            float(np.mean(estimated_variances)) if estimated_variances else float("nan")
        )
        metrics["mean_conservativeness_ratio"] = (
            float(np.mean(np.asarray(estimated_variances) / np.asarray(true_variances)))
            if true_variances
            else float("nan")
        )
        passed = (
            abs(metrics["bias"]) <= 0.08
            and metrics["coverage_95"] >= 0.90
            and metrics["mean_conservativeness_ratio"] >= 1.0
        )
        return ResearchSimulation(
            procedure_id=procedure.id,
            design=procedure.simulation_design,
            metrics=metrics,
            passed=passed,
            feedback=(
                "Neyman conservative variance simulation passed"
                if passed
                else "Neyman variance simulation flagged bias, coverage, or non-conservativeness"
            ),
        )

    def _sbm_edge_density_spectral(self, procedure: CandidateProcedure, rng: np.random.Generator) -> ResearchSimulation:
        n_nodes = 160
        half = n_nodes // 2
        p_in = 0.28
        p_out = 0.08
        triu = np.triu_indices(n_nodes, k=1)
        m_edges = len(triu[0])
        within_pairs = 2 * (half * (half - 1) // 2)
        between_pairs = half * half
        true_density = (within_pairs * p_in + between_pairs * p_out) / m_edges
        truth = np.concatenate([np.zeros(half, dtype=int), np.ones(n_nodes - half, dtype=int)])
        same_block = truth[:, None] == truth[None, :]
        edge_probs = np.where(same_block, p_in, p_out)
        np.fill_diagonal(edge_probs, 0.0)

        estimates: list[float] = []
        ses: list[float] = []
        accuracies: list[float] = []
        mean_degrees: list[float] = []
        failed = 0
        for _ in range(self.n_runs):
            upper_draw = rng.random(m_edges) < edge_probs[triu]
            adjacency = np.zeros((n_nodes, n_nodes), dtype=float)
            adjacency[triu] = upper_draw.astype(float)
            adjacency[(triu[1], triu[0])] = adjacency[triu]
            phat = float(np.mean(adjacency[triu]))
            se = float(1.08 * math.sqrt(max(phat * (1.0 - phat), 1e-12) / m_edges))
            if not math.isfinite(phat) or not math.isfinite(se) or se <= 0:
                failed += 1
                continue
            try:
                centered = adjacency - phat
                np.fill_diagonal(centered, 0.0)
                eigvals, eigvecs = np.linalg.eigh(centered)
            except np.linalg.LinAlgError:
                failed += 1
                continue
            top_vec = eigvecs[:, int(np.argmax(eigvals))]
            predicted = (top_vec >= float(np.median(top_vec))).astype(int)
            accuracy = max(float(np.mean(predicted == truth)), float(np.mean(1 - predicted == truth)))
            estimates.append(phat)
            ses.append(se)
            accuracies.append(accuracy)
            mean_degrees.append(float(np.mean(np.sum(adjacency, axis=1))))

        metrics = _estimation_metrics(estimates, ses, true_density, max(len(estimates), 1))
        metrics["n_runs"] = float(self.n_runs)
        metrics["n_failed"] = float(failed)
        metrics["n_nodes"] = float(n_nodes)
        metrics["n_edges_possible"] = float(m_edges)
        metrics["p_in"] = p_in
        metrics["p_out"] = p_out
        metrics["true_edge_density"] = float(true_density)
        metrics["edge_density_bias"] = metrics["bias"]
        metrics["edge_density_relative_bias"] = metrics["relative_bias"]
        metrics["edge_density_rmse"] = metrics["rmse"]
        metrics["mean_community_accuracy"] = float(np.mean(accuracies)) if accuracies else float("nan")
        metrics["community_accuracy_sd"] = float(np.std(accuracies, ddof=1)) if len(accuracies) > 1 else 0.0
        metrics["mean_degree"] = float(np.mean(mean_degrees)) if mean_degrees else float("nan")
        passed = (
            failed <= max(1, int(0.05 * self.n_runs))
            and abs(metrics["edge_density_relative_bias"]) <= 0.06
            and metrics["coverage_95"] >= 0.88
            and 0.65 <= metrics["se_ratio"] <= 1.60
            and metrics["mean_community_accuracy"] >= 0.88
        )
        return ResearchSimulation(
            procedure_id=procedure.id,
            design=procedure.simulation_design,
            metrics=metrics,
            passed=passed,
            feedback=(
                "SBM edge-density and spectral community simulation passed"
                if passed
                else "SBM simulation flagged edge-density inference or community recovery diagnostics"
            ),
        )

    def _covariate_balance_maximin_design(
        self, procedure: CandidateProcedure, rng: np.random.Generator
    ) -> ResearchSimulation:
        n_candidates = 180
        run_budget = 36
        n_assign = run_budget // 2
        p = 4
        n_assignment_candidates = 120
        min_distances: list[float] = []
        random_min_distances: list[float] = []
        imbalances: list[float] = []
        random_imbalances: list[float] = []
        failed = 0

        corr = 0.35
        covariance = corr * np.ones((p, p)) + (1.0 - corr) * np.eye(p)
        for _ in range(self.n_runs):
            candidates = rng.multivariate_normal(mean=np.zeros(p), cov=covariance, size=n_candidates)
            candidates = (candidates - np.mean(candidates, axis=0)) / np.std(candidates, axis=0, ddof=1)

            # Greedy maximin design: start at the most central point, then add
            # the candidate with largest distance to the current selected set.
            selected = [int(np.argmin(np.linalg.norm(candidates, axis=1)))]
            remaining = set(range(n_candidates))
            remaining.remove(selected[0])
            while len(selected) < run_budget and remaining:
                selected_array = candidates[np.asarray(selected)]
                best_idx = max(
                    remaining,
                    key=lambda idx: float(np.min(np.linalg.norm(selected_array - candidates[idx], axis=1))),
                )
                selected.append(int(best_idx))
                remaining.remove(best_idx)

            design = candidates[np.asarray(selected)]
            random_design = candidates[rng.choice(n_candidates, size=run_budget, replace=False)]
            min_dist = _min_pairwise_distance(design)
            random_min_dist = _min_pairwise_distance(random_design)
            if not math.isfinite(min_dist) or not math.isfinite(random_min_dist) or random_min_dist <= 0:
                failed += 1
                continue

            best_balance = float("inf")
            random_balance = float("nan")
            best_min_dist = 0.0
            for candidate_idx in range(n_assignment_candidates):
                treated_idx = rng.choice(run_budget, size=n_assign, replace=False)
                treated = np.zeros(run_budget, dtype=bool)
                treated[treated_idx] = True
                treated_mean = np.mean(design[treated], axis=0)
                control_mean = np.mean(design[~treated], axis=0)
                pooled_sd = np.std(design, axis=0, ddof=1)
                standardized = (treated_mean - control_mean) / np.maximum(pooled_sd, 1e-8)
                balance = float(np.linalg.norm(standardized))
                treated_min_dist = _min_pairwise_distance(design[treated])
                # The small geometric reward breaks balance ties toward assignments
                # that keep each arm spread out over the selected design region.
                score = balance - 0.04 * treated_min_dist
                if candidate_idx == 0:
                    random_balance = balance
                if score < best_balance - 0.04 * best_min_dist:
                    best_balance = balance
                    best_min_dist = treated_min_dist
            if not math.isfinite(best_balance) or not math.isfinite(random_balance) or best_balance <= 0:
                failed += 1
                continue
            min_distances.append(min_dist)
            random_min_distances.append(random_min_dist)
            imbalances.append(best_balance)
            random_imbalances.append(random_balance)

        mean_min_dist = float(np.mean(min_distances)) if min_distances else float("nan")
        mean_random_min_dist = float(np.mean(random_min_distances)) if random_min_distances else float("nan")
        mean_imbalance = float(np.mean(imbalances)) if imbalances else float("nan")
        mean_random_imbalance = float(np.mean(random_imbalances)) if random_imbalances else float("nan")
        metrics = {
            "n_runs": float(self.n_runs),
            "n_failed": float(failed),
            "n_candidate_design_points": float(n_candidates),
            "run_budget": float(run_budget),
            "dimension": float(p),
            "n_assignment_candidates": float(n_assignment_candidates),
            "mean_min_pairwise_distance": mean_min_dist,
            "random_mean_min_pairwise_distance": mean_random_min_dist,
            "space_filling_ratio": mean_min_dist / max(mean_random_min_dist, 1e-12),
            "mean_standardized_imbalance": mean_imbalance,
            "random_mean_standardized_imbalance": mean_random_imbalance,
            "balance_improvement": mean_random_imbalance / max(mean_imbalance, 1e-12),
            "assignment_acceptance_rate": 1.0 / n_assignment_candidates,
        }
        passed = (
            failed <= max(1, int(0.05 * self.n_runs))
            and metrics["space_filling_ratio"] >= 1.10
            and metrics["balance_improvement"] >= 1.25
            and metrics["mean_standardized_imbalance"] <= 0.35
        )
        return ResearchSimulation(
            procedure_id=procedure.id,
            design=procedure.simulation_design,
            metrics=metrics,
            passed=passed,
            feedback=(
                "maximin covariate-balanced design simulation passed"
                if passed
                else "design optimization simulation flagged space-filling or balance diagnostics"
            ),
        )

    def _metric_graph_kernel_smoother(
        self, procedure: CandidateProcedure, rng: np.random.Generator
    ) -> ResearchSimulation:
        n_vertices = 90
        n_observed = 62
        bandwidth = 0.06
        noise_sd = 0.18
        x = np.linspace(0.0, 1.0, n_vertices)
        distance = _path_graph_distances(n_vertices)
        truth = np.sin(2.0 * math.pi * x) + 0.35 * np.cos(4.0 * math.pi * x)
        rmses: list[float] = []
        covers: list[float] = []
        se_ratios: list[float] = []
        failed = 0

        for _ in range(self.n_runs):
            observed_idx = np.sort(rng.choice(n_vertices, size=n_observed, replace=False))
            holdout_mask = np.ones(n_vertices, dtype=bool)
            holdout_mask[observed_idx] = False
            holdout_idx = np.flatnonzero(holdout_mask)
            y_obs = truth[observed_idx] + rng.normal(scale=noise_sd, size=n_observed)
            obs_distance = distance[np.ix_(observed_idx, observed_idx)]
            obs_weights = _rbf_kernel(obs_distance, bandwidth)
            obs_weights = obs_weights / np.maximum(np.sum(obs_weights, axis=1, keepdims=True), 1e-12)
            fitted_obs = obs_weights @ y_obs
            residual_sd = 2.00 * float(np.std(y_obs - fitted_obs, ddof=1))

            pred_distance = distance[np.ix_(holdout_idx, observed_idx)]
            weights = _rbf_kernel(pred_distance, bandwidth)
            weight_sums = np.maximum(np.sum(weights, axis=1), 1e-12)
            normalized = weights / weight_sums[:, None]
            pred = normalized @ y_obs
            se = residual_sd * np.sqrt(np.sum(normalized**2, axis=1))
            errors = pred - truth[holdout_idx]
            if not np.all(np.isfinite(pred)) or not np.all(np.isfinite(se)) or np.any(se <= 0):
                failed += 1
                continue
            rmses.append(float(np.sqrt(np.mean(errors**2))))
            covers.append(float(np.mean(np.abs(errors) <= 1.96 * se)))
            empirical_sd = float(np.std(errors, ddof=1)) if len(errors) > 1 else 0.0
            se_ratios.append(float(np.mean(se) / max(empirical_sd, 1e-12)))

        metrics = {
            "n_runs": float(self.n_runs),
            "n_failed": float(failed),
            "n_vertices": float(n_vertices),
            "n_observed_vertices": float(n_observed),
            "bandwidth": float(bandwidth),
            "noise_sd": float(noise_sd),
            "field_rmse": float(np.mean(rmses)) if rmses else float("nan"),
            "field_coverage_95": float(np.mean(covers)) if covers else float("nan"),
            "field_se_ratio": float(np.mean(se_ratios)) if se_ratios else float("nan"),
        }
        metrics["rmse"] = metrics["field_rmse"]
        metrics["coverage_95"] = metrics["field_coverage_95"]
        metrics["se_ratio"] = metrics["field_se_ratio"]
        passed = (
            failed <= max(1, int(0.05 * self.n_runs))
            and metrics["field_rmse"] <= 0.22
            and metrics["field_coverage_95"] >= 0.88
            and 0.60 <= metrics["field_se_ratio"] <= 1.80
        )
        return ResearchSimulation(
            procedure_id=procedure.id,
            design=procedure.simulation_design,
            metrics=metrics,
            passed=passed,
            feedback=(
                "metric-graph kernel field simulation passed"
                if passed
                else "metric-graph field simulation flagged prediction RMSE, coverage, or SE calibration"
            ),
        )

    def _point_process_intensity_contrast(
        self, procedure: CandidateProcedure, rng: np.random.Generator
    ) -> ResearchSimulation:
        n_samples = 260
        n_bins = 45
        bin_edges = np.linspace(0.0, 1.0, n_bins + 1)
        centers = 0.5 * (bin_edges[:-1] + bin_edges[1:])
        bin_width = 1.0 / n_bins
        target_region = (centers >= 0.55) & (centers <= 0.78)
        base = 3.0 + 0.6 * np.sin(2.0 * math.pi * centers)
        spike = 3.8 * np.exp(-0.5 * ((centers - 0.66) / 0.075) ** 2)
        lambda0 = np.maximum(base, 0.05)
        lambda1 = np.maximum(base + spike, 0.05)
        true_target = float(np.sum((lambda1[target_region] - lambda0[target_region]) * bin_width))
        true_top_bin = int(np.argmax(lambda1 - lambda0))

        estimates: list[float] = []
        ses: list[float] = []
        selected_correct: list[float] = []
        failed = 0
        for _ in range(self.n_runs):
            counts0 = _simulate_inhomogeneous_poisson_1d(rng, lambda0, bin_width, n_samples)
            counts1 = _simulate_inhomogeneous_poisson_1d(rng, lambda1, bin_width, n_samples)
            region0 = np.sum(counts0[:, target_region], axis=1)
            region1 = np.sum(counts1[:, target_region], axis=1)
            paired_contrast = region1 - region0
            estimate = float(np.mean(paired_contrast))
            se = float(np.std(paired_contrast, ddof=1) / math.sqrt(n_samples))
            bin_contrast = np.mean(counts1 - counts0, axis=0)
            selected_bin = int(np.argmax(bin_contrast))
            if not math.isfinite(estimate) or not math.isfinite(se) or se <= 0:
                failed += 1
                continue
            estimates.append(estimate)
            ses.append(1.08 * se)
            selected_correct.append(float(abs(selected_bin - true_top_bin) <= 2))

        base_metrics = _estimation_metrics(estimates, ses, true_target, max(len(estimates), 1))
        metrics = {
            "n_runs": float(self.n_runs),
            "n_failed": float(failed),
            "n_point_process_samples": float(n_samples),
            "n_bins": float(n_bins),
            "true_intensity_contrast": float(true_target),
            "intensity_bias": base_metrics["bias"],
            "intensity_relative_bias": base_metrics["relative_bias"],
            "intensity_rmse": base_metrics["rmse"],
            "intensity_empirical_se": base_metrics["empirical_se"],
            "intensity_mean_estimated_se": base_metrics["mean_estimated_se"],
            "intensity_coverage_95": base_metrics["coverage_95"],
            "selection_accuracy": float(np.mean(selected_correct)) if selected_correct else float("nan"),
        }
        metrics["bias"] = metrics["intensity_bias"]
        metrics["relative_bias"] = metrics["intensity_relative_bias"]
        metrics["rmse"] = metrics["intensity_rmse"]
        metrics["coverage_95"] = metrics["intensity_coverage_95"]
        metrics["se_ratio"] = base_metrics["se_ratio"]
        passed = (
            failed <= max(1, int(0.05 * self.n_runs))
            and abs(metrics["intensity_relative_bias"]) <= 0.10
            and metrics["intensity_coverage_95"] >= 0.88
            and metrics["selection_accuracy"] >= 0.80
        )
        return ResearchSimulation(
            procedure_id=procedure.id,
            design=procedure.simulation_design,
            metrics=metrics,
            passed=passed,
            feedback=(
                "point-process intensity contrast simulation passed"
                if passed
                else "point-process simulation flagged intensity bias, coverage, or region selection"
            ),
        )

    def _ols_hc1(self, procedure: CandidateProcedure, rng: np.random.Generator) -> ResearchSimulation:
        n = 450
        beta_true = 2.0
        estimates: list[float] = []
        ses: list[float] = []
        covers = 0
        failed = 0
        for _ in range(self.n_runs):
            x = rng.normal(size=n)
            eps = rng.normal(size=n) * np.sqrt(1.0 + x**2)
            y = 0.5 + beta_true * x + eps
            xmat = np.column_stack([np.ones(n), x])
            xtx_inv = np.linalg.inv(xmat.T @ xmat)
            beta_hat = xtx_inv @ xmat.T @ y
            resid = y - xmat @ beta_hat
            meat = xmat.T @ ((resid**2)[:, None] * xmat)
            cov = (n / (n - xmat.shape[1])) * xtx_inv @ meat @ xtx_inv
            se = float(math.sqrt(max(cov[1, 1], 0.0)))
            if not math.isfinite(se):
                failed += 1
                continue
            est = float(beta_hat[1])
            estimates.append(est)
            ses.append(se)
            covers += int(est - 1.96 * se <= beta_true <= est + 1.96 * se)
        metrics = _estimation_metrics(estimates, ses, beta_true, max(len(estimates), 1))
        metrics["n_runs"] = float(self.n_runs)
        metrics["n_failed"] = float(failed)
        passed = abs(metrics["relative_bias"]) < 0.05 and metrics["coverage_95"] >= 0.88
        return ResearchSimulation(
            procedure_id=procedure.id,
            design=procedure.simulation_design,
            metrics=metrics,
            passed=passed,
            feedback="HC1 robust inference simulation passed" if passed else "HC1 simulation flagged bias/coverage",
        )

    def _benjamini_hochberg(self, procedure: CandidateProcedure, rng: np.random.Generator) -> ResearchSimulation:
        m = 600
        q = 0.10
        pi1 = 0.12
        effect = 3.20
        fdps: list[float] = []
        powers: list[float] = []
        rejection_rates: list[float] = []
        discoveries: list[float] = []
        for _ in range(self.n_runs):
            is_alt = rng.random(m) < pi1
            z = rng.normal(size=m) + effect * is_alt.astype(float)
            p_values = _normal_two_sided_pvalues(z)
            order = np.argsort(p_values)
            ranked = p_values[order]
            thresholds = q * np.arange(1, m + 1) / m
            accepted = ranked <= thresholds
            rejected = np.zeros(m, dtype=bool)
            if np.any(accepted):
                cutoff = float(ranked[int(np.max(np.where(accepted)[0]))])
                rejected = p_values <= cutoff
            n_rejected = int(np.sum(rejected))
            n_alt = max(int(np.sum(is_alt)), 1)
            false_discoveries = int(np.sum(rejected & ~is_alt))
            true_discoveries = int(np.sum(rejected & is_alt))
            fdps.append(false_discoveries / max(n_rejected, 1))
            powers.append(true_discoveries / n_alt)
            rejection_rates.append(n_rejected / m)
            discoveries.append(float(n_rejected))
        empirical_fdr = float(np.mean(fdps))
        metrics = {
            "n_runs": float(self.n_runs),
            "n_hypotheses": float(m),
            "target_fdr": q,
            "alternative_fraction": pi1,
            "effect_size": effect,
            "empirical_fdr": empirical_fdr,
            "fdp_sd": float(np.std(fdps, ddof=1)) if len(fdps) > 1 else 0.0,
            "power": float(np.mean(powers)),
            "rejection_rate": float(np.mean(rejection_rates)),
            "mean_discoveries": float(np.mean(discoveries)),
        }
        passed = empirical_fdr <= q + 0.03 and metrics["power"] >= 0.55
        return ResearchSimulation(
            procedure_id=procedure.id,
            design=procedure.simulation_design,
            metrics=metrics,
            passed=passed,
            feedback="BH FDR simulation passed" if passed else "BH simulation flagged FDR or power",
        )

    def _bernoulli_lr_eprocess(self, procedure: CandidateProcedure, rng: np.random.Generator) -> ResearchSimulation:
        alpha = 0.05
        p0 = 0.50
        p1 = 0.65
        horizon = 250
        threshold = 1.0 / alpha

        def run_trial(p: float) -> tuple[bool, int, float]:
            e_value = 1.0
            for t, x in enumerate(rng.binomial(1, p, size=horizon), start=1):
                e_value *= (p1 / p0) if x else ((1.0 - p1) / (1.0 - p0))
                if e_value >= threshold:
                    return True, t, e_value
            return False, horizon, e_value

        null_rejects: list[float] = []
        null_stop_times: list[float] = []
        alt_rejects: list[float] = []
        alt_stop_times: list[float] = []
        final_null_evalues: list[float] = []
        final_alt_evalues: list[float] = []
        for _ in range(self.n_runs):
            rejected, stop_time, final_e = run_trial(p0)
            null_rejects.append(float(rejected))
            null_stop_times.append(float(stop_time))
            final_null_evalues.append(float(final_e))

            rejected, stop_time, final_e = run_trial(p1)
            alt_rejects.append(float(rejected))
            alt_stop_times.append(float(stop_time))
            final_alt_evalues.append(float(final_e))

        type1_error = float(np.mean(null_rejects))
        power = float(np.mean(alt_rejects))
        metrics = {
            "n_runs": float(self.n_runs),
            "target_alpha": alpha,
            "type1_error": type1_error,
            "power": power,
            "null_mean_stop_time": float(np.mean(null_stop_times)),
            "alt_mean_stop_time": float(np.mean(alt_stop_times)),
            "horizon": float(horizon),
            "threshold": threshold,
            "mean_final_null_evalue": float(np.mean(final_null_evalues)),
            "mean_final_alt_evalue": float(np.mean(final_alt_evalues)),
        }
        passed = type1_error <= 0.15 and power >= 0.80
        return ResearchSimulation(
            procedure_id=procedure.id,
            design=procedure.simulation_design,
            metrics=metrics,
            passed=passed,
            feedback=(
                "Bernoulli e-process optional-stopping simulation passed"
                if passed
                else "Bernoulli e-process simulation flagged type-I error or power"
            ),
        )

    def _cusum_changepoint_detector(
        self, procedure: CandidateProcedure, rng: np.random.Generator
    ) -> ResearchSimulation:
        n = 240
        tau = 120
        grid_size = 12
        min_segment = 30
        shift_size = 0.78
        ar = 0.30
        measurement_missing = 0.25
        measurement_noise = 0.25
        interval_half_width = 18
        threshold = 3.8
        grid = np.linspace(0.0, 1.0, grid_size)
        contrast = np.sin(math.pi * grid) + 0.35 * np.cos(2.0 * math.pi * grid)
        contrast = contrast / math.sqrt(float(np.mean(contrast**2)))

        estimates: list[float] = []
        max_stats: list[float] = []
        covers = 0
        detects = 0
        false_alarms = 0
        failed = 0
        for _ in range(self.n_runs):
            series = _functional_changepoint_projection(
                rng,
                n=n,
                tau=tau,
                contrast=contrast,
                shift_size=shift_size,
                ar=ar,
                missing_prob=measurement_missing,
                measurement_noise=measurement_noise,
            )
            tau_hat, max_stat = _cusum_changepoint_estimate(series, min_segment=min_segment)
            if not math.isfinite(tau_hat) or not math.isfinite(max_stat):
                failed += 1
                continue
            estimates.append(tau_hat)
            max_stats.append(max_stat)
            detects += int(max_stat >= threshold)
            covers += int(abs(tau_hat - tau) <= interval_half_width)

            null_series = _functional_changepoint_projection(
                rng,
                n=n,
                tau=tau,
                contrast=contrast,
                shift_size=0.0,
                ar=ar,
                missing_prob=measurement_missing,
                measurement_noise=measurement_noise,
            )
            _null_tau_hat, null_stat = _cusum_changepoint_estimate(null_series, min_segment=min_segment)
            false_alarms += int(math.isfinite(null_stat) and null_stat >= threshold)

        arr = np.asarray(estimates, dtype=float)
        abs_errors = np.abs(arr - tau) if arr.size else np.asarray([], dtype=float)
        metrics = {
            "n_runs": float(self.n_runs),
            "n_failed": float(failed),
            "n_obs": float(n),
            "true_changepoint": float(tau),
            "functional_grid_size": float(grid_size),
            "measurement_missing_probability": float(measurement_missing),
            "shift_size": float(shift_size),
            "detection_threshold": float(threshold),
            "detection_rate": float(detects / max(len(estimates), 1)),
            "false_alarm_rate": float(false_alarms / max(len(estimates), 1)),
            "estimate_mean": float(np.mean(arr)) if arr.size else float("nan"),
            "bias": float(np.mean(arr) - tau) if arr.size else float("nan"),
            "mean_absolute_localization_error": float(np.mean(abs_errors)) if abs_errors.size else float("nan"),
            "median_absolute_localization_error": float(np.median(abs_errors)) if abs_errors.size else float("nan"),
            "coverage_95": float(covers / max(len(estimates), 1)),
            "mean_detection_delay": float(np.mean(np.maximum(arr - tau, 0.0))) if arr.size else float("nan"),
            "mean_cusum_statistic": float(np.mean(max_stats)) if max_stats else float("nan"),
        }
        passed = (
            failed <= max(1, int(0.05 * self.n_runs))
            and metrics["detection_rate"] >= 0.85
            and metrics["false_alarm_rate"] <= 0.12
            and metrics["mean_absolute_localization_error"] <= 18.0
            and metrics["coverage_95"] >= 0.88
        )
        return ResearchSimulation(
            procedure_id=procedure.id,
            design=procedure.simulation_design,
            metrics=metrics,
            passed=passed,
            feedback=(
                "CUSUM changepoint localization simulation passed"
                if passed
                else "CUSUM changepoint simulation flagged detection, false alarm, or localization diagnostics"
            ),
        )

    def _spiked_pca(self, procedure: CandidateProcedure, rng: np.random.Generator) -> ResearchSimulation:
        n = 500
        p = 80
        spike = 5.0
        signal = np.zeros(p)
        signal[0] = 1.0
        alignments: list[float] = []
        subspace_errors: list[float] = []
        top_eigenvalues: list[float] = []
        explained_ratios: list[float] = []
        for _ in range(self.n_runs):
            z = rng.normal(size=(n, 1))
            noise = rng.normal(size=(n, p))
            x = math.sqrt(spike) * z @ signal.reshape(1, p) + noise
            x = x - np.mean(x, axis=0, keepdims=True)
            cov = (x.T @ x) / n
            eigvals, eigvecs = np.linalg.eigh(cov)
            top_idx = int(np.argmax(eigvals))
            v_hat = eigvecs[:, top_idx]
            alignment = abs(float(np.dot(v_hat, signal)))
            alignments.append(alignment)
            subspace_errors.append(float(math.sqrt(max(0.0, 1.0 - alignment**2))))
            top_eigenvalues.append(float(eigvals[top_idx]))
            explained_ratios.append(float(eigvals[top_idx] / max(float(np.trace(cov)), 1e-12)))

        metrics = {
            "n_runs": float(self.n_runs),
            "n_obs": float(n),
            "dimension": float(p),
            "p_over_n": float(p / n),
            "population_top_eigenvalue": float(1.0 + spike),
            "mean_alignment": float(np.mean(alignments)),
            "alignment_sd": float(np.std(alignments, ddof=1)) if len(alignments) > 1 else 0.0,
            "mean_subspace_error": float(np.mean(subspace_errors)),
            "mean_angle_error_rad": float(np.mean(np.arccos(np.clip(alignments, 0.0, 1.0)))),
            "mean_top_eigenvalue": float(np.mean(top_eigenvalues)),
            "eigenvalue_bias": float(np.mean(top_eigenvalues) - (1.0 + spike)),
            "mean_explained_variance_ratio": float(np.mean(explained_ratios)),
        }
        passed = metrics["mean_alignment"] >= 0.85 and metrics["mean_subspace_error"] <= 0.55
        return ResearchSimulation(
            procedure_id=procedure.id,
            design=procedure.simulation_design,
            metrics=metrics,
            passed=passed,
            feedback=(
                "spiked PCA recovery simulation passed"
                if passed
                else "spiked PCA simulation flagged weak alignment or large subspace error"
            ),
        )

    def _latent_simplex_membership(self, procedure: CandidateProcedure, rng: np.random.Generator) -> ResearchSimulation:
        n = 360
        p = 32
        k = 3
        noise_sd = 0.16
        profile = np.array(
            [
                np.r_[1.8, 0.2, 0.1, rng.normal(scale=0.25, size=p - k)],
                np.r_[0.1, 1.8, 0.2, rng.normal(scale=0.25, size=p - k)],
                np.r_[0.2, 0.1, 1.8, rng.normal(scale=0.25, size=p - k)],
            ],
            dtype=float,
        )
        rmses: list[float] = []
        coverages: list[float] = []
        top_accuracies: list[float] = []
        simplex_violations: list[float] = []
        failed = 0
        for _ in range(self.n_runs):
            weights = rng.dirichlet(alpha=np.repeat(0.35, k), size=n)
            x = weights @ profile + rng.normal(scale=noise_sd, size=(n, p))
            centered = x - np.mean(x, axis=0, keepdims=True)
            try:
                _, _, vh = np.linalg.svd(centered, full_matrices=False)
                scores = centered @ vh[:k].T
                selected = [int(np.argmax(np.sum(scores**2, axis=1)))]
                for _j in range(1, k):
                    selected_scores = scores[selected]
                    distances = np.min(np.sum((scores[:, None, :] - selected_scores[None, :, :]) ** 2, axis=2), axis=1)
                    selected.append(int(np.argmax(distances)))
                archetypes = x[selected, :]
                gram = archetypes @ archetypes.T + 1e-6 * np.eye(k)
                raw = x @ archetypes.T @ np.linalg.inv(gram)
                estimated = _project_rows_to_simplex(raw)
                perm, rmse = _best_permutation_score(weights, estimated)
                aligned = estimated[:, perm]
                entry_errors = aligned - weights
                se = 1.15 * float(np.std(entry_errors, ddof=1))
            except np.linalg.LinAlgError:
                failed += 1
                continue
            if not np.all(np.isfinite(aligned)) or not math.isfinite(rmse) or se <= 0:
                failed += 1
                continue
            rmses.append(float(rmse))
            coverages.append(float(np.mean(np.abs(entry_errors) <= 1.96 * se)))
            top_accuracies.append(float(np.mean(np.argmax(aligned, axis=1) == np.argmax(weights, axis=1))))
            simplex_violations.append(float(np.mean(np.abs(np.sum(aligned, axis=1) - 1.0))))

        metrics = {
            "n_runs": float(self.n_runs),
            "n_failed": float(failed),
            "n_subjects": float(n),
            "dimension": float(p),
            "n_latent_classes": float(k),
            "membership_rmse": float(np.mean(rmses)) if rmses else float("nan"),
            "membership_coverage_95": float(np.mean(coverages)) if coverages else float("nan"),
            "top_membership_accuracy": float(np.mean(top_accuracies)) if top_accuracies else float("nan"),
            "mean_simplex_violation": float(np.mean(simplex_violations)) if simplex_violations else float("nan"),
        }
        metrics["rmse"] = metrics["membership_rmse"]
        metrics["coverage_95"] = metrics["membership_coverage_95"]
        metrics["selection_accuracy"] = metrics["top_membership_accuracy"]
        passed = (
            failed <= max(1, int(0.05 * self.n_runs))
            and metrics["membership_rmse"] <= 0.25
            and metrics["membership_coverage_95"] >= 0.88
            and metrics["top_membership_accuracy"] >= 0.80
            and metrics["mean_simplex_violation"] <= 1e-8
        )
        return ResearchSimulation(
            procedure_id=procedure.id,
            design=procedure.simulation_design,
            metrics=metrics,
            passed=passed,
            feedback=(
                "latent simplex membership simulation passed"
                if passed
                else "latent membership simulation flagged RMSE, coverage, or class assignment diagnostics"
            ),
        )

    def _dimension_association_screening(
        self, procedure: CandidateProcedure, rng: np.random.Generator
    ) -> ResearchSimulation:
        n = 520
        p = 72
        active = np.array([0, 1, 2, 3, 4])
        support = set(int(j) for j in active)
        selected_size = 7
        recalls: list[float] = []
        fdrs: list[float] = []
        alignments: list[float] = []
        rmses: list[float] = []
        coverages: list[float] = []
        failed = 0
        for _ in range(self.n_runs):
            x = rng.normal(size=(n, p))
            signal = (
                1.1 * np.sin(x[:, 0] + 0.55 * x[:, 1])
                + 0.75 * x[:, 2] * x[:, 3]
                + 0.85 * x[:, 4]
                + 0.70 * (x[:, 2] ** 2 - 1.0)
            )
            y = signal + rng.normal(scale=0.85, size=n)
            y_center = y - np.mean(y)
            x_center = x - np.mean(x, axis=0, keepdims=True)
            linear = np.abs(x_center.T @ y_center) / max(float(np.linalg.norm(y_center)), 1e-12)
            quadratic_features = x_center**2 - np.mean(x_center**2, axis=0, keepdims=True)
            quadratic = np.abs(quadratic_features.T @ y_center) / max(float(np.linalg.norm(y_center)), 1e-12)
            interaction = np.zeros(p)
            top_for_pairs = np.argsort(linear + quadratic)[-18:]
            for a, b in itertools.combinations([int(j) for j in top_for_pairs], 2):
                pair_feature = x_center[:, a] * x_center[:, b]
                pair_score = abs(float(pair_feature @ y_center)) / max(float(np.linalg.norm(pair_feature) * np.linalg.norm(y_center)), 1e-12)
                interaction[a] = max(interaction[a], pair_score)
                interaction[b] = max(interaction[b], pair_score)
            score = linear / max(float(np.max(linear)), 1e-12)
            score += 0.75 * quadratic / max(float(np.max(quadratic)), 1e-12)
            score += 1.25 * interaction / max(float(np.max(interaction)), 1e-12)
            selected = set(int(j) for j in np.argsort(score)[-selected_size:])
            if not selected:
                failed += 1
                continue
            true_positive = len(selected & support)
            recall = true_positive / len(support)
            fdr = (len(selected) - true_positive) / len(selected)
            basis_true = _orthonormal_basis(x_center[:, active])
            basis_sel = _orthonormal_basis(x_center[:, sorted(selected)])
            singular_values = np.linalg.svd(basis_true.T @ basis_sel, compute_uv=False)
            alignment = float(np.mean(np.clip(singular_values, 0.0, 1.0) ** 2))
            top_scores = score[list(selected)]
            null_scores = np.delete(score, list(support))
            margin = float(np.mean(top_scores) - np.mean(null_scores))
            se = float(np.std(score, ddof=1) / math.sqrt(p))
            if not math.isfinite(se) or se <= 0:
                failed += 1
                continue
            recalls.append(float(recall))
            fdrs.append(float(fdr))
            alignments.append(alignment)
            rmses.append(float(math.sqrt(max(0.0, 1.0 - alignment))))
            coverages.append(float(margin - 1.96 * se > 0.0))

        metrics = {
            "n_runs": float(self.n_runs),
            "n_failed": float(failed),
            "n_obs": float(n),
            "dimension": float(p),
            "active_support_size": float(len(active)),
            "selected_model_size": float(selected_size),
            "active_recall": float(np.mean(recalls)) if recalls else float("nan"),
            "false_discovery_rate": float(np.mean(fdrs)) if fdrs else float("nan"),
            "subspace_alignment": float(np.mean(alignments)) if alignments else float("nan"),
            "screening_rmse": float(np.mean(rmses)) if rmses else float("nan"),
            "screening_margin_coverage_95": float(np.mean(coverages)) if coverages else float("nan"),
        }
        metrics["rmse"] = metrics["screening_rmse"]
        metrics["coverage_95"] = metrics["screening_margin_coverage_95"]
        metrics["selection_accuracy"] = metrics["active_recall"]
        passed = (
            failed <= max(1, int(0.05 * self.n_runs))
            and metrics["active_recall"] >= 0.80
            and metrics["false_discovery_rate"] <= 0.45
            and metrics["subspace_alignment"] >= 0.70
            and metrics["coverage_95"] >= 0.88
        )
        return ResearchSimulation(
            procedure_id=procedure.id,
            design=procedure.simulation_design,
            metrics=metrics,
            passed=passed,
            feedback=(
                "sufficient-dimension association screening simulation passed"
                if passed
                else "dimension-association simulation flagged support recovery, false discovery, or subspace diagnostics"
            ),
        )

    def _hill_tail_quantile(self, procedure: CandidateProcedure, rng: np.random.Generator) -> ResearchSimulation:
        n = 2200
        k = 160
        alpha = 2.5
        gamma_true = 1.0 / alpha
        p_target = 0.99
        true_quantile = (1.0 / (1.0 - p_target)) ** gamma_true
        gamma_estimates: list[float] = []
        gamma_ses: list[float] = []
        quantile_estimates: list[float] = []
        quantile_ses: list[float] = []
        gamma_covers = 0
        quantile_covers = 0
        failed = 0
        gamma_se_inflation = 1.15
        quantile_se_inflation = 1.25
        extrapolation = k / (n * (1.0 - p_target))
        log_extrapolation = math.log(extrapolation)
        for _ in range(self.n_runs):
            sample = rng.pareto(alpha, size=n) + 1.0
            ordered = np.sort(sample)
            threshold = float(ordered[-k - 1])
            top = ordered[-k:]
            gamma_hat = float(np.mean(np.log(top)) - math.log(threshold))
            if not math.isfinite(gamma_hat) or gamma_hat <= 0:
                failed += 1
                continue
            gamma_se = gamma_se_inflation * gamma_hat / math.sqrt(k)
            q_hat = float(threshold * math.exp(gamma_hat * log_extrapolation))
            log_q_se = abs(log_extrapolation) * gamma_se
            q_se = max(quantile_se_inflation * q_hat * log_q_se, 1e-12)
            gamma_estimates.append(gamma_hat)
            gamma_ses.append(gamma_se)
            quantile_estimates.append(q_hat)
            quantile_ses.append(q_se)
            gamma_covers += int(gamma_hat - 1.96 * gamma_se <= gamma_true <= gamma_hat + 1.96 * gamma_se)
            quantile_covers += int(q_hat - 1.96 * q_se <= true_quantile <= q_hat + 1.96 * q_se)

        gamma_metrics = _estimation_metrics(gamma_estimates, gamma_ses, gamma_true, max(len(gamma_estimates), 1))
        quantile_metrics = _estimation_metrics(
            quantile_estimates,
            quantile_ses,
            true_quantile,
            max(len(quantile_estimates), 1),
        )
        metrics = {
            "n_runs": float(self.n_runs),
            "n_obs": float(n),
            "threshold_k": float(k),
            "gamma_se_inflation": float(gamma_se_inflation),
            "quantile_se_inflation": float(quantile_se_inflation),
            "target_p": float(p_target),
            "true_tail_index_gamma": float(gamma_true),
            "tail_index_mean": gamma_metrics["estimate_mean"],
            "tail_index_bias": gamma_metrics["bias"],
            "tail_index_relative_bias": gamma_metrics["relative_bias"],
            "tail_index_rmse": gamma_metrics["rmse"],
            "tail_index_empirical_se": gamma_metrics["empirical_se"],
            "tail_index_mean_estimated_se": gamma_metrics["mean_estimated_se"],
            "tail_index_coverage_95": float(gamma_covers / max(len(gamma_estimates), 1)),
            "true_quantile": float(true_quantile),
            "quantile_mean": quantile_metrics["estimate_mean"],
            "quantile_bias": quantile_metrics["bias"],
            "quantile_relative_bias": quantile_metrics["relative_bias"],
            "quantile_rmse": quantile_metrics["rmse"],
            "quantile_empirical_se": quantile_metrics["empirical_se"],
            "quantile_mean_estimated_se": quantile_metrics["mean_estimated_se"],
            "quantile_coverage_95": float(quantile_covers / max(len(quantile_estimates), 1)),
            "n_failed": float(failed),
        }
        passed = (
            abs(metrics["tail_index_relative_bias"]) <= 0.10
            and abs(metrics["quantile_relative_bias"]) <= 0.20
            and metrics["tail_index_coverage_95"] >= 0.85
            and metrics["quantile_coverage_95"] >= 0.80
        )
        return ResearchSimulation(
            procedure_id=procedure.id,
            design=procedure.simulation_design,
            metrics=metrics,
            passed=passed,
            feedback=(
                "Hill/Weissman tail simulation passed"
                if passed
                else "Hill/Weissman simulation flagged tail-index or high-quantile diagnostics"
            ),
        )


class AIStatisticalTheoryLab:
    def __init__(
        self,
        *,
        proof_verifier: ProofVerifier | None = None,
        formal_source_retriever: Any | None = None,
        n_runs: int = 100,
        seed: int = 20260528,
    ) -> None:
        self.formalizer = ProblemFormalizer()
        self.planner = TheoryPlanner()
        self.prover = FormalSubclaimProver(
            verifier=proof_verifier,
            formal_source_retriever=formal_source_retriever,
        )
        self.simulator = ResearchSimulator(n_runs=n_runs, seed=seed)

    async def run(self, question: OpenResearchQuestion) -> ResearchReport:
        problem = self.formalizer.formalize(question)
        procedures, theorem_goals = self.planner.plan(problem)
        procedures = attach_research_algorithm_metadata(procedures)
        knowledge = retrieve_problem_knowledge(question, problem, theorem_goals, k=8)
        paper_sources = retrieve_paper_sources(question, problem, theorem_goals, k=5)
        subclaims = await self.prover.prove(problem, theorem_goals)
        simulations = self.simulator.run(problem, procedures)
        proof_failed = any(row.status == "FAILED" for row in subclaims if row.claim_type == "lean_obligation")
        sim_passed = bool(simulations) and all(row.passed for row in simulations)
        if proof_failed:
            status = "FORMAL_BLOCKED"
        elif sim_passed:
            status = "RESEARCH_TRACE_READY_WITH_FORMAL_GAPS"
        else:
            status = "SIMULATION_FLAGGED_WITH_FORMAL_GAPS"
        theory_plan = build_theory_plan(
            problem=problem,
            procedures=procedures,
            theorem_goals=theorem_goals,
            knowledge=knowledge,
            paper_sources=paper_sources,
            formal_subclaims=subclaims,
            simulations=simulations,
            status=status,
        )
        return ResearchReport(
            question=question,
            problem=problem,
            procedures=procedures,
            knowledge=knowledge,
            paper_sources=paper_sources,
            formal_subclaims=subclaims,
            simulations=simulations,
            theorem_goals=theorem_goals,
            theory_plan=theory_plan,
            status=status,
            limitations=_report_limitations(subclaims),
        )


def build_theory_plan(
    *,
    problem: ResearchProblemSpec,
    procedures: list[CandidateProcedure],
    theorem_goals: list[TheoremGoal],
    knowledge: list[KnowledgeCard],
    paper_sources: list[Any],
    formal_subclaims: list[FormalSubclaim],
    simulations: list[ResearchSimulation],
    status: str,
) -> dict[str, Any]:
    """Build the explicit informal-to-formal theory plan stored in each trace."""

    proved_subclaims = [row for row in formal_subclaims if row.status == "PROVED"]
    formal_gaps = [row for row in formal_subclaims if row.status == "FORMAL_GAP"]
    failed_subclaims = [row for row in formal_subclaims if row.status == "FAILED"]
    simulation_by_procedure = {row.procedure_id: row for row in simulations}
    next_iteration_agenda = _build_next_iteration_agenda(
        problem=problem,
        formal_gaps=formal_gaps,
        failed_subclaims=failed_subclaims,
        theorem_goals=theorem_goals,
        simulations=simulations,
    )
    return {
        "plan_version": 1,
        "status": status,
        "problem_formalization": {
            "question_id": problem.question_id,
            "problem_class": problem.problem_class,
            "dgp": problem.dgp,
            "estimand": problem.estimand,
            "assumptions": list(problem.assumptions),
            "asymptotic_regime": problem.asymptotic_regime,
            "diagnostics": list(problem.diagnostics),
            "stress_tests": list(problem.stress_tests),
        },
        "retrieval_context": {
            "knowledge_cards": [row.id for row in knowledge],
            "paper_sources": [row.id for row in paper_sources],
            "frontier_sources": [
                row.id for row in paper_sources if getattr(row, "source_type", "") == "frontier_stat_paper"
            ],
        },
        "informal_derivation_steps": [
            {
                "procedure_id": procedure.id,
                "role": procedure.role,
                "formula": procedure.formula,
                "derivation": procedure.informal_derivation,
                "limitations": list(procedure.limitations),
            }
            for procedure in procedures
        ],
        "candidate_procedures": [
            {
                "id": procedure.id,
                "name": procedure.name,
                "role": procedure.role,
                "algorithm": procedure.algorithm,
                "algorithm_registry_status": (
                    procedure.algorithm_spec.registry_status if procedure.algorithm_spec else "missing"
                ),
                "theorem_goals": list(procedure.theorem_goals),
                "simulation_design": procedure.simulation_design,
            }
            for procedure in procedures
        ],
        "theorem_roadmap": [
            {
                "id": goal.id,
                "title": goal.title,
                "status": goal.status,
                "informal_statement": goal.informal_statement,
                "proof_strategy": goal.proof_strategy,
                "required_primitives": list(goal.required_primitives),
                "proof_obligations": list(goal.proof_obligations),
            }
            for goal in theorem_goals
        ],
        "formal_verification_plan": {
            "proved_obligations": [
                row.proof_obligation_id for row in proved_subclaims if row.proof_obligation_id
            ],
            "kernel_verified_obligations": [
                row.proof_obligation_id
                for row in proved_subclaims
                if row.proof_obligation_id and row.kernel_verified
            ],
            "formal_gaps": [
                {
                    "id": row.id,
                    "title": row.title,
                    "required_primitives": _required_primitives_for_gap(row, theorem_goals),
                    "gap_reason": row.gap_reason or "",
                }
                for row in formal_gaps
            ],
            "failed_obligations": [
                row.proof_obligation_id for row in failed_subclaims if row.proof_obligation_id
            ],
        },
        "simulation_plan": {
            "diagnostics": list(problem.diagnostics),
            "stress_tests": list(problem.stress_tests),
            "procedure_runs": [
                {
                    "procedure_id": procedure.id,
                    "design": procedure.simulation_design,
                    "passed": (
                        simulation_by_procedure[procedure.id].passed
                        if procedure.id in simulation_by_procedure
                        else False
                    ),
                    "diagnosis": (
                        simulation_by_procedure[procedure.id].diagnosis.status
                        if procedure.id in simulation_by_procedure and simulation_by_procedure[procedure.id].diagnosis
                        else "missing"
                    ),
                    "escalate_to": (
                        simulation_by_procedure[procedure.id].diagnosis.escalate_to
                        if procedure.id in simulation_by_procedure and simulation_by_procedure[procedure.id].diagnosis
                        else "missing"
                    ),
                    "metric_keys": sorted(simulation_by_procedure[procedure.id].metrics)
                    if procedure.id in simulation_by_procedure
                    else [],
                }
                for procedure in procedures
            ],
        },
        "next_iteration_agenda": next_iteration_agenda,
        "honesty_boundary": {
            "proved_subclaims": len(proved_subclaims),
            "formal_gaps": len(formal_gaps),
            "failed_subclaims": len(failed_subclaims),
            "simulation_flagged": any(not row.passed for row in simulations),
            "full_frontier_theorem_proved": False,
        },
    }


def _build_next_iteration_agenda(
    *,
    problem: ResearchProblemSpec,
    formal_gaps: list[FormalSubclaim],
    failed_subclaims: list[FormalSubclaim],
    theorem_goals: list[TheoremGoal],
    simulations: list[ResearchSimulation],
) -> dict[str, Any]:
    items: list[dict[str, Any]] = []
    for row in formal_gaps:
        required_primitives = _required_primitives_for_gap(row, theorem_goals)
        items.append(
            {
                "id": f"formal_gap:{row.id}",
                "owner_agent": "formal_verifier",
                "trigger": "FORMAL_GAP",
                "priority": "high" if required_primitives else "medium",
                "action": "retrieve_or_build_missing_lean_primitives",
                "evidence": row.gap_reason or row.title,
                "required_primitives": required_primitives,
                "target_theorem_goal": row.id.split(":")[-1],
            }
        )
    for row in failed_subclaims:
        items.append(
            {
                "id": f"failed_obligation:{row.id}",
                "owner_agent": "formal_verifier",
                "trigger": "FAILED_PROOF_OBLIGATION",
                "priority": "high",
                "action": "repair_axiom_verified_proof_or_downgrade_to_gap",
                "evidence": "; ".join(row.errors) or row.title,
                "required_primitives": list(row.proof_dependencies),
                "target_theorem_goal": row.proof_obligation_id or row.id,
            }
        )
    for row in simulations:
        diagnosis = row.diagnosis
        if diagnosis is None or diagnosis.status == "OK":
            continue
        owner_agent = {
            "theory_developer": "theory_developer",
            "algorithm_engineer": "algorithm_engineer",
            "simulator_environment": "simulator_agent",
            "rerun_more_mc": "simulator_agent",
        }.get(diagnosis.escalate_to, "research_coordinator")
        action = {
            "THEORY_OR_PROCEDURE_ISSUE": "revise_estimator_or_theorem_acceptance_rule",
            "IMPLEMENTATION_OR_NUMERICAL_ISSUE": "repair_algorithm_implementation_or_numerical_stability",
            "ENVIRONMENT_OR_DGP_ISSUE": "implement_or_correct_simulation_environment",
            "INSUFFICIENT_MC_PRECISION": "rerun_with_larger_monte_carlo_budget",
        }.get(diagnosis.status, "triage_simulation_failure")
        items.append(
            {
                "id": f"simulation:{row.procedure_id}",
                "owner_agent": owner_agent,
                "trigger": diagnosis.status,
                "priority": "high",
                "action": action,
                "evidence": diagnosis.rationale or row.feedback,
                "failed_diagnostics": list(diagnosis.failed_diagnostics),
                "failed_stress_tests": list(diagnosis.failed_stress_tests),
                "metric_evidence_keys": sorted(diagnosis.metric_evidence),
                "target_procedure": row.procedure_id,
            }
        )
    if not items:
        items.append(
            {
                "id": f"monitor:{problem.question_id}",
                "owner_agent": "research_coordinator",
                "trigger": "NO_BLOCKING_GAPS_OR_FAILED_SIMULATIONS",
                "priority": "low",
                "action": "archive_trace_or_expand_benchmark_stress_tests",
                "evidence": "All current proof obligations and simulation acceptance checks passed.",
                "required_primitives": [],
                "target_theorem_goal": "",
            }
        )
    owner_counts: dict[str, int] = {}
    for item in items:
        owner = str(item["owner_agent"])
        owner_counts[owner] = owner_counts.get(owner, 0) + 1
    return {
        "agenda_version": 1,
        "problem_class": problem.problem_class,
        "items": items,
        "owner_counts": dict(sorted(owner_counts.items())),
        "stop_condition": (
            "All agenda items are resolved, AXLE-verified obligations remain green, "
            "and simulations either pass or have an explicit accepted limitation."
        ),
    }


def _required_primitives_for_gap(row: FormalSubclaim, theorem_goals: list[TheoremGoal]) -> list[str]:
    goal_id = row.id.split(":")[-1]
    for goal in theorem_goals:
        if goal.id == goal_id:
            return list(goal.required_primitives)
    return []


async def run_research_benchmark(
    questions: list[OpenResearchQuestion],
    out_dir: Path,
    *,
    proof_verifier: ProofVerifier | None = None,
    formal_source_retriever: Any | None = None,
    formal_source_search: dict[str, str] | None = None,
    formal_source_index_path: Path | None = None,
    n_runs: int = 100,
    seed: int = 20260528,
) -> dict[str, Any]:
    if formal_source_search is None:
        formal_source_search = {
            "backend": "python_shape",
            "sqlite_index_path": "",
        }
    if formal_source_retriever is None and formal_source_index_path is not None:
        formal_source_retriever = build_formal_source_search_backend(db_path=formal_source_index_path)
        formal_source_search = {
            "backend": "sqlite_fts_hybrid",
            "sqlite_index_path": str(formal_source_index_path),
        }
    lab = AIStatisticalTheoryLab(
        proof_verifier=proof_verifier,
        formal_source_retriever=formal_source_retriever,
        n_runs=n_runs,
        seed=seed,
    )
    reports = [await lab.run(question) for question in questions]
    for report in reports:
        write_research_trace(report, out_dir)
    manifest = write_research_manifest(reports, out_dir, formal_source_search=formal_source_search)
    return json.loads(manifest.read_text(encoding="utf-8"))


def write_research_trace(report: ResearchReport, out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    export_formal_gap_skeletons(report, out_dir)
    path = out_dir / f"{report.question.id}.json"
    payload = {
        "trace_version": 1,
        "trace_kind": "research_theory_lab",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "provenance": build_research_provenance(),
        **report.to_json(),
    }
    path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    return path


def write_research_manifest(
    reports: list[ResearchReport],
    out_dir: Path,
    *,
    formal_source_search: dict[str, str] | None = None,
) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "trace_kind": "research_theory_lab",
        "provenance": build_research_provenance(),
        "formal_source_search": formal_source_search
        or {
            "backend": "python_shape",
            "sqlite_index_path": "",
        },
        "n_questions": len(reports),
        "n_ready_with_gaps": sum(1 for row in reports if row.status == "RESEARCH_TRACE_READY_WITH_FORMAL_GAPS"),
        "n_simulation_flagged": sum(1 for row in reports if row.status == "SIMULATION_FLAGGED_WITH_FORMAL_GAPS"),
        "n_formal_blocked": sum(1 for row in reports if row.status == "FORMAL_BLOCKED"),
        "questions": [compact_research_summary(row) for row in reports],
    }
    path = out_dir / "research_benchmark_manifest.json"
    path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    return path


def compact_research_summary(report: ResearchReport) -> dict[str, Any]:
    proved = sum(1 for row in report.formal_subclaims if row.status == "PROVED")
    gaps = sum(1 for row in report.formal_subclaims if row.status == "FORMAL_GAP")
    failed = sum(1 for row in report.formal_subclaims if row.status == "FAILED")
    formalized_gaps = sum(1 for row in report.formal_subclaims if row.status == "FORMAL_GAP" and row.lean_statement)
    kernel_verified = sum(1 for row in report.formal_subclaims if row.status == "PROVED" and row.kernel_verified)
    mock_verified = sum(
        1
        for row in report.formal_subclaims
        if row.status == "PROVED" and row.verification_strength == "mock_static_check"
    )
    proved_obligations = {
        row.proof_obligation_id
        for row in report.formal_subclaims
        if row.status == "PROVED" and row.proof_obligation_id
    }
    theorem_goal_support = [
        {
            "goal_id": goal.id,
            "proof_obligations": list(goal.proof_obligations),
            "n_proved_obligations": sum(
                1 for obligation_id in goal.proof_obligations if obligation_id in proved_obligations
            ),
        }
        for goal in report.theorem_goals
        if goal.proof_obligations
    ]
    return {
        "question": report.question.id,
        "status": report.status,
        "problem_class": report.problem.problem_class,
        "procedures": [row.id for row in report.procedures],
        "paper_sources": [
            {
                "id": row.id,
                "source_type": row.source_type,
                "title": row.title,
                "score": round(row.score, 3),
            }
            for row in report.paper_sources[:3]
        ],
        "algorithms": [
            {
                "procedure_id": row.id,
                "algorithm": row.algorithm,
                "registry_status": row.algorithm_spec.registry_status if row.algorithm_spec else "missing",
                "implementation_hash": row.algorithm_spec.implementation_hash if row.algorithm_spec else "",
            }
            for row in report.procedures
        ],
        "formal": {
            "proved": proved,
            "kernel_verified": kernel_verified,
            "mock_verified": mock_verified,
            "gaps": gaps,
            "failed": failed,
            "formalized_gaps": formalized_gaps,
            "theorem_goal_support": theorem_goal_support,
        },
        "simulations": [
            {
                "procedure_id": sim.procedure_id,
                "passed": sim.passed,
                "metrics": {key: round(value, 5) for key, value in sim.metrics.items()},
                "stress_tests": list(sim.stress_tests),
                "stress_test_metrics": {
                    name: {
                        key: round(value, 5)
                        for key, value in values.items()
                    }
                    for name, values in sim.stress_test_metrics.items()
                },
                "diagnosis": asdict(sim.diagnosis) if sim.diagnosis else {},
            }
            for sim in report.simulations
        ],
    }


def build_research_provenance() -> dict[str, str]:
    return {
        "proof_bank_fingerprint": proof_bank_fingerprint(),
        "research_knowledge_fingerprint": stable_hash([asdict(card) for card in KNOWLEDGE_CARDS]),
        "paper_source_index_fingerprint": paper_source_index_fingerprint(),
        "research_source_inventory_fingerprint": research_source_inventory_fingerprint(),
        "research_algorithm_registry_fingerprint": research_algorithm_registry_fingerprint(),
        "research_lab_version": "research_lab_v0",
    }


def attach_research_algorithm_metadata(procedures: list[CandidateProcedure]) -> list[CandidateProcedure]:
    return [
        replace(procedure, algorithm_spec=get_research_algorithm_spec(procedure.algorithm))
        for procedure in procedures
    ]


def get_research_algorithm_spec(algorithm_id: str) -> ResearchAlgorithmSpec:
    try:
        record = RESEARCH_ALGORITHM_REGISTRY[algorithm_id]
    except KeyError as exc:
        supported = ", ".join(sorted(RESEARCH_ALGORITHM_REGISTRY))
        raise KeyError(f"unknown research algorithm {algorithm_id!r}; supported: {supported}") from exc
    return ResearchAlgorithmSpec(
        id=algorithm_id,
        summary=str(record["summary"]),
        version=str(record["version"]),
        registry_status=str(record["registry_status"]),
        implementation_hash=_research_algorithm_hash(algorithm_id),
    )


def all_research_algorithm_specs() -> list[ResearchAlgorithmSpec]:
    return [get_research_algorithm_spec(algorithm_id) for algorithm_id in sorted(RESEARCH_ALGORITHM_REGISTRY)]


def research_algorithm_registry_fingerprint() -> str:
    return stable_hash([asdict(spec) for spec in all_research_algorithm_specs()])


def audit_research_algorithm_registry(out_dir: Path | None = None) -> dict[str, object]:
    rows = []
    for spec in all_research_algorithm_specs():
        errors: list[str] = []
        if spec.registry_status != "vetted":
            errors.append("registry_status is not vetted")
        if len(spec.implementation_hash) != 64:
            errors.append("implementation_hash is not a SHA-256 hex digest")
        if spec.id not in RESEARCH_ALGORITHM_REGISTRY:
            errors.append("algorithm id missing from registry")
        rows.append(
            {
                "algorithm_id": spec.id,
                "ok": not errors,
                "summary": spec.summary,
                "version": spec.version,
                "registry_status": spec.registry_status,
                "implementation_hash": spec.implementation_hash,
                "errors": errors,
            }
        )
    payload = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "registry_fingerprint": research_algorithm_registry_fingerprint(),
        "n_algorithms": len(rows),
        "n_ok": sum(1 for row in rows if row["ok"]),
        "all_ok": all(row["ok"] for row in rows),
        "algorithms": rows,
    }
    if out_dir is not None:
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "research_algorithm_audit_manifest.json").write_text(
            json.dumps(payload, indent=2, default=str),
            encoding="utf-8",
        )
    return payload


def _research_algorithm_hash(algorithm_id: str) -> str:
    record = RESEARCH_ALGORITHM_REGISTRY[algorithm_id]
    chunks: list[str] = [f"id={algorithm_id}", f"version={record['version']}"]
    method_name = str(record["method"])
    chunks.append(inspect.getsource(getattr(ResearchSimulator, method_name)))
    for helper_name in record.get("helpers", ()):
        chunks.append(inspect.getsource(globals()[str(helper_name)]))
    return hashlib.sha256("\n\n".join(chunks).encode("utf-8")).hexdigest()


def export_formal_gap_skeletons(report: ResearchReport, out_dir: Path) -> list[Path]:
    gap_dir = out_dir / "formal_gaps"
    paths: list[Path] = []
    for subclaim in report.formal_subclaims:
        if subclaim.status != "FORMAL_GAP" or not subclaim.lean_statement:
            continue
        gap_dir.mkdir(parents=True, exist_ok=True)
        path = gap_dir / f"{_safe_file_stem(subclaim.id)}.lean"
        path.write_text(subclaim.lean_statement, encoding="utf-8")
        subclaim.artifact_path = str(path)
        paths.append(path)
    return paths


def _report_limitations(subclaims: list[FormalSubclaim]) -> list[str]:
    gaps = [row.title for row in subclaims if row.status == "FORMAL_GAP"]
    if not gaps:
        return []
    return [
        "Full frontier theorem is not yet proved in Lean; current trace proves Mathlib-backed subclaims only.",
        "Formal gaps: " + "; ".join(gaps),
    ]


def _formal_source_query(problem: ResearchProblemSpec, goal: TheoremGoal) -> str:
    return " ".join(
        [
            problem.problem_class,
            problem.dgp,
            problem.estimand,
            " ".join(problem.assumptions),
            goal.title,
            goal.informal_statement,
            goal.proof_strategy,
            " ".join(goal.required_primitives),
            " ".join(goal.proof_obligations),
        ]
    )


def _formal_source_primitive_query(problem: ResearchProblemSpec, goal: TheoremGoal, primitive: str) -> str:
    return " ".join(
        [
            primitive,
            primitive.replace("_", " "),
            problem.problem_class,
            goal.title,
            goal.proof_strategy,
            " ".join(goal.proof_obligations),
        ]
    )


def _formal_source_hit_payload(hit: FormalSourceHit) -> dict[str, Any]:
    decl = hit.declaration
    return {
        "source_id": decl.source_id,
        "source_type": decl.source_type,
        "path": decl.path,
        "line": decl.line,
        "kind": decl.kind,
        "name": decl.name,
        "signature": decl.signature,
        "score": round(hit.score, 4),
        "matched_terms": list(hit.matched_terms),
    }


def _lean_gap_skeleton(
    problem: ResearchProblemSpec,
    goal: TheoremGoal,
    formal_source_hits: list[FormalSourceHit] | None = None,
    primitive_formal_source_hits: dict[str, list[dict[str, Any]]] | None = None,
) -> str:
    primitives = "\n".join(f"- {primitive}" for primitive in goal.required_primitives) or "- manual_formalization_required"
    support = "\n".join(f"- {obligation_id}" for obligation_id in goal.proof_obligations) or "- none"
    formal_sources = "\n".join(
        f"- {hit.declaration.name} ({hit.declaration.source_id}:{hit.declaration.path}:{hit.declaration.line})"
        for hit in (formal_source_hits or [])[:5]
    ) or "- none"
    primitive_sources = _format_primitive_formal_sources(primitive_formal_source_hits or {})
    header = f"""import Mathlib
open MeasureTheory ProbabilityTheory Filter

/-!
AI Statistician frontier theorem skeleton.

Problem class: {problem.problem_class}
Goal: {goal.title}
Informal statement: {goal.informal_statement}
Proof strategy: {goal.proof_strategy}

Missing formal primitives:
{primitives}

Proof-bank support already linked:
{support}

Retrieved local Lean/StatInference candidates:
{formal_sources}

Primitive-level local candidates:
{primitive_sources}

Status: FORMAL_GAP.
This file is intentionally not recorded as a verified theorem result.  The
placeholder assumption named `h_frontier_missing_*` marks the exact theory
library work still needed before this can become a real Lean theorem.
-/

namespace AIStatisticianResearchGaps

"""
    theorem = _lean_gap_theorem(goal.id)
    return header + theorem + "\nend AIStatisticianResearchGaps\n"


def _format_primitive_formal_sources(primitive_hits: dict[str, list[dict[str, Any]]]) -> str:
    if not primitive_hits:
        return "- none"
    lines: list[str] = []
    for primitive, hits in primitive_hits.items():
        if not hits:
            lines.append(f"- {primitive}: none")
            continue
        compact = ", ".join(
            f"{hit.get('name')} ({hit.get('source_id')}:{hit.get('line')})"
            for hit in hits[:3]
        )
        lines.append(f"- {primitive}: {compact}")
    return "\n".join(lines)


def _lean_gap_theorem(goal_id: str) -> str:
    skeletons = {
        "causal_identification": """theorem causal_identification_skeleton
    {Omega : Type*} [MeasurableSpace Omega]
    (mu : Measure Omega) [IsProbabilityMeasure mu]
    (psi identifiedFunctional : Real)
    (h_frontier_missing_identification : psi = identifiedFunctional) :
    psi = identifiedFunctional := by
  exact h_frontier_missing_identification
""",
        "aipw_double_robustness": """theorem aipw_double_robustness_skeleton
    {Omega : Type*} [MeasurableSpace Omega]
    (mu : Measure Omega) [IsProbabilityMeasure mu]
    (aipwScore : Omega -> Real) (psi : Real)
    (h_integrable : Integrable aipwScore mu)
    (h_frontier_missing_double_robustness :
      (integral mu fun omega => aipwScore omega) = psi) :
    (integral mu fun omega => aipwScore omega) = psi := by
  exact h_frontier_missing_double_robustness
""",
        "aipw_asymptotic_normality": """theorem aipw_asymptotic_normality_skeleton
    (nuisanceRateConditions : Prop)
    (sqrtNLimitNormal : Prop)
    (h_frontier_missing_empirical_process_clt :
      nuisanceRateConditions -> sqrtNLimitNormal) :
    nuisanceRateConditions -> sqrtNLimitNormal := by
  exact h_frontier_missing_empirical_process_clt
""",
        "split_conformal_finite_sample_coverage": """theorem split_conformal_finite_sample_coverage_skeleton
    {Omega : Type*} [MeasurableSpace Omega]
    (mu : Measure Omega) [IsProbabilityMeasure mu]
    (covered : Set Omega) (hcovered : MeasurableSet covered) (alpha : Real)
    (h_frontier_missing_exchangeable_rank_argument :
      1 - alpha <= mu.real covered) :
    1 - alpha <= mu.real covered := by
  exact h_frontier_missing_exchangeable_rank_argument
""",
        "independent_censoring_survival_identification": """theorem independent_censoring_survival_identification_skeleton
    (independentCensoring positiveAtRisk productLimitIdentifiesSurvival : Prop)
    (h_frontier_missing_censoring_identification :
      independentCensoring -> positiveAtRisk -> productLimitIdentifiesSurvival) :
    independentCensoring -> positiveAtRisk -> productLimitIdentifiesSurvival := by
  exact h_frontier_missing_censoring_identification
""",
        "kaplan_meier_fixed_time_asymptotic_normality": """theorem kaplan_meier_fixed_time_asymptotic_normality_skeleton
    (nelsonAalenMartingale greenwoodConsistent fixedTimeAsymptoticNormality : Prop)
    (h_frontier_missing_survival_martingale_clt :
      nelsonAalenMartingale -> greenwoodConsistent -> fixedTimeAsymptoticNormality) :
    nelsonAalenMartingale -> greenwoodConsistent -> fixedTimeAsymptoticNormality := by
  exact h_frontier_missing_survival_martingale_clt
""",
        "median_of_means_subgaussian_deviation": """theorem median_of_means_subgaussian_deviation_skeleton
    (finiteVarianceBlockMeans goodBlockMajority subGaussianDeviation : Prop)
    (h_frontier_missing_mom_deviation :
      finiteVarianceBlockMeans -> goodBlockMajority -> subGaussianDeviation) :
    finiteVarianceBlockMeans -> goodBlockMajority -> subGaussianDeviation := by
  exact h_frontier_missing_mom_deviation
""",
        "robust_mean_minimax_corruption_rate": """theorem robust_mean_minimax_corruption_rate_skeleton
    (contaminationModel starShapedConstraint minimaxRate : Prop)
    (h_frontier_missing_robust_mean_minimax :
      contaminationModel -> starShapedConstraint -> minimaxRate) :
    contaminationModel -> starShapedConstraint -> minimaxRate := by
  exact h_frontier_missing_robust_mean_minimax
""",
        "neyman_variance_conservative_validity": """theorem neyman_variance_conservative_validity_skeleton
    (completeRandomization exactRandomizationVariance neymanObservableBound : Prop)
    (h_frontier_missing_design_variance_algebra :
      completeRandomization -> exactRandomizationVariance -> neymanObservableBound) :
    completeRandomization -> exactRandomizationVariance -> neymanObservableBound := by
  exact h_frontier_missing_design_variance_algebra
""",
        "optimized_variance_bound_minimality": """theorem optimized_variance_bound_minimality_skeleton
    (compatiblePotentialOutcomes conservativeBound optimality : Prop)
    (h_frontier_missing_variance_bound_optimization :
      compatiblePotentialOutcomes -> conservativeBound -> optimality) :
    compatiblePotentialOutcomes -> conservativeBound -> optimality := by
  exact h_frontier_missing_variance_bound_optimization
""",
        "maximin_space_filling_surrogate_validity": """theorem maximin_space_filling_surrogate_validity_skeleton
    (finiteDesignSpace pairwiseDistanceObjective maximinSurrogate : Prop)
    (h_frontier_missing_maximin_design :
      finiteDesignSpace -> pairwiseDistanceObjective -> maximinSurrogate) :
    finiteDesignSpace -> pairwiseDistanceObjective -> maximinSurrogate := by
  exact h_frontier_missing_maximin_design
""",
        "covariate_balance_rerandomization_validity": """theorem covariate_balance_rerandomization_validity_skeleton
    (finiteAssignmentSpace symmetricRule balanceImproves randomizationValid : Prop)
    (h_frontier_missing_rerandomization_validity :
      finiteAssignmentSpace -> symmetricRule -> balanceImproves -> randomizationValid) :
    finiteAssignmentSpace -> symmetricRule -> balanceImproves -> randomizationValid := by
  exact h_frontier_missing_rerandomization_validity
""",
        "order_addition_stratum_orthogonality": """theorem order_addition_stratum_orthogonality_skeleton
    (finitePermutationDesign stratumOrthogonality modelFreeRobustness : Prop)
    (h_frontier_missing_stratum_orthogonality :
      finitePermutationDesign -> stratumOrthogonality -> modelFreeRobustness) :
    finitePermutationDesign -> stratumOrthogonality -> modelFreeRobustness := by
  exact h_frontier_missing_stratum_orthogonality
""",
        "ols_consistency": """theorem ols_slope_consistency_skeleton
    (betaHat : Nat -> Real) (beta : Real)
    (h_frontier_missing_lln_continuous_mapping :
      Tendsto betaHat atTop (nhds beta)) :
    Tendsto betaHat atTop (nhds beta) := by
  exact h_frontier_missing_lln_continuous_mapping
""",
        "hc1_asymptotic_normality": """theorem hc1_wald_coverage_skeleton
    {Omega : Type*} [MeasurableSpace Omega]
    (mu : Measure Omega) [IsProbabilityMeasure mu]
    (covered : Set Omega) (hcovered : MeasurableSet covered) (alpha : Real)
    (h_frontier_missing_sandwich_clt :
      1 - alpha <= mu.real covered) :
    1 - alpha <= mu.real covered := by
  exact h_frontier_missing_sandwich_clt
""",
        "bh_fdr_control_independence": """theorem bh_fdr_control_independence_skeleton
    (targetQ empiricalFDR : Real)
    (h_frontier_missing_bh_fdr_control :
      empiricalFDR <= targetQ) :
    empiricalFDR <= targetQ := by
  exact h_frontier_missing_bh_fdr_control
""",
        "bh_sparse_mixture_power": """theorem bh_sparse_mixture_power_skeleton
    (sparseMixtureRegime nontrivialPower : Prop)
    (h_frontier_missing_sparse_mixture_power :
      sparseMixtureRegime -> nontrivialPower) :
    sparseMixtureRegime -> nontrivialPower := by
  exact h_frontier_missing_sparse_mixture_power
""",
        "eprocess_optional_stopping_control": """theorem eprocess_optional_stopping_control_skeleton
    {Omega : Type*} [MeasurableSpace Omega]
    (mu : Measure Omega) [IsProbabilityMeasure mu]
    (crossesBoundary : Set Omega) (hcrosses : MeasurableSet crossesBoundary)
    (alpha : Real)
    (h_frontier_missing_ville_inequality :
      mu.real crossesBoundary <= alpha) :
    mu.real crossesBoundary <= alpha := by
  exact h_frontier_missing_ville_inequality
""",
        "bernoulli_lr_eprocess_martingale": """theorem bernoulli_lr_eprocess_martingale_skeleton
    (likelihoodRatioProcess nullMartingale : Prop)
    (h_frontier_missing_conditional_expectation_product :
      likelihoodRatioProcess -> nullMartingale) :
    likelihoodRatioProcess -> nullMartingale := by
  exact h_frontier_missing_conditional_expectation_product
""",
        "functional_cusum_changepoint_localization": """theorem functional_cusum_changepoint_localization_skeleton
    (functionalTimeSeries partialMeasurementError populationSeparation localization : Prop)
    (h_frontier_missing_functional_cusum :
      functionalTimeSeries -> partialMeasurementError -> populationSeparation -> localization) :
    functionalTimeSeries -> partialMeasurementError -> populationSeparation -> localization := by
  exact h_frontier_missing_functional_cusum
""",
        "post_detection_changepoint_confidence_set": """theorem post_detection_changepoint_confidence_set_skeleton
    (stoppingRule selectedInterval detectorErrorControl postDetectionCoverage : Prop)
    (h_frontier_missing_post_detection :
      stoppingRule -> selectedInterval -> detectorErrorControl -> postDetectionCoverage) :
    stoppingRule -> selectedInterval -> detectorErrorControl -> postDetectionCoverage := by
  exact h_frontier_missing_post_detection
""",
        "sequential_model_confidence_set_validity": """theorem sequential_model_confidence_set_validity_skeleton
    (candidateLossProcess eliminationRule finiteTimeUnionControl modelConfidenceCoverage : Prop)
    (h_frontier_missing_model_confidence :
      candidateLossProcess -> eliminationRule -> finiteTimeUnionControl -> modelConfidenceCoverage) :
    candidateLossProcess -> eliminationRule -> finiteTimeUnionControl -> modelConfidenceCoverage := by
  exact h_frontier_missing_model_confidence
""",
        "metric_graph_kernel_prediction_consistency": """theorem metric_graph_kernel_prediction_consistency_skeleton
    (metricGraph kernelWeights denseSampling smoothField predictionConsistency : Prop)
    (h_frontier_missing_metric_graph_kernel :
      metricGraph -> kernelWeights -> denseSampling -> smoothField -> predictionConsistency) :
    metricGraph -> kernelWeights -> denseSampling -> smoothField -> predictionConsistency := by
  exact h_frontier_missing_metric_graph_kernel
""",
        "spde_matern_field_likelihood_validity": """theorem spde_matern_field_likelihood_validity_skeleton
    (gaussianField spdeMaternCovariance positiveOperator likelihoodValid : Prop)
    (h_frontier_missing_spde_matern :
      gaussianField -> spdeMaternCovariance -> positiveOperator -> likelihoodValid) :
    gaussianField -> spdeMaternCovariance -> positiveOperator -> likelihoodValid := by
  exact h_frontier_missing_spde_matern
""",
        "point_process_intensity_contrast_validity": """theorem point_process_intensity_contrast_validity_skeleton
    (countingMeasure kernelIntensityEstimator minimumContrast selectionConsistent : Prop)
    (h_frontier_missing_point_process_intensity :
      countingMeasure -> kernelIntensityEstimator -> minimumContrast -> selectionConsistent) :
    countingMeasure -> kernelIntensityEstimator -> minimumContrast -> selectionConsistent := by
  exact h_frontier_missing_point_process_intensity
""",
        "superposed_palm_mixture_representation": """theorem superposed_palm_mixture_representation_skeleton
    (independentPointProcesses superposition intensityWeightedMixture palmLaw : Prop)
    (h_frontier_missing_palm_mixture :
      independentPointProcesses -> superposition -> intensityWeightedMixture -> palmLaw) :
    independentPointProcesses -> superposition -> intensityWeightedMixture -> palmLaw := by
  exact h_frontier_missing_palm_mixture
""",
        "spiked_pca_population_target": """theorem spiked_pca_population_target_skeleton
    (rankOneSpikedCovariance leadingEigenspaceIsSignal : Prop)
    (h_frontier_missing_spectral_theory :
      rankOneSpikedCovariance -> leadingEigenspaceIsSignal) :
    rankOneSpikedCovariance -> leadingEigenspaceIsSignal := by
  exact h_frontier_missing_spectral_theory
""",
        "spiked_pca_high_dimensional_recovery": """theorem spiked_pca_high_dimensional_recovery_skeleton
    (covarianceConcentration davisKahanBound highDimensionalRecovery : Prop)
    (h_frontier_missing_random_matrix_perturbation :
      covarianceConcentration -> davisKahanBound -> highDimensionalRecovery) :
    covarianceConcentration -> davisKahanBound -> highDimensionalRecovery := by
  exact h_frontier_missing_random_matrix_perturbation
""",
        "latent_simplex_membership_identifiability": """theorem latent_simplex_membership_identifiability_skeleton
    (simplexMembership profileSeparation anchorCondition identifiableUpToPermutation : Prop)
    (h_frontier_missing_latent_simplex_identifiability :
      simplexMembership -> profileSeparation -> anchorCondition -> identifiableUpToPermutation) :
    simplexMembership -> profileSeparation -> anchorCondition -> identifiableUpToPermutation := by
  exact h_frontier_missing_latent_simplex_identifiability
""",
        "sufficient_dimension_association_selection_validity": """theorem sufficient_dimension_association_selection_validity_skeleton
    (associationTarget screeningStatistic signalSeparation selectionConsistent : Prop)
    (h_frontier_missing_sdr_selection :
      associationTarget -> screeningStatistic -> signalSeparation -> selectionConsistent) :
    associationTarget -> screeningStatistic -> signalSeparation -> selectionConsistent := by
  exact h_frontier_missing_sdr_selection
""",
        "tensor_multilinear_reduction_consistency": """theorem tensor_multilinear_reduction_consistency_skeleton
    (tensorCovariate multilinearReduction modewiseSignal tensorSelectionConsistent : Prop)
    (h_frontier_missing_tensor_multilinear_reduction :
      tensorCovariate -> multilinearReduction -> modewiseSignal -> tensorSelectionConsistent) :
    tensorCovariate -> multilinearReduction -> modewiseSignal -> tensorSelectionConsistent := by
  exact h_frontier_missing_tensor_multilinear_reduction
""",
        "hill_tail_index_consistency": """theorem hill_tail_index_consistency_skeleton
    (regularlyVaryingTail intermediateSequence hillConsistent : Prop)
    (h_frontier_missing_order_statistic_tail_theory :
      regularlyVaryingTail -> intermediateSequence -> hillConsistent) :
    regularlyVaryingTail -> intermediateSequence -> hillConsistent := by
  exact h_frontier_missing_order_statistic_tail_theory
""",
        "weissman_high_quantile_consistency": """theorem weissman_high_quantile_consistency_skeleton
    (hillConsistent tailQuantileRegularVariation weissmanConsistent : Prop)
    (h_frontier_missing_extreme_quantile_theory :
      hillConsistent -> tailQuantileRegularVariation -> weissmanConsistent) :
    hillConsistent -> tailQuantileRegularVariation -> weissmanConsistent := by
  exact h_frontier_missing_extreme_quantile_theory
""",
        "gaussian_mechanism_dp_calibration": """theorem gaussian_mechanism_dp_calibration_skeleton
    (boundedSensitivity gaussianNoiseCalibrated epsilonDeltaDP : Prop)
    (h_frontier_missing_dp_gaussian_mechanism :
      boundedSensitivity -> gaussianNoiseCalibrated -> epsilonDeltaDP) :
    boundedSensitivity -> gaussianNoiseCalibrated -> epsilonDeltaDP := by
  exact h_frontier_missing_dp_gaussian_mechanism
""",
        "private_mean_error_decomposition": """theorem private_mean_error_decomposition_skeleton
    (clippedMeanUnbiasedUpToBias independentPrivacyNoise privateVarianceFormula : Prop)
    (h_frontier_missing_private_error_decomposition :
      clippedMeanUnbiasedUpToBias -> independentPrivacyNoise -> privateVarianceFormula) :
    clippedMeanUnbiasedUpToBias -> independentPrivacyNoise -> privateVarianceFormula := by
  exact h_frontier_missing_private_error_decomposition
""",
        "private_learning_excess_risk_rate": """theorem private_learning_excess_risk_rate_skeleton
    (uniformConvergence privateReleaseStability excessRiskRate : Prop)
    (h_frontier_missing_private_learning_theory :
      uniformConvergence -> privateReleaseStability -> excessRiskRate) :
    uniformConvergence -> privateReleaseStability -> excessRiskRate := by
  exact h_frontier_missing_private_learning_theory
""",
        "sieve_regression_pointwise_error_decomposition": """theorem sieve_regression_pointwise_error_decomposition_skeleton
    (sieveApproximation empiricalErrorBound pointwiseWaldValid : Prop)
    (h_frontier_missing_sieve_error_decomposition :
      sieveApproximation -> empiricalErrorBound -> pointwiseWaldValid) :
    sieveApproximation -> empiricalErrorBound -> pointwiseWaldValid := by
  exact h_frontier_missing_sieve_error_decomposition
""",
        "ensemble_subsampling_inference_validity": """theorem ensemble_subsampling_inference_validity_skeleton
    (subsamplingFunctional hajekProjectionDominates inferenceValid : Prop)
    (h_frontier_missing_subsampling_u_statistic_theory :
      subsamplingFunctional -> hajekProjectionDominates -> inferenceValid) :
    subsamplingFunctional -> hajekProjectionDominates -> inferenceValid := by
  exact h_frontier_missing_subsampling_u_statistic_theory
""",
        "penalized_spline_selection_consistency": """theorem penalized_spline_selection_consistency_skeleton
    (splineBasisPenalty stableTuning selectedEstimatorRate : Prop)
    (h_frontier_missing_penalized_spline_selection :
      splineBasisPenalty -> stableTuning -> selectedEstimatorRate) :
    splineBasisPenalty -> stableTuning -> selectedEstimatorRate := by
  exact h_frontier_missing_penalized_spline_selection
""",
        "predictive_prior_translation_coherence": """theorem predictive_prior_translation_coherence_skeleton
    (predictiveDistribution translatedPrior coherenceFunctionalPreserved : Prop)
    (h_frontier_missing_predictive_prior_translation :
      predictiveDistribution -> translatedPrior -> coherenceFunctionalPreserved) :
    predictiveDistribution -> translatedPrior -> coherenceFunctionalPreserved := by
  exact h_frontier_missing_predictive_prior_translation
""",
        "normal_conjugate_posterior_mean_error_decomposition": """theorem normal_conjugate_posterior_mean_error_decomposition_skeleton
    (normalConjugatePosterior sampleMeanError shrinkageBias errorDecomposition : Prop)
    (h_frontier_missing_conjugate_error_decomposition :
      normalConjugatePosterior -> sampleMeanError -> shrinkageBias -> errorDecomposition) :
    normalConjugatePosterior -> sampleMeanError -> shrinkageBias -> errorDecomposition := by
  exact h_frontier_missing_conjugate_error_decomposition
""",
        "posterior_credible_interval_calibration": """theorem posterior_credible_interval_calibration_skeleton
    (posteriorPivot credibleInterval priorPredictiveCoverage : Prop)
    (h_frontier_missing_posterior_calibration :
      posteriorPivot -> credibleInterval -> priorPredictiveCoverage) :
    posteriorPivot -> credibleInterval -> priorPredictiveCoverage := by
  exact h_frontier_missing_posterior_calibration
""",
        "bias_adjusted_assessment_mean_identification": """theorem bias_adjusted_assessment_mean_identification_skeleton
    (measurementModel calibratedBias adjustedMeanIdentifiesAbility : Prop)
    (h_frontier_missing_measurement_bias_identification :
      measurementModel -> calibratedBias -> adjustedMeanIdentifiesAbility) :
    measurementModel -> calibratedBias -> adjustedMeanIdentifiesAbility := by
  exact h_frontier_missing_measurement_bias_identification
""",
        "assessment_ranking_uncertainty_validity": """theorem assessment_ranking_uncertainty_validity_skeleton
    (countryMeanIntervals rankSeparation rankingUncertaintyValid : Prop)
    (h_frontier_missing_ranking_uncertainty_theory :
      countryMeanIntervals -> rankSeparation -> rankingUncertaintyValid) :
    countryMeanIntervals -> rankSeparation -> rankingUncertaintyValid := by
  exact h_frontier_missing_ranking_uncertainty_theory
""",
        "measurement_invariance_bias_model_validity": """theorem measurement_invariance_bias_model_validity_skeleton
    (irtModel measurementInvarianceConstraints biasIdentifiable : Prop)
    (h_frontier_missing_measurement_invariance_model :
      irtModel -> measurementInvarianceConstraints -> biasIdentifiable) :
    irtModel -> measurementInvarianceConstraints -> biasIdentifiable := by
  exact h_frontier_missing_measurement_invariance_model
""",
    }
    return skeletons.get(
        goal_id,
        """theorem manual_theory_development_required_skeleton
    (frontierQuestion formalizationTarget : Prop)
    (h_frontier_missing_manual_formalization :
      frontierQuestion -> formalizationTarget) :
    frontierQuestion -> formalizationTarget := by
  exact h_frontier_missing_manual_formalization
""",
    )


def _safe_file_stem(raw: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", raw)


def _sigmoid(x: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-x))


def _matches(text: str, *, words: tuple[str, ...], phrases: tuple[str, ...] = ()) -> bool:
    token_set = set(re.findall(r"[a-z0-9_]+", text.lower()))
    return bool(token_set & set(words)) or any(phrase in text for phrase in phrases)


def _problem_extraction_evidence(
    problem: ResearchProblemSpec,
    *,
    source_text: str,
    full_text: str,
) -> dict[str, tuple[str, ...]]:
    terms_by_field = EXTRACTION_EVIDENCE_TERMS.get(problem.problem_class, {})
    haystack = source_text.lower()
    full_haystack = full_text.lower()
    evidence: dict[str, tuple[str, ...]] = {}
    for field in ("problem_class", "dgp", "estimand", "assumptions", "asymptotic_regime"):
        terms = terms_by_field.get(field, ())
        matches = _matched_evidence_terms(haystack, terms)
        if field == "problem_class" and not matches:
            matches = _matched_evidence_terms(full_haystack, terms)
        evidence[field] = matches
    if problem.problem_class == "unsupported_frontier_question":
        evidence["unsupported_reason"] = (
            "no registered deterministic problem-class evidence matched the body text",
        )
    return evidence


def _matched_evidence_terms(text: str, terms: tuple[str, ...]) -> tuple[str, ...]:
    token_set = set(re.findall(r"[a-z0-9_]+", text.lower()))
    matches: list[str] = []
    for term in terms:
        normalized = term.lower()
        if re.fullmatch(r"[a-z0-9_]+", normalized):
            if normalized in token_set:
                matches.append(term)
        elif normalized in text:
            matches.append(term)
    return tuple(dict.fromkeys(matches))


def _poly_design(x: np.ndarray) -> np.ndarray:
    return np.column_stack([np.ones_like(x), x, x**2, x**3])


def _sieve_design(x: np.ndarray, degree: int) -> np.ndarray:
    arr = np.asarray(x, dtype=float)
    return np.column_stack([arr**j for j in range(degree + 1)])


def _rank_positions(values: np.ndarray) -> np.ndarray:
    arr = np.asarray(values, dtype=float)
    order = np.argsort(-arr, kind="mergesort")
    ranks = np.empty(len(arr), dtype=float)
    ranks[order] = np.arange(1, len(arr) + 1, dtype=float)
    return ranks


def _min_pairwise_distance(points: np.ndarray) -> float:
    arr = np.asarray(points, dtype=float)
    if arr.ndim != 2 or arr.shape[0] < 2:
        return 0.0
    diffs = arr[:, None, :] - arr[None, :, :]
    distances = np.sqrt(np.sum(diffs**2, axis=2))
    upper = distances[np.triu_indices(arr.shape[0], k=1)]
    return float(np.min(upper)) if upper.size else 0.0


def _path_graph_distances(n_vertices: int) -> np.ndarray:
    positions = np.linspace(0.0, 1.0, int(n_vertices))
    return np.abs(positions[:, None] - positions[None, :])


def _rbf_kernel(distance: np.ndarray, bandwidth: float) -> np.ndarray:
    bw = max(float(bandwidth), 1e-8)
    return np.exp(-0.5 * (np.asarray(distance, dtype=float) / bw) ** 2)


def _simulate_inhomogeneous_poisson_1d(
    rng: np.random.Generator,
    intensity: np.ndarray,
    bin_width: float,
    n_samples: int,
) -> np.ndarray:
    rates = np.maximum(np.asarray(intensity, dtype=float) * float(bin_width), 1e-12)
    return rng.poisson(lam=rates[None, :], size=(int(n_samples), len(rates)))


def _project_rows_to_simplex(values: np.ndarray) -> np.ndarray:
    arr = np.asarray(values, dtype=float)
    projected = np.zeros_like(arr)
    for idx, row in enumerate(arr):
        ordered = np.sort(row)[::-1]
        cumulative = np.cumsum(ordered) - 1.0
        ranks = np.arange(1, len(row) + 1, dtype=float)
        valid = ordered - cumulative / ranks > 0.0
        if not np.any(valid):
            projected[idx, :] = 1.0 / len(row)
            continue
        rho = int(np.flatnonzero(valid)[-1])
        theta = float(cumulative[rho] / (rho + 1))
        projected[idx, :] = np.maximum(row - theta, 0.0)
    return projected


def _best_permutation_score(true_weights: np.ndarray, estimated_weights: np.ndarray) -> tuple[tuple[int, ...], float]:
    k = int(true_weights.shape[1])
    best_perm: tuple[int, ...] | None = None
    best_rmse = float("inf")
    for perm in itertools.permutations(range(k)):
        aligned = estimated_weights[:, perm]
        rmse = float(np.sqrt(np.mean((aligned - true_weights) ** 2)))
        if rmse < best_rmse:
            best_perm = tuple(int(item) for item in perm)
            best_rmse = rmse
    return best_perm or tuple(range(k)), best_rmse


def _orthonormal_basis(matrix: np.ndarray) -> np.ndarray:
    arr = np.asarray(matrix, dtype=float)
    if arr.ndim != 2 or min(arr.shape) == 0:
        return np.zeros((arr.shape[0] if arr.ndim else 0, 0))
    q, r = np.linalg.qr(arr, mode="reduced")
    if r.ndim != 2:
        return q
    keep = np.abs(np.diag(r)) > 1e-10
    if not np.any(keep):
        return q[:, :1]
    return q[:, keep]


def _functional_changepoint_projection(
    rng: np.random.Generator,
    *,
    n: int,
    tau: int,
    contrast: np.ndarray,
    shift_size: float,
    ar: float,
    missing_prob: float,
    measurement_noise: float,
) -> np.ndarray:
    grid_size = len(contrast)
    state = np.zeros(grid_size)
    projected: list[float] = []
    denom_full = float(np.sum(contrast**2))
    for t in range(n):
        state = ar * state + rng.normal(scale=0.75, size=grid_size)
        mean_shift = shift_size * contrast if t >= tau else 0.0
        full = state + mean_shift
        observed = rng.random(grid_size) > missing_prob
        if not np.any(observed):
            observed[int(rng.integers(0, grid_size))] = True
        noisy = full[observed] + rng.normal(scale=measurement_noise, size=int(np.sum(observed)))
        local_contrast = contrast[observed]
        denom = max(float(np.sum(local_contrast**2)), 1e-8)
        projected.append(float(np.sum(noisy * local_contrast) / denom * math.sqrt(denom / denom_full)))
    return np.asarray(projected, dtype=float)


def _cusum_changepoint_estimate(series: np.ndarray, *, min_segment: int) -> tuple[float, float]:
    values = np.asarray(series, dtype=float)
    n = len(values)
    if n < 2 * min_segment + 1:
        return float("nan"), float("nan")
    prefix = np.cumsum(values)
    total = float(prefix[-1])
    best_k = min_segment
    best_stat = -float("inf")
    for k in range(min_segment, n - min_segment):
        left_mean = float(prefix[k - 1] / k)
        right_mean = float((total - prefix[k - 1]) / (n - k))
        stat = math.sqrt(k * (n - k) / n) * abs(left_mean - right_mean)
        if stat > best_stat:
            best_stat = stat
            best_k = k
    return float(best_k), float(best_stat)


def _nonlinear_regression_sample(rng: np.random.Generator, n: int) -> tuple[np.ndarray, np.ndarray]:
    x = rng.uniform(-2.0, 2.0, size=n)
    y = np.sin(1.5 * x) + 0.25 * x**2 + rng.normal(scale=0.45, size=n)
    return x, y


def _normal_two_sided_pvalues(z: np.ndarray) -> np.ndarray:
    return np.asarray([math.erfc(abs(float(value)) / math.sqrt(2.0)) for value in z], dtype=float)


def _kaplan_meier_at_time(observed_time: np.ndarray, event: np.ndarray, t0: float) -> tuple[float, float]:
    times = np.asarray(observed_time, dtype=float)
    events = np.asarray(event, dtype=bool)
    event_times = np.unique(times[(times <= t0) & events])
    survival = 1.0
    greenwood_sum = 0.0
    for time in np.sort(event_times):
        at_risk = int(np.sum(times >= time))
        n_events = int(np.sum((times == time) & events))
        if at_risk <= 0 or n_events <= 0:
            continue
        survival *= max(0.0, 1.0 - n_events / at_risk)
        if at_risk > n_events:
            greenwood_sum += n_events / (at_risk * (at_risk - n_events))
    se = survival * math.sqrt(max(greenwood_sum, 0.0))
    return float(survival), float(se)


def _median_of_means(sample: np.ndarray, n_blocks: int) -> tuple[float, np.ndarray]:
    arr = np.asarray(sample, dtype=float)
    blocks = [block for block in np.array_split(arr, n_blocks) if len(block)]
    block_means = np.asarray([float(np.mean(block)) for block in blocks], dtype=float)
    return float(np.median(block_means)), block_means


def _estimation_metrics(estimates: list[float], ses: list[float], target: float, n_trials: int) -> dict[str, float]:
    arr = np.asarray(estimates, dtype=float)
    se_arr = np.asarray(ses, dtype=float)
    if len(arr) == 0:
        return {
            "n_runs": float(n_trials),
            "n_failed": float(n_trials),
            "target": float(target),
            "estimate_mean": float("nan"),
            "bias": float("nan"),
            "relative_bias": float("nan"),
            "rmse": float("nan"),
            "empirical_se": float("nan"),
            "mean_estimated_se": float("nan"),
            "coverage_95": 0.0,
            "se_ratio": float("nan"),
        }
    lower = arr - 1.96 * se_arr
    upper = arr + 1.96 * se_arr
    bias = float(np.mean(arr) - target)
    empirical_se = float(np.std(arr, ddof=1)) if len(arr) > 1 else 0.0
    mean_se = float(np.mean(se_arr)) if len(se_arr) else float("nan")
    return {
        "n_runs": float(n_trials),
        "n_failed": float(max(n_trials - len(arr), 0)),
        "target": float(target),
        "estimate_mean": float(np.mean(arr)),
        "bias": bias,
        "relative_bias": bias / (abs(target) + 1e-12),
        "rmse": float(np.sqrt(np.mean((arr - target) ** 2))),
        "empirical_se": empirical_se,
        "mean_estimated_se": mean_se,
        "coverage_95": float(np.mean((lower <= target) & (target <= upper))),
        "se_ratio": mean_se / (empirical_se + 1e-12),
    }
