import StatInference.Matching.WDSM.VarianceAlgebra

/-!
# Prospective appendix variance-formula audit

This module audits the scalar variance formulas used in the prospective PATE
and PATT appendix routes.  The algebraic part is checked directly:

* known-score variance is heterogeneity plus residual variance;
* estimated-score variance is known-score variance minus the score-projection
  reduction plus the moving-target drift inflation;
* fixed-law targets are the zero-drift specialization.

The probability and geometry claims that identify the component limits remain
explicit named assumptions in the audit bridge structures below.
-/

namespace StatInference
namespace Matching
namespace WDSM

/-- Common scalar known-score variance formula for prospective PATE/PATT. -/
def prospectiveKnownScoreVarianceFormula
    (heterogeneityVariance residualVariance : Real) : Real :=
  oracleVariance heterogeneityVariance residualVariance

/--
Common scalar estimated-score variance formula for prospective PATE/PATT.
The projection term corresponds to
`gamma_1^T Sigma_U^{-1} gamma_1`; the drift term corresponds to
`gamma_2^T Sigma_theta gamma_2`.
-/
def prospectiveEstimatedScoreVarianceFormula
    (heterogeneityVariance residualVariance projectionReduction
      targetDriftInflation : Real) : Real :=
  estimatedScoreVariance
    (prospectiveKnownScoreVarianceFormula heterogeneityVariance
      residualVariance)
    projectionReduction targetDriftInflation

/-- The prospective known-score scalar variance is `V_H + V_E`. -/
theorem prospectiveKnownScoreVarianceFormula_eq_components
    (heterogeneityVariance residualVariance : Real) :
    prospectiveKnownScoreVarianceFormula heterogeneityVariance
        residualVariance =
      heterogeneityVariance + residualVariance := by
  rfl

/--
The prospective estimated-score scalar variance has the appendix component
form `V_H + V_E - projection + drift`.
-/
theorem prospectiveEstimatedScoreVarianceFormula_eq_appendix_components
    (heterogeneityVariance residualVariance projectionReduction
      targetDriftInflation : Real) :
    prospectiveEstimatedScoreVarianceFormula heterogeneityVariance
        residualVariance projectionReduction targetDriftInflation =
      heterogeneityVariance + residualVariance - projectionReduction +
        targetDriftInflation := by
  unfold prospectiveEstimatedScoreVarianceFormula
    prospectiveKnownScoreVarianceFormula estimatedScoreVariance oracleVariance
  ring

/-- Fixed-law prospective estimated-score variance is the zero-drift formula. -/
theorem prospectiveFixedLawEstimatedScoreVarianceFormula_eq_components
    (heterogeneityVariance residualVariance projectionReduction : Real) :
    prospectiveEstimatedScoreVarianceFormula heterogeneityVariance
        residualVariance projectionReduction 0 =
      heterogeneityVariance + residualVariance - projectionReduction := by
  rw [prospectiveEstimatedScoreVarianceFormula_eq_appendix_components]
  ring

/--
Changing-law prospective estimated-score variance is fixed-law variance plus
the moving-target drift inflation.
-/
theorem prospectiveChangingLawEstimatedScoreVarianceFormula_eq_fixed_plus_drift
    (heterogeneityVariance residualVariance projectionReduction
      targetDriftInflation : Real) :
    prospectiveEstimatedScoreVarianceFormula heterogeneityVariance
        residualVariance projectionReduction targetDriftInflation =
      prospectiveEstimatedScoreVarianceFormula heterogeneityVariance
        residualVariance projectionReduction 0 + targetDriftInflation := by
  rw [prospectiveEstimatedScoreVarianceFormula_eq_appendix_components,
    prospectiveFixedLawEstimatedScoreVarianceFormula_eq_components]

/--
If the moving-target drift term is zero, the prospective estimated-score
variance reduces to the fixed-law formula.
-/
theorem prospectiveEstimatedScoreVarianceFormula_eq_fixedLaw_of_drift_zero
    (heterogeneityVariance residualVariance projectionReduction
      targetDriftInflation : Real)
    (hdrift_zero : targetDriftInflation = 0) :
    prospectiveEstimatedScoreVarianceFormula heterogeneityVariance
        residualVariance projectionReduction targetDriftInflation =
      prospectiveEstimatedScoreVarianceFormula heterogeneityVariance
        residualVariance projectionReduction 0 := by
  rw [hdrift_zero]

