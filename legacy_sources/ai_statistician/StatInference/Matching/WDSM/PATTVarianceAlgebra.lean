import StatInference.Matching.WDSM.QuadraticVariation
import StatInference.Matching.WDSM.TwoArmVarianceAlgebra
import StatInference.Matching.WDSM.VarianceAlgebra

/-!
# One-sided PATT residual variance algebra for WDSM

The PATT residual term has a one-sided structure: a direct treated residual
contribution minus a matched-control residual contribution, normalized by the
treated Hájek denominator.  This module records the finite quadratic-variation
algebra behind the appendix PATT residual variance formulas before any
conditional variance or reuse-moment limit is invoked.
-/

namespace StatInference
namespace Matching
namespace WDSM

variable {Treated Control : Type*}

/-- Denominator-normalized one-sided PATT residual variance skeleton. -/
noncomputable def pattResidualVariance
    (treatedSet : Finset Treated) (controlSet : Finset Control)
    (treatedCoefficient treatedVariance : Treated -> Real)
    (controlReuseCoefficient controlVariance : Control -> Real)
    (denominator : Real) : Real :=
  (quadraticVariation treatedSet treatedCoefficient treatedVariance +
      quadraticVariation controlSet controlReuseCoefficient controlVariance) /
    denominator ^ 2

/--
The signed one-sided PATT residual variance skeleton equals the unsigned sum of
treated and matched-control quadratic variations divided by the denominator
squared.
-/
theorem signed_pattResidualVariance_eq
    (treatedSet : Finset Treated) (controlSet : Finset Control)
    (treatedCoefficient treatedVariance : Treated -> Real)
    (controlReuseCoefficient controlVariance : Control -> Real)
    (denominator : Real) :
    (quadraticVariation treatedSet treatedCoefficient treatedVariance +
        quadraticVariation controlSet
          (fun control => -controlReuseCoefficient control) controlVariance) /
        denominator ^ 2 =
      pattResidualVariance treatedSet controlSet treatedCoefficient
        treatedVariance controlReuseCoefficient controlVariance denominator := by
  unfold pattResidualVariance
  rw [quadraticVariation_neg_coefficient_eq]

/-- Nonnegativity of the one-sided PATT residual variance skeleton. -/
theorem pattResidualVariance_nonneg
    (treatedSet : Finset Treated) (controlSet : Finset Control)
    (treatedCoefficient treatedVariance : Treated -> Real)
    (controlReuseCoefficient controlVariance : Control -> Real)
    (denominator : Real)
    (htreatedVariance :
      ∀ treated, treated ∈ treatedSet -> 0 ≤ treatedVariance treated)
    (hcontrolVariance :
      ∀ control, control ∈ controlSet -> 0 ≤ controlVariance control) :
    0 ≤ pattResidualVariance treatedSet controlSet treatedCoefficient
      treatedVariance controlReuseCoefficient controlVariance denominator := by
  unfold pattResidualVariance
  exact div_nonneg
    (add_nonneg
      (quadraticVariation_nonneg treatedSet treatedCoefficient treatedVariance
        htreatedVariance)
      (quadraticVariation_nonneg controlSet controlReuseCoefficient
        controlVariance hcontrolVariance))
    (sq_nonneg denominator)

/--
If both treated and matched-control residual coefficients vanish on their
sample sets, the one-sided PATT residual variance skeleton is zero.
-/
theorem pattResidualVariance_eq_zero_of_coefficients_zero
    (treatedSet : Finset Treated) (controlSet : Finset Control)
    (treatedCoefficient treatedVariance : Treated -> Real)
    (controlReuseCoefficient controlVariance : Control -> Real)
    (denominator : Real)
    (htreatedZero :
      ∀ treated, treated ∈ treatedSet -> treatedCoefficient treated = 0)
    (hcontrolZero :
      ∀ control, control ∈ controlSet -> controlReuseCoefficient control = 0) :
    pattResidualVariance treatedSet controlSet treatedCoefficient
      treatedVariance controlReuseCoefficient controlVariance denominator = 0 := by
  unfold pattResidualVariance
  rw [quadraticVariation_zero_of_coeff_zero
    treatedSet treatedCoefficient treatedVariance htreatedZero]
  rw [quadraticVariation_zero_of_coeff_zero
    controlSet controlReuseCoefficient controlVariance hcontrolZero]
  ring

