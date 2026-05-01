# Formalization Semantic Audit

This audit classifies the current `StatInference` library by semantic claim
level.  The goal is to prevent benchmark or milestone progress from being read
as stronger mathematical progress than the Lean declarations actually establish.

## Claim Levels

| Level | Meaning | Promotion standard |
| --- | --- | --- |
| `primitive_proof` | A theorem is proved from existing Lean/mathlib facts and local definitions. | May be counted as formal mathematics, subject to semantic review of the statement. |
| `deterministic_reduction` | A proof of an algebraic/order/topological reduction that assumes the probabilistic input. | May be counted as a real reusable theorem, but not as proof of the assumed probability theorem. |
| `mathlib_wrapper` | A project-facing alias or wrapper around an existing mathlib concept. | May be counted as infrastructure, with source mathlib declaration cited. |
| `bridge_interface` | A structure carries assumptions and a proof field, then downstream theorems project that field. | Count only as interface/scaffold unless a concrete no-placeholder instance is proved from primitive assumptions. |
| `certificate_interface` | A proof-carrying certificate packages future entropy/GC/Donsker/concentration arguments. | Count only as a checked handoff API, not as the underlying empirical-process theorem. |
| `non_vacuity_witness` | A concrete trivial or finite example shows an interface is inhabited. | Count as a sanity check only. |
| `benchmark_hole` | A benchmark skeleton allows scoped placeholders. | Never count as promoted library theorem until replaced by no-placeholder Lean code. |

## Current Module Classification

| Area | Representative declarations | Current claim level | Source / theory provenance | What is proved now |
| --- | --- | --- | --- | --- |
| ERM oracle inequalities | `oracle_ineq_of_uniform_deviation`, `oracle_excess_sequence_bound` in `StatInference/Asymptotics/Basic.lean` | `deterministic_reduction` / `primitive_proof` | Vapnik-style ERM and uniform convergence arguments; standard statistical learning theory | The deterministic inequality from a uniform deviation bound and approximate ERM. |
| Restricted empirical-process ERM handoff | `oracle_ineq_of_uniform_deviation_on`, `oracle_excess_sequence_bound_on` in `StatInference/EmpiricalProcess/Basic.lean` | `deterministic_reduction` / `primitive_proof` | Same ERM-uniform-deviation argument, restricted to a class | The class-restricted deterministic excess-risk bound. |
| Empirical averages and empirical risk notation | `empiricalAverage`, `empiricalRiskOfLoss`, `empiricalRiskSequence_excess_bound_of_uniform_deviation` | `deterministic_reduction` | Empirical risk notation from statistical learning theory | Deterministic sample-average notation and handoff to ERM inequality. |
| Ratio / Hajek / IPW algebra | `ratio_sub_target_eq_residual_div`, `scaled_hajekRatio_sub_target_eq_residual_div` | `primitive_proof` / deterministic algebra | Standard ratio-estimator linearization algebra | Exact real-valued ratio identities. No probability or causal identification is proved here. |
| Convergence wrappers | `MathlibConvergesInProbability`, `MathlibConvergesInDistribution` | `mathlib_wrapper` | mathlib convergence in measure / distribution | Project-facing aliases for existing mathlib notions. |
| Slutsky / continuous mapping / delta method | `SlutskyBridge`, `ContinuousMappingBridge`, `DeltaMethodBridge` | `bridge_interface` | van der Vaart & Wellner Ch. 1 and Ch. 3.9 style asymptotic calculus | Only projection from supplied proof fields. The general theorems are not derived bottom-up. |
| Asymptotic linearity + CLT route | `AsymptoticLinearCLTBridge`, `IndexedAsymptoticLinearCLTRoute`, influence-function normality routes | `bridge_interface` | Standard asymptotic statistics and semiparametric inference | Downstream handoff from supplied asymptotic linearity, CLT, and remainder proofs. |
| M-estimator / Z-estimator interfaces | `MEstimatorWithOracle`, `MEstimatorArgminConsistencyRoute`, `ZEstimatorLinearizationBridge` | mixed: deterministic reductions plus `bridge_interface` | van der Vaart & Wellner Ch. 3.2-3.3 | Deterministic projection to existing oracle/ERM interfaces; Z/M asymptotic theorems remain bridges. |
| GC / entropy / bracketing / Rademacher / VC | `CoveringNumberDeviationCertificate`, `BracketingDeviationCertificate`, `RademacherDeviationCertificate`, `VCDeviationCertificate` | `certificate_interface` | van der Vaart & Wellner Ch. 2.4-2.6 and learning-theory entropy route | Handoff APIs from future deviation proofs to `GlivenkoCantelliClass`. The entropy theorems are not yet proved from primitive assumptions. |
| Donsker bridge | `DonskerBridgeCertificate` | `certificate_interface` | van der Vaart & Wellner Ch. 2.5 and later Donsker theory | Extracts a stored weak-convergence proof; does not prove Donsker criteria. |
| Causal identification | `ObservedATEIdentificationBridge`, `IPWIdentificationBridge`, `AIPWDoubleRobustBridge` | `bridge_interface` | Potential-outcome / IPW / AIPW identification architecture | Projects supplied causal proofs. Measure-theoretic identification is not yet derived. |
| Causal non-vacuity | `ATEIdentificationSanityExample`, trivial AIPW/IPW examples | `non_vacuity_witness` | Sanity examples for bridge APIs | Shows the interfaces are inhabited by deterministic examples. Not a substantive causal theorem. |
| Benchmark and curation artifacts | theorem-hole tasks, SFT/DPO/GRPO manifests | `benchmark_hole` / infrastructure | Agent-system engineering | Supports evaluation and training-data construction, not mathematical theorem completion by itself. |

