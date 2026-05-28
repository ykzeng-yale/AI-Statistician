import StatInference.Optimization.Basic

/-!
# Reductions between convex and strongly convex optimization

This module starts the proof-carrying layer for Chewi §4.1.  The first target
is Lemma 4.2: the quadratic regularization
`f_delta = f + delta / 2 * ‖· - x0‖^2` converts first-order convex/smooth
interfaces into first-order strongly-convex/smoother interfaces.
-/

namespace StatInference
namespace Optimization

open Set
open scoped InnerProductSpace

variable {E : Type*} [NormedAddCommGroup E] [InnerProductSpace ℝ E]

/-- Chewi Lemma 4.2 regularized objective `f_delta`. -/
noncomputable def quadraticRegularizedAround (f : E -> ℝ) (delta : ℝ)
    (x0 : E) : E -> ℝ :=
  fun x => f x + (delta / 2) * ‖x - x0‖ ^ (2 : ℕ)

/-- Supplied gradient for `quadraticRegularizedAround`. -/
noncomputable def regularizedGradient (grad : E -> E) (delta : ℝ)
    (x0 : E) : E -> E :=
  fun x => grad x + delta • (x - x0)

omit [InnerProductSpace ℝ E] in
theorem quadraticRegularizedAround_apply (f : E -> ℝ) (delta : ℝ)
    (x0 x : E) :
    quadraticRegularizedAround f delta x0 x =
      f x + (delta / 2) * ‖x - x0‖ ^ (2 : ℕ) :=
  rfl

theorem regularizedGradient_apply (grad : E -> E) (delta : ℝ)
    (x0 x : E) :
    regularizedGradient grad delta x0 x = grad x + delta • (x - x0) :=
  rfl

private theorem regularization_norm_sq_expansion (delta : ℝ) (x0 x y : E) :
    (delta / 2) * ‖x - x0‖ ^ (2 : ℕ) +
        inner ℝ (delta • (x - x0)) (y - x) +
          (delta / 2) * ‖y - x‖ ^ (2 : ℕ) =
      (delta / 2) * ‖y - x0‖ ^ (2 : ℕ) := by
  have hdecomp : y - x0 = (x - x0) + (y - x) := by
    abel
  rw [hdecomp, norm_add_sq_real]
  simp [real_inner_smul_left]
  ring

/--
Quadratic regularization shifts the first-order strong-convexity parameter by
`delta`.  In particular, a `0`-convex lower model becomes `delta`-strongly
convex after adding `delta / 2 * ‖· - x0‖^2`.
-/
theorem quadraticRegularizedAround_firstOrderStrongConvexOn
    {f : E -> ℝ} {grad : E -> E} {alpha delta : ℝ} {x0 : E}
    (hfirst : FirstOrderStrongConvexOn Set.univ f grad alpha) :
    FirstOrderStrongConvexOn Set.univ
      (quadraticRegularizedAround f delta x0)
      (regularizedGradient grad delta x0) (alpha + delta) := by
  refine ⟨convex_univ, ?_⟩
  intro x hx y hy
  have hmodel := hfirst.lower_model hx hy
  have hquad := regularization_norm_sq_expansion delta x0 x y
  simp [quadraticRegularizedAround, regularizedGradient, inner_add_left]
  nlinarith

/--
Quadratic regularization shifts the smoothness upper-model parameter by
`delta`.
-/
theorem quadraticRegularizedAround_smoothWithGradientOn
    {f : E -> ℝ} {grad : E -> E} {beta delta : ℝ} {x0 : E}
    (hsmooth : SmoothWithGradientOn Set.univ f grad beta) :
    SmoothWithGradientOn Set.univ
      (quadraticRegularizedAround f delta x0)
      (regularizedGradient grad delta x0) (beta + delta) := by
  refine ⟨convex_univ, ?_, ?_⟩
  · have hquad_cont :
        ContinuousOn
          (fun x : E => (delta / 2) * ‖x - x0‖ ^ (2 : ℕ)) Set.univ := by
      exact
        (continuous_const.mul
          (((continuous_id.sub continuous_const).norm).pow (2 : ℕ))).continuousOn
    simpa [quadraticRegularizedAround] using hsmooth.continuousOn.add hquad_cont
  · intro x hx y hy
    have hupper := hsmooth.upper_model hx hy
    have hquad := regularization_norm_sq_expansion delta x0 x y
    simp [quadraticRegularizedAround, regularizedGradient, inner_add_left]
    nlinarith

