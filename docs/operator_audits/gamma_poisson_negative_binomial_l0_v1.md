# Gamma-Poisson negative-binomial L0 v1 operator audit

## Immutable evaluation boundary

- Task: `gamma_poisson_negative_binomial_known_result`
- Product draw: exactly one fresh `research_eval` run with
  `claude-haiku-4-5-20251001` for every configured role.
- Product status: `BLOCKED` after seven outer-graph iterations.
- Hidden evaluation: exactly one evaluator-only pass after AgentRuntime
  termination.
- Full-task result: `0/1` under the pre-frozen protocol.
- Formalization: not applicable.
- The run must never be resumed, rerun, repaired, hidden-evaluated again,
  rescored, or resampled.

The runtime manifest SHA-256 is
`d47ff473fff5ed7365edb900b6263d3344f6e3f4a0f771729846c6f8670a8fd1`.
The hidden-evaluation artifact SHA-256 is
`a3d8f98f942b4c94dbae603b5b251bd3dce662a2d896aad740bed2ad510fb5a9`.
Hidden authority remained outside the runtime and generated no model feedback.

## What worked

TheoryDeveloper used one persistent Markdown/LaTeX workspace, exploratory
Python scratch, and an explicit immutable checkpoint. The core mixture integral,
negative-binomial failure-count parameterization, success probability, mean,
variance, and overdispersion identity were derived correctly. The frozen hidden
authority passed all `7/7` mechanical theory checks and found all `7/7` required
semantic claims satisfied.

AlgorithmEngineer used one same-session Python source workspace. Its exact
estimator source executed successfully, an isolated reviewer corrected its own
two failed probes without routing source repair through Architect, and the third
probe invoked the target successfully. The frozen hidden authority passed all
`12/12` algorithm checks and all `11/11` empirical checks. Algorithm diagnostics
remained developer evidence and were not promoted to confirmation.

## Operator mathematical finding

The active theory is not globally correct. It says that, with fixed rate
`beta` and exposure `t`, taking `r -> infinity` makes the overdispersion term
vanish and recovers a Poisson law. In that stated regime,

```text
E[Y] = r t / beta
Var(Y) - E[Y] = r t^2 / beta^2
Var(Y) / E[Y] = 1 + t / beta.
```

The absolute overdispersion grows linearly in `r`, and the Fano factor remains
constant. Only the latent Gamma coefficient of variation shrinks. A fixed-mean
Poisson limit needs a joint scaling such as `beta` increasing with `r`; it does
not follow from `r -> infinity` with the other displayed parameters fixed.
The estimator document and independent referee repeat the related claim that
large shape makes overdispersion small. Thus the runtime theory review is a
false acceptance. The hidden rubric correctly recognized the seven required
claims but did not penalize this additional active false claim.

This is a model-judgment limitation under exact Haiku, not a reason to add a
Gamma-Poisson parser, asymptotic rule, repeated reviewer vote, hidden feedback,
or task-specific prompt. The existing generic referee prompt already requires
review of every active statement and limiting regime.

## Runtime terminal finding

The model-authored `metric_protocol.md` was frozen before outcomes, but its
independent semantic reviewer never produced a valid terminal envelope. The
first submission covered the frozen requirement while omitting a complete
portfolio judgment. Later correction calls were interpreted as complete packet
replacement, so the previously supplied requirement review disappeared. After
three submissions the runtime failed closed with
`architect_metric_semantic_review_packet_validation_failed`. No confirmatory
SimulationEngineer source or final Critic ran.

Commit `ccaca8d7ffcc9cecd0380c0cb07879bcc395647f` fixes this shared harness
contract for future tasks. The same reviewer session now owns a persistent draft:
each tool call recursively updates model-authored object fields, arrays remain
explicit replacements, omitted fields remain unchanged, and the unmodified final
validator still controls acceptance. Raw validation observations return to the
same model. This adds no content repair, statistical rule, extra agent, Architect
route, provider, scheduler, or model escalation. The complete repository passed
`965/965` after the change.

## Disposition

`OPERATOR_INVALIDATED_ACTIVE_THEORY_AND_THEORY_REVIEW_RUNTIME_INCOMPLETE`

The task receives no trusted full-task capability credit. Its correct core
derivation, executable estimator, and hidden empirical checks remain component
evidence only. Trustworthy aggregate capability remains `4/62`, and exact
development theorem closure remains `0/2`.
