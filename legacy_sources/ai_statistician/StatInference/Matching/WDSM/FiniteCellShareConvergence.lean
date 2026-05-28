import StatInference.Matching.WDSM.DiscreteDoubleScoreApproximateBalancingRate

/-!
# Fixed finite-cell share convergence for WDSM

The double-score approximation bridges reduce the stochastic problem to L1
convergence of normalized score-cell share vectors.  For a fixed finite score
partition, this module proves the deterministic topological step: pointwise
cell-share convergence on every cell implies L1 share convergence.  It also
proves the scaled version needed for `sqrt n` arguments.
-/

namespace StatInference
namespace Matching
namespace WDSM

open Filter
open scoped BigOperators

variable {Index Cell : Type*} {l : Filter Index}

theorem tendsto_sum_abs_cell_error_zero
    (cells : Finset Cell) (error : Index -> Cell -> Real)
    (herror :
      ∀ cell, cell ∈ cells ->
        Tendsto (fun index => error index cell) l (nhds 0)) :
    Tendsto (fun index => ∑ cell ∈ cells, |error index cell|)
      l (nhds 0) := by
  classical
  induction cells using Finset.induction with
  | empty =>
      simpa using (tendsto_const_nhds : Tendsto (fun _ : Index => (0 : Real)) l (nhds 0))
  | insert cell cells hnot_mem ih =>
      have hcell :
          Tendsto (fun index => |error index cell|) l (nhds 0) :=
        (tendsto_zero_iff_abs_tendsto_zero _).1
          (herror cell (by simp [hnot_mem]))
      have hrest :
          Tendsto (fun index => ∑ other ∈ cells, |error index other|)
            l (nhds 0) :=
        ih (fun other hother => herror other (by simp [hother]))
      simpa [Finset.sum_insert, hnot_mem] using hcell.add hrest

theorem tendsto_scaled_sum_abs_cell_error_zero
    (cells : Finset Cell) (scale : Index -> Real)
    (error : Index -> Cell -> Real)
    (hscale_nonneg : ∀ index, 0 ≤ scale index)
    (herror :
      ∀ cell, cell ∈ cells ->
        Tendsto (fun index => scale index * error index cell)
          l (nhds 0)) :
    Tendsto
      (fun index => scale index * (∑ cell ∈ cells, |error index cell|))
      l (nhds 0) := by
  have hsum :
      Tendsto
        (fun index => ∑ cell ∈ cells, |scale index * error index cell|)
        l (nhds 0) :=
    tendsto_sum_abs_cell_error_zero cells
      (fun index cell => scale index * error index cell) herror
  convert hsum using 1
  ext index
  rw [Finset.mul_sum]
  exact Finset.sum_congr rfl
    (fun cell _ => by
      rw [abs_mul, abs_of_nonneg (hscale_nonneg index)])

variable {UnitA UnitB PropensityCell TreatedProgCell ControlProgCell PATTProgCell : Type*}
  [DecidableEq PropensityCell] [DecidableEq TreatedProgCell]
  [DecidableEq ControlProgCell] [DecidableEq PATTProgCell]

theorem tendsto_l1ScoreCellShareDistance_zero_of_cellwise
    [DecidableEq Cell]
    (cells : Finset Cell)
    (sampleA : Index -> Finset UnitA) (sampleB : Index -> Finset UnitB)
    (weightA : Index -> UnitA -> Real)
    (weightB : Index -> UnitB -> Real)
    (scoreA : Index -> UnitA -> Cell)
    (scoreB : Index -> UnitB -> Cell)
    (hcell :
      ∀ cell, cell ∈ cells ->
        Tendsto
          (fun index =>
            scoreCellShare (sampleA index) (weightA index)
                (scoreA index) cell -
              scoreCellShare (sampleB index) (weightB index)
                (scoreB index) cell)
          l (nhds 0)) :
    Tendsto
      (fun index =>
        l1ScoreCellShareDistance cells (sampleA index) (sampleB index)
          (weightA index) (weightB index) (scoreA index) (scoreB index))
      l (nhds 0) := by
  unfold l1ScoreCellShareDistance
  exact tendsto_sum_abs_cell_error_zero cells
    (fun index cell =>
      scoreCellShare (sampleA index) (weightA index) (scoreA index) cell -
        scoreCellShare (sampleB index) (weightB index) (scoreB index) cell)
    hcell

