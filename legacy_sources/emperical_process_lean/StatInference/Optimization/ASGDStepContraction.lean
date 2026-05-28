import StatInference.Optimization.ASGDL2Remainder
import StatInference.Optimization.AppendixA

/-!
# Chewi Chapter 12 ASGD Step Contractions

This module bridges the finite-dimensional matrix spectral contraction from
Appendix A to the continuous-linear-map step map used in the quadratic ASGD
formalization of Chewi Theorem 12.3.
-/

open Matrix
open scoped MatrixOrder Matrix.Norms.L2Operator

namespace StatInference
namespace Optimization

open Filter MeasureTheory ProbabilityTheory
open StatInference.AsymptoticStatistics

variable {n : Type*} [Fintype n] [DecidableEq n]

/-- The Euclidean continuous linear map induced by a real square matrix. -/
noncomputable abbrev chewi123MatrixCLM (A : Matrix n n ℝ) :
    EuclideanSpace ℝ n →L[ℝ] EuclideanSpace ℝ n :=
  Matrix.toEuclideanCLM (𝕜 := ℝ) A

/--
A scalar power-step gate for Chewi's `h_m = m^{-gamma}` schedule.  For every
`m >= 2`, a constant bounded by `2^gamma` satisfies the one-step product gate
`c h_m <= 1`.
-/
theorem chewi125PowerStep_mul_le_one_of_le_two_rpow
    {c gamma : ℝ} (hgamma_nonneg : 0 ≤ gamma) {m : ℕ} (hm : 2 ≤ m)
    (hc : c ≤ (2 : ℝ) ^ gamma) :
    c * chewi125PowerStep gamma m ≤ 1 := by
  have hmpos : 0 < m := by omega
  have hstep_nonneg : 0 ≤ chewi125PowerStep gamma m :=
    le_of_lt (chewi125PowerStep_pos gamma hmpos)
  have htwo_step :
      chewi125PowerStep gamma m ≤ chewi125PowerStep gamma 2 :=
    chewi125PowerStep_antitone_of_le hgamma_nonneg (m := 2) (n := m)
      (by omega) hm
  have htwo_pow_nonneg : 0 ≤ (2 : ℝ) ^ gamma :=
    Real.rpow_nonneg (by norm_num) gamma
  calc
    c * chewi125PowerStep gamma m
        ≤ (2 : ℝ) ^ gamma * chewi125PowerStep gamma m :=
          mul_le_mul_of_nonneg_right hc hstep_nonneg
    _ ≤ (2 : ℝ) ^ gamma * chewi125PowerStep gamma 2 :=
          mul_le_mul_of_nonneg_left htwo_step htwo_pow_nonneg
    _ = 1 := by
          rw [chewi125PowerStep_of_pos gamma (by omega)]
          change (2 : ℝ) ^ gamma * (2 : ℝ) ^ (-gamma) = 1
          rw [← Real.rpow_add (by norm_num : 0 < (2 : ℝ))]
          ring_nf
          simp

/--
The Euclidean continuous-linear-map bridge sends the nonsingular matrix
inverse to a left inverse whenever the matrix is coercive in Loewner order.
-/
theorem chewi123MatrixCLM_inv_mul_self_eq_one_of_pos_loewner
    {A : Matrix n n ℝ} (hA : A.IsHermitian) {alpha : ℝ}
    (halpha : 0 < alpha)
    (hlower : alpha • (1 : Matrix n n ℝ) ≤ A) :
    chewi123MatrixCLM A⁻¹ * chewi123MatrixCLM A = 1 := by
  have hA_posDef : A.PosDef :=
    chewiA5_posDef_of_pos_scalar_one_le hA halpha hlower
  have hdet : IsUnit A.det :=
    (Matrix.isUnit_iff_isUnit_det A).mp hA_posDef.isUnit
  have hmul : A⁻¹ * A = 1 := Matrix.nonsing_inv_mul A hdet
  calc
    chewi123MatrixCLM A⁻¹ * chewi123MatrixCLM A
        = chewi123MatrixCLM (A⁻¹ * A) := by
            simp [chewi123MatrixCLM]
    _ = 1 := by
            simp [hmul, chewi123MatrixCLM]

