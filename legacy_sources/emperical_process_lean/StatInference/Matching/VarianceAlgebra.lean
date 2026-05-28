import Mathlib

/-!
# Variance algebra for WDSM asymptotic statements

The probability layer must still prove the CLTs and covariance limits.  This
module verifies the scalar algebra used after those limits are available:
orthogonal heterogeneity/residual variances add, and estimated-score variance
adjustments reduce to the oracle variance in the advertised special cases.
-/

namespace StatInference
namespace Matching
namespace WDSM

/-- Variance of a sum expressed by two marginal variances and their covariance. -/
def sumVariance (varianceA varianceB covarianceAB : Real) : Real :=
  varianceA + varianceB + 2 * covarianceAB

/-- If the two limit components are uncorrelated, their variances add. -/
theorem sumVariance_eq_add_of_zero_covariance
    (varianceA varianceB covarianceAB : Real) (hcov : covarianceAB = 0) :
    sumVariance varianceA varianceB covarianceAB = varianceA + varianceB := by
  unfold sumVariance
  rw [hcov]
  ring

/-- Oracle WDSM variance after heterogeneity and residual limits are combined. -/
def oracleVariance (heterogeneityVariance residualVariance : Real) : Real :=
  heterogeneityVariance + residualVariance

/-- The oracle variance is the zero-covariance sum variance. -/
theorem oracleVariance_eq_sumVariance_zero_covariance
    (heterogeneityVariance residualVariance : Real) :
    oracleVariance heterogeneityVariance residualVariance =
      sumVariance heterogeneityVariance residualVariance 0 := by
  unfold oracleVariance sumVariance
  ring

/-- The oracle variance is nonnegative when both component variances are nonnegative. -/
theorem oracleVariance_nonneg
    (heterogeneityVariance residualVariance : Real)
    (hheterogeneity : 0 ≤ heterogeneityVariance)
    (hresidual : 0 ≤ residualVariance) :
    0 ≤ oracleVariance heterogeneityVariance residualVariance := by
  unfold oracleVariance
  exact add_nonneg hheterogeneity hresidual

/-- If the residual variance component is zero, the oracle variance is the heterogeneity variance. -/
theorem oracleVariance_eq_heterogeneity_of_residual_zero
    (heterogeneityVariance residualVariance : Real)
    (hresidual : residualVariance = 0) :
    oracleVariance heterogeneityVariance residualVariance =
      heterogeneityVariance := by
  unfold oracleVariance
  rw [hresidual]
  ring

/-- If the heterogeneity variance component is zero, the oracle variance is the residual variance. -/
theorem oracleVariance_eq_residual_of_heterogeneity_zero
    (heterogeneityVariance residualVariance : Real)
    (hheterogeneity : heterogeneityVariance = 0) :
    oracleVariance heterogeneityVariance residualVariance =
      residualVariance := by
  unfold oracleVariance
  rw [hheterogeneity]
  ring

/-- If both variance components are zero, the oracle variance is zero. -/
theorem oracleVariance_eq_zero_of_components_zero
    (heterogeneityVariance residualVariance : Real)
    (hheterogeneity : heterogeneityVariance = 0)
    (hresidual : residualVariance = 0) :
    oracleVariance heterogeneityVariance residualVariance = 0 := by
  unfold oracleVariance
  rw [hheterogeneity, hresidual]
  ring

/--
With nonnegative components, the oracle variance is zero exactly when both
heterogeneity and residual components are zero.
-/
theorem oracleVariance_eq_zero_iff_components_zero_of_nonneg
    (heterogeneityVariance residualVariance : Real)
    (hheterogeneity_nonneg : 0 ≤ heterogeneityVariance)
    (hresidual_nonneg : 0 ≤ residualVariance) :
    oracleVariance heterogeneityVariance residualVariance = 0 ↔
      heterogeneityVariance = 0 ∧ residualVariance = 0 := by
  constructor
  · intro hzero
    unfold oracleVariance at hzero
    constructor <;> linarith
  · intro hcomponents
    exact oracleVariance_eq_zero_of_components_zero
      heterogeneityVariance residualVariance hcomponents.1 hcomponents.2

/-- A positive heterogeneity component makes the oracle variance positive. -/
theorem oracleVariance_pos_of_heterogeneity_pos_of_residual_nonneg
    (heterogeneityVariance residualVariance : Real)
    (hheterogeneity_pos : 0 < heterogeneityVariance)
    (hresidual_nonneg : 0 ≤ residualVariance) :
    0 < oracleVariance heterogeneityVariance residualVariance := by
  unfold oracleVariance
  linarith

