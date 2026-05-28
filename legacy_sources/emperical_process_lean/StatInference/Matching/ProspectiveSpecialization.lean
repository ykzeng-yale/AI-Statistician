import StatInference.Matching.WDSM.ScoreRelations
import StatInference.Matching.WDSM.HajekWeights

/-!
# Prospective/common-weight specializations for WDSM

Prospective sampling is the common-inclusion-weight specialization of the
retrospective framework.  This module proves finite real-algebra reductions
used when treatment-specific weights collapse to a single common weight.
-/

namespace StatInference
namespace Matching
namespace WDSM

open scoped BigOperators

variable {Unit : Type*}

theorem populationPropensityFromSelected_common_weight_eq
    (commonWeight selected : Real) (hweight : commonWeight ≠ 0) :
    populationPropensityFromSelected commonWeight commonWeight selected =
      selected := by
  unfold populationPropensityFromSelected
  field_simp [hweight]
  ring

theorem weight_ratio_eq_one_of_common_weight
    (commonWeight : Real) (hweight : commonWeight ≠ 0) :
    commonWeight / commonWeight = 1 := by
  exact div_self hweight

/--
With a nonzero common survey weight, the Hajek mean equals the ratio formed by
the unweighted finite sum and the finite unit mass `sum 1`.
-/
theorem hajekMean_constant_weight_eq_unweighted_ratio
    (sample : Finset Unit) (value : Unit -> Real) (commonWeight : Real)
    (hweight : commonWeight ≠ 0)
    (hmass : (∑ _unit ∈ sample, (1 : Real)) ≠ 0) :
    hajekMean sample (fun _unit => commonWeight) value =
      (∑ unit ∈ sample, value unit) /
        (∑ _unit ∈ sample, (1 : Real)) := by
  unfold hajekMean weightedSum weightedDenominator
  have hnum :
      (∑ unit ∈ sample, commonWeight * value unit) =
        commonWeight * (∑ unit ∈ sample, value unit) := by
    rw [← Finset.mul_sum]
  have hden :
      (∑ unit ∈ sample, commonWeight) =
        commonWeight * (∑ _unit ∈ sample, (1 : Real)) := by
    calc
      (∑ unit ∈ sample, commonWeight) =
          (∑ unit ∈ sample, commonWeight * (1 : Real)) := by
            exact Finset.sum_congr rfl
              (fun _unit _hunit => by ring)
      _ = commonWeight * (∑ _unit ∈ sample, (1 : Real)) := by
            rw [← Finset.mul_sum]
  rw [hnum, hden]
  field_simp [hweight, hmass]

end WDSM
end Matching
end StatInference
