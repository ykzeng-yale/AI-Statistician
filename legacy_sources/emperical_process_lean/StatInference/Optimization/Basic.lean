import Mathlib

/-!
# Optimization interfaces

This file starts the Chewi optimization lane with proof-carrying interfaces for
the first textbook primitives: convex sets, strong convexity, smooth upper
models, and gradient-descent trajectories.  The definitions are intentionally
content-based rather than author-named theorem reports; exact source-audited
reports should be added only after an exact textbook theorem or lemma compiles.
-/

namespace StatInference
namespace Optimization

open Set Filter
open scoped Topology
open scoped InnerProductSpace
open scoped Gradient
open scoped NNReal

variable {E : Type*} [NormedAddCommGroup E] [InnerProductSpace ℝ E]

/--
Chewi Definition 1.5, specialized to real inner-product spaces.

The domain carries the convex-set hypothesis, and the inequality keeps the
strong-convexity correction term explicit for later gradient-flow and
gradient-descent estimates.
-/
def StrongConvexOn (C : Set E) (f : E -> ℝ) (alpha : ℝ) : Prop :=
  Convex ℝ C ∧
    ∀ ⦃x⦄, x ∈ C -> ∀ ⦃y⦄, y ∈ C -> ∀ ⦃t : ℝ⦄, t ∈ Icc (0 : ℝ) 1 ->
      f ((1 - t) • x + t • y) ≤
        (1 - t) * f x + t * f y -
          (alpha / 2) * t * (1 - t) * ‖y - x‖ ^ (2 : ℕ)

/-- Chewi Definition 1.5 with `alpha = 0`. -/
def ChewiConvexOn (C : Set E) (f : E -> ℝ) : Prop :=
  StrongConvexOn C f 0

/--
First-order strong-convexity lower model, Chewi Proposition 1.6 / equation
(1.4), represented with an explicit gradient oracle.

This is intentionally a supplied interface for now: mathlib and the local
segment definition do not currently provide a ready general Hilbert-space
bridge from segment strong convexity plus differentiability to this
first-order form.
-/
def FirstOrderStrongConvexOn (C : Set E) (f : E -> ℝ) (grad : E -> E)
    (alpha : ℝ) : Prop :=
  Convex ℝ C ∧
    ∀ ⦃x⦄, x ∈ C -> ∀ ⦃y⦄, y ∈ C ->
      f x + inner ℝ (grad x) (y - x) +
        (alpha / 2) * ‖y - x‖ ^ (2 : ℕ) ≤ f y

/--
Chewi Proposition 1.6 / equation (1.5), represented directly as monotonicity
of the supplied gradient oracle.

This supplied interface is separated from `FirstOrderStrongConvexOn` because
Theorem 3.3 uses the gradient monotonicity form directly.
-/
def StronglyMonotoneGradientOn (C : Set E) (grad : E -> E)
    (alpha : ℝ) : Prop :=
  ∀ ⦃x⦄, x ∈ C -> ∀ ⦃y⦄, y ∈ C ->
    alpha * ‖y - x‖ ^ (2 : ℕ) ≤ inner ℝ (grad y - grad x) (y - x)

/--
Chewi Exercise 3.1 / equation (3.5), represented in its source orientation.
This is the unscaled co-coercivity estimate used to supply Theorem 3.3.
-/
def GradientCocoerciveOn (C : Set E) (grad : E -> E) (beta : ℝ) : Prop :=
  ∀ ⦃x⦄, x ∈ C -> ∀ ⦃y⦄, y ∈ C ->
    ‖grad y - grad x‖ ^ (2 : ℕ) ≤
      beta * inner ℝ (grad y - grad x) (y - x)

/--
Chewi Exercise 3.1 / equation (3.5), specialized to the scaled inequality
needed in the proof of Theorem 3.3.
-/
def GradientStepCocoerciveOn (C : Set E) (grad : E -> E) (h : ℝ) : Prop :=
  ∀ ⦃x⦄, x ∈ C -> ∀ ⦃y⦄, y ∈ C ->
    h * ‖grad y - grad x‖ ^ (2 : ℕ) ≤ inner ℝ (y - x) (grad y - grad x)

