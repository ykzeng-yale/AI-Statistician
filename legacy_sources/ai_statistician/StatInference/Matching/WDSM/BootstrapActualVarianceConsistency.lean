import StatInference.Matching.WDSM.BootstrapVarianceStability
import StatInference.Matching.WDSM.BootstrapFiniteCellVarianceBridge
import StatInference.Matching.WDSM.FiniteCellIndicatorGCAdapter

/-!
# Actual bootstrap variance consistency from finite cells and error stability

This module composes two checked layers:

* finite-cell convergence of the linearized bootstrap centered-square target;
* negligible score-replication and bias-correction errors.

The resulting theorems prove convergence of the actual scalar bootstrap
variance estimator to the same finite-cell limit.  They still require the
stochastic proofs that the concrete score-replication and bias-correction
errors are negligible.
-/

namespace StatInference
namespace Matching
namespace WDSM

open Filter

variable {Index Unit Cell : Type*} {l : Filter Index}

/--
Actual bootstrap variance consistency from a fixed finite-cell loading and
negligible score/bias errors.
-/
theorem tendsto_actualBootstrapVariance_of_finiteCell_and_error_stability
    [DecidableEq Cell]
    (cells : Finset Cell)
    (sample : Index -> Finset Unit)
    (score : Index -> Unit -> Cell)
    (contribution weight : Index -> Unit -> Real)
    (target denominator normalizer : Real)
    (loading massLimit : Cell -> Real)
    (actualVariance scoreReplicationError biasCorrectionError : Index -> Real)
    (herror_decomp :
      (fun index =>
        actualVariance index -
          bootstrapCenteredVarianceTarget (sample index)
            (contribution index) (weight index) target denominator
            normalizer) =ᶠ[l]
        (fun index =>
          scoreReplicationError index + biasCorrectionError index))
    (hcover :
      ∀ index unit, unit ∈ sample index -> score index unit ∈ cells)
    (hloading :
      ∀ index unit, unit ∈ sample index ->
        loading (score index unit) =
          (contribution index unit - target * weight index unit) ^ 2)
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
          weightedScoreCellMomentLimit cells loading massLimit)) := by
  have hlinearized :
      Tendsto
        (fun index =>
          bootstrapCenteredVarianceTarget (sample index)
            (contribution index) (weight index) target denominator normalizer)
        l
        (nhds
          ((1 / denominator ^ 2) * (1 / normalizer) *
            weightedScoreCellMomentLimit cells loading massLimit)) :=
    tendsto_bootstrapCenteredVarianceTarget_of_cellwiseScoreCellMassLLN
      (l := l) cells sample score contribution weight target denominator
      normalizer loading massLimit hcover hloading hmass
  exact
    tendsto_bootstrapVariance_of_eventual_error_decomposition
      (l := l)
      (fun index =>
        bootstrapCenteredVarianceTarget (sample index)
          (contribution index) (weight index) target denominator normalizer)
      actualVariance scoreReplicationError biasCorrectionError
      ((1 / denominator ^ 2) * (1 / normalizer) *
        weightedScoreCellMomentLimit cells loading massLimit)
      herror_decomp hlinearized hscore hbias

