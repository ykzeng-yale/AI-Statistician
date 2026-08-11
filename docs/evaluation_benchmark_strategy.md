# Evaluation Benchmark Strategy

Updated: 2026-08-09

## Purpose

Evaluation must answer one question: can the canonical AI-Statistician runtime
complete a fresh statistical research task with model-authored theory, executable
scientific code, task-bound formal retrieval, iterative Lean feedback, and exact
kernel-checked theorem closure?

Component checks are useful for development, but they never substitute for that
end-to-end result.

## Canonical Evaluation Path

All capability evaluation runs through one typed `AgentRuntime` graph:

```text
Architect plan
  -> Theory workspace
  -> Scientific coding workspace
  -> Independent semantic review
  -> Formalization and proving workspace
  -> Critic and kernel gate
```

Each source-producing workspace owns its own bounded environment loop:

```text
model chooses a tool or complete source edit
  -> Python, R, retrieval, or Lean executes
  -> raw observation returns to the same model
  -> model revises the current artifact
```

The runtime may enforce identity, hashes, budgets, permissions, schemas, and
evidence boundaries. It must not author source patches, statistical answers,
Lean grammar fixes, tactic recipes, theorem-family rules, or hidden repair plans.

There is no post-runtime formal execution plane. When `AgentRuntime` terminates,
unresolved typed tasks remain debt for a later resumed run. Offline reports may
read immutable artifacts but may not execute workers or receive capability credit.

## Model Policy

- Every live test and evaluation call uses exactly
  `claude-haiku-4-5-20251001`.
- Production may use Haiku or Sonnet.
- Opus is forbidden in executable configuration.
- Every manifest records provider, requested tier, and resolved model.
- A run with a non-Haiku evaluation call fails model-policy conformance.

## Frozen Cross-Family Protocol

The authoritative split is
`benchmarks/autonomous_cross_family_e2e_protocol_20260713.json`.

Development tasks:

- `right_censored_survival_km`
- `sequential_anytime_bernoulli`

Held-out tasks:

- `high_dimensional_spiked_pca`
- `extreme_tail_quantile_hill`

Held-out evaluation remains sealed until both development tasks independently
reach exact source-theorem kernel closure. A support lemma, retrieved theorem,
simulation pass, semantic-review acceptance, or aggregate score cannot replace
per-task closure.

After held-out evaluation begins, task-specific runtime rules, validators,
prompts, fixtures, or policy-pack changes based on held-out outcomes are forbidden.

## Required Per-Task Evidence

Every passing task must contain task-bound, same-run evidence for:

1. A fresh live Architect plan.
2. A rigorous TheoryDeveloper derivation and Critic revision.
3. Model-generated Python or R source executed in the declared environment.
4. Independent exact-Haiku semantic review of the exact source, arguments,
   result lineage, theory alignment, and frozen measurement protocol.
5. Architect-authored empirical requirements evaluated independently.
6. Formal-source retrieval bound to the current target and accessible imports.
7. Model-authored Lean source with raw compiler or proof-state observations
   returned to the same source-producing model.
8. Immutable exact-target identity from source statement through proof attempt.
9. Local Lean or AXLE kernel acceptance of the exact source theorem.
10. Zero acceptance-gating formal gaps.

Evidence from another task, another source hash, a replay fixture, a registered
template, or a standalone component run does not satisfy these requirements.

## Capability Suites

The maintained suite registry is `benchmarks/capability_eval_suites.json`.

| Suite | Scope | Release meaning |
|---|---|---|
| S0 | Release sanity | Package, schemas, and baseline gates are coherent. |
| S1 | Core method E2E | Registered methods execute through the product path. |
| S2 | Frontier static coverage | Intake and routing coverage only. |
| S3 | Blind theory-target recovery | Theory targets are recovered without answer fixtures. |
| S4 | Formal primitive ladder | Missing primitives are identified and closed honestly. |
| S5 | Proof bank and search | Existing proof assets and search regressions work. |
| S6 | Algorithm and simulation stress | Generated scientific code survives execution stress. |
| S7 | Feedback-loop regeneration | The same source model improves from raw failures. |
| S8 | Unsupported intake | Unsupported tasks fail closed. |
| S9 | Fresh frontier holdout | Generalization on unseen tasks. |
| S12 | Live Architect path policy | Live orchestration follows the model policy. |
| S13 | Integrated runtime capability | Full same-run, cross-subsystem evidence gate. |

S13 is the readiness authority. No other suite, audit counter, or historical
component result implies S13 success.

## Evidence Authority

Evidence levels are deliberately non-interchangeable:

```text
retrieval or pseudo-formal support
  < model or independent-review judgment
  < source execution or Lean diagnostic
  < target-bound local kernel verification
```

Only the final level proves a theorem. Simulation establishes empirical behavior,
not theorem truth. Semantic review establishes a model judgment, not execution or
proof. Retrieval establishes source support, not acceptance.

The readiness scorecard uses a compact set of integrated requirements. Readiness
is false if any required task lacks exact target-bound kernel evidence, regardless
of the number of support artifacts or passing component tests.

## Artifact And Lineage Policy

Substantive artifacts are content-addressed and stored once. Runtime state and
manifests carry compact references:

```text
TaskRef: id, owner, objective_ref, workspace_ref, budget
ArtifactRef: id, path, hash, kind, size
Observation: tool, status, stdout_ref, stderr_ref
Decision: action, target_ref
```

References are dereferenced only at the consumer boundary and their hashes are
verified. Traces must not recursively embed full tasks, deferred tasks, source
packets, or prior traces.

## Efficiency Contract

Evaluation records model calls, tool calls, latency, token use, candidate lineage,
and repeated-finding fingerprints. A run fails the efficiency contract when it:

- resets a lineage budget after Architect replanning;
- repeats the same owner/finding/source-hash cycle without a new observation;
- routes routine compile or ABI failures through Architect;
- executes code before a required theory or identifiability preflight passes;
- continues work after the selected evaluation endpoint;
- copies large payloads into manifests instead of storing references.

Deterministic replay is allowed for harness regression tests. Replay cannot count
as live model capability, source execution, or theorem evidence.

## Anti-Hardcoding Review

Any proposed runtime rule must answer all of the following:

1. Is it an environment, identity, safety, budget, schema, or evidence invariant?
2. Does it apply unchanged across unrelated statistical task families?
3. Does it avoid selecting mathematical content or source edits?
4. Could the source-producing model instead decide it from raw observations?

If the fourth answer is yes and the first answer is no, the behavior belongs in
the model workspace or prompt, not in Python middleware.

## Current Status

The historical v310 development run ended `MAX_ITERATIONS_REACHED` on both
development tasks and achieved `0/2` exact theorem closures. It is diagnostic
history, not readiness evidence. No post-simplification integrated live run has
yet passed S13, so held-out evaluation remains sealed.

The next gate is a fresh exact-Haiku development run through the single typed
runtime endpoint. Architecture work should be driven by shared failures observed
there, with no task-answer patches and no new side evaluation path.
