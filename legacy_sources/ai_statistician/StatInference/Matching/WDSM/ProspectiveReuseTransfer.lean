import StatInference.Matching.WDSM.ProspectiveEstimatorSpecialization
import Mathlib.Tactic.Ring

/-!
# Prospective common-weight reuse-transfer identities for WDSM

This module connects the prospective/common-weight estimator normalizations to
the donor-side reuse-frequency matching-weight rewrites.  The results are
finite deterministic equalities: the prospective raw normalized estimator has
zero algebraic gap relative to the matching-weight representation once the
survey weight is common within the selected sample.
-/

namespace StatInference
namespace Matching
namespace WDSM

open scoped BigOperators

variable {Unit : Type*}

/--
Common-weight PATT numerator distribution.  This rewrites the compact
sum-of-contrasts numerator into the difference of weighted observed and
imputed sums expected by the reuse-frequency theorem.
-/
theorem patt_common_weight_raw_contrast_numerator_eq_weighted_difference
    (treatedSet controlSet : Finset Unit)
    (coefficient : Unit -> Unit -> Real)
    (treatedOutcome controlOutcome : Unit -> Real)
    (commonWeight : Real) :
    (∑ treated ∈ treatedSet,
        commonWeight *
          (treatedOutcome treated -
            imputedOutcome controlSet coefficient controlOutcome treated)) =
      (∑ treated ∈ treatedSet,
        commonWeight * treatedOutcome treated) -
        (∑ treated ∈ treatedSet,
          commonWeight *
            imputedOutcome controlSet coefficient controlOutcome treated) := by
  calc
    (∑ treated ∈ treatedSet,
        commonWeight *
          (treatedOutcome treated -
            imputedOutcome controlSet coefficient controlOutcome treated)) =
        ∑ treated ∈ treatedSet,
          (commonWeight * treatedOutcome treated -
            commonWeight *
              imputedOutcome controlSet coefficient controlOutcome
                treated) := by
          exact Finset.sum_congr rfl
            (fun treated _ => by ring)
    _ = (∑ treated ∈ treatedSet,
          commonWeight * treatedOutcome treated) -
        (∑ treated ∈ treatedSet,
          commonWeight *
            imputedOutcome controlSet coefficient controlOutcome treated) := by
        rw [Finset.sum_sub_distrib]

/--
Exact prospective/common-weight PATT transfer to the donor-side reuse-frequency
matching-weight representation.
-/
theorem patt_common_weight_raw_contrast_ratio_eq_reuse_ratio
    (treatedSet controlSet : Finset Unit)
    (coefficient : Unit -> Unit -> Real)
    (treatedOutcome controlOutcome : Unit -> Real)
    (commonWeight : Real) :
    ((∑ treated ∈ treatedSet,
        commonWeight *
          (treatedOutcome treated -
            imputedOutcome controlSet coefficient controlOutcome treated)) /
        (∑ _treated ∈ treatedSet, commonWeight)) =
      ((∑ treated ∈ treatedSet,
        commonWeight * treatedOutcome treated) -
        (∑ control ∈ controlSet,
          reuseContribution treatedSet coefficient
            (fun _treated => commonWeight) control *
            controlOutcome control)) /
        (∑ _treated ∈ treatedSet, commonWeight) := by
  rw [patt_common_weight_raw_contrast_numerator_eq_weighted_difference]
  exact patt_treated_mass_hajek_matching_weight_rewrite
    treatedSet controlSet coefficient (fun _treated => commonWeight)
    treatedOutcome controlOutcome

/--
The prospective/common-weight PATT raw ratio has zero algebraic error relative
to the donor-side reuse-frequency representation.
-/
theorem patt_common_weight_raw_contrast_reuse_error_eq_zero
    (treatedSet controlSet : Finset Unit)
    (coefficient : Unit -> Unit -> Real)
    (treatedOutcome controlOutcome : Unit -> Real)
    (commonWeight : Real) :
    ((∑ treated ∈ treatedSet,
        commonWeight *
          (treatedOutcome treated -
            imputedOutcome controlSet coefficient controlOutcome treated)) /
        (∑ _treated ∈ treatedSet, commonWeight)) -
      ((∑ treated ∈ treatedSet,
        commonWeight * treatedOutcome treated) -
        (∑ control ∈ controlSet,
          reuseContribution treatedSet coefficient
            (fun _treated => commonWeight) control *
            controlOutcome control)) /
        (∑ _treated ∈ treatedSet, commonWeight) =
      0 := by
  rw [patt_common_weight_raw_contrast_ratio_eq_reuse_ratio]
  ring

/--
Exact prospective/common-weight PATE transfer to the donor-side own-plus-reuse
matching-weight representation.
-/
theorem pate_common_weight_total_ratio_eq_matching_weight_ratio
    (treatedSet controlSet : Finset Unit)
    (treatedCoefficient controlCoefficient : Unit -> Unit -> Real)
    (treatedOutcome controlOutcome : Unit -> Real)
    (commonWeight : Real) :
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
      ((∑ treated ∈ treatedSet,
        (commonWeight +
          reuseContribution controlSet treatedCoefficient
            (fun _control => commonWeight) treated) *
          treatedOutcome treated) -
        (∑ control ∈ controlSet,
          (commonWeight +
            reuseContribution treatedSet controlCoefficient
              (fun _treated => commonWeight) control) *
            controlOutcome control)) /
        ((∑ _treated ∈ treatedSet, commonWeight) +
          (∑ _control ∈ controlSet, commonWeight)) := by
  exact pate_hajek_matching_weight_rewrite
    treatedSet controlSet treatedCoefficient controlCoefficient
    (fun _treated => commonWeight) (fun _control => commonWeight)
    treatedOutcome controlOutcome
    ((∑ _treated ∈ treatedSet, commonWeight) +
      (∑ _control ∈ controlSet, commonWeight))

/--
The prospective/common-weight PATE total ratio has zero algebraic error
relative to the donor-side own-plus-reuse representation.
-/
theorem pate_common_weight_total_ratio_matching_weight_error_eq_zero
    (treatedSet controlSet : Finset Unit)
    (treatedCoefficient controlCoefficient : Unit -> Unit -> Real)
    (treatedOutcome controlOutcome : Unit -> Real)
    (commonWeight : Real) :
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
          (∑ _control ∈ controlSet, commonWeight))) -
      ((∑ treated ∈ treatedSet,
        (commonWeight +
          reuseContribution controlSet treatedCoefficient
            (fun _control => commonWeight) treated) *
          treatedOutcome treated) -
        (∑ control ∈ controlSet,
          (commonWeight +
            reuseContribution treatedSet controlCoefficient
              (fun _treated => commonWeight) control) *
            controlOutcome control)) /
        ((∑ _treated ∈ treatedSet, commonWeight) +
          (∑ _control ∈ controlSet, commonWeight)) =
      0 := by
  rw [pate_common_weight_total_ratio_eq_matching_weight_ratio]
  ring

end WDSM
end Matching
end StatInference
