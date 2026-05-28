import StatInference.Optimization.GradientDescent

/-!
# Chewi Theorem 3.6 PL convergence layer

This module proves the main-text gradient-descent convergence theorem under a
Polyak-Lojasiewicz inequality from the compiled descent lemma.
-/

namespace StatInference
namespace Optimization

open Set
open scoped InnerProductSpace

variable {E : Type*} [NormedAddCommGroup E] [InnerProductSpace ℝ E]

/--
Chewi Theorem 3.6 one-step gap recurrence from Lemma 3.1 and the PL
inequality.
-/
theorem oneStepGap_le_of_polyakLojasiewiczOn
    {C : Set E} {f : E -> ℝ} {grad : E -> E}
    {alpha beta h fstar : ℝ} {x : E}
    (hsmooth : SmoothWithGradientOn C f grad beta)
    (hpl : PolyakLojasiewiczOn C f grad alpha fstar)
    (hx : x ∈ C)
    (hstep_mem : gradientDescentStep grad h x ∈ C)
    (hh_nonneg : 0 ≤ h)
    (hbeta_step : beta * h ≤ 1) :
    f (gradientDescentStep grad h x) - fstar ≤
      (1 - alpha * h) * (f x - fstar) := by
  have hdescent :
      f (gradientDescentStep grad h x) - f x ≤
        -(h / 2) * ‖grad x‖ ^ (2 : ℕ) :=
    descentLemma_of_smoothWithGradientOn hsmooth hx hstep_mem
      hh_nonneg hbeta_step
  have hplx :
      2 * alpha * (f x - fstar) ≤ ‖grad x‖ ^ (2 : ℕ) :=
    hpl.gradient_sq_lower hx
  have hscale :
      (h / 2) * (2 * alpha * (f x - fstar)) ≤
        (h / 2) * ‖grad x‖ ^ (2 : ℕ) :=
    mul_le_mul_of_nonneg_left hplx (by nlinarith)
  nlinarith

/--
Source-shaped step-size corollary of
`oneStepGap_le_of_polyakLojasiewiczOn`.
-/
theorem oneStepGap_le_of_polyakLojasiewiczOn_of_le_inv
    {C : Set E} {f : E -> ℝ} {grad : E -> E}
    {alpha beta h fstar : ℝ} {x : E}
    (hsmooth : SmoothWithGradientOn C f grad beta)
    (hpl : PolyakLojasiewiczOn C f grad alpha fstar)
    (hx : x ∈ C)
    (hstep_mem : gradientDescentStep grad h x ∈ C)
    (hbeta_pos : 0 < beta)
    (hh_nonneg : 0 ≤ h)
    (hstep_size : h ≤ 1 / beta) :
    f (gradientDescentStep grad h x) - fstar ≤
      (1 - alpha * h) * (f x - fstar) := by
  have hbeta_step : beta * h ≤ 1 := by
    have hmul : beta * h ≤ beta * (1 / beta) :=
      mul_le_mul_of_nonneg_left hstep_size hbeta_pos.le
    have hcancel : beta * (1 / beta) = 1 := by
      field_simp [hbeta_pos.ne']
    linarith
  exact oneStepGap_le_of_polyakLojasiewiczOn
    hsmooth hpl hx hstep_mem hh_nonneg hbeta_step

/--
Theorem 3.6 recurrence along a gradient-descent trajectory.
-/
theorem gapRecurrence_of_polyakLojasiewiczOn
    {C : Set E} {f : E -> ℝ} {grad : E -> E}
    {alpha beta h fstar : ℝ} {x : ℕ -> E}
    (hsmooth : SmoothWithGradientOn C f grad beta)
    (hpl : PolyakLojasiewiczOn C f grad alpha fstar)
    (htraj : IsGradientDescentTrajectory grad h x)
    (hmem : ∀ n, x n ∈ C)
    (hh_nonneg : 0 ≤ h)
    (hbeta_step : beta * h ≤ 1) :
    ∀ n, f (x (n + 1)) - fstar ≤
      (1 - alpha * h) * (f (x n) - fstar) := by
  intro n
  have hstep_eq : x (n + 1) = gradientDescentStep grad h (x n) :=
    htraj.succ n
  have hstep_mem : gradientDescentStep grad h (x n) ∈ C := by
    rw [← hstep_eq]
    exact hmem (n + 1)
  rw [hstep_eq]
  exact oneStepGap_le_of_polyakLojasiewiczOn
    hsmooth hpl (hmem n) hstep_mem hh_nonneg hbeta_step

/--
A scalar nonnegative-factor recurrence unrolls to the usual power bound.
-/
theorem scalarRecurrence_le_pow {u : ℕ -> ℝ} {A : ℝ}
    (hA : 0 ≤ A)
    (hrec : ∀ n, u (n + 1) ≤ A * u n) :
    ∀ N, u N ≤ A ^ N * u 0 := by
  intro N
  have hmain :=
    discreteGronwall_sum_le hA u (fun _ => 0) N (by
      intro n _hn
      simpa using hrec n)
  simpa using hmain

/--
Chewi Theorem 3.6, supplied-interface form: gradient descent under PL has
geometric function-value convergence.
-/
theorem chewi36_gap_le_of_polyakLojasiewiczOn
    {C : Set E} {f : E -> ℝ} {grad : E -> E}
    {alpha beta h fstar : ℝ} {x : ℕ -> E}
    (hsmooth : SmoothWithGradientOn C f grad beta)
    (hpl : PolyakLojasiewiczOn C f grad alpha fstar)
    (htraj : IsGradientDescentTrajectory grad h x)
    (hmem : ∀ n, x n ∈ C)
    (hh_nonneg : 0 ≤ h)
    (hbeta_step : beta * h ≤ 1)
    (hfactor_nonneg : 0 ≤ 1 - alpha * h) :
    ∀ N, f (x N) - fstar ≤
      (1 - alpha * h) ^ N * (f (x 0) - fstar) :=
  scalarRecurrence_le_pow hfactor_nonneg
    (gapRecurrence_of_polyakLojasiewiczOn
      hsmooth hpl htraj hmem hh_nonneg hbeta_step)

/--
Chewi Theorem 3.6 with the source step-size condition `h <= 1 / beta`.
-/
theorem chewi36_gap_le_of_polyakLojasiewiczOn_of_le_inv
    {C : Set E} {f : E -> ℝ} {grad : E -> E}
    {alpha beta h fstar : ℝ} {x : ℕ -> E}
    (hsmooth : SmoothWithGradientOn C f grad beta)
    (hpl : PolyakLojasiewiczOn C f grad alpha fstar)
    (htraj : IsGradientDescentTrajectory grad h x)
    (hmem : ∀ n, x n ∈ C)
    (hbeta_pos : 0 < beta)
    (hh_nonneg : 0 ≤ h)
    (hstep_size : h ≤ 1 / beta)
    (hfactor_nonneg : 0 ≤ 1 - alpha * h) :
    ∀ N, f (x N) - fstar ≤
      (1 - alpha * h) ^ N * (f (x 0) - fstar) := by
  have hbeta_step : beta * h ≤ 1 := by
    have hmul : beta * h ≤ beta * (1 / beta) :=
      mul_le_mul_of_nonneg_left hstep_size hbeta_pos.le
    have hcancel : beta * (1 / beta) = 1 := by
      field_simp [hbeta_pos.ne']
    linarith
  exact chewi36_gap_le_of_polyakLojasiewiczOn
    hsmooth hpl htraj hmem hh_nonneg hbeta_step hfactor_nonneg

end Optimization
end StatInference
