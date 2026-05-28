import StatInference.Matching.WDSM.FiniteCellIndicatorPartition

/-!
# Centered finite score-cell indicator covariance algebra for WDSM

The bounded score-cell indicators are the finite-dimensional random vector
that remains in the WDSM probability layer.  This module proves deterministic
centered-indicator identities needed to derive covariance formulas after a
survey-weighted LLN/CLT is supplied.
-/

namespace StatInference
namespace Matching
namespace WDSM

open scoped BigOperators

variable {Unit Cell : Type*} [DecidableEq Cell]

/-- A score-cell indicator centered by a reference cell share. -/
def centeredScoreCellIndicator
    (score : Unit -> Cell) (referenceShare : Cell -> Real)
    (cell : Cell) (unit : Unit) : Real :=
  scoreCellIndicator score cell unit - referenceShare cell

theorem centeredScoreCellIndicator_eq
    (score : Unit -> Cell) (referenceShare : Cell -> Real)
    (cell : Cell) (unit : Unit) :
    centeredScoreCellIndicator score referenceShare cell unit =
      scoreCellIndicator score cell unit - referenceShare cell := rfl

/--
Over a covered finite partition whose reference shares sum to one, centered
indicators sum to zero pointwise.
-/
theorem sum_centeredScoreCellIndicator_eq_zero_of_mem
    (cells : Finset Cell) (score : Unit -> Cell)
    (referenceShare : Cell -> Real) (unit : Unit)
    (hmem : score unit ∈ cells)
    (hshare_sum : (∑ cell ∈ cells, referenceShare cell) = 1) :
    (∑ cell ∈ cells,
        centeredScoreCellIndicator score referenceShare cell unit) = 0 := by
  unfold centeredScoreCellIndicator
  rw [Finset.sum_sub_distrib]
  rw [sum_scoreCellIndicator_eq_one_of_mem cells score unit hmem]
  rw [hshare_sum]
  ring

/--
The weighted sum of one centered indicator is the cell mass minus the
reference share times the total weight.
-/
theorem weightedSampleSum_centeredScoreCellIndicator_eq
    (sample : Finset Unit) (weight : Unit -> Real)
    (score : Unit -> Cell) (referenceShare : Cell -> Real)
    (cell : Cell) :
    weightedSampleSum sample weight
        (centeredScoreCellIndicator score referenceShare cell) =
      scoreCellMass sample weight score cell -
        referenceShare cell * weightedSampleTotal sample weight := by
  rw [← weightedSampleSum_scoreCellIndicator_eq_scoreCellMass
    sample weight score cell]
  rw [← weightedSampleSum_one_eq_weightedSampleTotal sample weight]
  unfold weightedSampleSum centeredScoreCellIndicator
  calc
    (∑ unit ∈ sample,
        weight unit *
          (scoreCellIndicator score cell unit - referenceShare cell)) =
        ∑ unit ∈ sample,
          (weight unit * scoreCellIndicator score cell unit -
            referenceShare cell * (weight unit * 1)) := by
          exact Finset.sum_congr rfl (fun unit _hunit => by ring)
    _ =
        (∑ unit ∈ sample, weight unit * scoreCellIndicator score cell unit) -
          (∑ unit ∈ sample, referenceShare cell * (weight unit * 1)) := by
          rw [Finset.sum_sub_distrib]
    _ =
        (∑ unit ∈ sample, weight unit * scoreCellIndicator score cell unit) -
          referenceShare cell *
            (∑ unit ∈ sample, weight unit * 1) := by
          rw [Finset.mul_sum]

/-- Product of two cell indicators as a weighted sum. -/
theorem weightedSampleSum_indicator_mul_eq
    (sample : Finset Unit) (weight : Unit -> Real)
    (score : Unit -> Cell) (cellA cellB : Cell) :
    weightedSampleSum sample weight
        (fun unit =>
          scoreCellIndicator score cellA unit *
            scoreCellIndicator score cellB unit) =
      if cellA = cellB then scoreCellMass sample weight score cellA else 0 := by
  by_cases h : cellA = cellB
  · subst cellB
    simp [weightedSampleSum_indicator_mul_self_eq_scoreCellMass]
  · simp [h, weightedSampleSum_indicator_mul_of_ne_eq_zero
      sample weight score cellA cellB h]

