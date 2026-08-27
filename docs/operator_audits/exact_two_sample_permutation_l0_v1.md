# Operator Audit: Exact Two-Sample Permutation L0 v1

## Immutable run

- Task: `exact_two_sample_permutation_known_result`
- Run head: `e6fa0a87d4adf76a31e34c74d49b2a3939e8cf36`
- Run: `runs/main_worker_research_l0_exact_two_sample_permutation_20260827_v1_codex_workspace_exact_haiku`
- Product model: exact `claude-haiku-4-5-20251001`
- Runtime result: `BLOCKED`
- Terminal classification: `architect_metric_requirement_packet_validation_failed`
- Full hidden result: `0/1`
- Formalization: `not_applicable`; Formalizer did not run

The sole product draw and sole post-runtime hidden evaluation are consumed. This
audit does not rerun, resume, repair, reevaluate, rescore, or reveal hidden results
to any source-owning model.

## What worked

The Codex-shaped inner harness worked mechanically. TheoryDeveloper used one
persistent Markdown/LaTeX session for 18 model-tool turns. AlgorithmEngineer read
raw sandbox observations and revised exact source in the same source-owner session.
The independent code reviewer kept two invalid self-authored probes local, corrected
its probe, invoked the immutable estimator, and submitted a separate review. There
was no RepairAgent, second scheduler, runtime-authored source patch, or Lean lane.

The hidden harness recorded:

- Theory mechanical checks: `7/7`.
- Theory semantic judge: `8/8` and `PASS`, after `10/10` calibration.
- Algorithm checks: `11/13`; all numerical, counting, affine, and permutation checks passed.
- Empirical checks: `9/9` over 12,000 estimator invocations.
- Runtime empirical completion: failed because no metric protocol was accepted and SimulationEngineer did not run.

These automatic component results remain immutable, but the mathematical and source
passes are not trustworthy capability credit after operator inspection.

## Theory findings

1. The load-bearing tied-rank proof states that the number of assignments with weak-tail count at most `k*` is exactly `k*`. With a tie block crossing the boundary it is only at most `k*`. The independent referee explicitly derived a counterexample and the correct inequality in its Markdown report, but still called the false active proof step a minor exposition issue and submitted `ACCEPT` with zero findings. This contradicts the general referee protocol, under which a false active load-bearing step is blocking.

2. The iid extension conditions on the complete labeled values `(X_1,...,X_m,Y_1,...,Y_n)` while also treating the group assignment as uniform. Conditional on those labeled observations the assignment is fixed. The valid exchangeability statement conditions on the unlabeled pooled orbit or multiset, or states unconditional validity. The runtime referee and hidden semantic judge both missed this scope error.

3. `estimator_implementation.md` says the request is a closed object, but its displayed source checks only that `x` and `y` are present and therefore accepts extra fields. It also converts entries with `float`, which accepts booleans and numeric strings forbidden by the public contract. The referee described this source as fully validating the contract.

Disposition: `OPERATOR_INVALIDATED_ACTIVE_THEORY_AND_THEORY_REVIEW`. The hidden
semantic `PASS` is a false positive and must not be promoted to trustworthy Theory
capability.

## Scientific-code findings

The final Algorithm source repaired extra-field rejection but still applies `float`
to entries. It therefore accepts booleans and numeric strings. The model-authored
review probe tested a generic nonnumeric value but not every explicit public edge
case, then incorrectly reported that strings were rejected.

The source also implements the weak tail as `statistic >= observed_statistic -
1e-15`. A fixed absolute tolerance can include a genuinely smaller statistic at a
small response scale and can change tail counts under positive rescaling. This is
not the frozen exact comparison. The hidden harness did not cover that adversarial
scale, so its `11/13` result understates the source defect.

Finally, the Algorithm artifact contains a `run_sandbox` labeled as confirmatory and
includes outcome-aware prose about an expected failure. That code was exploratory
and never became runtime empirical evidence, but its presence shows that the shared
scientific sandbox still encourages estimator and confirmatory-simulation concerns
to mix.

Disposition: `OPERATOR_INVALIDATED_SCIENTIFIC_CODE`. No generated source is edited.

## Harness finding

MetricProtocolSourceOwner received enough context and tokens, but the canonical
fresh path required a complete Markdown-like scientific protocol to be escaped
inside the `acceptance_protocol` field of `metric_protocol.json`. Its first edit
created a 10,240-character document with invalid JSON. Later exact-literal edits
matched zero or two locations, and the final hash-bound commit returned the raw JSON
parse error after the ordinary action budget was exhausted.

This is a shared harness defect, not a permutation-test defect. Future fresh tasks
use a model-owned `metric_protocol.md`; the compact hash-bound terminal commit
carries only evaluator identity, replicate count, and short rationale. Runtime
binds the exact Markdown as the existing acceptance protocol. Frozen-rebinding
compatibility retains its JSON path. No extra model call, retry, router,
statistical rule, or content repair is
introduced.

## Evidence hashes

- Runtime manifest: `027c5d9a4f2759fc3d06c68831f3f07d2cca0fb99a420bf75ddda40e5d7ca8cd`
- Runtime result: `5f6893aa1750aeea8f7f95b522f9c614cfa7135901ba0520fe8eb75c46a49207`
- Completion summary: `fa006440e2be13a22f07cb3b528410b503a6d1dbdde0d6708b74e142fac84972`
- Failure summary: `0fc2c70e90d9cd44b4de4b01265bc8c43ae8f7d830394e1737c73979cf77c635`
- Runtime topology: `7f1b7d0ad7daf8b4fd4ebcdc6283acfe4b822ae9d56b330bb657c5ee5385c019`
- Hidden gold evaluation: `5522431b484a9b20a811ffd8d4b07032cb9c4045e9435bc677ce9b3cafadde85`
- Accepted Theory packet: `46438b08a661cce8d3010d891352e3a9629e1b3b24d5f60f2653945ea57b3a71`
- Theory document set: `34c42e65ee09989b777218da595c126129e1f6bf90b72c556fe2065770198faf`
- Referee report: `c74413faee6415183d694e2e433154dcda23f0ab32aa030783206a9f9c339fb7`
- Accepted Algorithm source: `2d9a70ebdbe7527260465e40d0d36281e4b959a556f4028d4f5d5d4d4e5a0e50`
- Hidden Theory semantic result: `b94efa7c9086ee8dac9a77efeec73190519f2a8ec0ccf055ea623e71da3ee134`
- Hidden Algorithm result: `73cc4f2807a99fd569265170dcf75a347c9f330a61be028ff9f3119730a4c8e6`
- Hidden empirical result: `11f4abe7bf50f9ee2faa8c1582122d949f9af9b6a8a3bbb4ebee911d1142ce62`

## Boundary

Task 61 remains `0/1`. Its valid empirical and workspace-loop observations remain
scoped component evidence. They do not repair the failed theory, source contract,
missing runtime simulation, missing Critic disclosure, or incomplete research loop.
All post-run changes are future-task-only shared mechanism evidence.
