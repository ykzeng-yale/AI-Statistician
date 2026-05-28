import StatInference.Matching.WDSM.AsymptoticInterfaces
import StatInference.Matching.WDSM.ProspectiveResidualQuadraticVariationAudit

/-!
# Prospective residual martingale-array audit adapters

This module connects the prospective residual audit layer to the reusable
`ResidualMartingaleArrayCLTVarianceInput` interface.  It does not prove the
martingale CLT itself; it removes scenario-specific duplication by making the
remaining probability proof go through one generic martingale-array bridge.
-/

namespace StatInference
namespace Matching
namespace WDSM

/--
Build the prospective PATE residual CLT audit bridge from the generic residual
martingale-array input.
-/
def prospectivePATEResidualCLTAuditBridgeOfMartingaleArrayInput
    (input : ResidualMartingaleArrayCLTVarianceInput)
    (finiteQuadraticVariationFormula conditionalLyapunov
      quadraticVariationStabilization : Prop)
    (hmoments : input.exact_weighted_reuse_moment_limits)
    (hresidual : input.residual_moment_regularity)
    (hlyapunov_to_lindeberg :
      conditionalLyapunov -> input.conditional_lindeberg)
    (hqv_transfer :
      finiteQuadraticVariationFormula ->
      quadraticVariationStabilization ->
      input.predictable_quadratic_variation_stabilization) :
    ProspectivePATEResidualCLTAuditBridge where
  finite_quadratic_variation_formula_verified :=
    finiteQuadraticVariationFormula
  martingale_difference_array := input.martingale_difference_array
  conditional_lyapunov_condition := conditionalLyapunov
  quadratic_variation_stabilization := quadraticVariationStabilization
  residual_clt := input.residual_clt
  bridge := by
    intro hfinite hmartingale hlyapunov hqv
    exact residual_clt_of_martingale_array_input input hmoments hresidual
      hmartingale (hlyapunov_to_lindeberg hlyapunov)
      (hqv_transfer hfinite hqv)

/--
Prospective PATE residual CLT and residual variance formula from the generic
martingale-array input plus explicit finite-QV, Lyapunov, and QV-stabilization
transfers.
-/
theorem prospective_pate_residual_clt_and_variance_formula_of_martingale_array_input
    (input : ResidualMartingaleArrayCLTVarianceInput)
    (finiteQuadraticVariationFormula conditionalLyapunov
      quadraticVariationStabilization : Prop)
    (hmoments : input.exact_weighted_reuse_moment_limits)
    (hresidual : input.residual_moment_regularity)
    (hlyapunov_to_lindeberg :
      conditionalLyapunov -> input.conditional_lindeberg)
    (hqv_transfer :
      finiteQuadraticVariationFormula ->
      quadraticVariationStabilization ->
      input.predictable_quadratic_variation_stabilization)
    (hfinite : finiteQuadraticVariationFormula)
    (hmartingale : input.martingale_difference_array)
    (hlyapunov : conditionalLyapunov)
    (hqv : quadraticVariationStabilization) :
    input.residual_clt ∧ input.residual_variance_formula :=
  residual_clt_and_variance_formula_of_martingale_array_input input
    hmoments hresidual hmartingale
    (hlyapunov_to_lindeberg hlyapunov)
    (hqv_transfer hfinite hqv)

/-- Prospective PATE residual CLT from a generic martingale-array input. -/
theorem prospective_pate_residual_clt_of_martingale_array_input
    (input : ResidualMartingaleArrayCLTVarianceInput)
    (finiteQuadraticVariationFormula conditionalLyapunov
      quadraticVariationStabilization : Prop)
    (hmoments : input.exact_weighted_reuse_moment_limits)
    (hresidual : input.residual_moment_regularity)
    (hlyapunov_to_lindeberg :
      conditionalLyapunov -> input.conditional_lindeberg)
    (hqv_transfer :
      finiteQuadraticVariationFormula ->
      quadraticVariationStabilization ->
      input.predictable_quadratic_variation_stabilization)
    (hfinite : finiteQuadraticVariationFormula)
    (hmartingale : input.martingale_difference_array)
    (hlyapunov : conditionalLyapunov)
    (hqv : quadraticVariationStabilization) :
    input.residual_clt :=
  (prospective_pate_residual_clt_and_variance_formula_of_martingale_array_input
    input finiteQuadraticVariationFormula conditionalLyapunov
    quadraticVariationStabilization hmoments hresidual
    hlyapunov_to_lindeberg hqv_transfer hfinite hmartingale hlyapunov
    hqv).1

