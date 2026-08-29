# Non-robust LOWESS local-linear smoothing: public method record

## Primary sources

William S. Cleveland, "Robust Locally Weighted Regression and Smoothing
Scatterplots," *Journal of the American Statistical Association* 74(368),
1979, 829-836. DOI: `10.1080/01621459.1979.10481038`.

The public statsmodels implementation is documented at
<https://www.statsmodels.org/stable/generated/statsmodels.nonparametric.smoothers_lowess.lowess.html>
and released under the BSD-3-Clause license at
<https://github.com/statsmodels/statsmodels>. The evaluator pins statsmodels
`v0.14.6`, commit `40e6a84d26ac74623c6b94b718f0987ef0351c53`.
Its source and outputs are withheld from the model workspace for this
paper-to-code task.

This operator-authored record specifies one small implementation slice. It is
not a copy of the paper or package source. Robust residual reweighting,
`delta`-based interpolation, missing-value handling, repeated predictor values,
arbitrary evaluation points, bandwidth selection, uncertainty quantification,
and asymptotic theory are outside the frozen task.

## Data and neighborhood

The input consists of paired finite observations `(x_i, y_i)`, with all `x_i`
distinct, and an integer neighborhood size `k` satisfying `4 <= k <= n`.
Sort the observations by increasing `x`; all output is aligned with that sorted
order.

At each observed target `x`, select the `k` observations with smallest ordered
pair

```math
(|x_j-x|, x_j).
```

Thus a distance tie is resolved toward the smaller predictor value. Let

```math
h_x = \max_{j\in N_k(x)} |x_j-x|.
```

For `j` in this neighborhood define the tricube weight

```math
a_j(x)=
\begin{cases}
\left(1-(|x_j-x|/h_x)^3\right)^3,& |x_j-x|<h_x,\\
0,& |x_j-x|=h_x.
\end{cases}
```

The restrictions to distinct one-dimensional predictor values and `k >= 4`
ensure that at least two distinct predictor values have positive weight.

## Local-linear fit

Normalize the weights,

```math
w_j(x)=\frac{a_j(x)}{\sum_{\ell\in N_k(x)}a_\ell(x)},
\qquad
\bar x_w=\sum_j w_j(x)x_j,
\qquad
S_w=\sum_j w_j(x)(x_j-\bar x_w)^2.
```

The fitted value is the weighted least-squares intercept evaluated at the
target:

```math
\widehat m(x)
=\sum_{j\in N_k(x)}
w_j(x)\left[1+\frac{(x-\bar x_w)(x_j-\bar x_w)}{S_w}\right]y_j.
```

Equivalently, this is the value at `x` of the line minimizing

```math
\sum_{j\in N_k(x)} a_j(x)\{y_j-\alpha-\beta(x_j-x)\}^2.
```

For distinct finite inputs in the frozen domain, `h_x`, the weight sum, and
`S_w` are positive. A submitted implementation must reject inputs outside that
domain rather than coerce, drop, or silently repair them.

With `frac=k/n`, no robust residual iterations (`it=0`), no interpolation
(`delta=0`), and fitted values requested at the observed predictor values, this
slice agrees with the pinned statsmodels LOWESS implementation up to ordinary
floating-point error on the evaluator's independently frozen parity cases.

## Properties to audit

- Permuting paired input rows does not change the sorted output.
- Adding a finite constant to every response adds it to every fitted value.
- Multiplying every response by a finite scalar multiplies every fitted value
  by that scalar.
- Replacing every predictor by `a*x+b` for finite `a>0` relabels the sorted
  predictors and leaves fitted values unchanged.
- Any exactly affine response `y_i=c+d*x_i` is reproduced at every observed
  predictor value.
- Repeated calls are deterministic and do not mutate the request.

These are finite algorithmic properties. Passing them does not establish an
optimal smoothing fraction, robustness to outliers, confidence coverage,
consistency, source-code replication, novelty, or formal proof.

## Hidden implementation authority

After the product run, evaluator-only code may compare the submitted function
with an independent implementation and with behavior from the pinned
statsmodels release. Hidden source, cases, outputs, and acceptance thresholds
never enter AgentRuntime, RAG, model tools, or revision feedback.
