# Operator audit: exponential maximum Gumbel L0 v1

## Immutable draw boundary

Task `exponential_maximum_gumbel_known_result` consumed exactly one fresh product
draw and exactly one post-runtime hidden evaluation. The run used exact
`claude-haiku-4-5-20251001` for all seven enabled roles; no Sonnet, Opus, provider
fallback, or automatic model escalation occurred.

The immutable run is:

`runs/main_worker_research_l0_exponential_maximum_gumbel_20260827_v1_codex_single_loop_exact_haiku`

Runtime ended `BLOCKED` after 15 outer graph steps with
`critic_packet_validation_failed`. The frozen full-task result and trustworthy
capability result are both `0/1`. Formalization was correctly not applicable and
the Formalizer did not run. This task must never be rerun, resumed, repaired,
hidden-evaluated again, rescored, or resampled.

## What executed

The single AgentRuntime graph completed real work in the intended workspaces:

1. TheoryDeveloper authored and committed two Markdown documents containing the
   finite-sample law, limiting derivation, estimator contract, and diagnostics.
2. An independent Theory referee read the exact documents and accepted them.
3. AlgorithmEngineer produced an executable Python estimator. Its first source was
   revised by the same source owner after independent review; the second source was
   accepted.
4. SimulationEngineer produced exploratory and confirmatory sources, received raw
   execution and review observations, revised its own source, and reached an
   accepted confirmatory artifact.
5. CriticEvaluator inspected the exact Theory, code, simulation, reviews, and
   runtime evidence in one 25-turn tool session, but did not submit its terminal
   packet before the model-turn limit.

Runtime recorded 15 outer traces, two Architect traces, 14 outer tool calls, one
generated algorithm execution, and one generated simulation execution. There was
no second scheduler, RepairAgent, manually patched source, or hidden evaluator
feedback in the product loop.

## Frozen evaluator result

The post-termination evaluator observed the immutable accepted artifacts once:

- hidden algorithm checks: `8/8`, over 27 exact estimator invocations;
- hidden empirical checks: `10/10`, over 16,000 exact estimator invocations;
- hidden mechanical Theory checks: `7/7`;
- hidden Theory semantic document status: `PASS`;
- hidden Theory semantic claim status: six `SATISFIED`, two `INCONCLUSIVE`;
- full task: `0/1`.

The algorithm and empirical results are useful component evidence. They cannot be
promoted to full research-loop success because the hidden Theory authority did not
accept every required claim, Critic did not complete, unresolved-gap disclosure was
absent, and runtime research completion remained `0/1`.

## Operator Theory finding

The core task-specific derivation is mostly correct: for rate-one exponentials it
derives the support-aware finite law of `M_n - log n` and the fixed-y convergence to
the standard Gumbel CDF. The active document nevertheless contains a material false
contextual generalization.

At lines 92-94 it states that right-unbounded support plus a regularly varying tail
gives the Gumbel limit and that the exponential distribution satisfies those
conditions. This is false. Regularly varying heavy tails are associated with the
Frechet domain of attraction; the exponential tail is light and is not regularly
varying. Right-unbounded support alone also does not imply Gumbel attraction.

The same passage labels the normalization as `a_n = log n, b_n = 0`. Under the
common extreme-value convention `(M_n - b_n) / a_n`, the rate-one exponential uses
`a_n = 1` and `b_n = log n`. The document's parenthetical describes the intended
centering correctly, but its conventional parameter names are reversed or at least
undefined and misleading.

The independent referee explicitly read this passage and still called the
relationship correct. Critic also read the exact passage before exhausting its
turns. Operator authority therefore invalidates the active contextual Theory claim
and the referee's false acceptance. This does not alter the already-failed full-task
score, but it prevents the runtime Theory acceptance from being treated as trusted
component correctness.

Operator disposition:

`OPERATOR_INVALIDATED_CONTEXTUAL_THEORY_AND_RUNTIME_REFEREE_FALSE_ACCEPTANCE`

## Evaluator design finding

The hidden semantic result's two inconclusive claims concern empirical validation
that was also owned and passed by the separate hidden empirical lane. Requiring the
Theory document itself to establish those empirical outcomes conflates Theory and
empirical evidence ownership. The frozen result is not changed. Future disjoint
authorities should score derivation claims in the Theory rubric and leave executed
distributional claims to the independent empirical rubric.

