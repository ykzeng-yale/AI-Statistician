import StatInference.ProbabilityMeasure.FiniteDimensional
import StatInference.EmpiricalProcess.WeakConvergence
import StatInference.EmpiricalProcess.EllInfty
import Mathlib.MeasureTheory.Measure.HasOuterApproxClosedProd

/-!
# Finite-dimensional empirical-process law wrappers

This module records the uniqueness-only finite-dimensional-distribution layer
behind VdV&W Theorem 1.4.8.  It does not state the full weak-convergence
criterion for arbitrary nets; it gives law-extensionality wrappers for
measurable process laws and the forward weak-convergence-to-FDD restriction
direction.
-/

namespace StatInference

open MeasureTheory ProbabilityTheory
open scoped BoundedContinuousFunction

variable {T Ω : Type*} {𝓧 : T -> Type*} {mΩ : MeasurableSpace Ω}
  {m𝓧 : ∀ t, MeasurableSpace (𝓧 t)}
  {X Y : (t : T) -> Ω -> 𝓧 t} {P : Measure Ω}

/--
VdV&W Lemma 1.4.1: for separable metric-type Borel spaces, the product of the
Borel sigma-fields equals the Borel sigma-field of the product topology.

This is the local empirical-process wrapper around mathlib's
`Prod.borelSpace` instance, with separability providing second countability
for pseudometric spaces.
-/
theorem vdVW141_prod_borel_eq_product_borel
    {D E : Type*} [PseudoMetricSpace D] [TopologicalSpace.SeparableSpace D]
    [MeasurableSpace D] [BorelSpace D]
    [PseudoMetricSpace E] [TopologicalSpace.SeparableSpace E]
    [MeasurableSpace E] [BorelSpace E] :
    (inferInstance : MeasurableSpace (D × E)) = borel (D × E) :=
  BorelSpace.measurable_eq

/--
VdV&W 1.4.2 product-test uniqueness layer: a finite measure on `D × E` is
determined by integrals of products `f(x) g(y)` over bounded continuous real
test functions.

This is the ordinary measure-level product-space foundation.  It reuses
mathlib's `HasOuterApproxClosed` product-measure extensionality theorem.
-/
theorem vdVW142_prod_measure_ext_of_forall_boundedContinuous_integral_mul
    {D E : Type*}
    [MeasurableSpace D] [TopologicalSpace D] [BorelSpace D] [HasOuterApproxClosed D]
    [MeasurableSpace E] [TopologicalSpace E] [BorelSpace E] [HasOuterApproxClosed E]
    {μ ν : Measure (D × E)} [IsFiniteMeasure μ] [IsFiniteMeasure ν]
    (h : ∀ (f : D →ᵇ ℝ) (g : E →ᵇ ℝ),
      ∫ p, f p.1 * g p.2 ∂μ = ∫ p, f p.1 * g p.2 ∂ν) :
    μ = ν := by
  exact Measure.ext_of_integral_mul_boundedContinuousFunction h

/--
VdV&W 1.4.2 product-law uniqueness layer: a finite measure on `D × E` is the
product `μ.prod ν` if all bounded-continuous product tests factor into the
product of their marginal integrals.
-/
theorem vdVW142_prod_measure_eq_prod_of_forall_boundedContinuous_integral_mul
    {D E : Type*}
    [MeasurableSpace D] [TopologicalSpace D] [BorelSpace D] [HasOuterApproxClosed D]
    [MeasurableSpace E] [TopologicalSpace E] [BorelSpace E] [HasOuterApproxClosed E]
    {μ : Measure D} {ν : Measure E} {ξ : Measure (D × E)}
    [IsFiniteMeasure μ] [IsFiniteMeasure ν] [IsFiniteMeasure ξ]
    (h : ∀ (f : D →ᵇ ℝ) (g : E →ᵇ ℝ),
      ∫ p, f p.1 * g p.2 ∂ξ = (∫ x, f x ∂μ) * (∫ y, g y ∂ν)) :
    ξ = μ.prod ν := by
  exact Measure.eq_prod_of_integral_mul_boundedContinuousFunction h

/--
VdV&W 1.4.8 uniqueness-only layer: a process law is determined by all of its
finite-dimensional distributions.

This is only the law-extensionality component used in the proof of the
textbook weak-convergence criterion.  It is not the full theorem 1.4.8, which
also involves arbitrary nets, separability, asymptotic measurability, tightness,
and weak convergence.
-/
theorem vdVW148_processLaw_ext_of_forall_finiteDimensional_eq
    [IsFiniteMeasure P]
    (hX : AEMeasurable (fun ω => fun t => X t ω) P)
    (hY : AEMeasurable (fun ω => fun t => Y t ω) P)
    (hFDD : ∀ I : Finset T,
      P.map (fun ω => I.restrict (fun t => X t ω)) =
        P.map (fun ω => I.restrict (fun t => Y t ω))) :
    P.map (fun ω => fun t => X t ω) =
      P.map (fun ω => fun t => Y t ω) := by
  exact
    (StatInference.ProbabilityMeasure.processLaw_eq_iff_forall_finiteDimensional_eq
      hX hY).2 hFDD

/--
VdV&W 1.4.8 uniqueness-only layer in `IdentDistrib` form: process-level
identical distribution follows from identical distribution of every
finite-dimensional restriction.

This is still only a law-extensionality foundation.  It does not assert the
full weak-convergence/FDD-converse theorem.
-/
theorem vdVW148_identDistrib_of_forall_finiteDimensional_identDistrib
    [IsFiniteMeasure P]
    (hX : AEMeasurable (fun ω => fun t => X t ω) P)
    (hY : AEMeasurable (fun ω => fun t => Y t ω) P)
    (hFDD : ∀ I : Finset T,
      IdentDistrib
        (fun ω => I.restrict (fun t => X t ω))
        (fun ω => I.restrict (fun t => Y t ω)) P P) :
    IdentDistrib (fun ω => fun t => X t ω) (fun ω => fun t => Y t ω) P P := by
  exact
    (StatInference.ProbabilityMeasure.identDistrib_iff_forall_finiteDimensional_identDistrib
      hX hY).2 hFDD

/--
VdV&W 1.4.8 forward finite-dimensional weak-convergence layer: weak
convergence of process laws implies weak convergence of every
finite-dimensional restriction.

This is the easy direction of the textbook finite-dimensional-distribution
criterion.  The converse still needs the exact VdV&W tightness/separability
and asymptotic-measurability hypotheses before it can be stated honestly.
-/
theorem vdVW148_finiteDimensional_weakConvergence_of_processLaw_weakConvergence
    {ι : Type*} {l : Filter ι}
    [∀ t, TopologicalSpace (𝓧 t)] [∀ t, OpensMeasurableSpace (𝓧 t)]
    [MeasurableSpace ((t : T) -> 𝓧 t)] [OpensMeasurableSpace ((t : T) -> 𝓧 t)]
    {μs : ι -> ProbabilityMeasure ((t : T) -> 𝓧 t)}
    {μ : ProbabilityMeasure ((t : T) -> 𝓧 t)}
    (hμ : VdVWWeakConvergenceProbabilityMeasures μs l μ)
    (I : Finset T)
    [MeasurableSpace ((t : I) -> 𝓧 t)] [BorelSpace ((t : I) -> 𝓧 t)] :
    VdVWWeakConvergenceProbabilityMeasures
      (fun n => (μs n).map ((Finset.continuous_restrict I).measurable.aemeasurable))
      l
      (μ.map ((Finset.continuous_restrict I).measurable.aemeasurable)) := by
  exact VdVWWeakConvergenceProbabilityMeasures.finiteDimensionalRestrict hμ I

/--
Forward coordinate weak-convergence layer for dependent product process laws:
weak convergence of process laws implies weak convergence of every
single-coordinate marginal law.
-/
theorem vdVW148_coordinate_weakConvergence_of_processLaw_weakConvergence
    {ι : Type*} {l : Filter ι}
    [∀ t, TopologicalSpace (𝓧 t)] [∀ t, OpensMeasurableSpace (𝓧 t)]
    [MeasurableSpace ((t : T) -> 𝓧 t)] [OpensMeasurableSpace ((t : T) -> 𝓧 t)]
    {μs : ι -> ProbabilityMeasure ((t : T) -> 𝓧 t)}
    {μ : ProbabilityMeasure ((t : T) -> 𝓧 t)}
    (hμ : VdVWWeakConvergenceProbabilityMeasures μs l μ)
    (t : T)
    [MeasurableSpace (𝓧 t)] [BorelSpace (𝓧 t)] :
    VdVWWeakConvergenceProbabilityMeasures
      (fun n => (μs n).map ((continuous_apply t).measurable.aemeasurable))
      l
      (μ.map ((continuous_apply t).measurable.aemeasurable)) := by
  exact hμ.map_continuous (continuous_apply t)

/--
Forward finite-dimensional weak-convergence layer for laws on
`ell_infty(T)`.  This is the process-space version of the easy direction of
VdV&W 1.4.8: weak convergence of `ell_infty(T)` laws implies weak convergence
of every finite coordinate restriction.
-/
theorem vdVW148_ellInfty_finiteDimensional_weakConvergence_of_processLaw_weakConvergence
    {ι : Type*} {l : Filter ι}
    [MeasurableSpace (VdVWEllInfty T)] [OpensMeasurableSpace (VdVWEllInfty T)]
    {μs : ι -> ProbabilityMeasure (VdVWEllInfty T)}
    {μ : ProbabilityMeasure (VdVWEllInfty T)}
    (hμ : VdVWWeakConvergenceProbabilityMeasures μs l μ)
    (I : Finset T)
    [MeasurableSpace (I -> ℝ)] [BorelSpace (I -> ℝ)] :
    VdVWWeakConvergenceProbabilityMeasures
      (fun n => (μs n).map
        ((VdVWEllInfty.continuous_finiteRestrict (T := T) I).measurable.aemeasurable))
      l
      (μ.map
        ((VdVWEllInfty.continuous_finiteRestrict (T := T) I).measurable.aemeasurable)) := by
  exact hμ.map_continuous (VdVWEllInfty.continuous_finiteRestrict (T := T) I)

/--
Forward coordinate weak-convergence layer for laws on `ell_infty(T)`.
Weak convergence of `ell_infty(T)` laws implies weak convergence of every
single-coordinate marginal law.
-/
theorem vdVW148_ellInfty_coordinate_weakConvergence_of_processLaw_weakConvergence
    {ι : Type*} {l : Filter ι}
    [MeasurableSpace (VdVWEllInfty T)] [OpensMeasurableSpace (VdVWEllInfty T)]
    {μs : ι -> ProbabilityMeasure (VdVWEllInfty T)}
    {μ : ProbabilityMeasure (VdVWEllInfty T)}
    (hμ : VdVWWeakConvergenceProbabilityMeasures μs l μ)
    (t : T) :
    VdVWWeakConvergenceProbabilityMeasures
      (fun n => (μs n).map
        ((VdVWEllInfty.evalCLM (T := T) t).continuous.measurable.aemeasurable))
      l
      (μ.map
        ((VdVWEllInfty.evalCLM (T := T) t).continuous.measurable.aemeasurable)) := by
  exact hμ.map_continuous (VdVWEllInfty.evalCLM (T := T) t).continuous

/--
Forward finite-dimensional asymptotic-tightness layer for laws on
`ell_infty(T)`.  Ordinary asymptotic tightness of `ell_infty(T)` laws implies
ordinary asymptotic tightness of every finite-coordinate restriction.

This is only the measure-level forward FDD tightness direction; the
arbitrary-index VdV&W converse still needs separability, process
asymptotic-tightness, and nonmeasurable arbitrary-map primitives.
-/
theorem vdVW148_ellInfty_finiteDimensional_asymptoticallyTight_of_processLaw_asymptoticallyTight
    {ι : Type*} {l : Filter ι}
    [MeasurableSpace (VdVWEllInfty T)] [OpensMeasurableSpace (VdVWEllInfty T)]
    {μs : ι -> ProbabilityMeasure (VdVWEllInfty T)}
    (hμ : VdVWProbabilityMeasuresAsymptoticallyTight μs l)
    (I : Finset T)
    [MeasurableSpace (I -> ℝ)] [BorelSpace (I -> ℝ)] :
    VdVWProbabilityMeasuresAsymptoticallyTight
      (fun n => (μs n).map
        ((VdVWEllInfty.continuous_finiteRestrict (T := T) I).measurable.aemeasurable))
      l := by
  exact hμ.map_continuous (VdVWEllInfty.continuous_finiteRestrict (T := T) I)

/--
Forward coordinate asymptotic-tightness layer for laws on `ell_infty(T)`.
Ordinary asymptotic tightness of `ell_infty(T)` laws implies ordinary
asymptotic tightness of every single-coordinate marginal law.
-/
theorem vdVW148_ellInfty_coordinate_asymptoticallyTight_of_processLaw_asymptoticallyTight
    {ι : Type*} {l : Filter ι}
    [MeasurableSpace (VdVWEllInfty T)] [OpensMeasurableSpace (VdVWEllInfty T)]
    {μs : ι -> ProbabilityMeasure (VdVWEllInfty T)}
    (hμ : VdVWProbabilityMeasuresAsymptoticallyTight μs l)
    (t : T) :
    VdVWProbabilityMeasuresAsymptoticallyTight
      (fun n => (μs n).map
        ((VdVWEllInfty.evalCLM (T := T) t).continuous.measurable.aemeasurable))
      l := by
  exact hμ.map_continuous (VdVWEllInfty.evalCLM (T := T) t).continuous

/--
Forward coordinate asymptotic-tightness layer for dependent product process
laws: ordinary asymptotic tightness of process laws implies ordinary
asymptotic tightness of every single-coordinate marginal law.
-/
theorem vdVW148_coordinate_asymptoticallyTight_of_processLaw_asymptoticallyTight
    {ι : Type*} {l : Filter ι}
    [∀ t, TopologicalSpace (𝓧 t)] [∀ t, OpensMeasurableSpace (𝓧 t)]
    [MeasurableSpace ((t : T) -> 𝓧 t)] [OpensMeasurableSpace ((t : T) -> 𝓧 t)]
    {μs : ι -> ProbabilityMeasure ((t : T) -> 𝓧 t)}
    (hμ : VdVWProbabilityMeasuresAsymptoticallyTight μs l)
    (t : T)
    [MeasurableSpace (𝓧 t)] [BorelSpace (𝓧 t)] [T2Space (𝓧 t)] :
    VdVWProbabilityMeasuresAsymptoticallyTight
      (fun n => (μs n).map ((continuous_apply t).measurable.aemeasurable))
      l := by
  exact hμ.map_continuous (continuous_apply t)

/--
For finite index sets, mapping an `ell_infty(T)` law to the ordinary finite
product and back by the finite product equivalence recovers the original law.
-/
@[simp]
theorem vdVW148_ellInfty_map_finiteContinuousLinearEquiv_symm_map
    [Fintype T]
    [MeasurableSpace (VdVWEllInfty T)] [BorelSpace (VdVWEllInfty T)]
    [MeasurableSpace (T -> ℝ)] [BorelSpace (T -> ℝ)]
    (ν : ProbabilityMeasure (VdVWEllInfty T)) :
    ((ν.map
          ((VdVWEllInfty.finiteContinuousLinearEquiv (T := T)).continuous.measurable.aemeasurable)).map
        ((VdVWEllInfty.finiteContinuousLinearEquiv (T := T)).symm.continuous.measurable.aemeasurable)) =
      ν := by
  let e := VdVWEllInfty.finiteContinuousLinearEquiv (T := T)
  ext s hs
  change (Measure.map e.symm (Measure.map e (ν : Measure (VdVWEllInfty T)))) s =
    (ν : Measure (VdVWEllInfty T)) s
  rw [Measure.map_map e.symm.continuous.measurable e.continuous.measurable]
  simp

/--
Finite-index converse for the `ell_infty(T)` finite-dimensional criterion.
When `T` is finite, weak convergence after identifying `ell_infty(T)` with the
ordinary finite product `T -> ℝ` implies weak convergence of the original
`ell_infty(T)` laws.

This is only the finite-index converse.  The arbitrary-index VdV&W 1.4.8
converse still needs the textbook separability, tightness, asymptotic
measurability, and process primitives.
-/
theorem vdVW148_ellInfty_weakConvergence_of_finiteProduct_weakConvergence_finite
    {ι : Type*} {l : Filter ι}
    [Fintype T]
    [MeasurableSpace (VdVWEllInfty T)] [OpensMeasurableSpace (VdVWEllInfty T)]
    [BorelSpace (VdVWEllInfty T)]
    [MeasurableSpace (T -> ℝ)] [BorelSpace (T -> ℝ)]
    {μs : ι -> ProbabilityMeasure (VdVWEllInfty T)}
    {μ : ProbabilityMeasure (VdVWEllInfty T)}
    (hμ : VdVWWeakConvergenceProbabilityMeasures
      (fun n => (μs n).map
        ((VdVWEllInfty.finiteContinuousLinearEquiv (T := T)).continuous.measurable.aemeasurable))
      l
      (μ.map
        ((VdVWEllInfty.finiteContinuousLinearEquiv (T := T)).continuous.measurable.aemeasurable))) :
    VdVWWeakConvergenceProbabilityMeasures μs l μ := by
  let e := VdVWEllInfty.finiteContinuousLinearEquiv (T := T)
  have hback := hμ.map_continuous e.symm.continuous
  simpa [e] using hback

/--
Finite-index weak-convergence criterion for `ell_infty(T)`.

