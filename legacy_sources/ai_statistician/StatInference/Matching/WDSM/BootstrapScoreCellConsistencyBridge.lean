import Mathlib.Data.Finset.Basic
import Mathlib.Topology.Basic
import StatInference.Matching.WDSM.BootstrapScoreCellContributionBridge

/-!
# Bootstrap score-cell consistency bridge

This module composes the score-cell contribution adapters with the finite-cell
bootstrap variance-consistency bridge.  Scenario-level bootstrap consistency
can now be supplied from component-level score-cell representations, component
limits, denominator-weight limits, and score-cell mass convergence.
-/

namespace StatInference
namespace Matching
namespace WDSM

open Filter

variable {Index Unit Cell : Type*} {l : Filter Index} [DecidableEq Cell]

/--
Retrospective PATE bootstrap consistency from component-level score-cell
representations and limits.
-/
theorem retrospective_pate_bootstrap_variance_consistency_of_score_cell_components_direct
    (cells : Finset Cell)
    (sample : Index -> Finset Unit)
    (multiplier baseWeight reuseResidualWeight heterogeneity residual :
      Index -> Unit -> Real)
    (score : Index -> Unit -> Cell)
    (target denominator normalizer : Real)
    (cellBaseWeight cellReuseResidualWeight cellHeterogeneity cellResidual :
      Index -> Cell -> Real)
    (baseWeightLimit reuseResidualWeightLimit heterogeneityLimit
      residualLimit massLimit : Cell -> Real)
    (multiplierWeightRegular bootstrapScoreReplicationConsistent
      bootstrapBiasCorrectionConsistent bootstrapVarianceConsistent : Prop)
    (bridge :
      (∀ index,
        retrospectivePATEBootstrapFiniteAlgebraVerified (sample index)
          (multiplier index) (baseWeight index)
          (reuseResidualWeight index) (heterogeneity index)
          (residual index)) ->
        multiplierWeightRegular ->
        bootstrapScoreReplicationConsistent ->
        bootstrapBiasCorrectionConsistent ->
        Tendsto
          (fun index =>
            bootstrapCenteredVarianceTarget (sample index)
              (retrospectivePATEBootstrapInfluenceContribution
                (baseWeight index) (reuseResidualWeight index)
                (heterogeneity index) (residual index))
              (baseWeight index) target denominator normalizer)
          l
          (nhds
            ((1 / denominator ^ 2) * (1 / normalizer) *
              weightedScoreCellMomentLimit cells
                (fun cell =>
                  (pateBootstrapScoreCellContribution baseWeightLimit
                        reuseResidualWeightLimit heterogeneityLimit
                        residualLimit cell -
                      target * baseWeightLimit cell) ^ 2)
                massLimit)) ->
        bootstrapVarianceConsistent)
    (hcover :
      ∀ index unit, unit ∈ sample index -> score index unit ∈ cells)
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
        cellResidual index (score index unit) = residual index unit)
    (hbaseLimit :
      ∀ cell, cell ∈ cells ->
        Tendsto (fun index => cellBaseWeight index cell)
          l (nhds (baseWeightLimit cell)))
    (hreuseLimit :
      ∀ cell, cell ∈ cells ->
        Tendsto (fun index => cellReuseResidualWeight index cell)
          l (nhds (reuseResidualWeightLimit cell)))
    (hheterogeneityLimit :
      ∀ cell, cell ∈ cells ->
        Tendsto (fun index => cellHeterogeneity index cell)
          l (nhds (heterogeneityLimit cell)))
    (hresidualLimit :
      ∀ cell, cell ∈ cells ->
        Tendsto (fun index => cellResidual index cell)
          l (nhds (residualLimit cell)))
    (hmass :
      cellwiseScoreCellMassLLN (l := l) cells sample
        (fun _index _unit => 1) score massLimit)
    (hmultiplier : multiplierWeightRegular)
    (hscore : bootstrapScoreReplicationConsistent)
    (hbias : bootstrapBiasCorrectionConsistent) :
    bootstrapVarianceConsistent :=
  retrospective_pate_bootstrap_variance_consistency_of_indexed_cell_contribution_weight_limits_direct
    (l := l) cells sample multiplier baseWeight reuseResidualWeight
    heterogeneity residual score target denominator normalizer
    (fun index =>
      pateBootstrapScoreCellContribution (cellBaseWeight index)
        (cellReuseResidualWeight index) (cellHeterogeneity index)
        (cellResidual index))
    cellBaseWeight
    (pateBootstrapScoreCellContribution baseWeightLimit
      reuseResidualWeightLimit heterogeneityLimit residualLimit)
    baseWeightLimit massLimit multiplierWeightRegular
    bootstrapScoreReplicationConsistent bootstrapBiasCorrectionConsistent
    bootstrapVarianceConsistent bridge hcover
    (retrospective_pate_bootstrap_cellContribution_eq_of_score_components
      sample score baseWeight reuseResidualWeight heterogeneity residual
      cellBaseWeight cellReuseResidualWeight cellHeterogeneity cellResidual
      hbase hreuse hheterogeneity hresidual)
    hbase
    (tendsto_pateBootstrapScoreCellContribution_of_component_limits
      (l := l) cells cellBaseWeight cellReuseResidualWeight
      cellHeterogeneity cellResidual baseWeightLimit
      reuseResidualWeightLimit heterogeneityLimit residualLimit hbaseLimit
      hreuseLimit hheterogeneityLimit hresidualLimit)
    hbaseLimit hmass hmultiplier hscore hbias

/--
Prospective PATE bootstrap consistency from component-level score-cell
representations and limits.
-/
theorem prospective_pate_bootstrap_variance_consistency_of_score_cell_components_direct
    (cells : Finset Cell)
    (sample : Index -> Finset Unit)
    (multiplier baseWeight reuseResidualWeight heterogeneity residual :
      Index -> Unit -> Real)
    (score : Index -> Unit -> Cell)
    (target denominator normalizer : Real)
    (cellBaseWeight cellReuseResidualWeight cellHeterogeneity cellResidual :
      Index -> Cell -> Real)
    (baseWeightLimit reuseResidualWeightLimit heterogeneityLimit
      residualLimit massLimit : Cell -> Real)
    (multiplierWeightRegular bootstrapScoreReplicationConsistent
      bootstrapBiasCorrectionConsistent bootstrapVarianceConsistent : Prop)
    (bridge :
      (∀ index,
        prospectivePATEBootstrapFiniteAlgebraVerified (sample index)
          (multiplier index) (baseWeight index)
          (reuseResidualWeight index) (heterogeneity index)
          (residual index)) ->
        multiplierWeightRegular ->
        bootstrapScoreReplicationConsistent ->
        bootstrapBiasCorrectionConsistent ->
        Tendsto
          (fun index =>
            bootstrapCenteredVarianceTarget (sample index)
              (prospectivePATEBootstrapInfluenceContribution
                (baseWeight index) (reuseResidualWeight index)
                (heterogeneity index) (residual index))
              (baseWeight index) target denominator normalizer)
          l
          (nhds
            ((1 / denominator ^ 2) * (1 / normalizer) *
              weightedScoreCellMomentLimit cells
                (fun cell =>
                  (pateBootstrapScoreCellContribution baseWeightLimit
                        reuseResidualWeightLimit heterogeneityLimit
                        residualLimit cell -
                      target * baseWeightLimit cell) ^ 2)
                massLimit)) ->
        bootstrapVarianceConsistent)
    (hcover :
      ∀ index unit, unit ∈ sample index -> score index unit ∈ cells)
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
        cellResidual index (score index unit) = residual index unit)
    (hbaseLimit :
      ∀ cell, cell ∈ cells ->
        Tendsto (fun index => cellBaseWeight index cell)
          l (nhds (baseWeightLimit cell)))
    (hreuseLimit :
      ∀ cell, cell ∈ cells ->
        Tendsto (fun index => cellReuseResidualWeight index cell)
          l (nhds (reuseResidualWeightLimit cell)))
    (hheterogeneityLimit :
      ∀ cell, cell ∈ cells ->
        Tendsto (fun index => cellHeterogeneity index cell)
          l (nhds (heterogeneityLimit cell)))
    (hresidualLimit :
      ∀ cell, cell ∈ cells ->
        Tendsto (fun index => cellResidual index cell)
          l (nhds (residualLimit cell)))
    (hmass :
      cellwiseScoreCellMassLLN (l := l) cells sample
        (fun _index _unit => 1) score massLimit)
    (hmultiplier : multiplierWeightRegular)
    (hscore : bootstrapScoreReplicationConsistent)
    (hbias : bootstrapBiasCorrectionConsistent) :
    bootstrapVarianceConsistent :=
  prospective_pate_bootstrap_variance_consistency_of_indexed_cell_contribution_weight_limits_direct
    (l := l) cells sample multiplier baseWeight reuseResidualWeight
    heterogeneity residual score target denominator normalizer
    (fun index =>
      pateBootstrapScoreCellContribution (cellBaseWeight index)
        (cellReuseResidualWeight index) (cellHeterogeneity index)
        (cellResidual index))
    cellBaseWeight
    (pateBootstrapScoreCellContribution baseWeightLimit
      reuseResidualWeightLimit heterogeneityLimit residualLimit)
    baseWeightLimit massLimit multiplierWeightRegular
    bootstrapScoreReplicationConsistent bootstrapBiasCorrectionConsistent
    bootstrapVarianceConsistent bridge hcover
    (prospective_pate_bootstrap_cellContribution_eq_of_score_components
      sample score baseWeight reuseResidualWeight heterogeneity residual
      cellBaseWeight cellReuseResidualWeight cellHeterogeneity cellResidual
      hbase hreuse hheterogeneity hresidual)
    hbase
    (tendsto_pateBootstrapScoreCellContribution_of_component_limits
      (l := l) cells cellBaseWeight cellReuseResidualWeight
      cellHeterogeneity cellResidual baseWeightLimit
      reuseResidualWeightLimit heterogeneityLimit residualLimit hbaseLimit
      hreuseLimit hheterogeneityLimit hresidualLimit)
    hbaseLimit hmass hmultiplier hscore hbias

