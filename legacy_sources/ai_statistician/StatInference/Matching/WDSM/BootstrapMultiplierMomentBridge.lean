import Mathlib.Data.Finset.Basic
import StatInference.Matching.WDSM.BootstrapAlgebra
import StatInference.Matching.WDSM.ResidualVarianceAlgebra
import Mathlib.Tactic.Ring

/-!
# Finite multiplier moment bridge for linearized bootstrap sums

This module proves the finite algebra behind the conditional multiplier
variance calculation.  The stochastic bootstrap proof still needs a genuine
conditional probability theorem, but the exact moment reduction is no longer a
hidden step: a centered multiplier perturbation has second moment equal to the
linear covariance form induced by the multiplier covariance kernel, and this
collapses to the usual centered-square quadratic-variation target under a
diagonal unit-variance multiplier covariance.
-/

namespace StatInference
namespace Matching
namespace WDSM

open scoped BigOperators

variable {Unit Omega : Type*}

/-- Finite expectation with respect to an explicit finite support and mass. -/
noncomputable def finiteExpectation
    (support : Finset Omega) (mass : Omega -> Real)
    (value : Omega -> Real) : Real :=
  ∑ omega ∈ support, mass omega * value omega

/-- Centered multiplier covariance induced by the finite bootstrap law. -/
noncomputable def multiplierCenteredCovariance
    (support : Finset Omega) (mass : Omega -> Real)
    (multiplier : Omega -> Unit -> Real) (left right : Unit) : Real :=
  finiteExpectation support mass
    (fun omega =>
      (multiplier omega left - 1) * (multiplier omega right - 1))

/-- Finite conditional second moment of a multiplier perturbation. -/
noncomputable def multiplierPerturbationSecondMoment
    (support : Finset Omega) (mass : Omega -> Real)
    (sample : Finset Unit) (multiplier : Omega -> Unit -> Real)
    (contribution : Unit -> Real) : Real :=
  finiteExpectation support mass
    (fun omega =>
      (multiplierPerturbation sample (multiplier omega) contribution) ^ 2)

/-- Finite expectation respects pointwise equality. -/
theorem finiteExpectation_congr
    (support : Finset Omega) (mass : Omega -> Real)
    (valueA valueB : Omega -> Real)
    (hvalue : ∀ omega, omega ∈ support -> valueA omega = valueB omega) :
    finiteExpectation support mass valueA =
      finiteExpectation support mass valueB := by
  unfold finiteExpectation
  exact Finset.sum_congr rfl
    (fun omega homega => by rw [hvalue omega homega])

/-- Pull one finite sum through finite expectation. -/
theorem finiteExpectation_sum
    {Alpha : Type*} (support : Finset Omega) (mass : Omega -> Real)
    (indexSet : Finset Alpha) (value : Omega -> Alpha -> Real) :
    finiteExpectation support mass
        (fun omega => ∑ index ∈ indexSet, value omega index) =
      ∑ index ∈ indexSet,
        finiteExpectation support mass (fun omega => value omega index) := by
  unfold finiteExpectation
  calc
    (∑ omega ∈ support,
        mass omega * (∑ index ∈ indexSet, value omega index)) =
        ∑ omega ∈ support, ∑ index ∈ indexSet,
          mass omega * value omega index := by
          exact Finset.sum_congr rfl
            (fun omega _homega => by rw [Finset.mul_sum])
    _ =
        ∑ index ∈ indexSet, ∑ omega ∈ support,
          mass omega * value omega index := by
          rw [Finset.sum_comm]