/-- A positive residual component makes the oracle variance positive. -/
theorem oracleVariance_pos_of_residual_pos_of_heterogeneity_nonneg
    (heterogeneityVariance residualVariance : Real)
    (hheterogeneity_nonneg : 0 ≤ heterogeneityVariance)
    (hresidual_pos : 0 < residualVariance) :
    0 < oracleVariance heterogeneityVariance residualVariance := by
  unfold oracleVariance
  linarith

/--
With nonnegative components, oracle variance positivity is equivalent to at
least one positive component.
-/
theorem oracleVariance_pos_iff_component_pos_of_nonneg
    (heterogeneityVariance residualVariance : Real)
    (hheterogeneity_nonneg : 0 ≤ heterogeneityVariance)
    (hresidual_nonneg : 0 ≤ residualVariance) :
    0 < oracleVariance heterogeneityVariance residualVariance ↔
      0 < heterogeneityVariance ∨ 0 < residualVariance := by
  constructor
  · intro horacle_pos
    by_cases hheterogeneity_zero : heterogeneityVariance = 0
    · right
      unfold oracleVariance at horacle_pos
      rw [hheterogeneity_zero, zero_add] at horacle_pos
      exact horacle_pos
    · left
      exact lt_of_le_of_ne' hheterogeneity_nonneg hheterogeneity_zero
  · intro hcomponent_pos
    rcases hcomponent_pos with hheterogeneity_pos | hresidual_pos
    · exact oracleVariance_pos_of_heterogeneity_pos_of_residual_nonneg
        heterogeneityVariance residualVariance hheterogeneity_pos
        hresidual_nonneg
    · exact oracleVariance_pos_of_residual_pos_of_heterogeneity_nonneg
        heterogeneityVariance residualVariance hheterogeneity_nonneg
        hresidual_pos

/--
Scalar form of the estimated-score adjustment:
oracle variance minus the projection/score-correlation term plus the
moving-target derivative term.
-/
def estimatedScoreVariance
    (oracleVariance projectionReduction targetDriftInflation : Real) : Real :=
  oracleVariance - projectionReduction + targetDriftInflation

/-- With no first-step projection and no moving-target drift, the variance is oracle. -/
theorem estimatedScoreVariance_eq_oracle_of_zero_adjustments
    (oracleVariance : Real) :
    estimatedScoreVariance oracleVariance 0 0 = oracleVariance := by
  unfold estimatedScoreVariance
  ring

/-- Under fixed-law targets, the moving-target drift term is zero. -/
theorem fixedLawEstimatedScoreVariance_eq
    (oracleVariance projectionReduction : Real) :
    estimatedScoreVariance oracleVariance projectionReduction 0 =
      oracleVariance - projectionReduction := by
  unfold estimatedScoreVariance
  ring

/-- A nonnegative projection-reduction term cannot increase the fixed-law variance. -/
theorem fixedLawEstimatedScoreVariance_le_oracle
    (oracleVariance projectionReduction : Real)
    (hprojection_nonneg : 0 ≤ projectionReduction) :
    estimatedScoreVariance oracleVariance projectionReduction 0 ≤
      oracleVariance := by
  rw [fixedLawEstimatedScoreVariance_eq]
  linarith

/--
The fixed-law estimated-score variance remains nonnegative once the
projection-reduction term is no larger than the oracle variance.
-/
theorem fixedLawEstimatedScoreVariance_nonneg_of_projection_le_oracle
    (oracleVariance projectionReduction : Real)
    (hprojection_le_oracle : projectionReduction ≤ oracleVariance) :
    0 ≤ estimatedScoreVariance oracleVariance projectionReduction 0 := by
  rw [fixedLawEstimatedScoreVariance_eq]
  linarith

/--
The fixed-law estimated-score variance is strictly positive once the
projection reduction is strictly smaller than the oracle variance.
-/
theorem fixedLawEstimatedScoreVariance_pos_of_projection_lt_oracle
    (oracleVariance projectionReduction : Real)
    (hprojection_lt_oracle : projectionReduction < oracleVariance) :
    0 < estimatedScoreVariance oracleVariance projectionReduction 0 := by
  rw [fixedLawEstimatedScoreVariance_eq]
  linarith

/-- The changing-target adjustment splits into the fixed-law variance plus drift inflation. -/
theorem changingTargetVariance_eq_fixedLaw_plus_drift
    (oracleVariance projectionReduction targetDriftInflation : Real) :
    estimatedScoreVariance oracleVariance projectionReduction targetDriftInflation =
      estimatedScoreVariance oracleVariance projectionReduction 0 +
        targetDriftInflation := by
  unfold estimatedScoreVariance
  ring