/--
Retrospective PATT bootstrap consistency from component-level score-cell
representations and limits.
-/
theorem retrospective_patt_bootstrap_variance_consistency_of_score_cell_components_direct
    (cells : Finset Cell)
    (sample : Index -> Finset Unit)
    (multiplier denominatorWeight treatedContribution controlReuseContribution :
      Index -> Unit -> Real)
    (score : Index -> Unit -> Cell)
    (target denominator normalizer : Real)
    (cellDenominatorWeight cellTreatedContribution
      cellControlReuseContribution : Index -> Cell -> Real)
    (denominatorWeightLimit treatedContributionLimit
      controlReuseContributionLimit massLimit : Cell -> Real)
    (multiplierWeightRegular bootstrapScoreReplicationConsistent
      bootstrapBiasCorrectionConsistent bootstrapVarianceConsistent : Prop)
    (bridge :
      (∀ index,
        retrospectivePATTBootstrapFiniteAlgebraVerified (sample index)
          (multiplier index) (denominatorWeight index)
          (treatedContribution index) (controlReuseContribution index)) ->
        multiplierWeightRegular ->
        bootstrapScoreReplicationConsistent ->
        bootstrapBiasCorrectionConsistent ->
        Tendsto
          (fun index =>
            bootstrapCenteredVarianceTarget (sample index)
              (retrospectivePATTBootstrapInfluenceContribution
                (treatedContribution index) (controlReuseContribution index))
              (denominatorWeight index) target denominator normalizer)
          l
          (nhds
            ((1 / denominator ^ 2) * (1 / normalizer) *
              weightedScoreCellMomentLimit cells
                (fun cell =>
                  (pattBootstrapScoreCellContribution
                        treatedContributionLimit
                        controlReuseContributionLimit cell -
                      target * denominatorWeightLimit cell) ^ 2)
                massLimit)) ->
        bootstrapVarianceConsistent)
    (hcover :
      ∀ index unit, unit ∈ sample index -> score index unit ∈ cells)
    (hdenominator :
      ∀ index unit, unit ∈ sample index ->
        cellDenominatorWeight index (score index unit) =
          denominatorWeight index unit)
    (htreated :
      ∀ index unit, unit ∈ sample index ->
        cellTreatedContribution index (score index unit) =
          treatedContribution index unit)
    (hcontrol :
      ∀ index unit, unit ∈ sample index ->
        cellControlReuseContribution index (score index unit) =
          controlReuseContribution index unit)
    (hdenominatorLimit :
      ∀ cell, cell ∈ cells ->
        Tendsto (fun index => cellDenominatorWeight index cell)
          l (nhds (denominatorWeightLimit cell)))
    (htreatedLimit :
      ∀ cell, cell ∈ cells ->
        Tendsto (fun index => cellTreatedContribution index cell)
          l (nhds (treatedContributionLimit cell)))
    (hcontrolLimit :
      ∀ cell, cell ∈ cells ->
        Tendsto (fun index => cellControlReuseContribution index cell)
          l (nhds (controlReuseContributionLimit cell)))
    (hmass :
      cellwiseScoreCellMassLLN (l := l) cells sample
        (fun _index _unit => 1) score massLimit)
    (hmultiplier : multiplierWeightRegular)
    (hscore : bootstrapScoreReplicationConsistent)
    (hbias : bootstrapBiasCorrectionConsistent) :
    bootstrapVarianceConsistent :=
  retrospective_patt_bootstrap_variance_consistency_of_indexed_cell_contribution_weight_limits_direct
    (l := l) cells sample multiplier denominatorWeight treatedContribution
    controlReuseContribution score target denominator normalizer
    (fun index =>
      pattBootstrapScoreCellContribution (cellTreatedContribution index)
        (cellControlReuseContribution index))
    cellDenominatorWeight
    (pattBootstrapScoreCellContribution treatedContributionLimit
      controlReuseContributionLimit)
    denominatorWeightLimit massLimit multiplierWeightRegular
    bootstrapScoreReplicationConsistent bootstrapBiasCorrectionConsistent
    bootstrapVarianceConsistent bridge hcover
    (retrospective_patt_bootstrap_cellContribution_eq_of_score_components
      sample score treatedContribution controlReuseContribution
      cellTreatedContribution cellControlReuseContribution htreated hcontrol)
    hdenominator
    (tendsto_pattBootstrapScoreCellContribution_of_component_limits
      (l := l) cells cellTreatedContribution cellControlReuseContribution
      treatedContributionLimit controlReuseContributionLimit htreatedLimit
      hcontrolLimit)
    hdenominatorLimit hmass hmultiplier hscore hbias

/--
Prospective PATT bootstrap consistency from component-level score-cell
representations and limits.
-/
theorem prospective_patt_bootstrap_variance_consistency_of_score_cell_components_direct
    (cells : Finset Cell)
    (sample : Index -> Finset Unit)
    (multiplier denominatorWeight treatedContribution controlReuseContribution :
      Index -> Unit -> Real)
    (score : Index -> Unit -> Cell)
    (target denominator normalizer : Real)
    (cellDenominatorWeight cellTreatedContribution
      cellControlReuseContribution : Index -> Cell -> Real)
    (denominatorWeightLimit treatedContributionLimit
      controlReuseContributionLimit massLimit : Cell -> Real)
    (multiplierWeightRegular bootstrapScoreReplicationConsistent
      bootstrapBiasCorrectionConsistent bootstrapVarianceConsistent : Prop)
    (bridge :
      (∀ index,
        prospectivePATTBootstrapFiniteAlgebraVerified (sample index)
          (multiplier index) (denominatorWeight index)
          (treatedContribution index) (controlReuseContribution index)) ->
        multiplierWeightRegular ->
        bootstrapScoreReplicationConsistent ->
        bootstrapBiasCorrectionConsistent ->
        Tendsto
          (fun index =>
            bootstrapCenteredVarianceTarget (sample index)
              (prospectivePATTBootstrapInfluenceContribution
                (treatedContribution index) (controlReuseContribution index))
              (denominatorWeight index) target denominator normalizer)
          l
          (nhds
            ((1 / denominator ^ 2) * (1 / normalizer) *
              weightedScoreCellMomentLimit cells
                (fun cell =>
                  (pattBootstrapScoreCellContribution
                        treatedContributionLimit
                        controlReuseContributionLimit cell -
                      target * denominatorWeightLimit cell) ^ 2)
                massLimit)) ->
        bootstrapVarianceConsistent)
    (hcover :
      ∀ index unit, unit ∈ sample index -> score index unit ∈ cells)
    (hdenominator :
      ∀ index unit, unit ∈ sample index ->
        cellDenominatorWeight index (score index unit) =
          denominatorWeight index unit)
    (htreated :
      ∀ index unit, unit ∈ sample index ->
        cellTreatedContribution index (score index unit) =
          treatedContribution index unit)
    (hcontrol :
      ∀ index unit, unit ∈ sample index ->
        cellControlReuseContribution index (score index unit) =
          controlReuseContribution index unit)
    (hdenominatorLimit :
      ∀ cell, cell ∈ cells ->
        Tendsto (fun index => cellDenominatorWeight index cell)
          l (nhds (denominatorWeightLimit cell)))
    (htreatedLimit :
      ∀ cell, cell ∈ cells ->
        Tendsto (fun index => cellTreatedContribution index cell)
          l (nhds (treatedContributionLimit cell)))
    (hcontrolLimit :
      ∀ cell, cell ∈ cells ->
        Tendsto (fun index => cellControlReuseContribution index cell)
          l (nhds (controlReuseContributionLimit cell)))
    (hmass :
      cellwiseScoreCellMassLLN (l := l) cells sample
        (fun _index _unit => 1) score massLimit)
    (hmultiplier : multiplierWeightRegular)
    (hscore : bootstrapScoreReplicationConsistent)
    (hbias : bootstrapBiasCorrectionConsistent) :
    bootstrapVarianceConsistent :=
  prospective_patt_bootstrap_variance_consistency_of_indexed_cell_contribution_weight_limits_direct
    (l := l) cells sample multiplier denominatorWeight treatedContribution
    controlReuseContribution score target denominator normalizer
    (fun index =>
      pattBootstrapScoreCellContribution (cellTreatedContribution index)
        (cellControlReuseContribution index))
    cellDenominatorWeight
    (pattBootstrapScoreCellContribution treatedContributionLimit
      controlReuseContributionLimit)
    denominatorWeightLimit massLimit multiplierWeightRegular
    bootstrapScoreReplicationConsistent bootstrapBiasCorrectionConsistent
    bootstrapVarianceConsistent bridge hcover
    (prospective_patt_bootstrap_cellContribution_eq_of_score_components
      sample score treatedContribution controlReuseContribution
      cellTreatedContribution cellControlReuseContribution htreated hcontrol)
    hdenominator
    (tendsto_pattBootstrapScoreCellContribution_of_component_limits
      (l := l) cells cellTreatedContribution cellControlReuseContribution
      treatedContributionLimit controlReuseContributionLimit htreatedLimit
      hcontrolLimit)
    hdenominatorLimit hmass hmultiplier hscore hbias