/-- Increasing the smoothness parameter preserves the supplied upper model. -/
theorem SmoothWithGradientOn.mono
    {C : Set E} {f : E -> ℝ} {grad : E -> E} {beta gamma : ℝ}
    (hbeta_le_gamma : beta ≤ gamma)
    (h : SmoothWithGradientOn C f grad beta) :
    SmoothWithGradientOn C f grad gamma := by
  refine ⟨h.convex_set, h.continuousOn, ?_⟩
  intro x hx y hy
  have hupper := h.upper_model hx hy
  have hsq : 0 ≤ ‖y - x‖ ^ (2 : ℕ) := sq_nonneg _
  have hcoef :
      (beta / 2) * ‖y - x‖ ^ (2 : ℕ) ≤
        (gamma / 2) * ‖y - x‖ ^ (2 : ℕ) := by
    nlinarith
  nlinarith

/--
Source-shaped convex case of the regularization lower model: regularizing a
`0`-convex first-order lower model gives a `delta`-strongly convex one.
-/
theorem quadraticRegularizedAround_firstOrderStrongConvexOn_convex
    {f : E -> ℝ} {grad : E -> E} {delta : ℝ} {x0 : E}
    (hfirst : FirstOrderStrongConvexOn Set.univ f grad 0) :
    FirstOrderStrongConvexOn Set.univ
      (quadraticRegularizedAround f delta x0)
      (regularizedGradient grad delta x0) delta := by
  simpa using
    (quadraticRegularizedAround_firstOrderStrongConvexOn
      (f := f) (grad := grad) (alpha := 0) (delta := delta) (x0 := x0)
      hfirst)

omit [InnerProductSpace ℝ E] in
/-- The regularized objective dominates the base objective when `delta >= 0`. -/
theorem le_quadraticRegularizedAround
    {f : E -> ℝ} {delta : ℝ} {x0 x : E} (hdelta : 0 ≤ delta) :
    f x ≤ quadraticRegularizedAround f delta x0 x := by
  have hsq : 0 ≤ ‖x - x0‖ ^ (2 : ℕ) := sq_nonneg _
  simp [quadraticRegularizedAround]
  nlinarith

omit [InnerProductSpace ℝ E] in
/--
Source-shaped value chain from Lemma 4.2: an approximate minimizer of the
regularized problem is good for the original objective up to the regularization
penalty at any comparison point.
-/
theorem quadraticRegularizedAround_near_min_le_base_add_penalty
    {f : E -> ℝ} {delta eps : ℝ} {x0 x xDelta xStar : E}
    (hdelta : 0 ≤ delta)
    (hx_near :
      quadraticRegularizedAround f delta x0 x ≤
        quadraticRegularizedAround f delta x0 xDelta + eps / 2)
    (hDelta_le :
      quadraticRegularizedAround f delta x0 xDelta ≤
        quadraticRegularizedAround f delta x0 xStar) :
    f x ≤ f xStar + (delta / 2) * ‖xStar - x0‖ ^ (2 : ℕ) + eps / 2 := by
  have hfx_le : f x ≤ quadraticRegularizedAround f delta x0 x :=
    le_quadraticRegularizedAround hdelta
  simp [quadraticRegularizedAround] at hx_near hDelta_le ⊢
  nlinarith

