import Mathlib.Data.Finset.Basic
import Mathlib.Topology.Basic
import StatInference.Matching.WDSM.BootstrapFiniteAlgebraBridge
import StatInference.Matching.WDSM.BootstrapFiniteCellVarianceBridge

/-!
# Bootstrap finite-cell consistency bridge

This module composes two checked deterministic bootstrap layers:

* scenario-specific replicated-sum and replicated-ratio finite algebra, and
* finite-cell convergence of the centered-square bootstrap variance target.

The remaining bootstrap probability work is kept explicit as multiplier
regularity, score-replication consistency, bias-correction consistency, and a
transfer from the finite-cell centered-square convergence statement to the
scenario's conditional-variance convergence proposition.
-/

namespace StatInference
namespace Matching
namespace WDSM

open Filter
open scoped BigOperators

variable {Index Unit Cell : Type*} {l : Filter Index} [DecidableEq Cell]

/--
Generic bootstrap consistency route from checked finite algebra and checked
finite-cell centered-square variance convergence.
-/
theorem bootstrap_variance_consistency_of_finite_cell_variance
    (cells : Finset Cell)
    (sample : Index -> Finset Unit)
    (score : Index -> Unit -> Cell)
    (contribution weight : Index -> Unit -> Real)
    (target denominator normalizer : Real)
    (loading massLimit : Cell -> Real)
    (linearizedReplicateAlgebra multiplierWeightRegular
      bootstrapScoreReplicationConsistent bootstrapBiasCorrectionConsistent
      conditionalVarianceConvergence bootstrapVarianceConsistent : Prop)
    (bridge :
      linearizedReplicateAlgebra ->
        multiplierWeightRegular ->
        bootstrapScoreReplicationConsistent ->
        bootstrapBiasCorrectionConsistent ->
        conditionalVarianceConvergence ->
        bootstrapVarianceConsistent)
    (halgebra : linearizedReplicateAlgebra)
    (hcover :
      ∀ index unit, unit ∈ sample index -> score index unit ∈ cells)
    (hloading :
      ∀ index unit, unit ∈ sample index ->
        loading (score index unit) =
          (contribution index unit - target * weight index unit) ^ 2)
    (hmass :
      cellwiseScoreCellMassLLN (l := l) cells sample
        (fun _index _unit => 1) score massLimit)
    (hvariance_transfer :
      Tendsto
        (fun index =>
          bootstrapCenteredVarianceTarget (sample index)
            (contribution index) (weight index) target denominator normalizer)
        l
        (nhds
          ((1 / denominator ^ 2) * (1 / normalizer) *
            weightedScoreCellMomentLimit cells loading massLimit)) ->
      conditionalVarianceConvergence)
    (hmultiplier : multiplierWeightRegular)
    (hscore : bootstrapScoreReplicationConsistent)
    (hbias : bootstrapBiasCorrectionConsistent) :
    bootstrapVarianceConsistent :=
  bootstrap_variance_consistency_of_linearized_bridge
    { linearized_replicate_algebra_verified := linearizedReplicateAlgebra
      multiplier_weight_regular := multiplierWeightRegular
      bootstrap_score_replication_consistent :=
        bootstrapScoreReplicationConsistent
      bootstrap_bias_correction_consistent := bootstrapBiasCorrectionConsistent
      conditional_variance_convergence := conditionalVarianceConvergence
      bootstrap_variance_consistent := bootstrapVarianceConsistent
      bridge := bridge }
    halgebra hmultiplier hscore hbias
    (hvariance_transfer
      (tendsto_bootstrapCenteredVarianceTarget_of_cellwiseScoreCellMassLLN
        (l := l) cells sample score contribution weight target denominator
        normalizer loading massLimit hcover hloading hmass))

/--
Retrospective PATE bootstrap consistency from indexed finite algebra and
finite-cell centered-square variance convergence.
-/
theorem retrospective_pate_bootstrap_variance_consistency_of_indexed_finite_cell
    (cells : Finset Cell)
    (sample : Index -> Finset Unit)
    (multiplier baseWeight reuseResidualWeight heterogeneity residual :
      Index -> Unit -> Real)
    (score : Index -> Unit -> Cell)
    (target denominator normalizer : Real)
    (loading massLimit : Cell -> Real)
    (multiplierWeightRegular bootstrapScoreReplicationConsistent
      bootstrapBiasCorrectionConsistent conditionalVarianceConvergence
      bootstrapVarianceConsistent : Prop)
    (bridge :
      (∀ index,
        retrospectivePATEBootstrapFiniteAlgebraVerified (sample index)
          (multiplier index) (baseWeight index)
          (reuseResidualWeight index) (heterogeneity index)
          (residual index)) ->
        multiplierWeightRegular ->
        bootstrapScoreReplicationConsistent ->
        bootstrapBiasCorrectionConsistent ->
        conditionalVarianceConvergence ->
        bootstrapVarianceConsistent)
    (hcover :
      ∀ index unit, unit ∈ sample index -> score index unit ∈ cells)
    (hloading :
      ∀ index unit, unit ∈ sample index ->
        loading (score index unit) =
          (retrospectivePATEBootstrapInfluenceContribution
                (baseWeight index) (reuseResidualWeight index)
                (heterogeneity index) (residual index) unit -
              target * baseWeight index unit) ^ 2)
    (hmass :
      cellwiseScoreCellMassLLN (l := l) cells sample
        (fun _index _unit => 1) score massLimit)
    (hvariance_transfer :
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
            weightedScoreCellMomentLimit cells loading massLimit)) ->
      conditionalVarianceConvergence)
    (hmultiplier : multiplierWeightRegular)
    (hscore : bootstrapScoreReplicationConsistent)
    (hbias : bootstrapBiasCorrectionConsistent) :
    bootstrapVarianceConsistent :=
  bootstrap_variance_consistency_of_finite_cell_variance
    (l := l) cells sample score
    (fun index =>
      retrospectivePATEBootstrapInfluenceContribution (baseWeight index)
        (reuseResidualWeight index) (heterogeneity index) (residual index))
    baseWeight target denominator normalizer loading massLimit
    (∀ index,
      retrospectivePATEBootstrapFiniteAlgebraVerified (sample index)
        (multiplier index) (baseWeight index)
        (reuseResidualWeight index) (heterogeneity index) (residual index))
    multiplierWeightRegular bootstrapScoreReplicationConsistent
    bootstrapBiasCorrectionConsistent conditionalVarianceConvergence
    bootstrapVarianceConsistent bridge
    (fun index =>
      retrospectivePATEBootstrapFiniteAlgebraVerified_of_replicate_identities
        (sample index) (multiplier index) (baseWeight index)
        (reuseResidualWeight index) (heterogeneity index) (residual index))
    hcover hloading hmass hvariance_transfer hmultiplier hscore hbias

/--
Retrospective PATT bootstrap consistency from indexed finite algebra and
finite-cell centered-square variance convergence.
-/
theorem retrospective_patt_bootstrap_variance_consistency_of_indexed_finite_cell
    (cells : Finset Cell)
    (sample : Index -> Finset Unit)
    (multiplier denominatorWeight treatedContribution controlReuseContribution :
      Index -> Unit -> Real)
    (score : Index -> Unit -> Cell)
    (target denominator normalizer : Real)
    (loading massLimit : Cell -> Real)
    (multiplierWeightRegular bootstrapScoreReplicationConsistent
      bootstrapBiasCorrectionConsistent conditionalVarianceConvergence
      bootstrapVarianceConsistent : Prop)
    (bridge :
      (∀ index,
        retrospectivePATTBootstrapFiniteAlgebraVerified (sample index)
          (multiplier index) (denominatorWeight index)
          (treatedContribution index) (controlReuseContribution index)) ->
        multiplierWeightRegular ->
        bootstrapScoreReplicationConsistent ->
        bootstrapBiasCorrectionConsistent ->
        conditionalVarianceConvergence ->
        bootstrapVarianceConsistent)
    (hcover :
      ∀ index unit, unit ∈ sample index -> score index unit ∈ cells)
    (hloading :
      ∀ index unit, unit ∈ sample index ->
        loading (score index unit) =
          (retrospectivePATTBootstrapInfluenceContribution
                (treatedContribution index) (controlReuseContribution index)
                unit -
              target * denominatorWeight index unit) ^ 2)
    (hmass :
      cellwiseScoreCellMassLLN (l := l) cells sample
        (fun _index _unit => 1) score massLimit)
    (hvariance_transfer :
      Tendsto
        (fun index =>
          bootstrapCenteredVarianceTarget (sample index)
            (retrospectivePATTBootstrapInfluenceContribution
              (treatedContribution index) (controlReuseContribution index))
            (denominatorWeight index) target denominator normalizer)
        l
        (nhds
          ((1 / denominator ^ 2) * (1 / normalizer) *
            weightedScoreCellMomentLimit cells loading massLimit)) ->
      conditionalVarianceConvergence)
    (hmultiplier : multiplierWeightRegular)
    (hscore : bootstrapScoreReplicationConsistent)
    (hbias : bootstrapBiasCorrectionConsistent) :
    bootstrapVarianceConsistent :=
  bootstrap_variance_consistency_of_finite_cell_variance
    (l := l) cells sample score
    (fun index =>
      retrospectivePATTBootstrapInfluenceContribution
        (treatedContribution index) (controlReuseContribution index))
    denominatorWeight target denominator normalizer loading massLimit
    (∀ index,
      retrospectivePATTBootstrapFiniteAlgebraVerified (sample index)
        (multiplier index) (denominatorWeight index)
        (treatedContribution index) (controlReuseContribution index))
    multiplierWeightRegular bootstrapScoreReplicationConsistent
    bootstrapBiasCorrectionConsistent conditionalVarianceConvergence
    bootstrapVarianceConsistent bridge
    (fun index =>
      retrospectivePATTBootstrapFiniteAlgebraVerified_of_replicate_identities
        (sample index) (multiplier index) (denominatorWeight index)
        (treatedContribution index) (controlReuseContribution index))
    hcover hloading hmass hvariance_transfer hmultiplier hscore hbias

