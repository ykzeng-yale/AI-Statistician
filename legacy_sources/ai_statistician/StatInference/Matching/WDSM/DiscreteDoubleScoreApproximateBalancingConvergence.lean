import StatInference.Matching.WDSM.DiscreteDoubleScoreApproximateBalancingRate
import StatInference.Matching.WDSM.EnvelopeRateAlgebra

/-!
# Convergence wrappers for approximate double-score balancing

This module composes the WDSM double-score approximation bounds with the
envelope-rate algebra.  The result is a cleaner stochastic interface: it is
enough to prove convergence of the outcome envelopes and convergence of the L1
double-score share imbalances, rather than proving envelope-weighted product
rates directly.
-/

namespace StatInference
namespace Matching
namespace WDSM

open Filter

variable {Index Unit PropensityCell TreatedProgCell ControlProgCell PATTProgCell : Type*}
  [DecidableEq PropensityCell] [DecidableEq TreatedProgCell]
  [DecidableEq ControlProgCell] [DecidableEq PATTProgCell]
variable {l : Filter Index}

theorem tendsto_pateDoubleScoreApprox_error_zero_of_l1_and_envelopes
    (targetSample treatedSample controlSample : Index -> Finset Unit)
    (cells :
      Index -> Finset ((PropensityCell × TreatedProgCell) × ControlProgCell))
    (targetWeight treatedWeight controlWeight : Index -> Unit -> Real)
    (targetOutcomeT targetOutcomeC treatedOutcome controlOutcome :
      Index -> Unit -> Real)
    (propensityScore : Index -> Unit -> PropensityCell)
    (treatedPrognosticScore : Index -> Unit -> TreatedProgCell)
    (controlPrognosticScore : Index -> Unit -> ControlProgCell)
    (treatedValue : Index -> TreatedProgCell -> Real)
    (controlValue : Index -> ControlProgCell -> Real)
    (treatedEnvelope controlEnvelope : Index -> Real)
    (treatedEnvelopeLimit controlEnvelopeLimit : Real)
    (hcoverTarget :
      ∀ index unit, unit ∈ targetSample index ->
        pateDoubleScore (propensityScore index)
          (treatedPrognosticScore index)
          (controlPrognosticScore index) unit ∈ cells index)
    (hcoverTreated :
      ∀ index unit, unit ∈ treatedSample index ->
        pateDoubleScore (propensityScore index)
          (treatedPrognosticScore index)
          (controlPrognosticScore index) unit ∈ cells index)
    (hcoverControl :
      ∀ index unit, unit ∈ controlSample index ->
        pateDoubleScore (propensityScore index)
          (treatedPrognosticScore index)
          (controlPrognosticScore index) unit ∈ cells index)
    (hmassTarget :
      ∀ index cell, cell ∈ cells index ->
        scoreCellMass (targetSample index) (targetWeight index)
          (pateDoubleScore (propensityScore index)
            (treatedPrognosticScore index)
            (controlPrognosticScore index)) cell ≠ 0)
    (hmassTreated :
      ∀ index cell, cell ∈ cells index ->
        scoreCellMass (treatedSample index) (treatedWeight index)
          (pateDoubleScore (propensityScore index)
            (treatedPrognosticScore index)
            (controlPrognosticScore index)) cell ≠ 0)
    (hmassControl :
      ∀ index cell, cell ∈ cells index ->
        scoreCellMass (controlSample index) (controlWeight index)
          (pateDoubleScore (propensityScore index)
            (treatedPrognosticScore index)
            (controlPrognosticScore index)) cell ≠ 0)
    (hscoreMeasTargetT :
      ∀ index unit, unit ∈ targetSample index ->
        targetOutcomeT index unit =
          treatedValue index (treatedPrognosticScore index unit))
    (hscoreMeasTreated :
      ∀ index unit, unit ∈ treatedSample index ->
        treatedOutcome index unit =
          treatedValue index (treatedPrognosticScore index unit))
    (hscoreMeasTargetC :
      ∀ index unit, unit ∈ targetSample index ->
        targetOutcomeC index unit =
          controlValue index (controlPrognosticScore index unit))
    (hscoreMeasControl :
      ∀ index unit, unit ∈ controlSample index ->
        controlOutcome index unit =
          controlValue index (controlPrognosticScore index unit))
    (htreated_bound :
      ∀ index cell, cell ∈ cells index ->
        |treatedCellValueOnPATEDoubleScore (treatedValue index) cell| ≤
          treatedEnvelope index)
    (hcontrol_bound :
      ∀ index cell, cell ∈ cells index ->
        |controlCellValueOnPATEDoubleScore (controlValue index) cell| ≤
          controlEnvelope index)
    (htreatedEnvelope :
      Tendsto treatedEnvelope l (nhds treatedEnvelopeLimit))
    (hcontrolEnvelope :
      Tendsto controlEnvelope l (nhds controlEnvelopeLimit))
    (htreatedL1 :
      Tendsto
        (fun index =>
          l1PATEDoubleScoreShareDistance (cells index)
            (targetSample index) (treatedSample index)
            (targetWeight index) (treatedWeight index)
            (propensityScore index) (treatedPrognosticScore index)
            (controlPrognosticScore index))
        l (nhds 0))
    (hcontrolL1 :
      Tendsto
        (fun index =>
          l1PATEDoubleScoreShareDistance (cells index)
            (targetSample index) (controlSample index)
            (targetWeight index) (controlWeight index)
            (propensityScore index) (treatedPrognosticScore index)
            (controlPrognosticScore index))
        l (nhds 0)) :
    Tendsto
      (fun index =>
        weightedSampleMeanContrast (targetSample index)
          (targetWeight index) (targetOutcomeT index)
          (targetOutcomeC index) -
        twoArmWeightedMeanContrast (treatedSample index)
          (controlSample index) (treatedWeight index)
          (controlWeight index) (treatedOutcome index)
          (controlOutcome index))
      l (nhds 0) := by
  exact tendsto_pateDoubleScoreApprox_error_zero_of_l1
    targetSample treatedSample controlSample cells targetWeight treatedWeight
    controlWeight targetOutcomeT targetOutcomeC treatedOutcome controlOutcome
    propensityScore treatedPrognosticScore controlPrognosticScore
    treatedValue controlValue treatedEnvelope controlEnvelope hcoverTarget
    hcoverTreated hcoverControl hmassTarget hmassTreated hmassControl
    hscoreMeasTargetT hscoreMeasTreated hscoreMeasTargetC hscoreMeasControl
    htreated_bound hcontrol_bound
    (tendsto_two_envelope_mul_errors_zero treatedEnvelope controlEnvelope
      (fun index =>
        l1PATEDoubleScoreShareDistance (cells index)
          (targetSample index) (treatedSample index)
          (targetWeight index) (treatedWeight index)
          (propensityScore index) (treatedPrognosticScore index)
          (controlPrognosticScore index))
      (fun index =>
        l1PATEDoubleScoreShareDistance (cells index)
          (targetSample index) (controlSample index)
          (targetWeight index) (controlWeight index)
          (propensityScore index) (treatedPrognosticScore index)
          (controlPrognosticScore index))
      treatedEnvelopeLimit controlEnvelopeLimit htreatedEnvelope
      hcontrolEnvelope htreatedL1 hcontrolL1)

