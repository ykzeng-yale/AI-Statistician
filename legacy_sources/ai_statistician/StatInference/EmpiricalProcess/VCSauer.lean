import Mathlib.Combinatorics.SetFamily.Shatter
import Mathlib.Data.Nat.Choose.Bounds
import Mathlib.Tactic

/-!
# VC/Sauer combinatorial bridges

This file wraps mathlib's finite set-family Sauer-Shelah theorem in the
coarse polynomial form needed by the VdV&W empirical-process entropy route.
-/

namespace StatInference

open scoped BigOperators

/--
VdV&W-facing wrapper for mathlib's Sauer-Shelah bound:
`|A| <= sum_{k <= vcDim A} (|X| choose k)`.
-/
theorem vdVWSauerShelah_card_le_sum_vcDim {α : Type*} [Fintype α]
    [DecidableEq α] (family : Finset (Finset α)) :
    family.card ≤
      ∑ k ∈ Finset.Iic family.vcDim, (Fintype.card α).choose k := by
  exact
    (Finset.card_le_card_shatterer family).trans
      (Finset.card_shatterer_le_sum_vcDim (𝒜 := family))

/--
Sauer-Shelah with a supplied VC-dimension upper bound.
-/
theorem vdVWSauerShelah_card_le_sum_of_vcDim_le {α : Type*} [Fintype α]
    [DecidableEq α] (family : Finset (Finset α)) {d : ℕ}
    (hvc : family.vcDim ≤ d) :
    family.card ≤ ∑ k ∈ Finset.Iic d, (Fintype.card α).choose k := by
  refine (vdVWSauerShelah_card_le_sum_vcDim family).trans ?_
  exact
    Finset.sum_le_sum_of_subset_of_nonneg
      (by
        intro k hk
        exact Finset.mem_Iic.mpr ((Finset.mem_Iic.mp hk).trans hvc))
      (by
        intro k _hk_family _hk_not
        exact Nat.zero_le ((Fintype.card α).choose k))

/--
Coarse polynomial Sauer-Shelah consequence.

If the ground-set size is at most `N` and `vcDim family <= d`, then
`|family| + 1 <= (d + 2) * (N + 1)^d`.  This is intentionally coarse but has
the exact natural-polynomial shape needed by the Theorem 2.4.3 entropy bridge.
-/
theorem vdVWSauerShelah_card_add_one_le_nat_poly_of_vcDim_le
    {α : Type*} [Fintype α] [DecidableEq α] (family : Finset (Finset α))
    {N d : ℕ} (hcard : Fintype.card α ≤ N) (hvc : family.vcDim ≤ d) :
    family.card + 1 ≤ (d + 2) * (N + 1) ^ d := by
  have hsum_bound :
      family.card ≤ ∑ k ∈ Finset.Iic d, (Fintype.card α).choose k :=
    vdVWSauerShelah_card_le_sum_of_vcDim_le family hvc
  have hterm_le :
      ∀ k ∈ Finset.Iic d, (Fintype.card α).choose k ≤ (N + 1) ^ d := by
    intro k hk
    have hk_le_d : k ≤ d := Finset.mem_Iic.mp hk
    calc
      (Fintype.card α).choose k ≤ (Fintype.card α) ^ k :=
        Nat.choose_le_pow _ _
      _ ≤ (N + 1) ^ k :=
        Nat.pow_le_pow_left (hcard.trans (Nat.le_succ N)) _
      _ ≤ (N + 1) ^ d :=
        Nat.pow_le_pow_right (Nat.succ_pos N) hk_le_d
  have hsum_poly :
      (∑ k ∈ Finset.Iic d, (Fintype.card α).choose k) ≤
        (d + 1) * (N + 1) ^ d := by
    simpa using
      (Finset.sum_le_card_nsmul (Finset.Iic d)
        (fun k => (Fintype.card α).choose k) ((N + 1) ^ d) hterm_le)
  have hfamily_poly : family.card ≤ (d + 1) * (N + 1) ^ d :=
    hsum_bound.trans hsum_poly
  have hp_pos : 0 < (N + 1) ^ d :=
    pow_pos (Nat.succ_pos N) d
  calc
    family.card + 1 ≤ (d + 1) * (N + 1) ^ d + 1 :=
      Nat.add_le_add_right hfamily_poly 1
    _ ≤ (d + 1) * (N + 1) ^ d + (N + 1) ^ d :=
      Nat.add_le_add_left (Nat.succ_le_of_lt hp_pos) _
    _ = (d + 2) * (N + 1) ^ d := by
      ring

/--
Real-valued version of the coarse polynomial Sauer-Shelah consequence, ready
for logarithmic entropy estimates.
-/
theorem vdVWSauerShelah_card_add_one_real_le_nat_poly_of_vcDim_le
    {α : Type*} [Fintype α] [DecidableEq α] (family : Finset (Finset α))
    {N d : ℕ} (hcard : Fintype.card α ≤ N) (hvc : family.vcDim ≤ d) :
    ((family.card : ℝ) + 1) ≤
      ((d + 2 : ℕ) : ℝ) * (((N + 1 : ℕ) : ℝ) ^ d) := by
  exact_mod_cast
    vdVWSauerShelah_card_add_one_le_nat_poly_of_vcDim_le
      family hcard hvc

end StatInference
