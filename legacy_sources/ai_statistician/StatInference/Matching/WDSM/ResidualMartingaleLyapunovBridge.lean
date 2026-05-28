import StatInference.Matching.WDSM.ProspectiveResidualMartingaleAudit

/-!
# Residual martingale Lyapunov bridge

This module factors the WDSM residual CLT obligation through a Lyapunov-style
martingale-array interface.  The true probability theorem is still an explicit
input, but PATE/PATT residual audits can now share the same generic Lyapunov
bridge instead of carrying separate Lindeberg-transfer assumptions.
-/

namespace StatInference
namespace Matching
namespace WDSM

/--
Residual martingale-array CLT input stated directly with a conditional
Lyapunov control condition.

The field `lyapunov_martingale_clt_bridge` is the external probability theorem
still needed for the full WDSM asymptotic proof.
-/
structure ResidualLyapunovArrayCLTVarianceInput where
  exact_weighted_reuse_moment_limits : Prop
  residual_moment_regularity : Prop
  martingale_difference_array : Prop
  conditional_lyapunov : Prop
  predictable_quadratic_variation_stabilization : Prop
  residual_clt : Prop
  residual_variance_formula : Prop
  lyapunov_martingale_clt_bridge :
    exact_weighted_reuse_moment_limits ->
    residual_moment_regularity ->
    martingale_difference_array ->
    conditional_lyapunov ->
    predictable_quadratic_variation_stabilization ->
    residual_clt ∧ residual_variance_formula

/-- Lyapunov martingale-array input yields residual CLT plus variance formula. -/
theorem residual_clt_and_variance_formula_of_lyapunov_array_input
    (b : ResidualLyapunovArrayCLTVarianceInput)
    (hmoments : b.exact_weighted_reuse_moment_limits)
    (hresidual : b.residual_moment_regularity)
    (hmartingale : b.martingale_difference_array)
    (hlyapunov : b.conditional_lyapunov)
    (hquad : b.predictable_quadratic_variation_stabilization) :
    b.residual_clt ∧ b.residual_variance_formula :=
  b.lyapunov_martingale_clt_bridge hmoments hresidual hmartingale
    hlyapunov hquad

/-- Lyapunov martingale-array input yields the residual CLT. -/
theorem residual_clt_of_lyapunov_array_input
    (b : ResidualLyapunovArrayCLTVarianceInput)
    (hmoments : b.exact_weighted_reuse_moment_limits)
    (hresidual : b.residual_moment_regularity)
    (hmartingale : b.martingale_difference_array)
    (hlyapunov : b.conditional_lyapunov)
    (hquad : b.predictable_quadratic_variation_stabilization) :
    b.residual_clt :=
  (residual_clt_and_variance_formula_of_lyapunov_array_input b hmoments
    hresidual hmartingale hlyapunov hquad).1

/-- Lyapunov martingale-array input yields the residual variance formula. -/
theorem residual_variance_formula_of_lyapunov_array_input
    (b : ResidualLyapunovArrayCLTVarianceInput)
    (hmoments : b.exact_weighted_reuse_moment_limits)
    (hresidual : b.residual_moment_regularity)
    (hmartingale : b.martingale_difference_array)
    (hlyapunov : b.conditional_lyapunov)
    (hquad : b.predictable_quadratic_variation_stabilization) :
    b.residual_variance_formula :=
  (residual_clt_and_variance_formula_of_lyapunov_array_input b hmoments
    hresidual hmartingale hlyapunov hquad).2

/--
View the Lyapunov input as the existing martingale-array input by using the
Lyapunov condition as the sufficient Lindeberg-side control proposition.
-/
def residualMartingaleArrayCLTVarianceInputOfLyapunovArrayInput
    (b : ResidualLyapunovArrayCLTVarianceInput) :
    ResidualMartingaleArrayCLTVarianceInput where
  exact_weighted_reuse_moment_limits := b.exact_weighted_reuse_moment_limits
  residual_moment_regularity := b.residual_moment_regularity
  martingale_difference_array := b.martingale_difference_array
  conditional_lindeberg := b.conditional_lyapunov
  predictable_quadratic_variation_stabilization :=
    b.predictable_quadratic_variation_stabilization
  residual_clt := b.residual_clt
  residual_variance_formula := b.residual_variance_formula
  martingale_clt_bridge := by
    intro hmoments hresidual hmartingale hlyapunov hquad
    exact b.lyapunov_martingale_clt_bridge hmoments hresidual
      hmartingale hlyapunov hquad