/--
Matrix-to-ASGD bridge for Chewi Theorem 12.3.  The spectral Loewner step-size
gate from Appendix A supplies the exact continuous-linear-map contraction
hypothesis used by the quadratic ASGD recurrence.
-/
theorem chewi123QuadraticStepMap_matrixCLM_norm_le_one_sub_mul_of_loewner_bounds
    {A : Matrix n n ℝ} (hA : A.IsHermitian) {alpha beta h : ℝ}
    (hh_nonneg : 0 ≤ h)
    (halpha_step : alpha * h ≤ 1)
    (hbeta_step : beta * h ≤ 1)
    (hlower : alpha • (1 : Matrix n n ℝ) ≤ A)
    (hupper : A ≤ beta • (1 : Matrix n n ℝ)) :
    ‖chewi123QuadraticStepMap h (chewi123MatrixCLM A)‖ ≤
      1 - alpha * h := by
  have hmatrix :
      ‖(1 : Matrix n n ℝ) - h • A‖ ≤ 1 - alpha * h :=
    chewiA5_l2_opNorm_one_sub_smul_le_one_sub_mul_of_loewner_bounds
      hA hh_nonneg halpha_step hbeta_step hlower hupper
  rw [← Matrix.l2_opNorm_toEuclideanCLM] at hmatrix
  have hstep_eq :
      chewi123QuadraticStepMap h (chewi123MatrixCLM A) =
        chewi123MatrixCLM ((1 : Matrix n n ℝ) - h • A) := by
    change
      ContinuousLinearMap.id ℝ (EuclideanSpace ℝ n) -
          h • Matrix.toEuclideanCLM (𝕜 := ℝ) A =
        Matrix.toEuclideanCLM (𝕜 := ℝ) ((1 : Matrix n n ℝ) - h • A)
    rw [show ContinuousLinearMap.id ℝ (EuclideanSpace ℝ n) =
        (1 : EuclideanSpace ℝ n →L[ℝ] EuclideanSpace ℝ n) by
          ext x
          rfl]
    simp
  simpa [hstep_eq, chewi123MatrixCLM] using hmatrix

/--
One-based Chewi power-step version of the matrix-to-ASGD contraction bridge.
This is the exact `hstep` hypothesis shape consumed by the quadratic ASGD
limit packages.
-/
theorem chewi125QuadraticStepMap_matrixCLM_hstep_of_loewner_bounds
    {A : Matrix n n ℝ} (hA : A.IsHermitian) {alpha beta gamma : ℝ}
    (halpha_step : ∀ m, 2 ≤ m ->
      alpha * chewi125PowerStep gamma m ≤ 1)
    (hbeta_step : ∀ m, 2 ≤ m ->
      beta * chewi125PowerStep gamma m ≤ 1)
    (hlower : alpha • (1 : Matrix n n ℝ) ≤ A)
    (hupper : A ≤ beta • (1 : Matrix n n ℝ)) :
    ∀ m, 2 ≤ m ->
      ‖chewi123QuadraticStepMap (chewi125PowerStep gamma m)
          (chewi123MatrixCLM A)‖ ≤
        1 - alpha * chewi125PowerStep gamma m := by
  intro m hm
  exact
    chewi123QuadraticStepMap_matrixCLM_norm_le_one_sub_mul_of_loewner_bounds
      hA (le_of_lt (chewi125PowerStep_pos gamma (by omega)))
      (halpha_step m hm) (hbeta_step m hm) hlower hupper

