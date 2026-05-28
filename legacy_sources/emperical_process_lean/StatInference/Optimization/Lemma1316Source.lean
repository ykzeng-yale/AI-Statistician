import StatInference.Optimization.Lemma1315Source

/-!
# Chewi Lemma 13.16 source-facing surface

This module packages the displayed objective-gap estimate in Chewi Lemma 13.16.
The source writes the lemma for `(t, x) in R_+ x R^d`; the Lean theorem exposes
the proof-relevant side conditions `0 < t` and `lambda < 1`.
-/

namespace StatInference
namespace Optimization

/--
Chewi Lemma 13.16 source-facing objective-gap display.
-/
def Chewi1316ObjectiveGapSurface
    {E : Type*} [NormedAddCommGroup E] [InnerProductSpace ℝ E]
    (a x optimum : E) (t nu lambda : ℝ) : Prop :=
  inner ℝ a x - inner ℝ a optimum ≤
    (1 / t) *
      (nu + (((lambda + Real.sqrt nu) * lambda) / (1 - lambda)))

/--
Chewi Lemma 13.16 final-accuracy surface used after the standard
`lambda <= 1/4` and large-`t` simplification.
-/
def Chewi1316ObjectiveGapEpsSurface
    {E : Type*} [NormedAddCommGroup E] [InnerProductSpace ℝ E]
    (a x optimum : E) (eps : ℝ) : Prop :=
  inner ℝ a x - inner ℝ a optimum ≤ eps

/--
Chewi Lemma 13.16 supplied-interface assembly, with the Lemma 13.15 barrier
step and barrier gradient dual-norm supplied by the source surface and the
`SelfConcordantBarrierOn` oracle.
-/
theorem chewi1316_objectiveGap_sourceSurface_of_barrier_surface
    {E : Type*} [NormedAddCommGroup E] [InnerProductSpace ℝ E]
    {s : Set E} {hess : E -> E →L[ℝ] E}
    {invHess : E -> E →L[ℝ] E} {phiGrad : E -> E}
    {thirdMixed : E -> E -> E -> ℝ} {M nu : ℝ}
    {a x center optimum : E} {t lambda : ℝ}
    (hbar : SelfConcordantBarrierOn s hess phiGrad invHess thirdMixed M nu)
    (hsurface : Chewi1315SelfConcordantBarrierSourceSurface s hess phiGrad nu)
    (ht_pos : 0 < t)
    (hlambda_lt : lambda < 1)
    (hx : x ∈ s)
    (hcenter : center ∈ s)
    (hoptimum : optimum ∈ s)
    (hcentral : t • a + phiGrad center = 0)
    (hdecrement : dualLocalNorm invHess x (t • a + phiGrad x) ≤ lambda)
    (hcauchy : ∀ v w : E,
      inner ℝ v w ≤ dualLocalNorm invHess x v * localNorm hess x w)
    (hlower :
      (localNorm hess x (x - center)) ^ (2 : ℕ) /
          (1 + localNorm hess x (x - center)) ≤
        inner ℝ (t • a + phiGrad x) (x - center)) :
    Chewi1316ObjectiveGapSurface a x optimum t nu lambda :=
  chewi1316_objective_gap_le
    (hess := hess) (invHess := invHess) (phiGrad := phiGrad)
    (a := a) (x := x) (center := center) (optimum := optimum)
    (t := t) (nu := nu) (lambda := lambda)
    ht_pos hlambda_lt hcentral
    (hsurface.segment_inner hcenter hoptimum)
    hdecrement (hbar.gradient_bound hx) hcauchy hlower

