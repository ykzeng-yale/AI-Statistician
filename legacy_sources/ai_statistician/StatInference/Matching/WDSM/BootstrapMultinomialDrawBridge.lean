import Mathlib.Data.Finset.Basic
import StatInference.Matching.WDSM.BootstrapMultinomialCountBridge
import Mathlib.Tactic.Ring

/-!
# Multinomial draw-to-count bridge

The WDSM bootstrap draws multinomial counts.  A count can be represented as a
sum of one-hot draw indicators.  This module proves the finite algebra that
draw-level moment sums imply the raw count moments consumed by
`BootstrapMultinomialCountBridge`.

The remaining probability task can now be localized to one-hot draw moment
facts for the concrete equal-probability resampling law.
-/

namespace StatInference
namespace Matching
namespace WDSM

open scoped BigOperators

variable {Unit Draw Omega : Type*}

/-- Count for a unit as a finite sum of one-hot draw indicators. -/
noncomputable def multinomialCountFromDrawIndicators
    (draws : Finset Draw)
    (drawIndicator : Omega -> Draw -> Unit -> Real)
    (omega : Omega) (unit : Unit) : Real :=
  ∑ draw ∈ draws, drawIndicator omega draw unit

/-- Expectation of the count is the sum of draw-level expectations. -/
theorem finiteExpectation_multinomialCountFromDrawIndicators_eq_sum_draw_expectations
    (support : Finset Omega) (mass : Omega -> Real)
    (draws : Finset Draw)
    (drawIndicator : Omega -> Draw -> Unit -> Real)
    (unit : Unit) :
    finiteExpectation support mass
        (fun omega =>
          multinomialCountFromDrawIndicators draws drawIndicator omega unit) =
      ∑ draw ∈ draws,
        finiteExpectation support mass
          (fun omega => drawIndicator omega draw unit) := by
  unfold multinomialCountFromDrawIndicators
  exact finiteExpectation_sum support mass draws
    (fun omega draw => drawIndicator omega draw unit)

/-- Pointwise product of two count sums as a double draw sum. -/
theorem multinomialCountFromDrawIndicators_mul_eq_double_sum
    (draws : Finset Draw)
    (drawIndicator : Omega -> Draw -> Unit -> Real)
    (omega : Omega) (left right : Unit) :
    multinomialCountFromDrawIndicators draws drawIndicator omega left *
        multinomialCountFromDrawIndicators draws drawIndicator omega right =
      ∑ drawA ∈ draws, ∑ drawB ∈ draws,
        drawIndicator omega drawA left *
          drawIndicator omega drawB right := by
  unfold multinomialCountFromDrawIndicators
  calc
    (∑ drawA ∈ draws, drawIndicator omega drawA left) *
        (∑ drawB ∈ draws, drawIndicator omega drawB right) =
        ∑ drawA ∈ draws,
          drawIndicator omega drawA left *
            (∑ drawB ∈ draws, drawIndicator omega drawB right) := by
          rw [Finset.sum_mul]
    _ =
        ∑ drawA ∈ draws, ∑ drawB ∈ draws,
          drawIndicator omega drawA left *
            drawIndicator omega drawB right := by
          exact Finset.sum_congr rfl
            (fun drawA _hdrawA => by rw [Finset.mul_sum])

/-- Count cross moments are double sums of draw-level cross moments. -/
theorem finiteExpectation_multinomialCountFromDrawIndicators_mul_eq_sum_draw_cross_expectations
    (support : Finset Omega) (mass : Omega -> Real)
    (draws : Finset Draw)
    (drawIndicator : Omega -> Draw -> Unit -> Real)
    (left right : Unit) :
    finiteExpectation support mass
        (fun omega =>
          multinomialCountFromDrawIndicators draws drawIndicator omega left *
            multinomialCountFromDrawIndicators draws drawIndicator omega right) =
      ∑ drawA ∈ draws, ∑ drawB ∈ draws,
        finiteExpectation support mass
          (fun omega =>
            drawIndicator omega drawA left *
              drawIndicator omega drawB right) := by
  calc
    finiteExpectation support mass
        (fun omega =>
          multinomialCountFromDrawIndicators draws drawIndicator omega left *
            multinomialCountFromDrawIndicators draws drawIndicator omega right) =
        finiteExpectation support mass
          (fun omega =>
            ∑ drawA ∈ draws, ∑ drawB ∈ draws,
              drawIndicator omega drawA left *
                drawIndicator omega drawB right) := by
          exact finiteExpectation_congr support mass _ _
            (fun omega _homega =>
              multinomialCountFromDrawIndicators_mul_eq_double_sum
                draws drawIndicator omega left right)
    _ =
        ∑ drawA ∈ draws, ∑ drawB ∈ draws,
          finiteExpectation support mass
            (fun omega =>
              drawIndicator omega drawA left *
                drawIndicator omega drawB right) := by
          rw [finiteExpectation_sum]
          exact Finset.sum_congr rfl
            (fun drawA _hdrawA => by rw [finiteExpectation_sum])

