import StatInference.Matching.WDSM.ProspectiveScoreCellShare
import StatInference.Matching.WDSM.FiniteCellShareConvergence

/-!
# Prospective/common-weight score-cell share convergence for WDSM

This module connects ordinary finite cell-count ratio convergence to the WDSM
score-cell share convergence API when each sample uses a common survey weight.
It is the deterministic bridge from prospective unweighted cell proportions to
the existing finite-cell L1 double-score share convergence layer.
-/

namespace StatInference
namespace Matching
namespace WDSM

open Filter
open scoped BigOperators

variable {Index UnitA UnitB Cell : Type*} {l : Filter Index}
  [DecidableEq Cell]

theorem tendsto_l1ScoreCellShareDistance_zero_of_card_ratio_cellwise_constant_weight
    (cells : Finset Cell)
    (sampleA : Index -> Finset UnitA) (sampleB : Index -> Finset UnitB)
    (commonWeightA commonWeightB : Index -> Real)
    (scoreA : Index -> UnitA -> Cell)
    (scoreB : Index -> UnitB -> Cell)
    (hweightA : ∀ index, commonWeightA index ≠ 0)
    (hweightB : ∀ index, commonWeightB index ≠ 0)
    (hnonemptyA : ∀ index, (sampleA index).Nonempty)
    (hnonemptyB : ∀ index, (sampleB index).Nonempty)
    (hcell :
      ∀ cell, cell ∈ cells ->
        Tendsto
          (fun index =>
            (((sampleA index).filter
                  (fun unit => scoreA index unit = cell)).card : Real) /
                ((sampleA index).card : Real) -
              (((sampleB index).filter
                  (fun unit => scoreB index unit = cell)).card : Real) /
                ((sampleB index).card : Real))
          l (nhds 0)) :
    Tendsto
      (fun index =>
        l1ScoreCellShareDistance cells (sampleA index) (sampleB index)
          (fun _unit => commonWeightA index) (fun _unit => commonWeightB index)
          (scoreA index) (scoreB index))
      l (nhds 0) := by
  refine tendsto_l1ScoreCellShareDistance_zero_of_cellwise cells sampleA sampleB
    (fun index _unit => commonWeightA index)
    (fun index _unit => commonWeightB index)
    scoreA scoreB ?_
  intro cell hmem
  convert hcell cell hmem using 1
  ext index
  rw [scoreCellShare_constant_weight_eq_card_ratio_of_nonempty
    (sampleA index) (scoreA index) cell (commonWeightA index)
    (hweightA index) (hnonemptyA index)]
  rw [scoreCellShare_constant_weight_eq_card_ratio_of_nonempty
    (sampleB index) (scoreB index) cell (commonWeightB index)
    (hweightB index) (hnonemptyB index)]

