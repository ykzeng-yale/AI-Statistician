# Bernoulli Brier-score L0 v1 operator audit

## Immutable evaluation boundary

- Task: `brier_score_bernoulli_mean_known_result`
- Product draw: exactly one fresh `research_eval` run using
  `claude-haiku-4-5-20251001` for every enabled model role.
- Runtime status: `ACCEPTED` after nine outer-graph iterations.
- Runtime research evaluation: `0/1`; mode conformance: `1/1`.
- Hidden evaluation: exactly one evaluator-only pass after runtime termination,
  with full-task result `0/1`.
- Formalization: not applicable.
- The run must never be resumed, rerun, repaired, hidden-evaluated again,
  rescored, or resampled.

Run directory:
`runs/main_worker_research_l0_brier_bernoulli_20260827_v1_codex_workspace_exact_haiku`.
The runtime manifest SHA-256 is
`b3dc2972cd194bc5913bff6888deb6bce4ca3309c88dbd05fa88855dfe45dea2`,
the runtime-result SHA-256 is
`8d53bda9490146ef904fcf44a6cc2fe160356c5f46645621d43477c4bf1a5ed7`,
and the hidden-evaluation SHA-256 is
`674f3d3ba87feb9643f125dfbd6bd0a246dda021eb11880099ae10d1ffd10362`.
Hidden authority generated no model feedback.

## What worked

TheoryDeveloper used one persistent Markdown/LaTeX workspace. The population
identity

```text
E[(p-Y)^2] = q(1-q) + (p-q)^2
```

and its empirical analogue, uniqueness, boundary cases, and scope limitations
were correct. Frozen hidden authority passed all `7/7` mechanical checks and
all `6/6` calibrated semantic claims. The accepted theory packet hash is
`7ba412cbf5fafad83208950427378f37b80941a382d13e90bbe2625f860eca71`;
its document-set hash is
`2ac4f0135d99a54e52ea465ce8149b15f12ca336653314ddff28e3be3663349b`.

AlgorithmEngineer authored and executed one closed Python estimator, and an
isolated exact-source review accepted it. Operator inspection found the four
declared Brier quantities and input boundary consistent with the public
contract. The exact source hash is
`1f250c02e93013508a9bd512f8c2017d6ca612dbff8cfe8ce407673d89c57686`.
This remains component evidence only: the hidden algorithm harness was not
attempted in the consumed evaluation.

## Empirical authority failure

SimulationEngineer authored source with hash
`1e8aeb08c0dd848119720cd00e2504411b2ef62ec58aa5d50d397e569ab4e1af`.
Its diagnostic execution completed 4,759 estimator invocations at 128 requested
replicates. That execution did not create valid confirmatory evidence:

1. The evaluator source duplicated `run_estimator` instead of treating the
   injected reviewed estimator as its sole implementation dependency.
2. `acceptance_passed` was updated by algebraic and metamorphic checks, but not
   by the finite-sample event-rate or out-of-sample Brier measurements. Those
   large empirical outputs had no precommitted decision or precision criterion.
3. The independent Simulation review analyzed the upstream estimator rather
   than the current `run_sandbox` authority. Its report did not analyze
   `run_sandbox`, `acceptance_passed`, or `requested_runtime_replicates`.
4. The reviewer correctly restored the exact deferred confirmation task, but
   the outer transition policy replaced it with Critic because Simulation had
   already been visited. No byte-identical hidden-cohort confirmation ran.
5. Critic nevertheless declared every required dimension supported even though
   the canonical evidence view had `simulation_passed=false` and
   `confirmatory_empirical_evidence_eligible=false`. The deterministic terminal
   gate incorrectly allowed that model-authored ACCEPT.

The hidden evaluator also expected the retired
`RuntimeAcceptedImplementationInterfaceHandoff` middle layer and therefore did
not observe the direct hash-bound accepted-algorithm handoff that the reviewer
had produced. It skipped both hidden algorithm and empirical harnesses.
This is a future-evaluator mechanism defect, not permission to rerun Task 64;
no hidden algorithm or empirical pass is claimed.

## Shared future corrections

Commit `7e7c1a2e5837308a77770bbca994e0e059842294` makes the exact evaluator
source, its current-target review, accepted continuation, byte-identical hidden
replay, and required-evidence Critic gate agree on one lineage. Fresh research
evaluation now treats executable evaluator source as the authority and leaves
the old typed metric protocol as compatibility only.

Commit `b55a163388ba795d05bb48cd4194881ede829223` gives direct reviewed
algorithm handoffs a typed artifact identity and lets future hidden evaluation
consume that exact source without requiring the retired interface handoff.

These changes add no Brier or Bernoulli formula, threshold, content repair,
retry, task-family route, extra reviewer, scheduler, provider, or model
escalation. Raw source and execution failures remain in the same model-owned
workspace. The complete repository passed `980/980` after both commits.

## Disposition

`RUNTIME_FALSE_ACCEPTED_EMPIRICAL_EVIDENCE_MISSING`

The task receives `0/1` trusted full-task capability credit. Aggregate
trustworthy capability remains `4/64`, and exact development theorem closure
remains `0/2`.
