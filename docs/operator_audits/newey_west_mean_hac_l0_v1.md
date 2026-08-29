# Task 94 Operator Audit: Newey-West Mean HAC

## Immutable disposition

- Task: `newey_west_mean_hac_known_result`
- Public source: Whitney K. Newey and Kenneth D. West, *A Simple,
  Positive Semi-Definite, Heteroskedasticity and Autocorrelation Consistent
  Covariance Matrix*, Econometrica 55:703-708, 1987, DOI 10.2307/1913610
- Frozen product code HEAD: `262b593f287917081b5fe51572375f946c02ca45`
- Closeout evidence commit: `07448d9d14eef3253bee82647eeccd535d77f107`
- Run: `runs/main_worker_research_l0_newey_west_mean_hac_20260829_v1_codex_workspace_exact_haiku`
- Product runtime status: `BLOCKED`
- Frozen automated full-task result: `0/1`
- Operator trustworthy full-task result: `0/1`
- Trusted aggregate after consumption: `7/94`
- Runtime model for every executed model call: `claude-haiku-4-5-20251001`
- Formalization: not applicable and not executed

The sole product invocation and post-runtime evaluator assessment are consumed and
immutable. They must not be rerun, resumed, repaired, reevaluated, rescored,
resampled, manually patched, model-escalated, or exposed to the Task 94 source
owner as hidden feedback. The shared future-task corrections described below give
Task 94 no retroactive capability credit.

## Frozen authority

Before the first product call, the visible question fixed the stationary-mean
setup, divisor-`n` sample autocovariances, Bartlett weights, exact closed estimator
ABI, finite-sample nonnegativity claim, asymptotic bandwidth regime, AR(1)
specialization, confirmatory simulation requirements, and explicit task intent.
Its file SHA-256 is
`dc7e01da235c34723495d35db5f37eb6f0edf43f39dc3084a26e1143d7fd8b4a`;
the complete visible-question hash is
`f135bbb847e48963055726ed8a87534ea7ef0496fcbdb85be5f52125473220ad`;
and the runtime-visible projection hash is
`a63f974587914cb8755d53eca435a165951a560fbcb47d198d97239141d9ecb1`.
The pinned public-source snapshot hash is
`db842ef79ed2972414ef5f5eaf9e9d44eaca5d0b276f6544d1592745f3f48917`.

The evaluator-only schema-v4 bundle was frozen before activation. Its executable
reference passed seven theory-identity checks, eleven algorithm checks, and nine
empirical checks over 6,000 reference calls. Two behavioral negatives produced
three required rejections. The first semantic configuration failed closed at
`12/13` after fifteen exact-Haiku calls. A changed configuration then passed `6/6`
calibration cases, rejected `1/1` complete candidate-mode near miss, and accepted
all ten hidden reference claims in eight calls. Total preactivation evaluator
calls were twenty-three. None entered runtime feedback.

## Product execution

The one product invocation terminated after five outer graph steps:

1. Architect selected the frozen Theory-first path.
2. One retained TheoryDeveloper session authored two Markdown files and committed
   a content-addressed checkpoint.
3. An isolated source-grounded referee rejected the checkpoint for an incomplete
   Bartlett positive-semidefiniteness argument and an underspecified bandwidth
   regime, then returned its exact report to the same Theory workspace.
4. TheoryDeveloper revised the exact parent documents and committed a new source
   hash. A fresh isolated referee inspected that revision.
5. The second referee kept the prior findings active. The then-current runtime
   equated finding-ID closure with all mathematical progress, classified the
   lineage as stalled, and blocked before AlgorithmEngineer.

The terminal classification was
`architect_theory_execution_preflight_stalled`. This was not max-iteration
exhaustion: no next task remained pending. The visible research contract was
`0/1`, mode conformance was `1/1`, and the evaluator-only full-task result was
`0/1`. AlgorithmEngineer, generated Python execution, SimulationEngineer,
confirmatory simulation, Critic, Formalizer, Lean, and kernel promotion all
remained unexecuted.