/--
If projection and drift are equal, the prospective estimated-score variance
equals the known-score variance.
-/
theorem prospectiveEstimatedScoreVarianceFormula_eq_known_of_projection_eq_drift
    (heterogeneityVariance residualVariance projectionReduction
      targetDriftInflation : Real)
    (hprojection_eq_drift : projectionReduction = targetDriftInflation) :
    prospectiveEstimatedScoreVarianceFormula heterogeneityVariance
        residualVariance projectionReduction targetDriftInflation =
      prospectiveKnownScoreVarianceFormula heterogeneityVariance
        residualVariance := by
  unfold prospectiveEstimatedScoreVarianceFormula
  exact changingTargetVariance_eq_oracle_of_projection_eq_drift
    (prospectiveKnownScoreVarianceFormula heterogeneityVariance
      residualVariance)
    projectionReduction targetDriftInflation hprojection_eq_drift

/--
Strict projection slack and nonnegative drift imply positive prospective
estimated-score variance.
-/
theorem prospectiveEstimatedScoreVarianceFormula_pos_of_projection_lt_known_of_drift_nonneg
    (heterogeneityVariance residualVariance projectionReduction
      targetDriftInflation : Real)
    (hprojection_lt_known :
      projectionReduction <
        prospectiveKnownScoreVarianceFormula heterogeneityVariance
          residualVariance)
    (hdrift_nonneg : 0 ≤ targetDriftInflation) :
    0 <
      prospectiveEstimatedScoreVarianceFormula heterogeneityVariance
        residualVariance projectionReduction targetDriftInflation := by
  unfold prospectiveEstimatedScoreVarianceFormula
  exact changingTargetVariance_pos_of_projection_lt_oracle_of_drift_nonneg
    (prospectiveKnownScoreVarianceFormula heterogeneityVariance
      residualVariance)
    projectionReduction targetDriftInflation hprojection_lt_known
    hdrift_nonneg

/--
Weak projection slack and positive drift imply positive prospective
estimated-score variance.
-/
theorem prospectiveEstimatedScoreVarianceFormula_pos_of_projection_le_known_of_drift_pos
    (heterogeneityVariance residualVariance projectionReduction
      targetDriftInflation : Real)
    (hprojection_le_known :
      projectionReduction ≤
        prospectiveKnownScoreVarianceFormula heterogeneityVariance
          residualVariance)
    (hdrift_pos : 0 < targetDriftInflation) :
    0 <
      prospectiveEstimatedScoreVarianceFormula heterogeneityVariance
        residualVariance projectionReduction targetDriftInflation := by
  unfold prospectiveEstimatedScoreVarianceFormula
  exact changingTargetVariance_pos_of_projection_le_oracle_of_drift_pos
    (prospectiveKnownScoreVarianceFormula heterogeneityVariance
      residualVariance)
    projectionReduction targetDriftInflation hprojection_le_known
    hdrift_pos

/-- PATE-named wrapper for the prospective known-score variance formula. -/
def prospectivePATEKnownScoreVarianceFormula
    (heterogeneityVariance residualVariance : Real) : Real :=
  prospectiveKnownScoreVarianceFormula heterogeneityVariance residualVariance

/-- PATE-named wrapper for the prospective estimated-score variance formula. -/
def prospectivePATEEstimatedScoreVarianceFormula
    (heterogeneityVariance residualVariance projectionReduction
      targetDriftInflation : Real) : Real :=
  prospectiveEstimatedScoreVarianceFormula heterogeneityVariance
    residualVariance projectionReduction targetDriftInflation

/-- PATT-named wrapper for the prospective known-score variance formula. -/
def prospectivePATTKnownScoreVarianceFormula
    (heterogeneityVariance residualVariance : Real) : Real :=
  prospectiveKnownScoreVarianceFormula heterogeneityVariance residualVariance

