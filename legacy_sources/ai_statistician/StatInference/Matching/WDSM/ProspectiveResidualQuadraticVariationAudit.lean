import StatInference.Matching.WDSM.PATTVarianceAlgebra

/-!
# Prospective residual quadratic-variation audit

This module specializes the existing finite quadratic-variation algebra to the
prospective PATE and PATT appendix residual variance displays.  It verifies the
finite scalar form of the residual quadratic variation and records the
martingale/Lyapunov probability ingredients as explicit audit bridge inputs.
-/

namespace StatInference
namespace Matching
namespace WDSM

open scoped BigOperators

variable {Treated Control : Type*}

/--
Prospective PATE residual quadratic variation, including the sample-size
normalizer used in the appendix display.
-/
noncomputable def prospectivePATEResidualQuadraticVariation
    (treatedSet : Finset Treated) (controlSet : Finset Control)
    (treatedCoefficient treatedVariance : Treated -> Real)
    (controlCoefficient controlVariance : Control -> Real)
    (denominator normalizer : Real) : Real :=
  normalizer *
    twoArmResidualVariance treatedSet controlSet treatedCoefficient
      treatedVariance controlCoefficient controlVariance denominator

/--
The prospective PATE residual quadratic variation is the normalized sum of the
treated and control arm quadratic variations.
-/
theorem prospectivePATEResidualQuadraticVariation_eq_appendix_sum
    (treatedSet : Finset Treated) (controlSet : Finset Control)
    (treatedCoefficient treatedVariance : Treated -> Real)
    (controlCoefficient controlVariance : Control -> Real)
    (denominator normalizer : Real) :
    prospectivePATEResidualQuadraticVariation treatedSet controlSet
        treatedCoefficient treatedVariance controlCoefficient controlVariance
        denominator normalizer =
      normalizer *
        ((quadraticVariation treatedSet treatedCoefficient treatedVariance +
            quadraticVariation controlSet controlCoefficient controlVariance) /
          denominator ^ 2) := by
  rfl

/--
Expanded finite-sum form of the prospective PATE residual quadratic variation.
-/
theorem prospectivePATEResidualQuadraticVariation_eq_expanded_sum
    (treatedSet : Finset Treated) (controlSet : Finset Control)
    (treatedCoefficient treatedVariance : Treated -> Real)
    (controlCoefficient controlVariance : Control -> Real)
    (denominator normalizer : Real) :
    prospectivePATEResidualQuadraticVariation treatedSet controlSet
        treatedCoefficient treatedVariance controlCoefficient controlVariance
        denominator normalizer =
      normalizer *
        (((∑ treated ∈ treatedSet,
              treatedCoefficient treated ^ 2 * treatedVariance treated) +
            (∑ control ∈ controlSet,
              controlCoefficient control ^ 2 * controlVariance control)) /
          denominator ^ 2) := by
  rfl

/-- Nonnegativity of the prospective PATE residual quadratic variation. -/
theorem prospectivePATEResidualQuadraticVariation_nonneg
    (treatedSet : Finset Treated) (controlSet : Finset Control)
    (treatedCoefficient treatedVariance : Treated -> Real)
    (controlCoefficient controlVariance : Control -> Real)
    (denominator normalizer : Real)
    (hnormalizer : 0 ≤ normalizer)
    (htreatedVariance :
      ∀ treated, treated ∈ treatedSet -> 0 ≤ treatedVariance treated)
    (hcontrolVariance :
      ∀ control, control ∈ controlSet -> 0 ≤ controlVariance control) :
    0 ≤ prospectivePATEResidualQuadraticVariation treatedSet controlSet
      treatedCoefficient treatedVariance controlCoefficient controlVariance
      denominator normalizer := by
  unfold prospectivePATEResidualQuadraticVariation
  exact mul_nonneg hnormalizer
    (twoArmResidualVariance_nonneg treatedSet controlSet treatedCoefficient
      treatedVariance controlCoefficient controlVariance denominator
      htreatedVariance hcontrolVariance)

/--
Prospective PATT residual quadratic variation, including the sample-size
normalizer used in the appendix display.
-/
noncomputable def prospectivePATTResidualQuadraticVariation
    (treatedSet : Finset Treated) (controlSet : Finset Control)
    (treatedCoefficient treatedVariance : Treated -> Real)
    (controlReuseCoefficient controlVariance : Control -> Real)
    (denominator normalizer : Real) : Real :=
  normalizer *
    pattResidualVariance treatedSet controlSet treatedCoefficient
      treatedVariance controlReuseCoefficient controlVariance denominator

/--
The prospective PATT residual quadratic variation is the normalized sum of the
treated direct and matched-control reuse quadratic variations.
-/
theorem prospectivePATTResidualQuadraticVariation_eq_appendix_sum
    (treatedSet : Finset Treated) (controlSet : Finset Control)
    (treatedCoefficient treatedVariance : Treated -> Real)
    (controlReuseCoefficient controlVariance : Control -> Real)
    (denominator normalizer : Real) :
    prospectivePATTResidualQuadraticVariation treatedSet controlSet
        treatedCoefficient treatedVariance controlReuseCoefficient
        controlVariance denominator normalizer =
      normalizer *
        ((quadraticVariation treatedSet treatedCoefficient treatedVariance +
            quadraticVariation controlSet controlReuseCoefficient
              controlVariance) /
          denominator ^ 2) := by
  rfl

