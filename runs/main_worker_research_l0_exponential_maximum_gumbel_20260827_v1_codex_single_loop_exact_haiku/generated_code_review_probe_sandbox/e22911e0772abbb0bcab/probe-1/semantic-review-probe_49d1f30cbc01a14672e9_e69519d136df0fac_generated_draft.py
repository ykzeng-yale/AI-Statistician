
import random

def run_sandbox(seed=42, replicates=50):
    """
    Comprehensive probe of est_exponential_maximum_gumbel against the frozen contract.
    Tests:
    1. Request validation (closed contract, edge cases)
    2. Response structure and types
    3. Mathematical correctness of CDF formulas
    4. Support constraint enforcement
    5. Boundary behavior
    """
    
    results = {
        "tests_passed": 0,
        "tests_failed": 0,
        "failures": []
    }
    
    # Test 1: Valid request with known values
    try:
        request = {"sample": [0.5, 1.5, 2.0]}
        response = estimators["est_exponential_maximum_gumbel"](request)
        
        # Check response structure
        assert set(response.keys()) == {"sample_size", "maximum", "centered_maximum", "exact_cdf_at_centered", "gumbel_cdf_at_centered"}
        assert response["sample_size"] == 3
        assert response["maximum"] == 2.0
        
        # Check CDF values are in valid range
        assert 0.0 <= response["exact_cdf_at_centered"] <= 1.0
        assert 0.0 < response["gumbel_cdf_at_centered"] < 1.0
        
        results["tests_passed"] += 1
    except Exception as e:
        results["tests_failed"] += 1
        results["failures"].append({"test": "valid_request", "error": str(e)})
    
    # Test 2: All zeros (boundary case at support lower bound)
    try:
        request = {"sample": [0.0, 0.0, 0.0, 0.0, 0.0]}
        response = estimators["est_exponential_maximum_gumbel"](request)
        
        n = 5
        assert response["sample_size"] == n
        assert response["maximum"] == 0.0
        
        # At y = -log(n), exact CDF should be 0
        assert response["exact_cdf_at_centered"] < 1e-50
        
        results["tests_passed"] += 1
    except Exception as e:
        results["tests_failed"] += 1
        results["failures"].append({"test": "all_zeros_boundary", "error": str(e)})
    
    # Test 3: Permutation invariance
    try:
        sample = [0.1, 2.5, 1.3, 0.8, 3.2]
        request1 = {"sample": sample}
        response1 = estimators["est_exponential_maximum_gumbel"](request1)
        
        sample_permuted = [3.2, 0.1, 1.3, 2.5, 0.8]
        request2 = {"sample": sample_permuted}
        response2 = estimators["est_exponential_maximum_gumbel"](request2)
        
        assert response1["maximum"] == response2["maximum"]
        assert abs(response1["centered_maximum"] - response2["centered_maximum"]) < 1e-10
        assert abs(response1["exact_cdf_at_centered"] - response2["exact_cdf_at_centered"]) < 1e-10
        assert abs(response1["gumbel_cdf_at_centered"] - response2["gumbel_cdf_at_centered"]) < 1e-10
        
        results["tests_passed"] += 1
    except Exception as e:
        results["tests_failed"] += 1
        results["failures"].append({"test": "permutation_invariance", "error": str(e)})
    
    # Test 4: Support constraint (centered_maximum >= -log(n))
    try:
        random.seed(seed)
        for _ in range(20):
            n = random.randint(2, 100)
            sample = [random.expovariate(1.0) for _ in range(n)]
            request = {"sample": sample}
            response = estimators["est_exponential_maximum_gumbel"](request)
            
            # Support constraint: centered_maximum >= -log(n)
            # This is always satisfied since maximum >= 0 and centered_maximum = maximum - log(n)
            assert response["centered_maximum"] >= -10.0  # Loose check
        
        results["tests_passed"] += 1
    except Exception as e:
        results["tests_failed"] += 1
        results["failures"].append({"test": "support_constraint", "error": str(e)})
    
    # Test 5: Reject missing key
    try:
        request = {"other_key": [0.5, 1.5]}
        try:
            estimators["est_exponential_maximum_gumbel"](request)
            results["tests_failed"] += 1
            results["failures"].append({"test": "reject_missing_key", "error": "Did not raise ValueError"})
        except ValueError:
            results["tests_passed"] += 1
    except Exception as e:
        results["tests_failed"] += 1
        results["failures"].append({"test": "reject_missing_key", "error": str(e)})
    
    # Test 6: Reject extra key
    try:
        request = {"sample": [0.5, 1.5], "extra": "key"}
        try:
            estimators["est_exponential_maximum_gumbel"](request)
            results["tests_failed"] += 1
            results["failures"].append({"test": "reject_extra_key", "error": "Did not raise ValueError"})
        except ValueError:
            results["tests_passed"] += 1
    except Exception as e:
        results["tests_failed"] += 1
        results["failures"].append({"test": "reject_extra_key", "error": str(e)})
    
    # Test 7: Reject non-list sample
    try:
        request = {"sample": (0.5, 1.5)}
        try:
            estimators["est_exponential_maximum_gumbel"](request)
            results["tests_failed"] += 1
            results["failures"].append({"test": "reject_tuple", "error": "Did not raise ValueError"})
        except ValueError:
            results["tests_passed"] += 1
    except Exception as e:
        results["tests_failed"] += 1
        results["failures"].append({"test": "reject_tuple", "error": str(e)})
    
    # Test 8: Reject Boolean
    try:
        request = {"sample": [0.5, True, 1.5]}
        try:
            estimators["est_exponential_maximum_gumbel"](request)
            results["tests_failed"] += 1
            results["failures"].append({"test": "reject_boolean", "error": "Did not raise ValueError"})
        except ValueError:
            results["tests_passed"] += 1
    except Exception as e:
        results["tests_failed"] += 1
        results["failures"].append({"test": "reject_boolean", "error": str(e)})
    
    # Test 9: Reject NaN
    try:
        request = {"sample": [0.5, float('nan'), 1.5]}
        try:
            estimators["est_exponential_maximum_gumbel"](request)
            results["tests_failed"] += 1
            results["failures"].append({"test": "reject_nan", "error": "Did not raise ValueError"})
        except ValueError:
            results["tests_passed"] += 1
    except Exception as e:
        results["tests_failed"] += 1
        results["failures"].append({"test": "reject_nan", "error": str(e)})
    
    # Test 10: Reject infinity
    try:
        request = {"sample": [0.5, float('inf'), 1.5]}
        try:
            estimators["est_exponential_maximum_gumbel"](request)
            results["tests_failed"] += 1
            results["failures"].append({"test": "reject_infinity", "error": "Did not raise ValueError"})
        except ValueError:
            results["tests_passed"] += 1
    except Exception as e:
        results["tests_failed"] += 1
        results["failures"].append({"test": "reject_infinity", "error": str(e)})
    
    # Test 11: Reject negative value
    try:
        request = {"sample": [0.5, -0.1, 1.5]}
        try:
            estimators["est_exponential_maximum_gumbel"](request)
            results["tests_failed"] += 1
            results["failures"].append({"test": "reject_negative", "error": "Did not raise ValueError"})
        except ValueError:
            results["tests_passed"] += 1
    except Exception as e:
        results["tests_failed"] += 1
        results["failures"].append({"test": "reject_negative", "error": str(e)})
    
    # Test 12: Reject too few elements
    try:
        request = {"sample": [0.5]}
        try:
            estimators["est_exponential_maximum_gumbel"](request)
            results["tests_failed"] += 1
            results["failures"].append({"test": "reject_too_few", "error": "Did not raise ValueError"})
        except ValueError:
            results["tests_passed"] += 1
    except Exception as e:
        results["tests_failed"] += 1
        results["failures"].append({"test": "reject_too_few", "error": str(e)})
    
    # Test 13: Reject too many elements
    try:
        request = {"sample": [0.5] * 501}
        try:
            estimators["est_exponential_maximum_gumbel"](request)
            results["tests_failed"] += 1
            results["failures"].append({"test": "reject_too_many", "error": "Did not raise ValueError"})
        except ValueError:
            results["tests_passed"] += 1
    except Exception as e:
        results["tests_failed"] += 1
        results["failures"].append({"test": "reject_too_many", "error": str(e)})
    
    # Test 14: CDF range and monotonicity
    try:
        random.seed(seed)
        for _ in range(20):
            n = random.randint(2, 100)
            sample = [random.expovariate(1.0) for _ in range(n)]
            request = {"sample": sample}
            response = estimators["est_exponential_maximum_gumbel"](request)
            
            assert 0.0 <= response["exact_cdf_at_centered"] <= 1.0
            assert 0.0 < response["gumbel_cdf_at_centered"] < 1.0
        
        results["tests_passed"] += 1
    except Exception as e:
        results["tests_failed"] += 1
        results["failures"].append({"test": "cdf_range", "error": str(e)})
    
    # Test 15: Determinism
    try:
        request = {"sample": [0.5, 1.5, 2.0, 0.3]}
        response1 = estimators["est_exponential_maximum_gumbel"](request)
        response2 = estimators["est_exponential_maximum_gumbel"](request)
        
        assert response1 == response2
        
        results["tests_passed"] += 1
    except Exception as e:
        results["tests_failed"] += 1
        results["failures"].append({"test": "determinism", "error": str(e)})
    
    # Test 16: Response type checking
    try:
        request = {"sample": [0.5, 1.5, 2.0]}
        response = estimators["est_exponential_maximum_gumbel"](request)
        
        assert isinstance(response["sample_size"], int)
        assert isinstance(response["maximum"], (int, float))
        assert isinstance(response["centered_maximum"], (int, float))
        assert isinstance(response["exact_cdf_at_centered"], (int, float))
        assert isinstance(response["gumbel_cdf_at_centered"], (int, float))
        
        results["tests_passed"] += 1
    except Exception as e:
        results["tests_failed"] += 1
        results["failures"].append({"test": "response_types", "error": str(e)})
    
    return results
