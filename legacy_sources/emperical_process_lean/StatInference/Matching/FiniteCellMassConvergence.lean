import StatInference.Matching.WDSM.FiniteCellShareConvergence
import StatInference.Matching.WDSM.FiniteCellShareRatioConvergence

/-!
# Finite score-cell mass convergence for WDSM

This module composes the two deterministic reductions now proved:

* pointwise score-cell share convergence follows from convergence of weighted
  cell masses and total weighted masses;
* pointwise finite-cell share convergence implies L1 share convergence over a
  fixed finite partition.

The resulting theorems expose the next stochastic target as finite weighted
cell-mass and total-mass convergence.
-/

namespace StatInference
namespace Matching
namespace WDSM

open Filter

variable {Index UnitA UnitB Cell : Type*} {l : Filter Index}
  [DecidableEq Cell]

/-- A finite sum of cell-indexed values converges when every fixed cell does. -/
theorem tendsto_sum_cell_values
    (cells : Finset Cell) (value : Index -> Cell -> Real)
    (limit : Cell -> Real)
    (hvalue :
      ∀ cell, cell ∈ cells ->
        Tendsto (fun index => value index cell) l (nhds (limit cell))) :
    Tendsto (fun index => ∑ cell ∈ cells, value index cell)
      l (nhds (∑ cell ∈ cells, limit cell)) := by
  classical
  induction cells using Finset.induction with
  | empty =>
      simpa using
        (tendsto_const_nhds :
          Tendsto (fun _ : Index => (0 : Real)) l (nhds 0))
  | insert cell cells hnot_mem ih =>
      have hcell :
          Tendsto (fun index => value index cell) l (nhds (limit cell)) :=
        hvalue cell (by simp [hnot_mem])
      have hrest :
          Tendsto (fun index => ∑ other ∈ cells, value index other)
            l (nhds (∑ other ∈ cells, limit other)) :=
        ih (fun other hother => hvalue other (by simp [hother]))
      simpa [Finset.sum_insert, hnot_mem] using hcell.add hrest

/-- A finite sum of cell-indexed negligible values is negligible. -/
theorem tendsto_sum_cell_values_zero
    (cells : Finset Cell) (value : Index -> Cell -> Real)
    (hvalue :
      ∀ cell, cell ∈ cells ->
        Tendsto (fun index => value index cell) l (nhds 0)) :
    Tendsto (fun index => ∑ cell ∈ cells, value index cell)
      l (nhds 0) := by
  simpa using
    tendsto_sum_cell_values cells value (fun _cell => (0 : Real)) hvalue

/--
Total weighted-mass convergence follows from cellwise mass convergence when a
fixed finite partition covers every sampled unit.
-/
theorem tendsto_weightedSampleTotal_of_cell_mass
    (cells : Finset Cell)
    (sample : Index -> Finset UnitA)
    (weight : Index -> UnitA -> Real)
    (score : Index -> UnitA -> Cell)
    (massLimit : Cell -> Real)
    (hcover :
      ∀ index unit, unit ∈ sample index -> score index unit ∈ cells)
    (hmass :
      ∀ cell, cell ∈ cells ->
        Tendsto
          (fun index =>
            scoreCellMass (sample index) (weight index)
              (score index) cell)
          l (nhds (massLimit cell))) :
    Tendsto
      (fun index => weightedSampleTotal (sample index) (weight index))
      l (nhds (∑ cell ∈ cells, massLimit cell)) := by
  have hsum :
      Tendsto
        (fun index =>
          ∑ cell ∈ cells,
            scoreCellMass (sample index) (weight index)
              (score index) cell)
        l (nhds (∑ cell ∈ cells, massLimit cell)) :=
    tendsto_sum_cell_values cells
      (fun index cell =>
        scoreCellMass (sample index) (weight index)
          (score index) cell)
      massLimit hmass
  convert hsum using 1
  ext index
  exact (sum_scoreCellMass_eq_weightedSampleTotal_of_mapsTo
    (sample index) cells (weight index) (score index) (hcover index)).symm

