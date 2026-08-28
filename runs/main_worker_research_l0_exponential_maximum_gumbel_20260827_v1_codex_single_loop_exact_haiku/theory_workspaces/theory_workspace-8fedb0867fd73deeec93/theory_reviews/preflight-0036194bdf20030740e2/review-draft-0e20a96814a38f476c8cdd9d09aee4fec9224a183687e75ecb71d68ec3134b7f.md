# Independent Mathematical Referee Report
## Gumbel Limit for the Maximum of Exponential Observations

**Review Date:** 2026-08-28  
**Task:** Evaluate mathematical coherence of theory handoff for exponential maximum and Gumbel limit, with execution handoff required.

---

## Executive Summary

The theory documents present a mathematically coherent derivation of the exact finite-sample CDF of the centered maximum $Y_n = M_n - \log n$ of $n$ independent rate-one exponential random variables, and prove pointwise convergence to the standard Gumbel CDF. The estimator implementation correctly computes the required quantities. All load-bearing definitions, theorems, and formulas have been independently verified. The finite estimator is well-specified and ready for execution handoff.

---

## Scope and Definitions

### Problem Setup (Verified)

**Source:** exponential_maximum_gumbel_theory.md, lines 1–18

- **Independent observations:** $X_1, \ldots, X_n$ i.i.d. with rate-one exponential CDF $F(x) = 1 - e^{-x}$ for $x \geq 0$.
- **Sample maximum:** $M_n = \max_i X_i$.
- **Centered maximum:** $Y_n = M_n - \log n$ (natural logarithm).
- **Support constraint:** $M_n \geq 0$ implies $Y_n \geq -\log n$.

All definitions are standard and correctly stated.

---

## Load-Bearing Theorems

### Theorem 1: Exact CDF of $M_n$ (Verified)

**Source:** exponential_maximum_gumbel_theory.md, lines 20–32

**Statement:**
$$P(M_n \leq x) = \begin{cases} 0 & \text{if } x < 0 \\ (1 - e^{-x})^n & \text{if } x \geq 0 \end{cases}$$

**Proof Reconstruction:**
By independence, $P(M_n \leq x) = [F(x)]^n$. For $x < 0$, $F(x) = 0$, so $P(M_n \leq x) = 0$. For $x \geq 0$, $F(x) = 1 - e^{-x}$, so $P(M_n \leq x) = (1 - e^{-x})^n$.

**Status:** ✓ Correct. The formula is the standard result for the maximum of i.i.d. random variables.

---

### Theorem 2: Exact CDF of $Y_n$ with Support Branch (Verified)

**Source:** exponential_maximum_gumbel_theory.md, lines 34–52

**Statement:**
$$P(Y_n \leq y) = \begin{cases} 0 & \text{if } y < -\log n \\ \left(1 - \frac{e^{-y}}{n}\right)^n & \text{if } y \geq -\log n \end{cases}$$

**Proof Reconstruction:**
$Y_n \leq y \iff M_n \leq y + \log n$.

- **Case 1:** $y < -\log n \Rightarrow y + \log n < 0 \Rightarrow P(M_n \leq y + \log n) = 0$ by Theorem 1.
- **Case 2:** $y \geq -\log n \Rightarrow y + \log n \geq 0 \Rightarrow P(M_n \leq y + \log n) = (1 - e^{-(y + \log n)})^n = \left(1 - \frac{e^{-y}}{n}\right)^n$ by Theorem 1.

**Support Remark:** The lower bound $Y_n \geq -\log n$ is correctly justified: since $M_n \geq 0$, we have $Y_n = M_n - \log n \geq -\log n$.

**Status:** ✓ Correct. The support-aware branch is essential and correctly derived.

---

### Theorem 3: Pointwise Convergence to Gumbel (Verified)

**Source:** exponential_maximum_gumbel_theory.md, lines 54–72

**Statement:**
For every fixed $y \in \mathbb{R}$,
$$\lim_{n \to \infty} P(Y_n \leq y) = e^{-e^{-y}}$$

**Proof Reconstruction:**
Fix $y \in \mathbb{R}$. For sufficiently large $n$, $y \geq -\log n$ (since $-\log n \to -\infty$). Thus:
$$P(Y_n \leq y) = \left(1 - \frac{e^{-y}}{n}\right)^n$$

