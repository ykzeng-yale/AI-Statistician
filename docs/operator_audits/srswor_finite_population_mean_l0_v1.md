# SRSWOR finite-population mean L0 v1 operator audit

Date: 2026-08-26

## Immutable evaluation identity

- Task: `srswor_finite_population_mean_known_result`
- Frozen visible-task commit: `247a439013d6e317c5fc6e724b6354f57c6c7f72`
- Frozen activation-identity/runtime commit:
  `791fe29880da501da0ce696c789b7a3497d1ffe2`
- Run: `runs/main_worker_research_l0_srswor_mean_20260826_v1_exact_haiku`
- Runtime model: exact `claude-haiku-4-5-20251001` for all seven enabled
  LLM agents; no Sonnet or Opus call
- Runtime result: `ACCEPTED`, canonical `research_eval` complete and mode
  conformant
- Frozen hidden result: `0/1`
- Operator disposition: `INVALIDATED`
- Aggregate trustworthy score after consumption: `4/47`

This task used exactly one product-model draw and one post-runtime hidden
evaluation. The artifacts are immutable. It must never be resumed, rerun,
repaired, hidden-evaluated again, rescored, or resampled.

## Dimension result

| Dimension | Frozen result | Authority |
| --- | --- | --- |
| Theory | automated pass | hidden mechanical `7/7` plus calibrated semantic `10/10 SATISFIED` |
| Scientific code | fail | hidden public-contract checks `11/12` |
| Empirical | pass | hidden `6/6` over 96,000 estimator invocations |
| Formal | not applicable | task intent |
| Full task | fail | required scientific-code dimension failed |

The visible runtime executed both model-authored Python algorithm and Simulation
workspaces and reached Critic acceptance in 17 outer traces. This is useful
component evidence, but runtime acceptance is not hidden-gold correctness.

## Scientific-code failure

The public contract requires invalid sample values to be rejected without silent
coercion. The exact accepted estimator validates each value with `float(val)` and
then constructs `sample_array = [float(v) ...]`. It therefore accepts a numeric
string even though the model-owned implementation document says "No silent
coercion or repair of invalid inputs." The frozen hidden evaluator correctly
rejected this behavior. This is a model-authored source defect, not a sandbox or
runtime parser defect.

The generated-code semantic reviewer did not provide contrary execution evidence.
It authored two probes:

1. The first was rejected because it did not define `run_sandbox`.
2. The second failed because its `run_sandbox` did not accept the injected
   `estimators` argument; the bound estimator was never invoked.

The same reviewer then submitted `ACCEPT`. Future-task commit
`3b28df58d3ac03af48d7f855ba912725d3324aa3` changes only this shared harness
behavior: once a reviewer elects to probe, `ACCEPT` requires at least one
successful probe that actually invoked the exact hash-bound estimator. Raw probe
or terminal-validation errors return to the same reviewer session so the model can
repair its own probe or submit a non-accepting judgment. Runtime does not add an
SRSWOR case, infer a verdict from diagnostic values, or edit generated source.

## Mathematical operator findings

The final main identities for inclusion probabilities, unbiased sample mean,
finite-population variance, unbiased sample variance for `n >= 2`, and the plug-in
variance estimator are correct. The persistent Markdown/LaTeX workspace and
scratch feedback also recovered from an earlier incorrect claim that sample
variance was biased. That recovery is real long-horizon TheoryDeveloper evidence.

The accepted authoritative documents still contain required precision defects:

- The expanded binomial-coefficient equality in the second-order inclusion
  derivation has an extra factorial/denominator factor. Its initial combinatorial
  ratio and final `n(n-1)/(N(N-1))` result are correct, but the displayed equality
  chain between them is false.
- The constant-population section says `s^2 = 0` "for any sample" while displaying
  division by `n-1`; it does not preserve the already-declared singleton
  `n = 1` undefined case.
- The with-replacement comparison says the finite-population correction tends to
  one merely for large `N`. It also needs a vanishing sampling fraction
  `n/N -> 0`; large `N` with a fixed nonzero sampling fraction is insufficient.
- The implementation document claims no silent coercion while the exact source
  performs it.

The isolated theory referee eventually accepted every task-derived component and
the hidden semantic judge accepted all ten rubric claims. Those automated passes
are preserved, but they do not override direct operator-visible contradictions.

## Metric-protocol findings

The model-authored protocol contains wrong explicit constants:

- For population `1,...,10`, the denominator-`N-1` variance is
  `9.166666...`, not `8.25`, and the `N=10,n=3` design variance is
  `2.138888...`, not `1.925`.
- For population `1^2,...,10^2`, the mean is `38.5`, not `385`; the displayed
  variance and design-variance constants derived from `385` are consequently
  wrong.
- The required sample-mean unbiasedness check uses a constant population. Every
  sample mean is then exactly the population mean, so the check is vacuous for
  distinguishing many incorrect mean implementations.

The generated Simulation source recomputed its reference values from arrays, so
its executed metrics could pass despite the false constants in comments and
protocol prose. The hidden empirical evaluator used multiple nonconstant fixed
populations and supplied stronger evidence. This is evidence that a one-shot
structured metric reviewer can still fail despite an explicit arithmetic and
non-vacuity prompt; adding another synonymous checklist is not justified.

## Harness conclusion

The Codex-shaped lesson is narrow and general: a specialist that chooses an
environment action must receive the exact raw observation in the same session and
must resolve its own failed action before claiming success. Scientific content
stays model-owned. The harness should manage tool identity, source hashes,
sandboxing, permissions, budgets, and evidence boundaries; it should not encode
finite-population formulas, patch model output, add a repair agent, or introduce a
second scheduler.

The task remains frozen `0/1` even after the future-task harness change.

Future-task regression evidence: generated-code semantic-review tests passed
`29/29`, the complete repository passed `914/914` in 71.31 seconds, compile-all,
JSON, and diff checks passed, and production Python remains 149,999 lines. None of
this changes the consumed task's scientific score.
