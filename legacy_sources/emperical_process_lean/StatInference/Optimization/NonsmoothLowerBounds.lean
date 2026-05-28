import StatInference.Optimization.LowerBounds
import StatInference.Optimization.ProjectedSubgradient

/-!
# Chewi Chapter 6 nonsmooth lower-bound layer

This module starts the formalization of Chewi Theorems 6.21-6.25.  The first
packet isolates the reusable obstruction in Theorem 6.21: the resisting
subgradient oracle keeps every gradient-span iterate in the coordinate-prefix
subspace, and the max-coordinate hard objective is nonnegative on that
subspace while its optimum value is negative.
-/

namespace StatInference
namespace Optimization

open scoped InnerProductSpace Topology

/--
The maximum coordinate of a finite Euclidean vector.  Chewi Theorem 6.21 uses
`max_i x[i]` as the nonsmooth part of the hard objective.
-/
noncomputable def chewi621CoordinateMax {d : ℕ} [NeZero d]
    (x : EuclideanSpace ℝ (Fin d)) : ℝ :=
  (Finset.univ.image (fun i : Fin d => x i)).max' (by simp)

/-- The source hard objective `gamma * max_i x[i] + alpha / 2 * ‖x‖²`. -/
noncomputable def chewi621HardObjective {d : ℕ} [NeZero d]
    (alpha gamma : ℝ) (x : EuclideanSpace ℝ (Fin d)) : ℝ :=
  gamma * chewi621CoordinateMax x + (alpha / 2) * ‖x‖ ^ (2 : ℕ)

/-- Indices attaining the maximum coordinate of `x`. -/
noncomputable def chewi621ActiveIndexSet {d : ℕ} [NeZero d]
    (x : EuclideanSpace ℝ (Fin d)) : Finset (Fin d) :=
  Finset.univ.filter fun i : Fin d => x i = chewi621CoordinateMax x

