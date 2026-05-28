import Mathlib.Data.Finset.Basic
import Mathlib.Topology.Basic
import StatInference.Matching.WDSM.BootstrapActualVarianceConsistency
import StatInference.Matching.WDSM.BootstrapScoreCellContributionBridge

/-!
# Scenario actual bootstrap variance consistency from score cells

This module connects the actual scalar bootstrap variance convergence theorem
to the PATE/PATT score-cell contribution adapters.  It proves that
component-level score-cell representations and limits are enough to feed the
actual-variance stability bridge once score-replication and bias-correction
errors are negligible.
-/

namespace StatInference
namespace Matching
namespace WDSM

open Filter

variable {Index Unit Cell : Type*} {l : Filter Index} [DecidableEq Cell]

/--
Retrospective PATE actual bootstrap variance convergence from component-level
score-cell representations and negligible score/bias errors.
-/
theorem retrospective_pate_actualBootstrapVariance_tendsto_of_score_cell_components
    (cells : Finset Cell)
    (sample : Index -> Finset Unit)
    (baseWeight reuseResidualWeight heterogeneity residual :
      Index -> Unit -> Real)
    (score : Index -> Unit -> Cell)
    (target denominator normalizer : Real)
    (cellBaseWeight cellReuseResidualWeight cellHeterogeneity cellResidual :
      Index -> Cell -> Real)
    (baseWeightLimit reuseResidualWeightLimit heterogeneityLimit
      residualLimit massLimit : Cell -> Real)
    (actualVariance scoreReplicationError biasCorrectionError : Index -> Real)
    (herror_decomp :
      (fun index =>
        actualVariance index -
          bootstrapCenteredVarianceTarget (sample index)
            (retrospectivePATEBootstrapInfluenceContribution
              (baseWeight index) (reuseResidualWeight index)
              (heterogeneity index) (residual index))
            (baseWeight index) target denominator normalizer) =ᶠ[l]
        (fun index =>
          scoreReplicationError index + biasCorrectionError index))
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
    (hscore :
      bootstrapScoreReplicationErrorNegligible
        (l := l) scoreReplicationError)
    (hbias :
      bootstrapBiasCorrectionErrorNegligible
        (l := l) biasCorrectionError) :
    Tendsto actualVariance l
      (nhds
        ((1 / denominator ^ 2) * (1 / normalizer) *
          weightedScoreCellMomentLimit cells
            (fun cell =>
              (pateBootstrapScoreCellContribution baseWeightLimit
                    reuseResidualWeightLimit heterogeneityLimit
                    residualLimit cell -
                  target * baseWeightLimit cell) ^ 2)
            massLimit)) :=
  tendsto_actualBootstrapVariance_of_cell_contribution_weight_limits_and_error_stability
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
    baseWeightLimit massLimit actualVariance scoreReplicationError
    biasCorrectionError herror_decomp hcover
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
    hbaseLimit hmass hscore hbias

/--
Prospective PATE actual bootstrap variance convergence from component-level
score-cell representations and negligible score/bias errors.
-/
theorem prospective_pate_actualBootstrapVariance_tendsto_of_score_cell_components
    (cells : Finset Cell)
    (sample : Index -> Finset Unit)
    (baseWeight reuseResidualWeight heterogeneity residual :
      Index -> Unit -> Real)
    (score : Index -> Unit -> Cell)
    (target denominator normalizer : Real)
    (cellBaseWeight cellReuseResidualWeight cellHeterogeneity cellResidual :
      Index -> Cell -> Real)
    (baseWeightLimit reuseResidualWeightLimit heterogeneityLimit
      residualLimit massLimit : Cell -> Real)
    (actualVariance scoreReplicationError biasCorrectionError : Index -> Real)
    (herror_decomp :
      (fun index =>
        actualVariance index -
          bootstrapCenteredVarianceTarget (sample index)
            (prospectivePATEBootstrapInfluenceContribution
              (baseWeight index) (reuseResidualWeight index)
              (heterogeneity index) (residual index))
            (baseWeight index) target denominator normalizer) =ᶠ[l]
        (fun index =>
          scoreReplicationError index + biasCorrectionError index))
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
    (hscore :
      bootstrapScoreReplicationErrorNegligible
        (l := l) scoreReplicationError)
    (hbias :
      bootstrapBiasCorrectionErrorNegligible
        (l := l) biasCorrectionError) :
    Tendsto actualVariance l
      (nhds
        ((1 / denominator ^ 2) * (1 / normalizer) *
          weightedScoreCellMomentLimit cells
            (fun cell =>
              (pateBootstrapScoreCellContribution baseWeightLimit
                    reuseResidualWeightLimit heterogeneityLimit
                    residualLimit cell -
                  target * baseWeightLimit cell) ^ 2)
            massLimit)) :=
  tendsto_actualBootstrapVariance_of_cell_contribution_weight_limits_and_error_stability
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
    baseWeightLimit massLimit actualVariance scoreReplicationError
    biasCorrectionError herror_decomp hcover
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
    hbaseLimit hmass hscore hbias

