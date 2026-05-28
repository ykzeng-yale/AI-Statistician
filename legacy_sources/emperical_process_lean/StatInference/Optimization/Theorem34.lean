import StatInference.Optimization.GradientDescent

/-!
# Chewi Theorem 3.4 assembly lemmas

This module starts the supplied-interface assembly layer for Chewi Theorem 3.4,
the function-value convergence theorem for smooth gradient descent.  The first
result packages the finite weighted-sum inequality obtained by applying the
compiled discrete Gronwall lemma to the one-step recurrence (3.1).
-/

namespace StatInference
namespace Optimization

open Finset
open scoped InnerProductSpace

/--
Generic weighted-sum consequence of a discrete Gronwall recurrence with a
negative forcing term.

This is the algebraic core of the post-Lemma 3.5 step in Chewi Theorem 3.4.
-/
theorem weightedSumBound_of_gronwall_negative_forcing
    {A h : ℝ} (hA : 0 ≤ A) (u gap : ℕ -> ℝ) (N : ℕ)
    (huN_nonneg : 0 ≤ u N)
    (hrec : ∀ n, n < N ->
      u (n + 1) ≤ A * u n - 2 * h * gap (n + 1)) :
    2 * h *
        (∑ n ∈ Finset.range N, A ^ (N - 1 - n) * gap (n + 1)) ≤
      A ^ N * u 0 := by
  let B : ℕ -> ℝ := fun n => -2 * h * gap (n + 1)
  have hrec' : ∀ n, n < N -> u (n + 1) ≤ A * u n + B n := by
    intro n hn
    have h := hrec n hn
    simpa [B, sub_eq_add_neg, mul_assoc] using h
  have hgr :=
    discreteGronwall_sum_le hA u B N hrec'
  have hrhs_nonneg :
      0 ≤ A ^ N * u 0 +
        ∑ n ∈ Finset.range N, A ^ (N - 1 - n) * B n :=
    huN_nonneg.trans hgr
  have hsum :
      (∑ n ∈ Finset.range N, A ^ (N - 1 - n) * B n) =
        -(2 * h) *
          (∑ n ∈ Finset.range N, A ^ (N - 1 - n) * gap (n + 1)) := by
    calc
      (∑ n ∈ Finset.range N, A ^ (N - 1 - n) * B n)
          =
            ∑ n ∈ Finset.range N,
              -(2 * h) * (A ^ (N - 1 - n) * gap (n + 1)) := by
              refine Finset.sum_congr rfl ?_
              intro n hn
              simp [B]
              ring
      _ =
            -(2 * h) *
              (∑ n ∈ Finset.range N, A ^ (N - 1 - n) * gap (n + 1)) := by
              rw [Finset.mul_sum]
  have hnonneg :
      0 ≤ A ^ N * u 0 -
        2 * h *
          (∑ n ∈ Finset.range N, A ^ (N - 1 - n) * gap (n + 1)) := by
    simpa [hsum] using hrhs_nonneg
  nlinarith

/--
If every indexed gap in the weighted sum dominates a final gap, then the
weighted sum dominates the final gap times the total weight.
-/
theorem weightedFinalGap_le_weightedGapSum
    {A h finalGap : ℝ} (hA : 0 ≤ A) (hh : 0 ≤ h)
    (gap : ℕ -> ℝ) (N : ℕ)
    (hmono : ∀ n, n < N -> finalGap ≤ gap (n + 1)) :
    2 * h *
        ((∑ n ∈ Finset.range N, A ^ (N - 1 - n)) * finalGap) ≤
      2 * h *
        (∑ n ∈ Finset.range N, A ^ (N - 1 - n) * gap (n + 1)) := by
  have hsum_le :
      (∑ n ∈ Finset.range N, A ^ (N - 1 - n)) * finalGap ≤
        ∑ n ∈ Finset.range N, A ^ (N - 1 - n) * gap (n + 1) := by
    rw [Finset.sum_mul]
    refine Finset.sum_le_sum ?_
    intro n hn
    exact mul_le_mul_of_nonneg_left
      (hmono n (Finset.mem_range.mp hn)) (pow_nonneg hA _)
  have htwoh : 0 ≤ 2 * h := by nlinarith
  exact mul_le_mul_of_nonneg_left hsum_le htwoh

/--
The reversed geometric weights used by Chewi's zero-based Gronwall display are
the usual geometric sum.
-/
theorem geometricWeights_sum_eq_geom_sum {A : ℝ} (N : ℕ) :
    (∑ n ∈ Finset.range N, A ^ (N - 1 - n)) =
      ∑ n ∈ Finset.range N, A ^ n := by
  simpa using Finset.sum_range_reflect (fun n => A ^ n) N

/-- Positivity of the finite geometric denominator in Theorem 3.4. -/
theorem geometricWeights_sum_pos {A : ℝ} (hA : 0 ≤ A)
    {N : ℕ} (hN : N ≠ 0) :
    0 < ∑ n ∈ Finset.range N, A ^ (N - 1 - n) := by
  rw [geometricWeights_sum_eq_geom_sum]
  exact geom_sum_pos hA hN