/--
Paired retrospective PATE/PATT bootstrap consistency from component-level
score-cell representations and limits.
-/
theorem retrospective_pate_patt_bootstrap_variance_consistency_of_score_cell_components_direct
    (pateCells : Finset Cell)
    (pateSample : Index -> Finset Unit)
    (pateMultiplier pateBaseWeight pateReuseResidualWeight pateHeterogeneity
      pateResidual : Index -> Unit -> Real)
    (pateScore : Index -> Unit -> Cell)
    (pateTarget pateDenominator pateNormalizer : Real)
    (pateCellBaseWeight pateCellReuseResidualWeight pateCellHeterogeneity
      pateCellResidual : Index -> Cell -> Real)
    (pateBaseWeightLimit pateReuseResidualWeightLimit
      pateHeterogeneityLimit pateResidualLimit pateMassLimit : Cell -> Real)
    (pateMultiplierWeightRegular pateBootstrapScoreReplicationConsistent
      pateBootstrapBiasCorrectionConsistent pateBootstrapVarianceConsistent :
      Prop)
    (pateBridge :
      (∀ index,
        retrospectivePATEBootstrapFiniteAlgebraVerified (pateSample index)
          (pateMultiplier index) (pateBaseWeight index)
          (pateReuseResidualWeight index) (pateHeterogeneity index)
          (pateResidual index)) ->
        pateMultiplierWeightRegular ->
        pateBootstrapScoreReplicationConsistent ->
        pateBootstrapBiasCorrectionConsistent ->
        Tendsto
          (fun index =>
            bootstrapCenteredVarianceTarget (pateSample index)
              (retrospectivePATEBootstrapInfluenceContribution
                (pateBaseWeight index) (pateReuseResidualWeight index)
                (pateHeterogeneity index) (pateResidual index))
              (pateBaseWeight index) pateTarget pateDenominator
              pateNormalizer)
          l
          (nhds
            ((1 / pateDenominator ^ 2) * (1 / pateNormalizer) *
              weightedScoreCellMomentLimit pateCells
                (fun cell =>
                  (pateBootstrapScoreCellContribution pateBaseWeightLimit
                        pateReuseResidualWeightLimit pateHeterogeneityLimit
                        pateResidualLimit cell -
                      pateTarget * pateBaseWeightLimit cell) ^ 2)
                pateMassLimit)) ->
        pateBootstrapVarianceConsistent)
    (hpateCover :
      ∀ index unit, unit ∈ pateSample index ->
        pateScore index unit ∈ pateCells)
    (hpateBase :
      ∀ index unit, unit ∈ pateSample index ->
        pateCellBaseWeight index (pateScore index unit) =
          pateBaseWeight index unit)
    (hpateReuse :
      ∀ index unit, unit ∈ pateSample index ->
        pateCellReuseResidualWeight index (pateScore index unit) =
          pateReuseResidualWeight index unit)
    (hpateHeterogeneity :
      ∀ index unit, unit ∈ pateSample index ->
        pateCellHeterogeneity index (pateScore index unit) =
          pateHeterogeneity index unit)
    (hpateResidual :
      ∀ index unit, unit ∈ pateSample index ->
        pateCellResidual index (pateScore index unit) =
          pateResidual index unit)
    (hpateBaseLimit :
      ∀ cell, cell ∈ pateCells ->
        Tendsto (fun index => pateCellBaseWeight index cell)
          l (nhds (pateBaseWeightLimit cell)))
    (hpateReuseLimit :
      ∀ cell, cell ∈ pateCells ->
        Tendsto (fun index => pateCellReuseResidualWeight index cell)
          l (nhds (pateReuseResidualWeightLimit cell)))
    (hpateHeterogeneityLimit :
      ∀ cell, cell ∈ pateCells ->
        Tendsto (fun index => pateCellHeterogeneity index cell)
          l (nhds (pateHeterogeneityLimit cell)))
    (hpateResidualLimit :
      ∀ cell, cell ∈ pateCells ->
        Tendsto (fun index => pateCellResidual index cell)
          l (nhds (pateResidualLimit cell)))
    (hpateMass :
      cellwiseScoreCellMassLLN (l := l) pateCells pateSample
        (fun _index _unit => 1) pateScore pateMassLimit)
    (hpateMultiplier : pateMultiplierWeightRegular)
    (hpateScore : pateBootstrapScoreReplicationConsistent)
    (hpateBias : pateBootstrapBiasCorrectionConsistent)
    (pattCells : Finset Cell)
    (pattSample : Index -> Finset Unit)
    (pattMultiplier pattDenominatorWeight pattTreatedContribution
      pattControlReuseContribution : Index -> Unit -> Real)
    (pattScore : Index -> Unit -> Cell)
    (pattTarget pattDenominator pattNormalizer : Real)
    (pattCellDenominatorWeight pattCellTreatedContribution
      pattCellControlReuseContribution : Index -> Cell -> Real)
    (pattDenominatorWeightLimit pattTreatedContributionLimit
      pattControlReuseContributionLimit pattMassLimit : Cell -> Real)
    (pattMultiplierWeightRegular pattBootstrapScoreReplicationConsistent
      pattBootstrapBiasCorrectionConsistent pattBootstrapVarianceConsistent :
      Prop)
    (pattBridge :
      (∀ index,
        retrospectivePATTBootstrapFiniteAlgebraVerified (pattSample index)
          (pattMultiplier index) (pattDenominatorWeight index)
          (pattTreatedContribution index)
          (pattControlReuseContribution index)) ->
        pattMultiplierWeightRegular ->
        pattBootstrapScoreReplicationConsistent ->
        pattBootstrapBiasCorrectionConsistent ->
        Tendsto
          (fun index =>
            bootstrapCenteredVarianceTarget (pattSample index)
              (retrospectivePATTBootstrapInfluenceContribution
                (pattTreatedContribution index)
                (pattControlReuseContribution index))
              (pattDenominatorWeight index) pattTarget pattDenominator
              pattNormalizer)
          l
          (nhds
            ((1 / pattDenominator ^ 2) * (1 / pattNormalizer) *
              weightedScoreCellMomentLimit pattCells
                (fun cell =>
                  (pattBootstrapScoreCellContribution
                        pattTreatedContributionLimit
                        pattControlReuseContributionLimit cell -
                      pattTarget * pattDenominatorWeightLimit cell) ^ 2)
                pattMassLimit)) ->
        pattBootstrapVarianceConsistent)
    (hpattCover :
      ∀ index unit, unit ∈ pattSample index ->
        pattScore index unit ∈ pattCells)
    (hpattDenominator :
      ∀ index unit, unit ∈ pattSample index ->
        pattCellDenominatorWeight index (pattScore index unit) =
          pattDenominatorWeight index unit)
    (hpattTreated :
      ∀ index unit, unit ∈ pattSample index ->
        pattCellTreatedContribution index (pattScore index unit) =
          pattTreatedContribution index unit)
    (hpattControl :
      ∀ index unit, unit ∈ pattSample index ->
        pattCellControlReuseContribution index (pattScore index unit) =
          pattControlReuseContribution index unit)
    (hpattDenominatorLimit :
      ∀ cell, cell ∈ pattCells ->
        Tendsto (fun index => pattCellDenominatorWeight index cell)
          l (nhds (pattDenominatorWeightLimit cell)))
    (hpattTreatedLimit :
      ∀ cell, cell ∈ pattCells ->
        Tendsto (fun index => pattCellTreatedContribution index cell)
          l (nhds (pattTreatedContributionLimit cell)))
    (hpattControlLimit :
      ∀ cell, cell ∈ pattCells ->
        Tendsto (fun index => pattCellControlReuseContribution index cell)
          l (nhds (pattControlReuseContributionLimit cell)))
    (hpattMass :
      cellwiseScoreCellMassLLN (l := l) pattCells pattSample
        (fun _index _unit => 1) pattScore pattMassLimit)
    (hpattMultiplier : pattMultiplierWeightRegular)
    (hpattScore : pattBootstrapScoreReplicationConsistent)
    (hpattBias : pattBootstrapBiasCorrectionConsistent) :
    pateBootstrapVarianceConsistent ∧ pattBootstrapVarianceConsistent := by
  constructor
  · exact
      retrospective_pate_bootstrap_variance_consistency_of_score_cell_components_direct
        (l := l) pateCells pateSample pateMultiplier pateBaseWeight
        pateReuseResidualWeight pateHeterogeneity pateResidual pateScore
        pateTarget pateDenominator pateNormalizer pateCellBaseWeight
        pateCellReuseResidualWeight pateCellHeterogeneity pateCellResidual
        pateBaseWeightLimit pateReuseResidualWeightLimit
        pateHeterogeneityLimit pateResidualLimit pateMassLimit
        pateMultiplierWeightRegular pateBootstrapScoreReplicationConsistent
        pateBootstrapBiasCorrectionConsistent pateBootstrapVarianceConsistent
        pateBridge hpateCover hpateBase hpateReuse hpateHeterogeneity
        hpateResidual hpateBaseLimit hpateReuseLimit hpateHeterogeneityLimit
        hpateResidualLimit hpateMass hpateMultiplier hpateScore hpateBias
  · exact
      retrospective_patt_bootstrap_variance_consistency_of_score_cell_components_direct
        (l := l) pattCells pattSample pattMultiplier pattDenominatorWeight
        pattTreatedContribution pattControlReuseContribution pattScore
        pattTarget pattDenominator pattNormalizer pattCellDenominatorWeight
        pattCellTreatedContribution pattCellControlReuseContribution
        pattDenominatorWeightLimit pattTreatedContributionLimit
        pattControlReuseContributionLimit pattMassLimit
        pattMultiplierWeightRegular pattBootstrapScoreReplicationConsistent
        pattBootstrapBiasCorrectionConsistent pattBootstrapVarianceConsistent
        pattBridge hpattCover hpattDenominator hpattTreated hpattControl
        hpattDenominatorLimit hpattTreatedLimit hpattControlLimit hpattMass
        hpattMultiplier hpattScore hpattBias