/--
Chewi Definition 1.12, represented by the usual quadratic upper model with an
explicit gradient oracle.  Later exact smoothness equivalences can connect this
to Frechet derivatives and gradient Lipschitzness.
-/
def SmoothWithGradientOn (C : Set E) (f : E -> ℝ) (grad : E -> E)
    (beta : ℝ) : Prop :=
  Convex ℝ C ∧
    ContinuousOn f C ∧
      ∀ ⦃x⦄, x ∈ C -> ∀ ⦃y⦄, y ∈ C ->
        f y ≤ f x + inner ℝ (grad x) (y - x) +
          (beta / 2) * ‖y - x‖ ^ (2 : ℕ)

/--
Chewi Definition 2.5, Polyak-Lojasiewicz inequality with a supplied gradient
oracle and reference value `fstar`.
-/
def PolyakLojasiewiczOn (C : Set E) (f : E -> ℝ) (grad : E -> E)
    (alpha fstar : ℝ) : Prop :=
  ∀ ⦃x⦄, x ∈ C ->
    2 * alpha * (f x - fstar) ≤ ‖grad x‖ ^ (2 : ℕ)

/-- Gradient descent one-step map with an explicit gradient oracle. -/
def gradientDescentStep (grad : E -> E) (h : ℝ) (x : E) : E :=
  x - h • grad x

/-- A sequence follows gradient descent for a supplied gradient oracle. -/
def IsGradientDescentTrajectory (grad : E -> E) (h : ℝ)
    (x : ℕ -> E) : Prop :=
  ∀ n, x (n + 1) = gradientDescentStep grad h (x n)

theorem StrongConvexOn.convex_set {C : Set E} {f : E -> ℝ}
    {alpha : ℝ} (h : StrongConvexOn C f alpha) :
    Convex ℝ C :=
  h.1

theorem StrongConvexOn.segment_ineq {C : Set E} {f : E -> ℝ}
    {alpha : ℝ} (h : StrongConvexOn C f alpha)
    {x y : E} (hx : x ∈ C) (hy : y ∈ C)
    {t : ℝ} (ht : t ∈ Icc (0 : ℝ) 1) :
    f ((1 - t) • x + t • y) ≤
      (1 - t) * f x + t * f y -
        (alpha / 2) * t * (1 - t) * ‖y - x‖ ^ (2 : ℕ) :=
  h.2 hx hy ht

/--
Bridge from Chewi's segment strong-convexity display (1.3) to mathlib's
root `StrongConvexOn` API.
-/
theorem StrongConvexOn.to_mathlibStrongConvexOn
    {C : Set E} {f : E -> ℝ} {alpha : ℝ}
    (h : StrongConvexOn C f alpha) :
    _root_.StrongConvexOn C alpha f := by
  refine ⟨h.convex_set, ?_⟩
  intro x hx y hy a b ha hb hab
  have hb_le_one : b ≤ 1 := by nlinarith
  have hbIcc : b ∈ Icc (0 : ℝ) 1 := ⟨hb, hb_le_one⟩
  have ha_eq : a = 1 - b := by nlinarith
  have hseg := h.segment_ineq hx hy (t := b) hbIcc
  have hrhs :
      (1 - b) * f x + b * f y -
          (alpha / 2) * b * (1 - b) * ‖y - x‖ ^ (2 : ℕ) =
        a • f x + b • f y -
          a * b * (alpha / 2 * ‖x - y‖ ^ (2 : ℕ)) := by
    rw [ha_eq, norm_sub_rev]
    ring
  simpa [ha_eq, hrhs] using hseg

/--
Bridge from mathlib's root `StrongConvexOn` API back to Chewi's segment
display (1.3).
-/
theorem StrongConvexOn.of_mathlibStrongConvexOn
    {C : Set E} {f : E -> ℝ} {alpha : ℝ}
    (h : _root_.StrongConvexOn C alpha f) :
    StrongConvexOn C f alpha := by
  refine ⟨h.1, ?_⟩
  intro x hx y hy t ht
  have hone_sub_nonneg : 0 ≤ 1 - t := by nlinarith [ht.2]
  have hroot :=
    h.2 hx hy hone_sub_nonneg ht.1 (by ring : (1 - t) + t = 1)
  have hrhs :
      (1 - t) • f x + t • f y -
          (1 - t) * t * (alpha / 2 * ‖x - y‖ ^ (2 : ℕ)) =
        (1 - t) * f x + t * f y -
          (alpha / 2) * t * (1 - t) * ‖y - x‖ ^ (2 : ℕ) := by
    rw [norm_sub_rev]
    ring
  exact hroot.trans_eq hrhs

