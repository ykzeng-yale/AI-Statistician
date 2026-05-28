import StatInference.Matching.WDSM.FiniteCellIndicatorMass

/-!
# Finite score-cell indicator partition algebra for WDSM

This module records deterministic algebra for the bounded `0/1` indicators
introduced in `FiniteCellIndicatorMass`.  These identities are the finite
partition facts needed by later LLN/CLT and covariance calculations for
weighted joint-score indicator sums.
-/

namespace StatInference
namespace Matching
namespace WDSM

open scoped BigOperators

variable {Unit Cell : Type*} [DecidableEq Cell]

theorem scoreCellIndicator_mul_self
    (score : Unit -> Cell) (cell : Cell) (unit : Unit) :
    scoreCellIndicator score cell unit *
        scoreCellIndicator score cell unit =
      scoreCellIndicator score cell unit := by
  unfold scoreCellIndicator
  split_ifs <;> norm_num

theorem scoreCellIndicator_sq
    (score : Unit -> Cell) (cell : Cell) (unit : Unit) :
    scoreCellIndicator score cell unit ^ 2 =
      scoreCellIndicator score cell unit := by
  rw [sq]
  exact scoreCellIndicator_mul_self score cell unit

theorem scoreCellIndicator_mul_of_ne
    (score : Unit -> Cell) (cellA cellB : Cell) (unit : Unit)
    (hne : cellA ≠ cellB) :
    scoreCellIndicator score cellA unit *
        scoreCellIndicator score cellB unit =
      0 := by
  unfold scoreCellIndicator
  by_cases hA : score unit = cellA
  · simp [hA, hne]
  · simp [hA]

theorem scoreCellIndicator_mul
    (score : Unit -> Cell) (cellA cellB : Cell) (unit : Unit) :
    scoreCellIndicator score cellA unit *
        scoreCellIndicator score cellB unit =
      if cellA = cellB then scoreCellIndicator score cellA unit else 0 := by
  by_cases h : cellA = cellB
  · subst cellB
    simp [scoreCellIndicator_mul_self]
  · simp [h, scoreCellIndicator_mul_of_ne score cellA cellB unit h]

theorem sum_scoreCellIndicator_eq_one_of_mem
    (cells : Finset Cell) (score : Unit -> Cell) (unit : Unit)
    (hmem : score unit ∈ cells) :
    (∑ cell ∈ cells, scoreCellIndicator score cell unit) = 1 := by
  classical
  rw [Finset.sum_eq_single (score unit)]
  · exact scoreCellIndicator_of_eq score (score unit) unit rfl
  · intro cell hcell hne
    have hscore_ne : score unit ≠ cell := by
      intro h
      exact hne h.symm
    exact scoreCellIndicator_of_ne score cell unit hscore_ne
  · intro hnot
    exact (hnot hmem).elim

theorem sum_scoreCellIndicator_eq_zero_of_not_mem
    (cells : Finset Cell) (score : Unit -> Cell) (unit : Unit)
    (hnot_mem : score unit ∉ cells) :
    (∑ cell ∈ cells, scoreCellIndicator score cell unit) = 0 := by
  exact Finset.sum_eq_zero
    (fun cell hcell => by
      exact scoreCellIndicator_of_ne score cell unit
        (fun h => hnot_mem (h.symm ▸ hcell)))

theorem sum_scoreCellIndicator_eq_indicator_mem
    (cells : Finset Cell) (score : Unit -> Cell) (unit : Unit) :
    (∑ cell ∈ cells, scoreCellIndicator score cell unit) =
      if score unit ∈ cells then 1 else 0 := by
  by_cases hmem : score unit ∈ cells
  · simp [hmem, sum_scoreCellIndicator_eq_one_of_mem cells score unit hmem]
  · simp [hmem, sum_scoreCellIndicator_eq_zero_of_not_mem cells score unit hmem]

/--
If the finite score partition covers the sample, the weighted total is the sum
of weighted cell-indicator sums.
-/
theorem weightedSampleTotal_eq_sum_weightedSampleSum_scoreCellIndicator
    (sample : Finset Unit) (cells : Finset Cell)
    (weight : Unit -> Real) (score : Unit -> Cell)
    (hcover : ∀ unit, unit ∈ sample -> score unit ∈ cells) :
    weightedSampleTotal sample weight =
      ∑ cell ∈ cells,
        weightedSampleSum sample weight (scoreCellIndicator score cell) := by
  rw [← sum_scoreCellMass_eq_weightedSampleTotal_of_mapsTo
    sample cells weight score hcover]
  exact Finset.sum_congr rfl
    (fun cell _hcell => by
      rw [scoreCellMass_eq_weightedSampleSum_scoreCellIndicator])

theorem weightedSampleSum_indicator_mul_self_eq_scoreCellMass
    (sample : Finset Unit) (weight : Unit -> Real)
    (score : Unit -> Cell) (cell : Cell) :
    weightedSampleSum sample weight
        (fun unit =>
          scoreCellIndicator score cell unit *
            scoreCellIndicator score cell unit) =
      scoreCellMass sample weight score cell := by
  rw [← weightedSampleSum_scoreCellIndicator_eq_scoreCellMass]
  unfold weightedSampleSum
  exact Finset.sum_congr rfl
    (fun unit _hunit => by
      change
        weight unit *
            (scoreCellIndicator score cell unit *
              scoreCellIndicator score cell unit) =
          weight unit * scoreCellIndicator score cell unit
      rw [scoreCellIndicator_mul_self])

theorem weightedSampleSum_indicator_mul_of_ne_eq_zero
    (sample : Finset Unit) (weight : Unit -> Real)
    (score : Unit -> Cell) (cellA cellB : Cell)
    (hne : cellA ≠ cellB) :
    weightedSampleSum sample weight
        (fun unit =>
          scoreCellIndicator score cellA unit *
            scoreCellIndicator score cellB unit) =
      0 := by
  unfold weightedSampleSum
  exact Finset.sum_eq_zero
    (fun unit _hunit => by
      change
        weight unit *
            (scoreCellIndicator score cellA unit *
              scoreCellIndicator score cellB unit) =
          0
      rw [scoreCellIndicator_mul_of_ne score cellA cellB unit hne]
      ring)

end WDSM
end Matching
end StatInference