/--
Actual bootstrap variance consistency from score-cell contribution/weight
limits and negligible score/bias errors.
-/
theorem tendsto_actualBootstrapVariance_of_cell_contribution_weight_limits_and_error_stability
    [DecidableEq Cell]
    (cells : Finset Cell)
    (sample : Index -> Finset Unit)
    (score : Index -> Unit -> Cell)
    (contribution weight : Index -> Unit -> Real)
    (target denominator normalizer : Real)
    (cellContribution cellWeight : Index -> Cell -> Real)
    (contributionLimit weightLimit massLimit : Cell -> Real)
    (actualVariance scoreReplicationError biasCorrectionError : Index -> Real)
    (herror_decomp :
      (fun index =>
        actualVariance index -
          bootstrapCenteredVarianceTarget (sample index)
            (contribution index) (weight index) target denominator
            normalizer) =ᶠ[l]
        (fun index =>
          scoreReplicationError index + biasCorrectionError index))
    (hcover :
      ∀ index unit, unit ∈ sample index -> score index unit ∈ cells)
    (hcontributionCell :
      ∀ index unit, unit ∈ sample index ->
        cellContribution index (score index unit) = contribution index unit)
    (hweightCell :
      ∀ index unit, unit ∈ sample index ->
        cellWeight index (score index unit) = weight index unit)
    (hcontributionLimit :
      ∀ cell, cell ∈ cells ->
        Tendsto (fun index => cellContribution index cell)
          l (nhds (contributionLimit cell)))
    (hweightLimit :
      ∀ cell, cell ∈ cells ->
        Tendsto (fun index => cellWeight index cell)
          l (nhds (weightLimit cell)))
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
              (contributionLimit cell - target * weightLimit cell) ^ 2)
            massLimit)) := by
  have hlinearized :
      Tendsto
        (fun index =>
          bootstrapCenteredVarianceTarget (sample index)
            (contribution index) (weight index) target denominator normalizer)
        l
        (nhds
          ((1 / denominator ^ 2) * (1 / normalizer) *
            weightedScoreCellMomentLimit cells
              (fun cell =>
                (contributionLimit cell - target * weightLimit cell) ^ 2)
              massLimit)) :=
    tendsto_bootstrapCenteredVarianceTarget_of_cellwiseScoreCellMassLLN_of_cell_contribution_weight_limits
      (l := l) cells sample score contribution weight target denominator
      normalizer cellContribution cellWeight contributionLimit weightLimit
      massLimit hcover hcontributionCell hweightCell hcontributionLimit
      hweightLimit hmass
  exact
    tendsto_bootstrapVariance_of_eventual_error_decomposition
      (l := l)
      (fun index =>
        bootstrapCenteredVarianceTarget (sample index)
          (contribution index) (weight index) target denominator normalizer)
      actualVariance scoreReplicationError biasCorrectionError
      ((1 / denominator ^ 2) * (1 / normalizer) *
        weightedScoreCellMomentLimit cells
          (fun cell =>
            (contributionLimit cell - target * weightLimit cell) ^ 2)
          massLimit)
      herror_decomp hlinearized hscore hbias

/--
Eventual version for estimated-score/bootstrap settings where cell coverage and
score-cell representations hold only eventually.
-/
theorem tendsto_actualBootstrapVariance_of_eventually_cell_contribution_weight_limits_and_error_stability
    [DecidableEq Cell]
    (cells : Finset Cell)
    (sample : Index -> Finset Unit)
    (score : Index -> Unit -> Cell)
    (contribution weight : Index -> Unit -> Real)
    (target denominator normalizer : Real)
    (cellContribution cellWeight : Index -> Cell -> Real)
    (contributionLimit weightLimit massLimit : Cell -> Real)
    (actualVariance scoreReplicationError biasCorrectionError : Index -> Real)
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
        Tendsto (fun index => cellContribution index cell)
          l (nhds (contributionLimit cell)))
    (hweightLimit :
      ∀ cell, cell ∈ cells ->
        Tendsto (fun index => cellWeight index cell)
          l (nhds (weightLimit cell)))
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
              (contributionLimit cell - target * weightLimit cell) ^ 2)
            massLimit)) := by
  have hlinearized :
      Tendsto
        (fun index =>
          bootstrapCenteredVarianceTarget (sample index)
            (contribution index) (weight index) target denominator normalizer)
        l
        (nhds
          ((1 / denominator ^ 2) * (1 / normalizer) *
            weightedScoreCellMomentLimit cells
              (fun cell =>
                (contributionLimit cell - target * weightLimit cell) ^ 2)
              massLimit)) :=
    tendsto_bootstrapCenteredVarianceTarget_of_eventually_cell_contribution_weight_limits
      (l := l) cells sample score contribution weight target denominator
      normalizer cellContribution cellWeight contributionLimit weightLimit
      massLimit hcover hcontributionCell hweightCell hcontributionLimit
      hweightLimit hmass
  exact
    tendsto_bootstrapVariance_of_eventual_error_decomposition
      (l := l)
      (fun index =>
        bootstrapCenteredVarianceTarget (sample index)
          (contribution index) (weight index) target denominator normalizer)
      actualVariance scoreReplicationError biasCorrectionError
      ((1 / denominator ^ 2) * (1 / normalizer) *
        weightedScoreCellMomentLimit cells
          (fun cell =>
            (contributionLimit cell - target * weightLimit cell) ^ 2)
          massLimit)
      herror_decomp hlinearized hscore hbias

