import StatInference.Optimization.ASGDGeneral
import StatInference.Optimization.Theorem131Taylor

/-!
# Chewi Theorem 12.8, ASGD Source Taylor Remainder

This module connects the Chewi 12.8 ASGD Taylor/Hessian residual
`zeta_k = grad f(theta_k) - Hess f(thetaStar) (theta_k - thetaStar)` to the
general ASGD residual theorem.  The deterministic layer is a star-Hessian
linearization estimate from the segment-gradient FTC and a Hessian-Lipschitz
bound; the stochastic layer packages the resulting pointwise quadratic bound
for the `ASGDGeneral` source theorem.
-/

open Filter MeasureTheory ProbabilityTheory
open StatInference.AsymptoticStatistics
open scoped intervalIntegral BigOperators Topology

namespace StatInference
namespace Optimization

section StarHessian

variable {E : Type*} [NormedAddCommGroup E] [InnerProductSpace ℝ E]

/--
Star-Hessian Taylor linearization bound.  If the gradient has derivative
`hess` along the segment from `xStar` to `x`, `grad xStar = 0`, and the
Hessian is Lipschitz from the star point along that segment, then
`grad x - hess xStar (x - xStar)` is quadratic in `x - xStar`.
-/
theorem chewi128_starHessian_linearization_norm_le_of_gradient_ftc
    [CompleteSpace E]
    {grad : E -> E} {hess : E -> E →L[ℝ] E}
    {L : ℝ}
    {x xStar : E}
    (hgrad : ∀ t, t ∈ Set.uIcc (0 : ℝ) 1 ->
      HasFDerivAt grad
        (hess (hessianSegmentPoint xStar x t))
        (hessianSegmentPoint xStar x t))
    (hint : IntervalIntegrable
      (fun t : ℝ => hess (hessianSegmentPoint xStar x t) (x - xStar))
      MeasureTheory.volume (0 : ℝ) 1)
    (hgrad_star : grad xStar = 0)
    (hlip : ∀ t, t ∈ Set.Icc (0 : ℝ) 1 ->
      ‖hess (hessianSegmentPoint xStar x t) - hess xStar‖ ≤
        L * t * ‖x - xStar‖) :
    ‖grad x - hess xStar (x - xStar)‖ ≤
      (L / 2) * ‖x - xStar‖ ^ (2 : ℕ) := by
  let d : E := x - xStar
  let remainder : ℝ -> E := fun t =>
    hess (hessianSegmentPoint xStar x t) d - hess xStar d
  have hconst_int : IntervalIntegrable (fun _ : ℝ => hess xStar d)
      MeasureTheory.volume (0 : ℝ) 1 :=
    intervalIntegrable_const
  have hFTC :
      (∫ t in (0 : ℝ)..1,
          hess (hessianSegmentPoint xStar x t) d) =
        grad x - grad xStar := by
    simpa [d] using
      hessianSegmentGradient_integral_eq_sub_of_hasFDerivAt
        (grad := grad) (hess := hess) (x := xStar) (y := x)
        hgrad (by simpa [d] using hint)
  have hidentity :
      (∫ t in (0 : ℝ)..1, remainder t) =
        grad x - hess xStar d := by
    rw [show (∫ t in (0 : ℝ)..1, remainder t) =
        (∫ t in (0 : ℝ)..1,
            hess (hessianSegmentPoint xStar x t) d) -
          ∫ t in (0 : ℝ)..1, hess xStar d by
      exact intervalIntegral.integral_sub
        (by simpa [d] using hint) hconst_int]
    rw [hFTC]
    simp [hgrad_star]
  let e2 : ℝ := ‖x - xStar‖ ^ (2 : ℕ)
  have hscalar_int :
      IntervalIntegrable (fun t : ℝ => L * t * e2)
        MeasureTheory.volume (0 : ℝ) 1 := by
    have hcont : Continuous (fun t : ℝ => L * t * e2) := by
      continuity
    exact hcont.intervalIntegrable (0 : ℝ) 1
  have hbound_ae :
      ∀ᵐ t ∂MeasureTheory.volume,
        t ∈ Set.Ioc (0 : ℝ) 1 ->
          ‖remainder t‖ ≤ L * t * e2 := by
    exact Filter.Eventually.of_forall fun t ht => by
      have htIcc : t ∈ Set.Icc (0 : ℝ) 1 := ⟨le_of_lt ht.1, ht.2⟩
      have hpoint := hlip t htIcc
      calc
        ‖remainder t‖ =
            ‖(hess (hessianSegmentPoint xStar x t) - hess xStar) d‖ := by
              simp [remainder, d]
        _ ≤ ‖hess (hessianSegmentPoint xStar x t) - hess xStar‖ * ‖d‖ :=
            (hess (hessianSegmentPoint xStar x t) - hess xStar).le_opNorm d
        _ ≤ (L * t * ‖x - xStar‖) * ‖d‖ :=
            mul_le_mul_of_nonneg_right hpoint (norm_nonneg d)
        _ = L * t * e2 := by
            simp [d, e2]
            ring
  have hintegral_bound :
      ‖∫ t in (0 : ℝ)..1, remainder t‖ ≤
        ∫ t in (0 : ℝ)..1, L * t * e2 :=
    intervalIntegral.norm_integral_le_of_norm_le zero_le_one hbound_ae
      hscalar_int
  have hint_id :
      (∫ t in (0 : ℝ)..1, t) = (1 / 2 : ℝ) := by
    have hint_t : IntervalIntegrable (fun t : ℝ => t)
        MeasureTheory.volume (0 : ℝ) 1 :=
      continuous_id.intervalIntegrable (0 : ℝ) 1
    let primitive : ℝ -> ℝ := fun s => s ^ (2 : ℕ) / 2
    have hderiv : ∀ t, t ∈ Set.uIcc (0 : ℝ) 1 ->
        HasDerivAt primitive t t := by
      intro t _ht
      have hraw := ((hasDerivAt_id t).pow (2 : ℕ)).div_const 2
      convert hraw using 1
      simp
    have hFTC_id :=
      intervalIntegral.integral_eq_sub_of_hasDerivAt hderiv hint_t
    norm_num [primitive] at hFTC_id ⊢
  have hscalar_eval :
      (∫ t in (0 : ℝ)..1, L * t * e2) = (L / 2) * e2 := by
    have hfun :
        (fun t : ℝ => L * t * e2) = fun t : ℝ => (L * e2) * t := by
      ext t
      ring
    rw [hfun, intervalIntegral.integral_const_mul, hint_id]
    ring
  calc
    ‖grad x - hess xStar (x - xStar)‖ =
        ‖grad x - hess xStar d‖ := by simp [d]
    _ = ‖∫ t in (0 : ℝ)..1, remainder t‖ := by rw [hidentity]
    _ ≤ ∫ t in (0 : ℝ)..1, L * t * e2 := hintegral_bound
    _ = (L / 2) * ‖x - xStar‖ ^ (2 : ℕ) := by
        simp [hscalar_eval, e2]