/--
Prospective PATE bootstrap consistency from indexed finite algebra and
finite-cell centered-square variance convergence.
-/
theorem prospective_pate_bootstrap_variance_consistency_of_indexed_finite_cell
    (cells : Finset Cell)
    (sample : Index -> Finset Unit)
    (multiplier baseWeight reuseResidualWeight heterogeneity residual :
      Index -> Unit -> Real)
    (score : Index -> Unit -> Cell)
    (target denominator normalizer : Real)
    (loading massLimit : Cell -> Real)
    (multiplierWeightRegular bootstrapScoreReplicationConsistent
      bootstrapBiasCorrectionConsistent conditionalVarianceConvergence
      bootstrapVarianceConsistent : Prop)
    (bridge :
      (∀ index,
        prospectivePATEBootstrapFiniteAlgebraVerified (sample index)
          (multiplier index) (baseWeight index)
          (reuseResidualWeight index) (heterogeneity index)
          (residual index)) ->
        multiplierWeightRegular ->
        bootstrapScoreReplicationConsistent ->
        bootstrapBiasCorrectionConsistent ->
        conditionalVarianceConvergence ->
        bootstrapVarianceConsistent)
    (hcover :
      ∀ index unit, unit ∈ sample index -> score index unit ∈ cells)
    (hloading :
      ∀ index unit, unit ∈ sample index ->
        loading (score index unit) =
          (prospectivePATEBootstrapInfluenceContribution
                (baseWeight index) (reuseResidualWeight index)
                (heterogeneity index) (residual index) unit -
              target * baseWeight index unit) ^ 2)
    (hmass :
      cellwiseScoreCellMassLLN (l := l) cells sample
        (fun _index _unit => 1) score massLimit)
    (hvariance_transfer :
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
            weightedScoreCellMomentLimit cells loading massLimit)) ->
      conditionalVarianceConvergence)
    (hmultiplier : multiplierWeightRegular)
    (hscore : bootstrapScoreReplicationConsistent)
    (hbias : bootstrapBiasCorrectionConsistent) :
    bootstrapVarianceConsistent :=
  bootstrap_variance_consistency_of_finite_cell_variance
    (l := l) cells sample score
    (fun index =>
      prospectivePATEBootstrapInfluenceContribution (baseWeight index)
        (reuseResidualWeight index) (heterogeneity index) (residual index))
    baseWeight target denominator normalizer loading massLimit
    (∀ index,
      prospectivePATEBootstrapFiniteAlgebraVerified (sample index)
        (multiplier index) (baseWeight index)
        (reuseResidualWeight index) (heterogeneity index) (residual index))
    multiplierWeightRegular bootstrapScoreReplicationConsistent
    bootstrapBiasCorrectionConsistent conditionalVarianceConvergence
    bootstrapVarianceConsistent bridge
    (fun index =>
      prospectivePATEBootstrapFiniteAlgebraVerified_of_replicate_identities
        (sample index) (multiplier index) (baseWeight index)
        (reuseResidualWeight index) (heterogeneity index) (residual index))
    hcover hloading hmass hvariance_transfer hmultiplier hscore hbias

/--
Prospective PATT bootstrap consistency from indexed finite algebra and
finite-cell centered-square variance convergence.
-/
theorem prospective_patt_bootstrap_variance_consistency_of_indexed_finite_cell
    (cells : Finset Cell)
    (sample : Index -> Finset Unit)
    (multiplier denominatorWeight treatedContribution controlReuseContribution :
      Index -> Unit -> Real)
    (score : Index -> Unit -> Cell)
    (target denominator normalizer : Real)
    (loading massLimit : Cell -> Real)
    (multiplierWeightRegular bootstrapScoreReplicationConsistent
      bootstrapBiasCorrectionConsistent conditionalVarianceConvergence
      bootstrapVarianceConsistent : Prop)
    (bridge :
      (∀ index,
        prospectivePATTBootstrapFiniteAlgebraVerified (sample index)
          (multiplier index) (denominatorWeight index)
          (treatedContribution index) (controlReuseContribution index)) ->
        multiplierWeightRegular ->
        bootstrapScoreReplicationConsistent ->
        bootstrapBiasCorrectionConsistent ->
        conditionalVarianceConvergence ->
        bootstrapVarianceConsistent)
    (hcover :
      ∀ index unit, unit ∈ sample index -> score index unit ∈ cells)
    (hloading :
      ∀ index unit, unit ∈ sample index ->
        loading (score index unit) =
          (prospectivePATTBootstrapInfluenceContribution
                (treatedContribution index) (controlReuseContribution index)
                unit -
              target * denominatorWeight index unit) ^ 2)
    (hmass :
      cellwiseScoreCellMassLLN (l := l) cells sample
        (fun _index _unit => 1) score massLimit)
    (hvariance_transfer :
      Tendsto
        (fun index =>
          bootstrapCenteredVarianceTarget (sample index)
            (prospectivePATTBootstrapInfluenceContribution
              (treatedContribution index) (controlReuseContribution index))
            (denominatorWeight index) target denominator normalizer)
        l
        (nhds
          ((1 / denominator ^ 2) * (1 / normalizer) *
            weightedScoreCellMomentLimit cells loading massLimit)) ->
      conditionalVarianceConvergence)
    (hmultiplier : multiplierWeightRegular)
    (hscore : bootstrapScoreReplicationConsistent)
    (hbias : bootstrapBiasCorrectionConsistent) :
    bootstrapVarianceConsistent :=
  bootstrap_variance_consistency_of_finite_cell_variance
    (l := l) cells sample score
    (fun index =>
      prospectivePATTBootstrapInfluenceContribution
        (treatedContribution index) (controlReuseContribution index))
    denominatorWeight target denominator normalizer loading massLimit
    (∀ index,
      prospectivePATTBootstrapFiniteAlgebraVerified (sample index)
        (multiplier index) (denominatorWeight index)
        (treatedContribution index) (controlReuseContribution index))
    multiplierWeightRegular bootstrapScoreReplicationConsistent
    bootstrapBiasCorrectionConsistent conditionalVarianceConvergence
    bootstrapVarianceConsistent bridge
    (fun index =>
      prospectivePATTBootstrapFiniteAlgebraVerified_of_replicate_identities
        (sample index) (multiplier index) (denominatorWeight index)
        (treatedContribution index) (controlReuseContribution index))
    hcover hloading hmass hvariance_transfer hmultiplier hscore hbias

/--
Paired retrospective PATE/PATT bootstrap consistency from indexed finite
algebra and finite-cell centered-square variance convergence.
-/
theorem retrospective_pate_patt_bootstrap_variance_consistency_of_indexed_finite_cell
    (pateCells : Finset Cell)
    (pateSample : Index -> Finset Unit)
    (pateMultiplier pateBaseWeight pateReuseResidualWeight pateHeterogeneity
      pateResidual : Index -> Unit -> Real)
    (pateScore : Index -> Unit -> Cell)
    (pateTarget pateDenominator pateNormalizer : Real)
    (pateLoading pateMassLimit : Cell -> Real)
    (pateMultiplierWeightRegular pateBootstrapScoreReplicationConsistent
      pateBootstrapBiasCorrectionConsistent
      pateConditionalVarianceConvergence
      pateBootstrapVarianceConsistent : Prop)
    (pateBridge :
      (∀ index,
        retrospectivePATEBootstrapFiniteAlgebraVerified (pateSample index)
          (pateMultiplier index) (pateBaseWeight index)
          (pateReuseResidualWeight index) (pateHeterogeneity index)
          (pateResidual index)) ->
        pateMultiplierWeightRegular ->
        pateBootstrapScoreReplicationConsistent ->
        pateBootstrapBiasCorrectionConsistent ->
        pateConditionalVarianceConvergence ->
        pateBootstrapVarianceConsistent)
    (hpateCover :
      ∀ index unit, unit ∈ pateSample index ->
        pateScore index unit ∈ pateCells)
    (hpateLoading :
      ∀ index unit, unit ∈ pateSample index ->
        pateLoading (pateScore index unit) =
          (retrospectivePATEBootstrapInfluenceContribution
                (pateBaseWeight index) (pateReuseResidualWeight index)
                (pateHeterogeneity index) (pateResidual index) unit -
              pateTarget * pateBaseWeight index unit) ^ 2)
    (hpateMass :
      cellwiseScoreCellMassLLN (l := l) pateCells pateSample
        (fun _index _unit => 1) pateScore pateMassLimit)
    (hpateVarianceTransfer :
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
            weightedScoreCellMomentLimit pateCells pateLoading
              pateMassLimit)) ->
      pateConditionalVarianceConvergence)
    (hpateMultiplier : pateMultiplierWeightRegular)
    (hpateScore : pateBootstrapScoreReplicationConsistent)
    (hpateBias : pateBootstrapBiasCorrectionConsistent)
    (pattCells : Finset Cell)
    (pattSample : Index -> Finset Unit)
    (pattMultiplier pattDenominatorWeight pattTreatedContribution
      pattControlReuseContribution : Index -> Unit -> Real)
    (pattScore : Index -> Unit -> Cell)
    (pattTarget pattDenominator pattNormalizer : Real)
    (pattLoading pattMassLimit : Cell -> Real)
    (pattMultiplierWeightRegular pattBootstrapScoreReplicationConsistent
      pattBootstrapBiasCorrectionConsistent
      pattConditionalVarianceConvergence
      pattBootstrapVarianceConsistent : Prop)
    (pattBridge :
      (∀ index,
        retrospectivePATTBootstrapFiniteAlgebraVerified (pattSample index)
          (pattMultiplier index) (pattDenominatorWeight index)
          (pattTreatedContribution index)
          (pattControlReuseContribution index)) ->
        pattMultiplierWeightRegular ->
        pattBootstrapScoreReplicationConsistent ->
        pattBootstrapBiasCorrectionConsistent ->
        pattConditionalVarianceConvergence ->
        pattBootstrapVarianceConsistent)
    (hpattCover :
      ∀ index unit, unit ∈ pattSample index ->
        pattScore index unit ∈ pattCells)
    (hpattLoading :
      ∀ index unit, unit ∈ pattSample index ->
        pattLoading (pattScore index unit) =
          (retrospectivePATTBootstrapInfluenceContribution
                (pattTreatedContribution index)
                (pattControlReuseContribution index) unit -
              pattTarget * pattDenominatorWeight index unit) ^ 2)
    (hpattMass :
      cellwiseScoreCellMassLLN (l := l) pattCells pattSample
        (fun _index _unit => 1) pattScore pattMassLimit)
    (hpattVarianceTransfer :
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
            weightedScoreCellMomentLimit pattCells pattLoading
              pattMassLimit)) ->
      pattConditionalVarianceConvergence)
    (hpattMultiplier : pattMultiplierWeightRegular)
    (hpattScore : pattBootstrapScoreReplicationConsistent)
    (hpattBias : pattBootstrapBiasCorrectionConsistent) :
    pateBootstrapVarianceConsistent ∧ pattBootstrapVarianceConsistent :=
  ⟨retrospective_pate_bootstrap_variance_consistency_of_indexed_finite_cell
      (l := l) pateCells pateSample pateMultiplier pateBaseWeight
      pateReuseResidualWeight pateHeterogeneity pateResidual pateScore
      pateTarget pateDenominator pateNormalizer pateLoading pateMassLimit
      pateMultiplierWeightRegular pateBootstrapScoreReplicationConsistent
      pateBootstrapBiasCorrectionConsistent
      pateConditionalVarianceConvergence pateBootstrapVarianceConsistent
      pateBridge hpateCover hpateLoading hpateMass hpateVarianceTransfer
      hpateMultiplier hpateScore hpateBias,
    retrospective_patt_bootstrap_variance_consistency_of_indexed_finite_cell
      (l := l) pattCells pattSample pattMultiplier pattDenominatorWeight
      pattTreatedContribution pattControlReuseContribution pattScore
      pattTarget pattDenominator pattNormalizer pattLoading pattMassLimit
      pattMultiplierWeightRegular pattBootstrapScoreReplicationConsistent
      pattBootstrapBiasCorrectionConsistent
      pattConditionalVarianceConvergence pattBootstrapVarianceConsistent
      pattBridge hpattCover hpattLoading hpattMass hpattVarianceTransfer
      hpattMultiplier hpattScore hpattBias⟩

