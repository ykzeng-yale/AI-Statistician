import StatInference.Optimization.Basic

/-!
# Chewi Chapter 7 Frank-Wolfe layer

This module starts the Chapter 7 formalization lane with the source-facing
convergence theorem for Frank-Wolfe / conditional gradient.  The theorem is
kept in the same supplied-interface style as the earlier optimization lane:
smoothness is `SmoothWithGradientOn`, convexity is the compiled first-order
lower model with parameter `0`, and the linear optimization oracle is an
explicit argmin certificate for linear functionals over the feasible set.
-/

namespace StatInference
namespace Optimization

open Set
open scoped InnerProductSpace

variable {E : Type*} [NormedAddCommGroup E] [InnerProductSpace ℝ E]

/-- Chewi Chapter 7 linear optimization oracle over a feasible set. -/
def LinearOptimizationOracleOn (C : Set E) (loo : E -> E) : Prop :=
  ∀ p : E, loo p ∈ C ∧ ∀ z ∈ C, inner ℝ p (loo p) ≤ inner ℝ p z

theorem LinearOptimizationOracleOn.mem {C : Set E} {loo : E -> E}
    (hloo : LinearOptimizationOracleOn C loo) (p : E) :
    loo p ∈ C :=
  (hloo p).1

theorem LinearOptimizationOracleOn.inner_le {C : Set E} {loo : E -> E}
    (hloo : LinearOptimizationOracleOn C loo) (p : E)
    {z : E} (hz : z ∈ C) :
    inner ℝ p (loo p) ≤ inner ℝ p z :=
  (hloo p).2 z hz

/-- A source-facing finite diameter bound for Chapter 7. -/
def HasDiameterBound (C : Set E) (D : ℝ) : Prop :=
  0 ≤ D ∧ ∀ ⦃x⦄, x ∈ C -> ∀ ⦃y⦄, y ∈ C -> ‖y - x‖ ≤ D

omit [InnerProductSpace ℝ E] in
theorem HasDiameterBound.nonneg {C : Set E} {D : ℝ}
    (hD : HasDiameterBound C D) :
    0 ≤ D :=
  hD.1

omit [InnerProductSpace ℝ E] in
theorem HasDiameterBound.norm_le {C : Set E} {D : ℝ}
    (hD : HasDiameterBound C D)
    {x : E} (hx : x ∈ C) {y : E} (hy : y ∈ C) :
    ‖y - x‖ ≤ D :=
  hD.2 hx hy

omit [InnerProductSpace ℝ E] in
theorem HasDiameterBound.norm_sq_le {C : Set E} {D : ℝ}
    (hD : HasDiameterBound C D)
    {x : E} (hx : x ∈ C) {y : E} (hy : y ∈ C) :
    ‖y - x‖ ^ (2 : ℕ) ≤ D ^ (2 : ℕ) :=
  (sq_le_sq₀ (norm_nonneg _) hD.nonneg).mpr (hD.norm_le hx hy)

/-- Frank-Wolfe step with a supplied linear optimization oracle. -/
def frankWolfeStep (grad loo : E -> E) (h : ℝ) (x : E) : E :=
  (1 - h) • x + h • loo (grad x)

/-- Chewi's source step size `h_n = 2 / (n + 2)`. -/
noncomputable def chewi73StepSize (n : ℕ) : ℝ :=
  2 / ((n : ℝ) + 2)

/-- A sequence follows the Frank-Wolfe update. -/
def IsFrankWolfeTrajectory (grad loo : E -> E) (x : ℕ -> E) : Prop :=
  ∀ n : ℕ, x (n + 1) =
    frankWolfeStep grad loo (chewi73StepSize n) (x n)

theorem chewi73StepSize_pos (n : ℕ) : 0 < chewi73StepSize n := by
  have hden : 0 < (n : ℝ) + 2 := by positivity
  dsimp [chewi73StepSize]
  positivity

theorem chewi73StepSize_nonneg (n : ℕ) : 0 ≤ chewi73StepSize n :=
  (chewi73StepSize_pos n).le

theorem chewi73StepSize_le_one (n : ℕ) : chewi73StepSize n ≤ 1 := by
  have hden : 0 < (n : ℝ) + 2 := by positivity
  dsimp [chewi73StepSize]
  rw [div_le_iff₀ hden]
  norm_num

