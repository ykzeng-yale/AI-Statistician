
import math

def run_sandbox(seed=42, replicates=1):
    """Minimal sandbox for probe execution."""
    return {"status": "probe_ready"}

# Test 1: Tuple rejection (prior finding)
try:
    result = estimators["est_exponential_maximum_gumbel"]({"sample": (0.5, 1.5)})
    print("FAIL: Tuple was accepted instead of rejected")
except ValueError as e:
    print(f"PASS: Tuple correctly rejected")

# Test 2: Valid list input
try:
    result = estimators["est_exponential_maximum_gumbel"]({"sample": [0.5, 1.5, 2.0]})
    print(f"PASS: Valid list accepted with sample_size={result['sample_size']}")
except Exception as e:
    print(f"FAIL: Valid list rejected: {e}")

# Test 3: All zeros boundary
try:
    result = estimators["est_exponential_maximum_gumbel"]({"sample": [0.0, 0.0, 0.0, 0.0, 0.0]})
    print(f"PASS: All zeros accepted")
except Exception as e:
    print(f"FAIL: All zeros rejected: {e}")

# Test 4: Identity at y=0
try:
    n = 10
    maximum = math.log(n)
    sample = [0.0] * (n - 1) + [maximum]
    result = estimators["est_exponential_maximum_gumbel"]({"sample": sample})
    expected_exact = (1.0 - 1.0 / n) ** n
    expected_gumbel = math.exp(-1.0)
    exact_match = abs(result["exact_cdf_at_centered"] - expected_exact) < 1e-10
    gumbel_match = abs(result["gumbel_cdf_at_centered"] - expected_gumbel) < 1e-10
    if exact_match and gumbel_match:
        print(f"PASS: Identity at y=0 verified")
    else:
        print(f"FAIL: Identity at y=0 mismatch")
except Exception as e:
    print(f"FAIL: Identity test failed: {e}")

# Test 5: Reject NaN
try:
    result = estimators["est_exponential_maximum_gumbel"]({"sample": [0.5, float('nan'), 1.5]})
    print("FAIL: NaN was accepted")
except ValueError:
    print(f"PASS: NaN correctly rejected")

# Test 6: Reject infinity
try:
    result = estimators["est_exponential_maximum_gumbel"]({"sample": [0.5, float('inf'), 1.5]})
    print("FAIL: Infinity was accepted")
except ValueError:
    print(f"PASS: Infinity correctly rejected")

# Test 7: Reject negative
try:
    result = estimators["est_exponential_maximum_gumbel"]({"sample": [0.5, -0.1, 1.5]})
    print("FAIL: Negative was accepted")
except ValueError:
    print(f"PASS: Negative correctly rejected")

# Test 8: Reject Boolean
try:
    result = estimators["est_exponential_maximum_gumbel"]({"sample": [0.5, True, 1.5]})
    print("FAIL: Boolean was accepted")
except ValueError:
    print(f"PASS: Boolean correctly rejected")

# Test 9: Reject extra key
try:
    result = estimators["est_exponential_maximum_gumbel"]({"sample": [0.5, 1.5], "extra": "key"})
    print("FAIL: Extra key was accepted")
except ValueError:
    print(f"PASS: Extra key correctly rejected")

# Test 10: Reject missing key
try:
    result = estimators["est_exponential_maximum_gumbel"]({"other_key": [0.5, 1.5]})
    print("FAIL: Missing key was accepted")
except ValueError:
    print(f"PASS: Missing key correctly rejected")

# Test 11: Reject too few
try:
    result = estimators["est_exponential_maximum_gumbel"]({"sample": [0.5]})
    print("FAIL: Too few elements was accepted")
except ValueError:
    print(f"PASS: Too few elements correctly rejected")

# Test 12: Reject too many
try:
    result = estimators["est_exponential_maximum_gumbel"]({"sample": [0.5] * 501})
    print("FAIL: Too many elements was accepted")
except ValueError:
    print(f"PASS: Too many elements correctly rejected")

# Test 13: Permutation invariance
try:
    sample1 = [0.1, 2.5, 1.3, 0.8, 3.2]
    sample2 = [3.2, 0.1, 1.3, 2.5, 0.8]
    result1 = estimators["est_exponential_maximum_gumbel"]({"sample": sample1})
    result2 = estimators["est_exponential_maximum_gumbel"]({"sample": sample2})
    if (result1["maximum"] == result2["maximum"] and
        abs(result1["centered_maximum"] - result2["centered_maximum"]) < 1e-10):
        print(f"PASS: Permutation invariance verified")
    else:
        print(f"FAIL: Permutation invariance violated")
except Exception as e:
    print(f"FAIL: Permutation test failed: {e}")

# Test 14: Determinism
try:
    request = {"sample": [0.5, 1.5, 2.0, 0.3]}
    result1 = estimators["est_exponential_maximum_gumbel"](request)
    result2 = estimators["est_exponential_maximum_gumbel"](request)
    if result1 == result2:
        print(f"PASS: Determinism verified")
    else:
        print(f"FAIL: Determinism violated")
except Exception as e:
    print(f"FAIL: Determinism test failed: {e}")

# Test 15: Response structure
try:
    result = estimators["est_exponential_maximum_gumbel"]({"sample": [0.5, 1.5, 2.0]})
    expected_keys = {"sample_size", "maximum", "centered_maximum", "exact_cdf_at_centered", "gumbel_cdf_at_centered"}
    if set(result.keys()) == expected_keys:
        print(f"PASS: Response structure correct")
    else:
        print(f"FAIL: Response structure incorrect")
except Exception as e:
    print(f"FAIL: Response structure test failed: {e}")

# Test 16: CDF range
try:
    result = estimators["est_exponential_maximum_gumbel"]({"sample": [0.5, 1.5, 2.0]})
    if (0.0 <= result["exact_cdf_at_centered"] <= 1.0 and
        0.0 < result["gumbel_cdf_at_centered"] < 1.0):
        print(f"PASS: CDF values in valid range")
    else:
        print(f"FAIL: CDF values out of range")
except Exception as e:
    print(f"FAIL: CDF range test failed: {e}")
