import StatInference.Matching.WDSM.ProspectiveResidualQuadraticVariationAudit
import StatInference.Matching.WDSM.ProspectiveVarianceFormulaAudit

/-!
# Prospective residual-QV to variance-formula audit

This module connects the checked finite residual quadratic-variation displays
to the prospective appendix variance-formula audit.  It keeps the genuine
probability ingredients explicit: martingale structure, Lyapunov control, and
quadratic-variation stabilization still have to be supplied by later
reference-theorem ports or direct Lean proofs.
-/

namespace StatInference
namespace Matching
namespace WDSM

/--
Composition bridge from the prospective PATE residual-QV audit to the
prospective PATE variance-formula audit.
-/
structure ProspectivePATEResidualQVVarianceAuditBridge where
  residual_bridge : ProspectivePATEResidualCLTAuditBridge
  variance_bridge : ProspectivePATEAppendixVarianceFormulaAuditBridge
  residual_qv_limit_bridge :
    residual_bridge.finite_quadratic_variation_formula_verified ->
    residual_bridge.quadratic_variation_stabilization ->
    variance_bridge.residual_quadratic_variation_limit
  residual_lyapunov_bridge :
    residual_bridge.conditional_lyapunov_condition ->
    variance_bridge.residual_lyapunov_condition

/--
Prospective PATE residual CLT and appendix variance formulas from the checked
finite residual-QV audit plus explicit probability and component inputs.
-/
theorem prospective_pate_variance_formula_audit_of_residual_qv_audit
    (b : ProspectivePATEResidualQVVarianceAuditBridge)
    (hfinite : b.residual_bridge.finite_quadratic_variation_formula_verified)
    (hmartingale : b.residual_bridge.martingale_difference_array)
    (hlyapunov : b.residual_bridge.conditional_lyapunov_condition)
    (hqv : b.residual_bridge.quadratic_variation_stabilization)
    (hheterogeneity :
      b.variance_bridge.heterogeneity_variance_formula)
    (hprojection : b.variance_bridge.score_projection_formula)
    (hdrift : b.variance_bridge.target_drift_formula) :
    b.residual_bridge.residual_clt ∧
      b.variance_bridge.known_score_variance_formula ∧
      b.variance_bridge.estimated_score_variance_formula := by
  have hresidual_clt :
      b.residual_bridge.residual_clt :=
    prospective_pate_residual_clt_of_quadratic_variation_audit
      b.residual_bridge hfinite hmartingale hlyapunov hqv
  have hresidual_qv :
      b.variance_bridge.residual_quadratic_variation_limit :=
    b.residual_qv_limit_bridge hfinite hqv
  have hvariance_lyapunov :
      b.variance_bridge.residual_lyapunov_condition :=
    b.residual_lyapunov_bridge hlyapunov
  have hvariance :=
    prospective_pate_appendix_variance_formula_audit_of_components
      b.variance_bridge hresidual_qv hvariance_lyapunov
      hheterogeneity hprojection hdrift
  exact ⟨hresidual_clt, hvariance.1, hvariance.2⟩

/--
Composition bridge from the prospective PATT residual-QV audit to the
prospective PATT variance-formula audit.
-/
structure ProspectivePATTResidualQVVarianceAuditBridge where
  residual_bridge : ProspectivePATTResidualCLTAuditBridge
  variance_bridge : ProspectivePATTAppendixVarianceFormulaAuditBridge
  residual_qv_limit_bridge :
    residual_bridge.finite_quadratic_variation_formula_verified ->
    residual_bridge.quadratic_variation_stabilization ->
    variance_bridge.residual_quadratic_variation_limit
  residual_lyapunov_bridge :
    residual_bridge.conditional_lyapunov_condition ->
    variance_bridge.residual_lyapunov_condition