/--
With positive variance proxies and nonzero denominator, the one-sided PATT
residual variance skeleton is zero exactly when both treated and matched-control
residual coefficients vanish on their sample sets.
-/
theorem pattResidualVariance_eq_zero_iff_coefficients_zero_of_variance_pos
    (treatedSet : Finset Treated) (controlSet : Finset Control)
    (treatedCoefficient treatedVariance : Treated -> Real)
    (controlReuseCoefficient controlVariance : Control -> Real)
    (denominator : Real)
    (htreatedVariance :
      ∀ treated, treated ∈ treatedSet -> 0 < treatedVariance treated)
    (hcontrolVariance :
      ∀ control, control ∈ controlSet -> 0 < controlVariance control)
    (hdenominator : denominator ≠ 0) :
    pattResidualVariance treatedSet controlSet treatedCoefficient
        treatedVariance controlReuseCoefficient controlVariance denominator = 0 ↔
      (∀ treated, treated ∈ treatedSet -> treatedCoefficient treated = 0) ∧
        (∀ control, control ∈ controlSet ->
          controlReuseCoefficient control = 0) := by
  constructor
  · intro hzero
    unfold pattResidualVariance at hzero
    have hnumerator :
        quadraticVariation treatedSet treatedCoefficient treatedVariance +
          quadraticVariation controlSet controlReuseCoefficient
            controlVariance = 0 := by
      rcases div_eq_zero_iff.mp hzero with hnumerator |
        hdenominator_sq_zero
      · exact hnumerator
      · exact False.elim ((pow_ne_zero 2 hdenominator)
          hdenominator_sq_zero)
    have htreatedNonneg :
        0 ≤ quadraticVariation treatedSet treatedCoefficient
          treatedVariance :=
      quadraticVariation_nonneg treatedSet treatedCoefficient
        treatedVariance (fun treated htreated =>
          le_of_lt (htreatedVariance treated htreated))
    have hcontrolNonneg :
        0 ≤ quadraticVariation controlSet controlReuseCoefficient
          controlVariance :=
      quadraticVariation_nonneg controlSet controlReuseCoefficient
        controlVariance (fun control hcontrol =>
          le_of_lt (hcontrolVariance control hcontrol))
    have htreatedZero :
        quadraticVariation treatedSet treatedCoefficient treatedVariance =
          0 := by
      linarith
    have hcontrolZero :
        quadraticVariation controlSet controlReuseCoefficient
          controlVariance = 0 := by
      linarith
    constructor
    · exact
        (quadraticVariation_eq_zero_iff_coeff_zero_of_variance_pos
          treatedSet treatedCoefficient treatedVariance htreatedVariance).mp
          htreatedZero
    · exact
        (quadraticVariation_eq_zero_iff_coeff_zero_of_variance_pos
          controlSet controlReuseCoefficient controlVariance
          hcontrolVariance).mp hcontrolZero
  · intro hcoefficients
    exact pattResidualVariance_eq_zero_of_coefficients_zero
      treatedSet controlSet treatedCoefficient treatedVariance
      controlReuseCoefficient controlVariance denominator hcoefficients.1
      hcoefficients.2

