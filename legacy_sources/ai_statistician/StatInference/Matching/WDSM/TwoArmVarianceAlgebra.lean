import StatInference.Matching.WDSM.QuadraticVariation

/-!
# Two-arm residual variance algebra for WDSM

The PATE residual term subtracts the control-arm residual contribution from
the treated-arm residual contribution.  Before any residual CLT or reuse-moment
limit is invoked, the finite diagonal variance algebra reduces this to the sum
of the two arm-level quadratic variations because the control-arm sign is
squared away.
-/

namespace StatInference
namespace Matching
namespace WDSM

variable {Treated Control : Type*}

/-- Denominator-normalized two-arm residual variance skeleton. -/
noncomputable def twoArmResidualVariance
    (treatedSet : Finset Treated) (controlSet : Finset Control)
    (treatedCoefficient treatedVariance : Treated -> Real)
    (controlCoefficient controlVariance : Control -> Real)
    (denominator : Real) : Real :=
  (quadraticVariation treatedSet treatedCoefficient treatedVariance +
      quadraticVariation controlSet controlCoefficient controlVariance) /
    denominator ^ 2

/-- A negative sign on an arm-level residual coefficient does not change its quadratic variation. -/
theorem quadraticVariation_neg_coefficient_eq
    {Unit : Type*} (sample : Finset Unit) (coefficient variance : Unit -> Real) :
    quadraticVariation sample (fun unit => -coefficient unit) variance =
      quadraticVariation sample coefficient variance := by
  have hscale :=
    quadraticVariation_scale sample coefficient variance (-1 : Real)
  simpa using hscale

/--
The signed PATE residual variance skeleton equals the unsigned sum of arm-level
quadratic variations divided by the Hájek denominator squared.
-/
theorem signed_twoArmResidualVariance_eq
    (treatedSet : Finset Treated) (controlSet : Finset Control)
    (treatedCoefficient treatedVariance : Treated -> Real)
    (controlCoefficient controlVariance : Control -> Real)
    (denominator : Real) :
    (quadraticVariation treatedSet treatedCoefficient treatedVariance +
        quadraticVariation controlSet
          (fun control => -controlCoefficient control) controlVariance) /
        denominator ^ 2 =
      twoArmResidualVariance treatedSet controlSet
        treatedCoefficient treatedVariance controlCoefficient controlVariance
        denominator := by
  unfold twoArmResidualVariance
  rw [quadraticVariation_neg_coefficient_eq]

/-- Nonnegativity of the two-arm residual variance skeleton under nonnegative conditional variances. -/
theorem twoArmResidualVariance_nonneg
    (treatedSet : Finset Treated) (controlSet : Finset Control)
    (treatedCoefficient treatedVariance : Treated -> Real)
    (controlCoefficient controlVariance : Control -> Real)
    (denominator : Real)
    (htreatedVariance :
      ∀ treated, treated ∈ treatedSet -> 0 ≤ treatedVariance treated)
    (hcontrolVariance :
      ∀ control, control ∈ controlSet -> 0 ≤ controlVariance control) :
    0 ≤ twoArmResidualVariance treatedSet controlSet
      treatedCoefficient treatedVariance controlCoefficient controlVariance
      denominator := by
  unfold twoArmResidualVariance
  exact div_nonneg
    (add_nonneg
      (quadraticVariation_nonneg treatedSet treatedCoefficient treatedVariance
        htreatedVariance)
      (quadraticVariation_nonneg controlSet controlCoefficient controlVariance
        hcontrolVariance))
    (sq_nonneg denominator)

/-- If both arm coefficient arrays vanish, the two-arm residual variance vanishes. -/
theorem twoArmResidualVariance_eq_zero_of_coefficients_zero
    (treatedSet : Finset Treated) (controlSet : Finset Control)
    (treatedCoefficient treatedVariance : Treated -> Real)
    (controlCoefficient controlVariance : Control -> Real)
    (denominator : Real)
    (htreatedCoefficient :
      ∀ treated, treated ∈ treatedSet -> treatedCoefficient treated = 0)
    (hcontrolCoefficient :
      ∀ control, control ∈ controlSet -> controlCoefficient control = 0) :
    twoArmResidualVariance treatedSet controlSet
      treatedCoefficient treatedVariance controlCoefficient controlVariance
      denominator = 0 := by
  unfold twoArmResidualVariance
  rw [quadraticVariation_zero_of_coeff_zero treatedSet treatedCoefficient
      treatedVariance htreatedCoefficient,
    quadraticVariation_zero_of_coeff_zero controlSet controlCoefficient
      controlVariance hcontrolCoefficient]
  ring

/-- If both arm variance proxies vanish, the two-arm residual variance vanishes. -/
theorem twoArmResidualVariance_eq_zero_of_variances_zero
    (treatedSet : Finset Treated) (controlSet : Finset Control)
    (treatedCoefficient treatedVariance : Treated -> Real)
    (controlCoefficient controlVariance : Control -> Real)
    (denominator : Real)
    (htreatedVariance :
      ∀ treated, treated ∈ treatedSet -> treatedVariance treated = 0)
    (hcontrolVariance :
      ∀ control, control ∈ controlSet -> controlVariance control = 0) :
    twoArmResidualVariance treatedSet controlSet
      treatedCoefficient treatedVariance controlCoefficient controlVariance
      denominator = 0 := by
  unfold twoArmResidualVariance
  rw [quadraticVariation_zero_of_variance_zero treatedSet treatedCoefficient
      treatedVariance htreatedVariance,
    quadraticVariation_zero_of_variance_zero controlSet controlCoefficient
      controlVariance hcontrolVariance]
  ring

end WDSM
end Matching
end StatInference