/--
Retrospective PATT actual bootstrap variance convergence from component-level
score-cell representations and negligible score/bias errors.
-/
theorem retrospective_patt_actualBootstrapVariance_tendsto_of_score_cell_components
    (cells : Finset Cell)
    (sample : Index -> Finset Unit)
    (denominatorWeight treatedContribution controlReuseContribution :
      Index -> Unit -> Real)
    (score : Index -> Unit -> Cell)
    (target denominator normalizer : Real)
    (cellDenominatorWeight cellTreatedContribution
      cellControlReuseContribution : Index -> Cell -> Real)
    (denominatorWeightLimit treatedContributionLimit
      controlReuseContributionLimit massLimit : Cell -> Real)
    (actualVariance scoreReplicationError biasCorrectionError : Index -> Real)
    (herror_decomp :
      (fun index =>
        actualVariance index -
          bootstrapCenteredVarianceTarget (sample index)
            (retrospectivePATTBootstrapInfluenceContribution
              (treatedContribution index) (controlReuseContribution index))
            (denominatorWeight index) target denominator normalizer) =ᶠ[l]
        (fun index =>
          scoreReplicationError index + biasCorrectionError index))
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
    (hscore :
      bootstrapScoreReplicationErrorNegligible
        (l := l) scoreReplicationError)
    (hbias :
      bootstrapBiasCorrectionErrorNegligible
        (l := l) biasCorrectionError) :
    Tendsto actualVariance l
      (nhds
        ((1 / denominator ^ 2) * (1 / normalizer) *
          weightedScoreCellMomentLimit cells
            (fun cell =>
              (pattBootstrapScoreCellContribution treatedContributionLimit
                    controlReuseContributionLimit cell -
                  target * denominatorWeightLimit cell) ^ 2)
            massLimit)) :=
  tendsto_actualBootstrapVariance_of_cell_contribution_weight_limits_and_error_stability
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
    denominatorWeightLimit massLimit actualVariance scoreReplicationError
    biasCorrectionError herror_decomp hcover
    (retrospective_patt_bootstrap_cellContribution_eq_of_score_components
      sample score treatedContribution controlReuseContribution
      cellTreatedContribution cellControlReuseContribution htreated hcontrol)
    hdenominator
    (tendsto_pattBootstrapScoreCellContribution_of_component_limits
      (l := l) cells cellTreatedContribution cellControlReuseContribution
      treatedContributionLimit controlReuseContributionLimit htreatedLimit
      hcontrolLimit)
    hdenominatorLimit hmass hscore hbias

/--
Prospective PATT actual bootstrap variance convergence from component-level
score-cell representations and negligible score/bias errors.
-/
theorem prospective_patt_actualBootstrapVariance_tendsto_of_score_cell_components
    (cells : Finset Cell)
    (sample : Index -> Finset Unit)
    (denominatorWeight treatedContribution controlReuseContribution :
      Index -> Unit -> Real)
    (score : Index -> Unit -> Cell)
    (target denominator normalizer : Real)
    (cellDenominatorWeight cellTreatedContribution
      cellControlReuseContribution : Index -> Cell -> Real)
    (denominatorWeightLimit treatedContributionLimit
      controlReuseContributionLimit massLimit : Cell -> Real)
    (actualVariance scoreReplicationError biasCorrectionError : Index -> Real)
    (herror_decomp :
      (fun index =>
        actualVariance index -
          bootstrapCenteredVarianceTarget (sample index)
            (prospectivePATTBootstrapInfluenceContribution
              (treatedContribution index) (controlReuseContribution index))
            (denominatorWeight index) target denominator normalizer) =ᶠ[l]
        (fun index =>
          scoreReplicationError index + biasCorrectionError index))
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
    (hscore :
      bootstrapScoreReplicationErrorNegligible
        (l := l) scoreReplicationError)
    (hbias :
      bootstrapBiasCorrectionErrorNegligible
        (l := l) biasCorrectionError) :
    Tendsto actualVariance l
      (nhds
        ((1 / denominator ^ 2) * (1 / normalizer) *
          weightedScoreCellMomentLimit cells
            (fun cell =>
              (pattBootstrapScoreCellContribution treatedContributionLimit
                    controlReuseContributionLimit cell -
                  target * denominatorWeightLimit cell) ^ 2)
            massLimit)) :=
  tendsto_actualBootstrapVariance_of_cell_contribution_weight_limits_and_error_stability
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
    denominatorWeightLimit massLimit actualVariance scoreReplicationError
    biasCorrectionError herror_decomp hcover
    (prospective_patt_bootstrap_cellContribution_eq_of_score_components
      sample score treatedContribution controlReuseContribution
      cellTreatedContribution cellControlReuseContribution htreated hcontrol)
    hdenominator
    (tendsto_pattBootstrapScoreCellContribution_of_component_limits
      (l := l) cells cellTreatedContribution cellControlReuseContribution
      treatedContributionLimit controlReuseContributionLimit htreatedLimit
      hcontrolLimit)
    hdenominatorLimit hmass hscore hbias