theorem tendsto_scaled_l1ScoreCellShareDistance_zero_of_card_ratio_cellwise_constant_weight
    (cells : Finset Cell) (scale : Index -> Real)
    (sampleA : Index -> Finset UnitA) (sampleB : Index -> Finset UnitB)
    (commonWeightA commonWeightB : Index -> Real)
    (scoreA : Index -> UnitA -> Cell)
    (scoreB : Index -> UnitB -> Cell)
    (hscale_nonneg : ∀ index, 0 ≤ scale index)
    (hweightA : ∀ index, commonWeightA index ≠ 0)
    (hweightB : ∀ index, commonWeightB index ≠ 0)
    (hnonemptyA : ∀ index, (sampleA index).Nonempty)
    (hnonemptyB : ∀ index, (sampleB index).Nonempty)
    (hcell :
      ∀ cell, cell ∈ cells ->
        Tendsto
          (fun index =>
            scale index *
              ((((sampleA index).filter
                    (fun unit => scoreA index unit = cell)).card : Real) /
                  ((sampleA index).card : Real) -
                (((sampleB index).filter
                    (fun unit => scoreB index unit = cell)).card : Real) /
                  ((sampleB index).card : Real)))
          l (nhds 0)) :
    Tendsto
      (fun index =>
        scale index *
          l1ScoreCellShareDistance cells (sampleA index) (sampleB index)
            (fun _unit => commonWeightA index)
            (fun _unit => commonWeightB index)
            (scoreA index) (scoreB index))
      l (nhds 0) := by
  refine tendsto_scaled_l1ScoreCellShareDistance_zero_of_cellwise cells scale
    sampleA sampleB
    (fun index _unit => commonWeightA index)
    (fun index _unit => commonWeightB index)
    scoreA scoreB hscale_nonneg ?_
  intro cell hmem
  convert hcell cell hmem using 1
  ext index
  rw [scoreCellShare_constant_weight_eq_card_ratio_of_nonempty
    (sampleA index) (scoreA index) cell (commonWeightA index)
    (hweightA index) (hnonemptyA index)]
  rw [scoreCellShare_constant_weight_eq_card_ratio_of_nonempty
    (sampleB index) (scoreB index) cell (commonWeightB index)
    (hweightB index) (hnonemptyB index)]

/--
Ordinary and scaled L1 score-cell share convergence from pointwise ordinary and
scaled card-ratio convergence under common weights.
-/
theorem tendsto_l1ScoreCellShareDistance_zero_and_scaled_zero_of_card_ratio_cellwise_constant_weight
    (cells : Finset Cell) (scale : Index -> Real)
    (sampleA : Index -> Finset UnitA) (sampleB : Index -> Finset UnitB)
    (commonWeightA commonWeightB : Index -> Real)
    (scoreA : Index -> UnitA -> Cell)
    (scoreB : Index -> UnitB -> Cell)
    (hscale_nonneg : ∀ index, 0 ≤ scale index)
    (hweightA : ∀ index, commonWeightA index ≠ 0)
    (hweightB : ∀ index, commonWeightB index ≠ 0)
    (hnonemptyA : ∀ index, (sampleA index).Nonempty)
    (hnonemptyB : ∀ index, (sampleB index).Nonempty)
    (hcell :
      ∀ cell, cell ∈ cells ->
        Tendsto
          (fun index =>
            (((sampleA index).filter
                  (fun unit => scoreA index unit = cell)).card : Real) /
                ((sampleA index).card : Real) -
              (((sampleB index).filter
                  (fun unit => scoreB index unit = cell)).card : Real) /
                ((sampleB index).card : Real))
          l (nhds 0))
    (hscaledCell :
      ∀ cell, cell ∈ cells ->
        Tendsto
          (fun index =>
            scale index *
              ((((sampleA index).filter
                    (fun unit => scoreA index unit = cell)).card : Real) /
                  ((sampleA index).card : Real) -
                (((sampleB index).filter
                    (fun unit => scoreB index unit = cell)).card : Real) /
                  ((sampleB index).card : Real)))
          l (nhds 0)) :
    Tendsto
        (fun index =>
          l1ScoreCellShareDistance cells (sampleA index) (sampleB index)
            (fun _unit => commonWeightA index)
            (fun _unit => commonWeightB index)
            (scoreA index) (scoreB index))
        l (nhds 0) ∧
      Tendsto
        (fun index =>
          scale index *
            l1ScoreCellShareDistance cells (sampleA index) (sampleB index)
              (fun _unit => commonWeightA index)
              (fun _unit => commonWeightB index)
              (scoreA index) (scoreB index))
        l (nhds 0) := by
  constructor
  · exact
      tendsto_l1ScoreCellShareDistance_zero_of_card_ratio_cellwise_constant_weight
        cells sampleA sampleB commonWeightA commonWeightB scoreA scoreB
        hweightA hweightB hnonemptyA hnonemptyB hcell
  · exact
      tendsto_scaled_l1ScoreCellShareDistance_zero_of_card_ratio_cellwise_constant_weight
        cells scale sampleA sampleB commonWeightA commonWeightB scoreA scoreB
        hscale_nonneg hweightA hweightB hnonemptyA hnonemptyB hscaledCell