/--
Paired prospective PATE/PATT bootstrap consistency from component-level
score-cell representations and limits.
-/
theorem prospective_pate_patt_bootstrap_variance_consistency_of_score_cell_components_direct
    (pateCells : Finset Cell)
    (pateSample : Index -> Finset Unit)
    (pateMultiplier pateBaseWeight pateReuseResidualWeight pateHeterogeneity
      pateResidual : Index -> Unit -> Real)
    (pateScore : Index -> Unit -> Cell)
    (pateTarget pateDenominator pateNormalizer : Real)
    (pateCellBaseWeight pateCellReuseResidualWeight pateCellHeterogeneity
      pateCellResidual : Index -> Cell -> Real)
    (pateBaseWeightLimit pateReuseResidualWeightLimit
      pateHeterogeneityLimit pateResidualLimit pateMassLimit : Cell -> Real)
    (pateMultiplierWeightRegular pateBootstrapScoreReplicationConsistent
      pateBootstrapBiasCorrectionConsistent pateBootstrapVarianceConsistent :
      Prop)
    (pateBridge :
      (∀ index,
        prospectivePATEBootstrapFiniteAlgebraVerified (pateSample index)
          (pateMultiplier index) (pateBaseWeight index)
          (pateReuseResidualWeight index) (pateHeterogeneity index)
          (pateResidual index)) ->
        pateMultiplierWeightRegular ->
        pateBootstrapScoreReplicationConsistent ->
        pateBootstrapBiasCorrectionConsistent ->
        Tendsto
          (fun index =>
            bootstrapCenteredVarianceTarget (pateSample index)
              (prospectivePATEBootstrapInfluenceContribution
                (pateBaseWeight index) (pateReuseResidualWeight index)
                (pateHeterogeneity index) (pateResidual index))
              (pateBaseWeight index) pateTarget pateDenominator
              pateNormalizer)
          l
          (nhds
            ((1 / pateDenominator ^ 2) * (1 / pateNormalizer) *
              weightedScoreCellMomentLimit pateCells
                (fun cell =>
                  (pateBootstrapScoreCellContribution pateBaseWeightLimit
                        pateReuseResidualWeightLimit pateHeterogeneityLimit
                        pateResidualLimit cell -
                      pateTarget * pateBaseWeightLimit cell) ^ 2)
                pateMassLimit)) ->
        pateBootstrapVarianceConsistent)
    (hpateCover :
      ∀ index unit, unit ∈ pateSample index ->
        pateScore index unit ∈ pateCells)
    (hpateBase :
      ∀ index unit, unit ∈ pateSample index ->
        pateCellBaseWeight index (pateScore index unit) =
          pateBaseWeight index unit)
    (hpateReuse :
      ∀ index unit, unit ∈ pateSample index ->
        pateCellReuseResidualWeight index (pateScore index unit) =
          pateReuseResidualWeight index unit)
    (hpateHeterogeneity :
      ∀ index unit, unit ∈ pateSample index ->
        pateCellHeterogeneity index (pateScore index unit) =
          pateHeterogeneity index unit)
    (hpateResidual :
      ∀ index unit, unit ∈ pateSample index ->
        pateCellResidual index (pateScore index unit) =
          pateResidual index unit)
    (hpateBaseLimit :
      ∀ cell, cell ∈ pateCells ->
        Tendsto (fun index => pateCellBaseWeight index cell)
          l (nhds (pateBaseWeightLimit cell)))
    (hpateReuseLimit :
      ∀ cell, cell ∈ pateCells ->
        Tendsto (fun index => pateCellReuseResidualWeight index cell)
          l (nhds (pateReuseResidualWeightLimit cell)))
    (hpateHeterogeneityLimit :
      ∀ cell, cell ∈ pateCells ->
        Tendsto (fun index => pateCellHeterogeneity index cell)
          l (nhds (pateHeterogeneityLimit cell)))
    (hpateResidualLimit :
      ∀ cell, cell ∈ pateCells ->
        Tendsto (fun index => pateCellResidual index cell)
          l (nhds (pateResidualLimit cell)))
    (hpateMass :
      cellwiseScoreCellMassLLN (l := l) pateCells pateSample
        (fun _index _unit => 1) pateScore pateMassLimit)
    (hpateMultiplier : pateMultiplierWeightRegular)
    (hpateScore : pateBootstrapScoreReplicationConsistent)
    (hpateBias : pateBootstrapBiasCorrectionConsistent)
    (pattCells : Finset Cell)
    (pattSample : Index -> Finset Unit)
    (pattMultiplier pattDenominatorWeight pattTreatedContribution
      pattControlReuseContribution : Index -> Unit -> Real)
    (pattScore : Index -> Unit -> Cell)
    (pattTarget pattDenominator pattNormalizer : Real)
    (pattCellDenominatorWeight pattCellTreatedContribution
      pattCellControlReuseContribution : Index -> Cell -> Real)
    (pattDenominatorWeightLimit pattTreatedContributionLimit
      pattControlReuseContributionLimit pattMassLimit : Cell -> Real)
    (pattMultiplierWeightRegular pattBootstrapScoreReplicationConsistent
      pattBootstrapBiasCorrectionConsistent pattBootstrapVarianceConsistent :
      Prop)
    (pattBridge :
      (∀ index,
        prospectivePATTBootstrapFiniteAlgebraVerified (pattSample index)
          (pattMultiplier index) (pattDenominatorWeight index)
          (pattTreatedContribution index)
          (pattControlReuseContribution index)) ->
        pattMultiplierWeightRegular ->
        pattBootstrapScoreReplicationConsistent ->
        pattBootstrapBiasCorrectionConsistent ->
        Tendsto
          (fun index =>
            bootstrapCenteredVarianceTarget (pattSample index)
              (prospectivePATTBootstrapInfluenceContribution
                (pattTreatedContribution index)
                (pattControlReuseContribution index))
              (pattDenominatorWeight index) pattTarget pattDenominator
              pattNormalizer)
          l
          (nhds
            ((1 / pattDenominator ^ 2) * (1 / pattNormalizer) *
              weightedScoreCellMomentLimit pattCells
                (fun cell =>
                  (pattBootstrapScoreCellContribution
                        pattTreatedContributionLimit
                        pattControlReuseContributionLimit cell -
                      pattTarget * pattDenominatorWeightLimit cell) ^ 2)
                pattMassLimit)) ->
        pattBootstrapVarianceConsistent)
    (hpattCover :
      ∀ index unit, unit ∈ pattSample index ->
        pattScore index unit ∈ pattCells)
    (hpattDenominator :
      ∀ index unit, unit ∈ pattSample index ->
        pattCellDenominatorWeight index (pattScore index unit) =
          pattDenominatorWeight index unit)
    (hpattTreated :
      ∀ index unit, unit ∈ pattSample index ->
        pattCellTreatedContribution index (pattScore index unit) =
          pattTreatedContribution index unit)
    (hpattControl :
      ∀ index unit, unit ∈ pattSample index ->
        pattCellControlReuseContribution index (pattScore index unit) =
          pattControlReuseContribution index unit)
    (hpattDenominatorLimit :
      ∀ cell, cell ∈ pattCells ->
        Tendsto (fun index => pattCellDenominatorWeight index cell)
          l (nhds (pattDenominatorWeightLimit cell)))
    (hpattTreatedLimit :
      ∀ cell, cell ∈ pattCells ->
        Tendsto (fun index => pattCellTreatedContribution index cell)
          l (nhds (pattTreatedContributionLimit cell)))
    (hpattControlLimit :
      ∀ cell, cell ∈ pattCells ->
        Tendsto (fun index => pattCellControlReuseContribution index cell)
          l (nhds (pattControlReuseContributionLimit cell)))
    (hpattMass :
      cellwiseScoreCellMassLLN (l := l) pattCells pattSample
        (fun _index _unit => 1) pattScore pattMassLimit)
    (hpattMultiplier : pattMultiplierWeightRegular)
    (hpattScore : pattBootstrapScoreReplicationConsistent)
    (hpattBias : pattBootstrapBiasCorrectionConsistent) :
    pateBootstrapVarianceConsistent ∧ pattBootstrapVarianceConsistent := by
  constructor
  · exact
      prospective_pate_bootstrap_variance_consistency_of_score_cell_components_direct
        (l := l) pateCells pateSample pateMultiplier pateBaseWeight
        pateReuseResidualWeight pateHeterogeneity pateResidual pateScore
        pateTarget pateDenominator pateNormalizer pateCellBaseWeight
        pateCellReuseResidualWeight pateCellHeterogeneity pateCellResidual
        pateBaseWeightLimit pateReuseResidualWeightLimit
        pateHeterogeneityLimit pateResidualLimit pateMassLimit
        pateMultiplierWeightRegular pateBootstrapScoreReplicationConsistent
        pateBootstrapBiasCorrectionConsistent pateBootstrapVarianceConsistent
        pateBridge hpateCover hpateBase hpateReuse hpateHeterogeneity
        hpateResidual hpateBaseLimit hpateReuseLimit hpateHeterogeneityLimit
        hpateResidualLimit hpateMass hpateMultiplier hpateScore hpateBias
  · exact
      prospective_patt_bootstrap_variance_consistency_of_score_cell_components_direct
        (l := l) pattCells pattSample pattMultiplier pattDenominatorWeight
        pattTreatedContribution pattControlReuseContribution pattScore
        pattTarget pattDenominator pattNormalizer pattCellDenominatorWeight
        pattCellTreatedContribution pattCellControlReuseContribution
        pattDenominatorWeightLimit pattTreatedContributionLimit
        pattControlReuseContributionLimit pattMassLimit
        pattMultiplierWeightRegular pattBootstrapScoreReplicationConsistent
        pattBootstrapBiasCorrectionConsistent pattBootstrapVarianceConsistent
        pattBridge hpattCover hpattDenominator hpattTreated hpattControl
        hpattDenominatorLimit hpattTreatedLimit hpattControlLimit hpattMass
        hpattMultiplier hpattScore hpattBias

