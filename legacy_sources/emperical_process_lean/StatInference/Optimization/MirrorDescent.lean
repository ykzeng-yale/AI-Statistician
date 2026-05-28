import StatInference.Optimization.Bregman
import StatInference.Optimization.ProjectedSubgradient
import StatInference.Optimization.Proximal

/-!
# Chewi Chapter 10 mirror descent layer

This module starts the MPGD/OMD theorem lane.  The first packet proves Chewi
Theorem 10.9's one-step inequality in supplied-interface form: the MPGD update
is represented by the relative-growth certificate for the local mirror model,
and the proof reuses the relative lower/upper model wrappers from
`Bregman.lean`.
-/

namespace StatInference
namespace Optimization

open Finset
open scoped InnerProductSpace

variable {E : Type*} [NormedAddCommGroup E] [InnerProductSpace ℝ E]

/-- The local mirror proximal-gradient model from Chewi `(MPGD)`. -/
noncomputable def mirrorProximalGradientModel
    (f g : E -> ℝ) (gradF : E -> E)
    (phi : E -> ℝ) (gradPhi : E -> E)
    (h : ℝ) (x z : E) : ℝ :=
  f x + inner ℝ (gradF x) (z - x) + g z +
    (1 / h) * bregmanDivergence phi gradPhi z x

/--
Source-shaped certificate that `xPlus` is one MPGD step from `x`.

The growth field is the line in Chewi's proof of Theorem 10.9:
`psi_x(y) >= psi_x(x+) + (alpha_g + 1/h) D_phi(y,x+)`.
-/
structure IsMirrorProximalGradientStep
    (C : Set E) (f g : E -> ℝ) (gradF : E -> E)
    (phi : E -> ℝ) (gradPhi : E -> E)
    (alphaG h : ℝ) (x xPlus : E) : Prop where
  mem_start : x ∈ C
  mem_next : xPlus ∈ C
  growth : ∀ ⦃y : E⦄, y ∈ C ->
    mirrorProximalGradientModel f g gradF phi gradPhi h x xPlus +
        (alphaG + 1 / h) * bregmanDivergence phi gradPhi y xPlus ≤
      mirrorProximalGradientModel f g gradF phi gradPhi h x y

theorem mirrorProximalGradientModel_le_composite_add_bregman
    {C : Set E} {f g : E -> ℝ} {gradF : E -> E}
    {phi : E -> ℝ} {gradPhi : E -> E} {alphaF h : ℝ} {x y : E}
    (hrel : RelativelyStrongConvexOn C f gradF phi gradPhi alphaF)
    (hx : x ∈ C) (hy : y ∈ C) :
    mirrorProximalGradientModel f g gradF phi gradPhi h x y ≤
      compositeObjective f g y +
        (1 / h - alphaF) * bregmanDivergence phi gradPhi y x := by
  have hmodel := hrel.lower_model hy hx
  unfold mirrorProximalGradientModel compositeObjective
  nlinarith

theorem composite_le_mirrorProximalGradientModel
    {C : Set E} {f g : E -> ℝ} {gradF : E -> E}
    {phi : E -> ℝ} {gradPhi : E -> E} {betaF h : ℝ} {x xPlus : E}
    (hsmooth : RelativelySmoothOn C f gradF phi gradPhi betaF)
    (hx : x ∈ C) (hxPlus : xPlus ∈ C)
    (hh : 0 < h) (hbeta_step : betaF * h ≤ 1)
    (hD_nonneg : 0 ≤ bregmanDivergence phi gradPhi xPlus x) :
    compositeObjective f g xPlus ≤
      mirrorProximalGradientModel f g gradF phi gradPhi h x xPlus := by
  have hsmooth_model := hsmooth.upper_model hxPlus hx
  have hbeta_le_inv : betaF ≤ 1 / h :=
    (le_div_iff₀ hh).2 (by simpa using hbeta_step)
  have hcoeff_nonneg : 0 ≤ 1 / h - betaF := by
    nlinarith
  have hquad :
      0 ≤ (1 / h - betaF) * bregmanDivergence phi gradPhi xPlus x :=
    mul_nonneg hcoeff_nonneg hD_nonneg
  unfold mirrorProximalGradientModel compositeObjective at *
  nlinarith