/--
Package a Lyapunov residual input as the existing residual CLT/variance bridge
once martingale and Lyapunov conditions have been supplied.
-/
def residualArrayCLTVarianceBridgeOfLyapunovArrayInput
    (b : ResidualLyapunovArrayCLTVarianceInput)
    (hmartingale : b.martingale_difference_array)
    (hlyapunov : b.conditional_lyapunov) :
    ResidualArrayCLTVarianceBridge :=
  residualArrayCLTVarianceBridgeOfMartingaleArrayInput
    (residualMartingaleArrayCLTVarianceInputOfLyapunovArrayInput b)
    hmartingale hlyapunov

/--
Build the prospective PATE residual audit bridge directly from the generic
Lyapunov-array input.
-/
def prospectivePATEResidualCLTAuditBridgeOfLyapunovArrayInput
    (input : ResidualLyapunovArrayCLTVarianceInput)
    (finiteQuadraticVariationFormula quadraticVariationStabilization : Prop)
    (hmoments : input.exact_weighted_reuse_moment_limits)
    (hresidual : input.residual_moment_regularity)
    (hqv_transfer :
      finiteQuadraticVariationFormula ->
      quadraticVariationStabilization ->
      input.predictable_quadratic_variation_stabilization) :
    ProspectivePATEResidualCLTAuditBridge :=
  prospectivePATEResidualCLTAuditBridgeOfMartingaleArrayInput
    (residualMartingaleArrayCLTVarianceInputOfLyapunovArrayInput input)
    finiteQuadraticVariationFormula input.conditional_lyapunov
    quadraticVariationStabilization hmoments hresidual
    (fun hlyapunov => hlyapunov)
    hqv_transfer

/--
Prospective PATE residual CLT and residual variance formula from the generic
Lyapunov-array input.
-/
theorem prospective_pate_residual_clt_and_variance_formula_of_lyapunov_array_input
    (input : ResidualLyapunovArrayCLTVarianceInput)
    (finiteQuadraticVariationFormula quadraticVariationStabilization : Prop)
    (hmoments : input.exact_weighted_reuse_moment_limits)
    (hresidual : input.residual_moment_regularity)
    (hqv_transfer :
      finiteQuadraticVariationFormula ->
      quadraticVariationStabilization ->
      input.predictable_quadratic_variation_stabilization)
    (hfinite : finiteQuadraticVariationFormula)
    (hmartingale : input.martingale_difference_array)
    (hlyapunov : input.conditional_lyapunov)
    (hqv : quadraticVariationStabilization) :
    input.residual_clt ∧ input.residual_variance_formula :=
  prospective_pate_residual_clt_and_variance_formula_of_martingale_array_input
    (residualMartingaleArrayCLTVarianceInputOfLyapunovArrayInput input)
    finiteQuadraticVariationFormula input.conditional_lyapunov
    quadraticVariationStabilization hmoments hresidual
    (fun hlyapunov => hlyapunov) hqv_transfer
    hfinite hmartingale hlyapunov hqv

/-- Prospective PATE residual CLT from the generic Lyapunov-array input. -/
theorem prospective_pate_residual_clt_of_lyapunov_array_input
    (input : ResidualLyapunovArrayCLTVarianceInput)
    (finiteQuadraticVariationFormula quadraticVariationStabilization : Prop)
    (hmoments : input.exact_weighted_reuse_moment_limits)
    (hresidual : input.residual_moment_regularity)
    (hqv_transfer :
      finiteQuadraticVariationFormula ->
      quadraticVariationStabilization ->
      input.predictable_quadratic_variation_stabilization)
    (hfinite : finiteQuadraticVariationFormula)
    (hmartingale : input.martingale_difference_array)
    (hlyapunov : input.conditional_lyapunov)
    (hqv : quadraticVariationStabilization) :
    input.residual_clt :=
  (prospective_pate_residual_clt_and_variance_formula_of_lyapunov_array_input
    input finiteQuadraticVariationFormula quadraticVariationStabilization
    hmoments hresidual hqv_transfer hfinite hmartingale hlyapunov hqv).1

