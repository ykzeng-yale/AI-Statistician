import StatInference.Optimization.Theorem510

/-!
# Chewi Chapter 8 proximal-gradient layer

This module starts the Chapter 8 proximal-method lane.  It keeps the first
packet source-shaped and finite-valued: the nonsmooth part is represented by a
real-valued function `g`, and one proximal-gradient step is supplied by the
quadratic-growth certificate for the local model minimized in the PGD update.
-/

namespace StatInference
namespace Optimization

open Finset
open scoped InnerProductSpace

variable {E : Type*} [NormedAddCommGroup E] [InnerProductSpace ℝ E]

/-- The composite finite-valued objective `F = f + g` from Chewi Chapter 8. -/
def compositeObjective (f g : E -> ℝ) (x : E) : ℝ :=
  f x + g x

/--
The proximal-gradient local model at `x`, with the smooth part linearized and
the nonsmooth part left implicit.
-/
noncomputable def proximalGradientModel (f g : E -> ℝ) (grad : E -> E)
    (h : ℝ) (x z : E) : ℝ :=
  f x + inner ℝ (grad x) (z - x) + g z +
    (1 / (2 * h)) * ‖z - x‖ ^ (2 : ℕ)

/--
Source-shaped certificate that `xPlus` is one proximal-gradient step from `x`.

The growth field is the exact inequality used in Chewi's proof of Theorem 8.5:
the local model is `(alphaG + 1 / h)`-strongly convex and minimized at `xPlus`.
-/
structure IsProximalGradientStep
    (C : Set E) (f g : E -> ℝ) (grad : E -> E)
    (alphaG h : ℝ) (x xPlus : E) : Prop where
  mem_start : x ∈ C
  mem_next : xPlus ∈ C
  growth : ∀ ⦃y : E⦄, y ∈ C ->
    proximalGradientModel f g grad h x xPlus +
        ((alphaG + 1 / h) / 2) * ‖y - xPlus‖ ^ (2 : ℕ) ≤
      proximalGradientModel f g grad h x y

theorem proximalGradientModel_le_composite_add_sqdist
    {C : Set E} {f g : E -> ℝ} {grad : E -> E}
    {alphaF h : ℝ} {x y : E}
    (hfirst : FirstOrderStrongConvexOn C f grad alphaF)
    (hx : x ∈ C) (hy : y ∈ C) :
    proximalGradientModel f g grad h x y ≤
      compositeObjective f g y +
        (1 / (2 * h) - alphaF / 2) * ‖y - x‖ ^ (2 : ℕ) := by
  have hmodel := hfirst.lower_model hx hy
  unfold proximalGradientModel compositeObjective
  nlinarith