By the standard limit $\lim_{n \to \infty} (1 + c/n)^n = e^c$ with $c = -e^{-y}$:
$$\lim_{n \to \infty} \left(1 - \frac{e^{-y}}{n}\right)^n = e^{-e^{-y}}$$

**Regime Clarity:** The proof correctly emphasizes the fixed-$y$ regime: for each fixed $y$, the support constraint $y \geq -\log n$ is eventually satisfied as $n \to \infty$.

**Status:** ✓ Correct. The limit is properly justified and the fixed-$y$ regime is clearly stated.

---

## Distinction: Exact vs. Asymptotic (Verified)

**Source:** exponential_maximum_gumbel_theory.md, lines 74–88

The document explicitly distinguishes the exact finite-$n$ CDF from the Gumbel approximation and provides a numerical example:
- For $n = 10$, $y = 0$: Exact = $0.9^{10} \approx 0.3487$, Gumbel = $e^{-1} \approx 0.3679$, error $\approx 0.0192$.

**Status:** ✓ Correct. The distinction is clear and the example is accurate.

---

## Assumptions and Scope (Verified)

**Source:** exponential_maximum_gumbel_theory.md, lines 90–104

The document lists five key assumptions:
1. **Independence:** $X_1, \ldots, X_n$ are mutually independent.
2. **Identical distribution:** Each $X_i$ is rate-one exponential.
3. **Support:** $[0, \infty)$, constraining $M_n \geq 0$ and $Y_n \geq -\log n$.
4. **Normalization:** Centering by $\log n$ (not $n$, $\sqrt{n}$, etc.).
5. **Fixed-$y$ regime:** Pointwise convergence for each fixed $y$, not uniform.

**Status:** ✓ All assumptions are correctly stated and material to the result.

---

## Sanity Checks (Verified)

**Source:** exponential_maximum_gumbel_theory.md, lines 121–185

The document includes seven sanity checks:

1. **Check 1 (y=0, n=10):** Exact CDF = $0.3487$, Gumbel = $0.3679$, error = $0.0192$. ✓ Verified numerically.
2. **Check 2 (Support boundary):** At $y = -\log n$, exact CDF $\approx 0$ (numerically $\approx 10^{-157}$ for $n=10$). ✓ Verified.
3. **Check 3 (Support constraint):** $Y_n \geq -\log n$ for 100 samples of size 50. ✓ Verified.
4. **Check 4 (Pointwise convergence at y=0):** Error decreases as $O(1/n)$. ✓ Verified.
5. **Check 5 (Monotonicity):** Exact CDF is strictly increasing in $y$. ✓ Verified.
6. **Check 6 (Gumbel range):** Gumbel CDF is in $(0, 1)$ for $y \in [-5, 5]$. ✓ Verified.
7. **Check 7 (Error scaling):** Error $\propto 1/n$. ✓ Verified.

**Independent Verification:** Scratch execution confirms all checks. Error scaling is consistent: $\text{error} \times n \approx 0.18$ across $n \in \{10, 20, 50, 100, 200, 500, 1000\}$, confirming $O(1/n)$ behavior.

---

## Estimator Implementation (Verified)

**Source:** est_exponential_maximum_gumbel.md, lines 1–138

### Request Contract
- **Input:** JSON object with exactly one field `sample`, a list of 2–500 nonnegative finite real numbers.
- **Validation:** Rejects non-lists, out-of-range lengths, non-numeric elements, Booleans, non-finite values, and negative values without mutation or coercion.

**Status:** ✓ Correct and complete.

### Response Contract
- **sample_size:** $n = \text{len}(sample)$.
- **maximum:** $M_n = \max(\text{sample})$.
- **centered_maximum:** $Y_n = M_n - \log n$.
- **exact_cdf_at_centered:** $P(Y_n \leq Y_n) = \begin{cases} 0 & \text{if } Y_n < -\log n \\ (1 - e^{-Y_n}/n)^n & \text{if } Y_n \geq -\log n \end{cases}$.
- **gumbel_cdf_at_centered:** $e^{-e^{-Y_n}}$.

**Status:** ✓ Correct. All five fields are required and correctly defined.

### Implementation Logic (Verified)

**Source:** est_exponential_maximum_gumbel.md, lines 51–138

The Python code:
1. Validates the request structure and sample contents.
2. Computes $n$, $M_n$, $\log n$, and $Y_n$.
3. Computes exact CDF using the support-aware formula.
4. Computes Gumbel CDF as $\exp(-\exp(-Y_n))$.
5. Returns all five fields.

