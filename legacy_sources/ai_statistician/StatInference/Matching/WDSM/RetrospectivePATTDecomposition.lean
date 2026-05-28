import StatInference.Matching.WDSM.AggregateDecomposition
import Mathlib.Tactic.Ring

/-!
# Retrospective PATT exact decomposition

This module formalizes the finite algebra behind the retrospective PATT WDSM
decomposition.  PATT is one-sided: treated outcomes are observed directly,
while control outcomes enter through the treated-weight reuse contribution.
The residual term therefore keeps separate treated-own and control-donor
residual functions.
-/

namespace StatInference
namespace Matching
namespace WDSM

open scoped BigOperators

variable {Unit : Type*}

/-- Retrospective PATT treated-focal contrast. -/
noncomputable def retrospectivePATTContrast
    (controlSet : Finset Unit) (controlCoefficient : Unit -> Unit -> Real)
    (mu0 mu1 treatedResidual controlResidual : Unit -> Real)
    (treated : Unit) : Real :=
  (mu1 treated + treatedResidual treated) -
    imputedOutcome controlSet controlCoefficient
      (fun control => mu0 control + controlResidual control) treated

/-- Hájek denominator for retrospective PATT with treated-side survey weights. -/
noncomputable def retrospectivePATTDenominator
    (treatedSet : Finset Unit) (treatedWeight : Unit -> Real) : Real :=
  weightedDenominator treatedSet treatedWeight

/-- Contrast numerator for the retrospective PATT imputation estimator. -/
noncomputable def retrospectivePATTContrastNumerator
    (treatedSet controlSet : Finset Unit)
    (controlCoefficient : Unit -> Unit -> Real)
    (treatedWeight mu0 mu1 treatedResidual controlResidual : Unit -> Real) :
    Real :=
  weightedSum treatedSet treatedWeight
    (retrospectivePATTContrast controlSet controlCoefficient mu0 mu1
      treatedResidual controlResidual)

/-- Heterogeneity numerator in the retrospective PATT decomposition. -/
noncomputable def retrospectivePATTHeterogeneityNumerator
    (treatedSet : Finset Unit)
    (treatedWeight mu0 mu1 : Unit -> Real) (tau : Real) : Real :=
  weightedSum treatedSet treatedWeight
    (fun treated => mu1 treated - mu0 treated - tau)

/-- Focal-side residual numerator before control-donor reuse reindexing. -/
noncomputable def retrospectivePATTFocalResidualNumerator
    (treatedSet controlSet : Finset Unit)
    (controlCoefficient : Unit -> Unit -> Real)
    (treatedWeight treatedResidual controlResidual : Unit -> Real) : Real :=
  weightedSum treatedSet treatedWeight treatedResidual -
    weightedSum treatedSet treatedWeight
      (fun treated =>
        imputedOutcome controlSet controlCoefficient controlResidual treated)

/-- Donor-side asymmetric residual numerator for retrospective PATT. -/
noncomputable def retrospectivePATTDonorResidualNumerator
    (treatedSet controlSet : Finset Unit)
    (controlCoefficient : Unit -> Unit -> Real)
    (treatedWeight treatedResidual controlResidual : Unit -> Real) : Real :=
  weightedSum treatedSet treatedWeight treatedResidual -
    weightedSum controlSet
      (fun control =>
        reuseContribution treatedSet controlCoefficient treatedWeight control)
      controlResidual

/-- Matching-discrepancy numerator for retrospective PATT. -/
noncomputable def retrospectivePATTDiscrepancyNumerator
    (treatedSet controlSet : Finset Unit)
    (controlCoefficient : Unit -> Unit -> Real)
    (treatedWeight mu0 : Unit -> Real) : Real :=
  weightedSum treatedSet treatedWeight
    (fun treated =>
      ∑ control ∈ controlSet,
        controlCoefficient treated control * (mu0 treated - mu0 control))

