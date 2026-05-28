import StatInference.Optimization.Theorem54

/-!
# Chewi Chapter 11 alternating minimization

This module starts the deterministic alternating-minimization rate layer.  The
first packet proves the scalar inverse-gap algebra used at the end of Chewi
Theorem 11.4, after the block-coordinate descent estimate has reduced the
algorithm to a quadratic gap recurrence.
-/

namespace StatInference
namespace Optimization

open Finset

/-- Forward telescoping form dual to `sum_range_sub_succ`. -/
theorem sum_range_succ_sub (a : ℕ -> ℝ) (N : ℕ) :
    (∑ n ∈ Finset.range N, (a (n + 1) - a n)) = a N - a 0 := by
  calc
    (∑ n ∈ Finset.range N, (a (n + 1) - a n))
        = ∑ n ∈ Finset.range N, ((-a n) - (-a (n + 1))) := by
            refine Finset.sum_congr rfl ?_
            intro n _hn
            ring
    _ = (-a 0) - (-a N) := by
            simpa using sum_range_sub_succ (fun n => -a n) N
    _ = a N - a 0 := by ring

/--
One-step inverse-gap growth from the quadratic-descent recurrence appearing in
Chewi Theorem 11.4.
-/
theorem chewi114_inverse_gap_step_growth {K g g' : ℝ}
    (hK : 0 < K) (hg : 0 < g) (hg' : 0 < g')
    (hrec : g' ≤ g - g ^ (2 : ℕ) / K) :
    1 / K ≤ 1 / g' - 1 / g := by
  have hquad_pos : 0 < g ^ (2 : ℕ) / K :=
    div_pos (sq_pos_of_pos hg) hK
  have hg'_le_g : g' ≤ g := by nlinarith
  have hmul_le_sq : g * g' ≤ g ^ (2 : ℕ) := by
    simpa [pow_two] using mul_le_mul_of_nonneg_left hg'_le_g hg.le
  have hmain : g * g' ≤ K * (g - g') := by
    have hdrop : g ^ (2 : ℕ) ≤ K * (g - g') := by
      have h := mul_le_mul_of_nonneg_left hrec hK.le
      field_simp [hK.ne'] at h
      nlinarith
    nlinarith
  have hidentity :
      1 / g' - 1 / g = (g - g') / (g * g') := by
    field_simp [hg.ne', hg'.ne']
  rw [hidentity]
  rw [le_div_iff₀ (mul_pos hg hg')]
  rw [div_mul_eq_mul_div]
  rw [div_le_iff₀ hK]
  nlinarith

/--
Chewi Theorem 11.4 inverse-gap telescope after the quadratic-descent phase.

Here `M` is the number of post-threshold iterations and `K` is the source
constant `8 * beta * D^2 * R^2`.
-/
theorem chewi114_inverse_gap_growth_of_quadratic_descent
    {gap : ℕ -> ℝ} {K : ℝ} {n0 M : ℕ}
    (hK : 0 < K)
    (hpos : ∀ m, m ≤ M -> 0 < gap (n0 + m))
    (hrec : ∀ m, m < M ->
      gap (n0 + (m + 1)) ≤
        gap (n0 + m) - gap (n0 + m) ^ (2 : ℕ) / K) :
    (M : ℝ) / K ≤ 1 / gap (n0 + M) - 1 / gap n0 := by
  let invGap : ℕ -> ℝ := fun m => 1 / gap (n0 + m)
  have hstep : ∀ m, m < M -> 1 / K ≤ invGap (m + 1) - invGap m := by
    intro m hm
    exact chewi114_inverse_gap_step_growth
      (K := K) (g := gap (n0 + m)) (g' := gap (n0 + (m + 1)))
      hK (hpos m (Nat.le_of_lt hm)) (hpos (m + 1) (Nat.succ_le_of_lt hm))
      (hrec m hm)
  have hsum :
      (∑ m ∈ Finset.range M, (1 / K : ℝ)) ≤
        ∑ m ∈ Finset.range M, (invGap (m + 1) - invGap m) := by
    exact Finset.sum_le_sum fun m hm => hstep m (Finset.mem_range.mp hm)
  have hconst :
      (∑ m ∈ Finset.range M, (1 / K : ℝ)) = (M : ℝ) / K := by
    simp [Finset.sum_const, Finset.card_range, nsmul_eq_mul, div_eq_mul_inv]
  have htelescope :
      (∑ m ∈ Finset.range M, (invGap (m + 1) - invGap m)) =
        invGap M - invGap 0 :=
    sum_range_succ_sub invGap M
  calc
    (M : ℝ) / K = ∑ m ∈ Finset.range M, (1 / K : ℝ) := hconst.symm
    _ ≤ ∑ m ∈ Finset.range M, (invGap (m + 1) - invGap m) := hsum
    _ = invGap M - invGap 0 := htelescope
    _ = 1 / gap (n0 + M) - 1 / gap n0 := by simp [invGap]

/--
Closed source-facing post-threshold rate from the inverse-gap telescope:
`gap_{n0+M} <= K / M`.
-/
theorem chewi114_gap_le_K_div_iterations_of_quadratic_descent
    {gap : ℕ -> ℝ} {K : ℝ} {n0 M : ℕ}
    (hK : 0 < K) (hM : M ≠ 0)
    (hpos : ∀ m, m ≤ M -> 0 < gap (n0 + m))
    (hrec : ∀ m, m < M ->
      gap (n0 + (m + 1)) ≤
        gap (n0 + m) - gap (n0 + m) ^ (2 : ℕ) / K) :
    gap (n0 + M) ≤ K / (M : ℝ) := by
  have hgrowth :=
    chewi114_inverse_gap_growth_of_quadratic_descent
      (gap := gap) (K := K) (n0 := n0) (M := M) hK hpos hrec
  have hM_pos_nat : 0 < M := Nat.pos_of_ne_zero hM
  have hM_pos : 0 < (M : ℝ) := by exact_mod_cast hM_pos_nat
  have hgapN_pos : 0 < gap (n0 + M) := hpos M le_rfl
  have hgap0_pos : 0 < gap n0 := by
    simpa using hpos 0 (Nat.zero_le M)
  have hdiff_le_inv :
      1 / gap (n0 + M) - 1 / gap n0 ≤ 1 / gap (n0 + M) := by
    have hnonneg : 0 ≤ 1 / gap n0 := by positivity
    nlinarith
  have hMK_le_inv : (M : ℝ) / K ≤ 1 / gap (n0 + M) :=
    hgrowth.trans hdiff_le_inv
  have hMK_le_inv' := hMK_le_inv
  field_simp [hK.ne', hgapN_pos.ne'] at hMK_le_inv'
  rw [le_div_iff₀ hM_pos]
  nlinarith

/--
Accuracy wrapper for the post-threshold phase of Chewi Theorem 11.4.
-/
theorem chewi114_gap_le_eps_of_quadratic_descent
    {gap : ℕ -> ℝ} {K eps : ℝ} {n0 M : ℕ}
    (hK : 0 < K) (hM : M ≠ 0)
    (hpos : ∀ m, m ≤ M -> 0 < gap (n0 + m))
    (hrec : ∀ m, m < M ->
      gap (n0 + (m + 1)) ≤
        gap (n0 + m) - gap (n0 + m) ^ (2 : ℕ) / K)
    (hK_div_le : K / (M : ℝ) ≤ eps) :
    gap (n0 + M) ≤ eps :=
  (chewi114_gap_le_K_div_iterations_of_quadratic_descent
    (gap := gap) (K := K) (n0 := n0) (M := M)
    hK hM hpos hrec).trans hK_div_le

/--
Chewi Theorem 11.4 scalar bridge from the source recurrence involving
`g' ^ 2` to the post-threshold recurrence involving `g ^ 2`.

Here `A = 2 * beta * D^2 * R^2` and `K = 4 * A`.
-/
theorem chewi114_quadratic_descent_of_next_gap_sq {A K g g' : ℝ}
    (hA : 0 < A) (hK_eq : K = 4 * A)
    (hg_nonneg : 0 ≤ g) (hhalf : g / 2 ≤ g')
    (hsource : g' - g ≤ -g' ^ (2 : ℕ) / A) :
    g' ≤ g - g ^ (2 : ℕ) / K := by
  have hg'_nonneg : 0 ≤ g' := by nlinarith
  have hsq_le : g ^ (2 : ℕ) ≤ (2 * g') ^ (2 : ℕ) :=
    (sq_le_sq₀ hg_nonneg (by nlinarith)).mpr (by nlinarith)
  have hsq4 : g ^ (2 : ℕ) ≤ 4 * g' ^ (2 : ℕ) := by
    nlinarith
  have hdiv : g ^ (2 : ℕ) / (4 * A) ≤ g' ^ (2 : ℕ) / A := by
    have h4A : 0 < 4 * A := by nlinarith
    rw [div_le_iff₀ h4A]
    field_simp [hA.ne']
    nlinarith
  have hsource' : g' ≤ g - g' ^ (2 : ℕ) / A := by
    calc
      g' = (g' - g) + g := by ring
      _ ≤ -g' ^ (2 : ℕ) / A + g := by
        simpa [add_comm, add_left_comm, add_assoc] using add_le_add_right hsource g
      _ = g - g' ^ (2 : ℕ) / A := by ring
  rw [hK_eq]
  exact hsource'.trans (sub_le_sub_left hdiv g)

/--
Sequence form of the threshold implication in Chewi Theorem 11.4.
-/
theorem chewi114_quadratic_descent_recurrence_of_source
    {gap : ℕ -> ℝ} {A K : ℝ} {n0 M : ℕ}
    (hA : 0 < A) (hK_eq : K = 4 * A)
    (hgap_nonneg : ∀ m, m ≤ M -> 0 ≤ gap (n0 + m))
    (hhalf : ∀ m, m < M -> gap (n0 + m) / 2 ≤ gap (n0 + (m + 1)))
    (hsource : ∀ m, m < M ->
      gap (n0 + (m + 1)) - gap (n0 + m) ≤
        -gap (n0 + (m + 1)) ^ (2 : ℕ) / A) :
    ∀ m, m < M ->
      gap (n0 + (m + 1)) ≤
        gap (n0 + m) - gap (n0 + m) ^ (2 : ℕ) / K := by
  intro m hm
  exact chewi114_quadratic_descent_of_next_gap_sq
    (A := A) (K := K) (g := gap (n0 + m))
    (g' := gap (n0 + (m + 1))) hA hK_eq
    (hgap_nonneg m (Nat.le_of_lt hm)) (hhalf m hm) (hsource m hm)

/--
Theorem 11.4 post-threshold rate directly from the source one-step recurrence
and the half-gap condition.
-/
theorem chewi114_gap_le_K_div_iterations_of_source_recurrence
    {gap : ℕ -> ℝ} {A K : ℝ} {n0 M : ℕ}
    (hA : 0 < A) (hK_eq : K = 4 * A) (hM : M ≠ 0)
    (hpos : ∀ m, m ≤ M -> 0 < gap (n0 + m))
    (hhalf : ∀ m, m < M -> gap (n0 + m) / 2 ≤ gap (n0 + (m + 1)))
    (hsource : ∀ m, m < M ->
      gap (n0 + (m + 1)) - gap (n0 + m) ≤
        -gap (n0 + (m + 1)) ^ (2 : ℕ) / A) :
    gap (n0 + M) ≤ K / (M : ℝ) := by
  have hK_pos : 0 < K := by
    rw [hK_eq]
    nlinarith
  have hrec :=
    chewi114_quadratic_descent_recurrence_of_source
      (gap := gap) (A := A) (K := K) (n0 := n0) (M := M)
      hA hK_eq (fun m hm => (hpos m hm).le) hhalf hsource
  exact chewi114_gap_le_K_div_iterations_of_quadratic_descent
    (gap := gap) (K := K) (n0 := n0) (M := M)
    hK_pos hM hpos hrec

/-- Source denominator `2 * beta * D^2 * R^2` in Chewi Theorem 11.4. -/
def chewi114A (beta : ℝ) (D : ℕ) (R : ℝ) : ℝ :=
  2 * beta * (D : ℝ) ^ (2 : ℕ) * R ^ (2 : ℕ)

/-- Source constant in the post-threshold recurrence of Chewi Theorem 11.4. -/
def chewi114K (beta : ℝ) (D : ℕ) (R : ℝ) : ℝ :=
  8 * beta * (D : ℝ) ^ (2 : ℕ) * R ^ (2 : ℕ)

/-- The source constants satisfy `K = 4 * A`. -/
theorem chewi114K_eq_four_chewi114A (beta : ℝ) (D : ℕ) (R : ℝ) :
    chewi114K beta D R = 4 * chewi114A beta D R := by
  simp [chewi114K, chewi114A]
  ring

/--
The source-shaped Theorem 11.4 post-threshold rate, using
`K = 8 * beta * D^2 * R^2`.
-/
theorem chewi114_gap_le_source_K_div_iterations
    {gap : ℕ -> ℝ} {beta R : ℝ} {D n0 M : ℕ}
    (hK : 0 < chewi114K beta D R) (hM : M ≠ 0)
    (hpos : ∀ m, m ≤ M -> 0 < gap (n0 + m))
    (hrec : ∀ m, m < M ->
      gap (n0 + (m + 1)) ≤
        gap (n0 + m) - gap (n0 + m) ^ (2 : ℕ) / chewi114K beta D R) :
    gap (n0 + M) ≤ chewi114K beta D R / (M : ℝ) :=
  chewi114_gap_le_K_div_iterations_of_quadratic_descent
    (gap := gap) (K := chewi114K beta D R) (n0 := n0) (M := M)
    hK hM hpos hrec

/--
Source-shaped post-threshold Theorem 11.4 rate from the displayed recurrence
with denominator `2 * beta * D^2 * R^2` plus the half-gap condition.
-/
theorem chewi114_gap_le_source_K_div_iterations_of_source_recurrence
    {gap : ℕ -> ℝ} {beta R : ℝ} {D n0 M : ℕ}
    (hA : 0 < chewi114A beta D R) (hM : M ≠ 0)
    (hpos : ∀ m, m ≤ M -> 0 < gap (n0 + m))
    (hhalf : ∀ m, m < M -> gap (n0 + m) / 2 ≤ gap (n0 + (m + 1)))
    (hsource : ∀ m, m < M ->
      gap (n0 + (m + 1)) - gap (n0 + m) ≤
        -gap (n0 + (m + 1)) ^ (2 : ℕ) / chewi114A beta D R) :
    gap (n0 + M) ≤ chewi114K beta D R / (M : ℝ) :=
  chewi114_gap_le_K_div_iterations_of_source_recurrence
    (gap := gap) (A := chewi114A beta D R) (K := chewi114K beta D R)
    (n0 := n0) (M := M) hA
    (chewi114K_eq_four_chewi114A beta D R) hM hpos hhalf hsource

/--
Epsilon form of the source-shaped post-threshold Theorem 11.4 rate.
-/
theorem chewi114_gap_le_eps_of_source_recurrence
    {gap : ℕ -> ℝ} {beta R eps : ℝ} {D n0 M : ℕ}
    (hA : 0 < chewi114A beta D R) (hM : M ≠ 0)
    (hpos : ∀ m, m ≤ M -> 0 < gap (n0 + m))
    (hhalf : ∀ m, m < M -> gap (n0 + m) / 2 ≤ gap (n0 + (m + 1)))
    (hsource : ∀ m, m < M ->
      gap (n0 + (m + 1)) - gap (n0 + m) ≤
        -gap (n0 + (m + 1)) ^ (2 : ℕ) / chewi114A beta D R)
    (hK_div_le : chewi114K beta D R / (M : ℝ) ≤ eps) :
    gap (n0 + M) ≤ eps :=
  (chewi114_gap_le_source_K_div_iterations_of_source_recurrence
    (gap := gap) (beta := beta) (R := R) (D := D)
    (n0 := n0) (M := M) hA hM hpos hhalf hsource).trans hK_div_le

/--
Chewi Theorem 11.4 one-step max recurrence from the displayed source
recurrence, without assuming in advance that the next gap is at least half of
the current gap.
-/
theorem chewi114_next_gap_le_max_halving_quadratic_of_source {A K g g' : ℝ}
    (hA : 0 < A) (hK_eq : K = 4 * A)
    (hg_nonneg : 0 ≤ g)
    (hsource : g' - g ≤ -g' ^ (2 : ℕ) / A) :
    g' ≤ max (g / 2) (g - g ^ (2 : ℕ) / K) := by
  by_cases hhalf : g / 2 ≤ g'
  · exact (chewi114_quadratic_descent_of_next_gap_sq
      (A := A) (K := K) (g := g) (g' := g') hA hK_eq hg_nonneg hhalf
      hsource).trans (le_max_right (g / 2) (g - g ^ (2 : ℕ) / K))
  · exact (le_of_lt (not_le.mp hhalf)).trans
      (le_max_left (g / 2) (g - g ^ (2 : ℕ) / K))

/--
Sequence form of the Chewi Theorem 11.4 one-step max recurrence.
-/
theorem chewi114_max_recurrence_of_source
    {gap : ℕ -> ℝ} {A K : ℝ} {n0 M : ℕ}
    (hA : 0 < A) (hK_eq : K = 4 * A)
    (hgap_nonneg : ∀ m, m ≤ M -> 0 ≤ gap (n0 + m))
    (hsource : ∀ m, m < M ->
      gap (n0 + (m + 1)) - gap (n0 + m) ≤
        -gap (n0 + (m + 1)) ^ (2 : ℕ) / A) :
    ∀ m, m < M ->
      gap (n0 + (m + 1)) ≤
        max (gap (n0 + m) / 2)
          (gap (n0 + m) - gap (n0 + m) ^ (2 : ℕ) / K) := by
  intro m hm
  exact chewi114_next_gap_le_max_halving_quadratic_of_source
    (A := A) (K := K) (g := gap (n0 + m))
    (g' := gap (n0 + (m + 1))) hA hK_eq
    (hgap_nonneg m (Nat.le_of_lt hm)) (hsource m hm)

/--
Source-shaped max recurrence for Chewi Theorem 11.4 with
`A = 2 * beta * D^2 * R^2` and `K = 8 * beta * D^2 * R^2`.
-/
theorem chewi114_source_max_recurrence_of_source
    {gap : ℕ -> ℝ} {beta R : ℝ} {D n0 M : ℕ}
    (hA : 0 < chewi114A beta D R)
    (hgap_nonneg : ∀ m, m ≤ M -> 0 ≤ gap (n0 + m))
    (hsource : ∀ m, m < M ->
      gap (n0 + (m + 1)) - gap (n0 + m) ≤
        -gap (n0 + (m + 1)) ^ (2 : ℕ) / chewi114A beta D R) :
    ∀ m, m < M ->
      gap (n0 + (m + 1)) ≤
        max (gap (n0 + m) / 2)
          (gap (n0 + m) - gap (n0 + m) ^ (2 : ℕ) / chewi114K beta D R) :=
  chewi114_max_recurrence_of_source
    (gap := gap) (A := chewi114A beta D R) (K := chewi114K beta D R)
    (n0 := n0) (M := M) hA (chewi114K_eq_four_chewi114A beta D R)
    hgap_nonneg hsource

/--
Above the source threshold `K / 2`, Chewi's max recurrence is necessarily in
the halving regime.
-/
theorem chewi114_halving_of_max_recurrence_above_threshold {K g g' : ℝ}
    (hK : 0 < K) (hg_nonneg : 0 ≤ g) (hthreshold : K / 2 ≤ g)
    (hmax : g' ≤ max (g / 2) (g - g ^ (2 : ℕ) / K)) :
    g' ≤ g / 2 := by
  have hmul : (K / 2) * g ≤ g * g :=
    mul_le_mul_of_nonneg_right hthreshold hg_nonneg
  have hsq_div : g / 2 ≤ g ^ (2 : ℕ) / K := by
    rw [le_div_iff₀ hK]
    nlinarith [hmul]
  have hquad_le_half : g - g ^ (2 : ℕ) / K ≤ g / 2 := by
    nlinarith
  exact hmax.trans (max_le le_rfl hquad_le_half)

/--
Source-recurrence form of the halving step above the threshold `K / 2`.
-/
theorem chewi114_halving_of_source_above_threshold {A K g g' : ℝ}
    (hA : 0 < A) (hK_eq : K = 4 * A)
    (hg_nonneg : 0 ≤ g) (hthreshold : K / 2 ≤ g)
    (hsource : g' - g ≤ -g' ^ (2 : ℕ) / A) :
    g' ≤ g / 2 := by
  have hK_pos : 0 < K := by
    rw [hK_eq]
    nlinarith
  exact chewi114_halving_of_max_recurrence_above_threshold
    (K := K) (g := g) (g' := g') hK_pos hg_nonneg hthreshold
    (chewi114_next_gap_le_max_halving_quadratic_of_source
      (A := A) (K := K) (g := g) (g' := g') hA hK_eq hg_nonneg hsource)

/--
A finite consecutive halving phase gives the expected geometric upper bound.
-/
theorem chewi114_gap_le_half_pow_mul_of_halving
    {gap : ℕ -> ℝ} {n0 M : ℕ}
    (hhalve : ∀ m, m < M -> gap (n0 + (m + 1)) ≤ gap (n0 + m) / 2) :
    gap (n0 + M) ≤ (1 / 2 : ℝ) ^ M * gap n0 := by
  induction M with
  | zero =>
      simp
  | succ M ih =>
      have hprev :
          gap (n0 + M) ≤ (1 / 2 : ℝ) ^ M * gap n0 :=
        ih (fun m hm => hhalve m (Nat.lt_trans hm (Nat.lt_succ_self M)))
      have hstep : gap (n0 + (M + 1)) ≤ gap (n0 + M) / 2 :=
        hhalve M (Nat.lt_succ_self M)
      calc
        gap (n0 + (M + 1)) ≤ gap (n0 + M) / 2 := hstep
        _ ≤ ((1 / 2 : ℝ) ^ M * gap n0) / 2 := by nlinarith
        _ = (1 / 2 : ℝ) ^ (M + 1) * gap n0 := by ring

/--
Source-shaped halving step above Chewi's threshold
`chewi114K beta D R / 2 = 4 * beta * D^2 * R^2`.
-/
theorem chewi114_source_halving_above_threshold
    {gap : ℕ -> ℝ} {beta R : ℝ} {D n : ℕ}
    (hA : 0 < chewi114A beta D R)
    (hgap_nonneg : 0 ≤ gap n)
    (hthreshold : chewi114K beta D R / 2 ≤ gap n)
    (hsource :
      gap (n + 1) - gap n ≤
        -gap (n + 1) ^ (2 : ℕ) / chewi114A beta D R) :
    gap (n + 1) ≤ gap n / 2 :=
  chewi114_halving_of_source_above_threshold
    (A := chewi114A beta D R) (K := chewi114K beta D R)
    (g := gap n) (g' := gap (n + 1)) hA
    (chewi114K_eq_four_chewi114A beta D R) hgap_nonneg hthreshold hsource

/--
Below the source threshold `K / 2`, Chewi's max recurrence is necessarily in
the quadratic-descent regime.
-/
theorem chewi114_quadratic_of_max_recurrence_below_threshold {K g g' : ℝ}
    (hK : 0 < K) (hg_nonneg : 0 ≤ g) (hthreshold : g ≤ K / 2)
    (hmax : g' ≤ max (g / 2) (g - g ^ (2 : ℕ) / K)) :
    g' ≤ g - g ^ (2 : ℕ) / K := by
  have hmul : g * g ≤ (K / 2) * g :=
    mul_le_mul_of_nonneg_right hthreshold hg_nonneg
  have hsq_div : g ^ (2 : ℕ) / K ≤ g / 2 := by
    rw [div_le_iff₀ hK]
    nlinarith [hmul]
  have hhalf_le_quad : g / 2 ≤ g - g ^ (2 : ℕ) / K := by
    nlinarith
  exact hmax.trans (max_le hhalf_le_quad le_rfl)

/--
Source-recurrence form of the quadratic step below the threshold `K / 2`.
-/
theorem chewi114_quadratic_of_source_below_threshold {A K g g' : ℝ}
    (hA : 0 < A) (hK_eq : K = 4 * A)
    (hg_nonneg : 0 ≤ g) (hthreshold : g ≤ K / 2)
    (hsource : g' - g ≤ -g' ^ (2 : ℕ) / A) :
    g' ≤ g - g ^ (2 : ℕ) / K := by
  have hK_pos : 0 < K := by
    rw [hK_eq]
    nlinarith
  exact chewi114_quadratic_of_max_recurrence_below_threshold
    (K := K) (g := g) (g' := g') hK_pos hg_nonneg hthreshold
    (chewi114_next_gap_le_max_halving_quadratic_of_source
      (A := A) (K := K) (g := g) (g' := g') hA hK_eq hg_nonneg hsource)

/--
The scalar bridge from Chewi's two block-coordinate estimates to the displayed
source recurrence.  Here `energy` denotes the sum of squared gradient
increments in the proof, and `C = D^2 R^2`.
-/
theorem chewi114_source_recurrence_of_descent_energy {beta C g g' energy : ℝ}
    (hbeta : 0 < beta) (hC : 0 < C)
    (hdescent : energy / (2 * beta) ≤ g - g')
    (hgap_sq : g' ^ (2 : ℕ) ≤ C * energy) :
    g' - g ≤ -g' ^ (2 : ℕ) / (2 * beta * C) := by
  have hden : 0 < 2 * beta * C := by positivity
  have hdiv : g' ^ (2 : ℕ) / (2 * beta * C) ≤ energy / (2 * beta) := by
    rw [div_le_iff₀ hden]
    field_simp [hbeta.ne']
    nlinarith [hgap_sq]
  have hdrop : g' - g ≤ -energy / (2 * beta) := by
    calc
      g' - g = -(g - g') := by ring
      _ ≤ -(energy / (2 * beta)) := neg_le_neg hdescent
      _ = -energy / (2 * beta) := by ring
  have hneg_div : -energy / (2 * beta) ≤ -g' ^ (2 : ℕ) / (2 * beta * C) := by
    calc
      -energy / (2 * beta) = -(energy / (2 * beta)) := by ring
      _ ≤ -(g' ^ (2 : ℕ) / (2 * beta * C)) := neg_le_neg hdiv
      _ = -g' ^ (2 : ℕ) / (2 * beta * C) := by ring
  exact hdrop.trans hneg_div

/--
Algorithm-facing source certificate for the one-dimensional gap sequence
obtained from Chewi's AM proof after the block-coordinate descent estimate.
The fields are exactly the nonnegativity of the objective gap and the displayed
source recurrence before the burn-in split.
-/
structure IsChewi114AMSourceCertificate
    (gap : ℕ -> ℝ) (beta R : ℝ) (D : ℕ) : Prop where
  gap_nonneg : ∀ n, 0 ≤ gap n
  source_recurrence : ∀ n,
    gap (n + 1) - gap n ≤
      -gap (n + 1) ^ (2 : ℕ) / chewi114A beta D R

/--
Algorithm-facing descent certificate matching the two quantitative inequalities
in Chewi's proof of Theorem 11.4: the AM descent lemma and the comparison of
the next gap to the accumulated coordinate-gradient increments.
-/
structure IsChewi114AMDescentCertificate
    (gap energy : ℕ -> ℝ) (beta R : ℝ) (D : ℕ) : Prop where
  gap_nonneg : ∀ n, 0 ≤ gap n
  descent_energy : ∀ n, energy n / (2 * beta) ≤ gap n - gap (n + 1)
  gap_sq_le_energy : ∀ n,
    gap (n + 1) ^ (2 : ℕ) ≤ ((D : ℝ) ^ (2 : ℕ) * R ^ (2 : ℕ)) * energy n

/--
The two block-coordinate descent estimates supply the source recurrence
certificate used by the scalar Theorem 11.4 layer.
-/
theorem IsChewi114AMDescentCertificate.sourceCertificate
    {gap energy : ℕ -> ℝ} {beta R : ℝ} {D : ℕ}
    (hcert : IsChewi114AMDescentCertificate gap energy beta R D)
    (hbeta : 0 < beta) (hscale : 0 < (D : ℝ) ^ (2 : ℕ) * R ^ (2 : ℕ)) :
    IsChewi114AMSourceCertificate gap beta R D := by
  refine ⟨hcert.gap_nonneg, ?_⟩
  intro n
  have hrec := chewi114_source_recurrence_of_descent_energy
    (beta := beta) (C := (D : ℝ) ^ (2 : ℕ) * R ^ (2 : ℕ))
    (g := gap n) (g' := gap (n + 1)) (energy := energy n)
    hbeta hscale (hcert.descent_energy n) (hcert.gap_sq_le_energy n)
  simpa [chewi114A, mul_assoc] using hrec

/--
The block-coordinate descent certificate supplies Chewi's one-step max
recurrence.
-/
theorem IsChewi114AMDescentCertificate.max_recurrence
    {gap energy : ℕ -> ℝ} {beta R : ℝ} {D : ℕ}
    (hcert : IsChewi114AMDescentCertificate gap energy beta R D)
    (hbeta : 0 < beta) (hscale : 0 < (D : ℝ) ^ (2 : ℕ) * R ^ (2 : ℕ))
    (n : ℕ) :
    gap (n + 1) ≤
      max (gap n / 2) (gap n - gap n ^ (2 : ℕ) / chewi114K beta D R) := by
  have hsource := hcert.sourceCertificate hbeta hscale
  have hA : 0 < chewi114A beta D R := by
    have hprod : 0 < (2 * beta) * ((D : ℝ) ^ (2 : ℕ) * R ^ (2 : ℕ)) :=
      mul_pos (by positivity) hscale
    simpa [chewi114A, mul_assoc] using hprod
  exact chewi114_next_gap_le_max_halving_quadratic_of_source
    (A := chewi114A beta D R) (K := chewi114K beta D R)
    (g := gap n) (g' := gap (n + 1)) hA
    (chewi114K_eq_four_chewi114A beta D R) (hsource.gap_nonneg n)
    (hsource.source_recurrence n)

/--
The block-coordinate descent certificate supplies the tail `K/M` rate once the
post-threshold half-gap condition is known.
-/
theorem IsChewi114AMDescentCertificate.gap_le_source_K_div_iterations_of_tail_half
    {gap energy : ℕ -> ℝ} {beta R : ℝ} {D n0 M : ℕ}
    (hcert : IsChewi114AMDescentCertificate gap energy beta R D)
    (hbeta : 0 < beta) (hscale : 0 < (D : ℝ) ^ (2 : ℕ) * R ^ (2 : ℕ))
    (hM : M ≠ 0)
    (hpos : ∀ m, m ≤ M -> 0 < gap (n0 + m))
    (hhalf : ∀ m, m < M -> gap (n0 + m) / 2 ≤ gap (n0 + (m + 1))) :
    gap (n0 + M) ≤ chewi114K beta D R / (M : ℝ) := by
  have hsource := hcert.sourceCertificate hbeta hscale
  have hA : 0 < chewi114A beta D R := by
    have hprod : 0 < (2 * beta) * ((D : ℝ) ^ (2 : ℕ) * R ^ (2 : ℕ)) :=
      mul_pos (by positivity) hscale
    simpa [chewi114A, mul_assoc] using hprod
  exact chewi114_gap_le_source_K_div_iterations_of_source_recurrence
    (gap := gap) (beta := beta) (R := R) (D := D)
    (n0 := n0) (M := M) hA hM hpos hhalf
    (fun m _hm => hsource.source_recurrence (n0 + m))

/--
Epsilon form of the block-coordinate descent-certificate tail rate.
-/
theorem IsChewi114AMDescentCertificate.gap_le_eps_of_tail_half
    {gap energy : ℕ -> ℝ} {beta R eps : ℝ} {D n0 M : ℕ}
    (hcert : IsChewi114AMDescentCertificate gap energy beta R D)
    (hbeta : 0 < beta) (hscale : 0 < (D : ℝ) ^ (2 : ℕ) * R ^ (2 : ℕ))
    (hM : M ≠ 0)
    (hpos : ∀ m, m ≤ M -> 0 < gap (n0 + m))
    (hhalf : ∀ m, m < M -> gap (n0 + m) / 2 ≤ gap (n0 + (m + 1)))
    (hK_div_le : chewi114K beta D R / (M : ℝ) ≤ eps) :
    gap (n0 + M) ≤ eps :=
  (hcert.gap_le_source_K_div_iterations_of_tail_half
    hbeta hscale hM hpos hhalf).trans hK_div_le

/--
The block-coordinate descent certificate gives the quadratic recurrence
whenever the current gap is below the source burn-in threshold.
-/
theorem IsChewi114AMDescentCertificate.quadratic_recurrence_below_threshold
    {gap energy : ℕ -> ℝ} {beta R : ℝ} {D : ℕ}
    (hcert : IsChewi114AMDescentCertificate gap energy beta R D)
    (hbeta : 0 < beta) (hscale : 0 < (D : ℝ) ^ (2 : ℕ) * R ^ (2 : ℕ))
    {n : ℕ} (hthreshold : gap n ≤ chewi114K beta D R / 2) :
    gap (n + 1) ≤ gap n - gap n ^ (2 : ℕ) / chewi114K beta D R := by
  have hsource := hcert.sourceCertificate hbeta hscale
  have hA : 0 < chewi114A beta D R := by
    have hprod : 0 < (2 * beta) * ((D : ℝ) ^ (2 : ℕ) * R ^ (2 : ℕ)) :=
      mul_pos (by positivity) hscale
    simpa [chewi114A, mul_assoc] using hprod
  exact chewi114_quadratic_of_source_below_threshold
    (A := chewi114A beta D R) (K := chewi114K beta D R)
    (g := gap n) (g' := gap (n + 1)) hA
    (chewi114K_eq_four_chewi114A beta D R) (hsource.gap_nonneg n)
    hthreshold (hsource.source_recurrence n)

/--
The block-coordinate descent certificate supplies the post-threshold `K / M`
rate on any tail segment where the current gaps stay below `K / 2`.
-/
theorem IsChewi114AMDescentCertificate.gap_le_source_K_div_iterations_of_threshold_tail
    {gap energy : ℕ -> ℝ} {beta R : ℝ} {D n0 M : ℕ}
    (hcert : IsChewi114AMDescentCertificate gap energy beta R D)
    (hbeta : 0 < beta) (hscale : 0 < (D : ℝ) ^ (2 : ℕ) * R ^ (2 : ℕ))
    (hM : M ≠ 0)
    (hpos : ∀ m, m ≤ M -> 0 < gap (n0 + m))
    (hthreshold : ∀ m, m < M -> gap (n0 + m) ≤ chewi114K beta D R / 2) :
    gap (n0 + M) ≤ chewi114K beta D R / (M : ℝ) := by
  have hsource := hcert.sourceCertificate hbeta hscale
  have hA : 0 < chewi114A beta D R := by
    have hprod : 0 < (2 * beta) * ((D : ℝ) ^ (2 : ℕ) * R ^ (2 : ℕ)) :=
      mul_pos (by positivity) hscale
    simpa [chewi114A, mul_assoc] using hprod
  have hK_pos : 0 < chewi114K beta D R := by
    rw [chewi114K_eq_four_chewi114A beta D R]
    nlinarith
  exact chewi114_gap_le_source_K_div_iterations
    (gap := gap) (beta := beta) (R := R) (D := D)
    (n0 := n0) (M := M) hK_pos hM hpos
    (fun m hm => by
      simpa [Nat.add_assoc] using
        hcert.quadratic_recurrence_below_threshold
          hbeta hscale (n := n0 + m) (hthreshold m hm))

/--
Epsilon form of the threshold-tail block-coordinate descent-certificate rate.
-/
theorem IsChewi114AMDescentCertificate.gap_le_eps_of_threshold_tail
    {gap energy : ℕ -> ℝ} {beta R eps : ℝ} {D n0 M : ℕ}
    (hcert : IsChewi114AMDescentCertificate gap energy beta R D)
    (hbeta : 0 < beta) (hscale : 0 < (D : ℝ) ^ (2 : ℕ) * R ^ (2 : ℕ))
    (hM : M ≠ 0)
    (hpos : ∀ m, m ≤ M -> 0 < gap (n0 + m))
    (hthreshold : ∀ m, m < M -> gap (n0 + m) ≤ chewi114K beta D R / 2)
    (hK_div_le : chewi114K beta D R / (M : ℝ) ≤ eps) :
    gap (n0 + M) ≤ eps :=
  (hcert.gap_le_source_K_div_iterations_of_threshold_tail
    hbeta hscale hM hpos hthreshold).trans hK_div_le

/--
The AM source certificate supplies Chewi's one-step max recurrence at every
iteration.
-/
theorem IsChewi114AMSourceCertificate.max_recurrence
    {gap : ℕ -> ℝ} {beta R : ℝ} {D : ℕ}
    (hcert : IsChewi114AMSourceCertificate gap beta R D)
    (hA : 0 < chewi114A beta D R) (n : ℕ) :
    gap (n + 1) ≤
      max (gap n / 2) (gap n - gap n ^ (2 : ℕ) / chewi114K beta D R) :=
  chewi114_next_gap_le_max_halving_quadratic_of_source
    (A := chewi114A beta D R) (K := chewi114K beta D R)
    (g := gap n) (g' := gap (n + 1)) hA
    (chewi114K_eq_four_chewi114A beta D R) (hcert.gap_nonneg n)
    (hcert.source_recurrence n)

/--
The AM source certificate gives the quadratic recurrence whenever the current
gap is below the source burn-in threshold.
-/
theorem IsChewi114AMSourceCertificate.quadratic_recurrence_below_threshold
    {gap : ℕ -> ℝ} {beta R : ℝ} {D : ℕ}
    (hcert : IsChewi114AMSourceCertificate gap beta R D)
    (hA : 0 < chewi114A beta D R) {n : ℕ}
    (hthreshold : gap n ≤ chewi114K beta D R / 2) :
    gap (n + 1) ≤ gap n - gap n ^ (2 : ℕ) / chewi114K beta D R :=
  chewi114_quadratic_of_source_below_threshold
    (A := chewi114A beta D R) (K := chewi114K beta D R)
    (g := gap n) (g' := gap (n + 1)) hA
    (chewi114K_eq_four_chewi114A beta D R) (hcert.gap_nonneg n)
    hthreshold (hcert.source_recurrence n)

/--
The AM source certificate gives a halving step whenever the current gap is
above the source burn-in threshold.
-/
theorem IsChewi114AMSourceCertificate.halving_above_threshold
    {gap : ℕ -> ℝ} {beta R : ℝ} {D : ℕ}
    (hcert : IsChewi114AMSourceCertificate gap beta R D)
    (hA : 0 < chewi114A beta D R) {n : ℕ}
    (hthreshold : chewi114K beta D R / 2 ≤ gap n) :
    gap (n + 1) ≤ gap n / 2 :=
  chewi114_source_halving_above_threshold
    (gap := gap) (beta := beta) (R := R) (D := D) (n := n)
    hA (hcert.gap_nonneg n) hthreshold (hcert.source_recurrence n)

/--
If a whole finite prefix stays above the burn-in threshold, the AM source
certificate gives geometric halving across that prefix.
-/
theorem IsChewi114AMSourceCertificate.gap_le_half_pow_mul_of_threshold_phase
    {gap : ℕ -> ℝ} {beta R : ℝ} {D n0 M : ℕ}
    (hcert : IsChewi114AMSourceCertificate gap beta R D)
    (hA : 0 < chewi114A beta D R)
    (hthreshold : ∀ m, m < M -> chewi114K beta D R / 2 ≤ gap (n0 + m)) :
    gap (n0 + M) ≤ (1 / 2 : ℝ) ^ M * gap n0 :=
  chewi114_gap_le_half_pow_mul_of_halving
    (gap := gap) (n0 := n0) (M := M)
    (fun m hm => by
      simpa [Nat.add_assoc] using
        hcert.halving_above_threshold hA (n := n0 + m) (hthreshold m hm))

/--
Burn-in consumer for Chewi Theorem 11.4: a finite above-threshold phase reaches
the threshold once the corresponding geometric upper bound is below it.
-/
theorem IsChewi114AMSourceCertificate.gap_le_threshold_of_geometric_burnin
    {gap : ℕ -> ℝ} {beta R : ℝ} {D n0 M : ℕ}
    (hcert : IsChewi114AMSourceCertificate gap beta R D)
    (hA : 0 < chewi114A beta D R)
    (hthreshold : ∀ m, m < M -> chewi114K beta D R / 2 ≤ gap (n0 + m))
    (hpow_le :
      (1 / 2 : ℝ) ^ M * gap n0 ≤ chewi114K beta D R / 2) :
    gap (n0 + M) ≤ chewi114K beta D R / 2 :=
  (hcert.gap_le_half_pow_mul_of_threshold_phase hA hthreshold).trans hpow_le

/--
Existence form of Chewi's burn-in phase: if the geometric halving envelope is
below the threshold by time `M`, then some iterate no later than `M` is already
below the threshold.
-/
theorem IsChewi114AMSourceCertificate.exists_threshold_index_of_geometric_burnin
    {gap : ℕ -> ℝ} {beta R : ℝ} {D n0 M : ℕ}
    (hcert : IsChewi114AMSourceCertificate gap beta R D)
    (hA : 0 < chewi114A beta D R)
    (hpow_le :
      (1 / 2 : ℝ) ^ M * gap n0 ≤ chewi114K beta D R / 2) :
    ∃ m, m ≤ M ∧ gap (n0 + m) ≤ chewi114K beta D R / 2 := by
  classical
  by_cases hex : ∃ m, m ≤ M ∧ gap (n0 + m) ≤ chewi114K beta D R / 2
  · exact hex
  · have hthreshold :
        ∀ m, m < M -> chewi114K beta D R / 2 ≤ gap (n0 + m) := by
      intro m hm
      have hnot : ¬ gap (n0 + m) ≤ chewi114K beta D R / 2 := by
        intro hle
        exact hex ⟨m, Nat.le_of_lt hm, hle⟩
      exact (not_le.mp hnot).le
    have hM :
        gap (n0 + M) ≤ chewi114K beta D R / 2 :=
      hcert.gap_le_threshold_of_geometric_burnin hA hthreshold hpow_le
    exact False.elim (hex ⟨M, le_rfl, hM⟩)

/--
The AM source certificate supplies the post-threshold `K / M` rate once the
half-gap condition holds on a tail segment.
-/
theorem IsChewi114AMSourceCertificate.gap_le_source_K_div_iterations_of_tail_half
    {gap : ℕ -> ℝ} {beta R : ℝ} {D n0 M : ℕ}
    (hcert : IsChewi114AMSourceCertificate gap beta R D)
    (hA : 0 < chewi114A beta D R) (hM : M ≠ 0)
    (hpos : ∀ m, m ≤ M -> 0 < gap (n0 + m))
    (hhalf : ∀ m, m < M -> gap (n0 + m) / 2 ≤ gap (n0 + (m + 1))) :
    gap (n0 + M) ≤ chewi114K beta D R / (M : ℝ) :=
  chewi114_gap_le_source_K_div_iterations_of_source_recurrence
    (gap := gap) (beta := beta) (R := R) (D := D)
    (n0 := n0) (M := M) hA hM hpos hhalf
    (fun m _hm => hcert.source_recurrence (n0 + m))

/--
Epsilon form of the AM source-certificate tail rate.
-/
theorem IsChewi114AMSourceCertificate.gap_le_eps_of_tail_half
    {gap : ℕ -> ℝ} {beta R eps : ℝ} {D n0 M : ℕ}
    (hcert : IsChewi114AMSourceCertificate gap beta R D)
    (hA : 0 < chewi114A beta D R) (hM : M ≠ 0)
    (hpos : ∀ m, m ≤ M -> 0 < gap (n0 + m))
    (hhalf : ∀ m, m < M -> gap (n0 + m) / 2 ≤ gap (n0 + (m + 1)))
    (hK_div_le : chewi114K beta D R / (M : ℝ) ≤ eps) :
    gap (n0 + M) ≤ eps :=
  (hcert.gap_le_source_K_div_iterations_of_tail_half
    hA hM hpos hhalf).trans hK_div_le

/--
The AM source certificate supplies the post-threshold `K / M` rate on any tail
segment where the current gaps stay below `K / 2`.
-/
theorem IsChewi114AMSourceCertificate.gap_le_source_K_div_iterations_of_threshold_tail
    {gap : ℕ -> ℝ} {beta R : ℝ} {D n0 M : ℕ}
    (hcert : IsChewi114AMSourceCertificate gap beta R D)
    (hA : 0 < chewi114A beta D R) (hM : M ≠ 0)
    (hpos : ∀ m, m ≤ M -> 0 < gap (n0 + m))
    (hthreshold : ∀ m, m < M -> gap (n0 + m) ≤ chewi114K beta D R / 2) :
    gap (n0 + M) ≤ chewi114K beta D R / (M : ℝ) := by
  have hK_pos : 0 < chewi114K beta D R := by
    rw [chewi114K_eq_four_chewi114A beta D R]
    nlinarith
  exact chewi114_gap_le_source_K_div_iterations
    (gap := gap) (beta := beta) (R := R) (D := D)
    (n0 := n0) (M := M) hK_pos hM hpos
    (fun m hm => by
      simpa [Nat.add_assoc] using
        hcert.quadratic_recurrence_below_threshold hA
          (n := n0 + m) (hthreshold m hm))

/--
Epsilon form of the threshold-tail AM source-certificate rate.
-/
theorem IsChewi114AMSourceCertificate.gap_le_eps_of_threshold_tail
    {gap : ℕ -> ℝ} {beta R eps : ℝ} {D n0 M : ℕ}
    (hcert : IsChewi114AMSourceCertificate gap beta R D)
    (hA : 0 < chewi114A beta D R) (hM : M ≠ 0)
    (hpos : ∀ m, m ≤ M -> 0 < gap (n0 + m))
    (hthreshold : ∀ m, m < M -> gap (n0 + m) ≤ chewi114K beta D R / 2)
    (hK_div_le : chewi114K beta D R / (M : ℝ) ≤ eps) :
    gap (n0 + M) ≤ eps :=
  (hcert.gap_le_source_K_div_iterations_of_threshold_tail
    hA hM hpos hthreshold).trans hK_div_le

/--
Once the AM source-certificate gap enters the threshold region `gap <= K / 2`,
all later gaps in a finite tail remain in that region.
-/
theorem IsChewi114AMSourceCertificate.threshold_tail_of_initial_threshold
    {gap : ℕ -> ℝ} {beta R : ℝ} {D n0 M : ℕ}
    (hcert : IsChewi114AMSourceCertificate gap beta R D)
    (hA : 0 < chewi114A beta D R)
    (hinit : gap n0 ≤ chewi114K beta D R / 2) :
    ∀ m, m ≤ M -> gap (n0 + m) ≤ chewi114K beta D R / 2 := by
  have hK_pos : 0 < chewi114K beta D R := by
    rw [chewi114K_eq_four_chewi114A beta D R]
    nlinarith
  intro m hm
  induction m with
  | zero =>
      simpa using hinit
  | succ m ih =>
      have hm_lt : m < M := Nat.lt_of_succ_le hm
      have hprev : gap (n0 + m) ≤ chewi114K beta D R / 2 :=
        ih (Nat.le_of_lt hm_lt)
      have hrec :
          gap (n0 + (m + 1)) ≤
            gap (n0 + m) - gap (n0 + m) ^ (2 : ℕ) / chewi114K beta D R := by
        simpa [Nat.add_assoc] using
          hcert.quadratic_recurrence_below_threshold
            hA (n := n0 + m) hprev
      have hnonneg : 0 ≤ gap (n0 + m) ^ (2 : ℕ) / chewi114K beta D R :=
        div_nonneg (sq_nonneg _) hK_pos.le
      have hstep_le : gap (n0 + (m + 1)) ≤ gap (n0 + m) := by
        nlinarith
      exact hstep_le.trans hprev

/--
Post-threshold `K/M` rate from a single initial threshold certificate.
-/
theorem IsChewi114AMSourceCertificate.gap_le_source_K_div_iterations_of_initial_threshold
    {gap : ℕ -> ℝ} {beta R : ℝ} {D n0 M : ℕ}
    (hcert : IsChewi114AMSourceCertificate gap beta R D)
    (hA : 0 < chewi114A beta D R) (hM : M ≠ 0)
    (hpos : ∀ m, m ≤ M -> 0 < gap (n0 + m))
    (hinit : gap n0 ≤ chewi114K beta D R / 2) :
    gap (n0 + M) ≤ chewi114K beta D R / (M : ℝ) :=
  hcert.gap_le_source_K_div_iterations_of_threshold_tail
    hA hM hpos
    (fun m hm => hcert.threshold_tail_of_initial_threshold
      hA hinit m (Nat.le_of_lt hm))

/--
Epsilon form of the initial-threshold AM source-certificate rate.
-/
theorem IsChewi114AMSourceCertificate.gap_le_eps_of_initial_threshold
    {gap : ℕ -> ℝ} {beta R eps : ℝ} {D n0 M : ℕ}
    (hcert : IsChewi114AMSourceCertificate gap beta R D)
    (hA : 0 < chewi114A beta D R) (hM : M ≠ 0)
    (hpos : ∀ m, m ≤ M -> 0 < gap (n0 + m))
    (hinit : gap n0 ≤ chewi114K beta D R / 2)
    (hK_div_le : chewi114K beta D R / (M : ℝ) ≤ eps) :
    gap (n0 + M) ≤ eps :=
  (hcert.gap_le_source_K_div_iterations_of_initial_threshold
    hA hM hpos hinit).trans hK_div_le

/--
Burn-in plus tail epsilon endpoint: if the geometric envelope enters the
threshold region by time `B`, then some burn-in index `b <= B` starts a tail
whose endpoint is `eps`-accurate.
-/
theorem IsChewi114AMSourceCertificate.exists_tail_gap_le_eps_of_geometric_burnin
    {gap : ℕ -> ℝ} {beta R eps : ℝ} {D n0 B M : ℕ}
    (hcert : IsChewi114AMSourceCertificate gap beta R D)
    (hA : 0 < chewi114A beta D R) (hM : M ≠ 0)
    (hpow_le :
      (1 / 2 : ℝ) ^ B * gap n0 ≤ chewi114K beta D R / 2)
    (hpos : ∀ b, b ≤ B -> gap (n0 + b) ≤ chewi114K beta D R / 2 ->
      ∀ m, m ≤ M -> 0 < gap ((n0 + b) + m))
    (hK_div_le : chewi114K beta D R / (M : ℝ) ≤ eps) :
    ∃ b, b ≤ B ∧ gap ((n0 + b) + M) ≤ eps := by
  rcases hcert.exists_threshold_index_of_geometric_burnin
    hA hpow_le with ⟨b, hb, hinit⟩
  refine ⟨b, hb, ?_⟩
  exact hcert.gap_le_eps_of_initial_threshold
    (n0 := n0 + b) (M := M) hA hM (hpos b hb hinit) hinit hK_div_le

/--
Logarithmic sufficient condition for Chewi 11.4's geometric burn-in envelope.
This reuses the Chapter 5 scalar halving/log calculation.
-/
theorem chewi114_half_pow_mul_gap_le_threshold_of_log
    {gap0 K : ℝ} {B : ℕ}
    (hgap0_pos : 0 < gap0) (hK : 0 < K)
    (hB_log : Real.log (gap0 / (K / 2)) ≤ (B : ℝ) * Real.log (2 : ℝ)) :
    (1 / 2 : ℝ) ^ B * gap0 ≤ K / 2 :=
  chewi54_half_pow_mul_le_eps_of_log_ratio_le
    hgap0_pos (half_pos hK) hB_log

/--
Logarithmic burn-in existence for the AM source certificate.
-/
theorem IsChewi114AMSourceCertificate.exists_threshold_index_of_log_burnin
    {gap : ℕ -> ℝ} {beta R : ℝ} {D n0 B : ℕ}
    (hcert : IsChewi114AMSourceCertificate gap beta R D)
    (hA : 0 < chewi114A beta D R)
    (hgap0_pos : 0 < gap n0)
    (hB_log :
      Real.log (gap n0 / (chewi114K beta D R / 2)) ≤
        (B : ℝ) * Real.log (2 : ℝ)) :
    ∃ b, b ≤ B ∧ gap (n0 + b) ≤ chewi114K beta D R / 2 := by
  have hK_pos : 0 < chewi114K beta D R := by
    rw [chewi114K_eq_four_chewi114A beta D R]
    nlinarith
  exact hcert.exists_threshold_index_of_geometric_burnin hA
    (chewi114_half_pow_mul_gap_le_threshold_of_log
      (gap0 := gap n0) (K := chewi114K beta D R) (B := B)
      hgap0_pos hK_pos hB_log)

/--
Logarithmic burn-in plus tail epsilon endpoint for the AM source certificate.
-/
theorem IsChewi114AMSourceCertificate.exists_tail_gap_le_eps_of_log_burnin
    {gap : ℕ -> ℝ} {beta R eps : ℝ} {D n0 B M : ℕ}
    (hcert : IsChewi114AMSourceCertificate gap beta R D)
    (hA : 0 < chewi114A beta D R) (hM : M ≠ 0)
    (hgap0_pos : 0 < gap n0)
    (hB_log :
      Real.log (gap n0 / (chewi114K beta D R / 2)) ≤
        (B : ℝ) * Real.log (2 : ℝ))
    (hpos : ∀ b, b ≤ B -> gap (n0 + b) ≤ chewi114K beta D R / 2 ->
      ∀ m, m ≤ M -> 0 < gap ((n0 + b) + m))
    (hK_div_le : chewi114K beta D R / (M : ℝ) ≤ eps) :
    ∃ b, b ≤ B ∧ gap ((n0 + b) + M) ≤ eps := by
  have hK_pos : 0 < chewi114K beta D R := by
    rw [chewi114K_eq_four_chewi114A beta D R]
    nlinarith
  exact hcert.exists_tail_gap_le_eps_of_geometric_burnin
    hA hM
    (chewi114_half_pow_mul_gap_le_threshold_of_log
      (gap0 := gap n0) (K := chewi114K beta D R) (B := B)
      hgap0_pos hK_pos hB_log)
    hpos hK_div_le

/--
Post-threshold `K/M` rate from a block-coordinate descent certificate and a
single initial threshold certificate.
-/
theorem IsChewi114AMDescentCertificate.gap_le_source_K_div_iterations_of_initial_threshold
    {gap energy : ℕ -> ℝ} {beta R : ℝ} {D n0 M : ℕ}
    (hcert : IsChewi114AMDescentCertificate gap energy beta R D)
    (hbeta : 0 < beta) (hscale : 0 < (D : ℝ) ^ (2 : ℕ) * R ^ (2 : ℕ))
    (hM : M ≠ 0)
    (hpos : ∀ m, m ≤ M -> 0 < gap (n0 + m))
    (hinit : gap n0 ≤ chewi114K beta D R / 2) :
    gap (n0 + M) ≤ chewi114K beta D R / (M : ℝ) := by
  have hsource := hcert.sourceCertificate hbeta hscale
  have hA : 0 < chewi114A beta D R := by
    have hprod : 0 < (2 * beta) * ((D : ℝ) ^ (2 : ℕ) * R ^ (2 : ℕ)) :=
      mul_pos (by positivity) hscale
    simpa [chewi114A, mul_assoc] using hprod
  exact hsource.gap_le_source_K_div_iterations_of_initial_threshold
    hA hM hpos hinit

/--
Epsilon form of the initial-threshold block-coordinate descent-certificate
rate.
-/
theorem IsChewi114AMDescentCertificate.gap_le_eps_of_initial_threshold
    {gap energy : ℕ -> ℝ} {beta R eps : ℝ} {D n0 M : ℕ}
    (hcert : IsChewi114AMDescentCertificate gap energy beta R D)
    (hbeta : 0 < beta) (hscale : 0 < (D : ℝ) ^ (2 : ℕ) * R ^ (2 : ℕ))
    (hM : M ≠ 0)
    (hpos : ∀ m, m ≤ M -> 0 < gap (n0 + m))
    (hinit : gap n0 ≤ chewi114K beta D R / 2)
    (hK_div_le : chewi114K beta D R / (M : ℝ) ≤ eps) :
    gap (n0 + M) ≤ eps :=
  (hcert.gap_le_source_K_div_iterations_of_initial_threshold
    hbeta hscale hM hpos hinit).trans hK_div_le

/--
Existence form of the burn-in phase from a block-coordinate descent
certificate.
-/
theorem IsChewi114AMDescentCertificate.exists_threshold_index_of_geometric_burnin
    {gap energy : ℕ -> ℝ} {beta R : ℝ} {D n0 M : ℕ}
    (hcert : IsChewi114AMDescentCertificate gap energy beta R D)
    (hbeta : 0 < beta) (hscale : 0 < (D : ℝ) ^ (2 : ℕ) * R ^ (2 : ℕ))
    (hpow_le :
      (1 / 2 : ℝ) ^ M * gap n0 ≤ chewi114K beta D R / 2) :
    ∃ m, m ≤ M ∧ gap (n0 + m) ≤ chewi114K beta D R / 2 := by
  have hsource := hcert.sourceCertificate hbeta hscale
  have hA : 0 < chewi114A beta D R := by
    have hprod : 0 < (2 * beta) * ((D : ℝ) ^ (2 : ℕ) * R ^ (2 : ℕ)) :=
      mul_pos (by positivity) hscale
    simpa [chewi114A, mul_assoc] using hprod
  exact hsource.exists_threshold_index_of_geometric_burnin hA hpow_le

/--
Burn-in plus tail epsilon endpoint from a block-coordinate descent certificate.
-/
theorem IsChewi114AMDescentCertificate.exists_tail_gap_le_eps_of_geometric_burnin
    {gap energy : ℕ -> ℝ} {beta R eps : ℝ} {D n0 B M : ℕ}
    (hcert : IsChewi114AMDescentCertificate gap energy beta R D)
    (hbeta : 0 < beta) (hscale : 0 < (D : ℝ) ^ (2 : ℕ) * R ^ (2 : ℕ))
    (hM : M ≠ 0)
    (hpow_le :
      (1 / 2 : ℝ) ^ B * gap n0 ≤ chewi114K beta D R / 2)
    (hpos : ∀ b, b ≤ B -> gap (n0 + b) ≤ chewi114K beta D R / 2 ->
      ∀ m, m ≤ M -> 0 < gap ((n0 + b) + m))
    (hK_div_le : chewi114K beta D R / (M : ℝ) ≤ eps) :
    ∃ b, b ≤ B ∧ gap ((n0 + b) + M) ≤ eps := by
  have hsource := hcert.sourceCertificate hbeta hscale
  have hA : 0 < chewi114A beta D R := by
    have hprod : 0 < (2 * beta) * ((D : ℝ) ^ (2 : ℕ) * R ^ (2 : ℕ)) :=
      mul_pos (by positivity) hscale
    simpa [chewi114A, mul_assoc] using hprod
  exact hsource.exists_tail_gap_le_eps_of_geometric_burnin
    hA hM hpow_le hpos hK_div_le

/--
Logarithmic burn-in existence from a block-coordinate descent certificate.
-/
theorem IsChewi114AMDescentCertificate.exists_threshold_index_of_log_burnin
    {gap energy : ℕ -> ℝ} {beta R : ℝ} {D n0 B : ℕ}
    (hcert : IsChewi114AMDescentCertificate gap energy beta R D)
    (hbeta : 0 < beta) (hscale : 0 < (D : ℝ) ^ (2 : ℕ) * R ^ (2 : ℕ))
    (hgap0_pos : 0 < gap n0)
    (hB_log :
      Real.log (gap n0 / (chewi114K beta D R / 2)) ≤
        (B : ℝ) * Real.log (2 : ℝ)) :
    ∃ b, b ≤ B ∧ gap (n0 + b) ≤ chewi114K beta D R / 2 := by
  have hsource := hcert.sourceCertificate hbeta hscale
  have hA : 0 < chewi114A beta D R := by
    have hprod : 0 < (2 * beta) * ((D : ℝ) ^ (2 : ℕ) * R ^ (2 : ℕ)) :=
      mul_pos (by positivity) hscale
    simpa [chewi114A, mul_assoc] using hprod
  exact hsource.exists_threshold_index_of_log_burnin hA hgap0_pos hB_log

/--
Logarithmic burn-in plus tail epsilon endpoint from a block-coordinate descent
certificate.
-/
theorem IsChewi114AMDescentCertificate.exists_tail_gap_le_eps_of_log_burnin
    {gap energy : ℕ -> ℝ} {beta R eps : ℝ} {D n0 B M : ℕ}
    (hcert : IsChewi114AMDescentCertificate gap energy beta R D)
    (hbeta : 0 < beta) (hscale : 0 < (D : ℝ) ^ (2 : ℕ) * R ^ (2 : ℕ))
    (hM : M ≠ 0)
    (hgap0_pos : 0 < gap n0)
    (hB_log :
      Real.log (gap n0 / (chewi114K beta D R / 2)) ≤
        (B : ℝ) * Real.log (2 : ℝ))
    (hpos : ∀ b, b ≤ B -> gap (n0 + b) ≤ chewi114K beta D R / 2 ->
      ∀ m, m ≤ M -> 0 < gap ((n0 + b) + m))
    (hK_div_le : chewi114K beta D R / (M : ℝ) ≤ eps) :
    ∃ b, b ≤ B ∧ gap ((n0 + b) + M) ≤ eps := by
  have hsource := hcert.sourceCertificate hbeta hscale
  have hA : 0 < chewi114A beta D R := by
    have hprod : 0 < (2 * beta) * ((D : ℝ) ^ (2 : ℕ) * R ^ (2 : ℕ)) :=
      mul_pos (by positivity) hscale
    simpa [chewi114A, mul_assoc] using hprod
  exact hsource.exists_tail_gap_le_eps_of_log_burnin
    hA hM hgap0_pos hB_log hpos hK_div_le

end Optimization
end StatInference
