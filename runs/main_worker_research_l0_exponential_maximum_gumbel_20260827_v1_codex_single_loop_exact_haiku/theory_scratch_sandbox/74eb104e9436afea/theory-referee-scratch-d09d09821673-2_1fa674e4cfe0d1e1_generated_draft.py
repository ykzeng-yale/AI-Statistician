
def run_sandbox(seed, replicates):
    import math
    import numpy as np
    
    # Verify the exact finite-n CDF formula and Gumbel limit
    # for the centered maximum of exponential observations
    
    def exact_cdf_Y_n(y, n):
        """Exact finite-n CDF of Y_n = M_n - log(n)"""
        log_n = math.log(n)
        if y < -log_n:
            return 0.0
        else:
            exp_neg_y = math.exp(-y)
            return (1.0 - exp_neg_y / n) ** n
    
    def gumbel_cdf(y):
        """Standard Gumbel CDF"""
        return math.exp(-math.exp(-y))
    
    results = {}
    
    # Test 1: Verify the formula at y=0 for various n
    test1 = {}
    for n in [10, 50, 100, 500, 1000]:
        exact = exact_cdf_Y_n(0, n)
        gumbel = gumbel_cdf(0)
        error = abs(exact - gumbel)
        test1[f"n_{n}"] = {"exact": exact, "gumbel": gumbel, "error": error}
    results["test1_y_equals_0"] = test1
    
    # Test 2: Verify support boundary
    test2 = {}
    for n in [5, 10, 50]:
        log_n = math.log(n)
        y_boundary = -log_n
        exact = exact_cdf_Y_n(y_boundary, n)
        test2[f"n_{n}"] = {"y_boundary": y_boundary, "exact_cdf": exact}
    results["test2_support_boundary"] = test2
    
    # Test 3: Verify that y < -log(n) gives CDF = 0
    test3 = {}
    for n in [10, 50]:
        log_n = math.log(n)
        y_below = -log_n - 0.5
        exact = exact_cdf_Y_n(y_below, n)
        test3[f"n_{n}"] = {"y_below": y_below, "log_n": log_n, "exact_cdf": exact}
    results["test3_below_support"] = test3
    
    # Test 4: Verify the limit using the standard limit (1 + c/n)^n -> e^c
    test4 = {}
    y_test = 1.5
    for n in [10, 100, 1000, 10000]:
        exact = exact_cdf_Y_n(y_test, n)
        gumbel = gumbel_cdf(y_test)
        error = abs(exact - gumbel)
        test4[f"n_{n}"] = {"exact": exact, "gumbel": gumbel, "error": error}
    results["test4_limit_convergence"] = test4
    
    # Test 5: Verify the approximation error is O(1/n)
    test5 = {}
    y_test = 0.0
    for n in [10, 20, 50, 100, 200, 500, 1000]:
        exact = exact_cdf_Y_n(y_test, n)
        gumbel = gumbel_cdf(y_test)
        error = abs(exact - gumbel)
        error_times_n = error * n
        test5[f"n_{n}"] = {"error": error, "error_times_n": error_times_n}
    results["test5_error_scaling"] = test5
    
    # Test 6: Verify monotonicity of exact CDF in y
    test6 = {}
    n = 100
    y_vals = np.linspace(-math.log(n), 5, 20)
    cdfs = [exact_cdf_Y_n(y, n) for y in y_vals]
    is_monotone = all(cdfs[i] <= cdfs[i+1] for i in range(len(cdfs)-1))
    test6["n"] = n
    test6["is_monotone"] = is_monotone
    test6["first_cdf"] = float(cdfs[0])
    test6["last_cdf"] = float(cdfs[-1])
    results["test6_monotonicity"] = test6
    
    # Test 7: Verify the estimator implementation logic
    def estimator_logic(sample):
        n = len(sample)
        maximum = max(sample)
        log_n = math.log(n)
        centered_maximum = maximum - log_n
        
        # Exact CDF
        if centered_maximum < -log_n:
            exact_cdf = 0.0
        else:
            exp_neg_y = math.exp(-centered_maximum)
            exact_cdf = (1.0 - exp_neg_y / n) ** n
        
        # Gumbel CDF
        exp_neg_y = math.exp(-centered_maximum)
        gumbel_cdf_val = math.exp(-exp_neg_y)
        
        return {
            'sample_size': n,
            'maximum': maximum,
            'centered_maximum': centered_maximum,
            'exact_cdf_at_centered': exact_cdf,
            'gumbel_cdf_at_centered': gumbel_cdf_val
        }
    
    # Test with a sample
    np.random.seed(seed)
    sample = list(np.random.exponential(scale=1.0, size=50))
    result = estimator_logic(sample)
    test7 = {
        'sample_size': result['sample_size'],
        'maximum': float(result['maximum']),
        'centered_maximum': float(result['centered_maximum']),
        'exact_cdf': float(result['exact_cdf_at_centered']),
        'gumbel_cdf': float(result['gumbel_cdf_at_centered']),
        'centered_ge_minus_log_n': result['centered_maximum'] >= -math.log(result['sample_size'])
    }
    results["test7_estimator_logic"] = test7
    
    # Test 8: Edge case - all zeros
    sample_zeros = [0.0] * 5
    result_zeros = estimator_logic(sample_zeros)
    test8 = {
        'maximum': float(result_zeros['maximum']),
        'centered_maximum': float(result_zeros['centered_maximum']),
        'expected_centered': float(-math.log(5)),
        'exact_cdf': float(result_zeros['exact_cdf_at_centered']),
        'gumbel_cdf': float(result_zeros['gumbel_cdf_at_centered']),
        'exact_at_boundary': float(exact_cdf_Y_n(-math.log(5), 5))
    }
    results["test8_all_zeros"] = test8
    
    return results
