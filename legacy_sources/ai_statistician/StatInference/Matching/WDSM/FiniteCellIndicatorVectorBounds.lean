import StatInference.Matching.WDSM.FiniteCellIndicatorBounds
import StatInference.Matching.WDSM.FiniteCellIndicatorPartition

/-!
# Finite-vector bounds for score-cell indicators

For a fixed unit, the vector of score-cell indicators over a finite partition
has at most one nonzero entry.  This gives an `L1` envelope for weighted
indicator vectors that is no larger than the absolute survey weight.
-/

namespace StatInference
namespace Matching
namespace WDSM

open scoped BigOperators

variable {Unit Cell PropensityCell TreatedProgCell ControlProgCell PATTProgCell : Type*}
  [DecidableEq Cell] [DecidableEq PropensityCell]
  [DecidableEq TreatedProgCell] [DecidableEq ControlProgCell]
  [DecidableEq PATTProgCell]

/--
If a finite score partition contains a unit's score, the `L1` norm of that
unit's weighted indicator vector over the partition is exactly the absolute
weight.
-/
theorem sum_abs_weight_mul_scoreCellIndicator_eq_abs_weight_of_mem
    (cells : Finset Cell) (weight : Unit -> Real)
    (score : Unit -> Cell) (unit : Unit)
    (hmem : score unit ∈ cells) :
    (∑ cell ∈ cells,
      |weight unit * scoreCellIndicator score cell unit|) =
      |weight unit| := by
  calc
    (∑ cell ∈ cells,
      |weight unit * scoreCellIndicator score cell unit|) =
        ∑ cell ∈ cells,
          |weight unit| * scoreCellIndicator score cell unit := by
          exact Finset.sum_congr rfl
            (fun cell _hcell => by
              rw [abs_mul,
                abs_of_nonneg (scoreCellIndicator_nonneg score cell unit)])
    _ = |weight unit| *
        (∑ cell ∈ cells, scoreCellIndicator score cell unit) := by
          rw [← Finset.mul_sum]
    _ = |weight unit| := by
          rw [sum_scoreCellIndicator_eq_one_of_mem cells score unit hmem]
          ring

/--
If a finite score partition does not contain a unit's score, the weighted
indicator vector over the partition is zero in `L1`.
-/
theorem sum_abs_weight_mul_scoreCellIndicator_eq_zero_of_not_mem
    (cells : Finset Cell) (weight : Unit -> Real)
    (score : Unit -> Cell) (unit : Unit)
    (hnot_mem : score unit ∉ cells) :
    (∑ cell ∈ cells,
      |weight unit * scoreCellIndicator score cell unit|) = 0 := by
  exact Finset.sum_eq_zero
    (fun cell hcell => by
      have hne : score unit ≠ cell := by
        intro h
        exact hnot_mem (h.symm ▸ hcell)
      rw [scoreCellIndicator_of_ne score cell unit hne]
      simp)

/--
For any finite score set, the `L1` norm of a unit's weighted indicator vector
is bounded by the absolute weight.
-/
theorem sum_abs_weight_mul_scoreCellIndicator_le_abs_weight
    (cells : Finset Cell) (weight : Unit -> Real)
    (score : Unit -> Cell) (unit : Unit) :
    (∑ cell ∈ cells,
      |weight unit * scoreCellIndicator score cell unit|) ≤
      |weight unit| := by
  by_cases hmem : score unit ∈ cells
  · rw [sum_abs_weight_mul_scoreCellIndicator_eq_abs_weight_of_mem
      cells weight score unit hmem]
  · rw [sum_abs_weight_mul_scoreCellIndicator_eq_zero_of_not_mem
      cells weight score unit hmem]
    exact abs_nonneg (weight unit)

