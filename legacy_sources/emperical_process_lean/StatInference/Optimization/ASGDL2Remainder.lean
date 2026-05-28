import StatInference.Optimization.ASGDEndpointCorrection
import StatInference.ProbabilityTheory.Basic

/-!
# L2 remainder bridges for Chewi ASGD

This module isolates the probability-theory imports needed for the L2
endpoint-corrected ASGD remainder route.  Keeping these bridges separate avoids
changing the notation/import surface of the large endpoint-correction module.
-/

namespace StatInference
namespace Optimization

open Filter MeasureTheory ProbabilityTheory
open StatInference.AsymptoticStatistics
open Finset
open scoped BigOperators Topology ENNReal

/--
If a nonnegative triangular row has vanishing average and is uniformly bounded,
then the average of its squares also vanishes.  This is the deterministic
coefficient step needed before applying the L2/orthogonality argument after
Chewi Lemma 12.5.
-/
theorem chewi125_average_sq_tendsto_zero_of_average_uniform_bound
    (R : ℕ -> ℕ -> ℝ) {C : ℝ}
    (hR_nonneg : ∀ N k, k ∈ Finset.Ico 1 N -> 0 ≤ R N k)
    (hR_bound : ∀ N k, k ∈ Finset.Ico 1 N -> R N k ≤ C)
    (havg :
      Tendsto
        (fun N : ℕ => (N : ℝ)⁻¹ * ∑ k ∈ Finset.Ico 1 N, R N k)
        atTop (𝓝 0)) :
    Tendsto
      (fun N : ℕ => (N : ℝ)⁻¹ * ∑ k ∈ Finset.Ico 1 N, (R N k) ^ 2)
      atTop (𝓝 0) := by
  have hupper :
      Tendsto
        (fun N : ℕ => C * ((N : ℝ)⁻¹ * ∑ k ∈ Finset.Ico 1 N, R N k))
        atTop (𝓝 (C * 0)) :=
    tendsto_const_nhds.mul havg
  have hupper0 :
      Tendsto
        (fun N : ℕ => (N : ℝ)⁻¹ * (C * ∑ k ∈ Finset.Ico 1 N, R N k))
        atTop (𝓝 0) := by
    have hupper0' :
        Tendsto
          (fun N : ℕ => C * ((N : ℝ)⁻¹ * ∑ k ∈ Finset.Ico 1 N, R N k))
          atTop (𝓝 0) := by
      simpa using hupper
    refine hupper0'.congr' ?_
    exact Eventually.of_forall fun N => by ring
  refine tendsto_of_tendsto_of_tendsto_of_le_of_le' tendsto_const_nhds
    hupper0 ?_ ?_
  · exact Eventually.of_forall fun N =>
      mul_nonneg (inv_nonneg.mpr (Nat.cast_nonneg N))
        (Finset.sum_nonneg fun k _hk => sq_nonneg (R N k))
  · exact Eventually.of_forall fun N => by
      have hsum :
          (∑ k ∈ Finset.Ico 1 N, (R N k) ^ 2) ≤
            C * ∑ k ∈ Finset.Ico 1 N, R N k := by
        rw [Finset.mul_sum]
        exact Finset.sum_le_sum fun k hk => by
          have hnonneg := hR_nonneg N k hk
          have hle := hR_bound N k hk
          nlinarith
      exact mul_le_mul_of_nonneg_left hsum
        (inv_nonneg.mpr (Nat.cast_nonneg N))

/--
Chewi Lemma 12.5 square-average handoff: if the residual-row coefficients are
uniformly bounded, the source average convergence from V131 also gives
vanishing average squared coefficients.  This is the deterministic scalar input
for the subsequent martingale-orthogonality/L2 stochastic remainder proof.
-/
theorem chewi125SourceNoiseCoefficient_sub_left_inv_average_sq_tendsto_zero
    {E : Type*} [NormedAddCommGroup E] [NormedSpace ℝ E]
    (A Ainv : E →L[ℝ] E) {alpha gamma C : ℝ}
    (hleft : Ainv * A = 1)
    (halpha : 0 < alpha) (hgamma_pos : 0 < gamma) (hgamma_lt : gamma < 1)
    (hcoeff_bound : ∀ N k, k ∈ Finset.Ico 1 N ->
      ‖chewi123SourceNoiseCoefficient A (chewi125PowerStep gamma) k N - Ainv‖ ≤ C)
    (hstep : ∀ m, 2 ≤ m ->
      ‖chewi123QuadraticStepMap (chewi125PowerStep gamma m) A‖ ≤
        1 - alpha * chewi125PowerStep gamma m)
    (hsmall : ∀ m, 2 ≤ m ->
      0 ≤ 1 - alpha * chewi125PowerStep gamma m) :
    Tendsto
      (fun N : ℕ =>
        (N : ℝ)⁻¹ *
          ∑ k ∈ Finset.Ico 1 N,
            ‖chewi123SourceNoiseCoefficient A (chewi125PowerStep gamma) k N -
              Ainv‖ ^ 2)
      atTop (𝓝 0) := by
  exact chewi125_average_sq_tendsto_zero_of_average_uniform_bound
    (fun N k =>
      ‖chewi123SourceNoiseCoefficient A (chewi125PowerStep gamma) k N - Ainv‖)
    (fun N k _hk => norm_nonneg _)
    hcoeff_bound
    (chewi125SourceNoiseCoefficient_sub_left_inv_average_tendsto_zero
      A Ainv hleft halpha hgamma_pos hgamma_lt hstep hsmall)

/--
L2-to-probability endpoint for the Chewi ASGD endpoint-corrected remainder.
The next orthogonality packet only has to prove that the ordinary second moment
of the remainder norm tends to zero; this bridge turns that into the required
`o_P(1)` statement.
-/
theorem chewi123ASGDEndpointCorrectedRemainder_tendstoInMeasure_zero_of_integral_norm_sq_tendsto_zero
    {Ω E : Type*} [MeasurableSpace Ω] {P : Measure Ω}
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    (A Ainv : E →L[ℝ] E) (h : ℕ -> ℝ) (xi : ℕ -> Ω -> E)
    (hmem : ∀ N,
      MemLp
        (fun ω => ‖chewi123ASGDEndpointCorrectedRemainder A Ainv h
          (fun n => xi n ω) N‖) (2 : ℝ≥0∞) P)
    (hsq :
      Tendsto
        (fun N : ℕ =>
          ∫ ω,
            ‖chewi123ASGDEndpointCorrectedRemainder A Ainv h
              (fun n => xi n ω) N‖ ^ 2 ∂P)
        atTop (𝓝 (0 : ℝ))) :
    TendstoInMeasure P
      (fun N ω => chewi123ASGDEndpointCorrectedRemainder A Ainv h
        (fun n => xi n ω) N)
      atTop (fun _ => 0) := by
  have hnorm :
      TendstoInMeasure P
        (fun N ω =>
          ‖chewi123ASGDEndpointCorrectedRemainder A Ainv h
            (fun n => xi n ω) N‖)
        atTop (fun _ => (0 : ℝ)) :=
    durrett2019_lemma_2_2_2_tendstoInMeasure_of_integral_sq_tendsto_zero
      (P := P)
      (Z := fun N ω =>
        ‖chewi123ASGDEndpointCorrectedRemainder A Ainv h
          (fun n => xi n ω) N‖)
      hmem hsq
  refine vaart1998_tendstoInMeasure_const_of_norm_sub_const_zero
    (P := P)
    (X := fun N ω => chewi123ASGDEndpointCorrectedRemainder A Ainv h
      (fun n => xi n ω) N)
    (c := (0 : E)) ?_
  simpa [sub_zero] using hnorm

/--
If two Hilbert/normed-space random rows have vanishing second moments, then so
does their pointwise difference.  This is the deterministic L2 assembly step
used to combine Chewi's residual sum with the endpoint correction.
-/
theorem integral_norm_sq_sub_tendsto_zero_of_integral_norm_sq_tendsto_zero
    {Ω E : Type*} [MeasurableSpace Ω] {P : Measure Ω}
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    (U V : ℕ -> Ω -> E)
    (hU_int : ∀ N, Integrable (fun ω => ‖U N ω‖ ^ (2 : ℕ)) P)
    (hV_int : ∀ N, Integrable (fun ω => ‖V N ω‖ ^ (2 : ℕ)) P)
    (hU :
      Tendsto (fun N : ℕ => ∫ ω, ‖U N ω‖ ^ (2 : ℕ) ∂P) atTop (𝓝 0))
    (hV :
      Tendsto (fun N : ℕ => ∫ ω, ‖V N ω‖ ^ (2 : ℕ) ∂P) atTop (𝓝 0)) :
    Tendsto (fun N : ℕ => ∫ ω, ‖U N ω - V N ω‖ ^ (2 : ℕ) ∂P)
      atTop (𝓝 0) := by
  have hupper :
      Tendsto
        (fun N : ℕ =>
          (2 : ℝ) * ∫ ω, ‖U N ω‖ ^ (2 : ℕ) ∂P +
            (2 : ℝ) * ∫ ω, ‖V N ω‖ ^ (2 : ℕ) ∂P)
        atTop (𝓝 0) := by
    have hU2 :
        Tendsto
          (fun N : ℕ => (2 : ℝ) * ∫ ω, ‖U N ω‖ ^ (2 : ℕ) ∂P)
          atTop (𝓝 ((2 : ℝ) * 0)) :=
      tendsto_const_nhds.mul hU
    have hV2 :
        Tendsto
          (fun N : ℕ => (2 : ℝ) * ∫ ω, ‖V N ω‖ ^ (2 : ℕ) ∂P)
          atTop (𝓝 ((2 : ℝ) * 0)) :=
      tendsto_const_nhds.mul hV
    have hsum := hU2.add hV2
    simpa using hsum
  refine tendsto_of_tendsto_of_tendsto_of_le_of_le' tendsto_const_nhds
    hupper ?_ ?_
  · exact Eventually.of_forall fun N =>
      integral_nonneg fun ω => sq_nonneg _
  · exact Eventually.of_forall fun N => by
      have hrhs_int :
          Integrable
            (fun ω =>
              (2 : ℝ) * ‖U N ω‖ ^ (2 : ℕ) +
                (2 : ℝ) * ‖V N ω‖ ^ (2 : ℕ)) P :=
        (hU_int N).const_mul 2 |>.add ((hV_int N).const_mul 2)
      have hleft_nonneg :
          0 ≤ᵐ[P] fun ω => ‖U N ω - V N ω‖ ^ (2 : ℕ) :=
        Eventually.of_forall fun ω => sq_nonneg _
      have hpoint :
          (fun ω => ‖U N ω - V N ω‖ ^ (2 : ℕ)) ≤ᵐ[P]
            fun ω =>
              (2 : ℝ) * ‖U N ω‖ ^ (2 : ℕ) +
                (2 : ℝ) * ‖V N ω‖ ^ (2 : ℕ) := by
        exact Eventually.of_forall fun ω => by
          have htri : ‖U N ω - V N ω‖ ≤ ‖U N ω‖ + ‖V N ω‖ :=
            norm_sub_le _ _
          have hsq :
              ‖U N ω - V N ω‖ ^ (2 : ℕ) ≤
                (‖U N ω‖ + ‖V N ω‖) ^ (2 : ℕ) :=
            pow_le_pow_left₀ (norm_nonneg _) htri 2
          have hquad :
              (‖U N ω‖ + ‖V N ω‖) ^ (2 : ℕ) ≤
                (2 : ℝ) * ‖U N ω‖ ^ (2 : ℕ) +
                  (2 : ℝ) * ‖V N ω‖ ^ (2 : ℕ) := by
            nlinarith [sq_nonneg (‖U N ω‖ - ‖V N ω‖)]
          exact hsq.trans hquad
      have hmain :
          ∫ ω, ‖U N ω - V N ω‖ ^ (2 : ℕ) ∂P ≤
            ∫ ω,
              (2 : ℝ) * ‖U N ω‖ ^ (2 : ℕ) +
                (2 : ℝ) * ‖V N ω‖ ^ (2 : ℕ) ∂P :=
        integral_mono_of_nonneg hleft_nonneg hrhs_int hpoint
      calc
        ∫ ω, ‖U N ω - V N ω‖ ^ (2 : ℕ) ∂P
            ≤ ∫ ω,
                (2 : ℝ) * ‖U N ω‖ ^ (2 : ℕ) +
                  (2 : ℝ) * ‖V N ω‖ ^ (2 : ℕ) ∂P := hmain
        _ = (2 : ℝ) * ∫ ω, ‖U N ω‖ ^ (2 : ℕ) ∂P +
              (2 : ℝ) * ∫ ω, ‖V N ω‖ ^ (2 : ℕ) ∂P := by
              rw [integral_add ((hU_int N).const_mul 2) ((hV_int N).const_mul 2)]
              rw [integral_const_mul, integral_const_mul]

/--
Finite-sum Hilbert-space Pythagoras after integration.  If all cross inner
products have zero integral, the second moment of the sum is the sum of the
second moments.
-/
theorem integral_norm_sq_finset_sum_eq_sum_integral_norm_sq_of_pairwise_integral_inner_zero
    {Ω E ι : Type*} [MeasurableSpace Ω] {P : Measure Ω}
    [NormedAddCommGroup E] [InnerProductSpace ℝ E] [CompleteSpace E]
    (s : Finset ι) (Y : ι -> Ω -> E)
    (hinner_int : ∀ i, i ∈ s -> ∀ j, j ∈ s ->
      Integrable (fun ω => inner ℝ (Y i ω) (Y j ω)) P)
    (horth : ∀ i, i ∈ s -> ∀ j, j ∈ s -> i ≠ j ->
      ∫ ω, inner ℝ (Y i ω) (Y j ω) ∂P = 0) :
    ∫ ω, ‖∑ i ∈ s, Y i ω‖ ^ (2 : ℕ) ∂P =
      ∑ i ∈ s, ∫ ω, ‖Y i ω‖ ^ (2 : ℕ) ∂P := by
  calc
    ∫ ω, ‖∑ i ∈ s, Y i ω‖ ^ (2 : ℕ) ∂P
        = ∫ ω, ∑ i ∈ s, ∑ j ∈ s,
            inner ℝ (Y i ω) (Y j ω) ∂P := by
          congr 1
          ext ω
          rw [← real_inner_self_eq_norm_sq]
          rw [sum_inner]
          simp_rw [inner_sum]
    _ = ∑ i ∈ s, ∑ j ∈ s,
          ∫ ω, inner ℝ (Y i ω) (Y j ω) ∂P := by
          rw [integral_finsetSum]
          · refine Finset.sum_congr rfl ?_
            intro i hi
            rw [integral_finsetSum]
            exact fun j hj => hinner_int i hi j hj
          · intro i hi
            exact integrable_finsetSum s fun j hj => hinner_int i hi j hj
    _ = ∑ i ∈ s, ∫ ω, ‖Y i ω‖ ^ (2 : ℕ) ∂P := by
          refine Finset.sum_congr rfl ?_
          intro i hi
          calc
            (∑ j ∈ s, ∫ ω, inner ℝ (Y i ω) (Y j ω) ∂P)
                = ∫ ω, inner ℝ (Y i ω) (Y i ω) ∂P := by
                    refine Finset.sum_eq_single i ?_ ?_
                    · intro j hj hji
                      exact horth i hi j hj hji.symm
                    · intro hi_not
                      exact (hi_not hi).elim
            _ = ∫ ω, ‖Y i ω‖ ^ (2 : ℕ) ∂P := by
                    congr 1
                    ext ω
                    rw [real_inner_self_eq_norm_sq]

/--
Bounded version of the integrated finite-sum Pythagoras identity.
-/
theorem integral_norm_sq_finset_sum_le_sum_bound_of_pairwise_integral_inner_zero
    {Ω E ι : Type*} [MeasurableSpace Ω] {P : Measure Ω}
    [NormedAddCommGroup E] [InnerProductSpace ℝ E] [CompleteSpace E]
    (s : Finset ι) (Y : ι -> Ω -> E) (B : ι -> ℝ)
    (hinner_int : ∀ i, i ∈ s -> ∀ j, j ∈ s ->
      Integrable (fun ω => inner ℝ (Y i ω) (Y j ω)) P)
    (horth : ∀ i, i ∈ s -> ∀ j, j ∈ s -> i ≠ j ->
      ∫ ω, inner ℝ (Y i ω) (Y j ω) ∂P = 0)
    (hdiag_le : ∀ i, i ∈ s ->
      ∫ ω, ‖Y i ω‖ ^ (2 : ℕ) ∂P ≤ B i) :
    ∫ ω, ‖∑ i ∈ s, Y i ω‖ ^ (2 : ℕ) ∂P ≤
      ∑ i ∈ s, B i := by
  rw [integral_norm_sq_finset_sum_eq_sum_integral_norm_sq_of_pairwise_integral_inner_zero
    s Y hinner_int horth]
  exact Finset.sum_le_sum fun i hi => hdiag_le i hi

/--
Asymptotic version of the integrated finite-sum Pythagoras bound: if the
diagonal bound has vanishing row sum, then the second moment of the random sum
vanishes.
-/
theorem integral_norm_sq_finset_sum_tendsto_zero_of_pairwise_integral_inner_zero
    {Ω E ι : Type*} [MeasurableSpace Ω] {P : Measure Ω}
    [NormedAddCommGroup E] [InnerProductSpace ℝ E] [CompleteSpace E]
    (s : ℕ -> Finset ι) (Y : ℕ -> ι -> Ω -> E) (B : ℕ -> ι -> ℝ)
    (hinner_int : ∀ N i, i ∈ s N -> ∀ j, j ∈ s N ->
      Integrable (fun ω => inner ℝ (Y N i ω) (Y N j ω)) P)
    (horth : ∀ N i, i ∈ s N -> ∀ j, j ∈ s N -> i ≠ j ->
      ∫ ω, inner ℝ (Y N i ω) (Y N j ω) ∂P = 0)
    (hdiag_le : ∀ N i, i ∈ s N ->
      ∫ ω, ‖Y N i ω‖ ^ (2 : ℕ) ∂P ≤ B N i)
    (hB_tendsto :
      Tendsto (fun N : ℕ => ∑ i ∈ s N, B N i) atTop (𝓝 0)) :
    Tendsto
      (fun N : ℕ => ∫ ω, ‖∑ i ∈ s N, Y N i ω‖ ^ (2 : ℕ) ∂P)
      atTop (𝓝 0) := by
  refine tendsto_of_tendsto_of_tendsto_of_le_of_le' tendsto_const_nhds
    hB_tendsto ?_ ?_
  · exact Eventually.of_forall fun N =>
      integral_nonneg fun ω => sq_nonneg _
  · exact Eventually.of_forall fun N =>
      integral_norm_sq_finset_sum_le_sum_bound_of_pairwise_integral_inner_zero
        (s N) (Y N) (B N)
        (hinner_int N) (horth N) (hdiag_le N)

/--
L2 Cauchy-Schwarz integrability bridge for random Hilbert-space inner
products.  This packages the mathlib `MemLp`/Holder machinery in the source
shape needed by the Chewi martingale residual sums.
-/
theorem integrable_inner_of_integrable_norm_sq
    {Ω E : Type*} [MeasurableSpace Ω] {P : Measure Ω}
    [NormedAddCommGroup E] [InnerProductSpace ℝ E]
    {f g : Ω -> E}
    (hf_meas : AEStronglyMeasurable f P)
    (hg_meas : AEStronglyMeasurable g P)
    (hf_sq : Integrable (fun ω => ‖f ω‖ ^ (2 : ℕ)) P)
    (hg_sq : Integrable (fun ω => ‖g ω‖ ^ (2 : ℕ)) P) :
    Integrable (fun ω => inner ℝ (f ω) (g ω)) P := by
  have hf_mem : MemLp f (2 : ℝ≥0∞) P :=
    (memLp_two_iff_integrable_sq_norm hf_meas).2 (by simpa using hf_sq)
  have hg_mem : MemLp g (2 : ℝ≥0∞) P :=
    (memLp_two_iff_integrable_sq_norm hg_meas).2 (by simpa using hg_sq)
  haveI : ENNReal.HolderTriple
      (2 : ℝ≥0∞) (2 : ℝ≥0∞) (1 : ℝ≥0∞) := by
    simpa using Real.HolderConjugate.two_two.ennrealOfReal
  have hprod :
      Integrable (fun ω => ‖f ω‖ * ‖g ω‖) P := by
    simpa [Pi.mul_apply] using
      (MemLp.integrable_mul (hf_mem.norm) (hg_mem.norm))
  refine Integrable.mono' hprod (hf_meas.inner hg_meas) ?_
  exact Eventually.of_forall fun ω => norm_inner_le_norm (f ω) (g ω)

