import StatInference.Matching.WDSM.FiniteCellIndicatorMass
import StatInference.Matching.WDSM.ProspectiveScoreCellShare

/-!
# Prospective normalized counts as weighted indicator sums

This module connects the prospective normalized-count route to the finite
score-cell indicator LLN route.  A normalized cell count is exactly a weighted
sum of the score-cell indicator when the weight is the normalizer, and the
same holds for normalized total counts with the constant-one outcome.
-/

namespace StatInference
namespace Matching
namespace WDSM

open Filter

variable {Index Unit Cell PropensityCell TreatedProgCell ControlProgCell PATTProgCell : Type*}
  {l : Filter Index}
  [DecidableEq Cell] [DecidableEq PropensityCell]
  [DecidableEq TreatedProgCell] [DecidableEq ControlProgCell]
  [DecidableEq PATTProgCell]

/--
A normalized finite score-cell count is a weighted indicator sum with constant
weight equal to the normalizer.
-/
theorem normalized_cell_count_eq_weightedSampleSum_indicator_constant_weight
    (sample : Finset Unit) (score : Unit -> Cell) (cell : Cell)
    (normalizer : Real) :
    normalizer *
        (((sample.filter (fun unit => score unit = cell)).card : Real)) =
      weightedSampleSum sample (fun _unit => normalizer)
        (scoreCellIndicator score cell) := by
  rw [weightedSampleSum_scoreCellIndicator_eq_scoreCellMass,
    scoreCellMass_constant_weight_eq_card]

/--
A normalized finite sample size is a weighted constant-one sum with constant
weight equal to the normalizer.
-/
theorem normalized_total_count_eq_weightedSampleSum_one_constant_weight
    (sample : Finset Unit) (normalizer : Real) :
    normalizer * (sample.card : Real) =
      weightedSampleSum sample (fun _unit => normalizer)
        (fun _unit => (1 : Real)) := by
  rw [weightedSampleSum_one_eq_weightedSampleTotal,
    weightedSampleTotal_eq_weightedDenominator,
    weightedDenominator_constant_weight_eq_card]

/--
Convergence of constant-normalizer weighted score-cell indicator sums gives
convergence of the corresponding prospective normalized cell counts.
-/
theorem tendsto_normalized_cell_count_of_tendsto_weightedSampleSum_indicator_constant_weight
    (sample : Index -> Finset Unit)
    (score : Index -> Unit -> Cell)
    (normalizer : Index -> Real)
    (cell : Cell)
    (cellLimit : Real)
    (hindicator :
      Tendsto
        (fun index =>
          weightedSampleSum (sample index)
            (fun _unit => normalizer index)
            (scoreCellIndicator (score index) cell))
        l (nhds cellLimit)) :
    Tendsto
      (fun index =>
        normalizer index *
          (((sample index).filter
            (fun unit => score index unit = cell)).card : Real))
      l (nhds cellLimit) := by
  convert hindicator using 1
  ext index
  exact
    normalized_cell_count_eq_weightedSampleSum_indicator_constant_weight
      (sample index) (score index) cell (normalizer index)

/--
Convergence of constant-normalizer weighted constant-one sums gives convergence
of the corresponding prospective normalized sample sizes.
-/
theorem tendsto_normalized_total_count_of_tendsto_weightedSampleSum_one_constant_weight
    (sample : Index -> Finset Unit)
    (normalizer : Index -> Real)
    (totalLimit : Real)
    (hone :
      Tendsto
        (fun index =>
          weightedSampleSum (sample index)
            (fun _unit => normalizer index)
            (fun _unit => (1 : Real)))
        l (nhds totalLimit)) :
    Tendsto
      (fun index =>
        normalizer index * ((sample index).card : Real))
      l (nhds totalLimit) := by
  convert hone using 1
  ext index
  exact normalized_total_count_eq_weightedSampleSum_one_constant_weight
    (sample index) (normalizer index)

/--
PATE double-score specialization of the indicator-sum to normalized cell-count
convergence bridge.
-/
theorem tendsto_pate_normalized_cell_count_of_tendsto_indicator_constant_weight
    (sample : Index -> Finset Unit)
    (propensityScore : Index -> Unit -> PropensityCell)
    (treatedPrognosticScore : Index -> Unit -> TreatedProgCell)
    (controlPrognosticScore : Index -> Unit -> ControlProgCell)
    (normalizer : Index -> Real)
    (cell : (PropensityCell × TreatedProgCell) × ControlProgCell)
    (cellLimit : Real)
    (hindicator :
      Tendsto
        (fun index =>
          weightedSampleSum (sample index)
            (fun _unit => normalizer index)
            (scoreCellIndicator
              (pateDoubleScore (propensityScore index)
                (treatedPrognosticScore index)
                (controlPrognosticScore index)) cell))
        l (nhds cellLimit)) :
    Tendsto
      (fun index =>
        normalizer index *
          (((sample index).filter
            (fun unit =>
              pateDoubleScore (propensityScore index)
                (treatedPrognosticScore index)
                (controlPrognosticScore index) unit = cell)).card :
            Real))
      l (nhds cellLimit) :=
  tendsto_normalized_cell_count_of_tendsto_weightedSampleSum_indicator_constant_weight
    sample
    (fun index =>
      pateDoubleScore (propensityScore index)
        (treatedPrognosticScore index)
        (controlPrognosticScore index))
    normalizer cell cellLimit hindicator

/--
PATT double-score specialization of the indicator-sum to normalized cell-count
convergence bridge.
-/
theorem tendsto_patt_normalized_cell_count_of_tendsto_indicator_constant_weight
    (sample : Index -> Finset Unit)
    (propensityScore : Index -> Unit -> PropensityCell)
    (controlPrognosticScore : Index -> Unit -> PATTProgCell)
    (normalizer : Index -> Real)
    (cell : PropensityCell × PATTProgCell)
    (cellLimit : Real)
    (hindicator :
      Tendsto
        (fun index =>
          weightedSampleSum (sample index)
            (fun _unit => normalizer index)
            (scoreCellIndicator
              (pattDoubleScore (propensityScore index)
                (controlPrognosticScore index)) cell))
        l (nhds cellLimit)) :
    Tendsto
      (fun index =>
        normalizer index *
          (((sample index).filter
            (fun unit =>
              pattDoubleScore (propensityScore index)
                (controlPrognosticScore index) unit = cell)).card :
            Real))
      l (nhds cellLimit) :=
  tendsto_normalized_cell_count_of_tendsto_weightedSampleSum_indicator_constant_weight
    sample
    (fun index =>
      pattDoubleScore (propensityScore index)
        (controlPrognosticScore index))
    normalizer cell cellLimit hindicator

/--
Finite PATE partition wrapper: cellwise indicator-sum LLNs imply the
normalized PATE double-score cell-count limits needed by the prospective route.
-/
theorem tendsto_all_pate_normalized_cell_counts_of_tendsto_indicators_constant_weight
    (sample : Index -> Finset Unit)
    (propensityScore : Index -> Unit -> PropensityCell)
    (treatedPrognosticScore : Index -> Unit -> TreatedProgCell)
    (controlPrognosticScore : Index -> Unit -> ControlProgCell)
    (cells :
      Finset ((PropensityCell × TreatedProgCell) × ControlProgCell))
    (normalizer : Index -> Real)
    (cellLimit :
      (PropensityCell × TreatedProgCell) × ControlProgCell -> Real)
    (hindicator :
      ∀ cell, cell ∈ cells ->
        Tendsto
          (fun index =>
            weightedSampleSum (sample index)
              (fun _unit => normalizer index)
              (scoreCellIndicator
                (pateDoubleScore (propensityScore index)
                  (treatedPrognosticScore index)
                  (controlPrognosticScore index)) cell))
          l (nhds (cellLimit cell))) :
    ∀ cell, cell ∈ cells ->
      Tendsto
        (fun index =>
          normalizer index *
            (((sample index).filter
              (fun unit =>
                pateDoubleScore (propensityScore index)
                  (treatedPrognosticScore index)
                  (controlPrognosticScore index) unit = cell)).card :
              Real))
        l (nhds (cellLimit cell)) := by
  intro cell hmem
  exact
    tendsto_pate_normalized_cell_count_of_tendsto_indicator_constant_weight
      sample propensityScore treatedPrognosticScore controlPrognosticScore
      normalizer cell (cellLimit cell) (hindicator cell hmem)

