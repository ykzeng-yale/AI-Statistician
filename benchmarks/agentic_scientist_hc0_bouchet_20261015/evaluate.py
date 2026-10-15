"""Frozen development simulation evaluator; never a mathematical certificate.

The CLI always executes 12 cells x 5,000 datasets. Only the Python helper permits
smaller mechanism fixtures. Candidate code supplies run_estimator, not the DGP,
truth, reference, aggregation, or official artifacts. This native import boundary
is not a security sandbox; the calling harness owns process/resource isolation.

Monte Carlo uncertainty is across independent datasets within a cell, not across
coefficients, cells, or agent runs. Mean MCSEs use sample SD / sqrt(m); Bernoulli
MCSEs use sqrt(p*(1-p)/m). For nonlinear summaries, plug-in delta influences are:
  RMSE: (error**2 - mean(error**2)) / (2*RMSE)
  empirical SD: c*((estimate-mean(estimate))**2 - v) / (2*SD)
  RMS SE: (SE**2 - mean(SE**2)) / (2*RMS_SE)
where v is the central second moment with divisor m and c=m/(m-1). For RMS_SE/SD,
the influence is IF_RMS_SE/SD - RMS_SE*IF_SD/SD**2. Taking the sample SD of this
paired influence / sqrt(m) retains covariance between numerator and denominator.
These are first-order MCSEs (requiring finite relevant moments), not exact small-m
intervals. Singular derivatives and m<2 have null MCSE, never fabricated precision.

Performance uses inference-usable outputs, INCLUDING reference mismatches. It is
conditional on usability when outputs fail. Numerical failure rates additionally
count reference mismatches/unavailable checks. Unattempted rows are not successes
or observed failures. No coverage, power, bias, or MCSE threshold gates correctness.
"""

from __future__ import annotations

import argparse
from collections.abc import Mapping
import contextlib
from datetime import datetime, timezone
import hashlib
import importlib.util
import io
import json
import math
from pathlib import Path
import platform
from statistics import NormalDist
import sys
import time
import traceback
import warnings

import numpy as np


MASTER_SEED = 2026101517
REPETITIONS = 5000
REFERENCE_VERSION = "0.14.6"
RTOL, ATOL = 1e-6, 1e-9
CRITICAL_VALUE = NormalDist().inv_cdf(0.975)
METHODS = ("candidate_hc0", "conventional_ols")
CELLS = tuple(
    {"cell_id": index, "n": n, "beta1": beta1, "variance": variance}
    for index, (n, beta1, variance) in enumerate(
        (n, beta1, variance)
        for n in (50, 200, 1000)
        for beta1 in (0.0, 0.2)
        for variance in ("homoskedastic", "heteroskedastic")
    )
)
OUTPUT_NAMES = (
    "study_started.json", "source_before.json", "replicates.jsonl", "summaries.json", "study.json",
    "metrics.json", "correct.json",
)


def _json_safe(value):
    """Preserve invalid returns in strict JSON, including explicit nonfinite tags."""
    if isinstance(value, np.ndarray):
        return _json_safe(value.tolist())
    if isinstance(value, np.generic):
        return _json_safe(value.item())
    if isinstance(value, float) and not math.isfinite(value):
        return {"nonfinite": str(value)}
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    return {"python_type": type(value).__name__, "repr": repr(value)}


def _write_json(path, value):
    with path.open("x", encoding="utf-8") as stream:
        json.dump(_json_safe(value), stream, indent=2, allow_nan=False)
        stream.write("\n")


def _sha256(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def _source_hashes(root):
    hashes = {}
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root)
        if "__pycache__" in relative.parts or path.suffix in {".pyc", ".pyo"}:
            continue
        if path.is_symlink():
            raise ValueError(f"Source symlinks are outside the frozen source-tree contract: {relative}")
        if path.is_file():
            hashes[relative.as_posix()] = _sha256(path)
    return hashes


def generate_dataset(cell, replicate):
    """A dataset's PCG64 stream depends only on its stable cell/replicate key."""
    seed = np.random.SeedSequence(MASTER_SEED, spawn_key=(cell["cell_id"], replicate))
    draws = np.random.Generator(np.random.PCG64(seed)).standard_normal((cell["n"], 3))
    x = np.column_stack((np.ones(cell["n"]), draws[:, :2]))
    variance = (np.ones(cell["n"]) if cell["variance"] == "homoskedastic"
                else (1.0 + 4.0 * x[:, 1] ** 2) / 5.0)
    truth = np.array([0.0, cell["beta1"], 1.0])
    y = x @ truth + np.sqrt(variance) * draws[:, 2]
    return x, y