/--
Pointwise retrospective PATT imputation decomposition for one treated focal
unit.  The treated residual and control residual are deliberately separate.
-/
theorem retrospectivePATT_unit_decomposition
    (controlSet : Finset Unit) (controlCoefficient : Unit -> Unit -> Real)
    (mu0 mu1 treatedResidual controlResidual : Unit -> Real)
    (tau : Real) (treated : Unit)
    (hcontrolCoeffSum :
      (∑ control ∈ controlSet,
        controlCoefficient treated control) = 1) :
    retrospectivePATTContrast controlSet controlCoefficient mu0 mu1
        treatedResidual controlResidual treated - tau =
      (mu1 treated - mu0 treated - tau) +
        treatedResidual treated -
          imputedOutcome controlSet controlCoefficient controlResidual
            treated +
            ∑ control ∈ controlSet,
              controlCoefficient treated control *
                (mu0 treated - mu0 control) := by
  have hsplit :
      (∑ control ∈ controlSet,
          controlCoefficient treated control *
            (mu0 control + controlResidual control)) =
        (∑ control ∈ controlSet,
          controlCoefficient treated control * mu0 control) +
          (∑ control ∈ controlSet,
            controlCoefficient treated control *
              controlResidual control) := by
    calc
      (∑ control ∈ controlSet,
          controlCoefficient treated control *
            (mu0 control + controlResidual control))
          = (∑ control ∈ controlSet,
              (controlCoefficient treated control * mu0 control +
                controlCoefficient treated control *
                  controlResidual control)) := by
            exact Finset.sum_congr rfl
              (fun control _hcontrol => by ring)
      _ = (∑ control ∈ controlSet,
            controlCoefficient treated control * mu0 control) +
          (∑ control ∈ controlSet,
            controlCoefficient treated control *
              controlResidual control) := by
        rw [Finset.sum_add_distrib]
  have hdisc :
      (∑ control ∈ controlSet,
          controlCoefficient treated control *
            (mu0 treated - mu0 control)) =
        mu0 treated -
          (∑ control ∈ controlSet,
            controlCoefficient treated control * mu0 control) := by
    calc
      (∑ control ∈ controlSet,
          controlCoefficient treated control *
            (mu0 treated - mu0 control))
          = (∑ control ∈ controlSet,
              (controlCoefficient treated control * mu0 treated -
                controlCoefficient treated control * mu0 control)) := by
            exact Finset.sum_congr rfl
              (fun control _hcontrol => by ring)
      _ = (∑ control ∈ controlSet,
            controlCoefficient treated control * mu0 treated) -
          (∑ control ∈ controlSet,
            controlCoefficient treated control * mu0 control) := by
        rw [Finset.sum_sub_distrib]
      _ = (∑ control ∈ controlSet,
            controlCoefficient treated control) * mu0 treated -
          (∑ control ∈ controlSet,
            controlCoefficient treated control * mu0 control) := by
        rw [Finset.sum_mul]
      _ = mu0 treated -
          (∑ control ∈ controlSet,
            controlCoefficient treated control * mu0 control) := by
        rw [hcontrolCoeffSum]
        ring
  unfold retrospectivePATTContrast imputedOutcome
  rw [hsplit, hdisc]
  ring

/--
The focal-side residual numerator is exactly the asymmetric donor-side
treated-own/control-reuse residual numerator.
-/
theorem retrospectivePATT_focalResidual_eq_donorResidual
    (treatedSet controlSet : Finset Unit)
    (controlCoefficient : Unit -> Unit -> Real)
    (treatedWeight treatedResidual controlResidual : Unit -> Real) :
    retrospectivePATTFocalResidualNumerator treatedSet controlSet
        controlCoefficient treatedWeight treatedResidual controlResidual =
      retrospectivePATTDonorResidualNumerator treatedSet controlSet
        controlCoefficient treatedWeight treatedResidual controlResidual := by
  unfold retrospectivePATTFocalResidualNumerator
    retrospectivePATTDonorResidualNumerator weightedSum
  rw [focal_weighted_imputation_sum_eq_reuse_sum treatedSet controlSet
    controlCoefficient treatedWeight controlResidual]