/--
GC-backed atTop version of actual bootstrap variance consistency from a fixed
finite-cell loading and negligible score/bias errors.
-/
theorem tendsto_actualBootstrapVariance_of_finiteCell_glivenkoCantelli_and_error_stability
    [DecidableEq Cell]
    (cells : Finset Cell)
    (sample : ℕ -> Finset Unit)
    (score : ℕ -> Unit -> Cell)
    (contribution weight : ℕ -> Unit -> Real)
    (target denominator normalizer : Real)
    (loading massLimit : Cell -> Real)
    (actualVariance scoreReplicationError biasCorrectionError : ℕ -> Real)
    (herror_decomp :
      (fun index =>
        actualVariance index -
          bootstrapCenteredVarianceTarget (sample index)
            (contribution index) (weight index) target denominator
            normalizer) =ᶠ[atTop]
        (fun index =>
          scoreReplicationError index + biasCorrectionError index))
    (hcover :
      ∀ index unit, unit ∈ sample index -> score index unit ∈ cells)
    (hloading :
      ∀ index unit, unit ∈ sample index ->
        loading (score index unit) =
          (contribution index unit - target * weight index unit) ^ 2)
    (hgc :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        cells massLimit sample (fun _index _unit => 1)
        score).weighted_indicator_array_lln)
    (hscore :
      bootstrapScoreReplicationErrorNegligible
        (l := atTop) scoreReplicationError)
    (hbias :
      bootstrapBiasCorrectionErrorNegligible
        (l := atTop) biasCorrectionError) :
    Tendsto actualVariance atTop
      (nhds
        ((1 / denominator ^ 2) * (1 / normalizer) *
          weightedScoreCellMomentLimit cells loading massLimit)) :=
  tendsto_actualBootstrapVariance_of_finiteCell_and_error_stability
    (l := atTop) cells sample score contribution weight target denominator
    normalizer loading massLimit actualVariance scoreReplicationError
    biasCorrectionError herror_decomp hcover hloading
    (cellwise_mass_lln_of_glivenkoCantelli_bridge
      cells massLimit sample (fun _index _unit => 1) score hgc)
    hscore hbias

/--
GC-backed atTop version of actual bootstrap variance consistency from
score-cell contribution and weight limits.
-/
theorem
    tendsto_actualBootstrapVariance_of_cell_contribution_weight_limits_glivenkoCantelli_and_error_stability
    [DecidableEq Cell]
    (cells : Finset Cell)
    (sample : ℕ -> Finset Unit)
    (score : ℕ -> Unit -> Cell)
    (contribution weight : ℕ -> Unit -> Real)
    (target denominator normalizer : Real)
    (cellContribution cellWeight : ℕ -> Cell -> Real)
    (contributionLimit weightLimit massLimit : Cell -> Real)
    (actualVariance scoreReplicationError biasCorrectionError : ℕ -> Real)
    (herror_decomp :
      (fun index =>
        actualVariance index -
          bootstrapCenteredVarianceTarget (sample index)
            (contribution index) (weight index) target denominator
            normalizer) =ᶠ[atTop]
        (fun index =>
          scoreReplicationError index + biasCorrectionError index))
    (hcover :
      ∀ index unit, unit ∈ sample index -> score index unit ∈ cells)
    (hcontributionCell :
      ∀ index unit, unit ∈ sample index ->
        cellContribution index (score index unit) = contribution index unit)
    (hweightCell :
      ∀ index unit, unit ∈ sample index ->
        cellWeight index (score index unit) = weight index unit)
    (hcontributionLimit :
      ∀ cell, cell ∈ cells ->
        Tendsto (fun index => cellContribution index cell)
          atTop (nhds (contributionLimit cell)))
    (hweightLimit :
      ∀ cell, cell ∈ cells ->
        Tendsto (fun index => cellWeight index cell)
          atTop (nhds (weightLimit cell)))
    (hgc :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        cells massLimit sample (fun _index _unit => 1)
        score).weighted_indicator_array_lln)
    (hscore :
      bootstrapScoreReplicationErrorNegligible
        (l := atTop) scoreReplicationError)
    (hbias :
      bootstrapBiasCorrectionErrorNegligible
        (l := atTop) biasCorrectionError) :
    Tendsto actualVariance atTop
      (nhds
        ((1 / denominator ^ 2) * (1 / normalizer) *
          weightedScoreCellMomentLimit cells
            (fun cell =>
              (contributionLimit cell - target * weightLimit cell) ^ 2)
            massLimit)) :=
  tendsto_actualBootstrapVariance_of_cell_contribution_weight_limits_and_error_stability
    (l := atTop) cells sample score contribution weight target denominator
    normalizer cellContribution cellWeight contributionLimit weightLimit
    massLimit actualVariance scoreReplicationError biasCorrectionError
    herror_decomp hcover hcontributionCell hweightCell hcontributionLimit
    hweightLimit
    (cellwise_mass_lln_of_glivenkoCantelli_bridge
      cells massLimit sample (fun _index _unit => 1) score hgc)
    hscore hbias