/--
Expansion of the weighted centered-indicator product.  This is the finite
algebraic covariance identity before taking probability limits.
-/
theorem weightedSampleSum_centeredIndicator_mul_centeredIndicator_eq
    (sample : Finset Unit) (weight : Unit -> Real)
    (score : Unit -> Cell) (referenceShare : Cell -> Real)
    (cellA cellB : Cell) :
    weightedSampleSum sample weight
        (fun unit =>
          centeredScoreCellIndicator score referenceShare cellA unit *
            centeredScoreCellIndicator score referenceShare cellB unit) =
      weightedSampleSum sample weight
        (fun unit =>
          scoreCellIndicator score cellA unit *
            scoreCellIndicator score cellB unit) -
        referenceShare cellB * scoreCellMass sample weight score cellA -
        referenceShare cellA * scoreCellMass sample weight score cellB +
        referenceShare cellA * referenceShare cellB *
          weightedSampleTotal sample weight := by
  rw [← weightedSampleSum_scoreCellIndicator_eq_scoreCellMass
    sample weight score cellA]
  rw [← weightedSampleSum_scoreCellIndicator_eq_scoreCellMass
    sample weight score cellB]
  rw [← weightedSampleSum_one_eq_weightedSampleTotal sample weight]
  unfold weightedSampleSum centeredScoreCellIndicator
  rw [Finset.mul_sum, Finset.mul_sum, Finset.mul_sum]
  rw [← Finset.sum_sub_distrib]
  rw [← Finset.sum_sub_distrib]
  rw [← Finset.sum_add_distrib]
  exact Finset.sum_congr rfl
    (fun unit _hunit => by
      ring)

/--
Same-cell centered indicator product expansion.
-/
theorem weightedSampleSum_centeredIndicator_sq_eq
    (sample : Finset Unit) (weight : Unit -> Real)
    (score : Unit -> Cell) (referenceShare : Cell -> Real)
    (cell : Cell) :
    weightedSampleSum sample weight
        (fun unit =>
          centeredScoreCellIndicator score referenceShare cell unit *
            centeredScoreCellIndicator score referenceShare cell unit) =
      scoreCellMass sample weight score cell -
        referenceShare cell * scoreCellMass sample weight score cell -
        referenceShare cell * scoreCellMass sample weight score cell +
        referenceShare cell * referenceShare cell *
          weightedSampleTotal sample weight := by
  rw [weightedSampleSum_centeredIndicator_mul_centeredIndicator_eq]
  rw [weightedSampleSum_indicator_mul_self_eq_scoreCellMass]

/--
Distinct-cell centered indicator product expansion.
-/
theorem weightedSampleSum_centeredIndicator_mul_centeredIndicator_of_ne_eq
    (sample : Finset Unit) (weight : Unit -> Real)
    (score : Unit -> Cell) (referenceShare : Cell -> Real)
    (cellA cellB : Cell) (hne : cellA ≠ cellB) :
    weightedSampleSum sample weight
        (fun unit =>
          centeredScoreCellIndicator score referenceShare cellA unit *
            centeredScoreCellIndicator score referenceShare cellB unit) =
      -referenceShare cellB * scoreCellMass sample weight score cellA -
        referenceShare cellA * scoreCellMass sample weight score cellB +
        referenceShare cellA * referenceShare cellB *
          weightedSampleTotal sample weight := by
  rw [weightedSampleSum_centeredIndicator_mul_centeredIndicator_eq]
  rw [weightedSampleSum_indicator_mul_of_ne_eq_zero
    sample weight score cellA cellB hne]
  ring

end WDSM
end Matching
end StatInference
