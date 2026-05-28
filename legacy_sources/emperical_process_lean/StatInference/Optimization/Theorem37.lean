import StatInference.Optimization.GradientDescent

/-!
# Chewi Theorem 3.7 gradient-norm convergence layer

This module proves the main-text stationary-point guarantee for smooth
gradient descent from the compiled descent lemma.  It provides both the
proof-carrying existence form over `n < N` and the finite-minimum display used
in the source.
-/

namespace StatInference
namespace Optimization

open Finset
open scoped InnerProductSpace

variable {E : Type*} [NormedAddCommGroup E] [InnerProductSpace ℝ E]

/-- Telescoping form used in Chewi Theorem 3.7. -/
theorem sum_range_sub_succ (a : ℕ -> ℝ) (N : ℕ) :
    (∑ n ∈ Finset.range N, (a n - a (n + 1))) = a 0 - a N := by
  calc
    (∑ n ∈ Finset.range N, (a n - a (n + 1)))
        =
          ∑ n ∈ Finset.range N, (-a (n + 1) - -a n) := by
          refine Finset.sum_congr rfl ?_
          intro n _hn
          ring
    _ = -a N - -a 0 := Finset.sum_range_sub (fun n => -a n) N
    _ = a 0 - a N := by ring

/--
One-step lower bound on the function-value decrease obtained from Chewi
Lemma 3.1.
-/
theorem gradient_sq_step_le_drop_of_smoothWithGradientOn
    {C : Set E} {f : E -> ℝ} {grad : E -> E} {beta h : ℝ} {x : E}
    (hsmooth : SmoothWithGradientOn C f grad beta)
    (hx : x ∈ C)
    (hstep_mem : gradientDescentStep grad h x ∈ C)
    (hh_nonneg : 0 ≤ h)
    (hbeta_step : beta * h ≤ 1) :
    (h / 2) * ‖grad x‖ ^ (2 : ℕ) ≤
      f x - f (gradientDescentStep grad h x) := by
  have hdescent :
      f (gradientDescentStep grad h x) - f x ≤
        -(h / 2) * ‖grad x‖ ^ (2 : ℕ) :=
    descentLemma_of_smoothWithGradientOn hsmooth hx hstep_mem
      hh_nonneg hbeta_step
  nlinarith

/--
The one-step squared-gradient decrease bound along a gradient-descent
trajectory.
-/
theorem gradient_sq_step_le_drop_of_trajectory
    {C : Set E} {f : E -> ℝ} {grad : E -> E}
    {beta h : ℝ} {x : ℕ -> E}
    (hsmooth : SmoothWithGradientOn C f grad beta)
    (htraj : IsGradientDescentTrajectory grad h x)
    (hmem : ∀ n, x n ∈ C)
    (hh_nonneg : 0 ≤ h)
    (hbeta_step : beta * h ≤ 1) :
    ∀ n, (h / 2) * ‖grad (x n)‖ ^ (2 : ℕ) ≤
      f (x n) - f (x (n + 1)) := by
  intro n
  have hstep_eq : x (n + 1) = gradientDescentStep grad h (x n) :=
    htraj.succ n
  have hstep_mem : gradientDescentStep grad h (x n) ∈ C := by
    rw [← hstep_eq]
    exact hmem (n + 1)
  simpa [hstep_eq] using
    gradient_sq_step_le_drop_of_smoothWithGradientOn
      hsmooth (hmem n) hstep_mem hh_nonneg hbeta_step

/--
Chewi Theorem 3.7 telescoped squared-gradient sum bound.
-/
theorem chewi37_gradient_sq_sum_bound
    {C : Set E} {f : E -> ℝ} {grad : E -> E}
    {beta h fstar : ℝ} {x : ℕ -> E}
    (hsmooth : SmoothWithGradientOn C f grad beta)
    (htraj : IsGradientDescentTrajectory grad h x)
    (hmem : ∀ n, x n ∈ C)
    (hstar_lower : ∀ n, fstar ≤ f (x n))
    (hh_nonneg : 0 ≤ h)
    (hbeta_step : beta * h ≤ 1)
    (N : ℕ) :
    (h / 2) *
        (∑ n ∈ Finset.range N, ‖grad (x n)‖ ^ (2 : ℕ)) ≤
      f (x 0) - fstar := by
  have hstep :=
    gradient_sq_step_le_drop_of_trajectory
      hsmooth htraj hmem hh_nonneg hbeta_step
  have hsum :
      (∑ n ∈ Finset.range N,
          (h / 2) * ‖grad (x n)‖ ^ (2 : ℕ)) ≤
        ∑ n ∈ Finset.range N, (f (x n) - f (x (n + 1))) := by
    exact Finset.sum_le_sum fun n _hn => hstep n
  have hleft :
      (h / 2) *
          (∑ n ∈ Finset.range N, ‖grad (x n)‖ ^ (2 : ℕ)) ≤
        ∑ n ∈ Finset.range N, (f (x n) - f (x (n + 1))) := by
    simpa [Finset.mul_sum] using hsum
  have htelescope :
      (∑ n ∈ Finset.range N, (f (x n) - f (x (n + 1)))) =
        f (x 0) - f (x N) := by
    simpa using sum_range_sub_succ (fun n => f (x n)) N
  calc
    (h / 2) *
        (∑ n ∈ Finset.range N, ‖grad (x n)‖ ^ (2 : ℕ))
        ≤ ∑ n ∈ Finset.range N, (f (x n) - f (x (n + 1))) := hleft
    _ = f (x 0) - f (x N) := htelescope
    _ ≤ f (x 0) - fstar := by
        nlinarith [hstar_lower N]