theorem tendsto_scaled_l1ScoreCellShareDistance_zero_of_cellwise
    [DecidableEq Cell]
    (cells : Finset Cell) (scale : Index -> Real)
    (sampleA : Index -> Finset UnitA) (sampleB : Index -> Finset UnitB)
    (weightA : Index -> UnitA -> Real)
    (weightB : Index -> UnitB -> Real)
    (scoreA : Index -> UnitA -> Cell)
    (scoreB : Index -> UnitB -> Cell)
    (hscale_nonneg : ∀ index, 0 ≤ scale index)
    (hcell :
      ∀ cell, cell ∈ cells ->
        Tendsto
          (fun index =>
            scale index *
              (scoreCellShare (sampleA index) (weightA index)
                  (scoreA index) cell -
                scoreCellShare (sampleB index) (weightB index)
                  (scoreB index) cell))
          l (nhds 0)) :
    Tendsto
      (fun index =>
        scale index *
          l1ScoreCellShareDistance cells (sampleA index) (sampleB index)
            (weightA index) (weightB index) (scoreA index) (scoreB index))
      l (nhds 0) := by
  unfold l1ScoreCellShareDistance
  exact tendsto_scaled_sum_abs_cell_error_zero cells scale
    (fun index cell =>
      scoreCellShare (sampleA index) (weightA index) (scoreA index) cell -
        scoreCellShare (sampleB index) (weightB index) (scoreB index) cell)
    hscale_nonneg hcell