def _observe(call):
    stdout, stderr = io.StringIO(), io.StringIO()
    value, error = None, None
    start = time.perf_counter()
    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            try:
                value = call()
            except (Exception, SystemExit):
                error = traceback.format_exc()
    return value, {
        "error": error, "stdout": stdout.getvalue(), "stderr": stderr.getvalue(),
        "warnings": [{"category": type(item.message).__name__, "message": str(item.message)}
                     for item in caught],
        "elapsed_seconds": time.perf_counter() - start,
    }


def _load_candidate(path):
    spec = importlib.util.spec_from_file_location("hc0_evaluation_candidate", path)
    if spec is None or spec.loader is None:
        raise ValueError("Cannot import candidate entrypoint")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    # Execute the hashed source, not a potentially stale timestamp-based pyc.
    exec(compile(path.read_bytes(), str(path), "exec"), module.__dict__)
    function = getattr(module, "run_estimator", None)
    if not callable(function):
        raise TypeError("Candidate must export callable run_estimator(request)")
    return function


def _reference_methods(x, y):
    import statsmodels.api as sm

    fit = sm.OLS(y, x).fit(use_t=False)
    robust = fit.get_robustcov_results(cov_type="HC0", use_t=False)

    def output(result):
        return {"coefficients": result.params, "covariance": result.cov_params(),
                "standard_errors": result.bse}

    return output(robust), output(fit)


def _check_output(raw, reference=None):
    checks, values = {}, {}
    for key, shape in (("coefficients", (3,)), ("covariance", (3, 3)), ("standard_errors", (3,))):
        check = {"shape": False, "finite": False, "numeric": False,
                 "allclose": None, "error": None}
        try:
            if not isinstance(raw, Mapping):
                raise TypeError("run_estimator must return a mapping")
            array = np.asarray(raw[key])
            check["shape"] = array.shape == shape
            check["numeric"] = array.dtype.kind in "iuf"
            if check["numeric"]:
                array = array.astype(float)
                check["finite"] = bool(np.all(np.isfinite(array)))
            if all(check[name] for name in ("shape", "finite", "numeric")):
                values[key] = array
                if reference is not None:
                    check["allclose"] = bool(np.allclose(array, reference[key], rtol=RTOL, atol=ATOL))
        except Exception:
            check["error"] = traceback.format_exc()
        checks[key] = check
    usable = len(values) == 3
    inference_error = None
    if usable:
        try:
            if not np.all(values["standard_errors"] > 0):
                raise ValueError("Standard errors must be positive for this nondegenerate design")
            with np.errstate(over="raise", invalid="raise"):
                lower = values["coefficients"] - CRITICAL_VALUE * values["standard_errors"]
                upper = values["coefficients"] + CRITICAL_VALUE * values["standard_errors"]
                # Finite returns can still overflow performance calculations.
                np.square(values["coefficients"])
                np.square(values["standard_errors"])
                length = upper - lower
            values.update(lower=lower, upper=upper, length=length)
        except Exception:
            usable = False
            inference_error = traceback.format_exc()
    agreement = reference is not None and all(check["allclose"] for check in checks.values())
    return values, checks, bool(usable), bool(agreement), inference_error


def _method_record(raw, observation, reference=None, *, require_reference=False):
    values, checks, usable, agreement, inference_error = _check_output(raw, reference)
    usable = usable and observation["error"] is None
    serialization_error = None
    try:
        retained_raw = _json_safe(raw)
    except Exception:
        serialization_error = traceback.format_exc()
        try:
            representation = repr(raw)
        except Exception:
            representation = "unavailable: repr also raised"
        retained_raw = {"python_type": type(raw).__name__, "repr": representation}
        usable = False
    compliant = usable and (agreement or not require_reference)
    status = ("exception" if observation["error"] else "invalid_output" if not usable
              else "reference_unavailable" if require_reference and reference is None
              else "reference_mismatch" if not compliant else "ok")
    record = {
        **observation, "status": status, "usable": usable, "compliant": compliant,
        "raw_output": retained_raw, "checks": checks, "inference_error": inference_error,
        "serialization_error": serialization_error,
        "interval_lower": values["lower"].tolist() if usable else None,
        "interval_upper": values["upper"].tolist() if usable else None,
    }
    return record, values if usable else None