/--
GC-backed atTop version for estimated-score/bootstrap settings where cell
coverage and score-cell representations hold only eventually.
-/
theorem
    tendsto_actualBootstrapVariance_of_eventually_cell_contribution_weight_limits_glivenkoCantelli_and_error_stability
    [DecidableEq Cell]
    (cells : Finset Cell)
    (sample : ℕ -> Finset Unit)
    (score : ℕ -> Unit -> Cell)
    (contribution weight : ℕ -> Unit -> Real)
    (target denominator normalizer : Real)
    (cellContribution cellWeight : ℕ -> Cell -> Real)
    (contributionLimit weightLimit massLimit : Cell -> Real)
    (actualVariance scoreReplicationError biasCorrectionError : ℕ -> Real)
    (herror_decomp :
      (fun index =>
        actualVariance index -
          bootstrapCenteredVarianceTarget (sample index)
            (contribution index) (weight index) target denominator
            normalizer) =ᶠ[atTop]
        (fun index =>
          scoreReplicationError index + biasCorrectionError index))
    (hcover :
      ∀ᶠ index in atTop,
        ∀ unit, unit ∈ sample index -> score index unit ∈ cells)
    (hcontributionCell :
      ∀ᶠ index in atTop,
        ∀ unit, unit ∈ sample index ->
          cellContribution index (score index unit) =
            contribution index unit)
    (hweightCell :
      ∀ᶠ index in atTop,
        ∀ unit, unit ∈ sample index ->
          cellWeight index (score index unit) = weight index unit)
    (hcontributionLimit :
      ∀ cell, cell ∈ cells ->
        Tendsto (fun index => cellContribution index cell)
          atTop (nhds (contributionLimit cell)))
    (hweightLimit :
      ∀ cell, cell ∈ cells ->
        Tendsto (fun index => cellWeight index cell)
          atTop (nhds (weightLimit cell)))
    (hgc :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        cells massLimit sample (fun _index _unit => 1)
        score).weighted_indicator_array_lln)
    (hscore :
      bootstrapScoreReplicationErrorNegligible
        (l := atTop) scoreReplicationError)
    (hbias :
      bootstrapBiasCorrectionErrorNegligible
        (l := atTop) biasCorrectionError) :
    Tendsto actualVariance atTop
      (nhds
        ((1 / denominator ^ 2) * (1 / normalizer) *
          weightedScoreCellMomentLimit cells
            (fun cell =>
              (contributionLimit cell - target * weightLimit cell) ^ 2)
            massLimit)) :=
  tendsto_actualBootstrapVariance_of_eventually_cell_contribution_weight_limits_and_error_stability
    (l := atTop) cells sample score contribution weight target denominator
    normalizer cellContribution cellWeight contributionLimit weightLimit
    massLimit actualVariance scoreReplicationError biasCorrectionError
    herror_decomp hcover hcontributionCell hweightCell hcontributionLimit
    hweightLimit
    (cellwise_mass_lln_of_glivenkoCantelli_bridge
      cells massLimit sample (fun _index _unit => 1) score hgc)
    hscore hbias

