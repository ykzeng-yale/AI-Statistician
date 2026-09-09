# Task114: Consumed Failure

Date: 2026-09-09. Product commit: `cc563208f33b0217cb20ffc9394f5d2bfe464099`.
Task: `pareto_known_threshold_tail_index_mle_known_result`.
The pre-draw [activation ledger](../evaluation_activations/task114_pareto_tail_index_preactivation.json)
remains unchanged. This closeout records the sole draw, not a reassessment.

## Result

The process exited 1 after 496.754 seconds. AgentRuntime returned `FAILED`;
research and hidden-gold summaries both reported 0/1 accepted tasks. There was one
Architect planning call, nine TheoryDeveloper turns, and 25 independent theory
reviewer turns: 35 product model calls, all `claude-haiku-4-5-20251001`.
The 16 preactivation semantic-qualification calls are separate from that total.

The author committed one substantive Markdown derivation and its immutable
snapshot. Four scratch-tool calls occurred across author and reviewer workspaces;
these are exploratory diagnostics, not AlgorithmEngineer or confirmatory evidence.
The reviewer requested revision with three findings about interface completeness
and derivation presentation. These are reviewer judgments, not hidden-gold findings
or independently established mathematical errors. No theory was independently
accepted, and no scientific-code, Simulation, Critic, or Formalizer stage completed.
The evaluator therefore did not execute the hidden theory/code/empirical checks or
make candidate semantic-judging calls. Formalization was not applicable.

Five runtime steps consumed two outer research iterations and three workspace
continuations. The same TheoryDeveloper was selected to receive review feedback,
but failed before any revision model call with
`ValueError: client-tool session reference identity mismatch`.
The saved pending task is not permission to resume this consumed evaluation.

## Demonstrated Shared Defect

A read-only comparison of the saved author session and published handoff isolated
one difference: publication added the derived `estimator_interface_contract_id`.
The author session had already hashed the pre-publication handoff. Returning the
normalized handoff to that same session therefore failed its identity check despite
unchanged source content.

The future-task fix uses the existing interface identity normalizer when entering
the theory workspace and evaluating a model write, before state hashing. It does
not change mathematics, author code, review findings, budgets, or the retained
session verifier. A synthetic author/reviewer/author regression reproduces the
failure without Task114 material and verifies both valid continuation and rejection
of an actual interface-content change before another model call.

Shared commit: `146643bcad58192636c98dfcf8a3c9ccfe9a1fdc`. The full repository
suite passed 1,282 tests in 408.99 seconds. The focused theory/session, ladder, and
architecture panel passed 241 tests in 1.75 seconds. These establish mechanism
coverage, not fresh live efficacy of the fix.

Task114 remains failed and immutable. No rerun, resume, output patch, regrading,
resampling, or capability credit is authorized by this fix.

## Immutable Evidence

Root: `runs/main_worker_research_l0_pareto_tail_index_20260909_v1_codex_workspace_exact_haiku`.

| File | SHA-256 |
|---|---|
| `research_agent_runtime_manifest.json` | `ea6c6d63d8122e286242966af8487f88abc2893e3a9143de8b58d4b5c7d4605d` |
| `pareto_known_threshold_tail_index_mle_known_result_runtime_result.json` | `00ba9af9d38bdd3c21bc188202e81c24784d8b964c6c0985983f6c4f8b9fe70e` |
| `research_capability_gold_evaluation.json` | `5e43361cb0b38586e974a099abab4b236609a3a857db1775a0a457cab7fdd17a` |
| `runtime_progress.jsonl` | `78006f5d628dff756f33d430b854bf173e5865feba65e27a354a3f1b3c867445` |
| `operator_single_draw_terminal.json` | `da25314179569273201133f69cab0eb880a79cd22281043a90e281e26c631261` |

The explicitly designated Anthropic credential was used only in the execution
process. It was not printed, persisted, committed, or added to `.env.example` or
product credential discovery.
