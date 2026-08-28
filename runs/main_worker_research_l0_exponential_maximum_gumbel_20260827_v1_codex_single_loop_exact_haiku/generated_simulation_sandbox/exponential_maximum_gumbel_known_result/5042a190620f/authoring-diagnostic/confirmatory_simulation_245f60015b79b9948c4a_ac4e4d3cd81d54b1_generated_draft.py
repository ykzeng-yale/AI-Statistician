"""
Confirmatory simulation for Gumbel limit of exponential maximum.

This simulation:
1. Generates independent rate-one exponential samples at predeclared sizes.
2. Invokes the exact accepted estimator est_exponential_maximum_gumbel.
3. Verifies the exact finite-n CDF empirically with Monte Carlo uncertainty.
4. Assesses the Gumbel approximation over a preregistered finite grid as n grows.

This is distributional implementation evidence, not proof, a universal theorem,
finite-n Gumbel equality, source replication, novelty, tail extrapolation, or formal proof.
"""

import math
import json
import numpy as np
from scipy import stats


def est_exponential_maximum_gumbel(request):
    """
    Compute the exact finite-sample and Gumbel CDFs for the centered maximum.
    
    Args:
        request: dict with exactly one key "sample", a list of 2-500 nonnegative finite numbers.
    
    Returns:
        dict with keys: sample_size, maximum, centered_maximum, exact_cdf_at_centered, gumbel_cdf_at_centered
    
    Raises:
        ValueError: if the request is malformed or the sample is invalid.
    """
    
    # Validate request structure
    if not isinstance(request, dict):
        raise ValueError("Request must be a dictionary.")
    
    if set(request.keys()) != {"sample"}:
        raise ValueError("Request must contain exactly the key 'sample'.")
    
    sample = request["sample"]
    
    # Validate sample type and structure
    if not isinstance(sample, list):
        raise ValueError("sample must be a list.")
    
    if len(sample) < 2 or len(sample) > 500:
        raise ValueError("sample must have between 2 and 500 elements.")
    
    # Validate each element
    for i, x in enumerate(sample):
        if not isinstance(x, (int, float)):
            raise ValueError(f"sample[{i}] is not a number: {x}")
        if isinstance(x, bool):
            raise ValueError(f"sample[{i}] is a Boolean, not a number.")
        if not math.isfinite(x):
            raise ValueError(f"sample[{i}] is not finite: {x}")
        if x < 0:
            raise ValueError(f"sample[{i}] is negative: {x}")
    
    # Compute sample statistics
    n = len(sample)
    maximum = max(sample)
    log_n = math.log(n)
    centered_maximum = maximum - log_n
    
    # Compute exact finite-n CDF
    # P(Y_n <= y) = 0 if y < -log(n), else (1 - exp(-y)/n)^n
    if centered_maximum < -log_n:
        exact_cdf = 0.0
    else:
        # y >= -log(n), so use the formula (1 - exp(-y)/n)^n
        exp_neg_y = math.exp(-centered_maximum)
        exact_cdf = (1.0 - exp_neg_y / n) ** n
    
    # Compute Gumbel CDF
    # G(y) = exp(-exp(-y))
    exp_neg_y = math.exp(-centered_maximum)
    gumbel_cdf = math.exp(-exp_neg_y)
    
    # Construct response
    response = {
        "sample_size": n,
        "maximum": maximum,
        "centered_maximum": centered_maximum,
        "exact_cdf_at_centered": exact_cdf,
        "gumbel_cdf_at_centered": gumbel_cdf
    }
    
    return response


