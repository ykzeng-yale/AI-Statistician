import Mathlib.Data.Finset.Basic
import Mathlib.Topology.Basic
import StatInference.Matching.WDSM.BootstrapActualVarianceErrorBoundBridge
import StatInference.Matching.WDSM.BootstrapScoreCellLimitBridge

/-!
# Actual bootstrap variance from finite error envelopes

This module composes the finite-cell actual bootstrap variance bridge with
finite-component error envelopes.  It is the generic layer needed before the
scenario-specific WDSM bootstrap arrays: contribution and denominator-weight
limits feed the finite-cell variance route, while score-replication and
bias-correction errors are controlled by common shrinking envelopes.
-/

namespace StatInference
namespace Matching
namespace WDSM

open Filter

variable {Index Unit Cell ScoreComponent BiasComponent : Type*}
variable {l : Filter Index}

/--
Actual bootstrap variance convergence from eventual score-cell contribution
and denominator-weight representations, contribution/weight limits, score-cell
mass convergence, and finite-component score/bias errors bounded by common
shrinking envelopes.
-/
theorem tendsto_actualBootstrapVariance_of_eventually_cell_contribution_weight_limits_and_finite_error_envelope_bounds
    [DecidableEq Cell] [DecidableEq ScoreComponent]
    [DecidableEq BiasComponent]
    (cells : Finset Cell)
    (scoreComponents : Finset ScoreComponent)
    (biasComponents : Finset BiasComponent)
    (sample : Index -> Finset Unit)
    (score : Index -> Unit -> Cell)
    (contribution weight : Index -> Unit -> Real)
    (target denominator normalizer : Real)
    (cellContribution cellWeight : Index -> Cell -> Real)
    (contributionLimit weightLimit massLimit : Cell -> Real)
    (actualVariance scoreReplicationError biasCorrectionError : Index -> Real)
    (scoreErrorComponent : Index -> ScoreComponent -> Real)
    (biasErrorComponent : Index -> BiasComponent -> Real)
    (scoreErrorComponentScale : ScoreComponent -> Real)
    (biasErrorComponentScale : BiasComponent -> Real)
    (scoreErrorEnvelope biasErrorEnvelope : Index -> Real)
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
    (hscore_decomp :
      scoreReplicationError =ᶠ[l]
        (fun index => ∑ component ∈ scoreComponents,
          scoreErrorComponent index component))
    (hscore_component_bound :
      ∀ᶠ index in l,
        ∀ component, component ∈ scoreComponents ->
          |scoreErrorComponent index component| ≤
            scoreErrorComponentScale component * scoreErrorEnvelope index)
    (hscore_error_envelope_tendsto :
      Tendsto scoreErrorEnvelope l (nhds 0))
    (hbias_decomp :
      biasCorrectionError =ᶠ[l]
        (fun index => ∑ component ∈ biasComponents,
          biasErrorComponent index component))
    (hbias_component_bound :
      ∀ᶠ index in l,
        ∀ component, component ∈ biasComponents ->
          |biasErrorComponent index component| ≤
            biasErrorComponentScale component * biasErrorEnvelope index)
    (hbias_error_envelope_tendsto :
      Tendsto biasErrorEnvelope l (nhds 0)) :
    Tendsto actualVariance l
      (nhds
        ((1 / denominator ^ 2) * (1 / normalizer) *
          weightedScoreCellMomentLimit cells
            (fun cell =>
              (contributionLimit cell - target * weightLimit cell) ^ 2)
            massLimit)) :=
  tendsto_actualBootstrapVariance_of_eventually_cell_contribution_weight_limits_and_finite_error_bounds
    (l := l) cells scoreComponents biasComponents sample score
    contribution weight target denominator normalizer cellContribution
    cellWeight contributionLimit weightLimit massLimit actualVariance
    scoreReplicationError biasCorrectionError scoreErrorComponent
    (fun index component =>
      scoreErrorComponentScale component * scoreErrorEnvelope index)
    biasErrorComponent
    (fun index component =>
      biasErrorComponentScale component * biasErrorEnvelope index)
    herror_decomp hcover hcontributionCell hweightCell hcontributionLimit
    hweightLimit hmass hscore_decomp hscore_component_bound
    (fun component _hcomponent => by
      simpa using
        ((tendsto_const_nhds :
          Tendsto (fun _index : Index => scoreErrorComponentScale component)
            l (nhds (scoreErrorComponentScale component))).mul
          hscore_error_envelope_tendsto))
    hbias_decomp hbias_component_bound
    (fun component _hcomponent => by
      simpa using
        ((tendsto_const_nhds :
          Tendsto (fun _index : Index => biasErrorComponentScale component)
            l (nhds (biasErrorComponentScale component))).mul
          hbias_error_envelope_tendsto))

