# Warner randomized-response prevalence L0 v1 operator audit

## Immutable evaluation boundary

- Task: `warner_randomized_response_prevalence_known_result`.
- Product draw: exactly one fresh `research_eval` run using
  `claude-haiku-4-5-20251001` for every enabled model role.
- Runtime status: `BLOCKED` after eight outer-graph iterations.
- Runtime research evaluation: `0/1`; mode conformance: `1/1`.
- Hidden evaluation: exactly one evaluator-only pass after runtime termination,
  with full-task result `0/1`.
- Formalization: not applicable and not executed.
- The run must never be resumed, rerun, repaired, hidden-evaluated again,
  rescored, or resampled.

Run directory:
`runs/main_worker_research_l0_warner_randomized_response_20260827_v1_codex_workspace_exact_haiku`.
The runtime head was
`08346840eb328332c8c78d06af218c997c7fabcc`. The runtime manifest SHA-256 is
`bebc65edfad41a63b096296e79bfb6440458f398be14e9627574afcc76f48643`,
the runtime-result SHA-256 is
`8aeccda93e84ae3cf3b9ff4466459e33b3752debe84395cfd3bb1e1e7633138a`,
and the hidden-evaluation SHA-256 is
`ce8d18a467ba585e5e45824a58e6d737a24800e947e3618660eb11dcfd03f73a`.
Hidden authority generated no runtime feedback.

## Theory result

TheoryDeveloper used one persistent Markdown/LaTeX workspace and correctly
derived the response probability

```text
lambda = (1 - p) + (2p - 1) theta,
```

the inverse unbiased estimator, exact variance, sampling decomposition,
unbiased variance estimator, direct-response boundary at `p=1`, and loss of
identifiability as `p` approaches `1/2`. Frozen authority passed all `7/7`
mechanical checks and all `7/7` calibrated semantic claims.

The active `warner_theory_derivation.md` contains one false intermediate
expansion at lines 77-82. The model explicitly retracts it at line 83 with
"Wait, let me recalculate" and gives the correct derivation at lines 84-95.
It is retained as visible scratch history, not treated as an active final claim.
The theory packet hash is
`11edf18a8bbf71239b059b0c93b31c8965530166b82b1e626510ad48e518e3e6`,
the document-set hash is
`685bc1bb1e004de2e04e850bfdcc544446813488fc6e27fbbd7d5fdb665ac6b7`,
and the derivation document hash is
`f2904eac2822d93c4a8b9a09888073ff99c86158ad2e95b9e668cb06567775e6`.

## Scientific-code result

The first independent source review correctly found that the initial estimator
accepted Boolean responses and extra request fields. The exact same
AlgorithmEngineer session regenerated and executed source that rejected both.
The second isolated review accepted that exact source, but its probes did not
exercise every public field and it missed that Python `True` remained accepted
as `truth_probability=1` through the `int`/`float` check.

The hidden algorithm result was therefore `10/12`: formula, numerical,
boundary, and invariance checks passed, while the aggregate closed-contract and
invalid-request checks failed. The evaluated source hash is
`f7d373bc8ab6665e643d8d858a9ac802e158d38629422a93d914fb2b8a7f785f`.
The theory-side estimator note, hash
`b30b6e2e675c4ac42b02c589680d9983e48d52e4471e169d61e723eae246cd8d`,
also described a stricter closed implementation than the displayed code.

No deterministic Warner rule or Python-Boolean repair belongs in runtime. The
general lesson is that an independent coding-agent review must probe the whole
declared public contract and return raw failures to the same source owner.

## Required empirical lane was skipped

The hidden empirical harness passed `10/10` over 30,000 estimator invocations.
That is evaluator-only component evidence, not runtime empirical completion.
AgentRuntime executed no SimulationEngineer source and accepted no
confirmatory empirical evidence.

After the second source review accepted the algorithm, its exact deferred task
was Critic. The transition policy returned that continuation before checking
the frozen required primary lanes, so the required empirical lane was skipped.
Critic then repeatedly submitted an invalid `ACCEPT` packet and terminated with
`critic_packet_validation_failed`. The terminal validator failed closed, but
its aggregate rejection did not tell the model which required dimensions were
unsupported or contradicted.

## Shared future correction

Commit `5f0626727c99f0aa013ab83d004be56d12d3516b` preserves exact deferred
continuations for ordinary specialist work, while a deferred Critic yields to
any still-unvisited frozen required primary lane. When no required lane remains,
the exact Critic continuation is preserved. Critic `ACCEPT` rejection now returns
one structured mismatch containing unsupported required dimensions,
`NOT_REQUESTED` mismatches, contradictions, gap status, and blocking dimensions;
the final invalid model submission is retained for audit.

This follows the useful Codex harness boundary: preserve the issuing step's
state and exact continuation, return informative tool observations to the same
model, and keep cross-workspace coordination sparse. It adds no Warner formula,
Boolean rule, code patch, RepairAgent, retry, extra reviewer, task-family route,
provider, model escalation, or second scheduler. The complete repository passed
`983/983`; top-level production Python remains below the 150,000-line budget at
149,995 lines. Task 65 was not touched by this future-task correction.

## Disposition

`RUNTIME_SKIPPED_REQUIRED_EMPIRICAL_LANE_CODE_CONTRACT_FAILED`

The task receives `0/1` trusted full-task capability credit. Aggregate
trustworthy capability remains `4/65`, and exact development theorem closure
remains `0/2`.