theorem tendsto_scaled_pateDoubleScoreApprox_error_zero_of_scaled_l1_and_envelopes
    (scale : Index -> Real)
    (targetSample treatedSample controlSample : Index -> Finset Unit)
    (cells :
      Index -> Finset ((PropensityCell × TreatedProgCell) × ControlProgCell))
    (targetWeight treatedWeight controlWeight : Index -> Unit -> Real)
    (targetOutcomeT targetOutcomeC treatedOutcome controlOutcome :
      Index -> Unit -> Real)
    (propensityScore : Index -> Unit -> PropensityCell)
    (treatedPrognosticScore : Index -> Unit -> TreatedProgCell)
    (controlPrognosticScore : Index -> Unit -> ControlProgCell)
    (treatedValue : Index -> TreatedProgCell -> Real)
    (controlValue : Index -> ControlProgCell -> Real)
    (treatedEnvelope controlEnvelope : Index -> Real)
    (treatedEnvelopeLimit controlEnvelopeLimit : Real)
    (hscale_nonneg : ∀ index, 0 ≤ scale index)
    (hcoverTarget :
      ∀ index unit, unit ∈ targetSample index ->
        pateDoubleScore (propensityScore index)
          (treatedPrognosticScore index)
          (controlPrognosticScore index) unit ∈ cells index)
    (hcoverTreated :
      ∀ index unit, unit ∈ treatedSample index ->
        pateDoubleScore (propensityScore index)
          (treatedPrognosticScore index)
          (controlPrognosticScore index) unit ∈ cells index)
    (hcoverControl :
      ∀ index unit, unit ∈ controlSample index ->
        pateDoubleScore (propensityScore index)
          (treatedPrognosticScore index)
          (controlPrognosticScore index) unit ∈ cells index)
    (hmassTarget :
      ∀ index cell, cell ∈ cells index ->
        scoreCellMass (targetSample index) (targetWeight index)
          (pateDoubleScore (propensityScore index)
            (treatedPrognosticScore index)
            (controlPrognosticScore index)) cell ≠ 0)
    (hmassTreated :
      ∀ index cell, cell ∈ cells index ->
        scoreCellMass (treatedSample index) (treatedWeight index)
          (pateDoubleScore (propensityScore index)
            (treatedPrognosticScore index)
            (controlPrognosticScore index)) cell ≠ 0)
    (hmassControl :
      ∀ index cell, cell ∈ cells index ->
        scoreCellMass (controlSample index) (controlWeight index)
          (pateDoubleScore (propensityScore index)
            (treatedPrognosticScore index)
            (controlPrognosticScore index)) cell ≠ 0)
    (hscoreMeasTargetT :
      ∀ index unit, unit ∈ targetSample index ->
        targetOutcomeT index unit =
          treatedValue index (treatedPrognosticScore index unit))
    (hscoreMeasTreated :
      ∀ index unit, unit ∈ treatedSample index ->
        treatedOutcome index unit =
          treatedValue index (treatedPrognosticScore index unit))
    (hscoreMeasTargetC :
      ∀ index unit, unit ∈ targetSample index ->
        targetOutcomeC index unit =
          controlValue index (controlPrognosticScore index unit))
    (hscoreMeasControl :
      ∀ index unit, unit ∈ controlSample index ->
        controlOutcome index unit =
          controlValue index (controlPrognosticScore index unit))
    (htreated_bound :
      ∀ index cell, cell ∈ cells index ->
        |treatedCellValueOnPATEDoubleScore (treatedValue index) cell| ≤
          treatedEnvelope index)
    (hcontrol_bound :
      ∀ index cell, cell ∈ cells index ->
        |controlCellValueOnPATEDoubleScore (controlValue index) cell| ≤
          controlEnvelope index)
    (htreatedEnvelope :
      Tendsto treatedEnvelope l (nhds treatedEnvelopeLimit))
    (hcontrolEnvelope :
      Tendsto controlEnvelope l (nhds controlEnvelopeLimit))
    (htreatedScaledL1 :
      Tendsto
        (fun index =>
          scale index *
            l1PATEDoubleScoreShareDistance (cells index)
              (targetSample index) (treatedSample index)
              (targetWeight index) (treatedWeight index)
              (propensityScore index) (treatedPrognosticScore index)
              (controlPrognosticScore index))
        l (nhds 0))
    (hcontrolScaledL1 :
      Tendsto
        (fun index =>
          scale index *
            l1PATEDoubleScoreShareDistance (cells index)
              (targetSample index) (controlSample index)
              (targetWeight index) (controlWeight index)
              (propensityScore index) (treatedPrognosticScore index)
              (controlPrognosticScore index))
        l (nhds 0)) :
    Tendsto
      (fun index =>
        scale index *
          (weightedSampleMeanContrast (targetSample index)
            (targetWeight index) (targetOutcomeT index)
            (targetOutcomeC index) -
          twoArmWeightedMeanContrast (treatedSample index)
            (controlSample index) (treatedWeight index)
            (controlWeight index) (treatedOutcome index)
            (controlOutcome index)))
      l (nhds 0) := by
  exact tendsto_scaled_pateDoubleScoreApprox_error_zero_of_l1
    scale targetSample treatedSample controlSample cells targetWeight
    treatedWeight controlWeight targetOutcomeT targetOutcomeC treatedOutcome
    controlOutcome propensityScore treatedPrognosticScore
    controlPrognosticScore treatedValue controlValue treatedEnvelope
    controlEnvelope hscale_nonneg hcoverTarget hcoverTreated hcoverControl
    hmassTarget hmassTreated hmassControl hscoreMeasTargetT
    hscoreMeasTreated hscoreMeasTargetC hscoreMeasControl htreated_bound
    hcontrol_bound
    (tendsto_scaled_two_envelope_mul_errors_zero scale treatedEnvelope
      controlEnvelope
      (fun index =>
        l1PATEDoubleScoreShareDistance (cells index)
          (targetSample index) (treatedSample index)
          (targetWeight index) (treatedWeight index)
          (propensityScore index) (treatedPrognosticScore index)
          (controlPrognosticScore index))
      (fun index =>
        l1PATEDoubleScoreShareDistance (cells index)
          (targetSample index) (controlSample index)
          (targetWeight index) (controlWeight index)
          (propensityScore index) (treatedPrognosticScore index)
          (controlPrognosticScore index))
      treatedEnvelopeLimit controlEnvelopeLimit htreatedEnvelope
      hcontrolEnvelope htreatedScaledL1 hcontrolScaledL1)