/--
Actual bootstrap variance convergence from a fixed finite-cell loading when
score-replication and bias-correction errors decompose into finite
score-cell-by-component sums controlled by fixed cell-component scales times
shrinking envelopes.
-/
theorem tendsto_actualBootstrapVariance_of_finiteCell_and_finite_score_cell_error_envelope_bounds
    [DecidableEq Cell] [DecidableEq ScoreComponent]
    [DecidableEq BiasComponent]
    (cells : Finset Cell)
    (scoreComponents : Finset ScoreComponent)
    (biasComponents : Finset BiasComponent)
    (sample : Index -> Finset Unit)
    (score : Index -> Unit -> Cell)
    (contribution weight : Index -> Unit -> Real)
    (target denominator normalizer : Real)
    (loading massLimit : Cell -> Real)
    (actualVariance scoreReplicationError biasCorrectionError : Index -> Real)
    (scoreErrorComponent : Index -> Cell -> ScoreComponent -> Real)
    (biasErrorComponent : Index -> Cell -> BiasComponent -> Real)
    (scoreErrorComponentScale : Cell -> ScoreComponent -> Real)
    (biasErrorComponentScale : Cell -> BiasComponent -> Real)
    (scoreErrorEnvelope biasErrorEnvelope : Index -> Real)
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
    (hscore_decomp :
      scoreReplicationError =ᶠ[l]
        (fun index => ∑ cell ∈ cells, ∑ component ∈ scoreComponents,
          scoreErrorComponent index cell component))
    (hscore_component_bound :
      ∀ᶠ index in l,
        ∀ cell, cell ∈ cells ->
          ∀ component, component ∈ scoreComponents ->
            |scoreErrorComponent index cell component| ≤
              scoreErrorComponentScale cell component *
                scoreErrorEnvelope index)
    (hscore_error_envelope_tendsto :
      Tendsto scoreErrorEnvelope l (nhds 0))
    (hbias_decomp :
      biasCorrectionError =ᶠ[l]
        (fun index => ∑ cell ∈ cells, ∑ component ∈ biasComponents,
          biasErrorComponent index cell component))
    (hbias_component_bound :
      ∀ᶠ index in l,
        ∀ cell, cell ∈ cells ->
          ∀ component, component ∈ biasComponents ->
            |biasErrorComponent index cell component| ≤
              biasErrorComponentScale cell component *
                biasErrorEnvelope index)
    (hbias_error_envelope_tendsto :
      Tendsto biasErrorEnvelope l (nhds 0)) :
    Tendsto actualVariance l
      (nhds
        ((1 / denominator ^ 2) * (1 / normalizer) *
          weightedScoreCellMomentLimit cells loading massLimit)) :=
  tendsto_actualBootstrapVariance_of_finiteCell_and_finite_score_cell_error_bounds
    (l := l) cells scoreComponents biasComponents sample score
    contribution weight target denominator normalizer loading massLimit
    actualVariance scoreReplicationError biasCorrectionError
    scoreErrorComponent
    (fun index cell component =>
      scoreErrorComponentScale cell component * scoreErrorEnvelope index)
    biasErrorComponent
    (fun index cell component =>
      biasErrorComponentScale cell component * biasErrorEnvelope index)
    herror_decomp hcover hloading hmass hscore_decomp
    hscore_component_bound
    (fun cell _hcell component _hcomponent => by
      simpa using
        ((tendsto_const_nhds :
          Tendsto
            (fun _index : Index => scoreErrorComponentScale cell component)
            l (nhds (scoreErrorComponentScale cell component))).mul
          hscore_error_envelope_tendsto))
    hbias_decomp hbias_component_bound
    (fun cell _hcell component _hcomponent => by
      simpa using
        ((tendsto_const_nhds :
          Tendsto
            (fun _index : Index => biasErrorComponentScale cell component)
            l (nhds (biasErrorComponentScale cell component))).mul
          hbias_error_envelope_tendsto))