/-- PATT-named wrapper for the prospective estimated-score variance formula. -/
def prospectivePATTEstimatedScoreVarianceFormula
    (heterogeneityVariance residualVariance projectionReduction
      targetDriftInflation : Real) : Real :=
  prospectiveEstimatedScoreVarianceFormula heterogeneityVariance
    residualVariance projectionReduction targetDriftInflation

/-- PATE known-score variance formula in component form. -/
theorem prospectivePATEKnownScoreVarianceFormula_eq_components
    (heterogeneityVariance residualVariance : Real) :
    prospectivePATEKnownScoreVarianceFormula heterogeneityVariance
        residualVariance =
      heterogeneityVariance + residualVariance := by
  exact prospectiveKnownScoreVarianceFormula_eq_components
    heterogeneityVariance residualVariance

/-- PATT known-score variance formula in component form. -/
theorem prospectivePATTKnownScoreVarianceFormula_eq_components
    (heterogeneityVariance residualVariance : Real) :
    prospectivePATTKnownScoreVarianceFormula heterogeneityVariance
        residualVariance =
      heterogeneityVariance + residualVariance := by
  exact prospectiveKnownScoreVarianceFormula_eq_components
    heterogeneityVariance residualVariance

/-- PATE appendix estimated-score variance formula in component form. -/
theorem prospectivePATEEstimatedScoreVarianceFormula_eq_appendix_components
    (heterogeneityVariance residualVariance projectionReduction
      targetDriftInflation : Real) :
    prospectivePATEEstimatedScoreVarianceFormula heterogeneityVariance
        residualVariance projectionReduction targetDriftInflation =
      heterogeneityVariance + residualVariance - projectionReduction +
        targetDriftInflation := by
  exact prospectiveEstimatedScoreVarianceFormula_eq_appendix_components
    heterogeneityVariance residualVariance projectionReduction
    targetDriftInflation

/-- PATT appendix estimated-score variance formula in component form. -/
theorem prospectivePATTEstimatedScoreVarianceFormula_eq_appendix_components
    (heterogeneityVariance residualVariance projectionReduction
      targetDriftInflation : Real) :
    prospectivePATTEstimatedScoreVarianceFormula heterogeneityVariance
        residualVariance projectionReduction targetDriftInflation =
      heterogeneityVariance + residualVariance - projectionReduction +
        targetDriftInflation := by
  exact prospectiveEstimatedScoreVarianceFormula_eq_appendix_components
    heterogeneityVariance residualVariance projectionReduction
    targetDriftInflation

/-- PATE fixed-law estimated-score variance formula in component form. -/
theorem prospectivePATEFixedLawEstimatedScoreVarianceFormula_eq_components
    (heterogeneityVariance residualVariance projectionReduction : Real) :
    prospectivePATEEstimatedScoreVarianceFormula heterogeneityVariance
        residualVariance projectionReduction 0 =
      heterogeneityVariance + residualVariance - projectionReduction := by
  exact prospectiveFixedLawEstimatedScoreVarianceFormula_eq_components
    heterogeneityVariance residualVariance projectionReduction

/-- PATT fixed-law estimated-score variance formula in component form. -/
theorem prospectivePATTFixedLawEstimatedScoreVarianceFormula_eq_components
    (heterogeneityVariance residualVariance projectionReduction : Real) :
    prospectivePATTEstimatedScoreVarianceFormula heterogeneityVariance
        residualVariance projectionReduction 0 =
      heterogeneityVariance + residualVariance - projectionReduction := by
  exact prospectiveFixedLawEstimatedScoreVarianceFormula_eq_components
    heterogeneityVariance residualVariance projectionReduction

/-- Paired PATE/PATT known-score variance formula component rewrites. -/
theorem prospectivePATEPATTKnownScoreVarianceFormula_eq_components
    (pateHeterogeneityVariance pateResidualVariance
      pattHeterogeneityVariance pattResidualVariance : Real) :
    prospectivePATEKnownScoreVarianceFormula pateHeterogeneityVariance
        pateResidualVariance =
      pateHeterogeneityVariance + pateResidualVariance ∧
    prospectivePATTKnownScoreVarianceFormula pattHeterogeneityVariance
        pattResidualVariance =
      pattHeterogeneityVariance + pattResidualVariance := by
  exact
    ⟨prospectivePATEKnownScoreVarianceFormula_eq_components
        pateHeterogeneityVariance pateResidualVariance,
      prospectivePATTKnownScoreVarianceFormula_eq_components
        pattHeterogeneityVariance pattResidualVariance⟩

