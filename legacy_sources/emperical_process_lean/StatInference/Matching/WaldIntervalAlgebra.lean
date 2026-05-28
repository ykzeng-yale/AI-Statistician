import StatInference.Matching.WDSM.VarianceLimitAlgebra

/-!
# Wald interval algebra for WDSM

This module verifies the deterministic endpoint algebra behind Wald-style
intervals.  The probability layer must still provide the studentized limiting
distribution and critical-value calibration; here we only prove the real
inequalities connecting interval coverage to an absolute-error bound.
-/

namespace StatInference
namespace Matching
namespace WDSM

/-- Half-width of a Wald interval using a critical value, standard error, and scaling factor. -/
noncomputable def waldHalfWidth (criticalValue standardError scale : Real) : Real :=
  criticalValue * standardError / scale

/-- Lower endpoint of a Wald interval. -/
noncomputable def waldLower
    (estimator criticalValue standardError scale : Real) : Real :=
  estimator - waldHalfWidth criticalValue standardError scale

/-- Upper endpoint of a Wald interval. -/
noncomputable def waldUpper
    (estimator criticalValue standardError scale : Real) : Real :=
  estimator + waldHalfWidth criticalValue standardError scale

/-- A target is covered by the Wald interval. -/
def waldCovers
    (estimator target criticalValue standardError scale : Real) : Prop :=
  waldLower estimator criticalValue standardError scale ≤ target ∧
    target ≤ waldUpper estimator criticalValue standardError scale

/-- Studentized Wald statistic using the estimated standard error. -/
noncomputable def waldStudentized
    (estimator target standardError scale : Real) : Real :=
  scale * (estimator - target) * standardError⁻¹

/-- Nonnegativity of the Wald half-width under nonnegative inputs and positive scale. -/
theorem waldHalfWidth_nonneg
    (criticalValue standardError scale : Real)
    (hcritical : 0 ≤ criticalValue)
    (hstandardError : 0 ≤ standardError)
    (hscale : 0 ≤ scale) :
    0 ≤ waldHalfWidth criticalValue standardError scale := by
  unfold waldHalfWidth
  exact div_nonneg (mul_nonneg hcritical hstandardError) hscale

/-- The Wald lower endpoint is below the upper endpoint when the half-width is nonnegative. -/
theorem waldLower_le_waldUpper_of_halfWidth_nonneg
    (estimator criticalValue standardError scale : Real)
    (hhalf :
      0 ≤ waldHalfWidth criticalValue standardError scale) :
    waldLower estimator criticalValue standardError scale ≤
      waldUpper estimator criticalValue standardError scale := by
  unfold waldLower waldUpper
  linarith

/-- The point estimate belongs to its own Wald interval when the half-width is nonnegative. -/
theorem estimator_mem_waldInterval_of_halfWidth_nonneg
    (estimator criticalValue standardError scale : Real)
    (hhalf :
      0 ≤ waldHalfWidth criticalValue standardError scale) :
    waldCovers estimator estimator criticalValue standardError scale := by
  unfold waldCovers waldLower waldUpper
  constructor <;> linarith

/--
Wald interval coverage is equivalent to the absolute target-minus-estimator
error being bounded by the half-width.
-/
theorem waldCovers_iff_abs_target_sub_estimator_le_halfWidth
    (estimator target criticalValue standardError scale : Real) :
    waldCovers estimator target criticalValue standardError scale ↔
      |target - estimator| ≤
        waldHalfWidth criticalValue standardError scale := by
  unfold waldCovers waldLower waldUpper
  constructor
  · intro hcover
    rw [abs_le]
    constructor <;> linarith
  · intro habs
    rw [abs_le] at habs
    constructor <;> linarith

/--
Equivalent Wald coverage display using the estimator-minus-target absolute
error, matching the usual statistical notation.
-/
theorem waldCovers_iff_abs_estimator_sub_target_le_halfWidth
    (estimator target criticalValue standardError scale : Real) :
    waldCovers estimator target criticalValue standardError scale ↔
      |estimator - target| ≤
        waldHalfWidth criticalValue standardError scale := by
  rw [waldCovers_iff_abs_target_sub_estimator_le_halfWidth]
  rw [abs_sub_comm]

/--
The absolute Wald studentized statistic is the scaled absolute error divided
by the standard error when scale and standard error are positive.
-/
theorem abs_waldStudentized_eq
    (estimator target standardError scale : Real)
    (hstandardError : 0 < standardError)
    (hscale : 0 < scale) :
    |waldStudentized estimator target standardError scale| =
      scale * |estimator - target| / standardError := by
  unfold waldStudentized
  rw [abs_mul, abs_mul, abs_inv, abs_of_pos hscale,
    abs_of_pos hstandardError]
  ring

/--
With positive scale and standard error, Wald coverage is equivalent to the
usual studentized event `|scale * (estimator - target) / se| <= critical`.
-/
theorem waldCovers_iff_abs_waldStudentized_le_critical
    (estimator target criticalValue standardError scale : Real)
    (hstandardError : 0 < standardError)
    (hscale : 0 < scale) :
    waldCovers estimator target criticalValue standardError scale ↔
      |waldStudentized estimator target standardError scale| ≤
        criticalValue := by
  rw [waldCovers_iff_abs_estimator_sub_target_le_halfWidth]
  rw [abs_waldStudentized_eq estimator target standardError scale
    hstandardError hscale]
  unfold waldHalfWidth
  constructor
  · intro hcoverage
    rw [div_le_iff₀ hstandardError]
    have hscaled :
        scale * |estimator - target| ≤
          scale * (criticalValue * standardError / scale) :=
      mul_le_mul_of_nonneg_left hcoverage hscale.le
    have hright :
        scale * (criticalValue * standardError / scale) =
          criticalValue * standardError := by
      field_simp [hscale.ne']
    rwa [hright] at hscaled
  · intro hstudentized
    rw [div_le_iff₀ hstandardError] at hstudentized
    rw [le_div_iff₀ hscale]
    simpa [mul_comm] using hstudentized

/--
Equivalent two-sided display of the Wald coverage event in terms of the
studentized statistic lying between `-criticalValue` and `criticalValue`.
-/
theorem waldCovers_iff_waldStudentized_between
    (estimator target criticalValue standardError scale : Real)
    (hstandardError : 0 < standardError)
    (hscale : 0 < scale) :
    waldCovers estimator target criticalValue standardError scale ↔
      -criticalValue ≤ waldStudentized estimator target standardError scale ∧
        waldStudentized estimator target standardError scale ≤ criticalValue := by
  rw [waldCovers_iff_abs_waldStudentized_le_critical
    estimator target criticalValue standardError scale hstandardError hscale]
  rw [abs_le]

end WDSM
end Matching
end StatInference
