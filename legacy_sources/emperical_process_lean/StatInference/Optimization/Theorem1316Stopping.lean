import StatInference.Optimization.Lemma1316Source

/-!
# Chewi Theorem 13.16 stopping consequences

This module formalizes the sentence following Chewi Lemma 13.16: once the
main-stage parameter is large enough, the Lemma 13.16 source display gives an
epsilon-accurate linear-objective gap.
-/

namespace StatInference
namespace Optimization

/--
Chewi Lemma 13.16 source display implies the final epsilon surface under the
standard `lambda <= 1/4` and `2 * nu <= eps * t` stopping gates.
-/
theorem chewi1316_objectiveGapEpsSurface_of_sourceSurface_le_quarter_and_large_t
    {E : Type*} [NormedAddCommGroup E] [InnerProductSpace ℝ E]
    {a x optimum : E} {t nu lambda eps : ℝ}
    (hsurface : Chewi1316ObjectiveGapSurface a x optimum t nu lambda)
    (ht_pos : 0 < t)
    (hnu_one : 1 ≤ nu)
    (hlambda_nonneg : 0 ≤ lambda)
    (hlambda_le_quarter : lambda ≤ 1 / 4)
    (ht_large : 2 * nu ≤ eps * t) :
    Chewi1316ObjectiveGapEpsSurface a x optimum eps := by
  change inner ℝ a x - inner ℝ a optimum ≤ eps
  change inner ℝ a x - inner ℝ a optimum ≤
    (1 / t) *
      (nu + (((lambda + Real.sqrt nu) * lambda) / (1 - lambda))) at hsurface
  have hnumer :
      nu + (((lambda + Real.sqrt nu) * lambda) / (1 - lambda)) ≤ 2 * nu :=
    chewi1316_objectiveGapNumerator_le_two_mul
      hnu_one hlambda_nonneg hlambda_le_quarter
  have hscaled :
      (1 / t) *
          (nu + (((lambda + Real.sqrt nu) * lambda) / (1 - lambda))) ≤
        (1 / t) * (2 * nu) :=
    mul_le_mul_of_nonneg_left hnumer (by positivity)
  have hstop : (1 / t) * (2 * nu) ≤ eps := by
    rw [one_div, inv_mul_le_iff₀ ht_pos]
    simpa [mul_comm] using ht_large
  exact hsurface.trans (hscaled.trans hstop)

/--
Logarithmic main-stage stopping rule for the Chewi Lemma 13.16 source surface.
The hypothesis is the explicit source inequality
`log (2 * nu / (eps * t0)) <= N log (1 + c0 / sqrt nu)`.
-/
theorem chewi1316_objectiveGapEpsSurface_of_sourceSurface_log_le
    {E : Type*} [NormedAddCommGroup E] [InnerProductSpace ℝ E]
    {a x optimum : E} {N : ℕ} {nu c0 t0 lambda eps : ℝ}
    (hsurface :
      Chewi1316ObjectiveGapSurface a x optimum
        ((1 + c0 / Real.sqrt nu) ^ N * t0) nu lambda)
    (hnu_one : 1 ≤ nu)
    (hc0_pos : 0 < c0)
    (ht0_pos : 0 < t0)
    (heps_pos : 0 < eps)
    (hlambda_nonneg : 0 ≤ lambda)
    (hlambda_le_quarter : lambda ≤ 1 / 4)
    (hlog :
      Real.log ((2 * nu) / (eps * t0)) ≤
        (N : ℝ) * Real.log (1 + c0 / Real.sqrt nu)) :
    Chewi1316ObjectiveGapEpsSurface a x optimum eps := by
  have hnu_pos : 0 < nu := by nlinarith
  have hsqrt_pos : 0 < Real.sqrt nu := Real.sqrt_pos.2 hnu_pos
  have hdelta_pos : 0 < c0 / Real.sqrt nu := div_pos hc0_pos hsqrt_pos
  have hr_pos : 0 < 1 + c0 / Real.sqrt nu := by nlinarith
  have ht_pos : 0 < (1 + c0 / Real.sqrt nu) ^ N * t0 :=
    mul_pos (pow_pos hr_pos N) ht0_pos
  have htarget_pos : 0 < 2 * nu := by nlinarith
  have hlarge :
      2 * nu ≤
        eps * ((1 + c0 / Real.sqrt nu) ^ N * t0) :=
    chewi1316_large_parameter_condition_of_log_le
      (r := 1 + c0 / Real.sqrt nu) (tMain := t0)
      (eps := eps) (target := 2 * nu) (N := N)
      hr_pos ht0_pos heps_pos htarget_pos hlog
  exact
    chewi1316_objectiveGapEpsSurface_of_sourceSurface_le_quarter_and_large_t
      (a := a) (x := x) (optimum := optimum)
      (t := (1 + c0 / Real.sqrt nu) ^ N * t0)
      (nu := nu) (lambda := lambda) (eps := eps)
      hsurface ht_pos hnu_one hlambda_nonneg
      hlambda_le_quarter hlarge

/--
Existential main-stage stopping consequence: if every main-stage iterate has
the Chewi Lemma 13.16 source surface and Newton decrement at most `1/4`, then
some main-stage index is epsilon-accurate.
-/
theorem chewi1316_exists_mainStageIndex_objectiveGapEpsSurface_of_sourceSurface_family
    {E : Type*} [NormedAddCommGroup E] [InnerProductSpace ℝ E]
    {a optimum : E} {xseq : ℕ -> E} {lambdaSeq : ℕ -> ℝ}
    {nu c0 t0 eps : ℝ}
    (hnu_one : 1 ≤ nu)
    (hc0_pos : 0 < c0)
    (ht0_pos : 0 < t0)
    (heps_pos : 0 < eps)
    (hlambda_nonneg : ∀ N : ℕ, 0 ≤ lambdaSeq N)
    (hlambda_le_quarter : ∀ N : ℕ, lambdaSeq N ≤ 1 / 4)
    (hsurface : ∀ N : ℕ,
      Chewi1316ObjectiveGapSurface a (xseq N) optimum
        ((1 + c0 / Real.sqrt nu) ^ N * t0) nu (lambdaSeq N)) :
    ∃ N : ℕ, Chewi1316ObjectiveGapEpsSurface a (xseq N) optimum eps := by
  have hnu_pos : 0 < nu := by nlinarith
  obtain ⟨N, hlarge⟩ :=
    chewi1316_exists_mainStageIndex_large_parameter_of_pos
      (nu := nu) (c0 := c0) (tMain := t0) (eps := eps)
      hnu_pos hc0_pos ht0_pos heps_pos
  have hsqrt_pos : 0 < Real.sqrt nu := Real.sqrt_pos.2 hnu_pos
  have hdelta_pos : 0 < c0 / Real.sqrt nu := div_pos hc0_pos hsqrt_pos
  have hr_pos : 0 < 1 + c0 / Real.sqrt nu := by nlinarith
  have ht_pos : 0 < (1 + c0 / Real.sqrt nu) ^ N * t0 :=
    mul_pos (pow_pos hr_pos N) ht0_pos
  exact
    ⟨N,
      chewi1316_objectiveGapEpsSurface_of_sourceSurface_le_quarter_and_large_t
        (a := a) (x := xseq N) (optimum := optimum)
        (t := (1 + c0 / Real.sqrt nu) ^ N * t0)
        (nu := nu) (lambda := lambdaSeq N) (eps := eps)
        (hsurface N) ht_pos hnu_one (hlambda_nonneg N)
        (hlambda_le_quarter N) hlarge⟩

end Optimization
end StatInference