/--
A nonnegative changing-target drift term preserves nonnegativity once the
fixed-law adjusted variance is nonnegative.
-/
theorem changingTargetVariance_nonneg_of_fixed_nonneg_of_drift_nonneg
    (oracleVariance projectionReduction targetDriftInflation : Real)
    (hfixed : 0 ≤ estimatedScoreVariance oracleVariance projectionReduction 0)
    (hdrift : 0 ≤ targetDriftInflation) :
    0 ≤ estimatedScoreVariance oracleVariance projectionReduction
      targetDriftInflation := by
  rw [changingTargetVariance_eq_fixedLaw_plus_drift]
  exact add_nonneg hfixed hdrift

/--
A positive fixed-law adjusted variance remains positive after adding
nonnegative moving-target drift.
-/
theorem changingTargetVariance_pos_of_fixed_pos_of_drift_nonneg
    (oracleVariance projectionReduction targetDriftInflation : Real)
    (hfixed : 0 < estimatedScoreVariance oracleVariance projectionReduction 0)
    (hdrift : 0 ≤ targetDriftInflation) :
    0 < estimatedScoreVariance oracleVariance projectionReduction
      targetDriftInflation := by
  rw [changingTargetVariance_eq_fixedLaw_plus_drift]
  exact add_pos_of_pos_of_nonneg hfixed hdrift

/--
A positive moving-target drift term makes the changing-target adjusted variance
positive once the fixed-law adjusted variance is nonnegative.
-/
theorem changingTargetVariance_pos_of_fixed_nonneg_of_drift_pos
    (oracleVariance projectionReduction targetDriftInflation : Real)
    (hfixed : 0 ≤ estimatedScoreVariance oracleVariance projectionReduction 0)
    (hdrift : 0 < targetDriftInflation) :
    0 < estimatedScoreVariance oracleVariance projectionReduction
      targetDriftInflation := by
  rw [changingTargetVariance_eq_fixedLaw_plus_drift]
  exact add_pos_of_nonneg_of_pos hfixed hdrift

/--
Combining the projection bound and nonnegative drift gives nonnegativity of
the changing-target estimated-score variance.
-/
theorem changingTargetVariance_nonneg_of_projection_le_oracle_of_drift_nonneg
    (oracleVariance projectionReduction targetDriftInflation : Real)
    (hprojection_le_oracle : projectionReduction ≤ oracleVariance)
    (hdrift : 0 ≤ targetDriftInflation) :
    0 ≤ estimatedScoreVariance oracleVariance projectionReduction
      targetDriftInflation := by
  exact changingTargetVariance_nonneg_of_fixed_nonneg_of_drift_nonneg
    oracleVariance projectionReduction targetDriftInflation
    (fixedLawEstimatedScoreVariance_nonneg_of_projection_le_oracle
      oracleVariance projectionReduction hprojection_le_oracle)
    hdrift

/--
If the projection reduction is strictly below the oracle variance, then
nonnegative moving-target drift preserves strict positivity.
-/
theorem changingTargetVariance_pos_of_projection_lt_oracle_of_drift_nonneg
    (oracleVariance projectionReduction targetDriftInflation : Real)
    (hprojection_lt_oracle : projectionReduction < oracleVariance)
    (hdrift : 0 ≤ targetDriftInflation) :
    0 < estimatedScoreVariance oracleVariance projectionReduction
      targetDriftInflation := by
  exact changingTargetVariance_pos_of_fixed_pos_of_drift_nonneg
    oracleVariance projectionReduction targetDriftInflation
    (fixedLawEstimatedScoreVariance_pos_of_projection_lt_oracle
      oracleVariance projectionReduction hprojection_lt_oracle)
    hdrift

/--
If the projection reduction is no larger than the oracle variance, then
positive moving-target drift gives strict positivity.
-/
theorem changingTargetVariance_pos_of_projection_le_oracle_of_drift_pos
    (oracleVariance projectionReduction targetDriftInflation : Real)
    (hprojection_le_oracle : projectionReduction ≤ oracleVariance)
    (hdrift : 0 < targetDriftInflation) :
    0 < estimatedScoreVariance oracleVariance projectionReduction
      targetDriftInflation := by
  exact changingTargetVariance_pos_of_fixed_nonneg_of_drift_pos
    oracleVariance projectionReduction targetDriftInflation
    (fixedLawEstimatedScoreVariance_nonneg_of_projection_le_oracle
      oracleVariance projectionReduction hprojection_le_oracle)
    hdrift