/--
Chewi Lemma 13.16 final `epsilon` consequence from the source surface under
the standard `lambda <= 1/4` and `2 * nu <= eps * t` gates.
-/
theorem chewi1316_objectiveGap_eps_sourceSurface_of_barrier_surface
    {E : Type*} [NormedAddCommGroup E] [InnerProductSpace ℝ E]
    {s : Set E} {hess : E -> E →L[ℝ] E}
    {invHess : E -> E →L[ℝ] E} {phiGrad : E -> E}
    {thirdMixed : E -> E -> E -> ℝ} {M nu : ℝ}
    {a x center optimum : E} {t eps : ℝ}
    (hbar : SelfConcordantBarrierOn s hess phiGrad invHess thirdMixed M nu)
    (hsurface : Chewi1315SelfConcordantBarrierSourceSurface s hess phiGrad nu)
    (ht_pos : 0 < t)
    (heps_pos : 0 < eps)
    (hnu_one : 1 ≤ nu)
    (hx : x ∈ s)
    (hcenter : center ∈ s)
    (hoptimum : optimum ∈ s)
    (hcentral : t • a + phiGrad center = 0)
    (hdecrement : dualLocalNorm invHess x (t • a + phiGrad x) ≤ 1 / 4)
    (hcauchy : ∀ v w : E,
      inner ℝ v w ≤ dualLocalNorm invHess x v * localNorm hess x w)
    (hlower :
      (localNorm hess x (x - center)) ^ (2 : ℕ) /
          (1 + localNorm hess x (x - center)) ≤
        inner ℝ (t • a + phiGrad x) (x - center))
    (ht_large : 2 * nu ≤ eps * t) :
    Chewi1316ObjectiveGapEpsSurface a x optimum eps :=
  chewi1316_objective_gap_le_eps_of_le_quarter_and_large_t
    (hess := hess) (invHess := invHess) (phiGrad := phiGrad)
    (a := a) (x := x) (center := center) (optimum := optimum)
    (t := t) (nu := nu) (eps := eps)
    ht_pos heps_pos hnu_one hcentral
    (hsurface.segment_inner hcenter hoptimum)
    hdecrement (hbar.gradient_bound hx) hcauchy hlower ht_large

/--
Chewi Lemma 13.16 source surface with the Lemma 13.6 lower-model term supplied
by self-concordant value growth and a first-order convex lower model for the
central-path objective.
-/
theorem chewi1316_objectiveGap_sourceSurface_of_value_growth_and_firstOrder
    {E : Type*} [NormedAddCommGroup E] [InnerProductSpace ℝ E]
    {s C : Set E} {hess : E -> E →L[ℝ] E}
    {invHess : E -> E →L[ℝ] E} {phiValue : E -> ℝ} {phiGrad : E -> E}
    {thirdMixed : E -> E -> E -> ℝ} {M nu : ℝ}
    {a x center optimum : E} {t lambda : ℝ}
    (hbar : SelfConcordantBarrierOn s hess phiGrad invHess thirdMixed M nu)
    (hsurface : Chewi1315SelfConcordantBarrierSourceSurface s hess phiGrad nu)
    (ht_pos : 0 < t)
    (hlambda_lt : lambda < 1)
    (hx_barrier : x ∈ s)
    (hcenter_barrier : center ∈ s)
    (hoptimum_barrier : optimum ∈ s)
    (hcentral : t • a + phiGrad center = 0)
    (hdecrement : dualLocalNorm invHess x (t • a + phiGrad x) ≤ lambda)
    (hcauchy : ∀ v w : E,
      inner ℝ v w ≤ dualLocalNorm invHess x v * localNorm hess x w)
    (hfirst :
      FirstOrderStrongConvexOn C
        (fun z => t * inner ℝ a z + phiValue z)
        (fun z => t • a + phiGrad z) 0)
    (hx : x ∈ C) (hcenter : center ∈ C)
    (hgrowth :
      (localNorm hess x (x - center)) ^ (2 : ℕ) /
          (1 + localNorm hess x (x - center)) ≤
        (t * inner ℝ a x + phiValue x) -
          (t * inner ℝ a center + phiValue center)) :
    Chewi1316ObjectiveGapSurface a x optimum t nu lambda :=
  chewi1316_objective_gap_le_of_value_growth_and_firstOrderStrongConvexOn
    (C := C) (hess := hess) (invHess := invHess)
    (phiValue := phiValue) (phiGrad := phiGrad)
    (a := a) (x := x) (center := center) (optimum := optimum)
    (t := t) (nu := nu) (lambda := lambda)
    ht_pos hlambda_lt hcentral
    (hsurface.segment_inner hcenter_barrier hoptimum_barrier)
    hdecrement (hbar.gradient_bound hx_barrier) hcauchy
    hfirst hx hcenter hgrowth

end Optimization
end StatInference