/--
Prospective PATE residual variance formula from the generic Lyapunov-array
input.
-/
theorem prospective_pate_residual_variance_formula_of_lyapunov_array_input
    (input : ResidualLyapunovArrayCLTVarianceInput)
    (finiteQuadraticVariationFormula quadraticVariationStabilization : Prop)
    (hmoments : input.exact_weighted_reuse_moment_limits)
    (hresidual : input.residual_moment_regularity)
    (hqv_transfer :
      finiteQuadraticVariationFormula ->
      quadraticVariationStabilization ->
      input.predictable_quadratic_variation_stabilization)
    (hfinite : finiteQuadraticVariationFormula)
    (hmartingale : input.martingale_difference_array)
    (hlyapunov : input.conditional_lyapunov)
    (hqv : quadraticVariationStabilization) :
    input.residual_variance_formula :=
  (prospective_pate_residual_clt_and_variance_formula_of_lyapunov_array_input
    input finiteQuadraticVariationFormula quadraticVariationStabilization
    hmoments hresidual hqv_transfer hfinite hmartingale hlyapunov hqv).2

/--
Build the prospective PATT residual audit bridge directly from the generic
Lyapunov-array input.
-/
def prospectivePATTResidualCLTAuditBridgeOfLyapunovArrayInput
    (input : ResidualLyapunovArrayCLTVarianceInput)
    (finiteQuadraticVariationFormula quadraticVariationStabilization : Prop)
    (hmoments : input.exact_weighted_reuse_moment_limits)
    (hresidual : input.residual_moment_regularity)
    (hqv_transfer :
      finiteQuadraticVariationFormula ->
      quadraticVariationStabilization ->
      input.predictable_quadratic_variation_stabilization) :
    ProspectivePATTResidualCLTAuditBridge :=
  prospectivePATTResidualCLTAuditBridgeOfMartingaleArrayInput
    (residualMartingaleArrayCLTVarianceInputOfLyapunovArrayInput input)
    finiteQuadraticVariationFormula input.conditional_lyapunov
    quadraticVariationStabilization hmoments hresidual
    (fun hlyapunov => hlyapunov)
    hqv_transfer

/--
Prospective PATT residual CLT and residual variance formula from the generic
Lyapunov-array input.
-/
theorem prospective_patt_residual_clt_and_variance_formula_of_lyapunov_array_input
    (input : ResidualLyapunovArrayCLTVarianceInput)
    (finiteQuadraticVariationFormula quadraticVariationStabilization : Prop)
    (hmoments : input.exact_weighted_reuse_moment_limits)
    (hresidual : input.residual_moment_regularity)
    (hqv_transfer :
      finiteQuadraticVariationFormula ->
      quadraticVariationStabilization ->
      input.predictable_quadratic_variation_stabilization)
    (hfinite : finiteQuadraticVariationFormula)
    (hmartingale : input.martingale_difference_array)
    (hlyapunov : input.conditional_lyapunov)
    (hqv : quadraticVariationStabilization) :
    input.residual_clt ∧ input.residual_variance_formula :=
  prospective_patt_residual_clt_and_variance_formula_of_martingale_array_input
    (residualMartingaleArrayCLTVarianceInputOfLyapunovArrayInput input)
    finiteQuadraticVariationFormula input.conditional_lyapunov
    quadraticVariationStabilization hmoments hresidual
    (fun hlyapunov => hlyapunov) hqv_transfer
    hfinite hmartingale hlyapunov hqv

/-- Prospective PATT residual CLT from the generic Lyapunov-array input. -/
theorem prospective_patt_residual_clt_of_lyapunov_array_input
    (input : ResidualLyapunovArrayCLTVarianceInput)
    (finiteQuadraticVariationFormula quadraticVariationStabilization : Prop)
    (hmoments : input.exact_weighted_reuse_moment_limits)
    (hresidual : input.residual_moment_regularity)
    (hqv_transfer :
      finiteQuadraticVariationFormula ->
      quadraticVariationStabilization ->
      input.predictable_quadratic_variation_stabilization)
    (hfinite : finiteQuadraticVariationFormula)
    (hmartingale : input.martingale_difference_array)
    (hlyapunov : input.conditional_lyapunov)
    (hqv : quadraticVariationStabilization) :
    input.residual_clt :=
  (prospective_patt_residual_clt_and_variance_formula_of_lyapunov_array_input
    input finiteQuadraticVariationFormula quadraticVariationStabilization
    hmoments hresidual hqv_transfer hfinite hmartingale hlyapunov hqv).1