/-- Numerator-level exact retrospective PATT decomposition. -/
theorem retrospectivePATT_contrastNumerator_sub_target_denominator_eq
    (treatedSet controlSet : Finset Unit)
    (controlCoefficient : Unit -> Unit -> Real)
    (treatedWeight mu0 mu1 treatedResidual controlResidual : Unit -> Real)
    (tau : Real)
    (hcontrolCoeffSum :
      ∀ treated, treated ∈ treatedSet ->
        (∑ control ∈ controlSet,
          controlCoefficient treated control) = 1) :
    retrospectivePATTContrastNumerator treatedSet controlSet
        controlCoefficient treatedWeight mu0 mu1 treatedResidual
        controlResidual -
        tau * retrospectivePATTDenominator treatedSet treatedWeight =
      retrospectivePATTHeterogeneityNumerator treatedSet treatedWeight mu0
        mu1 tau +
        retrospectivePATTFocalResidualNumerator treatedSet controlSet
          controlCoefficient treatedWeight treatedResidual controlResidual +
        retrospectivePATTDiscrepancyNumerator treatedSet controlSet
          controlCoefficient treatedWeight mu0 := by
  have htarget :
      retrospectivePATTContrastNumerator treatedSet controlSet
          controlCoefficient treatedWeight mu0 mu1 treatedResidual
          controlResidual -
          tau * retrospectivePATTDenominator treatedSet treatedWeight =
        weightedSum treatedSet treatedWeight
          (fun treated =>
            retrospectivePATTContrast controlSet controlCoefficient mu0 mu1
              treatedResidual controlResidual treated - tau) := by
    rw [weightedSum_sub_const treatedSet treatedWeight
      (retrospectivePATTContrast controlSet controlCoefficient mu0 mu1
        treatedResidual controlResidual) tau]
    unfold retrospectivePATTContrastNumerator retrospectivePATTDenominator
    ring
  have htreated :
      weightedSum treatedSet treatedWeight
          (fun treated =>
            retrospectivePATTContrast controlSet controlCoefficient mu0 mu1
              treatedResidual controlResidual treated - tau) =
        weightedSum treatedSet treatedWeight
          (fun treated => mu1 treated - mu0 treated - tau) +
          weightedSum treatedSet treatedWeight treatedResidual -
            weightedSum treatedSet treatedWeight
              (fun treated =>
                imputedOutcome controlSet controlCoefficient controlResidual
                  treated) +
              weightedSum treatedSet treatedWeight
                (fun treated =>
                  ∑ control ∈ controlSet,
                    controlCoefficient treated control *
                      (mu0 treated - mu0 control)) := by
    exact weightedSum_pointwise_decomposition treatedSet treatedWeight
      (fun treated =>
        retrospectivePATTContrast controlSet controlCoefficient mu0 mu1
          treatedResidual controlResidual treated)
      (fun treated => mu1 treated - mu0 treated - tau)
      treatedResidual
      (fun treated =>
        imputedOutcome controlSet controlCoefficient controlResidual treated)
      (fun treated =>
        ∑ control ∈ controlSet,
          controlCoefficient treated control * (mu0 treated - mu0 control))
      tau
      (fun treated htreated =>
        retrospectivePATT_unit_decomposition controlSet controlCoefficient
          mu0 mu1 treatedResidual controlResidual tau treated
          (hcontrolCoeffSum treated htreated))
  calc
    retrospectivePATTContrastNumerator treatedSet controlSet
        controlCoefficient treatedWeight mu0 mu1 treatedResidual
        controlResidual -
        tau * retrospectivePATTDenominator treatedSet treatedWeight =
        weightedSum treatedSet treatedWeight
          (fun treated =>
            retrospectivePATTContrast controlSet controlCoefficient mu0 mu1
              treatedResidual controlResidual treated - tau) := htarget
    _ =
      retrospectivePATTHeterogeneityNumerator treatedSet treatedWeight mu0
        mu1 tau +
        retrospectivePATTFocalResidualNumerator treatedSet controlSet
          controlCoefficient treatedWeight treatedResidual controlResidual +
        retrospectivePATTDiscrepancyNumerator treatedSet controlSet
          controlCoefficient treatedWeight mu0 := by
      rw [htreated]
      unfold retrospectivePATTHeterogeneityNumerator
        retrospectivePATTFocalResidualNumerator
        retrospectivePATTDiscrepancyNumerator
      ring