/--
Actual bootstrap variance convergence from eventual score-cell contribution
and denominator-weight representations when score-replication and
bias-correction errors decompose into finite score-cell-by-component sums
controlled by fixed cell-component scales times shrinking envelopes.
-/
theorem tendsto_actualBootstrapVariance_of_eventually_cell_contribution_weight_limits_and_finite_score_cell_error_envelope_bounds
    [DecidableEq Cell] [DecidableEq ScoreComponent]
    [DecidableEq BiasComponent]
    (cells : Finset Cell)
    (scoreComponents : Finset ScoreComponent)
    (biasComponents : Finset BiasComponent)
    (sample : Index -> Finset Unit)
    (score : Index -> Unit -> Cell)
    (contribution weight : Index -> Unit -> Real)
    (target denominator normalizer : Real)
    (cellContribution cellWeight : Index -> Cell -> Real)
    (contributionLimit weightLimit massLimit : Cell -> Real)
    (actualVariance scoreReplicationError biasCorrectionError : Index -> Real)
    (scoreErrorComponent : Index -> Cell -> ScoreComponent -> Real)
    (biasErrorComponent : Index -> Cell -> BiasComponent -> Real)
    (scoreErrorComponentScale : Cell -> ScoreComponent -> Real)
    (biasErrorComponentScale : Cell -> BiasComponent -> Real)
    (scoreErrorEnvelope biasErrorEnvelope : Index -> Real)
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
    (hscore_decomp :
      scoreReplicationError =ᶠ[l]
        (fun index => ∑ cell ∈ cells, ∑ component ∈ scoreComponents,
          scoreErrorComponent index cell component))
    (hscore_component_bound :
      ∀ᶠ index in l,
        ∀ cell, cell ∈ cells ->
          ∀ component, component ∈ scoreComponents ->
            |scoreErrorComponent index cell component| ≤
              scoreErrorComponentScale cell component *
                scoreErrorEnvelope index)
    (hscore_error_envelope_tendsto :
      Tendsto scoreErrorEnvelope l (nhds 0))
    (hbias_decomp :
      biasCorrectionError =ᶠ[l]
        (fun index => ∑ cell ∈ cells, ∑ component ∈ biasComponents,
          biasErrorComponent index cell component))
    (hbias_component_bound :
      ∀ᶠ index in l,
        ∀ cell, cell ∈ cells ->
          ∀ component, component ∈ biasComponents ->
            |biasErrorComponent index cell component| ≤
              biasErrorComponentScale cell component *
                biasErrorEnvelope index)
    (hbias_error_envelope_tendsto :
      Tendsto biasErrorEnvelope l (nhds 0)) :
    Tendsto actualVariance l
      (nhds
        ((1 / denominator ^ 2) * (1 / normalizer) *
          weightedScoreCellMomentLimit cells
            (fun cell =>
              (contributionLimit cell - target * weightLimit cell) ^ 2)
            massLimit)) :=
  tendsto_actualBootstrapVariance_of_eventually_cell_contribution_weight_limits_and_finite_score_cell_error_bounds
    (l := l) cells scoreComponents biasComponents sample score
    contribution weight target denominator normalizer cellContribution
    cellWeight contributionLimit weightLimit massLimit actualVariance
    scoreReplicationError biasCorrectionError scoreErrorComponent
    (fun index cell component =>
      scoreErrorComponentScale cell component * scoreErrorEnvelope index)
    biasErrorComponent
    (fun index cell component =>
      biasErrorComponentScale cell component * biasErrorEnvelope index)
    herror_decomp hcover hcontributionCell hweightCell hcontributionLimit
    hweightLimit hmass hscore_decomp hscore_component_bound
    (fun cell _hcell component _hcomponent => by
      simpa using
        ((tendsto_const_nhds :
          Tendsto
            (fun _index : Index => scoreErrorComponentScale cell component)
            l (nhds (scoreErrorComponentScale cell component))).mul
          hscore_error_envelope_tendsto))
    hbias_decomp hbias_component_bound
    (fun cell _hcell component _hcomponent => by
      simpa using
        ((tendsto_const_nhds :
          Tendsto
            (fun _index : Index => biasErrorComponentScale cell component)
            l (nhds (biasErrorComponentScale cell component))).mul
          hbias_error_envelope_tendsto))