/--
Finite `L1(P)` bracketing supplies the score-cell mass LLN needed for actual
bootstrap variance consistency from a fixed finite-cell loading.
-/
theorem
    tendsto_actualBootstrapVariance_of_finiteCell_l1BracketingNumber_obligations_and_error_stability
    [DecidableEq Cell]
    {Bracket : Type*} [Fintype Bracket]
    (cells : Finset Cell)
    (sample : ℕ -> Finset Unit)
    (score : ℕ -> Unit -> Cell)
    (contribution weight : ℕ -> Unit -> Real)
    (target denominator normalizer : Real)
    (loading massLimit : Cell -> Real)
    (actualVariance scoreReplicationError biasCorrectionError : ℕ -> Real)
    (herror_decomp :
      (fun index =>
        actualVariance index -
          bootstrapCenteredVarianceTarget (sample index)
            (contribution index) (weight index) target denominator
            normalizer) =ᶠ[atTop]
        (fun index =>
          scoreReplicationError index + biasCorrectionError index))
    (hcover :
      ∀ index unit, unit ∈ sample index -> score index unit ∈ cells)
    (hloading :
      ∀ index unit, unit ∈ sample index ->
        loading (score index unit) =
          (contribution index unit - target * weight index unit) ^ 2)
    (obligations :
      L1BracketingNumberConstructorObligations (Bracket := Bracket)
        {cell : Cell | cell ∈ cells} massLimit
        (fun sampleSize cell =>
          weightedSampleSum (sample sampleSize)
            ((fun _index _unit => 1) sampleSize)
            (scoreCellIndicator (score sampleSize) cell)))
    (hscore :
      bootstrapScoreReplicationErrorNegligible
        (l := atTop) scoreReplicationError)
    (hbias :
      bootstrapBiasCorrectionErrorNegligible
        (l := atTop) biasCorrectionError) :
    Tendsto actualVariance atTop
      (nhds
        ((1 / denominator ^ 2) * (1 / normalizer) *
          weightedScoreCellMomentLimit cells loading massLimit)) :=
  tendsto_actualBootstrapVariance_of_finiteCell_glivenkoCantelli_and_error_stability
    cells sample score contribution weight target denominator normalizer
    loading massLimit actualVariance scoreReplicationError biasCorrectionError
    herror_decomp hcover hloading
    (weighted_indicator_array_lln_of_l1BracketingNumber_obligations
      cells massLimit sample (fun _index _unit => 1) score obligations)
    hscore hbias

/--
VdV&W endpoint assemblies supply the score-cell mass LLN needed for actual
bootstrap variance consistency from a fixed finite-cell loading.
-/
theorem
    tendsto_actualBootstrapVariance_of_finiteCell_vdvw241_endpoint_assembly_and_error_stability
    [DecidableEq Cell]
    {Bracket : Type*} [Fintype Bracket]
    (cells : Finset Cell)
    (sample : ℕ -> Finset Unit)
    (score : ℕ -> Unit -> Cell)
    (contribution weight : ℕ -> Unit -> Real)
    (target denominator normalizer : Real)
    (loading massLimit : Cell -> Real)
    (actualVariance scoreReplicationError biasCorrectionError : ℕ -> Real)
    (herror_decomp :
      (fun index =>
        actualVariance index -
          bootstrapCenteredVarianceTarget (sample index)
            (contribution index) (weight index) target denominator
            normalizer) =ᶠ[atTop]
        (fun index =>
          scoreReplicationError index + biasCorrectionError index))
    (hcover :
      ∀ index unit, unit ∈ sample index -> score index unit ∈ cells)
    (hloading :
      ∀ index unit, unit ∈ sample index ->
        loading (score index unit) =
          (contribution index unit - target * weight index unit) ^ 2)
    (assembly :
      FiniteBracketEndpointStrongLawAssembly (Bracket := Bracket)
        {cell : Cell | cell ∈ cells} massLimit
        (fun sampleSize cell =>
          weightedSampleSum (sample sampleSize)
            ((fun _index _unit => 1) sampleSize)
            (scoreCellIndicator (score sampleSize) cell)))
    (hscore :
      bootstrapScoreReplicationErrorNegligible
        (l := atTop) scoreReplicationError)
    (hbias :
      bootstrapBiasCorrectionErrorNegligible
        (l := atTop) biasCorrectionError) :
    Tendsto actualVariance atTop
      (nhds
        ((1 / denominator ^ 2) * (1 / normalizer) *
          weightedScoreCellMomentLimit cells loading massLimit)) :=
  tendsto_actualBootstrapVariance_of_finiteCell_glivenkoCantelli_and_error_stability
    cells sample score contribution weight target denominator normalizer
    loading massLimit actualVariance scoreReplicationError biasCorrectionError
    herror_decomp hcover hloading
    (weighted_indicator_array_lln_of_vdvw241_endpoint_assembly
      cells massLimit sample (fun _index _unit => 1) score assembly)
    hscore hbias