/--
Pointwise expansion of a centered multiplier perturbation square into a finite
double sum.
-/
theorem multiplierPerturbation_sq_eq_double_sum
    (sample : Finset Unit) (multiplier contribution : Unit -> Real) :
    (multiplierPerturbation sample multiplier contribution) ^ 2 =
      ∑ left ∈ sample, ∑ right ∈ sample,
        contribution left * contribution right *
          ((multiplier left - 1) * (multiplier right - 1)) := by
  unfold multiplierPerturbation
  calc
    (∑ unit ∈ sample, (multiplier unit - 1) * contribution unit) ^ 2 =
        (∑ left ∈ sample, (multiplier left - 1) * contribution left) *
          (∑ right ∈ sample, (multiplier right - 1) *
            contribution right) := by
          ring
    _ =
        ∑ left ∈ sample,
          ((multiplier left - 1) * contribution left) *
            (∑ right ∈ sample,
              (multiplier right - 1) * contribution right) := by
          rw [Finset.sum_mul]
    _ =
        ∑ left ∈ sample, ∑ right ∈ sample,
          ((multiplier left - 1) * contribution left) *
            ((multiplier right - 1) * contribution right) := by
          exact Finset.sum_congr rfl
            (fun left _hleft => by rw [Finset.mul_sum])
    _ =
        ∑ left ∈ sample, ∑ right ∈ sample,
          contribution left * contribution right *
            ((multiplier left - 1) * (multiplier right - 1)) := by
          exact Finset.sum_congr rfl
            (fun left _hleft =>
              Finset.sum_congr rfl
                (fun right _hright => by ring))

/--
Finite multiplier second moment equals the linear covariance form associated
with the centered multiplier covariance kernel.
-/
theorem multiplierPerturbationSecondMoment_eq_linearCovarianceVariation
    (support : Finset Omega) (mass : Omega -> Real)
    (sample : Finset Unit) (multiplier : Omega -> Unit -> Real)
    (contribution : Unit -> Real) :
    multiplierPerturbationSecondMoment support mass sample multiplier
        contribution =
      linearCovarianceVariation sample contribution
        (multiplierCenteredCovariance support mass multiplier) := by
  unfold multiplierPerturbationSecondMoment
  calc
    finiteExpectation support mass
        (fun omega =>
          (multiplierPerturbation sample (multiplier omega)
            contribution) ^ 2) =
        finiteExpectation support mass
          (fun omega =>
            ∑ left ∈ sample, ∑ right ∈ sample,
              contribution left * contribution right *
                ((multiplier omega left - 1) *
                  (multiplier omega right - 1))) := by
          exact finiteExpectation_congr support mass _ _
            (fun omega _homega =>
              multiplierPerturbation_sq_eq_double_sum
                sample (multiplier omega) contribution)
    _ =
        ∑ left ∈ sample, ∑ right ∈ sample,
          finiteExpectation support mass
            (fun omega =>
              contribution left * contribution right *
                ((multiplier omega left - 1) *
                  (multiplier omega right - 1))) := by
          rw [finiteExpectation_sum]
          exact Finset.sum_congr rfl
            (fun left _hleft => by rw [finiteExpectation_sum])
    _ =
        ∑ left ∈ sample, ∑ right ∈ sample,
          contribution left * contribution right *
            finiteExpectation support mass
              (fun omega =>
                (multiplier omega left - 1) *
                  (multiplier omega right - 1)) := by
          exact Finset.sum_congr rfl
            (fun left _hleft =>
              Finset.sum_congr rfl
                (fun right _hright => by
                  unfold finiteExpectation
                  rw [Finset.mul_sum]
                  exact Finset.sum_congr rfl
                    (fun omega _homega => by ring)))
    _ =
        linearCovarianceVariation sample contribution
          (multiplierCenteredCovariance support mass multiplier) := by
          rfl

/--
Usual pairwise multiplier moment assumptions imply the diagonal unit covariance
kernel on the fixed sample.
-/
theorem multiplierCenteredCovariance_eq_diagonal_unit_of_pairwise_moments
    [DecidableEq Unit]
    (support : Finset Omega) (mass : Omega -> Real)
    (sample : Finset Unit) (multiplier : Omega -> Unit -> Real)
    (hdiag :
      ∀ unit ∈ sample,
        multiplierCenteredCovariance support mass multiplier unit unit = 1)
    (hoffdiag :
      ∀ left ∈ sample, ∀ right ∈ sample, left ≠ right ->
        multiplierCenteredCovariance support mass multiplier left right = 0) :
    ∀ left ∈ sample, ∀ right ∈ sample,
      multiplierCenteredCovariance support mass multiplier left right =
        if left = right then 1 else 0 := by
  intro left hleft right hright
  by_cases heq : left = right
  · subst right
    simp [hdiag left hleft]
  · simp [heq, hoffdiag left hleft right hright heq]

