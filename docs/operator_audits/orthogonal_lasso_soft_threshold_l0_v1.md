# Orthogonal Lasso soft threshold L0 v1 operator audit

Date: 2026-08-27

## Immutable identity

- Task: `orthogonal_lasso_soft_threshold_known_result`
- Family: `sparse_linear_regression_regularization`
- Visible-question commit: `aa3fbc10a4a9687b0b5aaea25d682af5d1f667e9`
- Authority-binding commit: `3b7d98165c1ced62040ca4ef0898d9355720fc22`
- Activation-seal and run head: `ee796e5a212aff555949fc444b13cdf31c989026`
- Run:
  `runs/main_worker_research_l0_orthogonal_lasso_20260827_v1_codex_workspace_exact_haiku`
- Runtime model: exact `claude-haiku-4-5-20251001` for all seven enabled
  roles; no Sonnet, Opus, or automatic escalation
- Runtime result: `BLOCKED` after ten outer traces
- Frozen full-task result: `0/1`
- Trustworthy capability result: `0/1`
- Operator disposition: `OPERATOR_INVALIDATED_THEORY_AND_SCIENTIFIC_CODE`
- Future-task shared mechanism commit:
  `7b07d9e7c183cd5a11fcbe4959f058e7386cfdca`

The task received exactly one product draw and one post-runtime hidden evaluation.
It is closed and immutable. It must not be resumed, rerun, repaired,
hidden-evaluated again, rescored, or resampled. Hidden findings did not enter the
runtime context or generate revision feedback.

Immutable SHA-256 values:

- Visible question: `b3849bd124ff337895c6c7016c74f2210448046b2ac7c841149876f94316e589`
- Runtime manifest: `72559f9cfde4d89314a1b3abb5ab6f8146f97e8721b7563a1a629e32ca791384`
- Runtime result: `f85925146ccc2a048d3cec428e944347b3d0d2bea3d6ee283cf5693295a8a126`
- Runtime completion summary: `b70c6d929f151d57833c47e5127e1959a7a378980a61315f88d4afdd266e6dca`
- Runtime failure summary: `2cf8af51f00d8303794dd7d9aef7cabf2d87d77c2fa1eae3aa5eb59de3845330`
- Runtime model topology: `c22a0d0fe5432251d0c5778ed2aae6a7a836a262345ee669a1e6fd9399128015`
- Runtime progress: `6072cff04cc03647972e395e4644e1d78e723f0fdf3755e9de4e65eee8fd7deb`
- Runtime traces: `30dd08f009b51b4e998d8bee10af9d304c0dcb686ab7222c7153831e9235a5ef`
- Runtime observations: `4d3e97dcd7a58ce97a1ee0e73ce5275ccec518480a456eb9e1d93f478d3a1dfb`
- Runtime handoffs: `3d36a929a439def7d0661121304b6dcd4694e3bac1e235cf0c94dc748941f426`
- Runtime tool calls: `c220abdddbd2204e8b070930d255f8a79528a813d0506401295e5da8a5277a7e`
- Runtime source snapshot: `d50a076404a473281ba40760905b4d9e398619b0c01d93faed0bf22c8955f239`
- Runtime evidence ledger: `b8a1c2a1fa17bf3fe8fcc5ca7e3ba4c4428032d457edd92b28fb0c555f291991`
- Post-runtime gold evaluation: `66e260e95fad003b72f938d63e559abb8e868ac4f6d6649a6697861d4f814e50`

## Runtime result

The one canonical AgentRuntime executed ten outer traces: four Architect, one
retrieval, one TheoryDeveloper, two AlgorithmEngineer, and two independent code
reviewer traces. It recorded nine handoffs, twelve observations, five outer tool
calls, and no same-owner continuation marker. The generated Python estimator ran;
SimulationEngineer and the terminal Critic did not run. Formalization was not
applicable and the Formalizer did not run.

One persistent Theory owner used 21 model turns and authored two Markdown/LaTeX
documents. An isolated referee used 15 model turns, read the hash-bound documents,
ran scratch code, and accepted the theory. Runtime accepted Theory packet
`theory_derivation:28305876afc3c4d10e5b9f0d` with hash
`0fc46bff317c2978ed1bec92a997807900fe7c9998e3f867098dadcf40e308e4` and
document-set hash
`24d87a2d942fb6b5d6385c4f27ed2c799ab2719421dd121aacda36131e24f13c`.

The first code review authored invalid probes: it referenced undefined
`run_sandbox` and `estimators` names. Runtime correctly treated those as reviewer
probe failures, but the model reported a cross-artifact finding and routed through
Architect to a second Algorithm session. The second reviewer executed broad
functional probes and accepted the code, but did not test the public ABI's
boolean and numeric-string exclusions.

