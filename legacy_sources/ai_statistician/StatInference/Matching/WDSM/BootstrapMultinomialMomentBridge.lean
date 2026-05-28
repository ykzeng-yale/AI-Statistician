import Mathlib.Data.Finset.Basic
import StatInference.Matching.WDSM.BootstrapMultiplierMomentBridge
import Mathlib.Tactic.Ring

/-!
# Multinomial multiplier covariance bridge

The main WDSM bootstrap algorithm draws multinomial counts
`m_i^*` with equal cell probabilities.  Conditionally on the original sample,
the centered count covariance has the finite kernel `delta_ij - 1 / n`.

This module proves the deterministic algebra for that kernel.  The
multinomial covariance target equals the diagonal centered-square target minus
a finite-population centering correction.  When the centered linearized
contribution has exact zero finite sum, the correction vanishes and the
multinomial target agrees with `bootstrapCenteredVarianceTarget`.
-/

namespace StatInference
namespace Matching
namespace WDSM

open scoped BigOperators

variable {Unit Omega : Type*}

/-- Equal-probability multinomial centered count covariance kernel. -/
noncomputable def multinomialCenteredCovarianceKernel
    [DecidableEq Unit] (sampleSize : Real) (left right : Unit) : Real :=
  (if left = right then (1 : Real) else 0) - 1 / sampleSize

/-- Product of two finite linearized sums as a finite double sum. -/
theorem baseLinearizedSum_mul_baseLinearizedSum_eq_double_sum
    (sample : Finset Unit) (contributionA contributionB : Unit -> Real) :
    baseLinearizedSum sample contributionA *
        baseLinearizedSum sample contributionB =
      ∑ left ∈ sample, ∑ right ∈ sample,
        contributionA left * contributionB right := by
  unfold baseLinearizedSum
  calc
    (∑ left ∈ sample, contributionA left) *
        (∑ right ∈ sample, contributionB right) =
        ∑ left ∈ sample,
          contributionA left *
            (∑ right ∈ sample, contributionB right) := by
          rw [Finset.sum_mul]
    _ =
        ∑ left ∈ sample, ∑ right ∈ sample,
          contributionA left * contributionB right := by
          exact Finset.sum_congr rfl
            (fun left _hleft => by rw [Finset.mul_sum])

/-- Squared finite linearized sum as a finite double sum. -/
theorem baseLinearizedSum_sq_eq_double_sum
    (sample : Finset Unit) (contribution : Unit -> Real) :
    (baseLinearizedSum sample contribution) ^ 2 =
      ∑ left ∈ sample, ∑ right ∈ sample,
        contribution left * contribution right := by
  calc
    (baseLinearizedSum sample contribution) ^ 2 =
        baseLinearizedSum sample contribution *
          baseLinearizedSum sample contribution := by
          ring
    _ =
        ∑ left ∈ sample, ∑ right ∈ sample,
          contribution left * contribution right := by
          exact baseLinearizedSum_mul_baseLinearizedSum_eq_double_sum
            sample contribution contribution