When the index set is finite, the finite-dimensional map given by the
canonical continuous linear equivalence is a genuine equivalence, so weak
convergence of `ell_infty(T)` laws is equivalent to weak convergence of the
ordinary finite-product image laws.  This is the finite-index version only,
not the arbitrary-index VdV&W 1.4.8 converse.
-/
theorem vdVW148_ellInfty_weakConvergence_iff_finiteProduct_weakConvergence_finite
    {ι : Type*} {l : Filter ι}
    [Fintype T]
    [MeasurableSpace (VdVWEllInfty T)] [OpensMeasurableSpace (VdVWEllInfty T)]
    [BorelSpace (VdVWEllInfty T)]
    [MeasurableSpace (T -> ℝ)] [BorelSpace (T -> ℝ)]
    {μs : ι -> ProbabilityMeasure (VdVWEllInfty T)}
    {μ : ProbabilityMeasure (VdVWEllInfty T)} :
    VdVWWeakConvergenceProbabilityMeasures μs l μ ↔
      VdVWWeakConvergenceProbabilityMeasures
        (fun n => (μs n).map
          ((VdVWEllInfty.finiteContinuousLinearEquiv (T := T)).continuous.measurable.aemeasurable))
        l
        (μ.map
          ((VdVWEllInfty.finiteContinuousLinearEquiv (T := T)).continuous.measurable.aemeasurable)) := by
  constructor
  · intro h
    exact h.map_continuous (VdVWEllInfty.finiteContinuousLinearEquiv (T := T)).continuous
  · intro h
    exact
      vdVW148_ellInfty_weakConvergence_of_finiteProduct_weakConvergence_finite
        (T := T) h

/--
Direct finite-index measure-level converse: weak convergence of probability
measures on the ordinary finite product `T -> ℝ` pushes back to weak
convergence of their corresponding `ell_infty(T)` laws.

This is a convenient entry point for finite-dimensional process-law arguments.
It is still finite-index only, not the arbitrary-index VdV&W 1.4.8 converse.
-/
theorem vdVW148_ellInfty_map_symm_weakConvergence_of_finiteProduct_weakConvergence_finite
    {ι : Type*} {l : Filter ι}
    [Fintype T]
    [MeasurableSpace (VdVWEllInfty T)] [OpensMeasurableSpace (VdVWEllInfty T)]
    [BorelSpace (VdVWEllInfty T)]
    [MeasurableSpace (T -> ℝ)] [BorelSpace (T -> ℝ)]
    {νs : ι -> ProbabilityMeasure (T -> ℝ)}
    {ν : ProbabilityMeasure (T -> ℝ)}
    (hν : VdVWWeakConvergenceProbabilityMeasures νs l ν) :
    VdVWWeakConvergenceProbabilityMeasures
      (fun n => (νs n).map
        ((VdVWEllInfty.finiteContinuousLinearEquiv (T := T)).symm.continuous.measurable.aemeasurable))
      l
      (ν.map
        ((VdVWEllInfty.finiteContinuousLinearEquiv (T := T)).symm.continuous.measurable.aemeasurable)) :=
  hν.map_continuous (VdVWEllInfty.finiteContinuousLinearEquiv (T := T)).symm.continuous

/--
Finite-index converse for ordinary measure-level asymptotic tightness on
`ell_infty(T)`: if the finite-product image laws are asymptotically tight,
then the original `ell_infty(T)` laws are asymptotically tight.

This is finite-index only.  The arbitrary-index process asymptotic-tightness
criterion remains a separate VdV&W primitive.
-/
theorem vdVW148_ellInfty_asymptoticallyTight_of_finiteProduct_asymptoticallyTight_finite
    {ι : Type*} {l : Filter ι}
    [Fintype T]
    [MeasurableSpace (VdVWEllInfty T)] [OpensMeasurableSpace (VdVWEllInfty T)]
    [BorelSpace (VdVWEllInfty T)]
    [MeasurableSpace (T -> ℝ)] [BorelSpace (T -> ℝ)]
    {μs : ι -> ProbabilityMeasure (VdVWEllInfty T)}
    (hμ : VdVWProbabilityMeasuresAsymptoticallyTight
      (fun n => (μs n).map
        ((VdVWEllInfty.finiteContinuousLinearEquiv (T := T)).continuous.measurable.aemeasurable))
      l) :
    VdVWProbabilityMeasuresAsymptoticallyTight μs l := by
  let e := VdVWEllInfty.finiteContinuousLinearEquiv (T := T)
  have hback := hμ.map_continuous e.symm.continuous
  simpa [e] using hback

/--
Direct finite-index measure-level asymptotic-tightness pushback: ordinary
asymptotic tightness of probability measures on the finite product `T -> ℝ`
pushes back to their corresponding `ell_infty(T)` laws.
-/
theorem vdVW148_ellInfty_map_symm_asymptoticallyTight_of_finiteProduct_asymptoticallyTight_finite
    {ι : Type*} {l : Filter ι}
    [Fintype T]
    [MeasurableSpace (VdVWEllInfty T)] [OpensMeasurableSpace (VdVWEllInfty T)]
    [BorelSpace (VdVWEllInfty T)]
    [MeasurableSpace (T -> ℝ)] [BorelSpace (T -> ℝ)]
    {νs : ι -> ProbabilityMeasure (T -> ℝ)}
    (hν : VdVWProbabilityMeasuresAsymptoticallyTight νs l) :
    VdVWProbabilityMeasuresAsymptoticallyTight
      (fun n => (νs n).map
        ((VdVWEllInfty.finiteContinuousLinearEquiv (T := T)).symm.continuous.measurable.aemeasurable))
      l :=
  hν.map_continuous (VdVWEllInfty.finiteContinuousLinearEquiv (T := T)).symm.continuous

/--
Finite-index asymptotic-tightness criterion for `ell_infty(T)`.

For finite `T`, ordinary asymptotic tightness of `ell_infty(T)` laws is
equivalent to asymptotic tightness of the finite-product image laws under the
canonical continuous linear equivalence.  This is a finite-index support
theorem and does not assert the arbitrary-index VdV&W tightness criterion.
-/
theorem vdVW148_ellInfty_asymptoticallyTight_iff_finiteProduct_asymptoticallyTight_finite
    {ι : Type*} {l : Filter ι}
    [Fintype T]
    [MeasurableSpace (VdVWEllInfty T)] [OpensMeasurableSpace (VdVWEllInfty T)]
    [BorelSpace (VdVWEllInfty T)]
    [MeasurableSpace (T -> ℝ)] [BorelSpace (T -> ℝ)]
    {μs : ι -> ProbabilityMeasure (VdVWEllInfty T)} :
    VdVWProbabilityMeasuresAsymptoticallyTight μs l ↔
      VdVWProbabilityMeasuresAsymptoticallyTight
        (fun n => (μs n).map
          ((VdVWEllInfty.finiteContinuousLinearEquiv (T := T)).continuous.measurable.aemeasurable))
        l := by
  constructor
  · intro h
    exact h.map_continuous (VdVWEllInfty.finiteContinuousLinearEquiv (T := T)).continuous
  · intro h
    exact
      vdVW148_ellInfty_asymptoticallyTight_of_finiteProduct_asymptoticallyTight_finite
        (T := T) h

/-- Coordinate law of a dependent-product-valued random element. -/
theorem vdVW148_coordinate_hasLaw
    [MeasurableSpace Ω]
    [∀ t, TopologicalSpace (𝓧 t)] [∀ t, OpensMeasurableSpace (𝓧 t)]
    [MeasurableSpace ((t : T) -> 𝓧 t)] [OpensMeasurableSpace ((t : T) -> 𝓧 t)]
    {X : Ω -> (t : T) -> 𝓧 t} {P : Measure Ω}
    {μ : Measure ((t : T) -> 𝓧 t)}
    (hX : HasLaw X μ P) (t : T) [BorelSpace (𝓧 t)] :
    HasLaw
      (fun ω => X ω t)
      (μ.map (fun x => x t))
      P := by
  simpa [Function.comp_def] using
    (HasLaw.comp
      (Y := fun x : (t : T) -> 𝓧 t => x t)
      (ν := μ.map (fun x : (t : T) -> 𝓧 t => x t))
      { aemeasurable := (continuous_apply t).measurable.aemeasurable
        map_eq := rfl }
      hX)

