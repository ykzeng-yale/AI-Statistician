# Statlib uniform-consistency formal L0 v1

Date: 2026-08-22

## Frozen authority

- Task: `statlib_uniform_consistency_implies_consistency_formal_known_result`
- Model for every enabled role: `claude-haiku-4-5-20251001`
- Activation code: `d81ac4212501558d750bfc2a4b160f3f853b1724`
- Visible question SHA-256: `0a5b9a239889019c007f03ce3ce8b8efdc912dd211734387ac06345977751d1f`
- Visible formal-target prefix SHA-256: `4ff6129d04e7c7c6eebbcb02f16a90ec16064641cb479d0f4ec50f00c2dbe81f`
- Hidden authority manifest SHA-256: `d097d20c6ae82089c581eb5f508bd00457e18dad79fe08b43cfa02c6c21bbdc2`
- Hidden calibration SHA-256: `e2d2c1ea5c0b42fa0c6938e16f12ff10e668cb7cc0c22655a4609fbc05d1893b`
- Hidden calibration: human proof accepted; weakened conclusion, extra assumption,
  `sorry`, and custom axiom rejected (`5/5`).

The exact theorem statement and pinned Lean/Statlib environment were visible. The
human proof and evaluator remained outside the repository and model context.

## Immutable product result

The single authorized product draw is consumed. It ended `BLOCKED` with
`RESEARCH_CANDIDATE_INCONCLUSIVE`; hidden formal evaluation also failed. The task
is permanently `0/1` and may not be rerun, resumed, repaired, or rescored.

- Run: `runs/main_worker_research_l0_statlib_uniform_consistency_formal_20260822_v1_codex_harness_exact_haiku`
- Runtime manifest SHA-256: `290038d990aed7fbac801cf0cd1a71296cdd678e5addc0642f896a7b3ee18ea0`
- Hidden report SHA-256: `1c23f19bd19b23fee40e9f2c0f4e4c857c535ccb99ceb05d0b84d1c09a7e5739`
- Progress SHA-256: `7564ce845e1824524e979d37c1011698701d6f816ebf17f70614cb658d2c9041`
- Failure summary SHA-256: `f6829d782e54d4065c12ca6f2d97bd6df009f68728c0645e98508e1b19f369d2`
- Completion summary SHA-256: `982d3b7308ab2e387c41b5f3fe939eecf7b96e1a282553d8477c4578648dcab9`
- LLM topology SHA-256: `aa5c8b523eba57d2e61e999414b604b4b3a021791db35aec7043d744eff1ce00`

The one Formalizer workspace used two same-owner segments, 24 model-authored
source updates, 24 local Lean checks, and 10 formal-RAG calls. One source
elaborated only with `sorryAx`; independent axiom audit rejected it. No exact
candidate reached independent target review or kernel promotion. The final counts
are zero kernel-verified subclaims, zero full-theorem proofs, and one formal gap.
Architect was not called.

The hidden evaluator ran once after AgentRuntime terminated. Authority loading,
model policy, task identity, topology, and local-Lean checks were healthy, but
`one_kernel_promoted_candidate=false`; therefore the evaluator failed closed.

## Shared post-run corrections

Commit `fe7c7055` changes only future tasks:

1. Explicit `formal=required` research tasks now carry the actual Formalizer and
   target-review requirements in their runtime evidence contract.
2. A candidate rejected by structured axiom audit can no longer appear as a
   goal-free, locally accepted proof-state observation.
3. The same Formalizer session can inspect a model-selected declaration's exact
   source and importable module through the active, hash-bound RAG/project
   snapshot even when no LSP declaration provider is available.

These corrections contain no theorem proof, tactic, Lean grammar rule, symbol
alias, statistical formula, task-family route, new agent, scheduler, retry, or
budget increase. Focused tests passed `124/124`; the complete repository suite
passed `854/854` in 68.22 seconds. This is future-task mechanism evidence only and
does not change the consumed result.
