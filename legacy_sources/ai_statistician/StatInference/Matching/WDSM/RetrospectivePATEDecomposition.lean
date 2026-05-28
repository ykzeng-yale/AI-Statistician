import StatInference.Matching.WDSM.AggregateDecomposition
import Mathlib.Tactic.Ring

/-!
# Retrospective PATE exact decomposition

This module formalizes the finite algebra behind the retrospective PATE WDSM
decomposition in the appendix.  The matching discrepancy uses the corrected
recipient-minus-donor sign:

`mu_{1-Z_i}(X_i) - mu_{1-Z_i}(X_j)`.

The results are deterministic.  Probability limits, matching-radius rates, and
CLT assumptions are intentionally left to later modules.
-/

namespace StatInference
namespace Matching
namespace WDSM

open scoped BigOperators

variable {Unit : Type*}

/-- Retrospective PATE treated-focal contrast. -/
noncomputable def retrospectivePATETreatedContrast
    (controlSet : Finset Unit) (controlCoefficient : Unit -> Unit -> Real)
    (mu0 mu1 residual : Unit -> Real) (treated : Unit) : Real :=
  (mu1 treated + residual treated) -
    imputedOutcome controlSet controlCoefficient
      (fun control => mu0 control + residual control) treated

/-- Retrospective PATE control-focal contrast. -/
noncomputable def retrospectivePATEControlContrast
    (treatedSet : Finset Unit) (treatedCoefficient : Unit -> Unit -> Real)
    (mu0 mu1 residual : Unit -> Real) (control : Unit) : Real :=
  imputedOutcome treatedSet treatedCoefficient
      (fun treated => mu1 treated + residual treated) control -
    (mu0 control + residual control)

/-- Hájek denominator for retrospective PATE with arm-specific survey weights. -/
noncomputable def retrospectivePATEDenominator
    (treatedSet controlSet : Finset Unit)
    (treatedWeight controlWeight : Unit -> Real) : Real :=
  weightedDenominator treatedSet treatedWeight +
    weightedDenominator controlSet controlWeight

/-- Contrast numerator for the retrospective PATE imputation estimator. -/
noncomputable def retrospectivePATEContrastNumerator
    (treatedSet controlSet : Finset Unit)
    (treatedCoefficient controlCoefficient : Unit -> Unit -> Real)
    (treatedWeight controlWeight mu0 mu1 residual : Unit -> Real) : Real :=
  weightedSum treatedSet treatedWeight
      (retrospectivePATETreatedContrast controlSet controlCoefficient mu0 mu1
        residual) +
    weightedSum controlSet controlWeight
      (retrospectivePATEControlContrast treatedSet treatedCoefficient mu0 mu1
        residual)

/-- Heterogeneity numerator in the retrospective PATE decomposition. -/
noncomputable def retrospectivePATEHeterogeneityNumerator
    (treatedSet controlSet : Finset Unit)
    (treatedWeight controlWeight mu0 mu1 : Unit -> Real) (tau : Real) : Real :=
  weightedSum treatedSet treatedWeight
      (fun treated => mu1 treated - mu0 treated - tau) +
    weightedSum controlSet controlWeight
      (fun control => mu1 control - mu0 control - tau)

/-- Focal-side residual numerator before donor-side reuse reindexing. -/
noncomputable def retrospectivePATEFocalResidualNumerator
    (treatedSet controlSet : Finset Unit)
    (treatedCoefficient controlCoefficient : Unit -> Unit -> Real)
    (treatedWeight controlWeight residual : Unit -> Real) : Real :=
  weightedSum treatedSet treatedWeight residual -
    weightedSum treatedSet treatedWeight
      (fun treated =>
        imputedOutcome controlSet controlCoefficient residual treated) -
      weightedSum controlSet controlWeight residual +
        weightedSum controlSet controlWeight
          (fun control =>
            imputedOutcome treatedSet treatedCoefficient residual control)

/-- Donor-side own-plus-reuse residual numerator. -/
noncomputable def retrospectivePATEDonorResidualNumerator
    (treatedSet controlSet : Finset Unit)
    (treatedCoefficient controlCoefficient : Unit -> Unit -> Real)
    (treatedWeight controlWeight residual : Unit -> Real) : Real :=
  weightedSum treatedSet
      (fun treated =>
        treatedWeight treated +
          reuseContribution controlSet treatedCoefficient controlWeight
            treated)
      residual -
    weightedSum controlSet
      (fun control =>
        controlWeight control +
          reuseContribution treatedSet controlCoefficient treatedWeight
            control)
      residual

