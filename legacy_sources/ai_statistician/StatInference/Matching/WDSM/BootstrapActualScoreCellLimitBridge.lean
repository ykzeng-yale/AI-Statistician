import Mathlib.Data.Finset.Basic
import Mathlib.Topology.Basic
import StatInference.Matching.WDSM.BootstrapActualScoreCellErrorBoundBridge
import StatInference.Matching.WDSM.BootstrapScoreCellLimitBridge

/-!
# Actual bootstrap score-cell limit adapters

This module specializes `BootstrapScoreCellLimitBridge` to the four WDSM
bootstrap scenarios.  It removes a repetitive manual step: when each score-cell
component is eventually equal to a fixed limiting cell value, the scenario
actual-variance theorems can consume those eventual equalities directly instead
of asking for separate cellwise `Tendsto` proofs.
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
Retrospective PATE actual bootstrap variance convergence from eventually valid
score-cell component representations, eventual equality to fixed component
limits, and finite-component score/bias error bounds.
-/
theorem retrospective_pate_actualBootstrapVariance_tendsto_of_eventually_component_eq_and_finite_error_bounds
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
        (fun index => cellBaseWeight index cell) =ᶠ[l]
          fun _index => baseWeightLimit cell)
    (hreuseLimit :
      ∀ cell, cell ∈ cells ->
        (fun index => cellReuseResidualWeight index cell) =ᶠ[l]
          fun _index => reuseResidualWeightLimit cell)
    (hheterogeneityLimit :
      ∀ cell, cell ∈ cells ->
        (fun index => cellHeterogeneity index cell) =ᶠ[l]
          fun _index => heterogeneityLimit cell)
    (hresidualLimit :
      ∀ cell, cell ∈ cells ->
        (fun index => cellResidual index cell) =ᶠ[l]
          fun _index => residualLimit cell)
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
  retrospective_pate_actualBootstrapVariance_tendsto_of_eventually_score_cell_components_and_finite_error_bounds
    (l := l) cells scoreErrorComponents biasErrorComponents sample
    baseWeight reuseResidualWeight heterogeneity residual score target
    denominator normalizer cellBaseWeight cellReuseResidualWeight
    cellHeterogeneity cellResidual baseWeightLimit
    reuseResidualWeightLimit heterogeneityLimit residualLimit massLimit
    actualVariance scoreReplicationError biasCorrectionError
    scoreErrorComponent scoreErrorComponentBound biasErrorComponent
    biasErrorComponentBound herror_decomp hcover hbase hreuse
    hheterogeneity hresidual
    (cellwise_tendsto_real_of_eventually_eq_const
      (l := l) cells cellBaseWeight baseWeightLimit hbaseLimit)
    (cellwise_tendsto_real_of_eventually_eq_const
      (l := l) cells cellReuseResidualWeight reuseResidualWeightLimit
      hreuseLimit)
    (cellwise_tendsto_real_of_eventually_eq_const
      (l := l) cells cellHeterogeneity heterogeneityLimit
      hheterogeneityLimit)
    (cellwise_tendsto_real_of_eventually_eq_const
      (l := l) cells cellResidual residualLimit hresidualLimit)
    hmass hscore_decomp hscore_component_bound
    hscore_component_bound_tendsto hbias_decomp hbias_component_bound
    hbias_component_bound_tendsto

/--
Prospective PATE actual bootstrap variance convergence from eventually valid
score-cell component representations, eventual equality to fixed component
limits, and finite-component score/bias error bounds.
-/
theorem prospective_pate_actualBootstrapVariance_tendsto_of_eventually_component_eq_and_finite_error_bounds
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
        (fun index => cellBaseWeight index cell) =ᶠ[l]
          fun _index => baseWeightLimit cell)
    (hreuseLimit :
      ∀ cell, cell ∈ cells ->
        (fun index => cellReuseResidualWeight index cell) =ᶠ[l]
          fun _index => reuseResidualWeightLimit cell)
    (hheterogeneityLimit :
      ∀ cell, cell ∈ cells ->
        (fun index => cellHeterogeneity index cell) =ᶠ[l]
          fun _index => heterogeneityLimit cell)
    (hresidualLimit :
      ∀ cell, cell ∈ cells ->
        (fun index => cellResidual index cell) =ᶠ[l]
          fun _index => residualLimit cell)
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
  prospective_pate_actualBootstrapVariance_tendsto_of_eventually_score_cell_components_and_finite_error_bounds
    (l := l) cells scoreErrorComponents biasErrorComponents sample
    baseWeight reuseResidualWeight heterogeneity residual score target
    denominator normalizer cellBaseWeight cellReuseResidualWeight
    cellHeterogeneity cellResidual baseWeightLimit
    reuseResidualWeightLimit heterogeneityLimit residualLimit massLimit
    actualVariance scoreReplicationError biasCorrectionError
    scoreErrorComponent scoreErrorComponentBound biasErrorComponent
    biasErrorComponentBound herror_decomp hcover hbase hreuse
    hheterogeneity hresidual
    (cellwise_tendsto_real_of_eventually_eq_const
      (l := l) cells cellBaseWeight baseWeightLimit hbaseLimit)
    (cellwise_tendsto_real_of_eventually_eq_const
      (l := l) cells cellReuseResidualWeight reuseResidualWeightLimit
      hreuseLimit)
    (cellwise_tendsto_real_of_eventually_eq_const
      (l := l) cells cellHeterogeneity heterogeneityLimit
      hheterogeneityLimit)
    (cellwise_tendsto_real_of_eventually_eq_const
      (l := l) cells cellResidual residualLimit hresidualLimit)
    hmass hscore_decomp hscore_component_bound
    hscore_component_bound_tendsto hbias_decomp hbias_component_bound
    hbias_component_bound_tendsto