theorem tendsto_pattDoubleScoreApprox_error_zero_of_l1_and_envelope
    (targetSample controlSample : Index -> Finset Unit)
    (cells : Index -> Finset (PropensityCell × PATTProgCell))
    (targetWeight controlWeight : Index -> Unit -> Real)
    (treatedTargetOutcome targetControlOutcome controlOutcome :
      Index -> Unit -> Real)
    (propensityScore : Index -> Unit -> PropensityCell)
    (controlPrognosticScore : Index -> Unit -> PATTProgCell)
    (controlValue : Index -> PATTProgCell -> Real)
    (controlEnvelope : Index -> Real)
    (controlEnvelopeLimit : Real)
    (hcoverTarget :
      ∀ index unit, unit ∈ targetSample index ->
        pattDoubleScore (propensityScore index)
          (controlPrognosticScore index) unit ∈ cells index)
    (hcoverControl :
      ∀ index unit, unit ∈ controlSample index ->
        pattDoubleScore (propensityScore index)
          (controlPrognosticScore index) unit ∈ cells index)
    (hmassTarget :
      ∀ index cell, cell ∈ cells index ->
        scoreCellMass (targetSample index) (targetWeight index)
          (pattDoubleScore (propensityScore index)
            (controlPrognosticScore index)) cell ≠ 0)
    (hmassControl :
      ∀ index cell, cell ∈ cells index ->
        scoreCellMass (controlSample index) (controlWeight index)
          (pattDoubleScore (propensityScore index)
            (controlPrognosticScore index)) cell ≠ 0)
    (hscoreMeasTargetC :
      ∀ index unit, unit ∈ targetSample index ->
        targetControlOutcome index unit =
          controlValue index (controlPrognosticScore index unit))
    (hscoreMeasControl :
      ∀ index unit, unit ∈ controlSample index ->
        controlOutcome index unit =
          controlValue index (controlPrognosticScore index unit))
    (hcontrol_bound :
      ∀ index cell, cell ∈ cells index ->
        |controlCellValueOnPATTDoubleScore (controlValue index) cell| ≤
          controlEnvelope index)
    (hcontrolEnvelope :
      Tendsto controlEnvelope l (nhds controlEnvelopeLimit))
    (hcontrolL1 :
      Tendsto
        (fun index =>
          l1PATTDoubleScoreShareDistance (cells index)
            (targetSample index) (controlSample index)
            (targetWeight index) (controlWeight index)
            (propensityScore index) (controlPrognosticScore index))
        l (nhds 0)) :
    Tendsto
      (fun index =>
        weightedSampleMeanContrast (targetSample index)
          (targetWeight index) (treatedTargetOutcome index)
          (targetControlOutcome index) -
        pattWeightedMeanContrast (targetSample index) (controlSample index)
          (targetWeight index) (controlWeight index)
          (treatedTargetOutcome index) (controlOutcome index))
      l (nhds 0) := by
  exact tendsto_pattDoubleScoreApprox_error_zero_of_l1
    targetSample controlSample cells targetWeight controlWeight
    treatedTargetOutcome targetControlOutcome controlOutcome propensityScore
    controlPrognosticScore controlValue controlEnvelope hcoverTarget
    hcoverControl hmassTarget hmassControl hscoreMeasTargetC
    hscoreMeasControl hcontrol_bound
    (tendsto_envelope_mul_error_zero controlEnvelope
      (fun index =>
        l1PATTDoubleScoreShareDistance (cells index)
          (targetSample index) (controlSample index)
          (targetWeight index) (controlWeight index)
          (propensityScore index) (controlPrognosticScore index))
      controlEnvelopeLimit hcontrolEnvelope hcontrolL1)

