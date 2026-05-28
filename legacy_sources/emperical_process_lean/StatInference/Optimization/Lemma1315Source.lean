import StatInference.Optimization.InteriorPoint

/-!
# Chewi Lemma 13.15 source-facing surface

This file packages the two displayed conclusions of Chewi Lemma 13.15 for a
`nu`-self-concordant barrier.  The analytic work is already proved in
`InteriorPoint.lean`; this module provides theorem-shaped handles matching the
textbook statements so later path-following arguments can consume them directly.
-/

namespace StatInference
namespace Optimization

/--
Chewi Lemma 13.15(1), source-facing statement:
`<grad f x, v>^2 <= nu * <v, Hess f x v>` on the barrier domain.
-/
def Chewi1315GradientInnerSqSurface
    {E : Type*} [NormedAddCommGroup E] [InnerProductSpace ℝ E]
    (s : Set E) (hess : E -> E →L[ℝ] E) (grad : E -> E)
    (nu : ℝ) : Prop :=
  ∀ ⦃x : E⦄, x ∈ s -> ∀ v : E,
    (inner ℝ (grad x) v) ^ (2 : ℕ) ≤
      nu * inner ℝ v (hess x v)

/--
Chewi Lemma 13.15(2), source-facing statement:
`<grad f x, y - x> <= nu` for points in the barrier domain.
-/
def Chewi1315SegmentInnerSurface
    {E : Type*} [NormedAddCommGroup E] [InnerProductSpace ℝ E]
    (s : Set E) (grad : E -> E) (nu : ℝ) : Prop :=
  ∀ ⦃x y : E⦄, x ∈ s -> y ∈ s ->
    inner ℝ (grad x) (y - x) ≤ nu

/--
Bundle of the two displayed inequalities in Chewi Lemma 13.15.
-/
structure Chewi1315SelfConcordantBarrierSourceSurface
    {E : Type*} [NormedAddCommGroup E] [InnerProductSpace ℝ E]
    (s : Set E) (hess : E -> E →L[ℝ] E) (grad : E -> E)
    (nu : ℝ) : Prop where
  gradient_inner_sq : Chewi1315GradientInnerSqSurface s hess grad nu
  segment_inner : Chewi1315SegmentInnerSurface s grad nu

/--
Chewi Lemma 13.15 from the supplied-oracle `SelfConcordantBarrierOn` interface,
assuming the domain Cauchy bridge and the gradient regularity needed by the
segment proof.
-/
theorem chewi1315_selfConcordantBarrier_sourceSurface_of_cauchy_continuousOn
    {E : Type*} [NormedAddCommGroup E] [InnerProductSpace ℝ E]
    {s : Set E} {hess : E -> E →L[ℝ] E} {grad : E -> E}
    {invHess : E -> E →L[ℝ] E} {thirdMixed : E -> E -> E -> ℝ}
    {M nu : ℝ}
    (hbar : SelfConcordantBarrierOn s hess grad invHess thirdMixed M nu)
    (hnu_pos : 0 < nu)
    (hs : Convex ℝ s)
    (hgrad_cont : ContinuousOn grad s)
    (hgrad : ∀ ⦃x y : E⦄, x ∈ s -> y ∈ s ->
      ∀ t, t ∈ interior (Set.Icc (0 : ℝ) 1) ->
        HasFDerivAt grad (hess (hessianSegmentPoint x y t))
          (hessianSegmentPoint x y t))
    (hcauchy : ∀ ⦃z : E⦄, z ∈ s -> ∀ v w : E,
      inner ℝ v w ≤ dualLocalNorm invHess z v * localNorm hess z w) :
    Chewi1315SelfConcordantBarrierSourceSurface s hess grad nu where
  gradient_inner_sq := by
    intro x hx v
    exact chewi1315_gradient_inner_sq_le_of_cauchy
      (hess := hess) (grad := grad) (invHess := invHess)
      (thirdMixed := thirdMixed) (M := M) (nu := nu)
      hbar hx (hcauchy hx) v
  segment_inner := by
    intro x y hx hy
    exact chewi1315_gradient_segment_inner_le_of_cauchy_continuousOn
      (hess := hess) (grad := grad) (invHess := invHess)
      (thirdMixed := thirdMixed) (M := M) (nu := nu)
      hbar hnu_pos hs hx hy hgrad_cont
      (hgrad (x := x) (y := y) hx hy) hcauchy

/--
Chewi Lemma 13.15 with the Cauchy bridge derived from symmetry, strict Hessian
positivity, and a right-inverse Hessian oracle at every domain point.
-/
theorem chewi1315_selfConcordantBarrier_sourceSurface_of_hessian_right_inverse
    {E : Type*} [NormedAddCommGroup E] [InnerProductSpace ℝ E]
    {s : Set E} {hess : E -> E →L[ℝ] E} {grad : E -> E}
    {invHess : E -> E →L[ℝ] E} {thirdMixed : E -> E -> E -> ℝ}
    {M nu : ℝ}
    (hbar : SelfConcordantBarrierOn s hess grad invHess thirdMixed M nu)
    (hnu_pos : 0 < nu)
    (hs : Convex ℝ s)
    (hgrad_cont : ContinuousOn grad s)
    (hgrad : ∀ ⦃x y : E⦄, x ∈ s -> y ∈ s ->
      ∀ t, t ∈ interior (Set.Icc (0 : ℝ) 1) ->
        HasFDerivAt grad (hess (hessianSegmentPoint x y t))
          (hessianSegmentPoint x y t))
    (hsymm : ∀ ⦃z : E⦄, z ∈ s -> ∀ u v : E,
      inner ℝ (hess z u) v = inner ℝ u (hess z v))
    (hpos : ∀ ⦃z : E⦄, z ∈ s -> ∀ {w : E},
      w ≠ 0 -> 0 < inner ℝ w (hess z w))
    (hright : ∀ ⦃z : E⦄, z ∈ s -> ∀ v : E,
      hess z (invHess z v) = v) :
    Chewi1315SelfConcordantBarrierSourceSurface s hess grad nu :=
  chewi1315_selfConcordantBarrier_sourceSurface_of_cauchy_continuousOn
    (hess := hess) (grad := grad) (invHess := invHess)
    (thirdMixed := thirdMixed) (M := M) (nu := nu)
    hbar hnu_pos hs hgrad_cont hgrad
    (by
      intro z hz
      exact dualPrimalCauchy_of_hessian_right_inverse_pos
        (hess := hess) (invHess := invHess) (x := z)
        (hsymm (z := z) hz) (hpos (z := z) hz) (hright (z := z) hz))

end Optimization
end StatInference