/--
Retrospective PATT actual bootstrap variance convergence from eventually valid
score-cell component representations, eventual equality to fixed component
limits, and finite-component score/bias error bounds.
-/
theorem retrospective_patt_actualBootstrapVariance_tendsto_of_eventually_component_eq_and_finite_error_bounds
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
        (fun index => cellDenominatorWeight index cell) =ᶠ[l]
          fun _index => denominatorWeightLimit cell)
    (htreatedLimit :
      ∀ cell, cell ∈ cells ->
        (fun index => cellTreatedContribution index cell) =ᶠ[l]
          fun _index => treatedContributionLimit cell)
    (hcontrolLimit :
      ∀ cell, cell ∈ cells ->
        (fun index => cellControlReuseContribution index cell) =ᶠ[l]
          fun _index => controlReuseContributionLimit cell)
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
  retrospective_patt_actualBootstrapVariance_tendsto_of_eventually_score_cell_components_and_finite_error_bounds
    (l := l) cells scoreErrorComponents biasErrorComponents sample
    denominatorWeight treatedContribution controlReuseContribution score
    target denominator normalizer cellDenominatorWeight
    cellTreatedContribution cellControlReuseContribution
    denominatorWeightLimit treatedContributionLimit
    controlReuseContributionLimit massLimit actualVariance
    scoreReplicationError biasCorrectionError scoreErrorComponent
    scoreErrorComponentBound biasErrorComponent biasErrorComponentBound
    herror_decomp hcover hdenominator htreated hcontrol
    (cellwise_tendsto_real_of_eventually_eq_const
      (l := l) cells cellDenominatorWeight denominatorWeightLimit
      hdenominatorLimit)
    (cellwise_tendsto_real_of_eventually_eq_const
      (l := l) cells cellTreatedContribution treatedContributionLimit
      htreatedLimit)
    (cellwise_tendsto_real_of_eventually_eq_const
      (l := l) cells cellControlReuseContribution
      controlReuseContributionLimit hcontrolLimit)
    hmass hscore_decomp hscore_component_bound
    hscore_component_bound_tendsto hbias_decomp hbias_component_bound
    hbias_component_bound_tendsto

/--
Prospective PATT actual bootstrap variance convergence from eventually valid
score-cell component representations, eventual equality to fixed component
limits, and finite-component score/bias error bounds.
-/
theorem prospective_patt_actualBootstrapVariance_tendsto_of_eventually_component_eq_and_finite_error_bounds
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
        (fun index => cellDenominatorWeight index cell) =ᶠ[l]
          fun _index => denominatorWeightLimit cell)
    (htreatedLimit :
      ∀ cell, cell ∈ cells ->
        (fun index => cellTreatedContribution index cell) =ᶠ[l]
          fun _index => treatedContributionLimit cell)
    (hcontrolLimit :
      ∀ cell, cell ∈ cells ->
        (fun index => cellControlReuseContribution index cell) =ᶠ[l]
          fun _index => controlReuseContributionLimit cell)
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
  prospective_patt_actualBootstrapVariance_tendsto_of_eventually_score_cell_components_and_finite_error_bounds
    (l := l) cells scoreErrorComponents biasErrorComponents sample
    denominatorWeight treatedContribution controlReuseContribution score
    target denominator normalizer cellDenominatorWeight
    cellTreatedContribution cellControlReuseContribution
    denominatorWeightLimit treatedContributionLimit
    controlReuseContributionLimit massLimit actualVariance
    scoreReplicationError biasCorrectionError scoreErrorComponent
    scoreErrorComponentBound biasErrorComponent biasErrorComponentBound
    herror_decomp hcover hdenominator htreated hcontrol
    (cellwise_tendsto_real_of_eventually_eq_const
      (l := l) cells cellDenominatorWeight denominatorWeightLimit
      hdenominatorLimit)
    (cellwise_tendsto_real_of_eventually_eq_const
      (l := l) cells cellTreatedContribution treatedContributionLimit
      htreatedLimit)
    (cellwise_tendsto_real_of_eventually_eq_const
      (l := l) cells cellControlReuseContribution
      controlReuseContributionLimit hcontrolLimit)
    hmass hscore_decomp hscore_component_bound
    hscore_component_bound_tendsto hbias_decomp hbias_component_bound
    hbias_component_bound_tendsto

end WDSM
end Matching
end StatInference