/--
Paired prospective PATE/PATT bootstrap consistency from indexed finite
algebra and finite-cell centered-square variance convergence.
-/
theorem prospective_pate_patt_bootstrap_variance_consistency_of_indexed_finite_cell
    (pateCells : Finset Cell)
    (pateSample : Index -> Finset Unit)
    (pateMultiplier pateBaseWeight pateReuseResidualWeight pateHeterogeneity
      pateResidual : Index -> Unit -> Real)
    (pateScore : Index -> Unit -> Cell)
    (pateTarget pateDenominator pateNormalizer : Real)
    (pateLoading pateMassLimit : Cell -> Real)
    (pateMultiplierWeightRegular pateBootstrapScoreReplicationConsistent
      pateBootstrapBiasCorrectionConsistent
      pateConditionalVarianceConvergence
      pateBootstrapVarianceConsistent : Prop)
    (pateBridge :
      (∀ index,
        prospectivePATEBootstrapFiniteAlgebraVerified (pateSample index)
          (pateMultiplier index) (pateBaseWeight index)
          (pateReuseResidualWeight index) (pateHeterogeneity index)
          (pateResidual index)) ->
        pateMultiplierWeightRegular ->
        pateBootstrapScoreReplicationConsistent ->
        pateBootstrapBiasCorrectionConsistent ->
        pateConditionalVarianceConvergence ->
        pateBootstrapVarianceConsistent)
    (hpateCover :
      ∀ index unit, unit ∈ pateSample index ->
        pateScore index unit ∈ pateCells)
    (hpateLoading :
      ∀ index unit, unit ∈ pateSample index ->
        pateLoading (pateScore index unit) =
          (prospectivePATEBootstrapInfluenceContribution
                (pateBaseWeight index) (pateReuseResidualWeight index)
                (pateHeterogeneity index) (pateResidual index) unit -
              pateTarget * pateBaseWeight index unit) ^ 2)
    (hpateMass :
      cellwiseScoreCellMassLLN (l := l) pateCells pateSample
        (fun _index _unit => 1) pateScore pateMassLimit)
    (hpateVarianceTransfer :
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
            weightedScoreCellMomentLimit pateCells pateLoading
              pateMassLimit)) ->
      pateConditionalVarianceConvergence)
    (hpateMultiplier : pateMultiplierWeightRegular)
    (hpateScore : pateBootstrapScoreReplicationConsistent)
    (hpateBias : pateBootstrapBiasCorrectionConsistent)
    (pattCells : Finset Cell)
    (pattSample : Index -> Finset Unit)
    (pattMultiplier pattDenominatorWeight pattTreatedContribution
      pattControlReuseContribution : Index -> Unit -> Real)
    (pattScore : Index -> Unit -> Cell)
    (pattTarget pattDenominator pattNormalizer : Real)
    (pattLoading pattMassLimit : Cell -> Real)
    (pattMultiplierWeightRegular pattBootstrapScoreReplicationConsistent
      pattBootstrapBiasCorrectionConsistent
      pattConditionalVarianceConvergence
      pattBootstrapVarianceConsistent : Prop)
    (pattBridge :
      (∀ index,
        prospectivePATTBootstrapFiniteAlgebraVerified (pattSample index)
          (pattMultiplier index) (pattDenominatorWeight index)
          (pattTreatedContribution index)
          (pattControlReuseContribution index)) ->
        pattMultiplierWeightRegular ->
        pattBootstrapScoreReplicationConsistent ->
        pattBootstrapBiasCorrectionConsistent ->
        pattConditionalVarianceConvergence ->
        pattBootstrapVarianceConsistent)
    (hpattCover :
      ∀ index unit, unit ∈ pattSample index ->
        pattScore index unit ∈ pattCells)
    (hpattLoading :
      ∀ index unit, unit ∈ pattSample index ->
        pattLoading (pattScore index unit) =
          (prospectivePATTBootstrapInfluenceContribution
                (pattTreatedContribution index)
                (pattControlReuseContribution index) unit -
              pattTarget * pattDenominatorWeight index unit) ^ 2)
    (hpattMass :
      cellwiseScoreCellMassLLN (l := l) pattCells pattSample
        (fun _index _unit => 1) pattScore pattMassLimit)
    (hpattVarianceTransfer :
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
            weightedScoreCellMomentLimit pattCells pattLoading
              pattMassLimit)) ->
      pattConditionalVarianceConvergence)
    (hpattMultiplier : pattMultiplierWeightRegular)
    (hpattScore : pattBootstrapScoreReplicationConsistent)
    (hpattBias : pattBootstrapBiasCorrectionConsistent) :
    pateBootstrapVarianceConsistent ∧ pattBootstrapVarianceConsistent :=
  ⟨prospective_pate_bootstrap_variance_consistency_of_indexed_finite_cell
      (l := l) pateCells pateSample pateMultiplier pateBaseWeight
      pateReuseResidualWeight pateHeterogeneity pateResidual pateScore
      pateTarget pateDenominator pateNormalizer pateLoading pateMassLimit
      pateMultiplierWeightRegular pateBootstrapScoreReplicationConsistent
      pateBootstrapBiasCorrectionConsistent
      pateConditionalVarianceConvergence pateBootstrapVarianceConsistent
      pateBridge hpateCover hpateLoading hpateMass hpateVarianceTransfer
      hpateMultiplier hpateScore hpateBias,
    prospective_patt_bootstrap_variance_consistency_of_indexed_finite_cell
      (l := l) pattCells pattSample pattMultiplier pattDenominatorWeight
      pattTreatedContribution pattControlReuseContribution pattScore
      pattTarget pattDenominator pattNormalizer pattLoading pattMassLimit
      pattMultiplierWeightRegular pattBootstrapScoreReplicationConsistent
      pattBootstrapBiasCorrectionConsistent
      pattConditionalVarianceConvergence pattBootstrapVarianceConsistent
      pattBridge hpattCover hpattLoading hpattMass hpattVarianceTransfer
      hpattMultiplier hpattScore hpattBias⟩

/--
Direct generic variant where the bridge's conditional-variance premise is
exactly the finite-cell centered-square convergence statement.
-/
theorem bootstrap_variance_consistency_of_finite_cell_variance_direct
    (cells : Finset Cell)
    (sample : Index -> Finset Unit)
    (score : Index -> Unit -> Cell)
    (contribution weight : Index -> Unit -> Real)
    (target denominator normalizer : Real)
    (loading massLimit : Cell -> Real)
    (linearizedReplicateAlgebra multiplierWeightRegular
      bootstrapScoreReplicationConsistent bootstrapBiasCorrectionConsistent
      bootstrapVarianceConsistent : Prop)
    (bridge :
      linearizedReplicateAlgebra ->
        multiplierWeightRegular ->
        bootstrapScoreReplicationConsistent ->
        bootstrapBiasCorrectionConsistent ->
        Tendsto
          (fun index =>
            bootstrapCenteredVarianceTarget (sample index)
              (contribution index) (weight index) target denominator
              normalizer)
          l
          (nhds
            ((1 / denominator ^ 2) * (1 / normalizer) *
              weightedScoreCellMomentLimit cells loading massLimit)) ->
        bootstrapVarianceConsistent)
    (halgebra : linearizedReplicateAlgebra)
    (hcover :
      ∀ index unit, unit ∈ sample index -> score index unit ∈ cells)
    (hloading :
      ∀ index unit, unit ∈ sample index ->
        loading (score index unit) =
          (contribution index unit - target * weight index unit) ^ 2)
    (hmass :
      cellwiseScoreCellMassLLN (l := l) cells sample
        (fun _index _unit => 1) score massLimit)
    (hmultiplier : multiplierWeightRegular)
    (hscore : bootstrapScoreReplicationConsistent)
    (hbias : bootstrapBiasCorrectionConsistent) :
    bootstrapVarianceConsistent :=
  bootstrap_variance_consistency_of_finite_cell_variance
    (l := l) cells sample score contribution weight target denominator
    normalizer loading massLimit linearizedReplicateAlgebra
    multiplierWeightRegular bootstrapScoreReplicationConsistent
    bootstrapBiasCorrectionConsistent
    (Tendsto
      (fun index =>
        bootstrapCenteredVarianceTarget (sample index)
          (contribution index) (weight index) target denominator normalizer)
      l
      (nhds
        ((1 / denominator ^ 2) * (1 / normalizer) *
          weightedScoreCellMomentLimit cells loading massLimit)))
    bootstrapVarianceConsistent bridge halgebra hcover hloading hmass
    (fun h => h) hmultiplier hscore hbias

/--
Direct retrospective PATE bootstrap consistency when the bridge consumes the
finite-cell centered-square convergence statement itself.
-/
theorem retrospective_pate_bootstrap_variance_consistency_of_indexed_finite_cell_direct
    (cells : Finset Cell)
    (sample : Index -> Finset Unit)
    (multiplier baseWeight reuseResidualWeight heterogeneity residual :
      Index -> Unit -> Real)
    (score : Index -> Unit -> Cell)
    (target denominator normalizer : Real)
    (loading massLimit : Cell -> Real)
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
              weightedScoreCellMomentLimit cells loading massLimit)) ->
        bootstrapVarianceConsistent)
    (hcover :
      ∀ index unit, unit ∈ sample index -> score index unit ∈ cells)
    (hloading :
      ∀ index unit, unit ∈ sample index ->
        loading (score index unit) =
          (retrospectivePATEBootstrapInfluenceContribution
                (baseWeight index) (reuseResidualWeight index)
                (heterogeneity index) (residual index) unit -
              target * baseWeight index unit) ^ 2)
    (hmass :
      cellwiseScoreCellMassLLN (l := l) cells sample
        (fun _index _unit => 1) score massLimit)
    (hmultiplier : multiplierWeightRegular)
    (hscore : bootstrapScoreReplicationConsistent)
    (hbias : bootstrapBiasCorrectionConsistent) :
    bootstrapVarianceConsistent :=
  bootstrap_variance_consistency_of_finite_cell_variance_direct
    (l := l) cells sample score
    (fun index =>
      retrospectivePATEBootstrapInfluenceContribution (baseWeight index)
        (reuseResidualWeight index) (heterogeneity index) (residual index))
    baseWeight target denominator normalizer loading massLimit
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
    hcover hloading hmass hmultiplier hscore hbias

/--
Direct retrospective PATT bootstrap consistency when the bridge consumes the
finite-cell centered-square convergence statement itself.
-/
theorem retrospective_patt_bootstrap_variance_consistency_of_indexed_finite_cell_direct
    (cells : Finset Cell)
    (sample : Index -> Finset Unit)
    (multiplier denominatorWeight treatedContribution controlReuseContribution :
      Index -> Unit -> Real)
    (score : Index -> Unit -> Cell)
    (target denominator normalizer : Real)
    (loading massLimit : Cell -> Real)
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
              weightedScoreCellMomentLimit cells loading massLimit)) ->
        bootstrapVarianceConsistent)
    (hcover :
      ∀ index unit, unit ∈ sample index -> score index unit ∈ cells)
    (hloading :
      ∀ index unit, unit ∈ sample index ->
        loading (score index unit) =
          (retrospectivePATTBootstrapInfluenceContribution
                (treatedContribution index) (controlReuseContribution index)
                unit -
              target * denominatorWeight index unit) ^ 2)
    (hmass :
      cellwiseScoreCellMassLLN (l := l) cells sample
        (fun _index _unit => 1) score massLimit)
    (hmultiplier : multiplierWeightRegular)
    (hscore : bootstrapScoreReplicationConsistent)
    (hbias : bootstrapBiasCorrectionConsistent) :
    bootstrapVarianceConsistent :=
  bootstrap_variance_consistency_of_finite_cell_variance_direct
    (l := l) cells sample score
    (fun index =>
      retrospectivePATTBootstrapInfluenceContribution
        (treatedContribution index) (controlReuseContribution index))
    denominatorWeight target denominator normalizer loading massLimit
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
    hcover hloading hmass hmultiplier hscore hbias