/--
With positive variance proxies and nonzero denominator, a nonzero treated
residual coefficient makes the one-sided PATT residual variance positive.
-/
theorem pattResidualVariance_pos_of_exists_treated_coeff_ne_zero
    (treatedSet : Finset Treated) (controlSet : Finset Control)
    (treatedCoefficient treatedVariance : Treated -> Real)
    (controlReuseCoefficient controlVariance : Control -> Real)
    (denominator : Real)
    (htreatedVariance :
      ∀ treated, treated ∈ treatedSet -> 0 < treatedVariance treated)
    (hcontrolVariance :
      ∀ control, control ∈ controlSet -> 0 < controlVariance control)
    (hdenominator : denominator ≠ 0)
    (hexists :
      ∃ treated, treated ∈ treatedSet ∧ treatedCoefficient treated ≠ 0) :
    0 < pattResidualVariance treatedSet controlSet treatedCoefficient
      treatedVariance controlReuseCoefficient controlVariance denominator := by
  unfold pattResidualVariance
  exact div_pos
    (add_pos_of_pos_of_nonneg
      (quadraticVariation_pos_of_exists_coeff_ne_zero_of_variance_pos
        treatedSet treatedCoefficient treatedVariance htreatedVariance hexists)
      (quadraticVariation_nonneg controlSet controlReuseCoefficient
        controlVariance (fun control hcontrol =>
          le_of_lt (hcontrolVariance control hcontrol))))
    (sq_pos_of_ne_zero hdenominator)

/--
With positive variance proxies and nonzero denominator, a nonzero matched-control
reuse coefficient makes the one-sided PATT residual variance positive.
-/
theorem pattResidualVariance_pos_of_exists_control_coeff_ne_zero
    (treatedSet : Finset Treated) (controlSet : Finset Control)
    (treatedCoefficient treatedVariance : Treated -> Real)
    (controlReuseCoefficient controlVariance : Control -> Real)
    (denominator : Real)
    (htreatedVariance :
      ∀ treated, treated ∈ treatedSet -> 0 < treatedVariance treated)
    (hcontrolVariance :
      ∀ control, control ∈ controlSet -> 0 < controlVariance control)
    (hdenominator : denominator ≠ 0)
    (hexists :
      ∃ control, control ∈ controlSet ∧
        controlReuseCoefficient control ≠ 0) :
    0 < pattResidualVariance treatedSet controlSet treatedCoefficient
      treatedVariance controlReuseCoefficient controlVariance denominator := by
  unfold pattResidualVariance
  exact div_pos
    (add_pos_of_nonneg_of_pos
      (quadraticVariation_nonneg treatedSet treatedCoefficient
        treatedVariance (fun treated htreated =>
          le_of_lt (htreatedVariance treated htreated)))
      (quadraticVariation_pos_of_exists_coeff_ne_zero_of_variance_pos
        controlSet controlReuseCoefficient controlVariance
        hcontrolVariance hexists))
    (sq_pos_of_ne_zero hdenominator)

/--
Scalar skeleton of the PATT residual variance formula:
treated direct variance plus matched-control reuse variance, each weighted by
its sample share and normalized by the treated Hájek denominator squared.
-/
noncomputable def pattWeightedResidualVariance
    (denominator treatedShare controlShare treatedDirectVariance
      matchedControlVariance : Real) : Real :=
  (treatedShare * treatedDirectVariance +
      controlShare * matchedControlVariance) / denominator ^ 2

/-- PATT scalar residual variance is the generic two-component weighted residual target. -/
theorem pattWeightedResidualVariance_eq_twoArmWeightedResidualVariance
    (denominator treatedShare controlShare treatedDirectVariance
      matchedControlVariance : Real) :
    pattWeightedResidualVariance denominator treatedShare controlShare
        treatedDirectVariance matchedControlVariance =
      twoArmWeightedResidualVariance denominator treatedShare controlShare
        treatedDirectVariance matchedControlVariance := by
  rfl

/-- Equivalent inverse-square display for the scalar PATT residual variance target. -/
theorem pattWeightedResidualVariance_eq_inv_sq_mul
    (denominator treatedShare controlShare treatedDirectVariance
      matchedControlVariance : Real) :
    pattWeightedResidualVariance denominator treatedShare controlShare
        treatedDirectVariance matchedControlVariance =
      (1 / denominator ^ 2) *
        (treatedShare * treatedDirectVariance +
          controlShare * matchedControlVariance) := by
  rw [pattWeightedResidualVariance_eq_twoArmWeightedResidualVariance]
  exact twoArmWeightedResidualVariance_eq_inv_sq_mul denominator treatedShare
    controlShare treatedDirectVariance matchedControlVariance