/--
Prospective PATE residual variance formula from a generic martingale-array
input.
-/
theorem prospective_pate_residual_variance_formula_of_martingale_array_input
    (input : ResidualMartingaleArrayCLTVarianceInput)
    (finiteQuadraticVariationFormula conditionalLyapunov
      quadraticVariationStabilization : Prop)
    (hmoments : input.exact_weighted_reuse_moment_limits)
    (hresidual : input.residual_moment_regularity)
    (hlyapunov_to_lindeberg :
      conditionalLyapunov -> input.conditional_lindeberg)
    (hqv_transfer :
      finiteQuadraticVariationFormula ->
      quadraticVariationStabilization ->
      input.predictable_quadratic_variation_stabilization)
    (hfinite : finiteQuadraticVariationFormula)
    (hmartingale : input.martingale_difference_array)
    (hlyapunov : conditionalLyapunov)
    (hqv : quadraticVariationStabilization) :
    input.residual_variance_formula :=
  (prospective_pate_residual_clt_and_variance_formula_of_martingale_array_input
    input finiteQuadraticVariationFormula conditionalLyapunov
    quadraticVariationStabilization hmoments hresidual
    hlyapunov_to_lindeberg hqv_transfer hfinite hmartingale hlyapunov
    hqv).2

/--
Build the prospective PATT residual CLT audit bridge from the generic residual
martingale-array input.
-/
def prospectivePATTResidualCLTAuditBridgeOfMartingaleArrayInput
    (input : ResidualMartingaleArrayCLTVarianceInput)
    (finiteQuadraticVariationFormula conditionalLyapunov
      quadraticVariationStabilization : Prop)
    (hmoments : input.exact_weighted_reuse_moment_limits)
    (hresidual : input.residual_moment_regularity)
    (hlyapunov_to_lindeberg :
      conditionalLyapunov -> input.conditional_lindeberg)
    (hqv_transfer :
      finiteQuadraticVariationFormula ->
      quadraticVariationStabilization ->
      input.predictable_quadratic_variation_stabilization) :
    ProspectivePATTResidualCLTAuditBridge where
  finite_quadratic_variation_formula_verified :=
    finiteQuadraticVariationFormula
  martingale_difference_array := input.martingale_difference_array
  conditional_lyapunov_condition := conditionalLyapunov
  quadratic_variation_stabilization := quadraticVariationStabilization
  residual_clt := input.residual_clt
  bridge := by
    intro hfinite hmartingale hlyapunov hqv
    exact residual_clt_of_martingale_array_input input hmoments hresidual
      hmartingale (hlyapunov_to_lindeberg hlyapunov)
      (hqv_transfer hfinite hqv)

/--
Prospective PATT residual CLT and residual variance formula from the generic
martingale-array input plus explicit finite-QV, Lyapunov, and QV-stabilization
transfers.
-/
theorem prospective_patt_residual_clt_and_variance_formula_of_martingale_array_input
    (input : ResidualMartingaleArrayCLTVarianceInput)
    (finiteQuadraticVariationFormula conditionalLyapunov
      quadraticVariationStabilization : Prop)
    (hmoments : input.exact_weighted_reuse_moment_limits)
    (hresidual : input.residual_moment_regularity)
    (hlyapunov_to_lindeberg :
      conditionalLyapunov -> input.conditional_lindeberg)
    (hqv_transfer :
      finiteQuadraticVariationFormula ->
      quadraticVariationStabilization ->
      input.predictable_quadratic_variation_stabilization)
    (hfinite : finiteQuadraticVariationFormula)
    (hmartingale : input.martingale_difference_array)
    (hlyapunov : conditionalLyapunov)
    (hqv : quadraticVariationStabilization) :
    input.residual_clt ∧ input.residual_variance_formula :=
  residual_clt_and_variance_formula_of_martingale_array_input input
    hmoments hresidual hmartingale
    (hlyapunov_to_lindeberg hlyapunov)
    (hqv_transfer hfinite hqv)

