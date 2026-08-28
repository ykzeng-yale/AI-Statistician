# Gumbel Limit for the Maximum of Exponential Observations

## Problem Setup

Let $X_1, X_2, \ldots, X_n$ be independent and identically distributed random variables, each with the **rate-one exponential distribution**. The CDF of each $X_i$ is:
$$F(x) = \begin{cases} 0 & \text{if } x < 0 \\ 1 - e^{-x} & \text{if } x \geq 0 \end{cases}$$

The support is $[0, \infty)$.

Define the **sample maximum**:
$$M_n = \max_{1 \leq i \leq n} X_i$$

Define the **centered maximum**:
$$Y_n = M_n - \log n$$

where $\log$ denotes the natural logarithm.

## Exact Finite-Sample CDF of $M_n$

**Theorem 1 (Exact CDF of $M_n$):** For $n \geq 1$ and $x \in \mathbb{R}$,
$$P(M_n \leq x) = \begin{cases} 0 & \text{if } x < 0 \\ (1 - e^{-x})^n & \text{if } x \geq 0 \end{cases}$$

**Proof:** By independence,
$$P(M_n \leq x) = P(X_1 \leq x, X_2 \leq x, \ldots, X_n \leq x) = \prod_{i=1}^n P(X_i \leq x) = [F(x)]^n$$

For $x < 0$, $F(x) = 0$, so $P(M_n \leq x) = 0^n = 0$.

For $x \geq 0$, $F(x) = 1 - e^{-x}$, so $P(M_n \leq x) = (1 - e^{-x})^n$. $\square$

## Exact Finite-Sample CDF of $Y_n$ (Support-Aware)

**Theorem 2 (Exact CDF of $Y_n$ with Support Branch):** For $n \geq 1$ and $y \in \mathbb{R}$,
$$P(Y_n \leq y) = \begin{cases} 0 & \text{if } y < -\log n \\ \left(1 - \frac{e^{-y}}{n}\right)^n & \text{if } y \geq -\log n \end{cases}$$

**Proof:** We have $Y_n = M_n - \log n$, so $Y_n \leq y$ if and only if $M_n \leq y + \log n$.

**Case 1:** $y < -\log n$. Then $y + \log n < 0$, so by Theorem 1, $P(M_n \leq y + \log n) = 0$.

**Case 2:** $y \geq -\log n$. Then $y + \log n \geq 0$, so by Theorem 1,
$$P(Y_n \leq y) = P(M_n \leq y + \log n) = (1 - e^{-(y + \log n)})^n = \left(1 - \frac{e^{-y}}{n}\right)^n$$

$\square$

**Remark:** The support of $Y_n$ is $[-\log n, \infty)$. The lower bound arises because $M_n \geq 0$ (the support of the exponential), so $Y_n = M_n - \log n \geq -\log n$.

## Pointwise Convergence to the Gumbel Distribution

**Definition (Standard Gumbel CDF):** The standard Gumbel distribution has CDF:
$$G(y) = e^{-e^{-y}}, \quad y \in \mathbb{R}$$

**Theorem 3 (Pointwise Convergence):** For every fixed $y \in \mathbb{R}$,
$$\lim_{n \to \infty} P(Y_n \leq y) = e^{-e^{-y}}$$

**Proof:** Fix $y \in \mathbb{R}$. For sufficiently large $n$, we have $y \geq -\log n$ (since $-\log n \to -\infty$ as $n \to \infty$). Thus, for large $n$,
$$P(Y_n \leq y) = \left(1 - \frac{e^{-y}}{n}\right)^n$$

Let $a_n = -\frac{e^{-y}}{n}$. Then:
$$\left(1 - \frac{e^{-y}}{n}\right)^n = (1 + a_n)^n$$

By the standard limit,
$$\lim_{n \to \infty} \left(1 + \frac{c}{n}\right)^n = e^c$$

we have:
$$\lim_{n \to \infty} \left(1 - \frac{e^{-y}}{n}\right)^n = e^{-e^{-y}}$$

