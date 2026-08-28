# Operator audit: Fisher exact greater-tail L0 v1

## Immutable draw boundary

Task `fisher_exact_greater_fixed_margins_known_result` consumed exactly one
fresh product draw and exactly one post-runtime hidden evaluation from product
code head `6eb66dc973bc0a6fa2f67ac26d64df5cc993a8ec`. All seven enabled
roles used exact `claude-haiku-4-5-20251001`; no Sonnet or Opus call occurred.

The immutable run is:

`runs/main_worker_research_l0_fisher_exact_greater_20260827_v1_codex_single_loop_exact_haiku`

AgentRuntime returned `BLOCKED` after five outer iterations, and the visible
research-loop contract passed `0/1` while remaining mode-conformant. The sole
evaluator-only full-task result is also `0/1`. Formalization was correctly not
applicable, Formalizer did not execute, and no kernel claim was produced. This
task must never be rerun, resumed, repaired, hidden-evaluated again, rescored,
resampled, or fed hidden/operator findings as source-owner feedback.

## What executed

1. TheoryDeveloper used one persistent eleven-turn workspace, authored two
   Markdown documents, ran two Python scratch programs, and explicitly committed
   its checkpoint.
2. An isolated mathematical referee used seven turns, exact document reads, and
   three scratch attempts before accepting the theory for execution.
3. AlgorithmEngineer used ten turns in one persistent source workspace. It read
   the theory, submitted source, received raw execution feedback, edited the same
   source, recovered from one exact-edit input error, reran successfully, and
   explicitly committed source hash
   `2e230efa71e8a4bd21d5ad27da1d3f2bf7fe1d64ebba4f28bbafedefab91edf2`.
4. The isolated generated-code reviewer used six turns. It made four probe-tool
   calls and two terminal submissions. None of the probes reached the immutable
   estimator, yet both submissions requested `ACCEPT`; the runtime rejected both
   and stopped fail-closed with
   `generated_code_semantic_review_packet_invalid`.
5. SimulationEngineer and Critic did not run. Only after AgentRuntime terminated
   did the evaluator inspect the accepted theory. Because no independently
   accepted Algorithm handoff existed, hidden algorithm and empirical execution
   were correctly not attempted, and no hidden feedback was generated.

## Operator findings

### 1. The accepted theory and estimator contradict the public positive-margin domain

The frozen public contract requires both row totals and both column totals to be
strictly positive. The accepted Theory document states only positive row totals,
and its ADEM stress list explicitly includes `K = 0` and `K = N`. The estimator
likewise rejects only non-positive row totals; its check `K < 0 or K > N` accepts
both zero-success and zero-failure column margins. Its own smoke test labels the
`K = N` table with 200 successes a passing maximum-total boundary.

This is not a harmless extension. The active task deliberately restricted the
conditional null to positive margins, so the model changed the declared domain
instead of implementing it. The independent referee nevertheless called the
execution contract correct and achievable.

### 2. The generated estimator violates the public closed request ABI

The public contract requires exactly four named request fields and rejection of
extra fields without mutation or coercion. `run_estimator` indexes the four
required keys but never compares the request key set, so any extra field is
silently accepted. The Theory implementation notes claim that extra fields are
rejected even though the exact source does not do so.

The estimator also skips its load-bearing one-step tail identity test. Its source
comment states the wrong index,
`p_greater(a) - p_greater(a+1) = P(A = a+1)`, then records the check as
`SKIPPED` because of floating-point accumulation. The correct identity uses the
mass at `a` and is directly testable within the public tolerance contract.

The source did execute successfully in the developer sandbox, but that smoke
result is not semantic acceptance and cannot override these public-contract
violations. Since the code reviewer never accepted a handoff, the frozen hidden
algorithm evaluator was ineligible and was not run.

### 3. The empirical protocol was descriptive rather than frozen

The accepted ADEM object repeatedly refers to preregistered margin triples,
alpha levels, replicate counts, and Monte Carlo uncertainty, but supplies none of
their actual values. It also gives an example confidence-interval rule instead of
one frozen joint acceptance decision. Consequently, it cannot authorize a
confirmatory run under the public pre-outcome identity requirement.

The hidden mechanical theory harness passed `7/7`. The calibrated protocol-v10
semantic evaluator returned document status `PASS` but combined status
`INCONCLUSIVE`: seven claims were satisfied and the empirical-design-and-scope
claim was inconclusive. That automated result agrees with the missing
preregistration details, but it also false-accepted the positive-margin and
closed-ABI claims identified above. Operator inspection therefore invalidates
trusted Theory and full-task credit.