/-- Nonnegativity of the scalar PATT residual variance target. -/
theorem pattWeightedResidualVariance_nonneg
    (denominator treatedShare controlShare treatedDirectVariance
      matchedControlVariance : Real)
    (htreatedShare : 0 ≤ treatedShare)
    (hcontrolShare : 0 ≤ controlShare)
    (htreatedVariance : 0 ≤ treatedDirectVariance)
    (hcontrolVariance : 0 ≤ matchedControlVariance) :
    0 ≤ pattWeightedResidualVariance denominator treatedShare controlShare
      treatedDirectVariance matchedControlVariance := by
  rw [pattWeightedResidualVariance_eq_twoArmWeightedResidualVariance]
  exact twoArmWeightedResidualVariance_nonneg denominator treatedShare
    controlShare treatedDirectVariance matchedControlVariance htreatedShare
    hcontrolShare htreatedVariance hcontrolVariance

/--
A positive treated direct residual variance contribution makes the scalar PATT
residual variance target positive.
-/
theorem pattWeightedResidualVariance_pos_of_treated_pos
    (denominator treatedShare controlShare treatedDirectVariance
      matchedControlVariance : Real)
    (hdenominator : denominator ≠ 0)
    (htreatedShare : 0 < treatedShare)
    (hcontrolShare : 0 ≤ controlShare)
    (htreatedVariance : 0 < treatedDirectVariance)
    (hcontrolVariance : 0 ≤ matchedControlVariance) :
    0 < pattWeightedResidualVariance denominator treatedShare controlShare
      treatedDirectVariance matchedControlVariance := by
  rw [pattWeightedResidualVariance_eq_twoArmWeightedResidualVariance]
  exact twoArmWeightedResidualVariance_pos_of_treated_pos denominator
    treatedShare controlShare treatedDirectVariance matchedControlVariance
    hdenominator htreatedShare hcontrolShare htreatedVariance
    hcontrolVariance

/--
A positive matched-control reuse variance contribution makes the scalar PATT
residual variance target positive.
-/
theorem pattWeightedResidualVariance_pos_of_control_pos
    (denominator treatedShare controlShare treatedDirectVariance
      matchedControlVariance : Real)
    (hdenominator : denominator ≠ 0)
    (htreatedShare : 0 ≤ treatedShare)
    (hcontrolShare : 0 < controlShare)
    (htreatedVariance : 0 ≤ treatedDirectVariance)
    (hcontrolVariance : 0 < matchedControlVariance) :
    0 < pattWeightedResidualVariance denominator treatedShare controlShare
      treatedDirectVariance matchedControlVariance := by
  rw [pattWeightedResidualVariance_eq_twoArmWeightedResidualVariance]
  exact twoArmWeightedResidualVariance_pos_of_control_pos denominator
    treatedShare controlShare treatedDirectVariance matchedControlVariance
    hdenominator htreatedShare hcontrolShare htreatedVariance
    hcontrolVariance

/--
With positive scalar PATT shares, nonnegative variance components, and nonzero
denominator, zero scalar PATT residual variance is equivalent to zero treated
direct and matched-control variance components.
-/
theorem pattWeightedResidualVariance_eq_zero_iff_components_zero_of_shares_pos
    (denominator treatedShare controlShare treatedDirectVariance
      matchedControlVariance : Real)
    (hdenominator : denominator ≠ 0)
    (htreatedShare : 0 < treatedShare)
    (hcontrolShare : 0 < controlShare)
    (htreatedVariance : 0 ≤ treatedDirectVariance)
    (hcontrolVariance : 0 ≤ matchedControlVariance) :
    pattWeightedResidualVariance denominator treatedShare controlShare
        treatedDirectVariance matchedControlVariance = 0 ↔
      treatedDirectVariance = 0 ∧ matchedControlVariance = 0 := by
  rw [pattWeightedResidualVariance_eq_twoArmWeightedResidualVariance]
  exact
    twoArmWeightedResidualVariance_eq_zero_iff_arm_variances_zero_of_shares_pos
      denominator treatedShare controlShare treatedDirectVariance
      matchedControlVariance hdenominator htreatedShare hcontrolShare
      htreatedVariance hcontrolVariance

end WDSM
end Matching
end StatInference
