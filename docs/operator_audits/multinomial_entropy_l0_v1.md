# Multinomial Entropy: Consumed Failure

Date: 2026-09-09. Product commit: `27df7f6e99dd56f88f7fb49d87a4afba35393945`.
Task: `fixed_alphabet_multinomial_entropy_known_result`.
The pre-draw [activation ledger](../evaluation_activations/multinomial_entropy_preactivation.json)
remains unchanged. This records the sole draw, not a reassessment or Task114 retry.

## Result

The process exited 1 after 490.98 seconds. AgentRuntime returned `FAILED`;
research and hidden-gold summaries both reported 0/1 accepted tasks. Product calls
were one Architect plan, 13 initial TheoryDeveloper turns, 17 independent referee
turns, and 13 same-author revision turns: 44 calls, all exact
`claude-haiku-4-5-20251001`. The 32 preactivation semantic-qualification calls
are separate. Both qualification attempts and the corrected incomplete control
remain recorded in the frozen ledger; no failed qualification was discarded.

The model wrote Markdown theory, ran exploratory calculations, proposed an initial
checkpoint, received independent `REVISE` feedback, and continued in its own
workspace. There were 43 tool calls, including 12 scratch calls across the author
and referee. The author then saved progress with eight cumulative scratch refs.
Its description of being ready was not an accepted theory checkpoint.

The next continuation failed before another model call. No independently accepted
theory, AlgorithmEngineer execution, confirmatory Simulation, final Critic report,
or hidden candidate theory/code/empirical check followed. Post-runtime candidate
semantic-model calls were zero. Formalization was not applicable. Five runtime
steps consumed two outer iterations and three same-owner continuations; this was
not budget exhaustion, authentication failure, or a Lean blocker.

## Shared Defect

The continuation raised
`ValueError: continued theory scratch lineage conflicts with checkpoint`.
Read-only inspection found that the published parent had four scratch refs and the
checkpoint had eight. Its first four were identical structured values to the
parent history: both prefix hashes were
`da9aec66c19fe8b444c95de4ae1cf0aec09dbde00b12bb6e117f4a76600835be`.
The harness incorrectly required equality of the complete histories.

The shared correction accepts only an unchanged inherited prefix of the newer
checkpoint. It neither combines conflicting histories nor overwrites source or
observations. Synthetic regressions cover checkpoint-only, equal, and extended
histories, reject rewritten/reordered/dropped histories before any model call,
and exercise an actual source-owner revision/progress/continuation path using a
scripted provider and unrelated scratch calculation. The original parent remains
immutable and the appended observation survives without reexecution.

Shared commit: `8f4522f49bbaed8f8deee8932b06c5378f395601`. The focused synthetic
theory/workspace/runtime panel passed 125 tests in 1.41 seconds, and the full suite
passed 1,296 tests in 388.43 seconds. Compileall and diff checks passed. These are
mechanism checks, not a fresh live efficacy result.

This is a state-continuation fix, not evidence of mathematical acceptance or a
successful research loop. The consumed candidate, checkpoints, scores, and pending
task must never be resumed, repaired, rerun, or rescored.

## Immutable Evidence

Root: `runs/main_worker_research_l0_multinomial_entropy_20260909_v1_codex_workspace_exact_haiku`.

| File | SHA-256 |
|---|---|
| `research_agent_runtime_manifest.json` | `d3252853d2a255300f6ec223618c3babf8b395e9285bbb2c4736a6cbe5286bfc` |
| `fixed_alphabet_multinomial_entropy_known_result_runtime_result.json` | `35e3d3c175db50bc78e1afead2d34992fa90ba486c6ff85f79b020542b1e66e7` |
| `research_capability_gold_evaluation.json` | `ddbba76a83f6ab3b8ef35bac814637d9de97008865a7dcaa3ada12ffda600dc2` |
| `runtime_progress.jsonl` | `7cbba9c96670b3d26cfa668e162d14c5a6eff9dab5630ae70831884c2a873519` |
| `operator_single_draw_terminal.json` | `efc098b5c2e3ea99c0159926cbc3ac1851436b08be898cd3183778b06a38706a` |

The designated Anthropic credential was used only in process memory. It was not
printed, persisted, committed, or added to `.env.example` or credential discovery.