/--
Draw-level moment sums imply the raw count moments required by
`BootstrapMultinomialCountBridge`.
-/
theorem multinomialCountFromDrawIndicators_raw_count_moments_of_draw_moment_sums
    [DecidableEq Unit]
    (support : Finset Omega) (mass : Omega -> Real)
    (sample : Finset Unit) (draws : Finset Draw)
    (drawIndicator : Omega -> Draw -> Unit -> Real)
    (sampleSize : Real)
    (hmean :
      ∀ unit ∈ sample,
        (∑ draw ∈ draws,
          finiteExpectation support mass
            (fun omega => drawIndicator omega draw unit)) = 1)
    (hcross :
      ∀ left ∈ sample, ∀ right ∈ sample,
        (∑ drawA ∈ draws, ∑ drawB ∈ draws,
          finiteExpectation support mass
            (fun omega =>
              drawIndicator omega drawA left *
                drawIndicator omega drawB right)) =
          if left = right then 2 - 1 / sampleSize else 1 - 1 / sampleSize) :
    (∀ unit ∈ sample,
        finiteExpectation support mass
          (fun omega =>
            multinomialCountFromDrawIndicators draws drawIndicator omega unit) =
          1) ∧
      (∀ left ∈ sample, ∀ right ∈ sample,
        finiteExpectation support mass
          (fun omega =>
            multinomialCountFromDrawIndicators draws drawIndicator omega left *
              multinomialCountFromDrawIndicators draws drawIndicator omega right) =
          if left = right then 2 - 1 / sampleSize else 1 - 1 / sampleSize) := by
  constructor
  · intro unit hunit
    rw [finiteExpectation_multinomialCountFromDrawIndicators_eq_sum_draw_expectations]
    exact hmean unit hunit
  · intro left hleft right hright
    rw [
      finiteExpectation_multinomialCountFromDrawIndicators_mul_eq_sum_draw_cross_expectations]
    exact hcross left hleft right hright

/--
Draw-level moment-sum version of the normalized multinomial bootstrap variance
target.
-/
theorem multiplierPerturbationSecondMoment_normalized_eq_bootstrapCenteredVarianceTarget_of_multinomial_draw_moment_sums_of_base_ratio
    [DecidableEq Unit]
    (support : Finset Omega) (mass : Omega -> Real)
    (sample : Finset Unit) (draws : Finset Draw)
    (drawIndicator : Omega -> Draw -> Unit -> Real)
    (contribution weight : Unit -> Real)
    (target denominator normalizer sampleSize : Real)
    (hmass :
      finiteExpectation support mass (fun _omega => (1 : Real)) = 1)
    (hmean :
      ∀ unit ∈ sample,
        (∑ draw ∈ draws,
          finiteExpectation support mass
            (fun omega => drawIndicator omega draw unit)) = 1)
    (hcross :
      ∀ left ∈ sample, ∀ right ∈ sample,
        (∑ drawA ∈ draws, ∑ drawB ∈ draws,
          finiteExpectation support mass
            (fun omega =>
              drawIndicator omega drawA left *
                drawIndicator omega drawB right)) =
          if left = right then 2 - 1 / sampleSize else 1 - 1 / sampleSize)
    (hbase :
      baseLinearizedSum sample contribution =
        target * baseLinearizedSum sample weight) :
    (1 / denominator ^ 2) * (1 / normalizer) *
        multiplierPerturbationSecondMoment support mass sample
          (fun omega unit =>
            multinomialCountFromDrawIndicators draws drawIndicator omega unit)
          (fun unit => contribution unit - target * weight unit) =
      bootstrapCenteredVarianceTarget sample contribution weight target
        denominator normalizer := by
  have hraw :=
    multinomialCountFromDrawIndicators_raw_count_moments_of_draw_moment_sums
      support mass sample draws drawIndicator sampleSize hmean hcross
  exact
    multiplierPerturbationSecondMoment_normalized_eq_bootstrapCenteredVarianceTarget_of_multinomial_count_moments_of_base_ratio
      support mass sample
      (fun omega unit =>
        multinomialCountFromDrawIndicators draws drawIndicator omega unit)
      contribution weight target denominator normalizer sampleSize
      hmass hraw.1 hraw.2 hbase

end WDSM
end Matching
end StatInference
