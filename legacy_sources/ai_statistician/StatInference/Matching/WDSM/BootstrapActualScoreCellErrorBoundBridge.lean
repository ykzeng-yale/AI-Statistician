import Mathlib.Data.Finset.Basic
import Mathlib.Topology.Basic
import StatInference.Matching.WDSM.BootstrapActualScoreCellConsistencyBridge
import StatInference.Matching.WDSM.BootstrapActualVarianceErrorBoundBridge
import StatInference.Matching.WDSM.BootstrapErrorBoundBridge

/-!
# Scenario actual bootstrap variance from score cells and finite error bounds

This module specializes the score-cell actual-bootstrap bridge further: the
score-replication and bias-correction errors are supplied by finite component
decompositions with componentwise shrinking absolute bounds.
-/

namespace StatInference
namespace Matching
namespace WDSM

open Filter

variable {Index Unit Cell ScoreErrorComponent BiasErrorComponent : Type*}
variable {l : Filter Index}
variable [DecidableEq Cell] [DecidableEq ScoreErrorComponent]
  [DecidableEq BiasErrorComponent]

/--
Retrospective PATE actual bootstrap variance convergence from component-level
score-cell limits and finite-component score/bias error bounds.
-/
theorem retrospective_pate_actualBootstrapVariance_tendsto_of_score_cell_components_and_finite_error_bounds
    (cells : Finset Cell)
    (scoreErrorComponents : Finset ScoreErrorComponent)
    (biasErrorComponents : Finset BiasErrorComponent)
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
    (scoreErrorComponent scoreErrorComponentBound :
      Index -> ScoreErrorComponent -> Real)
    (biasErrorComponent biasErrorComponentBound :
      Index -> BiasErrorComponent -> Real)
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
    (hscore_decomp :
      scoreReplicationError =ᶠ[l]
        (fun index => ∑ component ∈ scoreErrorComponents,
          scoreErrorComponent index component))
    (hscore_component_bound :
      ∀ᶠ index in l,
        ∀ component, component ∈ scoreErrorComponents ->
          |scoreErrorComponent index component| ≤
            scoreErrorComponentBound index component)
    (hscore_component_bound_tendsto :
      ∀ component, component ∈ scoreErrorComponents ->
        Tendsto (fun index => scoreErrorComponentBound index component)
          l (nhds 0))
    (hbias_decomp :
      biasCorrectionError =ᶠ[l]
        (fun index => ∑ component ∈ biasErrorComponents,
          biasErrorComponent index component))
    (hbias_component_bound :
      ∀ᶠ index in l,
        ∀ component, component ∈ biasErrorComponents ->
          |biasErrorComponent index component| ≤
            biasErrorComponentBound index component)
    (hbias_component_bound_tendsto :
      ∀ component, component ∈ biasErrorComponents ->
        Tendsto (fun index => biasErrorComponentBound index component)
          l (nhds 0)) :
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
  retrospective_pate_actualBootstrapVariance_tendsto_of_score_cell_components
    (l := l) cells sample baseWeight reuseResidualWeight heterogeneity
    residual score target denominator normalizer cellBaseWeight
    cellReuseResidualWeight cellHeterogeneity cellResidual baseWeightLimit
    reuseResidualWeightLimit heterogeneityLimit residualLimit massLimit
    actualVariance scoreReplicationError biasCorrectionError herror_decomp
    hcover hbase hreuse hheterogeneity hresidual hbaseLimit hreuseLimit
    hheterogeneityLimit hresidualLimit hmass
    (bootstrapScoreReplicationErrorNegligible_of_finite_component_bounds
      (l := l) scoreErrorComponents scoreReplicationError
      scoreErrorComponent scoreErrorComponentBound hscore_decomp
      hscore_component_bound hscore_component_bound_tendsto)
    (bootstrapBiasCorrectionErrorNegligible_of_finite_component_bounds
      (l := l) biasErrorComponents biasCorrectionError biasErrorComponent
      biasErrorComponentBound hbias_decomp hbias_component_bound
      hbias_component_bound_tendsto)

/--
Prospective PATE actual bootstrap variance convergence from component-level
score-cell limits and finite-component score/bias error bounds.
-/
theorem prospective_pate_actualBootstrapVariance_tendsto_of_score_cell_components_and_finite_error_bounds
    (cells : Finset Cell)
    (scoreErrorComponents : Finset ScoreErrorComponent)
    (biasErrorComponents : Finset BiasErrorComponent)
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
    (scoreErrorComponent scoreErrorComponentBound :
      Index -> ScoreErrorComponent -> Real)
    (biasErrorComponent biasErrorComponentBound :
      Index -> BiasErrorComponent -> Real)
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
    (hscore_decomp :
      scoreReplicationError =ᶠ[l]
        (fun index => ∑ component ∈ scoreErrorComponents,
          scoreErrorComponent index component))
    (hscore_component_bound :
      ∀ᶠ index in l,
        ∀ component, component ∈ scoreErrorComponents ->
          |scoreErrorComponent index component| ≤
            scoreErrorComponentBound index component)
    (hscore_component_bound_tendsto :
      ∀ component, component ∈ scoreErrorComponents ->
        Tendsto (fun index => scoreErrorComponentBound index component)
          l (nhds 0))
    (hbias_decomp :
      biasCorrectionError =ᶠ[l]
        (fun index => ∑ component ∈ biasErrorComponents,
          biasErrorComponent index component))
    (hbias_component_bound :
      ∀ᶠ index in l,
        ∀ component, component ∈ biasErrorComponents ->
          |biasErrorComponent index component| ≤
            biasErrorComponentBound index component)
    (hbias_component_bound_tendsto :
      ∀ component, component ∈ biasErrorComponents ->
        Tendsto (fun index => biasErrorComponentBound index component)
          l (nhds 0)) :
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
  prospective_pate_actualBootstrapVariance_tendsto_of_score_cell_components
    (l := l) cells sample baseWeight reuseResidualWeight heterogeneity
    residual score target denominator normalizer cellBaseWeight
    cellReuseResidualWeight cellHeterogeneity cellResidual baseWeightLimit
    reuseResidualWeightLimit heterogeneityLimit residualLimit massLimit
    actualVariance scoreReplicationError biasCorrectionError herror_decomp
    hcover hbase hreuse hheterogeneity hresidual hbaseLimit hreuseLimit
    hheterogeneityLimit hresidualLimit hmass
    (bootstrapScoreReplicationErrorNegligible_of_finite_component_bounds
      (l := l) scoreErrorComponents scoreReplicationError
      scoreErrorComponent scoreErrorComponentBound hscore_decomp
      hscore_component_bound hscore_component_bound_tendsto)
    (bootstrapBiasCorrectionErrorNegligible_of_finite_component_bounds
      (l := l) biasErrorComponents biasCorrectionError biasErrorComponent
      biasErrorComponentBound hbias_decomp hbias_component_bound
      hbias_component_bound_tendsto)

/--
Retrospective PATT actual bootstrap variance convergence from component-level
score-cell limits and finite-component score/bias error bounds.
-/
theorem retrospective_patt_actualBootstrapVariance_tendsto_of_score_cell_components_and_finite_error_bounds
    (cells : Finset Cell)
    (scoreErrorComponents : Finset ScoreErrorComponent)
    (biasErrorComponents : Finset BiasErrorComponent)
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
    (scoreErrorComponent scoreErrorComponentBound :
      Index -> ScoreErrorComponent -> Real)
    (biasErrorComponent biasErrorComponentBound :
      Index -> BiasErrorComponent -> Real)
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
    (hscore_decomp :
      scoreReplicationError =ᶠ[l]
        (fun index => ∑ component ∈ scoreErrorComponents,
          scoreErrorComponent index component))
    (hscore_component_bound :
      ∀ᶠ index in l,
        ∀ component, component ∈ scoreErrorComponents ->
          |scoreErrorComponent index component| ≤
            scoreErrorComponentBound index component)
    (hscore_component_bound_tendsto :
      ∀ component, component ∈ scoreErrorComponents ->
        Tendsto (fun index => scoreErrorComponentBound index component)
          l (nhds 0))
    (hbias_decomp :
      biasCorrectionError =ᶠ[l]
        (fun index => ∑ component ∈ biasErrorComponents,
          biasErrorComponent index component))
    (hbias_component_bound :
      ∀ᶠ index in l,
        ∀ component, component ∈ biasErrorComponents ->
          |biasErrorComponent index component| ≤
            biasErrorComponentBound index component)
    (hbias_component_bound_tendsto :
      ∀ component, component ∈ biasErrorComponents ->
        Tendsto (fun index => biasErrorComponentBound index component)
          l (nhds 0)) :
    Tendsto actualVariance l
      (nhds
        ((1 / denominator ^ 2) * (1 / normalizer) *
          weightedScoreCellMomentLimit cells
            (fun cell =>
              (pattBootstrapScoreCellContribution treatedContributionLimit
                    controlReuseContributionLimit cell -
                  target * denominatorWeightLimit cell) ^ 2)
            massLimit)) :=
  retrospective_patt_actualBootstrapVariance_tendsto_of_score_cell_components
    (l := l) cells sample denominatorWeight treatedContribution
    controlReuseContribution score target denominator normalizer
    cellDenominatorWeight cellTreatedContribution cellControlReuseContribution
    denominatorWeightLimit treatedContributionLimit controlReuseContributionLimit
    massLimit actualVariance scoreReplicationError biasCorrectionError
    herror_decomp hcover hdenominator htreated hcontrol hdenominatorLimit
    htreatedLimit hcontrolLimit hmass
    (bootstrapScoreReplicationErrorNegligible_of_finite_component_bounds
      (l := l) scoreErrorComponents scoreReplicationError
      scoreErrorComponent scoreErrorComponentBound hscore_decomp
      hscore_component_bound hscore_component_bound_tendsto)
    (bootstrapBiasCorrectionErrorNegligible_of_finite_component_bounds
      (l := l) biasErrorComponents biasCorrectionError biasErrorComponent
      biasErrorComponentBound hbias_decomp hbias_component_bound
      hbias_component_bound_tendsto)

/--
Prospective PATT actual bootstrap variance convergence from component-level
score-cell limits and finite-component score/bias error bounds.
-/
theorem prospective_patt_actualBootstrapVariance_tendsto_of_score_cell_components_and_finite_error_bounds
    (cells : Finset Cell)
    (scoreErrorComponents : Finset ScoreErrorComponent)
    (biasErrorComponents : Finset BiasErrorComponent)
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
    (scoreErrorComponent scoreErrorComponentBound :
      Index -> ScoreErrorComponent -> Real)
    (biasErrorComponent biasErrorComponentBound :
      Index -> BiasErrorComponent -> Real)
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
    (hscore_decomp :
      scoreReplicationError =ᶠ[l]
        (fun index => ∑ component ∈ scoreErrorComponents,
          scoreErrorComponent index component))
    (hscore_component_bound :
      ∀ᶠ index in l,
        ∀ component, component ∈ scoreErrorComponents ->
          |scoreErrorComponent index component| ≤
            scoreErrorComponentBound index component)
    (hscore_component_bound_tendsto :
      ∀ component, component ∈ scoreErrorComponents ->
        Tendsto (fun index => scoreErrorComponentBound index component)
          l (nhds 0))
    (hbias_decomp :
      biasCorrectionError =ᶠ[l]
        (fun index => ∑ component ∈ biasErrorComponents,
          biasErrorComponent index component))
    (hbias_component_bound :
      ∀ᶠ index in l,
        ∀ component, component ∈ biasErrorComponents ->
          |biasErrorComponent index component| ≤
            biasErrorComponentBound index component)
    (hbias_component_bound_tendsto :
      ∀ component, component ∈ biasErrorComponents ->
        Tendsto (fun index => biasErrorComponentBound index component)
          l (nhds 0)) :
    Tendsto actualVariance l
      (nhds
        ((1 / denominator ^ 2) * (1 / normalizer) *
          weightedScoreCellMomentLimit cells
            (fun cell =>
              (pattBootstrapScoreCellContribution treatedContributionLimit
                    controlReuseContributionLimit cell -
                  target * denominatorWeightLimit cell) ^ 2)
            massLimit)) :=
  prospective_patt_actualBootstrapVariance_tendsto_of_score_cell_components
    (l := l) cells sample denominatorWeight treatedContribution
    controlReuseContribution score target denominator normalizer
    cellDenominatorWeight cellTreatedContribution cellControlReuseContribution
    denominatorWeightLimit treatedContributionLimit controlReuseContributionLimit
    massLimit actualVariance scoreReplicationError biasCorrectionError
    herror_decomp hcover hdenominator htreated hcontrol hdenominatorLimit
    htreatedLimit hcontrolLimit hmass
    (bootstrapScoreReplicationErrorNegligible_of_finite_component_bounds
      (l := l) scoreErrorComponents scoreReplicationError
      scoreErrorComponent scoreErrorComponentBound hscore_decomp
      hscore_component_bound hscore_component_bound_tendsto)
    (bootstrapBiasCorrectionErrorNegligible_of_finite_component_bounds
      (l := l) biasErrorComponents biasCorrectionError biasErrorComponent
      biasErrorComponentBound hbias_decomp hbias_component_bound
      hbias_component_bound_tendsto)