/--
Direct prospective PATE bootstrap consistency when the bridge consumes the
finite-cell centered-square convergence statement itself.
-/
theorem prospective_pate_bootstrap_variance_consistency_of_indexed_finite_cell_direct
    (cells : Finset Cell)
    (sample : Index -> Finset Unit)
    (multiplier baseWeight reuseResidualWeight heterogeneity residual :
      Index -> Unit -> Real)
    (score : Index -> Unit -> Cell)
    (target denominator normalizer : Real)
    (loading massLimit : Cell -> Real)
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
              weightedScoreCellMomentLimit cells loading massLimit)) ->
        bootstrapVarianceConsistent)
    (hcover :
      ∀ index unit, unit ∈ sample index -> score index unit ∈ cells)
    (hloading :
      ∀ index unit, unit ∈ sample index ->
        loading (score index unit) =
          (prospectivePATEBootstrapInfluenceContribution
                (baseWeight index) (reuseResidualWeight index)
                (heterogeneity index) (residual index) unit -
              target * baseWeight index unit) ^ 2)
    (hmass :
      cellwiseScoreCellMassLLN (l := l) cells sample
        (fun _index _unit => 1) score massLimit)
    (hmultiplier : multiplierWeightRegular)
    (hscore : bootstrapScoreReplicationConsistent)
    (hbias : bootstrapBiasCorrectionConsistent) :
    bootstrapVarianceConsistent :=
  bootstrap_variance_consistency_of_finite_cell_variance_direct
    (l := l) cells sample score
    (fun index =>
      prospectivePATEBootstrapInfluenceContribution (baseWeight index)
        (reuseResidualWeight index) (heterogeneity index) (residual index))
    baseWeight target denominator normalizer loading massLimit
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
    hcover hloading hmass hmultiplier hscore hbias

/--
Direct prospective PATT bootstrap consistency when the bridge consumes the
finite-cell centered-square convergence statement itself.
-/
theorem prospective_patt_bootstrap_variance_consistency_of_indexed_finite_cell_direct
    (cells : Finset Cell)
    (sample : Index -> Finset Unit)
    (multiplier denominatorWeight treatedContribution controlReuseContribution :
      Index -> Unit -> Real)
    (score : Index -> Unit -> Cell)
    (target denominator normalizer : Real)
    (loading massLimit : Cell -> Real)
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
              weightedScoreCellMomentLimit cells loading massLimit)) ->
        bootstrapVarianceConsistent)
    (hcover :
      ∀ index unit, unit ∈ sample index -> score index unit ∈ cells)
    (hloading :
      ∀ index unit, unit ∈ sample index ->
        loading (score index unit) =
          (prospectivePATTBootstrapInfluenceContribution
                (treatedContribution index) (controlReuseContribution index)
                unit -
              target * denominatorWeight index unit) ^ 2)
    (hmass :
      cellwiseScoreCellMassLLN (l := l) cells sample
        (fun _index _unit => 1) score massLimit)
    (hmultiplier : multiplierWeightRegular)
    (hscore : bootstrapScoreReplicationConsistent)
    (hbias : bootstrapBiasCorrectionConsistent) :
    bootstrapVarianceConsistent :=
  bootstrap_variance_consistency_of_finite_cell_variance_direct
    (l := l) cells sample score
    (fun index =>
      prospectivePATTBootstrapInfluenceContribution
        (treatedContribution index) (controlReuseContribution index))
    denominatorWeight target denominator normalizer loading massLimit
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
    hcover hloading hmass hmultiplier hscore hbias

/--
Paired retrospective PATE/PATT direct bootstrap consistency from indexed
finite-cell centered-square variance convergence.
-/
theorem retrospective_pate_patt_bootstrap_variance_consistency_of_indexed_finite_cell_direct
    (pateCells : Finset Cell)
    (pateSample : Index -> Finset Unit)
    (pateMultiplier pateBaseWeight pateReuseResidualWeight pateHeterogeneity
      pateResidual : Index -> Unit -> Real)
    (pateScore : Index -> Unit -> Cell)
    (pateTarget pateDenominator pateNormalizer : Real)
    (pateLoading pateMassLimit : Cell -> Real)
    (pateMultiplierWeightRegular pateBootstrapScoreReplicationConsistent
      pateBootstrapBiasCorrectionConsistent
      pateBootstrapVarianceConsistent : Prop)
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
              weightedScoreCellMomentLimit pateCells pateLoading
                pateMassLimit)) ->
        pateBootstrapVarianceConsistent)
    (hpateCover :
      ∀ index unit, unit ∈ pateSample index ->
        pateScore index unit ∈ pateCells)
    (hpateLoading :
      ∀ index unit, unit ∈ pateSample index ->
        pateLoading (pateScore index unit) =
          (retrospectivePATEBootstrapInfluenceContribution
                (pateBaseWeight index) (pateReuseResidualWeight index)
                (pateHeterogeneity index) (pateResidual index) unit -
              pateTarget * pateBaseWeight index unit) ^ 2)
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
    (pattLoading pattMassLimit : Cell -> Real)
    (pattMultiplierWeightRegular pattBootstrapScoreReplicationConsistent
      pattBootstrapBiasCorrectionConsistent
      pattBootstrapVarianceConsistent : Prop)
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
              weightedScoreCellMomentLimit pattCells pattLoading
                pattMassLimit)) ->
        pattBootstrapVarianceConsistent)
    (hpattCover :
      ∀ index unit, unit ∈ pattSample index ->
        pattScore index unit ∈ pattCells)
    (hpattLoading :
      ∀ index unit, unit ∈ pattSample index ->
        pattLoading (pattScore index unit) =
          (retrospectivePATTBootstrapInfluenceContribution
                (pattTreatedContribution index)
                (pattControlReuseContribution index) unit -
              pattTarget * pattDenominatorWeight index unit) ^ 2)
    (hpattMass :
      cellwiseScoreCellMassLLN (l := l) pattCells pattSample
        (fun _index _unit => 1) pattScore pattMassLimit)
    (hpattMultiplier : pattMultiplierWeightRegular)
    (hpattScore : pattBootstrapScoreReplicationConsistent)
    (hpattBias : pattBootstrapBiasCorrectionConsistent) :
    pateBootstrapVarianceConsistent ∧ pattBootstrapVarianceConsistent :=
  ⟨retrospective_pate_bootstrap_variance_consistency_of_indexed_finite_cell_direct
      (l := l) pateCells pateSample pateMultiplier pateBaseWeight
      pateReuseResidualWeight pateHeterogeneity pateResidual pateScore
      pateTarget pateDenominator pateNormalizer pateLoading pateMassLimit
      pateMultiplierWeightRegular pateBootstrapScoreReplicationConsistent
      pateBootstrapBiasCorrectionConsistent pateBootstrapVarianceConsistent
      pateBridge hpateCover hpateLoading hpateMass hpateMultiplier hpateScore
      hpateBias,
    retrospective_patt_bootstrap_variance_consistency_of_indexed_finite_cell_direct
      (l := l) pattCells pattSample pattMultiplier pattDenominatorWeight
      pattTreatedContribution pattControlReuseContribution pattScore
      pattTarget pattDenominator pattNormalizer pattLoading pattMassLimit
      pattMultiplierWeightRegular pattBootstrapScoreReplicationConsistent
      pattBootstrapBiasCorrectionConsistent pattBootstrapVarianceConsistent
      pattBridge hpattCover hpattLoading hpattMass hpattMultiplier hpattScore
      hpattBias⟩

/--
Paired prospective PATE/PATT direct bootstrap consistency from indexed
finite-cell centered-square variance convergence.
-/
theorem prospective_pate_patt_bootstrap_variance_consistency_of_indexed_finite_cell_direct
    (pateCells : Finset Cell)
    (pateSample : Index -> Finset Unit)
    (pateMultiplier pateBaseWeight pateReuseResidualWeight pateHeterogeneity
      pateResidual : Index -> Unit -> Real)
    (pateScore : Index -> Unit -> Cell)
    (pateTarget pateDenominator pateNormalizer : Real)
    (pateLoading pateMassLimit : Cell -> Real)
    (pateMultiplierWeightRegular pateBootstrapScoreReplicationConsistent
      pateBootstrapBiasCorrectionConsistent
      pateBootstrapVarianceConsistent : Prop)
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
              weightedScoreCellMomentLimit pateCells pateLoading
                pateMassLimit)) ->
        pateBootstrapVarianceConsistent)
    (hpateCover :
      ∀ index unit, unit ∈ pateSample index ->
        pateScore index unit ∈ pateCells)
    (hpateLoading :
      ∀ index unit, unit ∈ pateSample index ->
        pateLoading (pateScore index unit) =
          (prospectivePATEBootstrapInfluenceContribution
                (pateBaseWeight index) (pateReuseResidualWeight index)
                (pateHeterogeneity index) (pateResidual index) unit -
              pateTarget * pateBaseWeight index unit) ^ 2)
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
    (pattLoading pattMassLimit : Cell -> Real)
    (pattMultiplierWeightRegular pattBootstrapScoreReplicationConsistent
      pattBootstrapBiasCorrectionConsistent
      pattBootstrapVarianceConsistent : Prop)
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
              weightedScoreCellMomentLimit pattCells pattLoading
                pattMassLimit)) ->
        pattBootstrapVarianceConsistent)
    (hpattCover :
      ∀ index unit, unit ∈ pattSample index ->
        pattScore index unit ∈ pattCells)
    (hpattLoading :
      ∀ index unit, unit ∈ pattSample index ->
        pattLoading (pattScore index unit) =
          (prospectivePATTBootstrapInfluenceContribution
                (pattTreatedContribution index)
                (pattControlReuseContribution index) unit -
              pattTarget * pattDenominatorWeight index unit) ^ 2)
    (hpattMass :
      cellwiseScoreCellMassLLN (l := l) pattCells pattSample
        (fun _index _unit => 1) pattScore pattMassLimit)
    (hpattMultiplier : pattMultiplierWeightRegular)
    (hpattScore : pattBootstrapScoreReplicationConsistent)
    (hpattBias : pattBootstrapBiasCorrectionConsistent) :
    pateBootstrapVarianceConsistent ∧ pattBootstrapVarianceConsistent :=
  ⟨prospective_pate_bootstrap_variance_consistency_of_indexed_finite_cell_direct
      (l := l) pateCells pateSample pateMultiplier pateBaseWeight
      pateReuseResidualWeight pateHeterogeneity pateResidual pateScore
      pateTarget pateDenominator pateNormalizer pateLoading pateMassLimit
      pateMultiplierWeightRegular pateBootstrapScoreReplicationConsistent
      pateBootstrapBiasCorrectionConsistent pateBootstrapVarianceConsistent
      pateBridge hpateCover hpateLoading hpateMass hpateMultiplier hpateScore
      hpateBias,
    prospective_patt_bootstrap_variance_consistency_of_indexed_finite_cell_direct
      (l := l) pattCells pattSample pattMultiplier pattDenominatorWeight
      pattTreatedContribution pattControlReuseContribution pattScore
      pattTarget pattDenominator pattNormalizer pattLoading pattMassLimit
      pattMultiplierWeightRegular pattBootstrapScoreReplicationConsistent
      pattBootstrapBiasCorrectionConsistent pattBootstrapVarianceConsistent
      pattBridge hpattCover hpattLoading hpattMass hpattMultiplier hpattScore
      hpattBias⟩