/--
Finite PATT partition wrapper: cellwise indicator-sum LLNs imply the
normalized PATT double-score cell-count limits needed by the prospective route.
-/
theorem tendsto_all_patt_normalized_cell_counts_of_tendsto_indicators_constant_weight
    (sample : Index -> Finset Unit)
    (propensityScore : Index -> Unit -> PropensityCell)
    (controlPrognosticScore : Index -> Unit -> PATTProgCell)
    (cells : Finset (PropensityCell × PATTProgCell))
    (normalizer : Index -> Real)
    (cellLimit : PropensityCell × PATTProgCell -> Real)
    (hindicator :
      ∀ cell, cell ∈ cells ->
        Tendsto
          (fun index =>
            weightedSampleSum (sample index)
              (fun _unit => normalizer index)
              (scoreCellIndicator
                (pattDoubleScore (propensityScore index)
                  (controlPrognosticScore index)) cell))
          l (nhds (cellLimit cell))) :
    ∀ cell, cell ∈ cells ->
      Tendsto
        (fun index =>
          normalizer index *
            (((sample index).filter
              (fun unit =>
                pattDoubleScore (propensityScore index)
                  (controlPrognosticScore index) unit = cell)).card :
              Real))
    l (nhds (cellLimit cell)) := by
  intro cell hmem
  exact
    tendsto_patt_normalized_cell_count_of_tendsto_indicator_constant_weight
      sample propensityScore controlPrognosticScore normalizer cell
      (cellLimit cell) (hindicator cell hmem)

/--
Paired finite PATE/PATT partition wrapper: cellwise indicator-sum LLNs imply
the normalized double-score cell-count limits needed by both prospective routes.
-/
theorem tendsto_all_pate_patt_normalized_cell_counts_of_tendsto_indicators_constant_weight
    (sample : Index -> Finset Unit)
    (propensityScore : Index -> Unit -> PropensityCell)
    (treatedPrognosticScore : Index -> Unit -> TreatedProgCell)
    (controlPrognosticScore : Index -> Unit -> ControlProgCell)
    (pattPrognosticScore : Index -> Unit -> PATTProgCell)
    (pateCells :
      Finset ((PropensityCell × TreatedProgCell) × ControlProgCell))
    (pattCells : Finset (PropensityCell × PATTProgCell))
    (normalizer : Index -> Real)
    (pateCellLimit :
      (PropensityCell × TreatedProgCell) × ControlProgCell -> Real)
    (pattCellLimit : PropensityCell × PATTProgCell -> Real)
    (hpateIndicator :
      ∀ cell, cell ∈ pateCells ->
        Tendsto
          (fun index =>
            weightedSampleSum (sample index)
              (fun _unit => normalizer index)
              (scoreCellIndicator
                (pateDoubleScore (propensityScore index)
                  (treatedPrognosticScore index)
                  (controlPrognosticScore index)) cell))
          l (nhds (pateCellLimit cell)))
    (hpattIndicator :
      ∀ cell, cell ∈ pattCells ->
        Tendsto
          (fun index =>
            weightedSampleSum (sample index)
              (fun _unit => normalizer index)
              (scoreCellIndicator
                (pattDoubleScore (propensityScore index)
                  (pattPrognosticScore index)) cell))
          l (nhds (pattCellLimit cell))) :
    (∀ cell, cell ∈ pateCells ->
      Tendsto
        (fun index =>
          normalizer index *
            (((sample index).filter
              (fun unit =>
                pateDoubleScore (propensityScore index)
                  (treatedPrognosticScore index)
                  (controlPrognosticScore index) unit = cell)).card :
              Real))
        l (nhds (pateCellLimit cell))) ∧
      (∀ cell, cell ∈ pattCells ->
        Tendsto
          (fun index =>
            normalizer index *
              (((sample index).filter
                (fun unit =>
                  pattDoubleScore (propensityScore index)
                    (pattPrognosticScore index) unit = cell)).card :
                Real))
          l (nhds (pattCellLimit cell))) := by
  constructor
  · exact
      tendsto_all_pate_normalized_cell_counts_of_tendsto_indicators_constant_weight
        sample propensityScore treatedPrognosticScore controlPrognosticScore
        pateCells normalizer pateCellLimit hpateIndicator
  · exact
      tendsto_all_patt_normalized_cell_counts_of_tendsto_indicators_constant_weight
        sample propensityScore pattPrognosticScore pattCells normalizer
        pattCellLimit hpattIndicator

/--
Differences of normalized finite score-cell counts are exactly differences of
the corresponding constant-normalizer weighted indicator sums.
-/
theorem normalized_cell_count_difference_eq_weightedSampleSum_indicator_difference_constant_weight
    (leftSample rightSample : Finset Unit)
    (leftScore rightScore : Unit -> Cell)
    (cell : Cell)
    (leftNormalizer rightNormalizer : Real) :
    leftNormalizer *
        (((leftSample.filter (fun unit => leftScore unit = cell)).card :
          Real)) -
      rightNormalizer *
        (((rightSample.filter (fun unit => rightScore unit = cell)).card :
          Real)) =
      weightedSampleSum leftSample (fun _unit => leftNormalizer)
          (scoreCellIndicator leftScore cell) -
        weightedSampleSum rightSample (fun _unit => rightNormalizer)
          (scoreCellIndicator rightScore cell) := by
  rw [normalized_cell_count_eq_weightedSampleSum_indicator_constant_weight
      leftSample leftScore cell leftNormalizer,
    normalized_cell_count_eq_weightedSampleSum_indicator_constant_weight
      rightSample rightScore cell rightNormalizer]

/--
Differences of normalized total counts are exactly differences of the
corresponding constant-normalizer weighted constant-one sums.
-/
theorem normalized_total_count_difference_eq_weightedSampleSum_one_difference_constant_weight
    (leftSample rightSample : Finset Unit)
    (leftNormalizer rightNormalizer : Real) :
    leftNormalizer * (leftSample.card : Real) -
      rightNormalizer * (rightSample.card : Real) =
      weightedSampleSum leftSample (fun _unit => leftNormalizer)
          (fun _unit => (1 : Real)) -
        weightedSampleSum rightSample (fun _unit => rightNormalizer)
          (fun _unit => (1 : Real)) := by
  rw [normalized_total_count_eq_weightedSampleSum_one_constant_weight
      leftSample leftNormalizer,
    normalized_total_count_eq_weightedSampleSum_one_constant_weight
      rightSample rightNormalizer]

/--
Convergence of constant-normalizer weighted indicator-sum differences gives
convergence of the corresponding normalized cell-count differences.
-/
theorem tendsto_normalized_cell_count_difference_of_tendsto_weightedSampleSum_indicator_difference_constant_weight
    (leftSample rightSample : Index -> Finset Unit)
    (leftScore rightScore : Index -> Unit -> Cell)
    (leftNormalizer rightNormalizer : Index -> Real)
    (cell : Cell)
    (differenceLimit : Real)
    (hindicator :
      Tendsto
        (fun index =>
          weightedSampleSum (leftSample index)
              (fun _unit => leftNormalizer index)
              (scoreCellIndicator (leftScore index) cell) -
            weightedSampleSum (rightSample index)
              (fun _unit => rightNormalizer index)
              (scoreCellIndicator (rightScore index) cell))
        l (nhds differenceLimit)) :
    Tendsto
      (fun index =>
        leftNormalizer index *
            ((((leftSample index).filter
              (fun unit => leftScore index unit = cell)).card : Real)) -
          rightNormalizer index *
            ((((rightSample index).filter
              (fun unit => rightScore index unit = cell)).card : Real)))
      l (nhds differenceLimit) := by
  convert hindicator using 1
  ext index
  exact
    normalized_cell_count_difference_eq_weightedSampleSum_indicator_difference_constant_weight
      (leftSample index) (rightSample index) (leftScore index)
      (rightScore index) cell (leftNormalizer index)
      (rightNormalizer index)