/--
Scaled total-mass differences vanish when every scaled cell-mass difference
vanishes over a fixed finite partition covering both samples.
-/
theorem tendsto_scaled_weightedSampleTotal_sub_zero_of_cell_mass
    (cells : Finset Cell) (scale : Index -> Real)
    (sampleA : Index -> Finset UnitA) (sampleB : Index -> Finset UnitB)
    (weightA : Index -> UnitA -> Real)
    (weightB : Index -> UnitB -> Real)
    (scoreA : Index -> UnitA -> Cell)
    (scoreB : Index -> UnitB -> Cell)
    (hcoverA :
      ∀ index unit, unit ∈ sampleA index -> scoreA index unit ∈ cells)
    (hcoverB :
      ∀ index unit, unit ∈ sampleB index -> scoreB index unit ∈ cells)
    (hscaledMass :
      ∀ cell, cell ∈ cells ->
        Tendsto
          (fun index =>
            scale index *
              (scoreCellMass (sampleA index) (weightA index)
                  (scoreA index) cell -
                scoreCellMass (sampleB index) (weightB index)
                  (scoreB index) cell))
          l (nhds 0)) :
    Tendsto
      (fun index =>
        scale index *
          (weightedSampleTotal (sampleA index) (weightA index) -
            weightedSampleTotal (sampleB index) (weightB index)))
      l (nhds 0) := by
  have hsum :
      Tendsto
        (fun index =>
          ∑ cell ∈ cells,
            scale index *
              (scoreCellMass (sampleA index) (weightA index)
                  (scoreA index) cell -
                scoreCellMass (sampleB index) (weightB index)
                  (scoreB index) cell))
        l (nhds 0) :=
    tendsto_sum_cell_values_zero cells
      (fun index cell =>
        scale index *
          (scoreCellMass (sampleA index) (weightA index)
              (scoreA index) cell -
            scoreCellMass (sampleB index) (weightB index)
              (scoreB index) cell))
      hscaledMass
  convert hsum using 1
  ext index
  have hA :=
    sum_scoreCellMass_eq_weightedSampleTotal_of_mapsTo
      (sampleA index) cells (weightA index) (scoreA index)
      (hcoverA index)
  have hB :=
    sum_scoreCellMass_eq_weightedSampleTotal_of_mapsTo
      (sampleB index) cells (weightB index) (scoreB index)
      (hcoverB index)
  calc
    scale index *
        (weightedSampleTotal (sampleA index) (weightA index) -
          weightedSampleTotal (sampleB index) (weightB index))
        =
        scale index *
          ((∑ cell ∈ cells,
              scoreCellMass (sampleA index) (weightA index)
                (scoreA index) cell) -
            (∑ cell ∈ cells,
              scoreCellMass (sampleB index) (weightB index)
                (scoreB index) cell)) := by
          rw [← hA, ← hB]
    _ =
        ∑ cell ∈ cells,
          scale index *
            (scoreCellMass (sampleA index) (weightA index)
                (scoreA index) cell -
              scoreCellMass (sampleB index) (weightB index)
                (scoreB index) cell) := by
          rw [← Finset.sum_sub_distrib, Finset.mul_sum]