theorem tendsto_scaled_pattDoubleScoreApprox_error_zero_of_scaled_l1_and_envelope
    (scale : Index -> Real)
    (targetSample controlSample : Index -> Finset Unit)
    (cells : Index -> Finset (PropensityCell × PATTProgCell))
    (targetWeight controlWeight : Index -> Unit -> Real)
    (treatedTargetOutcome targetControlOutcome controlOutcome :
      Index -> Unit -> Real)
    (propensityScore : Index -> Unit -> PropensityCell)
    (controlPrognosticScore : Index -> Unit -> PATTProgCell)
    (controlValue : Index -> PATTProgCell -> Real)
    (controlEnvelope : Index -> Real)
    (controlEnvelopeLimit : Real)
    (hscale_nonneg : ∀ index, 0 ≤ scale index)
    (hcoverTarget :
      ∀ index unit, unit ∈ targetSample index ->
        pattDoubleScore (propensityScore index)
          (controlPrognosticScore index) unit ∈ cells index)
    (hcoverControl :
      ∀ index unit, unit ∈ controlSample index ->
        pattDoubleScore (propensityScore index)
          (controlPrognosticScore index) unit ∈ cells index)
    (hmassTarget :
      ∀ index cell, cell ∈ cells index ->
        scoreCellMass (targetSample index) (targetWeight index)
          (pattDoubleScore (propensityScore index)
            (controlPrognosticScore index)) cell ≠ 0)
    (hmassControl :
      ∀ index cell, cell ∈ cells index ->
        scoreCellMass (controlSample index) (controlWeight index)
          (pattDoubleScore (propensityScore index)
            (controlPrognosticScore index)) cell ≠ 0)
    (hscoreMeasTargetC :
      ∀ index unit, unit ∈ targetSample index ->
        targetControlOutcome index unit =
          controlValue index (controlPrognosticScore index unit))
    (hscoreMeasControl :
      ∀ index unit, unit ∈ controlSample index ->
        controlOutcome index unit =
          controlValue index (controlPrognosticScore index unit))
    (hcontrol_bound :
      ∀ index cell, cell ∈ cells index ->
        |controlCellValueOnPATTDoubleScore (controlValue index) cell| ≤
          controlEnvelope index)
    (hcontrolEnvelope :
      Tendsto controlEnvelope l (nhds controlEnvelopeLimit))
    (hcontrolScaledL1 :
      Tendsto
        (fun index =>
          scale index *
            l1PATTDoubleScoreShareDistance (cells index)
              (targetSample index) (controlSample index)
              (targetWeight index) (controlWeight index)
              (propensityScore index) (controlPrognosticScore index))
        l (nhds 0)) :
    Tendsto
      (fun index =>
        scale index *
          (weightedSampleMeanContrast (targetSample index)
            (targetWeight index) (treatedTargetOutcome index)
            (targetControlOutcome index) -
          pattWeightedMeanContrast (targetSample index) (controlSample index)
            (targetWeight index) (controlWeight index)
            (treatedTargetOutcome index) (controlOutcome index)))
      l (nhds 0) := by
  exact tendsto_scaled_pattDoubleScoreApprox_error_zero_of_l1
    scale targetSample controlSample cells targetWeight controlWeight
    treatedTargetOutcome targetControlOutcome controlOutcome propensityScore
    controlPrognosticScore controlValue controlEnvelope hscale_nonneg
    hcoverTarget hcoverControl hmassTarget hmassControl hscoreMeasTargetC
    hscoreMeasControl hcontrol_bound
    (tendsto_scaled_envelope_mul_error_zero scale controlEnvelope
      (fun index =>
        l1PATTDoubleScoreShareDistance (cells index)
          (targetSample index) (controlSample index)
          (targetWeight index) (controlWeight index)
          (propensityScore index) (controlPrognosticScore index))
      controlEnvelopeLimit hcontrolEnvelope hcontrolScaledL1)

