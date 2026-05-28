import Mathlib.Data.Finset.Basic
import Mathlib.Topology.Basic
import StatInference.Matching.WDSM.BootstrapActualVarianceErrorBoundBridge
import StatInference.Matching.WDSM.BootstrapScoreCellContributionBridge

/-!
# Bootstrap score-cell limit bridges

This module discharges a common deterministic premise in the WDSM bootstrap
route: cellwise `Tendsto` assumptions can be supplied by eventual equality to
fixed score-cell limits.  The resulting adapters are deliberately finite and
probability-free, so later stochastic arguments only need to prove eventual
constant cell representations or reduce them to shrinking deterministic
bounds.
-/

namespace StatInference
namespace Matching
namespace WDSM

open Filter

variable {Index Unit Cell ScoreErrorComponent BiasErrorComponent : Type*}
variable {l : Filter Index}

/--
Eventual equality to a constant gives convergence to that constant.
-/
theorem tendsto_real_of_eventually_eq_const
    (value : Index -> Real) (limit : Real)
    (hvalue : value =ᶠ[l] fun _index => limit) :
    Tendsto value l (nhds limit) :=
  tendsto_const_nhds.congr' hvalue.symm

/--
Cellwise eventual equality to fixed limits gives cellwise convergence.
-/
theorem cellwise_tendsto_real_of_eventually_eq_const
    (cells : Finset Cell) (value : Index -> Cell -> Real)
    (limit : Cell -> Real)
    (hvalue :
      ∀ cell, cell ∈ cells ->
        (fun index => value index cell) =ᶠ[l]
          fun _index => limit cell) :
    ∀ cell, cell ∈ cells ->
      Tendsto (fun index => value index cell) l
        (nhds (limit cell)) :=
  fun cell hcell =>
    tendsto_real_of_eventually_eq_const
      (l := l) (fun index => value index cell) (limit cell)
      (hvalue cell hcell)

/--
Weighted score-cell mass convergence follows from eventual equality to fixed
cell masses.
-/
theorem cellwiseScoreCellMassLLN_of_eventually_eq_const
    [DecidableEq Cell]
    (cells : Finset Cell)
    (sample : Index -> Finset Unit)
    (weight : Index -> Unit -> Real)
    (score : Index -> Unit -> Cell)
    (massLimit : Cell -> Real)
    (hmass :
      ∀ cell, cell ∈ cells ->
        (fun index =>
          scoreCellMass (sample index) (weight index)
            (score index) cell) =ᶠ[l]
          fun _index => massLimit cell) :
    cellwiseScoreCellMassLLN (l := l) cells sample weight score
      massLimit :=
  cellwise_tendsto_real_of_eventually_eq_const
    (l := l) cells
    (fun index cell =>
      scoreCellMass (sample index) (weight index) (score index) cell)
    massLimit hmass

/--
Weighted score-cell indicator-sum convergence follows from eventual equality
to fixed cell masses.
-/
theorem cellwiseWeightedIndicatorSumLLN_of_eventually_eq_const
    [DecidableEq Cell]
    (cells : Finset Cell)
    (sample : Index -> Finset Unit)
    (weight : Index -> Unit -> Real)
    (score : Index -> Unit -> Cell)
    (massLimit : Cell -> Real)
    (hmass :
      ∀ cell, cell ∈ cells ->
        (fun index =>
          weightedSampleSum (sample index) (weight index)
            (scoreCellIndicator (score index) cell)) =ᶠ[l]
          fun _index => massLimit cell) :
    cellwiseWeightedIndicatorSumLLN (l := l) cells sample weight score
      massLimit :=
  cellwise_tendsto_real_of_eventually_eq_const
    (l := l) cells
    (fun index cell =>
      weightedSampleSum (sample index) (weight index)
        (scoreCellIndicator (score index) cell))
    massLimit hmass