/--
Paired retrospective PATE/PATT actual bootstrap variance convergence from
score-cell limits and finite-component score/bias error bounds.
-/
theorem retrospective_pate_patt_actualBootstrapVariance_tendsto_of_score_cell_components_and_finite_error_bounds
    (pateCells : Finset Cell)
    (pateScoreErrorComponents : Finset ScoreErrorComponent)
    (pateBiasErrorComponents : Finset BiasErrorComponent)
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
    (pateScoreErrorComponent pateScoreErrorComponentBound :
      Index -> ScoreErrorComponent -> Real)
    (pateBiasErrorComponent pateBiasErrorComponentBound :
      Index -> BiasErrorComponent -> Real)
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
    (hpateScoreDecomp :
      pateScoreReplicationError =ᶠ[l]
        (fun index => ∑ component ∈ pateScoreErrorComponents,
          pateScoreErrorComponent index component))
    (hpateScoreComponentBound :
      ∀ᶠ index in l,
        ∀ component, component ∈ pateScoreErrorComponents ->
          |pateScoreErrorComponent index component| ≤
            pateScoreErrorComponentBound index component)
    (hpateScoreComponentBoundTendsto :
      ∀ component, component ∈ pateScoreErrorComponents ->
        Tendsto (fun index => pateScoreErrorComponentBound index component)
          l (nhds 0))
    (hpateBiasDecomp :
      pateBiasCorrectionError =ᶠ[l]
        (fun index => ∑ component ∈ pateBiasErrorComponents,
          pateBiasErrorComponent index component))
    (hpateBiasComponentBound :
      ∀ᶠ index in l,
        ∀ component, component ∈ pateBiasErrorComponents ->
          |pateBiasErrorComponent index component| ≤
            pateBiasErrorComponentBound index component)
    (hpateBiasComponentBoundTendsto :
      ∀ component, component ∈ pateBiasErrorComponents ->
        Tendsto (fun index => pateBiasErrorComponentBound index component)
          l (nhds 0))
    (pattCells : Finset Cell)
    (pattScoreErrorComponents : Finset ScoreErrorComponent)
    (pattBiasErrorComponents : Finset BiasErrorComponent)
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
    (pattScoreErrorComponent pattScoreErrorComponentBound :
      Index -> ScoreErrorComponent -> Real)
    (pattBiasErrorComponent pattBiasErrorComponentBound :
      Index -> BiasErrorComponent -> Real)
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
    (hpattScoreDecomp :
      pattScoreReplicationError =ᶠ[l]
        (fun index => ∑ component ∈ pattScoreErrorComponents,
          pattScoreErrorComponent index component))
    (hpattScoreComponentBound :
      ∀ᶠ index in l,
        ∀ component, component ∈ pattScoreErrorComponents ->
          |pattScoreErrorComponent index component| ≤
            pattScoreErrorComponentBound index component)
    (hpattScoreComponentBoundTendsto :
      ∀ component, component ∈ pattScoreErrorComponents ->
        Tendsto (fun index => pattScoreErrorComponentBound index component)
          l (nhds 0))
    (hpattBiasDecomp :
      pattBiasCorrectionError =ᶠ[l]
        (fun index => ∑ component ∈ pattBiasErrorComponents,
          pattBiasErrorComponent index component))
    (hpattBiasComponentBound :
      ∀ᶠ index in l,
        ∀ component, component ∈ pattBiasErrorComponents ->
          |pattBiasErrorComponent index component| ≤
            pattBiasErrorComponentBound index component)
    (hpattBiasComponentBoundTendsto :
      ∀ component, component ∈ pattBiasErrorComponents ->
        Tendsto (fun index => pattBiasErrorComponentBound index component)
          l (nhds 0)) :
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
      retrospective_pate_actualBootstrapVariance_tendsto_of_score_cell_components_and_finite_error_bounds
        (l := l) pateCells pateScoreErrorComponents
        pateBiasErrorComponents pateSample pateBaseWeight
        pateReuseResidualWeight pateHeterogeneity pateResidual pateScore
        pateTarget pateDenominator pateNormalizer pateCellBaseWeight
        pateCellReuseResidualWeight pateCellHeterogeneity pateCellResidual
        pateBaseWeightLimit pateReuseResidualWeightLimit
        pateHeterogeneityLimit pateResidualLimit pateMassLimit
        pateActualVariance pateScoreReplicationError pateBiasCorrectionError
        pateScoreErrorComponent pateScoreErrorComponentBound
        pateBiasErrorComponent pateBiasErrorComponentBound hpateErrorDecomp
        hpateCover hpateBase hpateReuse hpateHeterogeneity hpateResidual
        hpateBaseLimit hpateReuseLimit hpateHeterogeneityLimit
        hpateResidualLimit hpateMass hpateScoreDecomp
        hpateScoreComponentBound hpateScoreComponentBoundTendsto
        hpateBiasDecomp hpateBiasComponentBound hpateBiasComponentBoundTendsto
  · exact
      retrospective_patt_actualBootstrapVariance_tendsto_of_score_cell_components_and_finite_error_bounds
        (l := l) pattCells pattScoreErrorComponents
        pattBiasErrorComponents pattSample pattDenominatorWeight
        pattTreatedContribution pattControlReuseContribution pattScore
        pattTarget pattDenominator pattNormalizer pattCellDenominatorWeight
        pattCellTreatedContribution pattCellControlReuseContribution
        pattDenominatorWeightLimit pattTreatedContributionLimit
        pattControlReuseContributionLimit pattMassLimit pattActualVariance
        pattScoreReplicationError pattBiasCorrectionError
        pattScoreErrorComponent pattScoreErrorComponentBound
        pattBiasErrorComponent pattBiasErrorComponentBound hpattErrorDecomp
        hpattCover hpattDenominator hpattTreated hpattControl
        hpattDenominatorLimit hpattTreatedLimit hpattControlLimit hpattMass
        hpattScoreDecomp hpattScoreComponentBound
        hpattScoreComponentBoundTendsto hpattBiasDecomp
        hpattBiasComponentBound hpattBiasComponentBoundTendsto

/--
Paired prospective PATE/PATT actual bootstrap variance convergence from
score-cell limits and finite-component score/bias error bounds.
-/
theorem prospective_pate_patt_actualBootstrapVariance_tendsto_of_score_cell_components_and_finite_error_bounds
    (pateCells : Finset Cell)
    (pateScoreErrorComponents : Finset ScoreErrorComponent)
    (pateBiasErrorComponents : Finset BiasErrorComponent)
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
    (pateScoreErrorComponent pateScoreErrorComponentBound :
      Index -> ScoreErrorComponent -> Real)
    (pateBiasErrorComponent pateBiasErrorComponentBound :
      Index -> BiasErrorComponent -> Real)
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
    (hpateScoreDecomp :
      pateScoreReplicationError =ᶠ[l]
        (fun index => ∑ component ∈ pateScoreErrorComponents,
          pateScoreErrorComponent index component))
    (hpateScoreComponentBound :
      ∀ᶠ index in l,
        ∀ component, component ∈ pateScoreErrorComponents ->
          |pateScoreErrorComponent index component| ≤
            pateScoreErrorComponentBound index component)
    (hpateScoreComponentBoundTendsto :
      ∀ component, component ∈ pateScoreErrorComponents ->
        Tendsto (fun index => pateScoreErrorComponentBound index component)
          l (nhds 0))
    (hpateBiasDecomp :
      pateBiasCorrectionError =ᶠ[l]
        (fun index => ∑ component ∈ pateBiasErrorComponents,
          pateBiasErrorComponent index component))
    (hpateBiasComponentBound :
      ∀ᶠ index in l,
        ∀ component, component ∈ pateBiasErrorComponents ->
          |pateBiasErrorComponent index component| ≤
            pateBiasErrorComponentBound index component)
    (hpateBiasComponentBoundTendsto :
      ∀ component, component ∈ pateBiasErrorComponents ->
        Tendsto (fun index => pateBiasErrorComponentBound index component)
          l (nhds 0))
    (pattCells : Finset Cell)
    (pattScoreErrorComponents : Finset ScoreErrorComponent)
    (pattBiasErrorComponents : Finset BiasErrorComponent)
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
    (pattScoreErrorComponent pattScoreErrorComponentBound :
      Index -> ScoreErrorComponent -> Real)
    (pattBiasErrorComponent pattBiasErrorComponentBound :
      Index -> BiasErrorComponent -> Real)
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
    (hpattScoreDecomp :
      pattScoreReplicationError =ᶠ[l]
        (fun index => ∑ component ∈ pattScoreErrorComponents,
          pattScoreErrorComponent index component))
    (hpattScoreComponentBound :
      ∀ᶠ index in l,
        ∀ component, component ∈ pattScoreErrorComponents ->
          |pattScoreErrorComponent index component| ≤
            pattScoreErrorComponentBound index component)
    (hpattScoreComponentBoundTendsto :
      ∀ component, component ∈ pattScoreErrorComponents ->
        Tendsto (fun index => pattScoreErrorComponentBound index component)
          l (nhds 0))
    (hpattBiasDecomp :
      pattBiasCorrectionError =ᶠ[l]
        (fun index => ∑ component ∈ pattBiasErrorComponents,
          pattBiasErrorComponent index component))
    (hpattBiasComponentBound :
      ∀ᶠ index in l,
        ∀ component, component ∈ pattBiasErrorComponents ->
          |pattBiasErrorComponent index component| ≤
            pattBiasErrorComponentBound index component)
    (hpattBiasComponentBoundTendsto :
      ∀ component, component ∈ pattBiasErrorComponents ->
        Tendsto (fun index => pattBiasErrorComponentBound index component)
          l (nhds 0)) :
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
      prospective_pate_actualBootstrapVariance_tendsto_of_score_cell_components_and_finite_error_bounds
        (l := l) pateCells pateScoreErrorComponents
        pateBiasErrorComponents pateSample pateBaseWeight
        pateReuseResidualWeight pateHeterogeneity pateResidual pateScore
        pateTarget pateDenominator pateNormalizer pateCellBaseWeight
        pateCellReuseResidualWeight pateCellHeterogeneity pateCellResidual
        pateBaseWeightLimit pateReuseResidualWeightLimit
        pateHeterogeneityLimit pateResidualLimit pateMassLimit
        pateActualVariance pateScoreReplicationError pateBiasCorrectionError
        pateScoreErrorComponent pateScoreErrorComponentBound
        pateBiasErrorComponent pateBiasErrorComponentBound hpateErrorDecomp
        hpateCover hpateBase hpateReuse hpateHeterogeneity hpateResidual
        hpateBaseLimit hpateReuseLimit hpateHeterogeneityLimit
        hpateResidualLimit hpateMass hpateScoreDecomp
        hpateScoreComponentBound hpateScoreComponentBoundTendsto
        hpateBiasDecomp hpateBiasComponentBound hpateBiasComponentBoundTendsto
  · exact
      prospective_patt_actualBootstrapVariance_tendsto_of_score_cell_components_and_finite_error_bounds
        (l := l) pattCells pattScoreErrorComponents
        pattBiasErrorComponents pattSample pattDenominatorWeight
        pattTreatedContribution pattControlReuseContribution pattScore
        pattTarget pattDenominator pattNormalizer pattCellDenominatorWeight
        pattCellTreatedContribution pattCellControlReuseContribution
        pattDenominatorWeightLimit pattTreatedContributionLimit
        pattControlReuseContributionLimit pattMassLimit pattActualVariance
        pattScoreReplicationError pattBiasCorrectionError
        pattScoreErrorComponent pattScoreErrorComponentBound
        pattBiasErrorComponent pattBiasErrorComponentBound hpattErrorDecomp
        hpattCover hpattDenominator hpattTreated hpattControl
        hpattDenominatorLimit hpattTreatedLimit hpattControlLimit hpattMass
        hpattScoreDecomp hpattScoreComponentBound
        hpattScoreComponentBoundTendsto hpattBiasDecomp
        hpattBiasComponentBound hpattBiasComponentBoundTendsto