/--
Finite average principle used to turn the Theorem 3.7 sum bound into a
single indexed iterate.
-/
theorem exists_le_average_of_sum_le {a : ℕ -> ℝ} {N : ℕ} {B : ℝ}
    (hN : N ≠ 0)
    (hsum : (∑ n ∈ Finset.range N, a n) ≤ (N : ℝ) * B) :
    ∃ n, n < N ∧ a n ≤ B := by
  have hnonempty : (Finset.range N).Nonempty :=
    Finset.nonempty_range_iff.mpr hN
  have hsum_const :
      (∑ n ∈ Finset.range N, B) = (N : ℝ) * B := by
    simp [Finset.sum_const, Finset.card_range, nsmul_eq_mul]
  have hsum' :
      (∑ n ∈ Finset.range N, a n) ≤
        ∑ n ∈ Finset.range N, (fun _ => B) n := by
    simpa [hsum_const] using hsum
  rcases Finset.exists_le_of_sum_le
      (f := a) (g := fun _ => B) hnonempty hsum'
    with ⟨n, hnmem, hnle⟩
  exact ⟨n, Finset.mem_range.mp hnmem, hnle⟩

/--
Chewi Theorem 3.7, squared existence form.
-/
theorem chewi37_exists_grad_sq_le
    {C : Set E} {f : E -> ℝ} {grad : E -> E}
    {beta h fstar : ℝ} {x : ℕ -> E} {N : ℕ}
    (hsmooth : SmoothWithGradientOn C f grad beta)
    (htraj : IsGradientDescentTrajectory grad h x)
    (hmem : ∀ n, x n ∈ C)
    (hstar_lower : ∀ n, fstar ≤ f (x n))
    (hh_pos : 0 < h)
    (hbeta_step : beta * h ≤ 1)
    (hN : N ≠ 0) :
    ∃ n, n < N ∧
      ‖grad (x n)‖ ^ (2 : ℕ) ≤
        2 * (f (x 0) - fstar) / ((N : ℝ) * h) := by
  let S : ℝ := ∑ n ∈ Finset.range N, ‖grad (x n)‖ ^ (2 : ℕ)
  let B : ℝ := 2 * (f (x 0) - fstar) / ((N : ℝ) * h)
  have hsum_bound :
      (h / 2) * S ≤ f (x 0) - fstar := by
    simpa [S] using
      chewi37_gradient_sq_sum_bound
        hsmooth htraj hmem hstar_lower hh_pos.le hbeta_step N
  have hhalf_pos : 0 < h / 2 := by nlinarith
  have hsum_bound' :
      S * (h / 2) ≤ f (x 0) - fstar := by
    simpa [mul_comm] using hsum_bound
  have hS_le_div :
      S ≤ (f (x 0) - fstar) / (h / 2) :=
    (le_div_iff₀ hhalf_pos).mpr hsum_bound'
  have hS_le :
      S ≤ 2 * (f (x 0) - fstar) / h := by
    have hrewrite :
        (f (x 0) - fstar) / (h / 2) =
          2 * (f (x 0) - fstar) / h := by
      field_simp [hh_pos.ne']
    simpa [hrewrite] using hS_le_div
  have hN_pos_nat : 0 < N := Nat.pos_of_ne_zero hN
  have hN_pos : 0 < (N : ℝ) := by
    exact_mod_cast hN_pos_nat
  have hscale :
      (N : ℝ) * B = 2 * (f (x 0) - fstar) / h := by
    dsimp [B]
    field_simp [B, hN_pos.ne', hh_pos.ne']
  have hsum_for_exists :
      (∑ n ∈ Finset.range N, ‖grad (x n)‖ ^ (2 : ℕ)) ≤
        (N : ℝ) * B := by
    simpa [S, hscale] using hS_le
  rcases exists_le_average_of_sum_le
      (a := fun n => ‖grad (x n)‖ ^ (2 : ℕ)) hN hsum_for_exists
    with ⟨n, hnlt, hnle⟩
  exact ⟨n, hnlt, by simpa [B] using hnle⟩

/--
Chewi Theorem 3.7, supplied-interface existence form: among the first `N`
gradient-descent iterates, one has gradient norm bounded by the textbook
square-root rate.
-/
theorem chewi37_exists_grad_norm_le
    {C : Set E} {f : E -> ℝ} {grad : E -> E}
    {beta h fstar : ℝ} {x : ℕ -> E} {N : ℕ}
    (hsmooth : SmoothWithGradientOn C f grad beta)
    (htraj : IsGradientDescentTrajectory grad h x)
    (hmem : ∀ n, x n ∈ C)
    (hstar_lower : ∀ n, fstar ≤ f (x n))
    (hh_pos : 0 < h)
    (hbeta_step : beta * h ≤ 1)
    (hN : N ≠ 0) :
    ∃ n, n < N ∧
      ‖grad (x n)‖ ≤
        Real.sqrt (2 * (f (x 0) - fstar) / ((N : ℝ) * h)) := by
  rcases chewi37_exists_grad_sq_le
      hsmooth htraj hmem hstar_lower hh_pos hbeta_step hN
    with ⟨n, hnlt, hnle⟩
  exact ⟨n, hnlt, Real.le_sqrt_of_sq_le hnle⟩

/--
Chewi Theorem 3.7 with the source step-size condition `h <= 1 / beta`.
-/
theorem chewi37_exists_grad_norm_le_of_le_inv
    {C : Set E} {f : E -> ℝ} {grad : E -> E}
    {beta h fstar : ℝ} {x : ℕ -> E} {N : ℕ}
    (hsmooth : SmoothWithGradientOn C f grad beta)
    (htraj : IsGradientDescentTrajectory grad h x)
    (hmem : ∀ n, x n ∈ C)
    (hstar_lower : ∀ n, fstar ≤ f (x n))
    (hbeta_pos : 0 < beta)
    (hh_pos : 0 < h)
    (hstep_size : h ≤ 1 / beta)
    (hN : N ≠ 0) :
    ∃ n, n < N ∧
      ‖grad (x n)‖ ≤
        Real.sqrt (2 * (f (x 0) - fstar) / ((N : ℝ) * h)) := by
  have hbeta_step : beta * h ≤ 1 := by
    have hmul : beta * h ≤ beta * (1 / beta) :=
      mul_le_mul_of_nonneg_left hstep_size hbeta_pos.le
    have hcancel : beta * (1 / beta) = 1 := by
      field_simp [hbeta_pos.ne']
    linarith
  exact chewi37_exists_grad_norm_le
    hsmooth htraj hmem hstar_lower hh_pos hbeta_step hN

/--
Chewi Theorem 3.7, finite-minimum display form.
-/
theorem chewi37_min_grad_norm_le
    {C : Set E} {f : E -> ℝ} {grad : E -> E}
    {beta h fstar : ℝ} {x : ℕ -> E} {N : ℕ}
    (hsmooth : SmoothWithGradientOn C f grad beta)
    (htraj : IsGradientDescentTrajectory grad h x)
    (hmem : ∀ n, x n ∈ C)
    (hstar_lower : ∀ n, fstar ≤ f (x n))
    (hh_pos : 0 < h)
    (hbeta_step : beta * h ≤ 1)
    (hN : N ≠ 0) :
    (Finset.range N).inf' (Finset.nonempty_range_iff.mpr hN)
        (fun n => ‖grad (x n)‖) ≤
      Real.sqrt (2 * (f (x 0) - fstar) / ((N : ℝ) * h)) := by
  rcases chewi37_exists_grad_norm_le
      hsmooth htraj hmem hstar_lower hh_pos hbeta_step hN
    with ⟨n, hnlt, hnle⟩
  exact (Finset.inf'_le (s := Finset.range N)
      (f := fun n => ‖grad (x n)‖) (Finset.mem_range.mpr hnlt)).trans hnle

/--
Chewi Theorem 3.7 finite-minimum display with the source step-size condition
`h <= 1 / beta`.
-/
theorem chewi37_min_grad_norm_le_of_le_inv
    {C : Set E} {f : E -> ℝ} {grad : E -> E}
    {beta h fstar : ℝ} {x : ℕ -> E} {N : ℕ}
    (hsmooth : SmoothWithGradientOn C f grad beta)
    (htraj : IsGradientDescentTrajectory grad h x)
    (hmem : ∀ n, x n ∈ C)
    (hstar_lower : ∀ n, fstar ≤ f (x n))
    (hbeta_pos : 0 < beta)
    (hh_pos : 0 < h)
    (hstep_size : h ≤ 1 / beta)
    (hN : N ≠ 0) :
    (Finset.range N).inf' (Finset.nonempty_range_iff.mpr hN)
        (fun n => ‖grad (x n)‖) ≤
      Real.sqrt (2 * (f (x 0) - fstar) / ((N : ℝ) * h)) := by
  have hbeta_step : beta * h ≤ 1 := by
    have hmul : beta * h ≤ beta * (1 / beta) :=
      mul_le_mul_of_nonneg_left hstep_size hbeta_pos.le
    have hcancel : beta * (1 / beta) = 1 := by
      field_simp [hbeta_pos.ne']
    linarith
  exact chewi37_min_grad_norm_le
    hsmooth htraj hmem hstar_lower hh_pos hbeta_step hN

end Optimization
end StatInference
