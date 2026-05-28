import StatInference.Optimization.ASGD
import Mathlib.Analysis.SpecialFunctions.Integrals.Basic

/-!
# Endpoint correction for Chewi's quadratic ASGD display

Chewi's deterministic display (12.5) uses the source sum indexed by
`Finset.Ico 1 N`, while the martingale CLT normalization in Theorem 12.7 uses
the first `N` increments, represented in Lean as `Finset.range N` with index
`k + 1`.  This file packages the harmless endpoint correction as an explicit
remainder term so the source-shaped ASGD handoff can use the martingale CLT sum
without changing the deterministic source display.
-/

namespace StatInference
namespace Optimization

open Filter MeasureTheory ProbabilityTheory
open StatInference.AsymptoticStatistics
open Finset
open Asymptotics
open scoped BigOperators Topology

/--
Any source step-map norm bound of the form `||I - hA|| <= 1 - α h` implies
the scalar factor `1 - α h` is nonnegative.
-/
theorem chewi123QuadraticStepMap_one_sub_nonneg_of_norm_le
    {E : Type*} [NormedAddCommGroup E] [NormedSpace ℝ E]
    (A : E →L[ℝ] E) {alpha h : ℝ}
    (hstep : ‖chewi123QuadraticStepMap h A‖ ≤ 1 - alpha * h) :
    0 ≤ 1 - alpha * h :=
  (norm_nonneg (chewi123QuadraticStepMap h A)).trans hstep

/-- Reindex the shifted `range N` sum as the source `Ico 1 N` sum plus endpoint. -/
theorem chewi123_sum_range_succ_eq_sum_Ico_add_endpoint
    {E : Type*} [AddCommMonoid E] (f : ℕ -> E) {N : ℕ} (hN : N ≠ 0) :
    (∑ k ∈ Finset.range N, f (k + 1)) =
      (∑ k ∈ Finset.Ico 1 N, f k) + f N := by
  cases N with
  | zero => contradiction
  | succ n =>
      rw [Finset.sum_range_succ, Finset.sum_Ico_eq_sum_range]
      simp [Nat.add_comm]

/-- Deterministic version of the martingale-CLT scaled noise sum. -/
noncomputable def chewi123RangeScaledNoiseSum
    {E : Type*} [NormedAddCommGroup E] [NormedSpace ℝ E]
    (xi : ℕ -> E) (N : ℕ) : E :=
  (Real.sqrt (N : ℝ))⁻¹ • ∑ k ∈ Finset.range N, xi (k + 1)

/-- Deterministic `sqrt N`-scaled averaged quadratic ASGD error. -/
noncomputable def chewi123ScaledAverageDelta
    {E : Type*} [NormedAddCommGroup E] [NormedSpace ℝ E]
    (delta : ℕ -> E) (N : ℕ) : E :=
  Real.sqrt (N : ℝ) • ((N : ℝ)⁻¹ • ∑ i ∈ Finset.range N, delta i)

/-- The initial-condition term in the `sqrt N`-scaled quadratic ASGD display. -/
noncomputable def chewi123ASGDInitialTerm
    {E : Type*} [NormedAddCommGroup E] [NormedSpace ℝ E]
    (A : E →L[ℝ] E) (h : ℕ -> ℝ) (x0 : E) (N : ℕ) : E :=
  (Real.sqrt (N : ℝ))⁻¹ • chewi123InitialCoefficient A h N x0

/-- Norm control for the initial-condition term in the `sqrt N` ASGD display. -/
theorem chewi123ASGDInitialTerm_norm_le_opNorm
    {E : Type*} [NormedAddCommGroup E] [NormedSpace ℝ E]
    (A : E →L[ℝ] E) (h : ℕ -> ℝ) (x0 : E) (N : ℕ) :
    ‖chewi123ASGDInitialTerm A h x0 N‖ ≤
      ‖(Real.sqrt (N : ℝ))⁻¹‖ * ‖chewi123InitialCoefficient A h N‖ *
        ‖x0‖ := by
  calc
    ‖chewi123ASGDInitialTerm A h x0 N‖ =
        ‖(Real.sqrt (N : ℝ))⁻¹‖ *
          ‖chewi123InitialCoefficient A h N x0‖ := by
      simp [chewi123ASGDInitialTerm, norm_smul]
    _ ≤ ‖(Real.sqrt (N : ℝ))⁻¹‖ *
          (‖chewi123InitialCoefficient A h N‖ * ‖x0‖) := by
      exact mul_le_mul_of_nonneg_left
        ((chewi123InitialCoefficient A h N).le_opNorm x0) (norm_nonneg _)
    _ = ‖(Real.sqrt (N : ℝ))⁻¹‖ *
          ‖chewi123InitialCoefficient A h N‖ * ‖x0‖ := by
      ring

/--
The ASGD initial-condition term is `o_P(1)` whenever the initial error is
uniformly bounded and the deterministic source coefficient has the displayed
`sqrt N`-scaled operator-norm decay.
-/
theorem chewi123ASGDInitialTerm_tendstoInMeasure_zero_of_opNorm_decay_bounded_initial
    {Ω E : Type*} [MeasurableSpace Ω] {P : Measure Ω}
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    (A : E →L[ℝ] E) (h : ℕ -> ℝ) (delta0 : Ω -> E) (B : ℝ)
    (hdelta0_bound : ∀ ω, ‖delta0 ω‖ ≤ B)
    (hdecay :
      Tendsto
        (fun N : ℕ =>
          ‖(Real.sqrt (N : ℝ))⁻¹‖ *
            ‖chewi123InitialCoefficient A h N‖ * B)
        atTop (𝓝 0)) :
    TendstoInMeasure P
      (fun N ω => chewi123ASGDInitialTerm A h (delta0 ω) N)
      atTop (fun _ => 0) := by
  simpa [StochasticLittleO] using
    vaart1998_stochastic_littleO_of_uniform_norm_bound
      (P := P)
      (X := fun N ω => chewi123ASGDInitialTerm A h (delta0 ω) N)
      (a := fun N : ℕ =>
        ‖(Real.sqrt (N : ℝ))⁻¹‖ *
          ‖chewi123InitialCoefficient A h N‖ * B)
      hdecay
      (Eventually.of_forall fun N ω =>
        (chewi123ASGDInitialTerm_norm_le_opNorm A h (delta0 ω) N).trans
          (mul_le_mul_of_nonneg_left (hdelta0_bound ω)
            (mul_nonneg (norm_nonneg _) (norm_nonneg _))))

/--
The source remainder with the endpoint correction needed to match
`chewi127ScaledNoiseSum`.
-/
noncomputable def chewi123ASGDEndpointCorrectedRemainder
    {E : Type*} [NormedAddCommGroup E] [NormedSpace ℝ E]
    (A Ainv : E →L[ℝ] E) (h : ℕ -> ℝ) (xi : ℕ -> E) (N : ℕ) : E :=
  (Real.sqrt (N : ℝ))⁻¹ • Ainv (xi N) -
    (Real.sqrt (N : ℝ))⁻¹ •
      ∑ k ∈ Finset.Ico 1 N,
        (chewi123SourceNoiseCoefficient A h k N - Ainv) (xi k)

/--
Deterministic norm control for the endpoint-corrected ASGD coefficient
remainder.
-/
theorem chewi123ASGDEndpointCorrectedRemainder_norm_le_opNorm_sum
    {E : Type*} [NormedAddCommGroup E] [NormedSpace ℝ E]
    (A Ainv : E →L[ℝ] E) (h : ℕ -> ℝ) (xi : ℕ -> E) (N : ℕ) :
    ‖chewi123ASGDEndpointCorrectedRemainder A Ainv h xi N‖ ≤
      ‖(Real.sqrt (N : ℝ))⁻¹‖ * ‖Ainv‖ * ‖xi N‖ +
        ‖(Real.sqrt (N : ℝ))⁻¹‖ *
          ∑ k ∈ Finset.Ico 1 N,
            ‖chewi123SourceNoiseCoefficient A h k N - Ainv‖ * ‖xi k‖ := by
  let c : ℝ := (Real.sqrt (N : ℝ))⁻¹
  let R : E := ∑ k ∈ Finset.Ico 1 N,
    (chewi123SourceNoiseCoefficient A h k N - Ainv) (xi k)
  have hfirst :
      ‖c • Ainv (xi N)‖ ≤ ‖c‖ * ‖Ainv‖ * ‖xi N‖ := by
    calc
      ‖c • Ainv (xi N)‖ = ‖c‖ * ‖Ainv (xi N)‖ := by
        simp [norm_smul]
      _ ≤ ‖c‖ * (‖Ainv‖ * ‖xi N‖) :=
        mul_le_mul_of_nonneg_left (Ainv.le_opNorm (xi N)) (norm_nonneg _)
      _ = ‖c‖ * ‖Ainv‖ * ‖xi N‖ := by
        ring
  have hsum :
      ‖R‖ ≤
        ∑ k ∈ Finset.Ico 1 N,
          ‖chewi123SourceNoiseCoefficient A h k N - Ainv‖ * ‖xi k‖ := by
    calc
      ‖R‖ ≤
          ∑ k ∈ Finset.Ico 1 N,
            ‖(chewi123SourceNoiseCoefficient A h k N - Ainv) (xi k)‖ := by
        simpa [R] using
          norm_sum_le
            (s := Finset.Ico 1 N)
            (f := fun k =>
              (chewi123SourceNoiseCoefficient A h k N - Ainv) (xi k))
      _ ≤
          ∑ k ∈ Finset.Ico 1 N,
            ‖chewi123SourceNoiseCoefficient A h k N - Ainv‖ * ‖xi k‖ :=
        Finset.sum_le_sum fun k _hk =>
          (chewi123SourceNoiseCoefficient A h k N - Ainv).le_opNorm (xi k)
  have hsecond :
      ‖c • R‖ ≤
        ‖c‖ *
          ∑ k ∈ Finset.Ico 1 N,
            ‖chewi123SourceNoiseCoefficient A h k N - Ainv‖ * ‖xi k‖ := by
    calc
      ‖c • R‖ = ‖c‖ * ‖R‖ := by
        simp [norm_smul]
      _ ≤
          ‖c‖ *
            ∑ k ∈ Finset.Ico 1 N,
              ‖chewi123SourceNoiseCoefficient A h k N - Ainv‖ * ‖xi k‖ :=
        mul_le_mul_of_nonneg_left hsum (norm_nonneg _)
  calc
    ‖chewi123ASGDEndpointCorrectedRemainder A Ainv h xi N‖ =
        ‖c • Ainv (xi N) - c • R‖ := by
      simp [chewi123ASGDEndpointCorrectedRemainder, c, R]
    _ ≤ ‖c • Ainv (xi N)‖ + ‖c • R‖ := norm_sub_le _ _
    _ ≤
        ‖c‖ * ‖Ainv‖ * ‖xi N‖ +
          ‖c‖ *
            ∑ k ∈ Finset.Ico 1 N,
              ‖chewi123SourceNoiseCoefficient A h k N - Ainv‖ * ‖xi k‖ :=
      add_le_add hfirst hsecond

/--
The endpoint-corrected coefficient remainder is `o_P(1)` under a uniform
noise bound and deterministic decay of the displayed coefficient row bound.
-/
theorem chewi123ASGDEndpointCorrectedRemainder_tendstoInMeasure_zero_of_uniform_noise_bound_and_coeff_decay
    {Ω E : Type*} [MeasurableSpace Ω] {P : Measure Ω}
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    (A Ainv : E →L[ℝ] E) (h : ℕ -> ℝ) (xi : ℕ -> Ω -> E) (B : ℝ)
    (hxi_bound : ∀ n ω, ‖xi n ω‖ ≤ B)
    (hdecay :
      Tendsto
        (fun N : ℕ =>
          ‖(Real.sqrt (N : ℝ))⁻¹‖ * ‖Ainv‖ * B +
            ‖(Real.sqrt (N : ℝ))⁻¹‖ *
              ∑ k ∈ Finset.Ico 1 N,
                ‖chewi123SourceNoiseCoefficient A h k N - Ainv‖ * B)
        atTop (𝓝 0)) :
    TendstoInMeasure P
      (fun N ω =>
        chewi123ASGDEndpointCorrectedRemainder A Ainv h
          (fun n => xi n ω) N)
      atTop (fun _ => 0) := by
  simpa [StochasticLittleO] using
    vaart1998_stochastic_littleO_of_uniform_norm_bound
      (P := P)
      (X := fun N ω =>
        chewi123ASGDEndpointCorrectedRemainder A Ainv h
          (fun n => xi n ω) N)
      (a := fun N : ℕ =>
        ‖(Real.sqrt (N : ℝ))⁻¹‖ * ‖Ainv‖ * B +
          ‖(Real.sqrt (N : ℝ))⁻¹‖ *
            ∑ k ∈ Finset.Ico 1 N,
              ‖chewi123SourceNoiseCoefficient A h k N - Ainv‖ * B)
      hdecay
      (Eventually.of_forall fun N ω => by
        have hbase :=
          chewi123ASGDEndpointCorrectedRemainder_norm_le_opNorm_sum
            A Ainv h (fun n => xi n ω) N
        refine hbase.trans (add_le_add ?_ ?_)
        · exact
            mul_le_mul_of_nonneg_left (hxi_bound N ω)
              (mul_nonneg (norm_nonneg _) (norm_nonneg _))
        · exact
            mul_le_mul_of_nonneg_left
              (Finset.sum_le_sum fun k _hk =>
                mul_le_mul_of_nonneg_left (hxi_bound k ω) (norm_nonneg _))
              (norm_nonneg _))

/--
Operator-norm control for the ordered transition product from scalar one-step
majorants.  This is the first deterministic reduction behind Chewi Lemma 12.5:
later spectral or step-size estimates only need to bound each
`I - h_n A` factor by a scalar `rho n`.
-/
theorem chewi123TransitionProductFrom_norm_le_prod_of_stepMap_norm_le
    {E : Type*} [NormedAddCommGroup E] [NormedSpace ℝ E]
    (A : E →L[ℝ] E) (h : ℕ -> ℝ) (rho : ℕ -> ℝ)
    (hrho : ∀ n, 0 ≤ rho n)
    (hstep : ∀ n, ‖chewi123QuadraticStepMap (h n) A‖ ≤ rho n)
    (start len : ℕ) :
    ‖chewi123TransitionProductFrom A h start len‖ ≤
      ∏ r ∈ Finset.range len, rho (start + r + 1) := by
  induction len with
  | zero =>
      simpa [chewi123TransitionProductFrom] using
        (ContinuousLinearMap.norm_id_le (𝕜 := ℝ) (E := E))
  | succ len ih =>
      rw [chewi123TransitionProductFrom]
      rw [Finset.prod_range_succ]
      have hmul :
          ‖chewi123QuadraticStepMap (h (start + len + 1)) A *
              chewi123TransitionProductFrom A h start len‖ ≤
            ‖chewi123QuadraticStepMap (h (start + len + 1)) A‖ *
              ‖chewi123TransitionProductFrom A h start len‖ :=
        norm_mul_le _ _
      have hmul2 :
          ‖chewi123QuadraticStepMap (h (start + len + 1)) A‖ *
              ‖chewi123TransitionProductFrom A h start len‖ ≤
            rho (start + len + 1) *
              ∏ r ∈ Finset.range len, rho (start + r + 1) := by
        exact mul_le_mul (hstep (start + len + 1)) ih
          (norm_nonneg _) (hrho _)
      exact hmul.trans (by simpa [mul_comm] using hmul2)

/--
Localized version of `chewi123TransitionProductFrom_norm_le_prod_of_stepMap_norm_le`.
Only the factors that actually occur in the transition product need scalar
one-step bounds.  This is the right interface for eventually-small step sizes
such as Chewi's `h_n = n^{-γ}`.
-/
theorem chewi123TransitionProductFrom_norm_le_prod_of_stepMap_norm_le_range
    {E : Type*} [NormedAddCommGroup E] [NormedSpace ℝ E]
    (A : E →L[ℝ] E) (h : ℕ -> ℝ) (rho : ℕ -> ℝ)
    (start len : ℕ)
    (hrho : ∀ r ∈ Finset.range len, 0 ≤ rho (start + r + 1))
    (hstep : ∀ r ∈ Finset.range len,
      ‖chewi123QuadraticStepMap (h (start + r + 1)) A‖ ≤
        rho (start + r + 1)) :
    ‖chewi123TransitionProductFrom A h start len‖ ≤
      ∏ r ∈ Finset.range len, rho (start + r + 1) := by
  induction len with
  | zero =>
      simpa [chewi123TransitionProductFrom] using
        (ContinuousLinearMap.norm_id_le (𝕜 := ℝ) (E := E))
  | succ len ih =>
      rw [chewi123TransitionProductFrom]
      rw [Finset.prod_range_succ]
      have hprev :
          ‖chewi123TransitionProductFrom A h start len‖ ≤
            ∏ r ∈ Finset.range len, rho (start + r + 1) := by
        refine ih ?_ ?_
        · intro r hr
          exact hrho r (Finset.mem_range.mpr
            (Nat.lt_trans (Finset.mem_range.mp hr) (Nat.lt_succ_self len)))
        · intro r hr
          exact hstep r (Finset.mem_range.mpr
            (Nat.lt_trans (Finset.mem_range.mp hr) (Nat.lt_succ_self len)))
      have hmul :
          ‖chewi123QuadraticStepMap (h (start + len + 1)) A *
              chewi123TransitionProductFrom A h start len‖ ≤
            ‖chewi123QuadraticStepMap (h (start + len + 1)) A‖ *
              ‖chewi123TransitionProductFrom A h start len‖ :=
        norm_mul_le _ _
      have hmul2 :
          ‖chewi123QuadraticStepMap (h (start + len + 1)) A‖ *
              ‖chewi123TransitionProductFrom A h start len‖ ≤
            rho (start + len + 1) *
              ∏ r ∈ Finset.range len, rho (start + r + 1) := by
        exact mul_le_mul
          (hstep len (Finset.mem_range.mpr (Nat.lt_succ_self len))) hprev
          (norm_nonneg _)
          (hrho len (Finset.mem_range.mpr (Nat.lt_succ_self len)))
      exact hmul.trans (by simpa [mul_comm] using hmul2)

/--
Scalar product-to-exponential estimate used in Chewi Lemma 12.5.  It is the
finite product form of `1 - a <= exp (-a)`, with explicit nonnegativity of the
left factors so it can be used under `Finset.prod_le_prod`.
-/
theorem chewi123_scalar_prod_one_sub_le_exp_neg_sum
    {ι : Type*} (s : Finset ι) (a : ι -> ℝ)
    (hfactor_nonneg : ∀ i ∈ s, 0 ≤ 1 - a i) :
    (∏ i ∈ s, (1 - a i)) ≤
      Real.exp (-(∑ i ∈ s, a i)) := by
  calc
    (∏ i ∈ s, (1 - a i))
        ≤ ∏ i ∈ s, Real.exp (-(a i)) := by
          refine Finset.prod_le_prod hfactor_nonneg ?_
          intro i _hi
          simpa [sub_eq_add_neg, add_comm] using Real.add_one_le_exp (-(a i))
    _ = Real.exp (∑ i ∈ s, -(a i)) := by
          simpa using (Real.exp_sum s (fun i => -(a i))).symm
    _ = Real.exp (-(∑ i ∈ s, a i)) := by
          rw [Finset.sum_neg_distrib]

/--
Exponential transition-product majorant from one-step contraction factors.
This is the formal version of Chewi's bound
`||B_k^n|| <= prod_l (1 - alpha h_l) <= exp (-alpha sum_l h_l)`,
with the spectral step `||I - h_l A|| <= 1 - alpha h_l` kept as an explicit
input.
-/
theorem chewi123TransitionProductFrom_norm_le_exp_neg_sum_of_stepMap_norm_le_one_sub
    {E : Type*} [NormedAddCommGroup E] [NormedSpace ℝ E]
    (A : E →L[ℝ] E) (h : ℕ -> ℝ) (alpha : ℝ)
    (hrho : ∀ n, 0 ≤ 1 - alpha * h n)
    (hstep : ∀ n,
      ‖chewi123QuadraticStepMap (h n) A‖ ≤ 1 - alpha * h n)
    (start len : ℕ) :
    ‖chewi123TransitionProductFrom A h start len‖ ≤
      Real.exp (-(∑ r ∈ Finset.range len, alpha * h (start + r + 1))) := by
  have hprod :=
    chewi123TransitionProductFrom_norm_le_prod_of_stepMap_norm_le
      A h (fun n => 1 - alpha * h n) hrho hstep start len
  exact hprod.trans
    (chewi123_scalar_prod_one_sub_le_exp_neg_sum
      (s := Finset.range len)
      (a := fun r => alpha * h (start + r + 1))
      (fun r _hr => hrho (start + r + 1)))

/--
Localized exponential transition-product majorant.  This is the interval-local
form needed once the contraction `||I - h_n A|| <= 1 - alpha h_n` is only known
eventually or on the current source interval.
-/
theorem chewi123TransitionProductFrom_norm_le_exp_neg_sum_of_stepMap_norm_le_one_sub_range
    {E : Type*} [NormedAddCommGroup E] [NormedSpace ℝ E]
    (A : E →L[ℝ] E) (h : ℕ -> ℝ) (alpha : ℝ)
    (start len : ℕ)
    (hrho : ∀ r ∈ Finset.range len,
      0 ≤ 1 - alpha * h (start + r + 1))
    (hstep : ∀ r ∈ Finset.range len,
      ‖chewi123QuadraticStepMap (h (start + r + 1)) A‖ ≤
        1 - alpha * h (start + r + 1)) :
    ‖chewi123TransitionProductFrom A h start len‖ ≤
      Real.exp (-(∑ r ∈ Finset.range len, alpha * h (start + r + 1))) := by
  have hprod :=
    chewi123TransitionProductFrom_norm_le_prod_of_stepMap_norm_le_range
      A h (fun n => 1 - alpha * h n) start len hrho hstep
  exact hprod.trans
    (chewi123_scalar_prod_one_sub_le_exp_neg_sum
      (s := Finset.range len)
      (a := fun r => alpha * h (start + r + 1))
      hrho)

/-- Chewi Lemma 12.5 step size `h_n = n^{-γ}`, with a harmless value at zero. -/
noncomputable def chewi125PowerStep (gamma : ℝ) (n : ℕ) : ℝ :=
  if n = 0 then 1 else (n : ℝ) ^ (-gamma)

/-- For positive indices, `chewi125PowerStep` is exactly `n^{-γ}`. -/
theorem chewi125PowerStep_of_pos (gamma : ℝ) {n : ℕ} (hn : 0 < n) :
    chewi125PowerStep gamma n = (n : ℝ) ^ (-gamma) := by
  simp [chewi125PowerStep, ne_of_gt hn]

/-- Positivity of Chewi's power step size on positive indices. -/
theorem chewi125PowerStep_pos (gamma : ℝ) {n : ℕ} (hn : 0 < n) :
    0 < chewi125PowerStep gamma n := by
  rw [chewi125PowerStep_of_pos gamma hn]
  exact Real.rpow_pos_of_pos (Nat.cast_pos.mpr hn) (-gamma)

/--
Power-step version: the `hsmall` hypothesis used in the product/exponential
row estimates follows automatically from the corresponding step-map norm
contraction hypothesis.
-/
theorem chewi125QuadraticStepMap_hsmall_of_hstep
    {E : Type*} [NormedAddCommGroup E] [NormedSpace ℝ E]
    (A : E →L[ℝ] E) {alpha gamma : ℝ}
    (hstep : ∀ m, 2 ≤ m ->
      ‖chewi123QuadraticStepMap (chewi125PowerStep gamma m) A‖ ≤
        1 - alpha * chewi125PowerStep gamma m) :
    ∀ m, 2 ≤ m -> 0 ≤ 1 - alpha * chewi125PowerStep gamma m := by
  intro m hm
  exact chewi123QuadraticStepMap_one_sub_nonneg_of_norm_le A (hstep m hm)

/--
Source-shaped transition-product estimate for Chewi Lemma 12.5 with
`h_n = n^{-γ}`.  The one-step contraction is required only on the displayed
interval `l = k+1, ..., j`.
-/
theorem chewi125_transitionProduct_norm_le_exp_sum
    {E : Type*} [NormedAddCommGroup E] [NormedSpace ℝ E]
    (A : E →L[ℝ] E) {alpha gamma : ℝ} {N0 k j : ℕ}
    (hstep : ∀ m, N0 ≤ m ->
      ‖chewi123QuadraticStepMap (chewi125PowerStep gamma m) A‖ ≤
        1 - alpha * chewi125PowerStep gamma m)
    (hsmall : ∀ m, N0 ≤ m ->
      0 ≤ 1 - alpha * chewi125PowerStep gamma m)
    (hk : N0 ≤ k + 1) (hkj : k ≤ j) :
    ‖chewi123TransitionProductFrom A (chewi125PowerStep gamma) k (j - k)‖ ≤
      Real.exp (-alpha *
        ∑ l ∈ Finset.Ico (k + 1) (j + 1), chewi125PowerStep gamma l) := by
  have hlocal :=
    chewi123TransitionProductFrom_norm_le_exp_neg_sum_of_stepMap_norm_le_one_sub_range
      A (chewi125PowerStep gamma) alpha k (j - k)
      (fun r hr => by
        have hkr : k + 1 ≤ k + r + 1 := by omega
        exact hsmall (k + r + 1) (Nat.le_trans hk hkr))
      (fun r hr => by
        have hkr : k + 1 ≤ k + r + 1 := by omega
        exact hstep (k + r + 1) (Nat.le_trans hk hkr))
  have hsum :
      (∑ r ∈ Finset.range (j - k),
          alpha * chewi125PowerStep gamma (k + r + 1)) =
        alpha * ∑ l ∈ Finset.Ico (k + 1) (j + 1),
          chewi125PowerStep gamma l := by
    rw [Finset.mul_sum]
    rw [Finset.sum_Ico_eq_sum_range]
    have hlen : j + 1 - (k + 1) = j - k := by omega
    rw [hlen]
    refine Finset.sum_congr rfl ?_
    intro r hr
    have hidx : k + r + 1 = k + 1 + r := by omega
    rw [hidx]
  simpa [hsum, neg_mul] using hlocal

/--
If a deterministic scalar majorant has order `N^γ` with `γ < 1`, then its
`1 / N`-scaled version vanishes.  This is the asymptotic handoff used after
Chewi's Lemma 12.5 estimates reduce the residual rows to `O(N^γ)`.
-/
theorem chewi125_scaled_power_bound_tendsto_zero
    (C gamma : ℝ) (hgamma_lt : gamma < 1) :
    Tendsto (fun N : ℕ => (N : ℝ)⁻¹ * (C * (N : ℝ) ^ gamma))
      atTop (𝓝 0) := by
  have hpow :
      Tendsto (fun x : ℝ => x ^ (gamma - 1)) atTop (𝓝 0) := by
    simpa [sub_eq_add_neg] using
      (tendsto_rpow_neg_atTop (show 0 < 1 - gamma by linarith))
  have hnat :
      Tendsto (fun N : ℕ => (N : ℝ) ^ (gamma - 1)) atTop (𝓝 0) :=
    hpow.comp tendsto_natCast_atTop_atTop
  have hC :
      Tendsto (fun N : ℕ => C * (N : ℝ) ^ (gamma - 1)) atTop (𝓝 (C * 0)) :=
    tendsto_const_nhds.mul hnat
  have hC0 :
      Tendsto (fun N : ℕ => C * (N : ℝ) ^ (gamma - 1)) atTop (𝓝 0) := by
    simpa using hC
  refine hC0.congr' ?_
  refine eventually_atTop.2 ⟨1, ?_⟩
  intro N hN
  have hNpos : 0 < (N : ℝ) := by exact_mod_cast hN
  have hNnonneg : 0 ≤ (N : ℝ) := le_of_lt hNpos
  symm
  calc
    (N : ℝ)⁻¹ * (C * (N : ℝ) ^ gamma)
        = C * ((N : ℝ) ^ gamma * (N : ℝ)⁻¹) := by ring
    _ = C * ((N : ℝ) ^ gamma * (N : ℝ) ^ (-1 : ℝ)) := by
          rw [Real.rpow_neg hNnonneg (1 : ℝ), Real.rpow_one]
    _ = C * (N : ℝ) ^ (gamma - 1) := by
          rw [← Real.rpow_add hNpos]
          ring_nf