/--
Retrospective PATE eventual score-cell version with finite-component
score/bias error bounds.
-/
theorem retrospective_pate_actualBootstrapVariance_tendsto_of_eventually_score_cell_components_and_finite_error_bounds
    (cells : Finset Cell)
    (scoreErrorComponents : Finset ScoreErrorComponent)
    (biasErrorComponents : Finset BiasErrorComponent)
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
    (scoreErrorComponent scoreErrorComponentBound :
      Index -> ScoreErrorComponent -> Real)
    (biasErrorComponent biasErrorComponentBound :
      Index -> BiasErrorComponent -> Real)
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
    (hscore_decomp :
      scoreReplicationError =ᶠ[l]
        (fun index => ∑ component ∈ scoreErrorComponents,
          scoreErrorComponent index component))
    (hscore_component_bound :
      ∀ᶠ index in l,
        ∀ component, component ∈ scoreErrorComponents ->
          |scoreErrorComponent index component| ≤
            scoreErrorComponentBound index component)
    (hscore_component_bound_tendsto :
      ∀ component, component ∈ scoreErrorComponents ->
        Tendsto (fun index => scoreErrorComponentBound index component)
          l (nhds 0))
    (hbias_decomp :
      biasCorrectionError =ᶠ[l]
        (fun index => ∑ component ∈ biasErrorComponents,
          biasErrorComponent index component))
    (hbias_component_bound :
      ∀ᶠ index in l,
        ∀ component, component ∈ biasErrorComponents ->
          |biasErrorComponent index component| ≤
            biasErrorComponentBound index component)
    (hbias_component_bound_tendsto :
      ∀ component, component ∈ biasErrorComponents ->
        Tendsto (fun index => biasErrorComponentBound index component)
          l (nhds 0)) :
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
  retrospective_pate_actualBootstrapVariance_tendsto_of_eventually_score_cell_components
    (l := l) cells sample baseWeight reuseResidualWeight heterogeneity
    residual score target denominator normalizer cellBaseWeight
    cellReuseResidualWeight cellHeterogeneity cellResidual baseWeightLimit
    reuseResidualWeightLimit heterogeneityLimit residualLimit massLimit
    actualVariance scoreReplicationError biasCorrectionError herror_decomp
    hcover hbase hreuse hheterogeneity hresidual hbaseLimit hreuseLimit
    hheterogeneityLimit hresidualLimit hmass
    (bootstrapScoreReplicationErrorNegligible_of_finite_component_bounds
      (l := l) scoreErrorComponents scoreReplicationError
      scoreErrorComponent scoreErrorComponentBound hscore_decomp
      hscore_component_bound hscore_component_bound_tendsto)
    (bootstrapBiasCorrectionErrorNegligible_of_finite_component_bounds
      (l := l) biasErrorComponents biasCorrectionError biasErrorComponent
      biasErrorComponentBound hbias_decomp hbias_component_bound
      hbias_component_bound_tendsto)

/--
Retrospective PATE eventual score-cell version with finite `L1(P)` bracketing
mass evidence and finite-component score/bias error bounds.
-/
theorem
    retrospective_pate_actualBootstrapVariance_tendsto_of_eventually_score_cell_components_l1BracketingNumber_obligations_and_finite_error_bounds
    {Bracket : Type*} [Fintype Bracket]
    (cells : Finset Cell)
    (scoreErrorComponents : Finset ScoreErrorComponent)
    (biasErrorComponents : Finset BiasErrorComponent)
    (sample : ℕ -> Finset Unit)
    (baseWeight reuseResidualWeight heterogeneity residual :
      ℕ -> Unit -> Real)
    (score : ℕ -> Unit -> Cell)
    (target denominator normalizer : Real)
    (cellBaseWeight cellReuseResidualWeight cellHeterogeneity cellResidual :
      ℕ -> Cell -> Real)
    (baseWeightLimit reuseResidualWeightLimit heterogeneityLimit
      residualLimit massLimit : Cell -> Real)
    (actualVariance scoreReplicationError biasCorrectionError : ℕ -> Real)
    (scoreErrorComponent scoreErrorComponentBound :
      ℕ -> ScoreErrorComponent -> Real)
    (biasErrorComponent biasErrorComponentBound :
      ℕ -> BiasErrorComponent -> Real)
    (herror_decomp :
      (fun index =>
        actualVariance index -
          bootstrapCenteredVarianceTarget (sample index)
            (retrospectivePATEBootstrapInfluenceContribution
              (baseWeight index) (reuseResidualWeight index)
              (heterogeneity index) (residual index))
            (baseWeight index) target denominator normalizer) =ᶠ[atTop]
        (fun index =>
          scoreReplicationError index + biasCorrectionError index))
    (hcover :
      ∀ᶠ index in atTop,
        ∀ unit, unit ∈ sample index -> score index unit ∈ cells)
    (hbase :
      ∀ᶠ index in atTop,
        ∀ unit, unit ∈ sample index ->
          cellBaseWeight index (score index unit) = baseWeight index unit)
    (hreuse :
      ∀ᶠ index in atTop,
        ∀ unit, unit ∈ sample index ->
          cellReuseResidualWeight index (score index unit) =
            reuseResidualWeight index unit)
    (hheterogeneity :
      ∀ᶠ index in atTop,
        ∀ unit, unit ∈ sample index ->
          cellHeterogeneity index (score index unit) =
            heterogeneity index unit)
    (hresidual :
      ∀ᶠ index in atTop,
        ∀ unit, unit ∈ sample index ->
          cellResidual index (score index unit) = residual index unit)
    (hbaseLimit :
      ∀ cell, cell ∈ cells ->
        Tendsto (fun index => cellBaseWeight index cell)
          atTop (nhds (baseWeightLimit cell)))
    (hreuseLimit :
      ∀ cell, cell ∈ cells ->
        Tendsto (fun index => cellReuseResidualWeight index cell)
          atTop (nhds (reuseResidualWeightLimit cell)))
    (hheterogeneityLimit :
      ∀ cell, cell ∈ cells ->
        Tendsto (fun index => cellHeterogeneity index cell)
          atTop (nhds (heterogeneityLimit cell)))
    (hresidualLimit :
      ∀ cell, cell ∈ cells ->
        Tendsto (fun index => cellResidual index cell)
          atTop (nhds (residualLimit cell)))
    (obligations :
      L1BracketingNumberConstructorObligations (Bracket := Bracket)
        {cell : Cell | cell ∈ cells} massLimit
        (fun sampleSize cell =>
          weightedSampleSum (sample sampleSize)
            ((fun _index _unit => 1) sampleSize)
            (scoreCellIndicator (score sampleSize) cell)))
    (hscore_decomp :
      scoreReplicationError =ᶠ[atTop]
        (fun index => ∑ component ∈ scoreErrorComponents,
          scoreErrorComponent index component))
    (hscore_component_bound :
      ∀ᶠ index in atTop,
        ∀ component, component ∈ scoreErrorComponents ->
          |scoreErrorComponent index component| ≤
            scoreErrorComponentBound index component)
    (hscore_component_bound_tendsto :
      ∀ component, component ∈ scoreErrorComponents ->
        Tendsto (fun index => scoreErrorComponentBound index component)
          atTop (nhds 0))
    (hbias_decomp :
      biasCorrectionError =ᶠ[atTop]
        (fun index => ∑ component ∈ biasErrorComponents,
          biasErrorComponent index component))
    (hbias_component_bound :
      ∀ᶠ index in atTop,
        ∀ component, component ∈ biasErrorComponents ->
          |biasErrorComponent index component| ≤
            biasErrorComponentBound index component)
    (hbias_component_bound_tendsto :
      ∀ component, component ∈ biasErrorComponents ->
        Tendsto (fun index => biasErrorComponentBound index component)
          atTop (nhds 0)) :
    Tendsto actualVariance atTop
      (nhds
        ((1 / denominator ^ 2) * (1 / normalizer) *
          weightedScoreCellMomentLimit cells
            (fun cell =>
              (pateBootstrapScoreCellContribution baseWeightLimit
                    reuseResidualWeightLimit heterogeneityLimit
                    residualLimit cell -
                  target * baseWeightLimit cell) ^ 2)
            massLimit)) :=
  tendsto_actualBootstrapVariance_of_eventually_cell_contribution_weight_limits_l1BracketingNumber_obligations_and_finite_error_bounds
    (Bracket := Bracket) cells scoreErrorComponents biasErrorComponents
    sample score
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
    biasCorrectionError scoreErrorComponent scoreErrorComponentBound
    biasErrorComponent biasErrorComponentBound herror_decomp hcover
    (by
      filter_upwards [hbase, hreuse, hheterogeneity, hresidual] with index
        hbaseIndex hreuseIndex hheterogeneityIndex hresidualIndex unit hunit
      unfold pateBootstrapScoreCellContribution
        retrospectivePATEBootstrapInfluenceContribution
      rw [hbaseIndex unit hunit, hreuseIndex unit hunit,
        hheterogeneityIndex unit hunit, hresidualIndex unit hunit])
    hbase
    (tendsto_pateBootstrapScoreCellContribution_of_component_limits
      (l := atTop) cells cellBaseWeight cellReuseResidualWeight
      cellHeterogeneity cellResidual baseWeightLimit
      reuseResidualWeightLimit heterogeneityLimit residualLimit hbaseLimit
      hreuseLimit hheterogeneityLimit hresidualLimit)
    hbaseLimit obligations hscore_decomp hscore_component_bound
    hscore_component_bound_tendsto hbias_decomp hbias_component_bound
    hbias_component_bound_tendsto