/--
Retrospective PATE bootstrap consistency from eventually valid component-level
score-cell representations and component limits.
-/
theorem retrospective_pate_bootstrap_variance_consistency_of_eventually_score_cell_components_direct
    (cells : Finset Cell)
    (sample : Index -> Finset Unit)
    (multiplier baseWeight reuseResidualWeight heterogeneity residual :
      Index -> Unit -> Real)
    (score : Index -> Unit -> Cell)
    (target denominator normalizer : Real)
    (cellBaseWeight cellReuseResidualWeight cellHeterogeneity cellResidual :
      Index -> Cell -> Real)
    (baseWeightLimit reuseResidualWeightLimit heterogeneityLimit
      residualLimit massLimit : Cell -> Real)
    (multiplierWeightRegular bootstrapScoreReplicationConsistent
      bootstrapBiasCorrectionConsistent bootstrapVarianceConsistent : Prop)
    (bridge :
      (∀ index,
        retrospectivePATEBootstrapFiniteAlgebraVerified (sample index)
          (multiplier index) (baseWeight index)
          (reuseResidualWeight index) (heterogeneity index)
          (residual index)) ->
        multiplierWeightRegular ->
        bootstrapScoreReplicationConsistent ->
        bootstrapBiasCorrectionConsistent ->
        Tendsto
          (fun index =>
            bootstrapCenteredVarianceTarget (sample index)
              (retrospectivePATEBootstrapInfluenceContribution
                (baseWeight index) (reuseResidualWeight index)
                (heterogeneity index) (residual index))
              (baseWeight index) target denominator normalizer)
          l
          (nhds
            ((1 / denominator ^ 2) * (1 / normalizer) *
              weightedScoreCellMomentLimit cells
                (fun cell =>
                  (pateBootstrapScoreCellContribution baseWeightLimit
                        reuseResidualWeightLimit heterogeneityLimit
                        residualLimit cell -
                      target * baseWeightLimit cell) ^ 2)
                massLimit)) ->
        bootstrapVarianceConsistent)
    (hcover :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ sample index -> score index unit ∈ cells)
    (hbase :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ sample index ->
          cellBaseWeight index (score index unit) = baseWeight index unit)
    (hreuse :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ sample index ->
          cellReuseResidualWeight index (score index unit) =
            reuseResidualWeight index unit)
    (hheterogeneity :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ sample index ->
          cellHeterogeneity index (score index unit) =
            heterogeneity index unit)
    (hresidual :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ sample index ->
          cellResidual index (score index unit) = residual index unit)
    (hbaseLimit :
      ∀ cell, cell ∈ cells ->
        Tendsto (fun index => cellBaseWeight index cell)
          l (nhds (baseWeightLimit cell)))
    (hreuseLimit :
      ∀ cell, cell ∈ cells ->
        Tendsto (fun index => cellReuseResidualWeight index cell)
          l (nhds (reuseResidualWeightLimit cell)))
    (hheterogeneityLimit :
      ∀ cell, cell ∈ cells ->
        Tendsto (fun index => cellHeterogeneity index cell)
          l (nhds (heterogeneityLimit cell)))
    (hresidualLimit :
      ∀ cell, cell ∈ cells ->
        Tendsto (fun index => cellResidual index cell)
          l (nhds (residualLimit cell)))
    (hmass :
      cellwiseScoreCellMassLLN (l := l) cells sample
        (fun _index _unit => 1) score massLimit)
    (hmultiplier : multiplierWeightRegular)
    (hscore : bootstrapScoreReplicationConsistent)
    (hbias : bootstrapBiasCorrectionConsistent) :
    bootstrapVarianceConsistent :=
  bootstrap_variance_consistency_of_eventually_finite_cell_contribution_weight_limits_direct
    (l := l) cells sample score
    (fun index =>
      retrospectivePATEBootstrapInfluenceContribution (baseWeight index)
        (reuseResidualWeight index) (heterogeneity index) (residual index))
    baseWeight target denominator normalizer
    (fun index =>
      pateBootstrapScoreCellContribution (cellBaseWeight index)
        (cellReuseResidualWeight index) (cellHeterogeneity index)
        (cellResidual index))
    cellBaseWeight
    (pateBootstrapScoreCellContribution baseWeightLimit
      reuseResidualWeightLimit heterogeneityLimit residualLimit)
    baseWeightLimit massLimit
    (∀ index,
      retrospectivePATEBootstrapFiniteAlgebraVerified (sample index)
        (multiplier index) (baseWeight index)
        (reuseResidualWeight index) (heterogeneity index) (residual index))
    multiplierWeightRegular bootstrapScoreReplicationConsistent
    bootstrapBiasCorrectionConsistent bootstrapVarianceConsistent bridge
    (fun index =>
      retrospectivePATEBootstrapFiniteAlgebraVerified_of_replicate_identities
        (sample index) (multiplier index) (baseWeight index)
        (reuseResidualWeight index) (heterogeneity index) (residual index))
    hcover
    (by
      filter_upwards [hbase, hreuse, hheterogeneity, hresidual] with index
        hbaseIndex hreuseIndex hheterogeneityIndex hresidualIndex unit hunit
      unfold pateBootstrapScoreCellContribution
        retrospectivePATEBootstrapInfluenceContribution
      rw [hbaseIndex unit hunit, hreuseIndex unit hunit,
        hheterogeneityIndex unit hunit, hresidualIndex unit hunit])
    hbase
    (tendsto_pateBootstrapScoreCellContribution_of_component_limits
      (l := l) cells cellBaseWeight cellReuseResidualWeight
      cellHeterogeneity cellResidual baseWeightLimit
      reuseResidualWeightLimit heterogeneityLimit residualLimit hbaseLimit
      hreuseLimit hheterogeneityLimit hresidualLimit)
    hbaseLimit hmass hmultiplier hscore hbias

/--
Prospective PATE bootstrap consistency from eventually valid component-level
score-cell representations and component limits.
-/
theorem prospective_pate_bootstrap_variance_consistency_of_eventually_score_cell_components_direct
    (cells : Finset Cell)
    (sample : Index -> Finset Unit)
    (multiplier baseWeight reuseResidualWeight heterogeneity residual :
      Index -> Unit -> Real)
    (score : Index -> Unit -> Cell)
    (target denominator normalizer : Real)
    (cellBaseWeight cellReuseResidualWeight cellHeterogeneity cellResidual :
      Index -> Cell -> Real)
    (baseWeightLimit reuseResidualWeightLimit heterogeneityLimit
      residualLimit massLimit : Cell -> Real)
    (multiplierWeightRegular bootstrapScoreReplicationConsistent
      bootstrapBiasCorrectionConsistent bootstrapVarianceConsistent : Prop)
    (bridge :
      (∀ index,
        prospectivePATEBootstrapFiniteAlgebraVerified (sample index)
          (multiplier index) (baseWeight index)
          (reuseResidualWeight index) (heterogeneity index)
          (residual index)) ->
        multiplierWeightRegular ->
        bootstrapScoreReplicationConsistent ->
        bootstrapBiasCorrectionConsistent ->
        Tendsto
          (fun index =>
            bootstrapCenteredVarianceTarget (sample index)
              (prospectivePATEBootstrapInfluenceContribution
                (baseWeight index) (reuseResidualWeight index)
                (heterogeneity index) (residual index))
              (baseWeight index) target denominator normalizer)
          l
          (nhds
            ((1 / denominator ^ 2) * (1 / normalizer) *
              weightedScoreCellMomentLimit cells
                (fun cell =>
                  (pateBootstrapScoreCellContribution baseWeightLimit
                        reuseResidualWeightLimit heterogeneityLimit
                        residualLimit cell -
                      target * baseWeightLimit cell) ^ 2)
                massLimit)) ->
        bootstrapVarianceConsistent)
    (hcover :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ sample index -> score index unit ∈ cells)
    (hbase :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ sample index ->
          cellBaseWeight index (score index unit) = baseWeight index unit)
    (hreuse :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ sample index ->
          cellReuseResidualWeight index (score index unit) =
            reuseResidualWeight index unit)
    (hheterogeneity :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ sample index ->
          cellHeterogeneity index (score index unit) =
            heterogeneity index unit)
    (hresidual :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ sample index ->
          cellResidual index (score index unit) = residual index unit)
    (hbaseLimit :
      ∀ cell, cell ∈ cells ->
        Tendsto (fun index => cellBaseWeight index cell)
          l (nhds (baseWeightLimit cell)))
    (hreuseLimit :
      ∀ cell, cell ∈ cells ->
        Tendsto (fun index => cellReuseResidualWeight index cell)
          l (nhds (reuseResidualWeightLimit cell)))
    (hheterogeneityLimit :
      ∀ cell, cell ∈ cells ->
        Tendsto (fun index => cellHeterogeneity index cell)
          l (nhds (heterogeneityLimit cell)))
    (hresidualLimit :
      ∀ cell, cell ∈ cells ->
        Tendsto (fun index => cellResidual index cell)
          l (nhds (residualLimit cell)))
    (hmass :
      cellwiseScoreCellMassLLN (l := l) cells sample
        (fun _index _unit => 1) score massLimit)
    (hmultiplier : multiplierWeightRegular)
    (hscore : bootstrapScoreReplicationConsistent)
    (hbias : bootstrapBiasCorrectionConsistent) :
    bootstrapVarianceConsistent :=
  bootstrap_variance_consistency_of_eventually_finite_cell_contribution_weight_limits_direct
    (l := l) cells sample score
    (fun index =>
      prospectivePATEBootstrapInfluenceContribution (baseWeight index)
        (reuseResidualWeight index) (heterogeneity index) (residual index))
    baseWeight target denominator normalizer
    (fun index =>
      pateBootstrapScoreCellContribution (cellBaseWeight index)
        (cellReuseResidualWeight index) (cellHeterogeneity index)
        (cellResidual index))
    cellBaseWeight
    (pateBootstrapScoreCellContribution baseWeightLimit
      reuseResidualWeightLimit heterogeneityLimit residualLimit)
    baseWeightLimit massLimit
    (∀ index,
      prospectivePATEBootstrapFiniteAlgebraVerified (sample index)
        (multiplier index) (baseWeight index)
        (reuseResidualWeight index) (heterogeneity index) (residual index))
    multiplierWeightRegular bootstrapScoreReplicationConsistent
    bootstrapBiasCorrectionConsistent bootstrapVarianceConsistent bridge
    (fun index =>
      prospectivePATEBootstrapFiniteAlgebraVerified_of_replicate_identities
        (sample index) (multiplier index) (baseWeight index)
        (reuseResidualWeight index) (heterogeneity index) (residual index))
    hcover
    (by
      filter_upwards [hbase, hreuse, hheterogeneity, hresidual] with index
        hbaseIndex hreuseIndex hheterogeneityIndex hresidualIndex unit hunit
      unfold pateBootstrapScoreCellContribution
        prospectivePATEBootstrapInfluenceContribution
      rw [hbaseIndex unit hunit, hreuseIndex unit hunit,
        hheterogeneityIndex unit hunit, hresidualIndex unit hunit])
    hbase
    (tendsto_pateBootstrapScoreCellContribution_of_component_limits
      (l := l) cells cellBaseWeight cellReuseResidualWeight
      cellHeterogeneity cellResidual baseWeightLimit
      reuseResidualWeightLimit heterogeneityLimit residualLimit hbaseLimit
      hreuseLimit hheterogeneityLimit hresidualLimit)
    hbaseLimit hmass hmultiplier hscore hbias

