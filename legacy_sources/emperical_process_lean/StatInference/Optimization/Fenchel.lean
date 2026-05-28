import StatInference.Optimization.ProjectedSubgradient

/-!
# Chewi Chapter 9 Fenchel duality layer

This module starts Chapter 9 with a finite-valued, proof-carrying Fenchel
interface.  Chewi's notes use extended-real regular convex functions; the first
Lean packet keeps the existing Optimization style by representing the
conjugate value through an exact least-upper-bound certificate, with an `sSup`
definition available when the displayed supremum is bounded above.
-/

namespace StatInference
namespace Optimization

open scoped InnerProductSpace

variable {E : Type*} [NormedAddCommGroup E] [InnerProductSpace ℝ E]

/-- The displayed term `<x,p> - f x` in Chewi Definition 9.1. -/
def fenchelConjugateTerm (f : E -> ℝ) (p x : E) : ℝ :=
  inner ℝ p x - f x

/--
Chewi Definition 9.1 in finite-valued form.  For unbounded suprema this real
`sSup` is only a raw expression; theorem routes should use
`IsFenchelConjugateValue` or supply boundedness hypotheses.
-/
noncomputable def fenchelConjugate (f : E -> ℝ) (p : E) : ℝ :=
  sSup (Set.range fun x => fenchelConjugateTerm f p x)

/-- A number is an upper bound for the Fenchel display at `p`. -/
def IsFenchelUpperBound (f : E -> ℝ) (p : E) (value : ℝ) : Prop :=
  ∀ x, fenchelConjugateTerm f p x ≤ value

/-- Exact finite-valued Fenchel conjugate value at `p`. -/
structure IsFenchelConjugateValue (f : E -> ℝ) (p : E) (value : ℝ) : Prop where
  upper : IsFenchelUpperBound f p value
  least : ∀ ⦃upperValue : ℝ⦄,
    IsFenchelUpperBound f p upperValue -> value ≤ upperValue

theorem fenchelConjugate_isFenchelConjugateValue
    {f : E -> ℝ} {p : E}
    (hbdd : BddAbove (Set.range fun x => fenchelConjugateTerm f p x)) :
    IsFenchelConjugateValue f p (fenchelConjugate f p) where
  upper := by
    intro x
    exact le_csSup hbdd ⟨x, rfl⟩
  least := by
    intro upperValue hupper
    refine csSup_le (Set.range_nonempty _) ?_
    rintro _ ⟨x, rfl⟩
    exact hupper x

/-- Fenchel-Young inequality from the upper-bound half of Definition 9.1. -/
theorem fenchelYoung_of_upperBound
    {f : E -> ℝ} {p : E} {fStar_p : ℝ}
    (hstar : IsFenchelUpperBound f p fStar_p) (x : E) :
    inner ℝ p x ≤ f x + fStar_p := by
  have hx := hstar x
  unfold fenchelConjugateTerm at hx
  nlinarith

/-- Fenchel-Young inequality from an exact conjugate-value certificate. -/
theorem IsFenchelConjugateValue.fenchelYoung
    {f : E -> ℝ} {p : E} {fStar_p : ℝ}
    (hstar : IsFenchelConjugateValue f p fStar_p) (x : E) :
    inner ℝ p x ≤ f x + fStar_p :=
  fenchelYoung_of_upperBound hstar.upper x

/--
Chewi Theorem 9.6, finite-valued first equivalence:
equality in Fenchel-Young is equivalent to `p ∈ ∂f(x)`.
-/
theorem fenchelYoung_eq_iff_subgradient
    {f : E -> ℝ} {p x : E} {fStar_p : ℝ}
    (hstar : IsFenchelConjugateValue f p fStar_p) :
    f x + fStar_p = inner ℝ p x ↔ IsSubgradientAt Set.univ f p x := by
  constructor
  · intro heq
    refine ⟨Set.mem_univ x, ?_⟩
    intro y hy
    have hyUpper := hstar.upper y
    have hstar_eq : fStar_p = inner ℝ p x - f x := by
      nlinarith
    unfold fenchelConjugateTerm at hyUpper
    rw [inner_sub_right]
    nlinarith
  · intro hsub
    have hcandidateUpper :
        IsFenchelUpperBound f p (inner ℝ p x - f x) := by
      intro y
      have hy := hsub.2 (Set.mem_univ y)
      unfold fenchelConjugateTerm
      rw [inner_sub_right] at hy
      nlinarith
    have hle := hstar.least hcandidateUpper
    have hge := hstar.upper x
    unfold fenchelConjugateTerm at hge
    nlinarith

/--
Equality in Fenchel-Young gives the dual subgradient statement
`x ∈ ∂f*(p)`, provided `fStar` supplies the upper-bound side of the conjugate
for every dual point.
-/
theorem fenchelYoung_eq_to_conjugate_subgradient
    {f fStar : E -> ℝ} {p x : E}
    (hstar : ∀ q, IsFenchelUpperBound f q (fStar q))
    (heq : f x + fStar p = inner ℝ p x) :
    IsSubgradientAt Set.univ fStar x p := by
  refine ⟨Set.mem_univ p, ?_⟩
  intro q hq
  have hqUpper := hstar q x
  unfold fenchelConjugateTerm at hqUpper
  rw [inner_sub_right]
  have hxq : inner ℝ x q = inner ℝ q x := real_inner_comm q x
  have hxp : inner ℝ x p = inner ℝ p x := real_inner_comm p x
  nlinarith

