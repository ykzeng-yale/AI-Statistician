import StatInference.Optimization.ConjugateGradient
import StatInference.Optimization.Theorem36
import StatInference.Optimization.Theorem37

/-!
# Chewi Theorem 5.4 conjugate-gradient rate layer

This module starts the accelerated-convergence proof for Chapter 5.  The first
layer isolates the source descent comparison: a CG step that is no worse than
the `1 / beta` gradient step inherits the descent-lemma squared-gradient sum
bound.
-/

namespace StatInference
namespace Optimization

open Finset
open scoped InnerProductSpace

variable {E : Type*} [NormedAddCommGroup E] [InnerProductSpace ℝ E]

/--
First displayed bound in Chewi Theorem 5.4.  If each CG step is competitive
with the gradient-descent trial step `x_n - beta^{-1} ∇f(x_n)`, then the
descent lemma telescopes to the finite squared-gradient sum bound.
-/
theorem chewi54_gradient_sq_sum_bound_of_competitive_step
    {C : Set E} {f : E -> ℝ} {grad : E -> E}
    {beta fstar : ℝ} {x : ℕ -> E}
    (hsmooth : SmoothWithGradientOn C f grad beta)
    (hmem : ∀ n, x n ∈ C)
    (hgd_mem : ∀ n, gradientDescentStep grad (1 / beta) (x n) ∈ C)
    (hcomp : ∀ n,
      f (x (n + 1)) ≤ f (gradientDescentStep grad (1 / beta) (x n)))
    (hstar_lower : ∀ n, fstar ≤ f (x n))
    (hbeta_pos : 0 < beta)
    (N : ℕ) :
    (1 / (2 * beta)) *
        (∑ n ∈ Finset.range N, ‖grad (x n)‖ ^ (2 : ℕ)) ≤
      f (x 0) - fstar := by
  have hbeta_ne : beta ≠ 0 := hbeta_pos.ne'
  have hcoef_eq : 1 / beta / 2 = 1 / (2 * beta) := by
    field_simp [hbeta_ne]
  have hstep : ∀ n,
      (1 / beta / 2) * ‖grad (x n)‖ ^ (2 : ℕ) ≤
        f (x n) - f (x (n + 1)) := by
    intro n
    have hgd_drop :
        (1 / beta / 2) * ‖grad (x n)‖ ^ (2 : ℕ) ≤
          f (x n) - f (gradientDescentStep grad (1 / beta) (x n)) := by
      have hbeta_step : beta * (1 / beta) ≤ 1 := by
        field_simp [hbeta_ne]
        rfl
      exact gradient_sq_step_le_drop_of_smoothWithGradientOn
        hsmooth (hmem n) (hgd_mem n) (by positivity) hbeta_step
    have htrial_to_cg :
        f (x n) - f (gradientDescentStep grad (1 / beta) (x n)) ≤
          f (x n) - f (x (n + 1)) := by
      nlinarith [hcomp n]
    exact hgd_drop.trans htrial_to_cg
  have hsum :
      (∑ n ∈ Finset.range N,
          (1 / beta / 2) * ‖grad (x n)‖ ^ (2 : ℕ)) ≤
        ∑ n ∈ Finset.range N, (f (x n) - f (x (n + 1))) :=
    Finset.sum_le_sum fun n _hn => hstep n
  have hleft :
      (1 / beta / 2) *
          (∑ n ∈ Finset.range N, ‖grad (x n)‖ ^ (2 : ℕ)) ≤
        ∑ n ∈ Finset.range N, (f (x n) - f (x (n + 1))) := by
    simpa [Finset.mul_sum] using hsum
  have htelescope :
      (∑ n ∈ Finset.range N, (f (x n) - f (x (n + 1)))) =
        f (x 0) - f (x N) := by
    simpa using sum_range_sub_succ (fun n => f (x n)) N
  calc
    (1 / (2 * beta)) *
        (∑ n ∈ Finset.range N, ‖grad (x n)‖ ^ (2 : ℕ))
        = (1 / beta / 2) *
            (∑ n ∈ Finset.range N, ‖grad (x n)‖ ^ (2 : ℕ)) := by
            rw [hcoef_eq]
    _ ≤ ∑ n ∈ Finset.range N, (f (x n) - f (x (n + 1))) := hleft
    _ = f (x 0) - f (x N) := htelescope
    _ ≤ f (x 0) - fstar := by
        nlinarith [hstar_lower N]

