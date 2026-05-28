import StatInference.Optimization.Fenchel

/-!
# Chewi Chapter 10 Bregman and relative smoothness layer

This module starts the finite-valued Bregman substrate used by mirror methods.
It records Definition 10.2 and the relative convexity/smoothness inequalities
in the theorem-facing orientation needed for MPGD/OMD telescoping.
-/

namespace StatInference
namespace Optimization

open scoped InnerProductSpace

variable {E : Type*} [NormedAddCommGroup E] [InnerProductSpace ℝ E]

/-- Chewi Definition 10.2, finite-valued Bregman divergence. -/
def bregmanDivergence (phi : E -> ℝ) (gradPhi : E -> E) (x y : E) : ℝ :=
  phi x - phi y - inner ℝ (gradPhi y) (x - y)

theorem bregmanDivergence_self (phi : E -> ℝ) (gradPhi : E -> E) (x : E) :
    bregmanDivergence phi gradPhi x x = 0 := by
  simp [bregmanDivergence]

/-- Chewi Definition 10.4, `alpha`-convexity relative to a mirror map. -/
def RelativelyStrongConvexOn
    (C : Set E) (f : E -> ℝ) (gradF : E -> E)
    (phi : E -> ℝ) (gradPhi : E -> E) (alpha : ℝ) : Prop :=
  ∀ ⦃x⦄, x ∈ C -> ∀ ⦃y⦄, y ∈ C ->
    alpha * bregmanDivergence phi gradPhi x y ≤
      bregmanDivergence f gradF x y

/-- Chewi Definition 10.4, `beta`-smoothness relative to a mirror map. -/
def RelativelySmoothOn
    (C : Set E) (f : E -> ℝ) (gradF : E -> E)
    (phi : E -> ℝ) (gradPhi : E -> E) (beta : ℝ) : Prop :=
  ∀ ⦃x⦄, x ∈ C -> ∀ ⦃y⦄, y ∈ C ->
    bregmanDivergence f gradF x y ≤
      beta * bregmanDivergence phi gradPhi x y

/--
Proposition 10.5, lower-model orientation: relative strong convexity gives the
first-order lower model with a Bregman correction.
-/
theorem RelativelyStrongConvexOn.lower_model
    {C : Set E} {f : E -> ℝ} {gradF : E -> E}
    {phi : E -> ℝ} {gradPhi : E -> E} {alpha : ℝ}
    (hrel : RelativelyStrongConvexOn C f gradF phi gradPhi alpha)
    {x y : E} (hx : x ∈ C) (hy : y ∈ C) :
    f y + inner ℝ (gradF y) (x - y) +
        alpha * bregmanDivergence phi gradPhi x y ≤ f x := by
  have h := hrel hx hy
  unfold bregmanDivergence at h ⊢
  nlinarith

/--
Proposition 10.6, upper-model orientation: relative smoothness gives the
first-order upper model with a Bregman correction.
-/
theorem RelativelySmoothOn.upper_model
    {C : Set E} {f : E -> ℝ} {gradF : E -> E}
    {phi : E -> ℝ} {gradPhi : E -> E} {beta : ℝ}
    (hrel : RelativelySmoothOn C f gradF phi gradPhi beta)
    {x y : E} (hx : x ∈ C) (hy : y ∈ C) :
    f x ≤ f y + inner ℝ (gradF y) (x - y) +
        beta * bregmanDivergence phi gradPhi x y := by
  have h := hrel hx hy
  unfold bregmanDivergence at h ⊢
  nlinarith

/--
Chewi Lemma 10.7, finite-valued relative growth with the interior-minimizer
stationarity exposed as `gradF xStar = 0`.
-/
theorem RelativelyStrongConvexOn.growth_of_stationary
    {C : Set E} {f : E -> ℝ} {gradF : E -> E}
    {phi : E -> ℝ} {gradPhi : E -> E} {alpha : ℝ}
    (hrel : RelativelyStrongConvexOn C f gradF phi gradPhi alpha)
    {x xStar : E} (hx : x ∈ C) (hxStar : xStar ∈ C)
    (hgrad_zero : gradF xStar = 0) :
    alpha * bregmanDivergence phi gradPhi x xStar ≤ f x - f xStar := by
  have hmodel := hrel.lower_model hx hxStar
  rw [hgrad_zero] at hmodel
  simp at hmodel
  nlinarith

end Optimization
end StatInference
