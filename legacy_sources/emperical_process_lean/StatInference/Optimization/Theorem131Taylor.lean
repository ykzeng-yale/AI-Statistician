import StatInference.Optimization.Theorem131
import StatInference.Optimization.InteriorPoint

/-!
# Chewi Theorem 13.1, Taylor Remainder Bridge

This module discharges another layer of the Chewi Theorem 13.1 Taylor/Newton
remainder gate.  It reuses the segment-gradient FTC infrastructure from the
interior-point lane, then feeds the resulting integral representation and
pointwise Hessian-Lipschitz bound into the recurrence layer in `Theorem131`.
-/

open Matrix
open scoped MatrixOrder Matrix.Norms.L2Operator
open scoped intervalIntegral BigOperators Topology

namespace StatInference
namespace Optimization

section Normed

variable {E : Type*} [NormedAddCommGroup E]

/--
Chewi Theorem 13.1 recurrence scaffold: if every iterate inside the source
local radius admits the quadratic step and half-contraction, then the full
sequence satisfies those two estimates at every time.  This isolates the
induction used repeatedly by the matrix and range-space Newton routes.
-/
theorem chewi131_local_quadratic_recurrence_of_conditional_step
    {alpha gamma : ℝ}
    {x : ℕ -> E} {xStar : E}
    (hstep : ∀ k,
      ‖x k - xStar‖ ≤ alpha / (2 * gamma) ->
        ‖x (k + 1) - xStar‖ ≤
            (gamma / alpha) * ‖x k - xStar‖ ^ (2 : ℕ) ∧
          ‖x (k + 1) - xStar‖ ≤ (1 / 2) * ‖x k - xStar‖)
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
        have hstepk := hstep k ih
        have hshrink :
            (1 / 2) * ‖x k - xStar‖ ≤ ‖x k - xStar‖ := by
          nlinarith [norm_nonneg (x k - xStar)]
        exact hstepk.2.trans (hshrink.trans ih)
  intro k
  exact hstep k (hradius k)

end Normed

section Hilbert

variable {E : Type*} [NormedAddCommGroup E] [InnerProductSpace ℝ E]