/--
Finite `L1(P)` bracketing supplies the score-cell mass LLN needed for actual
bootstrap variance consistency from score-cell contribution and weight limits.
-/
theorem
    tendsto_actualBootstrapVariance_of_cell_contribution_weight_limits_l1BracketingNumber_obligations_and_error_stability
    [DecidableEq Cell]
    {Bracket : Type*} [Fintype Bracket]
    (cells : Finset Cell)
    (sample : ℕ -> Finset Unit)
    (score : ℕ -> Unit -> Cell)
    (contribution weight : ℕ -> Unit -> Real)
    (target denominator normalizer : Real)
    (cellContribution cellWeight : ℕ -> Cell -> Real)
    (contributionLimit weightLimit massLimit : Cell -> Real)
    (actualVariance scoreReplicationError biasCorrectionError : ℕ -> Real)
    (herror_decomp :
      (fun index =>
        actualVariance index -
          bootstrapCenteredVarianceTarget (sample index)
            (contribution index) (weight index) target denominator
            normalizer) =ᶠ[atTop]
        (fun index =>
          scoreReplicationError index + biasCorrectionError index))
    (hcover :
      ∀ index unit, unit ∈ sample index -> score index unit ∈ cells)
    (hcontributionCell :
      ∀ index unit, unit ∈ sample index ->
        cellContribution index (score index unit) = contribution index unit)
    (hweightCell :
      ∀ index unit, unit ∈ sample index ->
        cellWeight index (score index unit) = weight index unit)
    (hcontributionLimit :
      ∀ cell, cell ∈ cells ->
        Tendsto (fun index => cellContribution index cell)
          atTop (nhds (contributionLimit cell)))
    (hweightLimit :
      ∀ cell, cell ∈ cells ->
        Tendsto (fun index => cellWeight index cell)
          atTop (nhds (weightLimit cell)))
    (obligations :
      L1BracketingNumberConstructorObligations (Bracket := Bracket)
        {cell : Cell | cell ∈ cells} massLimit
        (fun sampleSize cell =>
          weightedSampleSum (sample sampleSize)
            ((fun _index _unit => 1) sampleSize)
            (scoreCellIndicator (score sampleSize) cell)))
    (hscore :
      bootstrapScoreReplicationErrorNegligible
        (l := atTop) scoreReplicationError)
    (hbias :
      bootstrapBiasCorrectionErrorNegligible
        (l := atTop) biasCorrectionError) :
    Tendsto actualVariance atTop
      (nhds
        ((1 / denominator ^ 2) * (1 / normalizer) *
          weightedScoreCellMomentLimit cells
            (fun cell =>
              (contributionLimit cell - target * weightLimit cell) ^ 2)
            massLimit)) :=
  tendsto_actualBootstrapVariance_of_cell_contribution_weight_limits_glivenkoCantelli_and_error_stability
    cells sample score contribution weight target denominator normalizer
    cellContribution cellWeight contributionLimit weightLimit massLimit
    actualVariance scoreReplicationError biasCorrectionError herror_decomp
    hcover hcontributionCell hweightCell hcontributionLimit hweightLimit
    (weighted_indicator_array_lln_of_l1BracketingNumber_obligations
      cells massLimit sample (fun _index _unit => 1) score obligations)
    hscore hbias

