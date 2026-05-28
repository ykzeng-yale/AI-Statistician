import StatInference.Optimization.AppendixA
import Mathlib.MeasureTheory.Integral.IntervalIntegral.FundThmCalculus

/-!
# Chewi Theorem 13.1, Local Quadratic Newton Recurrence

This module assembles the source recurrence step in Chewi Theorem 13.1 from
the Appendix A matrix perturbation and inverse-Hessian bounds.  The remaining
input is the Taylor/integral Newton remainder estimate from the theorem proof.
-/

open Matrix
open scoped MatrixOrder Matrix.Norms.L2Operator
open scoped intervalIntegral BigOperators Topology

namespace StatInference
namespace Optimization

variable {n : Type*} [Fintype n] [DecidableEq n]

/--
Chewi Theorem 13.1, Taylor/integral Newton remainder norm bound from the
source-shaped integral representation.  This packages the analytic step
`x_{+} - x_star = H^{-1} ∫_0^1 r(t) dt` together with the pointwise estimate
`||r(t)|| <= gamma (1 - t) ||x - x_star||^2`.
-/
theorem chewi131_taylor_norm_bound_of_integral_remainder
    {H : Matrix n n ℝ} {gamma : ℝ} (hgamma : 0 ≤ gamma)
    {x xNext xStar : EuclideanSpace ℝ n}
    {remainder : ℝ -> EuclideanSpace ℝ n}
    (hint : IntervalIntegrable remainder MeasureTheory.volume (0 : ℝ) 1)
    (hidentity :
      xNext - xStar =
        ((Matrix.toEuclideanLin (𝕜 := ℝ) (m := n) (n := n)).trans
          LinearMap.toContinuousLinearMap H⁻¹)
          (∫ t in (0 : ℝ)..1, remainder t))
    (hbound : ∀ t, t ∈ Set.Icc (0 : ℝ) 1 ->
      ‖remainder t‖ ≤ gamma * (1 - t) * ‖x - xStar‖ ^ (2 : ℕ)) :
    ‖xNext - xStar‖ ≤
      (gamma / 2) * ‖H⁻¹‖ * ‖x - xStar‖ ^ (2 : ℕ) := by
  have _ : 0 ≤ gamma := hgamma
  have _ : IntervalIntegrable remainder MeasureTheory.volume (0 : ℝ) 1 := hint
  rw [Matrix.l2_opNorm_def]
  let T : EuclideanSpace ℝ n →L[ℝ] EuclideanSpace ℝ n :=
    (Matrix.toEuclideanLin (𝕜 := ℝ) (m := n) (n := n)).trans
      LinearMap.toContinuousLinearMap H⁻¹
  change ‖xNext - xStar‖ ≤
    (gamma / 2) * ‖T‖ * ‖x - xStar‖ ^ (2 : ℕ)
  let e2 : ℝ := ‖x - xStar‖ ^ (2 : ℕ)
  have hscalar_int :
      IntervalIntegrable (fun t : ℝ => gamma * (1 - t) * e2)
        MeasureTheory.volume (0 : ℝ) 1 := by
    have hcont : Continuous (fun t : ℝ => gamma * (1 - t) * e2) := by
      continuity
    exact hcont.intervalIntegrable (0 : ℝ) 1
  have hbound_ae :
      ∀ᵐ t ∂MeasureTheory.volume,
        t ∈ Set.Ioc (0 : ℝ) 1 ->
          ‖remainder t‖ ≤ gamma * (1 - t) * e2 := by
    exact Filter.Eventually.of_forall fun t ht =>
      by
        have htIcc : t ∈ Set.Icc (0 : ℝ) 1 := ⟨le_of_lt ht.1, ht.2⟩
        simpa [e2] using hbound t htIcc
  have hintegral_bound :
      ‖∫ t in (0 : ℝ)..1, remainder t‖ ≤
        ∫ t in (0 : ℝ)..1, gamma * (1 - t) * e2 :=
    intervalIntegral.norm_integral_le_of_norm_le zero_le_one hbound_ae
      hscalar_int
  have hone_sub :
      (∫ t in (0 : ℝ)..1, (1 - t)) = (1 / 2 : ℝ) := by
    have hint_one_sub : IntervalIntegrable (fun t : ℝ => 1 - t)
        MeasureTheory.volume (0 : ℝ) 1 :=
      (continuous_const.sub continuous_id).intervalIntegrable (0 : ℝ) 1
    let primitive : ℝ -> ℝ := fun s => s - s ^ (2 : ℕ) / 2
    have hderiv : ∀ t, t ∈ Set.uIcc (0 : ℝ) 1 ->
        HasDerivAt primitive (1 - t) t := by
      intro t ht
      have hraw :=
        (hasDerivAt_id t).sub
          (((hasDerivAt_id t).pow (2 : ℕ)).div_const 2)
      convert hraw using 1
      simp
    have hFTC :=
      intervalIntegral.integral_eq_sub_of_hasDerivAt hderiv hint_one_sub
    norm_num [primitive] at hFTC
    simpa using hFTC
  have hscalar_eval :
      (∫ t in (0 : ℝ)..1, gamma * (1 - t) * e2) =
        (gamma / 2) * e2 := by
    have hfun :
        (fun t : ℝ => gamma * (1 - t) * e2) =
          fun t : ℝ => (gamma * e2) * (1 - t) := by
      ext t
      ring
    rw [hfun, intervalIntegral.integral_const_mul, hone_sub]
    ring
  have hintegral_bound' :
      ‖∫ t in (0 : ℝ)..1, remainder t‖ ≤ (gamma / 2) * e2 := by
    simpa [hscalar_eval] using hintegral_bound
  calc
    ‖xNext - xStar‖ =
        ‖T (∫ t in (0 : ℝ)..1, remainder t)‖ := by
      rw [hidentity]
    _ ≤ ‖T‖ * ‖∫ t in (0 : ℝ)..1, remainder t‖ :=
        T.le_opNorm _
    _ ≤ ‖T‖ * ((gamma / 2) * e2) :=
        mul_le_mul_of_nonneg_left hintegral_bound' (norm_nonneg T)
    _ = (gamma / 2) * ‖T‖ * ‖x - xStar‖ ^ (2 : ℕ) := by
        simp [e2]
        ring

