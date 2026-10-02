"""Evaluator-only exact finite checks; never an author tool or repair recipe."""

from fractions import Fraction
from itertools import combinations, product
import math
import random


def segment_cost(rows, start, end):
    total = Fraction(0)
    for coordinate in zip(*rows[start:end]):
        mean = sum(map(Fraction, coordinate)) / (end - start)
        total += sum((Fraction(value) - mean) ** 2 for value in coordinate)
    return total


def partition_values(rows, changes, minimum, jump):
    n = len(rows)
    costs = {(a, b): segment_cost(rows, a, b) for a in range(n) for b in range(a + minimum, n + 1)}
    values = {}
    for interior in combinations(range(jump, n, jump), changes):
        ends, starts = interior + (n,), (0,) + interior
        if all(b - a >= minimum for a, b in zip(starts, ends)):
            values[ends] = sum(costs[a, b] for a, b in zip(starts, ends))
    return values


def requests(seed):
    rng = random.Random(seed)
    for n, d in product((1, 2, 3, 6, 9, 11), (1, 2)):
        for pattern in ("constant", "noise"):
            rows = [[coordinate + 1 if pattern == "constant" else rng.randint(-6, 6)
                     for coordinate in range(d)] for _ in range(n)]
            for changes, minimum, jump in product(range(3), (1, 2, 4), (1, 2, 5)):
                yield {"signal": rows, "n_changes": changes, "min_size": minimum, "jump": jump}


def finite_experiment_values():
    return [min(partition_values([[mean + noise] for mean, noise in zip((0, 0, 0, 1, 1, 1), noises)],
                                 1, 2, 1).values()) for noises in product((-1, 1), repeat=6)]


def run_sandbox(seed, replicates, estimators):
    failures, checked, feasible, infeasible = [], 0, 0, 0
    for request in requests(seed):
        values = partition_values(request["signal"], request["n_changes"], request["min_size"], request["jump"])
        result = estimators["fixed_k_l2"](request)
        checked += 1
        valid = isinstance(result, dict) and type(result.get("feasible")) is bool
        if values:
            feasible += 1
            ends = result.get("breakpoints", []) if isinstance(result, dict) else []
            value = result.get("objective") if isinstance(result, dict) else None
            valid = (valid and result["feasible"] is True and isinstance(ends, list)
                     and all(type(item) is int for item in ends) and tuple(ends) in values
                     and values[tuple(ends)] == min(values.values())
                     and type(value) in (int, float) and math.isfinite(value)
                     and math.isclose(value, float(min(values.values())), rel_tol=1e-10, abs_tol=1e-10))
        else:
            infeasible += 1
            valid = valid and result["feasible"] is False and result.get("breakpoints") == [] and result.get("objective") is None
        if not valid:
            failures.append({"case": checked, "request": request, "returned": result})
    return {"all_cases_passed": not failures, "cases": checked, "feasible_cases": feasible,
            "infeasible_cases": infeasible, "failures": failures}


def evaluate_artifact(candidate, seed, replicates):
    selected_confirmation = (candidate.get("evaluator_source_confirmation") is True
                             and candidate.get("empirical_evaluation_phase") == "confirmatory_evaluator_execution")
    rows = [row for row in candidate.get("generated_simulation_rows", [])
            if isinstance(row, dict) and (row.get("execution_phase") == "confirmatory_evaluator_execution"
            or (selected_confirmation and row.get("execution_phase") != "exploratory_diagnostic"))]
    errors = []
    if len(rows) != 1:
        return {"compatible_numerical_experiment": False, "errors": ["exactly one selected confirmation is required"]}
    row = rows[0]
    metrics = row.get("metrics", {})
    if not isinstance(metrics, dict):
        return {"compatible_numerical_experiment": False, "errors": ["missing numerical metrics"]}
    samples = metrics.get("objective_values", [])
    count = metrics.get("n_cases")
    mode = metrics.get("evaluation_mode")
    law = finite_experiment_values()
    exact_mean = float(sum(law) / len(law))
    if (type(count) is not int or count < 1 or not isinstance(samples, list) or len(samples) != count
        or any(type(value) not in (int, float) or not math.isfinite(value) for value in samples)):
        return {"compatible_numerical_experiment": False, "errors": ["missing or invalid actual numerical sample vector"]}
    mean = sum(samples) / count
    reported_mean = metrics.get("mean_objective")
    if type(reported_mean) not in (int, float) or not math.isclose(reported_mean, mean, rel_tol=1e-10, abs_tol=1e-10):
        errors.append("reported mean does not match submitted samples")
    support = {float(value) for value in law}
    if any(not any(math.isclose(value, allowed, rel_tol=1e-10, abs_tol=1e-10) for allowed in support) for value in samples):
        errors.append("sample objective outside the exact finite support")
    if mode == "exact_enumeration":
        if count != 64 or any(not math.isclose(a, float(b), rel_tol=1e-10, abs_tol=1e-10)
                              for a, b in zip(sorted(samples), sorted(law))) or metrics.get("mcse") != 0:
            errors.append("exact integration does not match the complete equally likely finite law")
    elif mode == "monte_carlo" and count >= 1000:
        se = math.sqrt(sum((value - mean) ** 2 for value in samples) / (count * (count - 1)))
        if (type(metrics.get("mcse")) not in (int, float)
            or not math.isclose(metrics["mcse"], se, rel_tol=1e-8, abs_tol=1e-10)
            or se > 0.02 or abs(mean - exact_mean) > 3 * se + 1e-10):
            errors.append("fixed-count numerical precision or mean compatibility check failed")
    else:
        errors.append("unknown mode or inadequate Monte Carlo sample count")
    if (row.get("execution_attempted") is not True or row.get("execution_smoke_passed") is not True
        or metrics.get("requested_runtime_replicates") != count or row.get("runtime_replicates") != count):
        errors.append("sample count or successful fresh execution identity is missing")
    return {"compatible_numerical_experiment": not errors, "errors": errors,
            "exact_reference_mean": exact_mean, "candidate_mean": mean,
            "scope": "numerical_compatibility_not_source_generation_or_mathematical_certification"}