/--
PATE bootstrap score-cell contribution representations are eventually equal
to their fixed limiting contribution when each component is eventually equal
to its fixed limiting component.
-/
theorem eventually_pateBootstrapScoreCellContribution_eq_limit_of_eventually_component_eq
    (cells : Finset Cell)
    (cellBaseWeight cellReuseResidualWeight cellHeterogeneity cellResidual :
      Index -> Cell -> Real)
    (baseWeightLimit reuseResidualWeightLimit heterogeneityLimit
      residualLimit : Cell -> Real)
    (hbase :
      ∀ cell, cell ∈ cells ->
        (fun index => cellBaseWeight index cell) =ᶠ[l]
          fun _index => baseWeightLimit cell)
    (hreuse :
      ∀ cell, cell ∈ cells ->
        (fun index => cellReuseResidualWeight index cell) =ᶠ[l]
          fun _index => reuseResidualWeightLimit cell)
    (hheterogeneity :
      ∀ cell, cell ∈ cells ->
        (fun index => cellHeterogeneity index cell) =ᶠ[l]
          fun _index => heterogeneityLimit cell)
    (hresidual :
      ∀ cell, cell ∈ cells ->
        (fun index => cellResidual index cell) =ᶠ[l]
          fun _index => residualLimit cell) :
    ∀ cell, cell ∈ cells ->
      (fun index =>
        pateBootstrapScoreCellContribution
          (cellBaseWeight index) (cellReuseResidualWeight index)
          (cellHeterogeneity index) (cellResidual index) cell) =ᶠ[l]
        fun _index =>
          pateBootstrapScoreCellContribution baseWeightLimit
            reuseResidualWeightLimit heterogeneityLimit residualLimit cell :=
  fun cell hcell => by
    filter_upwards [hbase cell hcell, hreuse cell hcell,
      hheterogeneity cell hcell, hresidual cell hcell] with index
      hbaseIndex hreuseIndex hheterogeneityIndex hresidualIndex
    unfold pateBootstrapScoreCellContribution
    rw [hbaseIndex, hreuseIndex, hheterogeneityIndex, hresidualIndex]

/--
PATE bootstrap score-cell contribution limits from eventual equality of the
component score-cell arrays.
-/
theorem tendsto_pateBootstrapScoreCellContribution_of_eventually_component_eq
    (cells : Finset Cell)
    (cellBaseWeight cellReuseResidualWeight cellHeterogeneity cellResidual :
      Index -> Cell -> Real)
    (baseWeightLimit reuseResidualWeightLimit heterogeneityLimit
      residualLimit : Cell -> Real)
    (hbase :
      ∀ cell, cell ∈ cells ->
        (fun index => cellBaseWeight index cell) =ᶠ[l]
          fun _index => baseWeightLimit cell)
    (hreuse :
      ∀ cell, cell ∈ cells ->
        (fun index => cellReuseResidualWeight index cell) =ᶠ[l]
          fun _index => reuseResidualWeightLimit cell)
    (hheterogeneity :
      ∀ cell, cell ∈ cells ->
        (fun index => cellHeterogeneity index cell) =ᶠ[l]
          fun _index => heterogeneityLimit cell)
    (hresidual :
      ∀ cell, cell ∈ cells ->
        (fun index => cellResidual index cell) =ᶠ[l]
          fun _index => residualLimit cell) :
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
  cellwise_tendsto_real_of_eventually_eq_const
    (l := l) cells
    (fun index cell =>
      pateBootstrapScoreCellContribution
        (cellBaseWeight index) (cellReuseResidualWeight index)
        (cellHeterogeneity index) (cellResidual index) cell)
    (pateBootstrapScoreCellContribution baseWeightLimit
      reuseResidualWeightLimit heterogeneityLimit residualLimit)
    (eventually_pateBootstrapScoreCellContribution_eq_limit_of_eventually_component_eq
      (l := l) cells cellBaseWeight cellReuseResidualWeight
      cellHeterogeneity cellResidual baseWeightLimit
      reuseResidualWeightLimit heterogeneityLimit residualLimit hbase
      hreuse hheterogeneity hresidual)

/--
PATT bootstrap score-cell contribution representations are eventually equal
to their fixed limiting contribution when each one-sided component is
eventually equal to its fixed limiting component.
-/
theorem eventually_pattBootstrapScoreCellContribution_eq_limit_of_eventually_component_eq
    (cells : Finset Cell)
    (cellTreatedContribution cellControlReuseContribution :
      Index -> Cell -> Real)
    (treatedContributionLimit controlReuseContributionLimit : Cell -> Real)
    (htreated :
      ∀ cell, cell ∈ cells ->
        (fun index => cellTreatedContribution index cell) =ᶠ[l]
          fun _index => treatedContributionLimit cell)
    (hcontrol :
      ∀ cell, cell ∈ cells ->
        (fun index => cellControlReuseContribution index cell) =ᶠ[l]
          fun _index => controlReuseContributionLimit cell) :
    ∀ cell, cell ∈ cells ->
      (fun index =>
        pattBootstrapScoreCellContribution
          (cellTreatedContribution index)
          (cellControlReuseContribution index) cell) =ᶠ[l]
        fun _index =>
          pattBootstrapScoreCellContribution treatedContributionLimit
            controlReuseContributionLimit cell :=
  fun cell hcell => by
    filter_upwards [htreated cell hcell, hcontrol cell hcell] with index
      htreatedIndex hcontrolIndex
    unfold pattBootstrapScoreCellContribution
    rw [htreatedIndex, hcontrolIndex]