/--
If the centered multiplier covariance is diagonal with unit variance on the
sample, the multiplier perturbation second moment is exactly the quadratic
variation of the fixed contribution.
-/
theorem multiplierPerturbationSecondMoment_eq_quadraticVariation_of_diagonal_unit
    [DecidableEq Unit]
    (support : Finset Omega) (mass : Omega -> Real)
    (sample : Finset Unit) (multiplier : Omega -> Unit -> Real)
    (contribution : Unit -> Real)
    (hcov :
      ∀ left ∈ sample, ∀ right ∈ sample,
        multiplierCenteredCovariance support mass multiplier left right =
          if left = right then 1 else 0) :
    multiplierPerturbationSecondMoment support mass sample multiplier
        contribution =
      quadraticVariation sample contribution (fun _unit => 1) := by
  rw [multiplierPerturbationSecondMoment_eq_linearCovarianceVariation]
  have hkernel :
      linearCovarianceVariation sample contribution
          (multiplierCenteredCovariance support mass multiplier) =
        linearCovarianceVariation sample contribution
          (fun left right => if left = right then (1 : Real) else 0) := by
    unfold linearCovarianceVariation
    exact Finset.sum_congr rfl
      (fun left hleft =>
        Finset.sum_congr rfl
          (fun right hright => by rw [hcov left hleft right hright]))
  rw [hkernel]
  exact linearCovarianceVariation_diagonal_eq_quadraticVariation
    sample contribution (fun _unit => 1)

/--
Pairwise multiplier moments imply the quadratic-variation second-moment
formula for a fixed linearized contribution.
-/
theorem multiplierPerturbationSecondMoment_eq_quadraticVariation_of_pairwise_moments
    [DecidableEq Unit]
    (support : Finset Omega) (mass : Omega -> Real)
    (sample : Finset Unit) (multiplier : Omega -> Unit -> Real)
    (contribution : Unit -> Real)
    (hdiag :
      ∀ unit ∈ sample,
        multiplierCenteredCovariance support mass multiplier unit unit = 1)
    (hoffdiag :
      ∀ left ∈ sample, ∀ right ∈ sample, left ≠ right ->
        multiplierCenteredCovariance support mass multiplier left right = 0) :
    multiplierPerturbationSecondMoment support mass sample multiplier
        contribution =
      quadraticVariation sample contribution (fun _unit => 1) :=
  multiplierPerturbationSecondMoment_eq_quadraticVariation_of_diagonal_unit
    support mass sample multiplier contribution
    (multiplierCenteredCovariance_eq_diagonal_unit_of_pairwise_moments
      support mass sample multiplier hdiag hoffdiag)

/--
Under diagonal unit multiplier covariance, the finite multiplier second moment
is the centered-square numerator used by the bootstrap variance target.
-/
theorem multiplierPerturbationSecondMoment_eq_centeredSquareSum_of_diagonal_unit
    [DecidableEq Unit]
    (support : Finset Omega) (mass : Omega -> Real)
    (sample : Finset Unit) (multiplier : Omega -> Unit -> Real)
    (contribution weight : Unit -> Real) (target : Real)
    (hcov :
      ∀ left ∈ sample, ∀ right ∈ sample,
        multiplierCenteredCovariance support mass multiplier left right =
          if left = right then 1 else 0) :
    multiplierPerturbationSecondMoment support mass sample multiplier
        (fun unit => contribution unit - target * weight unit) =
      centeredSquareSum sample contribution weight target := by
  rw [
    multiplierPerturbationSecondMoment_eq_quadraticVariation_of_diagonal_unit
      support mass sample multiplier
        (fun unit => contribution unit - target * weight unit) hcov]
  unfold quadraticVariation centeredSquareSum
  exact Finset.sum_congr rfl
    (fun unit _hunit => by ring)