/-- A weight envelope bounds the finite indicator vector in `L1`. -/
theorem sum_abs_weight_mul_scoreCellIndicator_le_bound
    (cells : Finset Cell) (weight : Unit -> Real)
    (score : Unit -> Cell) (unit : Unit) (bound : Real)
    (hweight : |weight unit| ≤ bound) :
    (∑ cell ∈ cells,
      |weight unit * scoreCellIndicator score cell unit|) ≤ bound :=
  (sum_abs_weight_mul_scoreCellIndicator_le_abs_weight
    cells weight score unit).trans hweight

/-- PATE finite-vector weighted indicator `L1` bound. -/
theorem sum_abs_weight_mul_pateDoubleScoreCellIndicator_le_bound
    (cells :
      Finset ((PropensityCell × TreatedProgCell) × ControlProgCell))
    (weight : Unit -> Real)
    (propensityScore : Unit -> PropensityCell)
    (treatedPrognosticScore : Unit -> TreatedProgCell)
    (controlPrognosticScore : Unit -> ControlProgCell)
    (unit : Unit) (bound : Real)
    (hweight : |weight unit| ≤ bound) :
    (∑ cell ∈ cells,
      |weight unit *
        scoreCellIndicator
          (pateDoubleScore propensityScore treatedPrognosticScore
            controlPrognosticScore) cell unit|) ≤ bound :=
  sum_abs_weight_mul_scoreCellIndicator_le_bound cells weight
    (pateDoubleScore propensityScore treatedPrognosticScore
      controlPrognosticScore) unit bound hweight

/-- PATT finite-vector weighted indicator `L1` bound. -/
theorem sum_abs_weight_mul_pattDoubleScoreCellIndicator_le_bound
    (cells : Finset (PropensityCell × PATTProgCell))
    (weight : Unit -> Real)
    (propensityScore : Unit -> PropensityCell)
    (controlPrognosticScore : Unit -> PATTProgCell)
    (unit : Unit) (bound : Real)
    (hweight : |weight unit| ≤ bound) :
    (∑ cell ∈ cells,
      |weight unit *
        scoreCellIndicator
          (pattDoubleScore propensityScore controlPrognosticScore)
          cell unit|) ≤ bound :=
  sum_abs_weight_mul_scoreCellIndicator_le_bound cells weight
    (pattDoubleScore propensityScore controlPrognosticScore) unit bound
    hweight

/--
Paired PATE/PATT finite-vector weighted indicator `L1` bounds over the two
double-score partitions.
-/
theorem sum_abs_weight_mul_pate_pattDoubleScoreCellIndicator_le_bound
    (pateCells :
      Finset ((PropensityCell × TreatedProgCell) × ControlProgCell))
    (pattCells : Finset (PropensityCell × PATTProgCell))
    (pateWeight pattWeight : Unit -> Real)
    (propensityScore : Unit -> PropensityCell)
    (treatedPrognosticScore : Unit -> TreatedProgCell)
    (controlPrognosticScore : Unit -> ControlProgCell)
    (pattPrognosticScore : Unit -> PATTProgCell)
    (unit : Unit) (pateBound pattBound : Real)
    (hpateWeight : |pateWeight unit| ≤ pateBound)
    (hpattWeight : |pattWeight unit| ≤ pattBound) :
    (∑ cell ∈ pateCells,
      |pateWeight unit *
        scoreCellIndicator
          (pateDoubleScore propensityScore treatedPrognosticScore
            controlPrognosticScore) cell unit|) ≤ pateBound ∧
      (∑ cell ∈ pattCells,
        |pattWeight unit *
          scoreCellIndicator
            (pattDoubleScore propensityScore pattPrognosticScore)
            cell unit|) ≤ pattBound := by
  constructor
  · exact
      sum_abs_weight_mul_pateDoubleScoreCellIndicator_le_bound
        pateCells pateWeight propensityScore treatedPrognosticScore
        controlPrognosticScore unit pateBound hpateWeight
  · exact
      sum_abs_weight_mul_pattDoubleScoreCellIndicator_le_bound
        pattCells pattWeight propensityScore pattPrognosticScore unit
        pattBound hpattWeight

end WDSM
end Matching
end StatInference