variable {PropensityCell TreatedProgCell ControlProgCell PATTProgCell : Type*}
  [DecidableEq PropensityCell] [DecidableEq TreatedProgCell]
  [DecidableEq ControlProgCell] [DecidableEq PATTProgCell]

theorem tendsto_l1PATEDoubleScoreShareDistance_zero_of_card_ratio_cellwise_constant_weight
    (cells :
      Finset ((PropensityCell × TreatedProgCell) × ControlProgCell))
    (sampleA sampleB : Index -> Finset UnitA)
    (commonWeightA commonWeightB : Index -> Real)
    (propensityScore : Index -> UnitA -> PropensityCell)
    (treatedPrognosticScore : Index -> UnitA -> TreatedProgCell)
    (controlPrognosticScore : Index -> UnitA -> ControlProgCell)
    (hweightA : ∀ index, commonWeightA index ≠ 0)
    (hweightB : ∀ index, commonWeightB index ≠ 0)
    (hnonemptyA : ∀ index, (sampleA index).Nonempty)
    (hnonemptyB : ∀ index, (sampleB index).Nonempty)
    (hcell :
      ∀ cell, cell ∈ cells ->
        Tendsto
          (fun index =>
            (((sampleA index).filter
                  (fun unit =>
                    pateDoubleScore (propensityScore index)
                      (treatedPrognosticScore index)
                      (controlPrognosticScore index) unit = cell)).card :
                Real) /
                ((sampleA index).card : Real) -
              (((sampleB index).filter
                  (fun unit =>
                    pateDoubleScore (propensityScore index)
                      (treatedPrognosticScore index)
                      (controlPrognosticScore index) unit = cell)).card :
                Real) /
                ((sampleB index).card : Real))
          l (nhds 0)) :
    Tendsto
      (fun index =>
        l1PATEDoubleScoreShareDistance cells (sampleA index) (sampleB index)
          (fun _unit => commonWeightA index) (fun _unit => commonWeightB index)
          (propensityScore index) (treatedPrognosticScore index)
          (controlPrognosticScore index))
      l (nhds 0) := by
  unfold l1PATEDoubleScoreShareDistance
  exact
    tendsto_l1ScoreCellShareDistance_zero_of_card_ratio_cellwise_constant_weight
      cells sampleA sampleB commonWeightA commonWeightB
      (fun index =>
        pateDoubleScore (propensityScore index)
          (treatedPrognosticScore index)
          (controlPrognosticScore index))
      (fun index =>
        pateDoubleScore (propensityScore index)
          (treatedPrognosticScore index)
          (controlPrognosticScore index))
      hweightA hweightB hnonemptyA hnonemptyB hcell

