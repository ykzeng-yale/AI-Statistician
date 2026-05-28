from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path
from typing import Any

from .intake import infer_dgp_family, infer_estimator_family, infer_tags, infer_true_params
from .fingerprint import stable_hash
from .schema import EstimatorSpec, StatisticalQuestion
from .theory_proposal import TheoryProposer, proposal_to_json


QUESTIONS: dict[str, StatisticalQuestion] = {
    "normal_mean": StatisticalQuestion(
        id="normal_mean",
        title="Estimate the mean of a normal distribution",
        dgp="X_i iid Normal(mu=2.0, sigma=1.5)",
        target="mu = E[X]",
        dgp_family="normal",
        estimator_family="sample_mean",
        true_params={"mu": 2.0, "sigma": 1.5},
        n_obs=80,
        tags=("mean", "normal", "expectation"),
    ),
    "bernoulli_probability": StatisticalQuestion(
        id="bernoulli_probability",
        title="Estimate an event probability from Bernoulli observations",
        dgp="X_i iid Bernoulli(p=0.20)",
        target="p = P(X=1)",
        dgp_family="bernoulli",
        estimator_family="sample_proportion",
        true_params={"p": 0.20},
        n_obs=120,
        tags=("bernoulli", "probability", "indicator"),
    ),
    "normal_variance": StatisticalQuestion(
        id="normal_variance",
        title="Estimate the variance of a normal distribution",
        dgp="X_i iid Normal(mu=2.0, sigma=1.5)",
        target="sigma^2 = Var(X)",
        dgp_family="normal",
        estimator_family="sample_variance",
        true_params={"mu": 2.0, "sigma": 1.5},
        n_obs=90,
        tags=("variance", "normal"),
    ),
    "constant_mean": StatisticalQuestion(
        id="constant_mean",
        title="Sanity check: estimate a constant mean",
        dgp="X_i = c almost surely, c=3.0",
        target="c = E[X]",
        dgp_family="constant",
        estimator_family="constant_estimator",
        true_params={"c": 3.0},
        n_obs=20,
        tags=("constant", "mean", "expectation"),
    ),
}


ESTIMATOR_FAMILIES: dict[str, EstimatorSpec] = {
    "sample_mean": EstimatorSpec(
        id="sample_mean_normal",
        question_id="<question>",
        formula="hat_mu = n^{-1} sum_i X_i; CI = hat_mu +/- 1.96 * s/sqrt(n)",
        algorithm="sample_mean_normal_ci",
        guarantee="Asymptotic normality by CLT; finite-sample exact normal CI under normal DGP.",
        formal_obligation_ids=(
            "mean2_estimator_expectation",
            "mean2_estimator_unbiased",
            "mean2_estimator_variance_indep",
            "finite_sample_mean_unbiased",
            "finite_sample_mean_variance_indep",
            "finite_sample_mean_chebyshev_indep",
            "estimator_error_chebyshev",
            "mean2_estimator_chebyshev_indep",
            "variance_nonneg",
        ),
        notes=(
            "The current formal obligations verify Mathlib-backed expectation "
            "linearity, finite two-component unbiasedness, finite-sample "
            "arithmetic-mean unbiasedness and pairwise-independent variance "
            "identity over Fin n, a finite-sample Chebyshev error bound for "
            "arithmetic means under pairwise independence, independence-based "
            "variance reduction for averaging two estimators, a Chebyshev "
            "finite-sample error bound, a composed Chebyshev bound for an "
            "average of two independent estimators, and variance nonnegativity, "
            "not a full CLT proof."
        ),
    ),
    "sample_proportion": EstimatorSpec(
        id="sample_proportion_wilson",
        question_id="<question>",
        formula="hat_p = n^{-1} sum_i X_i; Wilson score CI for 95% coverage",
        algorithm="bernoulli_wilson_ci",
        guarantee="Consistency and asymptotic normality of the sample proportion.",
        formal_obligation_ids=(
            "event_indicator_expectation",
            "finite_event_indicator_mean_unbiased",
            "prob_compl",
            "prob_measure_univ",
        ),
        notes=(
            "The event-indicator expectation obligation is a genuine estimator "
            "property: E[1_A] = P(A). The finite event-indicator mean obligation "
            "formalizes unbiasedness of a finite sample-proportion estimator under "
            "common event probability."
        ),
    ),
    "sample_variance": EstimatorSpec(
        id="sample_variance_normal",
        question_id="<question>",
        formula="hat_sigma2 = (n-1)^{-1} sum_i (X_i - Xbar)^2; chi-square CI under normal DGP",
        algorithm="sample_variance_chi_square_ci",
        guarantee="Unbiased normal sample variance; exact chi-square finite-sample interval under normal DGP.",
        formal_obligation_ids=("variance_nonneg", "variance_indep_add"),
        notes=(
            "The current formal obligations verify Mathlib-backed variance facts "
            "used around this estimator, not the full finite-sample distribution of sample variance."
        ),
    ),
    "constant_estimator": EstimatorSpec(
        id="constant_estimator",
        question_id="<question>",
        formula="hat_c = c for all observations",
        algorithm="constant_mean",
        guarantee="Unbiased with zero variance.",
        formal_obligation_ids=(
            "constant_estimator_unbiased",
            "constant_estimator_variance_zero",
            "integral_of_constant",
        ),
    ),
}