$\square$

## Distinction: Exact Finite-$n$ Law vs. Asymptotic Approximation

For any fixed $n$ and $y \geq -\log n$:
- **Exact finite-$n$ CDF:** $P(Y_n \leq y) = \left(1 - \frac{e^{-y}}{n}\right)^n$
- **Gumbel approximation:** $G(y) = e^{-e^{-y}}$

These are **not equal** for finite $n$. The approximation improves as $n$ increases, but equality holds only in the limit $n \to \infty$.

**Example:** For $n = 10$ and $y = 0$:
- Exact: $\left(1 - \frac{1}{10}\right)^{10} = (0.9)^{10} \approx 0.3487$
- Gumbel: $e^{-e^0} = e^{-1} \approx 0.3679$

The error is approximately $0.0192$.

## Key Assumptions and Scope

1. **Independence:** $X_1, \ldots, X_n$ are mutually independent.
2. **Identical distribution:** Each $X_i$ follows the rate-one exponential distribution with CDF $F(x) = 1 - e^{-x}$ for $x \geq 0$.
3. **Support:** The exponential support is $[0, \infty)$, which constrains $M_n \geq 0$ and thus $Y_n \geq -\log n$.
4. **Normalization:** The centering is by $\log n$ (not $n$, $\sqrt{n}$, or other scales).
5. **Fixed-$y$ regime:** Convergence is pointwise for each fixed $y \in \mathbb{R}$, not uniform over all $y$.

## Relationship to Extreme Value Theory

This result is a special case of the **Fisher–Tippett–Gnedenko theorem** for maxima. The exponential distribution belongs to the **domain of attraction of the Gumbel distribution** with the normalization $a_n = \log n$ and $b_n = 0$ (i.e., $M_n$ is centered by $\log n$ and not shifted).

The general theorem states that if $X_1, \ldots, X_n$ are i.i.d. from a distribution $F$ with a right-unbounded support and a regularly varying tail, then the normalized maximum converges in distribution to the Gumbel distribution. The exponential distribution satisfies these conditions.

## Finite-Sample Approximation Error

For $y \geq -\log n$, the approximation error is:
$$\Delta_n(y) = \left(1 - \frac{e^{-y}}{n}\right)^n - e^{-e^{-y}}$$

Using the expansion $(1 + u)^n = e^{n \log(1+u)} \approx e^{nu - \frac{n u^2}{2} + O(n u^3)}$ for small $u$:

With $u = -\frac{e^{-y}}{n}$:
$$n \log\left(1 - \frac{e^{-y}}{n}\right) = n \left(-\frac{e^{-y}}{n} - \frac{e^{-2y}}{2n^2} + O(n^{-3})\right) = -e^{-y} - \frac{e^{-2y}}{2n} + O(n^{-2})$$

Thus:
$$\left(1 - \frac{e^{-y}}{n}\right)^n = e^{-e^{-y}} \cdot e^{-\frac{e^{-2y}}{2n} + O(n^{-2})} \approx e^{-e^{-y}} \left(1 - \frac{e^{-2y}}{2n} + O(n^{-2})\right)$$

The leading error term is $O(n^{-1})$, uniform in $y$ over compact intervals.

## Summary of Derivations

| Object | Formula | Domain |
|--------|---------|--------|
| $F(x)$ (exponential CDF) | $1 - e^{-x}$ | $x \geq 0$ |
| $P(M_n \leq x)$ | $(1 - e^{-x})^n$ | $x \geq 0$ |
| $P(Y_n \leq y)$ (exact) | $\left(1 - \frac{e^{-y}}{n}\right)^n$ | $y \geq -\log n$ |
| $G(y)$ (Gumbel CDF) | $e^{-e^{-y}}$ | $y \in \mathbb{R}$ |
| Limit | $\lim_{n \to \infty} P(Y_n \leq y) = G(y)$ | Fixed $y \in \mathbb{R}$ |