/--
Actual bootstrap variance convergence from eventual score-cell contribution
and denominator-weight representations when score-replication has a concrete
finite score-cell decomposition controlled by one shrinking envelope, while
bias-correction uses the existing finite component error-bound route.
-/
theorem tendsto_actualBootstrapVariance_of_eventually_cell_contribution_weight_limits_and_finite_score_cell_score_error_envelope_bounds
    [DecidableEq Cell] [DecidableEq ScoreComponent]
    [DecidableEq BiasComponent]
    (cells : Finset Cell)
    (scoreComponents : Finset ScoreComponent)
    (biasComponents : Finset BiasComponent)
    (sample : Index -> Finset Unit)
    (score : Index -> Unit -> Cell)
    (contribution weight : Index -> Unit -> Real)
    (target denominator normalizer : Real)
    (cellContribution cellWeight : Index -> Cell -> Real)
    (contributionLimit weightLimit massLimit : Cell -> Real)
    (actualVariance scoreReplicationError biasCorrectionError : Index -> Real)
    (scoreErrorComponent : Index -> Cell -> ScoreComponent -> Real)
    (scoreErrorComponentScale : Cell -> ScoreComponent -> Real)
    (scoreErrorEnvelope : Index -> Real)
    (biasErrorComponent biasErrorComponentBound :
      Index -> BiasComponent -> Real)
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
    (hscore_decomp :
      scoreReplicationError =ᶠ[l]
        (fun index => ∑ cell ∈ cells, ∑ component ∈ scoreComponents,
          scoreErrorComponent index cell component))
    (hscore_component_bound :
      ∀ᶠ index in l,
        ∀ cell, cell ∈ cells ->
          ∀ component, component ∈ scoreComponents ->
            |scoreErrorComponent index cell component| ≤
              scoreErrorComponentScale cell component *
                scoreErrorEnvelope index)
    (hscore_error_envelope_tendsto :
      Tendsto scoreErrorEnvelope l (nhds 0))
    (hbias_decomp :
      biasCorrectionError =ᶠ[l]
        (fun index => ∑ component ∈ biasComponents,
          biasErrorComponent index component))
    (hbias_component_bound :
      ∀ᶠ index in l,
        ∀ component, component ∈ biasComponents ->
          |biasErrorComponent index component| ≤
            biasErrorComponentBound index component)
    (hbias_component_bound_tendsto :
      ∀ component, component ∈ biasComponents ->
        Tendsto (fun index => biasErrorComponentBound index component)
          l (nhds 0)) :
    Tendsto actualVariance l
      (nhds
        ((1 / denominator ^ 2) * (1 / normalizer) *
          weightedScoreCellMomentLimit cells
            (fun cell =>
              (contributionLimit cell - target * weightLimit cell) ^ 2)
            massLimit)) :=
  tendsto_actualBootstrapVariance_of_eventually_cell_contribution_weight_limits_and_finite_score_cell_score_error_bounds
    (l := l) cells scoreComponents biasComponents sample score
    contribution weight target denominator normalizer cellContribution
    cellWeight contributionLimit weightLimit massLimit actualVariance
    scoreReplicationError biasCorrectionError scoreErrorComponent
    (fun index cell component =>
      scoreErrorComponentScale cell component * scoreErrorEnvelope index)
    biasErrorComponent biasErrorComponentBound herror_decomp hcover
    hcontributionCell hweightCell hcontributionLimit hweightLimit hmass
    hscore_decomp hscore_component_bound
    (fun cell _hcell component _hcomponent => by
      simpa using
        ((tendsto_const_nhds :
          Tendsto
            (fun _index : Index => scoreErrorComponentScale cell component)
            l (nhds (scoreErrorComponentScale cell component))).mul
          hscore_error_envelope_tendsto))
    hbias_decomp hbias_component_bound hbias_component_bound_tendsto