/--
Pairwise multiplier moments imply the centered-square second-moment formula
used by the bootstrap variance target.
-/
theorem multiplierPerturbationSecondMoment_eq_centeredSquareSum_of_pairwise_moments
    [DecidableEq Unit]
    (support : Finset Omega) (mass : Omega -> Real)
    (sample : Finset Unit) (multiplier : Omega -> Unit -> Real)
    (contribution weight : Unit -> Real) (target : Real)
    (hdiag :
      ∀ unit ∈ sample,
        multiplierCenteredCovariance support mass multiplier unit unit = 1)
    (hoffdiag :
      ∀ left ∈ sample, ∀ right ∈ sample, left ≠ right ->
        multiplierCenteredCovariance support mass multiplier left right = 0) :
    multiplierPerturbationSecondMoment support mass sample multiplier
        (fun unit => contribution unit - target * weight unit) =
      centeredSquareSum sample contribution weight target :=
  multiplierPerturbationSecondMoment_eq_centeredSquareSum_of_diagonal_unit
    support mass sample multiplier contribution weight target
    (multiplierCenteredCovariance_eq_diagonal_unit_of_pairwise_moments
      support mass sample multiplier hdiag hoffdiag)

/--
Normalized version matching the deterministic numerator of
`bootstrapCenteredVarianceTarget`.
-/
theorem multiplierPerturbationSecondMoment_normalized_eq_bootstrapCenteredVarianceTarget
    [DecidableEq Unit]
    (support : Finset Omega) (mass : Omega -> Real)
    (sample : Finset Unit) (multiplier : Omega -> Unit -> Real)
    (contribution weight : Unit -> Real) (target denominator normalizer : Real)
    (hcov :
      ∀ left ∈ sample, ∀ right ∈ sample,
        multiplierCenteredCovariance support mass multiplier left right =
          if left = right then 1 else 0) :
    (1 / denominator ^ 2) * (1 / normalizer) *
        multiplierPerturbationSecondMoment support mass sample multiplier
          (fun unit => contribution unit - target * weight unit) =
      bootstrapCenteredVarianceTarget sample contribution weight target
        denominator normalizer := by
  rw [
    multiplierPerturbationSecondMoment_eq_centeredSquareSum_of_diagonal_unit
      support mass sample multiplier contribution weight target hcov]
  rfl

/--
Pairwise multiplier moments imply the normalized finite variance-target
identity consumed by the WDSM bootstrap bridge.
-/
theorem multiplierPerturbationSecondMoment_normalized_eq_bootstrapCenteredVarianceTarget_of_pairwise_moments
    [DecidableEq Unit]
    (support : Finset Omega) (mass : Omega -> Real)
    (sample : Finset Unit) (multiplier : Omega -> Unit -> Real)
    (contribution weight : Unit -> Real) (target denominator normalizer : Real)
    (hdiag :
      ∀ unit ∈ sample,
        multiplierCenteredCovariance support mass multiplier unit unit = 1)
    (hoffdiag :
      ∀ left ∈ sample, ∀ right ∈ sample, left ≠ right ->
        multiplierCenteredCovariance support mass multiplier left right = 0) :
    (1 / denominator ^ 2) * (1 / normalizer) *
        multiplierPerturbationSecondMoment support mass sample multiplier
          (fun unit => contribution unit - target * weight unit) =
      bootstrapCenteredVarianceTarget sample contribution weight target
        denominator normalizer :=
  multiplierPerturbationSecondMoment_normalized_eq_bootstrapCenteredVarianceTarget
    support mass sample multiplier contribution weight target denominator
    normalizer
    (multiplierCenteredCovariance_eq_diagonal_unit_of_pairwise_moments
      support mass sample multiplier hdiag hoffdiag)

end WDSM
end Matching
end StatInference