/--
Chewi Theorem 13.1, one-step local quadratic recurrence from the Taylor
remainder estimate.  The hypotheses encode the source assumptions
`nabla^2 f(x_star) >= alpha I`, Lipschitz Hessian with constant `gamma`, and
the current radius condition.  The Taylor/integral estimate is supplied in the
exact norm shape immediately preceding the Hessian inverse bound in the
textbook proof.
-/
theorem chewi131_local_quadratic_step_of_taylor_bound
    {Hstar H : Matrix n n ℝ} (hHstar : Hstar.IsHermitian)
    (hH : H.IsHermitian) {alpha gamma : ℝ} (halpha : 0 < alpha)
    (hgamma : 0 < gamma)
    {x xNext xStar : EuclideanSpace ℝ n}
    (hlower : alpha • (1 : Matrix n n ℝ) ≤ Hstar)
    (hclose : ‖H - Hstar‖ ≤ gamma * ‖x - xStar‖)
    (hradius : ‖x - xStar‖ ≤ alpha / (2 * gamma))
    (htaylor :
      ‖xNext - xStar‖ ≤
        (gamma / 2) * ‖H⁻¹‖ * ‖x - xStar‖ ^ (2 : ℕ)) :
    ‖xNext - xStar‖ ≤
      (gamma / alpha) * ‖x - xStar‖ ^ (2 : ℕ) := by
  have hgr_nonneg : 0 ≤ gamma * ‖x - xStar‖ :=
    mul_nonneg (le_of_lt hgamma) (norm_nonneg _)
  have hmul_radius :
      gamma * ‖x - xStar‖ ≤ gamma * (alpha / (2 * gamma)) :=
    mul_le_mul_of_nonneg_left hradius (le_of_lt hgamma)
  have hhalf : gamma * ‖x - xStar‖ ≤ alpha / 2 := by
    have hscalar : gamma * (alpha / (2 * gamma)) = alpha / 2 := by
      field_simp [hgamma.ne']
    simpa [hscalar] using hmul_radius
  have hlower_half :
      (alpha / 2) • (1 : Matrix n n ℝ) ≤ H :=
    chewi131_hessian_lower_half_of_lipschitz_opNorm hHstar hH hgr_nonneg
      hlower hclose hhalf
  have hinv :
      ‖H⁻¹‖ ≤ 2 / alpha :=
    chewi131_inverse_l2_opNorm_le_two_div_alpha_of_hessian_lower_half hH
      halpha hlower_half
  have hcoef : (gamma / 2) * ‖H⁻¹‖ ≤ gamma / alpha := by
    calc
      (gamma / 2) * ‖H⁻¹‖ ≤ (gamma / 2) * (2 / alpha) := by
        exact mul_le_mul_of_nonneg_left hinv (by positivity)
      _ = gamma / alpha := by
        field_simp [halpha.ne']
  calc
    ‖xNext - xStar‖
        ≤ (gamma / 2) * ‖H⁻¹‖ * ‖x - xStar‖ ^ (2 : ℕ) := htaylor
    _ ≤ (gamma / alpha) * ‖x - xStar‖ ^ (2 : ℕ) := by
      exact mul_le_mul_of_nonneg_right hcoef (sq_nonneg _)

/--
Chewi Theorem 13.1, determinant invertibility of the current Hessian inside
the local radius.  This packages the source sentence that the Hessian at
`x_n` remains positive definite, hence Newton's inverse is well-defined.
-/
theorem chewi131_hessian_det_isUnit_of_radius
    {Hstar H : Matrix n n ℝ} (hHstar : Hstar.IsHermitian)
    (hH : H.IsHermitian) {alpha gamma : ℝ} (halpha : 0 < alpha)
    (hgamma : 0 < gamma)
    {x xStar : EuclideanSpace ℝ n}
    (hlower : alpha • (1 : Matrix n n ℝ) ≤ Hstar)
    (hclose : ‖H - Hstar‖ ≤ gamma * ‖x - xStar‖)
    (hradius : ‖x - xStar‖ ≤ alpha / (2 * gamma)) :
    IsUnit H.det := by
  have hgr_nonneg : 0 ≤ gamma * ‖x - xStar‖ :=
    mul_nonneg (le_of_lt hgamma) (norm_nonneg _)
  have hmul_radius :
      gamma * ‖x - xStar‖ ≤ gamma * (alpha / (2 * gamma)) :=
    mul_le_mul_of_nonneg_left hradius (le_of_lt hgamma)
  have hhalf : gamma * ‖x - xStar‖ ≤ alpha / 2 := by
    have hscalar : gamma * (alpha / (2 * gamma)) = alpha / 2 := by
      field_simp [hgamma.ne']
    simpa [hscalar] using hmul_radius
  have hlower_half :
      (alpha / 2) • (1 : Matrix n n ℝ) ≤ H :=
    chewi131_hessian_lower_half_of_lipschitz_opNorm hHstar hH hgr_nonneg
      hlower hclose hhalf
  have hhalf_pos : 0 < alpha / 2 := by
    positivity
  have hH_posDef : H.PosDef :=
    chewiA5_posDef_of_pos_scalar_one_le hH hhalf_pos hlower_half
  exact (Matrix.isUnit_iff_isUnit_det H).mp hH_posDef.isUnit

/--
Chewi Theorem 13.1, the one-step recurrence also gives the displayed
half-contraction while the current iterate remains in the local radius.
-/
theorem chewi131_local_quadratic_step_and_half_of_taylor_bound
    {Hstar H : Matrix n n ℝ} (hHstar : Hstar.IsHermitian)
    (hH : H.IsHermitian) {alpha gamma : ℝ} (halpha : 0 < alpha)
    (hgamma : 0 < gamma)
    {x xNext xStar : EuclideanSpace ℝ n}
    (hlower : alpha • (1 : Matrix n n ℝ) ≤ Hstar)
    (hclose : ‖H - Hstar‖ ≤ gamma * ‖x - xStar‖)
    (hradius : ‖x - xStar‖ ≤ alpha / (2 * gamma))
    (htaylor :
      ‖xNext - xStar‖ ≤
        (gamma / 2) * ‖H⁻¹‖ * ‖x - xStar‖ ^ (2 : ℕ)) :
    ‖xNext - xStar‖ ≤
        (gamma / alpha) * ‖x - xStar‖ ^ (2 : ℕ) ∧
      ‖xNext - xStar‖ ≤ (1 / 2) * ‖x - xStar‖ := by
  have hquad :
      ‖xNext - xStar‖ ≤
        (gamma / alpha) * ‖x - xStar‖ ^ (2 : ℕ) :=
    chewi131_local_quadratic_step_of_taylor_bound hHstar hH halpha hgamma
      hlower hclose hradius htaylor
  have hmul_radius :
      gamma * ‖x - xStar‖ ≤ gamma * (alpha / (2 * gamma)) :=
    mul_le_mul_of_nonneg_left hradius (le_of_lt hgamma)
  have hhalf_radius : gamma * ‖x - xStar‖ ≤ alpha / 2 := by
    have hscalar : gamma * (alpha / (2 * gamma)) = alpha / 2 := by
      field_simp [hgamma.ne']
    simpa [hscalar] using hmul_radius
  have hcoeff : (gamma / alpha) * ‖x - xStar‖ ≤ 1 / 2 := by
    have hdiv :
        (gamma * ‖x - xStar‖) / alpha ≤ (alpha / 2) / alpha :=
      div_le_div_of_nonneg_right hhalf_radius (le_of_lt halpha)
    calc
      (gamma / alpha) * ‖x - xStar‖ = (gamma * ‖x - xStar‖) / alpha := by
        ring
      _ ≤ (alpha / 2) / alpha := hdiv
      _ = 1 / 2 := by
        field_simp [halpha.ne']
  have hhalf_quad :
      (gamma / alpha) * ‖x - xStar‖ ^ (2 : ℕ) ≤
        (1 / 2) * ‖x - xStar‖ := by
    have hmul :=
      mul_le_mul_of_nonneg_right hcoeff (norm_nonneg (x - xStar))
    simpa [pow_two, mul_assoc, mul_comm, mul_left_comm] using hmul
  exact ⟨hquad, hquad.trans hhalf_quad⟩

/--
Chewi Theorem 13.1, one-step local quadratic recurrence from the
source-shaped integral Newton remainder representation.
-/
theorem chewi131_local_quadratic_step_of_integral_remainder
    {Hstar H : Matrix n n ℝ} (hHstar : Hstar.IsHermitian)
    (hH : H.IsHermitian) {alpha gamma : ℝ} (halpha : 0 < alpha)
    (hgamma : 0 < gamma)
    {x xNext xStar : EuclideanSpace ℝ n}
    {remainder : ℝ -> EuclideanSpace ℝ n}
    (hlower : alpha • (1 : Matrix n n ℝ) ≤ Hstar)
    (hclose : ‖H - Hstar‖ ≤ gamma * ‖x - xStar‖)
    (hradius : ‖x - xStar‖ ≤ alpha / (2 * gamma))
    (hint : IntervalIntegrable remainder MeasureTheory.volume (0 : ℝ) 1)
    (hidentity :
      xNext - xStar =
        ((Matrix.toEuclideanLin (𝕜 := ℝ) (m := n) (n := n)).trans
          LinearMap.toContinuousLinearMap H⁻¹)
          (∫ t in (0 : ℝ)..1, remainder t))
    (hbound : ∀ t, t ∈ Set.Icc (0 : ℝ) 1 ->
      ‖remainder t‖ ≤ gamma * (1 - t) * ‖x - xStar‖ ^ (2 : ℕ)) :
    ‖xNext - xStar‖ ≤
      (gamma / alpha) * ‖x - xStar‖ ^ (2 : ℕ) := by
  exact
    chewi131_local_quadratic_step_of_taylor_bound hHstar hH halpha hgamma
      hlower hclose hradius
      (chewi131_taylor_norm_bound_of_integral_remainder
        (H := H) (gamma := gamma) (x := x) (xNext := xNext)
        (xStar := xStar) (remainder := remainder) (le_of_lt hgamma)
        hint hidentity hbound)

/--
Chewi Theorem 13.1, sequence form of the local quadratic and half-contraction
display.  The induction keeps every iterate inside the local radius
`alpha / (2 * gamma)`, so the one-step theorem can be reused at each time.
-/
theorem chewi131_local_quadratic_recurrence_of_taylor_bound
    {Hstar : Matrix n n ℝ} {H : ℕ -> Matrix n n ℝ}
    (hHstar : Hstar.IsHermitian) (hH : ∀ k, (H k).IsHermitian)
    {alpha gamma : ℝ} (halpha : 0 < alpha) (hgamma : 0 < gamma)
    {x : ℕ -> EuclideanSpace ℝ n} {xStar : EuclideanSpace ℝ n}
    (hlower : alpha • (1 : Matrix n n ℝ) ≤ Hstar)
    (hclose : ∀ k, ‖H k - Hstar‖ ≤ gamma * ‖x k - xStar‖)
    (htaylor : ∀ k,
      ‖x (k + 1) - xStar‖ ≤
        (gamma / 2) * ‖(H k)⁻¹‖ * ‖x k - xStar‖ ^ (2 : ℕ))
    (hinit : ‖x 0 - xStar‖ ≤ alpha / (2 * gamma)) :
    ∀ k,
      ‖x (k + 1) - xStar‖ ≤
          (gamma / alpha) * ‖x k - xStar‖ ^ (2 : ℕ) ∧
        ‖x (k + 1) - xStar‖ ≤ (1 / 2) * ‖x k - xStar‖ := by
  have hradius : ∀ k, ‖x k - xStar‖ ≤ alpha / (2 * gamma) := by
    intro k
    induction k with
    | zero => exact hinit
    | succ k ih =>
        have hstep :=
          chewi131_local_quadratic_step_and_half_of_taylor_bound hHstar
            (hH k) halpha hgamma hlower (hclose k) ih (htaylor k)
        have hshrink :
            (1 / 2) * ‖x k - xStar‖ ≤ ‖x k - xStar‖ := by
          nlinarith [norm_nonneg (x k - xStar)]
        exact hstep.2.trans (hshrink.trans ih)
  intro k
  exact
    chewi131_local_quadratic_step_and_half_of_taylor_bound hHstar (hH k)
      halpha hgamma hlower (hclose k) (hradius k) (htaylor k)

/--
Chewi Theorem 13.1, recurrence from a Taylor estimate that is available only
while the current iterate is inside the local radius.  This matches the source
induction more closely than requiring an unconditional Taylor/inverse-Hessian
bound for every `k`.
-/
theorem chewi131_local_quadratic_recurrence_of_conditional_taylor_bound
    {Hstar : Matrix n n ℝ} {H : ℕ -> Matrix n n ℝ}
    (hHstar : Hstar.IsHermitian) (hH : ∀ k, (H k).IsHermitian)
    {alpha gamma : ℝ} (halpha : 0 < alpha) (hgamma : 0 < gamma)
    {x : ℕ -> EuclideanSpace ℝ n} {xStar : EuclideanSpace ℝ n}
    (hlower : alpha • (1 : Matrix n n ℝ) ≤ Hstar)
    (hclose : ∀ k, ‖H k - Hstar‖ ≤ gamma * ‖x k - xStar‖)
    (htaylor : ∀ k,
      ‖x k - xStar‖ ≤ alpha / (2 * gamma) ->
        ‖x (k + 1) - xStar‖ ≤
          (gamma / 2) * ‖(H k)⁻¹‖ * ‖x k - xStar‖ ^ (2 : ℕ))
    (hinit : ‖x 0 - xStar‖ ≤ alpha / (2 * gamma)) :
    ∀ k,
      ‖x (k + 1) - xStar‖ ≤
          (gamma / alpha) * ‖x k - xStar‖ ^ (2 : ℕ) ∧
        ‖x (k + 1) - xStar‖ ≤ (1 / 2) * ‖x k - xStar‖ := by
  have hradius : ∀ k, ‖x k - xStar‖ ≤ alpha / (2 * gamma) := by
    intro k
    induction k with
    | zero => exact hinit
    | succ k ih =>
        have hstep :=
          chewi131_local_quadratic_step_and_half_of_taylor_bound hHstar
            (hH k) halpha hgamma hlower (hclose k) ih (htaylor k ih)
        have hshrink :
            (1 / 2) * ‖x k - xStar‖ ≤ ‖x k - xStar‖ := by
          nlinarith [norm_nonneg (x k - xStar)]
        exact hstep.2.trans (hshrink.trans ih)
  intro k
  exact
    chewi131_local_quadratic_step_and_half_of_taylor_bound hHstar (hH k)
      halpha hgamma hlower (hclose k) (hradius k) (htaylor k (hradius k))

/--
Chewi Theorem 13.1, sequence form driven by the source-shaped integral
Newton remainder representation at every iteration.
-/
theorem chewi131_local_quadratic_recurrence_of_integral_remainder
    {Hstar : Matrix n n ℝ} {H : ℕ -> Matrix n n ℝ}
    (hHstar : Hstar.IsHermitian) (hH : ∀ k, (H k).IsHermitian)
    {alpha gamma : ℝ} (halpha : 0 < alpha) (hgamma : 0 < gamma)
    {x : ℕ -> EuclideanSpace ℝ n} {xStar : EuclideanSpace ℝ n}
    {remainder : ℕ -> ℝ -> EuclideanSpace ℝ n}
    (hlower : alpha • (1 : Matrix n n ℝ) ≤ Hstar)
    (hclose : ∀ k, ‖H k - Hstar‖ ≤ gamma * ‖x k - xStar‖)
    (hremainder_int : ∀ k,
      IntervalIntegrable (remainder k) MeasureTheory.volume (0 : ℝ) 1)
    (hidentity : ∀ k,
      x (k + 1) - xStar =
        ((Matrix.toEuclideanLin (𝕜 := ℝ) (m := n) (n := n)).trans
          LinearMap.toContinuousLinearMap (H k)⁻¹)
          (∫ t in (0 : ℝ)..1, remainder k t))
    (hbound : ∀ k t, t ∈ Set.Icc (0 : ℝ) 1 ->
      ‖remainder k t‖ ≤ gamma * (1 - t) * ‖x k - xStar‖ ^ (2 : ℕ))
    (hinit : ‖x 0 - xStar‖ ≤ alpha / (2 * gamma)) :
    ∀ k,
      ‖x (k + 1) - xStar‖ ≤
          (gamma / alpha) * ‖x k - xStar‖ ^ (2 : ℕ) ∧
        ‖x (k + 1) - xStar‖ ≤ (1 / 2) * ‖x k - xStar‖ := by
  refine
    chewi131_local_quadratic_recurrence_of_taylor_bound hHstar hH
      halpha hgamma hlower hclose ?_ hinit
  intro k
  exact
    chewi131_taylor_norm_bound_of_integral_remainder
      (H := H k) (gamma := gamma) (x := x k) (xNext := x (k + 1))
      (xStar := xStar) (remainder := remainder k) (le_of_lt hgamma)
      (hremainder_int k) (hidentity k) (hbound k)

end Optimization
end StatInference