### 4. The code-review blocker was model failure inside an adequate direct loop

The review tool description explicitly required the reviewer to define
`run_sandbox(seed, replicates, estimators)` and call
`estimators[artifact_id](request)` inside that function. One call failed before
creating an executable probe. Of the three executed probes, the first referenced
`estimators` at module scope and the next two referenced an undefined module-scope
`run_estimator`. Each raw `NameError` returned to the same reviewer session.

After the first three failed calls, the reviewer submitted `ACCEPT`; after the
runtime returned the exact requirement for at least one target invocation, it
made one more malformed probe and submitted `ACCEPT` again. The validator
correctly rejected both submissions. Existing deterministic tests already prove
that the exact binding works when a model-authored probe follows the advertised
interface.

This is useful negative evidence for Haiku, not evidence for a new repair harness.
Adding a wrapper, guessed symbol, forced retry, deterministic ABI patch, or second
scheduler would hide the failed capability and violate the project design. The
useful OpenAI Codex principle is already present: one persistent owner chooses
tools, receives raw observations, and revises its own bytes; validators preserve
identity and may block, but never rewrite scientific content.

## Evidence hashes

- Runtime manifest bytes: `78c31e44adc88ebb3b1d6bbd84b59042b45cdd91a69979eb79e91ed64a31b662`
- Runtime result bytes: `970298a28387be9291cb9e1d5b2e71307331d2885388cf37eb5d83118baaf9a7`
- Hidden evaluation bytes: `b7c64ffc3d3c97d0d59740a0b1c623852ad79d3ff97131ec9d637765d5cf8aec`
- Runtime topology bytes: `6bdc62213fc5a80faebac43bb92e7cb45e2ae115830c1dac095eb889d1909202`
- Runtime evidence-ledger bytes: `878352b6f6d0c07c8ae4418f2185d9b1bf4dc94161d9934187e8f7d97491a058`
- Runtime failure-summary bytes: `8a7ac3aadf669407f5154dba50200776485c58bc332a2a6bf4816562bc9e5b45`
- Accepted theory packet stable hash: `1da324fd5a0e9b4fd0fe65f40668c4cee88d38ba2049a9902beef82e9569b1cf`
- Accepted theory document set: `afbf5bffa4879c078cfc9b089c2575b03db090e955054752733610395adb645e`
- Theory document bytes: `112eb360cde2511c558d9da85a320fbbccbbfcbda5c5bc209b5fcb094adbb95d`
- Estimator document bytes: `7a4ed9fb309521411c863adb99b3ceb9d31b0c2efa0c3bf4f54c67d8e1bcd899`
- Theory-referee report bytes: `36c34454ff32689c4b7a33118944fb21018193942e7f3fa52324b321ac246e9c`
- Committed estimator source stable hash: `2e230efa71e8a4bd21d5ad27da1d3f2bf7fe1d64ebba4f28bbafedefab91edf2`
- Committed estimator source bytes: `26e243b4f71f97cafd73d56ed970ac5b4ff99e3ffbae62ac1f06dc8bdea69222`
- Code-review validation-failure bytes: `403b3e3cd8d25e4130dca5539f2b5737a25639a7ff977430bf0d97b2f1113116`
- Hidden theory mechanical result: `2448162397b7703a7f48b7085f566f96c6179c7bac3eeaf4f72af86fd45a11b6`
- Hidden theory semantic result: `f2797d8fa841544310c77170c1dd6fe21910d162bae09eed471584504eab387d`

## Disposition

Operator disposition:

`OPERATOR_INVALIDATED_PUBLIC_DOMAIN_CLOSED_ABI_AND_EMPIRICAL_PROTOCOL`

Trusted full-task capability remains `4/72`. No shared mechanism change is
justified by this draw: the single-owner workspaces, raw observation return,
explicit commit, independent review, hidden-authority boundary, and fail-closed
validator all behaved as designed. The failures are model-authored mathematics,
code, experimental design, and reviewer tool use under the required exact-Haiku
evaluation policy.

Deterministic verification passed the complete ladder panel `70/70`, the exact
generated-code reviewer loop panel `33/33`, and the complete repository
`989/989` in 85.41 seconds. These tests made no model or hidden-evaluator call
and do not alter the immutable score.

The next live task, if independently justified, must be a new disjoint task with
authority frozen before its first call. Task 72 remains immutable `0/1`.