theorem chewi621ActiveIndexSet_nonempty {d : ℕ} [NeZero d]
    (x : EuclideanSpace ℝ (Fin d)) :
    (chewi621ActiveIndexSet (d := d) x).Nonempty := by
  have hmax_mem :
      chewi621CoordinateMax x ∈
        Finset.univ.image (fun i : Fin d => x i) := by
    simpa [chewi621CoordinateMax] using
      (Finset.max'_mem (Finset.univ.image (fun i : Fin d => x i)) (by simp))
  rcases Finset.mem_image.mp hmax_mem with ⟨i, _hi, hxi⟩
  exact ⟨i, by simp [chewi621ActiveIndexSet, hxi]⟩

/--
The resisting oracle uses the first coordinate attaining the maximum.  The
minimum is with respect to the usual order on `Fin d`, matching Chewi's
`min I_*(x)`.
-/
noncomputable def chewi621FirstMaxIndex {d : ℕ} [NeZero d]
    (x : EuclideanSpace ℝ (Fin d)) : Fin d :=
  (chewi621ActiveIndexSet (d := d) x).min'
    (chewi621ActiveIndexSet_nonempty (d := d) x)

theorem chewi621FirstMaxIndex_is_max {d : ℕ} [NeZero d]
    (x : EuclideanSpace ℝ (Fin d)) :
    x (chewi621FirstMaxIndex (d := d) x) = chewi621CoordinateMax x := by
  have hmem :
      chewi621FirstMaxIndex (d := d) x ∈
        chewi621ActiveIndexSet (d := d) x := by
    simpa [chewi621FirstMaxIndex] using
      Finset.min'_mem (chewi621ActiveIndexSet (d := d) x)
        (chewi621ActiveIndexSet_nonempty (d := d) x)
  simpa [chewi621ActiveIndexSet] using hmem

/-- Standard coordinate basis vector in `EuclideanSpace ℝ (Fin d)`. -/
noncomputable def chewi621CoordinateBasis {d : ℕ}
    (i : Fin d) : EuclideanSpace ℝ (Fin d) :=
  WithLp.toLp 2 fun j : Fin d => if j = i then (1 : ℝ) else 0

@[simp] theorem chewi621CoordinateBasis_apply {d : ℕ}
    (i j : Fin d) :
    chewi621CoordinateBasis i j = if j = i then (1 : ℝ) else 0 := by
  simp [chewi621CoordinateBasis, PiLp.toLp_apply]

/-- Coordinate basis vectors extract the corresponding coordinate by inner product. -/
theorem chewi621CoordinateBasis_inner {d : ℕ}
    (i : Fin d) (z : EuclideanSpace ℝ (Fin d)) :
    inner ℝ (chewi621CoordinateBasis i) z = z i := by
  simp [chewi621CoordinateBasis, PiLp.inner_apply, RCLike.inner_apply]

/-- Coordinate basis vectors have unit Euclidean norm. -/
theorem chewi621CoordinateBasis_norm {d : ℕ}
    (i : Fin d) :
    ‖chewi621CoordinateBasis i‖ = 1 := by
  have hinner :
      inner ℝ (chewi621CoordinateBasis i) (chewi621CoordinateBasis i) = 1 := by
    rw [chewi621CoordinateBasis_inner]
    simp
  have hsq :
      ‖chewi621CoordinateBasis i‖ ^ (2 : ℕ) = 1 := by
    rw [← hinner, real_inner_self_eq_norm_sq]
  nlinarith [norm_nonneg (chewi621CoordinateBasis i)]

/--
Chewi's displayed candidate minimizer for Theorem 6.21:
`x_*[k] = -gamma / (alpha * d)`.
-/
noncomputable def chewi621Minimizer {d : ℕ}
    (alpha gamma : ℝ) : EuclideanSpace ℝ (Fin d) :=
  WithLp.toLp 2 fun _i : Fin d => -gamma / (alpha * (d : ℝ))

@[simp] theorem chewi621Minimizer_apply {d : ℕ}
    (alpha gamma : ℝ) (i : Fin d) :
    chewi621Minimizer (d := d) alpha gamma i =
      -gamma / (alpha * (d : ℝ)) := by
  simp [chewi621Minimizer, PiLp.toLp_apply]

/-- The maximum coordinate dominates each coordinate. -/
theorem chewi621CoordinateMax_ge_coord {d : ℕ} [NeZero d]
    (x : EuclideanSpace ℝ (Fin d)) (i : Fin d) :
    x i ≤ chewi621CoordinateMax x := by
  have hi_mem :
      x i ∈ Finset.univ.image (fun j : Fin d => x j) := by
    exact Finset.mem_image.mpr ⟨i, by simp, rfl⟩
  simpa [chewi621CoordinateMax] using
    (Finset.le_max'
      (s := Finset.univ.image (fun j : Fin d => x j)) (x i) hi_mem)

/-- The maximum coordinate of Chewi's constant candidate is its coordinate value. -/
theorem chewi621CoordinateMax_minimizer {d : ℕ} [NeZero d]
    (alpha gamma : ℝ) :
    chewi621CoordinateMax (d := d) (chewi621Minimizer (d := d) alpha gamma) =
      -gamma / (alpha * (d : ℝ)) := by
  unfold chewi621CoordinateMax
  rw [Finset.max'_eq_iff]
  constructor
  · exact Finset.mem_image.mpr
      ⟨Classical.choice (inferInstance : Nonempty (Fin d)), by simp, by simp⟩
  · intro y hy
    rcases Finset.mem_image.mp hy with ⟨i, _hi, rfl⟩
    simp

/-- Squared norm of Chewi's constant candidate. -/
theorem chewi621Minimizer_norm_sq {d : ℕ}
    (alpha gamma : ℝ) :
    ‖chewi621Minimizer (d := d) alpha gamma‖ ^ (2 : ℕ) =
      (d : ℝ) * (gamma / (alpha * (d : ℝ))) ^ (2 : ℕ) := by
  rw [EuclideanSpace.real_norm_sq_eq]
  calc
    (∑ i : Fin d, (chewi621Minimizer (d := d) alpha gamma i) ^ (2 : ℕ))
        = ∑ _i : Fin d, (gamma / (alpha * (d : ℝ))) ^ (2 : ℕ) := by
          refine Finset.sum_congr rfl ?_
          intro i _hi
          simp
          ring
    _ = (d : ℝ) * (gamma / (alpha * (d : ℝ))) ^ (2 : ℕ) := by
      simp [Finset.sum_const, nsmul_eq_mul]

/--
If `x ∈ V_k` and `k < d`, then the first maximum coordinate is at most `k`.
Indeed all coordinates from `k` onward vanish, and coordinate `k` is available
as a zero-valued maximizer whenever the first maximizer would otherwise be in
the tail.
-/
theorem chewi621FirstMaxIndex_le_of_mem_coordinatePrefixSubmodule
    {d k : ℕ} [NeZero d] {x : EuclideanSpace ℝ (Fin d)}
    (hkd : k < d) (hx : x ∈ coordinatePrefixSubmodule d k) :
    (chewi621FirstMaxIndex (d := d) x).1 ≤ k := by
  let idx := chewi621FirstMaxIndex (d := d) x
  by_cases hidx_le : idx.1 ≤ k
  · exact hidx_le
  · have hk_le_idx : k ≤ idx.1 := by omega
    have hidx_zero : x idx = 0 := hx idx hk_le_idx
    have hmax_zero : chewi621CoordinateMax x = 0 := by
      simpa [idx, hidx_zero] using
        (chewi621FirstMaxIndex_is_max (d := d) x).symm
    let ik : Fin d := ⟨k, hkd⟩
    have hik_mem : ik ∈ chewi621ActiveIndexSet (d := d) x := by
      have hik_zero : x ik = 0 := hx ik le_rfl
      simp [chewi621ActiveIndexSet, hik_zero, hmax_zero]
    have hidx_le_ik : idx ≤ ik := by
      simpa [idx, chewi621FirstMaxIndex] using
        Finset.min'_le (chewi621ActiveIndexSet (d := d) x) ik hik_mem
    exact hidx_le_ik

/-- Coordinate basis vectors are supported in the corresponding prefix subspace. -/
theorem chewi621CoordinateBasis_mem_coordinatePrefixSubmodule_succ
    {d : ℕ} (i : Fin d) :
    chewi621CoordinateBasis i ∈ coordinatePrefixSubmodule d (i.1 + 1) := by
  intro j hj
  have hne : j ≠ i := by
    intro hji
    have : j.1 = i.1 := congrArg Fin.val hji
    omega
  simp [hne]

/--
The first-max resisting oracle from Chewi Theorem 6.21:
`x ↦ alpha x + gamma e_i`, where `i` is the first maximum coordinate of `x`.
-/
noncomputable def chewi621FirstMaxOracle {d : ℕ} [NeZero d]
    (alpha gamma : ℝ) (x : EuclideanSpace ℝ (Fin d)) :
    EuclideanSpace ℝ (Fin d) :=
  alpha • x + gamma • chewi621CoordinateBasis (chewi621FirstMaxIndex (d := d) x)

/--
On a radius-`R` set, Chewi's first-max oracle has norm at most
`gamma + alpha * R`.  This is the bounded-domain replacement for the false
global Lipschitz statement when `alpha > 0`.
-/
theorem chewi621FirstMaxOracle_norm_le_of_norm_le
    {d : ℕ} [NeZero d] {alpha gamma R : ℝ}
    {x : EuclideanSpace ℝ (Fin d)}
    (halpha_nonneg : 0 ≤ alpha) (hgamma_nonneg : 0 ≤ gamma)
    (hxnorm : ‖x‖ ≤ R) :
    ‖chewi621FirstMaxOracle (d := d) alpha gamma x‖ ≤
      gamma + alpha * R := by
  let e := chewi621CoordinateBasis (chewi621FirstMaxIndex (d := d) x)
  have htri :
      ‖chewi621FirstMaxOracle (d := d) alpha gamma x‖ ≤
        ‖alpha • x‖ + ‖gamma • e‖ := by
    simpa [chewi621FirstMaxOracle, e] using
      norm_add_le (alpha • x) (gamma • e)
  have hnorm_eq :
      ‖alpha • x‖ + ‖gamma • e‖ =
        alpha * ‖x‖ + gamma := by
    rw [norm_smul, norm_smul, Real.norm_of_nonneg halpha_nonneg,
      Real.norm_of_nonneg hgamma_nonneg, chewi621CoordinateBasis_norm]
    ring
  have hscaled : alpha * ‖x‖ ≤ alpha * R :=
    mul_le_mul_of_nonneg_left hxnorm halpha_nonneg
  calc
    ‖chewi621FirstMaxOracle (d := d) alpha gamma x‖ ≤
        ‖alpha • x‖ + ‖gamma • e‖ := htri
    _ = alpha * ‖x‖ + gamma := hnorm_eq
    _ ≤ alpha * R + gamma := by nlinarith
    _ = gamma + alpha * R := by ring

/-- The quadratic part's first-order lower model. -/
theorem chewi621_quadratic_subgradient_ineq {d : ℕ}
    {alpha : ℝ} (halpha_nonneg : 0 ≤ alpha)
    (x y : EuclideanSpace ℝ (Fin d)) :
    (alpha / 2) * ‖x‖ ^ (2 : ℕ) + inner ℝ (alpha • x) (y - x) ≤
      (alpha / 2) * ‖y‖ ^ (2 : ℕ) := by
  have hdecomp : y = x + (y - x) := by
    module
  have hsq_nonneg : 0 ≤ ‖y - x‖ ^ (2 : ℕ) := sq_nonneg _
  rw [hdecomp, norm_add_sq_real, real_inner_smul_left]
  have hdiff : x + (y - x) - x = y - x := by
    module
  rw [hdiff]
  nlinarith [mul_nonneg halpha_nonneg hsq_nonneg]

/-- The quadratic part's exact `alpha`-strong first-order lower model. -/
theorem chewi621_quadratic_strong_subgradient_ineq {d : ℕ}
    (alpha : ℝ) (x y : EuclideanSpace ℝ (Fin d)) :
    (alpha / 2) * ‖x‖ ^ (2 : ℕ) + inner ℝ (alpha • x) (y - x) +
        (alpha / 2) * ‖y - x‖ ^ (2 : ℕ) =
      (alpha / 2) * ‖y‖ ^ (2 : ℕ) := by
  have hdecomp : y = x + (y - x) := by
    module
  rw [hdecomp, norm_add_sq_real, real_inner_smul_left]
  have hdiff : x + (y - x) - x = y - x := by
    module
  rw [hdiff]
  ring

/-- The first-max part's subgradient inequality. -/
theorem chewi621_firstMax_subgradient_ineq {d : ℕ} [NeZero d]
    {gamma : ℝ} (hgamma_nonneg : 0 ≤ gamma)
    (x y : EuclideanSpace ℝ (Fin d)) :
    gamma * chewi621CoordinateMax x +
        inner ℝ (gamma • chewi621CoordinateBasis (chewi621FirstMaxIndex (d := d) x))
          (y - x) ≤
      gamma * chewi621CoordinateMax y := by
  let i := chewi621FirstMaxIndex (d := d) x
  have hmax_x : x i = chewi621CoordinateMax x :=
    chewi621FirstMaxIndex_is_max (d := d) x
  have hcoord_y : y i ≤ chewi621CoordinateMax y :=
    chewi621CoordinateMax_ge_coord y i
  have hbasis :
      inner ℝ (chewi621CoordinateBasis i) (y - x) = y i - x i := by
    rw [chewi621CoordinateBasis_inner]
    rfl
  rw [real_inner_smul_left, hbasis, ← hmax_x]
  nlinarith [mul_le_mul_of_nonneg_left hcoord_y hgamma_nonneg]

/--
The first-max resisting oracle is a valid subgradient of Chewi's hard
max-plus-quadratic objective on the whole space.
-/
theorem chewi621FirstMaxOracle_isSubgradientAt_univ
    {d : ℕ} [NeZero d] {alpha gamma : ℝ}
    (halpha_nonneg : 0 ≤ alpha) (hgamma_nonneg : 0 ≤ gamma)
    (x : EuclideanSpace ℝ (Fin d)) :
    IsSubgradientAt Set.univ
      (chewi621HardObjective (d := d) alpha gamma)
      (chewi621FirstMaxOracle (d := d) alpha gamma x) x := by
  refine ⟨by simp, ?_⟩
  intro y _hy
  have hmax :=
    chewi621_firstMax_subgradient_ineq
      (d := d) (gamma := gamma) hgamma_nonneg x y
  have hquad :=
    chewi621_quadratic_subgradient_ineq
      (d := d) (alpha := alpha) halpha_nonneg x y
  calc
    chewi621HardObjective (d := d) alpha gamma x +
        inner ℝ (chewi621FirstMaxOracle (d := d) alpha gamma x) (y - x)
        =
      (gamma * chewi621CoordinateMax x +
          inner ℝ
            (gamma • chewi621CoordinateBasis (chewi621FirstMaxIndex (d := d) x))
            (y - x)) +
        ((alpha / 2) * ‖x‖ ^ (2 : ℕ) + inner ℝ (alpha • x) (y - x)) := by
          simp [chewi621HardObjective, chewi621FirstMaxOracle, inner_add_left]
          ring
    _ ≤ gamma * chewi621CoordinateMax y +
        (alpha / 2) * ‖y‖ ^ (2 : ℕ) := add_le_add hmax hquad
    _ = chewi621HardObjective (d := d) alpha gamma y := by
      rfl

/--
First-order convexity certificate for the max-plus-quadratic hard objective.
This packages the everywhere-valid first-max subgradient as the local
`FirstOrderStrongConvexOn ... 0` interface used by earlier theorem layers.
-/
theorem chewi621HardObjective_firstOrderConvexOn_univ
    {d : ℕ} [NeZero d] {alpha gamma : ℝ}
    (halpha_nonneg : 0 ≤ alpha) (hgamma_nonneg : 0 ≤ gamma) :
    FirstOrderStrongConvexOn Set.univ
      (chewi621HardObjective (d := d) alpha gamma)
      (chewi621FirstMaxOracle (d := d) alpha gamma) 0 := by
  refine ⟨convex_univ, ?_⟩
  intro x _hx y _hy
  have hsub :=
    chewi621FirstMaxOracle_isSubgradientAt_univ
      (d := d) (alpha := alpha) (gamma := gamma)
      halpha_nonneg hgamma_nonneg x
  simpa using hsub.2 (by simp : y ∈ (Set.univ :
    Set (EuclideanSpace ℝ (Fin d))))

/--
First-order strong-convexity certificate for the hard objective.  The max part
is convex via the first-max subgradient; the quadratic part supplies the
`alpha` lower-model correction exactly.
-/
theorem chewi621HardObjective_firstOrderStrongConvexOn_univ
    {d : ℕ} [NeZero d] {alpha gamma : ℝ}
    (hgamma_nonneg : 0 ≤ gamma) :
    FirstOrderStrongConvexOn Set.univ
      (chewi621HardObjective (d := d) alpha gamma)
      (chewi621FirstMaxOracle (d := d) alpha gamma) alpha := by
  refine ⟨convex_univ, ?_⟩
  intro x _hx y _hy
  have hmax :=
    chewi621_firstMax_subgradient_ineq
      (d := d) (gamma := gamma) hgamma_nonneg x y
  have hquad :=
    chewi621_quadratic_strong_subgradient_ineq
      (d := d) alpha x y
  calc
    chewi621HardObjective (d := d) alpha gamma x +
        inner ℝ (chewi621FirstMaxOracle (d := d) alpha gamma x) (y - x) +
          (alpha / 2) * ‖y - x‖ ^ (2 : ℕ)
        =
      (gamma * chewi621CoordinateMax x +
          inner ℝ
            (gamma • chewi621CoordinateBasis (chewi621FirstMaxIndex (d := d) x))
            (y - x)) +
        ((alpha / 2) * ‖x‖ ^ (2 : ℕ) + inner ℝ (alpha • x) (y - x) +
          (alpha / 2) * ‖y - x‖ ^ (2 : ℕ)) := by
          simp [chewi621HardObjective, chewi621FirstMaxOracle, inner_add_left]
          ring
    _ ≤ gamma * chewi621CoordinateMax y +
        (alpha / 2) * ‖y‖ ^ (2 : ℕ) := by
          rw [hquad]
          have hmax' :=
            add_le_add_right hmax ((alpha / 2) * ‖y‖ ^ (2 : ℕ))
          simpa [add_assoc, add_comm, add_left_comm] using hmax'
    _ = chewi621HardObjective (d := d) alpha gamma y := by
      rfl

/--
The support calculation for Chewi's first-max oracle: if an iterate is in
`V_k` and `k < d`, the oracle output lies in `V_{k+1}`.
-/
theorem chewi621FirstMaxOracle_mem_coordinatePrefixSubmodule
    {d k : ℕ} [NeZero d] {alpha gamma : ℝ}
    {x : EuclideanSpace ℝ (Fin d)}
    (hkd : k < d) (hx : x ∈ coordinatePrefixSubmodule d k) :
    chewi621FirstMaxOracle (d := d) alpha gamma x ∈
      coordinatePrefixSubmodule d (k + 1) := by
  let idx := chewi621FirstMaxIndex (d := d) x
  have hidx_le : idx.1 ≤ k :=
    chewi621FirstMaxIndex_le_of_mem_coordinatePrefixSubmodule hkd hx
  have hx_succ : x ∈ coordinatePrefixSubmodule d (k + 1) :=
    coordinatePrefixSubmodule_mono d (Nat.le_succ k) hx
  have hbasis_succ :
      chewi621CoordinateBasis idx ∈ coordinatePrefixSubmodule d (k + 1) :=
    coordinatePrefixSubmodule_mono d (Nat.succ_le_succ hidx_le)
      (chewi621CoordinateBasis_mem_coordinatePrefixSubmodule_succ idx)
  have hx_scaled :
      alpha • x ∈ coordinatePrefixSubmodule d (k + 1) :=
    (coordinatePrefixSubmodule d (k + 1)).smul_mem alpha hx_succ
  have hbasis_scaled :
      gamma • chewi621CoordinateBasis idx ∈ coordinatePrefixSubmodule d (k + 1) :=
    (coordinatePrefixSubmodule d (k + 1)).smul_mem gamma hbasis_succ
  simpa [chewi621FirstMaxOracle, idx] using
    (coordinatePrefixSubmodule d (k + 1)).add_mem hx_scaled hbasis_scaled

/--
The same support calculation without the `k < d` side condition.  Once
`k >= d`, the target prefix subspace is already all of `EuclideanSpace`.
-/
theorem chewi621FirstMaxOracle_mem_coordinatePrefixSubmodule_of_mem
    {d k : ℕ} [NeZero d] {alpha gamma : ℝ}
    {x : EuclideanSpace ℝ (Fin d)}
    (hx : x ∈ coordinatePrefixSubmodule d k) :
    chewi621FirstMaxOracle (d := d) alpha gamma x ∈
      coordinatePrefixSubmodule d (k + 1) := by
  by_cases hkd : k < d
  · exact chewi621FirstMaxOracle_mem_coordinatePrefixSubmodule hkd hx
  · have hdk : d ≤ k + 1 := by omega
    rw [coordinatePrefixSubmodule_eq_top_of_le hdk]
    trivial

/--
The value of the hard objective at Chewi's displayed candidate:
`f(x_*) = -gamma^2 / (2 alpha d)`.
-/
theorem chewi621HardObjective_minimizer_value {d : ℕ} [NeZero d]
    {alpha gamma : ℝ} (halpha : alpha ≠ 0) :
    chewi621HardObjective (d := d) alpha gamma
        (chewi621Minimizer (d := d) alpha gamma) =
      -gamma ^ (2 : ℕ) / (2 * alpha * (d : ℝ)) := by
  have hd : (d : ℝ) ≠ 0 := by exact_mod_cast (NeZero.ne d)
  rw [chewi621HardObjective, chewi621CoordinateMax_minimizer,
    chewi621Minimizer_norm_sq]
  field_simp [halpha, hd]
  ring

/-- Squared norm of Chewi's minimizer under the displayed source choice of `alpha`. -/
theorem chewi621Minimizer_norm_sq_source_alpha {d : ℕ} [NeZero d]
    {R gamma : ℝ} (hR : R ≠ 0) (hgamma : gamma ≠ 0) :
    ‖chewi621Minimizer (d := d)
        (gamma / (R * Real.sqrt (d : ℝ))) gamma‖ ^ (2 : ℕ) =
      R ^ (2 : ℕ) := by
  have hd_nonneg : 0 ≤ (d : ℝ) := by positivity
  have hd_pos : 0 < (d : ℝ) := by
    exact_mod_cast (Nat.pos_of_ne_zero (NeZero.ne d))
  have hsqrt_pos : 0 < Real.sqrt (d : ℝ) := Real.sqrt_pos.2 hd_pos
  have hsqrt_ne : Real.sqrt (d : ℝ) ≠ 0 := ne_of_gt hsqrt_pos
  have hd_ne : (d : ℝ) ≠ 0 := by exact_mod_cast (NeZero.ne d)
  rw [chewi621Minimizer_norm_sq]
  field_simp [hR, hgamma, hsqrt_ne, hd_ne]
  rw [Real.sq_sqrt hd_nonneg]

/-- Chewi's displayed `alpha` makes `‖x_*‖ = R`. -/
theorem chewi621Minimizer_norm_eq_radius_source_alpha {d : ℕ} [NeZero d]
    {R gamma : ℝ} (hR_pos : 0 < R) (hgamma : gamma ≠ 0) :
    ‖chewi621Minimizer (d := d)
        (gamma / (R * Real.sqrt (d : ℝ))) gamma‖ = R := by
  have hsq :=
    chewi621Minimizer_norm_sq_source_alpha
      (d := d) (R := R) (gamma := gamma) (ne_of_gt hR_pos) hgamma
  exact le_antisymm
    ((sq_le_sq₀ (norm_nonneg _) hR_pos.le).mp (le_of_eq hsq))
    ((sq_le_sq₀ hR_pos.le (norm_nonneg _)).mp (le_of_eq hsq.symm))

/--
For the displayed source parameters and `x_0 = 0`, the initial point lies in
the radius-`R` ball around the hard instance minimizer.
-/
theorem chewi621_zero_dist_minimizer_le_radius_source_alpha
    {d : ℕ} [NeZero d] {R gamma : ℝ}
    (hR_pos : 0 < R) (hgamma : gamma ≠ 0) :
    dist (0 : EuclideanSpace ℝ (Fin d))
        (chewi621Minimizer (d := d)
          (gamma / (R * Real.sqrt (d : ℝ))) gamma) ≤ R := by
  rw [dist_eq_norm, zero_sub, norm_neg]
  exact (chewi621Minimizer_norm_eq_radius_source_alpha
    (d := d) (R := R) (gamma := gamma) hR_pos hgamma).le

/--
Bounded-domain Lipschitz certificate for Chewi's hard instance on the ball
`‖x‖ <= R`.  The quadratic term prevents a global Lipschitz theorem for
`alpha > 0`, so Theorem 6.21 should use this radius-local statement.
-/
theorem chewi621HardObjective_lipschitzOnWith_closedBall_zero
    {d : ℕ} [NeZero d] {alpha gamma R : ℝ}
    (halpha_nonneg : 0 ≤ alpha) (hgamma_nonneg : 0 ≤ gamma) :
    LipschitzOnWith (Real.toNNReal (gamma + alpha * R))
      (chewi621HardObjective (d := d) alpha gamma)
      (Metric.closedBall (0 : EuclideanSpace ℝ (Fin d)) R) := by
  refine LipschitzOnWith.of_le_add_mul' (gamma + alpha * R) ?_
  intro x hx y _hy
  have hxnorm : ‖x‖ ≤ R := by
    simpa [Metric.mem_closedBall, dist_eq_norm] using hx
  let p := chewi621FirstMaxOracle (d := d) alpha gamma x
  have hgap :
      chewi621HardObjective (d := d) alpha gamma x -
          chewi621HardObjective (d := d) alpha gamma y ≤
        inner ℝ p (x - y) := by
    simpa [p] using
      (chewi621FirstMaxOracle_isSubgradientAt_univ
        (d := d) (alpha := alpha) (gamma := gamma)
        halpha_nonneg hgamma_nonneg x).gap_le_inner
        (C := Set.univ) (y := y) (by simp)
  have hinner :
      inner ℝ p (x - y) ≤ ‖p‖ * ‖x - y‖ :=
    real_inner_le_norm p (x - y)
  have hp_norm :
      ‖p‖ ≤ gamma + alpha * R := by
    simpa [p] using
      chewi621FirstMaxOracle_norm_le_of_norm_le
        (d := d) (alpha := alpha) (gamma := gamma) (R := R)
        halpha_nonneg hgamma_nonneg hxnorm
  have hmul :
      ‖p‖ * ‖x - y‖ ≤
        (gamma + alpha * R) * ‖x - y‖ :=
    mul_le_mul_of_nonneg_right hp_norm (norm_nonneg _)
  have hdist : dist x y = ‖x - y‖ := by
    simpa using (dist_eq_norm x y)
  have hgap_dist :
      chewi621HardObjective (d := d) alpha gamma x -
          chewi621HardObjective (d := d) alpha gamma y ≤
        (gamma + alpha * R) * dist x y := by
    calc
      chewi621HardObjective (d := d) alpha gamma x -
          chewi621HardObjective (d := d) alpha gamma y ≤
            inner ℝ p (x - y) := hgap
      _ ≤ ‖p‖ * ‖x - y‖ := hinner
      _ ≤ (gamma + alpha * R) * dist x y := by simpa [hdist] using hmul
  nlinarith

/--
Bounded-domain Lipschitz certificate on a ball with arbitrary center.  This is
the source-shaped form needed for Theorems 6.21 and 6.22, whose local domain is
`B(x_*, R)`.
-/
theorem chewi621HardObjective_lipschitzOnWith_closedBall
    {d : ℕ} [NeZero d] {alpha gamma R : ℝ}
    (center : EuclideanSpace ℝ (Fin d))
    (halpha_nonneg : 0 ≤ alpha) (hgamma_nonneg : 0 ≤ gamma) :
    LipschitzOnWith (Real.toNNReal (gamma + alpha * (‖center‖ + R)))
      (chewi621HardObjective (d := d) alpha gamma)
      (Metric.closedBall center R) := by
  refine LipschitzOnWith.of_le_add_mul'
    (gamma + alpha * (‖center‖ + R)) ?_
  intro x hx y _hy
  have hxcenter : ‖x - center‖ ≤ R := by
    simpa [Metric.mem_closedBall, dist_eq_norm] using hx
  have hxnorm : ‖x‖ ≤ ‖center‖ + R := by
    have hdecomp : center + (x - center) = x := by
      module
    calc
      ‖x‖ = ‖center + (x - center)‖ := by rw [hdecomp]
      _ ≤ ‖center‖ + ‖x - center‖ := norm_add_le _ _
      _ ≤ ‖center‖ + R := by nlinarith
  let p := chewi621FirstMaxOracle (d := d) alpha gamma x
  have hgap :
      chewi621HardObjective (d := d) alpha gamma x -
          chewi621HardObjective (d := d) alpha gamma y ≤
        inner ℝ p (x - y) := by
    simpa [p] using
      (chewi621FirstMaxOracle_isSubgradientAt_univ
        (d := d) (alpha := alpha) (gamma := gamma)
        halpha_nonneg hgamma_nonneg x).gap_le_inner
        (C := Set.univ) (y := y) (by simp)
  have hinner :
      inner ℝ p (x - y) ≤ ‖p‖ * ‖x - y‖ :=
    real_inner_le_norm p (x - y)
  have hp_norm :
      ‖p‖ ≤ gamma + alpha * (‖center‖ + R) := by
    simpa [p] using
      chewi621FirstMaxOracle_norm_le_of_norm_le
        (d := d) (alpha := alpha) (gamma := gamma)
        (R := ‖center‖ + R) halpha_nonneg hgamma_nonneg hxnorm
  have hmul :
      ‖p‖ * ‖x - y‖ ≤
        (gamma + alpha * (‖center‖ + R)) * ‖x - y‖ :=
    mul_le_mul_of_nonneg_right hp_norm (norm_nonneg _)
  have hdist : dist x y = ‖x - y‖ := by
    simpa using (dist_eq_norm x y)
  have hgap_dist :
      chewi621HardObjective (d := d) alpha gamma x -
          chewi621HardObjective (d := d) alpha gamma y ≤
        (gamma + alpha * (‖center‖ + R)) * dist x y := by
    calc
      chewi621HardObjective (d := d) alpha gamma x -
          chewi621HardObjective (d := d) alpha gamma y ≤
            inner ℝ p (x - y) := hgap
      _ ≤ ‖p‖ * ‖x - y‖ := hinner
      _ ≤ (gamma + alpha * (‖center‖ + R)) * dist x y := by
          simpa [hdist] using hmul
  nlinarith

/-- Chewi's displayed 6.21 parameters have local Lipschitz constant at most `L`. -/
theorem chewi621_source_lipschitz_constant_le
    {N : ℕ} {L R : ℝ} (hL_nonneg : 0 ≤ L) (hR_pos : 0 < R) :
    L / 4 +
        ((L / 4) / (R * Real.sqrt ((N + 1 : ℕ) : ℝ))) * R ≤
      L := by
  have hsqrt_pos : 0 < Real.sqrt ((N + 1 : ℕ) : ℝ) := by positivity
  have hR_ne : R ≠ 0 := ne_of_gt hR_pos
  have hsqrt_ne :
      Real.sqrt ((N + 1 : ℕ) : ℝ) ≠ 0 := ne_of_gt hsqrt_pos
  have hsqrt_ge_one :
      1 ≤ Real.sqrt ((N + 1 : ℕ) : ℝ) := by
    rw [Real.one_le_sqrt]
    norm_num
  have hL4_nonneg : 0 ≤ L / 4 := by positivity
  have hterm_eq :
      ((L / 4) / (R * Real.sqrt ((N + 1 : ℕ) : ℝ))) * R =
        (L / 4) / Real.sqrt ((N + 1 : ℕ) : ℝ) := by
    field_simp [hR_ne, hsqrt_ne]
  have hterm_le :
      (L / 4) / Real.sqrt ((N + 1 : ℕ) : ℝ) ≤ L / 4 := by
    rw [div_le_iff₀ hsqrt_pos]
    nlinarith [mul_le_mul_of_nonneg_left hsqrt_ge_one hL4_nonneg]
  rw [hterm_eq]
  nlinarith

/--
Source-shaped bounded-domain Lipschitz certificate for the concrete
`d = N + 1` Theorem 6.21 hard instance.  On the radius-`R` ball around the
initial point, the hard objective is `L`-Lipschitz for Chewi's displayed
choices `gamma = L/4` and `alpha = (L/4)/(R sqrt(N+1))`.
-/
theorem chewi621HardObjective_lipschitzOnWith_source_closedBall_zero
    {N : ℕ} {L R : ℝ} (hL_nonneg : 0 ≤ L) (hR_pos : 0 < R) :
    LipschitzOnWith (Real.toNNReal L)
      (chewi621HardObjective (d := N + 1)
        ((L / 4) / (R * Real.sqrt ((N + 1 : ℕ) : ℝ))) (L / 4))
      (Metric.closedBall (0 : EuclideanSpace ℝ (Fin (N + 1))) R) := by
  let alpha := (L / 4) / (R * Real.sqrt ((N + 1 : ℕ) : ℝ))
  let gamma := L / 4
  have hsqrt_pos : 0 < Real.sqrt ((N + 1 : ℕ) : ℝ) := by positivity
  have hden_pos : 0 < R * Real.sqrt ((N + 1 : ℕ) : ℝ) :=
    mul_pos hR_pos hsqrt_pos
  have halpha_nonneg : 0 ≤ alpha := by
    exact div_nonneg (div_nonneg hL_nonneg (by norm_num)) hden_pos.le
  have hgamma_nonneg : 0 ≤ gamma := by
    exact div_nonneg hL_nonneg (by norm_num)
  have hbase :
      LipschitzOnWith (Real.toNNReal (gamma + alpha * R))
        (chewi621HardObjective (d := N + 1) alpha gamma)
        (Metric.closedBall (0 : EuclideanSpace ℝ (Fin (N + 1))) R) :=
    chewi621HardObjective_lipschitzOnWith_closedBall_zero
      (d := N + 1) (alpha := alpha) (gamma := gamma) (R := R)
      halpha_nonneg hgamma_nonneg
  refine LipschitzOnWith.of_le_add_mul' L ?_
  intro x hx y hy
  have hraw := hbase.le_add_mul hx hy
  have hK_nonneg : 0 ≤ gamma + alpha * R := by
    exact add_nonneg hgamma_nonneg (mul_nonneg halpha_nonneg hR_pos.le)
  have hK_le : gamma + alpha * R ≤ L := by
    simpa [alpha, gamma, add_comm, add_left_comm, add_assoc, mul_comm,
      mul_left_comm, mul_assoc] using
      chewi621_source_lipschitz_constant_le
        (N := N) (L := L) (R := R) hL_nonneg hR_pos
  have hcoef :
      (Real.toNNReal (gamma + alpha * R) : ℝ) * dist x y ≤
        L * dist x y := by
    rw [Real.coe_toNNReal _ hK_nonneg]
    exact mul_le_mul_of_nonneg_right hK_le dist_nonneg
  nlinarith

/-- Chewi's displayed 6.21 parameters are `L`-Lipschitz on `B(x_*, R)`. -/
theorem chewi621_source_center_lipschitz_constant_le
    {N : ℕ} {L R : ℝ} (hL_nonneg : 0 ≤ L) (hR_pos : 0 < R) :
    L / 4 +
        ((L / 4) / (R * Real.sqrt ((N + 1 : ℕ) : ℝ))) * (R + R) ≤
      L := by
  have hsqrt_pos : 0 < Real.sqrt ((N + 1 : ℕ) : ℝ) := by positivity
  have hR_ne : R ≠ 0 := ne_of_gt hR_pos
  have hsqrt_ne :
      Real.sqrt ((N + 1 : ℕ) : ℝ) ≠ 0 := ne_of_gt hsqrt_pos
  have hsqrt_ge_one :
      1 ≤ Real.sqrt ((N + 1 : ℕ) : ℝ) := by
    rw [Real.one_le_sqrt]
    norm_num
  have hL2_nonneg : 0 ≤ L / 2 := by positivity
  have hterm_eq :
      ((L / 4) / (R * Real.sqrt ((N + 1 : ℕ) : ℝ))) * (R + R) =
        (L / 2) / Real.sqrt ((N + 1 : ℕ) : ℝ) := by
    field_simp [hR_ne, hsqrt_ne]
    ring
  have hterm_le :
      (L / 2) / Real.sqrt ((N + 1 : ℕ) : ℝ) ≤ L / 2 := by
    rw [div_le_iff₀ hsqrt_pos]
    nlinarith [mul_le_mul_of_nonneg_left hsqrt_ge_one hL2_nonneg]
  rw [hterm_eq]
  nlinarith

/--
Source-shaped centered-domain Lipschitz certificate for Theorem 6.21: Chewi's
hard objective is `L`-Lipschitz on `B(x_*, R)`.
-/
theorem chewi621HardObjective_lipschitzOnWith_source_closedBall_minimizer
    {N : ℕ} {L R : ℝ} (hL_pos : 0 < L) (hR_pos : 0 < R) :
    LipschitzOnWith (Real.toNNReal L)
      (chewi621HardObjective (d := N + 1)
        ((L / 4) / (R * Real.sqrt ((N + 1 : ℕ) : ℝ))) (L / 4))
      (Metric.closedBall
        (chewi621Minimizer (d := N + 1)
          ((L / 4) / (R * Real.sqrt ((N + 1 : ℕ) : ℝ))) (L / 4)) R) := by
  let alpha := (L / 4) / (R * Real.sqrt ((N + 1 : ℕ) : ℝ))
  let gamma := L / 4
  let center : EuclideanSpace ℝ (Fin (N + 1)) :=
    chewi621Minimizer (d := N + 1) alpha gamma
  have hsqrt_pos : 0 < Real.sqrt ((N + 1 : ℕ) : ℝ) := by positivity
  have hden_pos : 0 < R * Real.sqrt ((N + 1 : ℕ) : ℝ) :=
    mul_pos hR_pos hsqrt_pos
  have halpha_nonneg : 0 ≤ alpha :=
    div_nonneg (div_nonneg hL_pos.le (by norm_num)) hden_pos.le
  have hgamma_nonneg : 0 ≤ gamma :=
    div_nonneg hL_pos.le (by norm_num)
  have hcenter_norm : ‖center‖ = R := by
    simpa [center, alpha, gamma] using
      chewi621Minimizer_norm_eq_radius_source_alpha
        (d := N + 1) (R := R) (gamma := L / 4)
        hR_pos (ne_of_gt (by positivity : 0 < L / 4))
  have hbase :
      LipschitzOnWith (Real.toNNReal (gamma + alpha * (‖center‖ + R)))
        (chewi621HardObjective (d := N + 1) alpha gamma)
        (Metric.closedBall center R) :=
    chewi621HardObjective_lipschitzOnWith_closedBall
      (d := N + 1) (alpha := alpha) (gamma := gamma) (R := R)
      center halpha_nonneg hgamma_nonneg
  refine LipschitzOnWith.of_le_add_mul' L ?_
  intro x hx y hy
  have hraw := hbase.le_add_mul hx hy
  have hK_nonneg : 0 ≤ gamma + alpha * (‖center‖ + R) := by
    rw [hcenter_norm]
    positivity
  have hK_le : gamma + alpha * (‖center‖ + R) ≤ L := by
    rw [hcenter_norm]
    simpa [alpha, gamma] using
      chewi621_source_center_lipschitz_constant_le
        (N := N) (L := L) (R := R) hL_pos.le hR_pos
  have hcoef :
      (Real.toNNReal (gamma + alpha * (‖center‖ + R)) : ℝ) * dist x y ≤
        L * dist x y := by
    rw [Real.coe_toNNReal _ hK_nonneg]
    exact mul_le_mul_of_nonneg_right hK_le dist_nonneg
  nlinarith

/--
Source-shaped first-order convexity certificate for the concrete `d = N + 1`
Theorem 6.21 hard instance.
-/
theorem chewi621HardObjective_firstOrderConvexOn_source_univ
    {N : ℕ} {L R : ℝ} (hL_nonneg : 0 ≤ L) (hR_pos : 0 < R) :
    FirstOrderStrongConvexOn Set.univ
      (chewi621HardObjective (d := N + 1)
        ((L / 4) / (R * Real.sqrt ((N + 1 : ℕ) : ℝ))) (L / 4))
      (chewi621FirstMaxOracle (d := N + 1)
        ((L / 4) / (R * Real.sqrt ((N + 1 : ℕ) : ℝ))) (L / 4)) 0 := by
  have hsqrt_pos : 0 < Real.sqrt ((N + 1 : ℕ) : ℝ) := by positivity
  have hden_pos : 0 < R * Real.sqrt ((N + 1 : ℕ) : ℝ) :=
    mul_pos hR_pos hsqrt_pos
  have halpha_nonneg :
      0 ≤ (L / 4) / (R * Real.sqrt ((N + 1 : ℕ) : ℝ)) :=
    div_nonneg (div_nonneg hL_nonneg (by norm_num)) hden_pos.le
  have hgamma_nonneg : 0 ≤ L / 4 :=
    div_nonneg hL_nonneg (by norm_num)
  exact
    chewi621HardObjective_firstOrderConvexOn_univ
      (d := N + 1)
      (alpha := (L / 4) / (R * Real.sqrt ((N + 1 : ℕ) : ℝ)))
      (gamma := L / 4) halpha_nonneg hgamma_nonneg

/--
If a vector is supported on the first `N` coordinates and `N < d`, its maximum
coordinate is nonnegative: coordinate `N` itself is zero.
-/
theorem chewi621CoordinateMax_nonneg_of_mem_coordinatePrefixSubmodule
    {d N : ℕ} [NeZero d] {x : EuclideanSpace ℝ (Fin d)}
    (hNd : N < d) (hx : x ∈ coordinatePrefixSubmodule d N) :
    0 ≤ chewi621CoordinateMax x := by
  let i : Fin d := ⟨N, hNd⟩
  have hxi : x i = 0 := hx i le_rfl
  have hle := chewi621CoordinateMax_ge_coord x i
  simpa [hxi] using hle

/--
The max-plus-quadratic hard objective is nonnegative on the prefix subspace
`V_N` whenever `N < d`, `gamma >= 0`, and `alpha >= 0`.
-/
theorem chewi621HardObjective_nonneg_of_mem_coordinatePrefixSubmodule
    {d N : ℕ} [NeZero d] {alpha gamma : ℝ}
    {x : EuclideanSpace ℝ (Fin d)}
    (halpha_nonneg : 0 ≤ alpha) (hgamma_nonneg : 0 ≤ gamma)
    (hNd : N < d) (hx : x ∈ coordinatePrefixSubmodule d N) :
    0 ≤ chewi621HardObjective (d := d) alpha gamma x := by
  have hmax_nonneg :
      0 ≤ gamma * chewi621CoordinateMax x :=
    mul_nonneg hgamma_nonneg
      (chewi621CoordinateMax_nonneg_of_mem_coordinatePrefixSubmodule hNd hx)
  have hquad_nonneg :
      0 ≤ (alpha / 2) * ‖x‖ ^ (2 : ℕ) :=
    mul_nonneg (div_nonneg halpha_nonneg (by norm_num))
      (sq_nonneg ‖x‖)
  dsimp [chewi621HardObjective]
  nlinarith

/--
Chewi Theorem 6.21 obstruction, in reusable supplied-interface form.  A
resisting oracle that expands support by at most one coordinate per query keeps
the `N`th iterate in `V_N`; if all points in `V_N` have nonnegative objective
value and the optimum value is at most `-gap`, the final objective gap is at
least `gap`.
-/
theorem chewi621_gap_ge_of_gradientSpan_prefix_nonneg
    {d N : ℕ}
    {f : EuclideanSpace ℝ (Fin d) -> ℝ}
    {grad : EuclideanSpace ℝ (Fin d) -> EuclideanSpace ℝ (Fin d)}
    {x : ℕ -> EuclideanSpace ℝ (Fin d)}
    {fstar gap : ℝ}
    (hx0 : x 0 = 0)
    (hspan : IsGradientSpanTrajectory grad x)
    (hgrad : ∀ k, x k ∈ coordinatePrefixSubmodule d k ->
      grad (x k) ∈ coordinatePrefixSubmodule d (k + 1))
    (hprefix_nonneg :
      ∀ y, y ∈ coordinatePrefixSubmodule d N -> 0 ≤ f y)
    (hfstar_le : fstar ≤ -gap) :
    gap ≤ f (x N) - fstar := by
  have hxN : x N ∈ coordinatePrefixSubmodule d N :=
    gradientSpanTrajectory_mem_coordinatePrefixSubmodule_of_grad_mem_next
      hx0 hspan hgrad N
  have hfx_nonneg : 0 ≤ f (x N) := hprefix_nonneg (x N) hxN
  nlinarith

/--
Concrete Theorem 6.21 obstruction for Chewi's max-plus-quadratic hard
objective.  This is the compiled endpoint of the first nonsmooth lower-bound
packet; later packets instantiate the source's specific minimizer and
Lipschitz/radius parameter choices.
-/
theorem chewi621_hardObjective_gap_ge_of_gradientSpan
    {d N : ℕ} [NeZero d] {alpha gamma fstar gap : ℝ}
    {grad : EuclideanSpace ℝ (Fin d) -> EuclideanSpace ℝ (Fin d)}
    {x : ℕ -> EuclideanSpace ℝ (Fin d)}
    (halpha_nonneg : 0 ≤ alpha) (hgamma_nonneg : 0 ≤ gamma)
    (hNd : N < d)
    (hx0 : x 0 = 0)
    (hspan : IsGradientSpanTrajectory grad x)
    (hgrad : ∀ k, x k ∈ coordinatePrefixSubmodule d k ->
      grad (x k) ∈ coordinatePrefixSubmodule d (k + 1))
    (hfstar_le : fstar ≤ -gap) :
    gap ≤ chewi621HardObjective (d := d) alpha gamma (x N) - fstar := by
  exact
    chewi621_gap_ge_of_gradientSpan_prefix_nonneg
      (d := d) (N := N)
      (f := chewi621HardObjective (d := d) alpha gamma)
      (grad := grad) (x := x) (fstar := fstar) (gap := gap)
      hx0 hspan hgrad
      (fun y hy =>
        chewi621HardObjective_nonneg_of_mem_coordinatePrefixSubmodule
          halpha_nonneg hgamma_nonneg hNd hy)
      hfstar_le

/--
Chewi Theorem 6.21 obstruction with the concrete first-max resisting oracle and
the displayed candidate optimum value.  This removes the two main supplied
hypotheses from `chewi621_hardObjective_gap_ge_of_gradientSpan`: the oracle
prefix-support and the negative optimum-value calculation.
-/
theorem chewi621_gap_ge_minimizer_value_of_firstMaxGradientSpan
    {d N : ℕ} [NeZero d] {alpha gamma : ℝ}
    {x : ℕ -> EuclideanSpace ℝ (Fin d)}
    (halpha_pos : 0 < alpha) (hgamma_nonneg : 0 ≤ gamma)
    (hNd : N < d)
    (hx0 : x 0 = 0)
    (hspan :
      IsGradientSpanTrajectory
        (chewi621FirstMaxOracle (d := d) alpha gamma) x) :
    gamma ^ (2 : ℕ) / (2 * alpha * (d : ℝ)) ≤
      chewi621HardObjective (d := d) alpha gamma (x N) -
        chewi621HardObjective (d := d) alpha gamma
          (chewi621Minimizer (d := d) alpha gamma) := by
  have hfstar_le :
      chewi621HardObjective (d := d) alpha gamma
          (chewi621Minimizer (d := d) alpha gamma) ≤
        -(gamma ^ (2 : ℕ) / (2 * alpha * (d : ℝ))) := by
    rw [chewi621HardObjective_minimizer_value (d := d)
      (halpha := ne_of_gt halpha_pos)]
    ring_nf
    exact le_rfl
  exact
    chewi621_hardObjective_gap_ge_of_gradientSpan
      (d := d) (N := N) (alpha := alpha) (gamma := gamma)
      (fstar :=
        chewi621HardObjective (d := d) alpha gamma
          (chewi621Minimizer (d := d) alpha gamma))
      (gap := gamma ^ (2 : ℕ) / (2 * alpha * (d : ℝ)))
      (grad := chewi621FirstMaxOracle (d := d) alpha gamma)
      (x := x)
      (le_of_lt halpha_pos) hgamma_nonneg hNd hx0 hspan
      (fun k hxk =>
        chewi621FirstMaxOracle_mem_coordinatePrefixSubmodule_of_mem
          (d := d) (k := k) (alpha := alpha) (gamma := gamma) hxk)
      hfstar_le

/-- Scalar simplification for Chewi's displayed Theorem 6.21 parameters. -/
theorem chewi621_source_parameter_gap_eq
    {N : ℕ} {L R : ℝ} (hL : 0 < L) (hR : 0 < R) :
    (L / 4) ^ (2 : ℕ) /
        (2 * ((L / 4) / (R * Real.sqrt ((N + 1 : ℕ) : ℝ))) *
          ((N + 1 : ℕ) : ℝ)) =
      L * R / (8 * Real.sqrt ((N + 1 : ℕ) : ℝ)) := by
  have hL_ne : L ≠ 0 := ne_of_gt hL
  have hR_ne : R ≠ 0 := ne_of_gt hR
  have hsqrt_pos : 0 < Real.sqrt ((N + 1 : ℕ) : ℝ) := by positivity
  have hsqrt_ne : Real.sqrt ((N + 1 : ℕ) : ℝ) ≠ 0 := ne_of_gt hsqrt_pos
  have hsucc_nonneg : 0 ≤ ((N + 1 : ℕ) : ℝ) := by positivity
  field_simp [hL_ne, hR_ne, hsqrt_ne]
  rw [Real.sq_sqrt hsucc_nonneg]
  ring

/--
Chewi Theorem 6.21, source-parameter lower bound for the `d = N + 1` hard
instance and the concrete first-max resisting oracle.  This is the exact
finite-dimensional packet before embedding into arbitrary larger dimensions.
-/
theorem chewi621_gap_ge_source_parameters
    {N : ℕ} {L R : ℝ}
    {x : ℕ -> EuclideanSpace ℝ (Fin (N + 1))}
    (hL : 0 < L) (hR : 0 < R)
    (hx0 : x 0 = 0)
    (hspan :
      IsGradientSpanTrajectory
        (chewi621FirstMaxOracle (d := N + 1)
          ((L / 4) / (R * Real.sqrt ((N + 1 : ℕ) : ℝ))) (L / 4)) x) :
    L * R / (8 * Real.sqrt ((N + 1 : ℕ) : ℝ)) ≤
      chewi621HardObjective (d := N + 1)
        ((L / 4) / (R * Real.sqrt ((N + 1 : ℕ) : ℝ))) (L / 4) (x N) -
        chewi621HardObjective (d := N + 1)
          ((L / 4) / (R * Real.sqrt ((N + 1 : ℕ) : ℝ))) (L / 4)
          (chewi621Minimizer (d := N + 1)
            ((L / 4) / (R * Real.sqrt ((N + 1 : ℕ) : ℝ))) (L / 4)) := by
  have halpha_pos :
      0 < (L / 4) / (R * Real.sqrt ((N + 1 : ℕ) : ℝ)) := by positivity
  have hgamma_nonneg : 0 ≤ L / 4 := by positivity
  have hgap :=
    chewi621_gap_ge_minimizer_value_of_firstMaxGradientSpan
      (d := N + 1) (N := N)
      (alpha := (L / 4) / (R * Real.sqrt ((N + 1 : ℕ) : ℝ)))
      (gamma := L / 4) (x := x)
      halpha_pos hgamma_nonneg (Nat.lt_succ_self N) hx0 hspan
  rw [chewi621_source_parameter_gap_eq hL hR] at hgap
  exact hgap

/-- Scalar simplification for Chewi Theorem 6.22 parameters. -/
theorem chewi622_source_parameter_gap_eq
    {N : ℕ} {alpha L : ℝ} (halpha : alpha ≠ 0) :
    (L / 4) ^ (2 : ℕ) /
        (2 * alpha * ((N + 1 : ℕ) : ℝ)) =
      L ^ (2 : ℕ) / (32 * alpha * ((N + 1 : ℕ) : ℝ)) := by
  have hN : ((N + 1 : ℕ) : ℝ) ≠ 0 := by positivity
  field_simp [halpha, hN]
  ring

/-- Chewi Theorem 6.22's displayed radius for the strongly-convex hard instance. -/
noncomputable def chewi622Radius (N : ℕ) (alpha L : ℝ) : ℝ :=
  (L / 4) / (alpha * Real.sqrt ((N + 1 : ℕ) : ℝ))

theorem chewi622Radius_pos
    {N : ℕ} {alpha L : ℝ} (halpha : 0 < alpha) (hL : 0 < L) :
    0 < chewi622Radius N alpha L := by
  unfold chewi622Radius
  positivity

theorem chewi622_alpha_eq_source_radius
    {N : ℕ} {alpha L : ℝ} (halpha : 0 < alpha) (hL : 0 < L) :
    (L / 4) /
        (chewi622Radius N alpha L * Real.sqrt ((N + 1 : ℕ) : ℝ)) =
      alpha := by
  have halpha_ne : alpha ≠ 0 := ne_of_gt halpha
  have hL_ne : L ≠ 0 := ne_of_gt hL
  have hsqrt_pos : 0 < Real.sqrt ((N + 1 : ℕ) : ℝ) := by positivity
  have hsqrt_ne :
      Real.sqrt ((N + 1 : ℕ) : ℝ) ≠ 0 := ne_of_gt hsqrt_pos
  unfold chewi622Radius
  field_simp [halpha_ne, hL_ne, hsqrt_ne]

theorem chewi622Minimizer_norm_eq_radius
    {N : ℕ} {alpha L : ℝ} (halpha : 0 < alpha) (hL : 0 < L) :
    ‖chewi621Minimizer (d := N + 1) alpha (L / 4)‖ =
      chewi622Radius N alpha L := by
  have hR_pos := chewi622Radius_pos (N := N) halpha hL
  have hgamma_ne : L / 4 ≠ 0 := ne_of_gt (by positivity : 0 < L / 4)
  have hnorm :=
    chewi621Minimizer_norm_eq_radius_source_alpha
      (d := N + 1) (R := chewi622Radius N alpha L) (gamma := L / 4)
      hR_pos hgamma_ne
  rw [chewi622_alpha_eq_source_radius (N := N) halpha hL] at hnorm
  exact hnorm

theorem chewi622_zero_dist_minimizer_le_radius
    {N : ℕ} {alpha L : ℝ} (halpha : 0 < alpha) (hL : 0 < L) :
    dist (0 : EuclideanSpace ℝ (Fin (N + 1)))
        (chewi621Minimizer (d := N + 1) alpha (L / 4)) ≤
      chewi622Radius N alpha L := by
  rw [dist_eq_norm, zero_sub, norm_neg]
  exact (chewi622Minimizer_norm_eq_radius (N := N) halpha hL).le

/-- Chewi's displayed 6.22 parameters are `L`-Lipschitz on `B(x_*, R)`. -/
theorem chewi622_source_lipschitz_constant_le
    {N : ℕ} {alpha L : ℝ} (halpha : 0 < alpha) (hL : 0 < L) :
    L / 4 + alpha * (chewi622Radius N alpha L + chewi622Radius N alpha L) ≤
      L := by
  have halpha_ne : alpha ≠ 0 := ne_of_gt halpha
  have hsqrt_pos : 0 < Real.sqrt ((N + 1 : ℕ) : ℝ) := by positivity
  have hsqrt_ne :
      Real.sqrt ((N + 1 : ℕ) : ℝ) ≠ 0 := ne_of_gt hsqrt_pos
  have hsqrt_ge_one :
      1 ≤ Real.sqrt ((N + 1 : ℕ) : ℝ) := by
    rw [Real.one_le_sqrt]
    norm_num
  have hL2_nonneg : 0 ≤ L / 2 := by positivity
  have hterm_eq :
      alpha * (chewi622Radius N alpha L + chewi622Radius N alpha L) =
        (L / 2) / Real.sqrt ((N + 1 : ℕ) : ℝ) := by
    unfold chewi622Radius
    field_simp [halpha_ne, hsqrt_ne]
    ring
  have hterm_le :
      (L / 2) / Real.sqrt ((N + 1 : ℕ) : ℝ) ≤ L / 2 := by
    rw [div_le_iff₀ hsqrt_pos]
    nlinarith [mul_le_mul_of_nonneg_left hsqrt_ge_one hL2_nonneg]
  rw [hterm_eq]
  nlinarith

/--
Source-shaped centered-domain Lipschitz certificate for Theorem 6.22: the
strongly-convex hard objective is `L`-Lipschitz on `B(x_*, R)`.
-/
theorem chewi622HardObjective_lipschitzOnWith_source_closedBall_minimizer
    {N : ℕ} {alpha L : ℝ} (halpha : 0 < alpha) (hL : 0 < L) :
    LipschitzOnWith (Real.toNNReal L)
      (chewi621HardObjective (d := N + 1) alpha (L / 4))
      (Metric.closedBall
        (chewi621Minimizer (d := N + 1) alpha (L / 4))
        (chewi622Radius N alpha L)) := by
  let center : EuclideanSpace ℝ (Fin (N + 1)) :=
    chewi621Minimizer (d := N + 1) alpha (L / 4)
  let R := chewi622Radius N alpha L
  have hR_pos : 0 < R := by
    simpa [R] using chewi622Radius_pos (N := N) halpha hL
  have hgamma_nonneg : 0 ≤ L / 4 := by positivity
  have hcenter_norm : ‖center‖ = R := by
    simpa [center, R] using
      chewi622Minimizer_norm_eq_radius (N := N) halpha hL
  have hbase :
      LipschitzOnWith (Real.toNNReal (L / 4 + alpha * (‖center‖ + R)))
        (chewi621HardObjective (d := N + 1) alpha (L / 4))
        (Metric.closedBall center R) :=
    chewi621HardObjective_lipschitzOnWith_closedBall
      (d := N + 1) (alpha := alpha) (gamma := L / 4) (R := R)
      center halpha.le hgamma_nonneg
  refine LipschitzOnWith.of_le_add_mul' L ?_
  intro x hx y hy
  have hraw := hbase.le_add_mul hx hy
  have hK_nonneg : 0 ≤ L / 4 + alpha * (‖center‖ + R) := by
    rw [hcenter_norm]
    nlinarith [halpha, hL, hR_pos]
  have hK_le : L / 4 + alpha * (‖center‖ + R) ≤ L := by
    rw [hcenter_norm]
    simpa [R] using
      chewi622_source_lipschitz_constant_le
        (N := N) (alpha := alpha) (L := L) halpha hL
  have hcoef :
      (Real.toNNReal (L / 4 + alpha * (‖center‖ + R)) : ℝ) * dist x y ≤
        L * dist x y := by
    rw [Real.coe_toNNReal _ hK_nonneg]
    exact mul_le_mul_of_nonneg_right hK_le dist_nonneg
  nlinarith

/--
Chewi Theorem 6.22 source-rate lower-bound packet for the concrete
`d = N + 1` hard instance.  The same first-max oracle lower-bound construction
with `gamma = L / 4` yields a strongly-convex nonsmooth obstruction of order
`L^2 / (alpha * N)`.
-/
theorem chewi622_gap_ge_source_parameters
    {N : ℕ} {alpha L : ℝ}
    {x : ℕ -> EuclideanSpace ℝ (Fin (N + 1))}
    (halpha : 0 < alpha) (hL : 0 < L)
    (hx0 : x 0 = 0)
    (hspan :
      IsGradientSpanTrajectory
        (chewi621FirstMaxOracle (d := N + 1) alpha (L / 4)) x) :
    L ^ (2 : ℕ) / (32 * alpha * ((N + 1 : ℕ) : ℝ)) ≤
      chewi621HardObjective (d := N + 1) alpha (L / 4) (x N) -
        chewi621HardObjective (d := N + 1) alpha (L / 4)
          (chewi621Minimizer (d := N + 1) alpha (L / 4)) := by
  have hgamma_nonneg : 0 ≤ L / 4 := by positivity
  have hgap :=
    chewi621_gap_ge_minimizer_value_of_firstMaxGradientSpan
      (d := N + 1) (N := N)
      (alpha := alpha) (gamma := L / 4) (x := x)
      halpha hgamma_nonneg (Nat.lt_succ_self N) hx0 hspan
  rw [chewi622_source_parameter_gap_eq (N := N) (alpha := alpha) (L := L)
    (ne_of_gt halpha)] at hgap
  exact hgap

/--
Source-shaped first-order strong-convexity certificate for the concrete
Theorem 6.22 hard instance.
-/
theorem chewi622HardObjective_firstOrderStrongConvexOn_source_univ
    {N : ℕ} {alpha L : ℝ} (hL_nonneg : 0 ≤ L) :
    FirstOrderStrongConvexOn Set.univ
      (chewi621HardObjective (d := N + 1) alpha (L / 4))
      (chewi621FirstMaxOracle (d := N + 1) alpha (L / 4)) alpha := by
  exact
    chewi621HardObjective_firstOrderStrongConvexOn_univ
      (d := N + 1) (alpha := alpha) (gamma := L / 4)
      (div_nonneg hL_nonneg (by norm_num))

/-
## Theorem 6.25 feasibility lower-bound primitives

The feasibility lower bound uses a resisting separation oracle that repeatedly
halves an axis-aligned box along one coordinate.  This packet keeps the
geometric state elementary: a coordinate box, its strict coordinate interior,
the midpoint cut, and the separation vector returned by the resisting oracle.
-/

/-- Axis-aligned coordinate box `{x : a <= x <= b}`. -/
def chewi625CoordinateBox {d : ℕ}
    (a b : EuclideanSpace ℝ (Fin d)) : Set (EuclideanSpace ℝ (Fin d)) :=
  {x | ∀ i : Fin d, a i ≤ x i ∧ x i ≤ b i}

/--
The source proof only needs the strict coordinate interior of an axis-aligned
box.  A later report wrapper can bridge this to topological interior if needed.
-/
def chewi625StrictCoordinateBox {d : ℕ}
    (a b : EuclideanSpace ℝ (Fin d)) : Set (EuclideanSpace ℝ (Fin d)) :=
  {x | ∀ i : Fin d, a i < x i ∧ x i < b i}

/-- Axis-aligned coordinate boxes are closed convex feasibility bodies. -/
theorem chewi625CoordinateBox_isClosed {d : ℕ}
    (a b : EuclideanSpace ℝ (Fin d)) :
    IsClosed (chewi625CoordinateBox a b) := by
  have hrepr :
      chewi625CoordinateBox a b =
        ⋂ i : Fin d,
          {x : EuclideanSpace ℝ (Fin d) | a i ≤ x i ∧ x i ≤ b i} := by
    ext x
    simp [chewi625CoordinateBox]
  rw [hrepr]
  refine isClosed_iInter fun i => ?_
  have hcont :
      Continuous fun x : EuclideanSpace ℝ (Fin d) => x i :=
    (PiLp.continuous_apply (p := 2)
      (β := fun _ : Fin d => ℝ) i :
      Continuous fun x : EuclideanSpace ℝ (Fin d) => x i)
  exact (isClosed_Ici.preimage hcont).inter (isClosed_Iic.preimage hcont)

/-- Axis-aligned coordinate boxes are convex. -/
theorem chewi625CoordinateBox_convex {d : ℕ}
    (a b : EuclideanSpace ℝ (Fin d)) :
    Convex ℝ (chewi625CoordinateBox a b) := by
  rw [convex_iff_add_mem]
  intro x hx y hy μ ν hμ hν hsum i
  have hcoord :
      (μ • x + ν • y) i = μ * x i + ν * y i := by
    simp
  constructor
  · have hxlo : a i ≤ x i := (hx i).1
    have hylo : a i ≤ y i := (hy i).1
    have hμlo : μ * a i ≤ μ * x i :=
      mul_le_mul_of_nonneg_left hxlo hμ
    have hνlo : ν * a i ≤ ν * y i :=
      mul_le_mul_of_nonneg_left hylo hν
    have hscale : μ * a i + ν * a i = a i := by
      rw [← add_mul, hsum, one_mul]
    rw [hcoord]
    nlinarith
  · have hxhi : x i ≤ b i := (hx i).2
    have hyhi : y i ≤ b i := (hy i).2
    have hμhi : μ * x i ≤ μ * b i :=
      mul_le_mul_of_nonneg_left hxhi hμ
    have hνhi : ν * y i ≤ ν * b i :=
      mul_le_mul_of_nonneg_left hyhi hν
    have hscale : μ * b i + ν * b i = b i := by
      rw [← add_mul, hsum, one_mul]
    rw [hcoord]
    nlinarith

/--
The topological interior of a finite coordinate box is contained in its strict
coordinate interior.  This is the direction needed to upgrade the replay
lower bound from the source-shaped strict-box predicate to `interior C`.
-/
theorem chewi625CoordinateBox_interior_subset_strict {d : ℕ}
    {a b : EuclideanSpace ℝ (Fin d)} :
    interior (chewi625CoordinateBox a b) ⊆
      chewi625StrictCoordinateBox a b := by
  intro x hx i
  have hnhds : chewi625CoordinateBox a b ∈ 𝓝 x :=
    mem_interior_iff_mem_nhds.mp hx
  rcases Metric.nhds_basis_closedBall.mem_iff.mp hnhds with
    ⟨ρ, hρ_pos, hρ_subset⟩
  constructor
  · by_contra hnot
    have hxi_le : x i ≤ a i := le_of_not_gt hnot
    let y : EuclideanSpace ℝ (Fin d) :=
      x + (-(ρ / 2)) • chewi621CoordinateBasis i
    have hy_ball : y ∈ Metric.closedBall x ρ := by
      rw [Metric.mem_closedBall, dist_eq_norm]
      have hsub : y - x = (-(ρ / 2)) • chewi621CoordinateBasis i := by
        simp [y]
      rw [hsub, norm_smul, chewi621CoordinateBasis_norm]
      have hnorm : ‖(-(ρ / 2) : ℝ)‖ = ρ / 2 := by
        rw [Real.norm_eq_abs, abs_neg, abs_of_pos (half_pos hρ_pos)]
      rw [hnorm]
      nlinarith
    have hy_box := hρ_subset hy_ball
    have hlow : a i ≤ y i := (hy_box i).1
    have hy_coord : y i = x i - ρ / 2 := by
      simp [y]
      ring
    rw [hy_coord] at hlow
    nlinarith
  · by_contra hnot
    have hbi_le : b i ≤ x i := le_of_not_gt hnot
    let y : EuclideanSpace ℝ (Fin d) :=
      x + (ρ / 2) • chewi621CoordinateBasis i
    have hy_ball : y ∈ Metric.closedBall x ρ := by
      rw [Metric.mem_closedBall, dist_eq_norm]
      have hsub : y - x = (ρ / 2) • chewi621CoordinateBasis i := by
        simp [y]
      rw [hsub, norm_smul, chewi621CoordinateBasis_norm]
      have hnorm : ‖(ρ / 2 : ℝ)‖ = ρ / 2 := by
        rw [Real.norm_eq_abs, abs_of_pos (half_pos hρ_pos)]
      rw [hnorm]
      nlinarith
    have hy_box := hρ_subset hy_ball
    have hupper : y i ≤ b i := (hy_box i).2
    have hy_coord : y i = x i + ρ / 2 := by
      simp [y]
    rw [hy_coord] at hupper
    nlinarith

/-- Separation-certificate interface for the feasibility resisting oracle. -/
def IsSeparationVector {E : Type*} [NormedAddCommGroup E] [InnerProductSpace ℝ E]
    (C : Set E) (x p : E) : Prop :=
  p ≠ 0 ∧ ∀ y ∈ C, inner ℝ p y ≤ inner ℝ p x

/-- A separator for a set is also a separator for every subset. -/
theorem IsSeparationVector.mono {E : Type*}
    [NormedAddCommGroup E] [InnerProductSpace ℝ E]
    {C D : Set E} {x p : E}
    (hsep : IsSeparationVector C x p) (hsub : D ⊆ C) :
    IsSeparationVector D x p :=
  ⟨hsep.1, fun y hy => hsep.2 y (hsub hy)⟩

/-- Coordinatewise midpoint of a box. -/
noncomputable def chewi625Midpoint {d : ℕ}
    (a b : EuclideanSpace ℝ (Fin d)) : EuclideanSpace ℝ (Fin d) :=
  WithLp.toLp 2 fun i : Fin d => (a i + b i) / 2

@[simp] theorem chewi625Midpoint_apply {d : ℕ}
    (a b : EuclideanSpace ℝ (Fin d)) (i : Fin d) :
    chewi625Midpoint a b i = (a i + b i) / 2 := by
  simp [chewi625Midpoint, PiLp.toLp_apply]

/-- Replace one coordinate of a finite Euclidean vector. -/
noncomputable def chewi625ReplaceCoord {d : ℕ}
    (v : EuclideanSpace ℝ (Fin d)) (i : Fin d) (t : ℝ) :
    EuclideanSpace ℝ (Fin d) :=
  WithLp.toLp 2 fun j : Fin d => if j = i then t else v j

@[simp] theorem chewi625ReplaceCoord_apply_same {d : ℕ}
    (v : EuclideanSpace ℝ (Fin d)) (i : Fin d) (t : ℝ) :
    chewi625ReplaceCoord v i t i = t := by
  simp [chewi625ReplaceCoord, PiLp.toLp_apply]

@[simp] theorem chewi625ReplaceCoord_apply_ne {d : ℕ}
    (v : EuclideanSpace ℝ (Fin d)) {i j : Fin d} (hji : j ≠ i) (t : ℝ) :
    chewi625ReplaceCoord v i t j = v j := by
  simp [chewi625ReplaceCoord, PiLp.toLp_apply, hji]

/--
Lower endpoint after the resisting half-box cut in coordinate `i`.  If the
query is on the lower side of the midpoint, keep the upper half.
-/
noncomputable def chewi625CutLower {d : ℕ}
    (a b x : EuclideanSpace ℝ (Fin d)) (i : Fin d) :
    EuclideanSpace ℝ (Fin d) :=
  if x i ≤ chewi625Midpoint a b i then
    chewi625ReplaceCoord a i (chewi625Midpoint a b i)
  else
    a

/--
Upper endpoint after the resisting half-box cut in coordinate `i`.  If the
query is on the upper side of the midpoint, keep the lower half.
-/
noncomputable def chewi625CutUpper {d : ℕ}
    (a b x : EuclideanSpace ℝ (Fin d)) (i : Fin d) :
    EuclideanSpace ℝ (Fin d) :=
  if x i ≤ chewi625Midpoint a b i then
    b
  else
    chewi625ReplaceCoord b i (chewi625Midpoint a b i)

/--
The separation vector returned by the resisting oracle for the half-box cut:
`-e_i` when the retained box is above the query, and `+e_i` when it is below.
-/
noncomputable def chewi625CutVector {d : ℕ}
    (a b x : EuclideanSpace ℝ (Fin d)) (i : Fin d) :
    EuclideanSpace ℝ (Fin d) :=
  if x i ≤ chewi625Midpoint a b i then
    -chewi621CoordinateBasis i
  else
    chewi621CoordinateBasis i

/-- The resisting separation vector is nonzero. -/
theorem chewi625CutVector_norm {d : ℕ}
    (a b x : EuclideanSpace ℝ (Fin d)) (i : Fin d) :
    ‖chewi625CutVector a b x i‖ = 1 := by
  by_cases h : x i ≤ chewi625Midpoint a b i
  · have h' : x i ≤ (a i + b i) / 2 := by
      simpa using h
    simp [chewi625CutVector, chewi625Midpoint, h', chewi621CoordinateBasis_norm]
  · have h' : ¬ x i ≤ (a i + b i) / 2 := by
      simpa using h
    simp [chewi625CutVector, chewi625Midpoint, h', chewi621CoordinateBasis_norm]

theorem chewi625CutVector_ne_zero {d : ℕ}
    (a b x : EuclideanSpace ℝ (Fin d)) (i : Fin d) :
    chewi625CutVector a b x i ≠ 0 := by
  intro hzero
  have hnorm := chewi625CutVector_norm a b x i
  rw [hzero, norm_zero] at hnorm
  norm_num at hnorm

/--
After the resisting oracle halves the box, the queried point lies outside the
strict coordinate interior of the retained box.
-/
theorem chewi625_query_not_mem_strict_cut_box {d : ℕ}
    (a b x : EuclideanSpace ℝ (Fin d)) (i : Fin d) :
    x ∉ chewi625StrictCoordinateBox
      (chewi625CutLower a b x i) (chewi625CutUpper a b x i) := by
  intro hx
  by_cases h : x i ≤ chewi625Midpoint a b i
  · have hleft : chewi625CutLower a b x i i = chewi625Midpoint a b i := by
      have h' : x i ≤ (a i + b i) / 2 := by
        simpa using h
      simp [chewi625CutLower, chewi625Midpoint, h']
    have hxleft := (hx i).1
    rw [hleft] at hxleft
    exact (not_lt_of_ge h) hxleft
  · have hright : chewi625CutUpper a b x i i = chewi625Midpoint a b i := by
      have h' : ¬ x i ≤ (a i + b i) / 2 := by
        simpa using h
      simp [chewi625CutUpper, chewi625Midpoint, h']
    have hxright := (hx i).2
    rw [hright] at hxright
    exact (not_lt_of_ge (le_of_lt (lt_of_not_ge h))) hxright

/--
The resisting vector is a valid separation certificate for the retained
half-box: every point in the new box lies on the oracle side of the query.
-/
theorem chewi625CutVector_separates_cut_box {d : ℕ}
    (a b x : EuclideanSpace ℝ (Fin d)) (i : Fin d) :
    ∀ y ∈ chewi625CoordinateBox
        (chewi625CutLower a b x i) (chewi625CutUpper a b x i),
      inner ℝ (chewi625CutVector a b x i) y ≤
        inner ℝ (chewi625CutVector a b x i) x := by
  intro y hy
  by_cases h : x i ≤ chewi625Midpoint a b i
  · have hyi : chewi625Midpoint a b i ≤ y i := by
      have hbox := (hy i).1
      have h' : x i ≤ (a i + b i) / 2 := by
        simpa using h
      simpa [chewi625CutLower, chewi625Midpoint, h'] using hbox
    have hp : chewi625CutVector a b x i = -chewi621CoordinateBasis i := by
      have h' : x i ≤ (a i + b i) / 2 := by
        simpa using h
      simp [chewi625CutVector, chewi625Midpoint, h']
    calc
      inner ℝ (chewi625CutVector a b x i) y = -y i := by
        rw [hp, inner_neg_left, chewi621CoordinateBasis_inner]
      _ ≤ -x i := by nlinarith
      _ = inner ℝ (chewi625CutVector a b x i) x := by
        rw [hp, inner_neg_left, chewi621CoordinateBasis_inner]
  · have hyi : y i ≤ chewi625Midpoint a b i := by
      have hbox := (hy i).2
      have h' : ¬ x i ≤ (a i + b i) / 2 := by
        simpa using h
      simpa [chewi625CutUpper, chewi625Midpoint, h'] using hbox
    have hmid_le_x : chewi625Midpoint a b i ≤ x i :=
      le_of_lt (lt_of_not_ge h)
    have hp : chewi625CutVector a b x i = chewi621CoordinateBasis i := by
      have h' : ¬ x i ≤ (a i + b i) / 2 := by
        simpa using h
      simp [chewi625CutVector, chewi625Midpoint, h']
    calc
      inner ℝ (chewi625CutVector a b x i) y = y i := by
        rw [hp, chewi621CoordinateBasis_inner]
      _ ≤ x i := by nlinarith
      _ = inner ℝ (chewi625CutVector a b x i) x := by
        rw [hp, chewi621CoordinateBasis_inner]

/-- Interface wrapper: the retained half-box has a valid nonzero separator. -/
theorem chewi625CutVector_isSeparationVector {d : ℕ}
    (a b x : EuclideanSpace ℝ (Fin d)) (i : Fin d) :
    IsSeparationVector
      (chewi625CoordinateBox
        (chewi625CutLower a b x i) (chewi625CutUpper a b x i))
      x (chewi625CutVector a b x i) :=
  ⟨chewi625CutVector_ne_zero a b x i,
    chewi625CutVector_separates_cut_box a b x i⟩

/-- The midpoint lies between the two endpoints in one coordinate. -/
theorem chewi625_left_le_midpoint {d : ℕ}
    {a b : EuclideanSpace ℝ (Fin d)} (hab : ∀ j : Fin d, a j ≤ b j)
    (i : Fin d) :
    a i ≤ chewi625Midpoint a b i := by
  simp [chewi625Midpoint]
  nlinarith [hab i]

theorem chewi625_midpoint_le_right {d : ℕ}
    {a b : EuclideanSpace ℝ (Fin d)} (hab : ∀ j : Fin d, a j ≤ b j)
    (i : Fin d) :
    chewi625Midpoint a b i ≤ b i := by
  simp [chewi625Midpoint]
  nlinarith [hab i]

/-- The retained lower endpoint is coordinatewise above the old lower endpoint. -/
theorem chewi625_le_cutLower {d : ℕ}
    {a b x : EuclideanSpace ℝ (Fin d)} (hab : ∀ j : Fin d, a j ≤ b j)
    (i j : Fin d) :
    a j ≤ chewi625CutLower a b x i j := by
  by_cases h : x i ≤ chewi625Midpoint a b i
  · have h' : x i ≤ (a i + b i) / 2 := by
      simpa using h
    by_cases hji : j = i
    · simpa [chewi625CutLower, chewi625Midpoint, h', hji] using
        chewi625_left_le_midpoint (a := a) (b := b) hab i
    · simp [chewi625CutLower, chewi625Midpoint, h', hji]
  · have h' : ¬ x i ≤ (a i + b i) / 2 := by
      simpa using h
    simp [chewi625CutLower, chewi625Midpoint, h']

/-- The retained upper endpoint is coordinatewise below the old upper endpoint. -/
theorem chewi625_cutUpper_le {d : ℕ}
    {a b x : EuclideanSpace ℝ (Fin d)} (hab : ∀ j : Fin d, a j ≤ b j)
    (i j : Fin d) :
    chewi625CutUpper a b x i j ≤ b j := by
  by_cases h : x i ≤ chewi625Midpoint a b i
  · have h' : x i ≤ (a i + b i) / 2 := by
      simpa using h
    simp [chewi625CutUpper, chewi625Midpoint, h']
  · have h' : ¬ x i ≤ (a i + b i) / 2 := by
      simpa using h
    by_cases hji : j = i
    · simpa [chewi625CutUpper, chewi625Midpoint, h', hji] using
        chewi625_midpoint_le_right (a := a) (b := b) hab i
    · simp [chewi625CutUpper, chewi625Midpoint, h', hji]

/-- The retained lower endpoint remains below the retained upper endpoint. -/
theorem chewi625_cutLower_le_cutUpper {d : ℕ}
    {a b x : EuclideanSpace ℝ (Fin d)} (hab : ∀ j : Fin d, a j ≤ b j)
    (i j : Fin d) :
    chewi625CutLower a b x i j ≤ chewi625CutUpper a b x i j := by
  by_cases h : x i ≤ chewi625Midpoint a b i
  · have h' : x i ≤ (a i + b i) / 2 := by
      simpa using h
    by_cases hji : j = i
    · simpa [chewi625CutLower, chewi625CutUpper, chewi625Midpoint, h', hji] using
        chewi625_midpoint_le_right (a := a) (b := b) hab i
    · simpa [chewi625CutLower, chewi625CutUpper, chewi625Midpoint, h', hji] using
        hab j
  · have h' : ¬ x i ≤ (a i + b i) / 2 := by
      simpa using h
    by_cases hji : j = i
    · simpa [chewi625CutLower, chewi625CutUpper, chewi625Midpoint, h', hji] using
        chewi625_left_le_midpoint (a := a) (b := b) hab i
    · simpa [chewi625CutLower, chewi625CutUpper, chewi625Midpoint, h', hji] using
        hab j

/-- The retained half-box is nested inside the previous box. -/
theorem chewi625_cut_box_subset {d : ℕ}
    {a b x : EuclideanSpace ℝ (Fin d)} (hab : ∀ j : Fin d, a j ≤ b j)
    (i : Fin d) :
    chewi625CoordinateBox
        (chewi625CutLower a b x i) (chewi625CutUpper a b x i) ⊆
      chewi625CoordinateBox a b := by
  intro y hy j
  exact ⟨(chewi625_le_cutLower (a := a) (b := b) (x := x) hab i j).trans (hy j).1,
    (hy j).2.trans (chewi625_cutUpper_le (a := a) (b := b) (x := x) hab i j)⟩

/-- The selected coordinate width is halved by the resisting cut. -/
theorem chewi625_cut_selected_width {d : ℕ}
    (a b x : EuclideanSpace ℝ (Fin d)) (i : Fin d) :
    chewi625CutUpper a b x i i - chewi625CutLower a b x i i =
      (b i - a i) / 2 := by
  by_cases h : x i ≤ chewi625Midpoint a b i
  · have h' : x i ≤ (a i + b i) / 2 := by
      simpa using h
    simp [chewi625CutUpper, chewi625CutLower, chewi625Midpoint, h']
    ring
  · have h' : ¬ x i ≤ (a i + b i) / 2 := by
      simpa using h
    simp [chewi625CutUpper, chewi625CutLower, chewi625Midpoint, h']
    ring

/-- Non-selected coordinate widths are unchanged by the resisting cut. -/
theorem chewi625_cut_unselected_width {d : ℕ}
    (a b x : EuclideanSpace ℝ (Fin d)) {i j : Fin d} (hji : j ≠ i) :
    chewi625CutUpper a b x i j - chewi625CutLower a b x i j =
      b j - a j := by
  by_cases h : x i ≤ chewi625Midpoint a b i
  · have h' : x i ≤ (a i + b i) / 2 := by
      simpa using h
    simp [chewi625CutUpper, chewi625CutLower, chewi625Midpoint, h', hji]
  · have h' : ¬ x i ≤ (a i + b i) / 2 := by
      simpa using h
    simp [chewi625CutUpper, chewi625CutLower, chewi625Midpoint, h', hji]

/--
If every coordinate half-side of a box around `center` is at least `rho`, then
the Euclidean closed ball of radius `rho` around `center` is contained in the
coordinate box.  This is the reusable ball-containment primitive in Definition
6.24 / Theorem 6.25.
-/
theorem chewi625_closedBall_subset_coordinateBox {d : ℕ}
    {a b center : EuclideanSpace ℝ (Fin d)} {rho : ℝ}
    (hleft : ∀ i : Fin d, rho ≤ center i - a i)
    (hright : ∀ i : Fin d, rho ≤ b i - center i) :
    Metric.closedBall center rho ⊆ chewi625CoordinateBox a b := by
  intro y hy i
  have hynorm : ‖y - center‖ ≤ rho := by
    simpa [Metric.mem_closedBall, dist_eq_norm] using hy
  have hcoord_abs : |y i - center i| ≤ rho := by
    have hinner_abs :=
      abs_real_inner_le_norm (chewi621CoordinateBasis i) (y - center)
    have hcoord :
        inner ℝ (chewi621CoordinateBasis i) (y - center) = y i - center i := by
      rw [chewi621CoordinateBasis_inner]
      simp
    calc
      |y i - center i| =
          |inner ℝ (chewi621CoordinateBasis i) (y - center)| := by rw [hcoord]
      _ ≤ ‖chewi621CoordinateBasis i‖ * ‖y - center‖ := hinner_abs
      _ = ‖y - center‖ := by
            rw [chewi621CoordinateBasis_norm]
            ring
      _ ≤ rho := hynorm
  have hlow_coord : -rho ≤ y i - center i := (abs_le.mp hcoord_abs).1
  have hhigh_coord : y i - center i ≤ rho := (abs_le.mp hcoord_abs).2
  constructor <;> nlinarith [hleft i, hright i]

/--
A box with a coordinate side shorter than `2 * eps` cannot contain a Euclidean
closed ball of radius `eps`.  This is the geometric obstruction behind the
feasibility lower bound once repeated coordinate cuts make some side too short.
-/
theorem chewi625_no_closedBall_subset_of_short_side {d : ℕ}
    {a b : EuclideanSpace ℝ (Fin d)} {eps : ℝ} (heps : 0 < eps)
    {i : Fin d} (hside : b i - a i < 2 * eps) :
    ¬ ∃ center : EuclideanSpace ℝ (Fin d),
      Metric.closedBall center eps ⊆ chewi625CoordinateBox a b := by
  rintro ⟨center, hsubset⟩
  let e := chewi621CoordinateBasis i
  let yplus : EuclideanSpace ℝ (Fin d) := center + eps • e
  let yminus : EuclideanSpace ℝ (Fin d) := center + (-eps) • e
  have hdist_plus : dist yplus center = eps := by
    rw [dist_eq_norm]
    have hsub : yplus - center = eps • e := by
      simp [yplus]
    rw [hsub, norm_smul, chewi621CoordinateBasis_norm]
    rw [Real.norm_of_nonneg heps.le]
    ring
  have hdist_minus : dist yminus center = eps := by
    rw [dist_eq_norm]
    have hsub : yminus - center = (-eps) • e := by
      simp [yminus]
    rw [hsub, norm_smul, chewi621CoordinateBasis_norm]
    have hneg_norm : ‖(-eps : ℝ)‖ = eps := by
      rw [Real.norm_eq_abs, abs_neg, abs_of_pos heps]
    rw [hneg_norm]
    ring
  have hyplus_mem : yplus ∈ Metric.closedBall center eps := by
    simp [Metric.mem_closedBall, hdist_plus]
  have hyminus_mem : yminus ∈ Metric.closedBall center eps := by
    simp [Metric.mem_closedBall, hdist_minus]
  have hplus_upper : center i + eps ≤ b i := by
    have hbox := (hsubset hyplus_mem i).2
    simpa [yplus, e] using hbox
  have hminus_lower : a i + eps ≤ center i := by
    have hbox := (hsubset hyminus_mem i).1
    simpa [yminus, e] using hbox
  nlinarith

/-- Constant finite Euclidean vector, used for the initial cube. -/
noncomputable def chewi625ConstVec {d : ℕ} (c : ℝ) :
    EuclideanSpace ℝ (Fin d) :=
  WithLp.toLp 2 fun _i : Fin d => c

@[simp] theorem chewi625ConstVec_apply {d : ℕ} (c : ℝ) (i : Fin d) :
    chewi625ConstVec (d := d) c i = c := by
  simp [chewi625ConstVec, PiLp.toLp_apply]

/-- Chewi's cyclic coordinate schedule for the feasibility resisting oracle. -/
def chewi625CycleCoord {d : ℕ} [NeZero d] (n : ℕ) : Fin d :=
  ⟨n % d, Nat.mod_lt n (Nat.pos_of_neZero d)⟩

@[simp] theorem chewi625CycleCoord_val {d : ℕ} [NeZero d] (n : ℕ) :
    (chewi625CycleCoord (d := d) n).1 = n % d := rfl

/--
Recursive lower/upper endpoints of the resisting box.  At step `n`, the query
`x n` cuts coordinate `n % d`.
-/
noncomputable def chewi625BoxState {d : ℕ} [NeZero d]
    (R : ℝ) (x : ℕ -> EuclideanSpace ℝ (Fin d)) :
    ℕ -> EuclideanSpace ℝ (Fin d) × EuclideanSpace ℝ (Fin d)
  | 0 => (chewi625ConstVec (d := d) (-R), chewi625ConstVec (d := d) R)
  | n + 1 =>
      let state := chewi625BoxState R x n
      let a := state.1
      let b := state.2
      let i := chewi625CycleCoord (d := d) n
      (chewi625CutLower a b (x n) i, chewi625CutUpper a b (x n) i)

noncomputable def chewi625BoxLower {d : ℕ} [NeZero d]
    (R : ℝ) (x : ℕ -> EuclideanSpace ℝ (Fin d)) (n : ℕ) :
    EuclideanSpace ℝ (Fin d) :=
  (chewi625BoxState (d := d) R x n).1

noncomputable def chewi625BoxUpper {d : ℕ} [NeZero d]
    (R : ℝ) (x : ℕ -> EuclideanSpace ℝ (Fin d)) (n : ℕ) :
    EuclideanSpace ℝ (Fin d) :=
  (chewi625BoxState (d := d) R x n).2

@[simp] theorem chewi625BoxLower_zero {d : ℕ} [NeZero d]
    (R : ℝ) (x : ℕ -> EuclideanSpace ℝ (Fin d)) :
    chewi625BoxLower (d := d) R x 0 = chewi625ConstVec (d := d) (-R) := rfl

@[simp] theorem chewi625BoxUpper_zero {d : ℕ} [NeZero d]
    (R : ℝ) (x : ℕ -> EuclideanSpace ℝ (Fin d)) :
    chewi625BoxUpper (d := d) R x 0 = chewi625ConstVec (d := d) R := rfl

@[simp] theorem chewi625BoxLower_zero_apply {d : ℕ} [NeZero d]
    (R : ℝ) (x : ℕ -> EuclideanSpace ℝ (Fin d)) (i : Fin d) :
    chewi625BoxLower (d := d) R x 0 i = -R := by
  simp [chewi625BoxLower, chewi625BoxState]

@[simp] theorem chewi625BoxUpper_zero_apply {d : ℕ} [NeZero d]
    (R : ℝ) (x : ℕ -> EuclideanSpace ℝ (Fin d)) (i : Fin d) :
    chewi625BoxUpper (d := d) R x 0 i = R := by
  simp [chewi625BoxUpper, chewi625BoxState]

@[simp] theorem chewi625BoxLower_succ {d : ℕ} [NeZero d]
    (R : ℝ) (x : ℕ -> EuclideanSpace ℝ (Fin d)) (n : ℕ) :
    chewi625BoxLower (d := d) R x (n + 1) =
      chewi625CutLower (chewi625BoxLower (d := d) R x n)
        (chewi625BoxUpper (d := d) R x n) (x n)
        (chewi625CycleCoord (d := d) n) := by
  rfl

@[simp] theorem chewi625BoxUpper_succ {d : ℕ} [NeZero d]
    (R : ℝ) (x : ℕ -> EuclideanSpace ℝ (Fin d)) (n : ℕ) :
    chewi625BoxUpper (d := d) R x (n + 1) =
      chewi625CutUpper (chewi625BoxLower (d := d) R x n)
        (chewi625BoxUpper (d := d) R x n) (x n)
        (chewi625CycleCoord (d := d) n) := by
  rfl

/-- Every recursive resisting box has ordered endpoints. -/
theorem chewi625BoxState_ordered {d : ℕ} [NeZero d]
    {R : ℝ} (hR_nonneg : 0 ≤ R)
    (x : ℕ -> EuclideanSpace ℝ (Fin d)) :
    ∀ n, ∀ i : Fin d,
      chewi625BoxLower (d := d) R x n i ≤
        chewi625BoxUpper (d := d) R x n i := by
  intro n
  induction n with
  | zero =>
      intro i
      simp
      nlinarith
  | succ n ih =>
      intro j
      simpa using
        chewi625_cutLower_le_cutUpper
          (a := chewi625BoxLower (d := d) R x n)
          (b := chewi625BoxUpper (d := d) R x n)
          (x := x n) ih (chewi625CycleCoord (d := d) n) j

/-- Step `n` returns a valid separator for the retained recursive box. -/
theorem chewi625BoxState_step_isSeparationVector {d : ℕ} [NeZero d]
    (R : ℝ) (x : ℕ -> EuclideanSpace ℝ (Fin d)) (n : ℕ) :
    IsSeparationVector
      (chewi625CoordinateBox
        (chewi625BoxLower (d := d) R x (n + 1))
        (chewi625BoxUpper (d := d) R x (n + 1)))
      (x n)
      (chewi625CutVector
        (chewi625BoxLower (d := d) R x n)
        (chewi625BoxUpper (d := d) R x n) (x n)
        (chewi625CycleCoord (d := d) n)) := by
  simpa using
    chewi625CutVector_isSeparationVector
      (chewi625BoxLower (d := d) R x n)
      (chewi625BoxUpper (d := d) R x n) (x n)
      (chewi625CycleCoord (d := d) n)

/-- The query at step `n` is not in the strict interior of the retained box. -/
theorem chewi625BoxState_query_not_mem_next_strict_box {d : ℕ} [NeZero d]
    (R : ℝ) (x : ℕ -> EuclideanSpace ℝ (Fin d)) (n : ℕ) :
    x n ∉ chewi625StrictCoordinateBox
      (chewi625BoxLower (d := d) R x (n + 1))
      (chewi625BoxUpper (d := d) R x (n + 1)) := by
  simpa using
    chewi625_query_not_mem_strict_cut_box
      (chewi625BoxLower (d := d) R x n)
      (chewi625BoxUpper (d := d) R x n) (x n)
      (chewi625CycleCoord (d := d) n)

/-- Each recursive box is nested in the previous one. -/
theorem chewi625BoxState_step_subset {d : ℕ} [NeZero d]
    {R : ℝ} (hR_nonneg : 0 ≤ R)
    (x : ℕ -> EuclideanSpace ℝ (Fin d)) (n : ℕ) :
    chewi625CoordinateBox
        (chewi625BoxLower (d := d) R x (n + 1))
        (chewi625BoxUpper (d := d) R x (n + 1)) ⊆
      chewi625CoordinateBox
        (chewi625BoxLower (d := d) R x n)
        (chewi625BoxUpper (d := d) R x n) := by
  simpa using
    chewi625_cut_box_subset
      (a := chewi625BoxLower (d := d) R x n)
      (b := chewi625BoxUpper (d := d) R x n)
      (x := x n)
      (chewi625BoxState_ordered (d := d) hR_nonneg x n)
      (chewi625CycleCoord (d := d) n)

/-- Selected-coordinate width update for the recursive resisting box. -/
theorem chewi625BoxState_selected_width_succ {d : ℕ} [NeZero d]
    (R : ℝ) (x : ℕ -> EuclideanSpace ℝ (Fin d)) (n : ℕ) :
    chewi625BoxUpper (d := d) R x (n + 1) (chewi625CycleCoord (d := d) n) -
        chewi625BoxLower (d := d) R x (n + 1) (chewi625CycleCoord (d := d) n) =
      (chewi625BoxUpper (d := d) R x n (chewi625CycleCoord (d := d) n) -
          chewi625BoxLower (d := d) R x n (chewi625CycleCoord (d := d) n)) / 2 := by
  simpa using
    chewi625_cut_selected_width
      (chewi625BoxLower (d := d) R x n)
      (chewi625BoxUpper (d := d) R x n) (x n)
      (chewi625CycleCoord (d := d) n)

/-- Nonselected-coordinate widths are unchanged in one recursive step. -/
theorem chewi625BoxState_unselected_width_succ {d : ℕ} [NeZero d]
    (R : ℝ) (x : ℕ -> EuclideanSpace ℝ (Fin d)) {n : ℕ} {j : Fin d}
    (hjn : j ≠ chewi625CycleCoord (d := d) n) :
    chewi625BoxUpper (d := d) R x (n + 1) j -
        chewi625BoxLower (d := d) R x (n + 1) j =
      chewi625BoxUpper (d := d) R x n j -
        chewi625BoxLower (d := d) R x n j := by
  simpa using
    chewi625_cut_unselected_width
      (chewi625BoxLower (d := d) R x n)
      (chewi625BoxUpper (d := d) R x n) (x n) hjn

/-- Coordinate side width of the recursive resisting box. -/
noncomputable def chewi625BoxWidth {d : ℕ} [NeZero d]
    (R : ℝ) (x : ℕ -> EuclideanSpace ℝ (Fin d)) (n : ℕ) (i : Fin d) : ℝ :=
  chewi625BoxUpper (d := d) R x n i -
    chewi625BoxLower (d := d) R x n i

@[simp] theorem chewi625BoxWidth_zero {d : ℕ} [NeZero d]
    (R : ℝ) (x : ℕ -> EuclideanSpace ℝ (Fin d)) (i : Fin d) :
    chewi625BoxWidth (d := d) R x 0 i = 2 * R := by
  simp [chewi625BoxWidth]
  ring

/-- Width form of the selected-coordinate update. -/
theorem chewi625BoxWidth_selected_succ {d : ℕ} [NeZero d]
    (R : ℝ) (x : ℕ -> EuclideanSpace ℝ (Fin d)) (n : ℕ) :
    chewi625BoxWidth (d := d) R x (n + 1) (chewi625CycleCoord (d := d) n) =
      chewi625BoxWidth (d := d) R x n (chewi625CycleCoord (d := d) n) / 2 := by
  simpa [chewi625BoxWidth] using
    chewi625BoxState_selected_width_succ (d := d) R x n

/-- Width form of the nonselected-coordinate update. -/
theorem chewi625BoxWidth_unselected_succ {d : ℕ} [NeZero d]
    (R : ℝ) (x : ℕ -> EuclideanSpace ℝ (Fin d)) {n : ℕ} {j : Fin d}
    (hjn : j ≠ chewi625CycleCoord (d := d) n) :
    chewi625BoxWidth (d := d) R x (n + 1) j =
      chewi625BoxWidth (d := d) R x n j := by
  simpa [chewi625BoxWidth] using
    chewi625BoxState_unselected_width_succ (d := d) R x hjn

/-- If the cyclic schedule selects `j` at step `n`, then `j`'s width halves. -/
theorem chewi625BoxWidth_succ_of_cycleCoord_eq {d : ℕ} [NeZero d]
    (R : ℝ) (x : ℕ -> EuclideanSpace ℝ (Fin d)) {n : ℕ} {j : Fin d}
    (hjn : chewi625CycleCoord (d := d) n = j) :
    chewi625BoxWidth (d := d) R x (n + 1) j =
      chewi625BoxWidth (d := d) R x n j / 2 := by
  rw [← hjn]
  exact chewi625BoxWidth_selected_succ (d := d) R x n

/-- If the cyclic schedule does not select `j` at step `n`, then `j`'s width is unchanged. -/
theorem chewi625BoxWidth_succ_of_cycleCoord_ne {d : ℕ} [NeZero d]
    (R : ℝ) (x : ℕ -> EuclideanSpace ℝ (Fin d)) {n : ℕ} {j : Fin d}
    (hjn : chewi625CycleCoord (d := d) n ≠ j) :
    chewi625BoxWidth (d := d) R x (n + 1) j =
      chewi625BoxWidth (d := d) R x n j := by
  exact chewi625BoxWidth_unselected_succ (d := d) R x (Ne.symm hjn)

/-- In the cyclic schedule, coordinate `j` is selected at every step `j + m*d`. -/
theorem chewi625CycleCoord_add_mul_eq {d : ℕ} [NeZero d]
    (j : Fin d) (m : ℕ) :
    chewi625CycleCoord (d := d) ((j : ℕ) + m * d) = j := by
  ext
  simp [chewi625CycleCoord, Nat.mod_eq_of_lt j.is_lt]

/-- Width halving at the explicit cyclic hit time `j + m*d`. -/
theorem chewi625BoxWidth_succ_add_mul_self {d : ℕ} [NeZero d]
    (R : ℝ) (x : ℕ -> EuclideanSpace ℝ (Fin d)) (j : Fin d) (m : ℕ) :
    chewi625BoxWidth (d := d) R x (((j : ℕ) + m * d) + 1) j =
      chewi625BoxWidth (d := d) R x ((j : ℕ) + m * d) j / 2 := by
  exact
    chewi625BoxWidth_succ_of_cycleCoord_eq
      (d := d) R x (n := (j : ℕ) + m * d) (j := j)
      (chewi625CycleCoord_add_mul_eq (d := d) j m)

/-- A box containing an `eps`-ball has every coordinate width at least `2 * eps`. -/
theorem chewi625_side_ge_two_eps_of_closedBall_subset {d : ℕ}
    {a b : EuclideanSpace ℝ (Fin d)} {eps : ℝ} (heps : 0 < eps)
    (hball : ∃ center : EuclideanSpace ℝ (Fin d),
      Metric.closedBall center eps ⊆ chewi625CoordinateBox a b)
    (i : Fin d) :
    2 * eps ≤ b i - a i := by
  by_contra hnot
  have hlt : b i - a i < 2 * eps := lt_of_not_ge hnot
  exact
    (chewi625_no_closedBall_subset_of_short_side
      (d := d) (a := a) (b := b) heps (i := i) hlt) hball

/-- Recursive-box version of the necessary side-width condition for containing an `eps`-ball. -/
theorem chewi625BoxWidth_ge_two_eps_of_closedBall_subset {d : ℕ} [NeZero d]
    {R eps : ℝ} (heps : 0 < eps)
    {x : ℕ -> EuclideanSpace ℝ (Fin d)} {n : ℕ}
    (hball : ∃ center : EuclideanSpace ℝ (Fin d),
      Metric.closedBall center eps ⊆
        chewi625CoordinateBox
          (chewi625BoxLower (d := d) R x n)
          (chewi625BoxUpper (d := d) R x n))
    (i : Fin d) :
    2 * eps ≤ chewi625BoxWidth (d := d) R x n i := by
  simpa [chewi625BoxWidth] using
    chewi625_side_ge_two_eps_of_closedBall_subset
      (d := d) heps hball i

/-- Recursive-box obstruction: a side shorter than `2 * eps` rules out an `eps`-ball. -/
theorem chewi625BoxState_no_closedBall_subset_of_width_lt {d : ℕ} [NeZero d]
    {R eps : ℝ} (heps : 0 < eps)
    {x : ℕ -> EuclideanSpace ℝ (Fin d)} {n : ℕ} {i : Fin d}
    (hwidth : chewi625BoxWidth (d := d) R x n i < 2 * eps) :
    ¬ ∃ center : EuclideanSpace ℝ (Fin d),
      Metric.closedBall center eps ⊆
        chewi625CoordinateBox
          (chewi625BoxLower (d := d) R x n)
          (chewi625BoxUpper (d := d) R x n) := by
  intro hball
  have hge :=
    chewi625BoxWidth_ge_two_eps_of_closedBall_subset
      (d := d) (R := R) heps (x := x) (n := n) hball i
  nlinarith

/--
If a coordinate is not selected over a block of steps, its recursive box width
is unchanged across that block.
-/
theorem chewi625BoxWidth_add_eq_of_no_cycle_hits {d : ℕ} [NeZero d]
    (R : ℝ) (x : ℕ -> EuclideanSpace ℝ (Fin d))
    (j : Fin d) (n : ℕ) :
    ∀ l : ℕ,
      (∀ t, t < l -> chewi625CycleCoord (d := d) (n + t) ≠ j) ->
      chewi625BoxWidth (d := d) R x (n + l) j =
        chewi625BoxWidth (d := d) R x n j := by
  intro l
  induction l with
  | zero =>
      intro _hno
      simp
  | succ l ih =>
      intro hno
      have hlast :
          chewi625CycleCoord (d := d) (n + l) ≠ j :=
        hno l (Nat.lt_succ_self l)
      have hno' :
          ∀ t, t < l -> chewi625CycleCoord (d := d) (n + t) ≠ j := by
        intro t ht
        exact hno t (Nat.lt_trans ht (Nat.lt_succ_self l))
      have hstep :
          chewi625BoxWidth (d := d) R x ((n + l) + 1) j =
            chewi625BoxWidth (d := d) R x (n + l) j :=
        chewi625BoxWidth_succ_of_cycleCoord_ne
          (d := d) R x (n := n + l) (j := j) hlast
      have hidx : n + (l + 1) = (n + l) + 1 := by omega
      rw [hidx, hstep, ih hno']

/-- A full cycle selects coordinate `j` exactly at offset `j`. -/
theorem chewi625CycleCoord_mul_add_eq {d : ℕ} [NeZero d]
    (j : Fin d) (m : ℕ) :
    chewi625CycleCoord (d := d) (m * d + (j : ℕ)) = j := by
  simpa [Nat.add_comm] using chewi625CycleCoord_add_mul_eq (d := d) j m

/-- Before offset `j` in a cycle, the cyclic schedule has not yet selected `j`. -/
theorem chewi625CycleCoord_mul_add_ne_of_lt {d : ℕ} [NeZero d]
    (j : Fin d) {m t : ℕ} (ht : t < j.1) :
    chewi625CycleCoord (d := d) (m * d + t) ≠ j := by
  intro h
  have hval := congrArg Fin.val h
  have ht_d : t < d := lt_trans ht j.is_lt
  simp [chewi625CycleCoord, Nat.mod_eq_of_lt ht_d] at hval
  omega

/-- After offset `j` in a cycle, the remaining offsets do not select `j`. -/
theorem chewi625CycleCoord_after_mul_add_ne_of_lt {d : ℕ} [NeZero d]
    (j : Fin d) {m t : ℕ} (ht : t < d - (j.1 + 1)) :
    chewi625CycleCoord (d := d) (m * d + (j.1 + 1 + t)) ≠ j := by
  intro h
  have hval := congrArg Fin.val h
  have hoff_lt_d : j.1 + 1 + t < d := by
    omega
  simp [chewi625CycleCoord, Nat.mod_eq_of_lt hoff_lt_d] at hval
  omega

/--
One complete cycle halves every coordinate width exactly once.  This is the
core side-length recurrence in Chewi's proof of Theorem 6.25.
-/
theorem chewi625BoxWidth_full_cycle_succ {d : ℕ} [NeZero d]
    (R : ℝ) (x : ℕ -> EuclideanSpace ℝ (Fin d)) (j : Fin d) (m : ℕ) :
    chewi625BoxWidth (d := d) R x ((m + 1) * d) j =
      chewi625BoxWidth (d := d) R x (m * d) j / 2 := by
  have hpre :
      chewi625BoxWidth (d := d) R x (m * d + j.1) j =
        chewi625BoxWidth (d := d) R x (m * d) j := by
    simpa using
      chewi625BoxWidth_add_eq_of_no_cycle_hits
        (d := d) R x j (m * d) j.1
        (by
          intro t ht
          exact chewi625CycleCoord_mul_add_ne_of_lt (d := d) j (m := m) ht)
  have hhit :
      chewi625BoxWidth (d := d) R x ((m * d + j.1) + 1) j =
        chewi625BoxWidth (d := d) R x (m * d + j.1) j / 2 := by
    exact
      chewi625BoxWidth_succ_of_cycleCoord_eq
        (d := d) R x (n := m * d + j.1) (j := j)
        (chewi625CycleCoord_mul_add_eq (d := d) j m)
  let afterLen : ℕ := d - (j.1 + 1)
  have hpost :
      chewi625BoxWidth (d := d) R x ((m * d + j.1 + 1) + afterLen) j =
        chewi625BoxWidth (d := d) R x (m * d + j.1 + 1) j := by
    simpa [afterLen, Nat.add_assoc] using
      chewi625BoxWidth_add_eq_of_no_cycle_hits
        (d := d) R x j (m * d + j.1 + 1) afterLen
        (by
          intro t ht
          simpa [Nat.add_assoc] using
            chewi625CycleCoord_after_mul_add_ne_of_lt
              (d := d) j (m := m) ht)
  have hidx_left :
      ((m * d + j.1 + 1) + afterLen) = (m + 1) * d := by
    have hj_lt : j.1 < d := j.is_lt
    have htail : j.1 + 1 + afterLen = d := by
      dsimp [afterLen]
      omega
    calc
      ((m * d + j.1 + 1) + afterLen)
          = m * d + (j.1 + 1 + afterLen) := by omega
      _ = m * d + d := by rw [htail]
      _ = (m + 1) * d := by ring
  rw [← hidx_left, hpost, hhit, hpre]

/-- Closed form after `m` complete coordinate cycles. -/
theorem chewi625BoxWidth_full_cycles {d : ℕ} [NeZero d]
    (R : ℝ) (x : ℕ -> EuclideanSpace ℝ (Fin d)) (j : Fin d) :
    ∀ m : ℕ,
      chewi625BoxWidth (d := d) R x (m * d) j =
        (2 * R) / (2 : ℝ) ^ m := by
  intro m
  induction m with
  | zero =>
      simp [chewi625BoxWidth]
      ring
  | succ m ih =>
      rw [chewi625BoxWidth_full_cycle_succ (d := d) R x j m, ih]
      ring_nf

/-- If the full-cycle width is below `2 * eps`, the recursive box cannot contain an `eps`-ball. -/
theorem chewi625BoxState_no_closedBall_subset_of_full_cycles_width_lt {d : ℕ}
    [NeZero d] {R eps : ℝ} (heps : 0 < eps)
    {x : ℕ -> EuclideanSpace ℝ (Fin d)} {m : ℕ} (j : Fin d)
    (hwidth : (2 * R) / (2 : ℝ) ^ m < 2 * eps) :
    ¬ ∃ center : EuclideanSpace ℝ (Fin d),
      Metric.closedBall center eps ⊆
        chewi625CoordinateBox
          (chewi625BoxLower (d := d) R x (m * d))
          (chewi625BoxUpper (d := d) R x (m * d)) := by
  have hwidth_box :
      chewi625BoxWidth (d := d) R x (m * d) j < 2 * eps := by
    rw [chewi625BoxWidth_full_cycles (d := d) R x j m]
    exact hwidth
  exact
    chewi625BoxState_no_closedBall_subset_of_width_lt
      (d := d) (R := R) heps (x := x) (n := m * d) (i := j) hwidth_box

/-- Any `eps`-ball inside the box after `m` full cycles forces the source scalar width bound. -/
theorem chewi625_full_cycles_width_ge_two_eps_of_closedBall_subset {d : ℕ}
    [NeZero d] {R eps : ℝ} (heps : 0 < eps)
    {x : ℕ -> EuclideanSpace ℝ (Fin d)} {m : ℕ}
    (hball : ∃ center : EuclideanSpace ℝ (Fin d),
      Metric.closedBall center eps ⊆
        chewi625CoordinateBox
          (chewi625BoxLower (d := d) R x (m * d))
          (chewi625BoxUpper (d := d) R x (m * d)))
    (j : Fin d) :
    2 * eps ≤ (2 * R) / (2 : ℝ) ^ m := by
  have hge :=
    chewi625BoxWidth_ge_two_eps_of_closedBall_subset
      (d := d) (R := R) heps (x := x) (n := m * d) hball j
  rw [chewi625BoxWidth_full_cycles (d := d) R x j m] at hge
  exact hge

/-- Recursive resisting boxes are nested over any finite block of later steps. -/
theorem chewi625BoxState_subset_add {d : ℕ} [NeZero d]
    {R : ℝ} (hR_nonneg : 0 ≤ R)
    (x : ℕ -> EuclideanSpace ℝ (Fin d)) (n : ℕ) :
    ∀ k : ℕ,
      chewi625CoordinateBox
          (chewi625BoxLower (d := d) R x (n + k))
          (chewi625BoxUpper (d := d) R x (n + k)) ⊆
        chewi625CoordinateBox
          (chewi625BoxLower (d := d) R x n)
          (chewi625BoxUpper (d := d) R x n) := by
  intro k
  induction k with
  | zero =>
      intro y hy
      simpa using hy
  | succ k ih =>
      intro y hy
      have hidx : n + (k + 1) = (n + k) + 1 := by omega
      have hstep :
          y ∈ chewi625CoordinateBox
              (chewi625BoxLower (d := d) R x (n + k))
              (chewi625BoxUpper (d := d) R x (n + k)) := by
        exact
          chewi625BoxState_step_subset
            (d := d) (R := R) hR_nonneg x (n + k)
            (by simpa [hidx] using hy)
      exact ih hstep

/-- Later recursive resisting boxes are nested inside earlier boxes. -/
theorem chewi625BoxState_subset_of_le {d : ℕ} [NeZero d]
    {R : ℝ} (hR_nonneg : 0 ≤ R)
    (x : ℕ -> EuclideanSpace ℝ (Fin d)) {n m : ℕ} (hnm : n ≤ m) :
    chewi625CoordinateBox
        (chewi625BoxLower (d := d) R x m)
        (chewi625BoxUpper (d := d) R x m) ⊆
      chewi625CoordinateBox
        (chewi625BoxLower (d := d) R x n)
        (chewi625BoxUpper (d := d) R x n) := by
  have hsubset :=
    chewi625BoxState_subset_add
      (d := d) (R := R) hR_nonneg x n (m - n)
  have hidx : n + (m - n) = m := Nat.add_sub_of_le hnm
  simpa [hidx] using hsubset

/-- The lower endpoint of an ordered recursive box belongs to that box. -/
theorem chewi625BoxLower_mem_coordinateBox {d : ℕ} [NeZero d]
    {R : ℝ} (hR_nonneg : 0 ≤ R)
    (x : ℕ -> EuclideanSpace ℝ (Fin d)) (n : ℕ) :
    chewi625BoxLower (d := d) R x n ∈
      chewi625CoordinateBox
        (chewi625BoxLower (d := d) R x n)
        (chewi625BoxUpper (d := d) R x n) := by
  intro i
  exact ⟨le_rfl, chewi625BoxState_ordered (d := d) hR_nonneg x n i⟩

/-- The upper endpoint of an ordered recursive box belongs to that box. -/
theorem chewi625BoxUpper_mem_coordinateBox {d : ℕ} [NeZero d]
    {R : ℝ} (hR_nonneg : 0 ≤ R)
    (x : ℕ -> EuclideanSpace ℝ (Fin d)) (n : ℕ) :
    chewi625BoxUpper (d := d) R x n ∈
      chewi625CoordinateBox
        (chewi625BoxLower (d := d) R x n)
        (chewi625BoxUpper (d := d) R x n) := by
  intro i
  exact ⟨chewi625BoxState_ordered (d := d) hR_nonneg x n i, le_rfl⟩

/-- Lower endpoints increase coordinatewise along the recursive box sequence. -/
theorem chewi625BoxLower_le_of_le {d : ℕ} [NeZero d]
    {R : ℝ} (hR_nonneg : 0 ≤ R)
    (x : ℕ -> EuclideanSpace ℝ (Fin d)) {n m : ℕ} (hnm : n ≤ m)
    (i : Fin d) :
    chewi625BoxLower (d := d) R x n i ≤
      chewi625BoxLower (d := d) R x m i := by
  have hsubset :=
    chewi625BoxState_subset_of_le
      (d := d) (R := R) hR_nonneg x hnm
  exact
    (hsubset
      (chewi625BoxLower_mem_coordinateBox
        (d := d) (R := R) hR_nonneg x m) i).1

/-- Upper endpoints decrease coordinatewise along the recursive box sequence. -/
theorem chewi625BoxUpper_le_of_le {d : ℕ} [NeZero d]
    {R : ℝ} (hR_nonneg : 0 ≤ R)
    (x : ℕ -> EuclideanSpace ℝ (Fin d)) {n m : ℕ} (hnm : n ≤ m)
    (i : Fin d) :
    chewi625BoxUpper (d := d) R x m i ≤
      chewi625BoxUpper (d := d) R x n i := by
  have hsubset :=
    chewi625BoxState_subset_of_le
      (d := d) (R := R) hR_nonneg x hnm
  exact
    (hsubset
      (chewi625BoxUpper_mem_coordinateBox
        (d := d) (R := R) hR_nonneg x m) i).2

/-- Strict interiors of later recursive boxes are nested in strict interiors of earlier boxes. -/
theorem chewi625StrictBoxState_subset_of_le {d : ℕ} [NeZero d]
    {R : ℝ} (hR_nonneg : 0 ≤ R)
    (x : ℕ -> EuclideanSpace ℝ (Fin d)) {n m : ℕ} (hnm : n ≤ m) :
    chewi625StrictCoordinateBox
        (chewi625BoxLower (d := d) R x m)
        (chewi625BoxUpper (d := d) R x m) ⊆
      chewi625StrictCoordinateBox
        (chewi625BoxLower (d := d) R x n)
        (chewi625BoxUpper (d := d) R x n) := by
  intro y hy i
  exact
    ⟨lt_of_le_of_lt
        (chewi625BoxLower_le_of_le
          (d := d) (R := R) hR_nonneg x hnm i)
        (hy i).1,
      lt_of_lt_of_le
        (hy i).2
        (chewi625BoxUpper_le_of_le
          (d := d) (R := R) hR_nonneg x hnm i)⟩

/--
Every previous query is excluded from the strict interior of the final
recursive box.  This is the main geometric replay fact for the deterministic
resisting oracle construction in Theorem 6.25.
-/
theorem chewi625BoxState_query_not_mem_final_strict_box {d : ℕ} [NeZero d]
    {R : ℝ} (hR_nonneg : 0 ≤ R)
    (x : ℕ -> EuclideanSpace ℝ (Fin d)) {n N : ℕ} (hnN : n < N) :
    x n ∉ chewi625StrictCoordinateBox
      (chewi625BoxLower (d := d) R x N)
      (chewi625BoxUpper (d := d) R x N) := by
  intro hx_final
  have hnext_le : n + 1 ≤ N := Nat.succ_le_of_lt hnN
  have hx_next :
      x n ∈ chewi625StrictCoordinateBox
        (chewi625BoxLower (d := d) R x (n + 1))
        (chewi625BoxUpper (d := d) R x (n + 1)) :=
    chewi625StrictBoxState_subset_of_le
      (d := d) (R := R) hR_nonneg x hnext_le hx_final
  exact chewi625BoxState_query_not_mem_next_strict_box (d := d) R x n hx_next

/-- The cut vector returned by the resisting oracle at step `n`. -/
noncomputable def chewi625ReturnedCutVector {d : ℕ} [NeZero d]
    (R : ℝ) (x : ℕ -> EuclideanSpace ℝ (Fin d)) (n : ℕ) :
    EuclideanSpace ℝ (Fin d) :=
  chewi625CutVector
    (chewi625BoxLower (d := d) R x n)
    (chewi625BoxUpper (d := d) R x n) (x n)
    (chewi625CycleCoord (d := d) n)

/--
Every returned resisting-oracle vector is a valid separator for the eventual
final box, not only for the immediate retained box.  This is the post-hoc
separator validity statement used in Chewi's deterministic replay argument.
-/
theorem chewi625ReturnedCutVector_isSeparationVector_final_box {d : ℕ}
    [NeZero d] {R : ℝ} (hR_nonneg : 0 ≤ R)
    (x : ℕ -> EuclideanSpace ℝ (Fin d)) {n N : ℕ} (hnN : n < N) :
    IsSeparationVector
      (chewi625CoordinateBox
        (chewi625BoxLower (d := d) R x N)
        (chewi625BoxUpper (d := d) R x N))
      (x n) (chewi625ReturnedCutVector (d := d) R x n) := by
  have hnext_le : n + 1 ≤ N := Nat.succ_le_of_lt hnN
  have hsub :
      chewi625CoordinateBox
          (chewi625BoxLower (d := d) R x N)
          (chewi625BoxUpper (d := d) R x N) ⊆
        chewi625CoordinateBox
          (chewi625BoxLower (d := d) R x (n + 1))
          (chewi625BoxUpper (d := d) R x (n + 1)) :=
    chewi625BoxState_subset_of_le
      (d := d) (R := R) hR_nonneg x hnext_le
  exact
    (chewi625BoxState_step_isSeparationVector
      (d := d) R x n).mono hsub

/--
Finite transcript interface for a deterministic feasibility replay: for the
final set `C`, every one of the first `N` oracle replies is a valid separating
vector for the corresponding query.
-/
def IsFeasibilitySeparationTranscript {E : Type*}
    [NormedAddCommGroup E] [InnerProductSpace ℝ E]
    (C : Set E) (x p : ℕ -> E) (N : ℕ) : Prop :=
  ∀ n : ℕ, n < N -> IsSeparationVector C (x n) (p n)

/--
The resisting box construction supplies a valid separation transcript for its
final coordinate box.
-/
theorem chewi625BoxState_final_separationTranscript {d : ℕ} [NeZero d]
    {R : ℝ} (hR_nonneg : 0 ≤ R)
    (x : ℕ -> EuclideanSpace ℝ (Fin d)) (N : ℕ) :
    IsFeasibilitySeparationTranscript
      (chewi625CoordinateBox
        (chewi625BoxLower (d := d) R x N)
        (chewi625BoxUpper (d := d) R x N))
      x (chewi625ReturnedCutVector (d := d) R x) N := by
  intro n hnN
  exact
    chewi625ReturnedCutVector_isSeparationVector_final_box
      (d := d) (R := R) hR_nonneg x hnN

/--
Final-box replay certificate: all first `N` replies are valid separators for
the final box, and all first `N` queries fail final strict feasibility.
-/
def IsFeasibilityReplayCertificate {E : Type*}
    [NormedAddCommGroup E] [InnerProductSpace ℝ E]
    (C Cstrict : Set E) (x p : ℕ -> E) (N : ℕ) : Prop :=
  IsFeasibilitySeparationTranscript C x p N ∧
    ∀ n : ℕ, n < N -> x n ∉ Cstrict

/--
Source-facing feasibility-body package from Definition 6.24, specialized to
the coordinate cube model used in Theorem 6.25: the candidate set is closed,
convex, lies in `[-R,R]^d`, and contains an `eps`-ball.
-/
def IsChewi625FeasibilityInstance {d : ℕ} (eps R : ℝ)
    (C : Set (EuclideanSpace ℝ (Fin d))) : Prop :=
  IsClosed C ∧
    Convex ℝ C ∧
    C ⊆
      chewi625CoordinateBox
        (chewi625ConstVec (d := d) (-R)) (chewi625ConstVec (d := d) R) ∧
    ∃ center : EuclideanSpace ℝ (Fin d), Metric.closedBall center eps ⊆ C

/--
Supplied deterministic algorithm interface for feasibility lower bounds.  The
query functional at time `n` is allowed to inspect only the previous oracle
replies.  This is intentionally a light interface rather than a full program
semantics model.
-/
def IsPrefixCausalQueryFunctional {E : Type*}
    (queryOf : ℕ -> (ℕ -> E) -> E) : Prop :=
  ∀ n p q, (∀ k : ℕ, k < n -> p k = q k) ->
    queryOf n p = queryOf n q

/-- A finite run of a supplied deterministic query functional. -/
def IsDeterministicFeasibilityRun {E : Type*}
    (queryOf : ℕ -> (ℕ -> E) -> E) (x p : ℕ -> E) (N : ℕ) : Prop :=
  ∀ n : ℕ, n < N -> x n = queryOf n p

/--
If two finite runs of a prefix-causal deterministic query functional see the
same reply transcript through time `N`, then their query sequences agree
through time `N`.
-/
theorem deterministicFeasibilityRun_query_eq_of_transcript_eq {E : Type*}
    {queryOf : ℕ -> (ℕ -> E) -> E}
    {x y p q : ℕ -> E} {N : ℕ}
    (hcausal : IsPrefixCausalQueryFunctional queryOf)
    (hxrun : IsDeterministicFeasibilityRun queryOf x p N)
    (hyrun : IsDeterministicFeasibilityRun queryOf y q N)
    (hpq : ∀ k : ℕ, k < N -> p k = q k) :
    ∀ n : ℕ, n < N -> x n = y n := by
  intro n hnN
  calc
    x n = queryOf n p := hxrun n hnN
    _ = queryOf n q := hcausal n p q (fun k hkn => hpq k (lt_trans hkn hnN))
    _ = y n := (hyrun n hnN).symm

/--
Generic deterministic replay consequence: once a resisting transcript is a
valid final-box certificate, any deterministic run with the same reply
transcript makes the same first `N` queries and therefore never enters the
strict final feasible set.
-/
theorem IsFeasibilityReplayCertificate.no_strict_success_of_deterministic_run
    {E : Type*} [NormedAddCommGroup E] [InnerProductSpace ℝ E]
    {queryOf : ℕ -> (ℕ -> E) -> E}
    {C Cstrict : Set E} {x y p q : ℕ -> E} {N : ℕ}
    (hcert : IsFeasibilityReplayCertificate C Cstrict x p N)
    (hcausal : IsPrefixCausalQueryFunctional queryOf)
    (hxrun : IsDeterministicFeasibilityRun queryOf x p N)
    (hyrun : IsDeterministicFeasibilityRun queryOf y q N)
    (hpq : ∀ k : ℕ, k < N -> p k = q k) :
    ∀ n : ℕ, n < N -> y n ∉ Cstrict := by
  intro n hnN hy_mem
  have hxy :
      x n = y n :=
    deterministicFeasibilityRun_query_eq_of_transcript_eq
      hcausal hxrun hyrun hpq n hnN
  exact hcert.2 n hnN (by simpa [hxy] using hy_mem)

/--
The resisting box construction gives the full geometric certificate needed by
the deterministic post-hoc replay step: valid separation replies for the final
box and exclusion of every previous query from its strict coordinate interior.
-/
theorem chewi625BoxState_final_replayCertificate {d : ℕ} [NeZero d]
    {R : ℝ} (hR_nonneg : 0 ≤ R)
    (x : ℕ -> EuclideanSpace ℝ (Fin d)) (N : ℕ) :
    IsFeasibilityReplayCertificate
      (chewi625CoordinateBox
        (chewi625BoxLower (d := d) R x N)
        (chewi625BoxUpper (d := d) R x N))
      (chewi625StrictCoordinateBox
        (chewi625BoxLower (d := d) R x N)
        (chewi625BoxUpper (d := d) R x N))
      x (chewi625ReturnedCutVector (d := d) R x) N := by
  exact
    ⟨chewi625BoxState_final_separationTranscript
        (d := d) (R := R) hR_nonneg x N,
      fun n hnN =>
        chewi625BoxState_query_not_mem_final_strict_box
          (d := d) (R := R) hR_nonneg x hnN⟩

/--
At a complete cycle, if every side is still at least `2 * eps`, then the
recursive box contains an `eps`-ball around its midpoint.
-/
theorem chewi625_closedBall_subset_full_cycles_of_two_eps_le_width {d : ℕ}
    [NeZero d] {R eps : ℝ}
    {x : ℕ -> EuclideanSpace ℝ (Fin d)} {m : ℕ}
    (hwidth : 2 * eps ≤ (2 * R) / (2 : ℝ) ^ m) :
    ∃ center : EuclideanSpace ℝ (Fin d),
      Metric.closedBall center eps ⊆
        chewi625CoordinateBox
          (chewi625BoxLower (d := d) R x (m * d))
          (chewi625BoxUpper (d := d) R x (m * d)) := by
  let a := chewi625BoxLower (d := d) R x (m * d)
  let b := chewi625BoxUpper (d := d) R x (m * d)
  let center := chewi625Midpoint a b
  refine ⟨center, chewi625_closedBall_subset_coordinateBox ?_ ?_⟩
  · intro i
    have hcoordwidth : 2 * eps ≤ b i - a i := by
      have h := hwidth
      rw [← chewi625BoxWidth_full_cycles (d := d) R x i m] at h
      simpa [chewi625BoxWidth, a, b] using h
    simp [center, a, b, chewi625Midpoint]
    nlinarith
  · intro i
    have hcoordwidth : 2 * eps ≤ b i - a i := by
      have h := hwidth
      rw [← chewi625BoxWidth_full_cycles (d := d) R x i m] at h
      simpa [chewi625BoxWidth, a, b] using h
    simp [center, a, b, chewi625Midpoint]
    nlinarith

/--
Full-cycle source radius form: if `eps <= R / 2^m`, the recursive box after
`m` complete coordinate cycles still contains an `eps`-ball.
-/
theorem chewi625_closedBall_subset_full_cycles_of_eps_le_radius {d : ℕ}
    [NeZero d] {R eps : ℝ}
    {x : ℕ -> EuclideanSpace ℝ (Fin d)} {m : ℕ}
    (hradius : eps ≤ R / (2 : ℝ) ^ m) :
    ∃ center : EuclideanSpace ℝ (Fin d),
      Metric.closedBall center eps ⊆
        chewi625CoordinateBox
          (chewi625BoxLower (d := d) R x (m * d))
          (chewi625BoxUpper (d := d) R x (m * d)) := by
  have hwidth : 2 * eps ≤ (2 * R) / (2 : ℝ) ^ m := by
    calc
      2 * eps ≤ 2 * (R / (2 : ℝ) ^ m) := by nlinarith [hradius]
      _ = (2 * R) / (2 : ℝ) ^ m := by ring
  exact
    chewi625_closedBall_subset_full_cycles_of_two_eps_le_width
      (d := d) (R := R) (eps := eps) (x := x) (m := m) hwidth

/--
Logarithmic lower-bound scalar helper: if the number of complete cycles is at
most `log_2 (R / eps)`, then the exact full-cycle radius is still at least
`eps`.
-/
theorem chewi625_eps_le_half_pow_mul_of_nat_mul_log_le
    {R eps : ℝ} {m : ℕ}
    (hR_pos : 0 < R) (heps_pos : 0 < eps)
    (hM_log : (m : ℝ) * Real.log (2 : ℝ) ≤ Real.log (R / eps)) :
    eps ≤ (1 / 2 : ℝ) ^ m * R := by
  have hhalf_pos : 0 < (1 / 2 : ℝ) := by norm_num
  have hpow_pos : 0 < (1 / 2 : ℝ) ^ m := pow_pos hhalf_pos m
  have hright_pos : 0 < (1 / 2 : ℝ) ^ m * R :=
    mul_pos hpow_pos hR_pos
  have hlog_half : Real.log (1 / 2 : ℝ) = -Real.log (2 : ℝ) := by
    have hhalf : (1 / 2 : ℝ) = (2 : ℝ)⁻¹ := by norm_num
    rw [hhalf, Real.log_inv]
  have hlog_ratio :
      Real.log (R / eps) = Real.log R - Real.log eps := by
    rw [Real.log_div hR_pos.ne' heps_pos.ne']
  have hlog_right :
      Real.log ((1 / 2 : ℝ) ^ m * R) =
        (m : ℝ) * Real.log (1 / 2 : ℝ) + Real.log R := by
    rw [Real.log_mul hpow_pos.ne' hR_pos.ne', Real.log_pow]
  have hlog_le : Real.log eps ≤ Real.log ((1 / 2 : ℝ) ^ m * R) := by
    rw [hlog_right, hlog_half]
    have hM_log' :
        (m : ℝ) * Real.log (2 : ℝ) ≤ Real.log R - Real.log eps := by
      simpa [hlog_ratio] using hM_log
    linarith
  exact (Real.log_le_log_iff heps_pos hright_pos).mp hlog_le

/-- Division-by-powers form of `chewi625_eps_le_half_pow_mul_of_nat_mul_log_le`. -/
theorem chewi625_eps_le_radius_of_nat_mul_log_le
    {R eps : ℝ} {m : ℕ}
    (hR_pos : 0 < R) (heps_pos : 0 < eps)
    (hM_log : (m : ℝ) * Real.log (2 : ℝ) ≤ Real.log (R / eps)) :
    eps ≤ R / (2 : ℝ) ^ m := by
  have h :=
    chewi625_eps_le_half_pow_mul_of_nat_mul_log_le
      (R := R) (eps := eps) (m := m) hR_pos heps_pos hM_log
  have hpow :
      (1 / 2 : ℝ) ^ m * R = R / (2 : ℝ) ^ m := by
    have hhalf : (1 / 2 : ℝ) = (2 : ℝ)⁻¹ := by norm_num
    rw [hhalf, inv_pow]
    ring
  rw [hpow] at h
  exact h

/--
Full-cycle logarithmic source wrapper for the feasibility construction:
`m * log 2 <= log (R / eps)` guarantees that the box after `m` cycles still
contains an `eps`-ball.
-/
theorem chewi625_closedBall_subset_full_cycles_of_log_bound {d : ℕ}
    [NeZero d] {R eps : ℝ}
    (hR_pos : 0 < R) (heps_pos : 0 < eps)
    {x : ℕ -> EuclideanSpace ℝ (Fin d)} {m : ℕ}
    (hM_log : (m : ℝ) * Real.log (2 : ℝ) ≤ Real.log (R / eps)) :
    ∃ center : EuclideanSpace ℝ (Fin d),
      Metric.closedBall center eps ⊆
        chewi625CoordinateBox
          (chewi625BoxLower (d := d) R x (m * d))
          (chewi625BoxUpper (d := d) R x (m * d)) := by
  exact
    chewi625_closedBall_subset_full_cycles_of_eps_le_radius
      (d := d) (R := R) (eps := eps) (x := x) (m := m)
      (chewi625_eps_le_radius_of_nat_mul_log_le
        (R := R) (eps := eps) (m := m) hR_pos heps_pos hM_log)

/--
If a later full cycle still contains an `eps`-ball, then every earlier
recursive box contains that same ball by nesting.
-/
theorem chewi625_closedBall_subset_of_le_full_cycle {d : ℕ} [NeZero d]
    {R eps : ℝ} (hR_nonneg : 0 ≤ R)
    {x : ℕ -> EuclideanSpace ℝ (Fin d)} {n m : ℕ}
    (hnm : n ≤ m * d) (hradius : eps ≤ R / (2 : ℝ) ^ m) :
    ∃ center : EuclideanSpace ℝ (Fin d),
      Metric.closedBall center eps ⊆
        chewi625CoordinateBox
          (chewi625BoxLower (d := d) R x n)
          (chewi625BoxUpper (d := d) R x n) := by
  rcases
    chewi625_closedBall_subset_full_cycles_of_eps_le_radius
      (d := d) (R := R) (eps := eps) (x := x) (m := m) hradius with
    ⟨center, hball⟩
  refine ⟨center, ?_⟩
  exact
    hball.trans
      (chewi625BoxState_subset_of_le
        (d := d) (R := R) hR_nonneg x hnm)

/-- Logarithmic earlier-step wrapper for the source query-count lower bound. -/
theorem chewi625_closedBall_subset_of_le_full_cycle_log_bound {d : ℕ}
    [NeZero d] {R eps : ℝ}
    (hR_pos : 0 < R) (heps_pos : 0 < eps)
    {x : ℕ -> EuclideanSpace ℝ (Fin d)} {n m : ℕ}
    (hnm : n ≤ m * d)
    (hM_log : (m : ℝ) * Real.log (2 : ℝ) ≤ Real.log (R / eps)) :
    ∃ center : EuclideanSpace ℝ (Fin d),
      Metric.closedBall center eps ⊆
        chewi625CoordinateBox
          (chewi625BoxLower (d := d) R x n)
          (chewi625BoxUpper (d := d) R x n) := by
  exact
    chewi625_closedBall_subset_of_le_full_cycle
      (d := d) (R := R) (eps := eps) hR_pos.le (x := x)
      (n := n) (m := m) hnm
      (chewi625_eps_le_radius_of_nat_mul_log_le
        (R := R) (eps := eps) (m := m) hR_pos heps_pos hM_log)

/--
Source-shaped supplied-interface package for Chewi Theorem 6.25: under the log
query-count condition, the final box both admits a valid separation transcript
for all previous queries and still contains an `eps`-ball.
-/
theorem chewi625_final_replayCertificate_and_closedBall_of_le_full_cycle_log_bound
    {d : ℕ} [NeZero d] {R eps : ℝ}
    (hR_pos : 0 < R) (heps_pos : 0 < eps)
    {x : ℕ -> EuclideanSpace ℝ (Fin d)} {N m : ℕ}
    (hNm : N ≤ m * d)
    (hM_log : (m : ℝ) * Real.log (2 : ℝ) ≤ Real.log (R / eps)) :
    IsFeasibilityReplayCertificate
        (chewi625CoordinateBox
          (chewi625BoxLower (d := d) R x N)
          (chewi625BoxUpper (d := d) R x N))
        (chewi625StrictCoordinateBox
          (chewi625BoxLower (d := d) R x N)
          (chewi625BoxUpper (d := d) R x N))
        x (chewi625ReturnedCutVector (d := d) R x) N ∧
      ∃ center : EuclideanSpace ℝ (Fin d),
        Metric.closedBall center eps ⊆
          chewi625CoordinateBox
            (chewi625BoxLower (d := d) R x N)
            (chewi625BoxUpper (d := d) R x N) := by
  exact
    ⟨chewi625BoxState_final_replayCertificate
        (d := d) (R := R) hR_pos.le x N,
      chewi625_closedBall_subset_of_le_full_cycle_log_bound
        (d := d) (R := R) (eps := eps) hR_pos heps_pos
        (x := x) (n := N) (m := m) hNm hM_log⟩

/--
Deterministic replay wrapper for Chewi Theorem 6.25.  Under the log
query-count condition, the resisting construction supplies a final feasible
box with an `eps`-ball; any supplied deterministic run that sees the same
reply transcript as the resisting run makes no strict-feasible query in its
first `N` steps.
-/
theorem chewi625_deterministic_run_no_strict_success_of_log_bound {d : ℕ}
    [NeZero d] {R eps : ℝ}
    (hR_pos : 0 < R) (heps_pos : 0 < eps)
    {queryOf : ℕ ->
      (ℕ -> EuclideanSpace ℝ (Fin d)) -> EuclideanSpace ℝ (Fin d)}
    (hcausal : IsPrefixCausalQueryFunctional queryOf)
    {x y q : ℕ -> EuclideanSpace ℝ (Fin d)} {N m : ℕ}
    (hresistingRun :
      IsDeterministicFeasibilityRun
        queryOf x (chewi625ReturnedCutVector (d := d) R x) N)
    (hreplayRun : IsDeterministicFeasibilityRun queryOf y q N)
    (htranscript :
      ∀ n : ℕ, n < N -> chewi625ReturnedCutVector (d := d) R x n = q n)
    (hNm : N ≤ m * d)
    (hM_log : (m : ℝ) * Real.log (2 : ℝ) ≤ Real.log (R / eps)) :
    (∃ center : EuclideanSpace ℝ (Fin d),
        Metric.closedBall center eps ⊆
          chewi625CoordinateBox
            (chewi625BoxLower (d := d) R x N)
            (chewi625BoxUpper (d := d) R x N)) ∧
      ∀ n : ℕ, n < N ->
        y n ∉ chewi625StrictCoordinateBox
          (chewi625BoxLower (d := d) R x N)
          (chewi625BoxUpper (d := d) R x N) := by
  let C :=
    chewi625CoordinateBox
      (chewi625BoxLower (d := d) R x N)
      (chewi625BoxUpper (d := d) R x N)
  let Cstrict :=
    chewi625StrictCoordinateBox
      (chewi625BoxLower (d := d) R x N)
      (chewi625BoxUpper (d := d) R x N)
  have hpackage :=
    chewi625_final_replayCertificate_and_closedBall_of_le_full_cycle_log_bound
      (d := d) (R := R) (eps := eps) hR_pos heps_pos
      (x := x) (N := N) (m := m) hNm hM_log
  exact
    ⟨hpackage.2,
      IsFeasibilityReplayCertificate.no_strict_success_of_deterministic_run
        (queryOf := queryOf) (y := y) (q := q)
        hpackage.1 hcausal hresistingRun hreplayRun htranscript⟩

/--
The final resisting box is a closed convex Definition 6.24-style feasibility
instance inside the source cube, and it still contains an `eps`-ball under the
same logarithmic query-count condition.
-/
theorem chewi625_final_box_feasibilityInstance_of_le_full_cycle_log_bound
    {d : ℕ} [NeZero d] {R eps : ℝ}
    (hR_pos : 0 < R) (heps_pos : 0 < eps)
    {x : ℕ -> EuclideanSpace ℝ (Fin d)} {N m : ℕ}
    (hNm : N ≤ m * d)
    (hM_log : (m : ℝ) * Real.log (2 : ℝ) ≤ Real.log (R / eps)) :
    IsChewi625FeasibilityInstance (d := d) eps R
      (chewi625CoordinateBox
        (chewi625BoxLower (d := d) R x N)
        (chewi625BoxUpper (d := d) R x N)) := by
  refine
    ⟨chewi625CoordinateBox_isClosed _ _,
      chewi625CoordinateBox_convex _ _, ?_, ?_⟩
  · simpa using
      chewi625BoxState_subset_of_le
        (d := d) (R := R) hR_pos.le x
        (n := 0) (m := N) (Nat.zero_le N)
  · exact
      (chewi625_final_replayCertificate_and_closedBall_of_le_full_cycle_log_bound
        (d := d) (R := R) (eps := eps) hR_pos heps_pos
        (x := x) (N := N) (m := m) hNm hM_log).2

/--
Topological-interior form of Chewi Theorem 6.25's deterministic replay
lower-bound package.  The final post-hoc set is a closed convex feasibility
instance containing an `eps`-ball, and every first-`N` query of any deterministic
run with the same separation transcript fails to land in `interior C`.
-/
theorem chewi625_deterministic_run_no_interior_success_of_log_bound {d : ℕ}
    [NeZero d] {R eps : ℝ}
    (hR_pos : 0 < R) (heps_pos : 0 < eps)
    {queryOf : ℕ ->
      (ℕ -> EuclideanSpace ℝ (Fin d)) -> EuclideanSpace ℝ (Fin d)}
    (hcausal : IsPrefixCausalQueryFunctional queryOf)
    {x y q : ℕ -> EuclideanSpace ℝ (Fin d)} {N m : ℕ}
    (hresistingRun :
      IsDeterministicFeasibilityRun
        queryOf x (chewi625ReturnedCutVector (d := d) R x) N)
    (hreplayRun : IsDeterministicFeasibilityRun queryOf y q N)
    (htranscript :
      ∀ n : ℕ, n < N -> chewi625ReturnedCutVector (d := d) R x n = q n)
    (hNm : N ≤ m * d)
    (hM_log : (m : ℝ) * Real.log (2 : ℝ) ≤ Real.log (R / eps)) :
    IsChewi625FeasibilityInstance (d := d) eps R
        (chewi625CoordinateBox
          (chewi625BoxLower (d := d) R x N)
          (chewi625BoxUpper (d := d) R x N)) ∧
      ∀ n : ℕ, n < N ->
        y n ∉ interior
          (chewi625CoordinateBox
            (chewi625BoxLower (d := d) R x N)
            (chewi625BoxUpper (d := d) R x N)) := by
  have hstrict :=
    chewi625_deterministic_run_no_strict_success_of_log_bound
      (d := d) (R := R) (eps := eps) hR_pos heps_pos
      (queryOf := queryOf) hcausal
      (x := x) (y := y) (q := q) (N := N) (m := m)
      hresistingRun hreplayRun htranscript hNm hM_log
  refine
    ⟨chewi625_final_box_feasibilityInstance_of_le_full_cycle_log_bound
        (d := d) (R := R) (eps := eps) hR_pos heps_pos
        (x := x) (N := N) (m := m) hNm hM_log,
      ?_⟩
  intro n hn hy_interior
  exact
    hstrict.2 n hn
      (chewi625CoordinateBox_interior_subset_strict hy_interior)

/--
Source-shaped same-run package for Chewi Theorem 6.25.  If the deterministic
algorithm follows the resisting transcript for `N` steps and
`N ≤ m * d ≤ d * log₂(R / eps)` in logarithmic form, then the final post-hoc
coordinate box is a Definition 6.24 feasibility instance, the resisting replies
are valid separation vectors for that final instance, and none of the first
`N` queries reaches its topological interior.
-/
theorem chewi625_resisting_final_box_source_package_of_log_bound {d : ℕ}
    [NeZero d] {R eps : ℝ}
    (hR_pos : 0 < R) (heps_pos : 0 < eps)
    {queryOf : ℕ ->
      (ℕ -> EuclideanSpace ℝ (Fin d)) -> EuclideanSpace ℝ (Fin d)}
    (hcausal : IsPrefixCausalQueryFunctional queryOf)
    {x : ℕ -> EuclideanSpace ℝ (Fin d)} {N m : ℕ}
    (hresistingRun :
      IsDeterministicFeasibilityRun
        queryOf x (chewi625ReturnedCutVector (d := d) R x) N)
    (hNm : N ≤ m * d)
    (hM_log : (m : ℝ) * Real.log (2 : ℝ) ≤ Real.log (R / eps)) :
    IsChewi625FeasibilityInstance (d := d) eps R
        (chewi625CoordinateBox
          (chewi625BoxLower (d := d) R x N)
          (chewi625BoxUpper (d := d) R x N)) ∧
      IsDeterministicFeasibilityRun
        queryOf x (chewi625ReturnedCutVector (d := d) R x) N ∧
      IsFeasibilitySeparationTranscript
        (chewi625CoordinateBox
          (chewi625BoxLower (d := d) R x N)
          (chewi625BoxUpper (d := d) R x N))
        x (chewi625ReturnedCutVector (d := d) R x) N ∧
      ∀ n : ℕ, n < N ->
        x n ∉ interior
          (chewi625CoordinateBox
            (chewi625BoxLower (d := d) R x N)
            (chewi625BoxUpper (d := d) R x N)) := by
  have hnoInterior :=
    chewi625_deterministic_run_no_interior_success_of_log_bound
      (d := d) (R := R) (eps := eps) hR_pos heps_pos
      (queryOf := queryOf) hcausal
      (x := x) (y := x)
      (q := chewi625ReturnedCutVector (d := d) R x) (N := N) (m := m)
      hresistingRun hresistingRun (by intro n hn; rfl) hNm hM_log
  exact
    ⟨hnoInterior.1,
      hresistingRun,
      chewi625BoxState_final_separationTranscript
        (d := d) (R := R) hR_pos.le x N,
      hnoInterior.2⟩

/--
Existential Theorem 6.25 lower-bound package: the resisting construction
produces a closed convex feasibility instance and a valid separation transcript
for the given deterministic algorithm, while every first-`N` query misses the
interior of that instance.
-/
theorem chewi625_exists_resisting_feasibility_instance_of_log_bound {d : ℕ}
    [NeZero d] {R eps : ℝ}
    (hR_pos : 0 < R) (heps_pos : 0 < eps)
    {queryOf : ℕ ->
      (ℕ -> EuclideanSpace ℝ (Fin d)) -> EuclideanSpace ℝ (Fin d)}
    (hcausal : IsPrefixCausalQueryFunctional queryOf)
    {x : ℕ -> EuclideanSpace ℝ (Fin d)} {N m : ℕ}
    (hresistingRun :
      IsDeterministicFeasibilityRun
        queryOf x (chewi625ReturnedCutVector (d := d) R x) N)
    (hNm : N ≤ m * d)
    (hM_log : (m : ℝ) * Real.log (2 : ℝ) ≤ Real.log (R / eps)) :
    ∃ C : Set (EuclideanSpace ℝ (Fin d)),
      ∃ q : ℕ -> EuclideanSpace ℝ (Fin d),
        IsChewi625FeasibilityInstance (d := d) eps R C ∧
          IsDeterministicFeasibilityRun queryOf x q N ∧
          IsFeasibilitySeparationTranscript C x q N ∧
          ∀ n : ℕ, n < N -> x n ∉ interior C := by
  refine
    ⟨chewi625CoordinateBox
        (chewi625BoxLower (d := d) R x N)
        (chewi625BoxUpper (d := d) R x N),
      chewi625ReturnedCutVector (d := d) R x, ?_⟩
  exact
    chewi625_resisting_final_box_source_package_of_log_bound
      (d := d) (R := R) (eps := eps) hR_pos heps_pos
      (queryOf := queryOf) hcausal
      (x := x) (N := N) (m := m) hresistingRun hNm hM_log

end Optimization
end StatInference