/-- Closed form of the finite geometric denominator for `A ≠ 1`. -/
theorem geometricWeights_sum_eq_div {A : ℝ} (hA : A ≠ 1) (N : ℕ) :
    (∑ n ∈ Finset.range N, A ^ (N - 1 - n)) =
      (1 - A ^ N) / (1 - A) := by
  rw [geometricWeights_sum_eq_geom_sum]
  have hgeom :=
    geom_sum_Ico' (x := A) hA (m := 0) (n := N) (Nat.zero_le N)
  simpa using hgeom

/-- The `alpha = 0` geometric weights collapse to the number of steps. -/
theorem geometricWeights_sum_one (N : ℕ) :
    (∑ n ∈ Finset.range N, (1 : ℝ) ^ (N - 1 - n)) = N := by
  rw [geometricWeights_sum_eq_geom_sum]
  exact one_geom_sum N

/--
Chewi Theorem 3.4 weighted finite-sum bound, assuming the one-step recurrence
(3.1) as a supplied interface.
-/
theorem chewi34_weighted_sum_bound_of_one_step
    {E : Type*} [NormedAddCommGroup E]
    {f : E -> ℝ} {x : ℕ -> E} {xStar : E} {alpha h : ℝ}
    (hfactor : 0 ≤ 1 - alpha * h)
    (hone_step : ∀ n,
      ‖x (n + 1) - xStar‖ ^ (2 : ℕ) ≤
        (1 - alpha * h) * ‖x n - xStar‖ ^ (2 : ℕ) -
          2 * h * (f (x (n + 1)) - f xStar))
    (N : ℕ) :
    2 * h *
        (∑ n ∈ Finset.range N,
          (1 - alpha * h) ^ (N - 1 - n) *
            (f (x (n + 1)) - f xStar)) ≤
      (1 - alpha * h) ^ N * ‖x 0 - xStar‖ ^ (2 : ℕ) := by
  let u : ℕ -> ℝ := fun n => ‖x n - xStar‖ ^ (2 : ℕ)
  let gap : ℕ -> ℝ := fun n => f (x n) - f xStar
  have huN_nonneg : 0 ≤ u N := sq_nonneg ‖x N - xStar‖
  have hrec : ∀ n, n < N ->
      u (n + 1) ≤ (1 - alpha * h) * u n - 2 * h * gap (n + 1) := by
    intro n hn
    simpa [u, gap] using hone_step n
  simpa [u, gap] using
    weightedSumBound_of_gronwall_negative_forcing
      (A := 1 - alpha * h) (h := h) hfactor u gap N huN_nonneg hrec

/--
Source-indexed version of `chewi34_weighted_sum_bound_of_one_step`, matching
the display after Lemma 3.5 in Chewi's proof of Theorem 3.4.
-/
theorem chewi34_weighted_sum_bound_one_based_of_one_step
    {E : Type*} [NormedAddCommGroup E]
    {f : E -> ℝ} {x : ℕ -> E} {xStar : E} {alpha h : ℝ}
    (hfactor : 0 ≤ 1 - alpha * h)
    (hone_step : ∀ n,
      ‖x (n + 1) - xStar‖ ^ (2 : ℕ) ≤
        (1 - alpha * h) * ‖x n - xStar‖ ^ (2 : ℕ) -
          2 * h * (f (x (n + 1)) - f xStar))
    (N : ℕ) :
    2 * h *
        (∑ n ∈ Finset.Ico 1 (N + 1),
          (1 - alpha * h) ^ (N - n) * (f (x n) - f xStar)) ≤
      (1 - alpha * h) ^ N * ‖x 0 - xStar‖ ^ (2 : ℕ) := by
  have hzero :=
    chewi34_weighted_sum_bound_of_one_step hfactor hone_step N
  have hsum :
      (∑ n ∈ Finset.range N,
          (1 - alpha * h) ^ (N - 1 - n) *
            (f (x (n + 1)) - f xStar)) =
        ∑ n ∈ Finset.Ico 1 (N + 1),
          (1 - alpha * h) ^ (N - n) * (f (x n) - f xStar) := by
    rw [Finset.sum_Ico_eq_sum_range]
    refine Finset.sum_congr ?_ ?_
    · simp
    · intro n hn
      have hsub : N - (1 + n) = N - 1 - n := by
        omega
      rw [hsub]
      have hadd : n + 1 = 1 + n := by
        omega
      rw [hadd]
  simpa [hsum] using hzero

/--
Chewi Theorem 3.4 monotone-gap weighted lower bound, using a supplied
monotonicity estimate from Lemma 3.1.
-/
theorem chewi34_weighted_final_gap_le_weighted_gap_sum
    {E : Type*}
    {f : E -> ℝ} {x : ℕ -> E} {xStar : E} {alpha h : ℝ}
    (hfactor : 0 ≤ 1 - alpha * h)
    (hh : 0 ≤ h)
    (N : ℕ)
    (hmono : ∀ n, n < N -> f (x N) - f xStar ≤ f (x (n + 1)) - f xStar) :
    2 * h *
        ((∑ n ∈ Finset.range N, (1 - alpha * h) ^ (N - 1 - n)) *
          (f (x N) - f xStar)) ≤
      2 * h *
        (∑ n ∈ Finset.range N,
          (1 - alpha * h) ^ (N - 1 - n) *
            (f (x (n + 1)) - f xStar)) := by
  let gap : ℕ -> ℝ := fun n => f (x n) - f xStar
  simpa [gap] using
    weightedFinalGap_le_weightedGapSum
      (A := 1 - alpha * h) (h := h) (finalGap := f (x N) - f xStar)
      hfactor hh gap N hmono

