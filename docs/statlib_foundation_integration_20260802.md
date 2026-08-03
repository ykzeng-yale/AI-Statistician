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
| EmpericalProcessLEAN Lean graph source | `afe250da47daabbf6c97cad1b5a3e9c88abe2f4c` | Active downstream statistics/proof library |
| AI4SLT | `d0f506f0a695018265dccb33bcb05e2f5ca1c876` | Version-bound external retrieval and port corpus |

`EmpericalProcessLEAN/main` now points to `afe250da`. The integration retains
source history from the VdVW and WDSM branches, absorbs the later Chewi,
Durrett, and van der Vaart work, and recovers seven additional proof commits
that were still reachable only from non-main branches. A second content-level
branch audit recovered four more public results without replaying their stale
histories: the bounded-polytope logarithmic barrier, aperiodic Markov-chain
convergence, periodic cyclic decomposition, and the prefix-stopped Bernstein
projection-link empirical-supremum bound. The recovered work adds
regular self-concordant barrier sums, affine pullbacks, inf-projections,
stationary-chain return-period results, and stopped/terminal Bernstein
projection links. Their public modules are imported by `StatInference.lean`,
so they are part of one canonical StatLib-backed library rather than branch-only
or ad hoc retrieval material.

The canonical root now imports `StatInference.Foundation` plus 14 stable
domain entries. Those entries organize the existing import DAG into StatLib-
founded inference, asymptotics, local asymptotic theory, semiparametrics,
causal inference, empirical processes, probability, estimation, experiments,
optimization, source-matched applications, and evaluation surfaces. The
README publishes the same source-owned taxonomy with resolvable module paths;
RAG may use those labels as organization metadata, never as proof evidence.

"StatLib-backed" describes package dependency and API ownership, not a blanket
import added to every proof module. At this snapshot the reusable inference
extensions consume the foundation through `Inference.Deterministic`,
`Inference.QMD`, and the new `Estimator.InferenceModel` adapter. The adapter
embeds the existing sample-size-indexed estimator object into Statlib's
`InferenceModelofMeasure` and proves its conditional-risk integral identity.
Their public domain entries and the `StatInference` root expose one coherent
API. The
remaining canonical modules keep minimal Mathlib/local imports until they use a
StatLib statistical object. This follows the same layering rule as Mathlib:
reuse an upstream object where semantics match without coupling unrelated
mathematics for branding or retrieval.

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
| StatInference canonical closure | 1,211 | 52,004 | 0 | `BOUND_MATCH` |
| Pinned StatLib closure | 3 | 32 | 0 | `BOUND_MATCH` |
| AI4SLT public source | 65 | 2,000 | 0 | `BOUND_MATCH` |

The canonical entry now reaches every unique source module, including all 489
verified `StatInference.Matching.WDSM` modules. The 151 top-level
`StatInference.Matching.*` compatibility mirrors remain outside production RAG;
their 481 declarations duplicate the WDSM owners. Structural tests fail if a
new unique module is orphaned or a compatibility mirror enters the closure.
Statlib's canonical root is still a legacy import file, so Lean rejects a
direct import from module-mode `StatInference.Foundation`. The foundation
therefore mirrors the two public submodule imports at the current pin, and a
dynamic parity test fails if the pinned `Statlib.lean` root changes.

The lightweight declaration index now follows the same configured entry-module
closure instead of scanning every `.lean` file beneath a root. Nested aliases
of the same canonical source collapse to the broadest project root independent
of inventory order, and a configured source with no resolvable entry module
fails closed. A fresh StatInference lightweight build indexed 27,164
declarations from 1,075 declaration-bearing files, attached one of 11
source-authored domain labels to every declaration, and admitted zero
non-WDSM `Matching` compatibility files. This index remains a cheap retrieval
surface; the schema-v5 dependency graph is the source of exact import and
declaration-reference lineage.

The dependency graph and lightweight Python/SQLite retrievers now share the
same source-agnostic oversized-name policy taken from the source RAG design:
generated-scale Lean short names remain available by exact full or short
declaration identity, but do not occupy ordinary semantic results. Replaying a
QMD/inference query kept the downstream StatInference adapter at rank 1 and the
pinned StatLib theorem at rank 2, with no oversized result in the top eight;
an exact oversized-name query still recovered its declaration and explicit
quality-gate marker.

Both vendored historical snapshots were reconciled against this closure. The
430 Lean files in AI-Statistician's frozen EmpericalProcessLEAN source all have
current paths, while the canonical library adds 932 Lean files beyond that
snapshot. Changed qualified declarations retain
current short-name owners except four trivial `0 = 0` demo markers and one
obsolete reverse bridge whose semantics changed. The snapshots remain
audit/training inputs and are no longer competing live Formalizer providers.

