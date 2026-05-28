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

end WDSM
end Matching
end StatInference