/--
Paired retrospective PATE/PATT actual bootstrap variance convergence from
component-level score-cell representations and negligible score/bias errors.
-/
theorem retrospective_pate_patt_actualBootstrapVariance_tendsto_of_score_cell_components
    (pateCells : Finset Cell)
    (pateSample : Index -> Finset Unit)
    (pateBaseWeight pateReuseResidualWeight pateHeterogeneity pateResidual :
      Index -> Unit -> Real)
    (pateScore : Index -> Unit -> Cell)
    (pateTarget pateDenominator pateNormalizer : Real)
    (pateCellBaseWeight pateCellReuseResidualWeight pateCellHeterogeneity
      pateCellResidual : Index -> Cell -> Real)
    (pateBaseWeightLimit pateReuseResidualWeightLimit
      pateHeterogeneityLimit pateResidualLimit pateMassLimit : Cell -> Real)
    (pateActualVariance pateScoreReplicationError pateBiasCorrectionError :
      Index -> Real)
    (hpateErrorDecomp :
      (fun index =>
        pateActualVariance index -
          bootstrapCenteredVarianceTarget (pateSample index)
            (retrospectivePATEBootstrapInfluenceContribution
              (pateBaseWeight index) (pateReuseResidualWeight index)
              (pateHeterogeneity index) (pateResidual index))
            (pateBaseWeight index) pateTarget pateDenominator
            pateNormalizer) =ᶠ[l]
        (fun index =>
          pateScoreReplicationError index + pateBiasCorrectionError index))
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
    (hpateScoreError :
      bootstrapScoreReplicationErrorNegligible
        (l := l) pateScoreReplicationError)
    (hpateBiasError :
      bootstrapBiasCorrectionErrorNegligible
        (l := l) pateBiasCorrectionError)
    (pattCells : Finset Cell)
    (pattSample : Index -> Finset Unit)
    (pattDenominatorWeight pattTreatedContribution
      pattControlReuseContribution : Index -> Unit -> Real)
    (pattScore : Index -> Unit -> Cell)
    (pattTarget pattDenominator pattNormalizer : Real)
    (pattCellDenominatorWeight pattCellTreatedContribution
      pattCellControlReuseContribution : Index -> Cell -> Real)
    (pattDenominatorWeightLimit pattTreatedContributionLimit
      pattControlReuseContributionLimit pattMassLimit : Cell -> Real)
    (pattActualVariance pattScoreReplicationError pattBiasCorrectionError :
      Index -> Real)
    (hpattErrorDecomp :
      (fun index =>
        pattActualVariance index -
          bootstrapCenteredVarianceTarget (pattSample index)
            (retrospectivePATTBootstrapInfluenceContribution
              (pattTreatedContribution index)
              (pattControlReuseContribution index))
            (pattDenominatorWeight index) pattTarget pattDenominator
            pattNormalizer) =ᶠ[l]
        (fun index =>
          pattScoreReplicationError index + pattBiasCorrectionError index))
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
    (hpattScoreError :
      bootstrapScoreReplicationErrorNegligible
        (l := l) pattScoreReplicationError)
    (hpattBiasError :
      bootstrapBiasCorrectionErrorNegligible
        (l := l) pattBiasCorrectionError) :
    Tendsto pateActualVariance l
      (nhds
        ((1 / pateDenominator ^ 2) * (1 / pateNormalizer) *
          weightedScoreCellMomentLimit pateCells
            (fun cell =>
              (pateBootstrapScoreCellContribution pateBaseWeightLimit
                    pateReuseResidualWeightLimit pateHeterogeneityLimit
                    pateResidualLimit cell -
                  pateTarget * pateBaseWeightLimit cell) ^ 2)
            pateMassLimit)) ∧
      Tendsto pattActualVariance l
        (nhds
          ((1 / pattDenominator ^ 2) * (1 / pattNormalizer) *
            weightedScoreCellMomentLimit pattCells
              (fun cell =>
                (pattBootstrapScoreCellContribution
                      pattTreatedContributionLimit
                      pattControlReuseContributionLimit cell -
                    pattTarget * pattDenominatorWeightLimit cell) ^ 2)
              pattMassLimit)) := by
  constructor
  · exact
      retrospective_pate_actualBootstrapVariance_tendsto_of_score_cell_components
        (l := l) pateCells pateSample pateBaseWeight
        pateReuseResidualWeight pateHeterogeneity pateResidual pateScore
        pateTarget pateDenominator pateNormalizer pateCellBaseWeight
        pateCellReuseResidualWeight pateCellHeterogeneity pateCellResidual
        pateBaseWeightLimit pateReuseResidualWeightLimit
        pateHeterogeneityLimit pateResidualLimit pateMassLimit
        pateActualVariance pateScoreReplicationError pateBiasCorrectionError
        hpateErrorDecomp hpateCover hpateBase hpateReuse hpateHeterogeneity
        hpateResidual hpateBaseLimit hpateReuseLimit hpateHeterogeneityLimit
        hpateResidualLimit hpateMass hpateScoreError hpateBiasError
  · exact
      retrospective_patt_actualBootstrapVariance_tendsto_of_score_cell_components
        (l := l) pattCells pattSample pattDenominatorWeight
        pattTreatedContribution pattControlReuseContribution pattScore
        pattTarget pattDenominator pattNormalizer pattCellDenominatorWeight
        pattCellTreatedContribution pattCellControlReuseContribution
        pattDenominatorWeightLimit pattTreatedContributionLimit
        pattControlReuseContributionLimit pattMassLimit pattActualVariance
        pattScoreReplicationError pattBiasCorrectionError hpattErrorDecomp
        hpattCover hpattDenominator hpattTreated hpattControl
        hpattDenominatorLimit hpattTreatedLimit hpattControlLimit hpattMass
        hpattScoreError hpattBiasError