/--
Chewi Theorem 3.4 finite-denominator function-value bound, assembled from the
one-step recurrence (3.1), the weighted finite-sum bound, and the monotone-gap
lower bound.

This is the last inequality before rewriting the geometric denominator into
the closed form displayed in (3.2).
-/
theorem chewi34_final_gap_le_weighted_denominator_of_one_step
    {E : Type*} [NormedAddCommGroup E]
    {f : E -> ℝ} {x : ℕ -> E} {xStar : E} {alpha h : ℝ}
    (hfactor : 0 ≤ 1 - alpha * h)
    (hh : 0 < h)
    {N : ℕ} (hN : N ≠ 0)
    (hone_step : ∀ n,
      ‖x (n + 1) - xStar‖ ^ (2 : ℕ) ≤
        (1 - alpha * h) * ‖x n - xStar‖ ^ (2 : ℕ) -
          2 * h * (f (x (n + 1)) - f xStar))
    (hmono : ∀ n, n < N -> f (x N) - f xStar ≤
      f (x (n + 1)) - f xStar) :
    f (x N) - f xStar ≤
      ((1 - alpha * h) ^ N * ‖x 0 - xStar‖ ^ (2 : ℕ)) /
        (2 * h *
          ∑ n ∈ Finset.range N, (1 - alpha * h) ^ (N - 1 - n)) := by
  let weights : ℝ :=
    ∑ n ∈ Finset.range N, (1 - alpha * h) ^ (N - 1 - n)
  have hweights_pos : 0 < weights := by
    simpa [weights] using
      geometricWeights_sum_pos (A := 1 - alpha * h) hfactor hN
  have hden_pos : 0 < 2 * h * weights :=
    mul_pos (mul_pos two_pos hh) hweights_pos
  have hupper :=
    chewi34_weighted_sum_bound_of_one_step hfactor hone_step N
  have hlower :=
    chewi34_weighted_final_gap_le_weighted_gap_sum
      hfactor hh.le N hmono
  have hmain :
      2 * h * (weights * (f (x N) - f xStar)) ≤
        (1 - alpha * h) ^ N * ‖x 0 - xStar‖ ^ (2 : ℕ) := by
    exact hlower.trans (by simpa [weights] using hupper)
  have hmul :
      (f (x N) - f xStar) * (2 * h * weights) ≤
        (1 - alpha * h) ^ N * ‖x 0 - xStar‖ ^ (2 : ℕ) := by
    calc
      (f (x N) - f xStar) * (2 * h * weights)
          = 2 * h * (weights * (f (x N) - f xStar)) := by ring
      _ ≤ (1 - alpha * h) ^ N * ‖x 0 - xStar‖ ^ (2 : ℕ) := hmain
  exact (le_div_iff₀ hden_pos).2 hmul

/--
Chewi Theorem 3.4 closed-form geometric denominator bound, in the
`alpha > 0` case of the displayed formula (3.2).
-/
theorem chewi34_final_gap_le_geometric_denominator_of_one_step
    {E : Type*} [NormedAddCommGroup E]
    {f : E -> ℝ} {x : ℕ -> E} {xStar : E} {alpha h : ℝ}
    (halpha : 0 < alpha)
    (hh : 0 < h)
    (hfactor_pos : 0 < 1 - alpha * h)
    {N : ℕ} (hN : N ≠ 0)
    (hone_step : ∀ n,
      ‖x (n + 1) - xStar‖ ^ (2 : ℕ) ≤
        (1 - alpha * h) * ‖x n - xStar‖ ^ (2 : ℕ) -
          2 * h * (f (x (n + 1)) - f xStar))
    (hmono : ∀ n, n < N -> f (x N) - f xStar ≤
      f (x (n + 1)) - f xStar) :
    f (x N) - f xStar ≤
      alpha * ‖x 0 - xStar‖ ^ (2 : ℕ) /
        (2 * (((1 - alpha * h) ^ N)⁻¹ - 1)) := by
  let A : ℝ := 1 - alpha * h
  let R : ℝ := ‖x 0 - xStar‖ ^ (2 : ℕ)
  have hA_pos : 0 < A := by simpa [A] using hfactor_pos
  have hA_nonneg : 0 ≤ A := hA_pos.le
  have hA_lt_one : A < 1 := by
    have hmul_pos : 0 < alpha * h := mul_pos halpha hh
    dsimp [A]
    nlinarith
  have hA_ne_one : A ≠ 1 := ne_of_lt hA_lt_one
  have hA_pow_pos : 0 < A ^ N := pow_pos hA_pos N
  have hA_pow_ne : A ^ N ≠ 0 := hA_pow_pos.ne'
  have hA_pow_lt_one : A ^ N < 1 :=
    pow_lt_one₀ hA_nonneg hA_lt_one hN
  have hone_sub_pow_ne : 1 - A ^ N ≠ 0 := by
    nlinarith
  have hfinite :
      f (x N) - f xStar ≤
        (A ^ N * R) /
          (2 * h *
            ∑ n ∈ Finset.range N, A ^ (N - 1 - n)) := by
    simpa [A, R] using
      chewi34_final_gap_le_weighted_denominator_of_one_step
        (alpha := alpha) (h := h) hA_nonneg hh hN hone_step hmono
  have hsum :
      (∑ n ∈ Finset.range N, A ^ (N - 1 - n)) =
        (1 - A ^ N) / (1 - A) :=
    geometricWeights_sum_eq_div hA_ne_one N
  have hrhs :
      (A ^ N * R) /
          (2 * h *
            ∑ n ∈ Finset.range N, A ^ (N - 1 - n)) =
        alpha * R / (2 * ((A ^ N)⁻¹ - 1)) := by
    rw [hsum]
    have hsub : 1 - A = alpha * h := by
      dsimp [A]
      ring
    rw [hsub]
    field_simp [halpha.ne', hh.ne', hA_pow_ne, hone_sub_pow_ne]
  exact hfinite.trans_eq (by simpa [A, R] using hrhs)