/--
Pointwise stochastic version of the star-Hessian linearization bound for the
Chewi 12.8 residual sequence.
-/
theorem chewi128_zeta_pointwise_quadratic_of_starHessian_linearization
    {Ω : Type*} [MeasurableSpace Ω] {P : Measure Ω}
    [CompleteSpace E]
    {grad : E -> E} {hess : E -> E →L[ℝ] E}
    (theta : ℕ -> Ω -> E) (thetaStar : E)
    (zeta : ℕ -> Ω -> E) (L : ℝ)
    (hzeta_eq : ∀ k,
      (fun ω => zeta k ω) =ᵐ[P]
        fun ω => grad (theta k ω) -
          hess thetaStar (theta k ω - thetaStar))
    (hgrad : ∀ k ω t, t ∈ Set.uIcc (0 : ℝ) 1 ->
      HasFDerivAt grad
        (hess (hessianSegmentPoint thetaStar (theta k ω) t))
        (hessianSegmentPoint thetaStar (theta k ω) t))
    (hint : ∀ k ω,
      IntervalIntegrable
        (fun t : ℝ =>
          hess (hessianSegmentPoint thetaStar (theta k ω) t)
            (theta k ω - thetaStar))
        MeasureTheory.volume (0 : ℝ) 1)
    (hgrad_star : grad thetaStar = 0)
    (hlip : ∀ k ω t, t ∈ Set.Icc (0 : ℝ) 1 ->
      ‖hess (hessianSegmentPoint thetaStar (theta k ω) t) - hess thetaStar‖ ≤
        L * t * ‖theta k ω - thetaStar‖) :
    ∀ k,
      (fun ω => ‖zeta k ω‖) ≤ᵐ[P]
        fun ω => (L / 2) * ‖theta k ω - thetaStar‖ ^ (2 : ℕ) := by
  intro k
  filter_upwards [hzeta_eq k] with ω hω
  calc
    ‖zeta k ω‖ =
        ‖grad (theta k ω) -
            hess thetaStar (theta k ω - thetaStar)‖ := by rw [hω]
    _ ≤ (L / 2) * ‖theta k ω - thetaStar‖ ^ (2 : ℕ) :=
        chewi128_starHessian_linearization_norm_le_of_gradient_ftc
          (grad := grad) (hess := hess) (L := L)
          (x := theta k ω) (xStar := thetaStar)
          (fun t ht => hgrad k ω t ht) (hint k ω) hgrad_star
          (fun t ht => hlip k ω t ht)