theorem tendsto_pateDoubleScoreApprox_error_zero_of_eventually_l1_and_envelopes
    (targetSample treatedSample controlSample : Index -> Finset Unit)
    (cells :
      Index -> Finset ((PropensityCell × TreatedProgCell) × ControlProgCell))
    (targetWeight treatedWeight controlWeight : Index -> Unit -> Real)
    (targetOutcomeT targetOutcomeC treatedOutcome controlOutcome :
      Index -> Unit -> Real)
    (propensityScore : Index -> Unit -> PropensityCell)
    (treatedPrognosticScore : Index -> Unit -> TreatedProgCell)
    (controlPrognosticScore : Index -> Unit -> ControlProgCell)
    (treatedValue : Index -> TreatedProgCell -> Real)
    (controlValue : Index -> ControlProgCell -> Real)
    (treatedEnvelope controlEnvelope : Index -> Real)
    (treatedEnvelopeLimit controlEnvelopeLimit : Real)
    (hcoverTarget :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ targetSample index ->
          pateDoubleScore (propensityScore index)
            (treatedPrognosticScore index)
            (controlPrognosticScore index) unit ∈ cells index)
    (hcoverTreated :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ treatedSample index ->
          pateDoubleScore (propensityScore index)
            (treatedPrognosticScore index)
            (controlPrognosticScore index) unit ∈ cells index)
    (hcoverControl :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ controlSample index ->
          pateDoubleScore (propensityScore index)
            (treatedPrognosticScore index)
            (controlPrognosticScore index) unit ∈ cells index)
    (hmassTarget :
      ∀ᶠ index in l,
        ∀ cell, cell ∈ cells index ->
          scoreCellMass (targetSample index) (targetWeight index)
            (pateDoubleScore (propensityScore index)
              (treatedPrognosticScore index)
              (controlPrognosticScore index)) cell ≠ 0)
    (hmassTreated :
      ∀ᶠ index in l,
        ∀ cell, cell ∈ cells index ->
          scoreCellMass (treatedSample index) (treatedWeight index)
            (pateDoubleScore (propensityScore index)
              (treatedPrognosticScore index)
              (controlPrognosticScore index)) cell ≠ 0)
    (hmassControl :
      ∀ᶠ index in l,
        ∀ cell, cell ∈ cells index ->
          scoreCellMass (controlSample index) (controlWeight index)
            (pateDoubleScore (propensityScore index)
              (treatedPrognosticScore index)
              (controlPrognosticScore index)) cell ≠ 0)
    (hscoreMeasTargetT :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ targetSample index ->
          targetOutcomeT index unit =
            treatedValue index (treatedPrognosticScore index unit))
    (hscoreMeasTreated :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ treatedSample index ->
          treatedOutcome index unit =
            treatedValue index (treatedPrognosticScore index unit))
    (hscoreMeasTargetC :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ targetSample index ->
          targetOutcomeC index unit =
            controlValue index (controlPrognosticScore index unit))
    (hscoreMeasControl :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ controlSample index ->
          controlOutcome index unit =
            controlValue index (controlPrognosticScore index unit))
    (htreated_bound :
      ∀ᶠ index in l,
        ∀ cell, cell ∈ cells index ->
          |treatedCellValueOnPATEDoubleScore (treatedValue index) cell| ≤
            treatedEnvelope index)
    (hcontrol_bound :
      ∀ᶠ index in l,
        ∀ cell, cell ∈ cells index ->
          |controlCellValueOnPATEDoubleScore (controlValue index) cell| ≤
            controlEnvelope index)
    (htreatedEnvelope :
      Tendsto treatedEnvelope l (nhds treatedEnvelopeLimit))
    (hcontrolEnvelope :
      Tendsto controlEnvelope l (nhds controlEnvelopeLimit))
    (htreatedL1 :
      Tendsto
        (fun index =>
          l1PATEDoubleScoreShareDistance (cells index)
            (targetSample index) (treatedSample index)
            (targetWeight index) (treatedWeight index)
            (propensityScore index) (treatedPrognosticScore index)
            (controlPrognosticScore index))
        l (nhds 0))
    (hcontrolL1 :
      Tendsto
        (fun index =>
          l1PATEDoubleScoreShareDistance (cells index)
            (targetSample index) (controlSample index)
            (targetWeight index) (controlWeight index)
            (propensityScore index) (treatedPrognosticScore index)
            (controlPrognosticScore index))
        l (nhds 0)) :
    Tendsto
      (fun index =>
        weightedSampleMeanContrast (targetSample index)
          (targetWeight index) (targetOutcomeT index)
          (targetOutcomeC index) -
        twoArmWeightedMeanContrast (treatedSample index)
          (controlSample index) (treatedWeight index)
          (controlWeight index) (treatedOutcome index)
          (controlOutcome index))
      l (nhds 0) := by
  exact tendsto_pateDoubleScoreApprox_error_zero_of_eventually_l1
    targetSample treatedSample controlSample cells targetWeight treatedWeight
    controlWeight targetOutcomeT targetOutcomeC treatedOutcome controlOutcome
    propensityScore treatedPrognosticScore controlPrognosticScore
    treatedValue controlValue treatedEnvelope controlEnvelope hcoverTarget
    hcoverTreated hcoverControl hmassTarget hmassTreated hmassControl
    hscoreMeasTargetT hscoreMeasTreated hscoreMeasTargetC hscoreMeasControl
    htreated_bound hcontrol_bound
    (tendsto_two_envelope_mul_errors_zero treatedEnvelope controlEnvelope
      (fun index =>
        l1PATEDoubleScoreShareDistance (cells index)
          (targetSample index) (treatedSample index)
          (targetWeight index) (treatedWeight index)
          (propensityScore index) (treatedPrognosticScore index)
          (controlPrognosticScore index))
      (fun index =>
        l1PATEDoubleScoreShareDistance (cells index)
          (targetSample index) (controlSample index)
          (targetWeight index) (controlWeight index)
          (propensityScore index) (treatedPrognosticScore index)
          (controlPrognosticScore index))
      treatedEnvelopeLimit controlEnvelopeLimit htreatedEnvelope
      hcontrolEnvelope htreatedL1 hcontrolL1)