/-- Chewi's segment definition is definitionally equivalent to mathlib's root API. -/
theorem strongConvexOn_iff_mathlibStrongConvexOn
    {C : Set E} {f : E -> ℝ} {alpha : ℝ} :
    StrongConvexOn C f alpha ↔ _root_.StrongConvexOn C alpha f :=
  ⟨StrongConvexOn.to_mathlibStrongConvexOn,
    StrongConvexOn.of_mathlibStrongConvexOn⟩

/-- Lowering the strong-convexity parameter preserves Chewi strong convexity. -/
theorem StrongConvexOn.mono
    {C : Set E} {f : E -> ℝ} {alpha gamma : ℝ}
    (hgamma_le_alpha : gamma ≤ alpha)
    (h : StrongConvexOn C f alpha) :
    StrongConvexOn C f gamma :=
  StrongConvexOn.of_mathlibStrongConvexOn
    (_root_.StrongConvexOn.mono hgamma_le_alpha
      h.to_mathlibStrongConvexOn)

/-- Nonnegative Chewi strong convexity downshifts to Chewi convexity. -/
theorem StrongConvexOn.chewiConvexOn
    {C : Set E} {f : E -> ℝ} {alpha : ℝ}
    (h : StrongConvexOn C f alpha) (halpha : 0 ≤ alpha) :
    ChewiConvexOn C f :=
  StrongConvexOn.mono halpha h

/--
Nonnegative Chewi strong convexity gives the ordinary mathlib convex-function
API.
-/
theorem StrongConvexOn.convexOn
    {C : Set E} {f : E -> ℝ} {alpha : ℝ}
    (h : StrongConvexOn C f alpha) (halpha : 0 ≤ alpha) :
    _root_.ConvexOn ℝ C f := by
  exact h.to_mathlibStrongConvexOn.convexOn (by
    intro r
    positivity)

/-- Chewi convexity (`alpha = 0`) gives mathlib `ConvexOn`. -/
theorem ChewiConvexOn.convexOn {C : Set E} {f : E -> ℝ}
    (h : ChewiConvexOn C f) :
    _root_.ConvexOn ℝ C f := by
  have hroot : _root_.StrongConvexOn C (0 : ℝ) f :=
    h.to_mathlibStrongConvexOn
  simpa using hroot

theorem FirstOrderStrongConvexOn.convex_set {C : Set E} {f : E -> ℝ}
    {grad : E -> E} {alpha : ℝ}
    (h : FirstOrderStrongConvexOn C f grad alpha) :
    Convex ℝ C :=
  h.1

theorem FirstOrderStrongConvexOn.lower_model {C : Set E} {f : E -> ℝ}
    {grad : E -> E} {alpha : ℝ}
    (h : FirstOrderStrongConvexOn C f grad alpha)
    {x y : E} (hx : x ∈ C) (hy : y ∈ C) :
    f x + inner ℝ (grad x) (y - x) +
      (alpha / 2) * ‖y - x‖ ^ (2 : ℕ) ≤ f y :=
  h.2 hx hy

/--
Lowering the first-order strong-convexity parameter preserves the lower model.
-/
theorem FirstOrderStrongConvexOn.mono
    {C : Set E} {f : E -> ℝ} {grad : E -> E} {alpha gamma : ℝ}
    (hgamma_le_alpha : gamma ≤ alpha)
    (h : FirstOrderStrongConvexOn C f grad alpha) :
    FirstOrderStrongConvexOn C f grad gamma := by
  refine ⟨h.convex_set, ?_⟩
  intro x hx y hy
  have hmodel := h.lower_model hx hy
  have hcoef :
      (gamma / 2) * ‖y - x‖ ^ (2 : ℕ) ≤
        (alpha / 2) * ‖y - x‖ ^ (2 : ℕ) := by
    have hsq : 0 ≤ ‖y - x‖ ^ (2 : ℕ) := sq_nonneg _
    nlinarith
  nlinarith

/-- Nonnegative first-order strong convexity downshifts to the convex lower model. -/
theorem FirstOrderStrongConvexOn.convex
    {C : Set E} {f : E -> ℝ} {grad : E -> E} {alpha : ℝ}
    (h : FirstOrderStrongConvexOn C f grad alpha) (halpha : 0 ≤ alpha) :
    FirstOrderStrongConvexOn C f grad 0 :=
  FirstOrderStrongConvexOn.mono halpha h

