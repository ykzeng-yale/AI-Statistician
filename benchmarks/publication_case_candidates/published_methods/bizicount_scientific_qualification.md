# bizicount Scientific Qualification

2026-10-15. Operator source review for Q04/Q05; not an agent result, independently
accepted mathematical assessment, frozen rubric or activated study. The family
remains unconsumed and unqualified. Keep this assessment material outside author
input capsules; actual access separation still needs Q06 qualification. Do not
change the existing public question or use these findings as author hints.

## Sources And Scope

The [2024 journal paper](https://www.jstatsoft.org/article/view/v109i01), package
1.3.3 and replication archive retain their original input identities:

| Asset | SHA-256 |
| --- | --- |
| Journal PDF | `7d81e2488a318d737e5ab7eca382aadfd28c289ca8f92cca39358091d37a9ab2` |
| Package archive | `bb61a86f3f44746d337a45c3393cdaf4fd40f28ddc545c157203d6809897d838` |
| Replication archive | `ff40055cdbc34a77737cfd1b7713c8ffce6c70b2dab2674d6b5a4edb43383384` |

This pass inspected selected passages in Sections 2.2 and 5.3 and Appendix A,
the complete `empirical_replication.R`, and the relevant package likelihood,
copula, bounding and inference code. Original PDF pages 21 and 37 were rendered
and visually checked. It is not a full proof or package audit. Original reference
runs and their numerical discrepancies were not rerun or rescored.

The exact code members used below are:

- `R/bizicount.R`: `e16638a86aba5273431701a45e428b767fbe773ffc339c03819af226f0653d62`.
- `R/copula_dist_fns.R`: `c216d91c6706415198ee486d97c67ce420e44cd7b90d89ead6b0e79e87a420fc`.
- `R/bounds.R`: `09ba5cceea6df6cb42228534394dda026184b0c7f77cd4755d3ccae0691c4d32`.

## Numerical Objective Is Not The Exact Probability Model

**Source observation.** Appendix A describes CDF bounds and a positive PMF
floor. Package `cop.pmf` returns a four-CDF difference; it does not itself apply
its `pmf.min` argument. `cop.lik` then passes that difference to `bound`, whose
default also applies an upper cap. No normalization term follows before taking
logs (`R/copula_dist_fns.R:41--77`, `R/bizicount.R:284--300`, `R/bounds.R:14--24`).

**Analytic consequence.** Fix covariates and an admissible parameter vector
`theta`. Let $\widetilde p_\theta(y_1,y_2)$ denote the finite real-valued
four-CDF difference, including the source CDF modifications. Restrict this
argument to the unweighted fits used in the declared replication and to
$\epsilon=\mathtt{pmf.min}\in(0,1/2)$. The supplied default is $10^{-7}$.
Whenever all terms are defined, the implemented per-observation quantity is

\[
q_{\theta,\epsilon}(y_1,y_2)
=\min\{1-\epsilon,\max\{\epsilon,\widetilde p_\theta(y_1,y_2)\}\}.
\]

It satisfies $q_{\theta,\epsilon}(y_1,y_2)\geq\epsilon$. For every nonnegative
integer $M$, therefore,

\[
\begin{aligned}
\sum_{y_1=0}^{M}\sum_{y_2=0}^{M}q_{\theta,\epsilon}(y_1,y_2)
&\geq\sum_{y_1=0}^{M}\sum_{y_2=0}^{M}\epsilon
&&\text{(pointwise lower bound)}\\
&=\sum_{y_1=0}^{M}(M+1)\epsilon
&&\text{(sum over the second coordinate)}\\
&=(M+1)^2\epsilon
&&\text{(sum over the first coordinate)}.
\end{aligned}
\]

The last expression diverges as $M$ increases. Thus this clipped extension is
not a normalized PMF on the unbounded count grid, and the finite-sample objective
$-\sum_{i=1}^{n}\log q_{\theta,\epsilon}(Y_{i1},Y_{i2})$ cannot be identified
with the exact count-model negative log likelihood without further argument.
This elementary normalization check is operator analysis, not a new statistical
theorem, numerical experiment or accepted agent derivation.

This does **not** prove that clipping affected the recorded fits, changed their
maxima, caused the SE discrepancy, or invalidates every use of the estimator.
Locally, if every CDF modification and both PMF caps are inactive, objective
agreement is possible. That inactivity was not established for the original
fits. No claim about their realized bias or convergence follows here.
Do not add a numeric sensitivity run to manufacture a proof, repair the source,
or silently set floors to zero: the inspected `bound` rejects `low <= 0`.

## Inference Needs Its Own Authority

**Unresolved calibration.** The application uses a two-degree-of-freedom
chi-squared reference for the ZIP versus ZINB likelihood-ratio statistic
(paper p. 21; `empirical_replication.R`). For each margin, write the negative
binomial inverse-dispersion parameter as $\theta_j>0$ and dispersion as
$\alpha_j=1/\theta_j\geq0$. The Poisson null is the limit $\alpha_j=0$.
Testing both Poisson margins therefore places the null on the boundary of the
two-dispersion parameter space, not at its interior.

A parameter-count difference alone does not establish the ordinary Wilks
reference distribution. [Self and Liang (1987)](https://pages.stat.wisc.edu/~larget/Stat998/Fall2015/Self-Liang-1987.pdf)
describe boundary-dependent likelihood-ratio limits; the inspected abstract is
background, not verification of every condition for this copula model. The exact
null law, dependence of its weights on nuisance information, numerical-objective
effects and this application's calibration remain unestablished here. Do not
invent a universal chi-squared mixture or a corrected p-value. Reproducing the
printed calculation can establish software fidelity, not calibrated inference.

## Assessment Consequences

| Obligation | Evidence that can support it | Invalid shortcut |
| --- | --- | --- |
| Joint probability model | Correct marginal definitions and discrete rectangle argument; dependence family, support and relevant identifiability conditions | Treating a copula choice as no joint-distribution assumption, or importing a continuous-CDF transform argument unchanged to counts |
| Numerical implementation | Exact source/settings and the actual objective, with numerical modifications distinguished from the mathematical target | Certifying exact MLE theory from an optimizer return or rounded coefficient agreement |
| Inference | Conditions for the specific reported variance/test, with a reasoned uncertainty or limitation when those conditions are not established | Requiring agreement with the paper's p-value as proof of validity |
| Simulation | Complete requested-scope accounting and separate conditional/unconditional summaries, as already specified in the assessment draft | Treating absent fits as successes, or interpreting conditional performance as unconditional calibration |
| Application | Original response/model identities, computational correspondence, observational interpretation and justified diagnostics | Turning a better likelihood, residual-test nonrejection or reproduction into a causal conclusion |

The [existing BIC/SE/failure record](../../publication_reference_qualification_20261002/README.md#bizicount-reference-execution)
is unchanged. Its unresolved discrepancies are not replaced by this analysis.
A scientifically correct submission may faithfully reproduce a convention while
explaining why its inferential interpretation remains unsupported. Conversely,
flagging one issue does not fulfill the requested derivation, complete simulation,
reusable implementation and application. No new points, mandatory finding count,
numeric tolerance, automatic theorem verdict or reduced task is defined here.

Before activation, the independent assessor must qualify the exact obligations,
valid alternatives and numerical endpoints under the common arm-blind process.
Record unresolved model/source differences rather than force a false gold answer.
The [journal's code policy](https://www.jstatsoft.org/about/submissions) states a
GPL or GPL-compatible requirement, but does not identify the exact replication
archive license or grant underlying GTD/PRIO data rights. Those remain separate.
Q04/Q05/Q06/Q07 and the full-task qualification remain open.

A separate model-assisted, read-only review found no actionable error in the
source interpretation, normalization argument, boundary qualification or task
scope above; it rechecked the archive/member hashes. That reviewer did not
independently verify the replication's unit-weight setting or application
calculation. This review is operator QA, not the appointed mathematical assessor
or an additional scientific result.