/--
Chewi Theorem 3.4 limiting `alpha = 0` function-value bound, assuming the
one-step recurrence with factor `1`.
-/
theorem chewi34_final_gap_le_alpha_zero_denominator_of_one_step
    {E : Type*} [NormedAddCommGroup E]
    {f : E -> ℝ} {x : ℕ -> E} {xStar : E} {h : ℝ}
    (hh : 0 < h)
    {N : ℕ} (hN : N ≠ 0)
    (hone_step : ∀ n,
      ‖x (n + 1) - xStar‖ ^ (2 : ℕ) ≤
        ‖x n - xStar‖ ^ (2 : ℕ) -
          2 * h * (f (x (n + 1)) - f xStar))
    (hmono : ∀ n, n < N -> f (x N) - f xStar ≤
      f (x (n + 1)) - f xStar) :
    f (x N) - f xStar ≤
      ‖x 0 - xStar‖ ^ (2 : ℕ) / (2 * h * (N : ℝ)) := by
  have hone_step' : ∀ n,
      ‖x (n + 1) - xStar‖ ^ (2 : ℕ) ≤
        (1 - (0 : ℝ) * h) * ‖x n - xStar‖ ^ (2 : ℕ) -
          2 * h * (f (x (n + 1)) - f xStar) := by
    intro n
    simpa using hone_step n
  have hfinite :=
    chewi34_final_gap_le_weighted_denominator_of_one_step
      (alpha := (0 : ℝ)) (h := h) (x := x) (xStar := xStar)
      (f := f) (by norm_num) hh hN hone_step' hmono
  have hsum :
      (∑ n ∈ Finset.range N, (1 - (0 : ℝ) * h) ^ (N - 1 - n)) =
        (N : ℝ) := by
    simp
  have hrhs :
      ((1 - (0 : ℝ) * h) ^ N * ‖x 0 - xStar‖ ^ (2 : ℕ)) /
          (2 * h *
            ∑ n ∈ Finset.range N,
              (1 - (0 : ℝ) * h) ^ (N - 1 - n)) =
        ‖x 0 - xStar‖ ^ (2 : ℕ) / (2 * h * (N : ℝ)) := by
    rw [hsum]
    ring
  exact hfinite.trans_eq hrhs