/-- Prospective PATT residual CLT from a generic martingale-array input. -/
theorem prospective_patt_residual_clt_of_martingale_array_input
    (input : ResidualMartingaleArrayCLTVarianceInput)
    (finiteQuadraticVariationFormula conditionalLyapunov
      quadraticVariationStabilization : Prop)
    (hmoments : input.exact_weighted_reuse_moment_limits)
    (hresidual : input.residual_moment_regularity)
    (hlyapunov_to_lindeberg :
      conditionalLyapunov -> input.conditional_lindeberg)
    (hqv_transfer :
      finiteQuadraticVariationFormula ->
      quadraticVariationStabilization ->
      input.predictable_quadratic_variation_stabilization)
    (hfinite : finiteQuadraticVariationFormula)
    (hmartingale : input.martingale_difference_array)
    (hlyapunov : conditionalLyapunov)
    (hqv : quadraticVariationStabilization) :
    input.residual_clt :=
  (prospective_patt_residual_clt_and_variance_formula_of_martingale_array_input
    input finiteQuadraticVariationFormula conditionalLyapunov
    quadraticVariationStabilization hmoments hresidual
    hlyapunov_to_lindeberg hqv_transfer hfinite hmartingale hlyapunov
    hqv).1

/--
Prospective PATT residual variance formula from a generic martingale-array
input.
-/
theorem prospective_patt_residual_variance_formula_of_martingale_array_input
    (input : ResidualMartingaleArrayCLTVarianceInput)
    (finiteQuadraticVariationFormula conditionalLyapunov
      quadraticVariationStabilization : Prop)
    (hmoments : input.exact_weighted_reuse_moment_limits)
    (hresidual : input.residual_moment_regularity)
    (hlyapunov_to_lindeberg :
      conditionalLyapunov -> input.conditional_lindeberg)
    (hqv_transfer :
      finiteQuadraticVariationFormula ->
      quadraticVariationStabilization ->
      input.predictable_quadratic_variation_stabilization)
    (hfinite : finiteQuadraticVariationFormula)
    (hmartingale : input.martingale_difference_array)
    (hlyapunov : conditionalLyapunov)
    (hqv : quadraticVariationStabilization) :
    input.residual_variance_formula :=
  (prospective_patt_residual_clt_and_variance_formula_of_martingale_array_input
    input finiteQuadraticVariationFormula conditionalLyapunov
    quadraticVariationStabilization hmoments hresidual
    hlyapunov_to_lindeberg hqv_transfer hfinite hmartingale hlyapunov
    hqv).2