/--
The covariance form under the equal-probability multinomial count kernel is
the diagonal quadratic variation minus the finite-population centering
correction.
-/
theorem linearCovarianceVariation_multinomialCenteredCovarianceKernel_eq
    [DecidableEq Unit]
    (sample : Finset Unit) (contribution : Unit -> Real)
    (sampleSize : Real) :
    linearCovarianceVariation sample contribution
        (multinomialCenteredCovarianceKernel sampleSize) =
      quadraticVariation sample contribution (fun _unit => 1) -
        (1 / sampleSize) * (baseLinearizedSum sample contribution) ^ 2 := by
  unfold linearCovarianceVariation multinomialCenteredCovarianceKernel
  calc
    (∑ left ∈ sample, ∑ right ∈ sample,
        contribution left * contribution right *
          ((if left = right then (1 : Real) else 0) - 1 / sampleSize)) =
        (∑ left ∈ sample, ∑ right ∈ sample,
          contribution left * contribution right *
            (if left = right then (1 : Real) else 0)) -
        (∑ left ∈ sample, ∑ right ∈ sample,
          (1 / sampleSize) *
            (contribution left * contribution right)) := by
          calc
            (∑ left ∈ sample, ∑ right ∈ sample,
                contribution left * contribution right *
                  ((if left = right then (1 : Real) else 0) -
                    1 / sampleSize)) =
                ∑ left ∈ sample, ∑ right ∈ sample,
                  (contribution left * contribution right *
                    (if left = right then (1 : Real) else 0) -
                    (1 / sampleSize) *
                      (contribution left * contribution right)) := by
                  exact Finset.sum_congr rfl
                    (fun left _hleft =>
                      Finset.sum_congr rfl
                        (fun right _hright => by ring))
            _ =
                ∑ left ∈ sample,
                  ((∑ right ∈ sample,
                    contribution left * contribution right *
                      (if left = right then (1 : Real) else 0)) -
                    (∑ right ∈ sample,
                      (1 / sampleSize) *
                        (contribution left * contribution right))) := by
                  exact Finset.sum_congr rfl
                    (fun left _hleft => by rw [Finset.sum_sub_distrib])
            _ =
                (∑ left ∈ sample, ∑ right ∈ sample,
                  contribution left * contribution right *
                    (if left = right then (1 : Real) else 0)) -
                (∑ left ∈ sample, ∑ right ∈ sample,
                  (1 / sampleSize) *
                    (contribution left * contribution right)) := by
                  rw [Finset.sum_sub_distrib]
    _ =
        quadraticVariation sample contribution (fun _unit => 1) -
        (1 / sampleSize) *
          (∑ left ∈ sample, ∑ right ∈ sample,
            contribution left * contribution right) := by
          have hdiag :
              (∑ left ∈ sample, ∑ right ∈ sample,
                contribution left * contribution right *
                  (if left = right then (1 : Real) else 0)) =
                quadraticVariation sample contribution (fun _unit => 1) := by
            rw [← linearCovarianceVariation_diagonal_eq_quadraticVariation
              sample contribution (fun _unit => 1)]
            unfold linearCovarianceVariation
            exact Finset.sum_congr rfl
              (fun left _hleft =>
                Finset.sum_congr rfl
                  (fun right _hright => by rfl))
          have hconst :
              (∑ left ∈ sample, ∑ right ∈ sample,
                (1 / sampleSize) *
                  (contribution left * contribution right)) =
                (1 / sampleSize) *
                  (∑ left ∈ sample, ∑ right ∈ sample,
                    contribution left * contribution right) := by
            rw [Finset.mul_sum]
            exact Finset.sum_congr rfl
              (fun left _hleft => by rw [Finset.mul_sum])
          rw [hdiag, hconst]
    _ =
        quadraticVariation sample contribution (fun _unit => 1) -
          (1 / sampleSize) *
            (baseLinearizedSum sample contribution) ^ 2 := by
          rw [baseLinearizedSum_sq_eq_double_sum]

