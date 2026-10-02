# Fixed-K Segmentation Reference

Evaluator preparation only. No candidate call, activated study, full-task gold,
novel statistical result or Lean proof. This disclosed development inspection
cannot itself be a sealed test set. It is not product context or a repair recipe.

## Source Identity

Truong, Oudre and Vayatis, *Selective review of offline change point detection
methods*, Signal Processing 167:107299 (2020),
[DOI](https://doi.org/10.1016/j.sigpro.2019.107299),
[arXiv v3](https://arxiv.org/abs/1801.00718v3). This is not a JMLR paper.
Inspected portions are the objective, quadratic cost and dynamic-programming
sections, not an expert audit of the entire review. The pinned arXiv PDF hash is
in `sources.json`; other author-hosted PDF editions are not interchangeable.

The review distinguishes fixed change count from penalized unknown-count search.
Its cost (C2), recurrence (21) and Algorithm 1 inform the reference scope.
Algorithm 1 uses K for regimes, unlike the earlier change-count notation.
Below, K counts internal changes and s counts segments; no source is edited to
resolve that notation. The author implementations are separately pinned
post-publication versions, not a recovered publication-time implementation.

## Independent Mathematical Scope

Let T and d be positive integers, with observed finite vectors
\(\mathbf y_1,\ldots,\mathbf y_T\in\mathbb R^d\).
For integers \(0\le a<b\le T\), define

\[
\bar{\mathbf y}_{a:b}=\frac{1}{b-a}\sum_{t=a+1}^{b}\mathbf y_t,
\qquad
c(a,b)=\sum_{t=a+1}^{b}\|\mathbf y_t-\bar{\mathbf y}_{a:b}\|_2^2.
\]

For any \(\boldsymbol\theta\in\mathbb R^d\), direct algebra gives

\[
\begin{aligned}
\sum_{t=a+1}^{b}\|\mathbf y_t-\boldsymbol\theta\|_2^2
&=\sum_{t=a+1}^{b}\|\mathbf y_t-\bar{\mathbf y}_{a:b}
                 +\bar{\mathbf y}_{a:b}-\boldsymbol\theta\|_2^2
&&\text{(insert the same mean)}\\
&=\sum_{t=a+1}^{b}\left(\|\mathbf y_t-\bar{\mathbf y}_{a:b}\|_2^2
 +2\langle\mathbf y_t-\bar{\mathbf y}_{a:b},\bar{\mathbf y}_{a:b}-\boldsymbol\theta\rangle
 +\|\bar{\mathbf y}_{a:b}-\boldsymbol\theta\|_2^2\right)
&&\text{(expand each norm)}\\
&=\sum_{t=a+1}^{b}\|\mathbf y_t-\bar{\mathbf y}_{a:b}\|_2^2
 +2\left\langle\sum_{t=a+1}^{b}(\mathbf y_t-\bar{\mathbf y}_{a:b}),
               \bar{\mathbf y}_{a:b}-\boldsymbol\theta\right\rangle
 +(b-a)\|\bar{\mathbf y}_{a:b}-\boldsymbol\theta\|_2^2
&&\text{(linearity of the finite sum)}\\
&=\sum_{t=a+1}^{b}\|\mathbf y_t-\bar{\mathbf y}_{a:b}\|_2^2
 +(b-a)\|\bar{\mathbf y}_{a:b}-\boldsymbol\theta\|_2^2
&&\text{(centered vectors sum to zero)}\\
&\ge\sum_{t=a+1}^{b}\|\mathbf y_t-\bar{\mathbf y}_{a:b}\|_2^2
&&\text{(nonnegative squared norm).}
\end{aligned}
\]

Equality holds at the segment mean, uniquely since b-a is positive. This is
a deterministic least-squares statement; it requires no Gaussian or iid model.

Fix minimum segment length m>=1 and grid spacing g>=1. Let
\(\mathcal P_{s,b}\) contain tuples
\(0=t_0<t_1<\cdots<t_s=b\), with s segments, each length at least m,
and every internal endpoint a positive multiple of g. The final endpoint need
not be a grid multiple. Define

\[
F_s(b)=\min_{\mathbf t\in\mathcal P_{s,b}}
         \sum_{j=1}^{s}c(t_{j-1},t_j),
\]

with the minimum of an empty set equal to positive infinity. For s>=2, let
\(\mathcal U_{s,b}\) be the grid endpoints u<=b-m for which
\(\mathcal P_{s-1,u}\) is nonempty. Partitioning by the last internal endpoint,

\[
\begin{aligned}
F_s(b)
&=\min_{u\in\mathcal U_{s,b}}
   \min_{\mathbf t\in\mathcal P_{s-1,u}}
     \left\{\sum_{j=1}^{s-1}c(t_{j-1},t_j)+c(u,b)\right\}
&&\text{(bijection with prefix and last segment)}\\
&=\min_{u\in\mathcal U_{s,b}}
     \left\{\min_{\mathbf t\in\mathcal P_{s-1,u}}
        \sum_{j=1}^{s-1}c(t_{j-1},t_j)+c(u,b)\right\}
&&\text{(last cost does not depend on the prefix)}\\
&=\min_{u\in\mathcal U_{s,b}}\{F_{s-1}(u)+c(u,b)\}
&&\text{(definition of the prefix optimum).}
\end{aligned}
\]

The base is F_1(b)=c(0,b) for b>=m and infinity otherwise. Induction in s,
with an attaining split at each nonempty finite minimum, gives a globally
minimizing admissible segmentation. The desired fixed-K objective is F_{K+1}(T).
Ties need not have one specified breakpoint tuple. A restricted-grid optimum
need not be the full-grid optimum. Neither result proves consistency, identifies
the unknown K, or guarantees recovery of physical change locations. Complexity
also depends on segment-cost evaluation and preprocessing; no universal running
time bound is inferred from these finite inspections.

## Numerical Inspection

`qualify_ruptures.py` enumerates all admissible partitions independently of the
author DP and computes direct squared deviations with `fractions.Fraction` on
integer inputs. It does not invoke the author cost to choose the oracle minimum.
The returned partition must attain the *exact rational* minimum, not merely be
close to it. Floating tolerance applies only to the separate CostL2 value check.
Inputs cover 72 small univariate/multivariate constant, step, alternating and
fixed-seed integer-noise datasets. Configuration ranges and every result are
retained. These are selected development cases, not a population success rate,
stress test of extreme floating values or a randomized study sample.

The original 1.0.6 tests passed 484/484, but exhaustive inspection found 708
feasible failures and 165 returned nonoptima among 4,608 configurations.
For y=(0,0,0,3,3,3,3), K=1, m=2, g=1, the optimum is zero at (3,7),
while the source returns (4,7) with objective 27/4. Its left-prefix feasibility
check uses the current change count instead of the count of the recursive
prefix. This source version is not qualified as a trusted optimizer reference.
No operator patch was applied. Initial inspection stopped on an uncaught
invariance failure; later inspection preserves failures and has the same input
and case hashes. These are reference inspections, not consumed candidate scores.

Separately pinned 1.1.10 passed 585 author tests and all inspected configurations:
2,640 exact minima and 1,968 rejected infeasible configurations, plus 2,664
segment-cost and 144 translation/scaling checks. Its minimum supported CostL2
segment is one instead of two. Thus the two full configuration totals do not
describe identical feasible sets when requested min_size=1. This later source
can support a narrowly scoped prospective numerical reference, not exact
historical replication, a full-paper theory verdict or independent full-task gold.

Future theory acceptance needs an independently reviewed rubric, source fidelity
and explicit assumptions; numerical tests cannot accept a derivation. A future
agent must produce its own theory/source and must not see hidden evaluator
outputs. Task families, exclusions, data, source horizon, confirmation, comparison
arms and resources remain unfrozen. Neither publication study is activated.
