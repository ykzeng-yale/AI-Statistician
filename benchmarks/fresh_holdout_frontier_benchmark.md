# Fresh Holdout Frontier Benchmark

Created: 2026-06-01

This benchmark is intentionally separate from
`docs/frontier_stat_theory_benchmark.md`. It is a small fresh-holdout pilot for
checking whether the AI Statistician pipeline generalizes beyond the curated
60-question frontier corpus. The system under test should receive only each
generic holdout title, open question, and assumptions-to-recover. Paper identity,
source URL, and expected theoretical results are grading metadata.

## Scope and Sources

- Journal pool: Journal of the American Statistical Association and Biometrika.
- Date window: 2025-07-01 through 2026-05-31.
- Source rule: recent public journal pages with enough abstract or summary
  metadata to define a theory-target question.
- Holdout rule: these entries are not retrieval cards, proof-bank obligations,
  or training-export examples. They are audit targets only.
- Caveat: this is a pilot holdout, not a full manually reviewed journal
  benchmark. Use the source links for gold-standard paper verification before
  making scientific claims.

## Holdout Causal, Design, Conformal, Geometry, and Stochastic Process Problems

Topic test: Can the system classify and scope fresh frontier theory targets while
keeping paper identity and expected results out of the prompt?

### fresh_holdout_conformal_01: Holdout conformal model-selection inference

- Source: JASA, 2026-05-01 accepted author version; DOI: [10.1080/01621459.2026.2663588](https://doi.org/10.1080/01621459.2026.2663588)
- Open question: How can prediction sets remain valid after a data-dependent procedure selects the model or conformity score that appears most efficient?
- Assumptions to recover: exchangeable calibration data, candidate model or score family, data-dependent selection based on interval width or efficiency, marginal prediction coverage target.
- Expected theoretical results:
  - State a post-selection conformal validity target that accounts for model or score selection.
  - Develop a corrected or selection-aware conformal procedure with finite-sample marginal coverage.
  - Quantify efficiency tradeoffs relative to naive selection by interval width.

### fresh_holdout_design_01: Holdout incomplete-block randomization inference

- Source: Biometrika, 2026-02-19; DOI: [10.1093/biomet/asag013](https://doi.org/10.1093/biomet/asag013)
- Open question: In a randomized experiment with finite potential outcomes, how can finite-population causal inference be carried out when blocks contain many possible treatments but only an incomplete subset can be assigned within each block?
- Assumptions to recover: finite potential-outcome schedule, randomized experiment assignment mechanism, incomplete or balanced incomplete block randomization, many treatment arms, design-based estimators and conservative variance.
- Expected theoretical results:
  - Define design-based estimators for incomplete block and balanced incomplete block designs.
  - Prove finite-population unbiasedness or consistency properties under the randomization design.
  - Derive conservative variance estimators and a finite-population central limit theorem.

### fresh_holdout_missing_outcomes_01: Holdout design-based missing-outcomes inference

- Source: JASA, 2025-08-12; DOI: [10.1080/01621459.2025.2516204](https://doi.org/10.1080/01621459.2025.2516204)
- Open question: In a randomized experiment with missing outcomes, how can inference remain design-based when missingness may depend on treatment assignment or covariates?
- Assumptions to recover: finite population potential outcomes, randomized experiment assignment mechanism, missing outcome indicators, design-based estimand, inverse-probability or imputation-assisted adjustment.
- Expected theoretical results:
  - Define the target treatment-effect estimand under missing outcomes in the finite-population design.
  - Construct design-based estimators using missingness adjustment or imputation.
  - Prove unbiasedness, conservativeness, or asymptotic validity under stated randomization and missingness assumptions.

### fresh_holdout_selective_fdr_01: Holdout weighted conformal selective inference

- Source: Biometrika, 2026 issue; DOI: [10.1093/biomet/asaf066](https://doi.org/10.1093/biomet/asaf066)
- Open question: How can one build model-free selective inference procedures under covariate shift while controlling false discoveries?
- Assumptions to recover: source and target covariate distributions, covariate-shift weights, conformal p-values, selected hypotheses, independent valid null p-values, finite-sample FDR target.
- Expected theoretical results:
  - Construct weighted conformal p-values valid under covariate shift.
  - Prove finite-sample FDR control for a selective inference rule using those p-values.
  - Clarify assumptions on weight estimation, exchangeability, and target-population validity.

### fresh_holdout_manifold_01: Holdout Gaussian-process manifold reconstruction

- Source: Biometrika, 2026-02-19; DOI: [10.1093/biomet/asag011](https://doi.org/10.1093/biomet/asag011)
- Open question: How can Gaussian-process methods reconstruct a nonlinear manifold while providing prediction uncertainty and consistency guarantees for the recovered low-dimensional structure?
- Assumptions to recover: data sampled near lower-dimensional Riemannian manifolds, posterior distributions on Riemannian manifolds, local covariance information, Gaussian-process regression prior or smoother, manifold reconstruction target.
- Expected theoretical results:
  - Define a manifold reconstruction target based on local covariance or tangent information.
  - Reduce global manifold reconstruction to a collection of local regression problems.
  - Prove theoretical guarantees for interpolation or uncertainty around the estimated manifold.

### fresh_holdout_toroidal_diffusion_01: Holdout toroidal diffusion likelihood theory

- Source: Biometrika, 2025-07-09; DOI: [10.1093/biomet/asaf050](https://doi.org/10.1093/biomet/asaf050)
- Open question: How can exact likelihood inference be developed for continuous-time angular diffusion data on a torus with a prespecified stationary distribution?
- Assumptions to recover: toroidal state space, reversible diffusion process, explicit transition density, stationary distribution on the torus, one-sample or multi-group likelihood inference.
- Expected theoretical results:
  - Construct toroidal diffusion processes with explicit transition densities and target stationary laws.
  - Prove reversibility and exact likelihood validity for observed angular trajectories.
  - Derive asymptotic likelihood theory and tests for one-sample or multi-group hypotheses.