/--
Chewi Theorem 3.4 one-step recurrence (3.3), supplied with the first-order
strong-convexity lower model from Proposition 1.6 and the descent lemma.
-/
theorem oneStepRecurrence_of_firstOrderStrongConvexOn
    {E : Type*} [NormedAddCommGroup E] [InnerProductSpace ℝ E]
    {C : Set E} {f : E -> ℝ} {grad : E -> E}
    {alpha beta h : ℝ} {x z : E}
    (hfirst : FirstOrderStrongConvexOn C f grad alpha)
    (hsmooth : SmoothWithGradientOn C f grad beta)
    (hx : x ∈ C)
    (hz : z ∈ C)
    (hstep_mem : gradientDescentStep grad h x ∈ C)
    (hh_nonneg : 0 ≤ h)
    (hbeta_step : beta * h ≤ 1) :
    ‖gradientDescentStep grad h x - z‖ ^ (2 : ℕ) ≤
      (1 - alpha * h) * ‖x - z‖ ^ (2 : ℕ) -
        2 * h * (f (gradientDescentStep grad h x) - f z) := by
  let g := grad x
  let xplus := gradientDescentStep grad h x
  have hxplus_def : xplus = x - h • g := rfl
  have hdescent :
      f xplus - f x ≤ -(h / 2) * ‖g‖ ^ (2 : ℕ) := by
    simpa [xplus, g] using
      descentLemma_of_smoothWithGradientOn hsmooth hx hstep_mem
        hh_nonneg hbeta_step
  have hfirst_model :
      f x + inner ℝ g (z - x) +
        (alpha / 2) * ‖z - x‖ ^ (2 : ℕ) ≤ f z := by
    simpa [g] using hfirst.lower_model hx hz
  have hinner_lower :
      f x - f z + (alpha / 2) * ‖x - z‖ ^ (2 : ℕ) ≤
        inner ℝ (x - z) g := by
    have hmodel' :
        f x + inner ℝ g (z - x) +
            (alpha / 2) * ‖z - x‖ ^ (2 : ℕ) ≤ f z := by
      linarith
    have hflip : inner ℝ (x - z) g = -inner ℝ g (z - x) := by
      calc
        inner ℝ (x - z) g = inner ℝ g (x - z) := by
          rw [real_inner_comm]
        _ = inner ℝ g (-(z - x)) := by
          congr
          abel
        _ = -inner ℝ g (z - x) := by
          rw [inner_neg_right]
    have hnorm_eq : ‖z - x‖ ^ (2 : ℕ) = ‖x - z‖ ^ (2 : ℕ) := by
      rw [← norm_neg (x - z)]
      have hneg : -(x - z) = z - x := by
        abel
      rw [hneg]
    rw [hflip]
    rw [← hnorm_eq]
    nlinarith
  have hinner_bound :
      -2 * h * inner ℝ (x - z) g ≤
        -2 * h * (f x - f z) -
          alpha * h * ‖x - z‖ ^ (2 : ℕ) := by
    have hmul :=
      mul_le_mul_of_nonpos_left hinner_lower (by nlinarith : -2 * h ≤ 0)
    nlinarith
  have hquad_bound :
      h ^ (2 : ℕ) * ‖g‖ ^ (2 : ℕ) ≤ -2 * h * (f xplus - f x) := by
    have hmul :=
      mul_le_mul_of_nonpos_left hdescent (by nlinarith : -2 * h ≤ 0)
    nlinarith
  have hnorm_expand :
      ‖xplus - z‖ ^ (2 : ℕ) =
        ‖x - z‖ ^ (2 : ℕ) -
          2 * h * inner ℝ (x - z) g +
          h ^ (2 : ℕ) * ‖g‖ ^ (2 : ℕ) := by
    have hsub : xplus - z = (x - z) - h • g := by
      simp [xplus, g, gradientDescentStep]
      abel
    rw [hsub, norm_sub_sq_real, real_inner_smul_right, norm_smul,
      Real.norm_eq_abs, abs_of_nonneg hh_nonneg]
    ring
  rw [hnorm_expand]
  nlinarith

/--
Chewi Theorem 3.4 weighted finite-sum bound from the first-order
strong-convexity supplied interface and a gradient-descent trajectory.
-/
theorem chewi34_weighted_sum_bound_of_firstOrderStrongConvexOn
    {E : Type*} [NormedAddCommGroup E] [InnerProductSpace ℝ E]
    {C : Set E} {f : E -> ℝ} {grad : E -> E}
    {alpha beta h : ℝ} {x : ℕ -> E} {xStar : E}
    (hfirst : FirstOrderStrongConvexOn C f grad alpha)
    (hsmooth : SmoothWithGradientOn C f grad beta)
    (htraj : IsGradientDescentTrajectory grad h x)
    (hmem : ∀ n, x n ∈ C)
    (hxStar : xStar ∈ C)
    (hh_nonneg : 0 ≤ h)
    (hbeta_step : beta * h ≤ 1)
    (hfactor : 0 ≤ 1 - alpha * h)
    (N : ℕ) :
    2 * h *
        (∑ n ∈ Finset.range N,
          (1 - alpha * h) ^ (N - 1 - n) *
            (f (x (n + 1)) - f xStar)) ≤
      (1 - alpha * h) ^ N * ‖x 0 - xStar‖ ^ (2 : ℕ) := by
  have hone_step : ∀ n,
      ‖x (n + 1) - xStar‖ ^ (2 : ℕ) ≤
        (1 - alpha * h) * ‖x n - xStar‖ ^ (2 : ℕ) -
          2 * h * (f (x (n + 1)) - f xStar) := by
    intro n
    have hstep_eq : x (n + 1) = gradientDescentStep grad h (x n) :=
      htraj.succ n
    have hstep_mem : gradientDescentStep grad h (x n) ∈ C := by
      rw [← hstep_eq]
      exact hmem (n + 1)
    have hrec :=
      oneStepRecurrence_of_firstOrderStrongConvexOn
        (C := C) (f := f) (grad := grad) (alpha := alpha)
        (beta := beta) (h := h) (x := x n) (z := xStar)
        hfirst hsmooth (hmem n) hxStar hstep_mem hh_nonneg hbeta_step
    simpa [hstep_eq] using hrec
  exact chewi34_weighted_sum_bound_of_one_step hfactor hone_step N