/--
Corrected matching-discrepancy numerator for retrospective PATE.

The treated-focal side imputes control outcomes and contributes
`mu0(treated) - mu0(control)`.  The control-focal side imputes treated
outcomes and contributes the sign-reversed term
`-(mu1(control) - mu1(treated))`.
-/
noncomputable def retrospectivePATEDiscrepancyNumerator
    (treatedSet controlSet : Finset Unit)
    (treatedCoefficient controlCoefficient : Unit -> Unit -> Real)
    (treatedWeight controlWeight mu0 mu1 : Unit -> Real) : Real :=
  weightedSum treatedSet treatedWeight
      (fun treated =>
        ∑ control ∈ controlSet,
          controlCoefficient treated control * (mu0 treated - mu0 control)) +
    weightedSum controlSet controlWeight
      (fun control =>
        -∑ treated ∈ treatedSet,
          treatedCoefficient control treated * (mu1 control - mu1 treated))

/--
The focal-side residual numerator is exactly the donor-side own-plus-reuse
residual numerator.
-/
theorem retrospectivePATE_focalResidual_eq_donorResidual
    (treatedSet controlSet : Finset Unit)
    (treatedCoefficient controlCoefficient : Unit -> Unit -> Real)
    (treatedWeight controlWeight residual : Unit -> Real) :
    retrospectivePATEFocalResidualNumerator treatedSet controlSet
        treatedCoefficient controlCoefficient treatedWeight controlWeight
        residual =
      retrospectivePATEDonorResidualNumerator treatedSet controlSet
        treatedCoefficient controlCoefficient treatedWeight controlWeight
        residual := by
  unfold retrospectivePATEFocalResidualNumerator
    retrospectivePATEDonorResidualNumerator weightedSum
  rw [focal_weighted_imputation_sum_eq_reuse_sum treatedSet controlSet
    controlCoefficient treatedWeight residual]
  rw [focal_weighted_imputation_sum_eq_reuse_sum controlSet treatedSet
    treatedCoefficient controlWeight residual]
  simp [add_mul, Finset.sum_add_distrib]
  ring

