import Mathlib.Data.Real.Basic
import Mathlib.Tactic.FieldSimp
import Mathlib.Tactic.Ring

/-!
# Exact ratio linearization algebra for WDSM Hajek estimators

WDSM repeatedly rewrites Hajek-ratio errors and bootstrap perturbations.  This
module proves those rewrites as exact real identities.
-/

namespace StatInference
namespace Matching
namespace WDSM

theorem ratio_sub_const_eq_centered_numerator
    (numerator denominator target : Real) (hden : denominator ≠ 0) :
    numerator / denominator - target =
      (numerator - denominator * target) / denominator := by
  field_simp [hden]

theorem ratio_eq_const_of_centered_numerator_eq_zero
    (numerator denominator target : Real) (hden : denominator ≠ 0)
    (hcenter : numerator - denominator * target = 0) :
    numerator / denominator = target := by
  have hsub :
      numerator / denominator - target = 0 := by
    rw [ratio_sub_const_eq_centered_numerator numerator denominator target hden,
      hcenter]
    simp
  exact sub_eq_zero.mp hsub

theorem centered_numerator_eq_zero_of_ratio_eq_const
    (numerator denominator target : Real) (hden : denominator ≠ 0)
    (hratio : numerator / denominator = target) :
    numerator - denominator * target = 0 := by
  have hsub : numerator / denominator - target = 0 := by
    rw [hratio]
    ring
  rw [ratio_sub_const_eq_centered_numerator numerator denominator target hden] at hsub
  field_simp [hden] at hsub
  simpa using hsub

theorem ratio_eq_const_iff_centered_numerator_eq_zero
    (numerator denominator target : Real) (hden : denominator ≠ 0) :
    numerator / denominator = target ↔
      numerator - denominator * target = 0 := by
  constructor
  · exact centered_numerator_eq_zero_of_ratio_eq_const numerator denominator target hden
  · exact ratio_eq_const_of_centered_numerator_eq_zero numerator denominator target hden

theorem ratio_sub_const_eq_zero_iff_centered_numerator_eq_zero
    (numerator denominator target : Real) (hden : denominator ≠ 0) :
    numerator / denominator - target = 0 ↔
      numerator - denominator * target = 0 := by
  constructor
  · intro hsub
    rw [ratio_sub_const_eq_centered_numerator numerator denominator target hden] at hsub
    field_simp [hden] at hsub
    simpa using hsub
  · intro hcenter
    rw [ratio_sub_const_eq_centered_numerator numerator denominator target hden,
      hcenter]
    simp

theorem centered_numerator_eq_den_mul_ratio_sub_const
    (numerator denominator target : Real) (hden : denominator ≠ 0) :
    numerator - denominator * target =
      denominator * (numerator / denominator - target) := by
  field_simp [hden]

theorem ratio_sub_ratio_eq
    (numerator denominator deltaNumerator deltaDenominator : Real)
    (hden : denominator ≠ 0)
    (hden_perturbed : denominator + deltaDenominator ≠ 0) :
    (numerator + deltaNumerator) /
        (denominator + deltaDenominator) -
        numerator / denominator =
      (denominator * deltaNumerator -
        numerator * deltaDenominator) /
        (denominator * (denominator + deltaDenominator)) := by
  field_simp [hden, hden_perturbed]
  ring

/--
If the numerator and denominator perturbations have zero cross product error,
the exact perturbed ratio error is zero.
-/
theorem ratio_sub_ratio_eq_zero_of_cross_product_eq
    (numerator denominator deltaNumerator deltaDenominator : Real)
    (hden : denominator ≠ 0)
    (hden_perturbed : denominator + deltaDenominator ≠ 0)
    (hcross :
      denominator * deltaNumerator =
        numerator * deltaDenominator) :
    (numerator + deltaNumerator) /
        (denominator + deltaDenominator) -
        numerator / denominator = 0 := by
  rw [ratio_sub_ratio_eq numerator denominator deltaNumerator
    deltaDenominator hden hden_perturbed]
  rw [hcross]
  simp

/--
Zero exact perturbed ratio error forces the cross product error to vanish.
-/
theorem cross_product_eq_of_ratio_sub_ratio_eq_zero
    (numerator denominator deltaNumerator deltaDenominator : Real)
    (hden : denominator ≠ 0)
    (hden_perturbed : denominator + deltaDenominator ≠ 0)
    (hzero :
      (numerator + deltaNumerator) /
          (denominator + deltaDenominator) -
          numerator / denominator = 0) :
    denominator * deltaNumerator =
      numerator * deltaDenominator := by
  rw [ratio_sub_ratio_eq numerator denominator deltaNumerator
    deltaDenominator hden hden_perturbed] at hzero
  have hprod :
      denominator * (denominator + deltaDenominator) ≠ 0 :=
    mul_ne_zero hden hden_perturbed
  have hnum :
      denominator * deltaNumerator -
        numerator * deltaDenominator = 0 := by
    rcases div_eq_zero_iff.mp hzero with hnum | hdenom
    · exact hnum
    · exact False.elim (hprod hdenom)
  exact sub_eq_zero.mp hnum