/--
Chewi 12.8 ASGD residual theorem from a star-Hessian Taylor linearization and
the source second-moment rate.  This is the source-shaped wrapper for
`zeta_k = grad f(theta_k) - Hess f(thetaStar)(theta_k - thetaStar)`.
-/
theorem chewi128ASGDZetaContribution_tendstoInMeasure_zero_of_starHessian_linearization_moment_rate_and_gamma_gt_half
    {Ω : Type*} [MeasurableSpace Ω] {P : Measure Ω}
    [IsFiniteMeasure P] [CompleteSpace E]
    {grad : E -> E} {hess : E -> E →L[ℝ] E}
    (A Ainv : E →L[ℝ] E) (h : ℕ -> ℝ)
    (theta : ℕ -> Ω -> E) (thetaStar : E)
    (zeta : ℕ -> Ω -> E) (K L Ctheta gamma : ℝ)
    (hK_nonneg : 0 ≤ K)
    (hL_nonneg : 0 ≤ L)
    (hCtheta_nonneg : 0 ≤ Ctheta)
    (hgamma_half : (1 : ℝ) / 2 < gamma)
    (hgamma_lt_one : gamma < 1)
    (hA_eq : A = hess thetaStar)
    (hcoeff_bound : ∀ N k, k ∈ Finset.Ico 1 N ->
      ‖chewi123SourceNoiseCoefficient A h k N - Ainv‖ ≤ K)
    (hzeta_int : ∀ k, Integrable (fun ω => ‖zeta k ω‖) P)
    (htheta_sq_int :
      ∀ k, Integrable (fun ω => ‖theta k ω - thetaStar‖ ^ (2 : ℕ)) P)
    (hZetaContribution_int :
      ∀ N,
        Integrable
          (fun ω => ‖chewi128ASGDZetaContribution A Ainv h zeta N ω‖) P)
    (hzeta_eq : ∀ k,
      (fun ω => zeta k ω) =ᵐ[P]
        fun ω => grad (theta k ω) -
          A (theta k ω - thetaStar))
    (hgrad : ∀ k ω t, t ∈ Set.uIcc (0 : ℝ) 1 ->
      HasFDerivAt grad
        (hess (hessianSegmentPoint thetaStar (theta k ω) t))
        (hessianSegmentPoint thetaStar (theta k ω) t))
    (hint : ∀ k ω,
      IntervalIntegrable
        (fun t : ℝ =>
          hess (hessianSegmentPoint thetaStar (theta k ω) t)
            (theta k ω - thetaStar))
        MeasureTheory.volume (0 : ℝ) 1)
    (hgrad_star : grad thetaStar = 0)
    (hlip : ∀ k ω t, t ∈ Set.Icc (0 : ℝ) 1 ->
      ‖hess (hessianSegmentPoint thetaStar (theta k ω) t) - hess thetaStar‖ ≤
        L * t * ‖theta k ω - thetaStar‖)
    (hmoment_rate :
      ∀ k, ∫ ω, ‖theta k ω - thetaStar‖ ^ (2 : ℕ) ∂P ≤
        Ctheta * (((k + 1 : ℕ) : ℝ) ^ (-gamma))) :
    TendstoInMeasure P
      (fun N ω => chewi128ASGDZetaContribution A Ainv h zeta N ω)
      atTop (fun _ => 0) := by
  let delta : ℕ -> Ω -> E := fun k ω => theta k ω - thetaStar
  have hzeta_eq_star : ∀ k,
      (fun ω => zeta k ω) =ᵐ[P]
        fun ω => grad (theta k ω) -
          hess thetaStar (theta k ω - thetaStar) := by
    intro k
    filter_upwards [hzeta_eq k] with ω hω
    simpa [hA_eq] using hω
  have hpoint :
      ∀ k,
        (fun ω => ‖zeta k ω‖) ≤ᵐ[P]
          fun ω => (L / 2) * ‖delta k ω‖ ^ (2 : ℕ) := by
    intro k
    simpa [delta] using
      chewi128_zeta_pointwise_quadratic_of_starHessian_linearization
        (theta := theta) (thetaStar := thetaStar) (zeta := zeta)
        (L := L) hzeta_eq_star hgrad hint hgrad_star hlip k
  have hC0_nonneg : 0 ≤ L / 2 :=
    div_nonneg hL_nonneg (by norm_num : (0 : ℝ) ≤ 2)
  refine
    chewi128ASGDZetaContribution_tendstoInMeasure_zero_of_pointwise_quadratic_moment_rate_and_gamma_gt_half
      A Ainv h zeta delta K (L / 2) Ctheta gamma
      hK_nonneg hC0_nonneg hCtheta_nonneg hgamma_half hgamma_lt_one
      hcoeff_bound hzeta_int ?_ hZetaContribution_int hpoint ?_
  · intro k
    simpa [delta] using htheta_sq_int k
  · intro k
    simpa [delta] using hmoment_rate k

end StarHessian

end Optimization
end StatInference
