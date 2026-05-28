import StatInference.Optimization.Theorem34
import StatInference.Optimization.Theorem37

/-!
# Chewi Theorem 5.10 accelerated gradient descent layer

This module starts the discrete accelerated-gradient route for Chewi Theorem
5.10.  The first layer records the source recurrence parameters and reuses the
compiled Chapter 3 one-step inequality `(3.3)` rather than reproving smooth
gradient-descent algebra.
-/

namespace StatInference
namespace Optimization

open Finset
open scoped InnerProductSpace

variable {E : Type*} [NormedAddCommGroup E] [InnerProductSpace ℝ E]

/-- Chewi Theorem 5.10 sequence `λ₀ = 0`,
`λₙ₊₁ = (1 + sqrt(1 + 4 λₙ²)) / 2`. -/
noncomputable def chewi510Lambda : ℕ -> ℝ
  | 0 => 0
  | n + 1 =>
      (1 + Real.sqrt (1 + 4 * chewi510Lambda n ^ (2 : ℕ))) / 2

@[simp] theorem chewi510Lambda_zero : chewi510Lambda 0 = 0 := rfl

theorem chewi510Lambda_succ (n : ℕ) :
    chewi510Lambda (n + 1) =
      (1 + Real.sqrt (1 + 4 * chewi510Lambda n ^ (2 : ℕ))) / 2 := rfl

@[simp] theorem chewi510Lambda_one : chewi510Lambda 1 = 1 := by
  rw [chewi510Lambda_succ]
  simp [chewi510Lambda]

/-- Chewi Theorem 5.10 momentum coefficient
`θₙ = (λₙ - 1) / λₙ₊₁`. -/
noncomputable def chewi510Theta (n : ℕ) : ℝ :=
  (chewi510Lambda n - 1) / chewi510Lambda (n + 1)

/-- Source-shaped trial point `y₀ = x₀`,
`yₙ₊₁ = xₙ₊₁ + θₙ₊₁ (xₙ₊₁ - xₙ)`. -/
noncomputable def chewi510TrialPoint (x : ℕ -> E) : ℕ -> E
  | 0 => x 0
  | n + 1 => x (n + 1) + chewi510Theta (n + 1) • (x (n + 1) - x n)

@[simp] theorem chewi510TrialPoint_zero (x : ℕ -> E) :
    chewi510TrialPoint x 0 = x 0 := rfl

theorem chewi510TrialPoint_succ (x : ℕ -> E) (n : ℕ) :
    chewi510TrialPoint x (n + 1) =
      x (n + 1) + chewi510Theta (n + 1) • (x (n + 1) - x n) := rfl

/--
Source-shaped AGD interface for Theorem 5.10.

The source writes `x_{-1} = x_0`; over natural-number indices this is encoded
as the separate condition `y 0 = x 0`.
-/
def IsChewi510AGDTrajectory (grad : E -> E) (beta : ℝ)
    (x y : ℕ -> E) : Prop :=
  y 0 = x 0 ∧
    (∀ n, y (n + 1) =
      x (n + 1) + chewi510Theta (n + 1) • (x (n + 1) - x n)) ∧
    ∀ n, x (n + 1) = gradientDescentStep grad (1 / beta) (y n)

/-- The vector whose squared norm telescopes in Chewi Theorem 5.10. -/
noncomputable def chewi510EnergyVector (x y : ℕ -> E)
    (xStar : E) (n : ℕ) : E :=
  chewi510Lambda (n + 1) • y n -
    (chewi510Lambda (n + 1) - 1) • x n - xStar

theorem IsChewi510AGDTrajectory.y_zero
    {grad : E -> E} {beta : ℝ} {x y : ℕ -> E}
    (h : IsChewi510AGDTrajectory grad beta x y) :
    y 0 = x 0 :=
  h.1

theorem IsChewi510AGDTrajectory.y_succ
    {grad : E -> E} {beta : ℝ} {x y : ℕ -> E}
    (h : IsChewi510AGDTrajectory grad beta x y) (n : ℕ) :
    y (n + 1) =
      x (n + 1) + chewi510Theta (n + 1) • (x (n + 1) - x n) :=
  h.2.1 n

theorem IsChewi510AGDTrajectory.step
    {grad : E -> E} {beta : ℝ} {x y : ℕ -> E}
    (h : IsChewi510AGDTrajectory grad beta x y) (n : ℕ) :
    x (n + 1) = gradientDescentStep grad (1 / beta) (y n) :=
  h.2.2 n

/-- Nonnegativity of Chewi's `λₙ` sequence. -/
theorem chewi510Lambda_nonneg (n : ℕ) :
    0 ≤ chewi510Lambda n := by
  induction n with
  | zero =>
      simp [chewi510Lambda]
  | succ n ih =>
      rw [chewi510Lambda_succ]
      have hsqrt_nonneg :
          0 ≤ Real.sqrt (1 + 4 * chewi510Lambda n ^ (2 : ℕ)) :=
        Real.sqrt_nonneg _
      nlinarith

/-- Every successor `λₙ₊₁` is strictly positive. -/
theorem chewi510Lambda_pos_succ (n : ℕ) :
    0 < chewi510Lambda (n + 1) := by
  rw [chewi510Lambda_succ]
  have hsqrt_nonneg :
      0 ≤ Real.sqrt (1 + 4 * chewi510Lambda n ^ (2 : ℕ)) :=
    Real.sqrt_nonneg _
  nlinarith

theorem chewi510Lambda_ne_zero_succ (n : ℕ) :
    chewi510Lambda (n + 1) ≠ 0 :=
  (chewi510Lambda_pos_succ n).ne'

