
import math

def run_sandbox(seed=42, replicates=1):
    """Minimal sandbox for probe execution."""
    return {"status": "probe_ready"}

# Test 1: Tuple rejection (prior finding)
try:
    result = estimators["est_exponential_maximum_gumbel"]({"sample": (0.5, 1.5)})
    print("FAIL: Tuple was accepted instead of rejected")
    print(f"Result: {result}")
except ValueError as e:
    print(f"PASS: Tuple correctly rejected with error: {e}")

# Test 2: Valid list input
try:
    result = estimators["est_exponential_maximum_gumbel"]({"sample": [0.5, 1.5, 2.0]})
    print(f"PASS: Valid list accepted")
    print(f"  sample_size: {result['sample_size']}")
    print(f"  maximum: {result['maximum']}")
    print(f"  centered_maximum: {result['centered_maximum']}")
    print(f"  exact_cdf_at_centered: {result['exact_cdf_at_centered']}")
    print(f"  gumbel_cdf_at_centered: {result['gumbel_cdf_at_centered']}")
except Exception as e:
    print(f"FAIL: Valid list rejected with error: {e}")

# Test 3: Boundary case - all zeros
try:
    result = estimators["est_exponential_maximum_gumbel"]({"sample": [0.0, 0.0, 0.0, 0.0, 0.0]})
    n = 5
    log_n = math.log(n)
    print(f"PASS: All zeros accepted")
    print(f"  centered_maximum: {result['centered_maximum']}")
    print(f"  expected: {-log_n}")
    print(f"  exact_cdf_at_centered: {result['exact_cdf_at_centered']}")
    print(f"  gumbel_cdf_at_centered: {result['gumbel_cdf_at_centered']}")
except Exception as e:
    print(f"FAIL: All zeros rejected with error: {e}")

# Test 4: Identity check at y=0
try:
    n = 10
    maximum = math.log(n)
    sample = [0.0] * (n - 1) + [maximum]
    result = estimators["est_exponential_maximum_gumbel"]({"sample": sample})
    expected_exact = (1.0 - 1.0 / n) ** n
    expected_gumbel = math.exp(-1.0)
    print(f"PASS: Identity check at y=0")
    print(f"  centered_maximum: {result['centered_maximum']}")
    print(f"  exact_cdf_at_centered: {result['exact_cdf_at_centered']}")
    print(f"  expected_exact: {expected_exact}")
    print(f"  gumbel_cdf_at_centered: {result['gumbel_cdf_at_centered']}")
    print(f"  expected_gumbel: {expected_gumbel}")
except Exception as e:
    print(f"FAIL: Identity check failed with error: {e}")

# Test 5: Reject NaN
try:
    result = estimators["est_exponential_maximum_gumbel"]({"sample": [0.5, float('nan'), 1.5]})
    print("FAIL: NaN was accepted instead of rejected")
except ValueError as e:
    print(f"PASS: NaN correctly rejected with error: {e}")

# Test 6: Reject infinity
try:
    result = estimators["est_exponential_maximum_gumbel"]({"sample": [0.5, float('inf'), 1.5]})
    print("FAIL: Infinity was accepted instead of rejected")
except ValueError as e:
    print(f"PASS: Infinity correctly rejected with error: {e}")

# Test 7: Reject negative
try:
    result = estimators["est_exponential_maximum_gumbel"]({"sample": [0.5, -0.1, 1.5]})
    print("FAIL: Negative value was accepted instead of rejected")
except ValueError as e:
    print(f"PASS: Negative value correctly rejected with error: {e}")

# Test 8: Reject Boolean
try:
    result = estimators["est_exponential_maximum_gumbel"]({"sample": [0.5, True, 1.5]})
    print("FAIL: Boolean was accepted instead of rejected")
except ValueError as e:
    print(f"PASS: Boolean correctly rejected with error: {e}")