The metric author remained one model/tool session and saw all three raw validator
observations. Its third commit used semantic-reference paths that were absent from
the exposed acceptance-authority catalog. That forced-terminal rejection ended
the client loop before the same source owner could read, edit, and recommit.
AgentRuntime therefore blocked with
`architect_metric_requirement_packet_validation_failed`. Research evaluation was
`0/1` complete and `1/1` mode-conformant.

## Hidden evaluation

The evaluator-only gate ran once after AgentRuntime terminated. It generated no
runtime feedback.

- Theory mechanical checks passed `7/7`.
- The calibrated semantic judge passed `10/10` calibration cases but accepted
  only `7/8` candidate claims. The document omitted the required distinction
  between the exact orthogonal-design formula and correlated-design behavior.
- The accepted Python source passed `11/13` hidden checks. It failed
  `all_public_contract_checks` and `invalid_requests` because `float(...)`
  coercion accepts booleans and numeric strings forbidden by the public ABI.
- The hidden empirical assessment passed `10/10` checks across 6,000 estimator
  calls. This is evaluator evidence about the accepted source, not runtime
  empirical completion: no runtime metric contract or simulation was accepted.

The hidden result therefore remained `0/1`. Its dimension vector marked Theory
and scientific code failed, empirical hidden-gold-passed but runtime-not-accepted,
formal not applicable, unresolved gaps failed, and the overall research loop
failed.

## Mathematical audit

The hidden semantic judge did not catch a more basic normalization error, and the
isolated runtime referee reproduced it.

1. Theory lines 21-22 claim
   `||y-X beta||^2 = sum_j (X_j^T(y-X beta))^2 + orthogonal residual`.
   Since `X_j^T X_j=n`, the projection contribution requires division by `n`.
2. Line 27 writes
   `X_j^T y - n z_j - sum_(k != j) X_j^T X_k beta_k`. Because
   `z_j=X_j^T y/n`, this expression cancels the response term and also omits the
   required `-n beta_j` term. Line 30 later states the correct residual score, but
   it does not follow from line 27.
3. The final separable objective on lines 33-37 is correct, but it is reached
   through those invalid identities. A correct derivation expands
   `||y-X beta||^2 = ||y||^2 - 2n z^T beta + n||beta||^2` directly, or uses the
   normalized projection coefficients.
4. The required correlated-design limitation is absent. The coordinatewise soft
   threshold formula depends on the diagonal Gram matrix and does not remain an
   exact independent-coordinate solution under correlation.

The runtime referee repeated the false projection identity and declared the input
validation comprehensive. Document length, scratch execution, and an isolated
review session therefore did not establish mathematical or ABI correctness.

## Shared harness correction

Official OpenAI Codex was rechecked at
`57e2edc6e97474448f1fb634224471448bc09d40`. The applicable design is a scoped
model/tool/observation loop: one model owns its edits, environment observations
return to the same history, tools are authorized for the invocation, and external
artifacts remain compact and hash-bound. Codex core, App Server, Responses
transport, thread storage, Guardian, and its scheduler are not embedded because
they would create a second conversation and orchestration owner.

Commit `7b07d9e7` applies one future-task-only correction. A forced-terminal
validator rejection may return to the same source-owning model under a separate
bounded recovery-action budget. That owner may inspect or read, edit, and
recommit. Repeated terminal rejection and no-progress conditions remain bounded.

The regression exercises exactly:

`forced final commit rejected -> check/read -> edit -> final commit`.

This adds no Lasso formula, metric path, statistical condition, output patch,
RepairAgent, Architect route, retry scheduler, provider, or model escalation. It
does not change this task's artifacts or score.

The focused client-loop suite passed `24/24`; the cross-workspace client-tool,
Lean, and ladder panel passed `329/329`; and the complete repository passed
`958/958` in 78.30 seconds. Model-policy and ladder tests passed `89/89`.
Compile-all, JSON, diff, architecture line-budget, and changed-file secret hygiene
passed.

## Capability accounting

This is the fifty-ninth consumed scored task. It is `0/1`; four of 59 tasks retain
trustworthy full-task capability credit. The run demonstrates real persistent
Markdown/LaTeX Theory, direct Python execution, isolated model review, immutable
hidden evaluation, and correct non-formal task routing. It does not demonstrate a
valid reviewed derivation, ABI-complete scientific code, an accepted simulation
contract, runtime empirical validation, final Critic acceptance, or formal proof.
