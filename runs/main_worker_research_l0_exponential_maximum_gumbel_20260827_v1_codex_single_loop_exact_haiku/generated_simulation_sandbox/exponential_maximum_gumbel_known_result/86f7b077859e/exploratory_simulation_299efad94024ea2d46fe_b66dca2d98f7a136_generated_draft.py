"""
Exploratory simulation for exponential maximum and Gumbel limit.

This simulation:
1. Implements the est_exponential_maximum_gumbel estimator (run_estimator).
2. Generates independent rate-one exponential samples at predeclared sizes.
3. Invokes the estimator on each sample.
4. Verifies the exact finite-n CDF empirically via Monte Carlo.
5. Assesses the Gumbel approximation over a preregistered finite grid.

This is distributional implementation evidence, not proof, universal theorem,
finite-n Gumbel equality, source replication, novelty, tail extrapolation,
or formal proof.
"""

import math
import numpy as np
from scipy import stats


# ============================================================================
# ESTIMATOR: est_exponential_maximum_gumbel
# ============================================================================

def run_estimator(request):
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
        # This should not happen since centered_maximum = maximum - log(n) >= 0 - log(n) = -log(n)
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


# ============================================================================
# EXPLORATORY SIMULATION
# ============================================================================

def run_sandbox(seed, replicates, estimators):
    """
    Exploratory simulation for exponential maximum and Gumbel limit.
    
    Args:
        seed: Random seed for reproducibility.
        replicates: Number of Monte Carlo replicates per sample size.
        estimators: dict with key "est_exponential_maximum_gumbel" -> run_estimator callback.
    
    Returns:
        dict with measurements and diagnostics.
    """
    
    np.random.seed(seed)
    
    # Preregistered sample sizes for assessment
    sample_sizes = [10, 20, 50, 100, 200]
    
    # Preregistered grid of y values for Gumbel approximation assessment
    y_grid = [-2.0, -1.0, 0.0, 1.0, 2.0]
    
    # Extract the estimator callback
    estimator_callback = estimators.get("est_exponential_maximum_gumbel")
    if estimator_callback is None:
        raise ValueError("Estimator 'est_exponential_maximum_gumbel' not provided.")
    
    results = {
        "seed": seed,
        "replicates": replicates,
        "sample_sizes": sample_sizes,
        "y_grid": y_grid,
        "estimator_calls": [],
        "exact_cdf_empirical_verification": [],
        "gumbel_approximation_assessment": []
    }
    
    # ========================================================================
    # Part 1: Generate samples and invoke estimator
    # ========================================================================
    
    for n in sample_sizes:
        for rep in range(replicates):
            # Generate independent rate-one exponential sample
            sample = np.random.exponential(scale=1.0, size=n).tolist()
            
            # Invoke estimator
            request = {"sample": sample}
            response = estimator_callback(request)
            
            results["estimator_calls"].append({
                "sample_size": n,
                "replicate": rep,
                "response": response
            })
    
    # ========================================================================
    # Part 2: Verify exact finite-n CDF empirically
    # ========================================================================
    
    for n in sample_sizes:
        # Collect centered maxima from all replicates at this sample size
        centered_maxima = []
        exact_cdfs = []
        
        for call in results["estimator_calls"]:
            if call["sample_size"] == n:
                centered_maxima.append(call["response"]["centered_maximum"])
                exact_cdfs.append(call["response"]["exact_cdf_at_centered"])
        
        # Empirical CDF: fraction of centered maxima <= each centered maximum
        centered_maxima_sorted = sorted(centered_maxima)
        
        # For each centered maximum, compute empirical CDF
        empirical_vs_exact = []
        for i, y_obs in enumerate(centered_maxima_sorted):
            empirical_cdf = (i + 1) / len(centered_maxima)
            
            # Compute exact CDF at y_obs
            log_n = math.log(n)
            if y_obs < -log_n:
                exact_cdf_at_y = 0.0
            else:
                exp_neg_y = math.exp(-y_obs)
                exact_cdf_at_y = (1.0 - exp_neg_y / n) ** n
            
            empirical_vs_exact.append({
                "y_observed": y_obs,
                "empirical_cdf": empirical_cdf,
                "exact_cdf": exact_cdf_at_y,
                "discrepancy": abs(empirical_cdf - exact_cdf_at_y)
            })
        
        results["exact_cdf_empirical_verification"].append({
            "sample_size": n,
            "replicates": len(centered_maxima),
            "empirical_vs_exact": empirical_vs_exact,
            "max_discrepancy": max([e["discrepancy"] for e in empirical_vs_exact]) if empirical_vs_exact else 0.0,
            "mean_discrepancy": np.mean([e["discrepancy"] for e in empirical_vs_exact]) if empirical_vs_exact else 0.0
        })
    
    # ========================================================================
    # Part 3: Assess Gumbel approximation over preregistered grid
    # ========================================================================
    
    for n in sample_sizes:
        gumbel_assessment_at_n = []
        
        for y in y_grid:
            # Exact finite-n CDF at y
            log_n = math.log(n)
            if y < -log_n:
                exact_cdf_at_y = 0.0
            else:
                exp_neg_y = math.exp(-y)
                exact_cdf_at_y = (1.0 - exp_neg_y / n) ** n
            
            # Gumbel CDF at y
            exp_neg_y = math.exp(-y)
            gumbel_cdf_at_y = math.exp(-exp_neg_y)
            
            # Approximation error
            error = abs(exact_cdf_at_y - gumbel_cdf_at_y)
            
            gumbel_assessment_at_n.append({
                "y": y,
                "exact_cdf": exact_cdf_at_y,
                "gumbel_cdf": gumbel_cdf_at_y,
                "error": error
            })
        
        results["gumbel_approximation_assessment"].append({
            "sample_size": n,
            "grid_assessment": gumbel_assessment_at_n,
            "max_error": max([g["error"] for g in gumbel_assessment_at_n]),
            "mean_error": np.mean([g["error"] for g in gumbel_assessment_at_n])
        })
    
    return results


