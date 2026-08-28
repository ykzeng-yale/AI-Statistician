
import math
import numpy as np
from scipy import stats

def run_sandbox(seed, replicates):
    """
    Sanity checks for the exponential maximum Gumbel theory.
    """
    np.random.seed(seed)
    
    results = {}
    
    # Check 1: Verify exact CDF formula at y=0 for n=10
    # At y=0: exact = (1 - 1/10)^10 = 0.9^10
    n = 10
    y = 0
    exact_cdf_y0 = (1 - 1/n) ** n
    gumbel_cdf_y0 = math.exp(-math.exp(-y))
    results["check_1_exact_cdf_at_y0_n10"] = float(exact_cdf_y0)
    results["check_1_gumbel_cdf_at_y0_n10"] = float(gumbel_cdf_y0)
    results["check_1_error_at_y0_n10"] = float(abs(exact_cdf_y0 - gumbel_cdf_y0))
    
    # Check 2: Verify support boundary
    # At y = -log(n), exact CDF should be 0
    n = 10
    y = -math.log(n)
    # At this boundary, exp(-y) = n, so (1 - n/n)^n = 0^n = 0
    exact_cdf_boundary = (1 - math.exp(-y) / n) ** n
    results["check_2_exact_cdf_at_boundary_n10"] = float(exact_cdf_boundary)
    
    # Check 3: Verify that centered_maximum >= -log(n) always
    # Since M_n >= 0, we have Y_n = M_n - log(n) >= -log(n)
    # Generate samples and verify
    n = 50
    num_samples = 100
    for i in range(num_samples):
        sample = np.random.exponential(1.0, n)
        M_n = np.max(sample)
        Y_n = M_n - math.log(n)
        if Y_n < -math.log(n) - 1e-10:  # Allow small numerical error
            results["check_3_violation"] = True
            break
    else:
        results["check_3_all_samples_satisfy_support"] = True
    
    # Check 4: Verify pointwise convergence at y=0
    # As n increases, (1 - 1/n)^n should approach exp(-1)
    target = math.exp(-1)
    convergence_errors = []
    for n in [10, 50, 100, 500, 1000]:
        exact_cdf = (1 - 1/n) ** n
        error = abs(exact_cdf - target)
        convergence_errors.append(error)
    results["check_4_convergence_errors_at_y0"] = convergence_errors
    results["check_4_target_gumbel_cdf"] = float(target)
    
    # Check 5: Verify that exact CDF is monotone increasing in y
    n = 100
    y_values = np.linspace(-math.log(n), 5, 20)
    cdf_values = []
    for y in y_values:
        if y < -math.log(n):
            cdf = 0.0
        else:
            cdf = (1 - math.exp(-y) / n) ** n
        cdf_values.append(cdf)
    
    # Check monotonicity
    is_monotone = all(cdf_values[i] <= cdf_values[i+1] for i in range(len(cdf_values)-1))
    results["check_5_exact_cdf_is_monotone"] = is_monotone
    results["check_5_cdf_values_sample"] = [float(c) for c in cdf_values[::5]]
    
    # Check 6: Verify that Gumbel CDF is always in (0, 1)
    y_values = np.linspace(-5, 5, 20)
    gumbel_values = [math.exp(-math.exp(-y)) for y in y_values]
    all_in_unit_interval = all(0 < g < 1 for g in gumbel_values)
    results["check_6_gumbel_cdf_in_unit_interval"] = all_in_unit_interval
    results["check_6_gumbel_min"] = float(min(gumbel_values))
    results["check_6_gumbel_max"] = float(max(gumbel_values))
    
    # Check 7: Verify that exact CDF approaches Gumbel CDF as n increases
    y = 1.0
    errors_by_n = {}
    for n in [10, 50, 100, 500]:
        exact = (1 - math.exp(-y) / n) ** n
        gumbel = math.exp(-math.exp(-y))
        error = abs(exact - gumbel)
        errors_by_n[str(n)] = float(error)
    results["check_7_approximation_errors_at_y1"] = errors_by_n
    
    # Check 8: Verify that the estimator formula is correct
    # For a sample with maximum M_n, centered_maximum = M_n - log(n)
    # exact_cdf = (1 - exp(-centered_maximum) / n)^n
    # gumbel_cdf = exp(-exp(-centered_maximum))
    n = 20
    sample = np.random.exponential(1.0, n)
    M_n = np.max(sample)
    Y_n = M_n - math.log(n)
    
    exact_cdf_formula = (1 - math.exp(-Y_n) / n) ** n
    gumbel_cdf_formula = math.exp(-math.exp(-Y_n))
    
    results["check_8_sample_max"] = float(M_n)
    results["check_8_centered_max"] = float(Y_n)
    results["check_8_exact_cdf"] = float(exact_cdf_formula)
    results["check_8_gumbel_cdf"] = float(gumbel_cdf_formula)
    
    return results