/--
Convergence of constant-normalizer weighted total-indicator differences gives
convergence of the corresponding normalized total-count differences.
-/
theorem tendsto_normalized_total_count_difference_of_tendsto_weightedSampleSum_one_difference_constant_weight
    (leftSample rightSample : Index -> Finset Unit)
    (leftNormalizer rightNormalizer : Index -> Real)
    (differenceLimit : Real)
    (hone :
      Tendsto
        (fun index =>
          weightedSampleSum (leftSample index)
              (fun _unit => leftNormalizer index)
              (fun _unit => (1 : Real)) -
            weightedSampleSum (rightSample index)
              (fun _unit => rightNormalizer index)
              (fun _unit => (1 : Real)))
        l (nhds differenceLimit)) :
    Tendsto
      (fun index =>
        leftNormalizer index * ((leftSample index).card : Real) -
          rightNormalizer index * ((rightSample index).card : Real))
      l (nhds differenceLimit) := by
  convert hone using 1
  ext index
  exact
    normalized_total_count_difference_eq_weightedSampleSum_one_difference_constant_weight
      (leftSample index) (rightSample index) (leftNormalizer index)
      (rightNormalizer index)

/--
PATE double-score specialization of the indicator-sum difference to normalized
cell-count difference bridge.
-/
theorem tendsto_pate_normalized_cell_count_difference_of_tendsto_indicator_difference_constant_weight
    (leftSample rightSample : Index -> Finset Unit)
    (propensityScore : Index -> Unit -> PropensityCell)
    (treatedPrognosticScore : Index -> Unit -> TreatedProgCell)
    (controlPrognosticScore : Index -> Unit -> ControlProgCell)
    (leftNormalizer rightNormalizer : Index -> Real)
    (cell : (PropensityCell × TreatedProgCell) × ControlProgCell)
    (differenceLimit : Real)
    (hindicator :
      Tendsto
        (fun index =>
          weightedSampleSum (leftSample index)
              (fun _unit => leftNormalizer index)
              (scoreCellIndicator
                (pateDoubleScore (propensityScore index)
                  (treatedPrognosticScore index)
                  (controlPrognosticScore index)) cell) -
            weightedSampleSum (rightSample index)
              (fun _unit => rightNormalizer index)
              (scoreCellIndicator
                (pateDoubleScore (propensityScore index)
                  (treatedPrognosticScore index)
                  (controlPrognosticScore index)) cell))
        l (nhds differenceLimit)) :
    Tendsto
      (fun index =>
        leftNormalizer index *
            ((((leftSample index).filter
              (fun unit =>
                pateDoubleScore (propensityScore index)
                  (treatedPrognosticScore index)
                  (controlPrognosticScore index) unit = cell)).card :
              Real)) -
          rightNormalizer index *
            ((((rightSample index).filter
              (fun unit =>
                pateDoubleScore (propensityScore index)
                  (treatedPrognosticScore index)
                  (controlPrognosticScore index) unit = cell)).card :
              Real)))
      l (nhds differenceLimit) :=
  tendsto_normalized_cell_count_difference_of_tendsto_weightedSampleSum_indicator_difference_constant_weight
    leftSample rightSample
    (fun index =>
      pateDoubleScore (propensityScore index)
        (treatedPrognosticScore index)
        (controlPrognosticScore index))
    (fun index =>
      pateDoubleScore (propensityScore index)
        (treatedPrognosticScore index)
        (controlPrognosticScore index))
    leftNormalizer rightNormalizer cell differenceLimit hindicator

/--
PATT double-score specialization of the indicator-sum difference to normalized
cell-count difference bridge.
-/
theorem tendsto_patt_normalized_cell_count_difference_of_tendsto_indicator_difference_constant_weight
    (leftSample rightSample : Index -> Finset Unit)
    (propensityScore : Index -> Unit -> PropensityCell)
    (controlPrognosticScore : Index -> Unit -> PATTProgCell)
    (leftNormalizer rightNormalizer : Index -> Real)
    (cell : PropensityCell × PATTProgCell)
    (differenceLimit : Real)
    (hindicator :
      Tendsto
        (fun index =>
          weightedSampleSum (leftSample index)
              (fun _unit => leftNormalizer index)
              (scoreCellIndicator
                (pattDoubleScore (propensityScore index)
                  (controlPrognosticScore index)) cell) -
            weightedSampleSum (rightSample index)
              (fun _unit => rightNormalizer index)
              (scoreCellIndicator
                (pattDoubleScore (propensityScore index)
                  (controlPrognosticScore index)) cell))
        l (nhds differenceLimit)) :
    Tendsto
      (fun index =>
        leftNormalizer index *
            ((((leftSample index).filter
              (fun unit =>
                pattDoubleScore (propensityScore index)
                  (controlPrognosticScore index) unit = cell)).card :
              Real)) -
          rightNormalizer index *
            ((((rightSample index).filter
              (fun unit =>
                pattDoubleScore (propensityScore index)
                  (controlPrognosticScore index) unit = cell)).card :
              Real)))
      l (nhds differenceLimit) :=
  tendsto_normalized_cell_count_difference_of_tendsto_weightedSampleSum_indicator_difference_constant_weight
    leftSample rightSample
    (fun index =>
      pattDoubleScore (propensityScore index) (controlPrognosticScore index))
    (fun index =>
      pattDoubleScore (propensityScore index) (controlPrognosticScore index))
    leftNormalizer rightNormalizer cell differenceLimit hindicator

/--
Finite PATE partition wrapper: cellwise indicator-sum differences imply the
corresponding cellwise normalized count differences.
-/
theorem tendsto_all_pate_normalized_cell_count_differences_of_tendsto_indicator_differences_constant_weight
    (leftSample rightSample : Index -> Finset Unit)
    (propensityScore : Index -> Unit -> PropensityCell)
    (treatedPrognosticScore : Index -> Unit -> TreatedProgCell)
    (controlPrognosticScore : Index -> Unit -> ControlProgCell)
    (cells :
      Finset ((PropensityCell × TreatedProgCell) × ControlProgCell))
    (leftNormalizer rightNormalizer : Index -> Real)
    (differenceLimit :
      (PropensityCell × TreatedProgCell) × ControlProgCell -> Real)
    (hindicator :
      ∀ cell, cell ∈ cells ->
        Tendsto
          (fun index =>
            weightedSampleSum (leftSample index)
                (fun _unit => leftNormalizer index)
                (scoreCellIndicator
                  (pateDoubleScore (propensityScore index)
                    (treatedPrognosticScore index)
                    (controlPrognosticScore index)) cell) -
              weightedSampleSum (rightSample index)
                (fun _unit => rightNormalizer index)
                (scoreCellIndicator
                  (pateDoubleScore (propensityScore index)
                    (treatedPrognosticScore index)
                    (controlPrognosticScore index)) cell))
          l (nhds (differenceLimit cell))) :
    ∀ cell, cell ∈ cells ->
      Tendsto
        (fun index =>
          leftNormalizer index *
              ((((leftSample index).filter
                (fun unit =>
                  pateDoubleScore (propensityScore index)
                    (treatedPrognosticScore index)
                    (controlPrognosticScore index) unit = cell)).card :
                Real)) -
            rightNormalizer index *
              ((((rightSample index).filter
                (fun unit =>
                  pateDoubleScore (propensityScore index)
                    (treatedPrognosticScore index)
                    (controlPrognosticScore index) unit = cell)).card :
                Real)))
        l (nhds (differenceLimit cell)) := by
  intro cell hmem
  exact
    tendsto_pate_normalized_cell_count_difference_of_tendsto_indicator_difference_constant_weight
      leftSample rightSample propensityScore treatedPrognosticScore
      controlPrognosticScore leftNormalizer rightNormalizer cell
      (differenceLimit cell) (hindicator cell hmem)