/-- Chewi's defining recurrence implies `λₙ₊₁(λₙ₊₁ - 1) = λₙ²`. -/
theorem chewi510Lambda_succ_mul_sub_one (n : ℕ) :
    chewi510Lambda (n + 1) * (chewi510Lambda (n + 1) - 1) =
      chewi510Lambda n ^ (2 : ℕ) := by
  let a : ℝ := chewi510Lambda n
  have hnonneg : 0 ≤ 1 + 4 * a ^ (2 : ℕ) := by
    nlinarith [sq_nonneg a]
  have hsqrt_sq :
      (Real.sqrt (1 + 4 * a ^ (2 : ℕ))) ^ (2 : ℕ) =
        1 + 4 * a ^ (2 : ℕ) :=
    Real.sq_sqrt hnonneg
  rw [chewi510Lambda_succ]
  change
    ((1 + Real.sqrt (1 + 4 * a ^ (2 : ℕ))) / 2) *
        (((1 + Real.sqrt (1 + 4 * a ^ (2 : ℕ))) / 2) - 1) =
      a ^ (2 : ℕ)
  nlinarith [hsqrt_sq]

/-- A useful growth step: `λₙ₊₁ ≥ λₙ + 1/2`. -/
theorem chewi510Lambda_add_half_le_succ (n : ℕ) :
    chewi510Lambda n + (1 : ℝ) / 2 ≤ chewi510Lambda (n + 1) := by
  let a : ℝ := chewi510Lambda n
  have hsqrt_ge :
      2 * a ≤ Real.sqrt (1 + 4 * a ^ (2 : ℕ)) := by
    apply Real.le_sqrt_of_sq_le
    nlinarith [sq_nonneg a]
  rw [chewi510Lambda_succ]
  change a + (1 : ℝ) / 2 ≤
    (1 + Real.sqrt (1 + 4 * a ^ (2 : ℕ))) / 2
  nlinarith

/-- Source final estimate ingredient: `λ_N ≥ N / 2`. -/
theorem chewi510Lambda_ge_nat_half (N : ℕ) :
    (N : ℝ) / 2 ≤ chewi510Lambda N := by
  induction N with
  | zero =>
      simp [chewi510Lambda]
  | succ N ih =>
      have hstep := chewi510Lambda_add_half_le_succ N
      have hcast : ((N + 1 : ℕ) : ℝ) = (N : ℝ) + 1 := by
        norm_num
      nlinarith

/-- The source weight `λₙ₊₁ - 1` is nonnegative. -/
theorem chewi510Lambda_one_le_succ (n : ℕ) :
    1 ≤ chewi510Lambda (n + 1) := by
  rw [chewi510Lambda_succ]
  have hsqrt_ge_one :
      (1 : ℝ) ≤ Real.sqrt (1 + 4 * chewi510Lambda n ^ (2 : ℕ)) := by
    apply Real.le_sqrt_of_sq_le
    nlinarith [sq_nonneg (chewi510Lambda n)]
  nlinarith

theorem chewi510Lambda_sub_one_nonneg_succ (n : ℕ) :
    0 ≤ chewi510Lambda (n + 1) - 1 := by
  nlinarith [chewi510Lambda_one_le_succ n]

/-- The scalar identity behind the source choice of `θₙ₊₁`. -/
theorem chewi510Lambda_mul_theta_succ (n : ℕ) :
    chewi510Lambda (n + 2) * chewi510Theta (n + 1) =
      chewi510Lambda (n + 1) - 1 := by
  unfold chewi510Theta
  have hne : chewi510Lambda (n + 2) ≠ 0 :=
    chewi510Lambda_ne_zero_succ (n + 1)
  field_simp [hne]

/--
The source telescoping alignment forced by
`θₙ₊₁ = (λₙ₊₁ - 1) / λₙ₊₂`.
-/
theorem chewi510_telescopeAlignment_of_trial_succ
    (x y : ℕ -> E) (n : ℕ)
    (hy : y (n + 1) =
      x (n + 1) + chewi510Theta (n + 1) • (x (n + 1) - x n)) :
    chewi510Lambda (n + 1) • x (n + 1) -
        (chewi510Lambda (n + 1) - 1) • x n =
      chewi510Lambda (n + 2) • y (n + 1) -
        (chewi510Lambda (n + 2) - 1) • x (n + 1) := by
  rw [hy]
  have htheta := chewi510Lambda_mul_theta_succ n
  calc
    chewi510Lambda (n + 1) • x (n + 1) -
        (chewi510Lambda (n + 1) - 1) • x n
        =
          (chewi510Lambda (n + 1) - 1) • (x (n + 1) - x n) +
            x (n + 1) := by
          module
    _ =
      chewi510Lambda (n + 2) •
          (x (n + 1) + chewi510Theta (n + 1) • (x (n + 1) - x n)) -
        (chewi510Lambda (n + 2) - 1) • x (n + 1) := by
      rw [smul_add, smul_smul, htheta]
      module

/-- Telescoping alignment for a source-shaped AGD trajectory. -/
theorem IsChewi510AGDTrajectory.telescopeAlignment
    {grad : E -> E} {beta : ℝ} {x y : ℕ -> E}
    (h : IsChewi510AGDTrajectory grad beta x y) (n : ℕ) :
    chewi510Lambda (n + 1) • x (n + 1) -
        (chewi510Lambda (n + 1) - 1) • x n =
      chewi510Lambda (n + 2) • y (n + 1) -
        (chewi510Lambda (n + 2) - 1) • x (n + 1) :=
  chewi510_telescopeAlignment_of_trial_succ x y n (h.y_succ n)

/-- At time zero, the AGD energy vector is exactly `x₀ - x_*`. -/
theorem IsChewi510AGDTrajectory.energyVector_zero
    {grad : E -> E} {beta : ℝ} {x y : ℕ -> E} {xStar : E}
    (h : IsChewi510AGDTrajectory grad beta x y) :
    chewi510EnergyVector x y xStar 0 = x 0 - xStar := by
  unfold chewi510EnergyVector
  rw [h.y_zero]
  simp

/--
Source algebra:
`β/2 (‖y-z‖² - ‖x⁺-z‖²)
 = -β/2 ‖x⁺-y‖² - β <x⁺-y, y-z>`.
