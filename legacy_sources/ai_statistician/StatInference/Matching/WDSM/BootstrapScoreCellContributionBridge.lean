import Mathlib.Data.Finset.Basic
import Mathlib.Topology.Basic
import StatInference.Matching.WDSM.BootstrapLinearizedReplicate
import StatInference.Matching.WDSM.BootstrapFiniteCellConsistencyBridge
import StatInference.Matching.WDSM.ProspectiveBootstrapVariance

/-!
# Bootstrap score-cell contribution bridge

This module supplies deterministic score-cell contribution adapters for the
linearized WDSM bootstrap.  The finite-cell bootstrap variance bridge can now
consume score-cell contribution limits directly; this file proves that those
limits follow from component-level score-cell representations and component
limits for the PATE and PATT bootstrap influence layouts.
-/

namespace StatInference
namespace Matching
namespace WDSM

open Filter

variable {Index Unit Cell : Type*} {l : Filter Index}

/-- Score-cell version of the PATE bootstrap influence contribution. -/
noncomputable def pateBootstrapScoreCellContribution
    (cellBaseWeight cellReuseResidualWeight cellHeterogeneity cellResidual :
      Cell -> Real)
    (cell : Cell) : Real :=
  cellBaseWeight cell * cellHeterogeneity cell +
    cellReuseResidualWeight cell * cellResidual cell

/-- Score-cell version of the PATT bootstrap influence contribution. -/
noncomputable def pattBootstrapScoreCellContribution
    (cellTreatedContribution cellControlReuseContribution : Cell -> Real)
    (cell : Cell) : Real :=
  cellTreatedContribution cell - cellControlReuseContribution cell

/--
PATE score-cell component representations imply a score-cell representation
of the PATE bootstrap influence contribution.
-/
theorem retrospective_pate_bootstrap_cellContribution_eq_of_score_components
    (sample : Index -> Finset Unit)
    (score : Index -> Unit -> Cell)
    (baseWeight reuseResidualWeight heterogeneity residual :
      Index -> Unit -> Real)
    (cellBaseWeight cellReuseResidualWeight cellHeterogeneity cellResidual :
      Index -> Cell -> Real)
    (hbase :
      ∀ index unit, unit ∈ sample index ->
        cellBaseWeight index (score index unit) = baseWeight index unit)
    (hreuse :
      ∀ index unit, unit ∈ sample index ->
        cellReuseResidualWeight index (score index unit) =
          reuseResidualWeight index unit)
    (hheterogeneity :
      ∀ index unit, unit ∈ sample index ->
        cellHeterogeneity index (score index unit) = heterogeneity index unit)
    (hresidual :
      ∀ index unit, unit ∈ sample index ->
        cellResidual index (score index unit) = residual index unit) :
    ∀ index unit, unit ∈ sample index ->
      pateBootstrapScoreCellContribution
          (cellBaseWeight index) (cellReuseResidualWeight index)
          (cellHeterogeneity index) (cellResidual index)
          (score index unit) =
        retrospectivePATEBootstrapInfluenceContribution
          (baseWeight index) (reuseResidualWeight index)
          (heterogeneity index) (residual index) unit :=
  fun index unit hunit => by
    unfold pateBootstrapScoreCellContribution
      retrospectivePATEBootstrapInfluenceContribution
    rw [hbase index unit hunit, hreuse index unit hunit,
      hheterogeneity index unit hunit, hresidual index unit hunit]

/--
Prospective PATE has the same score-cell influence adapter as retrospective
PATE, with the prospective influence definition.
-/
theorem prospective_pate_bootstrap_cellContribution_eq_of_score_components
    (sample : Index -> Finset Unit)
    (score : Index -> Unit -> Cell)
    (baseWeight reuseResidualWeight heterogeneity residual :
      Index -> Unit -> Real)
    (cellBaseWeight cellReuseResidualWeight cellHeterogeneity cellResidual :
      Index -> Cell -> Real)
    (hbase :
      ∀ index unit, unit ∈ sample index ->
        cellBaseWeight index (score index unit) = baseWeight index unit)
    (hreuse :
      ∀ index unit, unit ∈ sample index ->
        cellReuseResidualWeight index (score index unit) =
          reuseResidualWeight index unit)
    (hheterogeneity :
      ∀ index unit, unit ∈ sample index ->
        cellHeterogeneity index (score index unit) = heterogeneity index unit)
    (hresidual :
      ∀ index unit, unit ∈ sample index ->
        cellResidual index (score index unit) = residual index unit) :
    ∀ index unit, unit ∈ sample index ->
      pateBootstrapScoreCellContribution
          (cellBaseWeight index) (cellReuseResidualWeight index)
          (cellHeterogeneity index) (cellResidual index)
          (score index unit) =
        prospectivePATEBootstrapInfluenceContribution
          (baseWeight index) (reuseResidualWeight index)
          (heterogeneity index) (residual index) unit :=
  fun index unit hunit => by
    unfold pateBootstrapScoreCellContribution
      prospectivePATEBootstrapInfluenceContribution
    rw [hbase index unit hunit, hreuse index unit hunit,
      hheterogeneity index unit hunit, hresidual index unit hunit]

