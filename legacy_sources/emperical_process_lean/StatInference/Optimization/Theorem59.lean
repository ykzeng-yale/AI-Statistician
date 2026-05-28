import StatInference.Optimization.Theorem58

/-!
# Chewi Theorem 5.9 strongly-convex accelerated gradient-flow layer

Chewi states the strongly-convex AGF convergence theorem and leaves the proof
to Exercise 5.3.  This module starts the reusable Lyapunov route.  The natural
energy is
`f x_t - f_* + 1 / 2 * ‖p_t + sqrt(alpha) • (x_t - x_*)‖^2`,
which is equivalent to the source-style shifted point
`x_t + (1 / sqrt(alpha)) • p_t` when `alpha > 0`.
-/

namespace StatInference
namespace Optimization

open Set Filter
open scoped Topology
open scoped InnerProductSpace

variable {E : Type*} [NormedAddCommGroup E] [InnerProductSpace ℝ E]

/-- Chewi Theorem 5.9 constant friction `γ_t = 2 sqrt(alpha)`. -/
noncomputable def chewi59Friction (alpha : ℝ) (_t : ℝ) : ℝ :=
  2 * Real.sqrt alpha

/-- Source-shaped AGF interface for Chewi Theorem 5.9. -/
def IsChewi59AcceleratedGradientFlowTrajectory (alpha : ℝ)
    (grad : E -> E) (x p : ℝ -> E) : Prop :=
  IsAcceleratedGradientFlowTrajectory grad (chewi59Friction alpha) x p

/--
The strongly-convex AGF Lyapunov vector
`p_t + sqrt(alpha) • (x_t - x_*)`.
-/
noncomputable def chewi59EnergyVector (alpha : ℝ)
    (x p : ℝ -> E) (xStar : E) (t : ℝ) : E :=
  p t + Real.sqrt alpha • (x t - xStar)

/--
Chewi Theorem 5.9 Lyapunov energy:
`f x_t - f_* + 1/2 ‖p_t + sqrt(alpha) • (x_t - x_*)‖^2`.
-/
noncomputable def chewi59Lyapunov (alpha : ℝ) (f : E -> ℝ) (fstar : ℝ)
    (x p : ℝ -> E) (xStar : E) (t : ℝ) : ℝ :=
  f (x t) - fstar +
    ((1 : ℝ) / 2) * ‖chewi59EnergyVector alpha x p xStar t‖ ^ (2 : ℕ)

/-- Function-gap derivative along a generic AGF trajectory. -/
theorem agf_gap_hasDerivAt
    [CompleteSpace E] {f : E -> ℝ} {grad : E -> E} {gamma : ℝ -> ℝ}
    {x p : ℝ -> E} {fstar t : ℝ}
    (hgrad : ∀ z, HasGradientAt f (grad z) z)
    (hflow : IsAcceleratedGradientFlowTrajectory grad gamma x p) :
    HasDerivAt (fun s => f (x s) - fstar)
      (inner ℝ (grad (x t)) (p t)) t := by
  have hcomp :=
    (hgrad (x t)).hasFDerivAt.comp_hasDerivAt (x := t) (hflow.1 t)
  simpa [InnerProductSpace.toDual_apply_apply] using hcomp.sub_const fstar

/--
Derivative of the Theorem 5.9 Lyapunov vector.  The constant friction
`2 sqrt(alpha)` leaves `q'_t = -∇f(x_t) - sqrt(alpha) p_t`.
-/
theorem chewi59EnergyVector_hasDerivAt
    {alpha : ℝ} {grad : E -> E} {x p : ℝ -> E} {xStar : E} {t : ℝ}
    (hflow : IsChewi59AcceleratedGradientFlowTrajectory alpha grad x p) :
    HasDerivAt (chewi59EnergyVector alpha x p xStar)
      (-(grad (x t)) - Real.sqrt alpha • p t) t := by
  have hpos :
      HasDerivAt (fun s => x s - xStar) (p t) t := by
    simpa using (hflow.1 t).sub_const xStar
  have hscaled :
      HasDerivAt
        (fun s => Real.sqrt alpha • (x s - xStar))
        (Real.sqrt alpha • p t) t := by
    simpa using hpos.const_smul (Real.sqrt alpha)
  have hraw :
      HasDerivAt
        (fun s => p s + Real.sqrt alpha • (x s - xStar))
        ((-(grad (x t)) - chewi59Friction alpha t • p t) +
          Real.sqrt alpha • p t) t :=
    (hflow.2 t).add hscaled
  have hderiv :
      (-(grad (x t)) - chewi59Friction alpha t • p t) +
          Real.sqrt alpha • p t =
        -(grad (x t)) - Real.sqrt alpha • p t := by
    rw [chewi59Friction]
    module
  have hraw' :
      HasDerivAt
        (fun s => p s + Real.sqrt alpha • (x s - xStar))
        (-(grad (x t)) - Real.sqrt alpha • p t) t := by
    convert hraw using 1
    exact hderiv.symm
  simpa [chewi59EnergyVector] using hraw'