# ============================================================================
# MAIN EXECUTION
# ============================================================================

if __name__ == "__main__":
    # Run exploratory simulation
    seed = 42
    replicates = 100
    
    # Create a mock estimators dict with the estimator callback
    estimators = {
        "est_exponential_maximum_gumbel": run_estimator
    }
    
    results = run_sandbox(seed=seed, replicates=replicates, estimators=estimators)
    
    # Print summary
    print("=" * 80)
    print("EXPLORATORY SIMULATION: Exponential Maximum and Gumbel Limit")
    print("=" * 80)
    print(f"Seed: {results['seed']}")
    print(f"Replicates per sample size: {results['replicates']}")
    print(f"Sample sizes: {results['sample_sizes']}")
    print(f"Y grid: {results['y_grid']}")
    print()
    
    print("=" * 80)
    print("PART 1: Estimator Invocations")
    print("=" * 80)
    print(f"Total estimator calls: {len(results['estimator_calls'])}")
    print()
    
    # Show a few example calls
    print("Example estimator calls (first 3):")
    for i, call in enumerate(results['estimator_calls'][:3]):
        print(f"\nCall {i+1}:")
        print(f"  Sample size: {call['sample_size']}")
        print(f"  Replicate: {call['replicate']}")
        print(f"  Maximum: {call['response']['maximum']:.6f}")
        print(f"  Centered maximum: {call['response']['centered_maximum']:.6f}")
        print(f"  Exact CDF: {call['response']['exact_cdf_at_centered']:.6f}")
        print(f"  Gumbel CDF: {call['response']['gumbel_cdf_at_centered']:.6f}")
    print()
    
    print("=" * 80)
    print("PART 2: Exact Finite-n CDF Empirical Verification")
    print("=" * 80)
    for verification in results['exact_cdf_empirical_verification']:
        print(f"\nSample size n={verification['sample_size']}:")
        print(f"  Replicates: {verification['replicates']}")
        print(f"  Max discrepancy (empirical vs exact): {verification['max_discrepancy']:.6f}")
        print(f"  Mean discrepancy: {verification['mean_discrepancy']:.6f}")
    print()
    
    print("=" * 80)
    print("PART 3: Gumbel Approximation Assessment")
    print("=" * 80)
    for assessment in results['gumbel_approximation_assessment']:
        print(f"\nSample size n={assessment['sample_size']}:")
        print(f"  Max error (exact vs Gumbel): {assessment['max_error']:.6f}")
        print(f"  Mean error: {assessment['mean_error']:.6f}")
        print(f"  Grid details:")
        for grid_point in assessment['grid_assessment']:
            print(f"    y={grid_point['y']:6.1f}: exact={grid_point['exact_cdf']:.6f}, "
                  f"gumbel={grid_point['gumbel_cdf']:.6f}, error={grid_point['error']:.6f}")
    print()
    
    print("=" * 80)
    print("SIMULATION COMPLETE")
    print("=" * 80)