/--
Retrospective PATT bootstrap consistency from eventually valid component-level
score-cell representations and component limits.
-/
theorem retrospective_patt_bootstrap_variance_consistency_of_eventually_score_cell_components_direct
    (cells : Finset Cell)
    (sample : Index -> Finset Unit)
    (multiplier denominatorWeight treatedContribution controlReuseContribution :
      Index -> Unit -> Real)
    (score : Index -> Unit -> Cell)
    (target denominator normalizer : Real)
    (cellDenominatorWeight cellTreatedContribution
      cellControlReuseContribution : Index -> Cell -> Real)
    (denominatorWeightLimit treatedContributionLimit
      controlReuseContributionLimit massLimit : Cell -> Real)
    (multiplierWeightRegular bootstrapScoreReplicationConsistent
      bootstrapBiasCorrectionConsistent bootstrapVarianceConsistent : Prop)
    (bridge :
      (∀ index,
        retrospectivePATTBootstrapFiniteAlgebraVerified (sample index)
          (multiplier index) (denominatorWeight index)
          (treatedContribution index) (controlReuseContribution index)) ->
        multiplierWeightRegular ->
        bootstrapScoreReplicationConsistent ->
        bootstrapBiasCorrectionConsistent ->
        Tendsto
          (fun index =>
            bootstrapCenteredVarianceTarget (sample index)
              (retrospectivePATTBootstrapInfluenceContribution
                (treatedContribution index) (controlReuseContribution index))
              (denominatorWeight index) target denominator normalizer)
          l
          (nhds
            ((1 / denominator ^ 2) * (1 / normalizer) *
              weightedScoreCellMomentLimit cells
                (fun cell =>
                  (pattBootstrapScoreCellContribution
                        treatedContributionLimit
                        controlReuseContributionLimit cell -
                      target * denominatorWeightLimit cell) ^ 2)
                massLimit)) ->
        bootstrapVarianceConsistent)
    (hcover :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ sample index -> score index unit ∈ cells)
    (hdenominator :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ sample index ->
          cellDenominatorWeight index (score index unit) =
            denominatorWeight index unit)
    (htreated :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ sample index ->
          cellTreatedContribution index (score index unit) =
            treatedContribution index unit)
    (hcontrol :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ sample index ->
          cellControlReuseContribution index (score index unit) =
            controlReuseContribution index unit)
    (hdenominatorLimit :
      ∀ cell, cell ∈ cells ->
        Tendsto (fun index => cellDenominatorWeight index cell)
          l (nhds (denominatorWeightLimit cell)))
    (htreatedLimit :
      ∀ cell, cell ∈ cells ->
        Tendsto (fun index => cellTreatedContribution index cell)
          l (nhds (treatedContributionLimit cell)))
    (hcontrolLimit :
      ∀ cell, cell ∈ cells ->
        Tendsto (fun index => cellControlReuseContribution index cell)
          l (nhds (controlReuseContributionLimit cell)))
    (hmass :
      cellwiseScoreCellMassLLN (l := l) cells sample
        (fun _index _unit => 1) score massLimit)
    (hmultiplier : multiplierWeightRegular)
    (hscore : bootstrapScoreReplicationConsistent)
    (hbias : bootstrapBiasCorrectionConsistent) :
    bootstrapVarianceConsistent :=
  bootstrap_variance_consistency_of_eventually_finite_cell_contribution_weight_limits_direct
    (l := l) cells sample score
    (fun index =>
      retrospectivePATTBootstrapInfluenceContribution
        (treatedContribution index) (controlReuseContribution index))
    denominatorWeight target denominator normalizer
    (fun index =>
      pattBootstrapScoreCellContribution (cellTreatedContribution index)
        (cellControlReuseContribution index))
    cellDenominatorWeight
    (pattBootstrapScoreCellContribution treatedContributionLimit
      controlReuseContributionLimit)
    denominatorWeightLimit massLimit
    (∀ index,
      retrospectivePATTBootstrapFiniteAlgebraVerified (sample index)
        (multiplier index) (denominatorWeight index)
        (treatedContribution index) (controlReuseContribution index))
    multiplierWeightRegular bootstrapScoreReplicationConsistent
    bootstrapBiasCorrectionConsistent bootstrapVarianceConsistent bridge
    (fun index =>
      retrospectivePATTBootstrapFiniteAlgebraVerified_of_replicate_identities
        (sample index) (multiplier index) (denominatorWeight index)
        (treatedContribution index) (controlReuseContribution index))
    hcover
    (by
      filter_upwards [htreated, hcontrol] with index htreatedIndex
        hcontrolIndex unit hunit
      unfold pattBootstrapScoreCellContribution
        retrospectivePATTBootstrapInfluenceContribution
      rw [htreatedIndex unit hunit, hcontrolIndex unit hunit])
    hdenominator
    (tendsto_pattBootstrapScoreCellContribution_of_component_limits
      (l := l) cells cellTreatedContribution cellControlReuseContribution
      treatedContributionLimit controlReuseContributionLimit htreatedLimit
      hcontrolLimit)
    hdenominatorLimit hmass hmultiplier hscore hbias

/--
Prospective PATT bootstrap consistency from eventually valid component-level
score-cell representations and component limits.
-/
theorem prospective_patt_bootstrap_variance_consistency_of_eventually_score_cell_components_direct
    (cells : Finset Cell)
    (sample : Index -> Finset Unit)
    (multiplier denominatorWeight treatedContribution controlReuseContribution :
      Index -> Unit -> Real)
    (score : Index -> Unit -> Cell)
    (target denominator normalizer : Real)
    (cellDenominatorWeight cellTreatedContribution
      cellControlReuseContribution : Index -> Cell -> Real)
    (denominatorWeightLimit treatedContributionLimit
      controlReuseContributionLimit massLimit : Cell -> Real)
    (multiplierWeightRegular bootstrapScoreReplicationConsistent
      bootstrapBiasCorrectionConsistent bootstrapVarianceConsistent : Prop)
    (bridge :
      (∀ index,
        prospectivePATTBootstrapFiniteAlgebraVerified (sample index)
          (multiplier index) (denominatorWeight index)
          (treatedContribution index) (controlReuseContribution index)) ->
        multiplierWeightRegular ->
        bootstrapScoreReplicationConsistent ->
        bootstrapBiasCorrectionConsistent ->
        Tendsto
          (fun index =>
            bootstrapCenteredVarianceTarget (sample index)
              (prospectivePATTBootstrapInfluenceContribution
                (treatedContribution index) (controlReuseContribution index))
              (denominatorWeight index) target denominator normalizer)
          l
          (nhds
            ((1 / denominator ^ 2) * (1 / normalizer) *
              weightedScoreCellMomentLimit cells
                (fun cell =>
                  (pattBootstrapScoreCellContribution
                        treatedContributionLimit
                        controlReuseContributionLimit cell -
                      target * denominatorWeightLimit cell) ^ 2)
                massLimit)) ->
        bootstrapVarianceConsistent)
    (hcover :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ sample index -> score index unit ∈ cells)
    (hdenominator :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ sample index ->
          cellDenominatorWeight index (score index unit) =
            denominatorWeight index unit)
    (htreated :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ sample index ->
          cellTreatedContribution index (score index unit) =
            treatedContribution index unit)
    (hcontrol :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ sample index ->
          cellControlReuseContribution index (score index unit) =
            controlReuseContribution index unit)
    (hdenominatorLimit :
      ∀ cell, cell ∈ cells ->
        Tendsto (fun index => cellDenominatorWeight index cell)
          l (nhds (denominatorWeightLimit cell)))
    (htreatedLimit :
      ∀ cell, cell ∈ cells ->
        Tendsto (fun index => cellTreatedContribution index cell)
          l (nhds (treatedContributionLimit cell)))
    (hcontrolLimit :
      ∀ cell, cell ∈ cells ->
        Tendsto (fun index => cellControlReuseContribution index cell)
          l (nhds (controlReuseContributionLimit cell)))
    (hmass :
      cellwiseScoreCellMassLLN (l := l) cells sample
        (fun _index _unit => 1) score massLimit)
    (hmultiplier : multiplierWeightRegular)
    (hscore : bootstrapScoreReplicationConsistent)
    (hbias : bootstrapBiasCorrectionConsistent) :
    bootstrapVarianceConsistent :=
  bootstrap_variance_consistency_of_eventually_finite_cell_contribution_weight_limits_direct
    (l := l) cells sample score
    (fun index =>
      prospectivePATTBootstrapInfluenceContribution
        (treatedContribution index) (controlReuseContribution index))
    denominatorWeight target denominator normalizer
    (fun index =>
      pattBootstrapScoreCellContribution (cellTreatedContribution index)
        (cellControlReuseContribution index))
    cellDenominatorWeight
    (pattBootstrapScoreCellContribution treatedContributionLimit
      controlReuseContributionLimit)
    denominatorWeightLimit massLimit
    (∀ index,
      prospectivePATTBootstrapFiniteAlgebraVerified (sample index)
        (multiplier index) (denominatorWeight index)
        (treatedContribution index) (controlReuseContribution index))
    multiplierWeightRegular bootstrapScoreReplicationConsistent
    bootstrapBiasCorrectionConsistent bootstrapVarianceConsistent bridge
    (fun index =>
      prospectivePATTBootstrapFiniteAlgebraVerified_of_replicate_identities
        (sample index) (multiplier index) (denominatorWeight index)
        (treatedContribution index) (controlReuseContribution index))
    hcover
    (by
      filter_upwards [htreated, hcontrol] with index htreatedIndex
        hcontrolIndex unit hunit
      unfold pattBootstrapScoreCellContribution
        prospectivePATTBootstrapInfluenceContribution
      rw [htreatedIndex unit hunit, hcontrolIndex unit hunit])
    hdenominator
    (tendsto_pattBootstrapScoreCellContribution_of_component_limits
      (l := l) cells cellTreatedContribution cellControlReuseContribution
      treatedContributionLimit controlReuseContributionLimit htreatedLimit
      hcontrolLimit)
    hdenominatorLimit hmass hmultiplier hscore hbias

