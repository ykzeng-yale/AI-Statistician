import StatInference.Matching.WDSM.AggregateDecomposition

/-!
# Normalized Hajek weights for WDSM

This module proves finite algebra for normalized survey weights.  It is the
deterministic part of the repeated WDSM step that turns a weighted numerator
and denominator into a convex weighted average.
-/

namespace StatInference
namespace Matching
namespace WDSM

open scoped BigOperators

variable {Unit : Type*}

/-- Unit's survey weight divided by the sample survey-weight denominator. -/
noncomputable def normalizedSurveyWeight (sample : Finset Unit)
    (weight : Unit -> Real) (unit : Unit) : Real :=
  weight unit / weightedDenominator sample weight

theorem sum_normalizedSurveyWeight_eq_one
    (sample : Finset Unit) (weight : Unit -> Real)
    (hden : weightedDenominator sample weight ≠ 0) :
    (∑ unit ∈ sample, normalizedSurveyWeight sample weight unit) = 1 := by
  unfold normalizedSurveyWeight
  unfold weightedDenominator at hden ⊢
  rw [← Finset.sum_div]
  exact div_self hden

theorem normalizedSurveyWeight_nonneg
    (sample : Finset Unit) (weight : Unit -> Real)
    (hden_pos : 0 < weightedDenominator sample weight)
    (hweight_nonneg : ∀ unit, unit ∈ sample -> 0 ≤ weight unit)
    {unit : Unit} (hunit : unit ∈ sample) :
    0 ≤ normalizedSurveyWeight sample weight unit := by
  unfold normalizedSurveyWeight
  exact div_nonneg (hweight_nonneg unit hunit) hden_pos.le

theorem normalizedSurveyWeight_pos
    (sample : Finset Unit) (weight : Unit -> Real)
    (hden_pos : 0 < weightedDenominator sample weight)
    (hweight_pos : ∀ unit, unit ∈ sample -> 0 < weight unit)
    {unit : Unit} (hunit : unit ∈ sample) :
    0 < normalizedSurveyWeight sample weight unit := by
  unfold normalizedSurveyWeight
  exact div_pos (hweight_pos unit hunit) hden_pos

theorem normalizedSurveyWeight_eq_zero_of_weight_zero
    (sample : Finset Unit) (weight : Unit -> Real)
    {unit : Unit} (hweight : weight unit = 0) :
    normalizedSurveyWeight sample weight unit = 0 := by
  simp [normalizedSurveyWeight, hweight]

theorem sum_normalizedSurveyWeight_mul_const
    (sample : Finset Unit) (weight : Unit -> Real) (target : Real)
    (hden : weightedDenominator sample weight ≠ 0) :
    (∑ unit ∈ sample,
      normalizedSurveyWeight sample weight unit * target) = target := by
  calc
    (∑ unit ∈ sample,
      normalizedSurveyWeight sample weight unit * target)
        = (∑ unit ∈ sample, normalizedSurveyWeight sample weight unit) *
            target := by
          rw [Finset.sum_mul]
    _ = target := by
          rw [sum_normalizedSurveyWeight_eq_one sample weight hden]
          ring

theorem hajekMean_eq_sum_normalizedSurveyWeight_mul
    (sample : Finset Unit) (weight value : Unit -> Real) :
    hajekMean sample weight value =
      ∑ unit ∈ sample,
        normalizedSurveyWeight sample weight unit * value unit := by
  unfold hajekMean weightedSum normalizedSurveyWeight
  calc
    (∑ unit ∈ sample, weight unit * value unit) /
        weightedDenominator sample weight =
        ∑ unit ∈ sample,
          (weight unit * value unit) / weightedDenominator sample weight := by
          rw [Finset.sum_div]
    _ = ∑ unit ∈ sample,
          weight unit / weightedDenominator sample weight * value unit := by
        exact Finset.sum_congr rfl
          (fun unit _hunit => by ring)

theorem sum_normalizedSurveyWeight_mul_eq_hajekMean
    (sample : Finset Unit) (weight value : Unit -> Real) :
    (∑ unit ∈ sample,
      normalizedSurveyWeight sample weight unit * value unit) =
        hajekMean sample weight value := by
  symm
  exact hajekMean_eq_sum_normalizedSurveyWeight_mul sample weight value

end WDSM
end Matching
end StatInference
