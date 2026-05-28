import StatInference.Matching.WDSM.FiniteCellIndicatorMass

/-!
# Bounded score-cell indicator summands

Survey-weighted LLNs for the WDSM finite score partitions need bounded
indicator arrays.  This module proves the deterministic boundedness facts for
unweighted indicators and for weighted indicator summands.
-/

namespace StatInference
namespace Matching
namespace WDSM

variable {Unit Cell PropensityCell TreatedProgCell ControlProgCell PATTProgCell : Type*}
  [DecidableEq Cell] [DecidableEq PropensityCell]
  [DecidableEq TreatedProgCell] [DecidableEq ControlProgCell]
  [DecidableEq PATTProgCell]

/-- A weighted score-cell indicator summand is bounded by the absolute weight. -/
theorem abs_weight_mul_scoreCellIndicator_le_abs_weight
    (weight : Unit -> Real) (score : Unit -> Cell) (cell : Cell)
    (unit : Unit) :
    |weight unit * scoreCellIndicator score cell unit| ≤ |weight unit| := by
  calc
    |weight unit * scoreCellIndicator score cell unit| =
        |weight unit| * |scoreCellIndicator score cell unit| := by
          rw [abs_mul]
    _ ≤ |weight unit| * 1 := by
          exact mul_le_mul_of_nonneg_left
            (abs_scoreCellIndicator_le_one score cell unit) (abs_nonneg _)
    _ = |weight unit| := by ring

/-- A weighted score-cell indicator summand inherits any absolute weight bound. -/
theorem abs_weight_mul_scoreCellIndicator_le_bound
    (weight : Unit -> Real) (score : Unit -> Cell) (cell : Cell)
    (unit : Unit) (bound : Real)
    (hweight : |weight unit| ≤ bound) :
    |weight unit * scoreCellIndicator score cell unit| ≤ bound :=
  (abs_weight_mul_scoreCellIndicator_le_abs_weight
    weight score cell unit).trans hweight

/--
Uniform weight envelopes bound every weighted score-cell indicator over a
fixed finite partition.
-/
theorem forall_mem_abs_weight_mul_scoreCellIndicator_le_bound
    (cells : Finset Cell) (weight : Unit -> Real)
    (score : Unit -> Cell) (bound : Real)
    (hweight : ∀ unit, |weight unit| ≤ bound) :
    ∀ cell, cell ∈ cells -> ∀ unit,
      |weight unit * scoreCellIndicator score cell unit| ≤ bound := by
  intro cell _hmem unit
  exact abs_weight_mul_scoreCellIndicator_le_bound
    weight score cell unit bound (hweight unit)

/-- PATE double-score weighted indicators inherit a uniform weight envelope. -/
theorem forall_mem_abs_weight_mul_pateDoubleScoreCellIndicator_le_bound
    (cells :
      Finset ((PropensityCell × TreatedProgCell) × ControlProgCell))
    (weight : Unit -> Real)
    (propensityScore : Unit -> PropensityCell)
    (treatedPrognosticScore : Unit -> TreatedProgCell)
    (controlPrognosticScore : Unit -> ControlProgCell)
    (bound : Real)
    (hweight : ∀ unit, |weight unit| ≤ bound) :
    ∀ cell, cell ∈ cells -> ∀ unit,
      |weight unit *
          scoreCellIndicator
            (pateDoubleScore propensityScore treatedPrognosticScore
              controlPrognosticScore) cell unit| ≤ bound :=
  forall_mem_abs_weight_mul_scoreCellIndicator_le_bound cells weight
    (pateDoubleScore propensityScore treatedPrognosticScore
      controlPrognosticScore) bound hweight

/-- PATT double-score weighted indicators inherit a uniform weight envelope. -/
theorem forall_mem_abs_weight_mul_pattDoubleScoreCellIndicator_le_bound
    (cells : Finset (PropensityCell × PATTProgCell))
    (weight : Unit -> Real)
    (propensityScore : Unit -> PropensityCell)
    (controlPrognosticScore : Unit -> PATTProgCell)
    (bound : Real)
    (hweight : ∀ unit, |weight unit| ≤ bound) :
    ∀ cell, cell ∈ cells -> ∀ unit,
      |weight unit *
          scoreCellIndicator
            (pattDoubleScore propensityScore controlPrognosticScore)
            cell unit| ≤ bound :=
  forall_mem_abs_weight_mul_scoreCellIndicator_le_bound cells weight
    (pattDoubleScore propensityScore controlPrognosticScore) bound hweight

/-- Constant weights give a uniform bound by the absolute constant weight. -/
theorem forall_mem_abs_constant_weight_mul_scoreCellIndicator_le_abs_weight
    (cells : Finset Cell) (commonWeight : Real)
    (score : Unit -> Cell) :
    ∀ cell, cell ∈ cells -> ∀ unit,
      |commonWeight * scoreCellIndicator score cell unit| ≤ |commonWeight| := by
  intro cell _hmem unit
  simpa using
    abs_weight_mul_scoreCellIndicator_le_abs_weight
      (fun _unit : Unit => commonWeight) score cell unit