/--
L1 convergence of fixed finite score-cell shares follows from cellwise
weighted-mass convergence and common total-mass convergence.
-/
theorem tendsto_l1ScoreCellShareDistance_zero_of_cell_mass_total
    (cells : Finset Cell)
    (sampleA : Index -> Finset UnitA) (sampleB : Index -> Finset UnitB)
    (weightA : Index -> UnitA -> Real)
    (weightB : Index -> UnitB -> Real)
    (scoreA : Index -> UnitA -> Cell)
    (scoreB : Index -> UnitB -> Cell)
    (massLimit : Cell -> Real) (totalLimit : Real)
    (hmassA :
      ∀ cell, cell ∈ cells ->
        Tendsto
          (fun index =>
            scoreCellMass (sampleA index) (weightA index)
              (scoreA index) cell)
          l (nhds (massLimit cell)))
    (hmassB :
      ∀ cell, cell ∈ cells ->
        Tendsto
          (fun index =>
            scoreCellMass (sampleB index) (weightB index)
              (scoreB index) cell)
          l (nhds (massLimit cell)))
    (htotalA :
      Tendsto
        (fun index => weightedSampleTotal (sampleA index) (weightA index))
        l (nhds totalLimit))
    (htotalB :
      Tendsto
        (fun index => weightedSampleTotal (sampleB index) (weightB index))
        l (nhds totalLimit))
    (htotalLimit : totalLimit ≠ 0) :
    Tendsto
      (fun index =>
        l1ScoreCellShareDistance cells (sampleA index) (sampleB index)
          (weightA index) (weightB index) (scoreA index) (scoreB index))
      l (nhds 0) := by
  exact tendsto_l1ScoreCellShareDistance_zero_of_cellwise
    cells sampleA sampleB weightA weightB scoreA scoreB
    (fun cell hcell =>
      tendsto_scoreCellShare_sub_scoreCellShare_zero_of_mass_total
        sampleA sampleB weightA weightB scoreA scoreB cell
        (massLimit cell) totalLimit (hmassA cell hcell)
        (hmassB cell hcell) htotalA htotalB htotalLimit)

/--
If a fixed finite partition covers both samples, L1 convergence of score-cell
shares follows from only the common cellwise weighted-mass limits.
-/
theorem tendsto_l1ScoreCellShareDistance_zero_of_cell_mass
    (cells : Finset Cell)
    (sampleA : Index -> Finset UnitA) (sampleB : Index -> Finset UnitB)
    (weightA : Index -> UnitA -> Real)
    (weightB : Index -> UnitB -> Real)
    (scoreA : Index -> UnitA -> Cell)
    (scoreB : Index -> UnitB -> Cell)
    (massLimit : Cell -> Real)
    (hcoverA :
      ∀ index unit, unit ∈ sampleA index -> scoreA index unit ∈ cells)
    (hcoverB :
      ∀ index unit, unit ∈ sampleB index -> scoreB index unit ∈ cells)
    (hmassA :
      ∀ cell, cell ∈ cells ->
        Tendsto
          (fun index =>
            scoreCellMass (sampleA index) (weightA index)
              (scoreA index) cell)
          l (nhds (massLimit cell)))
    (hmassB :
      ∀ cell, cell ∈ cells ->
        Tendsto
          (fun index =>
            scoreCellMass (sampleB index) (weightB index)
              (scoreB index) cell)
          l (nhds (massLimit cell)))
    (htotalLimit : (∑ cell ∈ cells, massLimit cell) ≠ 0) :
    Tendsto
      (fun index =>
        l1ScoreCellShareDistance cells (sampleA index) (sampleB index)
          (weightA index) (weightB index) (scoreA index) (scoreB index))
      l (nhds 0) := by
  exact tendsto_l1ScoreCellShareDistance_zero_of_cell_mass_total
    cells sampleA sampleB weightA weightB scoreA scoreB massLimit
    (∑ cell ∈ cells, massLimit cell) hmassA hmassB
    (tendsto_weightedSampleTotal_of_cell_mass
      cells sampleA weightA scoreA massLimit hcoverA hmassA)
    (tendsto_weightedSampleTotal_of_cell_mass
      cells sampleB weightB scoreB massLimit hcoverB hmassB)
    htotalLimit

