# Goal

Reconstruct ordinary least squares inference using the unadjusted HC0 covariance
method associated with White (1980), Econometrica, DOI 10.2307/1912934. This is an
exposed known-method development problem. The citation identifies the method;
the original full paper is not supplied. Disclose the sources actually available
and used. This condition tests the linked theory, method, prespecified study and
interpretation, rather than blind discovery or novelty.

Develop the complete argument in `program_1/src/theory.md` or LaTeX. Define the
sampling regime, target, estimator and asymptotic objects. State sufficient
conditions, justify the covariance construction and replacement of unobserved
errors by fitted residuals, and explain the conditions of invoked limit results.
Keep the covariance of an estimator distinct from the covariance of its scaled
limiting distribution. Preserve unresolved steps. No derivation length is fixed.

Implement `run_estimator(request)` in `program_1/src/program.py`. Input keys are
`design_matrix` (n-by-p nested list including its supplied intercept column) and
`outcomes` (length n). Return `coefficients`, `covariance` and `standard_errors`
as finite arrays/lists of shapes p, p-by-p and p. Implement unadjusted HC0, not a
different finite-sample correction. Additional source files are allowed. The
unimplemented starter is an interface, not a method or evaluated baseline.

Explain the complete study in `src/study.md`, relating the aim, target, methods,
data-generating mechanisms and performance measures to the theoretical claim.
The host executes this prespecified full study after source handoff:

- Two independent standard-normal predictors and a supplied intercept;
  `y = beta1*x1 + x2 + sigma(x1)*epsilon`, with independent standard-normal epsilon.
- n in {50,200,1000}, beta1 in {0,0.2}, and error variance 1 or
  `(1+4*x1**2)/5`, making twelve cells with 5,000 independent datasets each.
- Master seed 2026101517, keyed by cell and replicate; the same datasets are
  used for both methods and comparison arms.
- Compare submitted OLS-HC0 with conventional homoskedastic OLS inference using
  two-sided normal 95% Wald intervals and tests of slope zero. Statsmodels 0.14.6
  HC0 is an implementation reference, not a third scientific method.
- Record bias, RMSE, empirical SD, RMS SE/calibration, coverage, interval length,
  rejection and failures with Monte Carlo uncertainty. Reference agreement uses
  rtol=1e-6, atol=1e-9. No coverage or power threshold defines correctness.

The evaluator owns the DGP, reference, aggregation and exact outputs. It records
all 60,000 datasets and retains unusable outputs and reference disagreements.
This is a complete prespecified numerical study, not autonomous simulation-design
or simulation-code generation. Inner datasets are not independent agent trials.
The detailed files are `replicates.jsonl`, `summaries.json` and `study.json` at the
evaluated program root. Monte Carlo uncertainty is a statistical approximation,
not a proof of the theoretical claim.

A fresh reviewer context on the same pinned model will examine the exact theory,
method and study source without evaluator outputs or the author conversation.
It can report PASS, FAIL or UNCERTAIN, with source-located findings. Missing or
uncertain review remains unassessed. The next source owner receives real findings
and may revise a new candidate through the existing campaign. AI agreement is
not mathematical certification; the assessor has not been scientifically calibrated.

After the campaign, the existing posthoc stage interprets only the declared
public summaries and selected scientific source. It writes `analysis_summary.md`
and `appendix.md`, addressing the scientific aim, actual method comparisons,
Monte Carlo uncertainty, failures, complete supporting argument and limitations.
The reporting context has no execution tools. It cannot claim new simulations,
plots, calculations, source checks or proof that did not occur. A report with
negative or inconclusive findings is valid when its evidence supports them.

Lean is optional and is not requested. An application and a full journal
manuscript are outside this development condition. Numerical compliance, internal
review dispositions and a structurally complete report do not establish full
scientific acceptance or publication efficacy.

# Constraints

Use the existing candidate/memory interfaces and preserve `program_spec.toml`.
Prepare only `program_1` before host evaluation. Do not execute the evaluator,
run extra simulations, inspect private evaluator/test source, alter acceptance
criteria, or write official result/rubric/manifest files. Ordinary granted reads
and edits are available. Report planned work as pending until actual outputs
exist. Do not inspect another arm, its candidates, results or history. Every
revision belongs to a new candidate; consumed evaluations and reviews are not
repeated, repaired or rescored.