/--
Source-shaped power-step version of the matrix-to-ASGD contraction bridge.
The two scalar inequalities `alpha <= 2^gamma` and `beta <= 2^gamma` discharge
the all-iteration step-size gates in the Loewner contraction theorem.
-/
theorem chewi125QuadraticStepMap_matrixCLM_hstep_of_loewner_bounds_and_le_two_rpow
    {A : Matrix n n ℝ} (hA : A.IsHermitian) {alpha beta gamma : ℝ}
    (hgamma_nonneg : 0 ≤ gamma)
    (halpha_le_two : alpha ≤ (2 : ℝ) ^ gamma)
    (hbeta_le_two : beta ≤ (2 : ℝ) ^ gamma)
    (hlower : alpha • (1 : Matrix n n ℝ) ≤ A)
    (hupper : A ≤ beta • (1 : Matrix n n ℝ)) :
    ∀ m, 2 ≤ m ->
      ‖chewi123QuadraticStepMap (chewi125PowerStep gamma m)
          (chewi123MatrixCLM A)‖ ≤
        1 - alpha * chewi125PowerStep gamma m := by
  refine
    chewi125QuadraticStepMap_matrixCLM_hstep_of_loewner_bounds hA
      ?_ ?_ hlower hupper
  · intro m hm
    exact chewi125PowerStep_mul_le_one_of_le_two_rpow
      hgamma_nonneg hm halpha_le_two
  · intro m hm
    exact chewi125PowerStep_mul_le_one_of_le_two_rpow
      hgamma_nonneg hm hbeta_le_two