/--
If the finite multiplier covariance is the multinomial count kernel, the
second moment is the multinomial covariance target.
-/
theorem multiplierPerturbationSecondMoment_eq_multinomial_covariance_target
    [DecidableEq Unit]
    (support : Finset Omega) (mass : Omega -> Real)
    (sample : Finset Unit) (multiplier : Omega -> Unit -> Real)
    (contribution : Unit -> Real) (sampleSize : Real)
    (hcov :
      ∀ left ∈ sample, ∀ right ∈ sample,
        multiplierCenteredCovariance support mass multiplier left right =
          multinomialCenteredCovarianceKernel sampleSize left right) :
    multiplierPerturbationSecondMoment support mass sample multiplier
        contribution =
      quadraticVariation sample contribution (fun _unit => 1) -
        (1 / sampleSize) * (baseLinearizedSum sample contribution) ^ 2 := by
  rw [multiplierPerturbationSecondMoment_eq_linearCovarianceVariation]
  have hkernel :
      linearCovarianceVariation sample contribution
          (multiplierCenteredCovariance support mass multiplier) =
        linearCovarianceVariation sample contribution
          (multinomialCenteredCovarianceKernel sampleSize) := by
    unfold linearCovarianceVariation
    exact Finset.sum_congr rfl
      (fun left hleft =>
        Finset.sum_congr rfl
          (fun right hright => by rw [hcov left hleft right hright]))
  rw [hkernel]
  exact linearCovarianceVariation_multinomialCenteredCovarianceKernel_eq
    sample contribution sampleSize

/-- Finite centered linearized sums are numerator minus target times denominator. -/
theorem baseLinearizedSum_centered_eq_sub
    (sample : Finset Unit) (contribution weight : Unit -> Real)
    (target : Real) :
    baseLinearizedSum sample
        (fun unit => contribution unit - target * weight unit) =
      baseLinearizedSum sample contribution -
        target * baseLinearizedSum sample weight := by
  unfold baseLinearizedSum
  calc
    (∑ unit ∈ sample, (contribution unit - target * weight unit)) =
        (∑ unit ∈ sample, contribution unit) -
          (∑ unit ∈ sample, target * weight unit) := by
          rw [Finset.sum_sub_distrib]
    _ =
        (∑ unit ∈ sample, contribution unit) -
          target * (∑ unit ∈ sample, weight unit) := by
          rw [Finset.mul_sum]

/--
If the base numerator equals `target` times the base denominator, then the
centered linearized contribution has exact zero finite sum.
-/
theorem baseLinearizedSum_centered_eq_zero_of_base_ratio
    (sample : Finset Unit) (contribution weight : Unit -> Real)
    (target : Real)
    (hbase :
      baseLinearizedSum sample contribution =
        target * baseLinearizedSum sample weight) :
    baseLinearizedSum sample
        (fun unit => contribution unit - target * weight unit) = 0 := by
  rw [baseLinearizedSum_centered_eq_sub]
  rw [hbase]
  ring

/--
For a centered linearized contribution with exact zero finite sum, the
multinomial covariance correction vanishes.
-/
theorem multiplierPerturbationSecondMoment_eq_centeredSquareSum_of_multinomial_covariance_of_centered_sum_zero
    [DecidableEq Unit]
    (support : Finset Omega) (mass : Omega -> Real)
    (sample : Finset Unit) (multiplier : Omega -> Unit -> Real)
    (contribution weight : Unit -> Real) (target sampleSize : Real)
    (hcov :
      ∀ left ∈ sample, ∀ right ∈ sample,
        multiplierCenteredCovariance support mass multiplier left right =
          multinomialCenteredCovarianceKernel sampleSize left right)
    (hcentered :
      baseLinearizedSum sample
        (fun unit => contribution unit - target * weight unit) = 0) :
    multiplierPerturbationSecondMoment support mass sample multiplier
        (fun unit => contribution unit - target * weight unit) =
      centeredSquareSum sample contribution weight target := by
  rw [
    multiplierPerturbationSecondMoment_eq_multinomial_covariance_target
      support mass sample multiplier
        (fun unit => contribution unit - target * weight unit) sampleSize hcov]
  rw [hcentered]
  unfold quadraticVariation centeredSquareSum
  ring_nf
  exact Finset.sum_congr rfl
    (fun unit _hunit => by ring)