omit [InnerProductSpace ℝ E] in
/--
The previous source chain becomes an `eps`-gap once the regularization penalty
at the comparison minimizer is at most `eps`.
-/
theorem quadraticRegularizedAround_near_min_gap_le_eps
    {f : E -> ℝ} {delta eps : ℝ} {x0 x xDelta xStar : E}
    (hdelta : 0 ≤ delta)
    (hpenalty : delta * ‖xStar - x0‖ ^ (2 : ℕ) ≤ eps)
    (hx_near :
      quadraticRegularizedAround f delta x0 x ≤
        quadraticRegularizedAround f delta x0 xDelta + eps / 2)
    (hDelta_le :
      quadraticRegularizedAround f delta x0 xDelta ≤
        quadraticRegularizedAround f delta x0 xStar) :
    f x - f xStar ≤ eps := by
  have hvalue :=
    quadraticRegularizedAround_near_min_le_base_add_penalty
      (f := f) (delta := delta) (eps := eps) (x0 := x0)
      (x := x) (xDelta := xDelta) (xStar := xStar)
      hdelta hx_near hDelta_le
  nlinarith

omit [InnerProductSpace ℝ E] in
/--
Radius control implies the penalty estimate used after choosing
`delta = eps / R^2` in Lemma 4.2.
-/
theorem regularization_penalty_le_of_norm_le
    {delta eps R : ℝ} {x0 xStar : E}
    (hdelta : 0 ≤ delta) (hR_nonneg : 0 ≤ R)
    (hR : ‖xStar - x0‖ ≤ R)
    (hdeltaR : delta * R ^ (2 : ℕ) ≤ eps) :
    delta * ‖xStar - x0‖ ^ (2 : ℕ) ≤ eps := by
  have hsq :
      ‖xStar - x0‖ ^ (2 : ℕ) ≤ R ^ (2 : ℕ) :=
    (sq_le_sq₀ (norm_nonneg _) hR_nonneg).mpr hR
  have hmul := mul_le_mul_of_nonneg_left hsq hdelta
  exact hmul.trans hdeltaR

omit [InnerProductSpace ℝ E] in
/-- Positivity of the textbook choice `delta = eps / R^2`. -/
theorem regularization_delta_pos {eps R : ℝ}
    (heps : 0 < eps) (hR : 0 < R) :
    0 < eps / R ^ (2 : ℕ) := by
  exact div_pos heps (sq_pos_of_pos hR)

omit [InnerProductSpace ℝ E] in
/-- Nonnegativity of the textbook choice `delta = eps / R^2`. -/
theorem regularization_delta_nonneg {eps R : ℝ}
    (heps : 0 ≤ eps) :
    0 ≤ eps / R ^ (2 : ℕ) := by
  exact div_nonneg heps (sq_nonneg R)

omit [InnerProductSpace ℝ E] in
/--
If `eps <= beta * R^2`, then the textbook choice
`delta = eps / R^2` satisfies `delta <= beta`.
-/
theorem regularization_delta_le_beta_of_eps_le
    {beta eps R : ℝ} (hR : 0 < R)
    (heps_le : eps ≤ beta * R ^ (2 : ℕ)) :
    eps / R ^ (2 : ℕ) ≤ beta := by
  have hR_sq_pos : 0 < R ^ (2 : ℕ) := sq_pos_of_pos hR
  rw [div_le_iff₀ hR_sq_pos]
  simpa [mul_comm] using heps_le

omit [InnerProductSpace ℝ E] in
/-- The textbook choice `delta = eps / R^2` makes `delta * R^2 = eps`. -/
theorem regularization_delta_mul_radius_sq
    {eps R : ℝ} (hR_ne : R ≠ 0) :
    (eps / R ^ (2 : ℕ)) * R ^ (2 : ℕ) = eps := by
  have hR_sq_ne : R ^ (2 : ℕ) ≠ 0 := pow_ne_zero (2 : ℕ) hR_ne
  field_simp [hR_sq_ne]