/--
Squeeze a nonnegative scalar row between zero and an eventual `C * N^γ`
majorant with `γ < 1`.  This turns the integral-test output in Chewi's
heuristic Lemma 12.5 proof into the exact average-decay hypothesis needed by
the source-conditioned ASGD wrappers.
-/
theorem chewi125_average_tendsto_zero_of_power_bound
    (S : ℕ -> ℝ) {C gamma : ℝ}
    (hgamma_lt : gamma < 1)
    (hS_nonneg : ∀ᶠ N in atTop, 0 ≤ S N)
    (hS_bound : ∀ᶠ N in atTop, S N ≤ C * (N : ℝ) ^ gamma) :
    Tendsto (fun N : ℕ => (N : ℝ)⁻¹ * S N) atTop (𝓝 0) := by
  have hupper :
      Tendsto (fun N : ℕ => (N : ℝ)⁻¹ * (C * (N : ℝ) ^ gamma))
        atTop (𝓝 0) :=
    chewi125_scaled_power_bound_tendsto_zero C gamma hgamma_lt
  refine tendsto_of_tendsto_of_tendsto_of_le_of_le' tendsto_const_nhds hupper ?_ ?_
  · filter_upwards [hS_nonneg] with N hSN
    exact mul_nonneg (inv_nonneg.mpr (Nat.cast_nonneg N)) hSN
  · filter_upwards [hS_bound] with N hSN
    exact mul_le_mul_of_nonneg_left hSN (inv_nonneg.mpr (Nat.cast_nonneg N))

/--
Source-shaped Chewi Lemma 12.5 handoff for the terminal transition-product
row: once the exponential-tail sum is eventually `O(N^γ)`, `γ < 1`, its
average tends to zero.
-/
theorem chewi125_exp_tail_average_tendsto_zero_of_power_bound
    {alpha C gamma : ℝ}
    (hgamma_lt : gamma < 1)
    (hbound : ∀ᶠ (N : ℕ) in atTop,
      (∑ k ∈ Finset.Ico 1 N,
        Real.exp (-alpha *
          ∑ l ∈ Finset.Ico (k + 1) (N + 1),
            chewi125PowerStep gamma l)) ≤ C * (N : ℝ) ^ gamma) :
    Tendsto
      (fun N : ℕ =>
        (N : ℝ)⁻¹ *
          ∑ k ∈ Finset.Ico 1 N,
            Real.exp (-alpha *
              ∑ l ∈ Finset.Ico (k + 1) (N + 1),
                chewi125PowerStep gamma l))
      atTop (𝓝 0) := by
  refine chewi125_average_tendsto_zero_of_power_bound
    (fun N : ℕ =>
      ∑ k ∈ Finset.Ico 1 N,
        Real.exp (-alpha *
          ∑ l ∈ Finset.Ico (k + 1) (N + 1),
            chewi125PowerStep gamma l))
    hgamma_lt ?_ hbound
  exact Eventually.of_forall fun N =>
    Finset.sum_nonneg fun k _hk => le_of_lt (Real.exp_pos _)

/--
Source-shaped Chewi Lemma 12.5 handoff for the step-difference residual row:
once the displayed double sum is eventually `O(N^γ)`, `γ < 1`, its average
tends to zero.
-/
theorem chewi125_stepdiff_exp_double_average_tendsto_zero_of_power_bound
    {alpha C gamma : ℝ}
    (hgamma_lt : gamma < 1)
    (hbound : ∀ᶠ (N : ℕ) in atTop,
      (∑ k ∈ Finset.Ico 1 N,
        ∑ j ∈ Finset.Ico k N,
          ‖chewi125PowerStep gamma k - chewi125PowerStep gamma (j + 1)‖ *
            Real.exp (-alpha *
              ∑ l ∈ Finset.Ico (k + 1) (j + 1),
                chewi125PowerStep gamma l)) ≤ C * (N : ℝ) ^ gamma) :
    Tendsto
      (fun N : ℕ =>
        (N : ℝ)⁻¹ *
          ∑ k ∈ Finset.Ico 1 N,
            ∑ j ∈ Finset.Ico k N,
              ‖chewi125PowerStep gamma k - chewi125PowerStep gamma (j + 1)‖ *
                Real.exp (-alpha *
                  ∑ l ∈ Finset.Ico (k + 1) (j + 1),
                    chewi125PowerStep gamma l))
      atTop (𝓝 0) := by
  refine chewi125_average_tendsto_zero_of_power_bound
    (fun N : ℕ =>
      ∑ k ∈ Finset.Ico 1 N,
        ∑ j ∈ Finset.Ico k N,
          ‖chewi125PowerStep gamma k - chewi125PowerStep gamma (j + 1)‖ *
            Real.exp (-alpha *
              ∑ l ∈ Finset.Ico (k + 1) (j + 1),
                chewi125PowerStep gamma l))
    hgamma_lt ?_ hbound
  exact Eventually.of_forall fun N =>
    Finset.sum_nonneg fun k _hk =>
      Finset.sum_nonneg fun j _hj =>
        mul_nonneg (norm_nonneg _) (le_of_lt (Real.exp_pos _))

/-- Reflect the terminal index `N - k` in the Chewi Lemma 12.5 tail sum. -/
theorem chewi125_terminal_index_reflect_sum (N : ℕ) (f : ℕ -> ℝ) :
    (∑ k ∈ Finset.Ico 1 N, f (N - k)) =
      ∑ m ∈ Finset.Ico 1 N, f m := by
  simpa using
    (Finset.sum_Ico_reflect f 1 (m := N) (n := N) (Nat.le_succ N))

/--
Lower bound the Chewi power-step tail by the number of terms times the last
step size.  This is the discrete version of the source's
`τ(n) - τ(k)` lower estimate for the terminal transition-product row.
-/
theorem chewi125_power_tail_lower {gamma : ℝ} (hgamma_nonneg : 0 ≤ gamma)
    (N k : ℕ) :
    ((N - k : ℕ) : ℝ) * (N : ℝ) ^ (-gamma) ≤
      ∑ l ∈ Finset.Ico (k + 1) (N + 1), chewi125PowerStep gamma l := by
  have hconst :
      (∑ _l ∈ Finset.Ico (k + 1) (N + 1), (N : ℝ) ^ (-gamma)) =
        ((N - k : ℕ) : ℝ) * (N : ℝ) ^ (-gamma) := by
    rw [Finset.sum_const, Nat.card_Ico, nsmul_eq_mul]
    have hcard : N + 1 - (k + 1) = N - k := by omega
    rw [hcard]
  rw [← hconst]
  refine Finset.sum_le_sum ?_
  intro l hl
  have hlmem : k + 1 ≤ l ∧ l < N + 1 := by
    simpa [Finset.mem_Ico] using hl
  have hlpos : 0 < l := by omega
  have hlN : l ≤ N := by omega
  rw [chewi125PowerStep_of_pos gamma hlpos]
  exact Real.rpow_le_rpow_of_nonpos
    (Nat.cast_pos.mpr hlpos) (by exact_mod_cast hlN) (neg_nonpos.mpr hgamma_nonneg)

/--
Single-term terminal exponential-tail comparison for Chewi Lemma 12.5.  Each
source exponential tail is bounded by a geometric term with rate
`alpha * N^{-gamma}`.
-/
theorem chewi125_exp_tail_term_le_geometric {alpha gamma : ℝ}
    (halpha : 0 < alpha) (hgamma_nonneg : 0 ≤ gamma) (N k : ℕ) :
    Real.exp (-alpha *
        ∑ l ∈ Finset.Ico (k + 1) (N + 1), chewi125PowerStep gamma l) ≤
      Real.exp (-(alpha * (N : ℝ) ^ (-gamma)) * ((N - k : ℕ) : ℝ)) := by
  have htail := chewi125_power_tail_lower hgamma_nonneg N k
  have hmul :
      alpha * (((N - k : ℕ) : ℝ) * (N : ℝ) ^ (-gamma)) ≤
        alpha * ∑ l ∈ Finset.Ico (k + 1) (N + 1), chewi125PowerStep gamma l :=
    mul_le_mul_of_nonneg_left htail (le_of_lt halpha)
  apply Real.exp_monotone
  calc
    -alpha * (∑ l ∈ Finset.Ico (k + 1) (N + 1), chewi125PowerStep gamma l)
        = -(alpha * ∑ l ∈ Finset.Ico (k + 1) (N + 1),
              chewi125PowerStep gamma l) := by ring
    _ ≤ -(alpha * (((N - k : ℕ) : ℝ) * (N : ℝ) ^ (-gamma))) := neg_le_neg hmul
    _ = -(alpha * (N : ℝ) ^ (-gamma)) * ((N - k : ℕ) : ℝ) := by ring

/--
Terminal exponential-tail row bounded by a finite geometric/exponential sum.
This is the discrete counterpart of the source's terminal-row integral
majorization before simplifying the constant.
-/
theorem chewi125_exp_tail_sum_le_geometric {alpha gamma : ℝ}
    (halpha : 0 < alpha) (hgamma_nonneg : 0 ≤ gamma) (N : ℕ) :
    (∑ k ∈ Finset.Ico 1 N,
        Real.exp (-alpha *
          ∑ l ∈ Finset.Ico (k + 1) (N + 1), chewi125PowerStep gamma l)) ≤
      ∑ i ∈ Finset.Ico 0 N,
        Real.exp (-(alpha * (N : ℝ) ^ (-gamma)) * (i : ℝ)) := by
  calc
    (∑ k ∈ Finset.Ico 1 N,
        Real.exp (-alpha *
          ∑ l ∈ Finset.Ico (k + 1) (N + 1), chewi125PowerStep gamma l))
        ≤ ∑ k ∈ Finset.Ico 1 N,
            Real.exp (-(alpha * (N : ℝ) ^ (-gamma)) * ((N - k : ℕ) : ℝ)) := by
          exact Finset.sum_le_sum fun k _hk =>
            chewi125_exp_tail_term_le_geometric halpha hgamma_nonneg N k
    _ = ∑ i ∈ Finset.Ico 1 N,
            Real.exp (-(alpha * (N : ℝ) ^ (-gamma)) * (i : ℝ)) := by
          exact chewi125_terminal_index_reflect_sum N
            (fun i => Real.exp (-(alpha * (N : ℝ) ^ (-gamma)) * (i : ℝ)))
    _ ≤ ∑ i ∈ Finset.Ico 0 N,
            Real.exp (-(alpha * (N : ℝ) ^ (-gamma)) * (i : ℝ)) := by
          refine Finset.sum_le_sum_of_subset_of_nonneg ?_ ?_
          · exact Finset.Ico_subset_Ico (by omega) le_rfl
          · intro i _hi _hnot
            exact le_of_lt (Real.exp_pos _)

/--
Source-shaped terminal exponential-tail bound for Chewi Lemma 12.5.  Mathlib's
`sum_Ico_pow_mul_exp_neg_le` turns the reflected geometric row into the
explicit `exp(c) / c` bound with `c = alpha * N^{-gamma}`.
-/
theorem chewi125_exp_tail_sum_le_exp_div {alpha gamma : ℝ}
    (halpha : 0 < alpha) (hgamma_nonneg : 0 ≤ gamma) {N : ℕ}
    (hN : 1 ≤ N) :
    (∑ k ∈ Finset.Ico 1 N,
        Real.exp (-alpha *
          ∑ l ∈ Finset.Ico (k + 1) (N + 1), chewi125PowerStep gamma l)) ≤
      Real.exp (alpha * (N : ℝ) ^ (-gamma)) /
        (alpha * (N : ℝ) ^ (-gamma)) := by
  have hc : 0 < alpha * (N : ℝ) ^ (-gamma) := by
    exact mul_pos halpha (Real.rpow_pos_of_pos (by exact_mod_cast hN) (-gamma))
  have hgeom :=
    sum_Ico_pow_mul_exp_neg_le (k := 0) (M := N)
      (c := alpha * (N : ℝ) ^ (-gamma)) hc
  have hsum := chewi125_exp_tail_sum_le_geometric halpha hgamma_nonneg N
  refine hsum.trans ?_
  simpa [Nat.factorial, pow_one] using hgeom

/--
Terminal exponential-tail row bounded by the source-order quantity `N^γ`.
This is the formal finite-sum version of Chewi's
`I \lesssim n^γ` estimate for the second residual-row term.
-/
theorem chewi125_exp_tail_sum_le_power {alpha gamma : ℝ}
    (halpha : 0 < alpha) (hgamma_nonneg : 0 ≤ gamma) {N : ℕ}
    (hN : 1 ≤ N) :
    (∑ k ∈ Finset.Ico 1 N,
        Real.exp (-alpha *
          ∑ l ∈ Finset.Ico (k + 1) (N + 1), chewi125PowerStep gamma l)) ≤
      (Real.exp alpha / alpha) * (N : ℝ) ^ gamma := by
  let c : ℝ := alpha * (N : ℝ) ^ (-gamma)
  have hNpos : 0 < (N : ℝ) := Nat.cast_pos.mpr hN
  have hc_le_alpha : c ≤ alpha := by
    have hpow_le_one : (N : ℝ) ^ (-gamma) ≤ 1 :=
      Real.rpow_le_one_of_one_le_of_nonpos
        (Nat.one_le_cast.mpr hN) (by linarith)
    calc
      c = alpha * (N : ℝ) ^ (-gamma) := rfl
      _ ≤ alpha * 1 := mul_le_mul_of_nonneg_left hpow_le_one halpha.le
      _ = alpha := by ring
  have hconst :
      Real.exp c / c ≤ (Real.exp alpha / alpha) * (N : ℝ) ^ gamma := by
    have hexp : Real.exp c ≤ Real.exp alpha := Real.exp_le_exp_of_le hc_le_alpha
    have hc_nonneg : 0 ≤ c := by
      exact mul_nonneg halpha.le (Real.rpow_nonneg (le_of_lt hNpos) (-gamma))
    calc
      Real.exp c / c ≤ Real.exp alpha / c :=
        div_le_div_of_nonneg_right hexp hc_nonneg
      _ = (Real.exp alpha / alpha) * (N : ℝ) ^ gamma := by
        simp [c, Real.rpow_neg hNpos.le, div_eq_mul_inv,
          mul_assoc, mul_left_comm, mul_comm]
  exact (chewi125_exp_tail_sum_le_exp_div halpha hgamma_nonneg hN).trans hconst

/--
The terminal transition-product row in Chewi Lemma 12.5 has vanishing
`1 / N` average for `0 ≤ γ < 1`.  This closes the source's second residual
term after the V120 transition-product estimate.
-/
theorem chewi125_exp_tail_average_tendsto_zero
    {alpha gamma : ℝ}
    (halpha : 0 < alpha) (hgamma_nonneg : 0 ≤ gamma) (hgamma_lt : gamma < 1) :
    Tendsto
      (fun N : ℕ =>
        (N : ℝ)⁻¹ *
          ∑ k ∈ Finset.Ico 1 N,
            Real.exp (-alpha *
              ∑ l ∈ Finset.Ico (k + 1) (N + 1),
                chewi125PowerStep gamma l))
      atTop (𝓝 0) := by
  refine chewi125_exp_tail_average_tendsto_zero_of_power_bound
    (alpha := alpha) (C := Real.exp alpha / alpha) (gamma := gamma)
    hgamma_lt ?_
  refine eventually_atTop.2 ⟨1, ?_⟩
  intro N hN
  exact chewi125_exp_tail_sum_le_power halpha hgamma_nonneg hN

/-- Monotonicity of Chewi's power step size on positive indices. -/
theorem chewi125PowerStep_antitone_of_le {gamma : ℝ} (hgamma_nonneg : 0 ≤ gamma)
    {m n : ℕ} (hm : 0 < m) (hmn : m ≤ n) :
    chewi125PowerStep gamma n ≤ chewi125PowerStep gamma m := by
  have hn : 0 < n := Nat.lt_of_lt_of_le hm hmn
  rw [chewi125PowerStep_of_pos gamma hm, chewi125PowerStep_of_pos gamma hn]
  exact Real.rpow_le_rpow_of_nonpos
    (Nat.cast_pos.mpr hm) (by exact_mod_cast hmn) (neg_nonpos.mpr hgamma_nonneg)

/-- A first norm bound for the step-size difference in Chewi Lemma 12.5. -/
theorem chewi125PowerStep_norm_sub_le_left {gamma : ℝ} (hgamma_nonneg : 0 ≤ gamma)
    {m n : ℕ} (hm : 0 < m) (hmn : m ≤ n) :
    ‖chewi125PowerStep gamma m - chewi125PowerStep gamma n‖ ≤
      chewi125PowerStep gamma m := by
  have hle := chewi125PowerStep_antitone_of_le hgamma_nonneg hm hmn
  have hnnonneg : 0 ≤ chewi125PowerStep gamma n := by
    exact le_of_lt (chewi125PowerStep_pos gamma (Nat.lt_of_lt_of_le hm hmn))
  have hsub_nonneg :
      0 ≤ chewi125PowerStep gamma m - chewi125PowerStep gamma n :=
    sub_nonneg.mpr hle
  rw [Real.norm_eq_abs, abs_of_nonneg hsub_nonneg]
  exact sub_le_self _ hnnonneg

/--
Single-term step-difference exponential comparison for Chewi Lemma 12.5.  The
cumulative tail in the source display is replaced by an explicit geometric
kernel with rate `alpha * j^{-gamma}`.
-/
theorem chewi125_stepdiff_exp_term_le_geometric {alpha gamma : ℝ}
    (halpha : 0 < alpha) (hgamma_nonneg : 0 ≤ gamma) (k j : ℕ) :
    Real.exp (-alpha *
        ∑ l ∈ Finset.Ico (k + 1) (j + 1), chewi125PowerStep gamma l) ≤
      Real.exp (-(alpha * (j : ℝ) ^ (-gamma)) * ((j - k : ℕ) : ℝ)) := by
  have htail := chewi125_power_tail_lower hgamma_nonneg j k
  have hmul :
      alpha * (((j - k : ℕ) : ℝ) * (j : ℝ) ^ (-gamma)) ≤
        alpha * ∑ l ∈ Finset.Ico (k + 1) (j + 1), chewi125PowerStep gamma l :=
    mul_le_mul_of_nonneg_left htail (le_of_lt halpha)
  apply Real.exp_monotone
  calc
    -alpha * (∑ l ∈ Finset.Ico (k + 1) (j + 1), chewi125PowerStep gamma l)
        = -(alpha * ∑ l ∈ Finset.Ico (k + 1) (j + 1),
              chewi125PowerStep gamma l) := by ring
    _ ≤ -(alpha * (((j - k : ℕ) : ℝ) * (j : ℝ) ^ (-gamma))) := neg_le_neg hmul
    _ = -(alpha * (j : ℝ) ^ (-gamma)) * ((j - k : ℕ) : ℝ) := by ring

/--
Step-difference double row reduced to an explicit geometric kernel.  This is
the reusable finite-sum reduction for the remaining source lines 3944-3950.
-/
theorem chewi125_stepdiff_exp_double_sum_le_geometric {alpha gamma : ℝ}
    (halpha : 0 < alpha) (hgamma_nonneg : 0 ≤ gamma) (N : ℕ) :
    (∑ k ∈ Finset.Ico 1 N,
        ∑ j ∈ Finset.Ico k N,
          ‖chewi125PowerStep gamma k - chewi125PowerStep gamma (j + 1)‖ *
            Real.exp (-alpha *
              ∑ l ∈ Finset.Ico (k + 1) (j + 1),
                chewi125PowerStep gamma l)) ≤
      ∑ k ∈ Finset.Ico 1 N,
        ∑ j ∈ Finset.Ico k N,
          ‖chewi125PowerStep gamma k - chewi125PowerStep gamma (j + 1)‖ *
            Real.exp (-(alpha * (j : ℝ) ^ (-gamma)) * ((j - k : ℕ) : ℝ)) := by
  refine Finset.sum_le_sum ?_
  intro k _hk
  refine Finset.sum_le_sum ?_
  intro j _hj
  exact mul_le_mul_of_nonneg_left
    (chewi125_stepdiff_exp_term_le_geometric halpha hgamma_nonneg k j)
    (norm_nonneg _)

/--
Mean-value bound for the Chewi power-step difference.  On `[k, j + 1]`, the
derivative of `x ↦ x^{-γ}` is bounded by `γ * k^{-γ-1}`, so the displayed
step difference is controlled by that slope times the interval length.
-/
theorem chewi125PowerStep_norm_sub_le_deriv {gamma : ℝ}
    (hgamma_nonneg : 0 ≤ gamma) {k j : ℕ} (hk : 1 ≤ k) (hkj : k ≤ j + 1) :
    ‖chewi125PowerStep gamma k - chewi125PowerStep gamma (j + 1)‖ ≤
      (gamma * (k : ℝ) ^ (-gamma - 1)) *
        ‖((j + 1 : ℕ) : ℝ) - (k : ℝ)‖ := by
  have hkpos_nat : 0 < k := by omega
  have hjpos_nat : 0 < j + 1 := by omega
  rw [chewi125PowerStep_of_pos gamma hkpos_nat,
    chewi125PowerStep_of_pos gamma hjpos_nat]
  let f : ℝ → ℝ := fun x => x ^ (-gamma)
  have hkpos : 0 < (k : ℝ) := Nat.cast_pos.mpr hkpos_nat
  have hmvt :
      ‖f (((j + 1 : ℕ) : ℝ)) - f (k : ℝ)‖ ≤
        (gamma * (k : ℝ) ^ (-gamma - 1)) *
          ‖((j + 1 : ℕ) : ℝ) - (k : ℝ)‖ := by
    refine Convex.norm_image_sub_le_of_norm_deriv_le
      (𝕜 := ℝ)
      (f := f) (s := Set.Ici (k : ℝ))
      (C := gamma * (k : ℝ) ^ (-gamma - 1)) ?hdiff ?hbound
      (convex_Ici (k : ℝ)) ?hx ?hy
    · intro x hx
      exact Real.differentiableAt_rpow_const_of_ne (-gamma)
        (ne_of_gt (lt_of_lt_of_le hkpos hx))
    · intro x hx
      have hxpos : 0 < x := lt_of_lt_of_le hkpos hx
      have hxpow_nonneg : 0 ≤ x ^ (-gamma - 1) :=
        Real.rpow_nonneg (le_of_lt hxpos) (-gamma - 1)
      have hpow_le : x ^ (-gamma - 1) ≤ (k : ℝ) ^ (-gamma - 1) :=
        Real.rpow_le_rpow_of_nonpos hkpos hx (by linarith)
      have hderiv : deriv f x = (-gamma) * x ^ ((-gamma) - 1) := by
        dsimp [f]
        rw [Real.deriv_rpow_const]
      calc
        ‖deriv f x‖ = ‖(-gamma) * x ^ ((-gamma) - 1)‖ := by
          rw [hderiv]
        _ = gamma * x ^ (-gamma - 1) := by
          have hnorm_gamma : ‖(-gamma)‖ = gamma := by
            simp [Real.norm_eq_abs, abs_of_nonneg hgamma_nonneg]
          have hnorm_pow : ‖x ^ ((-gamma) - 1)‖ = x ^ (-gamma - 1) := by
            rw [show (-gamma) - 1 = -gamma - 1 by ring]
            exact Real.norm_of_nonneg hxpow_nonneg
          rw [norm_mul, hnorm_gamma, hnorm_pow]
        _ ≤ gamma * (k : ℝ) ^ (-gamma - 1) :=
          mul_le_mul_of_nonneg_left hpow_le hgamma_nonneg
    · simp [Set.mem_Ici]
    · simpa [Set.mem_Ici] using
        (show (k : ℝ) ≤ (((j + 1 : ℕ) : ℝ)) from by exact_mod_cast hkj)
  simpa [f, norm_sub_rev] using hmvt

/--
The remaining step-difference double row reduced to a derivative majorant
times the explicit geometric kernel from V124.  This is the direct formal
counterpart of the Taylor-expansion line in Chewi's heuristic proof.
-/
theorem chewi125_stepdiff_double_sum_le_deriv_geometric {alpha gamma : ℝ}
    (halpha : 0 < alpha) (hgamma_nonneg : 0 ≤ gamma) (N : ℕ) :
    (∑ k ∈ Finset.Ico 1 N,
        ∑ j ∈ Finset.Ico k N,
          ‖chewi125PowerStep gamma k - chewi125PowerStep gamma (j + 1)‖ *
            Real.exp (-alpha *
              ∑ l ∈ Finset.Ico (k + 1) (j + 1),
                chewi125PowerStep gamma l)) ≤
      ∑ k ∈ Finset.Ico 1 N,
        ∑ j ∈ Finset.Ico k N,
          ((gamma * (k : ℝ) ^ (-gamma - 1)) *
              ‖((j + 1 : ℕ) : ℝ) - (k : ℝ)‖) *
            Real.exp (-(alpha * (j : ℝ) ^ (-gamma)) * ((j - k : ℕ) : ℝ)) := by
  refine (chewi125_stepdiff_exp_double_sum_le_geometric halpha hgamma_nonneg N).trans ?_
  refine Finset.sum_le_sum ?_
  intro k hk
  refine Finset.sum_le_sum ?_
  intro j hj
  have hk_mem : 1 ≤ k ∧ k < N := by
    simpa [Finset.mem_Ico] using hk
  have hj_mem : k ≤ j ∧ j < N := by
    simpa [Finset.mem_Ico] using hj
  have hdiff :=
    chewi125PowerStep_norm_sub_le_deriv hgamma_nonneg
      (k := k) (j := j) hk_mem.1 (by omega)
  exact mul_le_mul_of_nonneg_right hdiff (le_of_lt (Real.exp_pos _))

/--
Weighted finite exponential row used by the remaining Chewi Lemma 12.5
step-difference summation.  It is just Mathlib's
`sum_Ico_pow_mul_exp_neg_le` at powers `1` and `0`, combined into the
source-shaped `(d + 1) exp(-c d)` row.
-/
theorem chewi125_sum_Ico_succ_mul_exp_neg_le {M : ℕ} {c : ℝ} (hc : 0 < c) :
    (∑ d ∈ Finset.Ico 0 M,
      (((d : ℕ) : ℝ) + 1) * Real.exp (-(c * ((d : ℕ) : ℝ)))) ≤
      Real.exp c / c ^ 2 + Real.exp c / c := by
  have h1 :=
    sum_Ico_pow_mul_exp_neg_le (k := 1) (M := M) (c := c) hc
  have h0 :=
    sum_Ico_pow_mul_exp_neg_le (k := 0) (M := M) (c := c) hc
  calc
    (∑ d ∈ Finset.Ico 0 M,
      (((d : ℕ) : ℝ) + 1) * Real.exp (-(c * ((d : ℕ) : ℝ))))
        = (∑ d ∈ Finset.Ico 0 M,
            ((d : ℝ) ^ 1 * Real.exp (-(c * (d : ℝ))) +
              (d : ℝ) ^ 0 * Real.exp (-(c * (d : ℝ))))) := by
          refine Finset.sum_congr rfl ?_
          intro d _hd
          ring
    _ = (∑ d ∈ Finset.Ico 0 M,
            (d : ℝ) ^ 1 * Real.exp (-(c * (d : ℝ)))) +
          (∑ d ∈ Finset.Ico 0 M,
            (d : ℝ) ^ 0 * Real.exp (-(c * (d : ℝ)))) := by
          rw [Finset.sum_add_distrib]
    _ ≤ Real.exp c * (1 : ℕ).factorial / c ^ (1 + 1) +
          Real.exp c * (0 : ℕ).factorial / c ^ (0 + 1) := by
          exact add_le_add h1 h0
    _ = Real.exp c / c ^ 2 + Real.exp c / c := by
          norm_num