There were 54 product-model response events, all exact Haiku: 30 in the retained
TheoryDeveloper session and 24 in the two isolated reviews. Client-tool execution
totaled 64: Theory used 33 actions and the reviewers used 31. The first source
session used Codex-style batches for three independent source searches and two
independent reads. Sonnet, Opus, retries, repair workers, fallbacks, hidden-feedback
revision, and model escalation were zero.

## Model-authored artifacts

The final Theory workspace contains:

- `theory_derivation.md`: 288 lines, 13,907 bytes, SHA-256
  `8ab9b57eea9f75744cfa8095f15003274e0bdaa144b4759b7afc923b677f91ea`
- `estimator_implementation.md`: 168 lines, 6,217 bytes, SHA-256
  `b1980e176f7771289bd50fea11b32485d564f42acf1c830275e35083a4d5ff90`

The first theory packet hash was
`9fe4190e032cf57805cabf6d5197e5ceb0c9dcbbde80c005cece647aaa188f9c`;
the revised hash was
`c6a72cda5797182738c51a5a86f92dcc9bd2a0b8cbbf3362582640a869879f10`.
No packet received independent acceptance. The first and second referee reports
were 220 and 284 lines respectively, with SHA-256 identities
`dde410a124ee257b58e807e39063d748402349946f5ba8a1b4c000fc990f4cba`
and `3e0833b3d95579d6cc60e6bf34f695b2986a0944f5b13090ec269485445e2900`.

The mathematics lived in durable Markdown/LaTeX files rather than a large JSON
answer. JSON carried only references, hashes, claim indices, and orchestration
metadata. Runtime wrote no equations, proof steps, estimator code, or statistical
answer.

## Mathematical audit

The runtime was right to refuse theory acceptance. Operator inspection found
material errors beyond the two referee reports:

- The stated Fejer/Bartlett transform is misnormalized, and the text never derives
  the exact divisor-`n` finite lag sum as a nonnegative quadratic form or frequency
  integral. Citing Toeplitz positive semidefiniteness does not complete the claimed
  estimator identity.
- The dependent-data CLT lists mixing, a bounded `2+delta` moment, and a generic
  martingale representation as interchangeable alternatives. A moment condition
  alone does not imply a dependent CLT; mixing requires quantitative rates and
  moments; the martingale condition is not stated precisely enough to imply the
  displayed limit.
- HAC consistency is asserted from autocovariance summability and `L_n=o(n)` using
  `Var(hat Omega)=O(L_n/n)` without dependence and higher-moment conditions that
  justify that variance bound.
- The finite-sample expectation is reduced to a truncation tail plus `O(1/n)` and
  described as generally downward. Demeaning and lag-window bias are not captured
  by that formula, and negative autocovariances invalidate the sign claim.
- The AR(1) identity `Omega=sigma_e^2/(1-phi)^2` and the ratio
  `Omega/gamma(0)=(1+phi)/(1-phi)` are correct. The later interpretation is not:
  for negative `phi`, long-run variance can be below the innovation variance and
  negative autocorrelation increases rather than reduces effective sample size
  relative to the marginal-iid comparison.

The isolated referee caught an incomplete PSD argument, but missed the CLT,
consistency, finite-bias, and negative-AR(1) errors. Its second report also treated
the finite estimator input `L` and the asymptotic sequence `L_n` as a decisive ABI
contradiction; that objection is overstated because the frozen finite estimator can
be invoked along a declared bandwidth sequence. The overall rejection remains
correct, but review precision and coverage are weak.

## Ownership audit

TheoryDeveloper also wrote a complete Python implementation inside
`estimator_implementation.md` before AlgorithmEngineer was authorized. Runtime
correctly treated it as unexecuted prose, not generated-code or empirical evidence.
The proposed source nevertheless exposes why role ownership matters:

- `dict.get` accepts undeclared request keys even though the frozen ABI is closed;
- `numpy.asarray(..., dtype=float64)` silently coerces strings and booleans;
- Python booleans satisfy the proposed integer test for `max_lag`;
- lagged products are averaged over `n-k` values despite the visible divisor-`n`
  convention;
- clipping or rejecting negative output masks the exact mathematical behavior the
  theory claimed to derive.