/--
Source-indexed version of
`chewi34_weighted_sum_bound_of_firstOrderStrongConvexOn`.
-/
theorem chewi34_weighted_sum_bound_one_based_of_firstOrderStrongConvexOn
    {E : Type*} [NormedAddCommGroup E] [InnerProductSpace ℝ E]
    {C : Set E} {f : E -> ℝ} {grad : E -> E}
    {alpha beta h : ℝ} {x : ℕ -> E} {xStar : E}
    (hfirst : FirstOrderStrongConvexOn C f grad alpha)
    (hsmooth : SmoothWithGradientOn C f grad beta)
    (htraj : IsGradientDescentTrajectory grad h x)
    (hmem : ∀ n, x n ∈ C)
    (hxStar : xStar ∈ C)
    (hh_nonneg : 0 ≤ h)
    (hbeta_step : beta * h ≤ 1)
    (hfactor : 0 ≤ 1 - alpha * h)
    (N : ℕ) :
    2 * h *
        (∑ n ∈ Finset.Ico 1 (N + 1),
          (1 - alpha * h) ^ (N - n) * (f (x n) - f xStar)) ≤
      (1 - alpha * h) ^ N * ‖x 0 - xStar‖ ^ (2 : ℕ) := by
  have hone_step : ∀ n,
      ‖x (n + 1) - xStar‖ ^ (2 : ℕ) ≤
        (1 - alpha * h) * ‖x n - xStar‖ ^ (2 : ℕ) -
          2 * h * (f (x (n + 1)) - f xStar) := by
    intro n
    have hstep_eq : x (n + 1) = gradientDescentStep grad h (x n) :=
      htraj.succ n
    have hstep_mem : gradientDescentStep grad h (x n) ∈ C := by
      rw [← hstep_eq]
      exact hmem (n + 1)
    have hrec :=
      oneStepRecurrence_of_firstOrderStrongConvexOn
        (C := C) (f := f) (grad := grad) (alpha := alpha)
        (beta := beta) (h := h) (x := x n) (z := xStar)
        hfirst hsmooth (hmem n) hxStar hstep_mem hh_nonneg hbeta_step
    simpa [hstep_eq] using hrec
  exact chewi34_weighted_sum_bound_one_based_of_one_step hfactor hone_step N

/--
Chewi Theorem 3.4 finite-denominator function-value bound from the
first-order strong-convexity supplied interface and a gradient-descent
trajectory.
-/
theorem chewi34_final_gap_le_weighted_denominator_of_firstOrderStrongConvexOn
    {E : Type*} [NormedAddCommGroup E] [InnerProductSpace ℝ E]
    {C : Set E} {f : E -> ℝ} {grad : E -> E}
    {alpha beta h : ℝ} {x : ℕ -> E} {xStar : E}
    (hfirst : FirstOrderStrongConvexOn C f grad alpha)
    (hsmooth : SmoothWithGradientOn C f grad beta)
    (htraj : IsGradientDescentTrajectory grad h x)
    (hmem : ∀ n, x n ∈ C)
    (hxStar : xStar ∈ C)
    (hh : 0 < h)
    (hbeta_step : beta * h ≤ 1)
    (hfactor : 0 ≤ 1 - alpha * h)
    {N : ℕ} (hN : N ≠ 0)
    (hmono : ∀ n, n < N -> f (x N) - f xStar ≤
      f (x (n + 1)) - f xStar) :
    f (x N) - f xStar ≤
      ((1 - alpha * h) ^ N * ‖x 0 - xStar‖ ^ (2 : ℕ)) /
        (2 * h *
          ∑ n ∈ Finset.range N, (1 - alpha * h) ^ (N - 1 - n)) := by
  have hone_step : ∀ n,
      ‖x (n + 1) - xStar‖ ^ (2 : ℕ) ≤
        (1 - alpha * h) * ‖x n - xStar‖ ^ (2 : ℕ) -
          2 * h * (f (x (n + 1)) - f xStar) := by
    intro n
    have hstep_eq : x (n + 1) = gradientDescentStep grad h (x n) :=
      htraj.succ n
    have hstep_mem : gradientDescentStep grad h (x n) ∈ C := by
      rw [← hstep_eq]
      exact hmem (n + 1)
    have hrec :=
      oneStepRecurrence_of_firstOrderStrongConvexOn
        (C := C) (f := f) (grad := grad) (alpha := alpha)
        (beta := beta) (h := h) (x := x n) (z := xStar)
        hfirst hsmooth (hmem n) hxStar hstep_mem hh.le hbeta_step
    simpa [hstep_eq] using hrec
  exact
    chewi34_final_gap_le_weighted_denominator_of_one_step
      hfactor hh hN hone_step hmono

/--
Chewi Theorem 3.4 closed-form function-value bound from the first-order
strong-convexity supplied interface and a gradient-descent trajectory, in the
`alpha > 0` case of the displayed formula (3.2).
-/
theorem chewi34_final_gap_le_geometric_denominator_of_firstOrderStrongConvexOn
    {E : Type*} [NormedAddCommGroup E] [InnerProductSpace ℝ E]
    {C : Set E} {f : E -> ℝ} {grad : E -> E}
    {alpha beta h : ℝ} {x : ℕ -> E} {xStar : E}
    (hfirst : FirstOrderStrongConvexOn C f grad alpha)
    (hsmooth : SmoothWithGradientOn C f grad beta)
    (htraj : IsGradientDescentTrajectory grad h x)
    (hmem : ∀ n, x n ∈ C)
    (hxStar : xStar ∈ C)
    (halpha : 0 < alpha)
    (hh : 0 < h)
    (hbeta_step : beta * h ≤ 1)
    (hfactor_pos : 0 < 1 - alpha * h)
    {N : ℕ} (hN : N ≠ 0)
    (hmono : ∀ n, n < N -> f (x N) - f xStar ≤
      f (x (n + 1)) - f xStar) :
    f (x N) - f xStar ≤
      alpha * ‖x 0 - xStar‖ ^ (2 : ℕ) /
        (2 * (((1 - alpha * h) ^ N)⁻¹ - 1)) := by
  have hone_step : ∀ n,
      ‖x (n + 1) - xStar‖ ^ (2 : ℕ) ≤
        (1 - alpha * h) * ‖x n - xStar‖ ^ (2 : ℕ) -
          2 * h * (f (x (n + 1)) - f xStar) := by
    intro n
    have hstep_eq : x (n + 1) = gradientDescentStep grad h (x n) :=
      htraj.succ n
    have hstep_mem : gradientDescentStep grad h (x n) ∈ C := by
      rw [← hstep_eq]
      exact hmem (n + 1)
    have hrec :=
      oneStepRecurrence_of_firstOrderStrongConvexOn
        (C := C) (f := f) (grad := grad) (alpha := alpha)
        (beta := beta) (h := h) (x := x n) (z := xStar)
        hfirst hsmooth (hmem n) hxStar hstep_mem hh.le hbeta_step
    simpa [hstep_eq] using hrec
  exact
    chewi34_final_gap_le_geometric_denominator_of_one_step
      halpha hh hfactor_pos hN hone_step hmono