/--
Scaled L1 convergence of score-cell shares follows from common cellwise
weighted-mass limits plus scaled cell-mass-difference convergence over a fixed
finite partition covering both samples.
-/
theorem tendsto_scaled_l1ScoreCellShareDistance_zero_of_cell_mass
    (cells : Finset Cell) (scale : Index -> Real)
    (sampleA : Index -> Finset UnitA) (sampleB : Index -> Finset UnitB)
    (weightA : Index -> UnitA -> Real)
    (weightB : Index -> UnitB -> Real)
    (scoreA : Index -> UnitA -> Cell)
    (scoreB : Index -> UnitB -> Cell)
    (massLimit : Cell -> Real)
    (hscale_nonneg : ∀ index, 0 ≤ scale index)
    (hcoverA :
      ∀ index unit, unit ∈ sampleA index -> scoreA index unit ∈ cells)
    (hcoverB :
      ∀ index unit, unit ∈ sampleB index -> scoreB index unit ∈ cells)
    (hmassA :
      ∀ cell, cell ∈ cells ->
        Tendsto
          (fun index =>
            scoreCellMass (sampleA index) (weightA index)
              (scoreA index) cell)
          l (nhds (massLimit cell)))
    (hmassB :
      ∀ cell, cell ∈ cells ->
        Tendsto
          (fun index =>
            scoreCellMass (sampleB index) (weightB index)
              (scoreB index) cell)
          l (nhds (massLimit cell)))
    (hscaledMass :
      ∀ cell, cell ∈ cells ->
        Tendsto
          (fun index =>
            scale index *
              (scoreCellMass (sampleA index) (weightA index)
                  (scoreA index) cell -
                scoreCellMass (sampleB index) (weightB index)
                  (scoreB index) cell))
          l (nhds 0))
    (htotalLimit : (∑ cell ∈ cells, massLimit cell) ≠ 0) :
    Tendsto
      (fun index =>
        scale index *
          l1ScoreCellShareDistance cells (sampleA index) (sampleB index)
            (weightA index) (weightB index) (scoreA index) (scoreB index))
      l (nhds 0) := by
  have htotalA :
      Tendsto
        (fun index => weightedSampleTotal (sampleA index) (weightA index))
        l (nhds (∑ cell ∈ cells, massLimit cell)) :=
    tendsto_weightedSampleTotal_of_cell_mass
      cells sampleA weightA scoreA massLimit hcoverA hmassA
  have htotalB :
      Tendsto
        (fun index => weightedSampleTotal (sampleB index) (weightB index))
        l (nhds (∑ cell ∈ cells, massLimit cell)) :=
    tendsto_weightedSampleTotal_of_cell_mass
      cells sampleB weightB scoreB massLimit hcoverB hmassB
  have hscaledTotal :
      Tendsto
        (fun index =>
          scale index *
            (weightedSampleTotal (sampleA index) (weightA index) -
              weightedSampleTotal (sampleB index) (weightB index)))
        l (nhds 0) :=
    tendsto_scaled_weightedSampleTotal_sub_zero_of_cell_mass
      cells scale sampleA sampleB weightA weightB scoreA scoreB
      hcoverA hcoverB hscaledMass
  exact tendsto_scaled_l1ScoreCellShareDistance_zero_of_cellwise
    cells scale sampleA sampleB weightA weightB scoreA scoreB
    hscale_nonneg
    (fun cell hcell =>
      tendsto_scaled_scoreCellShare_sub_scoreCellShare_zero_of_mass_total
        scale sampleA sampleB weightA weightB scoreA scoreB cell
        (massLimit cell) (∑ cell ∈ cells, massLimit cell)
        (hmassB cell hcell) htotalA htotalB (hscaledMass cell hcell)
        hscaledTotal htotalLimit)

variable {Unit PropensityCell TreatedProgCell ControlProgCell PATTProgCell : Type*}
  [DecidableEq PropensityCell] [DecidableEq TreatedProgCell]
  [DecidableEq ControlProgCell] [DecidableEq PATTProgCell]