theorem tendsto_scaled_pateDoubleScoreApprox_error_zero_of_eventually_scaled_l1_and_envelopes
    (scale : Index -> Real)
    (targetSample treatedSample controlSample : Index -> Finset Unit)
    (cells :
      Index -> Finset ((PropensityCell × TreatedProgCell) × ControlProgCell))
    (targetWeight treatedWeight controlWeight : Index -> Unit -> Real)
    (targetOutcomeT targetOutcomeC treatedOutcome controlOutcome :
      Index -> Unit -> Real)
    (propensityScore : Index -> Unit -> PropensityCell)
    (treatedPrognosticScore : Index -> Unit -> TreatedProgCell)
    (controlPrognosticScore : Index -> Unit -> ControlProgCell)
    (treatedValue : Index -> TreatedProgCell -> Real)
    (controlValue : Index -> ControlProgCell -> Real)
    (treatedEnvelope controlEnvelope : Index -> Real)
    (treatedEnvelopeLimit controlEnvelopeLimit : Real)
    (hscale_nonneg : ∀ᶠ index in l, 0 ≤ scale index)
    (hcoverTarget :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ targetSample index ->
          pateDoubleScore (propensityScore index)
            (treatedPrognosticScore index)
            (controlPrognosticScore index) unit ∈ cells index)
    (hcoverTreated :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ treatedSample index ->
          pateDoubleScore (propensityScore index)
            (treatedPrognosticScore index)
            (controlPrognosticScore index) unit ∈ cells index)
    (hcoverControl :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ controlSample index ->
          pateDoubleScore (propensityScore index)
            (treatedPrognosticScore index)
            (controlPrognosticScore index) unit ∈ cells index)
    (hmassTarget :
      ∀ᶠ index in l,
        ∀ cell, cell ∈ cells index ->
          scoreCellMass (targetSample index) (targetWeight index)
            (pateDoubleScore (propensityScore index)
              (treatedPrognosticScore index)
              (controlPrognosticScore index)) cell ≠ 0)
    (hmassTreated :
      ∀ᶠ index in l,
        ∀ cell, cell ∈ cells index ->
          scoreCellMass (treatedSample index) (treatedWeight index)
            (pateDoubleScore (propensityScore index)
              (treatedPrognosticScore index)
              (controlPrognosticScore index)) cell ≠ 0)
    (hmassControl :
      ∀ᶠ index in l,
        ∀ cell, cell ∈ cells index ->
          scoreCellMass (controlSample index) (controlWeight index)
            (pateDoubleScore (propensityScore index)
              (treatedPrognosticScore index)
              (controlPrognosticScore index)) cell ≠ 0)
    (hscoreMeasTargetT :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ targetSample index ->
          targetOutcomeT index unit =
            treatedValue index (treatedPrognosticScore index unit))
    (hscoreMeasTreated :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ treatedSample index ->
          treatedOutcome index unit =
            treatedValue index (treatedPrognosticScore index unit))
    (hscoreMeasTargetC :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ targetSample index ->
          targetOutcomeC index unit =
            controlValue index (controlPrognosticScore index unit))
    (hscoreMeasControl :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ controlSample index ->
          controlOutcome index unit =
            controlValue index (controlPrognosticScore index unit))
    (htreated_bound :
      ∀ᶠ index in l,
        ∀ cell, cell ∈ cells index ->
          |treatedCellValueOnPATEDoubleScore (treatedValue index) cell| ≤
            treatedEnvelope index)
    (hcontrol_bound :
      ∀ᶠ index in l,
        ∀ cell, cell ∈ cells index ->
          |controlCellValueOnPATEDoubleScore (controlValue index) cell| ≤
            controlEnvelope index)
    (htreatedEnvelope :
      Tendsto treatedEnvelope l (nhds treatedEnvelopeLimit))
    (hcontrolEnvelope :
      Tendsto controlEnvelope l (nhds controlEnvelopeLimit))
    (htreatedScaledL1 :
      Tendsto
        (fun index =>
          scale index *
            l1PATEDoubleScoreShareDistance (cells index)
              (targetSample index) (treatedSample index)
              (targetWeight index) (treatedWeight index)
              (propensityScore index) (treatedPrognosticScore index)
              (controlPrognosticScore index))
        l (nhds 0))
    (hcontrolScaledL1 :
      Tendsto
        (fun index =>
          scale index *
            l1PATEDoubleScoreShareDistance (cells index)
              (targetSample index) (controlSample index)
              (targetWeight index) (controlWeight index)
              (propensityScore index) (treatedPrognosticScore index)
              (controlPrognosticScore index))
        l (nhds 0)) :
    Tendsto
      (fun index =>
        scale index *
          (weightedSampleMeanContrast (targetSample index)
            (targetWeight index) (targetOutcomeT index)
            (targetOutcomeC index) -
          twoArmWeightedMeanContrast (treatedSample index)
            (controlSample index) (treatedWeight index)
            (controlWeight index) (treatedOutcome index)
            (controlOutcome index)))
      l (nhds 0) := by
  exact tendsto_scaled_pateDoubleScoreApprox_error_zero_of_eventually_l1
    scale targetSample treatedSample controlSample cells targetWeight
    treatedWeight controlWeight targetOutcomeT targetOutcomeC treatedOutcome
    controlOutcome propensityScore treatedPrognosticScore
    controlPrognosticScore treatedValue controlValue treatedEnvelope
    controlEnvelope hscale_nonneg hcoverTarget hcoverTreated hcoverControl
    hmassTarget hmassTreated hmassControl hscoreMeasTargetT
    hscoreMeasTreated hscoreMeasTargetC hscoreMeasControl htreated_bound
    hcontrol_bound
    (tendsto_scaled_two_envelope_mul_errors_zero scale treatedEnvelope
      controlEnvelope
      (fun index =>
        l1PATEDoubleScoreShareDistance (cells index)
          (targetSample index) (treatedSample index)
          (targetWeight index) (treatedWeight index)
          (propensityScore index) (treatedPrognosticScore index)
          (controlPrognosticScore index))
      (fun index =>
        l1PATEDoubleScoreShareDistance (cells index)
          (targetSample index) (controlSample index)
          (targetWeight index) (controlWeight index)
          (propensityScore index) (treatedPrognosticScore index)
          (controlPrognosticScore index))
      treatedEnvelopeLimit controlEnvelopeLimit htreatedEnvelope
      hcontrolEnvelope htreatedScaledL1 hcontrolScaledL1)