/--
For changing-law targets, the adjusted variance is no larger than the oracle
variance when the moving-target drift is no larger than the projection
reduction.
-/
theorem changingTargetVariance_le_oracle_of_drift_le_projection
    (oracleVariance projectionReduction targetDriftInflation : Real)
    (hdrift_le_projection : targetDriftInflation ≤ projectionReduction) :
    estimatedScoreVariance oracleVariance projectionReduction
      targetDriftInflation ≤ oracleVariance := by
  unfold estimatedScoreVariance
  linarith

/--
For changing-law targets, the adjusted variance is at least the oracle variance
when the projection reduction is no larger than the moving-target drift.
-/
theorem oracle_le_changingTargetVariance_of_projection_le_drift
    (oracleVariance projectionReduction targetDriftInflation : Real)
    (hprojection_le_drift : projectionReduction ≤ targetDriftInflation) :
    oracleVariance ≤ estimatedScoreVariance oracleVariance projectionReduction
      targetDriftInflation := by
  unfold estimatedScoreVariance
  linarith

/--
When the moving-target drift exactly equals the projection reduction, the
changing-law adjusted variance equals the oracle variance.
-/
theorem changingTargetVariance_eq_oracle_of_projection_eq_drift
    (oracleVariance projectionReduction targetDriftInflation : Real)
    (hprojection_eq_drift : projectionReduction = targetDriftInflation) :
    estimatedScoreVariance oracleVariance projectionReduction
      targetDriftInflation = oracleVariance := by
  unfold estimatedScoreVariance
  rw [hprojection_eq_drift]
  ring

/--
Scalar skeleton of the two-arm residual variance formulas:
`m^{-2} (q_1 V_1 + q_0 V_0)`.
-/
noncomputable def twoArmWeightedResidualVariance
    (denominator treatedShare controlShare treatedArmVariance controlArmVariance : Real) :
    Real :=
  (treatedShare * treatedArmVariance + controlShare * controlArmVariance) /
    denominator ^ 2

/-- Equivalent inverse-square form of the two-arm weighted residual variance. -/
theorem twoArmWeightedResidualVariance_eq_inv_sq_mul
    (denominator treatedShare controlShare treatedArmVariance controlArmVariance :
      Real) :
    twoArmWeightedResidualVariance denominator treatedShare controlShare
        treatedArmVariance controlArmVariance =
      (1 / denominator ^ 2) *
        (treatedShare * treatedArmVariance +
          controlShare * controlArmVariance) := by
  unfold twoArmWeightedResidualVariance
  ring

/-- Nonnegativity of the scalar two-arm residual variance target. -/
theorem twoArmWeightedResidualVariance_nonneg
    (denominator treatedShare controlShare treatedArmVariance controlArmVariance :
      Real)
    (htreatedShare : 0 ≤ treatedShare)
    (hcontrolShare : 0 ≤ controlShare)
    (htreatedVariance : 0 ≤ treatedArmVariance)
    (hcontrolVariance : 0 ≤ controlArmVariance) :
    0 ≤ twoArmWeightedResidualVariance denominator treatedShare controlShare
      treatedArmVariance controlArmVariance := by
  unfold twoArmWeightedResidualVariance
  exact div_nonneg
    (add_nonneg
      (mul_nonneg htreatedShare htreatedVariance)
      (mul_nonneg hcontrolShare hcontrolVariance))
    (sq_nonneg denominator)

/--
A positive treated-arm weighted variance contribution makes the scalar two-arm
residual variance target positive.
-/
theorem twoArmWeightedResidualVariance_pos_of_treated_pos
    (denominator treatedShare controlShare treatedArmVariance controlArmVariance :
      Real)
    (hdenominator : denominator ≠ 0)
    (htreatedShare : 0 < treatedShare)
    (hcontrolShare : 0 ≤ controlShare)
    (htreatedVariance : 0 < treatedArmVariance)
    (hcontrolVariance : 0 ≤ controlArmVariance) :
    0 < twoArmWeightedResidualVariance denominator treatedShare controlShare
      treatedArmVariance controlArmVariance := by
  unfold twoArmWeightedResidualVariance
  exact div_pos
    (add_pos_of_pos_of_nonneg
      (mul_pos htreatedShare htreatedVariance)
      (mul_nonneg hcontrolShare hcontrolVariance))
    (sq_pos_of_ne_zero hdenominator)

