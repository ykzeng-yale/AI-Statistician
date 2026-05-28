import Mathlib

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

end WDSM
end Matching
end StatInference