-/
theorem chewi510_norm_sq_diff_step_identity
    (beta : ℝ) (xplus y z : E) :
    (beta / 2) *
        (‖y - z‖ ^ (2 : ℕ) - ‖xplus - z‖ ^ (2 : ℕ)) =
      -(beta / 2) * ‖xplus - y‖ ^ (2 : ℕ) -
        beta * inner ℝ (xplus - y) (y - z) := by
  have hdecomp : xplus - z = (y - z) + (xplus - y) := by
    module
  rw [hdecomp, norm_add_sq_real, real_inner_comm (y - z) (xplus - y)]
  ring

/--
Scaled norm-difference identity used after the two weighted one-step
inequalities are added.
-/
theorem chewi510_scaled_norm_sq_diff_identity
    (beta lambda : ℝ) (hlambda_pos : 0 < lambda) (a c : E) :
    beta / (2 * lambda) *
        (‖c‖ ^ (2 : ℕ) - ‖c + lambda • a‖ ^ (2 : ℕ)) =
      -(beta * lambda / 2) * ‖a‖ ^ (2 : ℕ) -
        beta * inner ℝ a c := by
  rw [norm_add_sq_real, norm_smul, Real.norm_of_nonneg hlambda_pos.le,
    real_inner_smul_right, real_inner_comm c a]
  field_simp [hlambda_pos.ne']
  ring

/--
Chewi Theorem 5.10's reuse of `(3.3)`:
`x⁺ = y - β⁻¹ ∇f(y)` satisfies the source one-step inequality.
-/
theorem chewi510_oneStepInequality
    {C : Set E} {f : E -> ℝ} {grad : E -> E} {beta : ℝ}
    {y z : E}
    (hfirst : FirstOrderStrongConvexOn C f grad 0)
    (hsmooth : SmoothWithGradientOn C f grad beta)
    (hy : y ∈ C)
    (hz : z ∈ C)
    (hstep_mem : gradientDescentStep grad (1 / beta) y ∈ C)
    (hbeta_pos : 0 < beta) :
    ‖gradientDescentStep grad (1 / beta) y - z‖ ^ (2 : ℕ) ≤
      ‖y - z‖ ^ (2 : ℕ) -
        (2 / beta) * (f (gradientDescentStep grad (1 / beta) y) - f z) := by
  have hh_nonneg : 0 ≤ (1 : ℝ) / beta := by
    positivity
  have hbeta_step : beta * ((1 : ℝ) / beta) ≤ 1 := by
    have hmul : beta * ((1 : ℝ) / beta) = 1 := by
      field_simp [hbeta_pos.ne']
    exact le_of_eq hmul
  have hrec :=
    oneStepRecurrence_of_firstOrderStrongConvexOn
      (C := C) (f := f) (grad := grad) (alpha := (0 : ℝ))
      (beta := beta) (h := (1 : ℝ) / beta) (x := y) (z := z)
      hfirst hsmooth hy hz hstep_mem hh_nonneg hbeta_step
  have hsimp :
      (1 - (0 : ℝ) * ((1 : ℝ) / beta)) * ‖y - z‖ ^ (2 : ℕ) -
          2 * ((1 : ℝ) / beta) *
            (f (gradientDescentStep grad (1 / beta) y) - f z) =
        ‖y - z‖ ^ (2 : ℕ) -
          (2 / beta) * (f (gradientDescentStep grad (1 / beta) y) - f z) := by
    ring
  exact hrec.trans_eq hsimp

/-- Whole-space version of the Theorem 5.10 `(3.3)` reuse. -/
theorem chewi510_oneStepInequality_univ
    {f : E -> ℝ} {grad : E -> E} {beta : ℝ} {y z : E}
    (hfirst : FirstOrderStrongConvexOn Set.univ f grad 0)
    (hsmooth : SmoothWithGradientOn Set.univ f grad beta)
    (hbeta_pos : 0 < beta) :
    ‖gradientDescentStep grad (1 / beta) y - z‖ ^ (2 : ℕ) ≤
      ‖y - z‖ ^ (2 : ℕ) -
        (2 / beta) * (f (gradientDescentStep grad (1 / beta) y) - f z) := by
  exact
    chewi510_oneStepInequality
      (C := Set.univ) (f := f) (grad := grad) (beta := beta)
      (y := y) (z := z) hfirst hsmooth (by simp) (by simp) (by simp)
      hbeta_pos

/-- Scalar rearrangement of the source one-step inequality `(3.3)`. -/
theorem chewi510_gap_le_norm_sq_diff_of_oneStep
    {beta A B gap : ℝ}
    (hstep : B ≤ A - (2 / beta) * gap)
    (hbeta_pos : 0 < beta) :
    gap ≤ (beta / 2) * (A - B) := by
  have hcoef_nonneg : 0 ≤ beta / 2 := by
    positivity
  have hmain : (2 / beta) * gap ≤ A - B := by
    nlinarith
  have hmul := mul_le_mul_of_nonneg_left hmain hcoef_nonneg
  have hcoef :
      (beta / 2) * ((2 / beta) * gap) = gap := by
    field_simp [hbeta_pos.ne']
  nlinarith

/--
Rearranged Chewi Theorem 5.10 one-step estimate:
`f(x⁺)-f(z) ≤ β/2 (‖y-z‖² - ‖x⁺-z‖²)`.
-/
theorem chewi510_gap_le_norm_sq_diff
    {C : Set E} {f : E -> ℝ} {grad : E -> E} {beta : ℝ}
    {y z : E}
    (hfirst : FirstOrderStrongConvexOn C f grad 0)
    (hsmooth : SmoothWithGradientOn C f grad beta)
    (hy : y ∈ C)
    (hz : z ∈ C)
    (hstep_mem : gradientDescentStep grad (1 / beta) y ∈ C)
    (hbeta_pos : 0 < beta) :
    f (gradientDescentStep grad (1 / beta) y) - f z ≤
      (beta / 2) *
        (‖y - z‖ ^ (2 : ℕ) -
          ‖gradientDescentStep grad (1 / beta) y - z‖ ^ (2 : ℕ)) := by
  have hone :=
    chewi510_oneStepInequality
      (C := C) (f := f) (grad := grad) (beta := beta) (y := y) (z := z)
      hfirst hsmooth hy hz hstep_mem hbeta_pos
  exact
    chewi510_gap_le_norm_sq_diff_of_oneStep
      (beta := beta)
      (A := ‖y - z‖ ^ (2 : ℕ))
      (B := ‖gradientDescentStep grad (1 / beta) y - z‖ ^ (2 : ℕ))
      (gap := f (gradientDescentStep grad (1 / beta) y) - f z)
      hone hbeta_pos

/-- Whole-space rearranged one-step estimate for Chewi Theorem 5.10. -/
theorem chewi510_gap_le_norm_sq_diff_univ
    {f : E -> ℝ} {grad : E -> E} {beta : ℝ} {y z : E}
    (hfirst : FirstOrderStrongConvexOn Set.univ f grad 0)
    (hsmooth : SmoothWithGradientOn Set.univ f grad beta)
    (hbeta_pos : 0 < beta) :
    f (gradientDescentStep grad (1 / beta) y) - f z ≤
      (beta / 2) *
        (‖y - z‖ ^ (2 : ℕ) -
          ‖gradientDescentStep grad (1 / beta) y - z‖ ^ (2 : ℕ)) := by
  exact
    chewi510_gap_le_norm_sq_diff
      (C := Set.univ) (f := f) (grad := grad) (beta := beta)
      (y := y) (z := z) hfirst hsmooth (by simp) (by simp) (by simp)
      hbeta_pos

/--
Source inner-product form of the rearranged one-step estimate.
-/
theorem chewi510_gap_le_inner_form
    {C : Set E} {f : E -> ℝ} {grad : E -> E} {beta : ℝ}
    {y z : E}
    (hfirst : FirstOrderStrongConvexOn C f grad 0)
    (hsmooth : SmoothWithGradientOn C f grad beta)
    (hy : y ∈ C)
    (hz : z ∈ C)
    (hstep_mem : gradientDescentStep grad (1 / beta) y ∈ C)
    (hbeta_pos : 0 < beta) :
    f (gradientDescentStep grad (1 / beta) y) - f z ≤
      -(beta / 2) *
          ‖gradientDescentStep grad (1 / beta) y - y‖ ^ (2 : ℕ) -
        beta *
          inner ℝ (gradientDescentStep grad (1 / beta) y - y) (y - z) := by
  have hgap :=
    chewi510_gap_le_norm_sq_diff
      (C := C) (f := f) (grad := grad) (beta := beta) (y := y) (z := z)
      hfirst hsmooth hy hz hstep_mem hbeta_pos
  have hident :=
    chewi510_norm_sq_diff_step_identity beta
      (gradientDescentStep grad (1 / beta) y) y z
  exact hgap.trans_eq hident

/-- Whole-space source inner-product form of the one-step estimate. -/
theorem chewi510_gap_le_inner_form_univ
    {f : E -> ℝ} {grad : E -> E} {beta : ℝ} {y z : E}
    (hfirst : FirstOrderStrongConvexOn Set.univ f grad 0)
    (hsmooth : SmoothWithGradientOn Set.univ f grad beta)
    (hbeta_pos : 0 < beta) :
    f (gradientDescentStep grad (1 / beta) y) - f z ≤
      -(beta / 2) *
          ‖gradientDescentStep grad (1 / beta) y - y‖ ^ (2 : ℕ) -
        beta *
          inner ℝ (gradientDescentStep grad (1 / beta) y - y) (y - z) := by
  exact
    chewi510_gap_le_inner_form
      (C := Set.univ) (f := f) (grad := grad) (beta := beta)
      (y := y) (z := z) hfirst hsmooth (by simp) (by simp) (by simp)
      hbeta_pos

/--
Algebraic combination of the two one-step inequalities used in Chewi's AGD
proof, in the inner-product form just before the source rewrites it as a
scaled squared-norm difference.
-/
theorem chewi510_weighted_two_gap_le_inner
    {beta lambda gapX gapStar : ℝ} {a y x xStar : E}
    (hlambda_ge_one : 1 ≤ lambda)
    (hgapX :
      gapX ≤ -(beta / 2) * ‖a‖ ^ (2 : ℕ) -
        beta * inner ℝ a (y - x))
    (hgapStar :
      gapStar ≤ -(beta / 2) * ‖a‖ ^ (2 : ℕ) -
        beta * inner ℝ a (y - xStar)) :
    (lambda - 1) * gapX + gapStar ≤
      -(beta * lambda / 2) * ‖a‖ ^ (2 : ℕ) -
        beta * inner ℝ a (lambda • y - (lambda - 1) • x - xStar) := by
  have hw_nonneg : 0 ≤ lambda - 1 := by
    nlinarith
  have hmul := mul_le_mul_of_nonneg_left hgapX hw_nonneg
  have hsum := add_le_add hmul hgapStar
  calc
    (lambda - 1) * gapX + gapStar
        ≤
          (lambda - 1) *
              (-(beta / 2) * ‖a‖ ^ (2 : ℕ) -
                beta * inner ℝ a (y - x)) +
            (-(beta / 2) * ‖a‖ ^ (2 : ℕ) -
              beta * inner ℝ a (y - xStar)) := hsum
    _ =
      -(beta * lambda / 2) * ‖a‖ ^ (2 : ℕ) -
        beta * inner ℝ a (lambda • y - (lambda - 1) • x - xStar) := by
      simp [inner_sub_right, real_inner_smul_right]
      ring

/--
The same weighted two-gap bound after the source norm-square identity is
applied.
-/
theorem chewi510_weighted_two_gap_le_scaled_norm_diff
    {beta lambda gapX gapStar : ℝ} {a y x xStar : E}
    (hlambda_pos : 0 < lambda)
    (hlambda_ge_one : 1 ≤ lambda)
    (hgapX :
      gapX ≤ -(beta / 2) * ‖a‖ ^ (2 : ℕ) -
        beta * inner ℝ a (y - x))
    (hgapStar :
      gapStar ≤ -(beta / 2) * ‖a‖ ^ (2 : ℕ) -
        beta * inner ℝ a (y - xStar)) :
    (lambda - 1) * gapX + gapStar ≤
      beta / (2 * lambda) *
        (‖lambda • y - (lambda - 1) • x - xStar‖ ^ (2 : ℕ) -
          ‖lambda • y - (lambda - 1) • x - xStar +
            lambda • a‖ ^ (2 : ℕ)) := by
  have hinner :=
    chewi510_weighted_two_gap_le_inner
      (beta := beta) (lambda := lambda) (gapX := gapX)
      (gapStar := gapStar) (a := a) (y := y) (x := x) (xStar := xStar)
      hlambda_ge_one hgapX hgapStar
  have hident :=
    chewi510_scaled_norm_sq_diff_identity
      beta lambda hlambda_pos a
      (lambda • y - (lambda - 1) • x - xStar)
  exact hinner.trans_eq hident.symm

/--
Chewi Theorem 5.10 weighted two-point inequality for a source-shaped AGD
trajectory, before using the `θ` telescope alignment.
-/
theorem chewi510_weighted_two_point_bound
    {C : Set E} {f : E -> ℝ} {grad : E -> E} {beta : ℝ}
    {x y : ℕ -> E} {xStar : E} (n : ℕ)
    (hfirst : FirstOrderStrongConvexOn C f grad 0)
    (hsmooth : SmoothWithGradientOn C f grad beta)
    (htraj : IsChewi510AGDTrajectory grad beta x y)
    (hx_mem : ∀ k, x k ∈ C)
    (hy_mem : ∀ k, y k ∈ C)
    (hxStar_mem : xStar ∈ C)
    (hbeta_pos : 0 < beta) :
    (chewi510Lambda (n + 1) - 1) *
        (f (x (n + 1)) - f (x n)) +
      (f (x (n + 1)) - f xStar) ≤
      beta / (2 * chewi510Lambda (n + 1)) *
        (‖chewi510Lambda (n + 1) • y n -
            (chewi510Lambda (n + 1) - 1) • x n - xStar‖ ^ (2 : ℕ) -
          ‖chewi510Lambda (n + 1) • y n -
              (chewi510Lambda (n + 1) - 1) • x n - xStar +
            chewi510Lambda (n + 1) • (x (n + 1) - y n)‖ ^ (2 : ℕ)) := by
  have hstep_eq :
      x (n + 1) = gradientDescentStep grad (1 / beta) (y n) :=
    htraj.step n
  have hstep_eq' :
      gradientDescentStep grad beta⁻¹ (y n) = x (n + 1) := by
    simpa [one_div] using hstep_eq.symm
  have hstep_mem : gradientDescentStep grad (1 / beta) (y n) ∈ C := by
    rw [← hstep_eq]
    exact hx_mem (n + 1)
  have hgapX :
      f (x (n + 1)) - f (x n) ≤
        -(beta / 2) * ‖x (n + 1) - y n‖ ^ (2 : ℕ) -
          beta * inner ℝ (x (n + 1) - y n) (y n - x n) := by
    simpa [hstep_eq'] using
      chewi510_gap_le_inner_form
        (C := C) (f := f) (grad := grad) (beta := beta)
        (y := y n) (z := x n) hfirst hsmooth (hy_mem n) (hx_mem n)
        hstep_mem hbeta_pos
  have hgapStar :
      f (x (n + 1)) - f xStar ≤
        -(beta / 2) * ‖x (n + 1) - y n‖ ^ (2 : ℕ) -
          beta * inner ℝ (x (n + 1) - y n) (y n - xStar) := by
    simpa [hstep_eq'] using
      chewi510_gap_le_inner_form
        (C := C) (f := f) (grad := grad) (beta := beta)
        (y := y n) (z := xStar) hfirst hsmooth (hy_mem n) hxStar_mem
        hstep_mem hbeta_pos
  exact
    chewi510_weighted_two_gap_le_scaled_norm_diff
      (beta := beta) (lambda := chewi510Lambda (n + 1))
      (gapX := f (x (n + 1)) - f (x n))
      (gapStar := f (x (n + 1)) - f xStar)
      (a := x (n + 1) - y n) (y := y n) (x := x n)
      (xStar := xStar)
      (chewi510Lambda_pos_succ n) (chewi510Lambda_one_le_succ n)
      hgapX hgapStar

/--
Source-shaped version of `chewi510_weighted_two_point_bound` with the second
norm written as
`‖λₙ₊₁ xₙ₊₁ - (λₙ₊₁ - 1) xₙ - x_*‖²`.
-/
theorem chewi510_weighted_two_point_bound_source
    {C : Set E} {f : E -> ℝ} {grad : E -> E} {beta : ℝ}
    {x y : ℕ -> E} {xStar : E} (n : ℕ)
    (hfirst : FirstOrderStrongConvexOn C f grad 0)
    (hsmooth : SmoothWithGradientOn C f grad beta)
    (htraj : IsChewi510AGDTrajectory grad beta x y)
    (hx_mem : ∀ k, x k ∈ C)
    (hy_mem : ∀ k, y k ∈ C)
    (hxStar_mem : xStar ∈ C)
    (hbeta_pos : 0 < beta) :
    (chewi510Lambda (n + 1) - 1) *
        (f (x (n + 1)) - f (x n)) +
      (f (x (n + 1)) - f xStar) ≤
      beta / (2 * chewi510Lambda (n + 1)) *
        (‖chewi510Lambda (n + 1) • y n -
            (chewi510Lambda (n + 1) - 1) • x n - xStar‖ ^ (2 : ℕ) -
          ‖chewi510Lambda (n + 1) • x (n + 1) -
              (chewi510Lambda (n + 1) - 1) • x n - xStar‖ ^ (2 : ℕ)) := by
  have h :=
    chewi510_weighted_two_point_bound
      (C := C) (f := f) (grad := grad) (beta := beta)
      (x := x) (y := y) (xStar := xStar) n
      hfirst hsmooth htraj hx_mem hy_mem hxStar_mem hbeta_pos
  have hrewrite :
      chewi510Lambda (n + 1) • y n -
            (chewi510Lambda (n + 1) - 1) • x n - xStar +
          chewi510Lambda (n + 1) • (x (n + 1) - y n) =
        chewi510Lambda (n + 1) • x (n + 1) -
            (chewi510Lambda (n + 1) - 1) • x n - xStar := by
    module
  simpa [hrewrite] using h

/--
Telescope-ready source inequality: the second squared norm is rewritten as
the next AGD energy vector.
-/
theorem chewi510_weighted_two_point_bound_telescope
    {C : Set E} {f : E -> ℝ} {grad : E -> E} {beta : ℝ}
    {x y : ℕ -> E} {xStar : E} (n : ℕ)
    (hfirst : FirstOrderStrongConvexOn C f grad 0)
    (hsmooth : SmoothWithGradientOn C f grad beta)
    (htraj : IsChewi510AGDTrajectory grad beta x y)
    (hx_mem : ∀ k, x k ∈ C)
    (hy_mem : ∀ k, y k ∈ C)
    (hxStar_mem : xStar ∈ C)
    (hbeta_pos : 0 < beta) :
    (chewi510Lambda (n + 1) - 1) *
        (f (x (n + 1)) - f (x n)) +
      (f (x (n + 1)) - f xStar) ≤
      beta / (2 * chewi510Lambda (n + 1)) *
        (‖chewi510EnergyVector x y xStar n‖ ^ (2 : ℕ) -
          ‖chewi510EnergyVector x y xStar (n + 1)‖ ^ (2 : ℕ)) := by
  have h :=
    chewi510_weighted_two_point_bound_source
      (C := C) (f := f) (grad := grad) (beta := beta)
      (x := x) (y := y) (xStar := xStar) n
      hfirst hsmooth htraj hx_mem hy_mem hxStar_mem hbeta_pos
  have halign :
      chewi510Lambda (n + 1) • x (n + 1) -
          (chewi510Lambda (n + 1) - 1) • x n =
        chewi510Lambda (n + 2) • y (n + 1) -
          (chewi510Lambda (n + 2) - 1) • x (n + 1) :=
    htraj.telescopeAlignment n
  have hsecond :
      chewi510Lambda (n + 1) • x (n + 1) -
            (chewi510Lambda (n + 1) - 1) • x n - xStar =
        chewi510EnergyVector x y xStar (n + 1) := by
    unfold chewi510EnergyVector
    rw [halign]
  simpa [chewi510EnergyVector, hsecond] using h

/-- Scalar identity used when multiplying the AGD one-step inequality by `λₙ₊₁`. -/
theorem chewi510_lambda_mul_weighted_gap_eq (gap : ℕ -> ℝ) (n : ℕ) :
    chewi510Lambda (n + 1) *
        ((chewi510Lambda (n + 1) - 1) * (gap (n + 1) - gap n) +
          gap (n + 1)) =
      chewi510Lambda (n + 1) ^ (2 : ℕ) * gap (n + 1) -
        chewi510Lambda n ^ (2 : ℕ) * gap n := by
  rw [← chewi510Lambda_succ_mul_sub_one n]
  ring

/--
Finite weighted-sum consequence of the telescope-ready AGD one-step bound.
This is the summation skeleton in Chewi Theorem 5.10.
-/
theorem chewi510_weighted_sum_bound_of_step
    (beta : ℝ) (gap energySq : ℕ -> ℝ) (N : ℕ)
    (hstep : ∀ n,
      (chewi510Lambda (n + 1) - 1) * (gap (n + 1) - gap n) +
          gap (n + 1) ≤
        beta / (2 * chewi510Lambda (n + 1)) *
          (energySq n - energySq (n + 1))) :
    (∑ n ∈ Finset.range N,
        (chewi510Lambda (n + 1) ^ (2 : ℕ) * gap (n + 1) -
          chewi510Lambda n ^ (2 : ℕ) * gap n)) ≤
      beta / 2 * (energySq 0 - energySq N) := by
  have hterm : ∀ n,
      chewi510Lambda (n + 1) ^ (2 : ℕ) * gap (n + 1) -
          chewi510Lambda n ^ (2 : ℕ) * gap n ≤
        beta / 2 * (energySq n - energySq (n + 1)) := by
    intro n
    have hmul :=
      mul_le_mul_of_nonneg_left (hstep n) (chewi510Lambda_pos_succ n).le
    have hleft := chewi510_lambda_mul_weighted_gap_eq gap n
    have hright :
        chewi510Lambda (n + 1) *
            (beta / (2 * chewi510Lambda (n + 1)) *
              (energySq n - energySq (n + 1))) =
          beta / 2 * (energySq n - energySq (n + 1)) := by
      have hne : chewi510Lambda (n + 1) ≠ 0 :=
        chewi510Lambda_ne_zero_succ n
      field_simp [hne]
    rwa [hleft, hright] at hmul
  calc
    (∑ n ∈ Finset.range N,
        (chewi510Lambda (n + 1) ^ (2 : ℕ) * gap (n + 1) -
          chewi510Lambda n ^ (2 : ℕ) * gap n))
        ≤
          ∑ n ∈ Finset.range N,
            beta / 2 * (energySq n - energySq (n + 1)) := by
          exact Finset.sum_le_sum fun n _hn => hterm n
    _ = beta / 2 * (energySq 0 - energySq N) := by
      rw [← Finset.mul_sum, sum_range_sub_succ]

/--
Summed Chewi Theorem 5.10 inequality after multiplying each step by
`λₙ₊₁`.
-/
theorem chewi510_weighted_sum_bound
    {C : Set E} {f : E -> ℝ} {grad : E -> E} {beta : ℝ}
    {x y : ℕ -> E} {xStar : E} (N : ℕ)
    (hfirst : FirstOrderStrongConvexOn C f grad 0)
    (hsmooth : SmoothWithGradientOn C f grad beta)
    (htraj : IsChewi510AGDTrajectory grad beta x y)
    (hx_mem : ∀ k, x k ∈ C)
    (hy_mem : ∀ k, y k ∈ C)
    (hxStar_mem : xStar ∈ C)
    (hbeta_pos : 0 < beta) :
    (∑ n ∈ Finset.range N,
        (chewi510Lambda (n + 1) ^ (2 : ℕ) *
            (f (x (n + 1)) - f xStar) -
          chewi510Lambda n ^ (2 : ℕ) *
            (f (x n) - f xStar))) ≤
      beta / 2 *
        (‖chewi510EnergyVector x y xStar 0‖ ^ (2 : ℕ) -
          ‖chewi510EnergyVector x y xStar N‖ ^ (2 : ℕ)) := by
  let gap : ℕ -> ℝ := fun k => f (x k) - f xStar
  let energySq : ℕ -> ℝ :=
    fun k => ‖chewi510EnergyVector x y xStar k‖ ^ (2 : ℕ)
  have hstep : ∀ n,
      (chewi510Lambda (n + 1) - 1) * (gap (n + 1) - gap n) +
          gap (n + 1) ≤
        beta / (2 * chewi510Lambda (n + 1)) *
          (energySq n - energySq (n + 1)) := by
    intro n
    have hp :=
      chewi510_weighted_two_point_bound_telescope
        (C := C) (f := f) (grad := grad) (beta := beta)
        (x := x) (y := y) (xStar := xStar) n
        hfirst hsmooth htraj hx_mem hy_mem hxStar_mem hbeta_pos
    have hleft :
        (chewi510Lambda (n + 1) - 1) * (gap (n + 1) - gap n) +
            gap (n + 1) =
          (chewi510Lambda (n + 1) - 1) *
              (f (x (n + 1)) - f (x n)) +
            (f (x (n + 1)) - f xStar) := by
      simp [gap]
    simpa [energySq, hleft]
      using hp
  simpa [gap, energySq] using
    chewi510_weighted_sum_bound_of_step beta gap energySq N hstep

/-- The weighted gap sum telescopes after the `λ` recurrence is used. -/
theorem chewi510_weighted_sum_telescope (gap : ℕ -> ℝ) (N : ℕ) :
    (∑ n ∈ Finset.range N,
        (chewi510Lambda (n + 1) ^ (2 : ℕ) * gap (n + 1) -
          chewi510Lambda n ^ (2 : ℕ) * gap n)) =
      chewi510Lambda N ^ (2 : ℕ) * gap N -
        chewi510Lambda 0 ^ (2 : ℕ) * gap 0 := by
  have htel :=
    sum_range_sub_succ
      (fun n => -(chewi510Lambda n ^ (2 : ℕ) * gap n)) N
  simpa [sub_eq_add_neg, add_comm, add_left_comm, add_assoc] using htel

/--
Chewi Theorem 5.10 summed estimate after dropping the nonnegative terminal
energy:
`λ_N^2 (f(x_N)-f_*) <= β/2 * ||E_0||^2`.
-/
theorem chewi510_lambda_sq_gap_le_initial_energy
    {C : Set E} {f : E -> ℝ} {grad : E -> E} {beta : ℝ}
    {x y : ℕ -> E} {xStar : E} (N : ℕ)
    (hfirst : FirstOrderStrongConvexOn C f grad 0)
    (hsmooth : SmoothWithGradientOn C f grad beta)
    (htraj : IsChewi510AGDTrajectory grad beta x y)
    (hx_mem : ∀ k, x k ∈ C)
    (hy_mem : ∀ k, y k ∈ C)
    (hxStar_mem : xStar ∈ C)
    (hbeta_pos : 0 < beta) :
    chewi510Lambda N ^ (2 : ℕ) * (f (x N) - f xStar) ≤
      beta / 2 * ‖chewi510EnergyVector x y xStar 0‖ ^ (2 : ℕ) := by
  have hsum :=
    chewi510_weighted_sum_bound
      (C := C) (f := f) (grad := grad) (beta := beta)
      (x := x) (y := y) (xStar := xStar) N
      hfirst hsmooth htraj hx_mem hy_mem hxStar_mem hbeta_pos
  have htel :=
    chewi510_weighted_sum_telescope
      (fun k => f (x k) - f xStar) N
  rw [htel] at hsum
  have hsum' :
      chewi510Lambda N ^ (2 : ℕ) * (f (x N) - f xStar) ≤
        beta / 2 *
          (‖chewi510EnergyVector x y xStar 0‖ ^ (2 : ℕ) -
            ‖chewi510EnergyVector x y xStar N‖ ^ (2 : ℕ)) := by
    simpa [chewi510Lambda_zero] using hsum
  have hterminal_nonneg :
      0 ≤ ‖chewi510EnergyVector x y xStar N‖ ^ (2 : ℕ) :=
    sq_nonneg _
  have hdrop :
      beta / 2 *
          (‖chewi510EnergyVector x y xStar 0‖ ^ (2 : ℕ) -
            ‖chewi510EnergyVector x y xStar N‖ ^ (2 : ℕ)) ≤
        beta / 2 * ‖chewi510EnergyVector x y xStar 0‖ ^ (2 : ℕ) := by
    have hcoef_nonneg : 0 ≤ beta / 2 := by
      positivity
    have hdiff :
        ‖chewi510EnergyVector x y xStar 0‖ ^ (2 : ℕ) -
            ‖chewi510EnergyVector x y xStar N‖ ^ (2 : ℕ) ≤
          ‖chewi510EnergyVector x y xStar 0‖ ^ (2 : ℕ) := by
      nlinarith
    exact mul_le_mul_of_nonneg_left hdiff hcoef_nonneg
  exact hsum'.trans hdrop

/--
Chewi Theorem 5.10 denominator form before replacing `λ_N` by `N / 2`.
-/
theorem chewi510_gap_le_initial_distance_over_lambda_sq
    {C : Set E} {f : E -> ℝ} {grad : E -> E} {beta : ℝ}
    {x y : ℕ -> E} {xStar : E} {N : ℕ}
    (hfirst : FirstOrderStrongConvexOn C f grad 0)
    (hsmooth : SmoothWithGradientOn C f grad beta)
    (htraj : IsChewi510AGDTrajectory grad beta x y)
    (hx_mem : ∀ k, x k ∈ C)
    (hy_mem : ∀ k, y k ∈ C)
    (hxStar_mem : xStar ∈ C)
    (hbeta_pos : 0 < beta)
    (hN : N ≠ 0) :
    f (x N) - f xStar ≤
      (beta / 2 * ‖x 0 - xStar‖ ^ (2 : ℕ)) /
        chewi510Lambda N ^ (2 : ℕ) := by
  have hmain :=
    chewi510_lambda_sq_gap_le_initial_energy
      (C := C) (f := f) (grad := grad) (beta := beta)
      (x := x) (y := y) (xStar := xStar) N
      hfirst hsmooth htraj hx_mem hy_mem hxStar_mem hbeta_pos
  have hmain' :
      chewi510Lambda N ^ (2 : ℕ) * (f (x N) - f xStar) ≤
        beta / 2 * ‖x 0 - xStar‖ ^ (2 : ℕ) := by
    simpa [htraj.energyVector_zero] using hmain
  have hlambda_pos : 0 < chewi510Lambda N := by
    cases N with
    | zero =>
        contradiction
    | succ n =>
        exact chewi510Lambda_pos_succ n
  have hden_pos : 0 < chewi510Lambda N ^ (2 : ℕ) :=
    pow_pos hlambda_pos _
  apply (le_div_iff₀ hden_pos).mpr
  nlinarith

/--
Chewi Theorem 5.10 source rate:
`f(x_N)-f_* <= 2 β ||x_0-x_*||^2 / N^2`.
-/
theorem chewi510_gap_le_two_beta_dist_sq_over_nat_sq
    {C : Set E} {f : E -> ℝ} {grad : E -> E} {beta : ℝ}
    {x y : ℕ -> E} {xStar : E} {N : ℕ}
    (hfirst : FirstOrderStrongConvexOn C f grad 0)
    (hsmooth : SmoothWithGradientOn C f grad beta)
    (htraj : IsChewi510AGDTrajectory grad beta x y)
    (hx_mem : ∀ k, x k ∈ C)
    (hy_mem : ∀ k, y k ∈ C)
    (hxStar_mem : xStar ∈ C)
    (hbeta_pos : 0 < beta)
    (hN : N ≠ 0) :
    f (x N) - f xStar ≤
      2 * beta * ‖x 0 - xStar‖ ^ (2 : ℕ) / (N : ℝ) ^ (2 : ℕ) := by
  have hden :=
    chewi510_gap_le_initial_distance_over_lambda_sq
      (C := C) (f := f) (grad := grad) (beta := beta)
      (x := x) (y := y) (xStar := xStar)
      hfirst hsmooth htraj hx_mem hy_mem hxStar_mem hbeta_pos hN
  have hN_pos : 0 < (N : ℝ) := by
    exact_mod_cast Nat.pos_of_ne_zero hN
  have hhalf_pos : 0 < (N : ℝ) / 2 := by
    positivity
  have hlambda_ge : (N : ℝ) / 2 ≤ chewi510Lambda N :=
    chewi510Lambda_ge_nat_half N
  have hlambda_nonneg : 0 ≤ chewi510Lambda N :=
    chewi510Lambda_nonneg N
  have hlambda_sq_ge :
      ((N : ℝ) / 2) ^ (2 : ℕ) ≤ chewi510Lambda N ^ (2 : ℕ) :=
    (sq_le_sq₀ hhalf_pos.le hlambda_nonneg).mpr hlambda_ge
  have hhalf_sq_pos : 0 < ((N : ℝ) / 2) ^ (2 : ℕ) :=
    pow_pos hhalf_pos _
  have hinv_le :
      1 / chewi510Lambda N ^ (2 : ℕ) ≤
        1 / (((N : ℝ) / 2) ^ (2 : ℕ)) :=
    one_div_le_one_div_of_le hhalf_sq_pos hlambda_sq_ge
  have hcoef_nonneg :
      0 ≤ beta / 2 * ‖x 0 - xStar‖ ^ (2 : ℕ) :=
    mul_nonneg (by positivity) (sq_nonneg _)
  have hcompare :
      (beta / 2 * ‖x 0 - xStar‖ ^ (2 : ℕ)) /
          chewi510Lambda N ^ (2 : ℕ) ≤
        (beta / 2 * ‖x 0 - xStar‖ ^ (2 : ℕ)) /
          (((N : ℝ) / 2) ^ (2 : ℕ)) := by
    have hinv_le' :
        (chewi510Lambda N ^ (2 : ℕ))⁻¹ ≤
          (((N : ℝ) / 2) ^ (2 : ℕ))⁻¹ := by
      simpa [one_div] using hinv_le
    rw [div_eq_mul_inv, div_eq_mul_inv]
    exact mul_le_mul_of_nonneg_left hinv_le' hcoef_nonneg
  have hclosed :
      (beta / 2 * ‖x 0 - xStar‖ ^ (2 : ℕ)) /
          (((N : ℝ) / 2) ^ (2 : ℕ)) =
        2 * beta * ‖x 0 - xStar‖ ^ (2 : ℕ) / (N : ℝ) ^ (2 : ℕ) := by
    field_simp [hN_pos.ne']
  exact hden.trans (hcompare.trans_eq hclosed)

end Optimization
end StatInference