/--
Retrospective PATE eventual score-cell version with VdV&W endpoint-assembly
mass evidence and finite-component score/bias error bounds.
-/
theorem
    retrospective_pate_actualBootstrapVariance_tendsto_of_eventually_score_cell_components_vdvw241_endpoint_assembly_and_finite_error_bounds
    {Bracket : Type*} [Fintype Bracket]
    (cells : Finset Cell)
    (scoreErrorComponents : Finset ScoreErrorComponent)
    (biasErrorComponents : Finset BiasErrorComponent)
    (sample : ℕ -> Finset Unit)
    (baseWeight reuseResidualWeight heterogeneity residual :
      ℕ -> Unit -> Real)
    (score : ℕ -> Unit -> Cell)
    (target denominator normalizer : Real)
    (cellBaseWeight cellReuseResidualWeight cellHeterogeneity cellResidual :
      ℕ -> Cell -> Real)
    (baseWeightLimit reuseResidualWeightLimit heterogeneityLimit
      residualLimit massLimit : Cell -> Real)
    (actualVariance scoreReplicationError biasCorrectionError : ℕ -> Real)
    (scoreErrorComponent scoreErrorComponentBound :
      ℕ -> ScoreErrorComponent -> Real)
    (biasErrorComponent biasErrorComponentBound :
      ℕ -> BiasErrorComponent -> Real)
    (herror_decomp :
      (fun index =>
        actualVariance index -
          bootstrapCenteredVarianceTarget (sample index)
            (retrospectivePATEBootstrapInfluenceContribution
              (baseWeight index) (reuseResidualWeight index)
              (heterogeneity index) (residual index))
            (baseWeight index) target denominator normalizer) =ᶠ[atTop]
        (fun index =>
          scoreReplicationError index + biasCorrectionError index))
    (hcover :
      ∀ᶠ index in atTop,
        ∀ unit, unit ∈ sample index -> score index unit ∈ cells)
    (hbase :
      ∀ᶠ index in atTop,
        ∀ unit, unit ∈ sample index ->
          cellBaseWeight index (score index unit) = baseWeight index unit)
    (hreuse :
      ∀ᶠ index in atTop,
        ∀ unit, unit ∈ sample index ->
          cellReuseResidualWeight index (score index unit) =
            reuseResidualWeight index unit)
    (hheterogeneity :
      ∀ᶠ index in atTop,
        ∀ unit, unit ∈ sample index ->
          cellHeterogeneity index (score index unit) =
            heterogeneity index unit)
    (hresidual :
      ∀ᶠ index in atTop,
        ∀ unit, unit ∈ sample index ->
          cellResidual index (score index unit) = residual index unit)
    (hbaseLimit :
      ∀ cell, cell ∈ cells ->
        Tendsto (fun index => cellBaseWeight index cell)
          atTop (nhds (baseWeightLimit cell)))
    (hreuseLimit :
      ∀ cell, cell ∈ cells ->
        Tendsto (fun index => cellReuseResidualWeight index cell)
          atTop (nhds (reuseResidualWeightLimit cell)))
    (hheterogeneityLimit :
      ∀ cell, cell ∈ cells ->
        Tendsto (fun index => cellHeterogeneity index cell)
          atTop (nhds (heterogeneityLimit cell)))
    (hresidualLimit :
      ∀ cell, cell ∈ cells ->
        Tendsto (fun index => cellResidual index cell)
          atTop (nhds (residualLimit cell)))
    (assembly :
      FiniteBracketEndpointStrongLawAssembly (Bracket := Bracket)
        {cell : Cell | cell ∈ cells} massLimit
        (fun sampleSize cell =>
          weightedSampleSum (sample sampleSize)
            ((fun _index _unit => 1) sampleSize)
            (scoreCellIndicator (score sampleSize) cell)))
    (hscore_decomp :
      scoreReplicationError =ᶠ[atTop]
        (fun index => ∑ component ∈ scoreErrorComponents,
          scoreErrorComponent index component))
    (hscore_component_bound :
      ∀ᶠ index in atTop,
        ∀ component, component ∈ scoreErrorComponents ->
          |scoreErrorComponent index component| ≤
            scoreErrorComponentBound index component)
    (hscore_component_bound_tendsto :
      ∀ component, component ∈ scoreErrorComponents ->
        Tendsto (fun index => scoreErrorComponentBound index component)
          atTop (nhds 0))
    (hbias_decomp :
      biasCorrectionError =ᶠ[atTop]
        (fun index => ∑ component ∈ biasErrorComponents,
          biasErrorComponent index component))
    (hbias_component_bound :
      ∀ᶠ index in atTop,
        ∀ component, component ∈ biasErrorComponents ->
          |biasErrorComponent index component| ≤
            biasErrorComponentBound index component)
    (hbias_component_bound_tendsto :
      ∀ component, component ∈ biasErrorComponents ->
        Tendsto (fun index => biasErrorComponentBound index component)
          atTop (nhds 0)) :
    Tendsto actualVariance atTop
      (nhds
        ((1 / denominator ^ 2) * (1 / normalizer) *
          weightedScoreCellMomentLimit cells
            (fun cell =>
              (pateBootstrapScoreCellContribution baseWeightLimit
                    reuseResidualWeightLimit heterogeneityLimit
                    residualLimit cell -
                  target * baseWeightLimit cell) ^ 2)
            massLimit)) :=
  tendsto_actualBootstrapVariance_of_eventually_cell_contribution_weight_limits_vdvw241_endpoint_assembly_and_finite_error_bounds
    (Bracket := Bracket) cells scoreErrorComponents biasErrorComponents
    sample score
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
    biasCorrectionError scoreErrorComponent scoreErrorComponentBound
    biasErrorComponent biasErrorComponentBound herror_decomp hcover
    (by
      filter_upwards [hbase, hreuse, hheterogeneity, hresidual] with index
        hbaseIndex hreuseIndex hheterogeneityIndex hresidualIndex unit hunit
      unfold pateBootstrapScoreCellContribution
        retrospectivePATEBootstrapInfluenceContribution
      rw [hbaseIndex unit hunit, hreuseIndex unit hunit,
        hheterogeneityIndex unit hunit, hresidualIndex unit hunit])
    hbase
    (tendsto_pateBootstrapScoreCellContribution_of_component_limits
      (l := atTop) cells cellBaseWeight cellReuseResidualWeight
      cellHeterogeneity cellResidual baseWeightLimit
      reuseResidualWeightLimit heterogeneityLimit residualLimit hbaseLimit
      hreuseLimit hheterogeneityLimit hresidualLimit)
    hbaseLimit assembly hscore_decomp hscore_component_bound
    hscore_component_bound_tendsto hbias_decomp hbias_component_bound
    hbias_component_bound_tendsto

/--
Prospective PATE eventual score-cell version with finite-component score/bias
error bounds.
-/
theorem prospective_pate_actualBootstrapVariance_tendsto_of_eventually_score_cell_components_and_finite_error_bounds
    (cells : Finset Cell)
    (scoreErrorComponents : Finset ScoreErrorComponent)
    (biasErrorComponents : Finset BiasErrorComponent)
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
    (scoreErrorComponent scoreErrorComponentBound :
      Index -> ScoreErrorComponent -> Real)
    (biasErrorComponent biasErrorComponentBound :
      Index -> BiasErrorComponent -> Real)
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
    (hscore_decomp :
      scoreReplicationError =ᶠ[l]
        (fun index => ∑ component ∈ scoreErrorComponents,
          scoreErrorComponent index component))
    (hscore_component_bound :
      ∀ᶠ index in l,
        ∀ component, component ∈ scoreErrorComponents ->
          |scoreErrorComponent index component| ≤
            scoreErrorComponentBound index component)
    (hscore_component_bound_tendsto :
      ∀ component, component ∈ scoreErrorComponents ->
        Tendsto (fun index => scoreErrorComponentBound index component)
          l (nhds 0))
    (hbias_decomp :
      biasCorrectionError =ᶠ[l]
        (fun index => ∑ component ∈ biasErrorComponents,
          biasErrorComponent index component))
    (hbias_component_bound :
      ∀ᶠ index in l,
        ∀ component, component ∈ biasErrorComponents ->
          |biasErrorComponent index component| ≤
            biasErrorComponentBound index component)
    (hbias_component_bound_tendsto :
      ∀ component, component ∈ biasErrorComponents ->
        Tendsto (fun index => biasErrorComponentBound index component)
          l (nhds 0)) :
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
  prospective_pate_actualBootstrapVariance_tendsto_of_eventually_score_cell_components
    (l := l) cells sample baseWeight reuseResidualWeight heterogeneity
    residual score target denominator normalizer cellBaseWeight
    cellReuseResidualWeight cellHeterogeneity cellResidual baseWeightLimit
    reuseResidualWeightLimit heterogeneityLimit residualLimit massLimit
    actualVariance scoreReplicationError biasCorrectionError herror_decomp
    hcover hbase hreuse hheterogeneity hresidual hbaseLimit hreuseLimit
    hheterogeneityLimit hresidualLimit hmass
    (bootstrapScoreReplicationErrorNegligible_of_finite_component_bounds
      (l := l) scoreErrorComponents scoreReplicationError
      scoreErrorComponent scoreErrorComponentBound hscore_decomp
      hscore_component_bound hscore_component_bound_tendsto)
    (bootstrapBiasCorrectionErrorNegligible_of_finite_component_bounds
      (l := l) biasErrorComponents biasCorrectionError biasErrorComponent
      biasErrorComponentBound hbias_decomp hbias_component_bound
      hbias_component_bound_tendsto)

/--
Prospective PATE eventual score-cell version with finite `L1(P)` bracketing
mass evidence and finite-component score/bias error bounds.
-/
theorem
    prospective_pate_actualBootstrapVariance_tendsto_of_eventually_score_cell_components_l1BracketingNumber_obligations_and_finite_error_bounds
    {Bracket : Type*} [Fintype Bracket]
    (cells : Finset Cell)
    (scoreErrorComponents : Finset ScoreErrorComponent)
    (biasErrorComponents : Finset BiasErrorComponent)
    (sample : ℕ -> Finset Unit)
    (baseWeight reuseResidualWeight heterogeneity residual :
      ℕ -> Unit -> Real)
    (score : ℕ -> Unit -> Cell)
    (target denominator normalizer : Real)
    (cellBaseWeight cellReuseResidualWeight cellHeterogeneity cellResidual :
      ℕ -> Cell -> Real)
    (baseWeightLimit reuseResidualWeightLimit heterogeneityLimit
      residualLimit massLimit : Cell -> Real)
    (actualVariance scoreReplicationError biasCorrectionError : ℕ -> Real)
    (scoreErrorComponent scoreErrorComponentBound :
      ℕ -> ScoreErrorComponent -> Real)
    (biasErrorComponent biasErrorComponentBound :
      ℕ -> BiasErrorComponent -> Real)
    (herror_decomp :
      (fun index =>
        actualVariance index -
          bootstrapCenteredVarianceTarget (sample index)
            (prospectivePATEBootstrapInfluenceContribution
              (baseWeight index) (reuseResidualWeight index)
              (heterogeneity index) (residual index))
            (baseWeight index) target denominator normalizer) =ᶠ[atTop]
        (fun index =>
          scoreReplicationError index + biasCorrectionError index))
    (hcover :
      ∀ᶠ index in atTop,
        ∀ unit, unit ∈ sample index -> score index unit ∈ cells)
    (hbase :
      ∀ᶠ index in atTop,
        ∀ unit, unit ∈ sample index ->
          cellBaseWeight index (score index unit) = baseWeight index unit)
    (hreuse :
      ∀ᶠ index in atTop,
        ∀ unit, unit ∈ sample index ->
          cellReuseResidualWeight index (score index unit) =
            reuseResidualWeight index unit)
    (hheterogeneity :
      ∀ᶠ index in atTop,
        ∀ unit, unit ∈ sample index ->
          cellHeterogeneity index (score index unit) =
            heterogeneity index unit)
    (hresidual :
      ∀ᶠ index in atTop,
        ∀ unit, unit ∈ sample index ->
          cellResidual index (score index unit) = residual index unit)
    (hbaseLimit :
      ∀ cell, cell ∈ cells ->
        Tendsto (fun index => cellBaseWeight index cell)
          atTop (nhds (baseWeightLimit cell)))
    (hreuseLimit :
      ∀ cell, cell ∈ cells ->
        Tendsto (fun index => cellReuseResidualWeight index cell)
          atTop (nhds (reuseResidualWeightLimit cell)))
    (hheterogeneityLimit :
      ∀ cell, cell ∈ cells ->
        Tendsto (fun index => cellHeterogeneity index cell)
          atTop (nhds (heterogeneityLimit cell)))
    (hresidualLimit :
      ∀ cell, cell ∈ cells ->
        Tendsto (fun index => cellResidual index cell)
          atTop (nhds (residualLimit cell)))
    (obligations :
      L1BracketingNumberConstructorObligations (Bracket := Bracket)
        {cell : Cell | cell ∈ cells} massLimit
        (fun sampleSize cell =>
          weightedSampleSum (sample sampleSize)
            ((fun _index _unit => 1) sampleSize)
            (scoreCellIndicator (score sampleSize) cell)))
    (hscore_decomp :
      scoreReplicationError =ᶠ[atTop]
        (fun index => ∑ component ∈ scoreErrorComponents,
          scoreErrorComponent index component))
    (hscore_component_bound :
      ∀ᶠ index in atTop,
        ∀ component, component ∈ scoreErrorComponents ->
          |scoreErrorComponent index component| ≤
            scoreErrorComponentBound index component)
    (hscore_component_bound_tendsto :
      ∀ component, component ∈ scoreErrorComponents ->
        Tendsto (fun index => scoreErrorComponentBound index component)
          atTop (nhds 0))
    (hbias_decomp :
      biasCorrectionError =ᶠ[atTop]
        (fun index => ∑ component ∈ biasErrorComponents,
          biasErrorComponent index component))
    (hbias_component_bound :
      ∀ᶠ index in atTop,
        ∀ component, component ∈ biasErrorComponents ->
          |biasErrorComponent index component| ≤
            biasErrorComponentBound index component)
    (hbias_component_bound_tendsto :
      ∀ component, component ∈ biasErrorComponents ->
        Tendsto (fun index => biasErrorComponentBound index component)
          atTop (nhds 0)) :
    Tendsto actualVariance atTop
      (nhds
        ((1 / denominator ^ 2) * (1 / normalizer) *
          weightedScoreCellMomentLimit cells
            (fun cell =>
              (pateBootstrapScoreCellContribution baseWeightLimit
                    reuseResidualWeightLimit heterogeneityLimit
                    residualLimit cell -
                  target * baseWeightLimit cell) ^ 2)
            massLimit)) :=
  tendsto_actualBootstrapVariance_of_eventually_cell_contribution_weight_limits_l1BracketingNumber_obligations_and_finite_error_bounds
    (Bracket := Bracket) cells scoreErrorComponents biasErrorComponents
    sample score
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
    biasCorrectionError scoreErrorComponent scoreErrorComponentBound
    biasErrorComponent biasErrorComponentBound herror_decomp hcover
    (by
      filter_upwards [hbase, hreuse, hheterogeneity, hresidual] with index
        hbaseIndex hreuseIndex hheterogeneityIndex hresidualIndex unit hunit
      unfold pateBootstrapScoreCellContribution
        prospectivePATEBootstrapInfluenceContribution
      rw [hbaseIndex unit hunit, hreuseIndex unit hunit,
        hheterogeneityIndex unit hunit, hresidualIndex unit hunit])
    hbase
    (tendsto_pateBootstrapScoreCellContribution_of_component_limits
      (l := atTop) cells cellBaseWeight cellReuseResidualWeight
      cellHeterogeneity cellResidual baseWeightLimit
      reuseResidualWeightLimit heterogeneityLimit residualLimit hbaseLimit
      hreuseLimit hheterogeneityLimit hresidualLimit)
    hbaseLimit obligations hscore_decomp hscore_component_bound
    hscore_component_bound_tendsto hbias_decomp hbias_component_bound
    hbias_component_bound_tendsto