/--
Direct generic bootstrap consistency route with index-dependent finite-cell
centered-square loadings.
-/
theorem bootstrap_variance_consistency_of_finite_cell_varying_variance_direct
    (cells : Finset Cell)
    (sample : Index -> Finset Unit)
    (score : Index -> Unit -> Cell)
    (contribution weight : Index -> Unit -> Real)
    (target denominator normalizer : Real)
    (loading : Index -> Cell -> Real)
    (loadingLimit massLimit : Cell -> Real)
    (linearizedReplicateAlgebra multiplierWeightRegular
      bootstrapScoreReplicationConsistent bootstrapBiasCorrectionConsistent
      bootstrapVarianceConsistent : Prop)
    (bridge :
      linearizedReplicateAlgebra ->
        multiplierWeightRegular ->
        bootstrapScoreReplicationConsistent ->
        bootstrapBiasCorrectionConsistent ->
        Tendsto
          (fun index =>
            bootstrapCenteredVarianceTarget (sample index)
              (contribution index) (weight index) target denominator
              normalizer)
          l
          (nhds
            ((1 / denominator ^ 2) * (1 / normalizer) *
              weightedScoreCellMomentLimit cells loadingLimit massLimit)) ->
        bootstrapVarianceConsistent)
    (halgebra : linearizedReplicateAlgebra)
    (hcover :
      ∀ index unit, unit ∈ sample index -> score index unit ∈ cells)
    (hloading :
      ∀ index unit, unit ∈ sample index ->
        loading index (score index unit) =
          (contribution index unit - target * weight index unit) ^ 2)
    (hloadingLimit :
      ∀ cell, cell ∈ cells ->
        Tendsto (fun index => loading index cell)
          l (nhds (loadingLimit cell)))
    (hmass :
      cellwiseScoreCellMassLLN (l := l) cells sample
        (fun _index _unit => 1) score massLimit)
    (hmultiplier : multiplierWeightRegular)
    (hscore : bootstrapScoreReplicationConsistent)
    (hbias : bootstrapBiasCorrectionConsistent) :
    bootstrapVarianceConsistent :=
  bootstrap_variance_consistency_of_linearized_bridge
    { linearized_replicate_algebra_verified := linearizedReplicateAlgebra
      multiplier_weight_regular := multiplierWeightRegular
      bootstrap_score_replication_consistent :=
        bootstrapScoreReplicationConsistent
      bootstrap_bias_correction_consistent := bootstrapBiasCorrectionConsistent
      conditional_variance_convergence :=
        Tendsto
          (fun index =>
            bootstrapCenteredVarianceTarget (sample index)
              (contribution index) (weight index) target denominator
              normalizer)
          l
          (nhds
            ((1 / denominator ^ 2) * (1 / normalizer) *
              weightedScoreCellMomentLimit cells loadingLimit massLimit))
      bootstrap_variance_consistent := bootstrapVarianceConsistent
      bridge := bridge }
    halgebra hmultiplier hscore hbias
    (tendsto_bootstrapCenteredVarianceTarget_of_cellwiseScoreCellMassLLN_of_tendsto_loading
      (l := l) cells sample score contribution weight target denominator
      normalizer loading loadingLimit massLimit hcover hloading
      hloadingLimit hmass)

/--
Retrospective PATE bootstrap consistency with index-dependent finite-cell
centered-square loadings.
-/
theorem retrospective_pate_bootstrap_variance_consistency_of_indexed_varying_finite_cell_direct
    (cells : Finset Cell)
    (sample : Index -> Finset Unit)
    (multiplier baseWeight reuseResidualWeight heterogeneity residual :
      Index -> Unit -> Real)
    (score : Index -> Unit -> Cell)
    (target denominator normalizer : Real)
    (loading : Index -> Cell -> Real)
    (loadingLimit massLimit : Cell -> Real)
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
              weightedScoreCellMomentLimit cells loadingLimit massLimit)) ->
        bootstrapVarianceConsistent)
    (hcover :
      ∀ index unit, unit ∈ sample index -> score index unit ∈ cells)
    (hloading :
      ∀ index unit, unit ∈ sample index ->
        loading index (score index unit) =
          (retrospectivePATEBootstrapInfluenceContribution
                (baseWeight index) (reuseResidualWeight index)
                (heterogeneity index) (residual index) unit -
              target * baseWeight index unit) ^ 2)
    (hloadingLimit :
      ∀ cell, cell ∈ cells ->
        Tendsto (fun index => loading index cell)
          l (nhds (loadingLimit cell)))
    (hmass :
      cellwiseScoreCellMassLLN (l := l) cells sample
        (fun _index _unit => 1) score massLimit)
    (hmultiplier : multiplierWeightRegular)
    (hscore : bootstrapScoreReplicationConsistent)
    (hbias : bootstrapBiasCorrectionConsistent) :
    bootstrapVarianceConsistent :=
  bootstrap_variance_consistency_of_finite_cell_varying_variance_direct
    (l := l) cells sample score
    (fun index =>
      retrospectivePATEBootstrapInfluenceContribution (baseWeight index)
        (reuseResidualWeight index) (heterogeneity index) (residual index))
    baseWeight target denominator normalizer loading loadingLimit massLimit
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
    hcover hloading hloadingLimit hmass hmultiplier hscore hbias

/--
Retrospective PATT bootstrap consistency with index-dependent finite-cell
centered-square loadings.
-/
theorem retrospective_patt_bootstrap_variance_consistency_of_indexed_varying_finite_cell_direct
    (cells : Finset Cell)
    (sample : Index -> Finset Unit)
    (multiplier denominatorWeight treatedContribution controlReuseContribution :
      Index -> Unit -> Real)
    (score : Index -> Unit -> Cell)
    (target denominator normalizer : Real)
    (loading : Index -> Cell -> Real)
    (loadingLimit massLimit : Cell -> Real)
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
              weightedScoreCellMomentLimit cells loadingLimit massLimit)) ->
        bootstrapVarianceConsistent)
    (hcover :
      ∀ index unit, unit ∈ sample index -> score index unit ∈ cells)
    (hloading :
      ∀ index unit, unit ∈ sample index ->
        loading index (score index unit) =
          (retrospectivePATTBootstrapInfluenceContribution
                (treatedContribution index) (controlReuseContribution index)
                unit -
              target * denominatorWeight index unit) ^ 2)
    (hloadingLimit :
      ∀ cell, cell ∈ cells ->
        Tendsto (fun index => loading index cell)
          l (nhds (loadingLimit cell)))
    (hmass :
      cellwiseScoreCellMassLLN (l := l) cells sample
        (fun _index _unit => 1) score massLimit)
    (hmultiplier : multiplierWeightRegular)
    (hscore : bootstrapScoreReplicationConsistent)
    (hbias : bootstrapBiasCorrectionConsistent) :
    bootstrapVarianceConsistent :=
  bootstrap_variance_consistency_of_finite_cell_varying_variance_direct
    (l := l) cells sample score
    (fun index =>
      retrospectivePATTBootstrapInfluenceContribution
        (treatedContribution index) (controlReuseContribution index))
    denominatorWeight target denominator normalizer loading loadingLimit
    massLimit
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
    hcover hloading hloadingLimit hmass hmultiplier hscore hbias

/--
Prospective PATE bootstrap consistency with index-dependent finite-cell
centered-square loadings.
-/
theorem prospective_pate_bootstrap_variance_consistency_of_indexed_varying_finite_cell_direct
    (cells : Finset Cell)
    (sample : Index -> Finset Unit)
    (multiplier baseWeight reuseResidualWeight heterogeneity residual :
      Index -> Unit -> Real)
    (score : Index -> Unit -> Cell)
    (target denominator normalizer : Real)
    (loading : Index -> Cell -> Real)
    (loadingLimit massLimit : Cell -> Real)
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
              weightedScoreCellMomentLimit cells loadingLimit massLimit)) ->
        bootstrapVarianceConsistent)
    (hcover :
      ∀ index unit, unit ∈ sample index -> score index unit ∈ cells)
    (hloading :
      ∀ index unit, unit ∈ sample index ->
        loading index (score index unit) =
          (prospectivePATEBootstrapInfluenceContribution
                (baseWeight index) (reuseResidualWeight index)
                (heterogeneity index) (residual index) unit -
              target * baseWeight index unit) ^ 2)
    (hloadingLimit :
      ∀ cell, cell ∈ cells ->
        Tendsto (fun index => loading index cell)
          l (nhds (loadingLimit cell)))
    (hmass :
      cellwiseScoreCellMassLLN (l := l) cells sample
        (fun _index _unit => 1) score massLimit)
    (hmultiplier : multiplierWeightRegular)
    (hscore : bootstrapScoreReplicationConsistent)
    (hbias : bootstrapBiasCorrectionConsistent) :
    bootstrapVarianceConsistent :=
  bootstrap_variance_consistency_of_finite_cell_varying_variance_direct
    (l := l) cells sample score
    (fun index =>
      prospectivePATEBootstrapInfluenceContribution (baseWeight index)
        (reuseResidualWeight index) (heterogeneity index) (residual index))
    baseWeight target denominator normalizer loading loadingLimit massLimit
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
    hcover hloading hloadingLimit hmass hmultiplier hscore hbias

/--
Prospective PATT bootstrap consistency with index-dependent finite-cell
centered-square loadings.
-/
theorem prospective_patt_bootstrap_variance_consistency_of_indexed_varying_finite_cell_direct
    (cells : Finset Cell)
    (sample : Index -> Finset Unit)
    (multiplier denominatorWeight treatedContribution controlReuseContribution :
      Index -> Unit -> Real)
    (score : Index -> Unit -> Cell)
    (target denominator normalizer : Real)
    (loading : Index -> Cell -> Real)
    (loadingLimit massLimit : Cell -> Real)
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
              weightedScoreCellMomentLimit cells loadingLimit massLimit)) ->
        bootstrapVarianceConsistent)
    (hcover :
      ∀ index unit, unit ∈ sample index -> score index unit ∈ cells)
    (hloading :
      ∀ index unit, unit ∈ sample index ->
        loading index (score index unit) =
          (prospectivePATTBootstrapInfluenceContribution
                (treatedContribution index) (controlReuseContribution index)
                unit -
              target * denominatorWeight index unit) ^ 2)
    (hloadingLimit :
      ∀ cell, cell ∈ cells ->
        Tendsto (fun index => loading index cell)
          l (nhds (loadingLimit cell)))
    (hmass :
      cellwiseScoreCellMassLLN (l := l) cells sample
        (fun _index _unit => 1) score massLimit)
    (hmultiplier : multiplierWeightRegular)
    (hscore : bootstrapScoreReplicationConsistent)
    (hbias : bootstrapBiasCorrectionConsistent) :
    bootstrapVarianceConsistent :=
  bootstrap_variance_consistency_of_finite_cell_varying_variance_direct
    (l := l) cells sample score
    (fun index =>
      prospectivePATTBootstrapInfluenceContribution
        (treatedContribution index) (controlReuseContribution index))
    denominatorWeight target denominator normalizer loading loadingLimit
    massLimit
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
    hcover hloading hloadingLimit hmass hmultiplier hscore hbias