/--
Actual bootstrap variance convergence from eventual score-cell contribution
and denominator-weight representations when bias-correction has a concrete
finite score-cell decomposition controlled by one shrinking envelope, while
score-replication uses the existing finite component error-bound route.
-/
theorem tendsto_actualBootstrapVariance_of_eventually_cell_contribution_weight_limits_and_finite_score_cell_bias_error_envelope_bounds
    [DecidableEq Cell] [DecidableEq ScoreComponent]
    [DecidableEq BiasComponent]
    (cells : Finset Cell)
    (scoreComponents : Finset ScoreComponent)
    (biasComponents : Finset BiasComponent)
    (sample : Index -> Finset Unit)
    (score : Index -> Unit -> Cell)
    (contribution weight : Index -> Unit -> Real)
    (target denominator normalizer : Real)
    (cellContribution cellWeight : Index -> Cell -> Real)
    (contributionLimit weightLimit massLimit : Cell -> Real)
    (actualVariance scoreReplicationError biasCorrectionError : Index -> Real)
    (scoreErrorComponent scoreErrorComponentBound :
      Index -> ScoreComponent -> Real)
    (biasErrorComponent : Index -> Cell -> BiasComponent -> Real)
    (biasErrorComponentScale : Cell -> BiasComponent -> Real)
    (biasErrorEnvelope : Index -> Real)
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
    (hscore_decomp :
      scoreReplicationError =ᶠ[l]
        (fun index => ∑ component ∈ scoreComponents,
          scoreErrorComponent index component))
    (hscore_component_bound :
      ∀ᶠ index in l,
        ∀ component, component ∈ scoreComponents ->
          |scoreErrorComponent index component| ≤
            scoreErrorComponentBound index component)
    (hscore_component_bound_tendsto :
      ∀ component, component ∈ scoreComponents ->
        Tendsto (fun index => scoreErrorComponentBound index component)
          l (nhds 0))
    (hbias_decomp :
      biasCorrectionError =ᶠ[l]
        (fun index => ∑ cell ∈ cells, ∑ component ∈ biasComponents,
          biasErrorComponent index cell component))
    (hbias_component_bound :
      ∀ᶠ index in l,
        ∀ cell, cell ∈ cells ->
          ∀ component, component ∈ biasComponents ->
            |biasErrorComponent index cell component| ≤
              biasErrorComponentScale cell component *
                biasErrorEnvelope index)
    (hbias_error_envelope_tendsto :
      Tendsto biasErrorEnvelope l (nhds 0)) :
    Tendsto actualVariance l
      (nhds
        ((1 / denominator ^ 2) * (1 / normalizer) *
          weightedScoreCellMomentLimit cells
            (fun cell =>
              (contributionLimit cell - target * weightLimit cell) ^ 2)
            massLimit)) :=
  tendsto_actualBootstrapVariance_of_eventually_cell_contribution_weight_limits_and_finite_score_cell_bias_error_bounds
    (l := l) cells scoreComponents biasComponents sample score
    contribution weight target denominator normalizer cellContribution
    cellWeight contributionLimit weightLimit massLimit actualVariance
    scoreReplicationError biasCorrectionError scoreErrorComponent
    scoreErrorComponentBound biasErrorComponent
    (fun index cell component =>
      biasErrorComponentScale cell component * biasErrorEnvelope index)
    herror_decomp hcover hcontributionCell hweightCell hcontributionLimit
    hweightLimit hmass hscore_decomp hscore_component_bound
    hscore_component_bound_tendsto hbias_decomp hbias_component_bound
    (fun cell _hcell component _hcomponent => by
      simpa using
        ((tendsto_const_nhds :
          Tendsto
            (fun _index : Index => biasErrorComponentScale cell component)
            l (nhds (biasErrorComponentScale cell component))).mul
          hbias_error_envelope_tendsto))

