import StatInference.Matching.WDSM.AggregateDecomposition

/-!
# Finite weighted bias bounds for WDSM

This module proves deterministic weighted-sum inequalities used by the WDSM
matching-discrepancy argument.  Once each unit-level discrepancy is bounded by
a local radius, the survey-weighted aggregate discrepancy is bounded by the
corresponding weighted average radius.
-/

namespace StatInference
namespace Matching
namespace WDSM

open scoped BigOperators

variable {Unit : Type*}

theorem abs_weightedSum_le_weightedSum_bound
    (sample : Finset Unit) (weight value bound : Unit -> Real)
    (hweight_nonneg : ∀ unit, unit ∈ sample -> 0 ≤ weight unit)
    (hbound : ∀ unit, unit ∈ sample -> |value unit| ≤ bound unit) :
    |weightedSum sample weight value| ≤ weightedSum sample weight bound := by
  unfold weightedSum
  calc
    |∑ unit ∈ sample, weight unit * value unit|
        ≤ ∑ unit ∈ sample, |weight unit * value unit| := by
          exact Finset.abs_sum_le_sum_abs _ _
    _ = ∑ unit ∈ sample, weight unit * |value unit| := by
        exact Finset.sum_congr rfl
          (fun unit hunit => by
            rw [abs_mul, abs_of_nonneg (hweight_nonneg unit hunit)])
    _ ≤ ∑ unit ∈ sample, weight unit * bound unit := by
        exact Finset.sum_le_sum
          (fun unit hunit =>
            mul_le_mul_of_nonneg_left (hbound unit hunit)
              (hweight_nonneg unit hunit))

theorem abs_weightedAverage_le_weightedAverage_bound
    (sample : Finset Unit) (weight value bound : Unit -> Real)
    (hden_pos : 0 < weightedDenominator sample weight)
    (hweight_nonneg : ∀ unit, unit ∈ sample -> 0 ≤ weight unit)
    (hbound : ∀ unit, unit ∈ sample -> |value unit| ≤ bound unit) :
    |weightedSum sample weight value / weightedDenominator sample weight| ≤
      weightedSum sample weight bound / weightedDenominator sample weight := by
  rw [abs_div, abs_of_nonneg hden_pos.le]
  exact div_le_div_of_nonneg_right
    (abs_weightedSum_le_weightedSum_bound sample weight value bound
      hweight_nonneg hbound)
    hden_pos.le

theorem abs_weightedAverage_le_uniform_bound
    (sample : Finset Unit) (weight value : Unit -> Real) (radius : Real)
    (hden_pos : 0 < weightedDenominator sample weight)
    (hweight_nonneg : ∀ unit, unit ∈ sample -> 0 ≤ weight unit)
    (hbound : ∀ unit, unit ∈ sample -> |value unit| ≤ radius) :
    |weightedSum sample weight value / weightedDenominator sample weight| ≤
      radius := by
  have havg := abs_weightedAverage_le_weightedAverage_bound sample weight value
    (fun _unit => radius) hden_pos hweight_nonneg hbound
  refine le_trans havg ?_
  unfold weightedSum weightedDenominator
  change (∑ unit ∈ sample, weight unit * radius) /
      (∑ unit ∈ sample, weight unit) ≤ radius
  rw [← Finset.sum_mul]
  have hsum_ne : (∑ unit ∈ sample, weight unit) ≠ 0 := by
    unfold weightedDenominator at hden_pos
    exact hden_pos.ne'
  apply le_of_eq
  rw [div_eq_mul_inv]
  calc
    (∑ unit ∈ sample, weight unit) * radius *
        (∑ unit ∈ sample, weight unit)⁻¹ =
        radius * ((∑ unit ∈ sample, weight unit) *
          (∑ unit ∈ sample, weight unit)⁻¹) := by
          ring
    _ = radius := by
        rw [mul_inv_cancel₀ hsum_ne]
        ring

end WDSM
end Matching
end StatInference
