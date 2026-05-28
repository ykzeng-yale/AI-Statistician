import StatInference.Optimization.GradientFlow

/-!
# Chewi Corollary 2.8

This module proves the continuous-time gradient-norm convergence layer for
gradient flow.  It reuses the compiled Chewi Lemma 2.1 derivative identity
and the interval-integral API already used for Theorem 2.4.
-/

namespace StatInference
namespace Optimization

open Set
open scoped InnerProductSpace
open scoped intervalIntegral

variable {E : Type*} [NormedAddCommGroup E] [InnerProductSpace ℝ E]

/--
Chewi Lemma 2.1 integrated over `[0,t]`: along gradient flow, the integral of
the squared gradient norm is exactly the function-value drop.
-/
theorem gradientFlow_grad_sq_integral_eq_value_drop
    [CompleteSpace E] {f : E -> ℝ} {grad : E -> E}
    {x : ℝ -> E} {t : ℝ}
    (hgrad : ∀ z, HasGradientAt f (grad z) z)
    (hflow : IsGradientFlowTrajectory grad x)
    (hint_grad : IntervalIntegrable
      (fun s => ‖grad (x s)‖ ^ (2 : ℕ)) MeasureTheory.volume 0 t) :
    ∫ s in (0 : ℝ)..t, ‖grad (x s)‖ ^ (2 : ℕ) =
      f (x 0) - f (x t) := by
  let g : ℝ -> ℝ := fun s => ‖grad (x s)‖ ^ (2 : ℕ)
  let u : ℝ -> ℝ := fun s => f (x s)
  let u' : ℝ -> ℝ := fun s => -g s
  have hderiv :
      ∀ s ∈ Set.uIcc (0 : ℝ) t, HasDerivAt u (u' s) s := by
    intro s _hs
    simpa [u, u', g] using
      gradientFlow_value_hasDerivAt (t := s) hgrad hflow
  have hint_neg : IntervalIntegrable u' MeasureTheory.volume 0 t := by
    simpa [u', g] using hint_grad.neg
  have hFTC := intervalIntegral.integral_eq_sub_of_hasDerivAt hderiv hint_neg
  have hneg :
      (∫ s in (0 : ℝ)..t, u' s) =
        -∫ s in (0 : ℝ)..t, g s := by
    dsimp [u', g]
    rw [intervalIntegral.integral_neg]
  rw [hneg] at hFTC
  have hdrop :
      ∫ s in (0 : ℝ)..t, g s = u 0 - u t := by
    nlinarith
  simpa [u, g] using hdrop

/--
Chewi Corollary 2.8, integral bound:
`∫_0^t ||grad f(x_s)||^2 ds <= f(x_0) - f_*`.
-/
theorem chewi28_gradient_sq_integral_bound
    [CompleteSpace E] {f : E -> ℝ} {grad : E -> E}
    {x : ℝ -> E} {fstar t : ℝ}
    (hgrad : ∀ z, HasGradientAt f (grad z) z)
    (hflow : IsGradientFlowTrajectory grad x)
    (hstar_lower_t : fstar ≤ f (x t))
    (hint_grad : IntervalIntegrable
      (fun s => ‖grad (x s)‖ ^ (2 : ℕ)) MeasureTheory.volume 0 t) :
    ∫ s in (0 : ℝ)..t, ‖grad (x s)‖ ^ (2 : ℕ) ≤
      f (x 0) - fstar := by
  rw [gradientFlow_grad_sq_integral_eq_value_drop hgrad hflow hint_grad]
  nlinarith

/--
Chewi Corollary 2.8, average squared-gradient bound.
-/
theorem chewi28_gradient_sq_average_bound
    [CompleteSpace E] {f : E -> ℝ} {grad : E -> E}
    {x : ℝ -> E} {fstar t : ℝ}
    (hgrad : ∀ z, HasGradientAt f (grad z) z)
    (hflow : IsGradientFlowTrajectory grad x)
    (hstar_lower_t : fstar ≤ f (x t))
    (ht : 0 < t)
    (hint_grad : IntervalIntegrable
      (fun s => ‖grad (x s)‖ ^ (2 : ℕ)) MeasureTheory.volume 0 t) :
    (1 / t) * ∫ s in (0 : ℝ)..t, ‖grad (x s)‖ ^ (2 : ℕ) ≤
      (f (x 0) - fstar) / t := by
  have hbound :=
    chewi28_gradient_sq_integral_bound
      hgrad hflow hstar_lower_t hint_grad
  have hscale :=
    mul_le_mul_of_nonneg_left hbound (inv_nonneg.mpr ht.le)
  simpa [one_div, div_eq_mul_inv, mul_comm, mul_left_comm, mul_assoc]
    using hscale

/--
Continuous-time average principle for Corollary 2.8: any lower bound on all
squared gradient norms over `[0,t]` is bounded by the source average rate.
-/
theorem chewi28_interval_sq_lower_bound_le_average
    [CompleteSpace E] {f : E -> ℝ} {grad : E -> E}
    {x : ℝ -> E} {fstar m t : ℝ}
    (hgrad : ∀ z, HasGradientAt f (grad z) z)
    (hflow : IsGradientFlowTrajectory grad x)
    (hstar_lower_t : fstar ≤ f (x t))
    (ht : 0 < t)
    (hint_grad : IntervalIntegrable
      (fun s => ‖grad (x s)‖ ^ (2 : ℕ)) MeasureTheory.volume 0 t)
    (hlower : ∀ s, s ∈ Set.Icc (0 : ℝ) t ->
      m ≤ ‖grad (x s)‖ ^ (2 : ℕ)) :
    m ≤ (f (x 0) - fstar) / t := by
  have hlower_int :
      t * m ≤ ∫ s in (0 : ℝ)..t, ‖grad (x s)‖ ^ (2 : ℕ) :=
    integral_lower_bound_of_monotone_gap
      (gap := fun s => ‖grad (x s)‖ ^ (2 : ℕ))
      (t := t) (finalGap := m) ht.le hlower hint_grad
  have hupper_int :
      ∫ s in (0 : ℝ)..t, ‖grad (x s)‖ ^ (2 : ℕ) ≤
        f (x 0) - fstar :=
    chewi28_gradient_sq_integral_bound
      hgrad hflow hstar_lower_t hint_grad
  have htm : m * t ≤ f (x 0) - fstar := by
    nlinarith
  exact (le_div_iff₀ ht).mpr htm

/--
Chewi Corollary 2.8 in the source finite-minimum form, assuming the minimum
over `[0,t]` is represented by `sMin`.  A later compactness/continuity bridge
can instantiate this `IsMinOn` hypothesis automatically.
-/
theorem chewi28_min_grad_norm_le_of_isMinOn
    [CompleteSpace E] {f : E -> ℝ} {grad : E -> E}
    {x : ℝ -> E} {fstar t sMin : ℝ}
    (hgrad : ∀ z, HasGradientAt f (grad z) z)
    (hflow : IsGradientFlowTrajectory grad x)
    (hstar_lower_t : fstar ≤ f (x t))
    (ht : 0 < t)
    (hint_grad : IntervalIntegrable
      (fun s => ‖grad (x s)‖ ^ (2 : ℕ)) MeasureTheory.volume 0 t)
    (_hsMin : sMin ∈ Set.Icc (0 : ℝ) t)
    (hmin : IsMinOn (fun s => ‖grad (x s)‖) (Set.Icc (0 : ℝ) t) sMin) :
    ‖grad (x sMin)‖ ≤
      Real.sqrt ((f (x 0) - fstar) / t) := by
  have hlower_sq : ∀ s, s ∈ Set.Icc (0 : ℝ) t ->
      ‖grad (x sMin)‖ ^ (2 : ℕ) ≤
        ‖grad (x s)‖ ^ (2 : ℕ) := by
    intro s hs
    have hnorm : ‖grad (x sMin)‖ ≤ ‖grad (x s)‖ :=
      (isMinOn_iff.mp hmin) s hs
    exact (sq_le_sq₀ (norm_nonneg _) (norm_nonneg _)).mpr hnorm
  have hsq_bound :
      ‖grad (x sMin)‖ ^ (2 : ℕ) ≤
        (f (x 0) - fstar) / t :=
    chewi28_interval_sq_lower_bound_le_average
      hgrad hflow hstar_lower_t ht hint_grad hlower_sq
  exact Real.le_sqrt_of_sq_le hsq_bound

/--
Chewi Corollary 2.8, existence form.  Continuity of
`s ↦ ||grad (x s)||` on the compact interval supplies the minimizing time in
the textbook display `min_{s in [0,t]}`.
-/
theorem chewi28_exists_grad_norm_le_of_continuousOn
    [CompleteSpace E] {f : E -> ℝ} {grad : E -> E}
    {x : ℝ -> E} {fstar t : ℝ}
    (hgrad : ∀ z, HasGradientAt f (grad z) z)
    (hflow : IsGradientFlowTrajectory grad x)
    (hstar_lower_t : fstar ≤ f (x t))
    (ht : 0 < t)
    (hint_grad : IntervalIntegrable
      (fun s => ‖grad (x s)‖ ^ (2 : ℕ)) MeasureTheory.volume 0 t)
    (hcont_norm : ContinuousOn (fun s => ‖grad (x s)‖)
      (Set.Icc (0 : ℝ) t)) :
    ∃ sMin ∈ Set.Icc (0 : ℝ) t,
      ‖grad (x sMin)‖ ≤
        Real.sqrt ((f (x 0) - fstar) / t) := by
  rcases isCompact_Icc.exists_isMinOn (nonempty_Icc.mpr ht.le) hcont_norm
    with ⟨sMin, hsMin, hmin⟩
  exact ⟨sMin, hsMin,
    chewi28_min_grad_norm_le_of_isMinOn
      hgrad hflow hstar_lower_t ht hint_grad hsMin hmin⟩

/--
Chewi Corollary 2.8, existence form with the interval-integrability
hypothesis discharged by continuity of `s ↦ ||grad (x s)||`.
-/
theorem chewi28_exists_grad_norm_le_of_continuousOn_norm
    [CompleteSpace E] {f : E -> ℝ} {grad : E -> E}
    {x : ℝ -> E} {fstar t : ℝ}
    (hgrad : ∀ z, HasGradientAt f (grad z) z)
    (hflow : IsGradientFlowTrajectory grad x)
    (hstar_lower_t : fstar ≤ f (x t))
    (ht : 0 < t)
    (hcont_norm : ContinuousOn (fun s => ‖grad (x s)‖)
      (Set.Icc (0 : ℝ) t)) :
    ∃ sMin ∈ Set.Icc (0 : ℝ) t,
      ‖grad (x sMin)‖ ≤
        Real.sqrt ((f (x 0) - fstar) / t) := by
  have hint_grad : IntervalIntegrable
      (fun s => ‖grad (x s)‖ ^ (2 : ℕ)) MeasureTheory.volume 0 t :=
    (hcont_norm.pow 2).intervalIntegrable_of_Icc ht.le
  exact chewi28_exists_grad_norm_le_of_continuousOn
    hgrad hflow hstar_lower_t ht hint_grad hcont_norm

/--
Chewi Corollary 2.8, existence form from continuity of the gradient-oracle
trajectory.
-/
theorem chewi28_exists_grad_norm_le_of_continuousOn_grad
    [CompleteSpace E] {f : E -> ℝ} {grad : E -> E}
    {x : ℝ -> E} {fstar t : ℝ}
    (hgrad : ∀ z, HasGradientAt f (grad z) z)
    (hflow : IsGradientFlowTrajectory grad x)
    (hstar_lower_t : fstar ≤ f (x t))
    (ht : 0 < t)
    (hcont_grad : ContinuousOn (fun s => grad (x s))
      (Set.Icc (0 : ℝ) t)) :
    ∃ sMin ∈ Set.Icc (0 : ℝ) t,
      ‖grad (x sMin)‖ ≤
        Real.sqrt ((f (x 0) - fstar) / t) :=
  chewi28_exists_grad_norm_le_of_continuousOn_norm
    hgrad hflow hstar_lower_t ht hcont_grad.norm

end Optimization
end StatInference
