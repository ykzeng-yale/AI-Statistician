import Mathlib.Data.Finset.Basic
import Mathlib.Topology.Basic
import StatInference.Matching.WDSM.FiniteCellGeometryMomentBridge
import StatInference.Matching.WDSM.FiniteCellIndicatorLLNEnvelopeBridge

/-!
# Geometry moment bridges from finite-cell mass envelopes

This module composes the finite-cell mass-envelope LLN route with the
Chen-Han geometry audit interface.  The nearest-neighbor geometry theorem is
still an explicit transfer from finite-cell indicator LLNs to reuse-moment
limits, but the sampling/LLN side can now be supplied by common shrinking
mass envelopes rather than an abstract indicator-LLN proposition.
-/

namespace StatInference
namespace Matching
namespace WDSM

open Filter

variable {Index Unit Cell : Type*} {l : Filter Index} [DecidableEq Cell]

/--
Build a weighted geometry moment bridge from finite score-cell mass-envelope
bounds, together with the remaining finite-cell-to-reuse transfer.
-/
def weightedGeometryMomentBridgeOfMassEnvelope
    (cells : Finset Cell)
    (sample : Index -> Finset Unit)
    (weight : Index -> Unit -> Real)
    (score : Index -> Unit -> Cell)
    (massLimit cellScale : Cell -> Real)
    (envelope : Index -> Real)
    (scoreSpaceRegularity catchmentInput surveyDesignRegularity
      boundedScoreCellIndicators massEnvelopeBounds
      exactWeightedReuseMomentLimits : Prop)
    (regularity_to_design :
      scoreSpaceRegularity -> surveyDesignRegularity)
    (catchment_to_bounded :
      catchmentInput -> boundedScoreCellIndicators)
    (catchment_to_mass_envelope :
      catchmentInput -> massEnvelopeBounds)
    (mass_envelope_to_bounds :
      surveyDesignRegularity ->
      boundedScoreCellIndicators ->
      massEnvelopeBounds ->
        (∀ cell, cell ∈ cells ->
          ∀ᶠ index in l,
            |scoreCellMass (sample index) (weight index)
                (score index) cell - massLimit cell| ≤
              cellScale cell * envelope index) ∧
        Tendsto envelope l (nhds 0))
    (finite_cell_lln_to_reuse_moments :
      cellwiseWeightedIndicatorSumLLN (l := l) cells sample weight score
        massLimit ->
        exactWeightedReuseMomentLimits) :
    WeightedGeometryMomentBridge :=
  weightedGeometryMomentBridgeOfFiniteCellIndicatorLLN
    (finiteScoreCellIndicatorLLNBridgeOfMassEnvelope
      (l := l) cells sample weight score massLimit cellScale envelope
      surveyDesignRegularity boundedScoreCellIndicators massEnvelopeBounds
      mass_envelope_to_bounds)
    scoreSpaceRegularity catchmentInput exactWeightedReuseMomentLimits
    regularity_to_design catchment_to_bounded catchment_to_mass_envelope
    finite_cell_lln_to_reuse_moments