/--
Finite `L1(P)` bracketing supplies score-cell mass convergence while
finite-component shrinking envelopes supply score-replication and
bias-correction negligibility, for the eventual contribution/weight-limit
actual bootstrap variance route.
-/
theorem
    tendsto_actualBootstrapVariance_of_eventually_cell_contribution_weight_limits_l1BracketingNumber_obligations_and_finite_error_envelope_bounds
    [DecidableEq Cell] [DecidableEq ScoreComponent]
    [DecidableEq BiasComponent]
    {Bracket : Type*} [Fintype Bracket]
    (cells : Finset Cell)
    (scoreComponents : Finset ScoreComponent)
    (biasComponents : Finset BiasComponent)
    (sample : ℕ -> Finset Unit)
    (score : ℕ -> Unit -> Cell)
    (contribution weight : ℕ -> Unit -> Real)
    (target denominator normalizer : Real)
    (cellContribution cellWeight : ℕ -> Cell -> Real)
    (contributionLimit weightLimit massLimit : Cell -> Real)
    (actualVariance scoreReplicationError biasCorrectionError : ℕ -> Real)
    (scoreErrorComponent : ℕ -> ScoreComponent -> Real)
    (biasErrorComponent : ℕ -> BiasComponent -> Real)
    (scoreErrorComponentScale : ScoreComponent -> Real)
    (biasErrorComponentScale : BiasComponent -> Real)
    (scoreErrorEnvelope biasErrorEnvelope : ℕ -> Real)
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
    (hscore_decomp :
      scoreReplicationError =ᶠ[atTop]
        (fun index => ∑ component ∈ scoreComponents,
          scoreErrorComponent index component))
    (hscore_component_bound :
      ∀ᶠ index in atTop,
        ∀ component, component ∈ scoreComponents ->
          |scoreErrorComponent index component| ≤
            scoreErrorComponentScale component * scoreErrorEnvelope index)
    (hscore_error_envelope_tendsto :
      Tendsto scoreErrorEnvelope atTop (nhds 0))
    (hbias_decomp :
      biasCorrectionError =ᶠ[atTop]
        (fun index => ∑ component ∈ biasComponents,
          biasErrorComponent index component))
    (hbias_component_bound :
      ∀ᶠ index in atTop,
        ∀ component, component ∈ biasComponents ->
          |biasErrorComponent index component| ≤
            biasErrorComponentScale component * biasErrorEnvelope index)
    (hbias_error_envelope_tendsto :
      Tendsto biasErrorEnvelope atTop (nhds 0)) :
    Tendsto actualVariance atTop
      (nhds
        ((1 / denominator ^ 2) * (1 / normalizer) *
          weightedScoreCellMomentLimit cells
            (fun cell =>
              (contributionLimit cell - target * weightLimit cell) ^ 2)
            massLimit)) :=
  tendsto_actualBootstrapVariance_of_eventually_cell_contribution_weight_limits_l1BracketingNumber_obligations_and_finite_error_bounds
    (Bracket := Bracket) cells scoreComponents biasComponents sample score
    contribution weight target denominator normalizer cellContribution
    cellWeight contributionLimit weightLimit massLimit actualVariance
    scoreReplicationError biasCorrectionError scoreErrorComponent
    (fun index component =>
      scoreErrorComponentScale component * scoreErrorEnvelope index)
    biasErrorComponent
    (fun index component =>
      biasErrorComponentScale component * biasErrorEnvelope index)
    herror_decomp hcover hcontributionCell hweightCell hcontributionLimit
    hweightLimit obligations hscore_decomp hscore_component_bound
    (fun component _hcomponent => by
      simpa using
        ((tendsto_const_nhds :
          Tendsto (fun _index : ℕ => scoreErrorComponentScale component)
            atTop (nhds (scoreErrorComponentScale component))).mul
          hscore_error_envelope_tendsto))
    hbias_decomp hbias_component_bound
    (fun component _hcomponent => by
      simpa using
        ((tendsto_const_nhds :
          Tendsto (fun _index : ℕ => biasErrorComponentScale component)
            atTop (nhds (biasErrorComponentScale component))).mul
          hbias_error_envelope_tendsto))