/--
Raw derivative formula for the strongly-convex AGF Lyapunov energy.  The next
layer simplifies this expression with strong convexity to obtain
`L'_t <= -sqrt(alpha) * L_t`.
-/
theorem chewi59Lyapunov_hasDerivAt_raw
    [CompleteSpace E] {alpha : ℝ} {f : E -> ℝ} {grad : E -> E}
    {fstar : ℝ} {x p : ℝ -> E} {xStar : E} {t : ℝ}
    (hgrad : ∀ z, HasGradientAt f (grad z) z)
    (hflow : IsChewi59AcceleratedGradientFlowTrajectory alpha grad x p) :
    HasDerivAt (chewi59Lyapunov alpha f fstar x p xStar)
      (inner ℝ (grad (x t)) (p t) +
        inner ℝ (chewi59EnergyVector alpha x p xStar t)
          (-(grad (x t)) - Real.sqrt alpha • p t)) t := by
  have hgap :
      HasDerivAt (fun s => f (x s) - fstar)
        (inner ℝ (grad (x t)) (p t)) t :=
    agf_gap_hasDerivAt hgrad hflow
  have henergy :
      HasDerivAt (chewi59EnergyVector alpha x p xStar)
        (-(grad (x t)) - Real.sqrt alpha • p t) t :=
    chewi59EnergyVector_hasDerivAt hflow
  have hnorm := henergy.norm_sq
  have hscaled := hnorm.const_mul ((1 : ℝ) / 2)
  convert hgap.add hscaled using 1
  ring

/--
The algebraic heart of Chewi Theorem 5.9.  If strong convexity supplies the
gap bound `gap <= <g,d> - alpha/2 * ‖d‖²`, then the raw AGF Lyapunov
derivative is bounded by `-sqrt(alpha)` times the Lyapunov energy.
-/
theorem chewi59LyapunovDerivative_le_neg_sqrt_mul_of_gap_bound
    {alpha gap : ℝ} {g v d : E}
    (halpha_nonneg : 0 ≤ alpha)
    (hgap : gap ≤
      inner ℝ g d - (alpha / 2) * ‖d‖ ^ (2 : ℕ)) :
    inner ℝ g v +
        inner ℝ (v + Real.sqrt alpha • d)
          (-g - Real.sqrt alpha • v) ≤
      -Real.sqrt alpha *
        (gap +
          ((1 : ℝ) / 2) *
            ‖v + Real.sqrt alpha • d‖ ^ (2 : ℕ)) := by
  set r : ℝ := Real.sqrt alpha
  have hr_nonneg : 0 ≤ r := by
    simp [r]
  have hr_sq : r ^ (2 : ℕ) = alpha := by
    simpa [r] using Real.sq_sqrt halpha_nonneg
  have hnorm :
      ‖v + r • d‖ ^ (2 : ℕ) =
        ‖v‖ ^ (2 : ℕ) +
          2 * r * inner ℝ v d +
            alpha * ‖d‖ ^ (2 : ℕ) := by
    rw [norm_add_sq_real, norm_smul, Real.norm_of_nonneg hr_nonneg]
    simp [inner_smul_right]
    rw [← hr_sq]
    ring
  have hderiv :
      inner ℝ g v + inner ℝ (v + r • d) (-g - r • v) =
        -r * ‖v‖ ^ (2 : ℕ) - r * inner ℝ g d -
          alpha * inner ℝ v d := by
    simp [sub_eq_add_neg, inner_add_left, inner_add_right, inner_neg_right,
      inner_smul_left, inner_smul_right, real_inner_comm]
    rw [← hr_sq]
    ring
  have hgap_scaled :
      -r * inner ℝ g d ≤
        -r * gap - r * (alpha / 2) * ‖d‖ ^ (2 : ℕ) := by
    have hmul := mul_le_mul_of_nonneg_left hgap hr_nonneg
    nlinarith
  have hvel_half :
      -r * ‖v‖ ^ (2 : ℕ) ≤
        -(r / 2) * ‖v‖ ^ (2 : ℕ) := by
    have hv_nonneg : 0 ≤ ‖v‖ ^ (2 : ℕ) := sq_nonneg _
    nlinarith
  change
    inner ℝ g v + inner ℝ (v + r • d) (-g - r • v) ≤
      -r * (gap + ((1 : ℝ) / 2) * ‖v + r • d‖ ^ (2 : ℕ))
  rw [hderiv, hnorm]
  calc
    -r * ‖v‖ ^ (2 : ℕ) - r * inner ℝ g d -
        alpha * inner ℝ v d
        ≤ -r * ‖v‖ ^ (2 : ℕ) +
            (-r * gap - r * (alpha / 2) * ‖d‖ ^ (2 : ℕ)) -
              alpha * inner ℝ v d := by
          nlinarith [hgap_scaled]
    _ ≤ -(r / 2) * ‖v‖ ^ (2 : ℕ) +
            (-r * gap - r * (alpha / 2) * ‖d‖ ^ (2 : ℕ)) -
              alpha * inner ℝ v d := by
          nlinarith [hvel_half]
    _ = -r *
          (gap +
            ((1 : ℝ) / 2) *
              (‖v‖ ^ (2 : ℕ) + 2 * r * inner ℝ v d +
                alpha * ‖d‖ ^ (2 : ℕ))) := by
          rw [← hr_sq]
          ring