/--
Algebraic form of the first Theorem 5.4 descent-sum estimate.
-/
theorem chewi54_gradient_sq_sum_le_two_beta_gap
    {C : Set E} {f : E -> ℝ} {grad : E -> E}
    {beta fstar : ℝ} {x : ℕ -> E}
    (hsmooth : SmoothWithGradientOn C f grad beta)
    (hmem : ∀ n, x n ∈ C)
    (hgd_mem : ∀ n, gradientDescentStep grad (1 / beta) (x n) ∈ C)
    (hcomp : ∀ n,
      f (x (n + 1)) ≤ f (gradientDescentStep grad (1 / beta) (x n)))
    (hstar_lower : ∀ n, fstar ≤ f (x n))
    (hbeta_pos : 0 < beta)
    (N : ℕ) :
    (∑ n ∈ Finset.range N, ‖grad (x n)‖ ^ (2 : ℕ)) ≤
      2 * beta * (f (x 0) - fstar) := by
  have hsum :=
    chewi54_gradient_sq_sum_bound_of_competitive_step
      hsmooth hmem hgd_mem hcomp hstar_lower hbeta_pos N
  have hmul :=
    mul_le_mul_of_nonneg_left hsum (by positivity : 0 ≤ 2 * beta)
  have hcancel : (2 * beta) * (1 / (2 * beta)) = 1 := by
    field_simp [hbeta_pos.ne']
  have hleft_eq :
      2 * beta *
          (1 / (2 * beta) *
            (∑ n ∈ Finset.range N, ‖grad (x n)‖ ^ (2 : ℕ))) =
        ∑ n ∈ Finset.range N, ‖grad (x n)‖ ^ (2 : ℕ) := by
    rw [← mul_assoc, hcancel, one_mul]
  nlinarith

/--
Second displayed estimate in Chewi Theorem 5.4, isolated before the
Cauchy-Schwarz step.  The hypotheses correspond to monotonicity of the
objective gaps and the first-order/orthogonality calculation
`f(x_n)-fstar <= <grad(x_n), x_0-xstar>`.
-/
theorem chewi54_gap_sum_le_inner_gradient_sum
    {f : E -> ℝ} {grad : E -> E} {fstar : ℝ} {x : ℕ -> E}
    {xStar : E} {N : ℕ}
    (hgap_mono : ∀ n, n < N →
      f (x N) - fstar ≤ f (x n) - fstar)
    (hfirst_orth : ∀ n, n < N →
      f (x n) - fstar ≤ inner ℝ (grad (x n)) (x 0 - xStar)) :
    (N : ℝ) * (f (x N) - fstar) ≤
      inner ℝ (∑ n ∈ Finset.range N, grad (x n)) (x 0 - xStar) := by
  have hsum_gap :
      (∑ n ∈ Finset.range N, (f (x N) - fstar)) ≤
        ∑ n ∈ Finset.range N, (f (x n) - fstar) := by
    exact Finset.sum_le_sum fun n hn =>
      hgap_mono n (Finset.mem_range.mp hn)
  have hsum_inner :
      (∑ n ∈ Finset.range N, (f (x n) - fstar)) ≤
        ∑ n ∈ Finset.range N, inner ℝ (grad (x n)) (x 0 - xStar) := by
    exact Finset.sum_le_sum fun n hn =>
      hfirst_orth n (Finset.mem_range.mp hn)
  have hconst :
      (∑ n ∈ Finset.range N, (f (x N) - fstar)) =
        (N : ℝ) * (f (x N) - fstar) := by
    simp [mul_comm]
    ring
  have hinner :
      (∑ n ∈ Finset.range N, inner ℝ (grad (x n)) (x 0 - xStar)) =
        inner ℝ (∑ n ∈ Finset.range N, grad (x n)) (x 0 - xStar) := by
    rw [sum_inner]
  calc
    (N : ℝ) * (f (x N) - fstar)
        = ∑ n ∈ Finset.range N, (f (x N) - fstar) := hconst.symm
    _ ≤ ∑ n ∈ Finset.range N, (f (x n) - fstar) := hsum_gap
    _ ≤ ∑ n ∈ Finset.range N, inner ℝ (grad (x n)) (x 0 - xStar) := hsum_inner
    _ = inner ℝ (∑ n ∈ Finset.range N, grad (x n)) (x 0 - xStar) := hinner

/--
The Cauchy-Schwarz version of `chewi54_gap_sum_le_inner_gradient_sum`.
-/
theorem chewi54_gap_sum_le_norm_gradient_sum
    {f : E -> ℝ} {grad : E -> E} {fstar : ℝ} {x : ℕ -> E}
    {xStar : E} {N : ℕ}
    (hgap_mono : ∀ n, n < N →
      f (x N) - fstar ≤ f (x n) - fstar)
    (hfirst_orth : ∀ n, n < N →
      f (x n) - fstar ≤ inner ℝ (grad (x n)) (x 0 - xStar)) :
    (N : ℝ) * (f (x N) - fstar) ≤
      ‖∑ n ∈ Finset.range N, grad (x n)‖ * ‖x 0 - xStar‖ := by
  exact (chewi54_gap_sum_le_inner_gradient_sum hgap_mono hfirst_orth).trans
    (real_inner_le_norm
      (∑ n ∈ Finset.range N, grad (x n)) (x 0 - xStar))

/--
Finite Pythagoras identity for pairwise orthogonal gradients over
`Finset.range N`.
-/
theorem norm_sq_sum_range_eq_sum_norm_sq_of_pairwise_orthogonal
    (g : ℕ -> E) (N : ℕ)
    (horth : ∀ i j, i < N → j < N → i ≠ j →
      inner ℝ (g i) (g j) = 0) :
    ‖∑ n ∈ Finset.range N, g n‖ ^ (2 : ℕ) =
      ∑ n ∈ Finset.range N, ‖g n‖ ^ (2 : ℕ) := by
  rw [← real_inner_self_eq_norm_sq]
  rw [sum_inner]
  simp_rw [inner_sum]
  refine Finset.sum_congr rfl ?_
  intro i hi
  have hi_lt : i < N := Finset.mem_range.mp hi
  calc
    (∑ x ∈ Finset.range N, inner ℝ (g i) (g x))
        = inner ℝ (g i) (g i) := by
            refine Finset.sum_eq_single i ?_ ?_
            · intro j hj hji
              exact horth i j hi_lt (Finset.mem_range.mp hj) hji.symm
            · intro hi_not
              exact (hi_not hi).elim
    _ = ‖g i‖ ^ (2 : ℕ) := by
            simp

/--
Norm form of the finite Pythagoras identity for pairwise orthogonal gradients.
-/
theorem norm_sum_range_le_sqrt_sum_norm_sq_of_pairwise_orthogonal
    (g : ℕ -> E) (N : ℕ)
    (horth : ∀ i j, i < N → j < N → i ≠ j →
      inner ℝ (g i) (g j) = 0) :
    ‖∑ n ∈ Finset.range N, g n‖ ≤
      Real.sqrt (∑ n ∈ Finset.range N, ‖g n‖ ^ (2 : ℕ)) := by
  have hsq :=
    norm_sq_sum_range_eq_sum_norm_sq_of_pairwise_orthogonal g N horth
  exact Real.le_sqrt_of_sq_le (by
    rw [hsq])

/--
The Cauchy-Schwarz plus gradient-orthogonality estimate in Chewi Theorem 5.4.
-/
theorem chewi54_gap_sum_le_sqrt_sum_norm_sq_mul_dist
    {f : E -> ℝ} {grad : E -> E} {fstar : ℝ} {x : ℕ -> E}
    {xStar : E} {N : ℕ}
    (hgap_mono : ∀ n, n < N →
      f (x N) - fstar ≤ f (x n) - fstar)
    (hfirst_orth : ∀ n, n < N →
      f (x n) - fstar ≤ inner ℝ (grad (x n)) (x 0 - xStar))
    (hgrad_orth : ∀ i j, i < N → j < N → i ≠ j →
      inner ℝ (grad (x i)) (grad (x j)) = 0) :
    (N : ℝ) * (f (x N) - fstar) ≤
      Real.sqrt (∑ n ∈ Finset.range N, ‖grad (x n)‖ ^ (2 : ℕ)) *
        ‖x 0 - xStar‖ := by
  have hnorm :
      ‖∑ n ∈ Finset.range N, grad (x n)‖ ≤
        Real.sqrt (∑ n ∈ Finset.range N, ‖grad (x n)‖ ^ (2 : ℕ)) :=
    norm_sum_range_le_sqrt_sum_norm_sq_of_pairwise_orthogonal
      (fun n => grad (x n)) N hgrad_orth
  calc
    (N : ℝ) * (f (x N) - fstar)
        ≤ ‖∑ n ∈ Finset.range N, grad (x n)‖ * ‖x 0 - xStar‖ :=
          chewi54_gap_sum_le_norm_gradient_sum hgap_mono hfirst_orth
    _ ≤ Real.sqrt (∑ n ∈ Finset.range N, ‖grad (x n)‖ ^ (2 : ℕ)) *
          ‖x 0 - xStar‖ :=
          mul_le_mul_of_nonneg_right hnorm (norm_nonneg _)

/--
Pre-halving assembly for Chewi Theorem 5.4: combine the
orthogonality/Cauchy-Schwarz estimate with supplied sum and radius bounds.
-/
theorem chewi54_gap_sum_le_sqrt_product_bound
    {f : E -> ℝ} {grad : E -> E} {fstar alpha beta initialGap : ℝ}
    {x : ℕ -> E} {xStar : E} {N : ℕ}
    (hgap_mono : ∀ n, n < N →
      f (x N) - fstar ≤ f (x n) - fstar)
    (hfirst_orth : ∀ n, n < N →
      f (x n) - fstar ≤ inner ℝ (grad (x n)) (x 0 - xStar))
    (hgrad_orth : ∀ i j, i < N → j < N → i ≠ j →
      inner ℝ (grad (x i)) (grad (x j)) = 0)
    (hsum_bound :
      (∑ n ∈ Finset.range N, ‖grad (x n)‖ ^ (2 : ℕ)) ≤
        2 * beta * initialGap)
    (hdist_bound : ‖x 0 - xStar‖ ≤ Real.sqrt (2 * initialGap / alpha)) :
    (N : ℝ) * (f (x N) - fstar) ≤
      Real.sqrt (2 * beta * initialGap) *
        Real.sqrt (2 * initialGap / alpha) := by
  have hmain :
      (N : ℝ) * (f (x N) - fstar) ≤
        Real.sqrt (∑ n ∈ Finset.range N, ‖grad (x n)‖ ^ (2 : ℕ)) *
          ‖x 0 - xStar‖ :=
    chewi54_gap_sum_le_sqrt_sum_norm_sq_mul_dist
      hgap_mono hfirst_orth hgrad_orth
  have hsqrt_sum :
      Real.sqrt (∑ n ∈ Finset.range N, ‖grad (x n)‖ ^ (2 : ℕ)) ≤
        Real.sqrt (2 * beta * initialGap) :=
    Real.sqrt_le_sqrt hsum_bound
  have hstep1 :
      Real.sqrt (∑ n ∈ Finset.range N, ‖grad (x n)‖ ^ (2 : ℕ)) *
          ‖x 0 - xStar‖ ≤
        Real.sqrt (2 * beta * initialGap) * ‖x 0 - xStar‖ :=
    mul_le_mul_of_nonneg_right hsqrt_sum (norm_nonneg _)
  have hstep2 :
      Real.sqrt (2 * beta * initialGap) * ‖x 0 - xStar‖ ≤
        Real.sqrt (2 * beta * initialGap) *
          Real.sqrt (2 * initialGap / alpha) :=
      mul_le_mul_of_nonneg_left hdist_bound (Real.sqrt_nonneg _)
  exact hmain.trans (hstep1.trans hstep2)

/--
Pre-halving Theorem 5.4 bound with the descent-sum estimate instantiated from
the competitive CG step.
-/
theorem chewi54_gap_sum_le_sqrt_product_bound_of_competitive_step
    {C : Set E} {f : E -> ℝ} {grad : E -> E} {fstar alpha beta : ℝ}
    {x : ℕ -> E} {xStar : E} {N : ℕ}
    (hsmooth : SmoothWithGradientOn C f grad beta)
    (hmem : ∀ n, x n ∈ C)
    (hgd_mem : ∀ n, gradientDescentStep grad (1 / beta) (x n) ∈ C)
    (hcomp : ∀ n,
      f (x (n + 1)) ≤ f (gradientDescentStep grad (1 / beta) (x n)))
    (hstar_lower : ∀ n, fstar ≤ f (x n))
    (hbeta_pos : 0 < beta)
    (hgap_mono : ∀ n, n < N →
      f (x N) - fstar ≤ f (x n) - fstar)
    (hfirst_orth : ∀ n, n < N →
      f (x n) - fstar ≤ inner ℝ (grad (x n)) (x 0 - xStar))
    (hgrad_orth : ∀ i j, i < N → j < N → i ≠ j →
      inner ℝ (grad (x i)) (grad (x j)) = 0)
    (hdist_bound :
      ‖x 0 - xStar‖ ≤ Real.sqrt (2 * (f (x 0) - fstar) / alpha)) :
    (N : ℝ) * (f (x N) - fstar) ≤
      Real.sqrt (2 * beta * (f (x 0) - fstar)) *
        Real.sqrt (2 * (f (x 0) - fstar) / alpha) := by
  have hsum_bound :
      (∑ n ∈ Finset.range N, ‖grad (x n)‖ ^ (2 : ℕ)) ≤
        2 * beta * (f (x 0) - fstar) :=
    chewi54_gradient_sq_sum_le_two_beta_gap
      hsmooth hmem hgd_mem hcomp hstar_lower hbeta_pos N
  exact chewi54_gap_sum_le_sqrt_product_bound
    hgap_mono hfirst_orth hgrad_orth hsum_bound hdist_bound

/--
Strong-convexity radius estimate used in Chewi Theorem 5.4:
`||x_0 - x_*|| <= sqrt (2 (f x_0 - f_*) / alpha)`.
-/
theorem chewi54_dist_initial_le_sqrt_gap_of_firstOrderStrongConvexOn
    {C : Set E} {f : E -> ℝ} {grad : E -> E}
    {alpha fstar : ℝ} {x0 xStar : E}
    (hfirst : FirstOrderStrongConvexOn C f grad alpha)
    (hx0 : x0 ∈ C)
    (hxStar : xStar ∈ C)
    (hgrad_zero : grad xStar = 0)
    (hfstar : fstar = f xStar)
    (halpha_pos : 0 < alpha) :
    ‖x0 - xStar‖ ≤ Real.sqrt (2 * (f x0 - fstar) / alpha) := by
  have hmodel := hfirst.lower_model hxStar hx0
  rw [hgrad_zero] at hmodel
  simp at hmodel
  have hsq :
      ‖x0 - xStar‖ ^ (2 : ℕ) ≤ 2 * (f x0 - f xStar) / alpha := by
    have hmul :
        alpha * ‖x0 - xStar‖ ^ (2 : ℕ) ≤ 2 * (f x0 - f xStar) := by
      nlinarith
    exact (le_div_iff₀ halpha_pos).mpr (by
      simpa [mul_comm] using hmul)
  simpa [hfstar] using Real.le_sqrt_of_sq_le hsq

/--
Pre-halving Theorem 5.4 bound with both the descent sum and the strong
convexity radius estimate instantiated.
-/
theorem chewi54_gap_sum_le_sqrt_product_bound_of_firstOrderStrongConvexOn
    {C : Set E} {f : E -> ℝ} {grad : E -> E}
    {fstar alpha beta : ℝ} {x : ℕ -> E} {xStar : E} {N : ℕ}
    (hsmooth : SmoothWithGradientOn C f grad beta)
    (hfirst : FirstOrderStrongConvexOn C f grad alpha)
    (hmem : ∀ n, x n ∈ C)
    (hxStar : xStar ∈ C)
    (hgrad_zero : grad xStar = 0)
    (hfstar : fstar = f xStar)
    (hgd_mem : ∀ n, gradientDescentStep grad (1 / beta) (x n) ∈ C)
    (hcomp : ∀ n,
      f (x (n + 1)) ≤ f (gradientDescentStep grad (1 / beta) (x n)))
    (hstar_lower : ∀ n, fstar ≤ f (x n))
    (hbeta_pos : 0 < beta)
    (halpha_pos : 0 < alpha)
    (hgap_mono : ∀ n, n < N →
      f (x N) - fstar ≤ f (x n) - fstar)
    (hfirst_orth : ∀ n, n < N →
      f (x n) - fstar ≤ inner ℝ (grad (x n)) (x 0 - xStar))
    (hgrad_orth : ∀ i j, i < N → j < N → i ≠ j →
      inner ℝ (grad (x i)) (grad (x j)) = 0) :
    (N : ℝ) * (f (x N) - fstar) ≤
      Real.sqrt (2 * beta * (f (x 0) - fstar)) *
        Real.sqrt (2 * (f (x 0) - fstar) / alpha) := by
  have hdist :
      ‖x 0 - xStar‖ ≤ Real.sqrt (2 * (f (x 0) - fstar) / alpha) :=
    chewi54_dist_initial_le_sqrt_gap_of_firstOrderStrongConvexOn
      hfirst (hmem 0) hxStar hgrad_zero hfstar halpha_pos
  exact chewi54_gap_sum_le_sqrt_product_bound_of_competitive_step
    hsmooth hmem hgd_mem hcomp hstar_lower hbeta_pos
    hgap_mono hfirst_orth hgrad_orth hdist

/--
Scalar simplification of the pre-halving Theorem 5.4 product bound.
-/
theorem chewi54_sqrt_product_bound_le_conditioned_gap
    {alpha beta initialGap : ℝ}
    (halpha_pos : 0 < alpha)
    (hbeta_nonneg : 0 ≤ beta)
    (hgap_nonneg : 0 ≤ initialGap) :
    Real.sqrt (2 * beta * initialGap) *
        Real.sqrt (2 * initialGap / alpha) ≤
      2 * Real.sqrt (beta / alpha) * initialGap := by
  have hA : 0 ≤ 2 * beta * initialGap := by nlinarith
  have hB : 0 ≤ 2 * initialGap / alpha := by
    exact div_nonneg (by nlinarith) halpha_pos.le
  have hkappa_nonneg : 0 ≤ beta / alpha :=
    div_nonneg hbeta_nonneg halpha_pos.le
  have hleft_nonneg :
      0 ≤ Real.sqrt (2 * beta * initialGap) *
        Real.sqrt (2 * initialGap / alpha) :=
    mul_nonneg (Real.sqrt_nonneg _) (Real.sqrt_nonneg _)
  have hright_nonneg :
      0 ≤ 2 * Real.sqrt (beta / alpha) * initialGap := by
    positivity
  rw [← sq_le_sq₀ hleft_nonneg hright_nonneg]
  have hleft_sq :
      (Real.sqrt (2 * beta * initialGap) *
          Real.sqrt (2 * initialGap / alpha)) ^ (2 : ℕ) =
        (2 * beta * initialGap) * (2 * initialGap / alpha) := by
    rw [mul_pow, Real.sq_sqrt hA, Real.sq_sqrt hB]
  have hright_sq :
      (2 * Real.sqrt (beta / alpha) * initialGap) ^ (2 : ℕ) =
        4 * (beta / alpha) * initialGap ^ (2 : ℕ) := by
    rw [mul_pow, mul_pow, Real.sq_sqrt hkappa_nonneg]
    ring
  rw [hleft_sq, hright_sq]
  field_simp [halpha_pos.ne']
  ring_nf
  exact le_rfl

/--
Clean pre-halving Theorem 5.4 estimate:
`N (f x_N - f_*) <= 2 sqrt(beta / alpha) (f x_0 - f_*)`.
-/
theorem chewi54_gap_sum_le_two_sqrt_condition_mul_gap_of_firstOrderStrongConvexOn
    {C : Set E} {f : E -> ℝ} {grad : E -> E}
    {fstar alpha beta : ℝ} {x : ℕ -> E} {xStar : E} {N : ℕ}
    (hsmooth : SmoothWithGradientOn C f grad beta)
    (hfirst : FirstOrderStrongConvexOn C f grad alpha)
    (hmem : ∀ n, x n ∈ C)
    (hxStar : xStar ∈ C)
    (hgrad_zero : grad xStar = 0)
    (hfstar : fstar = f xStar)
    (hgd_mem : ∀ n, gradientDescentStep grad (1 / beta) (x n) ∈ C)
    (hcomp : ∀ n,
      f (x (n + 1)) ≤ f (gradientDescentStep grad (1 / beta) (x n)))
    (hstar_lower : ∀ n, fstar ≤ f (x n))
    (hbeta_pos : 0 < beta)
    (halpha_pos : 0 < alpha)
    (hgap_mono : ∀ n, n < N →
      f (x N) - fstar ≤ f (x n) - fstar)
    (hfirst_orth : ∀ n, n < N →
      f (x n) - fstar ≤ inner ℝ (grad (x n)) (x 0 - xStar))
    (hgrad_orth : ∀ i j, i < N → j < N → i ≠ j →
      inner ℝ (grad (x i)) (grad (x j)) = 0) :
    (N : ℝ) * (f (x N) - fstar) ≤
      2 * Real.sqrt (beta / alpha) * (f (x 0) - fstar) := by
  have hproduct :=
    chewi54_gap_sum_le_sqrt_product_bound_of_firstOrderStrongConvexOn
      hsmooth hfirst hmem hxStar hgrad_zero hfstar hgd_mem hcomp
      hstar_lower hbeta_pos halpha_pos hgap_mono hfirst_orth hgrad_orth
  have hgap_nonneg : 0 ≤ f (x 0) - fstar := sub_nonneg.mpr (hstar_lower 0)
  exact hproduct.trans
    (chewi54_sqrt_product_bound_le_conditioned_gap
      halpha_pos hbeta_pos.le hgap_nonneg)

/--
Halving contrapositive algebra in Chewi Theorem 5.4.  If the accelerated
bound holds and the final gap has not dropped below half the initial gap, then
the iteration count is at most `4 * sqrt (beta / alpha)`.
-/
theorem chewi54_iteration_le_four_sqrt_condition_of_not_halved
    {alpha beta gap0 gapN : ℝ} {N : ℕ}
    (hN_bound : (N : ℝ) * gapN ≤
      2 * Real.sqrt (beta / alpha) * gap0)
    (hnot_halved : gap0 / 2 ≤ gapN)
    (hgap0_pos : 0 < gap0)
    (halpha_pos : 0 < alpha)
    (hbeta_nonneg : 0 ≤ beta) :
    (N : ℝ) ≤ 4 * Real.sqrt (beta / alpha) := by
  have hkappa_nonneg : 0 ≤ beta / alpha :=
    div_nonneg hbeta_nonneg halpha_pos.le
  have hsqrt_nonneg : 0 ≤ Real.sqrt (beta / alpha) :=
    Real.sqrt_nonneg _
  have hgap_half_pos : 0 < gap0 / 2 := by nlinarith
  have hN_half : (N : ℝ) * (gap0 / 2) ≤ (N : ℝ) * gapN :=
    mul_le_mul_of_nonneg_left hnot_halved (Nat.cast_nonneg N)
  have hcombined :
      (N : ℝ) * (gap0 / 2) ≤
        2 * Real.sqrt (beta / alpha) * gap0 :=
    hN_half.trans hN_bound
  have hdiv :=
    (le_div_iff₀ hgap_half_pos).mpr hcombined
  have hratio :
      (2 * Real.sqrt (beta / alpha) * gap0) / (gap0 / 2) =
        4 * Real.sqrt (beta / alpha) := by
    field_simp [hgap0_pos.ne']
    ring
  simpa [hratio] using hdiv

/-- The affine CG search space `x₀ + span {p₀, ..., pₙ}`. -/
def cgAffineSpan (x0 : E) (p : ℕ -> E) (n : ℕ) : Set E :=
  {y | y - x0 ∈ cgDirectionSubmodule p n}

/-- Unfolding helper for `cgAffineSpan`. -/
theorem mem_cgAffineSpan_iff {x0 : E} {p : ℕ -> E} {n : ℕ} {y : E} :
    y ∈ cgAffineSpan x0 p n ↔ y - x0 ∈ cgDirectionSubmodule p n :=
  Iff.rfl

/--
Any point update along the current CG direction remains in the corresponding
affine direction span.
-/
theorem cgPoint_sub_initial_mem_cgDirectionSubmodule_of_step
    {x p : ℕ -> E} {a : ℕ -> ℝ}
    (hstep : ∀ n, x (n + 1) = x n + a n • p n) :
    ∀ n, x n - x 0 ∈ cgDirectionSubmodule p n := by
  intro n
  induction n with
  | zero =>
      simp
  | succ n ih =>
      have hprev :
          x n - x 0 ∈ cgDirectionSubmodule p (n + 1) :=
        cgDirectionSubmodule_mono p (Nat.le_succ n) ih
      have hp :
          p n ∈ cgDirectionSubmodule p (n + 1) :=
        cgDirectionSubmodule_mono p (Nat.le_succ n)
          (cgDirection_mem_cgDirectionSubmodule p n)
      have hnext :
          (x n - x 0) + a n • p n ∈
            cgDirectionSubmodule p (n + 1) :=
        Submodule.add_mem _ hprev (Submodule.smul_mem _ (a n) hp)
      rw [hstep n]
      simpa [sub_eq_add_neg, add_assoc, add_left_comm, add_comm] using hnext

/--
Sharper point-update membership: after `n + 1` displayed CG point updates, the
displacement uses only directions through `p_n`.
-/
theorem cgPoint_succ_sub_initial_mem_cgDirectionSubmodule_of_step
    {x p : ℕ -> E} {a : ℕ -> ℝ}
    (hstep : ∀ n, x (n + 1) = x n + a n • p n) :
    ∀ n, x (n + 1) - x 0 ∈ cgDirectionSubmodule p n := by
  intro n
  induction n with
  | zero =>
      have hp : p 0 ∈ cgDirectionSubmodule p 0 :=
        cgDirection_mem_cgDirectionSubmodule p 0
      have hmem : a 0 • p 0 ∈ cgDirectionSubmodule p 0 :=
        Submodule.smul_mem _ (a 0) hp
      rw [hstep 0]
      simpa [sub_eq_add_neg, add_assoc, add_left_comm, add_comm] using hmem
  | succ n ih =>
      have hprev :
          x (n + 1) - x 0 ∈ cgDirectionSubmodule p (n + 1) :=
        cgDirectionSubmodule_mono p (Nat.le_succ n) ih
      have hp :
          p (n + 1) ∈ cgDirectionSubmodule p (n + 1) :=
        cgDirection_mem_cgDirectionSubmodule p (n + 1)
      have hnext :
          (x (n + 1) - x 0) + a (n + 1) • p (n + 1) ∈
            cgDirectionSubmodule p (n + 1) :=
        Submodule.add_mem _ hprev (Submodule.smul_mem _ (a (n + 1)) hp)
      rw [hstep (n + 1)]
      simpa [sub_eq_add_neg, add_assoc, add_left_comm, add_comm] using hnext

/--
The `1 / beta` gradient trial point belongs to the current affine CG search
space once both the current displacement and the current gradient do.
-/
theorem gradientDescentStep_mem_cgAffineSpan_of_mem
    {grad : E -> E} {x0 x : E} {p : ℕ -> E} {n : ℕ} {h : ℝ}
    (hx : x - x0 ∈ cgDirectionSubmodule p n)
    (hgrad : grad x ∈ cgDirectionSubmodule p n) :
    gradientDescentStep grad h x ∈ cgAffineSpan x0 p n := by
  change gradientDescentStep grad h x - x0 ∈ cgDirectionSubmodule p n
  have hmem :
      (x - x0) - h • grad x ∈ cgDirectionSubmodule p n :=
    Submodule.sub_mem _ hx (Submodule.smul_mem _ h hgrad)
  simpa [gradientDescentStep, sub_eq_add_neg, add_assoc, add_left_comm,
    add_comm] using hmem

/--
First-order convexity plus orthogonality to the affine direction subspace gives
the constrained minimizer property over `x₀ + span {p₀, ..., pₙ}`.
-/
theorem firstOrderStrongConvexOn_isMinOn_cgAffineSpan_of_orthogonal
    {f : E -> ℝ} {grad : E -> E} {alpha : ℝ}
    {x0 x : E} {p : ℕ -> E} {n : ℕ}
    (hfirst : FirstOrderStrongConvexOn Set.univ f grad alpha)
    (halpha_nonneg : 0 ≤ alpha)
    (hx_feas : x ∈ cgAffineSpan x0 p n)
    (horth : IsOrthogonalToSubmodule (grad x) (cgDirectionSubmodule p n)) :
    IsMinOn f (cgAffineSpan x0 p n) x := by
  refine isMinOn_iff.mpr ?_
  intro y hy
  have hxS : x - x0 ∈ cgDirectionSubmodule p n :=
    mem_cgAffineSpan_iff.mp hx_feas
  have hyS : y - x0 ∈ cgDirectionSubmodule p n :=
    mem_cgAffineSpan_iff.mp hy
  have hdiff : y - x ∈ cgDirectionSubmodule p n := by
    have hsub : (y - x0) - (x - x0) ∈ cgDirectionSubmodule p n :=
      Submodule.sub_mem _ hyS hxS
    have hdiff_eq : y - x = (y - x0) - (x - x0) := by
      abel
    rw [hdiff_eq]
    exact hsub
  have horth_inner : inner ℝ (grad x) (y - x) = 0 :=
    horth (y - x) hdiff
  have hmodel := hfirst.lower_model (x := x) (y := y) (by simp) (by simp)
  have hquad_nonneg : 0 ≤ (alpha / 2) * ‖y - x‖ ^ (2 : ℕ) :=
    mul_nonneg (by nlinarith) (sq_nonneg _)
  rw [horth_inner] at hmodel
  nlinarith

/-- Displayed CG point updates give `x_n - x_0 ∈ span {p_0, ..., p_n}`. -/
theorem IsCGDisplayedIteration.point_sub_initial_mem_cgDirectionSubmodule
    {A : E →L[ℝ] E} {p0 : E} {x r p : ℕ -> E}
    (_h : IsCGDisplayedIteration A p0 r p)
    (hpoint : ∀ n, x (n + 1) =
      x n + cgLineSearchCoeff A r p n • p n) :
    ∀ n, x n - x 0 ∈ cgDirectionSubmodule p n :=
  cgPoint_sub_initial_mem_cgDirectionSubmodule_of_step hpoint

/--
Displayed CG point updates give the sharper membership
`x_{n+1} - x_0 ∈ span {p_0, ..., p_n}`.
-/
theorem IsCGDisplayedIteration.point_succ_sub_initial_mem_cgDirectionSubmodule
    {A : E →L[ℝ] E} {p0 : E} {x r p : ℕ -> E}
    (_h : IsCGDisplayedIteration A p0 r p)
    (hpoint : ∀ n, x (n + 1) =
      x n + cgLineSearchCoeff A r p n • p n) :
    ∀ n, x (n + 1) - x 0 ∈ cgDirectionSubmodule p n :=
  cgPoint_succ_sub_initial_mem_cgDirectionSubmodule_of_step hpoint

/--
For displayed CG point updates, the quadratic gradients belong to the current
direction span once the residuals identify with the quadratic gradients.
-/
theorem IsCGDisplayedIteration.quadraticGradient_mem_cgDirectionSubmodule
    {A : E →L[ℝ] E} {b p0 : E} {x r p : ℕ -> E}
    (h : IsCGDisplayedIteration A p0 r p)
    (hres0 : r 0 = quadraticGradient A b (x 0))
    (hpoint : ∀ n, x (n + 1) =
      x n + cgLineSearchCoeff A r p n • p n) :
    ∀ n, quadraticGradient A b (x n) ∈ cgDirectionSubmodule p n := by
  intro n
  have hres_eq := h.residual_eq_quadraticGradient_of_point_updates hres0 hpoint n
  rw [← hres_eq]
  exact h.to_isCGThreeTermRecurrence.residual_mem_cgDirectionSubmodule n

/--
Displayed CG residual orthogonality gives the source displacement
orthogonality `∇f(x_n) ⟂ x_n - x_0` for quadratic gradients.
-/
theorem IsCGDisplayedIteration.quadraticGradient_orthogonal_displacement
    {A : E →L[ℝ] E} {b p0 : E} {x r p : ℕ -> E}
    (h : IsCGDisplayedIteration A p0 r p)
    (hA_sym : IsSelfAdjointOperator A)
    (hres0 : r 0 = quadraticGradient A b (x 0))
    (hpoint : ∀ n, x (n + 1) =
      x n + cgLineSearchCoeff A r p n • p n) :
    ∀ n, inner ℝ (quadraticGradient A b (x n)) (x n - x 0) = 0 := by
  intro n
  cases n with
  | zero =>
      simp
  | succ n =>
      have horth_prev :
          ∀ m, IsOrthogonalToSubmodule (r (m + 1)) (cgDirectionSubmodule p m) :=
        orthogonalToPrevious_of_inner_directions_eq_zero
          (h.inner_residual_succ_directions_eq_zero hA_sym)
      have hdisp :
          x (n + 1) - x 0 ∈ cgDirectionSubmodule p n :=
        h.point_succ_sub_initial_mem_cgDirectionSubmodule hpoint n
      have horth :
          inner ℝ (r (n + 1)) (x (n + 1) - x 0) = 0 :=
        horth_prev n (x (n + 1) - x 0) hdisp
      have hres_eq :=
        h.residual_eq_quadraticGradient_of_point_updates hres0 hpoint (n + 1)
      rw [← hres_eq]
      exact horth

/--
Displayed CG residual orthogonality gives pairwise orthogonality of the
quadratic gradients along the point sequence.
-/
theorem IsCGDisplayedIteration.quadraticGradient_pairwise_orthogonal
    {A : E →L[ℝ] E} {b p0 : E} {x r p : ℕ -> E}
    (h : IsCGDisplayedIteration A p0 r p)
    (hA_sym : IsSelfAdjointOperator A)
    (hres0 : r 0 = quadraticGradient A b (x 0))
    (hpoint : ∀ n, x (n + 1) =
      x n + cgLineSearchCoeff A r p n • p n) :
    ∀ i j : ℕ, i ≠ j →
      inner ℝ (quadraticGradient A b (x i))
        (quadraticGradient A b (x j)) = 0 := by
  have horth_prev :
      ∀ m, IsOrthogonalToSubmodule (r (m + 1)) (cgDirectionSubmodule p m) :=
    orthogonalToPrevious_of_inner_directions_eq_zero
      (h.inner_residual_succ_directions_eq_zero hA_sym)
  have hpair : ∀ i j : ℕ, i ≠ j -> inner ℝ (r i) (r j) = 0 :=
    h.pairwise_residual_orthogonal horth_prev
  intro i j hij
  have hri := h.residual_eq_quadraticGradient_of_point_updates hres0 hpoint i
  have hrj := h.residual_eq_quadraticGradient_of_point_updates hres0 hpoint j
  rw [← hri, ← hrj]
  exact hpair i j hij

/--
Displayed CG point/residual updates imply the affine minimization property
over the current direction span.  This is the formal version of the source
sentence `x_{n+1} = argmin_{x_0 + K_n} f`.
-/
theorem IsCGDisplayedIteration.isMinOn_cgAffineSpan_of_point_updates
    {A : E →L[ℝ] E} {b p0 : E} {x r p : ℕ -> E} {alpha : ℝ}
    (h : IsCGDisplayedIteration A p0 r p)
    (hA_sym : IsSelfAdjointOperator A)
    (hfirst :
      FirstOrderStrongConvexOn Set.univ (quadraticObjective A b)
        (quadraticGradient A b) alpha)
    (halpha_nonneg : 0 ≤ alpha)
    (hres0 : r 0 = quadraticGradient A b (x 0))
    (hpoint : ∀ n, x (n + 1) =
      x n + cgLineSearchCoeff A r p n • p n) :
    ∀ n, IsMinOn (quadraticObjective A b) (cgAffineSpan (x 0) p n)
      (x (n + 1)) := by
  intro n
  have hfeas :
      x (n + 1) ∈ cgAffineSpan (x 0) p n :=
    mem_cgAffineSpan_iff.mpr
      (h.point_succ_sub_initial_mem_cgDirectionSubmodule hpoint n)
  have horth_prev :
      ∀ m, IsOrthogonalToSubmodule (r (m + 1)) (cgDirectionSubmodule p m) :=
    orthogonalToPrevious_of_inner_directions_eq_zero
      (h.inner_residual_succ_directions_eq_zero hA_sym)
  have hres_eq :=
    h.residual_eq_quadraticGradient_of_point_updates hres0 hpoint (n + 1)
  have horth_grad :
      IsOrthogonalToSubmodule
        (quadraticGradient A b (x (n + 1))) (cgDirectionSubmodule p n) := by
    intro y hy
    rw [← hres_eq]
    exact horth_prev n y hy
  exact firstOrderStrongConvexOn_isMinOn_cgAffineSpan_of_orthogonal
    hfirst halpha_nonneg hfeas horth_grad

/--
Source-facing CG competitive-step extraction: if `x_{n+1}` minimizes over the
current affine CG search space, it is no worse than the gradient-descent trial
point in that same affine space.
-/
theorem chewi54_competitive_step_of_cgAffineMinimizer
    {f : E -> ℝ} {grad : E -> E} {beta : ℝ} {x p : ℕ -> E}
    (hmin : ∀ n, IsMinOn f (cgAffineSpan (x 0) p n) (x (n + 1)))
    (hx_span : ∀ n, x n - x 0 ∈ cgDirectionSubmodule p n)
    (hgrad_span : ∀ n, grad (x n) ∈ cgDirectionSubmodule p n) :
    ∀ n, f (x (n + 1)) ≤
      f (gradientDescentStep grad (1 / beta) (x n)) := by
  intro n
  have htrial :
      gradientDescentStep grad (1 / beta) (x n) ∈ cgAffineSpan (x 0) p n :=
    gradientDescentStep_mem_cgAffineSpan_of_mem
      (hx_span n) (hgrad_span n)
  exact (isMinOn_iff.mp (hmin n))
    (gradientDescentStep grad (1 / beta) (x n)) htrial

/--
Competitive CG steps against the `1 / beta` gradient trial are function-value
nonincreasing.
-/
theorem chewi54_functionValue_antitone_of_competitive_step
    {C : Set E} {f : E -> ℝ} {grad : E -> E}
    {beta : ℝ} {x : ℕ -> E}
    (hsmooth : SmoothWithGradientOn C f grad beta)
    (hmem : ∀ n, x n ∈ C)
    (hgd_mem : ∀ n, gradientDescentStep grad (1 / beta) (x n) ∈ C)
    (hcomp : ∀ n,
      f (x (n + 1)) ≤ f (gradientDescentStep grad (1 / beta) (x n)))
    (hbeta_pos : 0 < beta) :
    Antitone fun n => f (x n) := by
  refine antitone_nat_of_succ_le ?_
  intro n
  have hbeta_step : beta * (1 / beta) ≤ 1 := by
    field_simp [hbeta_pos.ne']
    rfl
  have hdescent :
      f (gradientDescentStep grad (1 / beta) (x n)) - f (x n) ≤
        -((1 / beta) / 2) * ‖grad (x n)‖ ^ (2 : ℕ) :=
    descentLemma_of_smoothWithGradientOn hsmooth (hmem n) (hgd_mem n)
      (by positivity) hbeta_step
  have htrial_le : f (gradientDescentStep grad (1 / beta) (x n)) ≤ f (x n) := by
    have hcoef_nonneg : 0 ≤ (1 / beta) / 2 := by positivity
    have hnorm_nonneg : 0 ≤ ‖grad (x n)‖ ^ (2 : ℕ) := sq_nonneg _
    nlinarith
  exact (hcomp n).trans htrial_le

/--
Monotone-gap hypothesis for the Theorem 5.4 summation, derived from the
competitive-step descent property.
-/
theorem chewi54_gap_mono_of_competitive_step
    {C : Set E} {f : E -> ℝ} {grad : E -> E}
    {beta fstar : ℝ} {x : ℕ -> E} {N : ℕ}
    (hsmooth : SmoothWithGradientOn C f grad beta)
    (hmem : ∀ n, x n ∈ C)
    (hgd_mem : ∀ n, gradientDescentStep grad (1 / beta) (x n) ∈ C)
    (hcomp : ∀ n,
      f (x (n + 1)) ≤ f (gradientDescentStep grad (1 / beta) (x n)))
    (hbeta_pos : 0 < beta) :
    ∀ n, n < N -> f (x N) - fstar ≤ f (x n) - fstar := by
  intro n hn
  have hanti :
      Antitone fun n => f (x n) :=
    chewi54_functionValue_antitone_of_competitive_step
      hsmooth hmem hgd_mem hcomp hbeta_pos
  have hle : f (x N) ≤ f (x n) := hanti (Nat.le_of_lt hn)
  nlinarith

/--
The source first-order/orthogonality inequality in Theorem 5.4.  First-order
strong convexity gives the comparison with `x_n - x_*`; orthogonality of the
current gradient to the displacement `x_n - x_0` turns it into the displayed
`x_0 - x_*` inner product.
-/
theorem chewi54_first_orth_of_firstOrderStrongConvexOn
    {C : Set E} {f : E -> ℝ} {grad : E -> E}
    {alpha fstar : ℝ} {x : ℕ -> E} {xStar : E} {N : ℕ}
    (hfirst : FirstOrderStrongConvexOn C f grad alpha)
    (hmem : ∀ n, x n ∈ C)
    (hxStar : xStar ∈ C)
    (hfstar : fstar = f xStar)
    (halpha_nonneg : 0 ≤ alpha)
    (horth_disp : ∀ n, n < N →
      inner ℝ (grad (x n)) (x n - x 0) = 0) :
    ∀ n, n < N ->
      f (x n) - fstar ≤ inner ℝ (grad (x n)) (x 0 - xStar) := by
  intro n hn
  have hmodel := hfirst.lower_model (hmem n) hxStar
  have hterm_nonneg :
      0 ≤ (alpha / 2) * ‖xStar - x n‖ ^ (2 : ℕ) :=
    mul_nonneg (by nlinarith) (sq_nonneg _)
  have hfirst_bound :
      f (x n) - fstar ≤ inner ℝ (grad (x n)) (x n - xStar) := by
    have hinner :
        inner ℝ (grad (x n)) (xStar - x n) =
          -inner ℝ (grad (x n)) (x n - xStar) := by
      rw [show xStar - x n = -(x n - xStar) by abel]
      rw [inner_neg_right]
    rw [hinner] at hmodel
    rw [hfstar]
    nlinarith
  have hdecomp :
      x n - xStar = (x n - x 0) + (x 0 - xStar) := by
    abel
  have hinner_eq :
      inner ℝ (grad (x n)) (x n - xStar) =
        inner ℝ (grad (x n)) (x 0 - xStar) := by
    rw [hdecomp, inner_add_right, horth_disp n hn, zero_add]
  exact hfirst_bound.trans_eq hinner_eq

/--
Lower-bound property for the optimum value, derived from the first-order
strong-convexity model at a zero-gradient minimizer candidate.
-/
theorem chewi54_star_lower_of_firstOrderStrongConvexOn
    {C : Set E} {f : E -> ℝ} {grad : E -> E}
    {alpha fstar : ℝ} {x : ℕ -> E} {xStar : E}
    (hfirst : FirstOrderStrongConvexOn C f grad alpha)
    (hmem : ∀ n, x n ∈ C)
    (hxStar : xStar ∈ C)
    (hgrad_zero : grad xStar = 0)
    (hfstar : fstar = f xStar)
    (halpha_nonneg : 0 ≤ alpha) :
    ∀ n, fstar ≤ f (x n) := by
  intro n
  have hmodel := hfirst.lower_model hxStar (hmem n)
  rw [hgrad_zero] at hmodel
  simp at hmodel
  have hterm_nonneg :
      0 ≤ (alpha / 2) * ‖x n - xStar‖ ^ (2 : ℕ) :=
    mul_nonneg (by nlinarith) (sq_nonneg _)
  nlinarith

/--
Source-facing CG Theorem 5.4 wrapper.  It packages the displayed CG
affine-minimizer property into the competitive-step hypothesis, derives
monotone gaps and the first-order/orthogonality comparison, and then applies
the compiled analytic Theorem 5.4 core.
-/
theorem chewi54_accelerated_bound_of_cgAffineMinimizer
    {C : Set E} {f : E -> ℝ} {grad : E -> E}
    {fstar alpha beta : ℝ} {x p : ℕ -> E} {xStar : E} {N : ℕ}
    (hsmooth : SmoothWithGradientOn C f grad beta)
    (hfirst : FirstOrderStrongConvexOn C f grad alpha)
    (hmem : ∀ n, x n ∈ C)
    (hxStar : xStar ∈ C)
    (hgrad_zero : grad xStar = 0)
    (hfstar : fstar = f xStar)
    (hgd_mem : ∀ n, gradientDescentStep grad (1 / beta) (x n) ∈ C)
    (hmin : ∀ n, IsMinOn f (cgAffineSpan (x 0) p n) (x (n + 1)))
    (hx_span : ∀ n, x n - x 0 ∈ cgDirectionSubmodule p n)
    (hgrad_span : ∀ n, grad (x n) ∈ cgDirectionSubmodule p n)
    (horth_disp : ∀ n, n < N →
      inner ℝ (grad (x n)) (x n - x 0) = 0)
    (hgrad_orth : ∀ i j, i < N → j < N → i ≠ j →
      inner ℝ (grad (x i)) (grad (x j)) = 0)
    (hbeta_pos : 0 < beta)
    (halpha_pos : 0 < alpha) :
    (N : ℝ) * (f (x N) - fstar) ≤
      2 * Real.sqrt (beta / alpha) * (f (x 0) - fstar) := by
  have hcomp :
      ∀ n, f (x (n + 1)) ≤
        f (gradientDescentStep grad (1 / beta) (x n)) :=
    chewi54_competitive_step_of_cgAffineMinimizer hmin hx_span hgrad_span
  have hstar_lower : ∀ n, fstar ≤ f (x n) :=
    chewi54_star_lower_of_firstOrderStrongConvexOn
      hfirst hmem hxStar hgrad_zero hfstar halpha_pos.le
  have hgap_mono :
      ∀ n, n < N -> f (x N) - fstar ≤ f (x n) - fstar :=
    chewi54_gap_mono_of_competitive_step
      hsmooth hmem hgd_mem hcomp hbeta_pos
  have hfirst_orth :
      ∀ n, n < N ->
        f (x n) - fstar ≤ inner ℝ (grad (x n)) (x 0 - xStar) :=
    chewi54_first_orth_of_firstOrderStrongConvexOn
      hfirst hmem hxStar hfstar halpha_pos.le horth_disp
  exact
    chewi54_gap_sum_le_two_sqrt_condition_mul_gap_of_firstOrderStrongConvexOn
      hsmooth hfirst hmem hxStar hgrad_zero hfstar hgd_mem hcomp
      hstar_lower hbeta_pos halpha_pos hgap_mono hfirst_orth hgrad_orth

/--
Whole-space specialization of the source-facing CG Theorem 5.4 wrapper, suited
to the quadratic setting of the textbook.
-/
theorem chewi54_accelerated_bound_of_cgAffineMinimizer_univ
    {f : E -> ℝ} {grad : E -> E}
    {fstar alpha beta : ℝ} {x p : ℕ -> E} {xStar : E} {N : ℕ}
    (hsmooth : SmoothWithGradientOn Set.univ f grad beta)
    (hfirst : FirstOrderStrongConvexOn Set.univ f grad alpha)
    (hgrad_zero : grad xStar = 0)
    (hfstar : fstar = f xStar)
    (hmin : ∀ n, IsMinOn f (cgAffineSpan (x 0) p n) (x (n + 1)))
    (hx_span : ∀ n, x n - x 0 ∈ cgDirectionSubmodule p n)
    (hgrad_span : ∀ n, grad (x n) ∈ cgDirectionSubmodule p n)
    (horth_disp : ∀ n, n < N →
      inner ℝ (grad (x n)) (x n - x 0) = 0)
    (hgrad_orth : ∀ i j, i < N → j < N → i ≠ j →
      inner ℝ (grad (x i)) (grad (x j)) = 0)
    (hbeta_pos : 0 < beta)
    (halpha_pos : 0 < alpha) :
    (N : ℝ) * (f (x N) - fstar) ≤
      2 * Real.sqrt (beta / alpha) * (f (x 0) - fstar) := by
  exact chewi54_accelerated_bound_of_cgAffineMinimizer
    (C := Set.univ) hsmooth hfirst
    (by intro n; simp) (by simp) hgrad_zero hfstar
    (by intro n; simp) hmin hx_span hgrad_span horth_disp hgrad_orth
    hbeta_pos halpha_pos

/--
Quadratic displayed-CG specialization of the source-facing Theorem 5.4 wrapper.
The displayed recurrence supplies the search-span and orthogonality hypotheses;
the remaining algorithmic assumption is the defining affine minimization
property of CG.
-/
theorem IsCGDisplayedIteration.chewi54_accelerated_bound_of_cgAffineMinimizer
    {A : E →L[ℝ] E} {b p0 xStar : E} {x r p : ℕ -> E}
    {fstar alpha beta : ℝ} {N : ℕ}
    (h : IsCGDisplayedIteration A p0 r p)
    (hA_sym : IsSelfAdjointOperator A)
    (hsmooth :
      SmoothWithGradientOn Set.univ (quadraticObjective A b)
        (quadraticGradient A b) beta)
    (hfirst :
      FirstOrderStrongConvexOn Set.univ (quadraticObjective A b)
        (quadraticGradient A b) alpha)
    (hres0 : r 0 = quadraticGradient A b (x 0))
    (hpoint : ∀ n, x (n + 1) =
      x n + cgLineSearchCoeff A r p n • p n)
    (hmin : ∀ n,
      IsMinOn (quadraticObjective A b) (cgAffineSpan (x 0) p n)
        (x (n + 1)))
    (hgrad_zero : quadraticGradient A b xStar = 0)
    (hfstar : fstar = quadraticObjective A b xStar)
    (hbeta_pos : 0 < beta)
    (halpha_pos : 0 < alpha) :
    (N : ℝ) * (quadraticObjective A b (x N) - fstar) ≤
      2 * Real.sqrt (beta / alpha) *
        (quadraticObjective A b (x 0) - fstar) := by
  have hx_span :
      ∀ n, x n - x 0 ∈ cgDirectionSubmodule p n :=
    h.point_sub_initial_mem_cgDirectionSubmodule hpoint
  have hgrad_span :
      ∀ n, quadraticGradient A b (x n) ∈ cgDirectionSubmodule p n :=
    h.quadraticGradient_mem_cgDirectionSubmodule hres0 hpoint
  have horth_disp :
      ∀ n, n < N ->
        inner ℝ (quadraticGradient A b (x n)) (x n - x 0) = 0 := by
    intro n _hn
    exact h.quadraticGradient_orthogonal_displacement
      hA_sym hres0 hpoint n
  have hgrad_orth :
      ∀ i j, i < N → j < N → i ≠ j →
        inner ℝ (quadraticGradient A b (x i))
          (quadraticGradient A b (x j)) = 0 := by
    intro i j _hi _hj hij
    exact h.quadraticGradient_pairwise_orthogonal hA_sym hres0 hpoint i j hij
  exact chewi54_accelerated_bound_of_cgAffineMinimizer_univ
    hsmooth hfirst hgrad_zero hfstar hmin hx_span hgrad_span
    horth_disp hgrad_orth hbeta_pos halpha_pos

/--
Displayed-CG Theorem 5.4 rate wrapper from point/residual updates alone.  The
affine minimization property is derived from residual orthogonality and the
first-order strong-convexity lower model, so the theorem no longer assumes the
`argmin` property separately.
-/
theorem IsCGDisplayedIteration.chewi54_accelerated_bound_of_point_updates
    {A : E →L[ℝ] E} {b p0 xStar : E} {x r p : ℕ -> E}
    {fstar alpha beta : ℝ} {N : ℕ}
    (h : IsCGDisplayedIteration A p0 r p)
    (hA_sym : IsSelfAdjointOperator A)
    (hsmooth :
      SmoothWithGradientOn Set.univ (quadraticObjective A b)
        (quadraticGradient A b) beta)
    (hfirst :
      FirstOrderStrongConvexOn Set.univ (quadraticObjective A b)
        (quadraticGradient A b) alpha)
    (hres0 : r 0 = quadraticGradient A b (x 0))
    (hpoint : ∀ n, x (n + 1) =
      x n + cgLineSearchCoeff A r p n • p n)
    (hgrad_zero : quadraticGradient A b xStar = 0)
    (hfstar : fstar = quadraticObjective A b xStar)
    (hbeta_pos : 0 < beta)
    (halpha_pos : 0 < alpha) :
    (N : ℝ) * (quadraticObjective A b (x N) - fstar) ≤
      2 * Real.sqrt (beta / alpha) *
        (quadraticObjective A b (x 0) - fstar) := by
  have hmin :
      ∀ n, IsMinOn (quadraticObjective A b) (cgAffineSpan (x 0) p n)
        (x (n + 1)) :=
    h.isMinOn_cgAffineSpan_of_point_updates
      hA_sym hfirst halpha_pos.le hres0 hpoint
  exact h.chewi54_accelerated_bound_of_cgAffineMinimizer
    hA_sym hsmooth hfirst hres0 hpoint hmin hgrad_zero hfstar
    hbeta_pos halpha_pos

/--
Canonical integer block size for the restart presentation of Chewi Theorem
5.4.
-/
noncomputable def chewi54BlockSize (alpha beta : ℝ) : ℕ :=
  ⌈4 * Real.sqrt (beta / alpha)⌉₊

theorem chewi54_four_sqrt_le_blockSize (alpha beta : ℝ) :
    4 * Real.sqrt (beta / alpha) ≤
      (chewi54BlockSize alpha beta : ℝ) := by
  simpa [chewi54BlockSize] using
    Nat.le_ceil (4 * Real.sqrt (beta / alpha))

/--
Block-halving bridge for Chewi Theorem 5.4.  The accelerated estimate on one
block, together with an integer block length at least `4 * sqrt(beta / alpha)`,
forces the objective gap at the end of the block to be at most half the gap at
the start.
-/
theorem chewi54_block_halving_of_accelerated_block_bound
    {alpha beta gapStart gapEnd : ℝ} {B : ℕ}
    (hblock : (B : ℝ) * gapEnd ≤
      2 * Real.sqrt (beta / alpha) * gapStart)
    (hB : 4 * Real.sqrt (beta / alpha) ≤ (B : ℝ))
    (hgapEnd_nonneg : 0 ≤ gapEnd)
    (halpha_pos : 0 < alpha) (hbeta_pos : 0 < beta) :
    gapEnd ≤ (1 / 2 : ℝ) * gapStart := by
  let s := Real.sqrt (beta / alpha)
  have hs_pos : 0 < s := by
    exact Real.sqrt_pos.2 (div_pos hbeta_pos halpha_pos)
  have hleft : (4 * s) * gapEnd ≤ (B : ℝ) * gapEnd := by
    exact mul_le_mul_of_nonneg_right hB hgapEnd_nonneg
  have hcombined : (4 * s) * gapEnd ≤ 2 * s * gapStart := by
    exact hleft.trans hblock
  have htwo_pos : 0 < 2 * s := by nlinarith
  have hdiv : ((4 * s) * gapEnd) / (2 * s) ≤ gapStart := by
    rw [div_le_iff₀ htwo_pos]
    calc
      (4 * s) * gapEnd ≤ 2 * s * gapStart := hcombined
      _ = gapStart * (2 * s) := by ring
  have hratio : ((4 * s) * gapEnd) / (2 * s) = 2 * gapEnd := by
    field_simp [hs_pos.ne']
    ring
  have htwo_gap : 2 * gapEnd ≤ gapStart := by
    simpa [hratio] using hdiv
  nlinarith

/--
The block-halving recurrence obtained by applying the accelerated block bound
at every restart block.
-/
theorem chewi54_block_halving_recurrence_of_accelerated_block_bounds
    {alpha beta : ℝ} {gap : ℕ -> ℝ} {B : ℕ}
    (hblock : ∀ m,
      (B : ℝ) * gap ((m + 1) * B) ≤
        2 * Real.sqrt (beta / alpha) * gap (m * B))
    (hB : 4 * Real.sqrt (beta / alpha) ≤ (B : ℝ))
    (hgap_nonneg : ∀ n, 0 ≤ gap n)
    (halpha_pos : 0 < alpha) (hbeta_pos : 0 < beta) :
    ∀ m, gap ((m + 1) * B) ≤ (1 / 2 : ℝ) * gap (m * B) := by
  intro m
  exact chewi54_block_halving_of_accelerated_block_bound
    (alpha := alpha) (beta := beta) (gapStart := gap (m * B))
    (gapEnd := gap ((m + 1) * B)) (B := B) (hblock m) hB
    (hgap_nonneg _) halpha_pos hbeta_pos

/--
Chewi Theorem 5.4 restart algebra.  If each block of `B` conjugate-gradient
iterations halves the objective gap, then after `M` blocks the gap is bounded
by the `M`-th power of `1 / 2`.
-/
theorem chewi54_halvingBlocks_gap_le
    {gap : ℕ -> ℝ} {B : ℕ}
    (hhalve : ∀ m,
      gap ((m + 1) * B) ≤ (1 / 2 : ℝ) * gap (m * B)) :
    ∀ M, gap (M * B) ≤ (1 / 2 : ℝ) ^ M * gap 0 := by
  intro M
  let u : ℕ -> ℝ := fun m => gap (m * B)
  have hrec : ∀ m, u (m + 1) ≤ (1 / 2 : ℝ) * u m := by
    intro m
    simpa [u] using hhalve m
  have hpow :=
    scalarRecurrence_le_pow (u := u) (A := (1 / 2 : ℝ))
      (by norm_num) hrec M
  simpa [u] using hpow

/--
Source-facing endpoint form of the restart algebra: a separately supplied
power estimate on the halving factor gives the target accuracy.
-/
theorem chewi54_halvingBlocks_gap_le_of_power_bound
    {gap : ℕ -> ℝ} {B M : ℕ} {eps : ℝ}
    (hhalve : ∀ m,
      gap ((m + 1) * B) ≤ (1 / 2 : ℝ) * gap (m * B))
    (hpow_eps : (1 / 2 : ℝ) ^ M * gap 0 ≤ eps) :
    gap (M * B) ≤ eps :=
  (chewi54_halvingBlocks_gap_le (gap := gap) (B := B) hhalve M).trans
    hpow_eps

/--
Logarithmic sufficient condition for the halving power bound.  This is the
scalar calculation behind the textbook phrase that halving every block gives
`O(sqrt(kappa) log(gap_0 / eps))` iterations.
-/
theorem chewi54_half_pow_mul_le_eps_of_log_ratio_le
    {gap0 eps : ℝ} {M : ℕ}
    (hgap0_pos : 0 < gap0) (heps_pos : 0 < eps)
    (hM_log : Real.log (gap0 / eps) ≤ (M : ℝ) * Real.log (2 : ℝ)) :
    (1 / 2 : ℝ) ^ M * gap0 ≤ eps := by
  have hhalf_pos : 0 < (1 / 2 : ℝ) := by norm_num
  have hpow_pos : 0 < (1 / 2 : ℝ) ^ M := pow_pos hhalf_pos M
  have hleft_pos : 0 < (1 / 2 : ℝ) ^ M * gap0 :=
    mul_pos hpow_pos hgap0_pos
  have hlog_half : Real.log (1 / 2 : ℝ) = -Real.log (2 : ℝ) := by
    have hhalf : (1 / 2 : ℝ) = (2 : ℝ)⁻¹ := by norm_num
    rw [hhalf, Real.log_inv]
  have hlog_ratio :
      Real.log (gap0 / eps) = Real.log gap0 - Real.log eps := by
    rw [Real.log_div hgap0_pos.ne' heps_pos.ne']
  have hlog_left :
      Real.log ((1 / 2 : ℝ) ^ M * gap0) =
        (M : ℝ) * Real.log (1 / 2 : ℝ) + Real.log gap0 := by
    rw [Real.log_mul hpow_pos.ne' hgap0_pos.ne', Real.log_pow]
  have hlog_le : Real.log ((1 / 2 : ℝ) ^ M * gap0) ≤ Real.log eps := by
    rw [hlog_left, hlog_half]
    have hM_log' :
        Real.log gap0 - Real.log eps ≤ (M : ℝ) * Real.log (2 : ℝ) := by
      simpa [hlog_ratio] using hM_log
    linarith
  exact (Real.log_le_log_iff hleft_pos heps_pos).mp hlog_le

/--
Logarithmic source-facing restart endpoint for Chewi Theorem 5.4: once the
one-block halving property is available, the usual log-ratio condition implies
the requested accuracy after `M` blocks.
-/
theorem chewi54_halvingBlocks_gap_le_of_log_ratio_le
    {gap : ℕ -> ℝ} {B M : ℕ} {eps : ℝ}
    (hhalve : ∀ m,
      gap ((m + 1) * B) ≤ (1 / 2 : ℝ) * gap (m * B))
    (hgap0_pos : 0 < gap 0) (heps_pos : 0 < eps)
    (hM_log : Real.log ((gap 0) / eps) ≤
      (M : ℝ) * Real.log (2 : ℝ)) :
    gap (M * B) ≤ eps :=
  chewi54_halvingBlocks_gap_le_of_power_bound
    (gap := gap) (B := B) (M := M) (eps := eps) hhalve
    (chewi54_half_pow_mul_le_eps_of_log_ratio_le
      hgap0_pos heps_pos hM_log)

/--
Source-facing logarithmic endpoint from accelerated block estimates.  This is
the scalar restart shell around Chewi Theorem 5.4: prove the accelerated bound
on each block, choose a block length at least `4 * sqrt(beta / alpha)`, and the
log-ratio condition gives the target accuracy after `M` blocks.
-/
theorem chewi54_log_rate_of_accelerated_block_bounds
    {alpha beta : ℝ} {gap : ℕ -> ℝ} {B M : ℕ} {eps : ℝ}
    (hblock : ∀ m,
      (B : ℝ) * gap ((m + 1) * B) ≤
        2 * Real.sqrt (beta / alpha) * gap (m * B))
    (hB : 4 * Real.sqrt (beta / alpha) ≤ (B : ℝ))
    (hgap_nonneg : ∀ n, 0 ≤ gap n)
    (hgap0_pos : 0 < gap 0) (heps_pos : 0 < eps)
    (halpha_pos : 0 < alpha) (hbeta_pos : 0 < beta)
    (hM_log : Real.log ((gap 0) / eps) ≤
      (M : ℝ) * Real.log (2 : ℝ)) :
    gap (M * B) ≤ eps :=
  chewi54_halvingBlocks_gap_le_of_log_ratio_le
    (gap := gap) (B := B) (M := M) (eps := eps)
    (chewi54_block_halving_recurrence_of_accelerated_block_bounds
      hblock hB hgap_nonneg halpha_pos hbeta_pos)
    hgap0_pos heps_pos hM_log

/--
Ceiling-block specialization of the restart shell.  The block size is the
source-natural integer ceiling of `4 * sqrt(beta / alpha)`.
-/
theorem chewi54_log_rate_of_accelerated_block_bounds_blockSize
    {alpha beta : ℝ} {gap : ℕ -> ℝ} {M : ℕ} {eps : ℝ}
    (hblock : ∀ m,
      (chewi54BlockSize alpha beta : ℝ) *
          gap ((m + 1) * chewi54BlockSize alpha beta) ≤
        2 * Real.sqrt (beta / alpha) *
          gap (m * chewi54BlockSize alpha beta))
    (hgap_nonneg : ∀ n, 0 ≤ gap n)
    (hgap0_pos : 0 < gap 0) (heps_pos : 0 < eps)
    (halpha_pos : 0 < alpha) (hbeta_pos : 0 < beta)
    (hM_log : Real.log ((gap 0) / eps) ≤
      (M : ℝ) * Real.log (2 : ℝ)) :
    gap (M * chewi54BlockSize alpha beta) ≤ eps :=
  chewi54_log_rate_of_accelerated_block_bounds
    (alpha := alpha) (beta := beta) (gap := gap)
    (B := chewi54BlockSize alpha beta) (M := M) (eps := eps)
    hblock (chewi54_four_sqrt_le_blockSize alpha beta) hgap_nonneg
    hgap0_pos heps_pos halpha_pos hbeta_pos hM_log

/--
Per-block accelerated estimate from the existing affine-minimizer CG Theorem
5.4 wrapper, applied to the shifted sequence inside one restart block.
-/
theorem chewi54_block_bound_of_cgAffineMinimizer_blocks
    {C : Set E} {f : E -> ℝ} {grad : E -> E}
    {fstar alpha beta : ℝ} {x : ℕ -> E} {p : ℕ -> ℕ -> E}
    {xStar : E} {B : ℕ}
    (hsmooth : SmoothWithGradientOn C f grad beta)
    (hfirst : FirstOrderStrongConvexOn C f grad alpha)
    (hmem : ∀ n, x n ∈ C)
    (hxStar : xStar ∈ C)
    (hgrad_zero : grad xStar = 0)
    (hfstar : fstar = f xStar)
    (hgd_mem : ∀ n, gradientDescentStep grad (1 / beta) (x n) ∈ C)
    (hmin : ∀ m n,
      IsMinOn f (cgAffineSpan (x (m * B)) (p m) n)
        (x (m * B + (n + 1))))
    (hx_span : ∀ m n,
      x (m * B + n) - x (m * B) ∈ cgDirectionSubmodule (p m) n)
    (hgrad_span : ∀ m n,
      grad (x (m * B + n)) ∈ cgDirectionSubmodule (p m) n)
    (horth_disp : ∀ m n, n < B →
      inner ℝ (grad (x (m * B + n)))
        (x (m * B + n) - x (m * B)) = 0)
    (hgrad_orth : ∀ m i j, i < B → j < B → i ≠ j →
      inner ℝ (grad (x (m * B + i)))
        (grad (x (m * B + j))) = 0)
    (hbeta_pos : 0 < beta)
    (halpha_pos : 0 < alpha) :
    ∀ m,
      (B : ℝ) * (f (x ((m + 1) * B)) - fstar) ≤
        2 * Real.sqrt (beta / alpha) * (f (x (m * B)) - fstar) := by
  intro m
  let y : ℕ -> E := fun n => x (m * B + n)
  have hblock :
      (B : ℝ) * (f (y B) - fstar) ≤
        2 * Real.sqrt (beta / alpha) * (f (y 0) - fstar) := by
    exact chewi54_accelerated_bound_of_cgAffineMinimizer
      (C := C) (f := f) (grad := grad) (fstar := fstar)
      (alpha := alpha) (beta := beta) (x := y) (p := p m)
      (xStar := xStar) (N := B)
      hsmooth hfirst
      (by intro n; exact hmem _)
      hxStar hgrad_zero hfstar
      (by intro n; exact hgd_mem _)
      (by intro n; simpa [y] using hmin m n)
      (by intro n; simpa [y] using hx_span m n)
      (by intro n; simpa [y] using hgrad_span m n)
      (by intro n hn; simpa [y] using horth_disp m n hn)
      (by intro i j hi hj hij; simpa [y] using hgrad_orth m i j hi hj hij)
      hbeta_pos halpha_pos
  simpa [y, Nat.succ_mul, Nat.add_comm, Nat.add_left_comm, Nat.add_assoc]
    using hblock

/--
Restarted affine-minimizer CG logarithmic endpoint.  This combines the
blockwise shifted Theorem 5.4 estimate with the compiled integer-block restart
shell.
-/
theorem chewi54_log_rate_of_cgAffineMinimizer_blocks
    {C : Set E} {f : E -> ℝ} {grad : E -> E}
    {fstar alpha beta : ℝ} {x : ℕ -> E} {p : ℕ -> ℕ -> E}
    {xStar : E} {B M : ℕ} {eps : ℝ}
    (hsmooth : SmoothWithGradientOn C f grad beta)
    (hfirst : FirstOrderStrongConvexOn C f grad alpha)
    (hmem : ∀ n, x n ∈ C)
    (hxStar : xStar ∈ C)
    (hgrad_zero : grad xStar = 0)
    (hfstar : fstar = f xStar)
    (hgd_mem : ∀ n, gradientDescentStep grad (1 / beta) (x n) ∈ C)
    (hmin : ∀ m n,
      IsMinOn f (cgAffineSpan (x (m * B)) (p m) n)
        (x (m * B + (n + 1))))
    (hx_span : ∀ m n,
      x (m * B + n) - x (m * B) ∈ cgDirectionSubmodule (p m) n)
    (hgrad_span : ∀ m n,
      grad (x (m * B + n)) ∈ cgDirectionSubmodule (p m) n)
    (horth_disp : ∀ m n, n < B →
      inner ℝ (grad (x (m * B + n)))
        (x (m * B + n) - x (m * B)) = 0)
    (hgrad_orth : ∀ m i j, i < B → j < B → i ≠ j →
      inner ℝ (grad (x (m * B + i)))
        (grad (x (m * B + j))) = 0)
    (hB : 4 * Real.sqrt (beta / alpha) ≤ (B : ℝ))
    (hgap0_pos : 0 < f (x 0) - fstar)
    (heps_pos : 0 < eps)
    (halpha_pos : 0 < alpha)
    (hbeta_pos : 0 < beta)
    (hM_log : Real.log ((f (x 0) - fstar) / eps) ≤
      (M : ℝ) * Real.log (2 : ℝ)) :
    f (x (M * B)) - fstar ≤ eps := by
  let gap : ℕ -> ℝ := fun n => f (x n) - fstar
  have hstar_lower : ∀ n, fstar ≤ f (x n) :=
    chewi54_star_lower_of_firstOrderStrongConvexOn
      hfirst hmem hxStar hgrad_zero hfstar halpha_pos.le
  have hgap_nonneg : ∀ n, 0 ≤ gap n := by
    intro n
    exact sub_nonneg.mpr (hstar_lower n)
  have hblock : ∀ m,
      (B : ℝ) * gap ((m + 1) * B) ≤
        2 * Real.sqrt (beta / alpha) * gap (m * B) := by
    intro m
    simpa [gap] using
      chewi54_block_bound_of_cgAffineMinimizer_blocks
        hsmooth hfirst hmem hxStar hgrad_zero hfstar hgd_mem hmin
        hx_span hgrad_span horth_disp hgrad_orth hbeta_pos halpha_pos m
  exact chewi54_log_rate_of_accelerated_block_bounds
    (alpha := alpha) (beta := beta) (gap := gap) (B := B) (M := M)
    (eps := eps) hblock hB hgap_nonneg
    (by simpa [gap] using hgap0_pos) heps_pos halpha_pos hbeta_pos
    (by simpa [gap] using hM_log)

/--
Ceiling-block specialization of the restarted affine-minimizer CG logarithmic
endpoint.
-/
theorem chewi54_log_rate_of_cgAffineMinimizer_blocks_blockSize
    {C : Set E} {f : E -> ℝ} {grad : E -> E}
    {fstar alpha beta : ℝ} {x : ℕ -> E} {p : ℕ -> ℕ -> E}
    {xStar : E} {M : ℕ} {eps : ℝ}
    (hsmooth : SmoothWithGradientOn C f grad beta)
    (hfirst : FirstOrderStrongConvexOn C f grad alpha)
    (hmem : ∀ n, x n ∈ C)
    (hxStar : xStar ∈ C)
    (hgrad_zero : grad xStar = 0)
    (hfstar : fstar = f xStar)
    (hgd_mem : ∀ n, gradientDescentStep grad (1 / beta) (x n) ∈ C)
    (hmin : ∀ m n,
      IsMinOn f
        (cgAffineSpan (x (m * chewi54BlockSize alpha beta)) (p m) n)
        (x (m * chewi54BlockSize alpha beta + (n + 1))))
    (hx_span : ∀ m n,
      x (m * chewi54BlockSize alpha beta + n) -
          x (m * chewi54BlockSize alpha beta) ∈
        cgDirectionSubmodule (p m) n)
    (hgrad_span : ∀ m n,
      grad (x (m * chewi54BlockSize alpha beta + n)) ∈
        cgDirectionSubmodule (p m) n)
    (horth_disp : ∀ m n, n < chewi54BlockSize alpha beta →
      inner ℝ (grad (x (m * chewi54BlockSize alpha beta + n)))
        (x (m * chewi54BlockSize alpha beta + n) -
          x (m * chewi54BlockSize alpha beta)) = 0)
    (hgrad_orth : ∀ m i j,
      i < chewi54BlockSize alpha beta →
      j < chewi54BlockSize alpha beta → i ≠ j →
      inner ℝ (grad (x (m * chewi54BlockSize alpha beta + i)))
        (grad (x (m * chewi54BlockSize alpha beta + j))) = 0)
    (hgap0_pos : 0 < f (x 0) - fstar)
    (heps_pos : 0 < eps)
    (halpha_pos : 0 < alpha)
    (hbeta_pos : 0 < beta)
    (hM_log : Real.log ((f (x 0) - fstar) / eps) ≤
      (M : ℝ) * Real.log (2 : ℝ)) :
    f (x (M * chewi54BlockSize alpha beta)) - fstar ≤ eps :=
  chewi54_log_rate_of_cgAffineMinimizer_blocks
    (B := chewi54BlockSize alpha beta)
    hsmooth hfirst hmem hxStar hgrad_zero hfstar hgd_mem hmin hx_span
    hgrad_span horth_disp hgrad_orth
    (chewi54_four_sqrt_le_blockSize alpha beta)
    hgap0_pos heps_pos halpha_pos hbeta_pos hM_log

/--
Displayed/restarted CG logarithmic endpoint, with one displayed CG record per
restart block.  The existing displayed-CG bridges discharge the search-span,
gradient-span, orthogonality, and affine-minimizer hypotheses required by the
restarted affine-minimizer theorem.
-/
theorem chewi54_log_rate_of_displayed_cg_blocks
    {A : E →L[ℝ] E} {b xStar : E}
    {p0 : ℕ -> E} {x : ℕ -> E} {r p : ℕ -> ℕ -> E}
    {fstar alpha beta : ℝ} {B M : ℕ} {eps : ℝ}
    (h : ∀ m, IsCGDisplayedIteration A (p0 m) (r m) (p m))
    (hA_sym : IsSelfAdjointOperator A)
    (hsmooth :
      SmoothWithGradientOn Set.univ (quadraticObjective A b)
        (quadraticGradient A b) beta)
    (hfirst :
      FirstOrderStrongConvexOn Set.univ (quadraticObjective A b)
        (quadraticGradient A b) alpha)
    (hres0 : ∀ m, r m 0 = quadraticGradient A b (x (m * B)))
    (hpoint : ∀ m n, x (m * B + (n + 1)) =
      x (m * B + n) + cgLineSearchCoeff A (r m) (p m) n • p m n)
    (hgrad_zero : quadraticGradient A b xStar = 0)
    (hfstar : fstar = quadraticObjective A b xStar)
    (hB : 4 * Real.sqrt (beta / alpha) ≤ (B : ℝ))
    (hgap0_pos : 0 < quadraticObjective A b (x 0) - fstar)
    (heps_pos : 0 < eps)
    (halpha_pos : 0 < alpha)
    (hbeta_pos : 0 < beta)
    (hM_log :
      Real.log ((quadraticObjective A b (x 0) - fstar) / eps) ≤
        (M : ℝ) * Real.log (2 : ℝ)) :
    quadraticObjective A b (x (M * B)) - fstar ≤ eps := by
  have hmin : ∀ m n,
      IsMinOn (quadraticObjective A b)
        (cgAffineSpan (x (m * B)) (p m) n)
        (x (m * B + (n + 1))) := by
    intro m n
    let y : ℕ -> E := fun k => x (m * B + k)
    have hpoint_m : ∀ k, y (k + 1) =
        y k + cgLineSearchCoeff A (r m) (p m) k • p m k := by
      intro k
      simpa [y] using hpoint m k
    have hmin_m :=
      (h m).isMinOn_cgAffineSpan_of_point_updates
        hA_sym hfirst halpha_pos.le (by simpa [y] using hres0 m)
        hpoint_m n
    simpa [y] using hmin_m
  have hx_span : ∀ m n,
      x (m * B + n) - x (m * B) ∈ cgDirectionSubmodule (p m) n := by
    intro m n
    let y : ℕ -> E := fun k => x (m * B + k)
    have hpoint_m : ∀ k, y (k + 1) =
        y k + cgLineSearchCoeff A (r m) (p m) k • p m k := by
      intro k
      simpa [y] using hpoint m k
    have hspan_m :=
      (h m).point_sub_initial_mem_cgDirectionSubmodule hpoint_m n
    simpa [y] using hspan_m
  have hgrad_span : ∀ m n,
      quadraticGradient A b (x (m * B + n)) ∈
        cgDirectionSubmodule (p m) n := by
    intro m n
    let y : ℕ -> E := fun k => x (m * B + k)
    have hpoint_m : ∀ k, y (k + 1) =
        y k + cgLineSearchCoeff A (r m) (p m) k • p m k := by
      intro k
      simpa [y] using hpoint m k
    have hspan_m :=
      (h m).quadraticGradient_mem_cgDirectionSubmodule
        (b := b) (x := y) (by simpa [y] using hres0 m) hpoint_m n
    simpa [y] using hspan_m
  have horth_disp : ∀ m n, n < B →
      inner ℝ (quadraticGradient A b (x (m * B + n)))
        (x (m * B + n) - x (m * B)) = 0 := by
    intro m n _hn
    let y : ℕ -> E := fun k => x (m * B + k)
    have hpoint_m : ∀ k, y (k + 1) =
        y k + cgLineSearchCoeff A (r m) (p m) k • p m k := by
      intro k
      simpa [y] using hpoint m k
    have horth_m :=
      (h m).quadraticGradient_orthogonal_displacement
        hA_sym (b := b) (x := y) (by simpa [y] using hres0 m)
        hpoint_m n
    simpa [y] using horth_m
  have hgrad_orth : ∀ m i j, i < B → j < B → i ≠ j →
      inner ℝ (quadraticGradient A b (x (m * B + i)))
        (quadraticGradient A b (x (m * B + j))) = 0 := by
    intro m i j _hi _hj hij
    let y : ℕ -> E := fun k => x (m * B + k)
    have hpoint_m : ∀ k, y (k + 1) =
        y k + cgLineSearchCoeff A (r m) (p m) k • p m k := by
      intro k
      simpa [y] using hpoint m k
    have horth_m :=
      (h m).quadraticGradient_pairwise_orthogonal
        hA_sym (b := b) (x := y) (by simpa [y] using hres0 m)
        hpoint_m i j hij
    simpa [y] using horth_m
  exact chewi54_log_rate_of_cgAffineMinimizer_blocks
    (C := Set.univ) (f := quadraticObjective A b)
    (grad := quadraticGradient A b) (fstar := fstar)
    (alpha := alpha) (beta := beta) (x := x) (p := p)
    (xStar := xStar) (B := B) (M := M) (eps := eps)
    hsmooth hfirst (by intro n; simp) (by simp) hgrad_zero hfstar
    (by intro n; simp) hmin hx_span hgrad_span horth_disp hgrad_orth
    hB hgap0_pos heps_pos halpha_pos hbeta_pos hM_log

/--
Ceiling-block specialization of the displayed/restarted CG logarithmic
endpoint.
-/
theorem chewi54_log_rate_of_displayed_cg_blocks_blockSize
    {A : E →L[ℝ] E} {b xStar : E}
    {p0 : ℕ -> E} {x : ℕ -> E} {r p : ℕ -> ℕ -> E}
    {fstar alpha beta : ℝ} {M : ℕ} {eps : ℝ}
    (h : ∀ m, IsCGDisplayedIteration A (p0 m) (r m) (p m))
    (hA_sym : IsSelfAdjointOperator A)
    (hsmooth :
      SmoothWithGradientOn Set.univ (quadraticObjective A b)
        (quadraticGradient A b) beta)
    (hfirst :
      FirstOrderStrongConvexOn Set.univ (quadraticObjective A b)
        (quadraticGradient A b) alpha)
    (hres0 : ∀ m,
      r m 0 = quadraticGradient A b (x (m * chewi54BlockSize alpha beta)))
    (hpoint : ∀ m n,
      x (m * chewi54BlockSize alpha beta + (n + 1)) =
        x (m * chewi54BlockSize alpha beta + n) +
          cgLineSearchCoeff A (r m) (p m) n • p m n)
    (hgrad_zero : quadraticGradient A b xStar = 0)
    (hfstar : fstar = quadraticObjective A b xStar)
    (hgap0_pos : 0 < quadraticObjective A b (x 0) - fstar)
    (heps_pos : 0 < eps)
    (halpha_pos : 0 < alpha)
    (hbeta_pos : 0 < beta)
    (hM_log :
      Real.log ((quadraticObjective A b (x 0) - fstar) / eps) ≤
        (M : ℝ) * Real.log (2 : ℝ)) :
    quadraticObjective A b
        (x (M * chewi54BlockSize alpha beta)) - fstar ≤ eps :=
  chewi54_log_rate_of_displayed_cg_blocks
    (B := chewi54BlockSize alpha beta) h hA_sym hsmooth hfirst hres0 hpoint
    hgrad_zero hfstar (chewi54_four_sqrt_le_blockSize alpha beta)
    hgap0_pos heps_pos halpha_pos hbeta_pos hM_log

end Optimization
end StatInference