/--
VdV&W endpoint assemblies supply the score-cell mass LLN needed for actual
bootstrap variance consistency from score-cell contribution and weight limits.
-/
theorem
    tendsto_actualBootstrapVariance_of_cell_contribution_weight_limits_vdvw241_endpoint_assembly_and_error_stability
    [DecidableEq Cell]
    {Bracket : Type*} [Fintype Bracket]
    (cells : Finset Cell)
    (sample : ℕ -> Finset Unit)
    (score : ℕ -> Unit -> Cell)
    (contribution weight : ℕ -> Unit -> Real)
    (target denominator normalizer : Real)
    (cellContribution cellWeight : ℕ -> Cell -> Real)
    (contributionLimit weightLimit massLimit : Cell -> Real)
    (actualVariance scoreReplicationError biasCorrectionError : ℕ -> Real)
    (herror_decomp :
      (fun index =>
        actualVariance index -
          bootstrapCenteredVarianceTarget (sample index)
            (contribution index) (weight index) target denominator
            normalizer) =ᶠ[atTop]
        (fun index =>
          scoreReplicationError index + biasCorrectionError index))
    (hcover :
      ∀ index unit, unit ∈ sample index -> score index unit ∈ cells)
    (hcontributionCell :
      ∀ index unit, unit ∈ sample index ->
        cellContribution index (score index unit) = contribution index unit)
    (hweightCell :
      ∀ index unit, unit ∈ sample index ->
        cellWeight index (score index unit) = weight index unit)
    (hcontributionLimit :
      ∀ cell, cell ∈ cells ->
        Tendsto (fun index => cellContribution index cell)
          atTop (nhds (contributionLimit cell)))
    (hweightLimit :
      ∀ cell, cell ∈ cells ->
        Tendsto (fun index => cellWeight index cell)
          atTop (nhds (weightLimit cell)))
    (assembly :
      FiniteBracketEndpointStrongLawAssembly (Bracket := Bracket)
        {cell : Cell | cell ∈ cells} massLimit
        (fun sampleSize cell =>
          weightedSampleSum (sample sampleSize)
            ((fun _index _unit => 1) sampleSize)
            (scoreCellIndicator (score sampleSize) cell)))
    (hscore :
      bootstrapScoreReplicationErrorNegligible
        (l := atTop) scoreReplicationError)
    (hbias :
      bootstrapBiasCorrectionErrorNegligible
        (l := atTop) biasCorrectionError) :
    Tendsto actualVariance atTop
      (nhds
        ((1 / denominator ^ 2) * (1 / normalizer) *
          weightedScoreCellMomentLimit cells
            (fun cell =>
              (contributionLimit cell - target * weightLimit cell) ^ 2)
            massLimit)) :=
  tendsto_actualBootstrapVariance_of_cell_contribution_weight_limits_glivenkoCantelli_and_error_stability
    cells sample score contribution weight target denominator normalizer
    cellContribution cellWeight contributionLimit weightLimit massLimit
    actualVariance scoreReplicationError biasCorrectionError herror_decomp
    hcover hcontributionCell hweightCell hcontributionLimit hweightLimit
    (weighted_indicator_array_lln_of_vdvw241_endpoint_assembly
      cells massLimit sample (fun _index _unit => 1) score assembly)
    hscore hbias

/--
Finite `L1(P)` bracketing supplies the score-cell mass LLN needed for the
eventual score-cell contribution/weight version of actual bootstrap variance
consistency.
-/
theorem
    tendsto_actualBootstrapVariance_of_eventually_cell_contribution_weight_limits_l1BracketingNumber_obligations_and_error_stability
    [DecidableEq Cell]
    {Bracket : Type*} [Fintype Bracket]
    (cells : Finset Cell)
    (sample : ℕ -> Finset Unit)
    (score : ℕ -> Unit -> Cell)
    (contribution weight : ℕ -> Unit -> Real)
    (target denominator normalizer : Real)
    (cellContribution cellWeight : ℕ -> Cell -> Real)
    (contributionLimit weightLimit massLimit : Cell -> Real)
    (actualVariance scoreReplicationError biasCorrectionError : ℕ -> Real)
    (herror_decomp :
      (fun index =>
        actualVariance index -
          bootstrapCenteredVarianceTarget (sample index)
            (contribution index) (weight index) target denominator
            normalizer) =ᶠ[atTop]
        (fun index =>
          scoreReplicationError index + biasCorrectionError index))
    (hcover :
      ∀ᶠ index in atTop,
        ∀ unit, unit ∈ sample index -> score index unit ∈ cells)
    (hcontributionCell :
      ∀ᶠ index in atTop,
        ∀ unit, unit ∈ sample index ->
          cellContribution index (score index unit) =
            contribution index unit)
    (hweightCell :
      ∀ᶠ index in atTop,
        ∀ unit, unit ∈ sample index ->
          cellWeight index (score index unit) = weight index unit)
    (hcontributionLimit :
      ∀ cell, cell ∈ cells ->
        Tendsto (fun index => cellContribution index cell)
          atTop (nhds (contributionLimit cell)))
    (hweightLimit :
      ∀ cell, cell ∈ cells ->
        Tendsto (fun index => cellWeight index cell)
          atTop (nhds (weightLimit cell)))
    (obligations :
      L1BracketingNumberConstructorObligations (Bracket := Bracket)
        {cell : Cell | cell ∈ cells} massLimit
        (fun sampleSize cell =>
          weightedSampleSum (sample sampleSize)
            ((fun _index _unit => 1) sampleSize)
            (scoreCellIndicator (score sampleSize) cell)))
    (hscore :
      bootstrapScoreReplicationErrorNegligible
        (l := atTop) scoreReplicationError)
    (hbias :
      bootstrapBiasCorrectionErrorNegligible
        (l := atTop) biasCorrectionError) :
    Tendsto actualVariance atTop
      (nhds
        ((1 / denominator ^ 2) * (1 / normalizer) *
          weightedScoreCellMomentLimit cells
            (fun cell =>
              (contributionLimit cell - target * weightLimit cell) ^ 2)
            massLimit)) :=
  tendsto_actualBootstrapVariance_of_eventually_cell_contribution_weight_limits_glivenkoCantelli_and_error_stability
    cells sample score contribution weight target denominator normalizer
    cellContribution cellWeight contributionLimit weightLimit massLimit
    actualVariance scoreReplicationError biasCorrectionError herror_decomp
    hcover hcontributionCell hweightCell hcontributionLimit hweightLimit
    (weighted_indicator_array_lln_of_l1BracketingNumber_obligations
      cells massLimit sample (fun _index _unit => 1) score obligations)
    hscore hbias