/--
The converse dual-subgradient implication in Theorem 9.6.  The extra
`f = f**` certificate at `x` is the finite-valued replacement for the regular
convex hypothesis used in Chewi's notes.
-/
theorem fenchelYoung_eq_of_conjugate_subgradient
    {f fStar : E -> ℝ} {p x : E}
    (hstar_p : IsFenchelUpperBound f p (fStar p))
    (hbiconj_x : IsFenchelConjugateValue fStar x (f x))
    (hdual : IsSubgradientAt Set.univ fStar x p) :
    f x + fStar p = inner ℝ p x := by
  have hfy := fenchelYoung_of_upperBound hstar_p x
  have hcandidateUpper :
      IsFenchelUpperBound fStar x (inner ℝ x p - fStar p) := by
    intro q
    have hq := hdual.2 (Set.mem_univ q)
    unfold fenchelConjugateTerm
    rw [inner_sub_right] at hq
    nlinarith
  have hle := hbiconj_x.least hcandidateUpper
  have hcomm : inner ℝ x p = inner ℝ p x := real_inner_comm p x
  nlinarith

/--
Chewi Theorem 9.6, finite-valued dual equivalence:
equality in Fenchel-Young is equivalent to `x ∈ ∂f*(p)` once the local
double-conjugate equality at `x` is supplied.
-/
theorem fenchelYoung_eq_iff_conjugate_subgradient
    {f fStar : E -> ℝ} {p x : E}
    (hstar : ∀ q, IsFenchelUpperBound f q (fStar q))
    (hbiconj_x : IsFenchelConjugateValue fStar x (f x)) :
    f x + fStar p = inner ℝ p x ↔ IsSubgradientAt Set.univ fStar x p := by
  constructor
  · exact fenchelYoung_eq_to_conjugate_subgradient hstar
  · exact fenchelYoung_eq_of_conjugate_subgradient (hstar p) hbiconj_x

/--
Chewi Theorem 9.7, first statement, in finite-valued supplied-interface form:
any double-conjugate value is bounded above by the original value.
-/
theorem fenchelDoubleConjugate_le
    {f fStar : E -> ℝ} {x : E} {fDouble_x : ℝ}
    (hstar : ∀ p, IsFenchelUpperBound f p (fStar p))
    (hdouble : IsFenchelConjugateValue fStar x fDouble_x) :
    fDouble_x ≤ f x := by
  have hupper :
      IsFenchelUpperBound fStar x (f x) := by
    intro p
    have hp := hstar p x
    unfold fenchelConjugateTerm at hp ⊢
    have hcomm : inner ℝ x p = inner ℝ p x := real_inner_comm p x
    nlinarith
  exact hdouble.least hupper

/--
Strong monotonicity of the subgradient graph.  This is the nonsmooth analogue
of Chewi Proposition 1.6 / equation (1.5), and is the exact inequality used in
Lemma 9.12.
-/
def StrongSubgradientMonotoneOn (C : Set E) (f : E -> ℝ) (alpha : ℝ) : Prop :=
  ∀ ⦃x⦄, x ∈ C -> ∀ ⦃y⦄, y ∈ C -> ∀ ⦃p⦄, IsSubgradientAt C f p x ->
    ∀ ⦃q⦄, IsSubgradientAt C f q y ->
      alpha * ‖y - x‖ ^ (2 : ℕ) ≤ inner ℝ (q - p) (y - x)

/--
Chewi Lemma 9.12's core estimate: if `f` has an `alpha`-strongly monotone
subgradient graph and `gradStar y` selects a primal point with `y ∈ ∂f`, then
the selected conjugate-gradient map is `alpha^{-1}`-Lipschitz.
-/
theorem fenchelGradient_lipschitz_of_strongSubgradientMonotone
    {f : E -> ℝ} {gradStar : E -> E} {alpha : ℝ}
    (halpha : 0 < alpha)
    (hmono : StrongSubgradientMonotoneOn Set.univ f alpha)
    (hselect : ∀ y, IsSubgradientAt Set.univ f y (gradStar y))
    (y y' : E) :
    ‖gradStar y' - gradStar y‖ ≤ (1 / alpha) * ‖y' - y‖ := by
  let r : ℝ := ‖gradStar y' - gradStar y‖
  have hmono_app :
      alpha * r ^ (2 : ℕ) ≤
        inner ℝ (y' - y) (gradStar y' - gradStar y) := by
    simpa [r, real_inner_comm] using
      hmono (Set.mem_univ (gradStar y)) (Set.mem_univ (gradStar y'))
        (hselect y) (hselect y')
  have hcs :
      inner ℝ (y' - y) (gradStar y' - gradStar y) ≤
        ‖y' - y‖ * r := by
    simpa [r] using real_inner_le_norm (y' - y) (gradStar y' - gradStar y)
  have hmain : alpha * r ^ (2 : ℕ) ≤ ‖y' - y‖ * r :=
    hmono_app.trans hcs
  by_cases hr : r = 0
  · have hleft : ‖gradStar y' - gradStar y‖ = 0 := by simpa [r] using hr
    rw [hleft]
    positivity
  · have hrpos : 0 < r := lt_of_le_of_ne (by positivity) (Ne.symm hr)
    have hcancel : alpha * r ≤ ‖y' - y‖ := by
      have hmain' : (alpha * r) * r ≤ ‖y' - y‖ * r := by
        simpa [pow_two, mul_assoc] using hmain
      exact (mul_le_mul_iff_of_pos_right hrpos).1 hmain'
    have hdiv : r ≤ ‖y' - y‖ / alpha := by
      exact (le_div_iff₀ halpha).2 (by simpa [mul_comm] using hcancel)
    have hrewrite : ‖y' - y‖ / alpha = (1 / alpha) * ‖y' - y‖ := by
      field_simp [halpha.ne']
    simpa [r, hrewrite]
      using hdiv

end Optimization
end StatInference
