import Mathlib.MeasureTheory.Function.L2Space
import Mathlib.Probability.Process.Filtration
import StatInference.Optimization.MirrorDescent

/-!
# Chewi Chapter 12 stochastic gradient methods

This module opens the Chapter 12 lane.  The first packet proves the scalar
weighted-average consequence used at the end of Chewi Theorem 12.1 for SMPGD:
a Gronwall recurrence with a negative gap forcing and an additive stochastic
error gives the displayed weighted average bound.
-/

namespace StatInference
namespace Optimization

open Finset
open MeasureTheory
open scoped InnerProductSpace MeasureTheory

/--
If a conditional expectation is a constant vector, then the unconditional
Bochner integral is that vector under a probability law.
-/
theorem integral_eq_const_of_condExp_ae_eq_const
    {Ω : Type*} [mΩ : MeasurableSpace Ω] {μ : Measure Ω}
    [IsProbabilityMeasure μ]
    {E : Type*} [NormedAddCommGroup E] [NormedSpace ℝ E] [CompleteSpace E]
    {m : MeasurableSpace Ω} (hsub : m ≤ mΩ)
    [SigmaFinite (μ.trim hsub)]
    (p : Ω -> E) (c : E)
    (hcond : μ[p | m] =ᵐ[μ] fun _ => c) :
    (∫ ω, p ω ∂μ) = c := by
  rw [← integral_condExp
    (m := m) (m₀ := mΩ) (μ := μ) (f := p) hsub]
  calc
    (∫ ω, μ[p | m] ω ∂μ) = ∫ _ω, c ∂μ :=
      integral_congr_ae hcond
    _ = c := by simp

/--
Filtration-shaped version of the constant conditional-expectation bridge.
This is the source-facing handoff from a process conditional-mean assumption
to the unconditional mean used by the SMPGD rate theorem.
-/
theorem integral_eq_const_of_filtration_condExp_ae_eq_const
    {Ω : Type*} [mΩ : MeasurableSpace Ω] {μ : Measure Ω}
    [IsProbabilityMeasure μ]
    {E : Type*} [NormedAddCommGroup E] [NormedSpace ℝ E] [CompleteSpace E]
    (Ffiltration : Filtration ℕ mΩ) (n : ℕ)
    (p : Ω -> E) (c : E)
    (hcond : μ[p | Ffiltration n] =ᵐ[μ] fun _ => c) :
    (∫ ω, p ω ∂μ) = c :=
  integral_eq_const_of_condExp_ae_eq_const
    (μ := μ) (m := Ffiltration n) (hsub := Ffiltration.le n)
    p c hcond

/--
Relative finite-valued subgradient interface for the non-smooth branch of
Chewi Theorem 12.1.  It is the nonsmooth analogue of
`RelativelyStrongConvexOn.lower_model` at one point.
-/
def IsRelativeSubgradientAt
    {E : Type*} [NormedAddCommGroup E] [InnerProductSpace ℝ E]
    (C : Set E) (f : E -> ℝ) (p : E)
    (phi : E -> ℝ) (gradPhi : E -> E) (alpha : ℝ) (x : E) : Prop :=
  x ∈ C ∧ ∀ ⦃y : E⦄, y ∈ C ->
    f x + inner ℝ p (y - x) +
        alpha * bregmanDivergence phi gradPhi y x ≤ f y

theorem IsRelativeSubgradientAt.mem
    {E : Type*} [NormedAddCommGroup E] [InnerProductSpace ℝ E]
    {C : Set E} {f : E -> ℝ} {p : E}
    {phi : E -> ℝ} {gradPhi : E -> E} {alpha : ℝ} {x : E}
    (h : IsRelativeSubgradientAt C f p phi gradPhi alpha x) :
    x ∈ C :=
  h.1

theorem IsRelativeSubgradientAt.lower_model
    {E : Type*} [NormedAddCommGroup E] [InnerProductSpace ℝ E]
    {C : Set E} {f : E -> ℝ} {p : E}
    {phi : E -> ℝ} {gradPhi : E -> E} {alpha : ℝ} {x y : E}
    (h : IsRelativeSubgradientAt C f p phi gradPhi alpha x)
    (hy : y ∈ C) :
    f x + inner ℝ p (y - x) +
        alpha * bregmanDivergence phi gradPhi y x ≤ f y :=
  h.2 hy

/--
Weighted stochastic averaged iterate used by Chewi Theorem 12.1.  The weights
are intentionally left unnormalized; `Finset.centerMass` divides by their sum.
-/
noncomputable def weightedSampleAverage
    {Ω E : Type*} [NormedAddCommGroup E] [NormedSpace ℝ E]
    (w : ℕ -> ℝ) (x : ℕ -> Ω -> E) (N : ℕ) (ω : Ω) : E :=
  (Finset.range N).centerMass w (fun n => x n ω)

/--
Jensen bridge from a weighted average of expected gaps to the expected
objective gap at the weighted stochastic averaged iterate.
-/
theorem integral_weightedSampleAverage_gap_le_of_weighted_gap_bound
    {Ω : Type*} [MeasurableSpace Ω] {μ : Measure Ω}
    {E : Type*} [NormedAddCommGroup E] [InnerProductSpace ℝ E]
    {C : Set E} {F : E -> ℝ}
    {w gap : ℕ -> ℝ} {x : ℕ -> Ω -> E}
    {Fstar B : ℝ} {N : ℕ}
    (hconvF : ConvexOn ℝ C F)
    (hw_nonneg : ∀ n, n < N -> 0 ≤ w n)
    (hsum_pos : 0 < ∑ n ∈ Finset.range N, w n)
    (hx : ∀ n, n < N -> ∀ᵐ ω ∂μ, x n ω ∈ C)
    (havg_int :
      Integrable (fun ω => F (weightedSampleAverage w x N ω)) μ)
    (hF_int : ∀ n, n < N -> Integrable (fun ω => F (x n ω)) μ)
    (hgap : ∀ n, n < N -> Fstar + gap n = ∫ ω, F (x n ω) ∂μ)
    (hbound :
      (1 / (∑ n ∈ Finset.range N, w n)) *
          (∑ n ∈ Finset.range N, w n * gap n) ≤ B) :
    (∫ ω, F (weightedSampleAverage w x N ω) ∂μ) - Fstar ≤ B := by
  let S : ℝ := ∑ n ∈ Finset.range N, w n
  have hS_ne : S ≠ 0 := by
    simpa [S] using ne_of_gt hsum_pos
  have hx_ae :
      ∀ᵐ ω ∂μ, ∀ n, n ∈ Finset.range N -> x n ω ∈ C := by
    rw [eventually_finset_ball]
    intro n hn
    exact hx n (Finset.mem_range.mp hn)
  have hpoint :
      (fun ω => F (weightedSampleAverage w x N ω)) ≤ᵐ[μ]
        fun ω => (1 / S) *
          (∑ n ∈ Finset.range N, w n * F (x n ω)) := by
    filter_upwards [hx_ae] with ω hω
    have hjensen :=
      hconvF.map_centerMass_le
        (t := Finset.range N) (w := w) (p := fun n => x n ω)
        (fun n hn => hw_nonneg n (Finset.mem_range.mp hn))
        hsum_pos
        (fun n hn => hω n hn)
    simpa [weightedSampleAverage, Finset.centerMass, S, one_div, Function.comp] using hjensen
  have hsum_int :
      Integrable
        (fun ω => ∑ n ∈ Finset.range N, w n * F (x n ω)) μ := by
    refine integrable_finsetSum (Finset.range N) ?_
    intro n hn
    exact (hF_int n (Finset.mem_range.mp hn)).const_mul (w n)
  have hR_int :
      Integrable
        (fun ω => (1 / S) *
          (∑ n ∈ Finset.range N, w n * F (x n ω))) μ :=
    hsum_int.const_mul (1 / S)
  have hint_le :
      (∫ ω, F (weightedSampleAverage w x N ω) ∂μ) ≤
        ∫ ω, (1 / S) *
          (∑ n ∈ Finset.range N, w n * F (x n ω)) ∂μ :=
    integral_mono_ae havg_int hR_int hpoint
  have hint_rhs :
      (∫ ω, (1 / S) *
          (∑ n ∈ Finset.range N, w n * F (x n ω)) ∂μ) =
        (1 / S) *
          (∑ n ∈ Finset.range N, w n * ∫ ω, F (x n ω) ∂μ) := by
    rw [integral_const_mul]
    rw [integral_finsetSum]
    · refine congrArg ((HMul.hMul) (1 / S)) ?_
      refine Finset.sum_congr rfl ?_
      intro n hn
      rw [integral_const_mul]
    · intro n hn
      exact (hF_int n (Finset.mem_range.mp hn)).const_mul (w n)
  have hsum_gap :
      (∑ n ∈ Finset.range N, w n * ∫ ω, F (x n ω) ∂μ) =
        ∑ n ∈ Finset.range N, w n * (Fstar + gap n) := by
    refine Finset.sum_congr rfl ?_
    intro n hn
    rw [← hgap n (Finset.mem_range.mp hn)]
  have hsum_split :
      (∑ n ∈ Finset.range N, w n * (Fstar + gap n)) =
        S * Fstar + ∑ n ∈ Finset.range N, w n * gap n := by
    calc
      (∑ n ∈ Finset.range N, w n * (Fstar + gap n)) =
          ∑ n ∈ Finset.range N, (w n * Fstar + w n * gap n) := by
            refine Finset.sum_congr rfl ?_
            intro n hn
            ring
      _ =
          (∑ n ∈ Finset.range N, w n * Fstar) +
            ∑ n ∈ Finset.range N, w n * gap n := by
            rw [Finset.sum_add_distrib]
      _ = S * Fstar + ∑ n ∈ Finset.range N, w n * gap n := by
            rw [Finset.sum_mul]
  have hgap_rewrite :
      (1 / S) *
          (∑ n ∈ Finset.range N, w n * ∫ ω, F (x n ω) ∂μ) - Fstar =
        (1 / S) * (∑ n ∈ Finset.range N, w n * gap n) := by
    rw [hsum_gap, hsum_split]
    field_simp [hS_ne]
    ring
  calc
    (∫ ω, F (weightedSampleAverage w x N ω) ∂μ) - Fstar ≤
        (∫ ω, (1 / S) *
          (∑ n ∈ Finset.range N, w n * F (x n ω)) ∂μ) - Fstar := by
          nlinarith
    _ = (1 / S) * (∑ n ∈ Finset.range N, w n * gap n) := by
          rw [hint_rhs, hgap_rewrite]
    _ ≤ B := by
          simpa [S] using hbound

/--
Chewi-weighted version of the stochastic Jensen bridge.  This turns the
geometric weighted expected-gap bound from Theorem 12.1 into the same bound for
the objective value at the stochastic weighted averaged iterate.
-/
theorem chewi121_weightedSampleAverage_gap_le_geometric_of_weightedAverageGap
    {Ω : Type*} [MeasurableSpace Ω] {μ : Measure Ω}
    {E : Type*} [NormedAddCommGroup E] [InnerProductSpace ℝ E]
    {C : Set E} {F : E -> ℝ}
    {alphaF alphaG h Fstar B : ℝ} {N : ℕ}
    {gap : ℕ -> ℝ} {x : ℕ -> Ω -> E}
    (hconvF : ConvexOn ℝ C F)
    (hN : N ≠ 0)
    (hlambda_pos : 0 < chewi109Lambda alphaF alphaG h)
    (hx : ∀ n, n < N -> ∀ᵐ ω ∂μ, x n ω ∈ C)
    (havg_int : Integrable
      (fun ω =>
        F (weightedSampleAverage
          (fun n => (chewi109Lambda alphaF alphaG h) ^ (N - 1 - n))
          x N ω)) μ)
    (hF_int : ∀ n, n < N -> Integrable (fun ω => F (x n ω)) μ)
    (hgap : ∀ n, n < N ->
      Fstar + gap (n + 1) = ∫ ω, F (x n ω) ∂μ)
    (hbound :
      (1 / (∑ n ∈ Finset.range N,
            (chewi109Lambda alphaF alphaG h) ^ (N - 1 - n))) *
          (∑ n ∈ Finset.range N,
            (chewi109Lambda alphaF alphaG h) ^ (N - 1 - n) *
              gap (n + 1)) ≤ B) :
    (∫ ω,
        F (weightedSampleAverage
          (fun n => (chewi109Lambda alphaF alphaG h) ^ (N - 1 - n))
          x N ω) ∂μ) - Fstar ≤ B := by
  let A : ℝ := chewi109Lambda alphaF alphaG h
  let weights : ℕ -> ℝ := fun n => A ^ (N - 1 - n)
  have hA_nonneg : 0 ≤ A := le_of_lt (by simpa [A] using hlambda_pos)
  have hweights_nonneg : ∀ n, n < N -> 0 ≤ weights n := by
    intro n hn
    exact pow_nonneg hA_nonneg _
  have hweights_sum_pos :
      0 < ∑ n ∈ Finset.range N, weights n := by
    simpa [weights, A] using geometricWeights_sum_pos (A := A) hA_nonneg hN
  have hbound' :
      (1 / (∑ n ∈ Finset.range N, weights n)) *
          (∑ n ∈ Finset.range N, weights n * (fun k => gap (k + 1)) n) ≤ B := by
    simpa [weights, A] using hbound
  exact
    integral_weightedSampleAverage_gap_le_of_weighted_gap_bound
      (μ := μ) (C := C) (F := F) (w := weights)
      (gap := fun n => gap (n + 1)) (x := x) (Fstar := Fstar)
      (B := B) hconvF hweights_nonneg hweights_sum_pos hx
      (by simpa [weights, A] using havg_int) hF_int
      (by simpa using hgap) hbound'

/--
Upgrade a stronger smooth-case Chewi 12.1 averaged-iterate bound to the
constant displayed in the source theorem.  The compiled stochastic wrappers
prove the same estimate without the harmless factor `1 + alphaG * h`; this
lemma packages the exact displayed RHS under `0 <= alphaG`.
-/
theorem chewi121_smooth_displayed_error_rhs_of_stronger
    {lhs init alphaG sigma dim h alphaPhi : ℝ}
    (halphaG_nonneg : 0 ≤ alphaG) (hh : 0 < h)
    (halphaPhi : 0 < alphaPhi) (hdim_nonneg : 0 ≤ dim)
    (hstrong : lhs ≤ init + sigma ^ (2 : ℕ) * dim * h / alphaPhi) :
    lhs ≤ init + (1 + alphaG * h) *
        (sigma ^ (2 : ℕ) * dim * h / alphaPhi) := by
  let base : ℝ := sigma ^ (2 : ℕ) * dim * h / alphaPhi
  have hbase_nonneg : 0 ≤ base := by
    have hnum : 0 ≤ sigma ^ (2 : ℕ) * dim * h :=
      mul_nonneg (mul_nonneg (sq_nonneg sigma) hdim_nonneg) hh.le
    exact div_nonneg hnum halphaPhi.le
  have hfactor_ge_one : 1 ≤ 1 + alphaG * h := by
    have hmul : 0 ≤ alphaG * h := mul_nonneg halphaG_nonneg hh.le
    nlinarith
  have hbase_le : base ≤ (1 + alphaG * h) * base := by
    simpa using mul_le_mul_of_nonneg_right hfactor_ge_one hbase_nonneg
  nlinarith [hstrong]

/--
Smooth Chewi 12.1 averaged-iterate bound with the exact displayed stochastic
constant, as a corollary of any stronger bound at the same averaged iterate.
-/
theorem chewi121_smooth_weightedSampleAverage_gap_le_displayed_of_stronger
    {Ω : Type*} [MeasurableSpace Ω] {μ : Measure Ω}
    {E : Type*} [NormedAddCommGroup E] [InnerProductSpace ℝ E]
    {f g : E -> ℝ}
    {alphaF alphaG alphaPhi sigma dim h Fstar : ℝ} {N : ℕ}
    {D : ℕ -> ℝ} {xPlus : ℕ -> Ω -> E}
    (halphaG_nonneg : 0 ≤ alphaG) (hh : 0 < h)
    (halphaPhi : 0 < alphaPhi) (hdim_nonneg : 0 ≤ dim)
    (hstrong :
      (∫ ω,
          compositeObjective f g
            (weightedSampleAverage
              (fun n => (chewi109Lambda alphaF alphaG h) ^ (N - 1 - n))
              xPlus N ω) ∂μ) - Fstar ≤
        (alphaF + alphaG) /
            (((chewi109Lambda alphaF alphaG h) ^ N)⁻¹ - 1) * D 0 +
          sigma ^ (2 : ℕ) * dim * h / alphaPhi) :
    (∫ ω,
        compositeObjective f g
          (weightedSampleAverage
            (fun n => (chewi109Lambda alphaF alphaG h) ^ (N - 1 - n))
            xPlus N ω) ∂μ) - Fstar ≤
      (alphaF + alphaG) /
          (((chewi109Lambda alphaF alphaG h) ^ N)⁻¹ - 1) * D 0 +
        (1 + alphaG * h) *
          (sigma ^ (2 : ℕ) * dim * h / alphaPhi) :=
  chewi121_smooth_displayed_error_rhs_of_stronger
    halphaG_nonneg hh halphaPhi hdim_nonneg hstrong

/--
Upgrade a stronger non-smooth Chewi 12.1 averaged-iterate bound to the exact
constant displayed in the source theorem.
-/
theorem chewi121_nonsmooth_displayed_error_rhs_of_stronger
    {lhs init alphaG L h alphaPhi : ℝ}
    (halphaG_nonneg : 0 ≤ alphaG) (hh : 0 < h)
    (halphaPhi : 0 < alphaPhi)
    (hstrong : lhs ≤ init + 2 * L ^ (2 : ℕ) * h / alphaPhi) :
    lhs ≤ init + (1 + alphaG * h) *
        (2 * L ^ (2 : ℕ) * h / alphaPhi) := by
  let base : ℝ := 2 * L ^ (2 : ℕ) * h / alphaPhi
  have hbase_nonneg : 0 ≤ base := by
    have htwo : 0 ≤ (2 : ℝ) := by norm_num
    have hnum : 0 ≤ 2 * L ^ (2 : ℕ) * h :=
      mul_nonneg (mul_nonneg htwo (sq_nonneg L)) hh.le
    exact div_nonneg hnum halphaPhi.le
  have hfactor_ge_one : 1 ≤ 1 + alphaG * h := by
    have hmul : 0 ≤ alphaG * h := mul_nonneg halphaG_nonneg hh.le
    nlinarith
  have hbase_le : base ≤ (1 + alphaG * h) * base := by
    simpa using mul_le_mul_of_nonneg_right hfactor_ge_one hbase_nonneg
  nlinarith [hstrong]

/--
Non-smooth Chewi 12.1 averaged-iterate bound with the exact displayed
stochastic constant, as a corollary of any stronger bound at the same averaged
iterate.
-/
theorem chewi121_nonsmooth_weightedSampleAverage_gap_le_displayed_of_stronger
    {Ω : Type*} [MeasurableSpace Ω] {μ : Measure Ω}
    {E : Type*} [NormedAddCommGroup E] [InnerProductSpace ℝ E]
    {f g : E -> ℝ}
    {alphaF alphaG alphaPhi L h Fstar : ℝ} {N : ℕ}
    {D : ℕ -> ℝ} {xPlus : ℕ -> Ω -> E}
    (halphaG_nonneg : 0 ≤ alphaG) (hh : 0 < h)
    (halphaPhi : 0 < alphaPhi)
    (hstrong :
      (∫ ω,
          compositeObjective f g
            (weightedSampleAverage
              (fun n => (chewi109Lambda alphaF alphaG h) ^ (N - 1 - n))
              xPlus N ω) ∂μ) - Fstar ≤
        (alphaF + alphaG) /
            (((chewi109Lambda alphaF alphaG h) ^ N)⁻¹ - 1) * D 0 +
          2 * L ^ (2 : ℕ) * h / alphaPhi) :
    (∫ ω,
        compositeObjective f g
          (weightedSampleAverage
            (fun n => (chewi109Lambda alphaF alphaG h) ^ (N - 1 - n))
            xPlus N ω) ∂μ) - Fstar ≤
      (alphaF + alphaG) /
          (((chewi109Lambda alphaF alphaG h) ^ N)⁻¹ - 1) * D 0 +
        (1 + alphaG * h) *
          (2 * L ^ (2 : ℕ) * h / alphaPhi) :=
  chewi121_nonsmooth_displayed_error_rhs_of_stronger
    halphaG_nonneg hh halphaPhi hstrong

/--
Weighted-sum consequence of a discrete Gronwall recurrence with an additive
stochastic error term.

This is the scalar spine behind the final averaging step in Chewi Theorem 12.1.
-/
theorem weightedSumBound_of_gronwall_negative_forcing_with_error
    {A rho err : ℝ} (hA : 0 ≤ A) (u gap : ℕ -> ℝ) (N : ℕ)
    (huN_nonneg : 0 ≤ u N)
    (hrec : ∀ n, n < N ->
      u (n + 1) ≤ A * u n - rho * gap (n + 1) + err) :
    rho *
        (∑ n ∈ Finset.range N, A ^ (N - 1 - n) * gap (n + 1)) ≤
      A ^ N * u 0 +
        err * (∑ n ∈ Finset.range N, A ^ (N - 1 - n)) := by
  let B : ℕ -> ℝ := fun n => -rho * gap (n + 1) + err
  have hrec' : ∀ n, n < N -> u (n + 1) ≤ A * u n + B n := by
    intro n hn
    simpa [B, sub_eq_add_neg, add_assoc] using hrec n hn
  have hgr :=
    discreteGronwall_sum_le hA u B N hrec'
  have hrhs_nonneg :
      0 ≤ A ^ N * u 0 +
        ∑ n ∈ Finset.range N, A ^ (N - 1 - n) * B n :=
    huN_nonneg.trans hgr
  have hsum :
      (∑ n ∈ Finset.range N, A ^ (N - 1 - n) * B n) =
        -rho *
          (∑ n ∈ Finset.range N, A ^ (N - 1 - n) * gap (n + 1)) +
            err * (∑ n ∈ Finset.range N, A ^ (N - 1 - n)) := by
    calc
      (∑ n ∈ Finset.range N, A ^ (N - 1 - n) * B n)
          =
            ∑ n ∈ Finset.range N,
              ((-rho) * (A ^ (N - 1 - n) * gap (n + 1)) +
                err * A ^ (N - 1 - n)) := by
              refine Finset.sum_congr rfl ?_
              intro n hn
              simp [B]
              ring
      _ =
            (-rho) *
              (∑ n ∈ Finset.range N, A ^ (N - 1 - n) * gap (n + 1)) +
                err * (∑ n ∈ Finset.range N, A ^ (N - 1 - n)) := by
              rw [Finset.sum_add_distrib, Finset.mul_sum, Finset.mul_sum]
  have hnonneg :
      0 ≤ A ^ N * u 0 -
          rho *
            (∑ n ∈ Finset.range N, A ^ (N - 1 - n) * gap (n + 1)) +
          err * (∑ n ∈ Finset.range N, A ^ (N - 1 - n)) := by
    simpa [hsum, sub_eq_add_neg, add_assoc, add_left_comm, add_comm] using hrhs_nonneg
  nlinarith

/--
Weighted-average version of
`weightedSumBound_of_gronwall_negative_forcing_with_error`.
-/
theorem weightedAverageGap_le_of_gronwall_negative_forcing_with_error
    {A rho err : ℝ} (hA : 0 ≤ A) (hrho : 0 < rho)
    (u gap : ℕ -> ℝ) {N : ℕ} (hN : N ≠ 0)
    (huN_nonneg : 0 ≤ u N)
    (hrec : ∀ n, n < N ->
      u (n + 1) ≤ A * u n - rho * gap (n + 1) + err) :
    (1 / (∑ n ∈ Finset.range N, A ^ (N - 1 - n))) *
        (∑ n ∈ Finset.range N, A ^ (N - 1 - n) * gap (n + 1)) ≤
      (A ^ N * u 0) /
          (rho * ∑ n ∈ Finset.range N, A ^ (N - 1 - n)) +
        err / rho := by
  let weights : ℝ := ∑ n ∈ Finset.range N, A ^ (N - 1 - n)
  let weightedGap : ℝ :=
    ∑ n ∈ Finset.range N, A ^ (N - 1 - n) * gap (n + 1)
  have hweights_pos : 0 < weights := by
    simpa [weights] using geometricWeights_sum_pos (A := A) hA hN
  have hden_pos : 0 < rho * weights := mul_pos hrho hweights_pos
  have hsum :=
    weightedSumBound_of_gronwall_negative_forcing_with_error
      (A := A) (rho := rho) (err := err) hA u gap N huN_nonneg hrec
  have hsum' : rho * weightedGap ≤ A ^ N * u 0 + err * weights := by
    simpa [weights, weightedGap] using hsum
  calc
    (1 / weights) * weightedGap
        = (rho * weightedGap) / (rho * weights) := by
            field_simp [hrho.ne', hweights_pos.ne']
    _ ≤ (A ^ N * u 0 + err * weights) / (rho * weights) := by
            exact div_le_div_of_nonneg_right hsum' hden_pos.le
    _ = (A ^ N * u 0) / (rho * weights) + err / rho := by
            field_simp [hrho.ne', hweights_pos.ne']

/--
Chewi Theorem 12.1 scalar SMPGD averaging step.  Once the stochastic one-step
estimate has been proved in the normalized form
`u_{n+1} <= A u_n - rho * gap_{n+1} + err`, the suitably weighted average of
the expected gaps is bounded by the initial Bregman term plus the stochastic
error floor.
-/
theorem chewi121_weightedAverageGap_le_of_oneStep
    {A rho err : ℝ} (hA : 0 ≤ A) (hrho : 0 < rho)
    (D gap : ℕ -> ℝ) {N : ℕ} (hN : N ≠ 0)
    (hD_N_nonneg : 0 ≤ D N)
    (hone_step : ∀ n, n < N ->
      D (n + 1) ≤ A * D n - rho * gap (n + 1) + err) :
    (1 / (∑ n ∈ Finset.range N, A ^ (N - 1 - n))) *
        (∑ n ∈ Finset.range N, A ^ (N - 1 - n) * gap (n + 1)) ≤
      (A ^ N * D 0) /
          (rho * ∑ n ∈ Finset.range N, A ^ (N - 1 - n)) +
        err / rho :=
  weightedAverageGap_le_of_gronwall_negative_forcing_with_error
    (A := A) (rho := rho) (err := err) hA hrho D gap hN hD_N_nonneg hone_step