/-- PATE double-score constant-weight indicator bound. -/
theorem forall_mem_abs_constant_weight_mul_pateDoubleScoreCellIndicator_le_abs_weight
    (cells :
      Finset ((PropensityCell × TreatedProgCell) × ControlProgCell))
    (commonWeight : Real)
    (propensityScore : Unit -> PropensityCell)
    (treatedPrognosticScore : Unit -> TreatedProgCell)
    (controlPrognosticScore : Unit -> ControlProgCell) :
    ∀ cell, cell ∈ cells -> ∀ unit,
      |commonWeight *
          scoreCellIndicator
            (pateDoubleScore propensityScore treatedPrognosticScore
              controlPrognosticScore) cell unit| ≤ |commonWeight| :=
  forall_mem_abs_constant_weight_mul_scoreCellIndicator_le_abs_weight
    cells commonWeight
    (pateDoubleScore propensityScore treatedPrognosticScore
      controlPrognosticScore)

/-- PATT double-score constant-weight indicator bound. -/
theorem forall_mem_abs_constant_weight_mul_pattDoubleScoreCellIndicator_le_abs_weight
    (cells : Finset (PropensityCell × PATTProgCell))
    (commonWeight : Real)
    (propensityScore : Unit -> PropensityCell)
    (controlPrognosticScore : Unit -> PATTProgCell) :
    ∀ cell, cell ∈ cells -> ∀ unit,
      |commonWeight *
          scoreCellIndicator
            (pattDoubleScore propensityScore controlPrognosticScore)
            cell unit| ≤ |commonWeight| :=
  forall_mem_abs_constant_weight_mul_scoreCellIndicator_le_abs_weight
    cells commonWeight
    (pattDoubleScore propensityScore controlPrognosticScore)

/--
Paired PATE/PATT double-score weighted indicators inherit uniform weight
envelopes over their respective finite score partitions.
-/
theorem forall_mem_abs_weight_mul_pate_pattDoubleScoreCellIndicator_le_bound
    (pateCells :
      Finset ((PropensityCell × TreatedProgCell) × ControlProgCell))
    (pattCells : Finset (PropensityCell × PATTProgCell))
    (pateWeight pattWeight : Unit -> Real)
    (propensityScore : Unit -> PropensityCell)
    (treatedPrognosticScore : Unit -> TreatedProgCell)
    (controlPrognosticScore : Unit -> ControlProgCell)
    (pattPrognosticScore : Unit -> PATTProgCell)
    (pateBound pattBound : Real)
    (hpateWeight : ∀ unit, |pateWeight unit| ≤ pateBound)
    (hpattWeight : ∀ unit, |pattWeight unit| ≤ pattBound) :
    (∀ cell, cell ∈ pateCells -> ∀ unit,
      |pateWeight unit *
          scoreCellIndicator
            (pateDoubleScore propensityScore treatedPrognosticScore
              controlPrognosticScore) cell unit| ≤ pateBound) ∧
      (∀ cell, cell ∈ pattCells -> ∀ unit,
        |pattWeight unit *
            scoreCellIndicator
              (pattDoubleScore propensityScore pattPrognosticScore)
              cell unit| ≤ pattBound) := by
  constructor
  · exact
      forall_mem_abs_weight_mul_pateDoubleScoreCellIndicator_le_bound
        pateCells pateWeight propensityScore treatedPrognosticScore
        controlPrognosticScore pateBound hpateWeight
  · exact
      forall_mem_abs_weight_mul_pattDoubleScoreCellIndicator_le_bound
        pattCells pattWeight propensityScore pattPrognosticScore pattBound
        hpattWeight

/--
Paired PATE/PATT double-score constant-weight indicator bounds over their
respective finite score partitions.
-/
theorem forall_mem_abs_constant_weight_mul_pate_pattDoubleScoreCellIndicator_le_abs_weight
    (pateCells :
      Finset ((PropensityCell × TreatedProgCell) × ControlProgCell))
    (pattCells : Finset (PropensityCell × PATTProgCell))
    (pateCommonWeight pattCommonWeight : Real)
    (propensityScore : Unit -> PropensityCell)
    (treatedPrognosticScore : Unit -> TreatedProgCell)
    (controlPrognosticScore : Unit -> ControlProgCell)
    (pattPrognosticScore : Unit -> PATTProgCell) :
    (∀ cell, cell ∈ pateCells -> ∀ unit,
      |pateCommonWeight *
          scoreCellIndicator
            (pateDoubleScore propensityScore treatedPrognosticScore
              controlPrognosticScore) cell unit| ≤ |pateCommonWeight|) ∧
      (∀ cell, cell ∈ pattCells -> ∀ unit,
        |pattCommonWeight *
            scoreCellIndicator
              (pattDoubleScore propensityScore pattPrognosticScore)
              cell unit| ≤ |pattCommonWeight|) := by
  constructor
  · exact
      forall_mem_abs_constant_weight_mul_pateDoubleScoreCellIndicator_le_abs_weight
        pateCells pateCommonWeight propensityScore treatedPrognosticScore
        controlPrognosticScore
  · exact
      forall_mem_abs_constant_weight_mul_pattDoubleScoreCellIndicator_le_abs_weight
        pattCells pattCommonWeight propensityScore pattPrognosticScore

end WDSM
end Matching
end StatInference