/--
Chewi Proposition 1.6, implication `(1.3) => (1.4)` on the whole space:
segment strong convexity plus a mathlib gradient at every point gives the
first-order strong-convexity lower model.
-/
theorem FirstOrderStrongConvexOn.of_strongConvexOn_univ_hasGradientAt
    [CompleteSpace E] {f : E -> ℝ} {grad : E -> E} {alpha : ℝ}
    (hstrong : StrongConvexOn Set.univ f alpha)
    (hgrad : ∀ x, HasGradientAt f (grad x) x) :
    FirstOrderStrongConvexOn Set.univ f grad alpha := by
  refine ⟨convex_univ, ?_⟩
  intro x hx y hy
  let d : E := y - x
  let q : ℝ -> ℝ := fun t => t⁻¹ * (f (x + t • d) - f x)
  let corr : ℝ -> ℝ :=
    fun t => (alpha / 2) * (1 - t) * ‖d‖ ^ (2 : ℕ)
  let phi : ℝ -> E := fun t => x + t • d
  have hphi : HasDerivAt phi d 0 := by
    have hsmul : HasDerivAt (fun t : ℝ => t • d) d 0 := by
      simpa using (hasDerivAt_id (0 : ℝ)).smul_const d
    simpa [phi] using hsmul.const_add x
  have hderiv :
      HasDerivAt (fun t : ℝ => f (phi t)) (inner ℝ (grad x) d) 0 := by
    have hfx :
        HasFDerivAt f ((InnerProductSpace.toDual ℝ E) (grad x)) (phi 0) := by
      simpa [phi] using (hgrad x).hasFDerivAt
    have hcomp := hfx.comp_hasDerivAt (x := (0 : ℝ)) hphi
    have happly :
        ((InnerProductSpace.toDual ℝ E) (grad x)) d =
          inner ℝ (grad x) d := by
      simp
    simpa [phi, happly] using hcomp
  have hq_tend : Tendsto q (𝓝[>] (0 : ℝ)) (𝓝 (inner ℝ (grad x) d)) := by
    have h := hderiv.tendsto_slope_zero_right
    simpa [q, phi] using h
  have htend_id : Tendsto (fun t : ℝ => t) (𝓝[>] (0 : ℝ)) (𝓝 (0 : ℝ)) := by
    exact tendsto_id.mono_right nhdsWithin_le_nhds
  have hcorr_tend : Tendsto corr (𝓝[>] (0 : ℝ))
      (𝓝 ((alpha / 2) * (1 - 0) * ‖d‖ ^ (2 : ℕ))) := by
    have hone_minus :
        Tendsto (fun t : ℝ => 1 - t) (𝓝[>] (0 : ℝ)) (𝓝 (1 - 0)) :=
      tendsto_const_nhds.sub htend_id
    exact (tendsto_const_nhds.mul hone_minus).mul tendsto_const_nhds
  have hlim : Tendsto (fun t => q t + corr t) (𝓝[>] (0 : ℝ))
      (𝓝 (inner ℝ (grad x) d +
        (alpha / 2) * (1 - 0) * ‖d‖ ^ (2 : ℕ))) :=
    hq_tend.add hcorr_tend
  have hev_le1 : ∀ᶠ t : ℝ in 𝓝[>] (0 : ℝ), t ≤ 1 := by
    exact (eventually_le_nhds (show (0 : ℝ) < 1 by norm_num)).filter_mono
      nhdsWithin_le_nhds
  have hev : ∀ᶠ t : ℝ in 𝓝[>] (0 : ℝ), q t + corr t ≤ f y - f x := by
    filter_upwards [self_mem_nhdsWithin, hev_le1] with t htpos htle
    have htpos_real : 0 < t := htpos
    have htIcc : t ∈ Icc (0 : ℝ) 1 := ⟨le_of_lt htpos_real, htle⟩
    have hseg := hstrong.segment_ineq
      (by simp : x ∈ Set.univ) (by simp : y ∈ Set.univ) (t := t) htIcc
    have hpoint : (1 - t) • x + t • y = x + t • d := by
      simp [d]
      module
    have hsegd :
        f (x + t • d) ≤
          (1 - t) * f x + t * f y -
            alpha / 2 * t * (1 - t) * ‖d‖ ^ (2 : ℕ) := by
      simpa [d, hpoint] using hseg
    have hmul : t * (q t + corr t) ≤ t * (f y - f x) := by
      dsimp [q, corr]
      field_simp [htpos_real.ne']
      nlinarith [hsegd]
    exact (mul_le_mul_iff_of_pos_left htpos_real).mp hmul
  have hle_limit :
      inner ℝ (grad x) d + (alpha / 2) * (1 - 0) * ‖d‖ ^ (2 : ℕ) ≤
        f y - f x :=
    le_of_tendsto hlim hev
  have hfinal :
      f x + inner ℝ (grad x) d +
        (alpha / 2) * ‖d‖ ^ (2 : ℕ) ≤ f y := by
    nlinarith
  simpa [d] using hfinal

/--
Chewi Proposition 1.6, implication `(1.4) => (1.5)`: swapping the
first-order lower model and adding gives strong monotonicity of the supplied
gradient oracle.
-/
theorem FirstOrderStrongConvexOn.stronglyMonotoneGradientOn
    {C : Set E} {f : E -> ℝ} {grad : E -> E} {alpha : ℝ}
    (h : FirstOrderStrongConvexOn C f grad alpha) :
    StronglyMonotoneGradientOn C grad alpha := by
  intro x hx y hy
  let d : E := y - x
  have hxy :
      f x + inner ℝ (grad x) d +
        (alpha / 2) * ‖d‖ ^ (2 : ℕ) ≤ f y := by
    simpa [d] using h.lower_model hx hy
  have hyx :
      f y + inner ℝ (grad y) (x - y) +
        (alpha / 2) * ‖d‖ ^ (2 : ℕ) ≤ f x := by
    simpa [d, norm_sub_rev] using h.lower_model hy hx
  have hsum :
      inner ℝ (grad x) d + inner ℝ (grad y) (x - y) +
        alpha * ‖d‖ ^ (2 : ℕ) ≤ 0 := by
    nlinarith
  have hinner :
      inner ℝ (grad x) d + inner ℝ (grad y) (x - y) =
        -inner ℝ (grad y - grad x) d := by
    have hsub : x - y = -d := by
      simp [d]
    rw [hsub, inner_neg_right, inner_sub_left]
    ring
  have hmono :
      alpha * ‖d‖ ^ (2 : ℕ) ≤ inner ℝ (grad y - grad x) d := by
    rw [hinner] at hsum
    nlinarith
  simpa [d] using hmono

theorem StronglyMonotoneGradientOn.inner_lower {C : Set E}
    {grad : E -> E} {alpha : ℝ}
    (h : StronglyMonotoneGradientOn C grad alpha)
    {x y : E} (hx : x ∈ C) (hy : y ∈ C) :
    alpha * ‖y - x‖ ^ (2 : ℕ) ≤ inner ℝ (grad y - grad x) (y - x) :=
  h hx hy

theorem GradientCocoerciveOn.norm_sq_le {C : Set E}
    {grad : E -> E} {beta : ℝ}
    (h : GradientCocoerciveOn C grad beta)
    {x y : E} (hx : x ∈ C) (hy : y ∈ C) :
    ‖grad y - grad x‖ ^ (2 : ℕ) ≤
      beta * inner ℝ (grad y - grad x) (y - x) :=
  h hx hy

theorem GradientCocoerciveOn.stepCocoerciveOn {C : Set E}
    {grad : E -> E} {beta hstep : ℝ}
    (h : GradientCocoerciveOn C grad beta)
    (hbeta_pos : 0 < beta)
    (hh_nonneg : 0 ≤ hstep)
    (hbeta_step : beta * hstep ≤ 1) :
    GradientStepCocoerciveOn C grad hstep := by
  intro x hx y hy
  have hbase :
      ‖grad y - grad x‖ ^ (2 : ℕ) ≤
        beta * inner ℝ (y - x) (grad y - grad x) := by
    simpa [real_inner_comm] using h.norm_sq_le hx hy
  have hinner_nonneg :
      0 ≤ inner ℝ (y - x) (grad y - grad x) := by
    have hnorm_nonneg : 0 ≤ ‖grad y - grad x‖ ^ (2 : ℕ) :=
      sq_nonneg _
    nlinarith
  have hmul :
      hstep * ‖grad y - grad x‖ ^ (2 : ℕ) ≤
        hstep * (beta * inner ℝ (y - x) (grad y - grad x)) :=
    mul_le_mul_of_nonneg_left hbase hh_nonneg
  have hscale :
      hstep * (beta * inner ℝ (y - x) (grad y - grad x)) ≤
        inner ℝ (y - x) (grad y - grad x) := by
    have hbeta_step' : hstep * beta ≤ 1 := by
      nlinarith
    have hmul_inner :=
      mul_le_mul_of_nonneg_right hbeta_step' hinner_nonneg
    nlinarith
  exact hmul.trans hscale

theorem GradientCocoerciveOn.stepCocoerciveOn_of_le_inv {C : Set E}
    {grad : E -> E} {beta hstep : ℝ}
    (h : GradientCocoerciveOn C grad beta)
    (hbeta_pos : 0 < beta)
    (hh_nonneg : 0 ≤ hstep)
    (hstep_size : hstep ≤ 1 / beta) :
    GradientStepCocoerciveOn C grad hstep := by
  have hbeta_step : beta * hstep ≤ 1 := by
    have hmul : beta * hstep ≤ beta * (1 / beta) :=
      mul_le_mul_of_nonneg_left hstep_size hbeta_pos.le
    have hcancel : beta * (1 / beta) = 1 := by
      field_simp [hbeta_pos.ne']
    linarith
  exact h.stepCocoerciveOn hbeta_pos hh_nonneg hbeta_step

theorem GradientStepCocoerciveOn.inner_lower {C : Set E}
    {grad : E -> E} {hstep : ℝ}
    (h : GradientStepCocoerciveOn C grad hstep)
    {x y : E} (hx : x ∈ C) (hy : y ∈ C) :
    hstep * ‖grad y - grad x‖ ^ (2 : ℕ) ≤
      inner ℝ (y - x) (grad y - grad x) :=
  h hx hy

theorem SmoothWithGradientOn.convex_set {C : Set E} {f : E -> ℝ}
    {grad : E -> E} {beta : ℝ}
    (h : SmoothWithGradientOn C f grad beta) :
    Convex ℝ C :=
  h.1

theorem SmoothWithGradientOn.continuousOn {C : Set E} {f : E -> ℝ}
    {grad : E -> E} {beta : ℝ}
    (h : SmoothWithGradientOn C f grad beta) :
    ContinuousOn f C :=
  h.2.1

theorem SmoothWithGradientOn.upper_model {C : Set E} {f : E -> ℝ}
    {grad : E -> E} {beta : ℝ}
    (h : SmoothWithGradientOn C f grad beta)
    {x y : E} (hx : x ∈ C) (hy : y ∈ C) :
    f y ≤ f x + inner ℝ (grad x) (y - x) +
      (beta / 2) * ‖y - x‖ ^ (2 : ℕ) :=
  h.2.2 hx hy

omit [InnerProductSpace ℝ E] in
theorem PolyakLojasiewiczOn.gradient_sq_lower {C : Set E} {f : E -> ℝ}
    {grad : E -> E} {alpha fstar : ℝ}
    (h : PolyakLojasiewiczOn C f grad alpha fstar)
    {x : E} (hx : x ∈ C) :
    2 * alpha * (f x - fstar) ≤ ‖grad x‖ ^ (2 : ℕ) :=
  h hx

theorem IsGradientDescentTrajectory.succ {grad : E -> E} {h : ℝ}
    {x : ℕ -> E} (hx : IsGradientDescentTrajectory grad h x)
    (n : ℕ) :
    x (n + 1) = gradientDescentStep grad h (x n) :=
  hx n

section MathlibGradient

variable {H : Type*} [NormedAddCommGroup H] [InnerProductSpace ℝ H]
    [CompleteSpace H]

/--
Mathlib-gradient smoothness surface: differentiability on the domain plus a
Lipschitz gradient.  This is the preferred bridge when an exact theorem should
use mathlib's `gradient`/Frechet derivative API directly.
-/
def HasLipschitzGradientOn (L : ℝ≥0) (C : Set H) (f : H -> ℝ) : Prop :=
  DifferentiableOn ℝ f C ∧ LipschitzOnWith L (gradient f) C

/-- Gradient descent one-step map using mathlib's `gradient`. -/
noncomputable def gradientStep (eta : ℝ) (f : H -> ℝ) (x : H) : H :=
  x - eta • gradient f x

theorem HasLipschitzGradientOn.differentiableOn {L : ℝ≥0}
    {C : Set H} {f : H -> ℝ}
    (h : HasLipschitzGradientOn L C f) :
    DifferentiableOn ℝ f C :=
  h.1

theorem HasLipschitzGradientOn.lipschitzOnWith {L : ℝ≥0}
    {C : Set H} {f : H -> ℝ}
    (h : HasLipschitzGradientOn L C f) :
    LipschitzOnWith L (gradient f) C :=
  h.2

end MathlibGradient

end Optimization
end StatInference