/--
Paired prospective PATE/PATT actual bootstrap variance convergence from
component-level score-cell representations and negligible score/bias errors.
-/
theorem prospective_pate_patt_actualBootstrapVariance_tendsto_of_score_cell_components
    (pateCells : Finset Cell)
    (pateSample : Index -> Finset Unit)
    (pateBaseWeight pateReuseResidualWeight pateHeterogeneity pateResidual :
      Index -> Unit -> Real)
    (pateScore : Index -> Unit -> Cell)
    (pateTarget pateDenominator pateNormalizer : Real)
    (pateCellBaseWeight pateCellReuseResidualWeight pateCellHeterogeneity
      pateCellResidual : Index -> Cell -> Real)
    (pateBaseWeightLimit pateReuseResidualWeightLimit
      pateHeterogeneityLimit pateResidualLimit pateMassLimit : Cell -> Real)
    (pateActualVariance pateScoreReplicationError pateBiasCorrectionError :
      Index -> Real)
    (hpateErrorDecomp :
      (fun index =>
        pateActualVariance index -
          bootstrapCenteredVarianceTarget (pateSample index)
            (prospectivePATEBootstrapInfluenceContribution
              (pateBaseWeight index) (pateReuseResidualWeight index)
              (pateHeterogeneity index) (pateResidual index))
            (pateBaseWeight index) pateTarget pateDenominator
            pateNormalizer) =ᶠ[l]
        (fun index =>
          pateScoreReplicationError index + pateBiasCorrectionError index))
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
    (hpateScoreError :
      bootstrapScoreReplicationErrorNegligible
        (l := l) pateScoreReplicationError)
    (hpateBiasError :
      bootstrapBiasCorrectionErrorNegligible
        (l := l) pateBiasCorrectionError)
    (pattCells : Finset Cell)
    (pattSample : Index -> Finset Unit)
    (pattDenominatorWeight pattTreatedContribution
      pattControlReuseContribution : Index -> Unit -> Real)
    (pattScore : Index -> Unit -> Cell)
    (pattTarget pattDenominator pattNormalizer : Real)
    (pattCellDenominatorWeight pattCellTreatedContribution
      pattCellControlReuseContribution : Index -> Cell -> Real)
    (pattDenominatorWeightLimit pattTreatedContributionLimit
      pattControlReuseContributionLimit pattMassLimit : Cell -> Real)
    (pattActualVariance pattScoreReplicationError pattBiasCorrectionError :
      Index -> Real)
    (hpattErrorDecomp :
      (fun index =>
        pattActualVariance index -
          bootstrapCenteredVarianceTarget (pattSample index)
            (prospectivePATTBootstrapInfluenceContribution
              (pattTreatedContribution index)
              (pattControlReuseContribution index))
            (pattDenominatorWeight index) pattTarget pattDenominator
            pattNormalizer) =ᶠ[l]
        (fun index =>
          pattScoreReplicationError index + pattBiasCorrectionError index))
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
    (hpattScoreError :
      bootstrapScoreReplicationErrorNegligible
        (l := l) pattScoreReplicationError)
    (hpattBiasError :
      bootstrapBiasCorrectionErrorNegligible
        (l := l) pattBiasCorrectionError) :
    Tendsto pateActualVariance l
      (nhds
        ((1 / pateDenominator ^ 2) * (1 / pateNormalizer) *
          weightedScoreCellMomentLimit pateCells
            (fun cell =>
              (pateBootstrapScoreCellContribution pateBaseWeightLimit
                    pateReuseResidualWeightLimit pateHeterogeneityLimit
                    pateResidualLimit cell -
                  pateTarget * pateBaseWeightLimit cell) ^ 2)
            pateMassLimit)) ∧
      Tendsto pattActualVariance l
        (nhds
          ((1 / pattDenominator ^ 2) * (1 / pattNormalizer) *
            weightedScoreCellMomentLimit pattCells
              (fun cell =>
                (pattBootstrapScoreCellContribution
                      pattTreatedContributionLimit
                      pattControlReuseContributionLimit cell -
                    pattTarget * pattDenominatorWeightLimit cell) ^ 2)
              pattMassLimit)) := by
  constructor
  · exact
      prospective_pate_actualBootstrapVariance_tendsto_of_score_cell_components
        (l := l) pateCells pateSample pateBaseWeight
        pateReuseResidualWeight pateHeterogeneity pateResidual pateScore
        pateTarget pateDenominator pateNormalizer pateCellBaseWeight
        pateCellReuseResidualWeight pateCellHeterogeneity pateCellResidual
        pateBaseWeightLimit pateReuseResidualWeightLimit
        pateHeterogeneityLimit pateResidualLimit pateMassLimit
        pateActualVariance pateScoreReplicationError pateBiasCorrectionError
        hpateErrorDecomp hpateCover hpateBase hpateReuse hpateHeterogeneity
        hpateResidual hpateBaseLimit hpateReuseLimit hpateHeterogeneityLimit
        hpateResidualLimit hpateMass hpateScoreError hpateBiasError
  · exact
      prospective_patt_actualBootstrapVariance_tendsto_of_score_cell_components
        (l := l) pattCells pattSample pattDenominatorWeight
        pattTreatedContribution pattControlReuseContribution pattScore
        pattTarget pattDenominator pattNormalizer pattCellDenominatorWeight
        pattCellTreatedContribution pattCellControlReuseContribution
        pattDenominatorWeightLimit pattTreatedContributionLimit
        pattControlReuseContributionLimit pattMassLimit pattActualVariance
        pattScoreReplicationError pattBiasCorrectionError hpattErrorDecomp
        hpattCover hpattDenominator hpattTreated hpattControl
        hpattDenominatorLimit hpattTreatedLimit hpattControlLimit hpattMass
        hpattScoreError hpattBiasError