/--
Expanded finite-sum form of the prospective PATT residual quadratic variation.
-/
theorem prospectivePATTResidualQuadraticVariation_eq_expanded_sum
    (treatedSet : Finset Treated) (controlSet : Finset Control)
    (treatedCoefficient treatedVariance : Treated -> Real)
    (controlReuseCoefficient controlVariance : Control -> Real)
    (denominator normalizer : Real) :
    prospectivePATTResidualQuadraticVariation treatedSet controlSet
        treatedCoefficient treatedVariance controlReuseCoefficient
        controlVariance denominator normalizer =
      normalizer *
        (((∑ treated ∈ treatedSet,
              treatedCoefficient treated ^ 2 * treatedVariance treated) +
            (∑ control ∈ controlSet,
              controlReuseCoefficient control ^ 2 *
                controlVariance control)) /
          denominator ^ 2) := by
  rfl

/-- Nonnegativity of the prospective PATT residual quadratic variation. -/
theorem prospectivePATTResidualQuadraticVariation_nonneg
    (treatedSet : Finset Treated) (controlSet : Finset Control)
    (treatedCoefficient treatedVariance : Treated -> Real)
    (controlReuseCoefficient controlVariance : Control -> Real)
    (denominator normalizer : Real)
    (hnormalizer : 0 ≤ normalizer)
    (htreatedVariance :
      ∀ treated, treated ∈ treatedSet -> 0 ≤ treatedVariance treated)
    (hcontrolVariance :
      ∀ control, control ∈ controlSet -> 0 ≤ controlVariance control) :
    0 ≤ prospectivePATTResidualQuadraticVariation treatedSet controlSet
      treatedCoefficient treatedVariance controlReuseCoefficient
      controlVariance denominator normalizer := by
  unfold prospectivePATTResidualQuadraticVariation
  exact mul_nonneg hnormalizer
    (pattResidualVariance_nonneg treatedSet controlSet treatedCoefficient
      treatedVariance controlReuseCoefficient controlVariance denominator
      htreatedVariance hcontrolVariance)

/--
Audit bridge for the prospective PATE residual CLT.  The finite QV formula is
checked above; the martingale difference, Lyapunov, and QV-stabilization
claims remain explicit.
-/
structure ProspectivePATEResidualCLTAuditBridge where
  finite_quadratic_variation_formula_verified : Prop
  martingale_difference_array : Prop
  conditional_lyapunov_condition : Prop
  quadratic_variation_stabilization : Prop
  residual_clt : Prop
  bridge :
    finite_quadratic_variation_formula_verified ->
    martingale_difference_array ->
    conditional_lyapunov_condition ->
    quadratic_variation_stabilization ->
    residual_clt

/-- Prospective PATE residual CLT from explicit audit inputs. -/
theorem prospective_pate_residual_clt_of_quadratic_variation_audit
    (b : ProspectivePATEResidualCLTAuditBridge)
    (hfinite : b.finite_quadratic_variation_formula_verified)
    (hmartingale : b.martingale_difference_array)
    (hlyapunov : b.conditional_lyapunov_condition)
    (hqv : b.quadratic_variation_stabilization) :
    b.residual_clt :=
  b.bridge hfinite hmartingale hlyapunov hqv

/--
Audit bridge for the prospective PATT residual CLT.  The finite QV formula is
checked above; the one-sided martingale difference, Lyapunov, and
QV-stabilization claims remain explicit.
-/
structure ProspectivePATTResidualCLTAuditBridge where
  finite_quadratic_variation_formula_verified : Prop
  martingale_difference_array : Prop
  conditional_lyapunov_condition : Prop
  quadratic_variation_stabilization : Prop
  residual_clt : Prop
  bridge :
    finite_quadratic_variation_formula_verified ->
    martingale_difference_array ->
    conditional_lyapunov_condition ->
    quadratic_variation_stabilization ->
    residual_clt

/-- Prospective PATT residual CLT from explicit audit inputs. -/
theorem prospective_patt_residual_clt_of_quadratic_variation_audit
    (b : ProspectivePATTResidualCLTAuditBridge)
    (hfinite : b.finite_quadratic_variation_formula_verified)
    (hmartingale : b.martingale_difference_array)
    (hlyapunov : b.conditional_lyapunov_condition)
    (hqv : b.quadratic_variation_stabilization) :
    b.residual_clt :=
  b.bridge hfinite hmartingale hlyapunov hqv

/--
Paired prospective PATE/PATT residual CLT from explicit quadratic-variation
audit inputs.
-/
theorem prospective_pate_patt_residual_clt_of_quadratic_variation_audit
    (pate : ProspectivePATEResidualCLTAuditBridge)
    (patt : ProspectivePATTResidualCLTAuditBridge)
    (hpate_finite :
      pate.finite_quadratic_variation_formula_verified)
    (hpate_martingale : pate.martingale_difference_array)
    (hpate_lyapunov : pate.conditional_lyapunov_condition)
    (hpate_qv : pate.quadratic_variation_stabilization)
    (hpatt_finite :
      patt.finite_quadratic_variation_formula_verified)
    (hpatt_martingale : patt.martingale_difference_array)
    (hpatt_lyapunov : patt.conditional_lyapunov_condition)
    (hpatt_qv : patt.quadratic_variation_stabilization) :
    pate.residual_clt ∧ patt.residual_clt := by
  constructor
  · exact
      prospective_pate_residual_clt_of_quadratic_variation_audit
        pate hpate_finite hpate_martingale hpate_lyapunov hpate_qv
  · exact
      prospective_patt_residual_clt_of_quadratic_variation_audit
        patt hpatt_finite hpatt_martingale hpatt_lyapunov hpatt_qv

end WDSM
end Matching
end StatInference