/--
Power-step specialization of `chewi125_sum_Ico_succ_mul_exp_neg_le`.  For
`c = α j^{-γ}`, the `(d + 1)` exponential row is `O(j^{2γ})` with an explicit
constant.  This is the near-diagonal row estimate needed for Chewi's
step-difference double-sum bound.
-/
theorem chewi125_sum_Ico_succ_mul_exp_neg_power_le {alpha gamma : ℝ}
    (halpha : 0 < alpha) (hgamma_nonneg : 0 ≤ gamma)
    {j M : ℕ} (hj : 1 ≤ j) :
    (∑ d ∈ Finset.Ico 0 M,
      (((d : ℕ) : ℝ) + 1) *
        Real.exp (-((alpha * (j : ℝ) ^ (-gamma)) * ((d : ℕ) : ℝ)))) ≤
      (Real.exp alpha / alpha ^ 2 + Real.exp alpha / alpha) *
        (j : ℝ) ^ (2 * gamma) := by
  let c : ℝ := alpha * (j : ℝ) ^ (-gamma)
  have hjpos : 0 < (j : ℝ) := Nat.cast_pos.mpr (by omega)
  have hjone : 1 ≤ (j : ℝ) := by exact_mod_cast hj
  have hc : 0 < c := by
    exact mul_pos halpha (Real.rpow_pos_of_pos hjpos (-gamma))
  have hc_le_alpha : c ≤ alpha := by
    have hpow_le_one : (j : ℝ) ^ (-gamma) ≤ 1 :=
      Real.rpow_le_one_of_one_le_of_nonpos hjone (by linarith)
    calc
      c = alpha * (j : ℝ) ^ (-gamma) := rfl
      _ ≤ alpha * 1 := mul_le_mul_of_nonneg_left hpow_le_one halpha.le
      _ = alpha := by ring
  have hrow := chewi125_sum_Ico_succ_mul_exp_neg_le (M := M) (c := c) hc
  have hterm1 :
      Real.exp c / c ^ 2 ≤
        (Real.exp alpha / alpha ^ 2) * (j : ℝ) ^ (2 * gamma) := by
    have hexp : Real.exp c ≤ Real.exp alpha := Real.exp_le_exp_of_le hc_le_alpha
    have hc2_nonneg : 0 ≤ c ^ 2 := sq_nonneg c
    calc
      Real.exp c / c ^ 2 ≤ Real.exp alpha / c ^ 2 :=
        div_le_div_of_nonneg_right hexp hc2_nonneg
      _ = (Real.exp alpha / alpha ^ 2) * (j : ℝ) ^ (2 * gamma) := by
        simp [c, div_eq_mul_inv, pow_two, Real.rpow_neg (le_of_lt hjpos) gamma]
        rw [show 2 * gamma = gamma * (2 : ℕ) by norm_num [mul_comm]]
        rw [Real.rpow_mul_natCast (le_of_lt hjpos) gamma 2]
        ring
  have hterm0 :
      Real.exp c / c ≤
        (Real.exp alpha / alpha) * (j : ℝ) ^ (2 * gamma) := by
    have hexp : Real.exp c ≤ Real.exp alpha := Real.exp_le_exp_of_le hc_le_alpha
    have hc_nonneg : 0 ≤ c := hc.le
    have hpow_gamma_le :
        (j : ℝ) ^ gamma ≤ (j : ℝ) ^ (2 * gamma) :=
      Real.rpow_le_rpow_of_exponent_le hjone (by linarith)
    calc
      Real.exp c / c ≤ Real.exp alpha / c :=
        div_le_div_of_nonneg_right hexp hc_nonneg
      _ = (Real.exp alpha / alpha) * (j : ℝ) ^ gamma := by
        simp [c, div_eq_mul_inv, Real.rpow_neg (le_of_lt hjpos) gamma]
        ring
      _ ≤ (Real.exp alpha / alpha) * (j : ℝ) ^ (2 * gamma) := by
        exact mul_le_mul_of_nonneg_left hpow_gamma_le
          (div_nonneg (le_of_lt (Real.exp_pos alpha)) halpha.le)
  refine hrow.trans ?_
  calc
    Real.exp c / c ^ 2 + Real.exp c / c
        ≤ (Real.exp alpha / alpha ^ 2) * (j : ℝ) ^ (2 * gamma) +
          (Real.exp alpha / alpha) * (j : ℝ) ^ (2 * gamma) :=
        add_le_add hterm1 hterm0
    _ = (Real.exp alpha / alpha ^ 2 + Real.exp alpha / alpha) *
          (j : ℝ) ^ (2 * gamma) := by
        ring

/--
Near-diagonal row bound after replacing the varying rate by the `2k` rate.
This packages the V126 weighted exponential row with the source derivative
factor `γ k^{-γ-1}`.
-/
theorem chewi125_near_stepdiff_row_le_power {alpha gamma : ℝ}
    (halpha : 0 < alpha) (hgamma_nonneg : 0 ≤ gamma)
    {k M : ℕ} (hk : 1 ≤ k) :
    (∑ d ∈ Finset.Ico 0 M,
      ((gamma * (k : ℝ) ^ (-gamma - 1)) * (((d : ℕ) : ℝ) + 1)) *
        Real.exp (-((alpha * (((2 * k : ℕ) : ℝ) ^ (-gamma))) * ((d : ℕ) : ℝ)))) ≤
      (gamma * (k : ℝ) ^ (-gamma - 1)) *
        ((Real.exp alpha / alpha ^ 2 + Real.exp alpha / alpha) *
          (((2 * k : ℕ) : ℝ) ^ (2 * gamma))) := by
  have hrow :=
    chewi125_sum_Ico_succ_mul_exp_neg_power_le
      (alpha := alpha) (gamma := gamma) halpha hgamma_nonneg
      (j := 2 * k) (M := M) (by omega)
  have hconst_nonneg : 0 ≤ gamma * (k : ℝ) ^ (-gamma - 1) :=
    mul_nonneg hgamma_nonneg (Real.rpow_nonneg (Nat.cast_nonneg k) (-gamma - 1))
  calc
    (∑ d ∈ Finset.Ico 0 M,
      ((gamma * (k : ℝ) ^ (-gamma - 1)) * (((d : ℕ) : ℝ) + 1)) *
        Real.exp (-((alpha * (((2 * k : ℕ) : ℝ) ^ (-gamma))) * ((d : ℕ) : ℝ))))
        =
      (gamma * (k : ℝ) ^ (-gamma - 1)) *
        ∑ d ∈ Finset.Ico 0 M,
          (((d : ℕ) : ℝ) + 1) *
            Real.exp (-((alpha * (((2 * k : ℕ) : ℝ) ^ (-gamma))) *
              ((d : ℕ) : ℝ))) := by
          rw [Finset.mul_sum]
          refine Finset.sum_congr rfl ?_
          intro d _hd
          ring
    _ ≤
      (gamma * (k : ℝ) ^ (-gamma - 1)) *
        ((Real.exp alpha / alpha ^ 2 + Real.exp alpha / alpha) *
          (((2 * k : ℕ) : ℝ) ^ (2 * gamma))) :=
        mul_le_mul_of_nonneg_left hrow hconst_nonneg

/--
Simplified near-diagonal row bound: the preceding row has order
`k^(γ-1)`.  This is the exact outer summand needed for the V126 integral-test
bound.
-/
theorem chewi125_near_stepdiff_row_le_outer_power {alpha gamma : ℝ}
    (halpha : 0 < alpha) (hgamma_nonneg : 0 ≤ gamma)
    {k M : ℕ} (hk : 1 ≤ k) :
    (∑ d ∈ Finset.Ico 0 M,
      ((gamma * (k : ℝ) ^ (-gamma - 1)) * (((d : ℕ) : ℝ) + 1)) *
        Real.exp (-((alpha * (((2 * k : ℕ) : ℝ) ^ (-gamma))) * ((d : ℕ) : ℝ)))) ≤
      (gamma * (Real.exp alpha / alpha ^ 2 + Real.exp alpha / alpha) *
          (2 : ℝ) ^ (2 * gamma)) *
        (k : ℝ) ^ (gamma - 1) := by
  have hbase :=
    chewi125_near_stepdiff_row_le_power (alpha := alpha) (gamma := gamma)
      halpha hgamma_nonneg (k := k) (M := M) hk
  refine hbase.trans_eq ?_
  have hkpos : 0 < (k : ℝ) := Nat.cast_pos.mpr (by omega)
  have htwopos : 0 < (2 : ℝ) := by norm_num
  calc
    (gamma * (k : ℝ) ^ (-gamma - 1)) *
        ((Real.exp alpha / alpha ^ 2 + Real.exp alpha / alpha) *
          (((2 * k : ℕ) : ℝ) ^ (2 * gamma)))
        =
      (gamma * (k : ℝ) ^ (-gamma - 1)) *
        ((Real.exp alpha / alpha ^ 2 + Real.exp alpha / alpha) *
          ((2 : ℝ) * (k : ℝ)) ^ (2 * gamma)) := by
          norm_num
    _ =
      (gamma * (k : ℝ) ^ (-gamma - 1)) *
        ((Real.exp alpha / alpha ^ 2 + Real.exp alpha / alpha) *
          ((2 : ℝ) ^ (2 * gamma) * (k : ℝ) ^ (2 * gamma))) := by
          rw [Real.mul_rpow (le_of_lt htwopos) (le_of_lt hkpos)]
    _ =
      (gamma * (Real.exp alpha / alpha ^ 2 + Real.exp alpha / alpha) *
          (2 : ℝ) ^ (2 * gamma)) *
        ((k : ℝ) ^ (-gamma - 1) * (k : ℝ) ^ (2 * gamma)) := by
          ring
    _ =
      (gamma * (Real.exp alpha / alpha ^ 2 + Real.exp alpha / alpha) *
          (2 : ℝ) ^ (2 * gamma)) *
        (k : ℝ) ^ (gamma - 1) := by
          rw [← Real.rpow_add hkpos]
          ring_nf

/--
On the near diagonal `d ≤ k`, the true kernel with rate `(k+d)^{-γ}` is
bounded by the coarser `2k` kernel.  This is the source inequality
`k+d ≤ 2k` translated through the negative power and exponential.
-/
theorem chewi125_near_stepdiff_term_le_twokernel {alpha gamma : ℝ}
    (halpha : 0 < alpha) (hgamma_nonneg : 0 ≤ gamma)
    {k d : ℕ} (hk : 1 ≤ k) (hd : d ≤ k) :
    ((gamma * (k : ℝ) ^ (-gamma - 1)) * (((d : ℕ) : ℝ) + 1)) *
        Real.exp (-((alpha * (((k + d : ℕ) : ℝ) ^ (-gamma))) * ((d : ℕ) : ℝ))) ≤
      ((gamma * (k : ℝ) ^ (-gamma - 1)) * (((d : ℕ) : ℝ) + 1)) *
        Real.exp (-((alpha * (((2 * k : ℕ) : ℝ) ^ (-gamma))) * ((d : ℕ) : ℝ))) := by
  have hkdpos_nat : 0 < k + d := by omega
  have hkdpos : 0 < (((k + d : ℕ) : ℝ)) := Nat.cast_pos.mpr hkdpos_nat
  have hkd_le_twok : (((k + d : ℕ) : ℝ)) ≤ (((2 * k : ℕ) : ℝ)) := by
    exact_mod_cast (show k + d ≤ 2 * k by omega)
  have hpow :
      (((2 * k : ℕ) : ℝ) ^ (-gamma)) ≤
        (((k + d : ℕ) : ℝ) ^ (-gamma)) :=
    Real.rpow_le_rpow_of_nonpos hkdpos hkd_le_twok (neg_nonpos.mpr hgamma_nonneg)
  have hrate :
      (alpha * (((2 * k : ℕ) : ℝ) ^ (-gamma))) * ((d : ℕ) : ℝ) ≤
        (alpha * (((k + d : ℕ) : ℝ) ^ (-gamma))) * ((d : ℕ) : ℝ) := by
    exact mul_le_mul_of_nonneg_right
      (mul_le_mul_of_nonneg_left hpow halpha.le)
      (Nat.cast_nonneg d)
  have hexp :
      Real.exp (-((alpha * (((k + d : ℕ) : ℝ) ^ (-gamma))) * ((d : ℕ) : ℝ))) ≤
        Real.exp (-((alpha * (((2 * k : ℕ) : ℝ) ^ (-gamma))) * ((d : ℕ) : ℝ))) :=
    Real.exp_le_exp.mpr (neg_le_neg hrate)
  have hcoef_nonneg :
      0 ≤ (gamma * (k : ℝ) ^ (-gamma - 1)) * (((d : ℕ) : ℝ) + 1) := by
    exact mul_nonneg
      (mul_nonneg hgamma_nonneg (Real.rpow_nonneg (Nat.cast_nonneg k) (-gamma - 1)))
      (by positivity)
  exact mul_le_mul_of_nonneg_left hexp hcoef_nonneg

/--
Near-diagonal source row after reindexing `j = k + d`.  The true kernel is
first bounded by the `2k` kernel and then summed by
`chewi125_near_stepdiff_row_le_outer_power`.
-/
theorem chewi125_near_stepdiff_row_true_le_outer_power {alpha gamma : ℝ}
    (halpha : 0 < alpha) (hgamma_nonneg : 0 ≤ gamma)
    {k : ℕ} (hk : 1 ≤ k) :
    (∑ d ∈ Finset.Ico 0 (k + 1),
      ((gamma * (k : ℝ) ^ (-gamma - 1)) * (((d : ℕ) : ℝ) + 1)) *
        Real.exp (-((alpha * (((k + d : ℕ) : ℝ) ^ (-gamma))) * ((d : ℕ) : ℝ)))) ≤
      (gamma * (Real.exp alpha / alpha ^ 2 + Real.exp alpha / alpha) *
          (2 : ℝ) ^ (2 * gamma)) *
        (k : ℝ) ^ (gamma - 1) := by
  calc
    (∑ d ∈ Finset.Ico 0 (k + 1),
      ((gamma * (k : ℝ) ^ (-gamma - 1)) * (((d : ℕ) : ℝ) + 1)) *
        Real.exp (-((alpha * (((k + d : ℕ) : ℝ) ^ (-gamma))) * ((d : ℕ) : ℝ))))
        ≤
      ∑ d ∈ Finset.Ico 0 (k + 1),
        ((gamma * (k : ℝ) ^ (-gamma - 1)) * (((d : ℕ) : ℝ) + 1)) *
          Real.exp (-((alpha * (((2 * k : ℕ) : ℝ) ^ (-gamma))) * ((d : ℕ) : ℝ))) := by
          refine Finset.sum_le_sum ?_
          intro d hdmem
          have hd : d ≤ k := by
            have hmem : 0 ≤ d ∧ d < k + 1 := by
              simpa [Finset.mem_Ico] using hdmem
            omega
          exact chewi125_near_stepdiff_term_le_twokernel
            (alpha := alpha) (gamma := gamma) halpha hgamma_nonneg
            (k := k) (d := d) hk hd
    _ ≤
      (gamma * (Real.exp alpha / alpha ^ 2 + Real.exp alpha / alpha) *
          (2 : ℝ) ^ (2 * gamma)) *
        (k : ℝ) ^ (gamma - 1) :=
        chewi125_near_stepdiff_row_le_outer_power
          (alpha := alpha) (gamma := gamma) halpha hgamma_nonneg
          (k := k) (M := k + 1) hk

/--
Integral-test bound for the outer near-diagonal power row.  Since
`γ - 1 ∈ (-1, 0)`, the source sum is controlled by a one-sided integral and
has order `N^γ`.
-/
theorem chewi125_sum_Ico_rpow_gamma_sub_one_le
    {gamma : ℝ} (hgamma_pos : 0 < gamma) (hgamma_lt : gamma < 1)
    {N : ℕ} (hN : 1 ≤ N) :
    (∑ k ∈ Finset.Ico 1 N, (k : ℝ) ^ (gamma - 1)) ≤
      (1 + gamma⁻¹) * (N : ℝ) ^ gamma := by
  by_cases hN2 : 2 ≤ N
  · let f : ℝ → ℝ := fun x => x ^ (gamma - 1)
    have hanti : AntitoneOn f (Set.Icc (((1 : ℕ) : ℝ)) ((N : ℕ) : ℝ)) := by
      intro x hx y _hy hxy
      have hxone : (1 : ℝ) ≤ x := by simpa using hx.1
      have hxpos : 0 < x := lt_of_lt_of_le zero_lt_one hxone
      exact Real.rpow_le_rpow_of_nonpos hxpos hxy (by linarith)
    have htail_raw :=
      AntitoneOn.sum_le_integral_Ico (a := 1) (b := N) hN hanti
    have hshift :
        (∑ i ∈ Finset.Ico 1 N, f (((i + 1 : ℕ) : ℝ))) =
          ∑ k ∈ Finset.Ico 2 (N + 1), f (k : ℝ) := by
      have h :=
        Finset.sum_Ico_add
          (f := fun k : ℕ => f (k : ℝ)) (a := 1) (b := N) (c := 1)
      simpa [Nat.cast_add, Nat.add_comm, add_comm, add_left_comm, add_assoc] using h
    have htail :
        (∑ k ∈ Finset.Ico 2 (N + 1), (k : ℝ) ^ (gamma - 1)) ≤
          ∫ x in (1 : ℝ)..(N : ℝ), x ^ (gamma - 1) := by
      rw [hshift] at htail_raw
      simpa [f] using htail_raw
    have htail_subset :
        (∑ k ∈ Finset.Ico 2 N, (k : ℝ) ^ (gamma - 1)) ≤
          ∑ k ∈ Finset.Ico 2 (N + 1), (k : ℝ) ^ (gamma - 1) := by
      refine Finset.sum_le_sum_of_subset_of_nonneg ?_ ?_
      · exact Finset.Ico_subset_Ico le_rfl (by omega)
      · intro k _hk _hnot
        exact Real.rpow_nonneg (Nat.cast_nonneg k) (gamma - 1)
    have hsplit :
        (∑ k ∈ Finset.Ico 1 N, (k : ℝ) ^ (gamma - 1)) =
          1 + ∑ k ∈ Finset.Ico 2 N, (k : ℝ) ^ (gamma - 1) := by
      have hset : Finset.Ico 1 N = insert 1 (Finset.Ico 2 N) := by
        ext k
        simp [Finset.mem_Ico]
        omega
      rw [hset, Finset.sum_insert]
      · simp
      · simp [Finset.mem_Ico]
    have hint :
        ∫ x in (1 : ℝ)..(N : ℝ), x ^ (gamma - 1) =
          ((N : ℝ) ^ gamma - 1) / gamma := by
      have h :=
        integral_rpow (a := (1 : ℝ)) (b := (N : ℝ)) (r := gamma - 1)
          (Or.inl (by linarith))
      simpa using h
    have hNpow_one : 1 ≤ (N : ℝ) ^ gamma :=
      Real.one_le_rpow (Nat.one_le_cast.mpr hN) hgamma_pos.le
    have hint_bound :
        ((N : ℝ) ^ gamma - 1) / gamma ≤ gamma⁻¹ * (N : ℝ) ^ gamma := by
      have hnum : (N : ℝ) ^ gamma - 1 ≤ (N : ℝ) ^ gamma := by linarith
      have hdiv := div_le_div_of_nonneg_right hnum hgamma_pos.le
      simpa [div_eq_mul_inv, mul_comm, mul_left_comm, mul_assoc] using hdiv
    calc
      (∑ k ∈ Finset.Ico 1 N, (k : ℝ) ^ (gamma - 1))
          = 1 + ∑ k ∈ Finset.Ico 2 N, (k : ℝ) ^ (gamma - 1) := hsplit
      _ ≤ 1 + ∫ x in (1 : ℝ)..(N : ℝ), x ^ (gamma - 1) :=
          by simpa [add_comm] using
            (add_le_add_left (htail_subset.trans htail) 1)
      _ = 1 + ((N : ℝ) ^ gamma - 1) / gamma := by rw [hint]
      _ ≤ (N : ℝ) ^ gamma + gamma⁻¹ * (N : ℝ) ^ gamma :=
          add_le_add hNpow_one hint_bound
      _ = (1 + gamma⁻¹) * (N : ℝ) ^ gamma := by ring
  · have hN_eq : N = 1 := by omega
    simp [hN_eq]
    exact add_nonneg zero_le_one (inv_nonneg.mpr hgamma_pos.le)

/--
Near-diagonal step-difference rows summed over `k`.  This proves the
`O(N^γ)` half of the remaining Chewi Lemma 12.5 double-sum estimate after the
reindexing `j = k + d`, `d ≤ k`.
-/
theorem chewi125_near_stepdiff_rows_true_le_power {alpha gamma : ℝ}
    (halpha : 0 < alpha) (hgamma_pos : 0 < gamma) (hgamma_lt : gamma < 1)
    {N : ℕ} (hN : 1 ≤ N) :
    (∑ k ∈ Finset.Ico 1 N,
      ∑ d ∈ Finset.Ico 0 (k + 1),
        ((gamma * (k : ℝ) ^ (-gamma - 1)) * (((d : ℕ) : ℝ) + 1)) *
          Real.exp (-((alpha * (((k + d : ℕ) : ℝ) ^ (-gamma))) * ((d : ℕ) : ℝ)))) ≤
      (gamma * (Real.exp alpha / alpha ^ 2 + Real.exp alpha / alpha) *
          (2 : ℝ) ^ (2 * gamma)) *
        ((1 + gamma⁻¹) * (N : ℝ) ^ gamma) := by
  let Cnear : ℝ :=
    gamma * (Real.exp alpha / alpha ^ 2 + Real.exp alpha / alpha) *
      (2 : ℝ) ^ (2 * gamma)
  have hrow :
      (∑ k ∈ Finset.Ico 1 N,
        ∑ d ∈ Finset.Ico 0 (k + 1),
          ((gamma * (k : ℝ) ^ (-gamma - 1)) * (((d : ℕ) : ℝ) + 1)) *
            Real.exp (-((alpha * (((k + d : ℕ) : ℝ) ^ (-gamma))) * ((d : ℕ) : ℝ)))) ≤
        ∑ k ∈ Finset.Ico 1 N, Cnear * (k : ℝ) ^ (gamma - 1) := by
    refine Finset.sum_le_sum ?_
    intro k hk
    have hk_mem : 1 ≤ k ∧ k < N := by
      simpa [Finset.mem_Ico] using hk
    simpa [Cnear] using
      chewi125_near_stepdiff_row_true_le_outer_power
        (alpha := alpha) (gamma := gamma) halpha hgamma_pos.le
        (k := k) hk_mem.1
  have houter :=
    chewi125_sum_Ico_rpow_gamma_sub_one_le
      (gamma := gamma) hgamma_pos hgamma_lt hN
  have hCnear_nonneg : 0 ≤ Cnear := by
    refine mul_nonneg ?_ (Real.rpow_nonneg (by norm_num : (0 : ℝ) ≤ 2) (2 * gamma))
    refine mul_nonneg hgamma_pos.le ?_
    exact add_nonneg
      (div_nonneg (le_of_lt (Real.exp_pos alpha)) (sq_nonneg alpha))
      (div_nonneg (le_of_lt (Real.exp_pos alpha)) halpha.le)
  calc
    (∑ k ∈ Finset.Ico 1 N,
      ∑ d ∈ Finset.Ico 0 (k + 1),
        ((gamma * (k : ℝ) ^ (-gamma - 1)) * (((d : ℕ) : ℝ) + 1)) *
          Real.exp (-((alpha * (((k + d : ℕ) : ℝ) ^ (-gamma))) * ((d : ℕ) : ℝ))))
        ≤ ∑ k ∈ Finset.Ico 1 N, Cnear * (k : ℝ) ^ (gamma - 1) := hrow
    _ = Cnear * ∑ k ∈ Finset.Ico 1 N, (k : ℝ) ^ (gamma - 1) := by
      rw [Finset.mul_sum]
    _ ≤ Cnear * ((1 + gamma⁻¹) * (N : ℝ) ^ gamma) :=
      mul_le_mul_of_nonneg_left houter hCnear_nonneg
    _ =
      (gamma * (Real.exp alpha / alpha ^ 2 + Real.exp alpha / alpha) *
          (2 : ℝ) ^ (2 * gamma)) *
        ((1 + gamma⁻¹) * (N : ℝ) ^ gamma) := by
      simp [Cnear]

/--
On the far diagonal `k < d`, the true kernel with rate `(k+d)^{-γ}` is
bounded by the coarser `2d` kernel.  This is the far-tail analogue of
`chewi125_near_stepdiff_term_le_twokernel`, preparing the
stretched-exponential row estimate in the remaining Chewi Lemma 12.5 proof.
-/
theorem chewi125_far_stepdiff_term_le_twodkernel {alpha gamma : ℝ}
    (halpha : 0 < alpha) (hgamma_nonneg : 0 ≤ gamma)
    {k d : ℕ} (hk : 1 ≤ k) (hkd : k < d) :
    ((gamma * (k : ℝ) ^ (-gamma - 1)) * (((d : ℕ) : ℝ) + 1)) *
        Real.exp (-((alpha * (((k + d : ℕ) : ℝ) ^ (-gamma))) * ((d : ℕ) : ℝ))) ≤
      ((gamma * (k : ℝ) ^ (-gamma - 1)) * (((d : ℕ) : ℝ) + 1)) *
        Real.exp (-((alpha * (((2 * d : ℕ) : ℝ) ^ (-gamma))) * ((d : ℕ) : ℝ))) := by
  have hkdpos_nat : 0 < k + d := by omega
  have hkdpos : 0 < (((k + d : ℕ) : ℝ)) := Nat.cast_pos.mpr hkdpos_nat
  have hkd_le_twod : (((k + d : ℕ) : ℝ)) ≤ (((2 * d : ℕ) : ℝ)) := by
    exact_mod_cast (show k + d ≤ 2 * d by omega)
  have hpow :
      (((2 * d : ℕ) : ℝ) ^ (-gamma)) ≤
        (((k + d : ℕ) : ℝ) ^ (-gamma)) :=
    Real.rpow_le_rpow_of_nonpos hkdpos hkd_le_twod (neg_nonpos.mpr hgamma_nonneg)
  have hrate :
      (alpha * (((2 * d : ℕ) : ℝ) ^ (-gamma))) * ((d : ℕ) : ℝ) ≤
        (alpha * (((k + d : ℕ) : ℝ) ^ (-gamma))) * ((d : ℕ) : ℝ) := by
    exact mul_le_mul_of_nonneg_right
      (mul_le_mul_of_nonneg_left hpow halpha.le)
      (Nat.cast_nonneg d)
  have hexp :
      Real.exp (-((alpha * (((k + d : ℕ) : ℝ) ^ (-gamma))) * ((d : ℕ) : ℝ))) ≤
        Real.exp (-((alpha * (((2 * d : ℕ) : ℝ) ^ (-gamma))) * ((d : ℕ) : ℝ))) :=
    Real.exp_le_exp.mpr (neg_le_neg hrate)
  have hcoef_nonneg :
      0 ≤ (gamma * (k : ℝ) ^ (-gamma - 1)) * (((d : ℕ) : ℝ) + 1) := by
    exact mul_nonneg
      (mul_nonneg hgamma_nonneg (Real.rpow_nonneg (Nat.cast_nonneg k) (-gamma - 1)))
      (by positivity)
  exact mul_le_mul_of_nonneg_left hexp hcoef_nonneg

/--
Far-diagonal source row after reindexing `j = k + d`.  The true kernel is
bounded termwise by the `2d` kernel on `d ∈ Ico (k+1) M`; the remaining task is
to sum this stretched-exponential majorant.
-/
theorem chewi125_far_stepdiff_row_true_le_twodkernel {alpha gamma : ℝ}
    (halpha : 0 < alpha) (hgamma_nonneg : 0 ≤ gamma)
    {k M : ℕ} (hk : 1 ≤ k) :
    (∑ d ∈ Finset.Ico (k + 1) M,
      ((gamma * (k : ℝ) ^ (-gamma - 1)) * (((d : ℕ) : ℝ) + 1)) *
        Real.exp (-((alpha * (((k + d : ℕ) : ℝ) ^ (-gamma))) * ((d : ℕ) : ℝ)))) ≤
      ∑ d ∈ Finset.Ico (k + 1) M,
        ((gamma * (k : ℝ) ^ (-gamma - 1)) * (((d : ℕ) : ℝ) + 1)) *
          Real.exp (-((alpha * (((2 * d : ℕ) : ℝ) ^ (-gamma))) * ((d : ℕ) : ℝ))) := by
  refine Finset.sum_le_sum ?_
  intro d hdmem
  have hkd : k < d := by
    have hmem : k + 1 ≤ d ∧ d < M := by
      simpa [Finset.mem_Ico] using hdmem
    omega
  exact chewi125_far_stepdiff_term_le_twodkernel
    (alpha := alpha) (gamma := gamma) halpha hgamma_nonneg
    (k := k) (d := d) hk hkd

