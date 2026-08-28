
import math
import numpy as np

def run_sandbox(seed, replicates):
    """
    Test the estimator implementation against the theory.
    """
    np.random.seed(seed)
    
    results = {}
    
    # Simulate the estimator logic
    def estimator_exact_cdf(sample):
        n = len(sample)
        maximum = max(sample)
        log_n = math.log(n)
        centered_maximum = maximum - log_n
        
        if centered_maximum < -log_n:
            exact_cdf = 0.0
        else:
            exp_neg_y = math.exp(-centered_maximum)
            exact_cdf = (1.0 - exp_neg_y / n) ** n
        
        exp_neg_y = math.exp(-centered_maximum)
        gumbel_cdf = math.exp(-exp_neg_y)
        
        return {
            "sample_size": n,
            "maximum": maximum,
            "centered_maximum": centered_maximum,
            "exact_cdf_at_centered": exact_cdf,
            "gumbel_cdf_at_centered": gumbel_cdf
        }
    
    # Test 1: Permutation invariance
    sample1 = [0.5, 1.2, 0.3, 2.1, 0.8]
    sample1_perm = [2.1, 0.3, 1.2, 0.5, 0.8]
    
    resp1 = estimator_exact_cdf(sample1)
    resp1_perm = estimator_exact_cdf(sample1_perm)
    
    results["test_1_permutation_invariance"] = (
        resp1["maximum"] == resp1_perm["maximum"] and
        abs(resp1["centered_maximum"] - resp1_perm["centered_maximum"]) < 1e-10 and
        abs(resp1["exact_cdf_at_centered"] - resp1_perm["exact_cdf_at_centered"]) < 1e-10
    )
    
    # Test 2: All zeros
    sample_zeros = [0.0] * 10
    resp_zeros = estimator_exact_cdf(sample_zeros)
    
    results["test_2_all_zeros_maximum"] = resp_zeros["maximum"]
    results["test_2_all_zeros_centered"] = resp_zeros["centered_maximum"]
    results["test_2_all_zeros_exact_cdf"] = resp_zeros["exact_cdf_at_centered"]
    # At y = -log(10), exact CDF should be 0
    results["test_2_all_zeros_is_zero"] = resp_zeros["exact_cdf_at_centered"] < 1e-100
    
    # Test 3: Maximum equals log(n)
    n = 20
    sample_log_n = [math.log(n)] + [0.0] * (n - 1)
    resp_log_n = estimator_exact_cdf(sample_log_n)
    
    # At y = 0: exact = (1 - 1/n)^n, gumbel = exp(-1)
    exact_expected = (1 - 1/n) ** n
    gumbel_expected = math.exp(-1.0)
    
    results["test_3_y0_exact_cdf"] = resp_log_n["exact_cdf_at_centered"]
    results["test_3_y0_exact_expected"] = exact_expected
    results["test_3_y0_exact_error"] = abs(resp_log_n["exact_cdf_at_centered"] - exact_expected)
    results["test_3_y0_gumbel_cdf"] = resp_log_n["gumbel_cdf_at_centered"]
    results["test_3_y0_gumbel_expected"] = gumbel_expected
    results["test_3_y0_gumbel_error"] = abs(resp_log_n["gumbel_cdf_at_centered"] - gumbel_expected)
    
    # Test 4: Large sample
    n = 500
    sample_large = np.random.exponential(1.0, n)
    resp_large = estimator_exact_cdf(sample_large.tolist())
    
    results["test_4_large_sample_size"] = resp_large["sample_size"]
    results["test_4_large_sample_max"] = float(resp_large["maximum"])
    results["test_4_large_sample_centered"] = float(resp_large["centered_maximum"])
    results["test_4_large_sample_exact_cdf"] = float(resp_large["exact_cdf_at_centered"])
    results["test_4_large_sample_gumbel_cdf"] = float(resp_large["gumbel_cdf_at_centered"])
    
    # Test 5: Verify that exact_cdf <= 1 and >= 0
    for i in range(10):
        sample = np.random.exponential(1.0, np.random.randint(2, 100)).tolist()
        resp = estimator_exact_cdf(sample)
        if not (0 <= resp["exact_cdf_at_centered"] <= 1):
            results["test_5_cdf_out_of_bounds"] = True
            break
    else:
        results["test_5_all_cdfs_in_bounds"] = True
    
    # Test 6: Verify that gumbel_cdf is in (0, 1)
    for i in range(10):
        sample = np.random.exponential(1.0, np.random.randint(2, 100)).tolist()
        resp = estimator_exact_cdf(sample)
        if not (0 < resp["gumbel_cdf_at_centered"] < 1):
            results["test_6_gumbel_out_of_bounds"] = True
            break
    else:
        results["test_6_all_gumbel_in_bounds"] = True
    
    # Test 7: Verify centered_maximum >= -log(n)
    for i in range(20):
        n = np.random.randint(2, 100)
        sample = np.random.exponential(1.0, n).tolist()
        resp = estimator_exact_cdf(sample)
        if resp["centered_maximum"] < -math.log(n) - 1e-10:
            results["test_7_support_violation"] = True
            break
    else:
        results["test_7_all_support_satisfied"] = True
    
    return results