/--
Chewi Theorem 3.4 limiting `alpha = 0` bound from the first-order
strong-convexity supplied interface and a gradient-descent trajectory.
-/
theorem chewi34_final_gap_le_alpha_zero_denominator_of_firstOrderStrongConvexOn
    {E : Type*} [NormedAddCommGroup E] [InnerProductSpace ℝ E]
    {C : Set E} {f : E -> ℝ} {grad : E -> E}
    {beta h : ℝ} {x : ℕ -> E} {xStar : E}
    (hfirst : FirstOrderStrongConvexOn C f grad 0)
    (hsmooth : SmoothWithGradientOn C f grad beta)
    (htraj : IsGradientDescentTrajectory grad h x)
    (hmem : ∀ n, x n ∈ C)
    (hxStar : xStar ∈ C)
    (hh : 0 < h)
    (hbeta_step : beta * h ≤ 1)
    {N : ℕ} (hN : N ≠ 0)
    (hmono : ∀ n, n < N -> f (x N) - f xStar ≤
      f (x (n + 1)) - f xStar) :
    f (x N) - f xStar ≤
      ‖x 0 - xStar‖ ^ (2 : ℕ) / (2 * h * (N : ℝ)) := by
  have hone_step : ∀ n,
      ‖x (n + 1) - xStar‖ ^ (2 : ℕ) ≤
        ‖x n - xStar‖ ^ (2 : ℕ) -
          2 * h * (f (x (n + 1)) - f xStar) := by
    intro n
    have hstep_eq : x (n + 1) = gradientDescentStep grad h (x n) :=
      htraj.succ n
    have hstep_mem : gradientDescentStep grad h (x n) ∈ C := by
      rw [← hstep_eq]
      exact hmem (n + 1)
    have hrec :=
      oneStepRecurrence_of_firstOrderStrongConvexOn
        (C := C) (f := f) (grad := grad) (alpha := (0 : ℝ))
        (beta := beta) (h := h) (x := x n) (z := xStar)
        hfirst hsmooth (hmem n) hxStar hstep_mem hh.le hbeta_step
    simpa [hstep_eq] using hrec
  exact
    chewi34_final_gap_le_alpha_zero_denominator_of_one_step
      hh hN hone_step hmono

/--
Chewi Theorem 3.4 closed-form function-value bound from the first-order
strong-convexity supplied interface and gradient descent, deriving the
monotone-gap estimate from the descent lemma.
-/
theorem chewi34_final_gap_le_geometric_denominator_of_firstOrderStrongConvexOn_of_descent
    {E : Type*} [NormedAddCommGroup E] [InnerProductSpace ℝ E]
    {C : Set E} {f : E -> ℝ} {grad : E -> E}
    {alpha beta h : ℝ} {x : ℕ -> E} {xStar : E}
    (hfirst : FirstOrderStrongConvexOn C f grad alpha)
    (hsmooth : SmoothWithGradientOn C f grad beta)
    (htraj : IsGradientDescentTrajectory grad h x)
    (hmem : ∀ n, x n ∈ C)
    (hxStar : xStar ∈ C)
    (halpha : 0 < alpha)
    (hh : 0 < h)
    (hbeta_step : beta * h ≤ 1)
    (hfactor_pos : 0 < 1 - alpha * h)
    {N : ℕ} (hN : N ≠ 0) :
    f (x N) - f xStar ≤
      alpha * ‖x 0 - xStar‖ ^ (2 : ℕ) /
        (2 * (((1 - alpha * h) ^ N)⁻¹ - 1)) := by
  have hanti :
      Antitone fun n => f (x n) :=
    functionValue_antitone_of_smoothWithGradientOn
      hsmooth htraj hmem hh.le hbeta_step
  have hmono : ∀ n, n < N -> f (x N) - f xStar ≤
      f (x (n + 1)) - f xStar := by
    intro n hn
    have hle : n + 1 ≤ N := Nat.succ_le_of_lt hn
    have hvalue : f (x N) ≤ f (x (n + 1)) := hanti hle
    nlinarith
  exact
    chewi34_final_gap_le_geometric_denominator_of_firstOrderStrongConvexOn
      hfirst hsmooth htraj hmem hxStar halpha hh hbeta_step hfactor_pos hN
      hmono

