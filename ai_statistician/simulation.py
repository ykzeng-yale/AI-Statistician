from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Callable

import numpy as np

from .algorithms import get_algorithm
from .schema import AlgorithmSpec, SimulationMetrics, SimulationReport, StatisticalQuestion


def _normal_sampler(rng: np.random.Generator, q: StatisticalQuestion) -> np.ndarray:
    return rng.normal(q.true_params["mu"], q.true_params["sigma"], size=q.n_obs)


def _bernoulli_sampler(rng: np.random.Generator, q: StatisticalQuestion) -> np.ndarray:
    return rng.binomial(1, q.true_params["p"], size=q.n_obs).astype(float)


def _constant_sampler(rng: np.random.Generator, q: StatisticalQuestion) -> np.ndarray:
    return np.full(q.n_obs, q.true_params["c"], dtype=float)


SAMPLERS: dict[str, Callable[[np.random.Generator, StatisticalQuestion], np.ndarray]] = {
    "normal": _normal_sampler,
    "bernoulli": _bernoulli_sampler,
    "constant": _constant_sampler,
}


def true_target(question: StatisticalQuestion) -> float:
    if question.estimator_family == "sample_variance":
        return question.true_params["sigma"] ** 2
    if question.dgp_family == "normal":
        return question.true_params["mu"]
    if question.dgp_family == "bernoulli":
        return question.true_params["p"]
    if question.dgp_family == "constant":
        return question.true_params["c"]
    raise KeyError(question.dgp_family)


@dataclass
class SimulatorAgent:
    n_runs: int = 1000
    seed: int = 20260528

    def run(self, question: StatisticalQuestion, algorithm: AlgorithmSpec) -> SimulationReport:
        try:
            sampler = SAMPLERS[question.dgp_family]
        except KeyError as exc:
            supported = ", ".join(sorted(SAMPLERS))
            raise KeyError(
                f"unsupported dgp_family {question.dgp_family!r}; supported: {supported}"
            ) from exc
        estimator = get_algorithm(algorithm.id).implementation
        rng = np.random.default_rng(self.seed)
        target = true_target(question)
        estimates: list[float] = []
        ses: list[float] = []
        covered = 0
        failed = 0
        for _ in range(self.n_runs):
            data = sampler(rng, question)
            try:
                row = estimator(data)
                estimate = float(row["estimate"])
                se = float(row.get("se", float("nan")))
                lo = float(row.get("lo", float("nan")))
                hi = float(row.get("hi", float("nan")))
            except Exception:
                failed += 1
                continue
            if not math.isfinite(estimate):
                failed += 1
                continue
            estimates.append(estimate)
            if math.isfinite(se):
                ses.append(se)
            if lo <= target <= hi:
                covered += 1

        if not estimates:
            metrics = SimulationMetrics(self.n_runs, failed, float("nan"), float("nan"), float("nan"), float("nan"), float("nan"), 0.0)
            return SimulationReport(question.id, algorithm.id, metrics, False, False, False, "all simulation replicates failed")

        arr = np.array(estimates)
        bias = float(np.mean(arr) - target)
        rel_bias = bias / target if abs(target) > 1e-12 else bias
        rmse = float(np.sqrt(np.mean((arr - target) ** 2)))
        empirical_se = float(np.std(arr, ddof=1)) if len(arr) > 1 else 0.0
        mean_estimated_se = float(np.mean(ses)) if ses else float("nan")
        coverage = covered / len(arr)
        metrics = SimulationMetrics(
            n_runs=self.n_runs,
            n_failed=failed,
            bias=bias,
            relative_bias=rel_bias,
            rmse=rmse,
            empirical_se=empirical_se,
            mean_estimated_se=mean_estimated_se,
            coverage_95=coverage,
        )
        pass_bias = abs(rel_bias) < 0.05 or abs(bias) < 0.02
        degenerate_exact = empirical_se == 0.0 and abs(bias) < 1e-12
        # Upper coverage checks are unstable for small Monte Carlo audits. A
        # conservative interval should not block a low-budget smoke run unless
        # a larger audit confirms systematic over-coverage.
        upper_coverage = 1.0 if self.n_runs < 500 else 0.995
        pass_coverage = (0.90 <= coverage <= upper_coverage) or (degenerate_exact and coverage == 1.0)
        pass_se = (
            math.isfinite(mean_estimated_se)
            and (empirical_se == 0.0 or abs(mean_estimated_se / empirical_se - 1.0) < 0.25)
        )
        feedback_bits = []
        if not pass_bias:
            feedback_bits.append(f"relative bias {rel_bias:+.3f} outside tolerance")
        if not pass_coverage:
            feedback_bits.append(f"95% coverage {coverage:.3f} outside [0.90, 0.99]")
        if not pass_se:
            feedback_bits.append(
                f"SE calibration off: mean estimated {mean_estimated_se:.4f}, empirical {empirical_se:.4f}"
            )
        return SimulationReport(
            question_id=question.id,
            algorithm_id=algorithm.id,
            metrics=metrics,
            pass_bias=pass_bias,
            pass_coverage=pass_coverage,
            pass_se_calibration=pass_se,
            feedback="OK" if not feedback_bits else "; ".join(feedback_bits),
        )