/--
Chewi Theorem 12.1 normalized source one-step wrapper.  The displayed SMPGD
one-step estimate has a prefactor `1 + alphaG * h` on the next Bregman term;
dividing by this prefactor feeds the scalar weighted-average theorem.
-/
theorem chewi121_weightedAverageGap_le_of_source_oneStep
    {alphaF alphaG h err : ℝ}
    (hh : 0 < h) (hden_pos : 0 < 1 + alphaG * h)
    (hlambda_nonneg : 0 ≤ chewi109Lambda alphaF alphaG h)
    (D gap : ℕ -> ℝ) {N : ℕ} (hN : N ≠ 0)
    (hD_N_nonneg : 0 ≤ D N)
    (hone_step : ∀ n, n < N ->
      (1 + alphaG * h) * D (n + 1) ≤
        (1 - alphaF * h) * D n - h * gap (n + 1) + err) :
    (1 / (∑ n ∈ Finset.range N,
          (chewi109Lambda alphaF alphaG h) ^ (N - 1 - n))) *
        (∑ n ∈ Finset.range N,
          (chewi109Lambda alphaF alphaG h) ^ (N - 1 - n) * gap (n + 1)) ≤
      ((chewi109Lambda alphaF alphaG h) ^ N * D 0) /
          (chewi109Rho alphaG h *
            ∑ n ∈ Finset.range N,
              (chewi109Lambda alphaF alphaG h) ^ (N - 1 - n)) +
        err / h := by
  let A : ℝ := chewi109Lambda alphaF alphaG h
  let rho : ℝ := chewi109Rho alphaG h
  have hrho_pos : 0 < rho := by
    dsimp [rho, chewi109Rho]
    exact div_pos hh hden_pos
  have hrec : ∀ n, n < N ->
      D (n + 1) ≤ A * D n - rho * gap (n + 1) + err / (1 + alphaG * h) := by
    intro n hn
    have hstep := hone_step n hn
    have hdiv :
        D (n + 1) ≤
          ((1 - alphaF * h) * D n - h * gap (n + 1) + err) /
            (1 + alphaG * h) := by
      have hstep' :
          D (n + 1) * (1 + alphaG * h) ≤
            (1 - alphaF * h) * D n - h * gap (n + 1) + err := by
        simpa [mul_comm, mul_left_comm, mul_assoc] using hstep
      exact (le_div_iff₀ hden_pos).2 hstep'
    calc
      D (n + 1) ≤
          ((1 - alphaF * h) * D n - h * gap (n + 1) + err) /
            (1 + alphaG * h) := hdiv
      _ = A * D n - rho * gap (n + 1) + err / (1 + alphaG * h) := by
          dsimp [A, rho, chewi109Lambda, chewi109Rho]
          field_simp [hden_pos.ne']
  have hmain :=
    chewi121_weightedAverageGap_le_of_oneStep
      (A := A) (rho := rho) (err := err / (1 + alphaG * h))
      (by simpa [A] using hlambda_nonneg) hrho_pos D gap hN hD_N_nonneg hrec
  have herr :
      (err / (1 + alphaG * h)) / rho = err / h := by
    dsimp [rho, chewi109Rho]
    field_simp [hh.ne', hden_pos.ne']
  simpa [A, rho, herr] using hmain

/--
Chewi Theorem 12.1 one-step algebra from the three expected model bounds in
the proof: relative growth of `psi_x`, the upper bound on `E psi_x(y)`, and
the lower bound on `E psi_x(x+)` up to a stochastic error floor.
-/
theorem chewi121_source_oneStep_of_model_bounds
    {alphaF alphaG h Dcur Dnext Fstar gap psiNext psiStar modelError : ℝ}
    (hh : 0 < h)
    (hgrowth : (alphaG + 1 / h) * Dnext + psiNext ≤ psiStar)
    (hstar_upper : psiStar ≤ Fstar + ((1 - alphaF * h) / h) * Dcur)
    (hnext_lower : Fstar + gap - modelError ≤ psiNext) :
    (1 + alphaG * h) * Dnext ≤
      (1 - alphaF * h) * Dcur - h * gap + h * modelError := by
  have hmodel :
      (alphaG + 1 / h) * Dnext + (Fstar + gap - modelError) ≤
        Fstar + ((1 - alphaF * h) / h) * Dcur := by
    calc
      (alphaG + 1 / h) * Dnext + (Fstar + gap - modelError)
          ≤ (alphaG + 1 / h) * Dnext + psiNext := by
              nlinarith
      _ ≤ psiStar := hgrowth
      _ ≤ Fstar + ((1 - alphaF * h) / h) * Dcur := hstar_upper
  have hmul :
      (1 + alphaG * h) * Dnext + h * Fstar + h * gap - h * modelError ≤
        h * Fstar + (1 - alphaF * h) * Dcur := by
    have hleft :
        h * ((alphaG + 1 / h) * Dnext + (Fstar + gap - modelError)) =
          (1 + alphaG * h) * Dnext + h * Fstar + h * gap -
            h * modelError := by
      field_simp [hh.ne']
      ring
    have hright :
        h * (Fstar + ((1 - alphaF * h) / h) * Dcur) =
          h * Fstar + (1 - alphaF * h) * Dcur := by
      field_simp [hh.ne']
    calc
      (1 + alphaG * h) * Dnext + h * Fstar + h * gap - h * modelError
          = h * ((alphaG + 1 / h) * Dnext + (Fstar + gap - modelError)) :=
              hleft.symm
      _ ≤ h * (Fstar + ((1 - alphaF * h) / h) * Dcur) :=
              mul_le_mul_of_nonneg_left hmodel hh.le
      _ = h * Fstar + (1 - alphaF * h) * Dcur := hright
  nlinarith

/--
Chewi Theorem 12.1 weighted-average bound in the closed geometric-denominator
form, from the displayed source one-step recurrence.
-/
theorem chewi121_weightedAverageGap_le_geometric_of_source_oneStep
    {alphaF alphaG h err : ℝ}
    (htotal_pos : 0 < alphaF + alphaG)
    (hh : 0 < h) (hden_pos : 0 < 1 + alphaG * h)
    (hlambda_pos : 0 < chewi109Lambda alphaF alphaG h)
    (D gap : ℕ -> ℝ) {N : ℕ} (hN : N ≠ 0)
    (hD_N_nonneg : 0 ≤ D N)
    (hone_step : ∀ n, n < N ->
      (1 + alphaG * h) * D (n + 1) ≤
        (1 - alphaF * h) * D n - h * gap (n + 1) + err) :
    (1 / (∑ n ∈ Finset.range N,
          (chewi109Lambda alphaF alphaG h) ^ (N - 1 - n))) *
        (∑ n ∈ Finset.range N,
          (chewi109Lambda alphaF alphaG h) ^ (N - 1 - n) * gap (n + 1)) ≤
      (alphaF + alphaG) /
          (((chewi109Lambda alphaF alphaG h) ^ N)⁻¹ - 1) * D 0 +
        err / h := by
  let A : ℝ := chewi109Lambda alphaF alphaG h
  let rho : ℝ := chewi109Rho alphaG h
  have hrho_pos : 0 < rho := by
    dsimp [rho, chewi109Rho]
    exact div_pos hh hden_pos
  have hA_eq : A = 1 - (alphaF + alphaG) * rho := by
    have hden_ne_comm : 1 + h * alphaG ≠ 0 := by
      nlinarith [hden_pos]
    dsimp [A, rho, chewi109Lambda, chewi109Rho]
    field_simp [hden_pos.ne', hden_ne_comm]
    ring
  have hA_lt_one : A < 1 := by
    rw [hA_eq]
    have hmul_pos : 0 < (alphaF + alphaG) * rho := mul_pos htotal_pos hrho_pos
    nlinarith
  have hA_ne_one : A ≠ 1 := ne_of_lt hA_lt_one
  have hA_pow_pos : 0 < A ^ N := pow_pos (by simpa [A] using hlambda_pos) N
  have hA_pow_ne : A ^ N ≠ 0 := hA_pow_pos.ne'
  have hA_pow_lt_one : A ^ N < 1 :=
    pow_lt_one₀ (by positivity) hA_lt_one hN
  have hone_sub_pow_ne : 1 - A ^ N ≠ 0 := by
    nlinarith
  have hfinite :=
    chewi121_weightedAverageGap_le_of_source_oneStep
      (alphaF := alphaF) (alphaG := alphaG) (h := h) (err := err)
      hh hden_pos hlambda_pos.le D gap hN hD_N_nonneg hone_step
  have hsum :
      (∑ n ∈ Finset.range N, A ^ (N - 1 - n)) =
        (1 - A ^ N) / (1 - A) :=
    geometricWeights_sum_eq_div hA_ne_one N
  have hone_sub_A : 1 - A = (alphaF + alphaG) * rho := by
    rw [hA_eq]
    ring
  have hfirst :
      (A ^ N * D 0) /
          (rho * ∑ n ∈ Finset.range N, A ^ (N - 1 - n)) =
        (alphaF + alphaG) / ((A ^ N)⁻¹ - 1) * D 0 := by
    rw [hsum, hone_sub_A]
    field_simp [htotal_pos.ne', hrho_pos.ne', hA_pow_ne, hone_sub_pow_ne]
  have hrhs :
      (A ^ N * D 0) /
          (rho * ∑ n ∈ Finset.range N, A ^ (N - 1 - n)) + err / h =
        (alphaF + alphaG) / ((A ^ N)⁻¹ - 1) * D 0 + err / h := by
    rw [hfirst]
  simpa [A, rho] using hfinite.trans_eq hrhs

/--
Chewi Theorem 12.1 source-rate theorem from expected model bounds.  This
packages the proof skeleton before the smooth/non-smooth stochastic estimates
discharge `modelError`.
-/
theorem chewi121_weightedAverageGap_le_geometric_of_model_bounds
    {alphaF alphaG h modelError Fstar : ℝ}
    (htotal_pos : 0 < alphaF + alphaG)
    (hh : 0 < h) (hden_pos : 0 < 1 + alphaG * h)
    (hlambda_pos : 0 < chewi109Lambda alphaF alphaG h)
    (D gap psiNext psiStar : ℕ -> ℝ) {N : ℕ} (hN : N ≠ 0)
    (hD_N_nonneg : 0 ≤ D N)
    (hgrowth : ∀ n, n < N ->
      (alphaG + 1 / h) * D (n + 1) + psiNext n ≤ psiStar n)
    (hstar_upper : ∀ n, n < N ->
      psiStar n ≤ Fstar + ((1 - alphaF * h) / h) * D n)
    (hnext_lower : ∀ n, n < N ->
      Fstar + gap (n + 1) - modelError ≤ psiNext n) :
    (1 / (∑ n ∈ Finset.range N,
          (chewi109Lambda alphaF alphaG h) ^ (N - 1 - n))) *
        (∑ n ∈ Finset.range N,
          (chewi109Lambda alphaF alphaG h) ^ (N - 1 - n) * gap (n + 1)) ≤
      (alphaF + alphaG) /
          (((chewi109Lambda alphaF alphaG h) ^ N)⁻¹ - 1) * D 0 +
        modelError := by
  have hone_step : ∀ n, n < N ->
      (1 + alphaG * h) * D (n + 1) ≤
        (1 - alphaF * h) * D n - h * gap (n + 1) + h * modelError := by
    intro n hn
    exact
      chewi121_source_oneStep_of_model_bounds
        (alphaF := alphaF) (alphaG := alphaG) (h := h)
        (Dcur := D n) (Dnext := D (n + 1)) (Fstar := Fstar)
        (gap := gap (n + 1)) (psiNext := psiNext n)
        (psiStar := psiStar n) (modelError := modelError)
        hh (hgrowth n hn) (hstar_upper n hn) (hnext_lower n hn)
  have hmain :=
    chewi121_weightedAverageGap_le_geometric_of_source_oneStep
      (alphaF := alphaF) (alphaG := alphaG) (h := h)
      (err := h * modelError)
      htotal_pos hh hden_pos hlambda_pos D gap hN hD_N_nonneg hone_step
  have herr : h * modelError / h = modelError := by
    field_simp [hh.ne']
  simpa [herr] using hmain

/--
Smooth-case bridge from the stochastic lower model for `E psi_x(x+)` to the
exact `F_* + gap - error <= E psi_x(x+)` field consumed by the model-bound
recurrence.
-/
theorem chewi121_smooth_next_lower_of_expected_model_error
    {Fstar gap expectedNext psiNext sigma dim alphaPhi h : ℝ}
    (hmodel_lower :
      expectedNext - sigma ^ (2 : ℕ) * dim * h / alphaPhi ≤ psiNext)
    (hgap_sum : Fstar + gap = expectedNext) :
    Fstar + gap - sigma ^ (2 : ℕ) * dim * h / alphaPhi ≤ psiNext := by
  simpa [hgap_sum] using hmodel_lower

/--
Non-smooth-case bridge from the stochastic lower model for `E psi_x(x+)` to
the exact `F_* + gap - error <= E psi_x(x+)` field consumed by the model-bound
recurrence.
-/
theorem chewi121_nonsmooth_next_lower_of_expected_model_error
    {Fstar gap expectedNext psiNext L alphaPhi h : ℝ}
    (hmodel_lower :
      expectedNext - 2 * L ^ (2 : ℕ) * h / alphaPhi ≤ psiNext)
    (hgap_sum : Fstar + gap = expectedNext) :
    Fstar + gap - 2 * L ^ (2 : ℕ) * h / alphaPhi ≤ psiNext := by
  simpa [hgap_sum] using hmodel_lower

/--
Smooth-case completing-square estimate in Chewi Theorem 12.1:
the mirror strong-convexity quadratic with coefficient `alphaPhi/(4h)`
absorbs the Cauchy-Schwarz/RMS noise term at cost `varianceRms^2 h /
alphaPhi`.
-/
theorem chewi121_smooth_young_lower_bound
    {alphaPhi h varianceRms stepRms : ℝ}
    (hh : 0 < h) (halphaPhi : 0 < alphaPhi) :
    -(varianceRms ^ (2 : ℕ) * h / alphaPhi) ≤
      (alphaPhi / (4 * h)) * stepRms ^ (2 : ℕ) -
        varianceRms * stepRms := by
  have hden : 0 < 4 * h * alphaPhi := by positivity
  have hsquare : 0 ≤
      (alphaPhi * stepRms - 2 * varianceRms * h) ^ (2 : ℕ) :=
    sq_nonneg _
  have hnonneg :
      0 ≤
        (alphaPhi * stepRms - 2 * varianceRms * h) ^ (2 : ℕ) /
          (4 * h * alphaPhi) :=
    div_nonneg hsquare hden.le
  have hidentity :
      (alphaPhi * stepRms - 2 * varianceRms * h) ^ (2 : ℕ) /
          (4 * h * alphaPhi) =
        (alphaPhi / (4 * h)) * stepRms ^ (2 : ℕ) -
          varianceRms * stepRms +
            varianceRms ^ (2 : ℕ) * h / alphaPhi := by
    field_simp [hh.ne', halphaPhi.ne']
    ring
  rw [hidentity] at hnonneg
  nlinarith

/--
Smooth expected-model lower estimate from Chewi's RMS proof state.  The
probability layer should provide `hcore` by relative smoothness, mirror
strong convexity, and Cauchy-Schwarz, plus `hvariance` from the variance
assumption `(12.1)`.
-/
theorem chewi121_smooth_expected_model_lower_of_rms_bound
    {alphaPhi sigma dim h varianceRms stepRms expectedNext psiNext : ℝ}
    (hh : 0 < h) (halphaPhi : 0 < alphaPhi)
    (hvariance : varianceRms ^ (2 : ℕ) ≤ sigma ^ (2 : ℕ) * dim)
    (hcore :
      expectedNext + (alphaPhi / (4 * h)) * stepRms ^ (2 : ℕ) -
          varianceRms * stepRms ≤ psiNext) :
    expectedNext - sigma ^ (2 : ℕ) * dim * h / alphaPhi ≤ psiNext := by
  have hyoung :=
    chewi121_smooth_young_lower_bound
      (alphaPhi := alphaPhi) (h := h) (varianceRms := varianceRms)
      (stepRms := stepRms) hh halphaPhi
  have hlocal_lower :
      expectedNext - varianceRms ^ (2 : ℕ) * h / alphaPhi ≤
        expectedNext + (alphaPhi / (4 * h)) * stepRms ^ (2 : ℕ) -
          varianceRms * stepRms := by
    nlinarith
  have hscale_nonneg : 0 ≤ h / alphaPhi :=
    div_nonneg hh.le halphaPhi.le
  have herror :
      varianceRms ^ (2 : ℕ) * h / alphaPhi ≤
        sigma ^ (2 : ℕ) * dim * h / alphaPhi := by
    have hscaled :
        varianceRms ^ (2 : ℕ) * (h / alphaPhi) ≤
          (sigma ^ (2 : ℕ) * dim) * (h / alphaPhi) :=
      mul_le_mul_of_nonneg_right hvariance hscale_nonneg
    calc
      varianceRms ^ (2 : ℕ) * h / alphaPhi =
          varianceRms ^ (2 : ℕ) * (h / alphaPhi) := by ring
      _ ≤ (sigma ^ (2 : ℕ) * dim) * (h / alphaPhi) := hscaled
      _ = sigma ^ (2 : ℕ) * dim * h / alphaPhi := by ring
  exact (sub_le_sub_left herror expectedNext).trans (hlocal_lower.trans hcore)

/--
Non-smooth expected-model lower estimate from Chewi's bounded-gradient RMS
proof state, reusing the Chapter 10.11 completing-square inequality.
-/
theorem chewi121_nonsmooth_expected_model_lower_of_rms_bound
    {alphaPhi L h stepRms expectedNext psiNext : ℝ}
    (hh : 0 < h) (halphaPhi : 0 < alphaPhi)
    (hcore :
      expectedNext + (alphaPhi / (2 * h)) * stepRms ^ (2 : ℕ) -
          (2 * L) * stepRms ≤ psiNext) :
    expectedNext - 2 * L ^ (2 : ℕ) * h / alphaPhi ≤ psiNext := by
  have hyoung :=
    chewi1011_young_lower_bound
      (L := L) (alphaPhi := alphaPhi) (h := h) (r := stepRms)
      hh halphaPhi
  have hlocal_lower :
      expectedNext - 2 * L ^ (2 : ℕ) * h / alphaPhi ≤
        expectedNext + (alphaPhi / (2 * h)) * stepRms ^ (2 : ℕ) -
          (2 * L) * stepRms := by
    nlinarith
  exact hlocal_lower.trans hcore

/--
Smooth-case `hcore` estimate from the expected model components in Chewi's
proof.  The later Bochner layer should supply `hraw`, the smooth absorption
`D_f <= (1/(2h)) D_phi`, the mirror strong-convexity lower bound, and the
Cauchy-Schwarz noise estimate.
-/
theorem chewi121_smooth_hcore_of_expected_components
    {alphaPhi h expectedNext psiNext DfAvg DphiAvg noiseTerm varianceRms
      stepRms : ℝ}
    (hh : 0 < h)
    (hraw :
      expectedNext - DfAvg + (1 / h) * DphiAvg - noiseTerm ≤ psiNext)
    (hdf_absorb : DfAvg ≤ (1 / (2 * h)) * DphiAvg)
    (hphi_lower :
      (alphaPhi / 2) * stepRms ^ (2 : ℕ) ≤ DphiAvg)
    (hnoise : noiseTerm ≤ varianceRms * stepRms) :
    expectedNext + (alphaPhi / (4 * h)) * stepRms ^ (2 : ℕ) -
        varianceRms * stepRms ≤ psiNext := by
  have hscale_nonneg : 0 ≤ 1 / (2 * h) := by positivity
  have hphi_scaled :
      (alphaPhi / (4 * h)) * stepRms ^ (2 : ℕ) ≤
        (1 / (2 * h)) * DphiAvg := by
    have hmul := mul_le_mul_of_nonneg_left hphi_lower hscale_nonneg
    calc
      (alphaPhi / (4 * h)) * stepRms ^ (2 : ℕ) =
          (1 / (2 * h)) * ((alphaPhi / 2) * stepRms ^ (2 : ℕ)) := by
            field_simp [hh.ne']
            ring
      _ ≤ (1 / (2 * h)) * DphiAvg := hmul
  have hquad_model :
      (alphaPhi / (4 * h)) * stepRms ^ (2 : ℕ) ≤
        -DfAvg + (1 / h) * DphiAvg := by
    calc
      (alphaPhi / (4 * h)) * stepRms ^ (2 : ℕ) ≤
          (1 / (2 * h)) * DphiAvg := hphi_scaled
      _ = -(1 / (2 * h)) * DphiAvg + (1 / h) * DphiAvg := by
            field_simp [hh.ne']
            ring
      _ ≤ -DfAvg + (1 / h) * DphiAvg := by
            nlinarith
  have hleft :
      expectedNext + (alphaPhi / (4 * h)) * stepRms ^ (2 : ℕ) -
          varianceRms * stepRms ≤
        expectedNext - DfAvg + (1 / h) * DphiAvg - noiseTerm := by
    nlinarith
  exact hleft.trans hraw

/--
Non-smooth-case `hcore` estimate from Chewi's expected model components.  The
two linear terms correspond to Lipschitzness of `f` and the bounded stochastic
gradient term.
-/
theorem chewi121_nonsmooth_hcore_of_expected_components
    {alphaPhi L h expectedNext psiNext DphiAvg lipTerm gradTerm stepRms : ℝ}
    (hh : 0 < h)
    (hraw :
      expectedNext - lipTerm - gradTerm + (1 / h) * DphiAvg ≤ psiNext)
    (hphi_lower :
      (alphaPhi / 2) * stepRms ^ (2 : ℕ) ≤ DphiAvg)
    (hlip : lipTerm ≤ L * stepRms)
    (hgrad : gradTerm ≤ L * stepRms) :
    expectedNext + (alphaPhi / (2 * h)) * stepRms ^ (2 : ℕ) -
        (2 * L) * stepRms ≤ psiNext := by
  have hscale_nonneg : 0 ≤ 1 / h := by positivity
  have hphi_scaled :
      (alphaPhi / (2 * h)) * stepRms ^ (2 : ℕ) ≤
        (1 / h) * DphiAvg := by
    have hmul := mul_le_mul_of_nonneg_left hphi_lower hscale_nonneg
    calc
      (alphaPhi / (2 * h)) * stepRms ^ (2 : ℕ) =
          (1 / h) * ((alphaPhi / 2) * stepRms ^ (2 : ℕ)) := by
            field_simp [hh.ne']
      _ ≤ (1 / h) * DphiAvg := hmul
  have hleft :
      expectedNext + (alphaPhi / (2 * h)) * stepRms ^ (2 : ℕ) -
          (2 * L) * stepRms ≤
        expectedNext - lipTerm - gradTerm + (1 / h) * DphiAvg := by
    nlinarith
  exact hleft.trans hraw

/--
Finite-support smooth raw expected-model bound.  This is the finite-probability
analogue of the first equality/inequality in Chewi's smooth SMPGD lower-bound
display, after the pointwise model inequality has been proved for every sampled
stochastic gradient.
-/
theorem chewi121_smooth_finite_raw_component_bound
    {ι : Type*} [DecidableEq ι] (s : Finset ι)
    {w Fplus Df Dphi noise psi : ι -> ℝ} {h psiNext : ℝ}
    (hw_nonneg : ∀ i ∈ s, 0 ≤ w i)
    (hpoint : ∀ i ∈ s,
      Fplus i - Df i + (1 / h) * Dphi i - noise i ≤ psi i)
    (hpsi : (∑ i ∈ s, w i * psi i) ≤ psiNext) :
    (∑ i ∈ s, w i * Fplus i) - (∑ i ∈ s, w i * Df i) +
        (1 / h) * (∑ i ∈ s, w i * Dphi i) -
          (∑ i ∈ s, w i * noise i) ≤ psiNext := by
  have hsum :
      (∑ i ∈ s, w i *
        (Fplus i - Df i + (1 / h) * Dphi i - noise i)) ≤
        ∑ i ∈ s, w i * psi i := by
    refine Finset.sum_le_sum ?_
    intro i hi
    exact mul_le_mul_of_nonneg_left (hpoint i hi) (hw_nonneg i hi)
  have hsum_eq :
      (∑ i ∈ s, w i *
        (Fplus i - Df i + (1 / h) * Dphi i - noise i)) =
        (∑ i ∈ s, w i * Fplus i) - (∑ i ∈ s, w i * Df i) +
          (1 / h) * (∑ i ∈ s, w i * Dphi i) -
            (∑ i ∈ s, w i * noise i) := by
    calc
      (∑ i ∈ s, w i *
        (Fplus i - Df i + (1 / h) * Dphi i - noise i))
          =
        ∑ i ∈ s,
          (w i * Fplus i - w i * Df i +
            (1 / h) * (w i * Dphi i) - w i * noise i) := by
            refine Finset.sum_congr rfl ?_
            intro i hi
            ring
      _ =
        (∑ i ∈ s, w i * Fplus i) - (∑ i ∈ s, w i * Df i) +
          (1 / h) * (∑ i ∈ s, w i * Dphi i) -
            (∑ i ∈ s, w i * noise i) := by
            rw [Finset.sum_sub_distrib, Finset.sum_add_distrib,
              Finset.sum_sub_distrib, Finset.mul_sum]
  exact hsum_eq ▸ hsum.trans hpsi

/--
Finite-support lifting of the smooth relative-smoothness absorption
`D_f <= (1/(2h)) D_phi`.
-/
theorem chewi121_smooth_finite_absorb_component_bound
    {ι : Type*} [DecidableEq ι] (s : Finset ι)
    {w Df Dphi : ι -> ℝ} {h : ℝ}
    (hw_nonneg : ∀ i ∈ s, 0 ≤ w i)
    (hpoint : ∀ i ∈ s, Df i ≤ (1 / (2 * h)) * Dphi i) :
    (∑ i ∈ s, w i * Df i) ≤
      (1 / (2 * h)) * (∑ i ∈ s, w i * Dphi i) := by
  have hsum :
      (∑ i ∈ s, w i * Df i) ≤
        ∑ i ∈ s, w i * ((1 / (2 * h)) * Dphi i) := by
    refine Finset.sum_le_sum ?_
    intro i hi
    exact mul_le_mul_of_nonneg_left (hpoint i hi) (hw_nonneg i hi)
  have hsum_eq :
      (∑ i ∈ s, w i * ((1 / (2 * h)) * Dphi i)) =
        (1 / (2 * h)) * (∑ i ∈ s, w i * Dphi i) := by
    rw [Finset.mul_sum]
    refine Finset.sum_congr rfl ?_
    intro i hi
    ring
  exact hsum.trans_eq hsum_eq

/--
Finite-support lifting of the mirror strong-convexity lower bound
`D_phi >= alpha_phi / 2 * ||x+ - x||^2`.
-/
theorem chewi121_finite_mirror_lower_component_bound
    {ι : Type*} [DecidableEq ι] (s : Finset ι)
    {w Dphi stepSq : ι -> ℝ} {alphaPhi stepRms : ℝ}
    (halphaPhi_nonneg : 0 ≤ alphaPhi)
    (hw_nonneg : ∀ i ∈ s, 0 ≤ w i)
    (hstepRms_sq :
      stepRms ^ (2 : ℕ) ≤ ∑ i ∈ s, w i * stepSq i)
    (hpoint : ∀ i ∈ s, (alphaPhi / 2) * stepSq i ≤ Dphi i) :
    (alphaPhi / 2) * stepRms ^ (2 : ℕ) ≤
      ∑ i ∈ s, w i * Dphi i := by
  have hcoef_nonneg : 0 ≤ alphaPhi / 2 := by positivity
  have hsum :
      (∑ i ∈ s, w i * ((alphaPhi / 2) * stepSq i)) ≤
        ∑ i ∈ s, w i * Dphi i := by
    refine Finset.sum_le_sum ?_
    intro i hi
    exact mul_le_mul_of_nonneg_left (hpoint i hi) (hw_nonneg i hi)
  have hsum_eq :
      (∑ i ∈ s, w i * ((alphaPhi / 2) * stepSq i)) =
        (alphaPhi / 2) * (∑ i ∈ s, w i * stepSq i) := by
    rw [Finset.mul_sum]
    refine Finset.sum_congr rfl ?_
    intro i hi
    ring
  calc
    (alphaPhi / 2) * stepRms ^ (2 : ℕ) ≤
        (alphaPhi / 2) * (∑ i ∈ s, w i * stepSq i) :=
          mul_le_mul_of_nonneg_left hstepRms_sq hcoef_nonneg
    _ = ∑ i ∈ s, w i * ((alphaPhi / 2) * stepSq i) := hsum_eq.symm
    _ ≤ ∑ i ∈ s, w i * Dphi i := hsum

/-- Finite-support non-smooth raw expected-model bound. -/
theorem chewi121_nonsmooth_finite_raw_component_bound
    {ι : Type*} [DecidableEq ι] (s : Finset ι)
    {w Fplus lip grad Dphi psi : ι -> ℝ} {h psiNext : ℝ}
    (hw_nonneg : ∀ i ∈ s, 0 ≤ w i)
    (hpoint : ∀ i ∈ s,
      Fplus i - lip i - grad i + (1 / h) * Dphi i ≤ psi i)
    (hpsi : (∑ i ∈ s, w i * psi i) ≤ psiNext) :
    (∑ i ∈ s, w i * Fplus i) - (∑ i ∈ s, w i * lip i) -
        (∑ i ∈ s, w i * grad i) +
          (1 / h) * (∑ i ∈ s, w i * Dphi i) ≤ psiNext := by
  have hsum :
      (∑ i ∈ s, w i *
        (Fplus i - lip i - grad i + (1 / h) * Dphi i)) ≤
        ∑ i ∈ s, w i * psi i := by
    refine Finset.sum_le_sum ?_
    intro i hi
    exact mul_le_mul_of_nonneg_left (hpoint i hi) (hw_nonneg i hi)
  have hsum_eq :
      (∑ i ∈ s, w i *
        (Fplus i - lip i - grad i + (1 / h) * Dphi i)) =
        (∑ i ∈ s, w i * Fplus i) - (∑ i ∈ s, w i * lip i) -
          (∑ i ∈ s, w i * grad i) +
            (1 / h) * (∑ i ∈ s, w i * Dphi i) := by
    calc
      (∑ i ∈ s, w i *
        (Fplus i - lip i - grad i + (1 / h) * Dphi i))
          =
        ∑ i ∈ s,
          (w i * Fplus i - w i * lip i - w i * grad i +
            (1 / h) * (w i * Dphi i)) := by
            refine Finset.sum_congr rfl ?_
            intro i hi
            ring
      _ =
        (∑ i ∈ s, w i * Fplus i) - (∑ i ∈ s, w i * lip i) -
          (∑ i ∈ s, w i * grad i) +
            (1 / h) * (∑ i ∈ s, w i * Dphi i) := by
            rw [Finset.sum_add_distrib, Finset.sum_sub_distrib,
              Finset.sum_sub_distrib, Finset.mul_sum]
  exact hsum_eq ▸ hsum.trans hpsi

/--
Finite-support lifting for one linear non-smooth term, e.g. the Lipschitz term
or the stochastic-gradient term.
-/
theorem chewi121_finite_linear_component_bound
    {ι : Type*} [DecidableEq ι] (s : Finset ι)
    {w term stepNorm : ι -> ℝ} {L stepRms : ℝ}
    (hL_nonneg : 0 ≤ L)
    (hw_nonneg : ∀ i ∈ s, 0 ≤ w i)
    (hstep_avg : (∑ i ∈ s, w i * stepNorm i) ≤ stepRms)
    (hpoint : ∀ i ∈ s, term i ≤ L * stepNorm i) :
    (∑ i ∈ s, w i * term i) ≤ L * stepRms := by
  have hsum :
      (∑ i ∈ s, w i * term i) ≤
        ∑ i ∈ s, w i * (L * stepNorm i) := by
    refine Finset.sum_le_sum ?_
    intro i hi
    exact mul_le_mul_of_nonneg_left (hpoint i hi) (hw_nonneg i hi)
  have hsum_eq :
      (∑ i ∈ s, w i * (L * stepNorm i)) =
        L * (∑ i ∈ s, w i * stepNorm i) := by
    rw [Finset.mul_sum]
    refine Finset.sum_congr rfl ?_
    intro i hi
    ring
  calc
    (∑ i ∈ s, w i * term i) ≤ ∑ i ∈ s, w i * (L * stepNorm i) := hsum
    _ = L * (∑ i ∈ s, w i * stepNorm i) := hsum_eq
    _ ≤ L * stepRms := mul_le_mul_of_nonneg_left hstep_avg hL_nonneg

/--
Finite-support smooth `hcore` theorem.  The hypotheses are exactly the
per-sample model inequality, relative-smoothness absorption, mirror lower
bound, and a supplied finite Cauchy-Schwarz noise estimate.
-/
theorem chewi121_smooth_hcore_of_finite_components
    {ι : Type*} [DecidableEq ι] (s : Finset ι)
    {w Fplus Df Dphi noise psi stepSq : ι -> ℝ}
    {alphaPhi h psiNext varianceRms stepRms : ℝ}
    (hh : 0 < h) (halphaPhi_nonneg : 0 ≤ alphaPhi)
    (hw_nonneg : ∀ i ∈ s, 0 ≤ w i)
    (hraw_point : ∀ i ∈ s,
      Fplus i - Df i + (1 / h) * Dphi i - noise i ≤ psi i)
    (hpsi : (∑ i ∈ s, w i * psi i) ≤ psiNext)
    (hdf_point : ∀ i ∈ s, Df i ≤ (1 / (2 * h)) * Dphi i)
    (hstepRms_sq :
      stepRms ^ (2 : ℕ) ≤ ∑ i ∈ s, w i * stepSq i)
    (hphi_point : ∀ i ∈ s, (alphaPhi / 2) * stepSq i ≤ Dphi i)
    (hnoise : (∑ i ∈ s, w i * noise i) ≤ varianceRms * stepRms) :
    (∑ i ∈ s, w i * Fplus i) +
        (alphaPhi / (4 * h)) * stepRms ^ (2 : ℕ) -
          varianceRms * stepRms ≤ psiNext := by
  have hraw :=
    chewi121_smooth_finite_raw_component_bound
      (s := s) (w := w) (Fplus := Fplus) (Df := Df) (Dphi := Dphi)
      (noise := noise) (psi := psi) (h := h) (psiNext := psiNext)
      hw_nonneg hraw_point hpsi
  have hdf_absorb :=
    chewi121_smooth_finite_absorb_component_bound
      (s := s) (w := w) (Df := Df) (Dphi := Dphi) (h := h)
      hw_nonneg hdf_point
  have hphi_lower :=
    chewi121_finite_mirror_lower_component_bound
      (s := s) (w := w) (Dphi := Dphi) (stepSq := stepSq)
      (alphaPhi := alphaPhi) (stepRms := stepRms)
      halphaPhi_nonneg hw_nonneg hstepRms_sq hphi_point
  exact
    chewi121_smooth_hcore_of_expected_components
      (alphaPhi := alphaPhi) (h := h)
      (expectedNext := ∑ i ∈ s, w i * Fplus i) (psiNext := psiNext)
      (DfAvg := ∑ i ∈ s, w i * Df i)
      (DphiAvg := ∑ i ∈ s, w i * Dphi i)
      (noiseTerm := ∑ i ∈ s, w i * noise i)
      (varianceRms := varianceRms) (stepRms := stepRms)
      hh hraw hdf_absorb hphi_lower hnoise

/--
Finite-support non-smooth `hcore` theorem.  This packages the pointwise
Lipschitz and stochastic-gradient linear estimates into the scalar
component-hcore theorem.
-/
theorem chewi121_nonsmooth_hcore_of_finite_components
    {ι : Type*} [DecidableEq ι] (s : Finset ι)
    {w Fplus lip grad Dphi psi stepSq stepNorm : ι -> ℝ}
    {alphaPhi L h psiNext stepRms : ℝ}
    (hh : 0 < h) (halphaPhi_nonneg : 0 ≤ alphaPhi) (hL_nonneg : 0 ≤ L)
    (hw_nonneg : ∀ i ∈ s, 0 ≤ w i)
    (hraw_point : ∀ i ∈ s,
      Fplus i - lip i - grad i + (1 / h) * Dphi i ≤ psi i)
    (hpsi : (∑ i ∈ s, w i * psi i) ≤ psiNext)
    (hstepRms_sq :
      stepRms ^ (2 : ℕ) ≤ ∑ i ∈ s, w i * stepSq i)
    (hphi_point : ∀ i ∈ s, (alphaPhi / 2) * stepSq i ≤ Dphi i)
    (hstep_avg : (∑ i ∈ s, w i * stepNorm i) ≤ stepRms)
    (hlip_point : ∀ i ∈ s, lip i ≤ L * stepNorm i)
    (hgrad_point : ∀ i ∈ s, grad i ≤ L * stepNorm i) :
    (∑ i ∈ s, w i * Fplus i) +
        (alphaPhi / (2 * h)) * stepRms ^ (2 : ℕ) -
          (2 * L) * stepRms ≤ psiNext := by
  have hraw :=
    chewi121_nonsmooth_finite_raw_component_bound
      (s := s) (w := w) (Fplus := Fplus) (lip := lip) (grad := grad)
      (Dphi := Dphi) (psi := psi) (h := h) (psiNext := psiNext)
      hw_nonneg hraw_point hpsi
  have hphi_lower :=
    chewi121_finite_mirror_lower_component_bound
      (s := s) (w := w) (Dphi := Dphi) (stepSq := stepSq)
      (alphaPhi := alphaPhi) (stepRms := stepRms)
      halphaPhi_nonneg hw_nonneg hstepRms_sq hphi_point
  have hlip :=
    chewi121_finite_linear_component_bound
      (s := s) (w := w) (term := lip) (stepNorm := stepNorm)
      (L := L) (stepRms := stepRms)
      hL_nonneg hw_nonneg hstep_avg hlip_point
  have hgrad :=
    chewi121_finite_linear_component_bound
      (s := s) (w := w) (term := grad) (stepNorm := stepNorm)
      (L := L) (stepRms := stepRms)
      hL_nonneg hw_nonneg hstep_avg hgrad_point
  exact
    chewi121_nonsmooth_hcore_of_expected_components
      (alphaPhi := alphaPhi) (L := L) (h := h)
      (expectedNext := ∑ i ∈ s, w i * Fplus i) (psiNext := psiNext)
      (DphiAvg := ∑ i ∈ s, w i * Dphi i)
      (lipTerm := ∑ i ∈ s, w i * lip i)
      (gradTerm := ∑ i ∈ s, w i * grad i)
      (stepRms := stepRms)
      hh hraw hphi_lower hlip hgrad

/--
Bochner-integral smooth raw expected-model bound.  This is the measure-level
version of `chewi121_smooth_finite_raw_component_bound`; the pointwise or
almost-everywhere stochastic model inequality is lifted by `integral_mono_ae`.
-/
theorem chewi121_smooth_integral_raw_component_bound
    {Ω : Type*} [MeasurableSpace Ω] {μ : Measure Ω}
    {Fplus Df Dphi noise psi : Ω -> ℝ} {h psiNext : ℝ}
    (hFplus : Integrable Fplus μ) (hDf : Integrable Df μ)
    (hDphi : Integrable Dphi μ) (hnoise_int : Integrable noise μ)
    (hpsi_int : Integrable psi μ)
    (hpoint : (fun ω =>
      Fplus ω - Df ω + (1 / h) * Dphi ω - noise ω) ≤ᵐ[μ] psi)
    (hpsi : (∫ ω, psi ω ∂μ) ≤ psiNext) :
    (∫ ω, Fplus ω ∂μ) - (∫ ω, Df ω ∂μ) +
        (1 / h) * (∫ ω, Dphi ω ∂μ) -
          (∫ ω, noise ω ∂μ) ≤ psiNext := by
  have hFD : Integrable (fun ω => Fplus ω - Df ω) μ := hFplus.sub hDf
  have hscaled : Integrable (fun ω => (1 / h) * Dphi ω) μ :=
    hDphi.const_mul _
  have hpre :
      Integrable (fun ω => Fplus ω - Df ω + (1 / h) * Dphi ω) μ :=
    hFD.add hscaled
  have hcomb :
      Integrable (fun ω =>
        Fplus ω - Df ω + (1 / h) * Dphi ω - noise ω) μ :=
    hpre.sub hnoise_int
  have hmono : (∫ ω, Fplus ω - Df ω + (1 / h) * Dphi ω - noise ω ∂μ) ≤
      ∫ ω, psi ω ∂μ :=
    integral_mono_ae hcomb hpsi_int hpoint
  have hsplit :
      (∫ ω, Fplus ω - Df ω + (1 / h) * Dphi ω - noise ω ∂μ) =
        (∫ ω, Fplus ω ∂μ) - (∫ ω, Df ω ∂μ) +
          (1 / h) * (∫ ω, Dphi ω ∂μ) -
            (∫ ω, noise ω ∂μ) := by
    rw [integral_sub hpre hnoise_int, integral_add hFD hscaled,
      integral_sub hFplus hDf, integral_const_mul]
  exact hsplit ▸ hmono.trans hpsi

/--
Bochner-integral lifting of the smooth relative-smoothness absorption
`D_f <= (1/(2h)) D_phi`.
-/
theorem chewi121_smooth_integral_absorb_component_bound
    {Ω : Type*} [MeasurableSpace Ω] {μ : Measure Ω}
    {Df Dphi : Ω -> ℝ} {h : ℝ}
    (hDf : Integrable Df μ) (hDphi : Integrable Dphi μ)
    (hpoint : Df ≤ᵐ[μ] fun ω => (1 / (2 * h)) * Dphi ω) :
    (∫ ω, Df ω ∂μ) ≤ (1 / (2 * h)) * (∫ ω, Dphi ω ∂μ) := by
  have hscaled : Integrable (fun ω => (1 / (2 * h)) * Dphi ω) μ :=
    hDphi.const_mul _
  have hmono := integral_mono_ae hDf hscaled hpoint
  simpa [integral_const_mul] using hmono

/--
Bochner-integral lifting of the mirror strong-convexity lower bound
`D_phi >= alpha_phi / 2 * ||x+ - x||^2`.
-/
theorem chewi121_integral_mirror_lower_component_bound
    {Ω : Type*} [MeasurableSpace Ω] {μ : Measure Ω}
    {Dphi stepSq : Ω -> ℝ} {alphaPhi stepRms : ℝ}
    (halphaPhi_nonneg : 0 ≤ alphaPhi)
    (hDphi : Integrable Dphi μ) (hstepSq : Integrable stepSq μ)
    (hstepRms_sq : stepRms ^ (2 : ℕ) ≤ ∫ ω, stepSq ω ∂μ)
    (hpoint : (fun ω => (alphaPhi / 2) * stepSq ω) ≤ᵐ[μ] Dphi) :
    (alphaPhi / 2) * stepRms ^ (2 : ℕ) ≤ ∫ ω, Dphi ω ∂μ := by
  have hcoef_nonneg : 0 ≤ alphaPhi / 2 := by positivity
  have hscaled : Integrable (fun ω => (alphaPhi / 2) * stepSq ω) μ :=
    hstepSq.const_mul _
  have hmono := integral_mono_ae hscaled hDphi hpoint
  calc
    (alphaPhi / 2) * stepRms ^ (2 : ℕ) ≤
        (alphaPhi / 2) * (∫ ω, stepSq ω ∂μ) :=
          mul_le_mul_of_nonneg_left hstepRms_sq hcoef_nonneg
    _ = ∫ ω, (alphaPhi / 2) * stepSq ω ∂μ := by
          rw [integral_const_mul]
    _ ≤ ∫ ω, Dphi ω ∂μ := hmono

/-- Bochner-integral non-smooth raw expected-model bound. -/
theorem chewi121_nonsmooth_integral_raw_component_bound
    {Ω : Type*} [MeasurableSpace Ω] {μ : Measure Ω}
    {Fplus lip grad Dphi psi : Ω -> ℝ} {h psiNext : ℝ}
    (hFplus : Integrable Fplus μ) (hlip_int : Integrable lip μ)
    (hgrad_int : Integrable grad μ) (hDphi : Integrable Dphi μ)
    (hpsi_int : Integrable psi μ)
    (hpoint : (fun ω =>
      Fplus ω - lip ω - grad ω + (1 / h) * Dphi ω) ≤ᵐ[μ] psi)
    (hpsi : (∫ ω, psi ω ∂μ) ≤ psiNext) :
    (∫ ω, Fplus ω ∂μ) - (∫ ω, lip ω ∂μ) -
        (∫ ω, grad ω ∂μ) + (1 / h) * (∫ ω, Dphi ω ∂μ) ≤
      psiNext := by
  have hFl : Integrable (fun ω => Fplus ω - lip ω) μ :=
    hFplus.sub hlip_int
  have hFlg : Integrable (fun ω => Fplus ω - lip ω - grad ω) μ :=
    hFl.sub hgrad_int
  have hscaled : Integrable (fun ω => (1 / h) * Dphi ω) μ :=
    hDphi.const_mul _
  have hcomb :
      Integrable (fun ω => Fplus ω - lip ω - grad ω + (1 / h) * Dphi ω) μ :=
    hFlg.add hscaled
  have hmono :
      (∫ ω, Fplus ω - lip ω - grad ω + (1 / h) * Dphi ω ∂μ) ≤
        ∫ ω, psi ω ∂μ :=
    integral_mono_ae hcomb hpsi_int hpoint
  have hsplit :
      (∫ ω, Fplus ω - lip ω - grad ω + (1 / h) * Dphi ω ∂μ) =
        (∫ ω, Fplus ω ∂μ) - (∫ ω, lip ω ∂μ) -
          (∫ ω, grad ω ∂μ) + (1 / h) * (∫ ω, Dphi ω ∂μ) := by
    rw [integral_add hFlg hscaled, integral_sub hFl hgrad_int,
      integral_sub hFplus hlip_int, integral_const_mul]
  exact hsplit ▸ hmono.trans hpsi

/--
Bochner-integral lifting for one linear non-smooth term, e.g. the Lipschitz
term or the stochastic-gradient term.
-/
theorem chewi121_integral_linear_component_bound
    {Ω : Type*} [MeasurableSpace Ω] {μ : Measure Ω}
    {term stepNorm : Ω -> ℝ} {L stepRms : ℝ}
    (hL_nonneg : 0 ≤ L)
    (hterm : Integrable term μ) (hstepNorm : Integrable stepNorm μ)
    (hstep_avg : (∫ ω, stepNorm ω ∂μ) ≤ stepRms)
    (hpoint : term ≤ᵐ[μ] fun ω => L * stepNorm ω) :
    (∫ ω, term ω ∂μ) ≤ L * stepRms := by
  have hscaled : Integrable (fun ω => L * stepNorm ω) μ :=
    hstepNorm.const_mul _
  have hmono := integral_mono_ae hterm hscaled hpoint
  calc
    (∫ ω, term ω ∂μ) ≤ ∫ ω, L * stepNorm ω ∂μ := hmono
    _ = L * (∫ ω, stepNorm ω ∂μ) := by rw [integral_const_mul]
    _ ≤ L * stepRms := mul_le_mul_of_nonneg_left hstep_avg hL_nonneg

/--
Smooth sampled-model raw inequality for Chewi Theorem 12.1.  It rewrites the
local model with sampled oracle `p` into the smooth lower-model shape plus the
stochastic noise term.
-/
theorem chewi121_smooth_raw_point_of_sampled_model
    {E : Type*} [NormedAddCommGroup E] [InnerProductSpace ℝ E]
    {f g : E -> ℝ} {gradF : E -> E} {phi : E -> ℝ} {gradPhi : E -> E}
    {h noise : ℝ} {x xPlus p : E}
    (hnoise : -inner ℝ (p - gradF x) (xPlus - x) ≤ noise) :
    compositeObjective f g xPlus -
        bregmanDivergence f gradF xPlus x +
        (1 / h) * bregmanDivergence phi gradPhi xPlus x - noise ≤
      mirrorProximalGradientModel f g (fun _ : E => p) phi gradPhi h x xPlus := by
  unfold mirrorProximalGradientModel compositeObjective bregmanDivergence at *
  rw [inner_sub_left] at hnoise
  nlinarith

/--
Non-smooth sampled-model raw inequality for Chewi Theorem 12.1.  The two
source linear terms are left as supplied bounds, matching the later
Lipschitz/bounded-gradient route.
-/
theorem chewi121_nonsmooth_raw_point_of_sampled_model
    {E : Type*} [NormedAddCommGroup E] [InnerProductSpace ℝ E]
    {f g : E -> ℝ} {phi : E -> ℝ} {gradPhi : E -> E}
    {h lip grad : ℝ} {x xPlus p : E}
    (hlip : f xPlus - f x ≤ lip)
    (hgrad : -inner ℝ p (xPlus - x) ≤ grad) :
    compositeObjective f g xPlus - lip - grad +
        (1 / h) * bregmanDivergence phi gradPhi xPlus x ≤
      mirrorProximalGradientModel f g (fun _ : E => p) phi gradPhi h x xPlus := by
  unfold mirrorProximalGradientModel compositeObjective at *
  nlinarith

/--
Relative-smoothness absorption for the smooth SMPGD component proof:
`D_f(x+,x) <= beta_f D_phi(x+,x)` and `beta_f <= 1/(2h)`.
-/
theorem chewi121_smooth_absorb_of_relativeSmoothOn
    {E : Type*} [NormedAddCommGroup E] [InnerProductSpace ℝ E]
    {C : Set E} {f : E -> ℝ} {gradF : E -> E}
    {phi : E -> ℝ} {gradPhi : E -> E} {betaF h : ℝ} {x xPlus : E}
    (hsmooth : RelativelySmoothOn C f gradF phi gradPhi betaF)
    (hbeta : betaF ≤ 1 / (2 * h))
    (hDphi_nonneg : 0 ≤ bregmanDivergence phi gradPhi xPlus x)
    (hx : x ∈ C) (hxPlus : xPlus ∈ C) :
    bregmanDivergence f gradF xPlus x ≤
      (1 / (2 * h)) * bregmanDivergence phi gradPhi xPlus x := by
  have hrel := hsmooth hxPlus hx
  exact hrel.trans (mul_le_mul_of_nonneg_right hbeta hDphi_nonneg)

/--
Finite sampled growth inequality obtained by averaging the growth field of
each sampled mirror-proximal step.
-/
theorem chewi121_finite_sampled_growth_of_steps
    {E : Type*} [NormedAddCommGroup E] [InnerProductSpace ℝ E]
    {ι : Type*} [DecidableEq ι] (s : Finset ι)
    {C : Set E} {f g : E -> ℝ} {phi : E -> ℝ} {gradPhi : E -> E}
    {alphaG h : ℝ} {x y : E} {p xPlus : ι -> E} {w : ι -> ℝ}
    (hw_nonneg : ∀ i ∈ s, 0 ≤ w i)
    (hstep : ∀ i ∈ s,
      IsMirrorProximalGradientStep C f g (fun _ : E => p i)
        phi gradPhi alphaG h x (xPlus i))
    (hy : y ∈ C) :
    (alphaG + 1 / h) *
        (∑ i ∈ s, w i * bregmanDivergence phi gradPhi y (xPlus i)) +
      (∑ i ∈ s, w i *
        mirrorProximalGradientModel f g (fun _ : E => p i)
          phi gradPhi h x (xPlus i)) ≤
    ∑ i ∈ s, w i *
      mirrorProximalGradientModel f g (fun _ : E => p i) phi gradPhi h x y := by
  have hsum :
      (∑ i ∈ s, w i *
        (mirrorProximalGradientModel f g (fun _ : E => p i) phi gradPhi h x (xPlus i) +
          (alphaG + 1 / h) * bregmanDivergence phi gradPhi y (xPlus i))) ≤
        ∑ i ∈ s, w i *
          mirrorProximalGradientModel f g (fun _ : E => p i) phi gradPhi h x y := by
    refine Finset.sum_le_sum ?_
    intro i hi
    exact
      mul_le_mul_of_nonneg_left
        ((hstep i hi).growth hy) (hw_nonneg i hi)
  have hsplit :
      (alphaG + 1 / h) *
          (∑ i ∈ s, w i * bregmanDivergence phi gradPhi y (xPlus i)) +
        (∑ i ∈ s, w i *
          mirrorProximalGradientModel f g (fun _ : E => p i)
            phi gradPhi h x (xPlus i)) =
      (∑ i ∈ s, w i *
        (mirrorProximalGradientModel f g (fun _ : E => p i) phi gradPhi h x (xPlus i) +
          (alphaG + 1 / h) * bregmanDivergence phi gradPhi y (xPlus i))) := by
    rw [Finset.mul_sum, ← Finset.sum_add_distrib]
    refine Finset.sum_congr rfl ?_
    intro i hi
    ring
  exact hsplit.trans_le hsum

/--
Finite sampled star-model upper bound for Chewi Theorem 12.1.  Averaging
sampled mirror models at the comparison point `y` recovers the deterministic
model when the sampled oracle is unbiased, then relative strong convexity gives
the usual `F(y) + ((1 - alphaF h)/h) D_phi(y,x)` upper bound.
-/
theorem chewi121_finite_sampled_star_upper_of_unbiased
    {E : Type*} [NormedAddCommGroup E] [InnerProductSpace ℝ E]
    {ι : Type*} [DecidableEq ι] (s : Finset ι)
    {C : Set E} {f g : E -> ℝ} {gradF : E -> E}
    {phi : E -> ℝ} {gradPhi : E -> E} {alphaF h : ℝ}
    {x y : E} {p : ι -> E} {w : ι -> ℝ}
    (hh : 0 < h)
    (hmass : ∑ i ∈ s, w i = 1)
    (hunbiased : (∑ i ∈ s, w i • p i) = gradF x)
    (hconvF : RelativelyStrongConvexOn C f gradF phi gradPhi alphaF)
    (hx : x ∈ C) (hy : y ∈ C) :
    (∑ i ∈ s, w i *
      mirrorProximalGradientModel f g (fun _ : E => p i) phi gradPhi h x y) ≤
      compositeObjective f g y +
        ((1 - alphaF * h) / h) * bregmanDivergence phi gradPhi y x := by
  have hinner :
      (∑ i ∈ s, w i * inner ℝ (p i) (y - x)) =
        inner ℝ (gradF x) (y - x) := by
    calc
      (∑ i ∈ s, w i * inner ℝ (p i) (y - x)) =
          ∑ i ∈ s, inner ℝ (w i • p i) (y - x) := by
            refine Finset.sum_congr rfl ?_
            intro i hi
            simp [real_inner_smul_left]
      _ = inner ℝ (∑ i ∈ s, w i • p i) (y - x) := by
            rw [sum_inner]
      _ = inner ℝ (gradF x) (y - x) := by
            rw [hunbiased]
  have havg :
      (∑ i ∈ s, w i *
        mirrorProximalGradientModel f g (fun _ : E => p i) phi gradPhi h x y) =
        mirrorProximalGradientModel f g gradF phi gradPhi h x y := by
    unfold mirrorProximalGradientModel
    let q : ℝ := (1 / h) * bregmanDivergence phi gradPhi y x
    have hsplit :
        (∑ i ∈ s,
          w i * (f x + inner ℝ (p i) (y - x) + g y + q)) =
          (∑ i ∈ s, w i * (f x + g y + q)) +
            ∑ i ∈ s, w i * inner ℝ (p i) (y - x) := by
      rw [← Finset.sum_add_distrib]
      refine Finset.sum_congr rfl ?_
      intro i hi
      ring
    calc
      (∑ i ∈ s,
        w i *
          (f x + inner ℝ ((fun _ : E => p i) x) (y - x) + g y +
            (1 / h) * bregmanDivergence phi gradPhi y x)) =
          (∑ i ∈ s,
            w i * (f x + inner ℝ (p i) (y - x) + g y + q)) := by
              simp [q]
      _ =
          (∑ i ∈ s, w i * (f x + g y + q)) +
            ∑ i ∈ s, w i * inner ℝ (p i) (y - x) := hsplit
      _ =
          (∑ i ∈ s, w i) * (f x + g y + q) +
            ∑ i ∈ s, w i * inner ℝ (p i) (y - x) := by
              rw [Finset.sum_mul]
      _ =
          f x + inner ℝ (gradF x) (y - x) + g y +
            (1 / h) * bregmanDivergence phi gradPhi y x := by
              rw [hmass, hinner]
              dsimp [q]
              ring
  have hdet :
      mirrorProximalGradientModel f g gradF phi gradPhi h x y ≤
        compositeObjective f g y +
          (1 / h - alphaF) * bregmanDivergence phi gradPhi y x :=
    mirrorProximalGradientModel_le_composite_add_bregman
      hconvF hx hy
  have hcoeff :
      1 / h - alphaF = (1 - alphaF * h) / h := by
    field_simp [hh.ne']
  rw [hcoeff] at hdet
  rw [havg]
  simpa [one_div] using hdet

/--
Bochner-integral sampled growth inequality obtained by integrating the growth
field of an a.e. sampled mirror-proximal step.
-/
theorem chewi121_integral_sampled_growth_of_steps
    {Ω : Type*} [MeasurableSpace Ω] {μ : Measure Ω}
    {E : Type*} [NormedAddCommGroup E] [InnerProductSpace ℝ E]
    {C : Set E} {f g : E -> ℝ} {phi : E -> ℝ} {gradPhi : E -> E}
    {alphaG h psiNext psiStar Dnext : ℝ}
    {x y : E} {p xPlus : Ω -> E}
    (hpsiNext_int :
      Integrable (fun ω =>
        mirrorProximalGradientModel f g (fun _ : E => p ω)
          phi gradPhi h x (xPlus ω)) μ)
    (hDnext_int :
      Integrable (fun ω => bregmanDivergence phi gradPhi y (xPlus ω)) μ)
    (hpsiStar_int :
      Integrable (fun ω =>
        mirrorProximalGradientModel f g (fun _ : E => p ω)
          phi gradPhi h x y) μ)
    (hstep : ∀ᵐ ω ∂μ,
      IsMirrorProximalGradientStep C f g (fun _ : E => p ω)
        phi gradPhi alphaG h x (xPlus ω))
    (hy : y ∈ C)
    (hDnext :
      Dnext = ∫ ω, bregmanDivergence phi gradPhi y (xPlus ω) ∂μ)
    (hpsiNext :
      psiNext =
        ∫ ω,
          mirrorProximalGradientModel f g (fun _ : E => p ω)
            phi gradPhi h x (xPlus ω) ∂μ)
    (hpsiStar :
      psiStar =
        ∫ ω,
          mirrorProximalGradientModel f g (fun _ : E => p ω)
            phi gradPhi h x y ∂μ) :
    (alphaG + 1 / h) * Dnext + psiNext ≤ psiStar := by
  let A : ℝ := alphaG + 1 / h
  let psiPlus : Ω -> ℝ := fun ω =>
    mirrorProximalGradientModel f g (fun _ : E => p ω)
      phi gradPhi h x (xPlus ω)
  let Dfun : Ω -> ℝ := fun ω =>
    bregmanDivergence phi gradPhi y (xPlus ω)
  let psiY : Ω -> ℝ := fun ω =>
    mirrorProximalGradientModel f g (fun _ : E => p ω)
      phi gradPhi h x y
  have hpoint : (fun ω => psiPlus ω + A * Dfun ω) ≤ᵐ[μ] psiY := by
    filter_upwards [hstep] with ω hω
    simpa [psiPlus, Dfun, psiY, A] using hω.growth hy
  have hmono :
      (∫ ω, psiPlus ω + A * Dfun ω ∂μ) ≤ ∫ ω, psiY ω ∂μ :=
    integral_mono_ae (hpsiNext_int.add (hDnext_int.const_mul A))
      hpsiStar_int hpoint
  have hsplit :
      (∫ ω, psiPlus ω + A * Dfun ω ∂μ) =
        (∫ ω, psiPlus ω ∂μ) + A * (∫ ω, Dfun ω ∂μ) := by
    rw [integral_add hpsiNext_int (hDnext_int.const_mul A),
      integral_const_mul]
  have hmain :
      (∫ ω, psiPlus ω ∂μ) + A * (∫ ω, Dfun ω ∂μ) ≤
        ∫ ω, psiY ω ∂μ := by
    simpa [hsplit] using hmono
  rw [hDnext, hpsiNext, hpsiStar]
  simpa [psiPlus, Dfun, psiY, A, add_comm, add_left_comm, add_assoc] using hmain

/--
Bochner-integral sampled star-model upper bound for Chewi Theorem 12.1.
Unbiasedness of the sampled oracle recovers the deterministic mirror model
inside the integral, then relative strong convexity gives the usual star upper
bound.
-/
theorem chewi121_integral_sampled_star_upper_of_unbiased
    {Ω : Type*} [MeasurableSpace Ω] {μ : Measure Ω} [IsProbabilityMeasure μ]
    {E : Type*} [NormedAddCommGroup E] [InnerProductSpace ℝ E] [CompleteSpace E]
    {C : Set E} {f g : E -> ℝ} {gradF : E -> E}
    {phi : E -> ℝ} {gradPhi : E -> E} {alphaF h : ℝ}
    {x y : E} {p : Ω -> E}
    (hh : 0 < h)
    (hp_int : Integrable p μ)
    (hunbiased : (∫ ω, p ω ∂μ) = gradF x)
    (hconvF : RelativelyStrongConvexOn C f gradF phi gradPhi alphaF)
    (hx : x ∈ C) (hy : y ∈ C) :
    (∫ ω,
      mirrorProximalGradientModel f g (fun _ : E => p ω) phi gradPhi h x y ∂μ) ≤
      compositeObjective f g y +
        ((1 - alphaF * h) / h) * bregmanDivergence phi gradPhi y x := by
  have hinner :
      (∫ ω, inner ℝ (p ω) (y - x) ∂μ) =
        inner ℝ (gradF x) (y - x) := by
    calc
      (∫ ω, inner ℝ (p ω) (y - x) ∂μ) =
          ∫ ω, inner ℝ (y - x) (p ω) ∂μ := by
            simp [real_inner_comm]
      _ = inner ℝ (y - x) (∫ ω, p ω ∂μ) := by
            simpa using integral_inner hp_int (y - x)
      _ = inner ℝ (gradF x) (y - x) := by
            rw [hunbiased]
            rw [real_inner_comm]
  have havg :
      (∫ ω,
        mirrorProximalGradientModel f g (fun _ : E => p ω) phi gradPhi h x y ∂μ) =
        mirrorProximalGradientModel f g gradF phi gradPhi h x y := by
    unfold mirrorProximalGradientModel
    let q : ℝ := f x + g y + (1 / h) * bregmanDivergence phi gradPhi y x
    have hinner_int : Integrable (fun ω => inner ℝ (p ω) (y - x)) μ :=
      hp_int.inner_const (y - x)
    calc
      (∫ ω,
        f x + inner ℝ ((fun _ : E => p ω) x) (y - x) + g y +
          (1 / h) * bregmanDivergence phi gradPhi y x ∂μ) =
          ∫ ω, q + inner ℝ (p ω) (y - x) ∂μ := by
            congr 1
            ext ω
            dsimp [q]
            ring
      _ = q + ∫ ω, inner ℝ (p ω) (y - x) ∂μ := by
            rw [integral_add (integrable_const q) hinner_int]
            simp [q]
      _ =
          f x + inner ℝ (gradF x) (y - x) + g y +
            (1 / h) * bregmanDivergence phi gradPhi y x := by
            rw [hinner]
            dsimp [q]
            ring
  have hdet :
      mirrorProximalGradientModel f g gradF phi gradPhi h x y ≤
        compositeObjective f g y +
          (1 / h - alphaF) * bregmanDivergence phi gradPhi y x :=
    mirrorProximalGradientModel_le_composite_add_bregman
      hconvF hx hy
  have hcoeff :
      1 / h - alphaF = (1 - alphaF * h) / h := by
    field_simp [hh.ne']
  rw [hcoeff] at hdet
  rw [havg]
  simpa [one_div] using hdet

/--
Bochner-integral sampled star-model upper bound for the non-smooth branch of
Chewi Theorem 12.1.  The mean sampled oracle is assumed to be a relative
subgradient at `x`, matching the source condition
`E hatGrad f(x) in partial f(x)` with the relative-convexity correction.
-/
theorem chewi121_integral_sampled_star_upper_of_relativeSubgradient
    {Ω : Type*} [MeasurableSpace Ω] {μ : Measure Ω} [IsProbabilityMeasure μ]
    {E : Type*} [NormedAddCommGroup E] [InnerProductSpace ℝ E] [CompleteSpace E]
    {C : Set E} {f g : E -> ℝ}
    {phi : E -> ℝ} {gradPhi : E -> E} {alphaF h : ℝ}
    {x y : E} {p : Ω -> E}
    (hh : 0 < h)
    (hp_int : Integrable p μ)
    (hsub : IsRelativeSubgradientAt C f (∫ ω, p ω ∂μ)
      phi gradPhi alphaF x)
    (hy : y ∈ C) :
    (∫ ω,
      mirrorProximalGradientModel f g (fun _ : E => p ω) phi gradPhi h x y ∂μ) ≤
      compositeObjective f g y +
        ((1 - alphaF * h) / h) * bregmanDivergence phi gradPhi y x := by
  have hinner :
      (∫ ω, inner ℝ (p ω) (y - x) ∂μ) =
        inner ℝ (∫ ω, p ω ∂μ) (y - x) := by
    calc
      (∫ ω, inner ℝ (p ω) (y - x) ∂μ) =
          ∫ ω, inner ℝ (y - x) (p ω) ∂μ := by
            simp [real_inner_comm]
      _ = inner ℝ (y - x) (∫ ω, p ω ∂μ) := by
            simpa using integral_inner hp_int (y - x)
      _ = inner ℝ (∫ ω, p ω ∂μ) (y - x) := by
            rw [real_inner_comm]
  have havg :
      (∫ ω,
        mirrorProximalGradientModel f g (fun _ : E => p ω) phi gradPhi h x y ∂μ) =
        mirrorProximalGradientModel f g (fun _ : E => ∫ ω, p ω ∂μ)
          phi gradPhi h x y := by
    unfold mirrorProximalGradientModel
    let q : ℝ := f x + g y + (1 / h) * bregmanDivergence phi gradPhi y x
    have hinner_int : Integrable (fun ω => inner ℝ (p ω) (y - x)) μ :=
      hp_int.inner_const (y - x)
    calc
      (∫ ω,
        f x + inner ℝ ((fun _ : E => p ω) x) (y - x) + g y +
          (1 / h) * bregmanDivergence phi gradPhi y x ∂μ) =
          ∫ ω, q + inner ℝ (p ω) (y - x) ∂μ := by
            congr 1
            ext ω
            dsimp [q]
            ring
      _ = q + ∫ ω, inner ℝ (p ω) (y - x) ∂μ := by
            rw [integral_add (integrable_const q) hinner_int]
            simp [q]
      _ =
          f x + inner ℝ (∫ ω, p ω ∂μ) (y - x) + g y +
            (1 / h) * bregmanDivergence phi gradPhi y x := by
            rw [hinner]
            dsimp [q]
            ring
  have hsub_y := hsub.lower_model hy
  have hdet :
      mirrorProximalGradientModel f g (fun _ : E => ∫ ω, p ω ∂μ)
        phi gradPhi h x y ≤
        compositeObjective f g y +
          (1 / h - alphaF) * bregmanDivergence phi gradPhi y x := by
    unfold mirrorProximalGradientModel compositeObjective
    nlinarith
  have hcoeff :
      1 / h - alphaF = (1 - alphaF * h) / h := by
    field_simp [hh.ne']
  rw [hcoeff] at hdet
  rw [havg]
  simpa [one_div] using hdet

/--
Finite smooth sampled-model `hcore` theorem.  This discharges the pointwise
raw model inequality, relative-smoothness absorption, and mirror
strong-convexity lower bound from the actual sampled model data.
-/
theorem chewi121_smooth_hcore_of_finite_sampled_models
    {E : Type*} [NormedAddCommGroup E] [InnerProductSpace ℝ E]
    {ι : Type*} [DecidableEq ι] (s : Finset ι)
    {C : Set E} {f g : E -> ℝ} {gradF : E -> E}
    {phi : E -> ℝ} {gradPhi : E -> E}
    {alphaPhi betaF h psiNext varianceRms stepRms : ℝ}
    {x : E} {p xPlus : ι -> E} {w noise : ι -> ℝ}
    (hh : 0 < h) (halphaPhi_nonneg : 0 ≤ alphaPhi)
    (hw_nonneg : ∀ i ∈ s, 0 ≤ w i)
    (hsmooth : RelativelySmoothOn C f gradF phi gradPhi betaF)
    (hbeta : betaF ≤ 1 / (2 * h))
    (hphi : FirstOrderStrongConvexOn C phi gradPhi alphaPhi)
    (hx : x ∈ C) (hxPlus : ∀ i ∈ s, xPlus i ∈ C)
    (hnoise_point : ∀ i ∈ s,
      -inner ℝ (p i - gradF x) (xPlus i - x) ≤ noise i)
    (hpsi :
      (∑ i ∈ s, w i *
        mirrorProximalGradientModel f g (fun _ : E => p i)
          phi gradPhi h x (xPlus i)) ≤ psiNext)
    (hstepRms_sq :
      stepRms ^ (2 : ℕ) ≤ ∑ i ∈ s, w i * ‖xPlus i - x‖ ^ (2 : ℕ))
    (hnoise :
      (∑ i ∈ s, w i * noise i) ≤ varianceRms * stepRms) :
    (∑ i ∈ s, w i * compositeObjective f g (xPlus i)) +
        (alphaPhi / (4 * h)) * stepRms ^ (2 : ℕ) -
          varianceRms * stepRms ≤ psiNext := by
  refine
    chewi121_smooth_hcore_of_finite_components
      (s := s) (w := w)
      (Fplus := fun i => compositeObjective f g (xPlus i))
      (Df := fun i => bregmanDivergence f gradF (xPlus i) x)
      (Dphi := fun i => bregmanDivergence phi gradPhi (xPlus i) x)
      (noise := noise)
      (psi := fun i =>
        mirrorProximalGradientModel f g (fun _ : E => p i)
          phi gradPhi h x (xPlus i))
      (stepSq := fun i => ‖xPlus i - x‖ ^ (2 : ℕ))
      (alphaPhi := alphaPhi) (h := h) (psiNext := psiNext)
      (varianceRms := varianceRms) (stepRms := stepRms)
      hh halphaPhi_nonneg hw_nonneg ?_ hpsi ?_ hstepRms_sq ?_ hnoise
  · intro i hi
    exact
      chewi121_smooth_raw_point_of_sampled_model
        (f := f) (g := g) (gradF := gradF) (phi := phi)
        (gradPhi := gradPhi) (h := h) (noise := noise i)
        (x := x) (xPlus := xPlus i) (p := p i)
        (hnoise_point i hi)
  · intro i hi
    have hphi_lower :
        (alphaPhi / 2) * ‖xPlus i - x‖ ^ (2 : ℕ) ≤
          bregmanDivergence phi gradPhi (xPlus i) x :=
      bregmanDivergence_lower_of_firstOrderStrongConvexOn
        (C := C) (phi := phi) (gradPhi := gradPhi)
        (alphaPhi := alphaPhi) (x := x) (xPlus := xPlus i)
        hphi hx (hxPlus i hi)
    have hDphi_nonneg :
        0 ≤ bregmanDivergence phi gradPhi (xPlus i) x := by
      have hleft_nonneg :
          0 ≤ (alphaPhi / 2) * ‖xPlus i - x‖ ^ (2 : ℕ) :=
        mul_nonneg (by positivity) (sq_nonneg _)
      exact hleft_nonneg.trans hphi_lower
    exact
      chewi121_smooth_absorb_of_relativeSmoothOn
        (C := C) (f := f) (gradF := gradF) (phi := phi)
        (gradPhi := gradPhi) (betaF := betaF) (h := h)
        (x := x) (xPlus := xPlus i)
        hsmooth hbeta hDphi_nonneg hx (hxPlus i hi)
  · intro i hi
    exact
      bregmanDivergence_lower_of_firstOrderStrongConvexOn
        (C := C) (phi := phi) (gradPhi := gradPhi)
        (alphaPhi := alphaPhi) (x := x) (xPlus := xPlus i)
        hphi hx (hxPlus i hi)

/--
Finite non-smooth sampled-model `hcore` theorem in pointwise-norm form.  The
source L2-only theorem will use later expectation/Cauchy-Schwarz wrappers; this
finite bridge is useful when each sampled oracle is already pointwise bounded.
-/
theorem chewi121_nonsmooth_hcore_of_finite_sampled_models
    {E : Type*} [NormedAddCommGroup E] [InnerProductSpace ℝ E]
    {ι : Type*} [DecidableEq ι] (s : Finset ι)
    {C : Set E} {f g : E -> ℝ} {phi : E -> ℝ} {gradPhi : E -> E}
    {alphaPhi L h psiNext stepRms : ℝ}
    {x : E} {p xPlus : ι -> E} {w : ι -> ℝ}
    (hh : 0 < h) (halphaPhi_nonneg : 0 ≤ alphaPhi) (hL_nonneg : 0 ≤ L)
    (hw_nonneg : ∀ i ∈ s, 0 ≤ w i)
    (hLip : LipschitzOnWith (Real.toNNReal L) f C)
    (hphi : FirstOrderStrongConvexOn C phi gradPhi alphaPhi)
    (hx : x ∈ C) (hxPlus : ∀ i ∈ s, xPlus i ∈ C)
    (hp_norm : ∀ i ∈ s, ‖p i‖ ≤ L)
    (hpsi :
      (∑ i ∈ s, w i *
        mirrorProximalGradientModel f g (fun _ : E => p i)
          phi gradPhi h x (xPlus i)) ≤ psiNext)
    (hstepRms_sq :
      stepRms ^ (2 : ℕ) ≤ ∑ i ∈ s, w i * ‖xPlus i - x‖ ^ (2 : ℕ))
    (hstep_avg :
      (∑ i ∈ s, w i * ‖xPlus i - x‖) ≤ stepRms) :
    (∑ i ∈ s, w i * compositeObjective f g (xPlus i)) +
        (alphaPhi / (2 * h)) * stepRms ^ (2 : ℕ) -
          (2 * L) * stepRms ≤ psiNext := by
  refine
    chewi121_nonsmooth_hcore_of_finite_components
      (s := s) (w := w)
      (Fplus := fun i => compositeObjective f g (xPlus i))
      (lip := fun i => L * ‖xPlus i - x‖)
      (grad := fun i => L * ‖xPlus i - x‖)
      (Dphi := fun i => bregmanDivergence phi gradPhi (xPlus i) x)
      (psi := fun i =>
        mirrorProximalGradientModel f g (fun _ : E => p i)
          phi gradPhi h x (xPlus i))
      (stepSq := fun i => ‖xPlus i - x‖ ^ (2 : ℕ))
      (stepNorm := fun i => ‖xPlus i - x‖)
      (alphaPhi := alphaPhi) (L := L) (h := h) (psiNext := psiNext)
      (stepRms := stepRms)
      hh halphaPhi_nonneg hL_nonneg hw_nonneg ?_ hpsi
      hstepRms_sq ?_ hstep_avg ?_ ?_
  · intro i hi
    have hlip : f (xPlus i) - f x ≤ L * ‖xPlus i - x‖ := by
      have hraw := hLip.le_add_mul (hxPlus i hi) hx
      have hdist : dist (xPlus i) x = ‖xPlus i - x‖ := by
        rw [dist_eq_norm]
      have hupper : f (xPlus i) ≤ f x + L * ‖xPlus i - x‖ := by
        simpa [Real.coe_toNNReal L hL_nonneg, hdist] using hraw
      nlinarith
    have hgrad : -inner ℝ (p i) (xPlus i - x) ≤ L * ‖xPlus i - x‖ := by
      have habs := abs_real_inner_le_norm (p i) (xPlus i - x)
      have hneg : -inner ℝ (p i) (xPlus i - x) ≤
          ‖p i‖ * ‖xPlus i - x‖ :=
        (neg_le_abs _).trans habs
      have hscale :
          ‖p i‖ * ‖xPlus i - x‖ ≤ L * ‖xPlus i - x‖ :=
        mul_le_mul_of_nonneg_right (hp_norm i hi) (norm_nonneg _)
      exact hneg.trans hscale
    exact
      chewi121_nonsmooth_raw_point_of_sampled_model
        (f := f) (g := g) (phi := phi) (gradPhi := gradPhi)
        (h := h) (lip := L * ‖xPlus i - x‖)
        (grad := L * ‖xPlus i - x‖)
        (x := x) (xPlus := xPlus i) (p := p i)
        hlip hgrad
  · intro i hi
    exact
      bregmanDivergence_lower_of_firstOrderStrongConvexOn
        (C := C) (phi := phi) (gradPhi := gradPhi)
        (alphaPhi := alphaPhi) (x := x) (xPlus := xPlus i)
        hphi hx (hxPlus i hi)
  · intro i hi
    rfl
  · intro i hi
    rfl

/--
L2/Hölder noise bound for the smooth stochastic-gradient model in Chewi
Theorem 12.1.  The pointwise stochastic error is dominated by the product of a
variance norm and the step norm; the two root-mean-square bounds then give the
displayed Cauchy-Schwarz estimate.
-/
theorem chewi121_integral_noise_bound_of_l2_roots
    {Ω : Type*} [MeasurableSpace Ω] {μ : Measure Ω}
    {noise varianceNorm stepNorm : Ω -> ℝ} {varianceRms stepRms : ℝ}
    (hnoise_int : Integrable noise μ)
    (hvariance_nonneg : 0 ≤ᵐ[μ] varianceNorm)
    (hstep_nonneg : 0 ≤ᵐ[μ] stepNorm)
    (hvariance_mem : MemLp varianceNorm (ENNReal.ofReal (2 : ℝ)) μ)
    (hstep_mem : MemLp stepNorm (ENNReal.ofReal (2 : ℝ)) μ)
    (hnoise_point : noise ≤ᵐ[μ] fun ω => varianceNorm ω * stepNorm ω)
    (hvariance_root :
      (∫ ω, varianceNorm ω ^ (2 : ℝ) ∂μ) ^ (1 / (2 : ℝ)) ≤ varianceRms)
    (hstep_root :
      (∫ ω, stepNorm ω ^ (2 : ℝ) ∂μ) ^ (1 / (2 : ℝ)) ≤ stepRms) :
    (∫ ω, noise ω ∂μ) ≤ varianceRms * stepRms := by
  haveI : ENNReal.HolderTriple
      (ENNReal.ofReal (2 : ℝ)) (ENNReal.ofReal (2 : ℝ)) 1 := by
    simpa using Real.HolderConjugate.two_two.ennrealOfReal
  have hprod_int : Integrable (fun ω => varianceNorm ω * stepNorm ω) μ := by
    simpa [Pi.mul_apply] using hvariance_mem.integrable_mul hstep_mem
  have hmono :
      (∫ ω, noise ω ∂μ) ≤ ∫ ω, varianceNorm ω * stepNorm ω ∂μ :=
    integral_mono_ae hnoise_int hprod_int hnoise_point
  have hholder :
      (∫ ω, varianceNorm ω * stepNorm ω ∂μ) ≤
        (∫ ω, varianceNorm ω ^ (2 : ℝ) ∂μ) ^ (1 / (2 : ℝ)) *
          (∫ ω, stepNorm ω ^ (2 : ℝ) ∂μ) ^ (1 / (2 : ℝ)) :=
    integral_mul_le_Lp_mul_Lq_of_nonneg
      Real.HolderConjugate.two_two hvariance_nonneg hstep_nonneg
      hvariance_mem hstep_mem
  have hvariance_sq_nonneg :
      0 ≤ ∫ ω, varianceNorm ω ^ (2 : ℝ) ∂μ :=
    integral_nonneg_of_ae <| by
      filter_upwards [hvariance_nonneg] with ω hω
      exact Real.rpow_nonneg hω _
  have hstep_sq_nonneg :
      0 ≤ ∫ ω, stepNorm ω ^ (2 : ℝ) ∂μ :=
    integral_nonneg_of_ae <| by
      filter_upwards [hstep_nonneg] with ω hω
      exact Real.rpow_nonneg hω _
  have hvariance_root_nonneg :
      0 ≤ (∫ ω, varianceNorm ω ^ (2 : ℝ) ∂μ) ^ (1 / (2 : ℝ)) :=
    Real.rpow_nonneg hvariance_sq_nonneg _
  have hstep_root_nonneg :
      0 ≤ (∫ ω, stepNorm ω ^ (2 : ℝ) ∂μ) ^ (1 / (2 : ℝ)) :=
    Real.rpow_nonneg hstep_sq_nonneg _
  have hstepRms_nonneg : 0 ≤ stepRms :=
    hstep_root_nonneg.trans hstep_root
  calc
    (∫ ω, noise ω ∂μ) ≤
        (∫ ω, varianceNorm ω ^ (2 : ℝ) ∂μ) ^ (1 / (2 : ℝ)) *
          (∫ ω, stepNorm ω ^ (2 : ℝ) ∂μ) ^ (1 / (2 : ℝ)) :=
      hmono.trans hholder
    _ ≤ varianceRms *
          (∫ ω, stepNorm ω ^ (2 : ℝ) ∂μ) ^ (1 / (2 : ℝ)) :=
      mul_le_mul_of_nonneg_right hvariance_root hstep_root_nonneg
    _ ≤ varianceRms * stepRms :=
      mul_le_mul_of_nonneg_left hstep_root
        (hvariance_root_nonneg.trans hvariance_root)

/--
Probability-measure L2-to-L1 bound used by the non-smooth SMPGD sampled
endpoint.  It is the Cauchy-Schwarz estimate with the second factor equal to
the constant-one function.
-/
theorem chewi121_integral_average_le_l2_root_of_probability
    {Ω : Type*} [MeasurableSpace Ω] {μ : Measure Ω} [IsProbabilityMeasure μ]
    {stepNorm : Ω -> ℝ} {stepRms : ℝ}
    (hstep_nonneg : 0 ≤ᵐ[μ] stepNorm)
    (hstep_mem : MemLp stepNorm (ENNReal.ofReal (2 : ℝ)) μ)
    (hstep_root :
      (∫ ω, stepNorm ω ^ (2 : ℝ) ∂μ) ^ (1 / (2 : ℝ)) ≤ stepRms) :
    (∫ ω, stepNorm ω ∂μ) ≤ stepRms := by
  have hone_nonneg : 0 ≤ᵐ[μ] fun _ : Ω => (1 : ℝ) :=
    Filter.Eventually.of_forall fun _ => zero_le_one
  have hone_mem :
      MemLp (fun _ : Ω => (1 : ℝ)) (ENNReal.ofReal (2 : ℝ)) μ := by
    simpa using
      (memLp_const (1 : ℝ) :
        MemLp (fun _ : Ω => (1 : ℝ)) (ENNReal.ofReal (2 : ℝ)) μ)
  have hone_root :
      (∫ ω, (fun _ : Ω => (1 : ℝ)) ω ^ (2 : ℝ) ∂μ) ^ (1 / (2 : ℝ)) =
        1 := by
    simp
  have hholder :
      (∫ ω, stepNorm ω * (fun _ : Ω => (1 : ℝ)) ω ∂μ) ≤
        (∫ ω, stepNorm ω ^ (2 : ℝ) ∂μ) ^ (1 / (2 : ℝ)) *
          (∫ ω, (fun _ : Ω => (1 : ℝ)) ω ^ (2 : ℝ) ∂μ) ^ (1 / (2 : ℝ)) :=
    integral_mul_le_Lp_mul_Lq_of_nonneg
      Real.HolderConjugate.two_two hstep_nonneg hone_nonneg
      hstep_mem hone_mem
  have hholder' :
      (∫ ω, stepNorm ω ∂μ) ≤
        (∫ ω, stepNorm ω ^ (2 : ℝ) ∂μ) ^ (1 / (2 : ℝ)) := by
    simpa [hone_root] using hholder
  exact hholder'.trans hstep_root

/--
Bochner-integral smooth `hcore` theorem, reducing the stochastic-gradient
expectation proof to integral raw/absorption/mirror/noise component fields.
-/
theorem chewi121_smooth_hcore_of_integral_components
    {Ω : Type*} [MeasurableSpace Ω] {μ : Measure Ω}
    {Fplus Df Dphi noise psi stepSq : Ω -> ℝ}
    {alphaPhi h psiNext varianceRms stepRms : ℝ}
    (hh : 0 < h) (halphaPhi_nonneg : 0 ≤ alphaPhi)
    (hFplus : Integrable Fplus μ) (hDf : Integrable Df μ)
    (hDphi : Integrable Dphi μ) (hnoise_int : Integrable noise μ)
    (hpsi_int : Integrable psi μ) (hstepSq : Integrable stepSq μ)
    (hraw_point : (fun ω =>
      Fplus ω - Df ω + (1 / h) * Dphi ω - noise ω) ≤ᵐ[μ] psi)
    (hpsi : (∫ ω, psi ω ∂μ) ≤ psiNext)
    (hdf_point : Df ≤ᵐ[μ] fun ω => (1 / (2 * h)) * Dphi ω)
    (hstepRms_sq : stepRms ^ (2 : ℕ) ≤ ∫ ω, stepSq ω ∂μ)
    (hphi_point : (fun ω => (alphaPhi / 2) * stepSq ω) ≤ᵐ[μ] Dphi)
    (hnoise : (∫ ω, noise ω ∂μ) ≤ varianceRms * stepRms) :
    (∫ ω, Fplus ω ∂μ) +
        (alphaPhi / (4 * h)) * stepRms ^ (2 : ℕ) -
          varianceRms * stepRms ≤ psiNext := by
  have hraw :=
    chewi121_smooth_integral_raw_component_bound
      (Fplus := Fplus) (Df := Df) (Dphi := Dphi) (noise := noise)
      (psi := psi) (h := h) (psiNext := psiNext)
      hFplus hDf hDphi hnoise_int hpsi_int hraw_point hpsi
  have hdf_absorb :=
    chewi121_smooth_integral_absorb_component_bound
      (Df := Df) (Dphi := Dphi) (h := h) hDf hDphi hdf_point
  have hphi_lower :=
    chewi121_integral_mirror_lower_component_bound
      (Dphi := Dphi) (stepSq := stepSq) (alphaPhi := alphaPhi)
      (stepRms := stepRms)
      halphaPhi_nonneg hDphi hstepSq hstepRms_sq hphi_point
  exact
    chewi121_smooth_hcore_of_expected_components
      (alphaPhi := alphaPhi) (h := h)
      (expectedNext := ∫ ω, Fplus ω ∂μ) (psiNext := psiNext)
      (DfAvg := ∫ ω, Df ω ∂μ)
      (DphiAvg := ∫ ω, Dphi ω ∂μ)
      (noiseTerm := ∫ ω, noise ω ∂μ)
      (varianceRms := varianceRms) (stepRms := stepRms)
      hh hraw hdf_absorb hphi_lower hnoise

/--
Smooth integral `hcore` with the Cauchy-Schwarz noise estimate discharged from
pointwise stochastic-error domination and L2 root bounds.
-/
theorem chewi121_smooth_hcore_of_integral_l2_noise_components
    {Ω : Type*} [MeasurableSpace Ω] {μ : Measure Ω}
    {Fplus Df Dphi noise psi stepSq varianceNorm stepNorm : Ω -> ℝ}
    {alphaPhi h psiNext varianceRms stepRms : ℝ}
    (hh : 0 < h) (halphaPhi_nonneg : 0 ≤ alphaPhi)
    (hFplus : Integrable Fplus μ) (hDf : Integrable Df μ)
    (hDphi : Integrable Dphi μ) (hnoise_int : Integrable noise μ)
    (hpsi_int : Integrable psi μ) (hstepSq : Integrable stepSq μ)
    (hraw_point : (fun ω =>
      Fplus ω - Df ω + (1 / h) * Dphi ω - noise ω) ≤ᵐ[μ] psi)
    (hpsi : (∫ ω, psi ω ∂μ) ≤ psiNext)
    (hdf_point : Df ≤ᵐ[μ] fun ω => (1 / (2 * h)) * Dphi ω)
    (hstepRms_sq : stepRms ^ (2 : ℕ) ≤ ∫ ω, stepSq ω ∂μ)
    (hphi_point : (fun ω => (alphaPhi / 2) * stepSq ω) ≤ᵐ[μ] Dphi)
    (hvariance_nonneg : 0 ≤ᵐ[μ] varianceNorm)
    (hstep_nonneg : 0 ≤ᵐ[μ] stepNorm)
    (hvariance_mem : MemLp varianceNorm (ENNReal.ofReal (2 : ℝ)) μ)
    (hstep_mem : MemLp stepNorm (ENNReal.ofReal (2 : ℝ)) μ)
    (hnoise_point : noise ≤ᵐ[μ] fun ω => varianceNorm ω * stepNorm ω)
    (hvariance_root :
      (∫ ω, varianceNorm ω ^ (2 : ℝ) ∂μ) ^ (1 / (2 : ℝ)) ≤ varianceRms)
    (hstep_root :
      (∫ ω, stepNorm ω ^ (2 : ℝ) ∂μ) ^ (1 / (2 : ℝ)) ≤ stepRms) :
    (∫ ω, Fplus ω ∂μ) +
        (alphaPhi / (4 * h)) * stepRms ^ (2 : ℕ) -
          varianceRms * stepRms ≤ psiNext := by
  have hnoise :=
    chewi121_integral_noise_bound_of_l2_roots
      (noise := noise) (varianceNorm := varianceNorm) (stepNorm := stepNorm)
      (varianceRms := varianceRms) (stepRms := stepRms)
      hnoise_int hvariance_nonneg hstep_nonneg hvariance_mem hstep_mem
      hnoise_point hvariance_root hstep_root
  exact
    chewi121_smooth_hcore_of_integral_components
      (μ := μ) (Fplus := Fplus) (Df := Df) (Dphi := Dphi)
      (noise := noise) (psi := psi) (stepSq := stepSq)
      (alphaPhi := alphaPhi) (h := h) (psiNext := psiNext)
      (varianceRms := varianceRms) (stepRms := stepRms)
      hh halphaPhi_nonneg hFplus hDf hDphi hnoise_int hpsi_int hstepSq
      hraw_point hpsi hdf_point hstepRms_sq hphi_point hnoise

/--
Bochner-integral smooth sampled-model `hcore` theorem with the L2 noise
estimate discharged.  This is the measure-level analogue of
`chewi121_smooth_hcore_of_finite_sampled_models`: the actual sampled oracle
`p(omega)` supplies the raw model, while relative smoothness and mirror strong
convexity supply the deterministic component bounds.
-/
theorem chewi121_smooth_hcore_of_integral_l2_sampled_models
    {Ω : Type*} [MeasurableSpace Ω] {μ : Measure Ω}
    {E : Type*} [NormedAddCommGroup E] [InnerProductSpace ℝ E]
    {C : Set E} {f g : E -> ℝ} {gradF : E -> E}
    {phi : E -> ℝ} {gradPhi : E -> E}
    {alphaPhi betaF h psiNext varianceRms stepRms : ℝ}
    {x : E} {p xPlus : Ω -> E}
    {noise varianceNorm stepNorm : Ω -> ℝ}
    (hh : 0 < h) (halphaPhi_nonneg : 0 ≤ alphaPhi)
    (hsmooth : RelativelySmoothOn C f gradF phi gradPhi betaF)
    (hbeta : betaF ≤ 1 / (2 * h))
    (hphi : FirstOrderStrongConvexOn C phi gradPhi alphaPhi)
    (hx : x ∈ C) (hxPlus : ∀ᵐ ω ∂μ, xPlus ω ∈ C)
    (hFplus :
      Integrable (fun ω => compositeObjective f g (xPlus ω)) μ)
    (hDf :
      Integrable (fun ω => bregmanDivergence f gradF (xPlus ω) x) μ)
    (hDphi :
      Integrable (fun ω => bregmanDivergence phi gradPhi (xPlus ω) x) μ)
    (hnoise_int : Integrable noise μ)
    (hpsi_int :
      Integrable (fun ω =>
        mirrorProximalGradientModel f g (fun _ : E => p ω)
          phi gradPhi h x (xPlus ω)) μ)
    (hstepSq :
      Integrable (fun ω => ‖xPlus ω - x‖ ^ (2 : ℕ)) μ)
    (hnoise_raw : ∀ᵐ ω ∂μ,
      -inner ℝ (p ω - gradF x) (xPlus ω - x) ≤ noise ω)
    (hpsi :
      (∫ ω,
        mirrorProximalGradientModel f g (fun _ : E => p ω)
          phi gradPhi h x (xPlus ω) ∂μ) ≤ psiNext)
    (hstepRms_sq :
      stepRms ^ (2 : ℕ) ≤ ∫ ω, ‖xPlus ω - x‖ ^ (2 : ℕ) ∂μ)
    (hvariance_nonneg : 0 ≤ᵐ[μ] varianceNorm)
    (hstep_nonneg : 0 ≤ᵐ[μ] stepNorm)
    (hvariance_mem : MemLp varianceNorm (ENNReal.ofReal (2 : ℝ)) μ)
    (hstep_mem : MemLp stepNorm (ENNReal.ofReal (2 : ℝ)) μ)
    (hnoise_point : noise ≤ᵐ[μ] fun ω => varianceNorm ω * stepNorm ω)
    (hvariance_root :
      (∫ ω, varianceNorm ω ^ (2 : ℝ) ∂μ) ^ (1 / (2 : ℝ)) ≤ varianceRms)
    (hstep_root :
      (∫ ω, stepNorm ω ^ (2 : ℝ) ∂μ) ^ (1 / (2 : ℝ)) ≤ stepRms) :
    (∫ ω, compositeObjective f g (xPlus ω) ∂μ) +
        (alphaPhi / (4 * h)) * stepRms ^ (2 : ℕ) -
          varianceRms * stepRms ≤ psiNext := by
  have hraw_point :
      (fun ω =>
        compositeObjective f g (xPlus ω) -
          bregmanDivergence f gradF (xPlus ω) x +
          (1 / h) * bregmanDivergence phi gradPhi (xPlus ω) x -
            noise ω) ≤ᵐ[μ]
        fun ω =>
          mirrorProximalGradientModel f g (fun _ : E => p ω)
            phi gradPhi h x (xPlus ω) := by
    filter_upwards [hnoise_raw] with ω hω
    exact
      chewi121_smooth_raw_point_of_sampled_model
        (f := f) (g := g) (gradF := gradF) (phi := phi)
        (gradPhi := gradPhi) (h := h) (noise := noise ω)
        (x := x) (xPlus := xPlus ω) (p := p ω) hω
  have hdf_point :
      (fun ω => bregmanDivergence f gradF (xPlus ω) x) ≤ᵐ[μ]
        fun ω => (1 / (2 * h)) * bregmanDivergence phi gradPhi (xPlus ω) x := by
    filter_upwards [hxPlus] with ω hω
    have hphi_lower :
        (alphaPhi / 2) * ‖xPlus ω - x‖ ^ (2 : ℕ) ≤
          bregmanDivergence phi gradPhi (xPlus ω) x :=
      bregmanDivergence_lower_of_firstOrderStrongConvexOn
        (C := C) (phi := phi) (gradPhi := gradPhi)
        (alphaPhi := alphaPhi) (x := x) (xPlus := xPlus ω)
        hphi hx hω
    have hDphi_nonneg :
        0 ≤ bregmanDivergence phi gradPhi (xPlus ω) x := by
      have hleft_nonneg :
          0 ≤ (alphaPhi / 2) * ‖xPlus ω - x‖ ^ (2 : ℕ) :=
        mul_nonneg (by positivity) (sq_nonneg _)
      exact hleft_nonneg.trans hphi_lower
    exact
      chewi121_smooth_absorb_of_relativeSmoothOn
        (C := C) (f := f) (gradF := gradF) (phi := phi)
        (gradPhi := gradPhi) (betaF := betaF) (h := h)
        (x := x) (xPlus := xPlus ω)
        hsmooth hbeta hDphi_nonneg hx hω
  have hphi_point :
      (fun ω => (alphaPhi / 2) * ‖xPlus ω - x‖ ^ (2 : ℕ)) ≤ᵐ[μ]
        fun ω => bregmanDivergence phi gradPhi (xPlus ω) x := by
    filter_upwards [hxPlus] with ω hω
    exact
      bregmanDivergence_lower_of_firstOrderStrongConvexOn
        (C := C) (phi := phi) (gradPhi := gradPhi)
        (alphaPhi := alphaPhi) (x := x) (xPlus := xPlus ω)
        hphi hx hω
  exact
    chewi121_smooth_hcore_of_integral_l2_noise_components
      (μ := μ)
      (Fplus := fun ω => compositeObjective f g (xPlus ω))
      (Df := fun ω => bregmanDivergence f gradF (xPlus ω) x)
      (Dphi := fun ω => bregmanDivergence phi gradPhi (xPlus ω) x)
      (noise := noise)
      (psi := fun ω =>
        mirrorProximalGradientModel f g (fun _ : E => p ω)
          phi gradPhi h x (xPlus ω))
      (stepSq := fun ω => ‖xPlus ω - x‖ ^ (2 : ℕ))
      (varianceNorm := varianceNorm) (stepNorm := stepNorm)
      (alphaPhi := alphaPhi) (h := h) (psiNext := psiNext)
      (varianceRms := varianceRms) (stepRms := stepRms)
      hh halphaPhi_nonneg hFplus hDf hDphi hnoise_int hpsi_int hstepSq
      hraw_point hpsi hdf_point hstepRms_sq hphi_point
      hvariance_nonneg hstep_nonneg hvariance_mem hstep_mem hnoise_point
      hvariance_root hstep_root

/--
Bochner-integral non-smooth sampled-model `hcore` theorem with source-style
L2 sampled-gradient and step-norm controls.  The Lipschitz term uses the
probability-measure L2-to-L1 bound, while the sampled-gradient term uses the
same Hölder/L2 product estimate as the smooth stochastic-noise bridge.
-/
theorem chewi121_nonsmooth_hcore_of_integral_l2_sampled_models
    {Ω : Type*} [MeasurableSpace Ω] {μ : Measure Ω} [IsProbabilityMeasure μ]
    {E : Type*} [NormedAddCommGroup E] [InnerProductSpace ℝ E]
    {C : Set E} {f g : E -> ℝ} {phi : E -> ℝ} {gradPhi : E -> E}
    {alphaPhi L h psiNext stepRms : ℝ}
    {x : E} {p xPlus : Ω -> E} {pNorm stepNorm : Ω -> ℝ}
    (hh : 0 < h) (halphaPhi_nonneg : 0 ≤ alphaPhi) (hL_nonneg : 0 ≤ L)
    (hLip : LipschitzOnWith (Real.toNNReal L) f C)
    (hphi : FirstOrderStrongConvexOn C phi gradPhi alphaPhi)
    (hx : x ∈ C) (hxPlus : ∀ᵐ ω ∂μ, xPlus ω ∈ C)
    (hFplus :
      Integrable (fun ω => compositeObjective f g (xPlus ω)) μ)
    (hDphi :
      Integrable (fun ω => bregmanDivergence phi gradPhi (xPlus ω) x) μ)
    (hpsi_int :
      Integrable (fun ω =>
        mirrorProximalGradientModel f g (fun _ : E => p ω)
          phi gradPhi h x (xPlus ω)) μ)
    (hstepSq :
      Integrable (fun ω => ‖xPlus ω - x‖ ^ (2 : ℕ)) μ)
    (hpsi :
      (∫ ω,
        mirrorProximalGradientModel f g (fun _ : E => p ω)
          phi gradPhi h x (xPlus ω) ∂μ) ≤ psiNext)
    (hstepRms_sq :
      stepRms ^ (2 : ℕ) ≤ ∫ ω, ‖xPlus ω - x‖ ^ (2 : ℕ) ∂μ)
    (hstep_point : (fun ω => ‖xPlus ω - x‖) ≤ᵐ[μ] stepNorm)
    (hpNorm_nonneg : 0 ≤ᵐ[μ] pNorm)
    (hstep_nonneg : 0 ≤ᵐ[μ] stepNorm)
    (hpNorm_mem : MemLp pNorm (ENNReal.ofReal (2 : ℝ)) μ)
    (hstep_mem : MemLp stepNorm (ENNReal.ofReal (2 : ℝ)) μ)
    (hpNorm_point : (fun ω => ‖p ω‖) ≤ᵐ[μ] pNorm)
    (hpNorm_root :
      (∫ ω, pNorm ω ^ (2 : ℝ) ∂μ) ^ (1 / (2 : ℝ)) ≤ L)
    (hstep_root :
      (∫ ω, stepNorm ω ^ (2 : ℝ) ∂μ) ^ (1 / (2 : ℝ)) ≤ stepRms) :
    (∫ ω, compositeObjective f g (xPlus ω) ∂μ) +
        (alphaPhi / (2 * h)) * stepRms ^ (2 : ℕ) -
          (2 * L) * stepRms ≤ psiNext := by
  haveI : ENNReal.HolderTriple
      (ENNReal.ofReal (2 : ℝ)) (ENNReal.ofReal (2 : ℝ)) 1 := by
    simpa using Real.HolderConjugate.two_two.ennrealOfReal
  have hstepNorm_int : Integrable stepNorm μ := by
    exact memLp_one_iff_integrable.mp (hstep_mem.mono_exponent (by norm_num))
  have hlip_int : Integrable (fun ω => L * stepNorm ω) μ :=
    hstepNorm_int.const_mul _
  have hgrad_int : Integrable (fun ω => pNorm ω * stepNorm ω) μ := by
    simpa [Pi.mul_apply] using hpNorm_mem.integrable_mul hstep_mem
  have hraw_point :
      (fun ω =>
        compositeObjective f g (xPlus ω) - L * stepNorm ω -
          pNorm ω * stepNorm ω +
            (1 / h) * bregmanDivergence phi gradPhi (xPlus ω) x) ≤ᵐ[μ]
        fun ω =>
          mirrorProximalGradientModel f g (fun _ : E => p ω)
            phi gradPhi h x (xPlus ω) := by
    filter_upwards [hxPlus, hstep_point, hpNorm_point] with ω hxω hstepω hpω
    have hlip_norm :
        f (xPlus ω) - f x ≤ L * ‖xPlus ω - x‖ := by
      have hraw := hLip.le_add_mul hxω hx
      have hdist : dist (xPlus ω) x = ‖xPlus ω - x‖ := by
        rw [dist_eq_norm]
      have hupper : f (xPlus ω) ≤ f x + L * ‖xPlus ω - x‖ := by
        simpa [Real.coe_toNNReal L hL_nonneg, hdist] using hraw
      nlinarith
    have hlip : f (xPlus ω) - f x ≤ L * stepNorm ω := by
      have hscale :
          L * ‖xPlus ω - x‖ ≤ L * stepNorm ω :=
        mul_le_mul_of_nonneg_left hstepω hL_nonneg
      exact hlip_norm.trans hscale
    have hgrad_norm :
        -inner ℝ (p ω) (xPlus ω - x) ≤
          ‖p ω‖ * ‖xPlus ω - x‖ := by
      have habs := abs_real_inner_le_norm (p ω) (xPlus ω - x)
      exact (neg_le_abs _).trans habs
    have hpNorm_nonnegω : 0 ≤ pNorm ω :=
      (norm_nonneg _).trans hpω
    have hprod :
        ‖p ω‖ * ‖xPlus ω - x‖ ≤ pNorm ω * stepNorm ω :=
      mul_le_mul hpω hstepω (norm_nonneg _) hpNorm_nonnegω
    have hgrad :
        -inner ℝ (p ω) (xPlus ω - x) ≤ pNorm ω * stepNorm ω :=
      hgrad_norm.trans hprod
    exact
      chewi121_nonsmooth_raw_point_of_sampled_model
        (f := f) (g := g) (phi := phi) (gradPhi := gradPhi)
        (h := h) (lip := L * stepNorm ω)
        (grad := pNorm ω * stepNorm ω)
        (x := x) (xPlus := xPlus ω) (p := p ω)
        hlip hgrad
  have hphi_point :
      (fun ω => (alphaPhi / 2) * ‖xPlus ω - x‖ ^ (2 : ℕ)) ≤ᵐ[μ]
        fun ω => bregmanDivergence phi gradPhi (xPlus ω) x := by
    filter_upwards [hxPlus] with ω hω
    exact
      bregmanDivergence_lower_of_firstOrderStrongConvexOn
        (C := C) (phi := phi) (gradPhi := gradPhi)
        (alphaPhi := alphaPhi) (x := x) (xPlus := xPlus ω)
        hphi hx hω
  have hstep_avg : (∫ ω, stepNorm ω ∂μ) ≤ stepRms :=
    chewi121_integral_average_le_l2_root_of_probability
      (μ := μ) (stepNorm := stepNorm) (stepRms := stepRms)
      hstep_nonneg hstep_mem hstep_root
  have hlip_bound :
      (∫ ω, L * stepNorm ω ∂μ) ≤ L * stepRms :=
    chewi121_integral_linear_component_bound
      (term := fun ω => L * stepNorm ω) (stepNorm := stepNorm)
      (L := L) (stepRms := stepRms)
      hL_nonneg hlip_int hstepNorm_int hstep_avg
      (Filter.Eventually.of_forall fun _ => le_rfl)
  have hgrad_bound :
      (∫ ω, pNorm ω * stepNorm ω ∂μ) ≤ L * stepRms :=
    chewi121_integral_noise_bound_of_l2_roots
      (noise := fun ω => pNorm ω * stepNorm ω)
      (varianceNorm := pNorm) (stepNorm := stepNorm)
      (varianceRms := L) (stepRms := stepRms)
      hgrad_int hpNorm_nonneg hstep_nonneg hpNorm_mem hstep_mem
      (Filter.Eventually.of_forall fun _ => le_rfl) hpNorm_root hstep_root
  have hraw :=
    chewi121_nonsmooth_integral_raw_component_bound
      (Fplus := fun ω => compositeObjective f g (xPlus ω))
      (lip := fun ω => L * stepNorm ω)
      (grad := fun ω => pNorm ω * stepNorm ω)
      (Dphi := fun ω => bregmanDivergence phi gradPhi (xPlus ω) x)
      (psi := fun ω =>
        mirrorProximalGradientModel f g (fun _ : E => p ω)
          phi gradPhi h x (xPlus ω))
      (h := h) (psiNext := psiNext)
      hFplus hlip_int hgrad_int hDphi hpsi_int hraw_point hpsi
  have hphi_lower :=
    chewi121_integral_mirror_lower_component_bound
      (Dphi := fun ω => bregmanDivergence phi gradPhi (xPlus ω) x)
      (stepSq := fun ω => ‖xPlus ω - x‖ ^ (2 : ℕ))
      (alphaPhi := alphaPhi) (stepRms := stepRms)
      halphaPhi_nonneg hDphi hstepSq hstepRms_sq hphi_point
  exact
    chewi121_nonsmooth_hcore_of_expected_components
      (alphaPhi := alphaPhi) (L := L) (h := h)
      (expectedNext := ∫ ω, compositeObjective f g (xPlus ω) ∂μ)
      (psiNext := psiNext)
      (DphiAvg := ∫ ω, bregmanDivergence phi gradPhi (xPlus ω) x ∂μ)
      (lipTerm := ∫ ω, L * stepNorm ω ∂μ)
      (gradTerm := ∫ ω, pNorm ω * stepNorm ω ∂μ)
      (stepRms := stepRms)
      hh hraw hphi_lower hlip_bound hgrad_bound

/--
Bochner-integral non-smooth `hcore` theorem.
-/
theorem chewi121_nonsmooth_hcore_of_integral_components
    {Ω : Type*} [MeasurableSpace Ω] {μ : Measure Ω}
    {Fplus lip grad Dphi psi stepSq stepNorm : Ω -> ℝ}
    {alphaPhi L h psiNext stepRms : ℝ}
    (hh : 0 < h) (halphaPhi_nonneg : 0 ≤ alphaPhi) (hL_nonneg : 0 ≤ L)
    (hFplus : Integrable Fplus μ) (hlip_int : Integrable lip μ)
    (hgrad_int : Integrable grad μ) (hDphi : Integrable Dphi μ)
    (hpsi_int : Integrable psi μ) (hstepSq : Integrable stepSq μ)
    (hstepNorm : Integrable stepNorm μ)
    (hraw_point : (fun ω =>
      Fplus ω - lip ω - grad ω + (1 / h) * Dphi ω) ≤ᵐ[μ] psi)
    (hpsi : (∫ ω, psi ω ∂μ) ≤ psiNext)
    (hstepRms_sq : stepRms ^ (2 : ℕ) ≤ ∫ ω, stepSq ω ∂μ)
    (hphi_point : (fun ω => (alphaPhi / 2) * stepSq ω) ≤ᵐ[μ] Dphi)
    (hstep_avg : (∫ ω, stepNorm ω ∂μ) ≤ stepRms)
    (hlip_point : lip ≤ᵐ[μ] fun ω => L * stepNorm ω)
    (hgrad_point : grad ≤ᵐ[μ] fun ω => L * stepNorm ω) :
    (∫ ω, Fplus ω ∂μ) +
        (alphaPhi / (2 * h)) * stepRms ^ (2 : ℕ) -
          (2 * L) * stepRms ≤ psiNext := by
  have hraw :=
    chewi121_nonsmooth_integral_raw_component_bound
      (Fplus := Fplus) (lip := lip) (grad := grad) (Dphi := Dphi)
      (psi := psi) (h := h) (psiNext := psiNext)
      hFplus hlip_int hgrad_int hDphi hpsi_int hraw_point hpsi
  have hphi_lower :=
    chewi121_integral_mirror_lower_component_bound
      (Dphi := Dphi) (stepSq := stepSq) (alphaPhi := alphaPhi)
      (stepRms := stepRms)
      halphaPhi_nonneg hDphi hstepSq hstepRms_sq hphi_point
  have hlip :=
    chewi121_integral_linear_component_bound
      (term := lip) (stepNorm := stepNorm) (L := L) (stepRms := stepRms)
      hL_nonneg hlip_int hstepNorm hstep_avg hlip_point
  have hgrad :=
    chewi121_integral_linear_component_bound
      (term := grad) (stepNorm := stepNorm) (L := L) (stepRms := stepRms)
      hL_nonneg hgrad_int hstepNorm hstep_avg hgrad_point
  exact
    chewi121_nonsmooth_hcore_of_expected_components
      (alphaPhi := alphaPhi) (L := L) (h := h)
      (expectedNext := ∫ ω, Fplus ω ∂μ) (psiNext := psiNext)
      (DphiAvg := ∫ ω, Dphi ω ∂μ)
      (lipTerm := ∫ ω, lip ω ∂μ)
      (gradTerm := ∫ ω, grad ω ∂μ)
      (stepRms := stepRms)
      hh hraw hphi_lower hlip hgrad

/--
Smooth-case Chewi Theorem 12.1 rate from the expected model bounds plus the
source stochastic lower-bound estimate for `E psi_x(x+)`.
-/
theorem chewi121_smooth_weightedAverageGap_le_geometric_of_model_bounds
    {alphaF alphaG alphaPhi sigma dim h Fstar : ℝ}
    (htotal_pos : 0 < alphaF + alphaG)
    (hh : 0 < h) (hden_pos : 0 < 1 + alphaG * h)
    (hlambda_pos : 0 < chewi109Lambda alphaF alphaG h)
    (D gap psiNext psiStar expectedNext : ℕ -> ℝ) {N : ℕ} (hN : N ≠ 0)
    (hD_N_nonneg : 0 ≤ D N)
    (hgrowth : ∀ n, n < N ->
      (alphaG + 1 / h) * D (n + 1) + psiNext n ≤ psiStar n)
    (hstar_upper : ∀ n, n < N ->
      psiStar n ≤ Fstar + ((1 - alphaF * h) / h) * D n)
    (hmodel_lower : ∀ n, n < N ->
      expectedNext n - sigma ^ (2 : ℕ) * dim * h / alphaPhi ≤ psiNext n)
    (hgap_sum : ∀ n, n < N -> Fstar + gap (n + 1) = expectedNext n) :
    (1 / (∑ n ∈ Finset.range N,
          (chewi109Lambda alphaF alphaG h) ^ (N - 1 - n))) *
        (∑ n ∈ Finset.range N,
          (chewi109Lambda alphaF alphaG h) ^ (N - 1 - n) * gap (n + 1)) ≤
      (alphaF + alphaG) /
          (((chewi109Lambda alphaF alphaG h) ^ N)⁻¹ - 1) * D 0 +
        sigma ^ (2 : ℕ) * dim * h / alphaPhi := by
  have hnext_lower : ∀ n, n < N ->
      Fstar + gap (n + 1) -
          sigma ^ (2 : ℕ) * dim * h / alphaPhi ≤ psiNext n := by
    intro n hn
    exact
      chewi121_smooth_next_lower_of_expected_model_error
        (Fstar := Fstar) (gap := gap (n + 1))
        (expectedNext := expectedNext n) (psiNext := psiNext n)
        (sigma := sigma) (dim := dim) (alphaPhi := alphaPhi) (h := h)
        (hmodel_lower n hn) (hgap_sum n hn)
  exact
    chewi121_weightedAverageGap_le_geometric_of_model_bounds
      (alphaF := alphaF) (alphaG := alphaG) (h := h)
      (modelError := sigma ^ (2 : ℕ) * dim * h / alphaPhi) (Fstar := Fstar)
      htotal_pos hh hden_pos hlambda_pos D gap psiNext psiStar hN
      hD_N_nonneg hgrowth hstar_upper hnext_lower

/--
Non-smooth-case Chewi Theorem 12.1 rate from the expected model bounds plus
the source stochastic lower-bound estimate for `E psi_x(x+)`.
-/
theorem chewi121_nonsmooth_weightedAverageGap_le_geometric_of_model_bounds
    {alphaF alphaG alphaPhi L h Fstar : ℝ}
    (htotal_pos : 0 < alphaF + alphaG)
    (hh : 0 < h) (hden_pos : 0 < 1 + alphaG * h)
    (hlambda_pos : 0 < chewi109Lambda alphaF alphaG h)
    (D gap psiNext psiStar expectedNext : ℕ -> ℝ) {N : ℕ} (hN : N ≠ 0)
    (hD_N_nonneg : 0 ≤ D N)
    (hgrowth : ∀ n, n < N ->
      (alphaG + 1 / h) * D (n + 1) + psiNext n ≤ psiStar n)
    (hstar_upper : ∀ n, n < N ->
      psiStar n ≤ Fstar + ((1 - alphaF * h) / h) * D n)
    (hmodel_lower : ∀ n, n < N ->
      expectedNext n - 2 * L ^ (2 : ℕ) * h / alphaPhi ≤ psiNext n)
    (hgap_sum : ∀ n, n < N -> Fstar + gap (n + 1) = expectedNext n) :
    (1 / (∑ n ∈ Finset.range N,
          (chewi109Lambda alphaF alphaG h) ^ (N - 1 - n))) *
        (∑ n ∈ Finset.range N,
          (chewi109Lambda alphaF alphaG h) ^ (N - 1 - n) * gap (n + 1)) ≤
      (alphaF + alphaG) /
          (((chewi109Lambda alphaF alphaG h) ^ N)⁻¹ - 1) * D 0 +
        2 * L ^ (2 : ℕ) * h / alphaPhi := by
  have hnext_lower : ∀ n, n < N ->
      Fstar + gap (n + 1) - 2 * L ^ (2 : ℕ) * h / alphaPhi ≤ psiNext n := by
    intro n hn
    exact
      chewi121_nonsmooth_next_lower_of_expected_model_error
        (Fstar := Fstar) (gap := gap (n + 1))
        (expectedNext := expectedNext n) (psiNext := psiNext n)
        (L := L) (alphaPhi := alphaPhi) (h := h)
        (hmodel_lower n hn) (hgap_sum n hn)
  exact
    chewi121_weightedAverageGap_le_geometric_of_model_bounds
      (alphaF := alphaF) (alphaG := alphaG) (h := h)
      (modelError := 2 * L ^ (2 : ℕ) * h / alphaPhi) (Fstar := Fstar)
      htotal_pos hh hden_pos hlambda_pos D gap psiNext psiStar hN
      hD_N_nonneg hgrowth hstar_upper hnext_lower

/--
Smooth-case Chewi Theorem 12.1 rate from the expected model bounds plus the
RMS variance lower-bound proof state.
-/
theorem chewi121_smooth_weightedAverageGap_le_geometric_of_rms_model_bounds
    {alphaF alphaG alphaPhi sigma dim h Fstar : ℝ}
    (htotal_pos : 0 < alphaF + alphaG)
    (hh : 0 < h) (halphaPhi : 0 < alphaPhi)
    (hden_pos : 0 < 1 + alphaG * h)
    (hlambda_pos : 0 < chewi109Lambda alphaF alphaG h)
    (D gap psiNext psiStar expectedNext varianceRms stepRms : ℕ -> ℝ)
    {N : ℕ} (hN : N ≠ 0)
    (hD_N_nonneg : 0 ≤ D N)
    (hgrowth : ∀ n, n < N ->
      (alphaG + 1 / h) * D (n + 1) + psiNext n ≤ psiStar n)
    (hstar_upper : ∀ n, n < N ->
      psiStar n ≤ Fstar + ((1 - alphaF * h) / h) * D n)
    (hvariance : ∀ n, n < N ->
      varianceRms n ^ (2 : ℕ) ≤ sigma ^ (2 : ℕ) * dim)
    (hnext_core : ∀ n, n < N ->
      expectedNext n + (alphaPhi / (4 * h)) * stepRms n ^ (2 : ℕ) -
          varianceRms n * stepRms n ≤ psiNext n)
    (hgap_sum : ∀ n, n < N -> Fstar + gap (n + 1) = expectedNext n) :
    (1 / (∑ n ∈ Finset.range N,
          (chewi109Lambda alphaF alphaG h) ^ (N - 1 - n))) *
        (∑ n ∈ Finset.range N,
          (chewi109Lambda alphaF alphaG h) ^ (N - 1 - n) * gap (n + 1)) ≤
      (alphaF + alphaG) /
          (((chewi109Lambda alphaF alphaG h) ^ N)⁻¹ - 1) * D 0 +
        sigma ^ (2 : ℕ) * dim * h / alphaPhi := by
  refine
    chewi121_smooth_weightedAverageGap_le_geometric_of_model_bounds
      (alphaF := alphaF) (alphaG := alphaG) (alphaPhi := alphaPhi)
      (sigma := sigma) (dim := dim) (h := h) (Fstar := Fstar)
      htotal_pos hh hden_pos hlambda_pos D gap psiNext psiStar expectedNext
      hN hD_N_nonneg hgrowth hstar_upper ?_ hgap_sum
  intro n hn
  exact
    chewi121_smooth_expected_model_lower_of_rms_bound
      (alphaPhi := alphaPhi) (sigma := sigma) (dim := dim) (h := h)
      (varianceRms := varianceRms n) (stepRms := stepRms n)
      (expectedNext := expectedNext n) (psiNext := psiNext n)
      hh halphaPhi (hvariance n hn) (hnext_core n hn)

/--
Non-smooth-case Chewi Theorem 12.1 rate from the expected model bounds plus
the bounded-gradient RMS lower-bound proof state.
-/
theorem chewi121_nonsmooth_weightedAverageGap_le_geometric_of_rms_model_bounds
    {alphaF alphaG alphaPhi L h Fstar : ℝ}
    (htotal_pos : 0 < alphaF + alphaG)
    (hh : 0 < h) (halphaPhi : 0 < alphaPhi)
    (hden_pos : 0 < 1 + alphaG * h)
    (hlambda_pos : 0 < chewi109Lambda alphaF alphaG h)
    (D gap psiNext psiStar expectedNext stepRms : ℕ -> ℝ) {N : ℕ}
    (hN : N ≠ 0)
    (hD_N_nonneg : 0 ≤ D N)
    (hgrowth : ∀ n, n < N ->
      (alphaG + 1 / h) * D (n + 1) + psiNext n ≤ psiStar n)
    (hstar_upper : ∀ n, n < N ->
      psiStar n ≤ Fstar + ((1 - alphaF * h) / h) * D n)
    (hnext_core : ∀ n, n < N ->
      expectedNext n + (alphaPhi / (2 * h)) * stepRms n ^ (2 : ℕ) -
          (2 * L) * stepRms n ≤ psiNext n)
    (hgap_sum : ∀ n, n < N -> Fstar + gap (n + 1) = expectedNext n) :
    (1 / (∑ n ∈ Finset.range N,
          (chewi109Lambda alphaF alphaG h) ^ (N - 1 - n))) *
        (∑ n ∈ Finset.range N,
          (chewi109Lambda alphaF alphaG h) ^ (N - 1 - n) * gap (n + 1)) ≤
      (alphaF + alphaG) /
          (((chewi109Lambda alphaF alphaG h) ^ N)⁻¹ - 1) * D 0 +
        2 * L ^ (2 : ℕ) * h / alphaPhi := by
  refine
    chewi121_nonsmooth_weightedAverageGap_le_geometric_of_model_bounds
      (alphaF := alphaF) (alphaG := alphaG) (alphaPhi := alphaPhi)
      (L := L) (h := h) (Fstar := Fstar)
      htotal_pos hh hden_pos hlambda_pos D gap psiNext psiStar expectedNext
      hN hD_N_nonneg hgrowth hstar_upper ?_ hgap_sum
  intro n hn
  exact
    chewi121_nonsmooth_expected_model_lower_of_rms_bound
      (alphaPhi := alphaPhi) (L := L) (h := h)
      (stepRms := stepRms n) (expectedNext := expectedNext n)
      (psiNext := psiNext n)
      hh halphaPhi (hnext_core n hn)

/--
Finite-support smooth Chewi Theorem 12.1 rate.  This is the finite
stochastic-gradient theorem obtained by combining the per-sample component
model bounds with the already verified SMPGD Gronwall/rate layer.
-/
theorem chewi121_smooth_weightedAverageGap_le_geometric_of_finite_components
    {ι : Type*} [DecidableEq ι] (s : Finset ι)
    {alphaF alphaG alphaPhi sigma dim h Fstar : ℝ}
    (htotal_pos : 0 < alphaF + alphaG)
    (hh : 0 < h) (halphaPhi : 0 < alphaPhi)
    (hden_pos : 0 < 1 + alphaG * h)
    (hlambda_pos : 0 < chewi109Lambda alphaF alphaG h)
    (D gap psiNext psiStar varianceRms stepRms : ℕ -> ℝ)
    (w Fplus Df Dphi noise psi stepSq : ℕ -> ι -> ℝ)
    {N : ℕ} (hN : N ≠ 0)
    (hD_N_nonneg : 0 ≤ D N)
    (hgrowth : ∀ n, n < N ->
      (alphaG + 1 / h) * D (n + 1) + psiNext n ≤ psiStar n)
    (hstar_upper : ∀ n, n < N ->
      psiStar n ≤ Fstar + ((1 - alphaF * h) / h) * D n)
    (hw_nonneg : ∀ n, n < N -> ∀ i ∈ s, 0 ≤ w n i)
    (hraw_point : ∀ n, n < N -> ∀ i ∈ s,
      Fplus n i - Df n i + (1 / h) * Dphi n i - noise n i ≤ psi n i)
    (hpsi : ∀ n, n < N ->
      (∑ i ∈ s, w n i * psi n i) ≤ psiNext n)
    (hdf_point : ∀ n, n < N -> ∀ i ∈ s,
      Df n i ≤ (1 / (2 * h)) * Dphi n i)
    (hstepRms_sq : ∀ n, n < N ->
      stepRms n ^ (2 : ℕ) ≤ ∑ i ∈ s, w n i * stepSq n i)
    (hphi_point : ∀ n, n < N -> ∀ i ∈ s,
      (alphaPhi / 2) * stepSq n i ≤ Dphi n i)
    (hnoise : ∀ n, n < N ->
      (∑ i ∈ s, w n i * noise n i) ≤ varianceRms n * stepRms n)
    (hvariance : ∀ n, n < N ->
      varianceRms n ^ (2 : ℕ) ≤ sigma ^ (2 : ℕ) * dim)
    (hgap_sum : ∀ n, n < N ->
      Fstar + gap (n + 1) = ∑ i ∈ s, w n i * Fplus n i) :
    (1 / (∑ n ∈ Finset.range N,
          (chewi109Lambda alphaF alphaG h) ^ (N - 1 - n))) *
        (∑ n ∈ Finset.range N,
          (chewi109Lambda alphaF alphaG h) ^ (N - 1 - n) * gap (n + 1)) ≤
      (alphaF + alphaG) /
          (((chewi109Lambda alphaF alphaG h) ^ N)⁻¹ - 1) * D 0 +
        sigma ^ (2 : ℕ) * dim * h / alphaPhi := by
  refine
    chewi121_smooth_weightedAverageGap_le_geometric_of_rms_model_bounds
      (alphaF := alphaF) (alphaG := alphaG) (alphaPhi := alphaPhi)
      (sigma := sigma) (dim := dim) (h := h) (Fstar := Fstar)
      htotal_pos hh halphaPhi hden_pos hlambda_pos D gap psiNext psiStar
      (fun n => ∑ i ∈ s, w n i * Fplus n i) varianceRms stepRms
      hN hD_N_nonneg hgrowth hstar_upper hvariance ?_ hgap_sum
  intro n hn
  exact
    chewi121_smooth_hcore_of_finite_components
      (s := s) (w := w n) (Fplus := Fplus n) (Df := Df n)
      (Dphi := Dphi n) (noise := noise n) (psi := psi n)
      (stepSq := stepSq n) (alphaPhi := alphaPhi) (h := h)
      (psiNext := psiNext n) (varianceRms := varianceRms n)
      (stepRms := stepRms n)
      hh halphaPhi.le (hw_nonneg n hn) (hraw_point n hn) (hpsi n hn)
      (hdf_point n hn) (hstepRms_sq n hn) (hphi_point n hn) (hnoise n hn)

/--
Finite smooth sampled-model Chewi Theorem 12.1 rate.  This wrapper discharges
the growth inequality from sampled MPGD steps, the right-hand star model from
finite unbiasedness, and the next-iterate lower model from the sampled
smooth `hcore` theorem.
-/
theorem chewi121_smooth_weightedAverageGap_le_geometric_of_finite_sampled_models
    {E : Type*} [NormedAddCommGroup E] [InnerProductSpace ℝ E]
    {ι : Type*} [DecidableEq ι] (s : Finset ι)
    {C : Set E} {f g : E -> ℝ} {gradF : E -> E}
    {phi : E -> ℝ} {gradPhi : E -> E}
    {alphaF alphaG alphaPhi betaF sigma dim h Fstar : ℝ}
    (htotal_pos : 0 < alphaF + alphaG)
    (hh : 0 < h) (halphaPhi : 0 < alphaPhi)
    (hden_pos : 0 < 1 + alphaG * h)
    (hlambda_pos : 0 < chewi109Lambda alphaF alphaG h)
    (D gap varianceRms stepRms : ℕ -> ℝ)
    (x : ℕ -> E) (xStar : E)
    (w noise : ℕ -> ι -> ℝ) (p xPlus : ℕ -> ι -> E)
    {N : ℕ} (hN : N ≠ 0)
    (hD_N_nonneg : 0 ≤ D N)
    (hconvF : RelativelyStrongConvexOn C f gradF phi gradPhi alphaF)
    (hsmooth : RelativelySmoothOn C f gradF phi gradPhi betaF)
    (hbeta : betaF ≤ 1 / (2 * h))
    (hphi : FirstOrderStrongConvexOn C phi gradPhi alphaPhi)
    (hx : ∀ n, n < N -> x n ∈ C)
    (hxStar : xStar ∈ C)
    (hxPlus : ∀ n, n < N -> ∀ i ∈ s, xPlus n i ∈ C)
    (hFstar : Fstar = compositeObjective f g xStar)
    (hD_current : ∀ n, n < N ->
      D n = bregmanDivergence phi gradPhi xStar (x n))
    (hD_next : ∀ n, n < N ->
      D (n + 1) =
        ∑ i ∈ s, w n i * bregmanDivergence phi gradPhi xStar (xPlus n i))
    (hw_nonneg : ∀ n, n < N -> ∀ i ∈ s, 0 ≤ w n i)
    (hstep : ∀ n, n < N -> ∀ i ∈ s,
      IsMirrorProximalGradientStep C f g (fun _ : E => p n i)
        phi gradPhi alphaG h (x n) (xPlus n i))
    (hmass : ∀ n, n < N -> ∑ i ∈ s, w n i = 1)
    (hunbiased : ∀ n, n < N ->
      (∑ i ∈ s, w n i • p n i) = gradF (x n))
    (hnoise_point : ∀ n, n < N -> ∀ i ∈ s,
      -inner ℝ (p n i - gradF (x n)) (xPlus n i - x n) ≤
        noise n i)
    (hstepRms_sq : ∀ n, n < N ->
      stepRms n ^ (2 : ℕ) ≤
        ∑ i ∈ s, w n i * ‖xPlus n i - x n‖ ^ (2 : ℕ))
    (hnoise : ∀ n, n < N ->
      (∑ i ∈ s, w n i * noise n i) ≤ varianceRms n * stepRms n)
    (hvariance : ∀ n, n < N ->
      varianceRms n ^ (2 : ℕ) ≤ sigma ^ (2 : ℕ) * dim)
    (hgap_sum : ∀ n, n < N ->
      Fstar + gap (n + 1) =
        ∑ i ∈ s, w n i * compositeObjective f g (xPlus n i)) :
    (1 / (∑ n ∈ Finset.range N,
          (chewi109Lambda alphaF alphaG h) ^ (N - 1 - n))) *
        (∑ n ∈ Finset.range N,
          (chewi109Lambda alphaF alphaG h) ^ (N - 1 - n) * gap (n + 1)) ≤
      (alphaF + alphaG) /
          (((chewi109Lambda alphaF alphaG h) ^ N)⁻¹ - 1) * D 0 +
        sigma ^ (2 : ℕ) * dim * h / alphaPhi := by
  refine
    chewi121_smooth_weightedAverageGap_le_geometric_of_rms_model_bounds
      (alphaF := alphaF) (alphaG := alphaG) (alphaPhi := alphaPhi)
      (sigma := sigma) (dim := dim) (h := h) (Fstar := Fstar)
      htotal_pos hh halphaPhi hden_pos hlambda_pos D gap
      (fun n =>
        ∑ i ∈ s, w n i *
          mirrorProximalGradientModel f g (fun _ : E => p n i)
            phi gradPhi h (x n) (xPlus n i))
      (fun n =>
        ∑ i ∈ s, w n i *
          mirrorProximalGradientModel f g (fun _ : E => p n i)
            phi gradPhi h (x n) xStar)
      (fun n => ∑ i ∈ s, w n i * compositeObjective f g (xPlus n i))
      varianceRms stepRms hN hD_N_nonneg ?_ ?_ hvariance ?_ hgap_sum
  · intro n hn
    have hgrowth :=
      chewi121_finite_sampled_growth_of_steps
        (s := s) (C := C) (f := f) (g := g) (phi := phi)
        (gradPhi := gradPhi) (alphaG := alphaG) (h := h)
        (x := x n) (y := xStar) (p := p n) (xPlus := xPlus n)
        (w := w n) (hw_nonneg n hn) (hstep n hn) hxStar
    simpa [hD_next n hn] using hgrowth
  · intro n hn
    have hupper :=
      chewi121_finite_sampled_star_upper_of_unbiased
        (s := s) (C := C) (f := f) (g := g) (gradF := gradF)
        (phi := phi) (gradPhi := gradPhi) (alphaF := alphaF)
        (h := h) (x := x n) (y := xStar) (p := p n) (w := w n)
        hh (hmass n hn) (hunbiased n hn) hconvF (hx n hn) hxStar
    simpa [hFstar, hD_current n hn] using hupper
  · intro n hn
    exact
      chewi121_smooth_hcore_of_finite_sampled_models
        (s := s) (C := C) (f := f) (g := g) (gradF := gradF)
        (phi := phi) (gradPhi := gradPhi)
        (alphaPhi := alphaPhi) (betaF := betaF) (h := h)
        (psiNext :=
          ∑ i ∈ s, w n i *
            mirrorProximalGradientModel f g (fun _ : E => p n i)
              phi gradPhi h (x n) (xPlus n i))
        (varianceRms := varianceRms n) (stepRms := stepRms n)
        (x := x n) (p := p n) (xPlus := xPlus n)
        (w := w n) (noise := noise n)
        hh halphaPhi.le (hw_nonneg n hn) hsmooth hbeta hphi
        (hx n hn) (hxPlus n hn) (hnoise_point n hn) (le_refl _)
        (hstepRms_sq n hn) (hnoise n hn)

/-- Finite-support non-smooth Chewi Theorem 12.1 rate. -/
theorem chewi121_nonsmooth_weightedAverageGap_le_geometric_of_finite_components
    {ι : Type*} [DecidableEq ι] (s : Finset ι)
    {alphaF alphaG alphaPhi L h Fstar : ℝ}
    (htotal_pos : 0 < alphaF + alphaG)
    (hh : 0 < h) (halphaPhi : 0 < alphaPhi) (hL_nonneg : 0 ≤ L)
    (hden_pos : 0 < 1 + alphaG * h)
    (hlambda_pos : 0 < chewi109Lambda alphaF alphaG h)
    (D gap psiNext psiStar stepRms : ℕ -> ℝ)
    (w Fplus lip grad Dphi psi stepSq stepNorm : ℕ -> ι -> ℝ)
    {N : ℕ} (hN : N ≠ 0)
    (hD_N_nonneg : 0 ≤ D N)
    (hgrowth : ∀ n, n < N ->
      (alphaG + 1 / h) * D (n + 1) + psiNext n ≤ psiStar n)
    (hstar_upper : ∀ n, n < N ->
      psiStar n ≤ Fstar + ((1 - alphaF * h) / h) * D n)
    (hw_nonneg : ∀ n, n < N -> ∀ i ∈ s, 0 ≤ w n i)
    (hraw_point : ∀ n, n < N -> ∀ i ∈ s,
      Fplus n i - lip n i - grad n i + (1 / h) * Dphi n i ≤ psi n i)
    (hpsi : ∀ n, n < N ->
      (∑ i ∈ s, w n i * psi n i) ≤ psiNext n)
    (hstepRms_sq : ∀ n, n < N ->
      stepRms n ^ (2 : ℕ) ≤ ∑ i ∈ s, w n i * stepSq n i)
    (hphi_point : ∀ n, n < N -> ∀ i ∈ s,
      (alphaPhi / 2) * stepSq n i ≤ Dphi n i)
    (hstep_avg : ∀ n, n < N ->
      (∑ i ∈ s, w n i * stepNorm n i) ≤ stepRms n)
    (hlip_point : ∀ n, n < N -> ∀ i ∈ s,
      lip n i ≤ L * stepNorm n i)
    (hgrad_point : ∀ n, n < N -> ∀ i ∈ s,
      grad n i ≤ L * stepNorm n i)
    (hgap_sum : ∀ n, n < N ->
      Fstar + gap (n + 1) = ∑ i ∈ s, w n i * Fplus n i) :
    (1 / (∑ n ∈ Finset.range N,
          (chewi109Lambda alphaF alphaG h) ^ (N - 1 - n))) *
        (∑ n ∈ Finset.range N,
          (chewi109Lambda alphaF alphaG h) ^ (N - 1 - n) * gap (n + 1)) ≤
      (alphaF + alphaG) /
          (((chewi109Lambda alphaF alphaG h) ^ N)⁻¹ - 1) * D 0 +
        2 * L ^ (2 : ℕ) * h / alphaPhi := by
  refine
    chewi121_nonsmooth_weightedAverageGap_le_geometric_of_rms_model_bounds
      (alphaF := alphaF) (alphaG := alphaG) (alphaPhi := alphaPhi)
      (L := L) (h := h) (Fstar := Fstar)
      htotal_pos hh halphaPhi hden_pos hlambda_pos D gap psiNext psiStar
      (fun n => ∑ i ∈ s, w n i * Fplus n i) stepRms
      hN hD_N_nonneg hgrowth hstar_upper ?_ hgap_sum
  intro n hn
  exact
    chewi121_nonsmooth_hcore_of_finite_components
      (s := s) (w := w n) (Fplus := Fplus n) (lip := lip n)
      (grad := grad n) (Dphi := Dphi n) (psi := psi n)
      (stepSq := stepSq n) (stepNorm := stepNorm n)
      (alphaPhi := alphaPhi) (L := L) (h := h)
      (psiNext := psiNext n) (stepRms := stepRms n)
      hh halphaPhi.le hL_nonneg (hw_nonneg n hn) (hraw_point n hn)
      (hpsi n hn) (hstepRms_sq n hn) (hphi_point n hn)
      (hstep_avg n hn) (hlip_point n hn) (hgrad_point n hn)

/--
Finite non-smooth sampled-model Chewi Theorem 12.1 rate under a pointwise
sampled-gradient norm bound.  This is stronger than the source `(12.2)` L2
assumption, but it removes the remaining model-growth/star/lower fields for
bounded finite sampled oracles.
-/
theorem chewi121_nonsmooth_weightedAverageGap_le_geometric_of_finite_sampled_models
    {E : Type*} [NormedAddCommGroup E] [InnerProductSpace ℝ E]
    {ι : Type*} [DecidableEq ι] (s : Finset ι)
    {C : Set E} {f g : E -> ℝ} {gradF : E -> E}
    {phi : E -> ℝ} {gradPhi : E -> E}
    {alphaF alphaG alphaPhi L h Fstar : ℝ}
    (htotal_pos : 0 < alphaF + alphaG)
    (hh : 0 < h) (halphaPhi : 0 < alphaPhi) (hL_nonneg : 0 ≤ L)
    (hden_pos : 0 < 1 + alphaG * h)
    (hlambda_pos : 0 < chewi109Lambda alphaF alphaG h)
    (D gap stepRms : ℕ -> ℝ)
    (x : ℕ -> E) (xStar : E)
    (w : ℕ -> ι -> ℝ) (p xPlus : ℕ -> ι -> E)
    {N : ℕ} (hN : N ≠ 0)
    (hD_N_nonneg : 0 ≤ D N)
    (hconvF : RelativelyStrongConvexOn C f gradF phi gradPhi alphaF)
    (hLip : LipschitzOnWith (Real.toNNReal L) f C)
    (hphi : FirstOrderStrongConvexOn C phi gradPhi alphaPhi)
    (hx : ∀ n, n < N -> x n ∈ C)
    (hxStar : xStar ∈ C)
    (hxPlus : ∀ n, n < N -> ∀ i ∈ s, xPlus n i ∈ C)
    (hFstar : Fstar = compositeObjective f g xStar)
    (hD_current : ∀ n, n < N ->
      D n = bregmanDivergence phi gradPhi xStar (x n))
    (hD_next : ∀ n, n < N ->
      D (n + 1) =
        ∑ i ∈ s, w n i * bregmanDivergence phi gradPhi xStar (xPlus n i))
    (hw_nonneg : ∀ n, n < N -> ∀ i ∈ s, 0 ≤ w n i)
    (hstep : ∀ n, n < N -> ∀ i ∈ s,
      IsMirrorProximalGradientStep C f g (fun _ : E => p n i)
        phi gradPhi alphaG h (x n) (xPlus n i))
    (hmass : ∀ n, n < N -> ∑ i ∈ s, w n i = 1)
    (hunbiased : ∀ n, n < N ->
      (∑ i ∈ s, w n i • p n i) = gradF (x n))
    (hp_norm : ∀ n, n < N -> ∀ i ∈ s, ‖p n i‖ ≤ L)
    (hstepRms_sq : ∀ n, n < N ->
      stepRms n ^ (2 : ℕ) ≤
        ∑ i ∈ s, w n i * ‖xPlus n i - x n‖ ^ (2 : ℕ))
    (hstep_avg : ∀ n, n < N ->
      (∑ i ∈ s, w n i * ‖xPlus n i - x n‖) ≤ stepRms n)
    (hgap_sum : ∀ n, n < N ->
      Fstar + gap (n + 1) =
        ∑ i ∈ s, w n i * compositeObjective f g (xPlus n i)) :
    (1 / (∑ n ∈ Finset.range N,
          (chewi109Lambda alphaF alphaG h) ^ (N - 1 - n))) *
        (∑ n ∈ Finset.range N,
          (chewi109Lambda alphaF alphaG h) ^ (N - 1 - n) * gap (n + 1)) ≤
      (alphaF + alphaG) /
          (((chewi109Lambda alphaF alphaG h) ^ N)⁻¹ - 1) * D 0 +
        2 * L ^ (2 : ℕ) * h / alphaPhi := by
  refine
    chewi121_nonsmooth_weightedAverageGap_le_geometric_of_rms_model_bounds
      (alphaF := alphaF) (alphaG := alphaG) (alphaPhi := alphaPhi)
      (L := L) (h := h) (Fstar := Fstar)
      htotal_pos hh halphaPhi hden_pos hlambda_pos D gap
      (fun n =>
        ∑ i ∈ s, w n i *
          mirrorProximalGradientModel f g (fun _ : E => p n i)
            phi gradPhi h (x n) (xPlus n i))
      (fun n =>
        ∑ i ∈ s, w n i *
          mirrorProximalGradientModel f g (fun _ : E => p n i)
            phi gradPhi h (x n) xStar)
      (fun n => ∑ i ∈ s, w n i * compositeObjective f g (xPlus n i))
      stepRms hN hD_N_nonneg ?_ ?_ ?_ hgap_sum
  · intro n hn
    have hgrowth :=
      chewi121_finite_sampled_growth_of_steps
        (s := s) (C := C) (f := f) (g := g) (phi := phi)
        (gradPhi := gradPhi) (alphaG := alphaG) (h := h)
        (x := x n) (y := xStar) (p := p n) (xPlus := xPlus n)
        (w := w n) (hw_nonneg n hn) (hstep n hn) hxStar
    simpa [hD_next n hn] using hgrowth
  · intro n hn
    have hupper :=
      chewi121_finite_sampled_star_upper_of_unbiased
        (s := s) (C := C) (f := f) (g := g) (gradF := gradF)
        (phi := phi) (gradPhi := gradPhi) (alphaF := alphaF)
        (h := h) (x := x n) (y := xStar) (p := p n) (w := w n)
        hh (hmass n hn) (hunbiased n hn) hconvF (hx n hn) hxStar
    simpa [hFstar, hD_current n hn] using hupper
  · intro n hn
    exact
      chewi121_nonsmooth_hcore_of_finite_sampled_models
        (s := s) (C := C) (f := f) (g := g)
        (phi := phi) (gradPhi := gradPhi)
        (alphaPhi := alphaPhi) (L := L) (h := h)
        (psiNext :=
          ∑ i ∈ s, w n i *
            mirrorProximalGradientModel f g (fun _ : E => p n i)
              phi gradPhi h (x n) (xPlus n i))
        (stepRms := stepRms n)
        (x := x n) (p := p n) (xPlus := xPlus n) (w := w n)
        hh halphaPhi.le hL_nonneg (hw_nonneg n hn)
        hLip hphi (hx n hn) (hxPlus n hn) (hp_norm n hn)
        (le_refl _) (hstepRms_sq n hn) (hstep_avg n hn)

/--
Bochner-integral smooth Chewi Theorem 12.1 rate.  This lifts the
finite-support route to a supplied measure-level expectation interface.
-/
theorem chewi121_smooth_weightedAverageGap_le_geometric_of_integral_components
    {Ω : Type*} [MeasurableSpace Ω] {μ : Measure Ω}
    {alphaF alphaG alphaPhi sigma dim h Fstar : ℝ}
    (htotal_pos : 0 < alphaF + alphaG)
    (hh : 0 < h) (halphaPhi : 0 < alphaPhi)
    (hden_pos : 0 < 1 + alphaG * h)
    (hlambda_pos : 0 < chewi109Lambda alphaF alphaG h)
    (D gap psiNext psiStar varianceRms stepRms : ℕ -> ℝ)
    (Fplus Df Dphi noise psi stepSq : ℕ -> Ω -> ℝ)
    {N : ℕ} (hN : N ≠ 0)
    (hD_N_nonneg : 0 ≤ D N)
    (hgrowth : ∀ n, n < N ->
      (alphaG + 1 / h) * D (n + 1) + psiNext n ≤ psiStar n)
    (hstar_upper : ∀ n, n < N ->
      psiStar n ≤ Fstar + ((1 - alphaF * h) / h) * D n)
    (hFplus : ∀ n, n < N -> Integrable (Fplus n) μ)
    (hDf_int : ∀ n, n < N -> Integrable (Df n) μ)
    (hDphi_int : ∀ n, n < N -> Integrable (Dphi n) μ)
    (hnoise_int : ∀ n, n < N -> Integrable (noise n) μ)
    (hpsi_int : ∀ n, n < N -> Integrable (psi n) μ)
    (hstepSq_int : ∀ n, n < N -> Integrable (stepSq n) μ)
    (hraw_point : ∀ n, n < N ->
      (fun ω => Fplus n ω - Df n ω + (1 / h) * Dphi n ω - noise n ω) ≤ᵐ[μ]
        psi n)
    (hpsi : ∀ n, n < N -> (∫ ω, psi n ω ∂μ) ≤ psiNext n)
    (hdf_point : ∀ n, n < N ->
      Df n ≤ᵐ[μ] fun ω => (1 / (2 * h)) * Dphi n ω)
    (hstepRms_sq : ∀ n, n < N ->
      stepRms n ^ (2 : ℕ) ≤ ∫ ω, stepSq n ω ∂μ)
    (hphi_point : ∀ n, n < N ->
      (fun ω => (alphaPhi / 2) * stepSq n ω) ≤ᵐ[μ] Dphi n)
    (hnoise : ∀ n, n < N ->
      (∫ ω, noise n ω ∂μ) ≤ varianceRms n * stepRms n)
    (hvariance : ∀ n, n < N ->
      varianceRms n ^ (2 : ℕ) ≤ sigma ^ (2 : ℕ) * dim)
    (hgap_sum : ∀ n, n < N ->
      Fstar + gap (n + 1) = ∫ ω, Fplus n ω ∂μ) :
    (1 / (∑ n ∈ Finset.range N,
          (chewi109Lambda alphaF alphaG h) ^ (N - 1 - n))) *
        (∑ n ∈ Finset.range N,
          (chewi109Lambda alphaF alphaG h) ^ (N - 1 - n) * gap (n + 1)) ≤
      (alphaF + alphaG) /
          (((chewi109Lambda alphaF alphaG h) ^ N)⁻¹ - 1) * D 0 +
        sigma ^ (2 : ℕ) * dim * h / alphaPhi := by
  refine
    chewi121_smooth_weightedAverageGap_le_geometric_of_rms_model_bounds
      (alphaF := alphaF) (alphaG := alphaG) (alphaPhi := alphaPhi)
      (sigma := sigma) (dim := dim) (h := h) (Fstar := Fstar)
      htotal_pos hh halphaPhi hden_pos hlambda_pos D gap psiNext psiStar
      (fun n => ∫ ω, Fplus n ω ∂μ) varianceRms stepRms
      hN hD_N_nonneg hgrowth hstar_upper hvariance ?_ hgap_sum
  intro n hn
  exact
    chewi121_smooth_hcore_of_integral_components
      (μ := μ) (Fplus := Fplus n) (Df := Df n) (Dphi := Dphi n)
      (noise := noise n) (psi := psi n) (stepSq := stepSq n)
      (alphaPhi := alphaPhi) (h := h) (psiNext := psiNext n)
      (varianceRms := varianceRms n) (stepRms := stepRms n)
      hh halphaPhi.le (hFplus n hn) (hDf_int n hn) (hDphi_int n hn)
      (hnoise_int n hn) (hpsi_int n hn) (hstepSq_int n hn)
      (hraw_point n hn) (hpsi n hn) (hdf_point n hn)
      (hstepRms_sq n hn) (hphi_point n hn) (hnoise n hn)

/--
Smooth Bochner-integral Chewi Theorem 12.1 rate with the stochastic
Cauchy-Schwarz estimate discharged from L2 root bounds.  This is the next
probability-facing wrapper after the raw integral component transport.
-/
theorem chewi121_smooth_weightedAverageGap_le_geometric_of_integral_l2_noise_components
    {Ω : Type*} [MeasurableSpace Ω] {μ : Measure Ω}
    {alphaF alphaG alphaPhi sigma dim h Fstar : ℝ}
    (htotal_pos : 0 < alphaF + alphaG)
    (hh : 0 < h) (halphaPhi : 0 < alphaPhi)
    (hden_pos : 0 < 1 + alphaG * h)
    (hlambda_pos : 0 < chewi109Lambda alphaF alphaG h)
    (D gap psiNext psiStar varianceRms stepRms : ℕ -> ℝ)
    (Fplus Df Dphi noise psi stepSq varianceNorm stepNorm : ℕ -> Ω -> ℝ)
    {N : ℕ} (hN : N ≠ 0)
    (hD_N_nonneg : 0 ≤ D N)
    (hgrowth : ∀ n, n < N ->
      (alphaG + 1 / h) * D (n + 1) + psiNext n ≤ psiStar n)
    (hstar_upper : ∀ n, n < N ->
      psiStar n ≤ Fstar + ((1 - alphaF * h) / h) * D n)
    (hFplus : ∀ n, n < N -> Integrable (Fplus n) μ)
    (hDf_int : ∀ n, n < N -> Integrable (Df n) μ)
    (hDphi_int : ∀ n, n < N -> Integrable (Dphi n) μ)
    (hnoise_int : ∀ n, n < N -> Integrable (noise n) μ)
    (hpsi_int : ∀ n, n < N -> Integrable (psi n) μ)
    (hstepSq_int : ∀ n, n < N -> Integrable (stepSq n) μ)
    (hraw_point : ∀ n, n < N ->
      (fun ω => Fplus n ω - Df n ω + (1 / h) * Dphi n ω - noise n ω) ≤ᵐ[μ]
        psi n)
    (hpsi : ∀ n, n < N -> (∫ ω, psi n ω ∂μ) ≤ psiNext n)
    (hdf_point : ∀ n, n < N ->
      Df n ≤ᵐ[μ] fun ω => (1 / (2 * h)) * Dphi n ω)
    (hstepRms_sq : ∀ n, n < N ->
      stepRms n ^ (2 : ℕ) ≤ ∫ ω, stepSq n ω ∂μ)
    (hphi_point : ∀ n, n < N ->
      (fun ω => (alphaPhi / 2) * stepSq n ω) ≤ᵐ[μ] Dphi n)
    (hvariance_nonneg : ∀ n, n < N -> 0 ≤ᵐ[μ] varianceNorm n)
    (hstep_nonneg : ∀ n, n < N -> 0 ≤ᵐ[μ] stepNorm n)
    (hvariance_mem : ∀ n, n < N ->
      MemLp (varianceNorm n) (ENNReal.ofReal (2 : ℝ)) μ)
    (hstep_mem : ∀ n, n < N ->
      MemLp (stepNorm n) (ENNReal.ofReal (2 : ℝ)) μ)
    (hnoise_point : ∀ n, n < N ->
      noise n ≤ᵐ[μ] fun ω => varianceNorm n ω * stepNorm n ω)
    (hvariance_root : ∀ n, n < N ->
      (∫ ω, varianceNorm n ω ^ (2 : ℝ) ∂μ) ^ (1 / (2 : ℝ)) ≤ varianceRms n)
    (hstep_root : ∀ n, n < N ->
      (∫ ω, stepNorm n ω ^ (2 : ℝ) ∂μ) ^ (1 / (2 : ℝ)) ≤ stepRms n)
    (hvariance : ∀ n, n < N ->
      varianceRms n ^ (2 : ℕ) ≤ sigma ^ (2 : ℕ) * dim)
    (hgap_sum : ∀ n, n < N ->
      Fstar + gap (n + 1) = ∫ ω, Fplus n ω ∂μ) :
    (1 / (∑ n ∈ Finset.range N,
          (chewi109Lambda alphaF alphaG h) ^ (N - 1 - n))) *
        (∑ n ∈ Finset.range N,
          (chewi109Lambda alphaF alphaG h) ^ (N - 1 - n) * gap (n + 1)) ≤
      (alphaF + alphaG) /
          (((chewi109Lambda alphaF alphaG h) ^ N)⁻¹ - 1) * D 0 +
        sigma ^ (2 : ℕ) * dim * h / alphaPhi := by
  refine
    chewi121_smooth_weightedAverageGap_le_geometric_of_rms_model_bounds
      (alphaF := alphaF) (alphaG := alphaG) (alphaPhi := alphaPhi)
      (sigma := sigma) (dim := dim) (h := h) (Fstar := Fstar)
      htotal_pos hh halphaPhi hden_pos hlambda_pos D gap psiNext psiStar
      (fun n => ∫ ω, Fplus n ω ∂μ) varianceRms stepRms
      hN hD_N_nonneg hgrowth hstar_upper hvariance ?_ hgap_sum
  intro n hn
  exact
    chewi121_smooth_hcore_of_integral_l2_noise_components
      (μ := μ) (Fplus := Fplus n) (Df := Df n) (Dphi := Dphi n)
      (noise := noise n) (psi := psi n) (stepSq := stepSq n)
      (varianceNorm := varianceNorm n) (stepNorm := stepNorm n)
      (alphaPhi := alphaPhi) (h := h) (psiNext := psiNext n)
      (varianceRms := varianceRms n) (stepRms := stepRms n)
      hh halphaPhi.le (hFplus n hn) (hDf_int n hn) (hDphi_int n hn)
      (hnoise_int n hn) (hpsi_int n hn) (hstepSq_int n hn)
      (hraw_point n hn) (hpsi n hn) (hdf_point n hn)
      (hstepRms_sq n hn) (hphi_point n hn) (hvariance_nonneg n hn)
      (hstep_nonneg n hn) (hvariance_mem n hn) (hstep_mem n hn)
      (hnoise_point n hn) (hvariance_root n hn) (hstep_root n hn)

/--
Smooth Bochner-integral sampled-model Chewi Theorem 12.1 rate.  This combines
the sampled-model `hcore` bridge with the existing RMS-to-rate theorem.  The
expectation-level growth and star-upper fields are left supplied, because they
depend on the stochastic process/interface used to represent conditional
expectations.
-/
theorem chewi121_smooth_weightedAverageGap_le_geometric_of_integral_l2_sampled_models
    {Ω : Type*} [MeasurableSpace Ω] {μ : Measure Ω}
    {E : Type*} [NormedAddCommGroup E] [InnerProductSpace ℝ E]
    {C : Set E} {f g : E -> ℝ} {gradF : E -> E}
    {phi : E -> ℝ} {gradPhi : E -> E}
    {alphaF alphaG alphaPhi betaF sigma dim h Fstar : ℝ}
    (htotal_pos : 0 < alphaF + alphaG)
    (hh : 0 < h) (halphaPhi : 0 < alphaPhi)
    (hden_pos : 0 < 1 + alphaG * h)
    (hlambda_pos : 0 < chewi109Lambda alphaF alphaG h)
    (D gap psiNext psiStar varianceRms stepRms : ℕ -> ℝ)
    (x : ℕ -> E) (p xPlus : ℕ -> Ω -> E)
    (noise varianceNorm stepNorm : ℕ -> Ω -> ℝ)
    {N : ℕ} (hN : N ≠ 0)
    (hD_N_nonneg : 0 ≤ D N)
    (hsmooth : RelativelySmoothOn C f gradF phi gradPhi betaF)
    (hbeta : betaF ≤ 1 / (2 * h))
    (hphi : FirstOrderStrongConvexOn C phi gradPhi alphaPhi)
    (hx : ∀ n, n < N -> x n ∈ C)
    (hxPlus : ∀ n, n < N -> ∀ᵐ ω ∂μ, xPlus n ω ∈ C)
    (hgrowth : ∀ n, n < N ->
      (alphaG + 1 / h) * D (n + 1) + psiNext n ≤ psiStar n)
    (hstar_upper : ∀ n, n < N ->
      psiStar n ≤ Fstar + ((1 - alphaF * h) / h) * D n)
    (hFplus : ∀ n, n < N ->
      Integrable (fun ω => compositeObjective f g (xPlus n ω)) μ)
    (hDf : ∀ n, n < N ->
      Integrable (fun ω => bregmanDivergence f gradF (xPlus n ω) (x n)) μ)
    (hDphi : ∀ n, n < N ->
      Integrable
        (fun ω => bregmanDivergence phi gradPhi (xPlus n ω) (x n)) μ)
    (hnoise_int : ∀ n, n < N -> Integrable (noise n) μ)
    (hpsi_int : ∀ n, n < N ->
      Integrable (fun ω =>
        mirrorProximalGradientModel f g (fun _ : E => p n ω)
          phi gradPhi h (x n) (xPlus n ω)) μ)
    (hstepSq : ∀ n, n < N ->
      Integrable (fun ω => ‖xPlus n ω - x n‖ ^ (2 : ℕ)) μ)
    (hnoise_raw : ∀ n, n < N -> ∀ᵐ ω ∂μ,
      -inner ℝ (p n ω - gradF (x n)) (xPlus n ω - x n) ≤ noise n ω)
    (hpsi : ∀ n, n < N ->
      (∫ ω,
        mirrorProximalGradientModel f g (fun _ : E => p n ω)
          phi gradPhi h (x n) (xPlus n ω) ∂μ) ≤ psiNext n)
    (hstepRms_sq : ∀ n, n < N ->
      stepRms n ^ (2 : ℕ) ≤ ∫ ω, ‖xPlus n ω - x n‖ ^ (2 : ℕ) ∂μ)
    (hvariance_nonneg : ∀ n, n < N -> 0 ≤ᵐ[μ] varianceNorm n)
    (hstep_nonneg : ∀ n, n < N -> 0 ≤ᵐ[μ] stepNorm n)
    (hvariance_mem : ∀ n, n < N ->
      MemLp (varianceNorm n) (ENNReal.ofReal (2 : ℝ)) μ)
    (hstep_mem : ∀ n, n < N ->
      MemLp (stepNorm n) (ENNReal.ofReal (2 : ℝ)) μ)
    (hnoise_point : ∀ n, n < N ->
      noise n ≤ᵐ[μ] fun ω => varianceNorm n ω * stepNorm n ω)
    (hvariance_root : ∀ n, n < N ->
      (∫ ω, varianceNorm n ω ^ (2 : ℝ) ∂μ) ^ (1 / (2 : ℝ)) ≤ varianceRms n)
    (hstep_root : ∀ n, n < N ->
      (∫ ω, stepNorm n ω ^ (2 : ℝ) ∂μ) ^ (1 / (2 : ℝ)) ≤ stepRms n)
    (hvariance : ∀ n, n < N ->
      varianceRms n ^ (2 : ℕ) ≤ sigma ^ (2 : ℕ) * dim)
    (hgap_sum : ∀ n, n < N ->
      Fstar + gap (n + 1) =
        ∫ ω, compositeObjective f g (xPlus n ω) ∂μ) :
    (1 / (∑ n ∈ Finset.range N,
          (chewi109Lambda alphaF alphaG h) ^ (N - 1 - n))) *
        (∑ n ∈ Finset.range N,
          (chewi109Lambda alphaF alphaG h) ^ (N - 1 - n) * gap (n + 1)) ≤
      (alphaF + alphaG) /
          (((chewi109Lambda alphaF alphaG h) ^ N)⁻¹ - 1) * D 0 +
        sigma ^ (2 : ℕ) * dim * h / alphaPhi := by
  refine
    chewi121_smooth_weightedAverageGap_le_geometric_of_rms_model_bounds
      (alphaF := alphaF) (alphaG := alphaG) (alphaPhi := alphaPhi)
      (sigma := sigma) (dim := dim) (h := h) (Fstar := Fstar)
      htotal_pos hh halphaPhi hden_pos hlambda_pos D gap psiNext psiStar
      (fun n => ∫ ω, compositeObjective f g (xPlus n ω) ∂μ)
      varianceRms stepRms hN hD_N_nonneg hgrowth hstar_upper hvariance
      ?_ hgap_sum
  intro n hn
  exact
    chewi121_smooth_hcore_of_integral_l2_sampled_models
      (μ := μ) (C := C) (f := f) (g := g) (gradF := gradF)
      (phi := phi) (gradPhi := gradPhi)
      (alphaPhi := alphaPhi) (betaF := betaF) (h := h)
      (psiNext := psiNext n) (varianceRms := varianceRms n)
      (stepRms := stepRms n) (x := x n) (p := p n)
      (xPlus := xPlus n) (noise := noise n)
      (varianceNorm := varianceNorm n) (stepNorm := stepNorm n)
      hh halphaPhi.le hsmooth hbeta hphi (hx n hn) (hxPlus n hn)
      (hFplus n hn) (hDf n hn) (hDphi n hn) (hnoise_int n hn)
      (hpsi_int n hn) (hstepSq n hn) (hnoise_raw n hn)
      (hpsi n hn) (hstepRms_sq n hn) (hvariance_nonneg n hn)
      (hstep_nonneg n hn) (hvariance_mem n hn) (hstep_mem n hn)
      (hnoise_point n hn) (hvariance_root n hn) (hstep_root n hn)

/--
Smooth Bochner-integral sampled-model Chewi Theorem 12.1 rate with the
growth and star-upper fields discharged from a.e. sampled MPGD steps and
Bochner unbiasedness of the sampled oracle.
-/
theorem chewi121_smooth_weightedAverageGap_le_geometric_of_integral_l2_sampled_models_unbiased
    {Ω : Type*} [MeasurableSpace Ω] {μ : Measure Ω} [IsProbabilityMeasure μ]
    {E : Type*} [NormedAddCommGroup E] [InnerProductSpace ℝ E] [CompleteSpace E]
    {C : Set E} {f g : E -> ℝ} {gradF : E -> E}
    {phi : E -> ℝ} {gradPhi : E -> E}
    {alphaF alphaG alphaPhi betaF sigma dim h Fstar : ℝ}
    (htotal_pos : 0 < alphaF + alphaG)
    (hh : 0 < h) (halphaPhi : 0 < alphaPhi)
    (hden_pos : 0 < 1 + alphaG * h)
    (hlambda_pos : 0 < chewi109Lambda alphaF alphaG h)
    (D gap varianceRms stepRms : ℕ -> ℝ)
    (x : ℕ -> E) (xStar : E)
    (p xPlus : ℕ -> Ω -> E)
    (noise varianceNorm stepNorm : ℕ -> Ω -> ℝ)
    {N : ℕ} (hN : N ≠ 0)
    (hD_N_nonneg : 0 ≤ D N)
    (hconvF : RelativelyStrongConvexOn C f gradF phi gradPhi alphaF)
    (hsmooth : RelativelySmoothOn C f gradF phi gradPhi betaF)
    (hbeta : betaF ≤ 1 / (2 * h))
    (hphi : FirstOrderStrongConvexOn C phi gradPhi alphaPhi)
    (hx : ∀ n, n < N -> x n ∈ C)
    (hxStar : xStar ∈ C)
    (hxPlus : ∀ n, n < N -> ∀ᵐ ω ∂μ, xPlus n ω ∈ C)
    (hFstar : Fstar = compositeObjective f g xStar)
    (hD_current : ∀ n, n < N ->
      D n = bregmanDivergence phi gradPhi xStar (x n))
    (hD_next : ∀ n, n < N ->
      D (n + 1) =
        ∫ ω, bregmanDivergence phi gradPhi xStar (xPlus n ω) ∂μ)
    (hstep : ∀ n, n < N -> ∀ᵐ ω ∂μ,
      IsMirrorProximalGradientStep C f g (fun _ : E => p n ω)
        phi gradPhi alphaG h (x n) (xPlus n ω))
    (hp_int : ∀ n, n < N -> Integrable (p n) μ)
    (hunbiased : ∀ n, n < N ->
      (∫ ω, p n ω ∂μ) = gradF (x n))
    (hFplus : ∀ n, n < N ->
      Integrable (fun ω => compositeObjective f g (xPlus n ω)) μ)
    (hDf : ∀ n, n < N ->
      Integrable (fun ω => bregmanDivergence f gradF (xPlus n ω) (x n)) μ)
    (hDphi : ∀ n, n < N ->
      Integrable
        (fun ω => bregmanDivergence phi gradPhi (xPlus n ω) (x n)) μ)
    (hDnext_int : ∀ n, n < N ->
      Integrable
        (fun ω => bregmanDivergence phi gradPhi xStar (xPlus n ω)) μ)
    (hnoise_int : ∀ n, n < N -> Integrable (noise n) μ)
    (hpsi_int : ∀ n, n < N ->
      Integrable (fun ω =>
        mirrorProximalGradientModel f g (fun _ : E => p n ω)
          phi gradPhi h (x n) (xPlus n ω)) μ)
    (hpsiStar_int : ∀ n, n < N ->
      Integrable (fun ω =>
        mirrorProximalGradientModel f g (fun _ : E => p n ω)
          phi gradPhi h (x n) xStar) μ)
    (hstepSq : ∀ n, n < N ->
      Integrable (fun ω => ‖xPlus n ω - x n‖ ^ (2 : ℕ)) μ)
    (hnoise_raw : ∀ n, n < N -> ∀ᵐ ω ∂μ,
      -inner ℝ (p n ω - gradF (x n)) (xPlus n ω - x n) ≤ noise n ω)
    (hstepRms_sq : ∀ n, n < N ->
      stepRms n ^ (2 : ℕ) ≤ ∫ ω, ‖xPlus n ω - x n‖ ^ (2 : ℕ) ∂μ)
    (hvariance_nonneg : ∀ n, n < N -> 0 ≤ᵐ[μ] varianceNorm n)
    (hstep_nonneg : ∀ n, n < N -> 0 ≤ᵐ[μ] stepNorm n)
    (hvariance_mem : ∀ n, n < N ->
      MemLp (varianceNorm n) (ENNReal.ofReal (2 : ℝ)) μ)
    (hstep_mem : ∀ n, n < N ->
      MemLp (stepNorm n) (ENNReal.ofReal (2 : ℝ)) μ)
    (hnoise_point : ∀ n, n < N ->
      noise n ≤ᵐ[μ] fun ω => varianceNorm n ω * stepNorm n ω)
    (hvariance_root : ∀ n, n < N ->
      (∫ ω, varianceNorm n ω ^ (2 : ℝ) ∂μ) ^ (1 / (2 : ℝ)) ≤ varianceRms n)
    (hstep_root : ∀ n, n < N ->
      (∫ ω, stepNorm n ω ^ (2 : ℝ) ∂μ) ^ (1 / (2 : ℝ)) ≤ stepRms n)
    (hvariance : ∀ n, n < N ->
      varianceRms n ^ (2 : ℕ) ≤ sigma ^ (2 : ℕ) * dim)
    (hgap_sum : ∀ n, n < N ->
      Fstar + gap (n + 1) =
        ∫ ω, compositeObjective f g (xPlus n ω) ∂μ) :
    (1 / (∑ n ∈ Finset.range N,
          (chewi109Lambda alphaF alphaG h) ^ (N - 1 - n))) *
        (∑ n ∈ Finset.range N,
          (chewi109Lambda alphaF alphaG h) ^ (N - 1 - n) * gap (n + 1)) ≤
      (alphaF + alphaG) /
          (((chewi109Lambda alphaF alphaG h) ^ N)⁻¹ - 1) * D 0 +
        sigma ^ (2 : ℕ) * dim * h / alphaPhi := by
  refine
    chewi121_smooth_weightedAverageGap_le_geometric_of_integral_l2_sampled_models
      (μ := μ) (C := C) (f := f) (g := g) (gradF := gradF)
      (phi := phi) (gradPhi := gradPhi)
      (alphaF := alphaF) (alphaG := alphaG) (alphaPhi := alphaPhi)
      (betaF := betaF) (sigma := sigma) (dim := dim) (h := h)
      (Fstar := Fstar) htotal_pos hh halphaPhi hden_pos hlambda_pos D gap
      (fun n =>
        ∫ ω,
          mirrorProximalGradientModel f g (fun _ : E => p n ω)
            phi gradPhi h (x n) (xPlus n ω) ∂μ)
      (fun n =>
        ∫ ω,
          mirrorProximalGradientModel f g (fun _ : E => p n ω)
            phi gradPhi h (x n) xStar ∂μ)
      varianceRms stepRms x p xPlus noise varianceNorm stepNorm hN
      hD_N_nonneg hsmooth hbeta hphi hx hxPlus ?_ ?_
      hFplus hDf hDphi hnoise_int hpsi_int hstepSq hnoise_raw
      ?_ hstepRms_sq hvariance_nonneg hstep_nonneg hvariance_mem
      hstep_mem hnoise_point hvariance_root hstep_root hvariance hgap_sum
  · intro n hn
    exact
      chewi121_integral_sampled_growth_of_steps
        (μ := μ) (C := C) (f := f) (g := g) (phi := phi)
        (gradPhi := gradPhi) (alphaG := alphaG) (h := h)
        (x := x n) (y := xStar) (p := p n) (xPlus := xPlus n)
        (hpsiNext_int := hpsi_int n hn) (hDnext_int := hDnext_int n hn)
        (hpsiStar_int := hpsiStar_int n hn)
        (hstep := hstep n hn) hxStar (hD_next n hn) rfl rfl
  · intro n hn
    have hupper :=
      chewi121_integral_sampled_star_upper_of_unbiased
        (μ := μ) (C := C) (f := f) (g := g) (gradF := gradF)
        (phi := phi) (gradPhi := gradPhi) (alphaF := alphaF)
        (h := h) (x := x n) (y := xStar) (p := p n)
        hh (hp_int n hn) (hunbiased n hn) hconvF (hx n hn) hxStar
    simpa [hFstar, hD_current n hn] using hupper
  · intro n hn
    exact le_rfl

/--
Smooth Bochner-integral sampled-model Chewi Theorem 12.1 rate with the
displayed source variance bound `(12.1)` used directly.  The RMS variance
level is specialized to `sqrt (sigma^2 * dim)`, so the scalar domination
`varianceRms^2 <= sigma^2 * dim` is no longer a supplied field.
-/
theorem chewi121_smooth_weightedAverageGap_le_geometric_of_integral_l2_sampled_models_unbiased_of_variance_bound
    {Ω : Type*} [MeasurableSpace Ω] {μ : Measure Ω} [IsProbabilityMeasure μ]
    {E : Type*} [NormedAddCommGroup E] [InnerProductSpace ℝ E] [CompleteSpace E]
    {C : Set E} {f g : E -> ℝ} {gradF : E -> E}
    {phi : E -> ℝ} {gradPhi : E -> E}
    {alphaF alphaG alphaPhi betaF sigma dim h Fstar : ℝ}
    (htotal_pos : 0 < alphaF + alphaG)
    (hh : 0 < h) (halphaPhi : 0 < alphaPhi) (hdim_nonneg : 0 ≤ dim)
    (hden_pos : 0 < 1 + alphaG * h)
    (hlambda_pos : 0 < chewi109Lambda alphaF alphaG h)
    (D gap stepRms : ℕ -> ℝ)
    (x : ℕ -> E) (xStar : E)
    (p xPlus : ℕ -> Ω -> E)
    (noise varianceNorm stepNorm : ℕ -> Ω -> ℝ)
    {N : ℕ} (hN : N ≠ 0)
    (hD_N_nonneg : 0 ≤ D N)
    (hconvF : RelativelyStrongConvexOn C f gradF phi gradPhi alphaF)
    (hsmooth : RelativelySmoothOn C f gradF phi gradPhi betaF)
    (hbeta : betaF ≤ 1 / (2 * h))
    (hphi : FirstOrderStrongConvexOn C phi gradPhi alphaPhi)
    (hx : ∀ n, n < N -> x n ∈ C)
    (hxStar : xStar ∈ C)
    (hxPlus : ∀ n, n < N -> ∀ᵐ ω ∂μ, xPlus n ω ∈ C)
    (hFstar : Fstar = compositeObjective f g xStar)
    (hD_current : ∀ n, n < N ->
      D n = bregmanDivergence phi gradPhi xStar (x n))
    (hD_next : ∀ n, n < N ->
      D (n + 1) =
        ∫ ω, bregmanDivergence phi gradPhi xStar (xPlus n ω) ∂μ)
    (hstep : ∀ n, n < N -> ∀ᵐ ω ∂μ,
      IsMirrorProximalGradientStep C f g (fun _ : E => p n ω)
        phi gradPhi alphaG h (x n) (xPlus n ω))
    (hp_int : ∀ n, n < N -> Integrable (p n) μ)
    (hunbiased : ∀ n, n < N ->
      (∫ ω, p n ω ∂μ) = gradF (x n))
    (hFplus : ∀ n, n < N ->
      Integrable (fun ω => compositeObjective f g (xPlus n ω)) μ)
    (hDf : ∀ n, n < N ->
      Integrable (fun ω => bregmanDivergence f gradF (xPlus n ω) (x n)) μ)
    (hDphi : ∀ n, n < N ->
      Integrable
        (fun ω => bregmanDivergence phi gradPhi (xPlus n ω) (x n)) μ)
    (hDnext_int : ∀ n, n < N ->
      Integrable
        (fun ω => bregmanDivergence phi gradPhi xStar (xPlus n ω)) μ)
    (hnoise_int : ∀ n, n < N -> Integrable (noise n) μ)
    (hpsi_int : ∀ n, n < N ->
      Integrable (fun ω =>
        mirrorProximalGradientModel f g (fun _ : E => p n ω)
          phi gradPhi h (x n) (xPlus n ω)) μ)
    (hpsiStar_int : ∀ n, n < N ->
      Integrable (fun ω =>
        mirrorProximalGradientModel f g (fun _ : E => p n ω)
          phi gradPhi h (x n) xStar) μ)
    (hstepSq : ∀ n, n < N ->
      Integrable (fun ω => ‖xPlus n ω - x n‖ ^ (2 : ℕ)) μ)
    (hnoise_raw : ∀ n, n < N -> ∀ᵐ ω ∂μ,
      -inner ℝ (p n ω - gradF (x n)) (xPlus n ω - x n) ≤ noise n ω)
    (hstepRms_sq : ∀ n, n < N ->
      stepRms n ^ (2 : ℕ) ≤ ∫ ω, ‖xPlus n ω - x n‖ ^ (2 : ℕ) ∂μ)
    (hvariance_nonneg : ∀ n, n < N -> 0 ≤ᵐ[μ] varianceNorm n)
    (hstep_nonneg : ∀ n, n < N -> 0 ≤ᵐ[μ] stepNorm n)
    (hvariance_mem : ∀ n, n < N ->
      MemLp (varianceNorm n) (ENNReal.ofReal (2 : ℝ)) μ)
    (hstep_mem : ∀ n, n < N ->
      MemLp (stepNorm n) (ENNReal.ofReal (2 : ℝ)) μ)
    (hnoise_point : ∀ n, n < N ->
      noise n ≤ᵐ[μ] fun ω => varianceNorm n ω * stepNorm n ω)
    (hvariance_root : ∀ n, n < N ->
      (∫ ω, varianceNorm n ω ^ (2 : ℝ) ∂μ) ^ (1 / (2 : ℝ)) ≤
        Real.sqrt (sigma ^ (2 : ℕ) * dim))
    (hstep_root : ∀ n, n < N ->
      (∫ ω, stepNorm n ω ^ (2 : ℝ) ∂μ) ^ (1 / (2 : ℝ)) ≤ stepRms n)
    (hgap_sum : ∀ n, n < N ->
      Fstar + gap (n + 1) =
        ∫ ω, compositeObjective f g (xPlus n ω) ∂μ) :
    (1 / (∑ n ∈ Finset.range N,
          (chewi109Lambda alphaF alphaG h) ^ (N - 1 - n))) *
        (∑ n ∈ Finset.range N,
          (chewi109Lambda alphaF alphaG h) ^ (N - 1 - n) * gap (n + 1)) ≤
      (alphaF + alphaG) /
          (((chewi109Lambda alphaF alphaG h) ^ N)⁻¹ - 1) * D 0 +
        sigma ^ (2 : ℕ) * dim * h / alphaPhi := by
  refine
    chewi121_smooth_weightedAverageGap_le_geometric_of_integral_l2_sampled_models_unbiased
      (μ := μ) (C := C) (f := f) (g := g) (gradF := gradF)
      (phi := phi) (gradPhi := gradPhi)
      (alphaF := alphaF) (alphaG := alphaG) (alphaPhi := alphaPhi)
      (betaF := betaF) (sigma := sigma) (dim := dim) (h := h)
      (Fstar := Fstar) htotal_pos hh halphaPhi hden_pos hlambda_pos
      D gap (fun _ => Real.sqrt (sigma ^ (2 : ℕ) * dim)) stepRms
      x xStar p xPlus noise varianceNorm stepNorm hN hD_N_nonneg
      hconvF hsmooth hbeta hphi hx hxStar hxPlus hFstar hD_current
      hD_next hstep hp_int hunbiased hFplus hDf hDphi hDnext_int
      hnoise_int hpsi_int hpsiStar_int hstepSq hnoise_raw hstepRms_sq
      hvariance_nonneg hstep_nonneg hvariance_mem hstep_mem hnoise_point
      hvariance_root hstep_root ?_ hgap_sum
  intro n hn
  have hnonneg : 0 ≤ sigma ^ (2 : ℕ) * dim :=
    mul_nonneg (sq_nonneg sigma) hdim_nonneg
  have hsqrt :
      (Real.sqrt (sigma ^ (2 : ℕ) * dim)) ^ (2 : ℕ) =
        sigma ^ (2 : ℕ) * dim := by
    simpa [pow_two] using Real.sq_sqrt hnonneg
  rw [hsqrt]

/--
Smooth Chewi Theorem 12.1 source-shaped stochastic averaged-iterate rate.
This combines the smooth sampled-model variance-bound endpoint with Jensen's
inequality at the weighted stochastic averaged iterate.
-/
theorem chewi121_smooth_weightedSampleAverage_gap_le_geometric_of_integral_l2_sampled_models_unbiased_of_variance_bound
    {Ω : Type*} [MeasurableSpace Ω] {μ : Measure Ω} [IsProbabilityMeasure μ]
    {E : Type*} [NormedAddCommGroup E] [InnerProductSpace ℝ E] [CompleteSpace E]
    {C : Set E} {f g : E -> ℝ} {gradF : E -> E}
    {phi : E -> ℝ} {gradPhi : E -> E}
    {alphaF alphaG alphaPhi betaF sigma dim h Fstar : ℝ}
    (htotal_pos : 0 < alphaF + alphaG)
    (hh : 0 < h) (halphaPhi : 0 < alphaPhi) (hdim_nonneg : 0 ≤ dim)
    (hden_pos : 0 < 1 + alphaG * h)
    (hlambda_pos : 0 < chewi109Lambda alphaF alphaG h)
    (D gap stepRms : ℕ -> ℝ)
    (x : ℕ -> E) (xStar : E)
    (p xPlus : ℕ -> Ω -> E)
    (noise varianceNorm stepNorm : ℕ -> Ω -> ℝ)
    {N : ℕ} (hN : N ≠ 0)
    (hD_N_nonneg : 0 ≤ D N)
    (hconvComposite : ConvexOn ℝ C (compositeObjective f g))
    (hconvF : RelativelyStrongConvexOn C f gradF phi gradPhi alphaF)
    (hsmooth : RelativelySmoothOn C f gradF phi gradPhi betaF)
    (hbeta : betaF ≤ 1 / (2 * h))
    (hphi : FirstOrderStrongConvexOn C phi gradPhi alphaPhi)
    (hx : ∀ n, n < N -> x n ∈ C)
    (hxStar : xStar ∈ C)
    (hxPlus : ∀ n, n < N -> ∀ᵐ ω ∂μ, xPlus n ω ∈ C)
    (havg_int : Integrable
      (fun ω =>
        compositeObjective f g
          (weightedSampleAverage
            (fun n => (chewi109Lambda alphaF alphaG h) ^ (N - 1 - n))
            xPlus N ω)) μ)
    (hFstar : Fstar = compositeObjective f g xStar)
    (hD_current : ∀ n, n < N ->
      D n = bregmanDivergence phi gradPhi xStar (x n))
    (hD_next : ∀ n, n < N ->
      D (n + 1) =
        ∫ ω, bregmanDivergence phi gradPhi xStar (xPlus n ω) ∂μ)
    (hstep : ∀ n, n < N -> ∀ᵐ ω ∂μ,
      IsMirrorProximalGradientStep C f g (fun _ : E => p n ω)
        phi gradPhi alphaG h (x n) (xPlus n ω))
    (hp_int : ∀ n, n < N -> Integrable (p n) μ)
    (hunbiased : ∀ n, n < N ->
      (∫ ω, p n ω ∂μ) = gradF (x n))
    (hFplus : ∀ n, n < N ->
      Integrable (fun ω => compositeObjective f g (xPlus n ω)) μ)
    (hDf : ∀ n, n < N ->
      Integrable (fun ω => bregmanDivergence f gradF (xPlus n ω) (x n)) μ)
    (hDphi : ∀ n, n < N ->
      Integrable
        (fun ω => bregmanDivergence phi gradPhi (xPlus n ω) (x n)) μ)
    (hDnext_int : ∀ n, n < N ->
      Integrable
        (fun ω => bregmanDivergence phi gradPhi xStar (xPlus n ω)) μ)
    (hnoise_int : ∀ n, n < N -> Integrable (noise n) μ)
    (hpsi_int : ∀ n, n < N ->
      Integrable (fun ω =>
        mirrorProximalGradientModel f g (fun _ : E => p n ω)
          phi gradPhi h (x n) (xPlus n ω)) μ)
    (hpsiStar_int : ∀ n, n < N ->
      Integrable (fun ω =>
        mirrorProximalGradientModel f g (fun _ : E => p n ω)
          phi gradPhi h (x n) xStar) μ)
    (hstepSq : ∀ n, n < N ->
      Integrable (fun ω => ‖xPlus n ω - x n‖ ^ (2 : ℕ)) μ)
    (hnoise_raw : ∀ n, n < N -> ∀ᵐ ω ∂μ,
      -inner ℝ (p n ω - gradF (x n)) (xPlus n ω - x n) ≤ noise n ω)
    (hstepRms_sq : ∀ n, n < N ->
      stepRms n ^ (2 : ℕ) ≤ ∫ ω, ‖xPlus n ω - x n‖ ^ (2 : ℕ) ∂μ)
    (hvariance_nonneg : ∀ n, n < N -> 0 ≤ᵐ[μ] varianceNorm n)
    (hstep_nonneg : ∀ n, n < N -> 0 ≤ᵐ[μ] stepNorm n)
    (hvariance_mem : ∀ n, n < N ->
      MemLp (varianceNorm n) (ENNReal.ofReal (2 : ℝ)) μ)
    (hstep_mem : ∀ n, n < N ->
      MemLp (stepNorm n) (ENNReal.ofReal (2 : ℝ)) μ)
    (hnoise_point : ∀ n, n < N ->
      noise n ≤ᵐ[μ] fun ω => varianceNorm n ω * stepNorm n ω)
    (hvariance_root : ∀ n, n < N ->
      (∫ ω, varianceNorm n ω ^ (2 : ℝ) ∂μ) ^ (1 / (2 : ℝ)) ≤
        Real.sqrt (sigma ^ (2 : ℕ) * dim))
    (hstep_root : ∀ n, n < N ->
      (∫ ω, stepNorm n ω ^ (2 : ℝ) ∂μ) ^ (1 / (2 : ℝ)) ≤ stepRms n)
    (hgap_sum : ∀ n, n < N ->
      Fstar + gap (n + 1) =
        ∫ ω, compositeObjective f g (xPlus n ω) ∂μ) :
    (∫ ω,
        compositeObjective f g
          (weightedSampleAverage
            (fun n => (chewi109Lambda alphaF alphaG h) ^ (N - 1 - n))
            xPlus N ω) ∂μ) - Fstar ≤
      (alphaF + alphaG) /
          (((chewi109Lambda alphaF alphaG h) ^ N)⁻¹ - 1) * D 0 +
        sigma ^ (2 : ℕ) * dim * h / alphaPhi := by
  refine
    chewi121_weightedSampleAverage_gap_le_geometric_of_weightedAverageGap
      (μ := μ) (C := C) (F := compositeObjective f g)
      (alphaF := alphaF) (alphaG := alphaG) (h := h) (Fstar := Fstar)
      (gap := gap) (x := xPlus)
      hconvComposite hN hlambda_pos hxPlus havg_int hFplus hgap_sum ?_
  exact
    chewi121_smooth_weightedAverageGap_le_geometric_of_integral_l2_sampled_models_unbiased_of_variance_bound
      (μ := μ) (C := C) (f := f) (g := g) (gradF := gradF)
      (phi := phi) (gradPhi := gradPhi)
      (alphaF := alphaF) (alphaG := alphaG) (alphaPhi := alphaPhi)
      (betaF := betaF) (sigma := sigma) (dim := dim) (h := h)
      (Fstar := Fstar) htotal_pos hh halphaPhi hdim_nonneg hden_pos
      hlambda_pos D gap stepRms x xStar p xPlus noise varianceNorm
      stepNorm hN hD_N_nonneg hconvF hsmooth hbeta hphi hx hxStar
      hxPlus hFstar hD_current hD_next hstep hp_int hunbiased hFplus
      hDf hDphi hDnext_int hnoise_int hpsi_int hpsiStar_int hstepSq
      hnoise_raw hstepRms_sq hvariance_nonneg hstep_nonneg
      hvariance_mem hstep_mem hnoise_point hvariance_root hstep_root
      hgap_sum

/--
Smooth Chewi Theorem 12.1 source-shaped averaged-iterate rate with the exact
stochastic-error factor displayed in the theorem statement.
-/
theorem chewi121_smooth_weightedSampleAverage_gap_le_displayed_of_integral_l2_sampled_models_unbiased_of_variance_bound
    {Ω : Type*} [MeasurableSpace Ω] {μ : Measure Ω} [IsProbabilityMeasure μ]
    {E : Type*} [NormedAddCommGroup E] [InnerProductSpace ℝ E] [CompleteSpace E]
    {C : Set E} {f g : E -> ℝ} {gradF : E -> E}
    {phi : E -> ℝ} {gradPhi : E -> E}
    {alphaF alphaG alphaPhi betaF sigma dim h Fstar : ℝ}
    (htotal_pos : 0 < alphaF + alphaG)
    (halphaG_nonneg : 0 ≤ alphaG)
    (hh : 0 < h) (halphaPhi : 0 < alphaPhi) (hdim_nonneg : 0 ≤ dim)
    (hden_pos : 0 < 1 + alphaG * h)
    (hlambda_pos : 0 < chewi109Lambda alphaF alphaG h)
    (D gap stepRms : ℕ -> ℝ)
    (x : ℕ -> E) (xStar : E)
    (p xPlus : ℕ -> Ω -> E)
    (noise varianceNorm stepNorm : ℕ -> Ω -> ℝ)
    {N : ℕ} (hN : N ≠ 0)
    (hD_N_nonneg : 0 ≤ D N)
    (hconvComposite : ConvexOn ℝ C (compositeObjective f g))
    (hconvF : RelativelyStrongConvexOn C f gradF phi gradPhi alphaF)
    (hsmooth : RelativelySmoothOn C f gradF phi gradPhi betaF)
    (hbeta : betaF ≤ 1 / (2 * h))
    (hphi : FirstOrderStrongConvexOn C phi gradPhi alphaPhi)
    (hx : ∀ n, n < N -> x n ∈ C)
    (hxStar : xStar ∈ C)
    (hxPlus : ∀ n, n < N -> ∀ᵐ ω ∂μ, xPlus n ω ∈ C)
    (havg_int : Integrable
      (fun ω =>
        compositeObjective f g
          (weightedSampleAverage
            (fun n => (chewi109Lambda alphaF alphaG h) ^ (N - 1 - n))
            xPlus N ω)) μ)
    (hFstar : Fstar = compositeObjective f g xStar)
    (hD_current : ∀ n, n < N ->
      D n = bregmanDivergence phi gradPhi xStar (x n))
    (hD_next : ∀ n, n < N ->
      D (n + 1) =
        ∫ ω, bregmanDivergence phi gradPhi xStar (xPlus n ω) ∂μ)
    (hstep : ∀ n, n < N -> ∀ᵐ ω ∂μ,
      IsMirrorProximalGradientStep C f g (fun _ : E => p n ω)
        phi gradPhi alphaG h (x n) (xPlus n ω))
    (hp_int : ∀ n, n < N -> Integrable (p n) μ)
    (hunbiased : ∀ n, n < N ->
      (∫ ω, p n ω ∂μ) = gradF (x n))
    (hFplus : ∀ n, n < N ->
      Integrable (fun ω => compositeObjective f g (xPlus n ω)) μ)
    (hDf : ∀ n, n < N ->
      Integrable (fun ω => bregmanDivergence f gradF (xPlus n ω) (x n)) μ)
    (hDphi : ∀ n, n < N ->
      Integrable
        (fun ω => bregmanDivergence phi gradPhi (xPlus n ω) (x n)) μ)
    (hDnext_int : ∀ n, n < N ->
      Integrable
        (fun ω => bregmanDivergence phi gradPhi xStar (xPlus n ω)) μ)
    (hnoise_int : ∀ n, n < N -> Integrable (noise n) μ)
    (hpsi_int : ∀ n, n < N ->
      Integrable (fun ω =>
        mirrorProximalGradientModel f g (fun _ : E => p n ω)
          phi gradPhi h (x n) (xPlus n ω)) μ)
    (hpsiStar_int : ∀ n, n < N ->
      Integrable (fun ω =>
        mirrorProximalGradientModel f g (fun _ : E => p n ω)
          phi gradPhi h (x n) xStar) μ)
    (hstepSq : ∀ n, n < N ->
      Integrable (fun ω => ‖xPlus n ω - x n‖ ^ (2 : ℕ)) μ)
    (hnoise_raw : ∀ n, n < N -> ∀ᵐ ω ∂μ,
      -inner ℝ (p n ω - gradF (x n)) (xPlus n ω - x n) ≤ noise n ω)
    (hstepRms_sq : ∀ n, n < N ->
      stepRms n ^ (2 : ℕ) ≤ ∫ ω, ‖xPlus n ω - x n‖ ^ (2 : ℕ) ∂μ)
    (hvariance_nonneg : ∀ n, n < N -> 0 ≤ᵐ[μ] varianceNorm n)
    (hstep_nonneg : ∀ n, n < N -> 0 ≤ᵐ[μ] stepNorm n)
    (hvariance_mem : ∀ n, n < N ->
      MemLp (varianceNorm n) (ENNReal.ofReal (2 : ℝ)) μ)
    (hstep_mem : ∀ n, n < N ->
      MemLp (stepNorm n) (ENNReal.ofReal (2 : ℝ)) μ)
    (hnoise_point : ∀ n, n < N ->
      noise n ≤ᵐ[μ] fun ω => varianceNorm n ω * stepNorm n ω)
    (hvariance_root : ∀ n, n < N ->
      (∫ ω, varianceNorm n ω ^ (2 : ℝ) ∂μ) ^ (1 / (2 : ℝ)) ≤
        Real.sqrt (sigma ^ (2 : ℕ) * dim))
    (hstep_root : ∀ n, n < N ->
      (∫ ω, stepNorm n ω ^ (2 : ℝ) ∂μ) ^ (1 / (2 : ℝ)) ≤ stepRms n)
    (hgap_sum : ∀ n, n < N ->
      Fstar + gap (n + 1) =
        ∫ ω, compositeObjective f g (xPlus n ω) ∂μ) :
    (∫ ω,
        compositeObjective f g
          (weightedSampleAverage
            (fun n => (chewi109Lambda alphaF alphaG h) ^ (N - 1 - n))
            xPlus N ω) ∂μ) - Fstar ≤
      (alphaF + alphaG) /
          (((chewi109Lambda alphaF alphaG h) ^ N)⁻¹ - 1) * D 0 +
        (1 + alphaG * h) *
          (sigma ^ (2 : ℕ) * dim * h / alphaPhi) := by
  apply
    chewi121_smooth_weightedSampleAverage_gap_le_displayed_of_stronger
      (alphaF := alphaF) (alphaG := alphaG) (alphaPhi := alphaPhi)
      (sigma := sigma) (dim := dim) (h := h) (Fstar := Fstar)
      (D := D) (xPlus := xPlus)
      halphaG_nonneg hh halphaPhi hdim_nonneg
  exact
    chewi121_smooth_weightedSampleAverage_gap_le_geometric_of_integral_l2_sampled_models_unbiased_of_variance_bound
      (μ := μ) (C := C) (f := f) (g := g) (gradF := gradF)
      (phi := phi) (gradPhi := gradPhi)
      (alphaF := alphaF) (alphaG := alphaG) (alphaPhi := alphaPhi)
      (betaF := betaF) (sigma := sigma) (dim := dim) (h := h)
      (Fstar := Fstar) htotal_pos hh halphaPhi hdim_nonneg hden_pos
      hlambda_pos D gap stepRms x xStar p xPlus noise varianceNorm
      stepNorm hN hD_N_nonneg hconvComposite hconvF hsmooth hbeta hphi
      hx hxStar hxPlus havg_int hFstar hD_current hD_next hstep hp_int
      hunbiased hFplus hDf hDphi hDnext_int hnoise_int hpsi_int
      hpsiStar_int hstepSq hnoise_raw hstepRms_sq hvariance_nonneg
      hstep_nonneg hvariance_mem hstep_mem hnoise_point hvariance_root
      hstep_root hgap_sum

/--
Smooth Chewi Theorem 12.1 source-shaped averaged-iterate rate from a
filtration-level conditional unbiasedness assumption.
-/
theorem chewi121_smooth_weightedSampleAverage_gap_le_displayed_of_filtration_condExp_unbiased_of_variance_bound
    {Ω : Type*} [mΩ : MeasurableSpace Ω] {μ : Measure Ω} [IsProbabilityMeasure μ]
    {E : Type*} [NormedAddCommGroup E] [InnerProductSpace ℝ E] [CompleteSpace E]
    {C : Set E} {f g : E -> ℝ} {gradF : E -> E}
    {phi : E -> ℝ} {gradPhi : E -> E}
    {alphaF alphaG alphaPhi betaF sigma dim h Fstar : ℝ}
    (Ffiltration : Filtration ℕ mΩ)
    (htotal_pos : 0 < alphaF + alphaG)
    (halphaG_nonneg : 0 ≤ alphaG)
    (hh : 0 < h) (halphaPhi : 0 < alphaPhi) (hdim_nonneg : 0 ≤ dim)
    (hden_pos : 0 < 1 + alphaG * h)
    (hlambda_pos : 0 < chewi109Lambda alphaF alphaG h)
    (D gap stepRms : ℕ -> ℝ)
    (x : ℕ -> E) (xStar : E)
    (p xPlus : ℕ -> Ω -> E)
    (noise varianceNorm stepNorm : ℕ -> Ω -> ℝ)
    {N : ℕ} (hN : N ≠ 0)
    (hD_N_nonneg : 0 ≤ D N)
    (hconvComposite : ConvexOn ℝ C (compositeObjective f g))
    (hconvF : RelativelyStrongConvexOn C f gradF phi gradPhi alphaF)
    (hsmooth : RelativelySmoothOn C f gradF phi gradPhi betaF)
    (hbeta : betaF ≤ 1 / (2 * h))
    (hphi : FirstOrderStrongConvexOn C phi gradPhi alphaPhi)
    (hx : ∀ n, n < N -> x n ∈ C)
    (hxStar : xStar ∈ C)
    (hxPlus : ∀ n, n < N -> ∀ᵐ ω ∂μ, xPlus n ω ∈ C)
    (havg_int : Integrable
      (fun ω =>
        compositeObjective f g
          (weightedSampleAverage
            (fun n => (chewi109Lambda alphaF alphaG h) ^ (N - 1 - n))
            xPlus N ω)) μ)
    (hFstar : Fstar = compositeObjective f g xStar)
    (hD_current : ∀ n, n < N ->
      D n = bregmanDivergence phi gradPhi xStar (x n))
    (hD_next : ∀ n, n < N ->
      D (n + 1) =
        ∫ ω, bregmanDivergence phi gradPhi xStar (xPlus n ω) ∂μ)
    (hstep : ∀ n, n < N -> ∀ᵐ ω ∂μ,
      IsMirrorProximalGradientStep C f g (fun _ : E => p n ω)
        phi gradPhi alphaG h (x n) (xPlus n ω))
    (hp_int : ∀ n, n < N -> Integrable (p n) μ)
    (hcond_unbiased : ∀ n, n < N ->
      μ[p n | Ffiltration n] =ᵐ[μ] fun _ => gradF (x n))
    (hFplus : ∀ n, n < N ->
      Integrable (fun ω => compositeObjective f g (xPlus n ω)) μ)
    (hDf : ∀ n, n < N ->
      Integrable (fun ω => bregmanDivergence f gradF (xPlus n ω) (x n)) μ)
    (hDphi : ∀ n, n < N ->
      Integrable
        (fun ω => bregmanDivergence phi gradPhi (xPlus n ω) (x n)) μ)
    (hDnext_int : ∀ n, n < N ->
      Integrable
        (fun ω => bregmanDivergence phi gradPhi xStar (xPlus n ω)) μ)
    (hnoise_int : ∀ n, n < N -> Integrable (noise n) μ)
    (hpsi_int : ∀ n, n < N ->
      Integrable (fun ω =>
        mirrorProximalGradientModel f g (fun _ : E => p n ω)
          phi gradPhi h (x n) (xPlus n ω)) μ)
    (hpsiStar_int : ∀ n, n < N ->
      Integrable (fun ω =>
        mirrorProximalGradientModel f g (fun _ : E => p n ω)
          phi gradPhi h (x n) xStar) μ)
    (hstepSq : ∀ n, n < N ->
      Integrable (fun ω => ‖xPlus n ω - x n‖ ^ (2 : ℕ)) μ)
    (hnoise_raw : ∀ n, n < N -> ∀ᵐ ω ∂μ,
      -inner ℝ (p n ω - gradF (x n)) (xPlus n ω - x n) ≤ noise n ω)
    (hstepRms_sq : ∀ n, n < N ->
      stepRms n ^ (2 : ℕ) ≤ ∫ ω, ‖xPlus n ω - x n‖ ^ (2 : ℕ) ∂μ)
    (hvariance_nonneg : ∀ n, n < N -> 0 ≤ᵐ[μ] varianceNorm n)
    (hstep_nonneg : ∀ n, n < N -> 0 ≤ᵐ[μ] stepNorm n)
    (hvariance_mem : ∀ n, n < N ->
      MemLp (varianceNorm n) (ENNReal.ofReal (2 : ℝ)) μ)
    (hstep_mem : ∀ n, n < N ->
      MemLp (stepNorm n) (ENNReal.ofReal (2 : ℝ)) μ)
    (hnoise_point : ∀ n, n < N ->
      noise n ≤ᵐ[μ] fun ω => varianceNorm n ω * stepNorm n ω)
    (hvariance_root : ∀ n, n < N ->
      (∫ ω, varianceNorm n ω ^ (2 : ℝ) ∂μ) ^ (1 / (2 : ℝ)) ≤
        Real.sqrt (sigma ^ (2 : ℕ) * dim))
    (hstep_root : ∀ n, n < N ->
      (∫ ω, stepNorm n ω ^ (2 : ℝ) ∂μ) ^ (1 / (2 : ℝ)) ≤ stepRms n)
    (hgap_sum : ∀ n, n < N ->
      Fstar + gap (n + 1) =
        ∫ ω, compositeObjective f g (xPlus n ω) ∂μ) :
    (∫ ω,
        compositeObjective f g
          (weightedSampleAverage
            (fun n => (chewi109Lambda alphaF alphaG h) ^ (N - 1 - n))
            xPlus N ω) ∂μ) - Fstar ≤
      (alphaF + alphaG) /
          (((chewi109Lambda alphaF alphaG h) ^ N)⁻¹ - 1) * D 0 +
        (1 + alphaG * h) *
          (sigma ^ (2 : ℕ) * dim * h / alphaPhi) := by
  exact
    chewi121_smooth_weightedSampleAverage_gap_le_displayed_of_integral_l2_sampled_models_unbiased_of_variance_bound
      (μ := μ) (C := C) (f := f) (g := g) (gradF := gradF)
      (phi := phi) (gradPhi := gradPhi)
      (alphaF := alphaF) (alphaG := alphaG) (alphaPhi := alphaPhi)
      (betaF := betaF) (sigma := sigma) (dim := dim) (h := h)
      (Fstar := Fstar) htotal_pos halphaG_nonneg hh halphaPhi
      hdim_nonneg hden_pos hlambda_pos D gap stepRms x xStar p xPlus
      noise varianceNorm stepNorm hN hD_N_nonneg hconvComposite hconvF
      hsmooth hbeta hphi hx hxStar hxPlus havg_int hFstar hD_current
      hD_next hstep hp_int
      (fun n hn =>
        integral_eq_const_of_filtration_condExp_ae_eq_const
          (μ := μ) Ffiltration n (p n) (gradF (x n))
          (hcond_unbiased n hn))
      hFplus hDf hDphi hDnext_int hnoise_int hpsi_int hpsiStar_int
      hstepSq hnoise_raw hstepRms_sq hvariance_nonneg hstep_nonneg
      hvariance_mem hstep_mem hnoise_point hvariance_root hstep_root
      hgap_sum

/-- Bochner-integral non-smooth Chewi Theorem 12.1 rate. -/
theorem chewi121_nonsmooth_weightedAverageGap_le_geometric_of_integral_components
    {Ω : Type*} [MeasurableSpace Ω] {μ : Measure Ω}
    {alphaF alphaG alphaPhi L h Fstar : ℝ}
    (htotal_pos : 0 < alphaF + alphaG)
    (hh : 0 < h) (halphaPhi : 0 < alphaPhi) (hL_nonneg : 0 ≤ L)
    (hden_pos : 0 < 1 + alphaG * h)
    (hlambda_pos : 0 < chewi109Lambda alphaF alphaG h)
    (D gap psiNext psiStar stepRms : ℕ -> ℝ)
    (Fplus lip grad Dphi psi stepSq stepNorm : ℕ -> Ω -> ℝ)
    {N : ℕ} (hN : N ≠ 0)
    (hD_N_nonneg : 0 ≤ D N)
    (hgrowth : ∀ n, n < N ->
      (alphaG + 1 / h) * D (n + 1) + psiNext n ≤ psiStar n)
    (hstar_upper : ∀ n, n < N ->
      psiStar n ≤ Fstar + ((1 - alphaF * h) / h) * D n)
    (hFplus : ∀ n, n < N -> Integrable (Fplus n) μ)
    (hlip_int : ∀ n, n < N -> Integrable (lip n) μ)
    (hgrad_int : ∀ n, n < N -> Integrable (grad n) μ)
    (hDphi_int : ∀ n, n < N -> Integrable (Dphi n) μ)
    (hpsi_int : ∀ n, n < N -> Integrable (psi n) μ)
    (hstepSq_int : ∀ n, n < N -> Integrable (stepSq n) μ)
    (hstepNorm_int : ∀ n, n < N -> Integrable (stepNorm n) μ)
    (hraw_point : ∀ n, n < N ->
      (fun ω => Fplus n ω - lip n ω - grad n ω + (1 / h) * Dphi n ω) ≤ᵐ[μ]
        psi n)
    (hpsi : ∀ n, n < N -> (∫ ω, psi n ω ∂μ) ≤ psiNext n)
    (hstepRms_sq : ∀ n, n < N ->
      stepRms n ^ (2 : ℕ) ≤ ∫ ω, stepSq n ω ∂μ)
    (hphi_point : ∀ n, n < N ->
      (fun ω => (alphaPhi / 2) * stepSq n ω) ≤ᵐ[μ] Dphi n)
    (hstep_avg : ∀ n, n < N -> (∫ ω, stepNorm n ω ∂μ) ≤ stepRms n)
    (hlip_point : ∀ n, n < N ->
      lip n ≤ᵐ[μ] fun ω => L * stepNorm n ω)
    (hgrad_point : ∀ n, n < N ->
      grad n ≤ᵐ[μ] fun ω => L * stepNorm n ω)
    (hgap_sum : ∀ n, n < N ->
      Fstar + gap (n + 1) = ∫ ω, Fplus n ω ∂μ) :
    (1 / (∑ n ∈ Finset.range N,
          (chewi109Lambda alphaF alphaG h) ^ (N - 1 - n))) *
        (∑ n ∈ Finset.range N,
          (chewi109Lambda alphaF alphaG h) ^ (N - 1 - n) * gap (n + 1)) ≤
      (alphaF + alphaG) /
          (((chewi109Lambda alphaF alphaG h) ^ N)⁻¹ - 1) * D 0 +
        2 * L ^ (2 : ℕ) * h / alphaPhi := by
  refine
    chewi121_nonsmooth_weightedAverageGap_le_geometric_of_rms_model_bounds
      (alphaF := alphaF) (alphaG := alphaG) (alphaPhi := alphaPhi)
      (L := L) (h := h) (Fstar := Fstar)
      htotal_pos hh halphaPhi hden_pos hlambda_pos D gap psiNext psiStar
      (fun n => ∫ ω, Fplus n ω ∂μ) stepRms
      hN hD_N_nonneg hgrowth hstar_upper ?_ hgap_sum
  intro n hn
  exact
    chewi121_nonsmooth_hcore_of_integral_components
      (μ := μ) (Fplus := Fplus n) (lip := lip n) (grad := grad n)
      (Dphi := Dphi n) (psi := psi n) (stepSq := stepSq n)
      (stepNorm := stepNorm n) (alphaPhi := alphaPhi) (L := L)
      (h := h) (psiNext := psiNext n) (stepRms := stepRms n)
      hh halphaPhi.le hL_nonneg (hFplus n hn) (hlip_int n hn)
      (hgrad_int n hn) (hDphi_int n hn) (hpsi_int n hn)
      (hstepSq_int n hn) (hstepNorm_int n hn) (hraw_point n hn)
      (hpsi n hn) (hstepRms_sq n hn) (hphi_point n hn)
      (hstep_avg n hn) (hlip_point n hn) (hgrad_point n hn)

/--
Bochner-integral non-smooth sampled-model Chewi Theorem 12.1 rate with the
source `(12.2)` L2 sampled-gradient and step-norm controls.  Growth and
star-upper fields remain supplied here; the theorem discharges the sampled
non-smooth lower-model estimate and plugs it into the existing RMS-to-rate
wrapper.
-/
theorem chewi121_nonsmooth_weightedAverageGap_le_geometric_of_integral_l2_sampled_models
    {Ω : Type*} [MeasurableSpace Ω] {μ : Measure Ω} [IsProbabilityMeasure μ]
    {E : Type*} [NormedAddCommGroup E] [InnerProductSpace ℝ E]
    {C : Set E} {f g : E -> ℝ} {phi : E -> ℝ} {gradPhi : E -> E}
    {alphaF alphaG alphaPhi L h Fstar : ℝ}
    (htotal_pos : 0 < alphaF + alphaG)
    (hh : 0 < h) (halphaPhi : 0 < alphaPhi) (hL_nonneg : 0 ≤ L)
    (hden_pos : 0 < 1 + alphaG * h)
    (hlambda_pos : 0 < chewi109Lambda alphaF alphaG h)
    (D gap psiNext psiStar stepRms : ℕ -> ℝ)
    (x : ℕ -> E) (p xPlus : ℕ -> Ω -> E)
    (pNorm stepNorm : ℕ -> Ω -> ℝ)
    {N : ℕ} (hN : N ≠ 0)
    (hD_N_nonneg : 0 ≤ D N)
    (hLip : LipschitzOnWith (Real.toNNReal L) f C)
    (hphi : FirstOrderStrongConvexOn C phi gradPhi alphaPhi)
    (hx : ∀ n, n < N -> x n ∈ C)
    (hxPlus : ∀ n, n < N -> ∀ᵐ ω ∂μ, xPlus n ω ∈ C)
    (hgrowth : ∀ n, n < N ->
      (alphaG + 1 / h) * D (n + 1) + psiNext n ≤ psiStar n)
    (hstar_upper : ∀ n, n < N ->
      psiStar n ≤ Fstar + ((1 - alphaF * h) / h) * D n)
    (hFplus : ∀ n, n < N ->
      Integrable (fun ω => compositeObjective f g (xPlus n ω)) μ)
    (hDphi : ∀ n, n < N ->
      Integrable
        (fun ω => bregmanDivergence phi gradPhi (xPlus n ω) (x n)) μ)
    (hpsi_int : ∀ n, n < N ->
      Integrable (fun ω =>
        mirrorProximalGradientModel f g (fun _ : E => p n ω)
          phi gradPhi h (x n) (xPlus n ω)) μ)
    (hstepSq : ∀ n, n < N ->
      Integrable (fun ω => ‖xPlus n ω - x n‖ ^ (2 : ℕ)) μ)
    (hpsi : ∀ n, n < N ->
      (∫ ω,
        mirrorProximalGradientModel f g (fun _ : E => p n ω)
          phi gradPhi h (x n) (xPlus n ω) ∂μ) ≤ psiNext n)
    (hstepRms_sq : ∀ n, n < N ->
      stepRms n ^ (2 : ℕ) ≤ ∫ ω, ‖xPlus n ω - x n‖ ^ (2 : ℕ) ∂μ)
    (hstep_point : ∀ n, n < N ->
      (fun ω => ‖xPlus n ω - x n‖) ≤ᵐ[μ] stepNorm n)
    (hpNorm_nonneg : ∀ n, n < N -> 0 ≤ᵐ[μ] pNorm n)
    (hstep_nonneg : ∀ n, n < N -> 0 ≤ᵐ[μ] stepNorm n)
    (hpNorm_mem : ∀ n, n < N ->
      MemLp (pNorm n) (ENNReal.ofReal (2 : ℝ)) μ)
    (hstep_mem : ∀ n, n < N ->
      MemLp (stepNorm n) (ENNReal.ofReal (2 : ℝ)) μ)
    (hpNorm_point : ∀ n, n < N ->
      (fun ω => ‖p n ω‖) ≤ᵐ[μ] pNorm n)
    (hpNorm_root : ∀ n, n < N ->
      (∫ ω, pNorm n ω ^ (2 : ℝ) ∂μ) ^ (1 / (2 : ℝ)) ≤ L)
    (hstep_root : ∀ n, n < N ->
      (∫ ω, stepNorm n ω ^ (2 : ℝ) ∂μ) ^ (1 / (2 : ℝ)) ≤ stepRms n)
    (hgap_sum : ∀ n, n < N ->
      Fstar + gap (n + 1) =
        ∫ ω, compositeObjective f g (xPlus n ω) ∂μ) :
    (1 / (∑ n ∈ Finset.range N,
          (chewi109Lambda alphaF alphaG h) ^ (N - 1 - n))) *
        (∑ n ∈ Finset.range N,
          (chewi109Lambda alphaF alphaG h) ^ (N - 1 - n) * gap (n + 1)) ≤
      (alphaF + alphaG) /
          (((chewi109Lambda alphaF alphaG h) ^ N)⁻¹ - 1) * D 0 +
        2 * L ^ (2 : ℕ) * h / alphaPhi := by
  refine
    chewi121_nonsmooth_weightedAverageGap_le_geometric_of_rms_model_bounds
      (alphaF := alphaF) (alphaG := alphaG) (alphaPhi := alphaPhi)
      (L := L) (h := h) (Fstar := Fstar)
      htotal_pos hh halphaPhi hden_pos hlambda_pos D gap psiNext psiStar
      (fun n => ∫ ω, compositeObjective f g (xPlus n ω) ∂μ) stepRms
      hN hD_N_nonneg hgrowth hstar_upper ?_ hgap_sum
  intro n hn
  exact
    chewi121_nonsmooth_hcore_of_integral_l2_sampled_models
      (μ := μ) (C := C) (f := f) (g := g) (phi := phi)
      (gradPhi := gradPhi) (alphaPhi := alphaPhi) (L := L) (h := h)
      (psiNext := psiNext n) (stepRms := stepRms n)
      (x := x n) (p := p n) (xPlus := xPlus n)
      (pNorm := pNorm n) (stepNorm := stepNorm n)
      hh halphaPhi.le hL_nonneg hLip hphi (hx n hn) (hxPlus n hn)
      (hFplus n hn) (hDphi n hn) (hpsi_int n hn) (hstepSq n hn)
      (hpsi n hn) (hstepRms_sq n hn) (hstep_point n hn)
      (hpNorm_nonneg n hn) (hstep_nonneg n hn) (hpNorm_mem n hn)
      (hstep_mem n hn) (hpNorm_point n hn) (hpNorm_root n hn)
      (hstep_root n hn)

/--
Bochner-integral non-smooth sampled-model Chewi Theorem 12.1 rate with the
growth and star-upper fields discharged from a.e. sampled MPGD steps and a
relative-subgradient condition on the mean sampled oracle.
-/
theorem chewi121_nonsmooth_weightedAverageGap_le_geometric_of_integral_l2_sampled_models_relativeSubgradient
    {Ω : Type*} [MeasurableSpace Ω] {μ : Measure Ω} [IsProbabilityMeasure μ]
    {E : Type*} [NormedAddCommGroup E] [InnerProductSpace ℝ E] [CompleteSpace E]
    {C : Set E} {f g : E -> ℝ} {phi : E -> ℝ} {gradPhi : E -> E}
    {alphaF alphaG alphaPhi L h Fstar : ℝ}
    (htotal_pos : 0 < alphaF + alphaG)
    (hh : 0 < h) (halphaPhi : 0 < alphaPhi) (hL_nonneg : 0 ≤ L)
    (hden_pos : 0 < 1 + alphaG * h)
    (hlambda_pos : 0 < chewi109Lambda alphaF alphaG h)
    (D gap stepRms : ℕ -> ℝ)
    (x : ℕ -> E) (xStar : E)
    (p xPlus : ℕ -> Ω -> E)
    (pNorm stepNorm : ℕ -> Ω -> ℝ)
    {N : ℕ} (hN : N ≠ 0)
    (hD_N_nonneg : 0 ≤ D N)
    (hLip : LipschitzOnWith (Real.toNNReal L) f C)
    (hphi : FirstOrderStrongConvexOn C phi gradPhi alphaPhi)
    (hx : ∀ n, n < N -> x n ∈ C)
    (hxStar : xStar ∈ C)
    (hFstar : Fstar = compositeObjective f g xStar)
    (hD_current : ∀ n, n < N ->
      D n = bregmanDivergence phi gradPhi xStar (x n))
    (hD_next : ∀ n, n < N ->
      D (n + 1) =
        ∫ ω, bregmanDivergence phi gradPhi xStar (xPlus n ω) ∂μ)
    (hstep : ∀ n, n < N -> ∀ᵐ ω ∂μ,
      IsMirrorProximalGradientStep C f g (fun _ : E => p n ω)
        phi gradPhi alphaG h (x n) (xPlus n ω))
    (hp_int : ∀ n, n < N -> Integrable (p n) μ)
    (hmean_sub : ∀ n, n < N ->
      IsRelativeSubgradientAt C f (∫ ω, p n ω ∂μ)
        phi gradPhi alphaF (x n))
    (hxPlus : ∀ n, n < N -> ∀ᵐ ω ∂μ, xPlus n ω ∈ C)
    (hFplus : ∀ n, n < N ->
      Integrable (fun ω => compositeObjective f g (xPlus n ω)) μ)
    (hDphi : ∀ n, n < N ->
      Integrable
        (fun ω => bregmanDivergence phi gradPhi (xPlus n ω) (x n)) μ)
    (hDnext_int : ∀ n, n < N ->
      Integrable
        (fun ω => bregmanDivergence phi gradPhi xStar (xPlus n ω)) μ)
    (hpsi_int : ∀ n, n < N ->
      Integrable (fun ω =>
        mirrorProximalGradientModel f g (fun _ : E => p n ω)
          phi gradPhi h (x n) (xPlus n ω)) μ)
    (hpsiStar_int : ∀ n, n < N ->
      Integrable (fun ω =>
        mirrorProximalGradientModel f g (fun _ : E => p n ω)
          phi gradPhi h (x n) xStar) μ)
    (hstepSq : ∀ n, n < N ->
      Integrable (fun ω => ‖xPlus n ω - x n‖ ^ (2 : ℕ)) μ)
    (hstepRms_sq : ∀ n, n < N ->
      stepRms n ^ (2 : ℕ) ≤ ∫ ω, ‖xPlus n ω - x n‖ ^ (2 : ℕ) ∂μ)
    (hstep_point : ∀ n, n < N ->
      (fun ω => ‖xPlus n ω - x n‖) ≤ᵐ[μ] stepNorm n)
    (hpNorm_nonneg : ∀ n, n < N -> 0 ≤ᵐ[μ] pNorm n)
    (hstep_nonneg : ∀ n, n < N -> 0 ≤ᵐ[μ] stepNorm n)
    (hpNorm_mem : ∀ n, n < N ->
      MemLp (pNorm n) (ENNReal.ofReal (2 : ℝ)) μ)
    (hstep_mem : ∀ n, n < N ->
      MemLp (stepNorm n) (ENNReal.ofReal (2 : ℝ)) μ)
    (hpNorm_point : ∀ n, n < N ->
      (fun ω => ‖p n ω‖) ≤ᵐ[μ] pNorm n)
    (hpNorm_root : ∀ n, n < N ->
      (∫ ω, pNorm n ω ^ (2 : ℝ) ∂μ) ^ (1 / (2 : ℝ)) ≤ L)
    (hstep_root : ∀ n, n < N ->
      (∫ ω, stepNorm n ω ^ (2 : ℝ) ∂μ) ^ (1 / (2 : ℝ)) ≤ stepRms n)
    (hgap_sum : ∀ n, n < N ->
      Fstar + gap (n + 1) =
        ∫ ω, compositeObjective f g (xPlus n ω) ∂μ) :
    (1 / (∑ n ∈ Finset.range N,
          (chewi109Lambda alphaF alphaG h) ^ (N - 1 - n))) *
        (∑ n ∈ Finset.range N,
          (chewi109Lambda alphaF alphaG h) ^ (N - 1 - n) * gap (n + 1)) ≤
      (alphaF + alphaG) /
          (((chewi109Lambda alphaF alphaG h) ^ N)⁻¹ - 1) * D 0 +
        2 * L ^ (2 : ℕ) * h / alphaPhi := by
  refine
    chewi121_nonsmooth_weightedAverageGap_le_geometric_of_integral_l2_sampled_models
      (μ := μ) (C := C) (f := f) (g := g) (phi := phi)
      (gradPhi := gradPhi) (alphaF := alphaF) (alphaG := alphaG)
      (alphaPhi := alphaPhi) (L := L) (h := h) (Fstar := Fstar)
      htotal_pos hh halphaPhi hL_nonneg hden_pos hlambda_pos D gap
      (fun n =>
        ∫ ω,
          mirrorProximalGradientModel f g (fun _ : E => p n ω)
            phi gradPhi h (x n) (xPlus n ω) ∂μ)
      (fun n =>
        ∫ ω,
          mirrorProximalGradientModel f g (fun _ : E => p n ω)
            phi gradPhi h (x n) xStar ∂μ)
      stepRms x p xPlus pNorm stepNorm hN hD_N_nonneg hLip hphi hx hxPlus
      ?_ ?_ hFplus hDphi hpsi_int hstepSq ?_ hstepRms_sq hstep_point
      hpNorm_nonneg hstep_nonneg hpNorm_mem hstep_mem hpNorm_point
      hpNorm_root hstep_root hgap_sum
  · intro n hn
    exact
      chewi121_integral_sampled_growth_of_steps
        (μ := μ) (C := C) (f := f) (g := g) (phi := phi)
        (gradPhi := gradPhi) (alphaG := alphaG) (h := h)
        (x := x n) (y := xStar) (p := p n) (xPlus := xPlus n)
        (hpsiNext_int := hpsi_int n hn) (hDnext_int := hDnext_int n hn)
        (hpsiStar_int := hpsiStar_int n hn)
        (hstep := hstep n hn) hxStar (hD_next n hn) rfl rfl
  · intro n hn
    have hupper :=
      chewi121_integral_sampled_star_upper_of_relativeSubgradient
        (μ := μ) (C := C) (f := f) (g := g)
        (phi := phi) (gradPhi := gradPhi) (alphaF := alphaF)
        (h := h) (x := x n) (y := xStar) (p := p n)
        hh (hp_int n hn) (hmean_sub n hn) hxStar
    simpa [hFstar, hD_current n hn] using hupper
  · intro n hn
    exact le_rfl

/--
Non-smooth Chewi Theorem 12.1 source-shaped stochastic averaged-iterate rate.
This combines the relative-subgradient sampled-model endpoint with Jensen's
inequality at the weighted stochastic averaged iterate.
-/
theorem chewi121_nonsmooth_weightedSampleAverage_gap_le_geometric_of_integral_l2_sampled_models_relativeSubgradient
    {Ω : Type*} [MeasurableSpace Ω] {μ : Measure Ω} [IsProbabilityMeasure μ]
    {E : Type*} [NormedAddCommGroup E] [InnerProductSpace ℝ E] [CompleteSpace E]
    {C : Set E} {f g : E -> ℝ} {phi : E -> ℝ} {gradPhi : E -> E}
    {alphaF alphaG alphaPhi L h Fstar : ℝ}
    (htotal_pos : 0 < alphaF + alphaG)
    (hh : 0 < h) (halphaPhi : 0 < alphaPhi) (hL_nonneg : 0 ≤ L)
    (hden_pos : 0 < 1 + alphaG * h)
    (hlambda_pos : 0 < chewi109Lambda alphaF alphaG h)
    (D gap stepRms : ℕ -> ℝ)
    (x : ℕ -> E) (xStar : E)
    (p xPlus : ℕ -> Ω -> E)
    (pNorm stepNorm : ℕ -> Ω -> ℝ)
    {N : ℕ} (hN : N ≠ 0)
    (hD_N_nonneg : 0 ≤ D N)
    (hconvComposite : ConvexOn ℝ C (compositeObjective f g))
    (hLip : LipschitzOnWith (Real.toNNReal L) f C)
    (hphi : FirstOrderStrongConvexOn C phi gradPhi alphaPhi)
    (hx : ∀ n, n < N -> x n ∈ C)
    (hxStar : xStar ∈ C)
    (hFstar : Fstar = compositeObjective f g xStar)
    (hD_current : ∀ n, n < N ->
      D n = bregmanDivergence phi gradPhi xStar (x n))
    (hD_next : ∀ n, n < N ->
      D (n + 1) =
        ∫ ω, bregmanDivergence phi gradPhi xStar (xPlus n ω) ∂μ)
    (hstep : ∀ n, n < N -> ∀ᵐ ω ∂μ,
      IsMirrorProximalGradientStep C f g (fun _ : E => p n ω)
        phi gradPhi alphaG h (x n) (xPlus n ω))
    (hp_int : ∀ n, n < N -> Integrable (p n) μ)
    (hmean_sub : ∀ n, n < N ->
      IsRelativeSubgradientAt C f (∫ ω, p n ω ∂μ)
        phi gradPhi alphaF (x n))
    (hxPlus : ∀ n, n < N -> ∀ᵐ ω ∂μ, xPlus n ω ∈ C)
    (havg_int : Integrable
      (fun ω =>
        compositeObjective f g
          (weightedSampleAverage
            (fun n => (chewi109Lambda alphaF alphaG h) ^ (N - 1 - n))
            xPlus N ω)) μ)
    (hFplus : ∀ n, n < N ->
      Integrable (fun ω => compositeObjective f g (xPlus n ω)) μ)
    (hDphi : ∀ n, n < N ->
      Integrable
        (fun ω => bregmanDivergence phi gradPhi (xPlus n ω) (x n)) μ)
    (hDnext_int : ∀ n, n < N ->
      Integrable
        (fun ω => bregmanDivergence phi gradPhi xStar (xPlus n ω)) μ)
    (hpsi_int : ∀ n, n < N ->
      Integrable (fun ω =>
        mirrorProximalGradientModel f g (fun _ : E => p n ω)
          phi gradPhi h (x n) (xPlus n ω)) μ)
    (hpsiStar_int : ∀ n, n < N ->
      Integrable (fun ω =>
        mirrorProximalGradientModel f g (fun _ : E => p n ω)
          phi gradPhi h (x n) xStar) μ)
    (hstepSq : ∀ n, n < N ->
      Integrable (fun ω => ‖xPlus n ω - x n‖ ^ (2 : ℕ)) μ)
    (hstepRms_sq : ∀ n, n < N ->
      stepRms n ^ (2 : ℕ) ≤ ∫ ω, ‖xPlus n ω - x n‖ ^ (2 : ℕ) ∂μ)
    (hstep_point : ∀ n, n < N ->
      (fun ω => ‖xPlus n ω - x n‖) ≤ᵐ[μ] stepNorm n)
    (hpNorm_nonneg : ∀ n, n < N -> 0 ≤ᵐ[μ] pNorm n)
    (hstep_nonneg : ∀ n, n < N -> 0 ≤ᵐ[μ] stepNorm n)
    (hpNorm_mem : ∀ n, n < N ->
      MemLp (pNorm n) (ENNReal.ofReal (2 : ℝ)) μ)
    (hstep_mem : ∀ n, n < N ->
      MemLp (stepNorm n) (ENNReal.ofReal (2 : ℝ)) μ)
    (hpNorm_point : ∀ n, n < N ->
      (fun ω => ‖p n ω‖) ≤ᵐ[μ] pNorm n)
    (hpNorm_root : ∀ n, n < N ->
      (∫ ω, pNorm n ω ^ (2 : ℝ) ∂μ) ^ (1 / (2 : ℝ)) ≤ L)
    (hstep_root : ∀ n, n < N ->
      (∫ ω, stepNorm n ω ^ (2 : ℝ) ∂μ) ^ (1 / (2 : ℝ)) ≤ stepRms n)
    (hgap_sum : ∀ n, n < N ->
      Fstar + gap (n + 1) =
        ∫ ω, compositeObjective f g (xPlus n ω) ∂μ) :
    (∫ ω,
        compositeObjective f g
          (weightedSampleAverage
            (fun n => (chewi109Lambda alphaF alphaG h) ^ (N - 1 - n))
            xPlus N ω) ∂μ) - Fstar ≤
      (alphaF + alphaG) /
          (((chewi109Lambda alphaF alphaG h) ^ N)⁻¹ - 1) * D 0 +
        2 * L ^ (2 : ℕ) * h / alphaPhi := by
  refine
    chewi121_weightedSampleAverage_gap_le_geometric_of_weightedAverageGap
      (μ := μ) (C := C) (F := compositeObjective f g)
      (alphaF := alphaF) (alphaG := alphaG) (h := h) (Fstar := Fstar)
      (gap := gap) (x := xPlus)
      hconvComposite hN hlambda_pos hxPlus havg_int hFplus hgap_sum ?_
  exact
    chewi121_nonsmooth_weightedAverageGap_le_geometric_of_integral_l2_sampled_models_relativeSubgradient
      (μ := μ) (C := C) (f := f) (g := g) (phi := phi)
      (gradPhi := gradPhi) (alphaF := alphaF) (alphaG := alphaG)
      (alphaPhi := alphaPhi) (L := L) (h := h) (Fstar := Fstar)
      htotal_pos hh halphaPhi hL_nonneg hden_pos hlambda_pos D gap
      stepRms x xStar p xPlus pNorm stepNorm hN hD_N_nonneg hLip hphi
      hx hxStar hFstar hD_current hD_next hstep hp_int hmean_sub hxPlus
      hFplus hDphi hDnext_int hpsi_int hpsiStar_int hstepSq
      hstepRms_sq hstep_point hpNorm_nonneg hstep_nonneg hpNorm_mem
      hstep_mem hpNorm_point hpNorm_root hstep_root hgap_sum

/--
Non-smooth Chewi Theorem 12.1 source-shaped averaged-iterate rate with the
exact stochastic-error factor displayed in the theorem statement.
-/
theorem chewi121_nonsmooth_weightedSampleAverage_gap_le_displayed_of_integral_l2_sampled_models_relativeSubgradient
    {Ω : Type*} [MeasurableSpace Ω] {μ : Measure Ω} [IsProbabilityMeasure μ]
    {E : Type*} [NormedAddCommGroup E] [InnerProductSpace ℝ E] [CompleteSpace E]
    {C : Set E} {f g : E -> ℝ} {phi : E -> ℝ} {gradPhi : E -> E}
    {alphaF alphaG alphaPhi L h Fstar : ℝ}
    (htotal_pos : 0 < alphaF + alphaG)
    (halphaG_nonneg : 0 ≤ alphaG)
    (hh : 0 < h) (halphaPhi : 0 < alphaPhi) (hL_nonneg : 0 ≤ L)
    (hden_pos : 0 < 1 + alphaG * h)
    (hlambda_pos : 0 < chewi109Lambda alphaF alphaG h)
    (D gap stepRms : ℕ -> ℝ)
    (x : ℕ -> E) (xStar : E)
    (p xPlus : ℕ -> Ω -> E)
    (pNorm stepNorm : ℕ -> Ω -> ℝ)
    {N : ℕ} (hN : N ≠ 0)
    (hD_N_nonneg : 0 ≤ D N)
    (hconvComposite : ConvexOn ℝ C (compositeObjective f g))
    (hLip : LipschitzOnWith (Real.toNNReal L) f C)
    (hphi : FirstOrderStrongConvexOn C phi gradPhi alphaPhi)
    (hx : ∀ n, n < N -> x n ∈ C)
    (hxStar : xStar ∈ C)
    (hFstar : Fstar = compositeObjective f g xStar)
    (hD_current : ∀ n, n < N ->
      D n = bregmanDivergence phi gradPhi xStar (x n))
    (hD_next : ∀ n, n < N ->
      D (n + 1) =
        ∫ ω, bregmanDivergence phi gradPhi xStar (xPlus n ω) ∂μ)
    (hstep : ∀ n, n < N -> ∀ᵐ ω ∂μ,
      IsMirrorProximalGradientStep C f g (fun _ : E => p n ω)
        phi gradPhi alphaG h (x n) (xPlus n ω))
    (hp_int : ∀ n, n < N -> Integrable (p n) μ)
    (hmean_sub : ∀ n, n < N ->
      IsRelativeSubgradientAt C f (∫ ω, p n ω ∂μ)
        phi gradPhi alphaF (x n))
    (hxPlus : ∀ n, n < N -> ∀ᵐ ω ∂μ, xPlus n ω ∈ C)
    (havg_int : Integrable
      (fun ω =>
        compositeObjective f g
          (weightedSampleAverage
            (fun n => (chewi109Lambda alphaF alphaG h) ^ (N - 1 - n))
            xPlus N ω)) μ)
    (hFplus : ∀ n, n < N ->
      Integrable (fun ω => compositeObjective f g (xPlus n ω)) μ)
    (hDphi : ∀ n, n < N ->
      Integrable
        (fun ω => bregmanDivergence phi gradPhi (xPlus n ω) (x n)) μ)
    (hDnext_int : ∀ n, n < N ->
      Integrable
        (fun ω => bregmanDivergence phi gradPhi xStar (xPlus n ω)) μ)
    (hpsi_int : ∀ n, n < N ->
      Integrable (fun ω =>
        mirrorProximalGradientModel f g (fun _ : E => p n ω)
          phi gradPhi h (x n) (xPlus n ω)) μ)
    (hpsiStar_int : ∀ n, n < N ->
      Integrable (fun ω =>
        mirrorProximalGradientModel f g (fun _ : E => p n ω)
          phi gradPhi h (x n) xStar) μ)
    (hstepSq : ∀ n, n < N ->
      Integrable (fun ω => ‖xPlus n ω - x n‖ ^ (2 : ℕ)) μ)
    (hstepRms_sq : ∀ n, n < N ->
      stepRms n ^ (2 : ℕ) ≤ ∫ ω, ‖xPlus n ω - x n‖ ^ (2 : ℕ) ∂μ)
    (hstep_point : ∀ n, n < N ->
      (fun ω => ‖xPlus n ω - x n‖) ≤ᵐ[μ] stepNorm n)
    (hpNorm_nonneg : ∀ n, n < N -> 0 ≤ᵐ[μ] pNorm n)
    (hstep_nonneg : ∀ n, n < N -> 0 ≤ᵐ[μ] stepNorm n)
    (hpNorm_mem : ∀ n, n < N ->
      MemLp (pNorm n) (ENNReal.ofReal (2 : ℝ)) μ)
    (hstep_mem : ∀ n, n < N ->
      MemLp (stepNorm n) (ENNReal.ofReal (2 : ℝ)) μ)
    (hpNorm_point : ∀ n, n < N ->
      (fun ω => ‖p n ω‖) ≤ᵐ[μ] pNorm n)
    (hpNorm_root : ∀ n, n < N ->
      (∫ ω, pNorm n ω ^ (2 : ℝ) ∂μ) ^ (1 / (2 : ℝ)) ≤ L)
    (hstep_root : ∀ n, n < N ->
      (∫ ω, stepNorm n ω ^ (2 : ℝ) ∂μ) ^ (1 / (2 : ℝ)) ≤ stepRms n)
    (hgap_sum : ∀ n, n < N ->
      Fstar + gap (n + 1) =
        ∫ ω, compositeObjective f g (xPlus n ω) ∂μ) :
    (∫ ω,
        compositeObjective f g
          (weightedSampleAverage
            (fun n => (chewi109Lambda alphaF alphaG h) ^ (N - 1 - n))
            xPlus N ω) ∂μ) - Fstar ≤
      (alphaF + alphaG) /
          (((chewi109Lambda alphaF alphaG h) ^ N)⁻¹ - 1) * D 0 +
        (1 + alphaG * h) *
          (2 * L ^ (2 : ℕ) * h / alphaPhi) := by
  apply
    chewi121_nonsmooth_weightedSampleAverage_gap_le_displayed_of_stronger
      (alphaF := alphaF) (alphaG := alphaG) (alphaPhi := alphaPhi)
      (L := L) (h := h) (Fstar := Fstar) (D := D) (xPlus := xPlus)
      halphaG_nonneg hh halphaPhi
  exact
    chewi121_nonsmooth_weightedSampleAverage_gap_le_geometric_of_integral_l2_sampled_models_relativeSubgradient
      (μ := μ) (C := C) (f := f) (g := g) (phi := phi)
      (gradPhi := gradPhi) (alphaF := alphaF) (alphaG := alphaG)
      (alphaPhi := alphaPhi) (L := L) (h := h) (Fstar := Fstar)
      htotal_pos hh halphaPhi hL_nonneg hden_pos hlambda_pos D gap
      stepRms x xStar p xPlus pNorm stepNorm hN hD_N_nonneg
      hconvComposite hLip hphi hx hxStar hFstar hD_current hD_next
      hstep hp_int hmean_sub hxPlus havg_int hFplus hDphi hDnext_int
      hpsi_int hpsiStar_int hstepSq hstepRms_sq hstep_point
      hpNorm_nonneg hstep_nonneg hpNorm_mem hstep_mem hpNorm_point
      hpNorm_root hstep_root hgap_sum

/--
Non-smooth Chewi Theorem 12.1 source-shaped averaged-iterate rate from a
filtration-level conditional mean oracle and a relative-subgradient version of
that conditional mean.
-/
theorem chewi121_nonsmooth_weightedSampleAverage_gap_le_displayed_of_filtration_condExp_relativeSubgradient
    {Ω : Type*} [mΩ : MeasurableSpace Ω] {μ : Measure Ω} [IsProbabilityMeasure μ]
    {E : Type*} [NormedAddCommGroup E] [InnerProductSpace ℝ E] [CompleteSpace E]
    {C : Set E} {f g : E -> ℝ} {phi : E -> ℝ} {gradPhi : E -> E}
    {alphaF alphaG alphaPhi L h Fstar : ℝ}
    (Ffiltration : Filtration ℕ mΩ)
    (htotal_pos : 0 < alphaF + alphaG)
    (halphaG_nonneg : 0 ≤ alphaG)
    (hh : 0 < h) (halphaPhi : 0 < alphaPhi) (hL_nonneg : 0 ≤ L)
    (hden_pos : 0 < 1 + alphaG * h)
    (hlambda_pos : 0 < chewi109Lambda alphaF alphaG h)
    (D gap stepRms : ℕ -> ℝ)
    (x : ℕ -> E) (xStar : E)
    (p xPlus : ℕ -> Ω -> E)
    (meanOracle : ℕ -> E)
    (pNorm stepNorm : ℕ -> Ω -> ℝ)
    {N : ℕ} (hN : N ≠ 0)
    (hD_N_nonneg : 0 ≤ D N)
    (hconvComposite : ConvexOn ℝ C (compositeObjective f g))
    (hLip : LipschitzOnWith (Real.toNNReal L) f C)
    (hphi : FirstOrderStrongConvexOn C phi gradPhi alphaPhi)
    (hx : ∀ n, n < N -> x n ∈ C)
    (hxStar : xStar ∈ C)
    (hFstar : Fstar = compositeObjective f g xStar)
    (hD_current : ∀ n, n < N ->
      D n = bregmanDivergence phi gradPhi xStar (x n))
    (hD_next : ∀ n, n < N ->
      D (n + 1) =
        ∫ ω, bregmanDivergence phi gradPhi xStar (xPlus n ω) ∂μ)
    (hstep : ∀ n, n < N -> ∀ᵐ ω ∂μ,
      IsMirrorProximalGradientStep C f g (fun _ : E => p n ω)
        phi gradPhi alphaG h (x n) (xPlus n ω))
    (hp_int : ∀ n, n < N -> Integrable (p n) μ)
    (hcond_mean : ∀ n, n < N ->
      μ[p n | Ffiltration n] =ᵐ[μ] fun _ => meanOracle n)
    (hmean_sub : ∀ n, n < N ->
      IsRelativeSubgradientAt C f (meanOracle n)
        phi gradPhi alphaF (x n))
    (hxPlus : ∀ n, n < N -> ∀ᵐ ω ∂μ, xPlus n ω ∈ C)
    (havg_int : Integrable
      (fun ω =>
        compositeObjective f g
          (weightedSampleAverage
            (fun n => (chewi109Lambda alphaF alphaG h) ^ (N - 1 - n))
            xPlus N ω)) μ)
    (hFplus : ∀ n, n < N ->
      Integrable (fun ω => compositeObjective f g (xPlus n ω)) μ)
    (hDphi : ∀ n, n < N ->
      Integrable
        (fun ω => bregmanDivergence phi gradPhi (xPlus n ω) (x n)) μ)
    (hDnext_int : ∀ n, n < N ->
      Integrable
        (fun ω => bregmanDivergence phi gradPhi xStar (xPlus n ω)) μ)
    (hpsi_int : ∀ n, n < N ->
      Integrable (fun ω =>
        mirrorProximalGradientModel f g (fun _ : E => p n ω)
          phi gradPhi h (x n) (xPlus n ω)) μ)
    (hpsiStar_int : ∀ n, n < N ->
      Integrable (fun ω =>
        mirrorProximalGradientModel f g (fun _ : E => p n ω)
          phi gradPhi h (x n) xStar) μ)
    (hstepSq : ∀ n, n < N ->
      Integrable (fun ω => ‖xPlus n ω - x n‖ ^ (2 : ℕ)) μ)
    (hstepRms_sq : ∀ n, n < N ->
      stepRms n ^ (2 : ℕ) ≤ ∫ ω, ‖xPlus n ω - x n‖ ^ (2 : ℕ) ∂μ)
    (hstep_point : ∀ n, n < N ->
      (fun ω => ‖xPlus n ω - x n‖) ≤ᵐ[μ] stepNorm n)
    (hpNorm_nonneg : ∀ n, n < N -> 0 ≤ᵐ[μ] pNorm n)
    (hstep_nonneg : ∀ n, n < N -> 0 ≤ᵐ[μ] stepNorm n)
    (hpNorm_mem : ∀ n, n < N ->
      MemLp (pNorm n) (ENNReal.ofReal (2 : ℝ)) μ)
    (hstep_mem : ∀ n, n < N ->
      MemLp (stepNorm n) (ENNReal.ofReal (2 : ℝ)) μ)
    (hpNorm_point : ∀ n, n < N ->
      (fun ω => ‖p n ω‖) ≤ᵐ[μ] pNorm n)
    (hpNorm_root : ∀ n, n < N ->
      (∫ ω, pNorm n ω ^ (2 : ℝ) ∂μ) ^ (1 / (2 : ℝ)) ≤ L)
    (hstep_root : ∀ n, n < N ->
      (∫ ω, stepNorm n ω ^ (2 : ℝ) ∂μ) ^ (1 / (2 : ℝ)) ≤ stepRms n)
    (hgap_sum : ∀ n, n < N ->
      Fstar + gap (n + 1) =
        ∫ ω, compositeObjective f g (xPlus n ω) ∂μ) :
    (∫ ω,
        compositeObjective f g
          (weightedSampleAverage
            (fun n => (chewi109Lambda alphaF alphaG h) ^ (N - 1 - n))
            xPlus N ω) ∂μ) - Fstar ≤
      (alphaF + alphaG) /
          (((chewi109Lambda alphaF alphaG h) ^ N)⁻¹ - 1) * D 0 +
        (1 + alphaG * h) *
          (2 * L ^ (2 : ℕ) * h / alphaPhi) := by
  exact
    chewi121_nonsmooth_weightedSampleAverage_gap_le_displayed_of_integral_l2_sampled_models_relativeSubgradient
      (μ := μ) (C := C) (f := f) (g := g) (phi := phi)
      (gradPhi := gradPhi) (alphaF := alphaF) (alphaG := alphaG)
      (alphaPhi := alphaPhi) (L := L) (h := h) (Fstar := Fstar)
      htotal_pos halphaG_nonneg hh halphaPhi hL_nonneg hden_pos
      hlambda_pos D gap stepRms x xStar p xPlus pNorm stepNorm hN
      hD_N_nonneg hconvComposite hLip hphi hx hxStar hFstar hD_current
      hD_next hstep hp_int
      (fun n hn => by
        have hmean :
            (∫ ω, p n ω ∂μ) = meanOracle n :=
          integral_eq_const_of_filtration_condExp_ae_eq_const
            (μ := μ) Ffiltration n (p n) (meanOracle n)
            (hcond_mean n hn)
        simpa [hmean] using hmean_sub n hn)
      hxPlus havg_int hFplus hDphi hDnext_int hpsi_int hpsiStar_int
      hstepSq hstepRms_sq hstep_point hpNorm_nonneg hstep_nonneg
      hpNorm_mem hstep_mem hpNorm_point hpNorm_root hstep_root hgap_sum

/--
Smooth-case Chewi Theorem 12.1 rate from expected model components: this is
the theorem-facing wrapper just before the full Bochner stochastic-gradient
discharge.
-/
theorem chewi121_smooth_weightedAverageGap_le_geometric_of_component_model_bounds
    {alphaF alphaG alphaPhi sigma dim h Fstar : ℝ}
    (htotal_pos : 0 < alphaF + alphaG)
    (hh : 0 < h) (halphaPhi : 0 < alphaPhi)
    (hden_pos : 0 < 1 + alphaG * h)
    (hlambda_pos : 0 < chewi109Lambda alphaF alphaG h)
    (D gap psiNext psiStar expectedNext DfAvg DphiAvg noiseTerm varianceRms
      stepRms : ℕ -> ℝ)
    {N : ℕ} (hN : N ≠ 0)
    (hD_N_nonneg : 0 ≤ D N)
    (hgrowth : ∀ n, n < N ->
      (alphaG + 1 / h) * D (n + 1) + psiNext n ≤ psiStar n)
    (hstar_upper : ∀ n, n < N ->
      psiStar n ≤ Fstar + ((1 - alphaF * h) / h) * D n)
    (hraw : ∀ n, n < N ->
      expectedNext n - DfAvg n + (1 / h) * DphiAvg n - noiseTerm n ≤
        psiNext n)
    (hdf_absorb : ∀ n, n < N ->
      DfAvg n ≤ (1 / (2 * h)) * DphiAvg n)
    (hphi_lower : ∀ n, n < N ->
      (alphaPhi / 2) * stepRms n ^ (2 : ℕ) ≤ DphiAvg n)
    (hnoise : ∀ n, n < N -> noiseTerm n ≤ varianceRms n * stepRms n)
    (hvariance : ∀ n, n < N ->
      varianceRms n ^ (2 : ℕ) ≤ sigma ^ (2 : ℕ) * dim)
    (hgap_sum : ∀ n, n < N -> Fstar + gap (n + 1) = expectedNext n) :
    (1 / (∑ n ∈ Finset.range N,
          (chewi109Lambda alphaF alphaG h) ^ (N - 1 - n))) *
        (∑ n ∈ Finset.range N,
          (chewi109Lambda alphaF alphaG h) ^ (N - 1 - n) * gap (n + 1)) ≤
      (alphaF + alphaG) /
          (((chewi109Lambda alphaF alphaG h) ^ N)⁻¹ - 1) * D 0 +
        sigma ^ (2 : ℕ) * dim * h / alphaPhi := by
  refine
    chewi121_smooth_weightedAverageGap_le_geometric_of_rms_model_bounds
      (alphaF := alphaF) (alphaG := alphaG) (alphaPhi := alphaPhi)
      (sigma := sigma) (dim := dim) (h := h) (Fstar := Fstar)
      htotal_pos hh halphaPhi hden_pos hlambda_pos D gap psiNext psiStar
      expectedNext varianceRms stepRms hN hD_N_nonneg hgrowth hstar_upper
      hvariance ?_ hgap_sum
  intro n hn
  exact
    chewi121_smooth_hcore_of_expected_components
      (alphaPhi := alphaPhi) (h := h) (expectedNext := expectedNext n)
      (psiNext := psiNext n) (DfAvg := DfAvg n) (DphiAvg := DphiAvg n)
      (noiseTerm := noiseTerm n) (varianceRms := varianceRms n)
      (stepRms := stepRms n)
      hh (hraw n hn) (hdf_absorb n hn) (hphi_lower n hn) (hnoise n hn)

/--
Non-smooth-case Chewi Theorem 12.1 rate from expected model components.
-/
theorem chewi121_nonsmooth_weightedAverageGap_le_geometric_of_component_model_bounds
    {alphaF alphaG alphaPhi L h Fstar : ℝ}
    (htotal_pos : 0 < alphaF + alphaG)
    (hh : 0 < h) (halphaPhi : 0 < alphaPhi)
    (hden_pos : 0 < 1 + alphaG * h)
    (hlambda_pos : 0 < chewi109Lambda alphaF alphaG h)
    (D gap psiNext psiStar expectedNext DphiAvg lipTerm gradTerm stepRms :
      ℕ -> ℝ)
    {N : ℕ} (hN : N ≠ 0)
    (hD_N_nonneg : 0 ≤ D N)
    (hgrowth : ∀ n, n < N ->
      (alphaG + 1 / h) * D (n + 1) + psiNext n ≤ psiStar n)
    (hstar_upper : ∀ n, n < N ->
      psiStar n ≤ Fstar + ((1 - alphaF * h) / h) * D n)
    (hraw : ∀ n, n < N ->
      expectedNext n - lipTerm n - gradTerm n + (1 / h) * DphiAvg n ≤
        psiNext n)
    (hphi_lower : ∀ n, n < N ->
      (alphaPhi / 2) * stepRms n ^ (2 : ℕ) ≤ DphiAvg n)
    (hlip : ∀ n, n < N -> lipTerm n ≤ L * stepRms n)
    (hgrad : ∀ n, n < N -> gradTerm n ≤ L * stepRms n)
    (hgap_sum : ∀ n, n < N -> Fstar + gap (n + 1) = expectedNext n) :
    (1 / (∑ n ∈ Finset.range N,
          (chewi109Lambda alphaF alphaG h) ^ (N - 1 - n))) *
        (∑ n ∈ Finset.range N,
          (chewi109Lambda alphaF alphaG h) ^ (N - 1 - n) * gap (n + 1)) ≤
      (alphaF + alphaG) /
          (((chewi109Lambda alphaF alphaG h) ^ N)⁻¹ - 1) * D 0 +
        2 * L ^ (2 : ℕ) * h / alphaPhi := by
  refine
    chewi121_nonsmooth_weightedAverageGap_le_geometric_of_rms_model_bounds
      (alphaF := alphaF) (alphaG := alphaG) (alphaPhi := alphaPhi)
      (L := L) (h := h) (Fstar := Fstar)
      htotal_pos hh halphaPhi hden_pos hlambda_pos D gap psiNext psiStar
      expectedNext stepRms hN hD_N_nonneg hgrowth hstar_upper ?_ hgap_sum
  intro n hn
  exact
    chewi121_nonsmooth_hcore_of_expected_components
      (alphaPhi := alphaPhi) (L := L) (h := h)
      (expectedNext := expectedNext n) (psiNext := psiNext n)
      (DphiAvg := DphiAvg n) (lipTerm := lipTerm n)
      (gradTerm := gradTerm n) (stepRms := stepRms n)
      hh (hraw n hn) (hphi_lower n hn) (hlip n hn) (hgrad n hn)

/--
Chewi Theorem 12.1 smooth-case scalar rate, after the stochastic/proximal
one-step estimate has supplied the variance error
`sigma^2 * dim * h^2 / alphaPhi`.
-/
theorem chewi121_smooth_weightedAverageGap_le_of_source_oneStep
    {alphaF alphaG alphaPhi sigma dim h : ℝ}
    (htotal_pos : 0 < alphaF + alphaG)
    (hh : 0 < h) (halphaPhi : 0 < alphaPhi)
    (hden_pos : 0 < 1 + alphaG * h)
    (hlambda_pos : 0 < chewi109Lambda alphaF alphaG h)
    (D gap : ℕ -> ℝ) {N : ℕ} (hN : N ≠ 0)
    (hD_N_nonneg : 0 ≤ D N)
    (hone_step : ∀ n, n < N ->
      (1 + alphaG * h) * D (n + 1) ≤
        (1 - alphaF * h) * D n - h * gap (n + 1) +
          sigma ^ (2 : ℕ) * dim * h ^ (2 : ℕ) / alphaPhi) :
    (1 / (∑ n ∈ Finset.range N,
          (chewi109Lambda alphaF alphaG h) ^ (N - 1 - n))) *
        (∑ n ∈ Finset.range N,
          (chewi109Lambda alphaF alphaG h) ^ (N - 1 - n) * gap (n + 1)) ≤
      (alphaF + alphaG) /
          (((chewi109Lambda alphaF alphaG h) ^ N)⁻¹ - 1) * D 0 +
        sigma ^ (2 : ℕ) * dim * h / alphaPhi := by
  have hmain :=
    chewi121_weightedAverageGap_le_geometric_of_source_oneStep
      (alphaF := alphaF) (alphaG := alphaG) (h := h)
      (err := sigma ^ (2 : ℕ) * dim * h ^ (2 : ℕ) / alphaPhi)
      htotal_pos hh hden_pos hlambda_pos D gap hN hD_N_nonneg hone_step
  have herr :
      (sigma ^ (2 : ℕ) * dim * h ^ (2 : ℕ) / alphaPhi) / h =
        sigma ^ (2 : ℕ) * dim * h / alphaPhi := by
    field_simp [hh.ne', halphaPhi.ne']
  simpa [herr] using hmain

/--
Chewi Theorem 12.1 non-smooth-case scalar rate, after the stochastic/proximal
one-step estimate has supplied the bounded-gradient error
`2 * L^2 * h^2 / alphaPhi`.
-/
theorem chewi121_nonsmooth_weightedAverageGap_le_of_source_oneStep
    {alphaF alphaG alphaPhi L h : ℝ}
    (htotal_pos : 0 < alphaF + alphaG)
    (hh : 0 < h) (halphaPhi : 0 < alphaPhi)
    (hden_pos : 0 < 1 + alphaG * h)
    (hlambda_pos : 0 < chewi109Lambda alphaF alphaG h)
    (D gap : ℕ -> ℝ) {N : ℕ} (hN : N ≠ 0)
    (hD_N_nonneg : 0 ≤ D N)
    (hone_step : ∀ n, n < N ->
      (1 + alphaG * h) * D (n + 1) ≤
        (1 - alphaF * h) * D n - h * gap (n + 1) +
          2 * L ^ (2 : ℕ) * h ^ (2 : ℕ) / alphaPhi) :
    (1 / (∑ n ∈ Finset.range N,
          (chewi109Lambda alphaF alphaG h) ^ (N - 1 - n))) *
        (∑ n ∈ Finset.range N,
          (chewi109Lambda alphaF alphaG h) ^ (N - 1 - n) * gap (n + 1)) ≤
      (alphaF + alphaG) /
          (((chewi109Lambda alphaF alphaG h) ^ N)⁻¹ - 1) * D 0 +
        2 * L ^ (2 : ℕ) * h / alphaPhi := by
  have hmain :=
    chewi121_weightedAverageGap_le_geometric_of_source_oneStep
      (alphaF := alphaF) (alphaG := alphaG) (h := h)
      (err := 2 * L ^ (2 : ℕ) * h ^ (2 : ℕ) / alphaPhi)
      htotal_pos hh hden_pos hlambda_pos D gap hN hD_N_nonneg hone_step
  have herr :
      (2 * L ^ (2 : ℕ) * h ^ (2 : ℕ) / alphaPhi) / h =
        2 * L ^ (2 : ℕ) * h / alphaPhi := by
    field_simp [hh.ne', halphaPhi.ne']
  simpa [herr] using hmain

end Optimization
end StatInference
