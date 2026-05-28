import StatInference.Matching.WDSM.DiscreteDoubleScoreBalancing

/-!
# Indicator representation of finite WDSM score-cell masses

The remaining stochastic WDSM target is convergence of finite weighted
score-cell masses.  This module rewrites those masses as ordinary weighted
sums of `0/1` score-cell indicators.  That is the representation needed by
survey-weighted LLN, CLT, or empirical-process tools.
-/

namespace StatInference
namespace Matching
namespace WDSM

open Filter

variable {Unit UnitA UnitB Cell : Type*} [DecidableEq Cell]

/-- Real-valued indicator of membership in one discrete score cell. -/
def scoreCellIndicator (score : Unit -> Cell) (cell : Cell) (unit : Unit) :
    Real :=
  if score unit = cell then 1 else 0

theorem scoreCellIndicator_of_eq
    (score : Unit -> Cell) (cell : Cell) (unit : Unit)
    (h : score unit = cell) :
    scoreCellIndicator score cell unit = 1 := by
  simp [scoreCellIndicator, h]

theorem scoreCellIndicator_of_ne
    (score : Unit -> Cell) (cell : Cell) (unit : Unit)
    (h : score unit ≠ cell) :
    scoreCellIndicator score cell unit = 0 := by
  simp [scoreCellIndicator, h]

theorem scoreCellIndicator_nonneg
    (score : Unit -> Cell) (cell : Cell) (unit : Unit) :
    0 ≤ scoreCellIndicator score cell unit := by
  unfold scoreCellIndicator
  split_ifs <;> norm_num

theorem scoreCellIndicator_le_one
    (score : Unit -> Cell) (cell : Cell) (unit : Unit) :
    scoreCellIndicator score cell unit ≤ 1 := by
  unfold scoreCellIndicator
  split_ifs <;> norm_num

theorem abs_scoreCellIndicator_le_one
    (score : Unit -> Cell) (cell : Cell) (unit : Unit) :
    |scoreCellIndicator score cell unit| ≤ 1 := by
  unfold scoreCellIndicator
  split_ifs <;> norm_num

/-- Weighted total mass is the weighted sum of the constant-one outcome. -/
theorem weightedSampleSum_one_eq_weightedSampleTotal
    (sample : Finset Unit) (weight : Unit -> Real) :
    weightedSampleSum sample weight (fun _unit => (1 : Real)) =
      weightedSampleTotal sample weight := by
  unfold weightedSampleSum weightedSampleTotal
  exact Finset.sum_congr rfl (fun _unit _hunit => by ring)

/--
The weighted mass of one score cell is exactly the weighted sum of its
real-valued cell indicator.
-/
theorem weightedSampleSum_scoreCellIndicator_eq_scoreCellMass
    (sample : Finset Unit) (weight : Unit -> Real)
    (score : Unit -> Cell) (cell : Cell) :
    weightedSampleSum sample weight (scoreCellIndicator score cell) =
      scoreCellMass sample weight score cell := by
  unfold weightedSampleSum scoreCellMass scoreCellIndicator
  rw [Finset.sum_filter]
  exact Finset.sum_congr rfl
    (fun unit _hunit => by
      by_cases h : score unit = cell
      · simp [h]
      · simp [h])

theorem scoreCellMass_eq_weightedSampleSum_scoreCellIndicator
    (sample : Finset Unit) (weight : Unit -> Real)
    (score : Unit -> Cell) (cell : Cell) :
    scoreCellMass sample weight score cell =
      weightedSampleSum sample weight (scoreCellIndicator score cell) :=
  (weightedSampleSum_scoreCellIndicator_eq_scoreCellMass
    sample weight score cell).symm