omit [InnerProductSpace ℝ E] in
/--
The regularization penalty is at most `eps` when
`delta = eps / R^2` and the comparison minimizer is within radius `R`.
-/
theorem regularization_penalty_le_eps_of_norm_le_radius
    {eps R : ℝ} {x0 xStar : E}
    (heps : 0 ≤ eps) (hR : 0 < R)
    (hR_bound : ‖xStar - x0‖ ≤ R) :
    (eps / R ^ (2 : ℕ)) * ‖xStar - x0‖ ^ (2 : ℕ) ≤ eps := by
  refine regularization_penalty_le_of_norm_le
    (delta := eps / R ^ (2 : ℕ)) (eps := eps) (R := R)
    (x0 := x0) (xStar := xStar)
    (regularization_delta_nonneg heps) hR.le hR_bound ?_
  exact (regularization_delta_mul_radius_sq (eps := eps) hR.ne').le

omit [InnerProductSpace ℝ E] in
/--
Source-shaped final value conclusion in Lemma 4.2 after substituting
`delta = eps / R^2`.
-/
theorem quadraticRegularizedAround_near_min_gap_le_eps_of_radius
    {f : E -> ℝ} {eps R : ℝ} {x0 x xDelta xStar : E}
    (heps : 0 ≤ eps) (hR : 0 < R)
    (hR_bound : ‖xStar - x0‖ ≤ R)
    (hx_near :
      quadraticRegularizedAround f (eps / R ^ (2 : ℕ)) x0 x ≤
        quadraticRegularizedAround f (eps / R ^ (2 : ℕ)) x0 xDelta + eps / 2)
    (hDelta_le :
      quadraticRegularizedAround f (eps / R ^ (2 : ℕ)) x0 xDelta ≤
        quadraticRegularizedAround f (eps / R ^ (2 : ℕ)) x0 xStar) :
    f x - f xStar ≤ eps := by
  exact quadraticRegularizedAround_near_min_gap_le_eps
    (f := f) (delta := eps / R ^ (2 : ℕ)) (eps := eps)
    (x0 := x0) (x := x) (xDelta := xDelta) (xStar := xStar)
    (regularization_delta_nonneg heps)
    (regularization_penalty_le_eps_of_norm_le_radius
      (eps := eps) (R := R) (x0 := x0) (xStar := xStar)
      heps hR hR_bound)
    hx_near hDelta_le

omit [InnerProductSpace ℝ E] in
/--
When the regularized minimizer is no worse than a base minimizer, its initial
distance is no larger.  This is the distance estimate used in the complexity
part of Chewi Lemma 4.2.
-/
theorem regularized_minimizer_dist_le_of_base_min
    {f : E -> ℝ} {delta : ℝ} {x0 xDelta xStar : E}
    (hdelta : 0 < delta)
    (hDelta_le :
      quadraticRegularizedAround f delta x0 xDelta ≤
        quadraticRegularizedAround f delta x0 xStar)
    (hbase_min : f xStar ≤ f xDelta) :
    ‖xDelta - x0‖ ≤ ‖xStar - x0‖ := by
  have hcoef_pos : 0 < delta / 2 := by
    nlinarith
  have hsq_le :
      ‖xDelta - x0‖ ^ (2 : ℕ) ≤ ‖xStar - x0‖ ^ (2 : ℕ) := by
    simp [quadraticRegularizedAround] at hDelta_le
    nlinarith
  exact (sq_le_sq₀ (norm_nonneg _) (norm_nonneg _)).mp hsq_le

omit [InnerProductSpace ℝ E] in
/--
Radius form of the regularized-minimizer distance estimate in Lemma 4.2.
-/
theorem regularized_minimizer_dist_le_radius_of_base_min
    {f : E -> ℝ} {delta R : ℝ} {x0 xDelta xStar : E}
    (hdelta : 0 < delta)
    (hDelta_le :
      quadraticRegularizedAround f delta x0 xDelta ≤
        quadraticRegularizedAround f delta x0 xStar)
    (hbase_min : f xStar ≤ f xDelta)
    (hR_bound : ‖xStar - x0‖ ≤ R) :
    ‖xDelta - x0‖ ≤ R :=
  (regularized_minimizer_dist_le_of_base_min
    hdelta hDelta_le hbase_min).trans hR_bound

omit [InnerProductSpace ℝ E] in
/--
Radius form after substituting the textbook choice `delta = eps / R^2`.
-/
theorem regularized_minimizer_dist_le_radius_of_base_min_delta
    {f : E -> ℝ} {eps R : ℝ} {x0 xDelta xStar : E}
    (heps : 0 < eps) (hR : 0 < R)
    (hDelta_le :
      quadraticRegularizedAround f (eps / R ^ (2 : ℕ)) x0 xDelta ≤
        quadraticRegularizedAround f (eps / R ^ (2 : ℕ)) x0 xStar)
    (hbase_min : f xStar ≤ f xDelta)
    (hR_bound : ‖xStar - x0‖ ≤ R) :
    ‖xDelta - x0‖ ≤ R :=
  regularized_minimizer_dist_le_radius_of_base_min
    (delta := eps / R ^ (2 : ℕ))
    (regularization_delta_pos heps hR) hDelta_le hbase_min hR_bound

/-- If `delta <= beta`, the regularized smoothness constant is bounded by `2 beta`. -/
theorem regularized_smoothness_le_two_beta
    {beta delta : ℝ} (hdelta_le_beta : delta ≤ beta) :
    beta + delta ≤ 2 * beta := by
  nlinarith

/--
Regularization with `delta <= beta` gives a `2 beta` smooth upper model.
-/
theorem quadraticRegularizedAround_smoothWithGradientOn_two_beta
    {f : E -> ℝ} {grad : E -> E} {beta delta : ℝ} {x0 : E}
    (hsmooth : SmoothWithGradientOn Set.univ f grad beta)
    (hdelta_le_beta : delta ≤ beta) :
    SmoothWithGradientOn Set.univ
      (quadraticRegularizedAround f delta x0)
      (regularizedGradient grad delta x0) (2 * beta) :=
  SmoothWithGradientOn.mono
    (regularized_smoothness_le_two_beta hdelta_le_beta)
    (quadraticRegularizedAround_smoothWithGradientOn hsmooth)

omit [InnerProductSpace ℝ E] in
/--
Condition-number arithmetic from Lemma 4.2:
with `delta = eps / R^2`, `eps <= beta * R^2` implies
`(beta + delta) / delta <= 2 * beta * R^2 / eps`.
-/
theorem regularized_conditionNumber_le
    {beta eps R : ℝ} (heps : 0 < eps) (hR : 0 < R)
    (heps_le : eps ≤ beta * R ^ (2 : ℕ)) :
    (beta + eps / R ^ (2 : ℕ)) / (eps / R ^ (2 : ℕ)) ≤
      2 * beta * R ^ (2 : ℕ) / eps := by
  have hdelta_pos : 0 < eps / R ^ (2 : ℕ) :=
    regularization_delta_pos heps hR
  have hdelta_le_beta :
      eps / R ^ (2 : ℕ) ≤ beta :=
    regularization_delta_le_beta_of_eps_le hR heps_le
  have hsmooth_bound :
      beta + eps / R ^ (2 : ℕ) ≤ 2 * beta :=
    regularized_smoothness_le_two_beta hdelta_le_beta
  have hdiv :
      (beta + eps / R ^ (2 : ℕ)) / (eps / R ^ (2 : ℕ)) ≤
        (2 * beta) / (eps / R ^ (2 : ℕ)) :=
    div_le_div_of_nonneg_right hsmooth_bound hdelta_pos.le
  have hrhs :
      (2 * beta) / (eps / R ^ (2 : ℕ)) =
        2 * beta * R ^ (2 : ℕ) / eps := by
    have hR_sq_ne : R ^ (2 : ℕ) ≠ 0 := pow_ne_zero (2 : ℕ) hR.ne'
    field_simp [heps.ne', hR_sq_ne]
  exact hdiv.trans_eq hrhs

/--
Compiled package for the complexity-relevant part of Chewi Lemma 4.2.  It
collects the regularized problem's strong-convexity, smoothness, `2 beta`
smoothness bound, and condition-number estimate after choosing
`delta = eps / R^2`.
-/
theorem lemma42_regularization_complexity_package
    {f : E -> ℝ} {grad : E -> E} {beta eps R : ℝ} {x0 : E}
    (hfirst : FirstOrderStrongConvexOn Set.univ f grad 0)
    (hsmooth : SmoothWithGradientOn Set.univ f grad beta)
    (heps : 0 < eps) (hR : 0 < R)
    (heps_le : eps ≤ beta * R ^ (2 : ℕ)) :
    let delta := eps / R ^ (2 : ℕ)
    FirstOrderStrongConvexOn Set.univ
      (quadraticRegularizedAround f delta x0)
      (regularizedGradient grad delta x0) delta ∧
    SmoothWithGradientOn Set.univ
      (quadraticRegularizedAround f delta x0)
      (regularizedGradient grad delta x0) (beta + delta) ∧
    SmoothWithGradientOn Set.univ
      (quadraticRegularizedAround f delta x0)
      (regularizedGradient grad delta x0) (2 * beta) ∧
    (beta + delta) / delta ≤ 2 * beta * R ^ (2 : ℕ) / eps := by
  dsimp
  have hdelta_le_beta :
      eps / R ^ (2 : ℕ) ≤ beta :=
    regularization_delta_le_beta_of_eps_le hR heps_le
  exact ⟨
    quadraticRegularizedAround_firstOrderStrongConvexOn_convex hfirst,
    quadraticRegularizedAround_smoothWithGradientOn hsmooth,
    quadraticRegularizedAround_smoothWithGradientOn_two_beta
      hsmooth hdelta_le_beta,
    regularized_conditionNumber_le heps hR heps_le⟩

/--
Source-shaped package for Chewi Lemma 4.2 after choosing
`delta = eps / R^2`: an `eps / 2` approximate minimizer of the regularized
problem is an `eps` approximate minimizer of the original problem, the
regularized minimizer remains within the same initial radius, and the
regularized problem has the complexity-relevant strong-convexity/smoothness
and condition-number bounds.
-/
theorem lemma42_regularization_reduction_package
    {f : E -> ℝ} {grad : E -> E} {beta eps R : ℝ}
    {x0 x xDelta xStar : E}
    (hfirst : FirstOrderStrongConvexOn Set.univ f grad 0)
    (hsmooth : SmoothWithGradientOn Set.univ f grad beta)
    (heps : 0 < eps) (hR : 0 < R)
    (heps_le : eps ≤ beta * R ^ (2 : ℕ))
    (hR_bound : ‖xStar - x0‖ ≤ R)
    (hx_near :
      quadraticRegularizedAround f (eps / R ^ (2 : ℕ)) x0 x ≤
        quadraticRegularizedAround f (eps / R ^ (2 : ℕ)) x0 xDelta + eps / 2)
    (hDelta_le :
      quadraticRegularizedAround f (eps / R ^ (2 : ℕ)) x0 xDelta ≤
        quadraticRegularizedAround f (eps / R ^ (2 : ℕ)) x0 xStar)
    (hbase_min : f xStar ≤ f xDelta) :
    let delta := eps / R ^ (2 : ℕ)
    f x - f xStar ≤ eps ∧
    ‖xDelta - x0‖ ≤ R ∧
    FirstOrderStrongConvexOn Set.univ
      (quadraticRegularizedAround f delta x0)
      (regularizedGradient grad delta x0) delta ∧
    SmoothWithGradientOn Set.univ
      (quadraticRegularizedAround f delta x0)
      (regularizedGradient grad delta x0) (beta + delta) ∧
    SmoothWithGradientOn Set.univ
      (quadraticRegularizedAround f delta x0)
      (regularizedGradient grad delta x0) (2 * beta) ∧
    (beta + delta) / delta ≤ 2 * beta * R ^ (2 : ℕ) / eps := by
  dsimp
  have hvalue :
      f x - f xStar ≤ eps :=
    quadraticRegularizedAround_near_min_gap_le_eps_of_radius
      (f := f) (eps := eps) (R := R) (x0 := x0)
      (x := x) (xDelta := xDelta) (xStar := xStar)
      heps.le hR hR_bound hx_near hDelta_le
  have hdist :
      ‖xDelta - x0‖ ≤ R :=
    regularized_minimizer_dist_le_radius_of_base_min_delta
      (f := f) (eps := eps) (R := R) (x0 := x0)
      (xDelta := xDelta) (xStar := xStar)
      heps hR hDelta_le hbase_min hR_bound
  have hcomplex :=
    lemma42_regularization_complexity_package
      (f := f) (grad := grad) (beta := beta) (eps := eps)
      (R := R) (x0 := x0)
      hfirst hsmooth heps hR heps_le
  exact ⟨hvalue, hdist, hcomplex.1, hcomplex.2.1,
    hcomplex.2.2.1, hcomplex.2.2.2⟩

/--
Same package as `lemma42_regularization_reduction_package`, using a global
base minimizer hypothesis for the comparison point `xStar`.
-/
theorem lemma42_regularization_reduction_package_of_isMinOn
    {f : E -> ℝ} {grad : E -> E} {beta eps R : ℝ}
    {x0 x xDelta xStar : E}
    (hfirst : FirstOrderStrongConvexOn Set.univ f grad 0)
    (hsmooth : SmoothWithGradientOn Set.univ f grad beta)
    (heps : 0 < eps) (hR : 0 < R)
    (heps_le : eps ≤ beta * R ^ (2 : ℕ))
    (hR_bound : ‖xStar - x0‖ ≤ R)
    (hx_near :
      quadraticRegularizedAround f (eps / R ^ (2 : ℕ)) x0 x ≤
        quadraticRegularizedAround f (eps / R ^ (2 : ℕ)) x0 xDelta + eps / 2)
    (hDelta_le :
      quadraticRegularizedAround f (eps / R ^ (2 : ℕ)) x0 xDelta ≤
        quadraticRegularizedAround f (eps / R ^ (2 : ℕ)) x0 xStar)
    (hmin : IsMinOn f Set.univ xStar) :
    let delta := eps / R ^ (2 : ℕ)
    f x - f xStar ≤ eps ∧
    ‖xDelta - x0‖ ≤ R ∧
    FirstOrderStrongConvexOn Set.univ
      (quadraticRegularizedAround f delta x0)
      (regularizedGradient grad delta x0) delta ∧
    SmoothWithGradientOn Set.univ
      (quadraticRegularizedAround f delta x0)
      (regularizedGradient grad delta x0) (beta + delta) ∧
    SmoothWithGradientOn Set.univ
      (quadraticRegularizedAround f delta x0)
      (regularizedGradient grad delta x0) (2 * beta) ∧
    (beta + delta) / delta ≤ 2 * beta * R ^ (2 : ℕ) / eps := by
  exact lemma42_regularization_reduction_package
    (f := f) (grad := grad) (beta := beta) (eps := eps)
    (R := R) (x0 := x0) (x := x) (xDelta := xDelta)
    (xStar := xStar)
    hfirst hsmooth heps hR heps_le hR_bound hx_near hDelta_le
    (hmin (by simp : xDelta ∈ Set.univ))

end Optimization
end StatInference