/--
The exact ratio error is zero iff the perturbation cross product error is zero.
-/
theorem ratio_sub_ratio_eq_zero_iff_cross_product_eq
    (numerator denominator deltaNumerator deltaDenominator : Real)
    (hden : denominator ≠ 0)
    (hden_perturbed : denominator + deltaDenominator ≠ 0) :
    (numerator + deltaNumerator) /
        (denominator + deltaDenominator) -
        numerator / denominator = 0 ↔
      denominator * deltaNumerator =
        numerator * deltaDenominator := by
  constructor
  · exact cross_product_eq_of_ratio_sub_ratio_eq_zero numerator denominator
      deltaNumerator deltaDenominator hden hden_perturbed
  · exact ratio_sub_ratio_eq_zero_of_cross_product_eq numerator denominator
      deltaNumerator deltaDenominator hden hden_perturbed

theorem ratio_sub_ratio_eq_with_base_ratio
    (baseRatio denominator deltaNumerator deltaDenominator : Real)
    (hden_perturbed : denominator + deltaDenominator ≠ 0) :
    (baseRatio * denominator + deltaNumerator) /
        (denominator + deltaDenominator) - baseRatio =
      (deltaNumerator - baseRatio * deltaDenominator) /
        (denominator + deltaDenominator) := by
  field_simp [hden_perturbed]
  ring

/--
First-order expansion of a ratio around a base ratio, with the exact product
remainder from replacing the perturbed denominator by the base denominator.
-/
theorem ratio_sub_ratio_eq_with_base_ratio_linear_add_remainder
    (baseRatio denominator deltaNumerator deltaDenominator : Real)
    (hden : denominator ≠ 0)
    (hden_perturbed : denominator + deltaDenominator ≠ 0) :
    (baseRatio * denominator + deltaNumerator) /
        (denominator + deltaDenominator) - baseRatio =
      (deltaNumerator - baseRatio * deltaDenominator) / denominator -
        ((deltaNumerator - baseRatio * deltaDenominator) * deltaDenominator) /
          (denominator * (denominator + deltaDenominator)) := by
  field_simp [hden, hden_perturbed]
  ring

/--
The error in the first-order ratio expansion is the product of the centered
numerator perturbation and the denominator perturbation, divided by the two
denominators.
-/
theorem ratio_sub_ratio_with_base_ratio_linearization_error_eq
    (baseRatio denominator deltaNumerator deltaDenominator : Real)
    (hden : denominator ≠ 0)
    (hden_perturbed : denominator + deltaDenominator ≠ 0) :
    ((baseRatio * denominator + deltaNumerator) /
        (denominator + deltaDenominator) - baseRatio) -
        (deltaNumerator - baseRatio * deltaDenominator) / denominator =
      -((deltaNumerator - baseRatio * deltaDenominator) * deltaDenominator) /
        (denominator * (denominator + deltaDenominator)) := by
  rw [ratio_sub_ratio_eq_with_base_ratio_linear_add_remainder
    baseRatio denominator deltaNumerator deltaDenominator hden hden_perturbed]
  ring

theorem perturbed_ratio_eq_baseRatio_of_centered_delta_eq_zero
    (baseRatio denominator deltaNumerator deltaDenominator : Real)
    (hden_perturbed : denominator + deltaDenominator ≠ 0)
    (hcenter : deltaNumerator - baseRatio * deltaDenominator = 0) :
    (baseRatio * denominator + deltaNumerator) /
        (denominator + deltaDenominator) = baseRatio := by
  have hsub :
      (baseRatio * denominator + deltaNumerator) /
          (denominator + deltaDenominator) - baseRatio = 0 := by
    rw [ratio_sub_ratio_eq_with_base_ratio baseRatio denominator
      deltaNumerator deltaDenominator hden_perturbed, hcenter]
    simp
  exact sub_eq_zero.mp hsub

