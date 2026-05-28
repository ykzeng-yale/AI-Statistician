import Mathlib

/-!
# Finite quadratic-variation algebra for WDSM residual arrays

The residual CLT layer needs deterministic quadratic-variation objects of the
form `sum coefficient^2 * variance`.  This module proves basic finite algebra
for those objects before any probability limit is invoked.
-/

namespace StatInference
namespace Matching
namespace WDSM

open scoped BigOperators

variable {Unit : Type*}

/-- Finite quadratic variation for residual coefficients and conditional variances. -/
noncomputable def quadraticVariation (sample : Finset Unit)
    (coefficient variance : Unit -> Real) : Real :=
  ∑ unit ∈ sample, coefficient unit ^ 2 * variance unit

theorem quadraticVariation_nonneg
    (sample : Finset Unit) (coefficient variance : Unit -> Real)
    (hvariance_nonneg : ∀ unit, unit ∈ sample -> 0 ≤ variance unit) :
    0 ≤ quadraticVariation sample coefficient variance := by
  unfold quadraticVariation
  exact Finset.sum_nonneg
    (fun unit hunit =>
      mul_nonneg (sq_nonneg (coefficient unit))
        (hvariance_nonneg unit hunit))

theorem quadraticVariation_zero_of_coeff_zero
    (sample : Finset Unit) (coefficient variance : Unit -> Real)
    (hcoeff_zero : ∀ unit, unit ∈ sample -> coefficient unit = 0) :
    quadraticVariation sample coefficient variance = 0 := by
  unfold quadraticVariation
  exact Finset.sum_eq_zero
    (fun unit hunit => by
      rw [hcoeff_zero unit hunit]
      ring)

/--
With strictly positive variance proxies, zero quadratic variation is
equivalent to all sample coefficients being zero.
-/
theorem quadraticVariation_eq_zero_iff_coeff_zero_of_variance_pos
    (sample : Finset Unit) (coefficient variance : Unit -> Real)
    (hvariance_pos : ∀ unit, unit ∈ sample -> 0 < variance unit) :
    quadraticVariation sample coefficient variance = 0 ↔
      ∀ unit, unit ∈ sample -> coefficient unit = 0 := by
  constructor
  · intro hzero unit hunit
    have hzero' :
        (∑ unit ∈ sample, coefficient unit ^ 2 * variance unit) = 0 := by
      simpa [quadraticVariation] using hzero
    have hterms :
        ∀ unit, unit ∈ sample ->
          coefficient unit ^ 2 * variance unit = 0 :=
      (Finset.sum_eq_zero_iff_of_nonneg
        (s := sample)
        (f := fun unit => coefficient unit ^ 2 * variance unit)
        (fun unit hunit =>
          mul_nonneg (sq_nonneg (coefficient unit))
            (le_of_lt (hvariance_pos unit hunit)))).mp hzero'
    have hcoeff_sq : coefficient unit ^ 2 = 0 := by
      rcases mul_eq_zero.mp (hterms unit hunit) with hcoeff_sq | hvariance_zero
      · exact hcoeff_sq
      · exact False.elim ((ne_of_gt (hvariance_pos unit hunit))
          hvariance_zero)
    exact sq_eq_zero_iff.mp hcoeff_sq
  · intro hcoeff_zero
    exact quadraticVariation_zero_of_coeff_zero sample coefficient variance
      hcoeff_zero

/--
With strictly positive variance proxies, one nonzero sample coefficient makes
the quadratic variation strictly positive.
-/
theorem quadraticVariation_pos_of_exists_coeff_ne_zero_of_variance_pos
    (sample : Finset Unit) (coefficient variance : Unit -> Real)
    (hvariance_pos : ∀ unit, unit ∈ sample -> 0 < variance unit)
    (hexists : ∃ unit, unit ∈ sample ∧ coefficient unit ≠ 0) :
    0 < quadraticVariation sample coefficient variance := by
  have hne : quadraticVariation sample coefficient variance ≠ 0 := by
    intro hzero
    obtain ⟨unit, hunit, hcoeff_ne⟩ := hexists
    have hcoeff_zero :
        coefficient unit = 0 :=
      (quadraticVariation_eq_zero_iff_coeff_zero_of_variance_pos
        sample coefficient variance hvariance_pos).mp hzero unit hunit
    exact hcoeff_ne hcoeff_zero
  exact lt_of_le_of_ne'
    (quadraticVariation_nonneg sample coefficient variance
      (fun unit hunit => le_of_lt (hvariance_pos unit hunit))) hne

theorem quadraticVariation_scale
    (sample : Finset Unit) (coefficient variance : Unit -> Real)
    (scale : Real) :
    quadraticVariation sample (fun unit => scale * coefficient unit) variance =
      scale ^ 2 * quadraticVariation sample coefficient variance := by
  unfold quadraticVariation
  calc
    (∑ unit ∈ sample, (scale * coefficient unit) ^ 2 * variance unit)
        = ∑ unit ∈ sample,
            scale ^ 2 * (coefficient unit ^ 2 * variance unit) := by
          exact Finset.sum_congr rfl
            (fun unit _hunit => by ring)
    _ = scale ^ 2 *
          (∑ unit ∈ sample, coefficient unit ^ 2 * variance unit) := by
        rw [Finset.mul_sum]

end WDSM
end Matching
end StatInference
