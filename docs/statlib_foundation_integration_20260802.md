# StatLib Foundation Integration

## Decision

StatLib is the canonical reusable statistics foundation. The local
`EmpericalProcessLEAN` project pins StatLib and publicly re-exports
`Statlib.Inference` and `Statlib.QMD` through `StatInference.Foundation`.
Research-scale empirical-process, asymptotic-statistics, and WDSM developments
remain under `StatInference`; they should move upstream only after their API is
general, reviewed, and suitable for StatLib. This avoids creating a competing
statistics vocabulary while also avoiding a source dump into StatLib's
namespace.

The organization follows the current [StatLib roadmap](https://stat-lib.github.io/roadmap.html):
use Mathlib for general mathematics and probability, StatLib for reusable
statistics abstractions, and downstream libraries for larger domain
developments. The AI4SLT source and paper remain high-value organization,
signature, and proof-state references, but their different Lean/Mathlib snapshot
makes them port guidance rather than an importable proof dependency.

## Source Stack

| Layer | Bound revision | Runtime role |
| --- | --- | --- |
| Mathlib | `81343555dae873c8de2de2b27bbabf7bc4d8d97a` | Kernel-checked mathematical foundation |
| StatLib | `6575d611b5d32ef6013e9560d30b1a82a1972fb6` | Pinned reusable statistics API |
| EmpericalProcessLEAN | `dab7000b3d7a1fb4809347cf622cfd3a115746b4` | Active downstream statistics/proof library |
| AI4SLT | `d0f506f0a695018265dccb33bcb05e2f5ca1c876` | Version-bound external retrieval and port corpus |

`EmpericalProcessLEAN/main` and `codex/statlib-foundation-20260801` both point
to `dab7000b`. The merge retains source history from the VdVW and WDSM branches,
then resolves their public ownership on the StatLib-backed foundation. It also
absorbs the later Chewi, Durrett, and van der Vaart proof branches and connects
their standalone modules to the canonical entry module.

StatLib `main` was separately inspected at `0dc5b767`. It now follows Lean
`v4.33.0-rc1`; since the compatible pin, its only `Statlib/` source changes are
QMD tutorial anchors and proof adaptations for newer Mathlib, not new public
statistics declarations. Keeping the Lean `v4.30.0` pin is therefore an
explicit compatibility decision, not an unnoticed stale dependency.

## Canonical Corpus

The production dependency graph is no longer built from every `.lean` file in
the checkout. It follows the recursive local import closure of
`StatInference.lean`, so Lean's own module graph defines the public retrieval
surface. Private, local, and anonymous generated declarations are excluded.

Current schema-v5 graphs:

| Corpus | Modules | Declarations | Duplicate names | Snapshot |
| --- | ---: | ---: | ---: | --- |
| StatInference canonical closure | 630 | 39,176 | 0 | `BOUND_MATCH` |
| Pinned StatLib closure | 3 | 32 | 0 | `BOUND_MATCH` |
| AI4SLT public source | 65 | 2,000 | 0 | `BOUND_MATCH` |

The all-source StatInference audit still contains 481 duplicate names in
divergent historical/experimental branches. They are retained for review but
cannot enter the production RAG corpus. Eighty exactly identical top-level WDSM
mirrors were reduced to compatibility imports; non-identical pairs were not
mechanically merged.

## Verification

- `lake build StatInference` completed all 9,817 jobs on Lean `v4.30.0`.
- `lake env lean StatInference.lean` completed successfully.
- Namespace-aware `#print axioms` scans covered 4,718 changed foundation and
  WDSM declarations with zero unexpected axioms.
- An incremental scan covered 83 declarations in the four newly merged proof
  files with zero unexpected axioms and no `sorry`/`admit`/`axiom`/`unsafe`.
- The canonical graph contains zero `sorry`/`admit` declarations.
- All three graph health reports are schema-v5, integrity-valid, and
  `BOUND_MATCH`.
- The combined retrieval benchmark found all 30 cases at top 8. Its strict
  result remains 28/30 because of pre-existing LML and SciLean scoped-context
  misses; both StatLib cases and all AI4SLT cases passed their source scope.
- Declaration quality is source-agnostic: structural source-number prefixes,
  explicit numbered surfaces, thin wrappers, and oversized names are soft
  ranking metadata. No book or theorem name is encoded in this ranking path.
  The natural-language Newton-decrement query now ranks the semantic
  `SelfConcordantOn` theorem first while retaining historical surfaces below it.

Build success and retrieval success are not theorem-completion evidence. Only a
candidate elaborated in the exact active target project and accepted by Lean's
kernel can close a proof obligation.

## Formalizer Contract

Every dependency-context packet now records its entry module and corpus-scope
policy. `BOUND_MATCH` means only that the graph matches its own source snapshot.
It does not imply compatibility with the active target. The Formalizer must:

1. prefer import-visible declarations from the active project's canonical
   closure and pinned dependencies;
2. treat toolchain- or Mathlib-mismatched sources as port guidance;
3. use bounded qualified signatures and current proof-state diagnostics rather
   than full proof bodies;
4. re-elaborate every selected declaration and generated candidate locally;
5. preserve the existing kernel/evidence boundary.

No theorem-family answer, Lean grammar rule, or tactic template was added.

## Remaining Work

This integration improves the formal foundation and retrieval surface; it does
not make AI-Statistician fully end to end. The main remaining proof bottleneck
is still a live tactic-state Formalizer loop that reaches exact source-theorem
kernel closure on multiple unrelated statistical tasks. Reusable abstractions
should be proposed upstream to StatLib incrementally, while task-specific book
and paper developments stay downstream.