theorem tendsto_scaled_l1PATEDoubleScoreShareDistance_zero_of_card_ratio_cellwise_constant_weight
    (cells :
      Finset ((PropensityCell × TreatedProgCell) × ControlProgCell))
    (scale : Index -> Real)
    (sampleA sampleB : Index -> Finset UnitA)
    (commonWeightA commonWeightB : Index -> Real)
    (propensityScore : Index -> UnitA -> PropensityCell)
    (treatedPrognosticScore : Index -> UnitA -> TreatedProgCell)
    (controlPrognosticScore : Index -> UnitA -> ControlProgCell)
    (hscale_nonneg : ∀ index, 0 ≤ scale index)
    (hweightA : ∀ index, commonWeightA index ≠ 0)
    (hweightB : ∀ index, commonWeightB index ≠ 0)
    (hnonemptyA : ∀ index, (sampleA index).Nonempty)
    (hnonemptyB : ∀ index, (sampleB index).Nonempty)
    (hcell :
      ∀ cell, cell ∈ cells ->
        Tendsto
          (fun index =>
            scale index *
              ((((sampleA index).filter
                    (fun unit =>
                      pateDoubleScore (propensityScore index)
                        (treatedPrognosticScore index)
                        (controlPrognosticScore index) unit = cell)).card :
                  Real) /
                  ((sampleA index).card : Real) -
                (((sampleB index).filter
                    (fun unit =>
                      pateDoubleScore (propensityScore index)
                        (treatedPrognosticScore index)
                        (controlPrognosticScore index) unit = cell)).card :
                  Real) /
                  ((sampleB index).card : Real)))
          l (nhds 0)) :
    Tendsto
      (fun index =>
        scale index *
          l1PATEDoubleScoreShareDistance cells (sampleA index) (sampleB index)
            (fun _unit => commonWeightA index)
            (fun _unit => commonWeightB index)
            (propensityScore index) (treatedPrognosticScore index)
            (controlPrognosticScore index))
      l (nhds 0) := by
  unfold l1PATEDoubleScoreShareDistance
  exact
    tendsto_scaled_l1ScoreCellShareDistance_zero_of_card_ratio_cellwise_constant_weight
      cells scale sampleA sampleB commonWeightA commonWeightB
      (fun index =>
        pateDoubleScore (propensityScore index)
          (treatedPrognosticScore index)
          (controlPrognosticScore index))
      (fun index =>
        pateDoubleScore (propensityScore index)
          (treatedPrognosticScore index)
          (controlPrognosticScore index))
      hscale_nonneg hweightA hweightB hnonemptyA hnonemptyB hcell

/--
Ordinary and scaled PATE double-score L1 share convergence from pointwise
ordinary and scaled card-ratio convergence under common weights.
-/
theorem tendsto_l1PATEDoubleScoreShareDistance_zero_and_scaled_zero_of_card_ratio_cellwise_constant_weight
    (cells :
      Finset ((PropensityCell × TreatedProgCell) × ControlProgCell))
    (scale : Index -> Real)
    (sampleA sampleB : Index -> Finset UnitA)
    (commonWeightA commonWeightB : Index -> Real)
    (propensityScore : Index -> UnitA -> PropensityCell)
    (treatedPrognosticScore : Index -> UnitA -> TreatedProgCell)
    (controlPrognosticScore : Index -> UnitA -> ControlProgCell)
    (hscale_nonneg : ∀ index, 0 ≤ scale index)
    (hweightA : ∀ index, commonWeightA index ≠ 0)
    (hweightB : ∀ index, commonWeightB index ≠ 0)
    (hnonemptyA : ∀ index, (sampleA index).Nonempty)
    (hnonemptyB : ∀ index, (sampleB index).Nonempty)
    (hcell :
      ∀ cell, cell ∈ cells ->
        Tendsto
          (fun index =>
            (((sampleA index).filter
                  (fun unit =>
                    pateDoubleScore (propensityScore index)
                      (treatedPrognosticScore index)
                      (controlPrognosticScore index) unit = cell)).card :
                Real) /
                ((sampleA index).card : Real) -
              (((sampleB index).filter
                  (fun unit =>
                    pateDoubleScore (propensityScore index)
                      (treatedPrognosticScore index)
                      (controlPrognosticScore index) unit = cell)).card :
                Real) /
                ((sampleB index).card : Real))
          l (nhds 0))
    (hscaledCell :
      ∀ cell, cell ∈ cells ->
        Tendsto
          (fun index =>
            scale index *
              ((((sampleA index).filter
                    (fun unit =>
                      pateDoubleScore (propensityScore index)
                        (treatedPrognosticScore index)
                        (controlPrognosticScore index) unit = cell)).card :
                  Real) /
                  ((sampleA index).card : Real) -
                (((sampleB index).filter
                    (fun unit =>
                      pateDoubleScore (propensityScore index)
                        (treatedPrognosticScore index)
                        (controlPrognosticScore index) unit = cell)).card :
                  Real) /
                  ((sampleB index).card : Real)))
          l (nhds 0)) :
    Tendsto
        (fun index =>
          l1PATEDoubleScoreShareDistance cells (sampleA index) (sampleB index)
            (fun _unit => commonWeightA index)
            (fun _unit => commonWeightB index)
            (propensityScore index) (treatedPrognosticScore index)
            (controlPrognosticScore index))
        l (nhds 0) ∧
      Tendsto
        (fun index =>
          scale index *
            l1PATEDoubleScoreShareDistance cells (sampleA index)
              (sampleB index)
              (fun _unit => commonWeightA index)
              (fun _unit => commonWeightB index)
              (propensityScore index) (treatedPrognosticScore index)
              (controlPrognosticScore index))
        l (nhds 0) := by
  constructor
  · exact
      tendsto_l1PATEDoubleScoreShareDistance_zero_of_card_ratio_cellwise_constant_weight
        cells sampleA sampleB commonWeightA commonWeightB propensityScore
        treatedPrognosticScore controlPrognosticScore hweightA hweightB
        hnonemptyA hnonemptyB hcell
  · exact
      tendsto_scaled_l1PATEDoubleScoreShareDistance_zero_of_card_ratio_cellwise_constant_weight
        cells scale sampleA sampleB commonWeightA commonWeightB
        propensityScore treatedPrognosticScore controlPrognosticScore
        hscale_nonneg hweightA hweightB hnonemptyA hnonemptyB hscaledCell