theorem tendsto_pattDoubleScoreApprox_error_zero_of_eventually_l1_and_envelope
    (targetSample controlSample : Index -> Finset Unit)
    (cells : Index -> Finset (PropensityCell × PATTProgCell))
    (targetWeight controlWeight : Index -> Unit -> Real)
    (treatedTargetOutcome targetControlOutcome controlOutcome :
      Index -> Unit -> Real)
    (propensityScore : Index -> Unit -> PropensityCell)
    (controlPrognosticScore : Index -> Unit -> PATTProgCell)
    (controlValue : Index -> PATTProgCell -> Real)
    (controlEnvelope : Index -> Real)
    (controlEnvelopeLimit : Real)
    (hcoverTarget :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ targetSample index ->
          pattDoubleScore (propensityScore index)
            (controlPrognosticScore index) unit ∈ cells index)
    (hcoverControl :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ controlSample index ->
          pattDoubleScore (propensityScore index)
            (controlPrognosticScore index) unit ∈ cells index)
    (hmassTarget :
      ∀ᶠ index in l,
        ∀ cell, cell ∈ cells index ->
          scoreCellMass (targetSample index) (targetWeight index)
            (pattDoubleScore (propensityScore index)
              (controlPrognosticScore index)) cell ≠ 0)
    (hmassControl :
      ∀ᶠ index in l,
        ∀ cell, cell ∈ cells index ->
          scoreCellMass (controlSample index) (controlWeight index)
            (pattDoubleScore (propensityScore index)
              (controlPrognosticScore index)) cell ≠ 0)
    (hscoreMeasTargetC :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ targetSample index ->
          targetControlOutcome index unit =
            controlValue index (controlPrognosticScore index unit))
    (hscoreMeasControl :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ controlSample index ->
          controlOutcome index unit =
            controlValue index (controlPrognosticScore index unit))
    (hcontrol_bound :
      ∀ᶠ index in l,
        ∀ cell, cell ∈ cells index ->
          |controlCellValueOnPATTDoubleScore (controlValue index) cell| ≤
            controlEnvelope index)
    (hcontrolEnvelope :
      Tendsto controlEnvelope l (nhds controlEnvelopeLimit))
    (hcontrolL1 :
      Tendsto
        (fun index =>
          l1PATTDoubleScoreShareDistance (cells index)
            (targetSample index) (controlSample index)
            (targetWeight index) (controlWeight index)
            (propensityScore index) (controlPrognosticScore index))
        l (nhds 0)) :
    Tendsto
      (fun index =>
        weightedSampleMeanContrast (targetSample index)
          (targetWeight index) (treatedTargetOutcome index)
          (targetControlOutcome index) -
        pattWeightedMeanContrast (targetSample index) (controlSample index)
          (targetWeight index) (controlWeight index)
          (treatedTargetOutcome index) (controlOutcome index))
      l (nhds 0) := by
  exact tendsto_pattDoubleScoreApprox_error_zero_of_eventually_l1
    targetSample controlSample cells targetWeight controlWeight
    treatedTargetOutcome targetControlOutcome controlOutcome propensityScore
    controlPrognosticScore controlValue controlEnvelope hcoverTarget
    hcoverControl hmassTarget hmassControl hscoreMeasTargetC
    hscoreMeasControl hcontrol_bound
    (tendsto_envelope_mul_error_zero controlEnvelope
      (fun index =>
        l1PATTDoubleScoreShareDistance (cells index)
          (targetSample index) (controlSample index)
          (targetWeight index) (controlWeight index)
          (propensityScore index) (controlPrognosticScore index))
      controlEnvelopeLimit hcontrolEnvelope hcontrolL1)