/--
Retrospective PATE actual bootstrap variance convergence from eventually valid
component-level score-cell representations.
-/
theorem retrospective_pate_actualBootstrapVariance_tendsto_of_eventually_score_cell_components
    (cells : Finset Cell)
    (sample : Index -> Finset Unit)
    (baseWeight reuseResidualWeight heterogeneity residual :
      Index -> Unit -> Real)
    (score : Index -> Unit -> Cell)
    (target denominator normalizer : Real)
    (cellBaseWeight cellReuseResidualWeight cellHeterogeneity cellResidual :
      Index -> Cell -> Real)
    (baseWeightLimit reuseResidualWeightLimit heterogeneityLimit
      residualLimit massLimit : Cell -> Real)
    (actualVariance scoreReplicationError biasCorrectionError : Index -> Real)
    (herror_decomp :
      (fun index =>
        actualVariance index -
          bootstrapCenteredVarianceTarget (sample index)
            (retrospectivePATEBootstrapInfluenceContribution
              (baseWeight index) (reuseResidualWeight index)
              (heterogeneity index) (residual index))
            (baseWeight index) target denominator normalizer) =ᶠ[l]
        (fun index =>
          scoreReplicationError index + biasCorrectionError index))
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
    (hscore :
      bootstrapScoreReplicationErrorNegligible
        (l := l) scoreReplicationError)
    (hbias :
      bootstrapBiasCorrectionErrorNegligible
        (l := l) biasCorrectionError) :
    Tendsto actualVariance l
      (nhds
        ((1 / denominator ^ 2) * (1 / normalizer) *
          weightedScoreCellMomentLimit cells
            (fun cell =>
              (pateBootstrapScoreCellContribution baseWeightLimit
                    reuseResidualWeightLimit heterogeneityLimit
                    residualLimit cell -
                  target * baseWeightLimit cell) ^ 2)
            massLimit)) :=
  tendsto_actualBootstrapVariance_of_eventually_cell_contribution_weight_limits_and_error_stability
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
    baseWeightLimit massLimit actualVariance scoreReplicationError
    biasCorrectionError herror_decomp hcover
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
    hbaseLimit hmass hscore hbias

/--
Prospective PATE actual bootstrap variance convergence from eventually valid
component-level score-cell representations.
-/
theorem prospective_pate_actualBootstrapVariance_tendsto_of_eventually_score_cell_components
    (cells : Finset Cell)
    (sample : Index -> Finset Unit)
    (baseWeight reuseResidualWeight heterogeneity residual :
      Index -> Unit -> Real)
    (score : Index -> Unit -> Cell)
    (target denominator normalizer : Real)
    (cellBaseWeight cellReuseResidualWeight cellHeterogeneity cellResidual :
      Index -> Cell -> Real)
    (baseWeightLimit reuseResidualWeightLimit heterogeneityLimit
      residualLimit massLimit : Cell -> Real)
    (actualVariance scoreReplicationError biasCorrectionError : Index -> Real)
    (herror_decomp :
      (fun index =>
        actualVariance index -
          bootstrapCenteredVarianceTarget (sample index)
            (prospectivePATEBootstrapInfluenceContribution
              (baseWeight index) (reuseResidualWeight index)
              (heterogeneity index) (residual index))
            (baseWeight index) target denominator normalizer) =ᶠ[l]
        (fun index =>
          scoreReplicationError index + biasCorrectionError index))
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
    (hscore :
      bootstrapScoreReplicationErrorNegligible
        (l := l) scoreReplicationError)
    (hbias :
      bootstrapBiasCorrectionErrorNegligible
        (l := l) biasCorrectionError) :
    Tendsto actualVariance l
      (nhds
        ((1 / denominator ^ 2) * (1 / normalizer) *
          weightedScoreCellMomentLimit cells
            (fun cell =>
              (pateBootstrapScoreCellContribution baseWeightLimit
                    reuseResidualWeightLimit heterogeneityLimit
                    residualLimit cell -
                  target * baseWeightLimit cell) ^ 2)
            massLimit)) :=
  tendsto_actualBootstrapVariance_of_eventually_cell_contribution_weight_limits_and_error_stability
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
    baseWeightLimit massLimit actualVariance scoreReplicationError
    biasCorrectionError herror_decomp hcover
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
    hbaseLimit hmass hscore hbias

