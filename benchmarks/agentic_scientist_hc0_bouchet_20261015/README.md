# Bouchet HC0 Development Condition

Prospective preparation, 2026-10-15. No result is implied by this document.
This fresh condition does not modify or rescore
`../agentic_scientist_hc0_20261015/`. It reuses the exposed HC0 topic rather than
selecting a new family after failure. It is known-method reconstruction, not
blind rediscovery, a novel statistical result or an official H/S experiment.

## Question And Scope

Can the pinned v3 single-attempt research module, using Yale's managed Qwen/Pi service,
produce a reviewable HC0 argument and executable method that survives a complete
prespecified numerical study? Compare upstream's stock investigation instruction
with our statistical instruction plus portable guidance. Both use harness-owned
evaluation. This is a bundle contrast, not a prompt-only or model-size contrast.

The common evaluator owns the simulation DGP, random inputs, reference methods,
aggregation and official outputs. Thus this tests method implementation within a
complete simulation, **not autonomous simulation-design/code generation**. The
candidate also supplies a protocol-to-code explanation and result-reporting code.
Theory assessment, an application, final interpretation and the six-phase paper
workflow remain distinct unfinished evidence. No numerical score certifies them.

## Fixed Design

- One invocation of upstream `src/scripts/run.sh` and one candidate evaluation
  per arm: 90 minutes for source authoring and 30 minutes for the official
  full-study evaluator. No operator-written scientific idea or solution is
  supplied beyond the common public research brief. These are development
  resource envelopes, not scientific stopping rules or production defaults.
- Arm order: stock, then statistical. Fresh task, results and host conversation
  for each. No cross-arm candidate, outcome or memory is supplied to the author.
  Shared-service load and fixed order prevent a causal speed/efficacy claim.
- Upstream: `2b8aa39285c35aaca3b0e06dd121061ef8a2d854`; Headless:
  `93cd9b06b85f848af1308c41e018991b33907c5e`; managed Pi: observed `0.85.1`.
- Both use `bouchet/ycrc-local-think` with `YCRC_THINKING=1`, the managed
  Qwen3.8-Flash-Next route. Record returned model/usage/stop metadata. Managed
  weights revision, quantization and effective sampling are not independently
  pinned; do not relabel this as a reproducible publication model condition.
- Launch through the official YCRC wrapper on an allocated compute node. Do not
  extract service credentials or bypass its filesystem/network controls.
  The common `pi_project.sh` launch adapter selects only the current arm's root
  as YCRC's mounted project, supplies the original v3 task working directory and
  public source path as context, and explicitly selects its staged skills. It
  does not change upstream code, generated files, model credentials or evaluator.
  This host-path adaptation is shared by both arms; it is not a claim that the
  unadapted managed Pi wrapper provides v3's whole native filesystem view.
- No commercial API, external model fallback, optional Lean or hidden-family
  access. Public statistical references and the supplied task are exposed.
  No mandatory exploratory simulation or repeated evaluation of a consumed source.

The study has 12 cells: sample size 50, 200 or 1000; target slope 0 or 0.2;
homoskedastic or heteroskedastic independent Gaussian errors. Generate two
independent standard-normal predictors and an intercept. The outcome is
`beta1*x1 + x2 + sigma(x1)*epsilon`, with error variance 1 or
`(1 + 4*x1**2)/5`. Each cell has 5,000 independent datasets, master seed
2026101517, with cell/replicate keyed streams. Use the same datasets for both
arms and methods. Use two-sided normal 95% Wald intervals and tests of slope zero.

Compare candidate OLS-HC0 with conventional homoskedastic OLS inference.
Statsmodels 0.14.6 HC0 is an implementation reference, not a third scientific
method. Reference agreement uses `rtol=1e-6, atol=1e-9`, shape and finiteness
checks. No failed candidate output is replaced with reference output.
Retain all replicate statuses and conditional-on-success measures with failure
rates. Summaries include bias, RMSE, empirical SD, RMS SE, calibration ratio,
coverage, interval length and null/alternative rejection, with Monte Carlo
uncertainty. Poor coverage is a possible valid finding, not a correctness failure.
Sixty thousand datasets are inner Monte Carlo draws, not independent agent trials.
Uncertainty uses sample SD/sqrt(m) for means, binomial plug-in MCSE for proportions,
and first-order delta influences for RMSE, empirical SD, RMS SE and their paired
ratio. The evaluator documents these formulas and finite-moment assumptions.
Undefined derivatives or insufficient usable replicates yield null uncertainty.
There is no bootstrap layer, coverage gate or automatic stopping on MCSE.

## Evidence Rules

`correct.json` and `combined_score` concern computational compliance only.
The exact mathematical files remain **unassessed** until a separately recorded,
source-bound review. Any future AI review must disclose shared-model bias and is
neither expert endorsement nor proof. Assess assumptions, normalization,
residual substitution, limiting arguments and theory/code correspondence rather
than counting equations or checking a keyword list.

Preserve failed launches, missing files, timeouts and all consumed attempts.
Freeze input hashes before the first model call. No operator edits to generated
theory/code, evaluator tuning after outcomes, rerun-for-credit or cross-arm answer
transfer. A native investigation observation is not completed container-backed
drafting/final evaluation or Paper S's single-API implementation.

## Pre-call Controller Finding

Source inspection found that `main_entry.py` refuses harness-owned campaigns
without a validated incumbent. For native pre-evaluated sources,
`harness_incumbent.py` also requires sandbox-produced, correct baseline evidence.
An unimplemented reconstruction seed does not meet that condition. Supplying the
reference solution or a fabricated manifest would change or invalidate this task.
The existing single-attempt CLI does not require such an incumbent. This condition
therefore observes that real upstream module, not the complete `agsci investigate`
campaign. No second scheduler is introduced. The full controller's optimization
assumption remains a documented migration issue; successful module execution
cannot be presented as resolving it.
