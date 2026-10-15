# Goal

Reconstruct the heteroskedasticity-consistent covariance method for ordinary
least squares (White, 1980, Econometrica, DOI 10.2307/1912934). This is a public
known-method development task, not a request to discover a new result.

Develop the argument in `program_1/src/theory.md` or LaTeX: define the sampling
regime, target, estimator, assumptions and asymptotic objects; justify the
covariance construction and the passage from unobserved errors to residuals.
Distinguish covariance of the estimator from covariance of its scaled limiting
distribution. State the conditions of each invoked result and unresolved gaps.
There is no fixed derivation length. Numeric agreement is not a proof.

Implement `run_estimator(request)` in `program_1/src/program.py`. Input keys are
`design_matrix` (an n-by-p nested list including its supplied intercept column)
and `outcomes` (length n). Return `coefficients`, `covariance`, and
`standard_errors` as finite arrays/lists of shapes p, p-by-p and p. The intended
method is OLS with the unadjusted HC0 covariance, not another finite-sample variant.
Additional source files are allowed. The seed is unimplemented; do not evaluate it.

Explain the complete study in `src/study.md`. Supply `src/report.py` that reads
the eventual official replicate/summary files and produces tables or figures
without inventing unavailable observations. Before execution, label conclusions
as pending. This task does not require a preliminary small simulation.

The host, not the author, executes the fixed full simulation after handoff:
two independent standard-normal predictors plus an intercept;
`y = beta1*x1 + x2 + sigma(x1)*epsilon` with independent standard-normal epsilon;
n in {50,200,1000}, beta1 in {0,0.2}, and error variance 1 or
`(1+4*x1**2)/5`. There are 5,000 independent replicates in each of 12 cells.
Master seed 2026101517 is keyed by cell and replicate, shared across methods
and comparison arms. Compare the submitted HC0 method with conventional OLS
inference using identical normal 95% Wald intervals/tests. Statsmodels 0.14.6
HC0 is the numerical implementation reference, not a distinct competing method.
Record bias, RMSE, empirical SD, RMS SE/calibration, coverage, interval length,
null rejection, alternative rejection and failures with Monte Carlo uncertainty.
Reference agreement tolerance is rtol=1e-6, atol=1e-9.
Official detailed outputs are `replicates.jsonl`, `summaries.json` and `study.json`
in the evaluated program directory. The evaluator uses sample-mean MCSE,
binomial MCSE for proportions and paired plug-in delta MCSE for nonlinear
calibration measures; these are Monte Carlo approximations, not proof evidence.

The evaluator's score measures completed numerical agreement, not theory,
coverage success, independent review, novelty or publication readiness.
An honest poor-coverage result is not a failed mathematical proof. Theory remains
unassessed in this development observation. Lean is not required.

# Constraints

Use the existing v3 candidate/memory interfaces and preserve program_spec.toml.
Prepare only program_1 for the host-owned evaluator. Do not run the official
evaluator, generate official metrics/correct/rubric artifacts, change acceptance
rules, or execute additional simulations. Normal read/edit operations and public
source lookup are permitted. Do not inspect other arms or unrelated projects.
Retain explicit source references and gaps; never claim a planned study ran.
