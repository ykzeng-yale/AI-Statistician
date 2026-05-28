import StatInference.Matching.WDSM.BiasDecomposition

/-!
# Bias-correction algebra for WDSM

The WDSM bias-corrected imputation replaces matched outcomes by matched
residuals plus the focal unit's regression prediction.  This file proves the
finite cancellation that removes the matching-discrepancy term when the
regression function used in the correction is the target regression function.
-/

namespace StatInference
namespace Matching
namespace WDSM

open scoped BigOperators

variable {Unit : Type*}

/--
Bias-corrected imputed outcome for one focal unit: each donor contributes its
outcome residual relative to the donor regression value, plus the focal
regression value.
-/
noncomputable def biasCorrectedImputedOutcome (donorSet : Finset Unit)
    (coefficient : Unit -> Unit -> Real) (outcome donorMean focalMean : Unit -> Real)
    (focal : Unit) : Real :=
  ∑ donor ∈ donorSet,
    coefficient focal donor * (outcome donor - donorMean donor + focalMean focal)

/--
If the donor coefficients sum to one, bias-corrected imputation equals the
focal regression value plus the matched residual imputation.
-/
theorem biasCorrectedImputedOutcome_eq_focal_mean_plus_residual_imputation
    (donorSet : Finset Unit)
    (coefficient : Unit -> Unit -> Real)
    (outcome donorMean focalMean : Unit -> Real) (focal : Unit)
    (hsum : (∑ donor ∈ donorSet, coefficient focal donor) = 1) :
    biasCorrectedImputedOutcome donorSet coefficient outcome donorMean focalMean focal =
      focalMean focal +
        imputedOutcome donorSet coefficient
          (fun donor => outcome donor - donorMean donor) focal := by
  unfold biasCorrectedImputedOutcome imputedOutcome
  calc
    (∑ donor ∈ donorSet,
        coefficient focal donor *
          (outcome donor - donorMean donor + focalMean focal)) =
        ∑ donor ∈ donorSet,
          (coefficient focal donor * (outcome donor - donorMean donor) +
            coefficient focal donor * focalMean focal) := by
          exact Finset.sum_congr rfl
            (fun donor _hdonor => by ring)
    _ =
        (∑ donor ∈ donorSet,
          coefficient focal donor * (outcome donor - donorMean donor)) +
          (∑ donor ∈ donorSet,
            coefficient focal donor * focalMean focal) := by
          rw [Finset.sum_add_distrib]
    _ =
        (∑ donor ∈ donorSet,
          coefficient focal donor * (outcome donor - donorMean donor)) +
          (∑ donor ∈ donorSet, coefficient focal donor) * focalMean focal := by
          rw [Finset.sum_mul]
    _ =
        focalMean focal +
          ∑ donor ∈ donorSet,
            coefficient focal donor * (outcome donor - donorMean donor) := by
          rw [hsum]
          ring

/--
For a treated focal unit, exact bias correction removes the control-regression
matching-discrepancy term from the unit-level treatment-effect decomposition.
-/
theorem treated_unit_bias_corrected_decomposition
    (donorSet : Finset Unit)
    (coefficient : Unit -> Unit -> Real)
    (mu0 mu1 residual0 residual1 : Unit -> Real) (tau : Real) (focal : Unit)
    (hsum : (∑ donor ∈ donorSet, coefficient focal donor) = 1) :
    mu1 focal + residual1 focal -
        biasCorrectedImputedOutcome donorSet coefficient
          (fun donor => mu0 donor + residual0 donor) mu0 mu0 focal - tau =
      (mu1 focal - mu0 focal - tau) + residual1 focal -
        imputedOutcome donorSet coefficient residual0 focal := by
  have hbc :=
    biasCorrectedImputedOutcome_eq_focal_mean_plus_residual_imputation
      donorSet coefficient (fun donor => mu0 donor + residual0 donor) mu0 mu0
      focal hsum
  have himputed :
      imputedOutcome donorSet coefficient
          (fun donor => (mu0 donor + residual0 donor) - mu0 donor) focal =
        imputedOutcome donorSet coefficient residual0 focal := by
    unfold imputedOutcome
    exact Finset.sum_congr rfl
      (fun donor _hdonor => by ring)
  rw [hbc, himputed]
  ring

/--
For a control focal unit, exact bias correction removes the treated-regression
matching-discrepancy term from the unit-level treatment-effect decomposition.
-/
theorem control_unit_bias_corrected_decomposition
    (donorSet : Finset Unit)
    (coefficient : Unit -> Unit -> Real)
    (mu0 mu1 residual0 residual1 : Unit -> Real) (tau : Real) (focal : Unit)
    (hsum : (∑ donor ∈ donorSet, coefficient focal donor) = 1) :
    biasCorrectedImputedOutcome donorSet coefficient
        (fun donor => mu1 donor + residual1 donor) mu1 mu1 focal -
        (mu0 focal + residual0 focal) - tau =
      (mu1 focal - mu0 focal - tau) - residual0 focal +
        imputedOutcome donorSet coefficient residual1 focal := by
  have hbc :=
    biasCorrectedImputedOutcome_eq_focal_mean_plus_residual_imputation
      donorSet coefficient (fun donor => mu1 donor + residual1 donor) mu1 mu1
      focal hsum
  have himputed :
      imputedOutcome donorSet coefficient
          (fun donor => (mu1 donor + residual1 donor) - mu1 donor) focal =
        imputedOutcome donorSet coefficient residual1 focal := by
    unfold imputedOutcome
    exact Finset.sum_congr rfl
      (fun donor _hdonor => by ring)
  rw [hbc, himputed]
  ring

end WDSM
end Matching
end StatInference