theorem composite_le_proximalGradientModel
    {C : Set E} {f g : E -> ℝ} {grad : E -> E}
    {betaF h : ℝ} {x xPlus : E}
    (hsmooth : SmoothWithGradientOn C f grad betaF)
    (hx : x ∈ C) (hxPlus : xPlus ∈ C)
    (hh : 0 < h) (hbeta_step : betaF * h ≤ 1) :
    compositeObjective f g xPlus ≤
      proximalGradientModel f g grad h x xPlus := by
  have hsmooth_model := hsmooth.upper_model hx hxPlus
  have hbeta_le_inv : betaF ≤ 1 / h := by
    exact (le_div_iff₀ hh).2 (by simpa using hbeta_step)
  have hcoeff :
      betaF / 2 ≤ 1 / (2 * h) := by
    have hhalf : betaF / 2 ≤ (1 / h) / 2 :=
      div_le_div_of_nonneg_right hbeta_le_inv (by norm_num)
    have hrewrite : (1 / h) / 2 = 1 / (2 * h) := by
      field_simp [hh.ne']
    simpa [hrewrite] using hhalf
  have hquad :
      (betaF / 2) * ‖xPlus - x‖ ^ (2 : ℕ) ≤
        (1 / (2 * h)) * ‖xPlus - x‖ ^ (2 : ℕ) :=
    mul_le_mul_of_nonneg_right hcoeff (sq_nonneg ‖xPlus - x‖)
  unfold compositeObjective proximalGradientModel
  nlinarith

/--
Chewi Theorem 8.5, one-step inequality (8.1), in supplied-interface form.

The only proximal-oracle assumption is the quadratic-growth/minimizer
certificate in `IsProximalGradientStep`; the rest is exactly the source proof:
first-order convexity of `f`, smoothness of `f`, and algebra.
-/
theorem proximalGradient_oneStep_ineq
    {C : Set E} {f g : E -> ℝ} {grad : E -> E}
    {alphaF alphaG betaF h : ℝ} {x xPlus y : E}
    (hfirst : FirstOrderStrongConvexOn C f grad alphaF)
    (hsmooth : SmoothWithGradientOn C f grad betaF)
    (hstep : IsProximalGradientStep C f g grad alphaG h x xPlus)
    (hh : 0 < h) (hbeta_step : betaF * h ≤ 1)
    (hy : y ∈ C) :
    (1 + alphaG * h) * ‖y - xPlus‖ ^ (2 : ℕ) ≤
      (1 - alphaF * h) * ‖y - x‖ ^ (2 : ℕ) -
        2 * h *
          (compositeObjective f g xPlus - compositeObjective f g y) := by
  have hgrowth := hstep.growth hy
  have hmodel_y :
      proximalGradientModel f g grad h x y ≤
        compositeObjective f g y +
          (1 / (2 * h) - alphaF / 2) * ‖y - x‖ ^ (2 : ℕ) :=
    proximalGradientModel_le_composite_add_sqdist
      hfirst hstep.mem_start hy
  have hmodel_next :
      compositeObjective f g xPlus ≤
        proximalGradientModel f g grad h x xPlus :=
    composite_le_proximalGradientModel
      hsmooth hstep.mem_start hstep.mem_next hh hbeta_step
  have hcore :
      ((alphaG + 1 / h) / 2) * ‖y - xPlus‖ ^ (2 : ℕ) ≤
        compositeObjective f g y +
          (1 / (2 * h) - alphaF / 2) * ‖y - x‖ ^ (2 : ℕ) -
            compositeObjective f g xPlus := by
    nlinarith
  have hmul := mul_le_mul_of_nonneg_left hcore (by nlinarith [hh.le])
      (a := 2 * h)
  have hleft :
      2 * h *
          (((alphaG + 1 / h) / 2) * ‖y - xPlus‖ ^ (2 : ℕ)) =
        (1 + alphaG * h) * ‖y - xPlus‖ ^ (2 : ℕ) := by
    field_simp [hh.ne']
    ring
  have hright :
      2 * h *
          (compositeObjective f g y +
            (1 / (2 * h) - alphaF / 2) * ‖y - x‖ ^ (2 : ℕ) -
              compositeObjective f g xPlus) =
        (1 - alphaF * h) * ‖y - x‖ ^ (2 : ℕ) -
          2 * h *
            (compositeObjective f g xPlus - compositeObjective f g y) := by
    field_simp [hh.ne']
    ring
  calc
    (1 + alphaG * h) * ‖y - xPlus‖ ^ (2 : ℕ)
        =
          2 * h *
            (((alphaG + 1 / h) / 2) * ‖y - xPlus‖ ^ (2 : ℕ)) := hleft.symm
    _ ≤
          2 * h *
            (compositeObjective f g y +
              (1 / (2 * h) - alphaF / 2) * ‖y - x‖ ^ (2 : ℕ) -
                compositeObjective f g xPlus) := hmul
    _ =
        (1 - alphaF * h) * ‖y - x‖ ^ (2 : ℕ) -
          2 * h *
            (compositeObjective f g xPlus - compositeObjective f g y) := hright

omit [InnerProductSpace ℝ E] in
/--
Chewi Theorem 8.5 final geometric denominator bound, supplied with the PGD
one-step inequality `(8.1)` and monotonicity of the composite objective gaps.

This reuses the already-compiled Theorem 3.4 weighted-recurrence machinery with
effective step size `h / (1 + alphaG * h)` and total convexity
`alphaF + alphaG`.
-/
theorem chewi85_final_gap_le_geometric_denominator_of_oneStep
    {F : E -> ℝ} {x : ℕ -> E} {xStar : E}
    {alphaF alphaG h : ℝ}
    (htotal_pos : 0 < alphaF + alphaG)
    (hh : 0 < h)
    (hden_pos : 0 < 1 + alphaG * h)
    (hfactor_pos : 0 < (1 - alphaF * h) / (1 + alphaG * h))
    {N : ℕ} (hN : N ≠ 0)
    (hone_step : ∀ n,
      (1 + alphaG * h) * ‖x (n + 1) - xStar‖ ^ (2 : ℕ) ≤
        (1 - alphaF * h) * ‖x n - xStar‖ ^ (2 : ℕ) -
          2 * h * (F (x (n + 1)) - F xStar))
    (hmono : ∀ n, n < N ->
      F (x N) - F xStar ≤ F (x (n + 1)) - F xStar) :
    F (x N) - F xStar ≤
      (alphaF + alphaG) * ‖x 0 - xStar‖ ^ (2 : ℕ) /
        (2 * ((((1 - alphaF * h) / (1 + alphaG * h)) ^ N)⁻¹ - 1)) := by
  let hEff : ℝ := h / (1 + alphaG * h)
  have hhEff : 0 < hEff := by
    exact div_pos hh hden_pos
  have hfactor_eq :
      1 - (alphaF + alphaG) * hEff =
        (1 - alphaF * h) / (1 + alphaG * h) := by
    dsimp [hEff]
    field_simp [hden_pos.ne']
    ring
  have hfactor_eff_pos :
      0 < 1 - (alphaF + alphaG) * hEff := by
    rw [hfactor_eq]
    exact hfactor_pos
  have hone_eff : ∀ n,
      ‖x (n + 1) - xStar‖ ^ (2 : ℕ) ≤
        (1 - (alphaF + alphaG) * hEff) *
            ‖x n - xStar‖ ^ (2 : ℕ) -
          2 * hEff * (F (x (n + 1)) - F xStar) := by
    intro n
    have hstep := hone_step n
    have hdiv :
        ‖x (n + 1) - xStar‖ ^ (2 : ℕ) ≤
          ((1 - alphaF * h) * ‖x n - xStar‖ ^ (2 : ℕ) -
            2 * h * (F (x (n + 1)) - F xStar)) /
              (1 + alphaG * h) := by
      have hstep' :
          ‖x (n + 1) - xStar‖ ^ (2 : ℕ) * (1 + alphaG * h) ≤
            (1 - alphaF * h) * ‖x n - xStar‖ ^ (2 : ℕ) -
              2 * h * (F (x (n + 1)) - F xStar) := by
        simpa [mul_comm, mul_left_comm, mul_assoc] using hstep
      exact (le_div_iff₀ hden_pos).2 hstep'
    calc
      ‖x (n + 1) - xStar‖ ^ (2 : ℕ)
          ≤ ((1 - alphaF * h) * ‖x n - xStar‖ ^ (2 : ℕ) -
            2 * h * (F (x (n + 1)) - F xStar)) /
              (1 + alphaG * h) := hdiv
      _ =
        ((1 - alphaF * h) / (1 + alphaG * h)) *
            ‖x n - xStar‖ ^ (2 : ℕ) -
          2 * (h / (1 + alphaG * h)) *
            (F (x (n + 1)) - F xStar) := by
            field_simp [hden_pos.ne']
      _ =
        (1 - (alphaF + alphaG) * hEff) *
            ‖x n - xStar‖ ^ (2 : ℕ) -
          2 * hEff * (F (x (n + 1)) - F xStar) := by
            simp [hEff, hfactor_eq]
  have hbound :=
    chewi34_final_gap_le_geometric_denominator_of_one_step
      (f := F) (x := x) (xStar := xStar)
      (alpha := alphaF + alphaG) (h := hEff)
      htotal_pos hhEff hfactor_eff_pos hN hone_eff hmono
  simpa [hfactor_eq] using hbound

/--
Source-shaped accelerated proximal-gradient trajectory for Chewi Theorem 8.6.

The sequence `y` is the Nesterov trial point sequence, and each `x (n+1)` is a
PGD step from `y n` with step size `1 / beta`.
-/
def IsChewi86APGDTrajectory
    (C : Set E) (f g : E -> ℝ) (grad : E -> E) (beta : ℝ)
    (x y : ℕ -> E) : Prop :=
  y 0 = x 0 ∧
    (∀ n, y (n + 1) =
      x (n + 1) + chewi510Theta (n + 1) • (x (n + 1) - x n)) ∧
    ∀ n, IsProximalGradientStep C f g grad 0 (1 / beta) (y n) (x (n + 1))

theorem IsChewi86APGDTrajectory.y_zero
    {C : Set E} {f g : E -> ℝ} {grad : E -> E} {beta : ℝ}
    {x y : ℕ -> E}
    (h : IsChewi86APGDTrajectory C f g grad beta x y) :
    y 0 = x 0 :=
  h.1

theorem IsChewi86APGDTrajectory.y_succ
    {C : Set E} {f g : E -> ℝ} {grad : E -> E} {beta : ℝ}
    {x y : ℕ -> E}
    (h : IsChewi86APGDTrajectory C f g grad beta x y) (n : ℕ) :
    y (n + 1) =
      x (n + 1) + chewi510Theta (n + 1) • (x (n + 1) - x n) :=
  h.2.1 n

theorem IsChewi86APGDTrajectory.step
    {C : Set E} {f g : E -> ℝ} {grad : E -> E} {beta : ℝ}
    {x y : ℕ -> E}
    (h : IsChewi86APGDTrajectory C f g grad beta x y) (n : ℕ) :
    IsProximalGradientStep C f g grad 0 (1 / beta) (y n) (x (n + 1)) :=
  h.2.2 n

theorem IsChewi86APGDTrajectory.telescopeAlignment
    {C : Set E} {f g : E -> ℝ} {grad : E -> E} {beta : ℝ}
    {x y : ℕ -> E}
    (h : IsChewi86APGDTrajectory C f g grad beta x y) (n : ℕ) :
    chewi510Lambda (n + 1) • x (n + 1) -
        (chewi510Lambda (n + 1) - 1) • x n =
      chewi510Lambda (n + 2) • y (n + 1) -
        (chewi510Lambda (n + 2) - 1) • x (n + 1) :=
  chewi510_telescopeAlignment_of_trial_succ x y n (h.y_succ n)

theorem IsChewi86APGDTrajectory.energyVector_zero
    {C : Set E} {f g : E -> ℝ} {grad : E -> E} {beta : ℝ}
    {x y : ℕ -> E}
    (h : IsChewi86APGDTrajectory C f g grad beta x y)
    {xStar : E} :
    chewi510EnergyVector x y xStar 0 = x 0 - xStar := by
  unfold chewi510EnergyVector
  simp [h.y_zero]

/--
PGD analogue of the Chapter 5.10 inner-product one-step form.  This is the
formal replacement of GD `(3.3)` by Chewi `(8.1)` in the APGD proof.
-/
theorem proximalGradient_gap_le_inner_form
    {C : Set E} {f g : E -> ℝ} {grad : E -> E} {beta : ℝ}
    {y xPlus z : E}
    (hfirst : FirstOrderStrongConvexOn C f grad 0)
    (hsmooth : SmoothWithGradientOn C f grad beta)
    (hstep : IsProximalGradientStep C f g grad 0 (1 / beta) y xPlus)
    (hz : z ∈ C)
    (hbeta_pos : 0 < beta) :
    compositeObjective f g xPlus - compositeObjective f g z ≤
      -(beta / 2) * ‖xPlus - y‖ ^ (2 : ℕ) -
        beta * inner ℝ (xPlus - y) (y - z) := by
  have hone :
      ‖xPlus - z‖ ^ (2 : ℕ) ≤
        ‖y - z‖ ^ (2 : ℕ) -
          (2 / beta) *
          (compositeObjective f g xPlus - compositeObjective f g z) := by
    have hstepSize : beta * (1 / beta) ≤ 1 := by
      field_simp [hbeta_pos.ne']
      norm_num
    have hraw :=
      proximalGradient_oneStep_ineq
        (C := C) (f := f) (g := g) (grad := grad)
        (alphaF := 0) (alphaG := 0) (betaF := beta)
        (h := 1 / beta) (x := y) (xPlus := xPlus) (y := z)
        hfirst hsmooth hstep (one_div_pos.mpr hbeta_pos) hstepSize hz
    simpa [norm_sub_rev, one_div, div_eq_mul_inv, mul_assoc] using hraw
  have hgap :=
    chewi510_gap_le_norm_sq_diff_of_oneStep
      (beta := beta)
      (A := ‖y - z‖ ^ (2 : ℕ))
      (B := ‖xPlus - z‖ ^ (2 : ℕ))
      (gap := compositeObjective f g xPlus - compositeObjective f g z)
      hone hbeta_pos
  have hident :=
    chewi510_norm_sq_diff_step_identity beta xPlus y z
  exact hgap.trans_eq hident

/--
The APGD two-point estimate for Chapter 8.6, in the same telescope-ready form
as the Chapter 5.10 AGD proof.
-/
theorem chewi86_weighted_two_point_bound_telescope
    {C : Set E} {f g : E -> ℝ} {grad : E -> E} {beta : ℝ}
    {x y : ℕ -> E} {xStar : E} (n : ℕ)
    (hfirst : FirstOrderStrongConvexOn C f grad 0)
    (hsmooth : SmoothWithGradientOn C f grad beta)
    (htraj : IsChewi86APGDTrajectory C f g grad beta x y)
    (hx_mem : ∀ k, x k ∈ C)
    (hxStar_mem : xStar ∈ C)
    (hbeta_pos : 0 < beta) :
    (chewi510Lambda (n + 1) - 1) *
        (compositeObjective f g (x (n + 1)) -
          compositeObjective f g (x n)) +
      (compositeObjective f g (x (n + 1)) -
        compositeObjective f g xStar) ≤
      beta / (2 * chewi510Lambda (n + 1)) *
        (‖chewi510EnergyVector x y xStar n‖ ^ (2 : ℕ) -
          ‖chewi510EnergyVector x y xStar (n + 1)‖ ^ (2 : ℕ)) := by
  have hstep := htraj.step n
  have hgapX :
      compositeObjective f g (x (n + 1)) - compositeObjective f g (x n) ≤
        -(beta / 2) * ‖x (n + 1) - y n‖ ^ (2 : ℕ) -
          beta * inner ℝ (x (n + 1) - y n) (y n - x n) :=
    proximalGradient_gap_le_inner_form
      (C := C) (f := f) (g := g) (grad := grad) (beta := beta)
      (y := y n) (xPlus := x (n + 1)) (z := x n)
      hfirst hsmooth hstep (hx_mem n) hbeta_pos
  have hgapStar :
      compositeObjective f g (x (n + 1)) - compositeObjective f g xStar ≤
        -(beta / 2) * ‖x (n + 1) - y n‖ ^ (2 : ℕ) -
          beta * inner ℝ (x (n + 1) - y n) (y n - xStar) :=
    proximalGradient_gap_le_inner_form
      (C := C) (f := f) (g := g) (grad := grad) (beta := beta)
      (y := y n) (xPlus := x (n + 1)) (z := xStar)
      hfirst hsmooth hstep hxStar_mem hbeta_pos
  have hscaled :=
    chewi510_weighted_two_gap_le_scaled_norm_diff
      (beta := beta) (lambda := chewi510Lambda (n + 1))
      (gapX := compositeObjective f g (x (n + 1)) -
        compositeObjective f g (x n))
      (gapStar := compositeObjective f g (x (n + 1)) -
        compositeObjective f g xStar)
      (a := x (n + 1) - y n) (y := y n) (x := x n)
      (xStar := xStar)
      (chewi510Lambda_pos_succ n) (chewi510Lambda_one_le_succ n)
      hgapX hgapStar
  have hrewrite :
      chewi510Lambda (n + 1) • y n -
            (chewi510Lambda (n + 1) - 1) • x n - xStar +
          chewi510Lambda (n + 1) • (x (n + 1) - y n) =
        chewi510Lambda (n + 1) • x (n + 1) -
            (chewi510Lambda (n + 1) - 1) • x n - xStar := by
    module
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
  simpa [chewi510EnergyVector, hrewrite, hsecond] using hscaled

/-- Summed APGD estimate for Chewi Theorem 8.6. -/
theorem chewi86_weighted_sum_bound
    {C : Set E} {f g : E -> ℝ} {grad : E -> E} {beta : ℝ}
    {x y : ℕ -> E} {xStar : E} (N : ℕ)
    (hfirst : FirstOrderStrongConvexOn C f grad 0)
    (hsmooth : SmoothWithGradientOn C f grad beta)
    (htraj : IsChewi86APGDTrajectory C f g grad beta x y)
    (hx_mem : ∀ k, x k ∈ C)
    (hxStar_mem : xStar ∈ C)
    (hbeta_pos : 0 < beta) :
    (∑ n ∈ Finset.range N,
        (chewi510Lambda (n + 1) ^ (2 : ℕ) *
            (compositeObjective f g (x (n + 1)) -
              compositeObjective f g xStar) -
          chewi510Lambda n ^ (2 : ℕ) *
            (compositeObjective f g (x n) -
              compositeObjective f g xStar))) ≤
      beta / 2 *
        (‖chewi510EnergyVector x y xStar 0‖ ^ (2 : ℕ) -
          ‖chewi510EnergyVector x y xStar N‖ ^ (2 : ℕ)) := by
  let gap : ℕ -> ℝ := fun k => compositeObjective f g (x k) -
    compositeObjective f g xStar
  let energySq : ℕ -> ℝ :=
    fun k => ‖chewi510EnergyVector x y xStar k‖ ^ (2 : ℕ)
  have hstep : ∀ n,
      (chewi510Lambda (n + 1) - 1) * (gap (n + 1) - gap n) +
          gap (n + 1) ≤
        beta / (2 * chewi510Lambda (n + 1)) *
          (energySq n - energySq (n + 1)) := by
    intro n
    have hp :=
      chewi86_weighted_two_point_bound_telescope
        (C := C) (f := f) (g := g) (grad := grad) (beta := beta)
        (x := x) (y := y) (xStar := xStar) n
        hfirst hsmooth htraj hx_mem hxStar_mem hbeta_pos
    have hleft :
        (chewi510Lambda (n + 1) - 1) * (gap (n + 1) - gap n) +
            gap (n + 1) =
          (chewi510Lambda (n + 1) - 1) *
              (compositeObjective f g (x (n + 1)) -
                compositeObjective f g (x n)) +
            (compositeObjective f g (x (n + 1)) -
              compositeObjective f g xStar) := by
      simp [gap]
    simpa [energySq, hleft] using hp
  simpa [gap, energySq] using
    chewi510_weighted_sum_bound_of_step beta gap energySq N hstep

/-- Chewi Theorem 8.6 APGD/FISTA rate in supplied-interface form. -/
theorem chewi86_gap_le_two_beta_dist_sq_over_nat_sq
    {C : Set E} {f g : E -> ℝ} {grad : E -> E} {beta : ℝ}
    {x y : ℕ -> E} {xStar : E} {N : ℕ}
    (hfirst : FirstOrderStrongConvexOn C f grad 0)
    (hsmooth : SmoothWithGradientOn C f grad beta)
    (htraj : IsChewi86APGDTrajectory C f g grad beta x y)
    (hx_mem : ∀ k, x k ∈ C)
    (hxStar_mem : xStar ∈ C)
    (hbeta_pos : 0 < beta)
    (hN : N ≠ 0) :
    compositeObjective f g (x N) - compositeObjective f g xStar ≤
      2 * beta * ‖x 0 - xStar‖ ^ (2 : ℕ) / (N : ℝ) ^ (2 : ℕ) := by
  have hsum :=
    chewi86_weighted_sum_bound
      (C := C) (f := f) (g := g) (grad := grad) (beta := beta)
      (x := x) (y := y) (xStar := xStar) N
      hfirst hsmooth htraj hx_mem hxStar_mem hbeta_pos
  have htel :=
    chewi510_weighted_sum_telescope
      (fun k => compositeObjective f g (x k) - compositeObjective f g xStar) N
  rw [htel] at hsum
  have hmain :
      chewi510Lambda N ^ (2 : ℕ) *
          (compositeObjective f g (x N) - compositeObjective f g xStar) ≤
        beta / 2 * ‖chewi510EnergyVector x y xStar 0‖ ^ (2 : ℕ) := by
    have hsum' :
        chewi510Lambda N ^ (2 : ℕ) *
            (compositeObjective f g (x N) - compositeObjective f g xStar) ≤
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
      have hcoef_nonneg : 0 ≤ beta / 2 := by positivity
      have hdiff :
          ‖chewi510EnergyVector x y xStar 0‖ ^ (2 : ℕ) -
              ‖chewi510EnergyVector x y xStar N‖ ^ (2 : ℕ) ≤
            ‖chewi510EnergyVector x y xStar 0‖ ^ (2 : ℕ) := by
        nlinarith
      exact mul_le_mul_of_nonneg_left hdiff hcoef_nonneg
    exact hsum'.trans hdrop
  have hmain' :
      chewi510Lambda N ^ (2 : ℕ) *
          (compositeObjective f g (x N) - compositeObjective f g xStar) ≤
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
  have hden :
      compositeObjective f g (x N) - compositeObjective f g xStar ≤
        (beta / 2 * ‖x 0 - xStar‖ ^ (2 : ℕ)) /
          chewi510Lambda N ^ (2 : ℕ) := by
    apply (le_div_iff₀ hden_pos).mpr
    nlinarith
  have hN_pos : 0 < (N : ℝ) := by
    exact_mod_cast Nat.pos_of_ne_zero hN
  have hhalf_pos : 0 < (N : ℝ) / 2 := by positivity
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
    simpa [div_eq_mul_inv, mul_assoc] using
      mul_le_mul_of_nonneg_left hinv_le' hcoef_nonneg
  have hfinal_rhs :
      (beta / 2 * ‖x 0 - xStar‖ ^ (2 : ℕ)) /
          (((N : ℝ) / 2) ^ (2 : ℕ)) =
        2 * beta * ‖x 0 - xStar‖ ^ (2 : ℕ) /
          (N : ℝ) ^ (2 : ℕ) := by
    field_simp [hN_pos.ne']
  exact hden.trans (hcompare.trans_eq hfinal_rhs)

end Optimization
end StatInference