/--
Paired retrospective PATE/PATT direct bootstrap consistency with
index-dependent finite-cell centered-square loadings.
-/
theorem retrospective_pate_patt_bootstrap_variance_consistency_of_indexed_varying_finite_cell_direct
    (pateCells : Finset Cell)
    (pateSample : Index -> Finset Unit)
    (pateMultiplier pateBaseWeight pateReuseResidualWeight pateHeterogeneity
      pateResidual : Index -> Unit -> Real)
    (pateScore : Index -> Unit -> Cell)
    (pateTarget pateDenominator pateNormalizer : Real)
    (pateLoading : Index -> Cell -> Real)
    (pateLoadingLimit pateMassLimit : Cell -> Real)
    (pateMultiplierWeightRegular pateBootstrapScoreReplicationConsistent
      pateBootstrapBiasCorrectionConsistent
      pateBootstrapVarianceConsistent : Prop)
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
              weightedScoreCellMomentLimit pateCells pateLoadingLimit
                pateMassLimit)) ->
        pateBootstrapVarianceConsistent)
    (hpateCover :
      ∀ index unit, unit ∈ pateSample index ->
        pateScore index unit ∈ pateCells)
    (hpateLoading :
      ∀ index unit, unit ∈ pateSample index ->
        pateLoading index (pateScore index unit) =
          (retrospectivePATEBootstrapInfluenceContribution
                (pateBaseWeight index) (pateReuseResidualWeight index)
                (pateHeterogeneity index) (pateResidual index) unit -
              pateTarget * pateBaseWeight index unit) ^ 2)
    (hpateLoadingLimit :
      ∀ cell, cell ∈ pateCells ->
        Tendsto (fun index => pateLoading index cell)
          l (nhds (pateLoadingLimit cell)))
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
    (pattLoading : Index -> Cell -> Real)
    (pattLoadingLimit pattMassLimit : Cell -> Real)
    (pattMultiplierWeightRegular pattBootstrapScoreReplicationConsistent
      pattBootstrapBiasCorrectionConsistent
      pattBootstrapVarianceConsistent : Prop)
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
              weightedScoreCellMomentLimit pattCells pattLoadingLimit
                pattMassLimit)) ->
        pattBootstrapVarianceConsistent)
    (hpattCover :
      ∀ index unit, unit ∈ pattSample index ->
        pattScore index unit ∈ pattCells)
    (hpattLoading :
      ∀ index unit, unit ∈ pattSample index ->
        pattLoading index (pattScore index unit) =
          (retrospectivePATTBootstrapInfluenceContribution
                (pattTreatedContribution index)
                (pattControlReuseContribution index) unit -
              pattTarget * pattDenominatorWeight index unit) ^ 2)
    (hpattLoadingLimit :
      ∀ cell, cell ∈ pattCells ->
        Tendsto (fun index => pattLoading index cell)
          l (nhds (pattLoadingLimit cell)))
    (hpattMass :
      cellwiseScoreCellMassLLN (l := l) pattCells pattSample
        (fun _index _unit => 1) pattScore pattMassLimit)
    (hpattMultiplier : pattMultiplierWeightRegular)
    (hpattScore : pattBootstrapScoreReplicationConsistent)
    (hpattBias : pattBootstrapBiasCorrectionConsistent) :
    pateBootstrapVarianceConsistent ∧ pattBootstrapVarianceConsistent :=
  ⟨retrospective_pate_bootstrap_variance_consistency_of_indexed_varying_finite_cell_direct
      (l := l) pateCells pateSample pateMultiplier pateBaseWeight
      pateReuseResidualWeight pateHeterogeneity pateResidual pateScore
      pateTarget pateDenominator pateNormalizer pateLoading
      pateLoadingLimit pateMassLimit pateMultiplierWeightRegular
      pateBootstrapScoreReplicationConsistent
      pateBootstrapBiasCorrectionConsistent pateBootstrapVarianceConsistent
      pateBridge hpateCover hpateLoading hpateLoadingLimit hpateMass
      hpateMultiplier hpateScore hpateBias,
    retrospective_patt_bootstrap_variance_consistency_of_indexed_varying_finite_cell_direct
      (l := l) pattCells pattSample pattMultiplier pattDenominatorWeight
      pattTreatedContribution pattControlReuseContribution pattScore
      pattTarget pattDenominator pattNormalizer pattLoading
      pattLoadingLimit pattMassLimit pattMultiplierWeightRegular
      pattBootstrapScoreReplicationConsistent
      pattBootstrapBiasCorrectionConsistent pattBootstrapVarianceConsistent
      pattBridge hpattCover hpattLoading hpattLoadingLimit hpattMass
      hpattMultiplier hpattScore hpattBias⟩

/--
Paired prospective PATE/PATT direct bootstrap consistency with
index-dependent finite-cell centered-square loadings.
-/
theorem prospective_pate_patt_bootstrap_variance_consistency_of_indexed_varying_finite_cell_direct
    (pateCells : Finset Cell)
    (pateSample : Index -> Finset Unit)
    (pateMultiplier pateBaseWeight pateReuseResidualWeight pateHeterogeneity
      pateResidual : Index -> Unit -> Real)
    (pateScore : Index -> Unit -> Cell)
    (pateTarget pateDenominator pateNormalizer : Real)
    (pateLoading : Index -> Cell -> Real)
    (pateLoadingLimit pateMassLimit : Cell -> Real)
    (pateMultiplierWeightRegular pateBootstrapScoreReplicationConsistent
      pateBootstrapBiasCorrectionConsistent
      pateBootstrapVarianceConsistent : Prop)
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
              weightedScoreCellMomentLimit pateCells pateLoadingLimit
                pateMassLimit)) ->
        pateBootstrapVarianceConsistent)
    (hpateCover :
      ∀ index unit, unit ∈ pateSample index ->
        pateScore index unit ∈ pateCells)
    (hpateLoading :
      ∀ index unit, unit ∈ pateSample index ->
        pateLoading index (pateScore index unit) =
          (prospectivePATEBootstrapInfluenceContribution
                (pateBaseWeight index) (pateReuseResidualWeight index)
                (pateHeterogeneity index) (pateResidual index) unit -
              pateTarget * pateBaseWeight index unit) ^ 2)
    (hpateLoadingLimit :
      ∀ cell, cell ∈ pateCells ->
        Tendsto (fun index => pateLoading index cell)
          l (nhds (pateLoadingLimit cell)))
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
    (pattLoading : Index -> Cell -> Real)
    (pattLoadingLimit pattMassLimit : Cell -> Real)
    (pattMultiplierWeightRegular pattBootstrapScoreReplicationConsistent
      pattBootstrapBiasCorrectionConsistent
      pattBootstrapVarianceConsistent : Prop)
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
              weightedScoreCellMomentLimit pattCells pattLoadingLimit
                pattMassLimit)) ->
        pattBootstrapVarianceConsistent)
    (hpattCover :
      ∀ index unit, unit ∈ pattSample index ->
        pattScore index unit ∈ pattCells)
    (hpattLoading :
      ∀ index unit, unit ∈ pattSample index ->
        pattLoading index (pattScore index unit) =
          (prospectivePATTBootstrapInfluenceContribution
                (pattTreatedContribution index)
                (pattControlReuseContribution index) unit -
              pattTarget * pattDenominatorWeight index unit) ^ 2)
    (hpattLoadingLimit :
      ∀ cell, cell ∈ pattCells ->
        Tendsto (fun index => pattLoading index cell)
          l (nhds (pattLoadingLimit cell)))
    (hpattMass :
      cellwiseScoreCellMassLLN (l := l) pattCells pattSample
        (fun _index _unit => 1) pattScore pattMassLimit)
    (hpattMultiplier : pattMultiplierWeightRegular)
    (hpattScore : pattBootstrapScoreReplicationConsistent)
    (hpattBias : pattBootstrapBiasCorrectionConsistent) :
    pateBootstrapVarianceConsistent ∧ pattBootstrapVarianceConsistent :=
  ⟨prospective_pate_bootstrap_variance_consistency_of_indexed_varying_finite_cell_direct
      (l := l) pateCells pateSample pateMultiplier pateBaseWeight
      pateReuseResidualWeight pateHeterogeneity pateResidual pateScore
      pateTarget pateDenominator pateNormalizer pateLoading
      pateLoadingLimit pateMassLimit pateMultiplierWeightRegular
      pateBootstrapScoreReplicationConsistent
      pateBootstrapBiasCorrectionConsistent pateBootstrapVarianceConsistent
      pateBridge hpateCover hpateLoading hpateLoadingLimit hpateMass
      hpateMultiplier hpateScore hpateBias,
    prospective_patt_bootstrap_variance_consistency_of_indexed_varying_finite_cell_direct
      (l := l) pattCells pattSample pattMultiplier pattDenominatorWeight
      pattTreatedContribution pattControlReuseContribution pattScore
      pattTarget pattDenominator pattNormalizer pattLoading
      pattLoadingLimit pattMassLimit pattMultiplierWeightRegular
      pattBootstrapScoreReplicationConsistent
      pattBootstrapBiasCorrectionConsistent pattBootstrapVarianceConsistent
      pattBridge hpattCover hpattLoading hpattLoadingLimit hpattMass
      hpattMultiplier hpattScore hpattBias⟩

/--
Direct generic bootstrap consistency route from score-cell contribution and
denominator-weight limits.
-/
theorem bootstrap_variance_consistency_of_finite_cell_contribution_weight_limits_direct
    (cells : Finset Cell)
    (sample : Index -> Finset Unit)
    (score : Index -> Unit -> Cell)
    (contribution weight : Index -> Unit -> Real)
    (target denominator normalizer : Real)
    (cellContribution cellWeight : Index -> Cell -> Real)
    (contributionLimit weightLimit massLimit : Cell -> Real)
    (linearizedReplicateAlgebra multiplierWeightRegular
      bootstrapScoreReplicationConsistent bootstrapBiasCorrectionConsistent
      bootstrapVarianceConsistent : Prop)
    (bridge :
      linearizedReplicateAlgebra ->
        multiplierWeightRegular ->
        bootstrapScoreReplicationConsistent ->
        bootstrapBiasCorrectionConsistent ->
        Tendsto
          (fun index =>
            bootstrapCenteredVarianceTarget (sample index)
              (contribution index) (weight index) target denominator
              normalizer)
          l
          (nhds
            ((1 / denominator ^ 2) * (1 / normalizer) *
              weightedScoreCellMomentLimit cells
                (fun cell =>
                  (contributionLimit cell - target * weightLimit cell) ^ 2)
                massLimit)) ->
        bootstrapVarianceConsistent)
    (halgebra : linearizedReplicateAlgebra)
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
    (hmultiplier : multiplierWeightRegular)
    (hscore : bootstrapScoreReplicationConsistent)
    (hbias : bootstrapBiasCorrectionConsistent) :
    bootstrapVarianceConsistent :=
  bootstrap_variance_consistency_of_linearized_bridge
    { linearized_replicate_algebra_verified := linearizedReplicateAlgebra
      multiplier_weight_regular := multiplierWeightRegular
      bootstrap_score_replication_consistent :=
        bootstrapScoreReplicationConsistent
      bootstrap_bias_correction_consistent := bootstrapBiasCorrectionConsistent
      conditional_variance_convergence :=
        Tendsto
          (fun index =>
            bootstrapCenteredVarianceTarget (sample index)
              (contribution index) (weight index) target denominator
              normalizer)
          l
          (nhds
            ((1 / denominator ^ 2) * (1 / normalizer) *
              weightedScoreCellMomentLimit cells
                (fun cell =>
                  (contributionLimit cell - target * weightLimit cell) ^ 2)
                massLimit))
      bootstrap_variance_consistent := bootstrapVarianceConsistent
      bridge := bridge }
    halgebra hmultiplier hscore hbias
    (tendsto_bootstrapCenteredVarianceTarget_of_cellwiseScoreCellMassLLN_of_cell_contribution_weight_limits
      (l := l) cells sample score contribution weight target denominator
      normalizer cellContribution cellWeight contributionLimit weightLimit
      massLimit hcover hcontributionCell hweightCell hcontributionLimit
      hweightLimit hmass)