/--
Strong-convexity consumer for the raw Theorem 5.9 derivative formula.
-/
theorem chewi59LyapunovDerivative_le_neg_sqrt_mul_of_firstOrderStrongConvex
    {alpha : ℝ} {f : E -> ℝ} {grad : E -> E} {fstar L' : ℝ}
    {x p : ℝ -> E} {xStar : E} {t : ℝ}
    (hfirst : FirstOrderStrongConvexOn Set.univ f grad alpha)
    (hfxStar : f xStar = fstar)
    (halpha_nonneg : 0 ≤ alpha)
    (hL' : L' =
      inner ℝ (grad (x t)) (p t) +
        inner ℝ (chewi59EnergyVector alpha x p xStar t)
          (-(grad (x t)) - Real.sqrt alpha • p t)) :
    L' ≤
      -Real.sqrt alpha * chewi59Lyapunov alpha f fstar x p xStar t := by
  have hmodel :=
    hfirst.lower_model (x := x t) (by simp) (y := xStar) (by simp)
  have hinner :
      inner ℝ (grad (x t)) (xStar - x t) =
        -inner ℝ (grad (x t)) (x t - xStar) := by
    have hsub : xStar - x t = -(x t - xStar) := by abel
    rw [hsub, inner_neg_right]
  have hgap :
      f (x t) - fstar ≤
        inner ℝ (grad (x t)) (x t - xStar) -
          (alpha / 2) * ‖x t - xStar‖ ^ (2 : ℕ) := by
    rw [hinner, hfxStar, norm_sub_rev] at hmodel
    nlinarith
  have h :=
    chewi59LyapunovDerivative_le_neg_sqrt_mul_of_gap_bound
      (alpha := alpha) (gap := f (x t) - fstar)
      (g := grad (x t)) (v := p t) (d := x t - xStar)
      halpha_nonneg hgap
  rw [hL']
  simpa [chewi59EnergyVector, chewi59Lyapunov] using h

/-- The objective gap is bounded by the Theorem 5.9 Lyapunov energy. -/
theorem chewi59_gap_le_lyapunov
    {alpha : ℝ} {f : E -> ℝ} {fstar : ℝ}
    {x p : ℝ -> E} {xStar : E} {t : ℝ} :
    f (x t) - fstar ≤ chewi59Lyapunov alpha f fstar x p xStar t := by
  have hnonneg :
      0 ≤ ((1 : ℝ) / 2) *
        ‖chewi59EnergyVector alpha x p xStar t‖ ^ (2 : ℕ) := by
    have hsq :
        0 ≤ ‖chewi59EnergyVector alpha x p xStar t‖ ^ (2 : ℕ) :=
      sq_nonneg _
    nlinarith
  dsimp [chewi59Lyapunov]
  nlinarith

/--
Theorem 5.9 Lyapunov exponential decay from the raw derivative formula and
the strong-convexity derivative bound.
-/
theorem chewi59Lyapunov_le_exp_decay_of_firstOrderStrongConvex
    [CompleteSpace E] {alpha : ℝ} {f : E -> ℝ} {grad : E -> E}
    {fstar : ℝ} {x p : ℝ -> E} {xStar : E} {t : ℝ}
    (hfirst : FirstOrderStrongConvexOn Set.univ f grad alpha)
    (hgrad : ∀ z, HasGradientAt f (grad z) z)
    (hflow : IsChewi59AcceleratedGradientFlowTrajectory alpha grad x p)
    (hfxStar : f xStar = fstar)
    (halpha_nonneg : 0 ≤ alpha)
    (ht : 0 ≤ t) :
    chewi59Lyapunov alpha f fstar x p xStar t ≤
      chewi59Lyapunov alpha f fstar x p xStar 0 *
        Real.exp (-(Real.sqrt alpha * t)) := by
  let L' : ℝ -> ℝ := fun s =>
    inner ℝ (grad (x s)) (p s) +
      inner ℝ (chewi59EnergyVector alpha x p xStar s)
        (-(grad (x s)) - Real.sqrt alpha • p s)
  refine scalarExpDecay_le_of_hasDerivAt_le
    (u := chewi59Lyapunov alpha f fstar x p xStar)
    (u' := L') (c := Real.sqrt alpha) ?_ ?_ ht
  · intro s
    exact chewi59Lyapunov_hasDerivAt_raw hgrad hflow
  · intro s
    exact chewi59LyapunovDerivative_le_neg_sqrt_mul_of_firstOrderStrongConvex
      (f := f) (grad := grad) (fstar := fstar) (x := x) (p := p)
      (xStar := xStar) hfirst hfxStar halpha_nonneg rfl

/-- Theorem 5.9 gap bound with the initial Lyapunov energy still explicit. -/
theorem chewi59_gap_le_initial_lyapunov_exp_decay
    [CompleteSpace E] {alpha : ℝ} {f : E -> ℝ} {grad : E -> E}
    {fstar : ℝ} {x p : ℝ -> E} {xStar : E} {t : ℝ}
    (hfirst : FirstOrderStrongConvexOn Set.univ f grad alpha)
    (hgrad : ∀ z, HasGradientAt f (grad z) z)
    (hflow : IsChewi59AcceleratedGradientFlowTrajectory alpha grad x p)
    (hfxStar : f xStar = fstar)
    (halpha_nonneg : 0 ≤ alpha)
    (ht : 0 ≤ t) :
    f (x t) - fstar ≤
      chewi59Lyapunov alpha f fstar x p xStar 0 *
        Real.exp (-(Real.sqrt alpha * t)) := by
  exact chewi59_gap_le_lyapunov.trans
    (chewi59Lyapunov_le_exp_decay_of_firstOrderStrongConvex
      hfirst hgrad hflow hfxStar halpha_nonneg ht)

/-- At zero momentum, the Theorem 5.9 Lyapunov vector starts at `sqrt(alpha) • (x_0 - x_*)`. -/
theorem chewi59EnergyVector_zero_of_momentum_zero
    (alpha : ℝ) (x p : ℝ -> E) (xStar : E)
    (hp0 : p 0 = 0) :
    chewi59EnergyVector alpha x p xStar 0 =
      Real.sqrt alpha • (x 0 - xStar) := by
  simp [chewi59EnergyVector, hp0]

/--
With zero initial momentum and a stationary minimizer, the initial Theorem 5.9
Lyapunov energy is at most twice the initial function gap.
-/
theorem chewi59Lyapunov_zero_le_two_gap_of_momentum_zero
    {alpha : ℝ} {f : E -> ℝ} {grad : E -> E} {fstar : ℝ}
    {x p : ℝ -> E} {xStar : E}
    (hfirst : FirstOrderStrongConvexOn Set.univ f grad alpha)
    (hfxStar : f xStar = fstar)
    (halpha_nonneg : 0 ≤ alpha)
    (hgradStar : grad xStar = 0)
    (hp0 : p 0 = 0) :
    chewi59Lyapunov alpha f fstar x p xStar 0 ≤
      2 * (f (x 0) - fstar) := by
  have hmodel :=
    hfirst.lower_model (x := xStar) (by simp) (y := x 0) (by simp)
  have hquad_le_gap :
      (alpha / 2) * ‖x 0 - xStar‖ ^ (2 : ℕ) ≤
        f (x 0) - fstar := by
    have hmodel' :
        fstar + (alpha / 2) * ‖x 0 - xStar‖ ^ (2 : ℕ) ≤
          f (x 0) := by
      simpa [hfxStar, hgradStar] using hmodel
    nlinarith
  have henergy0 :
      chewi59EnergyVector alpha x p xStar 0 =
        Real.sqrt alpha • (x 0 - xStar) :=
    chewi59EnergyVector_zero_of_momentum_zero alpha x p xStar hp0
  have hnorm0 :
      ‖chewi59EnergyVector alpha x p xStar 0‖ ^ (2 : ℕ) =
        alpha * ‖x 0 - xStar‖ ^ (2 : ℕ) := by
    rw [henergy0, norm_smul, Real.norm_of_nonneg (Real.sqrt_nonneg alpha)]
    nlinarith [Real.sq_sqrt halpha_nonneg]
  dsimp [chewi59Lyapunov]
  rw [hnorm0]
  nlinarith

/--
Chewi Theorem 5.9 source-shaped exponential gap bound, with stationarity of
the reference minimizer supplied explicitly.
-/
theorem chewi59_gap_le_exp_decay_of_firstOrderStrongConvex
    [CompleteSpace E] {alpha : ℝ} {f : E -> ℝ} {grad : E -> E}
    {fstar : ℝ} {x p : ℝ -> E} {xStar : E} {t : ℝ}
    (hfirst : FirstOrderStrongConvexOn Set.univ f grad alpha)
    (hgrad : ∀ z, HasGradientAt f (grad z) z)
    (hflow : IsChewi59AcceleratedGradientFlowTrajectory alpha grad x p)
    (hfxStar : f xStar = fstar)
    (halpha_nonneg : 0 ≤ alpha)
    (hgradStar : grad xStar = 0)
    (hp0 : p 0 = 0)
    (ht : 0 ≤ t) :
    f (x t) - fstar ≤
      2 * Real.exp (-(Real.sqrt alpha * t)) *
        (f (x 0) - fstar) := by
  have hgap :=
    chewi59_gap_le_initial_lyapunov_exp_decay
      hfirst hgrad hflow hfxStar halpha_nonneg ht
  have hL0 :=
    chewi59Lyapunov_zero_le_two_gap_of_momentum_zero
      (f := f) (grad := grad) (fstar := fstar) (x := x) (p := p)
      (xStar := xStar)
      hfirst hfxStar halpha_nonneg hgradStar hp0
  have hmul :=
    mul_le_mul_of_nonneg_right hL0
      (Real.exp_nonneg (-(Real.sqrt alpha * t)))
  calc
    f (x t) - fstar
        ≤ chewi59Lyapunov alpha f fstar x p xStar 0 *
            Real.exp (-(Real.sqrt alpha * t)) := hgap
    _ ≤ (2 * (f (x 0) - fstar)) *
          Real.exp (-(Real.sqrt alpha * t)) := hmul
    _ = 2 * Real.exp (-(Real.sqrt alpha * t)) *
          (f (x 0) - fstar) := by ring

/--
Chewi Theorem 5.9 source-shaped exponential gap bound, deriving stationarity
of the reference point from an unconstrained minimizer hypothesis.
-/
theorem chewi59_gap_le_exp_decay_of_firstOrderStrongConvex_of_isMinOn
    [CompleteSpace E] {alpha : ℝ} {f : E -> ℝ} {grad : E -> E}
    {fstar : ℝ} {x p : ℝ -> E} {xStar : E} {t : ℝ}
    (hfirst : FirstOrderStrongConvexOn Set.univ f grad alpha)
    (hgrad : ∀ z, HasGradientAt f (grad z) z)
    (hflow : IsChewi59AcceleratedGradientFlowTrajectory alpha grad x p)
    (hmin : IsMinOn f Set.univ xStar)
    (hfxStar : f xStar = fstar)
    (halpha_nonneg : 0 ≤ alpha)
    (hp0 : p 0 = 0)
    (ht : 0 ≤ t) :
    f (x t) - fstar ≤
      2 * Real.exp (-(Real.sqrt alpha * t)) *
        (f (x 0) - fstar) := by
  have hgradStar : grad xStar = 0 :=
    gradient_eq_zero_of_isMinOn_univ_hasGradientAt hmin (hgrad xStar)
  exact chewi59_gap_le_exp_decay_of_firstOrderStrongConvex
    hfirst hgrad hflow hfxStar halpha_nonneg hgradStar hp0 ht

end Optimization
end StatInference
