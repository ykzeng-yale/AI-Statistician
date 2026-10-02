"""Validate evaluator mathematics and failure behavior, not product capability."""

from copy import deepcopy
from fractions import Fraction
import math

import pytest

from benchmarks.publication_development.fixed_k_l2_20261002 import numerical_evaluator as evaluator


def exact_candidate(*, runtime=False):
    samples = list(map(float, evaluator.finite_experiment_values()))
    row = {"metrics": {"evaluation_mode": "exact_enumeration", "objective_values": samples,
                       "mean_objective": sum(samples) / len(samples), "mcse": 0,
                       "n_cases": 64, "requested_runtime_replicates": 64},
           "execution_attempted": True, "execution_smoke_passed": True, "runtime_replicates": 64}
    if runtime:
        return {"generated_simulation_rows": [row], "evaluator_source_confirmation": True,
                "empirical_evaluation_phase": "confirmatory_evaluator_execution"}
    row["execution_phase"] = "confirmatory_evaluator_execution"
    return {"generated_simulation_rows": [row]}


def test_complete_small_finite_law_and_admissibility():
    law = evaluator.finite_experiment_values()
    assert len(law) == 64 and sum(law) / len(law) == Fraction(1237, 384)
    assert evaluator.segment_cost([[1], [2], [3]], 0, 3) == 2
    assert evaluator.partition_values([[0]] * 5, 1, 2, 2) == {(2, 5): 0}
    assert evaluator.partition_values([[0]] * 5, 2, 2, 2) == {}
    assert evaluator.partition_values([[0]], 0, 1, 5) == {(1,): 0}


def test_all_finite_requests_and_arbitrary_tie_choices():
    def independently_select(request):
        values = evaluator.partition_values(request["signal"], request["n_changes"], request["min_size"], request["jump"])
        if not values:
            return {"feasible": False, "breakpoints": [], "objective": None}
        optimum = min(values.values())
        selected = max(ends for ends, value in values.items() if value == optimum)
        return {"feasible": True, "breakpoints": list(selected), "objective": float(optimum)}

    result = evaluator.run_sandbox(730109, 1, {"fixed_k_l2": independently_select})
    assert result["all_cases_passed"] and result["cases"] == 648
    assert result["feasible_cases"] + result["infeasible_cases"] == 648
    failed = evaluator.run_sandbox(730109, 1, {"fixed_k_l2": lambda request: {"feasible": False, "breakpoints": [], "objective": None}})
    assert not failed["all_cases_passed"] and failed["failures"]


@pytest.mark.parametrize("runtime", [False, True])
def test_only_selected_confirmation_can_supply_numerical_compatibility(runtime):
    candidate = exact_candidate(runtime=runtime)
    before = deepcopy(candidate)
    assert evaluator.evaluate_artifact(candidate, 1, 1)["compatible_numerical_experiment"]
    assert candidate == before
    candidate["generated_simulation_rows"][0]["execution_phase"] = "exploratory_diagnostic"
    assert not evaluator.evaluate_artifact(candidate, 1, 1)["compatible_numerical_experiment"]


@pytest.mark.parametrize("field,value", [
    ("mean_objective", None), ("mean_objective", "unknown"), ("mean_objective", float("nan")),
    ("n_cases", 63), ("mcse", 0.1), ("evaluation_mode", "unrecognised"),
    ("objective_values", None), ("objective_values", [float("inf")] * 64),
    ("objective_values", [0] * 64), ("requested_runtime_replicates", 65),
])
def test_malformed_or_wrong_numerical_evidence_does_not_pass(field, value):
    candidate = exact_candidate()
    candidate["generated_simulation_rows"][0]["metrics"][field] = value
    assert not evaluator.evaluate_artifact(candidate, 1, 1)["compatible_numerical_experiment"]


def test_fixed_count_mcse_and_mean_checks_are_not_a_source_generation_certificate():
    candidate = exact_candidate()
    row = candidate["generated_simulation_rows"][0]
    samples = row["metrics"]["objective_values"] * 256
    count, mean = len(samples), sum(samples) / len(samples)
    row.update(runtime_replicates=count)
    row["metrics"].update(evaluation_mode="monte_carlo", objective_values=samples, n_cases=count,
                          requested_runtime_replicates=count, mean_objective=mean,
                          mcse=math.sqrt(sum((value - mean) ** 2 for value in samples) / (count * (count - 1))))
    result = evaluator.evaluate_artifact(candidate, 1, 1)
    assert result["compatible_numerical_experiment"]
    assert result["scope"] == "numerical_compatibility_not_source_generation_or_mathematical_certification"
    row["metrics"]["mcse"] = "unknown"
    assert not evaluator.evaluate_artifact(candidate, 1, 1)["compatible_numerical_experiment"]
