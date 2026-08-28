# Python Estimator: est_exponential_maximum_gumbel

## Closed Sample Contract

**Request:** A JSON object with exactly one field:
- `sample`: A list of 2 to 500 finite nonnegative real numbers.

**Response:** A JSON object with exactly five fields:
- `sample_size`: Integer, the length of the sample.
- `maximum`: The largest value in the sample.
- `centered_maximum`: The maximum minus the natural logarithm of the sample size.
- `exact_cdf_at_centered`: The exact finite-sample CDF of $Y_n$ evaluated at the centered maximum.
- `gumbel_cdf_at_centered`: The standard Gumbel CDF evaluated at the centered maximum.

## Implementation

```python
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
```

## Validation and Examples

### Example 1: Small Sample (n=10)

For a sample of 10 observations from the rate-one exponential distribution, the estimator computes:
- The sample maximum $M_{10}$
- The centered maximum $Y_{10} = M_{10} - \log(10)$
- The exact finite-sample CDF: $(1 - e^{-Y_{10}}/10)^{10}$
- The Gumbel CDF: $\exp(-e^{-Y_{10}})$

### Example 2: All Zeros (n=5)

If the sample is $[0, 0, 0, 0, 0]$:
- $M_5 = 0$
- $Y_5 = 0 - \log(5) = -\log(5) \approx -1.609$
- Exact CDF: $(1 - e^{\log(5)}/5)^5 = (1 - 1)^5 = 0$
- Gumbel CDF: $\exp(-e^{\log(5)}) = \exp(-5) \approx 0.0067$

### Example 3: Verification at y=0

If the maximum equals $\log(n)$, then $Y_n = 0$:
- Exact CDF: $(1 - 1/n)^n$
- Gumbel CDF: $\exp(-1) \approx 0.3679$

For $n=10$: Exact = $0.9^{10} \approx 0.3487$, Gumbel $\approx 0.3679$, error $\approx 0.0192$.

## Error Handling

The estimator rejects requests that:
- Do not have exactly the key `sample`
- Have a `sample` that is not a list
- Have fewer than 2 or more than 500 elements
- Contain non-numeric elements (including Booleans)
- Contain non-finite values (NaN, infinity)
- Contain negative values

All rejections raise a `ValueError` without mutation or coercion.

## Determinism and Permutation Invariance

- The estimator is deterministic: repeated calls with the same sample produce identical results (up to floating-point equality).
- The estimator is permutation-invariant: reordering the sample does not change the response (since the maximum is order-independent).
- The estimator does not mutate the request.
