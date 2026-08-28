# Pingouin repeated-measures correlation source replication L1 v1 operator audit

Date: 2026-08-28

## Immutable identity

- Task: `pingouin_joss_rmcorr_public_replication`
- Family: `repeated_measures_correlation_source_replication`
- Activation and runtime code identity:
  `126fc25cc5d82637b02866a7ff40cb034390e71f`
- Public source commit:
  `2d906c5fe30a44d3652c0895cea519e17d22a9f1` (`v0.6.1`)
- Source snapshot:
  `pingouin-joss-rmcorr-v0.6.1-public-replication-v1`
- Source snapshot hash:
  `ae890186047c1cd74a62b7e03ec24ff832a5cd4d21ca510da77d0073233bce52`
- Run:
  `runs/main_worker_research_l1_pingouin_rmcorr_replication_20260828_v1_codex_same_owner_exact_haiku`
- Configured model: exact `claude-haiku-4-5-20251001` for all seven
  enabled roles; no Sonnet, Opus, provider fallback, or automatic escalation
- Runtime result: `FAILED` in the first Architect trace
- Runtime product-model calls: `0`
- Post-runtime hidden result: `0/1`, with no eligible candidate execution
- Operator disposition: `CONSUMED_PROVIDER_ENVIRONMENT_FAILURE`

The task received one canonical runtime invocation and one post-runtime hidden
assessment. Both are closed and immutable. It must not be resumed, rerun,
repaired, hidden-evaluated again, reevaluated, rescored, or resampled.

Immutable SHA-256 values:

- Runtime manifest:
  `4a0b55ad8ea4fc72d2246be36599afd89d664a1443e6ee04671cbdfcc6ee2099`
- Runtime result:
  `8beb305aaa36ed4aeb9c934e576e5722d5d7c972abb59445fb9d73063538dd76`
- Runtime failure summary:
  `a6f3c39aa8fb1b7db1a92b9b1a80453cbb9d7604dcfdac987622587ba1473355`
- Runtime model topology:
  `633818b1ced695f59ada13da61343b9a94caa41c3be9d12c728550c0926bd49c`
- Hidden gold assessment:
  `d2df68ce83db5aea5ec5c06c45499f763a6587f44047fb3e4648d77b327b674e`

## Runtime result

The selected Codex bundled CPython 3.12.13 could import the local
`ai_statistician` package, but it did not contain the optional `anthropic` SDK.
The primary backend imports that SDK lazily on its first request. Architect
therefore raised `ModuleNotFoundError` before a request left the process.

The exact trace contains one Architect start, one failed plan-generation
substage, one exception observation, zero handoffs, and zero tool calls. No
source-owner session started. The frozen source entrypoint did not execute; no
report, checkpoint, generated scientific code, Simulation result, Critic
judgment, Lean artifact, or kernel evidence exists.

The topology record still establishes that all seven enabled roles were bound
to exact Haiku and both formal roles were disabled. It is model/configuration
provenance only, not scientific capability evidence.

## Hidden assessment

After AgentRuntime terminated, the evaluator-only boundary produced exactly
one assessment artifact. It reported `0/1`, `n_tasks_evaluated=0`, and no hidden
harness or semantic-judge execution because the runtime had not produced an
eligible source-replication checkpoint. Hidden expected values and evaluator
sources were not exposed to runtime or any model.

The preactivation `3/3` independent source reruns, `12/12` mechanical controls,
and exact-Haiku semantic qualification remain evaluator readiness evidence.
They cannot substitute for a product run and receive no Task 83 component or
full-task credit.

## Harness diagnosis

This is an operator/runtime-environment failure, not evidence that Haiku could
or could not audit Pingouin. It also exposes a generic activation gap: CLI model
topology was validated before runtime, but the selected process did not verify
that its live provider SDK and credential were loadable before creating the
first AgentTask.

For future tasks, the narrow correction is a provider-owned, no-network
environment preflight before AgentRuntime activation. It should check only
transport readiness, fail before a task trace or model call, and add no repair,
retry, content rule, extra agent, scheduler, or fallback. It cannot reopen this
task.

## Capability accounting

Task 83 is consumed at `0/1`. Four of 83 consumed scored tasks retain
trustworthy full-task capability credit. Formalization was correctly not
applicable. No Task 83 artifact may be changed or used for another model draw.