theorem tendsto_l1PATTDoubleScoreShareDistance_zero_of_card_ratio_cellwise_constant_weight
    (cells : Finset (PropensityCell × PATTProgCell))
    (sampleA sampleB : Index -> Finset UnitA)
    (commonWeightA commonWeightB : Index -> Real)
    (propensityScore : Index -> UnitA -> PropensityCell)
    (controlPrognosticScore : Index -> UnitA -> PATTProgCell)
    (hweightA : ∀ index, commonWeightA index ≠ 0)
    (hweightB : ∀ index, commonWeightB index ≠ 0)
    (hnonemptyA : ∀ index, (sampleA index).Nonempty)
    (hnonemptyB : ∀ index, (sampleB index).Nonempty)
    (hcell :
      ∀ cell, cell ∈ cells ->
        Tendsto
          (fun index =>
            (((sampleA index).filter
                  (fun unit =>
                    pattDoubleScore (propensityScore index)
                      (controlPrognosticScore index) unit = cell)).card :
                Real) /
                ((sampleA index).card : Real) -
              (((sampleB index).filter
                  (fun unit =>
                    pattDoubleScore (propensityScore index)
                      (controlPrognosticScore index) unit = cell)).card :
                Real) /
                ((sampleB index).card : Real))
          l (nhds 0)) :
    Tendsto
      (fun index =>
        l1PATTDoubleScoreShareDistance cells (sampleA index) (sampleB index)
          (fun _unit => commonWeightA index) (fun _unit => commonWeightB index)
          (propensityScore index) (controlPrognosticScore index))
      l (nhds 0) := by
  unfold l1PATTDoubleScoreShareDistance
  exact
    tendsto_l1ScoreCellShareDistance_zero_of_card_ratio_cellwise_constant_weight
      cells sampleA sampleB commonWeightA commonWeightB
      (fun index =>
        pattDoubleScore (propensityScore index) (controlPrognosticScore index))
      (fun index =>
        pattDoubleScore (propensityScore index) (controlPrognosticScore index))
      hweightA hweightB hnonemptyA hnonemptyB hcell

