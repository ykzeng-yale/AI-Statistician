import math
import json


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


def run_sandbox(seed=42, replicates=10):
    """
    Developer sandbox: unit, boundary, and metamorphic checks.
    
    This is NOT a confirmatory simulation or empirical gate.
    It exercises run_estimator with various inputs and validates:
    - Request validation (closed contract)
    - Response structure and types
    - Mathematical identities
    - Permutation invariance
    - Determinism
    
    Args:
        seed: random seed for reproducibility
        replicates: number of random samples to test
    
    Returns:
        dict with diagnostic results
    """
    
    import random
    random.seed(seed)
    
    diagnostics = {
        "test_results": [],
        "errors": []
    }
    
    # Test 1: Valid request with small sample
    try:
        request = {"sample": [0.5, 1.5, 2.0]}
        response = run_estimator(request)
        assert response["sample_size"] == 3
        assert response["maximum"] == 2.0
        assert abs(response["centered_maximum"] - (2.0 - math.log(3))) < 1e-10
        diagnostics["test_results"].append({
            "test": "valid_small_sample",
            "status": "PASS"
        })
    except Exception as e:
        diagnostics["errors"].append({"test": "valid_small_sample", "error": str(e)})
    
    # Test 2: All zeros (boundary case)
    try:
        request = {"sample": [0.0, 0.0, 0.0, 0.0, 0.0]}
        response = run_estimator(request)
        n = 5
        assert response["sample_size"] == n
        assert response["maximum"] == 0.0
        assert abs(response["centered_maximum"] - (-math.log(n))) < 1e-10
        # At y = -log(n), exact CDF should be 0
        assert response["exact_cdf_at_centered"] == 0.0
        diagnostics["test_results"].append({
            "test": "all_zeros",
            "status": "PASS"
        })
    except Exception as e:
        diagnostics["errors"].append({"test": "all_zeros", "error": str(e)})
    
    # Test 3: Permutation invariance
    try:
        sample = [0.1, 2.5, 1.3, 0.8, 3.2]
        request1 = {"sample": sample}
        response1 = run_estimator(request1)
        
        sample_permuted = [3.2, 0.1, 1.3, 2.5, 0.8]
        request2 = {"sample": sample_permuted}
        response2 = run_estimator(request2)
        
        assert response1["maximum"] == response2["maximum"]
        assert abs(response1["centered_maximum"] - response2["centered_maximum"]) < 1e-10
        assert abs(response1["exact_cdf_at_centered"] - response2["exact_cdf_at_centered"]) < 1e-10
        assert abs(response1["gumbel_cdf_at_centered"] - response2["gumbel_cdf_at_centered"]) < 1e-10
        diagnostics["test_results"].append({
            "test": "permutation_invariance",
            "status": "PASS"
        })
    except Exception as e:
        diagnostics["errors"].append({"test": "permutation_invariance", "error": str(e)})
    
    # Test 4: Determinism
    try:
        request = {"sample": [0.5, 1.5, 2.0, 0.3]}
        response1 = run_estimator(request)
        response2 = run_estimator(request)
        
        assert response1 == response2
        diagnostics["test_results"].append({
            "test": "determinism",
            "status": "PASS"
        })
    except Exception as e:
        diagnostics["errors"].append({"test": "determinism", "error": str(e)})
    
    # Test 5: CDF monotonicity (exact CDF should be in [0, 1])
    try:
        for _ in range(replicates):
            n = random.randint(2, 50)
            sample = [random.expovariate(1.0) for _ in range(n)]
            request = {"sample": sample}
            response = run_estimator(request)
            
            assert 0.0 <= response["exact_cdf_at_centered"] <= 1.0
            assert 0.0 < response["gumbel_cdf_at_centered"] < 1.0
        
        diagnostics["test_results"].append({
            "test": "cdf_range",
            "status": "PASS",
            "replicates": replicates
        })
    except Exception as e:
        diagnostics["errors"].append({"test": "cdf_range", "error": str(e)})
    
    # Test 6: Support constraint (centered_maximum >= -log(n))
    try:
        for _ in range(replicates):
            n = random.randint(2, 50)
            sample = [random.expovariate(1.0) for _ in range(n)]
            request = {"sample": sample}
            response = run_estimator(request)
            
            log_n = math.log(n)
            assert response["centered_maximum"] >= -log_n - 1e-10
        
        diagnostics["test_results"].append({
            "test": "support_constraint",
            "status": "PASS",
            "replicates": replicates
        })
    except Exception as e:
        diagnostics["errors"].append({"test": "support_constraint", "error": str(e)})
    
    # Test 7: Reject missing key
    try:
        request = {"other_key": [0.5, 1.5]}
        try:
            run_estimator(request)
            diagnostics["errors"].append({"test": "reject_missing_key", "error": "Did not raise ValueError"})
        except ValueError:
            diagnostics["test_results"].append({
                "test": "reject_missing_key",
                "status": "PASS"
            })
    except Exception as e:
        diagnostics["errors"].append({"test": "reject_missing_key", "error": str(e)})
    
    # Test 8: Reject extra key
    try:
        request = {"sample": [0.5, 1.5], "extra": "key"}
        try:
            run_estimator(request)
            diagnostics["errors"].append({"test": "reject_extra_key", "error": "Did not raise ValueError"})
        except ValueError:
            diagnostics["test_results"].append({
                "test": "reject_extra_key",
                "status": "PASS"
            })
    except Exception as e:
        diagnostics["errors"].append({"test": "reject_extra_key", "error": str(e)})
    
    # Test 9: Reject non-list sample
    try:
        request = {"sample": (0.5, 1.5)}
        try:
            run_estimator(request)
            diagnostics["errors"].append({"test": "reject_tuple", "error": "Did not raise ValueError"})
        except ValueError:
            diagnostics["test_results"].append({
                "test": "reject_tuple",
                "status": "PASS"
            })
    except Exception as e:
        diagnostics["errors"].append({"test": "reject_tuple", "error": str(e)})
    
    # Test 10: Reject Boolean
    try:
        request = {"sample": [0.5, True, 1.5]}
        try:
            run_estimator(request)
            diagnostics["errors"].append({"test": "reject_boolean", "error": "Did not raise ValueError"})
        except ValueError:
            diagnostics["test_results"].append({
                "test": "reject_boolean",
                "status": "PASS"
            })
    except Exception as e:
        diagnostics["errors"].append({"test": "reject_boolean", "error": str(e)})
    
    # Test 11: Reject NaN
    try:
        request = {"sample": [0.5, float('nan'), 1.5]}
        try:
            run_estimator(request)
            diagnostics["errors"].append({"test": "reject_nan", "error": "Did not raise ValueError"})
        except ValueError:
            diagnostics["test_results"].append({
                "test": "reject_nan",
                "status": "PASS"
            })
    except Exception as e:
        diagnostics["errors"].append({"test": "reject_nan", "error": str(e)})
    
    # Test 12: Reject infinity
    try:
        request = {"sample": [0.5, float('inf'), 1.5]}
        try:
            run_estimator(request)
            diagnostics["errors"].append({"test": "reject_infinity", "error": "Did not raise ValueError"})
        except ValueError:
            diagnostics["test_results"].append({
                "test": "reject_infinity",
                "status": "PASS"
            })
    except Exception as e:
        diagnostics["errors"].append({"test": "reject_infinity", "error": str(e)})
    
    # Test 13: Reject negative value
    try:
        request = {"sample": [0.5, -0.1, 1.5]}
        try:
            run_estimator(request)
            diagnostics["errors"].append({"test": "reject_negative", "error": "Did not raise ValueError"})
        except ValueError:
            diagnostics["test_results"].append({
                "test": "reject_negative",
                "status": "PASS"
            })
    except Exception as e:
        diagnostics["errors"].append({"test": "reject_negative", "error": str(e)})
    
    # Test 14: Reject too few elements
    try:
        request = {"sample": [0.5]}
        try:
            run_estimator(request)
            diagnostics["errors"].append({"test": "reject_too_few", "error": "Did not raise ValueError"})
        except ValueError:
            diagnostics["test_results"].append({
                "test": "reject_too_few",
                "status": "PASS"
            })
    except Exception as e:
        diagnostics["errors"].append({"test": "reject_too_few", "error": str(e)})
    
    # Test 15: Reject too many elements
    try:
        request = {"sample": [0.5] * 501}
        try:
            run_estimator(request)
            diagnostics["errors"].append({"test": "reject_too_many", "error": "Did not raise ValueError"})
        except ValueError:
            diagnostics["test_results"].append({
                "test": "reject_too_many",
                "status": "PASS"
            })
    except Exception as e:
        diagnostics["errors"].append({"test": "reject_too_many", "error": str(e)})
    
    # Test 16: Mathematical identity check at y=0
    try:
        # If maximum = log(n), then centered_maximum = 0
        n = 10
        maximum = math.log(n)
        sample = [0.0] * (n - 1) + [maximum]
        request = {"sample": sample}
        response = run_estimator(request)
        
        # Exact CDF at y=0: (1 - 1/n)^n
        expected_exact = (1.0 - 1.0 / n) ** n
        # Gumbel CDF at y=0: exp(-1)
        expected_gumbel = math.exp(-1.0)
        
        assert abs(response["centered_maximum"] - 0.0) < 1e-10
        assert abs(response["exact_cdf_at_centered"] - expected_exact) < 1e-10
        assert abs(response["gumbel_cdf_at_centered"] - expected_gumbel) < 1e-10
        
        diagnostics["test_results"].append({
            "test": "identity_at_y_zero",
            "status": "PASS",
            "exact_cdf": response["exact_cdf_at_centered"],
            "gumbel_cdf": response["gumbel_cdf_at_centered"]
        })
    except Exception as e:
        diagnostics["errors"].append({"test": "identity_at_y_zero", "error": str(e)})
    
    # Test 17: Response structure
    try:
        request = {"sample": [0.5, 1.5, 2.0]}
        response = run_estimator(request)
        
        expected_keys = {"sample_size", "maximum", "centered_maximum", "exact_cdf_at_centered", "gumbel_cdf_at_centered"}
        assert set(response.keys()) == expected_keys
        assert isinstance(response["sample_size"], int)
        assert isinstance(response["maximum"], (int, float))
        assert isinstance(response["centered_maximum"], (int, float))
        assert isinstance(response["exact_cdf_at_centered"], (int, float))
        assert isinstance(response["gumbel_cdf_at_centered"], (int, float))
        
        diagnostics["test_results"].append({
            "test": "response_structure",
            "status": "PASS"
        })
    except Exception as e:
        diagnostics["errors"].append({"test": "response_structure", "error": str(e)})
    
    # Summary
    diagnostics["summary"] = {
        "total_tests": len(diagnostics["test_results"]) + len(diagnostics["errors"]),
        "passed": len(diagnostics["test_results"]),
        "failed": len(diagnostics["errors"])
    }
    
    return diagnostics


if __name__ == "__main__":
    result = run_sandbox()
    print(json.dumps(result, indent=2))