/--
Chewi ASGD residual-sum second-moment handoff.  Under cross-term
orthogonality and a diagonal second-moment bound by a uniform noise scale times
the squared source coefficient residuals, the scaled coefficient-residual sum
has vanishing second moment.
-/
theorem chewi123ASGD_scaled_residual_sum_integral_norm_sq_tendsto_zero_of_pairwise_integral_inner_zero
    {Ω E : Type*} [MeasurableSpace Ω] {P : Measure Ω}
    [NormedAddCommGroup E] [InnerProductSpace ℝ E] [CompleteSpace E]
    (A Ainv : E →L[ℝ] E) (xi : ℕ -> Ω -> E) {alpha gamma C B : ℝ}
    (hleft : Ainv * A = 1)
    (halpha : 0 < alpha) (hgamma_pos : 0 < gamma) (hgamma_lt : gamma < 1)
    (hcoeff_bound : ∀ N k, k ∈ Finset.Ico 1 N ->
      ‖chewi123SourceNoiseCoefficient A (chewi125PowerStep gamma) k N - Ainv‖ ≤ C)
    (hstep : ∀ m, 2 ≤ m ->
      ‖chewi123QuadraticStepMap (chewi125PowerStep gamma m) A‖ ≤
        1 - alpha * chewi125PowerStep gamma m)
    (hsmall : ∀ m, 2 ≤ m ->
      0 ≤ 1 - alpha * chewi125PowerStep gamma m)
    (hinner_int : ∀ (N k : ℕ), k ∈ Finset.Ico 1 N -> ∀ (j : ℕ), j ∈ Finset.Ico 1 N ->
      Integrable
        (fun ω =>
          inner ℝ
            ((Real.sqrt (N : ℝ))⁻¹ •
              ((chewi123SourceNoiseCoefficient A (chewi125PowerStep gamma) k N -
                Ainv) (xi k ω)))
            ((Real.sqrt (N : ℝ))⁻¹ •
              ((chewi123SourceNoiseCoefficient A (chewi125PowerStep gamma) j N -
                Ainv) (xi j ω)))) P)
    (horth : ∀ (N k : ℕ), k ∈ Finset.Ico 1 N -> ∀ (j : ℕ), j ∈ Finset.Ico 1 N ->
      k ≠ j ->
      ∫ ω,
          inner ℝ
            ((Real.sqrt (N : ℝ))⁻¹ •
              ((chewi123SourceNoiseCoefficient A (chewi125PowerStep gamma) k N -
                Ainv) (xi k ω)))
            ((Real.sqrt (N : ℝ))⁻¹ •
              ((chewi123SourceNoiseCoefficient A (chewi125PowerStep gamma) j N -
                Ainv) (xi j ω))) ∂P = 0)
    (hdiag_le : ∀ (N k : ℕ), k ∈ Finset.Ico 1 N ->
      ∫ ω,
          ‖(Real.sqrt (N : ℝ))⁻¹ •
            ((chewi123SourceNoiseCoefficient A (chewi125PowerStep gamma) k N -
              Ainv) (xi k ω))‖ ^ (2 : ℕ) ∂P ≤
        (N : ℝ)⁻¹ * B *
          ‖chewi123SourceNoiseCoefficient A (chewi125PowerStep gamma) k N -
            Ainv‖ ^ (2 : ℕ)) :
    Tendsto
      (fun N : ℕ =>
        ∫ ω,
          ‖∑ k ∈ Finset.Ico 1 N,
            (Real.sqrt (N : ℝ))⁻¹ •
              ((chewi123SourceNoiseCoefficient A (chewi125PowerStep gamma) k N -
                Ainv) (xi k ω))‖ ^ (2 : ℕ) ∂P)
      atTop (𝓝 0) := by
  have hcoeff_sq :
      Tendsto
        (fun N : ℕ =>
          (N : ℝ)⁻¹ *
            ∑ k ∈ Finset.Ico 1 N,
              ‖chewi123SourceNoiseCoefficient A (chewi125PowerStep gamma) k N -
                Ainv‖ ^ 2)
        atTop (𝓝 0) :=
    chewi125SourceNoiseCoefficient_sub_left_inv_average_sq_tendsto_zero
      A Ainv hleft halpha hgamma_pos hgamma_lt hcoeff_bound hstep hsmall
  have hB_tendsto :
      Tendsto
        (fun N : ℕ =>
          ∑ k ∈ Finset.Ico 1 N,
            (N : ℝ)⁻¹ * B *
              ‖chewi123SourceNoiseCoefficient A (chewi125PowerStep gamma) k N -
                Ainv‖ ^ (2 : ℕ))
        atTop (𝓝 0) := by
    have hmul :
        Tendsto
          (fun N : ℕ =>
            B *
              ((N : ℝ)⁻¹ *
                ∑ k ∈ Finset.Ico 1 N,
                  ‖chewi123SourceNoiseCoefficient A (chewi125PowerStep gamma) k N -
                    Ainv‖ ^ 2))
          atTop (𝓝 (B * 0)) :=
      tendsto_const_nhds.mul hcoeff_sq
    have hmul0 :
        Tendsto
          (fun N : ℕ =>
            B *
              ((N : ℝ)⁻¹ *
                ∑ k ∈ Finset.Ico 1 N,
                  ‖chewi123SourceNoiseCoefficient A (chewi125PowerStep gamma) k N -
                    Ainv‖ ^ 2))
          atTop (𝓝 0) := by
      simpa using hmul
    refine hmul0.congr' ?_
    exact Eventually.of_forall fun N => by
      change
        B *
            ((N : ℝ)⁻¹ *
              ∑ k ∈ Finset.Ico 1 N,
                ‖chewi123SourceNoiseCoefficient A (chewi125PowerStep gamma) k N -
                  Ainv‖ ^ 2) =
          ∑ k ∈ Finset.Ico 1 N,
            ((N : ℝ)⁻¹ * B) *
              ‖chewi123SourceNoiseCoefficient A (chewi125PowerStep gamma) k N -
                Ainv‖ ^ 2
      rw [← Finset.mul_sum]
      ring
  exact
    integral_norm_sq_finset_sum_tendsto_zero_of_pairwise_integral_inner_zero
      (s := fun N => Finset.Ico 1 N)
      (Y := fun N k ω =>
        (Real.sqrt (N : ℝ))⁻¹ •
          ((chewi123SourceNoiseCoefficient A (chewi125PowerStep gamma) k N -
            Ainv) (xi k ω)))
      (B := fun N k =>
        (N : ℝ)⁻¹ * B *
          ‖chewi123SourceNoiseCoefficient A (chewi125PowerStep gamma) k N -
            Ainv‖ ^ (2 : ℕ))
      hinner_int horth hdiag_le hB_tendsto

/--
Diagonal second-moment bound for a scaled continuous-linear image.  This is
the pointwise analytic estimate used to discharge the diagonal term in the
Chewi ASGD Hilbert/L2 orthogonality argument.
-/
theorem scaled_linear_image_integral_norm_sq_le_of_integral_norm_sq_le
    {Ω E : Type*} [MeasurableSpace Ω] {P : Measure Ω}
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    (T : E →L[ℝ] E) (xi : Ω -> E) {B : ℝ} {N : ℕ}
    (hN : 0 < N)
    (hxi_int : Integrable (fun ω => ‖xi ω‖ ^ (2 : ℕ)) P)
    (hxi_le : ∫ ω, ‖xi ω‖ ^ (2 : ℕ) ∂P ≤ B) :
    ∫ ω, ‖(Real.sqrt (N : ℝ))⁻¹ • T (xi ω)‖ ^ (2 : ℕ) ∂P ≤
      (N : ℝ)⁻¹ * B * ‖T‖ ^ (2 : ℕ) := by
  have hNreal : 0 < (N : ℝ) := Nat.cast_pos.mpr hN
  have hnormc :
      ‖(Real.sqrt (N : ℝ))⁻¹‖ ^ (2 : ℕ) = (N : ℝ)⁻¹ := by
    rw [Real.norm_of_nonneg (inv_nonneg.mpr (Real.sqrt_nonneg _))]
    rw [inv_pow]
    rw [Real.sq_sqrt hNreal.le]
  let a : ℝ := (N : ℝ)⁻¹ * ‖T‖ ^ (2 : ℕ)
  have ha_nonneg : 0 ≤ a := by
    exact mul_nonneg (inv_nonneg.mpr (Nat.cast_nonneg N)) (sq_nonneg _)
  have hleft_nonneg :
      0 ≤ᵐ[P] fun ω => ‖(Real.sqrt (N : ℝ))⁻¹ • T (xi ω)‖ ^ (2 : ℕ) :=
    Eventually.of_forall fun ω => sq_nonneg _
  have hrhs_int : Integrable (fun ω => a * ‖xi ω‖ ^ (2 : ℕ)) P :=
    hxi_int.const_mul a
  have hpoint :
      (fun ω => ‖(Real.sqrt (N : ℝ))⁻¹ • T (xi ω)‖ ^ (2 : ℕ)) ≤ᵐ[P]
        fun ω => a * ‖xi ω‖ ^ (2 : ℕ) := by
    exact Eventually.of_forall fun ω => by
      have hT : ‖T (xi ω)‖ ≤ ‖T‖ * ‖xi ω‖ := T.le_opNorm (xi ω)
      have hT_sq :
          ‖T (xi ω)‖ ^ (2 : ℕ) ≤ (‖T‖ * ‖xi ω‖) ^ (2 : ℕ) :=
        pow_le_pow_left₀ (norm_nonneg _) hT 2
      have hT_sq' :
          ‖T (xi ω)‖ ^ (2 : ℕ) ≤ ‖T‖ ^ (2 : ℕ) * ‖xi ω‖ ^ (2 : ℕ) := by
        simpa [mul_pow] using hT_sq
      calc
        ‖(Real.sqrt (N : ℝ))⁻¹ • T (xi ω)‖ ^ (2 : ℕ)
            = ‖(Real.sqrt (N : ℝ))⁻¹‖ ^ (2 : ℕ) *
                ‖T (xi ω)‖ ^ (2 : ℕ) := by
              rw [norm_smul, mul_pow]
        _ ≤ (N : ℝ)⁻¹ * (‖T‖ ^ (2 : ℕ) * ‖xi ω‖ ^ (2 : ℕ)) := by
              rw [hnormc]
              exact mul_le_mul_of_nonneg_left hT_sq'
                (inv_nonneg.mpr (Nat.cast_nonneg N))
        _ = a * ‖xi ω‖ ^ (2 : ℕ) := by
              simp [a]
              ring
  have hmain :
      ∫ ω, ‖(Real.sqrt (N : ℝ))⁻¹ • T (xi ω)‖ ^ (2 : ℕ) ∂P ≤
        ∫ ω, a * ‖xi ω‖ ^ (2 : ℕ) ∂P :=
    integral_mono_of_nonneg hleft_nonneg hrhs_int hpoint
  calc
    ∫ ω, ‖(Real.sqrt (N : ℝ))⁻¹ • T (xi ω)‖ ^ (2 : ℕ) ∂P
        ≤ ∫ ω, a * ‖xi ω‖ ^ (2 : ℕ) ∂P := hmain
    _ = a * ∫ ω, ‖xi ω‖ ^ (2 : ℕ) ∂P := by
          rw [integral_const_mul]
    _ ≤ a * B :=
          mul_le_mul_of_nonneg_left hxi_le ha_nonneg
    _ = (N : ℝ)⁻¹ * B * ‖T‖ ^ (2 : ℕ) := by
          simp [a]
          ring

/--
Square integrability is preserved by deterministic scaled continuous linear
images.  This is the integrability counterpart of
`scaled_linear_image_integral_norm_sq_le_of_integral_norm_sq_le`.
-/
theorem scaled_linear_image_integrable_norm_sq_of_integrable_norm_sq
    {Ω E : Type*} [MeasurableSpace Ω] {P : Measure Ω}
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    (T : E →L[ℝ] E) (xi : Ω -> E) (c : ℝ)
    (hxi_meas : AEStronglyMeasurable xi P)
    (hxi_int : Integrable (fun ω => ‖xi ω‖ ^ (2 : ℕ)) P) :
    Integrable (fun ω => ‖c • T (xi ω)‖ ^ (2 : ℕ)) P := by
  have hxi_mem : MemLp xi (2 : ℝ≥0∞) P :=
    (memLp_two_iff_integrable_sq_norm hxi_meas).2 (by simpa using hxi_int)
  let L : E →L[ℝ] E := c • T
  have hscaled_mem : MemLp (fun ω => L (xi ω)) (2 : ℝ≥0∞) P := by
    simpa [Function.comp_def] using hxi_mem.continuousLinearMap_comp L
  have hscaled_int :
      Integrable (fun ω => ‖L (xi ω)‖ ^ (2 : ℕ)) P :=
    hscaled_mem.integrable_norm_pow (by norm_num : (2 : ℕ) ≠ 0)
  simpa [L] using hscaled_int

/--
Diagonal bound for one Chewi ASGD scaled coefficient-residual summand from a
uniform second-moment bound on the noise increment.
-/
theorem chewi123ASGD_scaled_residual_summand_integral_norm_sq_le_of_noise_integral_norm_sq_le
    {Ω E : Type*} [MeasurableSpace Ω] {P : Measure Ω}
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    (A Ainv : E →L[ℝ] E) (h : ℕ -> ℝ) (xi : ℕ -> Ω -> E) {B : ℝ}
    (hxi_int : ∀ k, Integrable (fun ω => ‖xi k ω‖ ^ (2 : ℕ)) P)
    (hxi_le : ∀ k, ∫ ω, ‖xi k ω‖ ^ (2 : ℕ) ∂P ≤ B)
    (N k : ℕ) (hk : k ∈ Finset.Ico 1 N) :
    ∫ ω,
        ‖(Real.sqrt (N : ℝ))⁻¹ •
          ((chewi123SourceNoiseCoefficient A h k N - Ainv) (xi k ω))‖ ^ (2 : ℕ) ∂P ≤
      (N : ℝ)⁻¹ * B *
        ‖chewi123SourceNoiseCoefficient A h k N - Ainv‖ ^ (2 : ℕ) := by
  have hN : 0 < N := by
    have hk_bounds := Finset.mem_Ico.mp hk
    omega
  exact scaled_linear_image_integral_norm_sq_le_of_integral_norm_sq_le
    (P := P)
    (T := chewi123SourceNoiseCoefficient A h k N - Ainv)
    (xi := xi k)
    (B := B)
    (N := N)
    hN (hxi_int k) (hxi_le k)

/--
Cross-inner integrability for two Chewi ASGD scaled coefficient-residual
summands follows from square-integrability of the corresponding noise
increments.
-/
theorem chewi123ASGD_scaled_residual_cross_integrable_of_noise_integrable_norm_sq
    {Ω E : Type*} [MeasurableSpace Ω] {P : Measure Ω}
    [NormedAddCommGroup E] [InnerProductSpace ℝ E]
    (A Ainv : E →L[ℝ] E) (h : ℕ -> ℝ) (xi : ℕ -> Ω -> E)
    (hxi_meas : ∀ k, AEStronglyMeasurable (xi k) P)
    (hxi_int : ∀ k, Integrable (fun ω => ‖xi k ω‖ ^ (2 : ℕ)) P)
    (N k : ℕ) (_hk : k ∈ Finset.Ico 1 N) (j : ℕ) (_hj : j ∈ Finset.Ico 1 N) :
    Integrable
      (fun ω =>
        inner ℝ
          ((Real.sqrt (N : ℝ))⁻¹ •
            ((chewi123SourceNoiseCoefficient A h k N - Ainv) (xi k ω)))
          ((Real.sqrt (N : ℝ))⁻¹ •
            ((chewi123SourceNoiseCoefficient A h j N - Ainv) (xi j ω)))) P := by
  let Tk : E →L[ℝ] E :=
    (Real.sqrt (N : ℝ))⁻¹ •
      (chewi123SourceNoiseCoefficient A h k N - Ainv)
  let Tj : E →L[ℝ] E :=
    (Real.sqrt (N : ℝ))⁻¹ •
      (chewi123SourceNoiseCoefficient A h j N - Ainv)
  have hk_meas :
      AEStronglyMeasurable (fun ω => Tk (xi k ω)) P :=
    Tk.continuous.comp_aestronglyMeasurable (hxi_meas k)
  have hj_meas :
      AEStronglyMeasurable (fun ω => Tj (xi j ω)) P :=
    Tj.continuous.comp_aestronglyMeasurable (hxi_meas j)
  have hk_int :
      Integrable (fun ω => ‖Tk (xi k ω)‖ ^ (2 : ℕ)) P := by
    simpa [Tk] using
      scaled_linear_image_integrable_norm_sq_of_integrable_norm_sq
        (P := P)
        (T := chewi123SourceNoiseCoefficient A h k N - Ainv)
        (xi := xi k)
        (c := (Real.sqrt (N : ℝ))⁻¹)
        (hxi_meas k) (hxi_int k)
  have hj_int :
      Integrable (fun ω => ‖Tj (xi j ω)‖ ^ (2 : ℕ)) P := by
    simpa [Tj] using
      scaled_linear_image_integrable_norm_sq_of_integrable_norm_sq
        (P := P)
        (T := chewi123SourceNoiseCoefficient A h j N - Ainv)
        (xi := xi j)
        (c := (Real.sqrt (N : ℝ))⁻¹)
        (hxi_meas j) (hxi_int j)
  have hinner :
      Integrable (fun ω => inner ℝ (Tk (xi k ω)) (Tj (xi j ω))) P :=
    integrable_inner_of_integrable_norm_sq
      hk_meas hj_meas hk_int hj_int
  simpa [Tk, Tj] using hinner

/--
The Chewi ASGD scaled residual sum is in L2 whenever each noise increment has a
finite second moment.
-/
theorem chewi123ASGD_scaled_residual_sum_memLp_two_of_noise_integrable_norm_sq
    {Ω E : Type*} [MeasurableSpace Ω] {P : Measure Ω}
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    (A Ainv : E →L[ℝ] E) (h : ℕ -> ℝ) (xi : ℕ -> Ω -> E)
    (hxi_meas : ∀ k, AEStronglyMeasurable (xi k) P)
    (hxi_int : ∀ k, Integrable (fun ω => ‖xi k ω‖ ^ (2 : ℕ)) P)
    (N : ℕ) :
    MemLp
      (fun ω =>
        ∑ k ∈ Finset.Ico 1 N,
          (Real.sqrt (N : ℝ))⁻¹ •
            ((chewi123SourceNoiseCoefficient A h k N - Ainv) (xi k ω)))
      (2 : ℝ≥0∞) P := by
  have hxi_mem : ∀ k, MemLp (xi k) (2 : ℝ≥0∞) P := fun k =>
    (memLp_two_iff_integrable_sq_norm (hxi_meas k)).2 (by simpa using hxi_int k)
  refine memLp_finsetSum (Finset.Ico 1 N) ?_
  intro k _hk
  let L : E →L[ℝ] E :=
    (Real.sqrt (N : ℝ))⁻¹ •
      (chewi123SourceNoiseCoefficient A h k N - Ainv)
  simpa [Function.comp_def, L] using (hxi_mem k).continuousLinearMap_comp L

/--
The endpoint-corrected ASGD remainder is in L2 under finite noise second
moments.  This supplies the `MemLp` side of the `o_P(1)` bridge.
-/
theorem chewi123ASGDEndpointCorrectedRemainder_memLp_two_of_noise_integrable_norm_sq
    {Ω E : Type*} [MeasurableSpace Ω] {P : Measure Ω}
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    (A Ainv : E →L[ℝ] E) (h : ℕ -> ℝ) (xi : ℕ -> Ω -> E)
    (hxi_meas : ∀ k, AEStronglyMeasurable (xi k) P)
    (hxi_int : ∀ k, Integrable (fun ω => ‖xi k ω‖ ^ (2 : ℕ)) P)
    (N : ℕ) :
    MemLp
      (fun ω => chewi123ASGDEndpointCorrectedRemainder A Ainv h
        (fun n => xi n ω) N) (2 : ℝ≥0∞) P := by
  have hxi_mem : ∀ k, MemLp (xi k) (2 : ℝ≥0∞) P := fun k =>
    (memLp_two_iff_integrable_sq_norm (hxi_meas k)).2 (by simpa using hxi_int k)
  have hend :
      MemLp (fun ω => (Real.sqrt (N : ℝ))⁻¹ • Ainv (xi N ω))
        (2 : ℝ≥0∞) P := by
    let L : E →L[ℝ] E := (Real.sqrt (N : ℝ))⁻¹ • Ainv
    simpa [Function.comp_def, L] using (hxi_mem N).continuousLinearMap_comp L
  have hsum :
      MemLp
        (fun ω =>
          (Real.sqrt (N : ℝ))⁻¹ •
            ∑ k ∈ Finset.Ico 1 N,
              (chewi123SourceNoiseCoefficient A h k N - Ainv) (xi k ω))
        (2 : ℝ≥0∞) P := by
    have hsum_inner :
        MemLp
          (fun ω =>
            ∑ k ∈ Finset.Ico 1 N,
              (chewi123SourceNoiseCoefficient A h k N - Ainv) (xi k ω))
          (2 : ℝ≥0∞) P := by
      refine memLp_finsetSum (Finset.Ico 1 N) ?_
      intro k _hk
      let L : E →L[ℝ] E := chewi123SourceNoiseCoefficient A h k N - Ainv
      simpa [Function.comp_def, L] using (hxi_mem k).continuousLinearMap_comp L
    simpa [Pi.smul_apply] using hsum_inner.const_smul (Real.sqrt (N : ℝ))⁻¹
  have hsub := hend.sub hsum
  simpa [chewi123ASGDEndpointCorrectedRemainder] using hsub

