# Lean Foundation Integration Check

AI integration: `c480917f7427c2ebbe2ddff1bb0c1c0c02d3b7e9`.
Lean main/submodule: `db6c7718349f3c14a7e37905f3529675f1ebaa52`.
This is release/mechanism evidence, not a new agent experiment or mathematical result.

The [foundation audit](../external/EmpericalProcessLEAN-main/docs/publication_foundation_audit_20261001.md#correction-baseline-inventory-mismatch)
corrects the earlier eight-name diagnosis. The separate baseline walker missed
inline attributes, unlike the current-file reader. It is deleted; both inventories
reuse the existing reader. No source theorem, proof body, name exception, new Lean
grammar or relaxed check is introduced. New attributed source-qualified names
remain rejected; explicit all-declaration audits still expose legacy debt.

Verification records are local under `runs/publication_lean_api_inventory_20261002/`:

- Primary suite: 1961 passed, 18 skipped, one existing xfail, 711.59 seconds.
  `primary_suite.junit.xml`: 1980 cases, zero failures/errors, SHA-256
  `a19fe2b524f3c59515d018bc0a17f39731f8a5c843bf8e161f1e31653eb822f3`.
- Lean/RAG tool suite: 86 passed, one opt-in skip. `tool_tests.junit.xml`:
  87 cases, zero failures/errors, SHA-256
  `ba118c575b789b511fb06fc9d68892732df66e5886b93c44e2d99e0f2800f139`.
- Default guarded InteriorPoint file/module and three existing ledger declarations:
  exit 0, complete native axiom-dependency records, zero unexpected axioms. No policy bypass.
  `guarded_check.log` SHA-256
  `9ee67527184179815bbcc48c120e5cacad4d94bfb571b14831ff26bbac2c237d`.
- Entire unchanged library incremental gate: zero new names/violations. This is
  not whole-API conformance: InteriorPoint's explicit all-declaration audit has
  746 violations among 1466 source declarations, including 328 oversized names.

Current main RAG was refreshed without changing historical indexes/evaluations
or tracked CSV exports. Its schema 6 SQLite metadata and shared manifest bind the
clean Lean commit above, Lean 4.30.0 and Mathlib
`81343555dae873c8de2de2b27bbabf7bc4d8d97a`. It has 52485 declarations;
canonical lookup of `negLogBarrier_selfConcordantBarrierOn_Ioi` returns the
same active source. Index counts and graph neighbors are not native proof evidence.
The source ledger is unchanged at SHA-256
`99f2a42a4813a896591a9296cc824d6131982bfd52a482056173a4f330c54e80`.

Partial branch review confirms the truncated-power-moments and affine-power-moments
files are byte-identical to their non-ancestor branch versions. Main retains the
compact-power-concave-family branch content and adds a constrained-family definition
and three lemmas. This checks those files, not all branch mathematics or proof fidelity;
unmerged ancestry alone does not justify a wholesale merge.

Release rights remain unresolved: the Lean tree tracks 50 textbook assets
(23 PDF, 20 Markdown and seven PNG files across five source groups). Presence in
Git does not establish redistribution rights. Neither repository has a root code
license. No book asset was deleted, redistributed anew or licensed by this check.
An exact-pattern scan of current tracked text found no Anthropic/GitHub token-prefix
matches; it is not a comprehensive security audit or a check of Git history.

## Release Access And PR Check, 2026-10-03

Configured Git access still fetches Lean main at the pin above. Anonymous GitHub
repository-page and repository-API requests both returned 404, so public release
access is not established. The fresh-source reconstruction is an operator-access
check, not an unauthenticated installation. No visibility, license or source-rights
setting was changed. The AI-Statistician public open-PR endpoint returned an empty
list; the Lean unauthenticated open-PR endpoint was unavailable, not an empty list.

The five advertised Lean PR head refs were compared with pinned main:

| PR ref | Head | Current integration evidence |
| --- | --- | --- |
| 1 | `262051e53073742d4e615ac45faefac73330c39d` | Ancestor of main |
| 2 | `cca6faa1d9173d77465a430a6b8572ea6d5d8603` | Non-ancestor, but `git cherry` finds a patch-equivalent main commit |
| 3 | `852c75295521316db6f87937310344265e37dee0` | Ancestor of main |
| 4 | `8978fa5e3860952805926c3af14d3af3f5a0a647` | Non-ancestor, but `git cherry` finds a patch-equivalent main commit |
| 5 | `bf131018bb3460b411454e382ae9dd425ae2a79b` | Not patch-equivalent; its eight touched paths were compared. The refresh script is byte-identical, Statlib/source profiles remain, and main adds pinned dependency preference and updated policy/tests. |

This is code-integration evidence, not an assertion about the five PRs' current
open/closed state. Re-merging old commits is not justified by their non-ancestor
status. In particular, PR 5's default rejection of `exact`/`simpa` proofs is not
restored: current policy assesses statements and consumers, not tactic spelling.
No branch, proof, canonical index or historical evaluation was changed.

## Fresh Source Reconstruction

The [2026-10-03 record](../benchmarks/publication_foundation_rebuild_20261003/README.md)
preserves the first preparation failure and separate first root-build timeout.
The latter reused verified third-party caches but no local-library build artifacts;
source and manifest stayed unchanged. At 3600.372 seconds the root was unfinished
and the owned build group was terminated. No native error line was observed before
that point, but partial compilation is not a successful reconstruction or an
all-proof audit. The complete raw output and identity records are available in
the record. No retry, source patch, pin migration or agent credit followed.

The active compiled 4.30.0 project remains available; this incomplete release
check is not a new prerequisite for non-formal scientific comparisons. Resolve
the actual study conditions and independent assessment next, rather than rerun
root builds or expand verification machinery to avoid publication execution.

No model calls, new theory acceptance, source-fidelity/coverage qualification,
clean-machine release or comparative scientific benefit is established. Both
official publication studies remain prospective. Historical Haiku and consumed
Qwen records remain unchanged; the full two-publication goal remains active.

## Candidate Import Scope For The Shared Appendix, 2026-10-04

The following small selection makes A05's proposed library scope concrete. It
uses nine existing principal theorems in eight existing modules, not a new root
module, forwarding aliases, proof development or another source ledger. These
are operator-selected library examples, not held-out targets or autonomous agent
results. The selection is not yet a source-fidelity-certified public API.
Import a listed leaf for its subject rather than the entire library root; this
limits the requested surface, not necessarily its transitive dependencies.

The active project is unchanged at `db6c7718349f3c14a7e37905f3529675f1ebaa52`,
Lean 4.30.0, Mathlib `81343555dae873c8de2de2b27bbabf7bc4d8d97a` and Statlib
`6575d611b5d32ef6013e9560d30b1a82a1972fb6`. Both actual dependency checkout
HEADs match those pins. Statlib supplies the reusable inference model and QMD
predicates; local consumers must not be described as independently inventing
those objects.

### Principal Declarations And Exact Scope

| Existing module and principal declaration | Formal scope and proof route | Source/release disposition |
| --- | --- | --- |
| `StatInference.Inference.Deterministic`: `StatInference.InferenceModelofMeasure.conditionalRisk_ofDeterministicEstimator` | Measurable data, estimator, functional and nonnegative extended-real loss; Statlib's deterministic-kernel risk equals a single loss integral. It uses `Kernel.lintegral_deterministic'`. No consistency, finite-risk or optimality conclusion is added. | A downstream Statlib consumer, not a mapped textbook theorem. |
| `StatInference.Inference.QMD`: `StatInference.QMD.integral_score_eq_zero_of_quadraticMeanDerivWithinAt` | Classical QMD within a neighborhood, probability measures throughout that set and domination by a sigma-finite measure imply mean-zero score in each direction. The proof uses Statlib's classical-to-Hadamard conversion and neighborhood score theorem. | Downstream specialization; it does not establish LAN, efficiency or a whole asymptotic theory. |
| `StatInference.ProbabilityTheory.MomentStandardization`: `ProbabilityTheory.secondRawMoment_eq_variance_add_mean_sq` | A probability measure and `MemLp X 2` give second raw moment = variance + squared mean, through Mathlib's `variance_eq_sub`. Higher standardized moments in the same file have additional conditions and are not implied by this selection. | Existing ledger: `lee-yue2021`, Equation 25, `proved-general`. Preserve that author label; this is a standard identity, not a new paper theorem. |
| `StatInference.EmpiricalProcess.GlivenkoCantelli`: `StatInference.vdVW_theorem_2_4_1_outerAlmostSureGlivenkoCantelli` | Equal laws (`HasLaw`), pairwise independent observations and finite primitive L1 bracketing number at every positive radius imply the explicit outer-a.s. uniform deviation predicate. The source route uses finite covers, endpoint strong laws and decreasing scales. | Existing VdV&W route report maps Theorem 2.4.1, but the JSONL ledger does not include this route. Do not infer a complete coverage denominator from that ledger. |
| Same module: `StatInference.vdVW_theorem_2_4_1_outerProbabilityGlivenkoCantelli_of_countable_of_classFun_measurable` | In addition to law/independence/bracketing, the displayed theorem requires a finite sampling measure, a countable index class and measurable class functions. It derives empirical-coordinate measurability and the direct outer-probability conclusion. | A conditional/countable version, not the arbitrary-class conclusion with those assumptions removed. The separate `VdVWPGlivenkoCantelliClass` is an OR of outer-probability and outer-a.s.; its checked book-style theorem enters the latter branch. |
| `StatInference.AsymptoticStatistics.BoundedRefinedL2ClassSupremumPositiveRadius`: `StatInference.AsymptoticStatistics.RefinedL2Chaining.outerExpectation_classSupremum_le_entropy_add_tail` | Positive sample size/radius, a nonempty measurable class, an envelope, the displayed second-moment bound and iid-law sample yield the extended outer-expectation entropy-plus-tail bound, with constants 115456 and 2. The proof scales the small-radius theorem and both entropy/tail terms. | Ledger: van der Vaart 1998, Lemma 19.34, `proved-general`. The centered process is `sqrt(n) (P_n-P)`, and entropy uses floored log and an extended integral. Finite/infinite entropy and total-integral conventions require source-fidelity review. |
| `StatInference.AsymptoticStatistics.L2BracketingEnvelopeMaximal`: `StatInference.AsymptoticStatistics.RefinedL2Chaining.outerExpectation_classSupremum_le_envelopeEntropy` | Nonempty measurable class, measurable L2 envelope, positive sample size and iid-law sample give a bound at the envelope L2 norm with constant 461825. The proof treats zero envelope norm separately, then invokes the positive-radius theorem and envelope-tail bound. | Ledger: Corollary 19.35, `proved-general`. Do not omit the envelope assumptions or claim the explicit constant is optimal. |
| `StatInference.AsymptoticStatistics.UniformlyBoundedL2BracketingMaximal`: `StatInference.AsymptoticStatistics.RefinedL2Chaining.outerExpectation_boundedClassSupremum_le_extendedEntropyCorrection` | Positive radius/sample size, nonempty measurable class, nonnegative uniform bound, the displayed second-moment condition and iid-law sample give the extended entropy correction with constant 115456. Finite entropy uses the real-valued correction; infinite entropy is a separate extended-value branch. | Ledger: Lemma 19.36, `proved-general`. An infinite right-hand side is not an informative finite guarantee. |
| `StatInference.Optimization.EntropicBarrierParameter`: `StatInference.Optimization.entropicBarrier_is_finrank_selfConcordant` | A finite-dimensional real inner-product space with the stated Borel/Haar-volume structure and a convex body with nonempty interior gives regularity, self-concordance, a dimension-valued gradient norm bound, gradient/Hessian derivatives, covariance inverse and boundary blow-up. The proof assembles the entropic domain, differential, varentropy and boundary results. | Ledger: `optimization2026`, Theorem 13.13 entropic-barrier bullet, `proved-exact`. The universal-barrier bullet is separate; this is not a proof of all optimization source material. |

Full Lean signatures and local definitions remain authoritative. In particular,
outer expectation is the infimum of measurable nonnegative majorant integrals;
the indexed supremum is over absolute centered coordinates in `ENNReal`.
The scope descriptions above are not additional hypotheses inserted into proofs
or replacements for independent comparison with the exact source edition.
No book statements or assets are redistributed by this selection.

### Native Check And Identity

A fresh default guarded check of the two Statlib consumers and the GC module
returned exit 0 in 41.473 seconds. It compiled each exact source file, built the
three named modules and required a complete native `Lean.collectAxioms` record
internally for each of five selected declarations: the two consumers, both GC
theorems above and `StatInference.vdVW_theorem_2_4_1_glivenkoCantelli`.
There were zero unexpected axioms; the allowed foundations were `Classical.choice`,
`Quot.sound` and `propext`. No guard, policy or module-build bypass was used.
The checker publishes its selected-name/summary log, not individual passing
axiom sets or a full theorem dependency graph; do not claim those were released.
The policy checked zero **new** names, not all legacy API names. The GC source's
book-qualified identifiers remain naming debt; no cosmetic aliases were added.

The log is `runs/publication_lean_curated_scope_20261004/selected_guard.log`,
SHA-256 `214e652533a58cd7b7a7d9b9b1552567fc78ad1adba92f00095c7808d65b3a17`.
Build output counts 2581/2581/8491 include cached dependencies, not newly proved
items. This was not a fresh-source or clean-machine reconstruction.

The other five principal declarations are members of the unchanged 102-name
kernel-only check already recorded above. Its original exit-0 log/hash remains
unchanged; it is not rerun, upgraded to API conformity or counted as a new result.
Their five source files are byte-identical between that audit baseline
`bd6a2ba599e4a9405fdc048cbe586ea3859390da` and current Lean HEAD. This establishes
source identity, not an independent source-fidelity judgment.

SHA-256 identities of the selected source and newly checked compiled files:

| Path relative to Lean project | SHA-256 |
| --- | --- |
| `StatInference/Inference/Deterministic.lean` | `315b0df3a357641d9973efae5f65f3f181512b83bb57659788eb9928ccce9c5b` |
| `StatInference/Inference/QMD.lean` | `074f6a5ae9d48f7906253032654db741567bc0a6a8909f6991032ad804ad5b53` |
| `StatInference/ProbabilityTheory/MomentStandardization.lean` | `fa138c88723946c617779f70f65e3610e8ac29de2e6b2461b8c5a22dff7da9fa` |
| `StatInference/EmpiricalProcess/GlivenkoCantelli.lean` | `a67c25ac4e9fb3d0b7545f6c7cef7b7b872069073247f8bb3603b4bde1ce5178` |
| `StatInference/AsymptoticStatistics/BoundedRefinedL2ClassSupremumPositiveRadius.lean` | `2523eab6cc914ba3590c9019d7eb22d0ad816d4163a2c6ddd4718e8b6cdfd022` |
| `StatInference/AsymptoticStatistics/L2BracketingEnvelopeMaximal.lean` | `a713dc15972e0668ee32369903fed82a871fc48635191244b65fd2f25b2528b8` |
| `StatInference/AsymptoticStatistics/UniformlyBoundedL2BracketingMaximal.lean` | `469d31f67ad4031f115f3b0fb2b76d02bd97ddd72c35432ffe858063d58d3a0f` |
| `StatInference/Optimization/EntropicBarrierParameter.lean` | `29f06f33d3afdeeac65098546088542761a4cc4d8748fd6ab67c1048c836f64a` |
| `.lake/build/lib/lean/StatInference/Inference/Deterministic.olean` | `53e97d97d07c4a321c52389a4c9af3edf07e22338d83a6c976638cb0851f9e9e` |
| `.lake/build/lib/lean/StatInference/Inference/QMD.olean` | `0554cd912dfc58a19259aa91aa41c0b21b812379a33f0f6909dd9cfcb8f04d46` |
| `.lake/build/lib/lean/StatInference/EmpiricalProcess/GlivenkoCantelli.olean` | `cc159d090c8f4d44bbb84ba6465ca107b2e0f4a8dfbf3de005c7f358e7bcd311` |

The Lake manifest hash is
`1a4a57144b4f871f233c42d125517b0598002e895e2e708779d646ee3ff2f65f`;
the existing source ledger remains
`99f2a42a4813a896591a9296cc824d6131982bfd52a482056173a4f330c54e80`.
No Lean source, proof, source-map role, RAG index, project pin or consumed agent
evaluation changes. The actual pinned Statlib files identify their Apache 2.0
license and original author; that observation does not license local code or
textbook assets.

T06/A05 remain open for source-edition fidelity review, useful consumer/API
curation, full permitted provenance/dependency release, attribution/rights and
successful clean reconstruction. No proving-performance comparison is claimed
or required by this optional support selection. Primary H/S qualification and
experiments remain the critical path.