/--
Scaled L1 share distance convergence from scaled cellwise convergence when the
scale is only eventually nonnegative.
-/
theorem tendsto_scaled_l1ScoreCellShareDistance_zero_of_eventually_nonneg_cellwise
    [DecidableEq Cell]
    (cells : Finset Cell) (scale : Index -> Real)
    (sampleA : Index -> Finset UnitA) (sampleB : Index -> Finset UnitB)
    (weightA : Index -> UnitA -> Real)
    (weightB : Index -> UnitB -> Real)
    (scoreA : Index -> UnitA -> Cell)
    (scoreB : Index -> UnitB -> Cell)
    (hscale_nonneg : ∀ᶠ index in l, 0 ≤ scale index)
    (hcell :
      ∀ cell, cell ∈ cells ->
        Tendsto
          (fun index =>
            scale index *
              (scoreCellShare (sampleA index) (weightA index)
                  (scoreA index) cell -
                scoreCellShare (sampleB index) (weightB index)
                  (scoreB index) cell))
          l (nhds 0)) :
    Tendsto
      (fun index =>
        scale index *
          l1ScoreCellShareDistance cells (sampleA index) (sampleB index)
            (weightA index) (weightB index) (scoreA index) (scoreB index))
      l (nhds 0) := by
  have hsum :
      Tendsto
        (fun index =>
          ∑ cell ∈ cells,
            |scale index *
              (scoreCellShare (sampleA index) (weightA index)
                (scoreA index) cell -
              scoreCellShare (sampleB index) (weightB index)
                (scoreB index) cell)|)
        l (nhds 0) :=
    tendsto_sum_abs_cell_error_zero cells
      (fun index cell =>
        scale index *
          (scoreCellShare (sampleA index) (weightA index)
            (scoreA index) cell -
          scoreCellShare (sampleB index) (weightB index)
            (scoreB index) cell))
      hcell
  have hEq :
      (fun index =>
        scale index *
          l1ScoreCellShareDistance cells (sampleA index) (sampleB index)
            (weightA index) (weightB index) (scoreA index) (scoreB index))
        =ᶠ[l] (fun index =>
          ∑ cell ∈ cells,
            |scale index *
              (scoreCellShare (sampleA index) (weightA index)
                (scoreA index) cell -
              scoreCellShare (sampleB index) (weightB index)
                (scoreB index) cell)|) := by
    filter_upwards [hscale_nonneg] with index hscale_nonneg'
    calc
      scale index *
          l1ScoreCellShareDistance cells (sampleA index) (sampleB index)
            (weightA index) (weightB index) (scoreA index) (scoreB index)
          =
          scale index * (∑ cell ∈ cells,
            |scoreCellShare (sampleA index) (weightA index)
              (scoreA index) cell -
            scoreCellShare (sampleB index) (weightB index)
              (scoreB index) cell|) := by
            simp [l1ScoreCellShareDistance]
      _ = ∑ cell ∈ cells,
            |scale index *
              (scoreCellShare (sampleA index) (weightA index)
                (scoreA index) cell -
              scoreCellShare (sampleB index) (weightB index)
                (scoreB index) cell)| := by
            simp [Finset.mul_sum, abs_mul, abs_of_nonneg hscale_nonneg']
  exact hsum.congr' hEq.symm

/--
Ordinary and scaled L1 score-cell share convergence from ordinary and scaled
cellwise share convergence.
-/
theorem tendsto_l1ScoreCellShareDistance_zero_and_scaled_zero_of_cellwise
    [DecidableEq Cell]
    (cells : Finset Cell) (scale : Index -> Real)
    (sampleA : Index -> Finset UnitA) (sampleB : Index -> Finset UnitB)
    (weightA : Index -> UnitA -> Real)
    (weightB : Index -> UnitB -> Real)
    (scoreA : Index -> UnitA -> Cell)
    (scoreB : Index -> UnitB -> Cell)
    (hscale_nonneg : ∀ index, 0 ≤ scale index)
    (hcell :
      ∀ cell, cell ∈ cells ->
        Tendsto
          (fun index =>
            scoreCellShare (sampleA index) (weightA index)
                (scoreA index) cell -
              scoreCellShare (sampleB index) (weightB index)
                (scoreB index) cell)
          l (nhds 0))
    (hscaledCell :
      ∀ cell, cell ∈ cells ->
        Tendsto
          (fun index =>
            scale index *
              (scoreCellShare (sampleA index) (weightA index)
                  (scoreA index) cell -
                scoreCellShare (sampleB index) (weightB index)
                  (scoreB index) cell))
          l (nhds 0)) :
    Tendsto
        (fun index =>
          l1ScoreCellShareDistance cells (sampleA index) (sampleB index)
            (weightA index) (weightB index) (scoreA index) (scoreB index))
        l (nhds 0) ∧
      Tendsto
        (fun index =>
          scale index *
            l1ScoreCellShareDistance cells (sampleA index) (sampleB index)
              (weightA index) (weightB index) (scoreA index) (scoreB index))
        l (nhds 0) := by
  constructor
  · exact
      tendsto_l1ScoreCellShareDistance_zero_of_cellwise
        cells sampleA sampleB weightA weightB scoreA scoreB hcell
  · exact
      tendsto_scaled_l1ScoreCellShareDistance_zero_of_cellwise
        cells scale sampleA sampleB weightA weightB scoreA scoreB
        hscale_nonneg hscaledCell

theorem tendsto_l1PATEDoubleScoreShareDistance_zero_of_cellwise
    (cells :
      Finset ((PropensityCell × TreatedProgCell) × ControlProgCell))
    (sampleA sampleB : Index -> Finset UnitA)
    (weightA weightB : Index -> UnitA -> Real)
    (propensityScore : Index -> UnitA -> PropensityCell)
    (treatedPrognosticScore : Index -> UnitA -> TreatedProgCell)
    (controlPrognosticScore : Index -> UnitA -> ControlProgCell)
    (hcell :
      ∀ cell, cell ∈ cells ->
        Tendsto
          (fun index =>
            scoreCellShare (sampleA index) (weightA index)
                (pateDoubleScore (propensityScore index)
                  (treatedPrognosticScore index)
                  (controlPrognosticScore index)) cell -
              scoreCellShare (sampleB index) (weightB index)
                (pateDoubleScore (propensityScore index)
                  (treatedPrognosticScore index)
                  (controlPrognosticScore index)) cell)
          l (nhds 0)) :
    Tendsto
      (fun index =>
        l1PATEDoubleScoreShareDistance cells (sampleA index) (sampleB index)
          (weightA index) (weightB index) (propensityScore index)
          (treatedPrognosticScore index) (controlPrognosticScore index))
      l (nhds 0) := by
  unfold l1PATEDoubleScoreShareDistance
  exact tendsto_l1ScoreCellShareDistance_zero_of_cellwise cells sampleA
    sampleB weightA weightB
    (fun index =>
      pateDoubleScore (propensityScore index) (treatedPrognosticScore index)
        (controlPrognosticScore index))
    (fun index =>
      pateDoubleScore (propensityScore index) (treatedPrognosticScore index)
        (controlPrognosticScore index))
    hcell

theorem tendsto_scaled_l1PATEDoubleScoreShareDistance_zero_of_cellwise
    (cells :
      Finset ((PropensityCell × TreatedProgCell) × ControlProgCell))
    (scale : Index -> Real)
    (sampleA sampleB : Index -> Finset UnitA)
    (weightA weightB : Index -> UnitA -> Real)
    (propensityScore : Index -> UnitA -> PropensityCell)
    (treatedPrognosticScore : Index -> UnitA -> TreatedProgCell)
    (controlPrognosticScore : Index -> UnitA -> ControlProgCell)
    (hscale_nonneg : ∀ index, 0 ≤ scale index)
    (hcell :
      ∀ cell, cell ∈ cells ->
        Tendsto
          (fun index =>
            scale index *
              (scoreCellShare (sampleA index) (weightA index)
                  (pateDoubleScore (propensityScore index)
                    (treatedPrognosticScore index)
                    (controlPrognosticScore index)) cell -
                scoreCellShare (sampleB index) (weightB index)
                  (pateDoubleScore (propensityScore index)
                    (treatedPrognosticScore index)
                    (controlPrognosticScore index)) cell))
          l (nhds 0)) :
    Tendsto
      (fun index =>
        scale index *
          l1PATEDoubleScoreShareDistance cells (sampleA index)
            (sampleB index) (weightA index) (weightB index)
            (propensityScore index) (treatedPrognosticScore index)
            (controlPrognosticScore index))
      l (nhds 0) := by
  unfold l1PATEDoubleScoreShareDistance
  exact tendsto_scaled_l1ScoreCellShareDistance_zero_of_cellwise cells scale
    sampleA sampleB weightA weightB
    (fun index =>
      pateDoubleScore (propensityScore index) (treatedPrognosticScore index)
        (controlPrognosticScore index))
    (fun index =>
      pateDoubleScore (propensityScore index) (treatedPrognosticScore index)
        (controlPrognosticScore index))
    hscale_nonneg hcell

/--
Ordinary and scaled PATE double-score L1 share convergence from ordinary and
scaled cellwise share convergence.
-/
theorem tendsto_l1PATEDoubleScoreShareDistance_zero_and_scaled_zero_of_cellwise
    (cells :
      Finset ((PropensityCell × TreatedProgCell) × ControlProgCell))
    (scale : Index -> Real)
    (sampleA sampleB : Index -> Finset UnitA)
    (weightA weightB : Index -> UnitA -> Real)
    (propensityScore : Index -> UnitA -> PropensityCell)
    (treatedPrognosticScore : Index -> UnitA -> TreatedProgCell)
    (controlPrognosticScore : Index -> UnitA -> ControlProgCell)
    (hscale_nonneg : ∀ index, 0 ≤ scale index)
    (hcell :
      ∀ cell, cell ∈ cells ->
        Tendsto
          (fun index =>
            scoreCellShare (sampleA index) (weightA index)
                (pateDoubleScore (propensityScore index)
                  (treatedPrognosticScore index)
                  (controlPrognosticScore index)) cell -
              scoreCellShare (sampleB index) (weightB index)
                (pateDoubleScore (propensityScore index)
                  (treatedPrognosticScore index)
                  (controlPrognosticScore index)) cell)
          l (nhds 0))
    (hscaledCell :
      ∀ cell, cell ∈ cells ->
        Tendsto
          (fun index =>
            scale index *
              (scoreCellShare (sampleA index) (weightA index)
                  (pateDoubleScore (propensityScore index)
                    (treatedPrognosticScore index)
                    (controlPrognosticScore index)) cell -
                scoreCellShare (sampleB index) (weightB index)
                  (pateDoubleScore (propensityScore index)
                    (treatedPrognosticScore index)
                    (controlPrognosticScore index)) cell))
          l (nhds 0)) :
    Tendsto
        (fun index =>
          l1PATEDoubleScoreShareDistance cells (sampleA index) (sampleB index)
            (weightA index) (weightB index) (propensityScore index)
            (treatedPrognosticScore index) (controlPrognosticScore index))
        l (nhds 0) ∧
      Tendsto
        (fun index =>
          scale index *
            l1PATEDoubleScoreShareDistance cells (sampleA index)
              (sampleB index) (weightA index) (weightB index)
              (propensityScore index) (treatedPrognosticScore index)
              (controlPrognosticScore index))
        l (nhds 0) := by
  constructor
  · exact
      tendsto_l1PATEDoubleScoreShareDistance_zero_of_cellwise
        cells sampleA sampleB weightA weightB propensityScore
        treatedPrognosticScore controlPrognosticScore hcell
  · exact
      tendsto_scaled_l1PATEDoubleScoreShareDistance_zero_of_cellwise
        cells scale sampleA sampleB weightA weightB propensityScore
        treatedPrognosticScore controlPrognosticScore hscale_nonneg
        hscaledCell

theorem tendsto_l1PATTDoubleScoreShareDistance_zero_of_cellwise
    (cells : Finset (PropensityCell × PATTProgCell))
    (sampleA sampleB : Index -> Finset UnitA)
    (weightA weightB : Index -> UnitA -> Real)
    (propensityScore : Index -> UnitA -> PropensityCell)
    (controlPrognosticScore : Index -> UnitA -> PATTProgCell)
    (hcell :
      ∀ cell, cell ∈ cells ->
        Tendsto
          (fun index =>
            scoreCellShare (sampleA index) (weightA index)
                (pattDoubleScore (propensityScore index)
                  (controlPrognosticScore index)) cell -
              scoreCellShare (sampleB index) (weightB index)
                (pattDoubleScore (propensityScore index)
                  (controlPrognosticScore index)) cell)
          l (nhds 0)) :
    Tendsto
      (fun index =>
        l1PATTDoubleScoreShareDistance cells (sampleA index) (sampleB index)
          (weightA index) (weightB index) (propensityScore index)
          (controlPrognosticScore index))
      l (nhds 0) := by
  unfold l1PATTDoubleScoreShareDistance
  exact tendsto_l1ScoreCellShareDistance_zero_of_cellwise cells sampleA
    sampleB weightA weightB
    (fun index =>
      pattDoubleScore (propensityScore index) (controlPrognosticScore index))
    (fun index =>
      pattDoubleScore (propensityScore index) (controlPrognosticScore index))
    hcell

theorem tendsto_scaled_l1PATTDoubleScoreShareDistance_zero_of_cellwise
    (cells : Finset (PropensityCell × PATTProgCell))
    (scale : Index -> Real)
    (sampleA sampleB : Index -> Finset UnitA)
    (weightA weightB : Index -> UnitA -> Real)
    (propensityScore : Index -> UnitA -> PropensityCell)
    (controlPrognosticScore : Index -> UnitA -> PATTProgCell)
    (hscale_nonneg : ∀ index, 0 ≤ scale index)
    (hcell :
      ∀ cell, cell ∈ cells ->
        Tendsto
          (fun index =>
            scale index *
              (scoreCellShare (sampleA index) (weightA index)
                  (pattDoubleScore (propensityScore index)
                    (controlPrognosticScore index)) cell -
                scoreCellShare (sampleB index) (weightB index)
                  (pattDoubleScore (propensityScore index)
                    (controlPrognosticScore index)) cell))
          l (nhds 0)) :
    Tendsto
      (fun index =>
        scale index *
          l1PATTDoubleScoreShareDistance cells (sampleA index)
            (sampleB index) (weightA index) (weightB index)
            (propensityScore index) (controlPrognosticScore index))
      l (nhds 0) := by
  unfold l1PATTDoubleScoreShareDistance
  exact tendsto_scaled_l1ScoreCellShareDistance_zero_of_cellwise cells scale
    sampleA sampleB weightA weightB
    (fun index =>
      pattDoubleScore (propensityScore index) (controlPrognosticScore index))
    (fun index =>
      pattDoubleScore (propensityScore index) (controlPrognosticScore index))
    hscale_nonneg hcell

/--
Ordinary and scaled PATT double-score L1 share convergence from ordinary and
scaled cellwise share convergence.
-/
theorem tendsto_l1PATTDoubleScoreShareDistance_zero_and_scaled_zero_of_cellwise
    (cells : Finset (PropensityCell × PATTProgCell))
    (scale : Index -> Real)
    (sampleA sampleB : Index -> Finset UnitA)
    (weightA weightB : Index -> UnitA -> Real)
    (propensityScore : Index -> UnitA -> PropensityCell)
    (controlPrognosticScore : Index -> UnitA -> PATTProgCell)
    (hscale_nonneg : ∀ index, 0 ≤ scale index)
    (hcell :
      ∀ cell, cell ∈ cells ->
        Tendsto
          (fun index =>
            scoreCellShare (sampleA index) (weightA index)
                (pattDoubleScore (propensityScore index)
                  (controlPrognosticScore index)) cell -
              scoreCellShare (sampleB index) (weightB index)
                (pattDoubleScore (propensityScore index)
                  (controlPrognosticScore index)) cell)
          l (nhds 0))
    (hscaledCell :
      ∀ cell, cell ∈ cells ->
        Tendsto
          (fun index =>
            scale index *
              (scoreCellShare (sampleA index) (weightA index)
                  (pattDoubleScore (propensityScore index)
                    (controlPrognosticScore index)) cell -
                scoreCellShare (sampleB index) (weightB index)
                  (pattDoubleScore (propensityScore index)
                    (controlPrognosticScore index)) cell))
          l (nhds 0)) :
    Tendsto
        (fun index =>
          l1PATTDoubleScoreShareDistance cells (sampleA index) (sampleB index)
            (weightA index) (weightB index) (propensityScore index)
            (controlPrognosticScore index))
        l (nhds 0) ∧
      Tendsto
        (fun index =>
          scale index *
            l1PATTDoubleScoreShareDistance cells (sampleA index)
              (sampleB index) (weightA index) (weightB index)
              (propensityScore index) (controlPrognosticScore index))
        l (nhds 0) := by
  constructor
  · exact
      tendsto_l1PATTDoubleScoreShareDistance_zero_of_cellwise
        cells sampleA sampleB weightA weightB propensityScore
        controlPrognosticScore hcell
  · exact
      tendsto_scaled_l1PATTDoubleScoreShareDistance_zero_of_cellwise
        cells scale sampleA sampleB weightA weightB propensityScore
        controlPrognosticScore hscale_nonneg hscaledCell

/--
Paired PATE/PATT ordinary and scaled double-score L1 share convergence from
cellwise share convergence for the respective finite score partitions.
-/
theorem tendsto_l1PATE_PATTDoubleScoreShareDistance_zero_and_scaled_zero_of_cellwise
    (pateCells :
      Finset ((PropensityCell × TreatedProgCell) × ControlProgCell))
    (pattCells : Finset (PropensityCell × PATTProgCell))
    (scale : Index -> Real)
    (sampleA sampleB : Index -> Finset UnitA)
    (weightA weightB : Index -> UnitA -> Real)
    (propensityScore : Index -> UnitA -> PropensityCell)
    (treatedPrognosticScore : Index -> UnitA -> TreatedProgCell)
    (controlPrognosticScore : Index -> UnitA -> ControlProgCell)
    (pattPrognosticScore : Index -> UnitA -> PATTProgCell)
    (hscale_nonneg : ∀ index, 0 ≤ scale index)
    (hpateCell :
      ∀ cell, cell ∈ pateCells ->
        Tendsto
          (fun index =>
            scoreCellShare (sampleA index) (weightA index)
                (pateDoubleScore (propensityScore index)
                  (treatedPrognosticScore index)
                  (controlPrognosticScore index)) cell -
              scoreCellShare (sampleB index) (weightB index)
                (pateDoubleScore (propensityScore index)
                  (treatedPrognosticScore index)
                  (controlPrognosticScore index)) cell)
          l (nhds 0))
    (hpateScaledCell :
      ∀ cell, cell ∈ pateCells ->
        Tendsto
          (fun index =>
            scale index *
              (scoreCellShare (sampleA index) (weightA index)
                  (pateDoubleScore (propensityScore index)
                    (treatedPrognosticScore index)
                    (controlPrognosticScore index)) cell -
                scoreCellShare (sampleB index) (weightB index)
                  (pateDoubleScore (propensityScore index)
                    (treatedPrognosticScore index)
                    (controlPrognosticScore index)) cell))
          l (nhds 0))
    (hpattCell :
      ∀ cell, cell ∈ pattCells ->
        Tendsto
          (fun index =>
            scoreCellShare (sampleA index) (weightA index)
                (pattDoubleScore (propensityScore index)
                  (pattPrognosticScore index)) cell -
              scoreCellShare (sampleB index) (weightB index)
                (pattDoubleScore (propensityScore index)
                  (pattPrognosticScore index)) cell)
          l (nhds 0))
    (hpattScaledCell :
      ∀ cell, cell ∈ pattCells ->
        Tendsto
          (fun index =>
            scale index *
              (scoreCellShare (sampleA index) (weightA index)
                  (pattDoubleScore (propensityScore index)
                    (pattPrognosticScore index)) cell -
                scoreCellShare (sampleB index) (weightB index)
                  (pattDoubleScore (propensityScore index)
                    (pattPrognosticScore index)) cell))
          l (nhds 0)) :
    (Tendsto
        (fun index =>
          l1PATEDoubleScoreShareDistance pateCells (sampleA index)
            (sampleB index) (weightA index) (weightB index)
            (propensityScore index) (treatedPrognosticScore index)
            (controlPrognosticScore index))
        l (nhds 0) ∧
      Tendsto
        (fun index =>
          scale index *
            l1PATEDoubleScoreShareDistance pateCells (sampleA index)
              (sampleB index) (weightA index) (weightB index)
              (propensityScore index) (treatedPrognosticScore index)
              (controlPrognosticScore index))
        l (nhds 0)) ∧
      (Tendsto
        (fun index =>
          l1PATTDoubleScoreShareDistance pattCells (sampleA index)
            (sampleB index) (weightA index) (weightB index)
            (propensityScore index) (pattPrognosticScore index))
        l (nhds 0) ∧
      Tendsto
        (fun index =>
          scale index *
            l1PATTDoubleScoreShareDistance pattCells (sampleA index)
              (sampleB index) (weightA index) (weightB index)
              (propensityScore index) (pattPrognosticScore index))
        l (nhds 0)) := by
  constructor
  · exact
      tendsto_l1PATEDoubleScoreShareDistance_zero_and_scaled_zero_of_cellwise
        pateCells scale sampleA sampleB weightA weightB propensityScore
        treatedPrognosticScore controlPrognosticScore hscale_nonneg
        hpateCell hpateScaledCell
  · exact
      tendsto_l1PATTDoubleScoreShareDistance_zero_and_scaled_zero_of_cellwise
        pattCells scale sampleA sampleB weightA weightB propensityScore
        pattPrognosticScore hscale_nonneg hpattCell hpattScaledCell

end WDSM
end Matching
end StatInference