/--
Prospective PATE eventual score-cell version with VdV&W endpoint-assembly
mass evidence and finite-component score/bias error bounds.
-/
theorem
    prospective_pate_actualBootstrapVariance_tendsto_of_eventually_score_cell_components_vdvw241_endpoint_assembly_and_finite_error_bounds
    {Bracket : Type*} [Fintype Bracket]
    (cells : Finset Cell)
    (scoreErrorComponents : Finset ScoreErrorComponent)
    (biasErrorComponents : Finset BiasErrorComponent)
    (sample : ℕ -> Finset Unit)
    (baseWeight reuseResidualWeight heterogeneity residual :
      ℕ -> Unit -> Real)
    (score : ℕ -> Unit -> Cell)
    (target denominator normalizer : Real)
    (cellBaseWeight cellReuseResidualWeight cellHeterogeneity cellResidual :
      ℕ -> Cell -> Real)
    (baseWeightLimit reuseResidualWeightLimit heterogeneityLimit
      residualLimit massLimit : Cell -> Real)
    (actualVariance scoreReplicationError biasCorrectionError : ℕ -> Real)
    (scoreErrorComponent scoreErrorComponentBound :
      ℕ -> ScoreErrorComponent -> Real)
    (biasErrorComponent biasErrorComponentBound :
      ℕ -> BiasErrorComponent -> Real)
    (herror_decomp :
      (fun index =>
        actualVariance index -
          bootstrapCenteredVarianceTarget (sample index)
            (prospectivePATEBootstrapInfluenceContribution
              (baseWeight index) (reuseResidualWeight index)
              (heterogeneity index) (residual index))
            (baseWeight index) target denominator normalizer) =ᶠ[atTop]
        (fun index =>
          scoreReplicationError index + biasCorrectionError index))
    (hcover :
      ∀ᶠ index in atTop,
        ∀ unit, unit ∈ sample index -> score index unit ∈ cells)
    (hbase :
      ∀ᶠ index in atTop,
        ∀ unit, unit ∈ sample index ->
          cellBaseWeight index (score index unit) = baseWeight index unit)
    (hreuse :
      ∀ᶠ index in atTop,
        ∀ unit, unit ∈ sample index ->
          cellReuseResidualWeight index (score index unit) =
            reuseResidualWeight index unit)
    (hheterogeneity :
      ∀ᶠ index in atTop,
        ∀ unit, unit ∈ sample index ->
          cellHeterogeneity index (score index unit) =
            heterogeneity index unit)
    (hresidual :
      ∀ᶠ index in atTop,
        ∀ unit, unit ∈ sample index ->
          cellResidual index (score index unit) = residual index unit)
    (hbaseLimit :
      ∀ cell, cell ∈ cells ->
        Tendsto (fun index => cellBaseWeight index cell)
          atTop (nhds (baseWeightLimit cell)))
    (hreuseLimit :
      ∀ cell, cell ∈ cells ->
        Tendsto (fun index => cellReuseResidualWeight index cell)
          atTop (nhds (reuseResidualWeightLimit cell)))
    (hheterogeneityLimit :
      ∀ cell, cell ∈ cells ->
        Tendsto (fun index => cellHeterogeneity index cell)
          atTop (nhds (heterogeneityLimit cell)))
    (hresidualLimit :
      ∀ cell, cell ∈ cells ->
        Tendsto (fun index => cellResidual index cell)
          atTop (nhds (residualLimit cell)))
    (assembly :
      FiniteBracketEndpointStrongLawAssembly (Bracket := Bracket)
        {cell : Cell | cell ∈ cells} massLimit
        (fun sampleSize cell =>
          weightedSampleSum (sample sampleSize)
            ((fun _index _unit => 1) sampleSize)
            (scoreCellIndicator (score sampleSize) cell)))
    (hscore_decomp :
      scoreReplicationError =ᶠ[atTop]
        (fun index => ∑ component ∈ scoreErrorComponents,
          scoreErrorComponent index component))
    (hscore_component_bound :
      ∀ᶠ index in atTop,
        ∀ component, component ∈ scoreErrorComponents ->
          |scoreErrorComponent index component| ≤
            scoreErrorComponentBound index component)
    (hscore_component_bound_tendsto :
      ∀ component, component ∈ scoreErrorComponents ->
        Tendsto (fun index => scoreErrorComponentBound index component)
          atTop (nhds 0))
    (hbias_decomp :
      biasCorrectionError =ᶠ[atTop]
        (fun index => ∑ component ∈ biasErrorComponents,
          biasErrorComponent index component))
    (hbias_component_bound :
      ∀ᶠ index in atTop,
        ∀ component, component ∈ biasErrorComponents ->
          |biasErrorComponent index component| ≤
            biasErrorComponentBound index component)
    (hbias_component_bound_tendsto :
      ∀ component, component ∈ biasErrorComponents ->
        Tendsto (fun index => biasErrorComponentBound index component)
          atTop (nhds 0)) :
    Tendsto actualVariance atTop
      (nhds
        ((1 / denominator ^ 2) * (1 / normalizer) *
          weightedScoreCellMomentLimit cells
            (fun cell =>
              (pateBootstrapScoreCellContribution baseWeightLimit
                    reuseResidualWeightLimit heterogeneityLimit
                    residualLimit cell -
                  target * baseWeightLimit cell) ^ 2)
            massLimit)) :=
  tendsto_actualBootstrapVariance_of_eventually_cell_contribution_weight_limits_vdvw241_endpoint_assembly_and_finite_error_bounds
    (Bracket := Bracket) cells scoreErrorComponents biasErrorComponents
    sample score
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
    biasCorrectionError scoreErrorComponent scoreErrorComponentBound
    biasErrorComponent biasErrorComponentBound herror_decomp hcover
    (by
      filter_upwards [hbase, hreuse, hheterogeneity, hresidual] with index
        hbaseIndex hreuseIndex hheterogeneityIndex hresidualIndex unit hunit
      unfold pateBootstrapScoreCellContribution
        prospectivePATEBootstrapInfluenceContribution
      rw [hbaseIndex unit hunit, hreuseIndex unit hunit,
        hheterogeneityIndex unit hunit, hresidualIndex unit hunit])
    hbase
    (tendsto_pateBootstrapScoreCellContribution_of_component_limits
      (l := atTop) cells cellBaseWeight cellReuseResidualWeight
      cellHeterogeneity cellResidual baseWeightLimit
      reuseResidualWeightLimit heterogeneityLimit residualLimit hbaseLimit
      hreuseLimit hheterogeneityLimit hresidualLimit)
    hbaseLimit assembly hscore_decomp hscore_component_bound
    hscore_component_bound_tendsto hbias_decomp hbias_component_bound
    hbias_component_bound_tendsto

/--
Retrospective PATT eventual score-cell version with finite-component
score/bias error bounds.
-/
theorem retrospective_patt_actualBootstrapVariance_tendsto_of_eventually_score_cell_components_and_finite_error_bounds
    (cells : Finset Cell)
    (scoreErrorComponents : Finset ScoreErrorComponent)
    (biasErrorComponents : Finset BiasErrorComponent)
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
    (scoreErrorComponent scoreErrorComponentBound :
      Index -> ScoreErrorComponent -> Real)
    (biasErrorComponent biasErrorComponentBound :
      Index -> BiasErrorComponent -> Real)
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
    (hscore_decomp :
      scoreReplicationError =ᶠ[l]
        (fun index => ∑ component ∈ scoreErrorComponents,
          scoreErrorComponent index component))
    (hscore_component_bound :
      ∀ᶠ index in l,
        ∀ component, component ∈ scoreErrorComponents ->
          |scoreErrorComponent index component| ≤
            scoreErrorComponentBound index component)
    (hscore_component_bound_tendsto :
      ∀ component, component ∈ scoreErrorComponents ->
        Tendsto (fun index => scoreErrorComponentBound index component)
          l (nhds 0))
    (hbias_decomp :
      biasCorrectionError =ᶠ[l]
        (fun index => ∑ component ∈ biasErrorComponents,
          biasErrorComponent index component))
    (hbias_component_bound :
      ∀ᶠ index in l,
        ∀ component, component ∈ biasErrorComponents ->
          |biasErrorComponent index component| ≤
            biasErrorComponentBound index component)
    (hbias_component_bound_tendsto :
      ∀ component, component ∈ biasErrorComponents ->
        Tendsto (fun index => biasErrorComponentBound index component)
          l (nhds 0)) :
    Tendsto actualVariance l
      (nhds
        ((1 / denominator ^ 2) * (1 / normalizer) *
          weightedScoreCellMomentLimit cells
            (fun cell =>
              (pattBootstrapScoreCellContribution treatedContributionLimit
                    controlReuseContributionLimit cell -
                  target * denominatorWeightLimit cell) ^ 2)
            massLimit)) :=
  retrospective_patt_actualBootstrapVariance_tendsto_of_eventually_score_cell_components
    (l := l) cells sample denominatorWeight treatedContribution
    controlReuseContribution score target denominator normalizer
    cellDenominatorWeight cellTreatedContribution cellControlReuseContribution
    denominatorWeightLimit treatedContributionLimit controlReuseContributionLimit
    massLimit actualVariance scoreReplicationError biasCorrectionError
    herror_decomp hcover hdenominator htreated hcontrol hdenominatorLimit
    htreatedLimit hcontrolLimit hmass
    (bootstrapScoreReplicationErrorNegligible_of_finite_component_bounds
      (l := l) scoreErrorComponents scoreReplicationError
      scoreErrorComponent scoreErrorComponentBound hscore_decomp
      hscore_component_bound hscore_component_bound_tendsto)
    (bootstrapBiasCorrectionErrorNegligible_of_finite_component_bounds
      (l := l) biasErrorComponents biasCorrectionError biasErrorComponent
      biasErrorComponentBound hbias_decomp hbias_component_bound
      hbias_component_bound_tendsto)