/--
Cell-mass differences can be targeted as differences of ordinary weighted
indicator sums.
-/
theorem scoreCellMass_sub_eq_weightedSampleSum_indicator_sub
    (sampleA : Finset UnitA) (sampleB : Finset UnitB)
    (weightA : UnitA -> Real) (weightB : UnitB -> Real)
    (scoreA : UnitA -> Cell) (scoreB : UnitB -> Cell)
    (cell : Cell) :
    scoreCellMass sampleA weightA scoreA cell -
        scoreCellMass sampleB weightB scoreB cell =
      weightedSampleSum sampleA weightA (scoreCellIndicator scoreA cell) -
        weightedSampleSum sampleB weightB (scoreCellIndicator scoreB cell) := by
  rw [scoreCellMass_eq_weightedSampleSum_scoreCellIndicator]
  rw [scoreCellMass_eq_weightedSampleSum_scoreCellIndicator]

/--
Scaled cell-mass differences are scaled differences of weighted indicator
sums.
-/
theorem scaled_scoreCellMass_sub_eq_scaled_weightedSampleSum_indicator_sub
    (scale : Real)
    (sampleA : Finset UnitA) (sampleB : Finset UnitB)
    (weightA : UnitA -> Real) (weightB : UnitB -> Real)
    (scoreA : UnitA -> Cell) (scoreB : UnitB -> Cell)
    (cell : Cell) :
    scale *
        (scoreCellMass sampleA weightA scoreA cell -
          scoreCellMass sampleB weightB scoreB cell) =
      scale *
        (weightedSampleSum sampleA weightA (scoreCellIndicator scoreA cell) -
          weightedSampleSum sampleB weightB
            (scoreCellIndicator scoreB cell)) := by
  rw [scoreCellMass_sub_eq_weightedSampleSum_indicator_sub]

variable {Index : Type*} {l : Filter Index}

/--
Convergence of weighted cell-indicator sums is exactly convergence of
weighted score-cell masses.
-/
theorem tendsto_scoreCellMass_of_tendsto_weightedSampleSum_indicator
    (sample : Index -> Finset Unit) (weight : Index -> Unit -> Real)
    (score : Index -> Unit -> Cell) (cell : Cell)
    (massLimit : Real)
    (hindicator :
      Tendsto
        (fun index =>
          weightedSampleSum (sample index) (weight index)
            (scoreCellIndicator (score index) cell))
        l (nhds massLimit)) :
    Tendsto
      (fun index =>
        scoreCellMass (sample index) (weight index) (score index) cell)
      l (nhds massLimit) := by
  convert hindicator using 1
  ext index
  exact scoreCellMass_eq_weightedSampleSum_scoreCellIndicator
    (sample index) (weight index) (score index) cell

/--
Scaled convergence of weighted cell-indicator sum differences is exactly
scaled convergence of weighted score-cell mass differences.
-/
theorem tendsto_scaled_scoreCellMass_sub_of_tendsto_scaled_weightedSampleSum_indicator_sub
    (scale : Index -> Real)
    (sampleA : Index -> Finset UnitA) (sampleB : Index -> Finset UnitB)
    (weightA : Index -> UnitA -> Real)
    (weightB : Index -> UnitB -> Real)
    (scoreA : Index -> UnitA -> Cell)
    (scoreB : Index -> UnitB -> Cell)
    (cell : Cell)
    (hindicator :
      Tendsto
        (fun index =>
          scale index *
            (weightedSampleSum (sampleA index) (weightA index)
                (scoreCellIndicator (scoreA index) cell) -
              weightedSampleSum (sampleB index) (weightB index)
                (scoreCellIndicator (scoreB index) cell)))
        l (nhds 0)) :
    Tendsto
      (fun index =>
        scale index *
          (scoreCellMass (sampleA index) (weightA index)
              (scoreA index) cell -
            scoreCellMass (sampleB index) (weightB index)
              (scoreB index) cell))
      l (nhds 0) := by
  convert hindicator using 1
  ext index
  exact scaled_scoreCellMass_sub_eq_scaled_weightedSampleSum_indicator_sub
    (scale index) (sampleA index) (sampleB index) (weightA index)
    (weightB index) (scoreA index) (scoreB index) cell

variable {PropensityCell TreatedProgCell ControlProgCell PATTProgCell : Type*}
  [DecidableEq PropensityCell] [DecidableEq TreatedProgCell]
  [DecidableEq ControlProgCell] [DecidableEq PATTProgCell]