/--
Retrospective PATT actual bootstrap variance convergence from eventually valid
component-level score-cell representations.
-/
theorem retrospective_patt_actualBootstrapVariance_tendsto_of_eventually_score_cell_components
    (cells : Finset Cell)
    (sample : Index -> Finset Unit)
    (denominatorWeight treatedContribution controlReuseContribution :
      Index -> Unit -> Real)
    (score : Index -> Unit -> Cell)
    (target denominator normalizer : Real)
    (cellDenominatorWeight cellTreatedContribution
      cellControlReuseContribution : Index -> Cell -> Real)
    (denominatorWeightLimit treatedContributionLimit
      controlReuseContributionLimit massLimit : Cell -> Real)
    (actualVariance scoreReplicationError biasCorrectionError : Index -> Real)
    (herror_decomp :
      (fun index =>
        actualVariance index -
          bootstrapCenteredVarianceTarget (sample index)
            (retrospectivePATTBootstrapInfluenceContribution
              (treatedContribution index) (controlReuseContribution index))
            (denominatorWeight index) target denominator normalizer) =ᶠ[l]
        (fun index =>
          scoreReplicationError index + biasCorrectionError index))
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
    (hscore :
      bootstrapScoreReplicationErrorNegligible
        (l := l) scoreReplicationError)
    (hbias :
      bootstrapBiasCorrectionErrorNegligible
        (l := l) biasCorrectionError) :
    Tendsto actualVariance l
      (nhds
        ((1 / denominator ^ 2) * (1 / normalizer) *
          weightedScoreCellMomentLimit cells
            (fun cell =>
              (pattBootstrapScoreCellContribution treatedContributionLimit
                    controlReuseContributionLimit cell -
                  target * denominatorWeightLimit cell) ^ 2)
            massLimit)) :=
  tendsto_actualBootstrapVariance_of_eventually_cell_contribution_weight_limits_and_error_stability
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
    denominatorWeightLimit massLimit actualVariance scoreReplicationError
    biasCorrectionError herror_decomp hcover
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
    hdenominatorLimit hmass hscore hbias

/--
Prospective PATT actual bootstrap variance convergence from eventually valid
component-level score-cell representations.
-/
theorem prospective_patt_actualBootstrapVariance_tendsto_of_eventually_score_cell_components
    (cells : Finset Cell)
    (sample : Index -> Finset Unit)
    (denominatorWeight treatedContribution controlReuseContribution :
      Index -> Unit -> Real)
    (score : Index -> Unit -> Cell)
    (target denominator normalizer : Real)
    (cellDenominatorWeight cellTreatedContribution
      cellControlReuseContribution : Index -> Cell -> Real)
    (denominatorWeightLimit treatedContributionLimit
      controlReuseContributionLimit massLimit : Cell -> Real)
    (actualVariance scoreReplicationError biasCorrectionError : Index -> Real)
    (herror_decomp :
      (fun index =>
        actualVariance index -
          bootstrapCenteredVarianceTarget (sample index)
            (prospectivePATTBootstrapInfluenceContribution
              (treatedContribution index) (controlReuseContribution index))
            (denominatorWeight index) target denominator normalizer) =ᶠ[l]
        (fun index =>
          scoreReplicationError index + biasCorrectionError index))
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
    (hscore :
      bootstrapScoreReplicationErrorNegligible
        (l := l) scoreReplicationError)
    (hbias :
      bootstrapBiasCorrectionErrorNegligible
        (l := l) biasCorrectionError) :
    Tendsto actualVariance l
      (nhds
        ((1 / denominator ^ 2) * (1 / normalizer) *
          weightedScoreCellMomentLimit cells
            (fun cell =>
              (pattBootstrapScoreCellContribution treatedContributionLimit
                    controlReuseContributionLimit cell -
                  target * denominatorWeightLimit cell) ^ 2)
            massLimit)) :=
  tendsto_actualBootstrapVariance_of_eventually_cell_contribution_weight_limits_and_error_stability
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
    denominatorWeightLimit massLimit actualVariance scoreReplicationError
    biasCorrectionError herror_decomp hcover
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
    hdenominatorLimit hmass hscore hbias