/--
Retrospective PATT eventual score-cell version with finite `L1(P)` bracketing
mass evidence and finite-component score/bias error bounds.
-/
theorem
    retrospective_patt_actualBootstrapVariance_tendsto_of_eventually_score_cell_components_l1BracketingNumber_obligations_and_finite_error_bounds
    {Bracket : Type*} [Fintype Bracket]
    (cells : Finset Cell)
    (scoreErrorComponents : Finset ScoreErrorComponent)
    (biasErrorComponents : Finset BiasErrorComponent)
    (sample : ℕ -> Finset Unit)
    (denominatorWeight treatedContribution controlReuseContribution :
      ℕ -> Unit -> Real)
    (score : ℕ -> Unit -> Cell)
    (target denominator normalizer : Real)
    (cellDenominatorWeight cellTreatedContribution
      cellControlReuseContribution : ℕ -> Cell -> Real)
    (denominatorWeightLimit treatedContributionLimit
      controlReuseContributionLimit massLimit : Cell -> Real)
    (actualVariance scoreReplicationError biasCorrectionError : ℕ -> Real)
    (scoreErrorComponent scoreErrorComponentBound :
      ℕ -> ScoreErrorComponent -> Real)
    (biasErrorComponent biasErrorComponentBound :
      ℕ -> BiasErrorComponent -> Real)
    (herror_decomp :
      (fun index =>
        actualVariance index -
          bootstrapCenteredVarianceTarget (sample index)
            (retrospectivePATTBootstrapInfluenceContribution
              (treatedContribution index) (controlReuseContribution index))
            (denominatorWeight index) target denominator normalizer) =ᶠ[atTop]
        (fun index =>
          scoreReplicationError index + biasCorrectionError index))
    (hcover :
      ∀ᶠ index in atTop,
        ∀ unit, unit ∈ sample index -> score index unit ∈ cells)
    (hdenominator :
      ∀ᶠ index in atTop,
        ∀ unit, unit ∈ sample index ->
          cellDenominatorWeight index (score index unit) =
            denominatorWeight index unit)
    (htreated :
      ∀ᶠ index in atTop,
        ∀ unit, unit ∈ sample index ->
          cellTreatedContribution index (score index unit) =
            treatedContribution index unit)
    (hcontrol :
      ∀ᶠ index in atTop,
        ∀ unit, unit ∈ sample index ->
          cellControlReuseContribution index (score index unit) =
            controlReuseContribution index unit)
    (hdenominatorLimit :
      ∀ cell, cell ∈ cells ->
        Tendsto (fun index => cellDenominatorWeight index cell)
          atTop (nhds (denominatorWeightLimit cell)))
    (htreatedLimit :
      ∀ cell, cell ∈ cells ->
        Tendsto (fun index => cellTreatedContribution index cell)
          atTop (nhds (treatedContributionLimit cell)))
    (hcontrolLimit :
      ∀ cell, cell ∈ cells ->
        Tendsto (fun index => cellControlReuseContribution index cell)
          atTop (nhds (controlReuseContributionLimit cell)))
    (obligations :
      L1BracketingNumberConstructorObligations (Bracket := Bracket)
        {cell : Cell | cell ∈ cells} massLimit
        (fun sampleSize cell =>
          weightedSampleSum (sample sampleSize)
            ((fun _index _unit => 1) sampleSize)
            (scoreCellIndicator (score sampleSize) cell)))
    (hscore_decomp :
      scoreReplicationError =ᶠ[atTop]
        (fun index => ∑ component ∈ scoreErrorComponents,
          scoreErrorComponent index component))
    (hscore_component_bound :
      ∀ᶠ index in atTop,
        ∀ component, component ∈ scoreErrorComponents ->
          |scoreErrorComponent index component| ≤
            scoreErrorComponentBound index component)
    (hscore_component_bound_tendsto :
      ∀ component, component ∈ scoreErrorComponents ->
        Tendsto (fun index => scoreErrorComponentBound index component)
          atTop (nhds 0))
    (hbias_decomp :
      biasCorrectionError =ᶠ[atTop]
        (fun index => ∑ component ∈ biasErrorComponents,
          biasErrorComponent index component))
    (hbias_component_bound :
      ∀ᶠ index in atTop,
        ∀ component, component ∈ biasErrorComponents ->
          |biasErrorComponent index component| ≤
            biasErrorComponentBound index component)
    (hbias_component_bound_tendsto :
      ∀ component, component ∈ biasErrorComponents ->
        Tendsto (fun index => biasErrorComponentBound index component)
          atTop (nhds 0)) :
    Tendsto actualVariance atTop
      (nhds
        ((1 / denominator ^ 2) * (1 / normalizer) *
          weightedScoreCellMomentLimit cells
            (fun cell =>
              (pattBootstrapScoreCellContribution treatedContributionLimit
                    controlReuseContributionLimit cell -
                  target * denominatorWeightLimit cell) ^ 2)
            massLimit)) :=
  tendsto_actualBootstrapVariance_of_eventually_cell_contribution_weight_limits_l1BracketingNumber_obligations_and_finite_error_bounds
    (Bracket := Bracket) cells scoreErrorComponents biasErrorComponents
    sample score
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
    biasCorrectionError scoreErrorComponent scoreErrorComponentBound
    biasErrorComponent biasErrorComponentBound herror_decomp hcover
    (by
      filter_upwards [htreated, hcontrol] with index htreatedIndex
        hcontrolIndex unit hunit
      unfold pattBootstrapScoreCellContribution
        retrospectivePATTBootstrapInfluenceContribution
      rw [htreatedIndex unit hunit, hcontrolIndex unit hunit])
    hdenominator
    (tendsto_pattBootstrapScoreCellContribution_of_component_limits
      (l := atTop) cells cellTreatedContribution
      cellControlReuseContribution treatedContributionLimit
      controlReuseContributionLimit htreatedLimit hcontrolLimit)
    hdenominatorLimit obligations hscore_decomp hscore_component_bound
    hscore_component_bound_tendsto hbias_decomp hbias_component_bound
    hbias_component_bound_tendsto

/--
Retrospective PATT eventual score-cell version with VdV&W endpoint-assembly
mass evidence and finite-component score/bias error bounds.
-/
theorem
    retrospective_patt_actualBootstrapVariance_tendsto_of_eventually_score_cell_components_vdvw241_endpoint_assembly_and_finite_error_bounds
    {Bracket : Type*} [Fintype Bracket]
    (cells : Finset Cell)
    (scoreErrorComponents : Finset ScoreErrorComponent)
    (biasErrorComponents : Finset BiasErrorComponent)
    (sample : ℕ -> Finset Unit)
    (denominatorWeight treatedContribution controlReuseContribution :
      ℕ -> Unit -> Real)
    (score : ℕ -> Unit -> Cell)
    (target denominator normalizer : Real)
    (cellDenominatorWeight cellTreatedContribution
      cellControlReuseContribution : ℕ -> Cell -> Real)
    (denominatorWeightLimit treatedContributionLimit
      controlReuseContributionLimit massLimit : Cell -> Real)
    (actualVariance scoreReplicationError biasCorrectionError : ℕ -> Real)
    (scoreErrorComponent scoreErrorComponentBound :
      ℕ -> ScoreErrorComponent -> Real)
    (biasErrorComponent biasErrorComponentBound :
      ℕ -> BiasErrorComponent -> Real)
    (herror_decomp :
      (fun index =>
        actualVariance index -
          bootstrapCenteredVarianceTarget (sample index)
            (retrospectivePATTBootstrapInfluenceContribution
              (treatedContribution index) (controlReuseContribution index))
            (denominatorWeight index) target denominator normalizer) =ᶠ[atTop]
        (fun index =>
          scoreReplicationError index + biasCorrectionError index))
    (hcover :
      ∀ᶠ index in atTop,
        ∀ unit, unit ∈ sample index -> score index unit ∈ cells)
    (hdenominator :
      ∀ᶠ index in atTop,
        ∀ unit, unit ∈ sample index ->
          cellDenominatorWeight index (score index unit) =
            denominatorWeight index unit)
    (htreated :
      ∀ᶠ index in atTop,
        ∀ unit, unit ∈ sample index ->
          cellTreatedContribution index (score index unit) =
            treatedContribution index unit)
    (hcontrol :
      ∀ᶠ index in atTop,
        ∀ unit, unit ∈ sample index ->
          cellControlReuseContribution index (score index unit) =
            controlReuseContribution index unit)
    (hdenominatorLimit :
      ∀ cell, cell ∈ cells ->
        Tendsto (fun index => cellDenominatorWeight index cell)
          atTop (nhds (denominatorWeightLimit cell)))
    (htreatedLimit :
      ∀ cell, cell ∈ cells ->
        Tendsto (fun index => cellTreatedContribution index cell)
          atTop (nhds (treatedContributionLimit cell)))
    (hcontrolLimit :
      ∀ cell, cell ∈ cells ->
        Tendsto (fun index => cellControlReuseContribution index cell)
          atTop (nhds (controlReuseContributionLimit cell)))
    (assembly :
      FiniteBracketEndpointStrongLawAssembly (Bracket := Bracket)
        {cell : Cell | cell ∈ cells} massLimit
        (fun sampleSize cell =>
          weightedSampleSum (sample sampleSize)
            ((fun _index _unit => 1) sampleSize)
            (scoreCellIndicator (score sampleSize) cell)))
    (hscore_decomp :
      scoreReplicationError =ᶠ[atTop]
        (fun index => ∑ component ∈ scoreErrorComponents,
          scoreErrorComponent index component))
    (hscore_component_bound :
      ∀ᶠ index in atTop,
        ∀ component, component ∈ scoreErrorComponents ->
          |scoreErrorComponent index component| ≤
            scoreErrorComponentBound index component)
    (hscore_component_bound_tendsto :
      ∀ component, component ∈ scoreErrorComponents ->
        Tendsto (fun index => scoreErrorComponentBound index component)
          atTop (nhds 0))
    (hbias_decomp :
      biasCorrectionError =ᶠ[atTop]
        (fun index => ∑ component ∈ biasErrorComponents,
          biasErrorComponent index component))
    (hbias_component_bound :
      ∀ᶠ index in atTop,
        ∀ component, component ∈ biasErrorComponents ->
          |biasErrorComponent index component| ≤
            biasErrorComponentBound index component)
    (hbias_component_bound_tendsto :
      ∀ component, component ∈ biasErrorComponents ->
        Tendsto (fun index => biasErrorComponentBound index component)
          atTop (nhds 0)) :
    Tendsto actualVariance atTop
      (nhds
        ((1 / denominator ^ 2) * (1 / normalizer) *
          weightedScoreCellMomentLimit cells
            (fun cell =>
              (pattBootstrapScoreCellContribution treatedContributionLimit
                    controlReuseContributionLimit cell -
                  target * denominatorWeightLimit cell) ^ 2)
            massLimit)) :=
  tendsto_actualBootstrapVariance_of_eventually_cell_contribution_weight_limits_vdvw241_endpoint_assembly_and_finite_error_bounds
    (Bracket := Bracket) cells scoreErrorComponents biasErrorComponents
    sample score
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
    biasCorrectionError scoreErrorComponent scoreErrorComponentBound
    biasErrorComponent biasErrorComponentBound herror_decomp hcover
    (by
      filter_upwards [htreated, hcontrol] with index htreatedIndex
        hcontrolIndex unit hunit
      unfold pattBootstrapScoreCellContribution
        retrospectivePATTBootstrapInfluenceContribution
      rw [htreatedIndex unit hunit, hcontrolIndex unit hunit])
    hdenominator
    (tendsto_pattBootstrapScoreCellContribution_of_component_limits
      (l := atTop) cells cellTreatedContribution
      cellControlReuseContribution treatedContributionLimit
      controlReuseContributionLimit htreatedLimit hcontrolLimit)
    hdenominatorLimit assembly hscore_decomp hscore_component_bound
    hscore_component_bound_tendsto hbias_decomp hbias_component_bound
    hbias_component_bound_tendsto

/--
Prospective PATT eventual score-cell version with finite-component score/bias
error bounds.
-/
theorem prospective_patt_actualBootstrapVariance_tendsto_of_eventually_score_cell_components_and_finite_error_bounds
    (cells : Finset Cell)
    (scoreErrorComponents : Finset ScoreErrorComponent)
    (biasErrorComponents : Finset BiasErrorComponent)
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
    (scoreErrorComponent scoreErrorComponentBound :
      Index -> ScoreErrorComponent -> Real)
    (biasErrorComponent biasErrorComponentBound :
      Index -> BiasErrorComponent -> Real)
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
    (hscore_decomp :
      scoreReplicationError =ᶠ[l]
        (fun index => ∑ component ∈ scoreErrorComponents,
          scoreErrorComponent index component))
    (hscore_component_bound :
      ∀ᶠ index in l,
        ∀ component, component ∈ scoreErrorComponents ->
          |scoreErrorComponent index component| ≤
            scoreErrorComponentBound index component)
    (hscore_component_bound_tendsto :
      ∀ component, component ∈ scoreErrorComponents ->
        Tendsto (fun index => scoreErrorComponentBound index component)
          l (nhds 0))
    (hbias_decomp :
      biasCorrectionError =ᶠ[l]
        (fun index => ∑ component ∈ biasErrorComponents,
          biasErrorComponent index component))
    (hbias_component_bound :
      ∀ᶠ index in l,
        ∀ component, component ∈ biasErrorComponents ->
          |biasErrorComponent index component| ≤
            biasErrorComponentBound index component)
    (hbias_component_bound_tendsto :
      ∀ component, component ∈ biasErrorComponents ->
        Tendsto (fun index => biasErrorComponentBound index component)
          l (nhds 0)) :
    Tendsto actualVariance l
      (nhds
        ((1 / denominator ^ 2) * (1 / normalizer) *
          weightedScoreCellMomentLimit cells
            (fun cell =>
              (pattBootstrapScoreCellContribution treatedContributionLimit
                    controlReuseContributionLimit cell -
                  target * denominatorWeightLimit cell) ^ 2)
            massLimit)) :=
  prospective_patt_actualBootstrapVariance_tendsto_of_eventually_score_cell_components
    (l := l) cells sample denominatorWeight treatedContribution
    controlReuseContribution score target denominator normalizer
    cellDenominatorWeight cellTreatedContribution cellControlReuseContribution
    denominatorWeightLimit treatedContributionLimit controlReuseContributionLimit
    massLimit actualVariance scoreReplicationError biasCorrectionError
    herror_decomp hcover hdenominator htreated hcontrol hdenominatorLimit
    htreatedLimit hcontrolLimit hmass
    (bootstrapScoreReplicationErrorNegligible_of_finite_component_bounds
      (l := l) scoreErrorComponents scoreReplicationError
      scoreErrorComponent scoreErrorComponentBound hscore_decomp
      hscore_component_bound hscore_component_bound_tendsto)
    (bootstrapBiasCorrectionErrorNegligible_of_finite_component_bounds
      (l := l) biasErrorComponents biasCorrectionError biasErrorComponent
      biasErrorComponentBound hbias_decomp hbias_component_bound
      hbias_component_bound_tendsto)