theorem tendsto_scaled_l1PATTDoubleScoreShareDistance_zero_of_card_ratio_cellwise_constant_weight
    (cells : Finset (PropensityCell × PATTProgCell))
    (scale : Index -> Real)
    (sampleA sampleB : Index -> Finset UnitA)
    (commonWeightA commonWeightB : Index -> Real)
    (propensityScore : Index -> UnitA -> PropensityCell)
    (controlPrognosticScore : Index -> UnitA -> PATTProgCell)
    (hscale_nonneg : ∀ index, 0 ≤ scale index)
    (hweightA : ∀ index, commonWeightA index ≠ 0)
    (hweightB : ∀ index, commonWeightB index ≠ 0)
    (hnonemptyA : ∀ index, (sampleA index).Nonempty)
    (hnonemptyB : ∀ index, (sampleB index).Nonempty)
    (hcell :
      ∀ cell, cell ∈ cells ->
        Tendsto
          (fun index =>
            scale index *
              ((((sampleA index).filter
                    (fun unit =>
                      pattDoubleScore (propensityScore index)
                        (controlPrognosticScore index) unit = cell)).card :
                  Real) /
                  ((sampleA index).card : Real) -
                (((sampleB index).filter
                    (fun unit =>
                      pattDoubleScore (propensityScore index)
                        (controlPrognosticScore index) unit = cell)).card :
                  Real) /
                  ((sampleB index).card : Real)))
          l (nhds 0)) :
    Tendsto
      (fun index =>
        scale index *
          l1PATTDoubleScoreShareDistance cells (sampleA index) (sampleB index)
            (fun _unit => commonWeightA index)
            (fun _unit => commonWeightB index)
            (propensityScore index) (controlPrognosticScore index))
      l (nhds 0) := by
  unfold l1PATTDoubleScoreShareDistance
  exact
    tendsto_scaled_l1ScoreCellShareDistance_zero_of_card_ratio_cellwise_constant_weight
      cells scale sampleA sampleB commonWeightA commonWeightB
      (fun index =>
        pattDoubleScore (propensityScore index) (controlPrognosticScore index))
      (fun index =>
        pattDoubleScore (propensityScore index) (controlPrognosticScore index))
      hscale_nonneg hweightA hweightB hnonemptyA hnonemptyB hcell

/--
Ordinary and scaled PATT double-score L1 share convergence from pointwise
ordinary and scaled card-ratio convergence under common weights.
-/
theorem tendsto_l1PATTDoubleScoreShareDistance_zero_and_scaled_zero_of_card_ratio_cellwise_constant_weight
    (cells : Finset (PropensityCell × PATTProgCell))
    (scale : Index -> Real)
    (sampleA sampleB : Index -> Finset UnitA)
    (commonWeightA commonWeightB : Index -> Real)
    (propensityScore : Index -> UnitA -> PropensityCell)
    (controlPrognosticScore : Index -> UnitA -> PATTProgCell)
    (hscale_nonneg : ∀ index, 0 ≤ scale index)
    (hweightA : ∀ index, commonWeightA index ≠ 0)
    (hweightB : ∀ index, commonWeightB index ≠ 0)
    (hnonemptyA : ∀ index, (sampleA index).Nonempty)
    (hnonemptyB : ∀ index, (sampleB index).Nonempty)
    (hcell :
      ∀ cell, cell ∈ cells ->
        Tendsto
          (fun index =>
            (((sampleA index).filter
                  (fun unit =>
                    pattDoubleScore (propensityScore index)
                      (controlPrognosticScore index) unit = cell)).card :
                Real) /
                ((sampleA index).card : Real) -
              (((sampleB index).filter
                  (fun unit =>
                    pattDoubleScore (propensityScore index)
                      (controlPrognosticScore index) unit = cell)).card :
                Real) /
                ((sampleB index).card : Real))
          l (nhds 0))
    (hscaledCell :
      ∀ cell, cell ∈ cells ->
        Tendsto
          (fun index =>
            scale index *
              ((((sampleA index).filter
                    (fun unit =>
                      pattDoubleScore (propensityScore index)
                        (controlPrognosticScore index) unit = cell)).card :
                  Real) /
                  ((sampleA index).card : Real) -
                (((sampleB index).filter
                    (fun unit =>
                      pattDoubleScore (propensityScore index)
                        (controlPrognosticScore index) unit = cell)).card :
                  Real) /
                  ((sampleB index).card : Real)))
          l (nhds 0)) :
    Tendsto
        (fun index =>
          l1PATTDoubleScoreShareDistance cells (sampleA index) (sampleB index)
            (fun _unit => commonWeightA index)
            (fun _unit => commonWeightB index)
            (propensityScore index) (controlPrognosticScore index))
        l (nhds 0) ∧
      Tendsto
        (fun index =>
          scale index *
            l1PATTDoubleScoreShareDistance cells (sampleA index)
              (sampleB index)
              (fun _unit => commonWeightA index)
              (fun _unit => commonWeightB index)
              (propensityScore index) (controlPrognosticScore index))
        l (nhds 0) := by
  constructor
  · exact
      tendsto_l1PATTDoubleScoreShareDistance_zero_of_card_ratio_cellwise_constant_weight
        cells sampleA sampleB commonWeightA commonWeightB propensityScore
        controlPrognosticScore hweightA hweightB hnonemptyA hnonemptyB
        hcell
  · exact
      tendsto_scaled_l1PATTDoubleScoreShareDistance_zero_of_card_ratio_cellwise_constant_weight
        cells scale sampleA sampleB commonWeightA commonWeightB
        propensityScore controlPrognosticScore hscale_nonneg hweightA
        hweightB hnonemptyA hnonemptyB hscaledCell

