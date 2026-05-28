import StatInference.EmpiricalProcess.Basic

/-!
# Outer empirical-process convergence signatures

This module records the outer-probability vocabulary needed for the exact
van der Vaart and Wellner Glivenko-Cantelli statements.

The declarations are intentionally semantic interfaces.  They do not replace
ordinary measurability assumptions with shortcuts, and they do not claim that a
deterministic `GlivenkoCantelliClass` certificate is already the exact
outer-almost-sure textbook theorem.
-/

namespace StatInference

open Filter
open scoped Topology

/--
Minimal outer-probability carrier for empirical-process statements.

The fields are deliberately modest: enough to state outer convergence targets
without pretending that the complete measure-theoretic outer-measure theory has
already been formalized in this project.
-/
structure OuterProbabilitySpace (Ω : Type*) [MeasurableSpace Ω] where
  outerProb : Set Ω -> ℝ
  empty : outerProb ∅ = 0
  monotone : ∀ ⦃event₁ event₂ : Set Ω⦄, event₁ ⊆ event₂ ->
    outerProb event₁ ≤ outerProb event₂
  univ_le_one : outerProb Set.univ ≤ 1

namespace OuterProbabilitySpace

/-- Monotonicity projection for premise retrieval. -/
theorem event_mono {Ω : Type*} [MeasurableSpace Ω]
    (outer : OuterProbabilitySpace Ω)
    {event₁ event₂ : Set Ω} (hsubset : event₁ ⊆ event₂) :
    outer.outerProb event₁ ≤ outer.outerProb event₂ :=
  outer.monotone hsubset

end OuterProbabilitySpace

/--
Outer convergence in probability to a real limit.

This is the VdV&W-style signature for possibly nonmeasurable empirical-process
suprema: every positive tolerance has outer probability tending to zero.
-/
def OuterTendstoInProbability {Ω : Type*} [MeasurableSpace Ω]
    (outer : OuterProbabilitySpace Ω) (process : ℕ -> Ω -> ℝ)
    (limit : ℝ) : Prop :=
  ∀ tolerance, 0 < tolerance ->
    Tendsto
      (fun sampleSize =>
        outer.outerProb
          {ω | tolerance < |process sampleSize ω - limit|})
      atTop (𝓝 0)

/--
Outer almost-sure convergence to a real limit.

The bad event is measured by outer probability.  This is only the statement
interface; proving usable constructors for it remains later work.
-/
def OuterAlmostSureTendsto {Ω : Type*} [MeasurableSpace Ω]
    (outer : OuterProbabilitySpace Ω) (process : ℕ -> Ω -> ℝ)
    (limit : ℝ) : Prop :=
  outer.outerProb
      {ω | ¬ Tendsto (fun sampleSize => process sampleSize ω) atTop (𝓝 limit)} =
    0

/--
Supremum deviation over an index class.

This is the deterministic real-valued supremum that will become
`‖Pₙ - P‖*_𝓕` once paired with outer-probability semantics.
-/
noncomputable def OuterSupremumDeviation {Index : Type*}
    (indexClass : Set Index)
    (populationRisk empiricalRisk : Index -> ℝ) : ℝ :=
  sSup ((fun index => |empiricalRisk index - populationRisk index|) '' indexClass)

/-- Unfold the outer supremum-deviation signature. -/
theorem OuterSupremumDeviation_eq {Index : Type*}
    (indexClass : Set Index)
    (populationRisk empiricalRisk : Index -> ℝ) :
    OuterSupremumDeviation indexClass populationRisk empiricalRisk =
      sSup
        ((fun index => |empiricalRisk index - populationRisk index|) ''
          indexClass) :=
  rfl

/--
Outer Glivenko-Cantelli target over an indexed class.

This packages a random supremum-deviation process and the intended outer
almost-sure and in-probability targets.  It is stronger bookkeeping than the
current deterministic `GlivenkoCantelliClass`, but still only a statement
interface until constructors are proved.
-/
structure OuterGlivenkoCantelliClass {Ω Index : Type*} [MeasurableSpace Ω]
    (outer : OuterProbabilitySpace Ω) (indexClass : Set Index)
    (populationRisk : Index -> ℝ)
    (empiricalRisk : ℕ -> Ω -> Index -> ℝ) where
  deviation : ℕ -> Ω -> ℝ
  deviation_eq :
    ∀ sampleSize ω,
      deviation sampleSize ω =
        OuterSupremumDeviation indexClass populationRisk
          (empiricalRisk sampleSize ω)
  outer_tendsto_in_probability :
    OuterTendstoInProbability outer deviation 0
  outer_almost_sure_tendsto :
    OuterAlmostSureTendsto outer deviation 0

namespace OuterGlivenkoCantelliClass

/-- Project the outer-in-probability target from an outer GC certificate. -/
theorem tendstoInProbability {Ω Index : Type*} [MeasurableSpace Ω]
    {outer : OuterProbabilitySpace Ω} {indexClass : Set Index}
    {populationRisk : Index -> ℝ}
    {empiricalRisk : ℕ -> Ω -> Index -> ℝ}
    (gc :
      OuterGlivenkoCantelliClass outer indexClass populationRisk empiricalRisk) :
    OuterTendstoInProbability outer gc.deviation 0 :=
  gc.outer_tendsto_in_probability

/-- Project the outer almost-sure target from an outer GC certificate. -/
theorem almostSureTendsto {Ω Index : Type*} [MeasurableSpace Ω]
    {outer : OuterProbabilitySpace Ω} {indexClass : Set Index}
    {populationRisk : Index -> ℝ}
    {empiricalRisk : ℕ -> Ω -> Index -> ℝ}
    (gc :
      OuterGlivenkoCantelliClass outer indexClass populationRisk empiricalRisk) :
    OuterAlmostSureTendsto outer gc.deviation 0 :=
  gc.outer_almost_sure_tendsto

end OuterGlivenkoCantelliClass

end StatInference