/--
Paired retrospective PATE/PATT actual bootstrap variance convergence from
eventually valid component-level score-cell representations.
-/
theorem retrospective_pate_patt_actualBootstrapVariance_tendsto_of_eventually_score_cell_components
    (pateCells : Finset Cell)
    (pateSample : Index -> Finset Unit)
    (pateBaseWeight pateReuseResidualWeight pateHeterogeneity pateResidual :
      Index -> Unit -> Real)
    (pateScore : Index -> Unit -> Cell)
    (pateTarget pateDenominator pateNormalizer : Real)
    (pateCellBaseWeight pateCellReuseResidualWeight pateCellHeterogeneity
      pateCellResidual : Index -> Cell -> Real)
    (pateBaseWeightLimit pateReuseResidualWeightLimit
      pateHeterogeneityLimit pateResidualLimit pateMassLimit : Cell -> Real)
    (pateActualVariance pateScoreReplicationError pateBiasCorrectionError :
      Index -> Real)
    (hpateErrorDecomp :
      (fun index =>
        pateActualVariance index -
          bootstrapCenteredVarianceTarget (pateSample index)
            (retrospectivePATEBootstrapInfluenceContribution
              (pateBaseWeight index) (pateReuseResidualWeight index)
              (pateHeterogeneity index) (pateResidual index))
            (pateBaseWeight index) pateTarget pateDenominator
            pateNormalizer) =ᶠ[l]
        (fun index =>
          pateScoreReplicationError index + pateBiasCorrectionError index))
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
    (hpateScoreError :
      bootstrapScoreReplicationErrorNegligible
        (l := l) pateScoreReplicationError)
    (hpateBiasError :
      bootstrapBiasCorrectionErrorNegligible
        (l := l) pateBiasCorrectionError)
    (pattCells : Finset Cell)
    (pattSample : Index -> Finset Unit)
    (pattDenominatorWeight pattTreatedContribution
      pattControlReuseContribution : Index -> Unit -> Real)
    (pattScore : Index -> Unit -> Cell)
    (pattTarget pattDenominator pattNormalizer : Real)
    (pattCellDenominatorWeight pattCellTreatedContribution
      pattCellControlReuseContribution : Index -> Cell -> Real)
    (pattDenominatorWeightLimit pattTreatedContributionLimit
      pattControlReuseContributionLimit pattMassLimit : Cell -> Real)
    (pattActualVariance pattScoreReplicationError pattBiasCorrectionError :
      Index -> Real)
    (hpattErrorDecomp :
      (fun index =>
        pattActualVariance index -
          bootstrapCenteredVarianceTarget (pattSample index)
            (retrospectivePATTBootstrapInfluenceContribution
              (pattTreatedContribution index)
              (pattControlReuseContribution index))
            (pattDenominatorWeight index) pattTarget pattDenominator
            pattNormalizer) =ᶠ[l]
        (fun index =>
          pattScoreReplicationError index + pattBiasCorrectionError index))
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
    (hpattScoreError :
      bootstrapScoreReplicationErrorNegligible
        (l := l) pattScoreReplicationError)
    (hpattBiasError :
      bootstrapBiasCorrectionErrorNegligible
        (l := l) pattBiasCorrectionError) :
    Tendsto pateActualVariance l
      (nhds
        ((1 / pateDenominator ^ 2) * (1 / pateNormalizer) *
          weightedScoreCellMomentLimit pateCells
            (fun cell =>
              (pateBootstrapScoreCellContribution pateBaseWeightLimit
                    pateReuseResidualWeightLimit pateHeterogeneityLimit
                    pateResidualLimit cell -
                  pateTarget * pateBaseWeightLimit cell) ^ 2)
            pateMassLimit)) ∧
      Tendsto pattActualVariance l
        (nhds
          ((1 / pattDenominator ^ 2) * (1 / pattNormalizer) *
            weightedScoreCellMomentLimit pattCells
              (fun cell =>
                (pattBootstrapScoreCellContribution
                      pattTreatedContributionLimit
                      pattControlReuseContributionLimit cell -
                    pattTarget * pattDenominatorWeightLimit cell) ^ 2)
              pattMassLimit)) := by
  constructor
  · exact
      retrospective_pate_actualBootstrapVariance_tendsto_of_eventually_score_cell_components
        (l := l) pateCells pateSample pateBaseWeight
        pateReuseResidualWeight pateHeterogeneity pateResidual pateScore
        pateTarget pateDenominator pateNormalizer pateCellBaseWeight
        pateCellReuseResidualWeight pateCellHeterogeneity pateCellResidual
        pateBaseWeightLimit pateReuseResidualWeightLimit
        pateHeterogeneityLimit pateResidualLimit pateMassLimit
        pateActualVariance pateScoreReplicationError pateBiasCorrectionError
        hpateErrorDecomp hpateCover hpateBase hpateReuse hpateHeterogeneity
        hpateResidual hpateBaseLimit hpateReuseLimit hpateHeterogeneityLimit
        hpateResidualLimit hpateMass hpateScoreError hpateBiasError
  · exact
      retrospective_patt_actualBootstrapVariance_tendsto_of_eventually_score_cell_components
        (l := l) pattCells pattSample pattDenominatorWeight
        pattTreatedContribution pattControlReuseContribution pattScore
        pattTarget pattDenominator pattNormalizer pattCellDenominatorWeight
        pattCellTreatedContribution pattCellControlReuseContribution
        pattDenominatorWeightLimit pattTreatedContributionLimit
        pattControlReuseContributionLimit pattMassLimit pattActualVariance
        pattScoreReplicationError pattBiasCorrectionError hpattErrorDecomp
        hpattCover hpattDenominator hpattTreated hpattControl
        hpattDenominatorLimit hpattTreatedLimit hpattControlLimit hpattMass
        hpattScoreError hpattBiasError