/--
Prospective PATT residual variance formula from the generic Lyapunov-array
input.
-/
theorem prospective_patt_residual_variance_formula_of_lyapunov_array_input
    (input : ResidualLyapunovArrayCLTVarianceInput)
    (finiteQuadraticVariationFormula quadraticVariationStabilization : Prop)
    (hmoments : input.exact_weighted_reuse_moment_limits)
    (hresidual : input.residual_moment_regularity)
    (hqv_transfer :
      finiteQuadraticVariationFormula ->
      quadraticVariationStabilization ->
      input.predictable_quadratic_variation_stabilization)
    (hfinite : finiteQuadraticVariationFormula)
    (hmartingale : input.martingale_difference_array)
    (hlyapunov : input.conditional_lyapunov)
    (hqv : quadraticVariationStabilization) :
    input.residual_variance_formula :=
  (prospective_patt_residual_clt_and_variance_formula_of_lyapunov_array_input
    input finiteQuadraticVariationFormula quadraticVariationStabilization
    hmoments hresidual hqv_transfer hfinite hmartingale hlyapunov hqv).2

/--
Paired prospective PATE/PATT residual CLT and residual variance formula from
generic Lyapunov martingale-array inputs plus explicit finite-QV and
QV-stabilization transfers.
-/
theorem prospective_pate_patt_residual_clt_and_variance_formula_of_lyapunov_array_input
    (pateInput pattInput : ResidualLyapunovArrayCLTVarianceInput)
    (pateFiniteQuadraticVariationFormula
      pateQuadraticVariationStabilization : Prop)
    (pattFiniteQuadraticVariationFormula
      pattQuadraticVariationStabilization : Prop)
    (hpate_moments :
      pateInput.exact_weighted_reuse_moment_limits)
    (hpate_residual : pateInput.residual_moment_regularity)
    (hpate_qv_transfer :
      pateFiniteQuadraticVariationFormula ->
      pateQuadraticVariationStabilization ->
      pateInput.predictable_quadratic_variation_stabilization)
    (hpatt_moments :
      pattInput.exact_weighted_reuse_moment_limits)
    (hpatt_residual : pattInput.residual_moment_regularity)
    (hpatt_qv_transfer :
      pattFiniteQuadraticVariationFormula ->
      pattQuadraticVariationStabilization ->
      pattInput.predictable_quadratic_variation_stabilization)
    (hpate_finite : pateFiniteQuadraticVariationFormula)
    (hpate_martingale : pateInput.martingale_difference_array)
    (hpate_lyapunov : pateInput.conditional_lyapunov)
    (hpate_qv : pateQuadraticVariationStabilization)
    (hpatt_finite : pattFiniteQuadraticVariationFormula)
    (hpatt_martingale : pattInput.martingale_difference_array)
    (hpatt_lyapunov : pattInput.conditional_lyapunov)
    (hpatt_qv : pattQuadraticVariationStabilization) :
    pateInput.residual_clt ∧
      pateInput.residual_variance_formula ∧
      pattInput.residual_clt ∧
      pattInput.residual_variance_formula := by
  have hpate :
      pateInput.residual_clt ∧
        pateInput.residual_variance_formula :=
    prospective_pate_residual_clt_and_variance_formula_of_lyapunov_array_input
      pateInput pateFiniteQuadraticVariationFormula
      pateQuadraticVariationStabilization hpate_moments hpate_residual
      hpate_qv_transfer hpate_finite hpate_martingale hpate_lyapunov
      hpate_qv
  have hpatt :
      pattInput.residual_clt ∧
        pattInput.residual_variance_formula :=
    prospective_patt_residual_clt_and_variance_formula_of_lyapunov_array_input
      pattInput pattFiniteQuadraticVariationFormula
      pattQuadraticVariationStabilization hpatt_moments hpatt_residual
      hpatt_qv_transfer hpatt_finite hpatt_martingale hpatt_lyapunov
      hpatt_qv
  exact ⟨hpate.1, hpate.2, hpatt.1, hpatt.2⟩