/--
Prospective PATT eventual score-cell version with finite `L1(P)` bracketing
mass evidence and finite-component score/bias error bounds.
-/
theorem
    prospective_patt_actualBootstrapVariance_tendsto_of_eventually_score_cell_components_l1BracketingNumber_obligations_and_finite_error_bounds
    {Bracket : Type*} [Fintype Bracket]
    (cells : Finset Cell)
    (scoreErrorComponents : Finset ScoreErrorComponent)
    (biasErrorComponents : Finset BiasErrorComponent)
    (sample : ℕ -> Finset Unit)
    (denominatorWeight treatedContribution controlReuseContribution :
      ℕ -> Unit -> Real)
    (score : ℕ -> Unit -> Cell)
    (target denominator normalizer : Real)
    (cellDenominatorWeight cellTreatedContribution
      cellControlReuseContribution : ℕ -> Cell -> Real)
    (denominatorWeightLimit treatedContributionLimit
      controlReuseContributionLimit massLimit : Cell -> Real)
    (actualVariance scoreReplicationError biasCorrectionError : ℕ -> Real)
    (scoreErrorComponent scoreErrorComponentBound :
      ℕ -> ScoreErrorComponent -> Real)
    (biasErrorComponent biasErrorComponentBound :
      ℕ -> BiasErrorComponent -> Real)
    (herror_decomp :
      (fun index =>
        actualVariance index -
          bootstrapCenteredVarianceTarget (sample index)
            (prospectivePATTBootstrapInfluenceContribution
              (treatedContribution index) (controlReuseContribution index))
            (denominatorWeight index) target denominator normalizer) =ᶠ[atTop]
        (fun index =>
          scoreReplicationError index + biasCorrectionError index))
    (hcover :
      ∀ᶠ index in atTop,
        ∀ unit, unit ∈ sample index -> score index unit ∈ cells)
    (hdenominator :
      ∀ᶠ index in atTop,
        ∀ unit, unit ∈ sample index ->
          cellDenominatorWeight index (score index unit) =
            denominatorWeight index unit)
    (htreated :
      ∀ᶠ index in atTop,
        ∀ unit, unit ∈ sample index ->
          cellTreatedContribution index (score index unit) =
            treatedContribution index unit)
    (hcontrol :
      ∀ᶠ index in atTop,
        ∀ unit, unit ∈ sample index ->
          cellControlReuseContribution index (score index unit) =
            controlReuseContribution index unit)
    (hdenominatorLimit :
      ∀ cell, cell ∈ cells ->
        Tendsto (fun index => cellDenominatorWeight index cell)
          atTop (nhds (denominatorWeightLimit cell)))
    (htreatedLimit :
      ∀ cell, cell ∈ cells ->
        Tendsto (fun index => cellTreatedContribution index cell)
          atTop (nhds (treatedContributionLimit cell)))
    (hcontrolLimit :
      ∀ cell, cell ∈ cells ->
        Tendsto (fun index => cellControlReuseContribution index cell)
          atTop (nhds (controlReuseContributionLimit cell)))
    (obligations :
      L1BracketingNumberConstructorObligations (Bracket := Bracket)
        {cell : Cell | cell ∈ cells} massLimit
        (fun sampleSize cell =>
          weightedSampleSum (sample sampleSize)
            ((fun _index _unit => 1) sampleSize)
            (scoreCellIndicator (score sampleSize) cell)))
    (hscore_decomp :
      scoreReplicationError =ᶠ[atTop]
        (fun index => ∑ component ∈ scoreErrorComponents,
          scoreErrorComponent index component))
    (hscore_component_bound :
      ∀ᶠ index in atTop,
        ∀ component, component ∈ scoreErrorComponents ->
          |scoreErrorComponent index component| ≤
            scoreErrorComponentBound index component)
    (hscore_component_bound_tendsto :
      ∀ component, component ∈ scoreErrorComponents ->
        Tendsto (fun index => scoreErrorComponentBound index component)
          atTop (nhds 0))
    (hbias_decomp :
      biasCorrectionError =ᶠ[atTop]
        (fun index => ∑ component ∈ biasErrorComponents,
          biasErrorComponent index component))
    (hbias_component_bound :
      ∀ᶠ index in atTop,
        ∀ component, component ∈ biasErrorComponents ->
          |biasErrorComponent index component| ≤
            biasErrorComponentBound index component)
    (hbias_component_bound_tendsto :
      ∀ component, component ∈ biasErrorComponents ->
        Tendsto (fun index => biasErrorComponentBound index component)
          atTop (nhds 0)) :
    Tendsto actualVariance atTop
      (nhds
        ((1 / denominator ^ 2) * (1 / normalizer) *
          weightedScoreCellMomentLimit cells
            (fun cell =>
              (pattBootstrapScoreCellContribution treatedContributionLimit
                    controlReuseContributionLimit cell -
                  target * denominatorWeightLimit cell) ^ 2)
            massLimit)) :=
  tendsto_actualBootstrapVariance_of_eventually_cell_contribution_weight_limits_l1BracketingNumber_obligations_and_finite_error_bounds
    (Bracket := Bracket) cells scoreErrorComponents biasErrorComponents
    sample score
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
    biasCorrectionError scoreErrorComponent scoreErrorComponentBound
    biasErrorComponent biasErrorComponentBound herror_decomp hcover
    (by
      filter_upwards [htreated, hcontrol] with index htreatedIndex
        hcontrolIndex unit hunit
      unfold pattBootstrapScoreCellContribution
        prospectivePATTBootstrapInfluenceContribution
      rw [htreatedIndex unit hunit, hcontrolIndex unit hunit])
    hdenominator
    (tendsto_pattBootstrapScoreCellContribution_of_component_limits
      (l := atTop) cells cellTreatedContribution
      cellControlReuseContribution treatedContributionLimit
      controlReuseContributionLimit htreatedLimit hcontrolLimit)
    hdenominatorLimit obligations hscore_decomp hscore_component_bound
    hscore_component_bound_tendsto hbias_decomp hbias_component_bound
    hbias_component_bound_tendsto

/--
Prospective PATT eventual score-cell version with VdV&W endpoint-assembly
mass evidence and finite-component score/bias error bounds.
-/
theorem
    prospective_patt_actualBootstrapVariance_tendsto_of_eventually_score_cell_components_vdvw241_endpoint_assembly_and_finite_error_bounds
    {Bracket : Type*} [Fintype Bracket]
    (cells : Finset Cell)
    (scoreErrorComponents : Finset ScoreErrorComponent)
    (biasErrorComponents : Finset BiasErrorComponent)
    (sample : ℕ -> Finset Unit)
    (denominatorWeight treatedContribution controlReuseContribution :
      ℕ -> Unit -> Real)
    (score : ℕ -> Unit -> Cell)
    (target denominator normalizer : Real)
    (cellDenominatorWeight cellTreatedContribution
      cellControlReuseContribution : ℕ -> Cell -> Real)
    (denominatorWeightLimit treatedContributionLimit
      controlReuseContributionLimit massLimit : Cell -> Real)
    (actualVariance scoreReplicationError biasCorrectionError : ℕ -> Real)
    (scoreErrorComponent scoreErrorComponentBound :
      ℕ -> ScoreErrorComponent -> Real)
    (biasErrorComponent biasErrorComponentBound :
      ℕ -> BiasErrorComponent -> Real)
    (herror_decomp :
      (fun index =>
        actualVariance index -
          bootstrapCenteredVarianceTarget (sample index)
            (prospectivePATTBootstrapInfluenceContribution
              (treatedContribution index) (controlReuseContribution index))
            (denominatorWeight index) target denominator normalizer) =ᶠ[atTop]
        (fun index =>
          scoreReplicationError index + biasCorrectionError index))
    (hcover :
      ∀ᶠ index in atTop,
        ∀ unit, unit ∈ sample index -> score index unit ∈ cells)
    (hdenominator :
      ∀ᶠ index in atTop,
        ∀ unit, unit ∈ sample index ->
          cellDenominatorWeight index (score index unit) =
            denominatorWeight index unit)
    (htreated :
      ∀ᶠ index in atTop,
        ∀ unit, unit ∈ sample index ->
          cellTreatedContribution index (score index unit) =
            treatedContribution index unit)
    (hcontrol :
      ∀ᶠ index in atTop,
        ∀ unit, unit ∈ sample index ->
          cellControlReuseContribution index (score index unit) =
            controlReuseContribution index unit)
    (hdenominatorLimit :
      ∀ cell, cell ∈ cells ->
        Tendsto (fun index => cellDenominatorWeight index cell)
          atTop (nhds (denominatorWeightLimit cell)))
    (htreatedLimit :
      ∀ cell, cell ∈ cells ->
        Tendsto (fun index => cellTreatedContribution index cell)
          atTop (nhds (treatedContributionLimit cell)))
    (hcontrolLimit :
      ∀ cell, cell ∈ cells ->
        Tendsto (fun index => cellControlReuseContribution index cell)
          atTop (nhds (controlReuseContributionLimit cell)))
    (assembly :
      FiniteBracketEndpointStrongLawAssembly (Bracket := Bracket)
        {cell : Cell | cell ∈ cells} massLimit
        (fun sampleSize cell =>
          weightedSampleSum (sample sampleSize)
            ((fun _index _unit => 1) sampleSize)
            (scoreCellIndicator (score sampleSize) cell)))
    (hscore_decomp :
      scoreReplicationError =ᶠ[atTop]
        (fun index => ∑ component ∈ scoreErrorComponents,
          scoreErrorComponent index component))
    (hscore_component_bound :
      ∀ᶠ index in atTop,
        ∀ component, component ∈ scoreErrorComponents ->
          |scoreErrorComponent index component| ≤
            scoreErrorComponentBound index component)
    (hscore_component_bound_tendsto :
      ∀ component, component ∈ scoreErrorComponents ->
        Tendsto (fun index => scoreErrorComponentBound index component)
          atTop (nhds 0))
    (hbias_decomp :
      biasCorrectionError =ᶠ[atTop]
        (fun index => ∑ component ∈ biasErrorComponents,
          biasErrorComponent index component))
    (hbias_component_bound :
      ∀ᶠ index in atTop,
        ∀ component, component ∈ biasErrorComponents ->
          |biasErrorComponent index component| ≤
            biasErrorComponentBound index component)
    (hbias_component_bound_tendsto :
      ∀ component, component ∈ biasErrorComponents ->
        Tendsto (fun index => biasErrorComponentBound index component)
          atTop (nhds 0)) :
    Tendsto actualVariance atTop
      (nhds
        ((1 / denominator ^ 2) * (1 / normalizer) *
          weightedScoreCellMomentLimit cells
            (fun cell =>
              (pattBootstrapScoreCellContribution treatedContributionLimit
                    controlReuseContributionLimit cell -
                  target * denominatorWeightLimit cell) ^ 2)
            massLimit)) :=
  tendsto_actualBootstrapVariance_of_eventually_cell_contribution_weight_limits_vdvw241_endpoint_assembly_and_finite_error_bounds
    (Bracket := Bracket) cells scoreErrorComponents biasErrorComponents
    sample score
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
    biasCorrectionError scoreErrorComponent scoreErrorComponentBound
    biasErrorComponent biasErrorComponentBound herror_decomp hcover
    (by
      filter_upwards [htreated, hcontrol] with index htreatedIndex
        hcontrolIndex unit hunit
      unfold pattBootstrapScoreCellContribution
        prospectivePATTBootstrapInfluenceContribution
      rw [htreatedIndex unit hunit, hcontrolIndex unit hunit])
    hdenominator
    (tendsto_pattBootstrapScoreCellContribution_of_component_limits
      (l := atTop) cells cellTreatedContribution
      cellControlReuseContribution treatedContributionLimit
      controlReuseContributionLimit htreatedLimit hcontrolLimit)
    hdenominatorLimit assembly hscore_decomp hscore_component_bound
    hscore_component_bound_tendsto hbias_decomp hbias_component_bound
    hbias_component_bound_tendsto