/--
Fixed finite PATE double-score L1 share convergence follows from convergence
of each joint double-score cell mass and the two total weighted masses.
-/
theorem tendsto_l1PATEDoubleScoreShareDistance_zero_of_cell_mass_total
    (cells :
      Finset ((PropensityCell × TreatedProgCell) × ControlProgCell))
    (sampleA sampleB : Index -> Finset Unit)
    (weightA weightB : Index -> Unit -> Real)
    (propensityScore : Index -> Unit -> PropensityCell)
    (treatedPrognosticScore : Index -> Unit -> TreatedProgCell)
    (controlPrognosticScore : Index -> Unit -> ControlProgCell)
    (massLimit :
      (PropensityCell × TreatedProgCell) × ControlProgCell -> Real)
    (totalLimit : Real)
    (hmassA :
      ∀ cell, cell ∈ cells ->
        Tendsto
          (fun index =>
            scoreCellMass (sampleA index) (weightA index)
              (pateDoubleScore (propensityScore index)
                (treatedPrognosticScore index)
                (controlPrognosticScore index)) cell)
          l (nhds (massLimit cell)))
    (hmassB :
      ∀ cell, cell ∈ cells ->
        Tendsto
          (fun index =>
            scoreCellMass (sampleB index) (weightB index)
              (pateDoubleScore (propensityScore index)
                (treatedPrognosticScore index)
                (controlPrognosticScore index)) cell)
          l (nhds (massLimit cell)))
    (htotalA :
      Tendsto
        (fun index => weightedSampleTotal (sampleA index) (weightA index))
        l (nhds totalLimit))
    (htotalB :
      Tendsto
        (fun index => weightedSampleTotal (sampleB index) (weightB index))
        l (nhds totalLimit))
    (htotalLimit : totalLimit ≠ 0) :
    Tendsto
      (fun index =>
        l1PATEDoubleScoreShareDistance cells (sampleA index) (sampleB index)
          (weightA index) (weightB index) (propensityScore index)
          (treatedPrognosticScore index) (controlPrognosticScore index))
      l (nhds 0) := by
  exact tendsto_l1PATEDoubleScoreShareDistance_zero_of_cellwise
    cells sampleA sampleB weightA weightB propensityScore
    treatedPrognosticScore controlPrognosticScore
    (fun cell hcell =>
      tendsto_pateDoubleScoreShare_sub_zero_of_mass_total
        sampleA sampleB weightA weightB propensityScore propensityScore
        treatedPrognosticScore treatedPrognosticScore
        controlPrognosticScore controlPrognosticScore cell
        (massLimit cell) totalLimit (hmassA cell hcell)
        (hmassB cell hcell) htotalA htotalB htotalLimit)

/--
PATE double-score L1 share convergence follows from common joint cell-mass
limits when the fixed joint score partition covers both samples.
-/
theorem tendsto_l1PATEDoubleScoreShareDistance_zero_of_cell_mass
    (cells :
      Finset ((PropensityCell × TreatedProgCell) × ControlProgCell))
    (sampleA sampleB : Index -> Finset Unit)
    (weightA weightB : Index -> Unit -> Real)
    (propensityScore : Index -> Unit -> PropensityCell)
    (treatedPrognosticScore : Index -> Unit -> TreatedProgCell)
    (controlPrognosticScore : Index -> Unit -> ControlProgCell)
    (massLimit :
      (PropensityCell × TreatedProgCell) × ControlProgCell -> Real)
    (hcoverA :
      ∀ index unit, unit ∈ sampleA index ->
        pateDoubleScore (propensityScore index)
          (treatedPrognosticScore index)
          (controlPrognosticScore index) unit ∈ cells)
    (hcoverB :
      ∀ index unit, unit ∈ sampleB index ->
        pateDoubleScore (propensityScore index)
          (treatedPrognosticScore index)
          (controlPrognosticScore index) unit ∈ cells)
    (hmassA :
      ∀ cell, cell ∈ cells ->
        Tendsto
          (fun index =>
            scoreCellMass (sampleA index) (weightA index)
              (pateDoubleScore (propensityScore index)
                (treatedPrognosticScore index)
                (controlPrognosticScore index)) cell)
          l (nhds (massLimit cell)))
    (hmassB :
      ∀ cell, cell ∈ cells ->
        Tendsto
          (fun index =>
            scoreCellMass (sampleB index) (weightB index)
              (pateDoubleScore (propensityScore index)
                (treatedPrognosticScore index)
                (controlPrognosticScore index)) cell)
          l (nhds (massLimit cell)))
    (htotalLimit : (∑ cell ∈ cells, massLimit cell) ≠ 0) :
    Tendsto
      (fun index =>
        l1PATEDoubleScoreShareDistance cells (sampleA index) (sampleB index)
          (weightA index) (weightB index) (propensityScore index)
          (treatedPrognosticScore index) (controlPrognosticScore index))
      l (nhds 0) := by
  exact tendsto_l1PATEDoubleScoreShareDistance_zero_of_cell_mass_total
    cells sampleA sampleB weightA weightB propensityScore
    treatedPrognosticScore controlPrognosticScore massLimit
    (∑ cell ∈ cells, massLimit cell) hmassA hmassB
    (tendsto_weightedSampleTotal_of_cell_mass cells sampleA weightA
      (fun index =>
        pateDoubleScore (propensityScore index)
          (treatedPrognosticScore index) (controlPrognosticScore index))
      massLimit hcoverA hmassA)
    (tendsto_weightedSampleTotal_of_cell_mass cells sampleB weightB
      (fun index =>
        pateDoubleScore (propensityScore index)
          (treatedPrognosticScore index) (controlPrognosticScore index))
      massLimit hcoverB hmassB)
    htotalLimit