/--
Paired prospective PATE/PATT residual CLT and residual variance formula from
generic martingale-array inputs plus explicit finite-QV, Lyapunov, and
QV-stabilization transfers.
-/
theorem prospective_pate_patt_residual_clt_and_variance_formula_of_martingale_array_input
    (pateInput pattInput : ResidualMartingaleArrayCLTVarianceInput)
    (pateFiniteQuadraticVariationFormula pateConditionalLyapunov
      pateQuadraticVariationStabilization : Prop)
    (pattFiniteQuadraticVariationFormula pattConditionalLyapunov
      pattQuadraticVariationStabilization : Prop)
    (hpate_moments :
      pateInput.exact_weighted_reuse_moment_limits)
    (hpate_residual : pateInput.residual_moment_regularity)
    (hpate_lyapunov_to_lindeberg :
      pateConditionalLyapunov -> pateInput.conditional_lindeberg)
    (hpate_qv_transfer :
      pateFiniteQuadraticVariationFormula ->
      pateQuadraticVariationStabilization ->
      pateInput.predictable_quadratic_variation_stabilization)
    (hpatt_moments :
      pattInput.exact_weighted_reuse_moment_limits)
    (hpatt_residual : pattInput.residual_moment_regularity)
    (hpatt_lyapunov_to_lindeberg :
      pattConditionalLyapunov -> pattInput.conditional_lindeberg)
    (hpatt_qv_transfer :
      pattFiniteQuadraticVariationFormula ->
      pattQuadraticVariationStabilization ->
      pattInput.predictable_quadratic_variation_stabilization)
    (hpate_finite : pateFiniteQuadraticVariationFormula)
    (hpate_martingale : pateInput.martingale_difference_array)
    (hpate_lyapunov : pateConditionalLyapunov)
    (hpate_qv : pateQuadraticVariationStabilization)
    (hpatt_finite : pattFiniteQuadraticVariationFormula)
    (hpatt_martingale : pattInput.martingale_difference_array)
    (hpatt_lyapunov : pattConditionalLyapunov)
    (hpatt_qv : pattQuadraticVariationStabilization) :
    pateInput.residual_clt ∧
      pateInput.residual_variance_formula ∧
      pattInput.residual_clt ∧
      pattInput.residual_variance_formula := by
  have hpate :
      pateInput.residual_clt ∧
        pateInput.residual_variance_formula :=
    prospective_pate_residual_clt_and_variance_formula_of_martingale_array_input
      pateInput pateFiniteQuadraticVariationFormula
      pateConditionalLyapunov pateQuadraticVariationStabilization
      hpate_moments hpate_residual hpate_lyapunov_to_lindeberg
      hpate_qv_transfer hpate_finite hpate_martingale hpate_lyapunov
      hpate_qv
  have hpatt :
      pattInput.residual_clt ∧
        pattInput.residual_variance_formula :=
    prospective_patt_residual_clt_and_variance_formula_of_martingale_array_input
      pattInput pattFiniteQuadraticVariationFormula
      pattConditionalLyapunov pattQuadraticVariationStabilization
      hpatt_moments hpatt_residual hpatt_lyapunov_to_lindeberg
      hpatt_qv_transfer hpatt_finite hpatt_martingale hpatt_lyapunov
      hpatt_qv
  exact ⟨hpate.1, hpate.2, hpatt.1, hpatt.2⟩

/-- Paired prospective residual CLTs from generic martingale-array inputs. -/
theorem prospective_pate_patt_residual_clts_of_martingale_array_input
    (pateInput pattInput : ResidualMartingaleArrayCLTVarianceInput)
    (pateFiniteQuadraticVariationFormula pateConditionalLyapunov
      pateQuadraticVariationStabilization : Prop)
    (pattFiniteQuadraticVariationFormula pattConditionalLyapunov
      pattQuadraticVariationStabilization : Prop)
    (hpate_moments :
      pateInput.exact_weighted_reuse_moment_limits)
    (hpate_residual : pateInput.residual_moment_regularity)
    (hpate_lyapunov_to_lindeberg :
      pateConditionalLyapunov -> pateInput.conditional_lindeberg)
    (hpate_qv_transfer :
      pateFiniteQuadraticVariationFormula ->
      pateQuadraticVariationStabilization ->
      pateInput.predictable_quadratic_variation_stabilization)
    (hpatt_moments :
      pattInput.exact_weighted_reuse_moment_limits)
    (hpatt_residual : pattInput.residual_moment_regularity)
    (hpatt_lyapunov_to_lindeberg :
      pattConditionalLyapunov -> pattInput.conditional_lindeberg)
    (hpatt_qv_transfer :
      pattFiniteQuadraticVariationFormula ->
      pattQuadraticVariationStabilization ->
      pattInput.predictable_quadratic_variation_stabilization)
    (hpate_finite : pateFiniteQuadraticVariationFormula)
    (hpate_martingale : pateInput.martingale_difference_array)
    (hpate_lyapunov : pateConditionalLyapunov)
    (hpate_qv : pateQuadraticVariationStabilization)
    (hpatt_finite : pattFiniteQuadraticVariationFormula)
    (hpatt_martingale : pattInput.martingale_difference_array)
    (hpatt_lyapunov : pattConditionalLyapunov)
    (hpatt_qv : pattQuadraticVariationStabilization) :
    pateInput.residual_clt ∧ pattInput.residual_clt := by
  have h :=
    prospective_pate_patt_residual_clt_and_variance_formula_of_martingale_array_input
      pateInput pattInput pateFiniteQuadraticVariationFormula
      pateConditionalLyapunov pateQuadraticVariationStabilization
      pattFiniteQuadraticVariationFormula pattConditionalLyapunov
      pattQuadraticVariationStabilization hpate_moments hpate_residual
      hpate_lyapunov_to_lindeberg hpate_qv_transfer hpatt_moments
      hpatt_residual hpatt_lyapunov_to_lindeberg hpatt_qv_transfer
      hpate_finite hpate_martingale hpate_lyapunov hpate_qv
      hpatt_finite hpatt_martingale hpatt_lyapunov hpatt_qv
  exact ⟨h.1, h.2.2.1⟩