/--
VdV&W endpoint assemblies supply score-cell mass convergence while
finite-component shrinking envelopes supply score-replication and
bias-correction negligibility, for the eventual contribution/weight-limit
actual bootstrap variance route.
-/
theorem
    tendsto_actualBootstrapVariance_of_eventually_cell_contribution_weight_limits_vdvw241_endpoint_assembly_and_finite_error_envelope_bounds
    [DecidableEq Cell] [DecidableEq ScoreComponent]
    [DecidableEq BiasComponent]
    {Bracket : Type*} [Fintype Bracket]
    (cells : Finset Cell)
    (scoreComponents : Finset ScoreComponent)
    (biasComponents : Finset BiasComponent)
    (sample : ℕ -> Finset Unit)
    (score : ℕ -> Unit -> Cell)
    (contribution weight : ℕ -> Unit -> Real)
    (target denominator normalizer : Real)
    (cellContribution cellWeight : ℕ -> Cell -> Real)
    (contributionLimit weightLimit massLimit : Cell -> Real)
    (actualVariance scoreReplicationError biasCorrectionError : ℕ -> Real)
    (scoreErrorComponent : ℕ -> ScoreComponent -> Real)
    (biasErrorComponent : ℕ -> BiasComponent -> Real)
    (scoreErrorComponentScale : ScoreComponent -> Real)
    (biasErrorComponentScale : BiasComponent -> Real)
    (scoreErrorEnvelope biasErrorEnvelope : ℕ -> Real)
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
    (hscore_decomp :
      scoreReplicationError =ᶠ[atTop]
        (fun index => ∑ component ∈ scoreComponents,
          scoreErrorComponent index component))
    (hscore_component_bound :
      ∀ᶠ index in atTop,
        ∀ component, component ∈ scoreComponents ->
          |scoreErrorComponent index component| ≤
            scoreErrorComponentScale component * scoreErrorEnvelope index)
    (hscore_error_envelope_tendsto :
      Tendsto scoreErrorEnvelope atTop (nhds 0))
    (hbias_decomp :
      biasCorrectionError =ᶠ[atTop]
        (fun index => ∑ component ∈ biasComponents,
          biasErrorComponent index component))
    (hbias_component_bound :
      ∀ᶠ index in atTop,
        ∀ component, component ∈ biasComponents ->
          |biasErrorComponent index component| ≤
            biasErrorComponentScale component * biasErrorEnvelope index)
    (hbias_error_envelope_tendsto :
      Tendsto biasErrorEnvelope atTop (nhds 0)) :
    Tendsto actualVariance atTop
      (nhds
        ((1 / denominator ^ 2) * (1 / normalizer) *
          weightedScoreCellMomentLimit cells
            (fun cell =>
              (contributionLimit cell - target * weightLimit cell) ^ 2)
            massLimit)) :=
  tendsto_actualBootstrapVariance_of_eventually_cell_contribution_weight_limits_vdvw241_endpoint_assembly_and_finite_error_bounds
    (Bracket := Bracket) cells scoreComponents biasComponents sample score
    contribution weight target denominator normalizer cellContribution
    cellWeight contributionLimit weightLimit massLimit actualVariance
    scoreReplicationError biasCorrectionError scoreErrorComponent
    (fun index component =>
      scoreErrorComponentScale component * scoreErrorEnvelope index)
    biasErrorComponent
    (fun index component =>
      biasErrorComponentScale component * biasErrorEnvelope index)
    herror_decomp hcover hcontributionCell hweightCell hcontributionLimit
    hweightLimit assembly hscore_decomp hscore_component_bound
    (fun component _hcomponent => by
      simpa using
        ((tendsto_const_nhds :
          Tendsto (fun _index : ℕ => scoreErrorComponentScale component)
            atTop (nhds (scoreErrorComponentScale component))).mul
          hscore_error_envelope_tendsto))
    hbias_decomp hbias_component_bound
    (fun component _hcomponent => by
      simpa using
        ((tendsto_const_nhds :
          Tendsto (fun _index : ℕ => biasErrorComponentScale component)
            atTop (nhds (biasErrorComponentScale component))).mul
          hbias_error_envelope_tendsto))

