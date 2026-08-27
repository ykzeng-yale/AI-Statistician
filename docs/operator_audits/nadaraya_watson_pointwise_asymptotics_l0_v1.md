# Nadaraya-Watson pointwise asymptotics L0 v1 operator audit

Date: 2026-08-26

## Immutable identity

- Task: `nadaraya_watson_pointwise_asymptotics_known_result`
- Family: `nonparametric_kernel_regression`
- Activation commits: `5b1feab6393002511bec0ae153b9947a284ccd63`,
  `8364ff9aa2c14ca6746cfee6fc5d7ca29f1e0f11`, and
  `46cfc2cef08380f6a3c9e503687af63c88671c78`
- Run head: `46cfc2cef08380f6a3c9e503687af63c88671c78`
- Run:
  `runs/main_worker_research_l0_nadaraya_watson_20260826_v1_codex_checkpoint_exact_haiku`
- Runtime model: exact `claude-haiku-4-5-20251001` for all seven enabled
  roles; no Sonnet, Opus, or automatic escalation
- Runtime result: `ACCEPTED` after six outer traces
- Frozen automated full-task result: `1/1`
- Trustworthy capability result: `0/1`
- Operator disposition:
  `OPERATOR_INVALIDATED_THEORY_AND_REVIEWER_FALSE_ACCEPTANCE`
- Future-task shared mechanism commit:
  `0824246428d4695bf273e578372cf0fae3d469de`

The task received exactly one product draw and one post-runtime hidden
evaluation. Both are closed and immutable. It must not be resumed, rerun,
repaired, hidden-evaluated again, rescored, or resampled.

Immutable SHA-256 values:

- Runtime manifest:
  `771f6023663b9d3a8a5735227586e00b13f4ec93b6433af5c3bb72ecbdc113db`
- Runtime result:
  `108124165307f7b738a6213f8058ba59dee187ab4b5b22e1232474a4c86137bb`
- Runtime completion summary:
  `b86b7a2b462e4873ee7b8a711ac9bef64480f6a2af4a7b5a17511fbb79fef6b4`
- Runtime model topology:
  `ce022bb18fbb2b408c4684f4a66129b158fd2dfefc202a23d82da94842b874a6`
- Runtime progress:
  `2f6d3e6bf06affe68b03e7f0ec692f451523b5a6f43547d46aa06f033052cbcf`
- Runtime traces:
  `ee27485c3abca6f92fde439a2c48034260f25a538d5f492aea4edcb76d4d91ea`
- Runtime observations:
  `1088d1c013edda4a3ff727489667181ed1994630b1084e7371c66e5b2712f13d`
- Runtime handoffs:
  `a19fa175a63af77276edeb138df0068cc4915f5d5968dc5be02a6cd138209718`
- Hidden gold evaluation:
  `bb4455521f854e763506de3fdba4aaeb4958ec1c41a2e49fcd190268b1afecb9`
- Initial Theory document:
  `67947ace170295f989328242d2ca942124ae77ffde74683569b49673749f8781`
- Final Theory document:
  `7a6a7e20031dc5d1c254b82c95d74e6d6a7fd3f5bf532aae3e3d493a2d36a4ac`
- Initial referee report:
  `b65659da4ae2bb4268b8a4c6c4b83d04d2f4a9f1b308c507b2297878c8ac5425`
- Final referee report:
  `f091ff1a4fcdc14d64dfffe5201c329a350227be5da35a44cebe6045787cd872`
- Hidden semantic result hash:
  `cbe88539e2858452126c8c5348eefc205ac4d44f5451db44530de31c7dc8e08f`

## Runtime result

One Architect call selected a Theory-only path. The persistent Theory owner
used 45 model turns and 44 model-selected tools across initial authoring and one
referee-driven revision. It wrote a substantive Markdown derivation, used
Python/SymPy scratch, handled ordinary edit and checkpoint errors inside the
same session, and committed two immutable checkpoints.

The isolated referee used 30 model turns and 31 tools across two reviews. Its
first report found a contradictory bandwidth paragraph and returned one
high-severity revision finding. TheoryDeveloper removed that contradiction in
the same source-owning workspace. The second report marked all 17 components
PASS. The final Critic used 10 model turns and 10 tools and returned ACCEPT.

The product draw used 86 model calls: one Architect call plus 85 client-tool
model turns. It recorded six outer traces, five handoffs, seven observations,
85 client-tool executions, and 12 ordinary model-actionable tool-error
observations. No Python/R algorithm, simulation, Formalizer, Lean, or kernel
evidence was requested or produced. Formalization was correctly not applicable.

## Frozen evaluation

The mechanical hidden Theory harness passed `7/7`. The independently
calibrated exact-Haiku semantic judge repeated its `12/12` calibration result
and marked all eight frozen claims `SATISFIED`, so the immutable automated
artifact says `1/1`.

That semantic pass is false. It remains part of the historical record but
receives no trustworthy capability credit. Hidden authority never entered the
runtime prompt, source revision loop, or Critic context.