No runtime rule will repair those details. A future AlgorithmEngineer must author
and execute its own source against the visible ABI, receive raw sandbox feedback,
and remain independently reviewed before Simulation consumes it.

## Shared future-task corrections

Two small general corrections follow from the run:

1. Preflight progress is no longer defined solely by reviewer finding-ID closure.
   When the prior reviewed source hash exists and a fresh review binds a genuinely
   changed source hash, the same Theory workspace may continue under the existing
   `AgentRuntime.max_iterations` budget. An unchanged source, missing provenance,
   or exhausted outer budget still fails closed. This adds no local retry counter,
   repair agent, statistical rule, or second scheduler.
2. The TheoryDeveloper role now explicitly owns mathematical procedure semantics
   and compact downstream interfaces, while AlgorithmEngineer owns deliverable
   Python/R source. Theory scratch remains available for diagnosis, not as a hidden
   substitute implementation.

These changes are future-task harness evidence only. They cannot accept, rerun, or
rescore Task 94. The mathematical defects remain model and referee capability
failures; they do not justify a Newey-West formula rule, Fejer parser, CLT checklist,
AR(1) branch, extra reviewer vote, larger packet schema, or manual source patch.

## Codex harness conclusion

Selective reuse of the OpenAI Codex harness was useful at the right layer: retained
source-owner history, ordinary files, exact reads, batched independent read-only
actions, atomic model-authored edits, raw observations, immutable checkpoints, and
isolated findings-first review. The run also shows the boundary: generic coding
mechanics did not make exact Haiku derive or referee the statistics correctly.

AI-Statistician therefore keeps one provider-neutral outer runtime and its
domain-specific Python/R/Simulation/Lean authorities. It does not embed Codex Core,
App Server, Responses transport, shell policy, patch grammar, hooks, goal manager,
thread/worktree state, or a second agent scheduler. Harness reuse must reduce
friction around model-owned work, not move scientific content into deterministic
middleware.

## Verification

Focused source-lineage regressions passed `4/4`; Theory and ladder tests passed
`156/156`; and the complete repository passed `1050/1050` in 80.62 seconds.
Compileall, JSON parsing, `git diff --check`, credential scanning, task-specific
production-diff scanning, the 399-line production-design gate, and the
149,995-line production Python gate passed. No closeout command made a product or
evaluator model call, reran Task 94, or exposed a hidden artifact.

## Immutable hashes

- Runtime manifest: `40ba5feab05a9267d5f6913221bcd2c83c00c5da6f69345e9783adb5cb1468e2`
- Runtime result: `cc0f7ef0e33121e6be4f6f466f9f6bddbf97166b95f5c75779a1adcdea757a56`
- Gold evaluation: `c3b3a0772fc081bd618dc86ff6e0314ea350a39bb49e49294eaf08ab6f266195`
- Runtime topology: `21abbae11003e9da13c02518aae98bbbca5fa602f4b1fd2b9ae25abdee2020b4`
- Completion summary: `84e5b3e5b76b2bd58aa3dfb11e5be517d81a6bc766bb68a87f2142bf456ad32b`
- Failure summary: `2ffccf8edae2d9b682a6f3dac52d529a605a8ebfc3c2cedb45bb0fea12d3e5fd`
- Runtime progress: `d328f211485a12051f1ed0ac898a43a8ce112c8158b7b382ee951bcb057b3211`
- Runtime traces: `3eff27111ca0b6396029ee75daf83d19127c05ebfed33564b9e4e987b5cd4863`
- Evidence ledger: `11f65e0047e5e0c99ab1408c6b3b53f3ab7114524f21052d5d5622b3e6107d82`
- Task handoffs: `8cd802c24c1225431cdf16e35f6e254ffa73186224af558715522e9b446a30cc`
- Runtime observations: `0117d28f5019ecc8c874356e61a47013a11fa25878506c99bf1f724430f8db53`
- Outer runtime tool calls: empty-file SHA-256
  `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`

A product-artifact scan excluding the post-runtime gold report found zero hidden
paths, filenames, reference hashes, claim identities, or evaluator judgments. The
gold evaluator records `hidden_expected_values_disclosed=false` and
`runtime_feedback_generated=false`; post-runtime evaluator model calls were zero.