ESTIMATORS: dict[str, EstimatorSpec] = {
    qid: replace(ESTIMATOR_FAMILIES[q.estimator_family], question_id=qid)
    for qid, q in QUESTIONS.items()
}


def question_registry_fingerprint() -> str:
    return stable_hash(
        [
            {
                "id": question.id,
                "title": question.title,
                "dgp": question.dgp,
                "target": question.target,
                "dgp_family": question.dgp_family,
                "estimator_family": question.estimator_family,
                "true_params": question.true_params,
                "n_obs": question.n_obs,
                "tags": question.tags,
            }
            for question in sorted(QUESTIONS.values(), key=lambda row: row.id)
        ]
    )


def estimator_registry_fingerprint() -> str:
    return stable_hash(
        [
            {
                "family": family,
                "id": estimator.id,
                "formula": estimator.formula,
                "algorithm": estimator.algorithm,
                "guarantee": estimator.guarantee,
                "formal_obligation_ids": estimator.formal_obligation_ids,
                "notes": estimator.notes,
            }
            for family, estimator in sorted(ESTIMATOR_FAMILIES.items())
        ]
    )


def get_question(question_id: str) -> StatisticalQuestion:
    try:
        return QUESTIONS[question_id]
    except KeyError as exc:
        raise KeyError(f"unknown question: {question_id}") from exc


def get_estimator_for_question(question_id: str) -> EstimatorSpec:
    try:
        return ESTIMATORS[question_id]
    except KeyError as exc:
        raise KeyError(f"no estimator registered for question: {question_id}") from exc


def derive_estimator_for_question(question: StatisticalQuestion) -> EstimatorSpec:
    try:
        template = ESTIMATOR_FAMILIES[question.estimator_family]
    except KeyError as exc:
        supported = ", ".join(sorted(ESTIMATOR_FAMILIES))
        raise KeyError(
            f"unsupported estimator_family {question.estimator_family!r}; supported: {supported}"
        ) from exc
    return replace(template, question_id=question.id)


def question_from_json(
    data: dict[str, Any],
    *,
    theory_proposer: TheoryProposer | None = None,
    force_theory_proposer: bool = False,
) -> StatisticalQuestion:
    required = {
        "id",
        "dgp",
        "target",
        "n_obs",
    }
    missing = sorted(required - set(data))
    if missing:
        raise ValueError(f"question JSON missing required keys: {', '.join(missing)}")
    if "true_params" in data and not isinstance(data["true_params"], dict):
        raise ValueError("question JSON field true_params must be an object")
    tags = data.get("tags") or ()
    if isinstance(tags, str):
        tags = (tags,)
    tags = tuple(str(tag) for tag in tags)
    dgp = str(data["dgp"])
    target = str(data["target"])
    proposal = None
    if theory_proposer is not None and force_theory_proposer:
        proposal = theory_proposer.propose(data).validated()

    if proposal is None:
        try:
            dgp_family = str(data.get("dgp_family") or infer_dgp_family(dgp, target, tags))
            estimator_family = str(
                data.get("estimator_family") or infer_estimator_family(dgp_family, target, tags)
            )
            true_params = infer_true_params(dgp_family, dgp, data.get("true_params"))
        except ValueError:
            if theory_proposer is None:
                raise
            proposal = theory_proposer.propose(data).validated()
    if proposal is not None:
        proposal_json = proposal_to_json(proposal)
        dgp_family = str(data.get("dgp_family") or proposal.dgp_family)
        estimator_family = str(data.get("estimator_family") or proposal.estimator_family)
        true_params = infer_true_params(
            dgp_family,
            dgp,
            data.get("true_params") or proposal.true_params,
        )
        tags = tuple(dict.fromkeys([*tags, *proposal.tags, f"proposal_source:{proposal.source}"]))
    else:
        proposal_json = None
    tags = infer_tags(
        dgp_family=dgp_family,
        estimator_family=estimator_family,
        target=target,
        provided=tags,
    )
    return StatisticalQuestion(
        id=str(data["id"]),
        title=str(data.get("title") or data["id"]),
        dgp=dgp,
        target=target,
        dgp_family=dgp_family,
        estimator_family=estimator_family,
        true_params=true_params,
        n_obs=int(data["n_obs"]),
        tags=tuple([*tags, f"theory_proposal:{proposal_json['source']}"] if proposal_json else tags),
    )


def load_question_file(
    path: Path,
    *,
    theory_proposer: TheoryProposer | None = None,
    force_theory_proposer: bool = False,
) -> list[StatisticalQuestion]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, list):
        return [
            question_from_json(
                row,
                theory_proposer=theory_proposer,
                force_theory_proposer=force_theory_proposer,
            )
            for row in data
        ]
    if isinstance(data, dict) and isinstance(data.get("questions"), list):
        return [
            question_from_json(
                row,
                theory_proposer=theory_proposer,
                force_theory_proposer=force_theory_proposer,
            )
            for row in data["questions"]
        ]
    if isinstance(data, dict):
        return [
            question_from_json(
                data,
                theory_proposer=theory_proposer,
                force_theory_proposer=force_theory_proposer,
            )
        ]
    raise ValueError(f"unsupported question JSON shape in {path}")
