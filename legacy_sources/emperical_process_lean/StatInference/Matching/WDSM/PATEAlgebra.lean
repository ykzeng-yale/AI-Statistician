import StatInference.Matching.WDSM.EstimatorAlgebra

/-!
# Two-arm PATE estimator algebra for WDSM

The retrospective and prospective PATE estimators estimate both potential
outcome arms and subtract them.  This module packages the finite two-arm
matching-weight rewrite used in the WDSM manuscript and appendix.
-/

namespace StatInference
namespace Matching
namespace WDSM

open scoped BigOperators

variable {Unit : Type*}

/--
Two-arm PATE numerator rewrite.  The direct observed contribution plus the
opposite-arm imputation contribution in each arm equals the donor-side
own-plus-reuse matching-weight representation, and the PATE numerator is their
difference.
-/
theorem pate_two_arm_matching_weight_rewrite
    (treatedSet controlSet : Finset Unit)
    (treatedCoefficient controlCoefficient : Unit -> Unit -> Real)
    (treatedWeight controlWeight treatedOutcome controlOutcome : Unit -> Real) :
    ((∑ treated ∈ treatedSet,
        treatedWeight treated * treatedOutcome treated) +
      (∑ control ∈ controlSet,
        controlWeight control *
          imputedOutcome treatedSet treatedCoefficient treatedOutcome control)) -
      ((∑ control ∈ controlSet,
          controlWeight control * controlOutcome control) +
        (∑ treated ∈ treatedSet,
          treatedWeight treated *
            imputedOutcome controlSet controlCoefficient controlOutcome treated)) =
      (∑ treated ∈ treatedSet,
        (treatedWeight treated +
          reuseContribution controlSet treatedCoefficient controlWeight treated) *
          treatedOutcome treated) -
        (∑ control ∈ controlSet,
          (controlWeight control +
            reuseContribution treatedSet controlCoefficient treatedWeight control) *
            controlOutcome control) := by
  rw [direct_plus_imputed_sum_eq_matching_weight_sum
    controlSet treatedSet treatedCoefficient (fun unit => treatedWeight unit)
    controlWeight treatedOutcome]
  rw [direct_plus_imputed_sum_eq_matching_weight_sum
    treatedSet controlSet controlCoefficient (fun unit => controlWeight unit)
    treatedWeight controlOutcome]

/--
The same PATE rewrite after division by any finite denominator.  This is the
exact algebra behind the Hájek-normalized matching-weight representation.
-/
theorem pate_hajek_matching_weight_rewrite
    (treatedSet controlSet : Finset Unit)
    (treatedCoefficient controlCoefficient : Unit -> Unit -> Real)
    (treatedWeight controlWeight treatedOutcome controlOutcome : Unit -> Real)
    (denominator : Real) :
    (((∑ treated ∈ treatedSet,
        treatedWeight treated * treatedOutcome treated) +
      (∑ control ∈ controlSet,
        controlWeight control *
          imputedOutcome treatedSet treatedCoefficient treatedOutcome control)) -
      ((∑ control ∈ controlSet,
          controlWeight control * controlOutcome control) +
        (∑ treated ∈ treatedSet,
          treatedWeight treated *
            imputedOutcome controlSet controlCoefficient controlOutcome treated))) /
        denominator =
      ((∑ treated ∈ treatedSet,
        (treatedWeight treated +
          reuseContribution controlSet treatedCoefficient controlWeight treated) *
          treatedOutcome treated) -
        (∑ control ∈ controlSet,
          (controlWeight control +
            reuseContribution treatedSet controlCoefficient treatedWeight control) *
            controlOutcome control)) /
        denominator := by
  rw [pate_two_arm_matching_weight_rewrite]

end WDSM
end Matching
end StatInference