## Current Risk

The Lean code is not unsound merely because it contains bridge records.  The
actual risk is semantic overclaiming:

- Correct: "The repository has verified ERM deterministic reductions and
  proof-carrying interfaces for empirical-process, M/Z-estimation, causal, and
  semiparametric routes."
- Incorrect: "The repository has already proved full self-contained GC,
  Donsker, AIPW double robustness, and semiparametric normality from primitive
  probability assumptions."

## Policy For Future Milestones

1. A milestone may be marked `done` only with its claim level stated.
2. A `bridge_interface` milestone must not be described as a completed theorem.
3. A theorem promoted from VdV&W or another textbook needs a provenance card:
   source label, theorem number, assumptions, conclusion, dependency list,
   current Lean status, and non-vacuity examples where relevant.
4. Every new empirical-process theorem should enter as a theorem-hole benchmark
   first, then become a no-placeholder Lean declaration only after the primitive
   dependencies are proved or explicitly imported from mathlib.
5. `StatInference` must remain no-`sorry`, no-`admit`, no unreviewed `axiom`,
   and no `unsafe` in promoted source files.

## VdV&W Guardrails For Empirical-Process Expansion

The first pass over the VdV&W markdown confirms that the current
proof-carrying interface strategy is the safe route.  The textbook repeatedly
uses conditions that must not be collapsed into a bare theorem name during
autoformalization.

Near-term guardrails:

1. Finite-bracketing GC should be the first primitive empirical-process target.
   Theorem 2.4.1 gives the clean route from finite `L1(P)` bracketing numbers
   to a Glivenko-Cantelli class.  The current `BracketingDeviationCertificate`
   may be used as a handoff API, but the theorem itself is not yet proved.
2. Random-entropy GC is dependency-heavy.  Theorem 2.4.3 uses
   `P`-measurability, an integrable envelope, outer probability notation, and
   empirical random covering numbers.  It should remain a theorem-card or
   benchmark-hole target until the outer-probability and measurability layer is
   explicit.
3. Uniform-entropy Donsker and bracketing Donsker should not be inferred from
   GC.  Theorems 2.5.2 and 2.5.6 require separate entropy-integral,
   measurability, envelope, weak-moment, pre-Gaussian/tight-limit, and
   asymptotic-equicontinuity infrastructure.
4. VC and VC-subgraph milestones must distinguish three layers:
   combinatorics, entropy translation, and stochastic convergence.  Theorem
   2.6.4 is a covering-number result for VC classes of sets; Theorem 2.6.7 is
   the corresponding VC-subgraph function-class entropy bound; Theorem 2.6.8
   is a Donsker theorem requiring pointwise separability, pre-Gaussianity, and
   envelope tail conditions.  A benchmark seed may test certificate plumbing,
   but it must not claim these layers have been proved.
5. VC permanence lemmas are valuable but late-stage.  Lemmas 2.6.15-2.6.20
   give construction rules for finite-dimensional spaces, translates,
   transformations, products, and hull/major classes.  They should first become
   provenance-backed theorem cards before any generated Lean statement is
   promoted.

For P10.M2, acceptable progress is therefore:

- prove the deterministic bracketing endpoint inequality from VdV&W 2.4.1;
- wrap mathlib's real-valued strong law for finite endpoint families;
- expose the strong-law result as almost-sure eventual fixed-tolerance endpoint
  control, not as a deterministic all-sample rate;
- add explicit finite `L1(P)` bracketing sequence routes and benchmark seeds
  for deterministic and L1-bracketing handoffs;
- keep `BracketingDeviationCertificate` as a handoff API, not the theorem
  itself;
- do not claim finite bracketing implies GC until finite bracket covers,
  endpoint LLNs, measurability, outer-probability bookkeeping, and convergence
  mode are all formalized.

For the later VC-subgraph milestone, acceptable progress is:

- add benchmark seeds for `VCDeviationCertificate` projection and non-vacuity;
- add explicit proof-obligation metadata for VC dimension, shatter bounds,
  entropy translation, measurability, envelope/moment, and separability;
- keep every promoted Lean declaration proof-carrying and no-placeholder;
- do not claim a self-contained VC-subgraph GC or Donsker theorem until the
  above obligations are discharged by primitive Lean proofs or cited mathlib
  imports.