/--
Retrospective PATE bootstrap consistency from score-cell contribution and
denominator-weight limits.
-/
theorem retrospective_pate_bootstrap_variance_consistency_of_indexed_cell_contribution_weight_limits_direct
    (cells : Finset Cell)
    (sample : Index -> Finset Unit)
    (multiplier baseWeight reuseResidualWeight heterogeneity residual :
      Index -> Unit -> Real)
    (score : Index -> Unit -> Cell)
    (target denominator normalizer : Real)
    (cellContribution cellWeight : Index -> Cell -> Real)
    (contributionLimit weightLimit massLimit : Cell -> Real)
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
                  (contributionLimit cell - target * weightLimit cell) ^ 2)
                massLimit)) ->
        bootstrapVarianceConsistent)
    (hcover :
      ∀ index unit, unit ∈ sample index -> score index unit ∈ cells)
    (hcontributionCell :
      ∀ index unit, unit ∈ sample index ->
        cellContribution index (score index unit) =
          retrospectivePATEBootstrapInfluenceContribution
            (baseWeight index) (reuseResidualWeight index)
            (heterogeneity index) (residual index) unit)
    (hweightCell :
      ∀ index unit, unit ∈ sample index ->
        cellWeight index (score index unit) = baseWeight index unit)
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
    (hmultiplier : multiplierWeightRegular)
    (hscore : bootstrapScoreReplicationConsistent)
    (hbias : bootstrapBiasCorrectionConsistent) :
    bootstrapVarianceConsistent :=
  bootstrap_variance_consistency_of_finite_cell_contribution_weight_limits_direct
    (l := l) cells sample score
    (fun index =>
      retrospectivePATEBootstrapInfluenceContribution (baseWeight index)
        (reuseResidualWeight index) (heterogeneity index) (residual index))
    baseWeight target denominator normalizer cellContribution cellWeight
    contributionLimit weightLimit massLimit
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
    hcover hcontributionCell hweightCell hcontributionLimit hweightLimit
    hmass hmultiplier hscore hbias

/--
Retrospective PATT bootstrap consistency from score-cell contribution and
denominator-weight limits.
-/
theorem retrospective_patt_bootstrap_variance_consistency_of_indexed_cell_contribution_weight_limits_direct
    (cells : Finset Cell)
    (sample : Index -> Finset Unit)
    (multiplier denominatorWeight treatedContribution controlReuseContribution :
      Index -> Unit -> Real)
    (score : Index -> Unit -> Cell)
    (target denominator normalizer : Real)
    (cellContribution cellWeight : Index -> Cell -> Real)
    (contributionLimit weightLimit massLimit : Cell -> Real)
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
                  (contributionLimit cell - target * weightLimit cell) ^ 2)
                massLimit)) ->
        bootstrapVarianceConsistent)
    (hcover :
      ∀ index unit, unit ∈ sample index -> score index unit ∈ cells)
    (hcontributionCell :
      ∀ index unit, unit ∈ sample index ->
        cellContribution index (score index unit) =
          retrospectivePATTBootstrapInfluenceContribution
            (treatedContribution index) (controlReuseContribution index) unit)
    (hweightCell :
      ∀ index unit, unit ∈ sample index ->
        cellWeight index (score index unit) = denominatorWeight index unit)
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
    (hmultiplier : multiplierWeightRegular)
    (hscore : bootstrapScoreReplicationConsistent)
    (hbias : bootstrapBiasCorrectionConsistent) :
    bootstrapVarianceConsistent :=
  bootstrap_variance_consistency_of_finite_cell_contribution_weight_limits_direct
    (l := l) cells sample score
    (fun index =>
      retrospectivePATTBootstrapInfluenceContribution
        (treatedContribution index) (controlReuseContribution index))
    denominatorWeight target denominator normalizer cellContribution
    cellWeight contributionLimit weightLimit massLimit
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
    hcover hcontributionCell hweightCell hcontributionLimit hweightLimit
    hmass hmultiplier hscore hbias

/--
Prospective PATE bootstrap consistency from score-cell contribution and
denominator-weight limits.
-/
theorem prospective_pate_bootstrap_variance_consistency_of_indexed_cell_contribution_weight_limits_direct
    (cells : Finset Cell)
    (sample : Index -> Finset Unit)
    (multiplier baseWeight reuseResidualWeight heterogeneity residual :
      Index -> Unit -> Real)
    (score : Index -> Unit -> Cell)
    (target denominator normalizer : Real)
    (cellContribution cellWeight : Index -> Cell -> Real)
    (contributionLimit weightLimit massLimit : Cell -> Real)
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
                  (contributionLimit cell - target * weightLimit cell) ^ 2)
                massLimit)) ->
        bootstrapVarianceConsistent)
    (hcover :
      ∀ index unit, unit ∈ sample index -> score index unit ∈ cells)
    (hcontributionCell :
      ∀ index unit, unit ∈ sample index ->
        cellContribution index (score index unit) =
          prospectivePATEBootstrapInfluenceContribution
            (baseWeight index) (reuseResidualWeight index)
            (heterogeneity index) (residual index) unit)
    (hweightCell :
      ∀ index unit, unit ∈ sample index ->
        cellWeight index (score index unit) = baseWeight index unit)
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
    (hmultiplier : multiplierWeightRegular)
    (hscore : bootstrapScoreReplicationConsistent)
    (hbias : bootstrapBiasCorrectionConsistent) :
    bootstrapVarianceConsistent :=
  bootstrap_variance_consistency_of_finite_cell_contribution_weight_limits_direct
    (l := l) cells sample score
    (fun index =>
      prospectivePATEBootstrapInfluenceContribution (baseWeight index)
        (reuseResidualWeight index) (heterogeneity index) (residual index))
    baseWeight target denominator normalizer cellContribution cellWeight
    contributionLimit weightLimit massLimit
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
    hcover hcontributionCell hweightCell hcontributionLimit hweightLimit
    hmass hmultiplier hscore hbias

/--
Prospective PATT bootstrap consistency from score-cell contribution and
denominator-weight limits.
-/
theorem prospective_patt_bootstrap_variance_consistency_of_indexed_cell_contribution_weight_limits_direct
    (cells : Finset Cell)
    (sample : Index -> Finset Unit)
    (multiplier denominatorWeight treatedContribution controlReuseContribution :
      Index -> Unit -> Real)
    (score : Index -> Unit -> Cell)
    (target denominator normalizer : Real)
    (cellContribution cellWeight : Index -> Cell -> Real)
    (contributionLimit weightLimit massLimit : Cell -> Real)
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
                  (contributionLimit cell - target * weightLimit cell) ^ 2)
                massLimit)) ->
        bootstrapVarianceConsistent)
    (hcover :
      ∀ index unit, unit ∈ sample index -> score index unit ∈ cells)
    (hcontributionCell :
      ∀ index unit, unit ∈ sample index ->
        cellContribution index (score index unit) =
          prospectivePATTBootstrapInfluenceContribution
            (treatedContribution index) (controlReuseContribution index) unit)
    (hweightCell :
      ∀ index unit, unit ∈ sample index ->
        cellWeight index (score index unit) = denominatorWeight index unit)
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
    (hmultiplier : multiplierWeightRegular)
    (hscore : bootstrapScoreReplicationConsistent)
    (hbias : bootstrapBiasCorrectionConsistent) :
    bootstrapVarianceConsistent :=
  bootstrap_variance_consistency_of_finite_cell_contribution_weight_limits_direct
    (l := l) cells sample score
    (fun index =>
      prospectivePATTBootstrapInfluenceContribution
        (treatedContribution index) (controlReuseContribution index))
    denominatorWeight target denominator normalizer cellContribution
    cellWeight contributionLimit weightLimit massLimit
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
    hcover hcontributionCell hweightCell hcontributionLimit hweightLimit
    hmass hmultiplier hscore hbias

/--
Paired retrospective PATE/PATT direct bootstrap consistency from score-cell
contribution and denominator-weight limits.
-/
theorem retrospective_pate_patt_bootstrap_variance_consistency_of_indexed_cell_contribution_weight_limits_direct
    (pateCells : Finset Cell)
    (pateSample : Index -> Finset Unit)
    (pateMultiplier pateBaseWeight pateReuseResidualWeight pateHeterogeneity
      pateResidual : Index -> Unit -> Real)
    (pateScore : Index -> Unit -> Cell)
    (pateTarget pateDenominator pateNormalizer : Real)
    (pateCellContribution pateCellWeight : Index -> Cell -> Real)
    (pateContributionLimit pateWeightLimit pateMassLimit : Cell -> Real)
    (pateMultiplierWeightRegular pateBootstrapScoreReplicationConsistent
      pateBootstrapBiasCorrectionConsistent
      pateBootstrapVarianceConsistent : Prop)
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
                  (pateContributionLimit cell -
                    pateTarget * pateWeightLimit cell) ^ 2)
                pateMassLimit)) ->
        pateBootstrapVarianceConsistent)
    (hpateCover :
      ∀ index unit, unit ∈ pateSample index ->
        pateScore index unit ∈ pateCells)
    (hpateContributionCell :
      ∀ index unit, unit ∈ pateSample index ->
        pateCellContribution index (pateScore index unit) =
          retrospectivePATEBootstrapInfluenceContribution
            (pateBaseWeight index) (pateReuseResidualWeight index)
            (pateHeterogeneity index) (pateResidual index) unit)
    (hpateWeightCell :
      ∀ index unit, unit ∈ pateSample index ->
        pateCellWeight index (pateScore index unit) =
          pateBaseWeight index unit)
    (hpateContributionLimit :
      ∀ cell, cell ∈ pateCells ->
        Tendsto (fun index => pateCellContribution index cell)
          l (nhds (pateContributionLimit cell)))
    (hpateWeightLimit :
      ∀ cell, cell ∈ pateCells ->
        Tendsto (fun index => pateCellWeight index cell)
          l (nhds (pateWeightLimit cell)))
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
    (pattCellContribution pattCellWeight : Index -> Cell -> Real)
    (pattContributionLimit pattWeightLimit pattMassLimit : Cell -> Real)
    (pattMultiplierWeightRegular pattBootstrapScoreReplicationConsistent
      pattBootstrapBiasCorrectionConsistent
      pattBootstrapVarianceConsistent : Prop)
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
                  (pattContributionLimit cell -
                    pattTarget * pattWeightLimit cell) ^ 2)
                pattMassLimit)) ->
        pattBootstrapVarianceConsistent)
    (hpattCover :
      ∀ index unit, unit ∈ pattSample index ->
        pattScore index unit ∈ pattCells)
    (hpattContributionCell :
      ∀ index unit, unit ∈ pattSample index ->
        pattCellContribution index (pattScore index unit) =
          retrospectivePATTBootstrapInfluenceContribution
            (pattTreatedContribution index)
            (pattControlReuseContribution index) unit)
    (hpattWeightCell :
      ∀ index unit, unit ∈ pattSample index ->
        pattCellWeight index (pattScore index unit) =
          pattDenominatorWeight index unit)
    (hpattContributionLimit :
      ∀ cell, cell ∈ pattCells ->
        Tendsto (fun index => pattCellContribution index cell)
          l (nhds (pattContributionLimit cell)))
    (hpattWeightLimit :
      ∀ cell, cell ∈ pattCells ->
        Tendsto (fun index => pattCellWeight index cell)
          l (nhds (pattWeightLimit cell)))
    (hpattMass :
      cellwiseScoreCellMassLLN (l := l) pattCells pattSample
        (fun _index _unit => 1) pattScore pattMassLimit)
    (hpattMultiplier : pattMultiplierWeightRegular)
    (hpattScore : pattBootstrapScoreReplicationConsistent)
    (hpattBias : pattBootstrapBiasCorrectionConsistent) :
    pateBootstrapVarianceConsistent ∧ pattBootstrapVarianceConsistent :=
  ⟨retrospective_pate_bootstrap_variance_consistency_of_indexed_cell_contribution_weight_limits_direct
      (l := l) pateCells pateSample pateMultiplier pateBaseWeight
      pateReuseResidualWeight pateHeterogeneity pateResidual pateScore
      pateTarget pateDenominator pateNormalizer pateCellContribution
      pateCellWeight pateContributionLimit pateWeightLimit pateMassLimit
      pateMultiplierWeightRegular pateBootstrapScoreReplicationConsistent
      pateBootstrapBiasCorrectionConsistent pateBootstrapVarianceConsistent
      pateBridge hpateCover hpateContributionCell hpateWeightCell
      hpateContributionLimit hpateWeightLimit hpateMass hpateMultiplier
      hpateScore hpateBias,
    retrospective_patt_bootstrap_variance_consistency_of_indexed_cell_contribution_weight_limits_direct
      (l := l) pattCells pattSample pattMultiplier pattDenominatorWeight
      pattTreatedContribution pattControlReuseContribution pattScore
      pattTarget pattDenominator pattNormalizer pattCellContribution
      pattCellWeight pattContributionLimit pattWeightLimit pattMassLimit
      pattMultiplierWeightRegular pattBootstrapScoreReplicationConsistent
      pattBootstrapBiasCorrectionConsistent pattBootstrapVarianceConsistent
      pattBridge hpattCover hpattContributionCell hpattWeightCell
      hpattContributionLimit hpattWeightLimit hpattMass hpattMultiplier
      hpattScore hpattBias⟩