/--
Numerator-level exact retrospective PATE decomposition with the corrected
matching-discrepancy sign.
-/
theorem retrospectivePATE_contrastNumerator_sub_target_denominator_eq
    (treatedSet controlSet : Finset Unit)
    (treatedCoefficient controlCoefficient : Unit -> Unit -> Real)
    (treatedWeight controlWeight mu0 mu1 residual : Unit -> Real) (tau : Real)
    (htreatedCoeffSum :
      ∀ control, control ∈ controlSet ->
        (∑ treated ∈ treatedSet,
          treatedCoefficient control treated) = 1)
    (hcontrolCoeffSum :
      ∀ treated, treated ∈ treatedSet ->
        (∑ control ∈ controlSet,
          controlCoefficient treated control) = 1) :
    retrospectivePATEContrastNumerator treatedSet controlSet
        treatedCoefficient controlCoefficient treatedWeight controlWeight mu0
        mu1 residual -
        tau *
          retrospectivePATEDenominator treatedSet controlSet treatedWeight
            controlWeight =
      retrospectivePATEHeterogeneityNumerator treatedSet controlSet
        treatedWeight controlWeight mu0 mu1 tau +
        retrospectivePATEFocalResidualNumerator treatedSet controlSet
          treatedCoefficient controlCoefficient treatedWeight controlWeight
          residual +
        retrospectivePATEDiscrepancyNumerator treatedSet controlSet
          treatedCoefficient controlCoefficient treatedWeight controlWeight mu0
          mu1 := by
  have htarget :
      retrospectivePATEContrastNumerator treatedSet controlSet
          treatedCoefficient controlCoefficient treatedWeight controlWeight mu0
          mu1 residual -
          tau *
            retrospectivePATEDenominator treatedSet controlSet treatedWeight
              controlWeight =
        weightedSum treatedSet treatedWeight
          (fun treated =>
            retrospectivePATETreatedContrast controlSet controlCoefficient mu0
              mu1 residual treated - tau) +
          weightedSum controlSet controlWeight
            (fun control =>
              retrospectivePATEControlContrast treatedSet treatedCoefficient
                mu0 mu1 residual control - tau) := by
    rw [weightedSum_sub_const treatedSet treatedWeight
      (retrospectivePATETreatedContrast controlSet controlCoefficient mu0 mu1
        residual) tau]
    rw [weightedSum_sub_const controlSet controlWeight
      (retrospectivePATEControlContrast treatedSet treatedCoefficient mu0 mu1
        residual) tau]
    unfold retrospectivePATEContrastNumerator retrospectivePATEDenominator
    ring
  have htreated :
      weightedSum treatedSet treatedWeight
          (fun treated =>
            retrospectivePATETreatedContrast controlSet controlCoefficient mu0
              mu1 residual treated - tau) =
        weightedSum treatedSet treatedWeight
          (fun treated => mu1 treated - mu0 treated - tau) +
          weightedSum treatedSet treatedWeight residual -
            weightedSum treatedSet treatedWeight
              (fun treated =>
                imputedOutcome controlSet controlCoefficient residual
                  treated) +
              weightedSum treatedSet treatedWeight
                (fun treated =>
                  ∑ control ∈ controlSet,
                    controlCoefficient treated control *
                      (mu0 treated - mu0 control)) := by
    exact weightedSum_pointwise_decomposition treatedSet treatedWeight
      (fun treated =>
        retrospectivePATETreatedContrast controlSet controlCoefficient mu0 mu1
          residual treated)
      (fun treated => mu1 treated - mu0 treated - tau)
      residual
      (fun treated =>
        imputedOutcome controlSet controlCoefficient residual treated)
      (fun treated =>
        ∑ control ∈ controlSet,
          controlCoefficient treated control * (mu0 treated - mu0 control))
      tau
      (fun treated htreated =>
        by
          unfold retrospectivePATETreatedContrast
          exact treated_unit_imputation_decomposition controlSet
            controlCoefficient mu0 mu1 residual tau treated
            (hcontrolCoeffSum treated htreated))
  have hcontrol :
      weightedSum controlSet controlWeight
          (fun control =>
            retrospectivePATEControlContrast treatedSet treatedCoefficient
              mu0 mu1 residual control - tau) =
        weightedSum controlSet controlWeight
          (fun control => mu1 control - mu0 control - tau) +
          weightedSum controlSet controlWeight
            (fun control =>
              imputedOutcome treatedSet treatedCoefficient residual control) -
            weightedSum controlSet controlWeight residual +
              weightedSum controlSet controlWeight
                (fun control =>
                  -∑ treated ∈ treatedSet,
                    treatedCoefficient control treated *
                      (mu1 control - mu1 treated)) := by
    exact weightedSum_pointwise_decomposition controlSet controlWeight
      (fun control =>
        retrospectivePATEControlContrast treatedSet treatedCoefficient mu0 mu1
          residual control)
      (fun control => mu1 control - mu0 control - tau)
      (fun control =>
        imputedOutcome treatedSet treatedCoefficient residual control)
      residual
      (fun control =>
        -∑ treated ∈ treatedSet,
          treatedCoefficient control treated * (mu1 control - mu1 treated))
      tau
      (fun control hcontrol =>
        by
          unfold retrospectivePATEControlContrast
          have h :=
            control_unit_imputation_decomposition treatedSet
              treatedCoefficient mu0 mu1 residual tau control
              (htreatedCoeffSum control hcontrol)
          simpa [sub_eq_add_neg, add_assoc, add_left_comm, add_comm] using h)
  calc
    retrospectivePATEContrastNumerator treatedSet controlSet
        treatedCoefficient controlCoefficient treatedWeight controlWeight mu0
        mu1 residual -
        tau *
          retrospectivePATEDenominator treatedSet controlSet treatedWeight
            controlWeight =
        weightedSum treatedSet treatedWeight
          (fun treated =>
            retrospectivePATETreatedContrast controlSet controlCoefficient mu0
              mu1 residual treated - tau) +
          weightedSum controlSet controlWeight
            (fun control =>
              retrospectivePATEControlContrast treatedSet treatedCoefficient
                mu0 mu1 residual control - tau) := htarget
    _ =
      retrospectivePATEHeterogeneityNumerator treatedSet controlSet
        treatedWeight controlWeight mu0 mu1 tau +
        retrospectivePATEFocalResidualNumerator treatedSet controlSet
          treatedCoefficient controlCoefficient treatedWeight controlWeight
          residual +
        retrospectivePATEDiscrepancyNumerator treatedSet controlSet
          treatedCoefficient controlCoefficient treatedWeight controlWeight mu0
          mu1 := by
      rw [htreated, hcontrol]
      unfold retrospectivePATEHeterogeneityNumerator
        retrospectivePATEFocalResidualNumerator
        retrospectivePATEDiscrepancyNumerator
      ring