/--
Chewi ASGD residual-sum second-moment convergence with the diagonal
second-moment bound discharged from a uniform noise second-moment hypothesis.
The remaining assumptions are the integrability and zero cross-inner-product
conditions supplied by the martingale/orthogonality layer.
-/
theorem chewi123ASGD_scaled_residual_sum_integral_norm_sq_tendsto_zero_of_noise_integral_norm_sq_le
    {Ω E : Type*} [MeasurableSpace Ω] {P : Measure Ω}
    [NormedAddCommGroup E] [InnerProductSpace ℝ E] [CompleteSpace E]
    (A Ainv : E →L[ℝ] E) (xi : ℕ -> Ω -> E) {alpha gamma C B : ℝ}
    (hleft : Ainv * A = 1)
    (halpha : 0 < alpha) (hgamma_pos : 0 < gamma) (hgamma_lt : gamma < 1)
    (hcoeff_bound : ∀ N k, k ∈ Finset.Ico 1 N ->
      ‖chewi123SourceNoiseCoefficient A (chewi125PowerStep gamma) k N - Ainv‖ ≤ C)
    (hstep : ∀ m, 2 ≤ m ->
      ‖chewi123QuadraticStepMap (chewi125PowerStep gamma m) A‖ ≤
        1 - alpha * chewi125PowerStep gamma m)
    (hsmall : ∀ m, 2 ≤ m ->
      0 ≤ 1 - alpha * chewi125PowerStep gamma m)
    (hxi_int : ∀ k, Integrable (fun ω => ‖xi k ω‖ ^ (2 : ℕ)) P)
    (hxi_le : ∀ k, ∫ ω, ‖xi k ω‖ ^ (2 : ℕ) ∂P ≤ B)
    (hinner_int : ∀ (N k : ℕ), k ∈ Finset.Ico 1 N -> ∀ (j : ℕ), j ∈ Finset.Ico 1 N ->
      Integrable
        (fun ω =>
          inner ℝ
            ((Real.sqrt (N : ℝ))⁻¹ •
              ((chewi123SourceNoiseCoefficient A (chewi125PowerStep gamma) k N -
                Ainv) (xi k ω)))
            ((Real.sqrt (N : ℝ))⁻¹ •
              ((chewi123SourceNoiseCoefficient A (chewi125PowerStep gamma) j N -
                Ainv) (xi j ω)))) P)
    (horth : ∀ (N k : ℕ), k ∈ Finset.Ico 1 N -> ∀ (j : ℕ), j ∈ Finset.Ico 1 N ->
      k ≠ j ->
      ∫ ω,
          inner ℝ
            ((Real.sqrt (N : ℝ))⁻¹ •
              ((chewi123SourceNoiseCoefficient A (chewi125PowerStep gamma) k N -
                Ainv) (xi k ω)))
            ((Real.sqrt (N : ℝ))⁻¹ •
              ((chewi123SourceNoiseCoefficient A (chewi125PowerStep gamma) j N -
                Ainv) (xi j ω))) ∂P = 0) :
    Tendsto
      (fun N : ℕ =>
        ∫ ω,
          ‖∑ k ∈ Finset.Ico 1 N,
            (Real.sqrt (N : ℝ))⁻¹ •
              ((chewi123SourceNoiseCoefficient A (chewi125PowerStep gamma) k N -
                Ainv) (xi k ω))‖ ^ (2 : ℕ) ∂P)
      atTop (𝓝 0) := by
  exact
    chewi123ASGD_scaled_residual_sum_integral_norm_sq_tendsto_zero_of_pairwise_integral_inner_zero
      A Ainv xi hleft halpha hgamma_pos hgamma_lt hcoeff_bound hstep hsmall
      hinner_int horth
      (fun N k hk =>
        chewi123ASGD_scaled_residual_summand_integral_norm_sq_le_of_noise_integral_norm_sq_le
          A Ainv (chewi125PowerStep gamma) xi hxi_int hxi_le N k hk)

/--
The endpoint correction term `(sqrt N)^{-1} A^{-1} ξ_N` has vanishing second
moment under the same uniform second-moment noise bound used for the residual
sum.
-/
theorem chewi123ASGD_endpoint_integral_norm_sq_tendsto_zero_of_noise_integral_norm_sq_le
    {Ω E : Type*} [MeasurableSpace Ω] {P : Measure Ω}
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    (Ainv : E →L[ℝ] E) (xi : ℕ -> Ω -> E) {B : ℝ}
    (hxi_int : ∀ k, Integrable (fun ω => ‖xi k ω‖ ^ (2 : ℕ)) P)
    (hxi_le : ∀ k, ∫ ω, ‖xi k ω‖ ^ (2 : ℕ) ∂P ≤ B) :
    Tendsto
      (fun N : ℕ =>
        ∫ ω, ‖(Real.sqrt (N : ℝ))⁻¹ • Ainv (xi N ω)‖ ^ (2 : ℕ) ∂P)
      atTop (𝓝 0) := by
  have hupper_tendsto :
      Tendsto
        (fun N : ℕ => (N : ℝ)⁻¹ * B * ‖Ainv‖ ^ (2 : ℕ))
        atTop (𝓝 0) := by
    have hinv : Tendsto (fun N : ℕ => ((N : ℝ)⁻¹ : ℝ)) atTop (𝓝 0) :=
      tendsto_inv_atTop_nhds_zero_nat
    have hmul :
        Tendsto
          (fun N : ℕ => ((N : ℝ)⁻¹ : ℝ) * (B * ‖Ainv‖ ^ (2 : ℕ)))
          atTop (𝓝 (0 * (B * ‖Ainv‖ ^ (2 : ℕ)))) :=
      hinv.mul tendsto_const_nhds
    have hmul0 :
        Tendsto
          (fun N : ℕ => ((N : ℝ)⁻¹ : ℝ) * (B * ‖Ainv‖ ^ (2 : ℕ)))
          atTop (𝓝 0) := by
      simpa using hmul
    refine hmul0.congr' ?_
    exact Eventually.of_forall fun N => by ring
  refine tendsto_of_tendsto_of_tendsto_of_le_of_le' tendsto_const_nhds
    hupper_tendsto ?_ ?_
  · exact Eventually.of_forall fun N =>
      integral_nonneg fun ω => sq_nonneg _
  · filter_upwards [eventually_gt_atTop (0 : ℕ)] with N hN
    exact scaled_linear_image_integral_norm_sq_le_of_integral_norm_sq_le
      (P := P)
      (T := Ainv)
      (xi := xi N)
      (B := B)
      (N := N)
      hN (hxi_int N) (hxi_le N)

/--
Conditional-expectation Hilbert orthogonality primitive.  An
`m`-measurable left factor has zero integral against a right factor whose
conditional expectation onto `m` is zero.
-/
theorem integral_inner_eq_zero_of_aestronglyMeasurable_left_condExp_right_eq_zero
    {Ω E : Type*} [mΩ : MeasurableSpace Ω] {P : Measure Ω}
    [IsProbabilityMeasure P]
    [NormedAddCommGroup E] [InnerProductSpace ℝ E] [CompleteSpace E]
    (m : MeasurableSpace Ω) (hm : m ≤ mΩ)
    (f g : Ω -> E)
    (hf : AEStronglyMeasurable[m] f P)
    (hfg : Integrable (fun ω => inner ℝ (f ω) (g ω)) P)
    (hg : Integrable g P)
    (hg_zero : P[g | m] =ᵐ[P] fun _ => 0) :
    (∫ ω, inner ℝ (f ω) (g ω) ∂P) = 0 := by
  let B : E →L[ℝ] E →L[ℝ] ℝ :=
    (isBoundedBilinearMap_inner (𝕜 := ℝ) (E := E)).toContinuousLinearMap
  have hcond :
      P[fun ω => B (f ω) (g ω) | m] =ᵐ[P]
        fun ω => B (f ω) (P[g | m] ω) :=
    condExp_bilin_of_aestronglyMeasurable_left
      (μ := P) (m := m) (B := B) hf hfg hg
  calc
    (∫ ω, inner ℝ (f ω) (g ω) ∂P)
        = ∫ ω, P[fun ω => B (f ω) (g ω) | m] ω ∂P := by
          rw [integral_condExp (m := m) (m₀ := mΩ) (μ := P)
            (f := fun ω => B (f ω) (g ω)) hm]
          simp [B]
    _ = ∫ ω, B (f ω) (P[g | m] ω) ∂P :=
          integral_congr_ae hcond
    _ = ∫ _ω, (0 : ℝ) ∂P := by
          refine integral_congr_ae ?_
          filter_upwards [hg_zero] with ω hω
          simp [B, hω]
    _ = 0 := by simp

/--
The martingale-difference conditional mean-zero property is preserved by a
deterministic continuous linear map.
-/
theorem Chewi127MartingaleDifferenceProcess.condExp_linearMap_next_eq_zero
    {Ω E : Type*} [mΩ : MeasurableSpace Ω] {P : Measure Ω}
    [IsProbabilityMeasure P]
    [NormedAddCommGroup E] [NormedSpace ℝ E] [CompleteSpace E]
    (M : Chewi127MartingaleDifferenceProcess Ω E P)
    (T : E →L[ℝ] E) (n : ℕ) :
    P[fun ω => T (M.xi (n + 1) ω) | M.filtration n]
      =ᵐ[P] fun _ => 0 := by
  have hcomm :
      (fun ω => T (P[M.xi (n + 1) | M.filtration n] ω))
        =ᵐ[P] P[fun ω => T (M.xi (n + 1) ω) | M.filtration n] := by
    simpa [Function.comp_def] using
      (ContinuousLinearMap.comp_condExp_comm
        (μ := P) (m := M.filtration n) (f := M.xi (n + 1))
        (T := T) (M.integrable (n + 1)))
  exact hcomm.symm.trans <|
    (M.condExp_zero n).mono fun ω hω => by simp [hω]

/--
Earlier adapted linear images are orthogonal in expectation to later
martingale-difference linear images.
-/
theorem Chewi127MartingaleDifferenceProcess.integral_inner_linear_image_next_eq_zero
    {Ω E : Type*} [mΩ : MeasurableSpace Ω] {P : Measure Ω}
    [IsProbabilityMeasure P]
    [NormedAddCommGroup E] [InnerProductSpace ℝ E] [CompleteSpace E]
    (M : Chewi127MartingaleDifferenceProcess Ω E P)
    (Tprev Tnext : E →L[ℝ] E) (j n : ℕ) (hj : j ≤ n)
    (hinner_int :
      Integrable
        (fun ω => inner ℝ (Tprev (M.xi j ω)) (Tnext (M.xi (n + 1) ω))) P) :
    (∫ ω, inner ℝ (Tprev (M.xi j ω)) (Tnext (M.xi (n + 1) ω)) ∂P) = 0 := by
  have hf_strong :
      StronglyMeasurable[M.filtration n] (fun ω => Tprev (M.xi j ω)) :=
    Tprev.continuous.comp_stronglyMeasurable
      (M.adapted.stronglyMeasurable_le hj)
  have hg_int : Integrable (fun ω => Tnext (M.xi (n + 1) ω)) P :=
    Tnext.integrable_comp (M.integrable (n + 1))
  exact
    integral_inner_eq_zero_of_aestronglyMeasurable_left_condExp_right_eq_zero
      (P := P)
      (m := M.filtration n)
      (hm := M.filtration.le n)
      (f := fun ω => Tprev (M.xi j ω))
      (g := fun ω => Tnext (M.xi (n + 1) ω))
      hf_strong.aestronglyMeasurable hinner_int hg_int
      (M.condExp_linearMap_next_eq_zero Tnext n)

/--
Pairwise version of martingale-difference linear-image orthogonality for any
two distinct time indices.
-/
theorem Chewi127MartingaleDifferenceProcess.integral_inner_linear_image_eq_zero_of_ne
    {Ω E : Type*} [mΩ : MeasurableSpace Ω] {P : Measure Ω}
    [IsProbabilityMeasure P]
    [NormedAddCommGroup E] [InnerProductSpace ℝ E] [CompleteSpace E]
    (M : Chewi127MartingaleDifferenceProcess Ω E P)
    (T : ℕ -> E →L[ℝ] E) {i j : ℕ} (hij_ne : i ≠ j)
    (hinner_int :
      Integrable
        (fun ω => inner ℝ (T i (M.xi i ω)) (T j (M.xi j ω))) P) :
    (∫ ω, inner ℝ (T i (M.xi i ω)) (T j (M.xi j ω)) ∂P) = 0 := by
  rcases lt_or_gt_of_ne hij_ne with hij | hji
  · have hjpos : 0 < j := by omega
    have hijle : i ≤ j - 1 := by omega
    have hsucc : j - 1 + 1 = j := by omega
    have hzero :=
      M.integral_inner_linear_image_next_eq_zero
        (Tprev := T i) (Tnext := T j) (j := i) (n := j - 1)
        hijle
        (by simpa [hsucc] using hinner_int)
    simpa [hsucc] using hzero
  · have hipos : 0 < i := by omega
    have hjle : j ≤ i - 1 := by omega
    have hsucc : i - 1 + 1 = i := by omega
    have hrev_int :
        Integrable
          (fun ω => inner ℝ (T j (M.xi j ω)) (T i (M.xi i ω))) P := by
      exact (integrable_congr (ae_of_all P fun ω => by rw [real_inner_comm])).mp hinner_int
    have hzero :=
      M.integral_inner_linear_image_next_eq_zero
        (Tprev := T j) (Tnext := T i) (j := j) (n := i - 1)
        hjle
        (by simpa [hsucc] using hrev_int)
    have hzero' :
        (∫ ω, inner ℝ (T j (M.xi j ω)) (T i (M.xi i ω)) ∂P) = 0 := by
      simpa [hsucc] using hzero
    calc
      (∫ ω, inner ℝ (T i (M.xi i ω)) (T j (M.xi j ω)) ∂P)
          = ∫ ω, inner ℝ (T j (M.xi j ω)) (T i (M.xi i ω)) ∂P := by
            refine integral_congr_ae (ae_of_all P fun ω => ?_)
            simpa using (real_inner_comm (T i (M.xi i ω)) (T j (M.xi j ω))).symm
      _ = 0 := hzero'

/--
Chewi ASGD scaled residual cross terms have zero integral when the noise comes
from the source martingale-difference process.  The remaining supplied input
is only the cross-inner integrability needed to state the Bochner integral.
-/
theorem Chewi127MartingaleDifferenceProcess.chewi123ASGD_scaled_residual_cross_integral_eq_zero
    {Ω E : Type*} [mΩ : MeasurableSpace Ω] {P : Measure Ω}
    [IsProbabilityMeasure P]
    [NormedAddCommGroup E] [InnerProductSpace ℝ E] [CompleteSpace E]
    (M : Chewi127MartingaleDifferenceProcess Ω E P)
    (A Ainv : E →L[ℝ] E) {gamma : ℝ} {N k j : ℕ}
    (hkj_ne : k ≠ j)
    (hinner_int :
      Integrable
        (fun ω =>
          inner ℝ
            ((Real.sqrt (N : ℝ))⁻¹ •
              ((chewi123SourceNoiseCoefficient A (chewi125PowerStep gamma) k N -
                Ainv) (M.xi k ω)))
            ((Real.sqrt (N : ℝ))⁻¹ •
              ((chewi123SourceNoiseCoefficient A (chewi125PowerStep gamma) j N -
                Ainv) (M.xi j ω)))) P) :
    (∫ ω,
        inner ℝ
          ((Real.sqrt (N : ℝ))⁻¹ •
            ((chewi123SourceNoiseCoefficient A (chewi125PowerStep gamma) k N -
              Ainv) (M.xi k ω)))
          ((Real.sqrt (N : ℝ))⁻¹ •
            ((chewi123SourceNoiseCoefficient A (chewi125PowerStep gamma) j N -
              Ainv) (M.xi j ω))) ∂P) = 0 := by
  let T : ℕ -> E →L[ℝ] E := fun r =>
    (Real.sqrt (N : ℝ))⁻¹ •
      (chewi123SourceNoiseCoefficient A (chewi125PowerStep gamma) r N - Ainv)
  have hzero :=
    M.integral_inner_linear_image_eq_zero_of_ne
      (T := T) hkj_ne (by simpa [T] using hinner_int)
  simpa [T] using hzero

/--
For a Chewi source martingale-difference process, the scaled residual
cross-inner terms are integrable under the same square-integrability hypothesis
used for the diagonal bounds.
-/
theorem Chewi127MartingaleDifferenceProcess.chewi123ASGD_scaled_residual_cross_integrable_of_noise_integrable_norm_sq
    {Ω E : Type*} [mΩ : MeasurableSpace Ω] {P : Measure Ω}
    [IsProbabilityMeasure P]
    [NormedAddCommGroup E] [InnerProductSpace ℝ E] [CompleteSpace E]
    (M : Chewi127MartingaleDifferenceProcess Ω E P)
    (A Ainv : E →L[ℝ] E) {gamma : ℝ}
    (hxi_int : ∀ k, Integrable (fun ω => ‖M.xi k ω‖ ^ (2 : ℕ)) P)
    (N k : ℕ) (hk : k ∈ Finset.Ico 1 N) (j : ℕ) (hj : j ∈ Finset.Ico 1 N) :
    Integrable
      (fun ω =>
        inner ℝ
          ((Real.sqrt (N : ℝ))⁻¹ •
            ((chewi123SourceNoiseCoefficient A (chewi125PowerStep gamma) k N -
              Ainv) (M.xi k ω)))
          ((Real.sqrt (N : ℝ))⁻¹ •
            ((chewi123SourceNoiseCoefficient A (chewi125PowerStep gamma) j N -
              Ainv) (M.xi j ω)))) P := by
  exact
    _root_.StatInference.Optimization.chewi123ASGD_scaled_residual_cross_integrable_of_noise_integrable_norm_sq
      (P := P)
      A Ainv (chewi125PowerStep gamma) M.xi
      (fun r => (M.integrable r).aestronglyMeasurable)
      hxi_int N k hk j hj

/--
Chewi ASGD residual-sum second-moment convergence with the cross-term
orthogonality discharged from the source martingale-difference process.
Only cross-inner integrability remains explicit.
-/
theorem chewi123ASGD_scaled_residual_sum_integral_norm_sq_tendsto_zero_of_martingale_difference_noise_integral_norm_sq_le
    {Ω E : Type*} [mΩ : MeasurableSpace Ω] {P : Measure Ω}
    [IsProbabilityMeasure P]
    [NormedAddCommGroup E] [InnerProductSpace ℝ E] [CompleteSpace E]
    (M : Chewi127MartingaleDifferenceProcess Ω E P)
    (A Ainv : E →L[ℝ] E) {alpha gamma C B : ℝ}
    (hleft : Ainv * A = 1)
    (halpha : 0 < alpha) (hgamma_pos : 0 < gamma) (hgamma_lt : gamma < 1)
    (hcoeff_bound : ∀ N k, k ∈ Finset.Ico 1 N ->
      ‖chewi123SourceNoiseCoefficient A (chewi125PowerStep gamma) k N - Ainv‖ ≤ C)
    (hstep : ∀ m, 2 ≤ m ->
      ‖chewi123QuadraticStepMap (chewi125PowerStep gamma m) A‖ ≤
        1 - alpha * chewi125PowerStep gamma m)
    (hsmall : ∀ m, 2 ≤ m ->
      0 ≤ 1 - alpha * chewi125PowerStep gamma m)
    (hxi_int : ∀ k, Integrable (fun ω => ‖M.xi k ω‖ ^ (2 : ℕ)) P)
    (hxi_le : ∀ k, ∫ ω, ‖M.xi k ω‖ ^ (2 : ℕ) ∂P ≤ B)
    (hinner_int : ∀ (N k : ℕ), k ∈ Finset.Ico 1 N -> ∀ (j : ℕ), j ∈ Finset.Ico 1 N ->
      Integrable
        (fun ω =>
          inner ℝ
            ((Real.sqrt (N : ℝ))⁻¹ •
              ((chewi123SourceNoiseCoefficient A (chewi125PowerStep gamma) k N -
                Ainv) (M.xi k ω)))
            ((Real.sqrt (N : ℝ))⁻¹ •
              ((chewi123SourceNoiseCoefficient A (chewi125PowerStep gamma) j N -
                Ainv) (M.xi j ω)))) P) :
    Tendsto
      (fun N : ℕ =>
        ∫ ω,
          ‖∑ k ∈ Finset.Ico 1 N,
            (Real.sqrt (N : ℝ))⁻¹ •
              ((chewi123SourceNoiseCoefficient A (chewi125PowerStep gamma) k N -
                Ainv) (M.xi k ω))‖ ^ (2 : ℕ) ∂P)
      atTop (𝓝 0) := by
  exact
    chewi123ASGD_scaled_residual_sum_integral_norm_sq_tendsto_zero_of_noise_integral_norm_sq_le
      A Ainv M.xi hleft halpha hgamma_pos hgamma_lt hcoeff_bound hstep hsmall
      hxi_int hxi_le hinner_int
      (fun N k hk j hj hkj =>
        M.chewi123ASGD_scaled_residual_cross_integral_eq_zero
          A Ainv hkj (hinner_int N k hk j hj))