/--
Scaled fixed finite PATE double-score L1 share convergence follows from
common joint cell-mass limits plus scaled joint cell-mass-difference
convergence.
-/
theorem tendsto_scaled_l1PATEDoubleScoreShareDistance_zero_of_cell_mass
    (cells :
      Finset ((PropensityCell × TreatedProgCell) × ControlProgCell))
    (scale : Index -> Real)
    (sampleA sampleB : Index -> Finset Unit)
    (weightA weightB : Index -> Unit -> Real)
    (propensityScore : Index -> Unit -> PropensityCell)
    (treatedPrognosticScore : Index -> Unit -> TreatedProgCell)
    (controlPrognosticScore : Index -> Unit -> ControlProgCell)
    (massLimit :
      (PropensityCell × TreatedProgCell) × ControlProgCell -> Real)
    (hscale_nonneg : ∀ index, 0 ≤ scale index)
    (hcoverA :
      ∀ index unit, unit ∈ sampleA index ->
        pateDoubleScore (propensityScore index)
          (treatedPrognosticScore index)
          (controlPrognosticScore index) unit ∈ cells)
    (hcoverB :
      ∀ index unit, unit ∈ sampleB index ->
        pateDoubleScore (propensityScore index)
          (treatedPrognosticScore index)
          (controlPrognosticScore index) unit ∈ cells)
    (hmassA :
      ∀ cell, cell ∈ cells ->
        Tendsto
          (fun index =>
            scoreCellMass (sampleA index) (weightA index)
              (pateDoubleScore (propensityScore index)
                (treatedPrognosticScore index)
                (controlPrognosticScore index)) cell)
          l (nhds (massLimit cell)))
    (hmassB :
      ∀ cell, cell ∈ cells ->
        Tendsto
          (fun index =>
            scoreCellMass (sampleB index) (weightB index)
              (pateDoubleScore (propensityScore index)
                (treatedPrognosticScore index)
                (controlPrognosticScore index)) cell)
          l (nhds (massLimit cell)))
    (hscaledMass :
      ∀ cell, cell ∈ cells ->
        Tendsto
          (fun index =>
            scale index *
              (scoreCellMass (sampleA index) (weightA index)
                  (pateDoubleScore (propensityScore index)
                    (treatedPrognosticScore index)
                    (controlPrognosticScore index)) cell -
                scoreCellMass (sampleB index) (weightB index)
                  (pateDoubleScore (propensityScore index)
                    (treatedPrognosticScore index)
                    (controlPrognosticScore index)) cell))
          l (nhds 0))
    (htotalLimit : (∑ cell ∈ cells, massLimit cell) ≠ 0) :
    Tendsto
      (fun index =>
        scale index *
          l1PATEDoubleScoreShareDistance cells (sampleA index)
            (sampleB index) (weightA index) (weightB index)
            (propensityScore index) (treatedPrognosticScore index)
            (controlPrognosticScore index))
      l (nhds 0) := by
  exact tendsto_scaled_l1ScoreCellShareDistance_zero_of_cell_mass
    cells scale sampleA sampleB weightA weightB
    (fun index =>
      pateDoubleScore (propensityScore index)
        (treatedPrognosticScore index) (controlPrognosticScore index))
    (fun index =>
      pateDoubleScore (propensityScore index)
        (treatedPrognosticScore index) (controlPrognosticScore index))
    massLimit hscale_nonneg hcoverA hcoverB hmassA hmassB
    hscaledMass htotalLimit