/--
Paired prospective PATE/PATT direct bootstrap consistency from score-cell
contribution and denominator-weight limits.
-/
theorem prospective_pate_patt_bootstrap_variance_consistency_of_indexed_cell_contribution_weight_limits_direct
    (pateCells : Finset Cell)
    (pateSample : Index -> Finset Unit)
    (pateMultiplier pateBaseWeight pateReuseResidualWeight pateHeterogeneity
      pateResidual : Index -> Unit -> Real)
    (pateScore : Index -> Unit -> Cell)
    (pateTarget pateDenominator pateNormalizer : Real)
    (pateCellContribution pateCellWeight : Index -> Cell -> Real)
    (pateContributionLimit pateWeightLimit pateMassLimit : Cell -> Real)
    (pateMultiplierWeightRegular pateBootstrapScoreReplicationConsistent
      pateBootstrapBiasCorrectionConsistent
      pateBootstrapVarianceConsistent : Prop)
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
                  (pateContributionLimit cell -
                    pateTarget * pateWeightLimit cell) ^ 2)
                pateMassLimit)) ->
        pateBootstrapVarianceConsistent)
    (hpateCover :
      ∀ index unit, unit ∈ pateSample index ->
        pateScore index unit ∈ pateCells)
    (hpateContributionCell :
      ∀ index unit, unit ∈ pateSample index ->
        pateCellContribution index (pateScore index unit) =
          prospectivePATEBootstrapInfluenceContribution
            (pateBaseWeight index) (pateReuseResidualWeight index)
            (pateHeterogeneity index) (pateResidual index) unit)
    (hpateWeightCell :
      ∀ index unit, unit ∈ pateSample index ->
        pateCellWeight index (pateScore index unit) =
          pateBaseWeight index unit)
    (hpateContributionLimit :
      ∀ cell, cell ∈ pateCells ->
        Tendsto (fun index => pateCellContribution index cell)
          l (nhds (pateContributionLimit cell)))
    (hpateWeightLimit :
      ∀ cell, cell ∈ pateCells ->
        Tendsto (fun index => pateCellWeight index cell)
          l (nhds (pateWeightLimit cell)))
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
    (pattCellContribution pattCellWeight : Index -> Cell -> Real)
    (pattContributionLimit pattWeightLimit pattMassLimit : Cell -> Real)
    (pattMultiplierWeightRegular pattBootstrapScoreReplicationConsistent
      pattBootstrapBiasCorrectionConsistent
      pattBootstrapVarianceConsistent : Prop)
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
                  (pattContributionLimit cell -
                    pattTarget * pattWeightLimit cell) ^ 2)
                pattMassLimit)) ->
        pattBootstrapVarianceConsistent)
    (hpattCover :
      ∀ index unit, unit ∈ pattSample index ->
        pattScore index unit ∈ pattCells)
    (hpattContributionCell :
      ∀ index unit, unit ∈ pattSample index ->
        pattCellContribution index (pattScore index unit) =
          prospectivePATTBootstrapInfluenceContribution
            (pattTreatedContribution index)
            (pattControlReuseContribution index) unit)
    (hpattWeightCell :
      ∀ index unit, unit ∈ pattSample index ->
        pattCellWeight index (pattScore index unit) =
          pattDenominatorWeight index unit)
    (hpattContributionLimit :
      ∀ cell, cell ∈ pattCells ->
        Tendsto (fun index => pattCellContribution index cell)
          l (nhds (pattContributionLimit cell)))
    (hpattWeightLimit :
      ∀ cell, cell ∈ pattCells ->
        Tendsto (fun index => pattCellWeight index cell)
          l (nhds (pattWeightLimit cell)))
    (hpattMass :
      cellwiseScoreCellMassLLN (l := l) pattCells pattSample
        (fun _index _unit => 1) pattScore pattMassLimit)
    (hpattMultiplier : pattMultiplierWeightRegular)
    (hpattScore : pattBootstrapScoreReplicationConsistent)
    (hpattBias : pattBootstrapBiasCorrectionConsistent) :
    pateBootstrapVarianceConsistent ∧ pattBootstrapVarianceConsistent :=
  ⟨prospective_pate_bootstrap_variance_consistency_of_indexed_cell_contribution_weight_limits_direct
      (l := l) pateCells pateSample pateMultiplier pateBaseWeight
      pateReuseResidualWeight pateHeterogeneity pateResidual pateScore
      pateTarget pateDenominator pateNormalizer pateCellContribution
      pateCellWeight pateContributionLimit pateWeightLimit pateMassLimit
      pateMultiplierWeightRegular pateBootstrapScoreReplicationConsistent
      pateBootstrapBiasCorrectionConsistent pateBootstrapVarianceConsistent
      pateBridge hpateCover hpateContributionCell hpateWeightCell
      hpateContributionLimit hpateWeightLimit hpateMass hpateMultiplier
      hpateScore hpateBias,
    prospective_patt_bootstrap_variance_consistency_of_indexed_cell_contribution_weight_limits_direct
      (l := l) pattCells pattSample pattMultiplier pattDenominatorWeight
      pattTreatedContribution pattControlReuseContribution pattScore
      pattTarget pattDenominator pattNormalizer pattCellContribution
      pattCellWeight pattContributionLimit pattWeightLimit pattMassLimit
      pattMultiplierWeightRegular pattBootstrapScoreReplicationConsistent
      pattBootstrapBiasCorrectionConsistent pattBootstrapVarianceConsistent
      pattBridge hpattCover hpattContributionCell hpattWeightCell
      hpattContributionLimit hpattWeightLimit hpattMass hpattMultiplier
      hpattScore hpattBias⟩

/--
Generic bootstrap consistency route from eventual score-cell contribution and
denominator-weight representations.  This is the consistency-level counterpart
of the eventual finite-cell variance bridge.
-/
theorem bootstrap_variance_consistency_of_eventually_finite_cell_contribution_weight_limits_direct
    (cells : Finset Cell)
    (sample : Index -> Finset Unit)
    (score : Index -> Unit -> Cell)
    (contribution weight : Index -> Unit -> Real)
    (target denominator normalizer : Real)
    (cellContribution cellWeight : Index -> Cell -> Real)
    (contributionLimit weightLimit massLimit : Cell -> Real)
    (linearizedReplicateAlgebra multiplierWeightRegular
      bootstrapScoreReplicationConsistent bootstrapBiasCorrectionConsistent
      bootstrapVarianceConsistent : Prop)
    (bridge :
      linearizedReplicateAlgebra ->
        multiplierWeightRegular ->
        bootstrapScoreReplicationConsistent ->
        bootstrapBiasCorrectionConsistent ->
        Tendsto
          (fun index =>
            bootstrapCenteredVarianceTarget (sample index)
              (contribution index) (weight index) target denominator
              normalizer)
          l
          (nhds
            ((1 / denominator ^ 2) * (1 / normalizer) *
              weightedScoreCellMomentLimit cells
                (fun cell =>
                  (contributionLimit cell - target * weightLimit cell) ^ 2)
                massLimit)) ->
        bootstrapVarianceConsistent)
    (halgebra : linearizedReplicateAlgebra)
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
    (hmultiplier : multiplierWeightRegular)
    (hscore : bootstrapScoreReplicationConsistent)
    (hbias : bootstrapBiasCorrectionConsistent) :
    bootstrapVarianceConsistent :=
  bootstrap_variance_consistency_of_linearized_bridge
    { linearized_replicate_algebra_verified := linearizedReplicateAlgebra
      multiplier_weight_regular := multiplierWeightRegular
      bootstrap_score_replication_consistent :=
        bootstrapScoreReplicationConsistent
      bootstrap_bias_correction_consistent := bootstrapBiasCorrectionConsistent
      conditional_variance_convergence :=
        Tendsto
          (fun index =>
            bootstrapCenteredVarianceTarget (sample index)
              (contribution index) (weight index) target denominator
              normalizer)
          l
          (nhds
            ((1 / denominator ^ 2) * (1 / normalizer) *
              weightedScoreCellMomentLimit cells
                (fun cell =>
                  (contributionLimit cell - target * weightLimit cell) ^ 2)
                massLimit))
      bootstrap_variance_consistent := bootstrapVarianceConsistent
      bridge := bridge }
    halgebra hmultiplier hscore hbias
    (tendsto_bootstrapCenteredVarianceTarget_of_eventually_cell_contribution_weight_limits
      (l := l) cells sample score contribution weight target denominator
      normalizer cellContribution cellWeight contributionLimit weightLimit
      massLimit hcover hcontributionCell hweightCell hcontributionLimit
      hweightLimit hmass)

end WDSM
end Matching
end StatInference
