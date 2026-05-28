import Mathlib.Data.Finset.Basic
import StatInference.Matching.WDSM.BootstrapMultinomialMomentBridge
import Mathlib.Tactic.Ring

/-!
# Multinomial count-moment bridge

`BootstrapMultinomialMomentBridge` consumes the centered count covariance
kernel `delta_ij - 1 / n`.  This file moves one step upstream: it proves that
the centered covariance kernel follows from the raw count moments delivered by
an equal-probability multinomial count vector:

* `E[m_i] = 1`,
* `E[m_i m_i] = 2 - 1 / n`,
* `E[m_i m_j] = 1 - 1 / n` for `i != j`.

The remaining probability task is therefore reduced to proving or importing
those raw multinomial count moments for the concrete resampling law.
-/

namespace StatInference
namespace Matching
namespace WDSM

variable {Unit Omega : Type*}

/--
Finite expectation of `(A - 1) * (B - 1)` in terms of raw first and second
moments.
-/
theorem finiteExpectation_centered_one_mul_centered_one_eq
    (support : Finset Omega) (mass : Omega -> Real)
    (valueA valueB : Omega -> Real) :
    finiteExpectation support mass
        (fun omega => (valueA omega - 1) * (valueB omega - 1)) =
      finiteExpectation support mass (fun omega => valueA omega * valueB omega) -
        finiteExpectation support mass valueA -
        finiteExpectation support mass valueB +
        finiteExpectation support mass (fun _omega => (1 : Real)) := by
  unfold finiteExpectation
  calc
    (∑ omega ∈ support,
        mass omega * ((valueA omega - 1) * (valueB omega - 1))) =
        ∑ omega ∈ support,
          (((mass omega * (valueA omega * valueB omega) -
              mass omega * valueA omega) -
              mass omega * valueB omega) +
              mass omega * 1) := by
          exact Finset.sum_congr rfl
            (fun omega _homega => by ring)
    _ =
        ((∑ omega ∈ support, mass omega * (valueA omega * valueB omega)) -
            (∑ omega ∈ support, mass omega * valueA omega)) -
          (∑ omega ∈ support, mass omega * valueB omega) +
          (∑ omega ∈ support, mass omega * 1) := by
          rw [Finset.sum_add_distrib]
          rw [Finset.sum_sub_distrib]
          rw [Finset.sum_sub_distrib]

/--
Raw equal-probability multinomial count moments imply the centered covariance
kernel `delta_ij - 1 / n`.
-/
theorem multiplierCenteredCovariance_eq_multinomialCenteredCovarianceKernel_of_raw_count_moments
    [DecidableEq Unit]
    (support : Finset Omega) (mass : Omega -> Real)
    (sample : Finset Unit) (multiplier : Omega -> Unit -> Real)
    (sampleSize : Real)
    (hmass :
      finiteExpectation support mass (fun _omega => (1 : Real)) = 1)
    (hmean :
      ∀ unit ∈ sample,
        finiteExpectation support mass (fun omega => multiplier omega unit) = 1)
    (hcross :
      ∀ left ∈ sample, ∀ right ∈ sample,
        finiteExpectation support mass
            (fun omega => multiplier omega left * multiplier omega right) =
          if left = right then 2 - 1 / sampleSize else 1 - 1 / sampleSize) :
    ∀ left ∈ sample, ∀ right ∈ sample,
      multiplierCenteredCovariance support mass multiplier left right =
        multinomialCenteredCovarianceKernel sampleSize left right := by
  intro left hleft right hright
  unfold multiplierCenteredCovariance
  rw [finiteExpectation_centered_one_mul_centered_one_eq]
  rw [hcross left hleft right hright]
  rw [hmean left hleft]
  rw [hmean right hright]
  rw [hmass]
  by_cases heq : left = right
  · simp [multinomialCenteredCovarianceKernel, heq]
    ring
  · simp [multinomialCenteredCovarianceKernel, heq]

/--
Count-moment version of the multinomial centered-square identity.  It consumes
raw count moments rather than a pre-proved centered covariance kernel.
-/
theorem multiplierPerturbationSecondMoment_eq_centeredSquareSum_of_multinomial_count_moments_of_base_ratio
    [DecidableEq Unit]
    (support : Finset Omega) (mass : Omega -> Real)
    (sample : Finset Unit) (multiplier : Omega -> Unit -> Real)
    (contribution weight : Unit -> Real) (target sampleSize : Real)
    (hmass :
      finiteExpectation support mass (fun _omega => (1 : Real)) = 1)
    (hmean :
      ∀ unit ∈ sample,
        finiteExpectation support mass (fun omega => multiplier omega unit) = 1)
    (hcross :
      ∀ left ∈ sample, ∀ right ∈ sample,
        finiteExpectation support mass
            (fun omega => multiplier omega left * multiplier omega right) =
          if left = right then 2 - 1 / sampleSize else 1 - 1 / sampleSize)
    (hbase :
      baseLinearizedSum sample contribution =
        target * baseLinearizedSum sample weight) :
    multiplierPerturbationSecondMoment support mass sample multiplier
        (fun unit => contribution unit - target * weight unit) =
      centeredSquareSum sample contribution weight target :=
  multiplierPerturbationSecondMoment_eq_centeredSquareSum_of_multinomial_covariance_of_base_ratio
    support mass sample multiplier contribution weight target sampleSize
    (multiplierCenteredCovariance_eq_multinomialCenteredCovarianceKernel_of_raw_count_moments
      support mass sample multiplier sampleSize hmass hmean hcross)
    hbase

/--
Normalized count-moment version matching `bootstrapCenteredVarianceTarget`.
-/
theorem multiplierPerturbationSecondMoment_normalized_eq_bootstrapCenteredVarianceTarget_of_multinomial_count_moments_of_base_ratio
    [DecidableEq Unit]
    (support : Finset Omega) (mass : Omega -> Real)
    (sample : Finset Unit) (multiplier : Omega -> Unit -> Real)
    (contribution weight : Unit -> Real)
    (target denominator normalizer sampleSize : Real)
    (hmass :
      finiteExpectation support mass (fun _omega => (1 : Real)) = 1)
    (hmean :
      ∀ unit ∈ sample,
        finiteExpectation support mass (fun omega => multiplier omega unit) = 1)
    (hcross :
      ∀ left ∈ sample, ∀ right ∈ sample,
        finiteExpectation support mass
            (fun omega => multiplier omega left * multiplier omega right) =
          if left = right then 2 - 1 / sampleSize else 1 - 1 / sampleSize)
    (hbase :
      baseLinearizedSum sample contribution =
        target * baseLinearizedSum sample weight) :
    (1 / denominator ^ 2) * (1 / normalizer) *
        multiplierPerturbationSecondMoment support mass sample multiplier
          (fun unit => contribution unit - target * weight unit) =
      bootstrapCenteredVarianceTarget sample contribution weight target
        denominator normalizer :=
  multiplierPerturbationSecondMoment_normalized_eq_bootstrapCenteredVarianceTarget_of_multinomial_covariance_of_base_ratio
    support mass sample multiplier contribution weight target denominator
    normalizer sampleSize
    (multiplierCenteredCovariance_eq_multinomialCenteredCovarianceKernel_of_raw_count_moments
      support mass sample multiplier sampleSize hmass hmean hcross)
    hbase

end WDSM
end Matching
end StatInference