/--
Finite-dimensional matrix front door for the strongest current Chewi Theorem
12.3 quadratic-ASGD weak-limit package.  The caller supplies Loewner spectral
bounds and power-step gates for the matrix `A`; this theorem converts them
into the continuous-linear-map contraction hypothesis used by the source ASGD
formalization.
-/
theorem Chewi127BoundedMartingaleCLTSource.asgd_limit_package_source_quadratic_of_source_uniform_bound_and_uniform_initial_norm_bound_and_matrix_loewner_step_bound
    {Ω Ω' : Type*} [mΩ : MeasurableSpace Ω] {P : Measure Ω}
    [IsProbabilityMeasure P] [MeasurableSpace Ω'] {Q : Measure Ω'}
    [IsProbabilityMeasure Q]
    (S : Chewi127BoundedMartingaleCLTSource Ω Ω'
      (EuclideanSpace ℝ n) P Q)
    (A : Matrix n n ℝ)
    (Ainv : EuclideanSpace ℝ n →L[ℝ] EuclideanSpace ℝ n)
    {alpha beta gamma C0 B0 : ℝ}
    (hleft : Ainv * chewi123MatrixCLM A = 1)
    (hA : A.IsHermitian)
    (halpha : 0 < alpha) (hgamma_pos : 0 < gamma)
    (hgamma_lt : gamma < 1)
    (halpha_step : ∀ m, 2 ≤ m ->
      alpha * chewi125PowerStep gamma m ≤ 1)
    (hbeta_step : ∀ m, 2 ≤ m ->
      beta * chewi125PowerStep gamma m ≤ 1)
    (hlower : alpha • (1 : Matrix n n ℝ) ≤ A)
    (hupper : A ≤ beta • (1 : Matrix n n ℝ))
    (hB0_nonneg : 0 ≤ B0)
    (hinitial_bound : ∀ N,
      ‖chewi123InitialCoefficient (chewi123MatrixCLM A)
          (chewi125PowerStep gamma) N‖ ≤ C0)
    (delta : ℕ -> Ω -> EuclideanSpace ℝ n)
    (hrec : ∀ n ω,
      delta (n + 1) ω =
        chewi123QuadraticStepMap (chewi125PowerStep gamma (n + 1))
          (chewi123MatrixCLM A) (delta n ω) -
          chewi125PowerStep gamma (n + 1) •
            S.martingale.xi (n + 1) ω)
    (hdelta0_meas : AEMeasurable (delta 0) P)
    (hdelta0_bound : ∀ ω, ‖delta 0 ω‖ ≤ B0) :
    TendstoInDistribution
        (fun N ω => chewi123ScaledAverageDelta (fun n => delta n ω) N)
        atTop (fun ω => -Ainv (S.Z ω)) (fun _ => P) Q ∧
      ProbabilityTheory.HasGaussianLaw (fun ω => -Ainv (S.Z ω)) Q ∧
      ∀ L R : StrongDual ℝ (EuclideanSpace ℝ n),
        ProbabilityTheory.covarianceBilinDual
            (Q.map fun ω => -Ainv (S.Z ω)) L R =
          vaart1998_inverseDerivativeCovarianceFunctional (-Ainv)
            (fun L0 R0 =>
              ProbabilityTheory.covarianceBilinDual (Q.map S.Z) L0 R0) L R := by
  have hstep :
      ∀ m, 2 ≤ m ->
        ‖chewi123QuadraticStepMap (chewi125PowerStep gamma m)
            (chewi123MatrixCLM A)‖ ≤
          1 - alpha * chewi125PowerStep gamma m :=
    chewi125QuadraticStepMap_matrixCLM_hstep_of_loewner_bounds
      hA halpha_step hbeta_step hlower hupper
  exact
    S.asgd_limit_package_source_quadratic_of_source_uniform_bound_and_uniform_initial_norm_bound_and_quadratic_step_bound
      (chewi123MatrixCLM A) Ainv hleft halpha hgamma_pos hgamma_lt hstep
      hB0_nonneg hinitial_bound delta hrec hdelta0_meas hdelta0_bound

/--
Finite-dimensional matrix front door for Chewi Theorem 12.3 with the
power-step side conditions discharged by the scalar bounds
`alpha <= 2^gamma` and `beta <= 2^gamma`.
-/
theorem Chewi127BoundedMartingaleCLTSource.asgd_limit_package_source_quadratic_of_source_uniform_bound_and_uniform_initial_norm_bound_and_matrix_loewner_two_rpow_step_bound
    {Ω Ω' : Type*} [mΩ : MeasurableSpace Ω] {P : Measure Ω}
    [IsProbabilityMeasure P] [MeasurableSpace Ω'] {Q : Measure Ω'}
    [IsProbabilityMeasure Q]
    (S : Chewi127BoundedMartingaleCLTSource Ω Ω'
      (EuclideanSpace ℝ n) P Q)
    (A : Matrix n n ℝ)
    (Ainv : EuclideanSpace ℝ n →L[ℝ] EuclideanSpace ℝ n)
    {alpha beta gamma C0 B0 : ℝ}
    (hleft : Ainv * chewi123MatrixCLM A = 1)
    (hA : A.IsHermitian)
    (halpha : 0 < alpha) (hgamma_pos : 0 < gamma)
    (hgamma_lt : gamma < 1)
    (halpha_le_two : alpha ≤ (2 : ℝ) ^ gamma)
    (hbeta_le_two : beta ≤ (2 : ℝ) ^ gamma)
    (hlower : alpha • (1 : Matrix n n ℝ) ≤ A)
    (hupper : A ≤ beta • (1 : Matrix n n ℝ))
    (hB0_nonneg : 0 ≤ B0)
    (hinitial_bound : ∀ N,
      ‖chewi123InitialCoefficient (chewi123MatrixCLM A)
          (chewi125PowerStep gamma) N‖ ≤ C0)
    (delta : ℕ -> Ω -> EuclideanSpace ℝ n)
    (hrec : ∀ n ω,
      delta (n + 1) ω =
        chewi123QuadraticStepMap (chewi125PowerStep gamma (n + 1))
          (chewi123MatrixCLM A) (delta n ω) -
          chewi125PowerStep gamma (n + 1) •
            S.martingale.xi (n + 1) ω)
    (hdelta0_meas : AEMeasurable (delta 0) P)
    (hdelta0_bound : ∀ ω, ‖delta 0 ω‖ ≤ B0) :
    TendstoInDistribution
        (fun N ω => chewi123ScaledAverageDelta (fun n => delta n ω) N)
        atTop (fun ω => -Ainv (S.Z ω)) (fun _ => P) Q ∧
      ProbabilityTheory.HasGaussianLaw (fun ω => -Ainv (S.Z ω)) Q ∧
      ∀ L R : StrongDual ℝ (EuclideanSpace ℝ n),
        ProbabilityTheory.covarianceBilinDual
            (Q.map fun ω => -Ainv (S.Z ω)) L R =
          vaart1998_inverseDerivativeCovarianceFunctional (-Ainv)
            (fun L0 R0 =>
              ProbabilityTheory.covarianceBilinDual (Q.map S.Z) L0 R0) L R := by
  exact
    S.asgd_limit_package_source_quadratic_of_source_uniform_bound_and_uniform_initial_norm_bound_and_matrix_loewner_step_bound
      A Ainv hleft hA halpha hgamma_pos hgamma_lt
      (fun m hm =>
        chewi125PowerStep_mul_le_one_of_le_two_rpow hgamma_pos.le hm
          halpha_le_two)
      (fun m hm =>
        chewi125PowerStep_mul_le_one_of_le_two_rpow hgamma_pos.le hm
          hbeta_le_two)
      hlower hupper hB0_nonneg hinitial_bound delta hrec hdelta0_meas
      hdelta0_bound

/--
Finite-dimensional matrix front door for Chewi Theorem 12.3 with the
left-inverse hypothesis discharged by the canonical matrix inverse.
-/
theorem Chewi127BoundedMartingaleCLTSource.asgd_limit_package_source_quadratic_of_source_uniform_bound_and_uniform_initial_norm_bound_and_matrix_inverse_loewner_two_rpow_step_bound
    {Ω Ω' : Type*} [mΩ : MeasurableSpace Ω] {P : Measure Ω}
    [IsProbabilityMeasure P] [MeasurableSpace Ω'] {Q : Measure Ω'}
    [IsProbabilityMeasure Q]
    (S : Chewi127BoundedMartingaleCLTSource Ω Ω'
      (EuclideanSpace ℝ n) P Q)
    (A : Matrix n n ℝ)
    {alpha beta gamma C0 B0 : ℝ}
    (hA : A.IsHermitian)
    (halpha : 0 < alpha) (hgamma_pos : 0 < gamma)
    (hgamma_lt : gamma < 1)
    (halpha_le_two : alpha ≤ (2 : ℝ) ^ gamma)
    (hbeta_le_two : beta ≤ (2 : ℝ) ^ gamma)
    (hlower : alpha • (1 : Matrix n n ℝ) ≤ A)
    (hupper : A ≤ beta • (1 : Matrix n n ℝ))
    (hB0_nonneg : 0 ≤ B0)
    (hinitial_bound : ∀ N,
      ‖chewi123InitialCoefficient (chewi123MatrixCLM A)
          (chewi125PowerStep gamma) N‖ ≤ C0)
    (delta : ℕ -> Ω -> EuclideanSpace ℝ n)
    (hrec : ∀ n ω,
      delta (n + 1) ω =
        chewi123QuadraticStepMap (chewi125PowerStep gamma (n + 1))
          (chewi123MatrixCLM A) (delta n ω) -
          chewi125PowerStep gamma (n + 1) •
            S.martingale.xi (n + 1) ω)
    (hdelta0_meas : AEMeasurable (delta 0) P)
    (hdelta0_bound : ∀ ω, ‖delta 0 ω‖ ≤ B0) :
    TendstoInDistribution
        (fun N ω => chewi123ScaledAverageDelta (fun n => delta n ω) N)
        atTop (fun ω => -chewi123MatrixCLM A⁻¹ (S.Z ω)) (fun _ => P) Q ∧
      ProbabilityTheory.HasGaussianLaw
        (fun ω => -chewi123MatrixCLM A⁻¹ (S.Z ω)) Q ∧
      ∀ L R : StrongDual ℝ (EuclideanSpace ℝ n),
        ProbabilityTheory.covarianceBilinDual
            (Q.map fun ω => -chewi123MatrixCLM A⁻¹ (S.Z ω)) L R =
          vaart1998_inverseDerivativeCovarianceFunctional
            (-chewi123MatrixCLM A⁻¹)
            (fun L0 R0 =>
              ProbabilityTheory.covarianceBilinDual (Q.map S.Z) L0 R0) L R := by
  exact
    S.asgd_limit_package_source_quadratic_of_source_uniform_bound_and_uniform_initial_norm_bound_and_matrix_loewner_two_rpow_step_bound
      A (chewi123MatrixCLM A⁻¹)
      (chewi123MatrixCLM_inv_mul_self_eq_one_of_pos_loewner
        hA halpha hlower)
      hA halpha hgamma_pos hgamma_lt halpha_le_two hbeta_le_two hlower
      hupper hB0_nonneg hinitial_bound delta hrec hdelta0_meas
      hdelta0_bound

/--
Finite-dimensional matrix front door for Chewi Theorem 12.3 with the
canonical matrix inverse, power-step side conditions, residual coefficient
bound, and initial-coefficient bound all discharged from Loewner assumptions.
-/
theorem Chewi127BoundedMartingaleCLTSource.asgd_limit_package_source_quadratic_of_source_uniform_bound_and_matrix_inverse_loewner_two_rpow_step_bound
    {Ω Ω' : Type*} [mΩ : MeasurableSpace Ω] {P : Measure Ω}
    [IsProbabilityMeasure P] [MeasurableSpace Ω'] {Q : Measure Ω'}
    [IsProbabilityMeasure Q]
    (S : Chewi127BoundedMartingaleCLTSource Ω Ω'
      (EuclideanSpace ℝ n) P Q)
    (A : Matrix n n ℝ)
    {alpha beta gamma B0 : ℝ}
    (hA : A.IsHermitian)
    (halpha : 0 < alpha) (hgamma_pos : 0 < gamma)
    (hgamma_lt : gamma < 1)
    (halpha_le_two : alpha ≤ (2 : ℝ) ^ gamma)
    (hbeta_le_two : beta ≤ (2 : ℝ) ^ gamma)
    (hlower : alpha • (1 : Matrix n n ℝ) ≤ A)
    (hupper : A ≤ beta • (1 : Matrix n n ℝ))
    (hB0_nonneg : 0 ≤ B0)
    (delta : ℕ -> Ω -> EuclideanSpace ℝ n)
    (hrec : ∀ n ω,
      delta (n + 1) ω =
        chewi123QuadraticStepMap (chewi125PowerStep gamma (n + 1))
          (chewi123MatrixCLM A) (delta n ω) -
          chewi125PowerStep gamma (n + 1) •
            S.martingale.xi (n + 1) ω)
    (hdelta0_meas : AEMeasurable (delta 0) P)
    (hdelta0_bound : ∀ ω, ‖delta 0 ω‖ ≤ B0) :
    TendstoInDistribution
        (fun N ω => chewi123ScaledAverageDelta (fun n => delta n ω) N)
        atTop (fun ω => -chewi123MatrixCLM A⁻¹ (S.Z ω)) (fun _ => P) Q ∧
      ProbabilityTheory.HasGaussianLaw
        (fun ω => -chewi123MatrixCLM A⁻¹ (S.Z ω)) Q ∧
      ∀ L R : StrongDual ℝ (EuclideanSpace ℝ n),
        ProbabilityTheory.covarianceBilinDual
            (Q.map fun ω => -chewi123MatrixCLM A⁻¹ (S.Z ω)) L R =
          vaart1998_inverseDerivativeCovarianceFunctional
            (-chewi123MatrixCLM A⁻¹)
            (fun L0 R0 =>
              ProbabilityTheory.covarianceBilinDual (Q.map S.Z) L0 R0) L R := by
  have hstep :
      ∀ m, 2 ≤ m ->
        ‖chewi123QuadraticStepMap (chewi125PowerStep gamma m)
            (chewi123MatrixCLM A)‖ ≤
          1 - alpha * chewi125PowerStep gamma m :=
    chewi125QuadraticStepMap_matrixCLM_hstep_of_loewner_bounds
      hA
      (fun m hm =>
        chewi125PowerStep_mul_le_one_of_le_two_rpow hgamma_pos.le hm
          halpha_le_two)
      (fun m hm =>
        chewi125PowerStep_mul_le_one_of_le_two_rpow hgamma_pos.le hm
          hbeta_le_two)
      hlower hupper
  exact
    S.asgd_limit_package_source_quadratic_of_source_uniform_bound_and_quadratic_step_bound
      (chewi123MatrixCLM A) (chewi123MatrixCLM A⁻¹)
      (chewi123MatrixCLM_inv_mul_self_eq_one_of_pos_loewner
        hA halpha hlower)
      halpha hgamma_pos hgamma_lt hstep hB0_nonneg delta hrec
      hdelta0_meas hdelta0_bound

/--
Finite-dimensional matrix front door for the Chewi Theorem 12.7
characteristic-function CLT source, with the canonical inverse and all
Chewi Theorem 12.3 ASGD deterministic side conditions discharged by the
Loewner power-step assumptions.
-/
theorem Chewi127BoundedMartingaleCharFunCLTSource.asgd_limit_package_source_quadratic_of_source_uniform_bound_and_matrix_inverse_loewner_two_rpow_step_bound
    {Ω Ω' : Type*} [mΩ : MeasurableSpace Ω] {P : Measure Ω}
    [IsProbabilityMeasure P] [MeasurableSpace Ω'] {Q : Measure Ω'}
    [IsProbabilityMeasure Q]
    (S : Chewi127BoundedMartingaleCharFunCLTSource Ω Ω'
      (EuclideanSpace ℝ n) P Q)
    (A : Matrix n n ℝ)
    {alpha beta gamma B0 : ℝ}
    (hA : A.IsHermitian)
    (halpha : 0 < alpha) (hgamma_pos : 0 < gamma)
    (hgamma_lt : gamma < 1)
    (halpha_le_two : alpha ≤ (2 : ℝ) ^ gamma)
    (hbeta_le_two : beta ≤ (2 : ℝ) ^ gamma)
    (hlower : alpha • (1 : Matrix n n ℝ) ≤ A)
    (hupper : A ≤ beta • (1 : Matrix n n ℝ))
    (hB0_nonneg : 0 ≤ B0)
    (delta : ℕ -> Ω -> EuclideanSpace ℝ n)
    (hrec : ∀ n ω,
      delta (n + 1) ω =
        chewi123QuadraticStepMap (chewi125PowerStep gamma (n + 1))
          (chewi123MatrixCLM A) (delta n ω) -
          chewi125PowerStep gamma (n + 1) •
            S.martingale.xi (n + 1) ω)
    (hdelta0_meas : AEMeasurable (delta 0) P)
    (hdelta0_bound : ∀ ω, ‖delta 0 ω‖ ≤ B0) :
    TendstoInDistribution
        (fun N ω => chewi123ScaledAverageDelta (fun n => delta n ω) N)
        atTop (fun ω => -chewi123MatrixCLM A⁻¹ (S.Z ω)) (fun _ => P) Q ∧
      ProbabilityTheory.HasGaussianLaw
        (fun ω => -chewi123MatrixCLM A⁻¹ (S.Z ω)) Q ∧
      ∀ L R : StrongDual ℝ (EuclideanSpace ℝ n),
        ProbabilityTheory.covarianceBilinDual
            (Q.map fun ω => -chewi123MatrixCLM A⁻¹ (S.Z ω)) L R =
          vaart1998_inverseDerivativeCovarianceFunctional
            (-chewi123MatrixCLM A⁻¹)
            (fun L0 R0 =>
              ProbabilityTheory.covarianceBilinDual (Q.map S.Z) L0 R0) L R := by
  simpa [Chewi127BoundedMartingaleCharFunCLTSource.toBoundedMartingaleCLTSource]
    using
      S.toBoundedMartingaleCLTSource.asgd_limit_package_source_quadratic_of_source_uniform_bound_and_matrix_inverse_loewner_two_rpow_step_bound
        A hA halpha hgamma_pos hgamma_lt halpha_le_two hbeta_le_two hlower
        hupper hB0_nonneg delta hrec hdelta0_meas hdelta0_bound

/--
Finite-dimensional matrix front door for the non-circular Chewi Theorem 12.7
core, with the canonical inverse and all Chewi Theorem 12.3 ASGD deterministic
side conditions discharged by the Loewner power-step assumptions.
-/
theorem Chewi127BoundedMartingaleCharFunCLTCore.asgd_limit_package_source_quadratic_of_source_uniform_bound_and_matrix_inverse_loewner_two_rpow_step_bound
    {Ω Ω' : Type*} [mΩ : MeasurableSpace Ω] {P : Measure Ω}
    [IsProbabilityMeasure P] [MeasurableSpace Ω'] {Q : Measure Ω'}
    [IsProbabilityMeasure Q]
    (S : Chewi127BoundedMartingaleCharFunCLTCore Ω Ω'
      (EuclideanSpace ℝ n) P Q)
    (A : Matrix n n ℝ)
    {alpha beta gamma B0 : ℝ}
    (hA : A.IsHermitian)
    (halpha : 0 < alpha) (hgamma_pos : 0 < gamma)
    (hgamma_lt : gamma < 1)
    (halpha_le_two : alpha ≤ (2 : ℝ) ^ gamma)
    (hbeta_le_two : beta ≤ (2 : ℝ) ^ gamma)
    (hlower : alpha • (1 : Matrix n n ℝ) ≤ A)
    (hupper : A ≤ beta • (1 : Matrix n n ℝ))
    (hB0_nonneg : 0 ≤ B0)
    (delta : ℕ -> Ω -> EuclideanSpace ℝ n)
    (hrec : ∀ n ω,
      delta (n + 1) ω =
        chewi123QuadraticStepMap (chewi125PowerStep gamma (n + 1))
          (chewi123MatrixCLM A) (delta n ω) -
          chewi125PowerStep gamma (n + 1) •
            S.martingale.xi (n + 1) ω)
    (hdelta0_meas : AEMeasurable (delta 0) P)
    (hdelta0_bound : ∀ ω, ‖delta 0 ω‖ ≤ B0) :
    TendstoInDistribution
        (fun N ω => chewi123ScaledAverageDelta (fun n => delta n ω) N)
        atTop (fun ω => -chewi123MatrixCLM A⁻¹ (S.Z ω)) (fun _ => P) Q ∧
      ProbabilityTheory.HasGaussianLaw
        (fun ω => -chewi123MatrixCLM A⁻¹ (S.Z ω)) Q ∧
      ∀ L R : StrongDual ℝ (EuclideanSpace ℝ n),
        ProbabilityTheory.covarianceBilinDual
            (Q.map fun ω => -chewi123MatrixCLM A⁻¹ (S.Z ω)) L R =
          vaart1998_inverseDerivativeCovarianceFunctional
            (-chewi123MatrixCLM A⁻¹)
            (fun L0 R0 =>
              ProbabilityTheory.covarianceBilinDual (Q.map S.Z) L0 R0) L R := by
  simpa [Chewi127BoundedMartingaleCharFunCLTCore.toCharFunCLTSource_of_uniform_bound_no_factor_bound]
    using
      S.toCharFunCLTSource_of_uniform_bound_no_factor_bound.asgd_limit_package_source_quadratic_of_source_uniform_bound_and_matrix_inverse_loewner_two_rpow_step_bound
        A hA halpha hgamma_pos hgamma_lt halpha_le_two hbeta_le_two hlower
        hupper hB0_nonneg delta hrec hdelta0_meas hdelta0_bound

end Optimization
end StatInference