/--
Paired prospective PATE/PATT actual bootstrap variance convergence from
eventually valid component-level score-cell representations.
-/
theorem prospective_pate_patt_actualBootstrapVariance_tendsto_of_eventually_score_cell_components
    (pateCells : Finset Cell)
    (pateSample : Index -> Finset Unit)
    (pateBaseWeight pateReuseResidualWeight pateHeterogeneity pateResidual :
      Index -> Unit -> Real)
    (pateScore : Index -> Unit -> Cell)
    (pateTarget pateDenominator pateNormalizer : Real)
    (pateCellBaseWeight pateCellReuseResidualWeight pateCellHeterogeneity
      pateCellResidual : Index -> Cell -> Real)
    (pateBaseWeightLimit pateReuseResidualWeightLimit
      pateHeterogeneityLimit pateResidualLimit pateMassLimit : Cell -> Real)
    (pateActualVariance pateScoreReplicationError pateBiasCorrectionError :
      Index -> Real)
    (hpateErrorDecomp :
      (fun index =>
        pateActualVariance index -
          bootstrapCenteredVarianceTarget (pateSample index)
            (prospectivePATEBootstrapInfluenceContribution
              (pateBaseWeight index) (pateReuseResidualWeight index)
              (pateHeterogeneity index) (pateResidual index))
            (pateBaseWeight index) pateTarget pateDenominator
            pateNormalizer) =ᶠ[l]
        (fun index =>
          pateScoreReplicationError index + pateBiasCorrectionError index))
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
    (hpateScoreError :
      bootstrapScoreReplicationErrorNegligible
        (l := l) pateScoreReplicationError)
    (hpateBiasError :
      bootstrapBiasCorrectionErrorNegligible
        (l := l) pateBiasCorrectionError)
    (pattCells : Finset Cell)
    (pattSample : Index -> Finset Unit)
    (pattDenominatorWeight pattTreatedContribution
      pattControlReuseContribution : Index -> Unit -> Real)
    (pattScore : Index -> Unit -> Cell)
    (pattTarget pattDenominator pattNormalizer : Real)
    (pattCellDenominatorWeight pattCellTreatedContribution
      pattCellControlReuseContribution : Index -> Cell -> Real)
    (pattDenominatorWeightLimit pattTreatedContributionLimit
      pattControlReuseContributionLimit pattMassLimit : Cell -> Real)
    (pattActualVariance pattScoreReplicationError pattBiasCorrectionError :
      Index -> Real)
    (hpattErrorDecomp :
      (fun index =>
        pattActualVariance index -
          bootstrapCenteredVarianceTarget (pattSample index)
            (prospectivePATTBootstrapInfluenceContribution
              (pattTreatedContribution index)
              (pattControlReuseContribution index))
            (pattDenominatorWeight index) pattTarget pattDenominator
            pattNormalizer) =ᶠ[l]
        (fun index =>
          pattScoreReplicationError index + pattBiasCorrectionError index))
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
    (hpattScoreError :
      bootstrapScoreReplicationErrorNegligible
        (l := l) pattScoreReplicationError)
    (hpattBiasError :
      bootstrapBiasCorrectionErrorNegligible
        (l := l) pattBiasCorrectionError) :
    Tendsto pateActualVariance l
      (nhds
        ((1 / pateDenominator ^ 2) * (1 / pateNormalizer) *
          weightedScoreCellMomentLimit pateCells
            (fun cell =>
              (pateBootstrapScoreCellContribution pateBaseWeightLimit
                    pateReuseResidualWeightLimit pateHeterogeneityLimit
                    pateResidualLimit cell -
                  pateTarget * pateBaseWeightLimit cell) ^ 2)
            pateMassLimit)) ∧
      Tendsto pattActualVariance l
        (nhds
          ((1 / pattDenominator ^ 2) * (1 / pattNormalizer) *
            weightedScoreCellMomentLimit pattCells
              (fun cell =>
                (pattBootstrapScoreCellContribution
                      pattTreatedContributionLimit
                      pattControlReuseContributionLimit cell -
                    pattTarget * pattDenominatorWeightLimit cell) ^ 2)
              pattMassLimit)) := by
  constructor
  · exact
      prospective_pate_actualBootstrapVariance_tendsto_of_eventually_score_cell_components
        (l := l) pateCells pateSample pateBaseWeight
        pateReuseResidualWeight pateHeterogeneity pateResidual pateScore
        pateTarget pateDenominator pateNormalizer pateCellBaseWeight
        pateCellReuseResidualWeight pateCellHeterogeneity pateCellResidual
        pateBaseWeightLimit pateReuseResidualWeightLimit
        pateHeterogeneityLimit pateResidualLimit pateMassLimit
        pateActualVariance pateScoreReplicationError pateBiasCorrectionError
        hpateErrorDecomp hpateCover hpateBase hpateReuse hpateHeterogeneity
        hpateResidual hpateBaseLimit hpateReuseLimit hpateHeterogeneityLimit
        hpateResidualLimit hpateMass hpateScoreError hpateBiasError
  · exact
      prospective_patt_actualBootstrapVariance_tendsto_of_eventually_score_cell_components
        (l := l) pattCells pattSample pattDenominatorWeight
        pattTreatedContribution pattControlReuseContribution pattScore
        pattTarget pattDenominator pattNormalizer pattCellDenominatorWeight
        pattCellTreatedContribution pattCellControlReuseContribution
        pattDenominatorWeightLimit pattTreatedContributionLimit
        pattControlReuseContributionLimit pattMassLimit pattActualVariance
        pattScoreReplicationError pattBiasCorrectionError hpattErrorDecomp
        hpattCover hpattDenominator hpattTreated hpattControl
        hpattDenominatorLimit hpattTreatedLimit hpattControlLimit hpattMass
        hpattScoreError hpattBiasError

end WDSM
end Matching
end StatInference