/--
Chewi Theorem 10.9, one-step MPGD inequality, in supplied-interface form.
-/
theorem mirrorProximalGradient_oneStep_ineq
    {C : Set E} {f g : E -> ℝ} {gradF : E -> E}
    {phi : E -> ℝ} {gradPhi : E -> E}
    {alphaF alphaG betaF h : ℝ} {x xPlus y : E}
    (hconvF : RelativelyStrongConvexOn C f gradF phi gradPhi alphaF)
    (hsmoothF : RelativelySmoothOn C f gradF phi gradPhi betaF)
    (hstep : IsMirrorProximalGradientStep C f g gradF phi gradPhi alphaG h x xPlus)
    (hh : 0 < h) (hbeta_step : betaF * h ≤ 1)
    (hD_next_nonneg : 0 ≤ bregmanDivergence phi gradPhi xPlus x)
    (hy : y ∈ C) :
    (1 + alphaG * h) * bregmanDivergence phi gradPhi y xPlus ≤
      (1 - alphaF * h) * bregmanDivergence phi gradPhi y x -
        h * (compositeObjective f g xPlus - compositeObjective f g y) := by
  have hgrowth := hstep.growth hy
  have hmodel_y :
      mirrorProximalGradientModel f g gradF phi gradPhi h x y ≤
        compositeObjective f g y +
          (1 / h - alphaF) * bregmanDivergence phi gradPhi y x :=
    mirrorProximalGradientModel_le_composite_add_bregman
      hconvF hstep.mem_start hy
  have hmodel_next :
      compositeObjective f g xPlus ≤
        mirrorProximalGradientModel f g gradF phi gradPhi h x xPlus :=
    composite_le_mirrorProximalGradientModel
      hsmoothF hstep.mem_start hstep.mem_next hh hbeta_step hD_next_nonneg
  have hcore :
      (alphaG + 1 / h) * bregmanDivergence phi gradPhi y xPlus ≤
        compositeObjective f g y +
          (1 / h - alphaF) * bregmanDivergence phi gradPhi y x -
            compositeObjective f g xPlus := by
    nlinarith
  have hmul := mul_le_mul_of_nonneg_left hcore hh.le (a := h)
  have hleft :
      h * ((alphaG + 1 / h) * bregmanDivergence phi gradPhi y xPlus) =
        (1 + alphaG * h) * bregmanDivergence phi gradPhi y xPlus := by
    field_simp [hh.ne']
    ring
  have hright :
      h *
          (compositeObjective f g y +
            (1 / h - alphaF) * bregmanDivergence phi gradPhi y x -
              compositeObjective f g xPlus) =
        (1 - alphaF * h) * bregmanDivergence phi gradPhi y x -
          h * (compositeObjective f g xPlus - compositeObjective f g y) := by
    field_simp [hh.ne']
    ring
  rw [hleft, hright] at hmul
  exact hmul

/--
The descent corollary in Chewi's proof of Theorem 10.9, obtained by taking
`y = x` in the one-step inequality.
-/
theorem mirrorProximalGradient_descent
    {C : Set E} {f g : E -> ℝ} {gradF : E -> E}
    {phi : E -> ℝ} {gradPhi : E -> E}
    {alphaF alphaG betaF h : ℝ} {x xPlus : E}
    (hconvF : RelativelyStrongConvexOn C f gradF phi gradPhi alphaF)
    (hsmoothF : RelativelySmoothOn C f gradF phi gradPhi betaF)
    (hstep : IsMirrorProximalGradientStep C f g gradF phi gradPhi alphaG h x xPlus)
    (hh : 0 < h) (hbeta_step : betaF * h ≤ 1)
    (hD_next_nonneg : 0 ≤ bregmanDivergence phi gradPhi xPlus x) :
    h * (compositeObjective f g xPlus - compositeObjective f g x) ≤
      - (1 + alphaG * h) * bregmanDivergence phi gradPhi x xPlus := by
  have hone :=
    mirrorProximalGradient_oneStep_ineq
      (C := C) (f := f) (g := g) (gradF := gradF)
      (phi := phi) (gradPhi := gradPhi)
      (alphaF := alphaF) (alphaG := alphaG) (betaF := betaF)
      (h := h) (x := x) (xPlus := xPlus) (y := x)
      hconvF hsmoothF hstep hh hbeta_step hD_next_nonneg hstep.mem_start
  have hstep' := hone
  simp [bregmanDivergence_self] at hstep'
  nlinarith

/-- Source-shaped MPGD trajectory interface. -/
def IsMirrorProximalGradientTrajectory
    (C : Set E) (f g : E -> ℝ) (gradF : E -> E)
    (phi : E -> ℝ) (gradPhi : E -> E)
    (alphaG h : ℝ) (x : ℕ -> E) : Prop :=
  ∀ n, IsMirrorProximalGradientStep C f g gradF phi gradPhi alphaG h
    (x n) (x (n + 1))

theorem IsMirrorProximalGradientTrajectory.step
    {C : Set E} {f g : E -> ℝ} {gradF : E -> E}
    {phi : E -> ℝ} {gradPhi : E -> E}
    {alphaG h : ℝ} {x : ℕ -> E}
    (htraj : IsMirrorProximalGradientTrajectory C f g gradF phi gradPhi alphaG h x)
    (n : ℕ) :
    IsMirrorProximalGradientStep C f g gradF phi gradPhi alphaG h
      (x n) (x (n + 1)) :=
  htraj n

theorem IsMirrorProximalGradientTrajectory.mem
    {C : Set E} {f g : E -> ℝ} {gradF : E -> E}
    {phi : E -> ℝ} {gradPhi : E -> E}
    {alphaG h : ℝ} {x : ℕ -> E}
    (htraj : IsMirrorProximalGradientTrajectory C f g gradF phi gradPhi alphaG h x)
    (n : ℕ) :
    x n ∈ C := by
  cases n with
  | zero => exact (htraj 0).mem_start
  | succ n => exact (htraj n).mem_next

theorem IsMirrorProximalGradientTrajectory.oneStep_ineq
    {C : Set E} {f g : E -> ℝ} {gradF : E -> E}
    {phi : E -> ℝ} {gradPhi : E -> E}
    {alphaF alphaG betaF h : ℝ} {x : ℕ -> E} {y : E}
    (htraj : IsMirrorProximalGradientTrajectory C f g gradF phi gradPhi alphaG h x)
    (hconvF : RelativelyStrongConvexOn C f gradF phi gradPhi alphaF)
    (hsmoothF : RelativelySmoothOn C f gradF phi gradPhi betaF)
    (hh : 0 < h) (hbeta_step : betaF * h ≤ 1)
    (hD_next_nonneg : ∀ n, 0 ≤ bregmanDivergence phi gradPhi (x (n + 1)) (x n))
    (hy : y ∈ C) (n : ℕ) :
    (1 + alphaG * h) * bregmanDivergence phi gradPhi y (x (n + 1)) ≤
      (1 - alphaF * h) * bregmanDivergence phi gradPhi y (x n) -
        h * (compositeObjective f g (x (n + 1)) - compositeObjective f g y) :=
  mirrorProximalGradient_oneStep_ineq
    hconvF hsmoothF (htraj.step n) hh hbeta_step (hD_next_nonneg n) hy

/--
Generic weighted-sum consequence for the MPGD-style recurrence
`u_{n+1} <= A u_n - rho * gap_{n+1}`.

This is the Chapter 10 variant of the scalar post-Gronwall step in Theorem
3.4, with a single `rho` rather than the Euclidean `2*h` coefficient.
-/
theorem weightedSumBound_of_gronwall_negative_forcing_one
    {A rho : ℝ} (hA : 0 ≤ A) (u gap : ℕ -> ℝ) (N : ℕ)
    (huN_nonneg : 0 ≤ u N)
    (hrec : ∀ n, n < N ->
      u (n + 1) ≤ A * u n - rho * gap (n + 1)) :
    rho *
        (∑ n ∈ Finset.range N, A ^ (N - 1 - n) * gap (n + 1)) ≤
      A ^ N * u 0 := by
  have hmain :=
    weightedSumBound_of_gronwall_negative_forcing
      (A := A) (h := rho / 2) hA u gap N huN_nonneg
      (by
        intro n hn
        have h := hrec n hn
        calc
          u (n + 1) ≤ A * u n - rho * gap (n + 1) := h
          _ = A * u n - 2 * (rho / 2) * gap (n + 1) := by ring)
  have hleft :
      rho * (∑ n ∈ Finset.range N, A ^ (N - 1 - n) * gap (n + 1)) =
        2 * (rho / 2) *
          (∑ n ∈ Finset.range N, A ^ (N - 1 - n) * gap (n + 1)) := by
    ring
  rw [hleft]
  exact hmain

/--
Finite weighted-denominator final-gap bound for the MPGD scalar recurrence.
-/
theorem finalGap_le_weighted_denominator_of_one_step
    {A rho : ℝ} (hA : 0 ≤ A) (hrho : 0 < rho)
    (u gap : ℕ -> ℝ) {N : ℕ} (hN : N ≠ 0)
    (huN_nonneg : 0 ≤ u N)
    (hrec : ∀ n, n < N ->
      u (n + 1) ≤ A * u n - rho * gap (n + 1))
    (hmono : ∀ n, n < N -> gap N ≤ gap (n + 1)) :
    gap N ≤
      (A ^ N * u 0) /
        (rho * ∑ n ∈ Finset.range N, A ^ (N - 1 - n)) := by
  let weights : ℝ := ∑ n ∈ Finset.range N, A ^ (N - 1 - n)
  have hweights_pos : 0 < weights := by
    simpa [weights] using geometricWeights_sum_pos (A := A) hA hN
  have hden_pos : 0 < rho * weights := mul_pos hrho hweights_pos
  have hupper :=
    weightedSumBound_of_gronwall_negative_forcing_one
      (A := A) (rho := rho) hA u gap N huN_nonneg hrec
  have hsum_le :
      weights * gap N ≤
        ∑ n ∈ Finset.range N, A ^ (N - 1 - n) * gap (n + 1) := by
    rw [Finset.sum_mul]
    refine Finset.sum_le_sum ?_
    intro n hn
    exact mul_le_mul_of_nonneg_left
      (hmono n (Finset.mem_range.mp hn)) (pow_nonneg hA _)
  have hlower :
      rho * (weights * gap N) ≤
        rho *
          (∑ n ∈ Finset.range N,
            A ^ (N - 1 - n) * gap (n + 1)) :=
    mul_le_mul_of_nonneg_left hsum_le hrho.le
  have hmain : rho * (weights * gap N) ≤ A ^ N * u 0 :=
    hlower.trans (by simpa [weights] using hupper)
  have hmul : gap N * (rho * weights) ≤ A ^ N * u 0 := by
    calc
      gap N * (rho * weights) = rho * (weights * gap N) := by ring
      _ ≤ A ^ N * u 0 := hmain
  exact (le_div_iff₀ hden_pos).2 hmul

/--
Closed geometric-denominator form for the MPGD scalar recurrence.

If `A = 1 - total * rho`, this rewrites the finite geometric denominator as
`total / ((A^N)⁻¹ - 1)`, matching Chewi Theorem 10.9.
-/
theorem finalGap_le_geometric_denominator_of_one_step
    {A rho total : ℝ} (htotal : 0 < total) (hrho : 0 < rho)
    (hA_pos : 0 < A) (hA_eq : A = 1 - total * rho)
    (u gap : ℕ -> ℝ) {N : ℕ} (hN : N ≠ 0)
    (huN_nonneg : 0 ≤ u N)
    (hrec : ∀ n, n < N ->
      u (n + 1) ≤ A * u n - rho * gap (n + 1))
    (hmono : ∀ n, n < N -> gap N ≤ gap (n + 1)) :
    gap N ≤ total / ((A ^ N)⁻¹ - 1) * u 0 := by
  have hA_nonneg : 0 ≤ A := hA_pos.le
  have hA_lt_one : A < 1 := by
    rw [hA_eq]
    have hmul_pos : 0 < total * rho := mul_pos htotal hrho
    nlinarith
  have hA_ne_one : A ≠ 1 := ne_of_lt hA_lt_one
  have hA_pow_pos : 0 < A ^ N := pow_pos hA_pos N
  have hA_pow_ne : A ^ N ≠ 0 := hA_pow_pos.ne'
  have hA_pow_lt_one : A ^ N < 1 :=
    pow_lt_one₀ hA_nonneg hA_lt_one hN
  have hone_sub_pow_ne : 1 - A ^ N ≠ 0 := by
    nlinarith
  have hfinite :=
    finalGap_le_weighted_denominator_of_one_step
      (A := A) (rho := rho) hA_nonneg hrho u gap hN
      huN_nonneg hrec hmono
  have hsum :
      (∑ n ∈ Finset.range N, A ^ (N - 1 - n)) =
        (1 - A ^ N) / (1 - A) :=
    geometricWeights_sum_eq_div hA_ne_one N
  have hone_sub_A : 1 - A = total * rho := by
    rw [hA_eq]
    ring
  have hrhs :
      (A ^ N * u 0) /
          (rho * ∑ n ∈ Finset.range N, A ^ (N - 1 - n)) =
        total / ((A ^ N)⁻¹ - 1) * u 0 := by
    rw [hsum, hone_sub_A]
    field_simp [htotal.ne', hrho.ne', hA_pow_ne, hone_sub_pow_ne]
  exact hfinite.trans_eq hrhs

/-- Chewi's Chapter 10 contraction factor `λ_h`. -/
noncomputable def chewi109Lambda (alphaF alphaG h : ℝ) : ℝ :=
  (1 - alphaF * h) / (1 + alphaG * h)

/-- Chewi's effective recurrence coefficient after dividing by `1+alpha_g h`. -/
noncomputable def chewi109Rho (alphaG h : ℝ) : ℝ :=
  h / (1 + alphaG * h)

/--
Chewi Theorem 10.9 final MPGD rate, supplied with the one-step inequality and
monotone composite gaps.
-/
theorem chewi109_final_gap_le_geometric_denominator_of_oneStep
    {F phi : E -> ℝ} {gradPhi : E -> E} {x : ℕ -> E} {xStar : E}
    {alphaF alphaG h : ℝ}
    (htotal_pos : 0 < alphaF + alphaG)
    (hh : 0 < h)
    (hden_pos : 0 < 1 + alphaG * h)
    (hlambda_pos : 0 < chewi109Lambda alphaF alphaG h)
    {N : ℕ} (hN : N ≠ 0)
    (hD_nonneg : 0 ≤ bregmanDivergence phi gradPhi xStar (x N))
    (hone_step : ∀ n,
      (1 + alphaG * h) * bregmanDivergence phi gradPhi xStar (x (n + 1)) ≤
        (1 - alphaF * h) * bregmanDivergence phi gradPhi xStar (x n) -
          h * (F (x (n + 1)) - F xStar))
    (hmono : ∀ n, n < N ->
      F (x N) - F xStar ≤ F (x (n + 1)) - F xStar) :
    F (x N) - F xStar ≤
      (alphaF + alphaG) /
        (((chewi109Lambda alphaF alphaG h) ^ N)⁻¹ - 1) *
          bregmanDivergence phi gradPhi xStar (x 0) := by
  let A : ℝ := chewi109Lambda alphaF alphaG h
  let rho : ℝ := chewi109Rho alphaG h
  let u : ℕ -> ℝ := fun n => bregmanDivergence phi gradPhi xStar (x n)
  let gap : ℕ -> ℝ := fun n => F (x n) - F xStar
  have hrho_pos : 0 < rho := by
    exact div_pos hh hden_pos
  have hA_eq : A = 1 - (alphaF + alphaG) * rho := by
    have hden_ne_comm : 1 + h * alphaG ≠ 0 := by
      nlinarith [hden_pos]
    dsimp [A, rho, chewi109Lambda, chewi109Rho]
    field_simp [hden_pos.ne', hden_ne_comm]
    ring
  have hrec : ∀ n, n < N -> u (n + 1) ≤ A * u n - rho * gap (n + 1) := by
    intro n hn
    have hstep := hone_step n
    have hdiv :
        u (n + 1) ≤
          ((1 - alphaF * h) * u n - h * gap (n + 1)) /
            (1 + alphaG * h) := by
      have hstep' :
          u (n + 1) * (1 + alphaG * h) ≤
            (1 - alphaF * h) * u n - h * gap (n + 1) := by
        simpa [u, gap, mul_comm, mul_left_comm, mul_assoc] using hstep
      exact (le_div_iff₀ hden_pos).2 hstep'
    calc
      u (n + 1) ≤
          ((1 - alphaF * h) * u n - h * gap (n + 1)) /
            (1 + alphaG * h) := hdiv
      _ = A * u n - rho * gap (n + 1) := by
          dsimp [A, rho, chewi109Lambda, chewi109Rho]
          field_simp [hden_pos.ne']
  have hbound :=
    finalGap_le_geometric_denominator_of_one_step
      (A := A) (rho := rho) (total := alphaF + alphaG)
      htotal_pos hrho_pos (by simpa [A] using hlambda_pos) hA_eq
      u gap hN (by simpa [u] using hD_nonneg) hrec
      (by
        intro n hn
        simpa [gap] using hmono n hn)
  simpa [A, rho, u, gap, chewi109Lambda, chewi109Rho, div_eq_mul_inv,
    mul_assoc] using hbound

/--
Chewi Theorem 10.9 final MPGD rate for a source-shaped trajectory, assembled
from the compiled one-step inequality.
-/
theorem chewi109_final_gap_le_geometric_denominator_of_trajectory
    {C : Set E} {f g : E -> ℝ} {gradF : E -> E}
    {phi : E -> ℝ} {gradPhi : E -> E} {x : ℕ -> E} {xStar : E}
    {alphaF alphaG betaF h : ℝ}
    (htraj : IsMirrorProximalGradientTrajectory
      C f g gradF phi gradPhi alphaG h x)
    (hconvF : RelativelyStrongConvexOn C f gradF phi gradPhi alphaF)
    (hsmoothF : RelativelySmoothOn C f gradF phi gradPhi betaF)
    (hh : 0 < h) (hbeta_step : betaF * h ≤ 1)
    (hD_next_nonneg :
      ∀ n, 0 ≤ bregmanDivergence phi gradPhi (x (n + 1)) (x n))
    (hxStar : xStar ∈ C)
    (htotal_pos : 0 < alphaF + alphaG)
    (hden_pos : 0 < 1 + alphaG * h)
    (hlambda_pos : 0 < chewi109Lambda alphaF alphaG h)
    {N : ℕ} (hN : N ≠ 0)
    (hD_starN_nonneg : 0 ≤ bregmanDivergence phi gradPhi xStar (x N))
    (hmono : ∀ n, n < N ->
      compositeObjective f g (x N) - compositeObjective f g xStar ≤
        compositeObjective f g (x (n + 1)) - compositeObjective f g xStar) :
    compositeObjective f g (x N) - compositeObjective f g xStar ≤
      (alphaF + alphaG) /
        (((chewi109Lambda alphaF alphaG h) ^ N)⁻¹ - 1) *
          bregmanDivergence phi gradPhi xStar (x 0) := by
  refine
    chewi109_final_gap_le_geometric_denominator_of_oneStep
      (F := compositeObjective f g) (phi := phi) (gradPhi := gradPhi)
      (x := x) (xStar := xStar)
      (alphaF := alphaF) (alphaG := alphaG) (h := h)
      htotal_pos hh hden_pos hlambda_pos hN hD_starN_nonneg ?_ hmono
  intro n
  exact
    htraj.oneStep_ineq hconvF hsmoothF hh hbeta_step
      hD_next_nonneg hxStar n

/--
Scalar Young/completing-square inequality used in Chewi Theorem 10.11:
`-2 L r + alpha/(2h) r^2` is bounded below by `-2 L^2 h / alpha`.
-/
theorem chewi1011_young_lower_bound
    {L alphaPhi h r : ℝ} (hh : 0 < h) (halphaPhi : 0 < alphaPhi) :
    -(2 * L ^ (2 : ℕ) * h / alphaPhi) ≤
      -2 * L * r + (alphaPhi / (2 * h)) * r ^ (2 : ℕ) := by
  have hden : 0 < 2 * h * alphaPhi := by positivity
  have hsquare : 0 ≤ (alphaPhi * r - 2 * L * h) ^ (2 : ℕ) := sq_nonneg _
  have hnonneg :
      0 ≤
        (alphaPhi * r - 2 * L * h) ^ (2 : ℕ) /
          (2 * h * alphaPhi) :=
    div_nonneg hsquare hden.le
  have hidentity :
      (alphaPhi * r - 2 * L * h) ^ (2 : ℕ) /
          (2 * h * alphaPhi) =
        -2 * L * r + (alphaPhi / (2 * h)) * r ^ (2 : ℕ) +
          2 * L ^ (2 : ℕ) * h / alphaPhi := by
    field_simp [hh.ne', halphaPhi.ne']
    ring
  rw [hidentity] at hnonneg
  nlinarith

/--
Chewi Theorem 10.11 analytic lower bound for the local mirror model from the
two displayed source estimates
`D_f(x⁺,x) <= 2 L r` and `D_phi(x⁺,x) >= alphaPhi/2 * r^2`.

The norm/dual-norm proof of these two estimates remains outside this small
interface, but the model lower bound no longer needs to be supplied as an
opaque assumption.
-/
theorem mirrorProximalGradientModel_lower_of_bregman_bounds
    {f g : E -> ℝ} {gradF : E -> E}
    {phi : E -> ℝ} {gradPhi : E -> E}
    {L alphaPhi h r : ℝ} {x xPlus : E}
    (hh : 0 < h) (halphaPhi : 0 < alphaPhi)
    (hDf_upper :
      bregmanDivergence f gradF xPlus x ≤ 2 * L * r)
    (hDphi_lower :
      (alphaPhi / 2) * r ^ (2 : ℕ) ≤
        bregmanDivergence phi gradPhi xPlus x) :
    compositeObjective f g xPlus - 2 * L ^ (2 : ℕ) * h / alphaPhi ≤
      mirrorProximalGradientModel f g gradF phi gradPhi h x xPlus := by
  have hDf_linear :
      f xPlus ≤ f x + inner ℝ (gradF x) (xPlus - x) + 2 * L * r := by
    unfold bregmanDivergence at hDf_upper
    nlinarith
  have hDphi_scaled :
      (alphaPhi / (2 * h)) * r ^ (2 : ℕ) ≤
        (1 / h) * bregmanDivergence phi gradPhi xPlus x := by
    have hinv_nonneg : 0 ≤ (1 / h) := by positivity
    have hmul :=
      mul_le_mul_of_nonneg_left hDphi_lower hinv_nonneg
    calc
      (alphaPhi / (2 * h)) * r ^ (2 : ℕ) =
          (1 / h) * ((alphaPhi / 2) * r ^ (2 : ℕ)) := by
            field_simp [hh.ne']
      _ ≤ (1 / h) * bregmanDivergence phi gradPhi xPlus x := hmul
  have hyoung :=
    chewi1011_young_lower_bound
      (L := L) (alphaPhi := alphaPhi) (h := h) (r := r)
      hh halphaPhi
  unfold mirrorProximalGradientModel compositeObjective
  nlinarith

/--
Ordinary Hilbert-norm version of the Cauchy-Schwarz/Lipschitz estimate in
Chewi Theorem 10.11:
`D_f(x⁺,x) <= 2 L ||x⁺-x||`.
-/
theorem bregmanDivergence_le_two_mul_lipschitz_norm
    {C : Set E} {f : E -> ℝ} {gradF : E -> E}
    {L : ℝ} {x xPlus : E}
    (hLip : LipschitzOnWith (Real.toNNReal L) f C)
    (hL_nonneg : 0 ≤ L)
    (hx : x ∈ C) (hxPlus : xPlus ∈ C)
    (hgrad_norm : ‖gradF x‖ ≤ L) :
    bregmanDivergence f gradF xPlus x ≤
      2 * L * ‖xPlus - x‖ := by
  let r : ℝ := ‖xPlus - x‖
  have hLip_upper :
      f xPlus ≤ f x + L * r := by
    have hraw := hLip.le_add_mul hxPlus hx
    simpa [r, Real.coe_toNNReal L hL_nonneg, dist_eq_norm] using hraw
  have hneg_inner_le_norm :
      -inner ℝ (gradF x) (xPlus - x) ≤ ‖gradF x‖ * r := by
    have habs := abs_real_inner_le_norm (gradF x) (xPlus - x)
    exact (neg_le_abs _).trans (by simpa [r] using habs)
  have hnorm_mul_le :
      ‖gradF x‖ * r ≤ L * r :=
    mul_le_mul_of_nonneg_right hgrad_norm (by positivity)
  unfold bregmanDivergence
  nlinarith

/--
First-order strong convexity of the mirror map gives the norm lower bound on
the Bregman divergence used in Chewi Theorem 10.11.
-/
theorem bregmanDivergence_lower_of_firstOrderStrongConvexOn
    {C : Set E} {phi : E -> ℝ} {gradPhi : E -> E}
    {alphaPhi : ℝ} {x xPlus : E}
    (hphi : FirstOrderStrongConvexOn C phi gradPhi alphaPhi)
    (hx : x ∈ C) (hxPlus : xPlus ∈ C) :
    (alphaPhi / 2) * ‖xPlus - x‖ ^ (2 : ℕ) ≤
      bregmanDivergence phi gradPhi xPlus x := by
  have hmodel := hphi.lower_model hx hxPlus
  unfold bregmanDivergence
  nlinarith

/--
Ordinary Hilbert-norm analytic discharge of the Chewi 10.11 local model lower
bound from Lipschitzness of `f`, a gradient/subgradient norm bound, and
first-order strong convexity of the mirror map.
-/
theorem mirrorProximalGradientModel_lower_of_lipschitz_norm
    {C : Set E} {f g : E -> ℝ} {gradF : E -> E}
    {phi : E -> ℝ} {gradPhi : E -> E}
    {L alphaPhi h : ℝ} {x xPlus : E}
    (hLip : LipschitzOnWith (Real.toNNReal L) f C)
    (hL_nonneg : 0 ≤ L)
    (hphi : FirstOrderStrongConvexOn C phi gradPhi alphaPhi)
    (hh : 0 < h) (halphaPhi : 0 < alphaPhi)
    (hx : x ∈ C) (hxPlus : xPlus ∈ C)
    (hgrad_norm : ‖gradF x‖ ≤ L) :
    compositeObjective f g xPlus - 2 * L ^ (2 : ℕ) * h / alphaPhi ≤
      mirrorProximalGradientModel f g gradF phi gradPhi h x xPlus :=
  mirrorProximalGradientModel_lower_of_bregman_bounds
    (f := f) (g := g) (gradF := gradF)
    (phi := phi) (gradPhi := gradPhi)
    (L := L) (alphaPhi := alphaPhi) (h := h)
    (r := ‖xPlus - x‖) (x := x) (xPlus := xPlus)
    hh halphaPhi
    (bregmanDivergence_le_two_mul_lipschitz_norm
      (C := C) (f := f) (gradF := gradF)
      (L := L) (x := x) (xPlus := xPlus)
      hLip hL_nonneg hx hxPlus hgrad_norm)
    (bregmanDivergence_lower_of_firstOrderStrongConvexOn
      (C := C) (phi := phi) (gradPhi := gradPhi)
      (alphaPhi := alphaPhi) (x := x) (xPlus := xPlus)
      hphi hx hxPlus)

/--
Chewi Theorem 10.11 nonsmooth MPGD one-step recurrence from the source proof,
with the Cauchy-Schwarz/Lipschitz lower bound on the local mirror model
supplied as an interface.

The supplied lower bound corresponds to
`ψ_x(x⁺) >= F(x⁺) - 2 L^2 h / alphaPhi`.
-/
theorem mirrorProximalGradient_nonsmooth_oneStep_ineq
    {C : Set E} {f g : E -> ℝ} {gradF : E -> E}
    {phi : E -> ℝ} {gradPhi : E -> E}
    {L alphaPhi h : ℝ} {x xPlus xStar : E}
    (hconvF : RelativelyStrongConvexOn C f gradF phi gradPhi 0)
    (hstep : IsMirrorProximalGradientStep C f g gradF phi gradPhi 0 h x xPlus)
    (hh : 0 < h)
    (hxStar : xStar ∈ C)
    (hmodel_lower :
      compositeObjective f g xPlus - 2 * L ^ (2 : ℕ) * h / alphaPhi ≤
        mirrorProximalGradientModel f g gradF phi gradPhi h x xPlus) :
    bregmanDivergence phi gradPhi xStar xPlus ≤
      bregmanDivergence phi gradPhi xStar x -
        h * (compositeObjective f g xPlus - compositeObjective f g xStar) +
          2 * L ^ (2 : ℕ) * h ^ (2 : ℕ) / alphaPhi := by
  have hgrowth := hstep.growth hxStar
  have hmodel_star :
      mirrorProximalGradientModel f g gradF phi gradPhi h x xStar ≤
        compositeObjective f g xStar +
          (1 / h) * bregmanDivergence phi gradPhi xStar x := by
    have hraw :=
      mirrorProximalGradientModel_le_composite_add_bregman
        (C := C) (f := f) (g := g) (gradF := gradF)
        (phi := phi) (gradPhi := gradPhi) (alphaF := 0) (h := h)
        hconvF hstep.mem_start hxStar
    simpa using hraw
  have hcore :
      compositeObjective f g xPlus - 2 * L ^ (2 : ℕ) * h / alphaPhi +
          (1 / h) * bregmanDivergence phi gradPhi xStar xPlus ≤
        compositeObjective f g xStar +
          (1 / h) * bregmanDivergence phi gradPhi xStar x := by
    nlinarith
  have hmul := mul_le_mul_of_nonneg_left hcore hh.le (a := h)
  have hleft :
      h *
        (compositeObjective f g xPlus - 2 * L ^ (2 : ℕ) * h / alphaPhi +
          (1 / h) * bregmanDivergence phi gradPhi xStar xPlus) =
        h * (compositeObjective f g xPlus) -
          2 * L ^ (2 : ℕ) * h ^ (2 : ℕ) / alphaPhi +
            bregmanDivergence phi gradPhi xStar xPlus := by
    field_simp [hh.ne']
  have hright :
      h *
        (compositeObjective f g xStar +
          (1 / h) * bregmanDivergence phi gradPhi xStar x) =
        h * (compositeObjective f g xStar) +
          bregmanDivergence phi gradPhi xStar x := by
    field_simp [hh.ne']
  rw [hleft, hright] at hmul
  nlinarith

/--
Chewi Theorem 10.11 nonsmooth MPGD one-step recurrence from the two analytic
Bregman estimates displayed in the proof.
-/
theorem mirrorProximalGradient_nonsmooth_oneStep_ineq_of_bregman_bounds
    {C : Set E} {f g : E -> ℝ} {gradF : E -> E}
    {phi : E -> ℝ} {gradPhi : E -> E}
    {L alphaPhi h r : ℝ} {x xPlus xStar : E}
    (hconvF : RelativelyStrongConvexOn C f gradF phi gradPhi 0)
    (hstep : IsMirrorProximalGradientStep C f g gradF phi gradPhi 0 h x xPlus)
    (hh : 0 < h) (halphaPhi : 0 < alphaPhi)
    (hxStar : xStar ∈ C)
    (hDf_upper :
      bregmanDivergence f gradF xPlus x ≤ 2 * L * r)
    (hDphi_lower :
      (alphaPhi / 2) * r ^ (2 : ℕ) ≤
        bregmanDivergence phi gradPhi xPlus x) :
    bregmanDivergence phi gradPhi xStar xPlus ≤
      bregmanDivergence phi gradPhi xStar x -
        h * (compositeObjective f g xPlus - compositeObjective f g xStar) +
          2 * L ^ (2 : ℕ) * h ^ (2 : ℕ) / alphaPhi :=
  mirrorProximalGradient_nonsmooth_oneStep_ineq
    (C := C) (f := f) (g := g) (gradF := gradF)
    (phi := phi) (gradPhi := gradPhi)
    (L := L) (alphaPhi := alphaPhi) (h := h)
    (x := x) (xPlus := xPlus) (xStar := xStar)
    hconvF hstep hh hxStar
    (mirrorProximalGradientModel_lower_of_bregman_bounds
      (f := f) (g := g) (gradF := gradF)
      (phi := phi) (gradPhi := gradPhi)
      (L := L) (alphaPhi := alphaPhi) (h := h) (r := r)
      (x := x) (xPlus := xPlus)
      hh halphaPhi hDf_upper hDphi_lower)

/--
Telescoping average-gap consequence of the nonsmooth MPGD recurrence in
Chewi Theorem 10.11.
-/
theorem chewi1011_average_gap_le_of_recurrence
    {D gap : ℕ -> ℝ} {h err : ℝ}
    (hh : 0 < h) {N : ℕ} (hN : N ≠ 0)
    (hD_N_nonneg : 0 ≤ D N)
    (hrec : ∀ n, n < N ->
      D (n + 1) ≤ D n - h * gap (n + 1) + err) :
    (1 / (N : ℝ)) *
        (∑ n ∈ Finset.range N, gap (n + 1)) ≤
      D 0 / ((N : ℝ) * h) + err / h := by
  have hN_pos_nat : 0 < N := Nat.pos_of_ne_zero hN
  have hN_pos : 0 < (N : ℝ) := by
    exact_mod_cast hN_pos_nat
  let S : ℝ := ∑ n ∈ Finset.range N, gap (n + 1)
  have hstep : ∀ n, n < N ->
      h * gap (n + 1) ≤ D n - D (n + 1) + err := by
    intro n hn
    have h := hrec n hn
    nlinarith
  have hsum :
      ∑ n ∈ Finset.range N, h * gap (n + 1) ≤
        ∑ n ∈ Finset.range N, (D n - D (n + 1) + err) := by
    exact Finset.sum_le_sum fun n hn => hstep n (Finset.mem_range.mp hn)
  have hleft :
      ∑ n ∈ Finset.range N, h * gap (n + 1) = h * S := by
    simp [S, Finset.mul_sum]
  have hright :
      (∑ n ∈ Finset.range N, (D n - D (n + 1) + err)) =
        D 0 - D N + (N : ℝ) * err := by
    rw [Finset.sum_add_distrib, sum_range_sub_succ]
    simp [Finset.sum_const, Finset.card_range, nsmul_eq_mul]
  have hsum_bound : h * S ≤ D 0 + (N : ℝ) * err := by
    rw [hleft, hright] at hsum
    nlinarith
  have hS_bound : S ≤ (D 0 + (N : ℝ) * err) / h :=
    (le_div_iff₀ hh).2 (by simpa [mul_comm] using hsum_bound)
  have havg_bound :
      (1 / (N : ℝ)) * S ≤
        (1 / (N : ℝ)) * ((D 0 + (N : ℝ) * err) / h) := by
    exact mul_le_mul_of_nonneg_left hS_bound (by positivity)
  have hrhs :
      (1 / (N : ℝ)) * ((D 0 + (N : ℝ) * err) / h) =
        D 0 / ((N : ℝ) * h) + err / h := by
    field_simp [hN_pos.ne', hh.ne']
  rw [hrhs] at havg_bound
  simpa [S] using havg_bound

/--
Chewi Theorem 10.11 average-gap bound from the displayed nonsmooth MPGD
one-step recurrence.
-/
theorem chewi1011_average_gap_le_of_oneStep
    {F phi : E -> ℝ} {gradPhi : E -> E} {x : ℕ -> E} {xStar : E}
    {L alphaPhi h : ℝ}
    (hh : 0 < h) (halphaPhi : 0 < alphaPhi)
    {N : ℕ} (hN : N ≠ 0)
    (hD_N_nonneg : 0 ≤ bregmanDivergence phi gradPhi xStar (x N))
    (hone_step : ∀ n, n < N ->
      bregmanDivergence phi gradPhi xStar (x (n + 1)) ≤
        bregmanDivergence phi gradPhi xStar (x n) -
          h * (F (x (n + 1)) - F xStar) +
            2 * L ^ (2 : ℕ) * h ^ (2 : ℕ) / alphaPhi) :
    (1 / (N : ℝ)) *
        (∑ n ∈ Finset.range N, (F (x (n + 1)) - F xStar)) ≤
      bregmanDivergence phi gradPhi xStar (x 0) / ((N : ℝ) * h) +
        2 * L ^ (2 : ℕ) * h / alphaPhi := by
  let D : ℕ -> ℝ := fun n => bregmanDivergence phi gradPhi xStar (x n)
  let gap : ℕ -> ℝ := fun n => F (x n) - F xStar
  let err : ℝ := 2 * L ^ (2 : ℕ) * h ^ (2 : ℕ) / alphaPhi
  have hmain :=
    chewi1011_average_gap_le_of_recurrence
      (D := D) (gap := gap) (h := h) (err := err)
      hh hN (by simpa [D] using hD_N_nonneg)
      (by
        intro n hn
        simpa [D, gap, err] using hone_step n hn)
  have herr :
      err / h = 2 * L ^ (2 : ℕ) * h / alphaPhi := by
    dsimp [err]
    field_simp [hh.ne', halphaPhi.ne']
  simpa [D, gap, err, herr] using hmain

/--
Chewi Theorem 11.8 scalar last-iterate wrapper.  A zero-error mirror-descent
telescope gives an average-gap bound; monotonicity of the displayed objective
gaps turns it into the last-iterate `D_0 / N` rate used for Sinkhorn.
-/
theorem chewi118_last_gap_le_of_recurrence
    {D gap : ℕ -> ℝ} {N : ℕ} (hN : N ≠ 0)
    (hD_N_nonneg : 0 ≤ D N)
    (hrec : ∀ n, n < N -> D (n + 1) ≤ D n - gap (n + 1))
    (hmono : ∀ n, n < N -> gap N ≤ gap (n + 1)) :
    gap N ≤ D 0 / (N : ℝ) := by
  let S : ℝ := ∑ n ∈ Finset.range N, gap (n + 1)
  have hN_pos_nat : 0 < N := Nat.pos_of_ne_zero hN
  have hN_pos : 0 < (N : ℝ) := by
    exact_mod_cast hN_pos_nat
  have havg :
      (1 / (N : ℝ)) * S ≤ D 0 / (N : ℝ) := by
    have hbase :=
      chewi1011_average_gap_le_of_recurrence
        (D := D) (gap := gap) (h := 1) (err := 0)
        (by norm_num) hN hD_N_nonneg
        (by
          intro n hn
          have hstep := hrec n hn
          simpa using hstep)
    have hrhs :
        D 0 / ((N : ℝ) * 1) + 0 / 1 = D 0 / (N : ℝ) := by ring
    simpa [S, hrhs] using hbase
  have hsum_lower : (N : ℝ) * gap N ≤ S := by
    calc
      (N : ℝ) * gap N
          = ∑ _n ∈ Finset.range N, gap N := by
              simp [Finset.sum_const, nsmul_eq_mul, mul_comm]
      _ ≤ ∑ n ∈ Finset.range N, gap (n + 1) := by
              exact Finset.sum_le_sum fun n hn => hmono n (Finset.mem_range.mp hn)
      _ = S := rfl
  have hlast_le_avg : gap N ≤ (1 / (N : ℝ)) * S := by
    rw [one_div_mul_eq_div]
    have hsum_lower' : gap N * (N : ℝ) ≤ S := by
      simpa [mul_comm] using hsum_lower
    exact (le_div_iff₀ hN_pos).2 hsum_lower'
  exact hlast_le_avg.trans havg

/--
Chewi Theorem 11.8 selected-iterate fallback.  The same zero-error
mirror-descent telescope gives a `D_0 / N` bound for some displayed gap among
the first `N` selected iterates, without any monotonicity assumption.
-/
theorem chewi118_exists_gap_le_of_recurrence
    {D gap : ℕ -> ℝ} {N : ℕ} (hN : N ≠ 0)
    (hD_N_nonneg : 0 ≤ D N)
    (hrec : ∀ n, n < N -> D (n + 1) ≤ D n - gap (n + 1)) :
    ∃ n, n < N ∧ gap (n + 1) ≤ D 0 / (N : ℝ) := by
  let shiftedGap : ℕ -> ℝ := fun n => gap (n + 1)
  let S : ℝ := ∑ n ∈ Finset.range N, shiftedGap n
  have hN_pos_nat : 0 < N := Nat.pos_of_ne_zero hN
  have hN_pos : 0 < (N : ℝ) := by
    exact_mod_cast hN_pos_nat
  have havg :
      (1 / (N : ℝ)) * S ≤ D 0 / (N : ℝ) := by
    have hbase :=
      chewi1011_average_gap_le_of_recurrence
        (D := D) (gap := gap) (h := 1) (err := 0)
        (by norm_num) hN hD_N_nonneg
        (by
          intro n hn
          have hstep := hrec n hn
          simpa using hstep)
    have hrhs :
        D 0 / ((N : ℝ) * 1) + 0 / 1 = D 0 / (N : ℝ) := by ring
    simpa [S, shiftedGap, hrhs] using hbase
  have hsum_bound : S ≤ (N : ℝ) * (D 0 / (N : ℝ)) := by
    rw [one_div_mul_eq_div] at havg
    have hmul := (le_div_iff₀ hN_pos).1 havg
    have hS_le_D0 : S ≤ D 0 := by
      have hleft : (N : ℝ) * (S / (N : ℝ)) = S := by
        field_simp [hN_pos.ne']
      nlinarith
    have hright : (N : ℝ) * (D 0 / (N : ℝ)) = D 0 := by
      field_simp [hN_pos.ne']
    rwa [hright]
  simpa [shiftedGap, S] using
    exists_le_average_of_sum_le
      (a := shiftedGap) (N := N) (B := D 0 / (N : ℝ))
      hN hsum_bound

/--
Chewi Theorem 11.8 supplied one-step form for a concrete objective.  This is
the theorem-facing layer for Sinkhorn-as-mirror-descent: once the Sinkhorn
iteration supplies the zero-error Bregman descent recurrence and monotone KL
gaps, the last marginal KL is at most the initial Bregman distance divided by
`N`.
-/
theorem chewi118_last_gap_le_of_oneStep
    {F phi : E -> ℝ} {gradPhi : E -> E} {x : ℕ -> E} {xStar : E}
    {N : ℕ} (hN : N ≠ 0)
    (hD_N_nonneg : 0 ≤ bregmanDivergence phi gradPhi xStar (x N))
    (hone_step : ∀ n, n < N ->
      bregmanDivergence phi gradPhi xStar (x (n + 1)) ≤
        bregmanDivergence phi gradPhi xStar (x n) -
          (F (x (n + 1)) - F xStar))
    (hmono : ∀ n, n < N ->
      F (x N) - F xStar ≤ F (x (n + 1)) - F xStar) :
    F (x N) - F xStar ≤
      bregmanDivergence phi gradPhi xStar (x 0) / (N : ℝ) :=
  chewi118_last_gap_le_of_recurrence
    (D := fun n => bregmanDivergence phi gradPhi xStar (x n))
    (gap := fun n => F (x n) - F xStar)
    hN hD_N_nonneg
    (by
      intro n hn
      simpa using hone_step n hn)
    (by
      intro n hn
      simpa using hmono n hn)

/--
Chewi Theorem 11.8 supplied selected-iterate form for a concrete objective.
The entropy recurrence alone gives the displayed `D_0 / N` rate for at least
one of the selected iterates `x_{n+1}`.
-/
theorem chewi118_exists_gap_le_of_oneStep
    {F phi : E -> ℝ} {gradPhi : E -> E} {x : ℕ -> E} {xStar : E}
    {N : ℕ} (hN : N ≠ 0)
    (hD_N_nonneg : 0 ≤ bregmanDivergence phi gradPhi xStar (x N))
    (hone_step : ∀ n, n < N ->
      bregmanDivergence phi gradPhi xStar (x (n + 1)) ≤
        bregmanDivergence phi gradPhi xStar (x n) -
          (F (x (n + 1)) - F xStar)) :
    ∃ n, n < N ∧
      F (x (n + 1)) - F xStar ≤
        bregmanDivergence phi gradPhi xStar (x 0) / (N : ℝ) :=
  chewi118_exists_gap_le_of_recurrence
    (D := fun n => bregmanDivergence phi gradPhi xStar (x n))
    (gap := fun n => F (x n) - F xStar)
    hN hD_N_nonneg
    (by
      intro n hn
      simpa using hone_step n hn)

/--
Chewi Theorem 10.11 source-facing averaged-iterate bound.  The Jensen step is
reused from the Chapter 6 projected-subgradient layer by applying it to the
shifted sequence `n ↦ x_{n+1}`.
-/
theorem chewi1011_iterateAverage_gap_le_of_oneStep
    {C : Set E} {F phi : E -> ℝ} {gradPhi : E -> E}
    {x : ℕ -> E} {xStar : E}
    {L alphaPhi h : ℝ} {N : ℕ}
    (hconvF : ConvexOn ℝ C F)
    (hmem : ∀ n, n < N -> x (n + 1) ∈ C)
    (hh : 0 < h) (halphaPhi : 0 < alphaPhi)
    (hN : N ≠ 0)
    (hD_N_nonneg : 0 ≤ bregmanDivergence phi gradPhi xStar (x N))
    (hone_step : ∀ n, n < N ->
      bregmanDivergence phi gradPhi xStar (x (n + 1)) ≤
        bregmanDivergence phi gradPhi xStar (x n) -
          h * (F (x (n + 1)) - F xStar) +
            2 * L ^ (2 : ℕ) * h ^ (2 : ℕ) / alphaPhi) :
    F (iterateAverage (fun n => x (n + 1)) N) - F xStar ≤
      bregmanDivergence phi gradPhi xStar (x 0) / ((N : ℝ) * h) +
        2 * L ^ (2 : ℕ) * h / alphaPhi := by
  have hjensen :=
    convex_value_iterateAverage_sub_le_average_gap
      (C := C) (f := F) (x := fun n => x (n + 1))
      (xStar := xStar) (N := N) hconvF hmem hN
  have havg :=
    chewi1011_average_gap_le_of_oneStep
      (F := F) (phi := phi) (gradPhi := gradPhi)
      (x := x) (xStar := xStar) (L := L)
      (alphaPhi := alphaPhi) (h := h)
      hh halphaPhi hN hD_N_nonneg hone_step
  exact hjensen.trans havg

/--
Scalar closing step for Chewi Theorem 10.11.  With the displayed positive
step-size choice `h^2 = alphaPhi * Rphi^2 / (2 * L^2 * N)`, the average-bound
right-hand side is at most `L Rphi sqrt(8/(alphaPhi N))`.
-/
theorem chewi1011_stepsize_rhs_bound
    {D0 L Rphi alphaPhi h : ℝ} {N : ℕ}
    (hL : 0 < L) (hRphi : 0 < Rphi)
    (halphaPhi : 0 < alphaPhi) (hh : 0 < h)
    (hN : N ≠ 0)
    (hD0_le : D0 ≤ Rphi ^ (2 : ℕ))
    (hh_sq :
      h ^ (2 : ℕ) =
        alphaPhi * Rphi ^ (2 : ℕ) /
          (2 * L ^ (2 : ℕ) * (N : ℝ))) :
    D0 / ((N : ℝ) * h) + 2 * L ^ (2 : ℕ) * h / alphaPhi ≤
      L * Rphi * Real.sqrt (8 / (alphaPhi * (N : ℝ))) := by
  have hN_pos_nat : 0 < N := Nat.pos_of_ne_zero hN
  have hN_pos : 0 < (N : ℝ) := by
    exact_mod_cast hN_pos_nat
  have hden_pos : 0 < (N : ℝ) * h := mul_pos hN_pos hh
  have hD_scaled :
      D0 / ((N : ℝ) * h) ≤
        Rphi ^ (2 : ℕ) / ((N : ℝ) * h) :=
    div_le_div_of_nonneg_right hD0_le hden_pos.le
  have hterm :
      Rphi ^ (2 : ℕ) / ((N : ℝ) * h) =
        2 * L ^ (2 : ℕ) * h / alphaPhi := by
    field_simp [hN_pos.ne', hh.ne', hL.ne', halphaPhi.ne'] at hh_sq ⊢
    nlinarith
  have hclosed_core :
      Rphi ^ (2 : ℕ) / ((N : ℝ) * h) +
          2 * L ^ (2 : ℕ) * h / alphaPhi =
        4 * L ^ (2 : ℕ) * h / alphaPhi := by
    rw [hterm]
    ring
  have hsqrt_arg_nonneg :
      0 ≤ 8 / (alphaPhi * (N : ℝ)) := by positivity
  have hleft_nonneg :
      0 ≤ 4 * L ^ (2 : ℕ) * h / alphaPhi := by positivity
  have hright_nonneg :
      0 ≤ L * Rphi * Real.sqrt (8 / (alphaPhi * (N : ℝ))) := by
    positivity
  have hclosed_squares :
      (4 * L ^ (2 : ℕ) * h / alphaPhi) ^ (2 : ℕ) =
        (L * Rphi * Real.sqrt (8 / (alphaPhi * (N : ℝ)))) ^ (2 : ℕ) := by
    rw [mul_pow, mul_pow, Real.sq_sqrt hsqrt_arg_nonneg]
    have hh_sq' := hh_sq
    field_simp [hN_pos.ne', hL.ne', halphaPhi.ne'] at hh_sq' ⊢
    nlinarith
  have hclosed :
      4 * L ^ (2 : ℕ) * h / alphaPhi =
        L * Rphi * Real.sqrt (8 / (alphaPhi * (N : ℝ))) :=
    (sq_eq_sq₀ hleft_nonneg hright_nonneg).mp hclosed_squares
  nlinarith

/--
Chewi Theorem 10.11 one-step supplied-interface bound with the displayed
positive step-size choice.
-/
theorem chewi1011_average_gap_le_of_oneStep_stepsize
    {F phi : E -> ℝ} {gradPhi : E -> E} {x : ℕ -> E} {xStar : E}
    {L Rphi alphaPhi h : ℝ} {N : ℕ}
    (hL : 0 < L) (hRphi : 0 < Rphi)
    (halphaPhi : 0 < alphaPhi) (hh : 0 < h)
    (hN : N ≠ 0)
    (hD0_le :
      bregmanDivergence phi gradPhi xStar (x 0) ≤ Rphi ^ (2 : ℕ))
    (hh_sq :
      h ^ (2 : ℕ) =
        alphaPhi * Rphi ^ (2 : ℕ) /
          (2 * L ^ (2 : ℕ) * (N : ℝ)))
    (hD_N_nonneg : 0 ≤ bregmanDivergence phi gradPhi xStar (x N))
    (hone_step : ∀ n, n < N ->
      bregmanDivergence phi gradPhi xStar (x (n + 1)) ≤
        bregmanDivergence phi gradPhi xStar (x n) -
          h * (F (x (n + 1)) - F xStar) +
            2 * L ^ (2 : ℕ) * h ^ (2 : ℕ) / alphaPhi) :
    (1 / (N : ℝ)) *
        (∑ n ∈ Finset.range N, (F (x (n + 1)) - F xStar)) ≤
      L * Rphi * Real.sqrt (8 / (alphaPhi * (N : ℝ))) := by
  have hbase :=
    chewi1011_average_gap_le_of_oneStep
      (F := F) (phi := phi) (gradPhi := gradPhi)
      (x := x) (xStar := xStar) (L := L)
      (alphaPhi := alphaPhi) (h := h)
      hh halphaPhi hN hD_N_nonneg hone_step
  have hclosed :=
    chewi1011_stepsize_rhs_bound
      (D0 := bregmanDivergence phi gradPhi xStar (x 0))
      (L := L) (Rphi := Rphi) (alphaPhi := alphaPhi)
      (h := h) (N := N)
      hL hRphi halphaPhi hh hN hD0_le hh_sq
  exact hbase.trans hclosed

/--
Chewi Theorem 10.11 averaged-iterate supplied-interface bound with the
displayed positive step-size choice.
-/
theorem chewi1011_iterateAverage_gap_le_of_oneStep_stepsize
    {C : Set E} {F phi : E -> ℝ} {gradPhi : E -> E}
    {x : ℕ -> E} {xStar : E}
    {L Rphi alphaPhi h : ℝ} {N : ℕ}
    (hconvF : ConvexOn ℝ C F)
    (hmem : ∀ n, n < N -> x (n + 1) ∈ C)
    (hL : 0 < L) (hRphi : 0 < Rphi)
    (halphaPhi : 0 < alphaPhi) (hh : 0 < h)
    (hN : N ≠ 0)
    (hD0_le :
      bregmanDivergence phi gradPhi xStar (x 0) ≤ Rphi ^ (2 : ℕ))
    (hh_sq :
      h ^ (2 : ℕ) =
        alphaPhi * Rphi ^ (2 : ℕ) /
          (2 * L ^ (2 : ℕ) * (N : ℝ)))
    (hD_N_nonneg : 0 ≤ bregmanDivergence phi gradPhi xStar (x N))
    (hone_step : ∀ n, n < N ->
      bregmanDivergence phi gradPhi xStar (x (n + 1)) ≤
        bregmanDivergence phi gradPhi xStar (x n) -
          h * (F (x (n + 1)) - F xStar) +
            2 * L ^ (2 : ℕ) * h ^ (2 : ℕ) / alphaPhi) :
    F (iterateAverage (fun n => x (n + 1)) N) - F xStar ≤
      L * Rphi * Real.sqrt (8 / (alphaPhi * (N : ℝ))) := by
  have hbase :=
    chewi1011_iterateAverage_gap_le_of_oneStep
      (C := C) (F := F) (phi := phi) (gradPhi := gradPhi)
      (x := x) (xStar := xStar) (L := L)
      (alphaPhi := alphaPhi) (h := h) (N := N)
      hconvF hmem hh halphaPhi hN hD_N_nonneg hone_step
  have hclosed :=
    chewi1011_stepsize_rhs_bound
      (D0 := bregmanDivergence phi gradPhi xStar (x 0))
      (L := L) (Rphi := Rphi) (alphaPhi := alphaPhi)
      (h := h) (N := N)
      hL hRphi halphaPhi hh hN hD0_le hh_sq
  exact hbase.trans hclosed

/--
Chewi Theorem 10.11 average-gap bound for a source-shaped MPGD trajectory,
assuming the nonsmooth model lower bound from the Cauchy-Schwarz/Lipschitz
part of the proof at each step.
-/
theorem chewi1011_average_gap_le_of_trajectory
    {C : Set E} {f g : E -> ℝ} {gradF : E -> E}
    {phi : E -> ℝ} {gradPhi : E -> E}
    {x : ℕ -> E} {xStar : E} {L alphaPhi h : ℝ} {N : ℕ}
    (htraj : IsMirrorProximalGradientTrajectory
      C f g gradF phi gradPhi 0 h x)
    (hconvF : RelativelyStrongConvexOn C f gradF phi gradPhi 0)
    (hh : 0 < h) (halphaPhi : 0 < alphaPhi)
    (hxStar : xStar ∈ C)
    (hmodel_lower : ∀ n, n < N ->
      compositeObjective f g (x (n + 1)) -
          2 * L ^ (2 : ℕ) * h / alphaPhi ≤
        mirrorProximalGradientModel f g gradF phi gradPhi h (x n) (x (n + 1)))
    (hN : N ≠ 0)
    (hD_N_nonneg : 0 ≤ bregmanDivergence phi gradPhi xStar (x N)) :
    (1 / (N : ℝ)) *
        (∑ n ∈ Finset.range N,
          (compositeObjective f g (x (n + 1)) -
            compositeObjective f g xStar)) ≤
      bregmanDivergence phi gradPhi xStar (x 0) / ((N : ℝ) * h) +
        2 * L ^ (2 : ℕ) * h / alphaPhi := by
  refine
    chewi1011_average_gap_le_of_oneStep
      (F := compositeObjective f g) (phi := phi) (gradPhi := gradPhi)
      (x := x) (xStar := xStar) (L := L)
      (alphaPhi := alphaPhi) (h := h)
      hh halphaPhi hN hD_N_nonneg ?_
  intro n hn
  exact
    mirrorProximalGradient_nonsmooth_oneStep_ineq
      (C := C) (f := f) (g := g) (gradF := gradF)
      (phi := phi) (gradPhi := gradPhi)
      (L := L) (alphaPhi := alphaPhi) (h := h)
      (x := x n) (xPlus := x (n + 1)) (xStar := xStar)
      hconvF (htraj.step n) hh hxStar (hmodel_lower n hn)

/--
Chewi Theorem 10.11 averaged-iterate bound for a source-shaped MPGD
trajectory.
-/
theorem chewi1011_iterateAverage_gap_le_of_trajectory
    {C : Set E} {f g : E -> ℝ} {gradF : E -> E}
    {phi : E -> ℝ} {gradPhi : E -> E}
    {x : ℕ -> E} {xStar : E} {L alphaPhi h : ℝ} {N : ℕ}
    (htraj : IsMirrorProximalGradientTrajectory
      C f g gradF phi gradPhi 0 h x)
    (hconvFmodel : RelativelyStrongConvexOn C f gradF phi gradPhi 0)
    (hconvComposite : ConvexOn ℝ C (compositeObjective f g))
    (hmem : ∀ n, n < N -> x (n + 1) ∈ C)
    (hh : 0 < h) (halphaPhi : 0 < alphaPhi)
    (hxStar : xStar ∈ C)
    (hmodel_lower : ∀ n, n < N ->
      compositeObjective f g (x (n + 1)) -
          2 * L ^ (2 : ℕ) * h / alphaPhi ≤
        mirrorProximalGradientModel f g gradF phi gradPhi h (x n) (x (n + 1)))
    (hN : N ≠ 0)
    (hD_N_nonneg : 0 ≤ bregmanDivergence phi gradPhi xStar (x N)) :
    compositeObjective f g (iterateAverage (fun n => x (n + 1)) N) -
        compositeObjective f g xStar ≤
      bregmanDivergence phi gradPhi xStar (x 0) / ((N : ℝ) * h) +
        2 * L ^ (2 : ℕ) * h / alphaPhi := by
  have hone : ∀ n, n < N ->
      bregmanDivergence phi gradPhi xStar (x (n + 1)) ≤
        bregmanDivergence phi gradPhi xStar (x n) -
          h * (compositeObjective f g (x (n + 1)) -
            compositeObjective f g xStar) +
            2 * L ^ (2 : ℕ) * h ^ (2 : ℕ) / alphaPhi := by
    intro n hn
    exact
      mirrorProximalGradient_nonsmooth_oneStep_ineq
        (C := C) (f := f) (g := g) (gradF := gradF)
        (phi := phi) (gradPhi := gradPhi)
        (L := L) (alphaPhi := alphaPhi) (h := h)
        (x := x n) (xPlus := x (n + 1)) (xStar := xStar)
        hconvFmodel (htraj.step n) hh hxStar (hmodel_lower n hn)
  exact
    chewi1011_iterateAverage_gap_le_of_oneStep
      (C := C) (F := compositeObjective f g) (phi := phi)
      (gradPhi := gradPhi) (x := x) (xStar := xStar)
      (L := L) (alphaPhi := alphaPhi) (h := h)
      (N := N) hconvComposite hmem hh halphaPhi hN hD_N_nonneg hone

/--
Chewi Theorem 10.11 average-gap bound for a trajectory, using the two
displayed analytic Bregman estimates at each step instead of an opaque model
lower-bound assumption.
-/
theorem chewi1011_average_gap_le_of_trajectory_bregman_bounds
    {C : Set E} {f g : E -> ℝ} {gradF : E -> E}
    {phi : E -> ℝ} {gradPhi : E -> E}
    {x : ℕ -> E} {xStar : E} {L alphaPhi h : ℝ}
    {r : ℕ -> ℝ} {N : ℕ}
    (htraj : IsMirrorProximalGradientTrajectory
      C f g gradF phi gradPhi 0 h x)
    (hconvF : RelativelyStrongConvexOn C f gradF phi gradPhi 0)
    (hh : 0 < h) (halphaPhi : 0 < alphaPhi)
    (hxStar : xStar ∈ C)
    (hDf_upper : ∀ n, n < N ->
      bregmanDivergence f gradF (x (n + 1)) (x n) ≤
        2 * L * r n)
    (hDphi_lower : ∀ n, n < N ->
      (alphaPhi / 2) * (r n) ^ (2 : ℕ) ≤
        bregmanDivergence phi gradPhi (x (n + 1)) (x n))
    (hN : N ≠ 0)
    (hD_N_nonneg : 0 ≤ bregmanDivergence phi gradPhi xStar (x N)) :
    (1 / (N : ℝ)) *
        (∑ n ∈ Finset.range N,
          (compositeObjective f g (x (n + 1)) -
            compositeObjective f g xStar)) ≤
      bregmanDivergence phi gradPhi xStar (x 0) / ((N : ℝ) * h) +
        2 * L ^ (2 : ℕ) * h / alphaPhi := by
  refine
    chewi1011_average_gap_le_of_trajectory
      (C := C) (f := f) (g := g) (gradF := gradF)
      (phi := phi) (gradPhi := gradPhi)
      (x := x) (xStar := xStar) (L := L)
      (alphaPhi := alphaPhi) (h := h) (N := N)
      htraj hconvF hh halphaPhi hxStar ?_ hN hD_N_nonneg
  intro n hn
  exact
    mirrorProximalGradientModel_lower_of_bregman_bounds
      (f := f) (g := g) (gradF := gradF)
      (phi := phi) (gradPhi := gradPhi)
      (L := L) (alphaPhi := alphaPhi) (h := h) (r := r n)
      (x := x n) (xPlus := x (n + 1))
      hh halphaPhi (hDf_upper n hn) (hDphi_lower n hn)

/--
Chewi Theorem 10.11 averaged-iterate bound for a trajectory, using the two
displayed analytic Bregman estimates at each step.
-/
theorem chewi1011_iterateAverage_gap_le_of_trajectory_bregman_bounds
    {C : Set E} {f g : E -> ℝ} {gradF : E -> E}
    {phi : E -> ℝ} {gradPhi : E -> E}
    {x : ℕ -> E} {xStar : E} {L alphaPhi h : ℝ}
    {r : ℕ -> ℝ} {N : ℕ}
    (htraj : IsMirrorProximalGradientTrajectory
      C f g gradF phi gradPhi 0 h x)
    (hconvFmodel : RelativelyStrongConvexOn C f gradF phi gradPhi 0)
    (hconvComposite : ConvexOn ℝ C (compositeObjective f g))
    (hmem : ∀ n, n < N -> x (n + 1) ∈ C)
    (hh : 0 < h) (halphaPhi : 0 < alphaPhi)
    (hxStar : xStar ∈ C)
    (hDf_upper : ∀ n, n < N ->
      bregmanDivergence f gradF (x (n + 1)) (x n) ≤
        2 * L * r n)
    (hDphi_lower : ∀ n, n < N ->
      (alphaPhi / 2) * (r n) ^ (2 : ℕ) ≤
        bregmanDivergence phi gradPhi (x (n + 1)) (x n))
    (hN : N ≠ 0)
    (hD_N_nonneg : 0 ≤ bregmanDivergence phi gradPhi xStar (x N)) :
    compositeObjective f g (iterateAverage (fun n => x (n + 1)) N) -
        compositeObjective f g xStar ≤
      bregmanDivergence phi gradPhi xStar (x 0) / ((N : ℝ) * h) +
        2 * L ^ (2 : ℕ) * h / alphaPhi := by
  refine
    chewi1011_iterateAverage_gap_le_of_trajectory
      (C := C) (f := f) (g := g) (gradF := gradF)
      (phi := phi) (gradPhi := gradPhi)
      (x := x) (xStar := xStar) (L := L)
      (alphaPhi := alphaPhi) (h := h) (N := N)
      htraj hconvFmodel hconvComposite hmem hh halphaPhi hxStar ?_
      hN hD_N_nonneg
  intro n hn
  exact
    mirrorProximalGradientModel_lower_of_bregman_bounds
      (f := f) (g := g) (gradF := gradF)
      (phi := phi) (gradPhi := gradPhi)
      (L := L) (alphaPhi := alphaPhi) (h := h) (r := r n)
      (x := x n) (xPlus := x (n + 1))
      hh halphaPhi (hDf_upper n hn) (hDphi_lower n hn)

/--
Chewi Theorem 10.11 trajectory average-gap bound with the displayed positive
step-size choice and the two source analytic Bregman estimates.
-/
theorem chewi1011_average_gap_le_of_trajectory_bregman_bounds_stepsize
    {C : Set E} {f g : E -> ℝ} {gradF : E -> E}
    {phi : E -> ℝ} {gradPhi : E -> E}
    {x : ℕ -> E} {xStar : E} {L Rphi alphaPhi h : ℝ}
    {r : ℕ -> ℝ} {N : ℕ}
    (htraj : IsMirrorProximalGradientTrajectory
      C f g gradF phi gradPhi 0 h x)
    (hconvF : RelativelyStrongConvexOn C f gradF phi gradPhi 0)
    (hL : 0 < L) (hRphi : 0 < Rphi)
    (hh : 0 < h) (halphaPhi : 0 < alphaPhi)
    (hxStar : xStar ∈ C)
    (hD0_le :
      bregmanDivergence phi gradPhi xStar (x 0) ≤ Rphi ^ (2 : ℕ))
    (hh_sq :
      h ^ (2 : ℕ) =
        alphaPhi * Rphi ^ (2 : ℕ) /
          (2 * L ^ (2 : ℕ) * (N : ℝ)))
    (hDf_upper : ∀ n, n < N ->
      bregmanDivergence f gradF (x (n + 1)) (x n) ≤
        2 * L * r n)
    (hDphi_lower : ∀ n, n < N ->
      (alphaPhi / 2) * (r n) ^ (2 : ℕ) ≤
        bregmanDivergence phi gradPhi (x (n + 1)) (x n))
    (hN : N ≠ 0)
    (hD_N_nonneg : 0 ≤ bregmanDivergence phi gradPhi xStar (x N)) :
    (1 / (N : ℝ)) *
        (∑ n ∈ Finset.range N,
          (compositeObjective f g (x (n + 1)) -
            compositeObjective f g xStar)) ≤
      L * Rphi * Real.sqrt (8 / (alphaPhi * (N : ℝ))) := by
  refine
    chewi1011_average_gap_le_of_oneStep_stepsize
      (F := compositeObjective f g) (phi := phi) (gradPhi := gradPhi)
      (x := x) (xStar := xStar) (L := L) (Rphi := Rphi)
      (alphaPhi := alphaPhi) (h := h) (N := N)
      hL hRphi halphaPhi hh hN hD0_le hh_sq hD_N_nonneg ?_
  intro n hn
  exact
    mirrorProximalGradient_nonsmooth_oneStep_ineq_of_bregman_bounds
      (C := C) (f := f) (g := g) (gradF := gradF)
      (phi := phi) (gradPhi := gradPhi)
      (L := L) (alphaPhi := alphaPhi) (h := h) (r := r n)
      (x := x n) (xPlus := x (n + 1)) (xStar := xStar)
      hconvF (htraj.step n) hh halphaPhi hxStar
      (hDf_upper n hn) (hDphi_lower n hn)

/--
Chewi Theorem 10.11 trajectory averaged-iterate bound with the displayed
positive step-size choice and the two source analytic Bregman estimates.
-/
theorem chewi1011_iterateAverage_gap_le_of_trajectory_bregman_bounds_stepsize
    {C : Set E} {f g : E -> ℝ} {gradF : E -> E}
    {phi : E -> ℝ} {gradPhi : E -> E}
    {x : ℕ -> E} {xStar : E} {L Rphi alphaPhi h : ℝ}
    {r : ℕ -> ℝ} {N : ℕ}
    (htraj : IsMirrorProximalGradientTrajectory
      C f g gradF phi gradPhi 0 h x)
    (hconvFmodel : RelativelyStrongConvexOn C f gradF phi gradPhi 0)
    (hconvComposite : ConvexOn ℝ C (compositeObjective f g))
    (hmem : ∀ n, n < N -> x (n + 1) ∈ C)
    (hL : 0 < L) (hRphi : 0 < Rphi)
    (hh : 0 < h) (halphaPhi : 0 < alphaPhi)
    (hxStar : xStar ∈ C)
    (hD0_le :
      bregmanDivergence phi gradPhi xStar (x 0) ≤ Rphi ^ (2 : ℕ))
    (hh_sq :
      h ^ (2 : ℕ) =
        alphaPhi * Rphi ^ (2 : ℕ) /
          (2 * L ^ (2 : ℕ) * (N : ℝ)))
    (hDf_upper : ∀ n, n < N ->
      bregmanDivergence f gradF (x (n + 1)) (x n) ≤
        2 * L * r n)
    (hDphi_lower : ∀ n, n < N ->
      (alphaPhi / 2) * (r n) ^ (2 : ℕ) ≤
        bregmanDivergence phi gradPhi (x (n + 1)) (x n))
    (hN : N ≠ 0)
    (hD_N_nonneg : 0 ≤ bregmanDivergence phi gradPhi xStar (x N)) :
    compositeObjective f g (iterateAverage (fun n => x (n + 1)) N) -
        compositeObjective f g xStar ≤
      L * Rphi * Real.sqrt (8 / (alphaPhi * (N : ℝ))) := by
  refine
    chewi1011_iterateAverage_gap_le_of_oneStep_stepsize
      (C := C) (F := compositeObjective f g) (phi := phi)
      (gradPhi := gradPhi) (x := x) (xStar := xStar)
      (L := L) (Rphi := Rphi) (alphaPhi := alphaPhi)
      (h := h) (N := N)
      hconvComposite hmem hL hRphi halphaPhi hh hN hD0_le
      hh_sq hD_N_nonneg ?_
  intro n hn
  exact
    mirrorProximalGradient_nonsmooth_oneStep_ineq_of_bregman_bounds
      (C := C) (f := f) (g := g) (gradF := gradF)
      (phi := phi) (gradPhi := gradPhi)
      (L := L) (alphaPhi := alphaPhi) (h := h) (r := r n)
      (x := x n) (xPlus := x (n + 1)) (xStar := xStar)
      hconvFmodel (htraj.step n) hh halphaPhi hxStar
      (hDf_upper n hn) (hDphi_lower n hn)

/--
Chewi Theorem 10.11 trajectory average-gap bound in the ordinary Hilbert norm:
the two analytic Bregman estimates are produced from Lipschitzness,
gradient/subgradient norm bounds, and first-order strong convexity of `phi`.
-/
theorem chewi1011_average_gap_le_of_trajectory_lipschitz_norm
    {C : Set E} {f g : E -> ℝ} {gradF : E -> E}
    {phi : E -> ℝ} {gradPhi : E -> E}
    {x : ℕ -> E} {xStar : E} {L alphaPhi h : ℝ} {N : ℕ}
    (htraj : IsMirrorProximalGradientTrajectory
      C f g gradF phi gradPhi 0 h x)
    (hconvF : RelativelyStrongConvexOn C f gradF phi gradPhi 0)
    (hLip : LipschitzOnWith (Real.toNNReal L) f C)
    (hL_nonneg : 0 ≤ L)
    (hphi : FirstOrderStrongConvexOn C phi gradPhi alphaPhi)
    (hh : 0 < h) (halphaPhi : 0 < alphaPhi)
    (hxStar : xStar ∈ C)
    (hgrad_norm : ∀ n, n < N -> ‖gradF (x n)‖ ≤ L)
    (hN : N ≠ 0)
    (hD_N_nonneg : 0 ≤ bregmanDivergence phi gradPhi xStar (x N)) :
    (1 / (N : ℝ)) *
        (∑ n ∈ Finset.range N,
          (compositeObjective f g (x (n + 1)) -
            compositeObjective f g xStar)) ≤
      bregmanDivergence phi gradPhi xStar (x 0) / ((N : ℝ) * h) +
        2 * L ^ (2 : ℕ) * h / alphaPhi := by
  refine
    chewi1011_average_gap_le_of_trajectory_bregman_bounds
      (C := C) (f := f) (g := g) (gradF := gradF)
      (phi := phi) (gradPhi := gradPhi)
      (x := x) (xStar := xStar) (L := L)
      (alphaPhi := alphaPhi) (h := h)
      (r := fun n => ‖x (n + 1) - x n‖) (N := N)
      htraj hconvF hh halphaPhi hxStar ?_ ?_ hN hD_N_nonneg
  · intro n hn
    exact
      bregmanDivergence_le_two_mul_lipschitz_norm
        (C := C) (f := f) (gradF := gradF)
        (L := L) (x := x n) (xPlus := x (n + 1))
        hLip hL_nonneg (htraj.mem n) (htraj.mem (n + 1))
        (hgrad_norm n hn)
  · intro n _hn
    exact
      bregmanDivergence_lower_of_firstOrderStrongConvexOn
        (C := C) (phi := phi) (gradPhi := gradPhi)
        (alphaPhi := alphaPhi) (x := x n) (xPlus := x (n + 1))
        hphi (htraj.mem n) (htraj.mem (n + 1))

/--
Chewi Theorem 10.11 trajectory averaged-iterate bound in the ordinary Hilbert
norm.
-/
theorem chewi1011_iterateAverage_gap_le_of_trajectory_lipschitz_norm
    {C : Set E} {f g : E -> ℝ} {gradF : E -> E}
    {phi : E -> ℝ} {gradPhi : E -> E}
    {x : ℕ -> E} {xStar : E} {L alphaPhi h : ℝ} {N : ℕ}
    (htraj : IsMirrorProximalGradientTrajectory
      C f g gradF phi gradPhi 0 h x)
    (hconvFmodel : RelativelyStrongConvexOn C f gradF phi gradPhi 0)
    (hconvComposite : ConvexOn ℝ C (compositeObjective f g))
    (hmem : ∀ n, n < N -> x (n + 1) ∈ C)
    (hLip : LipschitzOnWith (Real.toNNReal L) f C)
    (hL_nonneg : 0 ≤ L)
    (hphi : FirstOrderStrongConvexOn C phi gradPhi alphaPhi)
    (hh : 0 < h) (halphaPhi : 0 < alphaPhi)
    (hxStar : xStar ∈ C)
    (hgrad_norm : ∀ n, n < N -> ‖gradF (x n)‖ ≤ L)
    (hN : N ≠ 0)
    (hD_N_nonneg : 0 ≤ bregmanDivergence phi gradPhi xStar (x N)) :
    compositeObjective f g (iterateAverage (fun n => x (n + 1)) N) -
        compositeObjective f g xStar ≤
      bregmanDivergence phi gradPhi xStar (x 0) / ((N : ℝ) * h) +
        2 * L ^ (2 : ℕ) * h / alphaPhi := by
  refine
    chewi1011_iterateAverage_gap_le_of_trajectory_bregman_bounds
      (C := C) (f := f) (g := g) (gradF := gradF)
      (phi := phi) (gradPhi := gradPhi)
      (x := x) (xStar := xStar) (L := L)
      (alphaPhi := alphaPhi) (h := h)
      (r := fun n => ‖x (n + 1) - x n‖) (N := N)
      htraj hconvFmodel hconvComposite hmem hh halphaPhi hxStar
      ?_ ?_ hN hD_N_nonneg
  · intro n hn
    exact
      bregmanDivergence_le_two_mul_lipschitz_norm
        (C := C) (f := f) (gradF := gradF)
        (L := L) (x := x n) (xPlus := x (n + 1))
        hLip hL_nonneg (htraj.mem n) (htraj.mem (n + 1))
        (hgrad_norm n hn)
  · intro n _hn
    exact
      bregmanDivergence_lower_of_firstOrderStrongConvexOn
        (C := C) (phi := phi) (gradPhi := gradPhi)
        (alphaPhi := alphaPhi) (x := x n) (xPlus := x (n + 1))
        hphi (htraj.mem n) (htraj.mem (n + 1))

/--
Chewi Theorem 10.11 trajectory average-gap bound in the ordinary Hilbert norm
with the displayed positive step-size choice.
-/
theorem chewi1011_average_gap_le_of_trajectory_lipschitz_norm_stepsize
    {C : Set E} {f g : E -> ℝ} {gradF : E -> E}
    {phi : E -> ℝ} {gradPhi : E -> E}
    {x : ℕ -> E} {xStar : E} {L Rphi alphaPhi h : ℝ} {N : ℕ}
    (htraj : IsMirrorProximalGradientTrajectory
      C f g gradF phi gradPhi 0 h x)
    (hconvF : RelativelyStrongConvexOn C f gradF phi gradPhi 0)
    (hLip : LipschitzOnWith (Real.toNNReal L) f C)
    (hL : 0 < L) (hRphi : 0 < Rphi)
    (hphi : FirstOrderStrongConvexOn C phi gradPhi alphaPhi)
    (hh : 0 < h) (halphaPhi : 0 < alphaPhi)
    (hxStar : xStar ∈ C)
    (hD0_le :
      bregmanDivergence phi gradPhi xStar (x 0) ≤ Rphi ^ (2 : ℕ))
    (hh_sq :
      h ^ (2 : ℕ) =
        alphaPhi * Rphi ^ (2 : ℕ) /
          (2 * L ^ (2 : ℕ) * (N : ℝ)))
    (hgrad_norm : ∀ n, n < N -> ‖gradF (x n)‖ ≤ L)
    (hN : N ≠ 0)
    (hD_N_nonneg : 0 ≤ bregmanDivergence phi gradPhi xStar (x N)) :
    (1 / (N : ℝ)) *
        (∑ n ∈ Finset.range N,
          (compositeObjective f g (x (n + 1)) -
            compositeObjective f g xStar)) ≤
      L * Rphi * Real.sqrt (8 / (alphaPhi * (N : ℝ))) := by
  refine
    chewi1011_average_gap_le_of_trajectory_bregman_bounds_stepsize
      (C := C) (f := f) (g := g) (gradF := gradF)
      (phi := phi) (gradPhi := gradPhi)
      (x := x) (xStar := xStar) (L := L) (Rphi := Rphi)
      (alphaPhi := alphaPhi) (h := h)
      (r := fun n => ‖x (n + 1) - x n‖) (N := N)
      htraj hconvF hL hRphi hh halphaPhi hxStar
      hD0_le hh_sq ?_ ?_ hN hD_N_nonneg
  · intro n hn
    exact
      bregmanDivergence_le_two_mul_lipschitz_norm
        (C := C) (f := f) (gradF := gradF)
        (L := L) (x := x n) (xPlus := x (n + 1))
        hLip hL.le (htraj.mem n) (htraj.mem (n + 1))
        (hgrad_norm n hn)
  · intro n _hn
    exact
      bregmanDivergence_lower_of_firstOrderStrongConvexOn
        (C := C) (phi := phi) (gradPhi := gradPhi)
        (alphaPhi := alphaPhi) (x := x n) (xPlus := x (n + 1))
        hphi (htraj.mem n) (htraj.mem (n + 1))

/--
Chewi Theorem 10.11 trajectory averaged-iterate bound in the ordinary Hilbert
norm with the displayed positive step-size choice.
-/
theorem chewi1011_iterateAverage_gap_le_of_trajectory_lipschitz_norm_stepsize
    {C : Set E} {f g : E -> ℝ} {gradF : E -> E}
    {phi : E -> ℝ} {gradPhi : E -> E}
    {x : ℕ -> E} {xStar : E} {L Rphi alphaPhi h : ℝ} {N : ℕ}
    (htraj : IsMirrorProximalGradientTrajectory
      C f g gradF phi gradPhi 0 h x)
    (hconvFmodel : RelativelyStrongConvexOn C f gradF phi gradPhi 0)
    (hconvComposite : ConvexOn ℝ C (compositeObjective f g))
    (hmem : ∀ n, n < N -> x (n + 1) ∈ C)
    (hLip : LipschitzOnWith (Real.toNNReal L) f C)
    (hL : 0 < L) (hRphi : 0 < Rphi)
    (hphi : FirstOrderStrongConvexOn C phi gradPhi alphaPhi)
    (hh : 0 < h) (halphaPhi : 0 < alphaPhi)
    (hxStar : xStar ∈ C)
    (hD0_le :
      bregmanDivergence phi gradPhi xStar (x 0) ≤ Rphi ^ (2 : ℕ))
    (hh_sq :
      h ^ (2 : ℕ) =
        alphaPhi * Rphi ^ (2 : ℕ) /
          (2 * L ^ (2 : ℕ) * (N : ℝ)))
    (hgrad_norm : ∀ n, n < N -> ‖gradF (x n)‖ ≤ L)
    (hN : N ≠ 0)
    (hD_N_nonneg : 0 ≤ bregmanDivergence phi gradPhi xStar (x N)) :
    compositeObjective f g (iterateAverage (fun n => x (n + 1)) N) -
        compositeObjective f g xStar ≤
      L * Rphi * Real.sqrt (8 / (alphaPhi * (N : ℝ))) := by
  refine
    chewi1011_iterateAverage_gap_le_of_trajectory_bregman_bounds_stepsize
      (C := C) (f := f) (g := g) (gradF := gradF)
      (phi := phi) (gradPhi := gradPhi)
      (x := x) (xStar := xStar) (L := L) (Rphi := Rphi)
      (alphaPhi := alphaPhi) (h := h)
      (r := fun n => ‖x (n + 1) - x n‖) (N := N)
      htraj hconvFmodel hconvComposite hmem hL hRphi hh halphaPhi
      hxStar hD0_le hh_sq ?_ ?_ hN hD_N_nonneg
  · intro n hn
    exact
      bregmanDivergence_le_two_mul_lipschitz_norm
        (C := C) (f := f) (gradF := gradF)
        (L := L) (x := x n) (xPlus := x (n + 1))
        hLip hL.le (htraj.mem n) (htraj.mem (n + 1))
        (hgrad_norm n hn)
  · intro n _hn
    exact
      bregmanDivergence_lower_of_firstOrderStrongConvexOn
        (C := C) (phi := phi) (gradPhi := gradPhi)
        (alphaPhi := alphaPhi) (x := x n) (xPlus := x (n + 1))
        hphi (htraj.mem n) (htraj.mem (n + 1))

/-- The linear-loss OMD model from Chewi `(OMD)`. -/
noncomputable def onlineMirrorDescentModel
    (p : E) (phi : E -> ℝ) (gradPhi : E -> E)
    (h : ℝ) (x z : E) : ℝ :=
  inner ℝ p (z - x) + (1 / h) * bregmanDivergence phi gradPhi z x

/--
Source-shaped certificate that `xPlus` is one online mirror descent step from
`x` for the linear loss vector `p`.

The growth field records the first-order/Bregman projection inequality used in
the proof of Chewi Theorem 10.13.
-/
structure IsOnlineMirrorDescentStep
    (C : Set E) (phi : E -> ℝ) (gradPhi : E -> E)
    (h : ℝ) (p x xPlus : E) : Prop where
  mem_start : x ∈ C
  mem_next : xPlus ∈ C
  growth : ∀ ⦃y : E⦄, y ∈ C ->
    onlineMirrorDescentModel p phi gradPhi h x xPlus +
        (1 / h) * bregmanDivergence phi gradPhi y xPlus ≤
      onlineMirrorDescentModel p phi gradPhi h x y

/-- Source-shaped OMD trajectory interface. -/
def IsOnlineMirrorDescentTrajectory
    (C : Set E) (phi : E -> ℝ) (gradPhi : E -> E)
    (h : ℝ) (p x : ℕ -> E) : Prop :=
  ∀ n, IsOnlineMirrorDescentStep C phi gradPhi h (p n) (x n) (x (n + 1))

theorem IsOnlineMirrorDescentTrajectory.step
    {C : Set E} {phi : E -> ℝ} {gradPhi : E -> E}
    {h : ℝ} {p x : ℕ -> E}
    (htraj : IsOnlineMirrorDescentTrajectory C phi gradPhi h p x)
    (n : ℕ) :
    IsOnlineMirrorDescentStep C phi gradPhi h (p n) (x n) (x (n + 1)) :=
  htraj n

theorem IsOnlineMirrorDescentTrajectory.mem
    {C : Set E} {phi : E -> ℝ} {gradPhi : E -> E}
    {h : ℝ} {p x : ℕ -> E}
    (htraj : IsOnlineMirrorDescentTrajectory C phi gradPhi h p x)
    (n : ℕ) :
    x n ∈ C := by
  cases n with
  | zero => exact (htraj 0).mem_start
  | succ n => exact (htraj n).mem_next

/--
Scalar Young/completing-square inequality used in Chewi Theorem 10.13:
`-L r + alpha/(2h) r^2` is bounded below by `-L^2 h/(2 alpha)`.
-/
theorem chewi1013_young_lower_bound
    {L alphaPhi h r : ℝ} (hh : 0 < h) (halphaPhi : 0 < alphaPhi) :
    -(L ^ (2 : ℕ) * h / (2 * alphaPhi)) ≤
      -L * r + (alphaPhi / (2 * h)) * r ^ (2 : ℕ) := by
  have hden : 0 < 2 * h * alphaPhi := by positivity
  have hsquare : 0 ≤ (alphaPhi * r - L * h) ^ (2 : ℕ) := sq_nonneg _
  have hnonneg :
      0 ≤
        (alphaPhi * r - L * h) ^ (2 : ℕ) /
          (2 * h * alphaPhi) :=
    div_nonneg hsquare hden.le
  have hidentity :
      (alphaPhi * r - L * h) ^ (2 : ℕ) /
          (2 * h * alphaPhi) =
        -L * r + (alphaPhi / (2 * h)) * r ^ (2 : ℕ) +
          L ^ (2 : ℕ) * h / (2 * alphaPhi) := by
    field_simp [hh.ne', halphaPhi.ne']
    ring
  rw [hidentity] at hnonneg
  nlinarith

/--
First-order strong convexity of the mirror map gives nonnegativity of the
Bregman divergence in the ordinary Hilbert-norm specialization.
-/
theorem bregmanDivergence_nonneg_of_firstOrderStrongConvexOn
    {C : Set E} {phi : E -> ℝ} {gradPhi : E -> E}
    {alphaPhi : ℝ} {x y : E}
    (hphi : FirstOrderStrongConvexOn C phi gradPhi alphaPhi)
    (halphaPhi : 0 ≤ alphaPhi) (hx : x ∈ C) (hy : y ∈ C) :
    0 ≤ bregmanDivergence phi gradPhi y x := by
  have hlower :=
    bregmanDivergence_lower_of_firstOrderStrongConvexOn
      (C := C) (phi := phi) (gradPhi := gradPhi)
      (alphaPhi := alphaPhi) (x := x) (xPlus := y)
      hphi hx hy
  have hleft_nonneg :
      0 ≤ (alphaPhi / 2) * ‖y - x‖ ^ (2 : ℕ) := by positivity
  nlinarith

/--
Ordinary Hilbert-norm analytic lower bound for the OMD local model from
`||p|| <= L` and first-order strong convexity of the mirror map.
-/
theorem onlineMirrorDescentModel_lower_of_norm_bound
    {C : Set E} {phi : E -> ℝ} {gradPhi : E -> E}
    {p x xPlus : E} {L alphaPhi h : ℝ}
    (hphi : FirstOrderStrongConvexOn C phi gradPhi alphaPhi)
    (hpnorm : ‖p‖ ≤ L)
    (hh : 0 < h) (halphaPhi : 0 < alphaPhi)
    (hx : x ∈ C) (hxPlus : xPlus ∈ C) :
    -(L ^ (2 : ℕ) * h / (2 * alphaPhi)) ≤
      onlineMirrorDescentModel p phi gradPhi h x xPlus := by
  let r : ℝ := ‖xPlus - x‖
  have hneg_inner_le_norm :
      -inner ℝ p (xPlus - x) ≤ ‖p‖ * r := by
    have habs := abs_real_inner_le_norm p (xPlus - x)
    exact (neg_le_abs _).trans (by simpa [r] using habs)
  have hnorm_mul_le : ‖p‖ * r ≤ L * r :=
    mul_le_mul_of_nonneg_right hpnorm (by positivity)
  have hinner_lower : -L * r ≤ inner ℝ p (xPlus - x) := by
    nlinarith
  have hD_lower :
      (alphaPhi / 2) * r ^ (2 : ℕ) ≤
        bregmanDivergence phi gradPhi xPlus x := by
    simpa [r] using
      bregmanDivergence_lower_of_firstOrderStrongConvexOn
        (C := C) (phi := phi) (gradPhi := gradPhi)
        (alphaPhi := alphaPhi) (x := x) (xPlus := xPlus)
        hphi hx hxPlus
  have hD_scaled :
      (alphaPhi / (2 * h)) * r ^ (2 : ℕ) ≤
        (1 / h) * bregmanDivergence phi gradPhi xPlus x := by
    have hmul :=
      mul_le_mul_of_nonneg_left hD_lower (by positivity : 0 ≤ (1 / h))
    calc
      (alphaPhi / (2 * h)) * r ^ (2 : ℕ) =
          (1 / h) * ((alphaPhi / 2) * r ^ (2 : ℕ)) := by
            field_simp [hh.ne']
      _ ≤ (1 / h) * bregmanDivergence phi gradPhi xPlus x := hmul
  have hyoung :=
    chewi1013_young_lower_bound
      (L := L) (alphaPhi := alphaPhi) (h := h) (r := r)
      hh halphaPhi
  unfold onlineMirrorDescentModel
  nlinarith

/--
Chewi Theorem 10.13 one-step OMD regret inequality, from the OMD growth
certificate and the Young/Cauchy-Schwarz lower bound on the local model.
-/
theorem onlineMirrorDescent_oneStep_regret
    {C : Set E} {phi : E -> ℝ} {gradPhi : E -> E}
    {p x xPlus y : E} {L alphaPhi h : ℝ}
    (hstep : IsOnlineMirrorDescentStep C phi gradPhi h p x xPlus)
    (hy : y ∈ C)
    (hmodel_lower :
      -(L ^ (2 : ℕ) * h / (2 * alphaPhi)) ≤
        onlineMirrorDescentModel p phi gradPhi h x xPlus) :
    inner ℝ p (x - y) ≤
      (1 / h) *
          (bregmanDivergence phi gradPhi y x -
            bregmanDivergence phi gradPhi y xPlus) +
        L ^ (2 : ℕ) * h / (2 * alphaPhi) := by
  have hgrowth := hstep.growth hy
  have hinner_sym :
      inner ℝ p (x - y) = -inner ℝ p (y - x) := by
    rw [← neg_sub y x, inner_neg_right]
  unfold onlineMirrorDescentModel at hgrowth hmodel_lower
  nlinarith

/--
Finite comparator-regret telescope from the one-step OMD inequality.
-/
theorem onlineMirrorDescent_regret_gap_sum_le_of_oneStep
    {phi : E -> ℝ} {gradPhi : E -> E} {p x : ℕ -> E} {y : E}
    {h err : ℝ} (hh : 0 < h) {T : ℕ}
    (hD_T_nonneg : 0 ≤ bregmanDivergence phi gradPhi y (x T))
    (hone_step : ∀ n, n < T ->
      inner ℝ (p n) (x n - y) ≤
        (1 / h) *
          (bregmanDivergence phi gradPhi y (x n) -
            bregmanDivergence phi gradPhi y (x (n + 1))) + err) :
    (∑ n ∈ Finset.range T, inner ℝ (p n) (x n - y)) ≤
      bregmanDivergence phi gradPhi y (x 0) / h + (T : ℝ) * err := by
  let D : ℕ -> ℝ := fun n => bregmanDivergence phi gradPhi y (x n)
  have hsum :
      (∑ n ∈ Finset.range T, inner ℝ (p n) (x n - y)) ≤
        ∑ n ∈ Finset.range T, ((1 / h) * (D n - D (n + 1)) + err) := by
    exact Finset.sum_le_sum fun n hn => by
      simpa [D] using hone_step n (Finset.mem_range.mp hn)
  have hright :
      (∑ n ∈ Finset.range T, ((1 / h) * (D n - D (n + 1)) + err)) =
        (1 / h) * (D 0 - D T) + (T : ℝ) * err := by
    rw [Finset.sum_add_distrib, ← Finset.mul_sum, sum_range_sub_succ]
    simp [Finset.sum_const, Finset.card_range, nsmul_eq_mul]
  have htel_bound :
      (1 / h) * (D 0 - D T) + (T : ℝ) * err ≤
        D 0 / h + (T : ℝ) * err := by
    have hinv_nonneg : 0 ≤ 1 / h := by positivity
    have hdrop_nonneg : 0 ≤ D T := by simpa [D] using hD_T_nonneg
    have hdrop : D 0 - D T ≤ D 0 := by nlinarith
    have hmul :
        (1 / h) * (D 0 - D T) ≤ (1 / h) * D 0 :=
      mul_le_mul_of_nonneg_left hdrop hinv_nonneg
    have hmul_add :
        (1 / h) * (D 0 - D T) + (T : ℝ) * err ≤
          (1 / h) * D 0 + (T : ℝ) * err := by
      simpa [add_comm, add_left_comm, add_assoc] using
        add_le_add_right hmul ((T : ℝ) * err)
    calc
      (1 / h) * (D 0 - D T) + (T : ℝ) * err
          ≤ (1 / h) * D 0 + (T : ℝ) * err := hmul_add
      _ = D 0 / h + (T : ℝ) * err := by ring
  calc
    (∑ n ∈ Finset.range T, inner ℝ (p n) (x n - y))
        ≤ ∑ n ∈ Finset.range T, ((1 / h) * (D n - D (n + 1)) + err) := hsum
    _ = (1 / h) * (D 0 - D T) + (T : ℝ) * err := hright
    _ ≤ D 0 / h + (T : ℝ) * err := htel_bound

/--
Chewi Theorem 10.13 comparator form from supplied one-step regret
inequalities.  This is stronger than the displayed `inf` statement for each
fixed comparator `y ∈ C`.
-/
theorem chewi1013_regret_bound_of_oneStep
    {phi : E -> ℝ} {gradPhi : E -> E} {p x : ℕ -> E} {y : E}
    {L alphaPhi h : ℝ} (hh : 0 < h) {T : ℕ}
    (hD_T_nonneg : 0 ≤ bregmanDivergence phi gradPhi y (x T))
    (hone_step : ∀ n, n < T ->
      inner ℝ (p n) (x n - y) ≤
        (1 / h) *
          (bregmanDivergence phi gradPhi y (x n) -
            bregmanDivergence phi gradPhi y (x (n + 1))) +
          L ^ (2 : ℕ) * h / (2 * alphaPhi)) :
    (∑ n ∈ Finset.range T, inner ℝ (p n) (x n)) ≤
      (∑ n ∈ Finset.range T, inner ℝ (p n) y) +
        bregmanDivergence phi gradPhi y (x 0) / h +
          (T : ℝ) * (L ^ (2 : ℕ) * h / (2 * alphaPhi)) := by
  have hgap :=
    onlineMirrorDescent_regret_gap_sum_le_of_oneStep
      (phi := phi) (gradPhi := gradPhi) (p := p) (x := x)
      (y := y) (h := h)
      (err := L ^ (2 : ℕ) * h / (2 * alphaPhi))
      hh hD_T_nonneg hone_step
  have hsum_sub :
      (∑ n ∈ Finset.range T, inner ℝ (p n) (x n - y)) =
        (∑ n ∈ Finset.range T, inner ℝ (p n) (x n)) -
          ∑ n ∈ Finset.range T, inner ℝ (p n) y := by
    simp [inner_sub_right, Finset.sum_sub_distrib]
  nlinarith

/--
Chewi Theorem 10.13 comparator-regret bound for a source-shaped OMD
trajectory, with the local model lower bound supplied at each step.
-/
theorem chewi1013_regret_bound_of_trajectory
    {C : Set E} {phi : E -> ℝ} {gradPhi : E -> E}
    {p x : ℕ -> E} {y : E} {L alphaPhi h : ℝ} {T : ℕ}
    (htraj : IsOnlineMirrorDescentTrajectory C phi gradPhi h p x)
    (hy : y ∈ C) (hh : 0 < h)
    (hmodel_lower : ∀ n, n < T ->
      -(L ^ (2 : ℕ) * h / (2 * alphaPhi)) ≤
        onlineMirrorDescentModel (p n) phi gradPhi h (x n) (x (n + 1)))
    (hD_T_nonneg : 0 ≤ bregmanDivergence phi gradPhi y (x T)) :
    (∑ n ∈ Finset.range T, inner ℝ (p n) (x n)) ≤
      (∑ n ∈ Finset.range T, inner ℝ (p n) y) +
        bregmanDivergence phi gradPhi y (x 0) / h +
          (T : ℝ) * (L ^ (2 : ℕ) * h / (2 * alphaPhi)) := by
  refine
    chewi1013_regret_bound_of_oneStep
      (phi := phi) (gradPhi := gradPhi) (p := p) (x := x)
      (y := y) (L := L) (alphaPhi := alphaPhi) (h := h)
      hh hD_T_nonneg ?_
  intro n hn
  exact
    onlineMirrorDescent_oneStep_regret
      (C := C) (phi := phi) (gradPhi := gradPhi)
      (p := p n) (x := x n) (xPlus := x (n + 1))
      (y := y) (L := L) (alphaPhi := alphaPhi) (h := h)
      (htraj.step n) hy (hmodel_lower n hn)

/--
Chewi Theorem 10.13 comparator-regret bound for OMD in the ordinary Hilbert
norm.  The local model lower bound and terminal Bregman nonnegativity are
derived from `||p_n|| <= L` and first-order strong convexity of `phi`.
-/
theorem chewi1013_regret_bound_of_trajectory_norm_bound
    {C : Set E} {phi : E -> ℝ} {gradPhi : E -> E}
    {p x : ℕ -> E} {y : E} {L alphaPhi h : ℝ} {T : ℕ}
    (htraj : IsOnlineMirrorDescentTrajectory C phi gradPhi h p x)
    (hphi : FirstOrderStrongConvexOn C phi gradPhi alphaPhi)
    (hpnorm : ∀ n, n < T -> ‖p n‖ ≤ L)
    (hy : y ∈ C) (hh : 0 < h) (halphaPhi : 0 < alphaPhi) :
    (∑ n ∈ Finset.range T, inner ℝ (p n) (x n)) ≤
      (∑ n ∈ Finset.range T, inner ℝ (p n) y) +
        bregmanDivergence phi gradPhi y (x 0) / h +
          (T : ℝ) * (L ^ (2 : ℕ) * h / (2 * alphaPhi)) := by
  refine
    chewi1013_regret_bound_of_trajectory
      (C := C) (phi := phi) (gradPhi := gradPhi)
      (p := p) (x := x) (y := y)
      (L := L) (alphaPhi := alphaPhi) (h := h) (T := T)
      htraj hy hh ?_ ?_
  · intro n hn
    exact
      onlineMirrorDescentModel_lower_of_norm_bound
        (C := C) (phi := phi) (gradPhi := gradPhi)
        (p := p n) (x := x n) (xPlus := x (n + 1))
        (L := L) (alphaPhi := alphaPhi) (h := h)
        hphi (hpnorm n hn) hh halphaPhi
        (htraj.mem n) (htraj.mem (n + 1))
  · exact
      bregmanDivergence_nonneg_of_firstOrderStrongConvexOn
        (C := C) (phi := phi) (gradPhi := gradPhi)
        (alphaPhi := alphaPhi) (x := x T) (y := y)
        hphi halphaPhi.le (htraj.mem T) hy

/--
Scalar closing step for Chewi Theorem 10.13.  With the displayed positive
step-size choice, recorded as
`h^2 = 2 * alphaPhi * Rphi^2 / (L^2 * T)`, the comparator-regret right-hand
side is at most `L Rphi sqrt(2T/alphaPhi)`.
-/
theorem chewi1013_stepsize_rhs_bound
    {D0 L Rphi alphaPhi h : ℝ} {T : ℕ}
    (hL : 0 < L) (hRphi : 0 < Rphi)
    (halphaPhi : 0 < alphaPhi) (hh : 0 < h)
    (hT : T ≠ 0)
    (hD0_le : D0 ≤ Rphi ^ (2 : ℕ))
    (hh_sq :
      h ^ (2 : ℕ) =
        2 * alphaPhi * Rphi ^ (2 : ℕ) /
          (L ^ (2 : ℕ) * (T : ℝ))) :
    D0 / h + (T : ℝ) * (L ^ (2 : ℕ) * h / (2 * alphaPhi)) ≤
      L * Rphi * Real.sqrt (2 * (T : ℝ) / alphaPhi) := by
  have hT_pos_nat : 0 < T := Nat.pos_of_ne_zero hT
  have hT_pos : 0 < (T : ℝ) := by
    exact_mod_cast hT_pos_nat
  have hD_scaled :
      D0 / h ≤ Rphi ^ (2 : ℕ) / h :=
    div_le_div_of_nonneg_right hD0_le hh.le
  have hterm :
      Rphi ^ (2 : ℕ) / h =
        (T : ℝ) * (L ^ (2 : ℕ) * h / (2 * alphaPhi)) := by
    field_simp [hT_pos.ne', hh.ne', hL.ne', halphaPhi.ne'] at hh_sq ⊢
    nlinarith
  have hclosed_core :
      Rphi ^ (2 : ℕ) / h +
          (T : ℝ) * (L ^ (2 : ℕ) * h / (2 * alphaPhi)) =
        (T : ℝ) * L ^ (2 : ℕ) * h / alphaPhi := by
    rw [hterm]
    ring
  have hsqrt_arg_nonneg :
      0 ≤ 2 * (T : ℝ) / alphaPhi := by positivity
  have hleft_nonneg :
      0 ≤ (T : ℝ) * L ^ (2 : ℕ) * h / alphaPhi := by positivity
  have hright_nonneg :
      0 ≤ L * Rphi * Real.sqrt (2 * (T : ℝ) / alphaPhi) := by
    positivity
  have hclosed_squares :
      ((T : ℝ) * L ^ (2 : ℕ) * h / alphaPhi) ^ (2 : ℕ) =
        (L * Rphi * Real.sqrt (2 * (T : ℝ) / alphaPhi)) ^ (2 : ℕ) := by
    rw [mul_pow, mul_pow, Real.sq_sqrt hsqrt_arg_nonneg]
    have hh_sq' := hh_sq
    field_simp [hT_pos.ne', hL.ne', halphaPhi.ne'] at hh_sq' ⊢
    nlinarith
  have hclosed :
      (T : ℝ) * L ^ (2 : ℕ) * h / alphaPhi =
        L * Rphi * Real.sqrt (2 * (T : ℝ) / alphaPhi) :=
    (sq_eq_sq₀ hleft_nonneg hright_nonneg).mp hclosed_squares
  nlinarith

/--
Chewi Theorem 10.13 ordinary Hilbert-norm comparator-regret bound with the
displayed positive step-size choice.
-/
theorem chewi1013_regret_bound_of_trajectory_norm_bound_stepsize
    {C : Set E} {phi : E -> ℝ} {gradPhi : E -> E}
    {p x : ℕ -> E} {y : E} {L Rphi alphaPhi h : ℝ} {T : ℕ}
    (htraj : IsOnlineMirrorDescentTrajectory C phi gradPhi h p x)
    (hphi : FirstOrderStrongConvexOn C phi gradPhi alphaPhi)
    (hpnorm : ∀ n, n < T -> ‖p n‖ ≤ L)
    (hy : y ∈ C)
    (hL : 0 < L) (hRphi : 0 < Rphi)
    (hh : 0 < h) (halphaPhi : 0 < alphaPhi)
    (hT : T ≠ 0)
    (hD0_le :
      bregmanDivergence phi gradPhi y (x 0) ≤ Rphi ^ (2 : ℕ))
    (hh_sq :
      h ^ (2 : ℕ) =
        2 * alphaPhi * Rphi ^ (2 : ℕ) /
          (L ^ (2 : ℕ) * (T : ℝ))) :
    (∑ n ∈ Finset.range T, inner ℝ (p n) (x n)) ≤
      (∑ n ∈ Finset.range T, inner ℝ (p n) y) +
        L * Rphi * Real.sqrt (2 * (T : ℝ) / alphaPhi) := by
  have hbase :=
    chewi1013_regret_bound_of_trajectory_norm_bound
      (C := C) (phi := phi) (gradPhi := gradPhi)
      (p := p) (x := x) (y := y)
      (L := L) (alphaPhi := alphaPhi) (h := h) (T := T)
      htraj hphi hpnorm hy hh halphaPhi
  have hclosed :=
    chewi1013_stepsize_rhs_bound
      (D0 := bregmanDivergence phi gradPhi y (x 0))
      (L := L) (Rphi := Rphi) (alphaPhi := alphaPhi)
      (h := h) (T := T)
      hL hRphi halphaPhi hh hT hD0_le hh_sq
  nlinarith

/--
Infimum closing step for Chewi Theorem 10.13.  If a regret bound holds against
every comparator in a nonempty set, then it holds against the infimum of the
linear comparator losses.
-/
theorem chewi1013_regret_bound_inf_of_forall_comparator
    {C : Set E} {p x : ℕ -> E} {T : ℕ} {bound : ℝ}
    (hC_nonempty : C.Nonempty)
    (hcomp : ∀ y : E, y ∈ C ->
      (∑ n ∈ Finset.range T, inner ℝ (p n) (x n)) ≤
        (∑ n ∈ Finset.range T, inner ℝ (p n) y) + bound) :
    (∑ n ∈ Finset.range T, inner ℝ (p n) (x n)) ≤
      sInf {v : ℝ | ∃ y : E, y ∈ C ∧
        v = ∑ n ∈ Finset.range T, inner ℝ (p n) y} + bound := by
  let A : ℝ := ∑ n ∈ Finset.range T, inner ℝ (p n) (x n)
  let S : Set ℝ := {v : ℝ | ∃ y : E, y ∈ C ∧
    v = ∑ n ∈ Finset.range T, inner ℝ (p n) y}
  have hS_nonempty : S.Nonempty := by
    rcases hC_nonempty with ⟨y, hy⟩
    exact ⟨∑ n ∈ Finset.range T, inner ℝ (p n) y, ⟨y, hy, rfl⟩⟩
  have hlower : A - bound ≤ sInf S := by
    apply le_csInf hS_nonempty
    intro v hv
    rcases hv with ⟨y, hy, rfl⟩
    have hy_bound := hcomp y hy
    dsimp [A] at hy_bound ⊢
    linarith
  dsimp [A, S] at hlower ⊢
  linarith

/--
Chewi Theorem 10.13 in the displayed infimum form: online mirror descent with
the positive source step size satisfies the Hilbert-norm regret bound against
the best fixed comparator in `C`.
-/
theorem chewi1013_regret_bound_inf_of_trajectory_norm_bound_stepsize
    {C : Set E} {phi : E -> ℝ} {gradPhi : E -> E}
    {p x : ℕ -> E} {L Rphi alphaPhi h : ℝ} {T : ℕ}
    (htraj : IsOnlineMirrorDescentTrajectory C phi gradPhi h p x)
    (hphi : FirstOrderStrongConvexOn C phi gradPhi alphaPhi)
    (hpnorm : ∀ n, n < T -> ‖p n‖ ≤ L)
    (hC_nonempty : C.Nonempty)
    (hL : 0 < L) (hRphi : 0 < Rphi)
    (hh : 0 < h) (halphaPhi : 0 < alphaPhi)
    (hT : T ≠ 0)
    (hD0_le : ∀ y : E, y ∈ C ->
      bregmanDivergence phi gradPhi y (x 0) ≤ Rphi ^ (2 : ℕ))
    (hh_sq :
      h ^ (2 : ℕ) =
        2 * alphaPhi * Rphi ^ (2 : ℕ) /
          (L ^ (2 : ℕ) * (T : ℝ))) :
    (∑ n ∈ Finset.range T, inner ℝ (p n) (x n)) ≤
      sInf {v : ℝ | ∃ y : E, y ∈ C ∧
        v = ∑ n ∈ Finset.range T, inner ℝ (p n) y} +
        L * Rphi * Real.sqrt (2 * (T : ℝ) / alphaPhi) := by
  refine
    chewi1013_regret_bound_inf_of_forall_comparator
      (C := C) (p := p) (x := x) (T := T)
      (bound := L * Rphi * Real.sqrt (2 * (T : ℝ) / alphaPhi))
      hC_nonempty ?_
  intro y hy
  exact
    chewi1013_regret_bound_of_trajectory_norm_bound_stepsize
      (C := C) (phi := phi) (gradPhi := gradPhi)
      (p := p) (x := x) (y := y)
      (L := L) (Rphi := Rphi) (alphaPhi := alphaPhi)
      (h := h) (T := T)
      htraj hphi hpnorm hy hL hRphi hh halphaPhi hT
      (hD0_le y hy) hh_sq

end Optimization
end StatInference