/--
Finite PATT partition wrapper: cellwise indicator-sum differences imply the
corresponding cellwise normalized count differences.
-/
theorem tendsto_all_patt_normalized_cell_count_differences_of_tendsto_indicator_differences_constant_weight
    (leftSample rightSample : Index -> Finset Unit)
    (propensityScore : Index -> Unit -> PropensityCell)
    (controlPrognosticScore : Index -> Unit -> PATTProgCell)
    (cells : Finset (PropensityCell × PATTProgCell))
    (leftNormalizer rightNormalizer : Index -> Real)
    (differenceLimit : PropensityCell × PATTProgCell -> Real)
    (hindicator :
      ∀ cell, cell ∈ cells ->
        Tendsto
          (fun index =>
            weightedSampleSum (leftSample index)
                (fun _unit => leftNormalizer index)
                (scoreCellIndicator
                  (pattDoubleScore (propensityScore index)
                    (controlPrognosticScore index)) cell) -
              weightedSampleSum (rightSample index)
                (fun _unit => rightNormalizer index)
                (scoreCellIndicator
                  (pattDoubleScore (propensityScore index)
                    (controlPrognosticScore index)) cell))
          l (nhds (differenceLimit cell))) :
    ∀ cell, cell ∈ cells ->
      Tendsto
        (fun index =>
          leftNormalizer index *
              ((((leftSample index).filter
                (fun unit =>
                  pattDoubleScore (propensityScore index)
                    (controlPrognosticScore index) unit = cell)).card :
                Real)) -
            rightNormalizer index *
              ((((rightSample index).filter
                (fun unit =>
                  pattDoubleScore (propensityScore index)
                    (controlPrognosticScore index) unit = cell)).card :
                Real)))
        l (nhds (differenceLimit cell)) := by
  intro cell hmem
  exact
    tendsto_patt_normalized_cell_count_difference_of_tendsto_indicator_difference_constant_weight
      leftSample rightSample propensityScore controlPrognosticScore
      leftNormalizer rightNormalizer cell (differenceLimit cell)
      (hindicator cell hmem)

/--
Scaled differences of normalized finite score-cell counts are exactly scaled
differences of the corresponding constant-normalizer weighted indicator sums.
-/
theorem scaled_normalized_cell_count_difference_eq_scaled_weightedSampleSum_indicator_difference_constant_weight
    (scale : Real)
    (leftSample rightSample : Finset Unit)
    (leftScore rightScore : Unit -> Cell)
    (cell : Cell)
    (leftNormalizer rightNormalizer : Real) :
    scale *
        (leftNormalizer *
            (((leftSample.filter (fun unit => leftScore unit = cell)).card :
              Real)) -
          rightNormalizer *
            (((rightSample.filter (fun unit => rightScore unit = cell)).card :
              Real))) =
      scale *
        (weightedSampleSum leftSample (fun _unit => leftNormalizer)
            (scoreCellIndicator leftScore cell) -
          weightedSampleSum rightSample (fun _unit => rightNormalizer)
            (scoreCellIndicator rightScore cell)) := by
  rw [normalized_cell_count_eq_weightedSampleSum_indicator_constant_weight
      leftSample leftScore cell leftNormalizer,
    normalized_cell_count_eq_weightedSampleSum_indicator_constant_weight
      rightSample rightScore cell rightNormalizer]

/--
Scaled differences of normalized total counts are exactly scaled differences of
the corresponding constant-normalizer weighted constant-one sums.
-/
theorem scaled_normalized_total_count_difference_eq_scaled_weightedSampleSum_one_difference_constant_weight
    (scale : Real)
    (leftSample rightSample : Finset Unit)
    (leftNormalizer rightNormalizer : Real) :
    scale *
        (leftNormalizer * (leftSample.card : Real) -
          rightNormalizer * (rightSample.card : Real)) =
      scale *
        (weightedSampleSum leftSample (fun _unit => leftNormalizer)
            (fun _unit => (1 : Real)) -
          weightedSampleSum rightSample (fun _unit => rightNormalizer)
            (fun _unit => (1 : Real))) := by
  rw [normalized_total_count_eq_weightedSampleSum_one_constant_weight
      leftSample leftNormalizer,
    normalized_total_count_eq_weightedSampleSum_one_constant_weight
      rightSample rightNormalizer]

/--
Convergence of scaled constant-normalizer weighted indicator-sum differences
gives convergence of the corresponding scaled normalized cell-count
differences.
-/
theorem tendsto_scaled_normalized_cell_count_difference_of_tendsto_scaled_weightedSampleSum_indicator_difference_constant_weight
    (scale : Index -> Real)
    (leftSample rightSample : Index -> Finset Unit)
    (leftScore rightScore : Index -> Unit -> Cell)
    (leftNormalizer rightNormalizer : Index -> Real)
    (cell : Cell)
    (differenceLimit : Real)
    (hindicator :
      Tendsto
        (fun index =>
          scale index *
            (weightedSampleSum (leftSample index)
                (fun _unit => leftNormalizer index)
                (scoreCellIndicator (leftScore index) cell) -
              weightedSampleSum (rightSample index)
                (fun _unit => rightNormalizer index)
                (scoreCellIndicator (rightScore index) cell)))
        l (nhds differenceLimit)) :
    Tendsto
      (fun index =>
        scale index *
          (leftNormalizer index *
              ((((leftSample index).filter
                (fun unit => leftScore index unit = cell)).card : Real)) -
            rightNormalizer index *
              ((((rightSample index).filter
                (fun unit => rightScore index unit = cell)).card : Real))))
      l (nhds differenceLimit) := by
  convert hindicator using 1
  ext index
  exact
    scaled_normalized_cell_count_difference_eq_scaled_weightedSampleSum_indicator_difference_constant_weight
      (scale index) (leftSample index) (rightSample index)
      (leftScore index) (rightScore index) cell
      (leftNormalizer index) (rightNormalizer index)

/--
Ordinary and scaled normalized cell-count difference convergence from ordinary
and scaled weighted score-cell indicator-sum difference convergence.
-/
theorem tendsto_normalized_cell_count_difference_zero_and_scaled_zero_of_tendsto_weightedSampleSum_indicator_difference_constant_weight
    (scale : Index -> Real)
    (leftSample rightSample : Index -> Finset Unit)
    (leftScore rightScore : Index -> Unit -> Cell)
    (leftNormalizer rightNormalizer : Index -> Real)
    (cell : Cell)
    (hindicator :
      Tendsto
        (fun index =>
          weightedSampleSum (leftSample index)
              (fun _unit => leftNormalizer index)
              (scoreCellIndicator (leftScore index) cell) -
            weightedSampleSum (rightSample index)
              (fun _unit => rightNormalizer index)
              (scoreCellIndicator (rightScore index) cell))
        l (nhds 0))
    (hscaledIndicator :
      Tendsto
        (fun index =>
          scale index *
            (weightedSampleSum (leftSample index)
                (fun _unit => leftNormalizer index)
                (scoreCellIndicator (leftScore index) cell) -
              weightedSampleSum (rightSample index)
                (fun _unit => rightNormalizer index)
                (scoreCellIndicator (rightScore index) cell)))
        l (nhds 0)) :
    Tendsto
        (fun index =>
          leftNormalizer index *
              ((((leftSample index).filter
                (fun unit => leftScore index unit = cell)).card : Real)) -
            rightNormalizer index *
              ((((rightSample index).filter
                (fun unit => rightScore index unit = cell)).card : Real)))
        l (nhds 0) ∧
      Tendsto
        (fun index =>
          scale index *
            (leftNormalizer index *
                ((((leftSample index).filter
                  (fun unit => leftScore index unit = cell)).card : Real)) -
              rightNormalizer index *
                ((((rightSample index).filter
                  (fun unit => rightScore index unit = cell)).card : Real))))
        l (nhds 0) := by
  constructor
  · exact
      tendsto_normalized_cell_count_difference_of_tendsto_weightedSampleSum_indicator_difference_constant_weight
        leftSample rightSample leftScore rightScore leftNormalizer
        rightNormalizer cell 0 hindicator
  · exact
      tendsto_scaled_normalized_cell_count_difference_of_tendsto_scaled_weightedSampleSum_indicator_difference_constant_weight
        scale leftSample rightSample leftScore rightScore leftNormalizer
        rightNormalizer cell 0 hscaledIndicator