/--
Hájek-normalized exact retrospective PATE decomposition, with the residual term
written in donor-side own-plus-reuse form and the matching-discrepancy term
using the corrected recipient-minus-donor sign.
-/
theorem retrospectivePATE_hajek_exact_decomposition_corrected_sign
    (treatedSet controlSet : Finset Unit)
    (treatedCoefficient controlCoefficient : Unit -> Unit -> Real)
    (treatedWeight controlWeight mu0 mu1 residual : Unit -> Real) (tau : Real)
    (hden :
      retrospectivePATEDenominator treatedSet controlSet treatedWeight
        controlWeight ≠ 0)
    (htreatedCoeffSum :
      ∀ control, control ∈ controlSet ->
        (∑ treated ∈ treatedSet,
          treatedCoefficient control treated) = 1)
    (hcontrolCoeffSum :
      ∀ treated, treated ∈ treatedSet ->
        (∑ control ∈ controlSet,
          controlCoefficient treated control) = 1) :
    retrospectivePATEContrastNumerator treatedSet controlSet
        treatedCoefficient controlCoefficient treatedWeight controlWeight mu0
        mu1 residual /
        retrospectivePATEDenominator treatedSet controlSet treatedWeight
          controlWeight -
        tau =
      (retrospectivePATEHeterogeneityNumerator treatedSet controlSet
          treatedWeight controlWeight mu0 mu1 tau +
          retrospectivePATEDonorResidualNumerator treatedSet controlSet
            treatedCoefficient controlCoefficient treatedWeight controlWeight
            residual +
          retrospectivePATEDiscrepancyNumerator treatedSet controlSet
            treatedCoefficient controlCoefficient treatedWeight controlWeight
            mu0 mu1) /
        retrospectivePATEDenominator treatedSet controlSet treatedWeight
          controlWeight := by
  have hnum :=
    retrospectivePATE_contrastNumerator_sub_target_denominator_eq
      treatedSet controlSet treatedCoefficient controlCoefficient
      treatedWeight controlWeight mu0 mu1 residual tau htreatedCoeffSum
      hcontrolCoeffSum
  have hres :=
    retrospectivePATE_focalResidual_eq_donorResidual treatedSet controlSet
      treatedCoefficient controlCoefficient treatedWeight controlWeight
      residual
  calc
    retrospectivePATEContrastNumerator treatedSet controlSet
        treatedCoefficient controlCoefficient treatedWeight controlWeight mu0
        mu1 residual /
        retrospectivePATEDenominator treatedSet controlSet treatedWeight
          controlWeight -
        tau =
      (retrospectivePATEContrastNumerator treatedSet controlSet
          treatedCoefficient controlCoefficient treatedWeight controlWeight mu0
          mu1 residual -
          tau *
            retrospectivePATEDenominator treatedSet controlSet treatedWeight
              controlWeight) /
        retrospectivePATEDenominator treatedSet controlSet treatedWeight
          controlWeight := by
      field_simp [hden]
    _ =
      (retrospectivePATEHeterogeneityNumerator treatedSet controlSet
          treatedWeight controlWeight mu0 mu1 tau +
          retrospectivePATEFocalResidualNumerator treatedSet controlSet
            treatedCoefficient controlCoefficient treatedWeight controlWeight
            residual +
          retrospectivePATEDiscrepancyNumerator treatedSet controlSet
            treatedCoefficient controlCoefficient treatedWeight controlWeight
            mu0 mu1) /
        retrospectivePATEDenominator treatedSet controlSet treatedWeight
          controlWeight := by
      rw [hnum]
    _ =
      (retrospectivePATEHeterogeneityNumerator treatedSet controlSet
          treatedWeight controlWeight mu0 mu1 tau +
          retrospectivePATEDonorResidualNumerator treatedSet controlSet
            treatedCoefficient controlCoefficient treatedWeight controlWeight
            residual +
          retrospectivePATEDiscrepancyNumerator treatedSet controlSet
            treatedCoefficient controlCoefficient treatedWeight controlWeight
            mu0 mu1) /
        retrospectivePATEDenominator treatedSet controlSet treatedWeight
          controlWeight := by
      rw [hres]

end WDSM
end Matching
end StatInference