theorem one_sub_chewi73StepSize_nonneg (n : ℕ) :
    0 ≤ 1 - chewi73StepSize n := by
  exact sub_nonneg.mpr (chewi73StepSize_le_one n)

/-- Frank-Wolfe updates remain feasible by convexity when `0 <= h <= 1`. -/
theorem frankWolfeStep_mem
    {C : Set E} {grad loo : E -> E} {h : ℝ} {x : E}
    (hconv : Convex ℝ C)
    (hx : x ∈ C) (hy : loo (grad x) ∈ C)
    (hh_nonneg : 0 ≤ h) (hh_le_one : h ≤ 1) :
    frankWolfeStep grad loo h x ∈ C := by
  exact
    (convex_iff_add_mem.mp hconv) hx hy
      (by nlinarith) hh_nonneg (by ring)

/-- Source step-size version of `frankWolfeStep_mem`. -/
theorem frankWolfeStep_mem_chewi73
    {C : Set E} {grad loo : E -> E} {x : E}
    (hconv : Convex ℝ C)
    (hx : x ∈ C) (hy : loo (grad x) ∈ C) (n : ℕ) :
    frankWolfeStep grad loo (chewi73StepSize n) x ∈ C :=
  frankWolfeStep_mem hconv hx hy
    (chewi73StepSize_nonneg n) (chewi73StepSize_le_one n)

/--
Chewi Theorem 7.3 one-step recurrence from smoothness, the LOO certificate,
first-order convexity, and the diameter bound.
-/
theorem frankWolfe_oneStep_gap_recurrence
    {C : Set E} {f : E -> ℝ} {grad loo : E -> E}
    {beta D h : ℝ} {x xStar : E}
    (hfirst : FirstOrderStrongConvexOn C f grad 0)
    (hsmooth : SmoothWithGradientOn C f grad beta)
    (hloo : LinearOptimizationOracleOn C loo)
    (hdiam : HasDiameterBound C D)
    (hbeta_nonneg : 0 ≤ beta)
    (hx : x ∈ C) (hxStar : xStar ∈ C)
    (hh_nonneg : 0 ≤ h) (hh_le_one : h ≤ 1) :
    f (frankWolfeStep grad loo h x) - f xStar ≤
      (1 - h) * (f x - f xStar) +
        (beta * D ^ (2 : ℕ) * h ^ (2 : ℕ)) / 2 := by
  let y : E := loo (grad x)
  let xNext : E := frankWolfeStep grad loo h x
  have hy : y ∈ C := hloo.mem (grad x)
  have hxNext : xNext ∈ C := by
    exact frankWolfeStep_mem hfirst.convex_set hx hy hh_nonneg hh_le_one
  have hsmooth_step := hsmooth.upper_model hx hxNext
  have hsub : xNext - x = h • (y - x) := by
    simp [xNext, y, frankWolfeStep]
    module
  have hinner_step :
      inner ℝ (grad x) (xNext - x) =
        h * inner ℝ (grad x) (y - x) := by
    rw [hsub, real_inner_smul_right]
  have hloo_inner : inner ℝ (grad x) y ≤ inner ℝ (grad x) xStar :=
    hloo.inner_le (grad x) hxStar
  have hinner_y :
      inner ℝ (grad x) (y - x) ≤
        inner ℝ (grad x) (xStar - x) := by
    rw [inner_sub_right, inner_sub_right]
    nlinarith
  have hmodel := hfirst.lower_model hx hxStar
  have hconv_inner :
      inner ℝ (grad x) (xStar - x) ≤ f xStar - f x := by
    nlinarith [hmodel]
  have hinner_bound :
      inner ℝ (grad x) (xNext - x) ≤ h * (f xStar - f x) := by
    rw [hinner_step]
    exact mul_le_mul_of_nonneg_left (hinner_y.trans hconv_inner) hh_nonneg
  have hnorm_sq :
      ‖xNext - x‖ ^ (2 : ℕ) ≤
        h ^ (2 : ℕ) * D ^ (2 : ℕ) := by
    have hdiam_sq : ‖y - x‖ ^ (2 : ℕ) ≤ D ^ (2 : ℕ) :=
      hdiam.norm_sq_le hx hy
    rw [hsub, norm_smul, Real.norm_of_nonneg hh_nonneg, mul_pow]
    nlinarith [sq_nonneg h, hdiam_sq]
  have hquad :
      (beta / 2) * ‖xNext - x‖ ^ (2 : ℕ) ≤
        (beta / 2) * (h ^ (2 : ℕ) * D ^ (2 : ℕ)) := by
    exact mul_le_mul_of_nonneg_left hnorm_sq (by nlinarith)
  have htarget :
      f x + h * (f xStar - f x) +
          (beta / 2) * (h ^ (2 : ℕ) * D ^ (2 : ℕ)) - f xStar =
        (1 - h) * (f x - f xStar) +
          (beta * D ^ (2 : ℕ) * h ^ (2 : ℕ)) / 2 := by
    ring
  calc
    f xNext - f xStar
        ≤ f x + inner ℝ (grad x) (xNext - x) +
            (beta / 2) * ‖xNext - x‖ ^ (2 : ℕ) - f xStar := by
          nlinarith
    _ ≤ f x + h * (f xStar - f x) +
            (beta / 2) * (h ^ (2 : ℕ) * D ^ (2 : ℕ)) - f xStar := by
          nlinarith
    _ = (1 - h) * (f x - f xStar) +
          (beta * D ^ (2 : ℕ) * h ^ (2 : ℕ)) / 2 := htarget