/--
Chewi ASGD residual-sum second-moment convergence from the martingale
difference source assumptions and a uniform square-moment noise bound.  Both
the diagonal estimates and cross-inner integrability/orthogonality are
discharged from source-shaped hypotheses.
-/
theorem chewi123ASGD_scaled_residual_sum_integral_norm_sq_tendsto_zero_of_martingale_difference_noise_second_moment_bound
    {Ω E : Type*} [mΩ : MeasurableSpace Ω] {P : Measure Ω}
    [IsProbabilityMeasure P]
    [NormedAddCommGroup E] [InnerProductSpace ℝ E] [CompleteSpace E]
    (M : Chewi127MartingaleDifferenceProcess Ω E P)
    (A Ainv : E →L[ℝ] E) {alpha gamma C B : ℝ}
    (hleft : Ainv * A = 1)
    (halpha : 0 < alpha) (hgamma_pos : 0 < gamma) (hgamma_lt : gamma < 1)
    (hcoeff_bound : ∀ N k, k ∈ Finset.Ico 1 N ->
      ‖chewi123SourceNoiseCoefficient A (chewi125PowerStep gamma) k N - Ainv‖ ≤ C)
    (hstep : ∀ m, 2 ≤ m ->
      ‖chewi123QuadraticStepMap (chewi125PowerStep gamma m) A‖ ≤
        1 - alpha * chewi125PowerStep gamma m)
    (hsmall : ∀ m, 2 ≤ m ->
      0 ≤ 1 - alpha * chewi125PowerStep gamma m)
    (hxi_int : ∀ k, Integrable (fun ω => ‖M.xi k ω‖ ^ (2 : ℕ)) P)
    (hxi_le : ∀ k, ∫ ω, ‖M.xi k ω‖ ^ (2 : ℕ) ∂P ≤ B) :
    Tendsto
      (fun N : ℕ =>
        ∫ ω,
          ‖∑ k ∈ Finset.Ico 1 N,
            (Real.sqrt (N : ℝ))⁻¹ •
              ((chewi123SourceNoiseCoefficient A (chewi125PowerStep gamma) k N -
                Ainv) (M.xi k ω))‖ ^ (2 : ℕ) ∂P)
      atTop (𝓝 0) := by
  exact
    chewi123ASGD_scaled_residual_sum_integral_norm_sq_tendsto_zero_of_martingale_difference_noise_integral_norm_sq_le
      M A Ainv hleft halpha hgamma_pos hgamma_lt hcoeff_bound hstep hsmall
      hxi_int hxi_le
      (fun N k hk j hj =>
        M.chewi123ASGD_scaled_residual_cross_integrable_of_noise_integrable_norm_sq
          A Ainv hxi_int N k hk j hj)

/--
The full endpoint-corrected Chewi ASGD remainder has vanishing second moment
under the martingale-difference source assumptions and the uniform noise
second-moment bound.
-/
theorem chewi123ASGDEndpointCorrectedRemainder_integral_norm_sq_tendsto_zero_of_martingale_difference_noise_second_moment_bound
    {Ω E : Type*} [mΩ : MeasurableSpace Ω] {P : Measure Ω}
    [IsProbabilityMeasure P]
    [NormedAddCommGroup E] [InnerProductSpace ℝ E] [CompleteSpace E]
    (M : Chewi127MartingaleDifferenceProcess Ω E P)
    (A Ainv : E →L[ℝ] E) {alpha gamma C B : ℝ}
    (hleft : Ainv * A = 1)
    (halpha : 0 < alpha) (hgamma_pos : 0 < gamma) (hgamma_lt : gamma < 1)
    (hcoeff_bound : ∀ N k, k ∈ Finset.Ico 1 N ->
      ‖chewi123SourceNoiseCoefficient A (chewi125PowerStep gamma) k N - Ainv‖ ≤ C)
    (hstep : ∀ m, 2 ≤ m ->
      ‖chewi123QuadraticStepMap (chewi125PowerStep gamma m) A‖ ≤
        1 - alpha * chewi125PowerStep gamma m)
    (hsmall : ∀ m, 2 ≤ m ->
      0 ≤ 1 - alpha * chewi125PowerStep gamma m)
    (hxi_int : ∀ k, Integrable (fun ω => ‖M.xi k ω‖ ^ (2 : ℕ)) P)
    (hxi_le : ∀ k, ∫ ω, ‖M.xi k ω‖ ^ (2 : ℕ) ∂P ≤ B) :
    Tendsto
      (fun N : ℕ =>
        ∫ ω,
          ‖chewi123ASGDEndpointCorrectedRemainder A Ainv
            (chewi125PowerStep gamma) (fun n => M.xi n ω) N‖ ^ (2 : ℕ) ∂P)
      atTop (𝓝 0) := by
  let U : ℕ -> Ω -> E := fun N ω =>
    (Real.sqrt (N : ℝ))⁻¹ • Ainv (M.xi N ω)
  let V : ℕ -> Ω -> E := fun N ω =>
    ∑ k ∈ Finset.Ico 1 N,
      (Real.sqrt (N : ℝ))⁻¹ •
        ((chewi123SourceNoiseCoefficient A (chewi125PowerStep gamma) k N -
          Ainv) (M.xi k ω))
  have hU_int : ∀ N, Integrable (fun ω => ‖U N ω‖ ^ (2 : ℕ)) P := by
    intro N
    simpa [U] using
      scaled_linear_image_integrable_norm_sq_of_integrable_norm_sq
        (P := P)
        (T := Ainv)
        (xi := M.xi N)
        (c := (Real.sqrt (N : ℝ))⁻¹)
        (M.integrable N).aestronglyMeasurable (hxi_int N)
  have hV_mem : ∀ N, MemLp (V N) (2 : ℝ≥0∞) P := by
    intro N
    simpa [V] using
      chewi123ASGD_scaled_residual_sum_memLp_two_of_noise_integrable_norm_sq
        (P := P)
        A Ainv (chewi125PowerStep gamma) M.xi
        (fun k => (M.integrable k).aestronglyMeasurable) hxi_int N
  have hV_int : ∀ N, Integrable (fun ω => ‖V N ω‖ ^ (2 : ℕ)) P := by
    intro N
    exact (hV_mem N).integrable_norm_pow (by norm_num : (2 : ℕ) ≠ 0)
  have hU_tend :
      Tendsto (fun N : ℕ => ∫ ω, ‖U N ω‖ ^ (2 : ℕ) ∂P) atTop (𝓝 0) := by
    simpa [U] using
      chewi123ASGD_endpoint_integral_norm_sq_tendsto_zero_of_noise_integral_norm_sq_le
        (P := P) Ainv M.xi hxi_int hxi_le
  have hV_tend :
      Tendsto (fun N : ℕ => ∫ ω, ‖V N ω‖ ^ (2 : ℕ) ∂P) atTop (𝓝 0) := by
    simpa [V] using
      chewi123ASGD_scaled_residual_sum_integral_norm_sq_tendsto_zero_of_martingale_difference_noise_second_moment_bound
        (P := P)
        M A Ainv hleft halpha hgamma_pos hgamma_lt hcoeff_bound hstep hsmall
        hxi_int hxi_le
  have hsub :
      Tendsto (fun N : ℕ => ∫ ω, ‖U N ω - V N ω‖ ^ (2 : ℕ) ∂P)
        atTop (𝓝 0) :=
    integral_norm_sq_sub_tendsto_zero_of_integral_norm_sq_tendsto_zero
      U V hU_int hV_int hU_tend hV_tend
  refine hsub.congr' ?_
  exact Eventually.of_forall fun N => by
    refine integral_congr_ae (ae_of_all P fun ω => ?_)
    have hV_eq :
        V N ω =
          (Real.sqrt (N : ℝ))⁻¹ •
            ∑ k ∈ Finset.Ico 1 N,
              (chewi123SourceNoiseCoefficient A (chewi125PowerStep gamma) k N -
                Ainv) (M.xi k ω) := by
      simp only [V, ContinuousLinearMap.sub_apply]
      rw [← Finset.smul_sum]
    simp [U, hV_eq, chewi123ASGDEndpointCorrectedRemainder]

/--
Endpoint-corrected Chewi ASGD stochastic remainder is `o_P(1)` under the
martingale-difference source assumptions and the uniform noise second-moment
bound.
-/
theorem chewi123ASGDEndpointCorrectedRemainder_tendstoInMeasure_zero_of_martingale_difference_noise_second_moment_bound
    {Ω E : Type*} [mΩ : MeasurableSpace Ω] {P : Measure Ω}
    [IsProbabilityMeasure P]
    [NormedAddCommGroup E] [InnerProductSpace ℝ E] [CompleteSpace E]
    (M : Chewi127MartingaleDifferenceProcess Ω E P)
    (A Ainv : E →L[ℝ] E) {alpha gamma C B : ℝ}
    (hleft : Ainv * A = 1)
    (halpha : 0 < alpha) (hgamma_pos : 0 < gamma) (hgamma_lt : gamma < 1)
    (hcoeff_bound : ∀ N k, k ∈ Finset.Ico 1 N ->
      ‖chewi123SourceNoiseCoefficient A (chewi125PowerStep gamma) k N - Ainv‖ ≤ C)
    (hstep : ∀ m, 2 ≤ m ->
      ‖chewi123QuadraticStepMap (chewi125PowerStep gamma m) A‖ ≤
        1 - alpha * chewi125PowerStep gamma m)
    (hsmall : ∀ m, 2 ≤ m ->
      0 ≤ 1 - alpha * chewi125PowerStep gamma m)
    (hxi_int : ∀ k, Integrable (fun ω => ‖M.xi k ω‖ ^ (2 : ℕ)) P)
    (hxi_le : ∀ k, ∫ ω, ‖M.xi k ω‖ ^ (2 : ℕ) ∂P ≤ B) :
    TendstoInMeasure P
      (fun N ω => chewi123ASGDEndpointCorrectedRemainder A Ainv
        (chewi125PowerStep gamma) (fun n => M.xi n ω) N)
      atTop (fun _ => 0) := by
  refine
    chewi123ASGDEndpointCorrectedRemainder_tendstoInMeasure_zero_of_integral_norm_sq_tendsto_zero
      (P := P) A Ainv (chewi125PowerStep gamma) M.xi ?_ ?_
  · intro N
    exact
      (chewi123ASGDEndpointCorrectedRemainder_memLp_two_of_noise_integrable_norm_sq
        (P := P)
        A Ainv (chewi125PowerStep gamma) M.xi
        (fun k => (M.integrable k).aestronglyMeasurable) hxi_int N).norm
  · exact
      chewi123ASGDEndpointCorrectedRemainder_integral_norm_sq_tendsto_zero_of_martingale_difference_noise_second_moment_bound
        (P := P)
        M A Ainv hleft halpha hgamma_pos hgamma_lt hcoeff_bound hstep hsmall
        hxi_int hxi_le

/--
Positive-index version of the diagonal bound.  This matches Chewi's ASGD
indexing: all stochastic terms in the residual sum have `1 ≤ k`.
-/
theorem chewi123ASGD_scaled_residual_summand_integral_norm_sq_le_of_noise_integral_norm_sq_le_of_pos
    {Ω E : Type*} [MeasurableSpace Ω] {P : Measure Ω}
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    (A Ainv : E →L[ℝ] E) (h : ℕ -> ℝ) (xi : ℕ -> Ω -> E) {B : ℝ}
    (hxi_int : ∀ k, 1 ≤ k ->
      Integrable (fun ω => ‖xi k ω‖ ^ (2 : ℕ)) P)
    (hxi_le : ∀ k, 1 ≤ k ->
      ∫ ω, ‖xi k ω‖ ^ (2 : ℕ) ∂P ≤ B)
    (N k : ℕ) (hk : k ∈ Finset.Ico 1 N) :
    ∫ ω,
        ‖(Real.sqrt (N : ℝ))⁻¹ •
          ((chewi123SourceNoiseCoefficient A h k N - Ainv) (xi k ω))‖ ^ (2 : ℕ) ∂P ≤
      (N : ℝ)⁻¹ * B *
        ‖chewi123SourceNoiseCoefficient A h k N - Ainv‖ ^ (2 : ℕ) := by
  have hN : 0 < N := by
    have hk_bounds := Finset.mem_Ico.mp hk
    omega
  have hk_pos : 1 ≤ k := (Finset.mem_Ico.mp hk).1
  exact scaled_linear_image_integral_norm_sq_le_of_integral_norm_sq_le
    (P := P)
    (T := chewi123SourceNoiseCoefficient A h k N - Ainv)
    (xi := xi k)
    (B := B)
    (N := N)
    hN (hxi_int k hk_pos) (hxi_le k hk_pos)

/--
Positive-index cross-inner integrability for Chewi ASGD residual summands.
-/
theorem chewi123ASGD_scaled_residual_cross_integrable_of_noise_integrable_norm_sq_of_pos
    {Ω E : Type*} [MeasurableSpace Ω] {P : Measure Ω}
    [NormedAddCommGroup E] [InnerProductSpace ℝ E]
    (A Ainv : E →L[ℝ] E) (h : ℕ -> ℝ) (xi : ℕ -> Ω -> E)
    (hxi_meas : ∀ k, AEStronglyMeasurable (xi k) P)
    (hxi_int : ∀ k, 1 ≤ k ->
      Integrable (fun ω => ‖xi k ω‖ ^ (2 : ℕ)) P)
    (N k : ℕ) (hk : k ∈ Finset.Ico 1 N) (j : ℕ) (hj : j ∈ Finset.Ico 1 N) :
    Integrable
      (fun ω =>
        inner ℝ
          ((Real.sqrt (N : ℝ))⁻¹ •
            ((chewi123SourceNoiseCoefficient A h k N - Ainv) (xi k ω)))
          ((Real.sqrt (N : ℝ))⁻¹ •
            ((chewi123SourceNoiseCoefficient A h j N - Ainv) (xi j ω)))) P := by
  let Tk : E →L[ℝ] E :=
    (Real.sqrt (N : ℝ))⁻¹ •
      (chewi123SourceNoiseCoefficient A h k N - Ainv)
  let Tj : E →L[ℝ] E :=
    (Real.sqrt (N : ℝ))⁻¹ •
      (chewi123SourceNoiseCoefficient A h j N - Ainv)
  have hk_meas :
      AEStronglyMeasurable (fun ω => Tk (xi k ω)) P :=
    Tk.continuous.comp_aestronglyMeasurable (hxi_meas k)
  have hj_meas :
      AEStronglyMeasurable (fun ω => Tj (xi j ω)) P :=
    Tj.continuous.comp_aestronglyMeasurable (hxi_meas j)
  have hk_pos : 1 ≤ k := (Finset.mem_Ico.mp hk).1
  have hj_pos : 1 ≤ j := (Finset.mem_Ico.mp hj).1
  have hk_int :
      Integrable (fun ω => ‖Tk (xi k ω)‖ ^ (2 : ℕ)) P := by
    simpa [Tk] using
      scaled_linear_image_integrable_norm_sq_of_integrable_norm_sq
        (P := P)
        (T := chewi123SourceNoiseCoefficient A h k N - Ainv)
        (xi := xi k)
        (c := (Real.sqrt (N : ℝ))⁻¹)
        (hxi_meas k) (hxi_int k hk_pos)
  have hj_int :
      Integrable (fun ω => ‖Tj (xi j ω)‖ ^ (2 : ℕ)) P := by
    simpa [Tj] using
      scaled_linear_image_integrable_norm_sq_of_integrable_norm_sq
        (P := P)
        (T := chewi123SourceNoiseCoefficient A h j N - Ainv)
        (xi := xi j)
        (c := (Real.sqrt (N : ℝ))⁻¹)
        (hxi_meas j) (hxi_int j hj_pos)
  have hinner :
      Integrable (fun ω => inner ℝ (Tk (xi k ω)) (Tj (xi j ω))) P :=
    integrable_inner_of_integrable_norm_sq hk_meas hj_meas hk_int hj_int
  simpa [Tk, Tj] using hinner

/--
Positive-index L2 membership for the Chewi ASGD scaled residual sum.
-/
theorem chewi123ASGD_scaled_residual_sum_memLp_two_of_noise_integrable_norm_sq_of_pos
    {Ω E : Type*} [MeasurableSpace Ω] {P : Measure Ω}
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    (A Ainv : E →L[ℝ] E) (h : ℕ -> ℝ) (xi : ℕ -> Ω -> E)
    (hxi_meas : ∀ k, AEStronglyMeasurable (xi k) P)
    (hxi_int : ∀ k, 1 ≤ k ->
      Integrable (fun ω => ‖xi k ω‖ ^ (2 : ℕ)) P)
    (N : ℕ) :
    MemLp
      (fun ω =>
        ∑ k ∈ Finset.Ico 1 N,
          (Real.sqrt (N : ℝ))⁻¹ •
            ((chewi123SourceNoiseCoefficient A h k N - Ainv) (xi k ω)))
      (2 : ℝ≥0∞) P := by
  have hxi_mem : ∀ k, 1 ≤ k -> MemLp (xi k) (2 : ℝ≥0∞) P := fun k hk =>
    (memLp_two_iff_integrable_sq_norm (hxi_meas k)).2 (by simpa using hxi_int k hk)
  refine memLp_finsetSum (Finset.Ico 1 N) ?_
  intro k hk
  let L : E →L[ℝ] E :=
    (Real.sqrt (N : ℝ))⁻¹ •
      (chewi123SourceNoiseCoefficient A h k N - Ainv)
  have hk_pos : 1 ≤ k := (Finset.mem_Ico.mp hk).1
  simpa [Function.comp_def, L] using (hxi_mem k hk_pos).continuousLinearMap_comp L