This is an evaluator-ownership correction for future tasks only. No hidden expected
value, threshold, source, or rubric content is added to runtime, RAG, model context,
or this repository.

## Shared lifecycle finding

The Critic used all 24 ordinary workspace actions. On model turn 25 it requested one
more search; runtime correctly rejected that action with
`workspace_action_budget_exhausted`. The raw rejection became the final observation,
but the model-turn budget then ended without a sampling opportunity for the sole
terminal tool `submit_critic_evaluation`.

This was a shared lifecycle defect: a tool observation must be returned to the same
model before the session can terminate cleanly. Commit `bfae4e13` changes future
tasks only. When the last normal turn used an ordinary tool and did not attempt a
terminal disposition, the same model session receives exactly one terminal-only
continuation. It cannot execute another research action, route through Architect,
switch models, retry a rejected terminal packet, or invoke a fallback.

The client-loop, Theory, scientific-code, Lean, Critic, and architecture panel passed
`137/137`; the complete repository passed `995/995` in 80.45 seconds. Production
Python remains below the unchanged architecture budget at 149,998 lines. No live
model or hidden evaluator was called during this future-task correction.

## Evidence hashes

- Runtime manifest: `d431bab0e58410c885dbe980007b1ad9fe44ce8fbbb5c0bc5375f52c24c6b523`
- Runtime result: `bab966705af1b9eaecd2f0857289db8eb1f5c90dac80d791681adc179329624b`
- Hidden evaluation: `e47a1b4e799ac8f39ac7a66303e21ec98ec8e8b587ad76efeca8c38664445278`
- Runtime completion summary: `36fe3d295620acc4a2b49a40000e6dadb7b2021b1ad78f783ec5cfd0e7bb4a0a`
- Runtime failure summary: `e0966193342dc1a44a1bb192ff8d3fa665f6315ecb03c767e8fc2a592c51b8bc`
- Runtime model topology: `a16771d92443b4e577b9969ffe2c7b391a3cd3286fa0ab3955bd72480917870f`
- Runtime progress: `9aaee5a9d84040b387c1c37a0fed9cb4eb06fb4957c72439201f634d7e7c23b7`
- Runtime traces: `8f54b357d95607647bb68a822dd0d170ce0e0af0340aa18075417cbe8026a8d2`
- Runtime observations: `331dc778412a4e8e8251c4d6b9a64c87dccf7e5cc7bc6e4a57fd7f42611c51be`
- Runtime handoffs: `e7e25d209a59abbf3fc00285eacfc575ae9ccdcbe33b8c3efab146124d20dc31`
- Accepted Theory packet: `a99cec23c2c812ce5bde15187202ec5b73dc89a0282cc8f1d87e08d3092df7f6`
- Accepted Theory document set: `44c0b81c87531c6874424efd2762e7fa210b2a09c7b58f2a37a9c2bb3a940327`
- Main Theory document: `bdadfb57ea7a479d11d70de9fb0c1583a38fd6d136fa4a2cd3b06eb08b5e8af3`
- Estimator document: `12cb9bdff6d076ee8d33308031f5f95e8b7bbcfc8bcad2d6dc3b9a630559178d`
- Independent Theory review: `0e20a96814a38f476c8cdd9d09aee4fec9224a183687e75ecb71d68ec3134b7f`
- Accepted estimator source identity: `4fd67c64a4efc58e15626570460b00918097bf70e61c21f5d86f1f1455c16062`
- Hidden Theory mechanical result: `2448162397b7703a7f48b7085f566f96c6179c7bac3eeaf4f72af86fd45a11b6`
- Hidden Theory semantic result: `a0d44bb2bdf9ae407a081750fa313f3a92c922e896a82ce608d2e0fd9d272fdf`
- Hidden algorithm result: `825fa3b015cc8e93eb8eb50cc5825c2a52b86746c3637f13d11f8467b00eb2d4`
- Hidden empirical result: `32f559c8175e07e118551d6f297c38f00c176ef3e9e1aefa1bd90bed778ed0ee`

Trusted aggregate capability remains `4/73`. The exact formal-closure benchmark is
separate and remains unchanged.