## Verification

- A clean `lake build StatInference` completed all 9,843 jobs on Lean
  `v4.30.0`. This fresh build exposed and fixed a root import cycle in the
  benchmark module; a structural test now prevents any submodule from importing
  the canonical root.
- `lake env lean StatInference.lean` completed successfully.
- The canonical import closure covers 1,211 Lean files and all 489 WDSM modules.
- The production graph indexes 52,004 public declarations and 210,290
  declaration-reference edges plus 3,318 import edges, with zero duplicate
  names and zero `sorry`.
- Seventeen source-integration tests verify the direct StatLib dependency,
  canonical reachability of every recovered module, and the root-import rule.
- All 59 Lean-RAG tests pass, including the source-owned taxonomy path contract,
  declaration-aware live-result filtering, and canonical graph-neighbor policy.
- Namespace-aware `#print axioms` scans covered all sixteen recovered public
  theorem endpoints plus both declarations in the estimator adapter with zero
  unexpected axioms; only the accepted Mathlib foundations
  `Classical.choice`, `Quot.sound`, and `propext` were reported.
- Every recovered public declaration passed the source declaration policy, and
  the changed Lean files contain no
  `sorry`/`admit`/`axiom`.
- The canonical graph contains zero `sorry`/`admit` declarations.
- All three graph health reports are schema-v5, integrity-valid, and
  `BOUND_MATCH`.
- The combined retrieval benchmark found all 30 cases at top 8. Its strict
  result remains 28/30 because of pre-existing LML and SciLean scoped-context
  misses; both StatLib cases and all AI4SLT cases passed their source scope.
- The external user-intent benchmark found all 25 cases at top 8. The new
  indexed-estimator/conditional-risk query ranks the canonical StatInference
  adapter first globally and first in active-project scoped context. Its strict
  aggregate remains false only because the existing LeanMachineLearning UCB
  and SciLean Gaussian-calculus cases miss the source-scoped top-2 gate.
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
- Cross-corpus declaration lineage now resolves explicit references from a
  local declaration only into topology-declared direct dependencies. The live
  QMD adapter binds its statement to
  `QMD.HasQuadraticMeanDerivWithinAt` and its proof to
  `QMD.integral_score_eq_zero_of_mem_nhds` plus the uniquely resolved
  Hadamard-conversion method. The deterministic adapters bind to
  `InferenceModelofMeasure` and `InferenceModelofMeasure.conditionalRisk`.
  Exact names are preferred; a short method name is accepted only when globally
  unique in the dependency graph. Ambiguous names, reverse downstream lookup,
  comments, strings, and undeclared companion corpora fail closed.

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

The bounded Formalizer prompt now retains a per-hit source-activation
projection. It distinguishes active-project declarations, pinned direct
dependencies such as Statlib, and external port candidates such as AI4SLT,
while omitting broad provenance and proof bodies. This topology controls how a
candidate may be activated; it never upgrades retrieval into proof evidence.

An explicit source request is expanded only through declared transitive
dependencies. This is topology-driven scope selection, not score manipulation:
requesting `StatInference` permits pinned StatLib support, requesting StatLib
does not pull the downstream library back in, and AI4SLT remains an independent
port/RAG corpus until its declarations are re-elaborated in the active project.

For each selected declaration, the prompt also carries bounded
`cross_source_statement_uses` and `cross_source_proof_uses` rows with corpus id,
qualified declaration name, and match kind. These rows contain no proof bodies
and are labelled source-derived, non-proof evidence. This turns StatLib and
StatInference from unrelated result piles into an inspectable dependency route
without granting retrieval theorem authority.

No theorem-family answer, Lean grammar rule, or tactic template was added.

## Remaining Work

This integration improves the formal foundation and retrieval surface; it does
not make AI-Statistician fully end to end. The main remaining proof bottleneck
is still a live tactic-state Formalizer loop that reaches exact source-theorem
kernel closure on multiple unrelated statistical tasks. Reusable abstractions
should be proposed upstream to StatLib incrementally, while task-specific book
and paper developments stay downstream.

StatLib's current contiguity proposal is not yet a released, hole-free API, so
the verified downstream contiguity development is intentionally not rebound to
it. After a compatible upstream API lands, migration should use a small
orientation-checked adapter and real downstream consumers; importing a
provisional branch or duplicating its definitions would weaken the foundation.