def _mcse(influence):
    if len(influence) < 2:
        return None
    result = float(np.std(influence, ddof=1) / math.sqrt(len(influence)))
    return result if math.isfinite(result) else None


def _mean_measure(values, *, bernoulli=False):
    if not len(values):
        return {"estimate": None, "mcse": None}
    mean = float(np.mean(values))
    mcse = math.sqrt(mean * (1.0 - mean) / len(values)) if bernoulli else _mcse(values)
    return {"estimate": mean, "mcse": mcse}


def summarize_performance(estimates, standard_errors, truth):
    """Summarize one coefficient; delta uncertainty is documented above."""
    estimates, standard_errors = np.asarray(estimates), np.asarray(standard_errors)
    names = ("bias", "rmse", "empirical_sd", "rms_se", "se_sd_ratio", "coverage",
             "mean_interval_length", "rejection")
    if len(estimates) == 0:
        return {name: {"estimate": None, "mcse": None} for name in names}
    count = len(estimates)
    errors = estimates - truth
    squares, se_squares = errors ** 2, standard_errors ** 2
    mse, mean_se_squared = float(np.mean(squares)), float(np.mean(se_squares))
    rmse, rms_se = math.sqrt(mse), math.sqrt(mean_se_squared)
    sd = float(np.std(estimates, ddof=1)) if count > 1 else None
    sd_if = None
    if sd is not None and sd > 0:
        centered_squared = (estimates - np.mean(estimates)) ** 2
        sd_if = count / (count - 1) * (centered_squared - np.mean(centered_squared)) / (2 * sd)
    rms_if = (se_squares - mean_se_squared) / (2 * rms_se) if rms_se > 0 else None
    ratio = rms_se / sd if sd is not None and sd > 0 else None
    ratio_if = (rms_if / sd - rms_se * sd_if / sd ** 2
                if sd_if is not None and rms_if is not None else None)
    lower = estimates - CRITICAL_VALUE * standard_errors
    upper = estimates + CRITICAL_VALUE * standard_errors
    return {
        "bias": _mean_measure(errors),
        "rmse": {"estimate": rmse, "mcse": _mcse((squares - mse) / (2 * rmse)) if rmse > 0 else None},
        "empirical_sd": {"estimate": sd, "mcse": _mcse(sd_if) if sd_if is not None else None},
        "rms_se": {"estimate": rms_se, "mcse": _mcse(rms_if) if rms_if is not None else None},
        "se_sd_ratio": {"estimate": ratio, "mcse": _mcse(ratio_if) if ratio_if is not None else None},
        "coverage": _mean_measure((lower <= truth) & (truth <= upper), bernoulli=True),
        "mean_interval_length": _mean_measure(upper - lower),
        "rejection": _mean_measure((lower > 0) | (upper < 0), bernoulli=True),
    }


def _summaries(accumulators, repetitions):
    result = []
    for cell in CELLS:
        methods = {}
        for name in METHODS:
            accumulator = accumulators[cell["cell_id"]][name]
            attempted = len(accumulator["compliant"])
            usable = len(accumulator["estimates"])
            estimates = np.array(accumulator["estimates"]).reshape((-1, 3))
            standard_errors = np.array(accumulator["standard_errors"]).reshape((-1, 3))
            methods[name] = {
                "scheduled": repetitions, "attempted": attempted, "not_run": repetitions - attempted,
                "usable": usable, "compliant": sum(accumulator["compliant"]),
                "failure_rate": _mean_measure(1 - np.array(accumulator["compliant"], dtype=int), bernoulli=True),
                "unusable_rate": _mean_measure(np.array(accumulator["unusable"], dtype=int), bernoulli=True),
                "performance_denominator": usable,
                "coefficients": [
                    {"coefficient": j, "truth": truth,
                     "rejection_interpretation": "type_i_error" if truth == 0 else "power",
                     **summarize_performance(estimates[:, j], standard_errors[:, j], truth)}
                    for j, truth in enumerate((0.0, cell["beta1"], 1.0))
                ],
            }
        result.append({**cell, "methods": methods})
    return result