/--
Fixed finite PATT double-score L1 share convergence follows from convergence
of each joint double-score cell mass and the two total weighted masses.
-/
theorem tendsto_l1PATTDoubleScoreShareDistance_zero_of_cell_mass_total
    (cells : Finset (PropensityCell × PATTProgCell))
    (sampleA sampleB : Index -> Finset Unit)
    (weightA weightB : Index -> Unit -> Real)
    (propensityScore : Index -> Unit -> PropensityCell)
    (controlPrognosticScore : Index -> Unit -> PATTProgCell)
    (massLimit : PropensityCell × PATTProgCell -> Real)
    (totalLimit : Real)
    (hmassA :
      ∀ cell, cell ∈ cells ->
        Tendsto
          (fun index =>
            scoreCellMass (sampleA index) (weightA index)
              (pattDoubleScore (propensityScore index)
                (controlPrognosticScore index)) cell)
          l (nhds (massLimit cell)))
    (hmassB :
      ∀ cell, cell ∈ cells ->
        Tendsto
          (fun index =>
            scoreCellMass (sampleB index) (weightB index)
              (pattDoubleScore (propensityScore index)
                (controlPrognosticScore index)) cell)
          l (nhds (massLimit cell)))
    (htotalA :
      Tendsto
        (fun index => weightedSampleTotal (sampleA index) (weightA index))
        l (nhds totalLimit))
    (htotalB :
      Tendsto
        (fun index => weightedSampleTotal (sampleB index) (weightB index))
        l (nhds totalLimit))
    (htotalLimit : totalLimit ≠ 0) :
    Tendsto
      (fun index =>
        l1PATTDoubleScoreShareDistance cells (sampleA index) (sampleB index)
          (weightA index) (weightB index) (propensityScore index)
          (controlPrognosticScore index))
      l (nhds 0) := by
  exact tendsto_l1PATTDoubleScoreShareDistance_zero_of_cellwise
    cells sampleA sampleB weightA weightB propensityScore
    controlPrognosticScore
    (fun cell hcell =>
      tendsto_pattDoubleScoreShare_sub_zero_of_mass_total
        sampleA sampleB weightA weightB propensityScore propensityScore
        controlPrognosticScore controlPrognosticScore cell
        (massLimit cell) totalLimit (hmassA cell hcell)
        (hmassB cell hcell) htotalA htotalB htotalLimit)

/--
PATT double-score L1 share convergence follows from common joint cell-mass
limits when the fixed joint score partition covers both samples.
-/
theorem tendsto_l1PATTDoubleScoreShareDistance_zero_of_cell_mass
    (cells : Finset (PropensityCell × PATTProgCell))
    (sampleA sampleB : Index -> Finset Unit)
    (weightA weightB : Index -> Unit -> Real)
    (propensityScore : Index -> Unit -> PropensityCell)
    (controlPrognosticScore : Index -> Unit -> PATTProgCell)
    (massLimit : PropensityCell × PATTProgCell -> Real)
    (hcoverA :
      ∀ index unit, unit ∈ sampleA index ->
        pattDoubleScore (propensityScore index)
          (controlPrognosticScore index) unit ∈ cells)
    (hcoverB :
      ∀ index unit, unit ∈ sampleB index ->
        pattDoubleScore (propensityScore index)
          (controlPrognosticScore index) unit ∈ cells)
    (hmassA :
      ∀ cell, cell ∈ cells ->
        Tendsto
          (fun index =>
            scoreCellMass (sampleA index) (weightA index)
              (pattDoubleScore (propensityScore index)
                (controlPrognosticScore index)) cell)
          l (nhds (massLimit cell)))
    (hmassB :
      ∀ cell, cell ∈ cells ->
        Tendsto
          (fun index =>
            scoreCellMass (sampleB index) (weightB index)
              (pattDoubleScore (propensityScore index)
                (controlPrognosticScore index)) cell)
          l (nhds (massLimit cell)))
    (htotalLimit : (∑ cell ∈ cells, massLimit cell) ≠ 0) :
    Tendsto
      (fun index =>
        l1PATTDoubleScoreShareDistance cells (sampleA index) (sampleB index)
          (weightA index) (weightB index) (propensityScore index)
          (controlPrognosticScore index))
      l (nhds 0) := by
  exact tendsto_l1PATTDoubleScoreShareDistance_zero_of_cell_mass_total
    cells sampleA sampleB weightA weightB propensityScore
    controlPrognosticScore massLimit
    (∑ cell ∈ cells, massLimit cell) hmassA hmassB
    (tendsto_weightedSampleTotal_of_cell_mass cells sampleA weightA
      (fun index =>
        pattDoubleScore (propensityScore index)
          (controlPrognosticScore index))
      massLimit hcoverA hmassA)
    (tendsto_weightedSampleTotal_of_cell_mass cells sampleB weightB
      (fun index =>
        pattDoubleScore (propensityScore index)
          (controlPrognosticScore index))
      massLimit hcoverB hmassB)
    htotalLimit