/--
Paired PATE/PATT appendix estimated-score variance formula component rewrites.
-/
theorem prospectivePATEPATTEstimatedScoreVarianceFormula_eq_appendix_components
    (pateHeterogeneityVariance pateResidualVariance pateProjectionReduction
      pateTargetDriftInflation pattHeterogeneityVariance pattResidualVariance
      pattProjectionReduction pattTargetDriftInflation : Real) :
    prospectivePATEEstimatedScoreVarianceFormula pateHeterogeneityVariance
        pateResidualVariance pateProjectionReduction pateTargetDriftInflation =
      pateHeterogeneityVariance + pateResidualVariance -
        pateProjectionReduction + pateTargetDriftInflation ∧
    prospectivePATTEstimatedScoreVarianceFormula pattHeterogeneityVariance
        pattResidualVariance pattProjectionReduction pattTargetDriftInflation =
      pattHeterogeneityVariance + pattResidualVariance -
        pattProjectionReduction + pattTargetDriftInflation := by
  exact
    ⟨prospectivePATEEstimatedScoreVarianceFormula_eq_appendix_components
        pateHeterogeneityVariance pateResidualVariance pateProjectionReduction
        pateTargetDriftInflation,
      prospectivePATTEstimatedScoreVarianceFormula_eq_appendix_components
        pattHeterogeneityVariance pattResidualVariance pattProjectionReduction
        pattTargetDriftInflation⟩

/-- Paired PATE/PATT fixed-law estimated-score variance formula rewrites. -/
theorem prospectivePATEPATTFixedLawEstimatedScoreVarianceFormula_eq_components
    (pateHeterogeneityVariance pateResidualVariance pateProjectionReduction
      pattHeterogeneityVariance pattResidualVariance pattProjectionReduction :
      Real) :
    prospectivePATEEstimatedScoreVarianceFormula pateHeterogeneityVariance
        pateResidualVariance pateProjectionReduction 0 =
      pateHeterogeneityVariance + pateResidualVariance -
        pateProjectionReduction ∧
    prospectivePATTEstimatedScoreVarianceFormula pattHeterogeneityVariance
        pattResidualVariance pattProjectionReduction 0 =
      pattHeterogeneityVariance + pattResidualVariance -
        pattProjectionReduction := by
  exact
    ⟨prospectivePATEFixedLawEstimatedScoreVarianceFormula_eq_components
        pateHeterogeneityVariance pateResidualVariance pateProjectionReduction,
      prospectivePATTFixedLawEstimatedScoreVarianceFormula_eq_components
        pattHeterogeneityVariance pattResidualVariance pattProjectionReduction⟩

/--
Audit bridge for prospective PATE variance formulas.  The scalar formula is
checked above; the fields here name the remaining probability, geometry, and
first-step claims that must be supplied by reference-theorem ports or later
Lean proofs.
-/
structure ProspectivePATEAppendixVarianceFormulaAuditBridge where
  residual_quadratic_variation_limit : Prop
  residual_lyapunov_condition : Prop
  heterogeneity_variance_formula : Prop
  score_projection_formula : Prop
  target_drift_formula : Prop
  known_score_variance_formula : Prop
  estimated_score_variance_formula : Prop
  known_score_bridge :
    residual_quadratic_variation_limit ->
    residual_lyapunov_condition ->
    heterogeneity_variance_formula ->
    known_score_variance_formula
  estimated_score_bridge :
    known_score_variance_formula ->
    score_projection_formula ->
    target_drift_formula ->
    estimated_score_variance_formula

