import Mathlib.MeasureTheory.OuterMeasure.BorelCantelli
import Mathlib.Probability.BorelCantelli

/-!
# Borel-Cantelli wrappers

This module records content-based wrappers for the first and second
Borel-Cantelli lemmas.  These are useful for textbook probability source
crosswalks and for empirical-process tail-event arguments.
-/

namespace StatInference
namespace ProbabilityMeasure

open Filter MeasureTheory ProbabilityTheory

open scoped ENNReal

universe u

/--
First Borel-Cantelli lemma: if the measures of a sequence of events are
summable, then the limsup event has measure zero.
-/
theorem measure_limsup_atTop_eq_zero
    {Ω : Type u} [MeasurableSpace Ω] {μ : Measure Ω}
    {s : ℕ -> Set Ω}
    (hs : (∑' n, μ (s n)) ≠ ∞) :
    μ (limsup s atTop) = 0 := by
  exact MeasureTheory.measure_limsup_atTop_eq_zero hs

/--
First Borel-Cantelli in eventual form: under summability, almost every point
belongs to only finitely many events.
-/
theorem ae_eventually_notMem
    {Ω : Type u} [MeasurableSpace Ω] {μ : Measure Ω}
    {s : ℕ -> Set Ω}
    (hs : (∑' n, μ (s n)) ≠ ∞) :
    ∀ᵐ ω ∂μ, ∀ᶠ n in atTop, ω ∉ s n := by
  exact MeasureTheory.ae_eventually_notMem hs

/--
Second Borel-Cantelli lemma: for independent measurable events in a probability
space, divergent total mass forces the limsup event to have probability one.
-/
theorem measure_limsup_eq_one
    {Ω : Type u} [MeasurableSpace Ω] {μ : Measure Ω}
    {s : ℕ -> Set Ω}
    (hsm : ∀ n, MeasurableSet (s n))
    (hs_indep : iIndepSet s μ)
    (hs_sum : (∑' n, μ (s n)) = ∞) :
    μ (limsup s atTop) = 1 := by
  exact ProbabilityTheory.measure_limsup_eq_one hsm hs_indep hs_sum

end ProbabilityMeasure
end StatInference