/--
Paired PATE/PATT ordinary and scaled double-score L1 share convergence from
pointwise ordinary and scaled card-ratio convergence under common weights.
-/
theorem tendsto_l1PATE_PATTDoubleScoreShareDistance_zero_and_scaled_zero_of_card_ratio_cellwise_constant_weight
    (pateCells :
      Finset ((PropensityCell × TreatedProgCell) × ControlProgCell))
    (pattCells : Finset (PropensityCell × PATTProgCell))
    (scale : Index -> Real)
    (sampleA sampleB : Index -> Finset UnitA)
    (commonWeightA commonWeightB : Index -> Real)
    (propensityScore : Index -> UnitA -> PropensityCell)
    (treatedPrognosticScore : Index -> UnitA -> TreatedProgCell)
    (controlPrognosticScore : Index -> UnitA -> ControlProgCell)
    (pattPrognosticScore : Index -> UnitA -> PATTProgCell)
    (hscale_nonneg : ∀ index, 0 ≤ scale index)
    (hweightA : ∀ index, commonWeightA index ≠ 0)
    (hweightB : ∀ index, commonWeightB index ≠ 0)
    (hnonemptyA : ∀ index, (sampleA index).Nonempty)
    (hnonemptyB : ∀ index, (sampleB index).Nonempty)
    (hpateCell :
      ∀ cell, cell ∈ pateCells ->
        Tendsto
          (fun index =>
            (((sampleA index).filter
                  (fun unit =>
                    pateDoubleScore (propensityScore index)
                      (treatedPrognosticScore index)
                      (controlPrognosticScore index) unit = cell)).card :
                Real) /
                ((sampleA index).card : Real) -
              (((sampleB index).filter
                  (fun unit =>
                    pateDoubleScore (propensityScore index)
                      (treatedPrognosticScore index)
                      (controlPrognosticScore index) unit = cell)).card :
                Real) /
                ((sampleB index).card : Real))
          l (nhds 0))
    (hpateScaledCell :
      ∀ cell, cell ∈ pateCells ->
        Tendsto
          (fun index =>
            scale index *
              ((((sampleA index).filter
                    (fun unit =>
                      pateDoubleScore (propensityScore index)
                        (treatedPrognosticScore index)
                        (controlPrognosticScore index) unit = cell)).card :
                  Real) /
                  ((sampleA index).card : Real) -
                (((sampleB index).filter
                    (fun unit =>
                      pateDoubleScore (propensityScore index)
                        (treatedPrognosticScore index)
                        (controlPrognosticScore index) unit = cell)).card :
                  Real) /
                  ((sampleB index).card : Real)))
          l (nhds 0))
    (hpattCell :
      ∀ cell, cell ∈ pattCells ->
        Tendsto
          (fun index =>
            (((sampleA index).filter
                  (fun unit =>
                    pattDoubleScore (propensityScore index)
                      (pattPrognosticScore index) unit = cell)).card :
                Real) /
                ((sampleA index).card : Real) -
              (((sampleB index).filter
                  (fun unit =>
                    pattDoubleScore (propensityScore index)
                      (pattPrognosticScore index) unit = cell)).card :
                Real) /
                ((sampleB index).card : Real))
          l (nhds 0))
    (hpattScaledCell :
      ∀ cell, cell ∈ pattCells ->
        Tendsto
          (fun index =>
            scale index *
              ((((sampleA index).filter
                    (fun unit =>
                      pattDoubleScore (propensityScore index)
                        (pattPrognosticScore index) unit = cell)).card :
                  Real) /
                  ((sampleA index).card : Real) -
                (((sampleB index).filter
                    (fun unit =>
                      pattDoubleScore (propensityScore index)
                        (pattPrognosticScore index) unit = cell)).card :
                  Real) /
                  ((sampleB index).card : Real)))
          l (nhds 0)) :
    (Tendsto
        (fun index =>
          l1PATEDoubleScoreShareDistance pateCells (sampleA index)
            (sampleB index)
            (fun _unit => commonWeightA index)
            (fun _unit => commonWeightB index)
            (propensityScore index) (treatedPrognosticScore index)
            (controlPrognosticScore index))
        l (nhds 0) ∧
      Tendsto
        (fun index =>
          scale index *
            l1PATEDoubleScoreShareDistance pateCells (sampleA index)
              (sampleB index)
              (fun _unit => commonWeightA index)
              (fun _unit => commonWeightB index)
              (propensityScore index) (treatedPrognosticScore index)
              (controlPrognosticScore index))
        l (nhds 0)) ∧
      (Tendsto
        (fun index =>
          l1PATTDoubleScoreShareDistance pattCells (sampleA index)
            (sampleB index)
            (fun _unit => commonWeightA index)
            (fun _unit => commonWeightB index)
            (propensityScore index) (pattPrognosticScore index))
        l (nhds 0) ∧
      Tendsto
        (fun index =>
          scale index *
            l1PATTDoubleScoreShareDistance pattCells (sampleA index)
              (sampleB index)
              (fun _unit => commonWeightA index)
              (fun _unit => commonWeightB index)
              (propensityScore index) (pattPrognosticScore index))
        l (nhds 0)) := by
  constructor
  · exact
      tendsto_l1PATEDoubleScoreShareDistance_zero_and_scaled_zero_of_card_ratio_cellwise_constant_weight
        pateCells scale sampleA sampleB commonWeightA commonWeightB
        propensityScore treatedPrognosticScore controlPrognosticScore
        hscale_nonneg hweightA hweightB hnonemptyA hnonemptyB hpateCell
        hpateScaledCell
  · exact
      tendsto_l1PATTDoubleScoreShareDistance_zero_and_scaled_zero_of_card_ratio_cellwise_constant_weight
        pattCells scale sampleA sampleB commonWeightA commonWeightB
        propensityScore pattPrognosticScore hscale_nonneg hweightA hweightB
        hnonemptyA hnonemptyB hpattCell hpattScaledCell

end WDSM
end Matching
end StatInference