/--
Convergence of scaled constant-normalizer weighted total-indicator differences
gives convergence of the corresponding scaled normalized total-count
differences.
-/
theorem tendsto_scaled_normalized_total_count_difference_of_tendsto_scaled_weightedSampleSum_one_difference_constant_weight
    (scale : Index -> Real)
    (leftSample rightSample : Index -> Finset Unit)
    (leftNormalizer rightNormalizer : Index -> Real)
    (differenceLimit : Real)
    (hone :
      Tendsto
        (fun index =>
          scale index *
            (weightedSampleSum (leftSample index)
                (fun _unit => leftNormalizer index)
                (fun _unit => (1 : Real)) -
              weightedSampleSum (rightSample index)
                (fun _unit => rightNormalizer index)
                (fun _unit => (1 : Real))))
        l (nhds differenceLimit)) :
    Tendsto
      (fun index =>
        scale index *
          (leftNormalizer index * ((leftSample index).card : Real) -
            rightNormalizer index * ((rightSample index).card : Real)))
      l (nhds differenceLimit) := by
  convert hone using 1
  ext index
  exact
    scaled_normalized_total_count_difference_eq_scaled_weightedSampleSum_one_difference_constant_weight
      (scale index) (leftSample index) (rightSample index)
      (leftNormalizer index) (rightNormalizer index)

/--
Ordinary and scaled normalized total-count difference convergence from
ordinary and scaled weighted constant-one difference convergence.
-/
theorem tendsto_normalized_total_count_difference_zero_and_scaled_zero_of_tendsto_weightedSampleSum_one_difference_constant_weight
    (scale : Index -> Real)
    (leftSample rightSample : Index -> Finset Unit)
    (leftNormalizer rightNormalizer : Index -> Real)
    (hone :
      Tendsto
        (fun index =>
          weightedSampleSum (leftSample index)
              (fun _unit => leftNormalizer index)
              (fun _unit => (1 : Real)) -
            weightedSampleSum (rightSample index)
              (fun _unit => rightNormalizer index)
              (fun _unit => (1 : Real)))
        l (nhds 0))
    (hscaledOne :
      Tendsto
        (fun index =>
          scale index *
            (weightedSampleSum (leftSample index)
                (fun _unit => leftNormalizer index)
                (fun _unit => (1 : Real)) -
              weightedSampleSum (rightSample index)
                (fun _unit => rightNormalizer index)
                (fun _unit => (1 : Real))))
        l (nhds 0)) :
    Tendsto
        (fun index =>
          leftNormalizer index * ((leftSample index).card : Real) -
            rightNormalizer index * ((rightSample index).card : Real))
        l (nhds 0) ∧
      Tendsto
        (fun index =>
          scale index *
            (leftNormalizer index * ((leftSample index).card : Real) -
              rightNormalizer index * ((rightSample index).card : Real)))
        l (nhds 0) := by
  constructor
  · exact
      tendsto_normalized_total_count_difference_of_tendsto_weightedSampleSum_one_difference_constant_weight
        leftSample rightSample leftNormalizer rightNormalizer 0 hone
  · exact
      tendsto_scaled_normalized_total_count_difference_of_tendsto_scaled_weightedSampleSum_one_difference_constant_weight
        scale leftSample rightSample leftNormalizer rightNormalizer 0
        hscaledOne

/--
Paired PATE/PATT normalized total-count difference transfer.  Total counts do
not depend on the score cells, but downstream PATE and PATT bridges often carry
separate sample/normalizer pairs.
-/
theorem tendsto_pate_patt_normalized_total_count_differences_zero_and_scaled_zero_of_tendsto_weightedSampleSum_one_differences_constant_weight
    (scale : Index -> Real)
    (pateLeftSample pateRightSample pattLeftSample pattRightSample :
      Index -> Finset Unit)
    (pateLeftNormalizer pateRightNormalizer pattLeftNormalizer
      pattRightNormalizer : Index -> Real)
    (hpateOne :
      Tendsto
        (fun index =>
          weightedSampleSum (pateLeftSample index)
              (fun _unit => pateLeftNormalizer index)
              (fun _unit => (1 : Real)) -
            weightedSampleSum (pateRightSample index)
              (fun _unit => pateRightNormalizer index)
              (fun _unit => (1 : Real)))
        l (nhds 0))
    (hpateScaledOne :
      Tendsto
        (fun index =>
          scale index *
            (weightedSampleSum (pateLeftSample index)
                (fun _unit => pateLeftNormalizer index)
                (fun _unit => (1 : Real)) -
              weightedSampleSum (pateRightSample index)
                (fun _unit => pateRightNormalizer index)
                (fun _unit => (1 : Real))))
        l (nhds 0))
    (hpattOne :
      Tendsto
        (fun index =>
          weightedSampleSum (pattLeftSample index)
              (fun _unit => pattLeftNormalizer index)
              (fun _unit => (1 : Real)) -
            weightedSampleSum (pattRightSample index)
              (fun _unit => pattRightNormalizer index)
              (fun _unit => (1 : Real)))
        l (nhds 0))
    (hpattScaledOne :
      Tendsto
        (fun index =>
          scale index *
            (weightedSampleSum (pattLeftSample index)
                (fun _unit => pattLeftNormalizer index)
                (fun _unit => (1 : Real)) -
              weightedSampleSum (pattRightSample index)
                (fun _unit => pattRightNormalizer index)
                (fun _unit => (1 : Real))))
        l (nhds 0)) :
    (Tendsto
        (fun index =>
          pateLeftNormalizer index * ((pateLeftSample index).card : Real) -
            pateRightNormalizer index *
              ((pateRightSample index).card : Real))
        l (nhds 0) ∧
      Tendsto
        (fun index =>
          scale index *
            (pateLeftNormalizer index *
                ((pateLeftSample index).card : Real) -
              pateRightNormalizer index *
                ((pateRightSample index).card : Real)))
        l (nhds 0)) ∧
      (Tendsto
        (fun index =>
          pattLeftNormalizer index * ((pattLeftSample index).card : Real) -
            pattRightNormalizer index *
              ((pattRightSample index).card : Real))
        l (nhds 0) ∧
      Tendsto
        (fun index =>
          scale index *
            (pattLeftNormalizer index *
                ((pattLeftSample index).card : Real) -
              pattRightNormalizer index *
                ((pattRightSample index).card : Real)))
        l (nhds 0)) := by
  constructor
  · exact
      tendsto_normalized_total_count_difference_zero_and_scaled_zero_of_tendsto_weightedSampleSum_one_difference_constant_weight
        scale pateLeftSample pateRightSample pateLeftNormalizer
        pateRightNormalizer hpateOne hpateScaledOne
  · exact
      tendsto_normalized_total_count_difference_zero_and_scaled_zero_of_tendsto_weightedSampleSum_one_difference_constant_weight
        scale pattLeftSample pattRightSample pattLeftNormalizer
        pattRightNormalizer hpattOne hpattScaledOne