/--
Positive-index L2 membership for the endpoint-corrected ASGD remainder.  The
`N = 0` endpoint is zero, so no square-integrability of `ξ_0` is required.
-/
theorem chewi123ASGDEndpointCorrectedRemainder_memLp_two_of_noise_integrable_norm_sq_of_pos
    {Ω E : Type*} [MeasurableSpace Ω] {P : Measure Ω}
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    (A Ainv : E →L[ℝ] E) (h : ℕ -> ℝ) (xi : ℕ -> Ω -> E)
    (hxi_meas : ∀ k, AEStronglyMeasurable (xi k) P)
    (hxi_int : ∀ k, 1 ≤ k ->
      Integrable (fun ω => ‖xi k ω‖ ^ (2 : ℕ)) P)
    (N : ℕ) :
    MemLp
      (fun ω => chewi123ASGDEndpointCorrectedRemainder A Ainv h
        (fun n => xi n ω) N) (2 : ℝ≥0∞) P := by
  by_cases hN : N = 0
  · subst N
    have hzero :
        (fun ω : Ω => chewi123ASGDEndpointCorrectedRemainder A Ainv h
          (fun n => xi n ω) 0) = fun _ : Ω => (0 : E) := by
      funext ω
      simp [chewi123ASGDEndpointCorrectedRemainder]
    rw [hzero]
    exact (MemLp.zero' : MemLp (fun _ : Ω => (0 : E)) (2 : ℝ≥0∞) P)
  · have hN_pos_nat : 0 < N := Nat.pos_of_ne_zero hN
    have hN_pos : 1 ≤ N := Nat.succ_le_of_lt hN_pos_nat
    have hxi_mem : ∀ k, 1 ≤ k -> MemLp (xi k) (2 : ℝ≥0∞) P := fun k hk =>
      (memLp_two_iff_integrable_sq_norm (hxi_meas k)).2 (by simpa using hxi_int k hk)
    have hend :
        MemLp (fun ω => (Real.sqrt (N : ℝ))⁻¹ • Ainv (xi N ω))
          (2 : ℝ≥0∞) P := by
      let L : E →L[ℝ] E := (Real.sqrt (N : ℝ))⁻¹ • Ainv
      simpa [Function.comp_def, L] using (hxi_mem N hN_pos).continuousLinearMap_comp L
    have hsum :
        MemLp
          (fun ω =>
            (Real.sqrt (N : ℝ))⁻¹ •
              ∑ k ∈ Finset.Ico 1 N,
                (chewi123SourceNoiseCoefficient A h k N - Ainv) (xi k ω))
          (2 : ℝ≥0∞) P := by
      have hsum_inner :
          MemLp
            (fun ω =>
              ∑ k ∈ Finset.Ico 1 N,
                (chewi123SourceNoiseCoefficient A h k N - Ainv) (xi k ω))
            (2 : ℝ≥0∞) P := by
        refine memLp_finsetSum (Finset.Ico 1 N) ?_
        intro k hk
        let L : E →L[ℝ] E := chewi123SourceNoiseCoefficient A h k N - Ainv
        have hk_pos : 1 ≤ k := (Finset.mem_Ico.mp hk).1
        simpa [Function.comp_def, L] using (hxi_mem k hk_pos).continuousLinearMap_comp L
      simpa [Pi.smul_apply] using hsum_inner.const_smul (Real.sqrt (N : ℝ))⁻¹
    have hsub := hend.sub hsum
    simpa [chewi123ASGDEndpointCorrectedRemainder] using hsub

/--
Positive-index endpoint second-moment convergence.  Eventually `N ≥ 1`, so the
endpoint only requires bounds for positive noise indices.
-/
theorem chewi123ASGD_endpoint_integral_norm_sq_tendsto_zero_of_noise_integral_norm_sq_le_of_pos
    {Ω E : Type*} [MeasurableSpace Ω] {P : Measure Ω}
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    (Ainv : E →L[ℝ] E) (xi : ℕ -> Ω -> E) {B : ℝ}
    (hxi_int : ∀ k, 1 ≤ k ->
      Integrable (fun ω => ‖xi k ω‖ ^ (2 : ℕ)) P)
    (hxi_le : ∀ k, 1 ≤ k ->
      ∫ ω, ‖xi k ω‖ ^ (2 : ℕ) ∂P ≤ B) :
    Tendsto
      (fun N : ℕ =>
        ∫ ω, ‖(Real.sqrt (N : ℝ))⁻¹ • Ainv (xi N ω)‖ ^ (2 : ℕ) ∂P)
      atTop (𝓝 0) := by
  have hupper_tendsto :
      Tendsto
        (fun N : ℕ => (N : ℝ)⁻¹ * B * ‖Ainv‖ ^ (2 : ℕ))
        atTop (𝓝 0) := by
    have hinv : Tendsto (fun N : ℕ => ((N : ℝ)⁻¹ : ℝ)) atTop (𝓝 0) :=
      tendsto_inv_atTop_nhds_zero_nat
    have hmul :
        Tendsto
          (fun N : ℕ => ((N : ℝ)⁻¹ : ℝ) * (B * ‖Ainv‖ ^ (2 : ℕ)))
          atTop (𝓝 (0 * (B * ‖Ainv‖ ^ (2 : ℕ)))) :=
      hinv.mul tendsto_const_nhds
    have hmul0 :
        Tendsto
          (fun N : ℕ => ((N : ℝ)⁻¹ : ℝ) * (B * ‖Ainv‖ ^ (2 : ℕ)))
          atTop (𝓝 0) := by
      simpa using hmul
    refine hmul0.congr' ?_
    exact Eventually.of_forall fun N => by ring
  refine tendsto_of_tendsto_of_tendsto_of_le_of_le' tendsto_const_nhds
    hupper_tendsto ?_ ?_
  · exact Eventually.of_forall fun N =>
      integral_nonneg fun ω => sq_nonneg _
  · filter_upwards [eventually_gt_atTop (0 : ℕ)] with N hN
    have hN_pos : 1 ≤ N := Nat.succ_le_of_lt hN
    exact scaled_linear_image_integral_norm_sq_le_of_integral_norm_sq_le
      (P := P)
      (T := Ainv)
      (xi := xi N)
      (B := B)
      (N := N)
      hN (hxi_int N hN_pos) (hxi_le N hN_pos)

/--
Positive-index residual-sum second-moment convergence for a martingale
difference source.
-/
theorem chewi123ASGD_scaled_residual_sum_integral_norm_sq_tendsto_zero_of_martingale_difference_noise_second_moment_bound_of_pos
    {Ω E : Type*} [mΩ : MeasurableSpace Ω] {P : Measure Ω}
    [IsProbabilityMeasure P]
    [NormedAddCommGroup E] [InnerProductSpace ℝ E] [CompleteSpace E]
    (M : Chewi127MartingaleDifferenceProcess Ω E P)
    (A Ainv : E →L[ℝ] E) {alpha gamma C B : ℝ}
    (hleft : Ainv * A = 1)
    (halpha : 0 < alpha) (hgamma_pos : 0 < gamma) (hgamma_lt : gamma < 1)
    (hcoeff_bound : ∀ N k, k ∈ Finset.Ico 1 N ->
      ‖chewi123SourceNoiseCoefficient A (chewi125PowerStep gamma) k N - Ainv‖ ≤ C)
    (hstep : ∀ m, 2 ≤ m ->
      ‖chewi123QuadraticStepMap (chewi125PowerStep gamma m) A‖ ≤
        1 - alpha * chewi125PowerStep gamma m)
    (hsmall : ∀ m, 2 ≤ m ->
      0 ≤ 1 - alpha * chewi125PowerStep gamma m)
    (hxi_int : ∀ k, 1 ≤ k ->
      Integrable (fun ω => ‖M.xi k ω‖ ^ (2 : ℕ)) P)
    (hxi_le : ∀ k, 1 ≤ k ->
      ∫ ω, ‖M.xi k ω‖ ^ (2 : ℕ) ∂P ≤ B) :
    Tendsto
      (fun N : ℕ =>
        ∫ ω,
          ‖∑ k ∈ Finset.Ico 1 N,
            (Real.sqrt (N : ℝ))⁻¹ •
              ((chewi123SourceNoiseCoefficient A (chewi125PowerStep gamma) k N -
                Ainv) (M.xi k ω))‖ ^ (2 : ℕ) ∂P)
      atTop (𝓝 0) := by
  exact
    chewi123ASGD_scaled_residual_sum_integral_norm_sq_tendsto_zero_of_pairwise_integral_inner_zero
      A Ainv M.xi hleft halpha hgamma_pos hgamma_lt hcoeff_bound hstep hsmall
      (fun N k hk j hj =>
        chewi123ASGD_scaled_residual_cross_integrable_of_noise_integrable_norm_sq_of_pos
          (P := P) A Ainv (chewi125PowerStep gamma) M.xi
          (fun r => (M.integrable r).aestronglyMeasurable) hxi_int N k hk j hj)
      (fun N k hk j hj hkj =>
        M.chewi123ASGD_scaled_residual_cross_integral_eq_zero
          A Ainv hkj
          (chewi123ASGD_scaled_residual_cross_integrable_of_noise_integrable_norm_sq_of_pos
            (P := P) A Ainv (chewi125PowerStep gamma) M.xi
            (fun r => (M.integrable r).aestronglyMeasurable) hxi_int N k hk j hj))
      (fun N k hk =>
        chewi123ASGD_scaled_residual_summand_integral_norm_sq_le_of_noise_integral_norm_sq_le_of_pos
          A Ainv (chewi125PowerStep gamma) M.xi hxi_int hxi_le N k hk)

/--
Positive-index endpoint-corrected ASGD remainder has vanishing second moment.
-/
theorem chewi123ASGDEndpointCorrectedRemainder_integral_norm_sq_tendsto_zero_of_martingale_difference_noise_second_moment_bound_of_pos
    {Ω E : Type*} [mΩ : MeasurableSpace Ω] {P : Measure Ω}
    [IsProbabilityMeasure P]
    [NormedAddCommGroup E] [InnerProductSpace ℝ E] [CompleteSpace E]
    (M : Chewi127MartingaleDifferenceProcess Ω E P)
    (A Ainv : E →L[ℝ] E) {alpha gamma C B : ℝ}
    (hleft : Ainv * A = 1)
    (halpha : 0 < alpha) (hgamma_pos : 0 < gamma) (hgamma_lt : gamma < 1)
    (hcoeff_bound : ∀ N k, k ∈ Finset.Ico 1 N ->
      ‖chewi123SourceNoiseCoefficient A (chewi125PowerStep gamma) k N - Ainv‖ ≤ C)
    (hstep : ∀ m, 2 ≤ m ->
      ‖chewi123QuadraticStepMap (chewi125PowerStep gamma m) A‖ ≤
        1 - alpha * chewi125PowerStep gamma m)
    (hsmall : ∀ m, 2 ≤ m ->
      0 ≤ 1 - alpha * chewi125PowerStep gamma m)
    (hxi_int : ∀ k, 1 ≤ k ->
      Integrable (fun ω => ‖M.xi k ω‖ ^ (2 : ℕ)) P)
    (hxi_le : ∀ k, 1 ≤ k ->
      ∫ ω, ‖M.xi k ω‖ ^ (2 : ℕ) ∂P ≤ B) :
    Tendsto
      (fun N : ℕ =>
        ∫ ω,
          ‖chewi123ASGDEndpointCorrectedRemainder A Ainv
            (chewi125PowerStep gamma) (fun n => M.xi n ω) N‖ ^ (2 : ℕ) ∂P)
      atTop (𝓝 0) := by
  let U : ℕ -> Ω -> E := fun N ω =>
    (Real.sqrt (N : ℝ))⁻¹ • Ainv (M.xi N ω)
  let V : ℕ -> Ω -> E := fun N ω =>
    ∑ k ∈ Finset.Ico 1 N,
      (Real.sqrt (N : ℝ))⁻¹ •
        ((chewi123SourceNoiseCoefficient A (chewi125PowerStep gamma) k N -
          Ainv) (M.xi k ω))
  have hU_int : ∀ N, Integrable (fun ω => ‖U N ω‖ ^ (2 : ℕ)) P := by
    intro N
    by_cases hN : N = 0
    · subst N
      have hzero : (fun ω : Ω => ‖U 0 ω‖ ^ (2 : ℕ)) = fun _ : Ω => (0 : ℝ) := by
        funext ω
        simp [U]
      rw [hzero]
      exact integrable_zero Ω ℝ P
    · have hN_pos_nat : 0 < N := Nat.pos_of_ne_zero hN
      have hN_pos : 1 ≤ N := Nat.succ_le_of_lt hN_pos_nat
      simpa [U] using
        scaled_linear_image_integrable_norm_sq_of_integrable_norm_sq
          (P := P)
          (T := Ainv)
          (xi := M.xi N)
          (c := (Real.sqrt (N : ℝ))⁻¹)
          (M.integrable N).aestronglyMeasurable (hxi_int N hN_pos)
  have hV_mem : ∀ N, MemLp (V N) (2 : ℝ≥0∞) P := by
    intro N
    simpa [V] using
      chewi123ASGD_scaled_residual_sum_memLp_two_of_noise_integrable_norm_sq_of_pos
        (P := P)
        A Ainv (chewi125PowerStep gamma) M.xi
        (fun k => (M.integrable k).aestronglyMeasurable) hxi_int N
  have hV_int : ∀ N, Integrable (fun ω => ‖V N ω‖ ^ (2 : ℕ)) P := by
    intro N
    exact (hV_mem N).integrable_norm_pow (by norm_num : (2 : ℕ) ≠ 0)
  have hU_tend :
      Tendsto (fun N : ℕ => ∫ ω, ‖U N ω‖ ^ (2 : ℕ) ∂P) atTop (𝓝 0) := by
    simpa [U] using
      chewi123ASGD_endpoint_integral_norm_sq_tendsto_zero_of_noise_integral_norm_sq_le_of_pos
        (P := P) Ainv M.xi hxi_int hxi_le
  have hV_tend :
      Tendsto (fun N : ℕ => ∫ ω, ‖V N ω‖ ^ (2 : ℕ) ∂P) atTop (𝓝 0) := by
    simpa [V] using
      chewi123ASGD_scaled_residual_sum_integral_norm_sq_tendsto_zero_of_martingale_difference_noise_second_moment_bound_of_pos
        (P := P)
        M A Ainv hleft halpha hgamma_pos hgamma_lt hcoeff_bound hstep hsmall
        hxi_int hxi_le
  have hsub :
      Tendsto (fun N : ℕ => ∫ ω, ‖U N ω - V N ω‖ ^ (2 : ℕ) ∂P)
        atTop (𝓝 0) :=
    integral_norm_sq_sub_tendsto_zero_of_integral_norm_sq_tendsto_zero
      U V hU_int hV_int hU_tend hV_tend
  refine hsub.congr' ?_
  exact Eventually.of_forall fun N => by
    refine integral_congr_ae (ae_of_all P fun ω => ?_)
    have hV_eq :
        V N ω =
          (Real.sqrt (N : ℝ))⁻¹ •
            ∑ k ∈ Finset.Ico 1 N,
              (chewi123SourceNoiseCoefficient A (chewi125PowerStep gamma) k N -
                Ainv) (M.xi k ω) := by
      simp only [V, ContinuousLinearMap.sub_apply]
      rw [← Finset.smul_sum]
    simp [U, hV_eq, chewi123ASGDEndpointCorrectedRemainder]

/--
Positive-index endpoint-corrected ASGD stochastic remainder is `o_P(1)`.
-/
theorem chewi123ASGDEndpointCorrectedRemainder_tendstoInMeasure_zero_of_martingale_difference_noise_second_moment_bound_of_pos
    {Ω E : Type*} [mΩ : MeasurableSpace Ω] {P : Measure Ω}
    [IsProbabilityMeasure P]
    [NormedAddCommGroup E] [InnerProductSpace ℝ E] [CompleteSpace E]
    (M : Chewi127MartingaleDifferenceProcess Ω E P)
    (A Ainv : E →L[ℝ] E) {alpha gamma C B : ℝ}
    (hleft : Ainv * A = 1)
    (halpha : 0 < alpha) (hgamma_pos : 0 < gamma) (hgamma_lt : gamma < 1)
    (hcoeff_bound : ∀ N k, k ∈ Finset.Ico 1 N ->
      ‖chewi123SourceNoiseCoefficient A (chewi125PowerStep gamma) k N - Ainv‖ ≤ C)
    (hstep : ∀ m, 2 ≤ m ->
      ‖chewi123QuadraticStepMap (chewi125PowerStep gamma m) A‖ ≤
        1 - alpha * chewi125PowerStep gamma m)
    (hsmall : ∀ m, 2 ≤ m ->
      0 ≤ 1 - alpha * chewi125PowerStep gamma m)
    (hxi_int : ∀ k, 1 ≤ k ->
      Integrable (fun ω => ‖M.xi k ω‖ ^ (2 : ℕ)) P)
    (hxi_le : ∀ k, 1 ≤ k ->
      ∫ ω, ‖M.xi k ω‖ ^ (2 : ℕ) ∂P ≤ B) :
    TendstoInMeasure P
      (fun N ω => chewi123ASGDEndpointCorrectedRemainder A Ainv
        (chewi125PowerStep gamma) (fun n => M.xi n ω) N)
      atTop (fun _ => 0) := by
  refine
    chewi123ASGDEndpointCorrectedRemainder_tendstoInMeasure_zero_of_integral_norm_sq_tendsto_zero
      (P := P) A Ainv (chewi125PowerStep gamma) M.xi ?_ ?_
  · intro N
    exact
      (chewi123ASGDEndpointCorrectedRemainder_memLp_two_of_noise_integrable_norm_sq_of_pos
        (P := P)
        A Ainv (chewi125PowerStep gamma) M.xi
        (fun k => (M.integrable k).aestronglyMeasurable) hxi_int N).norm
  · exact
      chewi123ASGDEndpointCorrectedRemainder_integral_norm_sq_tendsto_zero_of_martingale_difference_noise_second_moment_bound_of_pos
        (P := P)
        M A Ainv hleft halpha hgamma_pos hgamma_lt hcoeff_bound hstep hsmall
        hxi_int hxi_le

/--
Chewi Theorem 12.3 ASGD weak-limit package with the endpoint-corrected
stochastic remainder discharged from the martingale-difference source
assumptions.

Compared with the upstream ASGD handoff, callers no longer supply the
`o_P(1)` coefficient-remainder proof or its measurability.  The only remaining
probabilistic ASGD-side inputs are the martingale CLT certificate, the
initial-condition `o_P(1)` proof, and the finite decomposition identifying the
chosen scaled average with the martingale term plus this endpoint-corrected
remainder.
-/
theorem chewi123_asgd_limit_package_of_martingale_certificate_and_endpoint_remainder
    {Ω Ω' E : Type*} [mΩ : MeasurableSpace Ω] {P : Measure Ω}
    [IsProbabilityMeasure P] [MeasurableSpace Ω'] {Q : Measure Ω'}
    [IsProbabilityMeasure Q]
    [NormedAddCommGroup E] [InnerProductSpace ℝ E] [CompleteSpace E]
    [MeasurableSpace E] [SecondCountableTopology E] [BorelSpace E]
    [OpensMeasurableSpace E]
    (C : Chewi127MartingaleCLTCertificate Ω Ω' E P Q)
    (M : Chewi127MartingaleDifferenceProcess Ω E P)
    (A Ainv : E →L[ℝ] E) {alpha gamma K B : ℝ}
    (hleft : Ainv * A = 1)
    (halpha : 0 < alpha) (hgamma_pos : 0 < gamma) (hgamma_lt : gamma < 1)
    (hcoeff_bound : ∀ N k, k ∈ Finset.Ico 1 N ->
      ‖chewi123SourceNoiseCoefficient A (chewi125PowerStep gamma) k N - Ainv‖ ≤ K)
    (hstep : ∀ m, 2 ≤ m ->
      ‖chewi123QuadraticStepMap (chewi125PowerStep gamma m) A‖ ≤
        1 - alpha * chewi125PowerStep gamma m)
    (hsmall : ∀ m, 2 ≤ m ->
      0 ≤ 1 - alpha * chewi125PowerStep gamma m)
    (hxi_int : ∀ k, Integrable (fun ω => ‖M.xi k ω‖ ^ (2 : ℕ)) P)
    (hxi_le : ∀ k, ∫ ω, ‖M.xi k ω‖ ^ (2 : ℕ) ∂P ≤ B)
    {scaledAverage initial : ℕ -> Ω -> E}
    (hInitial : TendstoInMeasure P initial atTop (fun _ => 0))
    (hInitial_meas : ∀ n, AEMeasurable (initial n) P)
    (hDecomp : ∀ n,
      (fun ω =>
        (-Ainv (C.noiseScaled n ω) + initial n ω) +
          chewi123ASGDEndpointCorrectedRemainder A Ainv
            (chewi125PowerStep gamma) (fun r => M.xi r ω) n)
        =ᵐ[P] scaledAverage n) :
    TendstoInDistribution scaledAverage atTop
        (fun ω => -Ainv (C.Z ω)) (fun _ => P) Q ∧
      ProbabilityTheory.HasGaussianLaw (fun ω => -Ainv (C.Z ω)) Q ∧
      ∀ L R : StrongDual ℝ E,
        ProbabilityTheory.covarianceBilinDual
            (Q.map fun ω => -Ainv (C.Z ω)) L R =
          vaart1998_inverseDerivativeCovarianceFunctional (-Ainv)
            (fun L0 R0 =>
              ProbabilityTheory.covarianceBilinDual (Q.map C.Z) L0 R0) L R := by
  have hRemainder :
      TendstoInMeasure P
        (fun N ω =>
          chewi123ASGDEndpointCorrectedRemainder A Ainv
            (chewi125PowerStep gamma) (fun r => M.xi r ω) N)
        atTop (fun _ => 0) :=
    chewi123ASGDEndpointCorrectedRemainder_tendstoInMeasure_zero_of_martingale_difference_noise_second_moment_bound
      (P := P)
      M A Ainv hleft halpha hgamma_pos hgamma_lt hcoeff_bound hstep hsmall
      hxi_int hxi_le
  have hRemainder_meas :
      ∀ n, AEMeasurable
        (fun ω =>
          chewi123ASGDEndpointCorrectedRemainder A Ainv
            (chewi125PowerStep gamma) (fun r => M.xi r ω) n) P := by
    intro n
    exact
      (chewi123ASGDEndpointCorrectedRemainder_memLp_two_of_noise_integrable_norm_sq
        (P := P)
        A Ainv (chewi125PowerStep gamma) M.xi
        (fun k => (M.integrable k).aestronglyMeasurable) hxi_int n).aemeasurable
  exact
    chewi123_asgd_limit_package_of_martingale_certificate
      (C := C) Ainv hInitial hRemainder
      hInitial_meas hRemainder_meas hDecomp

/--
Chewi Theorem 12.3 ASGD weak-limit package with both the initial-condition
term and endpoint-corrected stochastic remainder discharged from source-style
deterministic/probabilistic bounds.

The caller now supplies the finite ASGD decomposition with the concrete
`chewi123ASGDInitialTerm`, plus the deterministic operator-norm decay and
bounded-initial-error hypotheses used in Chewi's proof after `(12.5)`.
-/
theorem chewi123_asgd_limit_package_of_martingale_certificate_endpoint_remainder_and_initial_bound
    {Ω Ω' E : Type*} [mΩ : MeasurableSpace Ω] {P : Measure Ω}
    [IsProbabilityMeasure P] [MeasurableSpace Ω'] {Q : Measure Ω'}
    [IsProbabilityMeasure Q]
    [NormedAddCommGroup E] [InnerProductSpace ℝ E] [CompleteSpace E]
    [MeasurableSpace E] [SecondCountableTopology E] [BorelSpace E]
    [OpensMeasurableSpace E]
    (C : Chewi127MartingaleCLTCertificate Ω Ω' E P Q)
    (M : Chewi127MartingaleDifferenceProcess Ω E P)
    (A Ainv : E →L[ℝ] E) {alpha gamma K B B0 : ℝ}
    (hleft : Ainv * A = 1)
    (halpha : 0 < alpha) (hgamma_pos : 0 < gamma) (hgamma_lt : gamma < 1)
    (hcoeff_bound : ∀ N k, k ∈ Finset.Ico 1 N ->
      ‖chewi123SourceNoiseCoefficient A (chewi125PowerStep gamma) k N - Ainv‖ ≤ K)
    (hstep : ∀ m, 2 ≤ m ->
      ‖chewi123QuadraticStepMap (chewi125PowerStep gamma m) A‖ ≤
        1 - alpha * chewi125PowerStep gamma m)
    (hsmall : ∀ m, 2 ≤ m ->
      0 ≤ 1 - alpha * chewi125PowerStep gamma m)
    (hxi_int : ∀ k, Integrable (fun ω => ‖M.xi k ω‖ ^ (2 : ℕ)) P)
    (hxi_le : ∀ k, ∫ ω, ‖M.xi k ω‖ ^ (2 : ℕ) ∂P ≤ B)
    (delta0 : Ω -> E)
    (hdelta0_meas : AEMeasurable delta0 P)
    (hdelta0_bound : ∀ ω, ‖delta0 ω‖ ≤ B0)
    (hInitial_decay :
      Tendsto
        (fun N : ℕ =>
          ‖(Real.sqrt (N : ℝ))⁻¹‖ *
            ‖chewi123InitialCoefficient A (chewi125PowerStep gamma) N‖ * B0)
        atTop (𝓝 0))
    {scaledAverage : ℕ -> Ω -> E}
    (hDecomp : ∀ n,
      (fun ω =>
        (-Ainv (C.noiseScaled n ω) +
            chewi123ASGDInitialTerm A (chewi125PowerStep gamma) (delta0 ω) n) +
          chewi123ASGDEndpointCorrectedRemainder A Ainv
            (chewi125PowerStep gamma) (fun r => M.xi r ω) n)
        =ᵐ[P] scaledAverage n) :
    TendstoInDistribution scaledAverage atTop
        (fun ω => -Ainv (C.Z ω)) (fun _ => P) Q ∧
      ProbabilityTheory.HasGaussianLaw (fun ω => -Ainv (C.Z ω)) Q ∧
      ∀ L R : StrongDual ℝ E,
        ProbabilityTheory.covarianceBilinDual
            (Q.map fun ω => -Ainv (C.Z ω)) L R =
          vaart1998_inverseDerivativeCovarianceFunctional (-Ainv)
            (fun L0 R0 =>
              ProbabilityTheory.covarianceBilinDual (Q.map C.Z) L0 R0) L R := by
  have hInitial :
      TendstoInMeasure P
        (fun N ω => chewi123ASGDInitialTerm A (chewi125PowerStep gamma) (delta0 ω) N)
        atTop (fun _ => 0) :=
    chewi123ASGDInitialTerm_tendstoInMeasure_zero_of_opNorm_decay_bounded_initial
      (P := P) A (chewi125PowerStep gamma) delta0 B0 hdelta0_bound
      hInitial_decay
  have hInitial_meas :
      ∀ n, AEMeasurable
        (fun ω => chewi123ASGDInitialTerm A (chewi125PowerStep gamma) (delta0 ω) n) P := by
    intro n
    have hmap :
        AEMeasurable
          (fun ω => chewi123InitialCoefficient A (chewi125PowerStep gamma) n (delta0 ω)) P :=
      (chewi123InitialCoefficient A (chewi125PowerStep gamma) n).continuous.measurable.comp_aemeasurable
        hdelta0_meas
    simpa [chewi123ASGDInitialTerm, Pi.smul_apply] using
      hmap.const_smul ((Real.sqrt (n : ℝ))⁻¹)
  exact
    chewi123_asgd_limit_package_of_martingale_certificate_and_endpoint_remainder
      (C := C) M A Ainv hleft halpha hgamma_pos hgamma_lt hcoeff_bound hstep
      hsmall hxi_int hxi_le hInitial hInitial_meas hDecomp

/--
Chewi Theorem 12.3 ASGD weak-limit package with the deterministic quadratic
ASGD decomposition supplied by the source recurrence.

Compared with
`chewi123_asgd_limit_package_of_martingale_certificate_endpoint_remainder_and_initial_bound`,
callers no longer provide the finite decomposition.  They only identify the
martingale certificate's normalized noise with the local
`chewi127ScaledNoiseSum` and provide the quadratic ASGD error recurrence.
-/
theorem chewi123_asgd_limit_package_of_martingale_certificate_source_quadratic
    {Ω Ω' E : Type*} [mΩ : MeasurableSpace Ω] {P : Measure Ω}
    [IsProbabilityMeasure P] [MeasurableSpace Ω'] {Q : Measure Ω'}
    [IsProbabilityMeasure Q]
    [NormedAddCommGroup E] [InnerProductSpace ℝ E] [CompleteSpace E]
    [MeasurableSpace E] [SecondCountableTopology E] [BorelSpace E]
    [OpensMeasurableSpace E]
    (C : Chewi127MartingaleCLTCertificate Ω Ω' E P Q)
    (M : Chewi127MartingaleDifferenceProcess Ω E P)
    (A Ainv : E →L[ℝ] E) {alpha gamma K B B0 : ℝ}
    (hleft : Ainv * A = 1)
    (halpha : 0 < alpha) (hgamma_pos : 0 < gamma) (hgamma_lt : gamma < 1)
    (hcoeff_bound : ∀ N k, k ∈ Finset.Ico 1 N ->
      ‖chewi123SourceNoiseCoefficient A (chewi125PowerStep gamma) k N - Ainv‖ ≤ K)
    (hstep : ∀ m, 2 ≤ m ->
      ‖chewi123QuadraticStepMap (chewi125PowerStep gamma m) A‖ ≤
        1 - alpha * chewi125PowerStep gamma m)
    (hsmall : ∀ m, 2 ≤ m ->
      0 ≤ 1 - alpha * chewi125PowerStep gamma m)
    (hxi_int : ∀ k, Integrable (fun ω => ‖M.xi k ω‖ ^ (2 : ℕ)) P)
    (hxi_le : ∀ k, ∫ ω, ‖M.xi k ω‖ ^ (2 : ℕ) ∂P ≤ B)
    (delta : ℕ -> Ω -> E)
    (hNoise_eq : ∀ N, C.noiseScaled N =ᵐ[P] chewi127ScaledNoiseSum M.xi N)
    (hrec : ∀ n ω,
      delta (n + 1) ω =
        chewi123QuadraticStepMap (chewi125PowerStep gamma (n + 1)) A
          (delta n ω) -
          chewi125PowerStep gamma (n + 1) • M.xi (n + 1) ω)
    (hdelta0_meas : AEMeasurable (delta 0) P)
    (hdelta0_bound : ∀ ω, ‖delta 0 ω‖ ≤ B0)
    (hInitial_decay :
      Tendsto
        (fun N : ℕ =>
          ‖(Real.sqrt (N : ℝ))⁻¹‖ *
            ‖chewi123InitialCoefficient A (chewi125PowerStep gamma) N‖ * B0)
        atTop (𝓝 0)) :
    TendstoInDistribution
        (fun N ω => chewi123ScaledAverageDelta (fun n => delta n ω) N)
        atTop (fun ω => -Ainv (C.Z ω)) (fun _ => P) Q ∧
      ProbabilityTheory.HasGaussianLaw (fun ω => -Ainv (C.Z ω)) Q ∧
      ∀ L R : StrongDual ℝ E,
        ProbabilityTheory.covarianceBilinDual
            (Q.map fun ω => -Ainv (C.Z ω)) L R =
          vaart1998_inverseDerivativeCovarianceFunctional (-Ainv)
            (fun L0 R0 =>
              ProbabilityTheory.covarianceBilinDual (Q.map C.Z) L0 R0) L R := by
  refine
    chewi123_asgd_limit_package_of_martingale_certificate_endpoint_remainder_and_initial_bound
      (C := C) M A Ainv hleft halpha hgamma_pos hgamma_lt hcoeff_bound hstep
      hsmall hxi_int hxi_le (fun ω => delta 0 ω) hdelta0_meas
      hdelta0_bound hInitial_decay ?_
  intro N
  filter_upwards
    [hNoise_eq N,
      chewi123_quadratic_sqrt_average_delta_endpoint_corrected_decomposition_ae
        (P := P) A Ainv (chewi125PowerStep gamma) delta M.xi hrec N] with
    ω hnoise hdecomp
  simpa [hnoise] using hdecomp

/--
Chewi Theorem 12.3 ASGD weak-limit package from the bounded martingale CLT
source object, with the quadratic source recurrence supplying the finite
decomposition.

This removes the manual martingale-certificate and normalized-noise
identification inputs from
`chewi123_asgd_limit_package_of_martingale_certificate_source_quadratic`.
The remaining analytic assumptions are exactly the deterministic quadratic
ASGD bounds, square-integrability/uniform second-moment inputs for the noise,
and the bounded initial-condition decay input.
-/
theorem Chewi127BoundedMartingaleCLTSource.asgd_limit_package_source_quadratic
    {Ω Ω' E : Type*} [mΩ : MeasurableSpace Ω] {P : Measure Ω}
    [IsProbabilityMeasure P] [MeasurableSpace Ω'] {Q : Measure Ω'}
    [IsProbabilityMeasure Q]
    [NormedAddCommGroup E] [InnerProductSpace ℝ E] [CompleteSpace E]
    [MeasurableSpace E] [SecondCountableTopology E] [BorelSpace E]
    [OpensMeasurableSpace E]
    (S : Chewi127BoundedMartingaleCLTSource Ω Ω' E P Q)
    (A Ainv : E →L[ℝ] E) {alpha gamma K B B0 : ℝ}
    (hleft : Ainv * A = 1)
    (halpha : 0 < alpha) (hgamma_pos : 0 < gamma) (hgamma_lt : gamma < 1)
    (hcoeff_bound : ∀ N k, k ∈ Finset.Ico 1 N ->
      ‖chewi123SourceNoiseCoefficient A (chewi125PowerStep gamma) k N - Ainv‖ ≤ K)
    (hstep : ∀ m, 2 ≤ m ->
      ‖chewi123QuadraticStepMap (chewi125PowerStep gamma m) A‖ ≤
        1 - alpha * chewi125PowerStep gamma m)
    (hsmall : ∀ m, 2 ≤ m ->
      0 ≤ 1 - alpha * chewi125PowerStep gamma m)
    (hxi_int : ∀ k, Integrable (fun ω => ‖S.martingale.xi k ω‖ ^ (2 : ℕ)) P)
    (hxi_le : ∀ k, ∫ ω, ‖S.martingale.xi k ω‖ ^ (2 : ℕ) ∂P ≤ B)
    (delta : ℕ -> Ω -> E)
    (hrec : ∀ n ω,
      delta (n + 1) ω =
        chewi123QuadraticStepMap (chewi125PowerStep gamma (n + 1)) A
          (delta n ω) -
          chewi125PowerStep gamma (n + 1) • S.martingale.xi (n + 1) ω)
    (hdelta0_meas : AEMeasurable (delta 0) P)
    (hdelta0_bound : ∀ ω, ‖delta 0 ω‖ ≤ B0)
    (hInitial_decay :
      Tendsto
        (fun N : ℕ =>
          ‖(Real.sqrt (N : ℝ))⁻¹‖ *
            ‖chewi123InitialCoefficient A (chewi125PowerStep gamma) N‖ * B0)
        atTop (𝓝 0)) :
    TendstoInDistribution
        (fun N ω => chewi123ScaledAverageDelta (fun n => delta n ω) N)
        atTop (fun ω => -Ainv (S.Z ω)) (fun _ => P) Q ∧
      ProbabilityTheory.HasGaussianLaw (fun ω => -Ainv (S.Z ω)) Q ∧
      ∀ L R : StrongDual ℝ E,
        ProbabilityTheory.covarianceBilinDual
            (Q.map fun ω => -Ainv (S.Z ω)) L R =
          vaart1998_inverseDerivativeCovarianceFunctional (-Ainv)
            (fun L0 R0 =>
              ProbabilityTheory.covarianceBilinDual (Q.map S.Z) L0 R0) L R := by
  let C : Chewi127MartingaleCLTCertificate Ω Ω' E P Q :=
    S.toMartingaleCLTCertificate
  simpa [C, Chewi127BoundedMartingaleCLTSource.toMartingaleCLTCertificate,
    Chewi127BoundedMartingaleCLTSource.toProjectedBridge,
    Chewi127ProjectedMartingaleCLTBridge.toMartingaleCLTCertificate] using
    chewi123_asgd_limit_package_of_martingale_certificate_source_quadratic
      (C := C) S.martingale A Ainv hleft halpha hgamma_pos hgamma_lt
      hcoeff_bound hstep hsmall hxi_int hxi_le delta
      (fun _ => ae_of_all _ fun _ => rfl) hrec hdelta0_meas hdelta0_bound
      hInitial_decay

/--
Chewi Theorem 12.3 ASGD weak-limit package from the bounded martingale CLT
source object with only positive-index noise moment hypotheses.

This is the source-shaped bridge needed for `S.uniform_bound`: Chewi's
martingale-difference source bounds `ξ_{n+1}` a.e., while the ASGD residual
and endpoint-corrected remainder never need square-integrability of `ξ_0`.
-/
theorem Chewi127BoundedMartingaleCLTSource.asgd_limit_package_source_quadratic_of_pos_noise_second_moment_bound
    {Ω Ω' E : Type*} [mΩ : MeasurableSpace Ω] {P : Measure Ω}
    [IsProbabilityMeasure P] [MeasurableSpace Ω'] {Q : Measure Ω'}
    [IsProbabilityMeasure Q]
    [NormedAddCommGroup E] [InnerProductSpace ℝ E] [CompleteSpace E]
    [MeasurableSpace E] [SecondCountableTopology E] [BorelSpace E]
    [OpensMeasurableSpace E]
    (S : Chewi127BoundedMartingaleCLTSource Ω Ω' E P Q)
    (A Ainv : E →L[ℝ] E) {alpha gamma K B B0 : ℝ}
    (hleft : Ainv * A = 1)
    (halpha : 0 < alpha) (hgamma_pos : 0 < gamma) (hgamma_lt : gamma < 1)
    (hcoeff_bound : ∀ N k, k ∈ Finset.Ico 1 N ->
      ‖chewi123SourceNoiseCoefficient A (chewi125PowerStep gamma) k N - Ainv‖ ≤ K)
    (hstep : ∀ m, 2 ≤ m ->
      ‖chewi123QuadraticStepMap (chewi125PowerStep gamma m) A‖ ≤
        1 - alpha * chewi125PowerStep gamma m)
    (hsmall : ∀ m, 2 ≤ m ->
      0 ≤ 1 - alpha * chewi125PowerStep gamma m)
    (hxi_int : ∀ k, 1 ≤ k ->
      Integrable (fun ω => ‖S.martingale.xi k ω‖ ^ (2 : ℕ)) P)
    (hxi_le : ∀ k, 1 ≤ k ->
      ∫ ω, ‖S.martingale.xi k ω‖ ^ (2 : ℕ) ∂P ≤ B)
    (delta : ℕ -> Ω -> E)
    (hrec : ∀ n ω,
      delta (n + 1) ω =
        chewi123QuadraticStepMap (chewi125PowerStep gamma (n + 1)) A
          (delta n ω) -
          chewi125PowerStep gamma (n + 1) • S.martingale.xi (n + 1) ω)
    (hdelta0_meas : AEMeasurable (delta 0) P)
    (hdelta0_bound : ∀ ω, ‖delta 0 ω‖ ≤ B0)
    (hInitial_decay :
      Tendsto
        (fun N : ℕ =>
          ‖(Real.sqrt (N : ℝ))⁻¹‖ *
            ‖chewi123InitialCoefficient A (chewi125PowerStep gamma) N‖ * B0)
        atTop (𝓝 0)) :
    TendstoInDistribution
        (fun N ω => chewi123ScaledAverageDelta (fun n => delta n ω) N)
        atTop (fun ω => -Ainv (S.Z ω)) (fun _ => P) Q ∧
      ProbabilityTheory.HasGaussianLaw (fun ω => -Ainv (S.Z ω)) Q ∧
      ∀ L R : StrongDual ℝ E,
        ProbabilityTheory.covarianceBilinDual
            (Q.map fun ω => -Ainv (S.Z ω)) L R =
          vaart1998_inverseDerivativeCovarianceFunctional (-Ainv)
            (fun L0 R0 =>
              ProbabilityTheory.covarianceBilinDual (Q.map S.Z) L0 R0) L R := by
  have hInitial :
      TendstoInMeasure P
        (fun N ω =>
          chewi123ASGDInitialTerm A (chewi125PowerStep gamma) (delta 0 ω) N)
        atTop (fun _ => 0) :=
    chewi123ASGDInitialTerm_tendstoInMeasure_zero_of_opNorm_decay_bounded_initial
      (P := P) A (chewi125PowerStep gamma) (fun ω => delta 0 ω) B0
      hdelta0_bound hInitial_decay
  have hInitial_meas :
      ∀ n, AEMeasurable
        (fun ω => chewi123ASGDInitialTerm A (chewi125PowerStep gamma) (delta 0 ω) n) P := by
    intro n
    have hmap :
        AEMeasurable
          (fun ω => chewi123InitialCoefficient A (chewi125PowerStep gamma) n (delta 0 ω)) P :=
      (chewi123InitialCoefficient A (chewi125PowerStep gamma) n).continuous.measurable.comp_aemeasurable
        hdelta0_meas
    simpa [chewi123ASGDInitialTerm, Pi.smul_apply] using
      hmap.const_smul ((Real.sqrt (n : ℝ))⁻¹)
  have hRemainder :
      TendstoInMeasure P
        (fun N ω =>
          chewi123ASGDEndpointCorrectedRemainder A Ainv
            (chewi125PowerStep gamma) (fun r => S.martingale.xi r ω) N)
        atTop (fun _ => 0) :=
    chewi123ASGDEndpointCorrectedRemainder_tendstoInMeasure_zero_of_martingale_difference_noise_second_moment_bound_of_pos
      (P := P)
      S.martingale A Ainv hleft halpha hgamma_pos hgamma_lt hcoeff_bound hstep
      hsmall hxi_int hxi_le
  have hRemainder_meas :
      ∀ n, AEMeasurable
        (fun ω =>
          chewi123ASGDEndpointCorrectedRemainder A Ainv
            (chewi125PowerStep gamma) (fun r => S.martingale.xi r ω) n) P := by
    intro n
    exact
      (chewi123ASGDEndpointCorrectedRemainder_memLp_two_of_noise_integrable_norm_sq_of_pos
        (P := P)
        A Ainv (chewi125PowerStep gamma) S.martingale.xi
        (fun k => (S.martingale.integrable k).aestronglyMeasurable) hxi_int n).aemeasurable
  exact
    S.asgd_limit_package_endpoint_corrected A Ainv (chewi125PowerStep gamma) delta
      hrec hInitial hRemainder hInitial_meas hRemainder_meas

/--
Chewi Theorem 12.3 ASGD weak-limit package from the bounded martingale CLT
source object and a pointwise uniform noise bound.

This wrapper derives the square-integrability and uniform second-moment inputs
for the endpoint-corrected stochastic remainder from
`‖S.martingale.xi n ω‖ ≤ Bxi`.
-/
theorem Chewi127BoundedMartingaleCLTSource.asgd_limit_package_source_quadratic_of_uniform_noise_bound
    {Ω Ω' E : Type*} [mΩ : MeasurableSpace Ω] {P : Measure Ω}
    [IsProbabilityMeasure P] [MeasurableSpace Ω'] {Q : Measure Ω'}
    [IsProbabilityMeasure Q]
    [NormedAddCommGroup E] [InnerProductSpace ℝ E] [CompleteSpace E]
    [MeasurableSpace E] [SecondCountableTopology E] [BorelSpace E]
    [OpensMeasurableSpace E]
    (S : Chewi127BoundedMartingaleCLTSource Ω Ω' E P Q)
    (A Ainv : E →L[ℝ] E) {alpha gamma K Bxi B0 : ℝ}
    (hleft : Ainv * A = 1)
    (halpha : 0 < alpha) (hgamma_pos : 0 < gamma) (hgamma_lt : gamma < 1)
    (hcoeff_bound : ∀ N k, k ∈ Finset.Ico 1 N ->
      ‖chewi123SourceNoiseCoefficient A (chewi125PowerStep gamma) k N - Ainv‖ ≤ K)
    (hstep : ∀ m, 2 ≤ m ->
      ‖chewi123QuadraticStepMap (chewi125PowerStep gamma m) A‖ ≤
        1 - alpha * chewi125PowerStep gamma m)
    (hsmall : ∀ m, 2 ≤ m ->
      0 ≤ 1 - alpha * chewi125PowerStep gamma m)
    (hBxi_nonneg : 0 ≤ Bxi)
    (hxi_bound : ∀ n ω, ‖S.martingale.xi n ω‖ ≤ Bxi)
    (delta : ℕ -> Ω -> E)
    (hrec : ∀ n ω,
      delta (n + 1) ω =
        chewi123QuadraticStepMap (chewi125PowerStep gamma (n + 1)) A
          (delta n ω) -
          chewi125PowerStep gamma (n + 1) • S.martingale.xi (n + 1) ω)
    (hdelta0_meas : AEMeasurable (delta 0) P)
    (hdelta0_bound : ∀ ω, ‖delta 0 ω‖ ≤ B0)
    (hInitial_decay :
      Tendsto
        (fun N : ℕ =>
          ‖(Real.sqrt (N : ℝ))⁻¹‖ *
            ‖chewi123InitialCoefficient A (chewi125PowerStep gamma) N‖ * B0)
        atTop (𝓝 0)) :
    TendstoInDistribution
        (fun N ω => chewi123ScaledAverageDelta (fun n => delta n ω) N)
        atTop (fun ω => -Ainv (S.Z ω)) (fun _ => P) Q ∧
      ProbabilityTheory.HasGaussianLaw (fun ω => -Ainv (S.Z ω)) Q ∧
      ∀ L R : StrongDual ℝ E,
        ProbabilityTheory.covarianceBilinDual
            (Q.map fun ω => -Ainv (S.Z ω)) L R =
          vaart1998_inverseDerivativeCovarianceFunctional (-Ainv)
            (fun L0 R0 =>
              ProbabilityTheory.covarianceBilinDual (Q.map S.Z) L0 R0) L R := by
  have hxi_int :
      ∀ k, Integrable (fun ω => ‖S.martingale.xi k ω‖ ^ (2 : ℕ)) P := by
    intro k
    refine Integrable.of_bound
      ((S.martingale.integrable k).aestronglyMeasurable.norm.aemeasurable.pow_const
        (2 : ℕ)).aestronglyMeasurable
      (Bxi ^ (2 : ℕ)) ?_
    exact Eventually.of_forall fun ω => by
      have hnorm_nonneg : 0 ≤ ‖S.martingale.xi k ω‖ := norm_nonneg _
      have hpow_nonneg : 0 ≤ ‖S.martingale.xi k ω‖ ^ (2 : ℕ) := sq_nonneg _
      rw [Real.norm_eq_abs, abs_of_nonneg hpow_nonneg]
      nlinarith [hxi_bound k ω, hnorm_nonneg, hBxi_nonneg]
  have hxi_le :
      ∀ k, ∫ ω, ‖S.martingale.xi k ω‖ ^ (2 : ℕ) ∂P ≤ Bxi ^ (2 : ℕ) := by
    intro k
    have hconst_int : Integrable (fun _ : Ω => Bxi ^ (2 : ℕ)) P :=
      integrable_const _
    have hmono :=
      integral_mono_ae (hxi_int k) hconst_int
        (Eventually.of_forall fun ω => by
          have hnorm_nonneg : 0 ≤ ‖S.martingale.xi k ω‖ := norm_nonneg _
          nlinarith [hxi_bound k ω, hnorm_nonneg, hBxi_nonneg])
    simpa [integral_const, probReal_univ, smul_eq_mul] using hmono
  exact
    S.asgd_limit_package_source_quadratic A Ainv hleft halpha hgamma_pos
      hgamma_lt hcoeff_bound hstep hsmall hxi_int hxi_le delta hrec
      hdelta0_meas hdelta0_bound hInitial_decay

/--
Chewi Theorem 12.3 ASGD weak-limit package from the bounded martingale CLT
source object's own one-based a.e. uniform bound.

This is the source-aligned bounded-noise wrapper: it consumes
`S.uniform_bound` directly and therefore avoids any artificial
square-integrability assumption on `ξ_0`.
-/
theorem Chewi127BoundedMartingaleCLTSource.asgd_limit_package_source_quadratic_of_source_uniform_bound
    {Ω Ω' E : Type*} [mΩ : MeasurableSpace Ω] {P : Measure Ω}
    [IsProbabilityMeasure P] [MeasurableSpace Ω'] {Q : Measure Ω'}
    [IsProbabilityMeasure Q]
    [NormedAddCommGroup E] [InnerProductSpace ℝ E] [CompleteSpace E]
    [MeasurableSpace E] [SecondCountableTopology E] [BorelSpace E]
    [OpensMeasurableSpace E]
    (S : Chewi127BoundedMartingaleCLTSource Ω Ω' E P Q)
    (A Ainv : E →L[ℝ] E) {alpha gamma K B0 : ℝ}
    (hleft : Ainv * A = 1)
    (halpha : 0 < alpha) (hgamma_pos : 0 < gamma) (hgamma_lt : gamma < 1)
    (hcoeff_bound : ∀ N k, k ∈ Finset.Ico 1 N ->
      ‖chewi123SourceNoiseCoefficient A (chewi125PowerStep gamma) k N - Ainv‖ ≤ K)
    (hstep : ∀ m, 2 ≤ m ->
      ‖chewi123QuadraticStepMap (chewi125PowerStep gamma m) A‖ ≤
        1 - alpha * chewi125PowerStep gamma m)
    (hsmall : ∀ m, 2 ≤ m ->
      0 ≤ 1 - alpha * chewi125PowerStep gamma m)
    (delta : ℕ -> Ω -> E)
    (hrec : ∀ n ω,
      delta (n + 1) ω =
        chewi123QuadraticStepMap (chewi125PowerStep gamma (n + 1)) A
          (delta n ω) -
          chewi125PowerStep gamma (n + 1) • S.martingale.xi (n + 1) ω)
    (hdelta0_meas : AEMeasurable (delta 0) P)
    (hdelta0_bound : ∀ ω, ‖delta 0 ω‖ ≤ B0)
    (hInitial_decay :
      Tendsto
        (fun N : ℕ =>
          ‖(Real.sqrt (N : ℝ))⁻¹‖ *
            ‖chewi123InitialCoefficient A (chewi125PowerStep gamma) N‖ * B0)
        atTop (𝓝 0)) :
    TendstoInDistribution
        (fun N ω => chewi123ScaledAverageDelta (fun n => delta n ω) N)
        atTop (fun ω => -Ainv (S.Z ω)) (fun _ => P) Q ∧
      ProbabilityTheory.HasGaussianLaw (fun ω => -Ainv (S.Z ω)) Q ∧
      ∀ L R : StrongDual ℝ E,
        ProbabilityTheory.covarianceBilinDual
            (Q.map fun ω => -Ainv (S.Z ω)) L R =
          vaart1998_inverseDerivativeCovarianceFunctional (-Ainv)
            (fun L0 R0 =>
              ProbabilityTheory.covarianceBilinDual (Q.map S.Z) L0 R0) L R := by
  rcases S.uniform_bound with ⟨Bxi, hBxi_nonneg, hxi_bound⟩
  have hxi_int :
      ∀ k, 1 ≤ k ->
        Integrable (fun ω => ‖S.martingale.xi k ω‖ ^ (2 : ℕ)) P := by
    intro k hk
    have hidx : k - 1 + 1 = k := Nat.sub_add_cancel hk
    refine Integrable.of_bound
      ((S.martingale.integrable k).aestronglyMeasurable.norm.aemeasurable.pow_const
        (2 : ℕ)).aestronglyMeasurable
      (Bxi ^ (2 : ℕ)) ?_
    filter_upwards [hxi_bound (k - 1)] with ω hω
    have hbound : ‖S.martingale.xi k ω‖ ≤ Bxi := by
      simpa [hidx] using hω
    have hnorm_nonneg : 0 ≤ ‖S.martingale.xi k ω‖ := norm_nonneg _
    have hpow_nonneg : 0 ≤ ‖S.martingale.xi k ω‖ ^ (2 : ℕ) := sq_nonneg _
    rw [Real.norm_eq_abs, abs_of_nonneg hpow_nonneg]
    nlinarith [hbound, hnorm_nonneg, hBxi_nonneg]
  have hxi_le :
      ∀ k, 1 ≤ k ->
        ∫ ω, ‖S.martingale.xi k ω‖ ^ (2 : ℕ) ∂P ≤ Bxi ^ (2 : ℕ) := by
    intro k hk
    have hidx : k - 1 + 1 = k := Nat.sub_add_cancel hk
    have hconst_int : Integrable (fun _ : Ω => Bxi ^ (2 : ℕ)) P :=
      integrable_const _
    have hmono :=
      integral_mono_ae (hxi_int k hk) hconst_int
        (by
          filter_upwards [hxi_bound (k - 1)] with ω hω
          have hbound : ‖S.martingale.xi k ω‖ ≤ Bxi := by
            simpa [hidx] using hω
          have hnorm_nonneg : 0 ≤ ‖S.martingale.xi k ω‖ := norm_nonneg _
          nlinarith [hbound, hnorm_nonneg, hBxi_nonneg])
    simpa [integral_const, probReal_univ, smul_eq_mul] using hmono
  exact
    S.asgd_limit_package_source_quadratic_of_pos_noise_second_moment_bound
      A Ainv hleft halpha hgamma_pos hgamma_lt hcoeff_bound hstep hsmall
      hxi_int hxi_le delta hrec hdelta0_meas hdelta0_bound hInitial_decay

/--
Source-aligned Chewi Theorem 12.3 ASGD weak-limit package with the
initial-condition decay supplied by a scalar majorant for the initial
coefficient.  This reuses the deterministic coefficient layer from
`ASGDEndpointCorrection.lean` before entering the V142 a.e. one-based
noise-bound wrapper.
-/
theorem Chewi127BoundedMartingaleCLTSource.asgd_limit_package_source_quadratic_of_source_uniform_bound_and_initial_norm_bound
    {Ω Ω' E : Type*} [mΩ : MeasurableSpace Ω] {P : Measure Ω}
    [IsProbabilityMeasure P] [MeasurableSpace Ω'] {Q : Measure Ω'}
    [IsProbabilityMeasure Q]
    [NormedAddCommGroup E] [InnerProductSpace ℝ E] [CompleteSpace E]
    [MeasurableSpace E] [SecondCountableTopology E] [BorelSpace E]
    [OpensMeasurableSpace E]
    (S : Chewi127BoundedMartingaleCLTSource Ω Ω' E P Q)
    (A Ainv : E →L[ℝ] E) {alpha gamma K B0 : ℝ}
    (C0 : ℕ -> ℝ)
    (hleft : Ainv * A = 1)
    (halpha : 0 < alpha) (hgamma_pos : 0 < gamma) (hgamma_lt : gamma < 1)
    (hcoeff_bound : ∀ N k, k ∈ Finset.Ico 1 N ->
      ‖chewi123SourceNoiseCoefficient A (chewi125PowerStep gamma) k N - Ainv‖ ≤ K)
    (hstep : ∀ m, 2 ≤ m ->
      ‖chewi123QuadraticStepMap (chewi125PowerStep gamma m) A‖ ≤
        1 - alpha * chewi125PowerStep gamma m)
    (hsmall : ∀ m, 2 ≤ m ->
      0 ≤ 1 - alpha * chewi125PowerStep gamma m)
    (hB0_nonneg : 0 ≤ B0)
    (hinitial_bound : ∀ N,
      ‖chewi123InitialCoefficient A (chewi125PowerStep gamma) N‖ ≤ C0 N)
    (hinitial_decay :
      Tendsto
        (fun N : ℕ =>
          ‖(Real.sqrt (N : ℝ))⁻¹‖ * C0 N * B0)
        atTop (𝓝 0))
    (delta : ℕ -> Ω -> E)
    (hrec : ∀ n ω,
      delta (n + 1) ω =
        chewi123QuadraticStepMap (chewi125PowerStep gamma (n + 1)) A
          (delta n ω) -
          chewi125PowerStep gamma (n + 1) • S.martingale.xi (n + 1) ω)
    (hdelta0_meas : AEMeasurable (delta 0) P)
    (hdelta0_bound : ∀ ω, ‖delta 0 ω‖ ≤ B0) :
    TendstoInDistribution
        (fun N ω => chewi123ScaledAverageDelta (fun n => delta n ω) N)
        atTop (fun ω => -Ainv (S.Z ω)) (fun _ => P) Q ∧
      ProbabilityTheory.HasGaussianLaw (fun ω => -Ainv (S.Z ω)) Q ∧
      ∀ L R : StrongDual ℝ E,
        ProbabilityTheory.covarianceBilinDual
            (Q.map fun ω => -Ainv (S.Z ω)) L R =
          vaart1998_inverseDerivativeCovarianceFunctional (-Ainv)
            (fun L0 R0 =>
              ProbabilityTheory.covarianceBilinDual (Q.map S.Z) L0 R0) L R := by
  exact
    S.asgd_limit_package_source_quadratic_of_source_uniform_bound
      A Ainv hleft halpha hgamma_pos hgamma_lt hcoeff_bound hstep hsmall
      delta hrec hdelta0_meas hdelta0_bound
      (chewi123InitialCoefficient_sqrt_decay_of_norm_bound
        A (chewi125PowerStep gamma) C0 B0 hB0_nonneg hinitial_bound
        hinitial_decay)

/--
Source-aligned Chewi Theorem 12.3 ASGD weak-limit package when the initial
coefficient is uniformly bounded.  This removes the explicit
`hInitial_decay` input from the V142 source-uniform wrapper.
-/
theorem Chewi127BoundedMartingaleCLTSource.asgd_limit_package_source_quadratic_of_source_uniform_bound_and_uniform_initial_norm_bound
    {Ω Ω' E : Type*} [mΩ : MeasurableSpace Ω] {P : Measure Ω}
    [IsProbabilityMeasure P] [MeasurableSpace Ω'] {Q : Measure Ω'}
    [IsProbabilityMeasure Q]
    [NormedAddCommGroup E] [InnerProductSpace ℝ E] [CompleteSpace E]
    [MeasurableSpace E] [SecondCountableTopology E] [BorelSpace E]
    [OpensMeasurableSpace E]
    (S : Chewi127BoundedMartingaleCLTSource Ω Ω' E P Q)
    (A Ainv : E →L[ℝ] E) {alpha gamma K C0 B0 : ℝ}
    (hleft : Ainv * A = 1)
    (halpha : 0 < alpha) (hgamma_pos : 0 < gamma) (hgamma_lt : gamma < 1)
    (hcoeff_bound : ∀ N k, k ∈ Finset.Ico 1 N ->
      ‖chewi123SourceNoiseCoefficient A (chewi125PowerStep gamma) k N - Ainv‖ ≤ K)
    (hstep : ∀ m, 2 ≤ m ->
      ‖chewi123QuadraticStepMap (chewi125PowerStep gamma m) A‖ ≤
        1 - alpha * chewi125PowerStep gamma m)
    (hsmall : ∀ m, 2 ≤ m ->
      0 ≤ 1 - alpha * chewi125PowerStep gamma m)
    (hB0_nonneg : 0 ≤ B0)
    (hinitial_bound : ∀ N,
      ‖chewi123InitialCoefficient A (chewi125PowerStep gamma) N‖ ≤ C0)
    (delta : ℕ -> Ω -> E)
    (hrec : ∀ n ω,
      delta (n + 1) ω =
        chewi123QuadraticStepMap (chewi125PowerStep gamma (n + 1)) A
          (delta n ω) -
          chewi125PowerStep gamma (n + 1) • S.martingale.xi (n + 1) ω)
    (hdelta0_meas : AEMeasurable (delta 0) P)
    (hdelta0_bound : ∀ ω, ‖delta 0 ω‖ ≤ B0) :
    TendstoInDistribution
        (fun N ω => chewi123ScaledAverageDelta (fun n => delta n ω) N)
        atTop (fun ω => -Ainv (S.Z ω)) (fun _ => P) Q ∧
      ProbabilityTheory.HasGaussianLaw (fun ω => -Ainv (S.Z ω)) Q ∧
      ∀ L R : StrongDual ℝ E,
        ProbabilityTheory.covarianceBilinDual
            (Q.map fun ω => -Ainv (S.Z ω)) L R =
          vaart1998_inverseDerivativeCovarianceFunctional (-Ainv)
            (fun L0 R0 =>
              ProbabilityTheory.covarianceBilinDual (Q.map S.Z) L0 R0) L R := by
  exact
    S.asgd_limit_package_source_quadratic_of_source_uniform_bound
      A Ainv hleft halpha hgamma_pos hgamma_lt hcoeff_bound hstep hsmall
      delta hrec hdelta0_meas hdelta0_bound
      (chewi123InitialCoefficient_sqrt_decay_of_uniform_norm_bound
        A (chewi125PowerStep gamma) C0 B0 hB0_nonneg hinitial_bound)

/--
Source-aligned Chewi Theorem 12.3 ASGD weak-limit package with scalar
coefficient majorants for both the initial coefficient and the residual row.
The residual majorant only needs a uniform cap because the L2/martingale route
uses the coefficient row through the uniform diagonal estimate.
-/
theorem Chewi127BoundedMartingaleCLTSource.asgd_limit_package_source_quadratic_of_source_uniform_bound_and_scalar_coefficient_bounds
    {Ω Ω' E : Type*} [mΩ : MeasurableSpace Ω] {P : Measure Ω}
    [IsProbabilityMeasure P] [MeasurableSpace Ω'] {Q : Measure Ω'}
    [IsProbabilityMeasure Q]
    [NormedAddCommGroup E] [InnerProductSpace ℝ E] [CompleteSpace E]
    [MeasurableSpace E] [SecondCountableTopology E] [BorelSpace E]
    [OpensMeasurableSpace E]
    (S : Chewi127BoundedMartingaleCLTSource Ω Ω' E P Q)
    (A Ainv : E →L[ℝ] E) {alpha gamma K B0 : ℝ}
    (C0 : ℕ -> ℝ) (R : ℕ -> ℕ -> ℝ)
    (hleft : Ainv * A = 1)
    (halpha : 0 < alpha) (hgamma_pos : 0 < gamma) (hgamma_lt : gamma < 1)
    (hstep : ∀ m, 2 ≤ m ->
      ‖chewi123QuadraticStepMap (chewi125PowerStep gamma m) A‖ ≤
        1 - alpha * chewi125PowerStep gamma m)
    (hsmall : ∀ m, 2 ≤ m ->
      0 ≤ 1 - alpha * chewi125PowerStep gamma m)
    (hB0_nonneg : 0 ≤ B0)
    (hinitial_bound : ∀ N,
      ‖chewi123InitialCoefficient A (chewi125PowerStep gamma) N‖ ≤ C0 N)
    (hresidual_bound : ∀ N k, k ∈ Finset.Ico 1 N ->
      ‖chewi123SourceNoiseCoefficient A (chewi125PowerStep gamma) k N - Ainv‖ ≤ R N k)
    (hresidual_uniform_bound : ∀ N k, k ∈ Finset.Ico 1 N -> R N k ≤ K)
    (hinitial_decay :
      Tendsto
        (fun N : ℕ =>
          ‖(Real.sqrt (N : ℝ))⁻¹‖ * C0 N * B0)
        atTop (𝓝 0))
    (delta : ℕ -> Ω -> E)
    (hrec : ∀ n ω,
      delta (n + 1) ω =
        chewi123QuadraticStepMap (chewi125PowerStep gamma (n + 1)) A
          (delta n ω) -
          chewi125PowerStep gamma (n + 1) • S.martingale.xi (n + 1) ω)
    (hdelta0_meas : AEMeasurable (delta 0) P)
    (hdelta0_bound : ∀ ω, ‖delta 0 ω‖ ≤ B0) :
    TendstoInDistribution
        (fun N ω => chewi123ScaledAverageDelta (fun n => delta n ω) N)
        atTop (fun ω => -Ainv (S.Z ω)) (fun _ => P) Q ∧
      ProbabilityTheory.HasGaussianLaw (fun ω => -Ainv (S.Z ω)) Q ∧
      ∀ L R : StrongDual ℝ E,
        ProbabilityTheory.covarianceBilinDual
            (Q.map fun ω => -Ainv (S.Z ω)) L R =
          vaart1998_inverseDerivativeCovarianceFunctional (-Ainv)
            (fun L0 R0 =>
              ProbabilityTheory.covarianceBilinDual (Q.map S.Z) L0 R0) L R := by
  have hcoeff_bound : ∀ N k, k ∈ Finset.Ico 1 N ->
      ‖chewi123SourceNoiseCoefficient A (chewi125PowerStep gamma) k N - Ainv‖ ≤ K := by
    intro N k hk
    exact (hresidual_bound N k hk).trans (hresidual_uniform_bound N k hk)
  exact
    S.asgd_limit_package_source_quadratic_of_source_uniform_bound_and_initial_norm_bound
      A Ainv C0 hleft halpha hgamma_pos hgamma_lt hcoeff_bound hstep hsmall
      hB0_nonneg hinitial_bound hinitial_decay delta hrec hdelta0_meas
      hdelta0_bound

/--
Source-aligned Chewi Theorem 12.3 ASGD weak-limit package with the residual
coefficient bound discharged from the Chewi Lemma 12.5 power-step estimates.
Only the initial-coefficient scalar majorant remains supplied.
-/
theorem Chewi127BoundedMartingaleCLTSource.asgd_limit_package_source_quadratic_of_source_uniform_bound_and_quadratic_residual_bound
    {Ω Ω' E : Type*} [mΩ : MeasurableSpace Ω] {P : Measure Ω}
    [IsProbabilityMeasure P] [MeasurableSpace Ω'] {Q : Measure Ω'}
    [IsProbabilityMeasure Q]
    [NormedAddCommGroup E] [InnerProductSpace ℝ E] [CompleteSpace E]
    [MeasurableSpace E] [SecondCountableTopology E] [BorelSpace E]
    [OpensMeasurableSpace E]
    (S : Chewi127BoundedMartingaleCLTSource Ω Ω' E P Q)
    (A Ainv : E →L[ℝ] E) {alpha gamma B0 : ℝ}
    (C0 : ℕ -> ℝ)
    (hleft : Ainv * A = 1)
    (halpha : 0 < alpha) (hgamma_pos : 0 < gamma) (hgamma_lt : gamma < 1)
    (hstep : ∀ m, 2 ≤ m ->
      ‖chewi123QuadraticStepMap (chewi125PowerStep gamma m) A‖ ≤
        1 - alpha * chewi125PowerStep gamma m)
    (hsmall : ∀ m, 2 ≤ m ->
      0 ≤ 1 - alpha * chewi125PowerStep gamma m)
    (hB0_nonneg : 0 ≤ B0)
    (hinitial_bound : ∀ N,
      ‖chewi123InitialCoefficient A (chewi125PowerStep gamma) N‖ ≤ C0 N)
    (hinitial_decay :
      Tendsto
        (fun N : ℕ =>
          ‖(Real.sqrt (N : ℝ))⁻¹‖ * C0 N * B0)
        atTop (𝓝 0))
    (delta : ℕ -> Ω -> E)
    (hrec : ∀ n ω,
      delta (n + 1) ω =
        chewi123QuadraticStepMap (chewi125PowerStep gamma (n + 1)) A
          (delta n ω) -
          chewi125PowerStep gamma (n + 1) • S.martingale.xi (n + 1) ω)
    (hdelta0_meas : AEMeasurable (delta 0) P)
    (hdelta0_bound : ∀ ω, ‖delta 0 ω‖ ≤ B0) :
    TendstoInDistribution
        (fun N ω => chewi123ScaledAverageDelta (fun n => delta n ω) N)
        atTop (fun ω => -Ainv (S.Z ω)) (fun _ => P) Q ∧
      ProbabilityTheory.HasGaussianLaw (fun ω => -Ainv (S.Z ω)) Q ∧
      ∀ L R : StrongDual ℝ E,
        ProbabilityTheory.covarianceBilinDual
            (Q.map fun ω => -Ainv (S.Z ω)) L R =
          vaart1998_inverseDerivativeCovarianceFunctional (-Ainv)
            (fun L0 R0 =>
              ProbabilityTheory.covarianceBilinDual (Q.map S.Z) L0 R0) L R := by
  have hcoeff_bound : ∀ N k, k ∈ Finset.Ico 1 N ->
      ‖chewi123SourceNoiseCoefficient A (chewi125PowerStep gamma) k N - Ainv‖ ≤
        chewi125ResidualCoefficientUniformConstant Ainv alpha gamma := by
    intro N k hk
    exact
      chewi125SourceNoiseCoefficient_sub_left_inv_norm_le_uniform_constant
        A Ainv hleft halpha hgamma_pos hgamma_lt hstep hsmall hk
  exact
    S.asgd_limit_package_source_quadratic_of_source_uniform_bound_and_initial_norm_bound
      A Ainv C0 hleft halpha hgamma_pos hgamma_lt hcoeff_bound hstep hsmall
      hB0_nonneg hinitial_bound hinitial_decay delta hrec hdelta0_meas
      hdelta0_bound

/--
Source-aligned Chewi Theorem 12.3 ASGD weak-limit package with both the
initial decay and the residual coefficient bound discharged by deterministic
quadratic power-step estimates.
-/
theorem Chewi127BoundedMartingaleCLTSource.asgd_limit_package_source_quadratic_of_source_uniform_bound_and_uniform_initial_norm_bound_and_quadratic_residual_bound
    {Ω Ω' E : Type*} [mΩ : MeasurableSpace Ω] {P : Measure Ω}
    [IsProbabilityMeasure P] [MeasurableSpace Ω'] {Q : Measure Ω'}
    [IsProbabilityMeasure Q]
    [NormedAddCommGroup E] [InnerProductSpace ℝ E] [CompleteSpace E]
    [MeasurableSpace E] [SecondCountableTopology E] [BorelSpace E]
    [OpensMeasurableSpace E]
    (S : Chewi127BoundedMartingaleCLTSource Ω Ω' E P Q)
    (A Ainv : E →L[ℝ] E) {alpha gamma C0 B0 : ℝ}
    (hleft : Ainv * A = 1)
    (halpha : 0 < alpha) (hgamma_pos : 0 < gamma) (hgamma_lt : gamma < 1)
    (hstep : ∀ m, 2 ≤ m ->
      ‖chewi123QuadraticStepMap (chewi125PowerStep gamma m) A‖ ≤
        1 - alpha * chewi125PowerStep gamma m)
    (hsmall : ∀ m, 2 ≤ m ->
      0 ≤ 1 - alpha * chewi125PowerStep gamma m)
    (hB0_nonneg : 0 ≤ B0)
    (hinitial_bound : ∀ N,
      ‖chewi123InitialCoefficient A (chewi125PowerStep gamma) N‖ ≤ C0)
    (delta : ℕ -> Ω -> E)
    (hrec : ∀ n ω,
      delta (n + 1) ω =
        chewi123QuadraticStepMap (chewi125PowerStep gamma (n + 1)) A
          (delta n ω) -
          chewi125PowerStep gamma (n + 1) • S.martingale.xi (n + 1) ω)
    (hdelta0_meas : AEMeasurable (delta 0) P)
    (hdelta0_bound : ∀ ω, ‖delta 0 ω‖ ≤ B0) :
    TendstoInDistribution
        (fun N ω => chewi123ScaledAverageDelta (fun n => delta n ω) N)
        atTop (fun ω => -Ainv (S.Z ω)) (fun _ => P) Q ∧
      ProbabilityTheory.HasGaussianLaw (fun ω => -Ainv (S.Z ω)) Q ∧
      ∀ L R : StrongDual ℝ E,
        ProbabilityTheory.covarianceBilinDual
            (Q.map fun ω => -Ainv (S.Z ω)) L R =
          vaart1998_inverseDerivativeCovarianceFunctional (-Ainv)
            (fun L0 R0 =>
              ProbabilityTheory.covarianceBilinDual (Q.map S.Z) L0 R0) L R := by
  have hcoeff_bound : ∀ N k, k ∈ Finset.Ico 1 N ->
      ‖chewi123SourceNoiseCoefficient A (chewi125PowerStep gamma) k N - Ainv‖ ≤
        chewi125ResidualCoefficientUniformConstant Ainv alpha gamma := by
    intro N k hk
    exact
      chewi125SourceNoiseCoefficient_sub_left_inv_norm_le_uniform_constant
        A Ainv hleft halpha hgamma_pos hgamma_lt hstep hsmall hk
  exact
    S.asgd_limit_package_source_quadratic_of_source_uniform_bound_and_uniform_initial_norm_bound
      A Ainv hleft halpha hgamma_pos hgamma_lt hcoeff_bound hstep hsmall
      hB0_nonneg hinitial_bound delta hrec hdelta0_meas hdelta0_bound

/--
Source-aligned Chewi Theorem 12.3 ASGD weak-limit package with the residual
coefficient bound and scalar nonnegativity side condition discharged from a
single quadratic step-map contraction hypothesis.  This variant keeps the
more general initial-coefficient scalar majorant.
-/
theorem Chewi127BoundedMartingaleCLTSource.asgd_limit_package_source_quadratic_of_source_uniform_bound_and_initial_norm_bound_and_quadratic_step_bound
    {Ω Ω' E : Type*} [mΩ : MeasurableSpace Ω] {P : Measure Ω}
    [IsProbabilityMeasure P] [MeasurableSpace Ω'] {Q : Measure Ω'}
    [IsProbabilityMeasure Q]
    [NormedAddCommGroup E] [InnerProductSpace ℝ E] [CompleteSpace E]
    [MeasurableSpace E] [SecondCountableTopology E] [BorelSpace E]
    [OpensMeasurableSpace E]
    (S : Chewi127BoundedMartingaleCLTSource Ω Ω' E P Q)
    (A Ainv : E →L[ℝ] E) {alpha gamma B0 : ℝ}
    (C0 : ℕ -> ℝ)
    (hleft : Ainv * A = 1)
    (halpha : 0 < alpha) (hgamma_pos : 0 < gamma) (hgamma_lt : gamma < 1)
    (hstep : ∀ m, 2 ≤ m ->
      ‖chewi123QuadraticStepMap (chewi125PowerStep gamma m) A‖ ≤
        1 - alpha * chewi125PowerStep gamma m)
    (hB0_nonneg : 0 ≤ B0)
    (hinitial_bound : ∀ N,
      ‖chewi123InitialCoefficient A (chewi125PowerStep gamma) N‖ ≤ C0 N)
    (hinitial_decay :
      Tendsto
        (fun N : ℕ =>
          ‖(Real.sqrt (N : ℝ))⁻¹‖ * C0 N * B0)
        atTop (𝓝 0))
    (delta : ℕ -> Ω -> E)
    (hrec : ∀ n ω,
      delta (n + 1) ω =
        chewi123QuadraticStepMap (chewi125PowerStep gamma (n + 1)) A
          (delta n ω) -
          chewi125PowerStep gamma (n + 1) • S.martingale.xi (n + 1) ω)
    (hdelta0_meas : AEMeasurable (delta 0) P)
    (hdelta0_bound : ∀ ω, ‖delta 0 ω‖ ≤ B0) :
    TendstoInDistribution
        (fun N ω => chewi123ScaledAverageDelta (fun n => delta n ω) N)
        atTop (fun ω => -Ainv (S.Z ω)) (fun _ => P) Q ∧
      ProbabilityTheory.HasGaussianLaw (fun ω => -Ainv (S.Z ω)) Q ∧
      ∀ L R : StrongDual ℝ E,
        ProbabilityTheory.covarianceBilinDual
            (Q.map fun ω => -Ainv (S.Z ω)) L R =
          vaart1998_inverseDerivativeCovarianceFunctional (-Ainv)
            (fun L0 R0 =>
              ProbabilityTheory.covarianceBilinDual (Q.map S.Z) L0 R0) L R := by
  exact
    S.asgd_limit_package_source_quadratic_of_source_uniform_bound_and_quadratic_residual_bound
      A Ainv C0 hleft halpha hgamma_pos hgamma_lt hstep
      (chewi125QuadraticStepMap_hsmall_of_hstep A hstep)
      hB0_nonneg hinitial_bound hinitial_decay delta hrec hdelta0_meas
      hdelta0_bound

/--
Source-aligned Chewi Theorem 12.3 ASGD weak-limit package with the residual
coefficient and scalar nonnegativity side condition both discharged from the
single quadratic step-map contraction hypothesis.  This is the strongest
current source wrapper: the remaining deterministic contraction input is only
`hstep`.
-/
theorem Chewi127BoundedMartingaleCLTSource.asgd_limit_package_source_quadratic_of_source_uniform_bound_and_uniform_initial_norm_bound_and_quadratic_step_bound
    {Ω Ω' E : Type*} [mΩ : MeasurableSpace Ω] {P : Measure Ω}
    [IsProbabilityMeasure P] [MeasurableSpace Ω'] {Q : Measure Ω'}
    [IsProbabilityMeasure Q]
    [NormedAddCommGroup E] [InnerProductSpace ℝ E] [CompleteSpace E]
    [MeasurableSpace E] [SecondCountableTopology E] [BorelSpace E]
    [OpensMeasurableSpace E]
    (S : Chewi127BoundedMartingaleCLTSource Ω Ω' E P Q)
    (A Ainv : E →L[ℝ] E) {alpha gamma C0 B0 : ℝ}
    (hleft : Ainv * A = 1)
    (halpha : 0 < alpha) (hgamma_pos : 0 < gamma) (hgamma_lt : gamma < 1)
    (hstep : ∀ m, 2 ≤ m ->
      ‖chewi123QuadraticStepMap (chewi125PowerStep gamma m) A‖ ≤
        1 - alpha * chewi125PowerStep gamma m)
    (hB0_nonneg : 0 ≤ B0)
    (hinitial_bound : ∀ N,
      ‖chewi123InitialCoefficient A (chewi125PowerStep gamma) N‖ ≤ C0)
    (delta : ℕ -> Ω -> E)
    (hrec : ∀ n ω,
      delta (n + 1) ω =
        chewi123QuadraticStepMap (chewi125PowerStep gamma (n + 1)) A
          (delta n ω) -
          chewi125PowerStep gamma (n + 1) • S.martingale.xi (n + 1) ω)
    (hdelta0_meas : AEMeasurable (delta 0) P)
    (hdelta0_bound : ∀ ω, ‖delta 0 ω‖ ≤ B0) :
    TendstoInDistribution
        (fun N ω => chewi123ScaledAverageDelta (fun n => delta n ω) N)
        atTop (fun ω => -Ainv (S.Z ω)) (fun _ => P) Q ∧
      ProbabilityTheory.HasGaussianLaw (fun ω => -Ainv (S.Z ω)) Q ∧
      ∀ L R : StrongDual ℝ E,
        ProbabilityTheory.covarianceBilinDual
            (Q.map fun ω => -Ainv (S.Z ω)) L R =
          vaart1998_inverseDerivativeCovarianceFunctional (-Ainv)
            (fun L0 R0 =>
              ProbabilityTheory.covarianceBilinDual (Q.map S.Z) L0 R0) L R := by
  exact
    S.asgd_limit_package_source_quadratic_of_source_uniform_bound_and_uniform_initial_norm_bound_and_quadratic_residual_bound
      A Ainv hleft halpha hgamma_pos hgamma_lt hstep
      (chewi125QuadraticStepMap_hsmall_of_hstep A hstep)
      hB0_nonneg hinitial_bound delta hrec hdelta0_meas hdelta0_bound

/--
Source-aligned Chewi Theorem 12.3 ASGD weak-limit package with the residual
coefficient and the initial-coefficient bound both discharged from the single
quadratic step-map contraction hypothesis.
-/
theorem Chewi127BoundedMartingaleCLTSource.asgd_limit_package_source_quadratic_of_source_uniform_bound_and_quadratic_step_bound
    {Ω Ω' E : Type*} [mΩ : MeasurableSpace Ω] {P : Measure Ω}
    [IsProbabilityMeasure P] [MeasurableSpace Ω'] {Q : Measure Ω'}
    [IsProbabilityMeasure Q]
    [NormedAddCommGroup E] [InnerProductSpace ℝ E] [CompleteSpace E]
    [MeasurableSpace E] [SecondCountableTopology E] [BorelSpace E]
    [OpensMeasurableSpace E]
    (S : Chewi127BoundedMartingaleCLTSource Ω Ω' E P Q)
    (A Ainv : E →L[ℝ] E) {alpha gamma B0 : ℝ}
    (hleft : Ainv * A = 1)
    (halpha : 0 < alpha) (hgamma_pos : 0 < gamma) (hgamma_lt : gamma < 1)
    (hstep : ∀ m, 2 ≤ m ->
      ‖chewi123QuadraticStepMap (chewi125PowerStep gamma m) A‖ ≤
        1 - alpha * chewi125PowerStep gamma m)
    (hB0_nonneg : 0 ≤ B0)
    (delta : ℕ -> Ω -> E)
    (hrec : ∀ n ω,
      delta (n + 1) ω =
        chewi123QuadraticStepMap (chewi125PowerStep gamma (n + 1)) A
          (delta n ω) -
          chewi125PowerStep gamma (n + 1) • S.martingale.xi (n + 1) ω)
    (hdelta0_meas : AEMeasurable (delta 0) P)
    (hdelta0_bound : ∀ ω, ‖delta 0 ω‖ ≤ B0) :
    TendstoInDistribution
        (fun N ω => chewi123ScaledAverageDelta (fun n => delta n ω) N)
        atTop (fun ω => -Ainv (S.Z ω)) (fun _ => P) Q ∧
      ProbabilityTheory.HasGaussianLaw (fun ω => -Ainv (S.Z ω)) Q ∧
      ∀ L R : StrongDual ℝ E,
        ProbabilityTheory.covarianceBilinDual
            (Q.map fun ω => -Ainv (S.Z ω)) L R =
          vaart1998_inverseDerivativeCovarianceFunctional (-Ainv)
            (fun L0 R0 =>
              ProbabilityTheory.covarianceBilinDual (Q.map S.Z) L0 R0) L R := by
  let C0 : ℝ := chewi125InitialCoefficientUniformConstant A alpha gamma
  have hsmall : ∀ m, 2 ≤ m ->
      0 ≤ 1 - alpha * chewi125PowerStep gamma m :=
    chewi125QuadraticStepMap_hsmall_of_hstep A hstep
  have hinitial_bound : ∀ N,
      ‖chewi123InitialCoefficient A (chewi125PowerStep gamma) N‖ ≤ C0 := by
    intro N
    simpa [C0] using
      chewi123InitialCoefficient_norm_le_uniform_constant_of_quadratic_step_bound
        A halpha hgamma_pos hgamma_lt hstep hsmall N
  exact
    S.asgd_limit_package_source_quadratic_of_source_uniform_bound_and_uniform_initial_norm_bound_and_quadratic_step_bound
      A Ainv hleft halpha hgamma_pos hgamma_lt hstep hB0_nonneg
      hinitial_bound delta hrec hdelta0_meas hdelta0_bound

/--
Characteristic-function-source version of the strongest source-aligned Chewi
Theorem 12.3 ASGD weak-limit wrapper.  This connects the Chewi Theorem 12.7
bounded martingale CLT interface to the endpoint-corrected ASGD package after
the characteristic-function source has supplied its projected scalar CLTs.
-/
theorem Chewi127BoundedMartingaleCharFunCLTSource.asgd_limit_package_source_quadratic_of_source_uniform_bound_and_quadratic_step_bound
    {Ω Ω' E : Type*} [mΩ : MeasurableSpace Ω] {P : Measure Ω}
    [IsProbabilityMeasure P] [MeasurableSpace Ω'] {Q : Measure Ω'}
    [IsProbabilityMeasure Q]
    [NormedAddCommGroup E] [InnerProductSpace ℝ E] [CompleteSpace E]
    [MeasurableSpace E] [SecondCountableTopology E] [BorelSpace E]
    [OpensMeasurableSpace E]
    (S : Chewi127BoundedMartingaleCharFunCLTSource Ω Ω' E P Q)
    (A Ainv : E →L[ℝ] E) {alpha gamma B0 : ℝ}
    (hleft : Ainv * A = 1)
    (halpha : 0 < alpha) (hgamma_pos : 0 < gamma) (hgamma_lt : gamma < 1)
    (hstep : ∀ m, 2 ≤ m ->
      ‖chewi123QuadraticStepMap (chewi125PowerStep gamma m) A‖ ≤
        1 - alpha * chewi125PowerStep gamma m)
    (hB0_nonneg : 0 ≤ B0)
    (delta : ℕ -> Ω -> E)
    (hrec : ∀ n ω,
      delta (n + 1) ω =
        chewi123QuadraticStepMap (chewi125PowerStep gamma (n + 1)) A
          (delta n ω) -
          chewi125PowerStep gamma (n + 1) • S.martingale.xi (n + 1) ω)
    (hdelta0_meas : AEMeasurable (delta 0) P)
    (hdelta0_bound : ∀ ω, ‖delta 0 ω‖ ≤ B0) :
    TendstoInDistribution
        (fun N ω => chewi123ScaledAverageDelta (fun n => delta n ω) N)
        atTop (fun ω => -Ainv (S.Z ω)) (fun _ => P) Q ∧
      ProbabilityTheory.HasGaussianLaw (fun ω => -Ainv (S.Z ω)) Q ∧
      ∀ L R : StrongDual ℝ E,
        ProbabilityTheory.covarianceBilinDual
            (Q.map fun ω => -Ainv (S.Z ω)) L R =
          vaart1998_inverseDerivativeCovarianceFunctional (-Ainv)
            (fun L0 R0 =>
              ProbabilityTheory.covarianceBilinDual (Q.map S.Z) L0 R0) L R := by
  simpa [Chewi127BoundedMartingaleCharFunCLTSource.toBoundedMartingaleCLTSource]
    using
      S.toBoundedMartingaleCLTSource.asgd_limit_package_source_quadratic_of_source_uniform_bound_and_quadratic_step_bound
        A Ainv hleft halpha hgamma_pos hgamma_lt hstep hB0_nonneg delta hrec
        hdelta0_meas hdelta0_bound

/--
Non-circular-core version of the strongest current source-aligned Chewi
Theorem 12.3 ASGD weak-limit wrapper.  The Chewi Theorem 12.7 scalar
characteristic-function theorem is discharged internally from the core
boundedness and averaged-covariance assumptions.
-/
theorem Chewi127BoundedMartingaleCharFunCLTCore.asgd_limit_package_source_quadratic_of_source_uniform_bound_and_quadratic_step_bound
    {Ω Ω' E : Type*} [mΩ : MeasurableSpace Ω] {P : Measure Ω}
    [IsProbabilityMeasure P] [MeasurableSpace Ω'] {Q : Measure Ω'}
    [IsProbabilityMeasure Q]
    [NormedAddCommGroup E] [InnerProductSpace ℝ E] [CompleteSpace E]
    [MeasurableSpace E] [SecondCountableTopology E] [BorelSpace E]
    [OpensMeasurableSpace E]
    (S : Chewi127BoundedMartingaleCharFunCLTCore Ω Ω' E P Q)
    (A Ainv : E →L[ℝ] E) {alpha gamma B0 : ℝ}
    (hleft : Ainv * A = 1)
    (halpha : 0 < alpha) (hgamma_pos : 0 < gamma) (hgamma_lt : gamma < 1)
    (hstep : ∀ m, 2 ≤ m ->
      ‖chewi123QuadraticStepMap (chewi125PowerStep gamma m) A‖ ≤
        1 - alpha * chewi125PowerStep gamma m)
    (hB0_nonneg : 0 ≤ B0)
    (delta : ℕ -> Ω -> E)
    (hrec : ∀ n ω,
      delta (n + 1) ω =
        chewi123QuadraticStepMap (chewi125PowerStep gamma (n + 1)) A
          (delta n ω) -
          chewi125PowerStep gamma (n + 1) • S.martingale.xi (n + 1) ω)
    (hdelta0_meas : AEMeasurable (delta 0) P)
    (hdelta0_bound : ∀ ω, ‖delta 0 ω‖ ≤ B0) :
    TendstoInDistribution
        (fun N ω => chewi123ScaledAverageDelta (fun n => delta n ω) N)
        atTop (fun ω => -Ainv (S.Z ω)) (fun _ => P) Q ∧
      ProbabilityTheory.HasGaussianLaw (fun ω => -Ainv (S.Z ω)) Q ∧
      ∀ L R : StrongDual ℝ E,
        ProbabilityTheory.covarianceBilinDual
            (Q.map fun ω => -Ainv (S.Z ω)) L R =
          vaart1998_inverseDerivativeCovarianceFunctional (-Ainv)
            (fun L0 R0 =>
              ProbabilityTheory.covarianceBilinDual (Q.map S.Z) L0 R0) L R := by
  simpa [Chewi127BoundedMartingaleCharFunCLTCore.toCharFunCLTSource_of_uniform_bound_no_factor_bound]
    using
      S.toCharFunCLTSource_of_uniform_bound_no_factor_bound.asgd_limit_package_source_quadratic_of_source_uniform_bound_and_quadratic_step_bound
        A Ainv hleft halpha hgamma_pos hgamma_lt hstep hB0_nonneg delta hrec
        hdelta0_meas hdelta0_bound

end Optimization
end StatInference