/-- Scalar induction used in Chewi's proof of Theorem 7.3. -/
theorem chewi73_scalar_rate_aux {u : ℕ -> ℝ} {B : ℝ}
    (hB_nonneg : 0 ≤ B)
    (hrec : ∀ n : ℕ,
      u (n + 1) ≤
        (1 - chewi73StepSize n) * u n +
          (B * chewi73StepSize n ^ (2 : ℕ)) / 2) :
    ∀ n : ℕ, u (n + 1) ≤ 2 * B / ((n : ℝ) + 2) := by
  intro n
  induction n with
  | zero =>
      have h0 := hrec 0
      have hstep : u 1 ≤ B / 2 := by
        norm_num [chewi73StepSize] at h0 ⊢
        nlinarith
      norm_num
      nlinarith
  | succ n ih =>
      have hstep := hrec (n + 1)
      have hfactor_nonneg : 0 ≤ 1 - chewi73StepSize (n + 1) :=
        one_sub_chewi73StepSize_nonneg (n + 1)
      have hmul :
          (1 - chewi73StepSize (n + 1)) * u (n + 1) ≤
            (1 - chewi73StepSize (n + 1)) *
              (2 * B / ((n : ℝ) + 2)) :=
        mul_le_mul_of_nonneg_left ih hfactor_nonneg
      have hbound :
          u (n + 2) ≤
            (1 - chewi73StepSize (n + 1)) *
                (2 * B / ((n : ℝ) + 2)) +
              (B * chewi73StepSize (n + 1) ^ (2 : ℕ)) / 2 := by
        nlinarith
      have harith :
          (1 - chewi73StepSize (n + 1)) *
              (2 * B / ((n : ℝ) + 2)) +
            (B * chewi73StepSize (n + 1) ^ (2 : ℕ)) / 2 ≤
              2 * B / (((n + 1 : ℕ) : ℝ) + 2) := by
        have hden1 : 0 < (n : ℝ) + 2 := by positivity
        have hden2 : 0 < (n : ℝ) + 3 := by positivity
        have hcast : (((n + 1 : ℕ) : ℝ) + 2) = (n : ℝ) + 3 := by
          norm_num [Nat.cast_add, Nat.cast_one]
          ring
        dsimp [chewi73StepSize]
        rw [hcast]
        have hcalc :
            (1 - 2 / ((n : ℝ) + 3)) *
                (2 * B / ((n : ℝ) + 2)) +
              (B * (2 / ((n : ℝ) + 3)) ^ (2 : ℕ)) / 2 =
                2 * B / ((n : ℝ) + 3) -
                  2 * B / (((n : ℝ) + 2) * ((n : ℝ) + 3) ^ (2 : ℕ)) := by
          field_simp [hden1.ne', hden2.ne']
          ring
        rw [hcalc]
        exact sub_le_self _
          (div_nonneg (mul_nonneg (by norm_num) hB_nonneg)
            (mul_nonneg hden1.le (sq_nonneg ((n : ℝ) + 3))))
      exact hbound.trans harith