/--
PATE double-score specialization of the scaled indicator-sum difference to
scaled normalized cell-count difference bridge.
-/
theorem tendsto_scaled_pate_normalized_cell_count_difference_of_tendsto_indicator_difference_constant_weight
    (scale : Index -> Real)
    (leftSample rightSample : Index -> Finset Unit)
    (propensityScore : Index -> Unit -> PropensityCell)
    (treatedPrognosticScore : Index -> Unit -> TreatedProgCell)
    (controlPrognosticScore : Index -> Unit -> ControlProgCell)
    (leftNormalizer rightNormalizer : Index -> Real)
    (cell : (PropensityCell × TreatedProgCell) × ControlProgCell)
    (differenceLimit : Real)
    (hindicator :
      Tendsto
        (fun index =>
          scale index *
            (weightedSampleSum (leftSample index)
                (fun _unit => leftNormalizer index)
                (scoreCellIndicator
                  (pateDoubleScore (propensityScore index)
                    (treatedPrognosticScore index)
                    (controlPrognosticScore index)) cell) -
              weightedSampleSum (rightSample index)
                (fun _unit => rightNormalizer index)
                (scoreCellIndicator
                  (pateDoubleScore (propensityScore index)
                    (treatedPrognosticScore index)
                    (controlPrognosticScore index)) cell)))
        l (nhds differenceLimit)) :
    Tendsto
      (fun index =>
        scale index *
          (leftNormalizer index *
              ((((leftSample index).filter
                (fun unit =>
                  pateDoubleScore (propensityScore index)
                    (treatedPrognosticScore index)
                    (controlPrognosticScore index) unit = cell)).card :
                Real)) -
            rightNormalizer index *
              ((((rightSample index).filter
                (fun unit =>
                  pateDoubleScore (propensityScore index)
                    (treatedPrognosticScore index)
                    (controlPrognosticScore index) unit = cell)).card :
                Real))))
      l (nhds differenceLimit) :=
  tendsto_scaled_normalized_cell_count_difference_of_tendsto_scaled_weightedSampleSum_indicator_difference_constant_weight
    scale leftSample rightSample
    (fun index =>
      pateDoubleScore (propensityScore index)
        (treatedPrognosticScore index)
        (controlPrognosticScore index))
    (fun index =>
      pateDoubleScore (propensityScore index)
        (treatedPrognosticScore index)
        (controlPrognosticScore index))
    leftNormalizer rightNormalizer cell differenceLimit hindicator

/--
PATT double-score specialization of the scaled indicator-sum difference to
scaled normalized cell-count difference bridge.
-/
theorem tendsto_scaled_patt_normalized_cell_count_difference_of_tendsto_indicator_difference_constant_weight
    (scale : Index -> Real)
    (leftSample rightSample : Index -> Finset Unit)
    (propensityScore : Index -> Unit -> PropensityCell)
    (controlPrognosticScore : Index -> Unit -> PATTProgCell)
    (leftNormalizer rightNormalizer : Index -> Real)
    (cell : PropensityCell × PATTProgCell)
    (differenceLimit : Real)
    (hindicator :
      Tendsto
        (fun index =>
          scale index *
            (weightedSampleSum (leftSample index)
                (fun _unit => leftNormalizer index)
                (scoreCellIndicator
                  (pattDoubleScore (propensityScore index)
                    (controlPrognosticScore index)) cell) -
              weightedSampleSum (rightSample index)
                (fun _unit => rightNormalizer index)
                (scoreCellIndicator
                  (pattDoubleScore (propensityScore index)
                    (controlPrognosticScore index)) cell)))
        l (nhds differenceLimit)) :
    Tendsto
      (fun index =>
        scale index *
          (leftNormalizer index *
              ((((leftSample index).filter
                (fun unit =>
                  pattDoubleScore (propensityScore index)
                    (controlPrognosticScore index) unit = cell)).card :
                Real)) -
            rightNormalizer index *
              ((((rightSample index).filter
                (fun unit =>
                  pattDoubleScore (propensityScore index)
                    (controlPrognosticScore index) unit = cell)).card :
                Real))))
      l (nhds differenceLimit) :=
  tendsto_scaled_normalized_cell_count_difference_of_tendsto_scaled_weightedSampleSum_indicator_difference_constant_weight
    scale leftSample rightSample
    (fun index =>
      pattDoubleScore (propensityScore index) (controlPrognosticScore index))
    (fun index =>
      pattDoubleScore (propensityScore index) (controlPrognosticScore index))
    leftNormalizer rightNormalizer cell differenceLimit hindicator

/--
Finite PATE partition wrapper: cellwise scaled indicator-sum differences imply
the corresponding cellwise scaled normalized count differences.
-/
theorem tendsto_all_scaled_pate_normalized_cell_count_differences_of_tendsto_indicator_differences_constant_weight
    (scale : Index -> Real)
    (leftSample rightSample : Index -> Finset Unit)
    (propensityScore : Index -> Unit -> PropensityCell)
    (treatedPrognosticScore : Index -> Unit -> TreatedProgCell)
    (controlPrognosticScore : Index -> Unit -> ControlProgCell)
    (cells :
      Finset ((PropensityCell × TreatedProgCell) × ControlProgCell))
    (leftNormalizer rightNormalizer : Index -> Real)
    (differenceLimit :
      (PropensityCell × TreatedProgCell) × ControlProgCell -> Real)
    (hindicator :
      ∀ cell, cell ∈ cells ->
        Tendsto
          (fun index =>
            scale index *
              (weightedSampleSum (leftSample index)
                  (fun _unit => leftNormalizer index)
                  (scoreCellIndicator
                    (pateDoubleScore (propensityScore index)
                      (treatedPrognosticScore index)
                      (controlPrognosticScore index)) cell) -
                weightedSampleSum (rightSample index)
                  (fun _unit => rightNormalizer index)
                  (scoreCellIndicator
                    (pateDoubleScore (propensityScore index)
                      (treatedPrognosticScore index)
                      (controlPrognosticScore index)) cell)))
          l (nhds (differenceLimit cell))) :
    ∀ cell, cell ∈ cells ->
      Tendsto
        (fun index =>
          scale index *
            (leftNormalizer index *
                ((((leftSample index).filter
                  (fun unit =>
                    pateDoubleScore (propensityScore index)
                      (treatedPrognosticScore index)
                      (controlPrognosticScore index) unit = cell)).card :
                  Real)) -
              rightNormalizer index *
                ((((rightSample index).filter
                  (fun unit =>
                    pateDoubleScore (propensityScore index)
                      (treatedPrognosticScore index)
                      (controlPrognosticScore index) unit = cell)).card :
                  Real))))
        l (nhds (differenceLimit cell)) := by
  intro cell hmem
  exact
    tendsto_scaled_pate_normalized_cell_count_difference_of_tendsto_indicator_difference_constant_weight
      scale leftSample rightSample propensityScore treatedPrognosticScore
      controlPrognosticScore leftNormalizer rightNormalizer cell
      (differenceLimit cell) (hindicator cell hmem)