/--
Prospective PATT residual CLT and appendix variance formulas from the checked
finite residual-QV audit plus explicit probability and component inputs.
-/
theorem prospective_patt_variance_formula_audit_of_residual_qv_audit
    (b : ProspectivePATTResidualQVVarianceAuditBridge)
    (hfinite : b.residual_bridge.finite_quadratic_variation_formula_verified)
    (hmartingale : b.residual_bridge.martingale_difference_array)
    (hlyapunov : b.residual_bridge.conditional_lyapunov_condition)
    (hqv : b.residual_bridge.quadratic_variation_stabilization)
    (hheterogeneity :
      b.variance_bridge.heterogeneity_variance_formula)
    (hprojection : b.variance_bridge.score_projection_formula)
    (hdrift : b.variance_bridge.target_drift_formula) :
    b.residual_bridge.residual_clt ∧
      b.variance_bridge.known_score_variance_formula ∧
      b.variance_bridge.estimated_score_variance_formula := by
  have hresidual_clt :
      b.residual_bridge.residual_clt :=
    prospective_patt_residual_clt_of_quadratic_variation_audit
      b.residual_bridge hfinite hmartingale hlyapunov hqv
  have hresidual_qv :
      b.variance_bridge.residual_quadratic_variation_limit :=
    b.residual_qv_limit_bridge hfinite hqv
  have hvariance_lyapunov :
      b.variance_bridge.residual_lyapunov_condition :=
    b.residual_lyapunov_bridge hlyapunov
  have hvariance :=
    prospective_patt_appendix_variance_formula_audit_of_components
      b.variance_bridge hresidual_qv hvariance_lyapunov
      hheterogeneity hprojection hdrift
  exact ⟨hresidual_clt, hvariance.1, hvariance.2⟩

/--
Paired prospective PATE/PATT residual CLT and appendix variance-formula audit
from residual quadratic-variation audit inputs.
-/
theorem prospective_pate_patt_variance_formula_audit_of_residual_qv_audit
    (pate : ProspectivePATEResidualQVVarianceAuditBridge)
    (patt : ProspectivePATTResidualQVVarianceAuditBridge)
    (hpate_finite :
      pate.residual_bridge.finite_quadratic_variation_formula_verified)
    (hpate_martingale : pate.residual_bridge.martingale_difference_array)
    (hpate_lyapunov :
      pate.residual_bridge.conditional_lyapunov_condition)
    (hpate_qv : pate.residual_bridge.quadratic_variation_stabilization)
    (hpate_heterogeneity :
      pate.variance_bridge.heterogeneity_variance_formula)
    (hpate_projection : pate.variance_bridge.score_projection_formula)
    (hpate_drift : pate.variance_bridge.target_drift_formula)
    (hpatt_finite :
      patt.residual_bridge.finite_quadratic_variation_formula_verified)
    (hpatt_martingale : patt.residual_bridge.martingale_difference_array)
    (hpatt_lyapunov :
      patt.residual_bridge.conditional_lyapunov_condition)
    (hpatt_qv : patt.residual_bridge.quadratic_variation_stabilization)
    (hpatt_heterogeneity :
      patt.variance_bridge.heterogeneity_variance_formula)
    (hpatt_projection : patt.variance_bridge.score_projection_formula)
    (hpatt_drift : patt.variance_bridge.target_drift_formula) :
    pate.residual_bridge.residual_clt ∧
      pate.variance_bridge.known_score_variance_formula ∧
      pate.variance_bridge.estimated_score_variance_formula ∧
      patt.residual_bridge.residual_clt ∧
      patt.variance_bridge.known_score_variance_formula ∧
      patt.variance_bridge.estimated_score_variance_formula := by
  have hpate :
      pate.residual_bridge.residual_clt ∧
        pate.variance_bridge.known_score_variance_formula ∧
        pate.variance_bridge.estimated_score_variance_formula :=
    prospective_pate_variance_formula_audit_of_residual_qv_audit
      pate hpate_finite hpate_martingale hpate_lyapunov hpate_qv
      hpate_heterogeneity hpate_projection hpate_drift
  have hpatt :
      patt.residual_bridge.residual_clt ∧
        patt.variance_bridge.known_score_variance_formula ∧
        patt.variance_bridge.estimated_score_variance_formula :=
    prospective_patt_variance_formula_audit_of_residual_qv_audit
      patt hpatt_finite hpatt_martingale hpatt_lyapunov hpatt_qv
      hpatt_heterogeneity hpatt_projection hpatt_drift
  exact
    ⟨hpate.1, hpate.2.1, hpate.2.2, hpatt.1, hpatt.2.1,
      hpatt.2.2⟩

end WDSM
end Matching
end StatInference