/--
Base-ratio version of the multinomial centered-square identity.  This is the
form used after an exact finite Hájek centering step.
-/
theorem multiplierPerturbationSecondMoment_eq_centeredSquareSum_of_multinomial_covariance_of_base_ratio
    [DecidableEq Unit]
    (support : Finset Omega) (mass : Omega -> Real)
    (sample : Finset Unit) (multiplier : Omega -> Unit -> Real)
    (contribution weight : Unit -> Real) (target sampleSize : Real)
    (hcov :
      ∀ left ∈ sample, ∀ right ∈ sample,
        multiplierCenteredCovariance support mass multiplier left right =
          multinomialCenteredCovarianceKernel sampleSize left right)
    (hbase :
      baseLinearizedSum sample contribution =
        target * baseLinearizedSum sample weight) :
    multiplierPerturbationSecondMoment support mass sample multiplier
        (fun unit => contribution unit - target * weight unit) =
      centeredSquareSum sample contribution weight target :=
  multiplierPerturbationSecondMoment_eq_centeredSquareSum_of_multinomial_covariance_of_centered_sum_zero
    support mass sample multiplier contribution weight target sampleSize hcov
    (baseLinearizedSum_centered_eq_zero_of_base_ratio
      sample contribution weight target hbase)

/--
Normalized multinomial version matching `bootstrapCenteredVarianceTarget` when
the centered linearized contribution has exact zero finite sum.
-/
theorem multiplierPerturbationSecondMoment_normalized_eq_bootstrapCenteredVarianceTarget_of_multinomial_covariance_of_centered_sum_zero
    [DecidableEq Unit]
    (support : Finset Omega) (mass : Omega -> Real)
    (sample : Finset Unit) (multiplier : Omega -> Unit -> Real)
    (contribution weight : Unit -> Real)
    (target denominator normalizer sampleSize : Real)
    (hcov :
      ∀ left ∈ sample, ∀ right ∈ sample,
        multiplierCenteredCovariance support mass multiplier left right =
          multinomialCenteredCovarianceKernel sampleSize left right)
    (hcentered :
      baseLinearizedSum sample
        (fun unit => contribution unit - target * weight unit) = 0) :
    (1 / denominator ^ 2) * (1 / normalizer) *
        multiplierPerturbationSecondMoment support mass sample multiplier
          (fun unit => contribution unit - target * weight unit) =
      bootstrapCenteredVarianceTarget sample contribution weight target
        denominator normalizer := by
  rw [
    multiplierPerturbationSecondMoment_eq_centeredSquareSum_of_multinomial_covariance_of_centered_sum_zero
      support mass sample multiplier contribution weight target sampleSize
      hcov hcentered]
  rfl

/--
Base-ratio version of the normalized multinomial finite variance-target
identity.
-/
theorem multiplierPerturbationSecondMoment_normalized_eq_bootstrapCenteredVarianceTarget_of_multinomial_covariance_of_base_ratio
    [DecidableEq Unit]
    (support : Finset Omega) (mass : Omega -> Real)
    (sample : Finset Unit) (multiplier : Omega -> Unit -> Real)
    (contribution weight : Unit -> Real)
    (target denominator normalizer sampleSize : Real)
    (hcov :
      ∀ left ∈ sample, ∀ right ∈ sample,
        multiplierCenteredCovariance support mass multiplier left right =
          multinomialCenteredCovarianceKernel sampleSize left right)
    (hbase :
      baseLinearizedSum sample contribution =
        target * baseLinearizedSum sample weight) :
    (1 / denominator ^ 2) * (1 / normalizer) *
        multiplierPerturbationSecondMoment support mass sample multiplier
          (fun unit => contribution unit - target * weight unit) =
      bootstrapCenteredVarianceTarget sample contribution weight target
        denominator normalizer :=
  multiplierPerturbationSecondMoment_normalized_eq_bootstrapCenteredVarianceTarget_of_multinomial_covariance_of_centered_sum_zero
    support mass sample multiplier contribution weight target denominator
    normalizer sampleSize hcov
    (baseLinearizedSum_centered_eq_zero_of_base_ratio
      sample contribution weight target hbase)

end WDSM
end Matching
end StatInference