/-- Source-indexed scalar form of the Frank-Wolfe rate. -/
theorem chewi73_scalar_rate {u : ℕ -> ℝ} {B : ℝ}
    (hB_nonneg : 0 ≤ B)
    (hrec : ∀ n : ℕ,
      u (n + 1) ≤
        (1 - chewi73StepSize n) * u n +
          (B * chewi73StepSize n ^ (2 : ℕ)) / 2)
    {N : ℕ} (hN : 1 ≤ N) :
    u N ≤ 2 * B / ((N : ℝ) + 1) := by
  cases N with
  | zero => omega
  | succ n =>
      have hden : (((n + 1 : ℕ) : ℝ) + 1) = (n : ℝ) + 2 := by
        norm_num [Nat.cast_add, Nat.cast_one]
        ring
      rw [hden]
      exact chewi73_scalar_rate_aux (u := u) (B := B) hB_nonneg hrec n

/-- Theorem 7.3 recurrence along a Frank-Wolfe trajectory. -/
theorem chewi73_gap_recurrence
    {C : Set E} {f : E -> ℝ} {grad loo : E -> E}
    {beta D : ℝ} {x : ℕ -> E} {xStar : E}
    (hfirst : FirstOrderStrongConvexOn C f grad 0)
    (hsmooth : SmoothWithGradientOn C f grad beta)
    (hloo : LinearOptimizationOracleOn C loo)
    (hdiam : HasDiameterBound C D)
    (hbeta_nonneg : 0 ≤ beta)
    (htraj : IsFrankWolfeTrajectory grad loo x)
    (hmem : ∀ n, x n ∈ C)
    (hxStar : xStar ∈ C) :
    ∀ n : ℕ,
      f (x (n + 1)) - f xStar ≤
        (1 - chewi73StepSize n) * (f (x n) - f xStar) +
          (beta * D ^ (2 : ℕ) *
            chewi73StepSize n ^ (2 : ℕ)) / 2 := by
  intro n
  rw [htraj n]
  exact
    frankWolfe_oneStep_gap_recurrence
      (C := C) (f := f) (grad := grad) (loo := loo)
      (beta := beta) (D := D) (h := chewi73StepSize n)
      (x := x n) (xStar := xStar)
      hfirst hsmooth hloo hdiam hbeta_nonneg
      (hmem n) hxStar
      (chewi73StepSize_nonneg n) (chewi73StepSize_le_one n)

/--
Chewi Theorem 7.3, supplied-interface form: Frank-Wolfe with
`h_n = 2/(n+2)` has the source rate
`f x_N - f_* <= 2 beta D^2 / (N+1)`.
-/
theorem chewi73_gap_le_two_beta_mul_diam_sq_div
    {C : Set E} {f : E -> ℝ} {grad loo : E -> E}
    {beta D : ℝ} {x : ℕ -> E} {xStar : E}
    (hfirst : FirstOrderStrongConvexOn C f grad 0)
    (hsmooth : SmoothWithGradientOn C f grad beta)
    (hloo : LinearOptimizationOracleOn C loo)
    (hdiam : HasDiameterBound C D)
    (hbeta_nonneg : 0 ≤ beta)
    (htraj : IsFrankWolfeTrajectory grad loo x)
    (hmem : ∀ n, x n ∈ C)
    (hxStar : xStar ∈ C)
    {N : ℕ} (hN : 1 ≤ N) :
    f (x N) - f xStar ≤
      2 * beta * D ^ (2 : ℕ) / ((N : ℝ) + 1) := by
  let B : ℝ := beta * D ^ (2 : ℕ)
  have hB_nonneg : 0 ≤ B :=
    mul_nonneg hbeta_nonneg (sq_nonneg D)
  have hrec : ∀ n : ℕ,
      (f (x (n + 1)) - f xStar) ≤
        (1 - chewi73StepSize n) * (f (x n) - f xStar) +
          (B * chewi73StepSize n ^ (2 : ℕ)) / 2 := by
    intro n
    simpa [B, mul_assoc, mul_comm, mul_left_comm] using
      chewi73_gap_recurrence
        (C := C) (f := f) (grad := grad) (loo := loo)
        (beta := beta) (D := D) (x := x) (xStar := xStar)
        hfirst hsmooth hloo hdiam hbeta_nonneg htraj hmem hxStar n
  simpa [B, mul_assoc, mul_comm, mul_left_comm] using
    chewi73_scalar_rate
      (u := fun n => f (x n) - f xStar)
      (B := B) hB_nonneg hrec hN

end Optimization
end StatInference
