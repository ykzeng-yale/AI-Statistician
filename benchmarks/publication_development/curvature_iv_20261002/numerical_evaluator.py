"""Hidden numerical authority for a fresh development task, never a model tool."""

from fractions import Fraction
import math
import random


def exact_reference(request):
    z, d, y = (list(map(Fraction, request[key])) for key in ("z", "d", "y"))
    n = len(z)
    weights = [value * value - 2 for value in z]
    denominator = sum(w * value for w, value in zip(weights, d)) / n
    if not denominator:
        return {"status": "zero_moment", "beta": None, "standard_error": None,
                "n": n, "moment_denominator": 0.0}
    beta = sum(w * value for w, value in zip(weights, y)) / (n * denominator)
    variance = sum((w * (value - beta * treatment)) ** 2
                   for w, value, treatment in zip(weights, y, d)) / (n * n * denominator ** 2)
    return {"status": "ok", "beta": float(beta), "standard_error": math.sqrt(float(variance)),
            "n": n, "moment_denominator": float(denominator)}


def requests(seed):
    rng = random.Random(seed)
    for n in (2, 5, 11, 30):
        for pattern in range(8):
            z = [rng.choice((-2, -1, 0, 1, 2)) for _ in range(n)]
            d = [rng.randint(-5, 5) for _ in z]
            y = [rng.randint(-7, 7) for _ in z]
            if pattern == 0:
                d = [0] * n
            yield {"z": z, "d": d, "y": y}
    for scale in (-3, 1, 4):
        yield {"z": [-2, -1, 0, 1, 2], "d": [4, 1, 0, 1, 4],
               "y": [scale * value for value in (4, 1, 0, 1, 4)]}


def run_sandbox(seed, replicates, estimators):
    failures = []
    cases = 0
    for request in requests(seed):
        expected, actual = exact_reference(request), estimators["curvature_iv"](request)
        cases += 1
        errors = []
        if not isinstance(actual, dict):
            errors.append("non-object result")
        else:
            for field in ("status", "n"):
                if type(actual.get(field)) is not type(expected[field]) or actual.get(field) != expected[field]:
                    errors.append(field)
            for field in ("beta", "standard_error", "moment_denominator"):
                value, target = actual.get(field), expected[field]
                if target is None:
                    good = value is None
                else:
                    good = (type(value) in (int, float) and math.isfinite(value)
                            and math.isclose(value, target, rel_tol=1e-9, abs_tol=1e-10))
                if not good:
                    errors.append(field)
        if errors:
            failures.append({"case": cases, "fields": errors, "request": request,
                             "expected": expected, "actual": actual})
    return {"all_cases_passed": not failures, "cases": cases, "failures": failures}


def evaluate_artifact(candidate, seed, replicates):
    selected_confirmation = (candidate.get("evaluator_source_confirmation") is True
                             and candidate.get("empirical_evaluation_phase") == "confirmatory_evaluator_execution")
    rows = [row for row in candidate.get("generated_simulation_rows", []) if isinstance(row, dict)
            and (row.get("execution_phase") == "confirmatory_evaluator_execution"
                 or (selected_confirmation and row.get("execution_phase") != "exploratory_diagnostic"))]
    errors = []
    if len(rows) != 1:
        return {"compatible_numerical_experiment": False, "errors": ["exactly one selected confirmation is required"]}
    row = rows[0]
    metrics = row.get("metrics", {})
    scenarios = metrics.get("scenarios", []) if isinstance(metrics, dict) else []
    expected = {"positive_curvature": (0.5, 2.0), "negative_curvature": (-0.75, -1.0)}
    if (not isinstance(scenarios, list) or len(scenarios) != 2
        or any(not isinstance(item, dict) for item in scenarios)
        or {item.get("scenario_id") for item in scenarios} != set(expected)):
        return {"compatible_numerical_experiment": False, "errors": ["both frozen scenarios are required"]}
    for item in scenarios:
        name = item["scenario_id"]
        count, estimates, ses = item.get("n_replicates"), item.get("estimates"), item.get("standard_errors")
        if (type(count) is not int or count < 1000 or item.get("n") != 600
            or (item.get("a"), item.get("beta_true")) != expected[name]
            or not isinstance(estimates, list) or not isinstance(ses, list)
            or len(estimates) != count or len(ses) != count):
            errors.append(name + ": missing conditions or complete sample vectors")
            continue
        valid = [type(value) in (int, float) and math.isfinite(value)
                 and type(se) in (int, float) and math.isfinite(se) and se >= 0
                 for value, se in zip(estimates, ses)]
        failures = count - sum(valid)
        if (item.get("failed_replicates") != failures
            or any(not ok and (value is not None or se is not None)
                   for ok, value, se in zip(valid, estimates, ses))):
            errors.append(name + ": failed-slot accounting")
        values = [value for value, ok in zip(estimates, valid) if ok]
        if len(values) < 2:
            errors.append(name + ": fewer than two numerical successes")
            continue
        truth = expected[name][1]
        mean = sum(values) / len(values)
        bias_mcse = math.sqrt(sum((value - mean) ** 2 for value in values) / (len(values) * (len(values) - 1)))
        coverage = sum(ok and abs(value - truth) <= 1.959963984540054 * se
                       for value, se, ok in zip(estimates, ses, valid)) / count
        coverage_mcse = math.sqrt(coverage * (1 - coverage) / count)
        for field, target in (("mean_error", mean - truth), ("bias_mcse", bias_mcse),
                              ("coverage", coverage), ("coverage_mcse", coverage_mcse)):
            value = item.get(field)
            if not (type(value) in (int, float) and math.isfinite(value)
                    and math.isclose(value, target, rel_tol=1e-7, abs_tol=1e-9)):
                errors.append(name + ": inconsistent " + field)
        if failures or coverage_mcse > 0.01 or abs(mean - truth) > 0.02 + 3 * bias_mcse:
            errors.append(name + ": numerical failure, precision or bias criterion")
        if abs(coverage - 0.95) > 0.025 + 3 * coverage_mcse:
            errors.append(name + ": coverage compatibility criterion")
        if (bias_mcse == 0 or metrics.get("requested_runtime_replicates") != count
            or row.get("runtime_replicates") != count):
            errors.append(name + ": missing variable fresh sample or count identity")
    if row.get("execution_attempted") is not True or row.get("execution_smoke_passed") is not True:
        errors.append("successful exact-source confirmation missing")
    return {"compatible_numerical_experiment": not errors, "errors": errors,
            "scope": "submitted_numerical_compatibility_not_theory_or_autonomous_scientific_acceptance"}