/--
Finite PATT partition wrapper: cellwise scaled indicator-sum differences imply
the corresponding cellwise scaled normalized count differences.
-/
theorem tendsto_all_scaled_patt_normalized_cell_count_differences_of_tendsto_indicator_differences_constant_weight
    (scale : Index -> Real)
    (leftSample rightSample : Index -> Finset Unit)
    (propensityScore : Index -> Unit -> PropensityCell)
    (controlPrognosticScore : Index -> Unit -> PATTProgCell)
    (cells : Finset (PropensityCell × PATTProgCell))
    (leftNormalizer rightNormalizer : Index -> Real)
    (differenceLimit : PropensityCell × PATTProgCell -> Real)
    (hindicator :
      ∀ cell, cell ∈ cells ->
        Tendsto
          (fun index =>
            scale index *
              (weightedSampleSum (leftSample index)
                  (fun _unit => leftNormalizer index)
                  (scoreCellIndicator
                    (pattDoubleScore (propensityScore index)
                      (controlPrognosticScore index)) cell) -
                weightedSampleSum (rightSample index)
                  (fun _unit => rightNormalizer index)
                  (scoreCellIndicator
                    (pattDoubleScore (propensityScore index)
                      (controlPrognosticScore index)) cell)))
          l (nhds (differenceLimit cell))) :
    ∀ cell, cell ∈ cells ->
      Tendsto
        (fun index =>
          scale index *
            (leftNormalizer index *
                ((((leftSample index).filter
                  (fun unit =>
                    pattDoubleScore (propensityScore index)
                      (controlPrognosticScore index) unit = cell)).card :
                  Real)) -
              rightNormalizer index *
                ((((rightSample index).filter
                  (fun unit =>
                    pattDoubleScore (propensityScore index)
                      (controlPrognosticScore index) unit = cell)).card :
                  Real))))
        l (nhds (differenceLimit cell)) := by
  intro cell hmem
  exact
    tendsto_scaled_patt_normalized_cell_count_difference_of_tendsto_indicator_difference_constant_weight
      scale leftSample rightSample propensityScore controlPrognosticScore
      leftNormalizer rightNormalizer cell (differenceLimit cell)
      (hindicator cell hmem)

/--
Finite PATE partition wrapper: ordinary and scaled cellwise indicator-sum
differences imply ordinary and scaled normalized count differences.
-/
theorem tendsto_all_pate_normalized_cell_count_differences_zero_and_scaled_zero_of_tendsto_indicator_differences_constant_weight
    (scale : Index -> Real)
    (leftSample rightSample : Index -> Finset Unit)
    (propensityScore : Index -> Unit -> PropensityCell)
    (treatedPrognosticScore : Index -> Unit -> TreatedProgCell)
    (controlPrognosticScore : Index -> Unit -> ControlProgCell)
    (cells :
      Finset ((PropensityCell × TreatedProgCell) × ControlProgCell))
    (leftNormalizer rightNormalizer : Index -> Real)
    (hindicator :
      ∀ cell, cell ∈ cells ->
        Tendsto
          (fun index =>
            weightedSampleSum (leftSample index)
                (fun _unit => leftNormalizer index)
                (scoreCellIndicator
                  (pateDoubleScore (propensityScore index)
                    (treatedPrognosticScore index)
                    (controlPrognosticScore index)) cell) -
              weightedSampleSum (rightSample index)
                (fun _unit => rightNormalizer index)
                (scoreCellIndicator
                  (pateDoubleScore (propensityScore index)
                    (treatedPrognosticScore index)
                    (controlPrognosticScore index)) cell))
          l (nhds 0))
    (hscaledIndicator :
      ∀ cell, cell ∈ cells ->
        Tendsto
          (fun index =>
            scale index *
              (weightedSampleSum (leftSample index)
                  (fun _unit => leftNormalizer index)
                  (scoreCellIndicator
                    (pateDoubleScore (propensityScore index)
                      (treatedPrognosticScore index)
                      (controlPrognosticScore index)) cell) -
                weightedSampleSum (rightSample index)
                  (fun _unit => rightNormalizer index)
                  (scoreCellIndicator
                    (pateDoubleScore (propensityScore index)
                      (treatedPrognosticScore index)
                      (controlPrognosticScore index)) cell)))
          l (nhds 0)) :
    (∀ cell, cell ∈ cells ->
      Tendsto
        (fun index =>
          leftNormalizer index *
              ((((leftSample index).filter
                (fun unit =>
                  pateDoubleScore (propensityScore index)
                    (treatedPrognosticScore index)
                    (controlPrognosticScore index) unit = cell)).card :
                Real)) -
            rightNormalizer index *
              ((((rightSample index).filter
                (fun unit =>
                  pateDoubleScore (propensityScore index)
                    (treatedPrognosticScore index)
                    (controlPrognosticScore index) unit = cell)).card :
                Real)))
        l (nhds 0)) ∧
      (∀ cell, cell ∈ cells ->
        Tendsto
          (fun index =>
            scale index *
              (leftNormalizer index *
                  ((((leftSample index).filter
                    (fun unit =>
                      pateDoubleScore (propensityScore index)
                        (treatedPrognosticScore index)
                        (controlPrognosticScore index) unit = cell)).card :
                    Real)) -
                rightNormalizer index *
                  ((((rightSample index).filter
                    (fun unit =>
                      pateDoubleScore (propensityScore index)
                        (treatedPrognosticScore index)
                        (controlPrognosticScore index) unit = cell)).card :
                    Real))))
          l (nhds 0)) := by
  constructor
  · exact
      tendsto_all_pate_normalized_cell_count_differences_of_tendsto_indicator_differences_constant_weight
        leftSample rightSample propensityScore treatedPrognosticScore
        controlPrognosticScore cells leftNormalizer rightNormalizer
        (fun _cell => (0 : Real)) hindicator
  · exact
      tendsto_all_scaled_pate_normalized_cell_count_differences_of_tendsto_indicator_differences_constant_weight
        scale leftSample rightSample propensityScore treatedPrognosticScore
        controlPrognosticScore cells leftNormalizer rightNormalizer
        (fun _cell => (0 : Real)) hscaledIndicator

/--
Finite PATT partition wrapper: ordinary and scaled cellwise indicator-sum
differences imply ordinary and scaled normalized count differences.
-/
theorem tendsto_all_patt_normalized_cell_count_differences_zero_and_scaled_zero_of_tendsto_indicator_differences_constant_weight
    (scale : Index -> Real)
    (leftSample rightSample : Index -> Finset Unit)
    (propensityScore : Index -> Unit -> PropensityCell)
    (controlPrognosticScore : Index -> Unit -> PATTProgCell)
    (cells : Finset (PropensityCell × PATTProgCell))
    (leftNormalizer rightNormalizer : Index -> Real)
    (hindicator :
      ∀ cell, cell ∈ cells ->
        Tendsto
          (fun index =>
            weightedSampleSum (leftSample index)
                (fun _unit => leftNormalizer index)
                (scoreCellIndicator
                  (pattDoubleScore (propensityScore index)
                    (controlPrognosticScore index)) cell) -
              weightedSampleSum (rightSample index)
                (fun _unit => rightNormalizer index)
                (scoreCellIndicator
                  (pattDoubleScore (propensityScore index)
                    (controlPrognosticScore index)) cell))
          l (nhds 0))
    (hscaledIndicator :
      ∀ cell, cell ∈ cells ->
        Tendsto
          (fun index =>
            scale index *
              (weightedSampleSum (leftSample index)
                  (fun _unit => leftNormalizer index)
                  (scoreCellIndicator
                    (pattDoubleScore (propensityScore index)
                      (controlPrognosticScore index)) cell) -
                weightedSampleSum (rightSample index)
                  (fun _unit => rightNormalizer index)
                  (scoreCellIndicator
                    (pattDoubleScore (propensityScore index)
                      (controlPrognosticScore index)) cell)))
          l (nhds 0)) :
    (∀ cell, cell ∈ cells ->
      Tendsto
        (fun index =>
          leftNormalizer index *
              ((((leftSample index).filter
                (fun unit =>
                  pattDoubleScore (propensityScore index)
                    (controlPrognosticScore index) unit = cell)).card :
                Real)) -
            rightNormalizer index *
              ((((rightSample index).filter
                (fun unit =>
                  pattDoubleScore (propensityScore index)
                    (controlPrognosticScore index) unit = cell)).card :
                Real)))
        l (nhds 0)) ∧
      (∀ cell, cell ∈ cells ->
        Tendsto
          (fun index =>
            scale index *
              (leftNormalizer index *
                  ((((leftSample index).filter
                    (fun unit =>
                      pattDoubleScore (propensityScore index)
                        (controlPrognosticScore index) unit = cell)).card :
                    Real)) -
                rightNormalizer index *
                  ((((rightSample index).filter
                    (fun unit =>
                      pattDoubleScore (propensityScore index)
                        (controlPrognosticScore index) unit = cell)).card :
                    Real))))
          l (nhds 0)) := by
  constructor
  · exact
      tendsto_all_patt_normalized_cell_count_differences_of_tendsto_indicator_differences_constant_weight
        leftSample rightSample propensityScore controlPrognosticScore cells
        leftNormalizer rightNormalizer (fun _cell => (0 : Real)) hindicator
  · exact
      tendsto_all_scaled_patt_normalized_cell_count_differences_of_tendsto_indicator_differences_constant_weight
        scale leftSample rightSample propensityScore controlPrognosticScore
        cells leftNormalizer rightNormalizer (fun _cell => (0 : Real))
        hscaledIndicator