/--
Paired retrospective PATE/PATT bootstrap consistency from eventually valid
component-level score-cell representations and component limits.
-/
theorem retrospective_pate_patt_bootstrap_variance_consistency_of_eventually_score_cell_components_direct
    (pateCells : Finset Cell)
    (pateSample : Index -> Finset Unit)
    (pateMultiplier pateBaseWeight pateReuseResidualWeight pateHeterogeneity
      pateResidual : Index -> Unit -> Real)
    (pateScore : Index -> Unit -> Cell)
    (pateTarget pateDenominator pateNormalizer : Real)
    (pateCellBaseWeight pateCellReuseResidualWeight pateCellHeterogeneity
      pateCellResidual : Index -> Cell -> Real)
    (pateBaseWeightLimit pateReuseResidualWeightLimit
      pateHeterogeneityLimit pateResidualLimit pateMassLimit : Cell -> Real)
    (pateMultiplierWeightRegular pateBootstrapScoreReplicationConsistent
      pateBootstrapBiasCorrectionConsistent pateBootstrapVarianceConsistent :
      Prop)
    (pateBridge :
      (∀ index,
        retrospectivePATEBootstrapFiniteAlgebraVerified (pateSample index)
          (pateMultiplier index) (pateBaseWeight index)
          (pateReuseResidualWeight index) (pateHeterogeneity index)
          (pateResidual index)) ->
        pateMultiplierWeightRegular ->
        pateBootstrapScoreReplicationConsistent ->
        pateBootstrapBiasCorrectionConsistent ->
        Tendsto
          (fun index =>
            bootstrapCenteredVarianceTarget (pateSample index)
              (retrospectivePATEBootstrapInfluenceContribution
                (pateBaseWeight index) (pateReuseResidualWeight index)
                (pateHeterogeneity index) (pateResidual index))
              (pateBaseWeight index) pateTarget pateDenominator
              pateNormalizer)
          l
          (nhds
            ((1 / pateDenominator ^ 2) * (1 / pateNormalizer) *
              weightedScoreCellMomentLimit pateCells
                (fun cell =>
                  (pateBootstrapScoreCellContribution pateBaseWeightLimit
                        pateReuseResidualWeightLimit pateHeterogeneityLimit
                        pateResidualLimit cell -
                      pateTarget * pateBaseWeightLimit cell) ^ 2)
                pateMassLimit)) ->
        pateBootstrapVarianceConsistent)
    (hpateCover :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ pateSample index ->
          pateScore index unit ∈ pateCells)
    (hpateBase :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ pateSample index ->
          pateCellBaseWeight index (pateScore index unit) =
            pateBaseWeight index unit)
    (hpateReuse :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ pateSample index ->
          pateCellReuseResidualWeight index (pateScore index unit) =
            pateReuseResidualWeight index unit)
    (hpateHeterogeneity :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ pateSample index ->
          pateCellHeterogeneity index (pateScore index unit) =
            pateHeterogeneity index unit)
    (hpateResidual :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ pateSample index ->
          pateCellResidual index (pateScore index unit) =
            pateResidual index unit)
    (hpateBaseLimit :
      ∀ cell, cell ∈ pateCells ->
        Tendsto (fun index => pateCellBaseWeight index cell)
          l (nhds (pateBaseWeightLimit cell)))
    (hpateReuseLimit :
      ∀ cell, cell ∈ pateCells ->
        Tendsto (fun index => pateCellReuseResidualWeight index cell)
          l (nhds (pateReuseResidualWeightLimit cell)))
    (hpateHeterogeneityLimit :
      ∀ cell, cell ∈ pateCells ->
        Tendsto (fun index => pateCellHeterogeneity index cell)
          l (nhds (pateHeterogeneityLimit cell)))
    (hpateResidualLimit :
      ∀ cell, cell ∈ pateCells ->
        Tendsto (fun index => pateCellResidual index cell)
          l (nhds (pateResidualLimit cell)))
    (hpateMass :
      cellwiseScoreCellMassLLN (l := l) pateCells pateSample
        (fun _index _unit => 1) pateScore pateMassLimit)
    (hpateMultiplier : pateMultiplierWeightRegular)
    (hpateScore : pateBootstrapScoreReplicationConsistent)
    (hpateBias : pateBootstrapBiasCorrectionConsistent)
    (pattCells : Finset Cell)
    (pattSample : Index -> Finset Unit)
    (pattMultiplier pattDenominatorWeight pattTreatedContribution
      pattControlReuseContribution : Index -> Unit -> Real)
    (pattScore : Index -> Unit -> Cell)
    (pattTarget pattDenominator pattNormalizer : Real)
    (pattCellDenominatorWeight pattCellTreatedContribution
      pattCellControlReuseContribution : Index -> Cell -> Real)
    (pattDenominatorWeightLimit pattTreatedContributionLimit
      pattControlReuseContributionLimit pattMassLimit : Cell -> Real)
    (pattMultiplierWeightRegular pattBootstrapScoreReplicationConsistent
      pattBootstrapBiasCorrectionConsistent pattBootstrapVarianceConsistent :
      Prop)
    (pattBridge :
      (∀ index,
        retrospectivePATTBootstrapFiniteAlgebraVerified (pattSample index)
          (pattMultiplier index) (pattDenominatorWeight index)
          (pattTreatedContribution index)
          (pattControlReuseContribution index)) ->
        pattMultiplierWeightRegular ->
        pattBootstrapScoreReplicationConsistent ->
        pattBootstrapBiasCorrectionConsistent ->
        Tendsto
          (fun index =>
            bootstrapCenteredVarianceTarget (pattSample index)
              (retrospectivePATTBootstrapInfluenceContribution
                (pattTreatedContribution index)
                (pattControlReuseContribution index))
              (pattDenominatorWeight index) pattTarget pattDenominator
              pattNormalizer)
          l
          (nhds
            ((1 / pattDenominator ^ 2) * (1 / pattNormalizer) *
              weightedScoreCellMomentLimit pattCells
                (fun cell =>
                  (pattBootstrapScoreCellContribution
                        pattTreatedContributionLimit
                        pattControlReuseContributionLimit cell -
                      pattTarget * pattDenominatorWeightLimit cell) ^ 2)
                pattMassLimit)) ->
        pattBootstrapVarianceConsistent)
    (hpattCover :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ pattSample index ->
          pattScore index unit ∈ pattCells)
    (hpattDenominator :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ pattSample index ->
          pattCellDenominatorWeight index (pattScore index unit) =
            pattDenominatorWeight index unit)
    (hpattTreated :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ pattSample index ->
          pattCellTreatedContribution index (pattScore index unit) =
            pattTreatedContribution index unit)
    (hpattControl :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ pattSample index ->
          pattCellControlReuseContribution index (pattScore index unit) =
            pattControlReuseContribution index unit)
    (hpattDenominatorLimit :
      ∀ cell, cell ∈ pattCells ->
        Tendsto (fun index => pattCellDenominatorWeight index cell)
          l (nhds (pattDenominatorWeightLimit cell)))
    (hpattTreatedLimit :
      ∀ cell, cell ∈ pattCells ->
        Tendsto (fun index => pattCellTreatedContribution index cell)
          l (nhds (pattTreatedContributionLimit cell)))
    (hpattControlLimit :
      ∀ cell, cell ∈ pattCells ->
        Tendsto (fun index => pattCellControlReuseContribution index cell)
          l (nhds (pattControlReuseContributionLimit cell)))
    (hpattMass :
      cellwiseScoreCellMassLLN (l := l) pattCells pattSample
        (fun _index _unit => 1) pattScore pattMassLimit)
    (hpattMultiplier : pattMultiplierWeightRegular)
    (hpattScore : pattBootstrapScoreReplicationConsistent)
    (hpattBias : pattBootstrapBiasCorrectionConsistent) :
    pateBootstrapVarianceConsistent ∧ pattBootstrapVarianceConsistent := by
  constructor
  · exact
      retrospective_pate_bootstrap_variance_consistency_of_eventually_score_cell_components_direct
        (l := l) pateCells pateSample pateMultiplier pateBaseWeight
        pateReuseResidualWeight pateHeterogeneity pateResidual pateScore
        pateTarget pateDenominator pateNormalizer pateCellBaseWeight
        pateCellReuseResidualWeight pateCellHeterogeneity pateCellResidual
        pateBaseWeightLimit pateReuseResidualWeightLimit
        pateHeterogeneityLimit pateResidualLimit pateMassLimit
        pateMultiplierWeightRegular pateBootstrapScoreReplicationConsistent
        pateBootstrapBiasCorrectionConsistent pateBootstrapVarianceConsistent
        pateBridge hpateCover hpateBase hpateReuse hpateHeterogeneity
        hpateResidual hpateBaseLimit hpateReuseLimit hpateHeterogeneityLimit
        hpateResidualLimit hpateMass hpateMultiplier hpateScore hpateBias
  · exact
      retrospective_patt_bootstrap_variance_consistency_of_eventually_score_cell_components_direct
        (l := l) pattCells pattSample pattMultiplier pattDenominatorWeight
        pattTreatedContribution pattControlReuseContribution pattScore
        pattTarget pattDenominator pattNormalizer pattCellDenominatorWeight
        pattCellTreatedContribution pattCellControlReuseContribution
        pattDenominatorWeightLimit pattTreatedContributionLimit
        pattControlReuseContributionLimit pattMassLimit
        pattMultiplierWeightRegular pattBootstrapScoreReplicationConsistent
        pattBootstrapBiasCorrectionConsistent pattBootstrapVarianceConsistent
        pattBridge hpattCover hpattDenominator hpattTreated hpattControl
        hpattDenominatorLimit hpattTreatedLimit hpattControlLimit hpattMass
        hpattMultiplier hpattScore hpattBias

