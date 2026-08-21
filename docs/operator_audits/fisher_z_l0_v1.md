# Fisher Z L0 v1 Operator Audit

## Disposition

The single frozen exact-Haiku product draw is **failed, consumed, and closed**.
AgentRuntime reached a runtime-reviewed theory checkpoint and an independently
accepted generated estimator, then blocked while authoring the pre-execution
metric portfolio. The research and full hidden-gold outcomes remain `0/1`.
The task must not be rerun, repaired, resumed, or retrospectively rescored.

Run directory:
`runs/main_worker_research_l0_fisher_z_20260821_v1_codex_harness_exact_haiku`

Immutable evidence hashes:

- Runtime manifest SHA-256: `fdbb943f3a0edac7814cb81f1389b71b94873c3523b56e10b3c7385a29964b6c`
- Hidden-gold report SHA-256: `f5c6b90e2581b80e78732ecc38c4c603e31fc0305e5f9d4dd8bf32b9718897df`
- Runtime failure summary SHA-256: `b47d2e6b1f72c02a0ef7547721d82050e5e547ebe1b5bd97a634028d5b2c3eb2`
- Runtime completion summary SHA-256: `3b6e3be07cf2d9e0e588999c769d71800b71ac1c038402b4b3009824e82424cb`

Every enabled role used `claude-haiku-4-5-20251001`; no Sonnet or Opus
escalation occurred. Formalization was `not_applicable` by frozen task intent,
no formal lane ran, and Lean was not a blocker.

## Live Trajectory

TheoryDeveloper used the frozen three-document source snapshot and authored one
persistent Markdown/LaTeX document. A failed localized edit was returned as a
raw observation to that same model; it read the current document, revised it,
and explicitly committed a theory checkpoint. The isolated referee read the
document, used its own source and scratch context, and accepted all indexed
claims and review dimensions.

AlgorithmEngineer submitted one source that failed because it imported a
nonexistent `scipy.special.arctanh`. The raw sandbox traceback returned to the
same coding session. Its next complete source used a valid implementation,
executed successfully, and was accepted by the independent code-semantic
reviewer with no findings. This is direct evidence that the Codex-style
model-to-tool-to-raw-observation loop works without a RepairAgent or Architect
round trip for ordinary source errors.

The next Architect metric-authoring stage made two valid exact-Haiku structured
output calls. The final packet contained eight substantive metric rows. Six
rows repeated `required_runtime_replicates=5000`, while two invariant rows
repeated `required_runtime_replicates=300`. The runtime correctly rejected the
portfolio because one execution cohort cannot have two replicate counts. The
task ended `BLOCKED` after seven outer traces, before Simulation or Critic.

## Hidden Evaluation

The evaluator-only phase ran after AgentRuntime terminated and generated no
runtime feedback. It found:

- the generated estimator passed all 13 hidden algorithm checks;
- the generated estimator passed all 9 hidden empirical checks across 9,000
  invocations;
- the accepted theory passed 7 deterministic structure/identity checks but the
  calibrated ten-claim exact-Haiku semantic evaluation returned `FAIL`;
- the full task failed because theory was not gold validated and runtime never
  accepted a metric protocol, simulation, or unresolved-gap report.

These component results are evidence about exact accepted artifacts. They do
not override the frozen runtime completion contract or turn the task into a
`1/1` success. Hidden expected values and evaluator source remain outside the
repository, RAG, and model workspaces.

## Theory Audit

Independent operator inspection confirms that the hidden semantic failure is
not merely an evaluator transport artifact. The active theory document has
substantive mathematical defects:

- its displayed raw-moment covariance matrix omits factors of two in entries
  such as `Cov(X, X^2)` and contains dimensionally inconsistent cross-moments;
- it states that a Gaussian has excess kurtosis two, whereas Gaussian excess
  kurtosis is zero;
- it never derives the centered-moment covariance matrix on which the decisive
  delta-method quadratic form depends, then asserts the target variance;
- its nuisance-mean discussion calls an `O_p(n^-1/2)` effect absorbed at first
  order, rather than showing that sample centering differs from true centering
  by a second-order `O_p(n^-1)` term;
- the referee report additionally calls the sample correlation unbiased in
  expectation, which is not a valid finite-sample statement in general.

The runtime referee therefore produced a false acceptance despite having
document, source, and scratch tools. No formula-specific validator or post-hoc
document patch is being added. This remains a hard negative for improving the
general long-horizon theory and adversarial review loop.

## Shared Interface Defect

The metric response schema required the model to repeat one portfolio-level
execution choice inside every metric row and then required every copy to be
identical. This was redundant structured-output surface, not scientific
authority. Both model packets contained positive, feasible model-authored
counts, but row-local duplication turned one portfolio decision into an
avoidable consistency failure. Full-packet regeneration repeated the same
interface burden and supplied no useful coding-agent feedback loop.

## Shared Correction

Code commit `fbea1af3edee3de033f29dfd79e622ed213b8495` moves the existing
model-authored `required_runtime_replicates` choice to the top-level fresh
portfolio response. Runtime copies that one value unchanged into evaluator ABI
rows before hashing and independent review. It does not select a count, relax
the shared-cohort validator, infer statistics, repair model content, add an
agent, add a retry, or change frozen rebinding semantics.

The affected panel passed `129/129`, and the full suite passed `805/805` in
64.66 seconds. This is future-task mechanism evidence only. The frozen Fisher-z
draw and its theory failure remain unchanged at `0/1`.