/--
Paired prospective residual variance formulas from generic martingale-array
inputs.
-/
theorem prospective_pate_patt_residual_variance_formulas_of_martingale_array_input
    (pateInput pattInput : ResidualMartingaleArrayCLTVarianceInput)
    (pateFiniteQuadraticVariationFormula pateConditionalLyapunov
      pateQuadraticVariationStabilization : Prop)
    (pattFiniteQuadraticVariationFormula pattConditionalLyapunov
      pattQuadraticVariationStabilization : Prop)
    (hpate_moments :
      pateInput.exact_weighted_reuse_moment_limits)
    (hpate_residual : pateInput.residual_moment_regularity)
    (hpate_lyapunov_to_lindeberg :
      pateConditionalLyapunov -> pateInput.conditional_lindeberg)
    (hpate_qv_transfer :
      pateFiniteQuadraticVariationFormula ->
      pateQuadraticVariationStabilization ->
      pateInput.predictable_quadratic_variation_stabilization)
    (hpatt_moments :
      pattInput.exact_weighted_reuse_moment_limits)
    (hpatt_residual : pattInput.residual_moment_regularity)
    (hpatt_lyapunov_to_lindeberg :
      pattConditionalLyapunov -> pattInput.conditional_lindeberg)
    (hpatt_qv_transfer :
      pattFiniteQuadraticVariationFormula ->
      pattQuadraticVariationStabilization ->
      pattInput.predictable_quadratic_variation_stabilization)
    (hpate_finite : pateFiniteQuadraticVariationFormula)
    (hpate_martingale : pateInput.martingale_difference_array)
    (hpate_lyapunov : pateConditionalLyapunov)
    (hpate_qv : pateQuadraticVariationStabilization)
    (hpatt_finite : pattFiniteQuadraticVariationFormula)
    (hpatt_martingale : pattInput.martingale_difference_array)
    (hpatt_lyapunov : pattConditionalLyapunov)
    (hpatt_qv : pattQuadraticVariationStabilization) :
    pateInput.residual_variance_formula ∧
      pattInput.residual_variance_formula := by
  have h :=
    prospective_pate_patt_residual_clt_and_variance_formula_of_martingale_array_input
      pateInput pattInput pateFiniteQuadraticVariationFormula
      pateConditionalLyapunov pateQuadraticVariationStabilization
      pattFiniteQuadraticVariationFormula pattConditionalLyapunov
      pattQuadraticVariationStabilization hpate_moments hpate_residual
      hpate_lyapunov_to_lindeberg hpate_qv_transfer hpatt_moments
      hpatt_residual hpatt_lyapunov_to_lindeberg hpatt_qv_transfer
      hpate_finite hpate_martingale hpate_lyapunov hpate_qv
      hpatt_finite hpatt_martingale hpatt_lyapunov hpatt_qv
  exact ⟨h.2.1, h.2.2.2⟩

end WDSM
end Matching
end StatInference