/--
Hájek-normalized exact retrospective PATT decomposition, with the residual term
written in asymmetric donor-side form.
-/
theorem retrospectivePATT_hajek_exact_decomposition
    (treatedSet controlSet : Finset Unit)
    (controlCoefficient : Unit -> Unit -> Real)
    (treatedWeight mu0 mu1 treatedResidual controlResidual : Unit -> Real)
    (tau : Real)
    (hden : retrospectivePATTDenominator treatedSet treatedWeight ≠ 0)
    (hcontrolCoeffSum :
      ∀ treated, treated ∈ treatedSet ->
        (∑ control ∈ controlSet,
          controlCoefficient treated control) = 1) :
    retrospectivePATTContrastNumerator treatedSet controlSet
        controlCoefficient treatedWeight mu0 mu1 treatedResidual
        controlResidual /
        retrospectivePATTDenominator treatedSet treatedWeight -
        tau =
      (retrospectivePATTHeterogeneityNumerator treatedSet treatedWeight mu0
          mu1 tau +
          retrospectivePATTDonorResidualNumerator treatedSet controlSet
            controlCoefficient treatedWeight treatedResidual controlResidual +
          retrospectivePATTDiscrepancyNumerator treatedSet controlSet
            controlCoefficient treatedWeight mu0) /
        retrospectivePATTDenominator treatedSet treatedWeight := by
  have hnum :=
    retrospectivePATT_contrastNumerator_sub_target_denominator_eq
      treatedSet controlSet controlCoefficient treatedWeight mu0 mu1
      treatedResidual controlResidual tau hcontrolCoeffSum
  have hres :=
    retrospectivePATT_focalResidual_eq_donorResidual treatedSet controlSet
      controlCoefficient treatedWeight treatedResidual controlResidual
  calc
    retrospectivePATTContrastNumerator treatedSet controlSet
        controlCoefficient treatedWeight mu0 mu1 treatedResidual
        controlResidual /
        retrospectivePATTDenominator treatedSet treatedWeight -
        tau =
      (retrospectivePATTContrastNumerator treatedSet controlSet
          controlCoefficient treatedWeight mu0 mu1 treatedResidual
          controlResidual -
          tau * retrospectivePATTDenominator treatedSet treatedWeight) /
        retrospectivePATTDenominator treatedSet treatedWeight := by
      field_simp [hden]
    _ =
      (retrospectivePATTHeterogeneityNumerator treatedSet treatedWeight mu0
          mu1 tau +
          retrospectivePATTFocalResidualNumerator treatedSet controlSet
            controlCoefficient treatedWeight treatedResidual controlResidual +
          retrospectivePATTDiscrepancyNumerator treatedSet controlSet
            controlCoefficient treatedWeight mu0) /
        retrospectivePATTDenominator treatedSet treatedWeight := by
      rw [hnum]
    _ =
      (retrospectivePATTHeterogeneityNumerator treatedSet treatedWeight mu0
          mu1 tau +
          retrospectivePATTDonorResidualNumerator treatedSet controlSet
            controlCoefficient treatedWeight treatedResidual controlResidual +
          retrospectivePATTDiscrepancyNumerator treatedSet controlSet
            controlCoefficient treatedWeight mu0) /
        retrospectivePATTDenominator treatedSet treatedWeight := by
      rw [hres]

end WDSM
end Matching
end StatInference