theorem weightedSampleSum_pateDoubleScoreCellIndicator_eq_scoreCellMass
    (sample : Finset Unit) (weight : Unit -> Real)
    (propensityScore : Unit -> PropensityCell)
    (treatedPrognosticScore : Unit -> TreatedProgCell)
    (controlPrognosticScore : Unit -> ControlProgCell)
    (cell : (PropensityCell × TreatedProgCell) × ControlProgCell) :
    weightedSampleSum sample weight
        (scoreCellIndicator
          (pateDoubleScore propensityScore treatedPrognosticScore
            controlPrognosticScore) cell) =
      scoreCellMass sample weight
        (pateDoubleScore propensityScore treatedPrognosticScore
          controlPrognosticScore) cell :=
  weightedSampleSum_scoreCellIndicator_eq_scoreCellMass sample weight
    (pateDoubleScore propensityScore treatedPrognosticScore
      controlPrognosticScore) cell

theorem weightedSampleSum_pattDoubleScoreCellIndicator_eq_scoreCellMass
    (sample : Finset Unit) (weight : Unit -> Real)
    (propensityScore : Unit -> PropensityCell)
    (controlPrognosticScore : Unit -> PATTProgCell)
    (cell : PropensityCell × PATTProgCell) :
    weightedSampleSum sample weight
        (scoreCellIndicator
          (pattDoubleScore propensityScore controlPrognosticScore) cell) =
      scoreCellMass sample weight
        (pattDoubleScore propensityScore controlPrognosticScore) cell :=
  weightedSampleSum_scoreCellIndicator_eq_scoreCellMass sample weight
    (pattDoubleScore propensityScore controlPrognosticScore) cell

theorem tendsto_pateDoubleScoreCellMass_of_tendsto_indicator
    (sample : Index -> Finset Unit) (weight : Index -> Unit -> Real)
    (propensityScore : Index -> Unit -> PropensityCell)
    (treatedPrognosticScore : Index -> Unit -> TreatedProgCell)
    (controlPrognosticScore : Index -> Unit -> ControlProgCell)
    (cell : (PropensityCell × TreatedProgCell) × ControlProgCell)
    (massLimit : Real)
    (hindicator :
      Tendsto
        (fun index =>
          weightedSampleSum (sample index) (weight index)
            (scoreCellIndicator
              (pateDoubleScore (propensityScore index)
                (treatedPrognosticScore index)
                (controlPrognosticScore index)) cell))
        l (nhds massLimit)) :
    Tendsto
      (fun index =>
        scoreCellMass (sample index) (weight index)
          (pateDoubleScore (propensityScore index)
            (treatedPrognosticScore index)
            (controlPrognosticScore index)) cell)
      l (nhds massLimit) :=
  tendsto_scoreCellMass_of_tendsto_weightedSampleSum_indicator
    sample weight
    (fun index =>
      pateDoubleScore (propensityScore index)
        (treatedPrognosticScore index) (controlPrognosticScore index))
    cell massLimit hindicator

theorem tendsto_pattDoubleScoreCellMass_of_tendsto_indicator
    (sample : Index -> Finset Unit) (weight : Index -> Unit -> Real)
    (propensityScore : Index -> Unit -> PropensityCell)
    (controlPrognosticScore : Index -> Unit -> PATTProgCell)
    (cell : PropensityCell × PATTProgCell)
    (massLimit : Real)
    (hindicator :
      Tendsto
        (fun index =>
          weightedSampleSum (sample index) (weight index)
            (scoreCellIndicator
              (pattDoubleScore (propensityScore index)
                (controlPrognosticScore index)) cell))
        l (nhds massLimit)) :
    Tendsto
      (fun index =>
        scoreCellMass (sample index) (weight index)
          (pattDoubleScore (propensityScore index)
            (controlPrognosticScore index)) cell)
      l (nhds massLimit) :=
  tendsto_scoreCellMass_of_tendsto_weightedSampleSum_indicator
    sample weight
    (fun index =>
      pattDoubleScore (propensityScore index)
        (controlPrognosticScore index))
    cell massLimit hindicator

end WDSM
end Matching
end StatInference