/--
Paired prospective residual CLTs from generic Lyapunov martingale-array
inputs.
-/
theorem prospective_pate_patt_residual_clts_of_lyapunov_array_input
    (pateInput pattInput : ResidualLyapunovArrayCLTVarianceInput)
    (pateFiniteQuadraticVariationFormula
      pateQuadraticVariationStabilization : Prop)
    (pattFiniteQuadraticVariationFormula
      pattQuadraticVariationStabilization : Prop)
    (hpate_moments :
      pateInput.exact_weighted_reuse_moment_limits)
    (hpate_residual : pateInput.residual_moment_regularity)
    (hpate_qv_transfer :
      pateFiniteQuadraticVariationFormula ->
      pateQuadraticVariationStabilization ->
      pateInput.predictable_quadratic_variation_stabilization)
    (hpatt_moments :
      pattInput.exact_weighted_reuse_moment_limits)
    (hpatt_residual : pattInput.residual_moment_regularity)
    (hpatt_qv_transfer :
      pattFiniteQuadraticVariationFormula ->
      pattQuadraticVariationStabilization ->
      pattInput.predictable_quadratic_variation_stabilization)
    (hpate_finite : pateFiniteQuadraticVariationFormula)
    (hpate_martingale : pateInput.martingale_difference_array)
    (hpate_lyapunov : pateInput.conditional_lyapunov)
    (hpate_qv : pateQuadraticVariationStabilization)
    (hpatt_finite : pattFiniteQuadraticVariationFormula)
    (hpatt_martingale : pattInput.martingale_difference_array)
    (hpatt_lyapunov : pattInput.conditional_lyapunov)
    (hpatt_qv : pattQuadraticVariationStabilization) :
    pateInput.residual_clt ∧ pattInput.residual_clt := by
  have h :=
    prospective_pate_patt_residual_clt_and_variance_formula_of_lyapunov_array_input
      pateInput pattInput pateFiniteQuadraticVariationFormula
      pateQuadraticVariationStabilization
      pattFiniteQuadraticVariationFormula
      pattQuadraticVariationStabilization hpate_moments hpate_residual
      hpate_qv_transfer hpatt_moments hpatt_residual hpatt_qv_transfer
      hpate_finite hpate_martingale hpate_lyapunov hpate_qv
      hpatt_finite hpatt_martingale hpatt_lyapunov hpatt_qv
  exact ⟨h.1, h.2.2.1⟩

/--
Paired prospective residual variance formulas from generic Lyapunov
martingale-array inputs.
-/
theorem prospective_pate_patt_residual_variance_formulas_of_lyapunov_array_input
    (pateInput pattInput : ResidualLyapunovArrayCLTVarianceInput)
    (pateFiniteQuadraticVariationFormula
      pateQuadraticVariationStabilization : Prop)
    (pattFiniteQuadraticVariationFormula
      pattQuadraticVariationStabilization : Prop)
    (hpate_moments :
      pateInput.exact_weighted_reuse_moment_limits)
    (hpate_residual : pateInput.residual_moment_regularity)
    (hpate_qv_transfer :
      pateFiniteQuadraticVariationFormula ->
      pateQuadraticVariationStabilization ->
      pateInput.predictable_quadratic_variation_stabilization)
    (hpatt_moments :
      pattInput.exact_weighted_reuse_moment_limits)
    (hpatt_residual : pattInput.residual_moment_regularity)
    (hpatt_qv_transfer :
      pattFiniteQuadraticVariationFormula ->
      pattQuadraticVariationStabilization ->
      pattInput.predictable_quadratic_variation_stabilization)
    (hpate_finite : pateFiniteQuadraticVariationFormula)
    (hpate_martingale : pateInput.martingale_difference_array)
    (hpate_lyapunov : pateInput.conditional_lyapunov)
    (hpate_qv : pateQuadraticVariationStabilization)
    (hpatt_finite : pattFiniteQuadraticVariationFormula)
    (hpatt_martingale : pattInput.martingale_difference_array)
    (hpatt_lyapunov : pattInput.conditional_lyapunov)
    (hpatt_qv : pattQuadraticVariationStabilization) :
    pateInput.residual_variance_formula ∧
      pattInput.residual_variance_formula := by
  have h :=
    prospective_pate_patt_residual_clt_and_variance_formula_of_lyapunov_array_input
      pateInput pattInput pateFiniteQuadraticVariationFormula
      pateQuadraticVariationStabilization
      pattFiniteQuadraticVariationFormula
      pattQuadraticVariationStabilization hpate_moments hpate_residual
      hpate_qv_transfer hpatt_moments hpatt_residual hpatt_qv_transfer
      hpate_finite hpate_martingale hpate_lyapunov hpate_qv
      hpatt_finite hpatt_martingale hpatt_lyapunov hpatt_qv
  exact ⟨h.2.1, h.2.2.2⟩

end WDSM
end Matching
end StatInference