/--
Paired prospective PATE/PATT bootstrap consistency from eventually valid
component-level score-cell representations and component limits.
-/
theorem prospective_pate_patt_bootstrap_variance_consistency_of_eventually_score_cell_components_direct
    (pateCells : Finset Cell)
    (pateSample : Index -> Finset Unit)
    (pateMultiplier pateBaseWeight pateReuseResidualWeight pateHeterogeneity
      pateResidual : Index -> Unit -> Real)
    (pateScore : Index -> Unit -> Cell)
    (pateTarget pateDenominator pateNormalizer : Real)
    (pateCellBaseWeight pateCellReuseResidualWeight pateCellHeterogeneity
      pateCellResidual : Index -> Cell -> Real)
    (pateBaseWeightLimit pateReuseResidualWeightLimit
      pateHeterogeneityLimit pateResidualLimit pateMassLimit : Cell -> Real)
    (pateMultiplierWeightRegular pateBootstrapScoreReplicationConsistent
      pateBootstrapBiasCorrectionConsistent pateBootstrapVarianceConsistent :
      Prop)
    (pateBridge :
      (∀ index,
        prospectivePATEBootstrapFiniteAlgebraVerified (pateSample index)
          (pateMultiplier index) (pateBaseWeight index)
          (pateReuseResidualWeight index) (pateHeterogeneity index)
          (pateResidual index)) ->
        pateMultiplierWeightRegular ->
        pateBootstrapScoreReplicationConsistent ->
        pateBootstrapBiasCorrectionConsistent ->
        Tendsto
          (fun index =>
            bootstrapCenteredVarianceTarget (pateSample index)
              (prospectivePATEBootstrapInfluenceContribution
                (pateBaseWeight index) (pateReuseResidualWeight index)
                (pateHeterogeneity index) (pateResidual index))
              (pateBaseWeight index) pateTarget pateDenominator
              pateNormalizer)
          l
          (nhds
            ((1 / pateDenominator ^ 2) * (1 / pateNormalizer) *
              weightedScoreCellMomentLimit pateCells
                (fun cell =>
                  (pateBootstrapScoreCellContribution pateBaseWeightLimit
                        pateReuseResidualWeightLimit pateHeterogeneityLimit
                        pateResidualLimit cell -
                      pateTarget * pateBaseWeightLimit cell) ^ 2)
                pateMassLimit)) ->
        pateBootstrapVarianceConsistent)
    (hpateCover :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ pateSample index ->
          pateScore index unit ∈ pateCells)
    (hpateBase :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ pateSample index ->
          pateCellBaseWeight index (pateScore index unit) =
            pateBaseWeight index unit)
    (hpateReuse :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ pateSample index ->
          pateCellReuseResidualWeight index (pateScore index unit) =
            pateReuseResidualWeight index unit)
    (hpateHeterogeneity :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ pateSample index ->
          pateCellHeterogeneity index (pateScore index unit) =
            pateHeterogeneity index unit)
    (hpateResidual :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ pateSample index ->
          pateCellResidual index (pateScore index unit) =
            pateResidual index unit)
    (hpateBaseLimit :
      ∀ cell, cell ∈ pateCells ->
        Tendsto (fun index => pateCellBaseWeight index cell)
          l (nhds (pateBaseWeightLimit cell)))
    (hpateReuseLimit :
      ∀ cell, cell ∈ pateCells ->
        Tendsto (fun index => pateCellReuseResidualWeight index cell)
          l (nhds (pateReuseResidualWeightLimit cell)))
    (hpateHeterogeneityLimit :
      ∀ cell, cell ∈ pateCells ->
        Tendsto (fun index => pateCellHeterogeneity index cell)
          l (nhds (pateHeterogeneityLimit cell)))
    (hpateResidualLimit :
      ∀ cell, cell ∈ pateCells ->
        Tendsto (fun index => pateCellResidual index cell)
          l (nhds (pateResidualLimit cell)))
    (hpateMass :
      cellwiseScoreCellMassLLN (l := l) pateCells pateSample
        (fun _index _unit => 1) pateScore pateMassLimit)
    (hpateMultiplier : pateMultiplierWeightRegular)
    (hpateScore : pateBootstrapScoreReplicationConsistent)
    (hpateBias : pateBootstrapBiasCorrectionConsistent)
    (pattCells : Finset Cell)
    (pattSample : Index -> Finset Unit)
    (pattMultiplier pattDenominatorWeight pattTreatedContribution
      pattControlReuseContribution : Index -> Unit -> Real)
    (pattScore : Index -> Unit -> Cell)
    (pattTarget pattDenominator pattNormalizer : Real)
    (pattCellDenominatorWeight pattCellTreatedContribution
      pattCellControlReuseContribution : Index -> Cell -> Real)
    (pattDenominatorWeightLimit pattTreatedContributionLimit
      pattControlReuseContributionLimit pattMassLimit : Cell -> Real)
    (pattMultiplierWeightRegular pattBootstrapScoreReplicationConsistent
      pattBootstrapBiasCorrectionConsistent pattBootstrapVarianceConsistent :
      Prop)
    (pattBridge :
      (∀ index,
        prospectivePATTBootstrapFiniteAlgebraVerified (pattSample index)
          (pattMultiplier index) (pattDenominatorWeight index)
          (pattTreatedContribution index)
          (pattControlReuseContribution index)) ->
        pattMultiplierWeightRegular ->
        pattBootstrapScoreReplicationConsistent ->
        pattBootstrapBiasCorrectionConsistent ->
        Tendsto
          (fun index =>
            bootstrapCenteredVarianceTarget (pattSample index)
              (prospectivePATTBootstrapInfluenceContribution
                (pattTreatedContribution index)
                (pattControlReuseContribution index))
              (pattDenominatorWeight index) pattTarget pattDenominator
              pattNormalizer)
          l
          (nhds
            ((1 / pattDenominator ^ 2) * (1 / pattNormalizer) *
              weightedScoreCellMomentLimit pattCells
                (fun cell =>
                  (pattBootstrapScoreCellContribution
                        pattTreatedContributionLimit
                        pattControlReuseContributionLimit cell -
                      pattTarget * pattDenominatorWeightLimit cell) ^ 2)
                pattMassLimit)) ->
        pattBootstrapVarianceConsistent)
    (hpattCover :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ pattSample index ->
          pattScore index unit ∈ pattCells)
    (hpattDenominator :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ pattSample index ->
          pattCellDenominatorWeight index (pattScore index unit) =
            pattDenominatorWeight index unit)
    (hpattTreated :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ pattSample index ->
          pattCellTreatedContribution index (pattScore index unit) =
            pattTreatedContribution index unit)
    (hpattControl :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ pattSample index ->
          pattCellControlReuseContribution index (pattScore index unit) =
            pattControlReuseContribution index unit)
    (hpattDenominatorLimit :
      ∀ cell, cell ∈ pattCells ->
        Tendsto (fun index => pattCellDenominatorWeight index cell)
          l (nhds (pattDenominatorWeightLimit cell)))
    (hpattTreatedLimit :
      ∀ cell, cell ∈ pattCells ->
        Tendsto (fun index => pattCellTreatedContribution index cell)
          l (nhds (pattTreatedContributionLimit cell)))
    (hpattControlLimit :
      ∀ cell, cell ∈ pattCells ->
        Tendsto (fun index => pattCellControlReuseContribution index cell)
          l (nhds (pattControlReuseContributionLimit cell)))
    (hpattMass :
      cellwiseScoreCellMassLLN (l := l) pattCells pattSample
        (fun _index _unit => 1) pattScore pattMassLimit)
    (hpattMultiplier : pattMultiplierWeightRegular)
    (hpattScore : pattBootstrapScoreReplicationConsistent)
    (hpattBias : pattBootstrapBiasCorrectionConsistent) :
    pateBootstrapVarianceConsistent ∧ pattBootstrapVarianceConsistent := by
  constructor
  · exact
      prospective_pate_bootstrap_variance_consistency_of_eventually_score_cell_components_direct
        (l := l) pateCells pateSample pateMultiplier pateBaseWeight
        pateReuseResidualWeight pateHeterogeneity pateResidual pateScore
        pateTarget pateDenominator pateNormalizer pateCellBaseWeight
        pateCellReuseResidualWeight pateCellHeterogeneity pateCellResidual
        pateBaseWeightLimit pateReuseResidualWeightLimit
        pateHeterogeneityLimit pateResidualLimit pateMassLimit
        pateMultiplierWeightRegular pateBootstrapScoreReplicationConsistent
        pateBootstrapBiasCorrectionConsistent pateBootstrapVarianceConsistent
        pateBridge hpateCover hpateBase hpateReuse hpateHeterogeneity
        hpateResidual hpateBaseLimit hpateReuseLimit hpateHeterogeneityLimit
        hpateResidualLimit hpateMass hpateMultiplier hpateScore hpateBias
  · exact
      prospective_patt_bootstrap_variance_consistency_of_eventually_score_cell_components_direct
        (l := l) pattCells pattSample pattMultiplier pattDenominatorWeight
        pattTreatedContribution pattControlReuseContribution pattScore
        pattTarget pattDenominator pattNormalizer pattCellDenominatorWeight
        pattCellTreatedContribution pattCellControlReuseContribution
        pattDenominatorWeightLimit pattTreatedContributionLimit
        pattControlReuseContributionLimit pattMassLimit
        pattMultiplierWeightRegular pattBootstrapScoreReplicationConsistent
        pattBootstrapBiasCorrectionConsistent pattBootstrapVarianceConsistent
        pattBridge hpattCover hpattDenominator hpattTreated hpattControl
        hpattDenominatorLimit hpattTreatedLimit hpattControlLimit hpattMass
        hpattMultiplier hpattScore hpattBias

end WDSM
end Matching
end StatInference
