import StatInference.Matching.WDSM.EstimatorAlgebra
import StatInference.Matching.WDSM.PATTAlgebra
import StatInference.Matching.WDSM.PATEAlgebra

/-!
# Prospective estimator specializations for WDSM

This module connects the common-weight algebra in
`ProspectiveSpecialization` to finite PATT and PATE estimator expressions.
It is still deterministic finite algebra; probability-limit and CLT layers
should import these checked identities rather than re-derive the normalizations.
-/

namespace StatInference
namespace Matching
namespace WDSM

open scoped BigOperators

variable {Unit : Type*}

/-- A constant finite sum is the common weight times the finite cardinality. -/
theorem finite_sum_const_weight_eq_card
    (sample : Finset Unit) (commonWeight : Real) :
    (∑ _unit ∈ sample, commonWeight) =
      commonWeight * (sample.card : Real) := by
  calc
    (∑ _unit ∈ sample, commonWeight) =
        ∑ _unit ∈ sample, commonWeight * (1 : Real) := by
          exact Finset.sum_congr rfl
            (fun _unit _hunit => by ring)
    _ = commonWeight * (∑ _unit ∈ sample, (1 : Real)) := by
          rw [← Finset.mul_sum]
    _ = commonWeight * (sample.card : Real) := by
          simp

/--
With a nonzero common survey weight, the raw Hájek-normalized one-sided PATT
contrast is the ordinary finite average of the treated unit-level imputation
contrasts.  The identity is algebraic; nonempty/cardinality conditions can be
added by later statistical statements when they need a nondegenerate average.
-/
theorem patt_common_weight_raw_contrast_ratio_eq_card_average
    (treatedSet controlSet : Finset Unit)
    (coefficient : Unit -> Unit -> Real)
    (treatedOutcome controlOutcome : Unit -> Real)
    (commonWeight : Real)
    (hweight : commonWeight ≠ 0) :
    ((∑ treated ∈ treatedSet,
        commonWeight *
          (treatedOutcome treated -
            imputedOutcome controlSet coefficient controlOutcome treated)) /
        (∑ _treated ∈ treatedSet, commonWeight)) =
      (∑ i ∈ treatedSet,
          (treatedOutcome i -
            imputedOutcome controlSet coefficient controlOutcome i)) /
        (treatedSet.card : Real) := by
  rw [← Finset.mul_sum]
  rw [finite_sum_const_weight_eq_card]
  rw [mul_div_mul_left _ _ hweight]

/--
Generic two-arm common-weight raw ratio.  This is the deterministic
normalization used when a prospective estimator is written as two separately
normalized arm sums.
-/
theorem two_arm_common_weight_raw_ratio_difference_eq_card_average_difference
    (leftSet rightSet : Finset Unit)
    (leftValue rightValue : Unit -> Real)
    (commonWeight : Real)
    (hweight : commonWeight ≠ 0) :
    ((∑ left ∈ leftSet, commonWeight * leftValue left) /
        (∑ _left ∈ leftSet, commonWeight)) -
        ((∑ right ∈ rightSet, commonWeight * rightValue right) /
          (∑ _right ∈ rightSet, commonWeight)) =
      (∑ left ∈ leftSet, leftValue left) / (leftSet.card : Real) -
        (∑ right ∈ rightSet, rightValue right) / (rightSet.card : Real) := by
  rw [← Finset.mul_sum, finite_sum_const_weight_eq_card leftSet commonWeight,
    mul_div_mul_left _ _ hweight]
  rw [← Finset.mul_sum, finite_sum_const_weight_eq_card rightSet commonWeight,
    mul_div_mul_left _ _ hweight]

/--
Common-weight two-arm PATE numerator normalization with a total arm-cardinality
denominator.  This is the finite algebra behind replacing a prospective
survey-weighted two-arm numerator by the corresponding unweighted numerator
when both arms share the same nonzero survey weight.
-/
theorem pate_common_weight_total_ratio_eq_card_ratio
    (treatedSet controlSet : Finset Unit)
    (treatedCoefficient controlCoefficient : Unit -> Unit -> Real)
    (treatedOutcome controlOutcome : Unit -> Real)
    (commonWeight : Real)
    (hweight : commonWeight ≠ 0)
    (htotal_card :
      (treatedSet.card : Real) + (controlSet.card : Real) ≠ 0) :
    (((∑ treated ∈ treatedSet, commonWeight * treatedOutcome treated) +
        (∑ control ∈ controlSet,
          commonWeight *
            imputedOutcome treatedSet treatedCoefficient treatedOutcome
              control) -
          ((∑ control ∈ controlSet, commonWeight * controlOutcome control) +
            (∑ treated ∈ treatedSet,
              commonWeight *
                imputedOutcome controlSet controlCoefficient controlOutcome
                  treated))) /
        ((∑ _treated ∈ treatedSet, commonWeight) +
          (∑ _control ∈ controlSet, commonWeight))) =
      (((∑ treated ∈ treatedSet, treatedOutcome treated) +
          (∑ control ∈ controlSet,
            imputedOutcome treatedSet treatedCoefficient treatedOutcome
              control) -
            ((∑ control ∈ controlSet, controlOutcome control) +
              (∑ treated ∈ treatedSet,
                imputedOutcome controlSet controlCoefficient controlOutcome
                  treated))) /
        ((treatedSet.card : Real) + (controlSet.card : Real))) := by
  rw [← Finset.mul_sum]
  rw [← Finset.mul_sum]
  rw [← Finset.mul_sum]
  rw [← Finset.mul_sum]
  rw [finite_sum_const_weight_eq_card treatedSet commonWeight]
  rw [finite_sum_const_weight_eq_card controlSet commonWeight]
  have hweighted_total :
      commonWeight * (treatedSet.card : Real) +
          commonWeight * (controlSet.card : Real) ≠ 0 := by
    rw [← mul_add]
    exact mul_ne_zero hweight htotal_card
  have hnum :
      commonWeight * (∑ treated ∈ treatedSet, treatedOutcome treated) +
          commonWeight *
            (∑ control ∈ controlSet,
              imputedOutcome treatedSet treatedCoefficient treatedOutcome
                control) -
            (commonWeight *
              (∑ control ∈ controlSet, controlOutcome control) +
              commonWeight *
                (∑ treated ∈ treatedSet,
                  imputedOutcome controlSet controlCoefficient controlOutcome
                    treated)) =
        commonWeight *
          (((∑ treated ∈ treatedSet, treatedOutcome treated) +
            (∑ control ∈ controlSet,
              imputedOutcome treatedSet treatedCoefficient treatedOutcome
                control) -
              ((∑ control ∈ controlSet, controlOutcome control) +
                (∑ treated ∈ treatedSet,
                  imputedOutcome controlSet controlCoefficient controlOutcome
                    treated)))) := by
    ring
  rw [hnum]
  rw [← mul_add]
  rw [mul_div_mul_left _ _ hweight]

end WDSM
end Matching
end StatInference