/--
A positive control-arm weighted variance contribution makes the scalar two-arm
residual variance target positive.
-/
theorem twoArmWeightedResidualVariance_pos_of_control_pos
    (denominator treatedShare controlShare treatedArmVariance controlArmVariance :
      Real)
    (hdenominator : denominator ≠ 0)
    (htreatedShare : 0 ≤ treatedShare)
    (hcontrolShare : 0 < controlShare)
    (htreatedVariance : 0 ≤ treatedArmVariance)
    (hcontrolVariance : 0 < controlArmVariance) :
    0 < twoArmWeightedResidualVariance denominator treatedShare controlShare
      treatedArmVariance controlArmVariance := by
  unfold twoArmWeightedResidualVariance
  exact div_pos
    (add_pos_of_nonneg_of_pos
      (mul_nonneg htreatedShare htreatedVariance)
      (mul_pos hcontrolShare hcontrolVariance))
    (sq_pos_of_ne_zero hdenominator)

/--
If both arm-level residual variance limits are zero, the two-arm residual
variance target is zero.
-/
theorem twoArmWeightedResidualVariance_eq_zero_of_arm_variances_zero
    (denominator treatedShare controlShare treatedArmVariance controlArmVariance :
      Real)
    (htreatedVariance : treatedArmVariance = 0)
    (hcontrolVariance : controlArmVariance = 0) :
    twoArmWeightedResidualVariance denominator treatedShare controlShare
      treatedArmVariance controlArmVariance = 0 := by
  unfold twoArmWeightedResidualVariance
  rw [htreatedVariance, hcontrolVariance]
  ring

/--
With positive arm shares, nonnegative arm variances, and nonzero denominator,
the scalar two-arm residual variance target is zero exactly when both arm
variance components are zero.
-/
theorem twoArmWeightedResidualVariance_eq_zero_iff_arm_variances_zero_of_shares_pos
    (denominator treatedShare controlShare treatedArmVariance controlArmVariance :
      Real)
    (hdenominator : denominator ≠ 0)
    (htreatedShare : 0 < treatedShare)
    (hcontrolShare : 0 < controlShare)
    (htreatedVariance : 0 ≤ treatedArmVariance)
    (hcontrolVariance : 0 ≤ controlArmVariance) :
    twoArmWeightedResidualVariance denominator treatedShare controlShare
        treatedArmVariance controlArmVariance = 0 ↔
      treatedArmVariance = 0 ∧ controlArmVariance = 0 := by
  constructor
  · intro hzero
    unfold twoArmWeightedResidualVariance at hzero
    have hnumerator :
        treatedShare * treatedArmVariance +
          controlShare * controlArmVariance = 0 := by
      rcases div_eq_zero_iff.mp hzero with hnumerator | hdenominator_sq_zero
      · exact hnumerator
      · exact False.elim ((pow_ne_zero 2 hdenominator)
          hdenominator_sq_zero)
    have htreatedTerm : treatedShare * treatedArmVariance = 0 := by
      have htreatedTerm_nonneg :
          0 ≤ treatedShare * treatedArmVariance :=
        mul_nonneg (le_of_lt htreatedShare) htreatedVariance
      have hcontrolTerm_nonneg :
          0 ≤ controlShare * controlArmVariance :=
        mul_nonneg (le_of_lt hcontrolShare) hcontrolVariance
      linarith
    have hcontrolTerm : controlShare * controlArmVariance = 0 := by
      have htreatedTerm_nonneg :
          0 ≤ treatedShare * treatedArmVariance :=
        mul_nonneg (le_of_lt htreatedShare) htreatedVariance
      have hcontrolTerm_nonneg :
          0 ≤ controlShare * controlArmVariance :=
        mul_nonneg (le_of_lt hcontrolShare) hcontrolVariance
      linarith
    constructor
    · rcases mul_eq_zero.mp htreatedTerm with hshare_zero | hvariance_zero
      · exact False.elim ((ne_of_gt htreatedShare) hshare_zero)
      · exact hvariance_zero
    · rcases mul_eq_zero.mp hcontrolTerm with hshare_zero | hvariance_zero
      · exact False.elim ((ne_of_gt hcontrolShare) hshare_zero)
      · exact hvariance_zero
  · intro hvariances
    exact twoArmWeightedResidualVariance_eq_zero_of_arm_variances_zero
      denominator treatedShare controlShare treatedArmVariance
      controlArmVariance hvariances.1 hvariances.2

end WDSM
end Matching
end StatInference