/--
PATT score-cell component representations imply a score-cell representation
of the retrospective PATT bootstrap influence contribution.
-/
theorem retrospective_patt_bootstrap_cellContribution_eq_of_score_components
    (sample : Index -> Finset Unit)
    (score : Index -> Unit -> Cell)
    (treatedContribution controlReuseContribution : Index -> Unit -> Real)
    (cellTreatedContribution cellControlReuseContribution :
      Index -> Cell -> Real)
    (htreated :
      ∀ index unit, unit ∈ sample index ->
        cellTreatedContribution index (score index unit) =
          treatedContribution index unit)
    (hcontrol :
      ∀ index unit, unit ∈ sample index ->
        cellControlReuseContribution index (score index unit) =
          controlReuseContribution index unit) :
    ∀ index unit, unit ∈ sample index ->
      pattBootstrapScoreCellContribution
          (cellTreatedContribution index)
          (cellControlReuseContribution index)
          (score index unit) =
        retrospectivePATTBootstrapInfluenceContribution
          (treatedContribution index) (controlReuseContribution index) unit :=
  fun index unit hunit => by
    unfold pattBootstrapScoreCellContribution
      retrospectivePATTBootstrapInfluenceContribution
    rw [htreated index unit hunit, hcontrol index unit hunit]

/--
Prospective PATT has the same score-cell influence adapter as retrospective
PATT, with the prospective influence definition.
-/
theorem prospective_patt_bootstrap_cellContribution_eq_of_score_components
    (sample : Index -> Finset Unit)
    (score : Index -> Unit -> Cell)
    (treatedContribution controlReuseContribution : Index -> Unit -> Real)
    (cellTreatedContribution cellControlReuseContribution :
      Index -> Cell -> Real)
    (htreated :
      ∀ index unit, unit ∈ sample index ->
        cellTreatedContribution index (score index unit) =
          treatedContribution index unit)
    (hcontrol :
      ∀ index unit, unit ∈ sample index ->
        cellControlReuseContribution index (score index unit) =
          controlReuseContribution index unit) :
    ∀ index unit, unit ∈ sample index ->
      pattBootstrapScoreCellContribution
          (cellTreatedContribution index)
          (cellControlReuseContribution index)
          (score index unit) =
        prospectivePATTBootstrapInfluenceContribution
          (treatedContribution index) (controlReuseContribution index) unit :=
  fun index unit hunit => by
    unfold pattBootstrapScoreCellContribution
      prospectivePATTBootstrapInfluenceContribution
    rw [htreated index unit hunit, hcontrol index unit hunit]

/--
Cellwise convergence of PATE bootstrap influence components implies
cellwise convergence of the PATE score-cell contribution.
-/
theorem tendsto_pateBootstrapScoreCellContribution_of_component_limits
    (cells : Finset Cell)
    (cellBaseWeight cellReuseResidualWeight cellHeterogeneity cellResidual :
      Index -> Cell -> Real)
    (baseWeightLimit reuseResidualWeightLimit heterogeneityLimit
      residualLimit : Cell -> Real)
    (hbase :
      ∀ cell, cell ∈ cells ->
        Tendsto (fun index => cellBaseWeight index cell)
          l (nhds (baseWeightLimit cell)))
    (hreuse :
      ∀ cell, cell ∈ cells ->
        Tendsto (fun index => cellReuseResidualWeight index cell)
          l (nhds (reuseResidualWeightLimit cell)))
    (hheterogeneity :
      ∀ cell, cell ∈ cells ->
        Tendsto (fun index => cellHeterogeneity index cell)
          l (nhds (heterogeneityLimit cell)))
    (hresidual :
      ∀ cell, cell ∈ cells ->
        Tendsto (fun index => cellResidual index cell)
          l (nhds (residualLimit cell))) :
    ∀ cell, cell ∈ cells ->
      Tendsto
        (fun index =>
          pateBootstrapScoreCellContribution
            (cellBaseWeight index) (cellReuseResidualWeight index)
            (cellHeterogeneity index) (cellResidual index) cell)
        l
        (nhds
          (pateBootstrapScoreCellContribution baseWeightLimit
            reuseResidualWeightLimit heterogeneityLimit residualLimit cell)) :=
  fun cell hcell => by
    unfold pateBootstrapScoreCellContribution
    exact
      ((hbase cell hcell).mul (hheterogeneity cell hcell)).add
        ((hreuse cell hcell).mul (hresidual cell hcell))

/--
Cellwise convergence of PATT bootstrap influence components implies
cellwise convergence of the PATT score-cell contribution.
-/
theorem tendsto_pattBootstrapScoreCellContribution_of_component_limits
    (cells : Finset Cell)
    (cellTreatedContribution cellControlReuseContribution :
      Index -> Cell -> Real)
    (treatedContributionLimit controlReuseContributionLimit : Cell -> Real)
    (htreated :
      ∀ cell, cell ∈ cells ->
        Tendsto (fun index => cellTreatedContribution index cell)
          l (nhds (treatedContributionLimit cell)))
    (hcontrol :
      ∀ cell, cell ∈ cells ->
        Tendsto (fun index => cellControlReuseContribution index cell)
          l (nhds (controlReuseContributionLimit cell))) :
    ∀ cell, cell ∈ cells ->
      Tendsto
        (fun index =>
          pattBootstrapScoreCellContribution
            (cellTreatedContribution index)
            (cellControlReuseContribution index) cell)
        l
        (nhds
          (pattBootstrapScoreCellContribution treatedContributionLimit
            controlReuseContributionLimit cell)) :=
  fun cell hcell => by
    unfold pattBootstrapScoreCellContribution
    exact (htreated cell hcell).sub (hcontrol cell hcell)

end WDSM
end Matching
end StatInference