/--
Chewi Theorem 13.1 Taylor identity layer in a Hilbert-space supplied-Hessian
form.  The gradient FTC along the segment from `x_star` to `x` turns the
Newton update into
`x_+ - x_star = H_x^{-1} ∫_0^1 (H_x - Hess(z_t))(x - x_star) dt`.
-/
theorem chewi131_integral_remainder_identity_of_gradient_ftc
    [CompleteSpace E]
    {grad : E -> E} {hess : E -> E →L[ℝ] E}
    {Hinv : E →L[ℝ] E} {x xNext xStar : E}
    (hgrad : ∀ t, t ∈ Set.uIcc (0 : ℝ) 1 ->
      HasFDerivAt grad
        (hess (hessianSegmentPoint xStar x t))
        (hessianSegmentPoint xStar x t))
    (hint : IntervalIntegrable
      (fun t : ℝ => hess (hessianSegmentPoint xStar x t) (x - xStar))
      MeasureTheory.volume (0 : ℝ) 1)
    (hgrad_star : grad xStar = 0)
    (hnewton : xNext = x - Hinv (grad x))
    (hleft : Hinv (hess x (x - xStar)) = x - xStar) :
    xNext - xStar =
      Hinv (∫ t in (0 : ℝ)..1,
        hess x (x - xStar) -
          hess (hessianSegmentPoint xStar x t) (x - xStar)) := by
  let d : E := x - xStar
  have hFTC :
      (∫ t in (0 : ℝ)..1,
          hess (hessianSegmentPoint xStar x t) d) =
        grad x - grad xStar := by
    simpa [d] using
      hessianSegmentGradient_integral_eq_sub_of_hasFDerivAt
        (grad := grad) (hess := hess) (x := xStar) (y := x)
        hgrad (by simpa [d] using hint)
  have hconst_int : IntervalIntegrable (fun _ : ℝ => hess x d)
      MeasureTheory.volume (0 : ℝ) 1 :=
    intervalIntegrable_const
  have hintegral :
      (∫ t in (0 : ℝ)..1,
          hess x d - hess (hessianSegmentPoint xStar x t) d) =
        hess x d - (grad x - grad xStar) := by
    rw [intervalIntegral.integral_sub hconst_int (by simpa [d] using hint)]
    rw [hFTC]
    simp
  have hleft' : x - xStar = Hinv (hess x d) := by
    simpa [d] using hleft.symm
  calc
    xNext - xStar = (x - xStar) - Hinv (grad x) := by
      rw [hnewton]
      abel
    _ = Hinv (hess x d) - Hinv (grad x) := by
      rw [hleft']
    _ = Hinv (hess x d - grad x) := by
      simp
    _ = Hinv (hess x d - (grad x - grad xStar)) := by
      simp [hgrad_star]
    _ = Hinv (∫ t in (0 : ℝ)..1,
          hess x d - hess (hessianSegmentPoint xStar x t) d) := by
      rw [hintegral]
    _ = Hinv (∫ t in (0 : ℝ)..1,
          hess x (x - xStar) -
            hess (hessianSegmentPoint xStar x t) (x - xStar)) := by
      simp [d]

/--
Chewi Theorem 13.1 pointwise Taylor remainder bound from a Hessian-Lipschitz
operator-norm estimate along the segment from `x_star` to `x`.
-/
theorem chewi131_integral_remainder_pointwise_bound_of_hessian_lipschitz
    {hess : E -> E →L[ℝ] E} {gamma : ℝ} {x xStar : E}
    (hlip : ∀ t, t ∈ Set.Icc (0 : ℝ) 1 ->
      ‖hess x - hess (hessianSegmentPoint xStar x t)‖ ≤
        gamma * (1 - t) * ‖x - xStar‖) :
    ∀ t, t ∈ Set.Icc (0 : ℝ) 1 ->
      ‖hess x (x - xStar) -
          hess (hessianSegmentPoint xStar x t) (x - xStar)‖ ≤
        gamma * (1 - t) * ‖x - xStar‖ ^ (2 : ℕ) := by
  intro t ht
  let d : E := x - xStar
  calc
    ‖hess x (x - xStar) -
        hess (hessianSegmentPoint xStar x t) (x - xStar)‖ =
        ‖(hess x - hess (hessianSegmentPoint xStar x t)) d‖ := by
      simp [d]
    _ ≤ ‖hess x - hess (hessianSegmentPoint xStar x t)‖ * ‖d‖ :=
        (hess x - hess (hessianSegmentPoint xStar x t)).le_opNorm d
    _ ≤ (gamma * (1 - t) * ‖x - xStar‖) * ‖d‖ :=
        mul_le_mul_of_nonneg_right (hlip t ht) (norm_nonneg d)
    _ = gamma * (1 - t) * ‖x - xStar‖ ^ (2 : ℕ) := by
        simp [d]
        ring

/--
Chewi Theorem 13.1 Taylor norm estimate from gradient FTC in a Hilbert-space
continuous-linear-map form.  This is the range-space analogue of the matrix
bound below: the inverse Hessian is supplied as a CLM `Hinv`, and the bound
keeps its operator norm explicit.
-/
theorem chewi131_taylor_norm_bound_of_gradient_ftc_clm
    [CompleteSpace E]
    {grad : E -> E} {hess : E -> E →L[ℝ] E}
    {Hinv : E →L[ℝ] E} {gamma : ℝ}
    {x xNext xStar : E}
    (hgrad : ∀ t, t ∈ Set.uIcc (0 : ℝ) 1 ->
      HasFDerivAt grad
        (hess (hessianSegmentPoint xStar x t))
        (hessianSegmentPoint xStar x t))
    (hint : IntervalIntegrable
      (fun t : ℝ => hess (hessianSegmentPoint xStar x t) (x - xStar))
      MeasureTheory.volume (0 : ℝ) 1)
    (hgrad_star : grad xStar = 0)
    (hnewton : xNext = x - Hinv (grad x))
    (hleft : Hinv (hess x (x - xStar)) = x - xStar)
    (hlip : ∀ t, t ∈ Set.Icc (0 : ℝ) 1 ->
      ‖hess x - hess (hessianSegmentPoint xStar x t)‖ ≤
        gamma * (1 - t) * ‖x - xStar‖) :
    ‖xNext - xStar‖ ≤
      (gamma / 2) * ‖Hinv‖ * ‖x - xStar‖ ^ (2 : ℕ) := by
  let remainder : ℝ -> E := fun t =>
    hess x (x - xStar) -
      hess (hessianSegmentPoint xStar x t) (x - xStar)
  have hrem_int : IntervalIntegrable remainder MeasureTheory.volume (0 : ℝ) 1 := by
    have hconst_int : IntervalIntegrable
        (fun _ : ℝ => hess x (x - xStar))
        MeasureTheory.volume (0 : ℝ) 1 :=
      intervalIntegrable_const
    exact hconst_int.sub hint
  have hidentity :
      xNext - xStar = Hinv (∫ t in (0 : ℝ)..1, remainder t) := by
    simpa [remainder] using
      chewi131_integral_remainder_identity_of_gradient_ftc
        (grad := grad) (hess := hess) (Hinv := Hinv)
        (x := x) (xNext := xNext) (xStar := xStar)
        hgrad hint hgrad_star hnewton hleft
  have hbound : ∀ t, t ∈ Set.Icc (0 : ℝ) 1 ->
      ‖remainder t‖ ≤ gamma * (1 - t) * ‖x - xStar‖ ^ (2 : ℕ) := by
    simpa [remainder] using
      chewi131_integral_remainder_pointwise_bound_of_hessian_lipschitz
        (hess := hess) (gamma := gamma) (x := x) (xStar := xStar)
        hlip
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
    exact Filter.Eventually.of_forall fun t ht => by
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
      intro t _ht
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
    ‖xNext - xStar‖ = ‖Hinv (∫ t in (0 : ℝ)..1, remainder t)‖ := by
      rw [hidentity]
    _ ≤ ‖Hinv‖ * ‖∫ t in (0 : ℝ)..1, remainder t‖ :=
        Hinv.le_opNorm _
    _ ≤ ‖Hinv‖ * ((gamma / 2) * e2) :=
        mul_le_mul_of_nonneg_left hintegral_bound' (norm_nonneg Hinv)
    _ = (gamma / 2) * ‖Hinv‖ * ‖x - xStar‖ ^ (2 : ℕ) := by
        simp [e2]
        ring

/--
Chewi Theorem 13.1 inverse-Hessian norm bridge in continuous-linear-map form.
If the Hessian at the current point has quadratic lower bound `alpha / 2`
and `Hinv` is its right inverse, then `‖Hinv‖ <= 2 / alpha`.
-/
theorem chewi131_inverse_clm_opNorm_le_two_div_alpha_of_hessian_lower_half
    {H Hinv : E →L[ℝ] E} {alpha : ℝ} (halpha : 0 < alpha)
    (hlower : ∀ v : E, (alpha / 2) * ‖v‖ ^ (2 : ℕ) ≤ inner ℝ (H v) v)
    (hright : ∀ v : E, H (Hinv v) = v) :
    ‖Hinv‖ ≤ 2 / alpha := by
  have hhalf_pos : 0 < alpha / 2 := by positivity
  have hbound : ‖Hinv‖ ≤ (alpha / 2)⁻¹ :=
    continuousLinearMap_opNorm_right_inverse_le_of_inner_lower hhalf_pos
      hlower hright
  have hinv : (alpha / 2)⁻¹ = 2 / alpha := by
    field_simp [halpha.ne']
  simpa [hinv] using hbound

/--
Chewi Theorem 13.1 local quadratic Newton step in CLM form, after the Taylor
bound and an explicit inverse-Hessian norm estimate have been supplied.
-/
theorem chewi131_local_quadratic_step_of_taylor_bound_clm
    {Hinv : E →L[ℝ] E} {alpha gamma : ℝ}
    (halpha : 0 < alpha) (hgamma : 0 ≤ gamma)
    {x xNext xStar : E}
    (hinv : ‖Hinv‖ ≤ 2 / alpha)
    (htaylor :
      ‖xNext - xStar‖ ≤
        (gamma / 2) * ‖Hinv‖ * ‖x - xStar‖ ^ (2 : ℕ)) :
    ‖xNext - xStar‖ ≤
      (gamma / alpha) * ‖x - xStar‖ ^ (2 : ℕ) := by
  have hcoef : (gamma / 2) * ‖Hinv‖ ≤ gamma / alpha := by
    calc
      (gamma / 2) * ‖Hinv‖ ≤ (gamma / 2) * (2 / alpha) := by
        exact mul_le_mul_of_nonneg_left hinv (by positivity)
      _ = gamma / alpha := by
        field_simp [halpha.ne']
  exact htaylor.trans (mul_le_mul_of_nonneg_right hcoef (sq_nonneg _))

/--
Chewi Theorem 13.1 local quadratic Newton step in CLM form, with the
inverse-Hessian norm estimate discharged from the Hessian lower bound and the
right-inverse property.
-/
theorem chewi131_local_quadratic_step_of_taylor_bound_clm_of_hessian_lower_half
    {H Hinv : E →L[ℝ] E} {alpha gamma : ℝ}
    (halpha : 0 < alpha) (hgamma : 0 ≤ gamma)
    {x xNext xStar : E}
    (hlower : ∀ v : E, (alpha / 2) * ‖v‖ ^ (2 : ℕ) ≤ inner ℝ (H v) v)
    (hright : ∀ v : E, H (Hinv v) = v)
    (htaylor :
      ‖xNext - xStar‖ ≤
        (gamma / 2) * ‖Hinv‖ * ‖x - xStar‖ ^ (2 : ℕ)) :
    ‖xNext - xStar‖ ≤
      (gamma / alpha) * ‖x - xStar‖ ^ (2 : ℕ) := by
  exact chewi131_local_quadratic_step_of_taylor_bound_clm halpha hgamma
    (chewi131_inverse_clm_opNorm_le_two_div_alpha_of_hessian_lower_half
      halpha hlower hright)
    htaylor

/--
Chewi Theorem 13.1 local quadratic Newton step plus the source `1/2`
contraction consequence under the usual small-radius condition.
-/
theorem chewi131_local_quadratic_step_and_half_of_taylor_bound_clm_of_hessian_lower_half
    {H Hinv : E →L[ℝ] E} {alpha gamma : ℝ}
    (halpha : 0 < alpha) (hgamma : 0 < gamma)
    {x xNext xStar : E}
    (hradius : ‖x - xStar‖ ≤ alpha / (2 * gamma))
    (hlower : ∀ v : E, (alpha / 2) * ‖v‖ ^ (2 : ℕ) ≤ inner ℝ (H v) v)
    (hright : ∀ v : E, H (Hinv v) = v)
    (htaylor :
      ‖xNext - xStar‖ ≤
        (gamma / 2) * ‖Hinv‖ * ‖x - xStar‖ ^ (2 : ℕ)) :
    ‖xNext - xStar‖ ≤
        (gamma / alpha) * ‖x - xStar‖ ^ (2 : ℕ) ∧
      ‖xNext - xStar‖ ≤ (1 / 2) * ‖x - xStar‖ := by
  have hquad :=
    chewi131_local_quadratic_step_of_taylor_bound_clm_of_hessian_lower_half
      halpha hgamma.le hlower hright htaylor
  have hcoeff : (gamma / alpha) * ‖x - xStar‖ ≤ 1 / 2 := by
    have hcoef_nonneg : 0 ≤ gamma / alpha := div_nonneg hgamma.le halpha.le
    have hmul := mul_le_mul_of_nonneg_left hradius hcoef_nonneg
    have hscalar : (gamma / alpha) * (alpha / (gamma * 2)) = 1 / 2 := by
      field_simp [halpha.ne', hgamma.ne']
    simpa [hscalar, mul_assoc, mul_comm, mul_left_comm] using hmul
  have hhalf_quad :
      (gamma / alpha) * ‖x - xStar‖ ^ (2 : ℕ) ≤
        (1 / 2) * ‖x - xStar‖ := by
    have hmul :=
      mul_le_mul_of_nonneg_right hcoeff (norm_nonneg (x - xStar))
    simpa [pow_two, mul_assoc, mul_comm, mul_left_comm] using hmul
  exact ⟨hquad, hquad.trans hhalf_quad⟩

/--
Chewi Theorem 13.1 range-space sequence recurrence from an unconditional CLM
Taylor estimate and Hessian lower/right-inverse data at every iterate.
-/
theorem chewi131_local_quadratic_recurrence_of_taylor_bound_clm_of_hessian_lower_half
    {H Hinv : ℕ -> E →L[ℝ] E} {alpha gamma : ℝ}
    (halpha : 0 < alpha) (hgamma : 0 < gamma)
    {x : ℕ -> E} {xStar : E}
    (hlower : ∀ k v, (alpha / 2) * ‖v‖ ^ (2 : ℕ) ≤ inner ℝ (H k v) v)
    (hright : ∀ k v, H k (Hinv k v) = v)
    (htaylor : ∀ k,
      ‖x (k + 1) - xStar‖ ≤
        (gamma / 2) * ‖Hinv k‖ * ‖x k - xStar‖ ^ (2 : ℕ))
    (hinit : ‖x 0 - xStar‖ ≤ alpha / (2 * gamma)) :
    ∀ k,
      ‖x (k + 1) - xStar‖ ≤
          (gamma / alpha) * ‖x k - xStar‖ ^ (2 : ℕ) ∧
        ‖x (k + 1) - xStar‖ ≤ (1 / 2) * ‖x k - xStar‖ := by
  refine chewi131_local_quadratic_recurrence_of_conditional_step ?_ hinit
  intro k hradius
  exact chewi131_local_quadratic_step_and_half_of_taylor_bound_clm_of_hessian_lower_half
    (H := H k) (Hinv := Hinv k) (alpha := alpha) (gamma := gamma)
    (x := x k) (xNext := x (k + 1)) (xStar := xStar)
    halpha hgamma hradius (hlower k) (hright k) (htaylor k)

/--
Chewi Theorem 13.1 range-space sequence recurrence when the Taylor estimate
and quantitative Hessian data are available conditionally inside the local
radius.  This matches the source induction shape for local Newton convergence.
-/
theorem chewi131_local_quadratic_recurrence_of_conditional_taylor_bound_clm_of_hessian_lower_half
    {H Hinv : ℕ -> E →L[ℝ] E} {alpha gamma : ℝ}
    (halpha : 0 < alpha) (hgamma : 0 < gamma)
    {x : ℕ -> E} {xStar : E}
    (hlower : ∀ k, ‖x k - xStar‖ ≤ alpha / (2 * gamma) ->
      ∀ v, (alpha / 2) * ‖v‖ ^ (2 : ℕ) ≤ inner ℝ (H k v) v)
    (hright : ∀ k, ‖x k - xStar‖ ≤ alpha / (2 * gamma) ->
      ∀ v, H k (Hinv k v) = v)
    (htaylor : ∀ k, ‖x k - xStar‖ ≤ alpha / (2 * gamma) ->
      ‖x (k + 1) - xStar‖ ≤
        (gamma / 2) * ‖Hinv k‖ * ‖x k - xStar‖ ^ (2 : ℕ))
    (hinit : ‖x 0 - xStar‖ ≤ alpha / (2 * gamma)) :
    ∀ k,
      ‖x (k + 1) - xStar‖ ≤
          (gamma / alpha) * ‖x k - xStar‖ ^ (2 : ℕ) ∧
        ‖x (k + 1) - xStar‖ ≤ (1 / 2) * ‖x k - xStar‖ := by
  refine chewi131_local_quadratic_recurrence_of_conditional_step ?_ hinit
  intro k hradius
  exact chewi131_local_quadratic_step_and_half_of_taylor_bound_clm_of_hessian_lower_half
    (H := H k) (Hinv := Hinv k) (alpha := alpha) (gamma := gamma)
    (x := x k) (xNext := x (k + 1)) (xStar := xStar)
    halpha hgamma hradius (hlower k hradius) (hright k hradius)
    (htaylor k hradius)

end Hilbert

variable {n : Type*} [Fintype n] [DecidableEq n]

/-- The Euclidean continuous linear map induced by a real square matrix. -/
noncomputable abbrev chewi131MatrixCLM (A : Matrix n n ℝ) :
    EuclideanSpace ℝ n →L[ℝ] EuclideanSpace ℝ n :=
  ((Matrix.toEuclideanLin (𝕜 := ℝ) (m := n) (n := n)).trans
    LinearMap.toContinuousLinearMap) A

/--
The matrix L2 operator norm is exactly the operator norm of the induced
Euclidean continuous linear map, so subtracting Hessian matrices commutes with
the corresponding continuous-linear-map subtraction.
-/
theorem chewi131_matrix_clm_sub_norm_eq (A B : Matrix n n ℝ) :
    ‖chewi131MatrixCLM A - chewi131MatrixCLM B‖ = ‖A - B‖ := by
  rw [Matrix.l2_opNorm_def]
  let L :=
    (Matrix.toEuclideanLin (𝕜 := ℝ) (m := n) (n := n)).trans
      LinearMap.toContinuousLinearMap
  change ‖L A - L B‖ = ‖L (A - B)‖
  exact congrArg norm (L.map_sub A B).symm

/--
Matrix/Hessian bridge for the inverse-action hypothesis in Chewi Theorem 13.1:
if the supplied Hessian oracle at `x` is the Euclidean linear map induced by
`H`, then the matrix inverse acts as a left inverse on the displacement.
-/
theorem chewi131_matrix_inverse_action_of_hessian_matrix
    {H : Matrix n n ℝ} (hdet : IsUnit H.det)
    {hess : EuclideanSpace ℝ n ->
      EuclideanSpace ℝ n →L[ℝ] EuclideanSpace ℝ n}
    {x xStar : EuclideanSpace ℝ n}
    (hhess :
      hess x =
        ((Matrix.toEuclideanLin (𝕜 := ℝ) (m := n) (n := n)).trans
          LinearMap.toContinuousLinearMap H)) :
    ((Matrix.toEuclideanLin (𝕜 := ℝ) (m := n) (n := n)).trans
      LinearMap.toContinuousLinearMap H⁻¹) (hess x (x - xStar)) =
      x - xStar := by
  have hmul : H⁻¹ * H = 1 := Matrix.nonsing_inv_mul H hdet
  rw [hhess]
  simp [Matrix.toLpLin_apply, Matrix.mulVec_mulVec, hmul]

/--
Matrix-shaped Hessian Lipschitz control implies the continuous-linear-map
operator-norm Lipschitz control consumed by the gradient-FTC Taylor bridge.
-/
theorem chewi131_hessian_lipschitz_clm_of_matrix_lipschitz
    {H : Matrix n n ℝ} {Hseg : ℝ -> Matrix n n ℝ} {gamma : ℝ}
    {hess : EuclideanSpace ℝ n ->
      EuclideanSpace ℝ n →L[ℝ] EuclideanSpace ℝ n}
    {x xStar : EuclideanSpace ℝ n}
    (hhess_x :
      hess x =
        ((Matrix.toEuclideanLin (𝕜 := ℝ) (m := n) (n := n)).trans
          LinearMap.toContinuousLinearMap H))
    (hhess_seg : ∀ t, t ∈ Set.Icc (0 : ℝ) 1 ->
      hess (hessianSegmentPoint xStar x t) =
        ((Matrix.toEuclideanLin (𝕜 := ℝ) (m := n) (n := n)).trans
          LinearMap.toContinuousLinearMap (Hseg t)))
    (hlip : ∀ t, t ∈ Set.Icc (0 : ℝ) 1 ->
      ‖H - Hseg t‖ ≤ gamma * (1 - t) * ‖x - xStar‖) :
    ∀ t, t ∈ Set.Icc (0 : ℝ) 1 ->
      ‖hess x - hess (hessianSegmentPoint xStar x t)‖ ≤
        gamma * (1 - t) * ‖x - xStar‖ := by
  intro t ht
  calc
    ‖hess x - hess (hessianSegmentPoint xStar x t)‖ =
        ‖H - Hseg t‖ := by
      rw [hhess_x, hhess_seg t ht]
      simpa [chewi131MatrixCLM] using
        chewi131_matrix_clm_sub_norm_eq H (Hseg t)
    _ ≤ gamma * (1 - t) * ‖x - xStar‖ := hlip t ht

/--
Chewi Theorem 13.1 Taylor norm estimate from gradient FTC plus a
Hessian-Lipschitz operator-norm bound.  This removes the V60 supplied
integral-remainder data by constructing it from the segment gradient theorem.
-/
theorem chewi131_taylor_norm_bound_of_gradient_ftc
    {H : Matrix n n ℝ} {gamma : ℝ} (hgamma : 0 ≤ gamma)
    {grad : EuclideanSpace ℝ n -> EuclideanSpace ℝ n}
    {hess : EuclideanSpace ℝ n ->
      EuclideanSpace ℝ n →L[ℝ] EuclideanSpace ℝ n}
    {x xNext xStar : EuclideanSpace ℝ n}
    (hgrad : ∀ t, t ∈ Set.uIcc (0 : ℝ) 1 ->
      HasFDerivAt grad
        (hess (hessianSegmentPoint xStar x t))
        (hessianSegmentPoint xStar x t))
    (hint : IntervalIntegrable
      (fun t : ℝ => hess (hessianSegmentPoint xStar x t) (x - xStar))
      MeasureTheory.volume (0 : ℝ) 1)
    (hgrad_star : grad xStar = 0)
    (hnewton :
      xNext =
        x -
          ((Matrix.toEuclideanLin (𝕜 := ℝ) (m := n) (n := n)).trans
            LinearMap.toContinuousLinearMap H⁻¹) (grad x))
    (hleft :
      ((Matrix.toEuclideanLin (𝕜 := ℝ) (m := n) (n := n)).trans
        LinearMap.toContinuousLinearMap H⁻¹) (hess x (x - xStar)) =
        x - xStar)
    (hlip : ∀ t, t ∈ Set.Icc (0 : ℝ) 1 ->
      ‖hess x - hess (hessianSegmentPoint xStar x t)‖ ≤
        gamma * (1 - t) * ‖x - xStar‖) :
    ‖xNext - xStar‖ ≤
      (gamma / 2) * ‖H⁻¹‖ * ‖x - xStar‖ ^ (2 : ℕ) := by
  let Hinv : EuclideanSpace ℝ n →L[ℝ] EuclideanSpace ℝ n :=
    (Matrix.toEuclideanLin (𝕜 := ℝ) (m := n) (n := n)).trans
      LinearMap.toContinuousLinearMap H⁻¹
  let remainder : ℝ -> EuclideanSpace ℝ n := fun t =>
    hess x (x - xStar) -
      hess (hessianSegmentPoint xStar x t) (x - xStar)
  have hrem_int : IntervalIntegrable remainder MeasureTheory.volume (0 : ℝ) 1 := by
    have hconst_int : IntervalIntegrable
        (fun _ : ℝ => hess x (x - xStar))
        MeasureTheory.volume (0 : ℝ) 1 :=
      intervalIntegrable_const
    exact hconst_int.sub hint
  have hidentity :
      xNext - xStar =
        ((Matrix.toEuclideanLin (𝕜 := ℝ) (m := n) (n := n)).trans
          LinearMap.toContinuousLinearMap H⁻¹)
          (∫ t in (0 : ℝ)..1, remainder t) := by
    simpa [Hinv, remainder] using
      chewi131_integral_remainder_identity_of_gradient_ftc
        (grad := grad) (hess := hess) (Hinv := Hinv)
        (x := x) (xNext := xNext) (xStar := xStar)
        hgrad hint hgrad_star (by simpa [Hinv] using hnewton)
        (by simpa [Hinv] using hleft)
  have hbound : ∀ t, t ∈ Set.Icc (0 : ℝ) 1 ->
      ‖remainder t‖ ≤ gamma * (1 - t) * ‖x - xStar‖ ^ (2 : ℕ) := by
    simpa [remainder] using
      chewi131_integral_remainder_pointwise_bound_of_hessian_lipschitz
        (hess := hess) (gamma := gamma) (x := x) (xStar := xStar)
        hlip
  exact
    chewi131_taylor_norm_bound_of_integral_remainder
      (H := H) (gamma := gamma) (x := x) (xNext := xNext)
      (xStar := xStar) (remainder := remainder) hgamma
      hrem_int hidentity hbound

/--
Chewi Theorem 13.1 Taylor norm estimate in matrix-shaped Hessian notation.
The Hessian oracle is related to matrices only at the current point and along
the `x_star -> x` segment.
-/
theorem chewi131_taylor_norm_bound_of_matrix_gradient_ftc
    {H : Matrix n n ℝ} {Hseg : ℝ -> Matrix n n ℝ}
    {gamma : ℝ} (hgamma : 0 ≤ gamma) (hdet : IsUnit H.det)
    {grad : EuclideanSpace ℝ n -> EuclideanSpace ℝ n}
    {hess : EuclideanSpace ℝ n ->
      EuclideanSpace ℝ n →L[ℝ] EuclideanSpace ℝ n}
    {x xNext xStar : EuclideanSpace ℝ n}
    (hgrad : ∀ t, t ∈ Set.uIcc (0 : ℝ) 1 ->
      HasFDerivAt grad
        (hess (hessianSegmentPoint xStar x t))
        (hessianSegmentPoint xStar x t))
    (hint : IntervalIntegrable
      (fun t : ℝ => hess (hessianSegmentPoint xStar x t) (x - xStar))
      MeasureTheory.volume (0 : ℝ) 1)
    (hgrad_star : grad xStar = 0)
    (hnewton :
      xNext =
        x -
          ((Matrix.toEuclideanLin (𝕜 := ℝ) (m := n) (n := n)).trans
            LinearMap.toContinuousLinearMap H⁻¹) (grad x))
    (hhess_x :
      hess x =
        ((Matrix.toEuclideanLin (𝕜 := ℝ) (m := n) (n := n)).trans
          LinearMap.toContinuousLinearMap H))
    (hhess_seg : ∀ t, t ∈ Set.Icc (0 : ℝ) 1 ->
      hess (hessianSegmentPoint xStar x t) =
        ((Matrix.toEuclideanLin (𝕜 := ℝ) (m := n) (n := n)).trans
          LinearMap.toContinuousLinearMap (Hseg t)))
    (hlip_matrix : ∀ t, t ∈ Set.Icc (0 : ℝ) 1 ->
      ‖H - Hseg t‖ ≤ gamma * (1 - t) * ‖x - xStar‖) :
    ‖xNext - xStar‖ ≤
      (gamma / 2) * ‖H⁻¹‖ * ‖x - xStar‖ ^ (2 : ℕ) := by
  have hleft :
      ((Matrix.toEuclideanLin (𝕜 := ℝ) (m := n) (n := n)).trans
        LinearMap.toContinuousLinearMap H⁻¹) (hess x (x - xStar)) =
        x - xStar :=
    chewi131_matrix_inverse_action_of_hessian_matrix
      (H := H) hdet (hess := hess) (x := x) (xStar := xStar) hhess_x
  have hlip :
      ∀ t, t ∈ Set.Icc (0 : ℝ) 1 ->
        ‖hess x - hess (hessianSegmentPoint xStar x t)‖ ≤
          gamma * (1 - t) * ‖x - xStar‖ :=
    chewi131_hessian_lipschitz_clm_of_matrix_lipschitz
      (H := H) (Hseg := Hseg) (gamma := gamma)
      (hess := hess) (x := x) (xStar := xStar)
      hhess_x hhess_seg hlip_matrix
  exact
    chewi131_taylor_norm_bound_of_gradient_ftc
      (H := H) (gamma := gamma) (x := x) (xNext := xNext)
      (xStar := xStar) (grad := grad) (hess := hess)
      hgamma hgrad hint hgrad_star hnewton hleft hlip

/--
Chewi Theorem 13.1 Taylor norm estimate with a concrete matrix Hessian oracle.
The Hessian continuous-linear-map oracle is `chewi131MatrixCLM (Hfun z)`;
continuity along a set containing the segment supplies the interval
integrability hypothesis.
-/
theorem chewi131_taylor_norm_bound_of_continuous_matrix_gradient_ftc
    {Hfun : EuclideanSpace ℝ n -> Matrix n n ℝ}
    {s : Set (EuclideanSpace ℝ n)}
    {gamma : ℝ} (hgamma : 0 ≤ gamma)
    {grad : EuclideanSpace ℝ n -> EuclideanSpace ℝ n}
    {x xNext xStar : EuclideanSpace ℝ n}
    (hdet : IsUnit (Hfun x).det)
    (hhess_cont : ContinuousOn (fun z => chewi131MatrixCLM (Hfun z)) s)
    (hseg : ∀ t, t ∈ Set.Icc (0 : ℝ) 1 ->
      hessianSegmentPoint xStar x t ∈ s)
    (hgrad : ∀ t, t ∈ Set.uIcc (0 : ℝ) 1 ->
      HasFDerivAt grad
        (chewi131MatrixCLM (Hfun (hessianSegmentPoint xStar x t)))
        (hessianSegmentPoint xStar x t))
    (hgrad_star : grad xStar = 0)
    (hnewton :
      xNext =
        x - chewi131MatrixCLM ((Hfun x)⁻¹) (grad x))
    (hlip_matrix : ∀ t, t ∈ Set.Icc (0 : ℝ) 1 ->
      ‖Hfun x - Hfun (hessianSegmentPoint xStar x t)‖ ≤
        gamma * (1 - t) * ‖x - xStar‖) :
    ‖xNext - xStar‖ ≤
      (gamma / 2) * ‖(Hfun x)⁻¹‖ * ‖x - xStar‖ ^ (2 : ℕ) := by
  let hess : EuclideanSpace ℝ n ->
      EuclideanSpace ℝ n →L[ℝ] EuclideanSpace ℝ n :=
    fun z => chewi131MatrixCLM (Hfun z)
  have hint : IntervalIntegrable
      (fun t : ℝ => hess (hessianSegmentPoint xStar x t) (x - xStar))
      MeasureTheory.volume (0 : ℝ) 1 :=
    hessianSegmentHessian_apply_intervalIntegrable_of_continuousOn
      (hess := hess) (s := s) (x := xStar) (y := x) (v := x - xStar)
      (by simpa [hess] using hhess_cont) hseg
  exact
    chewi131_taylor_norm_bound_of_matrix_gradient_ftc
      (H := Hfun x)
      (Hseg := fun t => Hfun (hessianSegmentPoint xStar x t))
      (gamma := gamma) (x := x) (xNext := xNext) (xStar := xStar)
      (grad := grad) (hess := hess) hgamma hdet
      (by simpa [hess] using hgrad) hint hgrad_star
      (by simpa [hess, chewi131MatrixCLM] using hnewton)
      (by rfl) (by intro t ht; rfl) hlip_matrix

/--
Chewi Theorem 13.1 one-step local quadratic convergence from gradient FTC and
Hessian-Lipschitz data.
-/
theorem chewi131_local_quadratic_step_of_gradient_ftc
    {Hstar H : Matrix n n ℝ} (hHstar : Hstar.IsHermitian)
    (hH : H.IsHermitian) {alpha gamma : ℝ} (halpha : 0 < alpha)
    (hgamma : 0 < gamma)
    {grad : EuclideanSpace ℝ n -> EuclideanSpace ℝ n}
    {hess : EuclideanSpace ℝ n ->
      EuclideanSpace ℝ n →L[ℝ] EuclideanSpace ℝ n}
    {x xNext xStar : EuclideanSpace ℝ n}
    (hlower : alpha • (1 : Matrix n n ℝ) ≤ Hstar)
    (hclose : ‖H - Hstar‖ ≤ gamma * ‖x - xStar‖)
    (hradius : ‖x - xStar‖ ≤ alpha / (2 * gamma))
    (hgrad : ∀ t, t ∈ Set.uIcc (0 : ℝ) 1 ->
      HasFDerivAt grad
        (hess (hessianSegmentPoint xStar x t))
        (hessianSegmentPoint xStar x t))
    (hint : IntervalIntegrable
      (fun t : ℝ => hess (hessianSegmentPoint xStar x t) (x - xStar))
      MeasureTheory.volume (0 : ℝ) 1)
    (hgrad_star : grad xStar = 0)
    (hnewton :
      xNext =
        x -
          ((Matrix.toEuclideanLin (𝕜 := ℝ) (m := n) (n := n)).trans
            LinearMap.toContinuousLinearMap H⁻¹) (grad x))
    (hleft :
      ((Matrix.toEuclideanLin (𝕜 := ℝ) (m := n) (n := n)).trans
        LinearMap.toContinuousLinearMap H⁻¹) (hess x (x - xStar)) =
        x - xStar)
    (hlip : ∀ t, t ∈ Set.Icc (0 : ℝ) 1 ->
      ‖hess x - hess (hessianSegmentPoint xStar x t)‖ ≤
        gamma * (1 - t) * ‖x - xStar‖) :
    ‖xNext - xStar‖ ≤
      (gamma / alpha) * ‖x - xStar‖ ^ (2 : ℕ) := by
  exact
    chewi131_local_quadratic_step_of_taylor_bound hHstar hH halpha hgamma
      hlower hclose hradius
      (chewi131_taylor_norm_bound_of_gradient_ftc
        (H := H) (gamma := gamma) (x := x) (xNext := xNext)
        (xStar := xStar) (grad := grad) (hess := hess)
        (le_of_lt hgamma) hgrad hint hgrad_star hnewton hleft hlip)

/--
Chewi Theorem 13.1 one-step local quadratic convergence in matrix-shaped
Hessian notation.
-/
theorem chewi131_local_quadratic_step_of_matrix_gradient_ftc
    {Hstar H : Matrix n n ℝ} {Hseg : ℝ -> Matrix n n ℝ}
    (hHstar : Hstar.IsHermitian) (hH : H.IsHermitian)
    {alpha gamma : ℝ} (halpha : 0 < alpha) (hgamma : 0 < gamma)
    (hdet : IsUnit H.det)
    {grad : EuclideanSpace ℝ n -> EuclideanSpace ℝ n}
    {hess : EuclideanSpace ℝ n ->
      EuclideanSpace ℝ n →L[ℝ] EuclideanSpace ℝ n}
    {x xNext xStar : EuclideanSpace ℝ n}
    (hlower : alpha • (1 : Matrix n n ℝ) ≤ Hstar)
    (hclose : ‖H - Hstar‖ ≤ gamma * ‖x - xStar‖)
    (hradius : ‖x - xStar‖ ≤ alpha / (2 * gamma))
    (hgrad : ∀ t, t ∈ Set.uIcc (0 : ℝ) 1 ->
      HasFDerivAt grad
        (hess (hessianSegmentPoint xStar x t))
        (hessianSegmentPoint xStar x t))
    (hint : IntervalIntegrable
      (fun t : ℝ => hess (hessianSegmentPoint xStar x t) (x - xStar))
      MeasureTheory.volume (0 : ℝ) 1)
    (hgrad_star : grad xStar = 0)
    (hnewton :
      xNext =
        x -
          ((Matrix.toEuclideanLin (𝕜 := ℝ) (m := n) (n := n)).trans
            LinearMap.toContinuousLinearMap H⁻¹) (grad x))
    (hhess_x :
      hess x =
        ((Matrix.toEuclideanLin (𝕜 := ℝ) (m := n) (n := n)).trans
          LinearMap.toContinuousLinearMap H))
    (hhess_seg : ∀ t, t ∈ Set.Icc (0 : ℝ) 1 ->
      hess (hessianSegmentPoint xStar x t) =
        ((Matrix.toEuclideanLin (𝕜 := ℝ) (m := n) (n := n)).trans
          LinearMap.toContinuousLinearMap (Hseg t)))
    (hlip_matrix : ∀ t, t ∈ Set.Icc (0 : ℝ) 1 ->
      ‖H - Hseg t‖ ≤ gamma * (1 - t) * ‖x - xStar‖) :
    ‖xNext - xStar‖ ≤
      (gamma / alpha) * ‖x - xStar‖ ^ (2 : ℕ) := by
  exact
    chewi131_local_quadratic_step_of_taylor_bound hHstar hH halpha hgamma
      hlower hclose hradius
      (chewi131_taylor_norm_bound_of_matrix_gradient_ftc
        (H := H) (Hseg := Hseg) (gamma := gamma)
        (x := x) (xNext := xNext) (xStar := xStar)
        (grad := grad) (hess := hess) (le_of_lt hgamma) hdet
        hgrad hint hgrad_star hnewton hhess_x hhess_seg hlip_matrix)

/--
Chewi Theorem 13.1 one-step matrix-gradient-FTC form with Hessian
invertibility derived from the local-radius hypothesis, matching the textbook
proof's `nabla^2 f(x_n) >= alpha / 2` argument.
-/
theorem chewi131_local_quadratic_step_of_matrix_gradient_ftc_of_radius
    {Hstar H : Matrix n n ℝ} {Hseg : ℝ -> Matrix n n ℝ}
    (hHstar : Hstar.IsHermitian) (hH : H.IsHermitian)
    {alpha gamma : ℝ} (halpha : 0 < alpha) (hgamma : 0 < gamma)
    {grad : EuclideanSpace ℝ n -> EuclideanSpace ℝ n}
    {hess : EuclideanSpace ℝ n ->
      EuclideanSpace ℝ n →L[ℝ] EuclideanSpace ℝ n}
    {x xNext xStar : EuclideanSpace ℝ n}
    (hlower : alpha • (1 : Matrix n n ℝ) ≤ Hstar)
    (hclose : ‖H - Hstar‖ ≤ gamma * ‖x - xStar‖)
    (hradius : ‖x - xStar‖ ≤ alpha / (2 * gamma))
    (hgrad : ∀ t, t ∈ Set.uIcc (0 : ℝ) 1 ->
      HasFDerivAt grad
        (hess (hessianSegmentPoint xStar x t))
        (hessianSegmentPoint xStar x t))
    (hint : IntervalIntegrable
      (fun t : ℝ => hess (hessianSegmentPoint xStar x t) (x - xStar))
      MeasureTheory.volume (0 : ℝ) 1)
    (hgrad_star : grad xStar = 0)
    (hnewton :
      xNext =
        x -
          ((Matrix.toEuclideanLin (𝕜 := ℝ) (m := n) (n := n)).trans
            LinearMap.toContinuousLinearMap H⁻¹) (grad x))
    (hhess_x :
      hess x =
        ((Matrix.toEuclideanLin (𝕜 := ℝ) (m := n) (n := n)).trans
          LinearMap.toContinuousLinearMap H))
    (hhess_seg : ∀ t, t ∈ Set.Icc (0 : ℝ) 1 ->
      hess (hessianSegmentPoint xStar x t) =
        ((Matrix.toEuclideanLin (𝕜 := ℝ) (m := n) (n := n)).trans
          LinearMap.toContinuousLinearMap (Hseg t)))
    (hlip_matrix : ∀ t, t ∈ Set.Icc (0 : ℝ) 1 ->
      ‖H - Hseg t‖ ≤ gamma * (1 - t) * ‖x - xStar‖) :
    ‖xNext - xStar‖ ≤
      (gamma / alpha) * ‖x - xStar‖ ^ (2 : ℕ) := by
  have hdet : IsUnit H.det :=
    chewi131_hessian_det_isUnit_of_radius hHstar hH halpha hgamma
      hlower hclose hradius
  exact
    chewi131_local_quadratic_step_of_matrix_gradient_ftc hHstar hH
      halpha hgamma hdet hlower hclose hradius hgrad hint hgrad_star
      hnewton hhess_x hhess_seg hlip_matrix

/--
Chewi Theorem 13.1 one-step local quadratic convergence with a concrete
continuous matrix Hessian oracle.  This is the theorem-facing form that keeps
only the Hessian matrix family `Hfun` and derives both interval integrability
and Hessian invertibility from the source hypotheses.
-/
theorem chewi131_local_quadratic_step_of_continuous_matrix_gradient_ftc_of_radius
    {Hstar : Matrix n n ℝ}
    {Hfun : EuclideanSpace ℝ n -> Matrix n n ℝ}
    {s : Set (EuclideanSpace ℝ n)}
    (hHstar : Hstar.IsHermitian) {alpha gamma : ℝ}
    (halpha : 0 < alpha) (hgamma : 0 < gamma)
    {grad : EuclideanSpace ℝ n -> EuclideanSpace ℝ n}
    {x xNext xStar : EuclideanSpace ℝ n}
    (hH : (Hfun x).IsHermitian)
    (hlower : alpha • (1 : Matrix n n ℝ) ≤ Hstar)
    (hclose : ‖Hfun x - Hstar‖ ≤ gamma * ‖x - xStar‖)
    (hradius : ‖x - xStar‖ ≤ alpha / (2 * gamma))
    (hhess_cont : ContinuousOn (fun z => chewi131MatrixCLM (Hfun z)) s)
    (hseg : ∀ t, t ∈ Set.Icc (0 : ℝ) 1 ->
      hessianSegmentPoint xStar x t ∈ s)
    (hgrad : ∀ t, t ∈ Set.uIcc (0 : ℝ) 1 ->
      HasFDerivAt grad
        (chewi131MatrixCLM (Hfun (hessianSegmentPoint xStar x t)))
        (hessianSegmentPoint xStar x t))
    (hgrad_star : grad xStar = 0)
    (hnewton :
      xNext =
        x - chewi131MatrixCLM ((Hfun x)⁻¹) (grad x))
    (hlip_matrix : ∀ t, t ∈ Set.Icc (0 : ℝ) 1 ->
      ‖Hfun x - Hfun (hessianSegmentPoint xStar x t)‖ ≤
        gamma * (1 - t) * ‖x - xStar‖) :
    ‖xNext - xStar‖ ≤
      (gamma / alpha) * ‖x - xStar‖ ^ (2 : ℕ) := by
  let hess : EuclideanSpace ℝ n ->
      EuclideanSpace ℝ n →L[ℝ] EuclideanSpace ℝ n :=
    fun z => chewi131MatrixCLM (Hfun z)
  have hint : IntervalIntegrable
      (fun t : ℝ => hess (hessianSegmentPoint xStar x t) (x - xStar))
      MeasureTheory.volume (0 : ℝ) 1 :=
    hessianSegmentHessian_apply_intervalIntegrable_of_continuousOn
      (hess := hess) (s := s) (x := xStar) (y := x) (v := x - xStar)
      (by simpa [hess] using hhess_cont) hseg
  exact
    chewi131_local_quadratic_step_of_matrix_gradient_ftc_of_radius
      (Hstar := Hstar) (H := Hfun x)
      (Hseg := fun t => Hfun (hessianSegmentPoint xStar x t))
      hHstar hH halpha hgamma hlower hclose hradius
      (by simpa [hess] using hgrad) hint hgrad_star
      (by simpa [hess, chewi131MatrixCLM] using hnewton)
      (by rfl) (by intro t ht; rfl) hlip_matrix

/--
Chewi Theorem 13.1 sequence recurrence from gradient FTC and Hessian-Lipschitz
data at each Newton iterate.
-/
theorem chewi131_local_quadratic_recurrence_of_gradient_ftc
    {Hstar : Matrix n n ℝ} {H : ℕ -> Matrix n n ℝ}
    (hHstar : Hstar.IsHermitian) (hH : ∀ k, (H k).IsHermitian)
    {alpha gamma : ℝ} (halpha : 0 < alpha) (hgamma : 0 < gamma)
    {grad : EuclideanSpace ℝ n -> EuclideanSpace ℝ n}
    {hess : EuclideanSpace ℝ n ->
      EuclideanSpace ℝ n →L[ℝ] EuclideanSpace ℝ n}
    {x : ℕ -> EuclideanSpace ℝ n} {xStar : EuclideanSpace ℝ n}
    (hlower : alpha • (1 : Matrix n n ℝ) ≤ Hstar)
    (hclose : ∀ k, ‖H k - Hstar‖ ≤ gamma * ‖x k - xStar‖)
    (hgrad : ∀ k t, t ∈ Set.uIcc (0 : ℝ) 1 ->
      HasFDerivAt grad
        (hess (hessianSegmentPoint xStar (x k) t))
        (hessianSegmentPoint xStar (x k) t))
    (hint : ∀ k, IntervalIntegrable
      (fun t : ℝ => hess (hessianSegmentPoint xStar (x k) t) (x k - xStar))
      MeasureTheory.volume (0 : ℝ) 1)
    (hgrad_star : grad xStar = 0)
    (hnewton : ∀ k,
      x (k + 1) =
        x k -
          ((Matrix.toEuclideanLin (𝕜 := ℝ) (m := n) (n := n)).trans
            LinearMap.toContinuousLinearMap (H k)⁻¹) (grad (x k)))
    (hleft : ∀ k,
      ((Matrix.toEuclideanLin (𝕜 := ℝ) (m := n) (n := n)).trans
        LinearMap.toContinuousLinearMap (H k)⁻¹) (hess (x k) (x k - xStar)) =
        x k - xStar)
    (hlip : ∀ k t, t ∈ Set.Icc (0 : ℝ) 1 ->
      ‖hess (x k) - hess (hessianSegmentPoint xStar (x k) t)‖ ≤
        gamma * (1 - t) * ‖x k - xStar‖)
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
    chewi131_taylor_norm_bound_of_gradient_ftc
      (H := H k) (gamma := gamma) (x := x k) (xNext := x (k + 1))
      (xStar := xStar) (grad := grad) (hess := hess)
      (le_of_lt hgamma) (hgrad k) (hint k) hgrad_star
      (hnewton k) (hleft k) (hlip k)

/--
Chewi Theorem 13.1 sequence recurrence in matrix-shaped Hessian notation.
-/
theorem chewi131_local_quadratic_recurrence_of_matrix_gradient_ftc
    {Hstar : Matrix n n ℝ} {H : ℕ -> Matrix n n ℝ}
    {Hseg : ℕ -> ℝ -> Matrix n n ℝ}
    (hHstar : Hstar.IsHermitian) (hH : ∀ k, (H k).IsHermitian)
    {alpha gamma : ℝ} (halpha : 0 < alpha) (hgamma : 0 < gamma)
    (hdet : ∀ k, IsUnit (H k).det)
    {grad : EuclideanSpace ℝ n -> EuclideanSpace ℝ n}
    {hess : EuclideanSpace ℝ n ->
      EuclideanSpace ℝ n →L[ℝ] EuclideanSpace ℝ n}
    {x : ℕ -> EuclideanSpace ℝ n} {xStar : EuclideanSpace ℝ n}
    (hlower : alpha • (1 : Matrix n n ℝ) ≤ Hstar)
    (hclose : ∀ k, ‖H k - Hstar‖ ≤ gamma * ‖x k - xStar‖)
    (hgrad : ∀ k t, t ∈ Set.uIcc (0 : ℝ) 1 ->
      HasFDerivAt grad
        (hess (hessianSegmentPoint xStar (x k) t))
        (hessianSegmentPoint xStar (x k) t))
    (hint : ∀ k, IntervalIntegrable
      (fun t : ℝ => hess (hessianSegmentPoint xStar (x k) t) (x k - xStar))
      MeasureTheory.volume (0 : ℝ) 1)
    (hgrad_star : grad xStar = 0)
    (hnewton : ∀ k,
      x (k + 1) =
        x k -
          ((Matrix.toEuclideanLin (𝕜 := ℝ) (m := n) (n := n)).trans
            LinearMap.toContinuousLinearMap (H k)⁻¹) (grad (x k)))
    (hhess_x : ∀ k,
      hess (x k) =
        ((Matrix.toEuclideanLin (𝕜 := ℝ) (m := n) (n := n)).trans
          LinearMap.toContinuousLinearMap (H k)))
    (hhess_seg : ∀ k t, t ∈ Set.Icc (0 : ℝ) 1 ->
      hess (hessianSegmentPoint xStar (x k) t) =
        ((Matrix.toEuclideanLin (𝕜 := ℝ) (m := n) (n := n)).trans
          LinearMap.toContinuousLinearMap (Hseg k t)))
    (hlip_matrix : ∀ k t, t ∈ Set.Icc (0 : ℝ) 1 ->
      ‖H k - Hseg k t‖ ≤ gamma * (1 - t) * ‖x k - xStar‖)
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
    chewi131_taylor_norm_bound_of_matrix_gradient_ftc
      (H := H k) (Hseg := Hseg k) (gamma := gamma)
      (x := x k) (xNext := x (k + 1)) (xStar := xStar)
      (grad := grad) (hess := hess) (le_of_lt hgamma) (hdet k)
      (hgrad k) (hint k) hgrad_star (hnewton k) (hhess_x k)
      (hhess_seg k) (hlip_matrix k)

/--
Chewi Theorem 13.1 sequence recurrence in matrix-shaped Hessian notation,
with invertibility derived inside the radius induction.  This is closer to the
textbook proof than requiring a separate global `IsUnit (H k).det` assumption.
-/
theorem chewi131_local_quadratic_recurrence_of_matrix_gradient_ftc_of_radius
    {Hstar : Matrix n n ℝ} {H : ℕ -> Matrix n n ℝ}
    {Hseg : ℕ -> ℝ -> Matrix n n ℝ}
    (hHstar : Hstar.IsHermitian) (hH : ∀ k, (H k).IsHermitian)
    {alpha gamma : ℝ} (halpha : 0 < alpha) (hgamma : 0 < gamma)
    {grad : EuclideanSpace ℝ n -> EuclideanSpace ℝ n}
    {hess : EuclideanSpace ℝ n ->
      EuclideanSpace ℝ n →L[ℝ] EuclideanSpace ℝ n}
    {x : ℕ -> EuclideanSpace ℝ n} {xStar : EuclideanSpace ℝ n}
    (hlower : alpha • (1 : Matrix n n ℝ) ≤ Hstar)
    (hclose : ∀ k, ‖H k - Hstar‖ ≤ gamma * ‖x k - xStar‖)
    (hgrad : ∀ k t, t ∈ Set.uIcc (0 : ℝ) 1 ->
      HasFDerivAt grad
        (hess (hessianSegmentPoint xStar (x k) t))
        (hessianSegmentPoint xStar (x k) t))
    (hint : ∀ k, IntervalIntegrable
      (fun t : ℝ => hess (hessianSegmentPoint xStar (x k) t) (x k - xStar))
      MeasureTheory.volume (0 : ℝ) 1)
    (hgrad_star : grad xStar = 0)
    (hnewton : ∀ k,
      x (k + 1) =
        x k -
          ((Matrix.toEuclideanLin (𝕜 := ℝ) (m := n) (n := n)).trans
            LinearMap.toContinuousLinearMap (H k)⁻¹) (grad (x k)))
    (hhess_x : ∀ k,
      hess (x k) =
        ((Matrix.toEuclideanLin (𝕜 := ℝ) (m := n) (n := n)).trans
          LinearMap.toContinuousLinearMap (H k)))
    (hhess_seg : ∀ k t, t ∈ Set.Icc (0 : ℝ) 1 ->
      hess (hessianSegmentPoint xStar (x k) t) =
        ((Matrix.toEuclideanLin (𝕜 := ℝ) (m := n) (n := n)).trans
          LinearMap.toContinuousLinearMap (Hseg k t)))
    (hlip_matrix : ∀ k t, t ∈ Set.Icc (0 : ℝ) 1 ->
      ‖H k - Hseg k t‖ ≤ gamma * (1 - t) * ‖x k - xStar‖)
    (hinit : ‖x 0 - xStar‖ ≤ alpha / (2 * gamma)) :
    ∀ k,
      ‖x (k + 1) - xStar‖ ≤
          (gamma / alpha) * ‖x k - xStar‖ ^ (2 : ℕ) ∧
        ‖x (k + 1) - xStar‖ ≤ (1 / 2) * ‖x k - xStar‖ := by
  refine
    chewi131_local_quadratic_recurrence_of_conditional_taylor_bound hHstar hH
      halpha hgamma hlower hclose ?_ hinit
  intro k hradius
  have hdet : IsUnit (H k).det :=
    chewi131_hessian_det_isUnit_of_radius hHstar (hH k) halpha hgamma
      hlower (hclose k) hradius
  exact
    chewi131_taylor_norm_bound_of_matrix_gradient_ftc
      (H := H k) (Hseg := Hseg k) (gamma := gamma)
      (x := x k) (xNext := x (k + 1)) (xStar := xStar)
      (grad := grad) (hess := hess) (le_of_lt hgamma) hdet
      (hgrad k) (hint k) hgrad_star (hnewton k) (hhess_x k)
      (hhess_seg k) (hlip_matrix k)

/--
Chewi Theorem 13.1 sequence recurrence with a concrete continuous matrix
Hessian oracle.  The interval-integrability hypotheses are derived from
continuity of `z ↦ chewi131MatrixCLM (Hfun z)` on a set containing every
`x_star -> x_k` segment, and Hessian invertibility is derived inside the
radius induction.
-/
theorem chewi131_local_quadratic_recurrence_of_continuous_matrix_gradient_ftc_of_radius
    {Hstar : Matrix n n ℝ}
    {Hfun : EuclideanSpace ℝ n -> Matrix n n ℝ}
    {s : Set (EuclideanSpace ℝ n)}
    (hHstar : Hstar.IsHermitian)
    {alpha gamma : ℝ} (halpha : 0 < alpha) (hgamma : 0 < gamma)
    {grad : EuclideanSpace ℝ n -> EuclideanSpace ℝ n}
    {x : ℕ -> EuclideanSpace ℝ n} {xStar : EuclideanSpace ℝ n}
    (hH : ∀ k, (Hfun (x k)).IsHermitian)
    (hlower : alpha • (1 : Matrix n n ℝ) ≤ Hstar)
    (hclose : ∀ k, ‖Hfun (x k) - Hstar‖ ≤ gamma * ‖x k - xStar‖)
    (hhess_cont : ContinuousOn (fun z => chewi131MatrixCLM (Hfun z)) s)
    (hseg : ∀ k t, t ∈ Set.Icc (0 : ℝ) 1 ->
      hessianSegmentPoint xStar (x k) t ∈ s)
    (hgrad : ∀ k t, t ∈ Set.uIcc (0 : ℝ) 1 ->
      HasFDerivAt grad
        (chewi131MatrixCLM (Hfun (hessianSegmentPoint xStar (x k) t)))
        (hessianSegmentPoint xStar (x k) t))
    (hgrad_star : grad xStar = 0)
    (hnewton : ∀ k,
      x (k + 1) =
        x k - chewi131MatrixCLM ((Hfun (x k))⁻¹) (grad (x k)))
    (hlip_matrix : ∀ k t, t ∈ Set.Icc (0 : ℝ) 1 ->
      ‖Hfun (x k) - Hfun (hessianSegmentPoint xStar (x k) t)‖ ≤
        gamma * (1 - t) * ‖x k - xStar‖)
    (hinit : ‖x 0 - xStar‖ ≤ alpha / (2 * gamma)) :
    ∀ k,
      ‖x (k + 1) - xStar‖ ≤
          (gamma / alpha) * ‖x k - xStar‖ ^ (2 : ℕ) ∧
        ‖x (k + 1) - xStar‖ ≤ (1 / 2) * ‖x k - xStar‖ := by
  let hess : EuclideanSpace ℝ n ->
      EuclideanSpace ℝ n →L[ℝ] EuclideanSpace ℝ n :=
    fun z => chewi131MatrixCLM (Hfun z)
  have hint : ∀ k, IntervalIntegrable
      (fun t : ℝ => hess (hessianSegmentPoint xStar (x k) t) (x k - xStar))
      MeasureTheory.volume (0 : ℝ) 1 := by
    intro k
    exact
      hessianSegmentHessian_apply_intervalIntegrable_of_continuousOn
        (hess := hess) (s := s) (x := xStar) (y := x k)
        (v := x k - xStar) (by simpa [hess] using hhess_cont) (hseg k)
  exact
    chewi131_local_quadratic_recurrence_of_matrix_gradient_ftc_of_radius
      (Hstar := Hstar) (H := fun k => Hfun (x k))
      (Hseg := fun k t => Hfun (hessianSegmentPoint xStar (x k) t))
      hHstar hH halpha hgamma hlower hclose
      (by simpa [hess] using hgrad) hint hgrad_star
      (by intro k; simpa [hess, chewi131MatrixCLM] using hnewton k)
      (by intro k; rfl) (by intro k t ht; rfl) hlip_matrix hinit

end Optimization
end StatInference
