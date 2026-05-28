import Mathlib.Data.Finset.Basic
import Mathlib.Topology.Basic
import StatInference.Matching.WDSM.FiniteCellMassEnvelopeBridge

/-!
# Finite score-cell indicator LLN bridges from mass envelopes

This module packages the checked finite-cell mass envelope route as the
standard `FiniteScoreCellIndicatorLLNBridge` interface.  Concrete WDSM
sampling arguments can now provide a shrinking score-cell mass envelope and
reuse the existing approximation, residual, and bootstrap layers through the
same bridge interface.
-/

namespace StatInference
namespace Matching
namespace WDSM

open Filter

variable {Index Unit Cell : Type*} {l : Filter Index} [DecidableEq Cell]

/--
Build the generic finite score-cell indicator LLN bridge from a concrete
mass-envelope assumption.  The probability/design content remains abstract:
the supplied adapter turns design regularity, bounded indicators, and the
array-level mass-envelope statement into eventual absolute mass-error bounds
and a shrinking common envelope.
-/
def finiteScoreCellIndicatorLLNBridgeOfMassEnvelope
    (cells : Finset Cell)
    (sample : Index -> Finset Unit)
    (weight : Index -> Unit -> Real)
    (score : Index -> Unit -> Cell)
    (massLimit cellScale : Cell -> Real)
    (envelope : Index -> Real)
    (surveyDesignRegularity boundedScoreCellIndicators
      massEnvelopeBounds : Prop)
    (mass_envelope_to_bounds :
      surveyDesignRegularity ->
      boundedScoreCellIndicators ->
      massEnvelopeBounds ->
        (∀ cell, cell ∈ cells ->
          ∀ᶠ index in l,
            |scoreCellMass (sample index) (weight index)
                (score index) cell - massLimit cell| ≤
              cellScale cell * envelope index) ∧
        Tendsto envelope l (nhds 0)) :
    FiniteScoreCellIndicatorLLNBridge Cell where
  cells := cells
  referenceShare := massLimit
  survey_design_regularity := surveyDesignRegularity
  bounded_score_cell_indicators := boundedScoreCellIndicators
  weighted_indicator_array_lln := massEnvelopeBounds
  cellwise_weighted_indicator_sum_lln :=
    cellwiseWeightedIndicatorSumLLN (l := l) cells sample weight score
      massLimit
  bridge := by
    intro hdesign hbounded hmassEnvelope
    rcases mass_envelope_to_bounds hdesign hbounded hmassEnvelope with
      ⟨hbound, henvelope⟩
    exact
      cellwiseWeightedIndicatorSumLLN_of_eventually_abs_scoreCellMass_sub_le_envelope
        (l := l) cells sample weight score massLimit cellScale envelope
        hbound henvelope

/--
Applying the mass-envelope bridge gives the concrete cellwise weighted
indicator-sum LLN.
-/
theorem finite_score_cell_indicator_lln_of_mass_envelope_bridge
    (cells : Finset Cell)
    (sample : Index -> Finset Unit)
    (weight : Index -> Unit -> Real)
    (score : Index -> Unit -> Cell)
    (massLimit cellScale : Cell -> Real)
    (envelope : Index -> Real)
    (surveyDesignRegularity boundedScoreCellIndicators
      massEnvelopeBounds : Prop)
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
    (hdesign : surveyDesignRegularity)
    (hbounded : boundedScoreCellIndicators)
    (hmassEnvelope : massEnvelopeBounds) :
    cellwiseWeightedIndicatorSumLLN (l := l) cells sample weight score
      massLimit :=
  finite_score_cell_indicator_lln_of_bridge
    (finiteScoreCellIndicatorLLNBridgeOfMassEnvelope
      (l := l) cells sample weight score massLimit cellScale envelope
      surveyDesignRegularity boundedScoreCellIndicators massEnvelopeBounds
      mass_envelope_to_bounds)
    hdesign hbounded hmassEnvelope

end WDSM
end Matching
end StatInference