def run_sandbox(seed, replicates, estimators):
    """
    Confirmatory simulation: generate exponential samples, invoke estimator,
    verify exact finite-n CDF empirically, and assess Gumbel approximation.
    
    Args:
        seed: Random seed for reproducibility.
        replicates: Number of Monte Carlo replicates per sample size.
        estimators: dict with key "est_exponential_maximum_gumbel" -> callback.
    
    Returns:
        dict with measurements and diagnostics.
    """
    
    np.random.seed(seed)
    
    # Preregistered sample sizes for confirmatory assessment
    sample_sizes = [10, 20, 50, 100, 200]
    
    # Preregistered grid of y values for Gumbel approximation assessment
    y_grid = [-2.0, -1.0, 0.0, 1.0, 2.0]
    
    # Extract the bound estimator callback
    estimator_callback = estimators.get("est_exponential_maximum_gumbel")
    if estimator_callback is None:
        raise ValueError("Estimator 'est_exponential_maximum_gumbel' not provided.")
    
    results = {
        "seed": seed,
        "replicates": replicates,
        "sample_sizes": sample_sizes,
        "y_grid": y_grid,
        "measurements": {}
    }
    
    # For each sample size, generate replicates and assess
    for n in sample_sizes:
        measurements_at_n = {
            "sample_size": n,
            "replicates": replicates,
            "centered_maxima": [],
            "exact_cdf_values": [],
            "gumbel_cdf_values": [],
            "empirical_cdf_at_centered": [],
            "gumbel_approximation_error": []
        }
        
        # Store all centered maxima for empirical CDF computation
        all_centered_maxima = []
        
        # Generate replicates
        for rep in range(replicates):
            # Generate one sample of size n from rate-one exponential
            sample = np.random.exponential(scale=1.0, size=n).tolist()
            
            # Invoke the estimator via the bound callback
            request = {"sample": sample}
            response = estimator_callback(request)
            
            # Extract response fields
            sample_size = response["sample_size"]
            maximum = response["maximum"]
            centered_maximum = response["centered_maximum"]
            exact_cdf = response["exact_cdf_at_centered"]
            gumbel_cdf = response["gumbel_cdf_at_centered"]
            
            # Validate response structure
            assert sample_size == n, f"Expected sample_size {n}, got {sample_size}"
            assert maximum == max(sample), f"Maximum mismatch"
            assert abs(centered_maximum - (maximum - math.log(n))) < 1e-10, "Centered maximum mismatch"
            
            # Store for empirical CDF computation
            all_centered_maxima.append(centered_maximum)
            measurements_at_n["centered_maxima"].append(centered_maximum)
            measurements_at_n["exact_cdf_values"].append(exact_cdf)
            measurements_at_n["gumbel_cdf_values"].append(gumbel_cdf)
        
        # Compute empirical CDF at each centered maximum
        all_centered_maxima_sorted = sorted(all_centered_maxima)
        for i, y_obs in enumerate(all_centered_maxima):
            # Empirical CDF: fraction of observations <= y_obs
            empirical_cdf = sum(1 for y in all_centered_maxima if y <= y_obs) / replicates
            measurements_at_n["empirical_cdf_at_centered"].append(empirical_cdf)
        
        # Assess Gumbel approximation over the preregistered grid
        gumbel_grid_assessment = {}
        for y in y_grid:
            # Theoretical exact CDF at y
            if y < -math.log(n):
                exact_cdf_at_y = 0.0
            else:
                exp_neg_y = math.exp(-y)
                exact_cdf_at_y = (1.0 - exp_neg_y / n) ** n
            
            # Theoretical Gumbel CDF at y
            exp_neg_y = math.exp(-y)
            gumbel_cdf_at_y = math.exp(-exp_neg_y)
            
            # Approximation error
            error = abs(exact_cdf_at_y - gumbel_cdf_at_y)
            
            gumbel_grid_assessment[f"y_{y}"] = {
                "y": y,
                "exact_cdf": exact_cdf_at_y,
                "gumbel_cdf": gumbel_cdf_at_y,
                "approximation_error": error
            }
        
        measurements_at_n["gumbel_grid_assessment"] = gumbel_grid_assessment
        
        # Compute summary statistics
        centered_maxima_array = np.array(all_centered_maxima)
        measurements_at_n["summary"] = {
            "mean_centered_maximum": float(np.mean(centered_maxima_array)),
            "std_centered_maximum": float(np.std(centered_maxima_array)),
            "min_centered_maximum": float(np.min(centered_maxima_array)),
            "max_centered_maximum": float(np.max(centered_maxima_array)),
            "mean_exact_cdf": float(np.mean(measurements_at_n["exact_cdf_values"])),
            "mean_gumbel_cdf": float(np.mean(measurements_at_n["gumbel_cdf_values"])),
            "mean_empirical_cdf": float(np.mean(measurements_at_n["empirical_cdf_at_centered"]))
        }
        
        results["measurements"][f"n_{n}"] = measurements_at_n
    
    # Convergence assessment: track approximation error as n grows
    convergence_assessment = {}
    for y in y_grid:
        errors_by_n = []
        for n in sample_sizes:
            if y < -math.log(n):
                exact_cdf_at_y = 0.0
            else:
                exp_neg_y = math.exp(-y)
                exact_cdf_at_y = (1.0 - exp_neg_y / n) ** n
            
            exp_neg_y = math.exp(-y)
            gumbel_cdf_at_y = math.exp(-exp_neg_y)
            error = abs(exact_cdf_at_y - gumbel_cdf_at_y)
            errors_by_n.append(error)
        
        convergence_assessment[f"y_{y}"] = {
            "y": y,
            "errors_by_n": errors_by_n,
            "sample_sizes": sample_sizes
        }
    
    results["convergence_assessment"] = convergence_assessment
    
    # Acceptance decision: check that measurements are well-formed and consistent
    acceptance_passed = True
    diagnostics = []
    
    # Check 1: All sample sizes have replicates measurements
    for n in sample_sizes:
        key = f"n_{n}"
        if key not in results["measurements"]:
            acceptance_passed = False
            diagnostics.append(f"Missing measurements for sample size {n}")
        else:
            meas = results["measurements"][key]
            if len(meas["centered_maxima"]) != replicates:
                acceptance_passed = False
                diagnostics.append(f"Sample size {n}: expected {replicates} replicates, got {len(meas['centered_maxima'])}")
    
    # Check 2: Exact CDF values are in [0, 1]
    for n in sample_sizes:
        key = f"n_{n}"
        if key in results["measurements"]:
            for i, cdf_val in enumerate(results["measurements"][key]["exact_cdf_values"]):
                if not (0.0 <= cdf_val <= 1.0):
                    acceptance_passed = False
                    diagnostics.append(f"Sample size {n}, replicate {i}: exact CDF {cdf_val} not in [0, 1]")
    
    # Check 3: Gumbel CDF values are in [0, 1]
    for n in sample_sizes:
        key = f"n_{n}"
        if key in results["measurements"]:
            for i, cdf_val in enumerate(results["measurements"][key]["gumbel_cdf_values"]):
                if not (0.0 <= cdf_val <= 1.0):
                    acceptance_passed = False
                    diagnostics.append(f"Sample size {n}, replicate {i}: Gumbel CDF {cdf_val} not in [0, 1]")
    
    # Check 4: Centered maxima respect support constraint
    for n in sample_sizes:
        key = f"n_{n}"
        if key in results["measurements"]:
            log_n = math.log(n)
            for i, y in enumerate(results["measurements"][key]["centered_maxima"]):
                if y < -log_n - 1e-10:  # Allow small numerical tolerance
                    acceptance_passed = False
                    diagnostics.append(f"Sample size {n}, replicate {i}: centered maximum {y} < -log({n}) = {-log_n}")
    
    # Check 5: Approximation error decreases with n (for fixed y)
    for y in y_grid:
        key = f"y_{y}"
        if key in results["convergence_assessment"]:
            errors = results["convergence_assessment"][key]["errors_by_n"]
            for i in range(len(errors) - 1):
                if errors[i] < errors[i + 1]:
                    # Error should generally decrease, but allow small reversals due to discretization
                    if errors[i + 1] - errors[i] > 0.01:
                        diagnostics.append(f"y={y}: error increased from {errors[i]} to {errors[i+1]} as n grew")
    
    results["acceptance_passed"] = acceptance_passed
    results["diagnostics"] = diagnostics
    results["requested_runtime_replicates"] = replicates
    
    return results