/-- Prospective PATE appendix variance audit from explicit named inputs. -/
theorem prospective_pate_appendix_variance_formula_audit_of_components
    (b : ProspectivePATEAppendixVarianceFormulaAuditBridge)
    (hresidual_qv : b.residual_quadratic_variation_limit)
    (hlyapunov : b.residual_lyapunov_condition)
    (hheterogeneity : b.heterogeneity_variance_formula)
    (hprojection : b.score_projection_formula)
    (hdrift : b.target_drift_formula) :
    b.known_score_variance_formula ∧
      b.estimated_score_variance_formula := by
  have hknown :=
    b.known_score_bridge hresidual_qv hlyapunov hheterogeneity
  exact ⟨hknown, b.estimated_score_bridge hknown hprojection hdrift⟩

/--
Audit bridge for prospective PATT variance formulas.  This keeps the one-sided
PATT heterogeneity and residual components explicit.
-/
structure ProspectivePATTAppendixVarianceFormulaAuditBridge where
  residual_quadratic_variation_limit : Prop
  residual_lyapunov_condition : Prop
  heterogeneity_variance_formula : Prop
  score_projection_formula : Prop
  target_drift_formula : Prop
  known_score_variance_formula : Prop
  estimated_score_variance_formula : Prop
  known_score_bridge :
    residual_quadratic_variation_limit ->
    residual_lyapunov_condition ->
    heterogeneity_variance_formula ->
    known_score_variance_formula
  estimated_score_bridge :
    known_score_variance_formula ->
    score_projection_formula ->
    target_drift_formula ->
    estimated_score_variance_formula

/-- Prospective PATT appendix variance audit from explicit named inputs. -/
theorem prospective_patt_appendix_variance_formula_audit_of_components
    (b : ProspectivePATTAppendixVarianceFormulaAuditBridge)
    (hresidual_qv : b.residual_quadratic_variation_limit)
    (hlyapunov : b.residual_lyapunov_condition)
    (hheterogeneity : b.heterogeneity_variance_formula)
    (hprojection : b.score_projection_formula)
    (hdrift : b.target_drift_formula) :
    b.known_score_variance_formula ∧
      b.estimated_score_variance_formula := by
  have hknown :=
    b.known_score_bridge hresidual_qv hlyapunov hheterogeneity
  exact ⟨hknown, b.estimated_score_bridge hknown hprojection hdrift⟩

/--
Paired prospective PATE/PATT appendix variance audit from explicit named
inputs.
-/
theorem prospective_pate_patt_appendix_variance_formula_audit_of_components
    (pate : ProspectivePATEAppendixVarianceFormulaAuditBridge)
    (patt : ProspectivePATTAppendixVarianceFormulaAuditBridge)
    (hpate_residual_qv : pate.residual_quadratic_variation_limit)
    (hpate_lyapunov : pate.residual_lyapunov_condition)
    (hpate_heterogeneity : pate.heterogeneity_variance_formula)
    (hpate_projection : pate.score_projection_formula)
    (hpate_drift : pate.target_drift_formula)
    (hpatt_residual_qv : patt.residual_quadratic_variation_limit)
    (hpatt_lyapunov : patt.residual_lyapunov_condition)
    (hpatt_heterogeneity : patt.heterogeneity_variance_formula)
    (hpatt_projection : patt.score_projection_formula)
    (hpatt_drift : patt.target_drift_formula) :
    pate.known_score_variance_formula ∧
      pate.estimated_score_variance_formula ∧
      patt.known_score_variance_formula ∧
      patt.estimated_score_variance_formula := by
  have hpate :
      pate.known_score_variance_formula ∧
        pate.estimated_score_variance_formula :=
    prospective_pate_appendix_variance_formula_audit_of_components
      pate hpate_residual_qv hpate_lyapunov hpate_heterogeneity
      hpate_projection hpate_drift
  have hpatt :
      patt.known_score_variance_formula ∧
        patt.estimated_score_variance_formula :=
    prospective_patt_appendix_variance_formula_audit_of_components
      patt hpatt_residual_qv hpatt_lyapunov hpatt_heterogeneity
      hpatt_projection hpatt_drift
  exact ⟨hpate.1, hpate.2, hpatt.1, hpatt.2⟩

end WDSM
end Matching
end StatInference
