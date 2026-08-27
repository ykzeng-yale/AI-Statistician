# Statlib affine-variance formal L0 v1

Date: 2026-08-26

## Frozen authority

- Task: `statlib_variance_affine_formal_known_result`
- Model for every enabled role: `claude-haiku-4-5-20251001`
- Visible-target commit: `9123c629bb8571bf73bdb1221c4c48eebd566957`
- Hidden-authority binding commit: `f6f136864bc1c1cde87c22658cfaa8220e4d4ed4`
- Visible question SHA-256: `2a09b5021a3355b5596a9dd7ce26823b53eac2726d64889856e3d68917bc29ec`
- Visible question stable hash: `185d09b17c9e9fea49a277c58747816067b2abf7c31442f54a9d7d503bb5d40d`
- Visible Lean prefix SHA-256: `1ae8d4b9fd1b7f3d00d8a2e3a6bd88c3039cd92a74d824a6df1d1e64eb309edd`
- Hidden authority manifest SHA-256: `96d904189b03c327cccf13bb9fe856d0b683596a7f43810418b76d687b66fd66`
- Hidden calibration SHA-256: `6ef5165ea0db7f17005ba7da29e5111f2ca26f8c5ee1771b15b28357f3c12415`
- Active Lean project commit: `4cec7860c926feebd4cbcdaccedb63b2156972dd`
- Statlib commit: `6575d611b5d32ef6013e9560d30b1a82a1972fb6`
- Mathlib commit: `81343555dae873c8de2de2b27bbabf7bc4d8d97a`

The hidden proof compiled. The hidden harness accepted the gold source and
rejected a weakened conclusion, an extra assumption, `sorry`, and a custom
axiom (`5/5`). The proof and evaluator remained outside the repository and
model workspace.

## Immutable result

The sole authorized product draw ended `BLOCKED`. The hidden evaluator then ran
exactly once and failed because `one_kernel_promoted_candidate=false`; its
authority checks had no errors. The task is permanently `0/1`.

- Run: `runs/main_worker_research_l0_statlib_variance_affine_formal_20260826_v1_codex_harness_scratch_exact_haiku`
- Runtime manifest SHA-256: `d216914769ce7aa4f166bad6307a82f5d1e536243ef9c55946d219ef7e245e53`
- Hidden formal report SHA-256: `6737c3ee3d1707db58f6e638d238d6f8816cd4fd3933beed4f77cfabbe53ac03`
- Runtime result SHA-256: `1459c29c0ca44545338d8e5d44f1a2d925b8415f68e9ca09f784735c31e1968b`
- Completion summary SHA-256: `50359d3710e86d6537d0057ff7a5bca4f16c2dbf4fcfa5be5aa26aa20fcf3bd7`
- Failure summary SHA-256: `3658a3dee4f9e30d2d6c068da576b1631ffb18eb297c8ed6ea3a2cbe84449e42`
- LLM topology SHA-256: `a4de87390499e1ef085ebee5e6e5006b8b63cee83901fe5474a9df1e2665cc98`

The outer graph used three iterations, three traces, two handoffs, and no
Architect model call. One persistent Formalizer session used 14 turns and 19
model-selected tools: eight independent Lean scratch checks, seven formal
searches, three declaration inspections, and one terminal candidate source
submission.

## Model-authored candidate

The submitted exact candidate compiled in the pinned project, matched the
frozen declaration identity, and passed the axiom audit:

```lean
import Statlib
import Mathlib.Probability.Moments.Variance

open MeasureTheory ProbabilityTheory

namespace AIStatisticianBench

theorem variance_affine
    {Omega : Type*} [MeasurableSpace Omega] (mu : Measure Omega)
    [IsProbabilityMeasure mu] (X : Omega -> Real)
    (hX : AEStronglyMeasurable X mu) (a b : Real) :
    Var[fun omega => a * X omega + b; mu] = a ^ 2 * Var[X; mu] := by
  have h1 : AEStronglyMeasurable (fun omega => a * X omega) mu := hX.const_mul a
  rw [show (fun omega => a * X omega + b) = (fun omega => (a * X omega) + b) by rfl]
  rw [variance_add_const h1 b]
  rw [variance_const_mul a X mu]

end AIStatisticianBench
```

- Stable source hash: `1de915df0e61fd9611de8c6f59db31921ab274ee3c94699fdd3a7d2a7aee6756`
- File SHA-256: `92d70624245734bdc6fe4984788952ceec4f63e69a80711e1d437bb6417d0c4c`

This is strong component evidence for the same-session Lean coding loop, but it
is not proof credit. The independent statement-semantic reviewer was never
called, so the exact source never reached kernel promotion.

## Shared diagnosis and correction

The pre-run review dispatcher unconditionally required a TheoryDeveloper packet.
This task's frozen intent explicitly marked Theory not applicable and supplied
the complete operator-frozen question, statement, declaration identity, source
prefix, and Lean environment. The failure was therefore a generic authority
contract defect, not a missing mathematical derivation or a Lean-generation
failure.

Commit `e4d97ee62a4c6dcda6970e583770d2563afa3898` lets future formal-only tasks
bind independent semantic review to that exact frozen question and target
contract. Theory-bearing tasks still require the exact hash-bound Theory packet.
It also deletes one unreferenced legacy deterministic algorithm/simulation audit
module. The complete suite passed `951/951`.

The correction adds no theorem, tactic, grammar rule, proof template, retry,
model call, task-family route, agent, scheduler, or candidate-source mutation.
It cannot change this consumed result and does not authorize rerun, resume,
repair, reevaluation, rescore, or resampling.

## Harness interpretation

The live evidence supports selective reuse of the OpenAI Codex harness
principles: one persistent source-owning session, model-selected tools, raw
environment observations, external content-addressed state, and sparse
cross-workspace handoffs. It does not support embedding Codex core, App Server,
Responses transport, thread storage, provider code, or another scheduler in the
Claude-first runtime. Cross-workspace contracts should bind authority and
identity; they should not prescribe mathematical content or ordinary repair.
