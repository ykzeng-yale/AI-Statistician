import Mathlib.Data.Finset.Basic
import StatInference.Matching.WDSM.PATEAlgebra
import Mathlib.Tactic.Ring

/-!
# Retrospective survey-weighted reuse-transfer identities for WDSM

This module gives manuscript-facing finite algebra for the retrospective PATE
estimator.  It specializes the generic two-arm matching-weight rewrite to the
retrospective case where treated and control arms may carry different survey
weight functions.  No probability or asymptotics are used here.
-/

namespace StatInference
namespace Matching
namespace WDSM

open scoped BigOperators

variable {Unit : Type*}

/--
Arm-specific retrospective WDSM mean representation.

The direct observed donor contribution plus the opposite-arm imputation
contribution, divided by an arbitrary Hájek denominator, equals the donor-side
own-plus-reuse representation divided by the same denominator.
-/
theorem retrospective_pate_arm_ratio_eq_matching_weight_ratio
    (focalSet donorSet : Finset Unit)
    (coefficient : Unit -> Unit -> Real)
    (donorWeight focalWeight outcome : Unit -> Real)
    (denominator : Real) :
    ((∑ donor ∈ donorSet, donorWeight donor * outcome donor) +
        (∑ focal ∈ focalSet,
          focalWeight focal *
            imputedOutcome donorSet coefficient outcome focal)) /
        denominator =
      (∑ donor ∈ donorSet,
        (donorWeight donor +
          reuseContribution focalSet coefficient focalWeight donor) *
          outcome donor) /
        denominator := by
  rw [direct_plus_imputed_sum_eq_matching_weight_sum]

/--
The arm-specific retrospective WDSM mean has zero algebraic error relative to
its donor-side own-plus-reuse representation.
-/
theorem retrospective_pate_arm_matching_weight_error_eq_zero
    (focalSet donorSet : Finset Unit)
    (coefficient : Unit -> Unit -> Real)
    (donorWeight focalWeight outcome : Unit -> Real)
    (denominator : Real) :
    ((∑ donor ∈ donorSet, donorWeight donor * outcome donor) +
        (∑ focal ∈ focalSet,
          focalWeight focal *
            imputedOutcome donorSet coefficient outcome focal)) /
        denominator -
      (∑ donor ∈ donorSet,
        (donorWeight donor +
          reuseContribution focalSet coefficient focalWeight donor) *
          outcome donor) /
        denominator =
      0 := by
  rw [retrospective_pate_arm_ratio_eq_matching_weight_ratio]
  ring

/--
Exact retrospective PATE transfer to the donor-side own-plus-reuse
matching-weight representation with arm-specific survey weights.

This is the finite algebra behind the manuscript rewrite from the
Hájek-normalized imputation estimator to the matching-weight representation.
-/
theorem retrospective_pate_total_ratio_eq_matching_weight_ratio
    (treatedSet controlSet : Finset Unit)
    (treatedCoefficient controlCoefficient : Unit -> Unit -> Real)
    (treatedWeight controlWeight treatedOutcome controlOutcome : Unit -> Real) :
    (((∑ treated ∈ treatedSet, treatedWeight treated * treatedOutcome treated) +
        (∑ control ∈ controlSet,
          controlWeight control *
            imputedOutcome treatedSet treatedCoefficient treatedOutcome
              control) -
          ((∑ control ∈ controlSet,
              controlWeight control * controlOutcome control) +
            (∑ treated ∈ treatedSet,
              treatedWeight treated *
                imputedOutcome controlSet controlCoefficient controlOutcome
                  treated))) /
        ((∑ treated ∈ treatedSet, treatedWeight treated) +
          (∑ control ∈ controlSet, controlWeight control))) =
      ((∑ treated ∈ treatedSet,
        (treatedWeight treated +
          reuseContribution controlSet treatedCoefficient controlWeight
            treated) *
          treatedOutcome treated) -
        (∑ control ∈ controlSet,
          (controlWeight control +
            reuseContribution treatedSet controlCoefficient treatedWeight
              control) *
            controlOutcome control)) /
        ((∑ treated ∈ treatedSet, treatedWeight treated) +
          (∑ control ∈ controlSet, controlWeight control)) := by
  exact pate_hajek_matching_weight_rewrite
    treatedSet controlSet treatedCoefficient controlCoefficient treatedWeight
    controlWeight treatedOutcome controlOutcome
    ((∑ treated ∈ treatedSet, treatedWeight treated) +
      (∑ control ∈ controlSet, controlWeight control))

/--
The retrospective PATE imputation estimator has zero finite algebraic error
relative to its donor-side own-plus-reuse matching-weight representation.
-/
theorem retrospective_pate_total_ratio_matching_weight_error_eq_zero
    (treatedSet controlSet : Finset Unit)
    (treatedCoefficient controlCoefficient : Unit -> Unit -> Real)
    (treatedWeight controlWeight treatedOutcome controlOutcome : Unit -> Real) :
    (((∑ treated ∈ treatedSet, treatedWeight treated * treatedOutcome treated) +
        (∑ control ∈ controlSet,
          controlWeight control *
            imputedOutcome treatedSet treatedCoefficient treatedOutcome
              control) -
          ((∑ control ∈ controlSet,
              controlWeight control * controlOutcome control) +
            (∑ treated ∈ treatedSet,
              treatedWeight treated *
                imputedOutcome controlSet controlCoefficient controlOutcome
                  treated))) /
        ((∑ treated ∈ treatedSet, treatedWeight treated) +
          (∑ control ∈ controlSet, controlWeight control))) -
      ((∑ treated ∈ treatedSet,
        (treatedWeight treated +
          reuseContribution controlSet treatedCoefficient controlWeight
            treated) *
          treatedOutcome treated) -
        (∑ control ∈ controlSet,
          (controlWeight control +
            reuseContribution treatedSet controlCoefficient treatedWeight
              control) *
            controlOutcome control)) /
        ((∑ treated ∈ treatedSet, treatedWeight treated) +
          (∑ control ∈ controlSet, controlWeight control)) =
      0 := by
  rw [retrospective_pate_total_ratio_eq_matching_weight_ratio]
  ring

end WDSM
end Matching
end StatInference