## Operator findings

The final authoritative document has several load-bearing mathematical errors.

1. Lines 67-68 explicitly state `dX_i = h du` but omit the Jacobian from the
   integral. For the document's unscaled weight
   `W_i = K((X_i-x)/h)`, the correct leading expectation is
   `E W_i = h f(x) + O(h^3)`, not `f(x) + O(h^2)`. Lines 85-91 therefore omit
   one factor of `h` from the denominator expansion.
2. Lines 115-142 make the same omission for the numerator. The ratio can still
   have the familiar smoothing-bias formula because the common factor cancels,
   but the displayed numerator and denominator claims are false.
3. Lines 212-254 again omit the Jacobian in every squared-kernel expectation.
   The correct leading variance is
   `sigma^2(x) R(K) / (n h f(x))`, not the document's `1/n` expression.
   The stated variance therefore contradicts the later `sqrt(nh)` CLT.
4. Lines 308-316 use `S_n/n -> f(x)`. With the document's unscaled kernel sum,
   the coherent concentration statement is `S_n/(nh) ->p f(x)`. Denominator
   positivity can still follow, but not from the displayed normalization.
5. Lines 264-265 write `h^2 / sqrt(nh) = h^(5/2) sqrt(n)`. The relevant
   bias-to-standard-deviation comparison is `h^2 * sqrt(nh)`, not division by
   `sqrt(nh)`. Lines 271-274 state the familiar final CLT but do not derive it
   from the document's own variance calculation.
6. Line 188 says `O((nh)^-1) = o(h^2)` merely because `nh -> infinity`.
   That implication is false. A conservative remainder route needs an
   additional rate such as `nh^3 -> infinity`, or the sharper cancellation
   must actually be derived. Marking the bound OPEN later does not make the
   active complete-bias claim supported.
7. The conditional moment assumptions are stated only at the single point
   `x`, while the variance expansion and triangular-array CLT use local
   continuity or domination in a shrinking neighborhood. Continuity of
   `sigma^2` is also used but never assumed.

The final bias coefficient and limit-law formulas match the classical result,
but correct headlines do not cancel false intermediate derivations. The task
requires a rigorous chain, so required Theory fails.

## Reviewer failure

Both referee passes copied the candidate's already-transformed integrals as
their independent check. The model-authored scratch programs likewise began
from expressions with the missing factor and then verified downstream algebra.
The second referee called the `1/n` variance correct while also accepting the
`sqrt(nh)` CLT. The final Critic treated the referee's 17 PASS rows as
corroboration and repeated that no mathematical error existed.

The frozen semantic rubric explicitly required a valid change of variables and
the `1/(nh)` variance without a missing `h`. Its broad candidate call still
selected supporting final-formula paragraphs and marked every claim satisfied.
Its calibration set contained obvious single-error negatives, but no mixed
document with a familiar correct headline and a contradictory active
derivation. Calibration success therefore did not establish reliable deep
candidate adjudication.

## Shared correction

Commit `08242464` changes future tasks only:

1. The product Theory referee now reconstructs load-bearing substitutions and
   asymptotic normalizations from original definitions, preserves transformed
   measure/domain/constants, and reconciles variance order with limit scale.
2. Evaluator-only semantic judgment keeps the same frozen rubric, reference,
   evidence binding, and exact-Haiku policy, but uses one isolated candidate
   call per frozen claim. One broad response can no longer shallowly mark all
   claims at once.

This is a model-capacity and review-focus correction, not a mathematical
parser. It adds no Nadaraya-Watson formula, Jacobian detector, kernel rule,
output patch, repair agent, retry, scheduler, new product role, model
escalation, Sonnet call, or Opus call. The consumed candidate and old evaluator
result were not touched or invoked again.

The focused reviewer, semantic-gold, research-gold, and routing panel passed
`142/142`. The complete repository passed `953/953` in 79.47 seconds.
Compile-all and diff hygiene passed. The mechanism commit was pushed directly
to both `main` and `codex/runtime-eval-alignment-20260625`.

The official `openai/codex` checkout was incrementally audited through
`5af6979986a23fcd6bbeb1ef7b206cbc96e9a0a2`. Its new invocation-scoped
extension capabilities, gRPC trace propagation, Guardian tool/turn analytics,
and compact skill aliases reinforce lifecycle isolation, trace continuity, and
content-free telemetry. They do not provide scientific adjudication or justify
embedding Codex core, App Server, OpenAI Responses transport, thread storage,
or another scheduler in the Claude runtime.

## Capability accounting

This is the fifty-seventh consumed scored task. The immutable automated result
is `1/1`, but required Theory is false, so trustworthy full-task score is
`0/1`. Four of 57 tasks retain trustworthy full-task capability credit. Exact
development statistical theorem closure remains `0/2`.

No future shared change can alter this disposition. Task 57 is permanently
closed from rerun, resume, manuscript repair, hidden reevaluation, rescore, or
resampling.