# Test 9: Reject extra key
try:
    result = estimators["est_exponential_maximum_gumbel"]({"sample": [0.5, 1.5], "extra": "key"})
    print("FAIL: Extra key was accepted instead of rejected")
except ValueError as e:
    print(f"PASS: Extra key correctly rejected with error: {e}")

# Test 10: Reject missing key
try:
    result = estimators["est_exponential_maximum_gumbel"]({"other_key": [0.5, 1.5]})
    print("FAIL: Missing key was accepted instead of rejected")
except ValueError as e:
    print(f"PASS: Missing key correctly rejected with error: {e}")

# Test 11: Reject too few elements
try:
    result = estimators["est_exponential_maximum_gumbel"]({"sample": [0.5]})
    print("FAIL: Too few elements was accepted instead of rejected")
except ValueError as e:
    print(f"PASS: Too few elements correctly rejected with error: {e}")

# Test 12: Reject too many elements
try:
    result = estimators["est_exponential_maximum_gumbel"]({"sample": [0.5] * 501})
    print("FAIL: Too many elements was accepted instead of rejected")
except ValueError as e:
    print(f"PASS: Too many elements correctly rejected with error: {e}")

# Test 13: Permutation invariance
try:
    sample1 = [0.1, 2.5, 1.3, 0.8, 3.2]
    sample2 = [3.2, 0.1, 1.3, 2.5, 0.8]
    result1 = estimators["est_exponential_maximum_gumbel"]({"sample": sample1})
    result2 = estimators["est_exponential_maximum_gumbel"]({"sample": sample2})
    if (result1["maximum"] == result2["maximum"] and
        abs(result1["centered_maximum"] - result2["centered_maximum"]) < 1e-10 and
        abs(result1["exact_cdf_at_centered"] - result2["exact_cdf_at_centered"]) < 1e-10 and
        abs(result1["gumbel_cdf_at_centered"] - result2["gumbel_cdf_at_centered"]) < 1e-10):
        print("PASS: Permutation invariance verified")
    else:
        print("FAIL: Permutation invariance violated")
except Exception as e:
    print(f"FAIL: Permutation invariance test failed with error: {e}")

# Test 14: Determinism
try:
    request = {"sample": [0.5, 1.5, 2.0, 0.3]}
    result1 = estimators["est_exponential_maximum_gumbel"](request)
    result2 = estimators["est_exponential_maximum_gumbel"](request)
    if result1 == result2:
        print("PASS: Determinism verified")
    else:
        print("FAIL: Determinism violated")
except Exception as e:
    print(f"FAIL: Determinism test failed with error: {e}")

# Test 15: Response structure
try:
    result = estimators["est_exponential_maximum_gumbel"]({"sample": [0.5, 1.5, 2.0]})
    expected_keys = {"sample_size", "maximum", "centered_maximum", "exact_cdf_at_centered", "gumbel_cdf_at_centered"}
    if (set(result.keys()) == expected_keys and
        isinstance(result["sample_size"], int) and
        isinstance(result["maximum"], (int, float)) and
        isinstance(result["centered_maximum"], (int, float)) and
        isinstance(result["exact_cdf_at_centered"], (int, float)) and
        isinstance(result["gumbel_cdf_at_centered"], (int, float))):
        print("PASS: Response structure correct")
    else:
        print("FAIL: Response structure incorrect")
except Exception as e:
    print(f"FAIL: Response structure test failed with error: {e}")

# Test 16: CDF range
try:
    result = estimators["est_exponential_maximum_gumbel"]({"sample": [0.5, 1.5, 2.0]})
    if (0.0 <= result["exact_cdf_at_centered"] <= 1.0 and
        0.0 < result["gumbel_cdf_at_centered"] < 1.0):
        print("PASS: CDF values in valid range")
    else:
        print("FAIL: CDF values out of range")
except Exception as e:
    print(f"FAIL: CDF range test failed with error: {e}")
