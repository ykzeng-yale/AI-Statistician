import StatInference.Matching.WDSM.FiniteCellMassConvergence
import StatInference.Matching.WDSM.FiniteCellIndicatorLLNFromMass
import Mathlib.Tactic.Ring

/-!
# Finite score-cell moment convergence

This module turns cellwise score-cell mass convergence into convergence of
fixed finite cell moments.  It is a deterministic topological step toward the
Chen-Han geometry gap: once stochastic geometry supplies cell masses, any
fixed finite loading of those cells has a checked limit.
-/

namespace StatInference
namespace Matching
namespace WDSM

open Filter
open scoped BigOperators

variable {Index UnitA UnitB Cell : Type*} {l : Filter Index}
  [DecidableEq Cell]

/-- Fixed finite loading moment of score-cell masses. -/
noncomputable def weightedScoreCellMoment
    (cells : Finset Cell)
    (sample : Finset UnitA)
    (weight : UnitA -> Real)
    (score : UnitA -> Cell)
    (loading : Cell -> Real) : Real :=
  ∑ cell ∈ cells, loading cell * scoreCellMass sample weight score cell

/-- Limiting finite loading moment for score-cell mass limits. -/
noncomputable def weightedScoreCellMomentLimit
    (cells : Finset Cell)
    (loading massLimit : Cell -> Real) : Real :=
  ∑ cell ∈ cells, loading cell * massLimit cell

/--
Cellwise score-cell mass convergence implies convergence of any fixed finite
cell loading moment.
-/
theorem tendsto_weightedScoreCellMoment_of_cellwiseScoreCellMassLLN
    (cells : Finset Cell)
    (sample : Index -> Finset UnitA)
    (weight : Index -> UnitA -> Real)
    (score : Index -> UnitA -> Cell)
    (loading massLimit : Cell -> Real)
    (hmass :
      cellwiseScoreCellMassLLN (l := l) cells sample weight score massLimit) :
    Tendsto
      (fun index =>
        weightedScoreCellMoment cells (sample index) (weight index)
          (score index) loading)
      l (nhds (weightedScoreCellMomentLimit cells loading massLimit)) := by
  unfold weightedScoreCellMoment weightedScoreCellMomentLimit
  exact tendsto_sum_cell_values cells
    (fun index cell =>
      loading cell *
        scoreCellMass (sample index) (weight index) (score index) cell)
    (fun cell => loading cell * massLimit cell)
    (fun cell hcell => by
      exact
        (tendsto_const_nhds :
          Tendsto (fun _index : Index => loading cell) l
            (nhds (loading cell))).mul
          (hmass cell hcell))

/--
Two cell-mass arrays with the same cellwise limits have the same fixed finite
loading-moment limit.
-/
theorem tendsto_weightedScoreCellMoment_sub_zero_of_common_cellwise_limits
    (cells : Finset Cell)
    (sampleA : Index -> Finset UnitA) (sampleB : Index -> Finset UnitB)
    (weightA : Index -> UnitA -> Real)
    (weightB : Index -> UnitB -> Real)
    (scoreA : Index -> UnitA -> Cell)
    (scoreB : Index -> UnitB -> Cell)
    (loading massLimit : Cell -> Real)
    (hmassA :
      cellwiseScoreCellMassLLN (l := l) cells sampleA weightA scoreA
        massLimit)
    (hmassB :
      cellwiseScoreCellMassLLN (l := l) cells sampleB weightB scoreB
        massLimit) :
    Tendsto
      (fun index =>
        weightedScoreCellMoment cells (sampleA index) (weightA index)
            (scoreA index) loading -
          weightedScoreCellMoment cells (sampleB index) (weightB index)
            (scoreB index) loading)
      l (nhds 0) := by
  have hA :=
    tendsto_weightedScoreCellMoment_of_cellwiseScoreCellMassLLN
      cells sampleA weightA scoreA loading massLimit hmassA
  have hB :=
    tendsto_weightedScoreCellMoment_of_cellwiseScoreCellMassLLN
      cells sampleB weightB scoreB loading massLimit hmassB
  simpa using hA.sub hB

/--
Scaled cellwise mass differences imply scaled convergence of any fixed finite
cell loading-moment difference.
-/
theorem tendsto_scaled_weightedScoreCellMoment_sub_zero_of_cellwise
    (cells : Finset Cell) (scale : Index -> Real)
    (sampleA : Index -> Finset UnitA) (sampleB : Index -> Finset UnitB)
    (weightA : Index -> UnitA -> Real)
    (weightB : Index -> UnitB -> Real)
    (scoreA : Index -> UnitA -> Cell)
    (scoreB : Index -> UnitB -> Cell)
    (loading : Cell -> Real)
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
          (weightedScoreCellMoment cells (sampleA index) (weightA index)
              (scoreA index) loading -
            weightedScoreCellMoment cells (sampleB index) (weightB index)
              (scoreB index) loading))
      l (nhds 0) := by
  have hsum :
      Tendsto
        (fun index =>
          ∑ cell ∈ cells,
            loading cell *
              (scale index *
                (scoreCellMass (sampleA index) (weightA index)
                    (scoreA index) cell -
                  scoreCellMass (sampleB index) (weightB index)
                    (scoreB index) cell)))
        l (nhds 0) :=
    tendsto_sum_cell_values_zero cells
      (fun index cell =>
        loading cell *
          (scale index *
            (scoreCellMass (sampleA index) (weightA index)
                (scoreA index) cell -
              scoreCellMass (sampleB index) (weightB index)
                (scoreB index) cell)))
      (fun cell hcell =>
        by
          simpa using
            (tendsto_const_nhds :
              Tendsto (fun _index : Index => loading cell) l
                (nhds (loading cell))).mul
              (hscaledMass cell hcell))
  convert hsum using 1
  ext index
  unfold weightedScoreCellMoment
  calc
    scale index *
        ((∑ cell ∈ cells,
            loading cell *
              scoreCellMass (sampleA index) (weightA index)
                (scoreA index) cell) -
          (∑ cell ∈ cells,
            loading cell *
              scoreCellMass (sampleB index) (weightB index)
                (scoreB index) cell))
        =
        ∑ cell ∈ cells,
          scale index *
            (loading cell *
              scoreCellMass (sampleA index) (weightA index)
                (scoreA index) cell -
            loading cell *
              scoreCellMass (sampleB index) (weightB index)
                (scoreB index) cell) := by
          rw [← Finset.sum_sub_distrib, Finset.mul_sum]
    _ =
        ∑ cell ∈ cells,
          loading cell *
            (scale index *
              (scoreCellMass (sampleA index) (weightA index)
                  (scoreA index) cell -
                scoreCellMass (sampleB index) (weightB index)
                  (scoreB index) cell)) := by
          exact Finset.sum_congr rfl
            (fun cell _hcell => by ring)

end WDSM
end Matching
end StatInference