/--
Finite mass-envelope inputs yield exact weighted reuse-moment limits after
the supplied finite-cell-to-reuse transfer.
-/
theorem weighted_geometry_moments_of_mass_envelope
    (cells : Finset Cell)
    (sample : Index -> Finset Unit)
    (weight : Index -> Unit -> Real)
    (score : Index -> Unit -> Cell)
    (massLimit cellScale : Cell -> Real)
    (envelope : Index -> Real)
    (scoreSpaceRegularity catchmentInput surveyDesignRegularity
      boundedScoreCellIndicators massEnvelopeBounds
      exactWeightedReuseMomentLimits : Prop)
    (regularity_to_design :
      scoreSpaceRegularity -> surveyDesignRegularity)
    (catchment_to_bounded :
      catchmentInput -> boundedScoreCellIndicators)
    (catchment_to_mass_envelope :
      catchmentInput -> massEnvelopeBounds)
    (mass_envelope_to_bounds :
      surveyDesignRegularity ->
      boundedScoreCellIndicators ->
      massEnvelopeBounds ->
        (∀ cell, cell ∈ cells ->
          ∀ᶠ index in l,
            |scoreCellMass (sample index) (weight index)
                (score index) cell - massLimit cell| ≤
              cellScale cell * envelope index) ∧
        Tendsto envelope l (nhds 0))
    (finite_cell_lln_to_reuse_moments :
      cellwiseWeightedIndicatorSumLLN (l := l) cells sample weight score
        massLimit ->
        exactWeightedReuseMomentLimits)
    (hregular : scoreSpaceRegularity)
    (hcatchment : catchmentInput) :
    exactWeightedReuseMomentLimits :=
  exact_weighted_reuse_moments_of_geometry
    (weightedGeometryMomentBridgeOfMassEnvelope
      (l := l) cells sample weight score massLimit cellScale envelope
      scoreSpaceRegularity catchmentInput surveyDesignRegularity
      boundedScoreCellIndicators massEnvelopeBounds
      exactWeightedReuseMomentLimits regularity_to_design
      catchment_to_bounded catchment_to_mass_envelope
      mass_envelope_to_bounds finite_cell_lln_to_reuse_moments)
    hregular hcatchment

/--
Finite mass-envelope inputs yield the Chen-Han reuse-moment and limiting
variance conclusions after the supplied reuse-to-variance transfer.
-/
theorem chen_han_reuse_and_variance_of_mass_envelope
    (cells : Finset Cell)
    (sample : Index -> Finset Unit)
    (weight : Index -> Unit -> Real)
    (score : Index -> Unit -> Cell)
    (massLimit cellScale : Cell -> Real)
    (envelope : Index -> Real)
    (scoreSpaceRegularity catchmentInput surveyDesignRegularity
      boundedScoreCellIndicators massEnvelopeBounds
      exactWeightedReuseMomentLimits limitingVarianceFormula : Prop)
    (regularity_to_design :
      scoreSpaceRegularity -> surveyDesignRegularity)
    (catchment_to_bounded :
      catchmentInput -> boundedScoreCellIndicators)
    (catchment_to_mass_envelope :
      catchmentInput -> massEnvelopeBounds)
    (mass_envelope_to_bounds :
      surveyDesignRegularity ->
      boundedScoreCellIndicators ->
      massEnvelopeBounds ->
        (∀ cell, cell ∈ cells ->
          ∀ᶠ index in l,
            |scoreCellMass (sample index) (weight index)
                (score index) cell - massLimit cell| ≤
              cellScale cell * envelope index) ∧
        Tendsto envelope l (nhds 0))
    (finite_cell_lln_to_reuse_moments :
      cellwiseWeightedIndicatorSumLLN (l := l) cells sample weight score
        massLimit ->
        exactWeightedReuseMomentLimits)
    (varianceTransfer :
      exactWeightedReuseMomentLimits -> limitingVarianceFormula)
    (hregular : scoreSpaceRegularity)
    (hcatchment : catchmentInput) :
    exactWeightedReuseMomentLimits ∧ limitingVarianceFormula :=
  chen_han_reuse_and_limiting_variance_of_weighted_geometry_bridge
    (weightedGeometryMomentBridgeOfMassEnvelope
      (l := l) cells sample weight score massLimit cellScale envelope
      scoreSpaceRegularity catchmentInput surveyDesignRegularity
      boundedScoreCellIndicators massEnvelopeBounds
      exactWeightedReuseMomentLimits regularity_to_design
      catchment_to_bounded catchment_to_mass_envelope
      mass_envelope_to_bounds finite_cell_lln_to_reuse_moments)
    limitingVarianceFormula varianceTransfer hregular hcatchment

end WDSM
end Matching
end StatInference