/--
Paired finite PATE/PATT partition wrapper: ordinary and scaled cellwise
indicator-sum differences imply ordinary and scaled normalized count differences
for both double-score partitions.
-/
theorem tendsto_all_pate_patt_normalized_cell_count_differences_zero_and_scaled_zero_of_tendsto_indicator_differences_constant_weight
    (scale : Index -> Real)
    (leftSample rightSample : Index -> Finset Unit)
    (propensityScore : Index -> Unit -> PropensityCell)
    (treatedPrognosticScore : Index -> Unit -> TreatedProgCell)
    (controlPrognosticScore : Index -> Unit -> ControlProgCell)
    (pattPrognosticScore : Index -> Unit -> PATTProgCell)
    (pateCells :
      Finset ((PropensityCell × TreatedProgCell) × ControlProgCell))
    (pattCells : Finset (PropensityCell × PATTProgCell))
    (leftNormalizer rightNormalizer : Index -> Real)
    (hpateIndicator :
      ∀ cell, cell ∈ pateCells ->
        Tendsto
          (fun index =>
            weightedSampleSum (leftSample index)
                (fun _unit => leftNormalizer index)
                (scoreCellIndicator
                  (pateDoubleScore (propensityScore index)
                    (treatedPrognosticScore index)
                    (controlPrognosticScore index)) cell) -
              weightedSampleSum (rightSample index)
                (fun _unit => rightNormalizer index)
                (scoreCellIndicator
                  (pateDoubleScore (propensityScore index)
                    (treatedPrognosticScore index)
                    (controlPrognosticScore index)) cell))
          l (nhds 0))
    (hpattIndicator :
      ∀ cell, cell ∈ pattCells ->
        Tendsto
          (fun index =>
            weightedSampleSum (leftSample index)
                (fun _unit => leftNormalizer index)
                (scoreCellIndicator
                  (pattDoubleScore (propensityScore index)
                    (pattPrognosticScore index)) cell) -
              weightedSampleSum (rightSample index)
                (fun _unit => rightNormalizer index)
                (scoreCellIndicator
                  (pattDoubleScore (propensityScore index)
                    (pattPrognosticScore index)) cell))
          l (nhds 0))
    (hpateScaledIndicator :
      ∀ cell, cell ∈ pateCells ->
        Tendsto
          (fun index =>
            scale index *
              (weightedSampleSum (leftSample index)
                  (fun _unit => leftNormalizer index)
                  (scoreCellIndicator
                    (pateDoubleScore (propensityScore index)
                      (treatedPrognosticScore index)
                      (controlPrognosticScore index)) cell) -
                weightedSampleSum (rightSample index)
                  (fun _unit => rightNormalizer index)
                  (scoreCellIndicator
                    (pateDoubleScore (propensityScore index)
                      (treatedPrognosticScore index)
                      (controlPrognosticScore index)) cell)))
          l (nhds 0))
    (hpattScaledIndicator :
      ∀ cell, cell ∈ pattCells ->
        Tendsto
          (fun index =>
            scale index *
              (weightedSampleSum (leftSample index)
                  (fun _unit => leftNormalizer index)
                  (scoreCellIndicator
                    (pattDoubleScore (propensityScore index)
                      (pattPrognosticScore index)) cell) -
                weightedSampleSum (rightSample index)
                  (fun _unit => rightNormalizer index)
                  (scoreCellIndicator
                    (pattDoubleScore (propensityScore index)
                      (pattPrognosticScore index)) cell)))
          l (nhds 0)) :
    ((∀ cell, cell ∈ pateCells ->
      Tendsto
        (fun index =>
          leftNormalizer index *
              ((((leftSample index).filter
                (fun unit =>
                  pateDoubleScore (propensityScore index)
                    (treatedPrognosticScore index)
                    (controlPrognosticScore index) unit = cell)).card :
                Real)) -
            rightNormalizer index *
              ((((rightSample index).filter
                (fun unit =>
                  pateDoubleScore (propensityScore index)
                    (treatedPrognosticScore index)
                    (controlPrognosticScore index) unit = cell)).card :
                Real)))
        l (nhds 0)) ∧
      (∀ cell, cell ∈ pateCells ->
        Tendsto
          (fun index =>
            scale index *
              (leftNormalizer index *
                  ((((leftSample index).filter
                    (fun unit =>
                      pateDoubleScore (propensityScore index)
                        (treatedPrognosticScore index)
                        (controlPrognosticScore index) unit = cell)).card :
                    Real)) -
                rightNormalizer index *
                  ((((rightSample index).filter
                    (fun unit =>
                      pateDoubleScore (propensityScore index)
                        (treatedPrognosticScore index)
                        (controlPrognosticScore index) unit = cell)).card :
                    Real))))
          l (nhds 0))) ∧
      ((∀ cell, cell ∈ pattCells ->
        Tendsto
          (fun index =>
            leftNormalizer index *
                ((((leftSample index).filter
                  (fun unit =>
                    pattDoubleScore (propensityScore index)
                      (pattPrognosticScore index) unit = cell)).card :
                  Real)) -
              rightNormalizer index *
                ((((rightSample index).filter
                  (fun unit =>
                    pattDoubleScore (propensityScore index)
                      (pattPrognosticScore index) unit = cell)).card :
                  Real)))
          l (nhds 0)) ∧
        (∀ cell, cell ∈ pattCells ->
          Tendsto
            (fun index =>
              scale index *
                (leftNormalizer index *
                    ((((leftSample index).filter
                      (fun unit =>
                        pattDoubleScore (propensityScore index)
                          (pattPrognosticScore index) unit = cell)).card :
                      Real)) -
                  rightNormalizer index *
                    ((((rightSample index).filter
                      (fun unit =>
                        pattDoubleScore (propensityScore index)
                          (pattPrognosticScore index) unit = cell)).card :
                      Real))))
            l (nhds 0))) := by
  constructor
  · exact
      tendsto_all_pate_normalized_cell_count_differences_zero_and_scaled_zero_of_tendsto_indicator_differences_constant_weight
        scale leftSample rightSample propensityScore treatedPrognosticScore
        controlPrognosticScore pateCells leftNormalizer rightNormalizer
        hpateIndicator hpateScaledIndicator
  · exact
      tendsto_all_patt_normalized_cell_count_differences_zero_and_scaled_zero_of_tendsto_indicator_differences_constant_weight
        scale leftSample rightSample propensityScore pattPrognosticScore
        pattCells leftNormalizer rightNormalizer hpattIndicator
        hpattScaledIndicator

end WDSM
end Matching
end StatInference