/--
Chewi Theorem 3.4 limiting `alpha = 0` function-value bound from the
first-order strong-convexity supplied interface and gradient descent, deriving
the monotone-gap estimate from the descent lemma.
-/
theorem chewi34_final_gap_le_alpha_zero_denominator_of_firstOrderStrongConvexOn_of_descent
    {E : Type*} [NormedAddCommGroup E] [InnerProductSpace ℝ E]
    {C : Set E} {f : E -> ℝ} {grad : E -> E}
    {beta h : ℝ} {x : ℕ -> E} {xStar : E}
    (hfirst : FirstOrderStrongConvexOn C f grad 0)
    (hsmooth : SmoothWithGradientOn C f grad beta)
    (htraj : IsGradientDescentTrajectory grad h x)
    (hmem : ∀ n, x n ∈ C)
    (hxStar : xStar ∈ C)
    (hh : 0 < h)
    (hbeta_step : beta * h ≤ 1)
    {N : ℕ} (hN : N ≠ 0) :
    f (x N) - f xStar ≤
      ‖x 0 - xStar‖ ^ (2 : ℕ) / (2 * h * (N : ℝ)) := by
  have hanti :
      Antitone fun n => f (x n) :=
    functionValue_antitone_of_smoothWithGradientOn
      hsmooth htraj hmem hh.le hbeta_step
  have hmono : ∀ n, n < N -> f (x N) - f xStar ≤
      f (x (n + 1)) - f xStar := by
    intro n hn
    have hle : n + 1 ≤ N := Nat.succ_le_of_lt hn
    have hvalue : f (x N) ≤ f (x (n + 1)) := hanti hle
    nlinarith
  exact
    chewi34_final_gap_le_alpha_zero_denominator_of_firstOrderStrongConvexOn
      hfirst hsmooth htraj hmem hxStar hh hbeta_step hN hmono

/--
Chewi Theorem 3.4 closed-form `alpha > 0` function-value bound with
Proposition 1.6 `(1.3) => (1.4)` discharged from the actual segment
strong-convexity definition on the whole space.
-/
theorem chewi34_final_gap_le_geometric_denominator_of_strongConvexOn_univ_hasGradientAt_of_descent
    {E : Type*} [NormedAddCommGroup E] [InnerProductSpace ℝ E]
    [CompleteSpace E]
    {f : E -> ℝ} {grad : E -> E}
    {alpha beta h : ℝ} {x : ℕ -> E} {xStar : E}
    (hstrong : StrongConvexOn Set.univ f alpha)
    (hgrad : ∀ z, HasGradientAt f (grad z) z)
    (hsmooth : SmoothWithGradientOn Set.univ f grad beta)
    (htraj : IsGradientDescentTrajectory grad h x)
    (halpha : 0 < alpha)
    (hh : 0 < h)
    (hbeta_step : beta * h ≤ 1)
    (hfactor_pos : 0 < 1 - alpha * h)
    {N : ℕ} (hN : N ≠ 0) :
    f (x N) - f xStar ≤
      alpha * ‖x 0 - xStar‖ ^ (2 : ℕ) /
        (2 * (((1 - alpha * h) ^ N)⁻¹ - 1)) :=
  chewi34_final_gap_le_geometric_denominator_of_firstOrderStrongConvexOn_of_descent
    (FirstOrderStrongConvexOn.of_strongConvexOn_univ_hasGradientAt
      hstrong hgrad)
    hsmooth htraj (by intro n; simp) (by simp) halpha hh hbeta_step
    hfactor_pos hN

/--
Chewi Theorem 3.4 limiting `alpha = 0` function-value bound with Proposition
1.6 `(1.3) => (1.4)` discharged from the actual segment convexity definition
on the whole space.
-/
theorem chewi34_final_gap_le_alpha_zero_denominator_of_strongConvexOn_univ_hasGradientAt_of_descent
    {E : Type*} [NormedAddCommGroup E] [InnerProductSpace ℝ E]
    [CompleteSpace E]
    {f : E -> ℝ} {grad : E -> E}
    {beta h : ℝ} {x : ℕ -> E} {xStar : E}
    (hstrong : StrongConvexOn Set.univ f 0)
    (hgrad : ∀ z, HasGradientAt f (grad z) z)
    (hsmooth : SmoothWithGradientOn Set.univ f grad beta)
    (htraj : IsGradientDescentTrajectory grad h x)
    (hh : 0 < h)
    (hbeta_step : beta * h ≤ 1)
    {N : ℕ} (hN : N ≠ 0) :
    f (x N) - f xStar ≤
      ‖x 0 - xStar‖ ^ (2 : ℕ) / (2 * h * (N : ℝ)) :=
  chewi34_final_gap_le_alpha_zero_denominator_of_firstOrderStrongConvexOn_of_descent
    (FirstOrderStrongConvexOn.of_strongConvexOn_univ_hasGradientAt
      hstrong hgrad)
    hsmooth htraj (by intro n; simp) (by simp) hh hbeta_step hN

end Optimization
end StatInference