/--
Paired retrospective PATE/PATT eventual score-cell actual bootstrap variance
convergence from finite-component score/bias error bounds.
-/
theorem retrospective_pate_patt_actualBootstrapVariance_tendsto_of_eventually_score_cell_components_and_finite_error_bounds
    (pateCells : Finset Cell)
    (pateScoreErrorComponents : Finset ScoreErrorComponent)
    (pateBiasErrorComponents : Finset BiasErrorComponent)
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
    (pateScoreErrorComponent pateScoreErrorComponentBound :
      Index -> ScoreErrorComponent -> Real)
    (pateBiasErrorComponent pateBiasErrorComponentBound :
      Index -> BiasErrorComponent -> Real)
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
    (hpateScoreDecomp :
      pateScoreReplicationError =ᶠ[l]
        (fun index => ∑ component ∈ pateScoreErrorComponents,
          pateScoreErrorComponent index component))
    (hpateScoreComponentBound :
      ∀ᶠ index in l,
        ∀ component, component ∈ pateScoreErrorComponents ->
          |pateScoreErrorComponent index component| ≤
            pateScoreErrorComponentBound index component)
    (hpateScoreComponentBoundTendsto :
      ∀ component, component ∈ pateScoreErrorComponents ->
        Tendsto (fun index => pateScoreErrorComponentBound index component)
          l (nhds 0))
    (hpateBiasDecomp :
      pateBiasCorrectionError =ᶠ[l]
        (fun index => ∑ component ∈ pateBiasErrorComponents,
          pateBiasErrorComponent index component))
    (hpateBiasComponentBound :
      ∀ᶠ index in l,
        ∀ component, component ∈ pateBiasErrorComponents ->
          |pateBiasErrorComponent index component| ≤
            pateBiasErrorComponentBound index component)
    (hpateBiasComponentBoundTendsto :
      ∀ component, component ∈ pateBiasErrorComponents ->
        Tendsto (fun index => pateBiasErrorComponentBound index component)
          l (nhds 0))
    (pattCells : Finset Cell)
    (pattScoreErrorComponents : Finset ScoreErrorComponent)
    (pattBiasErrorComponents : Finset BiasErrorComponent)
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
    (pattScoreErrorComponent pattScoreErrorComponentBound :
      Index -> ScoreErrorComponent -> Real)
    (pattBiasErrorComponent pattBiasErrorComponentBound :
      Index -> BiasErrorComponent -> Real)
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
    (hpattScoreDecomp :
      pattScoreReplicationError =ᶠ[l]
        (fun index => ∑ component ∈ pattScoreErrorComponents,
          pattScoreErrorComponent index component))
    (hpattScoreComponentBound :
      ∀ᶠ index in l,
        ∀ component, component ∈ pattScoreErrorComponents ->
          |pattScoreErrorComponent index component| ≤
            pattScoreErrorComponentBound index component)
    (hpattScoreComponentBoundTendsto :
      ∀ component, component ∈ pattScoreErrorComponents ->
        Tendsto (fun index => pattScoreErrorComponentBound index component)
          l (nhds 0))
    (hpattBiasDecomp :
      pattBiasCorrectionError =ᶠ[l]
        (fun index => ∑ component ∈ pattBiasErrorComponents,
          pattBiasErrorComponent index component))
    (hpattBiasComponentBound :
      ∀ᶠ index in l,
        ∀ component, component ∈ pattBiasErrorComponents ->
          |pattBiasErrorComponent index component| ≤
            pattBiasErrorComponentBound index component)
    (hpattBiasComponentBoundTendsto :
      ∀ component, component ∈ pattBiasErrorComponents ->
        Tendsto (fun index => pattBiasErrorComponentBound index component)
          l (nhds 0)) :
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
      retrospective_pate_actualBootstrapVariance_tendsto_of_eventually_score_cell_components_and_finite_error_bounds
        (l := l) pateCells pateScoreErrorComponents
        pateBiasErrorComponents pateSample pateBaseWeight
        pateReuseResidualWeight pateHeterogeneity pateResidual pateScore
        pateTarget pateDenominator pateNormalizer pateCellBaseWeight
        pateCellReuseResidualWeight pateCellHeterogeneity pateCellResidual
        pateBaseWeightLimit pateReuseResidualWeightLimit
        pateHeterogeneityLimit pateResidualLimit pateMassLimit
        pateActualVariance pateScoreReplicationError pateBiasCorrectionError
        pateScoreErrorComponent pateScoreErrorComponentBound
        pateBiasErrorComponent pateBiasErrorComponentBound hpateErrorDecomp
        hpateCover hpateBase hpateReuse hpateHeterogeneity hpateResidual
        hpateBaseLimit hpateReuseLimit hpateHeterogeneityLimit
        hpateResidualLimit hpateMass hpateScoreDecomp
        hpateScoreComponentBound hpateScoreComponentBoundTendsto
        hpateBiasDecomp hpateBiasComponentBound hpateBiasComponentBoundTendsto
  · exact
      retrospective_patt_actualBootstrapVariance_tendsto_of_eventually_score_cell_components_and_finite_error_bounds
        (l := l) pattCells pattScoreErrorComponents
        pattBiasErrorComponents pattSample pattDenominatorWeight
        pattTreatedContribution pattControlReuseContribution pattScore
        pattTarget pattDenominator pattNormalizer pattCellDenominatorWeight
        pattCellTreatedContribution pattCellControlReuseContribution
        pattDenominatorWeightLimit pattTreatedContributionLimit
        pattControlReuseContributionLimit pattMassLimit pattActualVariance
        pattScoreReplicationError pattBiasCorrectionError
        pattScoreErrorComponent pattScoreErrorComponentBound
        pattBiasErrorComponent pattBiasErrorComponentBound hpattErrorDecomp
        hpattCover hpattDenominator hpattTreated hpattControl
        hpattDenominatorLimit hpattTreatedLimit hpattControlLimit hpattMass
        hpattScoreDecomp hpattScoreComponentBound
        hpattScoreComponentBoundTendsto hpattBiasDecomp
        hpattBiasComponentBound hpattBiasComponentBoundTendsto

/--
Paired prospective PATE/PATT eventual score-cell actual bootstrap variance
convergence from finite-component score/bias error bounds.
-/
theorem prospective_pate_patt_actualBootstrapVariance_tendsto_of_eventually_score_cell_components_and_finite_error_bounds
    (pateCells : Finset Cell)
    (pateScoreErrorComponents : Finset ScoreErrorComponent)
    (pateBiasErrorComponents : Finset BiasErrorComponent)
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
    (pateScoreErrorComponent pateScoreErrorComponentBound :
      Index -> ScoreErrorComponent -> Real)
    (pateBiasErrorComponent pateBiasErrorComponentBound :
      Index -> BiasErrorComponent -> Real)
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
    (hpateScoreDecomp :
      pateScoreReplicationError =ᶠ[l]
        (fun index => ∑ component ∈ pateScoreErrorComponents,
          pateScoreErrorComponent index component))
    (hpateScoreComponentBound :
      ∀ᶠ index in l,
        ∀ component, component ∈ pateScoreErrorComponents ->
          |pateScoreErrorComponent index component| ≤
            pateScoreErrorComponentBound index component)
    (hpateScoreComponentBoundTendsto :
      ∀ component, component ∈ pateScoreErrorComponents ->
        Tendsto (fun index => pateScoreErrorComponentBound index component)
          l (nhds 0))
    (hpateBiasDecomp :
      pateBiasCorrectionError =ᶠ[l]
        (fun index => ∑ component ∈ pateBiasErrorComponents,
          pateBiasErrorComponent index component))
    (hpateBiasComponentBound :
      ∀ᶠ index in l,
        ∀ component, component ∈ pateBiasErrorComponents ->
          |pateBiasErrorComponent index component| ≤
            pateBiasErrorComponentBound index component)
    (hpateBiasComponentBoundTendsto :
      ∀ component, component ∈ pateBiasErrorComponents ->
        Tendsto (fun index => pateBiasErrorComponentBound index component)
          l (nhds 0))
    (pattCells : Finset Cell)
    (pattScoreErrorComponents : Finset ScoreErrorComponent)
    (pattBiasErrorComponents : Finset BiasErrorComponent)
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
    (pattScoreErrorComponent pattScoreErrorComponentBound :
      Index -> ScoreErrorComponent -> Real)
    (pattBiasErrorComponent pattBiasErrorComponentBound :
      Index -> BiasErrorComponent -> Real)
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
    (hpattScoreDecomp :
      pattScoreReplicationError =ᶠ[l]
        (fun index => ∑ component ∈ pattScoreErrorComponents,
          pattScoreErrorComponent index component))
    (hpattScoreComponentBound :
      ∀ᶠ index in l,
        ∀ component, component ∈ pattScoreErrorComponents ->
          |pattScoreErrorComponent index component| ≤
            pattScoreErrorComponentBound index component)
    (hpattScoreComponentBoundTendsto :
      ∀ component, component ∈ pattScoreErrorComponents ->
        Tendsto (fun index => pattScoreErrorComponentBound index component)
          l (nhds 0))
    (hpattBiasDecomp :
      pattBiasCorrectionError =ᶠ[l]
        (fun index => ∑ component ∈ pattBiasErrorComponents,
          pattBiasErrorComponent index component))
    (hpattBiasComponentBound :
      ∀ᶠ index in l,
        ∀ component, component ∈ pattBiasErrorComponents ->
          |pattBiasErrorComponent index component| ≤
            pattBiasErrorComponentBound index component)
    (hpattBiasComponentBoundTendsto :
      ∀ component, component ∈ pattBiasErrorComponents ->
        Tendsto (fun index => pattBiasErrorComponentBound index component)
          l (nhds 0)) :
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
      prospective_pate_actualBootstrapVariance_tendsto_of_eventually_score_cell_components_and_finite_error_bounds
        (l := l) pateCells pateScoreErrorComponents
        pateBiasErrorComponents pateSample pateBaseWeight
        pateReuseResidualWeight pateHeterogeneity pateResidual pateScore
        pateTarget pateDenominator pateNormalizer pateCellBaseWeight
        pateCellReuseResidualWeight pateCellHeterogeneity pateCellResidual
        pateBaseWeightLimit pateReuseResidualWeightLimit
        pateHeterogeneityLimit pateResidualLimit pateMassLimit
        pateActualVariance pateScoreReplicationError pateBiasCorrectionError
        pateScoreErrorComponent pateScoreErrorComponentBound
        pateBiasErrorComponent pateBiasErrorComponentBound hpateErrorDecomp
        hpateCover hpateBase hpateReuse hpateHeterogeneity hpateResidual
        hpateBaseLimit hpateReuseLimit hpateHeterogeneityLimit
        hpateResidualLimit hpateMass hpateScoreDecomp
        hpateScoreComponentBound hpateScoreComponentBoundTendsto
        hpateBiasDecomp hpateBiasComponentBound hpateBiasComponentBoundTendsto
  · exact
      prospective_patt_actualBootstrapVariance_tendsto_of_eventually_score_cell_components_and_finite_error_bounds
        (l := l) pattCells pattScoreErrorComponents
        pattBiasErrorComponents pattSample pattDenominatorWeight
        pattTreatedContribution pattControlReuseContribution pattScore
        pattTarget pattDenominator pattNormalizer pattCellDenominatorWeight
        pattCellTreatedContribution pattCellControlReuseContribution
        pattDenominatorWeightLimit pattTreatedContributionLimit
        pattControlReuseContributionLimit pattMassLimit pattActualVariance
        pattScoreReplicationError pattBiasCorrectionError
        pattScoreErrorComponent pattScoreErrorComponentBound
        pattBiasErrorComponent pattBiasErrorComponentBound hpattErrorDecomp
        hpattCover hpattDenominator hpattTreated hpattControl
        hpattDenominatorLimit hpattTreatedLimit hpattControlLimit hpattMass
        hpattScoreDecomp hpattScoreComponentBound
        hpattScoreComponentBoundTendsto hpattBiasDecomp
        hpattBiasComponentBound hpattBiasComponentBoundTendsto

end WDSM
end Matching
end StatInference