/--
Scaled fixed finite PATT double-score L1 share convergence follows from
common joint cell-mass limits plus scaled joint cell-mass-difference
convergence.
-/
theorem tendsto_scaled_l1PATTDoubleScoreShareDistance_zero_of_cell_mass
    (cells : Finset (PropensityCell × PATTProgCell))
    (scale : Index -> Real)
    (sampleA sampleB : Index -> Finset Unit)
    (weightA weightB : Index -> Unit -> Real)
    (propensityScore : Index -> Unit -> PropensityCell)
    (controlPrognosticScore : Index -> Unit -> PATTProgCell)
    (massLimit : PropensityCell × PATTProgCell -> Real)
    (hscale_nonneg : ∀ index, 0 ≤ scale index)
    (hcoverA :
      ∀ index unit, unit ∈ sampleA index ->
        pattDoubleScore (propensityScore index)
          (controlPrognosticScore index) unit ∈ cells)
    (hcoverB :
      ∀ index unit, unit ∈ sampleB index ->
        pattDoubleScore (propensityScore index)
          (controlPrognosticScore index) unit ∈ cells)
    (hmassA :
      ∀ cell, cell ∈ cells ->
        Tendsto
          (fun index =>
            scoreCellMass (sampleA index) (weightA index)
              (pattDoubleScore (propensityScore index)
                (controlPrognosticScore index)) cell)
          l (nhds (massLimit cell)))
    (hmassB :
      ∀ cell, cell ∈ cells ->
        Tendsto
          (fun index =>
            scoreCellMass (sampleB index) (weightB index)
              (pattDoubleScore (propensityScore index)
                (controlPrognosticScore index)) cell)
          l (nhds (massLimit cell)))
    (hscaledMass :
      ∀ cell, cell ∈ cells ->
        Tendsto
          (fun index =>
            scale index *
              (scoreCellMass (sampleA index) (weightA index)
                  (pattDoubleScore (propensityScore index)
                    (controlPrognosticScore index)) cell -
                scoreCellMass (sampleB index) (weightB index)
                  (pattDoubleScore (propensityScore index)
                    (controlPrognosticScore index)) cell))
          l (nhds 0))
    (htotalLimit : (∑ cell ∈ cells, massLimit cell) ≠ 0) :
    Tendsto
      (fun index =>
        scale index *
          l1PATTDoubleScoreShareDistance cells (sampleA index)
            (sampleB index) (weightA index) (weightB index)
            (propensityScore index) (controlPrognosticScore index))
      l (nhds 0) := by
  exact tendsto_scaled_l1ScoreCellShareDistance_zero_of_cell_mass
    cells scale sampleA sampleB weightA weightB
    (fun index =>
      pattDoubleScore (propensityScore index)
        (controlPrognosticScore index))
    (fun index =>
      pattDoubleScore (propensityScore index)
        (controlPrognosticScore index))
    massLimit hscale_nonneg hcoverA hcoverB hmassA hmassB
    hscaledMass htotalLimit

end WDSM
end Matching
end StatInference