def run_study(program_path, results_dir, *, repetitions=REPETITIONS):
    """Execute once; repetitions is exposed solely for deterministic Python tests."""
    if isinstance(repetitions, bool) or not isinstance(repetitions, int) or repetitions < 1:
        raise ValueError("repetitions must be a positive integer")
    output = Path(results_dir)
    if output.is_symlink():
        raise FileExistsError("Refusing symlink results directory")
    output.mkdir(parents=True, exist_ok=True)
    output = output.resolve()
    for name in OUTPUT_NAMES:
        if (output / name).exists() or (output / name).is_symlink():
            raise FileExistsError(f"Consumed or occupied evaluation output: {output / name}")
    # Exclusive creation claims the run before import, dependency checks, or execution.
    _write_json(output / "study_started.json", {
        "started_at": datetime.now(timezone.utc).isoformat(), "master_seed": MASTER_SEED,
        "repetitions_per_cell": repetitions, "theory": "UNASSESSED",
    })
    start = time.perf_counter()
    path = Path(program_path).resolve()
    source_root = next((parent for parent in path.parents if parent.name == "src"), path.parent)
    accumulators = {
        cell["cell_id"]: {name: {"estimates": [], "standard_errors": [], "compliant": [], "unusable": []}
                          for name in METHODS} for cell in CELLS
    }
    details = {
        "scope": "development full finite-design simulation; no mathematical certification",
        "theory": "UNASSESSED", "master_seed": MASTER_SEED, "cells": CELLS,
        "repetitions_per_cell": repetitions, "cli_design": repetitions == REPETITIONS,
        "rng": "PCG64(SeedSequence(master_seed, spawn_key=(cell_id, zero_based_replicate)))",
        "draw_layout": "standard_normal((n,3)): columns X1, X2, independent error",
        "heteroskedastic_variance": "(1+4*X1**2)/5", "truth": "[0,beta1,1]",
        "methods": METHODS, "reference_hc0_role": "implementation check only",
        "critical_value": CRITICAL_VALUE, "reference_version_required": REFERENCE_VERSION,
        "rtol": RTOL, "atol": ATOL, "program_path": str(path),
        "candidate_source_root": str(source_root),
        "candidate_source_sha256_before": None, "candidate_source_sha256_after": None,
        "source_hash_exclusions": ["**/__pycache__/**", "**/*.pyc", "**/*.pyo"],
        "evaluator_sha256": _sha256(Path(__file__)), "python": platform.python_version(),
        "numpy": np.__version__, "error": None,
        "mcse": __doc__,
        "performance_population": "inference-usable outputs, including reference mismatches; conditional on usability",
        "failure_definition": "unusable output or failed/unavailable reference agreement; not_run excluded",
        "correct_definition": "all scheduled rows executed with both methods numerically compliant and unchanged candidate source tree; theory UNASSESSED",
    }
    rows_completed, reference_failures = 0, 0
    original_path, original_bytecode = list(sys.path), sys.dont_write_bytecode
    prior_module = sys.modules.get("hc0_evaluation_candidate")
    interrupt = None
    try:
        with (output / "replicates.jsonl").open("x", encoding="utf-8", buffering=1) as raw_stream:
            import scipy
            import statsmodels

            details.update(scipy=scipy.__version__, statsmodels=statsmodels.__version__)
            if statsmodels.__version__ != REFERENCE_VERSION:
                raise RuntimeError(f"Require statsmodels {REFERENCE_VERSION}, got {statsmodels.__version__}")
            details["candidate_source_sha256_before"] = _source_hashes(source_root)
            details["candidate_sha256_before"] = _sha256(path)
            _write_json(output / "source_before.json", {
                "candidate_source_root": str(source_root),
                "sha256": details["candidate_source_sha256_before"],
                "exclusions": details["source_hash_exclusions"], "theory": "UNASSESSED",
            })
            sys.path.insert(0, str(path.parent))
            sys.dont_write_bytecode = True
            candidate, details["candidate_import"] = _observe(lambda: _load_candidate(path))
            for cell in CELLS:
                for replicate in range(repetitions):
                    x, y = generate_dataset(cell, replicate)
                    fingerprint = hashlib.sha256(x.astype("<f8").tobytes() + y.astype("<f8").tobytes()).hexdigest()
                    references, reference_observation = _observe(lambda: _reference_methods(x, y))
                    reference, conventional = references if references is not None else (None, None)
                    reference_record, reference_values = _method_record(reference, reference_observation)
                    if not reference_record["usable"]:
                        reference_failures += 1
                    if candidate is not None:
                        returned, observation = _observe(lambda: candidate({
                            "design_matrix": x.tolist(), "outcomes": y.tolist(),
                        }))
                    else:
                        returned = None
                        observation = {**details["candidate_import"], "elapsed_seconds": 0.0}
                    candidate_record, candidate_values = _method_record(
                        returned, observation, reference_values, require_reference=True)
                    conventional_record, conventional_values = _method_record(conventional, reference_observation)
                    records = {"candidate_hc0": candidate_record, "conventional_ols": conventional_record}
                    row = {
                        **cell, "replicate": replicate, "seed_spawn_key": [cell["cell_id"], replicate],
                        "data_sha256": fingerprint, "reference_hc0": reference_record, "methods": records,
                    }
                    raw_stream.write(json.dumps(row, allow_nan=False) + "\n")
                    for name, values in (("candidate_hc0", candidate_values), ("conventional_ols", conventional_values)):
                        accumulator = accumulators[cell["cell_id"]][name]
                        accumulator["compliant"].append(records[name]["compliant"])
                        accumulator["unusable"].append(not records[name]["usable"])
                        if values is not None:
                            accumulator["estimates"].append(values["coefficients"])
                            accumulator["standard_errors"].append(values["standard_errors"])
                    rows_completed += 1
    except BaseException as error:
        details["error"] = traceback.format_exc()
        if not isinstance(error, Exception):
            interrupt = error
    finally:
        sys.path[:] = original_path
        sys.dont_write_bytecode = original_bytecode
        if prior_module is None:
            sys.modules.pop("hc0_evaluation_candidate", None)
        else:
            sys.modules["hc0_evaluation_candidate"] = prior_module
    details["source_identity_error"] = None
    details["candidate_sha256_after"] = None
    try:
        details["candidate_source_sha256_after"] = _source_hashes(source_root)
        details["candidate_sha256_after"] = _sha256(path) if path.is_file() else None
    except Exception:
        details["source_identity_error"] = traceback.format_exc()
    entrypoint_unchanged = (details.get("candidate_sha256_before") is not None
                           and details["candidate_sha256_after"] == details["candidate_sha256_before"])
    unchanged = (entrypoint_unchanged and details["candidate_source_sha256_before"] is not None
                 and details["candidate_source_sha256_after"] == details["candidate_source_sha256_before"]
                 and details["source_identity_error"] is None)
    expected = len(CELLS) * repetitions
    totals = {name: sum(sum(cell[name]["compliant"]) for cell in accumulators.values()) for name in METHODS}
    complete = rows_completed == expected and details["error"] is None
    correct = complete and unchanged and reference_failures == 0 and all(value == expected for value in totals.values())
    metrics = {
        "combined_score": int(correct), "study_complete": int(complete),
        "scheduled_replicates": expected, "completed_replicates": rows_completed,
        "candidate_compliant_replicates": totals["candidate_hc0"],
        "conventional_compliant_replicates": totals["conventional_ols"],
        "reference_failure_replicates": reference_failures,
        "numerical_compliance": int(correct),
    }
    details.update(completed_replicates=rows_completed, scheduled_replicates=expected,
                   entrypoint_unchanged=entrypoint_unchanged, source_tree_unchanged=unchanged,
                   elapsed_seconds=time.perf_counter() - start,
                   status="COMPLETE" if complete else "INCOMPLETE",
                   raw_sha256=_sha256(output / "replicates.jsonl"))
    _write_json(output / "summaries.json", _summaries(accumulators, repetitions))
    _write_json(output / "study.json", details)
    _write_json(output / "metrics.json", metrics)
    _write_json(output / "correct.json", {"correct": bool(correct)})
    if interrupt is not None:
        raise interrupt
    return metrics


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--program_path", required=True)
    parser.add_argument("--results_dir", required=True)
    args = parser.parse_args(argv)
    metrics = run_study(args.program_path, args.results_dir, repetitions=REPETITIONS)
    print(json.dumps(metrics, allow_nan=False))
    return 0 if metrics["study_complete"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
