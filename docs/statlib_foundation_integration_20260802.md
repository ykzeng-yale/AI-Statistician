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
| EmpericalProcessLEAN | `2053b8f7af9c6dd3c29118296ef7c152229cbf62` | Active downstream statistics/proof library |
| AI4SLT | `d0f506f0a695018265dccb33bcb05e2f5ca1c876` | Version-bound external retrieval and port corpus |

`EmpericalProcessLEAN/main` now points to `2053b8f7`. The integration retains
source history from the VdVW and WDSM branches, absorbs the later Chewi,
Durrett, and van der Vaart work, and recovers seven additional proof commits
that were still reachable only from non-main branches. The recovered work adds
regular self-concordant barrier sums, affine pullbacks, inf-projections,
stationary-chain return-period results, and stopped/terminal Bernstein
projection links. Their public modules are imported by `StatInference.lean`,
so they are part of one canonical StatLib-backed library rather than branch-only
or ad hoc retrieval material.

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

| Corpus | Lean files | Declarations | Duplicate names | Snapshot |
| --- | ---: | ---: | ---: | --- |
| StatInference canonical closure | 1,192 | 51,993 | 0 | `BOUND_MATCH` |
| Pinned StatLib closure | 3 | 32 | 0 | `BOUND_MATCH` |
| AI4SLT public source | 65 | 2,000 | 0 | `BOUND_MATCH` |

The canonical entry now reaches every unique source module, including all 489
verified `StatInference.Matching.WDSM` modules. The 151 top-level
`StatInference.Matching.*` compatibility mirrors remain outside production RAG;
their 481 declarations duplicate the WDSM owners. Structural tests fail if a
new unique module is orphaned or a compatibility mirror enters the closure.

Both vendored historical snapshots were reconciled against this closure. Every
historical file has a current path; changed qualified declarations retain
current short-name owners except four trivial `0 = 0` demo markers and one
obsolete reverse bridge whose semantics changed. The snapshots remain
audit/training inputs and are no longer competing live Formalizer providers.

## Verification

- A clean `lake build StatInference` completed all 9,824 jobs on Lean
  `v4.30.0`. This fresh build exposed and fixed a root import cycle in the
  benchmark module; a structural test now prevents any submodule from importing
  the canonical root.
- `lake env lean StatInference.lean` completed successfully.
- The canonical import closure covers 1,192 Lean files and all 489 WDSM modules.
- The production graph indexes 51,993 public declarations and 210,115
  declaration-reference edges, with zero duplicate names and zero `sorry`.
- Eleven source-integration tests verify the direct StatLib dependency,
  canonical reachability of every recovered module, and the root-import rule.
- Namespace-aware `#print axioms` scans covered all seven recovered public
  theorems with zero unexpected axioms; only the accepted Mathlib foundations
  `Classical.choice`, `Quot.sound`, and `propext` were reported.
- All eight declarations introduced by the recovered proof commits passed the
  source declaration policy, and the changed Lean files contain no
  `sorry`/`admit`/`axiom`.
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
- Natural-language WDSM construction and finite-cell covariance queries retrieve
  their newly exposed qualified declarations from the bound production graph.
- The runtime source topology declares `StatInference -> StatLib`. A live query
  scoped only to `empirical_process_lean` therefore retrieved both the active
  `StatInference.QMD.integral_score_eq_zero_of_quadraticMeanDerivWithinAt`
  result and the pinned StatLib `QMD.integral_score_eq_zero*` API, while the
  version-mismatched AI4SLT corpus stayed outside the scope.

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

An explicit source request is expanded only through declared transitive
dependencies. This is topology-driven scope selection, not score manipulation:
requesting `StatInference` permits pinned StatLib support, requesting StatLib
does not pull the downstream library back in, and AI4SLT remains an independent
port/RAG corpus until its declarations are re-elaborated in the active project.

No theorem-family answer, Lean grammar rule, or tactic template was added.

## Remaining Work

This integration improves the formal foundation and retrieval surface; it does
not make AI-Statistician fully end to end. The main remaining proof bottleneck
is still a live tactic-state Formalizer loop that reaches exact source-theorem
kernel closure on multiple unrelated statistical tasks. Reusable abstractions
should be proposed upstream to StatLib incrementally, while task-specific book
and paper developments stay downstream.