/--
Eventual-equality version of
`tendsto_actualBootstrapVariance_of_eventually_cell_contribution_weight_limits_and_finite_error_envelope_bounds`.
-/
theorem tendsto_actualBootstrapVariance_of_eventually_cell_contribution_weight_eq_and_finite_error_envelope_bounds
    [DecidableEq Cell] [DecidableEq ScoreComponent]
    [DecidableEq BiasComponent]
    (cells : Finset Cell)
    (scoreComponents : Finset ScoreComponent)
    (biasComponents : Finset BiasComponent)
    (sample : Index -> Finset Unit)
    (score : Index -> Unit -> Cell)
    (contribution weight : Index -> Unit -> Real)
    (target denominator normalizer : Real)
    (cellContribution cellWeight : Index -> Cell -> Real)
    (contributionLimit weightLimit massLimit : Cell -> Real)
    (actualVariance scoreReplicationError biasCorrectionError : Index -> Real)
    (scoreErrorComponent : Index -> ScoreComponent -> Real)
    (biasErrorComponent : Index -> BiasComponent -> Real)
    (scoreErrorComponentScale : ScoreComponent -> Real)
    (biasErrorComponentScale : BiasComponent -> Real)
    (scoreErrorEnvelope biasErrorEnvelope : Index -> Real)
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
        (fun index => ∑ component ∈ scoreComponents,
          scoreErrorComponent index component))
    (hscore_component_bound :
      ∀ᶠ index in l,
        ∀ component, component ∈ scoreComponents ->
          |scoreErrorComponent index component| ≤
            scoreErrorComponentScale component * scoreErrorEnvelope index)
    (hscore_error_envelope_tendsto :
      Tendsto scoreErrorEnvelope l (nhds 0))
    (hbias_decomp :
      biasCorrectionError =ᶠ[l]
        (fun index => ∑ component ∈ biasComponents,
          biasErrorComponent index component))
    (hbias_component_bound :
      ∀ᶠ index in l,
        ∀ component, component ∈ biasComponents ->
          |biasErrorComponent index component| ≤
            biasErrorComponentScale component * biasErrorEnvelope index)
    (hbias_error_envelope_tendsto :
      Tendsto biasErrorEnvelope l (nhds 0)) :
    Tendsto actualVariance l
      (nhds
        ((1 / denominator ^ 2) * (1 / normalizer) *
          weightedScoreCellMomentLimit cells
            (fun cell =>
              (contributionLimit cell - target * weightLimit cell) ^ 2)
            massLimit)) :=
  tendsto_actualBootstrapVariance_of_eventually_cell_contribution_weight_limits_and_finite_error_envelope_bounds
    (l := l) cells scoreComponents biasComponents sample score
    contribution weight target denominator normalizer cellContribution
    cellWeight contributionLimit weightLimit massLimit actualVariance
    scoreReplicationError biasCorrectionError scoreErrorComponent
    biasErrorComponent scoreErrorComponentScale biasErrorComponentScale
    scoreErrorEnvelope biasErrorEnvelope herror_decomp hcover
    hcontributionCell hweightCell
    (cellwise_tendsto_real_of_eventually_eq_const
      (l := l) cells cellContribution contributionLimit hcontributionLimit)
    (cellwise_tendsto_real_of_eventually_eq_const
      (l := l) cells cellWeight weightLimit hweightLimit)
    hmass hscore_decomp hscore_component_bound
    hscore_error_envelope_tendsto hbias_decomp hbias_component_bound
    hbias_error_envelope_tendsto

end WDSM
end Matching
end StatInference