/--
Identical distribution of dependent-product-valued random elements implies
identical single-coordinate laws.
-/
theorem vdVW148_coordinate_identDistrib
    [MeasurableSpace Ω] [MeasurableSpace Ω']
    [∀ t, TopologicalSpace (𝓧 t)] [∀ t, OpensMeasurableSpace (𝓧 t)]
    [MeasurableSpace ((t : T) -> 𝓧 t)] [OpensMeasurableSpace ((t : T) -> 𝓧 t)]
    {X : Ω -> (t : T) -> 𝓧 t} {Y : Ω' -> (t : T) -> 𝓧 t}
    {P : Measure Ω} {Q : Measure Ω'}
    (hXY : IdentDistrib X Y P Q) (t : T) [BorelSpace (𝓧 t)] :
    IdentDistrib
      (fun ω => X ω t)
      (fun ω' => Y ω' t)
      P Q := by
  simpa [Function.comp_def] using
    hXY.comp (continuous_apply t).measurable

/--
Coordinate form of the forward FDD implication for dependent product process
random elements.
-/
theorem vdVW148_coordinate_tendstoInDistribution
    {ι : Type*} {Ω : ι -> Type*} {Ω' : Type*}
    {mΩ : (i : ι) -> MeasurableSpace (Ω i)}
    {μ : (i : ι) -> @Measure (Ω i) (mΩ i)}
    [∀ i, IsProbabilityMeasure (μ i)]
    {mΩ' : MeasurableSpace Ω'} {μ' : @Measure Ω' mΩ'}
    [IsProbabilityMeasure μ']
    [∀ t, TopologicalSpace (𝓧 t)] [∀ t, OpensMeasurableSpace (𝓧 t)]
    [MeasurableSpace ((t : T) -> 𝓧 t)] [OpensMeasurableSpace ((t : T) -> 𝓧 t)]
    {X : (i : ι) -> Ω i -> (t : T) -> 𝓧 t}
    {Z : Ω' -> (t : T) -> 𝓧 t} {l : Filter ι}
    (hX : TendstoInDistribution X l Z μ μ')
    (t : T) [BorelSpace (𝓧 t)] :
    TendstoInDistribution
      (fun i ω => X i ω t)
      l
      (fun ω' => Z ω' t)
      μ μ' := by
  simpa [Function.comp_def] using
    hX.continuous_comp (continuous_apply t)

/-- Finite-dimensional law of an `ell_infty(T)`-valued random element. -/
theorem vdVW148_ellInfty_finiteDimensional_hasLaw
    [MeasurableSpace Ω] [MeasurableSpace (VdVWEllInfty T)]
    [BorelSpace (VdVWEllInfty T)]
    {X : Ω -> VdVWEllInfty T} {P : Measure Ω}
    {μ : Measure (VdVWEllInfty T)}
    (hX : HasLaw X μ P)
    (I : Finset T)
    [MeasurableSpace (I -> ℝ)] [BorelSpace (I -> ℝ)] :
    HasLaw
      (VdVWEllInfty.finiteRestrict I ∘ X)
      (μ.map (VdVWEllInfty.finiteRestrict I))
      P := by
  refine HasLaw.comp ?_ hX
  exact
    { aemeasurable :=
        ((VdVWEllInfty.continuous_finiteRestrict (T := T) I).measurable.aemeasurable)
      map_eq := rfl }

/-- Coordinate law of an `ell_infty(T)`-valued random element. -/
theorem vdVW148_ellInfty_coordinate_hasLaw
    [MeasurableSpace Ω] [MeasurableSpace (VdVWEllInfty T)]
    [BorelSpace (VdVWEllInfty T)]
    {X : Ω -> VdVWEllInfty T} {P : Measure Ω}
    {μ : Measure (VdVWEllInfty T)}
    (hX : HasLaw X μ P) (t : T) :
    HasLaw
      (fun ω => X ω t)
      (μ.map (VdVWEllInfty.evalCLM t))
      P := by
  simpa [Function.comp_def] using
    (HasLaw.comp
      (Y := VdVWEllInfty.evalCLM (T := T) t)
      (ν := μ.map (VdVWEllInfty.evalCLM t))
      { aemeasurable :=
          ((VdVWEllInfty.evalCLM (T := T) t).continuous.measurable.aemeasurable)
        map_eq := rfl }
      hX)

/-- Identical distribution of `ell_infty(T)` processes implies identical single-coordinate laws. -/
theorem vdVW148_ellInfty_coordinate_identDistrib
    [MeasurableSpace Ω] [MeasurableSpace Ω']
    [MeasurableSpace (VdVWEllInfty T)] [BorelSpace (VdVWEllInfty T)]
    {X : Ω -> VdVWEllInfty T} {Y : Ω' -> VdVWEllInfty T}
    {P : Measure Ω} {Q : Measure Ω'}
    (hXY : IdentDistrib X Y P Q) (t : T) :
    IdentDistrib
      (fun ω => X ω t)
      (fun ω' => Y ω' t)
      P Q := by
  simpa [Function.comp_def] using
    hXY.comp (VdVWEllInfty.evalCLM (T := T) t).continuous.measurable

/-- Identical distribution of `ell_infty(T)` processes implies identical FDDs. -/
theorem vdVW148_ellInfty_finiteDimensional_identDistrib
    [MeasurableSpace Ω] [MeasurableSpace Ω']
    [MeasurableSpace (VdVWEllInfty T)] [BorelSpace (VdVWEllInfty T)]
    {X : Ω -> VdVWEllInfty T} {Y : Ω' -> VdVWEllInfty T}
    {P : Measure Ω} {Q : Measure Ω'}
    (hXY : IdentDistrib X Y P Q)
    (I : Finset T)
    [MeasurableSpace (I -> ℝ)] [BorelSpace (I -> ℝ)] :
    IdentDistrib
      (VdVWEllInfty.finiteRestrict I ∘ X)
      (VdVWEllInfty.finiteRestrict I ∘ Y)
      P Q :=
  hXY.comp (VdVWEllInfty.measurable_finiteRestrict (T := T) I)

/--
Random-variable form of the forward FDD implication for `ell_infty(T)`:
convergence in distribution of `ell_infty(T)`-valued random elements implies
convergence in distribution of every finite coordinate restriction.

This is still the easy direction of VdV&W 1.4.8.  The FDD converse requires
the separate tightness/separability/asymptotic-measurability hypotheses.
-/
theorem vdVW148_ellInfty_finiteDimensional_tendstoInDistribution
    {ι : Type*} {Ω : ι -> Type*} {Ω' : Type*}
    {mΩ : (i : ι) -> MeasurableSpace (Ω i)}
    {μ : (i : ι) -> @Measure (Ω i) (mΩ i)}
    [∀ i, IsProbabilityMeasure (μ i)]
    {mΩ' : MeasurableSpace Ω'} {μ' : @Measure Ω' mΩ'}
    [IsProbabilityMeasure μ']
    [MeasurableSpace (VdVWEllInfty T)] [OpensMeasurableSpace (VdVWEllInfty T)]
    {X : (i : ι) -> Ω i -> VdVWEllInfty T}
    {Z : Ω' -> VdVWEllInfty T} {l : Filter ι}
    (hX : TendstoInDistribution X l Z μ μ')
    (I : Finset T)
    [MeasurableSpace (I -> ℝ)] [BorelSpace (I -> ℝ)] :
    TendstoInDistribution
      (fun i => VdVWEllInfty.finiteRestrict I ∘ X i)
      l
      (VdVWEllInfty.finiteRestrict I ∘ Z)
      μ μ' :=
  hX.continuous_comp (VdVWEllInfty.continuous_finiteRestrict (T := T) I)

/--
Coordinate form of the forward FDD implication for `ell_infty(T)`: convergence
in distribution of `ell_infty(T)`-valued random elements implies convergence
in distribution of every single coordinate.
-/
theorem vdVW148_ellInfty_coordinate_tendstoInDistribution
    {ι : Type*} {Ω : ι -> Type*} {Ω' : Type*}
    {mΩ : (i : ι) -> MeasurableSpace (Ω i)}
    {μ : (i : ι) -> @Measure (Ω i) (mΩ i)}
    [∀ i, IsProbabilityMeasure (μ i)]
    {mΩ' : MeasurableSpace Ω'} {μ' : @Measure Ω' mΩ'}
    [IsProbabilityMeasure μ']
    [MeasurableSpace (VdVWEllInfty T)] [OpensMeasurableSpace (VdVWEllInfty T)]
    {X : (i : ι) -> Ω i -> VdVWEllInfty T}
    {Z : Ω' -> VdVWEllInfty T} {l : Filter ι}
    (hX : TendstoInDistribution X l Z μ μ')
    (t : T) :
    TendstoInDistribution
      (fun i ω => X i ω t)
      l
      (fun ω' => Z ω' t)
      μ μ' := by
  simpa [Function.comp_def] using
    hX.continuous_comp (VdVWEllInfty.evalCLM (T := T) t).continuous

/--
Finite-dimensional law of a bounded raw process, routed through its
`ell_infty(T)` process law.  This is the raw-process version of the forward
FDD handoff used in VdV&W 1.4.8.
-/
theorem vdVW148_boundedProcess_finiteDimensional_hasLaw
    [MeasurableSpace Ω] [MeasurableSpace (VdVWEllInfty T)]
    [BorelSpace (VdVWEllInfty T)]
    {X : Ω -> T -> ℝ} (hbounded : VdVWEllInfty.IsBoundedSamplePath X)
    {P : Measure Ω} {μ : Measure (VdVWEllInfty T)}
    (hX : HasLaw (VdVWEllInfty.processMap X hbounded) μ P)
    (I : Finset T)
    [MeasurableSpace (I -> ℝ)] [BorelSpace (I -> ℝ)] :
    HasLaw
      (fun ω => I.restrict (X ω))
      (μ.map (VdVWEllInfty.finiteRestrict I))
      P := by
  simpa [Function.comp_def, VdVWEllInfty.finiteRestrict, VdVWEllInfty.processMap]
    using
      (vdVW148_ellInfty_finiteDimensional_hasLaw
        (T := T) (Ω := Ω) (X := VdVWEllInfty.processMap X hbounded)
        (P := P) (μ := μ) hX I)

/--
Single-coordinate law of a bounded raw process, routed through its
`ell_infty(T)` process law.
-/
theorem vdVW148_boundedProcess_coordinate_hasLaw
    [MeasurableSpace Ω] [MeasurableSpace (VdVWEllInfty T)]
    [BorelSpace (VdVWEllInfty T)]
    {X : Ω -> T -> ℝ} (hbounded : VdVWEllInfty.IsBoundedSamplePath X)
    {P : Measure Ω} {μ : Measure (VdVWEllInfty T)}
    (hX : HasLaw (VdVWEllInfty.processMap X hbounded) μ P)
    (t : T) :
    HasLaw
      (fun ω => X ω t)
      (μ.map (VdVWEllInfty.evalCLM t))
      P := by
  simpa [Function.comp_def, VdVWEllInfty.processMap] using
    (vdVW148_ellInfty_coordinate_hasLaw
      (T := T) (Ω := Ω) (X := VdVWEllInfty.processMap X hbounded)
      (P := P) (μ := μ) hX t)

/--
Identical `ell_infty(T)` laws of bounded raw processes imply identical
finite-dimensional distributions of the original coordinate processes.
-/
theorem vdVW148_boundedProcess_finiteDimensional_identDistrib
    [MeasurableSpace Ω] [MeasurableSpace Ω']
    [MeasurableSpace (VdVWEllInfty T)] [BorelSpace (VdVWEllInfty T)]
    {X : Ω -> T -> ℝ} {Y : Ω' -> T -> ℝ}
    (hXbounded : VdVWEllInfty.IsBoundedSamplePath X)
    (hYbounded : VdVWEllInfty.IsBoundedSamplePath Y)
    {P : Measure Ω} {Q : Measure Ω'}
    (hXY : IdentDistrib
      (VdVWEllInfty.processMap X hXbounded)
      (VdVWEllInfty.processMap Y hYbounded) P Q)
    (I : Finset T)
    [MeasurableSpace (I -> ℝ)] [BorelSpace (I -> ℝ)] :
    IdentDistrib
      (fun ω => I.restrict (X ω))
      (fun ω => I.restrict (Y ω))
      P Q := by
  simpa [Function.comp_def, VdVWEllInfty.finiteRestrict, VdVWEllInfty.processMap]
    using
      (vdVW148_ellInfty_finiteDimensional_identDistrib
        (T := T) (Ω := Ω) (Ω' := Ω')
        (X := VdVWEllInfty.processMap X hXbounded)
        (Y := VdVWEllInfty.processMap Y hYbounded)
        (P := P) (Q := Q) hXY I)

/--
Identical `ell_infty(T)` laws of bounded raw processes imply identical
single-coordinate distributions of the original coordinate processes.
-/
theorem vdVW148_boundedProcess_coordinate_identDistrib
    [MeasurableSpace Ω] [MeasurableSpace Ω']
    [MeasurableSpace (VdVWEllInfty T)] [BorelSpace (VdVWEllInfty T)]
    {X : Ω -> T -> ℝ} {Y : Ω' -> T -> ℝ}
    (hXbounded : VdVWEllInfty.IsBoundedSamplePath X)
    (hYbounded : VdVWEllInfty.IsBoundedSamplePath Y)
    {P : Measure Ω} {Q : Measure Ω'}
    (hXY : IdentDistrib
      (VdVWEllInfty.processMap X hXbounded)
      (VdVWEllInfty.processMap Y hYbounded) P Q)
    (t : T) :
    IdentDistrib
      (fun ω => X ω t)
      (fun ω => Y ω t)
      P Q := by
  simpa [Function.comp_def, VdVWEllInfty.processMap] using
    (vdVW148_ellInfty_coordinate_identDistrib
      (T := T) (Ω := Ω) (Ω' := Ω')
      (X := VdVWEllInfty.processMap X hXbounded)
      (Y := VdVWEllInfty.processMap Y hYbounded)
      (P := P) (Q := Q) hXY t)

/--
Raw-process form of the forward FDD implication: convergence in distribution
of the associated bounded `ell_infty(T)` processes implies convergence in
distribution of every finite coordinate restriction.
-/
theorem vdVW148_boundedProcess_finiteDimensional_tendstoInDistribution
    {ι : Type*} {Ω : ι -> Type*} {Ω' : Type*}
    {mΩ : (i : ι) -> MeasurableSpace (Ω i)}
    {μ : (i : ι) -> @Measure (Ω i) (mΩ i)}
    [∀ i, IsProbabilityMeasure (μ i)]
    {mΩ' : MeasurableSpace Ω'} {μ' : @Measure Ω' mΩ'}
    [IsProbabilityMeasure μ']
    [MeasurableSpace (VdVWEllInfty T)] [OpensMeasurableSpace (VdVWEllInfty T)]
    {X : (i : ι) -> Ω i -> T -> ℝ} {Z : Ω' -> T -> ℝ}
    (hXbounded : ∀ i, VdVWEllInfty.IsBoundedSamplePath (X i))
    (hZbounded : VdVWEllInfty.IsBoundedSamplePath Z)
    {l : Filter ι}
    (hX : TendstoInDistribution
      (fun i => VdVWEllInfty.processMap (X i) (hXbounded i))
      l
      (VdVWEllInfty.processMap Z hZbounded)
      μ μ')
    (I : Finset T)
    [MeasurableSpace (I -> ℝ)] [BorelSpace (I -> ℝ)] :
    TendstoInDistribution
      (fun i ω => I.restrict (X i ω))
      l
      (fun ω => I.restrict (Z ω))
      μ μ' := by
  simpa [Function.comp_def, VdVWEllInfty.finiteRestrict, VdVWEllInfty.processMap]
    using
      (vdVW148_ellInfty_finiteDimensional_tendstoInDistribution
        (T := T) (Ω := Ω) (Ω' := Ω') (μ := μ) (μ' := μ')
        (X := fun i => VdVWEllInfty.processMap (X i) (hXbounded i))
        (Z := VdVWEllInfty.processMap Z hZbounded) (l := l) hX I)

/--
Raw-process coordinate form of the forward FDD implication: convergence in
distribution of the associated bounded `ell_infty(T)` processes implies
convergence in distribution of every single coordinate.
-/
theorem vdVW148_boundedProcess_coordinate_tendstoInDistribution
    {ι : Type*} {Ω : ι -> Type*} {Ω' : Type*}
    {mΩ : (i : ι) -> MeasurableSpace (Ω i)}
    {μ : (i : ι) -> @Measure (Ω i) (mΩ i)}
    [∀ i, IsProbabilityMeasure (μ i)]
    {mΩ' : MeasurableSpace Ω'} {μ' : @Measure Ω' mΩ'}
    [IsProbabilityMeasure μ']
    [MeasurableSpace (VdVWEllInfty T)] [OpensMeasurableSpace (VdVWEllInfty T)]
    {X : (i : ι) -> Ω i -> T -> ℝ} {Z : Ω' -> T -> ℝ}
    (hXbounded : ∀ i, VdVWEllInfty.IsBoundedSamplePath (X i))
    (hZbounded : VdVWEllInfty.IsBoundedSamplePath Z)
    {l : Filter ι}
    (hX : TendstoInDistribution
      (fun i => VdVWEllInfty.processMap (X i) (hXbounded i))
      l
      (VdVWEllInfty.processMap Z hZbounded)
      μ μ')
    (t : T) :
    TendstoInDistribution
      (fun i ω => X i ω t)
      l
      (fun ω => Z ω t)
      μ μ' := by
  simpa [Function.comp_def, VdVWEllInfty.processMap] using
    (vdVW148_ellInfty_coordinate_tendstoInDistribution
      (T := T) (Ω := Ω) (Ω' := Ω') (μ := μ) (μ' := μ')
      (X := fun i => VdVWEllInfty.processMap (X i) (hXbounded i))
      (Z := VdVWEllInfty.processMap Z hZbounded) (l := l) hX t)

/--
Raw finite-dimensional laws can be transported directly to the corresponding
finite-coordinate restriction of the bounded `ell_infty(T)` process map.

This avoids assuming a full `ell_infty(T)` process law when only the selected
finite vector has already been identified.
-/
theorem vdVW148_boundedProcess_finiteRestrict_hasLaw_of_hasLaw
    [MeasurableSpace Ω]
    {X : Ω -> T -> ℝ} (hbounded : VdVWEllInfty.IsBoundedSamplePath X)
    {P : Measure Ω} (I : Finset T) {ν : Measure (I -> ℝ)}
    [MeasurableSpace (I -> ℝ)]
    (hX : HasLaw (fun ω => fun t : I => X ω t.1) ν P) :
    HasLaw
      (fun ω => VdVWEllInfty.finiteRestrict I
        (VdVWEllInfty.processMap X hbounded ω))
      ν P := by
  exact hX.congr (Filter.Eventually.of_forall fun ω => by
    ext t
    rfl)

/--
Raw finite-dimensional identical distributions transport to the corresponding
finite-coordinate restrictions of bounded `ell_infty(T)` process maps.
-/
theorem vdVW148_boundedProcess_finiteRestrict_identDistrib_of_identDistrib
    [MeasurableSpace Ω] [MeasurableSpace Ω']
    {X : Ω -> T -> ℝ} {Y : Ω' -> T -> ℝ}
    (hXbounded : VdVWEllInfty.IsBoundedSamplePath X)
    (hYbounded : VdVWEllInfty.IsBoundedSamplePath Y)
    {P : Measure Ω} {Q : Measure Ω'} (I : Finset T)
    [MeasurableSpace (I -> ℝ)]
    (hXY : IdentDistrib
      (fun ω => fun t : I => X ω t.1)
      (fun ω => fun t : I => Y ω t.1) P Q) :
    IdentDistrib
      (fun ω => VdVWEllInfty.finiteRestrict I
        (VdVWEllInfty.processMap X hXbounded ω))
      (fun ω => VdVWEllInfty.finiteRestrict I
        (VdVWEllInfty.processMap Y hYbounded ω))
      P Q := by
  have hXeq :
      (fun ω => fun t : I => X ω t.1)
        =ᵐ[P] fun ω => VdVWEllInfty.finiteRestrict I
          (VdVWEllInfty.processMap X hXbounded ω) :=
    Filter.Eventually.of_forall fun ω => by
      ext t
      rfl
  have hYeq :
      (fun ω => fun t : I => Y ω t.1)
        =ᵐ[Q] fun ω => VdVWEllInfty.finiteRestrict I
          (VdVWEllInfty.processMap Y hYbounded ω) :=
    Filter.Eventually.of_forall fun ω => by
      ext t
      rfl
  exact
    ((IdentDistrib.of_ae_eq hXY.aemeasurable_fst hXeq).symm).trans
      (hXY.trans (IdentDistrib.of_ae_eq hXY.aemeasurable_snd hYeq))

/--
Raw finite-dimensional convergence in distribution transports to the
finite-coordinate restrictions of bounded `ell_infty(T)` process maps.

This is still only a finite-dimensional FDD support lemma; it does not assert
the arbitrary-index VdV&W 1.4.8 converse.
-/
theorem vdVW148_boundedProcess_finiteRestrict_tendstoInDistribution_of_tendstoInDistribution
    {ι : Type*} {Ω : ι -> Type*} {Ω' : Type*}
    {mΩ : (i : ι) -> MeasurableSpace (Ω i)}
    {μ : (i : ι) -> @Measure (Ω i) (mΩ i)}
    [∀ i, IsProbabilityMeasure (μ i)]
    {mΩ' : MeasurableSpace Ω'} {μ' : @Measure Ω' mΩ'}
    [IsProbabilityMeasure μ']
    {X : (i : ι) -> Ω i -> T -> ℝ} {Z : Ω' -> T -> ℝ}
    (hXbounded : ∀ i, VdVWEllInfty.IsBoundedSamplePath (X i))
    (hZbounded : VdVWEllInfty.IsBoundedSamplePath Z)
    (I : Finset T) [MeasurableSpace (I -> ℝ)] [BorelSpace (I -> ℝ)]
    {l : Filter ι}
    (hX : TendstoInDistribution
      (fun i ω => fun t : I => X i ω t.1)
      l
      (fun ω => fun t : I => Z ω t.1)
      μ μ') :
    TendstoInDistribution
      (fun i ω => VdVWEllInfty.finiteRestrict I
        (VdVWEllInfty.processMap (X i) (hXbounded i) ω))
      l
      (fun ω => VdVWEllInfty.finiteRestrict I
        (VdVWEllInfty.processMap Z hZbounded ω))
      μ μ' := by
  refine hX.congr ?_ ?_
  · intro i
    exact Filter.Eventually.of_forall fun ω => by
      ext t
      rfl
  · exact Filter.Eventually.of_forall fun ω => by
      ext t
      rfl

/--
Finite-index law converse for bounded raw processes: a law for the ordinary
finite product process induces the corresponding `ell_infty(T)` process law.

This is finite-index only, using the local equivalence
`VdVWEllInfty.finiteContinuousLinearEquiv`.
-/
theorem vdVW148_boundedProcess_hasLaw_of_finiteProduct_hasLaw_finite
    [MeasurableSpace Ω]
    [Fintype T]
    [MeasurableSpace (VdVWEllInfty T)] [BorelSpace (VdVWEllInfty T)]
    [MeasurableSpace (T -> ℝ)] [BorelSpace (T -> ℝ)]
    {X : Ω -> T -> ℝ} (hbounded : VdVWEllInfty.IsBoundedSamplePath X)
    {P : Measure Ω} {ν : Measure (T -> ℝ)}
    (hX : HasLaw X ν P) :
    HasLaw
      (VdVWEllInfty.processMap X hbounded)
      (ν.map (VdVWEllInfty.finiteContinuousLinearEquiv (T := T)).symm)
      P := by
  let e := VdVWEllInfty.finiteContinuousLinearEquiv (T := T)
  have hmap : HasLaw (e.symm ∘ X) (ν.map e.symm) P := by
    refine HasLaw.comp ?_ hX
    exact
      { aemeasurable := e.symm.continuous.measurable.aemeasurable
        map_eq := rfl }
  simpa [e, Function.comp_def, VdVWEllInfty.processMap] using hmap

/--
Finite-index law converse without a separate bounded-sample-path hypothesis:
for finite `T`, boundedness of all sample paths is automatic.

This is still a finite-index support layer for VdV&W 1.4.8, not the
arbitrary-index FDD converse.
-/
theorem vdVW148_finiteProcess_hasLaw_of_finiteProduct_hasLaw_finite
    [MeasurableSpace Ω]
    [Fintype T]
    [MeasurableSpace (VdVWEllInfty T)] [BorelSpace (VdVWEllInfty T)]
    [MeasurableSpace (T -> ℝ)] [BorelSpace (T -> ℝ)]
    {X : Ω -> T -> ℝ} {P : Measure Ω} {ν : Measure (T -> ℝ)}
    (hX : HasLaw X ν P) :
    HasLaw
      (VdVWEllInfty.processMapFinite X)
      (ν.map (VdVWEllInfty.finiteContinuousLinearEquiv (T := T)).symm)
      P := by
  simpa [VdVWEllInfty.processMapFinite] using
    (vdVW148_boundedProcess_hasLaw_of_finiteProduct_hasLaw_finite
      (T := T) (Ω := Ω)
      (hbounded := VdVWEllInfty.isBoundedSamplePath_of_finite X)
      (P := P) (ν := ν) hX)

/--
Finite-index identical-distribution converse for bounded raw processes:
identical finite-product distributions induce identical `ell_infty(T)` process
distributions.
-/
theorem vdVW148_boundedProcess_identDistrib_of_finiteProduct_identDistrib_finite
    [MeasurableSpace Ω] [MeasurableSpace Ω']
    [Fintype T]
    [MeasurableSpace (VdVWEllInfty T)] [BorelSpace (VdVWEllInfty T)]
    [MeasurableSpace (T -> ℝ)] [BorelSpace (T -> ℝ)]
    {X : Ω -> T -> ℝ} {Y : Ω' -> T -> ℝ}
    (hXbounded : VdVWEllInfty.IsBoundedSamplePath X)
    (hYbounded : VdVWEllInfty.IsBoundedSamplePath Y)
    {P : Measure Ω} {Q : Measure Ω'}
    (hXY : IdentDistrib X Y P Q) :
    IdentDistrib
      (VdVWEllInfty.processMap X hXbounded)
      (VdVWEllInfty.processMap Y hYbounded)
      P Q := by
  let e := VdVWEllInfty.finiteContinuousLinearEquiv (T := T)
  have hmap : IdentDistrib (e.symm ∘ X) (e.symm ∘ Y) P Q :=
    hXY.comp e.symm.continuous.measurable
  simpa [e, Function.comp_def, VdVWEllInfty.processMap] using hmap

/--
Finite-index identical-distribution converse without explicit boundedness
hypotheses.  Finite index sets make every real sample path bounded.
-/
theorem vdVW148_finiteProcess_identDistrib_of_finiteProduct_identDistrib_finite
    [MeasurableSpace Ω] [MeasurableSpace Ω']
    [Fintype T]
    [MeasurableSpace (VdVWEllInfty T)] [BorelSpace (VdVWEllInfty T)]
    [MeasurableSpace (T -> ℝ)] [BorelSpace (T -> ℝ)]
    {X : Ω -> T -> ℝ} {Y : Ω' -> T -> ℝ}
    {P : Measure Ω} {Q : Measure Ω'}
    (hXY : IdentDistrib X Y P Q) :
    IdentDistrib
      (VdVWEllInfty.processMapFinite X)
      (VdVWEllInfty.processMapFinite Y)
      P Q := by
  simpa [VdVWEllInfty.processMapFinite] using
    (vdVW148_boundedProcess_identDistrib_of_finiteProduct_identDistrib_finite
      (T := T) (Ω := Ω) (Ω' := Ω')
      (hXbounded := VdVWEllInfty.isBoundedSamplePath_of_finite X)
      (hYbounded := VdVWEllInfty.isBoundedSamplePath_of_finite Y)
      (P := P) (Q := Q) hXY)

/--
Random-variable finite-index converse for `ell_infty(T)`: if `T` is finite,
convergence in distribution after the finite product identification implies
convergence in distribution of the original `ell_infty(T)`-valued variables.

This is the random-variable analogue of
`vdVW148_ellInfty_weakConvergence_of_finiteProduct_weakConvergence_finite`.
-/
theorem vdVW148_ellInfty_tendstoInDistribution_of_finiteProduct_tendstoInDistribution_finite
    {ι : Type*} {Ω : ι -> Type*} {Ω' : Type*}
    {mΩ : (i : ι) -> MeasurableSpace (Ω i)}
    {μ : (i : ι) -> @Measure (Ω i) (mΩ i)}
    [∀ i, IsProbabilityMeasure (μ i)]
    {mΩ' : MeasurableSpace Ω'} {μ' : @Measure Ω' mΩ'}
    [IsProbabilityMeasure μ']
    [Fintype T]
    [MeasurableSpace (VdVWEllInfty T)] [BorelSpace (VdVWEllInfty T)]
    [MeasurableSpace (T -> ℝ)] [BorelSpace (T -> ℝ)]
    {X : (i : ι) -> Ω i -> VdVWEllInfty T}
    {Z : Ω' -> VdVWEllInfty T} {l : Filter ι}
    (hX : TendstoInDistribution
      (fun i => (VdVWEllInfty.finiteContinuousLinearEquiv (T := T)) ∘ X i)
      l
      ((VdVWEllInfty.finiteContinuousLinearEquiv (T := T)) ∘ Z)
      μ μ') :
    TendstoInDistribution X l Z μ μ' := by
  haveI : Nonempty (VdVWEllInfty T) := ⟨0⟩
  let e := VdVWEllInfty.finiteContinuousLinearEquiv (T := T)
  have hback := hX.continuous_comp e.symm.continuous
  simpa [e, Function.comp_def] using hback

/--
Raw-process finite-index converse: for finite `T`, convergence in distribution
of the ordinary finite-coordinate processes implies convergence in
distribution of their bounded `ell_infty(T)` process maps.

This is the raw-process analogue of
`vdVW148_ellInfty_tendstoInDistribution_of_finiteProduct_tendstoInDistribution_finite`.
It remains finite-index only; the arbitrary-index VdV&W 1.4.8 converse still
requires separability, tightness, and asymptotic-measurability primitives.
-/
theorem vdVW148_boundedProcess_tendstoInDistribution_of_finiteProduct_tendstoInDistribution_finite
    {ι : Type*} {Ω : ι -> Type*} {Ω' : Type*}
    {mΩ : (i : ι) -> MeasurableSpace (Ω i)}
    {μ : (i : ι) -> @Measure (Ω i) (mΩ i)}
    [∀ i, IsProbabilityMeasure (μ i)]
    {mΩ' : MeasurableSpace Ω'} {μ' : @Measure Ω' mΩ'}
    [IsProbabilityMeasure μ']
    [Fintype T]
    [MeasurableSpace (VdVWEllInfty T)] [BorelSpace (VdVWEllInfty T)]
    [MeasurableSpace (T -> ℝ)] [BorelSpace (T -> ℝ)]
    {X : (i : ι) -> Ω i -> T -> ℝ} {Z : Ω' -> T -> ℝ}
    (hXbounded : ∀ i, VdVWEllInfty.IsBoundedSamplePath (X i))
    (hZbounded : VdVWEllInfty.IsBoundedSamplePath Z)
    {l : Filter ι}
    (hX : TendstoInDistribution X l Z μ μ') :
    TendstoInDistribution
      (fun i => VdVWEllInfty.processMap (X i) (hXbounded i))
      l
      (VdVWEllInfty.processMap Z hZbounded)
      μ μ' := by
  refine
    vdVW148_ellInfty_tendstoInDistribution_of_finiteProduct_tendstoInDistribution_finite
      (T := T) (Ω := Ω) (Ω' := Ω') (μ := μ) (μ' := μ')
      (X := fun i => VdVWEllInfty.processMap (X i) (hXbounded i))
      (Z := VdVWEllInfty.processMap Z hZbounded) (l := l) ?_
  simpa [Function.comp_def, VdVWEllInfty.processMap] using hX

/--
Raw finite-index converse without explicit boundedness hypotheses: for finite
`T`, convergence in distribution of the ordinary finite-coordinate processes
implies convergence in distribution of their canonical `ell_infty(T)` process
maps.

This removes a finite-index nuisance assumption while keeping the
arbitrary-index VdV&W 1.4.8 converse separate.
-/
theorem vdVW148_finiteProcess_tendstoInDistribution_of_finiteProduct_tendstoInDistribution_finite
    {ι : Type*} {Ω : ι -> Type*} {Ω' : Type*}
    {mΩ : (i : ι) -> MeasurableSpace (Ω i)}
    {μ : (i : ι) -> @Measure (Ω i) (mΩ i)}
    [∀ i, IsProbabilityMeasure (μ i)]
    {mΩ' : MeasurableSpace Ω'} {μ' : @Measure Ω' mΩ'}
    [IsProbabilityMeasure μ']
    [Fintype T]
    [MeasurableSpace (VdVWEllInfty T)] [BorelSpace (VdVWEllInfty T)]
    [MeasurableSpace (T -> ℝ)] [BorelSpace (T -> ℝ)]
    {X : (i : ι) -> Ω i -> T -> ℝ} {Z : Ω' -> T -> ℝ}
    {l : Filter ι}
    (hX : TendstoInDistribution X l Z μ μ') :
    TendstoInDistribution
      (fun i => VdVWEllInfty.processMapFinite (X i))
      l
      (VdVWEllInfty.processMapFinite Z)
      μ μ' := by
  haveI : Nonempty (VdVWEllInfty T) := ⟨0⟩
  simpa [VdVWEllInfty.processMapFinite] using
    (vdVW148_boundedProcess_tendstoInDistribution_of_finiteProduct_tendstoInDistribution_finite
      (T := T) (Ω := Ω) (Ω' := Ω') (μ := μ) (μ' := μ')
      (hXbounded := fun i => VdVWEllInfty.isBoundedSamplePath_of_finite (X i))
      (hZbounded := VdVWEllInfty.isBoundedSamplePath_of_finite Z)
      (l := l) hX)

/--
Law of a bounded raw process viewed as an `ell_infty(T)`-valued random
element.

This is a process-level Chapter 1 interface: it packages the ordinary law of
`VdVWEllInfty.processMap` as a probability measure, but it does not assert
full VdV&W separability, asymptotic measurability, or the FDD converse.
-/
noncomputable def vdVWEllInftyProcessLaw
    [MeasurableSpace Ω] [MeasurableSpace (VdVWEllInfty T)]
    (P : Measure Ω) [IsProbabilityMeasure P]
    (X : Ω -> T -> ℝ) (hbounded : VdVWEllInfty.IsBoundedSamplePath X)
    (hX : AEMeasurable (VdVWEllInfty.processMap X hbounded) P) :
    ProbabilityMeasure (VdVWEllInfty T) :=
  ⟨P.map (VdVWEllInfty.processMap X hbounded), Measure.isProbabilityMeasure_map hX⟩

/--
The `ell_infty(T)` process law is unchanged by replacing the bounded process
map with an a.e.-equal version.
-/
theorem vdVWEllInftyProcessLaw_congr_ae
    [MeasurableSpace Ω] [MeasurableSpace (VdVWEllInfty T)]
    (P : Measure Ω) [IsProbabilityMeasure P]
    (X Y : Ω -> T -> ℝ)
    (hXbounded : VdVWEllInfty.IsBoundedSamplePath X)
    (hYbounded : VdVWEllInfty.IsBoundedSamplePath Y)
    (hX : AEMeasurable (VdVWEllInfty.processMap X hXbounded) P)
    (hY : AEMeasurable (VdVWEllInfty.processMap Y hYbounded) P)
    (hXY :
      VdVWEllInfty.processMap Y hYbounded =ᵐ[P]
        VdVWEllInfty.processMap X hXbounded) :
    vdVWEllInftyProcessLaw (T := T) P Y hYbounded hY =
      vdVWEllInftyProcessLaw (T := T) P X hXbounded hX := by
  ext s hs
  exact congrArg (fun m : Measure (VdVWEllInfty T) => m s) (Measure.map_congr hXY)

/--
The `ell_infty(T)` process law is unchanged by replacing a raw bounded process
with another one whose entire sample path is coordinatewise equal a.e.

This is the raw-process form needed before constructing measurable or
canonical versions of a process.  The a.e. equality is over whole sample paths,
not merely separately for each coordinate.
-/
theorem vdVWEllInftyProcessLaw_congr_forall_coord_ae
    [MeasurableSpace Ω] [MeasurableSpace (VdVWEllInfty T)]
    (P : Measure Ω) [IsProbabilityMeasure P]
    (X Y : Ω -> T -> ℝ)
    (hXbounded : VdVWEllInfty.IsBoundedSamplePath X)
    (hYbounded : VdVWEllInfty.IsBoundedSamplePath Y)
    (hX : AEMeasurable (VdVWEllInfty.processMap X hXbounded) P)
    (hY : AEMeasurable (VdVWEllInfty.processMap Y hYbounded) P)
    (hXY : ∀ᵐ ω ∂P, ∀ t, Y ω t = X ω t) :
    vdVWEllInftyProcessLaw (T := T) P Y hYbounded hY =
      vdVWEllInftyProcessLaw (T := T) P X hXbounded hX :=
  vdVWEllInftyProcessLaw_congr_ae
    (T := T) (P := P) (X := X) (Y := Y)
    (hXbounded := hXbounded) (hYbounded := hYbounded)
    (hX := hX) (hY := hY)
    (VdVWEllInfty.processMap_congr_ae hXbounded hYbounded hXY)

/-- Finite-dimensional law of a raw real-valued process. -/
noncomputable def vdVWFDDProcessLaw
    [MeasurableSpace Ω] (P : Measure Ω) [IsProbabilityMeasure P]
    (I : Finset T) [MeasurableSpace (I -> ℝ)]
    (X : Ω -> T -> ℝ)
    (hX : AEMeasurable (fun ω => fun t : I => X ω t.1) P) :
    ProbabilityMeasure (I -> ℝ) :=
  ⟨P.map (fun ω => fun t : I => X ω t.1), Measure.isProbabilityMeasure_map hX⟩

/-- Single-coordinate law of a raw real-valued process. -/
noncomputable def vdVWCoordinateProcessLaw
    [MeasurableSpace Ω] (P : Measure Ω) [IsProbabilityMeasure P]
    (X : Ω -> T -> ℝ) (t : T)
    (hX : AEMeasurable (fun ω => X ω t) P) :
    ProbabilityMeasure ℝ :=
  ⟨P.map (fun ω => X ω t), Measure.isProbabilityMeasure_map hX⟩

/--
Single-coordinate a.e.-measurability is unchanged by replacing that coordinate
a.e.
-/
theorem aemeasurable_coordinate_congr_ae
    [MeasurableSpace Ω]
    {P : Measure Ω} {X Y : Ω -> T -> ℝ} {t : T}
    (hX : AEMeasurable (fun ω => X ω t) P)
    (hYX : ∀ᵐ ω ∂P, Y ω t = X ω t) :
    AEMeasurable (fun ω => Y ω t) P :=
  hX.congr (hYX.mono fun _ hω => hω.symm)

/--
Finite-dimensional a.e.-measurability is unchanged by replacing a raw process
with another one whose whole sample path is coordinatewise equal a.e.
-/
theorem aemeasurable_fdd_congr_forall_coord_ae
    [MeasurableSpace Ω]
    {P : Measure Ω} (I : Finset T) [MeasurableSpace (I -> ℝ)]
    {X Y : Ω -> T -> ℝ}
    (hX : AEMeasurable (fun ω => fun t : I => X ω t.1) P)
    (hYX : ∀ᵐ ω ∂P, ∀ t, Y ω t = X ω t) :
    AEMeasurable (fun ω => fun t : I => Y ω t.1) P := by
  exact hX.congr (hYX.mono fun ω hω => by
    funext t
    exact (hω t.1).symm)

/--
Finite-dimensional a.e.-measurability only needs a.e. equality on the selected
finite coordinate set.

This is weaker than `aemeasurable_fdd_congr_forall_coord_ae`: it is sufficient
for a fixed FDD law and does not assert whole-sample-path equality.
-/
theorem aemeasurable_fdd_congr_finite_coord_ae
    [MeasurableSpace Ω]
    {P : Measure Ω} (I : Finset T) [MeasurableSpace (I -> ℝ)]
    {X Y : Ω -> T -> ℝ}
    (hX : AEMeasurable (fun ω => fun t : I => X ω t.1) P)
    (hYX : ∀ᵐ ω ∂P, ∀ t : I, Y ω t.1 = X ω t.1) :
    AEMeasurable (fun ω => fun t : I => Y ω t.1) P := by
  exact hX.congr (hYX.mono fun ω hω => by
    funext t
    exact (hω t).symm)

/--
The finite-dimensional law of a raw process is unchanged by replacing the
process with a sample-path a.e.-equal version.
-/
theorem vdVWFDDProcessLaw_congr_forall_coord_ae
    [MeasurableSpace Ω]
    (P : Measure Ω) [IsProbabilityMeasure P]
    (I : Finset T) [MeasurableSpace (I -> ℝ)]
    (X Y : Ω -> T -> ℝ)
    (hX : AEMeasurable (fun ω => fun t : I => X ω t.1) P)
    (hY : AEMeasurable (fun ω => fun t : I => Y ω t.1) P)
    (hYX : ∀ᵐ ω ∂P, ∀ t, Y ω t = X ω t) :
    vdVWFDDProcessLaw P I Y hY = vdVWFDDProcessLaw P I X hX := by
  ext s hs
  exact congrArg (fun m : Measure (I -> ℝ) => m s)
    (Measure.map_congr (hYX.mono fun ω hω => by
      funext t
      exact hω t.1))

/--
The finite-dimensional law of a raw process is unchanged by replacing only the
selected finite coordinates a.e.

This is the fixed-FDD congruence form used before any arbitrary-index
separability or process-law converse is available.
-/
theorem vdVWFDDProcessLaw_congr_finite_coord_ae
    [MeasurableSpace Ω]
    (P : Measure Ω) [IsProbabilityMeasure P]
    (I : Finset T) [MeasurableSpace (I -> ℝ)]
    (X Y : Ω -> T -> ℝ)
    (hX : AEMeasurable (fun ω => fun t : I => X ω t.1) P)
    (hY : AEMeasurable (fun ω => fun t : I => Y ω t.1) P)
    (hYX : ∀ᵐ ω ∂P, ∀ t : I, Y ω t.1 = X ω t.1) :
    vdVWFDDProcessLaw P I Y hY = vdVWFDDProcessLaw P I X hX := by
  ext s hs
  exact congrArg (fun m : Measure (I -> ℝ) => m s)
    (Measure.map_congr (hYX.mono fun ω hω => by
      funext t
      exact hω t))

/--
The single-coordinate law of a raw process is unchanged by replacing that
coordinate a.e.
-/
theorem vdVWCoordinateProcessLaw_congr_ae
    [MeasurableSpace Ω]
    (P : Measure Ω) [IsProbabilityMeasure P]
    (X Y : Ω -> T -> ℝ) (t : T)
    (hX : AEMeasurable (fun ω => X ω t) P)
    (hY : AEMeasurable (fun ω => Y ω t) P)
    (hYX : ∀ᵐ ω ∂P, Y ω t = X ω t) :
    vdVWCoordinateProcessLaw P Y t hY = vdVWCoordinateProcessLaw P X t hX := by
  ext s hs
  exact congrArg (fun m : Measure ℝ => m s) (Measure.map_congr hYX)

/--
Finite-dimensional a.e.-measurability follows from a.e.-measurability of the
associated bounded `ell_infty(T)` process.
-/
theorem aemeasurable_fdd_of_aemeasurable_ellInftyProcessMap
    [MeasurableSpace Ω]
    [MeasurableSpace (VdVWEllInfty T)] [BorelSpace (VdVWEllInfty T)]
    {P : Measure Ω} (I : Finset T) [MeasurableSpace (I -> ℝ)] [BorelSpace (I -> ℝ)]
    {X : Ω -> T -> ℝ} {hbounded : VdVWEllInfty.IsBoundedSamplePath X}
    (hX : AEMeasurable (VdVWEllInfty.processMap X hbounded) P) :
    AEMeasurable (fun ω => fun t : I => X ω t.1) P := by
  have hcomp :
      AEMeasurable
        (fun ω => VdVWEllInfty.finiteRestrict I
          (VdVWEllInfty.processMap X hbounded ω)) P :=
    (VdVWEllInfty.measurable_finiteRestrict (T := T) I).comp_aemeasurable hX
  simpa [Function.comp_def, VdVWEllInfty.finiteRestrict, VdVWEllInfty.processMap]
    using hcomp

/--
The finite-dimensional restriction of an `ell_infty(T)` process law is the
ordinary finite-dimensional law of the raw coordinate process.
-/
theorem vdVWEllInftyProcessLaw_map_finiteRestrict
    [MeasurableSpace Ω]
    [MeasurableSpace (VdVWEllInfty T)] [BorelSpace (VdVWEllInfty T)]
    (P : Measure Ω) [IsProbabilityMeasure P]
    (X : Ω -> T -> ℝ) (hbounded : VdVWEllInfty.IsBoundedSamplePath X)
    (hX : AEMeasurable (VdVWEllInfty.processMap X hbounded) P)
    (I : Finset T) [MeasurableSpace (I -> ℝ)] [BorelSpace (I -> ℝ)] :
    (vdVWEllInftyProcessLaw (T := T) P X hbounded hX).map
        ((VdVWEllInfty.continuous_finiteRestrict (T := T) I).measurable.aemeasurable) =
      vdVWFDDProcessLaw P I X
        (aemeasurable_fdd_of_aemeasurable_ellInftyProcessMap (T := T) I hX) := by
  ext s hs
  change
    Measure.map (VdVWEllInfty.finiteRestrict (T := T) I)
        (Measure.map (VdVWEllInfty.processMap X hbounded) P) s =
      Measure.map (fun ω => fun t : I => X ω t.1) P s
  rw [AEMeasurable.map_map_of_aemeasurable
    ((VdVWEllInfty.continuous_finiteRestrict (T := T) I).measurable.aemeasurable) hX]
  have hfg :
      (VdVWEllInfty.finiteRestrict (T := T) I ∘
          VdVWEllInfty.processMap X hbounded) =ᵐ[P]
        (fun ω => fun t : I => X ω t.1) :=
    Filter.Eventually.of_forall fun ω => by
      funext t
      rfl
  exact congrArg (fun m : Measure (I -> ℝ) => m s) (Measure.map_congr hfg)

/--
The single-coordinate projection of an `ell_infty(T)` process law is the
ordinary coordinate law of the raw process.
-/
theorem vdVWEllInftyProcessLaw_map_eval
    [MeasurableSpace Ω]
    [MeasurableSpace (VdVWEllInfty T)] [BorelSpace (VdVWEllInfty T)]
    (P : Measure Ω) [IsProbabilityMeasure P]
    (X : Ω -> T -> ℝ) (hbounded : VdVWEllInfty.IsBoundedSamplePath X)
    (hX : AEMeasurable (VdVWEllInfty.processMap X hbounded) P)
    (t : T) :
    (vdVWEllInftyProcessLaw (T := T) P X hbounded hX).map
        ((VdVWEllInfty.evalCLM (T := T) t).continuous.measurable.aemeasurable) =
      vdVWCoordinateProcessLaw P X t
        ((VdVWEllInfty.evalCLM (T := T) t).continuous.measurable.aemeasurable.comp_aemeasurable hX) := by
  ext s hs
  change
    Measure.map (VdVWEllInfty.evalCLM (T := T) t)
        (Measure.map (VdVWEllInfty.processMap X hbounded) P) s =
      Measure.map (fun ω => X ω t) P s
  rw [AEMeasurable.map_map_of_aemeasurable
    ((VdVWEllInfty.evalCLM (T := T) t).continuous.measurable.aemeasurable) hX]
  have hfg :
      (VdVWEllInfty.evalCLM (T := T) t ∘
          VdVWEllInfty.processMap X hbounded) =ᵐ[P]
        (fun ω => X ω t) :=
    Filter.Eventually.of_forall fun ω => by
      simp [VdVWEllInfty.evalCLM_apply, VdVWEllInfty.processMap]
  exact congrArg (fun m : Measure ℝ => m s) (Measure.map_congr hfg)

/--
Weak convergence of bounded raw processes, expressed as weak convergence of
their ordinary `ell_infty(T)` process laws.

This is a process-law interface only.  It deliberately does not assert the
arbitrary-index VdV&W FDD converse or separability/asymptotic-measurability
clauses.
-/
def VdVWEllInftyProcessWeakConvergence
    {ι : Type*} {Ω : ι -> Type*} {Ωlim : Type*}
    {mΩ : (i : ι) -> MeasurableSpace (Ω i)}
    (μ : (i : ι) -> @Measure (Ω i) (mΩ i)) [∀ i, IsProbabilityMeasure (μ i)]
    [MeasurableSpace Ωlim] (μlim : Measure Ωlim) [IsProbabilityMeasure μlim]
    [MeasurableSpace (VdVWEllInfty T)] [OpensMeasurableSpace (VdVWEllInfty T)]
    (X : (i : ι) -> Ω i -> T -> ℝ)
    (Z : Ωlim -> T -> ℝ)
    (hbounded : ∀ i, VdVWEllInfty.IsBoundedSamplePath (X i))
    (hZbounded : VdVWEllInfty.IsBoundedSamplePath Z)
    (hX : ∀ i,
      AEMeasurable (VdVWEllInfty.processMap (X i) (hbounded i)) (μ i))
    (hZ : AEMeasurable (VdVWEllInfty.processMap Z hZbounded) μlim)
    (l : Filter ι) : Prop :=
  VdVWWeakConvergenceProbabilityMeasures
    (fun i => vdVWEllInftyProcessLaw (T := T) (μ i) (X i) (hbounded i) (hX i))
    l
    (vdVWEllInftyProcessLaw (T := T) μlim Z hZbounded hZ)

/--
Process weak convergence is stable under passing to a finer index filter.
This is the raw-process version of
`VdVWWeakConvergenceProbabilityMeasures.mono_filter`.
-/
theorem VdVWEllInftyProcessWeakConvergence.mono_filter
    {ι : Type*} {Ω : ι -> Type*} {Ωlim : Type*}
    {mΩ : (i : ι) -> MeasurableSpace (Ω i)}
    (μ : (i : ι) -> @Measure (Ω i) (mΩ i)) [∀ i, IsProbabilityMeasure (μ i)]
    [MeasurableSpace Ωlim] (μlim : Measure Ωlim) [IsProbabilityMeasure μlim]
    [MeasurableSpace (VdVWEllInfty T)] [OpensMeasurableSpace (VdVWEllInfty T)]
    (X : (i : ι) -> Ω i -> T -> ℝ)
    (Z : Ωlim -> T -> ℝ)
    (hbounded : ∀ i, VdVWEllInfty.IsBoundedSamplePath (X i))
    (hZbounded : VdVWEllInfty.IsBoundedSamplePath Z)
    (hX : ∀ i,
      AEMeasurable (VdVWEllInfty.processMap (X i) (hbounded i)) (μ i))
    (hZ : AEMeasurable (VdVWEllInfty.processMap Z hZbounded) μlim)
    {l l' : Filter ι}
    (h : VdVWEllInftyProcessWeakConvergence
      (T := T) μ μlim X Z hbounded hZbounded hX hZ l)
    (hl : l' ≤ l) :
    VdVWEllInftyProcessWeakConvergence
      (T := T) μ μlim X Z hbounded hZbounded hX hZ l' :=
  VdVWWeakConvergenceProbabilityMeasures.mono_filter
    (show VdVWWeakConvergenceProbabilityMeasures
      (fun i => vdVWEllInftyProcessLaw (T := T) (μ i) (X i) (hbounded i) (hX i))
      l
      (vdVWEllInftyProcessLaw (T := T) μlim Z hZbounded hZ) from h) hl

/--
Process weak convergence is stable under reindexing along a map tending to the
original index filter.  This gives the local raw-process subsequence/subnet
handoff without adding any FDD-converse claim.
-/
theorem VdVWEllInftyProcessWeakConvergence.comp_tendsto
    {ι κ : Type*} {Ω : ι -> Type*} {Ωlim : Type*}
    {mΩ : (i : ι) -> MeasurableSpace (Ω i)}
    (μ : (i : ι) -> @Measure (Ω i) (mΩ i)) [∀ i, IsProbabilityMeasure (μ i)]
    [MeasurableSpace Ωlim] (μlim : Measure Ωlim) [IsProbabilityMeasure μlim]
    [MeasurableSpace (VdVWEllInfty T)] [OpensMeasurableSpace (VdVWEllInfty T)]
    (X : (i : ι) -> Ω i -> T -> ℝ)
    (Z : Ωlim -> T -> ℝ)
    (hbounded : ∀ i, VdVWEllInfty.IsBoundedSamplePath (X i))
    (hZbounded : VdVWEllInfty.IsBoundedSamplePath Z)
    (hX : ∀ i,
      AEMeasurable (VdVWEllInfty.processMap (X i) (hbounded i)) (μ i))
    (hZ : AEMeasurable (VdVWEllInfty.processMap Z hZbounded) μlim)
    {l : Filter ι} {l' : Filter κ} {φ : κ -> ι}
    (h : VdVWEllInftyProcessWeakConvergence
      (T := T) μ μlim X Z hbounded hZbounded hX hZ l)
    (hφ : Filter.Tendsto φ l' l) :
    VdVWEllInftyProcessWeakConvergence
      (T := T) (fun k => μ (φ k)) μlim (fun k => X (φ k)) Z
        (fun k => hbounded (φ k)) hZbounded (fun k => hX (φ k)) hZ l' :=
  VdVWWeakConvergenceProbabilityMeasures.comp_tendsto
    (show VdVWWeakConvergenceProbabilityMeasures
      (fun i => vdVWEllInftyProcessLaw (T := T) (μ i) (X i) (hbounded i) (hX i))
      l
      (vdVWEllInftyProcessLaw (T := T) μlim Z hZbounded hZ) from h) hφ

/--
Process weak convergence is unchanged by replacing the source processes by
a.e.-equal bounded process maps eventually along the index filter.
-/
theorem VdVWEllInftyProcessWeakConvergence.congr_eventually_ae
    {ι : Type*} {Ω : ι -> Type*} {Ωlim : Type*}
    {mΩ : (i : ι) -> MeasurableSpace (Ω i)}
    (μ : (i : ι) -> @Measure (Ω i) (mΩ i)) [∀ i, IsProbabilityMeasure (μ i)]
    [MeasurableSpace Ωlim] (μlim : Measure Ωlim) [IsProbabilityMeasure μlim]
    [MeasurableSpace (VdVWEllInfty T)] [OpensMeasurableSpace (VdVWEllInfty T)]
    (X Y : (i : ι) -> Ω i -> T -> ℝ)
    (Z : Ωlim -> T -> ℝ)
    (hXbounded : ∀ i, VdVWEllInfty.IsBoundedSamplePath (X i))
    (hYbounded : ∀ i, VdVWEllInfty.IsBoundedSamplePath (Y i))
    (hZbounded : VdVWEllInfty.IsBoundedSamplePath Z)
    (hX : ∀ i,
      AEMeasurable (VdVWEllInfty.processMap (X i) (hXbounded i)) (μ i))
    (hY : ∀ i,
      AEMeasurable (VdVWEllInfty.processMap (Y i) (hYbounded i)) (μ i))
    (hZ : AEMeasurable (VdVWEllInfty.processMap Z hZbounded) μlim)
    {l : Filter ι}
    (h : VdVWEllInftyProcessWeakConvergence
      (T := T) μ μlim X Z hXbounded hZbounded hX hZ l)
    (hXY : ∀ᶠ i in l,
      VdVWEllInfty.processMap (Y i) (hYbounded i) =ᵐ[μ i]
        VdVWEllInfty.processMap (X i) (hXbounded i)) :
    VdVWEllInftyProcessWeakConvergence
      (T := T) μ μlim Y Z hYbounded hZbounded hY hZ l :=
  VdVWWeakConvergenceProbabilityMeasures.congr_eventually
    (show VdVWWeakConvergenceProbabilityMeasures
      (fun i => vdVWEllInftyProcessLaw (T := T) (μ i) (X i) (hXbounded i) (hX i))
      l
      (vdVWEllInftyProcessLaw (T := T) μlim Z hZbounded hZ) from h)
    (hXY.mono fun i hi =>
      vdVWEllInftyProcessLaw_congr_ae
        (T := T) (P := μ i) (X := X i) (Y := Y i)
        (hXbounded := hXbounded i) (hYbounded := hYbounded i)
        (hX := hX i) (hY := hY i) hi)

/--
Process weak convergence is unchanged by replacing the source raw processes by
sample-path a.e.-equal versions eventually along the index filter.

This consumes the raw coordinatewise sample-path equality form
`∀ᵐ ω, ∀ t, Y_i ω t = X_i ω t`, which is often the available output of
separability or canonical-version arguments.
-/
theorem VdVWEllInftyProcessWeakConvergence.congr_eventually_forall_coord_ae
    {ι : Type*} {Ω : ι -> Type*} {Ωlim : Type*}
    {mΩ : (i : ι) -> MeasurableSpace (Ω i)}
    (μ : (i : ι) -> @Measure (Ω i) (mΩ i)) [∀ i, IsProbabilityMeasure (μ i)]
    [MeasurableSpace Ωlim] (μlim : Measure Ωlim) [IsProbabilityMeasure μlim]
    [MeasurableSpace (VdVWEllInfty T)] [OpensMeasurableSpace (VdVWEllInfty T)]
    (X Y : (i : ι) -> Ω i -> T -> ℝ)
    (Z : Ωlim -> T -> ℝ)
    (hXbounded : ∀ i, VdVWEllInfty.IsBoundedSamplePath (X i))
    (hYbounded : ∀ i, VdVWEllInfty.IsBoundedSamplePath (Y i))
    (hZbounded : VdVWEllInfty.IsBoundedSamplePath Z)
    (hX : ∀ i,
      AEMeasurable (VdVWEllInfty.processMap (X i) (hXbounded i)) (μ i))
    (hY : ∀ i,
      AEMeasurable (VdVWEllInfty.processMap (Y i) (hYbounded i)) (μ i))
    (hZ : AEMeasurable (VdVWEllInfty.processMap Z hZbounded) μlim)
    {l : Filter ι}
    (h : VdVWEllInftyProcessWeakConvergence
      (T := T) μ μlim X Z hXbounded hZbounded hX hZ l)
    (hXY : ∀ᶠ i in l, ∀ᵐ ω ∂μ i, ∀ t, Y i ω t = X i ω t) :
    VdVWEllInftyProcessWeakConvergence
      (T := T) μ μlim Y Z hYbounded hZbounded hY hZ l :=
  VdVWEllInftyProcessWeakConvergence.congr_eventually_ae
    (T := T) μ μlim X Y Z hXbounded hYbounded hZbounded hX hY hZ h
    (hXY.mono fun i hi =>
      VdVWEllInfty.processMap_congr_ae (hXbounded i) (hYbounded i) hi)

/--
Process weak convergence is unchanged by replacing the limiting process by an
a.e.-equal bounded process map.
-/
theorem VdVWEllInftyProcessWeakConvergence.congr_limit_ae
    {ι : Type*} {Ω : ι -> Type*} {Ωlim : Type*}
    {mΩ : (i : ι) -> MeasurableSpace (Ω i)}
    (μ : (i : ι) -> @Measure (Ω i) (mΩ i)) [∀ i, IsProbabilityMeasure (μ i)]
    [MeasurableSpace Ωlim] (μlim : Measure Ωlim) [IsProbabilityMeasure μlim]
    [MeasurableSpace (VdVWEllInfty T)] [OpensMeasurableSpace (VdVWEllInfty T)]
    (X : (i : ι) -> Ω i -> T -> ℝ)
    (Z W : Ωlim -> T -> ℝ)
    (hbounded : ∀ i, VdVWEllInfty.IsBoundedSamplePath (X i))
    (hZbounded : VdVWEllInfty.IsBoundedSamplePath Z)
    (hWbounded : VdVWEllInfty.IsBoundedSamplePath W)
    (hX : ∀ i,
      AEMeasurable (VdVWEllInfty.processMap (X i) (hbounded i)) (μ i))
    (hZ : AEMeasurable (VdVWEllInfty.processMap Z hZbounded) μlim)
    (hW : AEMeasurable (VdVWEllInfty.processMap W hWbounded) μlim)
    {l : Filter ι}
    (h : VdVWEllInftyProcessWeakConvergence
      (T := T) μ μlim X Z hbounded hZbounded hX hZ l)
    (hWZ :
      VdVWEllInfty.processMap W hWbounded =ᵐ[μlim]
        VdVWEllInfty.processMap Z hZbounded) :
    VdVWEllInftyProcessWeakConvergence
      (T := T) μ μlim X W hbounded hWbounded hX hW l := by
  have hLaw :
      vdVWEllInftyProcessLaw (T := T) μlim W hWbounded hW =
        vdVWEllInftyProcessLaw (T := T) μlim Z hZbounded hZ :=
    vdVWEllInftyProcessLaw_congr_ae
      (T := T) (P := μlim) (X := Z) (Y := W)
      (hXbounded := hZbounded) (hYbounded := hWbounded)
      (hX := hZ) (hY := hW) hWZ
  exact
    VdVWWeakConvergenceProbabilityMeasures.congr_limit
      (show VdVWWeakConvergenceProbabilityMeasures
        (fun i => vdVWEllInftyProcessLaw (T := T) (μ i) (X i) (hbounded i) (hX i))
        l
        (vdVWEllInftyProcessLaw (T := T) μlim Z hZbounded hZ) from h)
      hLaw

/--
Process weak convergence is unchanged by replacing the limiting raw process by
a sample-path a.e.-equal version.
-/
theorem VdVWEllInftyProcessWeakConvergence.congr_limit_forall_coord_ae
    {ι : Type*} {Ω : ι -> Type*} {Ωlim : Type*}
    {mΩ : (i : ι) -> MeasurableSpace (Ω i)}
    (μ : (i : ι) -> @Measure (Ω i) (mΩ i)) [∀ i, IsProbabilityMeasure (μ i)]
    [MeasurableSpace Ωlim] (μlim : Measure Ωlim) [IsProbabilityMeasure μlim]
    [MeasurableSpace (VdVWEllInfty T)] [OpensMeasurableSpace (VdVWEllInfty T)]
    (X : (i : ι) -> Ω i -> T -> ℝ)
    (Z W : Ωlim -> T -> ℝ)
    (hbounded : ∀ i, VdVWEllInfty.IsBoundedSamplePath (X i))
    (hZbounded : VdVWEllInfty.IsBoundedSamplePath Z)
    (hWbounded : VdVWEllInfty.IsBoundedSamplePath W)
    (hX : ∀ i,
      AEMeasurable (VdVWEllInfty.processMap (X i) (hbounded i)) (μ i))
    (hZ : AEMeasurable (VdVWEllInfty.processMap Z hZbounded) μlim)
    (hW : AEMeasurable (VdVWEllInfty.processMap W hWbounded) μlim)
    {l : Filter ι}
    (h : VdVWEllInftyProcessWeakConvergence
      (T := T) μ μlim X Z hbounded hZbounded hX hZ l)
    (hWZ : ∀ᵐ ω ∂μlim, ∀ t, W ω t = Z ω t) :
    VdVWEllInftyProcessWeakConvergence
      (T := T) μ μlim X W hbounded hWbounded hX hW l :=
  VdVWEllInftyProcessWeakConvergence.congr_limit_ae
    (T := T) μ μlim X Z W hbounded hZbounded hWbounded hX hZ hW h
    (VdVWEllInfty.processMap_congr_ae hZbounded hWbounded hWZ)

/--
Process weak convergence is unchanged by simultaneous a.e.-equal replacement
of the source process family eventually along the index filter and the limiting
process.

This packages the two common canonicalization steps used in separability/FDD
arguments without changing the underlying weak-convergence statement.
-/
theorem VdVWEllInftyProcessWeakConvergence.congr_eventually_limit_ae
    {ι : Type*} {Ω : ι -> Type*} {Ωlim : Type*}
    {mΩ : (i : ι) -> MeasurableSpace (Ω i)}
    (μ : (i : ι) -> @Measure (Ω i) (mΩ i)) [∀ i, IsProbabilityMeasure (μ i)]
    [MeasurableSpace Ωlim] (μlim : Measure Ωlim) [IsProbabilityMeasure μlim]
    [MeasurableSpace (VdVWEllInfty T)] [OpensMeasurableSpace (VdVWEllInfty T)]
    (X Y : (i : ι) -> Ω i -> T -> ℝ)
    (Z W : Ωlim -> T -> ℝ)
    (hXbounded : ∀ i, VdVWEllInfty.IsBoundedSamplePath (X i))
    (hYbounded : ∀ i, VdVWEllInfty.IsBoundedSamplePath (Y i))
    (hZbounded : VdVWEllInfty.IsBoundedSamplePath Z)
    (hWbounded : VdVWEllInfty.IsBoundedSamplePath W)
    (hX : ∀ i,
      AEMeasurable (VdVWEllInfty.processMap (X i) (hXbounded i)) (μ i))
    (hY : ∀ i,
      AEMeasurable (VdVWEllInfty.processMap (Y i) (hYbounded i)) (μ i))
    (hZ : AEMeasurable (VdVWEllInfty.processMap Z hZbounded) μlim)
    (hW : AEMeasurable (VdVWEllInfty.processMap W hWbounded) μlim)
    {l : Filter ι}
    (h : VdVWEllInftyProcessWeakConvergence
      (T := T) μ μlim X Z hXbounded hZbounded hX hZ l)
    (hYX : ∀ᶠ i in l,
      VdVWEllInfty.processMap (Y i) (hYbounded i) =ᵐ[μ i]
        VdVWEllInfty.processMap (X i) (hXbounded i))
    (hWZ :
      VdVWEllInfty.processMap W hWbounded =ᵐ[μlim]
        VdVWEllInfty.processMap Z hZbounded) :
    VdVWEllInftyProcessWeakConvergence
      (T := T) μ μlim Y W hYbounded hWbounded hY hW l := by
  exact
    VdVWEllInftyProcessWeakConvergence.congr_limit_ae
      (T := T) μ μlim Y Z W hYbounded hZbounded hWbounded hY hZ hW
      (VdVWEllInftyProcessWeakConvergence.congr_eventually_ae
        (T := T) μ μlim X Y Z hXbounded hYbounded hZbounded hX hY hZ h hYX)
      hWZ

/--
Coordinatewise a.e. form of
`VdVWEllInftyProcessWeakConvergence.congr_eventually_limit_ae`.
-/
theorem VdVWEllInftyProcessWeakConvergence.congr_eventually_limit_forall_coord_ae
    {ι : Type*} {Ω : ι -> Type*} {Ωlim : Type*}
    {mΩ : (i : ι) -> MeasurableSpace (Ω i)}
    (μ : (i : ι) -> @Measure (Ω i) (mΩ i)) [∀ i, IsProbabilityMeasure (μ i)]
    [MeasurableSpace Ωlim] (μlim : Measure Ωlim) [IsProbabilityMeasure μlim]
    [MeasurableSpace (VdVWEllInfty T)] [OpensMeasurableSpace (VdVWEllInfty T)]
    (X Y : (i : ι) -> Ω i -> T -> ℝ)
    (Z W : Ωlim -> T -> ℝ)
    (hXbounded : ∀ i, VdVWEllInfty.IsBoundedSamplePath (X i))
    (hYbounded : ∀ i, VdVWEllInfty.IsBoundedSamplePath (Y i))
    (hZbounded : VdVWEllInfty.IsBoundedSamplePath Z)
    (hWbounded : VdVWEllInfty.IsBoundedSamplePath W)
    (hX : ∀ i,
      AEMeasurable (VdVWEllInfty.processMap (X i) (hXbounded i)) (μ i))
    (hY : ∀ i,
      AEMeasurable (VdVWEllInfty.processMap (Y i) (hYbounded i)) (μ i))
    (hZ : AEMeasurable (VdVWEllInfty.processMap Z hZbounded) μlim)
    (hW : AEMeasurable (VdVWEllInfty.processMap W hWbounded) μlim)
    {l : Filter ι}
    (h : VdVWEllInftyProcessWeakConvergence
      (T := T) μ μlim X Z hXbounded hZbounded hX hZ l)
    (hYX : ∀ᶠ i in l, ∀ᵐ ω ∂μ i, ∀ t, Y i ω t = X i ω t)
    (hWZ : ∀ᵐ ω ∂μlim, ∀ t, W ω t = Z ω t) :
    VdVWEllInftyProcessWeakConvergence
      (T := T) μ μlim Y W hYbounded hWbounded hY hW l := by
  exact
    VdVWEllInftyProcessWeakConvergence.congr_eventually_limit_ae
      (T := T) μ μlim X Y Z W hXbounded hYbounded hZbounded hWbounded
      hX hY hZ hW h
      (hYX.mono fun i hi =>
        VdVWEllInfty.processMap_congr_ae (hXbounded i) (hYbounded i) hi)
      (VdVWEllInfty.processMap_congr_ae hZbounded hWbounded hWZ)

/--
Process-level weak convergence implies weak convergence of every
finite-dimensional law.

This is the forward FDD direction for the local raw-process law interface.  It
does not prove the converse direction of VdV&W 1.4.8.
-/
theorem VdVWEllInftyProcessWeakConvergence.finiteDimensionalLaw
    {ι : Type*} {Ω : ι -> Type*} {Ωlim : Type*}
    {mΩ : (i : ι) -> MeasurableSpace (Ω i)}
    (μ : (i : ι) -> @Measure (Ω i) (mΩ i)) [∀ i, IsProbabilityMeasure (μ i)]
    [MeasurableSpace Ωlim] (μlim : Measure Ωlim) [IsProbabilityMeasure μlim]
    [MeasurableSpace (VdVWEllInfty T)] [OpensMeasurableSpace (VdVWEllInfty T)]
    [BorelSpace (VdVWEllInfty T)]
    (X : (i : ι) -> Ω i -> T -> ℝ)
    (Z : Ωlim -> T -> ℝ)
    (hbounded : ∀ i, VdVWEllInfty.IsBoundedSamplePath (X i))
    (hZbounded : VdVWEllInfty.IsBoundedSamplePath Z)
    (hX : ∀ i,
      AEMeasurable (VdVWEllInfty.processMap (X i) (hbounded i)) (μ i))
    (hZ : AEMeasurable (VdVWEllInfty.processMap Z hZbounded) μlim)
    {l : Filter ι}
    (h : VdVWEllInftyProcessWeakConvergence
      (T := T) μ μlim X Z hbounded hZbounded hX hZ l)
    (I : Finset T) [MeasurableSpace (I -> ℝ)] [BorelSpace (I -> ℝ)] :
    VdVWWeakConvergenceProbabilityMeasures
      (fun i => vdVWFDDProcessLaw (μ i) I (X i)
        (aemeasurable_fdd_of_aemeasurable_ellInftyProcessMap (T := T) I (hX i)))
      l
      (vdVWFDDProcessLaw μlim I Z
        (aemeasurable_fdd_of_aemeasurable_ellInftyProcessMap (T := T) I hZ)) := by
  have hmap :
      VdVWWeakConvergenceProbabilityMeasures
        (fun i =>
          (vdVWEllInftyProcessLaw (T := T) (μ i) (X i) (hbounded i) (hX i)).map
            ((VdVWEllInfty.continuous_finiteRestrict (T := T) I).measurable.aemeasurable))
        l
        ((vdVWEllInftyProcessLaw (T := T) μlim Z hZbounded hZ).map
          ((VdVWEllInfty.continuous_finiteRestrict (T := T) I).measurable.aemeasurable)) :=
    h.map_continuous (VdVWEllInfty.continuous_finiteRestrict (T := T) I)
  have hsrc :
      ∀ᶠ i in l,
        vdVWFDDProcessLaw (μ i) I (X i)
            (aemeasurable_fdd_of_aemeasurable_ellInftyProcessMap (T := T) I (hX i)) =
          (vdVWEllInftyProcessLaw (T := T) (μ i) (X i) (hbounded i) (hX i)).map
            ((VdVWEllInfty.continuous_finiteRestrict (T := T) I).measurable.aemeasurable) :=
    Filter.Eventually.of_forall fun i =>
      (vdVWEllInftyProcessLaw_map_finiteRestrict
        (T := T) (P := μ i) (X := X i) (hbounded := hbounded i) (hX := hX i) I).symm
  have hlim :
      (vdVWEllInftyProcessLaw (T := T) μlim Z hZbounded hZ).map
          ((VdVWEllInfty.continuous_finiteRestrict (T := T) I).measurable.aemeasurable) =
        vdVWFDDProcessLaw μlim I Z
          (aemeasurable_fdd_of_aemeasurable_ellInftyProcessMap (T := T) I hZ) :=
    vdVWEllInftyProcessLaw_map_finiteRestrict
      (T := T) (P := μlim) (X := Z) (hbounded := hZbounded) (hX := hZ) I
  simpa [hlim] using hmap.congr_eventually hsrc

/--
Finite-dimensional weak convergence from a process law is stable under
eventually replacing only the selected finite coordinates a.e. and replacing
the limiting selected coordinates a.e.

This is a fixed-FDD replacement primitive.  It is weaker than whole-process
a.e. congruence and still only proves the forward FDD direction.
-/
theorem VdVWEllInftyProcessWeakConvergence.finiteDimensionalLaw_congr_eventually_finite_coord_ae
    {ι : Type*} {Ω : ι -> Type*} {Ωlim : Type*}
    {mΩ : (i : ι) -> MeasurableSpace (Ω i)}
    (μ : (i : ι) -> @Measure (Ω i) (mΩ i)) [∀ i, IsProbabilityMeasure (μ i)]
    [MeasurableSpace Ωlim] (μlim : Measure Ωlim) [IsProbabilityMeasure μlim]
    [MeasurableSpace (VdVWEllInfty T)] [OpensMeasurableSpace (VdVWEllInfty T)]
    [BorelSpace (VdVWEllInfty T)]
    (X Y : (i : ι) -> Ω i -> T -> ℝ)
    (Z W : Ωlim -> T -> ℝ)
    (hbounded : ∀ i, VdVWEllInfty.IsBoundedSamplePath (X i))
    (hZbounded : VdVWEllInfty.IsBoundedSamplePath Z)
    (hX : ∀ i,
      AEMeasurable (VdVWEllInfty.processMap (X i) (hbounded i)) (μ i))
    (hZ : AEMeasurable (VdVWEllInfty.processMap Z hZbounded) μlim)
    {l : Filter ι}
    (h : VdVWEllInftyProcessWeakConvergence
      (T := T) μ μlim X Z hbounded hZbounded hX hZ l)
    (I : Finset T) [MeasurableSpace (I -> ℝ)] [BorelSpace (I -> ℝ)]
    (hY : ∀ i, AEMeasurable (fun ω => fun t : I => Y i ω t.1) (μ i))
    (hW : AEMeasurable (fun ω => fun t : I => W ω t.1) μlim)
    (hYX : ∀ᶠ i in l, ∀ᵐ ω ∂(μ i), ∀ t : I, Y i ω t.1 = X i ω t.1)
    (hWZ : ∀ᵐ ω ∂μlim, ∀ t : I, W ω t.1 = Z ω t.1) :
    VdVWWeakConvergenceProbabilityMeasures
      (fun i => vdVWFDDProcessLaw (μ i) I (Y i) (hY i))
      l
      (vdVWFDDProcessLaw μlim I W hW) := by
  have hfdd :=
    VdVWEllInftyProcessWeakConvergence.finiteDimensionalLaw
      (T := T) μ μlim X Z hbounded hZbounded hX hZ h I
  refine hfdd.congr_eventually_limit ?_ ?_
  · exact hYX.mono fun i hi =>
      vdVWFDDProcessLaw_congr_finite_coord_ae
        (P := μ i) I (X i) (Y i)
        (aemeasurable_fdd_of_aemeasurable_ellInftyProcessMap (T := T) I (hX i))
        (hY i) hi
  · exact
      vdVWFDDProcessLaw_congr_finite_coord_ae
        (P := μlim) I Z W
        (aemeasurable_fdd_of_aemeasurable_ellInftyProcessMap (T := T) I hZ)
        hW hWZ

/--
Process-level weak convergence implies weak convergence of every single
coordinate law.

This is a coordinate version of `finiteDimensionalLaw` for the local bounded
`ell_infty(T)` process interface.  It remains the forward direction only, not
the arbitrary-index FDD converse in VdV&W 1.4.8.
-/
theorem VdVWEllInftyProcessWeakConvergence.coordinateLaw
    {ι : Type*} {Ω : ι -> Type*} {Ωlim : Type*}
    {mΩ : (i : ι) -> MeasurableSpace (Ω i)}
    (μ : (i : ι) -> @Measure (Ω i) (mΩ i)) [∀ i, IsProbabilityMeasure (μ i)]
    [MeasurableSpace Ωlim] (μlim : Measure Ωlim) [IsProbabilityMeasure μlim]
    [MeasurableSpace (VdVWEllInfty T)] [OpensMeasurableSpace (VdVWEllInfty T)]
    [BorelSpace (VdVWEllInfty T)]
    (X : (i : ι) -> Ω i -> T -> ℝ)
    (Z : Ωlim -> T -> ℝ)
    (hbounded : ∀ i, VdVWEllInfty.IsBoundedSamplePath (X i))
    (hZbounded : VdVWEllInfty.IsBoundedSamplePath Z)
    (hX : ∀ i,
      AEMeasurable (VdVWEllInfty.processMap (X i) (hbounded i)) (μ i))
    (hZ : AEMeasurable (VdVWEllInfty.processMap Z hZbounded) μlim)
    {l : Filter ι}
    (h : VdVWEllInftyProcessWeakConvergence
      (T := T) μ μlim X Z hbounded hZbounded hX hZ l)
    (t : T) :
    VdVWWeakConvergenceProbabilityMeasures
      (fun i =>
        (vdVWEllInftyProcessLaw (T := T) (μ i) (X i) (hbounded i) (hX i)).map
          ((VdVWEllInfty.evalCLM (T := T) t).continuous.measurable.aemeasurable))
      l
      ((vdVWEllInftyProcessLaw (T := T) μlim Z hZbounded hZ).map
        ((VdVWEllInfty.evalCLM (T := T) t).continuous.measurable.aemeasurable)) :=
  h.map_continuous (VdVWEllInfty.evalCLM (T := T) t).continuous

/--
Process-level weak convergence implies weak convergence of the ordinary raw
single-coordinate process laws.

This unwraps `coordinateLaw` through `vdVWEllInftyProcessLaw_map_eval`; it is
still the forward continuous-mapping direction, not the VdV&W arbitrary-index
FDD converse.
-/
theorem VdVWEllInftyProcessWeakConvergence.rawCoordinateLaw
    {ι : Type*} {Ω : ι -> Type*} {Ωlim : Type*}
    {mΩ : (i : ι) -> MeasurableSpace (Ω i)}
    (μ : (i : ι) -> @Measure (Ω i) (mΩ i)) [∀ i, IsProbabilityMeasure (μ i)]
    [MeasurableSpace Ωlim] (μlim : Measure Ωlim) [IsProbabilityMeasure μlim]
    [MeasurableSpace (VdVWEllInfty T)] [OpensMeasurableSpace (VdVWEllInfty T)]
    [BorelSpace (VdVWEllInfty T)]
    (X : (i : ι) -> Ω i -> T -> ℝ)
    (Z : Ωlim -> T -> ℝ)
    (hbounded : ∀ i, VdVWEllInfty.IsBoundedSamplePath (X i))
    (hZbounded : VdVWEllInfty.IsBoundedSamplePath Z)
    (hX : ∀ i,
      AEMeasurable (VdVWEllInfty.processMap (X i) (hbounded i)) (μ i))
    (hZ : AEMeasurable (VdVWEllInfty.processMap Z hZbounded) μlim)
    {l : Filter ι}
    (h : VdVWEllInftyProcessWeakConvergence
      (T := T) μ μlim X Z hbounded hZbounded hX hZ l)
    (t : T) :
    VdVWWeakConvergenceProbabilityMeasures
      (fun i => vdVWCoordinateProcessLaw (μ i) (X i) t
        ((VdVWEllInfty.evalCLM (T := T) t).continuous.measurable.aemeasurable.comp_aemeasurable
          (hX i)))
      l
      (vdVWCoordinateProcessLaw μlim Z t
        ((VdVWEllInfty.evalCLM (T := T) t).continuous.measurable.aemeasurable.comp_aemeasurable
          hZ)) := by
  have hcoord :=
    VdVWEllInftyProcessWeakConvergence.coordinateLaw
      (T := T) μ μlim X Z hbounded hZbounded hX hZ h t
  have hsrc :
      ∀ᶠ i in l,
        vdVWCoordinateProcessLaw (μ i) (X i) t
            ((VdVWEllInfty.evalCLM (T := T) t).continuous.measurable.aemeasurable.comp_aemeasurable
              (hX i)) =
          (vdVWEllInftyProcessLaw (T := T) (μ i) (X i) (hbounded i) (hX i)).map
            ((VdVWEllInfty.evalCLM (T := T) t).continuous.measurable.aemeasurable) :=
    Filter.Eventually.of_forall fun i =>
      (vdVWEllInftyProcessLaw_map_eval
        (T := T) (P := μ i) (X := X i) (hbounded := hbounded i) (hX := hX i) t).symm
  have hlim :
      (vdVWEllInftyProcessLaw (T := T) μlim Z hZbounded hZ).map
          ((VdVWEllInfty.evalCLM (T := T) t).continuous.measurable.aemeasurable) =
        vdVWCoordinateProcessLaw μlim Z t
          ((VdVWEllInfty.evalCLM (T := T) t).continuous.measurable.aemeasurable.comp_aemeasurable
            hZ) :=
    vdVWEllInftyProcessLaw_map_eval
      (T := T) (P := μlim) (X := Z) (hbounded := hZbounded) (hX := hZ) t
  simpa [hlim] using hcoord.congr_eventually hsrc

/--
Raw coordinate-law weak convergence is stable under eventually replacing the
source coordinates and the limiting coordinate by a.e.-equal versions.

This is a one-coordinate replacement primitive for later separability and
canonical measurable-version arguments.  It does not replace the whole
`ell_infty(T)` process law.
-/
theorem VdVWEllInftyProcessWeakConvergence.rawCoordinateLaw_congr_eventually_ae
    {ι : Type*} {Ω : ι -> Type*} {Ωlim : Type*}
    {mΩ : (i : ι) -> MeasurableSpace (Ω i)}
    (μ : (i : ι) -> @Measure (Ω i) (mΩ i)) [∀ i, IsProbabilityMeasure (μ i)]
    [MeasurableSpace Ωlim] (μlim : Measure Ωlim) [IsProbabilityMeasure μlim]
    [MeasurableSpace (VdVWEllInfty T)] [OpensMeasurableSpace (VdVWEllInfty T)]
    [BorelSpace (VdVWEllInfty T)]
    (X Y : (i : ι) -> Ω i -> T -> ℝ)
    (Z W : Ωlim -> T -> ℝ)
    (hbounded : ∀ i, VdVWEllInfty.IsBoundedSamplePath (X i))
    (hZbounded : VdVWEllInfty.IsBoundedSamplePath Z)
    (hX : ∀ i,
      AEMeasurable (VdVWEllInfty.processMap (X i) (hbounded i)) (μ i))
    (hZ : AEMeasurable (VdVWEllInfty.processMap Z hZbounded) μlim)
    {l : Filter ι}
    (h : VdVWEllInftyProcessWeakConvergence
      (T := T) μ μlim X Z hbounded hZbounded hX hZ l)
    (t : T)
    (hY : ∀ i, AEMeasurable (fun ω => Y i ω t) (μ i))
    (hW : AEMeasurable (fun ω => W ω t) μlim)
    (hYX : ∀ᶠ i in l, ∀ᵐ ω ∂(μ i), Y i ω t = X i ω t)
    (hWZ : ∀ᵐ ω ∂μlim, W ω t = Z ω t) :
    VdVWWeakConvergenceProbabilityMeasures
      (fun i => vdVWCoordinateProcessLaw (μ i) (Y i) t (hY i))
      l
      (vdVWCoordinateProcessLaw μlim W t hW) := by
  have hcoord :=
    VdVWEllInftyProcessWeakConvergence.rawCoordinateLaw
      (T := T) μ μlim X Z hbounded hZbounded hX hZ h t
  refine hcoord.congr_eventually_limit ?_ ?_
  · exact hYX.mono fun i hi =>
      vdVWCoordinateProcessLaw_congr_ae
        (P := μ i) (X := X i) (Y := Y i) (t := t)
        ((VdVWEllInfty.evalCLM (T := T) t).continuous.measurable.aemeasurable.comp_aemeasurable
          (hX i))
        (hY i) hi
  · exact
      vdVWCoordinateProcessLaw_congr_ae
        (P := μlim) (X := Z) (Y := W) (t := t)
        ((VdVWEllInfty.evalCLM (T := T) t).continuous.measurable.aemeasurable.comp_aemeasurable
          hZ)
        hW hWZ

/--
Process-level asymptotic tightness for bounded raw processes, expressed as
ordinary asymptotic tightness of their `ell_infty(T)` laws.

This is the honest Chapter 1 process interface currently available locally; it
does not assert the full arbitrary-index VdV&W tightness/FDD converse.
-/
def VdVWEllInftyProcessAsymptoticallyTight
    {ι : Type*} {Ω : ι -> Type*}
    {mΩ : (i : ι) -> MeasurableSpace (Ω i)}
    (μ : (i : ι) -> @Measure (Ω i) (mΩ i)) [∀ i, IsProbabilityMeasure (μ i)]
    [MeasurableSpace (VdVWEllInfty T)]
    (X : (i : ι) -> Ω i -> T -> ℝ)
    (hbounded : ∀ i, VdVWEllInfty.IsBoundedSamplePath (X i))
    (hX : ∀ i,
      AEMeasurable (VdVWEllInfty.processMap (X i) (hbounded i)) (μ i))
    (l : Filter ι) : Prop :=
  VdVWProbabilityMeasuresAsymptoticallyTight
    (fun i => vdVWEllInftyProcessLaw (T := T) (μ i) (X i) (hbounded i) (hX i)) l

/--
Process-level asymptotic tightness is stable under passing to a finer index
filter.
-/
theorem VdVWEllInftyProcessAsymptoticallyTight.mono_filter
    {ι : Type*} {Ω : ι -> Type*}
    {mΩ : (i : ι) -> MeasurableSpace (Ω i)}
    (μ : (i : ι) -> @Measure (Ω i) (mΩ i)) [∀ i, IsProbabilityMeasure (μ i)]
    [MeasurableSpace (VdVWEllInfty T)]
    (X : (i : ι) -> Ω i -> T -> ℝ)
    (hbounded : ∀ i, VdVWEllInfty.IsBoundedSamplePath (X i))
    (hX : ∀ i,
      AEMeasurable (VdVWEllInfty.processMap (X i) (hbounded i)) (μ i))
    {l l' : Filter ι}
    (h : VdVWEllInftyProcessAsymptoticallyTight (T := T) μ X hbounded hX l)
    (hl : l' ≤ l) :
    VdVWEllInftyProcessAsymptoticallyTight (T := T) μ X hbounded hX l' :=
  VdVWProbabilityMeasuresAsymptoticallyTight.mono_filter
    (show VdVWProbabilityMeasuresAsymptoticallyTight
      (fun i => vdVWEllInftyProcessLaw (T := T) (μ i) (X i) (hbounded i) (hX i)) l from h)
    hl

/--
Process-level asymptotic tightness is stable under reindexing along a map
tending to the original index filter.
-/
theorem VdVWEllInftyProcessAsymptoticallyTight.comp_tendsto
    {ι κ : Type*} {Ω : ι -> Type*}
    {mΩ : (i : ι) -> MeasurableSpace (Ω i)}
    (μ : (i : ι) -> @Measure (Ω i) (mΩ i)) [∀ i, IsProbabilityMeasure (μ i)]
    [MeasurableSpace (VdVWEllInfty T)]
    (X : (i : ι) -> Ω i -> T -> ℝ)
    (hbounded : ∀ i, VdVWEllInfty.IsBoundedSamplePath (X i))
    (hX : ∀ i,
      AEMeasurable (VdVWEllInfty.processMap (X i) (hbounded i)) (μ i))
    {l : Filter ι} {l' : Filter κ} {φ : κ -> ι}
    (h : VdVWEllInftyProcessAsymptoticallyTight (T := T) μ X hbounded hX l)
    (hφ : Filter.Tendsto φ l' l) :
    VdVWEllInftyProcessAsymptoticallyTight
      (T := T) (fun k => μ (φ k)) (fun k => X (φ k))
        (fun k => hbounded (φ k)) (fun k => hX (φ k)) l' :=
  VdVWProbabilityMeasuresAsymptoticallyTight.comp_tendsto
    (show VdVWProbabilityMeasuresAsymptoticallyTight
      (fun i => vdVWEllInftyProcessLaw (T := T) (μ i) (X i) (hbounded i) (hX i)) l from h)
    hφ

/--
Process-level asymptotic tightness is unchanged by replacing the source
processes by a.e.-equal bounded process maps eventually along the index filter.
-/
theorem VdVWEllInftyProcessAsymptoticallyTight.congr_eventually_ae
    {ι : Type*} {Ω : ι -> Type*}
    {mΩ : (i : ι) -> MeasurableSpace (Ω i)}
    (μ : (i : ι) -> @Measure (Ω i) (mΩ i)) [∀ i, IsProbabilityMeasure (μ i)]
    [MeasurableSpace (VdVWEllInfty T)]
    (X Y : (i : ι) -> Ω i -> T -> ℝ)
    (hXbounded : ∀ i, VdVWEllInfty.IsBoundedSamplePath (X i))
    (hYbounded : ∀ i, VdVWEllInfty.IsBoundedSamplePath (Y i))
    (hX : ∀ i,
      AEMeasurable (VdVWEllInfty.processMap (X i) (hXbounded i)) (μ i))
    (hY : ∀ i,
      AEMeasurable (VdVWEllInfty.processMap (Y i) (hYbounded i)) (μ i))
    {l : Filter ι}
    (h : VdVWEllInftyProcessAsymptoticallyTight (T := T) μ X hXbounded hX l)
    (hXY : ∀ᶠ i in l,
      VdVWEllInfty.processMap (Y i) (hYbounded i) =ᵐ[μ i]
        VdVWEllInfty.processMap (X i) (hXbounded i)) :
    VdVWEllInftyProcessAsymptoticallyTight (T := T) μ Y hYbounded hY l :=
  VdVWProbabilityMeasuresAsymptoticallyTight.congr_eventually
    (show VdVWProbabilityMeasuresAsymptoticallyTight
      (fun i => vdVWEllInftyProcessLaw (T := T) (μ i) (X i) (hXbounded i) (hX i)) l from h)
    (hXY.mono fun i hi =>
      vdVWEllInftyProcessLaw_congr_ae
        (T := T) (P := μ i) (X := X i) (Y := Y i)
        (hXbounded := hXbounded i) (hYbounded := hYbounded i)
        (hX := hX i) (hY := hY i) hi)

/--
Process-level asymptotic tightness is unchanged by replacing source raw
processes with sample-path a.e.-equal versions eventually along the index
filter.
-/
theorem VdVWEllInftyProcessAsymptoticallyTight.congr_eventually_forall_coord_ae
    {ι : Type*} {Ω : ι -> Type*}
    {mΩ : (i : ι) -> MeasurableSpace (Ω i)}
    (μ : (i : ι) -> @Measure (Ω i) (mΩ i)) [∀ i, IsProbabilityMeasure (μ i)]
    [MeasurableSpace (VdVWEllInfty T)]
    (X Y : (i : ι) -> Ω i -> T -> ℝ)
    (hXbounded : ∀ i, VdVWEllInfty.IsBoundedSamplePath (X i))
    (hYbounded : ∀ i, VdVWEllInfty.IsBoundedSamplePath (Y i))
    (hX : ∀ i,
      AEMeasurable (VdVWEllInfty.processMap (X i) (hXbounded i)) (μ i))
    (hY : ∀ i,
      AEMeasurable (VdVWEllInfty.processMap (Y i) (hYbounded i)) (μ i))
    {l : Filter ι}
    (h : VdVWEllInftyProcessAsymptoticallyTight (T := T) μ X hXbounded hX l)
    (hXY : ∀ᶠ i in l, ∀ᵐ ω ∂μ i, ∀ t, Y i ω t = X i ω t) :
    VdVWEllInftyProcessAsymptoticallyTight (T := T) μ Y hYbounded hY l :=
  VdVWEllInftyProcessAsymptoticallyTight.congr_eventually_ae
    (T := T) μ X Y hXbounded hYbounded hX hY h
    (hXY.mono fun i hi =>
      VdVWEllInfty.processMap_congr_ae (hXbounded i) (hYbounded i) hi)

/--
Process-level tightness implies tightness of every finite-dimensional law.

This packages the existing measure-level continuous-image tightness theorem
with the raw-process finite-dimensional law identity above.
-/
theorem VdVWEllInftyProcessAsymptoticallyTight.finiteDimensionalLaw
    {ι : Type*} {Ω : ι -> Type*}
    {mΩ : (i : ι) -> MeasurableSpace (Ω i)}
    (μ : (i : ι) -> @Measure (Ω i) (mΩ i)) [∀ i, IsProbabilityMeasure (μ i)]
    [MeasurableSpace (VdVWEllInfty T)] [OpensMeasurableSpace (VdVWEllInfty T)]
    [BorelSpace (VdVWEllInfty T)]
    (X : (i : ι) -> Ω i -> T -> ℝ)
    (hbounded : ∀ i, VdVWEllInfty.IsBoundedSamplePath (X i))
    (hX : ∀ i,
      AEMeasurable (VdVWEllInfty.processMap (X i) (hbounded i)) (μ i))
    {l : Filter ι}
    (h : VdVWEllInftyProcessAsymptoticallyTight
      (T := T) μ X hbounded hX l)
    (I : Finset T) [MeasurableSpace (I -> ℝ)] [BorelSpace (I -> ℝ)]
    [T2Space (I -> ℝ)] :
    VdVWProbabilityMeasuresAsymptoticallyTight
      (fun i => vdVWFDDProcessLaw (μ i) I (X i)
        (aemeasurable_fdd_of_aemeasurable_ellInftyProcessMap (T := T) I (hX i))) l := by
  have hmap :
      VdVWProbabilityMeasuresAsymptoticallyTight
        (fun i =>
          (vdVWEllInftyProcessLaw (T := T) (μ i) (X i) (hbounded i) (hX i)).map
            ((VdVWEllInfty.continuous_finiteRestrict (T := T) I).measurable.aemeasurable))
        l :=
    h.map_continuous (VdVWEllInfty.continuous_finiteRestrict (T := T) I)
  exact hmap.congr_eventually (Filter.Eventually.of_forall fun i =>
    (vdVWEllInftyProcessLaw_map_finiteRestrict
      (T := T) (P := μ i) (X := X i) (hbounded := hbounded i) (hX := hX i) I).symm)

/--
Finite-dimensional asymptotic tightness from a process law is stable under
eventually replacing only the selected finite coordinates a.e.

This is a fixed-FDD tightness replacement primitive, not the arbitrary-index
tightness/FDD converse.
-/
theorem VdVWEllInftyProcessAsymptoticallyTight.finiteDimensionalLaw_congr_eventually_finite_coord_ae
    {ι : Type*} {Ω : ι -> Type*}
    {mΩ : (i : ι) -> MeasurableSpace (Ω i)}
    (μ : (i : ι) -> @Measure (Ω i) (mΩ i)) [∀ i, IsProbabilityMeasure (μ i)]
    [MeasurableSpace (VdVWEllInfty T)] [OpensMeasurableSpace (VdVWEllInfty T)]
    [BorelSpace (VdVWEllInfty T)]
    (X Y : (i : ι) -> Ω i -> T -> ℝ)
    (hbounded : ∀ i, VdVWEllInfty.IsBoundedSamplePath (X i))
    (hX : ∀ i,
      AEMeasurable (VdVWEllInfty.processMap (X i) (hbounded i)) (μ i))
    {l : Filter ι}
    (h : VdVWEllInftyProcessAsymptoticallyTight
      (T := T) μ X hbounded hX l)
    (I : Finset T) [MeasurableSpace (I -> ℝ)] [BorelSpace (I -> ℝ)]
    [T2Space (I -> ℝ)]
    (hY : ∀ i, AEMeasurable (fun ω => fun t : I => Y i ω t.1) (μ i))
    (hYX : ∀ᶠ i in l, ∀ᵐ ω ∂(μ i), ∀ t : I, Y i ω t.1 = X i ω t.1) :
    VdVWProbabilityMeasuresAsymptoticallyTight
      (fun i => vdVWFDDProcessLaw (μ i) I (Y i) (hY i)) l := by
  have hfdd :=
    VdVWEllInftyProcessAsymptoticallyTight.finiteDimensionalLaw
      (T := T) μ X hbounded hX h I
  exact hfdd.congr_eventually (hYX.mono fun i hi =>
    vdVWFDDProcessLaw_congr_finite_coord_ae
      (P := μ i) I (X i) (Y i)
      (aemeasurable_fdd_of_aemeasurable_ellInftyProcessMap (T := T) I (hX i))
      (hY i) hi)

/--
Process-level asymptotic tightness implies asymptotic tightness of every
single-coordinate law.

This is the coordinate version of the forward finite-dimensional tightness
handoff.  It is still a continuous-image result, not the VdV&W arbitrary-index
tightness/FDD converse.
-/
theorem VdVWEllInftyProcessAsymptoticallyTight.coordinateLaw
    {ι : Type*} {Ω : ι -> Type*}
    {mΩ : (i : ι) -> MeasurableSpace (Ω i)}
    (μ : (i : ι) -> @Measure (Ω i) (mΩ i)) [∀ i, IsProbabilityMeasure (μ i)]
    [MeasurableSpace (VdVWEllInfty T)] [OpensMeasurableSpace (VdVWEllInfty T)]
    [BorelSpace (VdVWEllInfty T)]
    (X : (i : ι) -> Ω i -> T -> ℝ)
    (hbounded : ∀ i, VdVWEllInfty.IsBoundedSamplePath (X i))
    (hX : ∀ i,
      AEMeasurable (VdVWEllInfty.processMap (X i) (hbounded i)) (μ i))
    {l : Filter ι}
    (h : VdVWEllInftyProcessAsymptoticallyTight
      (T := T) μ X hbounded hX l)
    (t : T) :
    VdVWProbabilityMeasuresAsymptoticallyTight
      (fun i =>
        (vdVWEllInftyProcessLaw (T := T) (μ i) (X i) (hbounded i) (hX i)).map
          ((VdVWEllInfty.evalCLM (T := T) t).continuous.measurable.aemeasurable))
      l :=
  h.map_continuous (VdVWEllInfty.evalCLM (T := T) t).continuous

/--
Process-level asymptotic tightness implies asymptotic tightness of the ordinary
raw single-coordinate process laws.

This is the raw-law form of the continuous-image coordinate tightness result.
-/
theorem VdVWEllInftyProcessAsymptoticallyTight.rawCoordinateLaw
    {ι : Type*} {Ω : ι -> Type*}
    {mΩ : (i : ι) -> MeasurableSpace (Ω i)}
    (μ : (i : ι) -> @Measure (Ω i) (mΩ i)) [∀ i, IsProbabilityMeasure (μ i)]
    [MeasurableSpace (VdVWEllInfty T)] [OpensMeasurableSpace (VdVWEllInfty T)]
    [BorelSpace (VdVWEllInfty T)]
    (X : (i : ι) -> Ω i -> T -> ℝ)
    (hbounded : ∀ i, VdVWEllInfty.IsBoundedSamplePath (X i))
    (hX : ∀ i,
      AEMeasurable (VdVWEllInfty.processMap (X i) (hbounded i)) (μ i))
    {l : Filter ι}
    (h : VdVWEllInftyProcessAsymptoticallyTight
      (T := T) μ X hbounded hX l)
    (t : T) :
    VdVWProbabilityMeasuresAsymptoticallyTight
      (fun i => vdVWCoordinateProcessLaw (μ i) (X i) t
        ((VdVWEllInfty.evalCLM (T := T) t).continuous.measurable.aemeasurable.comp_aemeasurable
          (hX i)))
      l := by
  have hcoord :=
    VdVWEllInftyProcessAsymptoticallyTight.coordinateLaw
      (T := T) μ X hbounded hX h t
  exact hcoord.congr_eventually (Filter.Eventually.of_forall fun i =>
    (vdVWEllInftyProcessLaw_map_eval
      (T := T) (P := μ i) (X := X i) (hbounded := hbounded i) (hX := hX i) t).symm)

/--
Raw coordinate-law asymptotic tightness is stable under eventually replacing
the source coordinates by a.e.-equal versions.

This is the tightness analogue of
`VdVWEllInftyProcessWeakConvergence.rawCoordinateLaw_congr_eventually_ae`.
-/
theorem VdVWEllInftyProcessAsymptoticallyTight.rawCoordinateLaw_congr_eventually_ae
    {ι : Type*} {Ω : ι -> Type*}
    {mΩ : (i : ι) -> MeasurableSpace (Ω i)}
    (μ : (i : ι) -> @Measure (Ω i) (mΩ i)) [∀ i, IsProbabilityMeasure (μ i)]
    [MeasurableSpace (VdVWEllInfty T)] [OpensMeasurableSpace (VdVWEllInfty T)]
    [BorelSpace (VdVWEllInfty T)]
    (X Y : (i : ι) -> Ω i -> T -> ℝ)
    (hbounded : ∀ i, VdVWEllInfty.IsBoundedSamplePath (X i))
    (hX : ∀ i,
      AEMeasurable (VdVWEllInfty.processMap (X i) (hbounded i)) (μ i))
    {l : Filter ι}
    (h : VdVWEllInftyProcessAsymptoticallyTight
      (T := T) μ X hbounded hX l)
    (t : T)
    (hY : ∀ i, AEMeasurable (fun ω => Y i ω t) (μ i))
    (hYX : ∀ᶠ i in l, ∀ᵐ ω ∂(μ i), Y i ω t = X i ω t) :
    VdVWProbabilityMeasuresAsymptoticallyTight
      (fun i => vdVWCoordinateProcessLaw (μ i) (Y i) t (hY i))
      l := by
  have hcoord :=
    VdVWEllInftyProcessAsymptoticallyTight.rawCoordinateLaw
      (T := T) μ X hbounded hX h t
  exact hcoord.congr_eventually (hYX.mono fun i hi =>
    vdVWCoordinateProcessLaw_congr_ae
      (P := μ i) (X := X i) (Y := Y i) (t := t)
      ((VdVWEllInfty.evalCLM (T := T) t).continuous.measurable.aemeasurable.comp_aemeasurable
        (hX i))
      (hY i) hi)

/--
Sequential weak convergence of bounded `ell_infty(T)` process laws implies
process-level asymptotic tightness.

This is the raw-process form of the measure-level Prokhorov/tightness
consequence already available in `WeakConvergence.lean`.
-/
theorem VdVWEllInftyProcessWeakConvergence.asymptoticallyTight_atTop
    {Ω : ℕ -> Type*} {Ωlim : Type*}
    {mΩ : (n : ℕ) -> MeasurableSpace (Ω n)}
    (μ : (n : ℕ) -> @Measure (Ω n) (mΩ n)) [∀ n, IsProbabilityMeasure (μ n)]
    [MeasurableSpace Ωlim] (μlim : Measure Ωlim) [IsProbabilityMeasure μlim]
    [MeasurableSpace (VdVWEllInfty T)] [OpensMeasurableSpace (VdVWEllInfty T)]
    [BorelSpace (VdVWEllInfty T)] [SecondCountableTopology (VdVWEllInfty T)]
    [CompleteSpace (VdVWEllInfty T)]
    (X : (n : ℕ) -> Ω n -> T -> ℝ)
    (Z : Ωlim -> T -> ℝ)
    (hbounded : ∀ n, VdVWEllInfty.IsBoundedSamplePath (X n))
    (hZbounded : VdVWEllInfty.IsBoundedSamplePath Z)
    (hX : ∀ n,
      AEMeasurable (VdVWEllInfty.processMap (X n) (hbounded n)) (μ n))
    (hZ : AEMeasurable (VdVWEllInfty.processMap Z hZbounded) μlim)
    (h : VdVWEllInftyProcessWeakConvergence
      (T := T) μ μlim X Z hbounded hZbounded hX hZ Filter.atTop) :
    VdVWEllInftyProcessAsymptoticallyTight μ X hbounded hX Filter.atTop := by
  exact
    VdVWWeakConvergenceProbabilityMeasures.asymptoticallyTight_atTop
      (S := VdVWEllInfty T)
      (μs := fun n => vdVWEllInftyProcessLaw (T := T) (μ n) (X n) (hbounded n) (hX n))
      (μ := vdVWEllInftyProcessLaw (T := T) μlim Z hZbounded hZ)
      (show VdVWWeakConvergenceProbabilityMeasures
        (fun n => vdVWEllInftyProcessLaw (T := T) (μ n) (X n) (hbounded n) (hX n))
        Filter.atTop
        (vdVWEllInftyProcessLaw (T := T) μlim Z hZbounded hZ) from h)

/--
Sequential weak convergence of bounded process laws implies asymptotic
tightness of every finite-dimensional raw coordinate law.
-/
theorem VdVWEllInftyProcessWeakConvergence.finiteDimensionalLaw_asymptoticallyTight_atTop
    {Ω : ℕ -> Type*} {Ωlim : Type*}
    {mΩ : (n : ℕ) -> MeasurableSpace (Ω n)}
    (μ : (n : ℕ) -> @Measure (Ω n) (mΩ n)) [∀ n, IsProbabilityMeasure (μ n)]
    [MeasurableSpace Ωlim] (μlim : Measure Ωlim) [IsProbabilityMeasure μlim]
    [MeasurableSpace (VdVWEllInfty T)] [OpensMeasurableSpace (VdVWEllInfty T)]
    [BorelSpace (VdVWEllInfty T)] [SecondCountableTopology (VdVWEllInfty T)]
    [CompleteSpace (VdVWEllInfty T)]
    (X : (n : ℕ) -> Ω n -> T -> ℝ)
    (Z : Ωlim -> T -> ℝ)
    (hbounded : ∀ n, VdVWEllInfty.IsBoundedSamplePath (X n))
    (hZbounded : VdVWEllInfty.IsBoundedSamplePath Z)
    (hX : ∀ n,
      AEMeasurable (VdVWEllInfty.processMap (X n) (hbounded n)) (μ n))
    (hZ : AEMeasurable (VdVWEllInfty.processMap Z hZbounded) μlim)
    (h : VdVWEllInftyProcessWeakConvergence
      (T := T) μ μlim X Z hbounded hZbounded hX hZ Filter.atTop)
    (I : Finset T) [MeasurableSpace (I -> ℝ)] [BorelSpace (I -> ℝ)]
    [T2Space (I -> ℝ)] :
    VdVWProbabilityMeasuresAsymptoticallyTight
      (fun n => vdVWFDDProcessLaw (μ n) I (X n)
        (aemeasurable_fdd_of_aemeasurable_ellInftyProcessMap (T := T) I (hX n)))
      Filter.atTop :=
  (VdVWEllInftyProcessWeakConvergence.asymptoticallyTight_atTop
    μ μlim X Z hbounded hZbounded hX hZ h).finiteDimensionalLaw
      μ X hbounded hX I

/--
Sequential weak convergence of bounded process laws implies asymptotic
tightness of every ordinary raw coordinate law.
-/
theorem VdVWEllInftyProcessWeakConvergence.rawCoordinateLaw_asymptoticallyTight_atTop
    {Ω : ℕ -> Type*} {Ωlim : Type*}
    {mΩ : (n : ℕ) -> MeasurableSpace (Ω n)}
    (μ : (n : ℕ) -> @Measure (Ω n) (mΩ n)) [∀ n, IsProbabilityMeasure (μ n)]
    [MeasurableSpace Ωlim] (μlim : Measure Ωlim) [IsProbabilityMeasure μlim]
    [MeasurableSpace (VdVWEllInfty T)] [OpensMeasurableSpace (VdVWEllInfty T)]
    [BorelSpace (VdVWEllInfty T)] [SecondCountableTopology (VdVWEllInfty T)]
    [CompleteSpace (VdVWEllInfty T)]
    (X : (n : ℕ) -> Ω n -> T -> ℝ)
    (Z : Ωlim -> T -> ℝ)
    (hbounded : ∀ n, VdVWEllInfty.IsBoundedSamplePath (X n))
    (hZbounded : VdVWEllInfty.IsBoundedSamplePath Z)
    (hX : ∀ n,
      AEMeasurable (VdVWEllInfty.processMap (X n) (hbounded n)) (μ n))
    (hZ : AEMeasurable (VdVWEllInfty.processMap Z hZbounded) μlim)
    (h : VdVWEllInftyProcessWeakConvergence
      (T := T) μ μlim X Z hbounded hZbounded hX hZ Filter.atTop)
    (t : T) :
    VdVWProbabilityMeasuresAsymptoticallyTight
      (fun n => vdVWCoordinateProcessLaw (μ n) (X n) t
        ((VdVWEllInfty.evalCLM (T := T) t).continuous.measurable.aemeasurable.comp_aemeasurable
          (hX n)))
      Filter.atTop :=
  (VdVWEllInftyProcessWeakConvergence.asymptoticallyTight_atTop
    μ μlim X Z hbounded hZbounded hX hZ h).rawCoordinateLaw
      μ X hbounded hX t

/--
Sequential weak convergence of bounded process laws implies asymptotic
tightness of replacement finite-dimensional laws when only the selected finite
coordinates are eventually a.e.-equal.
-/
theorem
    VdVWEllInftyProcessWeakConvergence.finiteDimensionalLaw_congr_eventually_finite_coord_ae_asymptoticallyTight_atTop
    {Ω : ℕ -> Type*} {Ωlim : Type*}
    {mΩ : (n : ℕ) -> MeasurableSpace (Ω n)}
    (μ : (n : ℕ) -> @Measure (Ω n) (mΩ n)) [∀ n, IsProbabilityMeasure (μ n)]
    [MeasurableSpace Ωlim] (μlim : Measure Ωlim) [IsProbabilityMeasure μlim]
    [MeasurableSpace (VdVWEllInfty T)] [OpensMeasurableSpace (VdVWEllInfty T)]
    [BorelSpace (VdVWEllInfty T)] [SecondCountableTopology (VdVWEllInfty T)]
    [CompleteSpace (VdVWEllInfty T)]
    (X Y : (n : ℕ) -> Ω n -> T -> ℝ)
    (Z : Ωlim -> T -> ℝ)
    (hbounded : ∀ n, VdVWEllInfty.IsBoundedSamplePath (X n))
    (hZbounded : VdVWEllInfty.IsBoundedSamplePath Z)
    (hX : ∀ n,
      AEMeasurable (VdVWEllInfty.processMap (X n) (hbounded n)) (μ n))
    (hZ : AEMeasurable (VdVWEllInfty.processMap Z hZbounded) μlim)
    (h : VdVWEllInftyProcessWeakConvergence
      (T := T) μ μlim X Z hbounded hZbounded hX hZ Filter.atTop)
    (I : Finset T) [MeasurableSpace (I -> ℝ)] [BorelSpace (I -> ℝ)]
    [T2Space (I -> ℝ)]
    (hY : ∀ n, AEMeasurable (fun ω => fun t : I => Y n ω t.1) (μ n))
    (hYX : ∀ᶠ n in Filter.atTop, ∀ᵐ ω ∂(μ n), ∀ t : I, Y n ω t.1 = X n ω t.1) :
    VdVWProbabilityMeasuresAsymptoticallyTight
      (fun n => vdVWFDDProcessLaw (μ n) I (Y n) (hY n)) Filter.atTop :=
  (VdVWEllInftyProcessWeakConvergence.asymptoticallyTight_atTop
    μ μlim X Z hbounded hZbounded hX hZ h).finiteDimensionalLaw_congr_eventually_finite_coord_ae
      μ X Y hbounded hX I hY hYX

/--
Sequential weak convergence of bounded process laws implies asymptotic
tightness of replacement raw coordinate laws when that coordinate is eventually
a.e.-equal.
-/
theorem
    VdVWEllInftyProcessWeakConvergence.rawCoordinateLaw_congr_eventually_ae_asymptoticallyTight_atTop
    {Ω : ℕ -> Type*} {Ωlim : Type*}
    {mΩ : (n : ℕ) -> MeasurableSpace (Ω n)}
    (μ : (n : ℕ) -> @Measure (Ω n) (mΩ n)) [∀ n, IsProbabilityMeasure (μ n)]
    [MeasurableSpace Ωlim] (μlim : Measure Ωlim) [IsProbabilityMeasure μlim]
    [MeasurableSpace (VdVWEllInfty T)] [OpensMeasurableSpace (VdVWEllInfty T)]
    [BorelSpace (VdVWEllInfty T)] [SecondCountableTopology (VdVWEllInfty T)]
    [CompleteSpace (VdVWEllInfty T)]
    (X Y : (n : ℕ) -> Ω n -> T -> ℝ)
    (Z : Ωlim -> T -> ℝ)
    (hbounded : ∀ n, VdVWEllInfty.IsBoundedSamplePath (X n))
    (hZbounded : VdVWEllInfty.IsBoundedSamplePath Z)
    (hX : ∀ n,
      AEMeasurable (VdVWEllInfty.processMap (X n) (hbounded n)) (μ n))
    (hZ : AEMeasurable (VdVWEllInfty.processMap Z hZbounded) μlim)
    (h : VdVWEllInftyProcessWeakConvergence
      (T := T) μ μlim X Z hbounded hZbounded hX hZ Filter.atTop)
    (t : T)
    (hY : ∀ n, AEMeasurable (fun ω => Y n ω t) (μ n))
    (hYX : ∀ᶠ n in Filter.atTop, ∀ᵐ ω ∂(μ n), Y n ω t = X n ω t) :
    VdVWProbabilityMeasuresAsymptoticallyTight
      (fun n => vdVWCoordinateProcessLaw (μ n) (Y n) t (hY n))
      Filter.atTop :=
  (VdVWEllInftyProcessWeakConvergence.asymptoticallyTight_atTop
    μ μlim X Z hbounded hZbounded hX hZ h).rawCoordinateLaw_congr_eventually_ae
      μ X Y hbounded hX t hY hYX

end StatInference