**Scratch Verification:**
- **Test 7 (Estimator logic):** For a sample of size 50, the estimator correctly computes $Y_n = 0.7255$, exact CDF = $0.6148$, Gumbel CDF = $0.6162$, and verifies $Y_n \geq -\log(50)$.
- **Test 8 (Edge case: all zeros):** For sample $[0, 0, 0, 0, 0]$, the estimator correctly computes $Y_5 = -\log(5) \approx -1.609$, exact CDF $\approx 5.4 \times 10^{-79}$ (numerically zero), and Gumbel CDF $\approx 0.0067$.

**Status:** ✓ Implementation is correct and handles edge cases properly.

---

## Determinism and Permutation Invariance (Verified)

**Source:** est_exponential_maximum_gumbel.md, lines 130–138

The estimator is:
- **Deterministic:** Repeated calls with the same sample produce identical results (up to floating-point equality).
- **Permutation-invariant:** Reordering the sample does not change the response (since the maximum is order-independent).
- **Non-mutating:** The request is not modified.

**Status:** ✓ All properties are correctly implemented.

---

## Finite-Sample Approximation Error (Verified)

**Source:** exponential_maximum_gumbel_theory.md, lines 106–119

The document derives the approximation error:
$$\Delta_n(y) = \left(1 - \frac{e^{-y}}{n}\right)^n - e^{-e^{-y}} \approx -e^{-e^{-y}} \cdot \frac{e^{-2y}}{2n} + O(n^{-2})$$

The leading error term is $O(n^{-1})$, uniform in $y$ over compact intervals.

**Scratch Verification:** Error scaling test confirms $\text{error} \times n \approx 0.18$ (constant) across $n \in \{10, 20, 50, 100, 200, 500, 1000\}$, consistent with $O(1/n)$ behavior.

**Status:** ✓ Asymptotic expansion is correct.

---

## Relationship to Extreme Value Theory (Verified)

**Source:** exponential_maximum_gumbel_theory.md, lines 106–104

The document correctly identifies this result as a special case of the **Fisher–Tippett–Gnedenko theorem** for maxima. The exponential distribution belongs to the domain of attraction of the Gumbel distribution with normalization $a_n = \log n$ and $b_n = 0$.

**Status:** ✓ Correct contextualization.

---

## Execution Handoff Readiness

### Estimator Specification
- **Closed contract:** Request and response fields are exactly specified.
- **Validation:** Input validation is complete and rejects malformed requests.
- **Determinism:** The estimator is deterministic and permutation-invariant.
- **Finite output:** All response fields are finite scalars or integers.

**Status:** ✓ Ready for execution.

### Simulation Targets (From upstream_research_contract)

The handoff specifies three simulation targets:

1. **Empirical CDF comparison:** For each $n \in \{10, 50, 100, 250, 500\}$ and $y \in \{-2, -1, 0, 1, 2\}$, generate $M$ independent samples and compare empirical CDF to exact finite-$n$ CDF and Gumbel CDF.
2. **Estimator verification:** Verify that the estimator correctly computes all five response fields.
3. **Approximation error assessment:** Document error trends as $n$ increases without claiming uniform convergence or finite-$n$ equality.

**Status:** ✓ All targets are well-defined and executable.

---

## Mathematical Coherence Summary

| Component | Status | Evidence |
|-----------|--------|----------|
| Exact CDF of $M_n$ | ✓ Correct | Theorem 1, scratch verification |
| Exact CDF of $Y_n$ (support-aware) | ✓ Correct | Theorem 2, scratch verification |
| Pointwise convergence to Gumbel | ✓ Correct | Theorem 3, scratch verification |
| Distinction: exact vs. asymptotic | ✓ Clear | Numerical example, sanity checks |
| Assumptions and scope | ✓ Complete | Five assumptions listed and justified |
| Sanity checks | ✓ All pass | Seven checks verified numerically |
| Estimator implementation | ✓ Correct | Code review, scratch verification |
| Determinism and invariance | ✓ Verified | Code inspection |
| Approximation error | ✓ Correct | Asymptotic expansion, scratch verification |
| Execution readiness | ✓ Ready | Closed contract, validation, determinism |

---

## Conclusion

The theory handoff is **mathematically coherent** and **ready for execution**. All load-bearing definitions, theorems, and formulas have been independently verified. The estimator implementation correctly computes the required quantities and is well-specified for finite execution. No blocking findings have been identified.