/--
PATT bootstrap score-cell contribution limits from eventual equality of the
one-sided component score-cell arrays.
-/
theorem tendsto_pattBootstrapScoreCellContribution_of_eventually_component_eq
    (cells : Finset Cell)
    (cellTreatedContribution cellControlReuseContribution :
      Index -> Cell -> Real)
    (treatedContributionLimit controlReuseContributionLimit : Cell -> Real)
    (htreated :
      ∀ cell, cell ∈ cells ->
        (fun index => cellTreatedContribution index cell) =ᶠ[l]
          fun _index => treatedContributionLimit cell)
    (hcontrol :
      ∀ cell, cell ∈ cells ->
        (fun index => cellControlReuseContribution index cell) =ᶠ[l]
          fun _index => controlReuseContributionLimit cell) :
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
  cellwise_tendsto_real_of_eventually_eq_const
    (l := l) cells
    (fun index cell =>
      pattBootstrapScoreCellContribution
        (cellTreatedContribution index)
        (cellControlReuseContribution index) cell)
    (pattBootstrapScoreCellContribution treatedContributionLimit
      controlReuseContributionLimit)
    (eventually_pattBootstrapScoreCellContribution_eq_limit_of_eventually_component_eq
      (l := l) cells cellTreatedContribution
      cellControlReuseContribution treatedContributionLimit
      controlReuseContributionLimit htreated hcontrol)

/--
Actual bootstrap variance convergence from eventual score-cell contribution
and denominator-weight equalities, plus finite-component score/bias error
bounds.
-/
theorem tendsto_actualBootstrapVariance_of_eventually_cell_contribution_weight_eq_and_finite_error_bounds
    [DecidableEq Cell] [DecidableEq ScoreErrorComponent]
    [DecidableEq BiasErrorComponent]
    (cells : Finset Cell)
    (scoreErrorComponents : Finset ScoreErrorComponent)
    (biasErrorComponents : Finset BiasErrorComponent)
    (sample : Index -> Finset Unit)
    (score : Index -> Unit -> Cell)
    (contribution weight : Index -> Unit -> Real)
    (target denominator normalizer : Real)
    (cellContribution cellWeight : Index -> Cell -> Real)
    (contributionLimit weightLimit massLimit : Cell -> Real)
    (actualVariance scoreReplicationError biasCorrectionError : Index -> Real)
    (scoreErrorComponent scoreErrorComponentBound :
      Index -> ScoreErrorComponent -> Real)
    (biasErrorComponent biasErrorComponentBound :
      Index -> BiasErrorComponent -> Real)
    (herror_decomp :
      (fun index =>
        actualVariance index -
          bootstrapCenteredVarianceTarget (sample index)
            (contribution index) (weight index) target denominator
            normalizer) =ᶠ[l]
        (fun index =>
          scoreReplicationError index + biasCorrectionError index))
    (hcover :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ sample index -> score index unit ∈ cells)
    (hcontributionCell :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ sample index ->
          cellContribution index (score index unit) =
            contribution index unit)
    (hweightCell :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ sample index ->
          cellWeight index (score index unit) = weight index unit)
    (hcontributionLimit :
      ∀ cell, cell ∈ cells ->
        (fun index => cellContribution index cell) =ᶠ[l]
          fun _index => contributionLimit cell)
    (hweightLimit :
      ∀ cell, cell ∈ cells ->
        (fun index => cellWeight index cell) =ᶠ[l]
          fun _index => weightLimit cell)
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
              (contributionLimit cell - target * weightLimit cell) ^ 2)
            massLimit)) :=
  tendsto_actualBootstrapVariance_of_eventually_cell_contribution_weight_limits_and_finite_error_bounds
    (l := l) cells scoreErrorComponents biasErrorComponents sample score
    contribution weight target denominator normalizer cellContribution
    cellWeight contributionLimit weightLimit massLimit actualVariance
    scoreReplicationError biasCorrectionError scoreErrorComponent
    scoreErrorComponentBound biasErrorComponent biasErrorComponentBound
    herror_decomp hcover hcontributionCell hweightCell
    (cellwise_tendsto_real_of_eventually_eq_const
      (l := l) cells cellContribution contributionLimit hcontributionLimit)
    (cellwise_tendsto_real_of_eventually_eq_const
      (l := l) cells cellWeight weightLimit hweightLimit)
    hmass hscore_decomp hscore_component_bound
    hscore_component_bound_tendsto hbias_decomp hbias_component_bound
    hbias_component_bound_tendsto

end WDSM
end Matching
end StatInference