/--
The far-diagonal `2d` kernel is exactly a stretched exponential with exponent
`1 - γ`.  This is the algebraic bridge needed before applying summability or
integral-comparison APIs to the far tail.
-/
theorem chewi125_twodkernel_exp_eq_stretched {alpha gamma : ℝ}
    {d : ℕ} (hd : 1 ≤ d) :
    Real.exp (-((alpha * (((2 * d : ℕ) : ℝ) ^ (-gamma))) * ((d : ℕ) : ℝ))) =
      Real.exp (-(alpha * (2 : ℝ) ^ (-gamma) * ((d : ℝ) ^ (1 - gamma)))) := by
  have hdpos : 0 < (d : ℝ) := Nat.cast_pos.mpr hd
  have htwopos : 0 < (2 : ℝ) := by norm_num
  congr 1
  calc
    -((alpha * (((2 * d : ℕ) : ℝ) ^ (-gamma))) * ((d : ℕ) : ℝ))
        = -((alpha * (((2 : ℝ) * (d : ℝ)) ^ (-gamma))) * (d : ℝ)) := by
          norm_num
    _ = -((alpha * ((2 : ℝ) ^ (-gamma) * (d : ℝ) ^ (-gamma))) * (d : ℝ)) := by
          rw [Real.mul_rpow (le_of_lt htwopos) (le_of_lt hdpos)]
    _ = -(alpha * (2 : ℝ) ^ (-gamma) * ((d : ℝ) ^ (-gamma) * (d : ℝ))) := by
          ring
    _ = -(alpha * (2 : ℝ) ^ (-gamma) * ((d : ℝ) ^ (-gamma) * (d : ℝ) ^ 1)) := by
          simp
    _ = -(alpha * (2 : ℝ) ^ (-gamma) * ((d : ℝ) ^ ((-gamma) + 1))) := by
          rw [Real.rpow_add hdpos]
          simp [Real.rpow_one]
    _ = -(alpha * (2 : ℝ) ^ (-gamma) * ((d : ℝ) ^ (1 - gamma))) := by
          ring_nf

/--
Source-shaped far-diagonal row comparison with the exact stretched-exponential
majorant `exp(-(alpha * 2^{-γ}) d^{1-γ})`.
-/
theorem chewi125_far_stepdiff_row_true_le_stretched_sum {alpha gamma : ℝ}
    (halpha : 0 < alpha) (hgamma_nonneg : 0 ≤ gamma)
    {k M : ℕ} (hk : 1 ≤ k) :
    (∑ d ∈ Finset.Ico (k + 1) M,
      ((gamma * (k : ℝ) ^ (-gamma - 1)) * (((d : ℕ) : ℝ) + 1)) *
        Real.exp (-((alpha * (((k + d : ℕ) : ℝ) ^ (-gamma))) * ((d : ℕ) : ℝ)))) ≤
      ∑ d ∈ Finset.Ico (k + 1) M,
        ((gamma * (k : ℝ) ^ (-gamma - 1)) * (((d : ℕ) : ℝ) + 1)) *
          Real.exp (-(alpha * (2 : ℝ) ^ (-gamma) * ((d : ℝ) ^ (1 - gamma)))) := by
  calc
    (∑ d ∈ Finset.Ico (k + 1) M,
      ((gamma * (k : ℝ) ^ (-gamma - 1)) * (((d : ℕ) : ℝ) + 1)) *
        Real.exp (-((alpha * (((k + d : ℕ) : ℝ) ^ (-gamma))) * ((d : ℕ) : ℝ))))
        ≤
      ∑ d ∈ Finset.Ico (k + 1) M,
        ((gamma * (k : ℝ) ^ (-gamma - 1)) * (((d : ℕ) : ℝ) + 1)) *
          Real.exp (-((alpha * (((2 * d : ℕ) : ℝ) ^ (-gamma))) * ((d : ℕ) : ℝ))) :=
        chewi125_far_stepdiff_row_true_le_twodkernel
          (alpha := alpha) (gamma := gamma) halpha hgamma_nonneg (k := k) (M := M) hk
    _ =
      ∑ d ∈ Finset.Ico (k + 1) M,
        ((gamma * (k : ℝ) ^ (-gamma - 1)) * (((d : ℕ) : ℝ) + 1)) *
          Real.exp (-(alpha * (2 : ℝ) ^ (-gamma) * ((d : ℝ) ^ (1 - gamma)))) := by
          refine Finset.sum_congr rfl ?_
          intro d hdmem
          have hd : 1 ≤ d := by
            have hmem : k + 1 ≤ d ∧ d < M := by
              simpa [Finset.mem_Ico] using hdmem
            omega
          rw [chewi125_twodkernel_exp_eq_stretched
            (alpha := alpha) (gamma := gamma) (d := d) hd]

/--
Polynomially weighted stretched exponentials are summable on `ℕ`.  This is the
main analytic primitive for the far-diagonal half of Chewi Lemma 12.5: the
stretched exponential eventually dominates the polynomial factor by comparison
with the summable p-series `d^{-2}`.
-/
theorem chewi125_summable_stretched_exp_mul_succ
    {c p : ℝ} (hc : 0 < c) (hp : 0 < p) :
    Summable fun d : ℕ => ((d : ℝ) + 1) * Real.exp (-(c * (d : ℝ) ^ p)) := by
  refine summable_of_isBigO_nat
    (Real.summable_nat_rpow.mpr (by norm_num : (-2 : ℝ) < -1)) ?_
  have hpow_exp (k : ℕ) :
      Tendsto (fun d : ℕ => ((d : ℝ) ^ k) * Real.exp (-(c * (d : ℝ) ^ p)))
        atTop (𝓝 0) := by
    have hraw :
        Tendsto
          (fun d : ℕ =>
            (((d : ℝ) ^ p) ^ ((k : ℝ) / p)) * Real.exp (-c * ((d : ℝ) ^ p)))
          atTop (𝓝 0) :=
      (tendsto_rpow_mul_exp_neg_mul_atTop_nhds_zero ((k : ℝ) / p) c hc).comp
        ((tendsto_rpow_atTop hp).comp tendsto_natCast_atTop_atTop)
    refine hraw.congr' ?_
    filter_upwards [eventually_ge_atTop (1 : ℕ)] with d hd
    have hdpos_nat : 0 < d := Nat.lt_of_lt_of_le Nat.zero_lt_one hd
    have hdpos : 0 < (d : ℝ) := Nat.cast_pos.mpr hdpos_nat
    rw [show -c * ((d : ℝ) ^ p) = -(c * (d : ℝ) ^ p) by ring]
    congr 1
    calc
      ((d : ℝ) ^ p) ^ ((k : ℝ) / p) = (d : ℝ) ^ (p * ((k : ℝ) / p)) := by
        rw [Real.rpow_mul (le_of_lt hdpos)]
      _ = (d : ℝ) ^ (k : ℝ) := by
        field_simp [ne_of_gt hp]
      _ = (d : ℝ) ^ k := by
        simp
  have hpolyexp :
      Tendsto
        (fun d : ℕ => (((d : ℝ) ^ 3 + (d : ℝ) ^ 2) *
          Real.exp (-(c * (d : ℝ) ^ p))))
        atTop (𝓝 0) := by
    simpa [add_mul] using (hpow_exp 3).add (hpow_exp 2)
  have hratio :
      Tendsto
        (fun d : ℕ =>
          (((d : ℝ) + 1) * Real.exp (-(c * (d : ℝ) ^ p))) / ((d : ℝ) ^ (-2 : ℝ)))
        atTop (𝓝 0) := by
    refine hpolyexp.congr' ?_
    filter_upwards [eventually_ge_atTop (1 : ℕ)] with d hd
    have hdpos_nat : 0 < d := Nat.lt_of_lt_of_le Nat.zero_lt_one hd
    have hdpos : 0 < (d : ℝ) := Nat.cast_pos.mpr hdpos_nat
    have hdne : (d : ℝ) ≠ 0 := ne_of_gt hdpos
    rw [Real.rpow_neg (le_of_lt hdpos)]
    field_simp [Real.rpow_natCast, hdne]
    simp
  refine isBigO_of_div_tendsto_nhds (c := (0 : ℝ)) ?_ hratio
  filter_upwards [eventually_ge_atTop (1 : ℕ)] with d hd hzero
  have hdpos_nat : 0 < d := Nat.lt_of_lt_of_le Nat.zero_lt_one hd
  have hdpos : 0 < (d : ℝ) := Nat.cast_pos.mpr hdpos_nat
  exact (Real.rpow_pos_of_pos hdpos (-2 : ℝ)).ne' hzero |>.elim

/-- Finite far-tail stretched-exponential rows are bounded by the full `tsum`. -/
theorem chewi125_stretched_exp_Ico_succ_le_tsum_of_summable
    {c p : ℝ}
    (hrow : Summable fun d : ℕ =>
      ((d : ℝ) + 1) * Real.exp (-(c * (d : ℝ) ^ p)))
    (k M : ℕ) :
    (∑ d ∈ Finset.Ico (k + 1) M,
        ((d : ℝ) + 1) * Real.exp (-(c * (d : ℝ) ^ p))) ≤
      ∑' d : ℕ, ((d : ℝ) + 1) * Real.exp (-(c * (d : ℝ) ^ p)) := by
  exact hrow.sum_le_tsum (Finset.Ico (k + 1) M) (fun d _hd => by positivity)

/--
Source-shaped finite-row bound for the stretched-exponential majorant.  This
is the reusable finite-row handoff that will feed the outer `k^{-γ-1}` sum in
the far-diagonal half of Chewi Lemma 12.5.
-/
theorem chewi125_stretched_exp_Ico_succ_le_tsum
    {c p : ℝ} (hc : 0 < c) (hp : 0 < p) (k M : ℕ) :
    (∑ d ∈ Finset.Ico (k + 1) M,
        ((d : ℝ) + 1) * Real.exp (-(c * (d : ℝ) ^ p))) ≤
      ∑' d : ℕ, ((d : ℝ) + 1) * Real.exp (-(c * (d : ℝ) ^ p)) :=
  chewi125_stretched_exp_Ico_succ_le_tsum_of_summable
    (chewi125_summable_stretched_exp_mul_succ (c := c) (p := p) hc hp) k M

/--
Far-diagonal source row bounded by a `k`-dependent coefficient times the full
stretched-exponential `tsum`.  This combines the V128 kernel reduction with
the summability/finite-row handoff above.
-/
theorem chewi125_far_stepdiff_row_true_le_stretched_tsum {alpha gamma : ℝ}
    (halpha : 0 < alpha) (hgamma_nonneg : 0 ≤ gamma) (hgamma_lt : gamma < 1)
    {k M : ℕ} (hk : 1 ≤ k) :
    (∑ d ∈ Finset.Ico (k + 1) M,
      ((gamma * (k : ℝ) ^ (-gamma - 1)) * (((d : ℕ) : ℝ) + 1)) *
        Real.exp (-((alpha * (((k + d : ℕ) : ℝ) ^ (-gamma))) * ((d : ℕ) : ℝ)))) ≤
      (gamma * (k : ℝ) ^ (-gamma - 1)) *
        (∑' d : ℕ,
          ((d : ℝ) + 1) *
            Real.exp (-(alpha * (2 : ℝ) ^ (-gamma) * ((d : ℝ) ^ (1 - gamma))))) := by
  let c : ℝ := alpha * (2 : ℝ) ^ (-gamma)
  let p : ℝ := 1 - gamma
  have hp : 0 < p := by
    simp [p]
    linarith
  have hc : 0 < c := by
    exact mul_pos halpha (Real.rpow_pos_of_pos (by norm_num : (0 : ℝ) < 2) (-gamma))
  have hrow :=
    chewi125_far_stepdiff_row_true_le_stretched_sum
      (alpha := alpha) (gamma := gamma) halpha hgamma_nonneg
      (k := k) (M := M) hk
  have hrewrite :
      (∑ d ∈ Finset.Ico (k + 1) M,
        ((gamma * (k : ℝ) ^ (-gamma - 1)) * (((d : ℕ) : ℝ) + 1)) *
          Real.exp (-(alpha * (2 : ℝ) ^ (-gamma) * ((d : ℝ) ^ (1 - gamma))))) =
        (gamma * (k : ℝ) ^ (-gamma - 1)) *
          ∑ d ∈ Finset.Ico (k + 1) M,
            ((d : ℝ) + 1) *
              Real.exp (-(alpha * (2 : ℝ) ^ (-gamma) * ((d : ℝ) ^ (1 - gamma)))) := by
    rw [Finset.mul_sum]
    refine Finset.sum_congr rfl ?_
    intro d _hd
    ring
  have hfinite :
      (∑ d ∈ Finset.Ico (k + 1) M,
            ((d : ℝ) + 1) *
              Real.exp (-(alpha * (2 : ℝ) ^ (-gamma) * ((d : ℝ) ^ (1 - gamma)))) ) ≤
        ∑' d : ℕ,
          ((d : ℝ) + 1) *
            Real.exp (-(alpha * (2 : ℝ) ^ (-gamma) * ((d : ℝ) ^ (1 - gamma))) ) := by
    simpa [c, p, mul_assoc] using
      chewi125_stretched_exp_Ico_succ_le_tsum
        (c := c) (p := p) hc hp k M
  have hcoef_nonneg : 0 ≤ gamma * (k : ℝ) ^ (-gamma - 1) := by
    exact mul_nonneg hgamma_nonneg
      (Real.rpow_nonneg (Nat.cast_nonneg k) (-gamma - 1))
  calc
    (∑ d ∈ Finset.Ico (k + 1) M,
      ((gamma * (k : ℝ) ^ (-gamma - 1)) * (((d : ℕ) : ℝ) + 1)) *
        Real.exp (-((alpha * (((k + d : ℕ) : ℝ) ^ (-gamma))) * ((d : ℕ) : ℝ))))
        ≤
      ∑ d ∈ Finset.Ico (k + 1) M,
        ((gamma * (k : ℝ) ^ (-gamma - 1)) * (((d : ℕ) : ℝ) + 1)) *
          Real.exp (-(alpha * (2 : ℝ) ^ (-gamma) * ((d : ℝ) ^ (1 - gamma)))) := hrow
    _ = (gamma * (k : ℝ) ^ (-gamma - 1)) *
          ∑ d ∈ Finset.Ico (k + 1) M,
            ((d : ℝ) + 1) *
              Real.exp (-(alpha * (2 : ℝ) ^ (-gamma) * ((d : ℝ) ^ (1 - gamma))) ) := hrewrite
    _ ≤ (gamma * (k : ℝ) ^ (-gamma - 1)) *
        (∑' d : ℕ,
          ((d : ℝ) + 1) *
            Real.exp (-(alpha * (2 : ℝ) ^ (-gamma) * ((d : ℝ) ^ (1 - gamma))))) :=
      mul_le_mul_of_nonneg_left hfinite hcoef_nonneg

/--
Far-diagonal rows summed over `k`, with the remaining finite outer factor left
as the source power row `∑ γ k^{-γ-1}`.
-/
theorem chewi125_far_stepdiff_rows_true_le_stretched_tsum_finite_power_sum
    {alpha gamma : ℝ}
    (halpha : 0 < alpha) (hgamma_nonneg : 0 ≤ gamma) (hgamma_lt : gamma < 1)
    {N M : ℕ} :
    (∑ k ∈ Finset.Ico 1 N,
      ∑ d ∈ Finset.Ico (k + 1) M,
        ((gamma * (k : ℝ) ^ (-gamma - 1)) * (((d : ℕ) : ℝ) + 1)) *
          Real.exp (-((alpha * (((k + d : ℕ) : ℝ) ^ (-gamma))) * ((d : ℕ) : ℝ)))) ≤
      (∑ k ∈ Finset.Ico 1 N, gamma * (k : ℝ) ^ (-gamma - 1)) *
        (∑' d : ℕ,
          ((d : ℝ) + 1) *
            Real.exp (-(alpha * (2 : ℝ) ^ (-gamma) * ((d : ℝ) ^ (1 - gamma))))) := by
  calc
    (∑ k ∈ Finset.Ico 1 N,
      ∑ d ∈ Finset.Ico (k + 1) M,
        ((gamma * (k : ℝ) ^ (-gamma - 1)) * (((d : ℕ) : ℝ) + 1)) *
          Real.exp (-((alpha * (((k + d : ℕ) : ℝ) ^ (-gamma))) * ((d : ℕ) : ℝ))))
        ≤
      ∑ k ∈ Finset.Ico 1 N,
        (gamma * (k : ℝ) ^ (-gamma - 1)) *
          (∑' d : ℕ,
            ((d : ℝ) + 1) *
              Real.exp (-(alpha * (2 : ℝ) ^ (-gamma) * ((d : ℝ) ^ (1 - gamma))))) := by
          refine Finset.sum_le_sum ?_
          intro k hk
          have hk_mem : 1 ≤ k ∧ k < N := by
            simpa [Finset.mem_Ico] using hk
          exact chewi125_far_stepdiff_row_true_le_stretched_tsum
            (alpha := alpha) (gamma := gamma) halpha hgamma_nonneg hgamma_lt
            (k := k) (M := M) hk_mem.1
    _ =
      (∑ k ∈ Finset.Ico 1 N, gamma * (k : ℝ) ^ (-gamma - 1)) *
        (∑' d : ℕ,
          ((d : ℝ) + 1) *
            Real.exp (-(alpha * (2 : ℝ) ^ (-gamma) * ((d : ℝ) ^ (1 - gamma))))) := by
        rw [Finset.sum_mul]

/--
The outer far-diagonal power row is bounded by its summable p-series tail.
This is the finite `k` handoff needed after the stretched-exponential row
bound.
-/
theorem chewi125_sum_Ico_rpow_neg_gamma_sub_one_le_tsum
    {gamma : ℝ} (hgamma_pos : 0 < gamma) (N : ℕ) :
    (∑ k ∈ Finset.Ico 1 N, (k : ℝ) ^ (-gamma - 1)) ≤
      ∑' k : ℕ, (k : ℝ) ^ (-gamma - 1) := by
  have hsummable :
      Summable fun k : ℕ => (k : ℝ) ^ (-gamma - 1) :=
    Real.summable_nat_rpow.mpr (by linarith)
  exact hsummable.sum_le_tsum (Finset.Ico 1 N) (fun k _hk =>
    Real.rpow_nonneg (Nat.cast_nonneg k) (-gamma - 1))