/--
VdV&W endpoint assemblies supply the score-cell mass LLN needed for the
eventual score-cell contribution/weight version of actual bootstrap variance
consistency.
-/
theorem
    tendsto_actualBootstrapVariance_of_eventually_cell_contribution_weight_limits_vdvw241_endpoint_assembly_and_error_stability
    [DecidableEq Cell]
    {Bracket : Type*} [Fintype Bracket]
    (cells : Finset Cell)
    (sample : ℕ -> Finset Unit)
    (score : ℕ -> Unit -> Cell)
    (contribution weight : ℕ -> Unit -> Real)
    (target denominator normalizer : Real)
    (cellContribution cellWeight : ℕ -> Cell -> Real)
    (contributionLimit weightLimit massLimit : Cell -> Real)
    (actualVariance scoreReplicationError biasCorrectionError : ℕ -> Real)
    (herror_decomp :
      (fun index =>
        actualVariance index -
          bootstrapCenteredVarianceTarget (sample index)
            (contribution index) (weight index) target denominator
            normalizer) =ᶠ[atTop]
        (fun index =>
          scoreReplicationError index + biasCorrectionError index))
    (hcover :
      ∀ᶠ index in atTop,
        ∀ unit, unit ∈ sample index -> score index unit ∈ cells)
    (hcontributionCell :
      ∀ᶠ index in atTop,
        ∀ unit, unit ∈ sample index ->
          cellContribution index (score index unit) =
            contribution index unit)
    (hweightCell :
      ∀ᶠ index in atTop,
        ∀ unit, unit ∈ sample index ->
          cellWeight index (score index unit) = weight index unit)
    (hcontributionLimit :
      ∀ cell, cell ∈ cells ->
        Tendsto (fun index => cellContribution index cell)
          atTop (nhds (contributionLimit cell)))
    (hweightLimit :
      ∀ cell, cell ∈ cells ->
        Tendsto (fun index => cellWeight index cell)
          atTop (nhds (weightLimit cell)))
    (assembly :
      FiniteBracketEndpointStrongLawAssembly (Bracket := Bracket)
        {cell : Cell | cell ∈ cells} massLimit
        (fun sampleSize cell =>
          weightedSampleSum (sample sampleSize)
            ((fun _index _unit => 1) sampleSize)
            (scoreCellIndicator (score sampleSize) cell)))
    (hscore :
      bootstrapScoreReplicationErrorNegligible
        (l := atTop) scoreReplicationError)
    (hbias :
      bootstrapBiasCorrectionErrorNegligible
        (l := atTop) biasCorrectionError) :
    Tendsto actualVariance atTop
      (nhds
        ((1 / denominator ^ 2) * (1 / normalizer) *
          weightedScoreCellMomentLimit cells
            (fun cell =>
              (contributionLimit cell - target * weightLimit cell) ^ 2)
            massLimit)) :=
  tendsto_actualBootstrapVariance_of_eventually_cell_contribution_weight_limits_glivenkoCantelli_and_error_stability
    cells sample score contribution weight target denominator normalizer
    cellContribution cellWeight contributionLimit weightLimit massLimit
    actualVariance scoreReplicationError biasCorrectionError herror_decomp
    hcover hcontributionCell hweightCell hcontributionLimit hweightLimit
    (weighted_indicator_array_lln_of_vdvw241_endpoint_assembly
      cells massLimit sample (fun _index _unit => 1) score assembly)
    hscore hbias

end WDSM
end Matching
end StatInference