theorem centered_delta_eq_zero_of_perturbed_ratio_eq_baseRatio
    (baseRatio denominator deltaNumerator deltaDenominator : Real)
    (hden_perturbed : denominator + deltaDenominator ≠ 0)
    (hratio :
      (baseRatio * denominator + deltaNumerator) /
          (denominator + deltaDenominator) = baseRatio) :
    deltaNumerator - baseRatio * deltaDenominator = 0 := by
  have hsub :
      (baseRatio * denominator + deltaNumerator) /
          (denominator + deltaDenominator) - baseRatio = 0 := by
    rw [hratio]
    ring
  rw [ratio_sub_ratio_eq_with_base_ratio baseRatio denominator
    deltaNumerator deltaDenominator hden_perturbed] at hsub
  field_simp [hden_perturbed] at hsub
  simpa using hsub

theorem perturbed_ratio_eq_baseRatio_iff_centered_delta_eq_zero
    (baseRatio denominator deltaNumerator deltaDenominator : Real)
    (hden_perturbed : denominator + deltaDenominator ≠ 0) :
    (baseRatio * denominator + deltaNumerator) /
        (denominator + deltaDenominator) = baseRatio ↔
      deltaNumerator - baseRatio * deltaDenominator = 0 := by
  constructor
  · exact centered_delta_eq_zero_of_perturbed_ratio_eq_baseRatio
      baseRatio denominator deltaNumerator deltaDenominator hden_perturbed
  · exact perturbed_ratio_eq_baseRatio_of_centered_delta_eq_zero
      baseRatio denominator deltaNumerator deltaDenominator hden_perturbed

theorem ratio_linearization_error_eq_zero_of_deltaDenominator_zero
    (baseRatio denominator deltaNumerator deltaDenominator : Real)
    (hden : denominator ≠ 0) (hdelta : deltaDenominator = 0) :
    ((baseRatio * denominator + deltaNumerator) /
        (denominator + deltaDenominator) - baseRatio) -
        (deltaNumerator - baseRatio * deltaDenominator) / denominator = 0 := by
  have hden_perturbed : denominator + deltaDenominator ≠ 0 := by
    simpa [hdelta] using hden
  rw [ratio_sub_ratio_with_base_ratio_linearization_error_eq
    baseRatio denominator deltaNumerator deltaDenominator hden hden_perturbed]
  simp [hdelta]

/--
Exact inverse-denominator perturbation identity used before replacing the
remainder by an `o_p` term.
-/
theorem inv_add_sub_inv_eq_neg_delta_div
    (denominator deltaDenominator : Real)
    (hden : denominator ≠ 0)
    (hden_perturbed : denominator + deltaDenominator ≠ 0) :
    1 / (denominator + deltaDenominator) - 1 / denominator =
      -deltaDenominator / (denominator * (denominator + deltaDenominator)) := by
  field_simp [hden, hden_perturbed]
  ring

/--
First-order inverse-denominator expansion with its exact quadratic remainder.
-/
theorem inv_add_sub_inv_eq_linear_add_quadratic
    (denominator deltaDenominator : Real)
    (hden : denominator ≠ 0)
    (hden_perturbed : denominator + deltaDenominator ≠ 0) :
    1 / (denominator + deltaDenominator) - 1 / denominator =
      -deltaDenominator / denominator ^ 2 +
        deltaDenominator ^ 2 /
          (denominator ^ 2 * (denominator + deltaDenominator)) := by
  field_simp [hden, hden_perturbed]
  ring

/--
The error in the linearized inverse denominator is exactly quadratic in the
denominator perturbation.
-/
theorem inv_add_sub_inv_linearization_error_eq_quadratic
    (denominator deltaDenominator : Real)
    (hden : denominator ≠ 0)
    (hden_perturbed : denominator + deltaDenominator ≠ 0) :
    (1 / (denominator + deltaDenominator) - 1 / denominator) -
        (-deltaDenominator / denominator ^ 2) =
      deltaDenominator ^ 2 /
        (denominator ^ 2 * (denominator + deltaDenominator)) := by
  rw [inv_add_sub_inv_eq_linear_add_quadratic
    denominator deltaDenominator hden hden_perturbed]
  ring

theorem inv_linearization_error_eq_zero_of_deltaDenominator_zero
    (denominator deltaDenominator : Real)
    (hden : denominator ≠ 0) (hdelta : deltaDenominator = 0) :
    (1 / (denominator + deltaDenominator) - 1 / denominator) -
        (-deltaDenominator / denominator ^ 2) = 0 := by
  have hden_perturbed : denominator + deltaDenominator ≠ 0 := by
    simpa [hdelta] using hden
  rw [inv_add_sub_inv_linearization_error_eq_quadratic
    denominator deltaDenominator hden hden_perturbed]
  simp [hdelta]

end WDSM
end Matching
end StatInference