/--
Uniform far-diagonal bound by the product of the stretched-exponential `tsum`
and the summable outer power `tsum`.  This is stronger than the eventual
`C * N^γ` shape needed for Chewi Lemma 12.5.
-/
theorem chewi125_far_stepdiff_rows_true_le_stretched_tsum_prod_tsum
    {alpha gamma : ℝ}
    (halpha : 0 < alpha) (hgamma_pos : 0 < gamma) (hgamma_lt : gamma < 1)
    {N M : ℕ} :
    (∑ k ∈ Finset.Ico 1 N,
      ∑ d ∈ Finset.Ico (k + 1) M,
        ((gamma * (k : ℝ) ^ (-gamma - 1)) * (((d : ℕ) : ℝ) + 1)) *
          Real.exp (-((alpha * (((k + d : ℕ) : ℝ) ^ (-gamma))) * ((d : ℕ) : ℝ)))) ≤
      (gamma * (∑' k : ℕ, (k : ℝ) ^ (-gamma - 1))) *
        (∑' d : ℕ,
          ((d : ℝ) + 1) *
            Real.exp (-(alpha * (2 : ℝ) ^ (-gamma) * ((d : ℝ) ^ (1 - gamma))))) := by
  have hfinite :=
    chewi125_far_stepdiff_rows_true_le_stretched_tsum_finite_power_sum
      (alpha := alpha) (gamma := gamma) halpha hgamma_pos.le hgamma_lt
      (N := N) (M := M)
  have hpower :=
    chewi125_sum_Ico_rpow_neg_gamma_sub_one_le_tsum
      (gamma := gamma) hgamma_pos N
  have hgamma_power :
      (∑ k ∈ Finset.Ico 1 N, gamma * (k : ℝ) ^ (-gamma - 1)) ≤
        gamma * (∑' k : ℕ, (k : ℝ) ^ (-gamma - 1)) := by
    rw [← Finset.mul_sum]
    exact mul_le_mul_of_nonneg_left hpower hgamma_pos.le
  have hD_nonneg :
      0 ≤
        (∑' d : ℕ,
          ((d : ℝ) + 1) *
            Real.exp (-(alpha * (2 : ℝ) ^ (-gamma) * ((d : ℝ) ^ (1 - gamma))))) :=
    tsum_nonneg fun d => by positivity
  exact hfinite.trans (mul_le_mul_of_nonneg_right hgamma_power hD_nonneg)

/--
Source-order far-diagonal estimate for Chewi Lemma 12.5.  The far rows are
uniformly bounded, hence also bounded by an explicit constant times `N^γ` for
`N ≥ 1`.
-/
theorem chewi125_far_stepdiff_rows_true_le_power
    {alpha gamma : ℝ}
    (halpha : 0 < alpha) (hgamma_pos : 0 < gamma) (hgamma_lt : gamma < 1)
    {N M : ℕ} (hN : 1 ≤ N) :
    (∑ k ∈ Finset.Ico 1 N,
      ∑ d ∈ Finset.Ico (k + 1) M,
        ((gamma * (k : ℝ) ^ (-gamma - 1)) * (((d : ℕ) : ℝ) + 1)) *
          Real.exp (-((alpha * (((k + d : ℕ) : ℝ) ^ (-gamma))) * ((d : ℕ) : ℝ)))) ≤
      ((gamma * (∑' k : ℕ, (k : ℝ) ^ (-gamma - 1))) *
        (∑' d : ℕ,
          ((d : ℝ) + 1) *
            Real.exp (-(alpha * (2 : ℝ) ^ (-gamma) * ((d : ℝ) ^ (1 - gamma))))))
        * (N : ℝ) ^ gamma := by
  let Cfar : ℝ :=
    (gamma * (∑' k : ℕ, (k : ℝ) ^ (-gamma - 1))) *
      (∑' d : ℕ,
        ((d : ℝ) + 1) *
          Real.exp (-(alpha * (2 : ℝ) ^ (-gamma) * ((d : ℝ) ^ (1 - gamma)))))
  have hprod :=
    chewi125_far_stepdiff_rows_true_le_stretched_tsum_prod_tsum
      (alpha := alpha) (gamma := gamma) halpha hgamma_pos hgamma_lt
      (N := N) (M := M)
  have hK_nonneg :
      0 ≤ ∑' k : ℕ, (k : ℝ) ^ (-gamma - 1) :=
    tsum_nonneg fun k => Real.rpow_nonneg (Nat.cast_nonneg k) (-gamma - 1)
  have hD_nonneg :
      0 ≤
        (∑' d : ℕ,
          ((d : ℝ) + 1) *
            Real.exp (-(alpha * (2 : ℝ) ^ (-gamma) * ((d : ℝ) ^ (1 - gamma))))) :=
    tsum_nonneg fun d => by positivity
  have hC_nonneg : 0 ≤ Cfar := by
    exact mul_nonneg (mul_nonneg hgamma_pos.le hK_nonneg) hD_nonneg
  have hpow_one : 1 ≤ (N : ℝ) ^ gamma :=
    Real.one_le_rpow (Nat.one_le_cast.mpr hN) hgamma_pos.le
  have hC_le : Cfar ≤ Cfar * (N : ℝ) ^ gamma := by
    calc
      Cfar = Cfar * 1 := by ring
      _ ≤ Cfar * (N : ℝ) ^ gamma :=
        mul_le_mul_of_nonneg_left hpow_one hC_nonneg
  exact hprod.trans (by simpa [Cfar] using hC_le)

/-- The reindexed derivative-geometric kernel in Chewi Lemma 12.5, with `j = k + d`. -/
noncomputable def chewi125StepdiffDerivativeKernel
    (alpha gamma : ℝ) (k d : ℕ) : ℝ :=
  ((gamma * (k : ℝ) ^ (-gamma - 1)) * (((d : ℕ) : ℝ) + 1)) *
    Real.exp (-((alpha * (((k + d : ℕ) : ℝ) ^ (-gamma))) * ((d : ℕ) : ℝ)))

/--
Split a reindexed derivative-geometric row into the near range `d ≤ k`, padded
to `Ico 0 (k+1)`, and the far range `k < d`, padded to `Ico (k+1) P`.
-/
theorem chewi125_deriv_geometric_reindexed_row_le_near_far_sums
    {alpha gamma : ℝ} (hgamma_nonneg : 0 ≤ gamma) (k M P : ℕ) (hMP : M ≤ P) :
    (∑ d ∈ Finset.Ico 0 M, chewi125StepdiffDerivativeKernel alpha gamma k d) ≤
      (∑ d ∈ Finset.Ico 0 (k + 1), chewi125StepdiffDerivativeKernel alpha gamma k d) +
        ∑ d ∈ Finset.Ico (k + 1) P,
          chewi125StepdiffDerivativeKernel alpha gamma k d := by
  let nearSet := (Finset.Ico 0 M).filter (fun d : ℕ => d ≤ k)
  let farSet := (Finset.Ico 0 M).filter (fun d : ℕ => k < d)
  have hpartition :
      Finset.Ico 0 M = nearSet ∪ farSet := by
    ext d
    simp [nearSet, farSet]
    omega
  have hdisj : Disjoint nearSet farSet := by
    rw [Finset.disjoint_left]
    intro d hdnear hdfar
    simp [nearSet, farSet] at hdnear hdfar
    omega
  have hsum_split :
      (∑ d ∈ Finset.Ico 0 M, chewi125StepdiffDerivativeKernel alpha gamma k d) =
        (∑ d ∈ nearSet, chewi125StepdiffDerivativeKernel alpha gamma k d) +
          ∑ d ∈ farSet, chewi125StepdiffDerivativeKernel alpha gamma k d := by
    rw [hpartition, Finset.sum_union hdisj]
  have hnear_subset : nearSet ⊆ Finset.Ico 0 (k + 1) := by
    intro d hd
    simp [nearSet] at hd ⊢
    omega
  have hnear_nonneg_extra :
      ∀ x ∈ Finset.Ico 0 (k + 1), x ∉ nearSet →
        0 ≤ chewi125StepdiffDerivativeKernel alpha gamma k x := by
    intro d _hd _hnot
    dsimp [chewi125StepdiffDerivativeKernel]
    positivity
  have hnear_le :
      (∑ d ∈ nearSet, chewi125StepdiffDerivativeKernel alpha gamma k d) ≤
        ∑ d ∈ Finset.Ico 0 (k + 1), chewi125StepdiffDerivativeKernel alpha gamma k d := by
    exact Finset.sum_le_sum_of_subset_of_nonneg hnear_subset hnear_nonneg_extra
  have hfar_subset : farSet ⊆ Finset.Ico (k + 1) P := by
    intro d hd
    simp [farSet] at hd ⊢
    omega
  have hfar_nonneg_extra :
      ∀ x ∈ Finset.Ico (k + 1) P, x ∉ farSet →
        0 ≤ chewi125StepdiffDerivativeKernel alpha gamma k x := by
    intro d _hd _hnot
    dsimp [chewi125StepdiffDerivativeKernel]
    positivity
  have hfar_le :
      (∑ d ∈ farSet, chewi125StepdiffDerivativeKernel alpha gamma k d) ≤
        ∑ d ∈ Finset.Ico (k + 1) P,
          chewi125StepdiffDerivativeKernel alpha gamma k d := by
    exact Finset.sum_le_sum_of_subset_of_nonneg hfar_subset hfar_nonneg_extra
  rw [hsum_split]
  exact add_le_add hnear_le hfar_le

/-- Reindex one derivative-geometric row from `j` to `d = j - k`. -/
theorem chewi125_deriv_geometric_row_reindex
    {alpha gamma : ℝ} (k N : ℕ) :
    (∑ j ∈ Finset.Ico k N,
      ((gamma * (k : ℝ) ^ (-gamma - 1)) *
          ‖((j + 1 : ℕ) : ℝ) - (k : ℝ)‖) *
        Real.exp (-(alpha * (j : ℝ) ^ (-gamma)) * ((j - k : ℕ) : ℝ))) =
      ∑ d ∈ Finset.Ico 0 (N - k), chewi125StepdiffDerivativeKernel alpha gamma k d := by
  rw [Finset.sum_Ico_eq_sum_range]
  rw [Finset.range_eq_Ico]
  refine Finset.sum_congr rfl ?_
  intro d hd
  have hsub : k + d - k = d := by omega
  have hcast_sub :
      (((k + d + 1 : ℕ) : ℝ) - (k : ℝ)) = ((d : ℕ) : ℝ) + 1 := by
    rw [show k + d + 1 = k + (d + 1) by omega]
    norm_num
  have habs : |(((k + d + 1 : ℕ) : ℝ) - (k : ℝ))| = ((d : ℝ) + 1) := by
    rw [hcast_sub]
    exact abs_of_nonneg (by positivity)
  dsimp [chewi125StepdiffDerivativeKernel]
  rw [hsub, habs]
  ring_nf

/--
The full reindexed derivative-geometric double sum is bounded by the sum of the
near and far source-order estimates.
-/
theorem chewi125_deriv_geometric_reindexed_double_sum_le_near_far
    {alpha gamma : ℝ}
    (halpha : 0 < alpha) (hgamma_pos : 0 < gamma) (hgamma_lt : gamma < 1)
    {N : ℕ} (hN : 1 ≤ N) :
    (∑ k ∈ Finset.Ico 1 N,
      ∑ d ∈ Finset.Ico 0 (N - k),
        chewi125StepdiffDerivativeKernel alpha gamma k d) ≤
      (gamma * (Real.exp alpha / alpha ^ 2 + Real.exp alpha / alpha) *
          (2 : ℝ) ^ (2 * gamma)) *
        ((1 + gamma⁻¹) * (N : ℝ) ^ gamma) +
      ((gamma * (∑' k : ℕ, (k : ℝ) ^ (-gamma - 1))) *
        (∑' d : ℕ,
          ((d : ℝ) + 1) *
            Real.exp (-(alpha * (2 : ℝ) ^ (-gamma) * ((d : ℝ) ^ (1 - gamma))))))
        * (N : ℝ) ^ gamma := by
  let nearRows : ℕ → ℝ := fun k =>
    ∑ d ∈ Finset.Ico 0 (k + 1), chewi125StepdiffDerivativeKernel alpha gamma k d
  let farRows : ℕ → ℝ := fun k =>
    ∑ d ∈ Finset.Ico (k + 1) N, chewi125StepdiffDerivativeKernel alpha gamma k d
  have hsplit :
      (∑ k ∈ Finset.Ico 1 N,
        ∑ d ∈ Finset.Ico 0 (N - k),
          chewi125StepdiffDerivativeKernel alpha gamma k d) ≤
        ∑ k ∈ Finset.Ico 1 N, (nearRows k + farRows k) := by
    refine Finset.sum_le_sum ?_
    intro k hk
    exact chewi125_deriv_geometric_reindexed_row_le_near_far_sums
      (alpha := alpha) (gamma := gamma) hgamma_pos.le k (N - k) N (by omega)
  have hnear :
      (∑ k ∈ Finset.Ico 1 N, nearRows k) ≤
        (gamma * (Real.exp alpha / alpha ^ 2 + Real.exp alpha / alpha) *
            (2 : ℝ) ^ (2 * gamma)) *
          ((1 + gamma⁻¹) * (N : ℝ) ^ gamma) := by
    simpa [nearRows, chewi125StepdiffDerivativeKernel] using
      chewi125_near_stepdiff_rows_true_le_power
        (alpha := alpha) (gamma := gamma) halpha hgamma_pos hgamma_lt hN
  have hfar :
      (∑ k ∈ Finset.Ico 1 N, farRows k) ≤
        ((gamma * (∑' k : ℕ, (k : ℝ) ^ (-gamma - 1))) *
          (∑' d : ℕ,
            ((d : ℝ) + 1) *
              Real.exp (-(alpha * (2 : ℝ) ^ (-gamma) * ((d : ℝ) ^ (1 - gamma))))))
          * (N : ℝ) ^ gamma := by
    simpa [farRows, chewi125StepdiffDerivativeKernel] using
      chewi125_far_stepdiff_rows_true_le_power
        (alpha := alpha) (gamma := gamma) halpha hgamma_pos hgamma_lt hN
  calc
    (∑ k ∈ Finset.Ico 1 N,
      ∑ d ∈ Finset.Ico 0 (N - k),
        chewi125StepdiffDerivativeKernel alpha gamma k d)
        ≤ ∑ k ∈ Finset.Ico 1 N, (nearRows k + farRows k) := hsplit
    _ = (∑ k ∈ Finset.Ico 1 N, nearRows k) +
          ∑ k ∈ Finset.Ico 1 N, farRows k := by
        rw [Finset.sum_add_distrib]
    _ ≤
      (gamma * (Real.exp alpha / alpha ^ 2 + Real.exp alpha / alpha) *
          (2 : ℝ) ^ (2 * gamma)) *
        ((1 + gamma⁻¹) * (N : ℝ) ^ gamma) +
      ((gamma * (∑' k : ℕ, (k : ℝ) ^ (-gamma - 1))) *
        (∑' d : ℕ,
          ((d : ℝ) + 1) *
            Real.exp (-(alpha * (2 : ℝ) ^ (-gamma) * ((d : ℝ) ^ (1 - gamma))))))
        * (N : ℝ) ^ gamma :=
        add_le_add hnear hfar

/--
Source-order `C * N^γ` bound for the full reindexed derivative-geometric double
sum in Chewi Lemma 12.5.
-/
theorem chewi125_deriv_geometric_reindexed_double_sum_le_power
    {alpha gamma : ℝ}
    (halpha : 0 < alpha) (hgamma_pos : 0 < gamma) (hgamma_lt : gamma < 1)
    {N : ℕ} (hN : 1 ≤ N) :
    (∑ k ∈ Finset.Ico 1 N,
      ∑ d ∈ Finset.Ico 0 (N - k),
        chewi125StepdiffDerivativeKernel alpha gamma k d) ≤
      ((gamma * (Real.exp alpha / alpha ^ 2 + Real.exp alpha / alpha) *
          (2 : ℝ) ^ (2 * gamma)) * (1 + gamma⁻¹) +
        (gamma * (∑' k : ℕ, (k : ℝ) ^ (-gamma - 1))) *
          (∑' d : ℕ,
            ((d : ℝ) + 1) *
              Real.exp (-(alpha * (2 : ℝ) ^ (-gamma) * ((d : ℝ) ^ (1 - gamma)))))) *
        (N : ℝ) ^ gamma := by
  have h :=
    chewi125_deriv_geometric_reindexed_double_sum_le_near_far
      (alpha := alpha) (gamma := gamma) halpha hgamma_pos hgamma_lt hN
  refine h.trans_eq ?_
  ring

/--
Source-order bound for the unreindexed derivative-geometric double sum.  This
is the direct consumer-facing version of the near/far reindexed estimate.
-/
theorem chewi125_deriv_geometric_double_sum_le_power
    {alpha gamma : ℝ}
    (halpha : 0 < alpha) (hgamma_pos : 0 < gamma) (hgamma_lt : gamma < 1)
    {N : ℕ} (hN : 1 ≤ N) :
    (∑ k ∈ Finset.Ico 1 N,
      ∑ j ∈ Finset.Ico k N,
        ((gamma * (k : ℝ) ^ (-gamma - 1)) *
            ‖((j + 1 : ℕ) : ℝ) - (k : ℝ)‖) *
          Real.exp (-(alpha * (j : ℝ) ^ (-gamma)) * ((j - k : ℕ) : ℝ))) ≤
      ((gamma * (Real.exp alpha / alpha ^ 2 + Real.exp alpha / alpha) *
          (2 : ℝ) ^ (2 * gamma)) * (1 + gamma⁻¹) +
        (gamma * (∑' k : ℕ, (k : ℝ) ^ (-gamma - 1))) *
          (∑' d : ℕ,
            ((d : ℝ) + 1) *
              Real.exp (-(alpha * (2 : ℝ) ^ (-gamma) * ((d : ℝ) ^ (1 - gamma)))))) *
        (N : ℝ) ^ gamma := by
  have hreindex :
      (∑ k ∈ Finset.Ico 1 N,
        ∑ j ∈ Finset.Ico k N,
          ((gamma * (k : ℝ) ^ (-gamma - 1)) *
              ‖((j + 1 : ℕ) : ℝ) - (k : ℝ)‖) *
            Real.exp (-(alpha * (j : ℝ) ^ (-gamma)) * ((j - k : ℕ) : ℝ))) =
        ∑ k ∈ Finset.Ico 1 N,
          ∑ d ∈ Finset.Ico 0 (N - k),
            chewi125StepdiffDerivativeKernel alpha gamma k d := by
    refine Finset.sum_congr rfl ?_
    intro k _hk
    exact chewi125_deriv_geometric_row_reindex (alpha := alpha) (gamma := gamma) k N
  rw [hreindex]
  exact chewi125_deriv_geometric_reindexed_double_sum_le_power
    (alpha := alpha) (gamma := gamma) halpha hgamma_pos hgamma_lt hN

/--
Source-order bound for the original step-difference residual double sum.  This
composes the V125 derivative-geometric reduction with the V130 near/far bound.
-/
theorem chewi125_stepdiff_exp_double_sum_le_power
    {alpha gamma : ℝ}
    (halpha : 0 < alpha) (hgamma_pos : 0 < gamma) (hgamma_lt : gamma < 1)
    {N : ℕ} (hN : 1 ≤ N) :
    (∑ k ∈ Finset.Ico 1 N,
      ∑ j ∈ Finset.Ico k N,
        ‖chewi125PowerStep gamma k - chewi125PowerStep gamma (j + 1)‖ *
          Real.exp (-alpha *
            ∑ l ∈ Finset.Ico (k + 1) (j + 1),
              chewi125PowerStep gamma l)) ≤
      ((gamma * (Real.exp alpha / alpha ^ 2 + Real.exp alpha / alpha) *
          (2 : ℝ) ^ (2 * gamma)) * (1 + gamma⁻¹) +
        (gamma * (∑' k : ℕ, (k : ℝ) ^ (-gamma - 1))) *
          (∑' d : ℕ,
            ((d : ℝ) + 1) *
              Real.exp (-(alpha * (2 : ℝ) ^ (-gamma) * ((d : ℝ) ^ (1 - gamma)))))) *
        (N : ℝ) ^ gamma := by
  exact (chewi125_stepdiff_double_sum_le_deriv_geometric
    (alpha := alpha) (gamma := gamma) halpha hgamma_pos.le N).trans
    (chewi125_deriv_geometric_double_sum_le_power
      (alpha := alpha) (gamma := gamma) halpha hgamma_pos hgamma_lt hN)

/--
The step-difference residual double sum in Chewi Lemma 12.5 has vanishing
`1 / N` average for `0 < γ < 1`.  This closes the scalar near/far summation
part after the V125 derivative-geometric reduction.
-/
theorem chewi125_stepdiff_exp_double_average_tendsto_zero
    {alpha gamma : ℝ}
    (halpha : 0 < alpha) (hgamma_pos : 0 < gamma) (hgamma_lt : gamma < 1) :
    Tendsto
      (fun N : ℕ =>
        (N : ℝ)⁻¹ *
          ∑ k ∈ Finset.Ico 1 N,
            ∑ j ∈ Finset.Ico k N,
              ‖chewi125PowerStep gamma k - chewi125PowerStep gamma (j + 1)‖ *
                Real.exp (-alpha *
                  ∑ l ∈ Finset.Ico (k + 1) (j + 1),
                    chewi125PowerStep gamma l))
      atTop (𝓝 0) := by
  let C : ℝ :=
    (gamma * (Real.exp alpha / alpha ^ 2 + Real.exp alpha / alpha) *
        (2 : ℝ) ^ (2 * gamma)) * (1 + gamma⁻¹) +
      (gamma * (∑' k : ℕ, (k : ℝ) ^ (-gamma - 1))) *
        (∑' d : ℕ,
          ((d : ℝ) + 1) *
            Real.exp (-(alpha * (2 : ℝ) ^ (-gamma) * ((d : ℝ) ^ (1 - gamma)))))
  refine chewi125_stepdiff_exp_double_average_tendsto_zero_of_power_bound
    (alpha := alpha) (C := C) (gamma := gamma) hgamma_lt ?_
  refine eventually_atTop.2 ⟨1, ?_⟩
  intro N hN
  simpa [C] using
    chewi125_stepdiff_exp_double_sum_le_power
      (alpha := alpha) (gamma := gamma) halpha hgamma_pos hgamma_lt
      (N := N) hN

/--
Initial ASGD coefficient norm bounded by any scalar majorant for the transition
products.
-/
theorem chewi123InitialCoefficient_norm_le_sum_transition_bound
    {E : Type*} [NormedAddCommGroup E] [NormedSpace ℝ E]
    (A : E →L[ℝ] E) (h : ℕ -> ℝ) (C : ℕ -> ℝ)
    (hC : ∀ i, ‖chewi123TransitionProductFrom A h 0 i‖ ≤ C i)
    (N : ℕ) :
    ‖chewi123InitialCoefficient A h N‖ ≤
      ∑ i ∈ Finset.range N, C i := by
  calc
    ‖chewi123InitialCoefficient A h N‖ =
        ‖∑ i ∈ Finset.range N, chewi123TransitionProductFrom A h 0 i‖ := by
      rfl
    _ ≤ ∑ i ∈ Finset.range N,
        ‖chewi123TransitionProductFrom A h 0 i‖ := by
      exact norm_sum_le (s := Finset.range N)
        (f := fun i => chewi123TransitionProductFrom A h 0 i)
    _ ≤ ∑ i ∈ Finset.range N, C i :=
      Finset.sum_le_sum fun i _hi => hC i

/--
Transition products starting at zero split into the first step followed by
the product starting at one.
-/
theorem chewi123TransitionProductFrom_zero_succ_eq_from_one_mul_first
    {E : Type*} [NormedAddCommGroup E] [NormedSpace ℝ E]
    (A : E →L[ℝ] E) (h : ℕ -> ℝ) (i : ℕ) :
    chewi123TransitionProductFrom A h 0 (i + 1) =
      chewi123TransitionProductFrom A h 1 i *
        chewi123QuadraticStepMap (h 1) A := by
  induction i with
  | zero =>
      simp [chewi123TransitionProductFrom]
  | succ i ih =>
      rw [chewi123TransitionProductFrom, ih]
      simp [chewi123TransitionProductFrom, mul_assoc, Nat.add_comm,
        Nat.add_left_comm]

/--
Lower bound the first-time tail of Chewi's power steps by the number of
remaining factors times the last step size.
-/
theorem chewi125_power_initial_tail_lower {gamma : ℝ}
    (hgamma_nonneg : 0 ≤ gamma) (d : ℕ) :
    (d : ℝ) * ((d + 1 : ℕ) : ℝ) ^ (-gamma) ≤
      ∑ l ∈ Finset.Ico 2 (d + 2), chewi125PowerStep gamma l := by
  simpa using
    (chewi125_power_tail_lower (gamma := gamma) hgamma_nonneg
      (N := d + 1) (k := 1))

/--
The initial tail exponential is bounded by the same stretched-exponential
majorant used in the far-diagonal part of Chewi Lemma 12.5.
-/
theorem chewi125_initial_tail_exp_le_stretched {alpha gamma : ℝ}
    (halpha : 0 < alpha) (hgamma_nonneg : 0 ≤ gamma)
    (hgamma_lt : gamma < 1) (d : ℕ) :
    Real.exp (-alpha *
        ∑ l ∈ Finset.Ico 2 (d + 2), chewi125PowerStep gamma l) ≤
      Real.exp (-(alpha * (2 : ℝ) ^ (-gamma) *
        ((d : ℝ) ^ (1 - gamma)))) := by
  cases d with
  | zero =>
      simp [Real.zero_rpow (by linarith : (1 - gamma) ≠ 0)]
  | succ d =>
      let d1 : ℕ := d + 1
      have hd1 : 1 ≤ d1 := by omega
      have htail :=
        chewi125_power_initial_tail_lower (gamma := gamma) hgamma_nonneg d1
      have hdpos : 0 < (d1 : ℝ) := Nat.cast_pos.mpr hd1
      have htwod_pos : 0 < (((2 * d1 : ℕ) : ℝ)) := by
        exact_mod_cast (show 0 < 2 * d1 by omega)
      have hd_succ_le_twod :
          (((d1 + 1 : ℕ) : ℝ)) ≤ (((2 * d1 : ℕ) : ℝ)) := by
        exact_mod_cast (show d1 + 1 ≤ 2 * d1 by omega)
      have hpow :
          (((2 * d1 : ℕ) : ℝ) ^ (-gamma)) ≤
            (((d1 + 1 : ℕ) : ℝ) ^ (-gamma)) :=
        Real.rpow_le_rpow_of_nonpos
          (by exact_mod_cast (show 0 < d1 + 1 by omega))
          hd_succ_le_twod (neg_nonpos.mpr hgamma_nonneg)
      have hrate_twod :
          alpha * (2 : ℝ) ^ (-gamma) * ((d1 : ℝ) ^ (1 - gamma)) =
            (alpha * (((2 * d1 : ℕ) : ℝ) ^ (-gamma))) *
              (d1 : ℝ) := by
        calc
          alpha * (2 : ℝ) ^ (-gamma) * ((d1 : ℝ) ^ (1 - gamma))
              = alpha * ((2 : ℝ) ^ (-gamma) *
                  ((d1 : ℝ) ^ ((-gamma) + 1))) := by ring_nf
          _ = alpha * ((2 : ℝ) ^ (-gamma) *
                  ((d1 : ℝ) ^ (-gamma) * (d1 : ℝ) ^ 1)) := by
                rw [Real.rpow_add hdpos]
                simp [Real.rpow_one]
          _ = (alpha * (((2 : ℝ) * (d1 : ℝ)) ^ (-gamma))) *
                  (d1 : ℝ) := by
                rw [Real.mul_rpow (by norm_num : (0 : ℝ) ≤ 2) hdpos.le]
                simp
                ring
          _ = (alpha * (((2 * d1 : ℕ) : ℝ) ^ (-gamma))) *
                  (d1 : ℝ) := by
                norm_num
      have hrate :
          alpha * (2 : ℝ) ^ (-gamma) * ((d1 : ℝ) ^ (1 - gamma)) ≤
            alpha *
              ∑ l ∈ Finset.Ico 2 (d1 + 2), chewi125PowerStep gamma l := by
        calc
          alpha * (2 : ℝ) ^ (-gamma) * ((d1 : ℝ) ^ (1 - gamma))
              = (alpha * (((2 * d1 : ℕ) : ℝ) ^ (-gamma))) *
                  (d1 : ℝ) := hrate_twod
          _ ≤ (alpha * (((d1 + 1 : ℕ) : ℝ) ^ (-gamma))) *
                  (d1 : ℝ) :=
                mul_le_mul_of_nonneg_right
                  (mul_le_mul_of_nonneg_left hpow halpha.le)
                  (Nat.cast_nonneg d1)
          _ = alpha * ((d1 : ℝ) *
                  (((d1 + 1 : ℕ) : ℝ) ^ (-gamma))) := by ring
          _ ≤ alpha *
                ∑ l ∈ Finset.Ico 2 (d1 + 2), chewi125PowerStep gamma l :=
                mul_le_mul_of_nonneg_left htail halpha.le
      exact Real.exp_le_exp.mpr (by linarith)

/--
Uniform constant for the deterministic initial coefficient in Chewi Lemma 12.5.
The first factor is kept as its operator norm; all later products are summed by
the stretched-exponential tail already used in the residual-row proof.
-/
noncomputable def chewi125InitialCoefficientUniformConstant
    {E : Type*} [NormedAddCommGroup E] [NormedSpace ℝ E]
    (A : E →L[ℝ] E) (alpha gamma : ℝ) : ℝ :=
  1 +
    ‖chewi123QuadraticStepMap (chewi125PowerStep gamma 1) A‖ *
      (∑' d : ℕ,
        ((d : ℝ) + 1) *
          Real.exp (-(alpha * (2 : ℝ) ^ (-gamma) *
            ((d : ℝ) ^ (1 - gamma)))))

/--
The source initial coefficient `M_0^N` is uniformly bounded under the same
eventual contraction hypothesis used in Chewi Lemma 12.5.
-/
theorem chewi123InitialCoefficient_norm_le_uniform_constant_of_quadratic_step_bound
    {E : Type*} [NormedAddCommGroup E] [NormedSpace ℝ E]
    (A : E →L[ℝ] E) {alpha gamma : ℝ}
    (halpha : 0 < alpha) (hgamma_pos : 0 < gamma) (hgamma_lt : gamma < 1)
    (hstep : ∀ m, 2 ≤ m ->
      ‖chewi123QuadraticStepMap (chewi125PowerStep gamma m) A‖ ≤
        1 - alpha * chewi125PowerStep gamma m)
    (hsmall : ∀ m, 2 ≤ m ->
      0 ≤ 1 - alpha * chewi125PowerStep gamma m)
    (N : ℕ) :
    ‖chewi123InitialCoefficient A (chewi125PowerStep gamma) N‖ ≤
      chewi125InitialCoefficientUniformConstant A alpha gamma := by
  let K : ℝ := ‖chewi123QuadraticStepMap (chewi125PowerStep gamma 1) A‖
  let W : ℕ -> ℝ := fun d =>
    ((d : ℝ) + 1) *
      Real.exp (-(alpha * (2 : ℝ) ^ (-gamma) *
        ((d : ℝ) ^ (1 - gamma))))
  have hK_nonneg : 0 ≤ K := norm_nonneg _
  have hW_nonneg : ∀ d, 0 ≤ W d := by
    intro d
    dsimp [W]
    exact mul_nonneg (by positivity) (le_of_lt (Real.exp_pos _))
  have hW_summable : Summable W := by
    simpa [W] using
      (chewi125_summable_stretched_exp_mul_succ
        (c := alpha * (2 : ℝ) ^ (-gamma)) (p := 1 - gamma)
        (mul_pos halpha
          (Real.rpow_pos_of_pos (by norm_num : (0 : ℝ) < 2) (-gamma)))
        (by linarith))
  have hW_tsum_nonneg : 0 ≤ ∑' d : ℕ, W d :=
    tsum_nonneg hW_nonneg
  cases N with
  | zero =>
      have hzero :
          chewi123InitialCoefficient A (chewi125PowerStep gamma) 0 = 0 := by
        simp [chewi123InitialCoefficient]
      have hconst_nonneg :
          0 ≤ chewi125InitialCoefficientUniformConstant A alpha gamma := by
        dsimp [chewi125InitialCoefficientUniformConstant]
        exact add_nonneg zero_le_one
          (mul_nonneg (norm_nonneg _)
            (by simpa [W] using hW_tsum_nonneg))
      simpa [hzero] using hconst_nonneg
  | succ N =>
      have htail_bound : ∀ d,
          ‖chewi123TransitionProductFrom A (chewi125PowerStep gamma) 0 (d + 1)‖ ≤
            K *
              Real.exp (-(alpha * (2 : ℝ) ^ (-gamma) *
                ((d : ℝ) ^ (1 - gamma)))) := by
        intro d
        have hsplit :=
          chewi123TransitionProductFrom_zero_succ_eq_from_one_mul_first
            A (chewi125PowerStep gamma) d
        have hprod :
            ‖chewi123TransitionProductFrom A (chewi125PowerStep gamma) 1 d‖ ≤
              Real.exp (-alpha *
                ∑ l ∈ Finset.Ico 2 (d + 2), chewi125PowerStep gamma l) := by
          have hraw :=
            chewi125_transitionProduct_norm_le_exp_sum
              (A := A) (alpha := alpha) (gamma := gamma) (N0 := 2)
              (k := 1) (j := d + 1) hstep hsmall (by omega) (by omega)
          simpa using hraw
        have hstretch :=
          chewi125_initial_tail_exp_le_stretched
            (alpha := alpha) (gamma := gamma) halpha hgamma_pos.le hgamma_lt d
        calc
          ‖chewi123TransitionProductFrom A (chewi125PowerStep gamma) 0 (d + 1)‖
              = ‖chewi123TransitionProductFrom A (chewi125PowerStep gamma) 1 d *
                    chewi123QuadraticStepMap (chewi125PowerStep gamma 1) A‖ := by
                  rw [hsplit]
          _ ≤ ‖chewi123TransitionProductFrom A (chewi125PowerStep gamma) 1 d‖ * K :=
                norm_mul_le _ _
          _ ≤ Real.exp (-alpha *
                  ∑ l ∈ Finset.Ico 2 (d + 2), chewi125PowerStep gamma l) * K :=
                mul_le_mul_of_nonneg_right hprod hK_nonneg
          _ ≤ Real.exp (-(alpha * (2 : ℝ) ^ (-gamma) *
                  ((d : ℝ) ^ (1 - gamma)))) * K :=
                mul_le_mul_of_nonneg_right hstretch hK_nonneg
          _ = K * Real.exp (-(alpha * (2 : ℝ) ^ (-gamma) *
                  ((d : ℝ) ^ (1 - gamma)))) := by ring
      have hsum_norm :
          ‖chewi123InitialCoefficient A (chewi125PowerStep gamma) (N + 1)‖ ≤
            ‖chewi123TransitionProductFrom A (chewi125PowerStep gamma) 0 0‖ +
              ∑ d ∈ Finset.range N,
                ‖chewi123TransitionProductFrom A (chewi125PowerStep gamma) 0 (d + 1)‖ := by
        calc
          ‖chewi123InitialCoefficient A (chewi125PowerStep gamma) (N + 1)‖
              ≤ ∑ i ∈ Finset.range (N + 1),
                  ‖chewi123TransitionProductFrom A (chewi125PowerStep gamma) 0 i‖ := by
                simpa [chewi123InitialCoefficient] using
                  norm_sum_le
                    (s := Finset.range (N + 1))
                    (f := fun i =>
                      chewi123TransitionProductFrom A (chewi125PowerStep gamma) 0 i)
          _ =
              ‖chewi123TransitionProductFrom A (chewi125PowerStep gamma) 0 0‖ +
                ∑ d ∈ Finset.range N,
                  ‖chewi123TransitionProductFrom A (chewi125PowerStep gamma) 0 (d + 1)‖ := by
                rw [Finset.sum_range_succ']
                rw [add_comm]
      have htail_sum :
          (∑ d ∈ Finset.range N,
              ‖chewi123TransitionProductFrom A (chewi125PowerStep gamma) 0 (d + 1)‖) ≤
            K * (∑' d : ℕ, W d) := by
        have htail_to_exp :
            (∑ d ∈ Finset.range N,
                ‖chewi123TransitionProductFrom A (chewi125PowerStep gamma) 0 (d + 1)‖) ≤
              ∑ d ∈ Finset.range N,
                K * Real.exp (-(alpha * (2 : ℝ) ^ (-gamma) *
                  ((d : ℝ) ^ (1 - gamma)))) :=
          Finset.sum_le_sum fun d _hd => htail_bound d
        have hexp_to_W :
            (∑ d ∈ Finset.range N,
                Real.exp (-(alpha * (2 : ℝ) ^ (-gamma) *
                  ((d : ℝ) ^ (1 - gamma))))) ≤
              ∑ d ∈ Finset.range N, W d := by
          refine Finset.sum_le_sum ?_
          intro d _hd
          have hcoef : 1 ≤ (d : ℝ) + 1 := by
            exact_mod_cast (Nat.le_add_left 1 d)
          have hexp_nonneg :
              0 ≤ Real.exp (-(alpha * (2 : ℝ) ^ (-gamma) *
                ((d : ℝ) ^ (1 - gamma)))) :=
            le_of_lt (Real.exp_pos _)
          calc
            Real.exp (-(alpha * (2 : ℝ) ^ (-gamma) *
                ((d : ℝ) ^ (1 - gamma))))
                = 1 *
                    Real.exp (-(alpha * (2 : ℝ) ^ (-gamma) *
                      ((d : ℝ) ^ (1 - gamma)))) := by ring
            _ ≤ ((d : ℝ) + 1) *
                    Real.exp (-(alpha * (2 : ℝ) ^ (-gamma) *
                      ((d : ℝ) ^ (1 - gamma)))) :=
                  mul_le_mul_of_nonneg_right hcoef hexp_nonneg
            _ = W d := rfl
        have hfinite_to_tsum :
            (∑ d ∈ Finset.range N, W d) ≤ ∑' d : ℕ, W d :=
          hW_summable.sum_le_tsum (Finset.range N) (fun d _hd => hW_nonneg d)
        calc
          (∑ d ∈ Finset.range N,
              ‖chewi123TransitionProductFrom A (chewi125PowerStep gamma) 0 (d + 1)‖)
              ≤ ∑ d ∈ Finset.range N,
                  K * Real.exp (-(alpha * (2 : ℝ) ^ (-gamma) *
                    ((d : ℝ) ^ (1 - gamma)))) := htail_to_exp
          _ = K * ∑ d ∈ Finset.range N,
                  Real.exp (-(alpha * (2 : ℝ) ^ (-gamma) *
                    ((d : ℝ) ^ (1 - gamma)))) := by
                rw [Finset.mul_sum]
          _ ≤ K * ∑ d ∈ Finset.range N, W d :=
                mul_le_mul_of_nonneg_left hexp_to_W hK_nonneg
          _ ≤ K * (∑' d : ℕ, W d) :=
                mul_le_mul_of_nonneg_left hfinite_to_tsum hK_nonneg
      have hzero_prod :
          ‖chewi123TransitionProductFrom A (chewi125PowerStep gamma) 0 0‖ ≤
            1 := by
        simpa [chewi123TransitionProductFrom] using
          (ContinuousLinearMap.norm_id_le (𝕜 := ℝ) (E := E))
      calc
        ‖chewi123InitialCoefficient A (chewi125PowerStep gamma) (N + 1)‖
            ≤
              ‖chewi123TransitionProductFrom A (chewi125PowerStep gamma) 0 0‖ +
                ∑ d ∈ Finset.range N,
                  ‖chewi123TransitionProductFrom A (chewi125PowerStep gamma) 0 (d + 1)‖ :=
              hsum_norm
        _ ≤ 1 + K * (∑' d : ℕ, W d) :=
              add_le_add hzero_prod htail_sum
        _ = chewi125InitialCoefficientUniformConstant A alpha gamma := by
              simp [chewi125InitialCoefficientUniformConstant, K, W]

/--
Adapter from a deterministic scalar majorant for the initial coefficient to
the exact `hinitial_decay` hypothesis used by the source-conditioned ASGD
wrappers.
-/
theorem chewi123InitialCoefficient_sqrt_decay_of_norm_bound
    {E : Type*} [NormedAddCommGroup E] [NormedSpace ℝ E]
    (A : E →L[ℝ] E) (h : ℕ -> ℝ) (C : ℕ -> ℝ) (B : ℝ)
    (hB : 0 ≤ B)
    (hbound : ∀ N, ‖chewi123InitialCoefficient A h N‖ ≤ C N)
    (hdecay :
      Tendsto
        (fun N : ℕ => ‖(Real.sqrt (N : ℝ))⁻¹‖ * C N * B)
        atTop (𝓝 0)) :
    Tendsto
      (fun N : ℕ =>
        ‖(Real.sqrt (N : ℝ))⁻¹‖ *
          ‖chewi123InitialCoefficient A h N‖ * B)
      atTop (𝓝 0) := by
  refine tendsto_of_tendsto_of_tendsto_of_le_of_le tendsto_const_nhds hdecay
    ?_ ?_
  · intro N
    exact mul_nonneg (mul_nonneg (norm_nonneg _) (norm_nonneg _)) hB
  · intro N
    have hmul :
        ‖chewi123InitialCoefficient A h N‖ * B ≤ C N * B :=
      mul_le_mul_of_nonneg_right (hbound N) hB
    simpa [mul_assoc] using
      mul_le_mul_of_nonneg_left hmul
        (norm_nonneg ((Real.sqrt (N : ℝ))⁻¹))

/--
The implicit initial-condition decay after Chewi Lemma 12.5: a uniform bound on
`M_0^N` makes the `sqrt N`-scaled initial coefficient vanish.  This isolates
the source's line after `(12.5)` from the harder residual-row estimates.
-/
theorem chewi123InitialCoefficient_sqrt_decay_of_uniform_norm_bound
    {E : Type*} [NormedAddCommGroup E] [NormedSpace ℝ E]
    (A : E →L[ℝ] E) (h : ℕ -> ℝ) (C B : ℝ)
    (hB : 0 ≤ B)
    (hbound : ∀ N, ‖chewi123InitialCoefficient A h N‖ ≤ C) :
    Tendsto
      (fun N : ℕ =>
        ‖(Real.sqrt (N : ℝ))⁻¹‖ *
          ‖chewi123InitialCoefficient A h N‖ * B)
      atTop (𝓝 0) := by
  refine chewi123InitialCoefficient_sqrt_decay_of_norm_bound
    A h (fun _N : ℕ => C) B hB hbound ?_
  have hinv_sqrt_tendsto :
      Tendsto (fun N : ℕ => (Real.sqrt (N : ℝ))⁻¹) atTop (𝓝 0) :=
    tendsto_inv_atTop_zero.comp vaart1998_sqrt_nat_tendsto_atTop
  have hnorm :
      Tendsto (fun N : ℕ => ‖(Real.sqrt (N : ℝ))⁻¹‖) atTop (𝓝 0) :=
    by simpa using hinv_sqrt_tendsto.norm
  simpa using
    ((hnorm.mul tendsto_const_nhds).mul tendsto_const_nhds :
      Tendsto (fun N : ℕ => ‖(Real.sqrt (N : ℝ))⁻¹‖ * C * B)
        atTop (𝓝 (0 * C * B)))

/-- Norm bound for a single source noise coefficient. -/
theorem chewi123NoiseCoefficient_norm_le_transition
    {E : Type*} [NormedAddCommGroup E] [NormedSpace ℝ E]
    (A : E →L[ℝ] E) (h : ℕ -> ℝ) (k n : ℕ) :
    ‖chewi123NoiseCoefficient A h k n‖ ≤
      ‖h k‖ * ‖chewi123TransitionProductFrom A h k (n - k)‖ := by
  simp [chewi123NoiseCoefficient, norm_smul]

/--
Source noise coefficient norm bounded by any scalar majorant for its summands.
-/
theorem chewi123SourceNoiseCoefficient_norm_le_sum_noise_bound
    {E : Type*} [NormedAddCommGroup E] [NormedSpace ℝ E]
    (A : E →L[ℝ] E) (h : ℕ -> ℝ) (R : ℕ -> ℕ -> ℝ)
    (hR : ∀ k i, ‖chewi123NoiseCoefficient A h k i‖ ≤ R k i)
    (k N : ℕ) :
    ‖chewi123SourceNoiseCoefficient A h k N‖ ≤
      ∑ i ∈ Finset.Ico k N, R k i := by
  calc
    ‖chewi123SourceNoiseCoefficient A h k N‖ =
        ‖∑ i ∈ Finset.Ico k N, chewi123NoiseCoefficient A h k i‖ := by
      rfl
    _ ≤ ∑ i ∈ Finset.Ico k N, ‖chewi123NoiseCoefficient A h k i‖ := by
      exact norm_sum_le (s := Finset.Ico k N)
        (f := fun i => chewi123NoiseCoefficient A h k i)
    _ ≤ ∑ i ∈ Finset.Ico k N, R k i :=
      Finset.sum_le_sum fun i _hi => hR k i

/--
One-step transition telescope for the quadratic ASGD product:
`B_r - B_{r+1} = h_{k+r+1} A B_r`.
-/
theorem chewi123TransitionProductFrom_sub_succ_eq_smul_A_mul
    {E : Type*} [NormedAddCommGroup E] [NormedSpace ℝ E]
    (A : E →L[ℝ] E) (h : ℕ -> ℝ) (start len : ℕ) :
    chewi123TransitionProductFrom A h start len -
        chewi123TransitionProductFrom A h start (len + 1) =
      h (start + len + 1) •
        (A * chewi123TransitionProductFrom A h start len) := by
  simp [chewi123TransitionProductFrom, chewi123QuadraticStepMap, sub_mul]
  rw [show ContinuousLinearMap.id ℝ E *
      chewi123TransitionProductFrom A h start len =
        chewi123TransitionProductFrom A h start len by
    ext x
    rfl]
  abel

/--
Finite transition-product telescope behind Chewi Lemma 12.5:
the weighted `A B_r` sum is `I - B_len`.
-/
theorem chewi123TransitionProductFrom_weighted_sum_eq_id_sub
    {E : Type*} [NormedAddCommGroup E] [NormedSpace ℝ E]
    (A : E →L[ℝ] E) (h : ℕ -> ℝ) (start len : ℕ) :
    (∑ r ∈ Finset.range len,
        h (start + r + 1) •
          (A * chewi123TransitionProductFrom A h start r)) =
      1 - chewi123TransitionProductFrom A h start len := by
  have htelescope :
      (∑ r ∈ Finset.range len,
        (chewi123TransitionProductFrom A h start r -
          chewi123TransitionProductFrom A h start (r + 1))) =
        chewi123TransitionProductFrom A h start 0 -
          chewi123TransitionProductFrom A h start len := by
    simpa [Finset.sum_sub_distrib, sub_eq_add_neg, add_comm, add_left_comm] using
      (Finset.sum_range_sub
        (fun r => -chewi123TransitionProductFrom A h start r) len)
  change (∑ r ∈ Finset.range len,
        h (start + r + 1) •
          (A * chewi123TransitionProductFrom A h start r)) =
      chewi123TransitionProductFrom A h start 0 -
        chewi123TransitionProductFrom A h start len
  rw [← htelescope]
  refine Finset.sum_congr rfl ?_
  intro r _hr
  exact (chewi123TransitionProductFrom_sub_succ_eq_smul_A_mul A h start r).symm

/--
Left-inverse version of the transition telescope:
if `Ainv * A = 1`, then the weighted transition sum is
`Ainv * (I - B_len)`.
-/
theorem chewi123TransitionProductFrom_weighted_sum_eq_left_inv_id_sub
    {E : Type*} [NormedAddCommGroup E] [NormedSpace ℝ E]
    (A Ainv : E →L[ℝ] E) (h : ℕ -> ℝ) (start len : ℕ)
    (hleft : Ainv * A = 1) :
    (∑ r ∈ Finset.range len,
        h (start + r + 1) •
          chewi123TransitionProductFrom A h start r) =
      Ainv * (1 - chewi123TransitionProductFrom A h start len) := by
  have htel := chewi123TransitionProductFrom_weighted_sum_eq_id_sub A h start len
  calc
    (∑ r ∈ Finset.range len,
        h (start + r + 1) •
          chewi123TransitionProductFrom A h start r)
        =
      Ainv * (∑ r ∈ Finset.range len,
        h (start + r + 1) •
          (A * chewi123TransitionProductFrom A h start r)) := by
          rw [Finset.mul_sum]
          refine Finset.sum_congr rfl ?_
          intro r _hr
          rw [mul_smul_comm]
          congr 1
          rw [← mul_assoc, hleft, one_mul]
    _ = Ainv * (1 - chewi123TransitionProductFrom A h start len) := by
          rw [htel]

/--
Exact residual-row identity for Chewi Lemma 12.5, in zero-based `range` form.
It turns `M_k^N - A^{-1}` into the step-difference transition sum plus the
terminal transition product.
-/
theorem chewi123SourceNoiseCoefficient_sub_left_inv_eq_range
    {E : Type*} [NormedAddCommGroup E] [NormedSpace ℝ E]
    (A Ainv : E →L[ℝ] E) (h : ℕ -> ℝ) (k N : ℕ)
    (hleft : Ainv * A = 1) :
    chewi123SourceNoiseCoefficient A h k N - Ainv =
      (∑ r ∈ Finset.range (N - k),
        (h k - h (k + r + 1)) •
          chewi123TransitionProductFrom A h k r) -
        Ainv * chewi123TransitionProductFrom A h k (N - k) := by
  have hsource :
      chewi123SourceNoiseCoefficient A h k N =
        ∑ r ∈ Finset.range (N - k),
          h k • chewi123TransitionProductFrom A h k r := by
    rw [chewi123SourceNoiseCoefficient, Finset.sum_Ico_eq_sum_range]
    refine Finset.sum_congr rfl ?_
    intro r _hr
    simp [chewi123NoiseCoefficient]
  have hsplit :
      (∑ r ∈ Finset.range (N - k),
          h k • chewi123TransitionProductFrom A h k r) =
        (∑ r ∈ Finset.range (N - k),
          (h k - h (k + r + 1)) •
            chewi123TransitionProductFrom A h k r) +
        (∑ r ∈ Finset.range (N - k),
          h (k + r + 1) •
            chewi123TransitionProductFrom A h k r) := by
    rw [← Finset.sum_add_distrib]
    refine Finset.sum_congr rfl ?_
    intro r _hr
    rw [← add_smul]
    congr 1
    ring
  have hAinv :=
    chewi123TransitionProductFrom_weighted_sum_eq_left_inv_id_sub
      A Ainv h k (N - k) hleft
  calc
    chewi123SourceNoiseCoefficient A h k N - Ainv =
        (∑ r ∈ Finset.range (N - k),
          h k • chewi123TransitionProductFrom A h k r) - Ainv := by
          rw [hsource]
    _ =
        ((∑ r ∈ Finset.range (N - k),
          (h k - h (k + r + 1)) •
            chewi123TransitionProductFrom A h k r) +
        (∑ r ∈ Finset.range (N - k),
          h (k + r + 1) •
            chewi123TransitionProductFrom A h k r)) - Ainv := by
          rw [hsplit]
    _ =
        ((∑ r ∈ Finset.range (N - k),
          (h k - h (k + r + 1)) •
            chewi123TransitionProductFrom A h k r) +
        Ainv * (1 - chewi123TransitionProductFrom A h k (N - k))) - Ainv := by
          rw [hAinv]
    _ =
        (∑ r ∈ Finset.range (N - k),
          (h k - h (k + r + 1)) •
            chewi123TransitionProductFrom A h k r) -
        Ainv * chewi123TransitionProductFrom A h k (N - k) := by
          rw [mul_sub, mul_one]
          abel

/--
Norm form of the residual-row identity, indexed by `range (N-k)`.
-/
theorem chewi123SourceNoiseCoefficient_sub_left_inv_norm_le_range
    {E : Type*} [NormedAddCommGroup E] [NormedSpace ℝ E]
    (A Ainv : E →L[ℝ] E) (h : ℕ -> ℝ) (k N : ℕ)
    (hleft : Ainv * A = 1) :
    ‖chewi123SourceNoiseCoefficient A h k N - Ainv‖ ≤
      (∑ r ∈ Finset.range (N - k),
        ‖h k - h (k + r + 1)‖ *
          ‖chewi123TransitionProductFrom A h k r‖) +
        ‖Ainv‖ * ‖chewi123TransitionProductFrom A h k (N - k)‖ := by
  rw [chewi123SourceNoiseCoefficient_sub_left_inv_eq_range A Ainv h k N hleft]
  have hsum :
      ‖∑ r ∈ Finset.range (N - k),
          (h k - h (k + r + 1)) •
            chewi123TransitionProductFrom A h k r‖ ≤
        ∑ r ∈ Finset.range (N - k),
          ‖h k - h (k + r + 1)‖ *
            ‖chewi123TransitionProductFrom A h k r‖ := by
    calc
      ‖∑ r ∈ Finset.range (N - k),
          (h k - h (k + r + 1)) •
            chewi123TransitionProductFrom A h k r‖
          ≤ ∑ r ∈ Finset.range (N - k),
              ‖(h k - h (k + r + 1)) •
                chewi123TransitionProductFrom A h k r‖ := by
            exact norm_sum_le (s := Finset.range (N - k))
              (f := fun r =>
                (h k - h (k + r + 1)) •
                  chewi123TransitionProductFrom A h k r)
      _ = ∑ r ∈ Finset.range (N - k),
          ‖h k - h (k + r + 1)‖ *
            ‖chewi123TransitionProductFrom A h k r‖ := by
            refine Finset.sum_congr rfl ?_
            intro r _hr
            simp [norm_smul]
  have hterminal :
      ‖Ainv * chewi123TransitionProductFrom A h k (N - k)‖ ≤
        ‖Ainv‖ * ‖chewi123TransitionProductFrom A h k (N - k)‖ :=
    norm_mul_le _ _
  exact (norm_sub_le _ _).trans (add_le_add hsum hterminal)

/--
Source-indexed residual-row norm bound for Chewi Lemma 12.5.
-/
theorem chewi123SourceNoiseCoefficient_sub_left_inv_norm_le_Ico
    {E : Type*} [NormedAddCommGroup E] [NormedSpace ℝ E]
    (A Ainv : E →L[ℝ] E) (h : ℕ -> ℝ) (k N : ℕ)
    (hleft : Ainv * A = 1) :
    ‖chewi123SourceNoiseCoefficient A h k N - Ainv‖ ≤
      (∑ i ∈ Finset.Ico k N,
        ‖h k - h (i + 1)‖ *
          ‖chewi123TransitionProductFrom A h k (i - k)‖) +
        ‖Ainv‖ * ‖chewi123TransitionProductFrom A h k (N - k)‖ := by
  have hrange :=
    chewi123SourceNoiseCoefficient_sub_left_inv_norm_le_range
      A Ainv h k N hleft
  simpa [Finset.sum_Ico_eq_sum_range] using hrange

/--
Adapter from a scalar residual-row majorant to the exact deterministic
coefficient-decay hypothesis used for the endpoint-corrected ASGD remainder.
-/
theorem chewi123ASGDEndpointCorrectedRemainder_coeff_decay_of_residual_row_bound
    {E : Type*} [NormedAddCommGroup E] [NormedSpace ℝ E]
    (A Ainv : E →L[ℝ] E) (h : ℕ -> ℝ) (B : ℝ)
    (R : ℕ -> ℕ -> ℝ) (hB : 0 ≤ B)
    (hres : ∀ N k, k ∈ Finset.Ico 1 N ->
      ‖chewi123SourceNoiseCoefficient A h k N - Ainv‖ ≤ R N k)
    (hdecay :
      Tendsto
        (fun N : ℕ =>
          ‖(Real.sqrt (N : ℝ))⁻¹‖ * ‖Ainv‖ * B +
            ‖(Real.sqrt (N : ℝ))⁻¹‖ *
              ∑ k ∈ Finset.Ico 1 N, R N k * B)
        atTop (𝓝 0)) :
    Tendsto
      (fun N : ℕ =>
        ‖(Real.sqrt (N : ℝ))⁻¹‖ * ‖Ainv‖ * B +
          ‖(Real.sqrt (N : ℝ))⁻¹‖ *
            ∑ k ∈ Finset.Ico 1 N,
              ‖chewi123SourceNoiseCoefficient A h k N - Ainv‖ * B)
      atTop (𝓝 0) := by
  refine tendsto_of_tendsto_of_tendsto_of_le_of_le tendsto_const_nhds hdecay
    ?_ ?_
  · intro N
    exact add_nonneg
      (mul_nonneg (mul_nonneg (norm_nonneg _) (norm_nonneg _)) hB)
      (mul_nonneg (norm_nonneg _)
        (Finset.sum_nonneg fun _k _hk =>
          mul_nonneg (norm_nonneg _) hB))
  · intro N
    have hsum :
        (∑ k ∈ Finset.Ico 1 N,
              ‖chewi123SourceNoiseCoefficient A h k N - Ainv‖ * B) ≤
          ∑ k ∈ Finset.Ico 1 N, R N k * B :=
      Finset.sum_le_sum fun k hk =>
        mul_le_mul_of_nonneg_right (hres N k hk) hB
    exact add_le_add le_rfl
      (mul_le_mul_of_nonneg_left hsum
        (norm_nonneg ((Real.sqrt (N : ℝ))⁻¹)))

/--
Source-row residual majorant for Chewi Lemma 12.5.  The V121 residual identity
reduces `M_k^N - A^{-1}` to the step-difference row and terminal product; the
localized transition-product bound turns both product norms into the source
exponential kernels.
-/
theorem chewi125SourceNoiseCoefficient_sub_left_inv_norm_le_exp_rows
    {E : Type*} [NormedAddCommGroup E] [NormedSpace ℝ E]
    (A Ainv : E →L[ℝ] E) {alpha gamma : ℝ}
    (hleft : Ainv * A = 1)
    (hstep : ∀ m, 2 ≤ m ->
      ‖chewi123QuadraticStepMap (chewi125PowerStep gamma m) A‖ ≤
        1 - alpha * chewi125PowerStep gamma m)
    (hsmall : ∀ m, 2 ≤ m ->
      0 ≤ 1 - alpha * chewi125PowerStep gamma m)
    {N k : ℕ} (hk : k ∈ Finset.Ico 1 N) :
    ‖chewi123SourceNoiseCoefficient A (chewi125PowerStep gamma) k N - Ainv‖ ≤
      (∑ j ∈ Finset.Ico k N,
        ‖chewi125PowerStep gamma k - chewi125PowerStep gamma (j + 1)‖ *
          Real.exp (-alpha *
            ∑ l ∈ Finset.Ico (k + 1) (j + 1),
              chewi125PowerStep gamma l)) +
        ‖Ainv‖ *
          Real.exp (-alpha *
            ∑ l ∈ Finset.Ico (k + 1) (N + 1),
              chewi125PowerStep gamma l) := by
  have hk_mem : 1 ≤ k ∧ k < N := by
    simpa [Finset.mem_Ico] using hk
  have hk2 : 2 ≤ k + 1 := by omega
  have hbase :=
    chewi123SourceNoiseCoefficient_sub_left_inv_norm_le_Ico
      A Ainv (chewi125PowerStep gamma) k N hleft
  refine hbase.trans ?_
  refine add_le_add ?_ ?_
  · refine Finset.sum_le_sum ?_
    intro j hj
    have hj_mem : k ≤ j ∧ j < N := by
      simpa [Finset.mem_Ico] using hj
    have htp :=
      chewi125_transitionProduct_norm_le_exp_sum
        (A := A) (alpha := alpha) (gamma := gamma) (N0 := 2)
        (k := k) (j := j) hstep hsmall hk2 hj_mem.1
    exact mul_le_mul_of_nonneg_left htp (norm_nonneg _)
  · have htp :=
      chewi125_transitionProduct_norm_le_exp_sum
        (A := A) (alpha := alpha) (gamma := gamma) (N0 := 2)
        (k := k) (j := N) hstep hsmall hk2 (le_of_lt hk_mem.2)
    exact mul_le_mul_of_nonneg_left htp (norm_nonneg _)

/--
Named scalar majorant for the Chewi Lemma 12.5 residual coefficient row.  It
packages the step-difference row and terminal transition-product row appearing
in the source proof so downstream ASGD wrappers can use it as the `R` input.
-/
noncomputable def chewi125ResidualCoefficientExpMajorant
    {E : Type*} [NormedAddCommGroup E] [NormedSpace ℝ E]
    (Ainv : E →L[ℝ] E) (alpha gamma : ℝ) (N k : ℕ) : ℝ :=
  (∑ j ∈ Finset.Ico k N,
    ‖chewi125PowerStep gamma k - chewi125PowerStep gamma (j + 1)‖ *
      Real.exp (-alpha *
        ∑ l ∈ Finset.Ico (k + 1) (j + 1),
          chewi125PowerStep gamma l)) +
    ‖Ainv‖ *
      Real.exp (-alpha *
        ∑ l ∈ Finset.Ico (k + 1) (N + 1),
          chewi125PowerStep gamma l)

/-- The source-shaped residual coefficient majorant is nonnegative. -/
theorem chewi125ResidualCoefficientExpMajorant_nonneg
    {E : Type*} [NormedAddCommGroup E] [NormedSpace ℝ E]
    (Ainv : E →L[ℝ] E) (alpha gamma : ℝ) (N k : ℕ) :
    0 ≤ chewi125ResidualCoefficientExpMajorant Ainv alpha gamma N k := by
  dsimp [chewi125ResidualCoefficientExpMajorant]
  exact add_nonneg
    (Finset.sum_nonneg fun _j _hj =>
      mul_nonneg (abs_nonneg _) (le_of_lt (Real.exp_pos _)))
    (mul_nonneg (norm_nonneg _) (le_of_lt (Real.exp_pos _)))

/--
The named majorant bounds the residual source coefficient whenever the
localized transition products satisfy Chewi's contraction estimates.
-/
theorem chewi125SourceNoiseCoefficient_sub_left_inv_norm_le_exp_majorant
    {E : Type*} [NormedAddCommGroup E] [NormedSpace ℝ E]
    (A Ainv : E →L[ℝ] E) {alpha gamma : ℝ}
    (hleft : Ainv * A = 1)
    (hstep : ∀ m, 2 ≤ m ->
      ‖chewi123QuadraticStepMap (chewi125PowerStep gamma m) A‖ ≤
        1 - alpha * chewi125PowerStep gamma m)
    (hsmall : ∀ m, 2 ≤ m ->
      0 ≤ 1 - alpha * chewi125PowerStep gamma m)
    {N k : ℕ} (hk : k ∈ Finset.Ico 1 N) :
    ‖chewi123SourceNoiseCoefficient A (chewi125PowerStep gamma) k N - Ainv‖ ≤
      chewi125ResidualCoefficientExpMajorant Ainv alpha gamma N k := by
  simpa [chewi125ResidualCoefficientExpMajorant] using
    (chewi125SourceNoiseCoefficient_sub_left_inv_norm_le_exp_rows
      A Ainv hleft hstep hsmall hk)

/--
The named residual-coefficient majorant has vanishing `1 / N` average under
Chewi's power-step assumptions.  This is the deterministic scalar half of the
source residual route; a separate uniform cap supplies the L2 diagonal bound.
-/
theorem chewi125ResidualCoefficientExpMajorant_average_tendsto_zero
    {E : Type*} [NormedAddCommGroup E] [NormedSpace ℝ E]
    (Ainv : E →L[ℝ] E) {alpha gamma : ℝ}
    (halpha : 0 < alpha) (hgamma_pos : 0 < gamma) (hgamma_lt : gamma < 1) :
    Tendsto
      (fun N : ℕ =>
        (N : ℝ)⁻¹ *
          ∑ k ∈ Finset.Ico 1 N,
            chewi125ResidualCoefficientExpMajorant Ainv alpha gamma N k)
      atTop (𝓝 0) := by
  let D : ℕ -> ℝ := fun N =>
    ∑ k ∈ Finset.Ico 1 N,
      ∑ j ∈ Finset.Ico k N,
        ‖chewi125PowerStep gamma k - chewi125PowerStep gamma (j + 1)‖ *
          Real.exp (-alpha *
            ∑ l ∈ Finset.Ico (k + 1) (j + 1),
              chewi125PowerStep gamma l)
  let T : ℕ -> ℝ := fun N =>
    ∑ k ∈ Finset.Ico 1 N,
      Real.exp (-alpha *
        ∑ l ∈ Finset.Ico (k + 1) (N + 1),
          chewi125PowerStep gamma l)
  have hD :
      Tendsto (fun N : ℕ => (N : ℝ)⁻¹ * D N) atTop (𝓝 0) := by
    simpa [D] using
      (chewi125_stepdiff_exp_double_average_tendsto_zero
        (alpha := alpha) (gamma := gamma) halpha hgamma_pos hgamma_lt)
  have hT :
      Tendsto (fun N : ℕ => (N : ℝ)⁻¹ * T N) atTop (𝓝 0) := by
    simpa [T] using
      (chewi125_exp_tail_average_tendsto_zero
        (alpha := alpha) (gamma := gamma) halpha hgamma_pos.le hgamma_lt)
  have hupper_tendsto :
      Tendsto (fun N : ℕ => (N : ℝ)⁻¹ * (D N + ‖Ainv‖ * T N))
        atTop (𝓝 0) := by
    have hscaledT :
        Tendsto (fun N : ℕ => ‖Ainv‖ * ((N : ℝ)⁻¹ * T N))
          atTop (𝓝 (‖Ainv‖ * 0)) :=
      tendsto_const_nhds.mul hT
    have hsum :
        Tendsto (fun N : ℕ =>
            (N : ℝ)⁻¹ * D N + ‖Ainv‖ * ((N : ℝ)⁻¹ * T N))
          atTop (𝓝 (0 + ‖Ainv‖ * 0)) :=
      hD.add hscaledT
    have hsum0 :
        Tendsto (fun N : ℕ =>
            (N : ℝ)⁻¹ * D N + ‖Ainv‖ * ((N : ℝ)⁻¹ * T N))
          atTop (𝓝 0) := by
      simpa using hsum
    refine hsum0.congr' ?_
    exact Eventually.of_forall fun N => by ring
  refine hupper_tendsto.congr' ?_
  exact Eventually.of_forall fun N => by
    simp [D, T, chewi125ResidualCoefficientExpMajorant,
      Finset.sum_add_distrib, Finset.mul_sum]

/-- Uniform constant for the source-shaped residual coefficient majorant. -/
noncomputable def chewi125ResidualCoefficientUniformConstant
    {E : Type*} [NormedAddCommGroup E] [NormedSpace ℝ E]
    (Ainv : E →L[ℝ] E) (alpha gamma : ℝ) : ℝ :=
  (gamma * (Real.exp alpha / alpha ^ 2 + Real.exp alpha / alpha) *
      (2 : ℝ) ^ (2 * gamma)) +
    gamma *
      (∑' d : ℕ,
        ((d : ℝ) + 1) *
          Real.exp (-(alpha * (2 : ℝ) ^ (-gamma) *
            ((d : ℝ) ^ (1 - gamma))))) +
    ‖Ainv‖

/--
One residual step-difference row is bounded by the reindexed
derivative-geometric row used in the near/far split.
-/
theorem chewi125_stepdiff_exp_row_le_deriv_geometric {alpha gamma : ℝ}
    (halpha : 0 < alpha) (hgamma_nonneg : 0 ≤ gamma)
    {N k : ℕ} (hk : k ∈ Finset.Ico 1 N) :
    (∑ j ∈ Finset.Ico k N,
        ‖chewi125PowerStep gamma k - chewi125PowerStep gamma (j + 1)‖ *
          Real.exp (-alpha *
            ∑ l ∈ Finset.Ico (k + 1) (j + 1),
              chewi125PowerStep gamma l)) ≤
      ∑ j ∈ Finset.Ico k N,
        ((gamma * (k : ℝ) ^ (-gamma - 1)) *
            ‖((j + 1 : ℕ) : ℝ) - (k : ℝ)‖) *
          Real.exp (-(alpha * (j : ℝ) ^ (-gamma)) *
            ((j - k : ℕ) : ℝ)) := by
  refine Finset.sum_le_sum ?_
  intro j hj
  have hk_mem : 1 ≤ k ∧ k < N := by
    simpa [Finset.mem_Ico] using hk
  have hj_mem : k ≤ j ∧ j < N := by
    simpa [Finset.mem_Ico] using hj
  have hexp :=
    chewi125_stepdiff_exp_term_le_geometric
      (alpha := alpha) (gamma := gamma) halpha hgamma_nonneg k j
  have hdiff :=
    chewi125PowerStep_norm_sub_le_deriv hgamma_nonneg
      (k := k) (j := j) hk_mem.1 (by omega)
  calc
    ‖chewi125PowerStep gamma k - chewi125PowerStep gamma (j + 1)‖ *
        Real.exp (-alpha *
          ∑ l ∈ Finset.Ico (k + 1) (j + 1),
            chewi125PowerStep gamma l)
      ≤
        ‖chewi125PowerStep gamma k - chewi125PowerStep gamma (j + 1)‖ *
          Real.exp (-(alpha * (j : ℝ) ^ (-gamma)) *
            ((j - k : ℕ) : ℝ)) :=
          mul_le_mul_of_nonneg_left hexp (norm_nonneg _)
    _ ≤
        ((gamma * (k : ℝ) ^ (-gamma - 1)) *
            ‖((j + 1 : ℕ) : ℝ) - (k : ℝ)‖) *
          Real.exp (-(alpha * (j : ℝ) ^ (-gamma)) *
            ((j - k : ℕ) : ℝ)) :=
          mul_le_mul_of_nonneg_right hdiff (le_of_lt (Real.exp_pos _))

/--
Near/far source row bound for the residual coefficient step-difference
component.
-/
theorem chewi125_stepdiff_exp_row_le_near_far_bound {alpha gamma : ℝ}
    (halpha : 0 < alpha) (hgamma_pos : 0 < gamma) (hgamma_lt : gamma < 1)
    {N k : ℕ} (hk : k ∈ Finset.Ico 1 N) :
    (∑ j ∈ Finset.Ico k N,
        ‖chewi125PowerStep gamma k - chewi125PowerStep gamma (j + 1)‖ *
          Real.exp (-alpha *
            ∑ l ∈ Finset.Ico (k + 1) (j + 1),
              chewi125PowerStep gamma l)) ≤
      (gamma * (Real.exp alpha / alpha ^ 2 + Real.exp alpha / alpha) *
          (2 : ℝ) ^ (2 * gamma)) *
        (k : ℝ) ^ (gamma - 1) +
      (gamma * (k : ℝ) ^ (-gamma - 1)) *
        (∑' d : ℕ,
          ((d : ℝ) + 1) *
            Real.exp (-(alpha * (2 : ℝ) ^ (-gamma) *
              ((d : ℝ) ^ (1 - gamma))))) := by
  have hk_mem : 1 ≤ k ∧ k < N := by
    simpa [Finset.mem_Ico] using hk
  have hrow :=
    chewi125_stepdiff_exp_row_le_deriv_geometric
      (alpha := alpha) (gamma := gamma) halpha hgamma_pos.le hk
  have hsplit :=
    chewi125_deriv_geometric_reindexed_row_le_near_far_sums
      (alpha := alpha) (gamma := gamma) hgamma_pos.le k (N - k) (N - k)
      (le_rfl)
  have hnear :=
    chewi125_near_stepdiff_row_true_le_outer_power
      (alpha := alpha) (gamma := gamma) halpha hgamma_pos.le
      (k := k) hk_mem.1
  have hfar :=
    chewi125_far_stepdiff_row_true_le_stretched_tsum
      (alpha := alpha) (gamma := gamma) halpha hgamma_pos.le hgamma_lt
      (k := k) (M := N - k) hk_mem.1
  calc
    (∑ j ∈ Finset.Ico k N,
        ‖chewi125PowerStep gamma k - chewi125PowerStep gamma (j + 1)‖ *
          Real.exp (-alpha *
            ∑ l ∈ Finset.Ico (k + 1) (j + 1),
              chewi125PowerStep gamma l))
      ≤
        ∑ j ∈ Finset.Ico k N,
          ((gamma * (k : ℝ) ^ (-gamma - 1)) *
              ‖((j + 1 : ℕ) : ℝ) - (k : ℝ)‖) *
            Real.exp (-(alpha * (j : ℝ) ^ (-gamma)) *
              ((j - k : ℕ) : ℝ)) := hrow
    _ =
        ∑ d ∈ Finset.Ico 0 (N - k),
          chewi125StepdiffDerivativeKernel alpha gamma k d := by
          exact chewi125_deriv_geometric_row_reindex
            (alpha := alpha) (gamma := gamma) k N
    _ ≤
        (∑ d ∈ Finset.Ico 0 (k + 1),
          chewi125StepdiffDerivativeKernel alpha gamma k d) +
          ∑ d ∈ Finset.Ico (k + 1) (N - k),
            chewi125StepdiffDerivativeKernel alpha gamma k d := hsplit
    _ ≤
        (gamma * (Real.exp alpha / alpha ^ 2 + Real.exp alpha / alpha) *
            (2 : ℝ) ^ (2 * gamma)) *
          (k : ℝ) ^ (gamma - 1) +
        (gamma * (k : ℝ) ^ (-gamma - 1)) *
          (∑' d : ℕ,
            ((d : ℝ) + 1) *
              Real.exp (-(alpha * (2 : ℝ) ^ (-gamma) *
                ((d : ℝ) ^ (1 - gamma))))) :=
          add_le_add hnear hfar

/-- Uniform source row bound for the step-difference residual component. -/
theorem chewi125_stepdiff_exp_row_le_uniform_constant {alpha gamma : ℝ}
    (halpha : 0 < alpha) (hgamma_pos : 0 < gamma) (hgamma_lt : gamma < 1)
    {N k : ℕ} (hk : k ∈ Finset.Ico 1 N) :
    (∑ j ∈ Finset.Ico k N,
        ‖chewi125PowerStep gamma k - chewi125PowerStep gamma (j + 1)‖ *
          Real.exp (-alpha *
            ∑ l ∈ Finset.Ico (k + 1) (j + 1),
              chewi125PowerStep gamma l)) ≤
      (gamma * (Real.exp alpha / alpha ^ 2 + Real.exp alpha / alpha) *
          (2 : ℝ) ^ (2 * gamma)) +
      gamma *
        (∑' d : ℕ,
          ((d : ℝ) + 1) *
            Real.exp (-(alpha * (2 : ℝ) ^ (-gamma) *
              ((d : ℝ) ^ (1 - gamma))))) := by
  let Cnear : ℝ :=
    gamma * (Real.exp alpha / alpha ^ 2 + Real.exp alpha / alpha) *
      (2 : ℝ) ^ (2 * gamma)
  let Dfar : ℝ :=
    ∑' d : ℕ,
      ((d : ℝ) + 1) *
        Real.exp (-(alpha * (2 : ℝ) ^ (-gamma) *
          ((d : ℝ) ^ (1 - gamma))))
  have hk_mem : 1 ≤ k ∧ k < N := by
    simpa [Finset.mem_Ico] using hk
  have hrow :=
    chewi125_stepdiff_exp_row_le_near_far_bound
      (alpha := alpha) (gamma := gamma) halpha hgamma_pos hgamma_lt hk
  have hCnear_nonneg : 0 ≤ Cnear := by
    dsimp [Cnear]
    positivity
  have hDfar_nonneg : 0 ≤ Dfar := by
    dsimp [Dfar]
    exact tsum_nonneg fun d => by positivity
  have hnear_pow :
      (k : ℝ) ^ (gamma - 1) ≤ 1 :=
    Real.rpow_le_one_of_one_le_of_nonpos
      (Nat.one_le_cast.mpr hk_mem.1) (by linarith)
  have hfar_pow :
      (k : ℝ) ^ (-gamma - 1) ≤ 1 :=
    Real.rpow_le_one_of_one_le_of_nonpos
      (Nat.one_le_cast.mpr hk_mem.1) (by linarith)
  have hnear :
      Cnear * (k : ℝ) ^ (gamma - 1) ≤ Cnear := by
    calc
      Cnear * (k : ℝ) ^ (gamma - 1) ≤ Cnear * 1 :=
        mul_le_mul_of_nonneg_left hnear_pow hCnear_nonneg
      _ = Cnear := by ring
  have hfar :
      (gamma * (k : ℝ) ^ (-gamma - 1)) * Dfar ≤ gamma * Dfar := by
    calc
      (gamma * (k : ℝ) ^ (-gamma - 1)) * Dfar =
          (gamma * Dfar) * (k : ℝ) ^ (-gamma - 1) := by ring
      _ ≤ (gamma * Dfar) * 1 :=
          mul_le_mul_of_nonneg_left hfar_pow
            (mul_nonneg hgamma_pos.le hDfar_nonneg)
      _ = gamma * Dfar := by ring
  calc
    (∑ j ∈ Finset.Ico k N,
        ‖chewi125PowerStep gamma k - chewi125PowerStep gamma (j + 1)‖ *
          Real.exp (-alpha *
            ∑ l ∈ Finset.Ico (k + 1) (j + 1),
              chewi125PowerStep gamma l))
      ≤ Cnear * (k : ℝ) ^ (gamma - 1) +
          (gamma * (k : ℝ) ^ (-gamma - 1)) * Dfar := by
          simpa [Cnear, Dfar] using hrow
    _ ≤ Cnear + gamma * Dfar := add_le_add hnear hfar
    _ =
        (gamma * (Real.exp alpha / alpha ^ 2 + Real.exp alpha / alpha) *
            (2 : ℝ) ^ (2 * gamma)) +
        gamma *
          (∑' d : ℕ,
            ((d : ℝ) + 1) *
              Real.exp (-(alpha * (2 : ℝ) ^ (-gamma) *
                ((d : ℝ) ^ (1 - gamma))))) := by
          simp [Cnear, Dfar]

/-- The source-shaped residual coefficient majorant is uniformly bounded. -/
theorem chewi125ResidualCoefficientExpMajorant_le_uniform_constant
    {E : Type*} [NormedAddCommGroup E] [NormedSpace ℝ E]
    (Ainv : E →L[ℝ] E) {alpha gamma : ℝ}
    (halpha : 0 < alpha) (hgamma_pos : 0 < gamma) (hgamma_lt : gamma < 1)
    {N k : ℕ} (hk : k ∈ Finset.Ico 1 N) :
    chewi125ResidualCoefficientExpMajorant Ainv alpha gamma N k ≤
      chewi125ResidualCoefficientUniformConstant Ainv alpha gamma := by
  have hk_mem : 1 ≤ k ∧ k < N := by
    simpa [Finset.mem_Ico] using hk
  have hrow :=
    chewi125_stepdiff_exp_row_le_uniform_constant
      (alpha := alpha) (gamma := gamma) halpha hgamma_pos hgamma_lt hk
  have htail_nonneg :
      0 ≤
        ∑ l ∈ Finset.Ico (k + 1) (N + 1),
          chewi125PowerStep gamma l := by
    refine Finset.sum_nonneg ?_
    intro l hl
    have hl_mem : k + 1 ≤ l ∧ l < N + 1 := by
      simpa [Finset.mem_Ico] using hl
    exact le_of_lt (chewi125PowerStep_pos gamma (by omega))
  have hexp_le_one :
      Real.exp (-alpha *
        ∑ l ∈ Finset.Ico (k + 1) (N + 1),
          chewi125PowerStep gamma l) ≤ 1 := by
    have hmul :
        0 ≤ alpha *
          ∑ l ∈ Finset.Ico (k + 1) (N + 1),
            chewi125PowerStep gamma l :=
      mul_nonneg halpha.le htail_nonneg
    have harg :
        -alpha *
          ∑ l ∈ Finset.Ico (k + 1) (N + 1),
            chewi125PowerStep gamma l ≤ 0 := by
      linarith
    have := Real.exp_le_exp.mpr harg
    simpa using this
  have hterminal :
      ‖Ainv‖ *
        Real.exp (-alpha *
          ∑ l ∈ Finset.Ico (k + 1) (N + 1),
            chewi125PowerStep gamma l) ≤ ‖Ainv‖ := by
    calc
      ‖Ainv‖ *
          Real.exp (-alpha *
            ∑ l ∈ Finset.Ico (k + 1) (N + 1),
              chewi125PowerStep gamma l) ≤ ‖Ainv‖ * 1 :=
            mul_le_mul_of_nonneg_left hexp_le_one (norm_nonneg _)
      _ = ‖Ainv‖ := by ring
  dsimp [chewi125ResidualCoefficientExpMajorant,
    chewi125ResidualCoefficientUniformConstant]
  exact add_le_add hrow hterminal

/-- Uniform bound for the actual source residual coefficient row. -/
theorem chewi125SourceNoiseCoefficient_sub_left_inv_norm_le_uniform_constant
    {E : Type*} [NormedAddCommGroup E] [NormedSpace ℝ E]
    (A Ainv : E →L[ℝ] E) {alpha gamma : ℝ}
    (hleft : Ainv * A = 1)
    (halpha : 0 < alpha) (hgamma_pos : 0 < gamma) (hgamma_lt : gamma < 1)
    (hstep : ∀ m, 2 ≤ m ->
      ‖chewi123QuadraticStepMap (chewi125PowerStep gamma m) A‖ ≤
        1 - alpha * chewi125PowerStep gamma m)
    (hsmall : ∀ m, 2 ≤ m ->
      0 ≤ 1 - alpha * chewi125PowerStep gamma m)
    {N k : ℕ} (hk : k ∈ Finset.Ico 1 N) :
    ‖chewi123SourceNoiseCoefficient A (chewi125PowerStep gamma) k N - Ainv‖ ≤
      chewi125ResidualCoefficientUniformConstant Ainv alpha gamma := by
  exact
    (chewi125SourceNoiseCoefficient_sub_left_inv_norm_le_exp_majorant
      A Ainv hleft hstep hsmall hk).trans
      (chewi125ResidualCoefficientExpMajorant_le_uniform_constant
        Ainv halpha hgamma_pos hgamma_lt hk)

/--
Source-facing Chewi Lemma 12.5 average residual-row convergence for the power
steps `h_n = n^{-γ}`.  This is the exact theorem displayed in the notes:
`(1 / N) * sum_k ||M_k^N - A^{-1}|| -> 0`.  It intentionally proves the
textbook average statement; the later `sqrt N`-scaled stochastic remainder uses
orthogonality rather than this theorem through a triangle inequality.
-/
theorem chewi125SourceNoiseCoefficient_sub_left_inv_average_tendsto_zero
    {E : Type*} [NormedAddCommGroup E] [NormedSpace ℝ E]
    (A Ainv : E →L[ℝ] E) {alpha gamma : ℝ}
    (hleft : Ainv * A = 1)
    (halpha : 0 < alpha) (hgamma_pos : 0 < gamma) (hgamma_lt : gamma < 1)
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
              Ainv‖)
      atTop (𝓝 0) := by
  let D : ℕ -> ℝ := fun N =>
    ∑ k ∈ Finset.Ico 1 N,
      ∑ j ∈ Finset.Ico k N,
        ‖chewi125PowerStep gamma k - chewi125PowerStep gamma (j + 1)‖ *
          Real.exp (-alpha *
            ∑ l ∈ Finset.Ico (k + 1) (j + 1),
              chewi125PowerStep gamma l)
  let T : ℕ -> ℝ := fun N =>
    ∑ k ∈ Finset.Ico 1 N,
      Real.exp (-alpha *
        ∑ l ∈ Finset.Ico (k + 1) (N + 1),
          chewi125PowerStep gamma l)
  have hD :
      Tendsto (fun N : ℕ => (N : ℝ)⁻¹ * D N) atTop (𝓝 0) := by
    simpa [D] using
      (chewi125_stepdiff_exp_double_average_tendsto_zero
        (alpha := alpha) (gamma := gamma) halpha hgamma_pos hgamma_lt)
  have hT :
      Tendsto (fun N : ℕ => (N : ℝ)⁻¹ * T N) atTop (𝓝 0) := by
    simpa [T] using
      (chewi125_exp_tail_average_tendsto_zero
        (alpha := alpha) (gamma := gamma) halpha hgamma_pos.le hgamma_lt)
  have hupper_tendsto :
      Tendsto (fun N : ℕ => (N : ℝ)⁻¹ * (D N + ‖Ainv‖ * T N))
        atTop (𝓝 0) := by
    have hscaledT :
        Tendsto (fun N : ℕ => ‖Ainv‖ * ((N : ℝ)⁻¹ * T N))
          atTop (𝓝 (‖Ainv‖ * 0)) :=
      tendsto_const_nhds.mul hT
    have hsum :
        Tendsto (fun N : ℕ =>
            (N : ℝ)⁻¹ * D N + ‖Ainv‖ * ((N : ℝ)⁻¹ * T N))
          atTop (𝓝 (0 + ‖Ainv‖ * 0)) :=
      hD.add hscaledT
    have hsum0 :
        Tendsto (fun N : ℕ =>
            (N : ℝ)⁻¹ * D N + ‖Ainv‖ * ((N : ℝ)⁻¹ * T N))
          atTop (𝓝 0) := by
      simpa using hsum
    refine hsum0.congr' ?_
    exact Eventually.of_forall fun N => by ring
  refine tendsto_of_tendsto_of_tendsto_of_le_of_le' tendsto_const_nhds
    hupper_tendsto ?_ ?_
  · exact Eventually.of_forall fun N =>
      mul_nonneg (inv_nonneg.mpr (Nat.cast_nonneg N))
        (Finset.sum_nonneg fun _k _hk => norm_nonneg _)
  · refine Eventually.of_forall fun N => ?_
    have hsum :
        (∑ k ∈ Finset.Ico 1 N,
            ‖chewi123SourceNoiseCoefficient A (chewi125PowerStep gamma) k N -
              Ainv‖) ≤
          D N + ‖Ainv‖ * T N := by
      calc
        (∑ k ∈ Finset.Ico 1 N,
            ‖chewi123SourceNoiseCoefficient A (chewi125PowerStep gamma) k N -
              Ainv‖)
            ≤ ∑ k ∈ Finset.Ico 1 N,
                ((∑ j ∈ Finset.Ico k N,
                    ‖chewi125PowerStep gamma k -
                        chewi125PowerStep gamma (j + 1)‖ *
                      Real.exp (-alpha *
                        ∑ l ∈ Finset.Ico (k + 1) (j + 1),
                          chewi125PowerStep gamma l)) +
                  ‖Ainv‖ *
                    Real.exp (-alpha *
                      ∑ l ∈ Finset.Ico (k + 1) (N + 1),
                        chewi125PowerStep gamma l)) := by
              exact Finset.sum_le_sum fun k hk =>
                chewi125SourceNoiseCoefficient_sub_left_inv_norm_le_exp_rows
                  A Ainv hleft hstep hsmall hk
        _ = D N + ‖Ainv‖ * T N := by
              simp [D, T, Finset.sum_add_distrib, Finset.mul_sum]
    exact mul_le_mul_of_nonneg_left hsum (inv_nonneg.mpr (Nat.cast_nonneg N))

/--
The linear image of the martingale-CLT source sum splits into Chewi's
`Ico 1 N` source sum plus the endpoint correction.
-/
theorem chewi123_Ainv_rangeScaledNoiseSum_eq_sourceSum_add_endpoint
    {E : Type*} [NormedAddCommGroup E] [NormedSpace ℝ E]
    (Ainv : E →L[ℝ] E) (xi : ℕ -> E) {N : ℕ} (hN : N ≠ 0) :
    Ainv (chewi123RangeScaledNoiseSum xi N) =
      (Real.sqrt (N : ℝ))⁻¹ • (∑ k ∈ Finset.Ico 1 N, Ainv (xi k)) +
        (Real.sqrt (N : ℝ))⁻¹ • Ainv (xi N) := by
  rw [chewi123RangeScaledNoiseSum, map_smul, map_sum]
  rw [chewi123_sum_range_succ_eq_sum_Ico_add_endpoint
    (fun k => Ainv (xi k)) hN]
  rw [smul_add]

/--
Endpoint-corrected deterministic form of Chewi's `sqrt N`-scaled quadratic
ASGD source decomposition.
-/
theorem chewi123_quadratic_sqrt_average_delta_endpoint_corrected_decomposition
    {E : Type*} [NormedAddCommGroup E] [NormedSpace ℝ E]
    (A Ainv : E →L[ℝ] E) (h : ℕ -> ℝ) (delta xi : ℕ -> E)
    (hrec : ∀ n,
      delta (n + 1) =
        chewi123QuadraticStepMap (h (n + 1)) A (delta n) -
          h (n + 1) • xi (n + 1))
    (N : ℕ) :
    (-Ainv (chewi123RangeScaledNoiseSum xi N) +
        chewi123ASGDInitialTerm A h (delta 0) N) +
      chewi123ASGDEndpointCorrectedRemainder A Ainv h xi N =
        chewi123ScaledAverageDelta delta N := by
  by_cases hNzero : N = 0
  · subst N
    simp [chewi123RangeScaledNoiseSum, chewi123ASGDInitialTerm,
      chewi123ASGDEndpointCorrectedRemainder, chewi123ScaledAverageDelta]
  · have hNpos_nat : 0 < N := Nat.pos_of_ne_zero hNzero
    have hNpos : 0 < (N : ℝ) := by exact_mod_cast hNpos_nat
    have hsrc :=
      chewi123_quadratic_sqrt_average_delta_source_decomposition
        A Ainv h delta xi hrec N hNpos
    have hnoise :=
      chewi123_Ainv_rangeScaledNoiseSum_eq_sourceSum_add_endpoint
        Ainv xi hNzero
    rw [chewi123ScaledAverageDelta, hsrc]
    rw [chewi123ASGDInitialTerm, chewi123ASGDEndpointCorrectedRemainder]
    rw [hnoise]
    module

/--
Almost-sure endpoint-corrected decomposition for random quadratic ASGD
trajectories.
-/
theorem chewi123_quadratic_sqrt_average_delta_endpoint_corrected_decomposition_ae
    {Ω E : Type*} [MeasurableSpace Ω] {P : Measure Ω}
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    (A Ainv : E →L[ℝ] E) (h : ℕ -> ℝ)
    (delta xi : ℕ -> Ω -> E)
    (hrec : ∀ n ω,
      delta (n + 1) ω =
        chewi123QuadraticStepMap (h (n + 1)) A (delta n ω) -
          h (n + 1) • xi (n + 1) ω)
    (N : ℕ) :
    (fun ω =>
        (-Ainv (chewi127ScaledNoiseSum xi N ω) +
            chewi123ASGDInitialTerm A h (delta 0 ω) N) +
          chewi123ASGDEndpointCorrectedRemainder A Ainv h
            (fun n => xi n ω) N)
      =ᵐ[P]
    (fun ω => chewi123ScaledAverageDelta (fun n => delta n ω) N) := by
  exact ae_of_all _ fun ω => by
    simpa [chewi127ScaledNoiseSum, chewi123RangeScaledNoiseSum] using
      chewi123_quadratic_sqrt_average_delta_endpoint_corrected_decomposition
        A Ainv h (fun n => delta n ω) (fun n => xi n ω)
        (fun n => hrec n ω) N

/--
Chewi Theorem 12.3 package with the deterministic endpoint correction already
absorbed into the supplied `o_P(1)` remainder.
-/
theorem chewi123_asgd_limit_package_of_martingale_certificate_endpoint_corrected
    {Ω Ω' E : Type*} [MeasurableSpace Ω] {P : Measure Ω}
    [IsProbabilityMeasure P] [MeasurableSpace Ω'] {Q : Measure Ω'}
    [IsProbabilityMeasure Q]
    [NormedAddCommGroup E] [NormedSpace ℝ E] [MeasurableSpace E]
    [CompleteSpace E] [SecondCountableTopology E] [BorelSpace E]
    [OpensMeasurableSpace E]
    (C : Chewi127MartingaleCLTCertificate Ω Ω' E P Q)
    (A Ainv : E →L[ℝ] E) (h : ℕ -> ℝ)
    (delta xi : ℕ -> Ω -> E)
    (hNoise_eq : ∀ N, C.noiseScaled N =ᵐ[P] chewi127ScaledNoiseSum xi N)
    (hrec : ∀ n ω,
      delta (n + 1) ω =
        chewi123QuadraticStepMap (h (n + 1)) A (delta n ω) -
          h (n + 1) • xi (n + 1) ω)
    (hInitial : TendstoInMeasure P
      (fun N ω => chewi123ASGDInitialTerm A h (delta 0 ω) N)
      atTop (fun _ => 0))
    (hRemainder : TendstoInMeasure P
      (fun N ω =>
        chewi123ASGDEndpointCorrectedRemainder A Ainv h
          (fun n => xi n ω) N)
      atTop (fun _ => 0))
    (hInitial_meas : ∀ N,
      AEMeasurable (fun ω => chewi123ASGDInitialTerm A h (delta 0 ω) N) P)
    (hRemainder_meas : ∀ N,
      AEMeasurable
        (fun ω =>
          chewi123ASGDEndpointCorrectedRemainder A Ainv h
            (fun n => xi n ω) N) P) :
    TendstoInDistribution
        (fun N ω => chewi123ScaledAverageDelta (fun n => delta n ω) N)
        atTop (fun ω => -Ainv (C.Z ω)) (fun _ => P) Q ∧
      HasGaussianLaw (fun ω => -Ainv (C.Z ω)) Q ∧
      ∀ L K : StrongDual ℝ E,
        ProbabilityTheory.covarianceBilinDual
            (Q.map fun ω => -Ainv (C.Z ω)) L K =
          vaart1998_inverseDerivativeCovarianceFunctional (-Ainv)
            (fun L0 K0 =>
              ProbabilityTheory.covarianceBilinDual (Q.map C.Z) L0 K0) L K := by
  refine
    chewi123_asgd_limit_package_of_martingale_certificate
      (C := C) (Ainv := Ainv)
      (scaledAverage :=
        fun N ω => chewi123ScaledAverageDelta (fun n => delta n ω) N)
      (initial := fun N ω => chewi123ASGDInitialTerm A h (delta 0 ω) N)
      (remainder :=
        fun N ω =>
          chewi123ASGDEndpointCorrectedRemainder A Ainv h
            (fun n => xi n ω) N)
      hInitial hRemainder hInitial_meas hRemainder_meas ?_
  intro N
  filter_upwards
    [hNoise_eq N,
      chewi123_quadratic_sqrt_average_delta_endpoint_corrected_decomposition_ae
        (P := P) A Ainv h delta xi hrec N] with ω hnoise hdecomp
  simpa [hnoise] using hdecomp

/--
Source-facing Chewi Theorem 12.3 package from a bounded martingale CLT source,
with the `(12.5)` endpoint correction already built into the remainder.
-/
theorem Chewi127BoundedMartingaleCLTSource.asgd_limit_package_endpoint_corrected
    {Ω Ω' E : Type*} [mΩ : MeasurableSpace Ω] {P : Measure Ω}
    [IsProbabilityMeasure P] [MeasurableSpace Ω'] {Q : Measure Ω'}
    [IsProbabilityMeasure Q]
    [NormedAddCommGroup E] [NormedSpace ℝ E] [MeasurableSpace E]
    [CompleteSpace E] [SecondCountableTopology E] [BorelSpace E]
    [OpensMeasurableSpace E]
    (S : Chewi127BoundedMartingaleCLTSource Ω Ω' E P Q)
    (A Ainv : E →L[ℝ] E) (h : ℕ -> ℝ)
    (delta : ℕ -> Ω -> E)
    (hrec : ∀ n ω,
      delta (n + 1) ω =
        chewi123QuadraticStepMap (h (n + 1)) A (delta n ω) -
          h (n + 1) • S.martingale.xi (n + 1) ω)
    (hInitial : TendstoInMeasure P
      (fun N ω => chewi123ASGDInitialTerm A h (delta 0 ω) N)
      atTop (fun _ => 0))
    (hRemainder : TendstoInMeasure P
      (fun N ω =>
        chewi123ASGDEndpointCorrectedRemainder A Ainv h
          (fun n => S.martingale.xi n ω) N)
      atTop (fun _ => 0))
    (hInitial_meas : ∀ N,
      AEMeasurable (fun ω => chewi123ASGDInitialTerm A h (delta 0 ω) N) P)
    (hRemainder_meas : ∀ N,
      AEMeasurable
        (fun ω =>
          chewi123ASGDEndpointCorrectedRemainder A Ainv h
            (fun n => S.martingale.xi n ω) N) P) :
    TendstoInDistribution
        (fun N ω => chewi123ScaledAverageDelta (fun n => delta n ω) N)
        atTop (fun ω => -Ainv (S.Z ω)) (fun _ => P) Q ∧
      HasGaussianLaw (fun ω => -Ainv (S.Z ω)) Q ∧
      ∀ L K : StrongDual ℝ E,
        ProbabilityTheory.covarianceBilinDual
            (Q.map fun ω => -Ainv (S.Z ω)) L K =
          vaart1998_inverseDerivativeCovarianceFunctional (-Ainv)
            (fun L0 K0 =>
              ProbabilityTheory.covarianceBilinDual (Q.map S.Z) L0 K0) L K := by
  let C : Chewi127MartingaleCLTCertificate Ω Ω' E P Q :=
    S.toMartingaleCLTCertificate
  simpa [C, Chewi127BoundedMartingaleCLTSource.toMartingaleCLTCertificate,
    Chewi127BoundedMartingaleCLTSource.toProjectedBridge,
    Chewi127ProjectedMartingaleCLTBridge.toMartingaleCLTCertificate] using
    chewi123_asgd_limit_package_of_martingale_certificate_endpoint_corrected
      (C := C) A Ainv h delta S.martingale.xi
      (fun _ => ae_of_all _ fun _ => rfl) hrec
      hInitial hRemainder hInitial_meas hRemainder_meas

/--
Source-conditioned Chewi Theorem 12.3 package from a bounded martingale CLT
source.  The two `o_P(1)` side conditions are discharged from deterministic
coefficient decay, a bounded initial error, and uniformly bounded noise.
-/
theorem Chewi127BoundedMartingaleCLTSource.asgd_limit_package_endpoint_corrected_of_bounded_initial_uniform_noise_and_coeff_decay
    {Ω Ω' E : Type*} [mΩ : MeasurableSpace Ω] {P : Measure Ω}
    [IsProbabilityMeasure P] [MeasurableSpace Ω'] {Q : Measure Ω'}
    [IsProbabilityMeasure Q]
    [NormedAddCommGroup E] [NormedSpace ℝ E] [MeasurableSpace E]
    [CompleteSpace E] [SecondCountableTopology E] [BorelSpace E]
    [OpensMeasurableSpace E]
    (S : Chewi127BoundedMartingaleCLTSource Ω Ω' E P Q)
    (A Ainv : E →L[ℝ] E) (h : ℕ -> ℝ)
    (delta : ℕ -> Ω -> E) (B0 Bxi : ℝ)
    (hdelta0_bound : ∀ ω, ‖delta 0 ω‖ ≤ B0)
    (hxi_bound : ∀ n ω, ‖S.martingale.xi n ω‖ ≤ Bxi)
    (hinitial_decay :
      Tendsto
        (fun N : ℕ =>
          ‖(Real.sqrt (N : ℝ))⁻¹‖ *
            ‖chewi123InitialCoefficient A h N‖ * B0)
        atTop (𝓝 0))
    (hremainder_decay :
      Tendsto
        (fun N : ℕ =>
          ‖(Real.sqrt (N : ℝ))⁻¹‖ * ‖Ainv‖ * Bxi +
            ‖(Real.sqrt (N : ℝ))⁻¹‖ *
              ∑ k ∈ Finset.Ico 1 N,
                ‖chewi123SourceNoiseCoefficient A h k N - Ainv‖ * Bxi)
        atTop (𝓝 0))
    (hrec : ∀ n ω,
      delta (n + 1) ω =
        chewi123QuadraticStepMap (h (n + 1)) A (delta n ω) -
          h (n + 1) • S.martingale.xi (n + 1) ω)
    (hInitial_meas : ∀ N,
      AEMeasurable (fun ω => chewi123ASGDInitialTerm A h (delta 0 ω) N) P)
    (hRemainder_meas : ∀ N,
      AEMeasurable
        (fun ω =>
          chewi123ASGDEndpointCorrectedRemainder A Ainv h
            (fun n => S.martingale.xi n ω) N) P) :
    TendstoInDistribution
        (fun N ω => chewi123ScaledAverageDelta (fun n => delta n ω) N)
        atTop (fun ω => -Ainv (S.Z ω)) (fun _ => P) Q ∧
      HasGaussianLaw (fun ω => -Ainv (S.Z ω)) Q ∧
      ∀ L K : StrongDual ℝ E,
        ProbabilityTheory.covarianceBilinDual
            (Q.map fun ω => -Ainv (S.Z ω)) L K =
          vaart1998_inverseDerivativeCovarianceFunctional (-Ainv)
            (fun L0 K0 =>
              ProbabilityTheory.covarianceBilinDual (Q.map S.Z) L0 K0) L K :=
  S.asgd_limit_package_endpoint_corrected A Ainv h delta hrec
    (chewi123ASGDInitialTerm_tendstoInMeasure_zero_of_opNorm_decay_bounded_initial
      (P := P) A h (fun ω => delta 0 ω) B0 hdelta0_bound
      hinitial_decay)
    (chewi123ASGDEndpointCorrectedRemainder_tendstoInMeasure_zero_of_uniform_noise_bound_and_coeff_decay
      (P := P) A Ainv h S.martingale.xi Bxi hxi_bound hremainder_decay)
    hInitial_meas hRemainder_meas

/--
Endpoint-corrected Chewi Theorem 12.3 package from the mixed-tower
future-tail predictability gate used to build the Chewi 12.7 martingale CLT.
-/
theorem Chewi127BoundedMartingaleCLTSource.asgd_limit_package_endpoint_corrected_of_mixed_tower_future_tail_measurability
    {Ω Ω' E : Type*} [mΩ : MeasurableSpace Ω] {P : Measure Ω}
    [IsProbabilityMeasure P] [MeasurableSpace Ω'] {Q : Measure Ω'}
    [IsProbabilityMeasure Q]
    [NormedAddCommGroup E] [NormedSpace ℝ E] [MeasurableSpace E]
    [CompleteSpace E] [SecondCountableTopology E] [BorelSpace E]
    [OpensMeasurableSpace E]
    (S : Chewi127BoundedMartingaleCLTSource Ω Ω' E P Q)
    (A Ainv : E →L[ℝ] E) (h : ℕ -> ℝ)
    (delta : ℕ -> Ω -> E)
    (hmean : ∀ L : StrongDual ℝ E, Q[fun ω => L (S.Z ω)] = 0)
    (hfuture_tail_meas : ∀ L : StrongDual ℝ E, ∀ t : ℝ,
      ∀ N r : ℕ, r < N ->
        AEStronglyMeasurable[S.martingale.filtration r]
          (fun ω =>
            ∏ k ∈ Finset.Ico (r + 1) N,
              S.projectedNormalizedTaylorFactor L N t k ω) P)
    (hrec : ∀ n ω,
      delta (n + 1) ω =
        chewi123QuadraticStepMap (h (n + 1)) A (delta n ω) -
          h (n + 1) • S.martingale.xi (n + 1) ω)
    (hInitial : TendstoInMeasure P
      (fun N ω => chewi123ASGDInitialTerm A h (delta 0 ω) N)
      atTop (fun _ => 0))
    (hRemainder : TendstoInMeasure P
      (fun N ω =>
        chewi123ASGDEndpointCorrectedRemainder A Ainv h
          (fun n => S.martingale.xi n ω) N)
      atTop (fun _ => 0))
    (hInitial_meas : ∀ N,
      AEMeasurable (fun ω => chewi123ASGDInitialTerm A h (delta 0 ω) N) P)
    (hRemainder_meas : ∀ N,
      AEMeasurable
        (fun ω =>
          chewi123ASGDEndpointCorrectedRemainder A Ainv h
            (fun n => S.martingale.xi n ω) N) P) :
    TendstoInDistribution
        (fun N ω => chewi123ScaledAverageDelta (fun n => delta n ω) N)
        atTop (fun ω => -Ainv (S.Z ω)) (fun _ => P) Q ∧
      HasGaussianLaw (fun ω => -Ainv (S.Z ω)) Q ∧
      ∀ L K : StrongDual ℝ E,
        ProbabilityTheory.covarianceBilinDual
            (Q.map fun ω => -Ainv (S.Z ω)) L K =
          vaart1998_inverseDerivativeCovarianceFunctional (-Ainv)
            (fun L0 K0 =>
              ProbabilityTheory.covarianceBilinDual (Q.map S.Z) L0 K0) L K := by
  let C : Chewi127MartingaleCLTCertificate Ω Ω' E P Q :=
    S.toMartingaleCLTCertificate_of_mixed_tower_future_tail_measurability
      hmean hfuture_tail_meas
  simpa [C,
    Chewi127BoundedMartingaleCLTSource.toMartingaleCLTCertificate_of_mixed_tower_future_tail_measurability,
    Chewi127BoundedMartingaleCLTSource.toProjectedBridge_of_mixed_tower_future_tail_measurability,
    Chewi127ProjectedMartingaleCLTBridge.toMartingaleCLTCertificate] using
    chewi123_asgd_limit_package_of_martingale_certificate_endpoint_corrected
      (C := C) A Ainv h delta S.martingale.xi
      (fun _ => ae_of_all _ fun _ => rfl) hrec
      hInitial hRemainder hInitial_meas hRemainder_meas

/--
Source-conditioned endpoint-corrected Chewi Theorem 12.3 package from the
mixed-tower future-tail predictability route.
-/
theorem Chewi127BoundedMartingaleCLTSource.asgd_limit_package_endpoint_corrected_of_mixed_tower_future_tail_measurability_and_bounded_initial_uniform_noise_coeff_decay
    {Ω Ω' E : Type*} [mΩ : MeasurableSpace Ω] {P : Measure Ω}
    [IsProbabilityMeasure P] [MeasurableSpace Ω'] {Q : Measure Ω'}
    [IsProbabilityMeasure Q]
    [NormedAddCommGroup E] [NormedSpace ℝ E] [MeasurableSpace E]
    [CompleteSpace E] [SecondCountableTopology E] [BorelSpace E]
    [OpensMeasurableSpace E]
    (S : Chewi127BoundedMartingaleCLTSource Ω Ω' E P Q)
    (A Ainv : E →L[ℝ] E) (h : ℕ -> ℝ)
    (delta : ℕ -> Ω -> E) (B0 Bxi : ℝ)
    (hmean : ∀ L : StrongDual ℝ E, Q[fun ω => L (S.Z ω)] = 0)
    (hfuture_tail_meas : ∀ L : StrongDual ℝ E, ∀ t : ℝ,
      ∀ N r : ℕ, r < N ->
        AEStronglyMeasurable[S.martingale.filtration r]
          (fun ω =>
            ∏ k ∈ Finset.Ico (r + 1) N,
              S.projectedNormalizedTaylorFactor L N t k ω) P)
    (hdelta0_bound : ∀ ω, ‖delta 0 ω‖ ≤ B0)
    (hxi_bound : ∀ n ω, ‖S.martingale.xi n ω‖ ≤ Bxi)
    (hinitial_decay :
      Tendsto
        (fun N : ℕ =>
          ‖(Real.sqrt (N : ℝ))⁻¹‖ *
            ‖chewi123InitialCoefficient A h N‖ * B0)
        atTop (𝓝 0))
    (hremainder_decay :
      Tendsto
        (fun N : ℕ =>
          ‖(Real.sqrt (N : ℝ))⁻¹‖ * ‖Ainv‖ * Bxi +
            ‖(Real.sqrt (N : ℝ))⁻¹‖ *
              ∑ k ∈ Finset.Ico 1 N,
                ‖chewi123SourceNoiseCoefficient A h k N - Ainv‖ * Bxi)
        atTop (𝓝 0))
    (hrec : ∀ n ω,
      delta (n + 1) ω =
        chewi123QuadraticStepMap (h (n + 1)) A (delta n ω) -
          h (n + 1) • S.martingale.xi (n + 1) ω)
    (hInitial_meas : ∀ N,
      AEMeasurable (fun ω => chewi123ASGDInitialTerm A h (delta 0 ω) N) P)
    (hRemainder_meas : ∀ N,
      AEMeasurable
        (fun ω =>
          chewi123ASGDEndpointCorrectedRemainder A Ainv h
            (fun n => S.martingale.xi n ω) N) P) :
    TendstoInDistribution
        (fun N ω => chewi123ScaledAverageDelta (fun n => delta n ω) N)
        atTop (fun ω => -Ainv (S.Z ω)) (fun _ => P) Q ∧
      HasGaussianLaw (fun ω => -Ainv (S.Z ω)) Q ∧
      ∀ L K : StrongDual ℝ E,
        ProbabilityTheory.covarianceBilinDual
            (Q.map fun ω => -Ainv (S.Z ω)) L K =
          vaart1998_inverseDerivativeCovarianceFunctional (-Ainv)
            (fun L0 K0 =>
              ProbabilityTheory.covarianceBilinDual (Q.map S.Z) L0 K0) L K :=
  S.asgd_limit_package_endpoint_corrected_of_mixed_tower_future_tail_measurability
    A Ainv h delta hmean hfuture_tail_meas hrec
    (chewi123ASGDInitialTerm_tendstoInMeasure_zero_of_opNorm_decay_bounded_initial
      (P := P) A h (fun ω => delta 0 ω) B0 hdelta0_bound
      hinitial_decay)
    (chewi123ASGDEndpointCorrectedRemainder_tendstoInMeasure_zero_of_uniform_noise_bound_and_coeff_decay
      (P := P) A Ainv h S.martingale.xi Bxi hxi_bound hremainder_decay)
    hInitial_meas hRemainder_meas

/--
Endpoint-corrected Chewi Theorem 12.3 package from factorwise future-tail
measurability.  This is often the easiest source-facing condition to apply:
prove each normalized Taylor factor is already predictable, then reuse the
mixed-tower route.
-/
theorem Chewi127BoundedMartingaleCLTSource.asgd_limit_package_endpoint_corrected_of_factorwise_future_tail_measurability
    {Ω Ω' E : Type*} [mΩ : MeasurableSpace Ω] {P : Measure Ω}
    [IsProbabilityMeasure P] [MeasurableSpace Ω'] {Q : Measure Ω'}
    [IsProbabilityMeasure Q]
    [NormedAddCommGroup E] [NormedSpace ℝ E] [MeasurableSpace E]
    [CompleteSpace E] [SecondCountableTopology E] [BorelSpace E]
    [OpensMeasurableSpace E]
    (S : Chewi127BoundedMartingaleCLTSource Ω Ω' E P Q)
    (A Ainv : E →L[ℝ] E) (h : ℕ -> ℝ)
    (delta : ℕ -> Ω -> E)
    (hmean : ∀ L : StrongDual ℝ E, Q[fun ω => L (S.Z ω)] = 0)
    (hfactor_tail_meas : ∀ L : StrongDual ℝ E, ∀ t : ℝ,
      ∀ N r : ℕ, r < N ->
        ∀ k ∈ Finset.Ico (r + 1) N,
          AEStronglyMeasurable[S.martingale.filtration r]
            (fun ω => S.projectedNormalizedTaylorFactor L N t k ω) P)
    (hrec : ∀ n ω,
      delta (n + 1) ω =
        chewi123QuadraticStepMap (h (n + 1)) A (delta n ω) -
          h (n + 1) • S.martingale.xi (n + 1) ω)
    (hInitial : TendstoInMeasure P
      (fun N ω => chewi123ASGDInitialTerm A h (delta 0 ω) N)
      atTop (fun _ => 0))
    (hRemainder : TendstoInMeasure P
      (fun N ω =>
        chewi123ASGDEndpointCorrectedRemainder A Ainv h
          (fun n => S.martingale.xi n ω) N)
      atTop (fun _ => 0))
    (hInitial_meas : ∀ N,
      AEMeasurable (fun ω => chewi123ASGDInitialTerm A h (delta 0 ω) N) P)
    (hRemainder_meas : ∀ N,
      AEMeasurable
        (fun ω =>
          chewi123ASGDEndpointCorrectedRemainder A Ainv h
            (fun n => S.martingale.xi n ω) N) P) :
    TendstoInDistribution
        (fun N ω => chewi123ScaledAverageDelta (fun n => delta n ω) N)
        atTop (fun ω => -Ainv (S.Z ω)) (fun _ => P) Q ∧
      HasGaussianLaw (fun ω => -Ainv (S.Z ω)) Q ∧
      ∀ L K : StrongDual ℝ E,
        ProbabilityTheory.covarianceBilinDual
            (Q.map fun ω => -Ainv (S.Z ω)) L K =
          vaart1998_inverseDerivativeCovarianceFunctional (-Ainv)
            (fun L0 K0 =>
              ProbabilityTheory.covarianceBilinDual (Q.map S.Z) L0 K0) L K :=
  S.asgd_limit_package_endpoint_corrected_of_mixed_tower_future_tail_measurability
    A Ainv h delta hmean
    (fun L t N r hr =>
      S.projectedNormalizedTaylorFutureTail_aestronglyMeasurable_of_factorwise
        L N r t (hfactor_tail_meas L t N r hr))
    hrec hInitial hRemainder hInitial_meas hRemainder_meas

/--
Fully source-conditioned endpoint-corrected Chewi Theorem 12.3 package from
factorwise future-tail measurability.  This is the preferred Chapter 12
surface: no caller-supplied initial/remainder convergence-in-measure
hypotheses remain.
-/
theorem Chewi127BoundedMartingaleCLTSource.asgd_limit_package_endpoint_corrected_of_factorwise_future_tail_measurability_and_bounded_initial_uniform_noise_coeff_decay
    {Ω Ω' E : Type*} [mΩ : MeasurableSpace Ω] {P : Measure Ω}
    [IsProbabilityMeasure P] [MeasurableSpace Ω'] {Q : Measure Ω'}
    [IsProbabilityMeasure Q]
    [NormedAddCommGroup E] [NormedSpace ℝ E] [MeasurableSpace E]
    [CompleteSpace E] [SecondCountableTopology E] [BorelSpace E]
    [OpensMeasurableSpace E]
    (S : Chewi127BoundedMartingaleCLTSource Ω Ω' E P Q)
    (A Ainv : E →L[ℝ] E) (h : ℕ -> ℝ)
    (delta : ℕ -> Ω -> E) (B0 Bxi : ℝ)
    (hmean : ∀ L : StrongDual ℝ E, Q[fun ω => L (S.Z ω)] = 0)
    (hfactor_tail_meas : ∀ L : StrongDual ℝ E, ∀ t : ℝ,
      ∀ N r : ℕ, r < N ->
        ∀ k ∈ Finset.Ico (r + 1) N,
          AEStronglyMeasurable[S.martingale.filtration r]
            (fun ω => S.projectedNormalizedTaylorFactor L N t k ω) P)
    (hdelta0_bound : ∀ ω, ‖delta 0 ω‖ ≤ B0)
    (hxi_bound : ∀ n ω, ‖S.martingale.xi n ω‖ ≤ Bxi)
    (hinitial_decay :
      Tendsto
        (fun N : ℕ =>
          ‖(Real.sqrt (N : ℝ))⁻¹‖ *
            ‖chewi123InitialCoefficient A h N‖ * B0)
        atTop (𝓝 0))
    (hremainder_decay :
      Tendsto
        (fun N : ℕ =>
          ‖(Real.sqrt (N : ℝ))⁻¹‖ * ‖Ainv‖ * Bxi +
            ‖(Real.sqrt (N : ℝ))⁻¹‖ *
              ∑ k ∈ Finset.Ico 1 N,
                ‖chewi123SourceNoiseCoefficient A h k N - Ainv‖ * Bxi)
        atTop (𝓝 0))
    (hrec : ∀ n ω,
      delta (n + 1) ω =
        chewi123QuadraticStepMap (h (n + 1)) A (delta n ω) -
          h (n + 1) • S.martingale.xi (n + 1) ω)
    (hInitial_meas : ∀ N,
      AEMeasurable (fun ω => chewi123ASGDInitialTerm A h (delta 0 ω) N) P)
    (hRemainder_meas : ∀ N,
      AEMeasurable
        (fun ω =>
          chewi123ASGDEndpointCorrectedRemainder A Ainv h
            (fun n => S.martingale.xi n ω) N) P) :
    TendstoInDistribution
        (fun N ω => chewi123ScaledAverageDelta (fun n => delta n ω) N)
        atTop (fun ω => -Ainv (S.Z ω)) (fun _ => P) Q ∧
      HasGaussianLaw (fun ω => -Ainv (S.Z ω)) Q ∧
      ∀ L K : StrongDual ℝ E,
        ProbabilityTheory.covarianceBilinDual
            (Q.map fun ω => -Ainv (S.Z ω)) L K =
          vaart1998_inverseDerivativeCovarianceFunctional (-Ainv)
            (fun L0 K0 =>
              ProbabilityTheory.covarianceBilinDual (Q.map S.Z) L0 K0) L K :=
  S.asgd_limit_package_endpoint_corrected_of_factorwise_future_tail_measurability
    A Ainv h delta hmean hfactor_tail_meas hrec
    (chewi123ASGDInitialTerm_tendstoInMeasure_zero_of_opNorm_decay_bounded_initial
      (P := P) A h (fun ω => delta 0 ω) B0 hdelta0_bound
      hinitial_decay)
    (chewi123ASGDEndpointCorrectedRemainder_tendstoInMeasure_zero_of_uniform_noise_bound_and_coeff_decay
      (P := P) A Ainv h S.martingale.xi Bxi hxi_bound hremainder_decay)
    hInitial_meas hRemainder_meas

/--
Preferred source-facing Chewi Theorem 12.3 package with scalar coefficient
majorants.  This is the handoff from the deterministic Lemma 12.5-style
coefficient work to the V117 ASGD limit wrapper: callers may prove scalar
bounds for `M_0^N` and the residual row `M_k^N - A^{-1}` instead of restating
the exact operator-norm decay hypotheses.
-/
theorem Chewi127BoundedMartingaleCLTSource.asgd_limit_package_endpoint_corrected_of_factorwise_future_tail_measurability_and_scalar_coefficient_bounds
    {Ω Ω' E : Type*} [mΩ : MeasurableSpace Ω] {P : Measure Ω}
    [IsProbabilityMeasure P] [MeasurableSpace Ω'] {Q : Measure Ω'}
    [IsProbabilityMeasure Q]
    [NormedAddCommGroup E] [NormedSpace ℝ E] [MeasurableSpace E]
    [CompleteSpace E] [SecondCountableTopology E] [BorelSpace E]
    [OpensMeasurableSpace E]
    (S : Chewi127BoundedMartingaleCLTSource Ω Ω' E P Q)
    (A Ainv : E →L[ℝ] E) (h : ℕ -> ℝ)
    (delta : ℕ -> Ω -> E) (B0 Bxi : ℝ)
    (C0 : ℕ -> ℝ) (R : ℕ -> ℕ -> ℝ)
    (hmean : ∀ L : StrongDual ℝ E, Q[fun ω => L (S.Z ω)] = 0)
    (hfactor_tail_meas : ∀ L : StrongDual ℝ E, ∀ t : ℝ,
      ∀ N r : ℕ, r < N ->
        ∀ k ∈ Finset.Ico (r + 1) N,
          AEStronglyMeasurable[S.martingale.filtration r]
            (fun ω => S.projectedNormalizedTaylorFactor L N t k ω) P)
    (hB0_nonneg : 0 ≤ B0) (hBxi_nonneg : 0 ≤ Bxi)
    (hdelta0_bound : ∀ ω, ‖delta 0 ω‖ ≤ B0)
    (hxi_bound : ∀ n ω, ‖S.martingale.xi n ω‖ ≤ Bxi)
    (hinitial_bound : ∀ N,
      ‖chewi123InitialCoefficient A h N‖ ≤ C0 N)
    (hresidual_bound : ∀ N k, k ∈ Finset.Ico 1 N ->
      ‖chewi123SourceNoiseCoefficient A h k N - Ainv‖ ≤ R N k)
    (hinitial_decay :
      Tendsto
        (fun N : ℕ =>
          ‖(Real.sqrt (N : ℝ))⁻¹‖ * C0 N * B0)
        atTop (𝓝 0))
    (hremainder_decay :
      Tendsto
        (fun N : ℕ =>
          ‖(Real.sqrt (N : ℝ))⁻¹‖ * ‖Ainv‖ * Bxi +
            ‖(Real.sqrt (N : ℝ))⁻¹‖ *
              ∑ k ∈ Finset.Ico 1 N, R N k * Bxi)
        atTop (𝓝 0))
    (hrec : ∀ n ω,
      delta (n + 1) ω =
        chewi123QuadraticStepMap (h (n + 1)) A (delta n ω) -
          h (n + 1) • S.martingale.xi (n + 1) ω)
    (hInitial_meas : ∀ N,
      AEMeasurable (fun ω => chewi123ASGDInitialTerm A h (delta 0 ω) N) P)
    (hRemainder_meas : ∀ N,
      AEMeasurable
        (fun ω =>
          chewi123ASGDEndpointCorrectedRemainder A Ainv h
            (fun n => S.martingale.xi n ω) N) P) :
    TendstoInDistribution
        (fun N ω => chewi123ScaledAverageDelta (fun n => delta n ω) N)
        atTop (fun ω => -Ainv (S.Z ω)) (fun _ => P) Q ∧
      HasGaussianLaw (fun ω => -Ainv (S.Z ω)) Q ∧
      ∀ L K : StrongDual ℝ E,
        ProbabilityTheory.covarianceBilinDual
            (Q.map fun ω => -Ainv (S.Z ω)) L K =
          vaart1998_inverseDerivativeCovarianceFunctional (-Ainv)
            (fun L0 K0 =>
              ProbabilityTheory.covarianceBilinDual (Q.map S.Z) L0 K0) L K :=
  S.asgd_limit_package_endpoint_corrected_of_factorwise_future_tail_measurability_and_bounded_initial_uniform_noise_coeff_decay
    A Ainv h delta B0 Bxi hmean hfactor_tail_meas
    hdelta0_bound hxi_bound
    (chewi123InitialCoefficient_sqrt_decay_of_norm_bound
      A h C0 B0 hB0_nonneg hinitial_bound hinitial_decay)
    (chewi123ASGDEndpointCorrectedRemainder_coeff_decay_of_residual_row_bound
      A Ainv h Bxi R hBxi_nonneg hresidual_bound hremainder_decay)
    hrec hInitial_meas hRemainder_meas

end Optimization
end StatInference
