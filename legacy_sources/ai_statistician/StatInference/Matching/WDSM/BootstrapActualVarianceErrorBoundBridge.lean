import StatInference.Matching.WDSM.BootstrapActualVarianceConsistency
import StatInference.Matching.WDSM.BootstrapErrorBoundBridge
import StatInference.Matching.WDSM.BootstrapLinearizedReplicate
import StatInference.Matching.WDSM.BootstrapUniformResamplingLaw

/-!
# Actual bootstrap variance consistency from finite error bounds

This module composes finite-cell convergence of the linearized bootstrap
variance target with finite-component bounds for score-replication and
bias-correction errors.  It removes the need to pass negligible-error
assumptions directly when the concrete WDSM proof has decomposed those errors
into finitely many bounded components.
-/

namespace StatInference
namespace Matching
namespace WDSM

open Filter

variable {Index Unit Draw Omega Cell ScoreComponent BiasComponent : Type*}
variable {l : Filter Index}

/--
Actual bootstrap variance consistency from a fixed finite-cell loading and
finite-component score/bias error bounds.
-/
theorem tendsto_actualBootstrapVariance_of_finiteCell_and_finite_error_bounds
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
    (scoreErrorComponent scoreErrorComponentBound :
      Index -> ScoreComponent -> Real)
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
          weightedScoreCellMomentLimit cells loading massLimit)) :=
  tendsto_actualBootstrapVariance_of_finiteCell_and_error_stability
    (l := l) cells sample score contribution weight target denominator
    normalizer loading massLimit actualVariance scoreReplicationError
    biasCorrectionError herror_decomp hcover hloading hmass
    (bootstrapScoreReplicationErrorNegligible_of_finite_component_bounds
      (l := l) scoreComponents scoreReplicationError scoreErrorComponent
      scoreErrorComponentBound hscore_decomp hscore_component_bound
      hscore_component_bound_tendsto)
    (bootstrapBiasCorrectionErrorNegligible_of_finite_component_bounds
      (l := l) biasComponents biasCorrectionError biasErrorComponent
      biasErrorComponentBound hbias_decomp hbias_component_bound
      hbias_component_bound_tendsto)

/--
Actual bootstrap variance consistency from a fixed finite-cell loading when
the score-replication and bias-correction errors decompose into finite
score-cell-by-component sums.

The double finite sums are reindexed as product components and then passed to
the existing fixed finite-cell finite-error adapter.
-/
theorem tendsto_actualBootstrapVariance_of_finiteCell_and_finite_score_cell_error_bounds
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
    (scoreErrorComponent scoreErrorComponentBound :
      Index -> Cell -> ScoreComponent -> Real)
    (biasErrorComponent biasErrorComponentBound :
      Index -> Cell -> BiasComponent -> Real)
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
              scoreErrorComponentBound index cell component)
    (hscore_component_bound_tendsto :
      ∀ cell, cell ∈ cells ->
        ∀ component, component ∈ scoreComponents ->
          Tendsto
            (fun index => scoreErrorComponentBound index cell component)
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
              biasErrorComponentBound index cell component)
    (hbias_component_bound_tendsto :
      ∀ cell, cell ∈ cells ->
        ∀ component, component ∈ biasComponents ->
          Tendsto
            (fun index => biasErrorComponentBound index cell component)
            l (nhds 0)) :
    Tendsto actualVariance l
      (nhds
        ((1 / denominator ^ 2) * (1 / normalizer) *
          weightedScoreCellMomentLimit cells loading massLimit)) := by
  have hscore_decomp_product :
      scoreReplicationError =ᶠ[l]
        (fun index => ∑ pair ∈ cells.product scoreComponents,
          scoreErrorComponent index pair.1 pair.2) := by
    filter_upwards [hscore_decomp] with index hdecomp_index
    calc
      scoreReplicationError index =
          ∑ cell ∈ cells, ∑ component ∈ scoreComponents,
            scoreErrorComponent index cell component := hdecomp_index
      _ = ∑ pair ∈ cells.product scoreComponents,
            scoreErrorComponent index pair.1 pair.2 := by
          rw [← Finset.sum_product']
          rfl
  have hscore_component_bound_product :
      ∀ᶠ index in l,
        ∀ pair, pair ∈ cells.product scoreComponents ->
          |scoreErrorComponent index pair.1 pair.2| ≤
            scoreErrorComponentBound index pair.1 pair.2 := by
    filter_upwards [hscore_component_bound] with index hbound pair hpair
    rcases Finset.mem_product.mp hpair with ⟨hcell, hcomponent⟩
    exact hbound pair.1 hcell pair.2 hcomponent
  have hbias_decomp_product :
      biasCorrectionError =ᶠ[l]
        (fun index => ∑ pair ∈ cells.product biasComponents,
          biasErrorComponent index pair.1 pair.2) := by
    filter_upwards [hbias_decomp] with index hdecomp_index
    calc
      biasCorrectionError index =
          ∑ cell ∈ cells, ∑ component ∈ biasComponents,
            biasErrorComponent index cell component := hdecomp_index
      _ = ∑ pair ∈ cells.product biasComponents,
            biasErrorComponent index pair.1 pair.2 := by
          rw [← Finset.sum_product']
          rfl
  have hbias_component_bound_product :
      ∀ᶠ index in l,
        ∀ pair, pair ∈ cells.product biasComponents ->
          |biasErrorComponent index pair.1 pair.2| ≤
            biasErrorComponentBound index pair.1 pair.2 := by
    filter_upwards [hbias_component_bound] with index hbound pair hpair
    rcases Finset.mem_product.mp hpair with ⟨hcell, hcomponent⟩
    exact hbound pair.1 hcell pair.2 hcomponent
  exact
    tendsto_actualBootstrapVariance_of_finiteCell_and_finite_error_bounds
      (l := l) cells (cells.product scoreComponents)
      (cells.product biasComponents) sample score contribution weight target
      denominator normalizer loading massLimit actualVariance
      scoreReplicationError biasCorrectionError
      (fun index pair => scoreErrorComponent index pair.1 pair.2)
      (fun index pair => scoreErrorComponentBound index pair.1 pair.2)
      (fun index pair => biasErrorComponent index pair.1 pair.2)
      (fun index pair => biasErrorComponentBound index pair.1 pair.2)
      herror_decomp hcover hloading hmass hscore_decomp_product
      hscore_component_bound_product
      (fun pair hpair => by
        rcases Finset.mem_product.mp hpair with ⟨hcell, hcomponent⟩
        exact hscore_component_bound_tendsto pair.1 hcell pair.2 hcomponent)
      hbias_decomp_product hbias_component_bound_product
      (fun pair hpair => by
        rcases Finset.mem_product.mp hpair with ⟨hcell, hcomponent⟩
        exact hbias_component_bound_tendsto pair.1 hcell pair.2 hcomponent)

/--
Finite `L1(P)` bracketing supplies the score-cell mass LLN, and finite
component error bounds supply score-replication and bias-correction
negligibility, for the fixed finite-cell actual bootstrap variance route.
-/
theorem
    tendsto_actualBootstrapVariance_of_finiteCell_l1BracketingNumber_obligations_and_finite_error_bounds
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
    (loading massLimit : Cell -> Real)
    (actualVariance scoreReplicationError biasCorrectionError : ℕ -> Real)
    (scoreErrorComponent scoreErrorComponentBound :
      ℕ -> ScoreComponent -> Real)
    (biasErrorComponent biasErrorComponentBound :
      ℕ -> BiasComponent -> Real)
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
    (hscore_decomp :
      scoreReplicationError =ᶠ[atTop]
        (fun index => ∑ component ∈ scoreComponents,
          scoreErrorComponent index component))
    (hscore_component_bound :
      ∀ᶠ index in atTop,
        ∀ component, component ∈ scoreComponents ->
          |scoreErrorComponent index component| ≤
            scoreErrorComponentBound index component)
    (hscore_component_bound_tendsto :
      ∀ component, component ∈ scoreComponents ->
        Tendsto (fun index => scoreErrorComponentBound index component)
          atTop (nhds 0))
    (hbias_decomp :
      biasCorrectionError =ᶠ[atTop]
        (fun index => ∑ component ∈ biasComponents,
          biasErrorComponent index component))
    (hbias_component_bound :
      ∀ᶠ index in atTop,
        ∀ component, component ∈ biasComponents ->
          |biasErrorComponent index component| ≤
            biasErrorComponentBound index component)
    (hbias_component_bound_tendsto :
      ∀ component, component ∈ biasComponents ->
        Tendsto (fun index => biasErrorComponentBound index component)
          atTop (nhds 0)) :
    Tendsto actualVariance atTop
      (nhds
        ((1 / denominator ^ 2) * (1 / normalizer) *
          weightedScoreCellMomentLimit cells loading massLimit)) :=
  tendsto_actualBootstrapVariance_of_finiteCell_l1BracketingNumber_obligations_and_error_stability
    (Bracket := Bracket) cells sample score contribution weight target
    denominator normalizer loading massLimit actualVariance
    scoreReplicationError biasCorrectionError herror_decomp hcover hloading
    obligations
    (bootstrapScoreReplicationErrorNegligible_of_finite_component_bounds
      (l := atTop) scoreComponents scoreReplicationError
      scoreErrorComponent scoreErrorComponentBound hscore_decomp
      hscore_component_bound hscore_component_bound_tendsto)
    (bootstrapBiasCorrectionErrorNegligible_of_finite_component_bounds
      (l := atTop) biasComponents biasCorrectionError biasErrorComponent
      biasErrorComponentBound hbias_decomp hbias_component_bound
      hbias_component_bound_tendsto)

/--
VdV&W endpoint assemblies supply the score-cell mass LLN, and finite component
error bounds supply score-replication and bias-correction negligibility, for
the fixed finite-cell actual bootstrap variance route.
-/
theorem
    tendsto_actualBootstrapVariance_of_finiteCell_vdvw241_endpoint_assembly_and_finite_error_bounds
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
    (loading massLimit : Cell -> Real)
    (actualVariance scoreReplicationError biasCorrectionError : ℕ -> Real)
    (scoreErrorComponent scoreErrorComponentBound :
      ℕ -> ScoreComponent -> Real)
    (biasErrorComponent biasErrorComponentBound :
      ℕ -> BiasComponent -> Real)
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
    (hscore_decomp :
      scoreReplicationError =ᶠ[atTop]
        (fun index => ∑ component ∈ scoreComponents,
          scoreErrorComponent index component))
    (hscore_component_bound :
      ∀ᶠ index in atTop,
        ∀ component, component ∈ scoreComponents ->
          |scoreErrorComponent index component| ≤
            scoreErrorComponentBound index component)
    (hscore_component_bound_tendsto :
      ∀ component, component ∈ scoreComponents ->
        Tendsto (fun index => scoreErrorComponentBound index component)
          atTop (nhds 0))
    (hbias_decomp :
      biasCorrectionError =ᶠ[atTop]
        (fun index => ∑ component ∈ biasComponents,
          biasErrorComponent index component))
    (hbias_component_bound :
      ∀ᶠ index in atTop,
        ∀ component, component ∈ biasComponents ->
          |biasErrorComponent index component| ≤
            biasErrorComponentBound index component)
    (hbias_component_bound_tendsto :
      ∀ component, component ∈ biasComponents ->
        Tendsto (fun index => biasErrorComponentBound index component)
          atTop (nhds 0)) :
    Tendsto actualVariance atTop
      (nhds
        ((1 / denominator ^ 2) * (1 / normalizer) *
          weightedScoreCellMomentLimit cells loading massLimit)) :=
  tendsto_actualBootstrapVariance_of_finiteCell_vdvw241_endpoint_assembly_and_error_stability
    (Bracket := Bracket) cells sample score contribution weight target
    denominator normalizer loading massLimit actualVariance
    scoreReplicationError biasCorrectionError herror_decomp hcover hloading
    assembly
    (bootstrapScoreReplicationErrorNegligible_of_finite_component_bounds
      (l := atTop) scoreComponents scoreReplicationError
      scoreErrorComponent scoreErrorComponentBound hscore_decomp
      hscore_component_bound hscore_component_bound_tendsto)
    (bootstrapBiasCorrectionErrorNegligible_of_finite_component_bounds
      (l := atTop) biasComponents biasCorrectionError biasErrorComponent
      biasErrorComponentBound hbias_decomp hbias_component_bound
      hbias_component_bound_tendsto)

/--
Actual bootstrap variance consistency from score-cell contribution/weight
limits and finite-component score/bias error bounds.
-/
theorem tendsto_actualBootstrapVariance_of_cell_contribution_weight_limits_and_finite_error_bounds
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
  tendsto_actualBootstrapVariance_of_cell_contribution_weight_limits_and_error_stability
    (l := l) cells sample score contribution weight target denominator
    normalizer cellContribution cellWeight contributionLimit weightLimit
    massLimit actualVariance scoreReplicationError biasCorrectionError
    herror_decomp hcover hcontributionCell hweightCell hcontributionLimit
    hweightLimit hmass
    (bootstrapScoreReplicationErrorNegligible_of_finite_component_bounds
      (l := l) scoreComponents scoreReplicationError scoreErrorComponent
      scoreErrorComponentBound hscore_decomp hscore_component_bound
      hscore_component_bound_tendsto)
    (bootstrapBiasCorrectionErrorNegligible_of_finite_component_bounds
      (l := l) biasComponents biasCorrectionError biasErrorComponent
      biasErrorComponentBound hbias_decomp hbias_component_bound
      hbias_component_bound_tendsto)

/--
Finite `L1(P)` bracketing supplies the score-cell mass LLN, and finite
component error bounds supply score-replication and bias-correction
negligibility, for the contribution/weight-limit actual bootstrap variance
route.
-/
theorem
    tendsto_actualBootstrapVariance_of_cell_contribution_weight_limits_l1BracketingNumber_obligations_and_finite_error_bounds
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
    (scoreErrorComponent scoreErrorComponentBound :
      ℕ -> ScoreComponent -> Real)
    (biasErrorComponent biasErrorComponentBound :
      ℕ -> BiasComponent -> Real)
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
    (hscore_decomp :
      scoreReplicationError =ᶠ[atTop]
        (fun index => ∑ component ∈ scoreComponents,
          scoreErrorComponent index component))
    (hscore_component_bound :
      ∀ᶠ index in atTop,
        ∀ component, component ∈ scoreComponents ->
          |scoreErrorComponent index component| ≤
            scoreErrorComponentBound index component)
    (hscore_component_bound_tendsto :
      ∀ component, component ∈ scoreComponents ->
        Tendsto (fun index => scoreErrorComponentBound index component)
          atTop (nhds 0))
    (hbias_decomp :
      biasCorrectionError =ᶠ[atTop]
        (fun index => ∑ component ∈ biasComponents,
          biasErrorComponent index component))
    (hbias_component_bound :
      ∀ᶠ index in atTop,
        ∀ component, component ∈ biasComponents ->
          |biasErrorComponent index component| ≤
            biasErrorComponentBound index component)
    (hbias_component_bound_tendsto :
      ∀ component, component ∈ biasComponents ->
        Tendsto (fun index => biasErrorComponentBound index component)
          atTop (nhds 0)) :
    Tendsto actualVariance atTop
      (nhds
        ((1 / denominator ^ 2) * (1 / normalizer) *
          weightedScoreCellMomentLimit cells
            (fun cell =>
              (contributionLimit cell - target * weightLimit cell) ^ 2)
            massLimit)) :=
  tendsto_actualBootstrapVariance_of_cell_contribution_weight_limits_l1BracketingNumber_obligations_and_error_stability
    (Bracket := Bracket) cells sample score contribution weight target
    denominator normalizer cellContribution cellWeight contributionLimit
    weightLimit massLimit actualVariance scoreReplicationError
    biasCorrectionError herror_decomp hcover hcontributionCell hweightCell
    hcontributionLimit hweightLimit obligations
    (bootstrapScoreReplicationErrorNegligible_of_finite_component_bounds
      (l := atTop) scoreComponents scoreReplicationError
      scoreErrorComponent scoreErrorComponentBound hscore_decomp
      hscore_component_bound hscore_component_bound_tendsto)
    (bootstrapBiasCorrectionErrorNegligible_of_finite_component_bounds
      (l := atTop) biasComponents biasCorrectionError biasErrorComponent
      biasErrorComponentBound hbias_decomp hbias_component_bound
      hbias_component_bound_tendsto)

/--
VdV&W endpoint assemblies supply the score-cell mass LLN, and finite component
error bounds supply score-replication and bias-correction negligibility, for
the contribution/weight-limit actual bootstrap variance route.
-/
theorem
    tendsto_actualBootstrapVariance_of_cell_contribution_weight_limits_vdvw241_endpoint_assembly_and_finite_error_bounds
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
    (scoreErrorComponent scoreErrorComponentBound :
      ℕ -> ScoreComponent -> Real)
    (biasErrorComponent biasErrorComponentBound :
      ℕ -> BiasComponent -> Real)
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
    (hscore_decomp :
      scoreReplicationError =ᶠ[atTop]
        (fun index => ∑ component ∈ scoreComponents,
          scoreErrorComponent index component))
    (hscore_component_bound :
      ∀ᶠ index in atTop,
        ∀ component, component ∈ scoreComponents ->
          |scoreErrorComponent index component| ≤
            scoreErrorComponentBound index component)
    (hscore_component_bound_tendsto :
      ∀ component, component ∈ scoreComponents ->
        Tendsto (fun index => scoreErrorComponentBound index component)
          atTop (nhds 0))
    (hbias_decomp :
      biasCorrectionError =ᶠ[atTop]
        (fun index => ∑ component ∈ biasComponents,
          biasErrorComponent index component))
    (hbias_component_bound :
      ∀ᶠ index in atTop,
        ∀ component, component ∈ biasComponents ->
          |biasErrorComponent index component| ≤
            biasErrorComponentBound index component)
    (hbias_component_bound_tendsto :
      ∀ component, component ∈ biasComponents ->
        Tendsto (fun index => biasErrorComponentBound index component)
          atTop (nhds 0)) :
    Tendsto actualVariance atTop
      (nhds
        ((1 / denominator ^ 2) * (1 / normalizer) *
          weightedScoreCellMomentLimit cells
            (fun cell =>
              (contributionLimit cell - target * weightLimit cell) ^ 2)
            massLimit)) :=
  tendsto_actualBootstrapVariance_of_cell_contribution_weight_limits_vdvw241_endpoint_assembly_and_error_stability
    (Bracket := Bracket) cells sample score contribution weight target
    denominator normalizer cellContribution cellWeight contributionLimit
    weightLimit massLimit actualVariance scoreReplicationError
    biasCorrectionError herror_decomp hcover hcontributionCell hweightCell
    hcontributionLimit hweightLimit assembly
    (bootstrapScoreReplicationErrorNegligible_of_finite_component_bounds
      (l := atTop) scoreComponents scoreReplicationError
      scoreErrorComponent scoreErrorComponentBound hscore_decomp
      hscore_component_bound hscore_component_bound_tendsto)
    (bootstrapBiasCorrectionErrorNegligible_of_finite_component_bounds
      (l := atTop) biasComponents biasCorrectionError biasErrorComponent
      biasErrorComponentBound hbias_decomp hbias_component_bound
      hbias_component_bound_tendsto)

/--
Eventual score-cell representation version with finite-component score/bias
error bounds.
-/
theorem tendsto_actualBootstrapVariance_of_eventually_cell_contribution_weight_limits_and_finite_error_bounds
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
  tendsto_actualBootstrapVariance_of_eventually_cell_contribution_weight_limits_and_error_stability
    (l := l) cells sample score contribution weight target denominator
    normalizer cellContribution cellWeight contributionLimit weightLimit
    massLimit actualVariance scoreReplicationError biasCorrectionError
    herror_decomp hcover hcontributionCell hweightCell hcontributionLimit
    hweightLimit hmass
    (bootstrapScoreReplicationErrorNegligible_of_finite_component_bounds
      (l := l) scoreComponents scoreReplicationError scoreErrorComponent
      scoreErrorComponentBound hscore_decomp hscore_component_bound
      hscore_component_bound_tendsto)
    (bootstrapBiasCorrectionErrorNegligible_of_finite_component_bounds
      (l := l) biasComponents biasCorrectionError biasErrorComponent
      biasErrorComponentBound hbias_decomp hbias_component_bound
      hbias_component_bound_tendsto)

/--
Actual bootstrap variance convergence from eventual score-cell contribution
and denominator-weight representations when the score-replication and
bias-correction errors decompose into finite score-cell-by-component sums.

This is the actual-bootstrap consumer for the finite score-cell error
decomposition: the double finite sums are reindexed as product components and
then passed to the existing finite-error actual-variance adapter.
-/
theorem tendsto_actualBootstrapVariance_of_eventually_cell_contribution_weight_limits_and_finite_score_cell_error_bounds
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
      Index -> Cell -> ScoreComponent -> Real)
    (biasErrorComponent biasErrorComponentBound :
      Index -> Cell -> BiasComponent -> Real)
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
              scoreErrorComponentBound index cell component)
    (hscore_component_bound_tendsto :
      ∀ cell, cell ∈ cells ->
        ∀ component, component ∈ scoreComponents ->
          Tendsto
            (fun index => scoreErrorComponentBound index cell component)
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
              biasErrorComponentBound index cell component)
    (hbias_component_bound_tendsto :
      ∀ cell, cell ∈ cells ->
        ∀ component, component ∈ biasComponents ->
          Tendsto
            (fun index => biasErrorComponentBound index cell component)
            l (nhds 0)) :
    Tendsto actualVariance l
      (nhds
        ((1 / denominator ^ 2) * (1 / normalizer) *
          weightedScoreCellMomentLimit cells
            (fun cell =>
              (contributionLimit cell - target * weightLimit cell) ^ 2)
            massLimit)) := by
  have hscore_decomp_product :
      scoreReplicationError =ᶠ[l]
        (fun index => ∑ pair ∈ cells.product scoreComponents,
          scoreErrorComponent index pair.1 pair.2) := by
    filter_upwards [hscore_decomp] with index hdecomp_index
    calc
      scoreReplicationError index =
          ∑ cell ∈ cells, ∑ component ∈ scoreComponents,
            scoreErrorComponent index cell component := hdecomp_index
      _ = ∑ pair ∈ cells.product scoreComponents,
            scoreErrorComponent index pair.1 pair.2 := by
          rw [← Finset.sum_product']
          rfl
  have hscore_component_bound_product :
      ∀ᶠ index in l,
        ∀ pair, pair ∈ cells.product scoreComponents ->
          |scoreErrorComponent index pair.1 pair.2| ≤
            scoreErrorComponentBound index pair.1 pair.2 := by
    filter_upwards [hscore_component_bound] with index hbound pair hpair
    rcases Finset.mem_product.mp hpair with ⟨hcell, hcomponent⟩
    exact hbound pair.1 hcell pair.2 hcomponent
  have hbias_decomp_product :
      biasCorrectionError =ᶠ[l]
        (fun index => ∑ pair ∈ cells.product biasComponents,
          biasErrorComponent index pair.1 pair.2) := by
    filter_upwards [hbias_decomp] with index hdecomp_index
    calc
      biasCorrectionError index =
          ∑ cell ∈ cells, ∑ component ∈ biasComponents,
            biasErrorComponent index cell component := hdecomp_index
      _ = ∑ pair ∈ cells.product biasComponents,
            biasErrorComponent index pair.1 pair.2 := by
          rw [← Finset.sum_product']
          rfl
  have hbias_component_bound_product :
      ∀ᶠ index in l,
        ∀ pair, pair ∈ cells.product biasComponents ->
          |biasErrorComponent index pair.1 pair.2| ≤
            biasErrorComponentBound index pair.1 pair.2 := by
    filter_upwards [hbias_component_bound] with index hbound pair hpair
    rcases Finset.mem_product.mp hpair with ⟨hcell, hcomponent⟩
    exact hbound pair.1 hcell pair.2 hcomponent
  exact
    tendsto_actualBootstrapVariance_of_eventually_cell_contribution_weight_limits_and_finite_error_bounds
      (l := l) cells (cells.product scoreComponents)
      (cells.product biasComponents) sample score contribution weight target
      denominator normalizer cellContribution cellWeight contributionLimit
      weightLimit massLimit actualVariance scoreReplicationError
      biasCorrectionError
      (fun index pair => scoreErrorComponent index pair.1 pair.2)
      (fun index pair => scoreErrorComponentBound index pair.1 pair.2)
      (fun index pair => biasErrorComponent index pair.1 pair.2)
      (fun index pair => biasErrorComponentBound index pair.1 pair.2)
      herror_decomp hcover hcontributionCell hweightCell hcontributionLimit
      hweightLimit hmass hscore_decomp_product
      hscore_component_bound_product
      (fun pair hpair => by
        rcases Finset.mem_product.mp hpair with ⟨hcell, hcomponent⟩
        exact hscore_component_bound_tendsto pair.1 hcell pair.2 hcomponent)
      hbias_decomp_product hbias_component_bound_product
      (fun pair hpair => by
        rcases Finset.mem_product.mp hpair with ⟨hcell, hcomponent⟩
        exact hbias_component_bound_tendsto pair.1 hcell pair.2 hcomponent)

/--
Actual bootstrap variance convergence when both score-replication and
bias-correction errors are constructed from the concrete multinomial
draw-count replicate and then bounded cell-componentwise.
-/
theorem tendsto_actualBootstrapVariance_of_eventually_cell_contribution_weight_limits_and_multinomial_draw_score_cell_error_bounds
    [DecidableEq Cell] [DecidableEq ScoreComponent]
    [DecidableEq BiasComponent]
    (cells : Finset Cell)
    (scoreComponents : Finset ScoreComponent)
    (biasComponents : Finset BiasComponent)
    (sample : Index -> Finset Unit) (draws : Index -> Finset Draw)
    (drawIndicator : Index -> Omega -> Draw -> Unit -> Real)
    (omega : Index -> Omega)
    (score : Index -> Unit -> Cell)
    (contribution weight : Index -> Unit -> Real)
    (target denominator normalizer : Real)
    (cellContribution cellWeight : Index -> Cell -> Real)
    (contributionLimit weightLimit massLimit : Cell -> Real)
    (actualVariance scoreReplicationError biasCorrectionError : Index -> Real)
    (scoreUnitComponent : Index -> Unit -> ScoreComponent -> Real)
    (biasUnitComponent : Index -> Unit -> BiasComponent -> Real)
    (scoreErrorComponentBound : Index -> Cell -> ScoreComponent -> Real)
    (biasErrorComponentBound : Index -> Cell -> BiasComponent -> Real)
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
    (hscore_construct :
      scoreReplicationError =ᶠ[l]
        (fun index =>
          ∑ component ∈ scoreComponents, ∑ unit ∈ sample index,
            (multinomialCountFromDrawIndicators (draws index)
                (drawIndicator index) (omega index) unit - 1) *
              scoreUnitComponent index unit component))
    (hscore_component_bound :
      ∀ᶠ index in l,
        ∀ cell, cell ∈ cells ->
          ∀ component, component ∈ scoreComponents ->
            |multinomialDrawScoreCellErrorComponent (sample index)
                (draws index) (drawIndicator index) (omega index)
                (score index) (scoreUnitComponent index) cell component| ≤
              scoreErrorComponentBound index cell component)
    (hscore_component_bound_tendsto :
      ∀ cell, cell ∈ cells ->
        ∀ component, component ∈ scoreComponents ->
          Tendsto
            (fun index => scoreErrorComponentBound index cell component)
            l (nhds 0))
    (hbias_construct :
      biasCorrectionError =ᶠ[l]
        (fun index =>
          ∑ component ∈ biasComponents, ∑ unit ∈ sample index,
            (multinomialCountFromDrawIndicators (draws index)
                (drawIndicator index) (omega index) unit - 1) *
              biasUnitComponent index unit component))
    (hbias_component_bound :
      ∀ᶠ index in l,
        ∀ cell, cell ∈ cells ->
          ∀ component, component ∈ biasComponents ->
            |multinomialDrawScoreCellErrorComponent (sample index)
                (draws index) (drawIndicator index) (omega index)
                (score index) (biasUnitComponent index) cell component| ≤
              biasErrorComponentBound index cell component)
    (hbias_component_bound_tendsto :
      ∀ cell, cell ∈ cells ->
        ∀ component, component ∈ biasComponents ->
          Tendsto
            (fun index => biasErrorComponentBound index cell component)
            l (nhds 0)) :
    Tendsto actualVariance l
      (nhds
        ((1 / denominator ^ 2) * (1 / normalizer) *
          weightedScoreCellMomentLimit cells
            (fun cell =>
              (contributionLimit cell - target * weightLimit cell) ^ 2)
            massLimit)) :=
  tendsto_actualBootstrapVariance_of_eventually_cell_contribution_weight_limits_and_finite_score_cell_error_bounds
    (l := l) cells scoreComponents biasComponents sample score contribution
    weight target denominator normalizer cellContribution cellWeight
    contributionLimit weightLimit massLimit actualVariance
    scoreReplicationError biasCorrectionError
    (fun index cell component =>
      multinomialDrawScoreCellErrorComponent (sample index) (draws index)
        (drawIndicator index) (omega index) (score index)
        (scoreUnitComponent index) cell component)
    scoreErrorComponentBound
    (fun index cell component =>
      multinomialDrawScoreCellErrorComponent (sample index) (draws index)
        (drawIndicator index) (omega index) (score index)
        (biasUnitComponent index) cell component)
    biasErrorComponentBound herror_decomp hcover hcontributionCell
    hweightCell hcontributionLimit hweightLimit hmass
    (eventually_actualBootstrapScoreReplicationError_eq_finite_score_cell_components_of_multinomial_draw_replicate
      (l := l) cells scoreComponents sample draws drawIndicator omega score
      scoreUnitComponent scoreReplicationError hscore_construct hcover)
    hscore_component_bound hscore_component_bound_tendsto
    (eventually_actualBootstrapBiasCorrectionError_eq_finite_score_cell_components_of_multinomial_draw_replicate
      (l := l) cells biasComponents sample draws drawIndicator omega score
      biasUnitComponent biasCorrectionError hbias_construct hcover)
    hbias_component_bound hbias_component_bound_tendsto

/--
Actual bootstrap variance convergence from concrete multinomial draw-count
score/bias error constructions and unit-level centered-count bounds.  The only
remaining bound convergence inputs are the induced finite score-cell sums of
those unit-level bounds.
-/
theorem tendsto_actualBootstrapVariance_of_eventually_cell_contribution_weight_limits_and_multinomial_draw_unit_error_bounds
    [DecidableEq Cell] [DecidableEq ScoreComponent]
    [DecidableEq BiasComponent]
    (cells : Finset Cell)
    (scoreComponents : Finset ScoreComponent)
    (biasComponents : Finset BiasComponent)
    (sample : Index -> Finset Unit) (draws : Index -> Finset Draw)
    (drawIndicator : Index -> Omega -> Draw -> Unit -> Real)
    (omega : Index -> Omega)
    (score : Index -> Unit -> Cell)
    (contribution weight : Index -> Unit -> Real)
    (target denominator normalizer : Real)
    (cellContribution cellWeight : Index -> Cell -> Real)
    (contributionLimit weightLimit massLimit : Cell -> Real)
    (actualVariance scoreReplicationError biasCorrectionError : Index -> Real)
    (scoreUnitComponent scoreUnitComponentBound :
      Index -> Unit -> ScoreComponent -> Real)
    (biasUnitComponent biasUnitComponentBound :
      Index -> Unit -> BiasComponent -> Real)
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
    (hscore_construct :
      scoreReplicationError =ᶠ[l]
        (fun index =>
          ∑ component ∈ scoreComponents, ∑ unit ∈ sample index,
            (multinomialCountFromDrawIndicators (draws index)
                (drawIndicator index) (omega index) unit - 1) *
              scoreUnitComponent index unit component))
    (hscore_unit_bound :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ sample index ->
          ∀ component, component ∈ scoreComponents ->
            |(multinomialCountFromDrawIndicators (draws index)
                (drawIndicator index) (omega index) unit - 1) *
              scoreUnitComponent index unit component| ≤
              scoreUnitComponentBound index unit component)
    (hscore_cell_bound_tendsto :
      ∀ cell, cell ∈ cells ->
        ∀ component, component ∈ scoreComponents ->
          Tendsto
            (fun index =>
              ∑ unit ∈ sample index,
                scoreCellIndicator (score index) cell unit *
                  scoreUnitComponentBound index unit component)
            l (nhds 0))
    (hbias_construct :
      biasCorrectionError =ᶠ[l]
        (fun index =>
          ∑ component ∈ biasComponents, ∑ unit ∈ sample index,
            (multinomialCountFromDrawIndicators (draws index)
                (drawIndicator index) (omega index) unit - 1) *
              biasUnitComponent index unit component))
    (hbias_unit_bound :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ sample index ->
          ∀ component, component ∈ biasComponents ->
            |(multinomialCountFromDrawIndicators (draws index)
                (drawIndicator index) (omega index) unit - 1) *
              biasUnitComponent index unit component| ≤
              biasUnitComponentBound index unit component)
    (hbias_cell_bound_tendsto :
      ∀ cell, cell ∈ cells ->
        ∀ component, component ∈ biasComponents ->
          Tendsto
            (fun index =>
              ∑ unit ∈ sample index,
                scoreCellIndicator (score index) cell unit *
                  biasUnitComponentBound index unit component)
            l (nhds 0)) :
    Tendsto actualVariance l
      (nhds
        ((1 / denominator ^ 2) * (1 / normalizer) *
          weightedScoreCellMomentLimit cells
            (fun cell =>
              (contributionLimit cell - target * weightLimit cell) ^ 2)
            massLimit)) :=
  tendsto_actualBootstrapVariance_of_eventually_cell_contribution_weight_limits_and_multinomial_draw_score_cell_error_bounds
    (l := l) cells scoreComponents biasComponents sample draws
    drawIndicator omega score contribution weight target denominator
    normalizer cellContribution cellWeight contributionLimit weightLimit
    massLimit actualVariance scoreReplicationError biasCorrectionError
    scoreUnitComponent biasUnitComponent
    (fun index cell component =>
      ∑ unit ∈ sample index,
        scoreCellIndicator (score index) cell unit *
          scoreUnitComponentBound index unit component)
    (fun index cell component =>
      ∑ unit ∈ sample index,
        scoreCellIndicator (score index) cell unit *
          biasUnitComponentBound index unit component)
    herror_decomp hcover hcontributionCell hweightCell hcontributionLimit
    hweightLimit hmass hscore_construct
    (eventually_abs_multinomialDrawScoreCellErrorComponent_le_indicator_unit_bounds
      (l := l) cells scoreComponents sample draws drawIndicator omega score
      scoreUnitComponent scoreUnitComponentBound hscore_unit_bound)
    hscore_cell_bound_tendsto hbias_construct
    (eventually_abs_multinomialDrawScoreCellErrorComponent_le_indicator_unit_bounds
      (l := l) cells biasComponents sample draws drawIndicator omega score
      biasUnitComponent biasUnitComponentBound hbias_unit_bound)
    hbias_cell_bound_tendsto

/--
If a unit-level bound is constant across units inside each component and its
component envelope tends to zero, then its score-cell indicator-weighted sum
also tends to zero under the existing cell-mass LLN.
-/
theorem tendsto_scoreCellIndicator_unit_envelope_sum_zero_of_cellwise_mass
    [DecidableEq Cell]
    {Component : Type*}
    (cells : Finset Cell)
    (components : Finset Component)
    (sample : Index -> Finset Unit)
    (score : Index -> Unit -> Cell)
    (massLimit : Cell -> Real)
    (componentEnvelope : Index -> Component -> Real)
    (hmass :
      cellwiseScoreCellMassLLN (l := l) cells sample
        (fun _index _unit => 1) score massLimit)
    (henvelope :
      ∀ component, component ∈ components ->
        Tendsto (fun index => componentEnvelope index component)
          l (nhds 0)) :
    ∀ cell, cell ∈ cells ->
      ∀ component, component ∈ components ->
        Tendsto
          (fun index =>
            ∑ unit ∈ sample index,
              scoreCellIndicator (score index) cell unit *
                componentEnvelope index component)
          l (nhds 0) := by
  intro cell hcell component hcomponent
  have hindicator :
      Tendsto
        (fun index =>
          weightedSampleSum (sample index) (fun _unit => (1 : Real))
            (scoreCellIndicator (score index) cell))
        l (nhds (massLimit cell)) :=
    cellwiseWeightedIndicatorSumLLN_of_mass
      (l := l) cells sample (fun _index _unit => (1 : Real)) score
      massLimit hmass cell hcell
  have hproduct :
      Tendsto
        (fun index =>
          weightedSampleSum (sample index) (fun _unit => (1 : Real))
            (scoreCellIndicator (score index) cell) *
            componentEnvelope index component)
        l (nhds 0) :=
    by simpa using hindicator.mul (henvelope component hcomponent)
  convert hproduct using 1
  ext index
  unfold weightedSampleSum
  calc
    (∑ unit ∈ sample index,
        scoreCellIndicator (score index) cell unit *
          componentEnvelope index component) =
        (∑ unit ∈ sample index,
          scoreCellIndicator (score index) cell unit) *
          componentEnvelope index component := by
          rw [Finset.sum_mul]
    _ =
        (∑ unit ∈ sample index,
          (fun _unit => (1 : Real)) unit *
            scoreCellIndicator (score index) cell unit) *
          componentEnvelope index component := by
          congr 1
          exact Finset.sum_congr rfl (fun unit _hunit => by ring)

/--
Actual bootstrap variance convergence from concrete multinomial draw-count
score/bias error constructions and component envelopes for the unit-level
centered-count bounds.  The indicator-weighted cell-bound convergence is
derived from the existing cell-mass LLN.
-/
theorem tendsto_actualBootstrapVariance_of_eventually_cell_contribution_weight_limits_and_multinomial_draw_unit_envelope_bounds
    [DecidableEq Cell] [DecidableEq ScoreComponent]
    [DecidableEq BiasComponent]
    (cells : Finset Cell)
    (scoreComponents : Finset ScoreComponent)
    (biasComponents : Finset BiasComponent)
    (sample : Index -> Finset Unit) (draws : Index -> Finset Draw)
    (drawIndicator : Index -> Omega -> Draw -> Unit -> Real)
    (omega : Index -> Omega)
    (score : Index -> Unit -> Cell)
    (contribution weight : Index -> Unit -> Real)
    (target denominator normalizer : Real)
    (cellContribution cellWeight : Index -> Cell -> Real)
    (contributionLimit weightLimit massLimit : Cell -> Real)
    (actualVariance scoreReplicationError biasCorrectionError : Index -> Real)
    (scoreUnitComponent : Index -> Unit -> ScoreComponent -> Real)
    (biasUnitComponent : Index -> Unit -> BiasComponent -> Real)
    (scoreUnitEnvelope : Index -> ScoreComponent -> Real)
    (biasUnitEnvelope : Index -> BiasComponent -> Real)
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
    (hscore_construct :
      scoreReplicationError =ᶠ[l]
        (fun index =>
          ∑ component ∈ scoreComponents, ∑ unit ∈ sample index,
            (multinomialCountFromDrawIndicators (draws index)
                (drawIndicator index) (omega index) unit - 1) *
              scoreUnitComponent index unit component))
    (hscore_unit_bound :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ sample index ->
          ∀ component, component ∈ scoreComponents ->
            |(multinomialCountFromDrawIndicators (draws index)
                (drawIndicator index) (omega index) unit - 1) *
              scoreUnitComponent index unit component| ≤
              scoreUnitEnvelope index component)
    (hscore_envelope_tendsto :
      ∀ component, component ∈ scoreComponents ->
        Tendsto (fun index => scoreUnitEnvelope index component)
          l (nhds 0))
    (hbias_construct :
      biasCorrectionError =ᶠ[l]
        (fun index =>
          ∑ component ∈ biasComponents, ∑ unit ∈ sample index,
            (multinomialCountFromDrawIndicators (draws index)
                (drawIndicator index) (omega index) unit - 1) *
              biasUnitComponent index unit component))
    (hbias_unit_bound :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ sample index ->
          ∀ component, component ∈ biasComponents ->
            |(multinomialCountFromDrawIndicators (draws index)
                (drawIndicator index) (omega index) unit - 1) *
              biasUnitComponent index unit component| ≤
              biasUnitEnvelope index component)
    (hbias_envelope_tendsto :
      ∀ component, component ∈ biasComponents ->
        Tendsto (fun index => biasUnitEnvelope index component)
          l (nhds 0)) :
    Tendsto actualVariance l
      (nhds
        ((1 / denominator ^ 2) * (1 / normalizer) *
          weightedScoreCellMomentLimit cells
            (fun cell =>
              (contributionLimit cell - target * weightLimit cell) ^ 2)
            massLimit)) :=
  tendsto_actualBootstrapVariance_of_eventually_cell_contribution_weight_limits_and_multinomial_draw_unit_error_bounds
    (l := l) cells scoreComponents biasComponents sample draws
    drawIndicator omega score contribution weight target denominator
    normalizer cellContribution cellWeight contributionLimit weightLimit
    massLimit actualVariance scoreReplicationError biasCorrectionError
    scoreUnitComponent
    (fun index _unit component => scoreUnitEnvelope index component)
    biasUnitComponent
    (fun index _unit component => biasUnitEnvelope index component)
    herror_decomp hcover hcontributionCell hweightCell hcontributionLimit
    hweightLimit hmass hscore_construct hscore_unit_bound
    (tendsto_scoreCellIndicator_unit_envelope_sum_zero_of_cellwise_mass
      (l := l) cells scoreComponents sample score massLimit
      scoreUnitEnvelope hmass hscore_envelope_tendsto)
    hbias_construct hbias_unit_bound
    (tendsto_scoreCellIndicator_unit_envelope_sum_zero_of_cellwise_mass
      (l := l) cells biasComponents sample score massLimit
      biasUnitEnvelope hmass hbias_envelope_tendsto)

/--
Actual bootstrap variance convergence from concrete multinomial draw-count
score/bias error constructions, a centered-count envelope with a finite
limit, and shrinking envelopes for the unit-level score/bias components.
-/
theorem tendsto_actualBootstrapVariance_of_eventually_cell_contribution_weight_limits_and_multinomial_draw_count_component_envelope_bounds
    [DecidableEq Cell] [DecidableEq ScoreComponent]
    [DecidableEq BiasComponent]
    (cells : Finset Cell)
    (scoreComponents : Finset ScoreComponent)
    (biasComponents : Finset BiasComponent)
    (sample : Index -> Finset Unit) (draws : Index -> Finset Draw)
    (drawIndicator : Index -> Omega -> Draw -> Unit -> Real)
    (omega : Index -> Omega)
    (score : Index -> Unit -> Cell)
    (contribution weight : Index -> Unit -> Real)
    (target denominator normalizer : Real)
    (cellContribution cellWeight : Index -> Cell -> Real)
    (contributionLimit weightLimit massLimit : Cell -> Real)
    (actualVariance scoreReplicationError biasCorrectionError : Index -> Real)
    (scoreUnitComponent : Index -> Unit -> ScoreComponent -> Real)
    (biasUnitComponent : Index -> Unit -> BiasComponent -> Real)
    (countEnvelope : Index -> Real) (countEnvelopeLimit : Real)
    (scoreUnitEnvelope : Index -> ScoreComponent -> Real)
    (biasUnitEnvelope : Index -> BiasComponent -> Real)
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
    (hscore_construct :
      scoreReplicationError =ᶠ[l]
        (fun index =>
          ∑ component ∈ scoreComponents, ∑ unit ∈ sample index,
            (multinomialCountFromDrawIndicators (draws index)
                (drawIndicator index) (omega index) unit - 1) *
              scoreUnitComponent index unit component))
    (hcount_bound :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ sample index ->
          |multinomialCountFromDrawIndicators (draws index)
              (drawIndicator index) (omega index) unit - 1| ≤
            countEnvelope index)
    (hcount_tendsto :
      Tendsto countEnvelope l (nhds countEnvelopeLimit))
    (hscore_component_bound :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ sample index ->
          ∀ component, component ∈ scoreComponents ->
            |scoreUnitComponent index unit component| ≤
              scoreUnitEnvelope index component)
    (hscore_envelope_tendsto :
      ∀ component, component ∈ scoreComponents ->
        Tendsto (fun index => scoreUnitEnvelope index component)
          l (nhds 0))
    (hbias_construct :
      biasCorrectionError =ᶠ[l]
        (fun index =>
          ∑ component ∈ biasComponents, ∑ unit ∈ sample index,
            (multinomialCountFromDrawIndicators (draws index)
                (drawIndicator index) (omega index) unit - 1) *
              biasUnitComponent index unit component))
    (hbias_component_bound :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ sample index ->
          ∀ component, component ∈ biasComponents ->
            |biasUnitComponent index unit component| ≤
              biasUnitEnvelope index component)
    (hbias_envelope_tendsto :
      ∀ component, component ∈ biasComponents ->
        Tendsto (fun index => biasUnitEnvelope index component)
          l (nhds 0)) :
    Tendsto actualVariance l
      (nhds
        ((1 / denominator ^ 2) * (1 / normalizer) *
          weightedScoreCellMomentLimit cells
            (fun cell =>
              (contributionLimit cell - target * weightLimit cell) ^ 2)
            massLimit)) :=
  tendsto_actualBootstrapVariance_of_eventually_cell_contribution_weight_limits_and_multinomial_draw_unit_envelope_bounds
    (l := l) cells scoreComponents biasComponents sample draws
    drawIndicator omega score contribution weight target denominator
    normalizer cellContribution cellWeight contributionLimit weightLimit
    massLimit actualVariance scoreReplicationError biasCorrectionError
    scoreUnitComponent biasUnitComponent
    (fun index component =>
      countEnvelope index * scoreUnitEnvelope index component)
    (fun index component =>
      countEnvelope index * biasUnitEnvelope index component)
    herror_decomp hcover hcontributionCell hweightCell hcontributionLimit
    hweightLimit hmass hscore_construct
    (eventually_abs_centered_multinomial_count_mul_unitComponent_le_count_mul_component_envelope
      (l := l) scoreComponents sample draws drawIndicator omega
      scoreUnitComponent countEnvelope scoreUnitEnvelope hcount_bound
      hscore_component_bound)
    (fun component hcomponent => by
      simpa using
        hcount_tendsto.mul (hscore_envelope_tendsto component hcomponent))
    hbias_construct
    (eventually_abs_centered_multinomial_count_mul_unitComponent_le_count_mul_component_envelope
      (l := l) biasComponents sample draws drawIndicator omega
      biasUnitComponent countEnvelope biasUnitEnvelope hcount_bound
      hbias_component_bound)
    (fun component hcomponent => by
      simpa using
        hcount_tendsto.mul (hbias_envelope_tendsto component hcomponent))

/--
Actual bootstrap variance convergence from the concrete finite draw-count
bound `|m_i^* - 1| <= #draws + 1` and shrinking unit-component envelopes fast
enough that the draw-cardinality-scaled envelopes vanish.
-/
theorem tendsto_actualBootstrapVariance_of_eventually_cell_contribution_weight_limits_and_multinomial_draw_card_component_product_bounds
    [DecidableEq Cell] [DecidableEq ScoreComponent]
    [DecidableEq BiasComponent]
    (cells : Finset Cell)
    (scoreComponents : Finset ScoreComponent)
    (biasComponents : Finset BiasComponent)
    (sample : Index -> Finset Unit) (draws : Index -> Finset Draw)
    (drawIndicator : Index -> Omega -> Draw -> Unit -> Real)
    (omega : Index -> Omega)
    (score : Index -> Unit -> Cell)
    (contribution weight : Index -> Unit -> Real)
    (target denominator normalizer : Real)
    (cellContribution cellWeight : Index -> Cell -> Real)
    (contributionLimit weightLimit massLimit : Cell -> Real)
    (actualVariance scoreReplicationError biasCorrectionError : Index -> Real)
    (scoreUnitComponent : Index -> Unit -> ScoreComponent -> Real)
    (biasUnitComponent : Index -> Unit -> BiasComponent -> Real)
    (scoreUnitEnvelope : Index -> ScoreComponent -> Real)
    (biasUnitEnvelope : Index -> BiasComponent -> Real)
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
    (hscore_construct :
      scoreReplicationError =ᶠ[l]
        (fun index =>
          ∑ component ∈ scoreComponents, ∑ unit ∈ sample index,
            (multinomialCountFromDrawIndicators (draws index)
                (drawIndicator index) (omega index) unit - 1) *
              scoreUnitComponent index unit component))
    (hdraw_bound :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ sample index ->
          ∀ draw, draw ∈ draws index ->
            |drawIndicator index (omega index) draw unit| ≤ 1)
    (hscore_component_bound :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ sample index ->
          ∀ component, component ∈ scoreComponents ->
            |scoreUnitComponent index unit component| ≤
              scoreUnitEnvelope index component)
    (hscore_scaled_envelope_tendsto :
      ∀ component, component ∈ scoreComponents ->
        Tendsto
          (fun index =>
            (((draws index).card : Real) + 1) *
              scoreUnitEnvelope index component)
          l (nhds 0))
    (hbias_construct :
      biasCorrectionError =ᶠ[l]
        (fun index =>
          ∑ component ∈ biasComponents, ∑ unit ∈ sample index,
            (multinomialCountFromDrawIndicators (draws index)
                (drawIndicator index) (omega index) unit - 1) *
              biasUnitComponent index unit component))
    (hbias_component_bound :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ sample index ->
          ∀ component, component ∈ biasComponents ->
            |biasUnitComponent index unit component| ≤
              biasUnitEnvelope index component)
    (hbias_scaled_envelope_tendsto :
      ∀ component, component ∈ biasComponents ->
        Tendsto
          (fun index =>
            (((draws index).card : Real) + 1) *
              biasUnitEnvelope index component)
          l (nhds 0)) :
    Tendsto actualVariance l
      (nhds
        ((1 / denominator ^ 2) * (1 / normalizer) *
          weightedScoreCellMomentLimit cells
            (fun cell =>
              (contributionLimit cell - target * weightLimit cell) ^ 2)
            massLimit)) :=
  tendsto_actualBootstrapVariance_of_eventually_cell_contribution_weight_limits_and_multinomial_draw_unit_envelope_bounds
    (l := l) cells scoreComponents biasComponents sample draws
    drawIndicator omega score contribution weight target denominator
    normalizer cellContribution cellWeight contributionLimit weightLimit
    massLimit actualVariance scoreReplicationError biasCorrectionError
    scoreUnitComponent biasUnitComponent
    (fun index component =>
      (((draws index).card : Real) + 1) *
        scoreUnitEnvelope index component)
    (fun index component =>
      (((draws index).card : Real) + 1) *
        biasUnitEnvelope index component)
    herror_decomp hcover hcontributionCell hweightCell hcontributionLimit
    hweightLimit hmass hscore_construct
    (eventually_abs_centered_multinomial_count_mul_unitComponent_le_count_mul_component_envelope
      (l := l) scoreComponents sample draws drawIndicator omega
      scoreUnitComponent
      (fun index => ((draws index).card : Real) + 1)
      scoreUnitEnvelope
      (eventually_abs_multinomialCountFromDrawIndicators_sub_one_le_draw_card_add_one
        (l := l) sample draws drawIndicator omega hdraw_bound)
      hscore_component_bound)
    hscore_scaled_envelope_tendsto hbias_construct
    (eventually_abs_centered_multinomial_count_mul_unitComponent_le_count_mul_component_envelope
      (l := l) biasComponents sample draws drawIndicator omega
      biasUnitComponent
      (fun index => ((draws index).card : Real) + 1)
      biasUnitEnvelope
      (eventually_abs_multinomialCountFromDrawIndicators_sub_one_le_draw_card_add_one
        (l := l) sample draws drawIndicator omega hdraw_bound)
      hbias_component_bound)
    hbias_scaled_envelope_tendsto

/--
Uniform-assignment specialization of the finite draw-cardinality route.  The
one-hot draw-indicator absolute bound is discharged by the concrete
`oneHotAssignmentIndicator` definition.
-/
theorem tendsto_actualBootstrapVariance_of_eventually_cell_contribution_weight_limits_and_uniformAssignment_draw_card_component_product_bounds
    [DecidableEq Unit] [DecidableEq Cell] [DecidableEq ScoreComponent]
    [DecidableEq BiasComponent]
    (cells : Finset Cell)
    (scoreComponents : Finset ScoreComponent)
    (biasComponents : Finset BiasComponent)
    (sample : Index -> Finset Unit) (draws : Index -> Finset Draw)
    (assignment : Index -> Draw -> Unit)
    (score : Index -> Unit -> Cell)
    (contribution weight : Index -> Unit -> Real)
    (target denominator normalizer : Real)
    (cellContribution cellWeight : Index -> Cell -> Real)
    (contributionLimit weightLimit massLimit : Cell -> Real)
    (actualVariance scoreReplicationError biasCorrectionError : Index -> Real)
    (scoreUnitComponent : Index -> Unit -> ScoreComponent -> Real)
    (biasUnitComponent : Index -> Unit -> BiasComponent -> Real)
    (scoreUnitEnvelope : Index -> ScoreComponent -> Real)
    (biasUnitEnvelope : Index -> BiasComponent -> Real)
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
    (hscore_construct :
      scoreReplicationError =ᶠ[l]
        (fun index =>
          ∑ component ∈ scoreComponents, ∑ unit ∈ sample index,
            (multinomialCountFromDrawIndicators (draws index)
                (fun assignment draw unit =>
                  oneHotAssignmentIndicator assignment draw unit)
                (assignment index) unit - 1) *
              scoreUnitComponent index unit component))
    (hscore_component_bound :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ sample index ->
          ∀ component, component ∈ scoreComponents ->
            |scoreUnitComponent index unit component| ≤
              scoreUnitEnvelope index component)
    (hscore_scaled_envelope_tendsto :
      ∀ component, component ∈ scoreComponents ->
        Tendsto
          (fun index =>
            (((draws index).card : Real) + 1) *
              scoreUnitEnvelope index component)
          l (nhds 0))
    (hbias_construct :
      biasCorrectionError =ᶠ[l]
        (fun index =>
          ∑ component ∈ biasComponents, ∑ unit ∈ sample index,
            (multinomialCountFromDrawIndicators (draws index)
                (fun assignment draw unit =>
                  oneHotAssignmentIndicator assignment draw unit)
                (assignment index) unit - 1) *
              biasUnitComponent index unit component))
    (hbias_component_bound :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ sample index ->
          ∀ component, component ∈ biasComponents ->
            |biasUnitComponent index unit component| ≤
              biasUnitEnvelope index component)
    (hbias_scaled_envelope_tendsto :
      ∀ component, component ∈ biasComponents ->
        Tendsto
          (fun index =>
            (((draws index).card : Real) + 1) *
              biasUnitEnvelope index component)
          l (nhds 0)) :
    Tendsto actualVariance l
      (nhds
        ((1 / denominator ^ 2) * (1 / normalizer) *
          weightedScoreCellMomentLimit cells
            (fun cell =>
              (contributionLimit cell - target * weightLimit cell) ^ 2)
            massLimit)) :=
  tendsto_actualBootstrapVariance_of_eventually_cell_contribution_weight_limits_and_multinomial_draw_card_component_product_bounds
    (l := l) cells scoreComponents biasComponents sample draws
    (fun _index assignment draw unit =>
      oneHotAssignmentIndicator assignment draw unit)
    assignment score contribution weight target denominator normalizer
    cellContribution cellWeight contributionLimit weightLimit massLimit
    actualVariance scoreReplicationError biasCorrectionError
    scoreUnitComponent biasUnitComponent scoreUnitEnvelope biasUnitEnvelope
    herror_decomp hcover hcontributionCell hweightCell hcontributionLimit
    hweightLimit hmass hscore_construct
    (eventually_abs_oneHotAssignmentIndicator_le_one
      (l := l) sample draws assignment)
    hscore_component_bound hscore_scaled_envelope_tendsto hbias_construct
    hbias_component_bound hbias_scaled_envelope_tendsto

/--
Uniform-assignment route with an explicit draw-count scale.  This is the
form expected by the paper when the bootstrap convention proves the number of
draw slots is eventually a named scale, such as the sample size.
-/
theorem tendsto_actualBootstrapVariance_of_eventually_cell_contribution_weight_limits_and_uniformAssignment_draw_count_scale_component_product_bounds
    [DecidableEq Unit] [DecidableEq Cell] [DecidableEq ScoreComponent]
    [DecidableEq BiasComponent]
    (cells : Finset Cell)
    (scoreComponents : Finset ScoreComponent)
    (biasComponents : Finset BiasComponent)
    (sample : Index -> Finset Unit) (draws : Index -> Finset Draw)
    (drawCount : Index -> Real)
    (assignment : Index -> Draw -> Unit)
    (score : Index -> Unit -> Cell)
    (contribution weight : Index -> Unit -> Real)
    (target denominator normalizer : Real)
    (cellContribution cellWeight : Index -> Cell -> Real)
    (contributionLimit weightLimit massLimit : Cell -> Real)
    (actualVariance scoreReplicationError biasCorrectionError : Index -> Real)
    (scoreUnitComponent : Index -> Unit -> ScoreComponent -> Real)
    (biasUnitComponent : Index -> Unit -> BiasComponent -> Real)
    (scoreUnitEnvelope : Index -> ScoreComponent -> Real)
    (biasUnitEnvelope : Index -> BiasComponent -> Real)
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
    (hdrawCount :
      ∀ᶠ index in l,
        ((draws index).card : Real) = drawCount index)
    (hscore_construct :
      scoreReplicationError =ᶠ[l]
        (fun index =>
          ∑ component ∈ scoreComponents, ∑ unit ∈ sample index,
            (multinomialCountFromDrawIndicators (draws index)
                (fun assignment draw unit =>
                  oneHotAssignmentIndicator assignment draw unit)
                (assignment index) unit - 1) *
              scoreUnitComponent index unit component))
    (hscore_component_bound :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ sample index ->
          ∀ component, component ∈ scoreComponents ->
            |scoreUnitComponent index unit component| ≤
              scoreUnitEnvelope index component)
    (hscore_scaled_envelope_tendsto :
      ∀ component, component ∈ scoreComponents ->
        Tendsto
          (fun index =>
            (drawCount index + 1) *
              scoreUnitEnvelope index component)
          l (nhds 0))
    (hbias_construct :
      biasCorrectionError =ᶠ[l]
        (fun index =>
          ∑ component ∈ biasComponents, ∑ unit ∈ sample index,
            (multinomialCountFromDrawIndicators (draws index)
                (fun assignment draw unit =>
                  oneHotAssignmentIndicator assignment draw unit)
                (assignment index) unit - 1) *
              biasUnitComponent index unit component))
    (hbias_component_bound :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ sample index ->
          ∀ component, component ∈ biasComponents ->
            |biasUnitComponent index unit component| ≤
              biasUnitEnvelope index component)
    (hbias_scaled_envelope_tendsto :
      ∀ component, component ∈ biasComponents ->
        Tendsto
          (fun index =>
            (drawCount index + 1) *
              biasUnitEnvelope index component)
          l (nhds 0)) :
    Tendsto actualVariance l
      (nhds
        ((1 / denominator ^ 2) * (1 / normalizer) *
          weightedScoreCellMomentLimit cells
            (fun cell =>
              (contributionLimit cell - target * weightLimit cell) ^ 2)
            massLimit)) := by
  have hscore_scaled_card :
      ∀ component, component ∈ scoreComponents ->
        Tendsto
          (fun index =>
            (((draws index).card : Real) + 1) *
              scoreUnitEnvelope index component)
          l (nhds 0) := by
    intro component hcomponent
    have heq :
        (fun index =>
          (((draws index).card : Real) + 1) *
            scoreUnitEnvelope index component) =ᶠ[l]
        (fun index =>
          (drawCount index + 1) *
            scoreUnitEnvelope index component) := by
      filter_upwards [hdrawCount] with index hindex
      rw [hindex]
    exact (hscore_scaled_envelope_tendsto component hcomponent).congr' heq.symm
  have hbias_scaled_card :
      ∀ component, component ∈ biasComponents ->
        Tendsto
          (fun index =>
            (((draws index).card : Real) + 1) *
              biasUnitEnvelope index component)
          l (nhds 0) := by
    intro component hcomponent
    have heq :
        (fun index =>
          (((draws index).card : Real) + 1) *
            biasUnitEnvelope index component) =ᶠ[l]
        (fun index =>
          (drawCount index + 1) *
            biasUnitEnvelope index component) := by
      filter_upwards [hdrawCount] with index hindex
      rw [hindex]
    exact (hbias_scaled_envelope_tendsto component hcomponent).congr' heq.symm
  exact
    tendsto_actualBootstrapVariance_of_eventually_cell_contribution_weight_limits_and_uniformAssignment_draw_card_component_product_bounds
      (l := l) cells scoreComponents biasComponents sample draws assignment
      score contribution weight target denominator normalizer
      cellContribution cellWeight contributionLimit weightLimit massLimit
      actualVariance scoreReplicationError biasCorrectionError
      scoreUnitComponent biasUnitComponent scoreUnitEnvelope biasUnitEnvelope
      herror_decomp hcover hcontributionCell hweightCell hcontributionLimit
      hweightLimit hmass hscore_construct hscore_component_bound
      hscore_scaled_card hbias_construct hbias_component_bound
      hbias_scaled_card

/--
The `drawCount + 1` scaled-envelope rate follows from the usual
`drawCount * envelope` rate plus the envelope itself vanishing.
-/
theorem tendsto_drawCount_add_one_mul_envelope_zero_of_scaled_and_envelope
    (drawCount envelope : Index -> Real)
    (hscaled :
      Tendsto (fun index => drawCount index * envelope index) l (nhds 0))
    (henvelope :
      Tendsto envelope l (nhds 0)) :
    Tendsto
      (fun index => (drawCount index + 1) * envelope index)
      l (nhds 0) := by
  have hsum :
      Tendsto
        (fun index =>
          drawCount index * envelope index + envelope index)
        l (nhds 0) :=
    by simpa using hscaled.add henvelope
  convert hsum using 1
  ext index
  ring

/--
Uniform-assignment draw-count-scale route where the scaled envelope rate is
provided in the common `drawCount * envelope -> 0` form, with the separate
plain envelope convergence supplying the `+ 1` term.
-/
theorem tendsto_actualBootstrapVariance_of_eventually_cell_contribution_weight_limits_and_uniformAssignment_draw_count_scale_unit_envelope_rate_bounds
    [DecidableEq Unit] [DecidableEq Cell] [DecidableEq ScoreComponent]
    [DecidableEq BiasComponent]
    (cells : Finset Cell)
    (scoreComponents : Finset ScoreComponent)
    (biasComponents : Finset BiasComponent)
    (sample : Index -> Finset Unit) (draws : Index -> Finset Draw)
    (drawCount : Index -> Real)
    (assignment : Index -> Draw -> Unit)
    (score : Index -> Unit -> Cell)
    (contribution weight : Index -> Unit -> Real)
    (target denominator normalizer : Real)
    (cellContribution cellWeight : Index -> Cell -> Real)
    (contributionLimit weightLimit massLimit : Cell -> Real)
    (actualVariance scoreReplicationError biasCorrectionError : Index -> Real)
    (scoreUnitComponent : Index -> Unit -> ScoreComponent -> Real)
    (biasUnitComponent : Index -> Unit -> BiasComponent -> Real)
    (scoreUnitEnvelope : Index -> ScoreComponent -> Real)
    (biasUnitEnvelope : Index -> BiasComponent -> Real)
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
    (hdrawCount :
      ∀ᶠ index in l,
        ((draws index).card : Real) = drawCount index)
    (hscore_construct :
      scoreReplicationError =ᶠ[l]
        (fun index =>
          ∑ component ∈ scoreComponents, ∑ unit ∈ sample index,
            (multinomialCountFromDrawIndicators (draws index)
                (fun assignment draw unit =>
                  oneHotAssignmentIndicator assignment draw unit)
                (assignment index) unit - 1) *
              scoreUnitComponent index unit component))
    (hscore_component_bound :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ sample index ->
          ∀ component, component ∈ scoreComponents ->
            |scoreUnitComponent index unit component| ≤
              scoreUnitEnvelope index component)
    (hscore_scaled_envelope_tendsto :
      ∀ component, component ∈ scoreComponents ->
        Tendsto
          (fun index =>
            drawCount index * scoreUnitEnvelope index component)
          l (nhds 0))
    (hscore_envelope_tendsto :
      ∀ component, component ∈ scoreComponents ->
        Tendsto (fun index => scoreUnitEnvelope index component)
          l (nhds 0))
    (hbias_construct :
      biasCorrectionError =ᶠ[l]
        (fun index =>
          ∑ component ∈ biasComponents, ∑ unit ∈ sample index,
            (multinomialCountFromDrawIndicators (draws index)
                (fun assignment draw unit =>
                  oneHotAssignmentIndicator assignment draw unit)
                (assignment index) unit - 1) *
              biasUnitComponent index unit component))
    (hbias_component_bound :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ sample index ->
          ∀ component, component ∈ biasComponents ->
            |biasUnitComponent index unit component| ≤
              biasUnitEnvelope index component)
    (hbias_scaled_envelope_tendsto :
      ∀ component, component ∈ biasComponents ->
        Tendsto
          (fun index =>
            drawCount index * biasUnitEnvelope index component)
          l (nhds 0))
    (hbias_envelope_tendsto :
      ∀ component, component ∈ biasComponents ->
        Tendsto (fun index => biasUnitEnvelope index component)
          l (nhds 0)) :
    Tendsto actualVariance l
      (nhds
        ((1 / denominator ^ 2) * (1 / normalizer) *
          weightedScoreCellMomentLimit cells
            (fun cell =>
              (contributionLimit cell - target * weightLimit cell) ^ 2)
            massLimit)) :=
  tendsto_actualBootstrapVariance_of_eventually_cell_contribution_weight_limits_and_uniformAssignment_draw_count_scale_component_product_bounds
    (l := l) cells scoreComponents biasComponents sample draws drawCount
    assignment score contribution weight target denominator normalizer
    cellContribution cellWeight contributionLimit weightLimit massLimit
    actualVariance scoreReplicationError biasCorrectionError
    scoreUnitComponent biasUnitComponent scoreUnitEnvelope biasUnitEnvelope
    herror_decomp hcover hcontributionCell hweightCell hcontributionLimit
    hweightLimit hmass hdrawCount hscore_construct hscore_component_bound
    (fun component hcomponent =>
      tendsto_drawCount_add_one_mul_envelope_zero_of_scaled_and_envelope
        (l := l) drawCount (fun index => scoreUnitEnvelope index component)
        (hscore_scaled_envelope_tendsto component hcomponent)
        (hscore_envelope_tendsto component hcomponent))
    hbias_construct hbias_component_bound
    (fun component hcomponent =>
      tendsto_drawCount_add_one_mul_envelope_zero_of_scaled_and_envelope
        (l := l) drawCount (fun index => biasUnitEnvelope index component)
        (hbias_scaled_envelope_tendsto component hcomponent)
        (hbias_envelope_tendsto component hcomponent))

/--
The abstract actual-minus-linearized bootstrap error decomposition follows
from the concrete uniform-assignment one-hot resampling law when the sample and
draw supports are eventually the full finite types.
-/
theorem eventually_actualBootstrapVariance_error_decomp_of_uniformAssignment_base_ratio
    [Fintype Unit] [Fintype Draw] [DecidableEq Unit]
    [DecidableEq Draw] [Nonempty Unit]
    (sample : Index -> Finset Unit) (draws : Index -> Finset Draw)
    (contribution weight : Index -> Unit -> Real)
    (target denominator normalizer sampleSize : Real)
    (actualVariance scoreReplicationError biasCorrectionError : Index -> Real)
    (hunit_card : (Fintype.card Unit : Real) = sampleSize)
    (hdraw_card : (Fintype.card Draw : Real) = sampleSize)
    (hsampleSize_ne : sampleSize ≠ 0)
    (hsample_univ :
      sample =ᶠ[l] fun _index => (Finset.univ : Finset Unit))
    (hdraws_univ :
      draws =ᶠ[l] fun _index => (Finset.univ : Finset Draw))
    (hbase :
      ∀ᶠ index in l,
        baseLinearizedSum (Finset.univ : Finset Unit)
            (contribution index) =
          target *
            baseLinearizedSum (Finset.univ : Finset Unit)
              (weight index))
    (hvariance_decomp :
      actualVariance =ᶠ[l]
        (fun index =>
          (1 / denominator ^ 2) * (1 / normalizer) *
              multiplierPerturbationSecondMoment
                (uniformAssignmentSupport Unit Draw)
                (uniformAssignmentMass Unit Draw)
                (sample index)
                (fun assignment unit =>
                  multinomialCountFromDrawIndicators (draws index)
                    (fun assignment draw unit =>
                      oneHotAssignmentIndicator assignment draw unit)
                    assignment unit)
                (fun unit =>
                  contribution index unit - target * weight index unit) +
            scoreReplicationError index + biasCorrectionError index)) :
    (fun index =>
      actualVariance index -
        bootstrapCenteredVarianceTarget (sample index)
          (contribution index) (weight index) target denominator normalizer) =ᶠ[l]
      (fun index => scoreReplicationError index + biasCorrectionError index) := by
  filter_upwards [hvariance_decomp, hsample_univ, hdraws_univ, hbase] with
    index hvariance hsample hdraws hbase_index
  have htarget :=
    multiplierPerturbationSecondMoment_normalized_eq_bootstrapCenteredVarianceTarget_of_uniformAssignment_base_ratio
      (Unit := Unit) (Draw := Draw)
      (contribution index) (weight index) target denominator normalizer
      sampleSize hunit_card hdraw_card hsampleSize_ne hbase_index
  calc
    actualVariance index -
        bootstrapCenteredVarianceTarget (sample index)
          (contribution index) (weight index) target denominator normalizer =
      ((1 / denominator ^ 2) * (1 / normalizer) *
            multiplierPerturbationSecondMoment
              (uniformAssignmentSupport Unit Draw)
              (uniformAssignmentMass Unit Draw)
              (sample index)
              (fun assignment unit =>
                multinomialCountFromDrawIndicators (draws index)
                  (fun assignment draw unit =>
                    oneHotAssignmentIndicator assignment draw unit)
                  assignment unit)
              (fun unit =>
                contribution index unit - target * weight index unit) +
          scoreReplicationError index + biasCorrectionError index) -
        bootstrapCenteredVarianceTarget (sample index)
          (contribution index) (weight index) target denominator
          normalizer := by
        rw [hvariance]
    _ =
      ((1 / denominator ^ 2) * (1 / normalizer) *
            multiplierPerturbationSecondMoment
              (uniformAssignmentSupport Unit Draw)
              (uniformAssignmentMass Unit Draw)
              (Finset.univ : Finset Unit)
              (fun assignment unit =>
                multinomialCountFromDrawIndicators
                  (Finset.univ : Finset Draw)
                  (fun assignment draw unit =>
                    oneHotAssignmentIndicator assignment draw unit)
                  assignment unit)
              (fun unit =>
                contribution index unit - target * weight index unit) +
          scoreReplicationError index + biasCorrectionError index) -
        bootstrapCenteredVarianceTarget (Finset.univ : Finset Unit)
          (contribution index) (weight index) target denominator
          normalizer := by
        rw [hsample, hdraws]
    _ =
      (bootstrapCenteredVarianceTarget (Finset.univ : Finset Unit)
          (contribution index) (weight index) target denominator
          normalizer +
          scoreReplicationError index + biasCorrectionError index) -
        bootstrapCenteredVarianceTarget (Finset.univ : Finset Unit)
          (contribution index) (weight index) target denominator
          normalizer := by
        rw [htarget]
    _ = scoreReplicationError index + biasCorrectionError index := by
        ring

/--
Uniform-assignment resampling-law route for actual bootstrap variance.  The
error decomposition is derived from the concrete one-hot law and then fed into
the draw-count-scale finite-error reducer.
-/
theorem tendsto_actualBootstrapVariance_of_eventually_cell_contribution_weight_limits_and_uniformAssignment_base_ratio_draw_count_scale_unit_envelope_rate_bounds
    [Fintype Unit] [Fintype Draw] [DecidableEq Unit] [DecidableEq Draw]
    [Nonempty Unit] [DecidableEq Cell] [DecidableEq ScoreComponent]
    [DecidableEq BiasComponent]
    (cells : Finset Cell)
    (scoreComponents : Finset ScoreComponent)
    (biasComponents : Finset BiasComponent)
    (sample : Index -> Finset Unit) (draws : Index -> Finset Draw)
    (drawCount : Index -> Real)
    (assignment : Index -> Draw -> Unit)
    (score : Index -> Unit -> Cell)
    (contribution weight : Index -> Unit -> Real)
    (target denominator normalizer sampleSize : Real)
    (cellContribution cellWeight : Index -> Cell -> Real)
    (contributionLimit weightLimit massLimit : Cell -> Real)
    (actualVariance scoreReplicationError biasCorrectionError : Index -> Real)
    (scoreUnitComponent : Index -> Unit -> ScoreComponent -> Real)
    (biasUnitComponent : Index -> Unit -> BiasComponent -> Real)
    (scoreUnitEnvelope : Index -> ScoreComponent -> Real)
    (biasUnitEnvelope : Index -> BiasComponent -> Real)
    (hunit_card : (Fintype.card Unit : Real) = sampleSize)
    (hdraw_card : (Fintype.card Draw : Real) = sampleSize)
    (hsampleSize_ne : sampleSize ≠ 0)
    (hsample_univ :
      sample =ᶠ[l] fun _index => (Finset.univ : Finset Unit))
    (hdraws_univ :
      draws =ᶠ[l] fun _index => (Finset.univ : Finset Draw))
    (hbase :
      ∀ᶠ index in l,
        baseLinearizedSum (Finset.univ : Finset Unit)
            (contribution index) =
          target *
            baseLinearizedSum (Finset.univ : Finset Unit)
              (weight index))
    (hvariance_decomp :
      actualVariance =ᶠ[l]
        (fun index =>
          (1 / denominator ^ 2) * (1 / normalizer) *
              multiplierPerturbationSecondMoment
                (uniformAssignmentSupport Unit Draw)
                (uniformAssignmentMass Unit Draw)
                (sample index)
                (fun assignment unit =>
                  multinomialCountFromDrawIndicators (draws index)
                    (fun assignment draw unit =>
                      oneHotAssignmentIndicator assignment draw unit)
                    assignment unit)
                (fun unit =>
                  contribution index unit - target * weight index unit) +
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
    (hdrawCount :
      ∀ᶠ index in l,
        ((draws index).card : Real) = drawCount index)
    (hscore_construct :
      scoreReplicationError =ᶠ[l]
        (fun index =>
          ∑ component ∈ scoreComponents, ∑ unit ∈ sample index,
            (multinomialCountFromDrawIndicators (draws index)
                (fun assignment draw unit =>
                  oneHotAssignmentIndicator assignment draw unit)
                (assignment index) unit - 1) *
              scoreUnitComponent index unit component))
    (hscore_component_bound :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ sample index ->
          ∀ component, component ∈ scoreComponents ->
            |scoreUnitComponent index unit component| ≤
              scoreUnitEnvelope index component)
    (hscore_scaled_envelope_tendsto :
      ∀ component, component ∈ scoreComponents ->
        Tendsto
          (fun index =>
            drawCount index * scoreUnitEnvelope index component)
          l (nhds 0))
    (hscore_envelope_tendsto :
      ∀ component, component ∈ scoreComponents ->
        Tendsto (fun index => scoreUnitEnvelope index component)
          l (nhds 0))
    (hbias_construct :
      biasCorrectionError =ᶠ[l]
        (fun index =>
          ∑ component ∈ biasComponents, ∑ unit ∈ sample index,
            (multinomialCountFromDrawIndicators (draws index)
                (fun assignment draw unit =>
                  oneHotAssignmentIndicator assignment draw unit)
                (assignment index) unit - 1) *
              biasUnitComponent index unit component))
    (hbias_component_bound :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ sample index ->
          ∀ component, component ∈ biasComponents ->
            |biasUnitComponent index unit component| ≤
              biasUnitEnvelope index component)
    (hbias_scaled_envelope_tendsto :
      ∀ component, component ∈ biasComponents ->
        Tendsto
          (fun index =>
            drawCount index * biasUnitEnvelope index component)
          l (nhds 0))
    (hbias_envelope_tendsto :
      ∀ component, component ∈ biasComponents ->
        Tendsto (fun index => biasUnitEnvelope index component)
          l (nhds 0)) :
    Tendsto actualVariance l
      (nhds
        ((1 / denominator ^ 2) * (1 / normalizer) *
          weightedScoreCellMomentLimit cells
            (fun cell =>
              (contributionLimit cell - target * weightLimit cell) ^ 2)
            massLimit)) := by
  have herror_decomp :
      (fun index =>
        actualVariance index -
          bootstrapCenteredVarianceTarget (sample index)
            (contribution index) (weight index) target denominator
            normalizer) =ᶠ[l]
        (fun index =>
          scoreReplicationError index + biasCorrectionError index) :=
    eventually_actualBootstrapVariance_error_decomp_of_uniformAssignment_base_ratio
      (l := l) sample draws contribution weight target denominator
      normalizer sampleSize actualVariance scoreReplicationError
      biasCorrectionError hunit_card hdraw_card hsampleSize_ne
      hsample_univ hdraws_univ hbase hvariance_decomp
  exact
    tendsto_actualBootstrapVariance_of_eventually_cell_contribution_weight_limits_and_uniformAssignment_draw_count_scale_unit_envelope_rate_bounds
      (l := l) cells scoreComponents biasComponents sample draws drawCount
      assignment score contribution weight target denominator normalizer
      cellContribution cellWeight contributionLimit weightLimit massLimit
      actualVariance scoreReplicationError biasCorrectionError
      scoreUnitComponent biasUnitComponent scoreUnitEnvelope biasUnitEnvelope
      herror_decomp hcover hcontributionCell hweightCell hcontributionLimit
      hweightLimit hmass hdrawCount hscore_construct hscore_component_bound
      hscore_scaled_envelope_tendsto hscore_envelope_tendsto
      hbias_construct hbias_component_bound hbias_scaled_envelope_tendsto
      hbias_envelope_tendsto

/--
Uniform-assignment resampling-law route for the common one-contribution
score/bias case.  The score-replication and bias-correction constructions are
the paper-facing replicated-linearized minus base expressions, and the finite
component sums are discharged by singleton component sets.
-/
theorem tendsto_actualBootstrapVariance_of_eventually_cell_contribution_weight_limits_and_uniformAssignment_base_ratio_draw_count_scale_singleton_replicatedLinearized_unit_envelope_rate_bounds
    [Fintype Unit] [Fintype Draw] [DecidableEq Unit] [DecidableEq Draw]
    [Nonempty Unit] [DecidableEq Cell] [DecidableEq ScoreComponent]
    [DecidableEq BiasComponent]
    (cells : Finset Cell)
    (scoreComponent : ScoreComponent)
    (biasComponent : BiasComponent)
    (sample : Index -> Finset Unit) (draws : Index -> Finset Draw)
    (drawCount : Index -> Real)
    (assignment : Index -> Draw -> Unit)
    (score : Index -> Unit -> Cell)
    (contribution weight : Index -> Unit -> Real)
    (target denominator normalizer sampleSize : Real)
    (cellContribution cellWeight : Index -> Cell -> Real)
    (contributionLimit weightLimit massLimit : Cell -> Real)
    (actualVariance scoreReplicationError biasCorrectionError : Index -> Real)
    (scoreUnitContribution biasUnitContribution : Index -> Unit -> Real)
    (scoreUnitEnvelope biasUnitEnvelope : Index -> Real)
    (hunit_card : (Fintype.card Unit : Real) = sampleSize)
    (hdraw_card : (Fintype.card Draw : Real) = sampleSize)
    (hsampleSize_ne : sampleSize ≠ 0)
    (hsample_univ :
      sample =ᶠ[l] fun _index => (Finset.univ : Finset Unit))
    (hdraws_univ :
      draws =ᶠ[l] fun _index => (Finset.univ : Finset Draw))
    (hbase :
      ∀ᶠ index in l,
        baseLinearizedSum (Finset.univ : Finset Unit)
            (contribution index) =
          target *
            baseLinearizedSum (Finset.univ : Finset Unit)
              (weight index))
    (hvariance_decomp :
      actualVariance =ᶠ[l]
        (fun index =>
          (1 / denominator ^ 2) * (1 / normalizer) *
              multiplierPerturbationSecondMoment
                (uniformAssignmentSupport Unit Draw)
                (uniformAssignmentMass Unit Draw)
                (sample index)
                (fun assignment unit =>
                  multinomialCountFromDrawIndicators (draws index)
                    (fun assignment draw unit =>
                      oneHotAssignmentIndicator assignment draw unit)
                    assignment unit)
                (fun unit =>
                  contribution index unit - target * weight index unit) +
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
    (hdrawCount :
      ∀ᶠ index in l,
        ((draws index).card : Real) = drawCount index)
    (hscore_construct :
      scoreReplicationError =ᶠ[l]
        (fun index =>
          replicatedLinearizedSum (sample index)
              (fun unit =>
                multinomialCountFromDrawIndicators (draws index)
                  (fun assignment draw unit =>
                    oneHotAssignmentIndicator assignment draw unit)
                  (assignment index) unit)
              (scoreUnitContribution index) -
            baseLinearizedSum (sample index)
              (scoreUnitContribution index)))
    (hscore_component_bound :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ sample index ->
          |scoreUnitContribution index unit| ≤ scoreUnitEnvelope index)
    (hscore_scaled_envelope_tendsto :
      Tendsto (fun index => drawCount index * scoreUnitEnvelope index)
        l (nhds 0))
    (hscore_envelope_tendsto :
      Tendsto scoreUnitEnvelope l (nhds 0))
    (hbias_construct :
      biasCorrectionError =ᶠ[l]
        (fun index =>
          replicatedLinearizedSum (sample index)
              (fun unit =>
                multinomialCountFromDrawIndicators (draws index)
                  (fun assignment draw unit =>
                    oneHotAssignmentIndicator assignment draw unit)
                  (assignment index) unit)
              (biasUnitContribution index) -
            baseLinearizedSum (sample index)
              (biasUnitContribution index)))
    (hbias_component_bound :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ sample index ->
          |biasUnitContribution index unit| ≤ biasUnitEnvelope index)
    (hbias_scaled_envelope_tendsto :
      Tendsto (fun index => drawCount index * biasUnitEnvelope index)
        l (nhds 0))
    (hbias_envelope_tendsto :
      Tendsto biasUnitEnvelope l (nhds 0)) :
    Tendsto actualVariance l
      (nhds
        ((1 / denominator ^ 2) * (1 / normalizer) *
          weightedScoreCellMomentLimit cells
            (fun cell =>
              (contributionLimit cell - target * weightLimit cell) ^ 2)
            massLimit)) := by
  have hscore_centered :
      scoreReplicationError =ᶠ[l]
        (fun index =>
          ∑ unit ∈ sample index,
            (multinomialCountFromDrawIndicators (draws index)
                (fun assignment draw unit =>
                  oneHotAssignmentIndicator assignment draw unit)
                (assignment index) unit - 1) *
              scoreUnitContribution index unit) :=
    eventually_error_eq_centered_count_sum_of_replicated_sub_base
      (l := l) sample draws
      (fun _index assignment draw unit =>
        oneHotAssignmentIndicator assignment draw unit)
      assignment scoreUnitContribution scoreReplicationError hscore_construct
  have hbias_centered :
      biasCorrectionError =ᶠ[l]
        (fun index =>
          ∑ unit ∈ sample index,
            (multinomialCountFromDrawIndicators (draws index)
                (fun assignment draw unit =>
                  oneHotAssignmentIndicator assignment draw unit)
                (assignment index) unit - 1) *
              biasUnitContribution index unit) :=
    eventually_error_eq_centered_count_sum_of_replicated_sub_base
      (l := l) sample draws
      (fun _index assignment draw unit =>
        oneHotAssignmentIndicator assignment draw unit)
      assignment biasUnitContribution biasCorrectionError hbias_construct
  have hscore_component_construct :
      scoreReplicationError =ᶠ[l]
        (fun index =>
          ∑ component ∈ ({scoreComponent} : Finset ScoreComponent),
            ∑ unit ∈ sample index,
              (multinomialCountFromDrawIndicators (draws index)
                  (fun assignment draw unit =>
                    oneHotAssignmentIndicator assignment draw unit)
                  (assignment index) unit - 1) *
                (fun _component => scoreUnitContribution index unit)
                  component) := by
    filter_upwards [hscore_centered] with index hindex
    simpa using hindex
  have hbias_component_construct :
      biasCorrectionError =ᶠ[l]
        (fun index =>
          ∑ component ∈ ({biasComponent} : Finset BiasComponent),
            ∑ unit ∈ sample index,
              (multinomialCountFromDrawIndicators (draws index)
                  (fun assignment draw unit =>
                    oneHotAssignmentIndicator assignment draw unit)
                  (assignment index) unit - 1) *
                (fun _component => biasUnitContribution index unit)
                  component) := by
    filter_upwards [hbias_centered] with index hindex
    simpa using hindex
  exact
    tendsto_actualBootstrapVariance_of_eventually_cell_contribution_weight_limits_and_uniformAssignment_base_ratio_draw_count_scale_unit_envelope_rate_bounds
      (l := l) cells ({scoreComponent} : Finset ScoreComponent)
      ({biasComponent} : Finset BiasComponent) sample draws drawCount
      assignment score contribution weight target denominator normalizer
      sampleSize cellContribution cellWeight contributionLimit weightLimit
      massLimit actualVariance scoreReplicationError biasCorrectionError
      (fun index unit _component => scoreUnitContribution index unit)
      (fun index unit _component => biasUnitContribution index unit)
      (fun index _component => scoreUnitEnvelope index)
      (fun index _component => biasUnitEnvelope index)
      hunit_card hdraw_card hsampleSize_ne hsample_univ hdraws_univ hbase
      hvariance_decomp hcover hcontributionCell hweightCell
      hcontributionLimit hweightLimit hmass hdrawCount
      hscore_component_construct
      (by
        filter_upwards [hscore_component_bound] with index hbound unit
          hunit component _hcomponent
        simpa using hbound unit hunit)
      (fun _component _hcomponent => by
        simpa using hscore_scaled_envelope_tendsto)
      (fun _component _hcomponent => by
        simpa using hscore_envelope_tendsto)
      hbias_component_construct
      (by
        filter_upwards [hbias_component_bound] with index hbound unit
          hunit component _hcomponent
        simpa using hbound unit hunit)
      (fun _component _hcomponent => by
        simpa using hbias_scaled_envelope_tendsto)
      (fun _component _hcomponent => by
        simpa using hbias_envelope_tendsto)

/--
Retrospective PATE/PATT manuscript-numerator companion for the singleton
uniform-assignment route.  It accepts the paper-facing linearized bootstrap
numerator-minus-base constructions and derives the replicated-linearized
construction fields used by the finite error reducer internally.
-/
theorem tendsto_actualBootstrapVariance_of_eventually_cell_contribution_weight_limits_and_uniformAssignment_base_ratio_draw_count_scale_retrospectivePATEPATT_linearized_numerator_unit_envelope_rate_bounds
    [Fintype Unit] [Fintype Draw] [DecidableEq Unit] [DecidableEq Draw]
    [Nonempty Unit] [DecidableEq Cell] [DecidableEq ScoreComponent]
    [DecidableEq BiasComponent]
    (cells : Finset Cell)
    (scoreComponent : ScoreComponent)
    (biasComponent : BiasComponent)
    (sample : Index -> Finset Unit) (draws : Index -> Finset Draw)
    (drawCount : Index -> Real)
    (assignment : Index -> Draw -> Unit)
    (score : Index -> Unit -> Cell)
    (contribution weight : Index -> Unit -> Real)
    (target denominator normalizer sampleSize : Real)
    (cellContribution cellWeight : Index -> Cell -> Real)
    (contributionLimit weightLimit massLimit : Cell -> Real)
    (actualVariance scoreReplicationError biasCorrectionError : Index -> Real)
    (scoreBaseWeight scoreReuseResidualWeight scoreHeterogeneity
      scoreResidual : Index -> Unit -> Real)
    (biasTreatedContribution biasControlReuseContribution :
      Index -> Unit -> Real)
    (scoreUnitEnvelope biasUnitEnvelope : Index -> Real)
    (hunit_card : (Fintype.card Unit : Real) = sampleSize)
    (hdraw_card : (Fintype.card Draw : Real) = sampleSize)
    (hsampleSize_ne : sampleSize ≠ 0)
    (hsample_univ :
      sample =ᶠ[l] fun _index => (Finset.univ : Finset Unit))
    (hdraws_univ :
      draws =ᶠ[l] fun _index => (Finset.univ : Finset Draw))
    (hbase :
      ∀ᶠ index in l,
        baseLinearizedSum (Finset.univ : Finset Unit)
            (contribution index) =
          target *
            baseLinearizedSum (Finset.univ : Finset Unit)
              (weight index))
    (hvariance_decomp :
      actualVariance =ᶠ[l]
        (fun index =>
          (1 / denominator ^ 2) * (1 / normalizer) *
              multiplierPerturbationSecondMoment
                (uniformAssignmentSupport Unit Draw)
                (uniformAssignmentMass Unit Draw)
                (sample index)
                (fun assignment unit =>
                  multinomialCountFromDrawIndicators (draws index)
                    (fun assignment draw unit =>
                      oneHotAssignmentIndicator assignment draw unit)
                    assignment unit)
                (fun unit =>
                  contribution index unit - target * weight index unit) +
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
    (hdrawCount :
      ∀ᶠ index in l,
        ((draws index).card : Real) = drawCount index)
    (hscore_construct :
      scoreReplicationError =ᶠ[l]
        (fun index =>
          retrospectivePATELinearizedBootstrapNumerator (sample index)
              (fun unit =>
                multinomialCountFromDrawIndicators (draws index)
                  (fun assignment draw unit =>
                    oneHotAssignmentIndicator assignment draw unit)
                  (assignment index) unit)
              (scoreBaseWeight index) (scoreReuseResidualWeight index)
              (scoreHeterogeneity index) (scoreResidual index) -
            baseLinearizedSum (sample index)
              (retrospectivePATEBootstrapInfluenceContribution
                (scoreBaseWeight index) (scoreReuseResidualWeight index)
                (scoreHeterogeneity index) (scoreResidual index))))
    (hscore_component_bound :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ sample index ->
          |retrospectivePATEBootstrapInfluenceContribution
              (scoreBaseWeight index) (scoreReuseResidualWeight index)
              (scoreHeterogeneity index) (scoreResidual index) unit| ≤
            scoreUnitEnvelope index)
    (hscore_scaled_envelope_tendsto :
      Tendsto (fun index => drawCount index * scoreUnitEnvelope index)
        l (nhds 0))
    (hscore_envelope_tendsto :
      Tendsto scoreUnitEnvelope l (nhds 0))
    (hbias_construct :
      biasCorrectionError =ᶠ[l]
        (fun index =>
          retrospectivePATTLinearizedBootstrapNumerator (sample index)
              (fun unit =>
                multinomialCountFromDrawIndicators (draws index)
                  (fun assignment draw unit =>
                    oneHotAssignmentIndicator assignment draw unit)
                  (assignment index) unit)
              (biasTreatedContribution index)
              (biasControlReuseContribution index) -
            baseLinearizedSum (sample index)
              (retrospectivePATTBootstrapInfluenceContribution
                (biasTreatedContribution index)
                (biasControlReuseContribution index))))
    (hbias_component_bound :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ sample index ->
          |retrospectivePATTBootstrapInfluenceContribution
              (biasTreatedContribution index)
              (biasControlReuseContribution index) unit| ≤
            biasUnitEnvelope index)
    (hbias_scaled_envelope_tendsto :
      Tendsto (fun index => drawCount index * biasUnitEnvelope index)
        l (nhds 0))
    (hbias_envelope_tendsto :
      Tendsto biasUnitEnvelope l (nhds 0)) :
    Tendsto actualVariance l
      (nhds
        ((1 / denominator ^ 2) * (1 / normalizer) *
          weightedScoreCellMomentLimit cells
            (fun cell =>
              (contributionLimit cell - target * weightLimit cell) ^ 2)
            massLimit)) := by
  have hscore_replicated :
      scoreReplicationError =ᶠ[l]
        (fun index =>
          replicatedLinearizedSum (sample index)
              (fun unit =>
                multinomialCountFromDrawIndicators (draws index)
                  (fun assignment draw unit =>
                    oneHotAssignmentIndicator assignment draw unit)
                  (assignment index) unit)
              (retrospectivePATEBootstrapInfluenceContribution
                (scoreBaseWeight index) (scoreReuseResidualWeight index)
                (scoreHeterogeneity index) (scoreResidual index)) -
            baseLinearizedSum (sample index)
              (retrospectivePATEBootstrapInfluenceContribution
                (scoreBaseWeight index) (scoreReuseResidualWeight index)
                (scoreHeterogeneity index) (scoreResidual index))) :=
    eventually_error_eq_retrospectivePATE_replicatedLinearized_sub_base_of_linearized_numerator
      (l := l) sample draws
      (fun _index assignment draw unit =>
        oneHotAssignmentIndicator assignment draw unit)
      assignment scoreBaseWeight scoreReuseResidualWeight
      scoreHeterogeneity scoreResidual scoreReplicationError
      hscore_construct
  have hbias_replicated :
      biasCorrectionError =ᶠ[l]
        (fun index =>
          replicatedLinearizedSum (sample index)
              (fun unit =>
                multinomialCountFromDrawIndicators (draws index)
                  (fun assignment draw unit =>
                    oneHotAssignmentIndicator assignment draw unit)
                  (assignment index) unit)
              (retrospectivePATTBootstrapInfluenceContribution
                (biasTreatedContribution index)
                (biasControlReuseContribution index)) -
            baseLinearizedSum (sample index)
              (retrospectivePATTBootstrapInfluenceContribution
                (biasTreatedContribution index)
                (biasControlReuseContribution index))) :=
    eventually_error_eq_retrospectivePATT_replicatedLinearized_sub_base_of_linearized_numerator
      (l := l) sample draws
      (fun _index assignment draw unit =>
        oneHotAssignmentIndicator assignment draw unit)
      assignment biasTreatedContribution biasControlReuseContribution
      biasCorrectionError hbias_construct
  exact
    tendsto_actualBootstrapVariance_of_eventually_cell_contribution_weight_limits_and_uniformAssignment_base_ratio_draw_count_scale_singleton_replicatedLinearized_unit_envelope_rate_bounds
      (l := l) cells scoreComponent biasComponent sample draws drawCount
      assignment score contribution weight target denominator normalizer
      sampleSize cellContribution cellWeight contributionLimit weightLimit
      massLimit actualVariance scoreReplicationError biasCorrectionError
      (fun index =>
        retrospectivePATEBootstrapInfluenceContribution
          (scoreBaseWeight index) (scoreReuseResidualWeight index)
          (scoreHeterogeneity index) (scoreResidual index))
      (fun index =>
        retrospectivePATTBootstrapInfluenceContribution
          (biasTreatedContribution index)
          (biasControlReuseContribution index))
      scoreUnitEnvelope biasUnitEnvelope hunit_card hdraw_card
      hsampleSize_ne hsample_univ hdraws_univ hbase hvariance_decomp
      hcover hcontributionCell hweightCell hcontributionLimit
      hweightLimit hmass hdrawCount hscore_replicated
      hscore_component_bound hscore_scaled_envelope_tendsto
      hscore_envelope_tendsto hbias_replicated hbias_component_bound
      hbias_scaled_envelope_tendsto hbias_envelope_tendsto

/--
Uniform full-support resampling-law route with no separate draw-count scale.
The draw-count equality follows from eventual full draw support and the
cardinality identity, and the scaled-envelope rates follow from the fixed
finite draw cardinality times the plain shrinking envelopes.
-/
theorem tendsto_actualBootstrapVariance_of_eventually_cell_contribution_weight_limits_and_uniformAssignment_base_ratio_full_support_unit_envelope_bounds
    [Fintype Unit] [Fintype Draw] [DecidableEq Unit] [DecidableEq Draw]
    [Nonempty Unit] [DecidableEq Cell] [DecidableEq ScoreComponent]
    [DecidableEq BiasComponent]
    (cells : Finset Cell)
    (scoreComponents : Finset ScoreComponent)
    (biasComponents : Finset BiasComponent)
    (sample : Index -> Finset Unit) (draws : Index -> Finset Draw)
    (assignment : Index -> Draw -> Unit)
    (score : Index -> Unit -> Cell)
    (contribution weight : Index -> Unit -> Real)
    (target denominator normalizer sampleSize : Real)
    (cellContribution cellWeight : Index -> Cell -> Real)
    (contributionLimit weightLimit massLimit : Cell -> Real)
    (actualVariance scoreReplicationError biasCorrectionError : Index -> Real)
    (scoreUnitComponent : Index -> Unit -> ScoreComponent -> Real)
    (biasUnitComponent : Index -> Unit -> BiasComponent -> Real)
    (scoreUnitEnvelope : Index -> ScoreComponent -> Real)
    (biasUnitEnvelope : Index -> BiasComponent -> Real)
    (hunit_card : (Fintype.card Unit : Real) = sampleSize)
    (hdraw_card : (Fintype.card Draw : Real) = sampleSize)
    (hsampleSize_ne : sampleSize ≠ 0)
    (hsample_univ :
      sample =ᶠ[l] fun _index => (Finset.univ : Finset Unit))
    (hdraws_univ :
      draws =ᶠ[l] fun _index => (Finset.univ : Finset Draw))
    (hbase :
      ∀ᶠ index in l,
        baseLinearizedSum (Finset.univ : Finset Unit)
            (contribution index) =
          target *
            baseLinearizedSum (Finset.univ : Finset Unit)
              (weight index))
    (hvariance_decomp :
      actualVariance =ᶠ[l]
        (fun index =>
          (1 / denominator ^ 2) * (1 / normalizer) *
              multiplierPerturbationSecondMoment
                (uniformAssignmentSupport Unit Draw)
                (uniformAssignmentMass Unit Draw)
                (sample index)
                (fun assignment unit =>
                  multinomialCountFromDrawIndicators (draws index)
                    (fun assignment draw unit =>
                      oneHotAssignmentIndicator assignment draw unit)
                    assignment unit)
                (fun unit =>
                  contribution index unit - target * weight index unit) +
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
    (hscore_construct :
      scoreReplicationError =ᶠ[l]
        (fun index =>
          ∑ component ∈ scoreComponents, ∑ unit ∈ sample index,
            (multinomialCountFromDrawIndicators (draws index)
                (fun assignment draw unit =>
                  oneHotAssignmentIndicator assignment draw unit)
                (assignment index) unit - 1) *
              scoreUnitComponent index unit component))
    (hscore_component_bound :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ sample index ->
          ∀ component, component ∈ scoreComponents ->
            |scoreUnitComponent index unit component| ≤
              scoreUnitEnvelope index component)
    (hscore_envelope_tendsto :
      ∀ component, component ∈ scoreComponents ->
        Tendsto (fun index => scoreUnitEnvelope index component)
          l (nhds 0))
    (hbias_construct :
      biasCorrectionError =ᶠ[l]
        (fun index =>
          ∑ component ∈ biasComponents, ∑ unit ∈ sample index,
            (multinomialCountFromDrawIndicators (draws index)
                (fun assignment draw unit =>
                  oneHotAssignmentIndicator assignment draw unit)
                (assignment index) unit - 1) *
              biasUnitComponent index unit component))
    (hbias_component_bound :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ sample index ->
          ∀ component, component ∈ biasComponents ->
            |biasUnitComponent index unit component| ≤
              biasUnitEnvelope index component)
    (hbias_envelope_tendsto :
      ∀ component, component ∈ biasComponents ->
        Tendsto (fun index => biasUnitEnvelope index component)
          l (nhds 0)) :
    Tendsto actualVariance l
      (nhds
        ((1 / denominator ^ 2) * (1 / normalizer) *
          weightedScoreCellMomentLimit cells
            (fun cell =>
              (contributionLimit cell - target * weightLimit cell) ^ 2)
            massLimit)) := by
  have hdrawCount :
      ∀ᶠ index in l,
        ((draws index).card : Real) =
          (fun _index : Index => sampleSize) index := by
    filter_upwards [hdraws_univ] with index hdraws_index
    rw [hdraws_index]
    simpa using hdraw_card
  have hscore_scaled_envelope_tendsto :
      ∀ component, component ∈ scoreComponents ->
        Tendsto
          (fun index =>
            (fun _index : Index => sampleSize) index *
              scoreUnitEnvelope index component)
          l (nhds 0) := by
    intro component hcomponent
    simpa using
      ((tendsto_const_nhds :
          Tendsto (fun _index : Index => sampleSize) l
            (nhds sampleSize)).mul
        (hscore_envelope_tendsto component hcomponent))
  have hbias_scaled_envelope_tendsto :
      ∀ component, component ∈ biasComponents ->
        Tendsto
          (fun index =>
            (fun _index : Index => sampleSize) index *
              biasUnitEnvelope index component)
          l (nhds 0) := by
    intro component hcomponent
    simpa using
      ((tendsto_const_nhds :
          Tendsto (fun _index : Index => sampleSize) l
            (nhds sampleSize)).mul
        (hbias_envelope_tendsto component hcomponent))
  exact
    tendsto_actualBootstrapVariance_of_eventually_cell_contribution_weight_limits_and_uniformAssignment_base_ratio_draw_count_scale_unit_envelope_rate_bounds
      (l := l) cells scoreComponents biasComponents sample draws
      (fun _index : Index => sampleSize) assignment score contribution
      weight target denominator normalizer sampleSize cellContribution
      cellWeight contributionLimit weightLimit massLimit actualVariance
      scoreReplicationError biasCorrectionError scoreUnitComponent
      biasUnitComponent scoreUnitEnvelope biasUnitEnvelope hunit_card
      hdraw_card hsampleSize_ne hsample_univ hdraws_univ hbase
      hvariance_decomp hcover hcontributionCell hweightCell
      hcontributionLimit hweightLimit hmass hdrawCount hscore_construct
      hscore_component_bound hscore_scaled_envelope_tendsto
      hscore_envelope_tendsto hbias_construct hbias_component_bound
      hbias_scaled_envelope_tendsto hbias_envelope_tendsto

/--
Fixed full-support version of the singleton replicated-linearized route.
The draw-count scale and scaled-envelope rates are derived from eventual full
draw support, leaving only ordinary singleton unit-envelope convergence.
-/
theorem tendsto_actualBootstrapVariance_of_eventually_cell_contribution_weight_limits_and_uniformAssignment_base_ratio_full_support_singleton_replicatedLinearized_unit_envelope_bounds
    [Fintype Unit] [Fintype Draw] [DecidableEq Unit] [DecidableEq Draw]
    [Nonempty Unit] [DecidableEq Cell] [DecidableEq ScoreComponent]
    [DecidableEq BiasComponent]
    (cells : Finset Cell)
    (scoreComponent : ScoreComponent)
    (biasComponent : BiasComponent)
    (sample : Index -> Finset Unit) (draws : Index -> Finset Draw)
    (assignment : Index -> Draw -> Unit)
    (score : Index -> Unit -> Cell)
    (contribution weight : Index -> Unit -> Real)
    (target denominator normalizer sampleSize : Real)
    (cellContribution cellWeight : Index -> Cell -> Real)
    (contributionLimit weightLimit massLimit : Cell -> Real)
    (actualVariance scoreReplicationError biasCorrectionError : Index -> Real)
    (scoreUnitContribution biasUnitContribution : Index -> Unit -> Real)
    (scoreUnitEnvelope biasUnitEnvelope : Index -> Real)
    (hunit_card : (Fintype.card Unit : Real) = sampleSize)
    (hdraw_card : (Fintype.card Draw : Real) = sampleSize)
    (hsampleSize_ne : sampleSize ≠ 0)
    (hsample_univ :
      sample =ᶠ[l] fun _index => (Finset.univ : Finset Unit))
    (hdraws_univ :
      draws =ᶠ[l] fun _index => (Finset.univ : Finset Draw))
    (hbase :
      ∀ᶠ index in l,
        baseLinearizedSum (Finset.univ : Finset Unit)
            (contribution index) =
          target *
            baseLinearizedSum (Finset.univ : Finset Unit)
              (weight index))
    (hvariance_decomp :
      actualVariance =ᶠ[l]
        (fun index =>
          (1 / denominator ^ 2) * (1 / normalizer) *
              multiplierPerturbationSecondMoment
                (uniformAssignmentSupport Unit Draw)
                (uniformAssignmentMass Unit Draw)
                (sample index)
                (fun assignment unit =>
                  multinomialCountFromDrawIndicators (draws index)
                    (fun assignment draw unit =>
                      oneHotAssignmentIndicator assignment draw unit)
                    assignment unit)
                (fun unit =>
                  contribution index unit - target * weight index unit) +
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
    (hscore_construct :
      scoreReplicationError =ᶠ[l]
        (fun index =>
          replicatedLinearizedSum (sample index)
              (fun unit =>
                multinomialCountFromDrawIndicators (draws index)
                  (fun assignment draw unit =>
                    oneHotAssignmentIndicator assignment draw unit)
                  (assignment index) unit)
              (scoreUnitContribution index) -
            baseLinearizedSum (sample index)
              (scoreUnitContribution index)))
    (hscore_component_bound :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ sample index ->
          |scoreUnitContribution index unit| ≤ scoreUnitEnvelope index)
    (hscore_envelope_tendsto :
      Tendsto scoreUnitEnvelope l (nhds 0))
    (hbias_construct :
      biasCorrectionError =ᶠ[l]
        (fun index =>
          replicatedLinearizedSum (sample index)
              (fun unit =>
                multinomialCountFromDrawIndicators (draws index)
                  (fun assignment draw unit =>
                    oneHotAssignmentIndicator assignment draw unit)
                  (assignment index) unit)
              (biasUnitContribution index) -
            baseLinearizedSum (sample index)
              (biasUnitContribution index)))
    (hbias_component_bound :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ sample index ->
          |biasUnitContribution index unit| ≤ biasUnitEnvelope index)
    (hbias_envelope_tendsto :
      Tendsto biasUnitEnvelope l (nhds 0)) :
    Tendsto actualVariance l
      (nhds
        ((1 / denominator ^ 2) * (1 / normalizer) *
          weightedScoreCellMomentLimit cells
            (fun cell =>
              (contributionLimit cell - target * weightLimit cell) ^ 2)
            massLimit)) := by
  have hscore_centered :
      scoreReplicationError =ᶠ[l]
        (fun index =>
          ∑ unit ∈ sample index,
            (multinomialCountFromDrawIndicators (draws index)
                (fun assignment draw unit =>
                  oneHotAssignmentIndicator assignment draw unit)
                (assignment index) unit - 1) *
              scoreUnitContribution index unit) :=
    eventually_error_eq_centered_count_sum_of_replicated_sub_base
      (l := l) sample draws
      (fun _index assignment draw unit =>
        oneHotAssignmentIndicator assignment draw unit)
      assignment scoreUnitContribution scoreReplicationError hscore_construct
  have hbias_centered :
      biasCorrectionError =ᶠ[l]
        (fun index =>
          ∑ unit ∈ sample index,
            (multinomialCountFromDrawIndicators (draws index)
                (fun assignment draw unit =>
                  oneHotAssignmentIndicator assignment draw unit)
                (assignment index) unit - 1) *
              biasUnitContribution index unit) :=
    eventually_error_eq_centered_count_sum_of_replicated_sub_base
      (l := l) sample draws
      (fun _index assignment draw unit =>
        oneHotAssignmentIndicator assignment draw unit)
      assignment biasUnitContribution biasCorrectionError hbias_construct
  have hscore_component_construct :
      scoreReplicationError =ᶠ[l]
        (fun index =>
          ∑ component ∈ ({scoreComponent} : Finset ScoreComponent),
            ∑ unit ∈ sample index,
              (multinomialCountFromDrawIndicators (draws index)
                  (fun assignment draw unit =>
                    oneHotAssignmentIndicator assignment draw unit)
                  (assignment index) unit - 1) *
                (fun _component => scoreUnitContribution index unit)
                  component) := by
    filter_upwards [hscore_centered] with index hindex
    simpa using hindex
  have hbias_component_construct :
      biasCorrectionError =ᶠ[l]
        (fun index =>
          ∑ component ∈ ({biasComponent} : Finset BiasComponent),
            ∑ unit ∈ sample index,
              (multinomialCountFromDrawIndicators (draws index)
                  (fun assignment draw unit =>
                    oneHotAssignmentIndicator assignment draw unit)
                  (assignment index) unit - 1) *
                (fun _component => biasUnitContribution index unit)
                  component) := by
    filter_upwards [hbias_centered] with index hindex
    simpa using hindex
  exact
    tendsto_actualBootstrapVariance_of_eventually_cell_contribution_weight_limits_and_uniformAssignment_base_ratio_full_support_unit_envelope_bounds
      (l := l) cells ({scoreComponent} : Finset ScoreComponent)
      ({biasComponent} : Finset BiasComponent) sample draws assignment
      score contribution weight target denominator normalizer sampleSize
      cellContribution cellWeight contributionLimit weightLimit massLimit
      actualVariance scoreReplicationError biasCorrectionError
      (fun index unit _component => scoreUnitContribution index unit)
      (fun index unit _component => biasUnitContribution index unit)
      (fun index _component => scoreUnitEnvelope index)
      (fun index _component => biasUnitEnvelope index)
      hunit_card hdraw_card hsampleSize_ne hsample_univ hdraws_univ hbase
      hvariance_decomp hcover hcontributionCell hweightCell
      hcontributionLimit hweightLimit hmass hscore_component_construct
      (by
        filter_upwards [hscore_component_bound] with index hbound unit
          hunit component _hcomponent
        simpa using hbound unit hunit)
      (fun _component _hcomponent => by
        simpa using hscore_envelope_tendsto)
      hbias_component_construct
      (by
        filter_upwards [hbias_component_bound] with index hbound unit
          hunit component _hcomponent
        simpa using hbound unit hunit)
      (fun _component _hcomponent => by
        simpa using hbias_envelope_tendsto)

/--
Fixed full-support retrospective PATE/PATT manuscript-numerator companion for
the singleton uniform-assignment route.  Compared with the draw-count-scale
version, this derives the fixed draw-count scaling internally from eventual
full draw support and only asks for ordinary shrinking unit envelopes.
-/
theorem tendsto_actualBootstrapVariance_of_eventually_cell_contribution_weight_limits_and_uniformAssignment_base_ratio_full_support_retrospectivePATEPATT_linearized_numerator_unit_envelope_bounds
    [Fintype Unit] [Fintype Draw] [DecidableEq Unit] [DecidableEq Draw]
    [Nonempty Unit] [DecidableEq Cell] [DecidableEq ScoreComponent]
    [DecidableEq BiasComponent]
    (cells : Finset Cell)
    (scoreComponent : ScoreComponent)
    (biasComponent : BiasComponent)
    (sample : Index -> Finset Unit) (draws : Index -> Finset Draw)
    (assignment : Index -> Draw -> Unit)
    (score : Index -> Unit -> Cell)
    (contribution weight : Index -> Unit -> Real)
    (target denominator normalizer sampleSize : Real)
    (cellContribution cellWeight : Index -> Cell -> Real)
    (contributionLimit weightLimit massLimit : Cell -> Real)
    (actualVariance scoreReplicationError biasCorrectionError : Index -> Real)
    (scoreBaseWeight scoreReuseResidualWeight scoreHeterogeneity
      scoreResidual : Index -> Unit -> Real)
    (biasTreatedContribution biasControlReuseContribution :
      Index -> Unit -> Real)
    (scoreUnitEnvelope biasUnitEnvelope : Index -> Real)
    (hunit_card : (Fintype.card Unit : Real) = sampleSize)
    (hdraw_card : (Fintype.card Draw : Real) = sampleSize)
    (hsampleSize_ne : sampleSize ≠ 0)
    (hsample_univ :
      sample =ᶠ[l] fun _index => (Finset.univ : Finset Unit))
    (hdraws_univ :
      draws =ᶠ[l] fun _index => (Finset.univ : Finset Draw))
    (hbase :
      ∀ᶠ index in l,
        baseLinearizedSum (Finset.univ : Finset Unit)
            (contribution index) =
          target *
            baseLinearizedSum (Finset.univ : Finset Unit)
              (weight index))
    (hvariance_decomp :
      actualVariance =ᶠ[l]
        (fun index =>
          (1 / denominator ^ 2) * (1 / normalizer) *
              multiplierPerturbationSecondMoment
                (uniformAssignmentSupport Unit Draw)
                (uniformAssignmentMass Unit Draw)
                (sample index)
                (fun assignment unit =>
                  multinomialCountFromDrawIndicators (draws index)
                    (fun assignment draw unit =>
                      oneHotAssignmentIndicator assignment draw unit)
                    assignment unit)
                (fun unit =>
                  contribution index unit - target * weight index unit) +
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
    (hscore_construct :
      scoreReplicationError =ᶠ[l]
        (fun index =>
          retrospectivePATELinearizedBootstrapNumerator (sample index)
              (fun unit =>
                multinomialCountFromDrawIndicators (draws index)
                  (fun assignment draw unit =>
                    oneHotAssignmentIndicator assignment draw unit)
                  (assignment index) unit)
              (scoreBaseWeight index) (scoreReuseResidualWeight index)
              (scoreHeterogeneity index) (scoreResidual index) -
            baseLinearizedSum (sample index)
              (retrospectivePATEBootstrapInfluenceContribution
                (scoreBaseWeight index) (scoreReuseResidualWeight index)
                (scoreHeterogeneity index) (scoreResidual index))))
    (hscore_component_bound :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ sample index ->
          |retrospectivePATEBootstrapInfluenceContribution
              (scoreBaseWeight index) (scoreReuseResidualWeight index)
              (scoreHeterogeneity index) (scoreResidual index) unit| ≤
            scoreUnitEnvelope index)
    (hscore_envelope_tendsto :
      Tendsto scoreUnitEnvelope l (nhds 0))
    (hbias_construct :
      biasCorrectionError =ᶠ[l]
        (fun index =>
          retrospectivePATTLinearizedBootstrapNumerator (sample index)
              (fun unit =>
                multinomialCountFromDrawIndicators (draws index)
                  (fun assignment draw unit =>
                    oneHotAssignmentIndicator assignment draw unit)
                  (assignment index) unit)
              (biasTreatedContribution index)
              (biasControlReuseContribution index) -
            baseLinearizedSum (sample index)
              (retrospectivePATTBootstrapInfluenceContribution
                (biasTreatedContribution index)
                (biasControlReuseContribution index))))
    (hbias_component_bound :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ sample index ->
          |retrospectivePATTBootstrapInfluenceContribution
              (biasTreatedContribution index)
              (biasControlReuseContribution index) unit| ≤
            biasUnitEnvelope index)
    (hbias_envelope_tendsto :
      Tendsto biasUnitEnvelope l (nhds 0)) :
    Tendsto actualVariance l
      (nhds
        ((1 / denominator ^ 2) * (1 / normalizer) *
          weightedScoreCellMomentLimit cells
            (fun cell =>
              (contributionLimit cell - target * weightLimit cell) ^ 2)
            massLimit)) := by
  have hscore_replicated :
      scoreReplicationError =ᶠ[l]
        (fun index =>
          replicatedLinearizedSum (sample index)
              (fun unit =>
                multinomialCountFromDrawIndicators (draws index)
                  (fun assignment draw unit =>
                    oneHotAssignmentIndicator assignment draw unit)
                  (assignment index) unit)
              (retrospectivePATEBootstrapInfluenceContribution
                (scoreBaseWeight index) (scoreReuseResidualWeight index)
                (scoreHeterogeneity index) (scoreResidual index)) -
            baseLinearizedSum (sample index)
              (retrospectivePATEBootstrapInfluenceContribution
                (scoreBaseWeight index) (scoreReuseResidualWeight index)
                (scoreHeterogeneity index) (scoreResidual index))) :=
    eventually_error_eq_retrospectivePATE_replicatedLinearized_sub_base_of_linearized_numerator
      (l := l) sample draws
      (fun _index assignment draw unit =>
        oneHotAssignmentIndicator assignment draw unit)
      assignment scoreBaseWeight scoreReuseResidualWeight
      scoreHeterogeneity scoreResidual scoreReplicationError
      hscore_construct
  have hbias_replicated :
      biasCorrectionError =ᶠ[l]
        (fun index =>
          replicatedLinearizedSum (sample index)
              (fun unit =>
                multinomialCountFromDrawIndicators (draws index)
                  (fun assignment draw unit =>
                    oneHotAssignmentIndicator assignment draw unit)
                  (assignment index) unit)
              (retrospectivePATTBootstrapInfluenceContribution
                (biasTreatedContribution index)
                (biasControlReuseContribution index)) -
            baseLinearizedSum (sample index)
              (retrospectivePATTBootstrapInfluenceContribution
                (biasTreatedContribution index)
                (biasControlReuseContribution index))) :=
    eventually_error_eq_retrospectivePATT_replicatedLinearized_sub_base_of_linearized_numerator
      (l := l) sample draws
      (fun _index assignment draw unit =>
        oneHotAssignmentIndicator assignment draw unit)
      assignment biasTreatedContribution biasControlReuseContribution
      biasCorrectionError hbias_construct
  exact
    tendsto_actualBootstrapVariance_of_eventually_cell_contribution_weight_limits_and_uniformAssignment_base_ratio_full_support_singleton_replicatedLinearized_unit_envelope_bounds
      (l := l) cells scoreComponent biasComponent sample draws
      assignment score contribution weight target denominator normalizer
      sampleSize cellContribution cellWeight contributionLimit weightLimit
      massLimit actualVariance scoreReplicationError biasCorrectionError
      (fun index =>
        retrospectivePATEBootstrapInfluenceContribution
          (scoreBaseWeight index) (scoreReuseResidualWeight index)
          (scoreHeterogeneity index) (scoreResidual index))
      (fun index =>
        retrospectivePATTBootstrapInfluenceContribution
          (biasTreatedContribution index)
          (biasControlReuseContribution index))
      scoreUnitEnvelope biasUnitEnvelope hunit_card hdraw_card
      hsampleSize_ne hsample_univ hdraws_univ hbase hvariance_decomp
      hcover hcontributionCell hweightCell hcontributionLimit
      hweightLimit hmass hscore_replicated hscore_component_bound
      hscore_envelope_tendsto hbias_replicated hbias_component_bound
      hbias_envelope_tendsto

/--
Finite `L1(P)` bracketing supplies the score-cell mass LLN for the
full-support singleton replicated-linearized endpoint.
-/
theorem
    tendsto_actualBootstrapVariance_of_eventually_cell_contribution_weight_limits_l1BracketingNumber_obligations_and_uniformAssignment_base_ratio_full_support_singleton_replicatedLinearized_unit_envelope_bounds
    [Fintype Unit] [Fintype Draw] [DecidableEq Unit] [DecidableEq Draw]
    [Nonempty Unit] [DecidableEq Cell] [DecidableEq ScoreComponent]
    [DecidableEq BiasComponent]
    {Bracket : Type*} [Fintype Bracket]
    (cells : Finset Cell)
    (scoreComponent : ScoreComponent)
    (biasComponent : BiasComponent)
    (sample : ℕ -> Finset Unit) (draws : ℕ -> Finset Draw)
    (assignment : ℕ -> Draw -> Unit)
    (score : ℕ -> Unit -> Cell)
    (contribution weight : ℕ -> Unit -> Real)
    (target denominator normalizer sampleSize : Real)
    (cellContribution cellWeight : ℕ -> Cell -> Real)
    (contributionLimit weightLimit massLimit : Cell -> Real)
    (actualVariance scoreReplicationError biasCorrectionError : ℕ -> Real)
    (scoreUnitContribution biasUnitContribution : ℕ -> Unit -> Real)
    (scoreUnitEnvelope biasUnitEnvelope : ℕ -> Real)
    (hunit_card : (Fintype.card Unit : Real) = sampleSize)
    (hdraw_card : (Fintype.card Draw : Real) = sampleSize)
    (hsampleSize_ne : sampleSize ≠ 0)
    (hsample_univ :
      sample =ᶠ[atTop] fun _index => (Finset.univ : Finset Unit))
    (hdraws_univ :
      draws =ᶠ[atTop] fun _index => (Finset.univ : Finset Draw))
    (hbase :
      ∀ᶠ index in atTop,
        baseLinearizedSum (Finset.univ : Finset Unit)
            (contribution index) =
          target *
            baseLinearizedSum (Finset.univ : Finset Unit)
              (weight index))
    (hvariance_decomp :
      actualVariance =ᶠ[atTop]
        (fun index =>
          (1 / denominator ^ 2) * (1 / normalizer) *
              multiplierPerturbationSecondMoment
                (uniformAssignmentSupport Unit Draw)
                (uniformAssignmentMass Unit Draw)
                (sample index)
                (fun assignment unit =>
                  multinomialCountFromDrawIndicators (draws index)
                    (fun assignment draw unit =>
                      oneHotAssignmentIndicator assignment draw unit)
                    assignment unit)
                (fun unit =>
                  contribution index unit - target * weight index unit) +
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
    (hscore_construct :
      scoreReplicationError =ᶠ[atTop]
        (fun index =>
          replicatedLinearizedSum (sample index)
              (fun unit =>
                multinomialCountFromDrawIndicators (draws index)
                  (fun assignment draw unit =>
                    oneHotAssignmentIndicator assignment draw unit)
                  (assignment index) unit)
              (scoreUnitContribution index) -
            baseLinearizedSum (sample index)
              (scoreUnitContribution index)))
    (hscore_component_bound :
      ∀ᶠ index in atTop,
        ∀ unit, unit ∈ sample index ->
          |scoreUnitContribution index unit| ≤ scoreUnitEnvelope index)
    (hscore_envelope_tendsto :
      Tendsto scoreUnitEnvelope atTop (nhds 0))
    (hbias_construct :
      biasCorrectionError =ᶠ[atTop]
        (fun index =>
          replicatedLinearizedSum (sample index)
              (fun unit =>
                multinomialCountFromDrawIndicators (draws index)
                  (fun assignment draw unit =>
                    oneHotAssignmentIndicator assignment draw unit)
                  (assignment index) unit)
              (biasUnitContribution index) -
            baseLinearizedSum (sample index)
              (biasUnitContribution index)))
    (hbias_component_bound :
      ∀ᶠ index in atTop,
        ∀ unit, unit ∈ sample index ->
          |biasUnitContribution index unit| ≤ biasUnitEnvelope index)
    (hbias_envelope_tendsto :
      Tendsto biasUnitEnvelope atTop (nhds 0)) :
    Tendsto actualVariance atTop
      (nhds
        ((1 / denominator ^ 2) * (1 / normalizer) *
          weightedScoreCellMomentLimit cells
            (fun cell =>
              (contributionLimit cell - target * weightLimit cell) ^ 2)
            massLimit)) :=
  tendsto_actualBootstrapVariance_of_eventually_cell_contribution_weight_limits_and_uniformAssignment_base_ratio_full_support_singleton_replicatedLinearized_unit_envelope_bounds
    (l := atTop) cells scoreComponent biasComponent sample draws assignment
    score contribution weight target denominator normalizer sampleSize
    cellContribution cellWeight contributionLimit weightLimit massLimit
    actualVariance scoreReplicationError biasCorrectionError
    scoreUnitContribution biasUnitContribution scoreUnitEnvelope
    biasUnitEnvelope hunit_card hdraw_card hsampleSize_ne hsample_univ
    hdraws_univ hbase hvariance_decomp hcover hcontributionCell
    hweightCell hcontributionLimit hweightLimit
    (cellwise_mass_lln_of_glivenkoCantelli_bridge
      cells massLimit sample (fun _index _unit => 1) score
      (weighted_indicator_array_lln_of_l1BracketingNumber_obligations
        cells massLimit sample (fun _index _unit => 1) score obligations))
    hscore_construct hscore_component_bound hscore_envelope_tendsto
    hbias_construct hbias_component_bound hbias_envelope_tendsto

/--
VdV&W endpoint assemblies supply the score-cell mass LLN for the
full-support singleton replicated-linearized endpoint.
-/
theorem
    tendsto_actualBootstrapVariance_of_eventually_cell_contribution_weight_limits_vdvw241_endpoint_assembly_and_uniformAssignment_base_ratio_full_support_singleton_replicatedLinearized_unit_envelope_bounds
    [Fintype Unit] [Fintype Draw] [DecidableEq Unit] [DecidableEq Draw]
    [Nonempty Unit] [DecidableEq Cell] [DecidableEq ScoreComponent]
    [DecidableEq BiasComponent]
    {Bracket : Type*} [Fintype Bracket]
    (cells : Finset Cell)
    (scoreComponent : ScoreComponent)
    (biasComponent : BiasComponent)
    (sample : ℕ -> Finset Unit) (draws : ℕ -> Finset Draw)
    (assignment : ℕ -> Draw -> Unit)
    (score : ℕ -> Unit -> Cell)
    (contribution weight : ℕ -> Unit -> Real)
    (target denominator normalizer sampleSize : Real)
    (cellContribution cellWeight : ℕ -> Cell -> Real)
    (contributionLimit weightLimit massLimit : Cell -> Real)
    (actualVariance scoreReplicationError biasCorrectionError : ℕ -> Real)
    (scoreUnitContribution biasUnitContribution : ℕ -> Unit -> Real)
    (scoreUnitEnvelope biasUnitEnvelope : ℕ -> Real)
    (hunit_card : (Fintype.card Unit : Real) = sampleSize)
    (hdraw_card : (Fintype.card Draw : Real) = sampleSize)
    (hsampleSize_ne : sampleSize ≠ 0)
    (hsample_univ :
      sample =ᶠ[atTop] fun _index => (Finset.univ : Finset Unit))
    (hdraws_univ :
      draws =ᶠ[atTop] fun _index => (Finset.univ : Finset Draw))
    (hbase :
      ∀ᶠ index in atTop,
        baseLinearizedSum (Finset.univ : Finset Unit)
            (contribution index) =
          target *
            baseLinearizedSum (Finset.univ : Finset Unit)
              (weight index))
    (hvariance_decomp :
      actualVariance =ᶠ[atTop]
        (fun index =>
          (1 / denominator ^ 2) * (1 / normalizer) *
              multiplierPerturbationSecondMoment
                (uniformAssignmentSupport Unit Draw)
                (uniformAssignmentMass Unit Draw)
                (sample index)
                (fun assignment unit =>
                  multinomialCountFromDrawIndicators (draws index)
                    (fun assignment draw unit =>
                      oneHotAssignmentIndicator assignment draw unit)
                    assignment unit)
                (fun unit =>
                  contribution index unit - target * weight index unit) +
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
    (hscore_construct :
      scoreReplicationError =ᶠ[atTop]
        (fun index =>
          replicatedLinearizedSum (sample index)
              (fun unit =>
                multinomialCountFromDrawIndicators (draws index)
                  (fun assignment draw unit =>
                    oneHotAssignmentIndicator assignment draw unit)
                  (assignment index) unit)
              (scoreUnitContribution index) -
            baseLinearizedSum (sample index)
              (scoreUnitContribution index)))
    (hscore_component_bound :
      ∀ᶠ index in atTop,
        ∀ unit, unit ∈ sample index ->
          |scoreUnitContribution index unit| ≤ scoreUnitEnvelope index)
    (hscore_envelope_tendsto :
      Tendsto scoreUnitEnvelope atTop (nhds 0))
    (hbias_construct :
      biasCorrectionError =ᶠ[atTop]
        (fun index =>
          replicatedLinearizedSum (sample index)
              (fun unit =>
                multinomialCountFromDrawIndicators (draws index)
                  (fun assignment draw unit =>
                    oneHotAssignmentIndicator assignment draw unit)
                  (assignment index) unit)
              (biasUnitContribution index) -
            baseLinearizedSum (sample index)
              (biasUnitContribution index)))
    (hbias_component_bound :
      ∀ᶠ index in atTop,
        ∀ unit, unit ∈ sample index ->
          |biasUnitContribution index unit| ≤ biasUnitEnvelope index)
    (hbias_envelope_tendsto :
      Tendsto biasUnitEnvelope atTop (nhds 0)) :
    Tendsto actualVariance atTop
      (nhds
        ((1 / denominator ^ 2) * (1 / normalizer) *
          weightedScoreCellMomentLimit cells
            (fun cell =>
              (contributionLimit cell - target * weightLimit cell) ^ 2)
            massLimit)) :=
  tendsto_actualBootstrapVariance_of_eventually_cell_contribution_weight_limits_and_uniformAssignment_base_ratio_full_support_singleton_replicatedLinearized_unit_envelope_bounds
    (l := atTop) cells scoreComponent biasComponent sample draws assignment
    score contribution weight target denominator normalizer sampleSize
    cellContribution cellWeight contributionLimit weightLimit massLimit
    actualVariance scoreReplicationError biasCorrectionError
    scoreUnitContribution biasUnitContribution scoreUnitEnvelope
    biasUnitEnvelope hunit_card hdraw_card hsampleSize_ne hsample_univ
    hdraws_univ hbase hvariance_decomp hcover hcontributionCell
    hweightCell hcontributionLimit hweightLimit
    (cellwise_mass_lln_of_glivenkoCantelli_bridge
      cells massLimit sample (fun _index _unit => 1) score
      (weighted_indicator_array_lln_of_vdvw241_endpoint_assembly
        cells massLimit sample (fun _index _unit => 1) score assembly))
    hscore_construct hscore_component_bound hscore_envelope_tendsto
    hbias_construct hbias_component_bound hbias_envelope_tendsto

/--
Fixed full-support singleton route whose score-replication and
bias-correction constructions are stated over the literal full finite
supports.  Eventual full-support equalities transport the manuscript-style
`Finset.univ` replicated-linearized formulas to the sample/draw endpoint.
-/
theorem tendsto_actualBootstrapVariance_of_eventually_cell_contribution_weight_limits_and_uniformAssignment_base_ratio_full_support_univ_singleton_replicatedLinearized_unit_envelope_bounds
    [Fintype Unit] [Fintype Draw] [DecidableEq Unit] [DecidableEq Draw]
    [Nonempty Unit] [DecidableEq Cell] [DecidableEq ScoreComponent]
    [DecidableEq BiasComponent]
    (cells : Finset Cell)
    (scoreComponent : ScoreComponent)
    (biasComponent : BiasComponent)
    (sample : Index -> Finset Unit) (draws : Index -> Finset Draw)
    (assignment : Index -> Draw -> Unit)
    (score : Index -> Unit -> Cell)
    (contribution weight : Index -> Unit -> Real)
    (target denominator normalizer sampleSize : Real)
    (cellContribution cellWeight : Index -> Cell -> Real)
    (contributionLimit weightLimit massLimit : Cell -> Real)
    (actualVariance scoreReplicationError biasCorrectionError : Index -> Real)
    (scoreUnitContribution biasUnitContribution : Index -> Unit -> Real)
    (scoreUnitEnvelope biasUnitEnvelope : Index -> Real)
    (hunit_card : (Fintype.card Unit : Real) = sampleSize)
    (hdraw_card : (Fintype.card Draw : Real) = sampleSize)
    (hsampleSize_ne : sampleSize ≠ 0)
    (hsample_univ :
      sample =ᶠ[l] fun _index => (Finset.univ : Finset Unit))
    (hdraws_univ :
      draws =ᶠ[l] fun _index => (Finset.univ : Finset Draw))
    (hbase :
      ∀ᶠ index in l,
        baseLinearizedSum (Finset.univ : Finset Unit)
            (contribution index) =
          target *
            baseLinearizedSum (Finset.univ : Finset Unit)
              (weight index))
    (hvariance_decomp :
      actualVariance =ᶠ[l]
        (fun index =>
          (1 / denominator ^ 2) * (1 / normalizer) *
              multiplierPerturbationSecondMoment
                (uniformAssignmentSupport Unit Draw)
                (uniformAssignmentMass Unit Draw)
                (sample index)
                (fun assignment unit =>
                  multinomialCountFromDrawIndicators (draws index)
                    (fun assignment draw unit =>
                      oneHotAssignmentIndicator assignment draw unit)
                    assignment unit)
                (fun unit =>
                  contribution index unit - target * weight index unit) +
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
    (hscore_construct_univ :
      scoreReplicationError =ᶠ[l]
        (fun index =>
          replicatedLinearizedSum (Finset.univ : Finset Unit)
              (fun unit =>
                multinomialCountFromDrawIndicators
                  (Finset.univ : Finset Draw)
                  (fun assignment draw unit =>
                    oneHotAssignmentIndicator assignment draw unit)
                  (assignment index) unit)
              (scoreUnitContribution index) -
            baseLinearizedSum (Finset.univ : Finset Unit)
              (scoreUnitContribution index)))
    (hscore_component_bound :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ sample index ->
          |scoreUnitContribution index unit| ≤ scoreUnitEnvelope index)
    (hscore_envelope_tendsto :
      Tendsto scoreUnitEnvelope l (nhds 0))
    (hbias_construct_univ :
      biasCorrectionError =ᶠ[l]
        (fun index =>
          replicatedLinearizedSum (Finset.univ : Finset Unit)
              (fun unit =>
                multinomialCountFromDrawIndicators
                  (Finset.univ : Finset Draw)
                  (fun assignment draw unit =>
                    oneHotAssignmentIndicator assignment draw unit)
                  (assignment index) unit)
              (biasUnitContribution index) -
            baseLinearizedSum (Finset.univ : Finset Unit)
              (biasUnitContribution index)))
    (hbias_component_bound :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ sample index ->
          |biasUnitContribution index unit| ≤ biasUnitEnvelope index)
    (hbias_envelope_tendsto :
      Tendsto biasUnitEnvelope l (nhds 0)) :
    Tendsto actualVariance l
      (nhds
        ((1 / denominator ^ 2) * (1 / normalizer) *
          weightedScoreCellMomentLimit cells
            (fun cell =>
              (contributionLimit cell - target * weightLimit cell) ^ 2)
            massLimit)) := by
  have hscore_construct :
      scoreReplicationError =ᶠ[l]
        (fun index =>
          replicatedLinearizedSum (sample index)
              (fun unit =>
                multinomialCountFromDrawIndicators (draws index)
                  (fun assignment draw unit =>
                    oneHotAssignmentIndicator assignment draw unit)
                  (assignment index) unit)
              (scoreUnitContribution index) -
            baseLinearizedSum (sample index)
              (scoreUnitContribution index)) := by
    filter_upwards [hscore_construct_univ, hsample_univ, hdraws_univ] with
      index hconstruct hsample hdraws
    calc
      scoreReplicationError index =
          replicatedLinearizedSum (Finset.univ : Finset Unit)
              (fun unit =>
                multinomialCountFromDrawIndicators
                  (Finset.univ : Finset Draw)
                  (fun assignment draw unit =>
                    oneHotAssignmentIndicator assignment draw unit)
                  (assignment index) unit)
              (scoreUnitContribution index) -
            baseLinearizedSum (Finset.univ : Finset Unit)
              (scoreUnitContribution index) := hconstruct
      _ =
          replicatedLinearizedSum (sample index)
              (fun unit =>
                multinomialCountFromDrawIndicators (draws index)
                  (fun assignment draw unit =>
                    oneHotAssignmentIndicator assignment draw unit)
                  (assignment index) unit)
              (scoreUnitContribution index) -
            baseLinearizedSum (sample index)
              (scoreUnitContribution index) := by
            rw [hsample, hdraws]
  have hbias_construct :
      biasCorrectionError =ᶠ[l]
        (fun index =>
          replicatedLinearizedSum (sample index)
              (fun unit =>
                multinomialCountFromDrawIndicators (draws index)
                  (fun assignment draw unit =>
                    oneHotAssignmentIndicator assignment draw unit)
                  (assignment index) unit)
              (biasUnitContribution index) -
            baseLinearizedSum (sample index)
              (biasUnitContribution index)) := by
    filter_upwards [hbias_construct_univ, hsample_univ, hdraws_univ] with
      index hconstruct hsample hdraws
    calc
      biasCorrectionError index =
          replicatedLinearizedSum (Finset.univ : Finset Unit)
              (fun unit =>
                multinomialCountFromDrawIndicators
                  (Finset.univ : Finset Draw)
                  (fun assignment draw unit =>
                    oneHotAssignmentIndicator assignment draw unit)
                  (assignment index) unit)
              (biasUnitContribution index) -
            baseLinearizedSum (Finset.univ : Finset Unit)
              (biasUnitContribution index) := hconstruct
      _ =
          replicatedLinearizedSum (sample index)
              (fun unit =>
                multinomialCountFromDrawIndicators (draws index)
                  (fun assignment draw unit =>
                    oneHotAssignmentIndicator assignment draw unit)
                  (assignment index) unit)
              (biasUnitContribution index) -
            baseLinearizedSum (sample index)
              (biasUnitContribution index) := by
            rw [hsample, hdraws]
  exact
    tendsto_actualBootstrapVariance_of_eventually_cell_contribution_weight_limits_and_uniformAssignment_base_ratio_full_support_singleton_replicatedLinearized_unit_envelope_bounds
      (l := l) cells scoreComponent biasComponent sample draws assignment
      score contribution weight target denominator normalizer sampleSize
      cellContribution cellWeight contributionLimit weightLimit massLimit
      actualVariance scoreReplicationError biasCorrectionError
      scoreUnitContribution biasUnitContribution scoreUnitEnvelope
      biasUnitEnvelope hunit_card hdraw_card hsampleSize_ne hsample_univ
      hdraws_univ hbase hvariance_decomp hcover hcontributionCell
      hweightCell hcontributionLimit hweightLimit hmass hscore_construct
      hscore_component_bound hscore_envelope_tendsto hbias_construct
      hbias_component_bound hbias_envelope_tendsto

/--
Finite `L1(P)` bracketing supplies the score-cell mass LLN for the
full-support singleton route whose replicated-linearized constructions are
stated over `Finset.univ`.
-/
theorem
    tendsto_actualBootstrapVariance_of_eventually_cell_contribution_weight_limits_l1BracketingNumber_obligations_and_uniformAssignment_base_ratio_full_support_univ_singleton_replicatedLinearized_unit_envelope_bounds
    [Fintype Unit] [Fintype Draw] [DecidableEq Unit] [DecidableEq Draw]
    [Nonempty Unit] [DecidableEq Cell] [DecidableEq ScoreComponent]
    [DecidableEq BiasComponent]
    {Bracket : Type*} [Fintype Bracket]
    (cells : Finset Cell)
    (scoreComponent : ScoreComponent)
    (biasComponent : BiasComponent)
    (sample : ℕ -> Finset Unit) (draws : ℕ -> Finset Draw)
    (assignment : ℕ -> Draw -> Unit)
    (score : ℕ -> Unit -> Cell)
    (contribution weight : ℕ -> Unit -> Real)
    (target denominator normalizer sampleSize : Real)
    (cellContribution cellWeight : ℕ -> Cell -> Real)
    (contributionLimit weightLimit massLimit : Cell -> Real)
    (actualVariance scoreReplicationError biasCorrectionError : ℕ -> Real)
    (scoreUnitContribution biasUnitContribution : ℕ -> Unit -> Real)
    (scoreUnitEnvelope biasUnitEnvelope : ℕ -> Real)
    (hunit_card : (Fintype.card Unit : Real) = sampleSize)
    (hdraw_card : (Fintype.card Draw : Real) = sampleSize)
    (hsampleSize_ne : sampleSize ≠ 0)
    (hsample_univ :
      sample =ᶠ[atTop] fun _index => (Finset.univ : Finset Unit))
    (hdraws_univ :
      draws =ᶠ[atTop] fun _index => (Finset.univ : Finset Draw))
    (hbase :
      ∀ᶠ index in atTop,
        baseLinearizedSum (Finset.univ : Finset Unit)
            (contribution index) =
          target *
            baseLinearizedSum (Finset.univ : Finset Unit)
              (weight index))
    (hvariance_decomp :
      actualVariance =ᶠ[atTop]
        (fun index =>
          (1 / denominator ^ 2) * (1 / normalizer) *
              multiplierPerturbationSecondMoment
                (uniformAssignmentSupport Unit Draw)
                (uniformAssignmentMass Unit Draw)
                (sample index)
                (fun assignment unit =>
                  multinomialCountFromDrawIndicators (draws index)
                    (fun assignment draw unit =>
                      oneHotAssignmentIndicator assignment draw unit)
                    assignment unit)
                (fun unit =>
                  contribution index unit - target * weight index unit) +
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
    (hscore_construct_univ :
      scoreReplicationError =ᶠ[atTop]
        (fun index =>
          replicatedLinearizedSum (Finset.univ : Finset Unit)
              (fun unit =>
                multinomialCountFromDrawIndicators
                  (Finset.univ : Finset Draw)
                  (fun assignment draw unit =>
                    oneHotAssignmentIndicator assignment draw unit)
                  (assignment index) unit)
              (scoreUnitContribution index) -
            baseLinearizedSum (Finset.univ : Finset Unit)
              (scoreUnitContribution index)))
    (hscore_component_bound :
      ∀ᶠ index in atTop,
        ∀ unit, unit ∈ sample index ->
          |scoreUnitContribution index unit| ≤ scoreUnitEnvelope index)
    (hscore_envelope_tendsto :
      Tendsto scoreUnitEnvelope atTop (nhds 0))
    (hbias_construct_univ :
      biasCorrectionError =ᶠ[atTop]
        (fun index =>
          replicatedLinearizedSum (Finset.univ : Finset Unit)
              (fun unit =>
                multinomialCountFromDrawIndicators
                  (Finset.univ : Finset Draw)
                  (fun assignment draw unit =>
                    oneHotAssignmentIndicator assignment draw unit)
                  (assignment index) unit)
              (biasUnitContribution index) -
            baseLinearizedSum (Finset.univ : Finset Unit)
              (biasUnitContribution index)))
    (hbias_component_bound :
      ∀ᶠ index in atTop,
        ∀ unit, unit ∈ sample index ->
          |biasUnitContribution index unit| ≤ biasUnitEnvelope index)
    (hbias_envelope_tendsto :
      Tendsto biasUnitEnvelope atTop (nhds 0)) :
    Tendsto actualVariance atTop
      (nhds
        ((1 / denominator ^ 2) * (1 / normalizer) *
          weightedScoreCellMomentLimit cells
            (fun cell =>
              (contributionLimit cell - target * weightLimit cell) ^ 2)
            massLimit)) :=
  tendsto_actualBootstrapVariance_of_eventually_cell_contribution_weight_limits_and_uniformAssignment_base_ratio_full_support_univ_singleton_replicatedLinearized_unit_envelope_bounds
    (l := atTop) cells scoreComponent biasComponent sample draws assignment
    score contribution weight target denominator normalizer sampleSize
    cellContribution cellWeight contributionLimit weightLimit massLimit
    actualVariance scoreReplicationError biasCorrectionError
    scoreUnitContribution biasUnitContribution scoreUnitEnvelope
    biasUnitEnvelope hunit_card hdraw_card hsampleSize_ne hsample_univ
    hdraws_univ hbase hvariance_decomp hcover hcontributionCell
    hweightCell hcontributionLimit hweightLimit
    (cellwise_mass_lln_of_glivenkoCantelli_bridge
      cells massLimit sample (fun _index _unit => 1) score
      (weighted_indicator_array_lln_of_l1BracketingNumber_obligations
        cells massLimit sample (fun _index _unit => 1) score obligations))
    hscore_construct_univ hscore_component_bound hscore_envelope_tendsto
    hbias_construct_univ hbias_component_bound hbias_envelope_tendsto

/--
VdV&W endpoint assemblies supply the score-cell mass LLN for the
full-support singleton route whose replicated-linearized constructions are
stated over `Finset.univ`.
-/
theorem
    tendsto_actualBootstrapVariance_of_eventually_cell_contribution_weight_limits_vdvw241_endpoint_assembly_and_uniformAssignment_base_ratio_full_support_univ_singleton_replicatedLinearized_unit_envelope_bounds
    [Fintype Unit] [Fintype Draw] [DecidableEq Unit] [DecidableEq Draw]
    [Nonempty Unit] [DecidableEq Cell] [DecidableEq ScoreComponent]
    [DecidableEq BiasComponent]
    {Bracket : Type*} [Fintype Bracket]
    (cells : Finset Cell)
    (scoreComponent : ScoreComponent)
    (biasComponent : BiasComponent)
    (sample : ℕ -> Finset Unit) (draws : ℕ -> Finset Draw)
    (assignment : ℕ -> Draw -> Unit)
    (score : ℕ -> Unit -> Cell)
    (contribution weight : ℕ -> Unit -> Real)
    (target denominator normalizer sampleSize : Real)
    (cellContribution cellWeight : ℕ -> Cell -> Real)
    (contributionLimit weightLimit massLimit : Cell -> Real)
    (actualVariance scoreReplicationError biasCorrectionError : ℕ -> Real)
    (scoreUnitContribution biasUnitContribution : ℕ -> Unit -> Real)
    (scoreUnitEnvelope biasUnitEnvelope : ℕ -> Real)
    (hunit_card : (Fintype.card Unit : Real) = sampleSize)
    (hdraw_card : (Fintype.card Draw : Real) = sampleSize)
    (hsampleSize_ne : sampleSize ≠ 0)
    (hsample_univ :
      sample =ᶠ[atTop] fun _index => (Finset.univ : Finset Unit))
    (hdraws_univ :
      draws =ᶠ[atTop] fun _index => (Finset.univ : Finset Draw))
    (hbase :
      ∀ᶠ index in atTop,
        baseLinearizedSum (Finset.univ : Finset Unit)
            (contribution index) =
          target *
            baseLinearizedSum (Finset.univ : Finset Unit)
              (weight index))
    (hvariance_decomp :
      actualVariance =ᶠ[atTop]
        (fun index =>
          (1 / denominator ^ 2) * (1 / normalizer) *
              multiplierPerturbationSecondMoment
                (uniformAssignmentSupport Unit Draw)
                (uniformAssignmentMass Unit Draw)
                (sample index)
                (fun assignment unit =>
                  multinomialCountFromDrawIndicators (draws index)
                    (fun assignment draw unit =>
                      oneHotAssignmentIndicator assignment draw unit)
                    assignment unit)
                (fun unit =>
                  contribution index unit - target * weight index unit) +
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
    (hscore_construct_univ :
      scoreReplicationError =ᶠ[atTop]
        (fun index =>
          replicatedLinearizedSum (Finset.univ : Finset Unit)
              (fun unit =>
                multinomialCountFromDrawIndicators
                  (Finset.univ : Finset Draw)
                  (fun assignment draw unit =>
                    oneHotAssignmentIndicator assignment draw unit)
                  (assignment index) unit)
              (scoreUnitContribution index) -
            baseLinearizedSum (Finset.univ : Finset Unit)
              (scoreUnitContribution index)))
    (hscore_component_bound :
      ∀ᶠ index in atTop,
        ∀ unit, unit ∈ sample index ->
          |scoreUnitContribution index unit| ≤ scoreUnitEnvelope index)
    (hscore_envelope_tendsto :
      Tendsto scoreUnitEnvelope atTop (nhds 0))
    (hbias_construct_univ :
      biasCorrectionError =ᶠ[atTop]
        (fun index =>
          replicatedLinearizedSum (Finset.univ : Finset Unit)
              (fun unit =>
                multinomialCountFromDrawIndicators
                  (Finset.univ : Finset Draw)
                  (fun assignment draw unit =>
                    oneHotAssignmentIndicator assignment draw unit)
                  (assignment index) unit)
              (biasUnitContribution index) -
            baseLinearizedSum (Finset.univ : Finset Unit)
              (biasUnitContribution index)))
    (hbias_component_bound :
      ∀ᶠ index in atTop,
        ∀ unit, unit ∈ sample index ->
          |biasUnitContribution index unit| ≤ biasUnitEnvelope index)
    (hbias_envelope_tendsto :
      Tendsto biasUnitEnvelope atTop (nhds 0)) :
    Tendsto actualVariance atTop
      (nhds
        ((1 / denominator ^ 2) * (1 / normalizer) *
          weightedScoreCellMomentLimit cells
            (fun cell =>
              (contributionLimit cell - target * weightLimit cell) ^ 2)
            massLimit)) :=
  tendsto_actualBootstrapVariance_of_eventually_cell_contribution_weight_limits_and_uniformAssignment_base_ratio_full_support_univ_singleton_replicatedLinearized_unit_envelope_bounds
    (l := atTop) cells scoreComponent biasComponent sample draws assignment
    score contribution weight target denominator normalizer sampleSize
    cellContribution cellWeight contributionLimit weightLimit massLimit
    actualVariance scoreReplicationError biasCorrectionError
    scoreUnitContribution biasUnitContribution scoreUnitEnvelope
    biasUnitEnvelope hunit_card hdraw_card hsampleSize_ne hsample_univ
    hdraws_univ hbase hvariance_decomp hcover hcontributionCell
    hweightCell hcontributionLimit hweightLimit
    (cellwise_mass_lln_of_glivenkoCantelli_bridge
      cells massLimit sample (fun _index _unit => 1) score
      (weighted_indicator_array_lln_of_vdvw241_endpoint_assembly
        cells massLimit sample (fun _index _unit => 1) score assembly))
    hscore_construct_univ hscore_component_bound hscore_envelope_tendsto
    hbias_construct_univ hbias_component_bound hbias_envelope_tendsto

/--
All-unit version of the full-support singleton `Finset.univ`
replicated-linearized route.  The coverage, cell-identification, and
component-bound premises are stated over all units, matching the fixed
full-support bootstrap convention.
-/
theorem tendsto_actualBootstrapVariance_of_eventually_cell_contribution_weight_limits_and_uniformAssignment_base_ratio_full_support_univ_singleton_replicatedLinearized_all_unit_envelope_bounds
    [Fintype Unit] [Fintype Draw] [DecidableEq Unit] [DecidableEq Draw]
    [Nonempty Unit] [DecidableEq Cell] [DecidableEq ScoreComponent]
    [DecidableEq BiasComponent]
    (cells : Finset Cell)
    (scoreComponent : ScoreComponent)
    (biasComponent : BiasComponent)
    (sample : Index -> Finset Unit) (draws : Index -> Finset Draw)
    (assignment : Index -> Draw -> Unit)
    (score : Index -> Unit -> Cell)
    (contribution weight : Index -> Unit -> Real)
    (target denominator normalizer sampleSize : Real)
    (cellContribution cellWeight : Index -> Cell -> Real)
    (contributionLimit weightLimit massLimit : Cell -> Real)
    (actualVariance scoreReplicationError biasCorrectionError : Index -> Real)
    (scoreUnitContribution biasUnitContribution : Index -> Unit -> Real)
    (scoreUnitEnvelope biasUnitEnvelope : Index -> Real)
    (hunit_card : (Fintype.card Unit : Real) = sampleSize)
    (hdraw_card : (Fintype.card Draw : Real) = sampleSize)
    (hsampleSize_ne : sampleSize ≠ 0)
    (hsample_univ :
      sample =ᶠ[l] fun _index => (Finset.univ : Finset Unit))
    (hdraws_univ :
      draws =ᶠ[l] fun _index => (Finset.univ : Finset Draw))
    (hbase :
      ∀ᶠ index in l,
        baseLinearizedSum (Finset.univ : Finset Unit)
            (contribution index) =
          target *
            baseLinearizedSum (Finset.univ : Finset Unit)
              (weight index))
    (hvariance_decomp :
      actualVariance =ᶠ[l]
        (fun index =>
          (1 / denominator ^ 2) * (1 / normalizer) *
              multiplierPerturbationSecondMoment
                (uniformAssignmentSupport Unit Draw)
                (uniformAssignmentMass Unit Draw)
                (sample index)
                (fun assignment unit =>
                  multinomialCountFromDrawIndicators (draws index)
                    (fun assignment draw unit =>
                      oneHotAssignmentIndicator assignment draw unit)
                    assignment unit)
                (fun unit =>
                  contribution index unit - target * weight index unit) +
            scoreReplicationError index + biasCorrectionError index))
    (hcover_all :
      ∀ᶠ index in l,
        ∀ unit, score index unit ∈ cells)
    (hcontributionCell_all :
      ∀ᶠ index in l,
        ∀ unit,
          cellContribution index (score index unit) =
            contribution index unit)
    (hweightCell_all :
      ∀ᶠ index in l,
        ∀ unit,
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
    (hscore_construct_univ :
      scoreReplicationError =ᶠ[l]
        (fun index =>
          replicatedLinearizedSum (Finset.univ : Finset Unit)
              (fun unit =>
                multinomialCountFromDrawIndicators
                  (Finset.univ : Finset Draw)
                  (fun assignment draw unit =>
                    oneHotAssignmentIndicator assignment draw unit)
                  (assignment index) unit)
              (scoreUnitContribution index) -
            baseLinearizedSum (Finset.univ : Finset Unit)
              (scoreUnitContribution index)))
    (hscore_component_bound_all :
      ∀ᶠ index in l,
        ∀ unit,
          |scoreUnitContribution index unit| ≤ scoreUnitEnvelope index)
    (hscore_envelope_tendsto :
      Tendsto scoreUnitEnvelope l (nhds 0))
    (hbias_construct_univ :
      biasCorrectionError =ᶠ[l]
        (fun index =>
          replicatedLinearizedSum (Finset.univ : Finset Unit)
              (fun unit =>
                multinomialCountFromDrawIndicators
                  (Finset.univ : Finset Draw)
                  (fun assignment draw unit =>
                    oneHotAssignmentIndicator assignment draw unit)
                  (assignment index) unit)
              (biasUnitContribution index) -
            baseLinearizedSum (Finset.univ : Finset Unit)
              (biasUnitContribution index)))
    (hbias_component_bound_all :
      ∀ᶠ index in l,
        ∀ unit,
          |biasUnitContribution index unit| ≤ biasUnitEnvelope index)
    (hbias_envelope_tendsto :
      Tendsto biasUnitEnvelope l (nhds 0)) :
    Tendsto actualVariance l
      (nhds
        ((1 / denominator ^ 2) * (1 / normalizer) *
          weightedScoreCellMomentLimit cells
            (fun cell =>
              (contributionLimit cell - target * weightLimit cell) ^ 2)
            massLimit)) := by
  have hcover :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ sample index -> score index unit ∈ cells := by
    filter_upwards [hcover_all] with index hcover_index unit _hunit
    exact hcover_index unit
  have hcontributionCell :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ sample index ->
          cellContribution index (score index unit) =
            contribution index unit := by
    filter_upwards [hcontributionCell_all] with index hcell_index unit _hunit
    exact hcell_index unit
  have hweightCell :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ sample index ->
          cellWeight index (score index unit) = weight index unit := by
    filter_upwards [hweightCell_all] with index hcell_index unit _hunit
    exact hcell_index unit
  have hscore_component_bound :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ sample index ->
          |scoreUnitContribution index unit| ≤ scoreUnitEnvelope index := by
    filter_upwards [hscore_component_bound_all] with
      index hbound_index unit _hunit
    exact hbound_index unit
  have hbias_component_bound :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ sample index ->
          |biasUnitContribution index unit| ≤ biasUnitEnvelope index := by
    filter_upwards [hbias_component_bound_all] with
      index hbound_index unit _hunit
    exact hbound_index unit
  exact
    tendsto_actualBootstrapVariance_of_eventually_cell_contribution_weight_limits_and_uniformAssignment_base_ratio_full_support_univ_singleton_replicatedLinearized_unit_envelope_bounds
      (l := l) cells scoreComponent biasComponent sample draws assignment
      score contribution weight target denominator normalizer sampleSize
      cellContribution cellWeight contributionLimit weightLimit massLimit
      actualVariance scoreReplicationError biasCorrectionError
      scoreUnitContribution biasUnitContribution scoreUnitEnvelope
      biasUnitEnvelope hunit_card hdraw_card hsampleSize_ne hsample_univ
      hdraws_univ hbase hvariance_decomp hcover hcontributionCell
      hweightCell hcontributionLimit hweightLimit hmass
      hscore_construct_univ hscore_component_bound hscore_envelope_tendsto
      hbias_construct_univ hbias_component_bound hbias_envelope_tendsto

/--
Finite `L1(P)` bracketing version of the all-unit singleton
`Finset.univ` replicated-linearized route.  The score-cell mass LLN is
derived from bracketing obligations, while deterministic support and envelope
fields remain stated over all units.
-/
theorem
    tendsto_actualBootstrapVariance_of_eventually_cell_contribution_weight_limits_l1BracketingNumber_obligations_and_uniformAssignment_base_ratio_full_support_univ_singleton_replicatedLinearized_all_unit_envelope_bounds
    [Fintype Unit] [Fintype Draw] [DecidableEq Unit] [DecidableEq Draw]
    [Nonempty Unit] [DecidableEq Cell] [DecidableEq ScoreComponent]
    [DecidableEq BiasComponent]
    {Bracket : Type*} [Fintype Bracket]
    (cells : Finset Cell)
    (scoreComponent : ScoreComponent)
    (biasComponent : BiasComponent)
    (sample : ℕ -> Finset Unit) (draws : ℕ -> Finset Draw)
    (assignment : ℕ -> Draw -> Unit)
    (score : ℕ -> Unit -> Cell)
    (contribution weight : ℕ -> Unit -> Real)
    (target denominator normalizer sampleSize : Real)
    (cellContribution cellWeight : ℕ -> Cell -> Real)
    (contributionLimit weightLimit massLimit : Cell -> Real)
    (actualVariance scoreReplicationError biasCorrectionError : ℕ -> Real)
    (scoreUnitContribution biasUnitContribution : ℕ -> Unit -> Real)
    (scoreUnitEnvelope biasUnitEnvelope : ℕ -> Real)
    (hunit_card : (Fintype.card Unit : Real) = sampleSize)
    (hdraw_card : (Fintype.card Draw : Real) = sampleSize)
    (hsampleSize_ne : sampleSize ≠ 0)
    (hsample_univ :
      sample =ᶠ[atTop] fun _index => (Finset.univ : Finset Unit))
    (hdraws_univ :
      draws =ᶠ[atTop] fun _index => (Finset.univ : Finset Draw))
    (hbase :
      ∀ᶠ index in atTop,
        baseLinearizedSum (Finset.univ : Finset Unit)
            (contribution index) =
          target *
            baseLinearizedSum (Finset.univ : Finset Unit)
              (weight index))
    (hvariance_decomp :
      actualVariance =ᶠ[atTop]
        (fun index =>
          (1 / denominator ^ 2) * (1 / normalizer) *
              multiplierPerturbationSecondMoment
                (uniformAssignmentSupport Unit Draw)
                (uniformAssignmentMass Unit Draw)
                (sample index)
                (fun assignment unit =>
                  multinomialCountFromDrawIndicators (draws index)
                    (fun assignment draw unit =>
                      oneHotAssignmentIndicator assignment draw unit)
                    assignment unit)
                (fun unit =>
                  contribution index unit - target * weight index unit) +
            scoreReplicationError index + biasCorrectionError index))
    (hcover_all :
      ∀ᶠ index in atTop,
        ∀ unit, score index unit ∈ cells)
    (hcontributionCell_all :
      ∀ᶠ index in atTop,
        ∀ unit,
          cellContribution index (score index unit) =
            contribution index unit)
    (hweightCell_all :
      ∀ᶠ index in atTop,
        ∀ unit,
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
    (hscore_construct_univ :
      scoreReplicationError =ᶠ[atTop]
        (fun index =>
          replicatedLinearizedSum (Finset.univ : Finset Unit)
              (fun unit =>
                multinomialCountFromDrawIndicators
                  (Finset.univ : Finset Draw)
                  (fun assignment draw unit =>
                    oneHotAssignmentIndicator assignment draw unit)
                  (assignment index) unit)
              (scoreUnitContribution index) -
            baseLinearizedSum (Finset.univ : Finset Unit)
              (scoreUnitContribution index)))
    (hscore_component_bound_all :
      ∀ᶠ index in atTop,
        ∀ unit,
          |scoreUnitContribution index unit| ≤ scoreUnitEnvelope index)
    (hscore_envelope_tendsto :
      Tendsto scoreUnitEnvelope atTop (nhds 0))
    (hbias_construct_univ :
      biasCorrectionError =ᶠ[atTop]
        (fun index =>
          replicatedLinearizedSum (Finset.univ : Finset Unit)
              (fun unit =>
                multinomialCountFromDrawIndicators
                  (Finset.univ : Finset Draw)
                  (fun assignment draw unit =>
                    oneHotAssignmentIndicator assignment draw unit)
                  (assignment index) unit)
              (biasUnitContribution index) -
            baseLinearizedSum (Finset.univ : Finset Unit)
              (biasUnitContribution index)))
    (hbias_component_bound_all :
      ∀ᶠ index in atTop,
        ∀ unit,
          |biasUnitContribution index unit| ≤ biasUnitEnvelope index)
    (hbias_envelope_tendsto :
      Tendsto biasUnitEnvelope atTop (nhds 0)) :
    Tendsto actualVariance atTop
      (nhds
        ((1 / denominator ^ 2) * (1 / normalizer) *
          weightedScoreCellMomentLimit cells
            (fun cell =>
              (contributionLimit cell - target * weightLimit cell) ^ 2)
            massLimit)) :=
  tendsto_actualBootstrapVariance_of_eventually_cell_contribution_weight_limits_and_uniformAssignment_base_ratio_full_support_univ_singleton_replicatedLinearized_all_unit_envelope_bounds
    (l := atTop) cells scoreComponent biasComponent sample draws assignment
    score contribution weight target denominator normalizer sampleSize
    cellContribution cellWeight contributionLimit weightLimit massLimit
    actualVariance scoreReplicationError biasCorrectionError
    scoreUnitContribution biasUnitContribution scoreUnitEnvelope
    biasUnitEnvelope hunit_card hdraw_card hsampleSize_ne hsample_univ
    hdraws_univ hbase hvariance_decomp hcover_all hcontributionCell_all
    hweightCell_all hcontributionLimit hweightLimit
    (cellwise_mass_lln_of_glivenkoCantelli_bridge
      cells massLimit sample (fun _index _unit => 1) score
      (weighted_indicator_array_lln_of_l1BracketingNumber_obligations
        cells massLimit sample (fun _index _unit => 1) score obligations))
    hscore_construct_univ hscore_component_bound_all
    hscore_envelope_tendsto hbias_construct_univ
    hbias_component_bound_all hbias_envelope_tendsto

/--
VdV&W endpoint-assembly version of the all-unit singleton `Finset.univ`
replicated-linearized route.  Endpoint evidence supplies the score-cell mass
LLN internally.
-/
theorem
    tendsto_actualBootstrapVariance_of_eventually_cell_contribution_weight_limits_vdvw241_endpoint_assembly_and_uniformAssignment_base_ratio_full_support_univ_singleton_replicatedLinearized_all_unit_envelope_bounds
    [Fintype Unit] [Fintype Draw] [DecidableEq Unit] [DecidableEq Draw]
    [Nonempty Unit] [DecidableEq Cell] [DecidableEq ScoreComponent]
    [DecidableEq BiasComponent]
    {Bracket : Type*} [Fintype Bracket]
    (cells : Finset Cell)
    (scoreComponent : ScoreComponent)
    (biasComponent : BiasComponent)
    (sample : ℕ -> Finset Unit) (draws : ℕ -> Finset Draw)
    (assignment : ℕ -> Draw -> Unit)
    (score : ℕ -> Unit -> Cell)
    (contribution weight : ℕ -> Unit -> Real)
    (target denominator normalizer sampleSize : Real)
    (cellContribution cellWeight : ℕ -> Cell -> Real)
    (contributionLimit weightLimit massLimit : Cell -> Real)
    (actualVariance scoreReplicationError biasCorrectionError : ℕ -> Real)
    (scoreUnitContribution biasUnitContribution : ℕ -> Unit -> Real)
    (scoreUnitEnvelope biasUnitEnvelope : ℕ -> Real)
    (hunit_card : (Fintype.card Unit : Real) = sampleSize)
    (hdraw_card : (Fintype.card Draw : Real) = sampleSize)
    (hsampleSize_ne : sampleSize ≠ 0)
    (hsample_univ :
      sample =ᶠ[atTop] fun _index => (Finset.univ : Finset Unit))
    (hdraws_univ :
      draws =ᶠ[atTop] fun _index => (Finset.univ : Finset Draw))
    (hbase :
      ∀ᶠ index in atTop,
        baseLinearizedSum (Finset.univ : Finset Unit)
            (contribution index) =
          target *
            baseLinearizedSum (Finset.univ : Finset Unit)
              (weight index))
    (hvariance_decomp :
      actualVariance =ᶠ[atTop]
        (fun index =>
          (1 / denominator ^ 2) * (1 / normalizer) *
              multiplierPerturbationSecondMoment
                (uniformAssignmentSupport Unit Draw)
                (uniformAssignmentMass Unit Draw)
                (sample index)
                (fun assignment unit =>
                  multinomialCountFromDrawIndicators (draws index)
                    (fun assignment draw unit =>
                      oneHotAssignmentIndicator assignment draw unit)
                    assignment unit)
                (fun unit =>
                  contribution index unit - target * weight index unit) +
            scoreReplicationError index + biasCorrectionError index))
    (hcover_all :
      ∀ᶠ index in atTop,
        ∀ unit, score index unit ∈ cells)
    (hcontributionCell_all :
      ∀ᶠ index in atTop,
        ∀ unit,
          cellContribution index (score index unit) =
            contribution index unit)
    (hweightCell_all :
      ∀ᶠ index in atTop,
        ∀ unit,
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
    (hscore_construct_univ :
      scoreReplicationError =ᶠ[atTop]
        (fun index =>
          replicatedLinearizedSum (Finset.univ : Finset Unit)
              (fun unit =>
                multinomialCountFromDrawIndicators
                  (Finset.univ : Finset Draw)
                  (fun assignment draw unit =>
                    oneHotAssignmentIndicator assignment draw unit)
                  (assignment index) unit)
              (scoreUnitContribution index) -
            baseLinearizedSum (Finset.univ : Finset Unit)
              (scoreUnitContribution index)))
    (hscore_component_bound_all :
      ∀ᶠ index in atTop,
        ∀ unit,
          |scoreUnitContribution index unit| ≤ scoreUnitEnvelope index)
    (hscore_envelope_tendsto :
      Tendsto scoreUnitEnvelope atTop (nhds 0))
    (hbias_construct_univ :
      biasCorrectionError =ᶠ[atTop]
        (fun index =>
          replicatedLinearizedSum (Finset.univ : Finset Unit)
              (fun unit =>
                multinomialCountFromDrawIndicators
                  (Finset.univ : Finset Draw)
                  (fun assignment draw unit =>
                    oneHotAssignmentIndicator assignment draw unit)
                  (assignment index) unit)
              (biasUnitContribution index) -
            baseLinearizedSum (Finset.univ : Finset Unit)
              (biasUnitContribution index)))
    (hbias_component_bound_all :
      ∀ᶠ index in atTop,
        ∀ unit,
          |biasUnitContribution index unit| ≤ biasUnitEnvelope index)
    (hbias_envelope_tendsto :
      Tendsto biasUnitEnvelope atTop (nhds 0)) :
    Tendsto actualVariance atTop
      (nhds
        ((1 / denominator ^ 2) * (1 / normalizer) *
          weightedScoreCellMomentLimit cells
            (fun cell =>
              (contributionLimit cell - target * weightLimit cell) ^ 2)
            massLimit)) :=
  tendsto_actualBootstrapVariance_of_eventually_cell_contribution_weight_limits_and_uniformAssignment_base_ratio_full_support_univ_singleton_replicatedLinearized_all_unit_envelope_bounds
    (l := atTop) cells scoreComponent biasComponent sample draws assignment
    score contribution weight target denominator normalizer sampleSize
    cellContribution cellWeight contributionLimit weightLimit massLimit
    actualVariance scoreReplicationError biasCorrectionError
    scoreUnitContribution biasUnitContribution scoreUnitEnvelope
    biasUnitEnvelope hunit_card hdraw_card hsampleSize_ne hsample_univ
    hdraws_univ hbase hvariance_decomp hcover_all hcontributionCell_all
    hweightCell_all hcontributionLimit hweightLimit
    (cellwise_mass_lln_of_glivenkoCantelli_bridge
      cells massLimit sample (fun _index _unit => 1) score
      (weighted_indicator_array_lln_of_vdvw241_endpoint_assembly
        cells massLimit sample (fun _index _unit => 1) score assembly))
    hscore_construct_univ hscore_component_bound_all
    hscore_envelope_tendsto hbias_construct_univ
    hbias_component_bound_all hbias_envelope_tendsto

/--
All-unit singleton full-support route where the base-sum identity is derived
from the paper-facing finite Hájek ratio equality.
-/
theorem tendsto_actualBootstrapVariance_of_eventually_cell_contribution_weight_limits_and_uniformAssignment_hajek_base_ratio_full_support_univ_singleton_replicatedLinearized_all_unit_envelope_bounds
    [Fintype Unit] [Fintype Draw] [DecidableEq Unit] [DecidableEq Draw]
    [Nonempty Unit] [DecidableEq Cell] [DecidableEq ScoreComponent]
    [DecidableEq BiasComponent]
    (cells : Finset Cell)
    (scoreComponent : ScoreComponent)
    (biasComponent : BiasComponent)
    (sample : Index -> Finset Unit) (draws : Index -> Finset Draw)
    (assignment : Index -> Draw -> Unit)
    (score : Index -> Unit -> Cell)
    (contribution weight : Index -> Unit -> Real)
    (target denominator normalizer sampleSize : Real)
    (cellContribution cellWeight : Index -> Cell -> Real)
    (contributionLimit weightLimit massLimit : Cell -> Real)
    (actualVariance scoreReplicationError biasCorrectionError : Index -> Real)
    (scoreUnitContribution biasUnitContribution : Index -> Unit -> Real)
    (scoreUnitEnvelope biasUnitEnvelope : Index -> Real)
    (hunit_card : (Fintype.card Unit : Real) = sampleSize)
    (hdraw_card : (Fintype.card Draw : Real) = sampleSize)
    (hsampleSize_ne : sampleSize ≠ 0)
    (hsample_univ :
      sample =ᶠ[l] fun _index => (Finset.univ : Finset Unit))
    (hdraws_univ :
      draws =ᶠ[l] fun _index => (Finset.univ : Finset Draw))
    (hbase_den_ne :
      ∀ᶠ index in l,
        baseLinearizedSum (Finset.univ : Finset Unit)
          (weight index) ≠ 0)
    (hbase_ratio :
      ∀ᶠ index in l,
        baseLinearizedSum (Finset.univ : Finset Unit)
            (contribution index) /
          baseLinearizedSum (Finset.univ : Finset Unit)
            (weight index) =
          target)
    (hvariance_decomp :
      actualVariance =ᶠ[l]
        (fun index =>
          (1 / denominator ^ 2) * (1 / normalizer) *
              multiplierPerturbationSecondMoment
                (uniformAssignmentSupport Unit Draw)
                (uniformAssignmentMass Unit Draw)
                (sample index)
                (fun assignment unit =>
                  multinomialCountFromDrawIndicators (draws index)
                    (fun assignment draw unit =>
                      oneHotAssignmentIndicator assignment draw unit)
                    assignment unit)
                (fun unit =>
                  contribution index unit - target * weight index unit) +
            scoreReplicationError index + biasCorrectionError index))
    (hcover_all :
      ∀ᶠ index in l,
        ∀ unit, score index unit ∈ cells)
    (hcontributionCell_all :
      ∀ᶠ index in l,
        ∀ unit,
          cellContribution index (score index unit) =
            contribution index unit)
    (hweightCell_all :
      ∀ᶠ index in l,
        ∀ unit,
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
    (hscore_construct_univ :
      scoreReplicationError =ᶠ[l]
        (fun index =>
          replicatedLinearizedSum (Finset.univ : Finset Unit)
              (fun unit =>
                multinomialCountFromDrawIndicators
                  (Finset.univ : Finset Draw)
                  (fun assignment draw unit =>
                    oneHotAssignmentIndicator assignment draw unit)
                  (assignment index) unit)
              (scoreUnitContribution index) -
            baseLinearizedSum (Finset.univ : Finset Unit)
              (scoreUnitContribution index)))
    (hscore_component_bound_all :
      ∀ᶠ index in l,
        ∀ unit,
          |scoreUnitContribution index unit| ≤ scoreUnitEnvelope index)
    (hscore_envelope_tendsto :
      Tendsto scoreUnitEnvelope l (nhds 0))
    (hbias_construct_univ :
      biasCorrectionError =ᶠ[l]
        (fun index =>
          replicatedLinearizedSum (Finset.univ : Finset Unit)
              (fun unit =>
                multinomialCountFromDrawIndicators
                  (Finset.univ : Finset Draw)
                  (fun assignment draw unit =>
                    oneHotAssignmentIndicator assignment draw unit)
                  (assignment index) unit)
              (biasUnitContribution index) -
            baseLinearizedSum (Finset.univ : Finset Unit)
              (biasUnitContribution index)))
    (hbias_component_bound_all :
      ∀ᶠ index in l,
        ∀ unit,
          |biasUnitContribution index unit| ≤ biasUnitEnvelope index)
    (hbias_envelope_tendsto :
      Tendsto biasUnitEnvelope l (nhds 0)) :
    Tendsto actualVariance l
      (nhds
        ((1 / denominator ^ 2) * (1 / normalizer) *
          weightedScoreCellMomentLimit cells
            (fun cell =>
              (contributionLimit cell - target * weightLimit cell) ^ 2)
            massLimit)) := by
  have hbase :
      ∀ᶠ index in l,
        baseLinearizedSum (Finset.univ : Finset Unit)
            (contribution index) =
          target *
            baseLinearizedSum (Finset.univ : Finset Unit)
              (weight index) := by
    filter_upwards [hbase_den_ne, hbase_ratio] with index hden hratio
    exact
      baseLinearizedSum_eq_target_mul_of_hajek_ratio_eq
        (Finset.univ : Finset Unit) (contribution index) (weight index)
        target hden hratio
  exact
    tendsto_actualBootstrapVariance_of_eventually_cell_contribution_weight_limits_and_uniformAssignment_base_ratio_full_support_univ_singleton_replicatedLinearized_all_unit_envelope_bounds
      (l := l) cells scoreComponent biasComponent sample draws assignment
      score contribution weight target denominator normalizer sampleSize
      cellContribution cellWeight contributionLimit weightLimit massLimit
      actualVariance scoreReplicationError biasCorrectionError
      scoreUnitContribution biasUnitContribution scoreUnitEnvelope
      biasUnitEnvelope hunit_card hdraw_card hsampleSize_ne hsample_univ
      hdraws_univ hbase hvariance_decomp hcover_all hcontributionCell_all
      hweightCell_all hcontributionLimit hweightLimit hmass
      hscore_construct_univ hscore_component_bound_all
      hscore_envelope_tendsto hbias_construct_univ
      hbias_component_bound_all hbias_envelope_tendsto

/--
Finite `L1(P)` bracketing version of the singleton all-unit route where the
base identity is supplied as a finite Hájek ratio equality.
-/
theorem
    tendsto_actualBootstrapVariance_of_eventually_cell_contribution_weight_limits_l1BracketingNumber_obligations_and_uniformAssignment_hajek_base_ratio_full_support_univ_singleton_replicatedLinearized_all_unit_envelope_bounds
    [Fintype Unit] [Fintype Draw] [DecidableEq Unit] [DecidableEq Draw]
    [Nonempty Unit] [DecidableEq Cell] [DecidableEq ScoreComponent]
    [DecidableEq BiasComponent]
    {Bracket : Type*} [Fintype Bracket]
    (cells : Finset Cell)
    (scoreComponent : ScoreComponent)
    (biasComponent : BiasComponent)
    (sample : ℕ -> Finset Unit) (draws : ℕ -> Finset Draw)
    (assignment : ℕ -> Draw -> Unit)
    (score : ℕ -> Unit -> Cell)
    (contribution weight : ℕ -> Unit -> Real)
    (target denominator normalizer sampleSize : Real)
    (cellContribution cellWeight : ℕ -> Cell -> Real)
    (contributionLimit weightLimit massLimit : Cell -> Real)
    (actualVariance scoreReplicationError biasCorrectionError : ℕ -> Real)
    (scoreUnitContribution biasUnitContribution : ℕ -> Unit -> Real)
    (scoreUnitEnvelope biasUnitEnvelope : ℕ -> Real)
    (hunit_card : (Fintype.card Unit : Real) = sampleSize)
    (hdraw_card : (Fintype.card Draw : Real) = sampleSize)
    (hsampleSize_ne : sampleSize ≠ 0)
    (hsample_univ :
      sample =ᶠ[atTop] fun _index => (Finset.univ : Finset Unit))
    (hdraws_univ :
      draws =ᶠ[atTop] fun _index => (Finset.univ : Finset Draw))
    (hbase_den_ne :
      ∀ᶠ index in atTop,
        baseLinearizedSum (Finset.univ : Finset Unit)
          (weight index) ≠ 0)
    (hbase_ratio :
      ∀ᶠ index in atTop,
        baseLinearizedSum (Finset.univ : Finset Unit)
            (contribution index) /
          baseLinearizedSum (Finset.univ : Finset Unit)
            (weight index) =
          target)
    (hvariance_decomp :
      actualVariance =ᶠ[atTop]
        (fun index =>
          (1 / denominator ^ 2) * (1 / normalizer) *
              multiplierPerturbationSecondMoment
                (uniformAssignmentSupport Unit Draw)
                (uniformAssignmentMass Unit Draw)
                (sample index)
                (fun assignment unit =>
                  multinomialCountFromDrawIndicators (draws index)
                    (fun assignment draw unit =>
                      oneHotAssignmentIndicator assignment draw unit)
                    assignment unit)
                (fun unit =>
                  contribution index unit - target * weight index unit) +
            scoreReplicationError index + biasCorrectionError index))
    (hcover_all :
      ∀ᶠ index in atTop,
        ∀ unit, score index unit ∈ cells)
    (hcontributionCell_all :
      ∀ᶠ index in atTop,
        ∀ unit,
          cellContribution index (score index unit) =
            contribution index unit)
    (hweightCell_all :
      ∀ᶠ index in atTop,
        ∀ unit,
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
    (hscore_construct_univ :
      scoreReplicationError =ᶠ[atTop]
        (fun index =>
          replicatedLinearizedSum (Finset.univ : Finset Unit)
              (fun unit =>
                multinomialCountFromDrawIndicators
                  (Finset.univ : Finset Draw)
                  (fun assignment draw unit =>
                    oneHotAssignmentIndicator assignment draw unit)
                  (assignment index) unit)
              (scoreUnitContribution index) -
            baseLinearizedSum (Finset.univ : Finset Unit)
              (scoreUnitContribution index)))
    (hscore_component_bound_all :
      ∀ᶠ index in atTop,
        ∀ unit,
          |scoreUnitContribution index unit| ≤ scoreUnitEnvelope index)
    (hscore_envelope_tendsto :
      Tendsto scoreUnitEnvelope atTop (nhds 0))
    (hbias_construct_univ :
      biasCorrectionError =ᶠ[atTop]
        (fun index =>
          replicatedLinearizedSum (Finset.univ : Finset Unit)
              (fun unit =>
                multinomialCountFromDrawIndicators
                  (Finset.univ : Finset Draw)
                  (fun assignment draw unit =>
                    oneHotAssignmentIndicator assignment draw unit)
                  (assignment index) unit)
              (biasUnitContribution index) -
            baseLinearizedSum (Finset.univ : Finset Unit)
              (biasUnitContribution index)))
    (hbias_component_bound_all :
      ∀ᶠ index in atTop,
        ∀ unit,
          |biasUnitContribution index unit| ≤ biasUnitEnvelope index)
    (hbias_envelope_tendsto :
      Tendsto biasUnitEnvelope atTop (nhds 0)) :
    Tendsto actualVariance atTop
      (nhds
        ((1 / denominator ^ 2) * (1 / normalizer) *
          weightedScoreCellMomentLimit cells
            (fun cell =>
              (contributionLimit cell - target * weightLimit cell) ^ 2)
            massLimit)) :=
  tendsto_actualBootstrapVariance_of_eventually_cell_contribution_weight_limits_and_uniformAssignment_hajek_base_ratio_full_support_univ_singleton_replicatedLinearized_all_unit_envelope_bounds
    (l := atTop) cells scoreComponent biasComponent sample draws assignment
    score contribution weight target denominator normalizer sampleSize
    cellContribution cellWeight contributionLimit weightLimit massLimit
    actualVariance scoreReplicationError biasCorrectionError
    scoreUnitContribution biasUnitContribution scoreUnitEnvelope
    biasUnitEnvelope hunit_card hdraw_card hsampleSize_ne hsample_univ
    hdraws_univ hbase_den_ne hbase_ratio hvariance_decomp hcover_all
    hcontributionCell_all hweightCell_all hcontributionLimit hweightLimit
    (cellwise_mass_lln_of_glivenkoCantelli_bridge
      cells massLimit sample (fun _index _unit => 1) score
      (weighted_indicator_array_lln_of_l1BracketingNumber_obligations
        cells massLimit sample (fun _index _unit => 1) score obligations))
    hscore_construct_univ hscore_component_bound_all
    hscore_envelope_tendsto hbias_construct_univ
    hbias_component_bound_all hbias_envelope_tendsto

/--
VdV&W endpoint-assembly version of the singleton all-unit route where the
base identity is supplied as a finite Hájek ratio equality.
-/
theorem
    tendsto_actualBootstrapVariance_of_eventually_cell_contribution_weight_limits_vdvw241_endpoint_assembly_and_uniformAssignment_hajek_base_ratio_full_support_univ_singleton_replicatedLinearized_all_unit_envelope_bounds
    [Fintype Unit] [Fintype Draw] [DecidableEq Unit] [DecidableEq Draw]
    [Nonempty Unit] [DecidableEq Cell] [DecidableEq ScoreComponent]
    [DecidableEq BiasComponent]
    {Bracket : Type*} [Fintype Bracket]
    (cells : Finset Cell)
    (scoreComponent : ScoreComponent)
    (biasComponent : BiasComponent)
    (sample : ℕ -> Finset Unit) (draws : ℕ -> Finset Draw)
    (assignment : ℕ -> Draw -> Unit)
    (score : ℕ -> Unit -> Cell)
    (contribution weight : ℕ -> Unit -> Real)
    (target denominator normalizer sampleSize : Real)
    (cellContribution cellWeight : ℕ -> Cell -> Real)
    (contributionLimit weightLimit massLimit : Cell -> Real)
    (actualVariance scoreReplicationError biasCorrectionError : ℕ -> Real)
    (scoreUnitContribution biasUnitContribution : ℕ -> Unit -> Real)
    (scoreUnitEnvelope biasUnitEnvelope : ℕ -> Real)
    (hunit_card : (Fintype.card Unit : Real) = sampleSize)
    (hdraw_card : (Fintype.card Draw : Real) = sampleSize)
    (hsampleSize_ne : sampleSize ≠ 0)
    (hsample_univ :
      sample =ᶠ[atTop] fun _index => (Finset.univ : Finset Unit))
    (hdraws_univ :
      draws =ᶠ[atTop] fun _index => (Finset.univ : Finset Draw))
    (hbase_den_ne :
      ∀ᶠ index in atTop,
        baseLinearizedSum (Finset.univ : Finset Unit)
          (weight index) ≠ 0)
    (hbase_ratio :
      ∀ᶠ index in atTop,
        baseLinearizedSum (Finset.univ : Finset Unit)
            (contribution index) /
          baseLinearizedSum (Finset.univ : Finset Unit)
            (weight index) =
          target)
    (hvariance_decomp :
      actualVariance =ᶠ[atTop]
        (fun index =>
          (1 / denominator ^ 2) * (1 / normalizer) *
              multiplierPerturbationSecondMoment
                (uniformAssignmentSupport Unit Draw)
                (uniformAssignmentMass Unit Draw)
                (sample index)
                (fun assignment unit =>
                  multinomialCountFromDrawIndicators (draws index)
                    (fun assignment draw unit =>
                      oneHotAssignmentIndicator assignment draw unit)
                    assignment unit)
                (fun unit =>
                  contribution index unit - target * weight index unit) +
            scoreReplicationError index + biasCorrectionError index))
    (hcover_all :
      ∀ᶠ index in atTop,
        ∀ unit, score index unit ∈ cells)
    (hcontributionCell_all :
      ∀ᶠ index in atTop,
        ∀ unit,
          cellContribution index (score index unit) =
            contribution index unit)
    (hweightCell_all :
      ∀ᶠ index in atTop,
        ∀ unit,
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
    (hscore_construct_univ :
      scoreReplicationError =ᶠ[atTop]
        (fun index =>
          replicatedLinearizedSum (Finset.univ : Finset Unit)
              (fun unit =>
                multinomialCountFromDrawIndicators
                  (Finset.univ : Finset Draw)
                  (fun assignment draw unit =>
                    oneHotAssignmentIndicator assignment draw unit)
                  (assignment index) unit)
              (scoreUnitContribution index) -
            baseLinearizedSum (Finset.univ : Finset Unit)
              (scoreUnitContribution index)))
    (hscore_component_bound_all :
      ∀ᶠ index in atTop,
        ∀ unit,
          |scoreUnitContribution index unit| ≤ scoreUnitEnvelope index)
    (hscore_envelope_tendsto :
      Tendsto scoreUnitEnvelope atTop (nhds 0))
    (hbias_construct_univ :
      biasCorrectionError =ᶠ[atTop]
        (fun index =>
          replicatedLinearizedSum (Finset.univ : Finset Unit)
              (fun unit =>
                multinomialCountFromDrawIndicators
                  (Finset.univ : Finset Draw)
                  (fun assignment draw unit =>
                    oneHotAssignmentIndicator assignment draw unit)
                  (assignment index) unit)
              (biasUnitContribution index) -
            baseLinearizedSum (Finset.univ : Finset Unit)
              (biasUnitContribution index)))
    (hbias_component_bound_all :
      ∀ᶠ index in atTop,
        ∀ unit,
          |biasUnitContribution index unit| ≤ biasUnitEnvelope index)
    (hbias_envelope_tendsto :
      Tendsto biasUnitEnvelope atTop (nhds 0)) :
    Tendsto actualVariance atTop
      (nhds
        ((1 / denominator ^ 2) * (1 / normalizer) *
          weightedScoreCellMomentLimit cells
            (fun cell =>
              (contributionLimit cell - target * weightLimit cell) ^ 2)
            massLimit)) :=
  tendsto_actualBootstrapVariance_of_eventually_cell_contribution_weight_limits_and_uniformAssignment_hajek_base_ratio_full_support_univ_singleton_replicatedLinearized_all_unit_envelope_bounds
    (l := atTop) cells scoreComponent biasComponent sample draws assignment
    score contribution weight target denominator normalizer sampleSize
    cellContribution cellWeight contributionLimit weightLimit massLimit
    actualVariance scoreReplicationError biasCorrectionError
    scoreUnitContribution biasUnitContribution scoreUnitEnvelope
    biasUnitEnvelope hunit_card hdraw_card hsampleSize_ne hsample_univ
    hdraws_univ hbase_den_ne hbase_ratio hvariance_decomp hcover_all
    hcontributionCell_all hweightCell_all hcontributionLimit hweightLimit
    (cellwise_mass_lln_of_glivenkoCantelli_bridge
      cells massLimit sample (fun _index _unit => 1) score
      (weighted_indicator_array_lln_of_vdvw241_endpoint_assembly
        cells massLimit sample (fun _index _unit => 1) score assembly))
    hscore_construct_univ hscore_component_bound_all
    hscore_envelope_tendsto hbias_construct_univ
    hbias_component_bound_all hbias_envelope_tendsto

/-- Finite absolute-sum envelope over full-support bootstrap units. -/
noncomputable def unitComponentAbsSumEnvelope
    [Fintype Unit] {Component : Type*}
    (unitComponent : Index -> Unit -> Component -> Real)
    (index : Index) (component : Component) : Real :=
  ∑ unit : Unit, |unitComponent index unit component|

/--
Every unit component is bounded by the finite absolute-sum envelope over all
bootstrap units.
-/
theorem unitComponentAbsSumEnvelope_bound
    [Fintype Unit] [DecidableEq Unit] {Component : Type*}
    (unitComponent : Index -> Unit -> Component -> Real)
    (index : Index) (unit : Unit) (component : Component) :
    |unitComponent index unit component| ≤
      unitComponentAbsSumEnvelope unitComponent index component := by
  unfold unitComponentAbsSumEnvelope
  exact
    Finset.single_le_sum
      (s := (Finset.univ : Finset Unit))
      (f := fun other => |unitComponent index other component|)
      (fun other _hother => abs_nonneg (unitComponent index other component))
      (Finset.mem_univ unit)

/--
If each fixed unit component tends to zero, the finite absolute-sum unit
envelope tends to zero.
-/
theorem tendsto_unitComponentAbsSumEnvelope_zero
    [Fintype Unit] [DecidableEq Unit] {Component : Type*}
    (unitComponent : Index -> Unit -> Component -> Real)
    (component : Component)
    (hunit :
      ∀ unit,
        Tendsto (fun index => unitComponent index unit component)
          l (nhds 0)) :
    Tendsto
      (fun index => unitComponentAbsSumEnvelope unitComponent index component)
      l (nhds 0) := by
  have hsum :
      Tendsto
        (fun index =>
          ∑ unit ∈ (Finset.univ : Finset Unit),
            |unitComponent index unit component|)
        l (nhds 0) :=
    tendsto_sum_cell_values_zero (l := l) (Finset.univ : Finset Unit)
      (fun index unit => |unitComponent index unit component|)
      (fun unit _hunit => by
        simpa using (hunit unit).abs)
  simpa [unitComponentAbsSumEnvelope] using hsum

/--
Pointwise unit-contribution version of the singleton all-unit finite-Hájek
route.  Finite absolute-sum envelopes over the full unit support are
constructed internally from convergence of each fixed unit contribution.
-/
theorem tendsto_actualBootstrapVariance_of_eventually_cell_contribution_weight_limits_and_uniformAssignment_hajek_base_ratio_full_support_univ_singleton_replicatedLinearized_all_unit_contribution_tendsto
    [Fintype Unit] [Fintype Draw] [DecidableEq Unit] [DecidableEq Draw]
    [Nonempty Unit] [DecidableEq Cell] [DecidableEq ScoreComponent]
    [DecidableEq BiasComponent]
    (cells : Finset Cell)
    (scoreComponent : ScoreComponent)
    (biasComponent : BiasComponent)
    (sample : Index -> Finset Unit) (draws : Index -> Finset Draw)
    (assignment : Index -> Draw -> Unit)
    (score : Index -> Unit -> Cell)
    (contribution weight : Index -> Unit -> Real)
    (target denominator normalizer sampleSize : Real)
    (cellContribution cellWeight : Index -> Cell -> Real)
    (contributionLimit weightLimit massLimit : Cell -> Real)
    (actualVariance scoreReplicationError biasCorrectionError : Index -> Real)
    (scoreUnitContribution biasUnitContribution : Index -> Unit -> Real)
    (hunit_card : (Fintype.card Unit : Real) = sampleSize)
    (hdraw_card : (Fintype.card Draw : Real) = sampleSize)
    (hsampleSize_ne : sampleSize ≠ 0)
    (hsample_univ :
      sample =ᶠ[l] fun _index => (Finset.univ : Finset Unit))
    (hdraws_univ :
      draws =ᶠ[l] fun _index => (Finset.univ : Finset Draw))
    (hbase_den_ne :
      ∀ᶠ index in l,
        baseLinearizedSum (Finset.univ : Finset Unit)
          (weight index) ≠ 0)
    (hbase_ratio :
      ∀ᶠ index in l,
        baseLinearizedSum (Finset.univ : Finset Unit)
            (contribution index) /
          baseLinearizedSum (Finset.univ : Finset Unit)
            (weight index) =
          target)
    (hvariance_decomp :
      actualVariance =ᶠ[l]
        (fun index =>
          (1 / denominator ^ 2) * (1 / normalizer) *
              multiplierPerturbationSecondMoment
                (uniformAssignmentSupport Unit Draw)
                (uniformAssignmentMass Unit Draw)
                (sample index)
                (fun assignment unit =>
                  multinomialCountFromDrawIndicators (draws index)
                    (fun assignment draw unit =>
                      oneHotAssignmentIndicator assignment draw unit)
                    assignment unit)
                (fun unit =>
                  contribution index unit - target * weight index unit) +
            scoreReplicationError index + biasCorrectionError index))
    (hcover_all :
      ∀ᶠ index in l,
        ∀ unit, score index unit ∈ cells)
    (hcontributionCell_all :
      ∀ᶠ index in l,
        ∀ unit,
          cellContribution index (score index unit) =
            contribution index unit)
    (hweightCell_all :
      ∀ᶠ index in l,
        ∀ unit,
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
    (hscore_construct_univ :
      scoreReplicationError =ᶠ[l]
        (fun index =>
          replicatedLinearizedSum (Finset.univ : Finset Unit)
              (fun unit =>
                multinomialCountFromDrawIndicators
                  (Finset.univ : Finset Draw)
                  (fun assignment draw unit =>
                    oneHotAssignmentIndicator assignment draw unit)
                  (assignment index) unit)
              (scoreUnitContribution index) -
            baseLinearizedSum (Finset.univ : Finset Unit)
              (scoreUnitContribution index)))
    (hscore_unit_tendsto :
      ∀ unit,
        Tendsto (fun index => scoreUnitContribution index unit)
          l (nhds 0))
    (hbias_construct_univ :
      biasCorrectionError =ᶠ[l]
        (fun index =>
          replicatedLinearizedSum (Finset.univ : Finset Unit)
              (fun unit =>
                multinomialCountFromDrawIndicators
                  (Finset.univ : Finset Draw)
                  (fun assignment draw unit =>
                    oneHotAssignmentIndicator assignment draw unit)
                  (assignment index) unit)
              (biasUnitContribution index) -
            baseLinearizedSum (Finset.univ : Finset Unit)
              (biasUnitContribution index)))
    (hbias_unit_tendsto :
      ∀ unit,
        Tendsto (fun index => biasUnitContribution index unit)
          l (nhds 0)) :
    Tendsto actualVariance l
      (nhds
        ((1 / denominator ^ 2) * (1 / normalizer) *
          weightedScoreCellMomentLimit cells
            (fun cell =>
              (contributionLimit cell - target * weightLimit cell) ^ 2)
            massLimit)) :=
  tendsto_actualBootstrapVariance_of_eventually_cell_contribution_weight_limits_and_uniformAssignment_hajek_base_ratio_full_support_univ_singleton_replicatedLinearized_all_unit_envelope_bounds
    (l := l) cells scoreComponent biasComponent sample draws assignment
    score contribution weight target denominator normalizer sampleSize
    cellContribution cellWeight contributionLimit weightLimit massLimit
    actualVariance scoreReplicationError biasCorrectionError
    scoreUnitContribution biasUnitContribution
    (fun index =>
      unitComponentAbsSumEnvelope
        (fun index unit (_component : ScoreComponent) =>
          scoreUnitContribution index unit)
        index scoreComponent)
    (fun index =>
      unitComponentAbsSumEnvelope
        (fun index unit (_component : BiasComponent) =>
          biasUnitContribution index unit)
        index biasComponent)
    hunit_card hdraw_card hsampleSize_ne hsample_univ hdraws_univ
    hbase_den_ne hbase_ratio hvariance_decomp hcover_all
    hcontributionCell_all hweightCell_all hcontributionLimit hweightLimit
    hmass hscore_construct_univ
    (Filter.Eventually.of_forall
      (fun index unit => by
        simpa using
          unitComponentAbsSumEnvelope_bound
            (fun index unit (_component : ScoreComponent) =>
              scoreUnitContribution index unit)
            index unit scoreComponent))
    (tendsto_unitComponentAbsSumEnvelope_zero (l := l)
      (fun index unit (_component : ScoreComponent) =>
        scoreUnitContribution index unit)
      scoreComponent hscore_unit_tendsto)
    hbias_construct_univ
    (Filter.Eventually.of_forall
      (fun index unit => by
        simpa using
          unitComponentAbsSumEnvelope_bound
            (fun index unit (_component : BiasComponent) =>
              biasUnitContribution index unit)
            index unit biasComponent))
    (tendsto_unitComponentAbsSumEnvelope_zero (l := l)
      (fun index unit (_component : BiasComponent) =>
        biasUnitContribution index unit)
      biasComponent hbias_unit_tendsto)

/--
Finite `L1(P)` bracketing companion for the pointwise singleton
unit-contribution route.
-/
theorem
    tendsto_actualBootstrapVariance_of_eventually_cell_contribution_weight_limits_l1BracketingNumber_obligations_and_uniformAssignment_hajek_base_ratio_full_support_univ_singleton_replicatedLinearized_all_unit_contribution_tendsto
    [Fintype Unit] [Fintype Draw] [DecidableEq Unit] [DecidableEq Draw]
    [Nonempty Unit] [DecidableEq Cell] [DecidableEq ScoreComponent]
    [DecidableEq BiasComponent]
    {Bracket : Type*} [Fintype Bracket]
    (cells : Finset Cell)
    (scoreComponent : ScoreComponent)
    (biasComponent : BiasComponent)
    (sample : ℕ -> Finset Unit) (draws : ℕ -> Finset Draw)
    (assignment : ℕ -> Draw -> Unit)
    (score : ℕ -> Unit -> Cell)
    (contribution weight : ℕ -> Unit -> Real)
    (target denominator normalizer sampleSize : Real)
    (cellContribution cellWeight : ℕ -> Cell -> Real)
    (contributionLimit weightLimit massLimit : Cell -> Real)
    (actualVariance scoreReplicationError biasCorrectionError : ℕ -> Real)
    (scoreUnitContribution biasUnitContribution : ℕ -> Unit -> Real)
    (hunit_card : (Fintype.card Unit : Real) = sampleSize)
    (hdraw_card : (Fintype.card Draw : Real) = sampleSize)
    (hsampleSize_ne : sampleSize ≠ 0)
    (hsample_univ :
      sample =ᶠ[atTop] fun _index => (Finset.univ : Finset Unit))
    (hdraws_univ :
      draws =ᶠ[atTop] fun _index => (Finset.univ : Finset Draw))
    (hbase_den_ne :
      ∀ᶠ index in atTop,
        baseLinearizedSum (Finset.univ : Finset Unit)
          (weight index) ≠ 0)
    (hbase_ratio :
      ∀ᶠ index in atTop,
        baseLinearizedSum (Finset.univ : Finset Unit)
            (contribution index) /
          baseLinearizedSum (Finset.univ : Finset Unit)
            (weight index) =
          target)
    (hvariance_decomp :
      actualVariance =ᶠ[atTop]
        (fun index =>
          (1 / denominator ^ 2) * (1 / normalizer) *
              multiplierPerturbationSecondMoment
                (uniformAssignmentSupport Unit Draw)
                (uniformAssignmentMass Unit Draw)
                (sample index)
                (fun assignment unit =>
                  multinomialCountFromDrawIndicators (draws index)
                    (fun assignment draw unit =>
                      oneHotAssignmentIndicator assignment draw unit)
                    assignment unit)
                (fun unit =>
                  contribution index unit - target * weight index unit) +
            scoreReplicationError index + biasCorrectionError index))
    (hcover_all :
      ∀ᶠ index in atTop,
        ∀ unit, score index unit ∈ cells)
    (hcontributionCell_all :
      ∀ᶠ index in atTop,
        ∀ unit,
          cellContribution index (score index unit) =
            contribution index unit)
    (hweightCell_all :
      ∀ᶠ index in atTop,
        ∀ unit,
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
    (hscore_construct_univ :
      scoreReplicationError =ᶠ[atTop]
        (fun index =>
          replicatedLinearizedSum (Finset.univ : Finset Unit)
              (fun unit =>
                multinomialCountFromDrawIndicators
                  (Finset.univ : Finset Draw)
                  (fun assignment draw unit =>
                    oneHotAssignmentIndicator assignment draw unit)
                  (assignment index) unit)
              (scoreUnitContribution index) -
            baseLinearizedSum (Finset.univ : Finset Unit)
              (scoreUnitContribution index)))
    (hscore_unit_tendsto :
      ∀ unit,
        Tendsto (fun index => scoreUnitContribution index unit)
          atTop (nhds 0))
    (hbias_construct_univ :
      biasCorrectionError =ᶠ[atTop]
        (fun index =>
          replicatedLinearizedSum (Finset.univ : Finset Unit)
              (fun unit =>
                multinomialCountFromDrawIndicators
                  (Finset.univ : Finset Draw)
                  (fun assignment draw unit =>
                    oneHotAssignmentIndicator assignment draw unit)
                  (assignment index) unit)
              (biasUnitContribution index) -
            baseLinearizedSum (Finset.univ : Finset Unit)
              (biasUnitContribution index)))
    (hbias_unit_tendsto :
      ∀ unit,
        Tendsto (fun index => biasUnitContribution index unit)
          atTop (nhds 0)) :
    Tendsto actualVariance atTop
      (nhds
        ((1 / denominator ^ 2) * (1 / normalizer) *
          weightedScoreCellMomentLimit cells
            (fun cell =>
              (contributionLimit cell - target * weightLimit cell) ^ 2)
            massLimit)) :=
  tendsto_actualBootstrapVariance_of_eventually_cell_contribution_weight_limits_and_uniformAssignment_hajek_base_ratio_full_support_univ_singleton_replicatedLinearized_all_unit_contribution_tendsto
    (l := atTop) cells scoreComponent biasComponent sample draws
    assignment score contribution weight target denominator normalizer
    sampleSize cellContribution cellWeight contributionLimit weightLimit
    massLimit actualVariance scoreReplicationError biasCorrectionError
    scoreUnitContribution biasUnitContribution hunit_card hdraw_card
    hsampleSize_ne hsample_univ hdraws_univ hbase_den_ne hbase_ratio
    hvariance_decomp hcover_all hcontributionCell_all hweightCell_all
    hcontributionLimit hweightLimit
    (cellwise_mass_lln_of_glivenkoCantelli_bridge
      cells massLimit sample (fun _index _unit => 1) score
      (weighted_indicator_array_lln_of_l1BracketingNumber_obligations
        cells massLimit sample (fun _index _unit => 1) score obligations))
    hscore_construct_univ hscore_unit_tendsto hbias_construct_univ
    hbias_unit_tendsto

/--
VdV&W endpoint companion for the pointwise singleton unit-contribution route.
-/
theorem
    tendsto_actualBootstrapVariance_of_eventually_cell_contribution_weight_limits_vdvw241_endpoint_assembly_and_uniformAssignment_hajek_base_ratio_full_support_univ_singleton_replicatedLinearized_all_unit_contribution_tendsto
    [Fintype Unit] [Fintype Draw] [DecidableEq Unit] [DecidableEq Draw]
    [Nonempty Unit] [DecidableEq Cell] [DecidableEq ScoreComponent]
    [DecidableEq BiasComponent]
    {Bracket : Type*} [Fintype Bracket]
    (cells : Finset Cell)
    (scoreComponent : ScoreComponent)
    (biasComponent : BiasComponent)
    (sample : ℕ -> Finset Unit) (draws : ℕ -> Finset Draw)
    (assignment : ℕ -> Draw -> Unit)
    (score : ℕ -> Unit -> Cell)
    (contribution weight : ℕ -> Unit -> Real)
    (target denominator normalizer sampleSize : Real)
    (cellContribution cellWeight : ℕ -> Cell -> Real)
    (contributionLimit weightLimit massLimit : Cell -> Real)
    (actualVariance scoreReplicationError biasCorrectionError : ℕ -> Real)
    (scoreUnitContribution biasUnitContribution : ℕ -> Unit -> Real)
    (hunit_card : (Fintype.card Unit : Real) = sampleSize)
    (hdraw_card : (Fintype.card Draw : Real) = sampleSize)
    (hsampleSize_ne : sampleSize ≠ 0)
    (hsample_univ :
      sample =ᶠ[atTop] fun _index => (Finset.univ : Finset Unit))
    (hdraws_univ :
      draws =ᶠ[atTop] fun _index => (Finset.univ : Finset Draw))
    (hbase_den_ne :
      ∀ᶠ index in atTop,
        baseLinearizedSum (Finset.univ : Finset Unit)
          (weight index) ≠ 0)
    (hbase_ratio :
      ∀ᶠ index in atTop,
        baseLinearizedSum (Finset.univ : Finset Unit)
            (contribution index) /
          baseLinearizedSum (Finset.univ : Finset Unit)
            (weight index) =
          target)
    (hvariance_decomp :
      actualVariance =ᶠ[atTop]
        (fun index =>
          (1 / denominator ^ 2) * (1 / normalizer) *
              multiplierPerturbationSecondMoment
                (uniformAssignmentSupport Unit Draw)
                (uniformAssignmentMass Unit Draw)
                (sample index)
                (fun assignment unit =>
                  multinomialCountFromDrawIndicators (draws index)
                    (fun assignment draw unit =>
                      oneHotAssignmentIndicator assignment draw unit)
                    assignment unit)
                (fun unit =>
                  contribution index unit - target * weight index unit) +
            scoreReplicationError index + biasCorrectionError index))
    (hcover_all :
      ∀ᶠ index in atTop,
        ∀ unit, score index unit ∈ cells)
    (hcontributionCell_all :
      ∀ᶠ index in atTop,
        ∀ unit,
          cellContribution index (score index unit) =
            contribution index unit)
    (hweightCell_all :
      ∀ᶠ index in atTop,
        ∀ unit,
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
    (hscore_construct_univ :
      scoreReplicationError =ᶠ[atTop]
        (fun index =>
          replicatedLinearizedSum (Finset.univ : Finset Unit)
              (fun unit =>
                multinomialCountFromDrawIndicators
                  (Finset.univ : Finset Draw)
                  (fun assignment draw unit =>
                    oneHotAssignmentIndicator assignment draw unit)
                  (assignment index) unit)
              (scoreUnitContribution index) -
            baseLinearizedSum (Finset.univ : Finset Unit)
              (scoreUnitContribution index)))
    (hscore_unit_tendsto :
      ∀ unit,
        Tendsto (fun index => scoreUnitContribution index unit)
          atTop (nhds 0))
    (hbias_construct_univ :
      biasCorrectionError =ᶠ[atTop]
        (fun index =>
          replicatedLinearizedSum (Finset.univ : Finset Unit)
              (fun unit =>
                multinomialCountFromDrawIndicators
                  (Finset.univ : Finset Draw)
                  (fun assignment draw unit =>
                    oneHotAssignmentIndicator assignment draw unit)
                  (assignment index) unit)
              (biasUnitContribution index) -
            baseLinearizedSum (Finset.univ : Finset Unit)
              (biasUnitContribution index)))
    (hbias_unit_tendsto :
      ∀ unit,
        Tendsto (fun index => biasUnitContribution index unit)
          atTop (nhds 0)) :
    Tendsto actualVariance atTop
      (nhds
        ((1 / denominator ^ 2) * (1 / normalizer) *
          weightedScoreCellMomentLimit cells
            (fun cell =>
              (contributionLimit cell - target * weightLimit cell) ^ 2)
            massLimit)) :=
  tendsto_actualBootstrapVariance_of_eventually_cell_contribution_weight_limits_and_uniformAssignment_hajek_base_ratio_full_support_univ_singleton_replicatedLinearized_all_unit_contribution_tendsto
    (l := atTop) cells scoreComponent biasComponent sample draws
    assignment score contribution weight target denominator normalizer
    sampleSize cellContribution cellWeight contributionLimit weightLimit
    massLimit actualVariance scoreReplicationError biasCorrectionError
    scoreUnitContribution biasUnitContribution hunit_card hdraw_card
    hsampleSize_ne hsample_univ hdraws_univ hbase_den_ne hbase_ratio
    hvariance_decomp hcover_all hcontributionCell_all hweightCell_all
    hcontributionLimit hweightLimit
    (cellwise_mass_lln_of_glivenkoCantelli_bridge
      cells massLimit sample (fun _index _unit => 1) score
      (weighted_indicator_array_lln_of_vdvw241_endpoint_assembly
        cells massLimit sample (fun _index _unit => 1) score assembly))
    hscore_construct_univ hscore_unit_tendsto hbias_construct_univ
    hbias_unit_tendsto

/--
If the sample and draw supports are eventually the full finite types, a
centered-count error construction written over those full supports gives the
sample/draw construction expected by the finite-error bootstrap routes.
-/
theorem eventually_uniformAssignment_full_support_error_construct_of_univ_construct
    [Fintype Unit] [Fintype Draw] [DecidableEq Unit]
    {Component : Type*}
    (components : Finset Component)
    (sample : Index -> Finset Unit) (draws : Index -> Finset Draw)
    (assignment : Index -> Draw -> Unit)
    (unitComponent : Index -> Unit -> Component -> Real)
    (error : Index -> Real)
    (hsample_univ :
      sample =ᶠ[l] fun _index => (Finset.univ : Finset Unit))
    (hdraws_univ :
      draws =ᶠ[l] fun _index => (Finset.univ : Finset Draw))
    (hconstruct_univ :
      error =ᶠ[l]
        (fun index =>
          ∑ component ∈ components, ∑ unit : Unit,
            (multinomialCountFromDrawIndicators (Finset.univ : Finset Draw)
                (fun assignment draw unit =>
                  oneHotAssignmentIndicator assignment draw unit)
                (assignment index) unit - 1) *
              unitComponent index unit component)) :
    error =ᶠ[l]
      (fun index =>
        ∑ component ∈ components, ∑ unit ∈ sample index,
          (multinomialCountFromDrawIndicators (draws index)
              (fun assignment draw unit =>
                oneHotAssignmentIndicator assignment draw unit)
              (assignment index) unit - 1) *
            unitComponent index unit component) := by
  filter_upwards [hconstruct_univ, hsample_univ, hdraws_univ] with
    index hconstruct hsample hdraws
  calc
    error index =
        ∑ component ∈ components, ∑ unit : Unit,
          (multinomialCountFromDrawIndicators (Finset.univ : Finset Draw)
              (fun assignment draw unit =>
                oneHotAssignmentIndicator assignment draw unit)
              (assignment index) unit - 1) *
            unitComponent index unit component := hconstruct
    _ =
        ∑ component ∈ components, ∑ unit ∈ sample index,
          (multinomialCountFromDrawIndicators (draws index)
              (fun assignment draw unit =>
                oneHotAssignmentIndicator assignment draw unit)
              (assignment index) unit - 1) *
            unitComponent index unit component := by
          rw [hsample, hdraws]

/--
Uniform full-support actual-variance route whose score-replication and
bias-correction construction formulas are supplied over the full finite
supports.  Full-support eventual equalities translate them to the
sample/draw formulas consumed by the finite-error route.
-/
theorem tendsto_actualBootstrapVariance_of_eventually_cell_contribution_weight_limits_and_uniformAssignment_base_ratio_full_support_univ_error_constructs_unit_envelope_bounds
    [Fintype Unit] [Fintype Draw] [DecidableEq Unit] [DecidableEq Draw]
    [Nonempty Unit] [DecidableEq Cell] [DecidableEq ScoreComponent]
    [DecidableEq BiasComponent]
    (cells : Finset Cell)
    (scoreComponents : Finset ScoreComponent)
    (biasComponents : Finset BiasComponent)
    (sample : Index -> Finset Unit) (draws : Index -> Finset Draw)
    (assignment : Index -> Draw -> Unit)
    (score : Index -> Unit -> Cell)
    (contribution weight : Index -> Unit -> Real)
    (target denominator normalizer sampleSize : Real)
    (cellContribution cellWeight : Index -> Cell -> Real)
    (contributionLimit weightLimit massLimit : Cell -> Real)
    (actualVariance scoreReplicationError biasCorrectionError : Index -> Real)
    (scoreUnitComponent : Index -> Unit -> ScoreComponent -> Real)
    (biasUnitComponent : Index -> Unit -> BiasComponent -> Real)
    (scoreUnitEnvelope : Index -> ScoreComponent -> Real)
    (biasUnitEnvelope : Index -> BiasComponent -> Real)
    (hunit_card : (Fintype.card Unit : Real) = sampleSize)
    (hdraw_card : (Fintype.card Draw : Real) = sampleSize)
    (hsampleSize_ne : sampleSize ≠ 0)
    (hsample_univ :
      sample =ᶠ[l] fun _index => (Finset.univ : Finset Unit))
    (hdraws_univ :
      draws =ᶠ[l] fun _index => (Finset.univ : Finset Draw))
    (hbase :
      ∀ᶠ index in l,
        baseLinearizedSum (Finset.univ : Finset Unit)
            (contribution index) =
          target *
            baseLinearizedSum (Finset.univ : Finset Unit)
              (weight index))
    (hvariance_decomp :
      actualVariance =ᶠ[l]
        (fun index =>
          (1 / denominator ^ 2) * (1 / normalizer) *
              multiplierPerturbationSecondMoment
                (uniformAssignmentSupport Unit Draw)
                (uniformAssignmentMass Unit Draw)
                (sample index)
                (fun assignment unit =>
                  multinomialCountFromDrawIndicators (draws index)
                    (fun assignment draw unit =>
                      oneHotAssignmentIndicator assignment draw unit)
                    assignment unit)
                (fun unit =>
                  contribution index unit - target * weight index unit) +
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
    (hscore_construct_univ :
      scoreReplicationError =ᶠ[l]
        (fun index =>
          ∑ component ∈ scoreComponents, ∑ unit : Unit,
            (multinomialCountFromDrawIndicators (Finset.univ : Finset Draw)
                (fun assignment draw unit =>
                  oneHotAssignmentIndicator assignment draw unit)
                (assignment index) unit - 1) *
              scoreUnitComponent index unit component))
    (hscore_component_bound :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ sample index ->
          ∀ component, component ∈ scoreComponents ->
            |scoreUnitComponent index unit component| ≤
              scoreUnitEnvelope index component)
    (hscore_envelope_tendsto :
      ∀ component, component ∈ scoreComponents ->
        Tendsto (fun index => scoreUnitEnvelope index component)
          l (nhds 0))
    (hbias_construct_univ :
      biasCorrectionError =ᶠ[l]
        (fun index =>
          ∑ component ∈ biasComponents, ∑ unit : Unit,
            (multinomialCountFromDrawIndicators (Finset.univ : Finset Draw)
                (fun assignment draw unit =>
                  oneHotAssignmentIndicator assignment draw unit)
                (assignment index) unit - 1) *
              biasUnitComponent index unit component))
    (hbias_component_bound :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ sample index ->
          ∀ component, component ∈ biasComponents ->
            |biasUnitComponent index unit component| ≤
              biasUnitEnvelope index component)
    (hbias_envelope_tendsto :
      ∀ component, component ∈ biasComponents ->
        Tendsto (fun index => biasUnitEnvelope index component)
          l (nhds 0)) :
    Tendsto actualVariance l
      (nhds
        ((1 / denominator ^ 2) * (1 / normalizer) *
          weightedScoreCellMomentLimit cells
            (fun cell =>
              (contributionLimit cell - target * weightLimit cell) ^ 2)
            massLimit)) := by
  have hscore_construct :
      scoreReplicationError =ᶠ[l]
        (fun index =>
          ∑ component ∈ scoreComponents, ∑ unit ∈ sample index,
            (multinomialCountFromDrawIndicators (draws index)
                (fun assignment draw unit =>
                  oneHotAssignmentIndicator assignment draw unit)
                (assignment index) unit - 1) *
              scoreUnitComponent index unit component) :=
    eventually_uniformAssignment_full_support_error_construct_of_univ_construct
      (l := l) scoreComponents sample draws assignment scoreUnitComponent
      scoreReplicationError hsample_univ hdraws_univ hscore_construct_univ
  have hbias_construct :
      biasCorrectionError =ᶠ[l]
        (fun index =>
          ∑ component ∈ biasComponents, ∑ unit ∈ sample index,
            (multinomialCountFromDrawIndicators (draws index)
                (fun assignment draw unit =>
                  oneHotAssignmentIndicator assignment draw unit)
                (assignment index) unit - 1) *
              biasUnitComponent index unit component) :=
    eventually_uniformAssignment_full_support_error_construct_of_univ_construct
      (l := l) biasComponents sample draws assignment biasUnitComponent
      biasCorrectionError hsample_univ hdraws_univ hbias_construct_univ
  exact
    tendsto_actualBootstrapVariance_of_eventually_cell_contribution_weight_limits_and_uniformAssignment_base_ratio_full_support_unit_envelope_bounds
      (l := l) cells scoreComponents biasComponents sample draws assignment
      score contribution weight target denominator normalizer sampleSize
      cellContribution cellWeight contributionLimit weightLimit massLimit
      actualVariance scoreReplicationError biasCorrectionError
      scoreUnitComponent biasUnitComponent scoreUnitEnvelope biasUnitEnvelope
      hunit_card hdraw_card hsampleSize_ne hsample_univ hdraws_univ hbase
      hvariance_decomp hcover hcontributionCell hweightCell
      hcontributionLimit hweightLimit hmass hscore_construct
      hscore_component_bound hscore_envelope_tendsto hbias_construct
      hbias_component_bound hbias_envelope_tendsto

/--
Finite `L1(P)` bracketing supplies the score-cell mass LLN for the concrete
uniform full-support route whose score/bias construction formulas are stated
over full finite supports.
-/
theorem
    tendsto_actualBootstrapVariance_of_eventually_cell_contribution_weight_limits_l1BracketingNumber_obligations_and_uniformAssignment_base_ratio_full_support_univ_error_constructs_unit_envelope_bounds
    [Fintype Unit] [Fintype Draw] [DecidableEq Unit] [DecidableEq Draw]
    [Nonempty Unit] [DecidableEq Cell] [DecidableEq ScoreComponent]
    [DecidableEq BiasComponent]
    {Bracket : Type*} [Fintype Bracket]
    (cells : Finset Cell)
    (scoreComponents : Finset ScoreComponent)
    (biasComponents : Finset BiasComponent)
    (sample : ℕ -> Finset Unit) (draws : ℕ -> Finset Draw)
    (assignment : ℕ -> Draw -> Unit)
    (score : ℕ -> Unit -> Cell)
    (contribution weight : ℕ -> Unit -> Real)
    (target denominator normalizer sampleSize : Real)
    (cellContribution cellWeight : ℕ -> Cell -> Real)
    (contributionLimit weightLimit massLimit : Cell -> Real)
    (actualVariance scoreReplicationError biasCorrectionError : ℕ -> Real)
    (scoreUnitComponent : ℕ -> Unit -> ScoreComponent -> Real)
    (biasUnitComponent : ℕ -> Unit -> BiasComponent -> Real)
    (scoreUnitEnvelope : ℕ -> ScoreComponent -> Real)
    (biasUnitEnvelope : ℕ -> BiasComponent -> Real)
    (hunit_card : (Fintype.card Unit : Real) = sampleSize)
    (hdraw_card : (Fintype.card Draw : Real) = sampleSize)
    (hsampleSize_ne : sampleSize ≠ 0)
    (hsample_univ :
      sample =ᶠ[atTop] fun _index => (Finset.univ : Finset Unit))
    (hdraws_univ :
      draws =ᶠ[atTop] fun _index => (Finset.univ : Finset Draw))
    (hbase :
      ∀ᶠ index in atTop,
        baseLinearizedSum (Finset.univ : Finset Unit)
            (contribution index) =
          target *
            baseLinearizedSum (Finset.univ : Finset Unit)
              (weight index))
    (hvariance_decomp :
      actualVariance =ᶠ[atTop]
        (fun index =>
          (1 / denominator ^ 2) * (1 / normalizer) *
              multiplierPerturbationSecondMoment
                (uniformAssignmentSupport Unit Draw)
                (uniformAssignmentMass Unit Draw)
                (sample index)
                (fun assignment unit =>
                  multinomialCountFromDrawIndicators (draws index)
                    (fun assignment draw unit =>
                      oneHotAssignmentIndicator assignment draw unit)
                    assignment unit)
                (fun unit =>
                  contribution index unit - target * weight index unit) +
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
    (hscore_construct_univ :
      scoreReplicationError =ᶠ[atTop]
        (fun index =>
          ∑ component ∈ scoreComponents, ∑ unit : Unit,
            (multinomialCountFromDrawIndicators (Finset.univ : Finset Draw)
                (fun assignment draw unit =>
                  oneHotAssignmentIndicator assignment draw unit)
                (assignment index) unit - 1) *
              scoreUnitComponent index unit component))
    (hscore_component_bound :
      ∀ᶠ index in atTop,
        ∀ unit, unit ∈ sample index ->
          ∀ component, component ∈ scoreComponents ->
            |scoreUnitComponent index unit component| ≤
              scoreUnitEnvelope index component)
    (hscore_envelope_tendsto :
      ∀ component, component ∈ scoreComponents ->
        Tendsto (fun index => scoreUnitEnvelope index component)
          atTop (nhds 0))
    (hbias_construct_univ :
      biasCorrectionError =ᶠ[atTop]
        (fun index =>
          ∑ component ∈ biasComponents, ∑ unit : Unit,
            (multinomialCountFromDrawIndicators (Finset.univ : Finset Draw)
                (fun assignment draw unit =>
                  oneHotAssignmentIndicator assignment draw unit)
                (assignment index) unit - 1) *
              biasUnitComponent index unit component))
    (hbias_component_bound :
      ∀ᶠ index in atTop,
        ∀ unit, unit ∈ sample index ->
          ∀ component, component ∈ biasComponents ->
            |biasUnitComponent index unit component| ≤
              biasUnitEnvelope index component)
    (hbias_envelope_tendsto :
      ∀ component, component ∈ biasComponents ->
        Tendsto (fun index => biasUnitEnvelope index component)
          atTop (nhds 0)) :
    Tendsto actualVariance atTop
      (nhds
        ((1 / denominator ^ 2) * (1 / normalizer) *
          weightedScoreCellMomentLimit cells
            (fun cell =>
              (contributionLimit cell - target * weightLimit cell) ^ 2)
            massLimit)) :=
  tendsto_actualBootstrapVariance_of_eventually_cell_contribution_weight_limits_and_uniformAssignment_base_ratio_full_support_univ_error_constructs_unit_envelope_bounds
    (l := atTop) cells scoreComponents biasComponents sample draws
    assignment score contribution weight target denominator normalizer
    sampleSize cellContribution cellWeight contributionLimit weightLimit
    massLimit actualVariance scoreReplicationError biasCorrectionError
    scoreUnitComponent biasUnitComponent scoreUnitEnvelope biasUnitEnvelope
    hunit_card hdraw_card hsampleSize_ne hsample_univ hdraws_univ hbase
    hvariance_decomp hcover hcontributionCell hweightCell
    hcontributionLimit hweightLimit
    (cellwise_mass_lln_of_glivenkoCantelli_bridge
      cells massLimit sample (fun _index _unit => 1) score
      (weighted_indicator_array_lln_of_l1BracketingNumber_obligations
        cells massLimit sample (fun _index _unit => 1) score obligations))
    hscore_construct_univ hscore_component_bound hscore_envelope_tendsto
    hbias_construct_univ hbias_component_bound hbias_envelope_tendsto

/--
VdV&W endpoint assemblies supply the score-cell mass LLN for the concrete
uniform full-support route whose score/bias construction formulas are stated
over full finite supports.
-/
theorem
    tendsto_actualBootstrapVariance_of_eventually_cell_contribution_weight_limits_vdvw241_endpoint_assembly_and_uniformAssignment_base_ratio_full_support_univ_error_constructs_unit_envelope_bounds
    [Fintype Unit] [Fintype Draw] [DecidableEq Unit] [DecidableEq Draw]
    [Nonempty Unit] [DecidableEq Cell] [DecidableEq ScoreComponent]
    [DecidableEq BiasComponent]
    {Bracket : Type*} [Fintype Bracket]
    (cells : Finset Cell)
    (scoreComponents : Finset ScoreComponent)
    (biasComponents : Finset BiasComponent)
    (sample : ℕ -> Finset Unit) (draws : ℕ -> Finset Draw)
    (assignment : ℕ -> Draw -> Unit)
    (score : ℕ -> Unit -> Cell)
    (contribution weight : ℕ -> Unit -> Real)
    (target denominator normalizer sampleSize : Real)
    (cellContribution cellWeight : ℕ -> Cell -> Real)
    (contributionLimit weightLimit massLimit : Cell -> Real)
    (actualVariance scoreReplicationError biasCorrectionError : ℕ -> Real)
    (scoreUnitComponent : ℕ -> Unit -> ScoreComponent -> Real)
    (biasUnitComponent : ℕ -> Unit -> BiasComponent -> Real)
    (scoreUnitEnvelope : ℕ -> ScoreComponent -> Real)
    (biasUnitEnvelope : ℕ -> BiasComponent -> Real)
    (hunit_card : (Fintype.card Unit : Real) = sampleSize)
    (hdraw_card : (Fintype.card Draw : Real) = sampleSize)
    (hsampleSize_ne : sampleSize ≠ 0)
    (hsample_univ :
      sample =ᶠ[atTop] fun _index => (Finset.univ : Finset Unit))
    (hdraws_univ :
      draws =ᶠ[atTop] fun _index => (Finset.univ : Finset Draw))
    (hbase :
      ∀ᶠ index in atTop,
        baseLinearizedSum (Finset.univ : Finset Unit)
            (contribution index) =
          target *
            baseLinearizedSum (Finset.univ : Finset Unit)
              (weight index))
    (hvariance_decomp :
      actualVariance =ᶠ[atTop]
        (fun index =>
          (1 / denominator ^ 2) * (1 / normalizer) *
              multiplierPerturbationSecondMoment
                (uniformAssignmentSupport Unit Draw)
                (uniformAssignmentMass Unit Draw)
                (sample index)
                (fun assignment unit =>
                  multinomialCountFromDrawIndicators (draws index)
                    (fun assignment draw unit =>
                      oneHotAssignmentIndicator assignment draw unit)
                    assignment unit)
                (fun unit =>
                  contribution index unit - target * weight index unit) +
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
    (hscore_construct_univ :
      scoreReplicationError =ᶠ[atTop]
        (fun index =>
          ∑ component ∈ scoreComponents, ∑ unit : Unit,
            (multinomialCountFromDrawIndicators (Finset.univ : Finset Draw)
                (fun assignment draw unit =>
                  oneHotAssignmentIndicator assignment draw unit)
                (assignment index) unit - 1) *
              scoreUnitComponent index unit component))
    (hscore_component_bound :
      ∀ᶠ index in atTop,
        ∀ unit, unit ∈ sample index ->
          ∀ component, component ∈ scoreComponents ->
            |scoreUnitComponent index unit component| ≤
              scoreUnitEnvelope index component)
    (hscore_envelope_tendsto :
      ∀ component, component ∈ scoreComponents ->
        Tendsto (fun index => scoreUnitEnvelope index component)
          atTop (nhds 0))
    (hbias_construct_univ :
      biasCorrectionError =ᶠ[atTop]
        (fun index =>
          ∑ component ∈ biasComponents, ∑ unit : Unit,
            (multinomialCountFromDrawIndicators (Finset.univ : Finset Draw)
                (fun assignment draw unit =>
                  oneHotAssignmentIndicator assignment draw unit)
                (assignment index) unit - 1) *
              biasUnitComponent index unit component))
    (hbias_component_bound :
      ∀ᶠ index in atTop,
        ∀ unit, unit ∈ sample index ->
          ∀ component, component ∈ biasComponents ->
            |biasUnitComponent index unit component| ≤
              biasUnitEnvelope index component)
    (hbias_envelope_tendsto :
      ∀ component, component ∈ biasComponents ->
        Tendsto (fun index => biasUnitEnvelope index component)
          atTop (nhds 0)) :
    Tendsto actualVariance atTop
      (nhds
        ((1 / denominator ^ 2) * (1 / normalizer) *
          weightedScoreCellMomentLimit cells
            (fun cell =>
              (contributionLimit cell - target * weightLimit cell) ^ 2)
            massLimit)) :=
  tendsto_actualBootstrapVariance_of_eventually_cell_contribution_weight_limits_and_uniformAssignment_base_ratio_full_support_univ_error_constructs_unit_envelope_bounds
    (l := atTop) cells scoreComponents biasComponents sample draws
    assignment score contribution weight target denominator normalizer
    sampleSize cellContribution cellWeight contributionLimit weightLimit
    massLimit actualVariance scoreReplicationError biasCorrectionError
    scoreUnitComponent biasUnitComponent scoreUnitEnvelope biasUnitEnvelope
    hunit_card hdraw_card hsampleSize_ne hsample_univ hdraws_univ hbase
    hvariance_decomp hcover hcontributionCell hweightCell
    hcontributionLimit hweightLimit
    (cellwise_mass_lln_of_glivenkoCantelli_bridge
      cells massLimit sample (fun _index _unit => 1) score
      (weighted_indicator_array_lln_of_vdvw241_endpoint_assembly
        cells massLimit sample (fun _index _unit => 1) score assembly))
    hscore_construct_univ hscore_component_bound hscore_envelope_tendsto
    hbias_construct_univ hbias_component_bound hbias_envelope_tendsto

/--
Full-support uniform route whose coverage, cell contribution/weight
representations, and unit-component envelope bounds are stated over all units,
rather than conditionally on membership in the eventual sample support.
-/
theorem tendsto_actualBootstrapVariance_of_eventually_cell_contribution_weight_limits_and_uniformAssignment_base_ratio_full_support_univ_all_unit_error_bounds
    [Fintype Unit] [Fintype Draw] [DecidableEq Unit] [DecidableEq Draw]
    [Nonempty Unit] [DecidableEq Cell] [DecidableEq ScoreComponent]
    [DecidableEq BiasComponent]
    (cells : Finset Cell)
    (scoreComponents : Finset ScoreComponent)
    (biasComponents : Finset BiasComponent)
    (sample : Index -> Finset Unit) (draws : Index -> Finset Draw)
    (assignment : Index -> Draw -> Unit)
    (score : Index -> Unit -> Cell)
    (contribution weight : Index -> Unit -> Real)
    (target denominator normalizer sampleSize : Real)
    (cellContribution cellWeight : Index -> Cell -> Real)
    (contributionLimit weightLimit massLimit : Cell -> Real)
    (actualVariance scoreReplicationError biasCorrectionError : Index -> Real)
    (scoreUnitComponent : Index -> Unit -> ScoreComponent -> Real)
    (biasUnitComponent : Index -> Unit -> BiasComponent -> Real)
    (scoreUnitEnvelope : Index -> ScoreComponent -> Real)
    (biasUnitEnvelope : Index -> BiasComponent -> Real)
    (hunit_card : (Fintype.card Unit : Real) = sampleSize)
    (hdraw_card : (Fintype.card Draw : Real) = sampleSize)
    (hsampleSize_ne : sampleSize ≠ 0)
    (hsample_univ :
      sample =ᶠ[l] fun _index => (Finset.univ : Finset Unit))
    (hdraws_univ :
      draws =ᶠ[l] fun _index => (Finset.univ : Finset Draw))
    (hbase :
      ∀ᶠ index in l,
        baseLinearizedSum (Finset.univ : Finset Unit)
            (contribution index) =
          target *
            baseLinearizedSum (Finset.univ : Finset Unit)
              (weight index))
    (hvariance_decomp :
      actualVariance =ᶠ[l]
        (fun index =>
          (1 / denominator ^ 2) * (1 / normalizer) *
              multiplierPerturbationSecondMoment
                (uniformAssignmentSupport Unit Draw)
                (uniformAssignmentMass Unit Draw)
                (sample index)
                (fun assignment unit =>
                  multinomialCountFromDrawIndicators (draws index)
                    (fun assignment draw unit =>
                      oneHotAssignmentIndicator assignment draw unit)
                    assignment unit)
                (fun unit =>
                  contribution index unit - target * weight index unit) +
            scoreReplicationError index + biasCorrectionError index))
    (hcover_all :
      ∀ᶠ index in l,
        ∀ unit, score index unit ∈ cells)
    (hcontributionCell_all :
      ∀ᶠ index in l,
        ∀ unit,
          cellContribution index (score index unit) =
            contribution index unit)
    (hweightCell_all :
      ∀ᶠ index in l,
        ∀ unit,
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
    (hscore_construct_univ :
      scoreReplicationError =ᶠ[l]
        (fun index =>
          ∑ component ∈ scoreComponents, ∑ unit : Unit,
            (multinomialCountFromDrawIndicators (Finset.univ : Finset Draw)
                (fun assignment draw unit =>
                  oneHotAssignmentIndicator assignment draw unit)
                (assignment index) unit - 1) *
              scoreUnitComponent index unit component))
    (hscore_component_bound_all :
      ∀ᶠ index in l,
        ∀ unit,
          ∀ component, component ∈ scoreComponents ->
            |scoreUnitComponent index unit component| ≤
              scoreUnitEnvelope index component)
    (hscore_envelope_tendsto :
      ∀ component, component ∈ scoreComponents ->
        Tendsto (fun index => scoreUnitEnvelope index component)
          l (nhds 0))
    (hbias_construct_univ :
      biasCorrectionError =ᶠ[l]
        (fun index =>
          ∑ component ∈ biasComponents, ∑ unit : Unit,
            (multinomialCountFromDrawIndicators (Finset.univ : Finset Draw)
                (fun assignment draw unit =>
                  oneHotAssignmentIndicator assignment draw unit)
                (assignment index) unit - 1) *
              biasUnitComponent index unit component))
    (hbias_component_bound_all :
      ∀ᶠ index in l,
        ∀ unit,
          ∀ component, component ∈ biasComponents ->
            |biasUnitComponent index unit component| ≤
              biasUnitEnvelope index component)
    (hbias_envelope_tendsto :
      ∀ component, component ∈ biasComponents ->
        Tendsto (fun index => biasUnitEnvelope index component)
          l (nhds 0)) :
    Tendsto actualVariance l
      (nhds
        ((1 / denominator ^ 2) * (1 / normalizer) *
          weightedScoreCellMomentLimit cells
            (fun cell =>
              (contributionLimit cell - target * weightLimit cell) ^ 2)
            massLimit)) := by
  have hcover :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ sample index -> score index unit ∈ cells := by
    filter_upwards [hcover_all] with index hcover_index unit _hunit
    exact hcover_index unit
  have hcontributionCell :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ sample index ->
          cellContribution index (score index unit) =
            contribution index unit := by
    filter_upwards [hcontributionCell_all] with index hcell_index unit _hunit
    exact hcell_index unit
  have hweightCell :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ sample index ->
          cellWeight index (score index unit) = weight index unit := by
    filter_upwards [hweightCell_all] with index hcell_index unit _hunit
    exact hcell_index unit
  have hscore_component_bound :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ sample index ->
          ∀ component, component ∈ scoreComponents ->
            |scoreUnitComponent index unit component| ≤
              scoreUnitEnvelope index component := by
    filter_upwards [hscore_component_bound_all] with
      index hbound_index unit _hunit component hcomponent
    exact hbound_index unit component hcomponent
  have hbias_component_bound :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ sample index ->
          ∀ component, component ∈ biasComponents ->
            |biasUnitComponent index unit component| ≤
              biasUnitEnvelope index component := by
    filter_upwards [hbias_component_bound_all] with
      index hbound_index unit _hunit component hcomponent
    exact hbound_index unit component hcomponent
  exact
    tendsto_actualBootstrapVariance_of_eventually_cell_contribution_weight_limits_and_uniformAssignment_base_ratio_full_support_univ_error_constructs_unit_envelope_bounds
      (l := l) cells scoreComponents biasComponents sample draws assignment
      score contribution weight target denominator normalizer sampleSize
      cellContribution cellWeight contributionLimit weightLimit massLimit
      actualVariance scoreReplicationError biasCorrectionError
      scoreUnitComponent biasUnitComponent scoreUnitEnvelope biasUnitEnvelope
      hunit_card hdraw_card hsampleSize_ne hsample_univ hdraws_univ hbase
      hvariance_decomp hcover hcontributionCell hweightCell
      hcontributionLimit hweightLimit hmass hscore_construct_univ
      hscore_component_bound hscore_envelope_tendsto hbias_construct_univ
      hbias_component_bound hbias_envelope_tendsto

/--
Full-support uniform all-unit route where the base-sum identity is derived
from the more paper-facing finite Hájek ratio equality.
-/
theorem tendsto_actualBootstrapVariance_of_eventually_cell_contribution_weight_limits_and_uniformAssignment_hajek_base_ratio_full_support_univ_all_unit_error_bounds
    [Fintype Unit] [Fintype Draw] [DecidableEq Unit] [DecidableEq Draw]
    [Nonempty Unit] [DecidableEq Cell] [DecidableEq ScoreComponent]
    [DecidableEq BiasComponent]
    (cells : Finset Cell)
    (scoreComponents : Finset ScoreComponent)
    (biasComponents : Finset BiasComponent)
    (sample : Index -> Finset Unit) (draws : Index -> Finset Draw)
    (assignment : Index -> Draw -> Unit)
    (score : Index -> Unit -> Cell)
    (contribution weight : Index -> Unit -> Real)
    (target denominator normalizer sampleSize : Real)
    (cellContribution cellWeight : Index -> Cell -> Real)
    (contributionLimit weightLimit massLimit : Cell -> Real)
    (actualVariance scoreReplicationError biasCorrectionError : Index -> Real)
    (scoreUnitComponent : Index -> Unit -> ScoreComponent -> Real)
    (biasUnitComponent : Index -> Unit -> BiasComponent -> Real)
    (scoreUnitEnvelope : Index -> ScoreComponent -> Real)
    (biasUnitEnvelope : Index -> BiasComponent -> Real)
    (hunit_card : (Fintype.card Unit : Real) = sampleSize)
    (hdraw_card : (Fintype.card Draw : Real) = sampleSize)
    (hsampleSize_ne : sampleSize ≠ 0)
    (hsample_univ :
      sample =ᶠ[l] fun _index => (Finset.univ : Finset Unit))
    (hdraws_univ :
      draws =ᶠ[l] fun _index => (Finset.univ : Finset Draw))
    (hbase_den_ne :
      ∀ᶠ index in l,
        baseLinearizedSum (Finset.univ : Finset Unit)
          (weight index) ≠ 0)
    (hbase_ratio :
      ∀ᶠ index in l,
        baseLinearizedSum (Finset.univ : Finset Unit)
            (contribution index) /
          baseLinearizedSum (Finset.univ : Finset Unit)
            (weight index) =
          target)
    (hvariance_decomp :
      actualVariance =ᶠ[l]
        (fun index =>
          (1 / denominator ^ 2) * (1 / normalizer) *
              multiplierPerturbationSecondMoment
                (uniformAssignmentSupport Unit Draw)
                (uniformAssignmentMass Unit Draw)
                (sample index)
                (fun assignment unit =>
                  multinomialCountFromDrawIndicators (draws index)
                    (fun assignment draw unit =>
                      oneHotAssignmentIndicator assignment draw unit)
                    assignment unit)
                (fun unit =>
                  contribution index unit - target * weight index unit) +
            scoreReplicationError index + biasCorrectionError index))
    (hcover_all :
      ∀ᶠ index in l,
        ∀ unit, score index unit ∈ cells)
    (hcontributionCell_all :
      ∀ᶠ index in l,
        ∀ unit,
          cellContribution index (score index unit) =
            contribution index unit)
    (hweightCell_all :
      ∀ᶠ index in l,
        ∀ unit,
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
    (hscore_construct_univ :
      scoreReplicationError =ᶠ[l]
        (fun index =>
          ∑ component ∈ scoreComponents, ∑ unit : Unit,
            (multinomialCountFromDrawIndicators (Finset.univ : Finset Draw)
                (fun assignment draw unit =>
                  oneHotAssignmentIndicator assignment draw unit)
                (assignment index) unit - 1) *
              scoreUnitComponent index unit component))
    (hscore_component_bound_all :
      ∀ᶠ index in l,
        ∀ unit,
          ∀ component, component ∈ scoreComponents ->
            |scoreUnitComponent index unit component| ≤
              scoreUnitEnvelope index component)
    (hscore_envelope_tendsto :
      ∀ component, component ∈ scoreComponents ->
        Tendsto (fun index => scoreUnitEnvelope index component)
          l (nhds 0))
    (hbias_construct_univ :
      biasCorrectionError =ᶠ[l]
        (fun index =>
          ∑ component ∈ biasComponents, ∑ unit : Unit,
            (multinomialCountFromDrawIndicators (Finset.univ : Finset Draw)
                (fun assignment draw unit =>
                  oneHotAssignmentIndicator assignment draw unit)
                (assignment index) unit - 1) *
              biasUnitComponent index unit component))
    (hbias_component_bound_all :
      ∀ᶠ index in l,
        ∀ unit,
          ∀ component, component ∈ biasComponents ->
            |biasUnitComponent index unit component| ≤
              biasUnitEnvelope index component)
    (hbias_envelope_tendsto :
      ∀ component, component ∈ biasComponents ->
        Tendsto (fun index => biasUnitEnvelope index component)
          l (nhds 0)) :
    Tendsto actualVariance l
      (nhds
        ((1 / denominator ^ 2) * (1 / normalizer) *
          weightedScoreCellMomentLimit cells
            (fun cell =>
              (contributionLimit cell - target * weightLimit cell) ^ 2)
            massLimit)) := by
  have hbase :
      ∀ᶠ index in l,
        baseLinearizedSum (Finset.univ : Finset Unit)
            (contribution index) =
          target *
            baseLinearizedSum (Finset.univ : Finset Unit)
              (weight index) := by
    filter_upwards [hbase_den_ne, hbase_ratio] with
      index hden hratio
    exact
      baseLinearizedSum_eq_target_mul_of_hajek_ratio_eq
        (Finset.univ : Finset Unit) (contribution index) (weight index)
        target hden hratio
  exact
    tendsto_actualBootstrapVariance_of_eventually_cell_contribution_weight_limits_and_uniformAssignment_base_ratio_full_support_univ_all_unit_error_bounds
      (l := l) cells scoreComponents biasComponents sample draws assignment
      score contribution weight target denominator normalizer sampleSize
      cellContribution cellWeight contributionLimit weightLimit massLimit
      actualVariance scoreReplicationError biasCorrectionError
      scoreUnitComponent biasUnitComponent scoreUnitEnvelope biasUnitEnvelope
      hunit_card hdraw_card hsampleSize_ne hsample_univ hdraws_univ hbase
      hvariance_decomp hcover_all hcontributionCell_all hweightCell_all
      hcontributionLimit hweightLimit hmass hscore_construct_univ
      hscore_component_bound_all hscore_envelope_tendsto
      hbias_construct_univ hbias_component_bound_all
      hbias_envelope_tendsto

/--
Finite `L1(P)` bracketing version of the full-support uniform all-unit route.
The score-cell mass LLN is supplied by bracketing obligations, while all
deterministic coverage and envelope bounds are stated over every unit.
-/
theorem
    tendsto_actualBootstrapVariance_of_eventually_cell_contribution_weight_limits_l1BracketingNumber_obligations_and_uniformAssignment_base_ratio_full_support_univ_all_unit_error_bounds
    [Fintype Unit] [Fintype Draw] [DecidableEq Unit] [DecidableEq Draw]
    [Nonempty Unit] [DecidableEq Cell] [DecidableEq ScoreComponent]
    [DecidableEq BiasComponent]
    {Bracket : Type*} [Fintype Bracket]
    (cells : Finset Cell)
    (scoreComponents : Finset ScoreComponent)
    (biasComponents : Finset BiasComponent)
    (sample : ℕ -> Finset Unit) (draws : ℕ -> Finset Draw)
    (assignment : ℕ -> Draw -> Unit)
    (score : ℕ -> Unit -> Cell)
    (contribution weight : ℕ -> Unit -> Real)
    (target denominator normalizer sampleSize : Real)
    (cellContribution cellWeight : ℕ -> Cell -> Real)
    (contributionLimit weightLimit massLimit : Cell -> Real)
    (actualVariance scoreReplicationError biasCorrectionError : ℕ -> Real)
    (scoreUnitComponent : ℕ -> Unit -> ScoreComponent -> Real)
    (biasUnitComponent : ℕ -> Unit -> BiasComponent -> Real)
    (scoreUnitEnvelope : ℕ -> ScoreComponent -> Real)
    (biasUnitEnvelope : ℕ -> BiasComponent -> Real)
    (hunit_card : (Fintype.card Unit : Real) = sampleSize)
    (hdraw_card : (Fintype.card Draw : Real) = sampleSize)
    (hsampleSize_ne : sampleSize ≠ 0)
    (hsample_univ :
      sample =ᶠ[atTop] fun _index => (Finset.univ : Finset Unit))
    (hdraws_univ :
      draws =ᶠ[atTop] fun _index => (Finset.univ : Finset Draw))
    (hbase :
      ∀ᶠ index in atTop,
        baseLinearizedSum (Finset.univ : Finset Unit)
            (contribution index) =
          target *
            baseLinearizedSum (Finset.univ : Finset Unit)
              (weight index))
    (hvariance_decomp :
      actualVariance =ᶠ[atTop]
        (fun index =>
          (1 / denominator ^ 2) * (1 / normalizer) *
              multiplierPerturbationSecondMoment
                (uniformAssignmentSupport Unit Draw)
                (uniformAssignmentMass Unit Draw)
                (sample index)
                (fun assignment unit =>
                  multinomialCountFromDrawIndicators (draws index)
                    (fun assignment draw unit =>
                      oneHotAssignmentIndicator assignment draw unit)
                    assignment unit)
                (fun unit =>
                  contribution index unit - target * weight index unit) +
            scoreReplicationError index + biasCorrectionError index))
    (hcover_all :
      ∀ᶠ index in atTop,
        ∀ unit, score index unit ∈ cells)
    (hcontributionCell_all :
      ∀ᶠ index in atTop,
        ∀ unit,
          cellContribution index (score index unit) =
            contribution index unit)
    (hweightCell_all :
      ∀ᶠ index in atTop,
        ∀ unit,
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
    (hscore_construct_univ :
      scoreReplicationError =ᶠ[atTop]
        (fun index =>
          ∑ component ∈ scoreComponents, ∑ unit : Unit,
            (multinomialCountFromDrawIndicators (Finset.univ : Finset Draw)
                (fun assignment draw unit =>
                  oneHotAssignmentIndicator assignment draw unit)
                (assignment index) unit - 1) *
              scoreUnitComponent index unit component))
    (hscore_component_bound_all :
      ∀ᶠ index in atTop,
        ∀ unit,
          ∀ component, component ∈ scoreComponents ->
            |scoreUnitComponent index unit component| ≤
              scoreUnitEnvelope index component)
    (hscore_envelope_tendsto :
      ∀ component, component ∈ scoreComponents ->
        Tendsto (fun index => scoreUnitEnvelope index component)
          atTop (nhds 0))
    (hbias_construct_univ :
      biasCorrectionError =ᶠ[atTop]
        (fun index =>
          ∑ component ∈ biasComponents, ∑ unit : Unit,
            (multinomialCountFromDrawIndicators (Finset.univ : Finset Draw)
                (fun assignment draw unit =>
                  oneHotAssignmentIndicator assignment draw unit)
                (assignment index) unit - 1) *
              biasUnitComponent index unit component))
    (hbias_component_bound_all :
      ∀ᶠ index in atTop,
        ∀ unit,
          ∀ component, component ∈ biasComponents ->
            |biasUnitComponent index unit component| ≤
              biasUnitEnvelope index component)
    (hbias_envelope_tendsto :
      ∀ component, component ∈ biasComponents ->
        Tendsto (fun index => biasUnitEnvelope index component)
          atTop (nhds 0)) :
    Tendsto actualVariance atTop
      (nhds
        ((1 / denominator ^ 2) * (1 / normalizer) *
          weightedScoreCellMomentLimit cells
            (fun cell =>
              (contributionLimit cell - target * weightLimit cell) ^ 2)
            massLimit)) :=
  tendsto_actualBootstrapVariance_of_eventually_cell_contribution_weight_limits_and_uniformAssignment_base_ratio_full_support_univ_all_unit_error_bounds
    (l := atTop) cells scoreComponents biasComponents sample draws
    assignment score contribution weight target denominator normalizer
    sampleSize cellContribution cellWeight contributionLimit weightLimit
    massLimit actualVariance scoreReplicationError biasCorrectionError
    scoreUnitComponent biasUnitComponent scoreUnitEnvelope biasUnitEnvelope
    hunit_card hdraw_card hsampleSize_ne hsample_univ hdraws_univ hbase
    hvariance_decomp hcover_all hcontributionCell_all hweightCell_all
    hcontributionLimit hweightLimit
    (cellwise_mass_lln_of_glivenkoCantelli_bridge
      cells massLimit sample (fun _index _unit => 1) score
      (weighted_indicator_array_lln_of_l1BracketingNumber_obligations
        cells massLimit sample (fun _index _unit => 1) score obligations))
    hscore_construct_univ hscore_component_bound_all
    hscore_envelope_tendsto hbias_construct_univ
    hbias_component_bound_all hbias_envelope_tendsto

/--
Finite `L1(P)` bracketing version of the full-support uniform all-unit route
where the base identity is supplied as a finite Hájek ratio equality.
-/
theorem
    tendsto_actualBootstrapVariance_of_eventually_cell_contribution_weight_limits_l1BracketingNumber_obligations_and_uniformAssignment_hajek_base_ratio_full_support_univ_all_unit_error_bounds
    [Fintype Unit] [Fintype Draw] [DecidableEq Unit] [DecidableEq Draw]
    [Nonempty Unit] [DecidableEq Cell] [DecidableEq ScoreComponent]
    [DecidableEq BiasComponent]
    {Bracket : Type*} [Fintype Bracket]
    (cells : Finset Cell)
    (scoreComponents : Finset ScoreComponent)
    (biasComponents : Finset BiasComponent)
    (sample : ℕ -> Finset Unit) (draws : ℕ -> Finset Draw)
    (assignment : ℕ -> Draw -> Unit)
    (score : ℕ -> Unit -> Cell)
    (contribution weight : ℕ -> Unit -> Real)
    (target denominator normalizer sampleSize : Real)
    (cellContribution cellWeight : ℕ -> Cell -> Real)
    (contributionLimit weightLimit massLimit : Cell -> Real)
    (actualVariance scoreReplicationError biasCorrectionError : ℕ -> Real)
    (scoreUnitComponent : ℕ -> Unit -> ScoreComponent -> Real)
    (biasUnitComponent : ℕ -> Unit -> BiasComponent -> Real)
    (scoreUnitEnvelope : ℕ -> ScoreComponent -> Real)
    (biasUnitEnvelope : ℕ -> BiasComponent -> Real)
    (hunit_card : (Fintype.card Unit : Real) = sampleSize)
    (hdraw_card : (Fintype.card Draw : Real) = sampleSize)
    (hsampleSize_ne : sampleSize ≠ 0)
    (hsample_univ :
      sample =ᶠ[atTop] fun _index => (Finset.univ : Finset Unit))
    (hdraws_univ :
      draws =ᶠ[atTop] fun _index => (Finset.univ : Finset Draw))
    (hbase_den_ne :
      ∀ᶠ index in atTop,
        baseLinearizedSum (Finset.univ : Finset Unit)
          (weight index) ≠ 0)
    (hbase_ratio :
      ∀ᶠ index in atTop,
        baseLinearizedSum (Finset.univ : Finset Unit)
            (contribution index) /
          baseLinearizedSum (Finset.univ : Finset Unit)
            (weight index) =
          target)
    (hvariance_decomp :
      actualVariance =ᶠ[atTop]
        (fun index =>
          (1 / denominator ^ 2) * (1 / normalizer) *
              multiplierPerturbationSecondMoment
                (uniformAssignmentSupport Unit Draw)
                (uniformAssignmentMass Unit Draw)
                (sample index)
                (fun assignment unit =>
                  multinomialCountFromDrawIndicators (draws index)
                    (fun assignment draw unit =>
                      oneHotAssignmentIndicator assignment draw unit)
                    assignment unit)
                (fun unit =>
                  contribution index unit - target * weight index unit) +
            scoreReplicationError index + biasCorrectionError index))
    (hcover_all :
      ∀ᶠ index in atTop,
        ∀ unit, score index unit ∈ cells)
    (hcontributionCell_all :
      ∀ᶠ index in atTop,
        ∀ unit,
          cellContribution index (score index unit) =
            contribution index unit)
    (hweightCell_all :
      ∀ᶠ index in atTop,
        ∀ unit,
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
    (hscore_construct_univ :
      scoreReplicationError =ᶠ[atTop]
        (fun index =>
          ∑ component ∈ scoreComponents, ∑ unit : Unit,
            (multinomialCountFromDrawIndicators (Finset.univ : Finset Draw)
                (fun assignment draw unit =>
                  oneHotAssignmentIndicator assignment draw unit)
                (assignment index) unit - 1) *
              scoreUnitComponent index unit component))
    (hscore_component_bound_all :
      ∀ᶠ index in atTop,
        ∀ unit,
          ∀ component, component ∈ scoreComponents ->
            |scoreUnitComponent index unit component| ≤
              scoreUnitEnvelope index component)
    (hscore_envelope_tendsto :
      ∀ component, component ∈ scoreComponents ->
        Tendsto (fun index => scoreUnitEnvelope index component)
          atTop (nhds 0))
    (hbias_construct_univ :
      biasCorrectionError =ᶠ[atTop]
        (fun index =>
          ∑ component ∈ biasComponents, ∑ unit : Unit,
            (multinomialCountFromDrawIndicators (Finset.univ : Finset Draw)
                (fun assignment draw unit =>
                  oneHotAssignmentIndicator assignment draw unit)
                (assignment index) unit - 1) *
              biasUnitComponent index unit component))
    (hbias_component_bound_all :
      ∀ᶠ index in atTop,
        ∀ unit,
          ∀ component, component ∈ biasComponents ->
            |biasUnitComponent index unit component| ≤
              biasUnitEnvelope index component)
    (hbias_envelope_tendsto :
      ∀ component, component ∈ biasComponents ->
        Tendsto (fun index => biasUnitEnvelope index component)
          atTop (nhds 0)) :
    Tendsto actualVariance atTop
      (nhds
        ((1 / denominator ^ 2) * (1 / normalizer) *
          weightedScoreCellMomentLimit cells
            (fun cell =>
              (contributionLimit cell - target * weightLimit cell) ^ 2)
            massLimit)) :=
  tendsto_actualBootstrapVariance_of_eventually_cell_contribution_weight_limits_and_uniformAssignment_hajek_base_ratio_full_support_univ_all_unit_error_bounds
    (l := atTop) cells scoreComponents biasComponents sample draws
    assignment score contribution weight target denominator normalizer
    sampleSize cellContribution cellWeight contributionLimit weightLimit
    massLimit actualVariance scoreReplicationError biasCorrectionError
    scoreUnitComponent biasUnitComponent scoreUnitEnvelope biasUnitEnvelope
    hunit_card hdraw_card hsampleSize_ne hsample_univ hdraws_univ
    hbase_den_ne hbase_ratio hvariance_decomp hcover_all
    hcontributionCell_all hweightCell_all hcontributionLimit hweightLimit
    (cellwise_mass_lln_of_glivenkoCantelli_bridge
      cells massLimit sample (fun _index _unit => 1) score
      (weighted_indicator_array_lln_of_l1BracketingNumber_obligations
        cells massLimit sample (fun _index _unit => 1) score obligations))
    hscore_construct_univ hscore_component_bound_all
    hscore_envelope_tendsto hbias_construct_univ
    hbias_component_bound_all hbias_envelope_tendsto

/--
VdV&W endpoint-assembly version of the full-support uniform all-unit route.
The score-cell mass LLN is supplied by the endpoint assembly, while all
deterministic coverage and envelope bounds are stated over every unit.
-/
theorem
    tendsto_actualBootstrapVariance_of_eventually_cell_contribution_weight_limits_vdvw241_endpoint_assembly_and_uniformAssignment_base_ratio_full_support_univ_all_unit_error_bounds
    [Fintype Unit] [Fintype Draw] [DecidableEq Unit] [DecidableEq Draw]
    [Nonempty Unit] [DecidableEq Cell] [DecidableEq ScoreComponent]
    [DecidableEq BiasComponent]
    {Bracket : Type*} [Fintype Bracket]
    (cells : Finset Cell)
    (scoreComponents : Finset ScoreComponent)
    (biasComponents : Finset BiasComponent)
    (sample : ℕ -> Finset Unit) (draws : ℕ -> Finset Draw)
    (assignment : ℕ -> Draw -> Unit)
    (score : ℕ -> Unit -> Cell)
    (contribution weight : ℕ -> Unit -> Real)
    (target denominator normalizer sampleSize : Real)
    (cellContribution cellWeight : ℕ -> Cell -> Real)
    (contributionLimit weightLimit massLimit : Cell -> Real)
    (actualVariance scoreReplicationError biasCorrectionError : ℕ -> Real)
    (scoreUnitComponent : ℕ -> Unit -> ScoreComponent -> Real)
    (biasUnitComponent : ℕ -> Unit -> BiasComponent -> Real)
    (scoreUnitEnvelope : ℕ -> ScoreComponent -> Real)
    (biasUnitEnvelope : ℕ -> BiasComponent -> Real)
    (hunit_card : (Fintype.card Unit : Real) = sampleSize)
    (hdraw_card : (Fintype.card Draw : Real) = sampleSize)
    (hsampleSize_ne : sampleSize ≠ 0)
    (hsample_univ :
      sample =ᶠ[atTop] fun _index => (Finset.univ : Finset Unit))
    (hdraws_univ :
      draws =ᶠ[atTop] fun _index => (Finset.univ : Finset Draw))
    (hbase :
      ∀ᶠ index in atTop,
        baseLinearizedSum (Finset.univ : Finset Unit)
            (contribution index) =
          target *
            baseLinearizedSum (Finset.univ : Finset Unit)
              (weight index))
    (hvariance_decomp :
      actualVariance =ᶠ[atTop]
        (fun index =>
          (1 / denominator ^ 2) * (1 / normalizer) *
              multiplierPerturbationSecondMoment
                (uniformAssignmentSupport Unit Draw)
                (uniformAssignmentMass Unit Draw)
                (sample index)
                (fun assignment unit =>
                  multinomialCountFromDrawIndicators (draws index)
                    (fun assignment draw unit =>
                      oneHotAssignmentIndicator assignment draw unit)
                    assignment unit)
                (fun unit =>
                  contribution index unit - target * weight index unit) +
            scoreReplicationError index + biasCorrectionError index))
    (hcover_all :
      ∀ᶠ index in atTop,
        ∀ unit, score index unit ∈ cells)
    (hcontributionCell_all :
      ∀ᶠ index in atTop,
        ∀ unit,
          cellContribution index (score index unit) =
            contribution index unit)
    (hweightCell_all :
      ∀ᶠ index in atTop,
        ∀ unit,
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
    (hscore_construct_univ :
      scoreReplicationError =ᶠ[atTop]
        (fun index =>
          ∑ component ∈ scoreComponents, ∑ unit : Unit,
            (multinomialCountFromDrawIndicators (Finset.univ : Finset Draw)
                (fun assignment draw unit =>
                  oneHotAssignmentIndicator assignment draw unit)
                (assignment index) unit - 1) *
              scoreUnitComponent index unit component))
    (hscore_component_bound_all :
      ∀ᶠ index in atTop,
        ∀ unit,
          ∀ component, component ∈ scoreComponents ->
            |scoreUnitComponent index unit component| ≤
              scoreUnitEnvelope index component)
    (hscore_envelope_tendsto :
      ∀ component, component ∈ scoreComponents ->
        Tendsto (fun index => scoreUnitEnvelope index component)
          atTop (nhds 0))
    (hbias_construct_univ :
      biasCorrectionError =ᶠ[atTop]
        (fun index =>
          ∑ component ∈ biasComponents, ∑ unit : Unit,
            (multinomialCountFromDrawIndicators (Finset.univ : Finset Draw)
                (fun assignment draw unit =>
                  oneHotAssignmentIndicator assignment draw unit)
                (assignment index) unit - 1) *
              biasUnitComponent index unit component))
    (hbias_component_bound_all :
      ∀ᶠ index in atTop,
        ∀ unit,
          ∀ component, component ∈ biasComponents ->
            |biasUnitComponent index unit component| ≤
              biasUnitEnvelope index component)
    (hbias_envelope_tendsto :
      ∀ component, component ∈ biasComponents ->
        Tendsto (fun index => biasUnitEnvelope index component)
          atTop (nhds 0)) :
    Tendsto actualVariance atTop
      (nhds
        ((1 / denominator ^ 2) * (1 / normalizer) *
          weightedScoreCellMomentLimit cells
            (fun cell =>
              (contributionLimit cell - target * weightLimit cell) ^ 2)
            massLimit)) :=
  tendsto_actualBootstrapVariance_of_eventually_cell_contribution_weight_limits_and_uniformAssignment_base_ratio_full_support_univ_all_unit_error_bounds
    (l := atTop) cells scoreComponents biasComponents sample draws
    assignment score contribution weight target denominator normalizer
    sampleSize cellContribution cellWeight contributionLimit weightLimit
    massLimit actualVariance scoreReplicationError biasCorrectionError
    scoreUnitComponent biasUnitComponent scoreUnitEnvelope biasUnitEnvelope
    hunit_card hdraw_card hsampleSize_ne hsample_univ hdraws_univ hbase
    hvariance_decomp hcover_all hcontributionCell_all hweightCell_all
    hcontributionLimit hweightLimit
    (cellwise_mass_lln_of_glivenkoCantelli_bridge
      cells massLimit sample (fun _index _unit => 1) score
      (weighted_indicator_array_lln_of_vdvw241_endpoint_assembly
        cells massLimit sample (fun _index _unit => 1) score assembly))
    hscore_construct_univ hscore_component_bound_all
    hscore_envelope_tendsto hbias_construct_univ
    hbias_component_bound_all hbias_envelope_tendsto

/--
VdV&W endpoint-assembly version of the full-support uniform all-unit route
where the base identity is supplied as a finite Hájek ratio equality.
-/
theorem
    tendsto_actualBootstrapVariance_of_eventually_cell_contribution_weight_limits_vdvw241_endpoint_assembly_and_uniformAssignment_hajek_base_ratio_full_support_univ_all_unit_error_bounds
    [Fintype Unit] [Fintype Draw] [DecidableEq Unit] [DecidableEq Draw]
    [Nonempty Unit] [DecidableEq Cell] [DecidableEq ScoreComponent]
    [DecidableEq BiasComponent]
    {Bracket : Type*} [Fintype Bracket]
    (cells : Finset Cell)
    (scoreComponents : Finset ScoreComponent)
    (biasComponents : Finset BiasComponent)
    (sample : ℕ -> Finset Unit) (draws : ℕ -> Finset Draw)
    (assignment : ℕ -> Draw -> Unit)
    (score : ℕ -> Unit -> Cell)
    (contribution weight : ℕ -> Unit -> Real)
    (target denominator normalizer sampleSize : Real)
    (cellContribution cellWeight : ℕ -> Cell -> Real)
    (contributionLimit weightLimit massLimit : Cell -> Real)
    (actualVariance scoreReplicationError biasCorrectionError : ℕ -> Real)
    (scoreUnitComponent : ℕ -> Unit -> ScoreComponent -> Real)
    (biasUnitComponent : ℕ -> Unit -> BiasComponent -> Real)
    (scoreUnitEnvelope : ℕ -> ScoreComponent -> Real)
    (biasUnitEnvelope : ℕ -> BiasComponent -> Real)
    (hunit_card : (Fintype.card Unit : Real) = sampleSize)
    (hdraw_card : (Fintype.card Draw : Real) = sampleSize)
    (hsampleSize_ne : sampleSize ≠ 0)
    (hsample_univ :
      sample =ᶠ[atTop] fun _index => (Finset.univ : Finset Unit))
    (hdraws_univ :
      draws =ᶠ[atTop] fun _index => (Finset.univ : Finset Draw))
    (hbase_den_ne :
      ∀ᶠ index in atTop,
        baseLinearizedSum (Finset.univ : Finset Unit)
          (weight index) ≠ 0)
    (hbase_ratio :
      ∀ᶠ index in atTop,
        baseLinearizedSum (Finset.univ : Finset Unit)
            (contribution index) /
          baseLinearizedSum (Finset.univ : Finset Unit)
            (weight index) =
          target)
    (hvariance_decomp :
      actualVariance =ᶠ[atTop]
        (fun index =>
          (1 / denominator ^ 2) * (1 / normalizer) *
              multiplierPerturbationSecondMoment
                (uniformAssignmentSupport Unit Draw)
                (uniformAssignmentMass Unit Draw)
                (sample index)
                (fun assignment unit =>
                  multinomialCountFromDrawIndicators (draws index)
                    (fun assignment draw unit =>
                      oneHotAssignmentIndicator assignment draw unit)
                    assignment unit)
                (fun unit =>
                  contribution index unit - target * weight index unit) +
            scoreReplicationError index + biasCorrectionError index))
    (hcover_all :
      ∀ᶠ index in atTop,
        ∀ unit, score index unit ∈ cells)
    (hcontributionCell_all :
      ∀ᶠ index in atTop,
        ∀ unit,
          cellContribution index (score index unit) =
            contribution index unit)
    (hweightCell_all :
      ∀ᶠ index in atTop,
        ∀ unit,
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
    (hscore_construct_univ :
      scoreReplicationError =ᶠ[atTop]
        (fun index =>
          ∑ component ∈ scoreComponents, ∑ unit : Unit,
            (multinomialCountFromDrawIndicators (Finset.univ : Finset Draw)
                (fun assignment draw unit =>
                  oneHotAssignmentIndicator assignment draw unit)
                (assignment index) unit - 1) *
              scoreUnitComponent index unit component))
    (hscore_component_bound_all :
      ∀ᶠ index in atTop,
        ∀ unit,
          ∀ component, component ∈ scoreComponents ->
            |scoreUnitComponent index unit component| ≤
              scoreUnitEnvelope index component)
    (hscore_envelope_tendsto :
      ∀ component, component ∈ scoreComponents ->
        Tendsto (fun index => scoreUnitEnvelope index component)
          atTop (nhds 0))
    (hbias_construct_univ :
      biasCorrectionError =ᶠ[atTop]
        (fun index =>
          ∑ component ∈ biasComponents, ∑ unit : Unit,
            (multinomialCountFromDrawIndicators (Finset.univ : Finset Draw)
                (fun assignment draw unit =>
                  oneHotAssignmentIndicator assignment draw unit)
                (assignment index) unit - 1) *
              biasUnitComponent index unit component))
    (hbias_component_bound_all :
      ∀ᶠ index in atTop,
        ∀ unit,
          ∀ component, component ∈ biasComponents ->
            |biasUnitComponent index unit component| ≤
              biasUnitEnvelope index component)
    (hbias_envelope_tendsto :
      ∀ component, component ∈ biasComponents ->
        Tendsto (fun index => biasUnitEnvelope index component)
          atTop (nhds 0)) :
    Tendsto actualVariance atTop
      (nhds
        ((1 / denominator ^ 2) * (1 / normalizer) *
          weightedScoreCellMomentLimit cells
            (fun cell =>
              (contributionLimit cell - target * weightLimit cell) ^ 2)
            massLimit)) :=
  tendsto_actualBootstrapVariance_of_eventually_cell_contribution_weight_limits_and_uniformAssignment_hajek_base_ratio_full_support_univ_all_unit_error_bounds
    (l := atTop) cells scoreComponents biasComponents sample draws
    assignment score contribution weight target denominator normalizer
    sampleSize cellContribution cellWeight contributionLimit weightLimit
    massLimit actualVariance scoreReplicationError biasCorrectionError
    scoreUnitComponent biasUnitComponent scoreUnitEnvelope biasUnitEnvelope
    hunit_card hdraw_card hsampleSize_ne hsample_univ hdraws_univ
    hbase_den_ne hbase_ratio hvariance_decomp hcover_all
    hcontributionCell_all hweightCell_all hcontributionLimit hweightLimit
    (cellwise_mass_lln_of_glivenkoCantelli_bridge
      cells massLimit sample (fun _index _unit => 1) score
      (weighted_indicator_array_lln_of_vdvw241_endpoint_assembly
        cells massLimit sample (fun _index _unit => 1) score assembly))
    hscore_construct_univ hscore_component_bound_all
    hscore_envelope_tendsto hbias_construct_univ
    hbias_component_bound_all hbias_envelope_tendsto

/--
Literal full finite-support version of the uniform all-unit route.  The
sample and draw supports are fixed to `Finset.univ`, so no eventual support
equalities are required.
-/
theorem tendsto_actualBootstrapVariance_of_eventually_cell_contribution_weight_limits_and_uniformAssignment_hajek_base_ratio_univ_support_all_unit_error_bounds
    [Fintype Unit] [Fintype Draw] [DecidableEq Unit] [DecidableEq Draw]
    [Nonempty Unit] [DecidableEq Cell] [DecidableEq ScoreComponent]
    [DecidableEq BiasComponent]
    (cells : Finset Cell)
    (scoreComponents : Finset ScoreComponent)
    (biasComponents : Finset BiasComponent)
    (assignment : Index -> Draw -> Unit)
    (score : Index -> Unit -> Cell)
    (contribution weight : Index -> Unit -> Real)
    (target denominator normalizer sampleSize : Real)
    (cellContribution cellWeight : Index -> Cell -> Real)
    (contributionLimit weightLimit massLimit : Cell -> Real)
    (actualVariance scoreReplicationError biasCorrectionError : Index -> Real)
    (scoreUnitComponent : Index -> Unit -> ScoreComponent -> Real)
    (biasUnitComponent : Index -> Unit -> BiasComponent -> Real)
    (scoreUnitEnvelope : Index -> ScoreComponent -> Real)
    (biasUnitEnvelope : Index -> BiasComponent -> Real)
    (hunit_card : (Fintype.card Unit : Real) = sampleSize)
    (hdraw_card : (Fintype.card Draw : Real) = sampleSize)
    (hsampleSize_ne : sampleSize ≠ 0)
    (hbase_den_ne :
      ∀ᶠ index in l,
        baseLinearizedSum (Finset.univ : Finset Unit)
          (weight index) ≠ 0)
    (hbase_ratio :
      ∀ᶠ index in l,
        baseLinearizedSum (Finset.univ : Finset Unit)
            (contribution index) /
          baseLinearizedSum (Finset.univ : Finset Unit)
            (weight index) =
          target)
    (hvariance_decomp :
      actualVariance =ᶠ[l]
        (fun index =>
          (1 / denominator ^ 2) * (1 / normalizer) *
              multiplierPerturbationSecondMoment
                (uniformAssignmentSupport Unit Draw)
                (uniformAssignmentMass Unit Draw)
                (Finset.univ : Finset Unit)
                (fun assignment unit =>
                  multinomialCountFromDrawIndicators
                    (Finset.univ : Finset Draw)
                    (fun assignment draw unit =>
                      oneHotAssignmentIndicator assignment draw unit)
                    assignment unit)
                (fun unit =>
                  contribution index unit - target * weight index unit) +
            scoreReplicationError index + biasCorrectionError index))
    (hcover_all :
      ∀ᶠ index in l,
        ∀ unit, score index unit ∈ cells)
    (hcontributionCell_all :
      ∀ᶠ index in l,
        ∀ unit,
          cellContribution index (score index unit) =
            contribution index unit)
    (hweightCell_all :
      ∀ᶠ index in l,
        ∀ unit,
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
      cellwiseScoreCellMassLLN (l := l) cells
        (fun _index => (Finset.univ : Finset Unit))
        (fun _index _unit => 1) score massLimit)
    (hscore_construct_univ :
      scoreReplicationError =ᶠ[l]
        (fun index =>
          ∑ component ∈ scoreComponents, ∑ unit : Unit,
            (multinomialCountFromDrawIndicators (Finset.univ : Finset Draw)
                (fun assignment draw unit =>
                  oneHotAssignmentIndicator assignment draw unit)
                (assignment index) unit - 1) *
              scoreUnitComponent index unit component))
    (hscore_component_bound_all :
      ∀ᶠ index in l,
        ∀ unit,
          ∀ component, component ∈ scoreComponents ->
            |scoreUnitComponent index unit component| ≤
              scoreUnitEnvelope index component)
    (hscore_envelope_tendsto :
      ∀ component, component ∈ scoreComponents ->
        Tendsto (fun index => scoreUnitEnvelope index component)
          l (nhds 0))
    (hbias_construct_univ :
      biasCorrectionError =ᶠ[l]
        (fun index =>
          ∑ component ∈ biasComponents, ∑ unit : Unit,
            (multinomialCountFromDrawIndicators (Finset.univ : Finset Draw)
                (fun assignment draw unit =>
                  oneHotAssignmentIndicator assignment draw unit)
                (assignment index) unit - 1) *
              biasUnitComponent index unit component))
    (hbias_component_bound_all :
      ∀ᶠ index in l,
        ∀ unit,
          ∀ component, component ∈ biasComponents ->
            |biasUnitComponent index unit component| ≤
              biasUnitEnvelope index component)
    (hbias_envelope_tendsto :
      ∀ component, component ∈ biasComponents ->
        Tendsto (fun index => biasUnitEnvelope index component)
          l (nhds 0)) :
    Tendsto actualVariance l
      (nhds
        ((1 / denominator ^ 2) * (1 / normalizer) *
          weightedScoreCellMomentLimit cells
            (fun cell =>
              (contributionLimit cell - target * weightLimit cell) ^ 2)
            massLimit)) :=
  tendsto_actualBootstrapVariance_of_eventually_cell_contribution_weight_limits_and_uniformAssignment_hajek_base_ratio_full_support_univ_all_unit_error_bounds
    (l := l) cells scoreComponents biasComponents
    (fun _index => (Finset.univ : Finset Unit))
    (fun _index => (Finset.univ : Finset Draw)) assignment score
    contribution weight target denominator normalizer sampleSize
    cellContribution cellWeight contributionLimit weightLimit massLimit
    actualVariance scoreReplicationError biasCorrectionError
    scoreUnitComponent biasUnitComponent scoreUnitEnvelope biasUnitEnvelope
    hunit_card hdraw_card hsampleSize_ne (by simp) (by simp)
    hbase_den_ne hbase_ratio hvariance_decomp hcover_all
    hcontributionCell_all hweightCell_all hcontributionLimit hweightLimit
    hmass hscore_construct_univ hscore_component_bound_all
    hscore_envelope_tendsto hbias_construct_univ
    hbias_component_bound_all hbias_envelope_tendsto

/--
Concrete finite-expectation variance version of the literal full-support
uniform route.  The actual variance sequence is the normalized one-hot
multiplier second moment plus the score-replication and bias-correction
errors, so no separate variance-decomposition premise is needed.
-/
theorem tendsto_concreteUniformAssignmentBootstrapVariance_of_eventually_cell_contribution_weight_limits_and_hajek_base_ratio_univ_support_all_unit_error_bounds
    [Fintype Unit] [Fintype Draw] [DecidableEq Unit] [DecidableEq Draw]
    [Nonempty Unit] [DecidableEq Cell] [DecidableEq ScoreComponent]
    [DecidableEq BiasComponent]
    (cells : Finset Cell)
    (scoreComponents : Finset ScoreComponent)
    (biasComponents : Finset BiasComponent)
    (assignment : Index -> Draw -> Unit)
    (score : Index -> Unit -> Cell)
    (contribution weight : Index -> Unit -> Real)
    (target denominator normalizer sampleSize : Real)
    (cellContribution cellWeight : Index -> Cell -> Real)
    (contributionLimit weightLimit massLimit : Cell -> Real)
    (scoreReplicationError biasCorrectionError : Index -> Real)
    (scoreUnitComponent : Index -> Unit -> ScoreComponent -> Real)
    (biasUnitComponent : Index -> Unit -> BiasComponent -> Real)
    (scoreUnitEnvelope : Index -> ScoreComponent -> Real)
    (biasUnitEnvelope : Index -> BiasComponent -> Real)
    (hunit_card : (Fintype.card Unit : Real) = sampleSize)
    (hdraw_card : (Fintype.card Draw : Real) = sampleSize)
    (hsampleSize_ne : sampleSize ≠ 0)
    (hbase_den_ne :
      ∀ᶠ index in l,
        baseLinearizedSum (Finset.univ : Finset Unit)
          (weight index) ≠ 0)
    (hbase_ratio :
      ∀ᶠ index in l,
        baseLinearizedSum (Finset.univ : Finset Unit)
            (contribution index) /
          baseLinearizedSum (Finset.univ : Finset Unit)
            (weight index) =
          target)
    (hcover_all :
      ∀ᶠ index in l,
        ∀ unit, score index unit ∈ cells)
    (hcontributionCell_all :
      ∀ᶠ index in l,
        ∀ unit,
          cellContribution index (score index unit) =
            contribution index unit)
    (hweightCell_all :
      ∀ᶠ index in l,
        ∀ unit,
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
      cellwiseScoreCellMassLLN (l := l) cells
        (fun _index => (Finset.univ : Finset Unit))
        (fun _index _unit => 1) score massLimit)
    (hscore_construct_univ :
      scoreReplicationError =ᶠ[l]
        (fun index =>
          ∑ component ∈ scoreComponents, ∑ unit : Unit,
            (multinomialCountFromDrawIndicators (Finset.univ : Finset Draw)
                (fun assignment draw unit =>
                  oneHotAssignmentIndicator assignment draw unit)
                (assignment index) unit - 1) *
              scoreUnitComponent index unit component))
    (hscore_component_bound_all :
      ∀ᶠ index in l,
        ∀ unit,
          ∀ component, component ∈ scoreComponents ->
            |scoreUnitComponent index unit component| ≤
              scoreUnitEnvelope index component)
    (hscore_envelope_tendsto :
      ∀ component, component ∈ scoreComponents ->
        Tendsto (fun index => scoreUnitEnvelope index component)
          l (nhds 0))
    (hbias_construct_univ :
      biasCorrectionError =ᶠ[l]
        (fun index =>
          ∑ component ∈ biasComponents, ∑ unit : Unit,
            (multinomialCountFromDrawIndicators (Finset.univ : Finset Draw)
                (fun assignment draw unit =>
                  oneHotAssignmentIndicator assignment draw unit)
                (assignment index) unit - 1) *
              biasUnitComponent index unit component))
    (hbias_component_bound_all :
      ∀ᶠ index in l,
        ∀ unit,
          ∀ component, component ∈ biasComponents ->
            |biasUnitComponent index unit component| ≤
              biasUnitEnvelope index component)
    (hbias_envelope_tendsto :
      ∀ component, component ∈ biasComponents ->
        Tendsto (fun index => biasUnitEnvelope index component)
          l (nhds 0)) :
    Tendsto
      (fun index =>
        (1 / denominator ^ 2) * (1 / normalizer) *
            multiplierPerturbationSecondMoment
              (uniformAssignmentSupport Unit Draw)
              (uniformAssignmentMass Unit Draw)
              (Finset.univ : Finset Unit)
              (fun assignment unit =>
                multinomialCountFromDrawIndicators
                  (Finset.univ : Finset Draw)
                  (fun assignment draw unit =>
                    oneHotAssignmentIndicator assignment draw unit)
                  assignment unit)
              (fun unit =>
                contribution index unit - target * weight index unit) +
          scoreReplicationError index + biasCorrectionError index)
      l
      (nhds
        ((1 / denominator ^ 2) * (1 / normalizer) *
          weightedScoreCellMomentLimit cells
            (fun cell =>
              (contributionLimit cell - target * weightLimit cell) ^ 2)
            massLimit)) := by
  have hvariance_decomp :
      (fun index =>
        (1 / denominator ^ 2) * (1 / normalizer) *
            multiplierPerturbationSecondMoment
              (uniformAssignmentSupport Unit Draw)
              (uniformAssignmentMass Unit Draw)
              (Finset.univ : Finset Unit)
              (fun assignment unit =>
                multinomialCountFromDrawIndicators
                  (Finset.univ : Finset Draw)
                  (fun assignment draw unit =>
                    oneHotAssignmentIndicator assignment draw unit)
                  assignment unit)
              (fun unit =>
                contribution index unit - target * weight index unit) +
          scoreReplicationError index + biasCorrectionError index) =ᶠ[l]
        (fun index =>
          (1 / denominator ^ 2) * (1 / normalizer) *
              multiplierPerturbationSecondMoment
                (uniformAssignmentSupport Unit Draw)
                (uniformAssignmentMass Unit Draw)
                (Finset.univ : Finset Unit)
                (fun assignment unit =>
                  multinomialCountFromDrawIndicators
                    (Finset.univ : Finset Draw)
                    (fun assignment draw unit =>
                      oneHotAssignmentIndicator assignment draw unit)
                    assignment unit)
                (fun unit =>
                  contribution index unit - target * weight index unit) +
            scoreReplicationError index + biasCorrectionError index) := by
    filter_upwards [] with index
    rfl
  exact
    tendsto_actualBootstrapVariance_of_eventually_cell_contribution_weight_limits_and_uniformAssignment_hajek_base_ratio_univ_support_all_unit_error_bounds
      (l := l) cells scoreComponents biasComponents assignment score
      contribution weight target denominator normalizer sampleSize
      cellContribution cellWeight contributionLimit weightLimit massLimit
      (fun index =>
        (1 / denominator ^ 2) * (1 / normalizer) *
            multiplierPerturbationSecondMoment
              (uniformAssignmentSupport Unit Draw)
              (uniformAssignmentMass Unit Draw)
              (Finset.univ : Finset Unit)
              (fun assignment unit =>
                multinomialCountFromDrawIndicators
                  (Finset.univ : Finset Draw)
                  (fun assignment draw unit =>
                    oneHotAssignmentIndicator assignment draw unit)
                  assignment unit)
              (fun unit =>
                contribution index unit - target * weight index unit) +
          scoreReplicationError index + biasCorrectionError index)
      scoreReplicationError biasCorrectionError scoreUnitComponent
      biasUnitComponent scoreUnitEnvelope biasUnitEnvelope hunit_card
      hdraw_card hsampleSize_ne hbase_den_ne hbase_ratio hvariance_decomp
      hcover_all hcontributionCell_all hweightCell_all
      hcontributionLimit hweightLimit hmass hscore_construct_univ
      hscore_component_bound_all hscore_envelope_tendsto
      hbias_construct_univ hbias_component_bound_all
      hbias_envelope_tendsto

/--
Concrete full-support uniform route where the score/bias envelopes are
constructed internally as finite absolute sums over the full unit support.
The caller only supplies pointwise convergence of every fixed unit component.
-/
theorem tendsto_concreteUniformAssignmentBootstrapVariance_of_eventually_cell_contribution_weight_limits_and_hajek_base_ratio_univ_support_unit_component_tendsto_bounds
    [Fintype Unit] [Fintype Draw] [DecidableEq Unit] [DecidableEq Draw]
    [Nonempty Unit] [DecidableEq Cell] [DecidableEq ScoreComponent]
    [DecidableEq BiasComponent]
    (cells : Finset Cell)
    (scoreComponents : Finset ScoreComponent)
    (biasComponents : Finset BiasComponent)
    (assignment : Index -> Draw -> Unit)
    (score : Index -> Unit -> Cell)
    (contribution weight : Index -> Unit -> Real)
    (target denominator normalizer sampleSize : Real)
    (cellContribution cellWeight : Index -> Cell -> Real)
    (contributionLimit weightLimit massLimit : Cell -> Real)
    (scoreReplicationError biasCorrectionError : Index -> Real)
    (scoreUnitComponent : Index -> Unit -> ScoreComponent -> Real)
    (biasUnitComponent : Index -> Unit -> BiasComponent -> Real)
    (hunit_card : (Fintype.card Unit : Real) = sampleSize)
    (hdraw_card : (Fintype.card Draw : Real) = sampleSize)
    (hsampleSize_ne : sampleSize ≠ 0)
    (hbase_den_ne :
      ∀ᶠ index in l,
        baseLinearizedSum (Finset.univ : Finset Unit)
          (weight index) ≠ 0)
    (hbase_ratio :
      ∀ᶠ index in l,
        baseLinearizedSum (Finset.univ : Finset Unit)
            (contribution index) /
          baseLinearizedSum (Finset.univ : Finset Unit)
            (weight index) =
          target)
    (hcover_all :
      ∀ᶠ index in l,
        ∀ unit, score index unit ∈ cells)
    (hcontributionCell_all :
      ∀ᶠ index in l,
        ∀ unit,
          cellContribution index (score index unit) =
            contribution index unit)
    (hweightCell_all :
      ∀ᶠ index in l,
        ∀ unit,
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
      cellwiseScoreCellMassLLN (l := l) cells
        (fun _index => (Finset.univ : Finset Unit))
        (fun _index _unit => 1) score massLimit)
    (hscore_construct_univ :
      scoreReplicationError =ᶠ[l]
        (fun index =>
          ∑ component ∈ scoreComponents, ∑ unit : Unit,
            (multinomialCountFromDrawIndicators (Finset.univ : Finset Draw)
                (fun assignment draw unit =>
                  oneHotAssignmentIndicator assignment draw unit)
                (assignment index) unit - 1) *
              scoreUnitComponent index unit component))
    (hscore_unit_tendsto :
      ∀ unit,
        ∀ component, component ∈ scoreComponents ->
          Tendsto (fun index => scoreUnitComponent index unit component)
            l (nhds 0))
    (hbias_construct_univ :
      biasCorrectionError =ᶠ[l]
        (fun index =>
          ∑ component ∈ biasComponents, ∑ unit : Unit,
            (multinomialCountFromDrawIndicators (Finset.univ : Finset Draw)
                (fun assignment draw unit =>
                  oneHotAssignmentIndicator assignment draw unit)
                (assignment index) unit - 1) *
              biasUnitComponent index unit component))
    (hbias_unit_tendsto :
      ∀ unit,
        ∀ component, component ∈ biasComponents ->
          Tendsto (fun index => biasUnitComponent index unit component)
            l (nhds 0)) :
    Tendsto
      (fun index =>
        (1 / denominator ^ 2) * (1 / normalizer) *
            multiplierPerturbationSecondMoment
              (uniformAssignmentSupport Unit Draw)
              (uniformAssignmentMass Unit Draw)
              (Finset.univ : Finset Unit)
              (fun assignment unit =>
                multinomialCountFromDrawIndicators
                  (Finset.univ : Finset Draw)
                  (fun assignment draw unit =>
                    oneHotAssignmentIndicator assignment draw unit)
                  assignment unit)
              (fun unit =>
                contribution index unit - target * weight index unit) +
          scoreReplicationError index + biasCorrectionError index)
      l
      (nhds
        ((1 / denominator ^ 2) * (1 / normalizer) *
          weightedScoreCellMomentLimit cells
            (fun cell =>
              (contributionLimit cell - target * weightLimit cell) ^ 2)
            massLimit)) :=
  tendsto_concreteUniformAssignmentBootstrapVariance_of_eventually_cell_contribution_weight_limits_and_hajek_base_ratio_univ_support_all_unit_error_bounds
    (l := l) cells scoreComponents biasComponents assignment score
    contribution weight target denominator normalizer sampleSize
    cellContribution cellWeight contributionLimit weightLimit massLimit
    scoreReplicationError biasCorrectionError scoreUnitComponent
    biasUnitComponent
    (unitComponentAbsSumEnvelope scoreUnitComponent)
    (unitComponentAbsSumEnvelope biasUnitComponent)
    hunit_card hdraw_card hsampleSize_ne hbase_den_ne hbase_ratio
    hcover_all hcontributionCell_all hweightCell_all hcontributionLimit
    hweightLimit hmass hscore_construct_univ
    (Filter.Eventually.of_forall
      (fun index unit component _hcomponent =>
        unitComponentAbsSumEnvelope_bound scoreUnitComponent index unit
          component))
    (fun component hcomponent =>
      tendsto_unitComponentAbsSumEnvelope_zero (l := l)
        scoreUnitComponent component
        (fun unit => hscore_unit_tendsto unit component hcomponent))
    hbias_construct_univ
    (Filter.Eventually.of_forall
      (fun index unit component _hcomponent =>
        unitComponentAbsSumEnvelope_bound biasUnitComponent index unit
          component))
    (fun component hcomponent =>
      tendsto_unitComponentAbsSumEnvelope_zero (l := l)
        biasUnitComponent component
        (fun unit => hbias_unit_tendsto unit component hcomponent))

/--
Finite `L1(P)` bracketing version of the concrete full-support route with
finite absolute-sum unit envelopes constructed from pointwise unit-component
convergence.
-/
theorem tendsto_concreteUniformAssignmentBootstrapVariance_of_eventually_cell_contribution_weight_limits_l1BracketingNumber_obligations_and_hajek_base_ratio_univ_support_unit_component_tendsto_bounds
    [Fintype Unit] [Fintype Draw] [DecidableEq Unit] [DecidableEq Draw]
    [Nonempty Unit] [DecidableEq Cell] [DecidableEq ScoreComponent]
    [DecidableEq BiasComponent]
    {Bracket : Type*} [Fintype Bracket]
    (cells : Finset Cell)
    (scoreComponents : Finset ScoreComponent)
    (biasComponents : Finset BiasComponent)
    (assignment : ℕ -> Draw -> Unit)
    (score : ℕ -> Unit -> Cell)
    (contribution weight : ℕ -> Unit -> Real)
    (target denominator normalizer sampleSize : Real)
    (cellContribution cellWeight : ℕ -> Cell -> Real)
    (contributionLimit weightLimit massLimit : Cell -> Real)
    (scoreReplicationError biasCorrectionError : ℕ -> Real)
    (scoreUnitComponent : ℕ -> Unit -> ScoreComponent -> Real)
    (biasUnitComponent : ℕ -> Unit -> BiasComponent -> Real)
    (hunit_card : (Fintype.card Unit : Real) = sampleSize)
    (hdraw_card : (Fintype.card Draw : Real) = sampleSize)
    (hsampleSize_ne : sampleSize ≠ 0)
    (hbase_den_ne :
      ∀ᶠ index in atTop,
        baseLinearizedSum (Finset.univ : Finset Unit)
          (weight index) ≠ 0)
    (hbase_ratio :
      ∀ᶠ index in atTop,
        baseLinearizedSum (Finset.univ : Finset Unit)
            (contribution index) /
          baseLinearizedSum (Finset.univ : Finset Unit)
            (weight index) =
          target)
    (hcover_all :
      ∀ᶠ index in atTop,
        ∀ unit, score index unit ∈ cells)
    (hcontributionCell_all :
      ∀ᶠ index in atTop,
        ∀ unit,
          cellContribution index (score index unit) =
            contribution index unit)
    (hweightCell_all :
      ∀ᶠ index in atTop,
        ∀ unit,
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
          weightedSampleSum ((fun _index : ℕ =>
              (Finset.univ : Finset Unit)) sampleSize)
            ((fun _index _unit => 1) sampleSize)
            (scoreCellIndicator (score sampleSize) cell)))
    (hscore_construct_univ :
      scoreReplicationError =ᶠ[atTop]
        (fun index =>
          ∑ component ∈ scoreComponents, ∑ unit : Unit,
            (multinomialCountFromDrawIndicators (Finset.univ : Finset Draw)
                (fun assignment draw unit =>
                  oneHotAssignmentIndicator assignment draw unit)
                (assignment index) unit - 1) *
              scoreUnitComponent index unit component))
    (hscore_unit_tendsto :
      ∀ unit,
        ∀ component, component ∈ scoreComponents ->
          Tendsto (fun index => scoreUnitComponent index unit component)
            atTop (nhds 0))
    (hbias_construct_univ :
      biasCorrectionError =ᶠ[atTop]
        (fun index =>
          ∑ component ∈ biasComponents, ∑ unit : Unit,
            (multinomialCountFromDrawIndicators (Finset.univ : Finset Draw)
                (fun assignment draw unit =>
                  oneHotAssignmentIndicator assignment draw unit)
                (assignment index) unit - 1) *
              biasUnitComponent index unit component))
    (hbias_unit_tendsto :
      ∀ unit,
        ∀ component, component ∈ biasComponents ->
          Tendsto (fun index => biasUnitComponent index unit component)
            atTop (nhds 0)) :
    Tendsto
      (fun index =>
        (1 / denominator ^ 2) * (1 / normalizer) *
            multiplierPerturbationSecondMoment
              (uniformAssignmentSupport Unit Draw)
              (uniformAssignmentMass Unit Draw)
              (Finset.univ : Finset Unit)
              (fun assignment unit =>
                multinomialCountFromDrawIndicators
                  (Finset.univ : Finset Draw)
                  (fun assignment draw unit =>
                    oneHotAssignmentIndicator assignment draw unit)
                  assignment unit)
              (fun unit =>
                contribution index unit - target * weight index unit) +
          scoreReplicationError index + biasCorrectionError index)
      atTop
      (nhds
        ((1 / denominator ^ 2) * (1 / normalizer) *
          weightedScoreCellMomentLimit cells
            (fun cell =>
              (contributionLimit cell - target * weightLimit cell) ^ 2)
            massLimit)) :=
  tendsto_concreteUniformAssignmentBootstrapVariance_of_eventually_cell_contribution_weight_limits_and_hajek_base_ratio_univ_support_unit_component_tendsto_bounds
    (l := atTop) cells scoreComponents biasComponents assignment score
    contribution weight target denominator normalizer sampleSize
    cellContribution cellWeight contributionLimit weightLimit massLimit
    scoreReplicationError biasCorrectionError scoreUnitComponent
    biasUnitComponent hunit_card hdraw_card hsampleSize_ne
    hbase_den_ne hbase_ratio hcover_all hcontributionCell_all
    hweightCell_all hcontributionLimit hweightLimit
    (cellwise_mass_lln_of_glivenkoCantelli_bridge
      cells massLimit (fun _index : ℕ => (Finset.univ : Finset Unit))
      (fun _index _unit => 1) score
      (weighted_indicator_array_lln_of_l1BracketingNumber_obligations
        cells massLimit
        (fun _index : ℕ => (Finset.univ : Finset Unit))
        (fun _index _unit => 1) score obligations))
    hscore_construct_univ hscore_unit_tendsto hbias_construct_univ
    hbias_unit_tendsto

/--
VdV&W endpoint-assembly version of the concrete full-support route with
finite absolute-sum unit envelopes constructed from pointwise unit-component
convergence.
-/
theorem tendsto_concreteUniformAssignmentBootstrapVariance_of_eventually_cell_contribution_weight_limits_vdvw241_endpoint_assembly_and_hajek_base_ratio_univ_support_unit_component_tendsto_bounds
    [Fintype Unit] [Fintype Draw] [DecidableEq Unit] [DecidableEq Draw]
    [Nonempty Unit] [DecidableEq Cell] [DecidableEq ScoreComponent]
    [DecidableEq BiasComponent]
    {Bracket : Type*} [Fintype Bracket]
    (cells : Finset Cell)
    (scoreComponents : Finset ScoreComponent)
    (biasComponents : Finset BiasComponent)
    (assignment : ℕ -> Draw -> Unit)
    (score : ℕ -> Unit -> Cell)
    (contribution weight : ℕ -> Unit -> Real)
    (target denominator normalizer sampleSize : Real)
    (cellContribution cellWeight : ℕ -> Cell -> Real)
    (contributionLimit weightLimit massLimit : Cell -> Real)
    (scoreReplicationError biasCorrectionError : ℕ -> Real)
    (scoreUnitComponent : ℕ -> Unit -> ScoreComponent -> Real)
    (biasUnitComponent : ℕ -> Unit -> BiasComponent -> Real)
    (hunit_card : (Fintype.card Unit : Real) = sampleSize)
    (hdraw_card : (Fintype.card Draw : Real) = sampleSize)
    (hsampleSize_ne : sampleSize ≠ 0)
    (hbase_den_ne :
      ∀ᶠ index in atTop,
        baseLinearizedSum (Finset.univ : Finset Unit)
          (weight index) ≠ 0)
    (hbase_ratio :
      ∀ᶠ index in atTop,
        baseLinearizedSum (Finset.univ : Finset Unit)
            (contribution index) /
          baseLinearizedSum (Finset.univ : Finset Unit)
            (weight index) =
          target)
    (hcover_all :
      ∀ᶠ index in atTop,
        ∀ unit, score index unit ∈ cells)
    (hcontributionCell_all :
      ∀ᶠ index in atTop,
        ∀ unit,
          cellContribution index (score index unit) =
            contribution index unit)
    (hweightCell_all :
      ∀ᶠ index in atTop,
        ∀ unit,
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
          weightedSampleSum ((fun _index : ℕ =>
              (Finset.univ : Finset Unit)) sampleSize)
            ((fun _index _unit => 1) sampleSize)
            (scoreCellIndicator (score sampleSize) cell)))
    (hscore_construct_univ :
      scoreReplicationError =ᶠ[atTop]
        (fun index =>
          ∑ component ∈ scoreComponents, ∑ unit : Unit,
            (multinomialCountFromDrawIndicators (Finset.univ : Finset Draw)
                (fun assignment draw unit =>
                  oneHotAssignmentIndicator assignment draw unit)
                (assignment index) unit - 1) *
              scoreUnitComponent index unit component))
    (hscore_unit_tendsto :
      ∀ unit,
        ∀ component, component ∈ scoreComponents ->
          Tendsto (fun index => scoreUnitComponent index unit component)
            atTop (nhds 0))
    (hbias_construct_univ :
      biasCorrectionError =ᶠ[atTop]
        (fun index =>
          ∑ component ∈ biasComponents, ∑ unit : Unit,
            (multinomialCountFromDrawIndicators (Finset.univ : Finset Draw)
                (fun assignment draw unit =>
                  oneHotAssignmentIndicator assignment draw unit)
                (assignment index) unit - 1) *
              biasUnitComponent index unit component))
    (hbias_unit_tendsto :
      ∀ unit,
        ∀ component, component ∈ biasComponents ->
          Tendsto (fun index => biasUnitComponent index unit component)
            atTop (nhds 0)) :
    Tendsto
      (fun index =>
        (1 / denominator ^ 2) * (1 / normalizer) *
            multiplierPerturbationSecondMoment
              (uniformAssignmentSupport Unit Draw)
              (uniformAssignmentMass Unit Draw)
              (Finset.univ : Finset Unit)
              (fun assignment unit =>
                multinomialCountFromDrawIndicators
                  (Finset.univ : Finset Draw)
                  (fun assignment draw unit =>
                    oneHotAssignmentIndicator assignment draw unit)
                  assignment unit)
              (fun unit =>
                contribution index unit - target * weight index unit) +
          scoreReplicationError index + biasCorrectionError index)
      atTop
      (nhds
        ((1 / denominator ^ 2) * (1 / normalizer) *
          weightedScoreCellMomentLimit cells
            (fun cell =>
              (contributionLimit cell - target * weightLimit cell) ^ 2)
            massLimit)) :=
  tendsto_concreteUniformAssignmentBootstrapVariance_of_eventually_cell_contribution_weight_limits_and_hajek_base_ratio_univ_support_unit_component_tendsto_bounds
    (l := atTop) cells scoreComponents biasComponents assignment score
    contribution weight target denominator normalizer sampleSize
    cellContribution cellWeight contributionLimit weightLimit massLimit
    scoreReplicationError biasCorrectionError scoreUnitComponent
    biasUnitComponent hunit_card hdraw_card hsampleSize_ne
    hbase_den_ne hbase_ratio hcover_all hcontributionCell_all
    hweightCell_all hcontributionLimit hweightLimit
    (cellwise_mass_lln_of_glivenkoCantelli_bridge
      cells massLimit (fun _index : ℕ => (Finset.univ : Finset Unit))
      (fun _index _unit => 1) score
      (weighted_indicator_array_lln_of_vdvw241_endpoint_assembly
        cells massLimit
        (fun _index : ℕ => (Finset.univ : Finset Unit))
        (fun _index _unit => 1) score assembly))
    hscore_construct_univ hscore_unit_tendsto hbias_construct_univ
    hbias_unit_tendsto

/--
Concrete one-hot multinomial component sum used by the WDSM bootstrap
score-replication and bias-correction constructions.
-/
noncomputable def concreteOneHotUnitComponentError
    [Fintype Unit] [Fintype Draw] [DecidableEq Unit]
    {Component : Type*}
    [DecidableEq Component]
    (components : Finset Component)
    (assignment : Index -> Draw -> Unit)
    (unitComponent : Index -> Unit -> Component -> Real)
    (index : Index) : Real :=
  ∑ component ∈ components, ∑ unit : Unit,
    (multinomialCountFromDrawIndicators (Finset.univ : Finset Draw)
        (fun assignment draw unit =>
          oneHotAssignmentIndicator assignment draw unit)
        (assignment index) unit - 1) *
      unitComponent index unit component

/--
A finite sum of multiplier perturbations under the concrete one-hot
multinomial counts is the literal one-hot unit-component error.
-/
theorem sum_multiplierPerturbation_oneHot_counts_eq_concreteOneHotUnitComponentError
    [Fintype Unit] [Fintype Draw] [DecidableEq Unit]
    {Component : Type*} [DecidableEq Component]
    (components : Finset Component)
    (assignment : Index -> Draw -> Unit)
    (unitComponent : Index -> Unit -> Component -> Real)
    (index : Index) :
    (∑ component ∈ components,
        multiplierPerturbation (Finset.univ : Finset Unit)
          (fun unit =>
            multinomialCountFromDrawIndicators (Finset.univ : Finset Draw)
              (fun assignment draw unit =>
                oneHotAssignmentIndicator assignment draw unit)
              (assignment index) unit)
          (fun unit => unitComponent index unit component)) =
      concreteOneHotUnitComponentError components assignment unitComponent
        index := by
  simp [multiplierPerturbation, concreteOneHotUnitComponentError]

/--
The literal full-support one-hot unit-component error is exactly the finite
score-cell decomposition induced by the concrete multinomial draw-count
replicate.
-/
theorem sum_multinomialDrawScoreCellErrorComponent_eq_concreteOneHotUnitComponentError
    [Fintype Unit] [Fintype Draw] [DecidableEq Unit]
    [DecidableEq Cell]
    {Component : Type*} [DecidableEq Component]
    (cells : Finset Cell) (components : Finset Component)
    (assignment : Index -> Draw -> Unit)
    (score : Index -> Unit -> Cell)
    (unitComponent : Index -> Unit -> Component -> Real)
    (index : Index)
    (hcover_all : ∀ unit, score index unit ∈ cells) :
    (∑ cell ∈ cells, ∑ component ∈ components,
        multinomialDrawScoreCellErrorComponent
          (Finset.univ : Finset Unit) (Finset.univ : Finset Draw)
          (fun assignment draw unit =>
            oneHotAssignmentIndicator assignment draw unit)
          (assignment index) (score index) (unitComponent index)
          cell component) =
      concreteOneHotUnitComponentError components assignment unitComponent
        index := by
  have hdecomp :=
    sum_multinomialDrawScoreCellErrorComponent_eq_centered_count_unit_sum
      cells components (Finset.univ : Finset Unit)
      (Finset.univ : Finset Draw)
      (fun assignment draw unit =>
        oneHotAssignmentIndicator assignment draw unit)
      (assignment index) (score index) (unitComponent index)
      (fun unit _hunit => hcover_all unit)
  simpa [concreteOneHotUnitComponentError] using hdecomp

/--
Eventual version of the concrete full-support one-hot score-cell
decomposition.  This discharges the finite score-cell decomposition premise
when the error term is the literal one-hot unit-component sum.
-/
theorem eventually_sum_multinomialDrawScoreCellErrorComponent_eq_concreteOneHotUnitComponentError
    [Fintype Unit] [Fintype Draw] [DecidableEq Unit]
    [DecidableEq Cell]
    {Component : Type*} [DecidableEq Component]
    (cells : Finset Cell) (components : Finset Component)
    (assignment : Index -> Draw -> Unit)
    (score : Index -> Unit -> Cell)
    (unitComponent : Index -> Unit -> Component -> Real)
    (hcover_all :
      ∀ᶠ index in l,
        ∀ unit, score index unit ∈ cells) :
    (fun index =>
      ∑ cell ∈ cells, ∑ component ∈ components,
        multinomialDrawScoreCellErrorComponent
          (Finset.univ : Finset Unit) (Finset.univ : Finset Draw)
          (fun assignment draw unit =>
            oneHotAssignmentIndicator assignment draw unit)
          (assignment index) (score index) (unitComponent index)
          cell component) =ᶠ[l]
      fun index =>
        concreteOneHotUnitComponentError components assignment
          unitComponent index := by
  filter_upwards [hcover_all] with index hcover_index
  exact
    sum_multinomialDrawScoreCellErrorComponent_eq_concreteOneHotUnitComponentError
      cells components assignment score unitComponent index hcover_index

/--
Pointwise convergence of every concrete centered-count product implies
negligibility of the literal one-hot unit-component error.
-/
theorem tendsto_concreteOneHotUnitComponentError_zero_of_product_tendsto
    [Fintype Unit] [Fintype Draw] [DecidableEq Unit]
    {Component : Type*} [DecidableEq Component]
    (components : Finset Component)
    (assignment : Index -> Draw -> Unit)
    (unitComponent : Index -> Unit -> Component -> Real)
    (hproduct :
      ∀ unit,
        ∀ component, component ∈ components ->
          Tendsto
            (fun index =>
              (multinomialCountFromDrawIndicators
                  (Finset.univ : Finset Draw)
                  (fun assignment draw unit =>
                    oneHotAssignmentIndicator assignment draw unit)
                  (assignment index) unit - 1) *
                unitComponent index unit component)
            l (nhds 0)) :
    Tendsto
      (fun index =>
        concreteOneHotUnitComponentError components assignment
          unitComponent index)
      l (nhds 0) := by
  have hsum :
      Tendsto
        (fun index =>
          ∑ component ∈ components, ∑ unit : Unit,
            (multinomialCountFromDrawIndicators
                (Finset.univ : Finset Draw)
                (fun assignment draw unit =>
                  oneHotAssignmentIndicator assignment draw unit)
                (assignment index) unit - 1) *
              unitComponent index unit component)
        l (nhds 0) :=
    tendsto_sum_cell_values_zero (l := l) components
      (fun index component =>
        ∑ unit : Unit,
          (multinomialCountFromDrawIndicators
              (Finset.univ : Finset Draw)
              (fun assignment draw unit =>
                oneHotAssignmentIndicator assignment draw unit)
              (assignment index) unit - 1) *
            unitComponent index unit component)
      (fun component hcomponent =>
        tendsto_sum_cell_values_zero (l := l)
          (Finset.univ : Finset Unit)
          (fun index unit =>
            (multinomialCountFromDrawIndicators
                (Finset.univ : Finset Draw)
                (fun assignment draw unit =>
                  oneHotAssignmentIndicator assignment draw unit)
                (assignment index) unit - 1) *
              unitComponent index unit component)
          (fun unit _hunit => hproduct unit component hcomponent))
  simpa [concreteOneHotUnitComponentError] using hsum

/--
Score-replication negligibility from an eventual equality to the literal
one-hot component error and pointwise convergence of its centered-count
products.
-/
theorem bootstrapScoreReplicationErrorNegligible_of_concreteOneHotUnitComponentError_product_tendsto
    [Fintype Unit] [Fintype Draw] [DecidableEq Unit]
    {Component : Type*} [DecidableEq Component]
    (components : Finset Component)
    (assignment : Index -> Draw -> Unit)
    (unitComponent : Index -> Unit -> Component -> Real)
    (scoreReplicationError : Index -> Real)
    (hconstruct :
      scoreReplicationError =ᶠ[l]
        fun index =>
          concreteOneHotUnitComponentError components assignment
            unitComponent index)
    (hproduct :
      ∀ unit,
        ∀ component, component ∈ components ->
          Tendsto
            (fun index =>
              (multinomialCountFromDrawIndicators
                  (Finset.univ : Finset Draw)
                  (fun assignment draw unit =>
                    oneHotAssignmentIndicator assignment draw unit)
                  (assignment index) unit - 1) *
                unitComponent index unit component)
            l (nhds 0)) :
    bootstrapScoreReplicationErrorNegligible
      (l := l) scoreReplicationError :=
  (tendsto_concreteOneHotUnitComponentError_zero_of_product_tendsto
    (l := l) components assignment unitComponent hproduct).congr'
      hconstruct.symm

/--
Bias-correction negligibility from an eventual equality to the literal
one-hot component error and pointwise convergence of its centered-count
products.
-/
theorem bootstrapBiasCorrectionErrorNegligible_of_concreteOneHotUnitComponentError_product_tendsto
    [Fintype Unit] [Fintype Draw] [DecidableEq Unit]
    {Component : Type*} [DecidableEq Component]
    (components : Finset Component)
    (assignment : Index -> Draw -> Unit)
    (unitComponent : Index -> Unit -> Component -> Real)
    (biasCorrectionError : Index -> Real)
    (hconstruct :
      biasCorrectionError =ᶠ[l]
        fun index =>
          concreteOneHotUnitComponentError components assignment
            unitComponent index)
    (hproduct :
      ∀ unit,
        ∀ component, component ∈ components ->
          Tendsto
            (fun index =>
              (multinomialCountFromDrawIndicators
                  (Finset.univ : Finset Draw)
                  (fun assignment draw unit =>
                    oneHotAssignmentIndicator assignment draw unit)
                  (assignment index) unit - 1) *
                unitComponent index unit component)
            l (nhds 0)) :
    bootstrapBiasCorrectionErrorNegligible
      (l := l) biasCorrectionError :=
  (tendsto_concreteOneHotUnitComponentError_zero_of_product_tendsto
    (l := l) components assignment unitComponent hproduct).congr'
      hconstruct.symm

/--
For the fixed full-support one-hot bootstrap law, a centered count times a
unit component tends to zero whenever the unit component itself tends to zero.
The deterministic input is the finite draw-count bound `#Draw + 1`.
-/
theorem tendsto_centered_oneHot_count_mul_unitComponent_zero_of_unitComponent_tendsto
    [Fintype Draw] [DecidableEq Unit]
    (assignment : Index -> Draw -> Unit)
    (unitComponent : Index -> Unit -> Component -> Real)
    (unit : Unit) (component : Component)
    (hunit :
      Tendsto (fun index => unitComponent index unit component)
        l (nhds 0)) :
    Tendsto
      (fun index =>
        (multinomialCountFromDrawIndicators
            (Finset.univ : Finset Draw)
            (fun assignment draw unit =>
              oneHotAssignmentIndicator assignment draw unit)
            (assignment index) unit - 1) *
          unitComponent index unit component)
      l (nhds 0) := by
  let countBound : Real := ((Finset.univ : Finset Draw).card : Real) + 1
  have hcount_bound :
      ∀ index,
        |multinomialCountFromDrawIndicators
            (Finset.univ : Finset Draw)
            (fun assignment draw unit =>
              oneHotAssignmentIndicator assignment draw unit)
            (assignment index) unit - 1| ≤ countBound := by
    intro index
    exact
      abs_multinomialCountFromDrawIndicators_sub_one_le_draw_card_add_one
        (Finset.univ : Finset Draw)
        (fun assignment draw unit =>
          oneHotAssignmentIndicator assignment draw unit)
        (assignment index) unit
        (fun draw _hdraw =>
          abs_oneHotAssignmentIndicator_le_one (assignment index) draw unit)
  have hbound :
      ∀ index,
        |(multinomialCountFromDrawIndicators
            (Finset.univ : Finset Draw)
            (fun assignment draw unit =>
              oneHotAssignmentIndicator assignment draw unit)
            (assignment index) unit - 1) *
          unitComponent index unit component| ≤
          countBound * |unitComponent index unit component| := by
    intro index
    calc
      |(multinomialCountFromDrawIndicators
          (Finset.univ : Finset Draw)
          (fun assignment draw unit =>
            oneHotAssignmentIndicator assignment draw unit)
          (assignment index) unit - 1) *
        unitComponent index unit component| =
          |multinomialCountFromDrawIndicators
              (Finset.univ : Finset Draw)
              (fun assignment draw unit =>
                oneHotAssignmentIndicator assignment draw unit)
              (assignment index) unit - 1| *
            |unitComponent index unit component| := by
            rw [abs_mul]
      _ ≤ countBound * |unitComponent index unit component| := by
            exact
              mul_le_mul_of_nonneg_right (hcount_bound index)
                (abs_nonneg _)
  exact
    tendsto_zero_of_abs_le_bound
      (fun index =>
        (multinomialCountFromDrawIndicators
            (Finset.univ : Finset Draw)
            (fun assignment draw unit =>
              oneHotAssignmentIndicator assignment draw unit)
            (assignment index) unit - 1) *
          unitComponent index unit component)
      (fun index => countBound * |unitComponent index unit component|)
      hbound
      (by
        simpa [countBound] using
          tendsto_const_nhds.mul hunit.abs)

/--
The literal one-hot unit-component error is negligible under pointwise
convergence of every fixed unit component.  The centered-count product
premises are discharged by the finite draw-count bound.
-/
theorem tendsto_concreteOneHotUnitComponentError_zero_of_unitComponent_tendsto
    [Fintype Unit] [Fintype Draw] [DecidableEq Unit]
    {Component : Type*} [DecidableEq Component]
    (components : Finset Component)
    (assignment : Index -> Draw -> Unit)
    (unitComponent : Index -> Unit -> Component -> Real)
    (hunit :
      ∀ unit,
        ∀ component, component ∈ components ->
          Tendsto (fun index => unitComponent index unit component)
            l (nhds 0)) :
    Tendsto
      (fun index =>
        concreteOneHotUnitComponentError components assignment
          unitComponent index)
      l (nhds 0) :=
  tendsto_concreteOneHotUnitComponentError_zero_of_product_tendsto
    (l := l) components assignment unitComponent
    (fun unit component hcomponent =>
      tendsto_centered_oneHot_count_mul_unitComponent_zero_of_unitComponent_tendsto
        (l := l) assignment unitComponent unit component
        (hunit unit component hcomponent))

/--
Score-replication negligibility for the literal one-hot component error from
pointwise convergence of every fixed unit component.
-/
theorem bootstrapScoreReplicationErrorNegligible_of_concreteOneHotUnitComponentError_unitComponent_tendsto
    [Fintype Unit] [Fintype Draw] [DecidableEq Unit]
    {Component : Type*} [DecidableEq Component]
    (components : Finset Component)
    (assignment : Index -> Draw -> Unit)
    (unitComponent : Index -> Unit -> Component -> Real)
    (scoreReplicationError : Index -> Real)
    (hconstruct :
      scoreReplicationError =ᶠ[l]
        fun index =>
          concreteOneHotUnitComponentError components assignment
            unitComponent index)
    (hunit :
      ∀ unit,
        ∀ component, component ∈ components ->
          Tendsto (fun index => unitComponent index unit component)
            l (nhds 0)) :
    bootstrapScoreReplicationErrorNegligible
      (l := l) scoreReplicationError :=
  (tendsto_concreteOneHotUnitComponentError_zero_of_unitComponent_tendsto
    (l := l) components assignment unitComponent hunit).congr'
      hconstruct.symm

/--
Bias-correction negligibility for the literal one-hot component error from
pointwise convergence of every fixed unit component.
-/
theorem bootstrapBiasCorrectionErrorNegligible_of_concreteOneHotUnitComponentError_unitComponent_tendsto
    [Fintype Unit] [Fintype Draw] [DecidableEq Unit]
    {Component : Type*} [DecidableEq Component]
    (components : Finset Component)
    (assignment : Index -> Draw -> Unit)
    (unitComponent : Index -> Unit -> Component -> Real)
    (biasCorrectionError : Index -> Real)
    (hconstruct :
      biasCorrectionError =ᶠ[l]
        fun index =>
          concreteOneHotUnitComponentError components assignment
            unitComponent index)
    (hunit :
      ∀ unit,
        ∀ component, component ∈ components ->
          Tendsto (fun index => unitComponent index unit component)
            l (nhds 0)) :
    bootstrapBiasCorrectionErrorNegligible
      (l := l) biasCorrectionError :=
  (tendsto_concreteOneHotUnitComponentError_zero_of_unitComponent_tendsto
    (l := l) components assignment unitComponent hunit).congr'
      hconstruct.symm

/--
Concrete full-support uniform variance convergence from pointwise convergence
of every literal centered-count product.  This endpoint bypasses separate
unit-envelope fields for the score and bias errors.
-/
theorem tendsto_concreteUniformAssignmentBootstrapVariance_of_eventually_cell_contribution_weight_limits_and_hajek_base_ratio_univ_support_centered_count_product_tendsto
    [Fintype Unit] [Fintype Draw] [DecidableEq Unit] [DecidableEq Draw]
    [Nonempty Unit] [DecidableEq Cell] [DecidableEq ScoreComponent]
    [DecidableEq BiasComponent]
    (cells : Finset Cell)
    (scoreComponents : Finset ScoreComponent)
    (biasComponents : Finset BiasComponent)
    (assignment : Index -> Draw -> Unit)
    (score : Index -> Unit -> Cell)
    (contribution weight : Index -> Unit -> Real)
    (target denominator normalizer sampleSize : Real)
    (cellContribution cellWeight : Index -> Cell -> Real)
    (contributionLimit weightLimit massLimit : Cell -> Real)
    (hunit_card : (Fintype.card Unit : Real) = sampleSize)
    (hdraw_card : (Fintype.card Draw : Real) = sampleSize)
    (hsampleSize_ne : sampleSize ≠ 0)
    (hbase_den_ne :
      ∀ᶠ index in l,
        baseLinearizedSum (Finset.univ : Finset Unit)
          (weight index) ≠ 0)
    (hbase_ratio :
      ∀ᶠ index in l,
        baseLinearizedSum (Finset.univ : Finset Unit)
            (contribution index) /
          baseLinearizedSum (Finset.univ : Finset Unit)
            (weight index) =
          target)
    (hcover_all :
      ∀ᶠ index in l,
        ∀ unit, score index unit ∈ cells)
    (hcontributionCell_all :
      ∀ᶠ index in l,
        ∀ unit,
          cellContribution index (score index unit) =
            contribution index unit)
    (hweightCell_all :
      ∀ᶠ index in l,
        ∀ unit,
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
      cellwiseScoreCellMassLLN (l := l) cells
        (fun _index => (Finset.univ : Finset Unit))
        (fun _index _unit => 1) score massLimit)
    (scoreUnitComponent : Index -> Unit -> ScoreComponent -> Real)
    (biasUnitComponent : Index -> Unit -> BiasComponent -> Real)
    (hscore_product_tendsto :
      ∀ unit,
        ∀ component, component ∈ scoreComponents ->
          Tendsto
            (fun index =>
              (multinomialCountFromDrawIndicators
                  (Finset.univ : Finset Draw)
                  (fun assignment draw unit =>
                    oneHotAssignmentIndicator assignment draw unit)
                  (assignment index) unit - 1) *
                scoreUnitComponent index unit component)
            l (nhds 0))
    (hbias_product_tendsto :
      ∀ unit,
        ∀ component, component ∈ biasComponents ->
          Tendsto
            (fun index =>
              (multinomialCountFromDrawIndicators
                  (Finset.univ : Finset Draw)
                  (fun assignment draw unit =>
                    oneHotAssignmentIndicator assignment draw unit)
                  (assignment index) unit - 1) *
                biasUnitComponent index unit component)
            l (nhds 0)) :
    Tendsto
      (fun index =>
        (1 / denominator ^ 2) * (1 / normalizer) *
            multiplierPerturbationSecondMoment
              (uniformAssignmentSupport Unit Draw)
              (uniformAssignmentMass Unit Draw)
              (Finset.univ : Finset Unit)
              (fun assignment unit =>
                multinomialCountFromDrawIndicators
                  (Finset.univ : Finset Draw)
                  (fun assignment draw unit =>
                    oneHotAssignmentIndicator assignment draw unit)
                  assignment unit)
              (fun unit =>
                contribution index unit - target * weight index unit) +
          concreteOneHotUnitComponentError scoreComponents assignment
            scoreUnitComponent index +
          concreteOneHotUnitComponentError biasComponents assignment
            biasUnitComponent index)
      l
      (nhds
        ((1 / denominator ^ 2) * (1 / normalizer) *
          weightedScoreCellMomentLimit cells
            (fun cell =>
              (contributionLimit cell - target * weightLimit cell) ^ 2)
            massLimit)) := by
  let linearizedVariance : Index -> Real :=
    fun index =>
      (1 / denominator ^ 2) * (1 / normalizer) *
        multiplierPerturbationSecondMoment
          (uniformAssignmentSupport Unit Draw)
          (uniformAssignmentMass Unit Draw)
          (Finset.univ : Finset Unit)
          (fun assignment unit =>
            multinomialCountFromDrawIndicators
              (Finset.univ : Finset Draw)
              (fun assignment draw unit =>
                oneHotAssignmentIndicator assignment draw unit)
              assignment unit)
          (fun unit =>
            contribution index unit - target * weight index unit)
  let scoreError : Index -> Real :=
    fun index =>
      concreteOneHotUnitComponentError scoreComponents assignment
        scoreUnitComponent index
  let biasError : Index -> Real :=
    fun index =>
      concreteOneHotUnitComponentError biasComponents assignment
        biasUnitComponent index
  have hcover :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ (Finset.univ : Finset Unit) ->
          score index unit ∈ cells := by
    filter_upwards [hcover_all] with index hcover_index unit _hunit
    exact hcover_index unit
  have hcontributionCell :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ (Finset.univ : Finset Unit) ->
          cellContribution index (score index unit) =
            contribution index unit := by
    filter_upwards [hcontributionCell_all] with index hcell_index unit _hunit
    exact hcell_index unit
  have hweightCell :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ (Finset.univ : Finset Unit) ->
          cellWeight index (score index unit) = weight index unit := by
    filter_upwards [hweightCell_all] with index hcell_index unit _hunit
    exact hcell_index unit
  have hcentered :
      Tendsto
        (fun index =>
          bootstrapCenteredVarianceTarget
            (Finset.univ : Finset Unit)
            (contribution index) (weight index) target denominator
            normalizer)
        l
        (nhds
          ((1 / denominator ^ 2) * (1 / normalizer) *
            weightedScoreCellMomentLimit cells
              (fun cell =>
                (contributionLimit cell - target * weightLimit cell) ^ 2)
              massLimit)) :=
    tendsto_bootstrapCenteredVarianceTarget_of_eventually_cell_contribution_weight_limits
      (l := l) cells (fun _index => (Finset.univ : Finset Unit)) score
      contribution weight target denominator normalizer cellContribution
      cellWeight contributionLimit weightLimit massLimit hcover
      hcontributionCell hweightCell hcontributionLimit hweightLimit hmass
  have hbase :
      ∀ᶠ index in l,
        baseLinearizedSum (Finset.univ : Finset Unit)
            (contribution index) =
          target *
            baseLinearizedSum (Finset.univ : Finset Unit)
              (weight index) := by
    filter_upwards [hbase_den_ne, hbase_ratio] with index hden hratio
    exact
      baseLinearizedSum_eq_target_mul_of_hajek_ratio_eq
        (Finset.univ : Finset Unit) (contribution index)
        (weight index) target hden hratio
  have hlinearized_eq :
      linearizedVariance =ᶠ[l]
        (fun index =>
          bootstrapCenteredVarianceTarget
            (Finset.univ : Finset Unit)
            (contribution index) (weight index) target denominator
            normalizer) := by
    filter_upwards [hbase] with index hbase_index
    exact
      multiplierPerturbationSecondMoment_normalized_eq_bootstrapCenteredVarianceTarget_of_uniformAssignment_base_ratio
        (Unit := Unit) (Draw := Draw)
        (contribution index) (weight index) target denominator normalizer
        sampleSize hunit_card hdraw_card hsampleSize_ne hbase_index
  have hlinearized :
      Tendsto linearizedVariance l
        (nhds
          ((1 / denominator ^ 2) * (1 / normalizer) *
            weightedScoreCellMomentLimit cells
              (fun cell =>
                (contributionLimit cell - target * weightLimit cell) ^ 2)
              massLimit)) :=
    hcentered.congr' hlinearized_eq.symm
  have hscore :
      bootstrapScoreReplicationErrorNegligible (l := l) scoreError :=
    tendsto_concreteOneHotUnitComponentError_zero_of_product_tendsto
      (l := l) scoreComponents assignment scoreUnitComponent
      hscore_product_tendsto
  have hbias :
      bootstrapBiasCorrectionErrorNegligible (l := l) biasError :=
    tendsto_concreteOneHotUnitComponentError_zero_of_product_tendsto
      (l := l) biasComponents assignment biasUnitComponent
      hbias_product_tendsto
  have hcombined :
      Tendsto
        (fun index => linearizedVariance index +
          (scoreError index + biasError index))
        l
        (nhds
          ((1 / denominator ^ 2) * (1 / normalizer) *
            weightedScoreCellMomentLimit cells
              (fun cell =>
                (contributionLimit cell - target * weightLimit cell) ^ 2)
              massLimit)) :=
    by simpa using hlinearized.add (hscore.add hbias)
  convert hcombined using 1
  ext index
  simp [linearizedVariance, scoreError, biasError, add_assoc]

/--
Finite `L1(P)` bracketing companion for the concrete full-support
centered-count product endpoint.
-/
theorem tendsto_concreteUniformAssignmentBootstrapVariance_of_eventually_cell_contribution_weight_limits_l1BracketingNumber_obligations_and_hajek_base_ratio_univ_support_centered_count_product_tendsto
    [Fintype Unit] [Fintype Draw] [DecidableEq Unit] [DecidableEq Draw]
    [Nonempty Unit] [DecidableEq Cell] [DecidableEq ScoreComponent]
    [DecidableEq BiasComponent]
    {Bracket : Type*} [Fintype Bracket]
    (cells : Finset Cell)
    (scoreComponents : Finset ScoreComponent)
    (biasComponents : Finset BiasComponent)
    (assignment : ℕ -> Draw -> Unit)
    (score : ℕ -> Unit -> Cell)
    (contribution weight : ℕ -> Unit -> Real)
    (target denominator normalizer sampleSize : Real)
    (cellContribution cellWeight : ℕ -> Cell -> Real)
    (contributionLimit weightLimit massLimit : Cell -> Real)
    (hunit_card : (Fintype.card Unit : Real) = sampleSize)
    (hdraw_card : (Fintype.card Draw : Real) = sampleSize)
    (hsampleSize_ne : sampleSize ≠ 0)
    (hbase_den_ne :
      ∀ᶠ index in atTop,
        baseLinearizedSum (Finset.univ : Finset Unit)
          (weight index) ≠ 0)
    (hbase_ratio :
      ∀ᶠ index in atTop,
        baseLinearizedSum (Finset.univ : Finset Unit)
            (contribution index) /
          baseLinearizedSum (Finset.univ : Finset Unit)
            (weight index) =
          target)
    (hcover_all :
      ∀ᶠ index in atTop,
        ∀ unit, score index unit ∈ cells)
    (hcontributionCell_all :
      ∀ᶠ index in atTop,
        ∀ unit,
          cellContribution index (score index unit) =
            contribution index unit)
    (hweightCell_all :
      ∀ᶠ index in atTop,
        ∀ unit,
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
          weightedSampleSum ((fun _index : ℕ =>
              (Finset.univ : Finset Unit)) sampleSize)
            ((fun _index _unit => 1) sampleSize)
            (scoreCellIndicator (score sampleSize) cell)))
    (scoreUnitComponent : ℕ -> Unit -> ScoreComponent -> Real)
    (biasUnitComponent : ℕ -> Unit -> BiasComponent -> Real)
    (hscore_product_tendsto :
      ∀ unit,
        ∀ component, component ∈ scoreComponents ->
          Tendsto
            (fun index =>
              (multinomialCountFromDrawIndicators
                  (Finset.univ : Finset Draw)
                  (fun assignment draw unit =>
                    oneHotAssignmentIndicator assignment draw unit)
                  (assignment index) unit - 1) *
                scoreUnitComponent index unit component)
            atTop (nhds 0))
    (hbias_product_tendsto :
      ∀ unit,
        ∀ component, component ∈ biasComponents ->
          Tendsto
            (fun index =>
              (multinomialCountFromDrawIndicators
                  (Finset.univ : Finset Draw)
                  (fun assignment draw unit =>
                    oneHotAssignmentIndicator assignment draw unit)
                  (assignment index) unit - 1) *
                biasUnitComponent index unit component)
            atTop (nhds 0)) :
    Tendsto
      (fun index =>
        (1 / denominator ^ 2) * (1 / normalizer) *
            multiplierPerturbationSecondMoment
              (uniformAssignmentSupport Unit Draw)
              (uniformAssignmentMass Unit Draw)
              (Finset.univ : Finset Unit)
              (fun assignment unit =>
                multinomialCountFromDrawIndicators
                  (Finset.univ : Finset Draw)
                  (fun assignment draw unit =>
                    oneHotAssignmentIndicator assignment draw unit)
                  assignment unit)
              (fun unit =>
                contribution index unit - target * weight index unit) +
          concreteOneHotUnitComponentError scoreComponents assignment
            scoreUnitComponent index +
          concreteOneHotUnitComponentError biasComponents assignment
            biasUnitComponent index)
      atTop
      (nhds
        ((1 / denominator ^ 2) * (1 / normalizer) *
          weightedScoreCellMomentLimit cells
            (fun cell =>
              (contributionLimit cell - target * weightLimit cell) ^ 2)
            massLimit)) :=
  tendsto_concreteUniformAssignmentBootstrapVariance_of_eventually_cell_contribution_weight_limits_and_hajek_base_ratio_univ_support_centered_count_product_tendsto
    (l := atTop) cells scoreComponents biasComponents assignment score
    contribution weight target denominator normalizer sampleSize
    cellContribution cellWeight contributionLimit weightLimit massLimit
    hunit_card hdraw_card hsampleSize_ne hbase_den_ne hbase_ratio
    hcover_all hcontributionCell_all hweightCell_all hcontributionLimit
    hweightLimit
    (cellwise_mass_lln_of_glivenkoCantelli_bridge
      cells massLimit (fun _index : ℕ => (Finset.univ : Finset Unit))
      (fun _index _unit => 1) score
      (weighted_indicator_array_lln_of_l1BracketingNumber_obligations
        cells massLimit
        (fun _index : ℕ => (Finset.univ : Finset Unit))
        (fun _index _unit => 1) score obligations))
    scoreUnitComponent biasUnitComponent hscore_product_tendsto
    hbias_product_tendsto

/--
VdV&W endpoint-assembly companion for the concrete full-support
centered-count product endpoint.
-/
theorem tendsto_concreteUniformAssignmentBootstrapVariance_of_eventually_cell_contribution_weight_limits_vdvw241_endpoint_assembly_and_hajek_base_ratio_univ_support_centered_count_product_tendsto
    [Fintype Unit] [Fintype Draw] [DecidableEq Unit] [DecidableEq Draw]
    [Nonempty Unit] [DecidableEq Cell] [DecidableEq ScoreComponent]
    [DecidableEq BiasComponent]
    {Bracket : Type*} [Fintype Bracket]
    (cells : Finset Cell)
    (scoreComponents : Finset ScoreComponent)
    (biasComponents : Finset BiasComponent)
    (assignment : ℕ -> Draw -> Unit)
    (score : ℕ -> Unit -> Cell)
    (contribution weight : ℕ -> Unit -> Real)
    (target denominator normalizer sampleSize : Real)
    (cellContribution cellWeight : ℕ -> Cell -> Real)
    (contributionLimit weightLimit massLimit : Cell -> Real)
    (hunit_card : (Fintype.card Unit : Real) = sampleSize)
    (hdraw_card : (Fintype.card Draw : Real) = sampleSize)
    (hsampleSize_ne : sampleSize ≠ 0)
    (hbase_den_ne :
      ∀ᶠ index in atTop,
        baseLinearizedSum (Finset.univ : Finset Unit)
          (weight index) ≠ 0)
    (hbase_ratio :
      ∀ᶠ index in atTop,
        baseLinearizedSum (Finset.univ : Finset Unit)
            (contribution index) /
          baseLinearizedSum (Finset.univ : Finset Unit)
            (weight index) =
          target)
    (hcover_all :
      ∀ᶠ index in atTop,
        ∀ unit, score index unit ∈ cells)
    (hcontributionCell_all :
      ∀ᶠ index in atTop,
        ∀ unit,
          cellContribution index (score index unit) =
            contribution index unit)
    (hweightCell_all :
      ∀ᶠ index in atTop,
        ∀ unit,
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
          weightedSampleSum ((fun _index : ℕ =>
              (Finset.univ : Finset Unit)) sampleSize)
            ((fun _index _unit => 1) sampleSize)
            (scoreCellIndicator (score sampleSize) cell)))
    (scoreUnitComponent : ℕ -> Unit -> ScoreComponent -> Real)
    (biasUnitComponent : ℕ -> Unit -> BiasComponent -> Real)
    (hscore_product_tendsto :
      ∀ unit,
        ∀ component, component ∈ scoreComponents ->
          Tendsto
            (fun index =>
              (multinomialCountFromDrawIndicators
                  (Finset.univ : Finset Draw)
                  (fun assignment draw unit =>
                    oneHotAssignmentIndicator assignment draw unit)
                  (assignment index) unit - 1) *
                scoreUnitComponent index unit component)
            atTop (nhds 0))
    (hbias_product_tendsto :
      ∀ unit,
        ∀ component, component ∈ biasComponents ->
          Tendsto
            (fun index =>
              (multinomialCountFromDrawIndicators
                  (Finset.univ : Finset Draw)
                  (fun assignment draw unit =>
                    oneHotAssignmentIndicator assignment draw unit)
                  (assignment index) unit - 1) *
                biasUnitComponent index unit component)
            atTop (nhds 0)) :
    Tendsto
      (fun index =>
        (1 / denominator ^ 2) * (1 / normalizer) *
            multiplierPerturbationSecondMoment
              (uniformAssignmentSupport Unit Draw)
              (uniformAssignmentMass Unit Draw)
              (Finset.univ : Finset Unit)
              (fun assignment unit =>
                multinomialCountFromDrawIndicators
                  (Finset.univ : Finset Draw)
                  (fun assignment draw unit =>
                    oneHotAssignmentIndicator assignment draw unit)
                  assignment unit)
              (fun unit =>
                contribution index unit - target * weight index unit) +
          concreteOneHotUnitComponentError scoreComponents assignment
            scoreUnitComponent index +
          concreteOneHotUnitComponentError biasComponents assignment
            biasUnitComponent index)
      atTop
      (nhds
        ((1 / denominator ^ 2) * (1 / normalizer) *
          weightedScoreCellMomentLimit cells
            (fun cell =>
              (contributionLimit cell - target * weightLimit cell) ^ 2)
            massLimit)) :=
  tendsto_concreteUniformAssignmentBootstrapVariance_of_eventually_cell_contribution_weight_limits_and_hajek_base_ratio_univ_support_centered_count_product_tendsto
    (l := atTop) cells scoreComponents biasComponents assignment score
    contribution weight target denominator normalizer sampleSize
    cellContribution cellWeight contributionLimit weightLimit massLimit
    hunit_card hdraw_card hsampleSize_ne hbase_den_ne hbase_ratio
    hcover_all hcontributionCell_all hweightCell_all hcontributionLimit
    hweightLimit
    (cellwise_mass_lln_of_glivenkoCantelli_bridge
      cells massLimit (fun _index : ℕ => (Finset.univ : Finset Unit))
      (fun _index _unit => 1) score
      (weighted_indicator_array_lln_of_vdvw241_endpoint_assembly
        cells massLimit
        (fun _index : ℕ => (Finset.univ : Finset Unit))
      (fun _index _unit => 1) score assembly))
    scoreUnitComponent biasUnitComponent hscore_product_tendsto
    hbias_product_tendsto

/--
Concrete full-support centered-count product endpoint with the manuscript
Hájek denominator and target-ratio premises.  The base-denominator nonzero
condition and base-ratio equality are derived internally.
-/
theorem tendsto_concreteUniformAssignmentBootstrapVariance_of_eventually_cell_contribution_weight_limits_and_hajek_target_denominator_univ_support_centered_count_product_tendsto
    [Fintype Unit] [Fintype Draw] [DecidableEq Unit] [DecidableEq Draw]
    [Nonempty Unit] [DecidableEq Cell] [DecidableEq ScoreComponent]
    [DecidableEq BiasComponent]
    (cells : Finset Cell)
    (scoreComponents : Finset ScoreComponent)
    (biasComponents : Finset BiasComponent)
    (assignment : Index -> Draw -> Unit)
    (score : Index -> Unit -> Cell)
    (contribution weight : Index -> Unit -> Real)
    (target denominator normalizer sampleSize : Real)
    (cellContribution cellWeight : Index -> Cell -> Real)
    (contributionLimit weightLimit massLimit : Cell -> Real)
    (hunit_card : (Fintype.card Unit : Real) = sampleSize)
    (hdraw_card : (Fintype.card Draw : Real) = sampleSize)
    (hsampleSize_ne : sampleSize ≠ 0)
    (hbase_denominator :
      ∀ᶠ index in l,
        baseLinearizedSum (Finset.univ : Finset Unit)
          (weight index) = denominator)
    (hdenominator_ne : denominator ≠ 0)
    (htarget_hajek :
      ∀ᶠ index in l,
        target =
          baseLinearizedSum (Finset.univ : Finset Unit)
            (contribution index) / denominator)
    (hcover_all :
      ∀ᶠ index in l,
        ∀ unit, score index unit ∈ cells)
    (hcontributionCell_all :
      ∀ᶠ index in l,
        ∀ unit,
          cellContribution index (score index unit) =
            contribution index unit)
    (hweightCell_all :
      ∀ᶠ index in l,
        ∀ unit,
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
      cellwiseScoreCellMassLLN (l := l) cells
        (fun _index => (Finset.univ : Finset Unit))
        (fun _index _unit => 1) score massLimit)
    (scoreUnitComponent : Index -> Unit -> ScoreComponent -> Real)
    (biasUnitComponent : Index -> Unit -> BiasComponent -> Real)
    (hscore_product_tendsto :
      ∀ unit,
        ∀ component, component ∈ scoreComponents ->
          Tendsto
            (fun index =>
              (multinomialCountFromDrawIndicators
                  (Finset.univ : Finset Draw)
                  (fun assignment draw unit =>
                    oneHotAssignmentIndicator assignment draw unit)
                  (assignment index) unit - 1) *
                scoreUnitComponent index unit component)
            l (nhds 0))
    (hbias_product_tendsto :
      ∀ unit,
        ∀ component, component ∈ biasComponents ->
          Tendsto
            (fun index =>
              (multinomialCountFromDrawIndicators
                  (Finset.univ : Finset Draw)
                  (fun assignment draw unit =>
                    oneHotAssignmentIndicator assignment draw unit)
                  (assignment index) unit - 1) *
                biasUnitComponent index unit component)
            l (nhds 0)) :
    Tendsto
      (fun index =>
        (1 / denominator ^ 2) * (1 / normalizer) *
            multiplierPerturbationSecondMoment
              (uniformAssignmentSupport Unit Draw)
              (uniformAssignmentMass Unit Draw)
              (Finset.univ : Finset Unit)
              (fun assignment unit =>
                multinomialCountFromDrawIndicators
                  (Finset.univ : Finset Draw)
                  (fun assignment draw unit =>
                    oneHotAssignmentIndicator assignment draw unit)
                  assignment unit)
              (fun unit =>
                contribution index unit - target * weight index unit) +
          concreteOneHotUnitComponentError scoreComponents assignment
            scoreUnitComponent index +
          concreteOneHotUnitComponentError biasComponents assignment
            biasUnitComponent index)
      l
      (nhds
        ((1 / denominator ^ 2) * (1 / normalizer) *
          weightedScoreCellMomentLimit cells
            (fun cell =>
              (contributionLimit cell - target * weightLimit cell) ^ 2)
            massLimit)) := by
  have hbase_den_ne :
      ∀ᶠ index in l,
        baseLinearizedSum (Finset.univ : Finset Unit)
          (weight index) ≠ 0 := by
    filter_upwards [hbase_denominator] with index hden_eq
    rw [hden_eq]
    exact hdenominator_ne
  have hbase_ratio :
      ∀ᶠ index in l,
        baseLinearizedSum (Finset.univ : Finset Unit)
            (contribution index) /
          baseLinearizedSum (Finset.univ : Finset Unit)
            (weight index) =
          target := by
    filter_upwards [hbase_denominator, htarget_hajek] with
      index hden_eq htarget
    rw [hden_eq]
    exact htarget.symm
  exact
    tendsto_concreteUniformAssignmentBootstrapVariance_of_eventually_cell_contribution_weight_limits_and_hajek_base_ratio_univ_support_centered_count_product_tendsto
      (l := l) cells scoreComponents biasComponents assignment score
      contribution weight target denominator normalizer sampleSize
      cellContribution cellWeight contributionLimit weightLimit massLimit
      hunit_card hdraw_card hsampleSize_ne hbase_den_ne hbase_ratio
      hcover_all hcontributionCell_all hweightCell_all hcontributionLimit
      hweightLimit hmass scoreUnitComponent biasUnitComponent
      hscore_product_tendsto hbias_product_tendsto

/--
Finite `L1(P)` bracketing companion for the manuscript Hájek denominator and
target-ratio product endpoint.
-/
theorem tendsto_concreteUniformAssignmentBootstrapVariance_of_eventually_cell_contribution_weight_limits_l1BracketingNumber_obligations_and_hajek_target_denominator_univ_support_centered_count_product_tendsto
    [Fintype Unit] [Fintype Draw] [DecidableEq Unit] [DecidableEq Draw]
    [Nonempty Unit] [DecidableEq Cell] [DecidableEq ScoreComponent]
    [DecidableEq BiasComponent]
    {Bracket : Type*} [Fintype Bracket]
    (cells : Finset Cell)
    (scoreComponents : Finset ScoreComponent)
    (biasComponents : Finset BiasComponent)
    (assignment : ℕ -> Draw -> Unit)
    (score : ℕ -> Unit -> Cell)
    (contribution weight : ℕ -> Unit -> Real)
    (target denominator normalizer sampleSize : Real)
    (cellContribution cellWeight : ℕ -> Cell -> Real)
    (contributionLimit weightLimit massLimit : Cell -> Real)
    (hunit_card : (Fintype.card Unit : Real) = sampleSize)
    (hdraw_card : (Fintype.card Draw : Real) = sampleSize)
    (hsampleSize_ne : sampleSize ≠ 0)
    (hbase_denominator :
      ∀ᶠ index in atTop,
        baseLinearizedSum (Finset.univ : Finset Unit)
          (weight index) = denominator)
    (hdenominator_ne : denominator ≠ 0)
    (htarget_hajek :
      ∀ᶠ index in atTop,
        target =
          baseLinearizedSum (Finset.univ : Finset Unit)
            (contribution index) / denominator)
    (hcover_all :
      ∀ᶠ index in atTop,
        ∀ unit, score index unit ∈ cells)
    (hcontributionCell_all :
      ∀ᶠ index in atTop,
        ∀ unit,
          cellContribution index (score index unit) =
            contribution index unit)
    (hweightCell_all :
      ∀ᶠ index in atTop,
        ∀ unit,
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
          weightedSampleSum ((fun _index : ℕ =>
              (Finset.univ : Finset Unit)) sampleSize)
            ((fun _index _unit => 1) sampleSize)
            (scoreCellIndicator (score sampleSize) cell)))
    (scoreUnitComponent : ℕ -> Unit -> ScoreComponent -> Real)
    (biasUnitComponent : ℕ -> Unit -> BiasComponent -> Real)
    (hscore_product_tendsto :
      ∀ unit,
        ∀ component, component ∈ scoreComponents ->
          Tendsto
            (fun index =>
              (multinomialCountFromDrawIndicators
                  (Finset.univ : Finset Draw)
                  (fun assignment draw unit =>
                    oneHotAssignmentIndicator assignment draw unit)
                  (assignment index) unit - 1) *
                scoreUnitComponent index unit component)
            atTop (nhds 0))
    (hbias_product_tendsto :
      ∀ unit,
        ∀ component, component ∈ biasComponents ->
          Tendsto
            (fun index =>
              (multinomialCountFromDrawIndicators
                  (Finset.univ : Finset Draw)
                  (fun assignment draw unit =>
                    oneHotAssignmentIndicator assignment draw unit)
                  (assignment index) unit - 1) *
                biasUnitComponent index unit component)
            atTop (nhds 0)) :
    Tendsto
      (fun index =>
        (1 / denominator ^ 2) * (1 / normalizer) *
            multiplierPerturbationSecondMoment
              (uniformAssignmentSupport Unit Draw)
              (uniformAssignmentMass Unit Draw)
              (Finset.univ : Finset Unit)
              (fun assignment unit =>
                multinomialCountFromDrawIndicators
                  (Finset.univ : Finset Draw)
                  (fun assignment draw unit =>
                    oneHotAssignmentIndicator assignment draw unit)
                  assignment unit)
              (fun unit =>
                contribution index unit - target * weight index unit) +
          concreteOneHotUnitComponentError scoreComponents assignment
            scoreUnitComponent index +
          concreteOneHotUnitComponentError biasComponents assignment
            biasUnitComponent index)
      atTop
      (nhds
        ((1 / denominator ^ 2) * (1 / normalizer) *
          weightedScoreCellMomentLimit cells
            (fun cell =>
              (contributionLimit cell - target * weightLimit cell) ^ 2)
            massLimit)) :=
  tendsto_concreteUniformAssignmentBootstrapVariance_of_eventually_cell_contribution_weight_limits_and_hajek_target_denominator_univ_support_centered_count_product_tendsto
    (l := atTop) cells scoreComponents biasComponents assignment score
    contribution weight target denominator normalizer sampleSize
    cellContribution cellWeight contributionLimit weightLimit massLimit
    hunit_card hdraw_card hsampleSize_ne hbase_denominator
    hdenominator_ne htarget_hajek hcover_all hcontributionCell_all
    hweightCell_all hcontributionLimit hweightLimit
    (cellwise_mass_lln_of_glivenkoCantelli_bridge
      cells massLimit (fun _index : ℕ => (Finset.univ : Finset Unit))
      (fun _index _unit => 1) score
      (weighted_indicator_array_lln_of_l1BracketingNumber_obligations
        cells massLimit
        (fun _index : ℕ => (Finset.univ : Finset Unit))
        (fun _index _unit => 1) score obligations))
    scoreUnitComponent biasUnitComponent hscore_product_tendsto
    hbias_product_tendsto

/--
VdV&W endpoint-assembly companion for the manuscript Hájek denominator and
target-ratio product endpoint.
-/
theorem tendsto_concreteUniformAssignmentBootstrapVariance_of_eventually_cell_contribution_weight_limits_vdvw241_endpoint_assembly_and_hajek_target_denominator_univ_support_centered_count_product_tendsto
    [Fintype Unit] [Fintype Draw] [DecidableEq Unit] [DecidableEq Draw]
    [Nonempty Unit] [DecidableEq Cell] [DecidableEq ScoreComponent]
    [DecidableEq BiasComponent]
    {Bracket : Type*} [Fintype Bracket]
    (cells : Finset Cell)
    (scoreComponents : Finset ScoreComponent)
    (biasComponents : Finset BiasComponent)
    (assignment : ℕ -> Draw -> Unit)
    (score : ℕ -> Unit -> Cell)
    (contribution weight : ℕ -> Unit -> Real)
    (target denominator normalizer sampleSize : Real)
    (cellContribution cellWeight : ℕ -> Cell -> Real)
    (contributionLimit weightLimit massLimit : Cell -> Real)
    (hunit_card : (Fintype.card Unit : Real) = sampleSize)
    (hdraw_card : (Fintype.card Draw : Real) = sampleSize)
    (hsampleSize_ne : sampleSize ≠ 0)
    (hbase_denominator :
      ∀ᶠ index in atTop,
        baseLinearizedSum (Finset.univ : Finset Unit)
          (weight index) = denominator)
    (hdenominator_ne : denominator ≠ 0)
    (htarget_hajek :
      ∀ᶠ index in atTop,
        target =
          baseLinearizedSum (Finset.univ : Finset Unit)
            (contribution index) / denominator)
    (hcover_all :
      ∀ᶠ index in atTop,
        ∀ unit, score index unit ∈ cells)
    (hcontributionCell_all :
      ∀ᶠ index in atTop,
        ∀ unit,
          cellContribution index (score index unit) =
            contribution index unit)
    (hweightCell_all :
      ∀ᶠ index in atTop,
        ∀ unit,
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
          weightedSampleSum ((fun _index : ℕ =>
              (Finset.univ : Finset Unit)) sampleSize)
            ((fun _index _unit => 1) sampleSize)
            (scoreCellIndicator (score sampleSize) cell)))
    (scoreUnitComponent : ℕ -> Unit -> ScoreComponent -> Real)
    (biasUnitComponent : ℕ -> Unit -> BiasComponent -> Real)
    (hscore_product_tendsto :
      ∀ unit,
        ∀ component, component ∈ scoreComponents ->
          Tendsto
            (fun index =>
              (multinomialCountFromDrawIndicators
                  (Finset.univ : Finset Draw)
                  (fun assignment draw unit =>
                    oneHotAssignmentIndicator assignment draw unit)
                  (assignment index) unit - 1) *
                scoreUnitComponent index unit component)
            atTop (nhds 0))
    (hbias_product_tendsto :
      ∀ unit,
        ∀ component, component ∈ biasComponents ->
          Tendsto
            (fun index =>
              (multinomialCountFromDrawIndicators
                  (Finset.univ : Finset Draw)
                  (fun assignment draw unit =>
                    oneHotAssignmentIndicator assignment draw unit)
                  (assignment index) unit - 1) *
                biasUnitComponent index unit component)
            atTop (nhds 0)) :
    Tendsto
      (fun index =>
        (1 / denominator ^ 2) * (1 / normalizer) *
            multiplierPerturbationSecondMoment
              (uniformAssignmentSupport Unit Draw)
              (uniformAssignmentMass Unit Draw)
              (Finset.univ : Finset Unit)
              (fun assignment unit =>
                multinomialCountFromDrawIndicators
                  (Finset.univ : Finset Draw)
                  (fun assignment draw unit =>
                    oneHotAssignmentIndicator assignment draw unit)
                  assignment unit)
              (fun unit =>
                contribution index unit - target * weight index unit) +
          concreteOneHotUnitComponentError scoreComponents assignment
            scoreUnitComponent index +
          concreteOneHotUnitComponentError biasComponents assignment
            biasUnitComponent index)
      atTop
      (nhds
        ((1 / denominator ^ 2) * (1 / normalizer) *
          weightedScoreCellMomentLimit cells
            (fun cell =>
              (contributionLimit cell - target * weightLimit cell) ^ 2)
            massLimit)) :=
  tendsto_concreteUniformAssignmentBootstrapVariance_of_eventually_cell_contribution_weight_limits_and_hajek_target_denominator_univ_support_centered_count_product_tendsto
    (l := atTop) cells scoreComponents biasComponents assignment score
    contribution weight target denominator normalizer sampleSize
    cellContribution cellWeight contributionLimit weightLimit massLimit
    hunit_card hdraw_card hsampleSize_ne hbase_denominator
    hdenominator_ne htarget_hajek hcover_all hcontributionCell_all
    hweightCell_all hcontributionLimit hweightLimit
    (cellwise_mass_lln_of_glivenkoCantelli_bridge
      cells massLimit (fun _index : ℕ => (Finset.univ : Finset Unit))
      (fun _index _unit => 1) score
      (weighted_indicator_array_lln_of_vdvw241_endpoint_assembly
        cells massLimit
        (fun _index : ℕ => (Finset.univ : Finset Unit))
        (fun _index _unit => 1) score assembly))
    scoreUnitComponent biasUnitComponent hscore_product_tendsto
    hbias_product_tendsto

/--
Manuscript Hájek denominator version of the concrete full-support endpoint
where centered-count product convergence is derived from pointwise
unit-component convergence.
-/
theorem tendsto_concreteUniformAssignmentBootstrapVariance_of_eventually_cell_contribution_weight_limits_and_hajek_target_denominator_univ_support_unit_component_tendsto
    [Fintype Unit] [Fintype Draw] [DecidableEq Unit] [DecidableEq Draw]
    [Nonempty Unit] [DecidableEq Cell] [DecidableEq ScoreComponent]
    [DecidableEq BiasComponent]
    (cells : Finset Cell)
    (scoreComponents : Finset ScoreComponent)
    (biasComponents : Finset BiasComponent)
    (assignment : Index -> Draw -> Unit)
    (score : Index -> Unit -> Cell)
    (contribution weight : Index -> Unit -> Real)
    (target denominator normalizer sampleSize : Real)
    (cellContribution cellWeight : Index -> Cell -> Real)
    (contributionLimit weightLimit massLimit : Cell -> Real)
    (hunit_card : (Fintype.card Unit : Real) = sampleSize)
    (hdraw_card : (Fintype.card Draw : Real) = sampleSize)
    (hsampleSize_ne : sampleSize ≠ 0)
    (hbase_denominator :
      ∀ᶠ index in l,
        baseLinearizedSum (Finset.univ : Finset Unit)
          (weight index) = denominator)
    (hdenominator_ne : denominator ≠ 0)
    (htarget_hajek :
      ∀ᶠ index in l,
        target =
          baseLinearizedSum (Finset.univ : Finset Unit)
            (contribution index) / denominator)
    (hcover_all :
      ∀ᶠ index in l,
        ∀ unit, score index unit ∈ cells)
    (hcontributionCell_all :
      ∀ᶠ index in l,
        ∀ unit,
          cellContribution index (score index unit) =
            contribution index unit)
    (hweightCell_all :
      ∀ᶠ index in l,
        ∀ unit,
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
      cellwiseScoreCellMassLLN (l := l) cells
        (fun _index => (Finset.univ : Finset Unit))
        (fun _index _unit => 1) score massLimit)
    (scoreUnitComponent : Index -> Unit -> ScoreComponent -> Real)
    (biasUnitComponent : Index -> Unit -> BiasComponent -> Real)
    (hscore_unit_tendsto :
      ∀ unit,
        ∀ component, component ∈ scoreComponents ->
          Tendsto (fun index => scoreUnitComponent index unit component)
            l (nhds 0))
    (hbias_unit_tendsto :
      ∀ unit,
        ∀ component, component ∈ biasComponents ->
          Tendsto (fun index => biasUnitComponent index unit component)
            l (nhds 0)) :
    Tendsto
      (fun index =>
        (1 / denominator ^ 2) * (1 / normalizer) *
            multiplierPerturbationSecondMoment
              (uniformAssignmentSupport Unit Draw)
              (uniformAssignmentMass Unit Draw)
              (Finset.univ : Finset Unit)
              (fun assignment unit =>
                multinomialCountFromDrawIndicators
                  (Finset.univ : Finset Draw)
                  (fun assignment draw unit =>
                    oneHotAssignmentIndicator assignment draw unit)
                  assignment unit)
              (fun unit =>
                contribution index unit - target * weight index unit) +
          concreteOneHotUnitComponentError scoreComponents assignment
            scoreUnitComponent index +
          concreteOneHotUnitComponentError biasComponents assignment
            biasUnitComponent index)
      l
      (nhds
        ((1 / denominator ^ 2) * (1 / normalizer) *
          weightedScoreCellMomentLimit cells
            (fun cell =>
              (contributionLimit cell - target * weightLimit cell) ^ 2)
            massLimit)) :=
  tendsto_concreteUniformAssignmentBootstrapVariance_of_eventually_cell_contribution_weight_limits_and_hajek_target_denominator_univ_support_centered_count_product_tendsto
    (l := l) cells scoreComponents biasComponents assignment score
    contribution weight target denominator normalizer sampleSize
    cellContribution cellWeight contributionLimit weightLimit massLimit
    hunit_card hdraw_card hsampleSize_ne hbase_denominator
    hdenominator_ne htarget_hajek hcover_all hcontributionCell_all
    hweightCell_all hcontributionLimit hweightLimit hmass
    scoreUnitComponent biasUnitComponent
    (fun unit component hcomponent =>
      tendsto_centered_oneHot_count_mul_unitComponent_zero_of_unitComponent_tendsto
        (l := l) assignment scoreUnitComponent unit component
        (hscore_unit_tendsto unit component hcomponent))
    (fun unit component hcomponent =>
      tendsto_centered_oneHot_count_mul_unitComponent_zero_of_unitComponent_tendsto
        (l := l) assignment biasUnitComponent unit component
        (hbias_unit_tendsto unit component hcomponent))

/--
Finite `L1(P)` bracketing companion for the manuscript Hájek denominator
endpoint with pointwise unit-component convergence.
-/
theorem tendsto_concreteUniformAssignmentBootstrapVariance_of_eventually_cell_contribution_weight_limits_l1BracketingNumber_obligations_and_hajek_target_denominator_univ_support_unit_component_tendsto
    [Fintype Unit] [Fintype Draw] [DecidableEq Unit] [DecidableEq Draw]
    [Nonempty Unit] [DecidableEq Cell] [DecidableEq ScoreComponent]
    [DecidableEq BiasComponent]
    {Bracket : Type*} [Fintype Bracket]
    (cells : Finset Cell)
    (scoreComponents : Finset ScoreComponent)
    (biasComponents : Finset BiasComponent)
    (assignment : ℕ -> Draw -> Unit)
    (score : ℕ -> Unit -> Cell)
    (contribution weight : ℕ -> Unit -> Real)
    (target denominator normalizer sampleSize : Real)
    (cellContribution cellWeight : ℕ -> Cell -> Real)
    (contributionLimit weightLimit massLimit : Cell -> Real)
    (hunit_card : (Fintype.card Unit : Real) = sampleSize)
    (hdraw_card : (Fintype.card Draw : Real) = sampleSize)
    (hsampleSize_ne : sampleSize ≠ 0)
    (hbase_denominator :
      ∀ᶠ index in atTop,
        baseLinearizedSum (Finset.univ : Finset Unit)
          (weight index) = denominator)
    (hdenominator_ne : denominator ≠ 0)
    (htarget_hajek :
      ∀ᶠ index in atTop,
        target =
          baseLinearizedSum (Finset.univ : Finset Unit)
            (contribution index) / denominator)
    (hcover_all :
      ∀ᶠ index in atTop,
        ∀ unit, score index unit ∈ cells)
    (hcontributionCell_all :
      ∀ᶠ index in atTop,
        ∀ unit,
          cellContribution index (score index unit) =
            contribution index unit)
    (hweightCell_all :
      ∀ᶠ index in atTop,
        ∀ unit,
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
          weightedSampleSum ((fun _index : ℕ =>
              (Finset.univ : Finset Unit)) sampleSize)
            ((fun _index _unit => 1) sampleSize)
            (scoreCellIndicator (score sampleSize) cell)))
    (scoreUnitComponent : ℕ -> Unit -> ScoreComponent -> Real)
    (biasUnitComponent : ℕ -> Unit -> BiasComponent -> Real)
    (hscore_unit_tendsto :
      ∀ unit,
        ∀ component, component ∈ scoreComponents ->
          Tendsto (fun index => scoreUnitComponent index unit component)
            atTop (nhds 0))
    (hbias_unit_tendsto :
      ∀ unit,
        ∀ component, component ∈ biasComponents ->
          Tendsto (fun index => biasUnitComponent index unit component)
            atTop (nhds 0)) :
    Tendsto
      (fun index =>
        (1 / denominator ^ 2) * (1 / normalizer) *
            multiplierPerturbationSecondMoment
              (uniformAssignmentSupport Unit Draw)
              (uniformAssignmentMass Unit Draw)
              (Finset.univ : Finset Unit)
              (fun assignment unit =>
                multinomialCountFromDrawIndicators
                  (Finset.univ : Finset Draw)
                  (fun assignment draw unit =>
                    oneHotAssignmentIndicator assignment draw unit)
                  assignment unit)
              (fun unit =>
                contribution index unit - target * weight index unit) +
          concreteOneHotUnitComponentError scoreComponents assignment
            scoreUnitComponent index +
          concreteOneHotUnitComponentError biasComponents assignment
            biasUnitComponent index)
      atTop
      (nhds
        ((1 / denominator ^ 2) * (1 / normalizer) *
          weightedScoreCellMomentLimit cells
            (fun cell =>
              (contributionLimit cell - target * weightLimit cell) ^ 2)
            massLimit)) :=
  tendsto_concreteUniformAssignmentBootstrapVariance_of_eventually_cell_contribution_weight_limits_and_hajek_target_denominator_univ_support_unit_component_tendsto
    (l := atTop) cells scoreComponents biasComponents assignment score
    contribution weight target denominator normalizer sampleSize
    cellContribution cellWeight contributionLimit weightLimit massLimit
    hunit_card hdraw_card hsampleSize_ne hbase_denominator
    hdenominator_ne htarget_hajek hcover_all hcontributionCell_all
    hweightCell_all hcontributionLimit hweightLimit
    (cellwise_mass_lln_of_glivenkoCantelli_bridge
      cells massLimit (fun _index : ℕ => (Finset.univ : Finset Unit))
      (fun _index _unit => 1) score
      (weighted_indicator_array_lln_of_l1BracketingNumber_obligations
        cells massLimit
        (fun _index : ℕ => (Finset.univ : Finset Unit))
        (fun _index _unit => 1) score obligations))
    scoreUnitComponent biasUnitComponent hscore_unit_tendsto
    hbias_unit_tendsto

/--
VdV&W endpoint-assembly companion for the manuscript Hájek denominator
endpoint with pointwise unit-component convergence.
-/
theorem tendsto_concreteUniformAssignmentBootstrapVariance_of_eventually_cell_contribution_weight_limits_vdvw241_endpoint_assembly_and_hajek_target_denominator_univ_support_unit_component_tendsto
    [Fintype Unit] [Fintype Draw] [DecidableEq Unit] [DecidableEq Draw]
    [Nonempty Unit] [DecidableEq Cell] [DecidableEq ScoreComponent]
    [DecidableEq BiasComponent]
    {Bracket : Type*} [Fintype Bracket]
    (cells : Finset Cell)
    (scoreComponents : Finset ScoreComponent)
    (biasComponents : Finset BiasComponent)
    (assignment : ℕ -> Draw -> Unit)
    (score : ℕ -> Unit -> Cell)
    (contribution weight : ℕ -> Unit -> Real)
    (target denominator normalizer sampleSize : Real)
    (cellContribution cellWeight : ℕ -> Cell -> Real)
    (contributionLimit weightLimit massLimit : Cell -> Real)
    (hunit_card : (Fintype.card Unit : Real) = sampleSize)
    (hdraw_card : (Fintype.card Draw : Real) = sampleSize)
    (hsampleSize_ne : sampleSize ≠ 0)
    (hbase_denominator :
      ∀ᶠ index in atTop,
        baseLinearizedSum (Finset.univ : Finset Unit)
          (weight index) = denominator)
    (hdenominator_ne : denominator ≠ 0)
    (htarget_hajek :
      ∀ᶠ index in atTop,
        target =
          baseLinearizedSum (Finset.univ : Finset Unit)
            (contribution index) / denominator)
    (hcover_all :
      ∀ᶠ index in atTop,
        ∀ unit, score index unit ∈ cells)
    (hcontributionCell_all :
      ∀ᶠ index in atTop,
        ∀ unit,
          cellContribution index (score index unit) =
            contribution index unit)
    (hweightCell_all :
      ∀ᶠ index in atTop,
        ∀ unit,
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
          weightedSampleSum ((fun _index : ℕ =>
              (Finset.univ : Finset Unit)) sampleSize)
            ((fun _index _unit => 1) sampleSize)
            (scoreCellIndicator (score sampleSize) cell)))
    (scoreUnitComponent : ℕ -> Unit -> ScoreComponent -> Real)
    (biasUnitComponent : ℕ -> Unit -> BiasComponent -> Real)
    (hscore_unit_tendsto :
      ∀ unit,
        ∀ component, component ∈ scoreComponents ->
          Tendsto (fun index => scoreUnitComponent index unit component)
            atTop (nhds 0))
    (hbias_unit_tendsto :
      ∀ unit,
        ∀ component, component ∈ biasComponents ->
          Tendsto (fun index => biasUnitComponent index unit component)
            atTop (nhds 0)) :
    Tendsto
      (fun index =>
        (1 / denominator ^ 2) * (1 / normalizer) *
            multiplierPerturbationSecondMoment
              (uniformAssignmentSupport Unit Draw)
              (uniformAssignmentMass Unit Draw)
              (Finset.univ : Finset Unit)
              (fun assignment unit =>
                multinomialCountFromDrawIndicators
                  (Finset.univ : Finset Draw)
                  (fun assignment draw unit =>
                    oneHotAssignmentIndicator assignment draw unit)
                  assignment unit)
              (fun unit =>
                contribution index unit - target * weight index unit) +
          concreteOneHotUnitComponentError scoreComponents assignment
            scoreUnitComponent index +
          concreteOneHotUnitComponentError biasComponents assignment
            biasUnitComponent index)
      atTop
      (nhds
        ((1 / denominator ^ 2) * (1 / normalizer) *
          weightedScoreCellMomentLimit cells
            (fun cell =>
              (contributionLimit cell - target * weightLimit cell) ^ 2)
            massLimit)) :=
  tendsto_concreteUniformAssignmentBootstrapVariance_of_eventually_cell_contribution_weight_limits_and_hajek_target_denominator_univ_support_unit_component_tendsto
    (l := atTop) cells scoreComponents biasComponents assignment score
    contribution weight target denominator normalizer sampleSize
    cellContribution cellWeight contributionLimit weightLimit massLimit
    hunit_card hdraw_card hsampleSize_ne hbase_denominator
    hdenominator_ne htarget_hajek hcover_all hcontributionCell_all
    hweightCell_all hcontributionLimit hweightLimit
    (cellwise_mass_lln_of_glivenkoCantelli_bridge
      cells massLimit (fun _index : ℕ => (Finset.univ : Finset Unit))
      (fun _index _unit => 1) score
      (weighted_indicator_array_lln_of_vdvw241_endpoint_assembly
        cells massLimit
        (fun _index : ℕ => (Finset.univ : Finset Unit))
        (fun _index _unit => 1) score assembly))
    scoreUnitComponent biasUnitComponent hscore_unit_tendsto
    hbias_unit_tendsto

/--
Manuscript Hájek denominator endpoint whose score and bias errors are written
as sums of concrete one-hot multiplier perturbations.
-/
theorem tendsto_concreteUniformAssignmentBootstrapVariance_of_eventually_cell_contribution_weight_limits_and_hajek_target_denominator_univ_support_multiplierPerturbation_errors
    [Fintype Unit] [Fintype Draw] [DecidableEq Unit] [DecidableEq Draw]
    [Nonempty Unit] [DecidableEq Cell] [DecidableEq ScoreComponent]
    [DecidableEq BiasComponent]
    (cells : Finset Cell)
    (scoreComponents : Finset ScoreComponent)
    (biasComponents : Finset BiasComponent)
    (assignment : Index -> Draw -> Unit)
    (score : Index -> Unit -> Cell)
    (contribution weight : Index -> Unit -> Real)
    (target denominator normalizer sampleSize : Real)
    (cellContribution cellWeight : Index -> Cell -> Real)
    (contributionLimit weightLimit massLimit : Cell -> Real)
    (hunit_card : (Fintype.card Unit : Real) = sampleSize)
    (hdraw_card : (Fintype.card Draw : Real) = sampleSize)
    (hsampleSize_ne : sampleSize ≠ 0)
    (hbase_denominator :
      ∀ᶠ index in l,
        baseLinearizedSum (Finset.univ : Finset Unit)
          (weight index) = denominator)
    (hdenominator_ne : denominator ≠ 0)
    (htarget_hajek :
      ∀ᶠ index in l,
        target =
          baseLinearizedSum (Finset.univ : Finset Unit)
            (contribution index) / denominator)
    (hcover_all :
      ∀ᶠ index in l,
        ∀ unit, score index unit ∈ cells)
    (hcontributionCell_all :
      ∀ᶠ index in l,
        ∀ unit,
          cellContribution index (score index unit) =
            contribution index unit)
    (hweightCell_all :
      ∀ᶠ index in l,
        ∀ unit,
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
      cellwiseScoreCellMassLLN (l := l) cells
        (fun _index => (Finset.univ : Finset Unit))
        (fun _index _unit => 1) score massLimit)
    (scoreUnitComponent : Index -> Unit -> ScoreComponent -> Real)
    (biasUnitComponent : Index -> Unit -> BiasComponent -> Real)
    (hscore_unit_tendsto :
      ∀ unit,
        ∀ component, component ∈ scoreComponents ->
          Tendsto (fun index => scoreUnitComponent index unit component)
            l (nhds 0))
    (hbias_unit_tendsto :
      ∀ unit,
        ∀ component, component ∈ biasComponents ->
          Tendsto (fun index => biasUnitComponent index unit component)
            l (nhds 0)) :
    Tendsto
      (fun index =>
        (1 / denominator ^ 2) * (1 / normalizer) *
            multiplierPerturbationSecondMoment
              (uniformAssignmentSupport Unit Draw)
              (uniformAssignmentMass Unit Draw)
              (Finset.univ : Finset Unit)
              (fun assignment unit =>
                multinomialCountFromDrawIndicators
                  (Finset.univ : Finset Draw)
                  (fun assignment draw unit =>
                    oneHotAssignmentIndicator assignment draw unit)
                  assignment unit)
              (fun unit =>
                contribution index unit - target * weight index unit) +
          (∑ component ∈ scoreComponents,
            multiplierPerturbation (Finset.univ : Finset Unit)
              (fun unit =>
                multinomialCountFromDrawIndicators
                  (Finset.univ : Finset Draw)
                  (fun assignment draw unit =>
                    oneHotAssignmentIndicator assignment draw unit)
                  (assignment index) unit)
              (fun unit => scoreUnitComponent index unit component)) +
          (∑ component ∈ biasComponents,
            multiplierPerturbation (Finset.univ : Finset Unit)
              (fun unit =>
                multinomialCountFromDrawIndicators
                  (Finset.univ : Finset Draw)
                  (fun assignment draw unit =>
                    oneHotAssignmentIndicator assignment draw unit)
                  (assignment index) unit)
              (fun unit => biasUnitComponent index unit component)))
      l
      (nhds
        ((1 / denominator ^ 2) * (1 / normalizer) *
          weightedScoreCellMomentLimit cells
            (fun cell =>
              (contributionLimit cell - target * weightLimit cell) ^ 2)
            massLimit)) := by
  have hconcrete :=
    tendsto_concreteUniformAssignmentBootstrapVariance_of_eventually_cell_contribution_weight_limits_and_hajek_target_denominator_univ_support_unit_component_tendsto
      (l := l) cells scoreComponents biasComponents assignment score
      contribution weight target denominator normalizer sampleSize
      cellContribution cellWeight contributionLimit weightLimit massLimit
      hunit_card hdraw_card hsampleSize_ne hbase_denominator
      hdenominator_ne htarget_hajek hcover_all hcontributionCell_all
      hweightCell_all hcontributionLimit hweightLimit hmass
      scoreUnitComponent biasUnitComponent hscore_unit_tendsto
      hbias_unit_tendsto
  simpa [sum_multiplierPerturbation_oneHot_counts_eq_concreteOneHotUnitComponentError,
    add_assoc] using hconcrete

/--
Finite `L1(P)` bracketing companion for the multiplier-perturbation error
form of the manuscript Hájek endpoint.
-/
theorem tendsto_concreteUniformAssignmentBootstrapVariance_of_eventually_cell_contribution_weight_limits_l1BracketingNumber_obligations_and_hajek_target_denominator_univ_support_multiplierPerturbation_errors
    [Fintype Unit] [Fintype Draw] [DecidableEq Unit] [DecidableEq Draw]
    [Nonempty Unit] [DecidableEq Cell] [DecidableEq ScoreComponent]
    [DecidableEq BiasComponent]
    {Bracket : Type*} [Fintype Bracket]
    (cells : Finset Cell)
    (scoreComponents : Finset ScoreComponent)
    (biasComponents : Finset BiasComponent)
    (assignment : ℕ -> Draw -> Unit)
    (score : ℕ -> Unit -> Cell)
    (contribution weight : ℕ -> Unit -> Real)
    (target denominator normalizer sampleSize : Real)
    (cellContribution cellWeight : ℕ -> Cell -> Real)
    (contributionLimit weightLimit massLimit : Cell -> Real)
    (hunit_card : (Fintype.card Unit : Real) = sampleSize)
    (hdraw_card : (Fintype.card Draw : Real) = sampleSize)
    (hsampleSize_ne : sampleSize ≠ 0)
    (hbase_denominator :
      ∀ᶠ index in atTop,
        baseLinearizedSum (Finset.univ : Finset Unit)
          (weight index) = denominator)
    (hdenominator_ne : denominator ≠ 0)
    (htarget_hajek :
      ∀ᶠ index in atTop,
        target =
          baseLinearizedSum (Finset.univ : Finset Unit)
            (contribution index) / denominator)
    (hcover_all :
      ∀ᶠ index in atTop,
        ∀ unit, score index unit ∈ cells)
    (hcontributionCell_all :
      ∀ᶠ index in atTop,
        ∀ unit,
          cellContribution index (score index unit) =
            contribution index unit)
    (hweightCell_all :
      ∀ᶠ index in atTop,
        ∀ unit,
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
          weightedSampleSum ((fun _index : ℕ =>
              (Finset.univ : Finset Unit)) sampleSize)
            ((fun _index _unit => 1) sampleSize)
            (scoreCellIndicator (score sampleSize) cell)))
    (scoreUnitComponent : ℕ -> Unit -> ScoreComponent -> Real)
    (biasUnitComponent : ℕ -> Unit -> BiasComponent -> Real)
    (hscore_unit_tendsto :
      ∀ unit,
        ∀ component, component ∈ scoreComponents ->
          Tendsto (fun index => scoreUnitComponent index unit component)
            atTop (nhds 0))
    (hbias_unit_tendsto :
      ∀ unit,
        ∀ component, component ∈ biasComponents ->
          Tendsto (fun index => biasUnitComponent index unit component)
            atTop (nhds 0)) :
    Tendsto
      (fun index =>
        (1 / denominator ^ 2) * (1 / normalizer) *
            multiplierPerturbationSecondMoment
              (uniformAssignmentSupport Unit Draw)
              (uniformAssignmentMass Unit Draw)
              (Finset.univ : Finset Unit)
              (fun assignment unit =>
                multinomialCountFromDrawIndicators
                  (Finset.univ : Finset Draw)
                  (fun assignment draw unit =>
                    oneHotAssignmentIndicator assignment draw unit)
                  assignment unit)
              (fun unit =>
                contribution index unit - target * weight index unit) +
          (∑ component ∈ scoreComponents,
            multiplierPerturbation (Finset.univ : Finset Unit)
              (fun unit =>
                multinomialCountFromDrawIndicators
                  (Finset.univ : Finset Draw)
                  (fun assignment draw unit =>
                    oneHotAssignmentIndicator assignment draw unit)
                  (assignment index) unit)
              (fun unit => scoreUnitComponent index unit component)) +
          (∑ component ∈ biasComponents,
            multiplierPerturbation (Finset.univ : Finset Unit)
              (fun unit =>
                multinomialCountFromDrawIndicators
                  (Finset.univ : Finset Draw)
                  (fun assignment draw unit =>
                    oneHotAssignmentIndicator assignment draw unit)
                  (assignment index) unit)
              (fun unit => biasUnitComponent index unit component)))
      atTop
      (nhds
        ((1 / denominator ^ 2) * (1 / normalizer) *
          weightedScoreCellMomentLimit cells
            (fun cell =>
              (contributionLimit cell - target * weightLimit cell) ^ 2)
            massLimit)) :=
  tendsto_concreteUniformAssignmentBootstrapVariance_of_eventually_cell_contribution_weight_limits_and_hajek_target_denominator_univ_support_multiplierPerturbation_errors
    (l := atTop) cells scoreComponents biasComponents assignment score
    contribution weight target denominator normalizer sampleSize
    cellContribution cellWeight contributionLimit weightLimit massLimit
    hunit_card hdraw_card hsampleSize_ne hbase_denominator
    hdenominator_ne htarget_hajek hcover_all hcontributionCell_all
    hweightCell_all hcontributionLimit hweightLimit
    (cellwise_mass_lln_of_glivenkoCantelli_bridge
      cells massLimit (fun _index : ℕ => (Finset.univ : Finset Unit))
      (fun _index _unit => 1) score
      (weighted_indicator_array_lln_of_l1BracketingNumber_obligations
        cells massLimit
        (fun _index : ℕ => (Finset.univ : Finset Unit))
        (fun _index _unit => 1) score obligations))
    scoreUnitComponent biasUnitComponent hscore_unit_tendsto
    hbias_unit_tendsto

/--
VdV&W endpoint-assembly companion for the multiplier-perturbation error form
of the manuscript Hájek endpoint.
-/
theorem tendsto_concreteUniformAssignmentBootstrapVariance_of_eventually_cell_contribution_weight_limits_vdvw241_endpoint_assembly_and_hajek_target_denominator_univ_support_multiplierPerturbation_errors
    [Fintype Unit] [Fintype Draw] [DecidableEq Unit] [DecidableEq Draw]
    [Nonempty Unit] [DecidableEq Cell] [DecidableEq ScoreComponent]
    [DecidableEq BiasComponent]
    {Bracket : Type*} [Fintype Bracket]
    (cells : Finset Cell)
    (scoreComponents : Finset ScoreComponent)
    (biasComponents : Finset BiasComponent)
    (assignment : ℕ -> Draw -> Unit)
    (score : ℕ -> Unit -> Cell)
    (contribution weight : ℕ -> Unit -> Real)
    (target denominator normalizer sampleSize : Real)
    (cellContribution cellWeight : ℕ -> Cell -> Real)
    (contributionLimit weightLimit massLimit : Cell -> Real)
    (hunit_card : (Fintype.card Unit : Real) = sampleSize)
    (hdraw_card : (Fintype.card Draw : Real) = sampleSize)
    (hsampleSize_ne : sampleSize ≠ 0)
    (hbase_denominator :
      ∀ᶠ index in atTop,
        baseLinearizedSum (Finset.univ : Finset Unit)
          (weight index) = denominator)
    (hdenominator_ne : denominator ≠ 0)
    (htarget_hajek :
      ∀ᶠ index in atTop,
        target =
          baseLinearizedSum (Finset.univ : Finset Unit)
            (contribution index) / denominator)
    (hcover_all :
      ∀ᶠ index in atTop,
        ∀ unit, score index unit ∈ cells)
    (hcontributionCell_all :
      ∀ᶠ index in atTop,
        ∀ unit,
          cellContribution index (score index unit) =
            contribution index unit)
    (hweightCell_all :
      ∀ᶠ index in atTop,
        ∀ unit,
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
          weightedSampleSum ((fun _index : ℕ =>
              (Finset.univ : Finset Unit)) sampleSize)
            ((fun _index _unit => 1) sampleSize)
            (scoreCellIndicator (score sampleSize) cell)))
    (scoreUnitComponent : ℕ -> Unit -> ScoreComponent -> Real)
    (biasUnitComponent : ℕ -> Unit -> BiasComponent -> Real)
    (hscore_unit_tendsto :
      ∀ unit,
        ∀ component, component ∈ scoreComponents ->
          Tendsto (fun index => scoreUnitComponent index unit component)
            atTop (nhds 0))
    (hbias_unit_tendsto :
      ∀ unit,
        ∀ component, component ∈ biasComponents ->
          Tendsto (fun index => biasUnitComponent index unit component)
            atTop (nhds 0)) :
    Tendsto
      (fun index =>
        (1 / denominator ^ 2) * (1 / normalizer) *
            multiplierPerturbationSecondMoment
              (uniformAssignmentSupport Unit Draw)
              (uniformAssignmentMass Unit Draw)
              (Finset.univ : Finset Unit)
              (fun assignment unit =>
                multinomialCountFromDrawIndicators
                  (Finset.univ : Finset Draw)
                  (fun assignment draw unit =>
                    oneHotAssignmentIndicator assignment draw unit)
                  assignment unit)
              (fun unit =>
                contribution index unit - target * weight index unit) +
          (∑ component ∈ scoreComponents,
            multiplierPerturbation (Finset.univ : Finset Unit)
              (fun unit =>
                multinomialCountFromDrawIndicators
                  (Finset.univ : Finset Draw)
                  (fun assignment draw unit =>
                    oneHotAssignmentIndicator assignment draw unit)
                  (assignment index) unit)
              (fun unit => scoreUnitComponent index unit component)) +
          (∑ component ∈ biasComponents,
            multiplierPerturbation (Finset.univ : Finset Unit)
              (fun unit =>
                multinomialCountFromDrawIndicators
                  (Finset.univ : Finset Draw)
                  (fun assignment draw unit =>
                    oneHotAssignmentIndicator assignment draw unit)
                  (assignment index) unit)
              (fun unit => biasUnitComponent index unit component)))
      atTop
      (nhds
        ((1 / denominator ^ 2) * (1 / normalizer) *
          weightedScoreCellMomentLimit cells
            (fun cell =>
              (contributionLimit cell - target * weightLimit cell) ^ 2)
            massLimit)) :=
  tendsto_concreteUniformAssignmentBootstrapVariance_of_eventually_cell_contribution_weight_limits_and_hajek_target_denominator_univ_support_multiplierPerturbation_errors
    (l := atTop) cells scoreComponents biasComponents assignment score
    contribution weight target denominator normalizer sampleSize
    cellContribution cellWeight contributionLimit weightLimit massLimit
    hunit_card hdraw_card hsampleSize_ne hbase_denominator
    hdenominator_ne htarget_hajek hcover_all hcontributionCell_all
    hweightCell_all hcontributionLimit hweightLimit
    (cellwise_mass_lln_of_glivenkoCantelli_bridge
      cells massLimit (fun _index : ℕ => (Finset.univ : Finset Unit))
      (fun _index _unit => 1) score
      (weighted_indicator_array_lln_of_vdvw241_endpoint_assembly
        cells massLimit
        (fun _index : ℕ => (Finset.univ : Finset Unit))
        (fun _index _unit => 1) score assembly))
    scoreUnitComponent biasUnitComponent hscore_unit_tendsto
    hbias_unit_tendsto

/--
A finite sum of replicated-minus-base linearized sums under the concrete
one-hot multinomial counts is the literal one-hot unit-component error.
-/
theorem sum_replicatedLinearizedSum_sub_base_oneHot_counts_eq_concreteOneHotUnitComponentError
    [Fintype Unit] [Fintype Draw] [DecidableEq Unit]
    {Component : Type*} [DecidableEq Component]
    (components : Finset Component)
    (assignment : Index -> Draw -> Unit)
    (unitComponent : Index -> Unit -> Component -> Real)
    (index : Index) :
    (∑ component ∈ components,
        (replicatedLinearizedSum (Finset.univ : Finset Unit)
            (fun unit =>
              multinomialCountFromDrawIndicators (Finset.univ : Finset Draw)
                (fun assignment draw unit =>
                  oneHotAssignmentIndicator assignment draw unit)
                (assignment index) unit)
            (fun unit => unitComponent index unit component) -
          baseLinearizedSum (Finset.univ : Finset Unit)
            (fun unit => unitComponent index unit component))) =
      concreteOneHotUnitComponentError components assignment unitComponent
        index := by
  simpa [concreteOneHotUnitComponentError] using
    sum_replicatedLinearizedSum_sub_base_eq_centered_count_component_sum_of_multinomial_draw_replicate
      components (Finset.univ : Finset Unit) (Finset.univ : Finset Draw)
      (fun assignment draw unit =>
        oneHotAssignmentIndicator assignment draw unit)
      (assignment index) (unitComponent index)

/--
Equivalent normalized finite-sum form of
`sum_replicatedLinearizedSum_sub_base_oneHot_counts_eq_concreteOneHotUnitComponentError`.
-/
theorem sum_replicatedLinearizedSum_sub_sum_base_oneHot_counts_eq_concreteOneHotUnitComponentError
    [Fintype Unit] [Fintype Draw] [DecidableEq Unit]
    {Component : Type*} [DecidableEq Component]
    (components : Finset Component)
    (assignment : Index -> Draw -> Unit)
    (unitComponent : Index -> Unit -> Component -> Real)
    (index : Index) :
    ((∑ component ∈ components,
        replicatedLinearizedSum (Finset.univ : Finset Unit)
          (fun unit =>
            multinomialCountFromDrawIndicators (Finset.univ : Finset Draw)
              (fun assignment draw unit =>
                oneHotAssignmentIndicator assignment draw unit)
              (assignment index) unit)
          (fun unit => unitComponent index unit component)) -
        ∑ component ∈ components,
          baseLinearizedSum (Finset.univ : Finset Unit)
            (fun unit => unitComponent index unit component)) =
      concreteOneHotUnitComponentError components assignment unitComponent
        index := by
  rw [← Finset.sum_sub_distrib]
  exact
    sum_replicatedLinearizedSum_sub_base_oneHot_counts_eq_concreteOneHotUnitComponentError
      components assignment unitComponent index

/--
The replicated-linearized one-hot component error is negligible under
pointwise convergence of every centered-count product.
-/
theorem tendsto_replicatedLinearized_oneHot_component_error_zero_of_product_tendsto
    [Fintype Unit] [Fintype Draw] [DecidableEq Unit]
    {Component : Type*} [DecidableEq Component]
    (components : Finset Component)
    (assignment : Index -> Draw -> Unit)
    (unitComponent : Index -> Unit -> Component -> Real)
    (hproduct :
      ∀ unit,
        ∀ component, component ∈ components ->
          Tendsto
            (fun index =>
              (multinomialCountFromDrawIndicators
                  (Finset.univ : Finset Draw)
                  (fun assignment draw unit =>
                    oneHotAssignmentIndicator assignment draw unit)
                  (assignment index) unit - 1) *
                unitComponent index unit component)
            l (nhds 0)) :
    Tendsto
      (fun index =>
        ∑ component ∈ components,
          (replicatedLinearizedSum (Finset.univ : Finset Unit)
              (fun unit =>
                multinomialCountFromDrawIndicators (Finset.univ : Finset Draw)
                  (fun assignment draw unit =>
                    oneHotAssignmentIndicator assignment draw unit)
                  (assignment index) unit)
              (fun unit => unitComponent index unit component) -
            baseLinearizedSum (Finset.univ : Finset Unit)
              (fun unit => unitComponent index unit component)))
      l (nhds 0) :=
  (tendsto_concreteOneHotUnitComponentError_zero_of_product_tendsto
    (l := l) components assignment unitComponent hproduct).congr'
      (Filter.Eventually.of_forall
        (fun index =>
          (sum_replicatedLinearizedSum_sub_base_oneHot_counts_eq_concreteOneHotUnitComponentError
            components assignment unitComponent index).symm))

/--
Score-replication negligibility from an eventual equality to the
replicated-linearized one-hot component error and pointwise convergence of
its centered-count products.
-/
theorem bootstrapScoreReplicationErrorNegligible_of_replicatedLinearized_oneHot_error_product_tendsto
    [Fintype Unit] [Fintype Draw] [DecidableEq Unit]
    {Component : Type*} [DecidableEq Component]
    (components : Finset Component)
    (assignment : Index -> Draw -> Unit)
    (unitComponent : Index -> Unit -> Component -> Real)
    (scoreReplicationError : Index -> Real)
    (hconstruct :
      scoreReplicationError =ᶠ[l]
        (fun index =>
          ∑ component ∈ components,
            (replicatedLinearizedSum (Finset.univ : Finset Unit)
                (fun unit =>
                  multinomialCountFromDrawIndicators (Finset.univ : Finset Draw)
                    (fun assignment draw unit =>
                      oneHotAssignmentIndicator assignment draw unit)
                    (assignment index) unit)
                (fun unit => unitComponent index unit component) -
              baseLinearizedSum (Finset.univ : Finset Unit)
                (fun unit => unitComponent index unit component))))
    (hproduct :
      ∀ unit,
        ∀ component, component ∈ components ->
          Tendsto
            (fun index =>
              (multinomialCountFromDrawIndicators
                  (Finset.univ : Finset Draw)
                  (fun assignment draw unit =>
                    oneHotAssignmentIndicator assignment draw unit)
                  (assignment index) unit - 1) *
                unitComponent index unit component)
            l (nhds 0)) :
    bootstrapScoreReplicationErrorNegligible
      (l := l) scoreReplicationError :=
  (tendsto_replicatedLinearized_oneHot_component_error_zero_of_product_tendsto
    (l := l) components assignment unitComponent hproduct).congr'
      hconstruct.symm

/--
Bias-correction negligibility from an eventual equality to the
replicated-linearized one-hot component error and pointwise convergence of
its centered-count products.
-/
theorem bootstrapBiasCorrectionErrorNegligible_of_replicatedLinearized_oneHot_error_product_tendsto
    [Fintype Unit] [Fintype Draw] [DecidableEq Unit]
    {Component : Type*} [DecidableEq Component]
    (components : Finset Component)
    (assignment : Index -> Draw -> Unit)
    (unitComponent : Index -> Unit -> Component -> Real)
    (biasCorrectionError : Index -> Real)
    (hconstruct :
      biasCorrectionError =ᶠ[l]
        (fun index =>
          ∑ component ∈ components,
            (replicatedLinearizedSum (Finset.univ : Finset Unit)
                (fun unit =>
                  multinomialCountFromDrawIndicators (Finset.univ : Finset Draw)
                    (fun assignment draw unit =>
                      oneHotAssignmentIndicator assignment draw unit)
                    (assignment index) unit)
                (fun unit => unitComponent index unit component) -
              baseLinearizedSum (Finset.univ : Finset Unit)
                (fun unit => unitComponent index unit component))))
    (hproduct :
      ∀ unit,
        ∀ component, component ∈ components ->
          Tendsto
            (fun index =>
              (multinomialCountFromDrawIndicators
                  (Finset.univ : Finset Draw)
                  (fun assignment draw unit =>
                    oneHotAssignmentIndicator assignment draw unit)
                  (assignment index) unit - 1) *
                unitComponent index unit component)
            l (nhds 0)) :
    bootstrapBiasCorrectionErrorNegligible
      (l := l) biasCorrectionError :=
  (tendsto_replicatedLinearized_oneHot_component_error_zero_of_product_tendsto
    (l := l) components assignment unitComponent hproduct).congr'
      hconstruct.symm

/--
The replicated-linearized one-hot component error is negligible under
pointwise convergence of every fixed unit component.
-/
theorem tendsto_replicatedLinearized_oneHot_component_error_zero_of_unitComponent_tendsto
    [Fintype Unit] [Fintype Draw] [DecidableEq Unit]
    {Component : Type*} [DecidableEq Component]
    (components : Finset Component)
    (assignment : Index -> Draw -> Unit)
    (unitComponent : Index -> Unit -> Component -> Real)
    (hunit :
      ∀ unit,
        ∀ component, component ∈ components ->
          Tendsto (fun index => unitComponent index unit component)
            l (nhds 0)) :
    Tendsto
      (fun index =>
        ∑ component ∈ components,
          (replicatedLinearizedSum (Finset.univ : Finset Unit)
              (fun unit =>
                multinomialCountFromDrawIndicators (Finset.univ : Finset Draw)
                  (fun assignment draw unit =>
                    oneHotAssignmentIndicator assignment draw unit)
                  (assignment index) unit)
              (fun unit => unitComponent index unit component) -
            baseLinearizedSum (Finset.univ : Finset Unit)
              (fun unit => unitComponent index unit component)))
      l (nhds 0) :=
  tendsto_replicatedLinearized_oneHot_component_error_zero_of_product_tendsto
    (l := l) components assignment unitComponent
    (fun unit component hcomponent =>
      tendsto_centered_oneHot_count_mul_unitComponent_zero_of_unitComponent_tendsto
        (l := l) assignment unitComponent unit component
        (hunit unit component hcomponent))

/--
Score-replication negligibility for the replicated-linearized one-hot
component error from pointwise convergence of every fixed unit component.
-/
theorem bootstrapScoreReplicationErrorNegligible_of_replicatedLinearized_oneHot_error_unitComponent_tendsto
    [Fintype Unit] [Fintype Draw] [DecidableEq Unit]
    {Component : Type*} [DecidableEq Component]
    (components : Finset Component)
    (assignment : Index -> Draw -> Unit)
    (unitComponent : Index -> Unit -> Component -> Real)
    (scoreReplicationError : Index -> Real)
    (hconstruct :
      scoreReplicationError =ᶠ[l]
        (fun index =>
          ∑ component ∈ components,
            (replicatedLinearizedSum (Finset.univ : Finset Unit)
                (fun unit =>
                  multinomialCountFromDrawIndicators (Finset.univ : Finset Draw)
                    (fun assignment draw unit =>
                      oneHotAssignmentIndicator assignment draw unit)
                    (assignment index) unit)
                (fun unit => unitComponent index unit component) -
              baseLinearizedSum (Finset.univ : Finset Unit)
                (fun unit => unitComponent index unit component))))
    (hunit :
      ∀ unit,
        ∀ component, component ∈ components ->
          Tendsto (fun index => unitComponent index unit component)
            l (nhds 0)) :
    bootstrapScoreReplicationErrorNegligible
      (l := l) scoreReplicationError :=
  (tendsto_replicatedLinearized_oneHot_component_error_zero_of_unitComponent_tendsto
    (l := l) components assignment unitComponent hunit).congr'
      hconstruct.symm

/--
Bias-correction negligibility for the replicated-linearized one-hot
component error from pointwise convergence of every fixed unit component.
-/
theorem bootstrapBiasCorrectionErrorNegligible_of_replicatedLinearized_oneHot_error_unitComponent_tendsto
    [Fintype Unit] [Fintype Draw] [DecidableEq Unit]
    {Component : Type*} [DecidableEq Component]
    (components : Finset Component)
    (assignment : Index -> Draw -> Unit)
    (unitComponent : Index -> Unit -> Component -> Real)
    (biasCorrectionError : Index -> Real)
    (hconstruct :
      biasCorrectionError =ᶠ[l]
        (fun index =>
          ∑ component ∈ components,
            (replicatedLinearizedSum (Finset.univ : Finset Unit)
                (fun unit =>
                  multinomialCountFromDrawIndicators (Finset.univ : Finset Draw)
                    (fun assignment draw unit =>
                      oneHotAssignmentIndicator assignment draw unit)
                    (assignment index) unit)
                (fun unit => unitComponent index unit component) -
              baseLinearizedSum (Finset.univ : Finset Unit)
                (fun unit => unitComponent index unit component))))
    (hunit :
      ∀ unit,
        ∀ component, component ∈ components ->
          Tendsto (fun index => unitComponent index unit component)
            l (nhds 0)) :
    bootstrapBiasCorrectionErrorNegligible
      (l := l) biasCorrectionError :=
  (tendsto_replicatedLinearized_oneHot_component_error_zero_of_unitComponent_tendsto
    (l := l) components assignment unitComponent hunit).congr'
      hconstruct.symm

/--
Manuscript Hájek denominator endpoint whose score and bias errors are written
as replicated-minus-base linearized sums under the concrete one-hot counts.
-/
theorem tendsto_concreteUniformAssignmentBootstrapVariance_of_eventually_cell_contribution_weight_limits_and_hajek_target_denominator_univ_support_replicatedLinearized_errors
    [Fintype Unit] [Fintype Draw] [DecidableEq Unit] [DecidableEq Draw]
    [Nonempty Unit] [DecidableEq Cell] [DecidableEq ScoreComponent]
    [DecidableEq BiasComponent]
    (cells : Finset Cell)
    (scoreComponents : Finset ScoreComponent)
    (biasComponents : Finset BiasComponent)
    (assignment : Index -> Draw -> Unit)
    (score : Index -> Unit -> Cell)
    (contribution weight : Index -> Unit -> Real)
    (target denominator normalizer sampleSize : Real)
    (cellContribution cellWeight : Index -> Cell -> Real)
    (contributionLimit weightLimit massLimit : Cell -> Real)
    (hunit_card : (Fintype.card Unit : Real) = sampleSize)
    (hdraw_card : (Fintype.card Draw : Real) = sampleSize)
    (hsampleSize_ne : sampleSize ≠ 0)
    (hbase_denominator :
      ∀ᶠ index in l,
        baseLinearizedSum (Finset.univ : Finset Unit)
          (weight index) = denominator)
    (hdenominator_ne : denominator ≠ 0)
    (htarget_hajek :
      ∀ᶠ index in l,
        target =
          baseLinearizedSum (Finset.univ : Finset Unit)
            (contribution index) / denominator)
    (hcover_all :
      ∀ᶠ index in l,
        ∀ unit, score index unit ∈ cells)
    (hcontributionCell_all :
      ∀ᶠ index in l,
        ∀ unit,
          cellContribution index (score index unit) =
            contribution index unit)
    (hweightCell_all :
      ∀ᶠ index in l,
        ∀ unit,
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
      cellwiseScoreCellMassLLN (l := l) cells
        (fun _index => (Finset.univ : Finset Unit))
        (fun _index _unit => 1) score massLimit)
    (scoreUnitComponent : Index -> Unit -> ScoreComponent -> Real)
    (biasUnitComponent : Index -> Unit -> BiasComponent -> Real)
    (hscore_unit_tendsto :
      ∀ unit,
        ∀ component, component ∈ scoreComponents ->
          Tendsto (fun index => scoreUnitComponent index unit component)
            l (nhds 0))
    (hbias_unit_tendsto :
      ∀ unit,
        ∀ component, component ∈ biasComponents ->
          Tendsto (fun index => biasUnitComponent index unit component)
            l (nhds 0)) :
    Tendsto
      (fun index =>
        (1 / denominator ^ 2) * (1 / normalizer) *
            multiplierPerturbationSecondMoment
              (uniformAssignmentSupport Unit Draw)
              (uniformAssignmentMass Unit Draw)
              (Finset.univ : Finset Unit)
              (fun assignment unit =>
                multinomialCountFromDrawIndicators
                  (Finset.univ : Finset Draw)
                  (fun assignment draw unit =>
                    oneHotAssignmentIndicator assignment draw unit)
                  assignment unit)
              (fun unit =>
                contribution index unit - target * weight index unit) +
          (∑ component ∈ scoreComponents,
            (replicatedLinearizedSum (Finset.univ : Finset Unit)
                (fun unit =>
                  multinomialCountFromDrawIndicators
                    (Finset.univ : Finset Draw)
                    (fun assignment draw unit =>
                      oneHotAssignmentIndicator assignment draw unit)
                    (assignment index) unit)
                (fun unit => scoreUnitComponent index unit component) -
              baseLinearizedSum (Finset.univ : Finset Unit)
                (fun unit => scoreUnitComponent index unit component))) +
          (∑ component ∈ biasComponents,
            (replicatedLinearizedSum (Finset.univ : Finset Unit)
                (fun unit =>
                  multinomialCountFromDrawIndicators
                    (Finset.univ : Finset Draw)
                    (fun assignment draw unit =>
                      oneHotAssignmentIndicator assignment draw unit)
                    (assignment index) unit)
              (fun unit => biasUnitComponent index unit component) -
              baseLinearizedSum (Finset.univ : Finset Unit)
                (fun unit => biasUnitComponent index unit component))))
      l
      (nhds
        ((1 / denominator ^ 2) * (1 / normalizer) *
          weightedScoreCellMomentLimit cells
            (fun cell =>
              (contributionLimit cell - target * weightLimit cell) ^ 2)
            massLimit)) := by
  have hconcrete :=
    tendsto_concreteUniformAssignmentBootstrapVariance_of_eventually_cell_contribution_weight_limits_and_hajek_target_denominator_univ_support_unit_component_tendsto
      (l := l) cells scoreComponents biasComponents assignment score
      contribution weight target denominator normalizer sampleSize
      cellContribution cellWeight contributionLimit weightLimit massLimit
      hunit_card hdraw_card hsampleSize_ne hbase_denominator
      hdenominator_ne htarget_hajek hcover_all hcontributionCell_all
      hweightCell_all hcontributionLimit hweightLimit hmass
      scoreUnitComponent biasUnitComponent hscore_unit_tendsto
      hbias_unit_tendsto
  simpa [sum_replicatedLinearizedSum_sub_sum_base_oneHot_counts_eq_concreteOneHotUnitComponentError,
    add_assoc] using hconcrete

/--
Named-error version of the replicated-linearized manuscript Hájek endpoint.
The score-replication and bias-correction terms may be supplied as actual
error sequences once they are eventually identified with the finite
replicated-minus-base constructions.
-/
theorem tendsto_concreteUniformAssignmentBootstrapVariance_of_eventually_cell_contribution_weight_limits_and_hajek_target_denominator_univ_support_replicatedLinearized_error_constructs
    [Fintype Unit] [Fintype Draw] [DecidableEq Unit] [DecidableEq Draw]
    [Nonempty Unit] [DecidableEq Cell] [DecidableEq ScoreComponent]
    [DecidableEq BiasComponent]
    (cells : Finset Cell)
    (scoreComponents : Finset ScoreComponent)
    (biasComponents : Finset BiasComponent)
    (assignment : Index -> Draw -> Unit)
    (score : Index -> Unit -> Cell)
    (contribution weight : Index -> Unit -> Real)
    (target denominator normalizer sampleSize : Real)
    (cellContribution cellWeight : Index -> Cell -> Real)
    (contributionLimit weightLimit massLimit : Cell -> Real)
    (scoreReplicationError biasCorrectionError : Index -> Real)
    (scoreUnitComponent : Index -> Unit -> ScoreComponent -> Real)
    (biasUnitComponent : Index -> Unit -> BiasComponent -> Real)
    (hunit_card : (Fintype.card Unit : Real) = sampleSize)
    (hdraw_card : (Fintype.card Draw : Real) = sampleSize)
    (hsampleSize_ne : sampleSize ≠ 0)
    (hbase_denominator :
      ∀ᶠ index in l,
        baseLinearizedSum (Finset.univ : Finset Unit)
          (weight index) = denominator)
    (hdenominator_ne : denominator ≠ 0)
    (htarget_hajek :
      ∀ᶠ index in l,
        target =
          baseLinearizedSum (Finset.univ : Finset Unit)
            (contribution index) / denominator)
    (hcover_all :
      ∀ᶠ index in l,
        ∀ unit, score index unit ∈ cells)
    (hcontributionCell_all :
      ∀ᶠ index in l,
        ∀ unit,
          cellContribution index (score index unit) =
            contribution index unit)
    (hweightCell_all :
      ∀ᶠ index in l,
        ∀ unit,
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
      cellwiseScoreCellMassLLN (l := l) cells
        (fun _index => (Finset.univ : Finset Unit))
        (fun _index _unit => 1) score massLimit)
    (hscore_construct :
      scoreReplicationError =ᶠ[l]
        (fun index =>
          ∑ component ∈ scoreComponents,
            (replicatedLinearizedSum (Finset.univ : Finset Unit)
                (fun unit =>
                  multinomialCountFromDrawIndicators (Finset.univ : Finset Draw)
                    (fun assignment draw unit =>
                      oneHotAssignmentIndicator assignment draw unit)
                    (assignment index) unit)
                (fun unit => scoreUnitComponent index unit component) -
              baseLinearizedSum (Finset.univ : Finset Unit)
                (fun unit => scoreUnitComponent index unit component))))
    (hscore_unit_tendsto :
      ∀ unit,
        ∀ component, component ∈ scoreComponents ->
          Tendsto (fun index => scoreUnitComponent index unit component)
            l (nhds 0))
    (hbias_construct :
      biasCorrectionError =ᶠ[l]
        (fun index =>
          ∑ component ∈ biasComponents,
            (replicatedLinearizedSum (Finset.univ : Finset Unit)
                (fun unit =>
                  multinomialCountFromDrawIndicators (Finset.univ : Finset Draw)
                    (fun assignment draw unit =>
                      oneHotAssignmentIndicator assignment draw unit)
                    (assignment index) unit)
                (fun unit => biasUnitComponent index unit component) -
              baseLinearizedSum (Finset.univ : Finset Unit)
                (fun unit => biasUnitComponent index unit component))))
    (hbias_unit_tendsto :
      ∀ unit,
        ∀ component, component ∈ biasComponents ->
          Tendsto (fun index => biasUnitComponent index unit component)
            l (nhds 0)) :
    Tendsto
      (fun index =>
        (1 / denominator ^ 2) * (1 / normalizer) *
            multiplierPerturbationSecondMoment
              (uniformAssignmentSupport Unit Draw)
              (uniformAssignmentMass Unit Draw)
              (Finset.univ : Finset Unit)
              (fun assignment unit =>
                multinomialCountFromDrawIndicators
                  (Finset.univ : Finset Draw)
                  (fun assignment draw unit =>
                    oneHotAssignmentIndicator assignment draw unit)
                  assignment unit)
              (fun unit =>
                contribution index unit - target * weight index unit) +
          scoreReplicationError index + biasCorrectionError index)
      l
      (nhds
        ((1 / denominator ^ 2) * (1 / normalizer) *
          weightedScoreCellMomentLimit cells
            (fun cell =>
              (contributionLimit cell - target * weightLimit cell) ^ 2)
            massLimit)) := by
  have hreplicated :=
    tendsto_concreteUniformAssignmentBootstrapVariance_of_eventually_cell_contribution_weight_limits_and_hajek_target_denominator_univ_support_replicatedLinearized_errors
      (l := l) cells scoreComponents biasComponents assignment score
      contribution weight target denominator normalizer sampleSize
      cellContribution cellWeight contributionLimit weightLimit massLimit
      hunit_card hdraw_card hsampleSize_ne hbase_denominator
      hdenominator_ne htarget_hajek hcover_all hcontributionCell_all
      hweightCell_all hcontributionLimit hweightLimit hmass
      scoreUnitComponent biasUnitComponent hscore_unit_tendsto
      hbias_unit_tendsto
  exact hreplicated.congr' <| by
    filter_upwards [hscore_construct, hbias_construct] with index hscore hbias
    rw [← hscore, ← hbias]

/--
Finite `L1(P)` bracketing companion for the named-error
replicated-linearized manuscript Hájek endpoint.
-/
theorem tendsto_concreteUniformAssignmentBootstrapVariance_of_eventually_cell_contribution_weight_limits_l1BracketingNumber_obligations_and_hajek_target_denominator_univ_support_replicatedLinearized_error_constructs
    [Fintype Unit] [Fintype Draw] [DecidableEq Unit] [DecidableEq Draw]
    [Nonempty Unit] [DecidableEq Cell] [DecidableEq ScoreComponent]
    [DecidableEq BiasComponent]
    {Bracket : Type*} [Fintype Bracket]
    (cells : Finset Cell)
    (scoreComponents : Finset ScoreComponent)
    (biasComponents : Finset BiasComponent)
    (assignment : ℕ -> Draw -> Unit)
    (score : ℕ -> Unit -> Cell)
    (contribution weight : ℕ -> Unit -> Real)
    (target denominator normalizer sampleSize : Real)
    (cellContribution cellWeight : ℕ -> Cell -> Real)
    (contributionLimit weightLimit massLimit : Cell -> Real)
    (scoreReplicationError biasCorrectionError : ℕ -> Real)
    (scoreUnitComponent : ℕ -> Unit -> ScoreComponent -> Real)
    (biasUnitComponent : ℕ -> Unit -> BiasComponent -> Real)
    (hunit_card : (Fintype.card Unit : Real) = sampleSize)
    (hdraw_card : (Fintype.card Draw : Real) = sampleSize)
    (hsampleSize_ne : sampleSize ≠ 0)
    (hbase_denominator :
      ∀ᶠ index in atTop,
        baseLinearizedSum (Finset.univ : Finset Unit)
          (weight index) = denominator)
    (hdenominator_ne : denominator ≠ 0)
    (htarget_hajek :
      ∀ᶠ index in atTop,
        target =
          baseLinearizedSum (Finset.univ : Finset Unit)
            (contribution index) / denominator)
    (hcover_all :
      ∀ᶠ index in atTop,
        ∀ unit, score index unit ∈ cells)
    (hcontributionCell_all :
      ∀ᶠ index in atTop,
        ∀ unit,
          cellContribution index (score index unit) =
            contribution index unit)
    (hweightCell_all :
      ∀ᶠ index in atTop,
        ∀ unit,
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
          weightedSampleSum ((fun _index : ℕ =>
              (Finset.univ : Finset Unit)) sampleSize)
            ((fun _index _unit => 1) sampleSize)
            (scoreCellIndicator (score sampleSize) cell)))
    (hscore_construct :
      scoreReplicationError =ᶠ[atTop]
        (fun index =>
          ∑ component ∈ scoreComponents,
            (replicatedLinearizedSum (Finset.univ : Finset Unit)
                (fun unit =>
                  multinomialCountFromDrawIndicators (Finset.univ : Finset Draw)
                    (fun assignment draw unit =>
                      oneHotAssignmentIndicator assignment draw unit)
                    (assignment index) unit)
                (fun unit => scoreUnitComponent index unit component) -
              baseLinearizedSum (Finset.univ : Finset Unit)
                (fun unit => scoreUnitComponent index unit component))))
    (hscore_unit_tendsto :
      ∀ unit,
        ∀ component, component ∈ scoreComponents ->
          Tendsto (fun index => scoreUnitComponent index unit component)
            atTop (nhds 0))
    (hbias_construct :
      biasCorrectionError =ᶠ[atTop]
        (fun index =>
          ∑ component ∈ biasComponents,
            (replicatedLinearizedSum (Finset.univ : Finset Unit)
                (fun unit =>
                  multinomialCountFromDrawIndicators (Finset.univ : Finset Draw)
                    (fun assignment draw unit =>
                      oneHotAssignmentIndicator assignment draw unit)
                    (assignment index) unit)
                (fun unit => biasUnitComponent index unit component) -
              baseLinearizedSum (Finset.univ : Finset Unit)
                (fun unit => biasUnitComponent index unit component))))
    (hbias_unit_tendsto :
      ∀ unit,
        ∀ component, component ∈ biasComponents ->
          Tendsto (fun index => biasUnitComponent index unit component)
            atTop (nhds 0)) :
    Tendsto
      (fun index =>
        (1 / denominator ^ 2) * (1 / normalizer) *
            multiplierPerturbationSecondMoment
              (uniformAssignmentSupport Unit Draw)
              (uniformAssignmentMass Unit Draw)
              (Finset.univ : Finset Unit)
              (fun assignment unit =>
                multinomialCountFromDrawIndicators
                  (Finset.univ : Finset Draw)
                  (fun assignment draw unit =>
                    oneHotAssignmentIndicator assignment draw unit)
                  assignment unit)
              (fun unit =>
                contribution index unit - target * weight index unit) +
          scoreReplicationError index + biasCorrectionError index)
      atTop
      (nhds
        ((1 / denominator ^ 2) * (1 / normalizer) *
          weightedScoreCellMomentLimit cells
            (fun cell =>
              (contributionLimit cell - target * weightLimit cell) ^ 2)
            massLimit)) :=
  tendsto_concreteUniformAssignmentBootstrapVariance_of_eventually_cell_contribution_weight_limits_and_hajek_target_denominator_univ_support_replicatedLinearized_error_constructs
    (l := atTop) cells scoreComponents biasComponents assignment score
    contribution weight target denominator normalizer sampleSize
    cellContribution cellWeight contributionLimit weightLimit massLimit
    scoreReplicationError biasCorrectionError scoreUnitComponent
    biasUnitComponent hunit_card hdraw_card hsampleSize_ne
    hbase_denominator hdenominator_ne htarget_hajek hcover_all
    hcontributionCell_all hweightCell_all hcontributionLimit
    hweightLimit
    (cellwise_mass_lln_of_glivenkoCantelli_bridge
      cells massLimit (fun _index : ℕ => (Finset.univ : Finset Unit))
      (fun _index _unit => 1) score
      (weighted_indicator_array_lln_of_l1BracketingNumber_obligations
        cells massLimit
        (fun _index : ℕ => (Finset.univ : Finset Unit))
        (fun _index _unit => 1) score obligations))
    hscore_construct hscore_unit_tendsto hbias_construct
    hbias_unit_tendsto

/--
VdV&W endpoint-assembly companion for the named-error
replicated-linearized manuscript Hájek endpoint.
-/
theorem tendsto_concreteUniformAssignmentBootstrapVariance_of_eventually_cell_contribution_weight_limits_vdvw241_endpoint_assembly_and_hajek_target_denominator_univ_support_replicatedLinearized_error_constructs
    [Fintype Unit] [Fintype Draw] [DecidableEq Unit] [DecidableEq Draw]
    [Nonempty Unit] [DecidableEq Cell] [DecidableEq ScoreComponent]
    [DecidableEq BiasComponent]
    {Bracket : Type*} [Fintype Bracket]
    (cells : Finset Cell)
    (scoreComponents : Finset ScoreComponent)
    (biasComponents : Finset BiasComponent)
    (assignment : ℕ -> Draw -> Unit)
    (score : ℕ -> Unit -> Cell)
    (contribution weight : ℕ -> Unit -> Real)
    (target denominator normalizer sampleSize : Real)
    (cellContribution cellWeight : ℕ -> Cell -> Real)
    (contributionLimit weightLimit massLimit : Cell -> Real)
    (scoreReplicationError biasCorrectionError : ℕ -> Real)
    (scoreUnitComponent : ℕ -> Unit -> ScoreComponent -> Real)
    (biasUnitComponent : ℕ -> Unit -> BiasComponent -> Real)
    (hunit_card : (Fintype.card Unit : Real) = sampleSize)
    (hdraw_card : (Fintype.card Draw : Real) = sampleSize)
    (hsampleSize_ne : sampleSize ≠ 0)
    (hbase_denominator :
      ∀ᶠ index in atTop,
        baseLinearizedSum (Finset.univ : Finset Unit)
          (weight index) = denominator)
    (hdenominator_ne : denominator ≠ 0)
    (htarget_hajek :
      ∀ᶠ index in atTop,
        target =
          baseLinearizedSum (Finset.univ : Finset Unit)
            (contribution index) / denominator)
    (hcover_all :
      ∀ᶠ index in atTop,
        ∀ unit, score index unit ∈ cells)
    (hcontributionCell_all :
      ∀ᶠ index in atTop,
        ∀ unit,
          cellContribution index (score index unit) =
            contribution index unit)
    (hweightCell_all :
      ∀ᶠ index in atTop,
        ∀ unit,
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
          weightedSampleSum ((fun _index : ℕ =>
              (Finset.univ : Finset Unit)) sampleSize)
            ((fun _index _unit => 1) sampleSize)
            (scoreCellIndicator (score sampleSize) cell)))
    (hscore_construct :
      scoreReplicationError =ᶠ[atTop]
        (fun index =>
          ∑ component ∈ scoreComponents,
            (replicatedLinearizedSum (Finset.univ : Finset Unit)
                (fun unit =>
                  multinomialCountFromDrawIndicators (Finset.univ : Finset Draw)
                    (fun assignment draw unit =>
                      oneHotAssignmentIndicator assignment draw unit)
                    (assignment index) unit)
                (fun unit => scoreUnitComponent index unit component) -
              baseLinearizedSum (Finset.univ : Finset Unit)
                (fun unit => scoreUnitComponent index unit component))))
    (hscore_unit_tendsto :
      ∀ unit,
        ∀ component, component ∈ scoreComponents ->
          Tendsto (fun index => scoreUnitComponent index unit component)
            atTop (nhds 0))
    (hbias_construct :
      biasCorrectionError =ᶠ[atTop]
        (fun index =>
          ∑ component ∈ biasComponents,
            (replicatedLinearizedSum (Finset.univ : Finset Unit)
                (fun unit =>
                  multinomialCountFromDrawIndicators (Finset.univ : Finset Draw)
                    (fun assignment draw unit =>
                      oneHotAssignmentIndicator assignment draw unit)
                    (assignment index) unit)
                (fun unit => biasUnitComponent index unit component) -
              baseLinearizedSum (Finset.univ : Finset Unit)
                (fun unit => biasUnitComponent index unit component))))
    (hbias_unit_tendsto :
      ∀ unit,
        ∀ component, component ∈ biasComponents ->
          Tendsto (fun index => biasUnitComponent index unit component)
            atTop (nhds 0)) :
    Tendsto
      (fun index =>
        (1 / denominator ^ 2) * (1 / normalizer) *
            multiplierPerturbationSecondMoment
              (uniformAssignmentSupport Unit Draw)
              (uniformAssignmentMass Unit Draw)
              (Finset.univ : Finset Unit)
              (fun assignment unit =>
                multinomialCountFromDrawIndicators
                  (Finset.univ : Finset Draw)
                  (fun assignment draw unit =>
                    oneHotAssignmentIndicator assignment draw unit)
                  assignment unit)
              (fun unit =>
                contribution index unit - target * weight index unit) +
          scoreReplicationError index + biasCorrectionError index)
      atTop
      (nhds
        ((1 / denominator ^ 2) * (1 / normalizer) *
          weightedScoreCellMomentLimit cells
            (fun cell =>
              (contributionLimit cell - target * weightLimit cell) ^ 2)
            massLimit)) :=
  tendsto_concreteUniformAssignmentBootstrapVariance_of_eventually_cell_contribution_weight_limits_and_hajek_target_denominator_univ_support_replicatedLinearized_error_constructs
    (l := atTop) cells scoreComponents biasComponents assignment score
    contribution weight target denominator normalizer sampleSize
    cellContribution cellWeight contributionLimit weightLimit massLimit
    scoreReplicationError biasCorrectionError scoreUnitComponent
    biasUnitComponent hunit_card hdraw_card hsampleSize_ne
    hbase_denominator hdenominator_ne htarget_hajek hcover_all
    hcontributionCell_all hweightCell_all hcontributionLimit
    hweightLimit
    (cellwise_mass_lln_of_glivenkoCantelli_bridge
      cells massLimit (fun _index : ℕ => (Finset.univ : Finset Unit))
      (fun _index _unit => 1) score
      (weighted_indicator_array_lln_of_vdvw241_endpoint_assembly
        cells massLimit
        (fun _index : ℕ => (Finset.univ : Finset Unit))
        (fun _index _unit => 1) score assembly))
    hscore_construct hscore_unit_tendsto hbias_construct
    hbias_unit_tendsto

/--
Finite `L1(P)` bracketing companion for the replicated-linearized error
form of the manuscript Hájek endpoint.
-/
theorem tendsto_concreteUniformAssignmentBootstrapVariance_of_eventually_cell_contribution_weight_limits_l1BracketingNumber_obligations_and_hajek_target_denominator_univ_support_replicatedLinearized_errors
    [Fintype Unit] [Fintype Draw] [DecidableEq Unit] [DecidableEq Draw]
    [Nonempty Unit] [DecidableEq Cell] [DecidableEq ScoreComponent]
    [DecidableEq BiasComponent]
    {Bracket : Type*} [Fintype Bracket]
    (cells : Finset Cell)
    (scoreComponents : Finset ScoreComponent)
    (biasComponents : Finset BiasComponent)
    (assignment : ℕ -> Draw -> Unit)
    (score : ℕ -> Unit -> Cell)
    (contribution weight : ℕ -> Unit -> Real)
    (target denominator normalizer sampleSize : Real)
    (cellContribution cellWeight : ℕ -> Cell -> Real)
    (contributionLimit weightLimit massLimit : Cell -> Real)
    (hunit_card : (Fintype.card Unit : Real) = sampleSize)
    (hdraw_card : (Fintype.card Draw : Real) = sampleSize)
    (hsampleSize_ne : sampleSize ≠ 0)
    (hbase_denominator :
      ∀ᶠ index in atTop,
        baseLinearizedSum (Finset.univ : Finset Unit)
          (weight index) = denominator)
    (hdenominator_ne : denominator ≠ 0)
    (htarget_hajek :
      ∀ᶠ index in atTop,
        target =
          baseLinearizedSum (Finset.univ : Finset Unit)
            (contribution index) / denominator)
    (hcover_all :
      ∀ᶠ index in atTop,
        ∀ unit, score index unit ∈ cells)
    (hcontributionCell_all :
      ∀ᶠ index in atTop,
        ∀ unit,
          cellContribution index (score index unit) =
            contribution index unit)
    (hweightCell_all :
      ∀ᶠ index in atTop,
        ∀ unit,
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
          weightedSampleSum ((fun _index : ℕ =>
              (Finset.univ : Finset Unit)) sampleSize)
            ((fun _index _unit => 1) sampleSize)
            (scoreCellIndicator (score sampleSize) cell)))
    (scoreUnitComponent : ℕ -> Unit -> ScoreComponent -> Real)
    (biasUnitComponent : ℕ -> Unit -> BiasComponent -> Real)
    (hscore_unit_tendsto :
      ∀ unit,
        ∀ component, component ∈ scoreComponents ->
          Tendsto (fun index => scoreUnitComponent index unit component)
            atTop (nhds 0))
    (hbias_unit_tendsto :
      ∀ unit,
        ∀ component, component ∈ biasComponents ->
          Tendsto (fun index => biasUnitComponent index unit component)
            atTop (nhds 0)) :
    Tendsto
      (fun index =>
        (1 / denominator ^ 2) * (1 / normalizer) *
            multiplierPerturbationSecondMoment
              (uniformAssignmentSupport Unit Draw)
              (uniformAssignmentMass Unit Draw)
              (Finset.univ : Finset Unit)
              (fun assignment unit =>
                multinomialCountFromDrawIndicators
                  (Finset.univ : Finset Draw)
                  (fun assignment draw unit =>
                    oneHotAssignmentIndicator assignment draw unit)
                  assignment unit)
              (fun unit =>
                contribution index unit - target * weight index unit) +
          (∑ component ∈ scoreComponents,
            (replicatedLinearizedSum (Finset.univ : Finset Unit)
                (fun unit =>
                  multinomialCountFromDrawIndicators
                    (Finset.univ : Finset Draw)
                    (fun assignment draw unit =>
                      oneHotAssignmentIndicator assignment draw unit)
                    (assignment index) unit)
                (fun unit => scoreUnitComponent index unit component) -
              baseLinearizedSum (Finset.univ : Finset Unit)
                (fun unit => scoreUnitComponent index unit component))) +
          (∑ component ∈ biasComponents,
            (replicatedLinearizedSum (Finset.univ : Finset Unit)
                (fun unit =>
                  multinomialCountFromDrawIndicators
                    (Finset.univ : Finset Draw)
                    (fun assignment draw unit =>
                      oneHotAssignmentIndicator assignment draw unit)
                    (assignment index) unit)
              (fun unit => biasUnitComponent index unit component) -
              baseLinearizedSum (Finset.univ : Finset Unit)
                (fun unit => biasUnitComponent index unit component))))
      atTop
      (nhds
        ((1 / denominator ^ 2) * (1 / normalizer) *
          weightedScoreCellMomentLimit cells
            (fun cell =>
              (contributionLimit cell - target * weightLimit cell) ^ 2)
            massLimit)) :=
  tendsto_concreteUniformAssignmentBootstrapVariance_of_eventually_cell_contribution_weight_limits_and_hajek_target_denominator_univ_support_replicatedLinearized_errors
    (l := atTop) cells scoreComponents biasComponents assignment score
    contribution weight target denominator normalizer sampleSize
    cellContribution cellWeight contributionLimit weightLimit massLimit
    hunit_card hdraw_card hsampleSize_ne hbase_denominator
    hdenominator_ne htarget_hajek hcover_all hcontributionCell_all
    hweightCell_all hcontributionLimit hweightLimit
    (cellwise_mass_lln_of_glivenkoCantelli_bridge
      cells massLimit (fun _index : ℕ => (Finset.univ : Finset Unit))
      (fun _index _unit => 1) score
      (weighted_indicator_array_lln_of_l1BracketingNumber_obligations
        cells massLimit
        (fun _index : ℕ => (Finset.univ : Finset Unit))
        (fun _index _unit => 1) score obligations))
    scoreUnitComponent biasUnitComponent hscore_unit_tendsto
    hbias_unit_tendsto

/--
VdV&W endpoint-assembly companion for the replicated-linearized error form
of the manuscript Hájek endpoint.
-/
theorem tendsto_concreteUniformAssignmentBootstrapVariance_of_eventually_cell_contribution_weight_limits_vdvw241_endpoint_assembly_and_hajek_target_denominator_univ_support_replicatedLinearized_errors
    [Fintype Unit] [Fintype Draw] [DecidableEq Unit] [DecidableEq Draw]
    [Nonempty Unit] [DecidableEq Cell] [DecidableEq ScoreComponent]
    [DecidableEq BiasComponent]
    {Bracket : Type*} [Fintype Bracket]
    (cells : Finset Cell)
    (scoreComponents : Finset ScoreComponent)
    (biasComponents : Finset BiasComponent)
    (assignment : ℕ -> Draw -> Unit)
    (score : ℕ -> Unit -> Cell)
    (contribution weight : ℕ -> Unit -> Real)
    (target denominator normalizer sampleSize : Real)
    (cellContribution cellWeight : ℕ -> Cell -> Real)
    (contributionLimit weightLimit massLimit : Cell -> Real)
    (hunit_card : (Fintype.card Unit : Real) = sampleSize)
    (hdraw_card : (Fintype.card Draw : Real) = sampleSize)
    (hsampleSize_ne : sampleSize ≠ 0)
    (hbase_denominator :
      ∀ᶠ index in atTop,
        baseLinearizedSum (Finset.univ : Finset Unit)
          (weight index) = denominator)
    (hdenominator_ne : denominator ≠ 0)
    (htarget_hajek :
      ∀ᶠ index in atTop,
        target =
          baseLinearizedSum (Finset.univ : Finset Unit)
            (contribution index) / denominator)
    (hcover_all :
      ∀ᶠ index in atTop,
        ∀ unit, score index unit ∈ cells)
    (hcontributionCell_all :
      ∀ᶠ index in atTop,
        ∀ unit,
          cellContribution index (score index unit) =
            contribution index unit)
    (hweightCell_all :
      ∀ᶠ index in atTop,
        ∀ unit,
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
          weightedSampleSum ((fun _index : ℕ =>
              (Finset.univ : Finset Unit)) sampleSize)
            ((fun _index _unit => 1) sampleSize)
            (scoreCellIndicator (score sampleSize) cell)))
    (scoreUnitComponent : ℕ -> Unit -> ScoreComponent -> Real)
    (biasUnitComponent : ℕ -> Unit -> BiasComponent -> Real)
    (hscore_unit_tendsto :
      ∀ unit,
        ∀ component, component ∈ scoreComponents ->
          Tendsto (fun index => scoreUnitComponent index unit component)
            atTop (nhds 0))
    (hbias_unit_tendsto :
      ∀ unit,
        ∀ component, component ∈ biasComponents ->
          Tendsto (fun index => biasUnitComponent index unit component)
            atTop (nhds 0)) :
    Tendsto
      (fun index =>
        (1 / denominator ^ 2) * (1 / normalizer) *
            multiplierPerturbationSecondMoment
              (uniformAssignmentSupport Unit Draw)
              (uniformAssignmentMass Unit Draw)
              (Finset.univ : Finset Unit)
              (fun assignment unit =>
                multinomialCountFromDrawIndicators
                  (Finset.univ : Finset Draw)
                  (fun assignment draw unit =>
                    oneHotAssignmentIndicator assignment draw unit)
                  assignment unit)
              (fun unit =>
                contribution index unit - target * weight index unit) +
          (∑ component ∈ scoreComponents,
            (replicatedLinearizedSum (Finset.univ : Finset Unit)
                (fun unit =>
                  multinomialCountFromDrawIndicators
                    (Finset.univ : Finset Draw)
                    (fun assignment draw unit =>
                      oneHotAssignmentIndicator assignment draw unit)
                    (assignment index) unit)
                (fun unit => scoreUnitComponent index unit component) -
              baseLinearizedSum (Finset.univ : Finset Unit)
                (fun unit => scoreUnitComponent index unit component))) +
          (∑ component ∈ biasComponents,
            (replicatedLinearizedSum (Finset.univ : Finset Unit)
                (fun unit =>
                  multinomialCountFromDrawIndicators
                    (Finset.univ : Finset Draw)
                    (fun assignment draw unit =>
                      oneHotAssignmentIndicator assignment draw unit)
                    (assignment index) unit)
              (fun unit => biasUnitComponent index unit component) -
              baseLinearizedSum (Finset.univ : Finset Unit)
                (fun unit => biasUnitComponent index unit component))))
      atTop
      (nhds
        ((1 / denominator ^ 2) * (1 / normalizer) *
          weightedScoreCellMomentLimit cells
            (fun cell =>
              (contributionLimit cell - target * weightLimit cell) ^ 2)
            massLimit)) :=
  tendsto_concreteUniformAssignmentBootstrapVariance_of_eventually_cell_contribution_weight_limits_and_hajek_target_denominator_univ_support_replicatedLinearized_errors
    (l := atTop) cells scoreComponents biasComponents assignment score
    contribution weight target denominator normalizer sampleSize
    cellContribution cellWeight contributionLimit weightLimit massLimit
    hunit_card hdraw_card hsampleSize_ne hbase_denominator
    hdenominator_ne htarget_hajek hcover_all hcontributionCell_all
    hweightCell_all hcontributionLimit hweightLimit
    (cellwise_mass_lln_of_glivenkoCantelli_bridge
      cells massLimit (fun _index : ℕ => (Finset.univ : Finset Unit))
      (fun _index _unit => 1) score
      (weighted_indicator_array_lln_of_vdvw241_endpoint_assembly
        cells massLimit
        (fun _index : ℕ => (Finset.univ : Finset Unit))
        (fun _index _unit => 1) score assembly))
    scoreUnitComponent biasUnitComponent hscore_unit_tendsto
    hbias_unit_tendsto

/--
Concrete full-support uniform route with the score-replication and
bias-correction errors specialized to their literal one-hot multinomial
finite-component sums.
-/
theorem tendsto_concreteUniformAssignmentBootstrapVariance_of_eventually_cell_contribution_weight_limits_and_hajek_base_ratio_univ_support_unit_component_tendsto_concrete_error_sums
    [Fintype Unit] [Fintype Draw] [DecidableEq Unit] [DecidableEq Draw]
    [Nonempty Unit] [DecidableEq Cell] [DecidableEq ScoreComponent]
    [DecidableEq BiasComponent]
    (cells : Finset Cell)
    (scoreComponents : Finset ScoreComponent)
    (biasComponents : Finset BiasComponent)
    (assignment : Index -> Draw -> Unit)
    (score : Index -> Unit -> Cell)
    (contribution weight : Index -> Unit -> Real)
    (target denominator normalizer sampleSize : Real)
    (cellContribution cellWeight : Index -> Cell -> Real)
    (contributionLimit weightLimit massLimit : Cell -> Real)
    (scoreUnitComponent : Index -> Unit -> ScoreComponent -> Real)
    (biasUnitComponent : Index -> Unit -> BiasComponent -> Real)
    (hunit_card : (Fintype.card Unit : Real) = sampleSize)
    (hdraw_card : (Fintype.card Draw : Real) = sampleSize)
    (hsampleSize_ne : sampleSize ≠ 0)
    (hbase_den_ne :
      ∀ᶠ index in l,
        baseLinearizedSum (Finset.univ : Finset Unit)
          (weight index) ≠ 0)
    (hbase_ratio :
      ∀ᶠ index in l,
        baseLinearizedSum (Finset.univ : Finset Unit)
            (contribution index) /
          baseLinearizedSum (Finset.univ : Finset Unit)
            (weight index) =
          target)
    (hcover_all :
      ∀ᶠ index in l,
        ∀ unit, score index unit ∈ cells)
    (hcontributionCell_all :
      ∀ᶠ index in l,
        ∀ unit,
          cellContribution index (score index unit) =
            contribution index unit)
    (hweightCell_all :
      ∀ᶠ index in l,
        ∀ unit,
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
      cellwiseScoreCellMassLLN (l := l) cells
        (fun _index => (Finset.univ : Finset Unit))
        (fun _index _unit => 1) score massLimit)
    (hscore_unit_tendsto :
      ∀ unit,
        ∀ component, component ∈ scoreComponents ->
          Tendsto (fun index => scoreUnitComponent index unit component)
            l (nhds 0))
    (hbias_unit_tendsto :
      ∀ unit,
        ∀ component, component ∈ biasComponents ->
          Tendsto (fun index => biasUnitComponent index unit component)
            l (nhds 0)) :
    Tendsto
      (fun index =>
        (1 / denominator ^ 2) * (1 / normalizer) *
            multiplierPerturbationSecondMoment
              (uniformAssignmentSupport Unit Draw)
              (uniformAssignmentMass Unit Draw)
              (Finset.univ : Finset Unit)
              (fun assignment unit =>
                multinomialCountFromDrawIndicators
                  (Finset.univ : Finset Draw)
                  (fun assignment draw unit =>
                    oneHotAssignmentIndicator assignment draw unit)
                  assignment unit)
              (fun unit =>
                contribution index unit - target * weight index unit) +
          concreteOneHotUnitComponentError scoreComponents assignment
            scoreUnitComponent index +
          concreteOneHotUnitComponentError biasComponents assignment
            biasUnitComponent index)
      l
      (nhds
        ((1 / denominator ^ 2) * (1 / normalizer) *
          weightedScoreCellMomentLimit cells
            (fun cell =>
              (contributionLimit cell - target * weightLimit cell) ^ 2)
            massLimit)) :=
  tendsto_concreteUniformAssignmentBootstrapVariance_of_eventually_cell_contribution_weight_limits_and_hajek_base_ratio_univ_support_unit_component_tendsto_bounds
    (l := l) cells scoreComponents biasComponents assignment score
    contribution weight target denominator normalizer sampleSize
    cellContribution cellWeight contributionLimit weightLimit massLimit
    (fun index =>
      concreteOneHotUnitComponentError scoreComponents assignment
        scoreUnitComponent index)
    (fun index =>
      concreteOneHotUnitComponentError biasComponents assignment
        biasUnitComponent index)
    scoreUnitComponent biasUnitComponent hunit_card hdraw_card
    hsampleSize_ne hbase_den_ne hbase_ratio hcover_all
    hcontributionCell_all hweightCell_all hcontributionLimit
    hweightLimit hmass
    (Filter.Eventually.of_forall
      (fun index => by
        simp [concreteOneHotUnitComponentError]))
    hscore_unit_tendsto
    (Filter.Eventually.of_forall
      (fun index => by
        simp [concreteOneHotUnitComponentError]))
    hbias_unit_tendsto

/--
Finite `L1(P)` bracketing version of the concrete full-support route whose
score and bias errors are the literal one-hot multinomial finite-component
sums.
-/
theorem tendsto_concreteUniformAssignmentBootstrapVariance_of_eventually_cell_contribution_weight_limits_l1BracketingNumber_obligations_and_hajek_base_ratio_univ_support_unit_component_tendsto_concrete_error_sums
    [Fintype Unit] [Fintype Draw] [DecidableEq Unit] [DecidableEq Draw]
    [Nonempty Unit] [DecidableEq Cell] [DecidableEq ScoreComponent]
    [DecidableEq BiasComponent]
    {Bracket : Type*} [Fintype Bracket]
    (cells : Finset Cell)
    (scoreComponents : Finset ScoreComponent)
    (biasComponents : Finset BiasComponent)
    (assignment : ℕ -> Draw -> Unit)
    (score : ℕ -> Unit -> Cell)
    (contribution weight : ℕ -> Unit -> Real)
    (target denominator normalizer sampleSize : Real)
    (cellContribution cellWeight : ℕ -> Cell -> Real)
    (contributionLimit weightLimit massLimit : Cell -> Real)
    (scoreUnitComponent : ℕ -> Unit -> ScoreComponent -> Real)
    (biasUnitComponent : ℕ -> Unit -> BiasComponent -> Real)
    (hunit_card : (Fintype.card Unit : Real) = sampleSize)
    (hdraw_card : (Fintype.card Draw : Real) = sampleSize)
    (hsampleSize_ne : sampleSize ≠ 0)
    (hbase_den_ne :
      ∀ᶠ index in atTop,
        baseLinearizedSum (Finset.univ : Finset Unit)
          (weight index) ≠ 0)
    (hbase_ratio :
      ∀ᶠ index in atTop,
        baseLinearizedSum (Finset.univ : Finset Unit)
            (contribution index) /
          baseLinearizedSum (Finset.univ : Finset Unit)
            (weight index) =
          target)
    (hcover_all :
      ∀ᶠ index in atTop,
        ∀ unit, score index unit ∈ cells)
    (hcontributionCell_all :
      ∀ᶠ index in atTop,
        ∀ unit,
          cellContribution index (score index unit) =
            contribution index unit)
    (hweightCell_all :
      ∀ᶠ index in atTop,
        ∀ unit,
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
          weightedSampleSum ((fun _index : ℕ =>
              (Finset.univ : Finset Unit)) sampleSize)
            ((fun _index _unit => 1) sampleSize)
            (scoreCellIndicator (score sampleSize) cell)))
    (hscore_unit_tendsto :
      ∀ unit,
        ∀ component, component ∈ scoreComponents ->
          Tendsto (fun index => scoreUnitComponent index unit component)
            atTop (nhds 0))
    (hbias_unit_tendsto :
      ∀ unit,
        ∀ component, component ∈ biasComponents ->
          Tendsto (fun index => biasUnitComponent index unit component)
            atTop (nhds 0)) :
    Tendsto
      (fun index =>
        (1 / denominator ^ 2) * (1 / normalizer) *
            multiplierPerturbationSecondMoment
              (uniformAssignmentSupport Unit Draw)
              (uniformAssignmentMass Unit Draw)
              (Finset.univ : Finset Unit)
              (fun assignment unit =>
                multinomialCountFromDrawIndicators
                  (Finset.univ : Finset Draw)
                  (fun assignment draw unit =>
                    oneHotAssignmentIndicator assignment draw unit)
                  assignment unit)
              (fun unit =>
                contribution index unit - target * weight index unit) +
          concreteOneHotUnitComponentError scoreComponents assignment
            scoreUnitComponent index +
          concreteOneHotUnitComponentError biasComponents assignment
            biasUnitComponent index)
      atTop
      (nhds
        ((1 / denominator ^ 2) * (1 / normalizer) *
          weightedScoreCellMomentLimit cells
            (fun cell =>
              (contributionLimit cell - target * weightLimit cell) ^ 2)
            massLimit)) :=
  tendsto_concreteUniformAssignmentBootstrapVariance_of_eventually_cell_contribution_weight_limits_and_hajek_base_ratio_univ_support_unit_component_tendsto_concrete_error_sums
    (l := atTop) cells scoreComponents biasComponents assignment score
    contribution weight target denominator normalizer sampleSize
    cellContribution cellWeight contributionLimit weightLimit massLimit
    scoreUnitComponent biasUnitComponent hunit_card hdraw_card
    hsampleSize_ne hbase_den_ne hbase_ratio hcover_all
    hcontributionCell_all hweightCell_all hcontributionLimit
    hweightLimit
    (cellwise_mass_lln_of_glivenkoCantelli_bridge
      cells massLimit (fun _index : ℕ => (Finset.univ : Finset Unit))
      (fun _index _unit => 1) score
      (weighted_indicator_array_lln_of_l1BracketingNumber_obligations
        cells massLimit
        (fun _index : ℕ => (Finset.univ : Finset Unit))
        (fun _index _unit => 1) score obligations))
    hscore_unit_tendsto hbias_unit_tendsto

/--
VdV&W endpoint-assembly version of the concrete full-support route whose
score and bias errors are the literal one-hot multinomial finite-component
sums.
-/
theorem tendsto_concreteUniformAssignmentBootstrapVariance_of_eventually_cell_contribution_weight_limits_vdvw241_endpoint_assembly_and_hajek_base_ratio_univ_support_unit_component_tendsto_concrete_error_sums
    [Fintype Unit] [Fintype Draw] [DecidableEq Unit] [DecidableEq Draw]
    [Nonempty Unit] [DecidableEq Cell] [DecidableEq ScoreComponent]
    [DecidableEq BiasComponent]
    {Bracket : Type*} [Fintype Bracket]
    (cells : Finset Cell)
    (scoreComponents : Finset ScoreComponent)
    (biasComponents : Finset BiasComponent)
    (assignment : ℕ -> Draw -> Unit)
    (score : ℕ -> Unit -> Cell)
    (contribution weight : ℕ -> Unit -> Real)
    (target denominator normalizer sampleSize : Real)
    (cellContribution cellWeight : ℕ -> Cell -> Real)
    (contributionLimit weightLimit massLimit : Cell -> Real)
    (scoreUnitComponent : ℕ -> Unit -> ScoreComponent -> Real)
    (biasUnitComponent : ℕ -> Unit -> BiasComponent -> Real)
    (hunit_card : (Fintype.card Unit : Real) = sampleSize)
    (hdraw_card : (Fintype.card Draw : Real) = sampleSize)
    (hsampleSize_ne : sampleSize ≠ 0)
    (hbase_den_ne :
      ∀ᶠ index in atTop,
        baseLinearizedSum (Finset.univ : Finset Unit)
          (weight index) ≠ 0)
    (hbase_ratio :
      ∀ᶠ index in atTop,
        baseLinearizedSum (Finset.univ : Finset Unit)
            (contribution index) /
          baseLinearizedSum (Finset.univ : Finset Unit)
            (weight index) =
          target)
    (hcover_all :
      ∀ᶠ index in atTop,
        ∀ unit, score index unit ∈ cells)
    (hcontributionCell_all :
      ∀ᶠ index in atTop,
        ∀ unit,
          cellContribution index (score index unit) =
            contribution index unit)
    (hweightCell_all :
      ∀ᶠ index in atTop,
        ∀ unit,
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
          weightedSampleSum ((fun _index : ℕ =>
              (Finset.univ : Finset Unit)) sampleSize)
            ((fun _index _unit => 1) sampleSize)
            (scoreCellIndicator (score sampleSize) cell)))
    (hscore_unit_tendsto :
      ∀ unit,
        ∀ component, component ∈ scoreComponents ->
          Tendsto (fun index => scoreUnitComponent index unit component)
            atTop (nhds 0))
    (hbias_unit_tendsto :
      ∀ unit,
        ∀ component, component ∈ biasComponents ->
          Tendsto (fun index => biasUnitComponent index unit component)
            atTop (nhds 0)) :
    Tendsto
      (fun index =>
        (1 / denominator ^ 2) * (1 / normalizer) *
            multiplierPerturbationSecondMoment
              (uniformAssignmentSupport Unit Draw)
              (uniformAssignmentMass Unit Draw)
              (Finset.univ : Finset Unit)
              (fun assignment unit =>
                multinomialCountFromDrawIndicators
                  (Finset.univ : Finset Draw)
                  (fun assignment draw unit =>
                    oneHotAssignmentIndicator assignment draw unit)
                  assignment unit)
              (fun unit =>
                contribution index unit - target * weight index unit) +
          concreteOneHotUnitComponentError scoreComponents assignment
            scoreUnitComponent index +
          concreteOneHotUnitComponentError biasComponents assignment
            biasUnitComponent index)
      atTop
      (nhds
        ((1 / denominator ^ 2) * (1 / normalizer) *
          weightedScoreCellMomentLimit cells
            (fun cell =>
              (contributionLimit cell - target * weightLimit cell) ^ 2)
            massLimit)) :=
  tendsto_concreteUniformAssignmentBootstrapVariance_of_eventually_cell_contribution_weight_limits_and_hajek_base_ratio_univ_support_unit_component_tendsto_concrete_error_sums
    (l := atTop) cells scoreComponents biasComponents assignment score
    contribution weight target denominator normalizer sampleSize
    cellContribution cellWeight contributionLimit weightLimit massLimit
    scoreUnitComponent biasUnitComponent hunit_card hdraw_card
    hsampleSize_ne hbase_den_ne hbase_ratio hcover_all
    hcontributionCell_all hweightCell_all hcontributionLimit
    hweightLimit
    (cellwise_mass_lln_of_glivenkoCantelli_bridge
      cells massLimit (fun _index : ℕ => (Finset.univ : Finset Unit))
      (fun _index _unit => 1) score
      (weighted_indicator_array_lln_of_vdvw241_endpoint_assembly
        cells massLimit
        (fun _index : ℕ => (Finset.univ : Finset Unit))
        (fun _index _unit => 1) score assembly))
    hscore_unit_tendsto hbias_unit_tendsto

/--
Finite `L1(P)` bracketing version of the concrete finite-expectation
full-support uniform route.  The actual variance sequence is the normalized
one-hot multiplier second moment plus the two finite errors.
-/
theorem tendsto_concreteUniformAssignmentBootstrapVariance_of_eventually_cell_contribution_weight_limits_l1BracketingNumber_obligations_and_hajek_base_ratio_univ_support_all_unit_error_bounds
    [Fintype Unit] [Fintype Draw] [DecidableEq Unit] [DecidableEq Draw]
    [Nonempty Unit] [DecidableEq Cell] [DecidableEq ScoreComponent]
    [DecidableEq BiasComponent]
    {Bracket : Type*} [Fintype Bracket]
    (cells : Finset Cell)
    (scoreComponents : Finset ScoreComponent)
    (biasComponents : Finset BiasComponent)
    (assignment : ℕ -> Draw -> Unit)
    (score : ℕ -> Unit -> Cell)
    (contribution weight : ℕ -> Unit -> Real)
    (target denominator normalizer sampleSize : Real)
    (cellContribution cellWeight : ℕ -> Cell -> Real)
    (contributionLimit weightLimit massLimit : Cell -> Real)
    (scoreReplicationError biasCorrectionError : ℕ -> Real)
    (scoreUnitComponent : ℕ -> Unit -> ScoreComponent -> Real)
    (biasUnitComponent : ℕ -> Unit -> BiasComponent -> Real)
    (scoreUnitEnvelope : ℕ -> ScoreComponent -> Real)
    (biasUnitEnvelope : ℕ -> BiasComponent -> Real)
    (hunit_card : (Fintype.card Unit : Real) = sampleSize)
    (hdraw_card : (Fintype.card Draw : Real) = sampleSize)
    (hsampleSize_ne : sampleSize ≠ 0)
    (hbase_den_ne :
      ∀ᶠ index in atTop,
        baseLinearizedSum (Finset.univ : Finset Unit)
          (weight index) ≠ 0)
    (hbase_ratio :
      ∀ᶠ index in atTop,
        baseLinearizedSum (Finset.univ : Finset Unit)
            (contribution index) /
          baseLinearizedSum (Finset.univ : Finset Unit)
            (weight index) =
          target)
    (hcover_all :
      ∀ᶠ index in atTop,
        ∀ unit, score index unit ∈ cells)
    (hcontributionCell_all :
      ∀ᶠ index in atTop,
        ∀ unit,
          cellContribution index (score index unit) =
            contribution index unit)
    (hweightCell_all :
      ∀ᶠ index in atTop,
        ∀ unit,
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
          weightedSampleSum ((fun _index : ℕ =>
              (Finset.univ : Finset Unit)) sampleSize)
            ((fun _index _unit => 1) sampleSize)
            (scoreCellIndicator (score sampleSize) cell)))
    (hscore_construct_univ :
      scoreReplicationError =ᶠ[atTop]
        (fun index =>
          ∑ component ∈ scoreComponents, ∑ unit : Unit,
            (multinomialCountFromDrawIndicators (Finset.univ : Finset Draw)
                (fun assignment draw unit =>
                  oneHotAssignmentIndicator assignment draw unit)
                (assignment index) unit - 1) *
              scoreUnitComponent index unit component))
    (hscore_component_bound_all :
      ∀ᶠ index in atTop,
        ∀ unit,
          ∀ component, component ∈ scoreComponents ->
            |scoreUnitComponent index unit component| ≤
              scoreUnitEnvelope index component)
    (hscore_envelope_tendsto :
      ∀ component, component ∈ scoreComponents ->
        Tendsto (fun index => scoreUnitEnvelope index component)
          atTop (nhds 0))
    (hbias_construct_univ :
      biasCorrectionError =ᶠ[atTop]
        (fun index =>
          ∑ component ∈ biasComponents, ∑ unit : Unit,
            (multinomialCountFromDrawIndicators (Finset.univ : Finset Draw)
                (fun assignment draw unit =>
                  oneHotAssignmentIndicator assignment draw unit)
                (assignment index) unit - 1) *
              biasUnitComponent index unit component))
    (hbias_component_bound_all :
      ∀ᶠ index in atTop,
        ∀ unit,
          ∀ component, component ∈ biasComponents ->
            |biasUnitComponent index unit component| ≤
              biasUnitEnvelope index component)
    (hbias_envelope_tendsto :
      ∀ component, component ∈ biasComponents ->
        Tendsto (fun index => biasUnitEnvelope index component)
          atTop (nhds 0)) :
    Tendsto
      (fun index =>
        (1 / denominator ^ 2) * (1 / normalizer) *
            multiplierPerturbationSecondMoment
              (uniformAssignmentSupport Unit Draw)
              (uniformAssignmentMass Unit Draw)
              (Finset.univ : Finset Unit)
              (fun assignment unit =>
                multinomialCountFromDrawIndicators
                  (Finset.univ : Finset Draw)
                  (fun assignment draw unit =>
                    oneHotAssignmentIndicator assignment draw unit)
                  assignment unit)
              (fun unit =>
                contribution index unit - target * weight index unit) +
          scoreReplicationError index + biasCorrectionError index)
      atTop
      (nhds
        ((1 / denominator ^ 2) * (1 / normalizer) *
          weightedScoreCellMomentLimit cells
            (fun cell =>
              (contributionLimit cell - target * weightLimit cell) ^ 2)
            massLimit)) :=
  tendsto_concreteUniformAssignmentBootstrapVariance_of_eventually_cell_contribution_weight_limits_and_hajek_base_ratio_univ_support_all_unit_error_bounds
    (l := atTop) cells scoreComponents biasComponents assignment score
    contribution weight target denominator normalizer sampleSize
    cellContribution cellWeight contributionLimit weightLimit massLimit
    scoreReplicationError biasCorrectionError scoreUnitComponent
    biasUnitComponent scoreUnitEnvelope biasUnitEnvelope hunit_card
    hdraw_card hsampleSize_ne hbase_den_ne hbase_ratio hcover_all
    hcontributionCell_all hweightCell_all hcontributionLimit hweightLimit
    (cellwise_mass_lln_of_glivenkoCantelli_bridge
      cells massLimit (fun _index : ℕ => (Finset.univ : Finset Unit))
      (fun _index _unit => 1) score
      (weighted_indicator_array_lln_of_l1BracketingNumber_obligations
        cells massLimit
        (fun _index : ℕ => (Finset.univ : Finset Unit))
        (fun _index _unit => 1) score obligations))
    hscore_construct_univ hscore_component_bound_all
    hscore_envelope_tendsto hbias_construct_univ
    hbias_component_bound_all hbias_envelope_tendsto

/--
VdV&W endpoint-assembly version of the concrete finite-expectation
full-support uniform route.  The actual variance sequence is the normalized
one-hot multiplier second moment plus the two finite errors.
-/
theorem tendsto_concreteUniformAssignmentBootstrapVariance_of_eventually_cell_contribution_weight_limits_vdvw241_endpoint_assembly_and_hajek_base_ratio_univ_support_all_unit_error_bounds
    [Fintype Unit] [Fintype Draw] [DecidableEq Unit] [DecidableEq Draw]
    [Nonempty Unit] [DecidableEq Cell] [DecidableEq ScoreComponent]
    [DecidableEq BiasComponent]
    {Bracket : Type*} [Fintype Bracket]
    (cells : Finset Cell)
    (scoreComponents : Finset ScoreComponent)
    (biasComponents : Finset BiasComponent)
    (assignment : ℕ -> Draw -> Unit)
    (score : ℕ -> Unit -> Cell)
    (contribution weight : ℕ -> Unit -> Real)
    (target denominator normalizer sampleSize : Real)
    (cellContribution cellWeight : ℕ -> Cell -> Real)
    (contributionLimit weightLimit massLimit : Cell -> Real)
    (scoreReplicationError biasCorrectionError : ℕ -> Real)
    (scoreUnitComponent : ℕ -> Unit -> ScoreComponent -> Real)
    (biasUnitComponent : ℕ -> Unit -> BiasComponent -> Real)
    (scoreUnitEnvelope : ℕ -> ScoreComponent -> Real)
    (biasUnitEnvelope : ℕ -> BiasComponent -> Real)
    (hunit_card : (Fintype.card Unit : Real) = sampleSize)
    (hdraw_card : (Fintype.card Draw : Real) = sampleSize)
    (hsampleSize_ne : sampleSize ≠ 0)
    (hbase_den_ne :
      ∀ᶠ index in atTop,
        baseLinearizedSum (Finset.univ : Finset Unit)
          (weight index) ≠ 0)
    (hbase_ratio :
      ∀ᶠ index in atTop,
        baseLinearizedSum (Finset.univ : Finset Unit)
            (contribution index) /
          baseLinearizedSum (Finset.univ : Finset Unit)
            (weight index) =
          target)
    (hcover_all :
      ∀ᶠ index in atTop,
        ∀ unit, score index unit ∈ cells)
    (hcontributionCell_all :
      ∀ᶠ index in atTop,
        ∀ unit,
          cellContribution index (score index unit) =
            contribution index unit)
    (hweightCell_all :
      ∀ᶠ index in atTop,
        ∀ unit,
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
          weightedSampleSum ((fun _index : ℕ =>
              (Finset.univ : Finset Unit)) sampleSize)
            ((fun _index _unit => 1) sampleSize)
            (scoreCellIndicator (score sampleSize) cell)))
    (hscore_construct_univ :
      scoreReplicationError =ᶠ[atTop]
        (fun index =>
          ∑ component ∈ scoreComponents, ∑ unit : Unit,
            (multinomialCountFromDrawIndicators (Finset.univ : Finset Draw)
                (fun assignment draw unit =>
                  oneHotAssignmentIndicator assignment draw unit)
                (assignment index) unit - 1) *
              scoreUnitComponent index unit component))
    (hscore_component_bound_all :
      ∀ᶠ index in atTop,
        ∀ unit,
          ∀ component, component ∈ scoreComponents ->
            |scoreUnitComponent index unit component| ≤
              scoreUnitEnvelope index component)
    (hscore_envelope_tendsto :
      ∀ component, component ∈ scoreComponents ->
        Tendsto (fun index => scoreUnitEnvelope index component)
          atTop (nhds 0))
    (hbias_construct_univ :
      biasCorrectionError =ᶠ[atTop]
        (fun index =>
          ∑ component ∈ biasComponents, ∑ unit : Unit,
            (multinomialCountFromDrawIndicators (Finset.univ : Finset Draw)
                (fun assignment draw unit =>
                  oneHotAssignmentIndicator assignment draw unit)
                (assignment index) unit - 1) *
              biasUnitComponent index unit component))
    (hbias_component_bound_all :
      ∀ᶠ index in atTop,
        ∀ unit,
          ∀ component, component ∈ biasComponents ->
            |biasUnitComponent index unit component| ≤
              biasUnitEnvelope index component)
    (hbias_envelope_tendsto :
      ∀ component, component ∈ biasComponents ->
        Tendsto (fun index => biasUnitEnvelope index component)
          atTop (nhds 0)) :
    Tendsto
      (fun index =>
        (1 / denominator ^ 2) * (1 / normalizer) *
            multiplierPerturbationSecondMoment
              (uniformAssignmentSupport Unit Draw)
              (uniformAssignmentMass Unit Draw)
              (Finset.univ : Finset Unit)
              (fun assignment unit =>
                multinomialCountFromDrawIndicators
                  (Finset.univ : Finset Draw)
                  (fun assignment draw unit =>
                    oneHotAssignmentIndicator assignment draw unit)
                  assignment unit)
              (fun unit =>
                contribution index unit - target * weight index unit) +
          scoreReplicationError index + biasCorrectionError index)
      atTop
      (nhds
        ((1 / denominator ^ 2) * (1 / normalizer) *
          weightedScoreCellMomentLimit cells
            (fun cell =>
              (contributionLimit cell - target * weightLimit cell) ^ 2)
            massLimit)) :=
  tendsto_concreteUniformAssignmentBootstrapVariance_of_eventually_cell_contribution_weight_limits_and_hajek_base_ratio_univ_support_all_unit_error_bounds
    (l := atTop) cells scoreComponents biasComponents assignment score
    contribution weight target denominator normalizer sampleSize
    cellContribution cellWeight contributionLimit weightLimit massLimit
    scoreReplicationError biasCorrectionError scoreUnitComponent
    biasUnitComponent scoreUnitEnvelope biasUnitEnvelope hunit_card
    hdraw_card hsampleSize_ne hbase_den_ne hbase_ratio hcover_all
    hcontributionCell_all hweightCell_all hcontributionLimit hweightLimit
    (cellwise_mass_lln_of_glivenkoCantelli_bridge
      cells massLimit (fun _index : ℕ => (Finset.univ : Finset Unit))
      (fun _index _unit => 1) score
      (weighted_indicator_array_lln_of_vdvw241_endpoint_assembly
        cells massLimit
        (fun _index : ℕ => (Finset.univ : Finset Unit))
        (fun _index _unit => 1) score assembly))
    hscore_construct_univ hscore_component_bound_all
    hscore_envelope_tendsto hbias_construct_univ
    hbias_component_bound_all hbias_envelope_tendsto

/--
Actual bootstrap variance convergence when score-replication has a concrete
finite score-cell-by-component decomposition, while bias-correction uses the
existing finite component error-bound route.

This removes the abstract score-replication negligibility input by reindexing
the score-cell double sum as product components and then feeding the existing
finite-error actual-bootstrap adapter.
-/
theorem tendsto_actualBootstrapVariance_of_eventually_cell_contribution_weight_limits_and_finite_score_cell_score_error_bounds
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
      Index -> Cell -> ScoreComponent -> Real)
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
              scoreErrorComponentBound index cell component)
    (hscore_component_bound_tendsto :
      ∀ cell, cell ∈ cells ->
        ∀ component, component ∈ scoreComponents ->
          Tendsto
            (fun index => scoreErrorComponentBound index cell component)
            l (nhds 0))
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
            massLimit)) := by
  have hscore_decomp_product :
      scoreReplicationError =ᶠ[l]
        (fun index => ∑ pair ∈ cells.product scoreComponents,
          scoreErrorComponent index pair.1 pair.2) := by
    filter_upwards [hscore_decomp] with index hdecomp_index
    calc
      scoreReplicationError index =
          ∑ cell ∈ cells, ∑ component ∈ scoreComponents,
            scoreErrorComponent index cell component := hdecomp_index
      _ = ∑ pair ∈ cells.product scoreComponents,
            scoreErrorComponent index pair.1 pair.2 := by
          rw [← Finset.sum_product']
          rfl
  have hscore_component_bound_product :
      ∀ᶠ index in l,
        ∀ pair, pair ∈ cells.product scoreComponents ->
          |scoreErrorComponent index pair.1 pair.2| ≤
            scoreErrorComponentBound index pair.1 pair.2 := by
    filter_upwards [hscore_component_bound] with index hbound pair hpair
    rcases Finset.mem_product.mp hpair with ⟨hcell, hcomponent⟩
    exact hbound pair.1 hcell pair.2 hcomponent
  exact
    tendsto_actualBootstrapVariance_of_eventually_cell_contribution_weight_limits_and_finite_error_bounds
      (l := l) cells (cells.product scoreComponents) biasComponents
      sample score contribution weight target denominator normalizer
      cellContribution cellWeight contributionLimit weightLimit massLimit
      actualVariance scoreReplicationError biasCorrectionError
      (fun index pair => scoreErrorComponent index pair.1 pair.2)
      (fun index pair => scoreErrorComponentBound index pair.1 pair.2)
      biasErrorComponent biasErrorComponentBound herror_decomp hcover
      hcontributionCell hweightCell hcontributionLimit hweightLimit hmass
      hscore_decomp_product hscore_component_bound_product
      (fun pair hpair => by
        rcases Finset.mem_product.mp hpair with ⟨hcell, hcomponent⟩
        exact hscore_component_bound_tendsto pair.1 hcell pair.2 hcomponent)
      hbias_decomp hbias_component_bound hbias_component_bound_tendsto

/--
Actual bootstrap variance convergence when bias-correction has a concrete
finite score-cell-by-component decomposition, while score-replication uses the
existing finite component error-bound route.

This removes the abstract bias-correction negligibility input by reindexing
the bias score-cell double sum as product components and then feeding the
existing finite-error actual-bootstrap adapter.
-/
theorem tendsto_actualBootstrapVariance_of_eventually_cell_contribution_weight_limits_and_finite_score_cell_bias_error_bounds
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
    (biasErrorComponent biasErrorComponentBound :
      Index -> Cell -> BiasComponent -> Real)
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
              biasErrorComponentBound index cell component)
    (hbias_component_bound_tendsto :
      ∀ cell, cell ∈ cells ->
        ∀ component, component ∈ biasComponents ->
          Tendsto
            (fun index => biasErrorComponentBound index cell component)
            l (nhds 0)) :
    Tendsto actualVariance l
      (nhds
        ((1 / denominator ^ 2) * (1 / normalizer) *
          weightedScoreCellMomentLimit cells
            (fun cell =>
              (contributionLimit cell - target * weightLimit cell) ^ 2)
            massLimit)) := by
  have hbias_decomp_product :
      biasCorrectionError =ᶠ[l]
        (fun index => ∑ pair ∈ cells.product biasComponents,
          biasErrorComponent index pair.1 pair.2) := by
    filter_upwards [hbias_decomp] with index hdecomp_index
    calc
      biasCorrectionError index =
          ∑ cell ∈ cells, ∑ component ∈ biasComponents,
            biasErrorComponent index cell component := hdecomp_index
      _ = ∑ pair ∈ cells.product biasComponents,
            biasErrorComponent index pair.1 pair.2 := by
          rw [← Finset.sum_product']
          rfl
  have hbias_component_bound_product :
      ∀ᶠ index in l,
        ∀ pair, pair ∈ cells.product biasComponents ->
          |biasErrorComponent index pair.1 pair.2| ≤
            biasErrorComponentBound index pair.1 pair.2 := by
    filter_upwards [hbias_component_bound] with index hbound pair hpair
    rcases Finset.mem_product.mp hpair with ⟨hcell, hcomponent⟩
    exact hbound pair.1 hcell pair.2 hcomponent
  exact
    tendsto_actualBootstrapVariance_of_eventually_cell_contribution_weight_limits_and_finite_error_bounds
      (l := l) cells scoreComponents (cells.product biasComponents)
      sample score contribution weight target denominator normalizer
      cellContribution cellWeight contributionLimit weightLimit massLimit
      actualVariance scoreReplicationError biasCorrectionError
      scoreErrorComponent scoreErrorComponentBound
      (fun index pair => biasErrorComponent index pair.1 pair.2)
      (fun index pair => biasErrorComponentBound index pair.1 pair.2)
      herror_decomp hcover hcontributionCell hweightCell hcontributionLimit
      hweightLimit hmass hscore_decomp hscore_component_bound
      hscore_component_bound_tendsto hbias_decomp_product
      hbias_component_bound_product
      (fun pair hpair => by
        rcases Finset.mem_product.mp hpair with ⟨hcell, hcomponent⟩
        exact hbias_component_bound_tendsto pair.1 hcell pair.2 hcomponent)

/--
Finite `L1(P)` bracketing supplies the score-cell mass LLN, and finite
component error bounds supply score-replication and bias-correction
negligibility, for the eventual contribution/weight-limit actual bootstrap
variance route.
-/
theorem
    tendsto_actualBootstrapVariance_of_eventually_cell_contribution_weight_limits_l1BracketingNumber_obligations_and_finite_error_bounds
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
    (scoreErrorComponent scoreErrorComponentBound :
      ℕ -> ScoreComponent -> Real)
    (biasErrorComponent biasErrorComponentBound :
      ℕ -> BiasComponent -> Real)
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
            scoreErrorComponentBound index component)
    (hscore_component_bound_tendsto :
      ∀ component, component ∈ scoreComponents ->
        Tendsto (fun index => scoreErrorComponentBound index component)
          atTop (nhds 0))
    (hbias_decomp :
      biasCorrectionError =ᶠ[atTop]
        (fun index => ∑ component ∈ biasComponents,
          biasErrorComponent index component))
    (hbias_component_bound :
      ∀ᶠ index in atTop,
        ∀ component, component ∈ biasComponents ->
          |biasErrorComponent index component| ≤
            biasErrorComponentBound index component)
    (hbias_component_bound_tendsto :
      ∀ component, component ∈ biasComponents ->
        Tendsto (fun index => biasErrorComponentBound index component)
          atTop (nhds 0)) :
    Tendsto actualVariance atTop
      (nhds
        ((1 / denominator ^ 2) * (1 / normalizer) *
          weightedScoreCellMomentLimit cells
            (fun cell =>
              (contributionLimit cell - target * weightLimit cell) ^ 2)
            massLimit)) :=
  tendsto_actualBootstrapVariance_of_eventually_cell_contribution_weight_limits_l1BracketingNumber_obligations_and_error_stability
    (Bracket := Bracket) cells sample score contribution weight target
    denominator normalizer cellContribution cellWeight contributionLimit
    weightLimit massLimit actualVariance scoreReplicationError
    biasCorrectionError herror_decomp hcover hcontributionCell hweightCell
    hcontributionLimit hweightLimit obligations
    (bootstrapScoreReplicationErrorNegligible_of_finite_component_bounds
      (l := atTop) scoreComponents scoreReplicationError
      scoreErrorComponent scoreErrorComponentBound hscore_decomp
      hscore_component_bound hscore_component_bound_tendsto)
    (bootstrapBiasCorrectionErrorNegligible_of_finite_component_bounds
      (l := atTop) biasComponents biasCorrectionError biasErrorComponent
      biasErrorComponentBound hbias_decomp hbias_component_bound
      hbias_component_bound_tendsto)

/--
VdV&W endpoint assemblies supply the score-cell mass LLN, and finite component
error bounds supply score-replication and bias-correction negligibility, for
the eventual contribution/weight-limit actual bootstrap variance route.
-/
theorem
    tendsto_actualBootstrapVariance_of_eventually_cell_contribution_weight_limits_vdvw241_endpoint_assembly_and_finite_error_bounds
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
    (scoreErrorComponent scoreErrorComponentBound :
      ℕ -> ScoreComponent -> Real)
    (biasErrorComponent biasErrorComponentBound :
      ℕ -> BiasComponent -> Real)
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
            scoreErrorComponentBound index component)
    (hscore_component_bound_tendsto :
      ∀ component, component ∈ scoreComponents ->
        Tendsto (fun index => scoreErrorComponentBound index component)
          atTop (nhds 0))
    (hbias_decomp :
      biasCorrectionError =ᶠ[atTop]
        (fun index => ∑ component ∈ biasComponents,
          biasErrorComponent index component))
    (hbias_component_bound :
      ∀ᶠ index in atTop,
        ∀ component, component ∈ biasComponents ->
          |biasErrorComponent index component| ≤
            biasErrorComponentBound index component)
    (hbias_component_bound_tendsto :
      ∀ component, component ∈ biasComponents ->
        Tendsto (fun index => biasErrorComponentBound index component)
          atTop (nhds 0)) :
    Tendsto actualVariance atTop
      (nhds
        ((1 / denominator ^ 2) * (1 / normalizer) *
          weightedScoreCellMomentLimit cells
            (fun cell =>
              (contributionLimit cell - target * weightLimit cell) ^ 2)
            massLimit)) :=
  tendsto_actualBootstrapVariance_of_eventually_cell_contribution_weight_limits_vdvw241_endpoint_assembly_and_error_stability
    (Bracket := Bracket) cells sample score contribution weight target
    denominator normalizer cellContribution cellWeight contributionLimit
    weightLimit massLimit actualVariance scoreReplicationError
    biasCorrectionError herror_decomp hcover hcontributionCell hweightCell
    hcontributionLimit hweightLimit assembly
    (bootstrapScoreReplicationErrorNegligible_of_finite_component_bounds
      (l := atTop) scoreComponents scoreReplicationError
      scoreErrorComponent scoreErrorComponentBound hscore_decomp
      hscore_component_bound hscore_component_bound_tendsto)
    (bootstrapBiasCorrectionErrorNegligible_of_finite_component_bounds
      (l := atTop) biasComponents biasCorrectionError biasErrorComponent
      biasErrorComponentBound hbias_decomp hbias_component_bound
      hbias_component_bound_tendsto)

/--
Paired actual bootstrap variance convergence from fixed finite-cell loadings
and finite-component score/bias error bounds.
-/
theorem paired_tendsto_actualBootstrapVariance_of_finiteCell_and_finite_error_bounds
    [DecidableEq Cell]
    {LeftScoreComponent RightScoreComponent LeftBiasComponent
      RightBiasComponent : Type*}
    [DecidableEq LeftScoreComponent] [DecidableEq RightScoreComponent]
    [DecidableEq LeftBiasComponent] [DecidableEq RightBiasComponent]
    (leftCells rightCells : Finset Cell)
    (leftScoreComponents : Finset LeftScoreComponent)
    (rightScoreComponents : Finset RightScoreComponent)
    (leftBiasComponents : Finset LeftBiasComponent)
    (rightBiasComponents : Finset RightBiasComponent)
    (leftSample rightSample : Index -> Finset Unit)
    (leftScore rightScore : Index -> Unit -> Cell)
    (leftContribution leftWeight rightContribution rightWeight :
      Index -> Unit -> Real)
    (leftTarget leftDenominator leftNormalizer
      rightTarget rightDenominator rightNormalizer : Real)
    (leftLoading leftMassLimit rightLoading rightMassLimit : Cell -> Real)
    (leftActualVariance leftScoreReplicationError leftBiasCorrectionError
      rightActualVariance rightScoreReplicationError
      rightBiasCorrectionError : Index -> Real)
    (leftScoreErrorComponent leftScoreErrorComponentBound :
      Index -> LeftScoreComponent -> Real)
    (rightScoreErrorComponent rightScoreErrorComponentBound :
      Index -> RightScoreComponent -> Real)
    (leftBiasErrorComponent leftBiasErrorComponentBound :
      Index -> LeftBiasComponent -> Real)
    (rightBiasErrorComponent rightBiasErrorComponentBound :
      Index -> RightBiasComponent -> Real)
    (hleft_error_decomp :
      (fun index =>
        leftActualVariance index -
          bootstrapCenteredVarianceTarget (leftSample index)
            (leftContribution index) (leftWeight index) leftTarget
            leftDenominator leftNormalizer) =ᶠ[l]
        (fun index =>
          leftScoreReplicationError index + leftBiasCorrectionError index))
    (hright_error_decomp :
      (fun index =>
        rightActualVariance index -
          bootstrapCenteredVarianceTarget (rightSample index)
            (rightContribution index) (rightWeight index) rightTarget
            rightDenominator rightNormalizer) =ᶠ[l]
        (fun index =>
          rightScoreReplicationError index + rightBiasCorrectionError index))
    (hleft_cover :
      ∀ index unit, unit ∈ leftSample index ->
        leftScore index unit ∈ leftCells)
    (hright_cover :
      ∀ index unit, unit ∈ rightSample index ->
        rightScore index unit ∈ rightCells)
    (hleft_loading :
      ∀ index unit, unit ∈ leftSample index ->
        leftLoading (leftScore index unit) =
          (leftContribution index unit -
            leftTarget * leftWeight index unit) ^ 2)
    (hright_loading :
      ∀ index unit, unit ∈ rightSample index ->
        rightLoading (rightScore index unit) =
          (rightContribution index unit -
            rightTarget * rightWeight index unit) ^ 2)
    (hleft_mass :
      cellwiseScoreCellMassLLN (l := l) leftCells leftSample
        (fun _index _unit => 1) leftScore leftMassLimit)
    (hright_mass :
      cellwiseScoreCellMassLLN (l := l) rightCells rightSample
        (fun _index _unit => 1) rightScore rightMassLimit)
    (hleft_score_decomp :
      leftScoreReplicationError =ᶠ[l]
        (fun index => ∑ component ∈ leftScoreComponents,
          leftScoreErrorComponent index component))
    (hright_score_decomp :
      rightScoreReplicationError =ᶠ[l]
        (fun index => ∑ component ∈ rightScoreComponents,
          rightScoreErrorComponent index component))
    (hleft_score_component_bound :
      ∀ᶠ index in l,
        ∀ component, component ∈ leftScoreComponents ->
          |leftScoreErrorComponent index component| ≤
            leftScoreErrorComponentBound index component)
    (hright_score_component_bound :
      ∀ᶠ index in l,
        ∀ component, component ∈ rightScoreComponents ->
          |rightScoreErrorComponent index component| ≤
            rightScoreErrorComponentBound index component)
    (hleft_score_component_bound_tendsto :
      ∀ component, component ∈ leftScoreComponents ->
        Tendsto (fun index => leftScoreErrorComponentBound index component)
          l (nhds 0))
    (hright_score_component_bound_tendsto :
      ∀ component, component ∈ rightScoreComponents ->
        Tendsto (fun index => rightScoreErrorComponentBound index component)
          l (nhds 0))
    (hleft_bias_decomp :
      leftBiasCorrectionError =ᶠ[l]
        (fun index => ∑ component ∈ leftBiasComponents,
          leftBiasErrorComponent index component))
    (hright_bias_decomp :
      rightBiasCorrectionError =ᶠ[l]
        (fun index => ∑ component ∈ rightBiasComponents,
          rightBiasErrorComponent index component))
    (hleft_bias_component_bound :
      ∀ᶠ index in l,
        ∀ component, component ∈ leftBiasComponents ->
          |leftBiasErrorComponent index component| ≤
            leftBiasErrorComponentBound index component)
    (hright_bias_component_bound :
      ∀ᶠ index in l,
        ∀ component, component ∈ rightBiasComponents ->
          |rightBiasErrorComponent index component| ≤
            rightBiasErrorComponentBound index component)
    (hleft_bias_component_bound_tendsto :
      ∀ component, component ∈ leftBiasComponents ->
        Tendsto (fun index => leftBiasErrorComponentBound index component)
          l (nhds 0))
    (hright_bias_component_bound_tendsto :
      ∀ component, component ∈ rightBiasComponents ->
        Tendsto (fun index => rightBiasErrorComponentBound index component)
          l (nhds 0)) :
    Tendsto leftActualVariance l
        (nhds
          ((1 / leftDenominator ^ 2) * (1 / leftNormalizer) *
            weightedScoreCellMomentLimit leftCells leftLoading
              leftMassLimit)) ∧
      Tendsto rightActualVariance l
        (nhds
          ((1 / rightDenominator ^ 2) * (1 / rightNormalizer) *
            weightedScoreCellMomentLimit rightCells rightLoading
              rightMassLimit)) :=
  ⟨tendsto_actualBootstrapVariance_of_finiteCell_and_finite_error_bounds
      (l := l) leftCells leftScoreComponents leftBiasComponents
      leftSample leftScore leftContribution leftWeight leftTarget
      leftDenominator leftNormalizer leftLoading leftMassLimit
      leftActualVariance leftScoreReplicationError leftBiasCorrectionError
      leftScoreErrorComponent leftScoreErrorComponentBound
      leftBiasErrorComponent leftBiasErrorComponentBound hleft_error_decomp
      hleft_cover hleft_loading hleft_mass hleft_score_decomp
      hleft_score_component_bound hleft_score_component_bound_tendsto
      hleft_bias_decomp hleft_bias_component_bound
      hleft_bias_component_bound_tendsto,
    tendsto_actualBootstrapVariance_of_finiteCell_and_finite_error_bounds
      (l := l) rightCells rightScoreComponents rightBiasComponents
      rightSample rightScore rightContribution rightWeight rightTarget
      rightDenominator rightNormalizer rightLoading rightMassLimit
      rightActualVariance rightScoreReplicationError rightBiasCorrectionError
      rightScoreErrorComponent rightScoreErrorComponentBound
      rightBiasErrorComponent rightBiasErrorComponentBound
      hright_error_decomp hright_cover hright_loading hright_mass
      hright_score_decomp hright_score_component_bound
      hright_score_component_bound_tendsto hright_bias_decomp
      hright_bias_component_bound hright_bias_component_bound_tendsto⟩

/--
Paired actual bootstrap variance convergence from score-cell contribution and
weight limits plus finite-component score/bias error bounds.
-/
theorem paired_tendsto_actualBootstrapVariance_of_cell_contribution_weight_limits_and_finite_error_bounds
    [DecidableEq Cell]
    {LeftScoreComponent RightScoreComponent LeftBiasComponent
      RightBiasComponent : Type*}
    [DecidableEq LeftScoreComponent] [DecidableEq RightScoreComponent]
    [DecidableEq LeftBiasComponent] [DecidableEq RightBiasComponent]
    (leftCells rightCells : Finset Cell)
    (leftScoreComponents : Finset LeftScoreComponent)
    (rightScoreComponents : Finset RightScoreComponent)
    (leftBiasComponents : Finset LeftBiasComponent)
    (rightBiasComponents : Finset RightBiasComponent)
    (leftSample rightSample : Index -> Finset Unit)
    (leftScore rightScore : Index -> Unit -> Cell)
    (leftContribution leftWeight rightContribution rightWeight :
      Index -> Unit -> Real)
    (leftTarget leftDenominator leftNormalizer
      rightTarget rightDenominator rightNormalizer : Real)
    (leftCellContribution leftCellWeight rightCellContribution
      rightCellWeight : Index -> Cell -> Real)
    (leftContributionLimit leftWeightLimit leftMassLimit
      rightContributionLimit rightWeightLimit rightMassLimit : Cell -> Real)
    (leftActualVariance leftScoreReplicationError leftBiasCorrectionError
      rightActualVariance rightScoreReplicationError
      rightBiasCorrectionError : Index -> Real)
    (leftScoreErrorComponent leftScoreErrorComponentBound :
      Index -> LeftScoreComponent -> Real)
    (rightScoreErrorComponent rightScoreErrorComponentBound :
      Index -> RightScoreComponent -> Real)
    (leftBiasErrorComponent leftBiasErrorComponentBound :
      Index -> LeftBiasComponent -> Real)
    (rightBiasErrorComponent rightBiasErrorComponentBound :
      Index -> RightBiasComponent -> Real)
    (hleft_error_decomp :
      (fun index =>
        leftActualVariance index -
          bootstrapCenteredVarianceTarget (leftSample index)
            (leftContribution index) (leftWeight index) leftTarget
            leftDenominator leftNormalizer) =ᶠ[l]
        (fun index =>
          leftScoreReplicationError index + leftBiasCorrectionError index))
    (hright_error_decomp :
      (fun index =>
        rightActualVariance index -
          bootstrapCenteredVarianceTarget (rightSample index)
            (rightContribution index) (rightWeight index) rightTarget
            rightDenominator rightNormalizer) =ᶠ[l]
        (fun index =>
          rightScoreReplicationError index + rightBiasCorrectionError index))
    (hleft_cover :
      ∀ index unit, unit ∈ leftSample index ->
        leftScore index unit ∈ leftCells)
    (hright_cover :
      ∀ index unit, unit ∈ rightSample index ->
        rightScore index unit ∈ rightCells)
    (hleft_contributionCell :
      ∀ index unit, unit ∈ leftSample index ->
        leftCellContribution index (leftScore index unit) =
          leftContribution index unit)
    (hright_contributionCell :
      ∀ index unit, unit ∈ rightSample index ->
        rightCellContribution index (rightScore index unit) =
          rightContribution index unit)
    (hleft_weightCell :
      ∀ index unit, unit ∈ leftSample index ->
        leftCellWeight index (leftScore index unit) =
          leftWeight index unit)
    (hright_weightCell :
      ∀ index unit, unit ∈ rightSample index ->
        rightCellWeight index (rightScore index unit) =
          rightWeight index unit)
    (hleft_contributionLimit :
      ∀ cell, cell ∈ leftCells ->
        Tendsto (fun index => leftCellContribution index cell)
          l (nhds (leftContributionLimit cell)))
    (hright_contributionLimit :
      ∀ cell, cell ∈ rightCells ->
        Tendsto (fun index => rightCellContribution index cell)
          l (nhds (rightContributionLimit cell)))
    (hleft_weightLimit :
      ∀ cell, cell ∈ leftCells ->
        Tendsto (fun index => leftCellWeight index cell)
          l (nhds (leftWeightLimit cell)))
    (hright_weightLimit :
      ∀ cell, cell ∈ rightCells ->
        Tendsto (fun index => rightCellWeight index cell)
          l (nhds (rightWeightLimit cell)))
    (hleft_mass :
      cellwiseScoreCellMassLLN (l := l) leftCells leftSample
        (fun _index _unit => 1) leftScore leftMassLimit)
    (hright_mass :
      cellwiseScoreCellMassLLN (l := l) rightCells rightSample
        (fun _index _unit => 1) rightScore rightMassLimit)
    (hleft_score_decomp :
      leftScoreReplicationError =ᶠ[l]
        (fun index => ∑ component ∈ leftScoreComponents,
          leftScoreErrorComponent index component))
    (hright_score_decomp :
      rightScoreReplicationError =ᶠ[l]
        (fun index => ∑ component ∈ rightScoreComponents,
          rightScoreErrorComponent index component))
    (hleft_score_component_bound :
      ∀ᶠ index in l,
        ∀ component, component ∈ leftScoreComponents ->
          |leftScoreErrorComponent index component| ≤
            leftScoreErrorComponentBound index component)
    (hright_score_component_bound :
      ∀ᶠ index in l,
        ∀ component, component ∈ rightScoreComponents ->
          |rightScoreErrorComponent index component| ≤
            rightScoreErrorComponentBound index component)
    (hleft_score_component_bound_tendsto :
      ∀ component, component ∈ leftScoreComponents ->
        Tendsto (fun index => leftScoreErrorComponentBound index component)
          l (nhds 0))
    (hright_score_component_bound_tendsto :
      ∀ component, component ∈ rightScoreComponents ->
        Tendsto (fun index => rightScoreErrorComponentBound index component)
          l (nhds 0))
    (hleft_bias_decomp :
      leftBiasCorrectionError =ᶠ[l]
        (fun index => ∑ component ∈ leftBiasComponents,
          leftBiasErrorComponent index component))
    (hright_bias_decomp :
      rightBiasCorrectionError =ᶠ[l]
        (fun index => ∑ component ∈ rightBiasComponents,
          rightBiasErrorComponent index component))
    (hleft_bias_component_bound :
      ∀ᶠ index in l,
        ∀ component, component ∈ leftBiasComponents ->
          |leftBiasErrorComponent index component| ≤
            leftBiasErrorComponentBound index component)
    (hright_bias_component_bound :
      ∀ᶠ index in l,
        ∀ component, component ∈ rightBiasComponents ->
          |rightBiasErrorComponent index component| ≤
            rightBiasErrorComponentBound index component)
    (hleft_bias_component_bound_tendsto :
      ∀ component, component ∈ leftBiasComponents ->
        Tendsto (fun index => leftBiasErrorComponentBound index component)
          l (nhds 0))
    (hright_bias_component_bound_tendsto :
      ∀ component, component ∈ rightBiasComponents ->
        Tendsto (fun index => rightBiasErrorComponentBound index component)
          l (nhds 0)) :
    Tendsto leftActualVariance l
        (nhds
          ((1 / leftDenominator ^ 2) * (1 / leftNormalizer) *
            weightedScoreCellMomentLimit leftCells
              (fun cell =>
                (leftContributionLimit cell -
                  leftTarget * leftWeightLimit cell) ^ 2)
              leftMassLimit)) ∧
      Tendsto rightActualVariance l
        (nhds
          ((1 / rightDenominator ^ 2) * (1 / rightNormalizer) *
            weightedScoreCellMomentLimit rightCells
              (fun cell =>
                (rightContributionLimit cell -
                  rightTarget * rightWeightLimit cell) ^ 2)
              rightMassLimit)) :=
  ⟨tendsto_actualBootstrapVariance_of_cell_contribution_weight_limits_and_finite_error_bounds
      (l := l) leftCells leftScoreComponents leftBiasComponents
      leftSample leftScore leftContribution leftWeight leftTarget
      leftDenominator leftNormalizer leftCellContribution leftCellWeight
      leftContributionLimit leftWeightLimit leftMassLimit leftActualVariance
      leftScoreReplicationError leftBiasCorrectionError
      leftScoreErrorComponent leftScoreErrorComponentBound
      leftBiasErrorComponent leftBiasErrorComponentBound hleft_error_decomp
      hleft_cover hleft_contributionCell hleft_weightCell
      hleft_contributionLimit hleft_weightLimit hleft_mass
      hleft_score_decomp hleft_score_component_bound
      hleft_score_component_bound_tendsto hleft_bias_decomp
      hleft_bias_component_bound hleft_bias_component_bound_tendsto,
    tendsto_actualBootstrapVariance_of_cell_contribution_weight_limits_and_finite_error_bounds
      (l := l) rightCells rightScoreComponents rightBiasComponents
      rightSample rightScore rightContribution rightWeight rightTarget
      rightDenominator rightNormalizer rightCellContribution rightCellWeight
      rightContributionLimit rightWeightLimit rightMassLimit
      rightActualVariance rightScoreReplicationError rightBiasCorrectionError
      rightScoreErrorComponent rightScoreErrorComponentBound
      rightBiasErrorComponent rightBiasErrorComponentBound
      hright_error_decomp hright_cover hright_contributionCell
      hright_weightCell hright_contributionLimit hright_weightLimit
      hright_mass hright_score_decomp hright_score_component_bound
      hright_score_component_bound_tendsto hright_bias_decomp
      hright_bias_component_bound hright_bias_component_bound_tendsto⟩

/--
Paired eventual score-cell representation version with finite-component
score/bias error bounds.
-/
theorem paired_tendsto_actualBootstrapVariance_of_eventually_cell_contribution_weight_limits_and_finite_error_bounds
    [DecidableEq Cell]
    {LeftScoreComponent RightScoreComponent LeftBiasComponent
      RightBiasComponent : Type*}
    [DecidableEq LeftScoreComponent] [DecidableEq RightScoreComponent]
    [DecidableEq LeftBiasComponent] [DecidableEq RightBiasComponent]
    (leftCells rightCells : Finset Cell)
    (leftScoreComponents : Finset LeftScoreComponent)
    (rightScoreComponents : Finset RightScoreComponent)
    (leftBiasComponents : Finset LeftBiasComponent)
    (rightBiasComponents : Finset RightBiasComponent)
    (leftSample rightSample : Index -> Finset Unit)
    (leftScore rightScore : Index -> Unit -> Cell)
    (leftContribution leftWeight rightContribution rightWeight :
      Index -> Unit -> Real)
    (leftTarget leftDenominator leftNormalizer
      rightTarget rightDenominator rightNormalizer : Real)
    (leftCellContribution leftCellWeight rightCellContribution
      rightCellWeight : Index -> Cell -> Real)
    (leftContributionLimit leftWeightLimit leftMassLimit
      rightContributionLimit rightWeightLimit rightMassLimit : Cell -> Real)
    (leftActualVariance leftScoreReplicationError leftBiasCorrectionError
      rightActualVariance rightScoreReplicationError
      rightBiasCorrectionError : Index -> Real)
    (leftScoreErrorComponent leftScoreErrorComponentBound :
      Index -> LeftScoreComponent -> Real)
    (rightScoreErrorComponent rightScoreErrorComponentBound :
      Index -> RightScoreComponent -> Real)
    (leftBiasErrorComponent leftBiasErrorComponentBound :
      Index -> LeftBiasComponent -> Real)
    (rightBiasErrorComponent rightBiasErrorComponentBound :
      Index -> RightBiasComponent -> Real)
    (hleft_error_decomp :
      (fun index =>
        leftActualVariance index -
          bootstrapCenteredVarianceTarget (leftSample index)
            (leftContribution index) (leftWeight index) leftTarget
            leftDenominator leftNormalizer) =ᶠ[l]
        (fun index =>
          leftScoreReplicationError index + leftBiasCorrectionError index))
    (hright_error_decomp :
      (fun index =>
        rightActualVariance index -
          bootstrapCenteredVarianceTarget (rightSample index)
            (rightContribution index) (rightWeight index) rightTarget
            rightDenominator rightNormalizer) =ᶠ[l]
        (fun index =>
          rightScoreReplicationError index + rightBiasCorrectionError index))
    (hleft_cover :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ leftSample index ->
          leftScore index unit ∈ leftCells)
    (hright_cover :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ rightSample index ->
          rightScore index unit ∈ rightCells)
    (hleft_contributionCell :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ leftSample index ->
          leftCellContribution index (leftScore index unit) =
            leftContribution index unit)
    (hright_contributionCell :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ rightSample index ->
          rightCellContribution index (rightScore index unit) =
            rightContribution index unit)
    (hleft_weightCell :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ leftSample index ->
          leftCellWeight index (leftScore index unit) =
            leftWeight index unit)
    (hright_weightCell :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ rightSample index ->
          rightCellWeight index (rightScore index unit) =
            rightWeight index unit)
    (hleft_contributionLimit :
      ∀ cell, cell ∈ leftCells ->
        Tendsto (fun index => leftCellContribution index cell)
          l (nhds (leftContributionLimit cell)))
    (hright_contributionLimit :
      ∀ cell, cell ∈ rightCells ->
        Tendsto (fun index => rightCellContribution index cell)
          l (nhds (rightContributionLimit cell)))
    (hleft_weightLimit :
      ∀ cell, cell ∈ leftCells ->
        Tendsto (fun index => leftCellWeight index cell)
          l (nhds (leftWeightLimit cell)))
    (hright_weightLimit :
      ∀ cell, cell ∈ rightCells ->
        Tendsto (fun index => rightCellWeight index cell)
          l (nhds (rightWeightLimit cell)))
    (hleft_mass :
      cellwiseScoreCellMassLLN (l := l) leftCells leftSample
        (fun _index _unit => 1) leftScore leftMassLimit)
    (hright_mass :
      cellwiseScoreCellMassLLN (l := l) rightCells rightSample
        (fun _index _unit => 1) rightScore rightMassLimit)
    (hleft_score_decomp :
      leftScoreReplicationError =ᶠ[l]
        (fun index => ∑ component ∈ leftScoreComponents,
          leftScoreErrorComponent index component))
    (hright_score_decomp :
      rightScoreReplicationError =ᶠ[l]
        (fun index => ∑ component ∈ rightScoreComponents,
          rightScoreErrorComponent index component))
    (hleft_score_component_bound :
      ∀ᶠ index in l,
        ∀ component, component ∈ leftScoreComponents ->
          |leftScoreErrorComponent index component| ≤
            leftScoreErrorComponentBound index component)
    (hright_score_component_bound :
      ∀ᶠ index in l,
        ∀ component, component ∈ rightScoreComponents ->
          |rightScoreErrorComponent index component| ≤
            rightScoreErrorComponentBound index component)
    (hleft_score_component_bound_tendsto :
      ∀ component, component ∈ leftScoreComponents ->
        Tendsto (fun index => leftScoreErrorComponentBound index component)
          l (nhds 0))
    (hright_score_component_bound_tendsto :
      ∀ component, component ∈ rightScoreComponents ->
        Tendsto (fun index => rightScoreErrorComponentBound index component)
          l (nhds 0))
    (hleft_bias_decomp :
      leftBiasCorrectionError =ᶠ[l]
        (fun index => ∑ component ∈ leftBiasComponents,
          leftBiasErrorComponent index component))
    (hright_bias_decomp :
      rightBiasCorrectionError =ᶠ[l]
        (fun index => ∑ component ∈ rightBiasComponents,
          rightBiasErrorComponent index component))
    (hleft_bias_component_bound :
      ∀ᶠ index in l,
        ∀ component, component ∈ leftBiasComponents ->
          |leftBiasErrorComponent index component| ≤
            leftBiasErrorComponentBound index component)
    (hright_bias_component_bound :
      ∀ᶠ index in l,
        ∀ component, component ∈ rightBiasComponents ->
          |rightBiasErrorComponent index component| ≤
            rightBiasErrorComponentBound index component)
    (hleft_bias_component_bound_tendsto :
      ∀ component, component ∈ leftBiasComponents ->
        Tendsto (fun index => leftBiasErrorComponentBound index component)
          l (nhds 0))
    (hright_bias_component_bound_tendsto :
      ∀ component, component ∈ rightBiasComponents ->
        Tendsto (fun index => rightBiasErrorComponentBound index component)
          l (nhds 0)) :
    Tendsto leftActualVariance l
        (nhds
          ((1 / leftDenominator ^ 2) * (1 / leftNormalizer) *
            weightedScoreCellMomentLimit leftCells
              (fun cell =>
                (leftContributionLimit cell -
                  leftTarget * leftWeightLimit cell) ^ 2)
              leftMassLimit)) ∧
      Tendsto rightActualVariance l
        (nhds
          ((1 / rightDenominator ^ 2) * (1 / rightNormalizer) *
            weightedScoreCellMomentLimit rightCells
              (fun cell =>
                (rightContributionLimit cell -
                  rightTarget * rightWeightLimit cell) ^ 2)
              rightMassLimit)) :=
  ⟨tendsto_actualBootstrapVariance_of_eventually_cell_contribution_weight_limits_and_finite_error_bounds
      (l := l) leftCells leftScoreComponents leftBiasComponents
      leftSample leftScore leftContribution leftWeight leftTarget
      leftDenominator leftNormalizer leftCellContribution leftCellWeight
      leftContributionLimit leftWeightLimit leftMassLimit leftActualVariance
      leftScoreReplicationError leftBiasCorrectionError
      leftScoreErrorComponent leftScoreErrorComponentBound
      leftBiasErrorComponent leftBiasErrorComponentBound hleft_error_decomp
      hleft_cover hleft_contributionCell hleft_weightCell
      hleft_contributionLimit hleft_weightLimit hleft_mass
      hleft_score_decomp hleft_score_component_bound
      hleft_score_component_bound_tendsto hleft_bias_decomp
      hleft_bias_component_bound hleft_bias_component_bound_tendsto,
    tendsto_actualBootstrapVariance_of_eventually_cell_contribution_weight_limits_and_finite_error_bounds
      (l := l) rightCells rightScoreComponents rightBiasComponents
      rightSample rightScore rightContribution rightWeight rightTarget
      rightDenominator rightNormalizer rightCellContribution rightCellWeight
      rightContributionLimit rightWeightLimit rightMassLimit
      rightActualVariance rightScoreReplicationError rightBiasCorrectionError
      rightScoreErrorComponent rightScoreErrorComponentBound
      rightBiasErrorComponent rightBiasErrorComponentBound
      hright_error_decomp hright_cover hright_contributionCell
      hright_weightCell hright_contributionLimit hright_weightLimit
      hright_mass hright_score_decomp hright_score_component_bound
      hright_score_component_bound_tendsto hright_bias_decomp
      hright_bias_component_bound hright_bias_component_bound_tendsto⟩

/--
Paired eventual score-cell representation version where score-replication on
both sides is supplied by concrete finite score-cell-by-component
decompositions, while bias-correction uses the existing finite component
error-bound route.
-/
theorem paired_tendsto_actualBootstrapVariance_of_eventually_cell_contribution_weight_limits_and_finite_score_cell_score_error_bounds
    [DecidableEq Cell]
    {LeftScoreComponent RightScoreComponent LeftBiasComponent
      RightBiasComponent : Type*}
    [DecidableEq LeftScoreComponent] [DecidableEq RightScoreComponent]
    [DecidableEq LeftBiasComponent] [DecidableEq RightBiasComponent]
    (leftCells rightCells : Finset Cell)
    (leftScoreComponents : Finset LeftScoreComponent)
    (rightScoreComponents : Finset RightScoreComponent)
    (leftBiasComponents : Finset LeftBiasComponent)
    (rightBiasComponents : Finset RightBiasComponent)
    (leftSample rightSample : Index -> Finset Unit)
    (leftScore rightScore : Index -> Unit -> Cell)
    (leftContribution leftWeight rightContribution rightWeight :
      Index -> Unit -> Real)
    (leftTarget leftDenominator leftNormalizer
      rightTarget rightDenominator rightNormalizer : Real)
    (leftCellContribution leftCellWeight rightCellContribution
      rightCellWeight : Index -> Cell -> Real)
    (leftContributionLimit leftWeightLimit leftMassLimit
      rightContributionLimit rightWeightLimit rightMassLimit : Cell -> Real)
    (leftActualVariance leftScoreReplicationError leftBiasCorrectionError
      rightActualVariance rightScoreReplicationError
      rightBiasCorrectionError : Index -> Real)
    (leftScoreErrorComponent leftScoreErrorComponentBound :
      Index -> Cell -> LeftScoreComponent -> Real)
    (rightScoreErrorComponent rightScoreErrorComponentBound :
      Index -> Cell -> RightScoreComponent -> Real)
    (leftBiasErrorComponent leftBiasErrorComponentBound :
      Index -> LeftBiasComponent -> Real)
    (rightBiasErrorComponent rightBiasErrorComponentBound :
      Index -> RightBiasComponent -> Real)
    (hleft_error_decomp :
      (fun index =>
        leftActualVariance index -
          bootstrapCenteredVarianceTarget (leftSample index)
            (leftContribution index) (leftWeight index) leftTarget
            leftDenominator leftNormalizer) =ᶠ[l]
        (fun index =>
          leftScoreReplicationError index + leftBiasCorrectionError index))
    (hright_error_decomp :
      (fun index =>
        rightActualVariance index -
          bootstrapCenteredVarianceTarget (rightSample index)
            (rightContribution index) (rightWeight index) rightTarget
            rightDenominator rightNormalizer) =ᶠ[l]
        (fun index =>
          rightScoreReplicationError index + rightBiasCorrectionError index))
    (hleft_cover :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ leftSample index ->
          leftScore index unit ∈ leftCells)
    (hright_cover :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ rightSample index ->
          rightScore index unit ∈ rightCells)
    (hleft_contributionCell :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ leftSample index ->
          leftCellContribution index (leftScore index unit) =
            leftContribution index unit)
    (hright_contributionCell :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ rightSample index ->
          rightCellContribution index (rightScore index unit) =
            rightContribution index unit)
    (hleft_weightCell :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ leftSample index ->
          leftCellWeight index (leftScore index unit) =
            leftWeight index unit)
    (hright_weightCell :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ rightSample index ->
          rightCellWeight index (rightScore index unit) =
            rightWeight index unit)
    (hleft_contributionLimit :
      ∀ cell, cell ∈ leftCells ->
        Tendsto (fun index => leftCellContribution index cell)
          l (nhds (leftContributionLimit cell)))
    (hright_contributionLimit :
      ∀ cell, cell ∈ rightCells ->
        Tendsto (fun index => rightCellContribution index cell)
          l (nhds (rightContributionLimit cell)))
    (hleft_weightLimit :
      ∀ cell, cell ∈ leftCells ->
        Tendsto (fun index => leftCellWeight index cell)
          l (nhds (leftWeightLimit cell)))
    (hright_weightLimit :
      ∀ cell, cell ∈ rightCells ->
        Tendsto (fun index => rightCellWeight index cell)
          l (nhds (rightWeightLimit cell)))
    (hleft_mass :
      cellwiseScoreCellMassLLN (l := l) leftCells leftSample
        (fun _index _unit => 1) leftScore leftMassLimit)
    (hright_mass :
      cellwiseScoreCellMassLLN (l := l) rightCells rightSample
        (fun _index _unit => 1) rightScore rightMassLimit)
    (hleft_score_decomp :
      leftScoreReplicationError =ᶠ[l]
        (fun index => ∑ cell ∈ leftCells,
          ∑ component ∈ leftScoreComponents,
            leftScoreErrorComponent index cell component))
    (hright_score_decomp :
      rightScoreReplicationError =ᶠ[l]
        (fun index => ∑ cell ∈ rightCells,
          ∑ component ∈ rightScoreComponents,
            rightScoreErrorComponent index cell component))
    (hleft_score_component_bound :
      ∀ᶠ index in l,
        ∀ cell, cell ∈ leftCells ->
          ∀ component, component ∈ leftScoreComponents ->
            |leftScoreErrorComponent index cell component| ≤
              leftScoreErrorComponentBound index cell component)
    (hright_score_component_bound :
      ∀ᶠ index in l,
        ∀ cell, cell ∈ rightCells ->
          ∀ component, component ∈ rightScoreComponents ->
            |rightScoreErrorComponent index cell component| ≤
              rightScoreErrorComponentBound index cell component)
    (hleft_score_component_bound_tendsto :
      ∀ cell, cell ∈ leftCells ->
        ∀ component, component ∈ leftScoreComponents ->
          Tendsto
            (fun index => leftScoreErrorComponentBound index cell component)
            l (nhds 0))
    (hright_score_component_bound_tendsto :
      ∀ cell, cell ∈ rightCells ->
        ∀ component, component ∈ rightScoreComponents ->
          Tendsto
            (fun index => rightScoreErrorComponentBound index cell component)
            l (nhds 0))
    (hleft_bias_decomp :
      leftBiasCorrectionError =ᶠ[l]
        (fun index => ∑ component ∈ leftBiasComponents,
          leftBiasErrorComponent index component))
    (hright_bias_decomp :
      rightBiasCorrectionError =ᶠ[l]
        (fun index => ∑ component ∈ rightBiasComponents,
          rightBiasErrorComponent index component))
    (hleft_bias_component_bound :
      ∀ᶠ index in l,
        ∀ component, component ∈ leftBiasComponents ->
          |leftBiasErrorComponent index component| ≤
            leftBiasErrorComponentBound index component)
    (hright_bias_component_bound :
      ∀ᶠ index in l,
        ∀ component, component ∈ rightBiasComponents ->
          |rightBiasErrorComponent index component| ≤
            rightBiasErrorComponentBound index component)
    (hleft_bias_component_bound_tendsto :
      ∀ component, component ∈ leftBiasComponents ->
        Tendsto (fun index => leftBiasErrorComponentBound index component)
          l (nhds 0))
    (hright_bias_component_bound_tendsto :
      ∀ component, component ∈ rightBiasComponents ->
        Tendsto (fun index => rightBiasErrorComponentBound index component)
          l (nhds 0)) :
    Tendsto leftActualVariance l
        (nhds
          ((1 / leftDenominator ^ 2) * (1 / leftNormalizer) *
            weightedScoreCellMomentLimit leftCells
              (fun cell =>
                (leftContributionLimit cell -
                  leftTarget * leftWeightLimit cell) ^ 2)
              leftMassLimit)) ∧
      Tendsto rightActualVariance l
        (nhds
          ((1 / rightDenominator ^ 2) * (1 / rightNormalizer) *
            weightedScoreCellMomentLimit rightCells
              (fun cell =>
                (rightContributionLimit cell -
                  rightTarget * rightWeightLimit cell) ^ 2)
              rightMassLimit)) :=
  ⟨tendsto_actualBootstrapVariance_of_eventually_cell_contribution_weight_limits_and_finite_score_cell_score_error_bounds
      (l := l) leftCells leftScoreComponents leftBiasComponents
      leftSample leftScore leftContribution leftWeight leftTarget
      leftDenominator leftNormalizer leftCellContribution leftCellWeight
      leftContributionLimit leftWeightLimit leftMassLimit leftActualVariance
      leftScoreReplicationError leftBiasCorrectionError
      leftScoreErrorComponent leftScoreErrorComponentBound
      leftBiasErrorComponent leftBiasErrorComponentBound hleft_error_decomp
      hleft_cover hleft_contributionCell hleft_weightCell
      hleft_contributionLimit hleft_weightLimit hleft_mass
      hleft_score_decomp hleft_score_component_bound
      hleft_score_component_bound_tendsto hleft_bias_decomp
      hleft_bias_component_bound hleft_bias_component_bound_tendsto,
    tendsto_actualBootstrapVariance_of_eventually_cell_contribution_weight_limits_and_finite_score_cell_score_error_bounds
      (l := l) rightCells rightScoreComponents rightBiasComponents
      rightSample rightScore rightContribution rightWeight rightTarget
      rightDenominator rightNormalizer rightCellContribution rightCellWeight
      rightContributionLimit rightWeightLimit rightMassLimit
      rightActualVariance rightScoreReplicationError rightBiasCorrectionError
      rightScoreErrorComponent rightScoreErrorComponentBound
      rightBiasErrorComponent rightBiasErrorComponentBound
      hright_error_decomp hright_cover hright_contributionCell
      hright_weightCell hright_contributionLimit hright_weightLimit
      hright_mass hright_score_decomp hright_score_component_bound
      hright_score_component_bound_tendsto hright_bias_decomp
      hright_bias_component_bound hright_bias_component_bound_tendsto⟩

/--
Paired eventual score-cell representation version where bias-correction on
both sides is supplied by concrete finite score-cell-by-component
decompositions, while score-replication uses the existing finite component
error-bound route.
-/
theorem paired_tendsto_actualBootstrapVariance_of_eventually_cell_contribution_weight_limits_and_finite_score_cell_bias_error_bounds
    [DecidableEq Cell]
    {LeftScoreComponent RightScoreComponent LeftBiasComponent
      RightBiasComponent : Type*}
    [DecidableEq LeftScoreComponent] [DecidableEq RightScoreComponent]
    [DecidableEq LeftBiasComponent] [DecidableEq RightBiasComponent]
    (leftCells rightCells : Finset Cell)
    (leftScoreComponents : Finset LeftScoreComponent)
    (rightScoreComponents : Finset RightScoreComponent)
    (leftBiasComponents : Finset LeftBiasComponent)
    (rightBiasComponents : Finset RightBiasComponent)
    (leftSample rightSample : Index -> Finset Unit)
    (leftScore rightScore : Index -> Unit -> Cell)
    (leftContribution leftWeight rightContribution rightWeight :
      Index -> Unit -> Real)
    (leftTarget leftDenominator leftNormalizer
      rightTarget rightDenominator rightNormalizer : Real)
    (leftCellContribution leftCellWeight rightCellContribution
      rightCellWeight : Index -> Cell -> Real)
    (leftContributionLimit leftWeightLimit leftMassLimit
      rightContributionLimit rightWeightLimit rightMassLimit : Cell -> Real)
    (leftActualVariance leftScoreReplicationError leftBiasCorrectionError
      rightActualVariance rightScoreReplicationError
      rightBiasCorrectionError : Index -> Real)
    (leftScoreErrorComponent leftScoreErrorComponentBound :
      Index -> LeftScoreComponent -> Real)
    (rightScoreErrorComponent rightScoreErrorComponentBound :
      Index -> RightScoreComponent -> Real)
    (leftBiasErrorComponent leftBiasErrorComponentBound :
      Index -> Cell -> LeftBiasComponent -> Real)
    (rightBiasErrorComponent rightBiasErrorComponentBound :
      Index -> Cell -> RightBiasComponent -> Real)
    (hleft_error_decomp :
      (fun index =>
        leftActualVariance index -
          bootstrapCenteredVarianceTarget (leftSample index)
            (leftContribution index) (leftWeight index) leftTarget
            leftDenominator leftNormalizer) =ᶠ[l]
        (fun index =>
          leftScoreReplicationError index + leftBiasCorrectionError index))
    (hright_error_decomp :
      (fun index =>
        rightActualVariance index -
          bootstrapCenteredVarianceTarget (rightSample index)
            (rightContribution index) (rightWeight index) rightTarget
            rightDenominator rightNormalizer) =ᶠ[l]
        (fun index =>
          rightScoreReplicationError index + rightBiasCorrectionError index))
    (hleft_cover :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ leftSample index ->
          leftScore index unit ∈ leftCells)
    (hright_cover :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ rightSample index ->
          rightScore index unit ∈ rightCells)
    (hleft_contributionCell :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ leftSample index ->
          leftCellContribution index (leftScore index unit) =
            leftContribution index unit)
    (hright_contributionCell :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ rightSample index ->
          rightCellContribution index (rightScore index unit) =
            rightContribution index unit)
    (hleft_weightCell :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ leftSample index ->
          leftCellWeight index (leftScore index unit) =
            leftWeight index unit)
    (hright_weightCell :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ rightSample index ->
          rightCellWeight index (rightScore index unit) =
            rightWeight index unit)
    (hleft_contributionLimit :
      ∀ cell, cell ∈ leftCells ->
        Tendsto (fun index => leftCellContribution index cell)
          l (nhds (leftContributionLimit cell)))
    (hright_contributionLimit :
      ∀ cell, cell ∈ rightCells ->
        Tendsto (fun index => rightCellContribution index cell)
          l (nhds (rightContributionLimit cell)))
    (hleft_weightLimit :
      ∀ cell, cell ∈ leftCells ->
        Tendsto (fun index => leftCellWeight index cell)
          l (nhds (leftWeightLimit cell)))
    (hright_weightLimit :
      ∀ cell, cell ∈ rightCells ->
        Tendsto (fun index => rightCellWeight index cell)
          l (nhds (rightWeightLimit cell)))
    (hleft_mass :
      cellwiseScoreCellMassLLN (l := l) leftCells leftSample
        (fun _index _unit => 1) leftScore leftMassLimit)
    (hright_mass :
      cellwiseScoreCellMassLLN (l := l) rightCells rightSample
        (fun _index _unit => 1) rightScore rightMassLimit)
    (hleft_score_decomp :
      leftScoreReplicationError =ᶠ[l]
        (fun index => ∑ component ∈ leftScoreComponents,
          leftScoreErrorComponent index component))
    (hright_score_decomp :
      rightScoreReplicationError =ᶠ[l]
        (fun index => ∑ component ∈ rightScoreComponents,
          rightScoreErrorComponent index component))
    (hleft_score_component_bound :
      ∀ᶠ index in l,
        ∀ component, component ∈ leftScoreComponents ->
          |leftScoreErrorComponent index component| ≤
            leftScoreErrorComponentBound index component)
    (hright_score_component_bound :
      ∀ᶠ index in l,
        ∀ component, component ∈ rightScoreComponents ->
          |rightScoreErrorComponent index component| ≤
            rightScoreErrorComponentBound index component)
    (hleft_score_component_bound_tendsto :
      ∀ component, component ∈ leftScoreComponents ->
        Tendsto (fun index => leftScoreErrorComponentBound index component)
          l (nhds 0))
    (hright_score_component_bound_tendsto :
      ∀ component, component ∈ rightScoreComponents ->
        Tendsto (fun index => rightScoreErrorComponentBound index component)
          l (nhds 0))
    (hleft_bias_decomp :
      leftBiasCorrectionError =ᶠ[l]
        (fun index => ∑ cell ∈ leftCells,
          ∑ component ∈ leftBiasComponents,
            leftBiasErrorComponent index cell component))
    (hright_bias_decomp :
      rightBiasCorrectionError =ᶠ[l]
        (fun index => ∑ cell ∈ rightCells,
          ∑ component ∈ rightBiasComponents,
            rightBiasErrorComponent index cell component))
    (hleft_bias_component_bound :
      ∀ᶠ index in l,
        ∀ cell, cell ∈ leftCells ->
          ∀ component, component ∈ leftBiasComponents ->
            |leftBiasErrorComponent index cell component| ≤
              leftBiasErrorComponentBound index cell component)
    (hright_bias_component_bound :
      ∀ᶠ index in l,
        ∀ cell, cell ∈ rightCells ->
          ∀ component, component ∈ rightBiasComponents ->
            |rightBiasErrorComponent index cell component| ≤
              rightBiasErrorComponentBound index cell component)
    (hleft_bias_component_bound_tendsto :
      ∀ cell, cell ∈ leftCells ->
        ∀ component, component ∈ leftBiasComponents ->
          Tendsto
            (fun index => leftBiasErrorComponentBound index cell component)
            l (nhds 0))
    (hright_bias_component_bound_tendsto :
      ∀ cell, cell ∈ rightCells ->
        ∀ component, component ∈ rightBiasComponents ->
          Tendsto
            (fun index => rightBiasErrorComponentBound index cell component)
            l (nhds 0)) :
    Tendsto leftActualVariance l
        (nhds
          ((1 / leftDenominator ^ 2) * (1 / leftNormalizer) *
            weightedScoreCellMomentLimit leftCells
              (fun cell =>
                (leftContributionLimit cell -
                  leftTarget * leftWeightLimit cell) ^ 2)
              leftMassLimit)) ∧
      Tendsto rightActualVariance l
        (nhds
          ((1 / rightDenominator ^ 2) * (1 / rightNormalizer) *
            weightedScoreCellMomentLimit rightCells
              (fun cell =>
                (rightContributionLimit cell -
                  rightTarget * rightWeightLimit cell) ^ 2)
              rightMassLimit)) :=
  ⟨tendsto_actualBootstrapVariance_of_eventually_cell_contribution_weight_limits_and_finite_score_cell_bias_error_bounds
      (l := l) leftCells leftScoreComponents leftBiasComponents
      leftSample leftScore leftContribution leftWeight leftTarget
      leftDenominator leftNormalizer leftCellContribution leftCellWeight
      leftContributionLimit leftWeightLimit leftMassLimit leftActualVariance
      leftScoreReplicationError leftBiasCorrectionError
      leftScoreErrorComponent leftScoreErrorComponentBound
      leftBiasErrorComponent leftBiasErrorComponentBound hleft_error_decomp
      hleft_cover hleft_contributionCell hleft_weightCell
      hleft_contributionLimit hleft_weightLimit hleft_mass
      hleft_score_decomp hleft_score_component_bound
      hleft_score_component_bound_tendsto hleft_bias_decomp
      hleft_bias_component_bound hleft_bias_component_bound_tendsto,
    tendsto_actualBootstrapVariance_of_eventually_cell_contribution_weight_limits_and_finite_score_cell_bias_error_bounds
      (l := l) rightCells rightScoreComponents rightBiasComponents
      rightSample rightScore rightContribution rightWeight rightTarget
      rightDenominator rightNormalizer rightCellContribution rightCellWeight
      rightContributionLimit rightWeightLimit rightMassLimit
      rightActualVariance rightScoreReplicationError rightBiasCorrectionError
      rightScoreErrorComponent rightScoreErrorComponentBound
      rightBiasErrorComponent rightBiasErrorComponentBound
      hright_error_decomp hright_cover hright_contributionCell
      hright_weightCell hright_contributionLimit hright_weightLimit
      hright_mass hright_score_decomp hright_score_component_bound
      hright_score_component_bound_tendsto hright_bias_decomp
      hright_bias_component_bound hright_bias_component_bound_tendsto⟩

end WDSM
end Matching
end StatInference
