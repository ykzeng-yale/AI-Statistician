import Mathlib.Data.Finset.Basic
import StatInference.Matching.WDSM.ResidualVarianceAlgebra

/-!
# Two-arm residual covariance algebra

The residual variance formulas in PATE and PATT combine residual sums from two
arms.  Conditional mean-zero residuals make cross-arm covariance blocks vanish,
and within-arm diagonal covariance kernels reduce to quadratic variations.
This module records that finite algebra before any probability limit is used.
-/

namespace StatInference
namespace Matching
namespace WDSM

open scoped BigOperators

variable {Treated Control : Type*} [DecidableEq Treated] [DecidableEq Control]

/-- Finite cross-covariance block between two residual arms. -/
noncomputable def crossLinearCovarianceVariation
    (leftSample : Finset Treated)
    (rightSample : Finset Control)
    (leftCoefficient : Treated -> Real)
    (rightCoefficient : Control -> Real)
    (crossCovariance : Treated -> Control -> Real) : Real :=
  ∑ left ∈ leftSample, ∑ right ∈ rightSample,
    leftCoefficient left * rightCoefficient right * crossCovariance left right

/--
Two-arm covariance form with treated-treated, control-control, and the two
cross-arm covariance blocks.
-/
noncomputable def twoArmLinearCovarianceVariation
    (treatedSample : Finset Treated)
    (controlSample : Finset Control)
    (treatedCoefficient : Treated -> Real)
    (controlCoefficient : Control -> Real)
    (treatedCovariance : Treated -> Treated -> Real)
    (controlCovariance : Control -> Control -> Real)
    (treatedControlCovariance : Treated -> Control -> Real)
    (controlTreatedCovariance : Control -> Treated -> Real) : Real :=
  linearCovarianceVariation treatedSample treatedCoefficient
      treatedCovariance +
    linearCovarianceVariation controlSample controlCoefficient
      controlCovariance +
    crossLinearCovarianceVariation treatedSample controlSample
      treatedCoefficient controlCoefficient treatedControlCovariance +
    crossLinearCovarianceVariation controlSample treatedSample
      controlCoefficient treatedCoefficient controlTreatedCovariance

omit [DecidableEq Treated] [DecidableEq Control] in
/-- A cross-covariance block with zero covariance kernel is zero. -/
theorem crossLinearCovarianceVariation_zero
    (leftSample : Finset Treated)
    (rightSample : Finset Control)
    (leftCoefficient : Treated -> Real)
    (rightCoefficient : Control -> Real) :
    crossLinearCovarianceVariation leftSample rightSample
      leftCoefficient rightCoefficient (fun _left _right => 0) = 0 := by
  unfold crossLinearCovarianceVariation
  simp

/--
With diagonal within-arm covariance kernels and zero cross-arm covariance
kernels, the two-arm covariance form equals the sum of treated and control
quadratic variations.
-/
theorem twoArmLinearCovarianceVariation_diagonal_zeroCross_eq_quadraticVariations
    (treatedSample : Finset Treated)
    (controlSample : Finset Control)
    (treatedCoefficient : Treated -> Real)
    (controlCoefficient : Control -> Real)
    (treatedVariance : Treated -> Real)
    (controlVariance : Control -> Real) :
    twoArmLinearCovarianceVariation treatedSample controlSample
        treatedCoefficient controlCoefficient
        (fun left right => if left = right then treatedVariance left else 0)
        (fun left right => if left = right then controlVariance left else 0)
        (fun _treated _control => 0)
        (fun _control _treated => 0) =
      quadraticVariation treatedSample treatedCoefficient treatedVariance +
        quadraticVariation controlSample controlCoefficient controlVariance := by
  unfold twoArmLinearCovarianceVariation
  rw [linearCovarianceVariation_diagonal_eq_quadraticVariation]
  rw [linearCovarianceVariation_diagonal_eq_quadraticVariation]
  rw [crossLinearCovarianceVariation_zero]
  rw [crossLinearCovarianceVariation_zero]
  ring

end WDSM
end Matching
end StatInference