theorem tendsto_scaled_pattDoubleScoreApprox_error_zero_of_eventually_scaled_l1_and_envelope
    (scale : Index -> Real)
    (targetSample controlSample : Index -> Finset Unit)
    (cells : Index -> Finset (PropensityCell × PATTProgCell))
    (targetWeight controlWeight : Index -> Unit -> Real)
    (treatedTargetOutcome targetControlOutcome controlOutcome :
      Index -> Unit -> Real)
    (propensityScore : Index -> Unit -> PropensityCell)
    (controlPrognosticScore : Index -> Unit -> PATTProgCell)
    (controlValue : Index -> PATTProgCell -> Real)
    (controlEnvelope : Index -> Real)
    (controlEnvelopeLimit : Real)
    (hscale_nonneg : ∀ᶠ index in l, 0 ≤ scale index)
    (hcoverTarget :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ targetSample index ->
          pattDoubleScore (propensityScore index)
            (controlPrognosticScore index) unit ∈ cells index)
    (hcoverControl :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ controlSample index ->
          pattDoubleScore (propensityScore index)
            (controlPrognosticScore index) unit ∈ cells index)
    (hmassTarget :
      ∀ᶠ index in l,
        ∀ cell, cell ∈ cells index ->
          scoreCellMass (targetSample index) (targetWeight index)
            (pattDoubleScore (propensityScore index)
              (controlPrognosticScore index)) cell ≠ 0)
    (hmassControl :
      ∀ᶠ index in l,
        ∀ cell, cell ∈ cells index ->
          scoreCellMass (controlSample index) (controlWeight index)
            (pattDoubleScore (propensityScore index)
              (controlPrognosticScore index)) cell ≠ 0)
    (hscoreMeasTargetC :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ targetSample index ->
          targetControlOutcome index unit =
            controlValue index (controlPrognosticScore index unit))
    (hscoreMeasControl :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ controlSample index ->
          controlOutcome index unit =
            controlValue index (controlPrognosticScore index unit))
    (hcontrol_bound :
      ∀ᶠ index in l,
        ∀ cell, cell ∈ cells index ->
          |controlCellValueOnPATTDoubleScore (controlValue index) cell| ≤
            controlEnvelope index)
    (hcontrolEnvelope :
      Tendsto controlEnvelope l (nhds controlEnvelopeLimit))
    (hcontrolScaledL1 :
      Tendsto
        (fun index =>
          scale index *
            l1PATTDoubleScoreShareDistance (cells index)
              (targetSample index) (controlSample index)
              (targetWeight index) (controlWeight index)
              (propensityScore index) (controlPrognosticScore index))
        l (nhds 0)) :
    Tendsto
      (fun index =>
        scale index *
          (weightedSampleMeanContrast (targetSample index)
            (targetWeight index) (treatedTargetOutcome index)
            (targetControlOutcome index) -
          pattWeightedMeanContrast (targetSample index) (controlSample index)
            (targetWeight index) (controlWeight index)
            (treatedTargetOutcome index) (controlOutcome index)))
      l (nhds 0) := by
  exact tendsto_scaled_pattDoubleScoreApprox_error_zero_of_eventually_l1
    scale targetSample controlSample cells targetWeight controlWeight
    treatedTargetOutcome targetControlOutcome controlOutcome propensityScore
    controlPrognosticScore controlValue controlEnvelope hscale_nonneg
    hcoverTarget hcoverControl hmassTarget hmassControl hscoreMeasTargetC
    hscoreMeasControl hcontrol_bound
    (tendsto_scaled_envelope_mul_error_zero scale controlEnvelope
      (fun index =>
        l1PATTDoubleScoreShareDistance (cells index)
          (targetSample index) (controlSample index)
          (targetWeight index) (controlWeight index)
          (propensityScore index) (controlPrognosticScore index))
      controlEnvelopeLimit hcontrolEnvelope hcontrolScaledL1)

end WDSM
end Matching
end StatInference
